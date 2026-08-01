# Installation

suslik ships as a Docker image in **five hardware variants** that share the exact same
application code — only the baked-in inference runtime differs. Pick the one that matches your
hardware:

| Variant | Image tag suffix | Accelerator | Use it when |
|---|---|---|---|
| **CPU** | `-cpu` | none (CPU only) | no GPU, or just trying it out (universal fallback) |
| **Intel** | `-gpu` | Intel iGPU / NPU via OpenVINO | you have an Intel integrated GPU (and optionally NPU) |
| **Intel legacy** | `-gpu-legacy` | Intel Gen8/9/11 iGPU (UHD 6xx) via OpenVINO legacy runtime | you have a 6th–10th gen Intel iGPU — the regular `-gpu` image cannot bind it |
| **NVIDIA** | `-cuda` | NVIDIA GPU via CUDA | you have an NVIDIA GPU |
| **AMD** | `-rocm` | AMD GPU via ROCm / MIGraphX (testing) | you have an AMD GPU — pass `/dev/kfd` + `/dev/dri` into the container |

> Why separate images instead of one universal image? The Intel (`onnxruntime-openvino`) and
> NVIDIA (`onnxruntime-gpu`) runtimes cannot coexist in one Python environment — they overwrite
> each other. This is the same approach Frigate takes (`stable` vs `stable-tensorrt`). See
> [architecture.md](architecture.md).

Every variant still contains the CPU provider, so it will fall back to CPU (with an honest
warning in the startup log) if the accelerator isn't available. Match the image to your hardware
for real performance.

## Prerequisites

- **Docker** with the Compose plugin (`docker compose`).
- A reachable **Frigate** instance (suslik triggers on Frigate person events and pulls recorded
  clips). You configure the Frigate URL later in the setup wizard — nothing is hardcoded. The
  simplest setup is to run suslik **right alongside Frigate on the same host** — a second Docker
  container (or the same compose stack) — then it reaches Frigate's internal **port 5000** out of
  the box. suslik uses that unauthenticated port 5000; it has **no support for Frigate's
  authenticated port 8971** (JWT/login) yet.
- **For the Intel variant:** an Intel iGPU exposed at `/dev/dri` (and, if present, an NPU at
  `/dev/accel/accel0`) on the host.
- **For the NVIDIA variant:** an NVIDIA driver (**R525 or newer**) on the host plus the
  [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html),
  configured for Docker:
  ```bash
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
  ```

## Getting the image

You can either **pull a published image** or **build it yourself**.

### Option 1 — pull from GHCR (CPU, Intel, NVIDIA)

> ⚠️ **Mind the variant names:** `-gpu` means **Intel** (OpenVINO iGPU/dGPU), `-cuda` means
> **NVIDIA**, `-cpu` is the CPU-only fallback. NVIDIA users want **`-cuda`** — don't pull `-gpu`
> expecting NVIDIA.

All variants are published on the GitHub Container Registry.

> **Alpha note:** `latest-*` follows the newest published version (currently
> **0.1.0.102-alpha** — learning module, camera areas; see the README status), so a
> plain `docker compose pull` tracks the alpha. If you'd rather stay on a fixed,
> validated build, pin its version tag (the last broadly validated one is
> **0.1.0.63**):

```bash
# the current alpha (work in progress, recommended for testers):
docker pull ghcr.io/bennobaer-dev/suslik:0.1.0.102-alpha-gpu    # Intel (OpenVINO)
docker pull ghcr.io/bennobaer-dev/suslik:0.1.0.102-alpha-cuda   # NVIDIA
docker pull ghcr.io/bennobaer-dev/suslik:0.1.0.102-alpha-cpu    # CPU-only

# the last broadly validated build:
docker pull ghcr.io/bennobaer-dev/suslik:latest-cpu
docker pull ghcr.io/bennobaer-dev/suslik:latest-gpu     # Intel (OpenVINO)
# Older Intel iGPU (UHD 6xx, 6th–10th gen Core)? Use the gpu-legacy variant instead —
# testing phase: pull the version tag from the Packages page (no latest-gpu-legacy yet).
docker pull ghcr.io/bennobaer-dev/suslik:latest-cuda    # NVIDIA
```

