# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). History older than 0.1.0.180 has been trimmed from
this file — the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git
history.

## 0.1.0.506 (2026-09-05)

Bundles the internal steps 0.1.0.502 – 0.1.0.505 (0.1.0.504 went out as a CUDA-only
test build for one field installation, 0.1.0.505 ran only on the maintainer's
machines; everything below ships for all variants for the first time in this release).

- Events page: the table no longer pushes the page sideways on tablet-wide screens;
  wide tables scroll inside their own frame.

- **Parallel analysis on both paths.** The number of analysis slots is a setting
  (`analyse_plaetze`, default 2; the GPU page proposes a value from the measured
  memory of your card). Until now only the MQTT path used several slots; the poll
  path (the factory default, and the only path without a broker) analysed one event
  after the other. Both paths now feed one event queue, so several events are
  analysed at the same time on either trigger.
- **One allocator for all GPU work, fair between classes.** Event analysis, the
  learning run and the background jobs (collection, wall clock) take their slots
  from the same allocator. No class may hold every slot while another is waiting
  (N−1 rule); with a single slot this is the old behaviour: analysis first. The
  learning run itself now harvests on several slots at once and gives one back as
  soon as events are waiting.
- **No more false reclaims.** A slot watchdog only reclaims an analysis that has
  really stopped sending its pulse (the pulse starts the moment the slot is taken,
  also while the worker is still busy with the previous job) and grants a grace
  period before it kills. A dead analysis is re-queued once; the reported cause of
  death names the shooter.
- **Honest backlog.** The header shows how many events are waiting and how many are
  being analysed, live. A full queue refuses new events instead of silently dropping
  the oldest, the catch-up bookmark is only released once an event has really been
  analysed (a restart in the middle keeps the rest), and `sweep_limit` /
  `einspiel_deckel` go up to 5000.
- **Support API: re-analyse a time window.** `POST /support/einspielen` takes a
  camera, a time window and a direction (oldest first or newest first, `start` is
  optional when going backwards), pages through Frigate instead of cutting off at
  100, reports what was really queued, marks incomplete windows, and refuses
  unknown fields, nonsense values and oversized bodies (413) instead of guessing.
- **Faster start on CPU-limited hosts.** The face model initialisation respects the
  container's CPU quota and allowed cores; the affinity warnings that flooded the
  logs of some installations are gone, and the cold start got noticeably faster
  where cores are restricted.
- **Much faster learning run on NVIDIA systems.** The feature-norm gate of the
  harvest, which decides which faces are good enough to learn from, used to run on
  the CPU on every machine and took by far the most time of a harvest. On CUDA it
  now runs on the graphics card, checked against the CPU before it is used. The
  device chain now follows the configured backend: on an Intel image with the
  backend explicitly set to `cpu`, the norm stays on the CPU (it used the NPU
  before); `SUSLIK_NORM_DEVICE` overrides this per installation.
  Measured on an RTX 2060: 64.9 s down to 11.8 s per event, with identical results.
  The OpenVINO/Intel chain is unchanged, ROCm stays on the CPU.
- GPU page: the slot list shows what each slot is doing (analysis, learning run,
  background). Systemstatus tile: "Backlog present" instead of "Catching up".

## 0.1.0.501 (2026-09-04)

Bundles the internal steps 0.1.0.382 – 0.1.0.500 (the 0.1.0.414/0.1.0.415 builds
were withdrawn; everything below ships for the first time in this release).

- **Face recognition is greatly improved.** Judgement now works in a sliding
  view window: a person needs one strong moment (an anchor vote) plus supporting
  votes inside that window, instead of a fixed three-second burst. Far-away
  people on wide cameras are recognised where they used to stay unknown, and a
  single lucky frame can no longer name someone. Two people in the same event
  are told apart from one ambiguous face — both get named, while a face that
  merely matches two references almost equally stays honestly unknown. Every
  vote passes the same four sieves in the live watcher and in the event worker
  (face size, two picture-quality bars, head pose), the live watcher processes
  the camera stream at native resolution, and the factory bars were
  re-calibrated on measured material. On first start the calibration rings,
  the per-camera sliders and the live judgement rules are reset once to these
  new factory values, so every installation starts from the same measured
  ground.
- **Presence detection.** The Presence page shows each person's day in quarter
  hours — red was there, green was not, empty means the system was not running.
  Switch between all cameras, one camera or an area, page back 30 days. Marks
  come from event analysis and the live watcher alike.
- **The Today page is rebuilt.** One card per recognised person with a presence
  mini-bar, no more group tiles, compact pass rows, images load as you scroll.
  People recognised live appear as normal cards with a "live" badge.
- Support API: a single event or a time window of a camera can be (re-)analysed
  on demand (`POST /support/einspielen`), for remote testing after an update.

## 0.1.0.381 (2026-08-31)

- **The Brightness check is gone from the learning card.** It was a page of its
  own where you could set the two brightness lines on your own pictures. Across
  714 pictures from a live installation those lines changed the outcome three
  times, and the picture-impression slider on the Calibrate page already covers
  what they were meant for. Two places to tune one effect mostly made it harder
  to tell which of them had done anything. The measurement behind it is
  untouched: brightness is still measured while faces are harvested, a badly lit
  cut-out still sorts behind the well-lit ones and still carries the reason "too
  dark" or "overexposed", and nothing was ever dropped over it. The two limits
  remain yours to change, now in Configuration (`reihung_luma_min` /
  `reihung_luma_max`; 0 switches a side off).


## 0.1.0.380 (2026-08-31)

- **The unknown-person pool now applies the same quality bar as a learning
  run.** It used to collect on face size and detector score alone; whether a
  cut-out showed a face at all, and whether it was good enough to learn from,
  was only checked much later, when you looked at it. On a business site that
  produced unknown groups made of foliage — groups you cannot do anything with.
  Collecting now sieves first and groups afterwards, through the very same two
  gates the learning run uses: the structure and feature-norm lines, and your
  calibration sliders. A candidate that fails does not take up one of the three
  slots per event either, so a real face behind it moves up and reaches the pool
  instead of the leaves. Faces already in the pool are never re-judged and never
  removed retroactively — they were collected without these measurements, and a
  verdict without a measurement would be a silent loss. Cost: three small
  measurements per candidate that would enter the pool (roughly 25 ms, CPU, at
  most a handful per event), never during live recognition.

- **Remote support access reaches your whole data folder now.** Until now it
  handed out a fixed set of named areas — logs, faces, learning runs, state
  files. Whatever we had not named in advance was simply out of reach: when a
  tester's unknown-person pool lived in a folder the list did not mention, the
  supporter could not fetch it at all, and only a new release would have changed
  that. With the switch on, the token now also opens a listing of the complete
  data folder (every file with its path, size and time — no content) and fetches
  any single file from it, or a whole folder as one `tar.gz` stream. Everything
  else stays as it was: read-only, off by default, and every request lands in
  your service log. Your configuration keeps its protection wherever it is
  fetched — under `config/` no secret leaves the machine in plain text, on its
  own or inside an archive, and that now includes the older `config.json.vor_*`
  copies that a named area never covered. Paths that try to leave the data
  folder answer `404`, like anything that does not exist. The flip side is worth
  knowing: raw clips and event history are reachable for whoever holds the token
  now, so keep the switch off except while a support session is running.


## 0.1.0.377 (2026-08-30)

- **New: calibration.** Which faces a learning run keeps was governed by a fixed
  sharpness number — and measured against real judgements it turned out to
  measure almost nothing: on one field installation it threw away 661 of 662
  pictures a human called usable, and what it kept was no better. It is replaced
  by two learned quality measures: picture impression (how clean the image
  looks) and recognisability (how well the person can be identified — this one
  also sorts out half-covered faces). Both run on CPU in milliseconds, only
  during learning runs. The thresholds are yours to set: the Smart-naming card
  now carries a Calibrate button (active once a run is finished) that opens all
  the run's pictures with two sliders — slide until the border feels right,
  apply, and future runs use your thresholds. Factory defaults were calibrated
  on real field material. For measured pictures the two sliders have the
  final say on quality (no side door: the old feature-norm rescue applies
  only to pictures without quality scores). Applying new thresholds
  re-grades the finished run
  right away (auto-named groups get a fresh selection, groups that previously
  failed the bar are retried; hand-named groups stay untouched) and takes you
  back to the learning run. Old runs keep their judgements;
  the feature norm and minimum face size stay as before. Learning runs take a
  few percent longer, because every candidate face is scored by both models
  (CPU only, milliseconds per face, never during live recognition).


## 0.1.0.376 (2026-08-30)

- **Person learning now works when Frigate sits behind an authenticated
  reverse proxy.** The harvest chain called Frigate directly and without the
  program's identification, so a proxy that filters unknown clients answered
  403 and the run failed before fetching a single event. Those calls now go
  through the same authenticated channel as everything else. Found on a live
  run against a remote Frigate; local installations never noticed.


## 0.1.0.375 (2026-08-30)

- **Person learning now works on Frigate up to 0.17.** The body harvest needs to
  know where the clip's clock stands, and only Frigate 0.18 provides the field
  for that; on older versions every event failed with "0 images harvested" and
  no visible reason. On a field installation that was 135 of 136 attempts since
  mid-August. On such versions the harvest now takes the one snapshot picture
  Frigate stores per event instead of the best three from the clip: fewer
  pictures per event, but the run produces material at all, and every quality
  check still applies. Each harvested picture records whether it came from the
  clip or the snapshot. Measured on a 30-event run: 3 events with pictures
  before, 15 after. With Frigate 0.18 nothing changes.


## 0.1.0.374 (2026-08-30)

- **A hand-edited value outside the allowed range no longer locks the whole
  configuration page.** If a config file carried, say, 100 hours of lookback
  where the page allows 1 to 72, every save of the page failed, because the save
  always sends all fields and stopped at the first invalid one — the same trap
  that once broke saving for everyone via a faulty picker. Such values are now
  clamped to the allowed range when the program starts, with a log line saying
  so, and the page stays usable.
- **Rejection reasons under anchor pictures now speak your language.** They were
  hard-coded English sentences; now they are translated like everything else, in
  all five languages, including the tooltip in the naming view.
- **The "check on startup" choice "ask" is not offered any more** while its
  button is hidden. Choosing it would have meant events are held back with no
  way to release them. Existing installations that had it set fall back to
  processing the backlog right away.
- **Chapter links in "Read me first" land where they should.** The jump target
  and the chapter list no longer hide behind the sticky header, the highlighted
  chapter follows your scrolling, and the header no longer marks Activity as
  active while you read.
