"""routes/system — System-Seite: Ampel, Drift-Banner, Write-back-, Sync-, QC-,
Backup-, Tools-/Docs-Karten (Modulumbau R1, byte-treu aus verifyd extrahiert).
BEWUSSTE Ausnahme vom reinen Daten-Parameter-Muster: die Seite zeigt die
Dienst-LAGE (log_path, processed, pub, letzter_hb, frigate_fehler, _nachhol_stat,
enroll_warnung) — der Handler injiziert deshalb das Service-OBJEKT (modulplan
§2c: Objekt-Injektion, nie Rueckimport; die Attr-Familie ist die in §2a
kartierte). Dazu ro=frigate_read_only(cfg) und docs_url — beide Quellen bleiben
im Kern. Die sync-Imports stehen IN der try wie im Original: ein Importfehler
gehoert dort zur Karten-Semantik (Fallback-Karte statt Seitenkiller).
Sprach-Stufe 2 (Tranche C, konzept_sprache.md v2): sichtbare Texte aus
core/sprache.t() — BYTE-TREU (Harnisch tools/harnisch_sprache.py). Die zwei
Diagnose-Saetze der Sync-Karte (<a>-Links mitten im Satz) sind seit Stufe 3
t_html-Schluessel (system.sync.diagnose_*). Verbleibende Grenzen: "health"
ist Anzeige==Endpunkt-Name (§8.2); "Frigate"/"MQTT" sind Produkt-/
Protokollnamen (§8.6); die Datumsformate %H:%M bleiben in der Route (B19)."""
import datetime
import html
import json
import os
import shutil
import time

