"""routes/konfiguration — Advanced-Settings-Blatt (Modulumbau R1, byte-treu aus
verifyd extrahiert; Muster auftritte.py). Der Handler reicht cfg, die
CONFIG_WHITELIST des Service und die Auto-Default-Hinweise
(svc._kette_auto_hinweise()) herein; hier wird NUR gerendert.
Seit .187 dazu: die Sektion 'Recognition chain' (User-Entscheid 12./13.08.,
konzept_kette_seite.md Stufe 1) — sie ERSETZT die zwei generischen
Dropdown-Zeilen person_pfad/vision_pfad (User: 'die Dropdowns ersetzen';
ein Wert, EIN Bedienort). Andock: core/kette.DEFAULT_KETTE + lage()."""
import html
import json

# person_pfad/vision_pfad erscheinen NICHT mehr in der generischen Tabelle —
# sie leben in der Ketten-Sektion (dieselben cfg-<key>-IDs, derselbe Save-Weg:
# konfigSpeichern sammelt alle [id^=cfg-]-Felder der Seite ein).
KETTE_KEYS = ("person_pfad", "vision_pfad")

# Anzeige-Fakten je Ketten-Stufe, die NICHT aus der Whitelist kommen (die
# Erklaertexte der Schalter kommen weiterhin von dort — eine Quelle): Titel,
# Kosten-Ehrlichkeit (konzept_kette_seite.md: zeigen, WAS ein Schalter spart)
# und der Entscheid-Zeitpunkt in Nutzerworten.
KETTE_ANZEIGE = {
    "gesicht": {"titel": "Face",
                "kosten": "base analysis on the recorded clip — always on",
                "zeitpunkt": "per event"},
    "person": {"titel": "Person (body)",
               "kosten": "the most expensive local step (body embedding on "
                         "your hardware)",
               "zeitpunkt": "per event, decided on the walk-through verdict"},
    "vision": {"titel": "Vision",
               "kosten": "one request per walk-through to your configured "
                         "vision endpoint",
               "zeitpunkt": "at the end of the walk-through"},
}


def kette_sektion(cfg, kette, lage, whitelist, auto_hinweis):
    """-> HTML der 'Recognition chain'-Sektion (Stufe 1: Bedingungen auf der
    BESTEHENDEN Kette; Reihenfolge/‚nur Vision' sind ein zweiter Schritt).
    kette = core/kette.DEFAULT_KETTE (Reihenfolge = Ketten-Reihenfolge),
    lage = core/kette.lage(cfg) (K1: dieselbe Quelle wie /health)."""
    karten = []
    for g in kette:
        stufe_name = g["stufe"]
        anz = KETTE_ANZEIGE.get(stufe_name) or {"titel": stufe_name,
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
            feld = '<b>always</b> <span class="dim">(not switchable today)</span>'
            erkl = ("the face path is the backbone of every analysis — "
                    "person and vision hang off its walk-through verdict")
            auto = ""
        lg = (lage or {}).get(stufe_name) or {}
        if not schalter:
            status = ""
        elif lg.get("wirksam"):
            status = ('<div class="dim kt-zeile">status: <b>armed</b> — '
                      'runs by itself</div>')
        else:
            if stufe_name == "person" and not lg.get("modell_scharf"):
                grund = "no trained person model armed yet"
            elif stufe_name == "vision" and not lg.get("aktiv"):
                grund = "vision detect is switched off"
            else:
                grund = "switched off here"
            status = (f'<div class="dim kt-zeile">status: not running '
                      f'({html.escape(grund)})</div>')
        karten.append(
            f'<div class="card kt-stufe">'
            f'<div class="kamhead"><b>{html.escape(anz["titel"])}</b>'
            f'<span class="dim num">{html.escape(anz["zeitpunkt"])}</span></div>'
            f'<div class="kt-zeile">{feld}</div>'
            + status
            + (f'<div class="dim kt-zeile">{html.escape(erkl)}</div>'
               if erkl else "")
            + (f'<div class="dim kt-zeile">cost: '
               f'{html.escape(anz["kosten"])}</div>' if anz["kosten"] else "")
            + auto
            + '</div>')
    pfeil = '<div class="kt-pfeil dim">→</div>'
    return ('<h3>Recognition chain</h3>'
            '<p class="sub">Which recognizers run, and in which order. The '
            'condition "nur_wenn_gesicht_leer" means: the step only runs '
            'when the face path could NOT confirm everyone on the '
            'walk-through — decided on the whole pass, never on a single '
            'event. Changing the order itself is a later stage; today the '
            'chain always starts with the face path.</p>'
            '<div class="kt-kette">' + pfeil.join(karten) + '</div>')


def kette_seite(cfg, kette, lage, whitelist, auto_hinweis):
    """-> Seiten-INHALT des EIGENEN Blatts /kette (.189, User: 'vier
    Menuepunkte' — Cameras · Notifications · Recognition chain · Advanced).
    Save nutzt denselben konfigSpeichern-Weg (sammelt die cfg-*-Felder DIESER
    Seite; config_schreiben schreibt nur gelieferte Schluessel)."""
    return (kette_sektion(cfg, kette, lage, whitelist, auto_hinweis)
            + '<p><button class="gtb on" onclick="konfigSpeichern()">'
              'Save + restart</button> '
              '<span id="cfg-status" style="color:var(--dim)"></span></p>'
              '<p class="sub">Changes are audited (config_audit.jsonl); after '
              'saving, the service restarts cleanly. All other parameters '
              'live under <a href="/konfiguration">Advanced</a>.</p>')


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
        wert = cfg.get(key)
        if typ is list:
            opts = "".join(f'<option{" selected" if wert == o else ""}>{o}</option>' for o in lo)
            feld = f'<select id="cfg-{key}">{opts}</select>'
        elif typ is bool:
            feld = (f'<select id="cfg-{key}">'
                    f'<option value="true"{" selected" if wert else ""}>on</option>'
                    f'<option value="false"{"" if wert else " selected"}>off</option></select>')
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
    inhalt = ("<h2>Advanced settings</h2>"
              "<p>Changes are audited (config_audit.jsonl); after saving, the service "
              "restarts cleanly (it waits for a running analysis to finish). "
              'Alert channels (Telegram/Pushover/MQTT) and their secrets are on the '
              '<a href="/benachrichtigungen">Notifications</a> page; which '
              'recognizers run is on the <a href="/kette">Recognition '
              'chain</a> page.</p>'
              + kette_html
              + '<h3>All parameters</h3>'
              '<div class="tabelle-wrap"><table><tr><th>Parameter</th><th>Value</th><th>Meaning</th></tr>'
              + "".join(zeilen) + "</table></div>"
              '<p><button class="gtb on" onclick="konfigSpeichern()">Save + restart</button> '
              '<a href="/setup" class="gtb" style="text-decoration:none">Re-run setup wizard</a> '
              '<span id="cfg-status" style="color:var(--dim)"></span></p>'
              "<h3>Read-only (console/yaml)</h3>"
              '<div class="tabelle-wrap"><table>' + "".join(nur_lesen) + "</table></div>"
              '<p class="sub">Camera on/off and per-camera zone conditions are now edited '
              'on the <a href="/kameras">Cameras</a> page.</p>')
    return inhalt
