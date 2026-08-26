"""routes/konfiguration — Advanced-Settings-Blatt (Modulumbau R1, byte-treu aus
verifyd extrahiert; Muster auftritte.py). Der Handler reicht cfg, die
CONFIG_WHITELIST des Service und die Auto-Default-Hinweise
(svc._kette_auto_hinweise()) herein; hier wird NUR gerendert.
Seit .187 dazu: die Sektion 'Recognition chain' (User-Entscheid 12./13.08.,
konzept_kette_seite.md Stufe 1) — sie ERSETZT die zwei generischen
Dropdown-Zeilen person_pfad/vision_pfad (User: 'die Dropdowns ersetzen';
ein Wert, EIN Bedienort). Andock: core/kette.DEFAULT_KETTE + lage().
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py; KETTE_ANZEIGE wurde dafuer zur
Funktion _kette_anzeige() (t() zur Render-Zeit, nie beim Import — sonst
froere die Sprachwahl auf den Import-Moment ein)."""
import html
import json

from core.frigate_auth import SEKTIONS_SCHLUESSEL as FRIGATE_AUTH_KEYS
from core.sprache import t

# person_pfad/vision_pfad erscheinen NICHT mehr in der generischen Tabelle —
# sie leben in der Ketten-Sektion (dieselben cfg-<key>-IDs, derselbe Save-Weg:
# konfigSpeichern sammelt alle [id^=cfg-]-Felder der Seite ein).
KETTE_KEYS = ("person_pfad", "vision_pfad")


def _kette_anzeige():
    """Anzeige-Fakten je Ketten-Stufe, die NICHT aus der Whitelist kommen (die
    Erklaertexte der Schalter kommen weiterhin von dort — eine Quelle): Titel,
    Kosten-Ehrlichkeit (konzept_kette_seite.md: zeigen, WAS ein Schalter spart)
    und der Entscheid-Zeitpunkt in Nutzerworten."""
    return {
        "gesicht": {"titel": t("konfiguration.kette.gesicht_titel"),
                    "kosten": t("konfiguration.kette.gesicht_kosten"),
                    "zeitpunkt": t("konfiguration.kette.gesicht_zeitpunkt")},
        "person": {"titel": t("konfiguration.kette.person_titel"),
                   "kosten": t("konfiguration.kette.person_kosten"),
                   "zeitpunkt": t("konfiguration.kette.person_zeitpunkt")},
        "vision": {"titel": t("konfiguration.kette.vision_titel"),
                   "kosten": t("konfiguration.kette.vision_kosten"),
                   "zeitpunkt": t("konfiguration.kette.vision_zeitpunkt")},
    }


def kette_sektion(cfg, kette, lage, whitelist, auto_hinweis):
    """-> HTML der 'Recognition chain'-Sektion (Stufe 1: Bedingungen auf der
    BESTEHENDEN Kette; Reihenfolge/‚nur Vision' sind ein zweiter Schritt).
    kette = core/kette.DEFAULT_KETTE (Reihenfolge = Ketten-Reihenfolge),
    lage = core/kette.lage(cfg) (K1: dieselbe Quelle wie /health)."""
    karten = []
    anzeige = _kette_anzeige()
    for g in kette:
        stufe_name = g["stufe"]
        anz = anzeige.get(stufe_name) or {"titel": stufe_name,
                                          "kosten": "", "zeitpunkt": ""}
        schalter = g.get("schalter")
        if schalter:
            wert = cfg.get(schalter)
            opts = "".join(
                f'<option{" selected" if wert == o else ""}>{o}</option>'
                for o in g["stufen"])
            feld = f'<select id="cfg-{schalter}">{opts}</select>'
            erkl = (whitelist.get(schalter) or (None, None, None, ""))[3]
            auto = (f'<div class="dim kt-zeile"><b style="color:var(--warn)">'
                    f'{html.escape(auto_hinweis[schalter])}</b></div>'
                    if schalter in auto_hinweis else "")
        else:
            feld = (f'<b>{t("konfiguration.kette.immer_an")}</b> '
                    f'<span class="dim">{t("konfiguration.kette.immer_hinweis")}</span>')
            erkl = t("konfiguration.kette.gesicht_erkl")
            auto = ""
        lg = (lage or {}).get(stufe_name) or {}
        if not schalter:
            status = ""
        elif lg.get("wirksam"):
            # Stufe-0-Grenze: <b>armed</b> mitten im Satz bleibt literal.
            status = ('<div class="dim kt-zeile">status: <b>armed</b> — '
                      'runs by itself</div>')
        else:
            if stufe_name == "person" and not lg.get("modell_scharf"):
                grund = t("konfiguration.kette.grund_person")
            elif stufe_name == "vision" and not lg.get("aktiv"):
                grund = t("konfiguration.kette.grund_vision")
            else:
                grund = t("konfiguration.kette.grund_aus")
            status = (f'<div class="dim kt-zeile">'
                      f'{t("konfiguration.kette.status_aus", grund=html.escape(grund))}</div>')
        karten.append(
            f'<div class="card kt-stufe">'
            f'<div class="kamhead"><b>{html.escape(anz["titel"])}</b>'
            f'<span class="dim num">{html.escape(anz["zeitpunkt"])}</span></div>'
            f'<div class="kt-zeile">{feld}</div>'
            + status
            + (f'<div class="dim kt-zeile">{html.escape(erkl)}</div>'
               if erkl else "")
            + (f'<div class="dim kt-zeile">'
               f'{t("konfiguration.kette.zeile_kosten", kosten=html.escape(anz["kosten"]))}</div>'
               if anz["kosten"] else "")
            + auto
            + '</div>')
    pfeil = '<div class="kt-pfeil dim">→</div>'
    return (f'<h3>{t("konfiguration.kette.titel")}</h3>'
            f'<p class="sub">{t("konfiguration.kette.satz")}</p>'
            '<div class="kt-kette">' + pfeil.join(karten) + '</div>')


