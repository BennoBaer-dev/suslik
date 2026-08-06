# Known issues & limitations

An honest list of what we know is rough, wrong or missing right now. If you hit
something that is not on this list, please open an issue — that is exactly the kind
of feedback this project needs.

_Last updated: 2026-08-06 (0.1.0.138)._

## Known bugs

- ~~**Installations older than 0.1.0.92 never see an update hint for alpha
  releases.**~~ **Resolved by policy since 0.1.0.109:** releases carry no
  version suffix anymore, and every old installation can parse the plain tags
  (measured on a real 0.1.0.63 container against `v0.1.0.109`). Kept here for
  the record.

- **Deleting in Frigate is intentionally out of scope.** suslik never deletes anything
  in Frigate — removals stay local (a tombstone prevents re-import on the next sync).
  Since 0.1.0.45 it does not even try (the old non-portable SSH attempt is gone).
  Since 0.1.0.137 the opposite direction has an explicit place instead of being silent:
  a reference you deleted **in Frigate** is never re-sent on its own. It shows up on the
  **Frigate sync** page as your decision, *offer again* or *respect the deletion*, and
  nothing goes out until you choose. "Respect the deletion" keeps the picture in your own
  library and only stops it from going to Frigate, including in the automatic sync; it
  deletes nothing on either side.
- ~~**Writing references back to Frigate is not portable yet.**~~ **Fixed in
  0.1.0.107-alpha, endpoints corrected in 0.1.0.128.** The export direction used to
  copy files over SSH, which only worked where suslik happens to have root SSH
  access to the Frigate host. It now uploads through the official Frigate HTTP API
  (`POST /api/faces/{name}/create` + `/register`), like every other Frigate call.
  Note: Frigate only accepts face uploads while its own face recognition is
  enabled (`face_recognition.enabled: true`); otherwise it answers
  "Face recognition is not enabled." and suslik reports exactly that.
- **Two GPU instances on one Intel iGPU could crash on startup** (exit 139) —
  **fixed as of 0.1.0.44**: all compute jobs of one instance now run through a single
  persistent worker process, which bundles the GPU contexts; the collision window was
  verified gone in dedicated context tests. Running *multiple suslik instances* against
  one iGPU is still not recommended.
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

- **Detection resolution follows the clip's aspect ratio since 0.1.0.44** (long edge
  1280, multiple-of-32 grid — bit-identical detections, about a quarter less GPU work
  on 16:9). Making the base size configurable is still on the list.
- **Person recognition (preview): the decision threshold is calibrated between
  your learned people only.** Real strangers are not part of that calibration yet
  (they would need their own harvested material); keep an eye on body-path alerts
  and disarm any time. Scenario-driven decisions themselves are live: the scene
  window gates stranger alerts, passes with no serious face get a quiet class,
  and body recognition attributes face-less passes.
- **Merge suggestions are capped at 20**, ordered by similarity, so the page stays
  usable. Answering them (Merge / Different) makes room for the next ones.
- **Backup comes in two sizes.** The configuration backup covers the settings; the
  **full backup** (System page, since 0.1.0.118) covers everything you taught the
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
- **Building from source needs the model files** — the source is published (since 0.1.0.92), but the bundled ONNX models (~600 MB, third-party terms — see NOTICE)
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
5. Configurable detection resolution.
