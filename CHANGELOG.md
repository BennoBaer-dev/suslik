# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.056 (2026-11-07)

- The self-watch now checks that the service is alive instead of how long the health report takes, restarts only the web server when just that stops answering, and the health report is served from a regularly updated snapshot.

## 0.1.1.055 (2026-11-05)

- Fewer file accesses per event (no usage journal, folders created once per process); built for large installations on network storage.
- The Today and Presence pages are served from memory while nothing changed (switch render_cache, on by default).

## 0.1.1.054 (2026-11-05)

Small fixes.

## 0.1.1.053 (2026-11-05)

Small fixes.

## 0.1.1.052 (2026-11-04)

Large installations: reference sets are read from one copy file instead of one file per set, so start and the daily cleanup no longer open thousands of files.