> The **NVIDIA/CUDA** image is now on GHCR too (`latest-cuda`), so you can pull it like the
> others. Note it is a **large image** — it bundles the multi-GB CUDA runtime — so the pull takes
> noticeably longer than the CPU/Intel ones. If you'd rather not pull that much, building from
> source is an equivalent alternative (see Option 2).

### Option 2 — build from source

The application source is published in this repository as of **0.1.0.102-alpha** — you can
read, audit and patch everything the images run. One honest limitation for now: the bundled
ONNX **model files are not in the git tree** (~600 MB, and they carry their own third-party
terms — see [NOTICE](../NOTICE)), so a fresh `docker build` will stop at the model `COPY`
step until you drop the model packs into `models/` and `docker/buffalo_l/` yourself. A
checksummed fetch script is planned. Until then, **Option 1 (GHCR pull) is the way to run
suslik**; the build files (`docker/Dockerfile*`) document exactly how the published images
are made.

## Common settings (all variants)

- **Port:** the web UI and API listen on **`8199`** inside the container.
- **Data volume:** mount a host directory at **`/data`**. All state (your reference faces,
  config, learned data, cached clips) lives here — it is **never** baked into the image, so your
  data survives image updates. Back up this directory.
- **Timezone:** set **`TZ`** (e.g. `Europe/Berlin`). Without it the container runs in UTC and all
  timestamps in the UI/alerts are wrong.
- **First run:** with an empty `/data`, suslik starts in the **setup wizard** — open
  `http://<host>:8199/` and it walks you through connecting Frigate, choosing cameras/zones, and
  picking the backend. See [configuration.md](configuration.md).

---

## CPU variant

The simplest start — no device passthrough.

**docker run:**
```bash
docker run -d --name suslik \
  -p 8199:8199 \
  -e TZ=Europe/Berlin \
  -v /path/to/suslik-data:/data \
  ghcr.io/bennobaer-dev/suslik:latest-cpu
```

**docker compose** (`compose.yml`):
```yaml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-cpu   # or your locally built suslik:<version>-cpu
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    volumes:
      - ./suslik-data:/data
```
```bash
docker compose up -d
docker compose logs -f          # watch the startup self-check
```

---

## Intel variant (iGPU / NPU via OpenVINO)

Pass through the render device (`/dev/dri`) and, if you have an NPU, `/dev/accel/accel0`. The
container also needs to be in the host's `render`/`video` groups; the group IDs differ per host,
so read them from the host rather than hardcoding.

**docker run:**
```bash
docker run -d --name suslik \
  -p 8199:8199 \
  -e TZ=Europe/Berlin \
  -v /path/to/suslik-data:/data \
  --device /dev/dri:/dev/dri \
  --device /dev/accel/accel0:/dev/accel/accel0 \
  --group-add "$(getent group render | cut -d: -f3)" \
  --group-add "$(getent group video  | cut -d: -f3)" \
  ghcr.io/bennobaer-dev/suslik:latest-gpu
```
> No NPU? Drop the `/dev/accel/accel0` line — the iGPU alone works.

**docker compose** (`compose.yml`):
```yaml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-gpu   # Intel — or your locally built suslik:<version>-gpu
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    devices:
      - "/dev/dri:/dev/dri"                       # iGPU
      - "/dev/accel/accel0:/dev/accel/accel0"     # NPU (omit if you don't have one)
    group_add:
      # NUMERIC host GIDs of the render/video groups. Group NAMES ("render") do NOT work here —
      # Docker resolves group_add against the CONTAINER's /etc/group, which has no render group,
      # and the container fails to start. Find your host's GIDs with:  getent group render video
      - "992"                                     # your host's 'render' GID (varies per system!)
      - "44"                                      # your host's 'video' GID
    volumes:
      - ./suslik-data:/data
```

The startup self-check will report `openvino:GPU — device engaged` when the iGPU is working. If
it says `running on CPU` instead, the host driver/runtime versions don't match — see
[hardware-acceleration.md](hardware-acceleration.md).

---


## Older Intel iGPUs (UHD 6xx, 6th–10th gen Core): the `gpu-legacy` variant

Intel's current compute runtime only covers Gen12 and later — on a 6th–10th gen iGPU the
regular `-gpu` image falls back to CPU (loudly, and with a banner pointing here). The
`gpu-legacy` variant ships Intel's legacy1 runtime instead and is confirmed working on a
UHD 630. The compose file is the same as for the regular Intel variant, with two
differences: the image tag, and no NPU line (these platforms have no NPU).

