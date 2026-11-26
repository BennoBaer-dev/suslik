# Configuration

Most configuration happens through the **setup wizard** in the web UI and is stored in your
`/data` volume — you rarely need to edit files by hand.

## Setup wizard

On first start (empty `/data`), opening `http://<host>:8199/` redirects to the wizard. You can
re-run it any time from **System → Re-run setup wizard**.

Already migrating from another instance? The wizard also offers **"Already have a
configuration?"** at the top — upload a previous config backup (see *Configuration backup &
restore* below) to restore all settings and skip the wizard entirely. Otherwise, the steps are:

1. **Connect Frigate** — enter your Frigate base URL, usually the internal, unauthenticated API on
   port 5000 (e.g. `http://<frigate-host>:5000`; run suslik on the same host or Docker network as
   Frigate, or expose 5000 on your LAN). If Frigate only answers on its authenticated port 8971,
   enter `https://<frigate-host>:8971`, set `frigate_user` and `frigate_password` on the
   **Advanced** settings page and switch `frigate_tls_verify` off for Frigate's self-signed
   certificate (see *Key settings*). suslik reads cameras and configuration from Frigate's API. Nothing is hardcoded.
2. **Cameras & zones** — choose which cameras to watch and, optionally, which zones must be
   entered for an event to be considered (see *Zone filter* below). A camera you turn off is fully
   off: suslik fetches and checks nothing from it, not even events where Frigate already assigned
   a face label.
3. **Backend** — pick the accelerator to use (only backends actually available in your image
   variant are offered). See [hardware-acceleration.md](hardware-acceleration.md).
4. **Import references** — optionally import your existing Frigate face references into suslik's
   master library (with live progress). You can run the same import later without re-running the
   wizard: **Faces → Known → Import / resync from Frigate**, or the *only in Frigate* section
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
| `refquelle/` | the reference source: one set per learned face (`refquelle/<ref_id>/`: face crop, fingerprint, profile picture, person crop, origin record) and the catalog `refquelle/katalog.jsonl` that binds each set to a person — your reference face library. `refquelle/koerperbilder/` holds the body images of the person recognition: one PNG per image and the file `koerperbilder.jsonl` with person, event, time, fingerprint and state (open, valid, discarded) |
| `faces/` | a derived copy of the profile pictures, one folder per person, rebuilt by suslik for display and export; not a source any more |
| `learn/` | enrollment data and the persistent unknown pool |
| `state/` | judgments, ground-truth labels, write-back log; `state/koerper_treffer.jsonl` holds the results of the body recognition: one line per comparison, a rename of a person appends more lines, and per event the last line counts; `state/anwesenheit/` holds the presence marks (one file per day: who was seen where, per quarter hour: confirmed by face or the live watcher, or via person recognition when that switch is on — personal data); `state/archiv/` holds removed reference sets, the copy of the old stock from the one-time migration (`vor_refquelle_<date>/`) and the parts replaced by a restore — nothing in it is deleted |
| `live/` | live watchers: per-camera evidence pictures of triggers and name messages, the appearance videos sent over Telegram and shown in the live day view, and the alert log |
| `personlern/` | only on systems that ran an older version: the material of the old person-learn run (model, harvested images, runs, vision galleries). Nothing reads it any more. The maintenance step "data cleanup" moves the whole folder into the trash, which suslik empties 7 days later |
| `clips/`, `events/` | cached recorded clips (auto-pruned) and per-event crops/logs |
| `backups/` | tar backups written by versions before the reference source; suslik writes none any more and leaves the old ones in place — the full backup below replaces them |

