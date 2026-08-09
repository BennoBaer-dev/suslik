# Changelog

All notable, user-visible changes to suslik. Versions 0.1.0.25–0.1.0.27 were internal
iterations on the author's production box and were never pushed to GHCR; their changes
ship together with **0.1.0.28**. Likewise 0.1.0.29–0.1.0.32 ship together with **0.1.0.33**,
and the performance-wave steps 0.1.0.34–0.1.0.44 ship together with **0.1.0.47**.
The Today-redesign steps 0.1.0.48–0.1.0.53 ship together with **0.1.0.54**, and the
local steps 0.1.0.55–0.1.0.62 ship together with **0.1.0.63**. The learning-module and
areas construction steps 0.1.0.64–0.1.0.91 ship together with **0.1.0.92-alpha**, the
QA/diagnostics steps 0.1.0.93–0.1.0.95 ship together with **0.1.0.96-alpha**, and the
person-recognition construction step 0.1.0.112 ships together with **0.1.0.113**, and the
performance/fusion steps 0.1.0.114–0.1.0.117 ship together with **0.1.0.118**, and the
frame-distributor and vision steps 0.1.0.142–0.1.0.167 ship together with **0.1.0.168**, and the
learning-area/run-management steps 0.1.0.119–0.1.0.128 ship together with **0.1.0.129**.

## 0.1.0.168 — 2026-08-09

Versions 0.1.0.142–0.1.0.167 were built and tested on the author's production box;
their changes ship together with **0.1.0.168**. This is an early working version,
published ahead of completion so testers can try the new recognition path.

- **Vision detect: a third, independent recognition path.** Alongside face
  recognition and the person model, a vision-language model can now judge a
  walk-through. The whole pass is presented as one candidate grid against your
  approved galleries — not single frames — which measurably beats picture-by-picture
  comparison. It runs against a local llama.cpp server or any OpenAI-compatible
  endpoint you configure; nothing is sent anywhere unless you set that up.
- **Gallery wizard with automatic curation.** Reference proposals are scored on face
  visibility, lighting and completeness, each cell carrying the reason it was picked
  or dropped, so a usable gallery comes together without hand-sorting every crop.
- **Recognition test for any past walk-through.** One page shows face, person and
  vision side by side for the same pass, with a live narrative log of what each path
  did and why — the fastest way to see where a judgement comes from.
- **Model guidance from measurements, not guesses.** The vision settings show which
  model class is needed, based on our own measured runs rather than vendor claims.
- **One download and one decode per event.** Frames are now handed out by a single
  distributor instead of every consumer fetching and decoding its own copy. Same
  results, noticeably less work per event; frozen fixpoints prove the output is
  unchanged.
- **Diagnostics you can hand over.** An optional control store keeps the images a
  judgement was based on, and `/health` reports frame fallbacks — both aimed at
  making remote support possible without guesswork.

## 0.1.0.140 — 2026-08-06

- **Model status tells the truth about the stranger folder in every case.** The line
  now distinguishes strangers that went into this model, strangers that are collected
  but not part of it (a single learned person has no classifier to put them in), and
  too few of them to calibrate the threshold against.

## 0.1.0.141 — 2026-08-06

- **The stranger folder can no longer stall training.** An unreadable file in
  `personlern/fremd/` (broken copy, non-image) is skipped and counted instead of
  silently stopping every future training run; if a run does fail, the model page
  says so in red with the time, instead of presenting the previous model as current.
- **Training and threshold always describe the same model.** With fewer than five
  stranger images they now stay out of the model entirely (before, they were
  trained from the first image while the threshold was measured without them —
  the status promised far more coverage than the shipped model had).
- **The calibrated threshold is steadier.** It is now the maximum over three fixed
  cross-validation splits instead of one, so a single lucky split no longer moves
  it. `.JPG`/`.jpeg`/`.png` spellings are accepted in the stranger folder.
- **Honest status everywhere.** The armed/not-armed prefix on the model card
  follows the real switch state; a manually set threshold is called "set by you"
  (with the calibration named for comparison) instead of "calibrated"; and the
  material pages now say what actually makes the model strong — images from many
  different days, and confirmed strangers for the threshold — with a per-person
  images/days/cameras line and an honest marker when a person's material covers
  too few days.

## 0.1.0.139 — 2026-08-06