- Small language fixes: the waiting-events line reads correctly for a single
  event in all five languages, and French and Italian use the short hour unit.


## 0.1.0.373 (2026-08-30)

- **An adopted anchor keeps the order it had while you were naming it.** Before
  adoption the pictures stand in sections by viewing direction, front, left and
  right, with the ones the program does not recommend below. Afterwards the same
  page fell back to a single flat row, so that structure was gone on exactly the
  view that makes a group readable. Both cases now build their sections from one
  function. Two things follow. The read-only view groups by what was really
  adopted back then instead of by a freshly computed recommendation, so changing
  a threshold later cannot rearrange a finished group after the fact. And
  pictures marked "not recommended" stay visible in easy mode, where the flat row
  had always shown them; on one group of 30 crops 18 would have disappeared. The
  reason under each picture, which the heading promises, was missing on 23 of 24
  adopted anchors here and is there now.


## 0.1.0.372 (2026-08-30)

- **"Read me first" no longer opens by itself.** It came up on its own after
  every restart, and once it was open there was no way out where you look for
  one: Escape did nothing, and the page had no close button. You now reach it
  through the button in the header, which was there anyway, and it has a back
  button that Escape also triggers.
- **The catch-up button from 0.1.0.371 is hidden again**, and catch-up goes back
  to working the events off on its own. Only the button and its dialog are out;
  the machinery behind them stays, so setting the mode to "ask" still gives the
  old behaviour. Taking the button away without taking the mode back would have
  left events held with nothing to release them. 0.1.0.371 was never published,
  so this affects in-house installations only.


## 0.1.0.371 (2026-08-30)

- **Fixed: the settings page could not save anything at all.** The allowed values
  for the Telegram video height were held as numbers, while the page sends every
  field as text, so the check compared "720" against 720 and refused it. A save
  is refused as a whole at the first value the service does not accept, and the
  page sends all of its settings in one go, so nothing could be saved there any
  more, no matter what you had changed. The error message then broke on the same
  mismatch, so not even a reason came back. Both are fixed. The notification
  settings, which sit on their own tab without that field, were never affected.
- **New page "Read me first"**, reached from a button in the header, with
  chapters you can jump between: what the recognition hangs on, how faces get
  taught, what is being worked on, and a personal note. In this version it also
  opens by itself once after every restart until you close it. Five languages.
- **Catch up on missed events on demand.** With catch-up set to "ask", events
  that piled up while the service was down are held back instead of being worked
  off unasked, and a button in the header offers them to you: you say how far
  back to go and how many at most. An event leaves the held stack only after it
  has really been through, so a run that does not reach it leaves it where it is.


## 0.1.0.370 (2026-08-29)

- **The remote support switch now shows its real state.** The check reads
  `support_zugriff` live from the config store on every request, by design, so
  turning it on takes effect immediately. The settings page, however, showed the
  value the service had read at startup. After switching it on and reloading, the
  page still said "off", which invites you to switch it on again, or worse, to
  believe access is closed while it is open. On one machine that gap lasted twelve
  minutes. Settings that are read live are now displayed live.


## 0.1.0.369 (2026-08-29)

- **Names with an apostrophe work in learning runs again.** Naming a group
  with an apostrophe (like "O'Brien") was rejected as invalid, and where such a name had been set, the
  group counted as broken and its pictures disappeared from the view. The learning
  run carried its own, stricter name pattern that allowed neither apostrophes nor
  brackets, while the rest of the program has always allowed both, because real
  names arrive that way from Frigate. Both now use the same definition. Reported by
  a field tester, where it hit exactly one person out of 31: the one with the
  apostrophe in her name. Path tricks and shell characters stay rejected as before.


## 0.1.0.368 (2026-08-29)

- **Stream details are now read once per camera, not on every restart.** The
  service probed every camera's stream on each start, even though the answer was
  already cached and a stream resolution hardly ever changes. Cameras it cannot
  reach cost a full timeout each time: on one test instance that was 15 cameras
  at roughly 30 seconds each, blocking the connections a parallel learning run
  needed for its clips. Now it only probes cameras with no entry yet, so a camera
  you add later is still picked up, and a failure is remembered too instead of
  being retried forever. The camera page shows the state and has a button to
  re-check.


## 0.1.0.367 (2026-08-29)

- **No more groups you cannot judge.** A learning run could produce a group whose
  pictures all failed the picture check, so the page showed a group with nothing
  in it. Cause: the sieve that builds groups did not know the two hard lines
  (face structure, feature norm) that the display applies. On one run that made
  two such groups, one of them 27 crops of foliage from a single camera. Both
  now ask the same function, so those groups are never built. Measured on that
  run: exactly the two empty groups disappear, the real ones keep their pictures
  (the largest loses 1 of 246).


## 0.1.0.366 (2026-08-28)

- **One yardstick per list of pictures.** Three places judged the same pictures
  by different rules, and you could see it: the overview tile picked its preview
  by detector confidence while the panel below it judged by picture quality, so
  a group could advertise itself with a face the panel throws out. Measured on a
  real run, that hit all five groups. The tile now uses the same ranking as the
  panel.
- **Automatic naming no longer proposes pictures that failed the check.** It
  ranked by size and sharpness only, blind to the quality line and to the
  identity check. On one run 3 of 40 proposed pictures had failed the panel's
  check and would have become references. The check result now goes into the
  selection; the count of proposals stayed at 40, the three were simply replaced
  by better ones.
- **"Group 1 of 5" now counts.** The heading was computed from how many groups
  you had already adopted, so it read "Group 1" above every group until you
  adopted one.
- **Quality line lowered from 22.0 to 21.75** (`sichtung_norm_veto`). Checked
  against the very group the 22.0 was calibrated on: it still catches 30 of its
  34 false detections, whose values sit far below both lines. Across the local
  stock it lets 2.8% more pictures through.


## 0.1.0.365 (2026-08-28)

- **Fix: a learning run now takes the last N events by default, even if they
  were searched before.** The "skip events already searched" box was ticked out
  of the box, so every second run walked further into the past instead of
  looking at the same recent recordings. Measured on two runs of 300 events
  each: they shared **not a single event**, and the second one found three
  people where the first found five. The box is still there for anyone who
  wants to work backwards through their archive, it just is not the default
  any more.
- **Housekeeping: starting a run now clears out unnamed groups of earlier runs.**
  They were not reachable any more (the page only ever shows the current run) but
  kept piling up — on one machine 92 of 163 groups, most of a 30 MB file. Named,
  adopted and dismissed groups stay: they feed the name suggestions, record what
  was already learned, and remember what you dismissed.


## 0.1.0.364 (2026-08-28)

- **New: smart learning — quality before identity (off by default).** The
  learning run used to group every face the harvest kept, which on one tester's
  machine produced groups full of black tiles and blurred fragments. Two new
  switches change the order: a quality sieve runs *before* the grouping, and
  clear groups get their name by themselves.
  - The sieve keeps only faces that pass the same "good" bar the reference
    check uses, looking roughly at the camera. It also reads the learning
    stock, which the grouping never saw before — measured on a 300-event run,
    254 of 327 kept faces exist *only* there.
  - Three guards keep rubbish out: the false-detection signature (which caught
    a dog that had slipped through), the scenario consensus against foliage and
    noise, and the rule that a group built from a single sighting is not a
    group.
  - Groups that clearly belong to someone you already named are named
    automatically, but only when three conditions hold at once: closeness,
    a clear lead over the second-best person, and agreement among the group's
    own images. Measured against 23 people and 30 groups: 18 of 18 checkable
    assignments correct, none wrong. Everything unclear still waits for you.
  - This is now how the learning run works, there is no switch back. The
    sieve does take material away — on a stock of 198 runs it keeps roughly a
    third — so short runs may end up with fewer groups than before, or none.
    The run's summary always says how many faces the sieve kept, how many were
    discarded as not-a-face, and how many groups fell to the single-sighting
    rule. The thresholds behind it stay adjustable in the settings.
- Step 3 is now called "Name the people", and it tells you how many groups the
  system named by itself.

## 0.1.0.363 (2026-08-28)

- **New: remote support access (read-only, off by default).** When you ask
  for help, you can now let the supporter download exactly six named areas
  (logs, masked config, faces, learning runs, body material, state files)
  with a dedicated token you create and can revoke any time. Everything is
  documented in `docs/support-access.md`: every request lands in your
  service log, secrets are masked by field-name pattern, raw clips and
  event history are never reachable, archives are streamed (works through
  reverse proxies — the lesson from a failed full-backup pull today), and
  the token never appears in logs, config downloads or backups. Built
  against a 21-point adversarial review before the first line of code.
- **Fixed: image links of B-runs never resolved** on the crop route (two
  contradictory run-id patterns; now one central pattern serves both).

## 0.1.0.362 (2026-08-28)

- **The live-watcher self-healing from 0.1.0.361 is now complete.** Concept
  review found three gaps in the first cut and they are closed: (1) engine
  test results only reached the config store while the live page was open in
  a browser — the service supervisor now picks them up itself every few
  seconds, so a watcher really does come up on its own after a passed check,
  browser or not; (2) pending source checks are queued automatically (one
  per tick, two attempts per camera) — enabling several cameras in a row, or
  enabling while the engine is still starting, no longer strands watchers;
  a failed check switches the watcher back off with the reason on the tile,
  no silent "on but never up" state; (3) with the engine down, the automatic
  check no longer starts a helper process with a second model next to the
  starting engine (the constellation behind an earlier GPU crash).
- **New tile state "Checking source".** While the automatic check runs, the
  tile says so instead of demanding "test required" for a test the system is
  already running; the Enable button is now also offered on configured but
  untested cameras (the check runs by itself).
- **Fixed: the vision prerequisites list ignored the interface language.**
  On an Italian page the "Still missing" items ("0 of 2 approved galleries…")
  appeared in English (field report). The three prerequisite lines are now
  proper language keys in all five languages, on the page and in the
  switch-on answer.
- **Job watchdog budget recalculated.** The 420 s emergency stop predated the
  longer probe timeouts from 0.1.0.354 and could kill a healthy but slow
  source test on WAN cameras; the budget is now derived from the actual
  timeouts.

## 0.1.0.361 (2026-08-28)

