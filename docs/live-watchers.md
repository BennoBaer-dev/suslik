# Live watchers

Live watchers are the fastest reaction path in my program: a watcher connects
straight to one camera stream and reacts **while the person is still in the
picture** — long before the recording is finished and analyzed. The goal is a
signal in **under one second** after the first face appears; on the reference
setup the measured range is **199–801 ms**. Use it as a trigger for home
automations (lights, announcements, gates), for example via MQTT.

A live watcher is a **fast trigger, not a verdict**. The confirmed
identification of *who* it was still comes from the normal analysis pipeline
afterwards. Every enabled watcher also runs a second, *preliminary* name
stage (see below). Its guess is kept only as a live record — you see it on
Today and in the live day view — it is never used for learning and never
overrules the real verdict.

## How the signal forms

1. **Stream** — the watcher decodes the camera stream (GPU decode where
   available) and scales it to the processing resolution you picked for that
   camera (360p / 720p / 1080p / 1440p / 2160p, default 1080p).
2. **Normal rate** — a face detector checks every Nth frame (default: every
   5th). Cheap enough to run continuously.
3. **Burst** — the first genuine face switches the watcher to checking *every*
   frame and opens a track for that spot in the image.
4. **Consistent detections** — once the configured number of spatially
   consistent detections lands in the time window (default: 4 within 2 s), the
   track fires. Consistency means "the same moving head", not a name.
5. **Pose confirmation** — before alerting, a pose model checks that a human
   skeleton actually stands at that spot. This is what rejects cats, headlight
   reflections and bush phantoms.
6. **Alert** — the presence signal goes out on the channels you picked. It
   reports *every* human, known or not.

**Stage 2 — the preliminary name.** While the appearance lasts, every real
face votes: each detected face is compared against your references frame by
frame (the embedding is computed during detection anyway, so this costs
microseconds). A person collects at most one vote per frame. Once the same
person is hit in two different frames at or above the recognition threshold,
and the appearance has passed the pose confirmation of stage 1, the watcher
sends one extra message for that person: title `<watcher> <camera>: recognized`,
text just `<name>` (alert style `worte`, the default; the style `worte_zahlen`
keeps the long form `recognized (live, preliminary): <name> (clear match, 2
consistent looks) [cosine 0.47]`). Stage 1 in the default style likewise says
only the quick-check name or `not recognized` under its "person detected" title.
Both come with a proof picture in which the face that carried the vote is framed. It
fires once per appearance and per person, so two people walking through
together produce two name messages. Stage 1 keeps alerting for everyone
regardless. Proof pictures of stage 1 frame the triggering detection as well.

The watcher also reports its own disturbances: if the stream stops delivering
frames for several minutes, you get a disturbance alert on the same channels,
and a recovery note when frames flow again.

## GPU requirement and the two brakes

Live watchers currently work **with a GPU only** — integrated Intel graphics
(gpu / gpu-legacy images), an NVIDIA card (cuda image) or an AMD card (rocm
image). We are working on a CPU option but can't promise it. On the CPU-only
image the tab shows the tiles as "not available".

**Enabled means running.** There is no computed capacity verdict: only two
hard brakes can refuse a watcher, and both are plain numbers — a watcher cap
(default **5**, raisable up to 20 via `live.max_slots` in the config store for
machines with stronger hardware), and a **RAM floor** taken from the real
container memory limit (one more stream must not push free RAM below the
floor). If the
machine runs hot, nothing is switched off: the engine **throttles at
runtime** by sampling frames more thinly and shows the current throttle level
and utilization on the engine card. The engine's self-measurements (detector
milliseconds, RAM per stream) are shown there too — they inform you, they
don't decide anything.

The **Measure load** button measures the real cost of *one* watcher on *your*
hardware: it runs that camera for 15–30 s with a visible countdown and reports
frames/s, detector time, CPU share, GPU share and RAM delta. The other
watchers are paused during the measurement so the numbers are honest.

## Setting up a watcher, step by step

