# Changelog

All notable, user-visible changes to suslik. Versions 0.1.0.25–0.1.0.27 were internal
iterations on the author's production box and were never pushed to GHCR; their changes
ship together with **0.1.0.28**. Likewise 0.1.0.29–0.1.0.32 ship together with **0.1.0.33**,
and the performance-wave steps 0.1.0.34–0.1.0.44 ship together with **0.1.0.47**.
The Today-redesign steps 0.1.0.48–0.1.0.53 ship together with **0.1.0.54**, and the
local steps 0.1.0.55–0.1.0.62 ship together with **0.1.0.63**. The learning-module and
areas construction steps 0.1.0.64–0.1.0.91 ship together with **0.1.0.92-alpha**, and the
QA/diagnostics steps 0.1.0.93–0.1.0.95 ship together with **0.1.0.96-alpha**.

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
