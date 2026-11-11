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

A watcher computes each frame it picks the same way the analysis worker
computes a recorded event: the same models, the same bars per camera and the
same voting rule (the "stack"). Only the door works differently, because a
live stream cannot be rewound.

1. **Stream** — the watcher reads the camera stream at the resolution the
   camera delivers, with hardware decoding where the image supports it and a
   logged fallback to software decoding. A source without a plausible frame
   rate is refused (its slot shows the watcher as disturbed), because step 2
   needs it.
2. **Frame grid** — it computes frames on the same sampling grid as the
   analysis (`fps_sample`).
3. **Door** — after a frame with a face that reaches the door bar for a name
   not yet recognized, the watcher computes *every* frame for the next
   `tuer_fenster` frames; a new such face extends the window, and a cap per
   stack window limits it. Frames that pass while a frame is being computed
   stay uncomputed.
4. **Stack** — every valid face (a recognition score, no false detection,
   large enough, quality and head pose above the camera's bars) votes for its
   best person, if that score reaches the vote bar and beats the second-best
   person by at least `stapel_abstand`. Two faces of the same person in one
   frame give two votes.
   A face that resembles nobody you know (it votes for no name, and its best
   person stays below the door bar) is valid only if it also passes the
   **second look**: the detector looks at that spot once more, cut out with
   a margin and brought to a fixed size, and must find a face there again
   with at least the camera's detection score ("Detection score" on the
   calibration page). This keeps leaves, bushes and similar things that the
   detector took for a small face from counting as an unknown person. Faces
   that vote for a name, or reach the door bar, are not looked at twice, so
   names and the door are not affected. The price: a stranger who keeps the
   head bowed during the whole visit counts as a face less often. Something
   that is not a face but resembles a known person is not caught by the
   second look. The analysis worker applies the same second look.
   A name counts as recognized once it has `stapel_stimmen` votes (factory
   value 3, range 1 to 10). The stack collects from the first real face and
   starts afresh every 60 s, when the appearance ends, and when references or
   bars change. Names already reported in the appearance stay reported.
