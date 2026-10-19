# Changelog

All notable, user-visible changes to suslik. Internal steps between releases are
never pushed to GHCR; they ship bundled with the next release (each release entry
says which steps it bundles). This file keeps the last five releases; the full record lives in the
[GitHub releases](https://github.com/BennoBaer-dev/suslik/releases) and the git history.

## 0.1.1.030 (2026-10-19)

This release bundles 0.1.1.029, which was built and tested but never pushed.

Faster start with a large reference store: the reference catalog is now read once per state. Pages opened while the
service starts wait for that one read instead of starting their own. With debug on, the log names who started the read
and who waited for it.

More detail in the debug log on where an event spends its time. With debug on, each event writes one line for the
time before the analysis (slot taken, name list, event folder) and one for the time after it (result line, unknown
stack, notifications), the worker writes one line per job (waiting, clip, first frame, decoding, models, answer), and
waits on the service lock and on the reference folder lock are logged. `/health` shows the longest log write per
channel. Recognition is unchanged.

## 0.1.1.028 (2026-10-19)

Shorter wait before each analysis. To find the known persons, the service no longer copies the whole reference
catalog for every event and no longer re-reads it after every new candidate set. It builds the name list once per
reference state and shares it; only a change that touches a reference makes it read again. On a large tester catalog
(13,685 sets) a lookup took 0.4 s alone and 9.5 s with six analysis slots at once; it now takes under 1 ms. With debug
on, the `zeit:` line in the log ends with a new column `vorlauf`: the time from taking a slot to the start of the
analysis.

## 0.1.1.027 (2026-10-18)

Less overhead per event. The worker re-reads the reference matrix only when a catalog change affects it,
not after every new candidate set. On CUDA, card measurements are counted once and the price file is
written only when a number changes, no longer on every planning step or `/health` call. Each job is
planned once instead of three times.

## 0.1.1.021 (2026-10-16)

New reference store. Every learned face now lives as one set under `refquelle/<ref_id>/` (original
image, 112 px crop, fingerprint, origin) with one catalog `refquelle/katalog.jsonl` that records the
person binding, status, quality verdicts and export marks per set. Everything that reads or writes
references (recognition, live watchers, enrollment, the unknown pool, learning runs, Review & sync to
Frigate, renaming, deleting a person, photo upload and Frigate import, the stock QS, backup and restore,
the support area) goes through this one module. The person folder `faces/` is no longer a source: on an
installation without an old stock the module builds it as a derived view, on an installation coming from
0.1.1.010 it stays exactly as it was (see "Going back to 0.1.1.010" below).

One-time migration at the first start of this version, as its own step before the worker starts. If the
old stock is present, the service runs the migration script as a separate process and waits for it
(setting `migration_timeout_s`, factory value 600 s; when the deadline passes, the process is ended, the
migration stays pending and the next start resumes it). The script first counts the old stock (numbers
in the log), records the target state and copies every old store into
`state/archiv/vor_refquelle_<date>/kopie/` byte for byte before anything new is written, writes the sets
(resumable after a crash, no duplicate lines), rebuilds the matrices and compares them bit for bit
against the old values, and only then marks the migration done. The old files stay where they are;
nothing is moved and nothing is deleted. If the comparison fails, the service keeps recognising on the untouched
old stock, `/health` turns red and the next start tries again. Damaged lines of the old catalog are
counted and reported loudly (log, `/health`); they do not stop the migration. Measured as a script: 46 seconds on the
owner's installation (553 sets of 23 persons, Intel Core Ultra 9); 382 seconds on a copy of a larger tester
stock (2,967 sets of 37 persons) in a container with 4 CPU cores, plus 57 seconds for missing fingerprints.
At the first start, step 6 of the start check runs before the migration; it now reports "faces of the
previous version found — migrating them after this check, the count follows when it is done" as info
instead of warning about an empty face master.

Going back to 0.1.1.010. Set the image back to 0.1.1.010 and restart; there is nothing to do in the data
folder. 0.1.1.010 finds its faces as they were on the day of the update. Faces this version learned since
the update are missing there, and what 0.1.1.010 learns afterwards is not taken over by a later update.
Tested before the release with the same migration code on the owner's installation and on a copy of a
tester stock: the old files stayed byte for byte the same, and 0.1.1.010 started again with the same faces.
A backup before the update is still recommended: `/backup_voll` plus a copy of `clips/refcache.npz`, which
the full backup does not contain.

Missing fingerprints. A face whose old stock holds no fingerprint gets one
computed from its stored image, on the CPU, once, right after the migration and before the worker starts
(same process, same deadline). Everything the old stock already had is taken over as it is; nothing else
is recomputed. A set whose image shows no face or cannot be read is marked and left without a
fingerprint; it is not retried. `/health` shows the compute step (open, computed, without face, errors)
and turns red if the step failed. The computed value carries the checksum of the model's source file, so
CUDA installations accept it as well.

Start and saving. The worker reads the references once at start, not at the first event, and re-reads
only when the store changes. When the worker saves a recognised face, it stores the numbers of the
recognition itself; the second computation at the end of the event is gone. The background trial
recalculation of 0.1.1.012 (`state/refquelle_nachrechnung.json`) is removed.

Start order. At every start the worker now builds its video geometries before anything else. To read the
references at start it only needs the model identity (model name and the checksum of the model's source
file), which it takes from the registry without building anything on the accelerator; the full engine
identity is fetched only when a set is saved after the first event. A start that still builds the image
path first stops the worker loudly, like a compilation mismatch (`/health` red, no verdicts), and the
short start proof does not run before the process has built a geometry; it runs again at the next occasion. Reason: on Intel iGPUs the compiled pose
model depends on what was compiled before it; reading the engine identity at start built the recognition
model first, which shifted the pose model and sieved every face on a fresh installation.

Unknown faces. The worker now groups the unknown faces of a clip by similarity (two faces in the same
frame are never one group) and keeps the best images per group (settings `unbekannt_latte`,
`unbekannt_bilder_je_gruppe`, `unbekannt_rahmen_max`; `unbekannt_rahmen_max` 0 switches this off). A
consumer in the service takes each group after the event and compares it with the unknown identities you
already have: if it matches one (setting `unbekannt_latte`), the faces are added there, otherwise a new
unknown identity is created. The alert for an unknown person (MQTT `szene_unbekannt` with the identity,
Telegram with the best image; switched by the alert category `fremd_verdacht`) now goes out once per pass
over the property and identity, after the scene grace `szene_karenz_s`. It is also sent when a known
person was recognised in the same pass; their names are listed in the alert as information. No alert for
re-analyses, for events older than 15 minutes, for visitors and objects. `/health` shows the consumer
under `unbekannt`.

Probably recognized. An unknown identity whose faces clearly point to one known person gets the mark
"probably <name>": at least two faces, most of them closest to that person, a median similarity to that
person of at least 0.30 and a median lead of at least 0.10 over the next person (settings
`aehnlich_latte`, `aehnlich_abstand`, `aehnlich_min_gesichter`). Visitors and objects are left out. On the
Unknown page these identities are collected per person under "Probably recognized"; there you can assign
a selection to the person or say that it is not them. Such an identity sends no unknown alert. `/health`
shows the classification under `aehnlich`.

What's new box. The entry of this version links to the new chapter "New in this version" on the "Read me
first" page, which also explains going back to 0.1.1.010.

`/backup_voll` and the restore carry the new store; the support area `faces` delivers the store and the
catalog. The older flat data layout from before July 2026 is no longer renamed at service start; the
migration adopts it. The duplicate check of the enrollment takeover asks the module instead of the
folder, so earlier takeovers still count after the migration.

Internal: a new coverage rule in the release checks (rule D: path words of the reference stores only
inside the module) and an invariant that binds it to the project rules; the migration script returns 4
when the migration is green but the compute step red.

## 0.1.1.010 (2026-10-04)

New face recognition. A name is now confirmed by votes: every face that passes all filters
and matches a known person with a score of at least 0.40 counts as one vote, and three
votes confirm the name (setting `stapel_stimmen`). When a face reaches 0.375 for a person
who is not confirmed yet, a door opens and the next 20 frames (setting `tuer_fenster`) are
checked one by one instead of every x-th frame; another hit inside the window keeps the
door open. The number of persons now comes from Frigate (overlapping person events on the
same camera), and the analysis of an event ends early once that many different persons are
confirmed and the door is shut. If the count cannot be read, the event is analysed to the
end of the clip and the log shows a WARNING; if more different persons are recognised than
Frigate reported, the verdict keeps the ones with the most votes (also a WARNING). Two
face-quality checks and a minimum recognition norm (factory value 18.5; a stored 0, the old
factory value, is raised once at startup) now filter faces before recognition, and the
enrollment and unknown-person pools only receive faces that passed every filter. The check
for silently damaged clips only counts messages from reading and decoding the video, summed
over all decoder runs of an event.

Fixes a silent recognition degradation after worker restarts (pose compiled-model drift):
the compiled-model probe now runs on all five hardware variants (one shared mechanism; no
engine is unguarded anymore), a deviation in a stage that filters the face cascade is fatal
(one fresh retry, then a loud stop visible in /health) instead of a hint, model builds at
worker start are serialized so the image path and the start proof never race the first
geometry build (the root cause), the failure-series shot no longer endlessly replaces a
worker that stopped itself over a compiled-model deviation, and the calibration mark is
only ever written by the first start of an installation. Measured bit-stable across four
worker starts on cpu and cuda.

Also in this release: the internal steps 0.1.0.546 to 0.1.1.008, never published on their own.

### 0.1.1.008

An empty clip download can no longer freeze an event analysis: a transiently empty Frigate
response is not written to the clip cache anymore, the error message names the cause (file
size, ffprobe outcome), and the retry fetches a fresh copy instead of hitting the frozen
cache entry. Bundles the internal release-pipeline rework: stage 5 now judges per hardware
variant (red / decision-pending / green / untested) with partial publishing, instead of
blocking the whole run on a single finding.

### 0.1.1.007

Damaged spots in a camera stream no longer cut an analysis short on Intel hardware decoding:
if the hardware decoder dies mid-clip (seen in the field on power-line camera links), the event
is re-analyzed once, completely, over the software decoder — one ERROR line in the log names the
failure and the full outcome. The over-engineered restart-behind-the-spot mechanism that was
built first never shipped and is fully removed again (including its config key).

### 0.1.1.006

First build that went through the rebuilt release run (release model 3.0; 0.1.1.001 and
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

### 0.1.0.547

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

### 0.1.0.546

- **A busy installation now really gets the compute threads its card can carry.**
  The number of concurrent analyses follows the number of compute threads, but it was
  only ever switched while no analysis was running — and on an installation with
  around 10 000 events a day that moment never comes. A field tester's machine (12 GB
  card, five live watchers, `worker_straenge` set to 6) therefore ran the whole
  morning with a single thread and a single analysis slot while the card's budget had
  long grown to six, with the log repeating "applies at the next worker start with no
  analysis running". The quiet moment is now *made* instead of waited for: no new
  slots are handed out, the running job finishes undisturbed, then the slots are
  switched and the worker is restarted so the compute threads follow. Nothing running
  is ever cancelled, the drain is capped (after 120 seconds everything simply stays as
  it was and is retried later), and a restart only happens when a fresh worker would
  really build more threads than the running one.
- **A restart with live watchers no longer talks the card down to one thread.** At
  service start the free-memory band is read from the statistics ring, which reaches
  600 seconds back — into the time *before* the restart, when the watchers, the live
  engine and the old worker were still on the card. Their memory is already inside
  that band, and the same watchers were then put aside a second time because the new
  live engine was not up yet. On the field tester's 12 GB card the two together
  produced a negative budget and the message that the card does not carry a single
  compute thread. Whichever way the watchers are accounted for, they are now counted
  once: while their memory is being reserved, the card's momentary value is used
  instead of the stale band, and the calculation path says so. Once the live engine has
  been up for a minute, the band applies again exactly as before — it is the more
  careful number in normal operation.

Also in this step, instrumentation only: the analysis worker now records how long each
inference request stood on the accelerator and how many requests were submitted at
that moment, writing one summary line per event and one line per request above
1000 ms — with wall-clock time, so the lines can be laid next to the host's engine
reset timestamps. Nothing about recognition, its results or its speed changes; the
new numbers also appear additively under `worker.inferenz` in `/health`.