- **Fixed: Person Learn harvested 0 body images on Frigate 0.17.x**
  ([#27](https://github.com/BennoBaer-dev/suslik/issues/27), thanks to the
  excellent report and trace). Frigate 0.17.2 can deliver events with
  `has_snapshot: true` but without `data.snapshot_frame_time`; the body
  harvest assumed the field is always present and every event died with
  `Fehler: 'snapshot_frame_time'` — after the clip had already been fully
  decoded, and on the live body path the clip was even decoded twice. The
  harvest now checks this precondition up front (before any snapshot
  download or clip decode) and records an honest per-event reason instead
  of a KeyError. Body judgements on such installations keep working via the
  snapshot path, and the service now logs one clear line per start when it
  detects a Frigate without the field. We deliberately did not silently
  substitute `start_time`: that value also calibrates the path clock, and
  measurements showed the substitute shifts it by up to tens of seconds on
  long events, which would silently harvest wrong training crops. A real
  calibration fallback for 0.17 (estimating the snapshot moment from
  `path_data`) is under evaluation with real 0.17 material.
- **Fixed: enabling a live watcher after its source changed no longer dead-ends.**
  A field installation had its most important watcher refused 20 times across
  three restarts ("enable refused: source changed since last test") — six hours
  without a watch, with no way out except knowing to press "Run source test".
  Enabling now accepts the switch, starts the source test automatically, and
  the watcher comes up on its own once the test passes. Also fixed a
  fingerprint mismatch (an out-of-range processing height was normalised on
  one side of the comparison but not the other) that could make this state
  permanent.
- **Fixed: one vanished cache file aborted the whole disk-watch pass.** A
  `.part` file removed concurrently (by the body worker) raised out of the
  cleanup loop, and size-cap eviction, live cleanup and the low-disk check
  were skipped for that pass. The removal is now per-file safe.
- **Fixed: three identical config saves spawned three restart threads.** The
  restart is now idempotent; duplicates are logged and ignored.
- **Learning runs and Person Learn are now visible in the service log.** The
  face harvest logs progress every 25 events (or 10 minutes) with the same
  numbers the UI shows; Person Learn logs start, end and failure. Both were
  previously invisible in the log — a five-hour harvest left no trace.
- **New setting `sweep_limit`** (50–2000, default 200): how many events one
  Frigate sweep may fetch. On busy multi-camera sites the sweep hit the fixed
  200 ceiling permanently (196 warnings in six hours on a 31-camera site) and
  the value could not be changed from the UI.
- **Fixed: hardware probe claimed "iGPU found" on machines without an Intel
  iGPU.** The probe now reads the PCI vendor of the render node; an
  NVIDIA/AMD-only machine reports that honestly instead of warning about a
  missing OpenVINO runtime.

## 0.1.0.360 (2026-08-27)

- **Fixed: after saving the setup wizard, the container log went silent.** The service restarts
  itself in place on a wizard save, and since .354 the new process kept writing into the dead pipe
  of the old log tee: proven with a probe, 0 of 3000 lines reached `docker logs`, all of them only
  reached the log file. The tee is now dismantled before the restart and rebuilt cleanly by the
  new process; both destinations get everything again. Found by the release gate's data-axis
  stage, which exercises exactly this restart — it only arms once all five image variants are
  built, which is why it caught the bug on release day and not earlier.

## 0.1.0.359 (2026-08-27)

- **The stranger rule now also looks at how close the best face came.** Since .356, a pass with a
  lot of usable face material and no match stays Unknown and the body path may not name it. Amount
  alone turned out to be too blunt: measured on 258 confirmed passes, a genuinely known person
  needs a median of 5 usable faces before the first near-match, but one in ten needs more than 22
  — plenty of material with weak values does not prove a stranger. A pass is therefore only
  declared a stranger if, on top of the amount, not a single face came near a match (0.40). The
  original case stays caught: 134 usable faces, best value 0.329. A resident who almost matched
  (best 0.465) can no longer lose his body-based name, no matter how much material the pass holds.

- **Fixed: a discarded body name could still appear in the vision footnote.** The pass card said
  Unknown while the vision line below still named the discarded person; the footnote now honours
  the discard.

## 0.1.0.358 (2026-08-27)

- **A learning run can now be limited to certain cameras.** The run costs time per event, and the
  cost is linear: on our own site a day has 440 person events across five cameras, 58 of them on
  the front door camera, so a run limited to that camera does an eighth of the work. On a site
  with 29 cameras and 12,000 events a working day the difference is larger still. The picker sits
  in the search dialog and offers the cameras you ticked on the camera page; picking nothing keeps
  today's behaviour. It combines with both "the last N events" and "one day".
  The filter is applied by Frigate, not by us: the events are never fetched in the first place
  rather than fetched and then discarded. Everything after the event list is untouched, there is
  no second recognition path. The run records which cameras it was limited to and shows it, so a
  camera run is not mistaken for a full one later, and it says plainly when the selected cameras
  simply hold fewer events than you asked for.

- **Fixed: a continued search took more events than ordered.** With the "continue" tick set, the
  run fetches extra events to compensate for those already searched, then filters them out. The
  cut back to the ordered number had ended up under a condition where it could never apply, so a
  run ordered for 50 events with 20 already searched processed 70. Found by our own quality pass
  before release; it affected every continued run, with or without a camera selection.

## 0.1.0.357 (2026-08-27)

- **Unknown visitors have their own section on the day page.** Until now their tiles sat at the
  end of the "Recognized" band, between the people you know, looking exactly like them. That made
  the heading untrue and buried the one tile that actually deserves a second look. They now get
  their own band between "Recognized" and "Passes", with an amber bar instead of a green one, and
  it only appears when there is something in it. Both kinds go there: a visitor the system has
  seen before and given a number, and one who is here for the first time. The tiles themselves are
  unchanged, and clicking one still opens that walk-through with its faces and the box where you
  can type a name, new or existing.
  The count says how many *passes* had nobody recognized, not how many visitors — one tile is one
  pass, and passes cannot honestly be folded into visitors: two tiles can be the same person six
  minutes apart, and one tile can carry several. The number in the side column counts persons and
  will differ, sometimes higher and sometimes lower. Two numbers, two questions, each named for
  what it is.

## 0.1.0.356 (2026-08-27)

- **Fixed: a pass could be given a resident's name when the person was in fact a stranger.**
  suslik has two ways to put a name on a walk-through: the face, and the body (build, clothing,
  posture). The body path only runs when the face path confirmed nobody, and until now whatever
  it said became the name of the whole pass, unchecked. That is wrong when the face path saw the
  person perfectly well and simply matched nobody, because then the visitor is a stranger and the
  body path is comparing a stranger's jacket against the people you enrolled. In the case that
  prompted this, a visitor who is not enrolled at all was labelled with a resident's name at 0.86,
  across five cameras, while the face path had correctly confirmed no one.
  From now on, if a pass contains a lot of usable face material and not one of those faces matches
  anybody, the pass stays unknown and the body path may not name it. "Usable" means a real
  detection, frontal enough and large enough; size alone is not enough, since a big face in pure
  profile tells you nothing. The threshold is the new setting `fremd_ab_gesichter` (default 20).
  Measured on our own data: passes that were named correctly had 2 to 4 usable faces, the one
  known bad case had 134. Where exactly the line belongs above 4 is not established, which is why
  it is a setting rather than a constant.

- **A body-based name is now clearly marked as such.** It gets a red bar on the pass row, a red
  badge next to the judgement, and the picture shown is the one the body recognition actually
  used, taken from that recording. Before, a body attribution looked exactly like a face match,
  and the thumbnail could even show a different person entirely. If you see the red marking, the
  face path did not speak.

- **Fixed: a pass could disappear from the day view entirely.** When the new rule removed the only
  name and no event in the pass counted as unknown, the pass was classified as plain motion and
  filtered out — no name, no unknown card, nothing. A pass where somebody was seen and
  deliberately not named is an unknown, not mere movement.

## 0.1.0.355 (2026-08-27)

- **suslik now keeps its log on disk, so it survives restarts.** Until now the log
  lived only in a 300 line memory buffer behind `/log` and in `docker logs`. On a busy
  site that buffer covered under twenty minutes, so the startup block — the part that
  matters most when something is wrong — was gone by the time anyone looked, and
  reading `docker logs` needs shell access you may not have. Everything suslik prints
  now also goes to `<data_dir>/logs/suslik.log`. It is rotated on every start, at
  midnight and when it passes `log_max_mb` (default 64); older pieces are gzipped and
  removed after `log_behalten_tage` days (default 14). `/log` reads the file now
  (5000 lines by default, `?lines=20000` for more), and `/log/suslik-logs.tar.gz`
  hands you every piece in one download — that is the file to attach when you report
  a problem. A full service run is around 70 kB, so two weeks cost megabytes. Set
  `log_datei: false` for the old behaviour.

- **Fixed: a live watcher on a slow machine could drop to software decoding even
  though its GPU was fine.** The watcher gives the hardware decoder a moment to
  produce its first frame and falls back to software if nothing arrives. That window
  was six seconds, which is a local-network number: measured against a local restream
  the first frame takes about three seconds, and against a remote 4K stream eight to
  nine. So the watcher threw the GPU away before it had delivered and then decoded
  4K on the CPU. The window is now 25 seconds for every source. It costs nothing when
  hardware decoding is genuinely broken, because ffmpeg exits on its own within about
  two and a half seconds and the fallback happens immediately.

- **Fixed: the watcher's start line could report impossible numbers.** Against a
  stream without duration metadata, ffprobe reported 989 frames per second and a
  bitrate of 2.5 gigabits for a single camera, and a different impossible value on
  every call. Frame rate and bitrate are now checked for plausibility; if the averaged
  frame rate fails, the stream's nominal rate is used instead, and an implausible
  value is reported in the log rather than silently displayed.

## 0.1.0.354 (2026-08-26)

- **Live watchers now work against a Frigate that requires a login.** Frigate hands
  its stream server through the same HTTPS port as its web UI, and until now the
  watcher's stream fetch was the one path that did not carry the login, so it got a
  401 while everything else worked. It now sends the same user agent and session
  cookie as the clip fetch, for `http://` and `https://` sources. The cookie only
  ever goes to the configured Frigate address: a watcher URL pointing anywhere else
  (your own camera, for example) receives the user agent and nothing more.
  Watchers without a login, and all RTSP sources, are unchanged.

## 0.1.0.353 (2026-08-26)

Bundles the in-house 0.1.0.352, which was never published: the fixes below were
found by a hardening run against simulated foreign Frigate setups after 0.1.0.352
was already built, and a rebuilt tag never silently gets new content.

- **Optional Frigate login.** New settings: Frigate user, password (stored in the
  config store, shown masked) and a TLS-verify switch for Frigate's self-signed
  authenticated port (8971). Works against Frigate 0.14+ (`POST /api/login`,
  cookie, exactly one silent re-login when the token expires). Without
  credentials nothing changes; proven request-identical.
- **Fixed: clearing the Frigate user and password did not take effect** until the
  container was restarted from outside. The service passes both to its own
  subprocesses through the environment and restarts itself in place on save, which
  inherits that environment; an emptied field was therefore still used, and after a
  change of the Frigate address the new host received a login with the deleted
  credentials. The environment now mirrors the configuration in both directions.
- **The error messages for Frigate's authenticated port were out of date** and told
  you to switch to the unauthenticated port 5000. They now point at the user,
  password and TLS settings instead. One error line was also still in German.
- **The startup log now states whether Frigate's own face recognition is on.** That
  single fact separates installations from one another and explains a whole class of
  reports; boot logs get pasted into issues, so it belongs in there.
- **New setting `sweep_limit`** (default 200, unchanged behaviour): how many person
  events the catch-up sweep asks Frigate for per round. It used to be hard-wired.
  On a busy site 200 events can be less than half an hour, which silently shortened
  the configured lookback window; the log line now says to raise this instead of
  giving the old advice of shortening the window, which does not help there.
- **All HTTP calls to Frigate now go through one shared client** (API, clips,
  thumbnails, faces, including the worker processes), and every request carries
  an honest `suslik/<version>` user agent. The video fetch via ffmpeg gets the
  same cookie and user agent passed along.

## 0.1.0.351 (2026-08-26)

- **New button "Brightness check" on the learning run card.** It opens a calibration
  page that shows your own clusters with each image's measured brightness, ordered
  exactly as the recommendation orders them. Two sliders preview live which images
  would fall back; saving writes the two thresholds through the regular configuration
  path (the service restarts briefly, as with any configuration change). If no image
  carries a brightness value yet, the page says so — values appear from the next
  learning run or pass check onwards. The row on the card has room for more quick
  actions later.

## 0.1.0.350 (2026-08-26)

- **Recommendations now consider exposure.** The harvest measures the brightness of
  every candidate face (a new per-image value, old data stays valid), and badly
  exposed images (too dark or blown out) drop to the end of their size class instead
  of filling the perspective slots before better-lit ones — the issue 26 follow-up,
  where the recommended picks were visibly too dark while brighter ones only lost to
  a full slot. Affected images say why ("too dark", "overexposed") and can still be
  ticked deliberately; nothing is ever dropped automatically. Two new settings,
  reihung_luma_min (default 78) and reihung_luma_max (default 182), 0 disables a
  side; changes apply to existing runs immediately. Proven bit-identical apart from
  the new field: same candidates, same embeddings, same crops.

## 0.1.0.349 (2026-08-26)

- Fixed: adopting an anchor cluster could fail with "nothing selected" although
  images were visibly ticked (reported in issue 26 — thanks). The adopt button on the
  cluster detail page only sent the cluster id; the server then used the previously
  saved selection, while the page showed recommendation ticks the server had never
  seen. The button now saves the current ticks and the name first, then adopts. Naming
  also reports the number of images actually matched and refuses loudly when a
  selection matches nothing instead of silently storing an empty one.

## 0.1.0.348 (2026-08-26)

- Fixed: with Frigate's own face recognition enabled, every request to the today page
  crashed (found by a field tester on 0.1.0.347 — thanks). The notice introduced in
  0.1.0.341 read its setting through the wrong object; on setups with Frigate face
  recognition disabled the broken branch was never reached, which is why our own
  machines never showed it.

## 0.1.0.347 (2026-08-26)

- Fixed: the pass-check progress block flickered on every refresh. The poll loop
  cleared the block and showed the "checking" text at the start of each tick before
  rebuilding it; now the block is built once and only its values change, like the
  wizard card.

## 0.1.0.346 (2026-08-25)

- Progress block layout: label and counter on one line, the bar below at full width.
  Long counters used to squeeze the bar track down to a few pixels in the narrow
  wizard card. On the pass check the block now takes the full row below the button
  instead of sitting squeezed next to it.
- Fixed: the pre-check counter (faces dropped before head pose for being too small or
  blurry, introduced in 0.1.0.342) never reached the run records or the wizard counter
  line — three transport lists picked counters by name and dropped the new one. Run
  records were violating their own counter invariant. The wizard now shows
  "filtered early (size/sharpness)" when the pre-check dropped faces.

## 0.1.0.345 (2026-08-25)

- **The progress display is now a real block of bars, in both places.** While a pass
  or a learning run is being prepared, the pass-check button and the wizard card show
  one overall bar for the whole run plus three sub-bars for the current event —
  searching faces (frame X of Y), head pose, recognizing — running side by side with
  live counters. Between events the block says it is fetching the next clip instead of
  freezing; waiting for another background job and the final rating step are covered
  too. This replaces the thin bar with the text line (0.1.0.343/.344) and the vertical
  column in the wizard card.

## 0.1.0.344 (2026-08-25)

- The learning-run wizard now shows the same three live counters while collecting faces
  (frame X of Y, head poses, recognized) — the second of the two places they belong.

## 0.1.0.343 (2026-08-25)

- Fixed: the live counters under the pass-check progress bar never reached the browser.
  The route handler assembled its reply field by field and silently dropped the new one.

## 0.1.0.342 (2026-08-25)

- **Harvesting got roughly twice as fast on passes with poor yield.** Faces that cannot
  clear the size and sharpness bar any more are dropped before head pose and embedding
  are computed, not after. Proven bit-identical on a real pass (same candidates, same
  embeddings); measured 36-38 s down to 20-24 s on the same event.
- **The pass-check progress got honest and alive.** The bar now moves smoothly across
  events and frames, and below it three live counters show what is happening right now:
  searching faces (frame X of Y), head poses computed, faces recognized.
- Interim builds of 0.1.0.341 carried today's earlier steps (system load page, cleanup
  job, Frigate face-recognition notice); this release names the final state.