def kette_seite(cfg, kette, lage, whitelist, auto_hinweis):
    """-> Seiten-INHALT des EIGENEN Blatts /kette (.189, User: 'vier
    Menuepunkte' — Cameras · Notifications · Recognition chain · Advanced).
    Save nutzt denselben konfigSpeichern-Weg (sammelt die cfg-*-Felder DIESER
    Seite; config_schreiben schreibt nur gelieferte Schluessel)."""
    return (kette_sektion(cfg, kette, lage, whitelist, auto_hinweis)
            + '<p><button class="gtb on" onclick="konfigSpeichern()">'
            + t("konfiguration.knopf_speichern") + '</button> '
              '<span id="cfg-status" style="color:var(--dim)"></span></p>'
              # Stufe-0-Grenze: der Satzrest mit <a>-Link bleibt literal.
              f'<p class="sub">{t("konfiguration.kette_blatt.hinweis")} '
              'All other parameters '
              'live under <a href="/konfiguration">Advanced</a>.</p>')


def frigate_auth_sektion(cfg):
    """-> HTML der Frigate-Login-Sektion (5e). Optional: leer gelassen aendert
    sich am Verhalten nichts, und genau das sagt der Text auch.

    Das Passwort wird NIE im Klartext gerendert — dasselbe Muster wie die
    Meldekanal-Secrets (routes/benachrichtigungen._txt): leeres Feld mit
    einem Platzhalter, der nur sagt, OB etwas gespeichert ist. Gespeichert
    wird ueber den BESTEHENDEN Weg: die IDs beginnen mit cfg-, damit
    konfigSpeichern() sie mit allen anderen Feldern des Blatts einsammelt und
    an POST /konfig schickt — kein zweiter Schreibweg, kein eigener fetch."""
    gesetzt = bool(cfg.get("frigate_password"))
    ph = (t("konfiguration.frigate_auth.pw_gesetzt") if gesetzt
          else t("konfiguration.frigate_auth.pw_leer"))
    tls = cfg.get("frigate_tls_verify", True)
    return (
        f'<h3>{t("konfiguration.frigate_auth.titel")}</h3>'
        f'<p class="sub">{t("konfiguration.frigate_auth.satz")}</p>'
        '<div class="tabelle-wrap"><table>'
        f'<tr><td><b>frigate_user</b></td>'
        f'<td><input id="cfg-frigate_user" size="24" autocomplete="off" '
        f'value="{html.escape(str(cfg.get("frigate_user") or ""), quote=True)}"></td>'
        f'<td>{t("konfiguration.frigate_auth.erkl_user")}</td></tr>'
        f'<tr><td><b>frigate_password</b></td>'
        f'<td><input id="cfg-frigate_password" type="password" size="24" '
        f'autocomplete="new-password" value="" placeholder="{html.escape(ph, quote=True)}"></td>'
        f'<td>{t("konfiguration.frigate_auth.erkl_password")}</td></tr>'
        f'<tr><td><b>frigate_tls_verify</b></td>'
        f'<td><select id="cfg-frigate_tls_verify">'
        f'<option value="true"{" selected" if tls else ""}>'
        f'{t("konfiguration.feld.option_an")}</option>'
        f'<option value="false"{"" if tls else " selected"}>'
        f'{t("konfiguration.feld.option_aus")}</option></select></td>'
        f'<td>{t("konfiguration.frigate_auth.erkl_tls")}</td></tr>'
        '</table></div>')


