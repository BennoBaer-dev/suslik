# Configuration

Most configuration happens through the **setup wizard** in the web UI and is stored in your
`/data` volume — you rarely need to edit files by hand.

## Setup wizard

On first start (empty `/data`), opening `http://<host>:8199/` redirects to the wizard. You can
re-run it any time from **System → Re-run setup wizard**.

Already migrating from another instance? The wizard also offers **"Already have a
configuration?"** at the top — upload a previous config backup (see *Configuration backup &
restore* below) to restore all settings and skip the wizard entirely. Otherwise, the steps are:

1. **Connect Frigate** — enter your Frigate base URL (e.g. `http://<frigate-host>:5000`). Use
   Frigate's **port 5000** (the internal, *unauthenticated* API) — **not** the authenticated port
   8971. Frigate authentication (the JWT/login on port 8971) is **not supported yet**, so suslik
   talks to the unauthenticated port 5000. suslik must be able to reach port 5000 (run it on the
   same host / Docker network as Frigate, or expose 5000 on your LAN). suslik reads cameras and
   configuration from Frigate's API. Nothing is hardcoded.
2. **Cameras & zones** — choose which cameras to watch and, optionally, which zones must be
   entered for an event to be considered (see *Zone filter* below).
3. **Backend** — pick the accelerator to use (only backends actually available in your image
   variant are offered). See [hardware-acceleration.md](hardware-acceleration.md).
4. **Import references** — optionally import your existing Frigate face references into suslik's
   master library (with live progress). The same sync function is also on the **System** page.
5. **Write back to Frigate?** — decide whether suslik may correct Frigate's `sub_label` and sync
   faces back (parallel operation) or stay read-only. Pre-filled with your current setting;
   read-only is the safe default. See *Read-back vs. write-back safety* below.

The wizard writes its choices into the config store and restarts the service once.

## Where configuration lives

Everything persistent is under the `/data` volume you mounted:

| Path (under `/data`) | What |
|---|---|
| `config/config.json` | the settings the wizard writes (Frigate URL, backend, zones, alert options …) |
| `faces/` | your reference face library (the "master") |
| `learn/` | enrollment data and the persistent unknown pool |
| `state/` | judgments, ground-truth labels, write-back log |
| `clips/`, `events/` | cached recorded clips (auto-pruned) and per-event crops/logs |
| `backups/` | daily rotating tar backups of the reference library + ground-truth files (14 kept) |

Because config and data live in the volume, they survive image updates. Back up `/data`.

## Key settings

These are the settings most people touch (all set via the wizard/UI; names shown for reference):

- **`backend`** — `auto` (default in the Intel image since 0.1.0.44: a one-time startup
  benchmark decides where recognition runs — Intel NPU (`openvino:MIXED`), GPU or CPU — and
  the choice sticks in `state/placement.json` until hardware, runtime or version change),
  or explicit: `openvino:GPU` \| `openvino:NPU` \| `openvino:MIXED` (Intel), `cuda` \| `cuda:0`
  (NVIDIA), `cpu` (universal fallback). Explicit values are never overridden.
  Equivalent environment variable: `VERIFY_BACKEND`.
- **`worker`** / **`worker_rss_max_mb`** — the persistent analysis worker (default on) keeps
  the models warm between events (the big per-event CPU win of 0.1.0.44). It exits by itself
  after 15 min of quiet and restarts lazily; if its memory ever exceeds
  `worker_rss_max_mb` (default 4096 MB) it is restarted cleanly. `worker: false` restores
  the old process-per-event behavior.
- **`fd_front_min` / `fd_sharp_min` / `fd_det_max`** — the false-detection filter. The face
  detector sometimes fires on things that are clearly not faces (a wheel hub, foliage, fabric);
  a detection is discarded from *counting, display and the unknown pool* when all three match:
  frontality ≥ `fd_front_min` (0.85), sharpness ≥ `fd_sharp_min` (1500) and detector score
  < `fd_det_max` (0.70) — the "static object" signature, calibrated on 407 hand-labeled
  detections (86% of false detections caught at a 1.2% cost of real faces, none of them
  load-bearing). Recognition itself is deliberately **not** filtered — judgments never change,
  and the Today page shows a footnote with what was filtered so nothing disappears silently.
