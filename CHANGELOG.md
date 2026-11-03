# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.050 (2026-11-03)

Camera calibration: the calibration page of a camera opens again. Since 0.1.1.045 it failed with a connection error on every installation. A detection value outside the slider's usual range is now shown and saved as it is, instead of being clamped.

Live watcher: for a camera whose watcher replaces the event analysis, the clip is no longer downloaded just to be skipped. The Events list and the event page now say 'Handled by live watcher' instead of 'Skipped at startup', and on the watcher's own events they also show the name it recognised.

Frigate: if writing a name to a Frigate event fails with a temporary error (timeout, no connection, server error), it is now tried again instead of being lost.

Faces: the Faces, Known and Suggestions pages no longer copy the whole reference catalog on every call, which took several seconds on large installations.

CUDA: if the worker can't find its own process in the `nvidia-smi` list, as seen on some drivers without `pid: host`, it no longer stops after its first build and reports a full card. It keeps working and warns in the log, and the GPU page no longer says the worker isn't started. A refused build is no longer logged as a failed allocation.

Log: the fallback of the name assignment is now logged as INFO instead of WARNING.

## 0.1.1.049 (2026-11-02)

Live watcher: saving new face candidates in the event analysis no longer stops the watcher. It re-reads its references only when a reference actually changes, and a catalog line arriving during a read is no longer treated as an error.

## 0.1.1.048 (2026-10-31)

What's new box: an entry for the new per-watcher switch.

Live watcher: when a watcher replaces the event analysis for its camera, the Frigate events it creates itself are no longer analysed a second time; a new per-watcher option 'Also re-check this watcher's own Frigate events in the event analysis' (off by default) brings the old behaviour back.

Fault alerts: the 'inactive' alert (no event analysis for more than four hours during the day) is no longer sent while the MQTT reconciliation has just confirmed that nothing is missing and the queue is empty, as after a quiet night.

## 0.1.1.047 (2026-10-30)

What's new box: an entry for the live watcher change from 0.1.1.045.

Live watcher: MQTT messages and Frigate events now also go out for a watcher that is switched on, or gets one of these channels, while the live engine is already running; before, they only went out if such a watcher was already on when the engine started.

## 0.1.1.045 (2026-10-30)

Live watcher: the watcher now recognises faces with the same computation as the event analysis (the same models, quality, head-pose and feature-norm checks and the same vote stack) at full camera resolution, on every hardware variant.
