"""core/melden — die MELDEWEGE als eigenes Modul (Modulumbau R3, modulplan.md #3).

Byte-treu aus verifyd.py ausgezogen (Runde R-2026-08-12-modulbau-r3, Basis 7b4c21d):
Kanal-Sender (Pushover/Telegram), die Kanal-Entscheidung des Szenen-Telegrams
(Modus, Unbekannt-Drossel, Captions), der MQTT-Publisher (erkennung + heartbeat,
rc-gepruefter Publish) samt Ausfall-Pfaden, der Transcode-Lauf des Telegram-Clips
und die Notifications-Settings (Store-Schreiber + Kanal-Tests). Keine neue
Semantik. Beweis: tools/harnisch_r3.py (Logik-Harnisch, Basis-Stand gegen
Umbau-Stand ueber eine Fall-Matrix mit Aufzeichnungs-Stubs statt echter Kanaele,
plus Mutations-Probe).

DIE LIVE-ANDOCK-API (stand.md Live-aware-Auflage; live_reiter_bauplan.md §6):
genau diese Funktionen nutzt spaeter die Live-Engine als ZWEITER Erzeuger —
push()/telegram_video() direkt (Wächter-Kennung via `herkunft`, Werte in
core.registry.MELDE_HERKUNFT), mqtt_pub() mit ihrem eigenen Topic, und
telegram_melden() mit EIGENEN Injektionen (die Engine liefert ihren Clip aus
Burst-Bildern via `clip_holen`, ihren eigenen Drossel-Zustand via `zustand`).
Kanalausfall ist nie Absenderausfall: jeder Sender faengt/meldet selbst.

INJEKTION PUR (Muster core/kette.py): dieses Modul importiert verifyd NIE.
Config, Secrets, Log-Kanaele, Locks und Zustands-Dicts kommen als Parameter
bzw. Callables vom Aufrufer. Es definiert KEINE eigenen Locks und haelt KEINEN
eigenen Zustand — die Drossel-Zeitstempel (`zustand`: tg_unbekannt, ha_warn)
und die Transcode-Registry (lock, procs) bleiben Eigentum des Dienstes
(eine Lock-Quelle, modulplan §9-Regel).
"""
import datetime
import json
import os
import re
import signal
import subprocess
import threading
import time
import urllib.request
import uuid

from core import areas as _areas_mod       # Areas Stufe 1 (Meldetext + Payload-Feld)
from core import registry as _reg          # MELDE_HERKUNFT (eine Quelle, .163)
from core import sprache as _sprache       # Sprach-Stufe 4: Meldetexte (Eintrittspunkt b/c)
from core import vertrauen as _vertrauen   # Wortstufen (.249, Kosinus-raus)


# ------------------------------------------------- Sprache am Meldeweg (Stufe 4)
# konzept_sprache.md §2 nennt drei Eintrittspunkte der Sprachaufloesung:
# (a) Request-Beginn (verifyd.handle_one_request), (b) Beginn jedes
# Meldetext-Baus, (c) Alert-Pfad des Live-Waechters. (b) und (c) sind DIESE
# Funktion — Meldungen entstehen OHNE Request, ihre Sprache kommt deshalb
# direkt aus dem Config-Store (mtime-gecacht, im Normalfall eine stat()).
#
# WARUM ueberhaupt ein Aufruf: sprache.aktive() faellt ohne gesetzte
# contextvar ohnehin auf store_sprache() zurueck — jede t()-Zeile fuer sich.
# aktivieren() PINNT die Sprache stattdessen fuer den ganzen Kontext: EIN
# Meldetext ist damit auch dann in EINER Sprache, wenn der Nutzer waehrend
# des Baus umschaltet (dieselbe Zusage wie "konsistent je Seite" beim
# Request). Der Aufruf steht deshalb am Beginn des TEXTBAUS, nicht im
# Sender.
#
# EIGENER PROZESS (c): core/livewached laeuft als eigener Prozess und hat
# keine Dienst-Config — er liest denselben Store. VERIFY_DATA_DIR ist im
# Image gesetzt (docker/Dockerfile*) und wird vom Dienst fuer Kinder
# gesetzt (verifyd.load_config); fehlt es, gilt Englisch (nie ein Fehler,
# nie eine Exception — store_sprache faengt selbst).
def sprache_aktivieren():
    """Aktive Sprache dieses Kontexts aus dem Config-Store pinnen -> Code."""
    return _sprache.aktivieren()


