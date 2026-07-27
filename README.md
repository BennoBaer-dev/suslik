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
- **Notifications tab** — configure the Pushover / Telegram / MQTT channels in the UI (secrets kept
  in the data volume, shown masked) and send a test message per channel.
- **Config backup/restore** — download all settings as a single JSON file and restore them from it.
- **Web UI** with a guided setup wizard, scenario view, reference/unknown management, and a
  startup self-check you can read from `docker logs`.
- **Optional write-back** to Frigate (`sub_label` correction) — off by default (read-only).

## Quick start

Run the variant that matches your hardware (CPU shown here; see the guide for Intel/NVIDIA):

```yaml
# compose.yml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-cpu   # -gpu = Intel · -cuda = NVIDIA · latest-<variant> = newest of that variant
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

> Using the **Intel** (`latest-gpu`) or **NVIDIA** (`latest-cuda`) variant? Those additionally
> need device passthrough (`devices:`/`group_add:` for Intel, `--gpus` for NVIDIA) — without it
> they silently fall back to CPU. See [installation](docs/installation.md) for the full compose
> blocks. suslik runs happily **next to Frigate on the same machine** as a second container.

Then open `http://<host>:8199/` and follow the setup wizard (connect Frigate → pick
cameras/zones → choose backend).

**Updating** — suslik never updates itself. Run `docker compose pull && docker compose up -d` when
you want a newer version; your data lives in the volume and is untouched. Details, and how to pin a
fixed version instead: [installation.md](docs/installation.md#updating).

## Documentation

- **[Changelog](CHANGELOG.md)** — what changed per release. Worth a look right now:
  **0.1.0.47 is the performance wave** — from roughly a CPU-minute per event to seconds,
  with NPU support, automatic accelerator placement and judgments proven unchanged.
- **[Installation](docs/installation.md)** — the three image variants (CPU / Intel / NVIDIA),
  pull from GHCR or build yourself, `docker run` and `docker compose`.
- **[Configuration](docs/configuration.md)** — the setup wizard, config keys, environment
  variables, and the `/data` layout.
- **[Usage](docs/usage.md)** — a tour of the web UI, enrollment, and the scenario view.
- **[Architecture](docs/architecture.md)** — how the verify layer works and why there are
  separate hardware images.
- **[Supported hardware](docs/supported-hardware.md)** — the full matrix (integrated GPUs are
  first-class; NVIDIA, CPU-only, and what is explicitly not supported) with a measured
  performance comparison across Intel iGPU+NPU, CUDA and CPU.
- **[Hardware acceleration](docs/hardware-acceleration.md)** — backend selection, benchmarks, and
  the Intel/NVIDIA specifics.
- **[Known issues & limitations](docs/known-issues.md)** — an honest list of current bugs,
  limitations and what comes next.

## Status

suslik runs daily on the author's own setup. It is being packaged for others: all three variants
— **CPU**, **Intel** and **NVIDIA/CUDA** — are published on GHCR and have been validated on real
hardware (the CUDA image is large, since it bundles the multi-GB CUDA runtime, so it takes longer
to pull). Expect rough edges and please open an issue if something doesn't fit your setup —
[known issues & limitations](docs/known-issues.md) lists what we already know.

**Source code:** the application source is **not published here yet — it will follow.** Until
then the images are prebuilt-only, which honestly means you can't audit the code, only its
behavior: everything runs locally, nothing is downloaded at runtime, and internet access is only
needed for the optional push-notification channels.

## What's being worked on right now

*(updated 2026-07-27 — this section changes with every release)*

- **Performance wave** *(shipped in 0.1.0.47)*: a persistent analysis worker keeps the
  models warm, recognition can run on the Intel NPU (picked automatically by a one-time
  startup benchmark), the detector follows the clip's aspect ratio, browser copies are
  transcoded lazily, and NVIDIA gets a full-hardware NVENC pipeline. Net effect on the
  author's box: from roughly a CPU-minute per event to ~8–13 CPU-seconds warm — with
  fixed-point acceptance proving judgments unchanged on CPU, Intel GPU/NPU and CUDA.
- **First-run backfill & guided learning mode**: choose how many past events suslik
  should analyze on first start (with a test-event time estimate), then learn people
  from frontal-anchor clusters — the most-requested tester feature so far.
- **Today view drill-down**: click a person and see their walkthroughs of the day
  (scenario view), instead of landing on a single event.
- **Automatic false-trigger class**: passes where Frigate saw a "person" but the whole
  clip contains no usable face will get their own quiet class instead of counting as
  unknown visitors.
- **Smaller images**: yes, we know the images are big — models, drivers and runtimes are
  baked in on purpose so nothing is ever downloaded at runtime. Docker only pulls changed
  layers on updates, but shrinking the images properly is planned for a later pass.
- **Checked — Google Coral TPU**: we looked into it properly, and the honest verdict is:
  not a fit. Face-recognition models are 40–260 MB of float weights, the Coral wants
  small fully-quantized models with ~7 MB of on-chip cache, Google has archived the
  entire Coral toolchain, and on CPU-only boxes the stick is usually already busy doing
  Frigate's object detection. We may still test a lightweight model with our
  every-frame method on real Coral hardware — if that surprises us, it goes in.
- **Further out — recognizing people beyond the face**: once a person has been positively
  identified by face, keep a few appearance snapshots and use a local vision model to
  recognize them even when no usable face is visible. Local-first, baked into the images
  like everything else.

Thanks to everyone testing and reporting back — the feedback is directly shaping this list.

## License

The suslik **code** is MIT — see [LICENSE](LICENSE).

The container images additionally ship third-party **models** that carry their own,
partly stricter terms (the InsightFace `buffalo_l` pack is released by its authors for
non-commercial research use only; AdaFace is MIT, © 2022 Minchul Kim). Details and the
verbatim terms are in [NOTICE](NOTICE) — read it before any commercial use.
