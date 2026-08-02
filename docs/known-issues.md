# Known issues & limitations

An honest list of what we know is rough, wrong or missing right now. If you hit
something that is not on this list, please open an issue — that is exactly the kind
of feedback this project needs.

_Last updated: 2026-07-30 (0.1.0.102-alpha)._

## Known bugs

- **Installations older than 0.1.0.92 never see an update hint for alpha releases.**
  Their version comparison cannot parse a tag like `v0.1.0.108-alpha` (the suffix
  handling was only added on 2026-07-30), so the check silently decides "nothing
  newer". Measured on a real 0.1.0.63 container: it fetches the release fine and
  stores `v0.1.0.108-alpha`, then compares it as *not* newer. Nothing is broken on
  your side — but if you are on such a version, you have to check for updates
  yourself. Every version from 0.1.0.92 on gets the hint correctly.

- **Deleting in Frigate is intentionally out of scope.** suslik never deletes anything
  in Frigate — removals stay local (a tombstone prevents re-import on the next sync).
  Since 0.1.0.45 it does not even try (the old non-portable SSH attempt is gone).
- ~~**Writing references back to Frigate is not portable yet.**~~ **Fixed in
  0.1.0.107-alpha.** The export direction used to copy files over SSH, which only
  worked where suslik happens to have root SSH access to the Frigate host. It now
  uploads through the official Frigate HTTP API (`POST /api/faces/{name}`), like
  every other Frigate call. Both directions work on a normal installation.
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
- **Scenarios (one walkthrough across several cameras) are displayed but not yet
  used for decisions.** Cross-camera grouping into zones — and judging a person by
  the best face across the whole walkthrough — is the next big construction site.
- **Merge suggestions are capped at 20**, ordered by similarity, so the page stays
  usable. Answering them (Merge / Different) makes room for the next ones.
- **Configuration backup does not cover everything yet**; treat it as a convenience,
  not a full disaster-recovery story. The `/data` volume is the source of truth —
  back that up.
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
- **Building from source needs the model files** — the source is published as of
  0.1.0.102-alpha, but the bundled ONNX models (~600 MB, third-party terms — see NOTICE)
  are not in the git tree. A checksummed fetch script is planned; until then the
  prebuilt images are the way to *run* suslik, and the source is there to read,
  audit and patch.

## Next up (rough order)

1. Zones / scenario-driven decisions (group cameras, judge the whole walkthrough).
2. Frigate write-back via the official HTTP API.
3. Harder failure handling for the compute backend.
4. Configurable detection resolution.
5. A second recognition path for faces the primary model cannot place.