# ------------------------------------------- MQTT-Topic-Praefix (#23, Zusage an Tokn59)
# DIE eine Topic-Quelle (K3-Regel qs_ebenen.md: Aufzaehlungen nie als Streu-Literal):
# JEDES verifyd/*-Topic entsteht ueber topic(cfg, name) — Publisher/Heartbeat/Test hier
# im Modul, die Szene-/Person-/Vision-Topics an ihren Erzeugern in verifyd. Default ist
# das heutige "verifyd" (Zusage: "the current names staying the default so existing
# setups keep working"); gespeichert wird der Praefix im mqtt-Block des Stores
# (mqtt.topic_praefix, Schreibweg notif_speichern wie die anderen Kanal-Felder).
PRAEFIX_STD = "verifyd"
PRAEFIX_MAX = 64
_PRAEFIX_RE = re.compile(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*")


def praefix_pruefen(roh):
    """Eingabe-Pruefung -> (True, wert) | (False, fehlertext). Leer (nach Trim,
    auch nur Schraegstriche) = '' = Default — NIE ein leerer Praefix im Topic
    (ein fuehrender '/' waere ein ANDERES, stilles Topic). Erlaubt sind
    Buchstaben/Ziffern/_-./ in nicht-leeren Segmenten; MQTT-Wildcards (+, #)
    und $-Praefixe scheitern an der Zeichenmenge."""
    w = str(roh if roh is not None else "").strip().strip("/").strip()
    if not w:
        return True, ""
    if len(w) > PRAEFIX_MAX:
        return False, f"topic prefix: at most {PRAEFIX_MAX} characters"
    if not _PRAEFIX_RE.fullmatch(w):
        return False, ("topic prefix: only letters, digits, '_', '-', '.' and '/' "
                       "between segments (no spaces, no '+', '#' or '$')")
    return True, w


def praefix(cfg):
    """Der WIRKSAME Praefix zur Laufzeit. Ein hand-editierter Store mit
    ungueltigem oder leerem Wert faellt auf den Default zurueck — der
    Publisher bricht daran nie (dieselbe Fail-safe-Haltung wie kette.stufe)."""
    ok, w = praefix_pruefen((cfg.get("mqtt") or {}).get("topic_praefix"))
    return w if ok and w else PRAEFIX_STD


def topic(cfg, name):
    """Volles Topic zu einem Namen ('erkennung', 'heartbeat', 'szene_erkannt' …)."""
    return f"{praefix(cfg)}/{name}"


# --------------------------------------------- konfigurierte Kanaele (.200, Fix 3)
def konfigurierte_kanaele(cfg):
    """DIE eine Antwort auf "welche Meldekanaele sind real eingerichtet?" (K3-Regel:
    nie wieder ein Streu-Literal). Nutzer: der Waechter-Kanal-Default in
    livewache.guards_lesen, die Kanal-Vorbelegung neuer Waechter im /live-Handler
    und der "no alert channel"-Hinweis der Today-Seite. Vorher stand dort dreimal
    etwas Eigenes — und neue Waechter defaulteten hart auf ['pushover'], auch wenn
    Pushover nie eingerichtet war: der Waechter triggerte und meldete NIRGENDWO.
    Reihenfolge = KANAELE_ERLAUBT der Live-Engine (pushover, telegram, mqtt)."""
    k = []
    if (cfg.get("pushover") or {}).get("token"):
        k.append("pushover")
    if cfg.get("telegram_modus", "aus") != "aus":
        k.append("telegram")
    if cfg.get("mqtt_publish") and (cfg.get("mqtt") or {}).get("host"):
        k.append("mqtt")
    return k


# ------------------------------------------------------------------ Pushover
def push(cfg, title, message, attachment=None, herkunft=None):
    """`herkunft` (.163): woher die Meldung kommt — Werte und Praefixe in
    core.registry.MELDE_HERKUNFT, Vorgabe live (keine Markierung). Alles, was
    NICHT aus dem Live-Betrieb kommt, sagt es im Text; sonst liest sich eine
    Test-Meldung am Handy wie ein Vorfall.
    Ein url/url_title-Link in den Payload (.200) wurde mit .201 wieder
    ENTFERNT (User-Entscheid 14.08.: erdachtes Personas-Beduerfnis, kein realer
    Nutzerwunsch; suslik ist nicht aus dem Internet erreichbar)."""
    po = cfg.get("pushover") or {}                 # fehlender Block darf keinen KeyError werfen
    token, user = po.get("token"), po.get("user")  # (telegram_video() faengt das laengst ab)
    if not (token and user):
        return False
    message = _reg.melde_text(message, herkunft)
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in [("token", token), ("user", user), ("title", title), ("message", message)]:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    if attachment and os.path.exists(attachment):
        img = open(attachment, "rb").read()
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"attachment\"; "
                     f"filename=\"crop.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode() + img + b"\r\n")
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://api.pushover.net/1/messages.json", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("status") == 1


def stoerung_melden(cfg, text, herkunft=None, bericht=None):
    """P3.5 (Widerleger-Fund: SD4/Watchdog meldeten NUR Pushover — eine Telegram-only-
    Installation erfuhr von Ausfaellen nichts): Stoerungs-Meldungen gehen ueber BEIDE
    Push-Kanaele, je nachdem was konfiguriert ist. MQTT bleibt bewusst aussen vor
    (Integrations-Bus, und bei MQTT-Stoerungen waere er selbst der kranke Kanal).
    `herkunft` (Live-Phase 1, additiv): die Live-Engine reicht ihre Kennung durch,
    damit auch ihre Engine-weiten Stoerungen die eine Herkunfts-Quelle tragen;
    Bestandsaufrufer ohne Argument senden unveraendert (Default live).
    `bericht` (Live-Phase 4, additiv): Liste des Aufrufers — je versuchtem Kanal
    wird ("pushover"|"telegram", ok) angehaengt (ok = Sender hat ANGENOMMEN).
    Die Live-Engine protokolliert damit real rausgegangene Stoerungen fuer die
    Dienst-Zaehler; Rueckgabe (Fehlerliste) bleibt unveraendert.

    SPRACH-STUFE 4 — GRENZE, BEWUSST: der Titel "suslik-Stoerung" ist ein
    deutsches Wort (Alt-Bestand) und die `text`-Inhalte der Aufrufer sind
    technische Stoerungs-DIAGNOSEN, die wortgleich auch ins Log gehen
    (Log bleibt englisch/maschinenlesbar, konzept_sprache.md §4 B20).
    Beides bleibt literal — de->en waere eine bewusste Textaenderung, und
    UI/Log zu trennen ist ein eigener Umbau (do_POST-Marker (b)+(c))."""
    fehler = []
    try:
        ok = push(cfg, "suslik-Stoerung", text, None, herkunft=herkunft)
        if bericht is not None:
            bericht.append(("pushover", bool(ok)))
    except Exception as e:
        fehler.append(f"pushover: {e}")
        if bericht is not None:
            bericht.append(("pushover", False))
    tg = (cfg.get("telegram") or {})
    if tg.get("bot_token") and tg.get("chat_id"):
        try:
            ok = telegram_video(cfg, None, f"suslik-Stoerung: {text}", herkunft=herkunft)
            if bericht is not None:
                bericht.append(("telegram", bool(ok)))
        except Exception as e:
            fehler.append(f"telegram: {e}")
            if bericht is not None:
                bericht.append(("telegram", False))
    return fehler


def telegram_video(cfg, video_path, caption, crop=None, herkunft=None):
    """Direktversand an die Telegram-Bot-API (Weg B): Video, sonst Foto, sonst reiner Text.
    Multipart wie push(); Secrets aus cfg['telegram'] (per ${VAR} aus der .env expandiert).
    `herkunft` (.163) wie bei push(): Nicht-Live-Meldungen tragen ihre Marke."""
    tg = cfg.get("telegram") or {}
    token, chat = tg.get("bot_token"), tg.get("chat_id")
    if not token or not chat:
        return False
    caption = _reg.melde_text(caption, herkunft)
    if video_path and os.path.exists(video_path) and os.path.getsize(video_path) <= 49 * 1024 * 1024:
        method, field, fname, ctype = "sendVideo", "video", "clip.mp4", "video/mp4"
        payload = open(video_path, "rb").read()
    elif crop and os.path.exists(crop):
        method, field, fname, ctype = "sendPhoto", "photo", "crop.jpg", "image/jpeg"
        payload = open(crop, "rb").read()
    else:
        method, field, payload = "sendMessage", None, None
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in [("chat_id", str(chat)), ("caption" if payload else "text", caption)]:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    if payload:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
                     f"filename=\"{fname}\"\r\nContent-Type: {ctype}\r\n\r\n".encode() + payload + b"\r\n")
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("ok") is True