- **Body recognition learns what a stranger looks like.** Confirmed stranger images in
  `personlern/fremd/` are trained as a class of their own, behind your people. If the
  model reads a body as a stranger, that event is dropped before it can become a hit —
  strangers never appear in alerts or on Today.
- **The decision threshold is calibrated against real strangers.** As long as stranger
  material is present, the threshold is the strongest confidence any real stranger
  reached for one of your people in cross-validation, plus a margin, instead of a value
  measured only between your learned people. Model status names both sides honestly:
  how many of your own images still pass, and how many of them would reach that
  threshold for the wrong person. Without stranger material nothing changes.

## 0.1.0.138 — 2026-08-06

The sync construction steps 0.1.0.130–0.1.0.137 ship together with **0.1.0.138**.

- **New "Frigate sync" page (own menu item).** A full reconciliation of your reference
  library with Frigate: what is on both sides, what is ready to transfer, what you
  deleted in Frigate (each an explicit decision — offer it again or respect the
  deletion, nothing is re-sent on its own), what was sent earlier through Frigate's
  API (Frigate renames those, so suslik says honestly that it cannot verify them),
  and what lives only in Frigate (import section, with a warning about your own
  renamed uploads). The balance line adds up across all classes.
- **Selective transfer.** Every candidate is shown as a picture, individually
  tickable, with select-all/deselect-all; a confirmation step summarizes what goes
  out, and after the transfer each image shows its real result — uploaded, or the
  exact reason Frigate refused it. Deselected images are remembered and skipped by
  the automatic sync too.