def render(cfg, whitelist, auto_hinweis, kette=None, kette_lage=None):
    """-> Seiten-INHALT des Advanced-Blatts. Die Ketten-Schalter erscheinen
    hier seit .189 GAR NICHT mehr (eigenes Blatt /kette, ein Bedienort);
    die kette/kette_lage-Parameter bleiben fuer Rueckwaerts-Aufrufer und
    rendern die Sektion inline, falls uebergeben."""
    NOTIF_KEYS = {"alert_cooldown", "anwesenheit_cooldown", "anwesenheit_push",
                  "mqtt_publish", "telegram_modus", "telegram_inhalt", "telegram_cooldown", "szene_karenz_s",
                  # hat eine eigene, farbig hervorgehobene Karte auf der System-Seite —
                  # hier NICHT nochmal als Tabellenzeile (Doppelbedienung verwirrt)
                  "frigate_read_only"}
    zeilen = []
    for key, (typ, lo, hi, erkl) in whitelist.items():
        if key in NOTIF_KEYS:                          # -> eigener Reiter / eigene Karte
            continue
        if key in KETTE_KEYS:                          # -> eigenes Blatt /kette (.189)
            continue
        if key in FRIGATE_AUTH_KEYS:                   # 5e -> eigene Sektion darueber
            continue
        wert = cfg.get(key)
        if typ is list:
            opts = "".join(f'<option{" selected" if wert == o else ""}>{o}</option>' for o in lo)
            feld = f'<select id="cfg-{key}">{opts}</select>'
        elif typ is bool:
            feld = (f'<select id="cfg-{key}">'
                    f'<option value="true"{" selected" if wert else ""}>'
                    f'{t("konfiguration.feld.option_an")}</option>'
                    f'<option value="false"{"" if wert else " selected"}>'
                    f'{t("konfiguration.feld.option_aus")}</option></select>')
        else:
            feld = (f'<input id="cfg-{key}" value="{wert}" size="7" '
                    f'>')
        grenzen = f" ({lo}–{hi})" if lo is not None and typ is not list else ""
        auto = (f'<br><b style="color:var(--warn)">'
                f'{html.escape(auto_hinweis[key])}</b>'
                if key in auto_hinweis else "")
        zeilen.append(f"<tr><td><b>{key}</b></td><td>{feld}</td>"
                      f"<td>{html.escape(erkl)}{grenzen}{auto}</td></tr>")
    nur_lesen = []
    for key in ("trigger", "ov_device", "backend",
                "lookback_h", "clip_delay", "web_port"):
        if key in cfg and key not in whitelist:
            nur_lesen.append(f"<tr><td>{key}</td><td colspan=2>"
                             f"{html.escape(json.dumps(cfg.get(key), ensure_ascii=False))}</td></tr>")
    kette_html = (kette_sektion(cfg, kette, kette_lage, whitelist,
                                auto_hinweis)
                  if kette is not None else "")
    # Stufe-0-Grenze: die Satzreste mit <a>-Links (Kopf-Absatz, Fussnote
    # zur Cameras-Seite) bleiben literal (t_html-Weg spaeterer Stufen).
    inhalt = (f"<h2>{t('konfiguration.titel')}</h2>"
              f"<p>{t('konfiguration.kopf.satz1')} "
              'Alert channels (Telegram/Pushover/MQTT) and their secrets are on the '
              '<a href="/benachrichtigungen">Notifications</a> page; which '
              'recognizers run is on the <a href="/kette">Recognition '
              'chain</a> page.</p>'
              + kette_html
              + frigate_auth_sektion(cfg)          # 5e: vor der grossen Tabelle,
                                                   # weil es zur Verbindung gehoert
              + f'<h3>{t("konfiguration.abschnitt_alle")}</h3>'
              f'<div class="tabelle-wrap"><table><tr><th>{t("konfiguration.tabelle.kopf_parameter")}</th>'
              f'<th>{t("konfiguration.tabelle.kopf_wert")}</th>'
              f'<th>{t("konfiguration.tabelle.kopf_bedeutung")}</th></tr>'
              + "".join(zeilen) + "</table></div>"
              f'<p><button class="gtb on" onclick="konfigSpeichern()">{t("konfiguration.knopf_speichern")}</button> '
              f'<a href="/setup" class="gtb" style="text-decoration:none">{t("konfiguration.knopf_setup")}</a> '
              '<span id="cfg-status" style="color:var(--dim)"></span></p>'
              f"<h3>{t('konfiguration.abschnitt_readonly')}</h3>"
              '<div class="tabelle-wrap"><table>' + "".join(nur_lesen) + "</table></div>"
              '<p class="sub">Camera on/off and per-camera zone conditions are now edited '
              'on the <a href="/kameras">Cameras</a> page.</p>')
    return inhalt