1. Open the **Live watchers** tab. Tiles are grouped by state — **Running**
   first, then **Ready** (tested, not enabled), **Not set up**, and a
   collapsed **Hidden** group; you can hide tiles you don't care about, and
   optionally group by area. Each running tile shows a small preview refreshed
   every couple of seconds — taken from the watcher's own processed frames, so
   you see exactly what the agent sees — and the tile header shows the real
   stream resolution.
2. **Configure** the camera: choose the source — `proxy` (the go2rtc restream
   via Frigate, the recommended default), `direct` (the camera's producer URL
   discovered via go2rtc) or `url` (a stream URL you enter yourself; any
   credentials in it are masked everywhere they are shown). Pick the
   processing resolution (default 1080p), set the two times (when an
   appearance ends, and the minimum seconds between alerts) and pick the
   notification channels.
3. **Run source test** — runs by itself if it is missing or outdated when
   you press Enable (since 0.1.0.362 the switch accepts, shows "Checking
   source", and the watcher starts on its own once the check passes; if the
   check fails, the switch turns back off and the tile names the reason).
   You can still run it manually at any time. It resolves the source,
   probes the stream, pulls real frames, runs one detector pass and measures
   the camera's **true delivery rate** (frames after the initial buffer
   burst, not raw decode throughput). Results from older versions are marked
   "(throughput, not delivery rate — rerun the source test)". The result is
   bound to exactly this source configuration: change the source or the
   resolution and the test is invalidated.
4. **Measure load** (recommended) — see above; the result stays on the tile
   as your decision basis.
5. **Enable** (works with or without a prior test — a missing or outdated
   check runs automatically). The tile turns green only once the engine confirms that frames
   are actually flowing — never from the saved configuration alone. Nothing
   else to do: the service starts and supervises the live engine itself,
   restarts it if it dies, and tells you on the page when something is wrong.
   (Starting an engine by hand still works for debugging — the page then says
   "standalone engine detected" and the service does not start a second one.)

## Where the results land

Every trigger stores its evidence pictures; a recognized person additionally
gets the proof frame of the name message. On **Today** you see "Recognized
live" cards for appearances with a name; clicking one opens the **live day
view** (`/live_alerts`), which bundles each pass into one card per camera
with *all* stored face pictures and short recap videos.

## Home automation via MQTT

If the `mqtt` channel is selected, every confirmed trigger publishes to

    <prefix>/live/<camera>

where `<prefix>` is your MQTT topic prefix from the Notifications page
(default `verifyd`). The presence trigger payload is JSON:

```json
{
  "ts": 1755000000.0,
  "kamera": "FrontDoor",
  "score": 0.87,
  "bild_anzahl": 4,
  "herkunft": "live_wache",
  "schnell_urteil": {"text": "probably X (preliminary)", "preliminary": true}
}
```

The preliminary name stage publishes its own message on the same topic when
it fires:

```json
{
  "ts": 1755000004.0,
  "kamera": "FrontDoor",
  "art": "name",
  "schnell_urteil": {"person": "X", "cosine": 0.47, "stimmen": 2,
                     "preliminary": true}
}
```

`herkunft` is always present and always `live_wache` for watcher alerts, so an
automation can filter on it without parsing text. (`schnell_urteil` is the
payload key's historic name — it is always included nowadays.) Messages are
**not retained** — a trigger is an event, not a state. In Home Assistant, an
MQTT trigger on `<prefix>/live/<camera>` is all you need to react in well
under a second from the first face.

## Honest limits

- **GPU only for now.** A CPU option is being worked on, without a promise.
- **At most 5 watchers by default** (`live.max_slots` raises the cap, up to 20), and the RAM floor can refuse one more stream.
- **Per camera only.** A watcher sees one stream; the cross-camera scenario
  view stays with the normal analysis.
- **The preliminary name is not a verdict.** The short default texts no
  longer say "preliminary", but the MQTT payload still carries
  `preliminary: true`, Today marks live-only names with "live", and the name is
  never used for learning; the confirmed verdict comes from the normal
  analysis of the full pass.
- **Watchers pause during a load measurement** (15–30 s, shown live with a
  countdown) — that is deliberate, so the measurement is honest.