# ------------------------------------------------------------------ MQTT-Publisher (AP2)
def mqtt_herkunft(payload, herkunft=None):
    """Das Herkunfts-Feld in einen JSON-Payload einsetzen (reine Textarbeit,
    damit der Beweis sie ohne Broker pruefen kann). Ist der Payload kein
    JSON-Objekt (Heartbeat sendet blanke Werte), bleibt er unangetastet —
    ein Kennzeichen ist nie wichtiger als ein zustellbarer Payload."""
    wert = herkunft or _reg.MELDE_HERKUNFT_STD
    if wert not in _reg.MELDE_HERKUNFT:
        wert = _reg.MELDE_HERKUNFT_STD
    try:
        d = json.loads(payload)
    except (TypeError, ValueError):
        return payload
    if not isinstance(d, dict):
        return payload
    d["herkunft"] = wert
    return json.dumps(d, ensure_ascii=False)


def mqtt_pub(pub, log, topic, payload, retain=False, herkunft=None):
    """Publish MIT rc-Pruefung. Rueckgabe True = von paho angenommen.

    paho wirft bei getrenntem Broker KEINE Exception: publish() liefert rc=MQTT_ERR_NO_CONN und
    die Nachricht ist bei QoS 0 verworfen. Ohne diese Pruefung stand die Erfolgszeile
    ('SCENE recognized', 'SCENE unknown') im Log, waehrend die HA-Automation nie etwas bekam —
    ein stiller Meldungsverlust, den niemand sehen konnte.

    `herkunft` (.163): dieselbe Herkunft wie bei push()/telegram_video(), hier aber
    als EIGENES FELD im Payload statt als Text-Praefix — Home Assistant soll darauf
    filtern koennen, ohne einen Meldetext zu zerlegen. Das Feld steht IMMER da
    (auch `live`), damit eine Automation sich auf seine Anwesenheit verlassen kann.

    `pub` kommt vom Aufrufer (Live-Andock: die Engine reicht denselben oder einen
    eigenen paho-Client herein); pub=None ist der ehrliche 'kein Publisher'-Fall."""
    payload = mqtt_herkunft(payload, herkunft)
    if not pub:
        return False
    try:
        info = pub.publish(topic, payload, retain=retain)
        if getattr(info, "rc", 1) == 0:                  # 0 == MQTT_ERR_SUCCESS
            return True
        log(f"!! MQTT NOT delivered ({topic}, rc={info.rc}) — broker disconnected?")
    except Exception as e:
        log(f"!! MQTT publish failed ({topic}): {e}")
    return False


