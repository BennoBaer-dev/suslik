# suslik

A small companion service for [Frigate](https://frigate.video/) that treats a person's walk
across your property as **one scenario across multiple cameras** — and gives Frigate's face
recognition an independent second opinion.

## Why this exists

Frigate's built-in face recognition works per frame and per camera, and on difficult footage it
can assign a confident label to the wrong person. suslik runs a **stronger, independent verify
layer**:

- It triggers on Frigate **person** events (robust), not on Frigate's face recognition (the part
  that struggles).
- It pulls the **full-resolution recorded clip** and searches across all frames itself for the
  best face — largest, sharpest, most frontal — instead of relying on one live crop.
- It matches against a calibrated reference library and requires **time consistency**: a person
  counts as recognized only when several frames within a short window agree. A single lucky frame
  is not enough.
- When it isn't sure, it says **"unknown"** — instead of a confident wrong guess.

The result is honest recognition: on good footage suslik and Frigate agree; on bad footage suslik
declines rather than mislabels.

## Features

- **Scenario grouping** across cameras — one walk = one verdict, not N noisy events.
- **Time-window confirmation** (several consistent frames, not a single frame).
- **Reference-library hygiene** tools (find no-face / mislabeled / confusable references).
- **Runs locally** — no cloud required. Hardware-accelerated on Intel (iGPU/NPU via OpenVINO) or
  NVIDIA (CUDA), with a CPU fallback that runs anywhere.
- **Alerts & integration** — Pushover, Telegram (via Home Assistant), and MQTT.
- **Web UI** with a guided setup wizard, scenario view, reference/unknown management, and a
  startup self-check you can read from `docker logs`.
- **Optional write-back** to Frigate (`sub_label` correction) — off by default (read-only).

## Quick start

Run the variant that matches your hardware (CPU shown here; see the guide for Intel/NVIDIA):

```yaml
# compose.yml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:<version>-cpu
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

Then open `http://<host>:8199/` and follow the setup wizard (connect Frigate → pick
cameras/zones → choose backend).

## Documentation

- **[Installation](docs/installation.md)** — the three image variants (CPU / Intel / NVIDIA),
  pull from GHCR or build yourself, `docker run` and `docker compose`.
- **[Configuration](docs/configuration.md)** — the setup wizard, config keys, environment
  variables, and the `/data` layout.
- **[Usage](docs/usage.md)** — a tour of the web UI, enrollment, and the scenario view.
- **[Architecture](docs/architecture.md)** — how the verify layer works and why there are
  separate hardware images.
- **[Hardware acceleration](docs/hardware-acceleration.md)** — backend selection, benchmarks, and
  the Intel/NVIDIA specifics.

## Status

suslik runs daily on the author's own setup. It is being packaged for others; the NVIDIA/CUDA
variant has been validated on real hardware. Expect rough edges and please open an issue if
something doesn't fit your setup.

## License

MIT — see [LICENSE](LICENSE).