5. **First face** — the first valid face of an appearance (valid as in
   step 4, second look included; the vote bar and `stapel_abstand` do not
   apply here) triggers the
   message `face_found` (MQTT). It reports every human, known or not, and
   carries a preliminary name only if that face's best person reaches the
   recognition threshold (`win_thresh`) and beats the second-best person by
   `stapel_abstand`. Pushover and Telegram get nothing at this moment. If the
   appearance starts outside the pause "Push pause" (see "MQTT does not
   pause"), it counts as reported: it can get an "Unknown person" alert at its
   end (step 7), and the recording of its Telegram video starts here (see
   "Pictures and video on Pushover and Telegram").
6. **Name message** — when a name reaches `stapel_stimmen` votes, the watcher
   sends `face_recognized` (MQTT), once per appearance and person, and right
   away the name alert on Pushover and Telegram, with the picture of that
   person's best valid vote and the face framed. Two people walking through
   together produce two name messages. From the second name of an appearance
   on, each name alert is followed by one more message that lists all names of
   the appearance so far, without a picture. Pushover and Telegram get both
   only when the watcher's `pushover_known` or `telegram_known` is on, and they
   hold a name back while its own pause runs (see "MQTT does not pause").
7. **End** — the appearance ends when no face has been seen for "Visit ends
   after" (`ende_ohne_gesicht_s`, factory value 10 s, range 3 to 120 s). MQTT
   then gets `appearance_ended` (see below). If nobody was recognized in a
   reported appearance, Pushover and Telegram now get "Unknown person on
   <camera>" with a small picture of the first face, on the channels whose
   `pushover_unknown` or `telegram_unknown` is on. Telegram gets this alert
   only when the appearance has no video; otherwise the video carries the
   note. The alert never carries a preliminary name. With `unknown_with_known`
   on, it also comes when names were recognized but other valid faces of the
   appearance gave no name vote, then without a picture. The video of the
   appearance goes out at this point as well, or as soon as its recording is
   done.

Every name, list and unknown person alert starts with one line, and so does
the video. Pushover shows it as the title, Telegram as the first line of the
message or the caption:

| Message | Line |
|---|---|
| Name alert | `Face of <name> recognized on <camera>` |
| List of names | `Faces of <name A> and <name B> recognized on <camera>`; with three or more names `Faces of <A>, <B> and <C> recognized on <camera>` |
| Unknown person | `Unknown person on <camera>` |
| Video | the name alert line for one name, the list line for several, `Unknown person on <camera>` when nobody was recognized |

In the default alert style `worte`, Pushover puts below that line only
`<name>` for a name alert, the names separated by commas for the list, and
`not recognized` for an unknown person; Telegram sends just the line for all
three. The style `worte_zahlen` uses the same lines and puts the long texts
below them on both channels. Its name alert reads `recognized (live,
preliminary): <name> (clear match, 3 consistent looks) [cosine 0.53]`, its
unknown person alert gives only the numbers of the first face (`1 face in <s>
s (score <score>, <ms> ms)`) and never a name, and its list gives the names.
The video has only its line in both styles. When `unknown_with_known` is on and
faces without a name were seen next to recognized names, a second line
`Unknown person on <camera>` follows. The MQTT messages do not depend on the
style.

The watcher also reports its own disturbances: when the stream stops
delivering frames for several minutes, when processing fails, or when the
watcher thread dies. You get a disturbance message on the same channels, and a
recovery note when frames flow again. At most one goes out per watcher every
10 minutes; a held-back state follows once that time has passed. These
messages keep the watcher name: Pushover titles them `Live watcher <camera>:
disturbance`, Telegram puts `Live watcher <camera>:` in front of the text.
They carry no picture.

## Pictures and video on Pushover and Telegram

Each watcher has nine settings for what Pushover and Telegram get:

| Key | On the watcher page (Push messages) | Factory value | Effect |
|---|---|---|---|
| `pushover_known` | Recognized person, column Pushover | on | Pushover gets name alerts and the list of names. |
| `telegram_known` | Recognized person, column Telegram | on | Telegram gets name alerts and the list of names. |
| `pushover_unknown` | Unknown person, column Pushover | on | Pushover gets "Unknown person" at the end of an appearance. |
| `telegram_unknown` | Unknown person, column Telegram | on | Telegram gets "Unknown person" at the end of an appearance that has no video. |
| `unknown_with_known` | Also report unknown people next to recognized ones | off | "Unknown person" also comes when names were recognized and other valid faces gave no name vote, then without a picture. Applies to both channels. |
| `pushover_image` | Attach picture, column Pushover | on | Name and unknown person alerts on Pushover carry the picture. Off: text only. |
| `telegram_image` | Attach picture, column Telegram | on | Name and unknown person alerts on Telegram come as a photo with the line as caption. Off: a text message. |
| `telegram_video` | Attach video, column Telegram | on | Telegram gets one video per reported appearance, whether anyone was recognized or not. |
| `video_s` | Attach video, the number next to the switch (Video length) | 10 | Length of that video in seconds, 3 to 60. |

`unknown_with_known` is off by default because a face without a name next to
a recognized person can easily be that person in a poor picture. Whether
Pushover or Telegram is used at all is still decided by the switches
Pushover and Telegram at the head of their columns.

All nine are on the watcher page in the section "Push messages". It is a
table: the rows are Recognized person, Unknown person, Attach picture and
Attach video, the columns are Pushover and Telegram, each headed by the
switch of its channel; a channel that is switched off shows its column
dimmed. Attach video exists for Telegram only. "Also report unknown people
next to recognized ones" sits below the table because it applies to both
channels. Save stores them. A video length outside
3 to 60 seconds, or one with a fraction, is refused with a message, and
nothing of that save is stored. The same keys are in the config store
`config/config.json` in the data folder, in the block of the camera under
`live` → `guards`; a missing key means the factory value, and a `video_s`
outside 3 to 60 written there by hand is clamped, with a log line. The engine
notices the changed store and applies the nine keys without restarting the
watcher. For an appearance that is already running, what was decided at its
first face stays: a video that has started is still sent and keeps its
length, and "Unknown person" only has a picture if a channel wanted one at the
first face.

**The picture** is a frame with the face framed: for a name alert that
person's best vote, for "Unknown person" the first valid face of the
appearance (valid as in step 4 of "How the signal forms", second look
included). The watcher scales it down to at most 720 lines (aspect ratio
kept, never enlarged) and sends it as a JPEG with quality 80, straight from
memory. It makes the small picture of the first face only when a channel
wants the unknown person alert with a picture. The evidence picture on disk
keeps the camera's resolution; Today and the live day view show that one. If
the small picture cannot be made, the alert goes out without it and the log
gets an ERROR line. The list of names never has a picture, and neither has an
unknown person alert next to recognized names, because the watcher keeps no
picture of the face without a name.

**The video** starts with the frame of the first face of a reported
appearance, without a lead-in, when Telegram is among the watcher's channels
and `telegram_video` is on. It covers `video_s` seconds from there, with at
most 3 frames per second. Its height comes from the Telegram video height on
the Advanced page (`telegram_hoehe`, 720 by default, or 480); a smaller camera
picture is not enlarged. It is sent when the appearance is over (no face for
"Visit ends after") and the recording is done, whichever comes later. Its
caption is the line from the table above.

- There is one video per appearance and watcher, and only for a reported
  appearance. A name alert in an appearance that started within "Push
  pause" brings no video.
- A watcher works on one video at a time. A second reported appearance gets
  none while the previous video is still being recorded or encoded.
- When the appearance has a video, Telegram gets no separate "Unknown person"
  alert; the caption of the video says it. What counts is whether the
  recording started, not the value of `telegram_video` at the end. If the
  video fails, Telegram gets no unknown person note at all.
- If the watcher is switched off, deleted or restarted for a new source while
  it records, there is no video. If the recording was already done, the video
  is sent, as long as the watcher still exists and Telegram is still among its
  channels. When the whole engine stops, nothing more is sent; a finished
  video stays on disk.
- The video is encoded with libx264 on the CPU at the lowest priority
  (`nice 19`), in its own thread, the same way on every image variant; the
  recognition does not wait for it. It is stored as
  `live/<camera>/<stamp>_T<n>.mp4` in the data folder, the live day view links
  it, and `live_retention_d` removes it with the evidence pictures.
- A finished video gets an INFO line `VIDEO` in the camera log with frames,
  seconds, bytes, dropped frames and encoder CPU seconds. A failed video
  (encoder, disk, or Telegram refusing it) gets an ERROR line and counts in
  `video_failed` in the live status file `state/live_status.json`. A video
  above Telegram's size limit (49 MiB) is such an error; the watcher does not
  send a photo or text instead.

## GPU requirement and the two brakes

Live watchers are built for a **GPU** — integrated Intel graphics (gpu /
gpu-legacy images), an NVIDIA card (cuda image) or an AMD card (rocm image).
On the CPU-only image they run in **CPU mode**, with limits: the quick check
typically takes 1–2 s (a GPU build reacts in under a second), and additional
watchers slow each other down, so start with one. A GPU image that finds no
usable GPU does not fall back to this mode: the page then says "Not available
on this build" and names the reason (check device passthrough and host
drivers).

