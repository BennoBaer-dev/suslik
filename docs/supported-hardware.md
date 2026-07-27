# Supported hardware

The short version: **suslik runs on anything x86-64, and integrated GPUs are first-class.**
Many self-hosted vision tools only accelerate on discrete GPUs — here the Intel iGPU (and
the NPU on Core Ultra chips) is a primary, fully supported path, picked automatically.

This matrix is about **suslik's own face pipeline**. Frigate's object-detection hardware
(Coral, OpenVINO detectors, TensorRT …) is a separate story and unaffected by suslik.

| Hardware | Analysis (judgments) | Display transcode | Status |
|---|---|---|---|
| **Intel iGPU** (OpenVINO) | ✅ first-class (`auto` placement) | ✅ VAAPI | verified: Core Ultra 9 285H (author) |
| **Intel NPU** (Core Ultra) | ✅ recognition via `auto` → `MIXED` | — | verified: Core Ultra 9 285H (author) |
| **Intel Arc dGPU** | ✅ (OpenVINO, same path as iGPU) | ✅ VAAPI | tester-confirmed: Arc A380 |
| **NVIDIA GPU** (CUDA ≥ Maxwell, driver ≥ R525) | ✅ (`-cuda` image) | ✅ NVENC full-HW | verified: RTX 2060 mobile (author), RTX 3060 (tester) |
| **CPU x86-64** | ✅ universal fallback (~25 s/event measured on a Ryzen 9 4900H) | ✅ libx264 | verified (it's our own reference box) |
| **AMD GPU / ROCm** | ❌ analysis falls back to CPU | ❌ CPU encode (mesa/VAAPI probing is a planned investigation) | our own CPU reference box is an AMD APU — the Radeon iGPU is simply unused |
| **ARM / Apple Silicon** | ❌ images are x86-64 only for now | — | untested |
| **Coral / EdgeTPU** | ❌ investigated & closed (model ~9× larger than the Coral cache; ecosystem archived) | — | see [known-issues.md](known-issues.md) |
| **Hailo-8** | possible future investigation | — | not started |

**AMD owners:** we would genuinely like to support AMD GPUs — what's missing is not the
will but the test hardware. If you run an AMD GPU and are willing to test, open an issue
on GitHub and we'll build it together.

Details, driver notes and the measured performance comparison:
[hardware-acceleration.md](hardware-acceleration.md). Older Intel iGPU generations should
work wherever the OpenVINO driver stack supports them — field reports welcome.
