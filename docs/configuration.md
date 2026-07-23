# Configuration

Most configuration happens through the **setup wizard** in the web UI and is stored in your
`/data` volume — you rarely need to edit files by hand.

## Setup wizard

On first start (empty `/data`), opening `http://<host>:8199/` redirects to the wizard. You can
re-run it any time from **Settings → Re-run setup**. Steps:

1. **Connect Frigate** — enter your Frigate base URL (e.g. `http://<frigate-host>:5000`). suslik
   reads cameras and configuration from Frigate's API. Nothing is hardcoded.
2. **Cameras & zones** — choose which cameras to watch and, optionally, which zones must be
   entered for an event to be considered (see *Zone filter* below).
3. **Backend** — pick the accelerator to use (only backends actually available in your image
   variant are offered). See [hardware-acceleration.md](hardware-acceleration.md).
4. **Import references** — optionally import your existing Frigate face references into suslik's
   master library (with live progress). The same sync function is also on the **System** page.

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

Because config and data live in the volume, they survive image updates. Back up `/data`.

## Key settings

These are the settings most people touch (all set via the wizard/UI; names shown for reference):

- **`backend`** — `openvino:GPU` \| `openvino:NPU` \| `openvino:MIXED` (Intel), `cuda` \| `cuda:0`
  (NVIDIA), or `cpu` (universal fallback). Equivalent environment variable: `VERIFY_BACKEND`.
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
  channels are Pushover, Telegram (via Home Assistant automations on MQTT), and MQTT topics.
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

## Read-back vs. write-back safety

By default suslik only **reads** from Frigate: it never modifies your Frigate configuration or
labels. Write-back (correcting Frigate's `sub_label`, syncing faces) is opt-in via
`frigate_read_only: false`. Published/test setups stay read-only unless you change this — so
"nothing can break on your Frigate side" holds by default.

Next: [usage.md](usage.md) · [hardware-acceleration.md](hardware-acceleration.md)