**Enabled means running.** There is no computed capacity verdict: only two
hard brakes can refuse a watcher, and both are plain numbers — a watcher cap
(default **5**, raisable up to 20 with `live_max_slots` on the Advanced page, for
machines with stronger hardware), and a **RAM floor** taken from the real
container memory limit (one more stream must not push free RAM below the
floor). If the
machine runs hot, nothing is switched off: the engine **throttles at
runtime** by sampling frames more thinly and shows the current throttle level
and utilization in "Engine and load", the collapsed block at the bottom of the
Live watchers page. The engine's self-measurements (detector
milliseconds, RAM per stream) are shown there too — they inform you, they
don't decide anything.

The **Measure load** button measures the real cost of *one* watcher on *your*
hardware: it runs that camera for 15–30 s with a visible countdown and reports
frames/s, detector time, CPU share, GPU share and RAM delta. The other
watchers are paused during the measurement so the numbers are honest.

## Setting up a watcher, step by step

1. Open the **Live watchers** tab. The title line shows the live engine:
   green "Live engine: running" with the number of active watchers, red
   "Live engine: not running", or "Not available on this build". Below
   it is the slot bar. There are as many slots as watchers may run at once
   (`live_max_slots` on the Advanced page, 5 by default, at most 20), and
   always enough to show the highest slot number in use. Each slot button
   shows its number, the camera and the state of its watcher in the colour of
   that state; a camera that is set up here but not in Frigate right now is
   yellow, unless it is disturbed. A free slot shows "Live N" and "free".
   Clicking a slot shows it below the bar. If you changed fields without
   saving, the page asks first ("Live N has unsaved changes.") with **Save and
   switch**, **Discard** and **Stay here**; as long as fields are unsaved, the
   page does not reload by itself either.
