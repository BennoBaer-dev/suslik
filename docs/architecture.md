# Architecture

## The verify layer

suslik is a second-opinion layer on top of Frigate. The pipeline for each detection:

1. **Trigger on person events.** suslik listens for Frigate **person** detections (via MQTT or
   polling), not for Frigate's own face-recognition result. Person detection is robust; face
   recognition is the part that struggles, so suslik doesn't depend on it to decide *when* to
   look.
2. **Pull the full-resolution clip.** It fetches the recorded clip for the event (the full
   record stream, not a small live crop) so it has the best possible pixels to work with.
3. **Find the best face itself.** Using a strong detector (SCRFD from the `buffalo_l` pack), it
   scans across the clip's frames and picks the best face per person — not the biggest frame, but
   the one that actually matches well.
4. **Recognize with a strong model.** The chosen face is aligned and embedded with an **AdaFace**
   model, then compared (nearest-neighbor cosine similarity) against your reference library.
   Detection/alignment stays on `buffalo_l`; only the recognition head is AdaFace.
5. **Aggregate over time.** A person counts as recognized only when **enough frames within a
   short sliding window agree** on the same identity. A single lucky frame is rejected. This is
   the key to separating a real person (many consistent hits) from noise or a stranger (near
   zero).
6. **Group into scenarios.** Events that belong to the same walk (adjacent in time, across
   cameras) are grouped into one **scenario**, and the verdict is formed over the whole walk —
   the best face across *all* cameras of that pass, never a single event in isolation.
7. **Judge and (optionally) act.** The result is a judgment — recognized / unknown / disagreement
   with Frigate — which can raise an alert (Pushover / Telegram / MQTT) and, if you opt in,
   correct Frigate's `sub_label`.

### Why it beats a per-frame guess

The advantage is not a magic model — both suslik and Frigate use ArcFace-family embeddings. The
levers are:

- **Offline luxury.** suslik may re-examine one finished event with full CPU/GPU budget and pick
  the objectively best face; Frigate must decide live across every camera at once.
- **Calibrated uncertainty + time consistency.** Instead of a single high-confidence threshold
  that overshoots on ambiguous crops, suslik requires agreement over a time window and keeps an
  honest "unknown" band.
- **Reference hygiene.** Matching against a cleaned, calibrated reference set.

"Better" here means *more honest*, not more trigger-happy: on good footage both agree; on bad
footage suslik declines instead of mislabeling.

## Image-variant architecture (one code, several hardware images)

suslik ships **one codebase** in **three hardware images** — the same application code is baked
into each; only the inference runtime and drivers differ:

| Variant | Runtime | Accelerator |
|---|---|---|
| `-cpu` | `onnxruntime` | none |
| `-gpu` | `onnxruntime-openvino` + Intel drivers | Intel iGPU / NPU |
| `-cuda` | `onnxruntime-gpu` + CUDA runtime | NVIDIA GPU |

The backend is chosen **at runtime** (via `VERIFY_BACKEND` / the setup wizard). The code is
backend-agnostic; the same `.py` files run in every image.

**Why not one universal image?** The Intel runtime (`onnxruntime-openvino`) and the NVIDIA
runtime (`onnxruntime-gpu`) **cannot coexist** in one Python environment — both provide the
`onnxruntime` module and overwrite each other's binary; whichever is installed last wins and the
other's provider silently disappears. There is no official wheel that contains both. So the
industry-standard approach (the one Frigate also uses with `stable` vs `stable-tensorrt` vs
`stable-rocm`) is **one image per accelerator family**.

Because the CPU provider is compiled into every ONNX Runtime build, every variant can still fall
back to CPU if its accelerator isn't available — and the startup self-check says so honestly
(`device engaged` vs `running on CPU`). The fallback is a safety net, not the intended mode:
match the image to your hardware.

See [hardware-acceleration.md](hardware-acceleration.md) for the accelerator specifics.

## What's baked in vs. what's in your volume

- **Baked into the image (reproducible, versioned):** the OS/runtime, the accelerator user-space
  libraries, the Python dependencies, and the models (detector + recognition). No runtime
  downloads.
- **In your `/data` volume (never in the image):** your reference faces, configuration, learned
  data, and cached clips.

This split keeps images reproducible and your data portable across updates.
