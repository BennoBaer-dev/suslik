# Hardware acceleration

suslik does face detection and recognition with ONNX Runtime. The backend is selected at runtime;
each [image variant](architecture.md#image-variant-architecture-one-code-several-hardware-images)
ships the runtime for one accelerator family plus a CPU fallback.

## Choosing a backend

Set it in the setup wizard, or via `VERIFY_BACKEND` (or `backend:` in the stored config):

| Value | Runs on | Image variant |
|---|---|---|
| `cpu` | CPU only | any (always available) |
| `openvino:GPU` | Intel iGPU | `-gpu` |
| `openvino:NPU` | Intel NPU | `-gpu` |
| `openvino:MIXED` | Intel iGPU + NPU | `-gpu` |
| `cuda` / `cuda:0` | NVIDIA GPU | `-cuda` |

The service validates the backend against the providers actually available and, if the requested
accelerator can't bind, falls back to CPU **with a loud warning** (never silently). The startup
self-check reports `… — device engaged` on success or `running on CPU` otherwise, and benchmarks
each usable backend on synthetic input so you can see it's really working.

## Rough performance (illustrative)

Single-inference latency on the author's hardware — treat as ballpark, not a promise:

| Backend | ~ ms / inference |
|---|---|
| CPU (a modern laptop CPU) | ~800 |
| Intel iGPU (OpenVINO) | ~26 |
| Intel NPU (OpenVINO) | ~18 |
| NVIDIA RTX 2060 (CUDA) | ~13–15 |

Any accelerator is roughly an order of magnitude faster than CPU. The CPU fallback is fine for
trying suslik out or for low camera counts, but a GPU/NPU is recommended for real use.

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