2. **Assign camera** on a free slot ("Live N is free"): choose one of the
   cameras that have no slot yet and press the button. A camera has at most
   one slot, and a slot at most one camera. An occupied slot shows the
   settings of its camera, called the watcher page in this guide. The
   settings belong to the camera, not to the slot: **Clear slot** in the head,
   or choosing another camera in the **Camera** list next to it, frees the
   slot and keeps every setting of the camera. Both work only while the
   watcher is off. The address `/live/<camera>` opens the slot of that camera;
   a camera without a slot gets the first free slot with it preselected, and
   when every slot is taken the page says so. A camera that is switched on
   while it has no slot gets the lowest free slot; with no slot free, the
   switch is refused. When you update from a version without slots, the
   watchers that are switched on get the slots from 1 in the order of their
   names, once; if they are more than the slots, every one still gets a
   number and the log warns, and a number above the limit can be cleared once
   its watcher is off.

   The head of the watcher page shows the live picture while the watcher
   runs, refreshed every 2 seconds from the watcher's own processed frames, so
   you see what the watcher sees; otherwise it shows what the last source test
   saw. Next to it come the camera name, the state and, when known, the frame
   rate, "not in Frigate" when Frigate does not list the camera right now, the
   counters since the start, and when the source was last tested, with a link
   to test it again. On the right are Save and Enable or Disable, and the
   note "unsaved changes" while fields are changed. Below come two columns:
   on the left Push messages (with "Push pause"), on the right Home Assistant
   (MQTT), Visit (with "Visit ends after") and Frigate (optional). MQTT is
   switched on with "Send to Home Assistant", Pushover and Telegram with the
   switches at the head of their columns. Two sections at the end are
   collapsed and show their main values in the title line: Advanced, with the
   connection, power saving and extra analysis, and Diagnostics, with the
   source test, the load measurement, the calibration values and the
   calibration samples. The connection is one of `proxy` (the go2rtc restream
   via Frigate, the recommended default), `direct` (the camera's producer URL
   discovered via go2rtc) or `url` (a stream URL you enter yourself; any
   credentials in it are masked everywhere they are shown). Save stores every
   field of the watcher page at once. "The settings on the watcher page" below
   explains them. At the very bottom of the Live watchers page, collapsed, is
   "Engine and load" (see "GPU requirement and the two brakes").