Because config and data live in the volume, they survive image updates. Back up `/data` —
or use the **Full backup** card on the System page: it downloads one portable archive with
`config`, `faces`, `learn`, an old `personlern` folder while it is still there, `state` (with `state/archiv/`)
and, from `refquelle/`, the catalog, the reference sets and the open and valid body images (candidate sets
stay out, they are produced again), deliberately without
the clip cache and per-event artifacts. The matching restore moves the parts it replaces into
`state/archiv/`, deletes nothing and restarts the service. Made for moving to another machine. Before
the update to the first version with the reference source, also save `clips/refcache.npz` (see
[installation.md](installation.md#before-you-update)).

Two settings belong to the reference source: `profil_faktor` (default 2.2, must be above 1.5) sets the
side of a stored profile picture as this factor times the longer side of the face box, and
`aufbewahrung_tage` (default 14, whole days from 1, on the **Advanced** settings page) is how long everything
tied to events is kept: old event folders, the monthly archive files of the event record
(`state/archiv/deckung_YYYY-MM.jsonl`), the pieces of the unknown queue and the log of names written to Frigate
(`state/sublabel_writes.jsonl`). The period is a fixed number of days counted by suslik itself; it does not follow
Frigate's own retention, so an event folder can outlive its Frigate event if Frigate keeps events for a shorter
time. Saving a new value restarts the service and the maintenance at that start applies it; lowering it deletes
older event folders without ground truth at once, and that start logs a line starting with `crops retention:` when folders were
removed.

Candidate sets that were never chosen and discarded sets do not follow `aufbewahrung_tage`: after an offer
period of 7 days they move, together with their catalog lines, into the trash folder `<data>/papierkorb/<date>/`.
Unknown groups without an appearance for 7 days and the archive files,
queue pieces and log lines above once they are older than `aufbewahrung_tage` go the same way; old event folders
are deleted directly. suslik empties each day folder of the trash 7 days later; until then you can take things
back out by hand. This runs in the maintenance step "data cleanup" at start and every day at 06:00, except for the
pieces of the unknown queue: the consumer of the unknown queue moves those itself in each of its rounds. The 7-day
periods are fixed defaults and cannot be changed in the UI. References and the archive `state/archiv/refquelle/`
are never moved to the trash, and the trash is not part of the full backup.

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
  (NVIDIA), `cpu` (computes on the CPU, available in every image).
  Explicit values are never overridden.
  `cpu` set explicitly is a deliberate choice, not a fallback, also on a GPU image: the log says
  `cpu requested — computing on CPU` instead of warning that the accelerator did not bind, and live
  watchers start in the limited CPU mode (one watcher recommended, they share the CPU cores) instead
  of being refused. A GPU image that ends up on the CPU without that choice — for example `auto`
  when the device does not bind — is still reported as a fallback. `openvino:CPU` is not offered by
  the wizard; set by hand, it computes on the CPU (the analysis worker runs its CPU engine, on the
  OpenVINO CPU runtime where the image has it), not on the GPU.
- **`worker`** / **`worker_rss_max_mb`** — the persistent analysis worker (default on) keeps
  the models warm between events (the big per-event CPU win). It exits by itself
  after 15 min of quiet and restarts lazily; if its memory ever exceeds
  `worker_rss_max_mb` (default 4096 MB) it is restarted cleanly. `worker: false` restores
  the old process-per-event behavior.
- **`stillstand_min`** — how many minutes work may wait without one successful analysis before
  the service reports a standstill: `/health` turns red, the log gets an ERROR line and the fault
  channel a message. Work means events in the queue or being analysed, background and harvest
  jobs, and due catch-up retries; the events held back at start for the catch-up button do not
  count. 10 is the default. The lowest value is 10 because the check runs every 10 minutes, a
  smaller one could not take effect; the highest is 120 so that a real standstill never stays
  unreported for more than two hours.
- **`speicher_ruhe_min`** — how many minutes the card memory must stay free before the service
  uses more of it again: one more compute thread for the analysis worker, or a live watcher that
  was switched off for lack of card memory. The room has to be there the whole time; after a
  setback the time starts again from the beginning. 10 is the default. The lowest value is 10 so
  that the number of threads cannot swing up and down within minutes (a field system went 5, 6,
  5); the highest is 240 so that a card with room again waits at most four hours. Watchers come
  back one per such period. The time only runs while the service runs and jobs arrive; after a
  restart it starts from the beginning.
- **`poll_interval`** — seconds between two queries to Frigate for new events, in poll mode only
  (`trigger: poll`); with MQTT it has no effect. Default 10, allowed 5 to 300. A shorter interval
  picks up finished events sooner and asks Frigate more often. It is on the **Advanced** settings
  page (`/konfiguration`, in the menu in Expert mode) and takes effect without a restart: the next
  poll waits the new interval. Up to version 0.1.1.034 the default was 20. On the first start of
  the version that brought this change, suslik moved the value once from 20 to 10 if it was still
  at the old default (whether from your config file or from the settings store), with a line in
  the log and in the config audit; any other value is kept. A marker in `state/` records that this
  happened, so setting 20 again later, or restoring an older config backup, keeps your value.
  Restoring a full backup from before that version brings back `state/` without the marker, and
  the next start moves the old default once more.
- **`clip_aufnahme_deckel_s`** — the longest time, in seconds from the moment an event is queued,
  that suslik waits until Frigate has recorded the event up to its end. Default 20, allowed 5 to
  120; on the **Advanced** settings page, takes effect without a restart. This is an upper limit,
  not a fixed delay. Frigate builds a clip only from the recording segments it has already
  written, so a clip fetched too early can end before the event does. Before every clip fetch
  suslik therefore asks Frigate whether the recording reaches the end of the event
  (`/api/<camera>/recordings` at the event's end time) and fetches as soon as Frigate says so; until
  then it asks again every 2 seconds. Older events are usually covered at the first question. If
  the limit is reached first, suslik fetches what is there, writes a WARNING to the log and notes
  `aufnahme_unbestaetigt: deckel` in the event's record. Only if Frigate does not answer the
  question (an error, or an answer that is not a list) does the limit act like a fixed delay: the
  event waits the full time from being queued and is then fetched without the check
  (`aufnahme_unbestaetigt: abfrage_fehler`), and `/health` `ok` is false until a query succeeds
  again. `/health` `vorlauf.aufnahme` shows the number of queries (`abfragen`), the number of
  fetches without confirmation (`deckel`), and for the fallback `rueckfall`, `fehler` and
  `letzter_fehler`. The limit counts on suslik's own clock and never compares it with Frigate's,
  so the two machines may run with different clocks. A larger value gives Frigate more time before
  a clip is fetched unconfirmed; it does not delay clips whose recording is already complete.
- **`clip_delay`** was removed. suslik no longer waits a fixed time before it fetches a clip (the
  check above replaces it). A `clip_delay` line in your config file, or a value in the settings
  store, has no effect: suslik drops it at every start and says so once in the log (with the old
  value) and in the config audit. You can delete the line.
- **`/health` fields for stalls, losses and fallbacks** — `ok` is false while a start check
  failed, an analysis-failure series is active or a standstill lasts; a standstill lasts until the
  next successful analysis. `nachhol` counts the events the catch-up run gave up for good since the
  service started (`verloren_n`, split by reason: `fenster`, `versuche`, `kaputt`, `event_weg`,
  `clip_weg`, `kein_ergebnis`); each of them also has one ERROR line in the log.
  `worker.absagen_n` counts the jobs the card memory gate refused since start. `worker.person`
  is no longer filled (it stays `{"fallback": false, "backend": null}`): the body fingerprint runs in
  its own body process, and a fallback to the CPU there writes one ERROR line.
  `worker_straenge.wechsel_letzter` (direction, from, to, time, reason) and `wechsel_n` show the
  changes of the compute thread count since start; a drop below the configured `worker_straenge`
  and a drop back after a rise are ERROR lines.
- **`fd_front_min` / `fd_sharp_min` / `fd_det_max`** — the false-detection filter. The face
  detector sometimes fires on things that are clearly not faces (a wheel hub, foliage, fabric);
  a detection is discarded from *counting, display and the unknown pool* when all three match:
  frontality ≥ `fd_front_min` (0.85), sharpness ≥ `fd_sharp_min` (1500) and detector score
  < `fd_det_max` (0.70) — the "static object" signature, calibrated on 407 hand-labeled
  detections (86% of false detections caught at a 1.2% cost of real faces, none of them
  load-bearing). Recognition itself is deliberately **not** filtered — judgments never change,
  and the Today page shows a footnote with what was filtered so nothing disappears silently.
- **`det_thresh`** — the face detector's own threshold (factory value 0.40, the same value the
  live watchers use; allowed 0.3 to 0.7), made visible and configurable. Raising it is *not*
  recommended: 0.60 already costs ~16% of real faces. It is also the bar of the second look for
  unknown faces (see [live-watchers.md](live-watchers.md), step 4).
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
  **Test** button per channel (see [usage.md](usage.md)). Pushover counts as **off** while the
  token or the user key is missing (one line in the startup log, nothing is sent). If Pushover
  rejects 5 messages in a row (wrong token/user), the channel **pauses** until you save the
  Notifications tab or a Test succeeds; the tab shows the state, `/health` carries it under
  `system.rueckstau.pushover_*`. Network errors never pause the channel.
- **Recognition threshold** — the time-window criterion (how many consistent frames within the
  window count as "recognized"). The defaults are calibrated; change only if you know why.
  The same similarity threshold also drives the live watchers' preliminary name stage.
- **Recognition chain** — its own page in the **Configuration** menu: the order face → person → vision with a
  plain-language condition per step (always / only when the face path could not confirm
  everyone / off). The vision step is parked and does not run (see
  [person-recognition.md](person-recognition.md)).
- **Body images and person recognition** — see [person-recognition.md](person-recognition.md) for how the
  path works. **`person_pfad`** (`immer` = always, the default \| `nur_wenn_gesicht_leer` = only when the
  face path could not confirm everyone on the walk-through; when a video shows several people, an event whose
  tracked person got no face name is always checked \| `aus` = off; a fresh install starts with `aus`):
  an event whose tracked person got no face name gets a body name when a body picture cut
  from its video is close enough to a valid image on the **Body images** page. It needs at least one valid
  image there. By default the name is only shown. Four switches, all off by default, let it report:
  **`koerper_meldet_frigate`** (sub label in Frigate, needs `sub_label_schreiben`),
  **`koerper_meldet_pushover`**, **`koerper_meldet_telegram`** and **`koerper_meldet_ha`** (MQTT topic
  `koerper_erkannt`), each only with its channel set up, once per walk-through and person. A fifth switch,
  **`koerper_meldet_anwesenheit`** (off by default), sends nothing outside (unlike `anwesenheit_push`): it
  writes presence marks for the events the body name counts for, shown on the **Presence** page and in the
  hour bar on **Today** as their own state *via person recognition*; red stays confirmed by face or live
  watcher. They are on the
  **Recognition** page (body card) and also on the **Advanced** settings page. The
  nine settings of the path, all on the **Advanced** settings page (`koerper_lauf` and `koerper_sichtpruefung`
  also on the body card of the **Recognition** page); none of the defaults is measured on more than one system:

  | Key | Default | Allowed | What it does |
  |---|---|---|---|
  | `koerper_auswahl_stimmen` | 6 | 1 to 20 | votes the recognized person needs before the video of an event counts as suitable for body images |
  | `koerper_bilder_je_video` | 3 | 1 to 10 | body images the cutter keeps from one video at most, spread over the time the person was seen |
  | `koerper_anker_min` | 0.5 | 0 to 1 | how close at least one cut picture must be to the person picture of the recognized face in the same event; below that, all pictures of the video are dropped |
  | `koerper_sichtpruefung` | on | on / off | new body images wait for your check on the Body images page; off: they count at once (on the body card of the **Recognition** page the switch **Accept new images automatically**, the other way round; images already waiting stay until you decide) |
  | `koerper_lauf` | `hand` | `hand` / `taeglich` / `sofort` | when the person learning run starts: `hand` = only by the button on the Body images page; `taeglich` = once a day with the daily maintenance at 06:00 (not at service start), over all suitable videos still waiting; `sofort` = right after each suitable event, one cut per event at the same time as the analysis of the next events, in the separate body process (on a CPU installation it shares the cores with the analysis) |
  | `koerper_max_tage` | 10 | 1 to 30 | days a body image is kept; older ones go to the trash in the daily data cleanup |
  | `koerper_max_je_person` | 50 | 5 to 200 | body images one person may have at most; the oldest go to the trash first |
  | `koerper_schwelle` | 0.65 | 0 to 0.99 | the threshold for a body name, the same for every person; a person whose valid images reach it against the valid images of another person is switched off for recognition (no body name, its images are still learned); a higher value switches it back on and is stricter for everyone; 0 switches off almost every person |
  | `koerper_stimmen` | 3 | 1 to 10 | body votes one walk-through must give the same person before the name counts; a vote is one query picture of an event over the threshold, only events whose tracked person got no face name give votes, the votes of all events add up; the name also counts when a face on the walk-through names another person |

  Two more settings belong to the body process: **`personwork_rss_max_mb`** (default 3072) is its memory
  limit, large events are thinned out instead of running out of memory; **`person_backend`** (default `cpu`)
  places the body fingerprint on another device (`openvino:GPU`, `openvino:NPU`, `cuda`, `migraphx`, each
  only in the matching image), with a loud fallback to the CPU.
- **Live watchers** — configured per camera on the **Live** tab, not in the wizard:
  source (`proxy` / `direct` / `url`), processing resolution (360p, 720p or 1080p,
  default 1080p), the two times (appearance end, re-arm), and the notification channels per
  watcher. See [live-watchers.md](live-watchers.md).
- **Service log on disk** (`log_datei`, `log_behalten_tage`, `log_max_mb`) — the service, the
  analysis worker and the live-watcher engine all log through one module, and suslik writes the
  result to `<data_dir>/logs/suslik.log`, so the log survives restarts and stays readable without
  shell access to the container. Every line has the same form: date, time with milliseconds and
  time zone, the level, the source as `process/module:function`, then ` | ` and the text;
  continuation lines of a multi-line entry (a traceback) repeat the head and use ` +| ` instead.
  The levels are Python's standard five (DEBUG, INFO, WARNING, ERROR, CRITICAL); by default the log
  shows INFO and above. The `debug` setting adds the DEBUG lines: it takes effect at once, without a
  restart, and is off again after every restart. The file is rotated on every service start, at
  midnight and when it passes `log_max_mb` (default 64); older pieces are gzipped and deleted after
  `log_behalten_tage` days (default 14). Read it at `/log` (the last 5000 lines; add `?lines=20000`
  for more, the ceiling is 200000), or download every piece at once from
  `/log/suslik-logs.tar.gz` — that archive is the file to attach when you report a problem.
  `/health` carries a `log` block: per process (`dienst`, `worker`, `live`) the number of WARNING,
  ERROR and CRITICAL entries since the service started, `fremd_n` for lines without the head
  (native library output, crash messages), `letzte_error` with time, source and text of the latest
  ERROR or CRITICAL line, and next to them the state of the log writer and the switches. Set
  `log_datei: false` to write no file; `/log` then shows the service's last 300 lines from memory.
- **Check log** (`pruef_log`, `pruef_takt_s`) — off by default. When on, suslik confirms its own
  state at a fixed interval in a second file, `<data_dir>/logs/pruef.log`: compute threads alive
  against the configured number, the backend and the device that really computes, events accepted
  and booked, time per event, the health counters and the live watchers. Every WARNING, ERROR and
  CRITICAL line of all processes is copied there as well, so the file is complete on its own; the
  confirmation lines themselves stay out of `suslik.log` (they do show in `docker logs`).
  `pruef_takt_s` is the interval in seconds (default 30, allowed 10–3600). Switch it on the
  **Advanced** settings page, or through the API with `POST /konfig` and a JSON body such as
  `{"pruef_log": true}`: it takes effect at once, without a restart, and stays on after a restart
  until you switch it off. `pruef.log` rotates like `suslik.log` and is part of
  `/log/suslik-logs.tar.gz` and of the support area `/support/logs`.

## Environment variables

Set these on the container (compose `environment:` / `env_file:`, or `docker run -e`):

| Variable | Purpose |
|---|---|
| `TZ` | container timezone (e.g. `Europe/Berlin`). Without it suslik uses the `zeitzone` setting, and `Europe/Berlin` if that is empty. |
| `FRIGATE_URL` | pre-fill the Frigate URL in the wizard (optional) |
| `SUSLIK_HWDEC` | hardware video decode for analysis frames: `auto` (default — uses the Intel iGPU via VAAPI or an NVIDIA GPU via NVDEC when the image ships a validated driver and the device is passed through; 8-bit 4:2:0 material only), `vaapi` / `nvdec` (force one source), `aus` (always software). Decoded pixels are bit-identical either way; if the hardware path fails, the software decoder takes over and the event is flagged. |
| `HA_URL`, `HA_TOKEN` | only for Telegram through Home Assistant (`telegram_modus` `ha` or `beide`): the address of your Home Assistant and a long-lived access token. All other channel secrets are entered on the **Notifications** page and stored in `/data`, never baked into the image. |

The service passes the chosen backend to all its sub-processes, so the one `backend` setting
controls face recognition everywhere; body recognition has its own setting, `person_backend`
(default `cpu`).

## Configuration backup & restore

The **System** page has a **Configuration backup** card:

- **Download configuration** saves all settings (thresholds, cameras, notification channels
  including their stored secrets) as one JSON file.
- **Restore from file…** loads such a file back — the previous settings are kept as a `.bak`
  next to the store, then the service restarts. The setup wizard can consume the same file via
  **"Already have a configuration?"**.

This covers **settings only**. Your learned people and reference faces are in the **Full backup**
(see *Where configuration lives* above).

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
