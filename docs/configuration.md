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
   master library (with live progress). You can run the same import later without re-running the
   wizard: **People → Known → Import / resync from Frigate**, or the *only in Frigate* section
   of the **Frigate sync** page. The System page only shows the sync balance and links there.
5. **Write back to Frigate?** — decide whether suslik may correct Frigate's `sub_label` and send
   face references back (parallel operation) or stay read-only. Pre-filled with your current
   setting; read-only is the safe default. Saying yes is a precondition, not the transfer
   itself: references go over on the **Frigate sync** page, where you pick the images (see
   [usage.md](usage.md)); `frigate_sync` additionally mirrors new references automatically.
   See *Read-back vs. write-back safety* below.

The wizard writes its choices into the config store and restarts the service once.

## Where configuration lives

Everything persistent is under the `/data` volume you mounted:

| Path (under `/data`) | What |
|---|---|
| `config/config.json` | the settings the wizard writes (Frigate URL, backend, zones, alert options …) |
| `faces/` | your reference face library (the "master") |
| `learn/` | enrollment data and the persistent unknown pool |
| `state/` | judgments, ground-truth labels, write-back log |
| `live/` | live watchers: per-camera evidence pictures of triggers and name messages, the recap videos of the live day view, and the alert log |
| `personlern/` | the person-recognition path: harvest runs with crops and your review verdicts, confirmed stranger images (`fremd/`), the trained model (`modell/`), judged live crops (`treffer/`, 30-day trim) and the fire-window state |
| `clips/`, `events/` | cached recorded clips (auto-pruned) and per-event crops/logs |
| `backups/` | daily rotating tar backups of the reference library + ground-truth files (14 kept) |

**`personlern/fremd/` — the stranger folder.** A flat folder of `.jpg` body crops of
people who are *not* residents. The model trains them as a class of its
own, and the decision threshold is calibrated against them instead of only between your
learned people (at least five images are needed; below that the old rule stays and Model
status says so). The folder starts empty on a fresh install; drop confirmed stranger
crops in, and the next training picks them up. Nothing else in suslik writes to it, and
removing the folder simply restores the previous behaviour.

Because config and data live in the volume, they survive image updates. Back up `/data` —
or use the **Full backup** card on the System page: it downloads one portable archive with
`config`, `faces`, `learn`, `personlern` and `state` (deliberately without the clip cache
and per-event artifacts), and the matching restore replaces those parts, keeps one
`.pre-restore` copy of each and restarts the service. Made for moving to another machine.

## Key settings

These are the settings most people touch (all set via the wizard/UI; names shown for reference):

- **`frigate_user` / `frigate_password`** — optional. Leave them empty and suslik talks to
  Frigate exactly as before, on the internal unauthenticated API (usually port 5000). Fill them in
  and suslik logs in the way the Frigate UI does (`POST /api/login`, session cookie, renewed by
  itself when it expires), which is what you need when suslik can only reach Frigate through its
  authenticated port 8971. The password is stored in the config store and shown masked; leaving
  the password field empty on save keeps the stored one. **`frigate_tls_verify`** (default on)
  can be switched off for Frigate's self signed certificate on 8971.
  Every request suslik sends to Frigate carries `suslik/<version>` as its user agent, with or
  without login, so you can allow it through a proxy by that name.

- **`backend`** — `auto` (default in the Intel image: a one-time startup
  benchmark decides where recognition runs — Intel NPU (`openvino:MIXED`), GPU or CPU — and
  the choice sticks in `state/placement.json` until hardware, runtime or version change),
  or explicit: `openvino:GPU` \| `openvino:NPU` \| `openvino:MIXED` (Intel), `cuda` \| `cuda:0`
  (NVIDIA), `cpu` (universal fallback for the analysis pipeline — note that **live
  watchers need a GPU build**; the watcher engine refuses to start on the cpu backend).
  Explicit values are never overridden.
  Equivalent environment variable: `VERIFY_BACKEND`.
- **`worker`** / **`worker_rss_max_mb`** — the persistent analysis worker (default on) keeps
  the models warm between events (the big per-event CPU win). It exits by itself
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
- **`frigate_sync`** — automatic mirroring of your reference library to Frigate (parallel
  operation), **off by default**. With `frigate_sync: true` *and* `frigate_read_only: false`,
  suslik uploads new active reference images by itself after each enrollment and after a sync
  run. It respects what you decided on the **Frigate sync** page: images you deselected are
  skipped, and images Frigate genuinely rejected are not retried until you tick them again. A
  round is skipped while a manual sync is running, since only one sync runs at a time. Selective,
  manual transfers on the sync page work regardless of this setting.