```yaml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:0.1.0.63-gpu-legacy   # version tag — no latest-gpu-legacy during the testing phase
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    devices:
      - "/dev/dri:/dev/dri"                       # iGPU (no /dev/accel line: these platforms have no NPU)
    group_add:
      - "992"                                     # your host's 'render' GID (varies — getent group render video)
      - "44"                                      # your host's 'video' GID
    volumes:
      - /path/to/suslik-data:/data
```

Once the variant graduates from testing, a `latest-gpu-legacy` tag will exist and the
version pin can go; check the [Packages page](https://github.com/BennoBaer-dev/suslik/pkgs/container/suslik)
for the newest `-gpu-legacy` version tag until then.

## NVIDIA variant (CUDA)

Requires the NVIDIA Container Toolkit (see Prerequisites). GPU access is granted via the standard
Docker GPU mechanism.

**docker run:**
```bash
docker run -d --name suslik \
  --gpus all \
  -p 8199:8199 \
  -e TZ=Europe/Berlin \
  -v /path/to/suslik-data:/data \
  ghcr.io/bennobaer-dev/suslik:latest-cuda
```

**docker compose** (`compose.yml`):
```yaml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-cuda      # or build locally
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    # GPU passthrough (Compose-spec native, equivalent to `--gpus all`):
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all                          # or device_ids: ["0"] for a specific GPU
              capabilities: [gpu, video]          # `video` enables NVENC clip transcoding
                                                  # (the image also sets NVIDIA_DRIVER_CAPABILITIES
                                                  # accordingly, so plain `--gpus all` works too)
    volumes:
      - ./suslik-data:/data
```
```bash
docker compose up -d
docker compose logs -f
```

The startup self-check will report `cuda:0 — device engaged`. The CUDA runtime baked into the
image (CUDA 12.8) runs on any host driver from **R525** upward via CUDA minor-version
compatibility, covering GPUs from Maxwell to the RTX 50 series. Details and the consumer-GPU
compatibility note are in [hardware-acceleration.md](hardware-acceleration.md).

---

## Verifying the start

Whatever variant you run, watch the log:

```bash
docker logs -f suslik
```

You should see a 7-step startup self-check ending in `========== ready ==========`. It reports
which accelerator was found and whether it really engaged, connects to Frigate, and benchmarks
each usable backend on synthetic input. Then open `http://<host>:8199/` and follow the setup
wizard.

## Updating

**suslik never updates itself.** There is no auto-updater and no phone-home. A running container
keeps the image it started with — even if you use a `latest-*` tag — until you pull a newer image
and recreate the container. Nothing changes behind your back, but nothing arrives on its own either.

To update:

```bash
docker compose pull && docker compose up -d
```

Your data is not in the image. Everything suslik learns — reference faces, the unknown pool,
settings, event history — lives in the `/data` volume from your compose file and survives the
update untouched. Read the release notes before a major jump, then check the footer of any page in
the web UI: it shows the version that is actually running.

A `latest-*` tag only moves once a release has been deployed and verified on real test hardware
(Intel, NVIDIA, and plain CPU), so pulling it does not put you on something untested.

### Staying on a fixed version

`latest-<variant>` always points at the newest release of that variant. If you would rather decide
when to move, pin the version explicitly:

```yaml
    image: ghcr.io/bennobaer-dev/suslik:0.1.0.33-cpu
```

To move, change the tag and run `docker compose up -d`. Recent versions stay pullable, but a
release can be withdrawn if a serious problem is found in it — so a pin is a decision to postpone
an update, not a way to stay on one version forever. Every release is listed under
[Releases](https://github.com/BennoBaer-dev/suslik/releases); the tags currently available are on
the [package page](https://github.com/users/BennoBaer-dev/packages/container/package/suslik).

### Before you update

Back up the `/data` volume. In the web UI, **System → Configuration backup → Download
configuration** additionally saves your settings (thresholds, cameras, notification channels
including their stored secrets) as a single JSON file, and restores them from the same page —
settings only, not the learned people. Those are covered by the daily archive suslik writes into
`<data>/backups/`.

Next: [configuration.md](configuration.md) · [usage.md](usage.md)
