# Installation

suslik ships as a Docker image in **three hardware variants** that share the exact same
application code — only the baked-in inference runtime differs. Pick the one that matches your
hardware:

| Variant | Image tag suffix | Accelerator | Use it when |
|---|---|---|---|
| **CPU** | `-cpu` | none (CPU only) | no GPU, or just trying it out (universal fallback) |
| **Intel** | `-gpu` | Intel iGPU / NPU via OpenVINO | you have an Intel integrated GPU (and optionally NPU) |
| **NVIDIA** | `-cuda` | NVIDIA GPU via CUDA | you have an NVIDIA GPU |

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
  clips). You configure the Frigate URL later in the setup wizard — nothing is hardcoded.
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

### Option 1 — pull from GHCR (recommended)

Published images live on the GitHub Container Registry. Check the repository's **Packages** page
for the available tags, then pull the variant/version you want:

```bash
docker pull ghcr.io/bennobaer-dev/suslik:<version>-cpu
docker pull ghcr.io/bennobaer-dev/suslik:<version>-gpu     # Intel
docker pull ghcr.io/bennobaer-dev/suslik:<version>-cuda    # NVIDIA
```

### Option 2 — build from source

Clone the repository and build the variant you need. The build bakes the models into the image
(no runtime downloads):

```bash
tools/build.sh cpu     # -> suslik:<version>-cpu
tools/build.sh gpu     # -> suslik:<version>-gpu   (Intel)
tools/build.sh cuda    # -> suslik:<version>-cuda  (NVIDIA)
```

`tools/build.sh` reads the version from the `VERSION` file and tags the image
`suslik:<version>-<variant>`. In the examples below, replace `suslik:<version>-<variant>` with
either your locally built tag or the `ghcr.io/bennobaer-dev/suslik:...` tag.

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
  suslik:<version>-cpu
```

**docker compose** (`compose.yml`):
```yaml
services:
  suslik:
    image: suslik:<version>-cpu       # or ghcr.io/bennobaer-dev/suslik:<version>-cpu
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
  suslik:<version>-gpu
```
> No NPU? Drop the `/dev/accel/accel0` line — the iGPU alone works.

**docker compose** (`compose.yml`):
```yaml
services:
  suslik:
    image: suslik:<version>-gpu       # or ghcr.io/bennobaer-dev/suslik:<version>-gpu
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
      - "render"                                  # or the numeric host GID of the render group
      - "video"
    volumes:
      - ./suslik-data:/data
```

The startup self-check will report `openvino:GPU — device engaged` when the iGPU is working. If
it says `running on CPU` instead, the host driver/runtime versions don't match — see
[hardware-acceleration.md](hardware-acceleration.md).

---

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
  suslik:<version>-cuda
```

**docker compose** (`compose.yml`):
```yaml
services:
  suslik:
    image: suslik:<version>-cuda      # or ghcr.io/bennobaer-dev/suslik:<version>-cuda
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
              capabilities: [gpu]
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

Next: [configuration.md](configuration.md) · [usage.md](usage.md)
