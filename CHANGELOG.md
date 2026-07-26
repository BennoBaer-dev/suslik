# Changelog

All notable, user-visible changes to suslik. Versions 0.1.0.25–0.1.0.27 were internal
iterations on the author's production box and were never pushed to GHCR; their changes
ship together with **0.1.0.28**. Likewise 0.1.0.29–0.1.0.32 ship together with **0.1.0.33**.

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
