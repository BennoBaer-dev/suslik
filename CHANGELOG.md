## 0.1.1.010 (2026-10-04)

Fixes a silent recognition degradation after worker restarts (pose compiled-model drift):
the compiled-model probe now runs on all five hardware variants (one shared mechanism; no
engine is unguarded anymore), a deviation in a stage that filters the face cascade is fatal
(one fresh retry, then a loud stop visible in /health) instead of a hint, model builds at
worker start are serialized so the image path and the start proof never race the first
geometry build (the root cause), the failure-series shot no longer endlessly replaces a
worker that stopped itself over a compiled-model deviation, and the calibration mark is
only ever written by the first start of an installation. Measured bit-stable across four
worker starts on cpu and cuda.

## 0.1.1.008

An empty clip download can no longer freeze an event analysis: a transiently empty Frigate
response is not written to the clip cache anymore, the error message names the cause (file
size, ffprobe outcome), and the retry fetches a fresh copy instead of hitting the frozen
cache entry. Bundles the internal release-pipeline rework: stage 5 now judges per hardware
variant (red / decision-pending / green / untested) with partial publishing, instead of
blocking the whole run on a single finding.

## 0.1.1.007

Damaged spots in a camera stream no longer cut an analysis short on Intel hardware decoding:
if the hardware decoder dies mid-clip (seen in the field on power-line camera links), the event
is re-analyzed once, completely, over the software decoder — one ERROR line in the log names the
failure and the full outcome. The over-engineered restart-behind-the-spot mechanism that was
built first never shipped and is fully removed again (including its config key).

# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). History older than 0.1.0.180 has been trimmed from
this file — the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git
history.

## 0.1.1.006

First release that went through the rebuilt release run (release model 3.0; 0.1.1.001 and
0.1.1.002 were test runs of that process and were never published; 0.1.1.005 was a
field-test build of this same content, shipped as a cuda-only test image and never
released). It bundles
0.1.0.547, 0.1.0.548 (the log rebuild) and the 0.1.0.549 test build (CUDA only, field test) and
adds the fixes below.

- **Rebuilt release process** (release model 3.0): every regular release now runs through an
  automated test on three machines (CUDA, Intel GPU, CPU) before it ships, with a check log that
  is read after the test.
- **Rebuilt log system:** one central log module, levels by cause (planned = INFO, unplanned =
  WARNING, unplanned with loss = ERROR), a check log the release run reads (`pruef_log`,
  `pruef_takt_s`) and a `log` block in `/health`.
- **Fixes from the field test and from GitHub issue #33 / discussion #30:** a worker that has
  died no longer keeps its share of the card memory booked; a standstill (no analysis for
  `stillstand_min` minutes, default 10) is reported as a disturbance and turns `/health ok` false;
  catch-up losses are counted (`/health nachhol`); refused analyses are counted
  (`worker.absagen_n`); the thread count only rises after a quiet period of `speicher_ruhe_min`
  minutes (default 10), and a drop below the configured count is an ERROR; live watchers are not
  switched off during the engine's first minute and come back after the quiet period; NVDEC
  decoder threads follow the 32-surface limit; `openvino:CPU` really computes on the CPU; a
  deliberately chosen `cpu` backend on a GPU image is no longer reported as a fallback; the person
  model reports when it silently fell back to the CPU.
- **Fixes from the 0.1.0.549 field test:** the MQTT connection line is INFO, not ERROR; while
  the card budget settles in the engine's first minute, one INFO line per start replaces an ERROR
  per tick; the first write to the live notification log no longer reports an error; the live
  watcher is no longer switched off in the engine's first minute because the worker's own share
  was left out of the start-up check.
- **GPU inference deadline (new setting `inferenz_frist_s`, default 10 seconds, range 2 to 120):**
  a compute request that does not return within the deadline is reported as an ERROR
  (`inference HANG`, also in the check log), the worker process is restarted and the event is
  queued again; `/health ok` stays false until a fresh worker runs. Before, a request dropped by the
  GPU driver left the worker waiting silently. The deadline applies to the OpenVINO engine; a change
  takes effect with the next worker start.

## 0.1.0.547 (unreleased)

- **An event that meets a restarting worker is put back calmly instead of spinning
  through the queue.** Since 0.1.0.545, an analysis that the worker turned away through
  no fault of the event (typically while it shuts down in an orderly way after the card
  ran out of memory) was meant to go back into the queue and be retried after 45
  seconds. A wrong argument in that step broke it: every such event ended with the log
  line "unexpected error in the processing thread: int() argument must be … not 'dict'",
  left the queue without any pause and was queued again by the next sweep. On a field
  tester's machine (12 GB card, five live watchers, `worker_straenge` set to 6) that
  meant almost 300 000 of these lines in less than nine hours, the queue going round at
  dozens of events per second while the worker restarted, and a growing backlog. The
  event now goes back into the queue as intended and is retried after 45 seconds, at
  most as often as `nachhol_versuche` allows (factory 3); after that it is booked as a
  failed analysis that records how often it was put back, and the catch-up run takes it
  on from there. A catch-up attempt that meets such a worker no longer counts against
  the event either.