def publisher_starten(cfg, log, *, pub_setzen, pub_holen, processed_len, hb_setzen):
    """AP2: eigener MQTT-Publish-Client (auch im poll-Modus) + 60s-Heartbeat (retained).

    Injektion pur: der Client-Halter bleibt der Dienst (pub_setzen/pub_holen sind
    seine self.pub-Zugriffe), die Heartbeat-Felder kommen als Callables
    (processed_len -> Zaehler, hb_setzen -> letzter_hb-Quittung). So sieht der
    Watchdog des Dienstes weiterhin denselben Client, den dieses Modul baut."""
    if not cfg.get("mqtt_publish", True):
        return
    # QS-K1: der stille praefix()-Rueckfall (hand-editierter Store) wird GENAU
    # HIER einmal laut — nicht in praefix() selbst, das liefe je Publish (Spam).
    _roh = (cfg.get("mqtt") or {}).get("topic_praefix")
    if _roh and praefix(cfg) == PRAEFIX_STD and _roh.strip("/") != PRAEFIX_STD:
        log(f"MQTT topic prefix in store is invalid ({str(_roh)[:40]!r}) — "
            f"falling back to '{PRAEFIX_STD}/' for ALL topics")
    try:
        import paho.mqtt.client as mqtt
        m = cfg["mqtt"]
        pub = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        pub_setzen(pub)
        if m.get("user"):
            pub.username_pw_set(m["user"], m.get("password", ""))
        # connect_async + loop_start statt connect(): paho baut die Verbindung im Netzwerk-Thread
        # auf UND reconnectet selbsttaetig. Vorher war ein Broker, der beim Dienststart kurz weg
        # war (Reboot-Reihenfolge!), ein Dauerzustand: connect() warf, self.pub blieb None, der
        # Heartbeat-Thread startete nie — und der Watchdog prueft 'self.pub and not is_connected()',
        # konnte pub=None also NIE melden. MQTT war still tot, bis jemand den Dienst neu startete.
        # Verbindungszustand ehrlich ins Log: connect_async kehrt SOFORT zurueck, die
        # Verbindung steht da noch nicht. *args, weil paho die Callback-Signaturen
        # zwischen Versionen geaendert hat — der Rueckgabewert wird hier nicht gebraucht.
        def _on_connect(client, userdata, *a):
            # a = (flags, reason_code[, properties]) — der Code steht in beiden
            # Callback-API-Versionen an Index 1 (paho 2.1.0 geprueft: VERSION2 liefert
            # ein ReasonCode mit .is_failure, VERSION1 einen MQTTErrorCode == 0).
            rc = a[1] if len(a) > 1 else None
            schlecht = getattr(rc, "is_failure", None)
            if schlecht is None:
                schlecht = str(rc) not in ("0", "Success")
            log(f"MQTT connection REJECTED: {rc} — check credentials/ACL." if schlecht
                else f"MQTT publisher connected to {m['host']}:{m.get('port', 1883)}")

        def _on_disconnect(client, userdata, *a):
            log("MQTT publisher disconnected — paho reconnects on its own.")
        pub.on_connect, pub.on_disconnect = _on_connect, _on_disconnect
        pub.reconnect_delay_set(min_delay=1, max_delay=60)
        pub.connect_async(m["host"], int(m.get("port", 1883)), 60)
        pub.loop_start()
        t_hb = topic(cfg, "heartbeat")            # #23: Praefix konfigurierbar, Default verifyd

        def hb():
            while True:
                try:
                    info = pub_holen().publish(t_hb, json.dumps(
                        {"ts": round(time.time(), 1), "status": "ok",
                         "processed": processed_len()}), retain=True)
                    # rc pruefen: bei getrenntem Broker wirft paho NICHT, es verwirft still
                    # (QoS 0). Ohne diese Pruefung war letzter_hb frisch, obwohl nichts ankam —
                    # der Watchdog haette den Ausfall nie bemerkt.
                    if info.rc == mqtt.MQTT_ERR_SUCCESS:
                        hb_setzen()
                except Exception:
                    pass
                time.sleep(60)
        threading.Thread(target=hb, daemon=True).start()
        log(f"MQTT publisher started, connecting to {m['host']} "
            f"({topic(cfg, 'erkennung')} + {t_hb})")
    except Exception as e:
        pub_setzen(None)
        log(f"MQTT publisher not available: {e}")


def publish_erkennung(cfg, pub, log, debug, entry):
    """Das Erkennungs-Urteil eines Events auf <praefix>/erkennung (an diesem Topic
    haengen HA-Automationen — Schluessel nur additiv aendern)."""
    t = topic(cfg, "erkennung")
    if mqtt_pub(pub, log, t, json.dumps({
            "eid": entry["eid"], "camera": entry["camera"], "ts": entry["ts"],
            # Areas Stufe 1: additives Feld, bestehende Schluessel unveraendert
            # (an diesem Topic haengen HA-Automationen).
            "areas": _areas_mod.kamera_areas(
                _areas_mod.normalisieren(cfg.get("areas")), entry["camera"]),
            "kategorie": entry["kategorie"],
            # "stufe" ADDITIV (.249, Kosinus-raus — User-Auflage 17.08.:
            # bestehende Schluessel byte-gleich, HA-Skripte duerfen nie
            # brechen; dasselbe Muster wie areas oben).
            "personen": [{"name": p, "cos": (entry["ours"].get(p) or {}).get("max"),
                          "win": (entry["ours"].get(p) or {}).get("win3s"),
                          "stufe": _vertrauen.stufe(
                              (entry["ours"].get(p) or {}).get("max"),
                              cfg.get("win_thresh"))}
                         for p in entry["bestaetigt"]]}, ensure_ascii=False)):
        debug(f"MQTT {t} -> {entry['eid']} cat={entry['kategorie']} "
              f"persons={entry['bestaetigt'] or '[]'}")


