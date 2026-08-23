# suslik

A small companion service for [Frigate](https://frigate.video/) that treats a person's walk
across your property as **one scenario across multiple cameras** — and gives Frigate's face
recognition an independent second opinion.

The learning module works end to end: a learning run walks through the person events
Frigate already recorded, harvests the usable faces, groups them into recurring people,
and lets you name a whole cluster at once instead of labeling single images. Named
clusters go straight into recognition. Camera areas (stage 1: areas as views) are in;
per-area alert behavior is the part still being built. **Live watchers**, extended in
0.1.0.199: selected cameras are watched directly on the stream — a presence signal with
a picture within about a second, plus a preliminary name while the appearance is still
running (see the roadmap section below).

The `latest-*` image tags follow the newest release, so `docker compose pull` gets you
what this README describes. To pin a version instead, use its tag explicitly:
`ghcr.io/bennobaer-dev/suslik:0.1.0.331-gpu`.

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

## What it looks like

The Today page answers "who was on the property, when, and where did they go" — one card per
person, one block per pass, unknowns kept visible instead of buried:

![suslik Today page — recognized people, unknown visitors and the day's passes](docs/img/today.png?v=0.1.0.331)

*(Screenshot from a live install of v0.1.0.199; names and faces anonymized. The
"Recognized live" row is the live watchers' preliminary naming, right on the stream.)*

"Recognized live" cards collect the appearances a live watcher named right on the
stream; clicking one opens the live day view with one card per camera appearance,
all stored face images and short look-back videos.

## Features

- **Scenario grouping** across cameras — one walk = one verdict, not N noisy events.
- **Time-window confirmation** (several consistent frames, not a single frame).
- **Reference-library hygiene** tools (find no-face / mislabeled / confusable references).
- **Live watchers** — selected cameras are watched directly on the live stream: an
  immediate presence signal with a picture for any person, and a preliminary name during
  the same appearance, over the same Pushover / Telegram / MQTT channels.
- **Runs locally** — no cloud required. Hardware-accelerated on Intel (iGPU/NPU via
  OpenVINO), NVIDIA (CUDA) and AMD (ROCm), with a CPU fallback that runs anywhere.
- **Alerts & integration** — Pushover, Telegram (via Home Assistant), and MQTT.
- **Notifications tab** — configure the Pushover / Telegram / MQTT channels in the UI (secrets kept
  in the data volume, shown masked) and send a test message per channel.
- **Config backup/restore** — download all settings as a single JSON file and restore them from it.
- **Web UI** with a guided setup wizard, scenario view, reference/unknown management, and a
  startup self-check you can read from `docker logs`.
- **Five languages** — the UI speaks English, German, Spanish, Italian and French. Pick
  yours with the header switch or in step 0 of the setup wizard; one setting for the whole
  installation, it survives backups. Almost everything is translated; only the Today page
  still has a few English bits, and it says so.
- **Optional write-back** to Frigate — `sub_label` correction *and* uploading reference faces
  from the Frigate sync page. Off by default (read-only); in read-only mode the import direction
  (Frigate → suslik) still works, only the transfer out is blocked.
- **Frigate sync (own page)** — a class-by-class reconciliation of your reference library with
  Frigate's: what is on both sides, what is ready to transfer, what only Frigate has (import),
  what you deleted in Frigate (your decision, offer it again or respect the deletion; nothing is
  re-sent on its own), what was sent earlier through Frigate's API (Frigate renames those, so
  suslik says honestly that it cannot verify them), and what Frigate rejected. You tick the
  images that go out, a pre-check flags the ones Frigate will likely refuse, and after the
  transfer every picture shows Frigate's real answer. A one-click diagnosis bundles the suslik
  report with Frigate's own log. Needs write-back enabled and Frigate's own face recognition
  switched on.
- **Vision detect (early working version)** — a third, independent recognition path: a
  vision-language model judges a whole walk-through as one candidate grid against your
  approved galleries. Runs against a local llama.cpp server or any OpenAI-compatible
  endpoint you configure — without that, nothing leaves your machine. Includes a gallery
  wizard that curates reference proposals itself, and a recognition test that shows face,
  person and vision side by side for any past pass.
- **Person recognition (preview)** — a second, independent path that learns residents by their
  whole appearance (build, hair, posture) and recognizes them **without a visible face**. You
  harvest images from your own recordings, approve every picture by hand, and arm it yourself;
  alerts are clearly marked as person recognition. See **[Person recognition](docs/person-recognition.md)**
  for the step-by-step guide.

## Two speeds: the live trigger and the confirmed verdict

The **verify layer** is not a real-time trigger. It works on the finished clip, after the
event ends — it waits for more evidence and then tries to be right. That is a design
decision, and it has a measurable cost: from a person appearing to the confirmed verdict is
typically **25 seconds at the very best, usually noticeably more** (event duration + clip
availability + analysis; measured across 414 real events by a user, median around a minute).
For arrival automations — a light that should turn on as someone walks up, or a spoken
greeting — use the **live watchers**: they signal a person off the stream within about a
second and add a preliminary name during the same appearance, e.g. over MQTT. The verify
layer's job is the part neither Frigate nor a live trigger can do: deliver the reliable answer afterwards
and correct the record.

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

> Using the **Intel** (`latest-gpu`, or `latest-gpu-legacy` for 6th–10th gen Core iGPUs),
> **NVIDIA** (`latest-cuda`) or **AMD** (`latest-rocm`) variant? Those additionally
> need device passthrough (`devices:`/`group_add:` for Intel and AMD, `--gpus` for NVIDIA) —
> without it they silently fall back to CPU. See [installation](docs/installation.md) for the full
> compose blocks. suslik runs happily **next to Frigate on the same machine** as a second container.

Then open `http://<host>:8199/` and follow the setup wizard (connect Frigate → pick
cameras/zones → choose backend).

**Updating** — suslik never updates itself. Run `docker compose pull && docker compose up -d` when
you want a newer version; your data lives in the volume and is untouched. Details, and how to pin a
fixed version instead: [installation.md](docs/installation.md#updating).

## Documentation

- **[Changelog](CHANGELOG.md)** — what changed per release. Worth a look right now:
  **0.1.0.199** gave the live watchers a preliminary **name stage** (per-frame voting
  across the whole appearance, fired once per person — two people in one pass produce
  two messages), made the processing resolution selectable per camera (default 1080p),
  replaced the predictive capacity model with "enabled means running" plus a runtime
  throttle, and added the appearance day view with all face pictures and recap videos
  per pass. The changelog file keeps recent releases; older release notes live on the
  [releases page](https://github.com/BennoBaer-dev/suslik/releases).
- **[Installation](docs/installation.md)** — the five image variants (CPU / Intel / Intel legacy / NVIDIA / AMD-testing),
  pull from GHCR or build from the source in this repository, `docker run` and `docker compose`.
- **[Configuration](docs/configuration.md)** — the setup wizard, config keys, environment
  variables, and the `/data` layout.
- **[Usage](docs/usage.md)** — a tour of the web UI, enrollment, and the scenario view.
- **[Learning people](docs/learning.md)** — the guided learning run over your own
  recordings: harvest, grouping into recurring people, naming a cluster once, adoption.
- **[Person recognition (preview)](docs/person-recognition.md)** — recognizing residents
  without a visible face: learn, review, arm, and what the alerts look like.
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

**This is an alpha and a published work in progress.** suslik runs daily on the author's own
setup, and the current focus is on two things at once: the **learning module** (harvesting faces
from your existing recordings and clustering recurring people) and **camera areas** (grouping
cameras into parts of the property as views, with per-area alerting to follow). The learning
side already holds up well — a learning run over any number of past events reliably surfaces
the people who keep coming back, ready to be named in one step. Everything around it is moving:
treat version jumps as normal, and please open an issue if something doesn't fit your setup —
[known issues & limitations](docs/known-issues.md) lists what we already know. If you'd
rather write me directly: **suslik_dev@posteo.de** — feedback of any kind, positive or
negative, is genuinely welcome.

All five image variants — **CPU**, **Intel**, **Intel legacy**, **NVIDIA/CUDA** and
**AMD/ROCm** — are published on GHCR (the CUDA image is large, since it bundles the multi-GB
CUDA runtime, so it takes longer to pull). Every variant carries its own `latest-<variant>`
tag; **gpu-legacy** and **rocm** are still community-tested — reports very welcome.

**Source code:** published in this repository (MIT). The images remain
self-contained: everything runs locally, nothing is downloaded at runtime, and internet access is
only needed for the optional push-notification channels.

## What's being worked on right now

*(updated 2026-08-21 — this section changes with every release)*

- **Face learning with a quality score** *(shipped in 0.1.0.321)*: the face check
  after a pass looks at every frame from every camera, measures how good a face really
  is with a reference-free score and offers more and better pictures, grouped by view.
  Every reference picture carries that quality value, weak ones are flagged, and group
  naming in learning runs pre-selects by it. Next: the same measure for the unknown
  visitor pool.

- **Multilingual UI** *(started in 0.1.0.298, nearly complete in 0.1.0.321)*: the
  interface speaks English, German, Spanish, Italian and French. The help pages, the
  setup wizard, all inner pages and dialogs and the notification texts are translated;
  only the Today page still has a few English bits and says so. All translations are
  native-speaker reviewed.

- **Vision detect (early working version)** *(shipped in 0.1.0.168)*: a third
  recognition path, independent of the other two. A vision-language model judges the
  whole walk-through as one candidate grid against your approved galleries — measured
  here as clearly better than comparing single pictures. It talks to a local
  llama.cpp server or any OpenAI-compatible endpoint you configure; without that
  configuration nothing leaves your machine. Galleries are built by a wizard that
  scores proposals on face visibility, lighting and completeness and says per image
  why it was picked or dropped. The recognition test page runs face, person and vision
  over the same past pass so you can see where a judgement comes from. This is
  published ahead of completion for testing: interfaces and defaults will still move,
  and which model class is good enough is documented from our own measurements.

- **Frigate sync** *(shipped in 0.1.0.138)*: your reference library and Frigate's are
  reconciled class by class on their own page — ready to transfer, only in Frigate,
  deleted in Frigate, sent earlier, rejected. Transfers are selective and pre-checked,
  and every image reports Frigate's real answer. Open: Frigate renames what it accepts,
  so images sent through the API cannot be verified afterwards.
- **Person recognition (preview)** *(shipped in 0.1.0.113, extended since)*: the second
  recognition path that works without a visible face. It cooperates with
  the face path on Today (passes with no usable face are attributed to the person the body
  path recognized, clearly marked), its decision threshold is measured from your own
  reviewed material after every training, and the fire rule is configurable. Since
  Confirmed stranger images (`personlern/fremd/`) are trained as their own
  class and the threshold is calibrated against them. Next: collecting that stranger
  material from inside the UI, and moving the harvest inference to the GPU/NPU.
- **Performance**: one pinned pixel path everywhere,
  video decoding on the GPU (Intel via VAAPI, NVIDIA via NVDEC) with hard gates and a loud
  software fallback, and only the sampled frames leave the decoder. On my machine a
  learning run went from 6.6 to 2.9 seconds per event. Still open: the person-harvest
  inference (pose gate + embedding) is CPU-bound and next in line.
- **False-trigger handling** *(shipped in 0.1.0.129)*: passes where the whole
  clip contains no serious face get their own quiet class instead of counting as unknown
  visitors, the labeling list collapses weak faces with nothing confirmed nearby, and a
  **No person** button closes a false trigger with one click (issue #16).
- **Anchor triage** *(shipped in 0.1.0.129)*: unnamed clusters show a
  "looks like: X" suggestion right on the overview, and clusters that a newer run
  re-harvested identically are dimmed so you only name the newest one.
- **Learning module** *(works end to end)*: harvest, quality gates, clustering into
  recurring people, naming with per-perspective recommendations, and adoption into
  recognition.
- **Camera areas** *(stage 1 shipped in 0.1.0.92-alpha)*: group cameras into parts of your
  property; areas act as views on Today/Appearances/Events, and alerts name the area.
  Passes are always judged across the whole property. Per-area alert behavior is stage 2.
- **Live watchers** *(shipped in 0.1.0.182, substantially extended through 0.1.0.199)*:
  the live path is real now — a Live tab watches selected cameras directly on the stream,
  in two stages: the presence trigger reports any person with a picture after four
  consistent face finds in about two seconds (measured 199–801 ms from first face to
  signal on my machine), and the name stage then votes frame by frame across the whole
  appearance and fires once per appearance and person — two people walking through
  together produce two name messages. Watchers are switched on per tile after a source
  test; enabled means running (no capacity estimate any more — the only hard limits are
  five watchers at once and a memory floor, and under load the service thins out its own
  sampling). GPU-only for now (video decode via Intel VAAPI or NVIDIA NVDEC, the latter
  verified on an RTX 2060). The live part is still young — report what breaks.
  How it works: [live-watchers.md](docs/live-watchers.md).
- **Planned — "recurring, not a resident"**: a third review option next to naming and
  discarding, so the courier who comes three times a week doesn't silently disable your
  stranger alerts (tester feedback).
- **Smaller images**: yes, I know the images are big — models, drivers and runtimes are
  baked in on purpose so nothing is ever downloaded at runtime. Shrinking them properly is
  planned for a later pass.
- **Checked — Google Coral TPU**: I ran the test instead of guessing. A Coral-sized
  recognition model does fit the chip and even keeps strangers out — but it loses real
  residents (the separation band collapses to ~0.02). No threshold fixes that, so the
  verdict is a measured no. Details in [known-issues.md](docs/known-issues.md).

Thanks to everyone testing and reporting back — the feedback is directly shaping this list.

## Contact

Two ways to reach me, whichever suits you:

- **GitHub** — [issues](https://github.com/BennoBaer-dev/suslik/issues) for bugs and
  requests, [discussions](https://github.com/BennoBaer-dev/suslik/discussions) for
  everything else.
- **E-mail** — **suslik_dev@posteo.de** for anything you'd rather write directly.

Positive or negative, short or long — every report helps, especially from hardware I
can't test myself (rocm, gpu-legacy).

## License

The suslik **code** is MIT — see [LICENSE](LICENSE).

The container images additionally ship third-party **models** that carry their own,
partly stricter terms (the InsightFace `buffalo_l` pack is released by its authors for
non-commercial research use only; AdaFace is MIT, © 2022 Minchul Kim). Details and the
verbatim terms are in [NOTICE](NOTICE) — read it before any commercial use.
