# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.048 (2026-10-31)

What's new box: an entry for the new per-watcher switch.

Live watcher: when a watcher replaces the event analysis for its camera, the Frigate events it creates itself are no longer analysed a second time; a new per-watcher option 'Also re-check this watcher's own Frigate events in the event analysis' (off by default) brings the old behaviour back.

Fault alerts: the 'inactive' alert (no event analysis for more than four hours during the day) is no longer sent while the MQTT reconciliation has just confirmed that nothing is missing and the queue is empty, as after a quiet night.

## 0.1.1.047 (2026-10-30)

What's new box: an entry for the live watcher change from 0.1.1.045.

Live watcher: MQTT messages and Frigate events now also go out for a watcher that is switched on, or gets one of these channels, while the live engine is already running; before, they only went out if such a watcher was already on when the engine started.

## 0.1.1.045 (2026-10-30)

Live watcher: the watcher now recognises faces with the same computation as the event analysis (the same models, quality, head-pose and feature-norm checks and the same vote stack) at full camera resolution, on every hardware variant.

## 0.1.1.043 (2026-10-28)

Today page: the side column now shows how many of the day's events had at least one face, instead of the 'not matched inside passes' count.

Housekeeping: face candidates nobody picked and unknown groups not seen for seven days are now cleared out automatically, together with old internal logs. Everything removed waits one week in a trash folder before it is deleted.

CUDA: the first card size query at startup now waits up to 30 seconds instead of 2. On machines where the graphics card answers slowly right after startup, the start then no longer logs two misleading errors about the card.

## 0.1.1.041 (2026-10-27)

Learning run: the feature-norm step now always gets a full hour, so large runs no longer stop the worker halfway through. Its success messages are no longer logged as errors; real problems get their own warning.
