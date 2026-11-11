# Usage

Once suslik is running and the wizard is done, everything happens through the web UI at
`http://<host>:8199/` and, in the background, automatically: live watchers keep watching
their camera streams and react while the person is still in the picture, and the full
analysis runs as Frigate produces person events.

## The web UI
The UI has **eleven sections** (top bar): **Activity** (Today / Passes / Events / Unknown),
**People** (your reference library), **Person** (the body-recognition path:
learned material and model status), **Vision** (vision detect), **Live**
(live watchers — see [live-watchers.md](live-watchers.md)), **Areas** (camera groups),
**Learn** (face learning runs, anchors, person learning), **Frigate sync** (the
class-by-class comparison with Frigate's own face library), **Settings**,
**Recognition test** and **System**.

Two buttons sit in the top bar next to the sections: **Calibration** (per-camera bars; shown
in Expert mode only, in Easy mode the page stays reachable at `/kalibrierung` and through each
camera's **Calibrate** button on the Live page) and **Presence** (route `/anwesenheit`) — the
day, person by person, in quarter-hour cells. Red =
that person was confirmed present in that quarter hour (by the event analysis or a live
watcher, shown once), green = the system was running and confirmed nobody, an empty cell =
the system was not running or did not look at that slot (no statement, not "absent"). The
hours outside the day window are one cell per hour; the window is derived from your
sightings (or fixed in Advanced settings). Arrows page day by day back to the first recorded
day; the three switches **All / Camera / Area** narrow the view. Clicking a red cell opens
the pass (or the person's day view for live-only sightings). Recording starts with the
version that introduced the page — earlier days stay empty.

**Activity**

- **Today** — the day at one glance: who was here, from when to when, and whether there
  were strangers. Below the day navigation and the area chips the page shows only cards,
  in three bands across the full width: **Recognized**, **Probably recognized** and
  **Unknown**. Each card has its action at the bottom right; the action belongs to the
  card, so a click anywhere on the card does the same. Card pictures are sent scaled down
  to at most 160 pixels wide.
  **Recognized** has one card per person with at least one confirmation that day (from
  the normal analysis or from a live watcher), newest sighting first: best picture,
  "first–last confirmed HH:MM–HH:MM · N passes · last seen CAMERA HH:MM", and, once the
  presence journal has that day, a small hour bar (red: confirmed present, green: system
  running, nobody seen; always over all cameras, even in an area view) with "present about
  N h". The action is **Change**, and the card opens the person's **Appearances** day view
  (route `/auftritte`). A person only a live watcher has named carries a small "live" mark
  (preliminary, no confirmed pass yet), and the card opens that live alert instead. Twelve
  cards are shown, the rest folds behind "all N people". There are no combined "A & B"
  cards: the person is the unit.
  **Probably recognized** appears when unknown faces of the day closely resemble a known
  person: one card "probably NAME" per person, listing the unknown identities behind it,
  with the action **Check**.
  **Unknown**: faces nobody was recognized for appear as "Unknown N" cards once the
  unknown pool has grouped them, each saying how often that identity was seen before
  ("seen N× before" or "first time here"), with the action **Name**. Behind them come the
  cards of live watchers (next paragraph). The band header counts the identities.
  **Unknown person from a live watcher.** When a live watcher judges an appearance as an
  unknown person, the Unknown band gets a card "Unknown person" with the "live" mark,
  newest first: "seen HH:MM" (or the span, when one card holds several such appearances),
  the camera and the watcher's picture of the first face (the camera picture with the face
  framed, not a cut-out face). Its action is **View**, and the card opens that
  appearance's card in the live day view (`/live_alerts`). The card comes for every
  appearance that started outside the watcher's "Push pause" and in which nobody was
  recognized, or, with "Also report unknown people next to recognized ones" on, in which
  names were recognized but other valid faces gave no name vote. The channel makes no
  difference: a watcher on MQTT only, one without any channel, or one with the "Unknown
  person" switches for Pushover and Telegram off gets these cards too, and there is no
  switch for them. An appearance that starts within the push pause gets no card, and none
  comes when the watcher or the engine stops before the appearance ends. These cards have
  no identity: they cannot be named, they do not say how often someone was seen, and the
  same person can show up several times, next to an "Unknown N" card or next to a person
  card of the same visit. Twelve are shown, the rest folds behind "all N alerts"; the band
  header adds "N live watcher alerts" to the count of identities. Appearances recorded
  before the version that added these cards have none. The page reads the newest 200
  alert groups of the day (in an area view those of its cameras); if the appearance is no
  longer among the newest 200 of the day in the live day view, the click lands at the top
  of that page.
  The page ends with a line giving the number of passes that day and a link to the
  **Passes** tab. On today's date, without any alert channel set up, a line under the
  Recognized band points to Notifications.
- **Passes** (route `/durchgaenge`, between Today and Events) — the numbers and the walks
  of the day. Day navigation and area chips work as on Today; the chosen day and area stay
  when you switch between the two tabs. A row of four numbers comes first: **People
  recognized** (links to the Recognized band on Today), **Passes**, **Events analysed**
  (links to Events) and **Detection rate** (the share of the analysed events with at least
  one checked face, the count in its tooltip); every number explains in its tooltip what
  it counts. One sentence follows with the unknown people and the people probably
  recognized (each a link to its band on Today), the passes with nobody recognized, more in
  archived clusters and the events without a match in recognized passes; in an area view a
  line above it says what the area view covers. Then the list of every walk (events
  grouped by time, across all cameras unless you set a narrower reach per area under
  Areas), newest first, one collapsed row each: time, duration, up to three avatars plus
  "+N", the "+N not matched" footnote, the source tag (via face / via person / live), the
  red body bar for body-only attributions and the vision line. A row starts open only when
  it needs a look: nobody recognized with a serious face, or an alert went out (at most
  three). Inside, each camera line shows at most three names plus "+N", eight camera lines
  are visible and the rest folds behind "all N cameras". Passes whose whole clip contains
  no serious face show a quiet "no usable face in this pass" note instead of a warning
  badge. Under the list, notes count the hidden motion-only passes (a link to Events), the
  detections filtered as non-faces and the likely false triggers per camera.
  Live-watcher statistics live on the Live tab and in System stats.
  A pass still in progress is marked "in progress" on both tabs, which then reload every
  30 seconds, and finalizes once the walk ends.
- **Events** — the flat event list with filters and paging, category badges, ground-truth
  buttons, and video links. Useful for drilling into a single event.
- The former **To label** work list is gone; its address `/offen` now leads to the **Unknown**
  tab, where faces are named per identity (see **People** below). Single events are labeled
  wherever the label buttons appear, for example on the event detail page: besides the person
  buttons and *Stranger*/*?* there is a **No person** button for false triggers (a video with
  nobody in it); one click closes the case and it stops counting as unknown. Passes whose
  whole clip contains no serious face get a quiet "no usable face in this pass" note in the
  list on the **Passes** tab instead of a warning badge and an unknown-visitor card.

**People**

- **Known** — your reference library (the "master"): the people suslik knows and their reference
  images. Also where you can upload photos to bootstrap a person.
- **Unknown** — persistent unknown identities: recurring faces that aren't in your library yet,
  grouped over time so you can promote one to a known person.
- **Suggestions** — enrollment suggestions. suslik proposes reference faces to add for known
  people after each walk; **"Apply all recommended"** accepts all suggested faces at once.
  Applying stays a manual click (a safeguard against poisoning the library with bad crops).
- **Quality** — reference-library quality reports (finding no-face, mislabeled, or confusable
  references so you can clean the master up). Every reference carries a quality value; weak
  pictures are flagged, and a progress bar shows the check while it runs.

**Frigate sync**

- **Frigate sync** (route `/sync_auswahl`) — the one place where your reference library and
  Frigate's own face library are compared, in both directions. The page opens with a balance
  line that adds up across all classes: how many reference images you have, how many are
  already in Frigate, how many are ready to transfer, how many Frigate rejected, how many you
  deleted in Frigate, how many were sent earlier, how many you deselected, and how many exist
  only in Frigate. The working order is: read the balance, tick what you want to send, confirm,
  then read the result per image.
  - *Ready to transfer* — candidates are shown as thumbnails grouped per person, individually
    tickable, with **Select all** / **Deselect all**. Before anything goes out, suslik runs
    every candidate through a face detector the way Frigate will on arrival (the **pre-check**:
    it runs in the background, caches its verdict per image, and the page reloads when it is
    done). Images that would likely be refused start unticked but stay clickable, because
    Frigate's verdict is the truth and suslik's detector is a different model.
    **Transfer N selected to Frigate** asks for confirmation and then shows, per image, whether
    it was uploaded or the exact reason Frigate refused it.
  - *Deleted in Frigate* — your decision, nothing happens on its own. **Offer again** puts the
    image back on the candidate list (the next sync, including the automatic one, sends it),
    **respect the deletion** keeps it out for good.
  - *Exported earlier* — Frigate renames every reference it accepts, so suslik cannot tell by
    name whether these are still on the other side, and says so instead of guessing.
  - *Only in Frigate* — **Import them into suslik** copies them into your library; nothing in
    Frigate changes. Import deliberately: your own earlier exports show up here too, renamed,
    and re-importing one duplicates it.
  - *Deselected* — images you skipped on purpose. The automatic sync skips them as well, and
    **restore** puts one back on the candidate list.
- **Frigate only accepts uploads while its own face recognition is on.** A live line at the top
  of the page reads that from Frigate as the page loads (on, off, or unknown). With
  `face_recognition.enabled: false` in your Frigate config every upload comes back as HTTP 400.
  Importing *from* Frigate works without it.
- **Read-only mode blocks the transfer**, and it is the default. The page says so and the
  transfer button stays disabled until you switch writing on with the **Frigate write-back**
  control on the System page. Comparison, pre-check and import work either way.
- **One sync at a time.** Starting a second run while one is going is refused with a clear
  message, and the automatic export skips a round instead of racing a running transfer.

**Settings**

- **Cameras** — the cameras from Frigate, with the zone condition as a checkbox per camera.
- **Notifications** — configure the alert channels (Pushover, Telegram, MQTT) and pick which
  judgment categories raise an alert. For Telegram you can choose the attachment: a short
  **video** clip (falls back to an image and says so) or **image only** (no transcoding —
  lighter on weak hardware). Each channel has a **Test** button; stored secrets are shown masked.
  The Pushover card shows the channel state: **off** while token or user key is missing (nothing
  is sent, one startup log line), **paused** after 5 rejections in a row (save the tab or run a
  successful Test to resume), otherwise active.
  This attachment choice applies to the service's own alerts. Live watchers use the same
  channels but pick them **per watcher** on the Live tab, and have their own switches for
  known and unknown people, picture and video
  ([live-watchers.md](live-watchers.md#pictures-and-video-on-pushover-and-telegram)).
- **Recognition chain** — its own page: the order and conditions of the recognition
  paths (face → person → vision), each step with a plain-language condition. It used to
  sit inside Advanced.
- **Advanced** — the remaining configuration values and a clean restart.

**System**

- **System** — the status "traffic light", the **Sync with Frigate** card (the same balance
  line as the Frigate sync page plus **Open Frigate sync**; the buttons themselves live on that
  page now), a QC report, the
  **configuration backup/restore** card, the **full backup** card (one portable archive with
  everything you taught the installation — settings, face references, learning results, the
  whole person-recognition material and models — plus a restore that replaces those parts
  and moves the previous ones into `state/archiv/`, deleting nothing), the **Frigate write-back** control (read-only
  is the safe default), **Re-run setup wizard**, and a link to this documentation.
- **System stats** (also the **System stats** button in the top bar) — the load of the machine
  and the state of recognition, one sample per minute, kept for 48 hours. Anything this
  hardware cannot measure says so instead of showing a zero. The **RAM** card shows what the
  program really occupies (processes + graphics memory) as the big number; the **file cache**
  is a separate line: the kernel keeps recently read clips in memory and hands it back the
  moment something else needs it, so a large file cache is neither a leak nor an error. A
  percentage appears only if the container has a memory limit, and then it is the docker
  stats view (cache included, labelled as such). **Event queue** shows the MQTT waiting line;
  in poll mode nothing waits there (events come straight from the sweep), so the card says so
  instead of a zero. **Backlog** shows how many events of the current catch-up are still open,
  with a history bar so you can see it drain. The **Live** button next to the title refreshes
  the page every 5 seconds with fresh samples for up to 5 minutes, then it switches back on
  its own; leaving the page ends it as well.

## Enrollment (teaching suslik a person)

suslik learns from your own camera footage — you don't upload photos. This section covers
the day-to-day path; to work through your event history in one guided go, see
[Learning people](learning.md). The flow is person-centric:

1. Let the person appear on camera normally. After each walk, suslik collects the best faces
   (up to three per event), generates enrollment suggestions (**People → Suggestions**) for
   people it already knows, and clusters faces it doesn't recognize into the **Unknown** tab.
   For a known person, the check button next to an event picture on their page goes further:
   it looks at every frame of that event, measures face quality with a reference-free score
   and offers the best new pictures grouped by view (left, front, right). A second button on
   the pass card does the same for the other events of that walk — several cameras give the
   better angle. The pictures are prepared when you ask for them, not in the background: the
   check takes priority over other jobs and shows a progress bar with the elapsed time and,
   once suslik has measured its own speed on your machine, an estimate.
2. To add a **new** person, the shortest path is the **Today page**: an *Unknown* card shows a
   sample face and is clickable — the panel that opens lets you pick exactly the faces you want
   (walkthrough faces first) and assign them to a new or existing name. Alternatively, promote a
   whole unknown cluster to a name on the **Unknown** tab.
3. Review the suggested faces and apply the good ones. Only clear, unambiguous faces make good
   references — suslik's suggestions are filtered, but the final accept is yours.

On the **Unknown** tab, *"same person?"* rows show faces of both identities so you can answer
**Merge** or **Different** at a glance; *Different* is remembered permanently. Clusters that turn
out to be static objects (a wheel arch, a light pattern the face detector keeps firing on) are
quarantined automatically into their own collapsed bucket. A person can also be **deleted
entirely** (name + references) from their detail page; like removing a single picture, this moves
the reference sets into the archive `state/archiv/refquelle/` — nothing is deleted, and the archive is
part of the full backup.

A recurring background job keeps the unknown pool tidy and re-checks it against your current
references. On an **event page**, images are grouped per person, and groups whose best match is
below the "unknown" threshold sit under a visible divider — *weak matches, the name is a guess*.

## How a judgment is reached

For each person event, suslik pulls the recorded clip, searches across frames for the best face,
and matches it against your references over time. It reports one of:

- **recognized** — a known person confirmed by enough consistent frames.
- **unknown** — a face was seen but didn't match any reference confidently.
- **disagreement** — suslik confirms a *different* person than Frigate's label (the case suslik
  exists to catch).
- (plus bookkeeping categories for "Frigate labeled but no usable face", "both unknown", etc.)

Alerts fire only for the categories you enable (disagreement by default), with a global cooldown
so continuous presence doesn't spam you.

Live watchers alert on a separate path these categories do not govern. MQTT reports every
person at the first face. Pushover and Telegram report a known person as soon as the name
stage has recognized them ("Face of <name> recognized on <camera>", once per appearance
and person); from the second name on, a list of all names of the appearance follows. When
nobody was recognized, they send "Unknown person on <camera>" once the appearance is over.
All of these go to the channels picked per watcher, and each watcher has switches for
which of the two kinds Pushover and Telegram get. By default Pushover and Telegram carry a
small picture, and Telegram also gets a video of the appearance once it is over; when
there is a video, it carries the unknown person note instead of a separate alert. The
per-watcher "Push pause" applies to Pushover and Telegram only: it
starts with the first face of a reported appearance, and appearances that start before it
runs out get no video and no unknown person alert. Names have their own pause of the same
length, per person and watcher, so a name still goes out in such an appearance. MQTT never
pauses; its messages are described in
[live-watchers.md](live-watchers.md#home-automation-via-mqtt). The alert style
`worte_zahlen` keeps the detailed texts with scores, seconds and the "preliminary"
wording; the MQTT messages are the same in both styles.

## Reading the startup self-check

If something looks wrong, the container log is the fastest diagnosis:

```bash
docker logs -f suslik
```

The service prints an 8-step self-check on start: config, hardware (which accelerator was found
and whether it engaged), backend bind, recognition model, Frigate connection, references, a
per-backend benchmark, and a compute check that each model produces on its device what the CPU
produces — ending in `========== ready ==========`. It contains no secrets, so it's
safe to share when asking for help.

If a **sync** reports a problem, `http://<host>:8199/sync_diagnose` (linked from the Frigate
sync page and from the System card) returns one plain-text bundle: suslik's last export report,
the current sync status, the last export and import stderr, the sync lines of the service log,
and the tail of Frigate's own log fetched over Frigate's API. It is made to be pasted into an
issue. Unlike the startup self-check it does contain your person names, camera names and local
addresses, so review it before posting it publicly.

Next: [architecture.md](architecture.md) · [hardware-acceleration.md](hardware-acceleration.md)
