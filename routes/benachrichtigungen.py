"""routes/benachrichtigungen — die Notifications-Seite (M1a, byte-treu aus verifyd
extrahiert; Muster auftritte.py: Daten als Parameter, kein Dienst-Import).
Secrets werden NIE im Klartext gerendert (Platzhalter, leer lassen = behalten).
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Zwei Markup-Saetze und die
Produktnamen-Titel bleiben literal (Grenzen: Abschnitts-Kommentar in en.py);
die frueheren Schleifenvariablen `t` sind umbenannt, damit sie t() nicht
verschatten."""
import html

from core.sprache import t


def render(cfg, kat_labels):
    """Liefert den Seiten-INHALT (ohne layout/banner — die bleiben beim Handler)."""
    tg = cfg.get("telegram") or {}
    po = cfg.get("pushover") or {}
    mq = cfg.get("mqtt") or {}
    _st = "margin:2px 0"

    def _selbool(id_, val):
        return (f'<select id="{id_}" style="{_st}"><option value="true"{" selected" if val else ""}>'
                f'{t("benachrichtigungen.felder.option_an")}</option>'
                f'<option value="false"{"" if val else " selected"}>'
                f'{t("benachrichtigungen.felder.option_aus")}</option></select>')

    def _num(id_, val):
        return f'<input id="{id_}" value="{html.escape(str(val))}" size="7" style="{_st}">'

    def _txt(id_, val, secret=False):
        if secret:                              # Secret NIE im Klartext rendern
            ph = (t("benachrichtigungen.felder.secret_gesetzt") if val
                  else t("benachrichtigungen.felder.secret_leer"))
            return f'<input id="{id_}" value="" placeholder="{ph}" size="36" autocomplete="off" style="{_st}">'
        return f'<input id="{id_}" value="{html.escape(str(val or ""))}" size="36" style="{_st}">'

    CATS = [("widerspruch", t("benachrichtigungen.kategorien.widerspruch")),
            ("frigate_nur", t("benachrichtigungen.kategorien.frigate_nur")),
            ("wir_nur", t("benachrichtigungen.kategorien.wir_nur")),
            ("beide_unknown", t("benachrichtigungen.kategorien.beide_unknown")),
            ("erkannt", t("benachrichtigungen.kategorien.erkannt")),
            ("fremd_verdacht", t("benachrichtigungen.kategorien.fremd_verdacht")),
            ("unbekannt_schwach", t("benachrichtigungen.kategorien.unbekannt_schwach"))]
    aktive = set(cfg.get("alert_kategorien") or [])
    cat_html = "".join(
        f'<label style="display:block;margin:3px 0"><input type="checkbox" class="n-cat" value="{c}"'
        f'{" checked" if c in aktive else ""}> <b>{html.escape(kat_labels.get(c, c))}</b> <span class="dim">— {html.escape(beschr)}</span></label>'
        for c, beschr in CATS)
    mod = cfg.get("telegram_modus", "aus")
    mod_opts = "".join(f'<option{" selected" if mod == o else ""}>{o}</option>'
                       for o in ("aus", "ha", "direkt", "beide"))
    inh = cfg.get("telegram_inhalt", "video")
    inh_opts = "".join(f'<option{" selected" if inh == o else ""}>{o}</option>'
                       for o in ("video", "bild"))
    return (
        f"<h2>{t('benachrichtigungen.titel')}</h2>"
        '<p class="sub">Alert channels and their secrets are stored with everything else in '
        '<b>/data</b>; an environment variable still wins if it is set. Leave a secret field blank to '
        'keep the stored value. Use <b>Test</b> next to a channel to send a real message right now '
        '(bypasses cooldowns).</p>'
        f'<div class="card"><b>{t("benachrichtigungen.alerts.titel")}</b>'
        # .200 (Fix 2): der Satz stimmt jetzt — die Kategorien steuern seither
        # wirklich ALLE Kanaele (vorher wirkten sie nur auf Pushover, Telegram/
        # MQTT-Szenen sendeten ungefragt).
        f'<p class="dim">{t("benachrichtigungen.alerts.hinweis")}</p>' + cat_html +
        f'<div style="margin-top:8px">{t("benachrichtigungen.alerts.stil_label")} '
        '<select id="n-alert_stil" style="' + _st + '">'
        + "".join(f'<option value="{o}"{" selected" if (cfg.get("alert_stil") or "worte") == o else ""}>{lbl}</option>'
                  for o, lbl in (("worte", t("benachrichtigungen.alerts.stil_worte")),
                                 ("worte_zahlen", t("benachrichtigungen.alerts.stil_worte_zahlen"))))
        + f'</select> <span class="dim">— {t("benachrichtigungen.alerts.stil_hinweis")}</span></div>'
        f'<div style="margin-top:8px">{t("benachrichtigungen.alerts.label_anwesenheit_push")} '
        + _selbool("n-anwesenheit_push", cfg.get("anwesenheit_push")) +
        f' &nbsp; {t("benachrichtigungen.alerts.label_alert_cooldown")} '
        + _num("n-alert_cooldown", cfg.get("alert_cooldown")) +
        f' &nbsp; {t("benachrichtigungen.alerts.label_anwesenheit_cooldown")} '
        + _num("n-anwesenheit_cooldown", cfg.get("anwesenheit_cooldown")) +
        f' &nbsp; {t("benachrichtigungen.alerts.label_szene_karenz")} '
        + _num("n-szene_karenz_s", cfg.get("szene_karenz_s")) + '</div></div>'
        '<div class="card"><b>Pushover</b>'
        f'<div>{t("benachrichtigungen.pushover.label_token")} '
        + _txt("n-pushover_token", po.get("token"), secret=True) + '</div>'
        f'<div>{t("benachrichtigungen.pushover.label_user")} '
        + _txt("n-pushover_user", po.get("user")) + '</div>'
        '<button class="gtb" onclick="testKanal(\'pushover\',this)">'
        f'{t("benachrichtigungen.pushover.knopf_test")}</button> '
        '<span id="test-pushover" class="dim"></span></div>'
        '<div class="card"><b>Telegram</b>'
        f'<div>{t("benachrichtigungen.telegram.label_modus")} '
        '<select id="n-telegram_modus" style="' + _st + '">' + mod_opts + '</select> '
        f'<span class="dim">{t("benachrichtigungen.telegram.hinweis_modus")}</span></div>'
        f'<div>{t("benachrichtigungen.telegram.label_inhalt")} '
        '<select id="n-telegram_inhalt" style="' + _st + '">' + inh_opts + '</select> '
        f'<span class="dim">{t("benachrichtigungen.telegram.hinweis_inhalt")}</span></div>'
        f'<div>{t("benachrichtigungen.telegram.label_bot_token")} '
        + _txt("n-telegram_bot_token", tg.get("bot_token"), secret=True) + '</div>'
        f'<div>{t("benachrichtigungen.telegram.label_chat_id")} '
        + _txt("n-telegram_chat_id", tg.get("chat_id")) + '</div>'
        f'<div>{t("benachrichtigungen.telegram.label_cooldown")} '
        + _num("n-telegram_cooldown", cfg.get("telegram_cooldown")) + '</div>'
        '<button class="gtb" onclick="testKanal(\'telegram\',this)">'
        f'{t("benachrichtigungen.telegram.knopf_test")}</button> '
        '<span id="test-telegram" class="dim"></span></div>'
        '<div class="card"><b>MQTT</b>'
        f'<div>{t("benachrichtigungen.mqtt.label_publish")} '
        + _selbool("n-mqtt_publish", cfg.get("mqtt_publish")) + '</div>'
        f'<div>{t("benachrichtigungen.mqtt.label_host")} '
        + _txt("n-mqtt_host", mq.get("host")) +
        f' {t("benachrichtigungen.mqtt.label_port")} '
        + _num("n-mqtt_port", mq.get("port") or 1883) + '</div>'
        f'<div>{t("benachrichtigungen.mqtt.label_user")} '
        + _txt("n-mqtt_user", mq.get("user")) + '</div>'
        f'<div>{t("benachrichtigungen.mqtt.label_password")} '
        + _txt("n-mqtt_password", mq.get("password"), secret=True) + '</div>'
        f'<div>{t("benachrichtigungen.mqtt.label_topic_praefix")} '
        + _txt("n-mqtt_topic_praefix", mq.get("topic_praefix")) + ' '
        '<span class="dim">all published topics start with this — blank keeps the default '
        '<b>verifyd</b> (verifyd/erkennung, verifyd/heartbeat, …), so existing setups keep '
        'working; letters, digits, "_", "-", ".", "/"</span></div>'
        '<button class="gtb" onclick="testKanal(\'mqtt\',this)">'
        f'{t("benachrichtigungen.mqtt.knopf_test")}</button> '
        '<span id="test-mqtt" class="dim"></span></div>'
        f'<p><button class="gtb on" onclick="notifSpeichern()">'
        f'{t("benachrichtigungen.fuss.knopf_speichern")}</button> '
        '<span id="notif-status" style="color:var(--dim)"></span></p>')
