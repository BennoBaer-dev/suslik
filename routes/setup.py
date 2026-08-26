"""routes/setup — der gefuehrte Erst-Einrichtungs-Wizard /setup (User 22.07.),
ME1 byte-treu aus verifyd extrahiert (Schnappschuss-Beweis
scratchpad/me1_schnappschuss.py; Muster kameras/benachrichtigungen: Daten als
Parameter, kein Dienst-Import). pruefe_url/frigate_cameras/frigate_read_only
bleiben im Kern (Frigate-HTTP-Block, wandert erst mit ME5 nach
core/frigatehttp) und kommen als CALLABLES herein — modulplan §2c
(Callback-Injektion, nie Rueckimport). onnxruntime laedt lazy im Render
(Import-Zeit-Vertrag: kein ORT beim Modul-Import; der Harnisch stubbt es).
Sprachschicht unangetastet: alle sichtbaren Texte sind seit Tranche B
Schluessel (setupwiz.*) — der Auszug fasst keine Texte an."""
import html
import json
import os
import urllib.request

import webui
from core.sprache import SPRACHEN, t, t_html


def render(qs, cfg, pruefe_url, frigate_cameras, frigate_read_only):
    """-> Seiten-INHALT des Wizards (Layout/Banner/Titel bleiben beim Handler).
    qs = parse_qs-Dict der Anfrage; die drei Callables kommen aus verifyd."""
    import onnxruntime as _ort
    url = (qs.get("url", [""])[0] or cfg.get("frigate_url", "")
           or os.environ.get("FRIGATE_URL", "")).strip()   # Vorbelegung: unser Deployment setzt FRIGATE_URL
    cams, ferr = ({}, None)
    if url:
        _ok, _res = pruefe_url(url)   # aus dem Query-String -> ungeprueft waere die Seite ein Datei-/Port-Orakel
        if not _ok:
            url, ferr = "", _res
    if url:
        cams, ferr = frigate_cameras({**cfg, "frigate_url": url}, force=("url" in qs))
    # --- Schritt 1: Frigate-Verbindung ---
    if url and not ferr and cams:
        fstat = f'<div class="ok-box">{t("setupwiz.frigate.status_ok", n=len(cams))}</div>'
    elif url or ferr:          # ferr auch OHNE url zeigen: eine abgelehnte URL (Tippfehler
                               # wie 'htp://…') darf nicht stillschweigend wirkungslos bleiben
        fstat = (f'<div class="err-box">{t("setupwiz.frigate.status_fehl", fehler=html.escape(str(ferr or t("setupwiz.frigate.status_fehl_keine"))))}'
                 f'<br><small>{t("setupwiz.frigate.status_fehl_hinweis")}</small></div>')
    else:
        fstat = f'<div class="dim">{t("setupwiz.frigate.status_leer")}</div>'
    s1 = ('<div class="card setup-step"><div class="sh"><span class="sn">1</span>'
          f'<b>{t("setupwiz.frigate.titel")}</b></div>'
          f'<p class="sub">{t("setupwiz.frigate.satz")}</p>'
          f'<div class="frow"><input id="setup-url" value="{html.escape(url)}" '
          'placeholder="http://192.168.x.x:5000" style="min-width:16rem">'
          f'<button class="gtb" onclick="setupTest()">{t("setupwiz.frigate.knopf_test")}</button></div>'
          f'{fstat}</div>')
    # --- Schritt 2: Kameras + Zonen (nur wenn verbunden) ---
    kam_store = cfg.get("kameras") or {}
    rz_cfg = cfg.get("required_zones") or {}
    if cams and not ferr:
        karten = []
        for name in sorted(cams):
            cc = cams[name]
            if name in kam_store:
                verw = bool(kam_store[name].get("verwenden", True)); zonen_akt = list(kam_store[name].get("zonen") or [])
            else:
                verw = bool(cc["enabled"]); zonen_akt = list(rz_cfg.get(name) or [])
            nid = html.escape(name, quote=True)
            # Karten-Texte: EINE Quelle mit routes/kameras.py (identische
            # Karten-UI) — kameras.karte.*-Schluessel wiederverwendet,
            # kein zweites Streu-Literal (QS-Ebenen-Regel).
            verwenden = (f'<label class="sw"><input type="checkbox" class="kam-verw" '
                         f'data-cam="{nid}"{" checked" if verw else ""}> {t("kameras.karte.verwenden")}</label>')
            if cc["zones"]:
                zboxes = " ".join(
                    f'<label class="zbox"><input type="checkbox" class="kam-zone" '
                    f'data-cam="{nid}" value="{html.escape(z, quote=True)}"'
                    f'{" checked" if z in zonen_akt else ""}> {html.escape(z)}</label>'
                    for z in cc["zones"])
                zonen_ui = f'<div class="zbar">{zboxes}<span class="dim">{t("kameras.karte.zonen_hinweis")}</span></div>'
            else:
                zonen_ui = f'<div class="zbar dim">{t("kameras.karte.zonen_keine")}</div>'
            karten.append(f'<div class="card"><div class="kamhead"><b>{html.escape(name)}</b>'
                          f'<span class="dim num">{cc["width"] or "?"}×{cc["height"] or "?"}</span>'
                          f'{verwenden}</div>{zonen_ui}</div>')
        s2 = ('<div class="setup-step"><div class="sh"><span class="sn">2</span>'
              f'<b>{t("setupwiz.kameras.titel")}</b></div>'
              f'<p class="sub">{t("setupwiz.kameras.satz")}</p>'
              + "".join(karten) + '</div>')
    else:
        s2 = ('<div class="setup-step dim"><div class="sh"><span class="sn">2</span>'
              f'<b>{t("setupwiz.kameras.titel")}</b></div>'
              f'<p class="sub">{t("setupwiz.kameras.satz_ohne")}</p></div>')
    # --- Schritt 3: Backend/GPU ---
    avail = _ort.get_available_providers()
    # P3.1: Optionen + Labels aus der Registry (wizard_optionen liefert die
    # Werte in der bisherigen Reihenfolge, cpu zuletzt als Universal-Fallback).
    from core.registry import wizard_optionen, WIZARD_LABELS
    _werte = wizard_optionen(avail)
    cur_bk = cfg.get("backend") or next(
        (w for w in _werte if w != "cpu"), "cpu")
    bk_opts = [(w, WIZARD_LABELS[w]) for w in _werte]
    bk_html = "".join(
        f'<label class="bk"><input type="radio" name="setup-backend" value="{html.escape(bid, quote=True)}"'
        f'{" checked" if bid == cur_bk else ""}> {html.escape(lbl)}</label>' for bid, lbl in bk_opts)
    s3 = ('<div class="setup-step"><div class="sh"><span class="sn">3</span>'
          f'<b>{t("setupwiz.backend.titel")}</b></div>'
          f'<p class="sub">{t("setupwiz.backend.verfuegbar")} <span class="num">{html.escape(", ".join(avail))}</span>. '
          f'{t("setupwiz.backend.satz_wahl")} '
          # Stufe 3 (t_html): der Satz zitiert die Seite
          # <b>System</b> — Kopplung (== system.titel/nav.system)
          # ist am Schluessel dokumentiert.
          f'{t_html("setupwiz.backend.system_satz")}</p>'
          f'<div class="bks">{bk_html}</div></div>')
    # --- Schritt 4: Gesichter aus Frigate importieren ---
    if cams and not ferr and url:
        try:
            from core import frigate_auth as _fauth      # 5e: DER eine Griff
            with _fauth.oeffnen(f"{url}/api/faces", timeout=15) as r:
                _fi = json.load(r)
            n_pers = len([k for k in _fi if k != "train"])
            n_img = sum(len(v) for k, v in _fi.items() if k != "train")
        except Exception:
            n_pers = n_img = 0
        if n_img:
            # Zaehler mit hervorgehobener Zahl (§8.10): Split an der
            # <b>-Markup-Grenze, die Zahlen bleiben Code.
            s4 = ('<div class="setup-step"><div class="sh"><span class="sn">4</span>'
                  f'<b>{t("setupwiz.import.titel")}</b></div>'
                  f'<p class="sub">{t("setupwiz.import.zahl_vor")}<b>{n_img}</b>{t("setupwiz.import.zahl_mitte")}'
                  f'<b>{n_pers}</b>{t("setupwiz.import.zahl_nach")} {t("setupwiz.import.satz")}</p>'
                  f'<button class="gtb on" onclick="wizImport(this)">{t("setupwiz.import.knopf", n=n_img)}</button> '
                  '<span id="wiz-import-status" class="dim"></span></div>')
        else:
            s4 = ('<div class="setup-step dim"><div class="sh"><span class="sn">4</span>'
                  f'<b>{t("setupwiz.import.titel")}</b></div>'
                  f'<p class="sub">{t("setupwiz.import.satz_leer")}</p></div>')
    else:
        s4 = ('<div class="setup-step dim"><div class="sh"><span class="sn">4</span>'
              f'<b>{t("setupwiz.import.titel")}</b></div>'
              f'<p class="sub">{t("setupwiz.import.satz_ohne")}</p></div>')
    # --- Abschluss ---
    fertig = ('<div class="setup-step"><button class="gtb on" onclick="setupSpeichern(this)">'
              f'{t("setupwiz.fertig.knopf")}</button> '
              '<span id="setup-status" style="color:var(--dim)"></span>'
              f'<p class="sub">{t("setupwiz.fertig.satz")} '
              # Stufe 3 (t_html): zitiert <b>System → Re-run setup
              # wizard</b> — Kopplung (system.titel +
              # konfiguration.knopf_setup) am Schluessel.
              f'{t_html("setupwiz.fertig.wieder_satz")}</p></div>')
    s0 = (f'<div class="setup-step"><div class="sh"><b>{t("setupwiz.restore.titel")}</b></div>'
          f'<p class="sub">{t("setupwiz.restore.satz")}</p>'
          f'<label class="gtb" style="cursor:pointer">{t("setupwiz.restore.knopf")}'
          '<input type="file" accept="application/json,.json" style="display:none" '
          'onchange="configRestore(this)"></label> '
          '<span id="restore-status" class="dim"></span></div>')
    _wb_ro = frigate_read_only(cfg)     # Vorbelegung mit dem Ist-Wert (Wizard-Durchlauf kippt prod nicht)
    s5 = ('<div class="setup-step"><div class="sh"><span class="sn">5</span>'
          f'<b>{t("setupwiz.write.titel")}</b></div>'
          f'<p class="sub">{t("setupwiz.write.satz")}</p>'
          '<label style="display:block;margin:3px 0"><input type="radio" name="setup-write" value="ro"'
          + (' checked' if _wb_ro else '') + f'> {t("setupwiz.write.opt_ro")}</label>'
          '<label style="display:block;margin:3px 0"><input type="radio" name="setup-write" value="rw"'
          + ('' if _wb_ro else ' checked') + f'> {t("setupwiz.write.opt_rw")}</label></div>')
    # --- Schritt 0: Sprachwahl (Sprach-Stufe 1, B20 — laeuft VOR jedem
    # Store-Inhalt, sonst ist die Ersteinrichtung immer englisch).
    # Eigener Sofort-Schrieb ohne Neustart: Klick -> app.js
    # spracheSetzen() -> POST /sprache_speichern (Areas-Muster) ->
    # Reload; die restlichen Schritte erscheinen dann uebersetzt,
    # soweit eingezogen. Unsichtbar, solange nur en registriert ist.
    s_spr = ""
    if len(SPRACHEN) >= 2:
        s_spr = ('<div class="setup-step"><div class="sh"><span class="sn">0</span>'
                 f'<b>{html.escape(t("setup.sprache.titel"))}</b></div>'
                 f'<p class="sub">{html.escape(t("setup.sprache.satz"))}</p>'
                 f'<div class="sp-reihe">{webui.sprache_knoepfe()}</div></div>')
    inhalt = (f'<h2>{t("setupwiz.willkommen.titel")}</h2>'
              f'<p class="sub">{t("setupwiz.willkommen.satz")}</p>'
              + s_spr + s0 + s1 + s2 + s3 + s4 + s5 + fertig)
    return inhalt