- **`det_thresh`** — the face detector's own threshold (upstream default 0.5), made visible and
  configurable. Raising it is *not* recommended: 0.60 already costs ~16% of real faces.
- **Frigate connection** — the Frigate base URL. Can be pre-filled via the `FRIGATE_URL`
  environment variable for convenience, but the wizard value in the store wins.
- **Zone filter** — per camera, an optional list of required zones. Events that never entered one
  of the zones are skipped (logged only, no judgment) — *except* events where Frigate already
  assigned a face label, which are always checked. This keeps passers-by on the street from
  generating noise.
- **`frigate_read_only`** — whether suslik may **write back** to Frigate (correcting `sub_label`,
  uploading face sync). **Default `true` = read-only** (suslik never changes anything in Frigate).
  Set to `false` only if you deliberately want write-back.
- **Alerts** — which judgment categories trigger an alert, and the global cooldown. Delivery
  channels are Pushover, Telegram (direct, or via Home Assistant: the `ha` mode calls the HA script `frigate_telegram_video` — create a script of that name in your HA instance, a configurable name is planned), and MQTT topics. The
  channels and their secrets are configured in the dedicated **Notifications** tab, which has a
  **Test** button per channel (see [usage.md](usage.md)).
- **Recognition threshold** — the time-window criterion (how many consistent frames within the
  window count as "recognized"). The defaults are calibrated; change only if you know why.

## Environment variables

Set these on the container (compose `environment:` / `env_file:`, or `docker run -e`):

| Variable | Purpose |
|---|---|
| `TZ` | container timezone (e.g. `Europe/Berlin`). **Set this** — otherwise timestamps are UTC. |
| `VERIFY_BACKEND` | force the backend (overrides `backend` in the store if you prefer env config) |
| `FRIGATE_URL` | pre-fill the Frigate URL in the wizard (optional) |
| Secrets | credentials for Pushover / Telegram / MQTT are provided via environment variables (e.g. an `env_file`), never baked into the image. |

The service sets `VERIFY_BACKEND` process-wide, and all sub-processes inherit it — so one setting
controls the whole pipeline.

## Configuration backup & restore

The **System** page has a **Configuration backup** card:

- **Download configuration** saves all settings (thresholds, cameras, notification channels
  including their stored secrets) as one JSON file.
- **Restore from file…** loads such a file back — the previous settings are kept as a `.bak`
  next to the store, then the service restarts. The setup wizard can consume the same file via
  **"Already have a configuration?"**.

This covers **settings only**. Your learned people and reference faces are backed up separately by
the daily data backup written to `/data/backups/`.

## Read-back vs. write-back safety

By default suslik only **reads** from Frigate: it never modifies your Frigate configuration or
labels. Write-back (correcting Frigate's `sub_label`, syncing faces) is opt-in via
`frigate_read_only: false`. Published/test setups stay read-only unless you change this — so
"nothing can break on your Frigate side" holds by default.

## Known limitations

Honest list of what suslik does not do yet:

- **suslik's own web UI has no authentication.** Anyone who can reach port 8199 can view your
  reference faces and change settings. Run it on a trusted LAN only — do **not** expose port 8199
  to the internet. If you need remote access, put it behind a reverse proxy that adds
  authentication, or reach it over a VPN.

- **No Frigate authentication support.** suslik talks to Frigate's internal, *unauthenticated*
  API on **port 5000** — it has no support for the JWT/login on the authenticated port 8971. If
  your Frigate is locked down, keep port 5000 reachable to suslik (same host / Docker network, or
  a LAN-only exposure). Auth support is a possible future addition.

Next: [usage.md](usage.md) · [hardware-acceleration.md](hardware-acceleration.md)
