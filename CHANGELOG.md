# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.037 (2026-10-24)

This release bundles 0.1.1.036, which was built but never pushed.

Faster with a large face catalog. When references are added, suslik now updates its catalog in place instead of reading and
checking all of it again. Pages that list people only check what changed since their last look.

The System page no longer compares the face library with Frigate on every visit. It shows a link to Frigate sync instead, where
the comparison still runs.

After a restart, suslik reads the detection record and the list of people in the background right after the start check. The
first visit to Presence, Today or System then no longer waits for this, as long as the background read has finished. If the
background read fails, the start counts as failed and the status stays red until the next start.

suslik now keeps a local record of how face candidates become references (offered, selected, taken over, used). It stays on your
machine, holds no names, and prepares better storage rules in a coming version.

## 0.1.1.035 (2026-10-23)

Poll interval and clip delay can now be changed on the Advanced page and take effect without a restart. New defaults: Frigate
is polled every 10 seconds instead of 20 (poll mode only), and the clip is fetched 5 seconds after an event ends instead of 15.
On the first start of this version, an installation that still uses the old defaults is switched once; values you set yourself
stay as they are.

## 0.1.1.034 (2026-10-22)

Priority per camera. In the camera settings each camera can be set to Low, Mid or High. When events pile up, cameras with a
higher priority are analyzed first.

The CUDA worker is no longer blocked when the first query of the card size fails (GitHub #33). The failure is logged as an error
with its reason, and the size is taken from the next measurement. If the card cannot be measured at all, the worker starts with
one thread and the status is red.

Events without a clip at Frigate are closed as skipped. Alarms are no longer sent for events that started more than 15 minutes
ago.

One log line per page request with route, duration and the slow steps; `/health` shows the requests in progress.

Remote support: clearing the clip cache and a thread list through the support API.

## 0.1.1.033 (2026-10-21)

This release bundles 0.1.1.032, which was built but never pushed.

Newest events first. When events pile up, the analysis now takes the most recently queued event first instead of the
oldest (last in, first out). The clip prefetch follows the same order. An unknown person is still reported only once per
walk-through, even if an earlier event of the same walk-through is analyzed later. MQTT messages on `erkennung` and
`person_erkennung` now carry the start time of the event in a new field `start`; all existing fields stay the same.

Clips come over `clip.mp4` again, VOD is off by default. On Frigate 0.17.1 to 0.18 the VOD path rebuilds its mapping on
every request for events that ended less than an hour ago, which slows down both the clip fetch and Frigate's API
(frigate#24029). After this update the service switches `clip_vod` off once, says so in the log and writes it to the
audit log. If you switch VOD on again in Settings, it stays on, and ffmpeg then gets the time from
`clip_erzeugung_deckel_s` instead of 30 seconds.

Calibration only in Expert mode. The "Calibration" button in the top bar now shows only in Expert mode; Easy mode hides
it. The page stays reachable by its address and, in both modes, through the "Calibrate" button of each camera on the
Live page.

Thread count on a fresh installation. On the very first start of a new installation, suslik put the number of CPU
threads into its environment as if you had chosen one, even on machines strong enough to handle it automatically. On
the cpu image with more than one compute thread, every thread then used all cores at the same time. The first start now
sets a thread count only on a weak machine, as intended; everywhere else it stays automatic (cores shared between the
compute threads). The warning about overbooked cores no longer calls a preset number "your setting". Only the first
start of an installation was affected, until the container restarted.

## 0.1.1.031 (2026-10-20)

Faster pages with a long event history. `/heute`, `/anwesenheit` and `/system` no longer read the whole event file
`state/deckung.jsonl` on every request. A small index follows the file and reads only the lines a page needs; the first
request after a start still reads the file once. On a copy of a 395 MB event file, `/heute` took 0.28 s instead of 8 to
13 s, `/anwesenheit` and `/system` a few milliseconds instead of about 3 s.

Unknown groups show the time of their event. The worker now saves each unknown face with the start time of its event.
A group without a time shows "time unknown" instead of a made-up date and sorts last; groups saved before this release
keep "time unknown" until new events join them.

Clips come over Frigate's VOD path again. Saving the settings page could switch VOD off without notice; after this update
the service switches `clip_vod` on once and writes this to the audit log. If you switch it off afterwards, it stays off.
If VOD fails and the service falls back to `clip.mp4`, the log shows an ERROR with the reason (once per process and
reason), and `/health` counts each fallback.

The log says when the clip stock cannot keep up. When analysis slots fetch their clips from Frigate themselves while
events are waiting, a WARNING marks the start of such a phase and an INFO its end; `/health` counts these phases.

Same build path on every backend. On Intel, gpu-legacy, ROCm and CPU each compute thread now creates its buffers and
warms up under the same build lock as on CUDA, so threads no longer allocate memory at the same moment. The log shows
this step as a build ("building warm-up … started"), and a failure there is logged as a failed build.

The GPU page on CUDA judges from the worker's own plan instead of a formula for a reference card. It says when the
worker waits for card memory, runs in minimum mode, has switched live watchers off or could not start, and a measured
0 MB free is shown as measured.