- **Alerts** — which judgment categories trigger an alert, and the global cooldown. Delivery
  channels are Pushover, Telegram (direct, or via Home Assistant: the `ha` mode calls the HA script `frigate_telegram_video` — create a script of that name in your HA instance, a configurable name is planned), and MQTT topics. The
  channels and their secrets are configured in the dedicated **Notifications** tab, which has a
  **Test** button per channel (see [usage.md](usage.md)).
- **Recognition threshold** — the time-window criterion (how many consistent frames within the
  window count as "recognized"). The defaults are calibrated; change only if you know why.
  The same similarity threshold also drives the live watchers' preliminary name stage.
- **Recognition chain** — its own Settings page: the order face → person → vision with a
  plain-language condition per step (always / only when the face path could not confirm
  everyone / off).
- **Live watchers** — configured per camera on the **Live** tab, not in the wizard:
  source (`proxy` / `direct` / `url`), processing resolution (360p–2160p, default
  1080p), the two times (appearance end, re-arm), and the notification channels per
  watcher. See [live-watchers.md](live-watchers.md).
- **Service log on disk** (`log_datei`, `log_behalten_tage`, `log_max_mb`) — suslik writes
  everything it prints to `<data_dir>/logs/suslik.log`, so the log survives restarts and stays
  readable without shell access to the container. The file is rotated on every service start,
  at midnight and when it passes `log_max_mb` (default 64); older pieces are gzipped and deleted
  after `log_behalten_tage` days (default 14). A full service run is roughly 70 kB, so two weeks
  cost megabytes, not gigabytes. Read it at `/log` (add `?lines=20000` for more than the default
  5000), or download every piece at once from `/log/suslik-logs.tar.gz` — that archive is the
  file to attach when you report a problem. Set `log_datei: false` to keep the old behaviour
  (in-memory ring buffer only).

## Environment variables

Set these on the container (compose `environment:` / `env_file:`, or `docker run -e`):

| Variable | Purpose |
|---|---|
| `TZ` | container timezone (e.g. `Europe/Berlin`). **Set this** — otherwise timestamps are UTC. |
| `VERIFY_BACKEND` | force the backend (overrides `backend` in the store if you prefer env config) |
| `FRIGATE_URL` | pre-fill the Frigate URL in the wizard (optional) |
| `SUSLIK_HWDEC` | hardware video decode for analysis frames: `auto` (default — uses the Intel iGPU via VAAPI or an NVIDIA GPU via NVDEC when the image ships a validated driver and the device is passed through; 8-bit 4:2:0 material only), `vaapi` / `nvdec` (force one source), `aus` (always software). Decoded pixels are bit-identical either way; if the hardware path fails, the software decoder takes over and the event is flagged. |
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

Two things are worth knowing before you switch it off. Frigate itself only accepts reference
uploads while **its own** face recognition is enabled (`face_recognition.enabled: true` in your
Frigate config); otherwise every upload comes back as HTTP 400 *"Face recognition is not
enabled."* suslik reports exactly that and shows Frigate's current on/off state live on the
**Frigate sync** page. And read-only never blocks reading: the class-by-class comparison, the
pre-check and importing *from* Frigate all keep working, only the transfer button is disabled.

## Known limitations

Honest list of what suslik does not do yet:

- **suslik's own web UI has no authentication.** Anyone who can reach port 8199 can view your
  reference faces and change settings. Run it on a trusted LAN only — do **not** expose port 8199
  to the internet. If you need remote access, put it behind a reverse proxy that adds
  authentication, or reach it over a VPN.

- **The catch-up sweep does not page through Frigate's event list.** Each round asks Frigate for
  the most recent `sweep_limit` person events (default 200) within `lookback_h`. On a busy site
  that window fills up long before the configured hours are covered: measured on a 31 camera
  commercial property, 773 person events in two hours, so the effective catch-up reach was about
  half an hour instead of two. Live operation is unaffected (every event is picked up as it ends);
  this only limits how far back suslik can catch up after downtime. Raise `sweep_limit` if you run
  many busy cameras. Real paging is planned.

Next: [usage.md](usage.md) · [hardware-acceleration.md](hardware-acceleration.md)