# ------------------------------------------------------- Szenen-Telegram + Transcode-Lauf
def telegram_melden(cfg, log, dry_alert, zustand, best_crop, clip_holen, ha_melden,
                    art, entry, personen=None):
    """Szenen-Telegram direkt aus verifyd (ersetzt die HA-MQTT-Automationen, 19.07.).
    art 'erkannt'|'unbekannt'; Modus telegram_modus: aus|ha|direkt|beide. Versand im
    Thread (Transcode+Upload blockieren den GPU-Lock nicht); Unbekannt zusaetzlich
    ueber telegram_cooldown gedrosselt (ersetzt die fehlerhafte HA-10-min-Sperre).

    Injektion: `zustand` ist das Drossel-Dict des Aufrufers (tg_unbekannt),
    `best_crop`/`clip_holen`/`ha_melden` seine Bild-/Clip-/HA-Quellen — die
    Live-Engine haengt hier mit eigenem Zustand und Burst-Clip an.

    SPRACH-STUFE 4 — GRENZE, BEWUSST (Bericht Stufe 4): die beiden Captions
    unten sind DEUTSCH ("… erkannt um …", "Unbekannte Person um … — niemand
    erkannt"). de->en waere eine bewusste TEXTAENDERUNG, nie Teil des
    Einzugs (dieselbe Regel wie die deutschen Alt-msgs im do_POST-Marker
    (b)) — sie bleiben literal, bis der User den Wortlaut entscheidet.
    Sprachfaehig ist hier nur der englische Video-Rueckfall-Zusatz."""
    sprache_aktivieren()          # Eintrittspunkt (b), s. sprache_aktivieren()
    modus = cfg.get("telegram_modus", "aus")
    if modus == "aus" or dry_alert:
        return
    if art == "unbekannt":
        now = time.time()
        if now - zustand.get("tg_unbekannt", 0.0) < cfg.get("telegram_cooldown", 600):
            log(f"{entry['eid']}: Telegram unknown throttled (cooldown)")
            return
        zustand["tg_unbekannt"] = now
    eid, camera = entry["eid"], entry["camera"]
    cam_name = camera.replace("_", " ")
    # Areas Stufe 1: die Caption nennt die Area(s) der Kamera — bei n:m ALLE,
    # alphabetisch (nur das ist wahr); '' ohne Zuordnung = Caption wie bisher.
    _ar = _areas_mod.melde_zusatz(cfg.get("areas"), camera)
    cam_name += f" · {_ar}" if _ar else ""
    t = datetime.datetime.fromtimestamp(entry.get("start") or entry["ts"]).strftime("%H:%M")
    if art == "erkannt":
        caption = f"✅ {cam_name}\n{' + '.join(personen or [])} erkannt um {t} (suslik)"
    else:
        caption = f"⚠️ {cam_name}\nUnbekannte Person um {t} — niemand erkannt (suslik)"
    event_dir = os.path.join(cfg["data_dir"], "events", eid.replace("/", "_"))
    crop = best_crop(event_dir, entry, personen or list(entry["ours"]))

    def job():
        try:
            if modus in ("direkt", "beide"):
                # User-Wunsch 25.07.: Bild ODER Video je Kanal waehlbar. "bild" spart das
                # komplette Transcoding (ffmpeg 720p) — auf schwacher Hardware der Unterschied
                # zwischen sofortiger und minutenspaeter Meldung. Vorgabe "video" = bisheriges
                # Verhalten. Faellt das Video aus, obwohl es gewollt war, steht das ab jetzt IN
                # der Meldung — der stille Bild-Rueckfall war der Grund, warum der ffmpeg-Defekt
                # aus Welle 3 erst durch die Beobachtung des Users auffiel (Fehlerklasse C).
                will_video = cfg.get("telegram_inhalt", "video") != "bild"
                video = clip_holen(eid) if will_video else None
                cap = caption + ("\n" + _sprache.t("meldung.video_ersatz.satz")
                                 if will_video and not video else "")
                ok = telegram_video(cfg, video, cap, crop)
                log(f"{eid}: Telegram {art} direct "
                    f"{'sent' if ok else 'FAILED'}"
                    + (" [video missing -> image]" if will_video and not video else "")
                    + (" [telegram_inhalt=bild]" if not will_video else ""))
            if modus in ("ha", "beide"):
                ha_melden(eid, camera, caption)
        except Exception as e:
            log(f"{eid}: Telegram {art} error: {e}")
    threading.Thread(target=job, daemon=True).start()


