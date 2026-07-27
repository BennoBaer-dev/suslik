# Hardware acceleration

suslik does face detection and recognition with ONNX Runtime. The backend is selected at runtime;
each [image variant](architecture.md#image-variant-architecture-one-code-several-hardware-images)
ships the runtime for one accelerator family plus a CPU fallback.

## Choosing a backend

Set it in the setup wizard, or via `VERIFY_BACKEND` (or `backend:` in the stored config):

| Value | Runs on | Image variant |
|---|---|---|
| `auto` *(default in `-gpu` since 0.1.0.44)* | picks NPU/GPU/CPU once, sticks | `-gpu` |
| `cpu` | CPU only | any (always available) |
| `openvino:GPU` | Intel iGPU | `-gpu` |
| `openvino:NPU` | Intel NPU | `-gpu` |
| `openvino:MIXED` | Intel iGPU (detector) + NPU (recognition) | `-gpu` |
| `cuda` / `cuda:0` | NVIDIA GPU | `-cuda` |

**`auto` placement**: at first start a short real benchmark builds sessions on the NPU and
GPU, measures them, and picks `openvino:MIXED` (recognition on the NPU — on a Core Ultra
that cuts recognition CPU cost from ~24 ms to well under 1 ms per inference), `openvino:GPU`,
or `cpu`. The decision is stored in `state/placement.json` and reused until hardware,
runtime or version change; systems without an NPU simply end up on GPU, identical to the
previous default. Per-model fallback chain NPU → GPU → CPU with a loud `PLACEMENT-FALLBACK`
log marker if a device stops binding.

The service validates the backend against the providers actually available and, if the requested
accelerator can't bind, falls back to CPU **with a loud warning** (never silently). The startup
self-check reports real bind probes per device (`found & usable — device bound in real probe`),
`… — device engaged` for the chosen backend, the resolved placement, and benchmarks each usable
backend on synthetic input so you can see it's really working. `/health` reports
`backend` and `placement` too.

**Why analysis decode stays on CPU (measured).** GPU *video decode* was tried and rejected
on purpose: on fixed-point clips, VAAPI-decoded frames shifted recognition scores by up to
0.021 (tolerance 0.005) and flipped time-window judgments. A verify layer whose verdict
depends on the decode hardware would be worthless, so clip decode for **judgments** stays on
CPU (with a frame-count guard against silent truncation) — while all **display** transcodes
(browser copies, Telegram clips) do run on the media engine, where no judgment is made.

## Measured performance (author's machines, 2026-07-27)

The same defined workload — 11 real events (3 fixed points + 8 stranger events), full
analysis wall-clock in a fresh container, second run with warm compile caches — on three
physically different boxes running 0.1.0.44. Different machines, so treat it as a trend,
not a lab benchmark; judgments were identical (green acceptance) on all three:

| System | cold | warm | ≈ per event (warm) |
|---|---|---|---|
| Intel Core Ultra 9 285H, iGPU + NPU (`auto` → MIXED) | 115 s | 69 s | **~6 s** |
| NVIDIA RTX 2060 mobile (CUDA) | 43 s | 38 s | **~3.5 s** |
| CPU only (AMD Ryzen 9 4900H) | 276 s | 281 s | **~25 s** |

Display transcode (720p browser/Telegram copy of one clip): NVENC full-HW **1.0 s** warm
(the very first call after long GPU idle pays a one-time ~5 s wake-up from the P8 power
state — real deployments where Frigate shares the GPU never see it), Intel VAAPI 2.1 s,
CPU libx264 1.5 s.

**Recommendation:** run suslik on *any* GPU or NPU — integrated is first-class here
(see [supported-hardware.md](supported-hardware.md)). The CPU fallback works everywhere
and is fine for trying it out, but budget roughly half a CPU-minute per event; an iGPU/NPU
turns that into seconds at near-zero CPU cost.

## Intel (iGPU / NPU via OpenVINO)

The `-gpu` image bakes in current Intel compute-runtime + NPU drivers. The **host kernel**
(`i915`/`xe` for the iGPU, `intel_vpu` for the NPU) is what the container's user-space runtime
talks to, so the devices are passed in at runtime (`/dev/dri`, `/dev/accel/accel0`) — see
[installation.md](installation.md#intel-variant-igpu--npu-via-openvino).

If the self-check says `running on CPU` on Intel hardware, the host driver and the image's
runtime versions don't line up for your kernel — that's the usual cause.

## NVIDIA (CUDA)

The `-cuda` image bakes in the **CUDA 12.8** runtime (plus cuDNN); the **kernel driver stays on
the host** and is injected by the NVIDIA Container Toolkit. This split is deliberate and gives
broad compatibility:

- **Driver range:** a CUDA 12.x build runs, via CUDA *minor-version compatibility*, on any Linux
  driver from **R525** upward (R525, R535, R550, R560, R570, R580, …). CUDA 13 would require R580+
  and lock out older drivers — which is why suslik targets 12.8.
- **GPU range:** CUDA 12.8 covers compute capabilities from **Maxwell (5.0)** through
  **Blackwell / RTX 50 series** — the widest still-relevant span. (CUDA 13 dropped
  Maxwell/Pascal/Volta.)
- **Requirement:** host driver **R525 or newer** and the NVIDIA Container Toolkit.

### Consumer-GPU note (important)

NVIDIA's stock CUDA images include a *forward-compatibility* (`cuda-compat`) layer. On
**consumer GeForce cards**, if your host driver is older than the image's CUDA version, that
layer triggers `CUDA failure 804: forward compatibility was attempted on non supported HW`, and
the container silently falls back to CPU — forward compatibility only works on data-center GPUs.
The suslik `-cuda` image **removes that layer at build time**, so it relies on ordinary
minor-version compatibility against your host driver instead. This is what lets the image run on
a GeForce card (e.g. an RTX 2060 on an R550 driver) without hitting 804 — validated on real
hardware.

If you build your own CUDA image from another base, remember to do the same
(`rm -rf /usr/local/cuda*/compat && ldconfig`), or you'll see error 804 on consumer GPUs.

## Verifying it's really on the GPU

Don't guess from latency alone. The startup self-check's backend step builds a real session on
the device and reports whether it bound; the benchmark step times it. On the host you can also
watch GPU utilization (`intel_gpu_top` for Intel, `nvidia-smi` for NVIDIA) during a benchmark run
to confirm the load actually lands on the accelerator.
