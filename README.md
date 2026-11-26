# suslik

suslik is a face recognition add-on for [Frigate](https://frigate.video/). It works together with
Frigate and replaces nothing there; it only talks to Frigate's API. It takes Frigate's person events,
looks for the best faces in the full-resolution recording, and counts a person's walk across several
cameras as one pass with one verdict. A name only counts when several frames agree; otherwise suslik
says "unknown".

It can also recognize residents by the whole body when no face is visible, for example from behind
(this part is a preview). Live watchers can watch selected cameras directly on the stream and report
a person within about a second.

The `latest-*` image tags follow the newest release. To stay on a fixed version, use its tag, for
example `ghcr.io/bennobaer-dev/suslik:0.1.1.116-gpu`.

## Why this exists

Frigate's built-in face recognition works per frame and per camera. On difficult footage it can put
a confident label on the wrong person. suslik checks the same events a second time, on its own. It
starts from Frigate's person events, which are reliable, and not from Frigate's face recognition. It
searches all frames of the recording itself for the best faces (large, sharp, frontal) and doesn't
rely on one live crop. And one lucky frame is not enough for a name: several frames within a short
window have to agree.

## What it looks like

The Today page shows who was on the property and when: one card per recognized person, plus cards
for probable matches and unknown visitors. The walks themselves are on the Passes tab.

![The Today page of suslik with recognized people and unknown visitors](docs/img/today.png?v=0.1.1.116)

*Screenshot from August 2026 (version 0.1.0.199), names and faces anonymized. The page has changed
since then.*

## What it does

- Person recognition (preview) names residents by the whole body when no face is visible. By
  default the name is only shown; notifications, presence and Frigate get it only if you switch
  that on. See [Person recognition](docs/person-recognition.md).
- Live watchers watch selected cameras directly on the stream. They report a person within about a
  second and add a preliminary name while the person is still in the picture. See
  [Live watchers](docs/live-watchers.md).
- suslik learns from your own recordings. A learning run goes through the person events Frigate has
  already recorded, collects the usable faces and groups them by person, and you name a whole group
  at once. See [Learning people](docs/learning.md).
- Notifications go out over Pushover, Telegram (directly or through Home Assistant) and MQTT.
- The recognition runs locally in Docker, with images for Intel (iGPU and NPU), NVIDIA, AMD and
  plain CPU.
- The web UI speaks English, German, Spanish, Italian, French and Finnish.
- Writing back to Frigate is optional and off by default: the name as a sub label, and reference
  faces for Frigate's own face library.
- Settings and everything the installation has learned can be saved as a backup and restored.

## Live trigger and confirmed name

The normal analysis works on the finished recording, after the event has ended. The confirmed name
therefore comes with a delay and is no real-time trigger. For automations that have to react while
someone is walking up (a light, an announcement), use the live watchers: they report a person on
the stream within about a second, for example over MQTT. The confirmed name still comes from the
normal analysis afterwards.

## Quick start

Pick the image for your hardware. This example uses the CPU image:

```yaml
# compose.yml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-cpu   # others: latest-gpu (Intel), latest-gpu-legacy, latest-cuda (NVIDIA), latest-rocm (AMD)
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

The gpu, gpu-legacy (older Intel iGPUs), cuda and rocm images also need the device passed into the
container (`devices:` and `group_add:`, or `--gpus` for cuda). Without it the gpu, gpu-legacy and
rocm images run on the CPU, and the cuda image cannot analyse at all. Either way, every page shows
a red notice, with the cause and the fix on the System page. The full compose blocks are in the
[installation guide](docs/installation.md). If suslik runs in an LXC container on Proxmox, see
[Proxmox](docs/proxmox.md). suslik can run next to Frigate on the same machine as a second
container.

Then open `http://<host>:8199/` and follow the setup wizard.

suslik never updates itself. Run `docker compose pull && docker compose up -d` when you want a
newer version. Learned faces and settings stay in the data volume. Event data is kept for 14 days
by default (`aufbewahrung_tage` on the Advanced page). Details, and how to stay on a fixed version:
[installation guide](docs/installation.md#updating).

## Documentation

- [Installation](docs/installation.md): the five image variants, pulling from GHCR or building
  from source, `docker run` and `docker compose`.
- [Proxmox](docs/proxmox.md): running suslik in an LXC container and passing the GPU through.
- [Configuration](docs/configuration.md): the setup wizard, config keys, environment variables and
  the `/data` layout.
- [Usage](docs/usage.md): a tour of the web UI.
- [Learning people](docs/learning.md): the learning run over your own recordings.
- [Person recognition (preview)](docs/person-recognition.md): recognizing residents without a
  visible face.
- [Live watchers](docs/live-watchers.md): watching camera streams directly, alerts and MQTT
  messages.
- [Architecture](docs/architecture.md): how the analysis works and why there are separate hardware
  images.
- [Supported hardware](docs/supported-hardware.md): what runs on which hardware, and what is not
  supported.
- [Hardware acceleration](docs/hardware-acceleration.md): backend selection and the Intel and
  NVIDIA specifics.
- [Known issues and limitations](docs/known-issues.md): current bugs, limits and what comes next.
- [Changelog](CHANGELOG.md): the last five releases. Older release notes are on the
  [releases page](https://github.com/BennoBaer-dev/suslik/releases).

## Status

suslik is an alpha. It runs every day on my own system, and versions change often. Person
recognition by the body is a preview. If something doesn't fit your setup, please open an issue.
What I already know about is on the [known issues](docs/known-issues.md) page.

All five image variants are on GHCR, each with its own `latest-<variant>` tag. The cuda image is
large because it bundles the CUDA runtime. gpu-legacy and rocm are tested by users and not on my
own machines, so reports from that hardware are welcome. Google Coral is not supported; I tested
it, and the details are on the known issues page.

The source code is in this repository under the MIT license. The images run offline: nothing is
downloaded at runtime, and internet access is only needed for the push notification channels.

## Contact

- GitHub: [issues](https://github.com/BennoBaer-dev/suslik/issues) for bugs and requests,
  [discussions](https://github.com/BennoBaer-dev/suslik/discussions) for everything else.
- E-mail: suslik_dev@posteo.de, if you'd rather write to me directly.

Every report helps, especially from hardware I can't test myself (rocm, gpu-legacy).

## License

The suslik code is MIT, see [LICENSE](LICENSE).

The container images also ship third-party models with their own, partly stricter terms: the
InsightFace `buffalo_l` pack is released by its authors for non-commercial research use only,
AdaFace is MIT (© 2022 Minchul Kim). The details and the verbatim terms are in [NOTICE](NOTICE).
Read it before any commercial use.
