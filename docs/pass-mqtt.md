# Pass-level MQTT

suslik can publish one message per pass — one person's walk across one or more
cameras — on `<mqtt.topic_praefix>/pass`. This is a read-only view for home
automation: it does not feed back into recognition, and vision stays off.
Messages are QoS 0 and non-retained, so a subscriber only sees passes that
arrive while it is connected.

## Status and revision

Each message carries one of three statuses:

- `active` — the pass is still collecting events. Repeated `active` publishes
  are throttled: they are only sent when `revision` changes.
- `final` — the pass is closed after its `szene_karenz_s` timer ran out.
- `revision` — events arrived after `final`; the same pass and segment are
  published again with a new `revision`.

`revision` is deterministic: the first 12 hex characters of the SHA-256 of a
canonical JSON object holding `schema` (`pass-v1`), `pass_key`, `segment`,
`window`, `eids`, frame ids, people, categories and counts. Consumers can use
it both to deduplicate messages and as the cache key for the contact sheet.

## Payload

```json
{
  "schema": "pass-v1",
  "herkunft": "pass",
  "pass_key": "1764231000",
  "segment": 0,
  "segments": 1,
  "status": "final",
  "revision": "9f3c1a7b2e40",
  "window": [1764231000, 1764231240],
  "eids": ["evt-1a2b3c", "evt-4d5e6f"],
  "counts": {"events": 2, "frames": 10, "known_people": 1, "unknown": 1},
  "camera_sequence": ["front_door", "driveway"],
  "camera_first_seen": "front_door",
  "inferred_direction": "front_door->driveway",
  "people": [
    {"name": "Person A", "count": 3, "first_camera": "front_door", "last_camera": "driveway", "best_cos": 0.82},
    {"name": "unknown", "count": 1, "first_camera": "driveway", "last_camera": "driveway", "best_cos": 0.0}
  ],
  "categories": "erkannt",
  "frames": [
    {"id": "evt-1a2b3c|person|Person A", "eid": "evt-1a2b3c", "camera": "front_door", "ts": 1764231004, "kind": "person", "url": "/events/evt-1a2b3c/crop_00.png", "score": 0.82},
    {"id": "evt-1a2b3c|ref|4d5e6f", "eid": "evt-1a2b3c", "camera": "front_door", "ts": 1764231006, "kind": "ref", "url": "/lernlauf/satz/4d5e6f?klein=1", "score": 0.79},
    {"id": "evt-1a2b3c|camera|front_door", "eid": "evt-1a2b3c", "camera": "front_door", "ts": 1764231010, "kind": "camera", "url": "/events/evt-1a2b3c/snapshot.jpg", "score": 0.71},
    {"id": "evt-4d5e6f|event|evt-4d5e6f", "eid": "evt-4d5e6f", "camera": "driveway", "ts": 1764231122, "kind": "event", "url": "/events/evt-4d5e6f/crop_00.png", "score": 0.64}
  ],
  "contact_url": "/pass/1764231000/9f3c1a7b2e40/0/contact.jpg"
}
```

The example shows four frames; a real message carries up to twelve, targeting
ten, and fewer when the segment has fewer usable images. All names in it are
synthetic. `pass_key` identifies the walk, `segment` is the zero-based part and
`segments` the part count. `window` is a two-element list `[start, end]` of
epoch seconds, and `eids` are the member event ids. `camera_sequence` is the
order cameras were seen in, `camera_first_seen` is the camera where the person
was first seen, and `inferred_direction` is `camera_first_seen` plus `->` plus
the last camera (for example `front_door->driveway`). `categories` is the pass
category string, for example `erkannt`. `people[].best_cos` is the best cosine
similarity and `frames[].score` the recognition score. A frame `id` is
`<eid>|<src>|key` and `kind` is one of `ref`, `person`, `camera`, `event`.

There is deliberately no `zones` field: zone data is not present in pass rows,
so it is not published.

## Frames and the contact sheet

The `url` of each frame is an existing guarded route, either
`/events/<eid>/<file>` for an event image or `/lernlauf/satz/<hex>?klein=1`
for a learned-set image. All URLs in the payload are relative, including
`contact_url`: Home Assistant prefixes its own base URL. These frame URLs are
diagnostic and secondary.

Ref frames come from the existing guarded `/lernlauf/satz/<hex>?klein=1` route,
reading `refquelle/<ref_id>/profil.*` from suslik's set directories, including
archived sets. A missing set is skipped, so `frames` and `counts.frames` only
contain usable images. When fewer than eight usable images exist, fewer frames
are sent.

`contact_url` is the primary input for Home Assistant. The HA host has no
ffmpeg, Pillow or ImageMagick, so Gemini `image_analyzer` gets one local file
per call: download `contact_url` and pass that file. The route
`/pass/<pass_key>/<revision>/<segment>/contact.jpg` is read-only, sits behind
the existing Caddy Basic Auth and validates its index key. It returns a 2x6
grid of tiles of about 512x384 pixels, each labelled with index, camera and
`ts`/`kind`, with at most twelve tiles. The JPEG is deterministic and cached
by `pass_key` + `revision` + `segment`; responses carry private, immutable
cache headers. No new public endpoint is added.

## Lifecycle

The hook runs after event analysis. A pass in progress publishes as `active`,
throttled by `revision`. Every `pass_key` owns its own in-memory
`szene_karenz_s` timer; when it expires the pass publishes `final`. Late
events restart the flow as `revision`. Timers live only in memory, so a
restart does not emit a storm of `final` messages.

## Pass segmentation

A pass is split at 600 seconds or 20 events, whichever comes first. Day and
pass boundaries are preserved, so a segment never crosses either. A single
overlong event forms a segment on its own. Frame selection is deterministic:
up to twelve frames per segment, targeting ten, and fewer when the segment has
fewer usable images.