- **Pre-check like Frigate's.** Before sending, suslik runs each candidate through
  a face detector the way Frigate will on arrival; likely rejections start unticked
  (you can still send them — Frigate's verdict is the truth). The check runs in the
  background and caches per image.
- **Export survives bad images and explains itself.** One rejected image no longer
  stops the run: errors are classified per image vs. fatal, three identical errors
  in a row raise a "wall" suspicion without aborting, and a one-click diagnosis
  bundles the suslik report with Frigate's own log (fetched over the API), ready to
  paste into an issue. A live status line shows whether Frigate's face recognition
  is on, read from Frigate as the page loads.
- **Rejection memory with judgment.** What Frigate genuinely rejected per image
  (400 from register) is remembered so the automatic sync stops re-running the same
  refusals; ambiguous errors (Frigate's generic 500) expire after a day and are
  retried, transport errors and person-level errors are never blamed on an image,
  and a detected wall discards its markers — a Frigate outage can no longer lock
  the whole queue out permanently.
- **One sync at a time.** Concurrent sync attempts are refused cleanly (409), and
  the automatic exports skip a round instead of racing a running transfer.

## 0.1.0.129 — 2026-08-05

- **Learning runs can be deleted completely.** One button per run on the anchor page
  removes all its clusters (named and dismissed ones included) and every harvested
  image — permanently, no trash folder. "Delete all old runs" clears everything except
  the newest run with a single confirmation. References you already adopted into
  recognition always stay (they are copies in your reference library), and a run that
  is still working can never be deleted.
- **Dismiss with memory.** Dismissing a cluster removes its images but remembers the
  cluster — re-harvests of the same events inherit the dismissal silently instead of
  asking about the same stranger again.
- **"Looks like" also recognizes people already in your system.** Anchor clusters of
  residents now get a suggestion badge ("already in your system" / "named on another
  cluster") instead of showing up unlabeled; the cluster overview shows the badges too,
  and re-harvested duplicates of unnamed clusters are marked and point to the newer run.
- **False-trigger class for empty events.** Events without any person can be marked as
  such in the label flow ("No person in this event"); they get their own silent class,
  stop showing up as open questions and are counted honestly on the QC report.
- **Adopting an already-covered cluster is no longer an error.** If every selected
  image is near-identical to references a person already has, the cluster is closed as
  adopted ("already covered — nothing copied") instead of failing with an error
  (issue #17). A guard makes sure this can never silently close a person whose
  reference images were deleted meanwhile.
- **Person learn and the Frigate sync now read the Frigate address from your saved
  settings** (issue #18). Both paths used to read it only from the process environment,
  which UI-configured installations never set — harvesting runs failed with
  *unknown url type* and the sync card showed the same error. Nothing to configure:
  the address you entered in the setup wizard now reaches every part of the program.
- **Writing references back to Frigate works with current Frigate 0.18.** Frigate
  changed its face-library API (upload is now `create` + `register`, uploads are
  renamed and processed asynchronously); suslik uses the new endpoints, keeps an
  export protocol so nothing is ever uploaded twice, never deletes anything in
  Frigate, and reports honestly when Frigate refuses uploads because its own face
  recognition is disabled.
- **Smaller improvements.** Today cards and recognition chips show a real photo for
  body-recognized passes (kept per day); appearances show how a pass was recognized;
  a person-learn run that finds no confirmed passes for the chosen person now explains
  why (with the person's last-seen date) instead of finishing silently; a duplicate
  guard in the harvest prevents storing the same frame twice; the GT correction bar
  on recognized events reads "Correct if wrong" instead of asking "Who was it?"
  (issue #17); video exports download with the correct `.mp4` name (issue #15).

## 0.1.0.118 — 2026-08-05

- **Recognition got a lot faster.** All judgment frames now come through one pinned
  pixel path: the color conversion is identical on every machine, video decoding can
  run on the GPU (Intel via VAAPI, NVIDIA via NVDEC — with hard gates: 8-bit 4:2:0
  material only, validated drivers only, and a loud software fallback), and only the
  sampled frames leave the decoder instead of every frame. Measured on the author's
  machine: a face learning run dropped from 6.6 to 2.9 seconds per event; the frame
  supply for a 4K HEVC event fell from 5.2 to 1.5 seconds. New environment switch
  `SUSLIK_HWDEC` (`auto`/`vaapi`/`nvdec`/`aus`), default `auto`. **Honest note:**
  because the color conversion is now pinned identically everywhere, a judgment that
  sat exactly on a decision threshold can flip once after this update; after that,
  everything is consistent again. Nothing to migrate on your side.
- **Face and person recognition now work together on Today.** A pass with no usable
  face is attributed to the person the body path recognized (it takes at least as
  many supporting events as your fire rule requires), clearly marked *via person
  recognition, no face*. Recognized cards count these passes and they no longer show
  up as unknown visitors. Face judgments always take precedence, and passes show
  where their recognition came from (face / person / both).
- **Full backup and restore.** The System page can download one portable archive with
  everything you taught your installation — settings (including connection values),
  the face reference library, learning-run results, the whole person-recognition
  material with your review verdicts, and the trained models. Restore replaces those
  parts (keeping one `.pre-restore` copy of each) and restarts the service. The video
  clip cache and per-event analysis artifacts are deliberately not included.
- **Measured decision threshold + configurable fire rule for person recognition.**
  After every training the threshold is measured by cross-validation on your own
  approved material (honest limit: it calibrates *between* your learned people —
  strangers are not in the material yet). The fire rule (window, supporting events,
  cool-down) is editable under *Person → Model status*; a manually set threshold
  wins until you clear the field.
- **Smaller improvements.** Person alerts attach the best body crop of the
  walk-through instead of the crop of the firing moment; the person-learn wizard
  keeps your person selection when clicking an event-count preset; the discard/delete
  buttons on the review and body-images pages work again; the hardware hint now also
  covers a cuda image without an NVIDIA GPU and a rocm image with one; event analysis
  starts a bit faster (one metadata probe per clip instead of three).

## 0.1.0.113 — 2026-08-04

- **Person recognition (preview) — a second recognition path that works without
  a visible face.** It learns residents by their whole appearance (build, hair,
  posture) from your own recordings: a guided learning run under *Learn → Person
  learn* harvests full-body images (tied to a person only when a face-confirmed
  walk-through proves it), you review every picture, and a small local model
  (DINOv2 embeddings + classifier) retrains in seconds. Manage the material under
  *Person → Body images*, arm/disarm the live path under *Person → Model status* —
  it stays off until at least one person is learned **and** reviewed. When armed,
  it judges live events independently of face recognition (own threshold, fire
  rule and cool-down), alerts via Pushover (best body crop of the walk-through as
  image), Telegram (event clip as video, same settings as face alerts) and MQTT
  (`verifyd/person_erkennung`), and every alert is clearly marked as *person
  recognition, not face*. The decision threshold is not yet calibrated against a
  large stranger set — treat it as a preview. Full guide:
  [docs/person-recognition.md](docs/person-recognition.md). Harvesting currently
  runs on the CPU (roughly 15–30 s per event); GPU/NPU support for this path is
  planned.
- **Telegram video height is configurable** (`telegram_hoehe`: 720 or 480) and
  applies to face and person alerts alike.
- **Saving a video from the player now yields a proper `.mp4` file** (issue #15:
  the browser picked a wrong extension from the event id in the URL).
- **NOTICE now covers the new model files** (DINOv2 ViT-S/14, Apache-2.0, with
  conversion notice; RTMPose, Apache-2.0, with provenance) including the full
  Apache-2.0 license text in the images.

## 0.1.0.111 — 2026-08-03

- **Frigate API errors now carry detail.** When Frigate answers with an HTTP
  error, the log used to show only `HTTP Error 500: Internal Server Error` —
  useless for remote diagnosis (issue #14: 67 identical lines, no path, no
  cause). The error now includes which request failed and what Frigate wrote
  into the response body, while existing retry classification (404/400) keeps
  working unchanged.

## 0.1.0.110 — 2026-08-03

- **Loud warning when `/data` is not a mounted volume.** A tester lost people,
  events and settings by running the container without a `volumes:` entry: the
  data lived inside the container and vanished when `docker compose up` replaced
  it for an update (issue #13). The startup self-check now prints a warning and
  the UI shows a persistent banner until a real volume or bind mount is in place.

## 0.1.0.109 — 2026-08-03

- **Version numbers no longer carry an `-alpha` suffix.** Installations older than
  0.1.0.92 could not parse a tag like `v0.1.0.108-alpha` and therefore never saw an
  update hint, no matter which release was marked as latest — measured on a real
  0.1.0.63 container. Dropping the suffix fixes that for every old installation at
  once. This is still an alpha-stage project; the version number just says so through
  its leading `0.1.`, and the README says it in words.
- **Fixed: the learning run page claimed that adoption into recognition "activates
  with the coming updates".** It has been working since 0.1.0.102.

## 0.1.0.108-alpha — 2026-08-03

Ships together with the 0.1.0.107 fixes below (0.1.0.107 was never promoted to `latest`).

- **Fixed: the new API export was still gated on `ssh`/`scp` being present.** Those
  are deliberately not in the images, so the automatic reference export to Frigate
  would have stayed disabled even after the switch to the HTTP API. It now only
  needs a configured Frigate URL, and a failing export is reported in the log
  instead of passing silently.
- **Removed `sshpass` from all images.** With the export on the HTTP API, no SSH
  tool is left in the containers at all.

## 0.1.0.107-alpha — 2026-08-03

- **Fixed: exporting reference images to Frigate no longer uses SSH.** The export
  path copied files over SSH, which only ever worked on setups where suslik has
  root SSH access to the Frigate host. It now uploads through the documented
  Frigate HTTP API (`POST /api/faces/{name}`), like every other Frigate call.
  This also removes a command-injection hole: a person name containing shell
  characters was interpolated into a remote shell command, and an ordinary name
  like `O'Brien` broke the whole export.
- **Fixed: person names with dots, apostrophes or parentheses were half-broken.**
  A face imported from Frigate as e.g. `Anna.B` showed up on the Known people
  page, but its thumbnails 404'd and deleting them failed. Name validation now
  comes from one shared definition used by both the import and every consumer.
- **Fixed: deleting a person under-reported how many images were moved to trash**
  (`.webp` files, which is what Frigate delivers, were not counted).
- **Fixed: two persons whose names differ only by space vs underscore shared one
  suggestions file**, silently mixing their candidates.
- **Fixed: deleting a multi-face crop from the Known people library failed with
  "ungueltiger Pfad".** Same root cause family as the broken crop images in
  0.1.0.103: filenames with `~` (multi-face crops) were rejected, this time by
  the delete path. The filename pattern now lives in one central place used by
  every route that validates image paths, so this class cannot scatter again.

## 0.1.0.106-alpha — 2026-08-02

- **New: import/resync faces from Frigate on the Known people page.** The Frigate
  face import used to live only inside the setup wizard — after restoring a
  configuration the wizard is skipped, leaving no way to trigger it. The Known
  people page now has a "Sync faces from Frigate" button; the import is
  incremental (only images missing locally are fetched, nothing is deleted).

## 0.1.0.105-alpha — 2026-08-02

- **Fixed: the configuration download was incomplete on environment-configured
  installs.** "Download configuration" only exported settings changed through the UI;
  if the Frigate URL or MQTT broker came from environment variables or the compose
  file, a restore on another machine came up without a Frigate connection. The
  download now includes the effective connection settings (Frigate URL, trigger
  mode, MQTT); values set through the UI always win. (0.1.0.104 was a local
  intermediate and ships together with this release.)

## 0.1.0.103-alpha — 2026-08-02

- **Fixed: crop images with `~` in the filename showed as broken (404).** Events with
  several faces name their crops `<event>~2.jpg`, `~3.jpg` and so on; the image routes
  for the unknown-pool crops and for reference photos did not accept the tilde.
  Reported by a community tester with an exact trace (#11) — thanks.

## 0.1.0.102-alpha — 2026-08-01

- **Adoption (learning module complete):** a named cluster can now be adopted into
  recognition with one click. The write is all-or-nothing, near-duplicates of already
  learned references are skipped and counted, changed settings since naming are
  surfaced for confirmation, every adoption lands in a protocol, and the drift
  watchdog checks the reference library right afterwards (System page shows red).

## 0.1.0.101-alpha — 2026-08-01

- **Cluster naming (learning module, stage E4a):** open an anchor cluster and name it.
  The page recommends the best faces per perspective (near-duplicates and same-detection
  copies are set aside with the reason shown on each image), lets you select images by
  clicking, warns when a name matches an existing person, and keeps every decision safe
  across restarts. Adoption into recognition ships with the next stage; naming alone
  changes nothing in detection yet. The learning-run page links the naming step
  directly once grouping is done (0.1.0.98-.100 were internal steps); every cluster card carries a clear naming button.

## 0.1.0.97-alpha — 2026-08-01

- **What's-new box on the Today page:** the latest releases' highlights at a glance —
  collapsed to three entries, expandable to the last ten, dismissible per version
  (it returns when the next version arrives). No server state; the dismissal lives
  in your browser like the theme choice.

## 0.1.0.96-alpha — 2026-08-01

Reliability and honest-diagnostics wave (includes the internal steps .93–.95).

- **AMD/ROCm (`-rocm`, testing) is now actually usable:** the startup self-check can
  probe MIGraphX, the log shows `/dev/kfd` status, real binding and a ROCm version
  line, and the setup wizard offers and saves the AMD backend (the previous alpha's
  `-rocm` image could not be configured at all).
- **CUDA:** hosts without an NVIDIA card get a clear "no /dev/nvidia* device" note
  instead of a misleading "runtime mismatch?" warning.
- **Failure-series watchdog:** three consecutive failed analyses trigger an immediate
  alert — on Pushover *and* Telegram, whichever is configured.
- **`/health` tells the truth:** `ok` is derived from the startup self-check
  (`startup_fails` field); a machine-readable `state/startup.json` accompanies the
  human-readable log.
- **Error events explain themselves** on the pass page (reason from the per-event
  analyze log instead of a bare "error" badge), and the Frigate-unreachable banner
  is now English and names the failing endpoint.
- **Setup, updates and restore are contract-tested before every release:** old data
  layouts migrate cleanly, the wizard round-trips for every image variant, config
  backup/restore is verified end-to-end.

## 0.1.0.92-alpha — 2026-07-31

First release with the **application source published** in this repository, and the
first one labeled what it is: an **alpha work in progress** (see the README status).

### Added
- **Learning module (guided runs, usable today)**: a wizard plans a learning run over
  as many past person events as you choose — it estimates the duration on *your*
  hardware first (a one-time self-benchmark), harvests faces from the recorded clips
  through calibrated quality gates (candidate → crop-worthy → anchor-ready), and
  groups the anchor-ready faces into clusters of **recurring people** across days and
  cameras. Runs survive restarts and resume; progress is visible per phase, per event,
  with live counters. An Anchors page shows every cluster with its face crops — each
  crop clicks through to the clip it came from. Naming a cluster (one step instead of
  labeling single images) is the part still under construction.
- **Camera areas, stage 1**: group cameras into parts of your property (driveway,
  backyard, …). One camera belongs to at most one area; everything unassigned stays in
  **Default**, and deleting an area returns its cameras there. Areas act as *views* on
  Today, Appearances and Events — passes are always grouped and judged across the whole
  property, an area only picks the passes that touched it — and alerts name the area of
  the camera (as text; per-area alert behavior is stage 2). Saving needs no restart.
- **Analysis rate per learning run**: choose the sampling frames-per-second per run,
  with a measured yield/time trade-off explained right in the wizard.
- **Sound in clip transcodes**: browser and Telegram copies now keep the audio track.
- **Clip cache size cap** (`clip_cache_max_gb`, default 50 GB) next to the age-based
  eviction, and the cache size is visible on `/health` — from a field report where the
  cache had quietly grown to ~74 GB.
- **CPU thread cap** (`cpu_threads`) for inference and transcode sessions.

### Changed
- Recognition-judgment invariance is now proven per release across CPU, Intel
  iGPU/NPU and CUDA with fixed-point acceptance runs; NVENC full-hardware transcode
  quality was recalibrated against field footage.
- Many UI honesty passes: per-phase progress with checkmarks, a "working" pulse with
  an honest stall warning, visible per-camera video buttons, and clearer wording
  ("passes" instead of "scenarios").

### Known limitations of this alpha
- Naming/adoption of learned clusters is under construction; areas have no per-area
  alert scoping yet; building from source needs model files that are not in the git
  tree (see installation.md). Interfaces and data formats may still change.

## 0.1.0.63 — 2026-07-28

Pass drill-down pages, a fourth image variant for older Intel iGPUs, and better
self-diagnosis when the image doesn't match the hardware.

### Added
- **`gpu-legacy` image variant (testing)**: Intel moved Gen8/Gen9/Gen11 graphics
  (UHD 6xx, 6th–10th gen Core) out of its current compute runtime, so the regular
  `gpu` image cannot bind those iGPUs — they silently ran on CPU. The new
  `gpu-legacy` variant ships Intel's legacy1 runtime (24.35 branch) instead.
  Marked *testing* until confirmed on real Gen9 hardware (issue #6); there is no
  `latest-gpu-legacy` tag yet, pull the version tag.
- **Pass detail pages**: a pass (one walk across the property) now has its own
  page — time span, camera route, best face per event — and event pages carry a
  strip to walk through the whole pass. Unknown visitors get stable U-numbers
  used consistently across the UI.
- **Variant hint**: if the startup probe finds hardware that a *different* image
  variant would support (an Intel iGPU on the cpu image, an older iGPU that needs
  gpu-legacy, an NVIDIA GPU without the cuda image), the UI banner and the
  startup log now say which variant to use. No hint when everything matches.
- **`/health` reports the running version** — please include its output when
  filing an issue; log excerpts often miss the startup banner.

### Improved
- The reference-drift guard (release tooling) was hardened: a newly enrolled
  person no longer crashes the check, and a missing baseline now turns the check
  red instead of silently green.

### Internal
- Groundwork for a "no person found (likely false trigger)" class ships disabled:
  a backtest against real recordings found no such events on the author's
  property (every candidate was a real person passing on the sidewalk), so no
  thresholds are set and nothing is suppressed.

## 0.1.0.54 — 2026-07-28

The Today redesign plus a calibrated false-detection filter: the first page now answers
"who was on the property, when, and where did they go" — and stops counting wheel hubs
and foliage as faces.

### Added
- **Person day view (`/auftritte`)**: clicking a person on the Today page now opens their
  passes for the day — one block per pass with the time span, the camera route (cameras
  with an actual confirmation in bold), the best face shot, and a thumbnail strip showing
  how the face developed across the pass (only events that actually have a face crop;
  unconfirmed near-hits are dimmed, the rest is summarized as "+N events without a
  face"). Single events stay reachable as evidence but are no longer the entry point.
- **False-detection filter**: the face detector occasionally fires on static objects
  (a wheel hub, hedges, fabric). A signature calibrated on 407 hand-labeled detections
  (high frontality + edge-rich + moderate detector score) now removes those from
  counting, display and the unknown-visitor pool — **recognition itself is deliberately
  untouched**, and the Today page shows a footnote with what was filtered so nothing
  disappears silently. Thresholds are configurable (`fd_front_min`, `fd_sharp_min`,
  `fd_det_max`); the detector's own threshold is now visible as `det_thresh`.
- **Confirmed-stranger visibility**: a pass you labeled as "Stranger" no longer vanishes
  from the Today page — it stays visible as unknown with a quiet "confirmed stranger"
  badge, and "?" (unclear) labels keep the pass on the board too.
- **Clickable day stats**: "Unidentified" and "Passes" jump to their sections,
  "Events analysed" opens the full event list of that day.
- **Per-detection metrics** are now persisted per event (time, size, sharpness,
  frontality, detector score, filter flag) — future threshold changes can be simulated
  on existing data instead of re-analyzing clips.

### Changed
- **Machine-independent pass grouping**: scenario grouping now uses Frigate's real event
  end time instead of the analysis wall clock — the same day groups identically on fast
  and slow hardware (measured before: 42 of 103 passes could flip at 5× analysis time).
- The unknown-visitor card wording "not grouped yet" is now **"no visitor profile yet"**
  (it describes the visitor pool, not the cameras — thanks for the report in issue #5).
- "N unknown" phrasing replaced by honest event counts ("N events with an unmatched
  face") wherever it could read as a number of people.

### Fixed
- Scenario grouping logic extracted into its own module with a byte-identical rendering
  proof; the day view, person view and tests now share one implementation.
- `/offen` displays the filtered face count (the number you act on), matching its filter.

## 0.1.0.47 — 2026-07-27

The performance wave: analysis cost per event dropped from roughly a CPU minute to
~8–13 CPU-seconds warm on the author's Intel box — with judgments proven unchanged
(fixed-point acceptance exact on CPU, Intel GPU/NPU and CUDA).

### Added
- **Persistent analysis worker**: models load once and stay warm between events instead
  of being rebuilt per analysis. The worker exits by itself after 15 min of quiet (that
  is the only way ONNX Runtime returns its memory) and restarts lazily; a memory
  threshold (`worker_rss_max_mb`, default 4096) triggers a clean restart if it ever
  balloons. Can be disabled with `worker: false`.
- **Automatic accelerator placement** (`backend: auto`, new default in the Intel image):
  a one-time startup benchmark decides where recognition runs — Intel NPU
  (`openvino:MIXED`: detector on GPU, recognition on NPU), GPU, or CPU — and the choice
  sticks in `state/placement.json` until hardware, runtime or version change. On the
  author's Core Ultra the NPU runs recognition at ~0.3 ms CPU per inference vs ~24 ms
  on the iGPU path. Explicit values (`openvino:GPU`, `cuda`, `cpu` …) behave as before.
- **Real hardware probes in the self-check**: "found & usable — device bound in real
  probe" replaces the earlier "engagement unconfirmed" question marks; `/health` now
  reports the resolved backend and placement.
- **Silent-decode guard**: decoded frames are counted against the container's packet
  count. Truncated/glitchy clips are flagged (UI badge, capped verdicts, below 50 %
  readable the event is treated as failed) instead of silently judging from the
  readable beginning — previously a corrupted clip could lose 39 % of its frames
  without a trace.
- **Lazy browser copies**: the web-view video is transcoded on first click (spinner)
  instead of eagerly for every event (~1.3 CPU-hours/day saved on the author's box).
- **Full-hardware NVENC pipeline** on NVIDIA (decode + scale + encode on the GPU,
  probed with the exact pipeline at startup; issue #4: 15.3 → 1.1 CPU-s per clip),
  and per-encoder quality calibration (`q_hw` for NVENC, `q_vaapi` for VAAPI) for
  smaller files at equal visual quality.
- **Aspect-ratio detector sizing**: the detector input follows the clip's aspect ratio
  (multiple-of-32 grid) instead of a fixed square — bit-identical detections measured,
  about a quarter less GPU time on 16:9 material.

### Fixed
- **Double model build on startup** (one rebuild per process) — about a quarter of the
  former cold-start CPU; a provider guard now also verifies after every rebuild that
  sessions really sit on the requested device, heals once, and reports if not.
- **Worker memory retention**: idle unload kept ONNX-Runtime arenas alive and grew RSS
  per cycle; replaced by idle process exit, which really frees the memory.

### Changed
- **Analysis decode intentionally stays on CPU.** A measured trial of GPU video decode
  (VAAPI) shifted recognition scores by up to 0.021 (tolerance 0.005) and flipped
  window judgments on fixed-point clips — so hardware decode is banned from the
  judgment path. The media engine still does all display transcodes, where no judgment
  is made. Quality over speed, with numbers.

## 0.1.0.33 — 2026-07-26

### Added
- **Update notice**: suslik now checks GitHub once a day (anonymous request to the
  public releases API, nothing else leaves your system) and shows a quiet hint in the
  header plus a clear note on the start page when a newer image is available. Can be
  switched off with the new `update_check` setting (Settings → Advanced).

### Fixed
- **Hardware video transcode was silently falling back to CPU in ALL published images**
  (reported by an early tester — thank you!): the VAAPI device path was hard-coded and
  the Intel image lacked the media drivers. The encoder is now probed with a real test
  encode at startup (NVENC → VAAPI per render node → CPU), the chosen encoder shows up
  in the startup self-check (`video h264_vaapi(...)`), 10-bit sources are converted
  explicitly, and a runtime fallback to CPU is logged instead of happening silently.
  Telegram clips and browser copies are now several times faster on Intel and NVIDIA.
- **An unreachable MQTT broker at startup crashed the service in a restart loop**
  (the trigger client connected synchronously). It now connects asynchronously with
  automatic retry, and the internal watchdog monitors the trigger connection too.

### Changed
- **The service log is now fully English.** Category values, data files and MQTT
  topics/payloads are unchanged — existing automations keep working.

## 0.1.0.28 — 2026-07-25

The theme of this release is the **unknown-faces pool**: collecting, clustering and
turning unknown faces into enrolled people, driven by a live enrollment test that
surfaced a series of real defects.

### Fixed
- **"Find new faces" could hang forever** after an enrollment: the reference-cache
  reader used a stale key and silently returned nothing, so the search never finished
  (0.1.0.25).
- **Reference watchdog showed red with no reason** after every enrollment inside the
  container: its self-test crashed on a missing fixture and the error was swallowed.
  The stderr is now surfaced in the banner (0.1.0.25).
- **Merge suggestions ("same person?") vanished before you could answer them**: they
  were only produced at the exact moment a cluster spanned two identities; the next
  automatic re-cluster overwrote them with an empty list. They are now derived fresh
  on every run from the similarity of all active identity pairs.
- **"Different" on a merge suggestion is now remembered** — previously the row was
  only hidden and the same question came back after every reload.

### Changed / added
- **Unknown-pool collection**: up to **3 best faces per event** (with a diversity
  guard) instead of a single one — a walkthrough no longer gets reduced to one
  unlucky crop.
- **Clustering rebuilt** as average-linkage agglomeration; the previous greedy-seed
  approach could split one person into many identities or glue different people
  together depending on insertion order.
- **Static-object quarantine**: clusters whose images are near-identical to each
  other but similar to no enrolled person (wheel arches, light patterns picked up by
  the face detector) are auto-flagged and moved to their own collapsed bucket instead
  of polluting the people cards.
- **Merge suggestions now show faces**: each "same person?" row displays up to three
  crops of *both* identities — the question is answerable at a glance.
- **Unknown cards are actionable**: cards on Today show a sample face, are clickable,
  and open a panel where you pick exactly the faces you want to assign to a person —
  faces from the same walkthrough listed first.
- **Delete a whole person** (name + all references) from the UI; the data is moved to
  a recoverable trash folder, not erased.
- **Event page groups images per person** instead of one flat grid, with a **visible
  boundary**: groups whose best match score is below the "unknown" threshold sit
  under a divider marked *weak matches — the name is a guess*.
- **Progress feedback**: re-clustering ("Reorganize") and reference searches show
  phase and elapsed time instead of appearing frozen.

## 0.1.0.24 — 2026-07-25

First release announced to outside testers.

- Reliability wave for the alert path (Pushover/Telegram/MQTT), including the choice
  between picture and video per Telegram notification.
- Four-area web UI with light/dark theme, day-by-day navigation on Today.
- License clarity: MIT for the code, `NOTICE` for the bundled third-party models
  (InsightFace `buffalo_l` is research-only — see NOTICE before commercial use).
- Guided first hour: setup wizard with honest error messages, first-success feedback,
  per-channel notification tests.
- Earlier hardening waves (input validation, atomic persistence, honest first-run)
  are summarized in the release notes of v0.1.0.24.
