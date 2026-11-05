# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.055 (2026-11-05)

- Fewer file accesses per event (no usage journal, folders created once per process); built for large installations on network storage.
- The Today and Presence pages are served from memory while nothing changed (switch render_cache, on by default).

## 0.1.1.054 (2026-11-05)

Small fixes.

## 0.1.1.053 (2026-11-05)

Small fixes.

## 0.1.1.052 (2026-11-04)

Large installations: reference sets are read from one copy file instead of one file per set, so start and the daily cleanup no longer open thousands of files.

## 0.1.1.051 (2026-11-04)

Start on large installations: the service no longer opens every reference set at startup. It reads the catalog and the folder lists and loads the set headers in the background; the analysis worker reads only the sets of its matrix. The worker's startup ping now has the deadline of a first analysis job instead of 180 s, so a worker still reading its references on slow storage is no longer killed. Seen at a field installation with 20,000 sets on NFS, where the start took over 30 minutes and the worker was restarted in a loop.

Diagnostics (debug mode): reads of the reference source log their open times, progress every 30 s and the NFS counters around them. The file probe lists every NFS request kind, measures opening the config file on its own and reports system load and the container's processes.
