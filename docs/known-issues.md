# Known issues & limitations

An honest list of what we know is rough, wrong or missing right now. If you hit
something that is not on this list, please open an issue — that is exactly the kind
of feedback this project needs.

_Last updated: 2026-08-13 (0.1.0.199)._

## Known bugs

- **Deleting in Frigate is intentionally out of scope.** suslik never deletes anything
  in Frigate — removals stay local (a tombstone prevents re-import on the next sync).
  The opposite direction has an explicit place instead of being silent:
  a reference you deleted **in Frigate** is never re-sent on its own. It shows up on the
  **Frigate sync** page as your decision, *offer again* or *respect the deletion*, and
  nothing goes out until you choose. "Respect the deletion" keeps the picture in your own
  library and only stops it from going to Frigate, including in the automatic sync; it
  deletes nothing on either side.
- **Running multiple suslik instances against one Intel iGPU is not recommended** —
  one instance bundles its GPU contexts in a single worker process, but two instances
  can still collide on the same device.
- **AMD GPU support is experimental.** There is a dedicated `-rocm` image (analysis via
  ROCm/MIGraphX — pass `/dev/kfd` and `/dev/dri` into the container); it is in the testing
  phase and has not been confirmed on real AMD hardware yet, so it may fall back to CPU.
  The universal CPU image always works on AMD. Willing testers welcome, see
  [supported-hardware.md](supported-hardware.md).
- **A failed accelerator can fall back to CPU too quietly.** If the compute backend
  dies mid-run, analysis may continue on CPU without making the failure loud. Hard
  failure handling is planned.
- **Single false detections still enter the unknown pool.** The static-object
  quarantine catches *clusters* of non-faces (wheel arches, light patterns) reliably,
  but an individual misdetection can sit in the pool as a one-image identity until
  enough similar ones accumulate.

## Limitations (by design, for now)

- **Live watchers are capped at five, and heavy load thins the sampling.** An enabled
  watcher simply runs — there is no capacity estimate deciding whether it may start.
  The only hard stops are the cap of five and a RAM floor read from the container's
  own memory limit; overload is handled at runtime by sampling frames more thinly
  (visible as the throttle level on the engine card).
- **Source-test results recorded before 0.1.0.199 measured decode throughput, not the
  camera's real delivery rate.** Such results are marked "(throughput, not delivery
  rate — rerun the source test)"; run the test again to get the real number.
- **Detection resolution follows the clip's aspect ratio** (long edge
  1280, multiple-of-32 grid — bit-identical detections, about a quarter less GPU work
  on 16:9). Live watchers have a selectable per-camera processing resolution since
  0.1.0.199 (360p–2160p, default 1080p); making the clip-analysis base size
  configurable as well is still on the list.
- **Person recognition (preview): the decision threshold is only as good as its
  stranger material.** The calibration uses real stranger images
  from `personlern/fremd/` when at least five are present, and the model drops
  bodies it reads as strangers; with an empty folder it falls back to calibrating
  between your learned people only. Either way, keep an eye on body-path alerts
  and disarm any time — Model status states which of the two applies. Collecting
  that stranger material still has no UI; you fill the folder yourself.
  Scenario-driven decisions themselves are live: the scene window gates stranger
  alerts, passes with no serious face get a quiet class, and body recognition
  attributes face-less passes.
- **Merge suggestions are capped at 20**, ordered by similarity, so the page stays
  usable. Answering them (Merge / Different) makes room for the next ones.
- **Backup comes in two sizes.** The configuration backup covers the settings; the
  **full backup** (System page) covers everything you taught the
  installation — settings, face references, learning results, person-recognition
  material and models. It deliberately excludes the clip cache and per-event
  artifacts (they rebuild over time). The `/data` volume remains the source of truth.
- **Frigate only accepts reference uploads while its own face recognition is on.**
  With `face_recognition.enabled: false` in your Frigate config, Frigate answers every
  upload with HTTP 400 ("Face recognition is not enabled."). suslik shows that verbatim,
  and the **Frigate sync** page reads the live state from Frigate as it loads ("Frigate
  face recognition: on/off"). Importing *from* Frigate works either way; only the
  direction out is blocked.
- **A picture Frigate refuses does not stop the sync.** Every image is judged on its own.
  A `400` from Frigate's `register` is Frigate's verdict about *that picture* (usually:
  no face found in it) and is remembered, so the automatic sync stops re-offering it —
  you can still send it by hand. Frigate's generic `500 could not process request` can
  just as well be Frigate's own state, so suslik retries that one after a day. Transport
  errors are never blamed on the image, and if three identical errors follow each other
  suslik flags a possible wall and throws those markers away, so a Frigate outage cannot
  lock your queue out for good. What the pre-check says beforehand is only suslik's own
  detector guessing; Frigate's answer is the truth.
- **Frigate renames what it accepts, so sent references cannot be verified afterwards.**
  Frigate stores every accepted upload under its own name and processes it asynchronously.
  suslik keeps an export protocol, so it knows *that* a picture went out, but it can no
  longer point at Frigate's copy; the sync page says so instead of pretending. The same
  images therefore also appear in the import section as "only in Frigate", where they are
  indistinguishable from faces you added in Frigate yourself, and importing them would
  create a duplicate in your library. Import from that section deliberately, not in bulk.
- **Coral / EdgeTPU sticks are not supported — actually tested and closed (07/2026).**
  This was measured, not assumed: a Coral-sized recognition model (MobileFaceNet-class,
  ~3 MB INT8 — it *does* fit the EdgeTPU cache) was run through suslik's full
  frame-by-frame method against the fixed-point clips. The stranger gate held (0 false
  windows on all 8 stranger events), but a real resident fell below recognition — the
  separation band between "hard genuine hit" and "stranger" collapsed to ~0.02
  (the full model keeps ~0.18). No threshold fixes that; the small model simply does
  not carry the method. The detector also does not fit the chip, so the stick could
  only ever accelerate the smallest part of the pipeline. Credit where due: the
  community keeps the Coral ecosystem alive and installable on current Python — the
  blocker is the physics of the shrunken model, not the tooling. If a
  small-accelerator path comes, it will more likely be a Hailo-8 investigation.
  A Coral still helps Frigate's own object detection — just not suslik's face pipeline.
- **Building from source needs the model files** — the source is published, but the bundled ONNX models (~600 MB, third-party terms — see NOTICE)
  are not in the git tree. A checksummed fetch script is planned; until then the
  prebuilt images are the way to *run* suslik, and the source is there to read,
  audit and patch.

## Next up (rough order)

1. Per-area alert behavior (camera areas stage 2).
2. Stranger material for the person-path calibration, and moving its harvest
   inference (pose gate + embedding) to the GPU/NPU.
3. A "recurring, not a resident" review option, so naming the courier does not
   silently disable stranger alerts.
4. Harder failure handling for the compute backend.
5. Configurable base size for the clip-analysis detection resolution (the
   per-camera live-watcher resolution shipped in 0.1.0.199).
