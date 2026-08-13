"""routes/system — System-Seite: Ampel, Drift-Banner, Write-back-, Sync-, QC-,
Backup-, Tools-/Docs-Karten (Modulumbau R1, byte-treu aus verifyd extrahiert).
BEWUSSTE Ausnahme vom reinen Daten-Parameter-Muster: die Seite zeigt die
Dienst-LAGE (log_path, processed, pub, letzter_hb, frigate_fehler, _nachhol_stat,
enroll_warnung) — der Handler injiziert deshalb das Service-OBJEKT (modulplan
§2c: Objekt-Injektion, nie Rueckimport; die Attr-Familie ist die in §2a
kartierte). Dazu ro=frigate_read_only(cfg) und docs_url — beide Quellen bleiben
im Kern. Die sync-Imports stehen IN der try wie im Original: ein Importfehler
gehoert dort zur Karten-Semantik (Fallback-Karte statt Seitenkiller)."""
import datetime
import html
import json
import os
import shutil
import time

from core import registry as _reg


def render(svc, cfg, ro, docs_url):
    """-> Seiten-INHALT (layout/banner bleiben beim Handler)."""
    # Ampel mit DEFINIERTEN Messungen (Plan AP5 — kein Latenz-Raten)
    letzte = None
    if os.path.exists(svc.log_path):
        with open(svc.log_path) as f:
            for l in f:
                try:
                    d = json.loads(l)
                    if d.get("nachhol"):
                        continue     # Retry misst einen Batch-Job, nicht den Live-Pfad
                    letzte = d
                except Exception:
                    pass
    frei_gb = shutil.disk_usage(cfg["data_dir"]).free / 1e9
    mq_ok = bool(svc.pub and svc.pub.is_connected())
    hb_alter = time.time() - getattr(svc, "letzter_hb", 0)
    ff = svc.frigate_fehler
    _url_da = bool((cfg.get("frigate_url") or "").strip())
    ampel = [
        ("Service", True, f"processed (session): {len(svc.processed)}"),
        # Erstlauf: "noch nie analysiert" ist KEIN Fehler — vorher stand hier eine
        # rote Lampe mit "last duration — s", bevor je ein Event kam (Plan-QS P.6).
        ("Analysis", (letzte is None) or (letzte.get('dauer_s') or 0) < 90,
         f"last duration {letzte.get('dauer_s')} s" if letzte else "no analysis yet"),
        # bewusst IMMER gruen: eine dauerhaft rote Lampe fuer aufgegebene Alt-Events
        # erzeugt nur Alarmmuedigkeit. Reine Bestandsanzeige.
        ("Retry queue", True,
         "{} open / {} given up (window {} d)".format(
             *getattr(svc, "_nachhol_stat", (0, 0)), cfg["nachhol_tage"])),
        # Ohne konfigurierte URL stand hier "reachable OK" — eine Erreichbarkeits-
        # aussage ueber etwas, das nie kontaktiert wurde.
        ("Frigate",
         _url_da and not (ff and time.time() - ff[0] < 600),
         ("not configured yet — set the URL in the setup wizard" if not _url_da else
          ("reachable" if not ff else
           f"last error {datetime.datetime.fromtimestamp(ff[0]):%H:%M}"))),
        # heartbeat-Alter gegen Epoche 0 gerechnet ergab "heartbeat 1784986e9 s ago".
        # Issue #10 (Tokn59, 27.07., gefixt .173): "not configured" stand frueher
        # fuer DREI verschiedene Lagen (kein Broker / Broker da + publishing aus /
        # Broker da + Publisher-Start gescheitert) — die dritte ist ein Fehler und
        # war als OK getarnt. Jetzt: eigene Texte je Lage, und die Lampe ist nur
        # noch dann gruen ohne Publisher, wenn das BEWUSST so ist (aus/kein Broker).
        ("MQTT", mq_ok or (not getattr(svc, "pub", None)
                           and (not cfg.get("mqtt_publish", True)
                                or not (cfg.get("mqtt") or {}).get("host"))),
         (f"heartbeat {hb_alter:.0f} s ago" if getattr(svc, "letzter_hb", 0) else
          ("no heartbeat yet" if getattr(svc, "pub", None) else
           ("configured, publishing off" if (cfg.get("mqtt") or {}).get("host")
            and not cfg.get("mqtt_publish", True) else
            ("configured, publisher not started — see service log"
             if (cfg.get("mqtt") or {}).get("host") else "not configured"))))),
        ("Disk", frei_gb > 20, f"{frei_gb:.0f} GB free"),
    ]
    a_teile = []
    for name, ok, info in ampel:
        farbe = "var(--ok)" if ok else "var(--crit)"   # Tokens statt Hex: Hellmodus-Kontrast (Vor-Release-Pruefung B12)
        wort = "OK" if ok else "CHECK"
        a_teile.append(f'<div class="zaehler"><b style="color:{farbe}">{wort}</b>'
                       f'{name}<br><small>{html.escape(str(info))}</small></div>')
    a_html = "".join(a_teile)
    drift = ""
    w = svc.enroll_warnung                   # s. Enroll-Seite: einmal binden (TOCTOU)
    if w and time.time() - w[0] < 86400:
        drift = ('<div class="banner">DRIFT GUARD RED after the last reference add:'
                 f"<pre style='white-space:pre-wrap'>{html.escape(w[1])}</pre></div>")
    sync_html = ""
    try:
        # .137: die System-Karte ist nur noch eine STATUSZEILE + Weg zur
        # Seite (eigener Nav-Punkt "Frigate sync"). Alles Bedienbare —
        # Auswahl, Transfer, Import, Entscheidungsfaelle — liegt dort,
        # damit es nicht zwei halbe Sync-Oberflaechen gibt.
        from sync_refs import abgleich as sync_abgleich
        # .138 Panel-Fix: die Zahlenzeile kommt aus DERSELBEN
        # Funktion wie auf der Sync-Seite (bilanz_zeile) — vorher
        # rechnete die Karte 'ready to transfer' selbst und ohne
        # die gemerkten Frigate-Ablehnungen: zwei Seiten, gleiche
        # Beschriftung, verschiedene Zahlen.
        from routes.syncauswahl import bilanz_zeile as sync_bilanz_zeile
        _ab = sync_abgleich()
        sync_html = ('<div class="card"><b>Sync with Frigate</b>'
                     + sync_bilanz_zeile(_ab, _ab.get("abgelehnt"),
                                         mit_personen=False)
                     + '<div style="margin-top:8px">'
                     '<a class="gtb on" href="/sync_auswahl">'
                     'Open Frigate sync</a></div>'
                     '<small>The sync page compares both libraries class by class, '
                     'pre-checks every candidate the way Frigate does, sends only what '
                     'you tick, and imports what only Frigate has. '
                     'If a sync reports a problem, <a href="/sync_diagnose" target="_blank">'
                     'open the diagnosis</a> — it bundles the suslik report and the Frigate '
                     'log, ready to copy into an issue.</small></div>')
    except Exception as e:
        # Roher Python-Fehler stand hier direkt in der Karte (Plan-QS P.6) — fuer
        # den haeufigsten Fall (frisches System ohne Frigate/Referenzen) jetzt ein Satz.
        sync_html = ('<div class="card"><b>Sync with Frigate</b><br>'
                     '<span class="dim">not available yet — needs a reachable Frigate '
                     'and at least one reference face</span>'
                     f'<br><small class="dim">({html.escape(str(e)[:60])})</small>'
                     '<br><small><a href="/sync_diagnose" target="_blank">open the '
                     'diagnosis</a> — bundles the suslik report and the Frigate log.'
                     '</small></div>')
    qs_html = ""
    qp = os.path.join(cfg["data_dir"], "state", "qs_bericht.json")
    if os.path.exists(qp):
        try:
            q = json.load(open(qp))
            zeilen = "".join(
                f"<tr><td>{html.escape(k)}</td><td>{v['events']}</td><td>{v['mit_gesicht']}</td>"
                f"<td>{v['bestaetigt']}</td><td>{v['fenster_quote']} %</td></tr>"
                for k, v in sorted(q.get("kameras", {}).items()))
            qs_html = (f'<div class="card"><b>QC report</b> (as of {html.escape(q.get("stand", "?"))}, '
                       f'{q.get("zeitraum_tage", "?")} days)'
                       '<div class="tabelle-wrap"><table><tr><th>Camera</th><th>Events</th>'
                       "<th>with face</th><th>confirmed</th><th>window rate</th></tr>"
                       + zeilen + "</table></div></div>")
        except Exception:
            pass
    backup_html = (
        '<div class="card"><b>Configuration backup</b>'
        '<p class="dim">Download the settings stored in /data/config as one JSON file, or restore '
        'them from such a file. Honest scope: today that is the CAMERA SHEET (incl. its '
        'stored values); thresholds/channels set only in verifyd.yaml or via environment '
        'are NOT in this file. Learned people/references: use the full backup below.</p>'
        '<a class="gtb on" href="/config_sichern">Download configuration</a> '
        '<label class="gtb" style="cursor:pointer">Restore from file…'
        '<input type="file" accept="application/json,.json" style="display:none" '
        'onchange="configRestore(this)"></label> '
        '<span id="restore-status" class="dim"></span>'
        # E8 (konzept_vision.md §9): der Vision-API-Key faehrt wie die anderen
        # Meldekanal-Secrets MIT, damit ein Umzug ihn nicht still verliert. Das
        # ist ein Preis, also steht er hier — nicht in einer Fussnote. Text aus
        # der zentralen Quelle, kein zweites Literal.
        f'<p class="dim"><b>Careful:</b> this file {_reg.VISION_EXPORT_HINWEIS} '
        '(notification channels and vision detect), so that a restore on another '
        'machine really works.</p>'
        '<p class="dim">Restore overwrites the current settings (the previous ones are kept '
        'as a .bak) and restarts the service.</p></div>'
        '<div class="card"><b>Full backup</b>'
        '<p class="dim">One portable archive with everything you taught this '
        'installation: settings, the face reference library, learning-run '
        'results, the whole person-recognition material (images, your review '
        'verdicts, trained models) and the event record. Made for moving to '
        'another machine. Honest scope: the video clip cache and per-event '
        'analysis artifacts are NOT included — they are rebuilt over time.</p>'
        '<a class="gtb on" href="/backup_voll">Download full backup</a> '
        '<label class="gtb" style="cursor:pointer">Restore full backup…'
        '<input type="file" accept=".tar.gz,application/gzip" style="display:none" '
        'onchange="vollRestore(this)"></label> '
        '<span id="vollrestore-status" class="dim"></span>'
        f'<p class="dim"><b>Careful:</b> this archive {_reg.VISION_EXPORT_HINWEIS}.</p>'
        '<p class="dim">Restore replaces those parts (each previous one is kept '
        'once as *.pre-restore-*) and restarts the service. Uploading a few '
        'hundred MB can take a while — leave the page open.</p></div>')
    # Live-Waechter-Karte (Phase 4 Baustein B, Sichtkontrolle .177 Befund 3):
    # dieselbe EINE Protokoll-Quelle wie die Today-Zeile (livewache.melde_
    # zaehler) + Supervisor-Lage (live_aufsicht_status — auch "standalone
    # engine detected"). Karte nur, wenn Live benutzt wird; Fehler hier sind
    # Karten-Semantik (weglassen), nie Seitenkiller — Muster Sync-Karte.
    live_html = ""
    try:
        from core import livewache as _lw
        if ((cfg.get("live") or {}).get("guards")
                or _lw.melde_protokoll_vorhanden(cfg)):
            _h0 = datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0).timestamp()
            _z = _lw.melde_zaehler(cfg, _h0, time.time())
            _alerts = " · ".join(
                f"{k} {_z.get(('alert', k), 0)}"
                for k in ("pushover", "telegram", "mqtt"))
            _stoer = sum(n for (art, _k), n in _z.items() if art == "stoerung")
            _aufsicht = svc.live_aufsicht_status()
            live_html = (
                '<div class="card"><b>Live watchers</b>'
                f'<div><small>{html.escape(str(_aufsicht.get("text") or ""))}'
                '</small></div>'
                f'<div>Alerts sent today: {html.escape(_alerts)}</div>'
                f'<div>Disturbance notices today: {_stoer}</div>'
                '<div style="margin-top:8px"><a class="gtb on" href="/live">'
                'Open Live watchers</a></div>'
                '<small class="dim">Counted from the engine\'s own message '
                'log — only messages that were really accepted by a channel. '
                'Live watcher alerts are separate from the event-analysis '
                'alert counters on the Today page.</small></div>')
    except Exception:
        live_html = ""
    fsync = bool(cfg.get("frigate_sync"))
    _rc = "var(--ok)" if ro else "var(--warn)"   # read-only = gruen/sicher, schreibend = Achtung; Tokens statt Hex (B12: 2,45/2,94 im Hellmodus)
    write_html = (
        f'<div class="card" style="border-left:4px solid {_rc}"><b>Frigate write-back</b>'
        '<p class="dim">Does suslik write back to Frigate, or only read? Read-only is the safe '
        'default; enable writing only for parallel operation (Frigate-Face + suslik).</p>'
        f'<div>Current: <b style="color:{_rc}">'
        + ('READ-ONLY — suslik does not write to Frigate' if ro
           else 'WRITING to Frigate — sub_labels' + (' + reference sync' if fsync else '')) + '</b></div>'
        '<div style="margin-top:8px">'
        # Auswahl farbNEUTRAL markieren (.sel statt .on): .on ist gruen, und gruen heisst
        # auf dieser Karte sonst "sicher". Bei aktivem Schreiben stand deshalb ein gruener
        # Knopf neben dem orangen Warnrahmen — zwei Signale, die sich widersprachen. Der
        # Haken sagt, was gilt, auch ohne Farbe.
        f'<button class="gtb{"" if ro else " sel"}" onclick="frigateWrite(false)">'
        + ("" if ro else "✓ ") + 'Enable writing</button> '
        f'<button class="gtb{" sel" if ro else ""}" onclick="frigateWrite(true)">'
        + ("✓ " if ro else "") + 'Read-only</button> '
        '<span id="fw-status" class="dim"></span></div></div>')
    inhalt = ("<h2>System</h2>"
              f'<div class="zeile">{a_html}</div>' + drift + live_html + write_html + sync_html + qs_html + backup_html +
              '<div class="card"><b>Tools</b><br>'
              '<a href="/log">Service log</a> · <a href="/health">health</a></div>'
              '<div class="card"><b>Docs</b><br>'
              f'<a href="{docs_url}" target="_blank" rel="noopener noreferrer">'
              'Documentation on GitHub</a></div>')
    return inhalt
