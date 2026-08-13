"""routes/benachrichtigungen — die Notifications-Seite (M1a, byte-treu aus verifyd
extrahiert; Muster auftritte.py: Daten als Parameter, kein Dienst-Import).
Secrets werden NIE im Klartext gerendert (Platzhalter, leer lassen = behalten)."""
import html


def render(cfg, kat_labels):
    """Liefert den Seiten-INHALT (ohne layout/banner — die bleiben beim Handler)."""
    tg = cfg.get("telegram") or {}
    po = cfg.get("pushover") or {}
    mq = cfg.get("mqtt") or {}
    _st = "margin:2px 0"

    def _selbool(id_, val):
        return (f'<select id="{id_}" style="{_st}"><option value="true"{" selected" if val else ""}>on</option>'
                f'<option value="false"{"" if val else " selected"}>off</option></select>')

    def _num(id_, val):
        return f'<input id="{id_}" value="{html.escape(str(val))}" size="7" style="{_st}">'

    def _txt(id_, val, secret=False):
        if secret:                              # Secret NIE im Klartext rendern
            ph = "•••• stored — blank keeps it" if val else "not set"
            return f'<input id="{id_}" value="" placeholder="{ph}" size="36" autocomplete="off" style="{_st}">'
        return f'<input id="{id_}" value="{html.escape(str(val or ""))}" size="36" style="{_st}">'

    CATS = [("widerspruch", "suslik confirms a different person than Frigate"),
            ("frigate_nur", "Frigate labeled someone, suslik saw no usable face"),
            ("wir_nur", "suslik recognized someone, Frigate did not"),
            ("beide_unknown", "neither side identified a face"),
            ("erkannt", "a known person was recognized"),
            ("fremd_verdacht", "a usable face, but nobody confirmed (possible stranger)"),
            ("unbekannt_schwach", "a face too weak or small to identify")]
    aktive = set(cfg.get("alert_kategorien") or [])
    cat_html = "".join(
        f'<label style="display:block;margin:3px 0"><input type="checkbox" class="n-cat" value="{c}"'
        f'{" checked" if c in aktive else ""}> <b>{html.escape(kat_labels.get(c, c))}</b> <span class="dim">— {html.escape(t)}</span></label>'
        for c, t in CATS)
    mod = cfg.get("telegram_modus", "aus")
    mod_opts = "".join(f'<option{" selected" if mod == o else ""}>{o}</option>'
                       for o in ("aus", "ha", "direkt", "beide"))
    inh = cfg.get("telegram_inhalt", "video")
    inh_opts = "".join(f'<option{" selected" if inh == o else ""}>{o}</option>'
                       for o in ("video", "bild"))
    return (
        "<h2>Notifications</h2>"
        '<p class="sub">Alert channels and their secrets are stored with everything else in '
        '<b>/data</b>; an environment variable still wins if it is set. Leave a secret field blank to '
        'keep the stored value. Use <b>Test</b> next to a channel to send a real message right now '
        '(bypasses cooldowns).</p>'
        '<div class="card"><b>Alerts</b>'
        '<p class="dim">Which judgment categories raise an alert:</p>' + cat_html +
        '<div style="margin-top:8px">Presence push: ' + _selbool("n-anwesenheit_push", cfg.get("anwesenheit_push")) +
        ' &nbsp; Alert cooldown (s): ' + _num("n-alert_cooldown", cfg.get("alert_cooldown")) +
        ' &nbsp; Presence cooldown (s): ' + _num("n-anwesenheit_cooldown", cfg.get("anwesenheit_cooldown")) +
        ' &nbsp; Scene grace (s): ' + _num("n-szene_karenz_s", cfg.get("szene_karenz_s")) + '</div></div>'
        '<div class="card"><b>Pushover</b>'
        '<div>Token: ' + _txt("n-pushover_token", po.get("token"), secret=True) + '</div>'
        '<div>User key: ' + _txt("n-pushover_user", po.get("user")) + '</div>'
        '<button class="gtb" onclick="testKanal(\'pushover\',this)">Test Pushover</button> '
        '<span id="test-pushover" class="dim"></span></div>'
        '<div class="card"><b>Telegram</b>'
        '<div>Mode: <select id="n-telegram_modus" style="' + _st + '">' + mod_opts + '</select> '
        '<span class="dim">aus=off · ha=via Home Assistant · direkt=direct bot · beide=both</span></div>'
        '<div>Attachment: <select id="n-telegram_inhalt" style="' + _st + '">' + inh_opts + '</select> '
        '<span class="dim">video=short clip, image if unavailable · bild=image only '
        '(no transcoding — lighter on weak hardware)</span></div>'
        '<div>Bot token: ' + _txt("n-telegram_bot_token", tg.get("bot_token"), secret=True) + '</div>'
        '<div>Chat ID: ' + _txt("n-telegram_chat_id", tg.get("chat_id")) + '</div>'
        '<div>Unknown cooldown (s): ' + _num("n-telegram_cooldown", cfg.get("telegram_cooldown")) + '</div>'
        '<button class="gtb" onclick="testKanal(\'telegram\',this)">Test Telegram</button> '
        '<span id="test-telegram" class="dim"></span></div>'
        '<div class="card"><b>MQTT</b>'
        '<div>Publish recognition topics: ' + _selbool("n-mqtt_publish", cfg.get("mqtt_publish")) + '</div>'
        '<div>Host: ' + _txt("n-mqtt_host", mq.get("host")) +
        ' Port: ' + _num("n-mqtt_port", mq.get("port") or 1883) + '</div>'
        '<div>User: ' + _txt("n-mqtt_user", mq.get("user")) + '</div>'
        '<div>Password: ' + _txt("n-mqtt_password", mq.get("password"), secret=True) + '</div>'
        '<div>Topic prefix: ' + _txt("n-mqtt_topic_praefix", mq.get("topic_praefix")) + ' '
        '<span class="dim">all published topics start with this — blank keeps the default '
        '<b>verifyd</b> (verifyd/erkennung, verifyd/heartbeat, …), so existing setups keep '
        'working; letters, digits, "_", "-", ".", "/"</span></div>'
        '<button class="gtb" onclick="testKanal(\'mqtt\',this)">Test MQTT</button> '
        '<span id="test-mqtt" class="dim"></span></div>'
        '<p><button class="gtb on" onclick="notifSpeichern()">Save + restart</button> '
        '<span id="notif-status" style="color:var(--dim)"></span></p>')
