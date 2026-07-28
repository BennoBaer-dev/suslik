# Changelog

All notable, user-visible changes to suslik. Versions 0.1.0.25–0.1.0.27 were internal
iterations on the author's production box and were never pushed to GHCR; their changes
ship together with **0.1.0.28**. Likewise 0.1.0.29–0.1.0.32 ship together with **0.1.0.33**,
and the performance-wave steps 0.1.0.34–0.1.0.44 ship together with **0.1.0.47**.
The Today-redesign steps 0.1.0.48–0.1.0.53 ship together with **0.1.0.54**, and the
local steps 0.1.0.55–0.1.0.62 ship together with **0.1.0.63**.

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