## 0.1.0.341 (2026-08-25)

- **New page: System stats, under System.** CPU (total and per core), memory, disk,
  GPU and NPU, each with the current value and the last hour as a bar row. Below that
  the numbers no other system page has: whether the analysis worker is running, how
  often it died in the last 24 hours and of what, analyses per hour and their average
  duration, and how many events are still waiting. That block exists because the worst
  failures we have seen in the field were recognition standing still while CPU and GPU
  looked perfectly calm — on one tester's machine the worker died 114 times in a day.
  A sample is taken every 60 seconds and kept for 48 hours; the nightly cleanup trims
  it. `/health` reports the same snapshot under `system`, so a diagnosis does not need
  a browser.
- **A number this hardware cannot measure says so.** Tiles never show a zero for a
  missing measurement, they say "not available" and give the reason. Concretely: Intel
  GPU utilization is not readable from inside a container without extra privileges (the
  i915 counter exists, `perf_event_open` is denied), so that tile stays honest instead
  of implying an idle GPU. The Intel NPU, CPU, memory and disk are measured normally,
  and NVIDIA reports through `nvidia-smi`.
- **No split per process on that page.** Frigate runs in its own container, so its share
  cannot be named from this side even with perfect driver numbers. The page shows total
  load and says why.
- **The startup notice about untranslated content is gone.** It sat on top of a page
  whose frame is fully translated and claimed the opposite, which read as a bug rather
  than as information. Only the evaluations in the content area are still English; that
  is fixed by translating them, not by a sign in front of them.
- **The nightly cleanup now actually cleans up.** It only ever touched event crops and
  the clip cache, so three places grew without limit: finished learning runs (973 MB in
  86 folders on our own machine, oldest three weeks), pin markers whose clip was deleted
  long ago (26 of 26 were orphans), and the OpenVINO compile caches (2.65 GB, no cap).
  All three are now cleared by age, and the run happens at startup as well as at night.
  Learned faces, the person model and the backups are off limits to it, enforced by a
  path check rather than by good intentions.
- **suslik now says when Frigate's own face recognition is running.** A quiet line on the
  today page points out that suslik does not need it and works either way, so nobody keeps
  a second recognition running by accident. The switch is read from the same Frigate
  config call the camera list already uses, and the notice stays away when the optional
  name write-back to Frigate is on, because that one does need it.

## 0.1.0.340 — 2026-08-25

After a restart or a broker reconnect, suslik fetches the person events it
missed while it was down and analyses them one after another. From the outside
that looked like load without a reason. The dashboard now says what is
happening while it runs, with a count of how far along it is, and offers to
turn the behaviour off.

New setting `start_catchup` (on by default, i.e. unchanged behaviour). Turned
off, the events that had already piled up when the service started are marked
as skipped on the first sweep instead of being analysed; they keep their place
in the record and are never retried as failures. Everything happening after
that start is analysed normally. In poll mode the periodic sweep itself keeps
running, because it is the only thing that picks up events there.

`/health` reports the setting and the progress of a running catch-up.

## 0.1.0.339 — 2026-08-24

Release build of 0.1.0.336–0.1.0.338 (which went only to one field tester),
with the agreed What's-new entries baked in. No code changes beyond the box.

## 0.1.0.338 — 2026-08-24

The startup log is now actually readable: the ~60 identical red
`pthread_setaffinity_np` driver lines per start are filtered at the file-
descriptor level (only that exact known-harmless line, everything else passes
through byte-for-byte) and replaced by one honest summary line with their
count. No library patching involved.

Note for small machines: the very first start of a `-gpu` image compiles its
models for the GPU inside the main process and needs about 3 GB of free memory
headroom; from the second start on the compilation cache carries it (a 2 GB
container then works). The startup log warns when the memory guard sits above
the container limit.

## 0.1.0.337 — 2026-08-24

Same fix as 0.1.0.336 (which went only to one field tester), plus log honesty:
a missing guard `enabled` no longer logs a false "invalid" alarm at every start,
a config field removed in an older version is named as such (with how to silence
it) instead of being warned about forever, and the live engine explains the red
thread-affinity lines of its model library itself.

## 0.1.0.336 — 2026-08-24

Bundles the internal steps 0.1.0.332–0.1.0.335.

- **Fixed: the analysis worker could die on every start on machines with tight
  memory** (regression introduced in 0.1.0.313, reported in the field on
  0.1.0.331 — 114 worker deaths in one day, recognition effectively stopped
  while live watching kept running). The learning-stock quality model was built
  eagerly at every worker start, outside the memory guard, without a
  compilation cache, and on the GPU chain even for live jobs that never use
  it. It is now built only when a harvest job actually needs it, behind a
  memory-budget check that skips the stock loudly instead of dying, with the
  compilation cached on disk (build time 10.4 s → 4.2 s, and no more
  recompile loop that kept the iGPU near 100 %). Measured peak per worker
  start drops from 1.5 GiB to 0.9 GiB — back to pre-0.1.0.313 level.