def telegram_ha_script(cfg, log, zustand, eid, camera, caption):
    """Weg A: das vorhandene HA-Script frigate_telegram_video via HA-REST-API ausloesen
    (HA transkodiert + versendet selbst). HA_URL/HA_TOKEN aus der .env.
    `zustand` traegt die 1x/h-Warn-Drossel (ha_warn) des Aufrufers."""
    ha_url, ha_tok = os.environ.get("HA_URL"), os.environ.get("HA_TOKEN")
    chat = (cfg.get("telegram") or {}).get("chat_id")
    if not ha_url or not ha_tok or not chat:
        # Frueher ein stummes return: telegram_modus stand auf "ha", die UI zeigte Telegram
        # als aktiv, und es kam nie etwas an — ohne eine einzige Logzeile. Gedrosselt auf
        # 1x/h, damit ein dauerhaft unvollstaendiges Setup das Log nicht flutet.
        fehlt = ", ".join(n for n, v in (("HA_URL", ha_url), ("HA_TOKEN", ha_tok),
                                         ("telegram.chat_id", chat)) if not v)
        if time.time() - zustand.get("ha_warn", 0) > 3600:
            zustand["ha_warn"] = time.time()
            log(f"telegram_modus=ha, but {fehlt} is missing — NO Telegram will be sent.")
        return
    body = json.dumps({"event_id": eid, "camera": camera,
                       "chat_id": str(chat), "caption": caption}).encode()
    req = urllib.request.Request(ha_url + "/api/services/script/frigate_telegram_video",
                                 data=body, method="POST",
                                 headers={"Authorization": f"Bearer {ha_tok}",
                                          "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=30)
        log(f"{eid}: Telegram triggered via HA script")
    except Exception as e:
        log(f"{eid}: HA script call failed: {e}")


def transcode_lauf(cmd, timeout, lock, procs):
    """ffmpeg-Transcode als EIGENE Prozessgruppe, registriert in `procs`.
    W3-Review-Fund: neustart() ersetzt per execv nur das Prozess-Image — ein laufendes
    ffmpeg-Kind ueberlebte, schrieb weiter in seine .part, und der neue Prozess startete
    einen ZWEITEN Bau auf denselben Namen -> gemeinsame Inode, dauerhaft kaputte Kopie
    ohne Logzeile. Registrierung + killpg in neustart() schliessen das; der eindeutige
    .part-Name je Versuch (s. Aufrufer) ist der doppelte Boden.
    `lock`/`procs` definiert der Dienst (eine Lock-Quelle) und reicht sie herein."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True)
    with lock:
        procs.add(p)
    try:
        try:
            out, err = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except Exception:
                pass
            out, err = p.communicate()
        return subprocess.CompletedProcess(cmd, p.returncode, out, err)
    finally:
        with lock:
            procs.discard(p)


def transcodes_killen(lock, procs):
    """Alle registrierten ffmpeg-Transcodes hart beenden — VOR execv (neustart)."""
    with lock:
        laufend = list(procs)
    for p in laufend:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except Exception:
            pass
        try:
            p.wait(timeout=5)
        except Exception:
            pass


def telegram_clip(cfg, log, transcode, kommandos, encoder, eid):
    """Kleines H.264-720p-Video (max 60 s, crf 28 CPU / cq 34 NVENC / qp 28 VAAPI) fuers
    Telegram-Bot-Limit (50 MB). Die 1080p-Browser-Kopie ist dafuer zu gross (teils >300 MB).
    Encoder aus video_encoder() (NVENC/VAAPI geprobt, sonst CPU), Fallback bleibt CPU;
    Quelle ist der bereits geladene Original-Clip im Cache.
    Injektion: `transcode` = der registrierte Lauf des Dienstes (transcode_lauf mit
    seiner Registry), `kommandos`/`encoder` = transcode_kommandos/video_encoder
    (Encoder-Wahl bleibt beim Dienst, bis der Transcode-Baustein sie auszieht)."""
    base = os.path.join(cfg["data_dir"], "clips", eid.replace("/", "_"))
    # Aufloesung waehlbar 720/480 (User 04.08.), gilt fuer Face UND
    # Person (gemeinsamer Weg); Cache-Name traegt die Hoehe, sonst
    # wuerde nach einem Umstellen die alte Datei ausgeliefert.
    hoehe = int(cfg.get("telegram_hoehe", 720))
    if hoehe not in (720, 480):
        hoehe = 720
    src, dst = base + ".mp4", base + f"_tg{hoehe}.mp4"
    if os.path.exists(dst):
        return dst
    if not os.path.exists(src):
        return None
    # Eindeutiger .part-Name je Versuch (endet auf .part -> Retention raeumt Waisen weg);
    # `-f mp4` steckt in transcode_kommandos(), s. dort: ffmpeg erkennt an ".part" kein Format
    # und bricht ab. Genau daran ist das Telegram-Video seit Welle 3 gescheitert — User-Meldung
    # 25.07.: "bei Telegram bekomme ich im Moment nur ein Bild und kein Video mehr". Der
    # Rueckfall auf das Bild passierte still, waehrend "gesendet" im Log stand.
    part = f"{dst}.{os.getpid()}-{threading.get_ident()}.part"
    # W3/Issue #4: q_hw (NVENC) 28->34 — die HW-Quantizer sind nicht auf die crf-Skala
    # kalibriert; cq 28 lieferte 3,4-3,7x groessere Dateien als der CPU-Pfad davor. cq 34 ist
    # SSIM-gemessen quality- UND size-matched zu crf 28 (Feldbericht Issue #4, RTX 3060). VAAPI bleibt bei
    # qp 28: dort ist die Qualitaets-Seite UNGEMESSEN (scale_vaapi-SSIM-Deckel, Issue §3) —
    # Telegram-Qualitaet nicht blind verstellen. CPU-Wert unveraendert.
    # N8a (RTX 2060 an 2 eigenen Clips + Feld-Sweep aus Issue #4): am FULL-HW-Pfad ist cq 34
    # nicht mehr size-matched (scale_cuda-Shift, s. transcode_kommandos-Docstring); Paritaets-
    # cq content-abhaengig 34-37 -> 36 als konservativer Mittelweg NUR fuer nvenc-voll.
    hw, cpu = kommandos(src, part, hoehe, 34, 28, dauer_s=60,
                        q_vaapi=28, q_hw_voll=36)
    try:
        r = transcode(hw, 300) if hw else None
        if r is None or r.returncode != 0 or not os.path.exists(part):
            if r is not None:
                # HW lief und scheiterte, CPU rettet gleich: SICHTBAR machen (Review-Fund —
                # sonst waere der Laufzeit-Rueckfall genauso still wie der alte Start-Rueckfall,
                # waehrend Selbstcheck und QS-Gate weiter HW-Betrieb behaupten).
                e1 = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
                log(f"{eid}: HW transcode ({encoder()[0]}) failed "
                    f"(rc={r.returncode}) — CPU takes over: {e1[-1] if e1 else 'no stderr'}")
            r = transcode(cpu, 600)
        if r.returncode == 0 and os.path.exists(part) and os.path.getsize(part) > 0:
            os.replace(part, dst)
        else:                     # rc des Fallbacks wurde frueher verworfen -> Alert ohne Video,
            err = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()   # ohne Grund
            log(f"{eid}: Telegram clip failed (rc={r.returncode}): "
                f"{' | '.join(err[-2:]) if err else 'no stderr output'}")
            try:
                os.remove(part)
            except OSError:
                pass
    except Exception as e:
        log(f"{eid}: Telegram clip failed: {e}")
        try:
            os.remove(part)
        except OSError:
            pass
    return dst if os.path.exists(dst) else None


# ------------------------------------------------- Notifications-Settings (Reiter + Tests)
def notif_speichern(cfg, d, *, log, whitelist, store_pfad, store_laden,
                    store_schreiben, maskieren, neustart):
    """SaveConfig fuer den Notifications-Reiter: die Kanal-Bloecke (telegram/pushover/mqtt inkl. Secrets),
    die Melde-Schalter/Cooldowns und alert_kategorien atomar in den JSON-Store. Getrennt von
    config_schreiben, weil die generische Whitelist keine Strings/verschachtelten Dicts kann.
    Secrets: LEERES Feld = bestehenden Wert behalten (nie mit Leer ueberschreiben); Audit maskiert.
    Der Store ersetzt ganze Top-Level-Keys -> die Kanal-Dicts werden KOMPLETT geschrieben.
    Injektion: Whitelist + Store-IO + Maskierung + Neustart kommen vom Dienst
    (die EINEN Schreibwege unter _cfg_lock, s. verifyd)."""
    store = store_laden(cfg)
    audit = {}

    def keep(neu, alt):                                # leeres Feld -> Bestand behalten
        neu = str(neu if neu is not None else "").strip()
        return neu if neu else (alt or "")

    # 1) Skalare/Enum/Bool ueber die bestehende Whitelist validieren
    for key in ("telegram_modus", "telegram_inhalt", "telegram_cooldown", "alert_cooldown",
                "anwesenheit_push", "anwesenheit_cooldown", "mqtt_publish", "szene_karenz_s",
                "alert_stil"):                    # .249 Kosinus-raus (Worte/Worte+Zahlen)
        if key not in d:
            continue
        typ, lo, hi, _ = whitelist[key]
        try:
            if typ is list:
                w = str(d[key]).strip()
                if w not in lo:
                    return False, f"'{key}': erlaubt {', '.join(lo)}"
            elif typ is bool:
                w = str(d[key]).lower() in ("1", "true", "ja", "on")
            else:
                w = typ(d[key])
                if not (lo <= w <= hi):
                    return False, f"'{key}': erlaubt {lo}–{hi}"
        except Exception:
            return False, f"'{key}': ungueltiger Wert"
        store[key] = w
        audit[key] = w

    # 2) alert_kategorien (Liste, nicht in der Whitelist)
    if "alert_kategorien" in d:
        erlaubt = {"widerspruch", "frigate_nur", "wir_nur", "beide_unknown",
                   "erkannt", "fremd_verdacht", "unbekannt_schwach"}
        kats = [k for k in (d.get("alert_kategorien") or []) if k in erlaubt]
        store["alert_kategorien"] = kats
        audit["alert_kategorien"] = kats

    # (Ein basis_url-Feld aus .200 wurde mit .201 wieder entfernt — ein etwaiger
    # Store-Rest bleibt wirkungslos liegen, kein Leser greift mehr darauf zu.)

    # 3) Kanal-Bloecke (kompletter Dict-Ersatz; Secrets maskiert im Audit)
    a = cfg.get("telegram") or {}
    tg = {"bot_token": keep(d.get("telegram_bot_token"), a.get("bot_token")),
          "chat_id": keep(d.get("telegram_chat_id"), a.get("chat_id"))}
    store["telegram"] = tg
    audit["telegram"] = {"bot_token": maskieren(tg["bot_token"]), "chat_id": tg["chat_id"]}

    a = cfg.get("pushover") or {}
    po = {"token": keep(d.get("pushover_token"), a.get("token")),
          "user": keep(d.get("pushover_user"), a.get("user"))}
    store["pushover"] = po
    audit["pushover"] = {"token": maskieren(po["token"]), "user": maskieren(po["user"])}

    a = cfg.get("mqtt") or {}
    mq = dict(a)
    mq["host"] = keep(d.get("mqtt_host"), a.get("host"))
    try:
        mq["port"] = int(d.get("mqtt_port") or a.get("port") or 1883)
    except Exception:
        mq["port"] = a.get("port") or 1883
    mq["user"] = keep(d.get("mqtt_user"), a.get("user"))
    mq["password"] = keep(d.get("mqtt_password"), a.get("password"))
    # #23: Topic-Praefix — kein Secret, kein keep(): was im Feld steht, wird
    # gespeichert; leer = Default (verifyd), so laesst sich ein gesetzter
    # Praefix auch wieder zuruecknehmen. Ungueltiges wird HIER abgewiesen
    # (VOR dem Store-Write, der Publisher bleibt unberuehrt); ein trotzdem
    # hand-editierter Fremdwert faellt zur Laufzeit in praefix() auf Default.
    if "mqtt_topic_praefix" in d:
        ok_p, tp = praefix_pruefen(d.get("mqtt_topic_praefix"))
        if not ok_p:
            return False, tp
        mq["topic_praefix"] = tp
    store["mqtt"] = mq
    audit["mqtt"] = {"host": mq["host"], "port": mq["port"],
                     "user": maskieren(mq["user"]), "password": maskieren(mq["password"])}
    if "topic_praefix" in mq:                      # nur wenn (jetzt) vorhanden — Bestand
        audit["mqtt"]["topic_praefix"] = mq["topic_praefix"]   # bleibt byte-identisch

    p = store_pfad(cfg)
    store_schreiben(p, store)      # atomar + fsync, unter _cfg_lock (5 Schreibwege)
    with open(os.path.join(cfg["data_dir"], "config", "config_audit.jsonl"), "a") as f:
        f.write(json.dumps({"ts": round(time.time(), 1), "notif": audit}, ensure_ascii=False) + "\n")
        f.flush()
    log("NOTIFICATIONS changed via UI (secrets masked) — restart after the current analysis")
    neustart("Notifications")
    return True, "gespeichert — Dienst startet gleich neu"


def notif_test(cfg, kanal, d):
    """Echter Test-Versand je Kanal mit den AKTUELLEN Formularwerten (leeres Feld -> gespeicherter Wert).
    Umgeht bewusst Drosseln/Modus-Gates. Gibt (ok, msg) zurueck; Secrets NIE in die Meldung.

    SPRACH-STUFE 4: der VERSENDETE Text ist sprachfaehig (er landet am Handy
    des Nutzers). Die (ok, msg)-RUECKGABE bleibt englisch — sie ist eine
    Fachschicht-msg des Notifications-Reiters und faellt damit unter
    Stufe-2-Marker (a) im do_POST-Dispatcher: ihr Einzug ist ein eigener Zug
    je Modul, kein Meldetext."""
    sprache_aktivieren()          # Eintrittspunkt (b), s. sprache_aktivieren()

    def keep(neu, alt):
        neu = str(neu if neu is not None else "").strip()
        return neu if neu else (alt or "")

    try:
        if kanal == "pushover":
            a = cfg.get("pushover") or {}
            tok, usr = keep(d.get("pushover_token"), a.get("token")), keep(d.get("pushover_user"), a.get("user"))
            if not tok or not usr:
                return False, "token/user missing"
            ok = push({"pushover": {"token": tok, "user": usr}}, "suslik",
                      _sprache.t("meldung.test.satz"),
                      herkunft="manuell")
            return (True, "Pushover: sent ✓") if ok else (False, "Pushover rejected it (check token/user)")
        if kanal == "telegram":
            a = cfg.get("telegram") or {}
            tok, chat = keep(d.get("telegram_bot_token"), a.get("bot_token")), keep(d.get("telegram_chat_id"), a.get("chat_id"))
            if not tok or not chat:
                return False, "bot_token/chat_id missing"
            ok = telegram_video({"telegram": {"bot_token": tok, "chat_id": chat}},
                                None, _sprache.t("meldung.test.satz"),
                                herkunft="manuell")
            return (True, "Telegram: sent ✓") if ok else (False, "Telegram rejected it (check bot_token/chat_id)")
        if kanal == "mqtt":
            a = cfg.get("mqtt") or {}
            host = keep(d.get("mqtt_host"), a.get("host"))
            if not host:
                return False, "host missing"
            try:
                port = int(d.get("mqtt_port") or a.get("port") or 1883)
            except Exception:
                port = 1883
            usr, pw = keep(d.get("mqtt_user"), a.get("user")), keep(d.get("mqtt_password"), a.get("password"))
            # #23: der Test prueft mit dem Praefix aus dem FORMULAR (Feld fehlt ->
            # gespeicherter Wert) — Ungueltiges wird abgewiesen, BEVOR verbunden wird.
            ok_p, tp = praefix_pruefen(d.get("mqtt_topic_praefix", a.get("topic_praefix")))
            if not ok_p:
                return False, tp
            t = f"{tp or PRAEFIX_STD}/test"
            import paho.mqtt.client as mqtt
            c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            if usr:
                c.username_pw_set(usr, pw)
            c.connect(host, port, 10)
            c.loop_start()
            # .163: auch der Test-Publish traegt sein Herkunfts-Feld — er
            # geht ueber einen eigenen Client, also wird das Kennzeichen
            # hier ausdruecklich gesetzt (dieselbe EINE Quelle).
            info = c.publish(t, mqtt_herkunft(
                json.dumps({"test": True, "ts": round(time.time(), 1)}),
                "manuell"))
            info.wait_for_publish(timeout=5)
            c.loop_stop()
            c.disconnect()
            return True, f"MQTT: connected {host}:{port} + published {t} ✓"
    except Exception as e:
        return False, f"{kanal} error: {str(e)[:90]}"
    return False, "unknown channel"
