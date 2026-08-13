# Live watchers

Live watchers are the fastest reaction path in my program: a watcher connects
straight to one camera stream and reacts **while the person is still in the
picture** — long before the recording is finished and analyzed. The goal is a
signal in **under one second** after the first face appears; on the reference
setup the measured range is **199–801 ms**. Use it as a trigger for home
automations (lights, announcements, gates), for example via MQTT.

A live watcher is a **fast trigger, not a verdict**. The confirmed
identification of *who* it was still comes from the normal analysis pipeline
afterwards. The watcher may add a *preliminary* name guess to its alert, but
that guess is never stored, never used for learning, and never overrules the
real verdict.

## How the signal forms

1. **Stream** — the watcher decodes the camera stream (GPU decode where
   available) and downscales it to a working resolution.
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
6. **Alert** — the signal goes out on the channels you picked. If the quick
   name guess is enabled, the alert may say "probably X (preliminary)" —
   preliminary by design; the confirmed verdict comes from the normal analysis.

The watcher also reports its own disturbances: if the stream stops delivering
frames for several minutes, you get a disturbance alert on the same channels,
and a recovery note when frames flow again.

## GPU requirement and capacity

Live watchers currently work **with a GPU only** — integrated Intel graphics
(gpu / gpu-legacy images), an NVIDIA card (cuda image) or an AMD card (rocm
image). We are working on a CPU option but can't promise it. On the CPU-only
image the tab shows the tiles as "not available".

Every active watcher draws real capacity: continuous decoding plus detector
passes. The engine therefore **measures itself** (detector milliseconds, RAM
per stream, GPU budget) and computes how many watchers your machine can run —
shown on the engine card as "capacity: up to N watcher(s)", with a hard upper
cap of 5. Enabling a watcher beyond that capacity is refused with the number,
so you never end up with watchers that are "enabled" but can't actually run.

The **Measure load** button measures the real cost of *one* watcher on *your*
hardware: it runs that camera for 15–30 s with a visible countdown and reports
frames/s, detector time, CPU share, GPU budget share and RAM delta. The other
watchers are paused during the measurement so the numbers are honest.

## Setting up a watcher, step by step

1. Open the **Live watchers** tab. There is one tile per camera known to
   Frigate (plus any watcher you configured earlier).
2. **Configure** the camera: choose the source — `proxy` (the go2rtc restream
   via Frigate, the recommended default), `direct` (the camera's producer URL
   discovered via go2rtc) or `url` (a stream URL you enter yourself; any
   credentials in it are masked everywhere they are shown). Set the two times
   (when an appearance ends, and the minimum seconds between alerts) and pick
   the notification channels.
3. **Run source test** — required before enabling. It resolves the source,
   probes resolution and frame rate, pulls real frames and runs one detector
   pass. The result is bound to exactly this source configuration: change the
   source and the test is invalidated.
4. **Measure load** (recommended) — see above; the result stays on the tile
   as your decision basis.
5. **Enable.** The tile turns green only once the engine confirms that frames
   are actually flowing — never from the saved configuration alone.
6. In this phase the engine itself is started by hand inside the container:
   `python -m core.livewached run`. Supervisor integration is planned; the
   page tells you honestly when the engine is not running.

## Home automation via MQTT

If the `mqtt` channel is selected, every confirmed trigger publishes to

    <prefix>/live/<camera>

where `<prefix>` is your MQTT topic prefix from the Notifications page
(default `verifyd`). The payload is JSON:

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

`herkunft` is always present and always `live_wache` for watcher alerts, so an
automation can filter on it without parsing text. `schnell_urteil` only
appears if the preliminary name guess is enabled. Messages are **not
retained** — a trigger is an event, not a state. In Home Assistant, an MQTT
trigger on `<prefix>/live/<camera>` is all you need to react in well under a
second from the first face.

## Honest limits

- **GPU only for now.** A CPU option is being worked on, without a promise.
- **Engine start is manual in this phase** (`python -m core.livewached run`);
  supervisor integration comes later.
- **Per camera only.** A watcher sees one stream; the cross-camera scenario
  view stays with the normal analysis.
- **The preliminary guess is not a verdict.** It is marked as preliminary,
  never stored, never used for learning.
- **Watchers pause during a load measurement** (15–30 s, shown live with a
  countdown) — that is deliberate, so the measurement is honest.