- **Worker deaths now say why**: `worker died mid-job (signal 9 = SIGKILL —
  most likely the kernel out-of-memory killer)` instead of a bare "died
  mid-job". The startup log also prints a memory picture (container limit if
  readable, meminfo with an honest "may show the host" note, and the
  configured worker guards, with a warning when the guard sits above the
  container limit).
- **The startup log no longer prints resident names** — it counts persons and
  reference images instead. Boot logs get pasted into public issues; names do
  not belong there.
- **debug is no longer persistent**: it resets to off at every start and can
  be toggled at runtime without a service restart. A debug switch someone
  forgot no longer floods the log forever.
- **Intel GPU driver cache moved into the data volume** (both Intel images):
  with a read-only root filesystem the driver silently computed wrong,
  non-reproducible results because it could not write its kernel cache under
  `$HOME`. The cache now lives in `/data/clips/neo_cache` (verified against
  the shipped driver binaries, 1 GiB cap).
- **The feature-norm device chain gained an FP32 stage** (NPU → GPU →
  GPU-FP32 → CPU) and its cross-check now measures at the real working point
  (face-like test input instead of noise, threshold re-derived from the
  decision lines). On healthy hardware nothing changes; a GPU whose fp16
  math is off now falls back to FP32 on the same GPU instead of losing the
  device entirely.

## 0.1.0.331 — 2026-08-22

Bundles the internal steps 0.1.0.299–0.1.0.330.

