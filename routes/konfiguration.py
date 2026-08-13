"""routes/konfiguration — Advanced-Settings-Blatt (Modulumbau R1, byte-treu aus
verifyd extrahiert; Muster auftritte.py). Der Handler reicht cfg, die
CONFIG_WHITELIST des Service und die Auto-Default-Hinweise
(svc._kette_auto_hinweise()) herein; hier wird NUR gerendert."""
import html
import json


def render(cfg, whitelist, auto_hinweis):
    """-> Seiten-INHALT (layout/banner bleiben beim Handler)."""
    NOTIF_KEYS = {"alert_cooldown", "anwesenheit_cooldown", "anwesenheit_push",
                  "mqtt_publish", "telegram_modus", "telegram_inhalt", "telegram_cooldown", "szene_karenz_s",
                  # hat eine eigene, farbig hervorgehobene Karte auf der System-Seite —
                  # hier NICHT nochmal als Tabellenzeile (Doppelbedienung verwirrt)
                  "frigate_read_only"}
    zeilen = []
    for key, (typ, lo, hi, erkl) in whitelist.items():
        if key in NOTIF_KEYS:                          # -> eigener Reiter / eigene Karte
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
    inhalt = ("<h2>Advanced settings</h2>"
              "<p>Changes are audited (config_audit.jsonl); after saving, the service "
              "restarts cleanly (it waits for a running analysis to finish). "
              'Alert channels (Telegram/Pushover/MQTT) and their secrets are on the '
              '<a href="/benachrichtigungen">Notifications</a> page.</p>'
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
