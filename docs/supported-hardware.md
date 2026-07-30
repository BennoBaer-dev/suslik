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
| **Intel iGPU Gen8/9/11** (UHD 6xx, 6th–10th gen Core) | 🧪 `-gpu-legacy` image (testing): Intel serves these generations only via its legacy1 runtime, which this variant ships — the regular `-gpu` image cannot bind them | ✅ VAAPI | awaiting tester confirmation on a UHD 630 (issue #6) |
| **NVIDIA GPU** (CUDA ≥ Maxwell, driver ≥ R525) | ✅ (`-cuda` image) | ✅ NVENC full-HW | verified: RTX 2060 mobile (author), RTX 3060 (tester) |
| **CPU x86-64** | ✅ universal fallback (~25 s/event measured on a Ryzen 9 4900H) | ✅ libx264 | verified (it's our own reference box) |
| **AMD GPU / ROCm** | 🧪 experimental `-rocm` image (MIGraphX EP) in testing — falls back to CPU where ROCm doesn't bind | ❌ CPU encode (mesa/VAAPI probing is a planned investigation) | testers wanted — open an issue with your GPU model |
| **ARM / Apple Silicon** | ❌ images are x86-64 only for now | — | untested |
| **Coral / EdgeTPU** | ❌ tested & closed (a Coral-sized model fits the chip but loses real residents — the separation the method needs does not survive the shrink) | — | see [known-issues.md](known-issues.md) |
| **Hailo-8** | possible future investigation | — | not started |

**AMD owners:** we would genuinely like to support AMD GPUs — what's missing is not the
will but the test hardware. If you run an AMD GPU and are willing to test, open an issue
on GitHub and we'll build it together.

Details, driver notes and the measured performance comparison:
[hardware-acceleration.md](hardware-acceleration.md). Older Intel iGPU generations
(Gen8/9/11 — UHD 6xx graphics on 6th–10th gen Core) need the `-gpu-legacy` variant:
Intel's current compute runtime only covers Gen12 and later, the older generations are
served by separate legacy1 packages, and that is exactly what `-gpu-legacy` ships.
The regular `-gpu` image on such hardware falls back to CPU (loudly) and now shows a
banner pointing to the right variant. Field reports welcome.