- **Disk limits now fit the disk** (issue #25): suslik measures the disk at
  startup and derives its cache cap and free-space floor from it, instead of
  using fixed numbers that suit one machine and not another. A 32 GB disk gets a
  4.8 GB cap, a 2 TB disk gets 300 GB. Fixed values still win if you set them.
  Cached clips are also kept for 2 days instead of 7 — they are only a cache,
  every clip can be fetched from Frigate again. The old default of 50 GB could
  never take effect on a 32 GB disk, which is exactly how one installation
  filled its disk and stopped; measured on the development system the change
  turns 25 GB of cached video into 4.9 GB. suslik now also says at startup which
  limits it is using and where they come from.
- **The example configuration no longer overrides the new default**: the
  shipped `verifyd.yaml` pinned the clip retention to 7 days, so anyone using it
  kept a week of video no matter what the default said. The line is gone. If you
  copied it into your own config, remove `clip_retention_d` there to get the
  2-day default, or set the number you want.
- **The disk tile showed a limit of 0 GB**: with the new automatic limits the
  System page printed the raw setting instead of the value actually in use, and
  the traffic light compared free space against 10 GB instead of the real floor.
  It would have stayed green well past the point where cleanup starts.
  Both now read the same source as the cleanup itself.
- **The disk check runs once a day instead of every ten minutes**: cleanup
  already runs after every processed event, so the timer is only a safety net.
  It stays at ten minutes while space is actually tight, because that is the
  situation where processing stops and no events arrive to trigger it.
- **The live watchers stop writing pictures nobody sees**: frames rejected by
  the pose gate (no human in view) were saved for two days, although the
  interface never shows them; on the development system they were the largest
  single item in the data folder. They are now only counted. A switch brings
  them back for troubleshooting.

- **People who arrive together now show up as a group**: next to the cards for
  each person, the Today page lists the passes in which two or three people were
  recognised together, with all their faces on one card. Clicking it opens
  exactly those shared passes. The group is always named in alphabetical order,
  so the same pair is always called the same thing.
- **The pass check no longer offers five pictures of the same second**: it
  suggested up to five frames from one recording, taken seconds apart in the
  same pose — different enough for the duplicate check, identical to the eye.
  At most two per event are now proposed; the rest stay visible as borderline.

- **A pass with several people now shows all of them**: until now a pass card
  showed the pictures of one person and squeezed everyone else into a line of
  names, even though each person has her own best shot, her own score and her
  own thumbnails. Now up to three people stand side by side with their own
  picture and value, and each gets her own row of thumbnails with her own
  "check this pass" button — so the button behind one person checks that
  person's pictures.

- **The face structure check no longer hogs the CPU**: its model was loaded in a
  way that bypassed the project's thread cap, so a single measurement spread
  over about ten threads and cost 126 ms of CPU time for 11 ms of wall clock.
  Capped at two threads it costs 15 ms of CPU for 3.8 ms wall clock, with
  bit-identical results. On small machines this is the difference between
  workable and not.

- **Cached clips that are in use are no longer deleted**: the cleanup had two
  paths — by age and by size — and only the size path checked whether someone
  was currently holding a clip. The age path did not, so a clip could be pulled
  away from a running job. Now both paths check.

- **Learning runs tell a face from a hedge**: the detector sometimes reports
  foliage, a neck or the back of a head as a face, and it is confident about
  it, so neither the size bar nor the object filter catches it. suslik now
  asks a different question first: it puts a 106-point landmark model on the
  crop and measures whether the points spread across a face or collapse to the
  centre. Crops without face structure are no longer harvested at all
  (`ernte_struktur_min`, default 0.11), and what is harvested but still weak is
  shown under "show all" instead of being offered (`sichtung_struktur_min`,
  default 0.15). Measured on 2000 random crops from 36 runs.
  The group consensus introduced in the previous step is gone: it judged whole
  groups by the quality measure and threw away five groups of real, recognised
  people to catch two hedges — the structure test catches those hedges on its
  own, picture by picture.

- **Face learning finds better pictures**: after a pass, the face check
  ("Check this pass for good pictures") now looks at every frame from every
  camera of that pass, measures how good a face really is with a
  reference-free quality score, and offers more and better pictures, grouped
  by view (left, front, right). It runs on its own right after each pass, so
  the check answers instantly. Faces that belong to a different person in the
  same pass (or a dog) are kept out by a consensus check.
- **Quality you can see**: every reference picture now carries a quality
  value, shown on the Quality page; weak pictures are flagged, and group
  naming in learning runs pre-selects by the same measure. "Matching faces"
  suggestions are checked against the other people you know before they are
  shown.
- **Progress bars for long steps**: the quality check, the pass check and
  rebuilding the reference library show a bar with a counter instead of a
  static "please wait" text; a stuck rebuild is reported after two failed
  attempts instead of retrying forever.
- **No more full rebuild after every group**: naming a group in a learning
  run (and adopting a face from the Unknown card, an enrollment suggestion or
  an upload) now adds the new pictures to the reference cache instead of
  throwing it away, so the next group opens right away instead of waiting a
  minute for a rebuild.
- **Honest learning-run estimate**: the remaining time is measured from the
  run itself (seconds per clip-second over the events already harvested) and
  the measured rate is kept for the next run's estimate on the same machine;
  the old estimate used the analysis constants and was off by a factor of two.
- **Translation almost complete**: the help pages, the setup wizard, the
  system, vision and person pages, all dialogs and the notification texts
  (Pushover/Telegram) are translated; only the Today page still has a few
  English bits.
- **The Crop column shows the face that was confirmed**: the Events list
  and the review list used to show the largest image of the event, which
  with small faces was the context picture, often with a different person
  in front. Now each confirmed person gets her own face crop with the name
  under it (click opens the context picture); unconfirmed rows show the
  best face, and rows without a usable face say so instead of staying empty.
- **Disk watch** (issue #25): the clip cache used to be trimmed only after
  an event had been processed, so a full disk stopped the processing and
  with it the cleanup. Now free space is checked at startup and every ten
  minutes, the cache is trimmed before it gets tight (`disk_frei_min_gb`,
  default 10 GB, next to the age and size limits), the System page shows
  the cache size and has a "clean up now" button, and a disk that stays
  tight raises a warning banner.
- **Learning runs no longer drop groups on their own**: a group whose
  pictures all fail the picture check used to be set aside automatically,
  and a group that looked like one you had dismissed in an earlier run was
  dismissed again silently, both with their pictures deleted. Now every
  group the run finds stays in naming until you name, skip or delete it,
  and only your own "Delete this group" removes pictures.
- **Learning runs always show their pictures**: the picture check used to
  detect the face a second time on the small, tightly cut crop and, on
  faces of 60–100 px, mostly found nothing ("no measurable face"), so whole
  groups looked empty; and pictures that were already learned were moved to
  the collapsed "show all" rest. Now the check uses the measurement the
  harvest already made on the full frame (the same one that fed the group),
  pictures you have already assigned stay visible with a note ("already
  learned", "already in the catalog") instead of being hidden, and adopting
  a picture from a learning run stores that measurement with the reference
  so the Quality page and the reference cache never re-detect the small file.
  Pictures that are already learned are shown but no longer pre-selected, so
  a single "take" cannot add a duplicate — or a face that belongs to someone
  else. A group no longer stops at 14 pictures per view either: everything
  above the quality line is listed behind them.
- **The quality measure can now rule a picture out**: the detector sometimes
  reports a hedge or a bush as a face, and it is confident about it — so
  neither the size/sharpness bar nor the object filter (which looks for a
  *low* detector score) catches it, and a whole group can end up showing
  greenery. The reference-free quality measure sees the difference, so it is
  now a veto: a face at or below `sichtung_norm_veto` (default 22) is dropped
  from the group view, with the measured value in the reason. Pictures whose
  quality was never measured are unaffected — they are judged by size and
  sharpness as before. A group is also judged as a whole: if fewer than
  `sichtung_konsens_min` (default 40 %) of its faces reach the line, the whole
  group is treated as a false detection — that catches a hedge whose few best
  crops sneak over the line, without raising the line for everyone. Nothing is
  deleted: the pictures stay under "show all", and only you remove a group.
  A group with nothing left to show is no longer the first one you are handed —
  it moves to the end of the run, still reachable and still deletable.
- **Far fewer notifications from the live watchers**: a watcher already had a
  quiet period after each alert (`wieder_scharf_s`, 120 s by default), but the
  name message slipped past it — it was sent before the check ran. It now uses
  the same quiet period, which cut the messages by half on the test system
  (1030 to 494 over nine days, from 115 a day to 55). Nothing else changes:
  MQTT still publishes every event, so Home Assistant automations are
  unaffected, and the live view still lists every appearance.
- **The live watchers clean up after themselves** (follow-up to the disk watch):
  `<data_dir>/live/` was the only data path without a cleaner. On the test
  machine it had grown to 73 GB in 137,719 files within nine days, 61 GB of
  which were frames the pose check had rejected — diagnostic material that is
  never shown. Both are now covered by the same disk watch, with separate
  retention times: `live_retention_d` (default 7) for evidence pictures and
  look-back clips, `live_verworfen_retention_d` (default 2) for the rejected
  frames. Set either to 0 to keep them forever.
- **Built with a different AI model**: this release was built with Claude Opus
  instead of Claude Fable 5. It passed the same quality gate as every other
  release, but there may be more mistakes than usual — please report anything
  that looks wrong.
- **Ground truth as a set**: the ground-truth buttons on the Events list
  and the review list now toggle each person separately (plus "stranger",
  "unclear", "nobody"), so a pass with two known people is one entry with
  both names; the combined "C+R" button is gone. The pass check reads the
  same set.
- **Live watchers**: one name vote per person and frame (a second face of
  the same person in a frame no longer doubles the vote), name messages are
  only sent after the pose check has confirmed a person, and the alert
  carries the frame with the face box of the person it names.
- **Face quality on the NPU**: the feature-norm measurement that the pass
  check and learning runs use now runs on the NPU when there is one, with
  the GPU and then the CPU as fallbacks (NPU→GPU→CPU, cross-checked at
  startup). On the test machine a 30-event learning run dropped from
  0.47 s to 0.12 s per clip-second.
- **Fixes**: adopting a picture from the pass check no longer throws the
  reference cache away (which forced a full rebuild on the next check);
  learning-run files are readable for backups again; a single event that
  Frigate discarded (HTTP 404) no longer raises the "Frigate unreachable"
  banner, which could otherwise stay up for hours in MQTT mode; a learning
  run with a single person no longer leaves the reference cache with only
  that person (which hid the others' pictures in the next run); the
  learning wizard now says which range of events was searched when the
  newest ones are all known already.

## 0.1.0.298 — 2026-08-19

Interim release. Bundles the internal steps 0.1.0.287–0.1.0.297.

- **Crash fix for large learning runs**: found and fixed a bug that could
  cause a crash of Frigate during very large, long learning runs with many
  events. Clip fetching for past events now takes a sturdier path and
  reports failures instead of piling up stalled downloads.
- **suslik now speaks five languages** — English, German, Spanish, Italian
  and French. Pick yours with the new switch in the header (or in step 0 of
  the setup wizard); the choice applies to the whole installation and
  survives backups. Translation is rolling out page by page: the menu, all
  dialogs, the main pages and the Today view are done, pages not yet
  translated say so honestly and follow with the next releases.
- **Learning runs tidy up after themselves**: groups without usable faces
  are set aside automatically at the end of a run (with a review link,
  nothing is deleted), so naming only shows real groups and the counters
  stay accurate.
- **Today as a tile grid**: the recognized-live row and person cards align
  in a steady grid instead of ragged rows.

## 0.1.0.286 — 2026-08-18

Interim release (entry added retroactively — it was missing from this file;
the GitHub release existed all along). Bundles the internal steps
0.1.0.244–0.1.0.285; 0.1.0.284/.285 were respun as 0.1.0.286 after the
privacy and layout gates flagged two issues (an operator name in old
comments, a table overflow on phone widths).

- Focused work on face learning: guided learning runs and easier assigning
  of faces to people.
- Picture quality: a one-click check finds weak, duplicate and mixed-up
  reference pictures for you.
- Clearer camera setup and configuration.

## 0.1.0.243 — 2026-08-17

Intermediate release — focus on simplification and clarity. We are mid-way
through the Easy/Expert rebuild; this release bundles the internal steps
0.1.0.203–0.1.0.242 (each documented below; 0.1.0.241/.242 were respun as
0.1.0.243 after the privacy gates flagged private names in old code
comments — comments neutralized, the name check itself hardened, nothing
else changed). The visible core:

- **Configuration start page, Faces area, guided learning flow**: tile-based
  start pages with plain-language "How it works" texts, a step-by-step
  learning run, and a naming card that walks you through the found groups.
- **Learn directly from the day view**: a person's pass cards offer a
  check/adopt bridge — review the suggested faces (borderline ones shown
  unticked), adopt them as references in one click, undo if needed. Already
  adopted references carry a green outline.
- **Unknown visitors, consistently**: clicking an unknown card on Today opens
  exactly that walk-through with its faces, ready to assign to a new or
  existing person.
- **Change connection inline**: the Frigate Connection tile edits the URL
  right there instead of routing you to the Advanced table.
- Honest feedback on whether this direction feels right is very welcome —
  suslik_dev@posteo.de.

## 0.1.0.240 — 2026-08-17

- "Change connection" on the Frigate page no longer dumps you into the whole
  Advanced table: the Connection tile opens a small form right there —
  current URL prefilled, Save & restart, Cancel. After the restart the tile
  itself shows live whether the new address answers.

## 0.1.0.239 — 2026-08-17

- Third and final shape of the unknown-visitor click, exactly as our user
  meant it: the Today card IS one walk-through, so clicking it opens exactly
  that walk — its camera chain, video and ONLY the faces collected on this
  walk (whatever internal group they landed in). Tick them, name them (new
  or existing person), done; doing nothing keeps them unknown. The full
  cross-day profile stays on the Unknown page.

## 0.1.0.238 — 2026-08-17

- The unknown visitor's page now really matches the person view: it merges
  the linked face groups of the same walks (the good pictures often sit in a
  neighbour group — 16 faces instead of 4 on the real test case), and every
  appearance card carries the big preview image on the left like a person's
  pass card.

## 0.1.0.237 — 2026-08-17

- Clicking an unknown visitor now opens the same kind of view as for known
  people: their appearances as pass cards (camera chain, face thumbnails,
  video), with one addition on top — "Who is this?": tick the faces that
  really belong to them, name them (new or existing person) and they are
  learned like everyone else.

## 0.1.0.236 — 2026-08-17

- Fix: after taking pictures, the NEXT check was slow again without saying
  why — adopting used to throw the whole reference cache away, and the next
  check rebuilt all ~300 reference embeddings inline. Taking pictures now
  slots the new embeddings into the cache directly; where a full rebuild is
  still needed (undo, deletions) the check honestly says "updating the
  reference library …", rebuilds in the background and re-runs by itself.

## 0.1.0.235 — 2026-08-17

- The pass check is fast for every pass now: it accidentally ran on a second,
  CPU-only model instance (~2 s per picture — passes with many faces took
  half a minute, passes with none answered instantly, which looked
  inconsistent). It now shares the service's accelerated instance; the
  warm-up on opening Today prepares exactly that one.

## 0.1.0.234 — 2026-08-17

- One click rule for all Today cards: clicking an unknown visitor now opens
  their profile on the Unknown page (all faces, naming, merging) — exactly
  like clicking a known person opens their day. The old inline
  assign-panel on Today is gone; assigning lives on the Unknown page.

## 0.1.0.233 — 2026-08-17

- The pass buttons got a cleaner look: consistent height and rounded corners,
  a small icon each (play for video, magnifier for the picture check, a check
  mark once pictures were taken) and a calm hover.

## 0.1.0.232 — 2026-08-17

- Smart model warm-up, designed by our user: opening Today (or a person's
  day) quietly prepares the face model in the background, so the pass check
  answers instantly; after 15 minutes without use the model is released from
  memory again (measured 379 MB — small boxes get it back). If you click a
  check while the model is still cold, the button says honestly "loading the
  recognition model — a few seconds …" and runs the check by itself once
  ready.

## 0.1.0.231 — 2026-08-17

- The pass check no longer hides borderline pictures: faces whose identity is
  sure but whose picture quality is only fair now appear in the dialog too —
  unticked, clearly labeled, tick to take anyway. The status line says
  honestly how many were kept back instead of a bare "nothing to take".

## 0.1.0.230 — 2026-08-17

- The pass check (and the automatic after-pass suggestion search) is much
  faster: the face-embedding models were rebuilt from scratch on every call
  (measured 11-13 s each time); they are now built once per service run and
  reused — a click costs the actual picture measurement only.

## 0.1.0.229 — 2026-08-17

- Rows with green-outlined pictures now say what the outline means, right
  next to the pictures: "green border = already in the references" — no
  hovering needed.

## 0.1.0.228 — 2026-08-17

- Fix: the green reference outlines from .227 did not appear — the periodic
  reference re-check rewrites metadata lines without the event link, and the
  newest line silently erased it. The event link now survives those
  rewrites (verified on the real library: 11 marked events instead of 1).

## 0.1.0.227 — 2026-08-17

- You can now SEE which pictures made it into the references: on a person's
  day view, every thumbnail whose event contributed an active reference is
  outlined green (tooltip "in the references") — immediately after taking
  pictures, permanently on every later visit, and Undo removes exactly those
  outlines again.

## 0.1.0.226 — 2026-08-17

- The pass-learning button is now two honest steps: "Check this pass for
  good pictures" runs the sieve and opens an in-page dialog showing exactly
  the pictures it would take — untick any you do not trust, then "Take N
  pictures" or Cancel. Nothing is adopted before you confirmed what you saw
  (no browser popup involved — the dialog is part of the page, so popup
  blockers cannot break it). Undo still works afterwards.

## 0.1.0.225 — 2026-08-16

- Learning where you already are: every confirmed pass on a person's day view
  got one button — "Add <name>'s faces from this pass". One click, the
  built-in check picks only clearly helpful new pictures (same identity,
  quality and novelty sieves as the reference search — a stranger's face can
  not be adopted by construction), the answer appears right there ("3
  pictures added · 2 kept back by the check"), and Undo takes them out again
  without a dialog.

## 0.1.0.224 — 2026-08-16

- Naming is now a guided card, not a document: the easy view shows "Group 2
  of 7" and one question — "Who is this?" — with the answer prepared when
  the system has a suggestion ("Yes, it's &lt;name&gt;"). One click names
  the group, adopts it into recognition and jumps to the next group; skip
  works the
  same way, and the last group says so. The full selection view (all images,
  checkboxes, per-image reasons) is the expert view, unchanged.
- Internal cluster-state words no longer leak into the interface in German
  ("unbestaetigt" → "unconfirmed").

## 0.1.0.223 — 2026-08-16

- The learning-run page is now a guided flow: a four-step bar (Collect →
  Group → Name → Adopt), one plain sentence saying where the run stands, and
  one button for the single next action — no anchor/cluster/harvest jargon
  in the easy view. The full phase chain with all counters is still there,
  one switch away in the expert view.

## 0.1.0.222 — 2026-08-16

- Areas left the main menu: the Recognition start page got a second, smaller
  tile row "Property set-up" with the Areas card (count + Manage areas), and
  the Areas sheet itself lives on as an expert tab under Configuration —
  same pattern as everywhere else, one menu entry less.

## 0.1.0.221 — 2026-08-16

- The four Faces tiles each got their "How it works" guide (same plain
  language as the recognition guides), leading back to Faces.
- Frigate page: the Connection tile has a "Change connection" button for
  both views, and the read-only "Frigate's own face recognition" tile moved
  to the expert view.
- Internal: a resident name in a code comment slipped past me again in .220
  and the privacy gate caught it; reworded. (.220 briefly ran on the in-house
  test instance despite the red gate — process slip on my side, the name
  never left the house.)

## 0.1.0.220 — 2026-08-16

- The face area is consolidated into one "Faces" start page (same tile
  pattern as Recognition and Frigate): Known people with an avatar row —
  one real face icon per person, tap it to see every reference picture —
  plus Learning as a guided three-step routine and Unknown for recurring
  visitors you have not named yet. Every tile's first sentence says WHEN
  you need it. The former People and Learn menus merge behind it: easy view
  shows the start page, expert view keeps all detail tabs; Person learn
  moved to the Person section. "How it works" guides per tile follow in a
  later step.

## 0.1.0.219 — 2026-08-16

- The AI vision card on the Recognition page now carries a visible "Beta"
  mark: this path still matures (mixed-grid handling and the per-endpoint
  calibration test are open) and users should know before they rely on it.

## 0.1.0.218 — 2026-08-16

- Internal: two code comments from .217 carried resident names; the privacy
  gate caught them before anything shipped. Reworded, no functional change.

## 0.1.0.217 — 2026-08-16

- Vision diagnosis package (V1-V3 from the lever analysis): the counters now
  see every round outcome (cut-off answers, errors and timeouts per round were
  invisible before — the store said 0 while the logs held 28 of them); a mixed
  round (one run "neither", the other picking a person) is counted as half an
  abstention instead of a positional contradiction; every run records the
  settings it actually ran with (model, thinking switch, token budget, prompt
  mark) plus each arm's visible answer text; and the candidate grid image is
  booked against the orphan cleanup the moment it is written — before, long
  runs lost exactly the evidence pictures of their hardest cases. New optional
  switch `vision_gitter_behalten` keeps no-verdict grids even in lean mode
  (default off, normal 30-day expiry still applies).

## 0.1.0.216 — 2026-08-16

- The "Frigate sync" section is now called "Frigate" and opens with a tile
  start page like Recognition: Connection (live reachability + Frigate
  version), Cameras (which ones are in use), Sync (same balance line as the
  sync page), and the live state of Frigate's own face recognition. The sync
  page itself is unchanged, one tab further (expert view).

## 0.1.0.215 — 2026-08-16

- Fix: the manual model-id check now really works. The probe request used to
  carry the standard verdict instruction ("answer A or B or NEITHER") next to
  its own "Say OK" — two contradicting orders; the model silently ruminated
  into the token cap and the check rejected working models. The probe now
  sends its question without the verdict instruction (verified against the
  live endpoint: real id passes in seconds, fake id gets a clear refusal).

## 0.1.0.214 — 2026-08-16

- Fix: the manual model-id check rejected working models. The tiny "Say OK"
  probe capped the answer at 64 tokens, but some models spend ~140 invisible
  template tokens before the first visible word (measured on Qwen3.5-9B) —
  the probe now allows 512.

## 0.1.0.213 — 2026-08-16

- Vision: you can now add a model id by hand on the Vision page — for
  endpoints that do not list every model they serve. The id is verified with
  a tiny real request first; only a model that actually answers is added to
  the list (marked "manually checked"), nothing unchecked can be saved.

## 0.1.0.212 — 2026-08-16

- The "How it works" guide links on the Recognition cards are now clearly
  visible: semibold, underlined, slightly larger — for a new user they are
  the first thing to click, and they looked like a footnote.

## 0.1.0.211 — 2026-08-16

- Vision: "thinking off" is now the default on endpoints that support the
  switch (local and custom). Reason, measured in production: on a hard
  comparison grid a thinking model talked itself past the token budget
  (47k tokens, requests over five minutes) and the pass ended without a
  verdict; with thinking off the same endpoint answers the same question
  correctly in seconds. A deliberately saved "off" stays respected, and
  the checkbox on the Vision page now shows the value that is actually
  sent.

## 0.1.0.210 — 2026-08-16

- The top navigation section is now called **Configuration** instead of
  Settings (all addresses unchanged).
- The Recognition page warns before you leave it with unsaved body or
  vision changes (browser dialog); the Live switch is exempt because it
  applies immediately.

## 0.1.0.209 — 2026-08-16

- Guide polish after the first read-through: the "Is it for you?" closers
  are gone, and the Face guide now says clearly that suslik alerts on its
  own channels (Pushover, Telegram, MQTT) when a face is recognized or an
  unknown one shows up — completely independent of Frigate, which needs no
  notification setup at all.

## 0.1.0.208 — 2026-08-16

- **Every Recognition card now carries a built-in guide** ("How it works …"):
  plain-language pages inside suslik, no GitHub needed. Each guide has two
  depths and follows the Easy/Expert switch: Easy readers get what the way
  does, what it costs and whether it is for them; Expert adds how the
  verdict forms, written for an interested user, not an engineer.
- **Register buttons per card**: Live and Face carry "Register face" (both
  use the same face library), Body "Register body", AI vision "Register
  vision" (jumps straight to the galleries). Each button leads into the
  existing flow of its own method — registering never drags you through
  methods you switched off. No photo upload, by design: the system learns
  from your cameras; Frigate import remains the supplementary source.
- Today's "Recognized" row now says honestly when a pass is still in
  progress ("events are analyzed as they finish and show up here") instead
  of looking empty for the minute or two the normal path needs after the
  live alert. The page already refreshes itself while a pass is running.

## 0.1.0.207 — 2026-08-16

- **The Recognition page is now the front door of Settings**: clicking
  "Settings" in the top navigation lands directly on the four pillars. In
  Easy mode it is the whole configuration view — the sub-tabs (Cameras,
  Notifications, Recognition chain, Advanced) appear in Expert mode; they
  are only hidden, never locked, and stay reachable by URL.
- Fixes the Face card claiming "0 people · 0 reference images": the counter
  looked in the wrong folder; it now counts the real reference library.

## 0.1.0.206 — 2026-08-15

- Fixes the new Recognition page crashing on load (0.1.0.205 was on the
  production box for minutes and never published): the watcher summary read
  the guard store with the wrong shape. The QA gate gained a new stage that
  starts the built image data-free and fetches EVERY navigation page over
  HTTP — the class "page renders in review but crashes in the image" cannot
  pass silently again.

## 0.1.0.205 — 2026-08-15

- **New "Recognition" settings page: four pillars, one per recognition
  method** (Live watch, Face, Body, AI vision). Each card leads with an
  enable/disable toggle so you decide per method what runs, followed by a
  plain-language sentence, the honest current state and one setup button.
  The Live toggle acts immediately (it starts/stops the set-up watchers
  through the same per-camera gate as the Live tab); body and vision
  changes apply with Save + restart — the same audited settings as the
  Recognition-chain page, one value shown in one more place. Face has no
  off switch today (it is the backbone the other methods hang off) and
  the card says so instead of faking one.
- The page is the first to use the Easy/Expert switch: both modes see the
  four cards, Expert additionally shows status details and deep links.

## 0.1.0.204 — 2026-08-15

- **New Easy/Expert switch in the header** (left of the Live indicator, styled
  like the Theme button): a two-segment pill showing both modes with the
  active one highlighted. For now it is just the switch — the choice is
  remembered per browser (like the theme choice) and pages will adopt their
  simplified Easy views step by step in the coming versions. Nothing is ever
  deleted; Easy only hides.

## 0.1.0.203 — 2026-08-15

Body recognition gets a new, measurably better and properly licensed model:

- **The person path now runs on Intel's OMZ person-reidentification-retail-0277**
  (Apache-2.0 including the model file) instead of DINOv2. Measured on the
  frozen benchmark: 32/30/30 of 37 scenarios across three seed sets vs
  18/16/16 before, max confusion probability 0.20 vs 0.89, and it passes
  the real hard-case walk the old candidate failed. An A/B on fresh
  out-of-sample walks fired 6/12 scenarios vs 3/12.
- **Existing installations migrate themselves**: on the first start after
  the update the service re-trains the person model once in the background
  from the stored, reviewed images (seconds to a few minutes on small
  CPUs); until then the old model keeps judging. A failure is shown on the
  model card, never silent.
- New setting `person_backend` (default `cpu`): compute placement of the
  embedding model. Measured on the reference box: 18.8 ms/image on CPU,
  3.2 ms on the iGPU, 3.6 ms on the NPU — the path is dominated by video
  decode, so CPU stays the default; move it only after measuring, an extra
  GPU context can starve the live watchers.
- The whitening step (PCA, fitted per training fold) ships inside the
  stored model; threshold calibration is unchanged in method and now lands
  at ~0.74 on the reference data.

## 0.1.0.202 — 2026-08-15

Memory fix — the important one. On 2026-08-15 our own production box went
down five times; the measured root cause applies to every installation:

- **Body recognition now runs in its own supervised process** ("personwork")
  instead of unbounded threads inside the main service. A burst of events
  used to spawn one heavy 4K-decode thread each (a 41-event re-analysis
  ate +1.2 GB in 30 s and froze the whole container); now they queue and
  run one at a time, live verdicts take priority over batch work.
- **The RAM budget guard from 0.1.0.172 finally applies to the body path.**
  It existed, but the body path silently skipped it; that skip is now a
  loud error, and a QA-gate check keeps it from ever coming back. Large
  events degrade their sampling instead of exhausting memory (median
  events are unaffected).
- The person-learn harvest goes through the same supervised process
  (it was the second unbounded door).
- A vision-request thread could outlive its deadline holding the full
  request body; it now discards late responses immediately.
- Image sharpness/height are computed once when a judged image is stored,
  instead of re-decoding every image of a pass on every vision run and
  page view.
- New setting `personwork_rss_max_mb` (default 3072) caps the body process.

Next up: a simpler Easy mode (with an Expert mode keeping every control).
Feedback is very welcome: suslik_dev@posteo.de.

## 0.1.0.201 — 2026-08-14

- Removes the "UI address" field and the push-message link again that
  0.1.0.200 had introduced (that version was never published): no real user
  ever asked for it, and suslik is deliberately not reachable from the
  internet, so the link would only ever work on the home network.

## 0.1.0.200 — 2026-08-14

Fix round from a full user's-eye review of all 31 pages:

- **Advanced settings page was unsaveable on a fresh installation**: four
  whitelist keys had no code default, two of them rendered the literal
  string "None" and any save of the whole page failed with HTTP 400. All
  four now carry their code default; this also removes a silent trap where
  the daily update check showed "off" on fresh installs while actually
  running.
- **Alert categories now govern every channel** as the Notifications page
  always claimed: Telegram scene messages and the MQTT scene topics
  (szene_erkannt/szene_unbekannt) respect the category checkboxes; the
  factory default has the matching categories ticked, so unchanged
  installations behave exactly as before. The MQTT data topics (erkennung,
  heartbeat) keep publishing unfiltered.
- **New live watchers no longer default to Pushover blindly**: the channel
  preselection comes from the channels you actually configured; a watcher
  whose channel list ends up empty says so loudly in the log.
- **Push messages can carry a link back into suslik**: set the new "UI
  address" field on the Notifications page and Pushover alerts get an
  "Open in suslik" link to the event, live-alerts or System page. Blank
  keeps the old behavior.
- **Stale texts corrected**: the learning-run, anchors and person-learn
  pages claimed naming/adoption/training would "ship in the next updates"
  although all of it works in this build; the System page now really has
  the "Re-run setup wizard" link and a Backend lamp confirming the
  accelerator self-check, as the setup wizard always promised.
- **Live alerts** is now in the navigation (Live section) instead of being
  reachable only through the Today sidebar.

## 0.1.0.199 — 2026-08-13

Release bundling the internal steps 0.1.0.184–0.1.0.198 (they were never
pushed to GHCR; see the individual entries below for details). Highlights:

- Live watchers now include a preliminary **name stage** on every enabled
  watcher: continuous per-frame voting fires "recognized (live,
  preliminary): NAME" seconds after the trigger, with a proof picture;
  several people in the same pass are reported individually.
- **Appearance view**: the live-alerts day view bundles each pass into one
  card with all stored face pictures and recap videos; Today's "Recognized
  live" cards link straight to it.
- **Per-camera processing resolution** (360p–2160p, default 1080p).
- **Simpler capacity model**: enabled means running — the predictive GPU
  budget that could refuse watchers is gone; overload is handled by the
  runtime sampling throttle. The source test measures the camera's real
  delivery rate.
- Live tab: agent-eye preview, real stream resolution, state/area grouping,
  per-tile hide; recognition chain as its own settings page.

## 0.1.0.198 — 2026-08-13

- Fixes a 0.1.0.197 startup crash of the live engine (a leftover reader of
  the removed quick-verdict field; the engine died three times and paused).
  References for the name stage now load whenever any watcher is enabled,
  and the QA gate got a new drift check that runs the engine-start
  predicates against normalized watcher configs.

## 0.1.0.197 — 2026-08-13

- The per-camera "quick verdict" toggle is gone: every enabled watcher now
  includes the preliminary name stage (it costs microseconds since the
  continuous voting — the toggle only caused confusion; a real pass was
  missed because the switch had silently flipped off).
- Watcher save API: fields missing from a save request now keep their
  stored values instead of silently resetting to defaults — exactly the
  bug that flipped the toggle above.

## 0.1.0.196 — 2026-08-13

- Watcher slots simplified: an enabled watcher now always runs. The
  GPU-budget prediction that could refuse a slot based on estimated
  numbers (and judged the same setup differently depending on start order
  and restart state) is gone — overload is handled at runtime by the
  existing sampling throttle, visible in the status. The only remaining
  guards are the hard cap (5 watchers) and the measured RAM floor.
- The source test now measures the camera's real delivery rate (frames
  after the initial buffer burst) instead of decode throughput — the old
  number could read several times the true frame rate; old test results
  are marked "throughput, not delivery rate" until rerun.

## 0.1.0.195 — 2026-08-13

- Live alerts day view now shows **appearances** instead of single triggers:
  triggers of the same camera within 30 s form one card carrying ALL stored
  face crops (including karenz triggers that never sent an alert) plus the
  recap videos — consistent with the pass view under Recognized. The
  "Recognized live" cards on Today link straight to their appearance card.
- Capacity check fix: a watcher slot candidate is now budgeted with the
  **measured delivery rate** (from "Measure load", anchored to the exact
  source) instead of the source-test throughput, which read several times
  the real frame rate and could refuse a slot that actually fits.

## 0.1.0.194 — 2026-08-13

- Live watchers: per-camera processing resolution (360p / 720p / 1080p /
  1440p / 2160p) on the watcher's configure page. Default is now 1080p —
  measured on a reference walk it fires the preliminary name ~2.4 s earlier
  than 720p; the detection net stays the same size, so the extra cost is
  decode/scaling (use Measure load for your hardware's real numbers).
  Changing the resolution invalidates the source test, honestly.
- Today / Live alerts: clicking a recognized-live card's picture opens the
  full-size proof image.

## 0.1.0.193 — 2026-08-13

- Live watchers: continuous name voting. Every processed face is now matched
  against the reference library across the WHOLE appearance (the embedding is
  already computed by the detector, so this costs a microseconds-range
  nearest-neighbour lookup, not a second model run). After 2 consistent
  hits above the recognition threshold for the same person, a second,
  clearly preliminary "recognized: <name>" message fires — once per
  appearance and person, independent of the instant presence alert. Fixes
  the structural miss where the name was only judged on the 4 trigger-moment
  frames (typically the farthest/worst faces of a walk).

## 0.1.0.192 — 2026-08-13

- New "Live alerts" day view: clicking the live-alert counter on Today opens
  all of that day's triggers with proof picture, name or "unknown", exact
  time, camera and channels — the unknown faces the Recognized-live row
  deliberately hides.

## 0.1.0.191 — 2026-08-13

- Today: the "Recognized live" row now shows only triggers where the quick
  check actually recognized someone — unknown triggers no longer flood the
  row (they stay in the live-alert counter and on the Live tab). The label
  says honestly how many of the day's triggers were recognized.

## 0.1.0.190 — 2026-08-13

- Today: live triggers now show as a "Recognized live" card row right under
  Recognized — proof picture, the quick-check name (or "unknown"), time and
  camera, honestly labeled "quick check, preliminary" (a live trigger is not
  the confirmed verdict). Replaces the plain text list from 0.1.0.188. The
  alert log now records the person and the proof-picture path; older entries
  render without a picture. The MQTT payload's quick-verdict block also
  carries the person as its own field now.

## 0.1.0.189 — 2026-08-13

- Settings: "Recognition chain" is now its own menu item (Cameras ·
  Notifications · Recognition chain · Advanced) with its own save button,
  instead of a section inside Advanced.

## 0.1.0.188 — 2026-08-13

- Today: live-watcher alerts now show as their own list next to the day
  counters — one row per trigger (time, camera, the alert text such as
  "probably …", and the channels it went out on). The engine's alert log
  now records the alert text, so rows from before this version show
  time and camera only.

## 0.1.0.187 — 2026-08-13

- Settings: new "Recognition chain" section — the chain Face → Person →
  Vision rendered in its real order, with per-step condition (always / only
  when the face path could not confirm everyone / off), an honest status line
  (configured vs. actually armed, same source as /health), and a cost hint
  per step. Replaces the two bare dropdown rows in the parameter table;
  changing the order itself is a later stage.

## 0.1.0.186 — 2026-08-13

- Live tab: tiles are grouped by state — Running (including disturbed ones,
  those never hide), Ready, and a collapsed "Not set up" section — instead of
  one wall of equal tiles. Cameras that will never be watchers can be hidden
  per tile; hidden ones live in a collapsed "Hidden" section at the bottom.
- Live tab: the service now probes every camera's real stream once at startup
  (background, cached), so tile headers show the true stream resolution
  without running a source test first.
- Live tab: optional "group by area" view using your camera areas.

## 0.1.0.185 — 2026-08-13

- Live tab: active watcher tiles now show a preview image straight from the
  watcher itself — the processed frame the engine actually analyzes (720p
  watcher scale), refreshed every ~2 seconds. You see what the watcher sees,
  not Frigate's picture.
- Live tab: the tile header now shows the camera's real stream resolution
  (from the source test) instead of Frigate's small detect-substream size,
  which made 4K cameras look like 800×600 webcams. Without a source test the
  detect size is still shown, honestly labeled "(detect)".

## 0.1.0.184 — 2026-08-13

- The service now forces umask 022 for itself and every child process, so
  all files written to the data volume are readable from the host (running
  as root in the container, learning-run references and state files were
  written as 600 and silently missing from host-side backups).

## 0.1.0.183 — 2026-08-13

- Privacy respin of 0.1.0.182 (which was public for under an hour and is
  withdrawn): the author's camera names appeared in code comments inside the
  shipped images. Comments anonymized, and the image privacy audit gained a
  dedicated stage that scans every image for camera names before publishing.
  No functional changes.

## 0.1.0.182 — 2026-08-13

- Live watcher sources: a custom stream URL (source "url") no longer fails for
  non-RTSP inputs — the RTSP transport flag was passed to ffmpeg
  unconditionally, so file/http sources were refused outright ("Option not
  found"), including the software fallback. Found during the CUDA real test.
- NVDEC live decoding confirmed on real NVIDIA hardware: watcher start line
  shows "HW-Decode (nvdec)" on an RTX 2060 (driver 550) against a live
  go2rtc restream, detector at 43 ms/frame.

## 0.1.0.181 — 2026-08-13

- Live watchers pick their video decoder by hardware: VAAPI on Intel/AMD
  (unchanged), NVDEC on NVIDIA cards (previously the live reader was
  VAAPI-only and fell back to software decoding on NVIDIA). The chosen mode
  is logged in the watcher's start line; if the hardware pipe fails, the
  loud software fallback remains.

## 0.1.0.180 — 2026-08-12

- Live watchers now start themselves: the service launches and supervises the
  watcher engine as its own process — restart with backoff on failure, a loud
  alert instead of a crash loop, clean shutdown with the service. A manually
  started engine is detected and never doubled.
- Live watcher alerts are counted on Today and System (per channel, with the
  channels you actually use), backed by a restart-proof log.
- The pose-gate model now ships inside every image variant (no manual staging
  step), and a new QA stage guards the live path on built images.
- Robustness: a corrupted unknown-pool line can no longer break the Today,
  Unknown or Appearances pages — one tolerant reader everywhere.
