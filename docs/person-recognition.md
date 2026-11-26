# Person recognition (preview) — recognizing residents without a face

Sometimes an event shows up as "unknown" although it clearly is a known
person, just seen from behind or too far away for a face. Person
recognition is suslik's second recognition path for these cases. It
compares the whole body of a person with body images of your residents.

Everything runs locally. A body image is turned into a numerical
fingerprint (Intel's `person-reidentification-retail-0277` model). There
is no training: suslik compares fingerprints and gives a name only when
an image is close enough to one of your body images.

**Preview status:** the path works end to end, but its defaults are
measured on one system only. By default a body name is only shown. On the
**Recognition** page, the body card shows **Notifies:** (where it reports)
and the four switches (Frigate, Pushover, Telegram, Home Assistant)
directly, all off by default. They also appear on the **Advanced**
settings page (`koerper_meldet_frigate`, `koerper_meldet_pushover`,
`koerper_meldet_telegram`, `koerper_meldet_ha`). A switch only works when
its channel is set up; otherwise the card says *not set up*. Below them a
fifth switch, **Presence page** (`koerper_meldet_anwesenheit`, off by
default), sends nothing outside: it shows the body name on the **Presence**
page and in the hour bar on **Today**, in its own state *via person
recognition* (see [usage.md](usage.md)).

## How body images get into the stock

Body images come from your own recordings, from events where the face
path already recognized the person.

1. **The face path marks suitable videos.** For every analysed event
   suslik notes a few numbers it counted anyway. A video is suitable when
   the face path recognized exactly one person with enough votes
   (`koerper_auswahl_stimmen`), Frigate counted exactly one person, no
   other name and no unknown face showed up, and no picture had two real
   faces in it.
2. **The person learning run starts.** The choice **Start learning run**
   on the body card of the **Recognition** page (setting `koerper_lauf`)
   has three positions:
   - **by hand** (the default): open **Person → Body images**, set how
     many videos per person, optionally choose single people, and press
     **Start learning run**. The run takes the newest suitable videos of
     the last `koerper_max_tage` days that it has not handled yet. It picks
     them from suslik's own event record, not from Frigate.
   - **once a day with the maintenance**: the daily maintenance at 06:00
     starts the run over all suitable videos of the last `koerper_max_tage`
     days that are still waiting, for all people. It does not run when the
     service starts; if the service is down at 06:00, or a run is already
     going, that day's run is skipped and the next day's run takes the
     videos.
   - **right after each suitable video**: right after the analysis of a
     suitable event, suslik cuts that one video. Then one cut runs for each
     suitable event at the same time as the analysis of the next events, in
     the separate body process (on a CPU installation it shares the cores
     with the analysis). Re-analyses and injected events start nothing.
   The button stays usable in every position. A restart of the service,
   also by saving a changed setting, stops a running run; the videos it did
   not reach wait for the next run by hand or the next daily run.
3. **The run cuts a few images per video.** It runs in its own
   background process, one video at a time. It follows the path of the
   person through the clip, keeps only pictures where the whole person is
   visible, and crops each one to the person. At least one picture must
   be close to the person picture of the recognized face in the same
   event (`koerper_anker_min`);
   if none is, all pictures of that video are dropped, because they might
   show someone else. At most `koerper_bilder_je_video` images per video
   are kept, spread over the time the person was seen.
4. **You check the new images.** With `koerper_sichtpruefung` on (the
   default), new images wait under **New images** until you accept or
   discard them. Only accepted images count. With the switch **Accept new
   images automatically** on the body card of the **Recognition** page
   (the check off) new images count at once; images that were already
   waiting stay under **New images** until you accept or discard them,
   nothing becomes valid by itself.

The person learning run needs the field `snapshot_frame_time` in
Frigate's event data; without it suslik cannot match the clip to the
person's path, and the video gives no body image. Frigate 0.18 reports the
field, Frigate 0.17.2 does not. The run also needs the pose model; if it
is missing, the start button is disabled and the page says why.

## The Body images page

**Person → Body images** (`/koerperbilder`) is the first page of the
Person menu, next to **Named persons** (below). It is one short page and
shows only what has data, from top to bottom:

- **Person learning run**: the button **Start learning run (N videos
  available)**, where N is the number of suitable videos waiting, next to
  it the field **How many videos to check per person** (default 1), and
  folded away **Choose people** (shown when videos wait for two or more
  people; without a choice all people are included). Below, the progress
  of a running run or the result of the last one (videos checked, images
  kept, videos skipped with the reason in plain words). While a run is
  going, a small bar under that line fills up with the share of videos
  checked so far, without reloading the page. The button is disabled
  while a run is going, when the pose model is missing, or when no video
  waits; then the card explains when a video is suitable. With
  `person_pfad` off a note says so, and you can still collect images.
  When the run starts and whether new images count at once are set on the
  body card of the **Recognition** page. A run started automatically or
  by the daily maintenance says so in its line.
- **New images (N)**, whenever images wait: accept or discard each image,
  or accept all images of one person; with the check off a line above
  says that new images count at once. Without waiting images a single
  line says where new images come from, or that they count at once.
- **Stock**: one row per person with valid images, most images first,
  with the number of images, on how many of the last days there are
  images, and the newest one. Tap a row to see the images; the × removes a
  single image (it goes to the archive, nothing is deleted), and the page
  reloads with that row open. People without valid images appear only as
  a count. A person whose images are too similar to another person's has
  a red ring around the initial and a short red line under the name: it is
  not recognised by body, which person it is too similar to, with the
  value (rounded down to two places) and the threshold
  `koerper_schwelle`. Its images are still learned; a threshold above the
  value switches recognition back on, stricter for everyone. The images
  that are too close to another person have a red border, and the red
  line says how many ("Outlined in red: 1 of 2 images."). Open the row:
  the first line links to the threshold field on the body card of the
  **Recognition** page. Remove a red image with its ×; when all red
  images of a person are gone, recognition is on again at the same
  threshold, as long as valid images are left. Red means "too close to
  another person", not "wrong": both sides of a pair are red, and you
  decide which image is under the wrong name.
- At the bottom, the state of the path (`person_pfad`, marked as a
  warning while there are no images yet or the pose model is missing), of
  the image check and of the learning run start, with a link to the
  **Recognition** page.

Images older than `koerper_max_tage` days, and the oldest images of a
person above `koerper_max_je_person`, go to the trash in the daily data
cleanup. Clothes change, so the stock stays fresh.

## Recognition by distance

After the analysis of an event whose tracked person got no face name,
suslik cuts body pictures from that video in the same way (without the
face check) and compares them with the valid images of all people. The
number of people in the video does not matter. When Frigate counts two or
more people, suslik decides which name belongs to the tracked person; if
that person got no name, the event is checked. Otherwise an event is
checked only when no face in the clip was confirmed. A body name that a
face in the same clip already confirmed is not used.

- Each picture is compared with the closest valid image of each person.
- The threshold is `koerper_schwelle` (default 0.65), the same for every
  person. It does not change with your images. You can set it in the body
  card of the **Recognition** page (Easy and Expert) or on the **Advanced**
  settings page; a new value works after the restart that saving starts.
- A person whose valid images reach the threshold against the valid
  images of another person is too similar to that person: recognition is
  switched off for this person, so it gets no body name. Its images are
  still learned. A picture whose best match is such a person gives no
  name, and next to a name from another picture it blocks the name of the
  event. A higher threshold switches the person back on and makes
  recognition stricter for everyone.
- If two pictures of the event point to different people, there is no
  name.
- With `person_pfad` on `nur_wenn_gesicht_leer`, this runs only when the
  face path could not confirm everyone on the walk-through; when a video
  shows several people and the tracked person got no face name, it always
  runs. With `aus` it never runs. It also needs at least one valid body
  image.

One event at a time is checked. If the background process has no room in
time, that event gets no body name; it is not queued for later.

## Where the name shows up

A body name counts for a whole walk-through, not for a single event. It
counts votes: every query picture of an event that reaches the threshold
for a person is one vote, and the votes of all events of the
walk-through add up.

- The name counts when the person has at least `koerper_stimmen` votes
  (default 3) on the walk-through: one video with three votes is enough,
  so are two videos with two and one.
- Only votes from events where the tracked person has no face name count,
  no matter how many people the video shows.
- On a walk-through without a face name it is shown on the **Passes** tab
  of Activity, marked *via person recognition, no face*, and on the
  appearances page and the recognition test. It does not count there when
  the face path saw many good faces of the walk-through and none of them
  came close to anyone you know (then it was most likely a stranger).
- Next to a face that names someone else it counts too: the walk-through
  shows both names, and the body name goes to presence, notifications and
  Frigate like any other.
- Next to a face that names the same person it counts too, for the events
  without a face of their own; the page then shows the face name.

Records from before this version carry no vote count; each such event
counts as one vote.

The defaults are cautious. In a test with 232 events, the path gave 5
body names, all of them right and none wrong. If the floor is too high for
your system, you get no name rather than a wrong one.

## The Named persons page

**Person → Named persons** (`/koerpernamen`) shows only the people who
got a body name in the last three days, by the same rule as above, plus
names suslik wrote to Frigate. Each person gets one row of the newest
pictures, at most twelve, newest on the left; the row scrolls sideways.
Each picture is the one the comparison used, saved with the event, and
opens the event; below it date and time, on hover the camera, score,
threshold and votes, and a small mark when the name went to Frigate.
Names from before this version have no picture and are only counted. The
pictures go with the event folder after `aufbewahrung_tage` days.

A wrong name is fixed with the small ✕ below its picture: you may pick
the correct person or "stranger", or leave "don't know", then Save. The
body name of that event is gone for good, and the log notes it without
names; if suslik wrote it to Frigate, Frigate loses it or gets the
person you picked, and a picked person is saved as your verdict.

## Notifications of person recognition

With a switch on, a body name reports once per walk-through and person,
with its own text ("… recognised (camera, time) – via person recognition,
no face"); Pushover and Telegram carry the cut body picture:

- **Frigate**: the name goes in as sub label of the events it counts for,
  never over a name Frigate already carries; a face name found later
  replaces it. Needs `sub_label_schreiben`.
- **Pushover** and **Telegram**: one message; quiet when the face path or
  the body path saw the person within `anwesenheit_cooldown`. A face
  notification for the same walk-through stays separate, so you can get
  two.
- **Home Assistant**: an MQTT message on `<prefix>/koerper_erkannt` with
  the same fields as `szene_erkannt` plus `"quelle": "koerper"` and the
  event ids. `erkennung` and `szene_erkannt` stay unchanged.

Old events (catch-up runs, events older than 15 minutes) never notify;
Frigate entries are still made.

With **Presence page** on, every event the body name counts for gets a
presence mark (event time and camera) — also for catch-up runs, old events,
`dry_alert` and read-only mode, and without a quiet time. A quarter hour with
a face or live-watcher mark stays red (confirmed). Marks are only added:
switching off stops new ones, a later face naming someone else or a rename
does not change marks already written.

## Settings

All settings of the path are listed in
[configuration.md](configuration.md) under "Body images and person
recognition": `person_pfad`, the nine `koerper_*` settings, the five
`koerper_meldet_*` switches,
`personwork_rss_max_mb` (memory limit of the background process) and
`person_backend` (device for the fingerprint, default `cpu`).

## Limits

- A second person in the video whose face is never seen and whom Frigate
  does not count can end up under the name. The face check of the person
  learning run and your review of new images are the protection.
- Body images are only learned from videos with exactly one person.
- The defaults are measured on one system only.
- The result of the last person learning run is gone after a restart; the images
  and the record of handled videos stay.

## Vision detect is parked

The third path, vision detect, is switched off in this version. Its
galleries and candidate pictures came from the old person-learn run,
which has been removed. The Vision pages say so, and it cannot be switched
on until it is rebuilt on the new body images.
