# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.054 (2026-11-05)

Small fixes.

## 0.1.1.053 (2026-11-05)

Small fixes.

## 0.1.1.052 (2026-11-04)

Large installations: reference sets are read from one copy file instead of one file per set, so start and the daily cleanup no longer open thousands of files.

## 0.1.1.051 (2026-11-04)

Start on large installations: the service no longer opens every reference set at startup. It reads the catalog and the folder lists and loads the set headers in the background; the analysis worker reads only the sets of its matrix. The worker's startup ping now has the deadline of a first analysis job instead of 180 s, so a worker still reading its references on slow storage is no longer killed. Seen at a field installation with 20,000 sets on NFS, where the start took over 30 minutes and the worker was restarted in a loop.

Diagnostics (debug mode): reads of the reference source log their open times, progress every 30 s and the NFS counters around them. The file probe lists every NFS request kind, measures opening the config file on its own and reports system load and the container's processes.

## 0.1.1.050 (2026-11-03)

Camera calibration: the calibration page of a camera opens again. Since 0.1.1.045 it failed with a connection error on every installation. A detection value outside the slider's usual range is now shown and saved as it is, instead of being clamped.

Live watcher: for a camera whose watcher replaces the event analysis, the clip is no longer downloaded just to be skipped. The Events list and the event page now say 'Handled by live watcher' instead of 'Skipped at startup', and on the watcher's own events they also show the name it recognised.

Frigate: if writing a name to a Frigate event fails with a temporary error (timeout, no connection, server error), it is now tried again instead of being lost.

Faces: the Faces, Known and Suggestions pages no longer copy the whole reference catalog on every call, which took several seconds on large installations.

CUDA: if the worker can't find its own process in the `nvidia-smi` list, as seen on some drivers without `pid: host`, it no longer stops after its first build and reports a full card. It keeps working and warns in the log, and the GPU page no longer says the worker isn't started. A refused build is no longer logged as a failed allocation.

Log: the fallback of the name assignment is now logged as INFO instead of WARNING.
