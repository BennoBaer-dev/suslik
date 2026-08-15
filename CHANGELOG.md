# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). History older than 0.1.0.180 has been trimmed from
this file — the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git
history.

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