3. **Run source test** — runs by itself if it is missing or outdated when
   you press Enable (since 0.1.0.362 the switch accepts, shows "Checking
   source", and the watcher starts on its own once the check passes; if the
   check fails, the switch turns back off and the head of the watcher page
   marks "last test failed"; Diagnostics shows the reason).
   You can still run it manually at any time. It resolves the source,
   probes the stream, pulls real frames, runs one detector pass and measures
   the camera's **true delivery rate** (frames after the initial buffer
   burst, not raw decode throughput). Results from older versions are marked
   "(throughput, not delivery rate — rerun the source test)". The result is
   bound to exactly this source configuration: change the source and the
   test is invalidated.
4. **Measure load** (recommended, under Diagnostics) — see above; the result
   stays in Diagnostics as your decision basis.
5. **Enable** (works with or without a prior test — a missing or outdated
   check runs automatically). The slot turns green only once the engine confirms that frames
   are actually flowing — never from the saved configuration alone. Nothing
   else to do: the service starts and supervises the live engine itself,
   restarts it if it dies, and tells you on the page when something is wrong.
   (Starting an engine by hand still works for debugging — the page then says
   "standalone engine detected" and the service does not start a second one.)

## The settings on the watcher page

**The visit.** A visit starts with the first face the watcher finds on the
camera, and every further face keeps it open. It ends when no face has been
seen for the time under "Visit ends after" (step 7 in "How the signal
forms"). The end resets the names: a person can be recognized again in the
next visit, and the push pause decides whether Pushover and Telegram report
the name again. The visit has nothing to do with the door of step 3, which
decides which frames are computed. The watcher page says "visit", while MQTT
(`appearance_ended`) and the rest of this guide say "appearance". Both mean
the same thing.

**Frames per second and minimum votes.** The section "Visit" shows these two
values in one line ("Same for all cameras: …") but does not change them. They
apply to every camera and to the analysis of recorded events alike. The link
"Configuration" in that line opens the Advanced page, where you set them; the
Advanced section of the watcher page does not have them. `fps_sample` is the
sampling grid of step 2, `stapel_stimmen` the votes a name needs (step 4).

**Push pause** (`wieder_scharf_s`, factory value 120 s, 0 to 3600 s). It
holds back Pushover and Telegram only; "MQTT does not pause" below describes
it in full.

**Frigate (optional).** "Create event in Frigate" is off by default. When it
is on and the watcher recognizes a name (step 6), suslik creates its own event
in Frigate for this camera, with the name in the sub label, and ends it when
the visit ends. It does not touch Frigate's own events, and it does not
depend on Pushover or Telegram. The event is written in the background, so
the watcher never waits for Frigate; when too many are waiting, new ones are
dropped and the log warns about it. In read-only mode (`frigate_read_only`,
the default) nothing is written. "Gap per person" is the least time between
two events for the same person on this camera; empty means the push pause.

**Power saving.** "Only look when something moves" is on by default. Between
visits, a frame of the sampling grid goes to face detection only when the
watcher sees motion in it. The motion check works like Frigate's, on the
brightness of a small copy of the picture. During a visit, and while the door
of step 3 is open, the motion check is skipped; the frame grid of step 2, the rule
of step 3 and the load protection still apply. Someone standing
perfectly still makes no motion, so the watcher looks anyway after the time
under "Look anyway every" (1 to 600 s; empty means the time under "Visit ends
after"). "Motion sensitivity" is the brightness change that counts as motion
(1 to 255), "Smallest moving area" the size a moving spot needs (1 to 10000);
empty means Frigate's default values. Smaller numbers make the watcher look
more often. These values belong to this camera only. With the switch off,
the motion check is off; everything else stays as described.

**Extra analysis.** "Replaces the event analysis" is off by default. When it
is on, suslik skips the analysis of recorded Frigate events from this camera,
because the watcher already looks at the same stream. This holds only while
the watcher is enabled and actually running: when it is disturbed or the
engine stops, the events are analysed normally again. A name that Frigate
itself has put on an event is always checked. Events that this watcher
created in Frigate ("Create event in Frigate") are skipped as well, although
they carry a name, unless "Re-check own Frigate events" is on; that second
switch matters only while the first one is on. A skipped event stays in the
event list, marked "Handled by live watcher".

**The preliminary name.** At the first face of an appearance the watcher
makes a quick guess from that one face (step 5). MQTT carries it in
`face_found` (`schnell_urteil`), and the live day view can show it on the
line of the first face. Pushover and Telegram never send this guess. They
name a person only after the votes are in (step 6): in the name alert, in the
list of names after it and in the title of a Telegram video. "Unknown person"
never carries a name. The guess is never used for learning.

## Where the results land

Every trigger stores its evidence pictures; a recognized person additionally
gets the proof frame of the name message. The **live day view**
(`/live_alerts`) bundles each pass into one card per camera with *all* stored
face pictures and, where Telegram video is on, the video of the appearance.
On **Today**, a person a watcher has named gets a person card in the band
Recognized, with the mark "live" as long as no confirmed pass exists; that
card opens the live day view.

An appearance the watcher judges as an unknown person gets a card "Unknown
person" in the band Unknown on Today, which opens its card in the live day
view. The judgment is the one behind the "Unknown person" alert (step 7)
without the channel part: the appearance started outside the push pause, and
nobody was recognized, or names were but `unknown_with_known` is on and other
valid faces gave no name vote. The card comes whatever the watcher reports
on, also with MQTT only, without any channel, or with `pushover_unknown` and
`telegram_unknown` off. For this the watcher marks the line of such an
appearance in its alert log `live/meldungen.jsonl` (in the data folder) with
the field `"unbekannt": true`: each line of an "Unknown person" alert that
Pushover or Telegram accepted carries the mark; if no channel accepted one,
the watcher writes exactly one line with the channel "none", the picture and
the time of the first face, and the same mark. Nothing extra is sent for it.
No line, and so no card, comes for an appearance within the push pause or
when the watcher or the engine stops before the appearance ends; the line of
the video carries no mark. Lines written before the version that added the
mark have none. The Today card has no identity, so it cannot be named there;
the details are in [usage.md](usage.md).

The "Unknown person" alert and the video are logged with the time of the
first face, so they land on the card of their appearance and do not stretch
it. A watcher without MQTT logs the first face of a reported appearance as
"not sent (no channel)"; the card shows that only as long as no channel got
anything from the appearance. Because the unknown person line with the
channel "none" carries the time of the first face, the card of such an
appearance can start a few seconds earlier, and in rare cases count one
trigger more. The System page counts sent alerts per channel (Pushover,
Telegram, MQTT), videos included; lines with the channel "none" are not
counted there. When an appearance starts before
midnight and its unknown person alert or video goes out after midnight, that
alert counts for the day before.

## Home automation via MQTT

A watcher with the `mqtt` channel publishes every message to

    <prefix>/live/<camera>

where `<prefix>` is your MQTT topic prefix from the Notifications page
(default `verifyd`). QoS 0, **not retained**: a message is an event, not a
state. What the broker does not receive is not sent again.

Every message is a JSON object. Since version 0.1.1.058 each one carries the
field `event`, and `herkunft` is always `live_wache`. An automation triggers on
the topic and tells the messages apart by `event`, without parsing any text.
The older fields keep their names and values.

### The five messages

Per appearance they come in this order:

| `event` | When |
|---|---|
| `face_found` | The first valid face of an appearance (valid as in step 4 above, second look included), once per appearance (step 5 above). |
| `face_recognized` | A name has reached `stapel_stimmen` votes; once per appearance and name. |
| `faces_recognized` | Right after every `face_recognized`, already after the first one. |
| `appearance_ended` | The appearance is over (see below). |
| `disturbance` | The watcher is disturbed, or has recovered. |

Within one frame, `face_found` comes first, then for each new name
`face_recognized` followed directly by `faces_recognized`. `appearance_ended`
comes after the last message of its appearance and before the first message
of the next appearance on the same camera.

**`face_found`** — `score` is the detection score (three decimals),
`bild_anzahl` is always 1. `schnell_urteil` is present when names are allowed
and the face has a candidate; `person` is the preliminary name, or `null`
when the best candidate is below the bar or too close to the second-best:

```json
{
  "ts": 1767268800.4,
  "kamera": "front_door",
  "score": 0.812,
  "bild_anzahl": 1,
  "schnell_urteil": {"text": "probably Probe-P1 (preliminary quick check — clear match)",
                     "preliminary": true, "person": "Probe-P1"},
  "event": "face_found",
  "herkunft": "live_wache"
}
```

**`face_recognized`** — `stimmen` is the vote count at that moment, `cosine`
the best score of that person (three decimals), `stufe` the level at that
moment (see below):

```json
{
  "ts": 1767268801.6,
  "kamera": "front_door",
  "art": "name",
  "schnell_urteil": {"person": "Probe-P1", "cosine": 0.534, "stimmen": 3,
                     "preliminary": true, "stufe": "clear"},
  "event": "face_recognized",
  "herkunft": "live_wache"
}
```

**`faces_recognized`** — `faces` lists every name of the appearance so far,
in the order they were recognized, each with the `stufe` frozen at the moment
it was recognized (the same value as in its `face_recognized`):

```json
{
  "ts": 1767268803.0,
  "kamera": "front_door",
  "faces": [{"name": "Probe-P1", "stufe": "clear"},
            {"name": "Probe-P2", "stufe": "narrow"}],
  "event": "faces_recognized",
  "herkunft": "live_wache"
}
```

**`appearance_ended`** — `faces` is the final list (empty when no name was
recognized), `duration_s` the seconds from the first to the last face of the
appearance (one decimal), and `reason` is `no_face` when "Visit ends after"
has run out, or `stopped` when the watcher is switched off, deleted, stopped
or restarted after a change of its source, or when the engine stops. `ts` is the moment the end was noticed.

```json
{
  "ts": 1767268815.2,
  "kamera": "front_door",
  "faces": [{"name": "Probe-P1", "stufe": "clear"},
            {"name": "Probe-P2", "stufe": "narrow"}],
  "duration_s": 4.6,
  "reason": "no_face",
  "event": "appearance_ended",
  "herkunft": "live_wache"
}
```

`appearance_ended` comes only when the `face_found` of that appearance was
queued for MQTT and the watcher still uses MQTT at the end. If you add the
`mqtt` channel in the middle of an appearance, the names and lists of that
appearance still come, but no end; if you remove it, nothing more comes.

**`disturbance`** — `state` is `disturbed` or `recovered`. `stoerung` is a
diagnostic text for people; it can contain internal state words, so filter on
`state`, not on the text. At most one disturbance message goes out per watcher
every 10 minutes; a state held back in that time follows afterwards, with a
note on how many changes were held back.

```json
{
  "ts": 1767269400.0,
  "kamera": "front_door",
  "stoerung": "recovered — frames flowing again",
  "state": "recovered",
  "event": "disturbance",
  "herkunft": "live_wache"
}
```

Disturbances of the whole engine are not sent over MQTT.

### The four levels in `stufe`

`stufe` places the score against the recognition threshold (`win_thresh`):
`clear` at least 0.10 above it, `narrow` from the threshold up to 0.10 above
it, `below` up to 0.10 under it, `none` further below or not measurable.

### MQTT does not pause

"Push pause" on the watcher page starts with the first face of a
reported appearance. Appearances that start before it runs out get no video
and no "Unknown person" alert on Pushover and Telegram. Names have their own
pause of the same length, per person and watcher: Pushover and Telegram report
a person's name on that watcher again only once that many seconds have passed
since its last name alert there. This holds across appearances and does not
depend on the watcher's pause, so a name still goes out in an appearance that
started within it. The list of names follows the decision for the name it
comes after and lists every name of the appearance, held-back ones included.
Name alerts never restart the watcher's pause; 0 means no pause at all.
Disturbances have their own limit (above). If the watcher has no value of its
own for `frigate_abstand_s`, the same time also limits the Frigate events per
person. **MQTT never pauses**: `face_found`, the name messages and the end
come on every appearance.

### Queue and send thread

The watcher puts its MQTT messages into a send queue before it saves the proof
picture, starts a video recording or sends Pushover and Telegram. A separate send thread
publishes them, independently of that other work. A hanging Pushover does not
hold up MQTT.

If the MQTT library refuses a message (for example broker not connected, or no
publisher), the watcher counts it as `mqtt_rejected` for that camera and logs
at most one ERROR line per watcher every 10 minutes. `mqtt_queue` shows how many
messages are waiting. Both are in the live status file `state/live_status.json`
in the data folder and start at 0 when the engine restarts.

## Honest limits

- **Built for a GPU.** On the CPU-only image watchers run in CPU mode with slower reactions (see "GPU requirement and the two brakes").
- **At most 5 watchers by default** (`live_max_slots` on the Advanced page raises the cap, up to 20), and the RAM floor can refuse one more stream.
- **Per camera only.** A watcher sees one stream; the cross-camera scenario
  view stays with the normal analysis.
- **The preliminary name is not a verdict.** The short default texts no
  longer say "preliminary", but the MQTT messages still carry
  `preliminary: true`, Today marks live-only names with "live", and the name is
  never used for learning; the confirmed verdict comes from the normal
  analysis of the full pass.
- **MQTT delivery.** "First" means first in the queue and first handed to the
  MQTT library. When Home Assistant sees a message depends on network and
  broker. With QoS 0 nothing is sent again, and a message lost after the
  library accepted it is not counted in `mqtt_rejected`. If the library hangs,
  MQTT stands still and `mqtt_queue` grows; Pushover and Telegram keep working.
  Messages still queued when the engine stop runs out of time are lost.
- **The end comes late.** With `reason: no_face`, `appearance_ended` comes at
  the earliest "Visit ends after" after the last face, checked every 2 s.
  Switching the watcher off or stopping the engine sends it with
  `reason: stopped` without waiting for that time (on an engine stop, after
  the running watcher threads have been collected). `duration_s` stops at the
  last face, not at that check.
- **Watchers pause during a load measurement** (15–30 s, shown live with a
  countdown) — that is deliberate, so the measurement is honest.
- **Name pause per watcher.** The same person passing two watchers is
  reported by both. When a watcher restarts for a new source or the service
  restarts, its name pauses start empty, and a name can go out again at once.
- **Known and unknown together.** When a known person and a stranger pass
  together, Pushover and Telegram report only the known one, unless
  `unknown_with_known` is on; with it on, a known person in poor pictures can
  also be reported as unknown. Two strangers in one appearance give one
  "Unknown person" alert, because the watcher does not tell unknown faces
  apart.
- **"Unknown person" comes late.** It arrives at the earliest "Visit ends
  after" after the last face, later when someone stays long. If the watcher is
  switched off, deleted or restarted for a new source during the appearance,
  or the engine stops, it does not come.
- **The video is choppy and comes late.** It shows at most 3 frames per
  second. It normally arrives "Visit ends after" after the last face, later
  when someone stays long. Only when the watcher is switched off or restarted
  for a new source and the video is already finished does it go out right
  away. Under load the frames between the face and
  the start of the recording are missing (the face frame itself is there);
  when frames pile up, some are dropped and the video gets shorter and plays
  faster, with a WARNING in the log. If the stream breaks off, the video ends
  early.
- **The video encoder is not capped by `cpu_threads`** (Advanced page); it
  only runs at the lowest priority.
- **Small faces get smaller** in the 720-line picture; the frame around them
  shows where they are.
- **Delivery to the phone is not checked.** suslik counts what Pushover and
  Telegram accept. Whether a Telegram app plays the video inline is not
  tested.
