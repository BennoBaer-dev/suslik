# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.101 (2026-11-11)

Test release. 0.1.1.058 was never published; its changes are part of this version.

- Today: the page now shows only cards, in three bands (Recognized, Probably recognized, Unknown), each card with its action. The list of passes and the numbers of the day moved to the new tab Passes. Card pictures are sent scaled down.
- Unknown people seen by a live watcher on Today: an appearance that a live watcher judges as an unknown person gets a card in the Unknown band, whatever channel the watcher reports on. The card opens the live alert. It has no identity and cannot be named there.
- Live watchers page: one page with slots replaces the tile overview and the separate settings page. A camera is assigned to a slot; below the slot bar are the settings of the selected slot: Push messages (a table with all nine push switches), Home Assistant (MQTT), Visit, Frigate (optional), and the folded sections Advanced and Diagnostics. "End after no face" is now "Visit ends after" and "Re-armed after" is now "Push pause"; the saved values are unchanged. The counter in the head reads "reported" instead of "alerts".
- Second look: a face that resembles nobody known must be found a second time by the detector before it counts as an unknown person. This keeps leaves, bushes and similar things out of the alerts and the unknown pool. Checked on Intel GPU and CPU, untested on AMD.
- The calibration samples of a live watcher keep all filter values.
- New setting `vorlauf_timeout_s` (factory value 60 s, 10 to 300 s): how long the service waits for the connection when it fetches a clip.
- Live watcher MQTT: every message has the field event, faces_recognized and appearance_ended are new. MQTT no longer waits for image, video or push, and "Push pause" no longer holds it back. Old fields are unchanged. Details in Read me first.
- Live watcher on Pushover and Telegram: the first face is no longer reported there. Known people come right away with name and a small picture, unknown people once the appearance is over, and Telegram gets one video per reported appearance. Each message type has its own switch per watcher, and "Push pause" now starts at the first face of a reported appearance.
- NVIDIA under Windows with Docker Desktop (WSL 2): the cuda image now detects the card without the device nodes /dev/nvidia*, so recognition, decoding and display videos run on the GPU there. Not yet verified on our own hardware. Thanks for the report in #37.
- Live alerts: the video of an appearance now also plays in Safari.

## 0.1.1.057 (2026-11-08)

- Margin rule for names: a face votes for a person only if its best match leads the second best by at least `stapel_abstand` (default 0.075, adjustable in Advanced Settings); closer faces give no vote and no preliminary name, in the analysis worker and the live watcher.

## 0.1.1.056 (2026-11-07)

- The self-watch now checks that the service is alive instead of how long the health report takes, restarts only the web server when just that stops answering, and the health report is served from a regularly updated snapshot.

## 0.1.1.055 (2026-11-05)

- Fewer file accesses per event (no usage journal, folders created once per process); built for large installations on network storage.
- The Today and Presence pages are served from memory while nothing changed (switch render_cache, on by default).

## 0.1.1.054 (2026-11-05)

Small fixes.