from core.sprache import t, t_html


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
    cache_gb, frei_gb = svc.cache_stand()      # .313: EINE Quelle (auch Knopf/Wache)
    # .32x: die WIRKSAMEN Grenzen, nicht die rohen Config-Zahlen. Seit 0 fuer
    # "aus der Plattengroesse ableiten" steht, ist der rohe Wert als Anzeige
    # sinnlos ("Clip-Cache 22,6 GB von 0 GB", Fund am laufenden Prod 22.08.) und als
    # Ampel-Schwelle sogar falsch: die Ampel blieb bis 10 GB gruen, waehrend
    # die Wache schon bei 74 GB raeumt. Dieselbe Quelle wie cleanup_cache.
    _cap_gb, _frei_min_gb, _grenz_quelle = svc.speichergrenzen()
    mq_ok = bool(svc.pub and svc.pub.is_connected())
    hb_alter = time.time() - getattr(svc, "letzter_hb", 0)
    ff = svc.frigate_fehler
    _url_da = bool((cfg.get("frigate_url") or "").strip())
    # .200 (Fix 4): der Setup-Wizard verspricht seit jeher "whether the accelerator
    # really engages is confirmed live on the System page" — die Lampe gab es nie.
    # Quelle = dieselben Felder wie /health (placement_info/backend + Selbstcheck-
    # Fails), die Anzeige kann dem Selbstcheck nicht widersprechen (K1).
    _pi = cfg.get("placement_info") or {}
    _bk = _pi.get("backend") or cfg.get("backend") or cfg.get("ov_device") or "?"
    _sf = getattr(svc, "startup_fails", 0)
    _nh = getattr(svc, "_nachhol_stat", (0, 0))
    ampel = [
        (t("system.ampel.service"), True,
         t("system.ampel.service_info", n=len(svc.processed))),
        (t("system.ampel.backend"), _sf == 0,
         t("system.ampel.backend_ok", backend=_bk) if _sf == 0 else
         t("system.ampel.backend_fail", backend=_bk, n=_sf)),
        # Erstlauf: "noch nie analysiert" ist KEIN Fehler — vorher stand hier eine
        # rote Lampe mit "last duration — s", bevor je ein Event kam (Plan-QS P.6).
        (t("system.ampel.analyse"), (letzte is None) or (letzte.get('dauer_s') or 0) < 90,
         t("system.ampel.analyse_dauer", s=letzte.get('dauer_s')) if letzte
         else t("system.ampel.analyse_nie")),
        # bewusst IMMER gruen: eine dauerhaft rote Lampe fuer aufgegebene Alt-Events
        # erzeugt nur Alarmmuedigkeit. Reine Bestandsanzeige.
        (t("system.ampel.retry"), True,
         t("system.ampel.retry_info", offen=_nh[0], aufgegeben=_nh[1],
           tage=cfg["nachhol_tage"])),
        # Ohne konfigurierte URL stand hier "reachable OK" — eine Erreichbarkeits-
        # aussage ueber etwas, das nie kontaktiert wurde. "Frigate" ist
        # Produktname (§8.6, bleibt literal); %H:%M bleibt in der Route (B19).
        ("Frigate",
         _url_da and not (ff and time.time() - ff[0] < 600),
         (t("system.ampel.frigate_unkonfiguriert") if not _url_da else
          (t("system.ampel.frigate_ok") if not ff else
           t("system.ampel.frigate_fehler",
             zeit=f"{datetime.datetime.fromtimestamp(ff[0]):%H:%M}")))),
        # heartbeat-Alter gegen Epoche 0 gerechnet ergab "heartbeat 1784986e9 s ago".
        # Issue #10 (Tokn59, 27.07., gefixt .173): "not configured" stand frueher
        # fuer DREI verschiedene Lagen (kein Broker / Broker da + publishing aus /
        # Broker da + Publisher-Start gescheitert) — die dritte ist ein Fehler und
        # war als OK getarnt. Jetzt: eigene Texte je Lage, und die Lampe ist nur
        # noch dann gruen ohne Publisher, wenn das BEWUSST so ist (aus/kein Broker).
        # "MQTT" ist Protokollname (§8.6, bleibt literal); {s} vorformatiert (§8.8).
        ("MQTT", mq_ok or (not getattr(svc, "pub", None)
                           and (not cfg.get("mqtt_publish", True)
                                or not (cfg.get("mqtt") or {}).get("host"))),
         (t("system.ampel.mqtt_hb", s=f"{hb_alter:.0f}") if getattr(svc, "letzter_hb", 0) else
          (t("system.ampel.mqtt_kein_hb") if getattr(svc, "pub", None) else
           (t("system.ampel.mqtt_pub_aus") if (cfg.get("mqtt") or {}).get("host")
            and not cfg.get("mqtt_publish", True) else
            (t("system.ampel.mqtt_pub_kaputt")
             if (cfg.get("mqtt") or {}).get("host")
             else t("system.ampel.mqtt_unkonfiguriert")))))),
        # .313 (Issue #25): Schwelle = Mindestfrei der Platten-Wache (dieselbe Zahl, die das
        # Aufraeumen ausloest), Text traegt Cache-Groesse gegen Deckel.
        (t("system.ampel.disk"), frei_gb > _frei_min_gb and not svc.disk_warnung,
         t("system.ampel.disk_info2", gb=f"{frei_gb:.0f}", cache=f"{cache_gb:.1f}",
           max=f"{_cap_gb:.0f}")),
    ]
    a_teile = []
    for name, ok, info in ampel:
        farbe = "var(--ok)" if ok else "var(--crit)"   # Tokens statt Hex: Hellmodus-Kontrast (Vor-Release-Pruefung B12)
        wort = t("system.ampel.ok") if ok else t("system.ampel.check")
        a_teile.append(f'<div class="zaehler"><b style="color:{farbe}">{wort}</b>'
                       f'{name}<br><small>{html.escape(str(info))}</small></div>')
    a_html = "".join(a_teile)
    # .313 (Issue #25): Aufraeum-Knopf + Warnung, wenn der Clip-Cache allein nicht reicht.
    a_html += (f'<div class="card" style="margin-top:8px"><b>{t("system.disk.titel")}</b> '
               f'<span class="dim">{t("system.disk.satz", tage=cfg.get("clip_retention_d"), max=f"{_cap_gb:.0f}", min=f"{_frei_min_gb:.0f}")}</span> '
               f'<button class="gtb" onclick="cacheAufraeumen(this)">{t("system.disk.knopf")}</button> '
               f'<span class="dim" id="disk-msg"></span>'
               + (f'<div class="banner" style="margin-top:6px">{t("system.disk.warnung", gb=svc.disk_warnung[1])}</div>'
                  if svc.disk_warnung else "") + '</div>')
    drift = ""
    w = svc.enroll_warnung                   # s. Enroll-Seite: einmal binden (TOCTOU)
    if w and time.time() - w[0] < 86400:
        drift = (f'<div class="banner">{t("system.drift.banner")}'
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
        sync_html = (f'<div class="card"><b>{t("system.sync.titel")}</b>'
                     + sync_bilanz_zeile(_ab, _ab.get("abgelehnt"),
                                         mit_personen=False)
                     + '<div style="margin-top:8px">'
                     '<a class="gtb on" href="/sync_auswahl">'
                     f'{t("system.sync.knopf")}</a></div>'
                     f'<small>{t("system.sync.satz")} '
                     # Stufe 3 (t_html): Diagnose-Satz mit <a>-Link — der
                     # statische href liegt im Wert (Tag-Folge gepinnt).
                     f'{t_html("system.sync.diagnose_satz")}</small></div>')
    except Exception as e:
        # Roher Python-Fehler stand hier direkt in der Karte (Plan-QS P.6) — fuer
        # den haeufigsten Fall (frisches System ohne Frigate/Referenzen) jetzt ein Satz.
        sync_html = (f'<div class="card"><b>{t("system.sync.titel")}</b><br>'
                     f'<span class="dim">{t("system.sync.fehlt")}</span>'
                     f'<br><small class="dim">({html.escape(str(e)[:60])})</small>'
                     # Stufe 3 (t_html): Kurz-Diagnose-Satz mit <a>-Link.
                     f'<br><small>{t_html("system.sync.diagnose_kurz")}'
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
            # Kopfzellen: "Camera"/"Events" wiederverwendet (byte-identisch zu
            # ereignisliste.tabelle.kopf_kamera / ereignisliste.titel).
            qs_html = (f'<div class="card"><b>{t("system.qc.titel")}</b> '
                       f'{t("system.qc.stand", stand=html.escape(q.get("stand", "?")), tage=q.get("zeitraum_tage", "?"))}'
                       f'<div class="tabelle-wrap"><table><tr><th>{t("ereignisliste.tabelle.kopf_kamera")}</th>'
                       f'<th>{t("ereignisliste.titel")}</th>'
                       f"<th>{t('system.qc.kopf_gesicht')}</th><th>{t('system.qc.kopf_bestaetigt')}</th>"
                       f"<th>{t('system.qc.kopf_quote')}</th></tr>"
                       + zeilen + "</table></div></div>")
        except Exception:
            pass
    # Der Abschnittstitel "Configuration backup" wird von setupwiz.restore.satz
    # aller fuenf Sprachen woertlich englisch zitiert — der Einzug hier macht
    # ihn uebersetzbar; die Zitate (und der "(page System)"-Wegweiser) muessen
    # in der Uebersetzungsrunde nachgezogen werden (Folge-Aufgabe Tranche C).
    backup_html = (
        f'<div class="card"><b>{t("system.backup.titel")}</b>'
        f'<p class="dim">{t("system.backup.satz")}</p>'
        f'<a class="gtb on" href="/config_sichern">{t("system.backup.knopf_download")}</a> '
        f'<label class="gtb" style="cursor:pointer">{t("system.backup.knopf_restore")}'
        '<input type="file" accept="application/json,.json" style="display:none" '
        'onchange="configRestore(this)"></label> '
        '<span id="restore-status" class="dim"></span>'
        # E8 (konzept_vision.md §9): der Vision-API-Key faehrt wie die anderen
        # Meldekanal-Secrets MIT, damit ein Umzug ihn nicht still verliert. Das
        # ist ein Preis, also steht er hier — nicht in einer Fussnote. Der
        # fette Vorsatz "Careful:" ist ein abgeschlossener Einleitungs-Baustein
        # (Split an der Markup-Grenze, Muster §8.10/unbekannte.kopf_satz).
        # Tranche D (3a): {hinweis} kommt uebersetzbar aus dem Schluessel;
        # die EN-Referenz bleibt die zentrale Quelle _reg.VISION_EXPORT_HINWEIS
        # (Gate prueft Wortgleichheit en.T == Konstante — kein Zweit-Literal).
        f'<p class="dim"><b>{t("system.backup.careful")}</b> '
        f'{t("system.backup.careful_config", hinweis=t("system.backup.hinweis"))}</p>'
        f'<p class="dim">{t("system.backup.restore_satz")}</p></div>'
        f'<div class="card"><b>{t("system.voll.titel")}</b>'
        f'<p class="dim">{t("system.voll.satz")}</p>'
        f'<a class="gtb on" href="/backup_voll">{t("system.voll.knopf_download")}</a> '
        f'<label class="gtb" style="cursor:pointer">{t("system.voll.knopf_restore")}'
        '<input type="file" accept=".tar.gz,application/gzip" style="display:none" '
        'onchange="vollRestore(this)"></label> '
        '<span id="vollrestore-status" class="dim"></span>'
        f'<p class="dim"><b>{t("system.backup.careful")}</b> '
        f'{t("system.voll.careful", hinweis=t("system.backup.hinweis"))}</p>'
        f'<p class="dim">{t("system.voll.restore_satz")}</p></div>')
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
                f'<div class="card"><b>{t("system.live.titel")}</b>'
                f'<div><small>{html.escape(str(_aufsicht.get("text") or ""))}'
                '</small></div>'
                f'<div>{t("system.live.alerts", kanaele=html.escape(_alerts))}</div>'
                f'<div>{t("system.live.stoerungen", n=_stoer)}</div>'
                '<div style="margin-top:8px"><a class="gtb on" href="/live">'
                f'{t("system.live.knopf")}</a></div>'
                f'<small class="dim">{t("system.live.quelle")}</small></div>')
    except Exception:
        live_html = ""
    fsync = bool(cfg.get("frigate_sync"))
    _rc = "var(--ok)" if ro else "var(--warn)"   # read-only = gruen/sicher, schreibend = Achtung; Tokens statt Hex (B12: 2,45/2,94 im Hellmodus)
    # Zustandszeile: der Sync-Zusatz ist ein abgeschlossener konditionaler
    # Anhang (§8.11 — eigener Schluessel statt 2^n Ganz-Satz-Varianten).
    write_html = (
        f'<div class="card" style="border-left:4px solid {_rc}"><b>{t("system.write.titel")}</b>'
        f'<p class="dim">{t("system.write.satz")}</p>'
        f'<div>{t("system.write.aktuell")} <b style="color:{_rc}">'
        + (t("system.write.zustand_ro") if ro
           else t("system.write.zustand_rw")
           + (t("system.write.zustand_rw_sync") if fsync else '')) + '</b></div>'
        '<div style="margin-top:8px">'
        # Auswahl farbNEUTRAL markieren (.sel statt .on): .on ist gruen, und gruen heisst
        # auf dieser Karte sonst "sicher". Bei aktivem Schreiben stand deshalb ein gruener
        # Knopf neben dem orangen Warnrahmen — zwei Signale, die sich widersprachen. Der
        # Haken sagt, was gilt, auch ohne Farbe.
        f'<button class="gtb{"" if ro else " sel"}" onclick="frigateWrite(false)">'
        + ("" if ro else "✓ ") + f'{t("system.write.knopf_rw")}</button> '
        f'<button class="gtb{" sel" if ro else ""}" onclick="frigateWrite(true)">'
        + ("✓ " if ro else "") + f'{t("system.write.knopf_ro")}</button> '
        '<span id="fw-status" class="dim"></span></div></div>')
    inhalt = (f"<h2>{t('system.titel')}</h2>"
              f'<div class="zeile">{a_html}</div>' + drift + live_html + write_html + sync_html + qs_html + backup_html +
              # .200 (Fix 4): der Abschluss-Text des Wizards verweist auf
              # "System → Re-run setup wizard" — den Link gab es hier nie
              # (nur auf Advanced). Jetzt steht er da, der Text stimmt.
              # Wiederverwendet: ui.fuss.log ("Service log") und
              # konfiguration.knopf_setup ("Re-run setup wizard") — beide
              # byte-identisch; "health" bleibt literal (Anzeige==Endpunkt-
              # Name, §8.2).
              f'<div class="card"><b>{t("system.tools.titel")}</b><br>'
              f'<a href="/log">{t("ui.fuss.log")}</a> · <a href="/health">health</a> · '
              f'<a href="/setup">{t("konfiguration.knopf_setup")}</a></div>'
              f'<div class="card"><b>{t("system.docs.titel")}</b><br>'
              f'<a href="{docs_url}" target="_blank" rel="noopener noreferrer">'
              f'{t("system.docs.link")}</a></div>')
    return inhalt
