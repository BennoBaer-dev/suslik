#!/usr/bin/env python3
"""verifyd — Face-Verify-Dienst v0.1 (Konzept: verify-dienst-konzept.md)

Prueft Frigates Personen-Zuordnung (sub_label) unabhaengig mit buffalo_l nach:
  Trigger (mqtt + Nachhol-Sweep bei Start/Reconnect; alternativ poll) -> Record-Clip
  -> analyze.py (GPU) -> Deckungs-Urteil (Frigate vs. wir, EINE Skala) -> deckung.jsonl
  -> Pushover bei Widerspruch -> Mini-Webview (read-only). Clip-Cache: Retention
  clip_retention_d Tage (User-Entscheidung 16.07.).

Read-only gegen Frigate. Keine Mutationen. Absturzsicher: jedes Event wird sofort
nach Verarbeitung geflusht protokolliert; Neustart ueberspringt Verarbeitetes.

Aufruf:
  verifyd.py --config verifyd.yaml            # Dienst (Trigger + Web)
  verifyd.py --config verifyd.yaml --once EID # ein Event verarbeiten (Test), dann Ende
  Optionen: --dry-alert (Alert nur loggen, nicht senden)
"""
import argparse, collections, datetime, html, json, math, os, re, select, signal, subprocess, sys, threading, time
import urllib.request, urllib.parse, urllib.error, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import yaml

from core.pfade import WURZEL as HERE, VERIFYD_PFAD   # M0-Anker (Falle 0): eine Pfad-Quelle
from core import areas as _areas_mod                  # Areas Stufe 1 (Sicht + Meldetext, 30.07.)
from core import registry as _reg                     # Dateinamen-Vertrag (Issues #11/#12)
from core import kette as _kette                      # Modulumbau R2: die Erkennungskette (Default-Kette)
from core import melden as _melden                    # Modulumbau R3: die Meldewege (Live-Andock-API)
# Oeffentliche Projekt-Doku (GitHub). Lokale Arbeitsnotizen des Autors enthalten interne
# IPs + Zugaenge und duerfen NICHT ueber das UI ausgeliefert werden -> System-Seite + /doc zeigen aufs Repo.
DOCS_URL = "https://github.com/BennoBaer-dev/suslik"


def suslik_version():
    """Feste Versionsnummer aus der VERSION-Datei neben dem Code (ins Image gebacken, git-getaggt).
    'dev' wenn keine da (roher Lauf ohne Release). So weiss jeder laufende Container, WELCHE Version er ist."""
    try:
        with open(os.path.join(HERE, "VERSION")) as _f:
            return _f.read().strip() or "dev"
    except Exception:
        return "dev"


os.environ.setdefault("SUSLIK_VERSION", suslik_version())   # Docker-ENV gewinnt, sonst VERSION-Datei


def _version_neuer(tag, aktuell):
    """True, wenn ein Release-Tag (z.B. 'v0.1.0.28') NEUER ist als die laufende Version (#53).
    Beide Seiten tolerant zerlegt; unlesbar/leer -> False (nie einen falschen Hinweis zeigen)."""
    def teile(s):
        s = re.sub(r"^[vV]", "", str(s or "").strip())
        # Alpha-Release (30.07.): Namens-Suffix wie '-alpha' faellt fuer den VERGLEICH
        # weg — sonst koennte genau die Alpha-Installation nie einen Update-Hinweis
        # sehen (int('92-alpha') scheiterte -> Vergleich immer False).
        s = re.sub(r"[-+].*$", "", s)
        try:
            t = [int(x) for x in s.split(".") if x != ""]
        except ValueError:
            return None
        return t or None
    t, a = teile(tag), teile(aktuell)
    if not t or not a:
        return False
    n = max(len(t), len(a))
    return t + [0] * (n - len(t)) > a + [0] * (n - len(a))


# ------------------------------------------------------------------ Config
def _config_store_pfad(cfg):
    """Phase 2 (Docker-Richtung, User 21.07.): UI-geaenderte Werte liegen in einem JSON-Store
    <data_dir>/config.json, NICHT mehr per Zeilenersatz in der yaml. Die yaml ist die Basis
    (Defaults + Secrets via ${VAR}); der Store ueberlagert sie mit den Whitelist-Werten, die
    NUR ueber die UI/SaveConfig geschrieben werden (validiert). Kein ${VAR}-Risiko, kein
    kaputter yaml-Kommentar. Live-Reload + reine Env-Vars fuer Secrets kommen in Phase 4 (Docker)."""
    return os.path.join(cfg.get("data_dir") or os.path.join(HERE, "verify_data"), "config", "config.json")


def _lade_config_store(cfg):
    p = _config_store_pfad(cfg)
    if os.path.exists(p):
        try:
            with open(p) as f:                 # Datei sicher schliessen (frueher: offener Handle)
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except Exception as e:
            # NICHT still zu {} degradieren: der naechste Schreiber wuerde den Bestand ueberbuegeln.
            # Laut auf stderr (landet in `docker logs`) — hier gibt es noch kein svc.log().
            sys.stderr.write(f"[suslik] WARN: config store {p} unreadable ({e}) — "
                             f"yaml defaults apply; do NOT let the store be overwritten!\n")
    return {}


# Sechs Wege schreiben den Config-Store (config_schreiben, notif_speichern, config_wiederherstellen,
# Setup-Wizard, Kamera-Blatt, Areas) — teils aus parallelen HTTP-Threads. Ohne gemeinsames Lock ist der
# Read-Modify-Write ein Race (letzter gewinnt, Aenderung des anderen weg), und mit dem FESTEN
# tmp-Namen "<p>.tmp" haetten sich zwei Schreiber gegenseitig die halbfertige Datei umbenannt.
# EHRLICH (Widerleger .91): das Lock deckt hier nur das SCHREIBEN; die fuenf Alt-Wege lesen den
# Store weiter ungeschuetzt davor (Race bleibt dort, entschaerft durch den folgenden neustart).
# Der Areas-Weg (.92, einziger OHNE Neustart) haelt als erster das Lock um Lesen+Aendern+Schreiben —
# deshalb RLock (die verschachtelte Sperre in _store_schreiben darf nicht klemmen); die Alt-Wege
# auf denselben Griff umzustellen ist als Task notiert.
_cfg_lock = threading.RLock()


def _store_schreiben(p, store):
    """Config-Store atomar ablegen: pid-eigene tmp + flush + fsync + os.replace, unter _cfg_lock.
    Fehler werden NICHT verschluckt — der Aufrufer meldet sie."""
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = f"{p}.tmp-{os.getpid()}"
    with _cfg_lock:
        try:
            with open(tmp, "w") as f:
                json.dump(store, f, ensure_ascii=False, indent=1)
                f.flush()
                os.fsync(f.fileno())           # ohne fsync kann nach Stromausfall eine LEERE Datei
            os.replace(tmp, p)                 # unter dem gueltigen Namen stehen
        except Exception:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise


def _mask_secret(s):
    """Secret fuers Audit-Log NIE im Klartext: nur 'set' vs leer."""
    return "•••• set" if str(s or "") else ""


def _live_guards_aktiv(cfg):
    """Autostart-Praedikat des Live-Supervisors: mindestens ein enabled-Guard
    im STORE (frisch gelesen — Hand-Edits zaehlen, nicht die Prozess-Sicht).

    Widerleger phase34 MUSS-1: die alte Fassung urteilte mit roher bool()-
    Wahrheit (`g.get("enabled")`) — `"enabled": "false"` hielt der Supervisor
    fuer AN, die Engine (livewache._bool_lesen via guards_lesen) fuer AUS.
    Folge gemessen: Spawn -> "nothing to do" -> Fehlstart-Kette -> alle
    15 min ein Stoerungs-Push, fuer einen ausdruecklich abgeschalteten
    Waechter. EIN Praedikat fuer eine Frage (K3): dieselbe _bool_lesen-
    Wahrheit wie die Engine, kein Nachbau. Log dabei stumm — der Takt fragt
    alle 5 s, die LAUTE Meldung eines ungueltigen Werts gehoert der Engine
    (guards_lesen beim Start); der Default False ist derselbe."""
    from core import livewache as _lw
    with _cfg_lock:
        store = _lade_config_store(cfg)
    blk = (store.get("live") or {}).get("guards") or {}
    return any(isinstance(g, dict)
               and _lw._bool_lesen(g.get("enabled"), False, lambda z: None,
                                   f"live.guards.{name}.enabled")
               for name, g in blk.items())


def _pool_eid_karte(data_dir):
    """/heute-Blick in den Unbekannt-Pool -> (eid2uid, uid_members): Event-ID
    zu U-Nummer plus Mitglieder je Identitaet (fuer "seen Nx before").

    Widerleger phase34 MUSS-2: der /heute-Handler trug hier einen DRITTEN
    Streu-Parser derselben Datei — `{"members": 5}` warf `TypeError: 'int'
    object is not iterable` UNGEFANGEN in do_GET, die Seite starb (gemessen),
    waehrend der Harnisch nur das tolerante Modul prueft (K1). Deckungs-
    Regel: EIN Leser fuer die Datei (core.unbekanntpool._cluster_lesen —
    liefert nur Dicts) + Toleranz JE Cluster: eine kaputte Zeile kostet nur
    sich selbst, nie die Seite. Semantik unveraendert: objekt-Zeilen fallen
    raus (nie als "Unknown N" anbieten, 25.07.), Archiv-Cluster bleiben
    drin (Vorbesuchs-Zaehlung), members nur als Liste."""
    from core import unbekanntpool as _ubp
    eid2uid, uid_members = {}, {}
    for _d in _ubp._cluster_lesen(data_dir):
        try:
            _u = _d.get("uid") or _d.get("id")
            if not _u or _d.get("objekt"):
                continue
            _mem = _d.get("members")
            if not isinstance(_mem, list):
                _mem = []
            uid_members[_u] = _mem            # Mitglieder BEHALTEN, nicht nur
            for _m in _mem:                   # zaehlen: "seen Nx before"
                _s = str(_m)                  # braucht deren ZEITEN
                eid2uid.setdefault(_s, _u)
                # Top-3-Sammlung haengt ~2/~3 an die Event-ID — die Karte
                # matcht ueber die BASIS-Event-ID des Durchgangs
                eid2uid.setdefault(_s.split("~")[0], _u)
        except (TypeError, ValueError, AttributeError):
            continue
    return eid2uid, uid_members


def _migrate_layout(dd):
    """Einmalige, idempotente Migration flach -> Unterordner (config/ faces/ clips/ learn/ state/).
    `shutil.move` = Rename auf demselben Dateisystem (auch fuer die 77G clips instant, kein Kopieren).
    Nur wenn Quelle da UND Ziel fehlt -> gefahrlos bei jedem Start. Frisch = nur die Basisordner."""
    import shutil

    def mv(src, dst):
        s, d = os.path.join(dd, src), os.path.join(dd, dst)
        if os.path.exists(s) and not os.path.exists(d):
            os.makedirs(os.path.dirname(d) or dd, exist_ok=True)
            shutil.move(s, d)
    mv("refs", "faces")                                   # 1) ganze Verzeichnisse umbenennen
    mv("cache", "clips")
    mv("anlernen", "learn")
    mv("enroll", os.path.join("learn", "enroll"))         # 2) enroll unter learn
    # refcache bleibt in clips/ (kam mit cache->clips mit; geteilt mit analyze SCRATCH_DIR)
    for f in ("deckung.jsonl", "ground_truth.jsonl", "sublabel_writes.jsonl", "qs_bericht.json", "archiv"):
        mv(f, os.path.join("state", f))                   # 4) lose Logs/State -> state/
    for f in ("config.json", "config_audit.jsonl"):
        mv(f, os.path.join("config", f))                  # 5) Config -> config/
    for sub in ("config", "faces", "clips", "events", "learn", "state", "backups"):
        os.makedirs(os.path.join(dd, sub), exist_ok=True)  # 6) Basisordner sicherstellen (frisch)


def _placement_hw_key():
    """Fingerabdruck der Rechen-Hardware+Runtime fuers klebrige Placement: aendert sich
    CPU, Geraetesatz, onnxruntime oder die suslik-Version, wird neu gebenchmarkt."""
    import glob as _glob
    cpu = ""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip(); break
    except Exception:
        pass
    try:
        import onnxruntime as _ort
        ov = _ort.__version__
    except Exception:
        ov = "?"
    # /dev/kfd + /dev/nvidia*: ohne sie aendert ein AMD-/Nvidia-GPU-Wechsel den Key nicht und
    # ein altes Placement bliebe kleben (Inventur-Fund 31.07.). Key-Aenderung invalidiert
    # gespeicherte Placements einmalig — gewollt, naechster Boot misst neu.
    devs = sorted(_glob.glob("/dev/dri/renderD*")) + sorted(_glob.glob("/dev/accel/accel*")) \
         + sorted(_glob.glob("/dev/kfd")) + sorted(_glob.glob("/dev/nvidia[0-9]*"))
    return f"{cpu}|{','.join(devs)}|ort{ov}|{os.environ.get('SUSLIK_VERSION', '')}"


# Issue #21 (Tokn59, i5-5300U 2C/4T): die Wanduhr-Selbstmessung ist ein ZWEITER voller
# Analyse-Prozess neben dem Live-Worker. Sie darf nur laufen, wo ZWEI Analyse-Akteure
# nebeneinander passen — jeder Akteur besteht strukturell aus zwei nebenlaeufigen
# Bausteinen (ffmpeg-Decode + Inferenz, s. decode.FrameIter). Die 4 ist damit eine
# STRUKTUR-UNTERGRENZE (2 Akteure x 2 Bausteine, ein Axiom aus der Architektur),
# KEINE Messung — der Dienstprozess (Poll/MQTT/UI/Alerts) laeuft obendrauf und ist
# darin nicht einmal eingerechnet. Unter der Grenze ist die Messung Minuten Volllast
# fuer eine blosse Prognose-Komfortzahl UND misst dort vor allem die eigene
# Verdraengung statt der Maschine — ueberspringen, LAUT (K1: Startlog + /health
# sagen warum). Wer es auf einer kleinen Maschine BEWUSST will (z. B. nachts),
# senkt `wanduhr_min_kerne` in den Settings (CONFIG_WHITELIST) — ein Axiom darf
# keinen Nutzer endgueltig aussperren (Nachbesserung W2).
WANDUHR_AKTEURE = 2                # Live-Analyse + Mess-Roundtrip
WANDUHR_BAUSTEINE_JE_AKTEUR = 2    # ffmpeg-Decode + Inferenz je Akteur nebenlaeufig
WANDUHR_MIN_KERNE = WANDUHR_AKTEURE * WANDUHR_BAUSTEINE_JE_AKTEUR


def _cpu_quote():
    """cgroup-CPU-Quote (docker --cpus / LXC cpulimit): os.sched_getaffinity sieht
    sie NICHT — ein Container mit cpus:1.0 auf einem 12-Kern-Wirt traegt die volle
    Affinitaetsmaske, darf aber nur 1 CPU-Sekunde je Sekunde verbrauchen
    (Nachbesserung W2: die Kern-Zaehlung war quota-blind). Rueckgabe: nutzbare
    GANZE CPUs laut Quote (abgerundet — konservativ, es geht um eine
    Ueberspringen-Entscheidung) oder None, wenn keine Quote gesetzt/lesbar ist.
    cgroup v2 (`cpu.max`: '<quota> <period>' oder 'max ...'), v1 als Rueckfall."""
    try:
        with open("/sys/fs/cgroup/cpu.max") as f:
            teile = f.read().split()
        if teile and teile[0] != "max":
            periode = int(teile[1]) if len(teile) > 1 else 100000
            return max(1, int(teile[0]) // max(1, periode))
    except (OSError, ValueError, IndexError):
        pass
    try:                                                   # cgroup v1
        q = int(open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us").read())
        p = int(open("/sys/fs/cgroup/cpu/cpu.cfs_period_us").read())
        if q > 0 and p > 0:
            return max(1, q // p)
    except (OSError, ValueError):
        pass
    return None


def _phys_kerne():
    """Physische Kerne unter den ERLAUBTEN CPUs (cgroup/LXC-Maske, Muster
    face_audit._so_mit_threads): SMT-Geschwister zaehlen EINMAL — Hyperthreads sind
    keine eigenen Rechenwerke, fuer 'traegt die Maschine zwei volle Analyse-Akteure?'
    zaehlen nur Kerne (der 2C/4T-Ausloeser meldet cpu_count=4, hat aber 2). Topologie
    aus /sys — auch im LXC/Container die Wirts-Nummerierung, dieselbe wie die
    Affinitaetsmaske. Nicht lesbar -> konservativ erlaubte/2 aufgerundet (SMT-2
    angenommen): lieber eine Messung zu viel LAUT ueberspringen als eine kleine
    Maschine minutenlang saettigen. Eine cgroup-CPU-Quote (docker --cpus) deckelt
    das Ergebnis zusaetzlich (_cpu_quote) — mehr Kerne als Quote sind fuer die
    Frage 'passen zwei Analyse-Akteure nebeneinander?' nicht real vorhanden."""
    try:
        erlaubt = os.sched_getaffinity(0)
    except AttributeError:                                 # nur ausserhalb Linux
        erlaubt = set(range(os.cpu_count() or 1))
    kerne = set()
    n = None
    for c in sorted(erlaubt):
        try:
            with open(f"/sys/devices/system/cpu/cpu{c}/topology/thread_siblings_list") as f:
                kerne.add(f.read().strip())     # Geschwister tragen dieselbe Liste ->
        except OSError:                         # ein Set-Eintrag je physischem Kern
            n = max(1, (len(erlaubt) + 1) // 2)
            break
    if n is None:
        n = max(1, len(kerne))
    quote = _cpu_quote()
    return min(n, quote) if quote is not None else n


def placement_aufloesen(cfg):
    """P4 (0.1.0.42): 'openvino:AUTO' -> konkretes Placement, EINMAL per Mini-Benchmark
    entschieden und in state/placement.json festgehalten (klebrig; neu nur bei HW-/
    Versionswechsel via hw_key). Wahl nach den P4.0-Gate-Kriterien LIVE auf dem System:
    NPU bindet + cpu<=3 ms/Inf + wall <= GPU-wall*1,5  -> openvino:MIXED (Recognition NPU,
    Detektor GPU — bestehende MIXED-Mechanik in face_audit._to_backend); sonst GPU bindet
    -> openvino:GPU; sonst cpu. Startup-Deckel ~30 s (mit warmem OV-Cache Sekunden).
    Rueckgabe: (backend_str, info_dict) — info geht in Selbstcheck + /health."""
    import time as _time
    pfad = os.path.join(cfg["data_dir"], "state", "placement.json")
    key = _placement_hw_key()
    try:
        with open(pfad) as f:
            alt = json.load(f)
        if alt.get("hw_key") == key and alt.get("backend"):
            return alt["backend"], {**alt, "quelle": "sticky"}
    except Exception:
        pass
    from face_audit import MODELLE, _ort_session
    onnx = next((v["onnx"] for v in MODELLE.values()
                 if v.get("onnx") and os.path.exists(v["onnx"])), None)
    cache = os.environ.get("OV_CACHE_DIR",
                           os.path.join(cfg["data_dir"], "clips", "ov_cache_models"))
    mess, t_start = {}, _time.perf_counter()
    if onnx:
        import numpy as _np
        x = _np.zeros((1, 3, 112, 112), _np.float32)
        for dev in ("NPU", "GPU"):
            if _time.perf_counter() - t_start > 25:          # Startup-Deckel: Rest der Kette faellt aus
                mess[dev] = {"bind": False, "grund": "startup budget exhausted"}
                continue
            try:
                s = _ort_session("openvino", dev, onnx, cache)
                if "OpenVINOExecutionProvider" not in s.get_providers():
                    mess[dev] = {"bind": False}
                    continue
                nm = s.get_inputs()[0].name
                s.run(None, {nm: x})                          # Kompilat/Warmup
                t0 = os.times(); w0 = _time.perf_counter()
                for _ in range(10):
                    s.run(None, {nm: x})
                w1 = _time.perf_counter(); t1 = os.times()
                mess[dev] = {"bind": True,
                             "wall_ms": round((w1 - w0) * 100.0, 1),
                             "cpu_ms": round(((t1.user - t0.user) + (t1.system - t0.system)) * 100.0, 2)}
            except Exception as e:
                mess[dev] = {"bind": False, "grund": str(e)[:80]}
    npu, gpu = mess.get("NPU", {}), mess.get("GPU", {})
    if (npu.get("bind") and npu.get("cpu_ms", 99) <= 3.0
            and npu.get("wall_ms", 9e9) <= (gpu.get("wall_ms") or 9e9) * 1.5):
        wahl = "openvino:MIXED"
    elif gpu.get("bind"):
        wahl = "openvino:GPU"
    else:
        wahl = "cpu"
    info = {"hw_key": key, "backend": wahl, "mess": mess, "ts": time.time(),
            "dauer_s": round(_time.perf_counter() - t_start, 1)}
    try:
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        tmp = f"{pfad}.tmp.{os.getpid()}"
        with open(tmp, "w") as f:
            json.dump(info, f)
        os.replace(tmp, pfad)
    except Exception:
        pass
    return wahl, {**info, "quelle": "benchmarked"}


def fehler_kern(text, n=220):
    """Kern eines Subprozess-Fehler-Outputs fuer Log/UI: die LETZTE nicht-leere
    Zeile (bei Tracebacks steht DORT die eigentliche Fehlermeldung — die ersten
    N Zeichen zeigten nur den Rahmen; Realfall Issue #18: carlsmith360 bekam
    'Traceback ... File "/u' und die Ursache war abgeschnitten). text darf
    bytes sein (subprocess ohne text=True)."""
    if isinstance(text, bytes):
        text = text.decode(errors="replace")
    zeilen = [z.strip() for z in (text or "").strip().splitlines() if z.strip()]
    return (zeilen[-1] if zeilen else "")[:n]


def load_config(path):
    raw = open(path).read()
    raw = re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), raw)
    cfg = yaml.safe_load(raw)
    cfg.setdefault("frigate_url", os.environ.get("FRIGATE_URL", ""))
    for key, default in [("poll_interval", 20), ("clip_delay", 15), ("fps_sample", 3),
                         # P4 (0.1.0.42, E4 "auto+klebrig"): Default AUTO = einmaliger Mini-Benchmark
                         # waehlt das Placement (NPU fuer Recognition, wenn sie die P4.0-Kriterien
                         # erfuellt) und wird in state/placement.json festgehalten. Explizite Werte
                         # (GPU/NPU/MIXED/CPU bzw. backend:) verhalten sich exakt wie bisher.
                         ("ov_device", "AUTO"), ("backend", ""), ("win_min", 3), ("win_thresh", 0.40), ("alert_cooldown", 300),
                         ("web_port", 8199), ("data_dir", os.path.join(HERE, "verify_data")),
                         ("trigger", "poll"), ("lookback_h", 2), ("clip_retention_d", 7),
                         ("clip_cache_max_gb", 50), ("cpu_threads", 0),
                         ("anker_sim1", 0.25), ("anker_sim2", 0.35),
                         ("anker_marge_warn", 0.15), ("anker_hart", 0.35),
                         ("anker_k_min", 5), ("anker_deckel", 250), ("anker_deckel_hart", 300),
                         # Crash-Loop-Wache Boot-Resume der Anker-Phase (#20 gr33nh07n:
                         # ein 1000er-Lauf blieb in phase=anker stecken und wurde nach
                         # jedem OOM-Neustart erneut angefahren — Endlosschleife bis
                         # zum Host-OOM). 0 = nie automatisch wiederaufnehmen.
                         ("anker_resume_max", 3),
                         ("benennung_k_je_bin", 4), ("benennung_yaw_grenze", 15.0),
                         ("benennung_dup_sim", 0.75), ("benennung_vorschlag_schwelle", 0.45),
                         ("required_zones", {}), ("areas", {}), ("alert_kategorien", ["widerspruch"]),
                         ("sub_label_schreiben", True), ("mqtt_publish", True), ("frigate_read_only", True),
                         ("szene_karenz_s", 90),
                         ("anwesenheit_push", True), ("anwesenheit_cooldown", 1800),
                         ("telegram", {}), ("telegram_modus", "aus"), ("telegram_inhalt", "video"),
                         ("telegram_hoehe", 720), ("telegram_cooldown", 600),
                         ("frigate_sync", False), ("unscharf_max", 350), ("min_kante", 70),
                         ("modell", "buffalo"),
                         # #42 Teil B: Fehldetektions-Signatur (kalibriert 24./25.07., s.
                         # face_audit.ist_fehldetektion) + sichtbarer SCRFD-det_thresh
                         # (war unsichtbarer insightface-Default 0.5; kein Hochdreh-Rat).
                         ("fd_front_min", 0.85), ("fd_sharp_min", 1500), ("fd_det_max", 0.70),
                         ("det_thresh", 0.5),
                         # E2 Ernte-Gates (V0.5 GEMESSEN, Auslieferungs-Defaults der
                         # Autor-Anlage — §2.4b: Werte hier, nie im Code; Gate L hat
                         # keine eigenen Zahlen, seine Stellschrauben SIND fd_*).
                         ("ernte_m_det_min", 0.60), ("ernte_m_kante_min", 60),
                         ("ernte_m_sharp_min", 60),
                         ("ernte_s_det_min", 0.70), ("ernte_s_winkel_max", 30),
                         # S2 no_person (konzept_no_person.md): Schwellen setzt der
                         # Retro-Backtest; None = Klassifikation komplett AUS (kein Rate-Default).
                         ("np_det_max", None), ("np_frigate_max", None),
                         # Nachhol-Lauf fuer gescheiterte Analysen (Vorfall 22./23.07.)
                         ("nachhol_versuche", 3),            # 0 = Feature komplett aus
                         ("nachhol_tage", 3),                # Fenster, gemessen an der EVENT-Startzeit
                         ("nachhol_intervall_s", 600),       # Takt: EIN Event pro Runde
                         ("nachhol_ruhe_s", 300),            # kein Nachholen kurz nach Live-Betrieb
                         ("nachhol_pause_s", 3600),          # Mindestabstand je Event (x Versuchsnr.)
                         ("nachhol_analyse_timeout_s", 300), # harter Deckel der Retry-Laeufe
                         ("nachhol_start_s", 600),           # Anlauf nach Dienststart
                         # Watchdog der LIVE-Analyse (Fix 10.08.; vorher fest 1800 s).
                         # MESSBASIS deckung.jsonl 27.07.-10.08. (n=1394 Live-Analysen
                         # auf der Prod-Maschine): Median 5,8 s, p90 20,2 s, p99 52,2 s,
                         # Maximum eines NORMALEN (erfolgreichen) Laufs 257,9 s (02.08.).
                         # 600 s = gut 2x dieses Maximum: kein regulaerer Lauf der
                         # letzten zwei Wochen waere gerissen, aber ein Haenger wie am
                         # 10.08. (Worker hing 1800 s im Swap-Thrashing, der Pass war
                         # 34 min blockiert) wird nach 10 min gekappt und SOFORT einmal
                         # nachgefahren (run_analyze). Der Riss ist MEHRDEUTIG
                         # (haengend ODER Maschine langsamer als die Messbasis) —
                         # der Retry faehrt deshalb mit VERDOPPELTER Frist:
                         # Maschinen bis ~4,6x langsamer als die Referenz kommen
                         # durch, Worst-Case-Blockade 600+1200 s = die alte feste
                         # 1800-s-Frist (nie schlechter als vor dem Fix).
                         ("analyse_timeout_s", 600),
                         # Issue #21/W2: Kern-Untergrenze der Wanduhr-Selbstmessung.
                         # Default = Struktur-Axiom 2 Akteure x 2 Bausteine (s.
                         # WANDUHR_MIN_KERNE-Kopf), KEINE Messung — deshalb als
                         # Config-Paar (Default HIER + Whitelist DORT) statt hart:
                         # ein Sub-4-Kern-Nutzer darf bewusst trotzdem messen.
                         ("wanduhr_min_kerne", WANDUHR_MIN_KERNE),
                         # W2: persistenter Analyse-Worker (worker.py) — Modelle EINMAL laden
                         ("worker", True),                   # aus = alter Subprozess-je-Event-Weg
                         # Z8 (konzept_frames.md §7): Kontroll-Speicher der beurteilten
                         # Bilder. False = SCHLANK und damit der Produkt-Default fuer fremde
                         # Installationen (Bilder nur fuer die Laufzeit des Durchgangs,
                         # danach bleiben Siegerbild + Urteils-Protokoll). True = SAMMEL:
                         # alle beurteilten Crops bleiben rollierend liegen und sind unter
                         # /person/kontrolle anschaubar. Nie im Code entschieden, immer hier.
                         ("diagnostic_collection", False),
                         # Vision-Detect V1 (konzept_vision.md v2 §5). DREI Paare:
                         # die beiden Zahlen stehen zusaetzlich in CONFIG_WHITELIST
                         # (Default HIER + Eintrag DORT — sonst lehnt config_schreiben
                         # jede UI-Aenderung mit 400 ab, Vorbild diagnostic_collection).
                         # Der Block `vision` traegt Endpunkt/Key/Prompt und ist bewusst
                         # NICHT in der Whitelist: dieselbe Bauart wie telegram/pushover/
                         # mqtt (Strings + Secret + verschachtelt, eigener Schreibweg
                         # vision_speichern) — und der Key darf nie ueber das generische
                         # Config-Blatt gerendert werden, das jeden Whitelist-Wert
                         # ausschreibt. Der Scharf-Schalter liegt IM Block, nicht in der
                         # Whitelist, damit er nur durch das E4-Gate gehen kann.
                         ("vision", {}),
                         # 12000 statt 3000 (.164): die eigene Whitelist-Hilfe sagt seit
                         # .157 woertlich, dass 3000 GEMESSEN zu klein war (die Antwort wurde
                         # abgeschnitten und zaehlte als kein Votum) — der Default folgte dem
                         # nicht. Real wieder passiert am 09.08. 09:23. Ein Default, der der
                         # eigenen Messung widerspricht, ist ein Fehler, keine Vorsicht.
                         ("vision_max_tokens", 12000),
                         ("vision_timeout_s", 900),
                         # V4 (§7): die Regeln des Urteilspfads. Jede als PAAR
                         # (hier Default, dort Whitelist mit Erklaertext).
                         # 12 statt 3 (User-Entscheid 09.08.: "immer 12 gegen max
                         # 12") — die Referenzgalerien sind 12er, das Kandidaten-
                         # Gitter darf genauso breit sein. OBERGRENZE, keine
                         # Forderung: weniger brauchbare Bilder = kleineres Gitter
                         # (`bilder_wirksam` <= `gewuenscht`), erfunden wird nichts.
                         # Kostet nichts extra, ein Galerien-Paar bleibt ZWEI
                         # Anfragen, egal wie viele Zellen. Prods Store traegt noch
                         # 10 (alte Grenze) und wird nach dem Deploy auf 12 gestellt.
                         ("vision_bilder_je_pass", 12),  # Zellen im Kandidaten-Gitter
                         ("vision_deadline_s", 1200),    # Gesamt-Deadline je Anfrage
                         ("vision_anfragen_h", 60),      # Mengendeckel je Stunde
                         ("vision_anfragen_tag", 300),   # und je Tag (= der E1-Tagesdeckel)
                         ("vision_quote", 1.0),          # Sammel-Regel: Anteil der Voten
                         # 1 statt 2 (.164, User-Entscheid 09.08.: "die erste, die passt;
                         # maximal vielleicht zwei"): EIN tausch-konsistentes Paar-Urteil
                         # traegt das Urteil. Wer mehr Bestaetigungen will, stellt sie ein —
                         # verlangen muss der Default sie nicht.
                         ("vision_min_voten", 1),        # ... und Mindestzahl abgegebener Voten
                         # Zwei OPTIONALE Meldungen (User-Entscheide 08.08.), beide
                         # Produkt-Default AUS. E6 bleibt unberuehrt: Vision hat kein
                         # Stimmrecht ueber die bestehenden Alarme, kein Veto, kein
                         # Entwarnen — das hier sind zusaetzliche Meldungen, keine.
                         # .165: der Tausch-Doppellauf ist abschaltbar. Default AN —
                         # die Positions-Schlagseite ist gemessen (§2.5) und der Tausch
                         # ist das Einzige, was sie sichtbar macht. Wer ein Modell hat,
                         # dem er nichts mehr nachweist, halbiert damit die Anfragen.
                         ("vision_doppellauf", True),
                         ("vision_meldung", False),      # Nachzuegler-Info nach dem Urteil
                         ("vision_alarm_unbestaetigt", False),
                         # Vision-STIMME (Fix vision-stimme-2): Urteil = EINE
                         # zusaetzliche Stuetze Richtung koerper_ab bei
                         # Namensgleichheit (szenarien.py). Default-Paar ist
                         # PFLICHT: ein Whitelist-Bool ohne Paar hier ist die
                         # stille Store-Falle der .171-Erstkontrolle (Seite
                         # zeigt off, Code faehrt on; der erste Save einer
                         # BELIEBIGEN Einstellung schriebe false).
                         ("vision_stimme", True),
                         # Ketten-Schalter (Issue #21, Entscheid 10.08.): jeder teure
                         # Erkennungs-Weg je Stufe schaltbar — "immer" (heutiges
                         # Verhalten), "nur_wenn_gesicht_leer" (erst wenn der Gesichts-
                         # Weg den Durchgang NICHT restlos bestaetigt hat, Mehr-
                         # Personen-Regel B) oder "aus" (der Weg startet an der QUELLE
                         # nicht: keine Koerper-Crops/kein Embedding bzw. kein Vision-
                         # Anstoss — auf 2C/4T-Maschinen die wirksamste Entlastung).
                         # PAAR-Bauart wie die vision_*-Zahlen: Default hier,
                         # Whitelist-Eintrag dort. Stufen-Quelle: KETTE_STUFEN.
                         ("person_pfad", "immer"),
                         ("vision_pfad", "immer"),
                         ("worker_rss_max_mb", 4096),        # Neustart-Schwelle (VmRSS des Workers;
                         # warm real ~1,9 GB [adaface/GPU] — 2048 liess nur 10 % Luft und riss im
                         # Soak 27.07.; 4096 = User-Entscheid: faengt Ausufern, nicht Normalbetrieb)
                         ("zeitzone", "")]:                  # leer = keine eigene Vorgabe (s. TZ-Block unten)
        cfg.setdefault(key, default)
    os.environ["VERIFY_DATA_DIR"] = cfg["data_dir"]   # Subprozesse (anlernen) erben den Datenpfad
    # #42 Teil B: Fehldetektions-Schwellen fuer anlernen (Sammel-Gate) — gleiches
    # Vererbungs-Muster wie der Datenpfad (Worker + Subprozess erben die Env).
    os.environ["VERIFY_FD_FRONT_MIN"] = str(cfg["fd_front_min"])
    os.environ["VERIFY_FD_SHARP_MIN"] = str(cfg["fd_sharp_min"])
    os.environ["VERIFY_FD_DET_MAX"] = str(cfg["fd_det_max"])
    _migrate_layout(cfg["data_dir"])                  # flach -> Unterordner, VOR dem Store-Lesen
    # UI-Store ueberlagert die yaml-Basis (config/config.json). Infrastruktur-/Boot-kritische Keys
    # kommen NUR aus yaml/ENV, nie aus dem Store/Restore (Code-Review 24.07.: sonst data_dir-Injection
    # = Schreiben ausserhalb des Datenpfads, bzw. ein kaputter web_port = Boot-Loop bei jedem Neustart).
    STORE_INFRA_TABU = {"data_dir", "web_port"}
    for k, v in _lade_config_store(cfg).items():
        if k in STORE_INFRA_TABU:
            continue
        cfg[k] = v
    # ENV-Bruecke Frigate-URL (#18 carlsmith360): personlern-Kette und sync_refs
    # lesen die Frigate-Adresse aus der ENV — normale Installationen setzen sie
    # aber NUR im UI (Store, eben eingemischt). Ohne Export sahen diese Pfade
    # nie eine URL ('unknown url type: /api/...'); bei uns maskierte die
    # compose-.env den Fall (K2-Klasse). Gleiches Vererbungs-Muster wie
    # VERIFY_DATA_DIR oben; Wizard-Save -> svc.neustart -> laeuft hier erneut durch.
    if (cfg.get("frigate_url") or "").strip():
        os.environ["FRIGATE_URL"] = cfg["frigate_url"]
    # Recognition-Modell prozessweit setzen: jeder Subprozess-env ist dict(os.environ, ...) und
    # erbt VERIFY_MODELL damit automatisch (analyze/backtest/anlernen/abnahme -> gleiches Modell,
    # kein refcache-Mix). Umschaltbar ueber modell: in verifyd.yaml/Store (buffalo | adaface).
    # Zeitzone — DREI Quellen mit klarer Rangfolge (User-Vorgabe 23.07.):
    #   1. ENV TZ         (compose/docker) — explizite Vorgabe des Betreibers gewinnt
    #   2. cfg["zeitzone"] (Wizard/Settings, liegt im Volume unter config/config.json)
    #   3. Code-Default Europe/Berlin
    # time.tzset() wirkt prozessweit auf ALLE datetime-Ausgaben (Log, Web-UI, Telegram-/
    # Pushover-Texte) und wird ueber os.environ an jeden Subprozess vererbt. Ohne das lief
    # der Container in UTC -> alle Zeiten 2 h zu frueh (Bug vom 22./23.07.).
    _tz_env = (os.environ.get("TZ") or "").strip()
    _tz_cfg = str(cfg.get("zeitzone") or "").strip()
    _tz = _tz_env or _tz_cfg or "Europe/Berlin"
    os.environ["TZ"] = _tz
    try:
        time.tzset()                                  # nur Unix; auf anderen Plattformen egal
    except AttributeError:
        pass
    cfg["zeitzone"] = _tz
    cfg["zeitzone_quelle"] = "env" if _tz_env else ("wizard" if _tz_cfg else "default")
    os.environ["VERIFY_MODELL"] = str(cfg["modell"])
    # Backend (ML-Provider) prozessweit wie VERIFY_MODELL — jeder Subprozess-env = dict(os.environ,..)
    # erbt es. Leerer backend-Schluessel -> aus ov_device abgeleitet (Abwaertskompat GPU/NPU/MIXED/CPU).
    _bk = str(cfg.get("backend") or "").strip()
    if not _bk:
        _ov = str(cfg.get("ov_device") or "").upper()
        _bk = "cpu" if _ov in ("", "CPU") else f"openvino:{_ov}"
    # P4: AUTO wird HIER aufgeloest — in Env/Subprozesse gelangt NIE 'AUTO' (dort waere es
    # OpenVINOs AUTO-Plugin, ein anderes Ding). Explizite Werte laufen unveraendert durch.
    if _bk.lower() in ("openvino:auto", "auto"):
        _bk, _pinfo = placement_aufloesen(cfg)
        cfg["placement_info"] = _pinfo
        cfg["ov_device"] = _bk.split(":", 1)[1] if ":" in _bk else "CPU"
    cfg["backend"] = _bk
    os.environ["VERIFY_BACKEND"] = _bk
    return cfg


LoadConfig = load_config          # oeffentlicher Name (Docker/Phase 2): yaml-Basis + JSON-Store


# ------------------------------------------------------------------ Frigate read-only (KONFIGURIERBAR)
# POLITIK (User 22.07.): read-only ist der SICHERE DEFAULT (`frigate_read_only: true`) fuer veroeffentlichte
# und Test-Systeme -> "bei euch kann nichts kaputtgehen". UNSER Prod setzt ihn bewusst auf false und darf
# schreiben (sub_labels + Face-Sync). FRIGATE_READONLY_FORCED kann eine Instanz NOTFALLS hart sperren
# (bleibt False = Config entscheidet).
FRIGATE_READONLY_FORCED = False

# Nachhol-Lauf: Pruning-Grenze der Versuchszaehler. BEWUSST fest und groesser als das
# konfigurierbare nachhol_tage (max 3): wuerde man gegen nachhol_tage prunen, koennte eine
# UI-Aenderung Zaehler wegwerfen und damit aufgegebene Events wiederbeleben.
NACHHOL_PRUNE_TAGE = 4

# Live-Reiter (Engine-M6): Frist, nach der ein Helfer-Quelltest-Job als tot
# gilt und seinen Riegel freigibt — der Subprozess hat timeout=180 s, der
# Puffer deckt Start/Auswertung; ein haengender Eintrag sperrte den Quelltest
# sonst bis zum Dienst-Neustart.
_LIVE_HELFER_FRIST_S = 240.0


def frigate_read_only(cfg):
    return FRIGATE_READONLY_FORCED or bool(cfg.get("frigate_read_only", True))


class FrigateHttpFehler(urllib.error.HTTPError):
    """HTTPError MIT Antwort-Auszug und Pfad. Anlass Issue #14 (Tokn59): das Log
    zeigte 67x nur 'HTTP Error 500: Internal Server Error' — Frigate schreibt die
    eigentliche Fehlermeldung aber oft in den Antwort-Body, und ohne den Pfad
    weiss man nicht mal, WELCHE Abfrage scheitert. Bewusst SUBKLASSE von
    HTTPError: bestehende except-Pfade und .code-Auswertungen (Retry-Klassen
    404/400, Port-Diagnose) greifen unveraendert."""

    def __init__(self, e, pfad):
        detail = ""
        try:
            detail = e.read(300).decode("utf-8", "replace").strip()
        except Exception:
            pass
        super().__init__(e.url, e.code, e.msg, e.hdrs, None)
        self.detail = detail
        self.pfad = pfad

    def __str__(self):
        d = f" — Frigate sagt: {self.detail[:200]}" if self.detail else ""
        return f"HTTP {self.code} {self.msg} bei {self.pfad}{d}"


def api_post(cfg, path, payload):
    if frigate_read_only(cfg):                    # Sperre greift, solange read-only an ist (Default sicher)
        raise RuntimeError(f"Frigate read-only mode active — POST {path} blocked")
    req = urllib.request.Request(cfg["frigate_url"] + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise FrigateHttpFehler(e, path) from None


def api(cfg, path):
    try:
        with urllib.request.urlopen(cfg["frigate_url"] + path, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise FrigateHttpFehler(e, path) from None


_frigate_cams_cache = {"ts": 0.0, "data": None, "err": None, "url": None}


def pruefe_url(u):
    """Frigate-Basis-URL validieren. (ok, gesaeuberte_url_oder_fehlertext).

    Die URL kommt aus Query-String/Body (Wizard, /sync_import) und landet in urlopen —
    urlopen spricht AUCH file://, ftp:// usw., d.h. ohne Schema-Pruefung wird die Setup-Seite
    zum Existenz-Orakel fuers lokale Dateisystem und interne Netz. Ein startswith("http")
    reicht nicht (laesst 'httpx://' und 'http-irgendwas' durch)."""
    u = (u or "").strip().rstrip("/")
    if not u:
        return False, "no URL given"
    try:
        p = urllib.parse.urlparse(u)
    except Exception:
        return False, "URL not parseable"
    if p.scheme not in ("http", "https"):
        return False, "only http:// or https:// is allowed"
    if not p.netloc:
        return False, "URL has no host"
    return True, u


def frigate_cameras(cfg, force=False):
    """Kameras aus Frigates /api/config lesen (Phase 2, User 21.07.): Namen, Zonen, enabled,
    Detect-Aufloesung, record. Kurz gecacht (60 s), damit die UI Frigate nicht bei jedem Aufruf
    abfragt. Damit sind Kameras NICHT hartkodiert, sondern kommen aus der realen Frigate des Users
    (Basis fuer das Kamera-Blatt: verwenden + Zonen-Bedingung). Rueckgabe: (dict, fehler|None)."""
    # Cache an die URL binden: sonst vergiftet EIN Aufruf mit abweichender URL (Wizard-Test,
    # /setup?url=...) 60 s lang das Kamera-Blatt ALLER Aufrufer — und /kameras_speichern
    # validiert dann gegen den fremden Bestand und wirft die eigenen Kameras still weg.
    _u = cfg.get("frigate_url")
    if not force and _frigate_cams_cache["data"] is not None and \
            _frigate_cams_cache["url"] == _u and \
            time.time() - _frigate_cams_cache["ts"] < 60:
        return _frigate_cams_cache["data"], _frigate_cams_cache["err"]
    out, err = {}, None
    if not _u:
        # Ohne Adresse gar nicht erst fragen. Vorher lief das in api() auf "unsupported operand
        # type(s) for +: 'NoneType' and 'str'" — ein Python-Typfehler mitten in der Oberflaeche,
        # der einem Erstnutzer nichts sagt (Fund 25.07. an der Vorschau-Instanz ohne Umgebung).
        err = ("no Frigate URL configured — set it in the setup wizard "
               "(Settings) or via the FRIGATE_URL environment variable")
        _frigate_cams_cache.update(ts=time.time(), data=out, err=err, url=_u)
        return out, err
    try:
        c = api(cfg, "/api/config")
        for name, cc in (c.get("cameras") or {}).items():
            det = cc.get("detect") or {}
            out[name] = {"enabled": bool(cc.get("enabled", True)),
                         "zones": sorted((cc.get("zones") or {}).keys()),
                         "width": det.get("width"), "height": det.get("height"),
                         # detect.enabled aus DERSELBEN Ableitung (Sicht-
                         # kontrolle 12.08., Realfall reiner Aufnahme-Klon:
                         # Frigate detektiert dort nichts -> nie Events).
                         "detect_enabled": bool(det.get("enabled", True)),
                         "record": bool((cc.get("record") or {}).get("enabled"))}
    # Fehler nach URSACHE auffaechern statt str(e) (Plan-QS 25.07.). Der haeufigste Erstnutzer-
    # Fehler ist Frigates AUTH-Port 8971 statt des internen Ports 5000 — und der zeigt sich real
    # NICHT als 401 (gegen die echte Frigate gemessen): http auf 8971 antwortet HTTP 400, https
    # scheitert am selbstsignierten Zertifikat. Ein 401-Zweig allein haette also nie gefeuert.
    except urllib.error.HTTPError as e:
        if e.code in (400, 401, 403) and ":8971" in _u:
            err = (f"HTTP {e.code} from port 8971 — that is Frigate's authenticated UI port, "
                   "which suslik cannot use. Point suslik at Frigate's internal port 5000 "
                   "(http://<frigate-host>:5000).")
        elif e.code in (401, 403):
            err = (f"HTTP {e.code}: this port requires authentication — suslik needs Frigate's "
                   "internal, unauthenticated port (default 5000)")
        else:
            err = str(e)
    except urllib.error.URLError as e:
        grund = getattr(e, "reason", e)
        if "SSL" in str(grund).upper() or "CERTIFICATE" in str(grund).upper() or ":8971" in _u:
            err = ("TLS/certificate error — this looks like Frigate's authenticated HTTPS port "
                   "(8971). suslik needs the internal HTTP port 5000 instead.")
        else:
            err = (f"cannot connect: {grund} — host or port wrong, Frigate not running, "
                   "or a firewall in between")
    except Exception as e:
        err = str(e)
    _frigate_cams_cache.update(ts=time.time(), data=out, err=err, url=_u)
    return out, err


def _setup_done(cfg):
    """Erst-Einrichtung abgeschlossen? Wizard-Flag ODER bereits konfiguriert (Kameras im Store /
    required_zones aus yaml). Schuetzt bestehende Installationen vor dem First-Run-Redirect in den
    Setup-Wizard; nur ein frisches System (Docker-Erstboot, leerer Store, keine Zonen) landet dort."""
    return bool(cfg.get("setup_done") or cfg.get("kameras") or cfg.get("required_zones"))


def master_persons(cfg):
    """Personenliste aus dem lokalen Referenz-Master (AP1) — Frigate-unabhaengig."""
    d = os.path.join(cfg["data_dir"], "faces")
    try:
        return sorted(p for p in os.listdir(d) if os.path.isdir(os.path.join(d, p)))
    except FileNotFoundError:
        return []


def frigate_to_cos(score):
    """Frigate-Anzeige-Score -> roher Cosinus (Sigmoid invertiert)."""
    if score is None:
        return None
    s = min(max(float(score), 1e-3), 1 - 1e-3)
    return round(0.3 + math.log(s / (1 - s)) / 20.0, 3)


# ------------------------------------------------------------------ Analyse (nutzt kalibriertes analyze.py)
# Nachbesserung W8 (roundtrip-seriell): EIN Analyse-Slot auch im Legacy-Weg
# (worker=aus). Im Worker-Modus serialisiert wk.lock; hier serialisiert dieses
# Modul-Lock den Analyse-Subprozess gegen die Wanduhr-Messung (_roundtrip_seriell
# nimmt bei worker=aus DASSELBE Lock). Vorher war die Live-Pruefung der Messung
# reines check-then-act — im TOCTOU-Fenster liefen Messung und Live-Analyse
# nachweislich PARALLEL (Kontroll-Harnisch W8).
_ANALYSE_SERIELL = threading.Lock()

# Issue #21 (Tokn59, i5-5300U 2C/4T): die Analyse-Kinder (worker.py bei ihm 2x ~160 %)
# saettigten die kleine CPU, UI/Poll/MQTT wurden minutenlang zaeh. Deshalb laufen der
# persistente Worker und jeder Analyse-Subprozess mit gesenkter CPU-Prioritaet
# (nice +10). Das senkt KEINE Last und macht keine Analyse schneller — es verteilt nur
# um, wer zuerst drankommt, wenn CPU knapp ist: der Dienstprozess (UI/Poll/MQTT) bleibt
# auf nice 0 und gewinnt die Konkurrenz, die gefuehlte Reaktion bessert sich; ist der
# Dienst idle (Normalfall), bekommt die Analyse weiter die volle CPU. 10 statt 19,
# damit die Analyse unter Dauerfremdlast nicht verhungert (nice ist ein Gewicht, keine
# Sperre). BEWUSST kein Config-Schalter (kein Config-Friedhof): es gibt keinen Fall,
# in dem die Analyse den UI-Threads vorgehen soll. ffmpeg-Enkel der Analyse erben den
# Wert per fork-Vererbung. Ein separates ionice ist unnoetig: ohne explizites
# ioprio_set folgt die I/O-Prioritaet der CPU-nice ("If no I/O scheduler has been set
# for a thread, then by default the I/O priority will follow the CPU nice value",
# man ioprio_set(2), man-pages 6.9.1, am 11.08. gegengelesen) — und die stdlib hat
# dafuer ohnehin keinen Wrapper, ein ctypes-Syscall waere arch-abhaengige Bastelei.
ANALYSE_NICE = 10


def _analyse_nice():
    """preexec_fn fuer Analyse-Spawns — laeuft im Kind zwischen fork und exec.
    Bewusst NUR dieser eine Syscall: kein Import, kein Lock, kein Log, keine
    nennenswerte Allokation — mehr waere im fork-Fenster eines Multithread-
    Prozesses nicht sicher (subprocess-Doku zu preexec_fn). nice ERHOEHEN ist
    unprivilegiert immer erlaubt; das leere except deckt nur exotische
    Sandbox-Policies ab und ist vertretbar, weil der Effekt reine Scheduling-
    Hoeflichkeit ist (sein Fehlen bleibt per `ps -o ni` sichtbar) — ein Raise
    hier liesse den Spawn und damit die ganze Analyse scheitern."""
    try:
        os.nice(ANALYSE_NICE)
    except OSError:
        pass


def run_analyze(cfg, eid, camera, persons, event_dir, timeout_s=None, worker=None,
                koerper=False, info=None):
    # Watchdog der Live-Analyse aus der Config (analyse_timeout_s, messbasiert —
    # s. Default-Block; vorher fest 1800 s: am 10.08. hing der Worker exakt diese
    # 1800 s im Swap-Thrashing und blockierte den Pass 34 min). Nachhol-Laeufe
    # bekommen weiter ihren eigenen, haerteren Deckel (nachhol_analyse_timeout_s).
    tmo = int(timeout_s or cfg.get("analyse_timeout_s") or 600)
    argv = [eid, "--labels", camera, "--persons", *persons,
            "--dir", event_dir, "--fps-sample", str(cfg["fps_sample"]),
            "--win-thresh", str(cfg["win_thresh"]),
            "--fd-front-min", str(cfg["fd_front_min"]), "--fd-sharp-min", str(cfg["fd_sharp_min"]),
            "--fd-det-max", str(cfg["fd_det_max"]), "--det-thresh", str(cfg["det_thresh"])]
    if koerper and worker is not None:
        # Z5 (konzept_frames v2 §4): der Koerper-Abnehmer faehrt im selben
        # Frame-Lauf mit — EIN Decode statt zwei. Scharf-Zustand kommt als
        # JOB-PARAMETER (der Worker soll nie fuer sich entscheiden), das
        # RAM-Budget als Deckel: analyze zieht davon seinen eigenen VmRSS ab
        # und puffert nur, wenn es hineinpasst (§5 'RAM'). Nur im Worker-Weg,
        # weil nur dort der Deckel gilt (worker_rss_max_mb, :695-698).
        argv += ["--koerper", "--koerper-rss-max-mb",
                 str(int(cfg.get("worker_rss_max_mb") or 4096))]
    logpfad = os.path.join(event_dir, "analyze.log")
    if worker is not None:
        # W2: Job in den persistenten Worker statt Prozess-Start je Event (~85 % der CPU
        # war Modell-Laden). Ergebnis-Kontrakt identisch: results.jsonl + analyze.log.
        open(logpfad, "w").close()            # wie der alte "w"-Modus: je Versuch frisch
        # Nachbesserung W7: die Wartezeit am Job-Lock (Ernte/Sammle/Wanduhr-
        # Roundtrip halten es teils minutenlang) ist KEINE Analysezeit. job()
        # meldet sie ueber `info` zurueck; dt (Watchdog-Einstufung, Logzeilen)
        # und dauer_s beim Aufrufer rechnen sie heraus — sonst erfindet die
        # Events-Anzeige eine Analysedauer und die watchdog/worker-died-
        # Unterscheidung (:dt >= frist) kippt nach langem Lock-Warten.
        w1, w2 = {}, {}
        t0 = time.monotonic()
        antwort = worker.job({"typ": "analyze", "argv": argv, "log": logpfad}, tmo,
                             info=w1)
        dt = time.monotonic() - t0 - float(w1.get("wartezeit_s") or 0.0)
        frist = tmo
        if antwort is None and timeout_s is None:
            # Requeue-Strecke (Fix 10.08., nachgebessert F5): EINMAL sofort
            # nachfassen, statt den Pass zu verlieren und auf die Nachhol-
            # Runde zu warten (die kam am 10.08. erst 29 min nach dem Kill;
            # der Sofort-Retry desselben Events lief dann in 9,4 s durch).
            # job() liefert None fuer ZWEI verschiedene Faelle, und nur die
            # gemessene Dauer trennt sie:
            #  - Worker TOT (Absturz/OOM -> EOF): dt << Frist, der Retry ist
            #    fast gratis -> gleiche Frist.
            #  - WATCHDOG gerissen (select lief die volle Frist): dt >= Frist.
            #    Das ist MEHRDEUTIG — wirklich haengend ODER die Maschine ist
            #    nur langsamer als die Messbasis der 600 s (Prod-Maschine,
            #    langsamster normaler Lauf 257,9 s). Der Retry faehrt deshalb
            #    mit VERDOPPELTER Frist: eine bloss langsame Maschine (bis
            #    ~4,6x Referenz, z. B. der ~774-s-Fall einer 3x langsameren
            #    CPU-Kiste) kommt damit durch, ein echt haengendes Event
            #    reisst erneut und geht in die stille Nachhol-Runde.
            #    Worst-Case-Blockade 600+1200 s = exakt die alte feste
            #    1800-s-Frist, nie schlechter als vor dem Fix.
            # worker.job() hat den haengenden Prozess bereits gekillt und
            # startet beim naechsten Job frisch; analyze ueberspringt via
            # results.jsonl, was der erste Versuch schon fertig hatte.
            # Bewusst nur EIN Retry (ein deterministisch haengendes Event
            # soll nicht schleifen) und nur live — Nachhol-Laeufe haben ihr
            # eigenes Versuchsbudget.
            watchdog = dt >= tmo
            frist = tmo * 2 if watchdog else tmo
            with open(logpfad, "a") as lf:
                if watchdog:
                    lf.write(f"\nverifyd: analyze watchdog fired after {dt:.0f}s "
                             f"(deadline {tmo}s) — one immediate retry on a "
                             f"fresh worker, deadline doubled to {frist}s\n")
                else:
                    lf.write(f"\nverifyd: worker died after {dt:.0f}s — one "
                             f"immediate retry on a fresh worker "
                             f"(deadline {tmo}s)\n")
            t0 = time.monotonic()
            antwort = worker.job({"typ": "analyze", "argv": argv, "log": logpfad},
                                 frist, info=w2)
            dt = time.monotonic() - t0 - float(w2.get("wartezeit_s") or 0.0)
        warte = float(w1.get("wartezeit_s") or 0.0) + float(w2.get("wartezeit_s") or 0.0)
        if info is not None:
            info["wartezeit_s"] = round(warte, 2)
        with open(logpfad, "a") as lf:
            if warte >= 0.1:                  # unter der dauer_s-Aufloesung waere es Rauschen
                lf.write(f"\nverifyd: waited {warte:.1f}s for the analysis slot "
                         f"(another analysis/measurement held it) — not counted "
                         f"as analysis time\n")
            if antwort is None:
                art = ("watchdog" if dt >= frist else "worker died")
                lf.write(f"\nverifyd: analyze aborted ({art} after {dt:.0f}s, "
                         f"deadline {frist}s)\n")
                return None
            if not antwort.get("ok"):
                lf.write(f"\nverifyd: analyze failed in worker: {antwort.get('fehler')}\n")
                return None
            # Telemetrie fuer den W2-Soak (CPU/Event, Peak-RSS) — greifbar per grep.
            # Z5: vmhwm_mb ist die SPITZE im Job (die rss_mb-Schwelle sieht nur den
            # Stand danach), koerper_* der zusatz-Rueckweg des zweiten Abnehmers.
            lf.write(f"verifyd-worker: cpu_s={antwort.get('cpu_s')} rss_mb={antwort.get('rss_mb')} "
                     f"vmhwm_mb={antwort.get('vmhwm_mb')} koerper={antwort.get('koerper_crops')}"
                     f"{'[' + str(antwort.get('koerper_degradiert')) + ']' if antwort.get('koerper_degradiert') else ''}"
                     f"{'/' + str(antwort.get('koerper_ausfall')) if antwort.get('koerper_ausfall') else ''}\n")
    else:
        env = dict(os.environ, OV_DEVICE=cfg["ov_device"], FRIGATE_URL=cfg["frigate_url"],
                   SCRATCH_DIR=os.path.join(cfg["data_dir"], "clips"))
        cmd = [sys.executable, os.path.join(HERE, "analyze.py"), *argv]
        # Nachbesserung W8: derselbe EINE Analyse-Slot wie im Worker-Zweig, hier
        # als Modul-Lock (_ANALYSE_SERIELL, s. Kopf) — die Wanduhr-Messung haelt
        # es waehrend ihres Roundtrips, ein Live-Lauf wartet dann HIER statt
        # parallel zu rechnen (und umgekehrt sieht die Messung diesen Lauf).
        # Wartezeit wie im Worker-Zweig herausrechnen (W7): die Frist beginnt
        # erst NACH dem Lock, dauer_s beim Aufrufer zaehlt nur Analysezeit.
        t_warte = time.monotonic()
        with _ANALYSE_SERIELL:
            warte = time.monotonic() - t_warte
            if info is not None:
                info["wartezeit_s"] = round(warte, 2)
            with open(logpfad, "w") as lf:
                if warte >= 0.1:              # unter der dauer_s-Aufloesung waere es Rauschen
                    lf.write(f"verifyd: waited {warte:.1f}s for the analysis slot "
                             f"(another analysis/measurement held it) — not "
                             f"counted as analysis time\n")
                # W1: eigene Prozessgruppe + killpg — ein Timeout-Kill muss auch ffmpeg-ENKEL treffen
                # (kuenftige HW-Decode-Pipes; der 480-MB-ffmpeg-Zombie aus der Plan-Recon war die
                # Live-Demo dieser Luecke). subprocess.run killte nur das direkte Kind.
                # Nachbesserung F7: der Sofort-Retry des Watchdogs gilt in BEIDEN
                # Zweigen — der Hilfetext von analyse_timeout_s verspricht ihn
                # ohne Einschraenkung, vorher blieb dieser Legacy-Zweig
                # (worker=false) Einzelschuss. Gleiche Politik wie im
                # Worker-Zweig: EIN Retry, nur live, verdoppelte Frist (der Riss
                # ist mehrdeutig: haengend oder bloss langsamer als die
                # Messbasis); jeder Versuch ist hier ohnehin ein frischer
                # Prozess, analyze ueberspringt via results.jsonl Fertiges.
                frist = tmo
                while True:
                    p = subprocess.Popen(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT,
                                         start_new_session=True,
                                         preexec_fn=_analyse_nice)   # Issue #21, s. ANALYSE_NICE
                    try:
                        p.wait(timeout=frist)
                        break
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(p.pid, signal.SIGKILL)
                        except Exception:
                            pass
                        p.wait()
                        if frist == tmo and timeout_s is None:
                            frist = tmo * 2
                            lf.write(f"\nverifyd: analyze watchdog ({tmo}s) — one "
                                     f"immediate retry in a fresh process, "
                                     f"deadline doubled to {frist}s\n")
                            lf.flush()
                            continue
                        lf.write(f"\nverifyd: analyze timeout ({frist}s), aborted (process group killed)\n")
                        return None
    rp = os.path.join(event_dir, "results.jsonl")
    if not os.path.exists(rp):
        return None
    with open(rp) as f:
        for line in f:
            try:
                return json.loads(line)
            except Exception:
                continue      # halb geschriebene Zeile (Kill mid-write); naechste vollstaendige zaehlt
    return None


class WorkerProzess:
    """W2: EIN persistenter Analyse-Worker (worker.py) statt Prozess-Start je Event.
    Haelt die Modelle warm (gemessen 26.07.: 55 CPU-s/Event, davon ~85 % Modell-Laden;
    warm ~6-14 CPU-s). ALLE Compute-Jobs laufen durch diesen einen Prozess — das buendelt
    die GPU-Kontexte und loest die Kontext-Kollision, die _gpu_bg_lock nur entschaerfte.
    Lebenszyklus: Lazy-Start beim ersten Job (nie parallel zum Startup-Benchmark,
    Exit-139-Bootfenster); Timeout/Absturz -> killpg + Neustart beim naechsten Job;
    RSS-Schwelle (worker_rss_max_mb) -> geordneter Neustart; stop() vor execv/--once-Ende.
    Antworten kommen ueber eine EIGENE Pipe (WORKER_ANTWORT_FD) — stdout gehoert den Jobs."""

    def __init__(self, cfg, log=None):
        self.cfg = cfg
        self.log = log or (lambda m: None)
        self.p = None
        self.rx = None                      # Leseende der Antwort-Pipe
        self.lock = threading.Lock()        # EIN Job gleichzeitig (die Buendelung ist der Zweck)
        # Z8 Mitnahme A: Verteiler-Rueckfaelle des Workers (getrennte Decodes statt
        # einem, konzept_frames.md §3.2). Der Worker meldet SEINEN kumulativen Stand;
        # ein Neustart setzt ihn zurueck, deshalb hier Summe + zuletzt gesehener Wert.
        self.rueckfaelle = {"summe": 0, "letzt": 0}

    def _start(self):
        r, w = os.pipe()
        env = dict(os.environ, OV_DEVICE=self.cfg["ov_device"], FRIGATE_URL=self.cfg["frigate_url"],
                   SCRATCH_DIR=os.path.join(self.cfg["data_dir"], "clips"),
                   WORKER_ANTWORT_FD=str(w))
        # start_new_session: killpg muss auch ffmpeg-ENKEL treffen (W1-Lektion). stdin-Pipe ist
        # non-inheritable (CLOEXEC) -> nach einem execv von verifyd bekommt eine Waise EOF und endet.
        self.p = subprocess.Popen([sys.executable, os.path.join(HERE, "worker.py")],
                                  stdin=subprocess.PIPE, pass_fds=(w,), env=env,
                                  start_new_session=True, text=True, bufsize=1,
                                  preexec_fn=_analyse_nice)   # Issue #21, s. ANALYSE_NICE

        os.close(w)                         # unser Ende des Schreib-fd: nur das Kind schreibt
        self.rx = os.fdopen(r, "r")
        try:                                # bevorzugtes OOM-Opfer vor verifyd selbst (v2qs-B3);
            with open(f"/proc/{self.p.pid}/oom_score_adj", "w") as f:   # erhoehen geht unprivilegiert
                f.write("500")
        except Exception:
            pass
        self.log(f"worker started (pid {self.p.pid})")

    def _stop(self, kill=False):
        p, rx = self.p, self.rx
        self.p = self.rx = None
        if rx:
            try:
                rx.close()
            except Exception:
                pass
        if not p:
            return
        try:
            if not kill:
                try:
                    p.stdin.close()          # EOF -> Worker endet geordnet
                except Exception:
                    pass
                try:
                    p.wait(timeout=10)
                    return
                except subprocess.TimeoutExpired:
                    pass
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except Exception:
                pass
            try:
                p.stdin.close()
            except Exception:
                pass
            p.wait()
        except Exception:
            pass

    def stop(self):
        with self.lock:
            self._stop()

    def job(self, job, timeout_s, info=None):
        """Job senden, Antwort mit Timeout lesen. None = Timeout/Absturz (Worker wird
        gekillt, der naechste Job startet ihn frisch); sonst die Antwort des Workers.
        `info` (optional, dict): bekommt `wartezeit_s` — wie lange DIESER Aufruf am
        Job-Lock hing (Nachbesserung W7: Ernte/Sammle/Wanduhr-Roundtrip halten das
        Lock teils minutenlang; die Wartezeit ist keine Analysezeit und darf weder
        in dauer_s noch in die watchdog/worker-died-Einstufung fallen)."""
        t_warte = time.monotonic()
        with self.lock:
            if info is not None:
                info["wartezeit_s"] = round(time.monotonic() - t_warte, 3)
            try:
                if self.p is None or self.p.poll() is not None:
                    self._stop(kill=True)    # Reste (Pipe/Zombie) wegraeumen
                    self._start()
                # Issue #20/#21: die In-Job-RSS-Wache bekommt ihre Politik-Grenze
                # als Job-Feld (Protokoll im worker.py-Kopf, Rangfolge _job_rss_grenze).
                # Deckungs-Vertrag: DIESELBE Config-Zahl wie die Neustart-Schwelle
                # unten in dieser Methode — keine zweite Zahlenquelle.
                if job.get("typ") != "ping":
                    job.setdefault("rss_max_mb",
                                   int(self.cfg.get("worker_rss_max_mb") or 4096))
                self.p.stdin.write(json.dumps(job) + "\n")
                self.p.stdin.flush()
                r, _, _ = select.select([self.rx], [], [], timeout_s)
                if not r:
                    self.log(f"worker job timeout ({timeout_s}s) — killing worker")
                    self._stop(kill=True)
                    return None
                zeile = self.rx.readline()
                if not zeile:                # Worker gestorben (Absturz/OOM) -> EOF
                    self.log("worker died mid-job — restart on next job")
                    self._stop(kill=True)
                    return None
                antwort = json.loads(zeile)
                if "frame_rueckfaelle" in antwort:
                    n, letzt = int(antwort["frame_rueckfaelle"] or 0), self.rueckfaelle["letzt"]
                    # n < letzt = der Worker ist zwischendurch neu gestartet (Zaehler
                    # bei 0 begonnen); dann zaehlt n ganz, sonst nur der Zuwachs.
                    self.rueckfaelle["summe"] += n if n < letzt else n - letzt
                    self.rueckfaelle["letzt"] = n
                grenze = int(self.cfg.get("worker_rss_max_mb") or 4096)
                if int(antwort.get("rss_mb") or 0) > grenze:
                    self.log(f"worker rss {antwort.get('rss_mb')} MB > {grenze} MB — restarting worker")
                    self._stop()
                return antwort
            except Exception as e:
                self.log(f"worker error: {type(e).__name__}: {e} — killing worker")
                self._stop(kill=True)
                return None


# ------------------------------------------------------------------ Deckungs-Logik (§6 Konzept)
def verdict(cfg, frigate_label, ours, confirmed=None):
    """ours: {person: {win3s, max, ...}} -> (kategorie, bestaetigte_personen).
    confirmed additiv (Issue #19): die deckung-Korrektur nach dem Anlernen liefert die
    Bestaetigung selbst (Embedding-Nachpruefung statt win3s) — die Kategorie-Ableitung
    bleibt trotzdem in DIESER einen Quelle statt als Kopie an der Korrektur-Stelle."""
    if confirmed is None:
        confirmed = sorted(p for p, r in ours.items() if r.get("win3s", 0) >= cfg["win_min"])
    if frigate_label and confirmed:
        return ("deckung" if frigate_label in confirmed else "widerspruch"), confirmed
    if frigate_label and not confirmed:
        return "frigate_nur", confirmed          # Frigate behauptet, wir koennen nicht bestaetigen (Postbote-Muster)
    if confirmed:
        return "wir_nur", confirmed              # wir sehen jemanden, Frigate schweigt
    return "beide_unknown", confirmed


def verdict_v2(cfg, ours, max_bw, confirmed=None):
    """Schema v2 (Plan AP2, Frigate-unabhaengig): erkannt / fremd_verdacht /
    unbekannt_schwach. fremd_verdacht = brauchbares Gesicht (>=100 px), aber niemand
    bestaetigt. HINWEIS: Trockenlauf 18.07. ergab 10-17x/Tag -> vorerst NICHT in
    alert_kategorien (Nachschaerfung in der Parallelphase mit GT-Labels).
    confirmed additiv wie bei verdict (Issue #19, deckung-Korrektur)."""
    if confirmed is None:
        confirmed = sorted(p for p, r in ours.items() if r.get("win3s", 0) >= cfg["win_min"])
    if confirmed:
        return "erkannt", confirmed
    if (max_bw or 0) >= 100:
        return "fremd_verdacht", confirmed
    return "unbekannt_schwach", confirmed


# Alert-Kategorien kommen aus der Config (alert_kategorien) — User-Entscheidung 16.07.:
# nur noch "widerspruch" (echte gegenteilige Erkennung); "frigate_nur" ("Person da,
# Gesicht nicht erkannt") laeuft nur noch ins Log/die Statistik.

# Kategorie-ANZEIGE-Tabellen: KAT_LABELS/KAT_FARBE wohnen seit Modulumbau R1 in
# webui/bausteine.py (Helfer-Heimat). Re-Import wie gt_leiste unten (Kompatibilitaet
# fuer Service-Meldetexte und verbleibende Seiten; Abbau erst mit M-Schlussetappe).
from webui.bausteine import KAT_LABELS, KAT_FARBE   # noqa: F401 (Re-Export)


def gt_schnellpersonen(rows, cfg, n=2):
    """Die n am haeufigsten bestaetigten Personen — GT-Schnellbuttons DYNAMISCH statt hardcoded
    Namen (User 22.07.: 'muss automatisch sein'). Fallback: erste Master-Personen."""
    zahl = {}
    for r in rows:
        for p in r.get("bestaetigt") or []:
            zahl[p] = zahl.get(p, 0) + 1
    top = sorted(zahl, key=lambda p: -zahl[p])[:n]
    return top or master_persons(cfg)[:n]


# M0: gt_leiste + bild_nn wohnen jetzt in webui/bausteine.py (Helfer-Heimat, loest die
# Import-Zyklen VOR den Seiten-Umzuegen). Re-Export hier ist KOMPATIBILITAET nach
# Modul-Konzept §4 (qs/Seiten nutzen verifyd als API) — Abbau erst mit M-Schlussetappe.
from webui.bausteine import gt_leiste, bild_nn   # noqa: F401 (Re-Export)
from webui.bausteine import fehler_grund as _fehler_grund   # Issue #9: die EINE Grund-Quelle


# ---------------------------------------------------- Meldewege (Modulumbau R3)
# push/stoerung_melden/telegram_video leben in core/melden.py (Live-Andock-API,
# modulplan.md #3; Docstrings/Begruendungen dort). Re-Export wie KETTE_STUFEN:
# bestehende Aufrufer (Service, Wartung/Watchdog, prototyp/live_wache) nutzen
# verifyd weiter als API-Heimat — Abbau erst mit der M-Schlussetappe.
push = _melden.push
stoerung_melden = _melden.stoerung_melden
telegram_video = _melden.telegram_video


# ------------------------------------------------- Video-Transcode: Encoder-Wahl (NVENC/VAAPI/CPU)
_VIDEO_ENCODER = None      # ("nvenc"|"vaapi"|"cpu", node, monotonic-Zeit der Entscheidung)
_VIDEO_PROBE_GRUND = ""    # fuer die Selbstcheck-Zeile: WARUM cpu (kein Geraet vs. Probe gescheitert)


def _encode_probe(argv):
    """True, wenn ffmpeg den Mini-Encode fehlerfrei schafft. Eigener Timeout: eine haengende
    Probe darf den Start nicht blockieren; jeder Fehler zaehlt als 'kann nicht'."""
    try:
        return subprocess.run(argv, capture_output=True, timeout=20).returncode == 0
    except Exception:
        return False


def video_encoder():
    """Waehlt den ffmpeg-Encoder fuers Clip-Transcoding: NVENC -> VAAPI (je Render-Node) -> CPU.
    Jeder Kandidat wird mit einer ECHTEN Mini-Encode-Probe belegt, nie nur gelistet —
    Tester-Issue 26.07. (RTX 3060 + i3-1220P, an unseren eigenen Images verifiziert):
    /dev/dri/renderD128 war hartcodiert, aber die DRM-Nummerierung verschiebt sich mit jedem
    weiteren Geraet (NVIDIA-Host: renderD129); und ffmpeg LISTET h264_vaapi auch, wenn im Image
    nur libva ohne *_drv_video.so-Mediatreiber liegt — der Encode scheitert dann erst zur
    Laufzeit. Ergebnis war ein 100% stiller libx264-Rueckfall, 25,5 s CPU statt 4,5 s NVENC pro
    Clip, ohne eine Logzeile (Klasse C). Probe-Frame 256x256, NICHT kleiner: NVENC lehnt 64x64
    mit "Frame Dimension less than the minimum supported value" ab (am RTX 2060 gemessen) —
    eine zu kleine Probe wuerde funktionierende Hardware verwerfen und exakt den stillen
    CPU-Rueckfall wieder einbauen, den sie verhindern soll. 256x256 ist an NVENC (RTX 2060)
    und VAAPI (Meteor-Lake-iGPU) belegt.
    Ein HW-Ergebnis ist final (erster Aufruf = Startup-Selbstcheck); ein cpu-Ergebnis wird
    fruehestens nach 600 s neu geprobt (Review-Fund: die GPU kann beim Containerstart noch
    belegt oder der Node noch nicht bereit sein — ohne Re-Probe wuerde ein einziger frueher
    Fehlschlag den Dienst bis zum Neustart auf libx264 festnageln, der alte Code versuchte
    VAAPI ja bei jedem Clip neu)."""
    global _VIDEO_ENCODER, _VIDEO_PROBE_GRUND
    if _VIDEO_ENCODER is not None:
        art, node, ts = _VIDEO_ENCODER
        if art != "cpu" or time.monotonic() - ts < 600:
            return art, node
    quelle = ["-f", "lavfi", "-i", "testsrc=size=256x256:duration=0.1"]
    # NVIDIA zuerst: dort gibt es kein VAAPI, und /dev/nvidia* existiert nur, wenn die Geraete
    # wirklich in den Container gereicht wurden (--gpus). Trotzdem proben, nicht annehmen.
    # -nostdin wie in jedem produktiven ffmpeg-Aufruf (die Probe erbt sonst stdin des Dienstes).
    try:
        nvidia = any(n.startswith("nvidia") for n in os.listdir("/dev"))
    except OSError:
        nvidia = False
    if nvidia and _encode_probe(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                                 *quelle, "-vf", "format=yuv420p", "-c:v", "h264_nvenc",
                                 "-f", "null", "-"]):
        # W3/Issue #4: volle HW-Pipeline (NVDEC-Decode + scale_cuda) NUR nach Probe der EXAKTEN
        # Kette — ffmpeg LISTET scale_cuda auch ohne nutzbares Geraet (dieselbe Falle wie beim
        # Encoder). Probe braucht echtes H.264-Material (testsrc ist nicht NVDEC-dekodierbar),
        # also erst Mini-Sample encodieren. Real sind die Quellen HEVC; die Probe belegt die
        # Pipeline (cuvid/scale_cuda vorhanden+nutzbar), Codec-Sonderfaelle faengt der
        # Laufzeit-CPU-Fallback der Aufrufer (mit Logzeile).
        import tempfile
        art = "nvenc"
        with tempfile.TemporaryDirectory() as td:
            smp = os.path.join(td, "probe.mp4")
            if _encode_probe(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                              *quelle, "-vf", "format=yuv420p", "-c:v", "libx264",
                              "-f", "mp4", smp]) \
               and _encode_probe(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                                  "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
                                  # 256 wie die Encode-Probe: NVENC lehnt zu kleine Frames ab
                                  # (64x64 gemessen; W3-Review: 128 laege unter dem Minimum und
                                  # liesse die Voll-HW-Probe IMMER scheitern -> Feature still tot)
                                  "-i", smp, "-vf", "scale_cuda=-2:256:format=yuv420p",
                                  "-c:v", "h264_nvenc", "-f", "null", "-"]):
                art = "nvenc-voll"
        _VIDEO_ENCODER = (art, None, time.monotonic())
        return art, None
    try:
        knoten = sorted(k for k in os.listdir("/dev/dri") if k.startswith("renderD"))
    except OSError:
        knoten = []
    for k in knoten:
        node = f"/dev/dri/{k}"
        if _encode_probe(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                          "-init_hw_device", f"vaapi=hw:{node}", *quelle,
                          "-vf", "format=nv12,hwupload", "-c:v", "h264_vaapi",
                          "-f", "null", "-"]):
            _VIDEO_ENCODER = ("vaapi", node, time.monotonic())
            return "vaapi", node
    # Grund fuers Selbstcheck-Log sauber trennen: "kein Geraet durchgereicht" ist eine ANDERE
    # Diagnose als "Geraet da, Probe gescheitert" (Review-Fund: der falsche Grund schickt den
    # Fern-Support in die falsche Richtung).
    _VIDEO_PROBE_GRUND = ("hw encode probes failed" if (nvidia or knoten)
                          else "no hw video device passed through (/dev/nvidia*, /dev/dri)")
    _VIDEO_ENCODER = ("cpu", None, time.monotonic())
    return "cpu", None


def transcode_kommandos(src, ziel, hoehe, q_hw, q_cpu, dauer_s=None, q_vaapi=None,
                        q_hw_voll=None):
    """Baut (hw_cmd | None, cpu_cmd) fuer den beim Start gewaehlten Encoder. Die q-Regler
    heissen je Encoder anders (-cq nvenc, -qp vaapi, -crf x264; gleiche 0-51-Skala, aber nicht
    identisch kalibriert), deshalb bleiben die kalibrierten Bestandswerte je Aufrufer erhalten.
    q_hw_voll: eigener cq fuer die volle HW-Pipeline (N8a, Issue-#4-Follow-up):
    scale_cuda erzeugt ein ANDERES Bild als swscale — dasselbe cq kostet dort mehr Bits
    (gemessen: +26 % an 2688p-Feldmaterial bis +79 % eigenes 4K bei cq34/720p). Die zwei
    NVENC-Pipelines sind verschiedene Operating Points (analog q_vaapi); None = q_hw.
    `-f mp4` ist ZWINGEND: Ziel ist der .part-Zwischenname, aus dem ffmpeg kein Format ableiten
    kann (Fund 25.07., s. make_browser_copy). Das Pixelformat wird in BEIDEN HW-Kommandos hart
    auf 8 bit gezogen (format=nv12 bzw. yuv420p) — Review-Fund, an beiden HW-Typen gemessen:
    eine 10-bit-Quelle (HEVC Main10) schickt sonst p010-Frames in den Encoder, h264_vaapi
    bricht mit 'No usable encoding profile found' (rc=218), h264_nvenc mit 'No capable devices
    found' (rc=187) ab, waehrend die 8-bit-Startprobe 'passed' meldet — der stille CPU-Rueckfall
    waere zurueck, nur mit gruenem Selbstcheck darueber. Der CPU-Pfad braucht nichts: ffmpeg
    handelt das Format bei Software-Frames selbst aus."""
    art, node = video_encoder()
    t = ["-t", str(dauer_s)] if dauer_s else []
    # N9: cpu_threads deckelt die CPU-lastigen Transcode-Zweige (libx264-Encode bzw.
    # Software-Decode+swscale beim encode-only-NVENC). ENV statt Config-Durchreichung,
    # damit derselbe Knopf auch im Worker-Subprozess gilt (gesetzt in Service.__init__).
    _thr = os.environ.get("SUSLIK_CPU_THREADS", "")
    thr = ["-threads", _thr] if _thr.isdigit() and int(_thr) > 0 else []
    # .83: Ton MITNEHMEN statt -an — als AAC-Re-Encode (immer mp4-kompatibel,
    # auch bei G.711-Kameras, bei denen -c:a copy den Mux braeche); ohne Audiospur in
    # der Quelle ist der Parameter wirkungslos. Audio-Anteil ~96 kbit/s, beruehrt die
    # kalibrierten VIDEO-Groessen (q_hw/q_hw_voll/crf) nicht.
    ton = ["-c:a", "aac", "-b:a", "96k"]
    cpu = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", src, *t,
           "-vf", f"scale=-2:{hoehe}", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", str(q_cpu), *thr, *ton, "-f", "mp4", ziel]
    if art == "nvenc-voll":
        # W3/Issue #4 (Feldbericht, gemessen RTX 3060): Decode+Scale MIT auf die GPU — 15,3 -> 1,1
        # CPU-s je Clip. scale_cuda=format=yuv420p haelt die 8-bit-Wache auf der GPU. Nur aktiv,
        # wenn die EXAKTE Pipeline beim Start probiert wurde (s. video_encoder): mit
        # -hwaccel_output_format cuda faellt nicht dekodierbares Material HART statt weich —
        # den weichen Rueckzug liefert dann der Laufzeit-CPU-Fallback der Aufrufer.
        hw = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y",
              "-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", src, *t,
              "-vf", f"scale_cuda=-2:{hoehe}:format=yuv420p", "-c:v", "h264_nvenc",
              "-cq", str(q_hw_voll if q_hw_voll is not None else q_hw),
              *ton, "-f", "mp4", ziel]
    elif art == "nvenc":
        hw = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *thr, "-i", src, *t,
              "-vf", f"scale=-2:{hoehe},format=yuv420p", "-c:v", "h264_nvenc",
              "-cq", str(q_hw), *ton, "-f", "mp4", ziel]
    elif art == "vaapi":
        hw = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y",
              "-hwaccel", "vaapi", "-hwaccel_device", node,
              "-hwaccel_output_format", "vaapi", "-i", src, *t,
              "-vf", f"scale_vaapi=w=-2:h={hoehe}:format=nv12", "-c:v", "h264_vaapi",
              # W3-Review: q_hw ist auf NVENC kalibriert (Issue #4, SSIM-gemessen); VAAPI bekommt
              # bei Bedarf seinen EIGENEN Wert (q_vaapi), weil die Qualitaets-Seite dort ungemessen
              # ist (scale_vaapi-SSIM-Deckel, Issue §3) — sonst verstellte die NVENC-Kalibrierung
              # still den Intel-Prod-Pfad mit.
              "-qp", str(q_vaapi if q_vaapi is not None else q_hw), *ton, "-f", "mp4", ziel]
    else:
        hw = None
    return hw, cpu


# Ketten-Schalter (Issue #21): Stufen-Enum + die ganze Erkennungskette leben seit
# Modulumbau R2 in core/kette.py (DEFAULT_KETTE als die EINE Stufen/Reihenfolge/
# Bedingungs-Struktur). Re-Export hier haelt den Deckungs-Vertrag der Whitelist
# (Stufen-Quelle bleibt EINE, qs_ebenen.md).
KETTE_STUFEN = _kette.KETTE_STUFEN


# ------------------------------------------------------------------ Kern: ein Event verarbeiten
class Service:
    def __init__(self, cfg, dry_alert=False):
        self.cfg = cfg
        self.dry_alert = dry_alert
        if cfg.get("cpu_threads"):
            # N9: EIN Knopf fuer beide Prozesse — ENV erbt der Worker-Subprozess; face_audit
            # liest es beim ersten Session-Bau (_so_mit_threads), Transcode je Kommando.
            # 0/unset = auto (erlaubte Kerne) = Verhalten wie bisher.
            os.environ["SUSLIK_CPU_THREADS"] = str(cfg["cpu_threads"])
        self.log_path = os.path.join(cfg["data_dir"], "state", "deckung.jsonl")
        os.makedirs(os.path.join(cfg["data_dir"], "events"), exist_ok=True)
        os.makedirs(os.path.join(cfg["data_dir"], "clips"), exist_ok=True)
        self.processed = self._load_processed()
        self.last_alert = 0.0
        self._melde_zustand = {}                  # Drossel-Zeitstempel der Meldewege (tg_unbekannt,
                                                  # ha_warn) — Eigentum des Dienstes, core/melden
                                                  # bekommt das Dict als Parameter (Modulumbau R3)
        self._sammel_lock = threading.Lock()      # schuetzt die Sammel-/Reorg-Flags (User 21.07.)
        self._sammel_laeuft = False               # ein Szenario-Sammeln gleichzeitig (Prozess-Ebene serialisiert der pool_lock in anlernen.py)
        self._sammel_nachhol = False              # Szenario waehrend eines Laufs -> danach EINMAL nachziehen statt verwerfen
        self._reorg_laeuft = False                # Reorganisieren-Button laeuft (Doppelklick-Schutz)
        self._qs_lock = threading.Lock()          # Guard-Zugriff (ThreadingHTTPServer-Threads)
        self._qs_laeuft = False
        self._qs_nochmal = False
        self._live_jobs_lock = threading.Lock()   # Live-Reiter: Helfer-Quelltests
        self._live_jobs = {}                      # kamera -> {art, weg, fertig, ...}
        self._live_cmd_lock = threading.Lock()    # Engine-M3: Kommando-Slot pruefen+schreiben atomar (2 Klicks im 2-s-Fenster)
        self._live_aufsicht = None                # Phase 4: Engine-Supervisor (core/liveaufsicht),
        self._live_aufsicht_stop = threading.Event()   # gebaut in start_live_aufsicht()
        self._vs_laeuft = set()                   # Personen mit laufender Bestands-Suche
        self._nachlern_lock = threading.Lock()    # schuetzt _nachlern_timer
        self._nachlern_timer = {}                 # person -> Debounce-Timer: Bestands-Suche erst nach Durchgangs-Ende (User 21.07.)
        self._gpu_bg_lock = threading.Lock()      # serialisiert schwere GPU-Hintergrund-Subprozesse (Review 21.07.): hoechstens EINER gleichzeitig, Live-run_analyze bleibt frei — AUSSER die Wanduhr-Messung: die serialisiert sich zusaetzlich ueber den Analyse-Slot gegen Live (_roundtrip_seriell, Issue #21: auf 2C/4T war "frei" = Minuten Doppellast) und nimmt DIESES Lock nur je Roundtrip, nie waehrend sie auf Live wartet (Nachbesserung W5, Regel wie start_nachhol)
        self._vision_lock = threading.Lock()      # V4: schuetzt Single-Flight + Debounce-Timer des Vision-Urteils
        self._vision_flug = None                  # core.visionurteil.Einfachlauf (lazy): 1 laufend + 1 wartend, Rest verworfen+gezaehlt
        self._vision_timer = {}                   # pass_key -> Debounce-Timer (Muster _nachlern_timer): Urteil erst nach Durchgangs-Ende
        self._kette_stumm = {}                    # Ketten-Schalter: pass_key -> ts der EINEN "vision_pfad=aus"-Zeile (eine je Durchgang, nicht je Event)
        self._nachanalyse = {"laeuft": False, "pass_key": "", "gesamt": 0, "fertig": 0}  # .161: erneute Analyse EINES Durchgangs (Sammel-Modus an, Material fehlt)
        self._vision_lebt = set()                 # .164: pass_keys mit WIRKLICH laufendem Vision-Thread (Waisen-Zweitsicherung)
        self.last_seen = self._load_last_seen()   # Person -> ts letzte Bestaetigung; aus dem Log
                                                  # rekonstruiert, sonst Push-Salve nach Neustart
        self.own_writes = self._load_own_writes() # eids mit VON UNS gesetztem sub_label (Echo-Freiheit)
        self.pub = None                           # MQTT-Publisher (AP2), Setup via start_publisher()
        self.mqtt_trigger = None                  # MQTT-Trigger-Client (nur trigger=mqtt), Setup via mqtt_loop()
        self.frigate_fehler = None                # (ts, msg) letzter Frigate-API-Fehler -> UI-Banner
        self._emb = None                          # Lazy-Embedder (nur Upload-/Aufnahme-Gate, AP4)
        self._worker_obj = None                   # W2: persistenter Analyse-Worker (lazy, s. _worker)
        self._review_lock = threading.Lock()      # W3: laufende Lazy-Browser-Kopien (ein Bau je Clip)
        self._review_laeuft = set()
        self._review_fehler = {}                  # ed -> ts letzter Fehlschlag: /video zeigt dann eine
                                                  # Fehlerseite statt per Auto-Refresh endlos neu zu bauen
        self._transcode_serial = threading.Lock() # W3-Review: EIN Lazy-Transcode gleichzeitig (Klick-
                                                  # Sturm darf nicht N parallele ffmpeg starten)
        self._transcode_procs = set()             # laufende ffmpeg-Popen: neustart() killt sie VOR execv
                                                  # (Waisen-ffmpeg schrieb sonst nach re-exec weiter)
        self.enroll_warnung = None                # letzte Drift-Waechter-Warnung (UI/System)
        os.makedirs(os.path.join(cfg["data_dir"], "learn", "enroll"), exist_ok=True)
        self.lock = threading.Lock()
        # Nachbesserung W1b: der Koerper-Strang (_person_live) laeuft in einem
        # daemon-Thread, der self.lock UEBERLEBT (voller Decode + Pose + DINOv2 +
        # SVM in-Prozess). 'Live laeuft' ist deshalb self.lock ODER dieser
        # Zaehler > 0 (_live_aktiv) — self.lock allein uebersah genau die
        # CPU-schwersten Installationen (Koerper-Strang opt-in, Issue-#21-Klasse).
        self._personlive_lock = threading.Lock()
        self._personlive_aktiv = 0
        self.logbuf = collections.deque(maxlen=300)   # Dienst-Log fuer Webview /log
        # .173 Auto-Default (User-Go 10.08.): Erst-Boot-Entscheid HIER im __init__ —
        # vor Publisher/Trigger/Web, es kann noch kein Event verarbeitet worden sein.
        self._kette_auto_default()

    def _load_processed(self):
        done = set()
        if os.path.exists(self.log_path):
            with open(self.log_path) as f:
                for line in f:
                    try:
                        done.add(json.loads(line)["eid"])
                    except Exception:
                        pass
        return done

    def _load_last_seen(self):
        seen = {}
        if os.path.exists(self.log_path):
            with open(self.log_path) as f:
                for line in f:
                    try:
                        d = json.loads(line)
                        for p in d.get("bestaetigt") or []:
                            seen[p] = max(seen.get(p, 0), d.get("start") or d.get("ts") or 0)
                    except Exception:
                        pass
        return seen

    def _load_own_writes(self):
        eids = set()
        p = os.path.join(self.cfg["data_dir"], "state", "sublabel_writes.jsonl")
        if os.path.exists(p):
            with open(p) as f:
                for l in f:
                    try:
                        eids.add(json.loads(l)["eid"])
                    except Exception:
                        pass
        return eids

    def _writes_append(self, **d):
        with open(os.path.join(self.cfg["data_dir"], "state", "sublabel_writes.jsonl"), "a") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **d}, ensure_ascii=False) + "\n")
            f.flush()

    def _maybe_sublabel(self, entry, nachhol=0):
        """AP2 (User-Entscheid: sofort aktiv): bestaetigte Person nach Frigate schreiben.
        Echo-Freiheit nach Plan §1: writes-Protokoll VOR dem POST; Gegenpruefung mit
        Retry (Frigate persistiert asynchron, AP0-Befund ~3 s)."""
        cfg = self.cfg
        if not cfg["sub_label_schreiben"] or not entry["bestaetigt"] or self.dry_alert:
            return None
        eid = entry["eid"]
        top = max(entry["bestaetigt"], key=lambda p: (entry["ours"].get(p) or {}).get("max") or 0)
        if eid in self.own_writes or entry["frigate"].get("label") == top:
            return None                       # schon von uns geschrieben / Frigate sagt es selbst
        if nachhol and entry["frigate"].get("label"):
            self.log(f"{eid}: catch-up — Frigate meanwhile carries "
                     f"'{entry['frigate']['label']}', will NOT be overwritten")
            return None                       # rueckwirkend nie eine zwischenzeitliche Korrektur ueberschreiben
        cos = (entry["ours"].get(top) or {}).get("max") or 0
        score = round(1.0 / (1.0 + math.exp(-20.0 * (cos - 0.3))), 3)
        if frigate_read_only(cfg):                # Vertrauensphase: NICHT schreiben, nur protokollieren
            self._writes_append(eid=eid, label=top, score=score, cos=cos, readonly=True)
            self.log(f"{eid}: read-only — would set sub_label -> '{top}' ({score}), Frigate NOT modified")
            return None
        self._writes_append(eid=eid, label=top, score=score, cos=cos)
        self.own_writes.add(eid)
        try:
            api_post(cfg, f"/api/events/{eid}/sub_label", {"subLabel": top, "subLabelScore": score})
            for wartezeit in (2, 6):
                time.sleep(wartezeit)
                if api(cfg, f"/api/events/{eid}").get("sub_label") == top:
                    self.log(f"{eid}: sub_label -> '{top}' ({score}) written + verified")
                    return top
            self.log(f"{eid}: sub_label write without GET echo (async? check later)")
            return top
        except Exception as e:
            self.log(f"{eid}: sub_label write failed: {e}")
            return None

    # Modulumbau R3: MQTT-Publisher lebt in core/melden.py (Docstrings/
    # Begruendungen dort). Hier nur Einhaenge: der Dienst bleibt Halter von
    # self.pub/self.letzter_hb (der Watchdog prueft weiter DENSELBEN Client),
    # core/melden bekommt Zugriff als Callables — Injektion pur, kein Rueckimport.
    def _mqtt_pub(self, topic, payload, retain=False, herkunft=None):
        return _melden.mqtt_pub(self.pub, self.log, topic, payload,
                                retain=retain, herkunft=herkunft)

    _mqtt_herkunft = staticmethod(_melden.mqtt_herkunft)

    def start_publisher(self):
        def pub_setzen(client):
            self.pub = client

        def hb_setzen():
            self.letzter_hb = time.time()
        _melden.publisher_starten(self.cfg, self.log,
                                  pub_setzen=pub_setzen,
                                  pub_holen=lambda: self.pub,
                                  processed_len=lambda: len(self.processed),
                                  hb_setzen=hb_setzen)

    def _szene_unbekannt_pruefen(self, entry):
        """Szenen-Karenz (User 18.07.): fremd_verdacht wird erst nach szene_karenz_s
        gemeldet — und NUR, wenn im Fenster [Event-Start − Karenz, jetzt] auf KEINER
        Kamera jemand bestaetigt wurde. Verhindert Fehlalarm durch schlechte
        Einzel-Schnipsel eines bekannten Durchgangs (bis zur echten v1.1-Fusion)."""
        karenz = int(self.cfg.get("szene_karenz_s", 90))
        start = entry.get("start") or entry["ts"]

        def entscheiden():
            # symmetrisches Szenen-Fenster ±karenz um den VORFALL (Event-Zeiten beidseits).
            # Ueber einen SNAPSHOT iterieren: last_seen wird aus den Verarbeitungs-Threads
            # geschrieben, waehrend dieser Timer-Thread laeuft — ein "dictionary changed size
            # during iteration" haette den Timer-Thread still getoetet und den fremd_verdacht
            # damit komplett verschluckt (kein Alert, keine Logzeile).
            snap = dict(self.last_seen)
            erkannt = [p for p, ts in snap.items()
                       if start - karenz <= ts <= start + karenz]
            if erkannt:
                self.log(f"{entry['eid']}: fremd_verdacht defused by scene context "
                         f"(recognized in the window: {', '.join(sorted(erkannt))})")
                return
            if self._ist_ignorierter_besucher(entry):        # User 21.07.: "Ignorieren" = kein Alert
                self.log(f"{entry['eid']}: fremd_verdacht suppressed (ignored visitor)")
                return
            # Areas Stufe 1: Meldungen NENNEN die Area (Text + additives MQTT-Feld areas[]),
            # Verhalten/Anzahl/Timing unveraendert — Melde-Scoping je Area kommt mit Stufe 2.
            _ar = _areas_mod.kamera_areas(_areas_mod.normalisieren(self.cfg.get("areas")),
                                          entry["camera"])
            if self._mqtt_pub(_melden.topic(self.cfg, "szene_unbekannt"), json.dumps(
                    {"eid": entry["eid"], "camera": entry["camera"], "areas": _ar,
                     "ts": entry.get("start") or entry["ts"],      # Vorfalls-Zeit fuer die Caption
                     "max_bw": entry.get("max_bw")}, ensure_ascii=False)):
                self.log(f"SCENE unknown: {entry['eid']} ({entry['camera']}"
                         f"{' · ' + ' + '.join(_ar) if _ar else ''}) — "
                         f"nobody recognized in the {karenz}s window")
            self._telegram_melden("unbekannt", entry)
            self._szenario_nachsammeln()             # sofort sammeln+clustern statt bis 06:00 warten (User 21.07.)
        threading.Timer(karenz, entscheiden).start()

    def _ist_ignorierter_besucher(self, entry):
        """True, wenn das Gesicht dieses Unbekannt-Events zu einer als 'Ignorieren' markierten
        Unbekannt-Identitaet gehoert (Cosinus >= besucher_sim) — dann kein Alert (User 21.07.,
        'Ignorieren' soll wiederkehrende Fremde wie die Heckencrew ruhigstellen). KONSERVATIV:
        bei Unsicherheit (keine besucher-Identitaet, kein Embedding) NICHT unterdruecken —
        lieber ein Alert zu viel als einen echten Fremden verschluckt."""
        try:
            import anlernen
            import numpy as _np
            besucher = [u for u in anlernen.lade_unbekannte() if u.get("status") == "besucher"]
            if not besucher:
                return False
            faces = {g["id"]: g for g in anlernen.lade_gesichter()}
            V = [faces[m]["emb"] for u in besucher for m in u.get("members", [])
                 if faces.get(m) and faces[m].get("emb")]
            if not V:
                return False
            V = _np.asarray(V, dtype=_np.float32)
            V = V / (_np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
            kp = os.path.join(self.cfg["data_dir"], "events", str(entry["eid"]), "kandidaten.jsonl")
            E = []
            if os.path.exists(kp):
                for line in open(kp):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line).get("emb")
                    except Exception:
                        continue
                    if e and len(e) == 512:
                        E.append(e)
            if not E:
                return False
            E = _np.asarray(E, dtype=_np.float32)
            E = E / (_np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
            return float((E @ V.T).max()) >= float(self.cfg.get("besucher_sim", 0.50))
        except Exception as e:
            self.log(f"visitor check error: {e}")
            return False

    def _szenario_nachsammeln(self):
        """Nach einem abgeschlossenen UNBEKANNTEN Szenario (Szenen-Karenz vorbei, niemand Bekanntes
        im Fenster, kein ignorierter Besucher) sofort die neuen Gesichter sammeln + clustern, statt
        bis zum 06:00-Job zu warten (User 21.07.). Serialisiert (ein Lauf gleichzeitig) + gethrottled;
        dank geprueft.jsonl werden nur wirklich NEUE Events verarbeitet, also Sekundensache. Der
        06:00-Job bleibt Sicherheitsnetz + eigentliche Wartung (Pool-Pruefung/Referenz-QS/Backup)."""
        with self._sammel_lock:
            if self._sammel_laeuft:
                self._sammel_nachhol = True              # laeuft schon -> nach dem Lauf EINMAL nachziehen
                return
            self._sammel_laeuft = True

        def lauf():
            try:
                out, fehler = self._sammle_fahren(tage=0.1, mit_migriere=False, timeout=600)
                if fehler:
                    self.log(f"scenario collection FAILED: {fehler}")
                else:
                    m = re.search(r"(\d+) faces collected", out or "")
                    if m and int(m.group(1)) > 0:            # nur bei echten neuen Gesichtern clustern
                        import anlernen
                        idents, _ = anlernen.reconcile_unbekannte()   # nimmt selbst den pool_lock
                        self.log(f"scenario collection: {m.group(1)} new faces, "
                                 f"{len(idents)} unknown identities")
            except subprocess.TimeoutExpired:
                self.log("scenario collection TIMEOUT (>10 min)")
            except Exception as e:
                self.log(f"scenario collection error: {e}")
            finally:
                with self._sammel_lock:
                    nachhol = self._sammel_nachhol
                    self._sammel_nachhol = False
                    self._sammel_laeuft = False
                if nachhol:
                    self._szenario_nachsammeln()             # ausstehenden Durchgang nachziehen
        try:
            threading.Thread(target=lauf, daemon=True).start()
        except Exception as e:                               # Thread-Start-Fehler -> Flag nicht haengen lassen (Review 21.07.)
            with self._sammel_lock:
                self._sammel_laeuft = False
            self.log(f"scenario collection thread start error: {e}")

    def _nachlern_anstossen(self, person):
        """Nach einem abgeschlossenen Durchgang mit einer erkannten BEKANNTEN Person die
        Nachlern-Vorschlaege (vorschlaege_person) automatisch aktualisieren — 'am Ende des
        Durchgangs, ohne Klick' (User 21.07.). Debounce pro Person: jeder neue Treffer setzt
        den szene_karenz_s-Timer zurueck, sodass die Suche GENAU EINMAL laeuft, wenn seit dem
        letzten Auftritt der Person die Karenz vorbei ist. Das ANWENDEN bleibt manuell (ein
        falsch zugeordnetes Gesicht wuerde die Person vergiften) — nur das Bereitstellen
        laeuft automatisch."""
        karenz = int(self.cfg.get("szene_karenz_s", 90))
        with self._nachlern_lock:
            alt = self._nachlern_timer.get(person)
            if alt:
                alt.cancel()
            t = threading.Timer(karenz, self._nachlern_lauf)
            t.args = (person, t)                             # Timer-Token: nur GENAU dieser Timer darf sich austragen (Review 21.07.)
            t.daemon = True
            self._nachlern_timer[person] = t
            t.start()

    def _nachlern_lauf(self, person, mein_timer):
        with self._nachlern_lock:
            if self._nachlern_timer.get(person) is not mein_timer:
                return                                       # ein neuerer Timer hat uebernommen -> No-op (kein Doppellauf)
            self._nachlern_timer.pop(person, None)
        self.vorschlaege_starten(person)                     # async, hat eigenen _vs_laeuft-Guard

    # Modulumbau R3: Szenen-Telegram + Transcode-Lauf leben in core/melden.py
    # (Docstrings/Begruendungen dort). Hier nur Einhaenge: Drossel-Zustand
    # (_melde_zustand), Transcode-Registry (_review_lock/_transcode_procs — eine
    # Lock-Quelle, Definition bleibt im Service) und die Bild-/Encoder-Quellen
    # reicht der Dienst als Parameter/Callables herein.
    def publish_erkennung(self, entry):
        _melden.publish_erkennung(self.cfg, self.pub, self.log, self.debug, entry)

    def _telegram_melden(self, art, entry, personen=None):
        _melden.telegram_melden(self.cfg, self.log, self.dry_alert,
                                self._melde_zustand, self._best_crop,
                                self._telegram_clip, self._telegram_ha_script,
                                art, entry, personen)

    def _telegram_ha_script(self, eid, camera, caption):
        _melden.telegram_ha_script(self.cfg, self.log, self._melde_zustand,
                                   eid, camera, caption)

    def _transcode_lauf(self, cmd, timeout):
        return _melden.transcode_lauf(cmd, timeout, self._review_lock,
                                      self._transcode_procs)

    def transcodes_killen(self):
        _melden.transcodes_killen(self._review_lock, self._transcode_procs)

    def _telegram_clip(self, eid):
        return _melden.telegram_clip(self.cfg, self.log, self._transcode_lauf,
                                     transcode_kommandos, video_encoder, eid)

    # ---------------------------------------------------------- Wartung + Watchdog (AP6/AP7)
    def qs_bericht_erzeugen(self, tage=14):
        """Konzept §4: pro Kamera Events / verwertbare Gesichter / Bestaetigungen /
        Fenster-Quote ueber die letzten N Tage -> qs_bericht.json (System-Seite)."""
        grenze = time.time() - tage * 86400
        by = {}
        if os.path.exists(self.log_path):
            with open(self.log_path) as f:
                for l in f:
                    try:
                        r = json.loads(l)
                        if r.get("eid") and (r.get("start") or r.get("ts", 0)) >= grenze:
                            by[r["eid"]] = r
                    except Exception:
                        pass
        kameras = {}
        for r in by.values():
            k = kameras.setdefault(r.get("camera", "?"),
                                   {"events": 0, "mit_gesicht": 0, "bestaetigt": 0,
                                    "unvollstaendig": 0})
            k["events"] += 1
            if r.get("faces_geprueft", r.get("faces") or 0) > 0:   # #42 Teil B: gefilterte Zahl
                k["mit_gesicht"] += 1
            if r.get("bestaetigt"):
                k["bestaetigt"] += 1
            if r.get("frames_fehlen"):           # W1-Telemetrie: stiller Verlust wird Betriebsgroesse
                k["unvollstaendig"] += 1
        for k in kameras.values():
            k["fenster_quote"] = round(100 * k["bestaetigt"] / k["mit_gesicht"]) if k["mit_gesicht"] else 0
        # atomar + Datei sauber schliessen (frueher: json.dump in ein offenes, nie geschlossenes
        # open(...) direkt auf den Zielpfad -> ein Abbruch liess die QS-Karte halb/leer zurueck)
        qp = os.path.join(self.cfg["data_dir"], "state", "qs_bericht.json")
        qtmp = f"{qp}.tmp-{os.getpid()}"
        try:
            with open(qtmp, "w") as f:
                json.dump({"stand": datetime.datetime.now().strftime("%d.%m. %H:%M"),
                           "zeitraum_tage": tage, "kameras": kameras}, f,
                          ensure_ascii=False, indent=1)
                f.flush()
                os.fsync(f.fileno())
            os.replace(qtmp, qp)
        except Exception as e:
            try:
                os.remove(qtmp)
            except OSError:
                pass
            self.log(f"QS report NOT written: {e}")
            return
        self.log(f"QS report written ({len(by)} events / {tage} days)")

    def master_backup(self):
        """AP7: taegliches tar des Masters + aller Wahrheits-Dateien, 14 Staende rotierend."""
        import tarfile
        bdir = os.path.join(self.cfg["data_dir"], "backups")
        os.makedirs(bdir, exist_ok=True)
        ziel = os.path.join(bdir, f"master_{datetime.datetime.now():%Y%m%d}.tar.gz")
        if os.path.exists(ziel):
            return
        # Pfade seit dem Layout-Umbau 22.07. GENESTET (refs->faces, *.jsonl->state/, enroll->learn/).
        # Vorher standen hier die flachen Alt-Pfade: alle exists()-Checks schlugen fehl und das
        # Backup war 24 h lang ein leeres 65-Byte-tar — STILL. Daher unten der Leer-Guard.
        # Quellen im data_dir. WICHTIG (24.07.): frueher fehlten config/config.json (Live-Config
        # INKL. Notification-Secrets — nur das Audit-Log war dabei) und der reale learn/-Pool
        # (Unbekannt-Identitaeten, gesichter/geprueft/crops/vorschlaege; gesichert war nur der stale
        # learn/enroll). Jetzt ganzes learn/ statt Einzeldateien, damit kuenftige Pool-Dateien
        # automatisch mitkommen; die Laufzeit-Lock (pool.lock) wird ausgefiltert.
        QUELLEN = ("faces", "config/config.json", "config/config_audit.jsonl",
                   "state/ground_truth.jsonl", "state/sublabel_writes.jsonl",
                   "state/deckung.jsonl", "learn")
        gefunden, fehlend = [], []
        # ATOMAR (tmp + fsync + os.replace): frueher schrieb tarfile DIREKT auf `ziel`. Brach der
        # Lauf mittendrin ab (Stromausfall, OOM — bis 0.1.0.21 auch jedes `docker stop` per SIGKILL),
        # blieb ein TORSO liegen, und der exists()-Guard oben hielt ihn fuer erledigt: das Backup des
        # Tages wurde nie wiederholt, das Archiv war unbrauchbar und niemand erfuhr davon.
        # Jetzt entsteht `ziel` erst, wenn das Archiv vollstaendig und auf Platte ist.
        tmp = f"{ziel}.tmp-{os.getpid()}"
        try:
            with open(tmp, "wb") as fh:
                with tarfile.open(fileobj=fh, mode="w:gz") as t:
                    for rel in QUELLEN:
                        p = os.path.join(self.cfg["data_dir"], rel)
                        if os.path.exists(p):
                            t.add(p, arcname=rel,
                                  filter=lambda ti: None if ti.name.endswith("pool.lock") else ti)
                            gefunden.append(rel)
                        else:
                            fehlend.append(rel)
                fh.flush()
                os.fsync(fh.fileno())
        except Exception as e:                # Schreibfehler NIE verschlucken (Fehlerklasse C)
            try:
                os.remove(tmp)
            except OSError:
                pass
            self.log(f"!! MASTER BACKUP FAILED: {e} — nothing backed up, next run will retry")
            if not self.dry_alert:
                try:
                    push(self.cfg, "suslik-Stoerung", f"Master-Backup fehlgeschlagen: {e}", None)
                except Exception as pe:
                    self.log(f"backup fault push failed: {pe}")
            return
        if not gefunden:                      # Total-Leere: nie wieder still scheitern — Archiv weg
            try:                              # (damit der naechste Lauf es erneut versucht) + laut
                os.remove(tmp)
            except Exception:
                pass
            self.log("!! MASTER BACKUP EMPTY: not a single source path found — layout changed? "
                     "(nothing backed up, archive discarded)")
            if not self.dry_alert:
                try:
                    push(self.cfg, "suslik-Stoerung",
                         "Master-Backup leer: Quellpfade nicht gefunden — Referenzen UNGESICHERT", None)
                except Exception as e:
                    self.log(f"backup fault push failed: {e}")
            return
        # Teil-Verlust-Guard: faces/ sind die nicht-reproduzierbaren Referenzen. Fehlen sie, WAEHREND
        # der Betrieb laeuft (state-Dateien vorhanden), ist das kein frischer Install, sondern ein
        # Pfad-/Layout-Problem -> laut melden, das Backup mit dem Rest aber behalten (Teil > nichts).
        if "faces" in fehlend and any(r.startswith("state/") for r in gefunden):
            self.log("!! master backup WITHOUT faces/ — references missing while the service is running (check)")
            if not self.dry_alert:
                try:
                    push(self.cfg, "suslik-Stoerung",
                         "Master-Backup ohne Referenzen (faces/) — Pfad/Layout pruefen", None)
                except Exception as e:
                    self.log(f"backup warning push failed: {e}")
        os.replace(tmp, ziel)                 # erst JETZT gilt das Backup als vorhanden/erledigt
        for f in os.listdir(bdir):            # Reste abgebrochener Laeufe (auch aelterer PIDs) weg
            if f.startswith("master_") and ".tmp-" in f:
                try:
                    os.remove(os.path.join(bdir, f))
                except OSError:
                    pass
        alte = sorted(f for f in os.listdir(bdir)
                      if f.startswith("master_") and f.endswith(".tar.gz"))    # nur fertige Staende
        for f in alte[:-14]:
            os.remove(os.path.join(bdir, f))
        self.log(f"master backup: {os.path.basename(ziel)} ({len(alte[-14:])} snapshots) — "
                 f"{len(gefunden)} sources, missing: {', '.join(fehlend) if fehlend else '—'}")

    def deckung_rotieren(self):
        """AP7: monatlich — Zeilen aelter 7 Tage ins Archiv, aktive Datei behaelt den
        Ueberlapp (processed/last_seen/Sweep bleiben korrekt, QS-Auflage)."""
        grenze = time.time() - 7 * 86400
        adir = os.path.join(self.cfg["data_dir"], "state", "archiv")
        os.makedirs(adir, exist_ok=True)
        # Read-Rewrite-Replace MUSS unter self.lock: sonst kann eine Zeile, die process()
        # zwischen Lesen und Ersetzen anhaengt, verlorengehen (Bestandsfehler). Fuer den
        # Nachhol-Zaehler waere das fatal — Versuch verbraucht, Ergebniszeile weg.
        with self.lock:
            behalten, archiv = [], []
            with open(self.log_path) as f:
                for l in f:
                    try:
                        (behalten if json.loads(l).get("ts", 0) >= grenze else archiv).append(l)
                    except Exception:
                        behalten.append(l)
            if not archiv:
                return
            with open(os.path.join(adir, f"deckung_{datetime.datetime.now():%Y-%m}.jsonl"), "a") as f:
                f.writelines(archiv)
            tmp = self.log_path + ".neu"
            with open(tmp, "w") as f:
                f.writelines(behalten)
                f.flush()
                os.fsync(f.fileno())      # deckung.jsonl ist die zentrale Akte: ohne fsync koennte
            os.replace(tmp, self.log_path)   # nach Stromausfall eine LEERE Datei unter dem gueltigen
                                             # Namen stehen — die Rotation haette das Log dann geloescht
        self.log(f"deckung.jsonl rotated: {len(archiv)} lines archived, {len(behalten)} kept (7-day overlap)")

    def crops_retention(self):
        """AP7: events/-Ordner aelter 60 Tage OHNE GT-Label loeschen."""
        import shutil
        gt = set()
        gtp = os.path.join(self.cfg["data_dir"], "state", "ground_truth.jsonl")
        if os.path.exists(gtp):
            with open(gtp) as f:
                for l in f:
                    try:
                        gt.add(json.loads(l)["eid"])
                    except Exception:
                        pass
        basis = os.path.join(self.cfg["data_dir"], "events")
        grenze = time.time() - 60 * 86400
        n = 0
        for d in os.listdir(basis):
            p = os.path.join(basis, d)
            if os.path.isdir(p) and d not in gt and os.path.getmtime(p) < grenze:
                shutil.rmtree(p, ignore_errors=True)
                n += 1
        if n:
            self.log(f"crops retention: {n} event folders older than 60 days (no GT) deleted")

    def update_check(self):
        """#53 (User 26.07.): 1x taeglich anonym die neueste Release-Version von GitHub holen
        und als dezente Kopfzeilen-Marke anzeigen — Installationen draussen erfahren sonst NIE
        von Updates. Bewusst die EINZIGE neue Aussenverbindung neben den Meldekanaelen:
        Config-Key 'update_check' (Default an) schaltet sie komplett ab; es geht nur ein
        GET auf die oeffentliche Releases-API raus, nichts ueber das System hinaus.
        Ergebnis atomar nach state/update_check.json (uebersteht Neustarts); Fehler sind
        leise (debug) — ein Offline-System ist kein Stoerfall."""
        import webui
        if not self.cfg.get("update_check", True):
            webui.UPDATE_INFO = None
            return
        p = os.path.join(self.cfg["data_dir"], "state", "update_check.json")
        try:
            with open(p) as f:
                d = json.load(f) or {}
        except Exception:
            d = {}
        # 20-h-Drossel gegen Neustart-Serien (Wizard/Config-Neustarts laufen alle durch den
        # Wartungs-Thread-Sofortlauf — GitHub soll davon genau einen Ping am Tag sehen).
        if time.time() - (d.get("ts") or 0) >= 20 * 3600:
            try:
                req = urllib.request.Request(
                    "https://api.github.com/repos/BennoBaer-dev/suslik/releases/latest",
                    headers={"User-Agent": f"suslik/{os.environ.get('SUSLIK_VERSION', 'dev')}",
                             "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    rel = json.load(r)
                d = {"ts": round(time.time(), 1), "tag": str(rel.get("tag_name") or ""),
                     "url": str(rel.get("html_url") or "")}
                tmp = f"{p}.tmp-{os.getpid()}"
                with open(tmp, "w") as f:
                    json.dump(d, f)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, p)
            except Exception as e:
                self.debug(f"update check failed (offline is fine): {e}")
        neu = _version_neuer(d.get("tag"), os.environ.get("SUSLIK_VERSION", ""))
        webui.UPDATE_INFO = ({"tag": d["tag"], "url": d.get("url") or
                              "https://github.com/BennoBaer-dev/suslik/releases"} if neu else None)
        if neu and d.get("tag") != getattr(self, "_upd_gemeldet", None):
            self._upd_gemeldet = d["tag"]     # genau EINE Logzeile je entdeckter Version
            self.log(f"update check: {d['tag']} is available on GitHub "
                     f"(running {os.environ.get('SUSLIK_VERSION', 'dev')})")

    def qs_neu_starten(self):
        """Referenz-QS im Hintergrund (separater Prozess) neu berechnen — nach jedem Anlernen/
        Entfernen und auf Knopfdruck. Doppelstart-Guard: parallele Laeufe wuerden sich GPU und
        das JSON-Schreiben streiten (Einzel-Loeschungen kommen sonst im Sekundentakt)."""
        with self._qs_lock:
            if self._qs_laeuft:
                self._qs_nochmal = True            # nicht still verwerfen: nach dem Lauf nachholen
                return
            self._qs_laeuft = True

        def job():
            try:
                env = dict(os.environ, OV_DEVICE=self.cfg["ov_device"])
                with self._gpu_bg_lock:                       # gegen die anderen GPU-Hintergrund-Jobs serialisieren (Review 21.07.)
                    subprocess.run([sys.executable,
                                    os.path.join(HERE, "anlernen.py"), "pruefe",
                                    "--unscharf", str(self.cfg.get("unscharf_max", 350)),
                                    "--minkante", str(self.cfg.get("min_kante", 70))],
                                   capture_output=True, timeout=600, check=False, env=env,
                                   preexec_fn=_analyse_nice)   # Issue #21, s. ANALYSE_NICE
                self.log("reference QS recalculated")
            finally:
                with self._qs_lock:
                    self._qs_laeuft = False
                    nochmal, self._qs_nochmal = self._qs_nochmal, False
            if nochmal:                            # waehrend des Laufs kam eine Aenderung
                self.qs_neu_starten()
        threading.Thread(target=job, daemon=True).start()

    def vorschlaege_starten(self, person):
        """Bestands-Suche fuer eine Person im Hintergrund (separater Prozess, GPU);
        je Person nur ein Lauf gleichzeitig."""
        with self._qs_lock:
            if person in self._vs_laeuft:
                return
            self._vs_laeuft.add(person)

        def job():
            try:
                env = dict(os.environ, OV_DEVICE=self.cfg["ov_device"])
                with self._gpu_bg_lock:                       # nicht K Personen parallel auf die GPU (Review 21.07.)
                    subprocess.run([sys.executable,
                                    os.path.join(HERE, "anlernen.py"), "vorschlaege", person,
                                    "--unscharf", str(self.cfg.get("unscharf_max", 350)),
                                    "--minkante", str(self.cfg.get("min_kante", 70))],
                                   capture_output=True, timeout=900, check=False, env=env,
                                   preexec_fn=_analyse_nice)   # Issue #21, s. ANALYSE_NICE
                self.log(f"reference search for {person} finished")
            finally:
                with self._qs_lock:
                    self._vs_laeuft.discard(person)
        threading.Thread(target=job, daemon=True).start()

    def anlern_nachpruefung_starten(self, person, betroffen):
        """Issue #19 Teil 2: nach dem Anlernen die EVENTS der uebernommenen Gesichter im
        Hintergrund gegen die neue Referenzbibliothek pruefen (anlernen.py nachpruefen,
        Embedding-Vergleich, keine Video-Neuanalyse) und je bestaetigtem Event die
        deckung-Akte korrigieren — vorher blieben die Karten der gerade angelernten
        Person als "Unknown" stehen (Repro: 4/4 angelernte eids weiter bestaetigt=[]).
        Subprozess-Muster wie vorschlaege_starten, MIT _gpu_bg_lock (Widerleger 11.08.:
        die fruehere Fassung lud die KOMPLETTE Referenzbibliothek — 674 s auf CPU bei
        260 Bildern — und kollidierte ungelockt mit dem qs_neu_starten desselben
        Klicks; seitdem laedt anlernen.nachpruefe_events nur noch die Referenzen der
        EINEN Person, der Lock bleibt trotzdem: Embedder-Bau + Einbettung gehoeren
        serialisiert). Uebergabe/Ergebnis je Lauf in eigener Datei unter state/
        (stdout ist durch die Modell-Lade-Prints kein Kanal)."""
        faces = [f for f in (betroffen or []) if f.get("eid") and f.get("emb")]
        if not faces:
            return

        def job():
            pfad = os.path.join(self.cfg["data_dir"], "state",
                                f"anlern_nachpruefung_{os.getpid()}_{threading.get_ident()}.json")
            try:
                with open(pfad, "w") as f:
                    json.dump(faces, f)
                env = dict(os.environ, OV_DEVICE=self.cfg["ov_device"])
                with self._gpu_bg_lock:               # gegen qs_neu_starten/vorschlaege desselben Klicks (Widerleger 11.08.)
                    r = subprocess.run([sys.executable, os.path.join(HERE, "anlernen.py"),
                                        "nachpruefen", person, pfad],
                                       capture_output=True, timeout=900, check=False, env=env,
                                       preexec_fn=_analyse_nice)   # Issue #21, s. ANALYSE_NICE
                if not os.path.exists(pfad + ".ergebnis"):
                    self.log(f"enroll re-check FAILED rc={r.returncode}: "
                             f"{(r.stderr or b'').decode(errors='replace')[-300:]}")
                    return
                erg = json.load(open(pfad + ".ergebnis"))
                schwelle = erg.get("schwelle")
                for eid, e in sorted((erg.get("events") or {}).items()):
                    if e.get("bestaetigt"):
                        self._deckung_korrektur(eid, person, e.get("sim"), "anlernen", schwelle)
                    else:
                        self.log(f"{eid}: enroll re-check NOT confirmed "
                                 f"(sim {e.get('sim')} < {schwelle}) — card stays")
            except Exception as e:
                self.log(f"enroll re-check error: {type(e).__name__}: {e}")
            finally:
                for p in (pfad, pfad + ".ergebnis"):
                    try:
                        os.remove(p)
                    except FileNotFoundError:
                        pass
        threading.Thread(target=job, daemon=True).start()

    def _deckung_korrektur(self, eid, person, sim, quelle, schwelle=None):
        """Issue #19: ein nachtraeglich bestaetigtes Event in der deckung-Akte korrigieren —
        als ANGEHAENGTE Zeile (last-wins-Muster der Akte, kein Rewrite), unter self.lock
        wie der process()-Append (_deckung_by_eid nimmt self.lock selbst NICHT — auf
        genau dieser Invariante steht dieser with-Block, threading.Lock ist nicht
        reentrant). Gehoben werden NUR ts/bestaetigt/kategorie/kategorie_v1; die
        Kategorien kommen aus der EINEN zentralen Quelle verdict/verdict_v2
        (confirmed-Override). `ours` bleibt UNANGETASTET (Widerleger 11.08.): die
        Nachpruef-sim ist die Aehnlichkeit des gerade angelernten Crops zu sich selbst
        (~0.99), keine Live-Messung — sie steht ehrlich im korrektur-Marker, nie als
        Mess-Score in ours. alerted/presence_push/sublabel/frames bleiben historische
        Wahrheit — sonst faelschte die Korrektur die Alert-Tageszahl. Events mit
        Basis-Kategorie fehler/no_person werden NICHT gehoben (dort lief nie eine
        tragende Analyse bzw. war keine Person — eine Bestaetigung wuerde das
        maskieren). Kein Alarm, kein MQTT, kein sublabel; ground_truth.jsonl
        unberuehrt."""
        with self.lock:
            basis = self._deckung_by_eid().get(eid)
            if not basis:
                self.log(f"{eid}: enroll re-check confirmed, but no deckung record — skipped")
                return
            if basis.get("kategorie") in ("fehler", "no_person"):
                self.log(f"{eid}: enroll re-check confirmed, but record says "
                         f"'{basis.get('kategorie')}' — not corrected (no analysis to lift)")
                return
            z = dict(basis)
            z["ts"] = round(time.time(), 1)
            ours = z.get("ours") or {}
            confirmed = sorted(set((z.get("bestaetigt") or []) + [person]))
            kategorie, _ = verdict_v2(self.cfg, ours, z.get("max_bw"), confirmed=confirmed)
            kategorie_v1, _ = verdict(self.cfg, (z.get("frigate") or {}).get("label"),
                                      ours, confirmed=confirmed)
            z["bestaetigt"] = confirmed
            z["kategorie"] = kategorie
            z["kategorie_v1"] = kategorie_v1
            z["korrektur"] = {"quelle": quelle, "person": person, "sim": sim,
                              **({"schwelle": schwelle} if schwelle is not None else {})}
            with open(self.log_path, "a") as f:
                f.write(json.dumps(z, ensure_ascii=False) + "\n")
                f.flush()
        self.log(f"{eid}: record corrected after enrolling — now '{kategorie}' "
                 f"({person}, sim {sim})")

    # ENTFERNT 0.1.0.45 (User 27.07.): suslik loescht NIE in Frigate. Richtung Frigate gibt
    # es nur Holen (Import) und Schicken (Export) — eine Fern-Loeschung muesste zu 100 %
    # sicher das Richtige treffen und lief hier ohnehin ueber einen nicht portablen SSH-Weg,
    # der seit dem Container-Umzug scheiterte und dabei irrefuehrend meldete. Den Re-Import
    # lokal geloeschter Bilder verhindert der Tombstone in refs_meta (anlernen.entferne_referenz);
    # eine in Frigate liegende Kopie bleibt bewusst unangetastet.

    def frigate_sync_export(self):
        """Falls frigate_sync an: aktive Master-Bilder, die Frigate fehlen, ueber die
        Frigate-HTTP-API hochladen (separater Prozess, sync_refs.py export).
        Fuer Parallelbetrieb Frigate-Face + verifyd."""
        if not self.cfg.get("frigate_sync") or frigate_read_only(self.cfg):
            return
        # Seit 0.1.0.108 laeuft der Export ueber die Frigate-HTTP-API (sync_refs.api_upload).
        # Die alte ssh/scp-Vorbedingung MUSSTE hier weg: ssh/scp liegen bewusst nicht im
        # Image, die Wache haette den API-Export also dauerhaft gesperrt (Selbstfund beim
        # Doku-Durchgang .107 — die Umstellung waere fuer Nutzer wirkungslos geblieben).
        if not (self.cfg.get("frigate_url") or "").strip():
            if not getattr(self, "_sync_url_gemeldet", False):
                self._sync_url_gemeldet = True
                self.log("frigate_sync: no Frigate URL configured — export skipped")
            return
        def job():
            # .134 Lauf-Riegel: laeuft ein manueller Sync, kapert der Auto-Export
            # sonst dessen Status-/Ergebnis-Dateien — dann lieber diese Runde
            # auslassen (der naechste Anlass exportiert nach).
            if getattr(self, "_sync_job_aktiv", False):
                self.log("frigate_sync: a manual sync is running — auto export skipped")
                return
            self._sync_job_aktiv = True
            try:
                env = dict(os.environ, OV_DEVICE=self.cfg["ov_device"])
                # --force: der Dienst hat frigate_read_only oben selbst geprueft; der
                # CLI-Riegel in cmd_export (.132) gilt fuer Hand-Laeufe ohne Dienst-Kontext.
                r = subprocess.run([sys.executable,
                                    os.path.join(HERE, "sync_refs.py"), "export", "--force"],
                                   capture_output=True, text=True, timeout=600, check=False, env=env)
            finally:
                self._sync_job_aktiv = False
            if r.returncode == 0:
                self.log("frigate_sync: master -> Frigate exported")
            else:                                  # Fehler NICHT verschlucken (frueher: immer 'exportiert')
                err = fehler_kern(r.stderr or r.stdout)
                self.log(f"!! frigate_sync: auto export FAILED (rc={r.returncode}): {err}")
        threading.Thread(target=job, daemon=True).start()

    def _reorganisieren(self):
        """Reorganisieren-Button (User 21.07.): Pool-Neupruefung (migriere: Modell-Konsistenz,
        bekannt-gewordene raus, tote Crops) + Identitaeten/Cluster neu bilden (reconcile) +
        Referenz-QS. Laeuft als Subprozess ('anlernen.py reorganisieren'), der intern den pool_lock
        haelt und damit das kontinuierliche Sammeln pausiert, solange er laeuft ('Fleck'). Das
        SAMMELN laeuft kontinuierlich szenario-getriggert und ist hier bewusst NICHT dabei. Fehler
        werden geloggt + gepusht statt verschluckt. Doppelklick-Schutz via _reorg_laeuft.
        Rueckgabe: True gestartet, False laeuft schon."""
        with self._sammel_lock:
            if self._reorg_laeuft:
                return False
            self._reorg_laeuft = True

        def lauf():
            self.log("reorganize started ...")
            try:
                env = dict(os.environ, OV_DEVICE=self.cfg["ov_device"])
                r = subprocess.run([sys.executable,
                                    os.path.join(HERE, "anlernen.py"), "reorganisieren"],
                                   capture_output=True, text=True, timeout=1800, env=env,
                                   preexec_fn=_analyse_nice)   # Issue #21, s. ANALYSE_NICE
                if r.returncode != 0:
                    tail = " | ".join((r.stderr or r.stdout or "").strip().splitlines()[-3:])[:300]
                    self.log(f"REORGANIZE FAILED (exit {r.returncode}): {tail}")
                    push(self.cfg, "suslik: Reorganisieren fehlgeschlagen",
                         f"reorganisieren beendete mit exit {r.returncode}. {tail}", None)
                else:
                    m = re.search(r"Reorganized: (\d+) identities", r.stdout or "")
                    self.log(f"reorganize ok ({m.group(1) if m else '?'} unknown identities)")
                    self.qs_neu_starten()                # Referenz-QS mit erneuern
            except subprocess.TimeoutExpired:
                self.log("REORGANIZE TIMEOUT (>30 min)")
                push(self.cfg, "suslik: Reorganisieren-Timeout", "reorganisieren lief >30 min.", None)
            except Exception as e:
                self.log(f"reorganize error: {e}")
                push(self.cfg, "suslik: Reorganisieren-Fehler", str(e)[:200], None)
            finally:
                with self._sammel_lock:
                    self._reorg_laeuft = False
        try:
            threading.Thread(target=lauf, daemon=True).start()
            return True
        except Exception as e:                           # Thread-Start-Fehler -> Flag nicht haengen lassen
            with self._sammel_lock:
                self._reorg_laeuft = False
            self.log(f"reorganize thread start error: {e}")
            return False

    def _sammle_fahren(self, tage, mit_migriere, timeout):
        """anlernen-sammle fahren — durch den W2-Worker (worker=an, Kontext-Buendelung) oder
        als Subprozess (Fallback worker=aus). Rueckgabe (stdout_text, fehler|None); der
        Subprozess-Weg wirft bei Timeout weiter subprocess.TimeoutExpired (alter Kontrakt)."""
        w = self._worker()
        if w is not None:
            lp = os.path.join(self.cfg["data_dir"], "state", "sammle.log")
            open(lp, "w").close()
            with self._gpu_bg_lock:              # gegen vorschlaege/qs serialisieren (Review 21.07.)
                antwort = w.job({"typ": "sammle", "tage": tage,
                                 "mit_migriere": mit_migriere, "log": lp}, timeout)
            try:
                out = open(lp).read()
            except Exception:
                out = ""
            if antwort is None:
                return out, f"worker timeout ({timeout}s) or died"
            if not antwort.get("ok"):
                return out, str(antwort.get("fehler") or "unbekannt")
            return out, None
        env = dict(os.environ, OV_DEVICE=self.cfg["ov_device"])
        cmd = [sys.executable, os.path.join(HERE, "anlernen.py"), "sammle", "--tage", str(tage)]
        if not mit_migriere:
            cmd.append("--kein-migriere")
        with self._gpu_bg_lock:                  # gegen vorschlaege/qs/Netz serialisieren (Review 21.07.)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env,
                               preexec_fn=_analyse_nice)   # Issue #21, s. ANALYSE_NICE
        if r.returncode != 0:
            tail = " | ".join((r.stderr or r.stdout or "").strip().splitlines()[-3:])[:300]
            return (r.stdout or ""), f"exit {r.returncode}: {tail}"
        return (r.stdout or ""), None

    def _netz_sammeln(self):
        """Naechtliches Auffangnetz (06:00): breiter Sammel-Sweep MIT Modell-Neupruefung (migriere).
        Faengt schwache Durchgaenge, die der szenario-Trigger (nur fremd_verdacht) verpasst, und haelt
        den Unbekannt-Pool modell-konsistent (Review 21.07.). Dank geprueft.jsonl nur die verpassten
        Events -> nachts in Sekunden. Blockierend (laeuft im Wartungs-Thread); der pool_lock serialisiert
        gegen das kontinuierliche Sammeln, der _sammel_laeuft-Guard vermeidet parallelen GPU-Init."""
        with self._sammel_lock:
            if self._sammel_laeuft:
                # Sammeln ODER Ernte aktiv -> Netz heute auslassen, aber SAGEN
                # (Leitprinzip 3/§2.6: nichts faellt still aus; Widerleger .75)
                self.log("safety-net collection skipped for today "
                         "(collection or harvest active)")
                return
            self._sammel_laeuft = True
        try:
            out, fehler = self._sammle_fahren(tage=2, mit_migriere=True, timeout=1800)
            if fehler:
                self.log(f"SAFETY-NET COLLECTION FAILED: {fehler}")
                push(self.cfg, "suslik: Netz-Sammeln fehlgeschlagen",
                     f"sammle scheiterte: {fehler}", None)
            else:
                m = re.search(r"(\d+) faces collected", out or "")
                n = int(m.group(1)) if m else 0
                import anlernen
                idents, _ = anlernen.reconcile_unbekannte()
                self.log(f"safety-net collection ok ({n} new faces, {len(idents)} unknown identities)")
        except subprocess.TimeoutExpired:
            self.log("SAFETY-NET COLLECTION TIMEOUT (>30 min)")
            push(self.cfg, "suslik: Netz-Sammeln-Timeout", "sammle lief laenger als 30 min.", None)
        except Exception as e:
            self.log(f"safety-net collection error: {e}")
        finally:
            with self._sammel_lock:
                self._sammel_laeuft = False

    def start_wartung(self):
        """06:00-Job: QS-Bericht + Master-Backup + Crops-Retention + (monatlich) Rotation + schlankes
        Auffangnetz-Sammeln (Review 21.07.: faengt schwache Durchgaenge, die der szenario-Trigger
        verpasst, + haelt den Pool modell-konsistent). Das Sammeln laeuft im Normalfall kontinuierlich
        szenario-getriggert; das Netz ist nur Backstop (dank geprueft.jsonl nachts in Sekunden).
        Beim Start laeuft alles einmal sofort AUSSER dem GPU-Netz (nur taeglich, nicht bei Neustart)."""
        def lauf():
            erst = True
            while True:
                # JEDER Schritt in eigenem try/except: vorher hing alles an EINEM try — eine
                # Exception im ersten Schritt (z.B. QS-Bericht) uebersprang stillschweigend
                # Backup, Retention und Sammeln fuer diesen Tag. Genau der Fall, in dem das
                # Backup wochenlang ausbleibt, ohne dass es jemand merkt.
                jobs = [("QS report", self.qs_bericht_erzeugen),
                        ("master backup", self.master_backup),
                        ("crops retention", self.crops_retention),
                        ("update check", self.update_check)]
                if not erst:                             # GPU-Netz nur taeglich, nicht bei jedem Neustart
                    jobs.append(("safety-net collection", self._netz_sammeln))
                if datetime.datetime.now().day == 1:
                    jobs.append(("deckung rotation", self.deckung_rotieren))
                for name, fn in jobs:
                    try:
                        fn()
                    except Exception as e:
                        self.log(f"maintenance job '{name}' failed: {e}")
                erst = False
                jetzt = datetime.datetime.now()
                ziel = jetzt.replace(hour=6, minute=0, second=0, microsecond=0)
                if ziel <= jetzt:
                    ziel += datetime.timedelta(days=1)
                time.sleep(max(60, (ziel - jetzt).total_seconds()))
        threading.Thread(target=lauf, daemon=True).start()

    def _backup_frische_pruefen(self, melde):
        """Waechter-Regel: das juengste Master-Backup darf nicht aelter als 48 h sein.

        Der 06:00-Job kann aus vielen Gruenden ausfallen (volle Platte, Rechte, Exception im
        Tar). Ohne diese Regel faellt das erst auf, wenn man das Backup BRAUCHT — die
        schlimmstmoegliche Gelegenheit. 48 h statt 24 h, damit ein einzelner verpasster Lauf
        (Neustart kurz nach 06:00) nicht schon meldet."""
        bdir = os.path.join(self.cfg["data_dir"], "backups")
        try:
            staende = [os.path.join(bdir, f) for f in os.listdir(bdir)
                      if f.startswith("master_") and f.endswith(".tar.gz")]
        except OSError as e:
            melde("backup", f"Backup-Verzeichnis nicht lesbar ({bdir}): {e}")
            return
        if not staende:
            melde("backup", f"Kein einziges Master-Backup in {bdir} — 06:00-Job pruefen.")
            return
        alter_h = (time.time() - max(os.path.getmtime(p) for p in staende)) / 3600
        if alter_h > 48:
            melde("backup", f"Juengstes Master-Backup ist {alter_h:.0f} h alt (>48 h) — "
                            f"der 06:00-Job laeuft nicht durch. Log auf 'maintenance job' pruefen.")

    def start_stoerungswaechter(self):
        """AP7: dienstinterner Watchdog — Pushover bei stillem Ausfall (Plan-Kriterien).
        Prueft alle 10 min; je Grund max. ein Push pro 6 h."""
        self.letzte_aktivitaet = time.time()
        gemeldet = {}

        def melde(grund, text):
            if time.time() - gemeldet.get(grund, 0) < 6 * 3600:
                return
            gemeldet[grund] = time.time()
            self.log(f"STOERUNG ({grund}): {text}")
            if not self.dry_alert:
                for _f in stoerung_melden(self.cfg, text):
                    self.log(f"fault notify failed: {_f}")

        def lauf():
            while True:
                time.sleep(600)
                try:
                    jetzt = datetime.datetime.now()
                    if 7 <= jetzt.hour <= 22 and time.time() - self.letzte_aktivitaet > 4 * 3600:
                        melde("inaktiv", "Seit >4 h tagsueber kein Event verarbeitet/uebersprungen — "
                                         "MQTT/Frigate/Analyse pruefen.")
                    ff = self.frigate_fehler
                    if ff and time.time() - ff[0] < 900 and getattr(self, "frigate_fehlerserie", 0) >= 5:
                        melde("frigate", f"5+ Frigate-Abrufe in Folge fehlgeschlagen: {ff[1][:100]}")
                    if self.cfg.get("mqtt_publish", True):
                        # pub is None = Publisher gar nicht erst hochgekommen. Die alte Bedingung
                        # verlangte 'self.pub and ...' und konnte genau diesen Fall NIE melden:
                        # MQTT war tot und niemand erfuhr es.
                        if not self.pub:
                            melde("mqtt", "MQTT-Publisher ist nicht gestartet (mqtt_publish=an) — "
                                          "Broker-Adresse/Zugangsdaten pruefen.")
                        elif not self.pub.is_connected():
                            melde("mqtt", "MQTT-Publisher laenger getrennt — Broker/Netz pruefen.")
                    if self.cfg.get("trigger") == "mqtt":
                        # Der Trigger-Client ist im mqtt-Modus die EINZIGE Event-Quelle. Seit er
                        # den Erstverbindungsversuch wiederholt statt den Prozess zu reissen
                        # (26.07.), waere ein nie erreichter Broker sonst ein STILLER Totalausfall:
                        # Web-UI und /health blieben gruen, es kaeme nur nie wieder ein Event.
                        if not self.mqtt_trigger:
                            melde("mqtt_trigger", "MQTT-Trigger-Client ist nicht gestartet "
                                                  "(trigger=mqtt) — es kommen KEINE Events an.")
                        elif not self.mqtt_trigger.is_connected():
                            melde("mqtt_trigger", "MQTT-Trigger nicht mit dem Broker verbunden — "
                                                  "es kommen KEINE Events an (Netz/Firewall/Broker "
                                                  "pruefen).")
                    self._backup_frische_pruefen(melde)
                except Exception:
                    pass
        threading.Thread(target=lauf, daemon=True).start()
        self.wanduhr_messen_starten()  # E1: Selbstmessung EINMAL vom Boot (nie von Seitenbesuchen — Widerleger F2.3)
        self.lernlauf_wiederaufnehmen()  # E2: unterbrochener Lauf ueberlebt Neustarts (Konzept §4)

    def lernlauf_wiederaufnehmen(self):
        """Boot-Resume (E2): ein Lauf in 'ernte' laeuft nach einem Neustart von
        selbst weiter; ein VORBEREITETER Lauf nur, wenn er unter Ernte-Semantik
        angelegt wurde (erntefreigabe — Widerleger .75/L1: ein E1-Shadow-Zustand,
        etwa 'ALL reachable' nur fuer die Schaetzung geklickt, darf nach dem Update
        nicht ungefragt zur echten 40000er-Ernte werden). Defekte/unvollstaendige
        Zustaende werden laut gemeldet, nie geraten."""
        from core import lernlauf as _ll
        try:
            zustand, fehler = _ll.lauf_lesen(self.cfg["data_dir"])
            if zustand is None:
                if fehler:
                    self.log(f"learning run state unreadable — not resuming ({fehler})")
                return
            ph = zustand.get("phase")
            f = zustand.get("fortschritt") or {}
            if ph == "ernte":
                if str(f.get("status", "")).startswith("harvest finished"):
                    self._anker_boot_start(zustand,
                                           "learning run found complete (harvest finished) — "
                                           "starting the anchor stage")
                    return
                self.log("learning run resumes after restart (harvest)")
                self.lernlauf_ernte_starten()
                return
            if ph == "anker":
                st = str(f.get("status", ""))
                if st.startswith("anchors ready") or st.startswith("anchors: none"):
                    self.log("learning run found complete (anchors ready) — "
                             "open the anchor clusters to name them")
                    return
                # unterbrochen oder failed: die Phase ist nur so lange wiederholbar,
                # wie der Lauf KEINE benannten Zeilen traegt (E4a-Schutz; das
                # Neuschreiben behielte sie zwar, aber ein Re-Run waehrend der
                # Benennung bleibt bewusst aus — Widerleger-MUSS 01.08.).
                if _ll.benannte_zaehlen(self.cfg["data_dir"], zustand["lauf_id"]):
                    self.log("naming in progress — anchor stage not re-run")
                    return
                self._anker_boot_start(zustand,
                                       "learning run resumes after restart (anchor stage)")
                return
            if ph != "vorbereitung":
                if "status" not in f:
                    self.log(f"learning run found in phase '{ph}' — waiting for its "
                             "stage to ship (no engine for it in this build)")
                return
            if not zustand.get("erntefreigabe"):
                self.log("learning run from the foundation build found — NOT starting "
                         "a harvest without a fresh run creation")
                _ll.lauf_fortschreiben(self.cfg["data_dir"], fortschritt={
                    "status": "planned under the foundation build — abort this run "
                              "and create it again to actually harvest"})
                return
            if zustand.get("events_liste"):
                self.log("learning run resumes after restart (prepared -> harvest)")
                self.lernlauf_ernte_starten()
                return
            ev = int(zustand.get("events") or 0)
            if ev <= 0:
                # NIE einen Ersatz-Umfang raten (frueher: stiller 100er-Rueckfall)
                self.log("learning run state incomplete (no scope) — not resuming; "
                         "abort the run and create a new one")
                return
            self.log("learning run resumes after restart (preparation from scratch)")
            self.lernlauf_vorbereiten_starten(ev, alle_modus=bool(zustand.get("alle")))
        except Exception as e:
            self.log(f"learning run resume failed ({type(e).__name__}: {e})")

    def _anker_boot_start(self, zustand, meldung):
        """Crash-Loop-Wache um jeden BOOT-Start der Anker-Phase (#20 gr33nh07n:
        ein fertig geernteter 1000er-Lauf blieb in phase=anker; jeder Neustart
        nahm die Phase erneut von vorn auf, riss das Container-Memory-Limit,
        wurde vom OOM-Killer beendet und per Restart-Policy wieder gestartet —
        Endlosschleife ohne Ausweg). Die Phase selbst bleibt bewusst
        wiederhol-idempotent (kein Zwischen-Checkpoint: anker_lauf_schreiben
        ersetzt nur unbenannte Zeilen dieses Laufs) — was fehlte, war das LAUTE
        AUFGEBEN: anker_neuanlaeufe zaehlt die Boot-Starts write-ahead (VOR dem
        Start, damit auch ein Kill mitten im Lauf zaehlt), ein erfolgreicher
        Abschluss setzt auf 0 zurueck (_lernlauf_anker), und ab
        anker_resume_max Fehlversuchen haelt der Lauf mit Klartext-Status an
        ('anchor stage failed: …' — der Wizard zeigt dann den Abort-Knopf)
        statt endlos neu anzufahren. Nur BOOT-Starts zaehlen; die Auto-Kette
        Ernte->Anker im laufenden Dienst ist kein Neustart-Symptom."""
        from core import lernlauf as _ll
        dd = self.cfg["data_dir"]
        limit = int(self.cfg["anker_resume_max"])
        n = int(zustand.get("anker_neuanlaeufe") or 0)
        if n >= limit:
            halt = ("anchor stage failed: automatic resume is off "
                    "(anker_resume_max 0) — abort the run, or raise the value "
                    "in Settings and restart" if limit == 0 else
                    f"anchor stage failed: interrupted {n} time(s) in a row — "
                    "automatic resume stopped so a crash cannot loop (out of "
                    "memory? check the container memory limit and "
                    "anker_deckel_hart). Abort the run, or raise "
                    "anker_resume_max in Settings and restart to retry")
            if str((zustand.get("fortschritt") or {}).get("status", "")) != halt:
                _ll.lauf_fortschreiben(dd, fortschritt={"status": halt})
            self.log(f"learning run NOT resumed: anchor stage already interrupted "
                     f"{n}x (anker_resume_max {limit}) — halted, waiting for user")
            return
        _ll.lauf_fortschreiben(dd, anker_neuanlaeufe=n + 1)
        self.log(meldung + f" — attempt {n + 1}/{limit}")
        self.lernlauf_anker_starten()

    # ---------------------------------------------------------- Konfigblatt (Plan AP5)
    CONFIG_WHITELIST = {          # UI-aenderbar (User-Entscheid: ohne PIN, mit Audit+Dialog)
        "win_thresh": (float, 0.30, 0.60, "per-frame threshold in the 3s window (calibrated 0.38)"),
        "win_min": (int, 1, 10, "min. hits in the 3s window (calibrated 2)"),
        "alert_cooldown": (int, 30, 3600, "global push cooldown in seconds"),
        "anwesenheit_cooldown": (int, 300, 86400, "quiet window for the presence push (sec.)"),
        "anwesenheit_push": (bool, None, None, "presence push on/off"),
        "sub_label_schreiben": (bool, None, None, "write recognized names back to Frigate"),
        # Ohne diesen Eintrag lehnte config_schreiben() jede Aenderung mit 400 ab -> der
        # Write-back-Schalter auf der System-Seite war wirkungslos (nur ueber den Wizard setzbar).
        "frigate_read_only": (bool, None, None, "read-only mode: never write anything back to Frigate"),
        "mqtt_publish": (bool, None, None, "publish verifyd/erkennung + heartbeat"),
        "clip_retention_d": (int, 1, 60, "clip cache retention in days"),
        "clip_cache_max_gb": (int, 1, 500, "clip cache size cap in GB, oldest evicted first (age eviction stays)"),
        "cpu_threads": (int, 0, 64, "CPU thread cap for inference sessions + transcode (0 = auto: allowed cores)"),
        "anker_sim1": (float, 0.05, 0.95, "anchor clustering stage 1 (within a pass; measured 0.25)"),
        "anker_sim2": (float, 0.05, 0.95, "anchor clustering stage 2 (pass centroids; measured 0.35)"),
        "anker_marge_warn": (float, 0.01, 0.9, "anchor margin below which a cluster goes to review (measured 0.15)"),
        "anker_hart": (float, 0.05, 0.95, "hard ambiguity: closest foreign centroid at/above this at >=2 identities (measured 0.35)"),
        "anker_k_min": (int, 2, 50, "minimum faces per anchor cluster (margin uncalibratable below 5)"),
        "anker_deckel": (int, 10, 2000, "stage-2 clustering cap per round (measured 250 for this hw class)"),
        "anker_deckel_hart": (int, 10, 4000, "hard stage-2 bound; runs never start above it (memory guard)"),
        "anker_resume_max": (int, 0, 10, "automatic restarts of an interrupted anchor stage after a service restart before it halts and waits for you (crash-loop guard; 0 = never auto-resume)"),
        "benennung_k_je_bin": (int, 1, 50, "naming: recommended images kept per perspective bin (starting value, calibrate in the first naming run)"),
        "benennung_yaw_grenze": (float, 5, 40, "naming: yaw beyond this counts as looking left/right (sub-bin INSIDE the harvest gate window; starting value)"),
        "benennung_dup_sim": (float, 0.5, 0.99, "naming: embedding similarity at/above this = near-identical, one kept (same notion as pool sim_neu)"),
        "benennung_vorschlag_schwelle": (float, 0.2, 0.95, "naming: 'looks like X' suggestion threshold vs named-anchor centroids (conservative start; suggestion only, never forces)"),
        "fps_sample": (float, 1, 30, "analysis sampling rate (calibrated 3)"),
        "szene_karenz_s": (int, 30, 900, "scene grace: unknown alert only if nobody was confirmed in the window"),
        "telegram_modus": (list, ["aus", "ha", "direkt", "beide"], None, "Telegram sending: aus (off) / ha (HA script) / direkt (direct) / beide (both)"),
        "telegram_inhalt": (list, ["video", "bild"], None, "Telegram attachment: video (short clip, image if unavailable) / bild (image only, no transcoding)"),
        "telegram_hoehe": (list, [720, 480], None, "Telegram video height: 720 (default) / 480 (smaller files, faster on weak hardware) — applies to face AND person alerts"),
        "telegram_cooldown": (int, 30, 3600, "throttle for the unknown Telegram (sec.)"),
        "frigate_sync": (bool, None, None, "mirror references to Frigate automatically (parallel operation)"),
        "unscharf_max": (int, 100, 2000, "sharpness threshold for the blur list (higher = more images flagged)"),
        "min_kante": (int, 30, 300, "minimum face size (px) for a usable reference"),
        "szenario_gap_min": (int, 1, 30, "time gap (min) for pass grouping on the Today page"),
        "besucher_sim": (float, 0.40, 0.70, "threshold: at this similarity an unknown event counts as an ignored visitor (no alert)"),
        "modell": (list, ["buffalo", "adaface"], None, "recognition model: buffalo (insightface w600k_r50) | adaface (IR101, better separation) — the refcache is rebuilt automatically after a switch"),
        "update_check": (bool, None, None, "daily anonymous check for a newer release on GitHub — shows a quiet hint in the header; the only outbound call besides notification channels"),
        "debug": (bool, None, None, "verbose debug logging: per-person scores/windows, MQTT payloads, timing (INFO stays the default; turn on to validate the system in depth)"),
        "nachhol_versuche": (int, 0, 5, "retry attempts for events whose analysis failed (0 = off); retries are silent, they never alert"),
        "nachhol_tage": (int, 1, 3, "how far back the retry looks for failed analyses (days)"),
        "worker": (bool, None, None, "persistent analysis worker: keeps the models loaded between events (large CPU saving); off = one process per event (pre-0.1.0.38 behavior)"),
        "worker_rss_max_mb": (int, 512, 16384, "memory threshold (MB): the worker is restarted cleanly once its RSS exceeds this"),
        "wanduhr_min_kerne": (int, 1, 64, "self-measurement gate: minimum PHYSICAL cores (capped by a cgroup CPU quota if one is set) required to run the boot-time timing self-measurement, which is a second full analysis process next to the live one. The default 4 is a structural floor (2 processes x 2 concurrent parts each: video decode + inference), not a measured value. On a machine below the floor the measurement is skipped loudly and run-duration forecasts keep the labeled fallback values. Lower this deliberately if you accept minutes of full load on a small machine in exchange for measured forecasts. Also used as the weak-machine floor for the first-boot chain defaults (fresh installs below it start with person_pfad=nur_wenn_gesicht_leer, vision_pfad=aus) — raising it widens that group too"),
        "analyse_timeout_s": (int, 60, 3600, "watchdog for one live analysis (seconds): if the analysis has not answered by then it is presumed hung, killed, and the event is retried once immediately with a doubled deadline (in worker mode on a fresh worker, otherwise in a fresh process). The default 600 is measured, not guessed: across 1394 live analyses on the reference machine the slowest successful run took 258 s, so 600 leaves over twice that, and the doubled retry additionally carries machines up to roughly 4-5x slower before an event is handed to the silent catch-up. Raise this if you keep seeing 'analyze watchdog' lines for runs that would have finished"),
        # Vision detect (konzept_vision.md v2 §5): die zwei reinen Zahlen des
        # Adapters. Endpunkt/Key/Prompt liegen im `vision`-Block und werden NUR
        # auf dem Vision-Reiter bearbeitet — ein Key in dieser Tabelle stuende
        # als value="..." im HTML (Key-Austritt, §10 Stufe 1).
        "vision_max_tokens": (int, 256, 32000, "vision detect: token budget for one answer — the default is 12000, which is the value that was measured to be enough. 3000 was measured to be too small: the answer was cut off in the middle and counted as no verdict, so a whole run was wasted. Lower it only if your endpoint charges per token and you have seen your model answer well below that"),
        "vision_timeout_s": (int, 10, 3600, "vision detect: seconds to wait for one request — a local model on a CPU machine needs minutes, an external endpoint seconds"),
        # V4 (§7): Auslöser, Reissleine, Deckel und Sammel-Regel des Urteilspfads.
        # Obergrenze 12 statt 10 (User-Entscheid 09.08.): "immer 12 gegen max 12".
        # Die Referenzgalerien sind 12er — das Kandidaten-Gitter darf dieselbe
        # Breite haben, dann steht Gitter gegen Gitter in gleicher Groesse.
        "vision_bilder_je_pass": (int, 1, 12, "vision detect: how many of a walk-through's best pictures go into the ONE candidate grid, as cells — the reference galleries hold 12 pictures, so 12 is the cap here too. This is an UPPER LIMIT, not a demand: a walk-through with fewer usable pictures simply gets a smaller grid, and nothing is invented to fill it. The whole walk is shown as a single grid, so the cost is TWO requests per compared PAIR of galleries — the same two requests whether the grid has three cells or twelve, because every question is asked again with the galleries swapped"),
        "vision_deadline_s": (int, 30, 7200, "vision detect: overall deadline for one request in seconds — the timeout above is a socket timeout, which a slowly trickling answer walks straight past; when this one hits, the connection is closed and the verdict is 'no vision verdict (timeout)'"),
        "vision_anfragen_h": (int, 2, 5000, "vision detect: request limit per hour (every attempt counts, including failed ones); when it is reached vision pauses itself and says so instead of running on quietly"),
        "vision_anfragen_tag": (int, 2, 20000, "vision detect: request limit per day — this is the day cap: one walk-through costs 2 requests per compared pair of galleries, and on a paid endpoint every request is money"),
        "vision_quote": (float, 0.5, 1.0, "vision detect: share of the CAST votes that must agree for a walk-through verdict (1.0 = unanimous); a comparison without a usable answer is an abstention, never a vote against"),
        "vision_min_voten": (int, 1, 10, "vision detect: how many consistent comparisons must back a name before there is a verdict — the winner has to hold its place against that many other galleries. The default is 1: the first comparison that comes out clean carries the verdict. Raise it if you want the winner to defend its place against further galleries; every extra confirmation costs two more requests. It can never demand more comparisons than you have galleries for: with two approved galleries there is exactly one possible pair"),
        # Zwei optionale Meldungen, beide AUS im Auslieferungszustand. Sie aendern
        # NICHTS an den bestehenden Alarmen — Vision bekommt kein Stimmrecht, kein
        # Veto und kann nichts entwarnen (E6).
        "vision_doppellauf": (bool, None, None, "vision detect: ask each pair twice with the galleries swapped (on by default) — the swap is what catches position bias: A in the first run and B in the swapped run mean the same gallery, so a contradiction exposes a model that just prefers the first picture. Measured here: every wrong answer across all test series was an \"A\", never a \"B\". Switching it off halves the requests and gives that check up; a comparison then rests on a single answer"),
        "vision_meldung": (bool, None, None, "vision detect: send a short note through your usual channels when a walk-through has been judged (off by default) — it arrives AFTER the pass, minutes late on a local model, and it is information only: it never raises or cancels an alarm"),
        "vision_alarm_unbestaetigt": (bool, None, None, "vision detect: alert when vision CONTRADICTS the body recognition (off by default) — it fires only when the body path claimed a known person, the run really happened, the model answered, and vision still confirmed nobody (neither, or the two swapped rounds disagreed). It stays quiet on walk-throughs the body path already called unknown (there vision agrees, so there is nothing to report) and when there was simply too little material: recognising known people is the strong side of this path, so a non-confirmation is a real signal — turning strangers away is the weak side, so it never votes in that direction"),
        "vision_stimme": (bool, None, None, "vision detect: count a clean vision verdict as ONE additional support toward the body-path support rule, when it names the SAME person the body path already favors on that walk-through (on by default). It can only ever add that one vote: a contradiction or a tie between body candidates is simply no support (never a veto), vision alone never credits a pass, and alarms are completely untouched — this changes only how a pass is credited on the Today and Appearances pages. With the vision path set to 'aus' no automatic verdicts arise, so there is nothing to count; verdicts from runs you start yourself on the Vision page still vote, and verdicts that already exist keep voting even when vision detection as a whole is switched off later — this switch here is the one that silences them"),
        # Ketten-Schalter (Issue #21): Enum aus KETTE_STUFEN (eine Quelle fuer
        # Default, Whitelist und UI-Dropdown). "aus" ueberspringt den Weg an
        # der QUELLE — die teuren Rechnungen starten gar nicht erst.
        "person_pfad": (list, KETTE_STUFEN, None, "person (body) recognition path: immer = runs on every analyzed event once the person model is armed (today's behavior) | nur_wenn_gesicht_leer = the expensive person judgment (embedding) only starts when the FACE path could NOT confirm everyone on the walk-through — one unconfirmed or unclear person and it runs; body pictures are still collected during the analysis so the judgment has material when it is needed | aus = the path never starts by itself: no body pictures are collected and no person judgment is computed (the biggest saving on weak CPUs); a re-analysis you start yourself keeps working"),
        "vision_pfad": (list, KETTE_STUFEN, None, "vision detect path: immer = a run starts automatically at the end of every walk-through, as long as vision detect itself is switched on (today's behavior) | nur_wenn_gesicht_leer = the automatic run only starts when the FACE path could NOT confirm everyone on the walk-through | aus = no automatic vision runs at all; runs you start yourself on the Vision page keep working"),
        "diagnostic_collection": (bool, None, None, "keep every JUDGED body image for inspection (Person -> Judged images): on = images of all passes stay for 30 days, roughly 20-40 MB a day; off (default) = they only live while the pass is running, then only the winning image and the verdict log remain"),
        "fd_front_min": (float, 0.5, 1.0, "false-detection rule: frontality at/above which a detection looks like a static object (calibrated 0.85)"),
        "fd_sharp_min": (int, 200, 5000, "false-detection rule: sharpness (Laplacian var.) at/above which a crop is edge-rich like vegetation/spokes (calibrated 1500)"),
        "fd_det_max": (float, 0.5, 0.9, "false-detection rule: only detections BELOW this detector score can be discarded (calibrated 0.70)"),
        "det_thresh": (float, 0.3, 0.7, "SCRFD detector threshold (insightface default 0.5); raising it costs real faces — visible here, not a tuning hint"),
        # E2 harvest gates (measured V0.5; gate L's knobs are the fd_* rule above)
        "ernte_m_det_min": (float, 0.4, 0.9, "harvest gate M: min. detector score for a crop-worthy face (calibrated 0.60)"),
        "ernte_m_kante_min": (int, 20, 200, "harvest gate M: min. face edge in px (calibrated 60)"),
        "ernte_m_sharp_min": (int, 10, 500, "harvest gate M: min. sharpness (calibrated 60)"),
        "ernte_s_det_min": (float, 0.5, 0.95, "harvest gate S (anchor-ready): min. detector score (calibrated 0.70)"),
        "ernte_s_winkel_max": (int, 10, 60, "harvest gate S: max. |pitch|/|yaw|/|roll| in degrees (calibrated 30)"),
    }

    def config_schreiben(self, aenderungen):
        """SaveConfig (Phase 2, User 21.07.): Whitelist-Werte validieren und in den JSON-Store
        <data_dir>/config.json schreiben — der EINZIGE Schreibweg fuer Config. Loest den yaml-
        Zeilenersatz ab (kein ${VAR}-Risiko, keine kaputten Kommentare). Die yaml bleibt die Basis,
        der Store ueberlagert sie (s. load_config). Danach sauberer Exit nach laufender Analyse;
        systemd startet neu (Live-Reload folgt in Phase 4)."""
        angewendet = {}
        for key, wert in aenderungen.items():
            if key not in self.CONFIG_WHITELIST:
                return False, f"'{key}' ist nicht aenderbar"
            typ, lo, hi, _ = self.CONFIG_WHITELIST[key]
            if typ is list:                                    # Enum-String (z.B. telegram_modus)
                w = str(wert).strip()
                if w not in lo:
                    return False, f"'{key}': erlaubt {', '.join(lo)}"
            else:
                try:
                    w = (str(wert).lower() in ("1", "true", "ja", "on")) if typ is bool else typ(wert)
                except Exception:
                    return False, f"'{key}': ungueltiger Wert"
                if typ is not bool and not (lo <= w <= hi):
                    return False, f"'{key}': erlaubt {lo}–{hi}"
            angewendet[key] = w
        if not angewendet:
            return False, "keine Aenderung"
        store = _lade_config_store(self.cfg)
        store.update(angewendet)
        p = _config_store_pfad(self.cfg)
        _store_schreiben(p, store)      # atomar + fsync, unter _cfg_lock (5 Schreibwege)
        with open(os.path.join(self.cfg["data_dir"], "config", "config_audit.jsonl"), "a") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "aenderungen": angewendet},
                               ensure_ascii=False) + "\n")
            f.flush()
        self.log(f"CONFIG changed via UI (JSON store): {angewendet} — restart after the current analysis")

        self.neustart("Konfig")
        return True, f"gespeichert: {angewendet} — Dienst startet gleich neu"

    # Modulumbau R2: Erst-Boot-Auto-Default + Settings-Hinweis leben in
    # core/kette.py (Injektion pur: die EINEN Store-IO-/Mess-Funktionen dieses
    # Dienstes kommen als Parameter mit — keine Duplikate, kein Rueckimport).
    def _kette_auto_default(self):
        _kette.auto_default(self.cfg, self.log_path, self.log,
                            store_pfad=_config_store_pfad,
                            store_laden=_lade_config_store,
                            store_schreiben=_store_schreiben,
                            phys_kerne=_phys_kerne,
                            min_kerne_default=WANDUHR_MIN_KERNE)

    def _kette_auto_hinweise(self):
        return _kette.auto_hinweise(self.cfg)


    # Modulumbau R3: Notifications-Settings (Store-Schreiber + Kanal-Tests) leben
    # in core/melden.py (Docstrings dort). Injektion pur: Whitelist, Store-IO,
    # Maskierung und Neustart reicht der Dienst als Parameter herein.
    def notif_speichern(self, d):
        return _melden.notif_speichern(self.cfg, d, log=self.log,
                                       whitelist=self.CONFIG_WHITELIST,
                                       store_pfad=_config_store_pfad,
                                       store_laden=_lade_config_store,
                                       store_schreiben=_store_schreiben,
                                       maskieren=_mask_secret,
                                       neustart=self.neustart)

    def notif_test(self, kanal, d):
        return _melden.notif_test(self.cfg, kanal, d)

    # ------------------------------------------------- Live-Reiter (Phase 2)
    # Duenne Maentel: Zustands-Ableitung, Validierung und Store-Schreibwege
    # liegen in core/livewache (ui_zustand/live_speichern/live_schalter,
    # Injektion der EINEN Store-IO-Wege wie bei notif_speichern). Die Engine
    # ist ein eigener Prozess; Auftraege (Quelltest/Last-Messung) laufen als
    # Kommando-Datei + Status-Quittung — der STORE-Schreib der Ergebnisse
    # bleibt bei DIESEM Dienst (live_quittungen_uebernehmen, _cfg_lock).

    def _live_gesperrt(self):
        """CPU-only-Sperre der Kacheln — DASSELBE Praedikat wie der Engine-
        Startweg (livewached._cpu_sperre: resolve_backend kind == 'cpu').
        -> (gesperrt, grund).

        UI-M5 (Fix-Zyklus 12.08.): der Grund kommt aus der ECHTEN Ursache —
        'CPU-only image' stimmt nur auf der cpu-Variante; ein gpu-/cuda-Image
        ohne durchgereichte GPU loest AUTO ebenfalls auf cpu auf, und der
        User braucht dann den Durchreichungs-Hinweis, keine Fehldiagnose.
        FAIL-CLOSED wie die Engine (_cpu_sperre hat kein try): wirft die
        Pruefung, gilt Live als gesperrt — nie stillschweigend freigeben."""
        try:
            from face_audit import resolve_backend
            kind, _dev = resolve_backend()
            if kind != "cpu":
                return False, ""
            variante = os.environ.get("SUSLIK_VARIANT", "")
            if variante == "cpu":
                grund = ("Live watchers are not available on this build "
                         "(CPU-only image)")
            elif variante:
                grund = (f"Live watchers need GPU recognition, but this "
                         f"'{variante}' image is running on the CPU here — "
                         f"no usable GPU was found or bound (check device "
                         f"passthrough and host drivers)")
            else:
                grund = ("Live watchers need GPU recognition, but the "
                         "detector backend resolved to CPU on this machine")
            return True, grund
        except Exception as e:
            self.log(f"!! live: backend check failed ({type(e).__name__}: "
                     f"{e}) — treating live as unavailable (fail-closed, "
                     f"same direction as the engine lock)")
            return True, ("Live watchers unavailable: the backend check "
                          "failed (see service log)")

    def live_lage(self, cams):
        """Kachel-Daten des Live-Reiters: Kameras aus Frigate (injizierte
        EINE Aufzaehlung) + konfigurierte Guards, Zustand je Kachel aus
        ui_zustand (Engine-QUITTUNG, K1 in beide Richtungen).
        -> (kacheln, engine_info, gesperrt).

        UI-B2 (Frische-Tor): ALLE Anzeige-Inhalte aus dem Status (Zaehler,
        Auftraege, Slot-Neubewertung) laufen durch livewache.status_fuer_ui —
        ein toter Engine-Prozess friert sonst Zaehler/Countdown/re-check-
        Texte als Dauer-Luege ein (UI-MUSS-1, RECHECK 12.08.: genau die
        neubewertung lief noch am Tor vorbei)."""
        from core import livewache as _lw
        status, frisch = _lw.status_lesen(self.cfg)
        if status:
            self.live_quittungen_uebernehmen(status)
        gesperrt, sperr_grund = self._live_gesperrt()
        _auftrag, _auftraege, ks_ui = _lw.status_fuer_ui(status, frisch)
        _d, guards = _lw.guards_lesen(self.cfg, lambda z: None)
        versteckt = set(_lw.versteckt_lesen(self.cfg))
        briefe = _lw.steckbriefe_lesen(self.cfg)
        kacheln = []
        for name in sorted(set(cams or {}) | set(guards)):
            g = guards.get(name)
            ks = ((status or {}).get("kacheln") or {}).get(name)
            verw = ((status or {}).get("verweigert") or {}).get(name, "")
            z, detail = _lw.ui_zustand(g, ks, frisch, gesperrt,
                                       verweigert_grund=verw,
                                       sperr_grund=sperr_grund)
            kacheln.append({
                "name": name, "zustand": z, "detail": detail,
                "in_frigate": name in (cams or {}),
                "cam": (cams or {}).get(name) or {},
                "guard": g, "live": ks_ui.get(name),
                "test": (g or {}).get("test") or None,
                "test_fehler": (g or {}).get("test_fehler") or None,
                "messung": (g or {}).get("messung") or None,
                "versteckt": name in versteckt,
                "steckbrief": briefe.get(name) or None,
            })
        return kacheln, {"frisch": frisch, "status": status,
                         "sperr_grund": sperr_grund,
                         # Phase 4: Supervisor-Lage (Autostart/Standalone) —
                         # dieselbe Quelle wie /health (live_aufsicht_status).
                         "aufsicht": self.live_aufsicht_status()}, gesperrt

    def live_health(self):
        """Der /health-Block des Live-Reiters — aus DERSELBEN Ableitung wie
        die Kacheln (ui_zustand + registry.LIVE_ZUSTAENDE, K3: eine Quelle).
        Nur konfigurierte Guards (kein Frigate-Aufruf im health-Pfad)."""
        from core import livewache as _lw
        status, frisch = _lw.status_lesen(self.cfg)
        gesperrt, sperr_grund = self._live_gesperrt()
        _d, guards = _lw.guards_lesen(self.cfg, lambda z: None)
        aus = {"engine": "ok" if frisch else "not running", "watchers": {}}
        if status and status.get("engine") not in (None, "ok"):
            aus["engine"] = str(status.get("engine"))
        # Phase 4: Supervisor-Lage — Standalone-Erkennung sichtbar in /health
        # ("standalone engine detected"), dieselbe Quelle wie die Live-Seite.
        aus["supervisor"] = self.live_aufsicht_status()
        for name, g in sorted(guards.items()):
            ks = ((status or {}).get("kacheln") or {}).get(name)
            verw = ((status or {}).get("verweigert") or {}).get(name, "")
            z, detail = _lw.ui_zustand(g, ks, frisch, gesperrt,
                                       verweigert_grund=verw,
                                       sperr_grund=sperr_grund)
            aus["watchers"][name] = ({"state": z, "detail": detail}
                                     if detail else {"state": z})
        return aus

    def live_speichern(self, kamera, d):
        # Engine-M5: das _cfg_lock umgreift Lesen+Aendern+Schreiben (Areas-
        # Muster) — der Store-Schreibweg allein trennte nichts, der Verlierer
        # war gemessen IMMER der Lock-Halter (Helfer-Testblock 40/40 weg).
        from core import livewache as _lw
        gesperrt, _grund = self._live_gesperrt()
        if gesperrt:
            # UI-KANN 4 (RECHECK 12.08.): die Kachel sagt 'Bedienelemente
            # aus' — der Save-Weg haelt sich fail-closed daran, analog
            # live_schalter (vorher 200 inkl. stiller Test-Entwertung).
            return False, "not available on this build"
        with _cfg_lock:
            return _lw.live_speichern(self.cfg, kamera, d, log=self.log,
                                      store_pfad=_config_store_pfad,
                                      store_laden=_lade_config_store,
                                      store_schreiben=_store_schreiben)

    def live_schalter(self, kamera, enabled):
        from core import livewache as _lw
        gesperrt, _grund = self._live_gesperrt()
        if gesperrt:
            # UI-KANN 14: die Kachel zeigt 'Bedienelemente aus' — der Server
            # haelt sich jetzt auch daran (vorher 200 am UI-Grau vorbei).
            return False, "not available on this build"
        with _cfg_lock:                    # Engine-M5, s. live_speichern
            ok, msg = _lw.live_schalter(self.cfg, kamera, bool(enabled),
                                        log=self.log,
                                        store_pfad=_config_store_pfad,
                                        store_laden=_lade_config_store,
                                        store_schreiben=_store_schreiben)
        # Phase 4: Enable startet die Engine, wenn sie nicht laeuft (Bauplan-
        # Auftrag) — der Anstoss weckt den Supervisor-Takt sofort und hebt
        # Pause/Backoff auf. Disable stoppt BEWUSST NICHT (naechstes Enable
        # ist dann in Sekunden wirksam statt einen Kaltstart zu kosten).
        if ok and enabled and self._live_aufsicht is not None:
            self._live_aufsicht.anstossen()
        return ok, msg

    def live_verstecken(self, kamera, versteckt):
        """Duenner Mantel (Muster live_schalter) — reine Anzeige-Praeferenz,
        deshalb KEINE Build-Sperre: auch auf cpu-only darf man die Kachel-
        Liste aufraeumen (die Kacheln existieren dort ja, nur gesperrt)."""
        from core import livewache as _lw
        with _cfg_lock:                    # Engine-M5, s. live_speichern
            return _lw.live_verstecken(self.cfg, kamera, bool(versteckt),
                                       log=self.log,
                                       store_pfad=_config_store_pfad,
                                       store_laden=_lade_config_store,
                                       store_schreiben=_store_schreiben)

    def start_stream_steckbriefe(self):
        """Stream-Steckbriefe je Frigate-Kamera EINMAL je Dienststart im
        Hintergrund proben (User 13.08.: der Kachel-Kopf soll die ECHTE
        Stream-Aufloesung zeigen, ohne Quelltest-Klick — Frigates Config
        kennt nur die kleine detect-Groesse). ffprobe am go2rtc-Restream
        (dieselbe proxy_url-Formel wie der Waechter), Ergebnis je Kamera
        SOFORT in den Cache geflusht (Absturz-Regel). Auf gesperrten Builds
        (CPU-only) laeuft der Lauf trotzdem — die Seite zeigt die Kacheln
        auch dort, und ffprobe ist ein Cent-Posten. Vorstufe des geplanten
        vollen Stream-Analyse-Features (stand.md-Vormerkung)."""
        from core import livewache as _lw

        def lauf():
            try:
                cams, err = frigate_cameras(self.cfg)
                if err or not cams:
                    return
                for name in sorted(cams):
                    url = _lw.proxy_url(self.cfg, name)
                    if not url:
                        return
                    try:
                        s = _lw.steckbrief_ermitteln(url, versuche=1,
                                                     log=lambda z: None)
                        _lw.steckbrief_schreiben(
                            self.cfg, name, dict(s, ts=round(time.time(), 1)))
                        self.log(f"stream profile {name}: "
                                 f"{s.get('breite')}x{s.get('hoehe')}"
                                 + (f" @ {s.get('fps')} fps" if s.get("fps")
                                    else "")
                                 + (f", {s.get('codec')}" if s.get("codec")
                                    else ""))
                    except Exception as e:
                        # LAUT je Kamera, aber der Lauf stirbt nie still an
                        # EINER unerreichbaren Quelle.
                        self.log(f"stream profile {name}: "
                                 f"{type(e).__name__} — skipped")
                    time.sleep(1.0)
            except Exception as e:
                self.log(f"!! stream profile run failed: "
                         f"{type(e).__name__}: {e}")
        threading.Thread(target=lauf, name="steckbriefe",
                         daemon=True).start()

    def live_quittungen_uebernehmen(self, status):
        """Engine-Ergebnisse (Quelltest-Block, Last-Messung) in den Store —
        der SCHREIBWEG bleibt beim Dienst (_cfg_lock), die Engine quittiert
        nur im Status-JSON. Idempotent ueber den ts-Vergleich (jeder Poll
        prueft, geschrieben wird nur Neues).

        AUCH FEHL-AUFTRAEGE (UI-M3, gemessen: 'unreachable'/'0/20' erreichten
        die Seite nie — der fehler-Zweig des Renderers war toter Code):
         * Mess-FEHLER ersetzen den messung-Block (er ist reine Anzeige, kein
           Riegel — die letzte Wahrheit zaehlt, auch wenn sie 'kaputt' heisst).
         * Test-FEHLER gehen in ein EIGENES Feld test_fehler: der gruene
           test-Block traegt den Enable-/Weiterlauf-Riegel (test_gueltig),
           ein transient roter Re-Test darf einen laufenden Waechter nicht
           stoppen. Ein neuer gruener Test raeumt das Feld."""
        auftraege = (status or {}).get("auftraege") or {}
        if not auftraege:
            return
        with _cfg_lock:
            store = _lade_config_store(self.cfg)
            geaendert = []
            for kamera, erg in auftraege.items():
                t = erg.get("test") or {}
                block = t.get("block")
                if t.get("ok") and block:
                    g = (store.setdefault("live", {})
                         .setdefault("guards", {}).setdefault(kamera, {}))
                    if (g.get("test") or {}).get("ts") != block.get("ts"):
                        g["test"] = block
                        g.pop("test_fehler", None)
                        geaendert.append(f"{kamera}:test")
                elif t and not t.get("ok") and not t.get("vorab"):
                    g = (store.setdefault("live", {})
                         .setdefault("guards", {}).setdefault(kamera, {}))
                    if (g.get("test_fehler") or {}).get("ts") != t.get("ts"):
                        g["test_fehler"] = {
                            "ok": False, "ts": t.get("ts"),
                            "fehler": str(t.get("fehler") or t.get("text")
                                          or "source test failed")[:300]}
                        geaendert.append(f"{kamera}:test_fehler")
                m = erg.get("messung") or {}
                if m and m.get("ts") is not None and not m.get("vorab"):
                    g = (store.setdefault("live", {})
                         .setdefault("guards", {}).setdefault(kamera, {}))
                    if (g.get("messung") or {}).get("ts") != m.get("ts"):
                        g["messung"] = m
                        geaendert.append(f"{kamera}:messung"
                                         + ("" if m.get("ok") else "(fehler)"))
            if geaendert:
                _store_schreiben(_config_store_pfad(self.cfg), store)
                self.cfg["live"] = store["live"]
                self.log(f"LIVE: engine job results stored "
                         f"({', '.join(geaendert)})")

    def _live_jobs_altern(self):
        """Engine-M6 (unter _live_jobs_lock aufrufen): haengende Helfer-Jobs
        nach Frist in ein ehrliches Fehler-Ergebnis kippen — ein toter
        Helfer-Thread sperrte den Quelltest sonst bis zum Dienst-Neustart
        mit der falschen Meldung 'another test is already running'."""
        jetzt = time.time()
        for k, v in list(self._live_jobs.items()):
            if (not v.get("fertig")
                    and jetzt - v.get("seit", jetzt) > _LIVE_HELFER_FRIST_S):
                self._live_jobs[k] = {
                    "art": v.get("art") or "test", "weg": "prozess",
                    "fertig": True, "ok": False,
                    "text": (f"helper did not report back within "
                             f"{_LIVE_HELFER_FRIST_S:.0f}s (thread died?) — "
                             f"slot freed"),
                    "ts": jetzt}
                self.log(f"!! LIVE helper job {k}: stale after "
                         f"{_LIVE_HELFER_FRIST_S:.0f}s — marked failed, "
                         f"slot freed")

    def live_test_starten(self, kamera):
        """§5-Quelltest, asynchron: laeuft die ENGINE, uebernimmt SIE ihn
        (geteilter Detektor — kein zweites Modell auf der iGPU, Lehre aus
        dem Vier-Waechter-Tod 11.08.); ohne Engine faehrt ein Helfer-
        Subprozess (`livewached test --json`, kurzlebiges eigenes Modell).
        Ergebnis holt der UI-Poll ueber /live_status; den test-Block
        schreibt in beiden Wegen DIESER Dienst. -> (ok, msg).

        Engine-M3: der Kommando-Slot wird nie stumm ueberschrieben — haengt
        ein unverarbeitetes ts (kommando_unverarbeitet gegen die Engine-
        Quittung status.kommando_ts), wird ABGELEHNT statt ueberschrieben;
        Pruefung+Schreib unter _live_cmd_lock (zwei UI-Klicks im selben
        Fenster). Engine-M4: die Weg-Entscheidung Engine/Helfer haengt nicht
        mehr allein an der 6-s-Frische — haelt ein Prozess das Engine-flock
        (engine_lebt), startet NIE ein Helfer-Zweitmodell auf derselben GPU."""
        from core import livewache as _lw
        kamera = str(kamera or "").strip()
        if not kamera:
            return False, "camera name missing"
        gesperrt, _grund = self._live_gesperrt()
        if gesperrt:
            return False, "not available on this build"
        with self._live_cmd_lock:
            status, frisch = _lw.status_lesen(self.cfg)
            if frisch:
                if (status or {}).get("auftrag"):
                    return False, "another test/measurement is already running"
                if _lw.kommando_unverarbeitet(self.cfg, status) is not None:
                    return False, ("a command is already queued for the "
                                   "engine — try again in a few seconds")
                _lw.kommando_schreiben(self.cfg, "test", kamera)
                return True, "source test started (inside the live engine)"
        if _lw.engine_lebt(self.cfg):
            return False, ("the live engine process is running but its "
                           "status is stale (busy?) — not starting a second "
                           "model on the same GPU; try again shortly")
        with self._live_jobs_lock:
            self._live_jobs_altern()
            if any(not j.get("fertig") for j in self._live_jobs.values()):
                return False, "another test is already running"
            self._live_jobs[kamera] = {"art": "test", "weg": "prozess",
                                       "fertig": False, "seit": time.time()}

        def lauf():
            # Engine-M6: erg ist VOR jedem riskanten Schritt belegt und das
            # finally setzt IMMER fertig — der Store-Schreib lag vorher
            # ausserhalb des try, ein Fehler dort (volle Platte, Rechte)
            # liess den Job-Eintrag fuer immer 'laufend'.
            erg = {"ok": False, "text": "helper crashed before reporting"}
            try:
                env = dict(os.environ)
                env["VERIFYD_CONFIG"] = self.config_pfad or os.path.join(
                    HERE, "verifyd.yaml")
                p = subprocess.run(
                    [sys.executable, "-m", "core.livewached", "test",
                     kamera, "--json"],
                    cwd=HERE, capture_output=True, text=True,
                    timeout=180, env=env)
                zeilen = [z for z in (p.stdout or "").splitlines()
                          if z.strip().startswith("{")]
                erg = json.loads(zeilen[-1]) if zeilen else {
                    "ok": False, "text": (p.stderr or "no output")[-200:]}
                with _cfg_lock:
                    store = _lade_config_store(self.cfg)
                    g = (store.setdefault("live", {})
                         .setdefault("guards", {}).setdefault(kamera, {}))
                    if erg.get("ok") and erg.get("block"):
                        g["test"] = erg["block"]
                        g.pop("test_fehler", None)
                        _store_schreiben(_config_store_pfad(self.cfg), store)
                        self.cfg["live"] = store["live"]
                        self.log(f"LIVE source test {kamera}: stored "
                                 f"(helper process)")
                    elif not erg.get("ok"):
                        # UI-M3: auch der Helfer-Fehlschlag wird sichtbar
                        # gespeichert (test_fehler), nicht nur gepollt.
                        g["test_fehler"] = {
                            "ok": False, "ts": round(time.time(), 1),
                            "fehler": str(erg.get("text") or "")[:300]}
                        _store_schreiben(_config_store_pfad(self.cfg), store)
                        self.cfg["live"] = store["live"]
            except Exception as e:
                erg = {"ok": False,
                       "text": f"{type(e).__name__}: {str(e)[:120]}"}
            finally:
                with self._live_jobs_lock:
                    self._live_jobs[kamera] = {
                        "art": "test", "weg": "prozess", "fertig": True,
                        "ok": bool(erg.get("ok")),
                        "text": str(erg.get("text") or ""), "ts": time.time()}
        threading.Thread(target=lauf, name=f"live-test-{kamera}",
                         daemon=True).start()
        return True, ("source test started — the engine is not running, so a "
                      "helper process runs it (up to ~2 minutes)")

    def live_messung_starten(self, kamera):
        """Last-Messung EINES Waechters (User-Auflage 12.08.) — laeuft NUR
        in der Engine (sie pausiert die anderen Kacheln, das Modell bleibt
        geladen). -> (ok, msg); Fortschritt/Countdown via /live_status.
        Kommando-Slot-Riegel wie live_test_starten (Engine-M3)."""
        from core import livewache as _lw
        kamera = str(kamera or "").strip()
        if not kamera:
            return False, "camera name missing"
        gesperrt, _grund = self._live_gesperrt()
        if gesperrt:
            return False, "not available on this build"
        with self._live_cmd_lock:
            status, frisch = _lw.status_lesen(self.cfg)
            if not frisch:
                return False, ("the live engine is not running — the load "
                               "measurement runs inside the engine; the "
                               "service starts it automatically once a "
                               "watcher is enabled")
            if (status or {}).get("auftrag"):
                return False, "another test/measurement is already running"
            if _lw.kommando_unverarbeitet(self.cfg, status) is not None:
                return False, ("a command is already queued for the engine — "
                               "try again in a few seconds")
            _lw.kommando_schreiben(self.cfg, "messung", kamera)
        return True, ("measurement started — other watchers are paused while "
                      "it runs")

    def live_status_daten(self):
        """JSON fuer den UI-Poll: Engine-Frische, laufender Auftrag (Phase +
        Restsekunden fuer den Countdown), Ergebnisse, Helfer-Jobs und die
        Kachel-Zustaende (Reload-Erkennung). Uebernimmt nebenbei frische
        Engine-Ergebnisse in den Store (Schreibweg beim Dienst).

        UI-B2: auftrag/auftraege laufen durch livewache.status_fuer_ui —
        ohne frischen Herzschlag friert sonst ein toter Auftrag Countdown
        und Reload-Tor der Seite als Dauer-Luege ein."""
        from core import livewache as _lw
        status, frisch = _lw.status_lesen(self.cfg)
        if status:
            self.live_quittungen_uebernehmen(status)
        gesperrt, sperr_grund = self._live_gesperrt()
        auftrag, auftraege, _ks_ui = _lw.status_fuer_ui(status, frisch)
        _d, guards = _lw.guards_lesen(self.cfg, lambda z: None)
        zustaende = {}
        for name, g in guards.items():
            ks = ((status or {}).get("kacheln") or {}).get(name)
            verw = ((status or {}).get("verweigert") or {}).get(name, "")
            # UI-KANN 3 (RECHECK 12.08.): derselbe ehrliche Sperr-Text wie
            # auf der Seite — vorher stand hier die CPU-only-Fehldiagnose.
            z, detail = _lw.ui_zustand(g, ks, frisch, gesperrt,
                                       verweigert_grund=verw,
                                       sperr_grund=sperr_grund)
            zustaende[name] = {"z": z, "detail": detail}
        with self._live_jobs_lock:
            self._live_jobs_altern()               # Engine-M6
            jobs = {k: dict(v) for k, v in self._live_jobs.items()}
            # abgeholte fertige Helfer-Jobs nach 60 s auskehren
            for k in [k for k, v in self._live_jobs.items()
                      if v.get("fertig")
                      and time.time() - v.get("ts", 0) > 60]:
                del self._live_jobs[k]
        return {"engine": {"frisch": frisch,
                           "zustand": (status or {}).get("engine")},
                "auftrag": auftrag,
                "auftraege": auftraege,
                "jobs": jobs, "zustaende": zustaende}

    # ---------------------------------------- Live-Engine-Supervisor (Phase 4)
    # User-Entscheid 12.08. abends: der Dienst startet und ueberwacht die
    # Engine als eigenen Prozess IM selben Container. Logik in
    # core/liveaufsicht (injektionsrein, Harnisch tools/harnisch_phase34.py);
    # hier nur die echten Aussenkontakte + der Takt-Thread.

    def start_live_aufsicht(self):
        """Supervisor-Thread starten (einmalig, im Serve-Pfad von main())."""
        if self._live_aufsicht is not None:
            return
        from core import liveaufsicht as _la
        from core import livewache as _lw

        def spawn():
            env = dict(os.environ)
            cp = self.config_pfad or os.path.join(HERE, "verifyd.yaml")
            env["VERIFYD_CONFIG"] = (cp if os.path.isabs(cp)
                                     else os.path.join(HERE, cp))
            # start_new_session: die Engine forkt (ffmpeg-Leser), und die
            # Kinder ERBEN das flock — Stopp/Aufraeumen laeuft deshalb immer
            # ueber die Prozessgruppe (killpg), nie nur die Eltern-PID.
            return subprocess.Popen(
                [sys.executable, "-m", "core.livewached", "run"],
                cwd=HERE, env=env, start_new_session=True)

        def guards_aktiv():
            # STORE-Blick (Hand-Edits zaehlen) mit der EINEN enabled-Wahrheit
            # der Engine — _live_guards_aktiv (MUSS-1: "enabled": "false"
            # darf nie spawnen; Fall/Mutant in tools/harnisch_phase34.py).
            try:
                return _live_guards_aktiv(self.cfg)
            except Exception:
                return False

        def gesperrt():
            g, _grund = self._live_gesperrt()
            return g

        def frisch():
            _st, f = _lw.status_lesen(self.cfg)
            return f

        def stoerung(text):
            from core import melden
            for fz in melden.stoerung_melden(self.cfg, text) or []:
                self.log(f"!! live supervisor notice channel failed: {fz}")

        a = _la.Aufsicht(self.log, spawn_fn=spawn, guards_aktiv_fn=guards_aktiv,
                         gesperrt_fn=gesperrt,
                         lock_gehalten_fn=lambda: _lw.engine_lebt(self.cfg),
                         status_frisch_fn=frisch, stoerung_fn=stoerung)
        self._live_aufsicht = a

        def lauf():
            while not self._live_aufsicht_stop.is_set():
                a.weck.wait(_la.TAKT_S)
                a.weck.clear()
                if self._live_aufsicht_stop.is_set():
                    break
                try:
                    a.takt()
                except Exception as e:
                    self.log(f"!! live supervisor tick failed: "
                             f"{type(e).__name__}: {e}")
        threading.Thread(target=lauf, name="live-aufsicht", daemon=True).start()
        # sys.exit (SIGTERM-Handler) laeuft durch atexit — execv NICHT, dort
        # ruft neustart() den Stopp explizit (Muster worker_stoppen).
        import atexit
        atexit.register(self.live_aufsicht_stoppen)
        self.log("live supervisor started (engine autostarts once a watcher "
                 "is enabled)")

    def live_aufsicht_stoppen(self):
        """Engine sauber beenden (SIGTERM-Prozessgruppe + Frist) — vor execv
        (neustart) und am Dienst-Ende (atexit). Idempotent."""
        a = self._live_aufsicht
        if a is None:
            return
        self._live_aufsicht_stop.set()
        try:
            a.stop("service stop")
        except Exception as e:
            self.log(f"!! live supervisor stop failed: {type(e).__name__}: {e}")

    def live_aufsicht_status(self):
        """Anzeige-Block des Supervisors (Live-Seite + /health) — EINE Quelle.
        getattr statt Attribut-Zugriff: T16-artige Pruef-Objekte bauen den
        Service ohne __init__ (Service.__new__), die Lage-Ableitung muss
        darauf antworten koennen statt zu werfen."""
        a = getattr(self, "_live_aufsicht", None)
        if a is None:
            return {"laeuft": False, "standalone": False,
                    "text": "supervisor not running (service still starting, "
                            "or --once mode)"}
        try:
            return a.status()
        except Exception as e:
            return {"laeuft": False, "standalone": False,
                    "text": f"supervisor status failed: {type(e).__name__}"}

    # ------------------------------------------------- Vision detect (V1, §5)
    # Duenne Maentel: Validierung, Test und Vorbedingungen liegen vollstaendig in
    # core/vision.py (dort ohne laufenden Dienst pruefbar). Hier bleibt Store,
    # Audit und der E4-Riegel. Der Vision-Pfad beruehrt den Urteilspfad NICHT.
    def _vision_form(self, d, cloud_gate=True):
        """Formularwerte ueber den gespeicherten Block legen (leeres Secret =
        behalten, Muster notif_speichern) und pruefen -> (ok, block|msg)."""
        from core import vision as _vis
        return _vis.werte_pruefen(d or {}, self.cfg.get("vision") or {},
                                  cloud_gate)

    def vision_speichern(self, d):
        """Vision-Block in den JSON-Store. Secrets im Audit maskiert; die
        Cloud-Bestaetigung wird MIT Zeitstempel protokolliert (§9: ein Hinweis
        neben einem Schalter dokumentiert keine Entscheidung). Kein Neustart:
        den Block liest nur dieser Reiter, und die Live-Config wird hier
        mitgezogen — die zwei Zahlen daneben laufen ueber /konfig und starten
        wie gewohnt neu."""
        from core import vision as _vis
        ok, neu = self._vision_form(d)
        if not ok:
            return False, neu
        # Ein NEU gewaehltes Modell muss aus der Entdeckung GENAU DIESER
        # Verbindung stammen (§5: nie Modelle vorab, auch nicht ueber den
        # Umweg des Speicherns). Ein schon gespeichertes Modell bleibt immer
        # speicherbar — sonst sperrte ein Update ohne frische Entdeckung den
        # Nutzer aus seiner eigenen Config aus.
        _alt_m = str((self.cfg.get("vision") or {}).get("modell") or "")
        if neu.get("modell") and neu["modell"] != _alt_m:
            _p = self._vision_datei("vision_modelle.json")
            if not (_vis.modelle_gueltig(_p, neu)
                    and any(m.get("id") == neu["modell"]
                            for m in _p.get("modelle") or [])):
                return False, ("pick the model from the list this endpoint "
                               "reported — check the connection first")
        neu["aktiv"] = bool((self.cfg.get("vision") or {}).get("aktiv"))  # nur ueber das Gate
        store = _lade_config_store(self.cfg)
        store["vision"] = neu
        _store_schreiben(_config_store_pfad(self.cfg), store)
        self.cfg["vision"] = neu
        audit = {k: neu.get(k) for k in ("preset", "betriebsart", "modell",
                                         "think_aus", "cloud_ok", "cloud_ok_ts")}
        audit["api_key"] = _mask_secret(neu.get("api_key"))
        audit["endpunkt"] = _reg.endpunkt_anzeige(neu.get("endpunkt"))
        audit["prompt_angepasst"] = bool(neu.get("prompt"))
        with open(os.path.join(self.cfg["data_dir"], "config", "config_audit.jsonl"), "a") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "vision": audit},
                               ensure_ascii=False) + "\n")
            f.flush()
        self.log("VISION config changed via UI (key + endpoint masked)")
        return True, "saved"

    def vision_test(self, d):
        """Der dreistufige Test-Knopf mit den AKTUELLEN Formularwerten (leeres
        Key-Feld -> gespeicherter Wert), Ergebnis nach state/vision_test.json.
        Nutzt ausschliesslich zur Laufzeit erzeugte Bilder — nie Bewohner-Bilder,
        auch nicht auf Wunsch (§5).

        Seit V4 kann EINE Stufe angefordert werden (`stufe`: 1|2|3). Der Browser
        ruft sie nacheinander und fuellt das Testlog live — lokal dauert eine
        Stufe Minuten, und ein Knopf, der solange schweigt, sieht aus wie ein
        Haenger. Zusaetzlicher Server-Zustand entsteht dabei keiner: das
        Protokoll ist dieselbe Datei wie vorher, sie waechst nur stufenweise."""
        from core import vision as _vis
        ok, block = self._vision_form(d)
        if not ok:
            return False, block
        block["max_tokens"] = self.cfg.get("vision_max_tokens")
        block["timeout_s"] = self.cfg.get("vision_timeout_s")
        p = os.path.join(self.cfg["data_dir"], "state", "vision_test.json")
        nr = int(d.get("stufe") or 0)
        if nr:
            prot = self._vision_datei("vision_test.json") if nr > 1 else {}
            if not prot.get("stufen") or nr == 1:
                prot = _vis.test_protokoll(block)
            prot, weiter = _vis.test_stufe(block, nr, prot)
        else:
            prot, weiter = _vis.test_lauf(block), True
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _store_schreiben(p, prot)          # atomar + fsync, gleicher Griff
        stufe = next((s for s in prot["stufen"] if s["nr"] == nr), None)
        self.log(f"VISION test{f' step {nr}' if nr else ''}: "
                 f"{(stufe or prot)['ampel']}")
        if nr:
            return True, {"stufe": stufe, "weiter": bool(weiter),
                          "ampel": prot["ampel"]}
        return prot["ampel"] != "rot", f"test finished: {prot['ampel']}"

    def vision_lage(self):
        """(block, testprotokoll, vorbedingungen) fuer die Seite und das Gate.
        Der Block wird beim Lesen auf die Kachel-Welt gezogen (V1 kannte
        `preset`) — sonst verloere ein Update still die Verbindung."""
        from core import vision as _vis
        block = _vis.block_migrieren(self.cfg.get("vision") or {})
        prot = self._vision_datei("vision_test.json")
        return block, prot, _vis.vorbedingungen(self.cfg["data_dir"], block, prot)

    def _vision_datei(self, name):
        try:
            with open(os.path.join(self.cfg["data_dir"], "state", name)) as f:
                return json.load(f)
        except Exception:
            return {}

    def _vision_modelle(self, block):
        """Das gespeicherte Entdeckungs-Ergebnis — aber NUR, wenn es zu genau
        dieser Verbindung gehoert (§5: nie Modelle vorab anzeigen). Nach einem
        Kachel- oder Endpunkt-Wechsel ist es ungueltig und die Seite steht
        wieder auf 'erst verbinden'. Ein fehlgeschlagener Versuch bleibt
        dagegen sichtbar — die ehrliche Fehlermeldung ist der Sinn der Sache."""
        from core import vision as _vis
        prot = self._vision_datei("vision_modelle.json")
        if prot.get("ok") and not _vis.modelle_gueltig(prot, block):
            return {}
        return prot

    def vision_schluessel(self, d):
        """Key-Sofortpruefung per Modell-Listen-Abruf (§5): kostenlos, kein
        Bild. Ergebnis (ohne Geheimnisse) nach state/vision_modelle.json — die
        Modellwahl der Seite liest genau diese Datei.

        Bewusst OHNE Cloud-Gate geprueft (und deshalb auch ohne Speichern des
        Blocks): hier verlaesst kein Bild das Haus, und die Bestaetigung nach
        §9 ist eine Bild-Frage. Gespeichert wird die Verbindung erst ueber
        `vision_speichern`, und dort gilt das Gate."""
        from core import vision as _vis
        ok, block = self._vision_form(d, cloud_gate=False)
        if not ok:
            return False, block
        block["timeout_s"] = min(60, int(self.cfg.get("vision_timeout_s") or 60))
        prot = _vis.schluessel_pruefen(block, block["timeout_s"])
        p = os.path.join(self.cfg["data_dir"], "state", "vision_modelle.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _store_schreiben(p, prot)
        self.log(f"VISION key check: {prot['ampel']} "
                 f"({len(prot.get('modelle') or [])} models)")
        # Die Liste faehrt MIT der Antwort zurueck (Live-Fund 08.08.): die Seite
        # zeigt sie, ohne neu zu laden — sonst gingen die gerade eingetippten
        # Felder verloren und die Liste passte danach nicht mehr zur
        # gespeicherten Verbindung. Geheimnisse sind im Protokoll keine.
        return bool(prot["ok"]), {k: prot[k] for k in
                                  ("text", "modelle", "ts", "endpunkt",
                                   "kachel", "ampel")}

    # --------------------------------------------- Galerie-Wizard (V2, §6)
    # Auch hier nur Maentel: Reihen-Vorschlag, Guete-Sieb, Kopien und
    # Herkunft liegen vollstaendig in core/visiongalerie.py.
    def _galerie_personen(self):
        """Die massgebliche Personen-Menge: personlern/modell/status.json ->
        personen (§3.2). NICHT der Gesichts-Bestand — der hat einen anderen
        Nenner, und beide nebeneinander haben schon einmal verwirrt."""
        try:
            with open(os.path.join(self.cfg["data_dir"], "personlern", "modell",
                                   "status.json")) as f:
                return sorted((json.load(f).get("personen") or {}))
        except Exception:
            return []

    def _galerie_person_ok(self, person):
        """Der Personen-Name aus einer POST-Anfrage wird zu einem PFAD
        (personlern/galerien/<person>/). Deshalb kommt er nicht ungeprueft
        durch: erlaubt ist ausschliesslich ein Name aus dem Koerpermodell —
        eine exakte Whitelist, kein Muster-Filter, den man umschreiben kann.
        Muster-Pruefungen allein haben in diesem Projekt schon zweimal nicht
        gereicht (Anzeige- und Loesch-Weg)."""
        return bool(person) and person in self._galerie_personen()

    def vision_galerie_lage(self, person="", groesse=None, neu=False):
        from core import personernte as _pe
        from core import visiongalerie as _vg
        dd = self.cfg["data_dir"]
        # Schaerfe einmalig nachziehen (§6.4): der Wizard liest nur, gerechnet
        # wird genau hier und genau einmal je Bild.
        _vg.schaerfe_nachziehen(dd, _pe.laeufe_lesen)
        return _vg.wizard_lage(dd, _pe.laeufe_lesen, self._galerie_personen(),
                               person, groesse, neu)

    def vision_galerie_weg(self, person, schluessel, reihe, belegt=(),
                           reihe_belegt=()):
        """Eine Zelle ablehnen und den naechstbesten Kandidaten DERSELBEN
        Ansicht liefern. Die Ablehnung landet in der EIGENEN Ablage der
        Galerie — der Lernlauf-Status wird nie angefasst (§6.5).

        `reihe_belegt` sind die Zellen, die in DIESER Reihe stehen bleiben; sie
        fuellen die Vielfalts-Deckel des Kurators (.161), damit der Nachruecker
        nicht den Tag oder das Ereignis doppelt, das der Nutzer gerade behalten
        hat."""
        from core import personernte as _pe
        from core import visiongalerie as _vg
        if not self._galerie_person_ok(person):
            return False, "unknown person"
        dd = self.cfg["data_dir"]
        _vg.ablehnen(dd, person, schluessel, reihe)
        abgelehnt = _vg.abgelehnt_lesen(dd, person)
        k = _vg.kandidaten(dd, _pe.laeufe_lesen, person)
        nach_s = {_vg.schluessel(e): e for e in k}
        gewaehlt = [nach_s[s] for s in (reihe_belegt or ())
                    if s in nach_s and s != schluessel]
        neu = _vg.nachruecken(k, reihe, abgelehnt, belegt, gewaehlt)
        return True, {"zelle": {kk: neu[kk] for kk in
                                ("lauf_id", "datei", "blick", "hoehe", "tag",
                                 "camera", "geliehen_aus", "note",
                                 "begruendung")} if neu else None,
                      "schluessel": (f'{neu["lauf_id"]}/{neu["datei"]}'
                                     if neu else None),
                      "abgelehnt": len(abgelehnt)}

    def vision_galerie_vergessen(self, person):
        """Das Ablehn-Gedaechtnis dieser Person leeren (Ruecknahme bleibt
        moeglich, wie beim bestehenden Abnahme-Muster)."""
        from core import visiongalerie as _vg
        if not self._galerie_person_ok(person):
            return False, "unknown person"
        for s in list(_vg.abgelehnt_lesen(self.cfg["data_dir"], person)):
            _vg.ablehnung_zuruecknehmen(self.cfg["data_dir"], person, s)
        return True, "rejections forgotten"

    def vision_galerie_abnahme(self, person, groesse, auswahl):
        """Abnahme: Kopien + Herkunfts-Manifest (§6.6). `auswahl` ist die
        Lesereihenfolge der Zellen als Schluessel (lauf_id/datei), None fuer
        eine Luecke."""
        from core import personernte as _pe
        from core import visiongalerie as _vg
        if not self._galerie_person_ok(person):
            return False, "unknown person"
        if int(groesse or 0) not in _vg.GROESSEN:
            return False, "unsupported gallery size"
        dd = self.cfg["data_dir"]
        k = {_vg.schluessel(e): e for e in
             _vg.kandidaten(dd, _pe.laeufe_lesen, person)}
        zellen = []
        for s in auswahl:
            e = k.get(s) if s else None
            if s and not e:
                return False, f"image {s} is no longer available — reload the page"
            zellen.append(e)
        if not [z for z in zellen if z]:
            return False, "nothing to approve"
        m = _vg.abnehmen(dd, person, zellen, int(groesse), bestand=len(k))
        self.log(f"VISION gallery approved: {person} {m['groesse']} cells "
                 f"({m['luecken']} empty, {m['geliehen']} borrowed)")
        return True, (f"approved — {m['groesse']} cells copied into the "
                      "gallery folder")

    def vision_schalter(self, an):
        """E4-Gate: einschalten nur mit ALLEN Vorbedingungen (>=2 abgenommene
        Galerien, gruener Test, Kandidaten-Quelle). Ausschalten geht immer."""
        block, _prot, vor = self.vision_lage()
        if an and not vor["erfuellt"]:
            return False, "still missing: " + "; ".join(vor["fehlt"])
        block["aktiv"] = bool(an)
        store = _lade_config_store(self.cfg)
        store["vision"] = block
        _store_schreiben(_config_store_pfad(self.cfg), store)
        self.cfg["vision"] = block
        self.log(f"VISION detect switched {'on' if an else 'off'}")
        return True, "on" if an else "off"

    # ------------------------------------------- Vision-Urteilspfad (V4, §7)
    # Auch hier nur Maentel: Kandidatenwahl, Kaskade, Sammel-Regel, Deckel,
    # Zaehler und Protokoll liegen vollstaendig in core/visionurteil.py (dort
    # ohne laufenden Dienst pruefbar). Hier bleibt: Debounce, Single-Flight mit
    # Thread, Config-Werte und Log. DER ANALYSE-LOCK WIRD IN DIESEM GANZEN
    # BLOCK NIE GENOMMEN — Vision haelt den Gesichts-Pfad nie auf (§7).
    def _vision_regeln(self, lauf_regeln=None):
        """Die Regeln EINES Laufs. Vorgabe ist die Config; `lauf_regeln`
        ueberschreibt sie NUR fuer diesen einen Lauf (.164, User-Wunsch: "ich
        kann den Testlauf nutzen, um mich an meine optimale Frameanzahl
        ranzutesten" + "die Anzahl der Votes sollten wir einstellbar haben,
        auch fuer den Test").

        Der Weg ist ausdruecklich EINWEG: hier wird nichts gespeichert, und die
        Automatik faehrt weiter mit den Config-Werten. Zulaessig sind nur die
        beiden Felder, die der Test anbietet, und nur in den Grenzen ihrer
        eigenen Whitelist-Eintraege — ein Formularwert wird nie ungeprueft zur
        Regel."""
        r = {"bilder_je_pass": self.cfg.get("vision_bilder_je_pass"),
             "quote": self.cfg.get("vision_quote"),
             "min_voten": self.cfg.get("vision_min_voten"),
             "anfragen_h": self.cfg.get("vision_anfragen_h"),
             "anfragen_tag": self.cfg.get("vision_anfragen_tag"),
             # Der ECHTE Sammel-Schalter (.161): ohne ihn riet die
             # Kein-Material-Meldung "turn on diagnostic collection", auch
             # wenn er laengst an war (Live-Fund 08.08.).
             "doppellauf": bool(self.cfg.get("vision_doppellauf", True)),
             "sammeln": bool(self.cfg.get("diagnostic_collection"))}
        wert = (lauf_regeln or {}).get("doppellauf")
        if wert not in (None, ""):
            # Ein Schalter, kein Zahlenwert: alles ausser den bekannten
            # Falsch-Schreibweisen zaehlt als AN — und "an" ist die sichere
            # Seite (der Tausch bleibt).
            r["doppellauf"] = str(wert).lower() not in ("false", "0", "off",
                                                        "no", "aus")
        for feld, schluessel in (("bilder_je_pass", "vision_bilder_je_pass"),
                                 ("min_voten", "vision_min_voten")):
            wert = (lauf_regeln or {}).get(feld)
            if wert in (None, ""):
                continue
            art, tief, hoch = self.CONFIG_WHITELIST[schluessel][:3]
            try:
                w = art(wert)
            except (TypeError, ValueError):
                continue
            r[feld] = max(tief, min(hoch, w))
        return r

    def _vision_galerien(self):
        """Nur ABGENOMMENE und unversehrte Galerien (§6.6): eine, die eine
        Nachabnahme braucht, urteilt nicht mehr mit — statt still mit halben
        Loechern weiterzulaufen."""
        from core import visiongalerie as _vg
        dd = self.cfg["data_dir"]
        return {n: m for n, m in _vg.alle(dd).items()
                if _vg.pruefen(dd, n).get("status") == "gut"}

    def _vision_anstossen(self, eid, entry=None):
        """Debounce am Durchgangs-ENDE (Muster _nachlern_anstossen): jedes neue
        Event desselben Durchgangs setzt den szene_karenz_s-Timer zurueck, das
        Urteil laeuft GENAU EINMAL, wenn der Durchgang wirklich vorbei ist.
        Frueher zu urteilen hiesse, ueber einen halben Durchgang zu urteilen —
        genau der Fehler, den das Szenario-Prinzip verbietet."""
        if not eid or not (self.cfg.get("vision") or {}).get("aktiv"):
            return
        pk = (self._kontroll_speicher(eid, entry) or {}).get("pass_key")
        if not pk:
            return
        if self.kette_stufe("vision") == "aus":
            # Ketten-Schalter (Issue #21): QUELLE uebersprungen — kein Timer,
            # kein Lauf. EINE laute Zeile je DURCHGANG, nicht je Event
            # (Dedup unten; der 6-h-Verfall haelt die Map endlich).
            jetzt = time.time()
            with self._vision_lock:
                self._kette_stumm = {k: t for k, t in self._kette_stumm.items()
                                     if jetzt - t < 6 * 3600}
                schon = pk in self._kette_stumm
                self._kette_stumm[pk] = jetzt
            if not schon:
                self.log(f"VISION auto-run off (vision_pfad=aus) — pass {pk} "
                         f"will not be judged automatically")
            return
        with self._vision_lock:
            alt = self._vision_timer.get(pk)
            if alt:
                alt.cancel()
            t = threading.Timer(int(self.cfg.get("szene_karenz_s", 90)),
                                self._vision_faellig)
            t.args = (pk, t)                     # Token: nur DIESER Timer feuert
            t.daemon = True
            self._vision_timer[pk] = t
            t.start()

    def _vision_faellig(self, pass_key, mein_timer):
        with self._vision_lock:
            if self._vision_timer.get(pass_key) is not mein_timer:
                return                           # ein neuerer Timer hat uebernommen
            self._vision_timer.pop(pass_key, None)
        # Ketten-Schalter (Issue #21), Stufe "nur_wenn_gesicht_leer": erst am
        # Durchgangs-ENDE steht fest, ob der Gesichts-Weg restlos bestaetigt
        # hat (Regel B) — deshalb faellt die Entscheidung HIER, nicht beim
        # Timer-Start. Nur der automatische Anstoss; manuelle Laeufe gehen
        # direkt ueber vision_urteil_anstossen und bleiben frei.
        # Modulumbau R2: Entscheid in core/kette. "aus" laeuft hier bewusst
        # DURCH (heutiges Verhalten: dieser Punkt prueft nur die
        # nur_wenn_gesicht_leer-Bedingung; die "aus"-Quelle sitzt in
        # _vision_anstossen und laesst gar keinen Timer entstehen).
        if _kette.entscheide(
                self.kette_stufe("vision"),
                lambda: self._gesicht_pass_bestaetigt(pass_key=pass_key)
                ) == "gesicht_bestaetigt":
            self.log(f"VISION run for pass {pass_key} not started — face path "
                     f"confirmed the whole pass (vision_pfad=nur_wenn_gesicht_leer)")
            return
        self.vision_urteil_anstossen(pass_key)

    def vision_waisen(self, pass_key=None):
        """Verwaiste Lauf-Protokolle schliessen (.164, Live-Fund 09.08.).

        Eine Waise ist ein Protokoll, das laut Anzeige noch laeuft, obwohl kein
        Thread mehr dazu gehoert — der Dienst ist mitten im Lauf gestorben.
        Ohne diesen Griff bleibt die Seite ewig auf "a run is going right now"
        stehen und der Start-Knopf gesperrt (der User war real blockiert).

        Der Lebend-Test kommt aus DIESEM Prozess (`_vision_lebt`): ein wirklich
        laufender Lauf wird nie geschlossen. `pass_key=None` raeumt alles (beim
        Dienst-Start, wo es per Definition keinen lebenden Lauf gibt).

        Rueckgabe: Liste der geschlossenen pass_keys."""
        from core import visionurteil as _vu
        with self._vision_lock:
            lebt = set(self._vision_lebt)
        dd = self.cfg["data_dir"]
        if pass_key:
            if str(pass_key) in lebt:
                return []
            return [str(pass_key)] if _vu.waise_schliessen(dd, pass_key) else []
        return _vu.waisen_schliessen(dd, lebt=lambda pk: pk in lebt)

    def vision_waisen_start(self):
        """Beim Dienst-Start EINMAL aufraeumen. Namensfreie Log-Zeile (§9): nur
        die Zahl, keine Person, kein pass_key-Inhalt darueber hinaus."""
        try:
            geschlossen = self.vision_waisen()
        except Exception as e:
            self.log(f"VISION orphan check failed: {e}")
            return 0
        if geschlossen:
            self.log(f"VISION: closed {len(geschlossen)} unfinished run(s) "
                     "from before the restart — they were left without a "
                     "result and would have blocked their walk-through")
        return len(geschlossen)

    def vision_urteil_anstossen(self, pass_key, manuell=False, lauf_regeln=None):
        """Single-Flight mit gedeckelter Warteschlange (§7): 1 laufend +
        1 wartend, alles weitere wird verworfen UND gezaehlt. Der gemessene
        lokale Server laeuft mit --parallel 1; zwei gleichzeitige Laeufe wuerden
        sich dort gegenseitig ausbremsen und den Deckel doppelt verbrauchen.

        .164: VOR dem Single-Flight faellt ein etwaiger Waisen-Stand dieses
        Durchgangs — sonst blockierte ein toter Lauf den Start fuer immer."""
        self.vision_waisen(pass_key)
        with self._vision_lock:
            if self._vision_flug is None:
                from core import visionurteil as _vu
                self._vision_flug = _vu.Einfachlauf()
            lage = self._vision_flug.annehmen(pass_key)
        if lage == "verworfen":
            self.log(f"VISION run for pass {pass_key} discarded "
                     f"(one running, one queued)")
            return False, "a vision run is already going for this pass"
        if lage == "wartet":
            return True, "queued behind the running vision run"
        threading.Thread(target=self._vision_thread,
                         args=(pass_key, manuell, lauf_regeln),
                         daemon=True, name="vision").start()
        return True, "vision run started"

    def _vision_thread(self, pass_key, manuell, lauf_regeln=None):
        # .164: der Thread traegt sich ein und wieder aus. Das ist die
        # Zweitsicherung gegen verwaiste Protokolle: ein Lauf, zu dem KEIN
        # lebender Thread gehoert, darf geschlossen werden, egal was im
        # Protokoll steht.
        with self._vision_lock:
            self._vision_lebt.add(str(pass_key))
        try:
            self._vision_lauf(pass_key, manuell, lauf_regeln)
        except Exception as e:
            self.log(f"VISION run error ({pass_key}): {e}")
        with self._vision_lock:
            self._vision_lebt.discard(str(pass_key))
            naechster = self._vision_flug.fertig()
        if naechster:
            # Der nachrueckende Lauf ist der automatische — er faehrt bewusst
            # mit den Config-Regeln, nicht mit den Feld-Werten eines fremden
            # Testlaufs.
            threading.Thread(target=self._vision_thread,
                             args=(naechster, False, None), daemon=True,
                             name="vision").start()

    def _vision_lauf(self, pass_key, manuell=False, lauf_regeln=None):
        """EIN Vision-Gesamturteil fuer einen Durchgang, ueber den ECHTEN Pfad
        (der Szenario-Test faehrt genau diesen, nie eine Kopie).

        `lauf_regeln` (.164) sind die Felder des manuellen Testlaufs — sie
        gelten NUR fuer diesen Lauf und werden nirgends gespeichert."""
        from core import vision as _vis
        from core import visionurteil as _vu
        blk = _vis.block_migrieren(self.cfg.get("vision") or {})
        blk["max_tokens"] = self.cfg.get("vision_max_tokens")
        blk["timeout_s"] = self.cfg.get("vision_timeout_s")
        tiefe = int(self.cfg.get("vision_deadline_s") or 1200)

        def _fragen(teile):
            try:
                roh, meta = _vis.anfrage(blk, teile, deadline_s=tiefe)
            except _vis.VisionFehler as ex:
                return _vis.urteil_leer(
                    grund="timeout" if ex.code == "deadline" else "fehler",
                    backend=_vis.kachel(blk.get("kachel"))["label"],
                    sichtbar=str(ex)[:200])
            return _vis.antwort_auswerten(
                roh, kachel_name=blk.get("kachel"), dauer_s=meta["dauer_s"],
                quelle=meta["quelle"], custom_prompt=meta["prompt_angepasst"],
                retry_ohne_zusatzfeld=meta["retry_ohne_zusatzfeld"])

        # DIENST-LOG (V4b): Start UND Ende. Vorher stand im Service-Log gar
        # nichts ueber Vision-Laeufe — beim Live-Debugging zeigte `docker logs`
        # schlicht keine Zeile, obwohl minutenlang gearbeitet wurde.
        # NIE ein Personenname hier: das Service-Log geht in Diagnosen und
        # Support-Ausschnitte. Wer WER erkannt wurde, steht im Protokoll im
        # Datenordner und in der Oberflaeche, nicht hier.
        gal = self._vision_galerien()
        self.log(f"VISION run start: pass={pass_key} "
                 f"backend={_reg.endpunkt_anzeige(_vis.endpunkt_wirksam(blk)) or 'n/a'} "
                 f"galleries={len(gal)} manual={bool(manuell)}")
        z = _vu.pass_urteilen(self.cfg["data_dir"], pass_key, gal,
                              self._vision_regeln(lauf_regeln), _fragen,
                              manuell=manuell)
        # Zellen-Ausweis (User 09.08.): WIE VIELE Bilder das Kandidaten-Gitter
        # wirklich traegt, direkt in der End-Zeile — bisher stand das nur im
        # Lauf-Protokoll (vision.jsonl), nicht im Dienst-Log. "7/10" heisst:
        # 7 genommen, 10 waren als Obergrenze gewuenscht.
        _rl = z.get("regeln_lauf") or {}
        _zellen = _rl.get("bilder_wirksam")
        _gew = _rl.get("bilder_je_pass")
        self.log(f"VISION run end: pass={pass_key} "
                 f"{'verdict' if z.get('person') else 'no verdict'} "
                 f"votes={z.get('voten')} requests={z.get('anfragen')} "
                 f"cells={_zellen if _zellen is not None else '?'}"
                 f"/{_gew if _gew is not None else '?'} "
                 f"{z.get('dauer_s')}s"
                 + (f" — {z['grund']}" if z.get("grund") else ""))
        try:
            art = self._vision_melden(z)          # optional, beide Default AUS
            if art:
                self.log(f"VISION notice sent: pass={pass_key} kind={art}")
        except Exception as e:
            self.log(f"VISION notice failed: {e}")   # nie urteils-relevant
        if z.get("stoerung"):
            # Stiller Ausfall (§10 Stufe 3): DIE Fehlerklasse dieses Pfades.
            # Watchdog-Konvention wie beim Fehlerserien-Waechter, damit es in
            # derselben Log-Suche auftaucht.
            self.log(f"STOERUNG (vision-serie): {z['ausfall_serie']} vision "
                     f"runs in a row without a verdict — last reason: "
                     f"{z.get('grund') or 'unknown'}")
        return z

    def _vision_unbestaetigt(self, z):
        """Feuert der OPTIONALE Nicht-bestaetigt-Alarm fuer diesen Lauf?

        Semantik, eng gefasst (User-Entscheid 08.08.): der Alarm meint genau
        einen Fall — Vision WIDERSPRICHT der Koerper-Einstufung. Der Lauf ist
        wirklich gelaufen, das Modell hat geantwortet, und trotzdem hat kein
        Name gewonnen (konsistentes NEITHER oder Tausch-Widerspruch).

        ABGRENZUNG SEIT V4c (User-Entscheid 08.08. spaetabend): Vision urteilt jetzt auch
        ueber Durchgaenge, die die Koerper-Erkennung als UNBEKANNT gefuehrt hat
        — dort ist ein Nicht-Bestaetigen aber ueberhaupt kein Widerspruch,
        sondern UEBEREINSTIMMUNG, und der Alarm bleibt still (sonst feuerte er
        bei jedem Postboten: Laerm statt Signal). Die Koerper-Einstufung wird
        dafuer als Vergleichs-INPUT gelesen (die Zeilen liegen ohnehin da), NICHT
        als Vorschaltung des Laufs — der Lauf selbst kennt sie nicht mehr.

        Ausdruecklich NICHT: zu wenig Material, Deckel, Selbst-Pause, Timeout,
        Fehler, abgelaufenes Bild. Das waere Laerm, kein Signal.

        Messbasis fuer diese Asymmetrie: die Bekannten-Erkennung liegt in den
        Messreihen bei ~100 %, eine Nicht-Bestaetigung ist also aussagekraeftig;
        die Fremd-Abweisung ist schwach (Decke 44 %), deshalb bekommt Vision in
        die andere Richtung weiterhin kein Stimmrecht."""
        if z.get("person") or not z.get("runden"):
            return False
        if not self._vision_koerper_namen(z):
            return False            # unbekannt eingestuft -> kein Widerspruch
        gruende = [r.get("grund") for r in z["runden"] if r.get("kein_votum")]
        return bool(gruende) and all(g in ("neither", "tausch_widerspruch")
                                     for g in gruende)

    def _vision_koerper_namen(self, z):
        """Wen die KOERPER-Erkennung auf diesem Durchgang behauptet hat (Namen,
        ohne FREMD). Vergleichs-Input, mehr nicht."""
        return sorted({b.get("koerper_klasse") for b in (z.get("bilder") or [])
                       if b.get("koerper_klasse")
                       and b["koerper_klasse"] != "FREMD"})

    def _vision_melden(self, z):
        """Die zwei optionalen Meldungen — ueber die BESTEHENDEN Kanaele, ohne
        eigenen Weg. Beide Schalter sind Produkt-Default AUS; ohne sie passiert
        hier nichts. Personennamen stehen NUR im Meldungs-INHALT (das sind die
        Nutzdaten), nie in der Service-Log-Zeile daneben."""
        s = z.get("sammlung") or {}
        art, titel, text = None, None, None
        if self.cfg.get("vision_alarm_unbestaetigt") and self._vision_unbestaetigt(z):
            art, titel = "unbestaetigt", "suslik vision"
            wer = self._vision_koerper_namen(z)
            text = ("vision could not confirm anyone on this pass"
                    + (f" — the body ranking said {', '.join(wer)}" if wer else "")
                    + f" ({len(z['bilder'])} picture(s) in the grid)")
        elif self.cfg.get("vision_meldung") and (z.get("person") or z.get("bilder")):
            art, titel = "info", "suslik vision"
            text = (f"vision: {z['person']} — unanimous, {s.get('voten')} of "
                    f"{s.get('bilder')} comparison(s)" if z.get("person") else
                    f"vision: no verdict — {z.get('grund') or s.get('grund')}")
        if not text:
            return None
        # .163: ein Lauf, den der Nutzer im Erkennungstest selbst angestossen
        # hat, ist kein Vorfall — die Meldung sagt das jetzt (Praefix im Text,
        # eigenes Feld im MQTT-Payload). Die Unterscheidung steht schon im
        # Protokoll (`manuell`), sie wird hier nur durchgereicht.
        _herk = "manuell" if z.get("manuell") else "live"
        self._mqtt_pub(_melden.topic(self.cfg, "vision_urteil"), json.dumps(
            {"pass_key": z.get("pass_key"), "art": art,
             "person": z.get("person"), "voten": s.get("voten"),
             "bilder": s.get("bilder"), "ts": round(time.time(), 1)},
            ensure_ascii=False), herkunft=_herk)
        push(self.cfg, titel, text, herkunft=_herk)
        if self.cfg.get("telegram_modus", "aus") in ("direkt", "beide"):
            telegram_video(self.cfg, None, text, herkunft=_herk)
        return art

    def vision_test_lage(self, pass_key=""):
        """Alles fuer den Erkennungs-Test (Drei-Wege-Sicht §4) in EINEM Griff:
        die juengsten Durchgaenge und, wenn einer gewaehlt ist, die drei Wege
        nebeneinander. Gesicht und Koerper kommen aus den BUECHERN — hier wird
        nichts nachgerechnet."""
        import datetime
        import szenarien as _sz
        from core import personlive as _plv
        from core import personmodell as _pmz
        from core import visionurteil as _vu
        dd = self.cfg["data_dir"]
        by_eid = {}
        grenze = time.time() - 3 * 86400
        try:
            with open(self.log_path) as f:
                for ln in f:
                    try:
                        r = json.loads(ln)
                    except Exception:
                        continue
                    if r.get("eid") and (r.get("start") or r.get("ts") or 0) >= grenze:
                        by_eid[r["eid"]] = r
        except FileNotFoundError:
            pass
        # .164: bevor die Seite einen Lauf als "laufend" zeigt, faellt ein
        # etwaiger Waisen-Stand dieses Durchgangs. Sonst haengt die Anzeige an
        # einem Lauf, den es nicht mehr gibt.
        if pass_key:
            self.vision_waisen(pass_key)
        kmap = _plv.treffer_karte(dd)
        vmap = _vu.protokoll_karte(dd)      # nur URTEILE (Karte+Liste+Stimme)
        # Stuetzen-Schwelle aus DERSELBEN Quelle wie /heute und /auftritte
        # (status_lesen feuer_ab, Fallback personlive.FEUER_AB) — ohne sie
        # fuhr die Passliste den Signatur-Default und driftete von /heute
        # weg, sobald ein Nutzer die Feuer-Regel unter Person -> Modell-
        # Status verstellt (Randbefund der vision-stimme-2-Drittkontrolle).
        kab = int((_pmz.status_lesen(dd) or {}).get("feuer_ab")
                  or _plv.FEUER_AB)
        passe, treffer = [], None
        for tag in range(3):
            t0 = (datetime.datetime.now().replace(hour=0, minute=0, second=0,
                                                  microsecond=0)
                  - datetime.timedelta(days=tag))
            for s in _sz.szenarien_des_tages(
                    by_eid, t0.timestamp(),
                    (t0 + datetime.timedelta(days=1)).timestamp(), self.cfg,
                    {}, koerper_map=kmap, koerper_ab=kab, vision_map=vmap):
                pk = "%d" % round(s["start"])
                passe.append({"pass_key": pk, "start": s["start"],
                              "events": s["n"], "kameras": len(s["kams"]),
                              "personen": sorted(s["pers"]),
                              "vision": bool(vmap.get(pk))})
                if pk == str(pass_key):
                    treffer = s
        sicht = None
        if treffer is not None:
            zeilen = next((p["zeilen"] for p in _plv.kontrolle_lesen(dd)
                           if p["pass_key"] == str(pass_key)), [])
            # V4b: der LAUF-Stand (Erzaehl-Schritte + Urteil), nicht nur das
            # Urteil — die Spalte zeigt waehrend eines Laufs mit, was passiert.
            sicht = _vu.dreiwege(treffer, zeilen, kmap, _vu.lauf_lesen(dd, pass_key),
                                 bool((self.cfg.get("vision") or {}).get("modell")),
                                 _vu.gesichtsbilder(dd, treffer))
        with self._vision_lock:
            laeuft = bool(self._vision_flug and self._vision_flug.laeuft)
        # ... oder das Protokoll sagt, dass ein Lauf ohne Urteil offen ist (nach
        # einem Dienst-Neustart weiss der Prozess-Zustand nichts mehr davon).
        laeuft = laeuft or bool((sicht or {}).get("vision", {}).get("laeuft"))
        with self._vision_lock:
            nach = dict(self._nachanalyse)
        # .164: die Felder des manuellen Testlaufs brauchen ihre Grenzen — so
        # viele Bestaetigungen, wie es Herausforderer gibt. Die ZELLENZAHL
        # haengt seit .170 nicht mehr am Material (User-Fund: ein Durchgang mit
        # einem Bild belegte das Feld mit 1, der Test fuhr `cells=1/1` statt
        # der Config); Deckel ist die Whitelist-Obergrenze DERSELBEN
        # Einstellung, kein zweites Literal. Begruendung im Docstring von
        # routes.visiontest._felder.
        _mat = (_vu.kandidaten(dd, pass_key, 1,
                               sammeln=bool(self.cfg.get("diagnostic_collection")))
                ["gesamt"] if treffer is not None else 0)
        _gal_n = len(self._vision_galerien())
        return {"passe": passe[:24], "pass_key": str(pass_key or ""),
                "sicht": sicht, "laeuft": laeuft,
                "lauffeld": {
                    "zellen": int(self.cfg.get("vision_bilder_je_pass") or 1),
                    "zellen_max": int(self.CONFIG_WHITELIST
                                      ["vision_bilder_je_pass"][2]),
                    "material": int(_mat or 0),
                    "voten": int(self.cfg.get("vision_min_voten") or 1),
                    "voten_max": max(1, _gal_n - 1),
                    "galerien": _gal_n,
                    "doppellauf": bool(self.cfg.get("vision_doppellauf", True))},
                "laeufe": (_vu.laufliste(dd, pass_key)
                           if treffer is not None else []),
                # .161: die Events dieses Durchgangs (fuer die erneute Analyse)
                # und ihr Laufzustand. Die eids kommen aus DERSELBEN
                # Szenario-Gruppierung wie die Anzeige — nicht aus einer
                # zweiten Rechnung (Szenario-Prinzip).
                "eids": [e["eid"] for e in ((treffer or {}).get("evs") or [])
                         if e.get("eid")],
                "sammeln": bool(self.cfg.get("diagnostic_collection")),
                "nachanalyse": nach}

    def vision_nachanalyse(self, pass_key):
        """.161: EINEN vergangenen Durchgang noch einmal analysieren, damit
        seine beurteilten Bilder im Kontroll-Speicher entstehen.

        Der Fall dahinter (Live-Fund 08.08.): der Sammel-Modus ist AN, aber der
        gewaehlte Durchgang lief davor — dann fehlt Vision jedes Material, und
        der alte Hinweis "turn on diagnostic collection" ging ins Leere.

        Gefahren wird der BESTEHENDE Nachhol-Weg (`process(..., nachhol=1)`):
        stumm, ohne Alarme, ohne Live-Echo, mit dem kurzen Nachhol-Timeout, und
        Event fuer Event unter dem normalen Analyse-Lock — die Live-Erkennung
        wird also nie verdraengt, sie kommt dazwischen. Kein zweiter Decode-
        oder Analysepfad. Einziger Unterschied zum stillen Nachholen: der
        Koerper-Strang laeuft mit, denn nur er legt die Bilder ab.

        Ohne Sammel-Modus verweigert der Anstoss — die Bilder wuerden nach der
        Karenz sofort wieder verschwinden."""
        if not self.cfg.get("diagnostic_collection"):
            return False, ("turn on diagnostic collection under Person first — "
                           "without it the images are deleted again right after "
                           "the pass")
        eids = self.vision_test_lage(pass_key).get("eids") or []
        if not eids:
            return False, "no events found for this walk-through"
        with self._vision_lock:
            if self._nachanalyse.get("laeuft"):
                return False, ("a re-analysis is already running — one at a "
                               "time")
            self._nachanalyse = {"laeuft": True, "pass_key": str(pass_key),
                                 "gesamt": len(eids), "fertig": 0}
        threading.Thread(target=self._nachanalyse_thread,
                         args=(str(pass_key), list(eids)), daemon=True,
                         name="nachanalyse").start()
        return True, (f"re-analysing {len(eids)} event(s) — the judged images "
                      "are collected along the way, this takes a few minutes")

    def _nachanalyse_thread(self, pass_key, eids):
        self.log(f"RE-ANALYSIS start: pass={pass_key} events={len(eids)}")
        try:
            for eid in eids:
                self.process_safe(eid, nachhol=1, koerper=True)
                with self._vision_lock:
                    self._nachanalyse["fertig"] = \
                        int(self._nachanalyse.get("fertig") or 0) + 1
        finally:
            with self._vision_lock:
                self._nachanalyse["laeuft"] = False
            self.log(f"RE-ANALYSIS end: pass={pass_key}")

    def config_wiederherstellen(self, raw):
        """Config-Store aus einer hochgeladenen JSON zurueckspielen (UI 'Restore configuration').
        Validiert (JSON-Objekt, plausible Groesse), sichert den ALTEN Store als .bak-<ts> (Rueckweg —
        kein Rollback ohne Netz), schreibt atomar, startet den Dienst neu. Betrifft NUR die Einstellungen
        (Schwellen/Kameras/Meldekanaele inkl. Secrets); Referenzen/Pool sind separat (Daten-Backup)."""
        import shutil
        try:
            d = json.loads(raw)
        except Exception:
            return False, "not valid JSON — is this a suslik config backup?"
        if not isinstance(d, dict):
            return False, "config backup must be a JSON object"
        if len(d) > 500:
            return False, "config implausibly large — refused"
        # Härten (Code-Review 24.07.): kein roher Store-Dump. Infrastruktur-/Boot-kritische Keys
        # verwerfen (data_dir/web_port kommen nur aus yaml/ENV), Whitelist-Werte gegen Typ/Range
        # pruefen wie config_schreiben; kaputte/verbotene Keys fallen still raus statt den Dienst
        # in einen Boot-Loop zu schreiben.
        bereinigt, verworfen = {}, []
        for key, wert in d.items():
            if key in ("data_dir", "web_port"):
                verworfen.append(key); continue
            if key in self.CONFIG_WHITELIST:
                typ, lo, hi, _ = self.CONFIG_WHITELIST[key]
                try:
                    if typ is list:
                        w = str(wert).strip()
                        if w not in lo:
                            verworfen.append(key); continue
                    elif typ is bool:
                        w = str(wert).lower() in ("1", "true", "ja", "on")
                    else:
                        w = typ(wert)
                        if not (lo <= w <= hi):
                            verworfen.append(key); continue
                except Exception:
                    verworfen.append(key); continue
                bereinigt[key] = w
            else:
                bereinigt[key] = wert          # bekannte Nicht-Whitelist-Keys (Wizard/Meldekanaele) unveraendert
        if not bereinigt:
            return False, "config backup had no usable settings after validation"
        p = _config_store_pfad(self.cfg)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        bak = None
        if os.path.exists(p):
            bak = p + f".bak-{datetime.datetime.now():%Y%m%d_%H%M%S}"
            try:
                shutil.copy2(p, bak)
            except Exception:
                bak = None
        _store_schreiben(p, bereinigt)      # atomar + fsync, unter _cfg_lock (5 Schreibwege)
        try:                                   # Restore-Backups auf die letzten 10 begrenzen
            import glob as _glob
            for old in sorted(_glob.glob(p + ".bak-*"))[:-10]:
                os.remove(old)
        except Exception:
            pass
        try:
            with open(os.path.join(self.cfg["data_dir"], "config", "config_audit.jsonl"), "a") as f:
                f.write(json.dumps({"ts": round(time.time(), 1),
                                    "restore": {"applied": len(bereinigt), "rejected": verworfen,
                                                "backup": os.path.basename(bak) if bak else None}},
                                   ensure_ascii=False) + "\n")
        except Exception:
            pass
        self.log(f"CONFIG RESTORED via UI ({len(bereinigt)} keys, {len(verworfen)} rejected, "
                 f"backup {os.path.basename(bak) if bak else '—'}) — restart after the current analysis")
        self.neustart("Config-Restore")
        msg = f"restored {len(bereinigt)} settings"
        if verworfen:
            msg += f" ({len(verworfen)} rejected: {', '.join(verworfen[:8])})"
        return True, msg + " — service is restarting, reload in ~1 min"

    def voll_wiederherstellen(self, tmp_pfad):
        """PE6 Full-Restore aus dem /backup_voll-Archiv. Ablauf: Mitglieder gegen
        Whitelist validieren -> in .restore-tmp entpacken (tarfile filter='data'
        gegen Pfad-Ausbrueche) -> bestehende Teile als .pre-restore-<ts> zur Seite
        drehen (je Teil bleibt genau EIN Vorstand liegen) -> neue Teile einsetzen ->
        Config-Export ueber den validierten Restore-Weg anwenden -> Neustart."""
        import shutil as _sh
        import tarfile
        data = self.cfg["data_dir"]
        ERLAUBT = ("config-export.json", "config", "faces", "learn", "personlern", "state")
        ziel = os.path.join(data, f".restore-tmp-{os.getpid()}")
        try:
            with tarfile.open(tmp_pfad, "r:gz") as tar:
                for n in tar.getnames():
                    if (n.split("/", 1)[0] not in ERLAUBT or n.startswith("/")
                            or ".." in n.split("/")):
                        return False, f"archive rejected: unexpected member '{n[:80]}'"
                os.makedirs(ziel, exist_ok=True)
                tar.extractall(ziel, filter="data")
        except (tarfile.TarError, OSError) as e:
            _sh.rmtree(ziel, ignore_errors=True)
            return False, f"archive unreadable: {e}"
        stempel = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"
        teile = [t for t in ERLAUBT[1:] if os.path.isdir(os.path.join(ziel, t))]
        if not teile and not os.path.isfile(os.path.join(ziel, "config-export.json")):
            _sh.rmtree(ziel, ignore_errors=True)
            return False, "archive contains none of the expected parts"
        for t in teile:
            alt = os.path.join(data, t)
            for rest in [d for d in os.listdir(data)
                         if d.startswith(f"{t}.pre-restore-")]:
                _sh.rmtree(os.path.join(data, rest), ignore_errors=True)
            if os.path.exists(alt):
                os.rename(alt, f"{alt}.pre-restore-{stempel}")
            os.rename(os.path.join(ziel, t), alt)
        msg = f"restored: {', '.join(teile) or '(no data dirs)'}"
        ce = os.path.join(ziel, "config-export.json")
        if os.path.isfile(ce):
            with open(ce, "rb") as f:
                ok_cfg, msg_cfg = self.config_wiederherstellen(f.read())
            msg += f" · config: {msg_cfg}"           # config-Weg macht den Neustart
            if not ok_cfg:
                self.neustart("Full-Restore (config-Teil abgelehnt)")
        else:
            self.neustart("Full-Restore")
        _sh.rmtree(ziel, ignore_errors=True)
        self.log(f"FULL RESTORE via UI: {msg} (previous state kept as "
                 f"*.pre-restore-{stempel})")
        return True, msg + " — service is restarting, reload in ~1 min"

    def neustart(self, grund=""):
        """Selbst-Neustart nach Config-Aenderung (Setup-Wizard / Konfig / Kamera-Blatt).
        Re-exec des EIGENEN Prozesses statt os._exit(0): supervisor-UNABHAENGIG, laeuft also auch
        ohne systemd Restart=always bzw. docker restart:unless-stopped (frischer Fresh-Install-
        Container mit restart:"no", bare metal). Ein Wizard-Abschluss kann das System so NIE tot
        zuruecklassen. Faellt bei execv-Fehler auf os._exit(0) zurueck (dann uebernimmt ein evtl.
        vorhandener Supervisor doch noch). cwd ist stabil (kein os.chdir im Code), daher loest die
        relative --config nach dem re-exec wieder korrekt auf."""
        def _lauf():
            self._neustart_laeuft = True           # E2: Ernte-Schleife startet keinen neuen
            #                                        Worker mehr (Waisen-Fenster, Widerleger .75)
            with self.lock:                        # wartet auf Abschluss einer laufenden Analyse
                self.log(f"restarting now via re-exec{(': ' + grund) if grund else ''}")
                self.worker_stoppen()              # W2: beenden+wait VOR execv (kein Waisen-Worker
                self.live_aufsicht_stoppen()       # Phase 4: Engine sauber beenden (execv laeuft
                #                                    NICHT durch atexit) — der neue Prozess zieht
                #                                    sie via Supervisor wieder hoch (Bauplan §8)
                self.transcodes_killen()           # W3: kein Waisen-ffmpeg, das nach dem re-exec
                try:                               # weiter in eine .part schreibt (Review-Fund)
                    sys.stdout.flush(); sys.stderr.flush()
                except Exception:
                    pass
                try:
                    # M0/Falle 0: NIE __file__ — nach einer Modul-Verschiebung zeigte das ins
                    # Unterverzeichnis und execv startete das falsche Modul (kein Gate faengt das).
                    os.execv(sys.executable, [sys.executable, VERIFYD_PFAD, *sys.argv[1:]])
                except Exception as e:                 # re-exec scheiterte: Prozess NICHT lebend lassen,
                    self.log(f"re-exec failed ({type(e).__name__}: {e}); os._exit(0), supervisor takes over")
                    os._exit(0)                        # ein evtl. Supervisor holt ihn dann doch hoch
        threading.Thread(target=_lauf, daemon=True).start()

    # ---------------------------------------------------------- W2: persistenter Worker
    def _worker(self):
        """Worker-Objekt bei worker=an (Default), sonst None -> alter Subprozess-Weg
        (der Fallback bleibt vollstaendig im Code, Config-Schalter 'worker')."""
        if not self.cfg.get("worker", True):
            return None
        if self._worker_obj is None:
            self._worker_obj = WorkerProzess(self.cfg, log=self.log)
        return self._worker_obj

    def worker_stoppen(self):
        """Worker beenden+wait — VOR execv (neustart) und am --once-Ende. Sonst liefe eine
        Waise parallel zum frischen Boot in dessen Startup-Benchmark (Exit-139-Bootfenster)."""
        if self._worker_obj is not None:
            try:
                self._worker_obj.stop()
            except Exception:
                pass

    # ------------------------------------------------- Lern-Lauf (E1): Selbstmessung
    _wanduhr_start_lock = threading.Lock()        # Klassen-Lock: Doppelstart-Rennen (F2.2)
    _lernlauf_start_lock = threading.RLock()      # E2: check-then-act der Lauf-Starter atomar
    #                                               (ThreadingHTTPServer; RLock, weil der
    #                                               POST-Handler Starter UNTER dem Lock ruft)
    LERNLAUF_EVENTS_MAX = 40000                   # EIN Eingabe-Deckel fuer POST/GET/Wizard
    #                                               (stand vierfach hartkodiert, Widerleger .75)

    def wanduhr_messen_starten(self):
        """E1 3b (Fassung .71): Selbstmessung EINMAL je Prozess-Leben, gestartet vom
        BOOT (nie von Seitenbesuchen — der QS-Sweep loeste sonst Fremdlast im Gate aus,
        F2.3). Lock gegen Doppelstart (F2.2); nach Scheitern 1 h persistierte Sperre.
        Issue #21: auf Maschinen unter `wanduhr_min_kerne` physischen Kernen
        (Config-Paar, Default WANDUHR_MIN_KERNE — ein Struktur-Axiom, s. dessen
        Kopf) wird GAR NICHT gemessen — LAUT + /health-Vermerk (K1), Prognosen
        bleiben ehrlich auf den als 'rueckfall' gekennzeichneten Autorwerten."""
        min_kerne = int(self.cfg.get("wanduhr_min_kerne") or WANDUHR_MIN_KERNE)
        kerne = _phys_kerne()
        if kerne < min_kerne:
            # K1: der Grund steht im STARTLOG und klebt fuer /health am Dienst —
            # sonst ist 'keine Messung vorhanden' nicht von 'still verhungert'
            # unterscheidbar (Tokn59-Klasse: 2C/4T-NUC saettigte minutenlang).
            self._wanduhr_skip = (
                f"{kerne} physical core(s) usable (cgroup CPU quota counted), "
                f"self-measurement needs >= {min_kerne} (it runs a second full "
                f"analysis process next to the live one); run-duration forecasts "
                f"keep the fallback values (labeled as such) — to measure anyway, "
                f"deliberately lower wanduhr_min_kerne in Settings")
            self.log(f"wanduhr: measurement SKIPPED on this machine — {self._wanduhr_skip}")
            return False
        with self._wanduhr_start_lock:
            t = getattr(self, "_wanduhr_thread", None)
            if t and t.is_alive():
                return True
            if getattr(self, "_wanduhr_versucht", False):
                return False
            sp = os.path.join(self.cfg["data_dir"], "state", "wanduhr_fehl.json")
            try:
                letzte = json.load(open(sp)).get("ts", 0)
            except Exception:
                letzte = 0
            if time.time() - letzte < 3600:
                return False
            self._wanduhr_versucht = True
            t = threading.Thread(target=self._wanduhr_messen, daemon=True,
                                 name="wanduhr-mess")
            self._wanduhr_thread = t
            t.start()
            return True

    def wanduhr_laeuft(self):
        t = getattr(self, "_wanduhr_thread", None)
        return bool(t and t.is_alive())

    def wanduhr_status(self):
        """Wanduhr-Lage fuer /health (K1, Issue #21): OB Messwerte fuer DIESE
        Maschine+Version vorliegen (quelle gemessen/rueckfall, dieselben Slugs wie
        im Wizard), ob gerade gemessen wird, und WARUM nicht (uebersprungen /
        letzter Fehlversuch) — vorher war eine fehlende Messung still und aus der
        Ferne nicht diagnostizierbar."""
        from core import wanduhr as _wu
        _, quelle, _ = _wu.lesen(self.cfg["data_dir"], _placement_hw_key(),
                                 os.environ.get("SUSLIK_VERSION", "dev"))
        st = {"quelle": quelle, "laeuft": self.wanduhr_laeuft()}
        if st["laeuft"]:
            # Warte- und Mess-Zustand getrennt ausweisen (Pflichtpunkt .172):
            # "waiting" = Schleife wartet lockfrei auf Live-Ende, "measuring" =
            # Roundtrip rechnet wirklich — "laeuft" allein verschmolz beides.
            st["phase"] = getattr(self, "_wanduhr_phase", None) or "starting"
        grund = getattr(self, "_wanduhr_skip", None)
        if grund:
            st["uebersprungen"] = grund
        try:
            with open(os.path.join(self.cfg["data_dir"], "state",
                                   "wanduhr_fehl.json")) as f:
                d = json.load(f)
            st["letzter_fehlversuch"] = {"ts": d.get("ts"), "grund": d.get("grund")}
        except Exception:
            pass
        return st

    def _roundtrip_fahren(self, eid, person, out):
        """EIN worker-Roundtrip als Subprozess — mit derselben Umgebung wie die
        produktiven Spawns (F2.4: SCRATCH_DIR fehlte -> refcache/Clip landeten in /tmp
        und verfaelschten den Kaltaufschlag; OV_DEVICE der Symmetrie halber)."""
        import subprocess as _sp
        cmd = [sys.executable, os.path.join(HERE, "worker.py"), "--roundtrip",
               str(eid), "--persons", person, "--labels", "WANDUHR",
               "--dir", out, "--fps-sample", str(self.cfg.get("fps_sample", 3))]
        _env = {**os.environ,
                "FRIGATE_URL": self.cfg.get("frigate_url") or "",
                "SCRATCH_DIR": os.path.join(self.cfg["data_dir"], "clips"),
                "OV_DEVICE": str(self.cfg.get("ov_device") or "")}
        # Deckel je Roundtrip aus der Config statt hart 1800 (Nachbesserung W6):
        # ein Roundtrip = kalter + warmer Lauf in EINEM Subprozess, also 2 Analysen
        # + Kaltstart-Luft -> 3 x analyse_timeout_s (Default 3*600 = die bisherigen
        # 1800). Waehrend der Frist haelt _roundtrip_seriell den Analyse-Slot —
        # ein eintreffender Live-Job wartet dort; die Frist deckelt damit auch
        # SEINE Wartezeit, und sie skaliert mit, wenn der Nutzer den Watchdog
        # fuer eine langsame Maschine anhebt.
        tmo = 3 * int(self.cfg.get("analyse_timeout_s") or 600)
        # ANALYSE_NICE auch hier (Issue #21): die Wanduhr misst, wie lange eine
        # Analyse auf DIESER Maschine dauert — die echten Analysen laufen mit
        # nice +10, also muss die Messung es auch, sonst misst sie eine andere
        # Scheduling-Welt als die, in der spaeter geurteilt wird.
        r = _sp.run(cmd, capture_output=True, text=True, timeout=tmo, env=_env,
                    preexec_fn=_analyse_nice)
        d = json.loads((r.stdout.strip().splitlines() or ["{}"])[-1])
        if not (d.get("lauf1", {}).get("ok") and d.get("lauf2", {}).get("ok")):
            grund = (d.get("lauf1", {}).get("fehler") or d.get("lauf2", {}).get("fehler")
                     or (r.stderr or "").strip().splitlines()[-1:] or "?")
            raise RuntimeError(f"roundtrip not ok (rc={r.returncode}): {grund}")
        return d

    def _live_aktiv(self):
        """'Live laeuft' im Sinne der Wanduhr-Serialisierung (Nachbesserung W1b):
        der Gesichts-Pass (process() haelt self.lock) ODER ein laufender
        Koerper-Strang — _person_live startet einen daemon-Thread, der self.lock
        UEBERLEBT und in-Prozess voll rechnet (Decode 3 fps + PoseWache + DINOv2 +
        SVM); self.lock allein uebersah ihn, und zwar genau bei _koerper_scharf(),
        also den CPU-schwersten Installationen der Issue-#21-Klasse. Vision zaehlt
        bewusst NICHT: dessen Urteil rechnet nicht im Dienstprozess (eigener/
        externer Endpunkt-Prozess), nur der Anstoss laeuft hier."""
        return self.lock.locked() or self._personlive_aktiv > 0

    def _roundtrip_seriell(self, eid, person, out):
        """Issue #21 (Tokn59, 2C/4T): der Mess-Roundtrip ist ein ZWEITER voller
        Analyse-Prozess neben der Live-Verarbeitung; _gpu_bg_lock liess Live
        bewusst frei — auf kleinen Maschinen hiess 'frei' Minuten Doppellast.

        Ablauf je Runde (Ernte-Muster, s. deren `with self._gpu_bg_lock`-Schleife
        — ALLE Locks werden je Runde wieder hergegeben, gewartet wird IMMER
        lockfrei):
          (1) _gpu_bg_lock nehmen (BG-Jobs seriell). NIE waehrend des Wartens
              halten (Nachbesserung W5: genau das blockierte _nachhol_runde,
              _sammle_fahren und _szenario_nachsammeln — die start_nachhol-Regel
              gilt auch hier).
          (2) Live pruefen (_live_aktiv: Gesichts-Pass ODER Koerper-Strang, W1b)
              und den Analyse-Slot NICHT-BLOCKIEREND nehmen (wk.lock; bei
              worker=aus dasselbe _ANALYSE_SERIELL, das der Legacy-run_analyze
              nimmt — Nachbesserung W8, vorher reines check-then-act mit
              nachgewiesenem Parallel-Fenster).
          (3) Live UNTER dem Slot erneut pruefen (TOCTOU: zwischen Pruefung und
              acquire kann ein Pass self.lock genommen haben; der haengt dann
              gleich am Slot — wir geben ihn zurueck statt neben ihm zu starten).
          (4) Erst wenn alles haelt: Roundtrip fahren, Locks am Ende freigeben.

        EHRLICHE GRENZEN (Nachbesserung W6, kein Vorrang-Ueberclaim): Vorrang hat
        Live nur fuer den START der Messung. Laeuft der Roundtrip erst, wartet
        ein NEU eintreffender Live-Job am Analyse-Slot bis zu dessen Ende (er
        haelt dabei self.lock, die Live-Kette steht) — Obergrenze je Roundtrip
        ist die _roundtrip_fahren-Frist 3 x analyse_timeout_s. Seine
        Watchdog-Frist beginnt erst NACH dem Lock und die Wartezeit wird aus
        dauer_s herausgerechnet (W7). Zwischen den beiden Roundtrips einer
        Messung ist alles freigegeben, ein Wartender kommt dort dran. Das gilt
        auf JEDER Maschine, die misst — auch auf grossen aendert die
        Serialisierung den Messweg (dafuer misst sie unverfaelscht; "nicht
        doppellastig" gilt gegen Gesichts-Pass, Koerper-Strang und Analyse-Slot,
        s. _live_aktiv — Anzeige-Transcodes und der Vision-Anstoss bleiben
        aussen vor, die rechnen im Dienstprozess nicht schwer).
        Lock-Ordnung wie Ernte/_sammle_fahren: _gpu_bg_lock ->
        Slot; niemand nimmt sie andersherum, der Slot wird nur nicht-blockierend
        genommen, und kein self.lock-Halter blockiert auf _gpu_bg_lock (die
        BG-Starter unter self.lock spawnen nur Threads) — deadlockfrei. Ein
        Neustart (neustart -> worker_stoppen -> wk.lock) wartet das Ende des
        laufenden Roundtrips ab, statt ihn als Vollast-Waise ins frische
        Boot-Fenster zu entlassen."""
        wk = self._worker()
        slot = wk.lock if wk is not None else _ANALYSE_SERIELL
        gemeldet = False
        # Warten ist nicht Messen (Pflichtpunkt der .172-Kontrolle): die Schleife
        # kann Minuten stehen, wanduhr_status zeigt die Phase getrennt an.
        self._wanduhr_phase = "waiting"
        while True:
            with self._gpu_bg_lock:
                if not self._live_aktiv() and slot.acquire(blocking=False):
                    try:
                        if not self._live_aktiv():          # Schritt (3), s. Docstring
                            self._wanduhr_phase = "measuring"
                            return self._roundtrip_fahren(eid, person, out)
                    finally:
                        slot.release()
            if not gemeldet:
                gemeldet = True
                self.log("wanduhr: waiting for live activity (face pass / person "
                         "judgment) to finish before measuring")
            time.sleep(2)

    def _wanduhr_messen(self):
        """Messablauf .71: (1) 90 s Boot-Ruhe, (2) jeder Roundtrip einzeln gegen
        Live serialisiert UND nur fuer seine Dauer unter _gpu_bg_lock
        (_roundtrip_seriell; Nachbesserung W5: das Lock lag frueher um die GANZE
        Messung und wurde damit unbegrenzt lange gehalten, waehrend auf Live
        gewartet wurde — _nachhol_runde fiel aus, _sammle_fahren blockierte.
        F2.3 'hoechstens EIN schwerer Hintergrundlauf' bleibt erfuellt: schwer
        sind allein die Roundtrips, und die laufen unter dem Lock; die Event-Wahl
        hier sind API-Reads), (3) Mess-Event mit MINDESTLAENGE via
        core.wanduhr.kontroll_event (F2.5), (4) Konstanten ableiten, (5) REALITAETS-
        KOPPLUNG an einem ZWEITEN Event (F1.5) — erst bei Bestehen wird gespeichert,
        mit ehrlicher Liste der wirklich gemessenen Felder (F3.1)."""
        try:
            time.sleep(90)                        # Boot-Warmup/Backfill nicht stoeren
            import shutil as _sh
            from core import ereignisse as _evm
            from core import wanduhr as _wu
            evs, _ = _evm.person_events(lambda p: api(self.cfg, p), 40)
            mess, clip_s = _wu.kontroll_event(evs)
            personen = master_persons(self.cfg)
            if mess is None or not personen:
                self.log("wanduhr: no suitable measurement event yet (need a clip "
                         ">= %.0f s) or empty master — fallback values stay"
                         % _wu.KONTROLL_MIN_CLIP_S)
                return
            out = os.path.join(self.cfg["data_dir"], "state", "wanduhr_mess")
            _sh.rmtree(out, ignore_errors=True)
            os.makedirs(out, exist_ok=True)
            d = self._roundtrip_seriell(mess["id"], personen[0], out)
            werte = _wu.aus_roundtrip(d["lauf1"], d["lauf2"], clip_s, None)
            # Realitaets-Kopplung am ZWEITEN Event: warm-Lauf gegen die Prognose.
            k2, k2_clip_s = _wu.zweit_event(evs, mess["id"])
            if k2 is not None:
                _sh.rmtree(out, ignore_errors=True)
                os.makedirs(out, exist_ok=True)
                d2 = self._roundtrip_seriell(k2["id"], personen[0], out)
                okk, abw = _wu.kopplung_pruefen(werte, k2_clip_s, None,
                                                float(d2["lauf2"]["wall_s"]))
                if not okk:
                    raise RuntimeError(
                        f"reality check failed on control event {k2['id']}: "
                        f"prediction off by {abw:+.0%} (> ±{_wu.KOPPLUNG_TOLERANZ:.0%})")
                kopp = {"eid": k2["id"], "abweichung": round(abw, 3)}
            else:
                kopp = None
                self.log("wanduhr: no second control event — storing measurement "
                         "WITHOUT reality check (will be validated by later runs)")
            _wu.schreiben(self.cfg["data_dir"], _placement_hw_key(),
                          os.environ.get("SUSLIK_VERSION", "dev"), werte,
                          {"eid": mess["id"], "clip_s": round(clip_s, 1),
                           **({"kopplung": kopp} if kopp else {})},
                          gemessen=_wu.GEMESSENE_FELDER_ROUNDTRIP)
            self.log(f"wanduhr: measured — cold {d['lauf1'].get('wall_s')} s / warm "
                     f"{d['lauf2'].get('wall_s')} s on {clip_s:.0f} s clip"
                     + (f"; reality check on 2nd event passed ({kopp['abweichung']:+.0%})"
                        if kopp else ""))
        except Exception as ex:
            self.log(f"wanduhr: measurement failed ({ex}) — keeping fallback values; "
                     f"next attempt in 1 h (or on restart)")
            try:
                sp = os.path.join(self.cfg["data_dir"], "state", "wanduhr_fehl.json")
                with open(sp, "w", encoding="utf-8") as f:
                    json.dump({"ts": round(time.time(), 1), "grund": str(ex)[:300]}, f)
            except Exception:
                pass
        finally:
            import shutil as _sh
            _sh.rmtree(os.path.join(self.cfg["data_dir"], "state", "wanduhr_mess"),
                       ignore_errors=True)

    def lernlauf_vorbereiten_starten(self, anzahl, alle_modus=False):
        """E1.72: die Vorbereitungs-Phase ARBEITET sichtbar (User-Wunsch nach dem
        ersten 10er-Lauf: 'dann wuesste man, der arbeitet im Hintergrund') — geht die
        gewaehlten Events einzeln durch, prueft Clip-Verfuegbarkeit, zaehlt im
        Lauf-Zustand hoch und persistiert die GEPRUEFTE Event-Liste (die braucht E2
        ohnehin; schliesst zugleich die Widerleger-Luecke 'nur die Zahl gespeichert')."""
        with self._lernlauf_start_lock:               # F2.2: check-then-act atomar
            t = getattr(self, "_lernlauf_prep_thread", None)
            if t and t.is_alive():
                return False
            t = threading.Thread(target=self._lernlauf_vorbereiten, daemon=True,
                                 name="lernlauf-prep", args=(anzahl, alle_modus))
            self._lernlauf_prep_thread = t
        t.start()
        return True

    def _lernlauf_vorbereiten(self, anzahl, alle_modus):
        from core import ereignisse as _evm
        from core import lernlauf as _ll
        dd = self.cfg["data_dir"]
        try:
            evs, _ = _evm.person_events(lambda p: api(self.cfg, p),
                                        None if alle_modus else anzahl)
            n = len(evs)
            _ll.lauf_fortschreiben(dd, fortschritt={"checking events": f"0/{n}"})
            liste, mit_clip = [], 0
            for i, e in enumerate(evs, 1):
                hat_clip = e.get("has_clip") is True
                mit_clip += 1 if hat_clip else 0
                t0, t1 = e.get("start_time"), e.get("end_time")
                liste.append({"eid": e.get("id"), "kamera": e.get("camera"),
                              "start": t0, "clip_s": round(max(t1 - t0, 0.0), 1)
                              if (t0 and t1) else None, "hat_clip": hat_clip})
                # jede Handvoll persistieren: sichtbares Ticken + absturzfest
                if i % 2 == 0 or i == n:
                    if _ll.lauf_fortschreiben(dd, fortschritt={
                            "checking events": f"{i}/{n}"}) is None:
                        self.log("learning run preparation stopped (run aborted)")
                        return
                time.sleep(0.2)                   # UI-sichtbar, nicht Frigate-fluten
            z = _ll.lauf_fortschreiben(dd, events_liste=liste,
                                       fortschritt={"checking events": f"{n}/{n}",
                                                    "with clip": mit_clip,
                                                    "skipped (no clip)": n - mit_clip,
                                                    "status": "prepared — starting "
                                                              "the harvest"})
            if z is not None:
                self.log(f"learning run prepared: {n} events checked, {mit_clip} with clip")
                if z.get("erntefreigabe"):
                    self.lernlauf_ernte_starten()  # E2: die Kette laeuft von selbst weiter
                else:
                    # Alt-Zustand aus dem Fundament-Build (E1-Shadow): NIE ungefragt
                    # ernten (Widerleger .75/L1) — der Nutzer legt den Lauf neu an.
                    _ll.lauf_fortschreiben(dd, fortschritt={
                        "status": "planned under the foundation build — abort and "
                                  "create the run again to harvest"})
        except Exception as e:
            _ll.lauf_fortschreiben(dd, fortschritt={"status": f"preparation failed: {e}"})
            self.log(f"learning run preparation failed ({e})")

    def lernlauf_ernte_starten(self):
        """E2 (S7): Frontal-Ernte-Schleife starten (ein Thread; Doppelstart-Guard
        UNTER dem Klassen-Lock — check-then-act war unter ThreadingHTTPServer ein
        Rennen, die F2.2-Klasse aus E1)."""
        with self._lernlauf_start_lock:
            t = getattr(self, "_lernlauf_ernte_thread", None)
            if t and t.is_alive():
                return False
            t = threading.Thread(target=self._lernlauf_ernte, daemon=True,
                                 name="lernlauf-ernte")
            self._lernlauf_ernte_thread = t
        t.start()
        return True

    def lernlauf_anker_starten(self):
        """E3 (§P2): Anker-Phase starten (ein Thread, Doppelstart-Guard wie Ernte).
        Rein rechnerisch (liest nur den Laufordner) — braucht weder GPU-Lock noch
        Sammel-Koexistenz; den Unbekannt-Pool fasst sie nicht an."""
        with self._lernlauf_start_lock:
            t = getattr(self, "_lernlauf_anker_thread", None)
            if t and t.is_alive():
                return False
            t = threading.Thread(target=self._lernlauf_anker, daemon=True,
                                 name="lernlauf-anker")
            self._lernlauf_anker_thread = t
            t.start()          # .83: unter dem Lock — ein zweiter Aufrufer sah den
        return True            # gespeicherten, ungestarteten Thread als is_alive()==False

    def _lernlauf_anker(self):
        """Duenner Dienst-Mantel um core.anker.anker_phase_fahren (Logik NUR im Modul,
        I1): Config-Schwellen einsammeln, Callbacks reichen, Fehler in den Lauf-Store
        statt in einen stillen Thread-Tod."""
        from core import anker as _ank, lernlauf as _ll
        import anlernen as _al
        dd = self.cfg["data_dir"]
        try:
            zustand, fehler = _ll.lauf_lesen(dd)
            if zustand is None:
                self.log(f"anchor stage: no learning run to work on ({fehler or 'no state'})")
                return
            if not zustand.get("events_liste"):
                _ll.lauf_fortschreiben(dd, fortschritt={
                    "status": "anchor stage failed: run has no persisted event list"})
                return
            lauf_id = zustand["lauf_id"]
            schwellen = {k: self.cfg[k] for k in
                         ("anker_sim1", "anker_sim2", "anker_marge_warn", "anker_hart",
                          "anker_k_min", "anker_deckel", "anker_deckel_hart")}
            schwellen["szenario_gap_min"] = int(self.cfg.get("szenario_gap_min", 5))
            self.log(f"anchor stage starting (run {lauf_id})")
            erg = _ank.anker_phase_fahren(
                dd, os.path.join(dd, "state", "lernlauf", lauf_id), lauf_id,
                zustand["events_liste"], schwellen, _al.clustere,
                os.environ.get("SUSLIK_VERSION", "dev"), self.log,
                lambda **u: _ll.lauf_fortschreiben(dd, **u))
            if erg is not None:
                # Crash-Loop-Wache (#20): erfolgreicher Abschluss setzt den
                # Boot-Resume-Zaehler zurueck — nur ununterbrochene Fehlserien
                # derselben Phase laufen gegen anker_resume_max.
                _ll.lauf_fortschreiben(dd, anker_neuanlaeufe=0)
        except Exception as e:
            from core import lernlauf as _ll2
            _ll2.lauf_fortschreiben(dd, fortschritt={"status": f"anchor stage failed: {e}"})
            self.log(f"anchor stage failed ({type(e).__name__}: {e})")

    def _lernlauf_ernte(self):
        """Frontal-Ernte (Konzept §P1): 1 Event je Worker-Job; die Live-Wache wird
        UNTER dem _gpu_bg_lock geprueft (Widerleger .75/L2: davor konnte sie beim
        Absenden beliebig veraltet sein); das Regime (Schwellen/fps) friert das
        Lauf-Manifest ein — Resume nutzt IMMER das Manifest, nie die aktuelle
        Config; Koexistenz-Pause uebers _sammel_laeuft/_nachhol-Muster; Resume
        idempotent (fertig.jsonl + Kandidaten-Datei je Event); ehrliche Zaehler
        inkl. fd/ohne_pose/teilweise-lesbar; am Ende Buecher-gegen-Platte-Wache."""
        from core import ernte as _ern
        from core import lernlauf as _ll
        from core import wanduhr as _wu
        dd = self.cfg["data_dir"]
        zustand, fehler = _ll.lauf_lesen(dd)
        if zustand is None:
            if fehler:
                self.log(f"harvest not started: run state unreadable ({fehler})")
            return
        if zustand.get("phase") not in ("vorbereitung", "ernte"):
            return
        liste = zustand.get("events_liste")
        if not liste:
            _ll.lauf_fortschreiben(dd, fortschritt={
                "status": "harvest failed: no prepared event list"})
            self.log("harvest failed: run state carries no events_liste")
            return
        if not self.cfg.get("worker", True):
            # Die Ernte laeuft AUSSCHLIESSLICH ueber den Worker (1 Event je Job =
            # der Live-Vorrang-Mechanismus selbst) — ohne ihn ehrlich stoppen.
            _ll.lauf_fortschreiben(dd, fortschritt={
                "status": "harvest failed: the persistent worker is disabled "
                          "(config 'worker'), the harvest needs it"})
            self.log("harvest failed: worker disabled")
            return
        lauf_id = zustand.get("lauf_id") or ("L" + time.strftime("%Y%m%d_%H%M%S"))
        lauf_dir = os.path.join(dd, "state", "lernlauf", lauf_id)
        # REGIME einfrieren bzw. beim Resume aus dem Manifest uebernehmen — sonst
        # mischt eine Schwellen-Aenderung + execv zwei Gate-Saetze in EINEN Lauf.
        manifest = _ern.manifest_lesen(lauf_dir)
        if manifest is None:
            schwellen = {"det_thresh": self.cfg.get("det_thresh"),
                         "fd_front_min": self.cfg.get("fd_front_min"),
                         "fd_sharp_min": self.cfg.get("fd_sharp_min"),
                         "fd_det_max": self.cfg.get("fd_det_max"),
                         "m_det_min": self.cfg.get("ernte_m_det_min"),
                         "m_kante_min": self.cfg.get("ernte_m_kante_min"),
                         "m_sharp_min": self.cfg.get("ernte_m_sharp_min"),
                         "s_det_min": self.cfg.get("ernte_s_det_min"),
                         "s_winkel_max": self.cfg.get("ernte_s_winkel_max")}
            fehlend = _ern.schwellen_pruefen(schwellen)
            if fehlend:
                _ll.lauf_fortschreiben(dd, fortschritt={
                    "status": f"harvest failed: thresholds missing ({', '.join(fehlend)})"})
                self.log(f"harvest failed: thresholds missing ({fehlend})")
                return
            starts = [e.get("start") for e in liste if e.get("start")]
            manifest = {"schema": 1,
                        "version": os.environ.get("SUSLIK_VERSION", "dev"),
                        "modell": self.cfg.get("modell"),
                        # .83: Lauf-Wahl aus dem Wizard schlaegt den Config-Default
                        # (Task #10); das Manifest friert sie ein — Resume rechnet
                        # NIE mit veraendertem Wert weiter (E2-Vertrag).
                        "fps_sample": zustand.get("fps_sample") or self.cfg.get("fps_sample"),
                        "schwellen": schwellen,
                        "angelegt": round(time.time(), 1),
                        # E3-Hinweis (§Q): exakter N-Schnitt kann den aeltesten
                        # Durchgang anschneiden — die Grenze steht HIER, nicht nirgends.
                        "schnitt_exakt_n": not bool(zustand.get("alle")),
                        "aeltester_start": min(starts) if starts else None}
            _ern.manifest_schreiben(lauf_dir, manifest)
        schwellen = manifest["schwellen"]
        fps = manifest.get("fps_sample") or self.cfg.get("fps_sample")
        # Phasen-Uebergang ABBRUCHSICHER: fortschreiben liefert None, wenn der
        # Nutzer eben abgebrochen hat (lauf_schreiben haette den Lauf wiederbelebt).
        if _ll.lauf_fortschreiben(dd, phase="ernte", lauf_id=lauf_id,
                                  fortschritt={"status": "harvesting"}) is None:
            self.log("harvest not started (run aborted)")
            return
        erworben = False
        try:
            # Koexistenz (§2.6): sichtbar warten, bis ein ECHTES Sammeln ausgelaufen
            # ist; danach pausiert das Auto-Sammeln fuer die Lauf-Dauer.
            gewartet = False
            while True:
                z0, f0 = _ll.lauf_lesen(dd)
                if z0 is None:
                    self.log(f"harvest stopped: run state unreadable ({f0})"
                             if f0 else "harvest stopped while waiting (run aborted)")
                    return
                with self._sammel_lock:
                    if not self._sammel_laeuft:
                        self._sammel_laeuft = True
                        erworben = True
                        break
                if not gewartet:
                    gewartet = True
                    self.log("harvest waiting for a running collection to finish")
                    _ll.lauf_fortschreiben(dd, fortschritt={
                        "status": "waiting for the auto-collection to finish"})
                time.sleep(5)
            if gewartet:
                if _ll.lauf_fortschreiben(dd,
                                          fortschritt={"status": "harvesting"}) is None:
                    self.log("harvest stopped (run aborted)")
                    return
            self.log(f"harvest starting (run {lauf_id}): auto-collection paused until done")
            fertig, summe = _ern.fertig_lesen(lauf_dir)
            if summe.get("kaputt"):
                self.log(f"harvest resume: {summe['kaputt']} unreadable fertig.jsonl "
                         "lines — the affected events will be harvested again")
            mit_clip = [e for e in liste if e.get("hat_clip")]
            ohne_clip = len(liste) - len(mit_clip)
            werte, _q, _g = _wu.lesen(dd, _placement_hw_key(),
                                      os.environ.get("SUSLIK_VERSION", "dev"))
            n = len(mit_clip)
            clips_dir = os.path.join(dd, "clips")
            # Deckel wie beim Nachhol-Backfill (Config, nie hart): ein pathologisches
            # Event darf den Live-Pfad nicht minutenlang halten (Leitprinzip 5;
            # 1800 hart war das Loch, das dieser Key historisch geschlossen hat).
            timeout_s = int(self.cfg.get("nachhol_analyse_timeout_s") or 300)
            for i, e in enumerate(mit_clip, 1):
                eid = e.get("eid")
                if eid in fertig:
                    continue
                # .86: das AKTUELLE Event sichtbar machen — bei hoher fps dauert
                # ein Event Minuten, und ohne diese Zeile sah 'event: 11/50' wie ein
                # Haenger aus, obwohl Event 12 mitten in der Analyse steckte.
                _ll.lauf_fortschreiben(dd, fortschritt={
                    "analysing": f"{e.get('kamera', '?')} clip {round(e.get('clip_s') or 0)}s"})
                z, ferr = _ll.lauf_lesen(dd)
                if z is None:
                    self.log(f"harvest stopped: run state unreadable ({ferr})"
                             if ferr else "harvest stopped (run aborted)")
                    return
                if getattr(self, "_neustart_laeuft", False):
                    # execv im Anflug: keinen neuen Worker starten (Waisen-Fenster,
                    # Widerleger .75/L2) — der Boot-Resume setzt den Lauf fort.
                    self.log("harvest paused for service restart — resumes after boot")
                    return
                antwort, abgesendet = None, False
                while not abgesendet:
                    with self._gpu_bg_lock:         # BG-Jobs seriell; Live-Wache HIER,
                        if not self.lock.locked():  # nicht davor (sonst veraltet sie)
                            antwort = self._worker().job(
                                {"typ": "ernte", "eid": eid, "kamera": e.get("kamera"),
                                 "ts": e.get("start") or 0, "fps_sample": fps,
                                 "schwellen": schwellen, "lauf_dir": lauf_dir,
                                 "log": os.path.join(lauf_dir, "ernte.log")},
                                timeout_s=timeout_s)
                            abgesendet = True
                    if not abgesendet:
                        time.sleep(1)
                        zz, zf = _ll.lauf_lesen(dd)
                        if zz is None:
                            self.log(f"harvest stopped: run state unreadable ({zf})"
                                     if zf else "harvest stopped while waiting for "
                                                "the live path (run aborted)")
                            return
                # Abbruch WAEHREND des Jobs: nichts mehr buchen — fertig_anhaengen
                # wuerde das eben nach trash verschobene Lauf-Verzeichnis neu anlegen.
                z, ferr = _ll.lauf_lesen(dd)
                if z is None:
                    self.log(f"harvest stopped: run state unreadable ({ferr})"
                             if ferr else "harvest stopped after the running event "
                                          "(run aborted)")
                    return
                eintrag = {"eid": eid, "ok": bool(antwort and antwort.get("ok"))}
                if antwort and antwort.get("ok"):
                    for k in ("detektionen", "fd", "ohne_pose", "kandidaten", "m", "s"):
                        eintrag[k] = int(antwort.get(k) or 0)
                        summe[k] = summe.get(k, 0) + eintrag[k]
                    for k in ("frames_gelesen", "frames_soll"):
                        eintrag[k] = antwort.get(k)
                    inv = _ern.zaehler_pruefen(antwort)
                    if inv:
                        summe["invariante"] = summe.get("invariante", 0) + 1
                        self.log(f"harvest {eid}: {inv}")
                    if antwort.get("unvollstaendig"):
                        eintrag["unvollstaendig"] = True   # Teil-Verlust NIE still (§2.3)
                        summe["unvollstaendig"] = summe.get("unvollstaendig", 0) + 1
                    if antwort.get("unlesbar"):
                        eintrag["unlesbar"] = True
                        summe["unlesbar"] = summe.get("unlesbar", 0) + 1
                    elif not antwort.get("kandidaten"):
                        eintrag["ohne_gesicht"] = True
                        summe["ohne_gesicht"] = summe.get("ohne_gesicht", 0) + 1
                    if antwort.get("letzter_m"):
                        summe["letzter_fund"] = antwort["letzter_m"]
                else:
                    eintrag["fehler"] = ((antwort or {}).get("fehler")
                                         or "worker timeout/crash")
                    summe["fehler"] = summe.get("fehler", 0) + 1
                    self.log(f"harvest {eid} FAILED: {eintrag['fehler']}")
                    _ern.event_aufraeumen(lauf_dir, eid)   # keine Teilzeilen-Leichen
                _ern.fertig_anhaengen(lauf_dir, eintrag)
                fertig.add(eid)
                rest_txt = "?"
                try:
                    offen = [{"clip_s": x.get("clip_s") or 0.0,
                              "im_cache": os.path.isfile(os.path.join(
                                  clips_dir, str(x.get("eid")).replace("/", "_") + ".mp4"))}
                             for x in mit_clip[i:] if x.get("eid") not in fertig]
                    p = _wu.lauf_prognose(werte, offen, live_last=True)
                    rest_txt = f"~{int(round((p['gesamt_s'] - p['kalt_s']) / 60))} min"
                except Exception:
                    pass
                fs = {"event": f"{i}/{n}", "candidates": summe.get("kandidaten", 0),
                      "crop-worthy (M)": summe.get("m", 0),
                      "anchor-ready (S)": summe.get("s", 0),
                      "objects filtered (fd rule)": summe.get("fd", 0),
                      "without a face": summe.get("ohne_gesicht", 0),
                      "clip not readable": summe.get("unlesbar", 0),
                      "rest": rest_txt}
                if summe.get("ohne_pose"):
                    fs["no pose data"] = summe["ohne_pose"]
                if summe.get("unvollstaendig"):
                    fs["clips partly readable"] = summe["unvollstaendig"]
                if summe.get("invariante"):
                    fs["counter mismatch"] = summe["invariante"]
                if summe.get("fehler"):
                    fs["worker errors"] = summe["fehler"]
                if ohne_clip:
                    fs["skipped (no clip)"] = ohne_clip
                lf = summe.get("letzter_fund")
                if lf:
                    fs["last find"] = f"{lf.get('kamera')} @ {lf.get('t')} s"
                if _ll.lauf_fortschreiben(dd, fortschritt=fs) is None:
                    self.log("harvest stopped (run aborted)")
                    return
            # Buecher-gegen-Platte (Widerleger .75/L3: zaehler_pruefen prueft nur
            # das Dict gegen sich selbst — HIER stehen Datei und Zaehler gegeneinander).
            befunde = _ern.bestand_pruefen(lauf_dir)
            if befunde:
                self.log(f"harvest BOOKKEEPING MISMATCH ({len(befunde)}): "
                         + " · ".join(befunde[:5]))
            schluss = {"status": "harvest finished — anchor stage starting (E3)",
                       "analysing": None}      # .87: aktuelles-Event-Zeile raeumen (Forensik-Fund 7)
            if befunde:
                schluss["files vs counters"] = f"{len(befunde)} mismatches (see log)"
            _ll.lauf_fortschreiben(dd, fortschritt=schluss)
            self.log(f"harvest finished (run {lauf_id}): "
                     f"{summe.get('kandidaten', 0)} candidates "
                     f"({summe.get('m', 0)} crop-worthy, {summe.get('s', 0)} anchor-ready) "
                     f"from {n} events; {summe.get('ohne_gesicht', 0)} without a face, "
                     f"{summe.get('unlesbar', 0)} not readable, "
                     f"{summe.get('unvollstaendig', 0)} partly readable, "
                     f"{summe.get('fehler', 0)} errors")
            self.lernlauf_anker_starten()      # E3: Auto-Kette Ernte -> Anker (wie Vorbereitung -> Ernte)
        except Exception as e:
            from core import lernlauf as _ll2
            _ll2.lauf_fortschreiben(dd, fortschritt={"status": f"harvest failed: {e}"})
            self.log(f"harvest failed ({type(e).__name__}: {e})")
        finally:
            if erworben:
                with self._sammel_lock:
                    nachhol = self._sammel_nachhol
                    self._sammel_nachhol = False
                    self._sammel_laeuft = False
                self.log("harvest done: auto-collection resumed")
                if nachhol:
                    self._szenario_nachsammeln()

    # ---------------------------------------------------------- Enrollment (Plan AP4)
    @property
    def embedder(self):
        if self._emb is None:
            os.environ.setdefault("OV_DEVICE", self.cfg["ov_device"])
            from face_audit import Embedder
            self._emb = Embedder()                # det 320: Referenzbild-Groessen (Reihenfolge-Falle!)
        return self._emb

    def _enroll_queue_pfad(self):
        return os.path.join(self.cfg["data_dir"], "learn", "enroll", "queue.jsonl")

    def _enroll_queue(self):
        """Queue lesen: letzte Zeile pro id gewinnt (append-only Status-Updates)."""
        q = {}
        p = self._enroll_queue_pfad()
        if os.path.exists(p):
            with open(p) as f:
                for l in f:
                    try:
                        d = json.loads(l)
                        q[d["id"]] = d
                    except Exception:
                        pass
        return q

    def _enroll_append(self, d):
        with open(self._enroll_queue_pfad(), "a") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
            f.flush()

    def _enroll_uebernehmen(self, eid, event_dir, camera):
        """Kandidaten aus analyze (kandidaten.jsonl) in die Queue — mit Tages-Drossel
        (max 3/Person) und Fremd-Wiedervorlage (Embedding-Abgleich gegen Abgelehnte)."""
        kp = os.path.join(event_dir, "kandidaten.jsonl")
        if not os.path.exists(kp):
            return
        q = self._enroll_queue()
        heute0 = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        pro_person = collections.Counter(d.get("person") or "FREMD" for d in q.values()
                                         if d.get("ts", 0) >= heute0)
        abgelehnt = []
        ab_p = os.path.join(self.cfg["data_dir"], "learn", "enroll", "abgelehnt_fremde.jsonl")
        if os.path.exists(ab_p):
            with open(ab_p) as f:
                for l in f:
                    try:
                        abgelehnt.append(json.loads(l)["emb"])
                    except Exception:
                        pass
        with open(kp) as f:
            for l in f:
                try:
                    kd = json.loads(l)
                except Exception:
                    continue
                kid = f"{eid}:{kd.get('person') or 'FREMD'}:{kd.get('t')}"
                if kid in q:
                    continue
                schluessel = kd.get("person") or "FREMD"
                if pro_person[schluessel] >= 3:
                    continue                      # Tages-Drossel
                if not kd.get("person") and abgelehnt and kd.get("emb"):
                    import numpy as np
                    v = np.asarray(kd["emb"], dtype=np.float32)
                    A = np.asarray(abgelehnt, dtype=np.float32)
                    if float((A @ v).max()) > 0.5:
                        continue                  # derselbe abgelehnte Fremde — keine Wiedervorlage
                pro_person[schluessel] += 1
                self._enroll_append({"id": kid, "ts": round(time.time(), 1), "eid": eid,
                                     "camera": camera, "person": kd.get("person"),
                                     "score": kd.get("score"), "nn_eigen": kd.get("nn_eigen"),
                                     "front": kd.get("front"), "sharp": kd.get("sharp"),
                                     "bw": kd.get("bw"), "bh": kd.get("bh"),
                                     "datei": kd.get("datei"), "emb": kd.get("emb"),
                                     "status": "offen"})
                self.log(f"{eid}: enrollment suggestion ({schluessel}, score {kd.get('score')})")

    def enroll_entscheiden(self, kid, aktion, person=None):
        """UI-Entscheidung: aufnehmen (in Master + Export + Drift-Waechter) oder ablehnen."""
        q = self._enroll_queue()
        d = q.get(kid)
        if not d or d.get("status") != "offen":
            return False, "Vorschlag unbekannt oder schon entschieden"
        if aktion == "ablehnen":
            if not d.get("person") and d.get("emb"):
                with open(os.path.join(self.cfg["data_dir"], "learn", "enroll", "abgelehnt_fremde.jsonl"), "a") as f:
                    f.write(json.dumps({"ts": round(time.time(), 1), "emb": d["emb"]}) + "\n")
            self._enroll_append({**d, "status": "abgelehnt", "ts_entschieden": round(time.time(), 1)})
            return True, "abgelehnt"
        ziel_person = person or d.get("person")
        if not ziel_person or not re.fullmatch(_reg.PERSON_RE, ziel_person):
            return False, "ungueltiger Personenname"
        quelle = os.path.join(self.cfg["data_dir"], "events", d["eid"].replace("/", "_"), d["datei"])
        if not os.path.isfile(quelle):
            return False, "Kandidaten-Crop nicht mehr vorhanden"
        ziel_dir = os.path.join(self.cfg["data_dir"], "faces", ziel_person)
        os.makedirs(ziel_dir, exist_ok=True)
        ziel_name = f"enroll_{int(time.time())}_{re.sub(r'[^\w.-]', '_', d['datei'])[-40:]}"
        import shutil
        shutil.copyfile(quelle, os.path.join(ziel_dir, ziel_name))
        with open(os.path.join(self.cfg["data_dir"], "faces", "refs_meta.jsonl"), "a") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "person": ziel_person,
                                "datei": ziel_name, "herkunft": "enrollment",
                                "eid": d["eid"], "aktiv": True}, ensure_ascii=False) + "\n")
            f.flush()
        try:
            os.remove(os.path.join(self.cfg["data_dir"], "clips", "refcache.npz"))
        except FileNotFoundError:
            pass                                  # naechster Analyse-Lauf baut mit neuem Master
        self._enroll_append({**d, "status": "aufgenommen", "als": ziel_person,
                             "ts_entschieden": round(time.time(), 1)})
        self.log(f"ENROLLMENT: {d['datei']} -> master/{ziel_person}/ (export + drift watchdog running)")
        self.referenz_nacharbeit()
        return True, f"aufgenommen als {ziel_person}"

    def referenz_nacharbeit(self):
        """Gemeinsame Nacharbeit nach JEDER Referenz-Aenderung — Pool-Enrollment UND
        E4b-Uebernahme (E4b haette den Block sonst dupliziert): optionaler
        Frigate-Export mit read-only-Riegel + Drift-Waechter; Ergebnis landet in
        enroll_warnung (System-Seite) und im Log. Ein Daemon-Thread je Aufruf."""
        def nacharbeit():
            env = dict(os.environ, OV_DEVICE=self.cfg["ov_device"])
            # Derselbe Riegel wie an den anderen beiden sync-Stellen (Fund der Vor-Release-
            # Pruefung 25.07.): dieser Pfad war der EINZIGE, der frigate_read_only NICHT prueft —
            # ein Betreiber, der auf read-only stellt, waere nach einem Enrollment trotzdem
            # beschrieben worden, still und mit check=False. Zusaetzlich vorab pruefen, ob
            if self.cfg.get("frigate_sync") and not frigate_read_only(self.cfg):
                if getattr(self, "_sync_job_aktiv", False):
                    # .134 Lauf-Riegel: manueller Sync laeuft — Runde auslassen.
                    self.log("frigate_sync: a manual sync is running — post-enrollment export skipped")
                else:
                    self._sync_job_aktiv = True
                    try:
                        # API-Export (0.1.0.108): keine ssh/scp-Vorbedingung mehr, nur eine URL.
                        # --force: read-only wurde eben mit voller Config geprueft (.132).
                        r = subprocess.run([sys.executable,
                                            os.path.join(HERE, "sync_refs.py"), "export", "--force"],
                                           capture_output=True, timeout=300, check=False, env=env)
                        if r.returncode != 0:    # Fehler NIE still verschlucken (Klasse C)
                            self.log(f"frigate_sync: reference export failed (rc={r.returncode}): "
                                     f"{fehler_kern(r.stderr)}")
                    finally:
                        self._sync_job_aktiv = False
            r = subprocess.run([sys.executable,
                                os.path.join(HERE, "abnahme.py"), "--nach-enrollment"],
                               capture_output=True, timeout=900, check=False, env=env,
                               preexec_fn=_analyse_nice)   # Issue #21, s. ANALYSE_NICE
            if r.returncode == 0:
                self.enroll_warnung = None
                self.log("drift watchdog GREEN after enrollment")
            else:
                # stderr MIT aufnehmen (Fund 25.07.): auf Prod starb abnahme.py mangels
                # Fixture sofort mit Traceback auf STDERR — der Banner zeigte ROT mit leerem
                # Text. Eine Warnung ohne Grund ist nicht pruefbar und erzieht zum Wegklicken.
                _txt = ((r.stdout or b"") + b"\n" + (r.stderr or b"")).decode(errors="replace").strip()
                self.enroll_warnung = (time.time(), _txt[-400:])
                self.log("DRIFT WATCHDOG RED after enrollment — check the reference! (System page)")
        threading.Thread(target=nacharbeit, daemon=True).start()

    def upload_referenz(self, person, daten):
        """Eigenes Foto in den Master (AP4): Gate-Pruefung mit Lazy-Embedder;
        Gate-Fail liefert Warnung, Aufnahme nur mit override=1."""
        import cv2
        import numpy as np
        arr = cv2.imdecode(np.frombuffer(daten, np.uint8), cv2.IMREAD_COLOR)
        if arr is None:
            return False, "Bild nicht lesbar (JPEG/PNG?)"
        override = person.endswith("!")            # 'Name!' = Gate-Override (UI setzt das bewusst)
        person = person.rstrip("!")
        if self.embedder.embed(arr) is None and not override:
            return False, "GATE: kein Gesicht fuer buffalo_l erkennbar — Override moeglich"
        ziel_dir = os.path.join(self.cfg["data_dir"], "faces", person)
        os.makedirs(ziel_dir, exist_ok=True)
        name = f"upload_{int(time.time())}.jpg"
        ok, enc = cv2.imencode(".jpg", arr)
        if not ok:
            return False, "Konvertierung fehlgeschlagen"
        with open(os.path.join(ziel_dir, name), "wb") as f:
            f.write(enc.tobytes())
        with open(os.path.join(self.cfg["data_dir"], "faces", "refs_meta.jsonl"), "a") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "person": person, "datei": name,
                                "herkunft": "upload", "aktiv": True}, ensure_ascii=False) + "\n")
            f.flush()
        try:
            os.remove(os.path.join(self.cfg["data_dir"], "clips", "refcache.npz"))
        except FileNotFoundError:
            pass
        self.log(f"UPLOAD: {person}/{name} into the master")
        return True, f"{name} aufgenommen (Export beim naechsten sync/Enrollment)"

    def _crop_je_person(self, event_dir, personen):
        """Je gemeldeter Person EIN Anzeigebild, in der uebergebenen Reihenfolge.
        _show_ zuerst (Gesicht mit Umfeld), sonst der enge _best_-Ausschnitt."""
        jpgs = [c for c in os.listdir(event_dir) if c.endswith(".jpg")]
        treffer = []
        for p in personen:
            for pref in (f"_show_{p}_", f"_best_{p}_NN"):
                fund = next((c for c in jpgs if pref in c), None)
                if fund:
                    treffer.append((p, os.path.join(event_dir, fund)))
                    break
        return treffer

    def _best_crop(self, event_dir, entry, personen):
        """Push-Bild. EINE Person: ihr Anzeigebild. MEHRERE: eine Collage aus allen,
        weil eine Meldung ueber zwei Personen auch zwei Gesichter zeigen soll (User 25.07.:
        "wenn drei Personen erkannt worden sind, eben drei, dann zwei nebeneinander,
        eines darunter"). Raster: ceil(sqrt(n)) Spalten — 2 nebeneinander, 3 als 2+1,
        4 als 2x2. Jede Zelle wird auf dieselbe Groesse gebracht und mit Rand aufgefuellt
        statt verzerrt; die Zielflaeche ist 4:3, damit Pushover nichts wegschneidet.

        Rangfolge wie bisher: die am besten erkannte Person zuerst (Fund 16.07.: vorher ging
        stumpf die groesste Datei raus, das war ein schwaches Crop 0.19 statt eines starken 0.52)."""
        rang = sorted(personen, key=lambda p: -((entry["ours"].get(p) or {}).get("max") or 0))
        treffer = self._crop_je_person(event_dir, rang)
        if not treffer:
            jpgs = [os.path.join(event_dir, c) for c in os.listdir(event_dir) if c.endswith(".jpg")]
            return max(jpgs, key=os.path.getsize) if jpgs else None
        if len(treffer) == 1:
            return treffer[0][1]
        try:
            import cv2, numpy as np
            bilder = [b for b in (cv2.imread(p) for _, p in treffer) if b is not None and b.size]
            if len(bilder) < 2:
                return treffer[0][1]
            spalten = math.ceil(math.sqrt(len(bilder)))
            zeilen = math.ceil(len(bilder) / spalten)
            # Zellformat so waehlen, dass die GESAMTflaeche 4:3 ergibt — sonst ist das fertige
            # Bild bei zwei Personen 2,67 breit und Pushover legt oben und unten Balken an
            # (derselbe Fehler wie vorher seitlich, nur um 90 Grad gedreht).
            # n=2 -> hochkantige Zellen (2:3), n=3/4 -> 4:3-Zellen. Passt beides zu Gesichtern.
            zell_ar = (4 / 3) * zeilen / spalten
            zh = 420
            zw = max(1, int(zh * zell_ar))
            grund = (24, 26, 32)                        # dunkler Fond wie die UI, nicht schwarz
            leinwand = np.full((zeilen * zh, spalten * zw, 3), grund, np.uint8)
            for i, b in enumerate(bilder):
                s = min(zw / b.shape[1], zh / b.shape[0])          # einpassen, NICHT verzerren
                nb = cv2.resize(b, (max(1, int(b.shape[1] * s)), max(1, int(b.shape[0] * s))),
                                interpolation=cv2.INTER_AREA)
                r, c = divmod(i, spalten)
                # Letzte Reihe zentrieren: bei drei Personen soll das dritte Bild MITTIG unter
                # den beiden stehen, nicht linksbuendig (User 25.07.: "zwei nebeneinander,
                # eines darunter").
                in_reihe = min(spalten, len(bilder) - r * spalten)
                rand = (spalten - in_reihe) * zw // 2
                y = r * zh + (zh - nb.shape[0]) // 2
                x = rand + c * zw + (zw - nb.shape[1]) // 2
                leinwand[y:y + nb.shape[0], x:x + nb.shape[1]] = nb
            # Selbst kodieren statt cv2.imwrite: OpenCV bestimmt das Format an der DATEIENDUNG,
            # und eine tmp-Datei auf ".tmp-1234" hat keine — imwrite scheitert dann mit
            # "could not find a writer for the specified extension" (Fund beim Test 25.07.).
            # Bytes schreiben passt ausserdem zum atomaren Muster aus Welle 3.
            ok, puffer = cv2.imencode(".jpg", leinwand, [cv2.IMWRITE_JPEG_QUALITY, 88])
            if not ok:
                raise RuntimeError("imencode lieferte False")
            ziel = os.path.join(event_dir, "_push_collage.jpg")
            tmp = f"{ziel}.tmp-{os.getpid()}-{threading.get_ident()}"
            with open(tmp, "wb") as fh:
                fh.write(puffer.tobytes())
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, ziel)
            return ziel
        except Exception as e:
            # Eine misslungene Montage darf die MELDUNG nicht kosten — dann eben ein Bild.
            self.log(f"push collage failed ({len(treffer)} persons): {e}")
            return treffer[0][1]

    def log(self, msg):
        line = f"[{datetime.datetime.now():%d.%m %H:%M:%S}] {msg}"
        print(line, flush=True)
        self.logbuf.append(line)

    def debug(self, msg):
        """DEBUG-Log: nur wenn cfg['debug'] gesetzt. Geht ueber log() (stdout + /log-Ringpuffer)
        mit [dbg]-Prefix, damit man die Tiefe zur Laufzeit ein-/ausschalten kann, ohne INFO
        zuzumuellen. Aktiviert wird ueber Settings (Whitelist-Key 'debug') oder die yaml."""
        if self.cfg.get("debug"):
            self.log(f"[dbg] {msg}")

    def process(self, eid, nachhol=0, koerper=False):
        """nachhol=N (N>=1): Wiederholung einer frueher mit 'fehler' geendeten Analyse.
        Ein Nachhol-Lauf ist STUMM (kein Alert/Push/Telegram/MQTT, s. _nachhol_runde) und
        fasst die Live-Gesundheitssignale nicht an — er repariert nur die Akte.
        koerper=True (nur .161-Nachanalyse): derselbe stumme Weg, aber der Koerper-Strang
        laeuft mit, weil NUR er die beurteilten Bilder in den Kontroll-Speicher legt."""
        cfg = self.cfg
        with self.lock:                                   # ein Event nach dem anderen (GPU)
            if eid in self.processed and not nachhol:     # Nachhol darf den Guard passieren, OHNE
                return None                               # self.processed zu manipulieren (kein Race
            if not nachhol:                               # mit Sweep/MQTT-Redelivery)
                self.letzte_aktivitaet = time.time()      # Retry beruhigt den Stoerungswaechter NICHT
            try:
                ev = api(cfg, f"/api/events/{eid}")
                if not nachhol:                           # ein 404 auf ein 3 Tage altes Event ist kein
                    self.frigate_fehler = None            # Frigate-Ausfall, und ein geglueckter Retry
                    self.frigate_fehlerserie = 0          # darf keine echte Fehlerserie loeschen
            except Exception as e:
                if not nachhol:
                    self.frigate_fehler = (time.time(), f"event fetch: {e}")
                    self.frigate_fehlerserie = getattr(self, "frigate_fehlerserie", 0) + 1
                self.log(f"{eid}: Frigate fetch failed: {e} (no processed entry, sweep will catch up)")
                return None
            camera = ev.get("camera", "?")
            eigen = eid in self.own_writes          # Echo-Freiheit: unser eigenes Label ist
            f_label = None if eigen else (ev.get("sub_label") or None)   # keine Frigate-Wahrheit
            f_score = None if eigen else (ev.get("data") or {}).get("sub_label_score")
            # S2-Backtest-Fund (ROT, 28.07.): fuer no_person zaehlt Frigates OBJEKT-Score
            # (data.top_score/score, in 2228/2234 Events vorhanden), NICHT der sub_label_score
            # (nur 77/2234, davon 0 mit faces==0 — S1 und S3 schlossen sich strukturell aus).
            _d = ev.get("data") or {}
            obj_score = _d.get("top_score", _d.get("score", ev.get("top_score")))
            kc = (cfg.get("kameras") or {}).get(camera)     # Kamera-Blatt (Phase 2b) hat Vorrang
            if isinstance(kc, dict):                         # malformierte Config -> sicherer Fallback
                # verwenden=False unterdrueckt nur die Entdeckung neuer Gesichter; Frigates EIGENE
                # Behauptung (sub_label) wird IMMER geprueft (Fremder->Bekannt-Fehlmatch, wie beim Zonen-
                # Filter). Review 21.07.: ohne "and not f_label" verlor "aus" dieses Sicherheitsnetz.
                if not kc.get("verwenden", True) and not f_label:
                    self.processed.add(eid)
                    self.log(f"{eid} ({camera}): skipped (camera off, no sub_label)")
                    return None
                z = kc.get("zonen")                          # gegen handeditierte String-Zonen haerten
                zonen = z if isinstance(z, list) else ([z] if isinstance(z, str) and z else [])
                if zonen and not f_label and not set(ev.get("zones") or []) & set(zonen):
                    self.processed.add(eid)
                    self.log(f"{eid} ({camera}): skipped (not in a selected zone, no sub_label)")
                    return None
            else:                                           # Fallback: altes required_zones-Verhalten
                rz = (cfg.get("required_zones") or {}).get(camera)
                if rz and not f_label and not set(ev.get("zones") or []) & set(rz):
                    self.processed.add(eid)  # nur in-memory, kein deckung-Eintrag; nach Neustart
                    self.log(f"{eid} ({camera}): skipped (no required_zone, no sub_label)")
                    return None              # prueft der Sweep das billig erneut (nur API-Call)
            persons = master_persons(cfg)    # AP1: aus dem Master, nicht mehr /api/faces
            if not persons:
                self.log(f"{eid}: reference master empty — sync_refs.py import needed (no processed entry)")
                return None
            event_dir = os.path.join(cfg["data_dir"], "events", eid.replace("/", "_"))
            os.makedirs(event_dir, exist_ok=True)
            self.log(f"{eid} ({camera}, Frigate={f_label} {f_score}): analysis running ...")
            # Ketten-Schalter (Issue #21): Stufe EINMAL je Lauf lesen. "aus"
            # ueberspringt den Koerper-Strang an der QUELLE (kein --koerper im
            # Job -> analyze sammelt keine Crops, unten startet kein Urteil).
            # EINE laute Zeile je Lauf — und nur, wenn der Strang sonst
            # gelaufen waere (Modell scharf); sonst waere die Zeile Rauschen.
            kette_person = self.kette_stufe("person")
            _koerper_will = (not nachhol and self._koerper_scharf())
            if _koerper_will and kette_person == "aus":
                self.log(f"{eid}: person path off (person_pfad=aus) — no body "
                         f"crops collected, no person judgment started")
            t0 = time.time()
            # Nachbesserung W7: run_analyze meldet ueber `info`, wie lange der
            # Job am Analyse-Slot WARTETE (Ernte/Sammle/Wanduhr-Roundtrip halten
            # ihn teils minutenlang). Die Wartezeit faellt aus dauer_s heraus —
            # dauer_s traegt sonst erfundene Analysedauer in die Events-/Today-
            # Anzeige, in den Szenario-Ende-Rueckfall (dort gemessen: 42/103
            # Durchgaenge kippen bei 5x-Analysezeit) und in die Watchdog-Logzeilen.
            _ainfo = {}
            res = run_analyze(cfg, eid, camera, persons, event_dir,
                              timeout_s=(int(cfg["nachhol_analyse_timeout_s"]) if nachhol else None),
                              worker=self._worker(),
                              # Z5: EINMAL vor dem Job entschieden — waehrend
                              # der Analyse ist der Scharf-Zustand nicht mehr
                              # abfragbar (anderer Prozess). Nur Live-Laeufe:
                              # nur sie rufen unten _person_live.
                              koerper=(_koerper_will and kette_person != "aus"),
                              info=_ainfo)
            _warte_s = float(_ainfo.get("wartezeit_s") or 0.0)
            # P1: Provider-Guard-Vorfaelle aus dem Subprozess ins DIENST-Log heben —
            # analyze.log liest sonst niemand, und ein degradierter Lauf bliebe unsichtbar
            # (Plan-QS Lens3-8). qs S4 warnt auf den Marker.
            try:
                with open(os.path.join(event_dir, "analyze.log")) as _gf:
                    _gt = _gf.read()
                if "PROVIDER-GUARD" in _gt:
                    self.log(f"{eid}: PROVIDER-GUARD tripped in analyze "
                             f"({'NOT healed' if 'PROVIDER-GUARD FAILED' in _gt else 'healed'}) "
                             f"— see analyze.log")
                # P4: Placement-Rueckfall (NPU band nicht -> Kette) ebenso heben — qs S4 warnt.
                if "PLACEMENT-FALLBACK" in _gt:
                    self.log(f"{eid}: PLACEMENT-FALLBACK in analyze — requested device did "
                             f"not bind, chain took over — see analyze.log")
            except Exception:
                pass
            # W1/E1 (User 26.07.): unter der Haelfte lesbarer Frames traegt kein Teilurteil
            # mehr — wie ein Analysefehler behandeln (stumm; der Nachhol-Lauf versucht es mit
            # seinem Versuchsbudget erneut). Darueber: Teilurteil MIT sichtbarem Flag.
            _fg = (res or {}).get("frames_gelesen")
            _fs = (res or {}).get("frames_soll")
            if res is not None and _fs and _fg is not None and _fg * 2 < _fs:
                self.log(f"{eid}: clip only {_fg}/{_fs} frames readable (<50%) — "
                         f"treated as analysis failure")
                res = None
            ours = (res or {}).get("persons", {})
            max_bw = (res or {}).get("max_bw", 0)
            if res is None:      # analyze gescheitert -> nicht als "unknown" fehlwerten/alerten
                kategorie = kategorie_v1 = "fehler"
                confirmed = []
            else:
                kategorie, confirmed = verdict_v2(cfg, ours, max_bw)
                kategorie_v1, _ = verdict(cfg, f_label, ours)
                if kategorie in ("fremd_verdacht", "unbekannt_schwach"):
                    # S2 no_person (deklarierte I1-Ausnahme, Masterbauplan §5.2): EIN
                    # Eingriff am Urteilspunkt, Logik in no_person.py. Greift nur mit
                    # kalibrierten np_*-Schwellen (Retro-Backtest), sonst inert. Folge-
                    # Wirkungen (kein Fremd-Alarm, kein Unbekannt-Pool) entstehen dadurch,
                    # dass der fremd_verdacht-Zweig unten nicht mehr betreten wird.
                    if self._no_person_pruefen(eid, ev, res, obj_score):
                        kategorie = "no_person"
            # SD4 Fehlerserien-Waechter (qs.md §offen, qs_ebenen.md Paket 1): der 22.07.-Ausfall
            # blieb 9 h unbemerkt, weil Startup//health gruen blieben. Drei gescheiterte Analysen
            # IN FOLGE sind ein Struktursignal (Backend/Decode tot), kein Einzelfall-Rauschen ->
            # SOFORT melden (nicht erst im 10-min-Watchdog-Takt), je 6 h hoechstens einmal.
            # Widerleger-MUSS 31.07.: NUR der Live-Pfad zaehlt UND setzt zurueck — Nachhol-Laeufe
            # sind per Vertrag stumm ("retries are silent") und ein geglueckter Retry darf eine
            # echte Live-Serie nicht loeschen. Serien-Fenster 1 h: drei Einzelfehler ueber Tage
            # sind KEINE Serie (Anlagen mit wenig Verkehr). >=3 statt ==3: eine ANHALTENDE
            # Stoerung meldet nach Cooldown erneut statt genau einmal im Prozess-Leben.
            if not nachhol:
                if kategorie == "fehler":
                    jetzt_ts = time.time()
                    if jetzt_ts - getattr(self, "_fehlerserie_start", 0) > 3600:
                        self._fehlerserie = 0                  # alte Serie verjaehrt
                    if getattr(self, "_fehlerserie", 0) == 0:
                        self._fehlerserie_start = jetzt_ts
                    self._fehlerserie = getattr(self, "_fehlerserie", 0) + 1
                    if self._fehlerserie >= 3 and \
                            jetzt_ts - getattr(self, "_fehlerserie_gemeldet", 0) > 6 * 3600:
                        self._fehlerserie_gemeldet = jetzt_ts
                        self.log("STOERUNG (analyse-serie): 3 Analysen in Folge fehlgeschlagen — "
                                 "Erkennung moeglicherweise tot (Backend/Decode pruefen)")
                        if not self.dry_alert:
                            def _sd4_push():
                                # eigener Thread: 20-s-HTTP darf den Analyse-Lock nicht halten
                                for _f in stoerung_melden(
                                        self.cfg, "3 Analysen in Folge fehlgeschlagen — die "
                                        "Erkennung ist moeglicherweise tot (Dienst-Log / "
                                        "System-Seite pruefen)."):
                                    self.log(f"fault notify failed: {_f}")
                            threading.Thread(target=_sd4_push, daemon=True).start()
                else:
                    self._fehlerserie = 0
            entry = {
                # Schema 3 (W1): +frames_gelesen/+frames_soll/+frames_fehlen — Leser greifen
                # ueber .get() zu, Schema-2-Bestandszeilen bleiben unveraendert lesbar.
                "schema": 3, "ts": round(time.time(), 1), "eid": eid, "camera": camera,
                "start": ev.get("start_time"), "faces": (res or {}).get("faces", 0),
                # #42 Teil B, additiv + nur vorwaerts: gefilterte Gesichtszahl (Leser:
                # .get("faces_geprueft", .get("faces")) — Bestandszeilen behalten faces).
                **({"faces_geprueft": res["faces_geprueft"]}
                   if res is not None and "faces_geprueft" in res else {}),
                "max_bw": max_bw,
                "frames_gelesen": _fg, "frames_soll": _fs,
                **({"frames_fehlen": True} if (res or {}).get("frames_fehlen") else {}),
                "frigate": {"label": f_label, "score": f_score, "cos": frigate_to_cos(f_score),
                            # additiv, nur vorwaerts (S2-Fund): Objekt-Score fuer no_person —
                            # Altzeilen ohne das Feld sind un-klassifizierbar (Sicherheits-Semantik)
                            **({"obj_score": obj_score} if obj_score is not None else {}),
                            **({"eigen": True} if eigen else {})},
                "ours": {p: {"max": r.get("max"), "win3s": r.get("win3s")} for p, r in ours.items()},
                "bestaetigt": confirmed, "kategorie": kategorie, "kategorie_v1": kategorie_v1,
                # W7: reine Analysezeit — die Wartezeit am Analyse-Slot ist abgezogen
                # und steht (wenn nennenswert) separat als warte_s daneben, additiv.
                "dauer_s": round(max(0.0, time.time() - t0 - _warte_s), 1),
                **({"warte_s": round(_warte_s, 1)} if _warte_s >= 0.1 else {}),
                "alerted": False,
                # Paket A (0.1.0.48, Today-QS F1): das ECHTE Event-Ende aus Frigate — die
                # Szenario-Gruppierung rechnete das Ende bisher aus der ANALYSE-Wanduhr
                # (dauer_s), wodurch derselbe Tag auf schneller/langsamer Hardware anders
                # geschnitten wurde (gemessen: 42/103 Durchgaenge kippen bei 5x-Analysezeit).
                # Additiv + nur wenn Frigate es liefert (der Sweep wartet ohnehin auf
                # end_time); Alt-Zeilen ohne das Feld behalten den dauer_s-Fallback.
                **({"ende_ts": float(ev["end_time"])} if ev.get("end_time") else {}),
                **({"nachhol": nachhol} if nachhol else {}),   # nur auf Retry-Zeilen
            }
            # STUMM bei Nachhol: die Drosseln sind GLOBAL (alert_cooldown 300s, telegram_cooldown
            # 600s) und die Szenen-Karenz kann fuer ein altes Event nicht mehr entschaerfen
            # (last_seen haelt nur den juengsten ts). Ein nachgeholter Alarm waere meist falsch UND
            # wuerde die Drossel fuer einen echten Live-Alarm verbrennen.
            entry["alerted"] = False if nachhol else self._maybe_alert(entry, event_dir)
            entry["presence_push"] = False if nachhol else self._maybe_presence(entry, event_dir)
            entry["sublabel"] = self._maybe_sublabel(entry, nachhol=nachhol)
            if not nachhol:
                self.publish_erkennung(entry)     # kein Live-Echo fuer alte Ereignisse
                # PE4 (stufe2.md): Koerper-Strang — eigener, losgeloester
                # Urteilsweg, nur wenn der User ihn scharf geschaltet hat;
                # laeuft im Daemon-Thread, blockiert den Gesichts-Pfad nie.
                # Ketten-Schalter davor (Issue #21): "aus" wurde schon VOR der
                # Analyse laut uebersprungen (eine Zeile je Lauf, steht oben);
                # "nur_wenn_gesicht_leer" laesst das teure Urteil (Embedding)
                # nur an, wenn der Gesichts-Weg den DURCHGANG nicht restlos
                # bestaetigt hat (Mehr-Personen-Regel B, s. Helfer).
                # Modulumbau R2: der Stufen-Entscheid faellt in core/kette.
                # Das Pass-Urteil kommt lazy (nur "nur_wenn_gesicht_leer"
                # wertet es aus) und in der ALTEN Reihenfolge: erst
                # Scharf-Frage, dann Pass-Urteil.
                _p_urteil = _kette.entscheide(
                    kette_person,
                    lambda: self._koerper_scharf()
                    and self._gesicht_pass_bestaetigt(eid=eid, entry=entry))
                if _p_urteil == "aus":
                    pass
                elif _p_urteil == "gesicht_bestaetigt":
                    self.log(f"{eid}: person judgment skipped — face path "
                             f"confirmed the whole pass "
                             f"(person_pfad=nur_wenn_gesicht_leer)")
                else:
                    self._person_live(entry.get("eid"), entry)
                # V4 (konzept_vision.md §7): dritter Weg, Auslöser auf
                # PASS-Ebene und erst am Durchgangs-Ende (Debounce). Nur ein
                # Timer-Start, keine Arbeit, kein Lock — die Analyse laeuft
                # unveraendert weiter.
                self._vision_anstossen(entry.get("eid"), entry)
            elif koerper:
                # .161: Nachanalyse AUF WUNSCH eines Durchgangs. Sie faehrt den
                # bestehenden Nachhol-Weg (stumm, keine Alarme, kein Live-Echo,
                # kurzer Timeout) — mit der EINEN Ausnahme, dass der
                # Koerper-Strang laufen darf: nur er legt die beurteilten Bilder
                # in den Kontroll-Speicher, und genau die fehlen dem Nutzer.
                # Vision wird bewusst NICHT angestossen: der Nutzer entscheidet
                # selbst, wann er den (kostenpflichtigen) Lauf startet.
                # still=True (.163): NUR das Bild ablegen. Ohne diesen Schalter
                # meldete die Nachanalyse eines Durchgangs von gestern per
                # Telegram, als stuende die Person gerade vor der Tuer
                # (Live-Bug 09.08. 08:19).
                self._person_live(entry.get("eid"), entry, still=True)
            if entry["kategorie"] == "fremd_verdacht":
                # Auch OHNE nachhol-Flag kann ein Event alt sein (verspaetetes MQTT, Poll nach
                # kurzer Netzstoerung). Die Karenz haette dann karenz Sekunden spaeter einen
                # Alarm fuer einen laengst vergangenen Vorfall abgesetzt — gleiche Begruendung
                # wie oben beim Nachhol-Pfad, deshalb dieselbe 900s-Grenze wie _maybe_presence.
                if nachhol or time.time() - (entry.get("start") or entry["ts"]) > 900:
                    if not nachhol:
                        self.log(f"{eid}: fremd_verdacht without alarm — event older than 900 s "
                                 f"(unknown pool only)")
                    self._szenario_nachsammeln()  # Gesichter in den Unbekannt-Pool, aber KEIN Alarm
                else:
                    self._szene_unbekannt_pruefen(entry)
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f.flush()
            self.processed.add(eid)
            self.log(f"{eid}: {kategorie} [v1:{kategorie_v1}] (Frigate={f_label}, "
                     f"ours={confirmed or 'unknown'}, {entry['faces']} faces, {entry['dauer_s']}s)" +
                     (" -> ALERT" if entry["alerted"] else "") +
                     (f" -> SUBLABEL '{entry['sublabel']}'" if entry.get("sublabel") else ""))
            self.debug(f"{eid}: scores " + (", ".join(
                f"{p}=max{(r.get('max') or 0):.3f}/win{r.get('win3s') or 0}" for p, r in ours.items()) or "(no candidate)")
                + f" | gate win_thresh={cfg['win_thresh']} win_min={cfg['win_min']}"
                + f" faces={entry['faces']} max_bw={max_bw} dur={entry['dauer_s']}s")
            self.cleanup_cache()
            if kategorie != "fehler":
                # W3: Browser-Kopie NICHT mehr eifrig je Event (~1,35 CPU-h/Tag fuer kaum
                # angesehene Kopien) — sie entsteht lazy beim Klick (/video -> review_anfordern).
                self._enroll_uebernehmen(eid, event_dir, camera)
            return entry

    def _no_person_pruefen(self, eid, ev, res, obj_score):
        """S2 (konzept_no_person.md): prueft, ob der GANZE Durchgang um dieses Event
        beweisbar ohne Person ist — Szenario-Prinzip, nie aus einem Event allein.
        obj_score = Frigates OBJEKT-Score (data.top_score/score), NICHT sub_label_score
        (Backtest-Fund 28.07.); Siblings lesen frigate.obj_score (additiv seit .61).
        Schwellen NUR aus der Config (np_det_max/np_frigate_max, Retro-Backtest-
        kalibriert); fehlen sie, ist das Feature aus. Sicherheits-Semantik liefert
        no_person.klassifiziere (jede Datenluecke -> kein Urteil). Gruppierungs-Regel
        ist dieselbe Kette wie szenarien.szenarien_des_tages (szenario_gap_min).
        Ein Fehler hier darf NIE die Analyse reissen -> immer False im Zweifel."""
        cfg = self.cfg
        nd, nf = cfg.get("np_det_max"), cfg.get("np_frigate_max")
        if nd is None or nf is None or res is None:
            return False
        try:
            from no_person import klassifiziere
            gap = int(cfg.get("szenario_gap_min", 5)) * 60
            t0 = float(ev.get("start_time") or time.time())
            by_eid = {}
            try:
                with open(self.log_path) as f:
                    for ln in f:
                        try:
                            r = json.loads(ln)
                        except Exception:
                            continue
                        if r.get("eid"):
                            by_eid[r["eid"]] = r        # last-wins je eid (wie /heute)
            except FileNotFoundError:
                pass
            pseudo = {"eid": eid, "start": t0,
                      "ende_ts": float(ev["end_time"]) if ev.get("end_time") else t0}
            by_eid[eid] = pseudo
            alle = sorted(by_eid.values(), key=lambda r: (r.get("start") or r.get("ts") or 0))
            gruppen, cur = [], None
            for r in alle:
                ts = r.get("start") or r.get("ts") or 0
                ende = r.get("ende_ts") or (ts + (r.get("dauer_s") or 0)) or ts
                if cur and ts - cur["ende"] <= gap:      # dieselbe Regel wie szenarien.py
                    cur["evs"].append(r)
                    cur["ende"] = max(cur["ende"], ende)
                else:
                    cur = {"evs": [r], "ende": ende}
                    gruppen.append(cur)
            ziel = next((g for g in gruppen if any(x.get("eid") == eid for x in g["evs"])), None)
            if ziel is None:
                return False
            events = []
            for r in ziel["evs"]:
                reid = r.get("eid")
                if reid == eid:
                    events.append({"faces_geprueft": res.get("faces_geprueft"),
                                   "detektionen": res.get("detektionen"),
                                   "frigate_score": obj_score})
                    continue
                d = {"faces_geprueft": r.get("faces_geprueft"),
                     "frigate_score": (r.get("frigate") or {}).get("obj_score"),
                     "detektionen": None}
                rp = os.path.join(cfg["data_dir"], "events",
                                  str(reid).replace("/", "_"), "results.jsonl")
                try:
                    with open(rp) as f:
                        for ln in f:
                            try:
                                rr = json.loads(ln)
                            except Exception:
                                continue
                            if "detektionen" in rr:
                                d["detektionen"] = rr["detektionen"]
                except (FileNotFoundError, NotADirectoryError):
                    pass
                events.append(d)
            ist, beg = klassifiziere(events, np_det_max=nd, np_frigate_max=nf)
            if ist:
                self.log(f"{eid}: no_person — whole pass shows no usable person "
                         f"(faces=0, det_max={beg['s2_det_max']:.2f}, "
                         f"frigate_max={beg['s3_frigate_max']:.2f}, {len(events)} events)")
            return ist
        except Exception as e:
            self.log(f"{eid}: no_person check failed ({e}) — keeping original category")
            return False

    def _maybe_presence(self, entry, event_dir):
        """Anwesenheits-Push (User 16.07. abends): EIN Push pro Person und Erscheinen —
        'recognized people'. Zustandslogik nach Konzept §3: gemeldet wird nur, wer
        laenger als anwesenheit_cooldown nicht bestaetigt wurde; jeder Treffer verlaengert
        den Timer (Gartenarbeit spammt also nicht). Getrennt vom widerspruch-Alert."""
        cfg = self.cfg
        if not entry["bestaetigt"]:
            return False
        now = time.time()
        # Altes Event (Sweep/Replay nach Downtime): kein "erkannt"-Push fuer laengst Vergangenes
        # (AP2-Fix). Der Guard unterdrueckt aber NUR den Push — der Zustand wird trotzdem
        # nachgefuehrt. Vorher stand das return davor, dadurch blieb nach jeder Downtime
        # last_seen auf dem Stand VOR dem Ausfall: das erste Live-Event danach galt als
        # neues Auftauchen und pushte doppelt, und _nachlern_anstossen lief fuer den ganzen
        # nachgeholten Durchgang nie.
        alt = now - (entry.get("start") or entry["ts"]) > 900
        neu = [p for p in entry["bestaetigt"] if now - self.last_seen.get(p, 0) > cfg["anwesenheit_cooldown"]]
        for p in entry["bestaetigt"]:
            # EVENT-Zeit statt Verarbeitungszeit (Szenen-Fenster rechnet in Event-Zeit;
            # Sweep-Nachverarbeitung bleibt damit zeitlich konsistent)
            self.last_seen[p] = max(self.last_seen.get(p, 0), entry.get("start") or now)
            self._nachlern_anstossen(p)      # Bestands-Suche nach Durchgangs-Ende (Debounce, User 21.07.)
        if alt or not neu:
            return False
        # SZENEN-Ereignis (User 18.07. "szenenorientiert"): genau EIN Publish pro
        # Auftauchen (die anwesenheit_cooldown-Ruhe definiert die Szene) — unabhaengig
        # vom Pushover-Schalter; die HA-Telegram-Automation haengt hieran.
        # Areas Stufe 1: Area-Namen in Payload (additiv) + Log + Push-Text; Verhalten gleich.
        _ar = _areas_mod.kamera_areas(_areas_mod.normalisieren(cfg.get("areas")), entry["camera"])
        if self._mqtt_pub(_melden.topic(self.cfg, "szene_erkannt"), json.dumps(
                {"eid": entry["eid"], "camera": entry["camera"], "areas": _ar,
                 "ts": entry.get("start") or entry["ts"],         # Vorfalls-Zeit fuer die Caption
                 "personen": [{"name": p,
                               "cos": (entry["ours"].get(p) or {}).get("max"),
                               "win": (entry["ours"].get(p) or {}).get("win3s")} for p in neu]},
                ensure_ascii=False)):
            self.log(f"SCENE recognized: {' + '.join(neu)} ({entry['camera']}"
                     f"{' · ' + ' + '.join(_ar) if _ar else ''})")
        self._telegram_melden("erkannt", entry, neu)
        if not cfg["anwesenheit_push"] or entry.get("alerted"):
            return False
        t = datetime.datetime.fromtimestamp(entry.get("start") or entry["ts"]).strftime("%H:%M")
        msg = (f"{' + '.join(neu)} erkannt ({entry['camera']}"
               f"{' · ' + ' + '.join(_ar) if _ar else ''}, {t})")
        if self.dry_alert:
            self.log(f"DRY-PRESENCE: {msg}")
            return False
        try:
            # push() liefert False, wenn Pushover die Nachricht ABLEHNT (status != 1, z.B.
            # falsches token/user). Ohne diese Pruefung stand "PRESENCE-PUSH" im Log und die
            # UI zeigte "gepusht", waehrend nie ein Push ankam.
            if not push(cfg, f"suslik: {KAT_LABELS['erkannt']}", msg, self._best_crop(event_dir, entry, neu)):
                self.log(f"presence push REJECTED by Pushover (status!=1) — check token/user: {msg}")
                return False
            self.log(f"PRESENCE-PUSH: {msg}")
            return True
        except Exception as e:
            self.log(f"presence push failed: {e}")
            return False

    def process_safe(self, eid, nachhol=0, koerper=False):
        """process() fuer Timer-/Sweep-Threads: Exception darf nie einen Thread still toeten."""
        try:
            self.process(eid, nachhol=nachhol, koerper=koerper)
        except Exception as e:
            self.log(f"{eid}: unexpected error in the processing thread: {e}")

    def review_anfordern(self, ed):
        """W3 Lazy: Browser-Kopie erst beim Klick bauen statt je Event (Recon: der eifrige Bau
        war ein ~1,35-CPU-h-Tagesposten fuer Kopien, die fast nie jemand ansieht). Startet den
        Bau EINMAL im Hintergrund (Doppelklick-/Reload-fest); die /video-Route pollt per
        Seiten-Refresh, bis die Kopie liegt (E8: Wartezeit mit Spinner akzeptiert)."""
        with self._review_lock:
            if ed in self._review_laeuft:
                return
            # W3-Review: Klick-Sturm-Kappe — hoechstens 3 wartende/laufende Baujobs. Der
            # Spinner-Refresh der abgewiesenen Seite versucht es alle 2 s erneut und rueckt
            # nach, sobald ein Platz frei ist (kein Fehler, nur Warteschlange).
            if len(self._review_laeuft) >= 3:
                return
            self._review_laeuft.add(ed)

        def lauf():
            try:
                with self._transcode_serial:      # W3-Review: EIN ffmpeg-Transcode gleichzeitig
                    self.make_browser_copy(ed)
                if not os.path.exists(os.path.join(self.cfg["data_dir"], "clips",
                                                   ed + "_review.mp4")):
                    with self._review_lock:       # Fehlschlag merken: Auto-Refresh darf den Bau
                        self._review_fehler[ed] = time.monotonic()   # nicht endlos neu anstossen
            except Exception as e:
                # W3-Review: OHNE dieses except stuerbe der Thread VOR dem Fehler-Marker —
                # und der Auto-Refresh wuerde den Bau alle 2 s endlos neu anstossen.
                self.log(f"{ed}: lazy browser copy error: {type(e).__name__}: {e}")
                with self._review_lock:
                    self._review_fehler[ed] = time.monotonic()
            finally:
                with self._review_lock:
                    self._review_laeuft.discard(ed)
        try:
            threading.Thread(target=lauf, daemon=True).start()
        except Exception as e:                    # Thread-Start-Fehler -> Flag nicht haengen lassen
            with self._review_lock:
                self._review_laeuft.discard(ed)
            self.log(f"{ed}: lazy browser copy thread start error: {e}")

    def make_browser_copy(self, eid):
        """1080p-H.264-Kopie des Clips (Kameras zeichnen HEVC auf, das spielt im Browser
        nicht). Encoder aus video_encoder() (NVENC/VAAPI geprobt, sonst CPU), Fallback bleibt
        CPU. Kopie altert mit der Cache-Retention. Seit W3 NICHT mehr je Event, sondern lazy
        ueber review_anfordern() (die /video-Route)."""
        base = os.path.join(self.cfg["data_dir"], "clips", eid.replace("/", "_"))
        src, dst = base + ".mp4", base + "_review.mp4"
        if not os.path.exists(src) or os.path.exists(dst):
            return
        # ffmpeg schreibt auf .part und wird erst bei Erfolg umbenannt: ein Timeout-Kill liess
        # sonst eine mp4 OHNE moov-Atom liegen, die der exists()-Guard oben dauerhaft als fertige
        # Kopie wertete -> im Browser ein ewig kaputtes Video, ohne Logzeile.
        # Eindeutiger .part-Name je Versuch (W3-Review: execv-Waise + Zweitbau teilten sich sonst
        # dieselbe Inode -> dauerhaft kaputte Kopie; endet auf .part -> Retention raeumt Waisen).
        # `-f mp4` steckt in transcode_kommandos() und ist ZWINGEND, weil der Zielname auf .part
        # endet (Fund 25.07.): ffmpeg leitet den Muxer aus der Dateiendung ab, kennt ".part" nicht
        # und bricht mit "Error opening output file … Invalid argument" ab (rc=234). Die .part-
        # Absicherung aus Welle 3 hat damit genau das erschlagen, was sie schuetzen sollte — im
        # Prod-Log 14x "Browser-Kopie fehlgeschlagen". Dasselbe Muster wie bei cv2.imwrite auf
        # einen .tmp-Namen: wer atomar schreibt, muss dem Werkzeug das Format sagen, weil der
        # Zwischenname keins mehr verraet.
        part = f"{dst}.{os.getpid()}-{threading.get_ident()}.part"
        # W3/Issue #4: q_hw 24->28 (NVENC wie VAAPI) — mit 24 war die 1080p-Kopie GROESSER als
        # ihr 4K-Quell-Clip (21,7 MB aus 16,45 MB); 28 ist auf NVENC SSIM-gemessen crf-23-Niveau,
        # und fuer Intel ist genau diese Stufe die ausdrueckliche Tester-Empfehlung (Issue #4). CPU unveraendert.
        # N8a-Gegenprobe 30.07.: full-hw-1080 liegt bei cq 28 ueberall <= CPU-Referenz
        # (eigene Clips -6/-28 %, Feldclip -0,4 %) -> bewusst DERSELBE Wert wie encode-only.
        hw, cpu = transcode_kommandos(src, part, 1080, 28, 23, q_vaapi=28, q_hw_voll=28)
        try:
            r = self._transcode_lauf(hw, 300) if hw else None
            if r is None or r.returncode != 0 or not os.path.exists(part):
                if r is not None:
                    # s. _telegram_clip: Laufzeit-Rueckfall HW->CPU nie still lassen (Review-Fund).
                    e1 = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
                    self.log(f"{eid}: HW transcode ({video_encoder()[0]}) failed "
                             f"(rc={r.returncode}) — CPU takes over: {e1[-1] if e1 else 'no stderr'}")
                r = self._transcode_lauf(cpu, 600)
            # rc des FALLBACKS wurde frueher verworfen: scheiterten beide Encoder, gab es keinerlei
            # Hinweis — die Kopie fehlte einfach.
            if r.returncode == 0 and os.path.exists(part) and os.path.getsize(part) > 0:
                os.replace(part, dst)
            else:
                err = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
                self.log(f"{eid}: browser copy failed (rc={r.returncode}): "
                         f"{' | '.join(err[-2:]) if err else 'no stderr output'}")
                try:
                    os.remove(part)
                except OSError:
                    pass
        except Exception as e:
            self.log(f"{eid}: browser copy failed: {e}")
            try:
                os.remove(part)
            except OSError:
                pass

    def clip_cache_bytes(self):
        """Aktuelle Groesse des Clip-Caches (nur .mp4/.part). Fuer /health + cleanup-Log —
        N8b (Issue #4): age-only-Eviction wurde erst am 97 % vollen Host bemerkt,
        WEIL die Groesse nirgends sichtbar war."""
        cache = os.path.join(self.cfg["data_dir"], "clips")
        try:
            return sum(os.path.getsize(os.path.join(cache, fn)) for fn in os.listdir(cache)
                       if fn.endswith((".mp4", ".part")))
        except OSError:
            return 0

    def cleanup_cache(self):
        """Record-Clips aelter clip_retention_d Tage loeschen (Crops/Logs/refcache bleiben;
        Frigate haelt die Aufnahme selbst vor, der Clip ist bei Bedarf erneut holbar).
        N8b (Issue #4): zusaetzlich Size-Cap clip_cache_max_gb — bei hoher Input-
        Bitrate (Feldbericht: ~10,5 GB/Tag -> ~74 GB steady) laeuft die Platte sonst voll,
        bevor die Alters-Eviction je greift. Aelteste zuerst, bis unter den Deckel."""
        try:
            cutoff = time.time() - self.cfg["clip_retention_d"] * 86400
            cache = os.path.join(self.cfg["data_dir"], "clips")
            gone = [fn for fn in os.listdir(cache)
                    if fn.endswith((".mp4", ".part")) and os.path.getmtime(os.path.join(cache, fn)) < cutoff]
            for fn in gone:
                os.remove(os.path.join(cache, fn))
            if gone:
                self.log(f"cache cleanup: {len(gone)} clips older than {self.cfg['clip_retention_d']}d deleted")
            cap = self.cfg["clip_cache_max_gb"] * 1024**3
            rest = []
            for fn in os.listdir(cache):
                if fn.endswith((".mp4", ".part")):
                    p = os.path.join(cache, fn)
                    try:
                        rest.append((os.path.getmtime(p), os.path.getsize(p), p))
                    except OSError:
                        pass
            gesamt = sum(r[1] for r in rest)
            if gesamt > cap:
                rest.sort()                                   # aelteste zuerst
                n = 0
                from core import frames as _fr
                for _, groesse, p in rest:
                    # Z1 (konzept_frames v2): GEPINNTE Clips haelt gerade
                    # ein Abnehmer (Refcount je Halter) — nie wegraeumen,
                    # sonst reisst der Size-Cap dem zweiten Halter die
                    # Datei unterm Urteil weg (Widerleger-MUSS 4).
                    if _fr.gepinnt(p):
                        continue
                    if gesamt <= cap:
                        break
                    try:
                        os.remove(p)
                        gesamt -= groesse
                        n += 1
                    except OSError:
                        pass
                self.log(f"cache cleanup: size cap {self.cfg['clip_cache_max_gb']} GB exceeded — "
                         f"{n} oldest clips deleted, now {gesamt / 1024**3:.1f} GB")
        except Exception as e:
            self.log(f"cache cleanup error: {e}")

    # Modulumbau R2: die Ketten-Praedikate leben in core/kette.py (Docstrings/
    # Begruendungen dort). Hier nur Einhaenge: der Dienst reicht cfg, den
    # deckung-Pfad und seinen debug-Kanal herein. core/kette haelt keine Locks
    # und keinen Zustand — die _deckung_korrektur-Invariante (deckung_by_eid
    # nimmt self.lock NICHT) gilt unveraendert.
    def _koerper_scharf(self):
        return _kette.koerper_scharf(self.cfg["data_dir"])

    def kette_stufe(self, weg):
        return _kette.stufe(self.cfg, weg)

    def kette_lage(self):
        return _kette.lage(self.cfg)

    def _deckung_by_eid(self, entry=None):
        return _kette.deckung_by_eid(self.log_path, entry)

    def _gesicht_pass_bestaetigt(self, eid=None, entry=None, pass_key=None):
        return _kette.gesicht_pass_bestaetigt(self.cfg, self.log_path, self.debug,
                                              eid=eid, entry=entry,
                                              pass_key=pass_key)

    def _kontroll_speicher(self, eid, entry=None):
        return _kette.kontroll_speicher(self.cfg, self.log_path, self.debug,
                                        eid, entry)


    def _person_live(self, eid, entry=None, still=False):
        """PE4: Koerper-Urteil im Hintergrund (core/personlive) — Meldung
        traegt die Kennzeichnung 'person recognition, not face'
        (User-Anforderung 04.08.). Kommt nur zum Zug, wenn der User den
        Strang auf /person/modell scharf geschaltet hat.

        `still=True` (Nachanalyse eines VERGANGENEN Durchgangs, .163): der Lauf
        legt nur das beurteilte Bild ab und schweigt danach vollstaendig. Die
        Sperre liegt ZWEIMAL: `plv.urteilen(still=True)` kann konstruktiv kein
        Melde-Objekt zurueckgeben, und dieser Mantel betritt den Melde-Block
        gar nicht erst. Zwei Ebenen, weil genau hier am 09.08. eine Funktion
        mit zwei Wirkungen scharf geschaltet und nur an eine gedacht wurde."""
        if not eid or not self._koerper_scharf():
            return
        import threading

        def lauf():
            try:
                self._person_lauf(eid, entry, still)
            finally:
                # W1b: Zaehler IMMER raeumen — sonst haelt ein einziger
                # Fehlerfall die Wanduhr-Messung fuer immer im Warten.
                with self._personlive_lock:
                    self._personlive_aktiv -= 1
        # W1b: Zaehler VOR dem Thread-Start erhoehen, noch UNTER self.lock des
        # Aufrufers — erst im Thread erhoeht bliebe ein Fenster, in dem weder
        # self.lock noch der Zaehler den laufenden Koerper-Strang verraten
        # (_live_aktiv saehe 'frei', die Wanduhr-Messung startete daneben).
        with self._personlive_lock:
            self._personlive_aktiv += 1
        try:
            threading.Thread(target=lauf, daemon=True,
                             name="personlive").start()
        except Exception:
            with self._personlive_lock:      # Start-Fehler: Zaehler ehrlich halten
                self._personlive_aktiv -= 1
            raise

    def _person_lauf(self, eid, entry, still):
        """Rumpf des Koerper-Urteils (aus _person_live.lauf ausgelagert, W1b:
        der Mantel fuehrt jetzt den Aktiv-Zaehler fuer _live_aktiv)."""
        try:
            from core import personlive as plv
            u = plv.urteilen(self.cfg["data_dir"],
                             os.environ.get("FRIGATE_URL", ""), eid,
                             kontrolle=self._kontroll_speicher(eid, entry),
                             still=still)
            if still:
                # Zweite, unabhaengige Sperre. KEIN Personenname im
                # Dienst-Log (Log-Vertrag §9) — die Zeile sagt nur, dass
                # gearbeitet und geschwiegen wurde.
                print("[personlive] quiet re-analysis: judged image "
                      "stored, nothing announced, live state untouched",
                      flush=True)
                return
            if u:
                # MQTT fuer HA-Automationen (User 04.08.): JEDER Treffer
                # ueber der Schwelle auf ein eigenes Topic — das Feld
                # feuer sagt, ob die Feuer-Regel erfuellt war.
                self._mqtt_pub(_melden.topic(self.cfg, "person_erkennung"), json.dumps({
                    "eid": eid, "person": u["person"],
                    "score": u["score"], "stuetzen": u["stuetzen"],
                    "feuer": bool(u.get("feuer")),
                    "quelle": "person_recognition",
                    "ts": round(time.time(), 1)}, ensure_ascii=False))
            if u and u.get("feuer"):
                text = (f"{u['person']} recognized by body "
                        f"(person recognition, not face) — score "
                        f"{u['score']}, {u['stuetzen']} supporting "
                        "events")
                push(self.cfg, "suslik person recognition", text,
                     attachment=u.get("bild"))
                # Telegram EXAKT wie die Gesichtsseite (User 04.08.:
                # allgemeine Einstellungen gelten fuer BEIDE Straenge):
                # _telegram_clip transkodiert mit der Guete-Einstellung,
                # telegram_inhalt bild/video und telegram_modus greifen.
                if self.cfg.get("telegram_modus", "aus") in ("direkt",
                                                             "beide"):
                    will_video = self.cfg.get("telegram_inhalt",
                                              "video") != "bild"
                    vid = self._telegram_clip(eid) if will_video else None
                    cap = text + ("\n(video unavailable — sending image)"
                                  if will_video and not vid else "")
                    telegram_video(self.cfg, vid, cap,
                                   crop=u.get("bild"))
                print(f"[personlive] MELDUNG {u}", flush=True)
            elif u:
                print(f"[personlive] Treffer ohne Feuer {u}", flush=True)
        except Exception as e:
            print(f"[personlive] Fehler: {e}", flush=True)

    def _maybe_alert(self, entry, event_dir):
        # matcht v2-Kategorie ODER v1-Vergleichskategorie (Parallelphase: "widerspruch" lebt in v1)
        if not ({entry.get("kategorie"), entry.get("kategorie_v1")} & set(self.cfg["alert_kategorien"])):
            return False
        now = time.time()
        if now - self.last_alert < self.cfg["alert_cooldown"]:
            self.log(f"{entry['eid']}: alert suppressed (cooldown)")
            return False
        f = entry["frigate"]
        fs = f"{f['score']:.2f}" if f["score"] is not None else "?"
        ours_txt = ", ".join(f"{p} {r['max']:+.2f}/{r['win3s']}x" for p, r in sorted(entry["ours"].items(),
                             key=lambda x: -(x[1]["max"] or 0))[:3]) or "keine Gesichter"
        _ar = _areas_mod.melde_zusatz(self.cfg.get("areas"), entry["camera"])   # Areas Stufe 1
        msg = (f"{entry['camera']}{f' · {_ar}' if _ar else ''} — Frigate: '{f['label']} {fs}' (= cos {f['cos']})"
               f" | Verify: {'bestaetigt: ' + ', '.join(entry['bestaetigt']) if entry['bestaetigt'] else 'NICHT bestaetigt'}"
               f" — {ours_txt} ({entry['faces']} Gesichter)")
        anhang = self._best_crop(event_dir, entry, entry["bestaetigt"] or list(entry["ours"]))
        if self.dry_alert:
            self.log(f"DRY-ALERT: {msg}")
            return False
        try:
            ok = push(self.cfg, f"suslik: {KAT_LABELS.get(entry['kategorie'], entry['kategorie'])}", msg, anhang)
            if ok:
                self.last_alert = now
            else:
                self.log("alert REJECTED by Pushover (status!=1) — check token/user")
            return ok
        except Exception as e:
            self.log(f"Pushover error: {e}")
            return False

    # -------------------------------------------------------------- Trigger: poll / Nachhol-Sweep
    def sweep(self):
        """Unverarbeitete person-Events der letzten lookback_h nachholen (Poll-Modus,
        MQTT-Start und -Reconnect) — Neustarts/Downtime reissen keine Loecher ins Log."""
        cfg = self.cfg
        LIMIT = 200
        try:
            after = time.time() - cfg["lookback_h"] * 3600
            evs = api(cfg, f"/api/events?label=person&after={after:.0f}&limit={LIMIT}&include_thumbnails=0")
            # after= filtert auf start_time (16.07. gemessen): Events, die VOR lookback_h
            # starteten und erst in einer Downtime endeten, entgehen dem Sweep — bei
            # lookback 2h vs. Eventdauern <2min real irrelevant.
            if self.frigate_fehler:                   # Frigate antwortet wieder -> Banner/Ampel entwarnen
                self.log("Frigate reachable again (sweep)")
            self.frigate_fehler = None
            self.frigate_fehlerserie = 0
            if len(evs) >= LIMIT:                     # harte Grenze ohne Pagination: aelteste fielen still weg
                self.log(f"sweep: Frigate returned the limit of {LIMIT} events — older ones may be missing "
                         f"(consider lowering lookback_h={cfg['lookback_h']})")
            todo = [ev for ev in sorted(evs, key=lambda e: e["start_time"])
                    if ev["id"] not in self.processed and ev.get("end_time")
                    and time.time() - ev["end_time"] >= cfg["clip_delay"]]
            # Leerer Master: EINMAL pro Sweep melden statt pro Event einen Frigate-GET + Logzeile zu
            # erzeugen. Ohne Referenzen kann keine Analyse gelingen -> der Sweep baute die gleiche
            # todo-Liste im 20s-Takt endlos neu (Dauerlast auf einer frischen Installation).
            if todo and not master_persons(cfg):
                self.log(f"sweep: {len(todo)} events waiting, but the reference master is EMPTY — "
                         f"enroll people first (setup wizard / enroll), then analysis will start")
                return
            if todo:
                self.log(f"sweep: catching up on {len(todo)} unprocessed events")
            for ev in todo:
                self.process_safe(ev["id"])
        except Exception as e:
            # Sichtbar machen: im Poll-Modus (Default der ausgelieferten Container) ist sweep() der
            # EINZIGE Frigate-Pfad. Ohne das blieben UI-Banner, System-Ampel und Stoerungswaechter
            # gruen, waehrend Frigate tot ist und Events aus dem lookback-Fenster laufen.
            self.log(f"sweep error: {e}")
            self.frigate_fehler = (time.time(), f"event poll: {e}")
            self.frigate_fehlerserie = getattr(self, "frigate_fehlerserie", 0) + 1

    # ------------------------------------------------ Nachhol-Lauf (Vorfall 22./23.07.)
    # 9 h lang scheiterte JEDE Analyse (kategorie="fehler"); die Events galten danach als
    # erledigt und wurden nie nachgeholt. Der Nachhol-Lauf repariert die Akte: getrennt vom
    # 2h-Live-Sweep, eigenes Fenster (nachhol_tage), begrenzte Versuche, STUMM.
    # Bewusst OHNE flock: nur dieser eine Thread schreibt nachhol.json (process() hat KEINEN
    # State-Hook, --once fasst die Datei nie an), Schreiben ist atomar via os.replace, und die
    # Kandidaten werden in jeder Runde neu aus deckung.jsonl abgeleitet -> der State ist
    # selbstheilend, ein Totalverlust kostet hoechstens eine doppelte Versuchsserie.
    def _nachhol_pfad(self):
        return os.path.join(self.cfg["data_dir"], "state", "nachhol.json")

    def _nachhol_lesen(self):
        """Versuchszaehler. FAIL-SAFE: ein Eintrag, den wir nicht sauber lesen koennen, gilt als
        AUFGEGEBEN, nie als 'noch nie versucht' — eine kaputte Datei darf keine Analyse-Schleife
        ausloesen. Wird NUR im Nachhol-Thread gerufen, nie in __init__ (dort gibt es self.logbuf
        noch nicht, ein log() wuerde den Dienststart killen)."""
        try:
            with open(self._nachhol_pfad()) as f:
                roh = (json.load(f) or {}).get("events")
            if not isinstance(roh, dict):
                return {}
        except FileNotFoundError:
            return {}
        except Exception as e:
            self.log(f"nachhol.json unreadable ({e}) — counters start over")
            return {}
        out = {}
        for eid, s in roh.items():
            try:
                out[str(eid)] = {"n": int(s["n"]), "ts": float(s.get("ts") or 0),
                                 "ev": float(s.get("ev") or 0), "aus": s.get("aus") or None}
            except Exception:
                out[str(eid)] = {"n": 99, "ts": time.time(), "ev": 0.0, "aus": "state_kaputt"}
        return out

    def _nachhol_schreiben(self, st):
        """Atomar (tmp + os.replace) + Pruning gegen die FESTE Grenze. Rueckgabe False bei
        Schreibfehler; der Aufrufer bricht die Runde dann ab, BEVOR GPU-Arbeit anfaellt — ein
        nicht persistierter Zaehler waere genau die Endlosschleife, die wir verhindern wollen."""
        grenze = time.time() - NACHHOL_PRUNE_TAGE * 86400
        st = {e: s for e, s in st.items() if (s.get("ev") or s.get("ts") or 0) >= grenze}
        p = self._nachhol_pfad()
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p + ".tmp", "w") as f:
                json.dump({"version": 1, "events": st}, f, ensure_ascii=False, indent=1)
                f.flush(); os.fsync(f.fileno())
            os.replace(p + ".tmp", p)
            return True
        except Exception as e:
            self.log(f"writing nachhol.json failed: {e} — catch-up round skipped")
            return False

    def _nachhol_kandidaten(self):
        """Kandidaten sind ABGELEITET, nicht gespeichert: Events, deren LETZTE deckung-Zeile
        'fehler' ist, im Fenster nachhol_tage, Versuche offen, nicht aufgegeben — und nach deren
        Fehlschlag der Dienst nachweislich mindestens EINE Analyse geschafft hat (letzte_gute).
        Damit verbrennt eine noch laufende Stoerung kein Versuchsbudget.
        Sortierung: laengster nicht-Versuch zuerst (Round-Robin), darunter juengste Events."""
        cfg, jetzt = self.cfg, time.time()
        fenster = jetzt - float(cfg["nachhol_tage"]) * 86400
        letzte, letzte_gute = {}, 0.0
        if os.path.exists(self.log_path):
            with open(self.log_path) as f:
                for l in f:
                    try:
                        r = json.loads(l); eid = r["eid"]
                    except Exception:
                        continue
                    letzte[eid] = r
                    # Korrekturzeilen (Issue #19) sind KEINE gelaufene Analyse — ihr ts ist
                    # der Anlern-Zeitpunkt. Als "letzte gute" gezaehlt, taeuschten sie
                    # "Stoerung nachweislich vorbei" vor und gaeben Nachhol-Versuche
                    # mitten in einer laufenden Stoerung frei (Widerleger 11.08.).
                    if r.get("kategorie") != "fehler" and not r.get("korrektur"):
                        letzte_gute = max(letzte_gute, float(r.get("ts") or 0))
        st = self._nachhol_lesen()
        kand, offen, tot, neu_aus = [], 0, 0, False
        for eid, r in letzte.items():
            if r.get("kategorie") != "fehler":
                continue
            ev = float(r.get("start") or r.get("ts") or 0) or jetzt
            s = st.get(eid) or {}
            if s.get("aus"):
                tot += 1
                continue
            n = int(s.get("n") or 0)
            if not (fenster <= ev <= jetzt + 3600):        # Fenster + Schutz gegen Zukunfts-ts
                if n < int(cfg["nachhol_versuche"]) and eid in st:
                    st[eid] = {**s, "aus": "fenster"}      # genau EINE Logzeile statt stillem Verlust
                    neu_aus = True
                    self.log(f"{eid}: catch-up abandoned (fell out of the {cfg['nachhol_tage']}d window "
                             f"after {n} attempts)")
                continue
            if n >= int(cfg["nachhol_versuche"]):
                tot += 1
                continue
            offen += 1
            if float(r.get("ts") or 0) >= letzte_gute:
                continue                                    # Stoerung seither nicht nachweislich vorbei
            lv = float(s.get("ts") or 0)
            pause = float(cfg["nachhol_pause_s"]) * max(1, n)
            if lv and lv <= jetzt and jetzt - lv < pause:
                continue                                    # Backoff; lv > jetzt (Uhrsprung) = faellig
            kand.append((lv, -ev, eid, ev))
        if neu_aus:
            self._nachhol_schreiben(st)
        kand.sort()
        self._nachhol_stat = (offen, tot)
        return [(e, v) for _, _, e, v in kand], offen, tot

    def _nachhol_vorpruefung(self, eid):
        """Billig, zwei HTTP-Calls, KEINE GPU. Trennt 'reparierbar' von 'dauerhaft tot':
          GET  /api/events/<eid>          -> 404, wenn das Event weg ist
          HEAD /api/events/<eid>/clip.mp4 -> 400/404/410, wenn die Aufnahme weg ist
        Ohne das wuerde jedes Event mit geloeschter Aufnahme 3x den Modell-Init verbrennen.
        Rueckgabe: None (weiter) | 'event_weg' | 'clip_weg' | 'frigate' (Runde abbrechen)."""
        cfg = self.cfg
        try:
            api(cfg, f"/api/events/{eid}")
        except urllib.error.HTTPError as e:
            return "event_weg" if e.code == 404 else "frigate"
        except Exception:
            return "frigate"
        try:
            req = urllib.request.Request(cfg["frigate_url"].rstrip("/") + f"/api/events/{eid}/clip.mp4",
                                         method="HEAD")
            with urllib.request.urlopen(req, timeout=20) as r:
                return None if r.status < 400 else "clip_weg"
        except urllib.error.HTTPError as e:
            return "clip_weg" if e.code in (400, 404, 410) else "frigate"
        except Exception:
            return "frigate"

    def _nachhol_aufraeumen(self, eid, n):
        """Vor jedem Versuch: Artefakte des gescheiterten Laufs weg, altes analyze.log sichern.
        ZWINGEND, weil analyze.py einen Resume hat (done_labels aus results.jsonl) und
        results/kandidaten im Append-Modus schreibt: ohne Aufraeumen wuerde ein Wiederholungs-
        lauf GAR NICHT neu rechnen, sondern das alte Ergebnis als Erfolg melden."""
        d = os.path.join(self.cfg["data_dir"], "events", eid.replace("/", "_"))
        try:
            lp = os.path.join(d, "analyze.log")
            if os.path.exists(lp):
                os.replace(lp, os.path.join(d, f"analyze_versuch{max(0, n - 1)}.log"))
            for f in ("results.jsonl", "kandidaten.jsonl"):
                p = os.path.join(d, f)
                if os.path.exists(p):
                    os.remove(p)
        except Exception as e:
            self.log(f"{eid}: catch-up cleanup failed: {e}")

    def _nachhol_runde(self):
        cfg, jetzt = self.cfg, time.time()
        if self._nachhol_sperre > 0:                        # Schutzschalter nach Fehlversuch
            self._nachhol_sperre -= 1
            return
        if jetzt - getattr(self, "letzte_aktivitaet", 0) < int(cfg["nachhol_ruhe_s"]):
            return                                          # Live-Betrieb hat Vorrang (GPU)
        if self._gpu_bg_lock.locked():
            return                                          # schwerer GPU-Hintergrundjob laeuft
        kand, offen, tot = self._nachhol_kandidaten()
        if not kand:
            return
        if not master_persons(cfg):
            self.log("catch-up: reference master empty — round skipped")
            return
        eid, ev = kand[0]
        st = self._nachhol_lesen()
        s = st.setdefault(eid, {"n": 0, "ts": 0.0, "ev": ev, "aus": None})
        s["ts"], s["ev"] = round(jetzt, 1), ev              # ts IMMER fortschreiben: ein Event kann
        grund = self._nachhol_vorpruefung(eid)              # den einen Slot nie dauerhaft belegen
        if grund == "frigate":
            self._nachhol_schreiben(st)                     # Backoff, aber KEIN Versuch verbrannt
            return
        if grund:
            s["aus"] = grund
            self._nachhol_schreiben(st)
            self.log(f"{eid}: catch-up abandoned for good ({grund}) — no GPU spent")
            return
        s["n"] = int(s.get("n") or 0) + 1
        if not self._nachhol_schreiben(st):
            return                                          # Zaehler nicht persistierbar -> KEINE Analyse
        n = s["n"]
        self.log(f"{eid}: catch-up attempt {n}/{cfg['nachhol_versuche']} "
                 f"({max(0, offen - 1)} more pending, {tot} abandoned)")
        self._nachhol_aufraeumen(eid, n)
        entry = self.process(eid, nachhol=n)
        if entry is None:                                   # Kamera aus / Zonen-Gate / Abbruch:
            st = self._nachhol_lesen()                      # process() hat KEINE Zeile geschrieben
            st.setdefault(eid, s)["aus"] = "kein_ergebnis"  # -> FAIL-SAFE endgueltig aufgeben
            self._nachhol_schreiben(st)
            self.log(f"{eid}: catch-up without result (skipped/aborted) — abandoned")
            return
        if entry.get("kategorie") == "fehler":
            self._nachhol_sperre = min(6, self._nachhol_sperre * 2 + 1)   # 1, 3, 6 Runden Pause
            self.log(f"{eid}: catch-up attempt {n} again 'fehler' — pausing {self._nachhol_sperre} "
                     f"rounds (malfunction may still be active)")
            return
        self._nachhol_sperre = 0
        # W3: Browser-Kopie lazy beim Klick (/video), nicht mehr im Nachhol-Pfad.
        self.log(f"{eid}: catch-up successful -> {entry['kategorie']} "
                 f"(ours={entry['bestaetigt'] or 'unknown'}, {entry['dauer_s']}s, silent)")

    def start_nachhol(self):
        """Nachhol-Thread. Nimmt _gpu_bg_lock NICHT, sondern prueft es nur — sonst wuerde er das
        Lock halten, waehrend er auf self.lock wartet, und dabei das live getriggerte
        _szenario_nachsammeln sowie das 06:00-Netz blockieren."""
        self._nachhol_sperre = 0
        self._nachhol_stat = (0, 0)
        if int(self.cfg["nachhol_versuche"]) <= 0 or not self.cfg.get("frigate_url"):
            self.log("catch-up run off (nachhol_versuche=0 or no frigate_url)")
            return
        def lauf():
            time.sleep(max(60, int(self.cfg["nachhol_start_s"])))
            while True:
                try:
                    self._nachhol_runde()
                except Exception as e:
                    self.log(f"catch-up round error: {e}")
                time.sleep(max(120, int(self.cfg["nachhol_intervall_s"])))   # nie Busy-Loop
        threading.Thread(target=lauf, daemon=True).start()
        self.log(f"catch-up run active: every {self.cfg['nachhol_intervall_s']}s, window "
                 f"{self.cfg['nachhol_tage']}d, max {self.cfg['nachhol_versuche']} attempts, "
                 f"analysis cap {self.cfg['nachhol_analyse_timeout_s']}s, silent (no alerts)")

    def poll_loop(self):
        cfg = self.cfg
        self.log(f"poll mode: every {cfg['poll_interval']}s, lookback {cfg['lookback_h']}h, "
                 f"clip_delay {cfg['clip_delay']}s, backend {cfg.get('backend') or cfg['ov_device']}")
        while True:
            self.sweep()
            time.sleep(cfg["poll_interval"])

    # -------------------------------------------------------------- Trigger: mqtt
    def mqtt_loop(self):
        import paho.mqtt.client as mqtt
        cfg = self.cfg["mqtt"]
        cl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if cfg.get("user"):
            cl.username_pw_set(cfg["user"], cfg.get("password", ""))

        def on_connect(_c, _u, _f, rc, _p=None):
            if getattr(rc, "is_failure", False):
                self.log(f"MQTT connect rejected: {rc} (check credentials/broker)")
                return
            # subscribe MUSS hier stehen: paho reconnectet nach Abriss still, eine nur
            # einmalig gesetzte Subscription waere danach weg (Dienst liefe taub weiter).
            cl.subscribe("frigate/events")
            self.log(f"MQTT connected ({rc}), subscribed to frigate/events, catch-up sweep starting")
            threading.Thread(target=self.sweep, daemon=True).start()

        def on_disconnect(_c, _u, _f, rc, _p=None):
            self.log(f"MQTT disconnected ({rc}), reconnect runs automatically")

        def on_msg(_c, _u, m):
            try:
                d = json.loads(m.payload)
                after = d.get("after", {})
                if d.get("type") == "end" and after.get("label") == "person":
                    eid = after.get("id")
                    threading.Timer(self.cfg["clip_delay"], self.process_safe, args=(eid,)).start()
            except Exception as e:
                self.log(f"MQTT payload error: {e}")

        letzte_fehlmeldung = [0.0]

        def on_connect_fail(_c, _u):
            # Ohne diese Meldung retryt paho stumm (nur im DEBUG-Log) — der Dienst laege
            # taub da, waehrend UI und /health munter "ok" sagen. Gedrosselt auf 5 min,
            # sonst schreibt ein dauerhaft toter Broker im 1-60s-Backoff das Log voll.
            if time.time() - letzte_fehlmeldung[0] >= 300:
                letzte_fehlmeldung[0] = time.time()
                self.log(f"MQTT trigger: broker {cfg['host']}:{cfg.get('port', 1883)} not "
                         f"reachable — no event trigger, reconnect keeps running "
                         f"(check network/firewall/broker)")

        cl.on_connect = on_connect
        cl.on_disconnect = on_disconnect
        cl.on_message = on_msg
        cl.on_connect_fail = on_connect_fail
        self.mqtt_trigger = cl                    # Watchdog sieht den Trigger-Client (s. start_stoerungswaechter)
        # connect_async + retry_first_connection statt connect(): ein beim Dienststart nicht
        # erreichbarer Broker warf hier eine TimeoutError ungefangen bis in main() hoch — der
        # PROZESS starb, und `restart: unless-stopped` startete ihn endlos neu (26.07. auf der
        # neuen Projektmaschine 48 Neustarts in Folge, gar kein Betrieb; Ursache dort: die neue
        # Host-IP darf noch nicht an den Broker). Der Publisher-Pfad ist seit Welle 4 genau
        # dagegen gehaertet, der Trigger-Pfad war es nie — dieselbe Fehlerklasse, andere Haelfte.
        # An der installierten paho-Quelle geprueft (client.py, Zweig MQTT_CS_CONNECT_ASYNC):
        # loop_forever() wiederholt den ERSTEN Verbindungsversuch nur mit
        # retry_first_connection=True, sonst reicht es die OSError durch.
        cl.reconnect_delay_set(min_delay=1, max_delay=60)
        cl.connect_async(cfg["host"], int(cfg.get("port", 1883)), 60)
        self.log(f"MQTT mode: {cfg['host']}:{cfg.get('port', 1883)} frigate/events")
        cl.loop_forever(retry_first_connection=True)


# ------------------------------------------------------------------ Mini-Webview (read-only, §1 Konzept)
def make_handler(svc):
    cfg = svc.cfg

    class H(BaseHTTPRequestHandler):
        # Ohne timeout blockiert eine haengende Verbindung (schlafendes Notebook, abgezogenes
        # Netz, halber Upload) ihren Thread unbegrenzt — ueber Wochen ein Thread-Leck, ganz ohne
        # Angreifer. 60 s ist grosszuegig genug fuer Video-Ranges an einen langsamen Client.
        timeout = 60

        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="text/html; charset=utf-8", location=None):
            self.send_response(code)
            if location:
                self.send_header("Location", location)
            self.send_header("Content-Type", ctype)
            if ctype.startswith(("text/html", "application/json",
                                 "application/javascript", "text/css")):
                # ohne das zeigte der Browser beim Oeffnen die GESTRIGE Seite aus seinem
                # Heuristik-Cache (User-Befund 19.07.); JS/CSS ebenfalls, sonst laufen neue
                # Seiten gegen ein altes app.js (onclick-Funktionen fehlen -> Knoepfe tot)
                self.send_header("Cache-Control", "no-store")
            self.end_headers()
            # Getrennte Clients sind Normalbetrieb, kein Dienstfehler (Fund 25.07. durch das
            # Geometrie-Gate): ein Browser bricht Bildladevorgaenge ab, sobald er weiternavigiert,
            # und ein Telefon wechselt mitten im Laden das Netz. Vorher lief der BrokenPipeError
            # ungefangen bis in socketserver hoch — VOLLER Traceback im Log fuer jeden geschlossenen
            # Tab, und das Prod-Log-Gate (S4/Release Stufe 2 greppen auf "Traceback") wird rot fuer
            # einen Nicht-Fehler. Ein Gate, das Fehlalarm gibt, wird ignoriert; deshalb gehoert der
            # Fall HIER behandelt, nicht im Gate ausgenommen.
            try:
                self.wfile.write(body if isinstance(body, bytes) else body.encode())
            except (BrokenPipeError, ConnectionResetError):
                pass                              # Client weg — nichts mehr zuzustellen

        def _banner(self):
            f = getattr(svc, "frigate_fehler", None)
            if f and time.time() - f[0] < 600:
                t = datetime.datetime.fromtimestamp(f[0]).strftime("%H:%M:%S")
                # Tokn59-Fund Issue #8 (31.07.): der Banner war als letzte UI-Stelle noch
                # deutsch UND nannte den gescheiterten Endpunkt nicht — "test ok" (config)
                # und Banner-Rot (event poll) koennen GLEICHZEITIG wahr sein; das Label
                # kommt seither von der Setz-Stelle mit (event fetch/poll/list).
                # 220 statt 110 Zeichen (Issue #14-Nachbefund): der Endpunkt-Fehlertext
                # ("event poll: HTTP 500 ... bei /api/events?...") war laenger als die
                # alte Kappung — genau das Detail, fuer das das Label gebaut wurde,
                # fiel im Banner wieder weg.
                return (f"Frigate unreachable (last error {t}): {f[1][:220]} — "
                        "the UI keeps serving local data.")
            # Issue #13: Daten-ohne-Mount geht vor Varianten-Hinweis — Datenverlust-
            # Risiko schlaegt Performance-Tipp (beide einmal je Start berechnet).
            d = getattr(svc, "daten_hinweis", None)
            if d:
                return d
            # Task #13: Varianten-Hinweis (einmal je Start berechnet; Frigate-Fehler geht vor)
            return getattr(svc, "varianten_hinweis", None)

        def _send_file_ranged(self, p, ctype, dl_name=None):
            """Datei mit HTTP-Range ausliefern (Browser-Video braucht das zum Spulen).
            dl_name: Download-Dateiname fuer 'Video speichern' — ohne ihn nimmt der Browser
            den URL-Namen, und da Event-IDs einen Punkt tragen, haelt er den Rest hinter dem
            Punkt fuer die Endung (Issue #15: Export ohne .mp4)."""
            size = os.path.getsize(p)
            rng = self.headers.get("Range")
            m = re.match(r"bytes=(\d*)-(\d*)$", rng or "")
            partial = bool(rng and m)
            start, end = 0, size - 1
            if partial:
                if m.group(1):
                    start = int(m.group(1))
                    if m.group(2):
                        end = min(int(m.group(2)), size - 1)
                elif m.group(2):                           # bytes=-N: letzte N Bytes
                    start = max(0, size - int(m.group(2)))
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
            self.send_response(206 if partial else 200)
            self.send_header("Content-Type", ctype)
            if dl_name:
                self.send_header("Content-Disposition", f'inline; filename="{dl_name}"')
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            if partial:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            try:
                with open(p, "rb") as f:
                    f.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = f.read(min(1 << 20, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass                                       # Browser hat abgebrochen (Spulen/Tab zu)

        def do_POST(self):
            pfad = urllib.parse.unquote(self.path.split("?")[0])
            # CSRF-Schutz (Code-Review 24.07.): mutierende Requests nur same-origin. Ein Browser sendet
            # bei cross-site-POST immer Origin/Referer; weicht deren Host vom eigenen Host ab -> ablehnen.
            # Fehlt beides (curl/API-Client, kein Browser), ist es kein CSRF-Vektor -> durchlassen.
            _host = self.headers.get("Host", "")
            for _h in ("Origin", "Referer"):
                _v = self.headers.get(_h)
                if _v:
                    _net = urllib.parse.urlparse(_v).netloc
                    if _host and _net and _net != _host:
                        return self._send(403, json.dumps({"ok": False, "msg": "cross-origin POST refused"}),
                                          "application/json")
                    break
            if pfad == "/enroll":                              # Lern-Entscheidung (AP4)
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    ok, msg = svc.enroll_entscheiden(str(d["id"]), str(d["aktion"]),
                                                     (str(d["person"]).strip() or None) if d.get("person") else None)
                    return self._send(200 if ok else 400,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                                      "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/ref_entfernen_batch":                 # mehrere Referenzbilder auf einmal loeschen
                try:
                    import anlernen
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    weg, geloescht = 0, []
                    for it in (d.get("items") or []):
                        person = (it.get("person") or "").strip()
                        datei = (it.get("datei") or "").strip()
                        ok, _ = anlernen.entferne_referenz(person, datei)
                        if ok:
                            weg += 1
                            geloescht.append((person, datei))
                    if weg:
                        svc.log(f"REFERENCES REMOVED (batch): {weg} (Frigate untouched by design)")
                        svc.qs_neu_starten()
                    return self._send(200, json.dumps({"ok": weg > 0,
                                      "msg": f"{weg} Bild(er) entfernt"}, ensure_ascii=False),
                                      "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/person_loeschen":                     # GANZE Person entfernen (User 25.07.:
                # "es muss ja auch moeglich sein, ein ganzes Benutzerkonto rauszuloeschen — nicht
                # nur ein Gesicht, sondern auch den Namen"). REVERSIBEL: der Ordner wandert in
                # <data>/trash/ statt geloescht zu werden — eine Ein-Klick-Vernichtung von
                # Referenzdaten gaebe es sonst nicht wieder her. refcache wird invalidiert,
                # damit Suche/Vorschlaege die Person sofort vergessen.
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 8192))) if n else {}
                    p = (d.get("person") or "").strip()
                    if not p or p not in master_persons(cfg):
                        return self._send(200, json.dumps({"ok": False, "msg": "unknown person"}),
                                          "application/json")
                    quelle = os.path.join(cfg["data_dir"], "faces", p)
                    if os.path.realpath(quelle) != os.path.realpath(
                            os.path.join(cfg["data_dir"], "faces", os.path.basename(p))):
                        return self._send(200, json.dumps({"ok": False, "msg": "invalid name"}),
                                          "application/json")
                    papierkorb = os.path.join(cfg["data_dir"], "trash")
                    os.makedirs(papierkorb, exist_ok=True)
                    ziel = os.path.join(papierkorb, f"person_{p}_{int(time.time())}")
                    n_bilder = len([f for f in os.listdir(quelle)      # .webp NICHT vergessen: Frigate liefert webp
                                    if f.lower().endswith(_reg.BILD_ENDUNGEN)])
                    os.rename(quelle, ziel)
                    try:
                        os.remove(os.path.join(cfg["data_dir"], "clips", "refcache.npz"))
                    except OSError:
                        pass
                    svc.log(f"PERSON DELETED: {p} ({n_bilder} reference image(s)) -> trash/"
                            f"{os.path.basename(ziel)} — recoverable by moving back")
                    return self._send(200, json.dumps(
                        {"ok": True, "msg": f"{p} removed ({n_bilder} reference images moved "
                                            f"to trash — recoverable)"}), "application/json")
                except Exception as e:
                    return self._send(200, json.dumps({"ok": False, "msg": str(e)[:120]}),
                                      "application/json")
            if pfad == "/ref_entfernen":                       # Referenzbild loeschen (Fehllabel)
                try:
                    import anlernen
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 8192)))
                    person = (d.get("person") or "").strip()
                    datei = (d.get("datei") or "").strip()
                    ok, msg = anlernen.entferne_referenz(person, datei)
                    if ok:
                        svc.log(f"REFERENCE REMOVED: {msg} (Frigate untouched by design)")
                        svc.qs_neu_starten()               # nach Entfernen automatisch gegenpruefen
                    return self._send(200 if ok else 400,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                                      "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/ref_pruef_neu":                       # Referenz-QS neu berechnen (Hintergrund)
                svc.qs_neu_starten()
                return self._send(200, json.dumps({"ok": True,
                                  "msg": "Prüfung läuft, Seite in ~1 min neu laden"}, ensure_ascii=False),
                                  "application/json")
            if pfad == "/anlern_wartung_jetzt":                # Reorganisieren (Pool-Neupruefung + Cluster neu), manuell
                gestartet = svc._reorganisieren()
                msg = ("Reorganizing (pool re-check + re-cluster, 1-2 min, then reload the pages)"
                       if gestartet else "Reorganizing already running — please wait")
                return self._send(200, json.dumps({"ok": bool(gestartet), "msg": msg},
                                  ensure_ascii=False), "application/json")
            if pfad in ("/unbekannt_reconcile", "/unbekannt_besucher", "/unbekannt_verwerfen",
                        "/unbekannt_merge", "/unbekannt_benennen"):   # Unbekannt-Reiter (20.07.)
                try:
                    import anlernen
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 8192))) if n else {}
                    if pfad == "/unbekannt_reconcile":
                        idents, vs = anlernen.reconcile_unbekannte()
                        svc.log(f"unknown reconcile (manual): {len(idents)} identities, {len(vs)} suggestions")
                        res = (True, f"{len(idents)} Unbekannte, {len(vs)} Vorschläge")
                    elif pfad == "/unbekannt_besucher":
                        an = bool(d.get("an", True))
                        ok = anlernen.unbekannt_besucher(d.get("uid", ""), an)
                        res = (ok, ("ignoriert" if an else "wieder aktiv") if ok else "nicht gefunden")
                    elif pfad == "/unbekannt_merge":
                        ok = anlernen.unbekannt_merge(d.get("a", ""), d.get("b", ""))
                        res = (ok, "zusammengelegt" if ok else "Fehler")
                    elif pfad == "/unbekannt_verwerfen":       # 'Different' persistent (25.07.)
                        ok = anlernen.verwerfe_vorschlag(d.get("a", ""), d.get("b", ""))
                        res = (ok, "noted — won't suggest this pair again" if ok else "Fehler")
                    else:                                        # /unbekannt_benennen
                        _person = (d.get("person") or "").strip()
                        ok, msg, betroffen = anlernen.unbekannt_benennen(d.get("uid", ""), _person)
                        if ok:
                            svc.log(f"UNKNOWN NAMED: {d.get('uid')} -> {d.get('person')} ({msg})")
                            svc.qs_neu_starten()
                            # Issue #19: Events der uebernommenen Gesichter nachpruefen,
                            # damit die Unknown-Karten des Durchgangs verschwinden.
                            svc.anlern_nachpruefung_starten(_person, betroffen)
                            msg += " — re-checking this pass's events in the background"
                        res = (ok, msg)
                    return self._send(200, json.dumps({"ok": res[0], "msg": res[1]},
                                      ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad in ("/sync_abwahl", "/sync_wieder_anbieten"):   # .133/.137: Merker der Sync-Seite
                # Bewusst abgewaehlte Referenzbilder bleiben im Master, gehen aber
                # nie nach Frigate — auch der AUTO-Export ueberspringt sie (Filter
                # in sync_refs.cmd_export). Eigener Merker, NICHT die refs_meta-
                # Tombstones: die bedeuten "Bild geloescht" und sperren den Import.
                import sync_refs as _sr
                try:
                    _n = int(self.headers.get("Content-Length", 0))
                    _d = json.loads(self.rfile.read(min(_n, 1000000)) or "{}")
                except Exception:
                    _d = {}

                # .134 Hinweis-Fix: Namen gegen die Registry-Muster pruefen (Gate
                # PYDATEI-Regel) — der Merker nimmt sonst beliebige Fremdeingabe an.
                from core.registry import PERSON_RE as _pre, DATEI_RE as _dre
                _p_ok = re.compile(rf"^{_pre}$", re.UNICODE)
                _d_ok = re.compile(rf"^{_dre}$", re.UNICODE)

                def _paare(feld):
                    return [(str(x[0]), str(x[1])) for x in (_d.get(feld) or [])
                            if isinstance(x, (list, tuple)) and len(x) >= 2
                            and _p_ok.match(str(x[0])) and _d_ok.match(str(x[1]))]
                if pfad == "/sync_wieder_anbieten":
                    # .137 "offer again": ein in Frigate geloeschtes bzw. frueher
                    # exportiertes Bild wird wieder normaler Kandidat. Das
                    # Protokoll wird nur ANGEHAENGT (aktiv=false), nie umgeschrieben.
                    try:
                        n_wa = _sr.wieder_anbieten(_paare("bilder"))
                    except Exception as e:
                        return self._send(400, json.dumps({"ok": False, "msg": str(e)},
                                                          ensure_ascii=False), "application/json")
                    if n_wa:
                        svc.log(f"sync selection: {n_wa} image(s) offered again")
                    return self._send(200, json.dumps(
                        {"ok": True, "msg": f"{n_wa} back on the candidate list"},
                        ensure_ascii=False), "application/json")
                try:
                    n_ab = _sr.abwahl_setzen(_paare("abwahl"), True)
                    n_zu = _sr.abwahl_setzen(_paare("zurueck"), False)
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)},
                                                      ensure_ascii=False), "application/json")
                if n_ab or n_zu:
                    svc.log(f"sync selection: {n_ab} deselected, {n_zu} restored")
                return self._send(200, json.dumps(
                    {"ok": True, "msg": f"{n_ab} deselected, {n_zu} restored"},
                    ensure_ascii=False), "application/json")
            if pfad in ("/sync_export", "/sync_import", "/sync_auswahl_start"):
                # Referenz-Sync Master <-> Frigate manuell. /sync_auswahl_start ist
                # derselbe Export mit einer AUSWAHL (.133, Review-&-sync-Seite):
                # bewusst KEINE zweite Job-Schleife — Status-Reset, Fortschritt,
                # eigener_status und Fehlerauswertung duerfen nie auseinanderlaufen.
                modus = "import" if pfad == "/sync_import" else "export"
                # .134 Review-SOLL (Lauf-Riegel): ein Sync zur Zeit — sonst kapert
                # ein Auto-Export waehrend des selektiven Transfers Fortschritt,
                # eigener_status und Ergebnisanzeige (gemeinsame Status-Dateien).
                if getattr(svc, "_sync_job_aktiv", False):
                    return self._send(409, json.dumps({"ok": False,
                        "msg": "a sync is already running — wait for it to finish"},
                        ensure_ascii=False), "application/json")
                if modus == "export" and frigate_read_only(svc.cfg):   # read-only: kein Schreiben nach Frigate (Import bleibt)
                    return self._send(403, json.dumps({"ok": False,
                        "msg": "read-only mode: writing references to Frigate is disabled (see the System page switch)"},
                        ensure_ascii=False), "application/json")
                try:
                    _n = int(self.headers.get("Content-Length", 0))
                    # Die Auswahl kann hunderte Namen tragen — dafuer ein groesserer
                    # Deckel, fuer die beiden Alt-Routen bleibt es bei 4 KB.
                    _body = json.loads(self.rfile.read(
                        min(_n, 1000000 if pfad == "/sync_auswahl_start" else 4096)) or "{}")
                except Exception:
                    _body = {}
                auswahl_pfad = ""
                if pfad == "/sync_auswahl_start":
                    _paare = [[str(x[0]), str(x[1])] for x in (_body.get("auswahl") or [])
                              if isinstance(x, (list, tuple)) and len(x) >= 2]
                    if not _paare:
                        return self._send(400, json.dumps(
                            {"ok": False, "msg": "nothing selected — tick at least one image"},
                            ensure_ascii=False), "application/json")
                    # Uebergabe als DATEI, nie als argv (hunderte Namen sprengen jede
                    # Kommandozeile); sync_refs filtert damit die ECHTE Kandidatenliste.
                    auswahl_pfad = os.path.join(svc.cfg["data_dir"], "state",
                                                "sync_auswahl_lauf.json")
                    os.makedirs(os.path.dirname(auswahl_pfad), exist_ok=True)
                    with open(auswahl_pfad, "w", encoding="utf-8") as _af:
                        json.dump(_paare, _af, ensure_ascii=False)
                furl = (_body.get("url") or svc.cfg.get("frigate_url") or "").strip()   # Wizard reicht die URL mit
                if furl:                                   # Fremdeingabe -> nur http(s), sonst spricht urlopen auch file://
                    _ok, _res = pruefe_url(furl)
                    if not _ok:
                        return self._send(400, json.dumps({"ok": False, "msg": f"Frigate URL: {_res}"},
                                                          ensure_ascii=False), "application/json")
                    furl = _res
                def job():
                    env = dict(os.environ, OV_DEVICE=svc.cfg["ov_device"])
                    if furl:
                        env["FRIGATE_URL"] = furl
                    prog = os.path.join(svc.cfg["data_dir"], "state", "sync_progress.json")
                    svc.log(f"reference sync {modus}: started")
                    # .132 Review-MUSS: Status VOR dem Start zuruecksetzen — sonst
                    # lesen die 1-s-Poller den ENDstatus des VORIGEN Laufs als
                    # Ergebnis DIESES Laufs (phase error/done -> sofort Abbruch).
                    start_ts = time.time()
                    try:
                        json.dump({"ts": round(start_ts, 1), "phase": "loading",
                                   "modus": modus, "total": 0, "done": 0},
                                  open(prog, "w"))
                    except Exception:
                        pass
                    errp = os.path.join(svc.cfg["data_dir"], "state", f"sync_{modus}_err.log")
                    ef = open(errp, "w+")                      # stderr NICHT verwerfen (frueher DEVNULL -> Fehler still)
                    args = [sys.executable,                    # Container hat kein venv/
                            os.path.join(HERE, "sync_refs.py"), modus]
                    if modus == "export":
                        args.append("--force")                 # read-only oben mit voller Config geprueft (.132)
                    if auswahl_pfad:                           # .133: nur die gewaehlten Kandidaten
                        args.append(f"--auswahl={auswahl_pfad}")
                    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=ef, env=env)
                    while proc.poll() is None:                 # laeuft -> Fortschritt ins Log (docker logs / /log)
                        time.sleep(8)
                        try:
                            with open(prog) as f:
                                s = json.load(f)
                            if s.get("phase") in ("import", "export"):
                                svc.log(f"Sync {modus}: {s.get('done')}/{s.get('total')} ({s.get('current','')})")
                        except Exception:
                            pass
                    try:
                        ef.seek(0); err_txt = fehler_kern(ef.read()); ef.close()
                    except Exception:
                        err_txt = ""
                    if proc.returncode != 0:                   # Exit-Code JETZT geprueft (frueher NIE -> immer 'fertig')
                        svc.log(f"!! reference sync {modus} FAILED (rc={proc.returncode}): {err_txt}")
                        # .132: cmd_export schreibt bei Fatal-Stopps selbst einen
                        # REICHEREN error-Status (detail + hinweis aus einer Quelle)
                        # — den NIE ueberschreiben. Review-MUSS: nur ein Status, der
                        # NACH dem Start DIESES Laufs geschrieben wurde, zaehlt als
                        # eigener (sonst verschluckte ein Alt-Fehler die echte Ursache).
                        eigener_status = False
                        try:
                            with open(prog) as f:
                                _ps = json.load(f)
                            eigener_status = (_ps.get("phase") == "error"
                                              and float(_ps.get("ts") or 0) >= start_ts
                                              and bool(_ps.get("detail") or _ps.get("hinweis")))
                        except Exception:
                            pass
                        from sync_refs import FR_AUS_MARKER as _frm, FR_AUS_HINWEIS as _frh
                        hinweis = _frh if _frm in err_txt else ""
                        try:                                   # UI-Status auf error statt endlosem Poll auf 'done'
                            if not eigener_status:
                                json.dump({"ts": round(time.time(), 1), "phase": "error",
                                           "modus": modus, "total": 0, "done": 0,
                                           "msg": f"sync {modus} failed (rc={proc.returncode})",
                                           "detail": err_txt, "hinweis": hinweis},
                                          open(prog, "w"))
                        except Exception:
                            pass
                        return
                    if modus == "import":                      # importierte Referenzen -> Embeddings auf GPU neu
                        try:
                            os.remove(os.path.join(svc.cfg["data_dir"], "clips", "refcache.npz"))
                        except FileNotFoundError:
                            pass
                        svc.log("sync import finished -> recomputing embeddings on GPU (refcache) …")
                        svc.qs_neu_starten()
                    svc.log(f"reference sync {modus}: finished")
                # .134 Lauf-Riegel: Flag VOR dem Start setzen (nicht im Thread —
                # sonst schluepft ein zweiter POST durchs Fenster), im finally raeumen.
                svc._sync_job_aktiv = True

                def _job_mit_riegel():
                    try:
                        job()
                    finally:
                        svc._sync_job_aktiv = False
                threading.Thread(target=_job_mit_riegel, daemon=True).start()
                if auswahl_pfad:
                    return self._send(200, json.dumps({"ok": True,
                                      "msg": f"transfer running ({len(_paare)} selected)"},
                                      ensure_ascii=False), "application/json")
                ziel = "Master → Frigate" if modus == "export" else "Frigate → Master"
                return self._send(200, json.dumps({"ok": True,
                                  "msg": f"Sync läuft ({ziel}), Seite in ~1 min neu laden"},
                                  ensure_ascii=False), "application/json")
            if pfad == "/vorschlaege_neu":                     # Bestands-Suche neu anstossen
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 8192)))
                    person = (d.get("person") or "").strip()
                    if person not in master_persons(cfg):
                        return self._send(400, json.dumps({"ok": False, "msg": "Person unbekannt"}),
                                          "application/json")
                    import anlernen
                    try:
                        os.remove(anlernen._vorschlaege_pfad(person))
                    except FileNotFoundError:
                        pass
                    svc.vorschlaege_starten(person)
                    return self._send(200, json.dumps({"ok": True,
                                      "msg": "Suche läuft, Seite lädt gleich neu"}, ensure_ascii=False),
                                      "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/vorschlag_aufnehmen":                 # Bestands-Vorschlaege uebernehmen
                try:
                    import anlernen
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    person = (d.get("person") or "").strip()
                    if person not in master_persons(cfg):
                        return self._send(400, json.dumps({"ok": False, "msg": "Person unbekannt"}),
                                          "application/json")
                    n_ok = 0
                    for it in (d.get("items") or []):
                        ok, _ = anlernen.vorschlag_aufnehmen(person, (it.get("eid") or "").strip(),
                                                             (it.get("datei") or "").strip())
                        if ok:
                            n_ok += 1
                    if n_ok:
                        svc.log(f"REFERENCE SEARCH: {n_ok} reference(s) adopted for {person}")
                        svc.qs_neu_starten()
                        svc.frigate_sync_export()
                    return self._send(200 if n_ok else 400,
                                      json.dumps({"ok": n_ok > 0, "msg": f"{n_ok} übernommen"},
                                                 ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/anlernen_benennen":                   # Cluster als Person anlernen (19.07.)
                try:
                    import anlernen
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    ids = [i for i in (d.get("ids") or "").split(",") if i]
                    person = (d.get("person") or "").strip()
                    # Issue #19: benenne_mit_abzug statt benenne — die Today-Karte lief
                    # ueber diesen Weg und liess die Gesichter im Unbekannt-Pool zurueck
                    # (Karte blieb stehen, Event-Akte blieb "unknown").
                    ok, msg, betroffen = anlernen.benenne_mit_abzug(ids, person)
                    if ok:
                        svc.log(f"ENROLL: {msg}")
                        svc.qs_neu_starten()               # nach Anlernen automatisch gegenpruefen
                        svc.frigate_sync_export()          # falls frigate_sync an: nach Frigate spiegeln
                        svc.anlern_nachpruefung_starten(person, betroffen)
                        msg += " — re-checking this pass's events in the background"
                    return self._send(200 if ok else 400,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                                      "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/personlauf/urteil":
                # PE2: Klick-Urteil (letzte Zeile je Datei gilt), fsync-los
                # bewusst — flush reicht, Muster Klick-Server.
                from core import personernte as _pe
                try:
                    _n1 = int(self.headers.get("Content-Length", 0))
                    _d1 = json.loads(self.rfile.read(min(_n1, 4096)) or b"{}")
                    _lid = str(_d1.get("lauf_id") or "")
                    _dat = str(_d1.get("datei") or "")
                    _urt = _d1.get("urteil")
                except (ValueError, TypeError):
                    _lid = _dat = ""
                    _urt = None
                if (_urt not in ("ok", "falsch") or not _lid or not _dat
                        or "/" in _lid or "/" in _dat or ".." in _lid
                        or ".." in _dat):
                    return self._send(400, json.dumps({"ok": False}),
                                      "application/json")
                _up = os.path.join(_pe.lauf_dir(cfg["data_dir"], _lid),
                                   "urteile.jsonl")
                if not os.path.isdir(os.path.dirname(_up)):
                    return self._send(404, json.dumps({"ok": False}),
                                      "application/json")
                with open(_up, "a") as _f:
                    _f.write(json.dumps({"datei": _dat, "urteil": _urt})
                             + "\n")
                    _f.flush()
                return self._send(200, json.dumps({"ok": True}),
                                  "application/json")
            if pfad == "/person/einstellungen":
                # .114: Schwelle + Feuer-Regel aus der Model-status-Seite —
                # Validierung (Grenzen) liegt in personmodell.einstellungen_setzen.
                from core import personmodell as _pm
                try:
                    _n6 = int(self.headers.get("Content-Length", 0))
                    _d6 = json.loads(self.rfile.read(min(_n6, 4096)) or b"{}")
                except (ValueError, TypeError):
                    return self._send(400, json.dumps({"ok": False, "msg": "bad json"}),
                                      "application/json")
                _ok6, _erg6 = _pm.einstellungen_setzen(cfg["data_dir"], _d6)
                return self._send(200 if _ok6 else 400, json.dumps(
                    {"ok": _ok6, "msg": _erg6 if isinstance(_erg6, str) else "saved"},
                    ensure_ascii=False), "application/json")
            if pfad == "/person/schalter":
                # PE4 Aktivierungs-Gate: Arm/Disarm nur mit Modell.
                from core import personmodell as _pm
                try:
                    _n5 = int(self.headers.get("Content-Length", 0))
                    _d5 = json.loads(self.rfile.read(min(_n5, 1024)) or b"{}")
                    _an = bool(_d5.get("scharf"))
                except (ValueError, TypeError):
                    return self._send(400, json.dumps({"ok": False}),
                                      "application/json")
                _ok5, _erg5 = _pm.scharf_setzen(cfg["data_dir"], _an)
                if not _ok5:
                    return self._send(409, json.dumps(
                        {"ok": False, "msg": str(_erg5)}),
                        "application/json")
                return self._send(200, json.dumps({"ok": True,
                                                   "scharf": _an}),
                                  "application/json")
            if pfad == "/personlauf/loeschen":
                # PE2b: Einzelbild- oder Lauf-Loeschung (Crop weg, Manifest-
                # Grabstein bleibt; neuer Lauf kann jederzeit neu ernten).
                # .146 (User 07.08.: 'fremde muessen auch geloescht werden
                # koennen'): {"fremd": <datei>} loescht aus personlern/fremd/
                # — Containment + Endungs-Vertrag, danach dasselbe
                # Re-Training wie bei Personen-Bildern (FREMD_MIN-Regel
                # greift von selbst, faellt der Pool unter 5).
                from core import personernte as _pe
                try:
                    _n2 = int(self.headers.get("Content-Length", 0))
                    _d2 = json.loads(self.rfile.read(min(_n2, 4096)) or b"{}")
                    _lid = str(_d2.get("lauf_id") or "")
                    _dat = _d2.get("datei")
                    _frd = _d2.get("fremd")
                except (ValueError, TypeError):
                    _lid, _dat, _frd = "", None, None
                if _frd is not None:
                    _frd = str(_frd)
                    _wurz = os.path.normpath(os.path.join(
                        cfg["data_dir"], "personlern", "fremd"))
                    _voll = os.path.normpath(os.path.join(_wurz, _frd))
                    if (not _voll.startswith(_wurz + os.sep)
                            or not _frd.lower().endswith(_reg.BILD_ENDUNGEN)
                            or not os.path.isfile(_voll)):
                        return self._send(400, json.dumps({"ok": False}),
                                          "application/json")
                    os.remove(_voll)
                    # .147: Grabstein im Ursprungs-Lauf, damit der
                    # Bestands-Skip das Event WIEDER anbieten darf.
                    _pe.fremd_grabstein(cfg["data_dir"], _frd)
                    _n3 = 1
                elif (not _lid or "/" in _lid or ".." in _lid
                        or (_dat is not None
                            and ("/" in str(_dat) or ".." in str(_dat)))):
                    return self._send(400, json.dumps({"ok": False}),
                                      "application/json")
                else:
                    _n3 = _pe.loeschen(cfg["data_dir"], _lid,
                                       str(_dat) if _dat else None)
                # Ganzer-Lauf-Verwurf des Laufs, der gerade auf Review
                # wartet (User 04.08.: schlechtes Ergebnis muss komplett
                # verwerfbar sein) -> Wizard wieder freigeben.
                if _frd is None and _dat is None:
                    from core import personlauf as _pl
                    _zv = _pl.zustand_lesen(cfg["data_dir"])
                    if _zv and str(_zv.get("lauf_id")) == _lid \
                            and _zv.get("phase") == "abnahme":
                        _zv.update(phase="fertig", abgenommen=0,
                                   verworfen=_n3)
                        _pl.zustand_schreiben(cfg["data_dir"], _zv)
                # PE3: Loeschung wirkt sofort -> Re-Training (Sekunden)
                import threading as _th

                def _pm_train2():
                    try:
                        from core import personmodell as _pm
                        _pm.trainieren(cfg["data_dir"])
                    except Exception as e:
                        # .141 Panel-MUSS: der Fehlschlag wird SICHTBAR
                        # (Modell-Karte), nicht nur eine Container-Logzeile —
                        # die Karte zeigte sonst den Alt-Stand als aktuell.
                        print(f"[personmodell] Training fehlgeschlagen: {e}",
                              flush=True)
                        try:
                            from core import personmodell as _pmf
                            _pmf.fehler_vermerken(
                                cfg["data_dir"], f"{type(e).__name__}: {e}")
                        except Exception:
                            pass
                _th.Thread(target=_pm_train2, daemon=True,
                           name="personmodell").start()
                return self._send(200, json.dumps({"ok": True,
                                                   "geloescht": _n3}),
                                  "application/json")
            if pfad == "/personlauf/abnahme_fertig":
                # PE2-Abschluss (User: "wo bestaetige ich das?"): Urteile in
                # den Bestand stempeln, Lauf -> fertig, Formular wieder frei.
                from core import personlauf as _pl
                from core import personernte as _pe
                _zf = _pl.zustand_lesen(cfg["data_dir"])
                if not _zf or _zf.get("phase") != "abnahme":
                    return self._send(409, json.dumps(
                        {"ok": False, "msg": "no run awaiting review"}),
                        "application/json")
                _lid = str(_zf.get("lauf_id") or "")
                _falsch = set()
                _up = os.path.join(_pe.lauf_dir(cfg["data_dir"], _lid),
                                   "urteile.jsonl")
                if os.path.exists(_up):
                    for l in open(_up):
                        if l.strip():
                            _u = json.loads(l)
                            (_falsch.add if _u["urteil"] == "falsch"
                             else _falsch.discard)(_u["datei"])
                _nok, _nfalsch = _pe.abnahme_anwenden(cfg["data_dir"], _lid,
                                                      _falsch)
                _zf.update(phase="fertig", abgenommen=_nok,
                           verworfen=_nfalsch)
                # .147: bestaetigte FREMD-Bilder wandern in den Pool —
                # das folgende Training liest ihn von selbst.
                if _zf.get("person") == "FREMD":
                    _zf["fremd_uebernommen"] = _pe.fremd_uebernehmen(
                        cfg["data_dir"], _lid)
                _pl.zustand_schreiben(cfg["data_dir"], _zf)
                # PE3: nach jedem Review-Abschluss automatisch trainieren
                import threading as _th

                def _pm_train():
                    try:
                        from core import personmodell as _pm
                        _pm.trainieren(cfg["data_dir"])
                    except Exception as e:
                        # .141 Panel-MUSS: der Fehlschlag wird SICHTBAR
                        # (Modell-Karte), nicht nur eine Container-Logzeile —
                        # die Karte zeigte sonst den Alt-Stand als aktuell.
                        print(f"[personmodell] Training fehlgeschlagen: {e}",
                              flush=True)
                        try:
                            from core import personmodell as _pmf
                            _pmf.fehler_vermerken(
                                cfg["data_dir"], f"{type(e).__name__}: {e}")
                        except Exception:
                            pass
                _th.Thread(target=_pm_train, daemon=True,
                           name="personmodell").start()
                return self._send(200, json.dumps(
                    {"ok": True, "abgenommen": _nok, "verworfen": _nfalsch}),
                    "application/json")
            if pfad == "/personlauf_abbruch":
                # PE1 (User-Wunsch 04.08.): laufenden Person-Learn-Lauf
                # stoppen — Geerntetes bleibt, fahren() liest die Phase
                # vor jedem Event.
                from core import personlauf as _pl
                _za = _pl.zustand_lesen(cfg["data_dir"])
                if not _za or _za.get("phase") not in ("vorbereitung",
                                                       "ernte"):
                    return self._send(409, json.dumps(
                        {"ok": False, "msg": "no active run"}),
                        "application/json")
                _za["phase"] = "abbruch"
                _pl.zustand_schreiben(cfg["data_dir"], _za)
                return self._send(200, json.dumps({"ok": True}),
                                  "application/json")
            if pfad == "/personlauf_start":
                # PE1 B4 (stufe2.md): Person-Learn-Lauf starten — Bindung
                # EINMAL beim Anlegen (core/personlauf), Ernte inline im
                # Hintergrund-Thread; EIN Lauf zur Zeit (Zustands-Phase).
                # Worker-Job-Umbau folgt mit dem Einback-Port (PE1 B5).
                from core import personlauf as _pl
                try:
                    _n0 = int(self.headers.get("Content-Length", 0))
                    _d = json.loads(self.rfile.read(min(_n0, 4096)) or b"{}")
                    _ev = int(_d.get("events") or 0)
                    _person = str(_d.get("person") or "").strip()
                except (ValueError, TypeError):
                    _ev, _person = 0, ""
                if _ev <= 0 or _ev > svc.LERNLAUF_EVENTS_MAX:
                    return self._send(400, json.dumps(
                        {"ok": False,
                         "msg": f"events must be 1..{svc.LERNLAUF_EVENTS_MAX}"}),
                        "application/json")
                _z0 = _pl.zustand_lesen(cfg["data_dir"])
                # aktiv = Phase sagt aktiv UND der Thread lebt wirklich —
                # nach einem Dienst-Neustart ist die Disk-Phase sonst eine
                # Geisterbremse (Neustart-Resume laeuft ueber die eids).
                _lebt = bool(getattr(svc, "_personlauf_thread", None)
                             and svc._personlauf_thread.is_alive())
                if _z0 and _z0.get("phase") in ("vorbereitung", "ernte") \
                        and _lebt:
                    return self._send(409, json.dumps(
                        {"ok": False,
                         "msg": "a person-learn run is already active"}),
                        "application/json")
                import threading as _th
                # Sofort-Feedback (User-Fund 04.08.: Bindung dauert 1-2 min,
                # die Seite zeigte solange den ALTEN Zustand): Vorbereitungs-
                # Phase schreiben, BEVOR der Thread startet.
                _pl.zustand_schreiben(cfg["data_dir"], {
                    "schema": 1, "phase": "vorbereitung", "person": _person,
                    "wunsch_n": _ev, "ts": time.time()})

                # Echtes Resume (Ehrlichkeits-Fix 04.08.): gleicher Auftrag
                # nach Unterbrechung setzt DENSELBEN Lauf fort (eids-Skip
                # greift nur innerhalb eines Laufs), sonst neuer Lauf.
                _wieder = bool(_z0 and not _lebt and _z0.get("events_liste")
                               and _z0.get("phase") in ("vorbereitung",
                                                        "ernte")
                               and _z0.get("person") == _person
                               and _z0.get("wunsch_n") == _ev)

                def _pl_lauf():
                    try:
                        if _wieder:
                            _z = dict(_z0, phase="ernte")
                            _pl.zustand_schreiben(cfg["data_dir"], _z)
                        else:
                            _z = _pl.anlegen(cfg["data_dir"], _ev, _person)

                        def _fs(k, von, okz, bilder):
                            _z["fortschritt"] = {"events": k, "von": von,
                                                 "bilder": bilder,
                                                 "ts": time.time()}
                            _pl.zustand_schreiben(cfg["data_dir"], _z)
                        _pl.fahren(cfg["data_dir"], _z, _fs)
                    except Exception as e:
                        try:
                            _z2 = _pl.zustand_lesen(cfg["data_dir"]) \
                                or {"schema": 1}
                            _z2["phase"] = "fehler"
                            _z2["fehler"] = f"{type(e).__name__}: {str(e)[:180]}"
                            _pl.zustand_schreiben(cfg["data_dir"], _z2)
                        except Exception:
                            pass
                svc._personlauf_thread = _th.Thread(
                    target=_pl_lauf, daemon=True, name="personlauf")
                svc._personlauf_thread.start()
                return self._send(200, json.dumps({"ok": True}),
                                  "application/json")
            if pfad == "/lernlauf_start":
                # E2: Lauf anlegen — atomar via core.lernlauf, UNTER dem Starter-Lock
                # (zwei gleichzeitige POSTs waren ein check-then-act-Rennen, F2.2).
                # erntefreigabe kennzeichnet: dieser Lauf DARF wirklich ernten
                # (Abgrenzung zu E1-Shadow-Altzustaenden beim Boot-Resume).
                from core import lernlauf as _ll
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 4096)) or b"{}")
                    ev = int(d.get("events") or 0)
                    # .83 (Task #10): Abtastrate JE LAUF waehlbar; nur der
                    # Whitelist-Bereich zaehlt, sonst gilt der Config-Default.
                    lauf_fps = float(d.get("fps") or 0)
                    if not (1 <= lauf_fps <= 30):
                        lauf_fps = 0
                except (ValueError, TypeError):
                    ev = 0
                    lauf_fps = 0
                if ev <= 0 or ev > svc.LERNLAUF_EVENTS_MAX:
                    return self._send(400, json.dumps({"ok": False,
                                      "msg": f"events must be 1..{svc.LERNLAUF_EVENTS_MAX}"}),
                                      "application/json")
                with svc._lernlauf_start_lock:
                    # Phasen-Wache (F5.3): ein alter Browser-Tab darf einen
                    # fortgeschrittenen Lauf nicht still zuruecksetzen.
                    bestand, _le = _ll.lauf_lesen(cfg["data_dir"])
                    if bestand and bestand.get("phase") not in (None, "vorbereitung"):
                        # .83 (Widerleger): ein FERTIGER Anker-Lauf blockiert den naechsten
                        # nicht mehr (vorher war Abbruch+Trash der einzige Weg zum neuen
                        # Lauf). Der alte Laufordner + seine Anker BLEIBEN liegen —
                        # nur der Abbruch trasht.
                        bst = str((bestand.get("fortschritt") or {}).get("status", ""))
                        fertig_anker = (bestand.get("phase") == "anker"
                                        and bst.startswith(("anchors ready", "anchors: none")))
                        if not fertig_anker:
                            return self._send(409, json.dumps({"ok": False,
                                              "msg": f"a run is already in phase "
                                                     f"'{bestand.get('phase')}' — abort it first"}),
                                              "application/json")
                        svc.log(f"learning run {bestand.get('lauf_id')} is complete — "
                                "starting a new run, keeping its folder and anchors")
                    # Laufende Arbeits-Threads nicht mit neuem Umfang ueberschreiben.
                    # .83: auch der Anker-Thread zaehlt (Widerleger: Abbruch + sofortiger
                    # Neustart liess den alten Thread in den NEUEN Lauf-Store schreiben).
                    for tn in ("_lernlauf_prep_thread", "_lernlauf_ernte_thread",
                               "_lernlauf_anker_thread"):
                        t = getattr(svc, tn, None)
                        if t and t.is_alive():
                            return self._send(409, json.dumps({"ok": False,
                                              "msg": "the previous run is still finishing "
                                                     "its current event — try again in a "
                                                     "moment"}), "application/json")
                    try:
                        with _ll.store_lock(cfg["data_dir"]):     # .87: Anlage unter dem Store-Lock
                            _ll.lauf_schreiben(cfg["data_dir"], dict({"phase": "vorbereitung",
                                                             "events": ev,
                                                             "alle": bool(d.get("alle")),
                                                             "erntefreigabe": True,
                                                             "ts": round(time.time(), 1),
                                                             "fortschritt": {}},
                                                            **({"fps_sample": lauf_fps}
                                                               if lauf_fps else {})))
                    except OSError as e:           # F2.7: voller Datentraeger u.ae. LAUT
                        svc.log(f"learning run NOT created: {e}")
                        return self._send(500, json.dumps({"ok": False,
                                          "msg": f"could not write run state: {e}"}),
                                          "application/json")
                    svc.log(f"learning run created: scope {ev} events")
                    svc.lernlauf_vorbereiten_starten(ev, alle_modus=bool(d.get("alle")))
                return self._send(200, json.dumps({"ok": True, "msg": "run created"}),
                                  "application/json")
            if pfad == "/lernlauf_abbruch":
                # E2: Abbruch = Zustand entfernen + geerntete Artefakte nach
                # state/lernlauf/trash/ verschieben (§6 Speicher-Reste: gesammelte
                # Gesichts-Crops bleiben nie unsichtbar liegen; endgueltig loeschen
                # ist der Trash-Weg der Benennungs-Etappe). Ein GERADE laufendes
                # Event erntet im Hintergrund zu Ende; die Schleife erkennt den
                # Abbruch danach und bucht nichts mehr.
                from core import lernlauf as _ll
                # .87 (Forensik-Fund 6): Loeschen UNTER store_lock — sonst konnte das
                # remove ins fortschreiben-Fenster eines Arbeits-Threads fallen und
                # der abgebrochene Lauf kam als Zombie zurueck.
                with _ll.store_lock(cfg["data_dir"]):
                    z, _le = _ll.lauf_lesen(cfg["data_dir"])
                    p = os.path.join(cfg["data_dir"], "state", "lernlauf.json")
                    if os.path.exists(p):
                        os.remove(p)
                verschoben = ""
                lid = (z or {}).get("lauf_id")
                if lid:
                    quelle = os.path.join(cfg["data_dir"], "state", "lernlauf", lid)
                    if os.path.isdir(quelle):
                        ziel = os.path.join(cfg["data_dir"], "state", "lernlauf",
                                            "trash", lid)
                        try:
                            os.makedirs(os.path.dirname(ziel), exist_ok=True)
                            if os.path.exists(ziel):
                                ziel += "-" + str(int(time.time()))
                            os.replace(quelle, ziel)
                            verschoben = "; harvested material moved to trash"
                        except OSError as e2:
                            svc.log(f"learning run abort: could not move {lid} "
                                    f"to trash ({e2})")
                    # .83 (Widerleger A11): die anker.jsonl-Zeilen des abgebrochenen
                    # Laufs raeumen — sein Material liegt im Trash, die Zeilen waeren
                    # Waisen mit toten Crop-Pfaden ('anchors so far' zaehlte sie mit).
                    try:
                        from core import anker as _ank
                        _ank.anker_lauf_schreiben(cfg["data_dir"], [], lid)
                    except Exception as e3:
                        svc.log(f"learning run abort: could not clean anchors of {lid} ({e3})")
                svc.log(f"learning run aborted (state removed{verschoben})")
                return self._send(200, json.dumps(
                    {"ok": True, "msg": "aborted — a running event may still finish "
                                        "in the background"}), "application/json")
            if pfad == "/konfig":                              # Konfigblatt speichern (AP5)
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 8192)))
                    ok, msg = svc.config_schreiben(d)
                    return self._send(200 if ok else 400,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                                      "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/benachrichtigung_speichern":          # Notifications-Reiter committen (Kanaele + Secrets)
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 16384)))
                    ok, msg = svc.notif_speichern(d)
                    return self._send(200 if ok else 400,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad in ("/live_speichern", "/live_schalter", "/live_test",
                        "/live_messung", "/live_verstecken"):
                # Live-Reiter (Phase 2): duenne Maentel, Logik/Riegel in
                # core/livewache (live_speichern/live_schalter serverseitig —
                # ein direkter POST kommt hier am UI-Grau vorbei und MUSS am
                # selben Riegel scheitern, Bauplan §2.4).
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 16384)) or b"{}")
                except Exception:
                    return self._send(400, json.dumps(
                        {"ok": False, "msg": "bad json"}), "application/json")
                kamera = str(d.get("kamera") or "")
                if pfad == "/live_speichern":
                    ok, msg = svc.live_speichern(kamera, d)
                elif pfad == "/live_schalter":
                    ok, msg = svc.live_schalter(kamera, bool(d.get("enabled")))
                elif pfad == "/live_test":
                    ok, msg = svc.live_test_starten(kamera)
                elif pfad == "/live_verstecken":
                    ok, msg = svc.live_verstecken(kamera,
                                                  bool(d.get("versteckt")))
                else:
                    ok, msg = svc.live_messung_starten(kamera)
                return self._send(200 if ok else 400,
                                  json.dumps({"ok": ok, "msg": msg},
                                             ensure_ascii=False),
                                  "application/json")
            if pfad.startswith("/vision/"):
                try:                                           # Vision detect: duenne Maentel, Logik in core/
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 262144)) or b"{}")
                except Exception:
                    return self._send(400, json.dumps({"ok": False, "msg": "bad json"}), "application/json")
                if pfad == "/vision/schalter":                  # E4-Gate: 409 + Klartext, was fehlt
                    ok, msg = svc.vision_schalter(bool(d.get("aktiv")))
                    return self._send(200 if ok else 409,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False), "application/json")
                if pfad == "/vision/galerie/weg":               # Zelle ablehnen -> Nachruecker
                    ok, msg = svc.vision_galerie_weg(d.get("person") or "", d.get("schluessel") or "",
                                                     d.get("reihe") or "", d.get("belegt") or [],
                                                     d.get("reihe_belegt") or [])
                elif pfad == "/vision/galerie/abnahme":
                    ok, msg = svc.vision_galerie_abnahme(d.get("person") or "", d.get("groesse") or 0,
                                                         d.get("auswahl") or [])
                elif pfad == "/vision/galerie/vergessen":       # Ablehn-Gedaechtnis zuruecknehmen
                    ok, msg = svc.vision_galerie_vergessen(d.get("person") or "")
                elif pfad == "/vision/nachanalyse":             # .161: Durchgang erneut analysieren (Material fehlt)
                    ok, msg = svc.vision_nachanalyse(d.get("pass_key") or "")
                elif pfad == "/vision/urteil":                  # V4: Vision-Lauf fuer EINEN Durchgang (Szenario-Test)
                    # .164: die beiden Felder des Testlaufs fahren mit — sie
                    # gelten NUR fuer diesen Lauf (kein Config-Schreibweg).
                    ok, msg = svc.vision_urteil_anstossen(
                        str(d.get("pass_key") or ""), manuell=True,
                        lauf_regeln={"bilder_je_pass": d.get("zellen"),
                                     "min_voten": d.get("voten"),
                                     "doppellauf": d.get("doppellauf")})
                elif pfad == "/vision/schluessel":              # Key-Sofortpruefung (Modell-Liste, kein Bild)
                    ok, msg = svc.vision_schluessel(d)
                elif pfad in ("/vision/test", "/vision/konfig"):
                    ok, msg = (svc.vision_test(d) if pfad == "/vision/test"
                               else svc.vision_speichern(d))
                else:
                    return self._send(404, json.dumps({"ok": False, "msg": "unknown"}), "application/json")
                return self._send(200 if ok else 400,
                                  json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False), "application/json")
            if pfad == "/config_wiederherstellen":             # Config-Store aus Upload zurueckspielen (UI-Restore)
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    raw = self.rfile.read(min(n, 1000000))     # 1 MB Deckel
                    ok, msg = svc.config_wiederherstellen(raw)
                    return self._send(200 if ok else 400,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/backup_voll_wiederherstellen":   # PE6 Full-Restore (Body = rohes tar.gz)
                try:
                    import tempfile
                    n = int(self.headers.get("Content-Length", 0))
                    if n <= 0 or n > 8 * 1024 ** 3:
                        return self._send(400, json.dumps(
                            {"ok": False, "msg": "missing or oversized upload"}), "application/json")
                    with tempfile.NamedTemporaryFile(prefix=".restore-up-", suffix=".tar.gz",
                                                     dir=svc.cfg["data_dir"], delete=False) as f:
                        tmp, rest = f.name, n
                        while rest > 0:                    # stueckweise: 100+-MB-Archive
                            buf = self.rfile.read(min(rest, 512 * 1024))
                            if not buf:
                                break
                            f.write(buf)
                            rest -= len(buf)
                    if rest > 0:
                        os.unlink(tmp)
                        return self._send(400, json.dumps(
                            {"ok": False, "msg": "upload truncated"}), "application/json")
                    try:
                        ok, msg = svc.voll_wiederherstellen(tmp)
                    finally:
                        try:
                            os.unlink(tmp)
                        except OSError:
                            pass
                    return self._send(200 if ok else 400,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                                      "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad in ("/test_pushover", "/test_telegram", "/test_mqtt"):   # Test-Versand je Kanal
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 8192))) if n else {}
                except Exception:
                    d = {}
                ok, msg = svc.notif_test(pfad.split("_", 1)[1], d)
                return self._send(200 if ok else 400,
                                  json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False), "application/json")
            if pfad == "/setup_speichern":                     # Setup-Wizard committen (User 22.07.)
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    updates = {}
                    url = (d.get("frigate_url") or "").strip()
                    if url:
                        _ok, _res = pruefe_url(url)        # startswith("http") liess 'httpx://' & Co durch
                        if not _ok:
                            return self._send(400, json.dumps({"ok": False, "msg": f"Frigate URL: {_res}"},
                                                              ensure_ascii=False), "application/json")
                        url = _res
                        updates["frigate_url"] = url
                    backend = (d.get("backend") or "").strip()
                    from core.registry import alle_wizard_werte
                    ALLOWED_BK = alle_wizard_werte()   # P3.1: statische Whitelist aus der Registry
                    if backend:
                        if backend not in ALLOWED_BK:
                            return self._send(400, json.dumps({"ok": False, "msg": f"unknown backend '{backend}'"}), "application/json")
                        updates["backend"] = backend
                    if d.get("kameras") is not None:               # gegen die REALE Frigate validieren (neue URL falls gesetzt)
                        kams, err = frigate_cameras({**cfg, **({"frigate_url": url} if url else {})}, force=True)
                        if err or not kams:
                            return self._send(400, json.dumps({"ok": False, "msg": f"Frigate cameras not available: {err or 'none'}"}, ensure_ascii=False), "application/json")
                        neu = {}
                        for name, k in (d.get("kameras") or {}).items():
                            if name not in kams:
                                continue
                            zonen = [z for z in (k.get("zonen") or []) if z in kams[name]["zones"]]
                            verw = bool(k.get("verwenden", True))
                            if not kams[name]["enabled"]:
                                verw = True
                            neu[name] = {"verwenden": verw, "zonen": zonen}
                        updates["kameras"] = neu
                    if "frigate_read_only" in d:               # Wizard-Schritt 5 'write back?' (Vorbelegung = Ist-Wert)
                        updates["frigate_read_only"] = bool(d.get("frigate_read_only"))
                    updates["setup_done"] = True
                    store = _lade_config_store(cfg)
                    store.update(updates)
                    p = _config_store_pfad(cfg)
                    _store_schreiben(p, store)      # atomar + fsync, unter _cfg_lock (5 Schreibwege)
                    with open(os.path.join(cfg["data_dir"], "config", "config_audit.jsonl"), "a") as f:
                        f.write(json.dumps({"ts": round(time.time(), 1), "setup": {
                            k: (f"{len(v)} cams" if k == "kameras" else v) for k, v in updates.items()}},
                            ensure_ascii=False) + "\n")
                        f.flush()
                    svc.log(f"SETUP WIZARD saved: {list(updates.keys())} — restart after the current analysis")

                    svc.neustart("Setup-Wizard")
                    return self._send(200, json.dumps({"ok": True, "msg": "Setup saved — restarting"}, ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}, ensure_ascii=False), "application/json")
            if pfad == "/kameras_speichern":                   # Kamera-Blatt speichern (Phase 2b)
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    kams, err = frigate_cameras(cfg)
                    if err or not kams:
                        return self._send(400, json.dumps({"ok": False,
                            "msg": f"Frigate cameras not available: {err or 'none'}"},
                            ensure_ascii=False), "application/json")
                    neu = {}
                    for name, k in (d.get("kameras") or {}).items():
                        if name not in kams:                   # nur echte Frigate-Kameras
                            continue
                        zonen = [z for z in (k.get("zonen") or []) if z in kams[name]["zones"]]
                        verw = bool(k.get("verwenden", True))
                        if not kams[name]["enabled"]:          # Review 21.07.: eine in Frigate gerade
                            verw = True                        # deaktivierte Kamera NICHT als verifyd-off
                        neu[name] = {"verwenden": verw, "zonen": zonen}   # einfrieren (Re-Enable laeuft)
                    store = _lade_config_store(cfg)
                    store["kameras"] = neu
                    p = _config_store_pfad(cfg)
                    _store_schreiben(p, store)      # atomar + fsync, unter _cfg_lock (5 Schreibwege)
                    with open(os.path.join(cfg["data_dir"], "config", "config_audit.jsonl"), "a") as f:
                        f.write(json.dumps({"ts": round(time.time(), 1), "kameras": neu},
                                           ensure_ascii=False) + "\n")
                        f.flush()
                    svc.log(f"CAMERA SHEET saved: {len(neu)} cameras — restart after the current analysis")

                    svc.neustart("Kamera-Blatt")
                    return self._send(200, json.dumps({"ok": True,
                        "msg": f"{len(neu)} cameras saved — restarting"}, ensure_ascii=False),
                        "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/lernlauf/benennen":                   # E4a Zug 2b: Cluster benennen
                # Duenner Mantel (I1): Namens-/Kollisions-Logik im Modul, Schreibweg
                # AUSSCHLIESSLICH core/lernlauf.anker_aktualisieren (Lock+atomar+Wache).
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 262144)))
                    from core import lernlauf as _ll, benennung as _bn
                    aid = str(d.get("anker_id") or "")
                    name = _ll.person_norm(d.get("person"))
                    if not (name and re.match(_ll.PERSON_RE, name)):
                        return self._send(400, json.dumps(
                            {"ok": False, "msg": "invalid person name (2-40 letters, digits, space, -)"}), "application/json")
                    saetze, _k = _ll.anker_lesen(cfg["data_dir"])
                    satz = next((s for s in saetze if s.get("anker_id") == aid), None)
                    if satz is None:
                        return self._send(404, json.dumps({"ok": False, "msg": "unknown anchor"}), "application/json")
                    quelle = _bn.personen_quelle(
                        master_persons(cfg),
                        [a for a in saetze if a.get("anker_id") != aid], _ll.person_norm)
                    koll = _bn.namens_kollision(name, quelle, _ll.person_norm)
                    if koll and koll != name and not d.get("bestaetigt"):
                        # Namens-Ebene (Bauplan 4c): Rueckfrage statt stillem Zweit-Eintrag.
                        return self._send(200, json.dumps({"ok": False, "kollision": koll}), "application/json")
                    gew = {str(x) for x in (d.get("gewaehlt") or [])}
                    mit = [dict(m, gewaehlt=(str(m.get("datei", "")).rsplit("/", 1)[-1] in gew))
                           for m in (satz.get("mitglieder") or [])]
                    tag = {"modell": (mit[0].get("modell", "") if mit else ""),
                           "k_je_bin": cfg["benennung_k_je_bin"],
                           "yaw_grenze": cfg["benennung_yaw_grenze"],
                           "dup_sim": cfg["benennung_dup_sim"]}
                    _ll.anker_aktualisieren(
                        cfg["data_dir"], aid, person=name, status="benannt", mitglieder=mit,
                        auswahl={"ts": round(time.time(), 1), "n": len(gew), "bedingungs_tag": tag})
                    svc.log(f"anchor {aid} named '{name}' ({len(gew)} of {len(mit)} images "
                            "selected) — adoption ships with E4b")
                    return self._send(200, json.dumps(
                        {"ok": True, "msg": f"named '{name}' — {len(gew)} images selected, adoption pending"},
                        ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/lernlauf/verwerfen":                  # Dismiss mit Gedaechtnis (User 05.08.)
                # Duenner Mantel: Status+Crop-Loeschung in core/lernlauf.anker_verwerfen;
                # Zeile+Zentroid bleiben, damit Wiederernten still erben (core/anker).
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    from core import lernlauf as _ll
                    aid = str(d.get("anker_id") or "")
                    saetze, _k = _ll.anker_lesen(cfg["data_dir"])
                    satz = next((s for s in saetze if s.get("anker_id") == aid), None)
                    if satz is None or satz.get("status") != "unbenannt":
                        return self._send(400, json.dumps(
                            {"ok": False, "msg": "only unnamed clusters can be dismissed"}),
                            "application/json")
                    _s2, ncrops = _ll.anker_verwerfen(cfg["data_dir"], aid)
                    return self._send(200, json.dumps(
                        {"ok": True, "msg": f"dismissed — {ncrops} images removed, "
                                            "re-harvests of these events stay quiet"},
                        ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/lernlauf/lauf_loeschen":              # Lauf KOMPLETT loeschen (User 05.08., 2. Fassung)
                # Duenner Mantel: Loesch-Regel + Schreibweg in
                # core/lernlauf.lauf_loeschen (ALLE Zeilen des Laufs + Ordner hart
                # weg, kein trash; uebernommene Referenzen sind Kopien in faces/).
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    from core import lernlauf as _ll
                    lid = str(d.get("lauf_id") or "")
                    if not re.match(r"^L[\w]+$", lid):
                        return self._send(400, json.dumps(
                            {"ok": False, "msg": "invalid run id"}), "application/json")
                    lauf, _f = _ll.lauf_lesen(cfg["data_dir"])
                    # Review-MUSS .125: 'fertig' wird vom Lernlauf nie geschrieben —
                    # abgeschlossen entscheidet die zentrale Quelle lauf_abgeschlossen
                    # (Anker-Phase durch), sonst blockte der Knopf den neuesten Lauf immer.
                    if lauf and str(lauf.get("lauf_id") or "") == lid \
                            and not _ll.lauf_abgeschlossen(lauf):
                        return self._send(400, json.dumps(
                            {"ok": False, "msg": "this run is still active — abort it first"}),
                            "application/json")
                    z = _ll.lauf_loeschen(cfg["data_dir"], lid)
                    if not z["entfernt"] and not z["dateien"] and z["ordner"]:
                        return self._send(200, json.dumps(
                            {"ok": True, "msg": f"nothing found for run {lid} — already deleted?"},
                            ensure_ascii=False), "application/json")
                    detail = ", ".join(t for t in (
                        f"{z['benannt']} named/adopted" if z["benannt"] else "",
                        f"{z['verworfen']} dismissed" if z["verworfen"] else "") if t)
                    # Ehrliche Bilanz (Review .125): nie eine Loeschung behaupten,
                    # die nicht stattfand — rest/ordner kommen nachgezaehlt aus dem Kern.
                    warn = ("" if z["ordner"] else
                            "; WARNING: run folder could not be fully removed"
                            + (f" — {z['rest']} file(s) remain on disk" if z["rest"] else ""))
                    svc.log(f"RUN DELETED: {lid} — {z['entfernt']} cluster(s)"
                            + (f" ({detail})" if detail else "")
                            + f", {z['dateien']} file(s){warn}")
                    return self._send(200, json.dumps(
                        {"ok": True, "msg": f"run {lid} deleted: {z['entfernt']} cluster(s)"
                                            + (f" ({detail})" if detail else "")
                                            + f" and {z['dateien']} file(s) permanently removed"
                                            + warn},
                        ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/lernlauf/alte_loeschen":              # Sammel-Loeschung (User 05.08.: EIN OK)
                # Duenner Mantel: Auswahl (alle ausser dem neuesten, aktiver Lauf
                # wird uebersprungen) + Loeschung in core/lernlauf.alte_laeufe_loeschen.
                try:
                    from core import lernlauf as _ll
                    z, weg, behalten = _ll.alte_laeufe_loeschen(cfg["data_dir"])
                    if not weg:
                        return self._send(200, json.dumps(
                            {"ok": True, "msg": "nothing to delete — only one run in the store"},
                            ensure_ascii=False), "application/json")
                    warn = ("" if z["ordner"] else
                            "; WARNING: not every run folder could be fully removed"
                            + (f" — {z['rest']} file(s) remain on disk" if z["rest"] else ""))
                    svc.log(f"OLD RUNS DELETED: {', '.join(weg)} — {z['entfernt']} cluster(s), "
                            f"{z['dateien']} file(s); kept {behalten}{warn}")
                    return self._send(200, json.dumps(
                        {"ok": True, "msg": f"{z['laeufe']} old run(s) deleted: {z['entfernt']} "
                                            f"cluster(s) and {z['dateien']} file(s) permanently "
                                            f"removed; kept newest run {behalten}" + warn},
                        ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/lernlauf/uebernehmen":                # E4b: Uebernahme in den Master
                # Duenner Mantel: Plan/Dedup/Tag-Pruefung/Alles-oder-nichts im Modul
                # (core/uebernahme), Nacharbeit = derselbe Weg wie Pool-Enrollment.
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    from core import lernlauf as _ll, uebernahme as _ue
                    aid = str(d.get("anker_id") or "")
                    saetze, _k = _ll.anker_lesen(cfg["data_dir"])
                    satz = next((s for s in saetze if s.get("anker_id") == aid), None)
                    if satz is None or satz.get("status") != "benannt":
                        return self._send(400, json.dumps(
                            {"ok": False, "msg": "anchor is not named (or unknown)"}), "application/json")
                    person = satz.get("person")
                    werte = {"k_je_bin": cfg["benennung_k_je_bin"],
                             "yaw_grenze": cfg["benennung_yaw_grenze"],
                             "dup_sim": cfg["benennung_dup_sim"]}
                    ab = _ue.bedingungs_tag_pruefen(satz, werte)
                    if ab and not d.get("bestaetigt"):
                        return self._send(200, json.dumps({"ok": False, "tag_abweichung": ab}), "application/json")
                    plan = _ue.plan_bauen(satz, cfg["benennung_dup_sim"],
                                          _ue.adoptierte_embs(cfg["data_dir"], person))
                    if not plan["aufnehmen"]:
                        if not plan["uebersprungen"]:
                            return self._send(400, json.dumps(
                                {"ok": False, "msg": "nothing selected — tick at least one image to adopt"}), "application/json")
                        # #17 (Tokn59): ALLE gewaehlten Bilder sind Beinahe-Duplikate schon
                        # uebernommener Referenzen — das Dedup-Urteil ist richtig, aber kein
                        # Fehler: Cluster ehrlich als uebernommen abschliessen (0 neue Dateien,
                        # das Protokoll weist die Entscheidung aus) statt 'error' zu zeigen.
                        # Phantom-Wache (Review-MUSS .127): abschliessen NUR, wenn die Person
                        # wirklich noch Referenzbilder auf der Platte hat — adoptierte_embs
                        # filtert Geloeschtes zwar schon, aber dieser Zustand darf nie still
                        # als Erfolg enden (sonst Person mit 0 Referenzen 'fertig' markiert).
                        _rd = os.path.join(cfg["data_dir"], "faces", person)
                        if not (os.path.isdir(_rd) and any(
                                f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                                for f in os.listdir(_rd))):
                            return self._send(400, json.dumps(
                                {"ok": False, "msg": "dedup matched only references that no "
                                                     "longer exist on disk — please retry the "
                                                     "adoption; if this persists, report it"}),
                                "application/json")
                        _ue.protokoll_anhaengen(cfg["data_dir"], {
                            "ts": round(time.time(), 1), "anker_id": aid, "person": person,
                            "dateien": [], "uebersprungen": plan["uebersprungen"],
                            "manuelle_refs_ungeprueft": True,
                            "bedingungs_tag": (satz.get("auswahl") or {}).get("bedingungs_tag"),
                            "tag_abweichung": ab})
                        _ll.anker_aktualisieren(cfg["data_dir"], aid, status="uebernommen")
                        svc.log(f"ADOPTION: anchor {aid} -> master/{person}/ (0 new refs — already "
                                f"covered, {len(plan['uebersprungen'])} near-identical)")
                        return self._send(200, json.dumps(
                            {"ok": True, "msg": f"already covered — all {len(plan['uebersprungen'])} "
                                                f"selected image(s) are near-identical to {person}'s "
                                                "existing references; cluster marked as adopted, "
                                                "nothing copied"},
                            ensure_ascii=False), "application/json")
                    lid = (satz.get("lauf") or {}).get("lauf_id", "")
                    namen = _ue.uebernehmen(cfg["data_dir"], lid, aid, person, plan)
                    with open(os.path.join(cfg["data_dir"], "faces", "refs_meta.jsonl"), "a") as f:
                        for nm in namen:
                            f.write(json.dumps({"ts": round(time.time(), 1), "person": person,
                                                "datei": nm, "herkunft": "lernlauf",
                                                "anker": aid, "aktiv": True}, ensure_ascii=False) + "\n")
                        f.flush()
                    _ue.protokoll_anhaengen(cfg["data_dir"], {
                        "ts": round(time.time(), 1), "anker_id": aid, "person": person,
                        "dateien": [{"quelle": m.get("datei"), "ziel": nm, "emb": m.get("emb") or None}
                                    for nm, m in zip(namen, plan["aufnehmen"])],
                        "uebersprungen": plan["uebersprungen"],
                        "manuelle_refs_ungeprueft": True,      # Upload-Refs tragen keine Embs (Protokoll-Ehrlichkeit)
                        "bedingungs_tag": (satz.get("auswahl") or {}).get("bedingungs_tag"),
                        "tag_abweichung": ab})
                    _ll.anker_aktualisieren(cfg["data_dir"], aid, status="uebernommen")
                    try:
                        os.remove(os.path.join(cfg["data_dir"], "clips", "refcache.npz"))
                    except FileNotFoundError:
                        pass                      # naechster Analyse-Lauf baut mit neuem Master
                    svc.log(f"ADOPTION: anchor {aid} -> master/{person}/ ({len(namen)} refs, "
                            f"{len(plan['uebersprungen'])} skipped) — export + drift watchdog running")
                    svc.referenz_nacharbeit()
                    return self._send(200, json.dumps({"ok": True,
                        "msg": f"adopted {len(namen)} reference{'s' if len(namen) != 1 else ''} for '{person}'"
                               + (f", {len(plan['uebersprungen'])} skipped as near-identical" if plan["uebersprungen"] else "")
                               + " — drift watchdog running (System page)"}, ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/areas_speichern":                     # Areas Stufe 1: Schrieb OHNE Neustart
                try:
                    n = int(self.headers.get("Content-Length", 0))
                    d = json.loads(self.rfile.read(min(n, 65536)))
                    ok, erg = _areas_mod.validieren(d.get("areas"))
                    if not ok:
                        return self._send(400, json.dumps({"ok": False, "msg": erg},
                                                          ensure_ascii=False), "application/json")
                    with _cfg_lock:                       # Lesen+Aendern+Schreiben unter EINEM Lock
                        store = _lade_config_store(cfg)   # (Widerleger .91: sonst verliert ein
                        store["areas"] = erg              # paralleler Kamera-Schrieb still)
                        _store_schreiben(_config_store_pfad(cfg), store)
                    # KEIN svc.neustart(): Areas sind reine Sicht/Meldetext — FRISCHES Objekt
                    # zuweisen statt in-place mutieren (alle Threads teilen svc.cfg; Leser sehen
                    # so alt ODER neu, nie einen Zwischenstand). Ein laufender Lernlauf bleibt
                    # unangetastet (execv wuerde seine Vorbereitung von vorn aufsetzen).
                    # VOR dem Audit (Widerleger .91): scheitert der Audit-Append, sind Platte und
                    # laufende Instanz trotzdem schon einig — kein geteilter Zustand.
                    cfg["areas"] = erg
                    try:
                        with open(os.path.join(cfg["data_dir"], "config", "config_audit.jsonl"), "a") as f:
                            f.write(json.dumps({"ts": round(time.time(), 1), "areas": erg},
                                               ensure_ascii=False) + "\n")
                            f.flush()
                    except OSError as e:
                        svc.log(f"AREAS audit line failed ({e}) — change is saved and active")
                    svc.log(f"AREAS saved: {len(erg)} area{'s' if len(erg) != 1 else ''} (no restart)")
                    return self._send(200, json.dumps({"ok": True,
                        "msg": f"{len(erg)} area{'s' if len(erg) != 1 else ''} saved"},
                        ensure_ascii=False), "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad == "/upload":                              # eigenes Referenz-Foto (AP4)
                try:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                    person = urllib.parse.unquote(qs.get("person", [""])[0]).strip()
                    if not re.fullmatch(rf"{_reg.PERSON_RE}!?", person):
                        return self._send(400, json.dumps({"ok": False, "msg": "Person fehlt/ungueltig"}),
                                          "application/json")
                    n = int(self.headers.get("Content-Length", 0))
                    if n > 15 * 1024 * 1024:
                        return self._send(400, json.dumps({"ok": False, "msg": "Datei > 15 MB"}),
                                          "application/json")
                    ok, msg = svc.upload_referenz(person, self.rfile.read(n))
                    if ok:
                        svc.frigate_sync_export()          # falls frigate_sync an: nach Frigate spiegeln
                    return self._send(200 if ok else 400,
                                      json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False),
                                      "application/json")
                except Exception as e:
                    return self._send(400, json.dumps({"ok": False, "msg": str(e)}), "application/json")
            if pfad != "/gt":                                  # Ground-Truth-Label (User-Klick in der UI)
                return self._send(404, "not found", "text/plain")
            try:
                n = int(self.headers.get("Content-Length", 0))
                d = json.loads(self.rfile.read(min(n, 4096)))
                eid, label = str(d["eid"]), str(d["label"])[:40]
                if not re.match(r"^[\w.\-]+$", eid):
                    return self._send(400, '{"ok": false}', "application/json")
                with open(os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl"), "a") as f:
                    f.write(json.dumps({"ts": round(time.time(), 1), "eid": eid,
                                        "label": label}, ensure_ascii=False) + "\n")
                    f.flush()
                return self._send(200, '{"ok": true}', "application/json")
            except Exception:
                return self._send(400, '{"ok": false}', "application/json")

        def do_GET(self):
            roh = urllib.parse.urlparse(self.path)
            path = urllib.parse.unquote(roh.path)    # Crop-Namen enthalten Personennamen mit Leerzeichen (%20)
            qs = urllib.parse.parse_qs(roh.query)
            if path.startswith("/static/"):            # UI-Statik aus webui/ (AP3)
                fn = os.path.basename(path)
                p = os.path.join(HERE, "webui", fn)
                if fn in ("style.css", "app.js") and os.path.isfile(p):
                    ct = "text/css" if fn.endswith(".css") else "application/javascript"
                    return self._send(200, open(p, "rb").read(), ct + "; charset=utf-8")
                return self._send(404, "not found", "text/plain")
            if path == "/":
                ziel = "/heute" if _setup_done(cfg) else "/setup"   # frisches System -> Wizard (User 22.07.)
                return self._send(302, "", "text/plain", location=ziel)
            if path == "/setup":                          # gefuehrter Erst-Einrichtungs-Wizard (User 22.07.)
                import webui
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
                    fstat = f'<div class="ok-box">✓ Connected — {len(cams)} camera(s) found</div>'
                elif url or ferr:          # ferr auch OHNE url zeigen: eine abgelehnte URL (Tippfehler
                                           # wie 'htp://…') darf nicht stillschweigend wirkungslos bleiben
                    fstat = f'<div class="err-box">✗ Could not reach Frigate: {html.escape(str(ferr or "no cameras"))}<br><small>Fix the URL (or set FRIGATE_URL in your .env / docker-compose) and test again.</small></div>'
                else:
                    fstat = '<div class="dim">Enter your Frigate URL and test the connection.</div>'
                s1 = ('<div class="card setup-step"><div class="sh"><span class="sn">1</span>'
                      '<b>Connect to Frigate</b></div>'
                      '<p class="sub">suslik reads your cameras straight from Frigate\'s API '
                      '(usually port 5000). No cameras are hard-coded.</p>'
                      f'<div class="frow"><input id="setup-url" value="{html.escape(url)}" '
                      'placeholder="http://192.168.x.x:5000" style="min-width:16rem">'
                      '<button class="gtb" onclick="setupTest()">Test connection</button></div>'
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
                        verwenden = (f'<label class="sw"><input type="checkbox" class="kam-verw" '
                                     f'data-cam="{nid}"{" checked" if verw else ""}> use this camera</label>')
                        if cc["zones"]:
                            zboxes = " ".join(
                                f'<label class="zbox"><input type="checkbox" class="kam-zone" '
                                f'data-cam="{nid}" value="{html.escape(z, quote=True)}"'
                                f'{" checked" if z in zonen_akt else ""}> {html.escape(z)}</label>'
                                for z in cc["zones"])
                            zonen_ui = f'<div class="zbar">{zboxes}<span class="dim">none ticked = all events</span></div>'
                        else:
                            zonen_ui = '<div class="zbar dim">no zones defined in Frigate — all events</div>'
                        karten.append(f'<div class="card"><div class="kamhead"><b>{html.escape(name)}</b>'
                                      f'<span class="dim num">{cc["width"] or "?"}×{cc["height"] or "?"}</span>'
                                      f'{verwenden}</div>{zonen_ui}</div>')
                    s2 = ('<div class="setup-step"><div class="sh"><span class="sn">2</span>'
                          '<b>Pick cameras &amp; conditions</b></div>'
                          '<p class="sub">Tick which cameras to watch; tick one or more zones to only '
                          'analyze events that entered them (e.g. person in the garden). None ticked = all events.</p>'
                          + "".join(karten) + '</div>')
                else:
                    s2 = ('<div class="setup-step dim"><div class="sh"><span class="sn">2</span>'
                          '<b>Pick cameras &amp; conditions</b></div>'
                          '<p class="sub">Connect to Frigate first — your cameras appear here.</p></div>')
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
                      '<b>Acceleration</b></div>'
                      f'<p class="sub">Available on this machine: <span class="num">{html.escape(", ".join(avail))}</span>. '
                      'Pick one — CPU always works. Whether the accelerator really engages is confirmed live on the '
                      '<b>System</b> page after start (suslik never silently falls back to CPU without saying so).</p>'
                      f'<div class="bks">{bk_html}</div></div>')
                # --- Schritt 4: Gesichter aus Frigate importieren ---
                if cams and not ferr and url:
                    try:
                        with urllib.request.urlopen(f"{url}/api/faces", timeout=15) as r:
                            _fi = json.load(r)
                        n_pers = len([k for k in _fi if k != "train"])
                        n_img = sum(len(v) for k, v in _fi.items() if k != "train")
                    except Exception:
                        n_pers = n_img = 0
                    if n_img:
                        s4 = ('<div class="setup-step"><div class="sh"><span class="sn">4</span>'
                              '<b>Import faces from Frigate</b></div>'
                              f'<p class="sub">Frigate already has <b>{n_img}</b> reference image(s) of '
                              f'<b>{n_pers}</b> person(s). Import them so suslik recognizes everyone from the start. '
                              'The images are downloaded quickly, then suslik computes its own face features on '
                              'your accelerator (GPU/NPU).</p>'
                              f'<button class="gtb on" onclick="wizImport(this)">Import {n_img} faces from Frigate</button> '
                              '<span id="wiz-import-status" class="dim"></span></div>')
                    else:
                        s4 = ('<div class="setup-step dim"><div class="sh"><span class="sn">4</span>'
                              '<b>Import faces from Frigate</b></div>'
                              '<p class="sub">No faces in Frigate yet. Note: suslik needs at least one reference face before it can recognize anyone — import from Frigate here, or upload photos later on the Known page.</p></div>')
                else:
                    s4 = ('<div class="setup-step dim"><div class="sh"><span class="sn">4</span>'
                          '<b>Import faces from Frigate</b></div>'
                          '<p class="sub">Connect to Frigate first — then you can import its known faces here.</p></div>')
                # --- Abschluss ---
                fertig = ('<div class="setup-step"><button class="gtb on" onclick="setupSpeichern(this)">'
                          'Save &amp; start suslik</button> '
                          '<span id="setup-status" style="color:var(--dim)"></span>'
                          '<p class="sub">Saves your choices and restarts the service once. You can re-run this '
                          'wizard any time from <b>System → Re-run setup wizard</b>.</p></div>')
                s0 = ('<div class="setup-step"><div class="sh"><b>Already have a configuration?</b></div>'
                      '<p class="sub">If you exported a suslik configuration before (System → Configuration '
                      'backup), load it here to restore all settings and skip the wizard.</p>'
                      '<label class="gtb" style="cursor:pointer">Load configuration file…'
                      '<input type="file" accept="application/json,.json" style="display:none" '
                      'onchange="configRestore(this)"></label> '
                      '<span id="restore-status" class="dim"></span></div>')
                _wb_ro = frigate_read_only(cfg)     # Vorbelegung mit dem Ist-Wert (Wizard-Durchlauf kippt prod nicht)
                s5 = ('<div class="setup-step"><div class="sh"><span class="sn">5</span>'
                      '<b>Write back to Frigate?</b></div>'
                      '<p class="sub">suslik can write its verdicts back to Frigate (sub_labels) and mirror '
                      'references, for running both in parallel. Read-only is the safe default.</p>'
                      '<label style="display:block;margin:3px 0"><input type="radio" name="setup-write" value="ro"'
                      + (' checked' if _wb_ro else '') + '> Read-only (recommended) — suslik never writes to Frigate</label>'
                      '<label style="display:block;margin:3px 0"><input type="radio" name="setup-write" value="rw"'
                      + ('' if _wb_ro else ' checked') + '> Write back to Frigate (parallel operation)</label></div>')
                inhalt = ('<h2>Welcome to suslik</h2>'
                          '<p class="sub">A quick guided setup — or load an existing configuration to skip it. '
                          'Everything here is editable later on the normal pages.</p>'
                          + s0 + s1 + s2 + s3 + s4 + s5 + fertig)
                return self._send(200, webui.layout("Setup", "/setup", inhalt, self._banner()))
            if path.startswith("/pass/"):         # Haeppchen 2: Durchgangs-Seite
                import webui
                import auftritte as _auf
                _eidp = urllib.parse.unquote(path[len("/pass/"):])
                _titel, _inhalt = _auf.render_pass(cfg, svc.log_path, master_persons(cfg), _eidp)
                return self._send(200, webui.layout(_titel, "/heute", _inhalt, self._banner()))
            if path == "/auftritte":
                # Paket B (.50): Personen-Tagessicht — Klick auf eine Person landet auf ihren
                # DURCHGAENGEN (Spec 02_today §4.3/S3), nicht mehr auf einem Einzel-Event.
                import webui
                import auftritte as _auf
                _titel, _inhalt = _auf.render(cfg, svc.log_path, master_persons(cfg), qs)
                return self._send(200, webui.layout(_titel, "/heute", _inhalt, self._banner()))
            if path == "/heute":
                rows, letzte = [], {}
                if os.path.exists(svc.log_path):
                    with open(svc.log_path) as f:
                        for l in f:
                            try:
                                rows.append(json.loads(l))
                            except Exception:
                                pass
                # Tagesnavigation (User 25.07.: "tagweise vor und zurück pendeln"). Gleiche
                # Konvention wie der Filter auf /ereignisse: ?tag=JJJJ-MM-TT, ungueltige Eingabe
                # faellt still auf heute zurueck statt den Request abzureissen. Ohne Parameter
                # bleibt alles wie bisher — die Seite ist weiterhin das 302-Ziel von "/".
                _heute_dt = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                _tag_par = qs.get("tag", [""])[0]
                tag_dt = _heute_dt
                if _tag_par:
                    # ALLES in den try, was am Fremdwert scheitern kann — nicht nur strptime.
                    # Fund der Nachpruefung 25.07.: `?tag=9999-12-31` ist ein GUELTIGES Datum, also
                    # kommt strptime durch; erst .timestamp() bzw. das +1 Tag darunter wirft
                    # OverflowError/OSError (ausserhalb des 64-bit-Zeitbereichs). Die Ausnahme lag
                    # ausserhalb des try -> Verbindungsabbruch (HTTP 000) plus Traceback im Log, und
                    # tools/qs.sh:158 macht daraus ein rotes Release-Gate. /ereignisse macht es
                    # richtig; hier war es beim Nachziehen der Tagesnavigation uebersehen worden.
                    # Bei Unsinn still auf heute zurueckfallen: ein manipulierter Parameter darf die
                    # Seite nicht kosten.
                    try:
                        _t = datetime.datetime.strptime(_tag_par, "%Y-%m-%d")
                        _h0, _he = _t.timestamp(), (_t + datetime.timedelta(days=1)).timestamp()
                        tag_dt, heute0, tag_ende = _t, _h0, _he
                    except (ValueError, OverflowError, OSError):
                        _tag_par = ""
                if not _tag_par:
                    heute0 = tag_dt.timestamp()
                    tag_ende = (tag_dt + datetime.timedelta(days=1)).timestamp()
                ist_heute = tag_dt.date() == _heute_dt.date()
                z_events = z_alerts = z_presence = 0
                # by_h (last-wins je eid) MUSS vor die KPI: nach einem Nachhol-Lauf gibt es zwei
                # Zeilen fuer dasselbe Event. Zaehlte die KPI wie frueher die ERSTE, stuende die
                # Szenario-Karte auf der korrigierten Kategorie und der Zaehler darueber weiter
                # auf dem alten Fehler-Stand.
                by_h = {}
                for r in rows:
                    if r.get("eid"):
                        by_h[r["eid"]] = r
                # Areas Stufe 1 v2: Sicht aufloesen BEVOR irgendetwas zaehlt. Die Pass-Liste
                # WAEHLT beruehrte Durchgaenge aus (Urteil bleibt property-weit, s. szenarien);
                # die Event-KPIs zaehlen die Kameras der Sicht. Beobachtete Menge fuer die
                # Default-Sicht = Kameras der Bestandsdaten (Frigate-Ausfall aendert nichts).
                _areas_h = _areas_mod.normalisieren(cfg.get("areas"))
                _ar_aktiv, _nk = _areas_mod.sicht_aufloesen(
                    _areas_h, qs.get("area", [""])[0],
                    {str(r.get("camera", "?")) for r in by_h.values()})
                _aq = f'&amp;area={urllib.parse.quote(_ar_aktiv)}' if _nk is not None else ''
                for r in by_h.values():
                    if _nk is not None and str(r.get("camera", "?")) not in _nk:
                        continue
                    if heute0 <= (r.get("start") or r.get("ts", 0)) < tag_ende:
                        z_events += 1
                        if r.get("alerted"):
                            z_alerts += 1
                        # Anwesenheits-Push GETRENNT zaehlen (Fund 25.07.): gezaehlt wurde nur
                        # `alerted`, also der Vorfall-Alarm. Heute stand deshalb "Alerts sent 0"
                        # auf der Seite, waehrend vier Anwesenheitsmeldungen rausgegangen waren.
                        # Woertlich richtig, in der Sache irreführend — der Betreiber sieht eine
                        # Null und hat vier Meldungen auf dem Telefon. Beide Arten sind
                        # Benachrichtigungen, aber nicht dasselbe, also zwei Zeilen statt einer
                        # gemischten Summe.
                        if r.get("presence_push"):
                            z_presence += 1
                # Live-Waechter-Meldungen (Phase 4 Baustein B, Sichtkontrolle
                # .177 Befund 3: real rausgegangene Engine-Pushes tauchten in
                # KEINEM Zaehler auf). EINE Quelle: das Melde-Protokoll der
                # Engine (<data_dir>/live/meldungen.jsonl) — der Dienst liest
                # nur, nichts wird doppelt gezaehlt. Zeile erscheint, sobald
                # Live benutzt wird (Guards oder Historie), sonst gar nicht.
                from core import livewache as _lwz
                z_live = 0
                z_live_kanaele = {}
                z_live_liste, z_live_gruppen = [], 0
                _live_zeile = False
                try:
                    _live_zeile = (bool((cfg.get("live") or {}).get("guards"))
                                   or _lwz.melde_protokoll_vorhanden(cfg))
                    if _live_zeile:
                        # KANN-7 (Widerleger phase34): kanalNEUTRAL zaehlen —
                        # die Zeile zeigte nur ("alert","pushover"), eine
                        # Telegram-only-Installation sah dauerhaft "Pushover 0"
                        # als einzige Wahrheit. Summe + Aufschluesselung je
                        # real benutztem Kanal (Reihenfolge = KANAELE_ERLAUBT,
                        # zentrale Quelle).
                        _zk = _lwz.melde_zaehler(cfg, heute0, tag_ende,
                                                 kameras=_nk)
                        z_live_kanaele = {
                            k: _zk.get(("alert", k), 0)
                            for k in _lwz.KANAELE_ERLAUBT
                            if _zk.get(("alert", k), 0)}
                        z_live = sum(z_live_kanaele.values())
                        # .188 (User 13.08.): Today zeigt SEPARAT, was live
                        # erkannt wurde — die Liste je Trigger (gebuendelte
                        # Kanaele, Meldetext), dieselbe Quelle+Sicht wie der
                        # Zaehler.
                        # .191 (User: 'nur zeigen, was wirklich erkannt
                        # wurde'): breit lesen, unten auf person-Gruppen
                        # gefiltert — unknown-Trigger erschlagen die Reihe
                        # nicht mehr, sie bleiben im Zaehler + Live-Reiter.
                        z_live_liste, z_live_gruppen = _lwz.melde_liste(
                            cfg, heute0, tag_ende, kameras=_nk,
                            max_gruppen=200)
                except Exception as e:
                    svc.log(f"!! live alert counter failed: "
                            f"{type(e).__name__}: {e}")
                for r in rows:                       # Personen-Historie ueber ALLE Zeilen
                    t = r.get("start") or r.get("ts", 0)
                    for p in r.get("bestaetigt") or []:
                        if t > letzte.get(p, (0, None))[0]:
                            letzte[p] = (t, r)
                import webui
                gtmap_h = {}   # F2 (.54): eid -> LETZTES Label (Muster Event-Seite) — der
                #  Label-WERT entscheidet: Person=beurteilt/raus, "Stranger"/"?"=BLEIBT
                #  sichtbar (konzept_gt_label_fix.md, abgenommen; vorher warf das reine
                #  eid-Set auch bestaetigte Fremde aus der Unbekannt-Zaehlung).
                gtp_h = os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl")
                if os.path.exists(gtp_h):
                    with open(gtp_h) as f:
                        for l in f:
                            try:
                                _d = json.loads(l); gtmap_h[_d["eid"]] = _d["label"]
                            except Exception:
                                pass
                # (by_h wird oben vor der KPI gebaut)

                def _av_farbe(name):
                    # Avatar-Toene (weisse Initiale darauf). Ersetzt am 25.07.: von den sechs
                    # alten erreichte nur einer WCAG AA mit Weiss, #c98a2b lag bei 2,94.
                    # Diese sechs liegen alle ueber 5,2 und sind im Farbton klar getrennt.
                    # Bewusst NICHT modusabhaengig: eine Person soll in Hell und Dunkel
                    # dieselbe Farbe haben, das ist ein Wiedererkennungsmerkmal.
                    pal = ["#2c62ad", "#a33163", "#6f45b0", "#1f7a5f", "#8a5f16", "#4c5a6b"]
                    return pal[sum(bytearray(name.encode("utf-8"))) % len(pal)]

                def _crop_url(eid, person):
                    ed = str(eid or "").replace("/", "_")
                    edir = os.path.join(cfg["data_dir"], "events", ed)
                    if ed and os.path.isdir(edir):
                        js = ([c for c in os.listdir(edir) if f"_show_{person}_" in c] or
                              [c for c in os.listdir(edir) if f"_best_{person}_NN" in c])
                        if js:
                            return f"/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(js[0])}"
                    return None

                def _av(person, eid=None, cls="av"):
                    u = _crop_url(eid or (letzte[person][1].get("eid") if person in letzte else None), person)
                    if u:
                        return f'<div class="{cls}"><img src="{u}" alt=""></div>'
                    return f'<div class="{cls}" style="background:{_av_farbe(person)}">{html.escape(person[:1].upper())}</div>'

                import szenarien as _szen
                _uk_gesehen = False   # .54: Anker id="unidentified" an die ERSTE Unknown-Karte (Kennzahl-Link)
                gap = int(cfg.get("szenario_gap_min", 5)) * 60   # auch unten (Besuchs-Buendelung) genutzt
                try:                  # Koerper-Treffer je Event (Zuschreibung + Ausweis)
                    from core import personlive as _plv
                    _kmap = _plv.treffer_karte(cfg["data_dir"])
                    from core import personmodell as _pmz
                    _kab = int((_pmz.status_lesen(cfg["data_dir"]) or {})
                               .get("feuer_ab") or _plv.FEUER_AB)
                except Exception:
                    _kmap, _kab = {}, 2
                try:                  # V4 (§7/E6): Vision-Urteil je Durchgang —
                    from core import vision as _visx       # Info auf der Karte
                    from core import visionurteil as _vu   # + Stimme der Zu-
                    _vmap = _vu.protokoll_karte(cfg["data_dir"])  # schreibung
                    _vis_grund = _visx.grund_text  # (vision_stimme, szenarien.py);
                except Exception:                  # nie Alarm-Ausloeser, nie Veto
                    _vmap, _vis_grund = {}, str
                szenarien = _szen.szenarien_des_tages(by_h, heute0, tag_ende, cfg, gtmap_h,
                                                      nur_kameras=_nk,
                                                      koerper_map=_kmap,
                                                      koerper_ab=_kab,
                                                      vision_map=_vmap)
                interessant = [s for s in szenarien if s["kat"] != "motion"]
                motion_n = len(szenarien) - len(interessant)

                # Unbekannt-Identitaeten des Pools: face_id IST die Event-ID (anlernen.py), damit
                # laesst sich ein unerkannter Durchgang direkt einer U-Nummer zuordnen. User
                # 25.07.: "dann könnte das auch angezeigt werden als unbekannt Nummer XY."
                # Faellt still aus, wenn der Pool fehlt — dann steht schlicht "Unknown".
                # MUSS-2 (Widerleger phase34): EIN toleranter Leser (_pool_eid_karte ->
                # core.unbekanntpool._cluster_lesen) statt des dritten Streu-Parsers,
                # der die Seite an {"members": 5} sterben liess.
                eid2uid, uid_members = _pool_eid_karte(cfg["data_dir"])

                def _besuche_vorher(u, start_t):
                    """Wie oft war Identitaet u VOR diesem Durchgang da — als BESUCHE gezaehlt,
                    nicht als Events (Fund der Vor-Release-Pruefung, 25.07.: zwei U83-Karten am
                    selben Tag zeigten beide 'seen 8x before' — der alte Zaehler nahm die
                    Mitgliederzahl der Identitaet, also Events ueber alle Zeit, ohne die Zeit
                    dieses Durchgangs zu beachten). Die Zeit steckt im Event-ID-Praefix
                    ('1784967720.988397-…'); Events vor dem Durchgangs-Start werden mit derselben
                    Luecke zu Besuchen gebuendelt wie die Szenarien selbst (gap)."""
                    ts = []
                    for _m in (uid_members.get(u) or []):
                        try:
                            t = float(str(_m).split("-", 1)[0])
                        except ValueError:
                            continue
                        if t < start_t - 1:
                            ts.append(t)
                    ts.sort()
                    n, letzte = 0, None
                    for t in ts:
                        if letzte is None or t - letzte > gap:
                            n += 1
                        letzte = t
                    return n

                # --- Auswertung je Person ueber den ganzen Tag (fuer das Personen-Band) ---
                # User-Vorgabe 25.07.: "Wichtig ist, WER erkannt wurde." Die Zahlen dafuer
                # liegen alle in den Szenarien vor, sie wurden bisher nur nicht ausgewertet.
                pers_tag = {}
                for s in interessant:
                    for p, d in s["pers"].items():
                        # erst = erste BESTAETIGUNG dieser Person, nicht der Szenario-Start. Ein
                        # Durchgang beginnt mit Bewegung; wer da kommt, steht erst Minuten spaeter
                        # fest (gemessen 25.07.: Person im Durchgang ab 09:20:39, bestaetigt erst 09:26:09).
                        # Die Seite schrieb "since 09:20" und behauptete damit Wissen, das zu diesem
                        # Zeitpunkt niemand hatte.
                        e = pers_tag.setdefault(p, {"durchgaenge": 0, "erst": d["erst_t"],
                                                    "letzt": 0, "eid": None, "erst_live": 0,
                                                    "best": -1.0, "kam": None, "laeuft": False})
                        e["durchgaenge"] += 1
                        e["erst"] = min(e["erst"], d["erst_t"])
                        # Fuer "since …" bei einem LAUFENDEN Durchgang zaehlt dessen eigene erste
                        # Bestaetigung, nicht die des Tages. Sonst stand bei jemandem, der morgens
                        # kurz da war und abends wiederkommt, "since 08:21" — das behauptet zwoelf
                        # Stunden durchgehende Anwesenheit statt zwei getrennter Besuche.
                        if s.get("laeuft"):
                            e["erst_live"] = (min(e["erst_live"], d["erst_t"])
                                              if e["erst_live"] else d["erst_t"])
                        # letzt/kam kommen aus dem letzten Event, in dem DIESE Person bestaetigt
                        # wurde — nicht aus dem Ende des Durchgangs (das kann Minuten spaeter und
                        # auf einer ganz anderen Kamera liegen).
                        if d["letzt_t"] >= e["letzt"]:
                            e["letzt"], e["kam"] = d["letzt_t"], d["letzt_cam"]
                        # Karten-Foto NUR aus Gesichts-Quellen (User-Fund 05.08.:
                        # ein koerper-zugeschriebener Pass traegt SVM-Scores ~0.9x,
                        # gewann den best-Vergleich gegen Gesichts-cos ~0.6x — sein
                        # eid hat aber kein Gesichts-Crop, Karte fiel auf den
                        # Buchstaben zurueck). koerper zaehlt Passe/letzt/kam mit,
                        # nur die Foto-Wahl ueberspringt ihn.
                        if d.get("quelle") != "koerper" and d["best"] >= e["best"]:
                            e["best"], e["eid"] = d["best"], d["eid"]
                        e["laeuft"] = e["laeuft"] or bool(s.get("laeuft"))

                # Unbekannte KONTEXTABHAENGIG trennen (User-Entscheid 25.07., Kernpunkt): Gesichter, die in
                # einem Durchgang MIT bestaetigter Person nicht zugeordnet wurden, sind harmlos —
                # das sind dieselben Leute, nur schlecht getroffen. Sie gehoeren als Fussnote an
                # den Durchgang. Nur Durchgaenge OHNE jede Bestaetigung sind echte Unbekannte.
                # Das ist exakt die Regel, die die Szenen-Karenz im Alarmpfad schon anwendet.
                unbek_echt = [s for s in interessant
                              if not s["pers"] and s["unbek"]
                              and s.get("unbek_stark", 1) > 0]   # Issue #16: stille Klasse
                unbek_nebenbei = sum(s["unbek"] for s in interessant if s["pers"] and s["unbek"])
                # Unbekannt-Sichtbarkeit Baustein A (12.08., Realfall Besuch 13:12-15:02):
                # die Unidentified-Kachel ZUSAETZLICH aus dem UNBEKANNT-POOL speisen.
                # Unbekannte, die MIT einer erkannten Person kommen (der haeufigste
                # Besuchsfall), liefen in der Pass-Zaehlung als Fussnote "normally the
                # same people" mit und verschwanden. EINE Quelle fuer Kachel + Learn-
                # Hinweis: core/unbekanntpool (aktive Nicht-Objekt-Cluster mit Stuetzen
                # im angezeigten Tag; Auftritte gap-gebuendelt wie die Vorbesuche).
                from core import unbekanntpool as _ubp
                pool_tag = _ubp.tages_cluster(cfg["data_dir"], heute0, tag_ende,
                                              gap, log=svc.log)
                pool_unbek_n = len(pool_tag)
                pool_auftritte = sum(pool_tag.values())
                # Widerleger MUSS-2 (Realfall U155): ARCHIVIERTE Nicht-Objekt-Cluster
                # mit frischer Stuetze im Fenster als eigene Zeile mitzaehlen — der
                # naechste Reconcile reaktiviert sie automatisch und laut (anlernen),
                # bis dahin darf die Kachel sie nicht still verstecken.
                pool_archiv_n = _ubp.tages_archiv(cfg["data_dir"], heute0,
                                                  tag_ende, log=svc.log)

                # Die vier gleichrangigen Kennzahlkacheln sind am 25.07. entfallen: "People
                # recognized: 3" ist redundant, sobald drei Personenkarten dastehen, und "With
                # unknowns" zaehlte Ereignisse mit Gesichtern — darin steckten Gras, Laub und der
                # Radkasten (24.07.: gezaehlte 83 gegen real 9 unterscheidbare Unbekannte).
                # Ersetzt durch das Personen-Band + die ruhige Randspalte weiter unten.

                # --- Personen-Chip (echter Crop, Fallback Initiale) ---
                def _chip(name, eid, count=1, best=0.0, koerper=False):
                    u = _crop_url(eid, name)
                    if not u and koerper and eid:
                        # koerper-zugeschriebener Pass: statt Buchstabe das
                        # BESTE Koerper-Bild des Durchgangs zeigen (User
                        # 05.08.) — der Crop liegt tagesbestaendig unter
                        # personlern/treffer/ (personlive schreibt ihn).
                        ed = str(eid).replace("/", "_")
                        if os.path.isfile(os.path.join(
                                cfg["data_dir"], "personlern", "treffer",
                                ed + ".jpg")):
                            u = ("/person/treffer/"
                                 + urllib.parse.quote(ed) + ".jpg")
                    av = (f'<span class="avs"><img src="{u}" alt=""></span>' if u
                          else f'<span class="avs" style="background:{_av_farbe(name)}">'
                               f'{html.escape(name[:1].upper())}</span>')
                    cnt = f' <span class="sc">×{count}</span>' if count > 1 else ''
                    sc = f' <span class="sc">{best:.2f}</span>' if best else ''
                    inner = f'{av}{html.escape(name)}{cnt}{sc}'
                    # Paket B (.50): Chip -> Personen-Tagessicht (Spec: Chips wie Karten);
                    # eine aktive Area-Sicht wird mitgetragen (der Blick bleibt im Bereich).
                    _zt = ('' if ist_heute else f'&tag={tag_dt.strftime("%Y-%m-%d")}') \
                        + (f'&area={urllib.parse.quote(_ar_aktiv)}' if _nk is not None else '')
                    return (f'<a class="pchip" href="/auftritte?person={urllib.parse.quote(name)}{_zt}">'
                            f'{inner}</a>')

                def _hhmm(t):
                    return datetime.datetime.fromtimestamp(t).strftime("%H:%M")

                chev = ('<svg class="chev" viewBox="0 0 16 16" fill="none"><path d="M6 4l4 4-4 4" '
                        'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
                        'stroke-linejoin="round"/></svg>')
                karten = []
                live_offen = False
                for s in interessant:
                    live = s.get("laeuft")
                    live_offen = live_offen or live
                    if live:
                        zeit = f'since {_hhmm(s["start"])}'
                        dauer = f'{s["n"]} event{"s" if s["n"] != 1 else ""} so far'
                    else:
                        kurz = (s["ende"] - s["start"]) < 60
                        zeit = _hhmm(s["start"]) if kurz else f'{_hhmm(s["start"])}–{_hhmm(s["ende"])}'
                        _pl = "s" if s["n"] != 1 else ""
                        dauer = (f'{s["n"]} event{_pl}' if kurz
                                 else f'{int((s["ende"] - s["start"]) / 60)} min · {s["n"]} event{_pl}')
                    mitte = "".join(_chip(p, d["eid"], d["count"], d["best"],
                                          koerper=d.get("quelle") == "koerper")
                                    for p, d in sorted(s["pers"].items(), key=lambda x: -x[1]["count"]))
                    if live:
                        # Durchgang laeuft noch (letztes Event < Karenz her): nur Fakten (erkannte
                        # Personen), noch KEIN abschliessendes Urteil, es koennen Kameras dazukommen
                        mitte = ('<span class="badge live"><span class="ldot"></span>in progress</span>'
                                 + (mitte or '<span class="dim">identifying…</span>'))
                    else:
                        if not s["pers"] and s["unbek"] and not s.get("unbek_stark"):
                            # Issue #16 Automatik: kein einziges ernstzunehmendes
                            # Gesicht im ganzen Durchgang -> stille Klasse statt
                            # Warn-Plakette und Unknown-Karte. Events bleiben
                            # unter Events/To-label erreichbar.
                            mitte = ('<span class="dim">no usable face in this '
                                     f'pass ({s["unbek"]} event'
                                     f'{"s" if s["unbek"] != 1 else ""})</span>')
                        elif not s["pers"]:
                            mitte = '<span class="badge q">?</span><span class="dim">no known person</span>'
                        if s["unbek"] and not s["pers"] and s.get("unbek_stark"):
                            # Kein einziger Bestaetigter im ganzen Durchgang — DAS ist der Fall,
                            # der Aufmerksamkeit verdient, und nur der.
                            # "N unknown" las sich wie N unbekannte PERSONEN, gezaehlt werden aber
                            # unerkannte Events desselben Durchgangs — meist ein und dieselbe Person
                            # auf mehreren Kameras. "unmatched" ohne Hauptwort behauptet keine Anzahl
                            # von Menschen; wie viele es waren, weiss an dieser Stelle niemand.
                            mitte += (f'<a class="badge warn" href="/event/{urllib.parse.quote(str(s["unbek_eid"]))}">'
                                      f'{s["unbek"]} unmatched</a>' if s.get("unbek_eid")
                                      else f'<span class="badge warn">{s["unbek"]} unmatched</span>')
                        elif s["unbek"]:
                            # Nicht zugeordnete Gesichter in einem Durchgang MIT bestaetigter Person:
                            # das sind dieselben Leute, nur schlecht getroffen (User 25.07.). Ruhige
                            # Fussnote statt Warn-Plakette — sonst sieht jeder normale Durchgang
                            # nach Vorfall aus.
                            mitte += (f'<a class="fussnote" href="/event/{urllib.parse.quote(str(s["unbek_eid"]))}">'
                                      f'+{s["unbek"]} not matched</a>' if s.get("unbek_eid")
                                      else f'<span class="fussnote">+{s["unbek"]} not matched</span>')
                        elif s["pers"]:
                            mitte += '<span class="badge ok">all recognized</span>'
                        # Erkennungs-QUELLE ausweisen (User 04.08./05.08.): face /
                        # person / beides — Zuschreibung passiert in szenarien
                        # (quelle="koerper"), hier nur noch die Kennzeichnung.
                        _kp = sorted({t["person"] for e in s["evs"]
                                      if (t := _kmap.get(e["eid"]))})
                        _nur_k = s["pers"] and all(
                            d.get("quelle") == "koerper" for d in s["pers"].values())
                        if _nur_k:
                            # Fix vision-stimme-2: hat die Vision-Stimme die
                            # Zuschreibung MITgetragen, weist die Quelle das
                            # aus; reine Koerper-Zuschreibung bleibt woertlich
                            # wie bisher (core/highlights.py zitiert den Text).
                            mitte += ('<span class="fussnote">via person + '
                                      'vision, no face</span>'
                                      if any(d.get("vision_stimme")
                                             for d in s["pers"].values())
                                      else '<span class="fussnote">via person '
                                           'recognition, no face</span>')
                        elif s["pers"] and _kp:
                            mitte += '<span class="fussnote">via face + person</span>'
                        elif s["pers"]:
                            mitte += '<span class="fussnote">via face</span>'
                        elif _kp:
                            # Koerper-Treffer unter der Stuetzen-Regel (keine
                            # Zuschreibung): als Hinweis zeigen, ehrlich duenn.
                            mitte += ("".join(f'<span class="badge q">{html.escape(p)}</span>'
                                              for p in _kp)
                                      + '<span class="fussnote">person recognition hint '
                                        '(below support rule)</span>')
                    # V4: die Vision-Zeile steht auf der KARTE (nicht in der
                    # Live-Meldung — der Alarm geht synchron raus, Vision
                    # braucht Sekunden bis Minuten). Sie nennt die beiden
                    # TATSAECHLICH verglichenen Namen; ueber ungepruefte
                    # Personen sagt sie nichts (§1/§4).
                    _vpk = "%d" % round(s["start"])
                    _vz = _vmap.get(_vpk)
                    if _vz:
                        # .166 (User 09.08. am Screenshot): auf der KARTE steht
                        # nur das ERGEBNIS. Der Paar-Zusatz "(A vs B)" war ein
                        # Ehrlichkeits-Detail aus V4 (E6: nie eine Aussage ueber
                        # ungepruefte Personen suggerieren) — an dieser Stelle
                        # las er sich aber wie ein Zweifel am Ergebnis
                        # ("entweder ist es X oder eben jemand anderes oder
                        # unbekannt"). Er ist nicht geloescht, er ist umgezogen:
                        # die volle Methodik (Runden, offene Paare, Zeiten,
                        # welche zwei Galerien verglichen wurden) steht im
                        # Erzaehl-Log des Erkennungstests, und der Link daneben
                        # fuehrt genau dorthin.
                        mitte += ('<span class="fussnote">vision: '
                                  + (html.escape(_vz["person"])
                                     if _vz.get("person") else
                                     "no verdict — " + html.escape(
                                         _vis_grund(_vz.get("grund"))[:70]))
                                  + ' <a href="/erkennungstest?pass='
                                  + urllib.parse.quote(_vpk)
                                  + '" title="how vision got there: rounds, '
                                  'galleries compared, timings">details</a>'
                                  "</span>")
                    crows = []
                    for cam, cl in s["kams"].items():
                        chips = "".join(_chip(p, cl["eid"].get(p), k) for p, k in cl["erk"].items())
                        ub = (f'<a class="badge warn" href="/event/{urllib.parse.quote(str(cl["unbek_eid"]))}">'
                              f'{cl["unbek"]} unmatched</a>' if cl["unbek"] and cl.get("unbek_eid")
                              else (f'<span class="badge warn">{cl["unbek"]} unmatched</span>' if cl["unbek"] else ''))
                        detail = (chips + ub) or '<span class="dim">motion only, no face</span>'
                        px = f'<span class="num">{cl["bw"]}px</span>' if cl["bw"] else '<span class="dim">—</span>'
                        vid = (f' <a class="badge" href="/video/{urllib.parse.quote(str(cl["bw_eid"]))}" '
                               f'title="best clip of this camera">&#9654; video</a>'
                               if cl.get("bw_eid") else '')
                        crows.append(
                            f'<div class="camrow"><div class="camname"><span class="dot"></span>'
                            f'{html.escape(cam)}</div><span class="camn num">{cl["n"]} '
                            f'event{"s" if cl["n"] != 1 else ""}</span>'
                            f'<div class="camdetail">{detail}</div><span class="campx">{px}{vid}</span></div>')
                    nk = len(s["kams"])
                    kls = "sz k-" + s["kat"] + (" sz-live" if live else "")
                    karten.append(
                        f'<details class="{kls}"><summary>'
                        f'<div class="sz-zeit"><div class="t num">{zeit}</div><div class="d">{dauer}</div></div>'
                        f'<div class="sz-mitte">{mitte}</div>'
                        f'<div class="sz-rechts"><span>{nk} camera{"s" if nk > 1 else ""}</span>{chev}</div>'
                        f'</summary><div class="sz-body">{"".join(crows)}</div></details>')
                if karten:
                    liste = f'<div class="szlist">{"".join(karten)}</div>'
                elif _nk is not None:
                    # Leerzustand einer Area-Sicht: der Standard-Text waere hier woertlich
                    # falsch ('niemand auf dem Grundstueck'), wenn nur DIESE Sicht leer ist.
                    liste = webui.leer(f"No passes touched {_ar_aktiv} "
                                       + ("yet today." if ist_heute else "on this day."),
                                       "The All chip above shows the whole property.")
                elif ist_heute:
                    # Pass-Begriffs-Hygiene (Areas Stufe 1/K4): sichtbar heisst es ueberall
                    # "pass" — "scenario" bleibt interner Begriff (Speicherwerte-Regel).
                    liste = webui.leer("No passes with a face yet today.",
                                       "As soon as someone walks across the property, the pass appears here.")
                else:
                    liste = webui.leer("Nothing with a face on this day.",
                                       "Use the arrows to look at another day, or open Events for the full list.")
                motiv = (f'<div class="pnote">{motion_n} motion-only passes without a face are hidden, '
                         f'fully listed under <a href="/ereignisse?tag={tag_dt.strftime("%Y-%m-%d")}{_aq}">'
                         f'Events</a>.</div>' if motion_n else '')
                # #42 Teil B: was der Fehldetektions-Filter heute aussortiert hat, als
                # Fussnote ausweisen — nichts verschwindet still (QS-Fehlerklasse 3).
                # Bei aktiver Area-Sicht zaehlen beide Fussnoten NUR die Sicht-Kameras
                # (dieselbe Menge wie Karten und KPI — Zaehler-Ehrlichkeit).
                fd_tag = sum(x.get("faces", 0) - x["faces_geprueft"] for x in by_h.values()
                             if "faces_geprueft" in x
                             and (_nk is None or str(x.get("camera", "?")) in _nk)
                             and heute0 <= (x.get("start") or x.get("ts") or 0) < tag_ende
                             and x.get("faces", 0) > x["faces_geprueft"])
                if fd_tag:
                    motiv += (f'<div class="pnote">{fd_tag} detection{"s" if fd_tag != 1 else ""} '
                              f'filtered as non-faces (static-object signature) — judgments untouched.</div>')
                # S2/A4 (konzept_no_person.md): stille Fussnote je Kamera — zeigt, WO
                # Frigate die Fehltrigger produziert (Tuning-Hinweis, User-v2-Wunsch).
                # Event-Zaehlung je Kamera; die Events selbst bleiben unter Events auffindbar.
                np_cams = {}
                for x in by_h.values():
                    if (x.get("kategorie") == "no_person"
                            and (_nk is None or str(x.get("camera", "?")) in _nk)
                            and heute0 <= (x.get("start") or x.get("ts") or 0) < tag_ende):
                        c = x.get("camera") or "?"
                        np_cams[c] = np_cams.get(c, 0) + 1
                if np_cams:
                    np_n = sum(np_cams.values())
                    je = ", ".join(f"{html.escape(str(c))} ×{n}"
                                   for c, n in sorted(np_cams.items(), key=lambda kv: -kv[1]))
                    motiv += (f'<div class="pnote">{np_n} event{"s" if np_n != 1 else ""} '
                              f'classified as likely false trigger (no person found): {je}.</div>')
                cnt = ('newest first · a pass in progress updates automatically'
                       if live_offen else 'newest first · click opens the cameras')
                # Tagesnavigation: vor/zurueck um einen Tag. Vorwaerts ist am heutigen Tag
                # deaktiviert — in die Zukunft gibt es nichts zu sehen, und ein Link dorthin
                # waere ein Versprechen, das die Seite nicht halten kann.
                _vor = (tag_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                _zur = (tag_dt - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                _titel = "Today" if ist_heute else tag_dt.strftime("%A, %d %B %Y")
                _unter = (tag_dt.strftime("%A, %d %B %Y") if ist_heute else
                          ("yesterday" if (_heute_dt - tag_dt).days == 1 else ""))
                # Areas: die aktive Sicht ueberlebt das Tage-Blaettern (_aq, s.o.) und die
                # Chip-Leiste ist der Umschalter — sie rendert NUR, wenn Areas angelegt sind.
                from routes import areas as _r_areas
                nav_tag = (
                    '<div class="tagnav">'
                    f'<a class="gtb" href="/heute?tag={_zur}{_aq}" title="previous day">&#8592;</a>'
                    f'<div class="tagnav-mitte"><div class="tagnav-t">{html.escape(_titel)}</div>'
                    f'<div class="tagnav-u">{html.escape(_unter)}</div></div>'
                    + (f'<span class="gtb" aria-disabled="true" title="no future days">&#8594;</span>'
                       if ist_heute else
                       f'<a class="gtb" href="/heute?tag={_vor}{_aq}" title="next day">&#8594;</a>')
                    + ('' if ist_heute else
                       f'<a class="gtb on" href="/heute{_aq.replace("&amp;", "?", 1)}">back to today</a>')
                    + '</div>'
                    + _r_areas.chips(_areas_h, _ar_aktiv, "/heute",
                                     {} if ist_heute else {"tag": tag_dt.strftime("%Y-%m-%d")})
                    + webui.update_block() + webui.whatsnew_block())
                # --- Personen-Band (ersetzt die vier gleichrangigen Kennzahlkacheln) ---
                # User 25.07.: "Wichtig ist, WER erkannt wurde." Vier gleich grosse Kacheln, von
                # denen eine "People recognized: 3" sagt, sind redundant, sobald drei Personen
                # dastehen. Die Restzahlen wandern in eine ruhige Randspalte.
                pkarten = []
                for p, e in sorted(pers_tag.items(), key=lambda x: -x[1]["letzt"]):
                    spanne = (f'since {_hhmm(e["erst_live"] or e["erst"])}' if e["laeuft"] else
                              (_hhmm(e["erst"]) if (e["letzt"] - e["erst"]) < 60
                               else f'{_hhmm(e["erst"])}–{_hhmm(e["letzt"])}'))
                    dg = (f'{e["durchgaenge"]} passes' if e["durchgaenge"] != 1 else '1 pass')
                    kam = (f'<div class="pk-kam">last seen {html.escape(str(e["kam"]))}, '
                           f'{_hhmm(e["letzt"])}</div>' if e["kam"] else '')
                    live = ('<span class="badge live"><span class="ldot"></span>in progress</span>'
                            if e["laeuft"] else '')
                    # Paket B (.50): Personen-Karte -> Personen-Tagessicht (nicht mehr Einzel-Event)
                    ziel = (f'/auftritte?person={urllib.parse.quote(p)}'
                            + ('' if ist_heute else f'&tag={tag_dt.strftime("%Y-%m-%d")}')
                            + (f'&area={urllib.parse.quote(_ar_aktiv)}' if _nk is not None else ''))
                    pkarten.append(
                        f'<a class="pk{" pk-live" if e["laeuft"] else ""}" href="{ziel}">'
                        f'{_av(p, e["eid"], cls="pk-av")}'
                        f'<div class="pk-txt"><div class="pk-name">{html.escape(p)} {live}</div>'
                        f'<div class="pk-meta">{dg} · {spanne}</div>{kam}</div></a>')
                # --- Unerkannte Durchgaenge GEHOEREN INS BAND (User 25.07.) ---
                # "Ich habe oben zwei gesehen, heute waren aber mehr Events." Wer nicht erkannt
                # wurde, war trotzdem da. Optisch abgesetzt (bernstein statt gruen), und wo unser
                # Pool die Person schon kennt, mit ihrer Nummer statt als anonymer Haufen:
                # "dann könnte das auch angezeigt werden als unbekannt Nummer XY".
                for s in unbek_echt:
                    # Den Pool ueber ALLE Events des Durchgangs fragen UND ueber alle ENTSCHEIDEN
                    # (Vor-Release-Pruefung 25.07.: die erste Fassung fragte zwar alle, brach aber
                    # beim ersten Treffer ab — und weil unbek_eids zeitsortiert ist, gewann immer
                    # das frueheste Event. Ein Durchgang, dessen erstes Event zur heute angelegten
                    # U98 gehoerte und dessen zweites zur U19 mit zehn Vorbesuchen, wurde als
                    # "Unknown 98 · first time here" angezeigt: der Wiederkehrer sah aus wie ein
                    # Erstbesucher). Jetzt: alle Identitaeten des Durchgangs einsammeln, die mit
                    # den meisten VOR-Besuchen traegt die Karte, weitere stehen als "+N more" dran.
                    treffer = {}                             # uid -> erstes Event dieser Identitaet
                    for _e in (s.get("unbek_eids") or []):
                        _u = eid2uid.get(str(_e or ""))
                        if _u and _u not in treffer:
                            treffer[_u] = _e
                    if treffer:
                        vorher_je = {u: _besuche_vorher(u, s["start"]) for u in treffer}
                        uid = max(treffer, key=lambda u: (vorher_je[u],
                                                          len(uid_members.get(u) or []), u))
                        treffer_eid, vorher = treffer[uid], vorher_je[uid]
                        weitere = len(treffer) - 1
                        # Gesichter ALLER Identitaeten des Durchgangs — Reihenfolge nach NUTZEN
                        # (User-Test 25.07.: "die ungelernten Gesichter der Testperson fehlen"): die
                        # Mitgliederliste ist einfuegesortiert, also AELTESTE zuerst — bei U34
                        # mit 27 Mitgliedern fielen die frischen Gesichter des angeklickten
                        # Durchgangs hinter der Anzeige-Kappe ab. Jetzt: erst die Gesichter
                        # DIESES Durchgangs, dann der Rest neueste zuerst (Zeit steckt im
                        # Event-ID-Praefix).
                        _im_pass = set(str(e) for e in (s.get("unbek_eids") or []))
                        def _ts(m):
                            try:
                                return float(str(m).split("-", 1)[0])
                            except ValueError:
                                return 0.0
                        _roh = []
                        for _u in sorted(treffer, key=lambda u: (u != uid,)):
                            for _m in (uid_members.get(_u) or []):
                                if _m not in _roh:
                                    _roh.append(_m)
                        alle_member = (sorted((m for m in _roh if str(m) in _im_pass),
                                              key=_ts, reverse=True)
                                       + sorted((m for m in _roh if str(m) not in _im_pass),
                                                key=_ts, reverse=True))
                    else:
                        uid = treffer_eid = None
                        vorher = weitere = 0
                        alle_member = []
                    _uk_anker = ' id="unidentified"' if not _uk_gesehen else ''
                    _uk_gesehen = True
                    name = (f"Unknown {uid.lstrip('U')}" if uid else "Unknown") \
                        + (f" +{weitere} more" if weitere else "")
                    zusatz = (f'<div class="pk-kam">seen {vorher}× before</div>' if vorher > 0 else
                              ('<div class="pk-kam">first time here</div>' if uid else
                               # Umbenannt (.54, Issue-#5-Zusage): 'not grouped yet' las sich
                               # als Kamera-Aussage — gemeint ist das fehlende Besucher-Profil.
                               '<div class="pk-kam">no visitor profile yet</div>'))
                    if s.get("gt_fremd"):   # F2/A2: vom User bestaetigter Fremder, ruhig ausweisen
                        zusatz += '<div class="pk-kam badge-gtfremd">confirmed stranger</div>'
                    spanne = (_hhmm(s["start"]) if (s["ende"] - s["start"]) < 60
                              else f'{_hhmm(s["start"])}–{_hhmm(s["ende"])}')
                    nk = len(s["kams"])
                    _z = treffer_eid or s.get("unbek_eid")
                    ziel = f'/event/{urllib.parse.quote(str(_z))}' if _z else "/unbekannte"
                    # Zuweisen DIREKT an der Karte (User-Entscheid 25.07. abends): Klappe mit den
                    # Gesichtern der Identitaet, JEDES einzeln anwaehlbar — ausdruecklich KEINE
                    # Pauschal-Zuweisung der ganzen Identitaet, weil das Clustering (Greedy-Seed,
                    # #57) Identitaeten mischt und Nicht-Gesichter buendelt: der Nutzer sieht, was
                    # er uebernimmt, und klickt es bewusst an ("der Benutzer sollte klicken,
                    # welches der unbekannten Gesichter er hinzufuegen moechte"). Uebernahme laeuft
                    # ueber den BESTEHENDEN Weg /anlernen_benennen (gleiches Verfahren wie die
                    # Vorschlags-Seite) — beste Bilder werden Referenzen.
                    klappe = ""
                    if uid:
                        # User-Feedback 25.07. (Screenshot-Test): "hier wuerde ich auf einen
                        # unknown klicken um den zuzuweisen" — der natuerliche Klick ist die
                        # KARTE, nicht ein Extra-Knopf daneben. Also: uid-Karte klappt beim
                        # Klick das Zuweisungsfeld auf; der Sprung zum Event liegt als Link IM
                        # Feld. Karten ohne uid verlinken weiter direkt aufs Event.
                        pass
                    if uid:
                        _mem = alle_member[:12]
                        _thumbs = "".join(
                            f'<label class="ukw"><input type="checkbox" class="ukcb-{html.escape(uid)}" '
                            f'value="{html.escape(str(_m))}">'
                            f'<img src="/anlern/crops/{urllib.parse.quote(str(_m))}.jpg" alt=""></label>'
                            for _m in _mem)
                        klappe = (
                            f'<div class="ukpanel" id="ukp-{html.escape(uid)}" hidden>'
                            f'<div class="dim" style="margin-bottom:4px">Tick the faces that really '
                            f'belong to this person — junk stays behind:</div>'
                            f'<div class="ukthumbs">{_thumbs}</div>'
                            f'<input list="personen-liste" id="ukperson-{html.escape(uid)}" '
                            f'placeholder="person (new or existing)" style="margin:6px 4px 0 0">'
                            f'<button class="gtb on" onclick="ukZuweisen(\'{html.escape(uid)}\',this)">'
                            f'Add selected faces</button> '
                            f'<span class="dim" id="ukst-{html.escape(uid)}"></span>'
                            f'<a class="fussnote" style="float:right" href="{ziel}">open event →</a></div>')
                    # "N faces" war falsch: `unbek` zaehlt EVENTS, nicht Gesichter (heute 43 Events
                    # gegen 657 in ihren faces-Feldern). Die faces-Zahl selbst taugt hier ohnehin
                    # nicht als Aussage, weil darin SCRFD-Fehldetektionen stecken (Gras, Laub,
                    # Radkasten — genau der Grund, aus dem die alte Kennzahlkachel abgeschafft
                    # wurde). Also die Zahl nennen, die stimmt, und sie richtig benennen.
                    if uid:
                        huelle_auf = (f'<div{_uk_anker} class="pk pk-unbek pk-klick" role="button" tabindex="0" '
                                      f'title="Click to assign these faces" '
                                      f'onclick="ukKlappe(\'{html.escape(uid)}\')">')
                        huelle_zu = '</div>'
                    else:
                        huelle_auf = f'<a{_uk_anker} class="pk pk-unbek" href="{ziel}">'
                        huelle_zu = '</a>'
                    _av_bild = (f'<img src="/anlern/crops/{urllib.parse.quote(str(alle_member[0]))}.jpg" '
                                f'alt="">' if alle_member else "?")
                    pkarten.append(
                        f'<div class="pkwrap">'
                        f'{huelle_auf}'
                        f'<div class="pk-av pk-av-unbek">{_av_bild}</div>'
                        f'<div class="pk-txt"><div class="pk-name">{html.escape(name)}</div>'
                        f'<div class="pk-meta">{s["unbek"]} event{"s" if s["unbek"] != 1 else ""} · '
                        f'{spanne} · {nk} camera{"s" if nk != 1 else ""}</div>{zusatz}</div>'
                        f'{huelle_zu}'
                        f'{klappe}</div>')
                # Leerzustand nach URSACHE (Plan-QS P.6): ein frisches System hat drei sehr
                # verschiedene Gruende fuer eine leere Seite, und nur einer davon ist "heute war
                # niemand da". Ohne Frigate-URL kann nie etwas kommen; ohne Referenzgesichter
                # wird KEIN Event verarbeitet (der Wizard behauptete frueher das Gegenteil).
                if not pkarten and not (cfg.get("frigate_url") or "").strip():
                    band = webui.leer("No Frigate connected yet.",
                                      "Set your Frigate URL in the setup wizard (Settings) — "
                                      "then passes appear here automatically.")
                elif not pkarten and not master_persons(cfg):
                    band = webui.leer("Connected — but no reference faces yet, so nobody can "
                                      "be recognized.",
                                      "Import faces from Frigate or upload photos — both on the "
                                      "Known page. suslik then keeps learning from the "
                                      "cameras on its own.")
                elif pkarten:
                    band = f'<div class="pband">{"".join(pkarten)}</div>'
                else:
                    band = webui.leer("Nothing with a face " + ("yet today." if ist_heute else "on this day."),
                                      "People appear here as soon as a pass is analysed.")
                # Ab Werk ist JEDER Meldeweg aus — wer auf die erste Meldung wartet, wartet
                # vergebens und erfaehrt es sonst nirgends (Plan-QS P.8).
                _kanal_da = (cfg.get("telegram_modus", "aus") != "aus"
                             or bool((cfg.get("pushover") or {}).get("token"))
                             or bool(cfg.get("mqtt_publish")))
                if ist_heute and not _kanal_da:
                    band += ('<p class="dim" style="margin-top:8px">No alert channel configured '
                             'yet — recognitions appear here, but nothing will notify you. '
                             '<a href="/benachrichtigungen">Set one up in Notifications.</a></p>')
                # Randspalte: alles, was NICHT "wer war da" ist — bewusst leise.
                unbek_txt = (f'{len(unbek_echt)} pass{"es" if len(unbek_echt) != 1 else ""} '
                             f'with nobody recognized' if unbek_echt else 'none unidentified')
                neben = (
                    '<aside class="tagseite">'
                    # Areas: die Randspalte traegt die aktive Sicht im Kopf — sonst laese sich
                    # "Events analysed 6" wie eine Tages-Gesamtzahl (Fehlerklasse Darstellung).
                    # Auswahl-Semantik (.92): Paesse = beruehrt die Area, gezeigt wird der GANZE
                    # Durchgang; die Event-Zaehler unten zaehlen die Kameras der Area.
                    + (f'<div class="ts-block"><div class="ts-lab">Area view</div>'
                       f'<div class="ts-meta">{html.escape(_ar_aktiv)}: passes that touched this '
                       f'area (each shown in full); event counts cover its cameras only'
                       f'</div></div>' if _nk is not None else '')
                    + '<div class="ts-block"><div class="ts-lab">'
                    '<a href="#unidentified" class="ts-link">Unidentified</a></div>'
                    # Baustein A: hat der Pool Unbekannt-Stuetzen im Tag, traegt ER die
                    # Kachel-Zahl (PERSONEN aus einer Quelle, nicht Passes) — auch und
                    # gerade, wenn die Unbekannten innerhalb erkannter Passes liefen.
                    # "today"/"on this day" folgt der Tagesnavigation (Widerleger MUSS-3:
                    # das Fenster war schon der ANGEZEIGTE Tag, nur das Wort log). Ohne
                    # Pool-Stuetzen im Tag bleibt die alte Anzeige unveraendert.
                    + (f'<div class="ts-val">{pool_unbek_n}</div>'
                       f'<div class="ts-meta"><a class="ts-link" href="/unbekannte">'
                       f'{pool_unbek_n} unknown person{"s" if pool_unbek_n != 1 else ""} '
                       f'{"today" if ist_heute else "on this day"} '
                       f'({pool_auftritte} appearance{"s" if pool_auftritte != 1 else ""}) '
                       f'— see Unknown</a></div>'
                       if pool_unbek_n else f'<div class="ts-val">{len(unbek_echt)}</div>')
                    # EINE widerspruchsfreie Kachel (Widerleger MUSS-1, Realfall 12.08.:
                    # "none unidentified" stand direkt unter "16 unknown persons today"):
                    # neben der Pool-Zeile erscheint die Pass-Zeile nur, wenn sie selbst
                    # etwas meldet — ein leeres unbek_echt schweigt dann, statt der
                    # Pool-Zahl zu widersprechen. Ohne Pool-Zeile alte Anzeige.
                    + (f'<div class="ts-meta">{html.escape(unbek_txt)}</div>'
                       if unbek_echt or not (pool_unbek_n or pool_archiv_n) else '')
                    # Widerleger MUSS-2 (U155): Archiv-Cluster mit frischer Fenster-
                    # Stuetze als eigene Zeile — nie still verstecken; der naechste
                    # Reconcile (Reorganize) reaktiviert sie automatisch und laut.
                    + (f'<div class="ts-meta">{pool_archiv_n} more in archived '
                       f'cluster{"s" if pool_archiv_n != 1 else ""} — reactivated by '
                       f'the next reorganize</div>' if pool_archiv_n else '')
                    # Der "normally the same people"-Satz war im Besuchsfall die Luege:
                    # mit frischen Unbekannt-Stuetzen im Tag heisst es ehrlich, dass
                    # mindestens ein Teil davon unbekannte Besucher sind.
                    + ((f'<div class="ts-meta">plus {unbek_nebenbei} event'
                        f'{"s" if unbek_nebenbei != 1 else ""} not matched inside '
                        f'recognized passes — at least some belong to unknown visitors '
                        f'(<a class="ts-link" href="/unbekannte">see Unknown</a>)</div>')
                       if unbek_nebenbei and (pool_unbek_n or pool_archiv_n) else
                       (f'<div class="ts-meta">plus {unbek_nebenbei} event'
                        f'{"s" if unbek_nebenbei != 1 else ""} not matched inside '
                        f'recognized passes — normally the same people</div>'
                        if unbek_nebenbei else ''))
                    + '</div>'
                    '<div class="ts-block"><div class="ts-zeile"><span><a href="#passes" class="ts-link">Passes</a></span>'
                    f'<span class="num">{len(interessant)}</span></div>'
                    f'<div class="ts-zeile"><span><a class="ts-link" '
                    f'href="/ereignisse?tag={tag_dt.strftime("%Y-%m-%d")}{_aq}">Events analysed</a></span>'
                    f'<span class="num">{z_events}</span></div>'
                    f'<div class="ts-zeile"><span>Alerts sent (Pushover)</span><span class="num">{z_alerts}</span></div>'
                    f'<div class="ts-zeile"><span>Presence pushes (Pushover)</span><span class="num">{z_presence}</span></div>'
                    # Baustein B: eigene Zeile NEBEN den Event-Zaehlern — Live-
                    # Meldungen kommen aus der Engine, nicht aus der Event-
                    # Analyse, und wuerden in "Alerts sent" die Summen luegen.
                    # KANN-7: kanalneutral (Summe), Aufschluesselung je real
                    # benutztem Kanal darunter — nie "Pushover 0" als einzige
                    # Wahrheit einer Telegram-only-Installation.
                    + ((f'<div class="ts-zeile"><span><a class="ts-link" '
                        f'href="/live_alerts?tag={tag_dt.strftime("%Y-%m-%d")}">'
                        f'Live watcher alerts</a></span>'
                        f'<span class="num">{z_live}</span></div>'
                        + (f'<div class="ts-meta">'
                           + " · ".join(f"{k} {n}"
                                        for k, n in z_live_kanaele.items())
                           + '</div>' if z_live_kanaele else ''))
                       if _live_zeile else '')
                    + '</div></aside>')
                # .190 (User 13.08., ersetzt die .188-Sidebar-Liste): die
                # Live-Trigger als KARTENREIHE unter Recognized — Beweisbild
                # (Protokoll-Feld bild, ALARMBILD_RE-Vertrag), Schnell-
                # Urteils-Name oder "unknown", Zeit + Kamera. Das Label sagt
                # die VORLAEUFIGKEIT laut (Trigger != Urteil).
                live_reihe = ""
                # .195 (User: "nicht konsequent"): Karten sind jetzt
                # AUFTRITTE (auftritts_gruppen), der Klick fuehrt zur
                # Auftrittskarte der Tagesansicht mit ALLEN Gesichts-Crops —
                # analog der Pass-Ansicht, nicht mehr nur ein Einzelbild.
                _erkannt = [a for a in _lwz.auftritts_gruppen(z_live_liste)
                            if a.get("person")] if z_live_liste else []
                if _erkannt:
                    _lk = []
                    for g in _erkannt[:8]:
                        _bu = (f'/live_alarmbild?p='
                               f'{urllib.parse.quote(g["bild"])}'
                               if g.get("bild") else "")
                        _au = (f'/live_alerts?tag='
                               f'{time.strftime("%Y-%m-%d", time.localtime(g["ts"]))}'
                               f'#a{int(g["ts"])}')
                        _lk.append(
                            '<div class="card lv-alarmkarte">'
                            + (f'<a href="{_au}">'
                               f'<img class="lv-alarmbild" '
                               f'loading="lazy" src="{_bu}" alt=""></a>'
                               if _bu else '')
                            + f'<div><b>{html.escape(g["person"])}</b>'
                            + f'<div class="dim">'
                              f'{time.strftime("%H:%M", time.localtime(g["ts"]))}'
                              f' · {html.escape(g["kamera"])}</div></div></div>')
                    live_reihe = (
                        '<div class="listhead"><h3>Recognized live</h3>'
                        '<span class="cnt">quick check, preliminary — '
                        f'{len(_erkannt)} appearance'
                        f'{"" if len(_erkannt) == 1 else "s"}, '
                        f'{z_live_gruppen} trigger'
                        f'{"" if z_live_gruppen == 1 else "s"}</span></div>'
                        '<div class="lv-alarmreihe">' + "".join(_lk)
                        + (f'<div class="dim lv-alarmmehr">… '
                           f'{len(_erkannt) - 8} more</div>'
                           if len(_erkannt) > 8 else '')
                        + '</div>')
                _dl = ('<datalist id="personen-liste">'
                       + "".join(f'<option value="{html.escape(p)}">' for p in master_persons(cfg))
                       + '</datalist>')
                inhalt = (f'{_dl}{nav_tag}'
                          f'<div class="tagraster"><div>'
                          f'<div class="listhead" id="recognized"><h3>Recognized</h3>'
                          f'<span class="cnt">{len(pers_tag)} '
                          f'{"person" if len(pers_tag) == 1 else "people"}</span></div>{band}'
                          f'{live_reihe}'
                          f'<div class="listhead" id="passes"><h3>Passes</h3>'
                          f'<span class="cnt">{cnt}</span></div>'
                          f'{liste}{motiv}</div>{neben}</div>')
                # Auto-Aktualisierung NUR am heutigen Tag: ein vergangener Tag aendert sich nicht
                # mehr, ein Reload wuerde nur die Position im Blaettern zerstoeren.
                return self._send(200, webui.layout(_titel, "/heute", inhalt, self._banner(),
                                                    refresh=(30 if live_offen else 120) if ist_heute else 0))
            if path == "/lernlauf/anker":
                # E3-Ansicht (read-only): Cluster mit Crops — der erste Blick vor
                # der Benennung. Renderer im Modul (I1), hier nur Daten + Layout.
                # .83: ?a=<anker_id> oeffnet die Detail-Seite ALLER Crops des Clusters.
                import webui
                from core import lernlauf as _ll
                from routes import lernanker as _r_ank
                saetze, kaputt = _ll.anker_lesen(cfg["data_dir"])
                qd = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                aid = (qd.get("a", [""])[0] or "").strip()
                if aid:
                    satz = next((s for s in saetze if s.get("anker_id") == aid), None)
                    if satz:
                        # E4a Zug 2b: die Detail-Seite IST der Benennungs-Fluss —
                        # Kontext (Empfehlung/Personen/Vorschlag) rechnet das Modul.
                        from core import benennung as _bn
                        bkt = _bn.benennungs_kontext(
                            satz, saetze, master_persons(cfg),
                            {k: cfg["benennung_" + k] for k in
                             ("k_je_bin", "yaw_grenze", "dup_sim", "vorschlag_schwelle")},
                            _ll.person_norm,
                            referenz=_bn.referenz_zentroide(
                                os.path.join(cfg["data_dir"], "clips",
                                             "refcache.npz"), cfg["modell"]))
                        return self._send(200, webui.layout(
                            "Anchor", "/lernlauf/anker",
                            _r_ank.anker_detail_seite(satz, kaputt, benennung=bkt),
                            self._banner()))
                # Uebersichts-Zusatz (User 05.08.): looks-like-Vorschlag je
                # Cluster (gleiche Rechnung wie die Detail-Seite, nur ohne das
                # teure empfehlen()) + Lauf-uebergreifende Dubletten-Erkennung
                # (Wiederernte derselben unbenannten Leute: Event-Ueberlapp).
                from core import benennung as _bn2
                vorschlaege, dubletten = {}, {}
                try:
                    _q = _bn2.personen_quelle(
                        master_persons(cfg), saetze, _ll.person_norm,
                        referenz=_bn2.referenz_zentroide(
                            os.path.join(cfg["data_dir"], "clips",
                                         "refcache.npz"), cfg["modell"]))
                    for s in saetze:
                        if s.get("status") in ("benannt", "uebernommen", "verworfen"):
                            continue
                        v, _n = _bn2.person_vorschlag(
                            s.get("zentroid"), _q,
                            cfg["benennung_vorschlag_schwelle"])
                        if v:
                            vorschlaege[s["anker_id"]] = v
                    offene = [s for s in saetze
                              if s.get("status") not in ("benannt", "uebernommen",
                                                         "verworfen")]
                    ev = {s["anker_id"]: {str(m.get("event"))
                                          for m in (s.get("mitglieder") or [])
                                          if m.get("event")} for s in offene}
                    offene.sort(key=lambda s: str((s.get("lauf") or {})
                                                  .get("lauf_id", "")))
                    for i, alt_s in enumerate(offene):
                        for neu_s in offene[i + 1:]:
                            a, b = ev[alt_s["anker_id"]], ev[neu_s["anker_id"]]
                            # Event-Ueberlapp ALLEIN verkoppelt zwei Personen,
                            # die zusammen durchs Bild liefen — der Zentroid-
                            # Kosinus trennt (am Echtbestand 05.08. kalibriert:
                            # echte Wiederernten 0.945-1.0, Fremd-Paar faellt).
                            c = _bn2._cos(alt_s.get("zentroid"),
                                          neu_s.get("zentroid"))
                            if a and b and len(a & b) >= 0.8 * min(len(a), len(b)) \
                                    and c is not None and c >= 0.9:
                                dubletten[alt_s["anker_id"]] = neu_s["anker_id"]
                                break
                except Exception:
                    pass                       # Zusatz-Nutzen, nie Seiten-Blocker
                return self._send(200, webui.layout(
                    "Anchors", "/lernlauf/anker",
                    _r_ank.anker_seite(saetze, kaputt, vorschlaege, dubletten),
                    self._banner()))
            if path.startswith("/lernlauf/crop/"):
                # Lauf-Crops (Containment wie /refs/: realpath-Wache gegen Traversal).
                m = re.match(rf"^/lernlauf/crop/(L[\w]+)/({_reg.DATEI_RE}\.jpg)$", path)
                if m:
                    base = os.path.realpath(os.path.join(
                        cfg["data_dir"], "state", "lernlauf", m.group(1), "crops"))
                    p = os.path.realpath(os.path.join(base, m.group(2)))
                    if p.startswith(base + os.sep) and os.path.isfile(p):
                        return self._send(200, open(p, "rb").read(), "image/jpeg")
                return self._send(404, "not found", "text/plain")
            if path.startswith("/personlauf/bild/"):
                # PE2: Crop-Auslieferung mit Containment (Muster /lernlauf/crop)
                _rel = urllib.parse.unquote(path[len("/personlauf/bild/"):])
                _lid, _, _datei = _rel.partition("/")
                _wurz = os.path.normpath(os.path.join(cfg["data_dir"],
                                                      "personlern"))
                _voll = os.path.normpath(os.path.join(_wurz, _lid, "crops",
                                                      _datei))
                if _voll.startswith(_wurz + os.sep) and os.path.isfile(_voll):
                    return self._send(200, open(_voll, "rb").read(),
                                      "image/jpeg")
                return self._send(404, b"gone")
            if path.startswith("/personlauf/fremdbild/"):
                # .145: Fremd-Pool-Ansicht — Auslieferung mit Containment
                # (Muster /personlauf/bild), jpg/png nach Endung.
                _datei = urllib.parse.unquote(
                    path[len("/personlauf/fremdbild/"):])
                _wurz = os.path.normpath(os.path.join(
                    cfg["data_dir"], "personlern", "fremd"))
                _voll = os.path.normpath(os.path.join(_wurz, _datei))
                if _voll.startswith(_wurz + os.sep) and os.path.isfile(_voll):
                    _e = os.path.splitext(_voll)[1].lower()
                    _typ = {".png": "image/png",
                            ".webp": "image/webp"}.get(_e, "image/jpeg")
                    return self._send(200, open(_voll, "rb").read(), _typ)
                return self._send(404, b"gone")
            if path.startswith("/person/kontrolle/bild/"):
                # Z8: Kontroll-Bild ausliefern. Containment wie /person/treffer
                # (realpath-Wache), aber ein AUSBRUCHS-Versuch ist eine schlechte
                # Anfrage (400) und kein fehlendes Bild (404) — die beiden Faelle
                # zu vermischen hat schon einmal einen Fund verdeckt.
                _b = os.path.realpath(os.path.join(cfg["data_dir"], "personlern",
                                                   "kontrolle"))
                _m = re.fullmatch(rf"/person/kontrolle/bild/({_reg.DATEI_RE})"
                                  rf"/({_reg.DATEI_RE}\.jpg)",
                                  urllib.parse.unquote(path))
                if not _m:
                    return self._send(400, b"bad path")
                _p = os.path.realpath(os.path.join(_b, _m.group(1), _m.group(2)))
                if not _p.startswith(_b + os.sep):
                    return self._send(400, b"bad path")
                if not os.path.isfile(_p):
                    return self._send(404, b"gone")
                return self._send(200, open(_p, "rb").read(), "image/jpeg")
            if path == "/person/kontrolle":
                import webui
                # Z8 (konzept_frames.md §7): Kachel-Browser der BEURTEILTEN Bilder,
                # je Durchgang gruppiert (Szenario-Prinzip), view-only. Was die Seite
                # zeigt, entscheidet der Schalter diagnostic_collection — der Renderer
                # bekommt ihn mit und erklaert den leeren Fall, statt ihn zu verschweigen.
                from core import personlive as _plv
                from routes import personwizard as _r_pw
                inhalt = _r_pw.kontrolle_seite(
                    _plv.kontrolle_lesen(cfg["data_dir"]),
                    bool(cfg.get("diagnostic_collection")))
                return self._send(200, webui.layout(
                    "Person", "/person/kontrolle", inhalt, self._banner()))
            m = re.match(r"^/person/treffer/([\w.\-]+)\.jpg$", path)
            if m:                # Koerper-Treffer-Crop (Chip-Bild, .120)
                base = os.path.realpath(os.path.join(cfg["data_dir"],
                                                     "personlern", "treffer"))
                p = os.path.realpath(os.path.join(base, m.group(1) + ".jpg"))
                if p.startswith(base + os.sep) and os.path.isfile(p):
                    return self._send(200, open(p, "rb").read(), "image/jpeg")
                return self._send(404, b"gone")
            if path == "/person/modell":
                import webui
                # PE3-Status als eigener Reiter im Person-Bereich (User).
                from core import personlive as _plv
                from core import personmodell as _pm
                from routes import personwizard as _r_pw
                # Standard-Werte der Feuer-Regel kommen aus personlive (eine
                # Quelle, kein Streu-Literal); Grenzen aus personmodell.
                regeln = {"fenster_s": _plv.FENSTER_S,
                          "feuer_ab": _plv.FEUER_AB,
                          "karenz_s": _plv.KARENZ_S,
                          "schwelle_std": _plv.SCHWELLE_STD,
                          "grenzen": _pm.REGEL_GRENZEN}
                inhalt = _r_pw.modell_seite(_pm.status_lesen(cfg["data_dir"]),
                                            regeln)
                return self._send(200, webui.layout(
                    "Person", "/person/modell", inhalt, self._banner()))
            if path in ("/person", "/personlauf/bestand"):
                import webui
                # PE2b (User 04.08.: Anchors-Pendant fuer Personen), seit
                # abends EIGENER Hauptbereich "Person" neben People (People
                # = Gesichter, Person = Koerper-Bilder). Alte Learn-URL
                # bleibt als Alias. .145 (User 07.08.): ?wer=<Gruppe> zeigt
                # NUR deren Bilder (statt Bandwurm), Fremd-Pool als Eintrag.
                from core import personernte as _pe
                from core import personmodell as _pm
                from routes import personwizard as _r_pw
                _qd = urllib.parse.parse_qs(
                    urllib.parse.urlparse(self.path).query)
                _wer = (_qd.get("wer", [""])[0] or "").strip()
                _fdir = os.path.join(cfg["data_dir"], "personlern", "fremd")
                try:
                    _fremd = sorted(
                        (f for f in os.listdir(_fdir)
                         if f.lower().endswith(_reg.BILD_ENDUNGEN)
                         and os.path.isfile(os.path.join(_fdir, f))),
                        reverse=True)
                except OSError:
                    _fremd = []
                inhalt = _r_pw.bestand_seite(
                    _pe.laeufe_lesen(cfg["data_dir"]),
                    modell=_pm.status_lesen(cfg["data_dir"]),
                    wer=_wer, fremd=_fremd)
                return self._send(200, webui.layout(
                    "Person", "/person", inhalt, self._banner()))
            if path == "/personlauf/abnahme":
                import webui
                # PE2 (User 04.08.: "haette ich jetzt nicht die Bilder
                # pruefen sollen?"): Klick-Abnahme des letzten Laufs.
                from core import personlauf as _pl
                from core import personernte as _pe
                from routes import personwizard as _r_pw
                _z = _pl.zustand_lesen(cfg["data_dir"]) or {}
                _lid = str(_z.get("lauf_id") or "")
                _zeilen, _markiert = [], set()
                if _lid:
                    _mp = _pe.manifest_pfad(cfg["data_dir"], _lid)
                    if os.path.exists(_mp):
                        _zeilen = [json.loads(l) for l in open(_mp)
                                   if l.strip()]
                    _up = os.path.join(_pe.lauf_dir(cfg["data_dir"], _lid),
                                       "urteile.jsonl")
                    if os.path.exists(_up):
                        for l in open(_up):
                            if l.strip():
                                _u = json.loads(l)
                                (_markiert.add if _u["urteil"] == "falsch"
                                 else _markiert.discard)(_u["datei"])
                inhalt = _r_pw.abnahme_seite(_z, _zeilen, _markiert)
                return self._send(200, webui.layout("Learn", "/personlauf",
                                                    inhalt, self._banner()))
            if path == "/personlauf":
                import webui
                # PE1 Baustein 2 (stufe2.md): Person-Learn-Wizard, Anzeige-
                # Teil — Lauf/Worker-Job folgt als Baustein 3. Personen-
                # Quelle = Master-Ordner unter <data_dir>/faces (wie :508).
                from routes import personwizard as _r_pw
                _qd = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                try:
                    _pn = int((_qd.get("events", [""])[0] or "0") or 0)
                except ValueError:
                    _pn = 0
                _pn = max(0, _pn)
                _pp = (_qd.get("person", [""])[0] or "").strip()
                _fd = os.path.join(cfg["data_dir"], "faces")
                try:
                    _pers = sorted(d for d in os.listdir(_fd)
                                   if os.path.isdir(os.path.join(_fd, d)))
                except OSError:
                    _pers = []
                # .147: "FREMD" ist reservierte Wahl (Fremd-Sammel-Lauf)
                if _pp and _pp != "FREMD" and _pp not in _pers:
                    _pp = ""
                from core import personlauf as _pl
                _z = _pl.zustand_lesen(cfg["data_dir"])
                # Dienst-Neustart: Disk-Phase 'aktiv' ohne lebenden Thread =
                # unterbrochen — Formular freigeben, Neustart resumed per eids
                if _z and _z.get("phase") in ("vorbereitung", "ernte"):
                    _lebt = bool(getattr(svc, "_personlauf_thread", None)
                                 and svc._personlauf_thread.is_alive())
                    if not _lebt:
                        _z = dict(_z, phase="unterbrochen")
                from core import personmodell as _pm
                inhalt = _r_pw.wizard(_pers, _pn or None, _pp,
                                      bilanz={"n": _pn} if _pn else None,
                                      lauf=_z,
                                      modell=_pm.status_lesen(cfg["data_dir"]))
                _tickt = bool(_z and _z.get("phase") in ("vorbereitung",
                                                         "ernte"))
                return self._send(200, webui.layout("Learn", "/personlauf",
                                                    inhalt, self._banner(),
                                                    refresh=3 if _tickt else None))
            if path == "/lernlauf":
                import webui
                # E1 (S6): Anlern-Wizard + Lauf-Seite (Shadow — plant, lernt nichts).
                from core import ereignisse as _evm
                from core import lernlauf as _ll
                from core import wanduhr as _wu
                from routes import lernwizard as _r_wiz
                zustand, _lerr = _ll.lauf_lesen(cfg["data_dir"])
                # .89: fertiger Lauf zeigt 'Start a new run' — ?neu=1 oeffnet
                # den Wizard, OHNE den fertigen Lauf zu trashen (vorher war Abort der
                # einzige Weg zum naechsten Lauf).
                _qd0 = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                # .99-Fix (User-Fund): auch ?events=... ist Wizard-Absicht — die
                # Scope-Knoepfe/das go-Formular tragen kein neu=1, und der fertige
                # Lauf verschluckte sonst Schritt 2 (fps-Karte unerreichbar).
                if zustand and (_qd0.get("neu") or _qd0.get("events")) and str(
                        (zustand.get("fortschritt") or {}).get("status", "")).startswith(
                            ("anchors ready", "anchors: none")):
                    zustand = None
                if zustand:
                    saetze, kaputt = _ll.anker_lesen(cfg["data_dir"])
                    # .83 (Widerleger): 'anchors so far' zaehlt nur den AKTUELLEN Lauf —
                    # vorher zaehlte die Zeile laufuebergreifend und startete den
                    # naechsten Lauf mit den Waisen des abgebrochenen.
                    eigene = [s for s in saetze
                              if (s.get("lauf") or {}).get("lauf_id") == zustand.get("lauf_id")]
                    inhalt = _r_wiz.lauf_seite(zustand, len(eigene), kaputt)
                    f = zustand.get("fortschritt") or {}
                    st = str(f.get("status", ""))
                    # E2: die Seite tickt in Vorbereitung UND Ernte; .83: auch waehrend
                    # der Anker-Phase (vorher fror die Anzeige bei 'grouping starting' ein).
                    tickt = ((zustand.get("phase") in ("vorbereitung", "ernte")
                              and (not st
                                   or st.startswith(("prepared", "harvesting", "waiting"))))
                             or (zustand.get("phase") == "anker"
                                 and not st.startswith(("anchors", "anchor stage failed"))))
                    return self._send(200, webui.layout("Learn", "/lernlauf", inhalt,
                                                        self._banner(),
                                                        refresh=3 if tickt else None))
                qd = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                roh = (qd.get("events", [""])[0] or "").strip().lower()
                alle_modus = roh in ("alle", "all")
                try:
                    # Cap = Pagination-Deckel (Widerleger F2.1/F2.10); <=0 -> keine Wahl
                    auswahl = None if alle_modus else (
                        min(int(roh), svc.LERNLAUF_EVENTS_MAX) if roh else None)
                    if auswahl is not None and auswahl <= 0:
                        auswahl = None
                except ValueError:
                    auswahl = None
                werte, quelle, gemessen_f = _wu.lesen(cfg["data_dir"], _placement_hw_key(),
                                                      os.environ.get("SUSLIK_VERSION", "dev"))
                mess_st = svc.wanduhr_status()        # Anzeige-Status; getriggert wird vom BOOT
                mess_laeuft = bool(mess_st.get("laeuft"))
                bilanz = prog = None
                if auswahl or alle_modus:
                    try:
                        evs, _ = _evm.person_events(lambda p: api(cfg, p),
                                                    None if alle_modus else auswahl)
                        bilanz = _evm.auswahl_bilanz(evs)
                        _cd = os.path.join(cfg["data_dir"], "clips")
                        clips = _evm.clips_fuer_prognose(
                            evs, None, cache_pruefer=lambda eid: os.path.isfile(
                                os.path.join(_cd, str(eid).replace("/", "_") + ".mp4")))
                        prog = _wu.lauf_prognose(werte, clips)
                    except (urllib.error.URLError, OSError, TimeoutError) as e:
                        # ECHTER Frigate-/Netz-Ausfall -> Banner + Seite bleibt nutzbar
                        svc.frigate_fehler = (time.time(), f"event list: {e}")
                        auswahl, alle_modus = None, False
                    except Exception as e:
                        # Widerleger F5.5: interne Fehler NICHT als Frigate-Ausfall
                        # etikettieren — laut loggen, Auswahl-Teil erklaert sich.
                        svc.log(f"lernlauf wizard: estimate failed ({type(e).__name__}: {e})")
                        auswahl, alle_modus = None, False
                schwellen = [(k, cfg.get(k)) for k in
                             ("det_thresh", "fd_front_min", "fd_sharp_min", "fd_det_max",
                              "win_thresh",
                              # E2: alle drei Ernte-Gates sichtbar (L = fd_* oben)
                              "ernte_m_det_min", "ernte_m_kante_min", "ernte_m_sharp_min",
                              "ernte_s_det_min", "ernte_s_winkel_max")]
                # Unbekannt-Sichtbarkeit Baustein B (12.08.): der Wizard ist ein
                # separater Lauf — wer nach einem Besuch hier landet, erfuhr nirgends,
                # dass der Pool schon frische Unbekannt-Cluster von heute bereithaelt.
                # DIESELBE Ableitung wie die Today-Kachel (core/unbekanntpool, Fenster
                # = heutiger Tag), keine zweite Zaehlung.
                from core import unbekanntpool as _ubp
                _ub_tag = datetime.datetime.now().replace(hour=0, minute=0,
                                                          second=0, microsecond=0)
                _ub_k = len(_ubp.tages_cluster(
                    cfg["data_dir"], _ub_tag.timestamp(),
                    (_ub_tag + datetime.timedelta(days=1)).timestamp(),
                    int(cfg.get("szenario_gap_min", 5)) * 60, log=svc.log))
                inhalt = _r_wiz.wizard(len(master_persons(cfg)), auswahl, bilanz, prog,
                                       quelle, schwellen, mess_laeuft,
                                       gemessen_felder=gemessen_f, alle=alle_modus,
                                       max_events=svc.LERNLAUF_EVENTS_MAX,
                                       mess_wartet=(mess_st.get("phase") == "waiting"),
                                       mess_skip=(mess_st.get("uebersprungen") or ""),
                                       unbekannt_offen=_ub_k)
                return self._send(200, webui.layout("Learn", "/lernlauf", inhalt,
                                                    self._banner()))
            if path == "/lernen":
                import webui
                # M1b (S5): Rendern byte-treu in routes/lernen.py; Queue-Zugriff und die
                # Drift-Warnungs-Bindung (Thread-Race-Schutz, s.u.) bleiben beim Dienst.
                from routes import lernen as _r_lernen
                q = svc._enroll_queue()
                offen = sorted((d for d in q.values() if d.get("status") == "offen"),
                               key=lambda d: -d.get("ts", 0))
                warnung = None
                # einmal binden: der Drift-Waechter-Thread setzt enroll_warnung waehrenddessen
                # auf None zurueck — zwischen Pruefung und Zugriff [0]/[1] haette das ein
                # TypeError-500 statt der Seite ergeben (wie _banner es fuer frigate_fehler macht)
                w = svc.enroll_warnung
                if w and time.time() - w[0] < 86400:
                    warnung = "DRIFT GUARD RED after the last add — details on the System page!"
                inhalt = _r_lernen.render(offen, master_persons(cfg), cfg["data_dir"])
                return self._send(200, webui.layout("Enroll", "/lernen", inhalt, warnung or self._banner()))
            if path.startswith("/refs/"):              # Master-Referenzbilder (read-only, Containment)
                # ~ auch hier (Issue-#11-Klasse): uebernommene Lern-Referenzen behalten
                # den Crop-Namen (lern_<anker>_<eid>~N.jpg) — ohne ~ waeren sie auf der
                # Personen-Seite unsichtbar, derselbe 404 wie bei /anlern/crops/.
                m = re.match(rf"^/refs/({_reg.PERSON_RE})/({_reg.DATEI_RE}\.(?:jpg|jpeg|png|webp))$", path, re.I)
                if m:
                    base = os.path.realpath(os.path.join(cfg["data_dir"], "faces"))
                    p = os.path.realpath(os.path.join(base, m.group(1), m.group(2)))
                    if p.startswith(base + os.sep) and os.path.isfile(p):
                        return self._send(200, open(p, "rb").read(), "image/jpeg")
                return self._send(404, "not found", "text/plain")
            if path == "/anlernen":     # Cluster (alter Ephemeral-Clustering-Weg) von Unknown abgeloest (22.07.)
                return self._send(302, "", "text/plain", location="/unbekannte")
            if path == "/unbekannte":                    # persistente Unbekannt-Identitaeten (User 20.07.)
                import webui, anlernen
                import numpy as _np
                # kaputte Pool-Zeilen duerfen die Seite nie toeten (kc_phase34 R-2):
                # nur Dicts mit Listen-members kommen in die Darstellung
                idents = [u for u in anlernen.lade_unbekannte()
                          if isinstance(u, dict) and isinstance(u.get("members"), list)]
                faces = {g["id"]: g for g in anlernen.lade_gesichter()}
                vors = anlernen.lade_unbekannt_vorschlaege()
                opts = "".join(f"<option>{html.escape(p)}</option>" for p in master_persons(cfg))

                def _info(u):
                    mids = [m for m in u.get("members", []) if m in faces]
                    if not mids:
                        return None
                    cams = {}
                    for m in mids:
                        c = str(faces[m].get("camera", "?"))
                        cams[c] = cams.get(c, 0) + 1
                    tss = [faces[m]["ts"] for m in mids]
                    rep = max(mids, key=lambda m: faces[m].get("guete", 0))
                    coh = 1.0
                    if len(mids) > 1:
                        M = _np.asarray([faces[m]["emb"] for m in mids], dtype=_np.float32)
                        M = M / (_np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
                        S = M @ M.T
                        coh = float((S.sum() - len(mids)) / (len(mids) * (len(mids) - 1)))
                    return {"u": u, "mids": mids, "cams": cams, "von": min(tss), "bis": max(tss),
                            "rep": rep, "coh": coh, "n": len(mids)}

                infos = [i for i in (_info(u) for u in idents) if i]
                # Statische Objekte (Radkasten, Lichtflecken — Objekt-Regel des Reconcile,
                # 25.07.) raus aus den Personen-Eimern: sie sind keine Besucher und duerfen
                # nirgends als "Unknown N" zum Anlernen angeboten werden. Eigener Eimer
                # unten, damit sichtbar bleibt, WAS aussortiert wurde (kein stiller Verlust).
                objekte = [i for i in infos if i["u"].get("objekt")]
                infos = [i for i in infos if not i["u"].get("objekt")]
                aktiv = sorted((i for i in infos if i["u"].get("status", "aktiv") == "aktiv"),
                               key=lambda i: -i["bis"])
                besucher = [i for i in infos if i["u"].get("status") == "besucher"]
                wieder = [i for i in aktiv if i["n"] >= 2]
                einzeln = [i for i in aktiv if i["n"] == 1]

                def _tag(t0, t1):
                    d0 = datetime.datetime.fromtimestamp(t0)
                    d1 = datetime.datetime.fromtimestamp(t1)
                    if d0.date() == d1.date():
                        s = d0.strftime("%d.%m. %H:%M")
                        return s if t1 - t0 < 60 else f"{s}–{d1.strftime('%H:%M')}"
                    return f"{d0.strftime('%d.%m.')}–{d1.strftime('%d.%m.')}"

                def _kachel(i, besuch=False):
                    u = i["u"]
                    uid = html.escape(u["id"], quote=True)
                    name = html.escape(u["id"].replace("U", "Unknown "))
                    thumbs = "".join(
                        f'<img src="/anlern/crops/{urllib.parse.quote(m)}.jpg" alt="">'
                        for m in sorted(i["mids"], key=lambda m: -faces[m].get("guete", 0))[:6])
                    if i["coh"] >= 0.55:
                        sicher = '<span class="badge ok">clearly one person</span>'
                    elif i["n"] > 1:
                        sicher = f'<span class="badge">similarity {i["coh"]:.2f}</span>'
                    else:
                        sicher = '<span class="badge">seen once</span>'
                    cams = " · ".join(f'{html.escape(c)} {n}'
                                      for c, n in sorted(i["cams"].items(), key=lambda x: -x[1]))
                    andere = "".join(
                        f'<option value="{html.escape(j["u"]["id"], quote=True)}">'
                        f'{html.escape(j["u"]["id"].replace("U", "Unknown "))}</option>'
                        for j in aktiv if j["u"]["id"] != u["id"])
                    if besuch:
                        akt = (f'<button class="gtb" onclick="unbBesucher(\'{uid}\',false,this)">'
                               'reactivate</button>')
                    else:
                        akt = (f'<input id="nm-{uid}" placeholder="Name (new or existing)" list="pers-list">'
                               f'<button class="gtb on" onclick="unbBenennen(\'{uid}\',this)">Assign person</button>'
                               f'<button class="gtb" onclick="unbBesucher(\'{uid}\',true,this)">Ignore</button>'
                               + (f'<select id="mg-{uid}"><option value="">merge with…</option>{andere}</select>'
                                  f'<button class="gtb" onclick="unbMerge(\'{uid}\',this)">OK</button>' if andere else ''))
                    return (
                        f'<div class="uk" id="uk-{uid}">'
                        f'<div class="uk-kopf">'
                        f'<img class="uk-face" src="/anlern/crops/{urllib.parse.quote(i["rep"])}.jpg" alt="">'
                        f'<div style="min-width:0"><div class="uk-titel">{name}</div>'
                        f'<div class="uk-meta"><span class="num">{i["n"]}</span> appearances · {_tag(i["von"], i["bis"])}</div>'
                        f'<div class="chips">{sicher}<span class="chip">{cams}</span></div></div></div>'
                        f'<div class="streifen">{thumbs}</div>'
                        f'<div class="uk-akt">{akt}</div></div>')

                vors_html = ""
                # Vorschlag MIT Gesichtern (User 25.07., Screenshot: "welche Person soll same
                # person sein?" — eine Gleiche-Person-Frage ohne Bilder ist nicht beantwortbar).
                # Je Seite bis zu drei Crops, dazwischen ein Trenner; erst dann die Knoepfe.
                _mitglieder = {u["id"]: (u.get("members") or []) for u in idents}
                def _merge_thumbs(uid_):
                    return "".join(
                        f'<img src="/anlern/crops/{urllib.parse.quote(str(m))}.jpg" alt="">'
                        for m in _mitglieder.get(uid_, [])[:3])
                for a, b in vors:
                    if a in [i["u"]["id"] for i in aktiv] and b in [i["u"]["id"] for i in aktiv]:
                        vors_html += (
                            '<div class="merge"><span class="badge warn">same person?</span>'
                            f'<span class="merge-seite"><b>{html.escape(a.replace("U", "Unknown "))}</b>'
                            f'<span class="merge-thumbs">{_merge_thumbs(a)}</span></span>'
                            '<span class="merge-vs">↔</span>'
                            f'<span class="merge-seite"><b>{html.escape(b.replace("U", "Unknown "))}</b>'
                            f'<span class="merge-thumbs">{_merge_thumbs(b)}</span></span>'
                            f'<button class="gtb on" onclick="unbMergePaar(\'{html.escape(a, quote=True)}\','
                            f'\'{html.escape(b, quote=True)}\',this)">Merge</button>'
                            f'<button class="gtb" onclick="unbVerwerfen(\'{html.escape(a, quote=True)}\','
                            f'\'{html.escape(b, quote=True)}\',this)">Different</button></div>')

                kopf = ('<h2>Unknown</h2>'
                        '<p class="sub">Faces with no known match, grouped into recurring identities. '
                        '<b>Assign person</b> links a tile to a person (new or existing, type the name), '
                        '<b>Ignore</b> mutes a known stranger (no alert). '
                        'New faces are collected automatically after each pass.</p>'
                        '<p><button class="gtb on" onclick="anlernWartungJetzt(this)">Reorganize now</button> '
                        '<span style="color:var(--dim);font-size:13px">re-check the pool and rebuild the '
                        'clusters — collection itself runs automatically (1-2 min)</span></p>'
                        f'<datalist id="pers-list">{opts}</datalist>')
                inhalt = kopf + vors_html
                if wieder:
                    inhalt += ('<h3>Recurring</h3><div class="ukliste">'
                               + "".join(_kachel(i) for i in wieder) + '</div>')
                if einzeln:
                    inhalt += (f'<details class="mehr"><summary>{len(einzeln)} single appearances '
                               '(seen once so far)</summary><div class="ukliste">'
                               + "".join(_kachel(i) for i in einzeln) + '</div></details>')
                if besucher:
                    inhalt += (f'<details class="mehr"><summary>{len(besucher)} known visitors '
                               '(muted)</summary><div class="ukliste">'
                               + "".join(_kachel(i, besuch=True) for i in besucher) + '</div></details>')
                if objekte:
                    inhalt += (f'<details class="mehr"><summary>{len(objekte)} static objects '
                               '(auto-detected — not people)</summary>'
                               '<p class="dim">Groups whose images are near-identical to each '
                               'other and unlike any person — typically a wheel arch, pavement '
                               'or light pattern the detector keeps mistaking for a face. They '
                               'are frozen: new finds are never added here (they form fresh, '
                               'visible clusters and get re-checked by the same rule) — the '
                               'groups stay listed so nothing is hidden.</p><div class="ukliste">'
                               + "".join(_kachel(i, besuch=True) for i in objekte) + '</div></details>')
                if not (wieder or einzeln or besucher):
                    inhalt += webui.leer("No unknown faces collected yet.",
                                         "Identities appear here after the next unknown visitor.")
                return self._send(200, webui.layout("Unknown", "/unbekannte", inhalt, self._banner()))
            if path == "/gesichter":                     # zentrale Personen-/Referenzverwaltung (19.07.)
                import webui
                # M1b (S5): Rendern byte-treu in routes/gesichter.py.
                from routes import gesichter as _r_gesichter
                inhalt = _r_gesichter.render(master_persons(cfg), cfg["data_dir"])
                return self._send(200, webui.layout("Faces", "/gesichter", inhalt, self._banner()))
            if path == "/reconcile_status":            # Fortschritt des Pool-Umbaus (User 25.07.:
                # "ich kann nicht sehen, was er macht")
                p = os.path.join(cfg["data_dir"], "learn", "reconcile_status.json")
                try:
                    d = json.load(open(p))
                except Exception:
                    d = {"phase": "-", "done": 0, "total": 0, "ts": 0}
                return self._send(200, json.dumps(d), "application/json")
            if path == "/aehnliche_status":            # Poll der Wartezustaende (Hochzaehlen, 25.07.)
                import anlernen
                qp = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                p = (qp.get("person", [""])[0] or "").strip()
                try:
                    fertig = (anlernen.aehnliche_unbekannte(p) is not None
                              and anlernen.lade_vorschlaege(p) is not None)
                except Exception:
                    fertig = False
                return self._send(200, json.dumps({"fertig": bool(fertig)}), "application/json")
            if path == "/aehnliche":                     # umgedrehter Weg: passende Unbekannte zu Person
                import webui, anlernen
                # M1a (S4): Rendern byte-treu in routes/aehnliche.py; die SEITENEFFEKTE
                # (Suchlaeufe anstossen, wenn eine Quelle noch rechnet) bleiben HIER.
                from routes import aehnliche as _r_aehnliche
                qd = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                person = urllib.parse.unquote(qd.get("person", [""])[0]).strip()
                if person not in master_persons(cfg):
                    return self._send(200, webui.layout("?", "/gesichter",
                                      webui.leer("Person unknown."), self._banner()))
                kand = anlernen.aehnliche_unbekannte(person)
                if kand is None:
                    svc.qs_neu_starten()           # rechnet Embeddings UND schreibt den refcache
                vs = anlernen.lade_vorschlaege(person)
                if vs is None:
                    svc.vorschlaege_starten(person)
                inhalt, refresh = _r_aehnliche.render(person, kand, vs, cfg["data_dir"])
                return self._send(200, webui.layout("Matching faces", "/gesichter", inhalt,
                                                    self._banner(), refresh=refresh))
            if path.startswith("/anlern/crops/"):        # Anlern-Crops (read-only, Containment)
                # ~ gehoert in die Klasse (Issue #11, fvdpol): Mehr-Gesichter-Crops
                # heissen <eid>~N.jpg und liefen ins 404 — /lernlauf/crop/ konnte
                # die Tilde laengst. realpath-Containment bleibt die Wache.
                m = re.match(rf"^/anlern/crops/({_reg.DATEI_RE}\.jpg)$", path)
                if m:
                    base = os.path.realpath(os.path.join(cfg["data_dir"], "learn", "crops"))
                    p = os.path.realpath(os.path.join(base, m.group(1)))
                    if p.startswith(base + os.sep) and os.path.isfile(p):
                        return self._send(200, open(p, "rb").read(), "image/jpeg")
                return self._send(404, "not found", "text/plain")
            if path in ("/qualitaet", "/pruefen"):      # Qualität: Verwechslung + Eignung (Unter-Tabs)
                import webui, anlernen
                # M1a (S4): Rendern byte-treu in routes/qualitaet.py; der Handler laedt
                # das QS-JSON und normalisiert die ansicht (Deep-Link-Altlast inklusive).
                from routes import qualitaet as _r_qualitaet
                qd = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                ansicht = qd.get("ansicht", ["verwechslung"])[0]
                if ansicht == "unschaerfe":              # alter Deep-Link
                    ansicht = "eignung"
                if ansicht not in ("verwechslung", "eignung"):
                    ansicht = "verwechslung"
                qs = {}
                if os.path.exists(anlernen.QS_PATH):
                    try:
                        qs = json.load(open(anlernen.QS_PATH))
                    except Exception:
                        qs = {}
                inhalt = _r_qualitaet.render(ansicht, qs, cfg["data_dir"])
                return self._send(200, webui.layout("Quality", "/qualitaet", inhalt, self._banner()))
            if path == "/kameras":                # Kamera-Blatt: Discovery + verwenden + Zonen (Phase 2b)
                import webui
                # Modulumbau R1: Rendern byte-treu in routes/kameras.py (Muster
                # qualitaet/auftritte — Daten als Parameter, kein Dienst-Import).
                from routes import kameras as _r_kameras
                cams, err = frigate_cameras(cfg, force=("refresh" in qs))
                inhalt = _r_kameras.render(cams, err, cfg.get("kameras") or {},
                                           cfg.get("required_zones") or {})
                return self._send(200, webui.layout("Cameras", "/kameras",
                                                    inhalt, self._banner()))
            if path == "/areas":                  # Areas-Hauptbereich: Sicht + Konfig
                import webui
                from routes import areas as _r_areas
                cams, err = frigate_cameras(cfg)
                fehlerbanner = (f'<div class="banner">Could not read the Frigate config: '
                                f'{html.escape(str(err))}</div>' if err else "")
                inhalt = _r_areas.uebersicht(_areas_mod.normalisieren(cfg.get("areas")), set(cams))
                return self._send(200, webui.layout("Areas", "/areas",
                                                    fehlerbanner + inhalt, self._banner()))
            if path == "/benachrichtigungen":
                import webui
                # M1a (S4): Seite byte-treu nach routes/benachrichtigungen.py extrahiert
                # (auftritte-Muster: cfg+Labels als Parameter, layout/banner bleiben hier).
                from routes import benachrichtigungen as _r_benach
                inhalt = _r_benach.render(cfg, KAT_LABELS)
                return self._send(200, webui.layout("Notifications", "/benachrichtigungen", inhalt, self._banner()))
            if path == "/live":                    # Live-Reiter (Phase 2)
                import webui
                from routes import live as _r_live
                # _areas_mod ist der MODUL-Import (Z. 25) — ein lokaler
                # Import hier wuerde ihn fuer den GANZEN Handler-Scope
                # verschatten (UnboundLocalError-Klasse, Gate-Fang .186).
                cams, err = frigate_cameras(cfg)
                kacheln, engine_info, gesperrt = svc.live_lage(cams)
                # .186: optionale Area-Gruppierung (?gruppe=area) — die
                # Kamera->Area-Zuordnung kommt aus der EINEN Areas-Quelle.
                nach_area = (qs.get("gruppe") or [""])[0] == "area"
                _am = _areas_mod.normalisieren(cfg.get("areas"))
                cam_area = {kd["name"]: (_areas_mod.kamera_area(_am, kd["name"])
                                         or "") for kd in kacheln}
                inhalt = _r_live.uebersicht(kacheln, engine_info, gesperrt, err,
                                            nach_area=nach_area,
                                            cam_area=cam_area)
                return self._send(200, webui.layout("Live watchers", "/live",
                                                    inhalt, self._banner()))
            if path == "/live_status":             # UI-Poll (Countdown/Quittung)
                return self._send(200, json.dumps(svc.live_status_daten(),
                                                  ensure_ascii=False),
                                  "application/json")
            if path == "/live_alerts":             # Tages-Uebersicht ALLER Live-
                import webui                       #  Trigger (.192, User: 'was er
                #  da wirklich erkannt hat' — auch die unbekannten Gesichter;
                #  die Today-Reihe zeigt seit .191 nur Erkannte, DIESE Seite
                #  ist der Klick dahinter mit allem, inkl. Beweisbild).
                from core import livewache as _lwz
                try:
                    _tag = (qs.get("tag") or [""])[0]
                    _t0 = (time.mktime(time.strptime(_tag, "%Y-%m-%d"))
                           if _tag else None)
                except Exception:
                    _t0 = None
                if _t0 is None:
                    _lt = time.localtime()
                    _t0 = time.mktime((_lt.tm_year, _lt.tm_mon, _lt.tm_mday,
                                       0, 0, 0, 0, 0, -1))
                gruppen, gesamt = _lwz.melde_liste(cfg, _t0, _t0 + 86400,
                                                   max_gruppen=200)
                # .195 (User: "bei Recognized live sehe ich nur ein Bild, das
                # ist nicht konsequent"): je Kamera-AUFTRITT eine Karte mit
                # ALLEN gespeicherten Gesichts-Crops von der Platte (auch
                # Karenz-Trigger ohne Meldezeile) + Rueckblick-Video — analog
                # der Pass-Ansicht unter Recognized.
                auftritte = _lwz.auftritts_gruppen(gruppen)
                karten = []
                for a in auftritte:
                    bilder, videos = _lwz.auftritt_medien(
                        cfg, a["kamera"], a["ts"], a["ts_letzte"])
                    if not bilder and a.get("bild"):
                        bilder = [a["bild"]]   # Platte schon aufgeraeumt
                    thumbs = "".join(
                        f'<a href="/live_alarmbild?p={urllib.parse.quote(b)}"'
                        f' target="_blank" rel="noopener">'
                        f'<img class="lv-thumb" loading="lazy" '
                        f'src="/live_alarmbild?p={urllib.parse.quote(b)}" '
                        f'alt=""></a>' for b in bilder)
                    vlinks = " ".join(
                        f'<a href="/live_alarmbild?p={urllib.parse.quote(v)}"'
                        f' target="_blank" rel="noopener">&#9654; video '
                        f'{i + 1}</a>' for i, v in enumerate(videos))
                    _bis = (f'&ndash;{time.strftime("%H:%M:%S", time.localtime(a["ts_letzte"]))}'
                            if a["ts_letzte"] - a["ts"] >= 1 else "")
                    karten.append(
                        f'<div class="card lv-auftrittkarte" id="a{int(a["ts"])}">'
                        f'<div><b>{html.escape(a.get("person") or "unknown")}</b>'
                        f' <span class="dim">'
                        f'{time.strftime("%H:%M:%S", time.localtime(a["ts"]))}{_bis}'
                        f' · {html.escape(a["kamera"])}'
                        f' · {a["trigger"]} trigger{"" if a["trigger"] == 1 else "s"}'
                        f' · {html.escape("+".join(a["kanaele"]))}</span></div>'
                        + (f'<div class="dim">{html.escape(a["zusatz"][:90])}'
                           f'</div>' if a.get("zusatz") else '')
                        + (f'<div class="lv-medienreihe">{thumbs}</div>'
                           if thumbs else
                           '<div class="dim">no stored pictures</div>')
                        + (f'<div class="dim">{vlinks}</div>' if vlinks else '')
                        + '</div>')
                inhalt = (
                    f'<h2>Live watcher alerts</h2>'
                    f'<p class="sub">{len(auftritte)} appearance'
                    f'{"" if len(auftritte) == 1 else "s"} ({gesamt} trigger'
                    f'{"" if gesamt == 1 else "s"}) on '
                    f'{time.strftime("%Y-%m-%d", time.localtime(_t0))} — '
                    f'quick check, preliminary; the confirmed verdict comes '
                    f'from the normal analysis. Entries from before 0.1.0.190 '
                    f'have no picture or name recorded.</p>'
                    + ("".join(karten) if karten else
                       '<div class="leer"><b>No live alerts that day.</b></div>'))
                return self._send(200, webui.layout(
                    "Live alerts", "/live", inhalt, self._banner()))
            if path == "/live_alarmbild":          # Beweismedium eines Live-Alerts (.190, .195: +mp4)
                # Pfad kommt aus dem Melde-Protokoll bzw. der Auftritts-
                # Ansicht und MUSS dem einen Vertrag ALARMBILD_RE genuegen
                # (data_dir-relativ, kein Traversal) — derselbe Regex wie
                # beim Schreiber.
                from core import livewache as _lw
                rel = (qs.get("p") or [""])[0]
                if not _lw.ALARMBILD_RE.match(rel):
                    return self._send(404, "not found", "text/plain")
                p = os.path.join(cfg.get("data_dir") or "", rel)
                try:
                    roh_med = open(p, "rb").read()
                except OSError:
                    return self._send(404, "not found", "text/plain")
                return self._send(200, roh_med,
                                  "video/mp4" if rel.endswith(".mp4")
                                  else "image/jpeg")
            if path.startswith("/live_bild/"):     # Kachel-Vorschau (User 13.08.)
                # Das JPEG schreibt der DETEKTOR-Thread der Engine aus dem
                # VERARBEITETEN Frame (Waechter-Skala) — der Reiter zeigt, was
                # der Waechter sieht, nicht Frigates Bild. Namens-Muster wie
                # der Schreiber (nie Fremdnamen in einen Pfad); Frische-Frist,
                # damit nach Waechter-Stopp kein eingefrorenes Bild als "live"
                # rausgeht. Cache-Busting macht der Poll per ?t=-Zeitstempel.
                from core import livewache as _lw
                kamera = path[len("/live_bild/"):]
                if not _lw.VORSCHAU_NAME_RE.match(kamera):
                    return self._send(404, "not found", "text/plain")
                p = os.path.join(cfg.get("data_dir") or "", "live", "preview",
                                 f"{kamera}.jpg")
                try:
                    if (time.time() - os.path.getmtime(p)
                            > _lw.VORSCHAU_FRISCH_S):
                        return self._send(404, "preview stale", "text/plain")
                    roh_jpg = open(p, "rb").read()
                except OSError:
                    return self._send(404, "not found", "text/plain")
                return self._send(200, roh_jpg, "image/jpeg")
            if path.startswith("/live/"):          # Detailseite /live/<kamera>
                import webui
                from routes import live as _r_live
                kamera = urllib.parse.unquote(path[len("/live/"):])
                cams, _err = frigate_cameras(cfg)
                kacheln, engine_info, gesperrt = svc.live_lage(cams)
                kd = next((x for x in kacheln if x["name"] == kamera), None)
                if kd is None:
                    # Kachel auch fuer eine (noch) unbekannte Kamera rendern
                    # duerfen wir NICHT — der Name kaeme aus der URL, nicht
                    # aus Frigate/Store (keine zweite Kamera-Quelle).
                    return self._send(404, webui.layout(
                        "Live watchers", "/live",
                        webui.leer("Unknown camera.",
                                   "Tiles come from Frigate's camera list "
                                   "and saved watchers only."),
                        self._banner()))
                inhalt = _r_live.detail(kamera, kd.get("guard"), kd, gesperrt)
                return self._send(200, webui.layout(
                    f"Live — {kamera}", "/live", inhalt, self._banner()))
            if path == "/vision":                  # Vision detect (Reiter)
                import webui
                from core import vision as _vis
                from routes import vision as _r_vision
                _blk, _prot, _vor = svc.vision_lage()
                # ?kachel= zeigt eine andere Anbieter-Kachel VOR dem Speichern
                # (sonst muesste man eine externe Verbindung speichern, um
                # ueberhaupt die Cloud-Bestaetigung zu Gesicht zu bekommen —
                # das waere ein Ring). Nur Anzeige, nichts wird geschrieben.
                _w = urllib.parse.parse_qs(
                    urllib.parse.urlsplit(self.path).query).get("kachel")
                if _w and _w[0] in _vis.KACHELN:
                    _blk["kachel"] = _w[0]
                    _blk["betriebsart"] = _vis.KACHELN[_w[0]]["betriebsart"]
                _blk["max_tokens"] = cfg.get("vision_max_tokens")
                _blk["timeout_s"] = cfg.get("vision_timeout_s")
                # .165/.166: die Haken-Felder der Seite lesen aus DIESEM
                # Block. Die bestehenden lagen nie darin — sie standen deshalb
                # IMMER unangehakt da, egal was gespeichert war, und ein Save
                # von dieser Seite haette sie still ausgeschaltet. Die Menge
                # kommt aus dem Renderer selbst (EINE Quelle), damit ein
                # vierter Haken nicht denselben Fehler mitbringt.
                for _s in _r_vision.CFGV_HAKEN:
                    _blk[_s] = bool(cfg.get(_s))
                _blk["api_key_gesetzt"] = bool(_blk.get("api_key"))
                _blk.pop("api_key", None)          # Key verlaesst den Renderer nie
                _lage = svc.vision_galerie_lage()
                inhalt = _r_vision.seite(
                    _blk, _vis.KACHELN, _vis.KACHEL_REIHE, _vor, _prot,
                    svc._vision_modelle(_blk),
                    _vis.MASCHINEN_ANKER,
                    _vis.prompt_default(bool(_blk.get("cloud_ok"))),
                    _reg.endpunkt_anzeige(_vis.endpunkt_wirksam(_blk)),
                    _lage["deckung"], _lage["galerien"],
                    _reg.VISION_MESSWERTE_STAND, _lage["reihen_text"],
                    _vis.pruef_wort(_vis.kachel(_blk.get("kachel"))),
                    # .165: der Orientierungssatz zur Modellklasse — ERZEUGT
                    # aus der Messwerte-Registry, nie im Renderer formuliert.
                    _reg.vision_klassen_hinweis(_blk.get("kachel")))
                return self._send(200, webui.layout("Vision detect", "/vision",
                                                    inhalt, self._banner()))
            if path == "/erkennungstest":          # Szenario-Test, DREI Wege (V4, §4)
                import webui
                from routes import visiontest as _r_vt
                _q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                _l = svc.vision_test_lage((_q.get("pass") or [""])[0])
                return self._send(200, webui.layout(
                    "Recognition test", "/erkennungstest",
                    _r_vt.seite(_l["passe"], _l["pass_key"], _l["sicht"],
                                _l["laeuft"], nachanalyse=_l["nachanalyse"],
                                lauffeld=_l["lauffeld"], laeufe=_l["laeufe"]),
                    self._banner(),
                    refresh=30 if (_l["laeuft"]
                                   or _l["nachanalyse"].get("laeuft"))
                    else None))
            if path == "/vision/galerie":          # Galerie-Wizard (V2, §6)
                import webui
                from routes import visionwizard as _r_vw
                _q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                _p = (_q.get("person") or [""])[0]
                try:
                    _g = int((_q.get("groesse") or ["0"])[0])
                except ValueError:
                    _g = 0
                _l = svc.vision_galerie_lage(_p, _g or None,
                                             bool((_q.get("neu") or [""])[0]))
                return self._send(200, webui.layout(
                    "Build a gallery", "/vision", _r_vw.seite(**_l),
                    self._banner()))
            if path.startswith("/vision/galerie/bild/"):
                # Galerie-KOPIE ausliefern, Containment wie /personlauf/bild
                _rel = urllib.parse.unquote(path[len("/vision/galerie/bild/"):])
                _pers, _, _datei = _rel.partition("/")
                _wurz = os.path.normpath(os.path.join(cfg["data_dir"],
                                                      "personlern", "galerien"))
                _voll = os.path.normpath(os.path.join(_wurz, _pers, _datei))
                if _voll.startswith(_wurz + os.sep) and os.path.isfile(_voll):
                    return self._send(200, open(_voll, "rb").read(),
                                      "image/jpeg")
                return self._send(404, b"gone")
            if path == "/kette":                   # Recognition chain (.189,
                import webui                       #  eigener Settings-Punkt)
                # _kette ist der MODUL-Import (Z. 27), nie lokal importieren
                # (Schatten-Import-Klasse, Gate-Fang .186).
                from routes import konfiguration as _r_konf
                inhalt = _r_konf.kette_seite(cfg, _kette.DEFAULT_KETTE,
                                             _kette.lage(cfg),
                                             svc.CONFIG_WHITELIST,
                                             svc._kette_auto_hinweise())
                return self._send(200, webui.layout(
                    "Recognition chain", "/kette", inhalt, self._banner()))
            if path == "/konfiguration":
                import webui
                # Modulumbau R1: Rendern byte-treu in routes/konfiguration.py.
                # Die Ketten-Schalter leben seit .189 auf /kette.
                from routes import konfiguration as _r_konf
                inhalt = _r_konf.render(cfg, svc.CONFIG_WHITELIST,
                                        svc._kette_auto_hinweise())
                return self._send(200, webui.layout("Settings", "/konfiguration", inhalt, self._banner()))
            if path == "/config_sichern":              # Config-Store als Download (UI 'Download configuration')
                # Store + wirksame Verbindungs-Werte (Vertrag core.registry.EXPORT_VERBINDUNG):
                # ENV-/yaml-konfigurierte Installationen haben frigate_url/mqtt NICHT im Store,
                # das Backup waere dort unvollstaendig (User-Fund 02.08., NB-Restore ohne Frigate).
                d = _reg.export_ergaenzen(_lade_config_store(cfg), cfg)   # Modul-Import oben (kein lokaler Schatten!)
                data = (json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode()
                fn = f"suslik-config-{datetime.datetime.now():%Y%m%d}.json"
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{fn}"')
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/backup_voll":         # PE6: Full-Backup als EIN Archiv (Umzugs-faehig)
                # Inhalt: Config-Export (inkl. wirksamer Verbindungs-Werte) + alles
                # Gelernte/Handarbeit: config/, faces/, learn/, personlern/ (ohne
                # werkstatt-Scratch), state/. BEWUSST NICHT drin: clips/ (Cache) und
                # events/ (abgeleitete Analyse-Historie) — der Karten-Text sagt das.
                import io as _io
                import shutil as _sh
                import tarfile
                import tempfile
                d = _reg.export_ergaenzen(_lade_config_store(cfg), cfg)
                fn = f"suslik-full-backup-{datetime.datetime.now():%Y%m%d_%H%M}.tar.gz"
                tmpf = tempfile.NamedTemporaryFile(prefix=".backup-voll-", suffix=".tar.gz",
                                                   dir=cfg["data_dir"], delete=False)
                try:
                    with tarfile.open(fileobj=tmpf, mode="w:gz") as tar:
                        blob = (json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode()
                        ti = tarfile.TarInfo("config-export.json")
                        ti.size, ti.mtime = len(blob), int(time.time())
                        tar.addfile(ti, _io.BytesIO(blob))
                        for teil in ("config", "faces", "learn", "personlern", "state"):
                            p = os.path.join(cfg["data_dir"], teil)
                            if os.path.isdir(p):
                                tar.add(p, arcname=teil, filter=lambda t:
                                        None if "/werkstatt" in t.name else t)
                    groesse = tmpf.tell()
                    tmpf.seek(0)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/gzip")
                    self.send_header("Content-Disposition", f'attachment; filename="{fn}"')
                    self.send_header("Content-Length", str(groesse))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    _sh.copyfileobj(tmpf, self.wfile, 512 * 1024)
                finally:
                    tmpf.close()
                    try:
                        os.unlink(tmpf.name)
                    except OSError:
                        pass
                return
            if path == "/system":
                import webui
                # Modulumbau R1: Rendern byte-treu in routes/system.py (Service-Objekt
                # injiziert — die Seite zeigt die Dienst-LAGE, s. Modul-Docstring;
                # ro/docs_url bleiben Kern-Quellen).
                from routes import system as _r_system
                inhalt = _r_system.render(svc, cfg, frigate_read_only(cfg), DOCS_URL)
                return self._send(200, webui.layout("System", "/system", inhalt, self._banner()))
            if path == "/health":
                # version zuerst (Task #12, User 28.07.): eingesandte Log-AUSSCHNITTE tragen
                # die Startup-Banner-Zeile oft nicht, und "latest-gpu" im Issue-Formular ist
                # mehrdeutig — /health ist die eine Zeile, die Support-Faelle eindeutig macht.
                _sf = getattr(svc, "startup_fails", 0)   # SD1: B8-Fang — Selbstcheck-FAIL
                h = {"ok": _sf == 0,                     # und health-ok nie wieder gleichzeitig
                     "startup_fails": _sf,
                     "version": os.environ.get("SUSLIK_VERSION", "dev"),
                     "processed": len(svc.processed),
                     "backend": cfg.get("backend") or "",
                     # N8b: Cache-Groesse SICHTBAR (Feldbericht: 74-GB-Steady-State erst am
                     # 97 % vollen Host bemerkt) + der wirksame Deckel daneben.
                     "clip_cache_gb": round(svc.clip_cache_bytes() / 1024**3, 2),
                     "clip_cache_max_gb": cfg["clip_cache_max_gb"],
                     # Ketten-Schalter (Issue #21, K1): konfigurierte Stufe UND
                     # tatsaechliche Scharf-Lage je Erkennungs-Weg — aus DENSELBEN
                     # Praedikaten wie die Quell-Hooks (kette_lage), die Anzeige
                     # kann dem Verhalten nicht widersprechen.
                     "erkennungskette": svc.kette_lage(),
                     # Wanduhr-Lage (K1, Issue #21): sagt WARUM (k)eine Selbst-
                     # messung vorliegt (uebersprungen auf kleinen Maschinen /
                     # letzter Fehlversuch), statt still zu fehlen.
                     "wanduhr": svc.wanduhr_status(),
                     # Live-Reiter (Phase 2): Engine-Herzschlag + Waechter-
                     # Zustaende aus DERSELBEN Ableitung wie die Kacheln
                     # (livewache.ui_zustand + registry.LIVE_ZUSTAENDE — die
                     # Anzeige kann den Kacheln nicht widersprechen, K3/K1).
                     "live": svc.live_health()}
                pi = cfg.get("placement_info")
                if pi:                                     # P4: aufgeloestes Auto-Placement ausweisen
                    h["placement"] = {"backend": pi.get("backend"), "quelle": pi.get("quelle"),
                                      "ts": pi.get("ts")}
                # Z8 Mitnahme A: Verteiler-Rueckfall sichtbar (konzept_frames.md §3.2 —
                # "geloggt und in /health sichtbar"). Rueckfall = die Abnehmer eines Events
                # wollten verschiedene steps, also lief der Decode GETRENNT statt einmal;
                # ein Download bleibt, das Urteil auch. NUR ANZEIGE, nichts wird gesteuert.
                # Zwei Toepfe, weil der Zaehler prozessweit ist: 'dienst' ist der des
                # Dienstprozesses (heute faehrt hier kein Lauf, also normal 0), 'worker' die
                # aufsummierten Meldungen des Analyse-Workers, wo die Laeufe wirklich wohnen.
                _wk = getattr(svc._worker_obj, "rueckfaelle", None) or {}
                from core import frames as _frames_health
                _dn = int(_frames_health.RUECKFAELLE.get("n") or 0)
                h["frame_rueckfaelle"] = {"n": _dn + int(_wk.get("summe") or 0),
                                          "dienst": _dn,
                                          "worker": int(_wk.get("summe") or 0)}
                _zl = _frames_health.RUECKFAELLE.get("zuletzt")
                if _zl and _zl.get("steps"):               # nur die steps, nie der Clip-Name
                    h["frame_rueckfaelle"]["zuletzt_steps"] = _zl["steps"]
                return self._send(200, json.dumps(h), "application/json")
            if path == "/sync_diagnose":                   # .132: Diagnose-Paket BEIDE Seiten (carlsmith-Lehre)
                # Ein Klick fuer Tester und uns: suslik-Bericht + Sync-Status +
                # Sync-Logzeilen des Dienstes + Frigate-Log-Tail per API
                # (GET /api/logs/frigate, an der laufenden 0.18-OpenAPI verifiziert).
                teile = [f"suslik {os.environ.get('SUSLIK_VERSION', 'dev')} — sync diagnosis "
                         f"({datetime.datetime.now():%Y-%m-%d %H:%M:%S})",
                         "NOTE: this bundle contains your person names, camera names and "
                         "local addresses — review before posting it publicly."]
                furl = (cfg.get("frigate_url") or "").strip()
                furl_anzeige = re.sub(r"//[^/@]*@", "//***@", furl)   # etwaige Zugangsdaten maskieren
                teile.append(f"frigate: {furl_anzeige or '(not configured)'}")

                def _alter(pfad):
                    try:
                        s = int(time.time() - os.path.getmtime(pfad))
                        return f"written {s // 3600}h {s % 3600 // 60}m {s % 60}s ago"
                    except OSError:
                        return "age unknown"
                # Review-SOLL: jedes Teil traegt sein ALTER (ein Alt-Bericht darf sich
                # nie wie das Ergebnis des aktuellen Laufs lesen) + die err-Logs mit
                # dem VOLLEN Traceback des jeweils letzten Laufs.
                for name, pfad, ganz in (
                        ("last export report (sync_export_bericht.json)",
                         os.path.join(cfg["data_dir"], "state", "sync_export_bericht.json"), True),
                        ("current sync status (sync_progress.json)",
                         os.path.join(cfg["data_dir"], "state", "sync_progress.json"), True),
                        ("last export stderr (sync_export_err.log)",
                         os.path.join(cfg["data_dir"], "state", "sync_export_err.log"), False),
                        ("last import stderr (sync_import_err.log)",
                         os.path.join(cfg["data_dir"], "state", "sync_import_err.log"), False)):
                    teile.append(f"\n== {name} — {_alter(pfad)} ==")
                    try:
                        with open(pfad, encoding="utf-8", errors="replace") as f:
                            inhalt = f.read().strip()
                        if not ganz:
                            inhalt = "\n".join(inhalt.splitlines()[-40:])
                        teile.append(inhalt or "(empty)")
                    except Exception as e:
                        teile.append(f"(not available: {e})")
                teile.append("\n== suslik service log (sync lines, latest last) ==")
                zeilen = [z for z in list(svc.logbuf) if "sync" in z.lower()]
                teile.append("\n".join(zeilen[-30:]) or "(none)")
                teile.append("\n== frigate log tail (via GET /api/logs/frigate) ==")
                if not furl:
                    teile.append("(no Frigate URL configured)")
                else:
                    try:
                        fbasis = furl.rstrip("/")
                        with urllib.request.urlopen(f"{fbasis}/api/logs/frigate?start=0&end=1",
                                                    timeout=6) as r:
                            gesamt = int(json.load(r).get("totalLines") or 0)
                        lstart = max(0, gesamt - 80)
                        with urllib.request.urlopen(f"{fbasis}/api/logs/frigate?start={lstart}",
                                                    timeout=6) as r:
                            d = json.load(r)
                        teile.append(f"(lines {lstart}..{gesamt} of {gesamt})")
                        teile.append("\n".join(d.get("lines") or []) or "(empty)")
                    except Exception as e:
                        teile.append(f"(frigate log not reachable: {type(e).__name__}: {e})")
                return self._send(200, "\n".join(teile), "text/plain; charset=utf-8")
            if path == "/sync_auswahl":                    # .133 "Review & sync": selektiver Export
                import webui
                import sync_refs as _sr
                from routes import syncauswahl as _r_sa
                # .137: die Seite rechnet den VIER-KLASSEN-Abgleich (abgleich()),
                # nicht mehr nur die Kandidaten von diff() — sonst bleiben in
                # Frigate geloeschte und frueher exportierte Bilder unsichtbar
                # (Operator-Befund 06.08.). kandidaten = uebertragbare + bewusst
                # abgewaehlte, genau die Menge, die die Seite selbst aufteilt.
                bilanz, kand, pruefbar, fehler = None, [], [], ""
                try:
                    bilanz = _sr.abgleich()
                    kand = bilanz["kandidaten"] + bilanz["abgewaehlt"]
                    # .138 Panel-Fix: 'offen' nur ueber Bilder rechnen, die
                    # cmd_vorpruefung JE erreicht (diff() ueberspringt D1-/D2-
                    # Herkuenfte). Ein per 'respect the deletion' abgewaehltes
                    # D1-Bild blieb sonst ewig offen -> der Vorpruefungs-
                    # Subprozess startete bei JEDEM Seitenaufruf neu (K3:
                    # Erzeuger-/Verbrauchermenge liefen auseinander).
                    _unpr = set(bilanz["abgewaehlt_unpruefbar"])
                    pruefbar = [x for x in kand if x not in _unpr]
                except Exception as e:
                    fehler = f"{type(e).__name__}: {e}"
                cache = _sr.vorpruefung_lesen()
                # Nur Urteile zeigen, deren Bild sich seit der Messung NICHT geaendert
                # hat — ein ausgetauschtes Referenzbild darf nie das alte Urteil erben.
                offen = _sr.vorpruefung_offen(pruefbar, cache)
                _offen_k = {_sr.schluessel(p, d) for p, d in offen}
                urteile = {}
                for _p, _d in kand:
                    _s = _sr.schluessel(_p, _d)
                    if _s not in _offen_k and _s in cache:
                        urteile[_s] = cache[_s]
                pstat = _sr.vorpruefung_status()
                # Hintergrund-Lauf anstossen (Muster job(): Thread + Subprozess, der
                # Detektor bleibt AUSSERHALB des Dienst-Prozesses). Ein Lauf zur Zeit.
                _lebt = bool(getattr(svc, "_vorpruef_thread", None)
                             and svc._vorpruef_thread.is_alive())
                # .134 Review-SOLL: 'detektor: aus' ist ein ABSCHLUSS-Vermerk —
                # nie neu starten (vorher: Endlos-Karussell aus Reload + neuem
                # Subprozess, wenn der Detektor nicht ladbar war).
                if offen and not _lebt and pstat.get("detektor") != "aus" \
                        and not pstat.get("fehler"):
                    def _vp_job():
                        env = dict(os.environ, OV_DEVICE=svc.cfg["ov_device"])
                        _fu = (svc.cfg.get("frigate_url") or "").strip()
                        if _fu:
                            env["FRIGATE_URL"] = _fu
                        errp = os.path.join(svc.cfg["data_dir"], "state",
                                            "sync_vorpruefung_err.log")
                        r = subprocess.run(
                            [sys.executable, os.path.join(HERE, "sync_refs.py"),
                             "vorpruefung"], capture_output=True, timeout=3600,
                            check=False, env=env)
                        if r.returncode != 0:              # Fehler NIE still verschlucken
                            try:
                                with open(errp, "wb") as _ef:
                                    _ef.write(r.stderr or b"")
                            except OSError:
                                pass
                            svc.log("!! sync pre-check FAILED "
                                    f"(rc={r.returncode}): {fehler_kern(r.stderr)}")
                            # .134 Hinweis-Fix: Status darf nie auf laeuft=True
                            # stehenbleiben (Seite hinge sonst ewig auf 'checking');
                            # ein fehler-Feld stoppt auch den Neustart-Versuch.
                            try:
                                import sync_refs as _sr3
                                _st = _sr3.vorpruefung_status()
                                if _st.get("laeuft"):
                                    _sr3._vp_status(
                                        laeuft=False, gesamt=_st.get("gesamt", 0),
                                        fertig=_st.get("fertig", 0),
                                        fehler=fehler_kern(r.stderr)
                                        or f"pre-check failed (rc={r.returncode})")
                            except Exception:
                                pass
                    svc._vorpruef_thread = threading.Thread(target=_vp_job, daemon=True)
                    svc._vorpruef_thread.start()
                    pstat = {"laeuft": True, "gesamt": len(offen), "fertig": 0}
                try:
                    with open(os.path.join(cfg["data_dir"], "state",
                                           "sync_export_bericht.json"), encoding="utf-8") as f:
                        bericht = json.load(f)
                except Exception:
                    bericht = None
                # .137 Live-Flag: Frigates eigene Erkennung JETZT lesen (5 s
                # Deckel) — nie den gespeicherten Alt-Status als Live-Zustand
                # ausgeben. Bei unerreichbarem Frigate steht ohnehin schon die
                # Fehlerkarte, dann sparen wir uns den zweiten Anlauf.
                fr = None if fehler else _sr.frigate_fr_status()
                inhalt = _r_sa.render(kand, urteile, _sr.abwahl_lesen(), pstat,
                                      bericht=bericht, fehler=fehler,
                                      schreibsperre=frigate_read_only(cfg),
                                      bilanz=bilanz,
                                      ablehnungen=(bilanz or {}).get("abgelehnt") or {},
                                      fr=fr)
                return self._send(200, webui.layout("Frigate sync", "/sync_auswahl",
                                                    inhalt, self._banner()))
            if path == "/sync_vorpruefung_status":         # .133: Fortschritt der Vorpruefung
                import sync_refs as _sr
                return self._send(200, json.dumps(_sr.vorpruefung_status()),
                                  "application/json")
            if path == "/sync_status":                     # Fortschritt des Referenz-Syncs fuer die UI (X von Y)
                try:
                    with open(os.path.join(cfg["data_dir"], "state", "sync_progress.json")) as f:
                        return self._send(200, f.read(), "application/json")
                except Exception:
                    return self._send(200, json.dumps({"phase": "idle"}), "application/json")
            if path == "/log":
                return self._send(200, "\n".join(svc.logbuf) or "(no log lines yet since service start)",
                                  "text/plain; charset=utf-8")
            m = re.match(r"^/video/([\w.\-]+)$", path)
            if m:            # W3 Lazy: Browser-Kopie auf Klick bauen, Spinner bis sie liegt (E8)
                import webui
                ed = m.group(1)
                base = os.path.realpath(os.path.join(cfg["data_dir"], "clips"))
                rev = os.path.realpath(os.path.join(base, ed + "_review.mp4"))
                src = os.path.realpath(os.path.join(base, ed + ".mp4"))
                if not (rev.startswith(base + os.sep) and src.startswith(base + os.sep)):
                    return self._send(404, "not found", "text/plain; charset=utf-8")
                if os.path.isfile(rev):
                    return self._send(302, "", "text/plain",
                                      location=f"/clip/{urllib.parse.quote(ed)}_review")
                if not os.path.isfile(src):
                    return self._send(404, "Clip no longer in cache — retention "
                                      f"{cfg['clip_retention_d']} days", "text/plain; charset=utf-8")
                with svc._review_lock:
                    laeuft = ed in svc._review_laeuft
                    fehler = None if laeuft else svc._review_fehler.pop(ed, None)
                if fehler is not None:
                    # Bau ist gescheitert (Details im Dienst-Log). KEIN Auto-Refresh — sonst
                    # Endlos-Neubau-Schleife; ein manueller Reload versucht es bewusst erneut.
                    inhalt = ('<div class="card" style="text-align:center;padding:40px">'
                              '<p>&#9888; Transcode failed — see the service log (/log).</p>'
                              '<p style="color:var(--dim)">Reload this page to retry, or open the '
                              f'original clip: <a href="/clip/{urllib.parse.quote(ed)}">'
                              '4K/HEVC</a></p></div>')
                    return self._send(200, webui.layout("Video", "", inhalt, self._banner()))
                svc.review_anfordern(ed)
                inhalt = ('<div class="card" style="text-align:center;padding:40px">'
                          '<div class="spin"></div>'
                          '<p>Preparing browser video (H.264)&nbsp;…</p>'
                          '<p style="color:var(--dim)">This page refreshes automatically. '
                          'The copy is built once and then cached.</p></div>')
                return self._send(200, webui.layout("Video", "", inhalt, self._banner(), refresh=2))
            m = re.match(r"^/clip/([\w.\-]+)$", path)
            if m:                                          # der analysierte Record-Clip aus dem Cache
                base = os.path.realpath(os.path.join(cfg["data_dir"], "clips"))
                p = os.path.realpath(os.path.join(base, m.group(1) + ".mp4"))
                if p.startswith(base + os.sep) and os.path.isfile(p):
                    return self._send_file_ranged(p, "video/mp4", dl_name=m.group(1) + ".mp4")
                return self._send(404, "Clip no longer in cache — retention "
                                  f"{cfg['clip_retention_d']} days", "text/plain; charset=utf-8")
            if path in ("/review", "/fremde"):
                # Alt-Galerien aus prototypes/backtest.py — das Werkzeug liegt in keinem Image, die
                # Seiten entstehen dort also nie. Die Links dorthin sind am 25.07. aus Fusszeile und
                # System-Seite entfernt; die Routen bleiben nur fuer alte Lesezeichen und liefern die
                # vorhandene Datei aus, wenn es sie gibt. Statt der frueheren nackten 404-Textzeile
                # jetzt eine Weiterleitung auf die Seite, die dieselbe Frage heute beantwortet.
                p = os.path.join(cfg["data_dir"], path.strip("/") + ".html")
                if os.path.isfile(p):
                    return self._send(200, open(p, "rb").read())
                return self._send(302, "", "text/plain",
                                  location="/offen" if path == "/review" else "/unbekannte")
            if path == "/doc" or path.startswith("/doc/"):  # Projekt-Doku -> GitHub. Frueher lieferte /doc/*
                # lokale Arbeitsnotizen mit internen IPs + Zugaengen aus; der
                # Redirect schliesst den Leak auch fuer alte /doc/-Bookmarks.
                return self._send(302, "", "text/plain", location=DOCS_URL)
            if path.startswith("/event/"):        # Einzel-Event-Detail (Klick aus Today, User 22.07.)
                import webui
                eid = urllib.parse.unquote(path[len("/event/"):])
                row, rows_all = None, []
                if os.path.exists(svc.log_path):
                    with open(svc.log_path) as f:
                        for l in f:
                            try:
                                r = json.loads(l)
                            except Exception:
                                continue
                            rows_all.append(r)
                            if r.get("eid") == eid:
                                row = r                    # letzter Eintrag pro eid gewinnt
                if not row:
                    return self._send(404, webui.layout("Event", "/heute",
                                      webui.leer("Event not found.", "It may have aged out of the log."),
                                      self._banner()))
                ed = eid.replace("/", "_")
                edir = os.path.join(cfg["data_dir"], "events", ed)
                t = datetime.datetime.fromtimestamp(row.get("start") or row.get("ts", 0)).strftime("%d.%m.%Y %H:%M:%S")
                cam = html.escape(str(row.get("camera", "?")))
                kat = str(row.get("kategorie", "?"))
                fr = row.get("frigate") or {}
                ftxt = (f"{fr.get('label')} {fr['score']:.2f}" if fr.get("label") and fr.get("score") is not None
                        else "—")
                ours = ", ".join(f"{p} {(v.get('max') or 0):+.2f}/{v.get('win3s', 0)}×" for p, v in
                                 sorted((row.get("ours") or {}).items(), key=lambda x: -(x[1].get("max") or 0))) or "—"
                best = row.get("bestaetigt") or []
                if os.path.isdir(edir):
                    # PRO PERSON gruppiert (User 25.07., Screenshot-Befund: "die Bilder eines
                    # Events sind voellig unordentlich und durcheinander — es haette pro Gesicht
                    # geordnet angezeigt werden muessen"). Vorher war das Raster EINE flache
                    # Liste ueber alle Personen des Events; bei dreien ein Durcheinander. Die
                    # Zuordnung steckt im Dateinamen (…_best_<Person>_NN… / …_show_<Person>_NN…),
                    # es braucht keine neue Analyse. Abschnitte nach bestem NN sortiert,
                    # innerhalb wie gehabt NN und dann Groesse; Bilder ohne Zuordnung
                    # (z.B. Enrollment-Crops) zuletzt.
                    def _gal_rang(c):
                        nn = bild_nn(c)
                        return (nn if nn is not None else -9.0,
                                os.path.getsize(os.path.join(edir, c)))
                    def _gal_person(c):
                        m2 = re.search(r"_(?:best|show)_(.+?)_NN", c)
                        return m2.group(1) if m2 else None
                    jpgs = sorted((c for c in os.listdir(edir) if c.endswith(".jpg")),
                                  key=_gal_rang, reverse=True)
                    gruppen = {}
                    for c in jpgs:
                        gruppen.setdefault(_gal_person(c), []).append(c)
                    def _grp_rang(pn):
                        return max((bild_nn(c) or -9.0) for c in gruppen[pn])
                    # SICHTBARE GRENZE sicher/unsicher (User-Befund an einer Tuerkamera:
                    # "hier sollte eine deutliche sichtbare Grenze sein — das habe ich klar
                    # erkannt, und diese koennten ggf. als falsche Person erkannt werden").
                    # Grenze = anlernen.UNBEKANNT_MAX: unterhalb davon haelt suslik ein Gesicht
                    # selbst fuer "unbekannt" — eine Namenszuordnung darunter ist also nur eine
                    # Vermutung (+0.41, Hinterkopf), keine Erkennung (+0.70). Beurteilt
                    # wird die GRUPPE an ihrem besten Bild: traegt eine Person EIN starkes Bild,
                    # sind ihre schwaecheren Zusatz-Crops mitbelegt und gehoeren nicht unter den
                    # Strich. Import HIER noetig: do_GET importiert anlernen an anderer Stelle
                    # lokal, damit ist der Name in der GANZEN Funktion lokal — ohne diesen
                    # Import flog auf jeder Event-Seite ein UnboundLocalError (Prod 25.07. 21:30).
                    import anlernen
                    _grenze_nn = anlernen.UNBEKANNT_MAX
                    teile_gal, _unter_grenze = [], False
                    _namen = sorted((k for k in gruppen if k is not None), key=_grp_rang,
                                    reverse=True)
                    _klar = [p for p in _namen if _grp_rang(p) >= _grenze_nn]
                    _vage = [p for p in _namen if _grp_rang(p) < _grenze_nn]
                    for pn in _klar + _vage + ([None] if None in gruppen else []):
                        if not _unter_grenze and (pn in _vage or pn is None):
                            teile_gal.append(
                                '<div class="evgrenze">below this line: weak matches '
                                f'(best score &lt; {_grenze_nn:.2f}) — the name is a guess, '
                                'this could be a different person</div>')
                            _unter_grenze = True
                        zellen = "".join(
                            f'<a href="/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(c)}" '
                            f'class="evimg"><img src="/events/{urllib.parse.quote(ed)}/'
                            f'{urllib.parse.quote(c)}" alt="{html.escape(c)}"></a>'
                            for c in gruppen[pn])
                        titel = html.escape(pn) if pn else "Unattributed"
                        _b = ' <span class="badge warn">unsure</span>' if pn in _vage else ""
                        teile_gal.append(
                            f'<h4 class="evgrp">{titel} <span class="cnt">{len(gruppen[pn])}'
                            f'</span>{_b}</h4><div class="evgal">{zellen}</div>')
                    galerie = "".join(teile_gal) if teile_gal                         else webui.leer("No face crops stored for this event.")
                else:
                    galerie = webui.leer("No face crops stored for this event.")
                vid = ""
                # W3: /video baut die Browser-Kopie lazy beim Klick (Spinner) bzw. leitet auf die
                # fertige Kopie weiter. Link zeigen, solange EINE der beiden Dateien lebt — die
                # Kopie ueberlebt ihren Quell-Clip um bis zu clip_retention_d (Review-Fund).
                if any(os.path.isfile(os.path.join(cfg["data_dir"], "clips", ed + s))
                       for s in ("_review.mp4", ".mp4")):
                    vid = f'<a class="btn" href="/video/{urllib.parse.quote(ed)}">&#9654; Video</a>'
                logl = (f'<a class="btn" href="/events/{urllib.parse.quote(ed)}/analyze.log">Analysis log</a>'
                        if os.path.isfile(os.path.join(edir, "analyze.log")) else "")
                gtmap = {}
                gtp = os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl")
                if os.path.exists(gtp):
                    with open(gtp) as f:
                        for l in f:
                            try:
                                d = json.loads(l); gtmap[d["eid"]] = d["label"]
                            except Exception:
                                pass
                gt_schnell = gt_schnellpersonen(rows_all, cfg)
                andere = [p for p in master_persons(cfg) if p not in gt_schnell]
                gtb = gt_leiste(eid, gt_schnell, andere, gtmap.get(eid, ""))
                kbadge = (f'<span class=k style=background:{KAT_FARBE.get(kat, "#666")}>'
                          f'{html.escape(KAT_LABELS.get(kat, kat))}</span>')
                if row.get("frames_fehlen"):   # W1: unvollstaendig gelesener Clip sichtbar machen
                    kbadge += (' <span class=k style="background:#8a6d1a" title="clip incomplete — '
                               f'read {row.get("frames_gelesen")}/{row.get("frames_soll")} frames; '
                               'judged from the readable part">⚠ incomplete clip</span>')
                conf = (' · <b style="color:var(--ok)">✓ ' + html.escape(", ".join(best)) + '</b>') if best else ''
                # Haeppchen 2: Szenario-Leiste — das Event im Kontext seines Durchgangs
                # (Szenario-Prinzip als Navigation: view pass + prev/next INNERHALB des
                # Durchgangs). Faellt still weg, wenn das Event keinem Durchgang angehoert.
                passleiste = ""
                try:
                    import szenarien as _szn
                    _t0 = row.get("start") or row.get("ts") or 0
                    _tagd = datetime.datetime.fromtimestamp(_t0).replace(
                        hour=0, minute=0, second=0, microsecond=0)
                    _byh = {}
                    for _r in rows_all:
                        if _r.get("eid"):
                            _byh[_r["eid"]] = _r
                    # Kalendertag statt 86400 s (Review .55 — DST-Klasse wie .54/ereignisse)
                    _sz = _szn.szenarien_des_tages(_byh, _tagd.timestamp(),
                                                   (_tagd + datetime.timedelta(days=1)).timestamp(),
                                                   cfg, gtmap)
                    _s = next((x for x in _sz
                               if any(e.get("eid") == eid for e in x.get("evs") or [])), None)
                    if _s:
                        # Auch bei n==1 (Issue #9-Nachbefund .173): die Leiste ist der
                        # einzige Weg zur Pass-Seite und damit zum Analyse-Grund — ein
                        # EINZELNES Fehler-Event (genau Tokn59s Screenshot-Fall) hatte
                        # vorher keinen. prev/next entfallen bei n==1 von selbst.
                        _evs = [e for e in _s.get("evs") or [] if e.get("eid")]
                        _i = next((k for k, e in enumerate(_evs) if e["eid"] == eid), None)
                        _pl = (f'<a class="gtb" href="/event/{urllib.parse.quote(str(_evs[_i-1]["eid"]))}">&#8592; prev</a>'
                               if _i and _i > 0 else '')
                        _nl = (f'<a class="gtb" href="/event/{urllib.parse.quote(str(_evs[_i+1]["eid"]))}">next &#8594;</a>'
                               if _i is not None and _i + 1 < len(_evs) else '')
                        passleiste = (
                            f'<div class="card passleiste">Part of a pass '
                            f'<span class="num">{datetime.datetime.fromtimestamp(_s["start"]).strftime("%H:%M")}'
                            f'&ndash;{datetime.datetime.fromtimestamp(_s["ende"]).strftime("%H:%M")}</span>'
                            f' · {_s["n"]} {"event" if _s["n"] == 1 else "events"} · '
                            f'<a class="gtb" href="/pass/{urllib.parse.quote(eid)}">view pass</a> {_pl}{_nl}</div>')
                except Exception:
                    passleiste = ""               # Leiste ist Komfort, nie ein Seitenkiller
                # Issue #9 (Tokn59, 31.07., Zusage endlich eingeloest .173): der GRUND
                # eines Fehler-Events steht DIREKT auf der Event-Seite. Quelle ist die
                # EINE Helferin webui.bausteine.fehler_grund (auch die Pass-Seite liest
                # sie — Widerleger 11.08.: drei Streu-Antworten auf dieselbe Frage,
                # zwei zeigten Nachspann statt Ursache). Ohne Log ein ehrlicher
                # Verweis statt gar nichts (genau sein Screenshot-Fall).
                fehlergrund = ""
                if kat == "fehler":
                    _lp = os.path.join(cfg["data_dir"], "events", ed, "analyze.log")
                    try:
                        _g = _fehler_grund(_lp)
                        _hat_log = os.path.isfile(_lp)
                    except Exception:
                        _g, _hat_log = "", False   # Grund-Zeile ist Komfort, nie ein Seitenkiller
                    # Zwei ehrliche Fallbacks (Widerleger-Recheck): ein VORHANDENES Log
                    # ohne Grund-Zeile darf nicht als "kein Log" ausgegeben werden.
                    fehlergrund = (
                        f'<div class="evrow"><span class="lab">Error reason</span>'
                        + (f'<span>{html.escape(_g)}</span></div>' if _g else
                           ('<span class="dim">analyze.log holds no reason line — '
                            'use the log button below</span></div>' if _hat_log else
                            '<span class="dim">no analyze.log kept for this event — '
                            'see the service log (System page)</span></div>')))
                inhalt = (
                    f'<div class="evhead"><a href="/heute" class="back">← Today</a>'
                    f'<h2>{cam} · <span class="num">{t}</span></h2></div>'
                    f'{passleiste}'
                    f'<div class="card evmeta"><div class="evbadges">{kbadge}{conf}</div>'
                    f'<div class="evrow"><span class="lab">Frigate</span><span>{html.escape(ftxt)}</span></div>'
                    f'<div class="evrow"><span class="lab">suslik</span><span>{html.escape(ours)}</span></div>'
                    f'{fehlergrund}'
                    f'<div class="evactions">{vid}{logl}</div>'
                    f'<div class="evgt"><span class="lab">{"Correct if wrong" if best else "Who was it?"}</span>{gtb}</div></div>'
                    f'<h3>Images</h3>{galerie}')
                return self._send(200, webui.layout("Event", "/heute", inhalt, self._banner()))
            m = re.match(rf"^/events/({_reg.EID_RE})/({_reg.DATEI_RE}\.(?:jpg|log|jsonl))$", path)
            if m:                                          # Crops/Logs ausliefern (Pfad strikt validiert)
                base = os.path.realpath(os.path.join(cfg["data_dir"], "events"))
                p = os.path.realpath(os.path.join(base, m.group(1), m.group(2)))
                # realpath-Containment: der Regex laesst ".." als Segment durch ([\w.-] enthaelt Punkte)
                if p.startswith(base + os.sep) and os.path.isfile(p):
                    ct = "image/jpeg" if p.endswith(".jpg") else "text/plain; charset=utf-8"
                    return self._send(200, open(p, "rb").read(), ct)
                return self._send(404, "not found", "text/plain")
            if path == "/offen":                           # Abend-Arbeitsliste: unbestaetigt + Gesicht + ungelabelt
                import webui
                # Modulumbau R1: Rendern byte-treu in routes/ereignisliste.py
                # (gt_schnellpersonen/master_persons injiziert — eine Quelle im Kern).
                from routes import ereignisliste as _r_el
                inhalt = _r_el.render_offen(cfg, svc.log_path, qs,
                                            gt_schnellpersonen, master_persons)
                return self._send(200, webui.layout("To label", "/offen", inhalt, self._banner()))
            if path != "/ereignisse":
                return self._send(404, "not found", "text/plain")
            import webui
            # Modulumbau R1: Rendern byte-treu in routes/ereignisliste.py.
            from routes import ereignisliste as _r_el
            self._send(200, webui.layout("Events", "/ereignisse",
                                         _r_el.render_ereignisse(
                                             cfg, svc.log_path, qs,
                                             gt_schnellpersonen, master_persons),
                                         self._banner()))

    return H


# ------------------------------------------------------------------ Main
def hardware_probe(placement_mess=None):
    """Beschleuniger-Status fuer Selbstcheck/Wizard: je Geraet -> gefunden (Geraetedatei) + nutzbar.
    Autoritativ via openvino.Core().available_devices (wenn das Paket da ist — dort erscheinen GPU/NPU
    nur, wenn Treiber+Runtime wirklich greifen); sonst Fallback: Geraetedatei da + OpenVINO-EP
    einkompiliert = 'gefunden, Nutzung hier nicht bestaetigt'. Ergebnis: Liste (marker, name, detail),
    marker 'ok'=gruen (gefunden+nutzbar), 'warn'=gelb (gefunden, Treiber fehlt), '?'=unbestaetigt,
    '--'=nicht gefunden."""
    import glob as _glob
    ov_usable = None
    try:
        import openvino as _ov
        ov_usable = {d.split(".")[0].upper() for d in _ov.Core().available_devices}
    except Exception:
        ov_usable = None
    try:
        import onnxruntime as _ort
        eps = _ort.get_available_providers()
    except Exception:
        eps = []
    ov_ep = "OpenVINOExecutionProvider" in eps

    def stat(present, key):
        if not present:
            return ("--", "not found")
        if ov_usable is not None:
            return ("ok", "found & usable") if key in ov_usable \
                else ("warn", "found but NOT usable — runtime/driver version mismatch — using CPU")
        return ("?", "found; OpenVINO EP present, engagement unconfirmed here") if ov_ep \
            else ("warn", "found; no OpenVINO runtime")

    from core.registry import knoten_von              # P3.1: Knoten-Muster aus der Registry
    res = []
    m, d = stat(bool(_glob.glob(knoten_von("GPU"))), "GPU"); res.append((m, "hw iGPU", d))
    m, d = stat(bool(_glob.glob(knoten_von("NPU"))), "NPU"); res.append((m, "hw NPU", d))
    # P4-Nachzieher (0.1.0.44, User 27.07.): das "?"-Urteil aufloesen. Das openvino-Paket
    # fehlt im Image BEWUSST (zweite OV-Runtime neben onnxruntime-openvino = Konfliktrisiko),
    # available_devices ist also nicht abfragbar. Stattdessen ECHTE Bind-Fakten: (a) die
    # Placement-Benchmark-Messung vom Boot (AUTO-Fall — beide Geraete real gebunden/nicht),
    # (b) sonst eine budgetierte Mini-Bind-Probe je gefundenem Geraet (Session bauen,
    # get_providers pruefen; mit warmem OV-Cache <1 s). Gleiche Probe-Philosophie wie
    # video_encoder() — messen statt raten.
    if ov_usable is None and ov_ep:
        mess = dict(placement_mess or {})
        if not mess:
            try:
                from face_audit import MODELLE, _ort_session
                onnx = next((v["onnx"] for v in MODELLE.values()
                             if v.get("onnx") and os.path.exists(v["onnx"])), None)
                cache = os.environ.get("OV_CACHE_DIR")
                if onnx:
                    for dev in ("GPU", "NPU"):
                        try:
                            s = _ort_session("openvino", dev, onnx, cache)
                            mess[dev] = {"bind": "OpenVINOExecutionProvider" in s.get_providers()}
                        except Exception:
                            mess[dev] = {"bind": False}
            except Exception:
                mess = {}
        neu = []
        for m2, name, d2 in res:
            key = "GPU" if "iGPU" in name else "NPU"
            fakt = (mess.get(key) or {}).get("bind")
            if m2 == "?" and fakt is True:
                neu.append(("ok", name, "found & usable — device bound in real probe"))
            elif m2 == "?" and fakt is False:
                neu.append(("warn", name, "found but did NOT bind in real probe — driver/runtime mismatch"))
            else:
                neu.append((m2, name, d2))
        res = neu
    if "CUDAExecutionProvider" in eps:
        res.append(("ok", "hw CUDA", "CUDAExecutionProvider available"))
    if "MIGraphXExecutionProvider" in eps:
        # AMD/ROCm (rocm-Fall 31.07.): /dev/kfd ist die Schluessel-Voraussetzung und war bisher
        # NIRGENDS im Startlog sichtbar — Fern-Diagnose am Tester-Log war damit unmoeglich.
        if _glob.glob(knoten_von("KFD")):
            res.append(("ok", "hw AMD", "MIGraphXExecutionProvider available, /dev/kfd present"))
        else:
            res.append(("warn", "hw AMD", "MIGraphXExecutionProvider available but no /dev/kfd — "
                                          "pass /dev/kfd + /dev/dri into the container; using CPU"))
    return res


def driver_versions():
    """Installierte Intel-Treiber-Versionen (compute-runtime/NPU/level-zero/IGC) aus dpkg — zeigt im
    Startlog, WELCHE Treiber im Image wirklich stecken. Leer, wenn keine da (CPU-Image / Nicht-Debian)."""
    import subprocess
    pkgs = [("compute-runtime", "intel-opencl-icd"), ("NPU", "intel-level-zero-npu"),
            ("level-zero", "libze1"), ("IGC", "intel-igc-core-2")]
    out = []
    for label, pkg in pkgs:
        try:
            v = subprocess.run(["dpkg-query", "-W", "-f=${Version}", pkg],
                               capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            v = ""
        if v:
            out.append(f"{label} {v}")
    return ", ".join(out)


def cuda_versions():
    """CUDA-Seite fuers Startlog (analog zu driver_versions fuer Intel): welcher HOST-Treiber greift
    (nvidia-smi kommt zur Laufzeit vom nvidia-container-toolkit, inkl. dessen max. CUDA) plus die im Image
    GEBACKENE CUDA-Runtime + cuDNN + onnxruntime-gpu. Leer, wenn kein CUDA-EP da (Nicht-CUDA-Image)."""
    try:
        import onnxruntime as _ort
        if "CUDAExecutionProvider" not in _ort.get_available_providers():
            return ""
    except Exception:
        return ""
    import glob as _glob
    out = []
    try:                                                   # Host-GPU + Treiber + max. CUDA des Treibers
        q = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=5).stdout.strip().splitlines()
        if q:
            name, drv = (q[0].split(",") + ["", ""])[:2]
            out.append(f"host {name.strip()} driver {drv.strip()}")
        head = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5).stdout
        mm = re.search(r"CUDA Version:\s*([0-9.]+)", head)
        if mm:
            out.append(f"driver-CUDA {mm.group(1)}")
    except Exception:
        pass
    try:                                                   # gebackene CUDA-Runtime aus dem Image
        with open("/usr/local/cuda/version.json") as f:
            cv = json.load(f).get("cuda", {}).get("version", "")
        if cv:
            out.append(f"image-CUDA {cv}")
    except Exception:
        pass
    cud = _glob.glob("/usr/lib/*/libcudnn.so.*") + _glob.glob("/usr/local/cuda*/lib64/libcudnn.so.*")
    if cud:
        out.append("cuDNN " + os.path.basename(sorted(cud)[-1]).split("libcudnn.so.")[-1])
    try:
        out.append(f"onnxruntime-gpu {_ort.__version__}")
    except Exception:
        pass
    return ", ".join(out)


def rocm_versions():
    """ROCm-Seite fuers Startlog (analog driver_versions/cuda_versions): das rocm-Image traegt
    ROCm als selektives Datei-Buendel OHNE dpkg-Eintraege (am Image gemessen 31.07.) — darum
    dateibasiert: /opt/rocm-Symlink traegt die Version im Zielnamen, HIP-Runtime im
    libamdhip64-Suffix, MIGraphX-Libs unter lib/migraphx. Leer, wenn kein MIGraphX-EP da."""
    try:
        import onnxruntime as _ort
        if "MIGraphXExecutionProvider" not in _ort.get_available_providers():
            return ""
    except Exception:
        return ""
    import glob as _glob
    out = []
    try:
        ziel = os.path.basename(os.path.realpath("/opt/rocm"))     # rocm-7.2.4
        if ziel.startswith("rocm-"):
            out.append(f"ROCm {ziel[5:]}")
    except Exception:
        pass
    hip = _glob.glob("/opt/rocm*/lib/libamdhip64.so.*.*")
    if hip:
        out.append("HIP " + os.path.basename(sorted(hip)[-1]).split("libamdhip64.so.")[-1])
    if _glob.glob("/opt/rocm*/lib/migraphx/lib/libmigraphx.so*"):
        out.append("MIGraphX libs present")
    try:
        import onnxruntime as _ort
        out.append(f"onnxruntime-migraphx {_ort.__version__}")
    except Exception:
        pass
    return ", ".join(out)


# Referenzwerte, auf UNSEREM System GEMESSEN (2026-07-22) — Vergleichsbasis fuer andere Hardware, damit
# das Ergebnis fuer alle einordbar ist (User-Wunsch: "Referenzwerte mit angeben"). Gemessen, nicht geraten.
BENCHMARK_REFERENCE = ("Intel Core Ultra 9 285H", "2026-07-22", {"CPU": 840, "iGPU": 26, "NPU": 18})


def hardware_benchmark(max_iters=30, budget_s=3.0, cache_dir=None):
    """Synthetischer Funktions-/Perf-Test je NUTZBAREM Backend (Startup-Schritt + on-demand `--benchmark`).
    Baut eine ECHTE onnxruntime-Session, misst ms/Inferenz mit Zufalls-Input. ZEITBUDGETIERT: pro Device
    laeuft es bis budget_s ODER max_iters erreicht ist (haelt den Boot bounded, egal wie langsam die CPU).
    Nur Backends, die WIRKLICH binden (der EP muss in get_providers() bleiben) -> kein irrefuehrender
    CPU-Fallback als 'GPU'. Synthetisch -> keine echten Gesichter noetig. cache_dir cached den OpenVINO-
    Kernel-Compile ueber Boots hinweg (erster Start kompiliert, danach schnell). Beantwortet
    'laeuft es wirklich + wie gut sind wir aufgestellt' messbasiert statt angenommen."""
    import onnxruntime as ort, numpy as np
    import time as _time
    from face_audit import MODELLE, aktuelles_modell, _ort_session
    m = aktuelles_modell(); mspec = MODELLE.get(m, {})
    onnx = mspec.get("onnx") if mspec.get("art") == "onnx" and os.path.exists(mspec.get("onnx", "")) else None
    if not onnx:
        onnx = next((v["onnx"] for v in MODELLE.values() if v.get("onnx") and os.path.exists(v["onnx"])), None)
    if not onnx:
        return [("--", "benchmark", "no onnx model available to probe")]
    avail = ort.get_available_providers()
    # Kandidaten: (Label, kind, device, erwarteter EP) — P3.1 aus der Registry generiert
    # (ein neues Backend/Geraet erscheint hier automatisch; Reihenfolge = Registry-Ordnung,
    # identisch zur bisherigen Literal-Liste, MIXED traegt bewusst kein Benchmark-Label).
    from core.registry import BACKENDS, geraete_von
    cands = [("CPU (baseline)", "cpu", None, BACKENDS["cpu"]["ep"])]
    for _kind in ("openvino", "cuda", "migraphx"):
        if BACKENDS[_kind]["ep"] in avail:
            for _d in geraete_von(_kind):
                if _d.get("benchmark_label"):
                    cands.append((_d["benchmark_label"], _kind, _d["name"], BACKENDS[_kind]["ep"]))
    # laufendes System auslesen (Kontext: welche CPU misst hier ueberhaupt?)
    cpu = "?"
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip(); break
    except Exception:
        pass
    res = [("info", "this system", f"{cpu} ({os.cpu_count()} threads)")]
    for label, kind, dev, want in cands:
        try:
            s = _ort_session(kind, dev, onnx, cache=cache_dir)
            if want not in s.get_providers():                 # gebaut, aber Device band NICHT -> ehrlich skip
                res.append(("--", label, "device not available (would fall back to CPU) — skipped"))
                continue
            inp = s.get_inputs()[0]
            shape = [d if isinstance(d, int) else 1 for d in inp.shape]
            x = np.random.randn(*shape).astype(np.float32)
            s.run(None, {inp.name: x})                        # Warmup (Modell-Compile/Kernel-Cache)
            t0 = _time.perf_counter(); n = 0
            while n < max_iters and (_time.perf_counter() - t0) < budget_s:
                s.run(None, {inp.name: x}); n += 1
            ms = (_time.perf_counter() - t0) / max(n, 1) * 1000.0
            res.append(("ok", label, f"{ms:6.1f} ms/inf  {1000.0 / ms:5.0f} inf/s  ({n} runs)"))
        except Exception as e:
            res.append(("--", label, f"error: {str(e)[:60]}"))
    # Referenzwerte (auf unserem System gemessen) als Vergleichsbasis anhaengen
    ref_cpu, ref_date, ref_vals = BENCHMARK_REFERENCE
    res.append(("info", "reference", f"{ref_cpu} ({ref_date}): "
                + " · ".join(f"{k} {v}ms" for k, v in ref_vals.items())))
    return res


def varianten_hinweis(variante, probe):
    """Task #13, schlanke Stufe (User 28.07., "muss nicht perfekt sein"): sagt dem
    Nutzer im Banner, wenn eine ANDERE Image-Variante seine GEFUNDENE Hardware nutzen
    koennte. Nur sichere Faelle (Probe-Fakten, sichtbare Geraete-Nodes), KEINE
    Performance-Versprechen, keine Generations-Raterei; None = kein Hinweis.
    variante kommt als SUSLIK_VARIANT aus dem Image — leer (Alt-Image/venv) = still."""
    if not variante:
        return None
    igpu_da = igpu_kaputt = False
    for mark, name, detail in probe:
        if name.strip().lower().startswith("igpu"):
            igpu_da = not detail.startswith("not found")
            igpu_kaputt = "did NOT bind" in detail
    nvidia_da = os.path.exists("/dev/nvidiactl") or os.path.exists("/dev/nvidia0")
    if variante == "cpu" and igpu_da:
        return ("Found an Intel GPU that this CPU-only image cannot use — the gpu image "
                "(or gpu-legacy for Intel 6th–10th gen / UHD 6xx) would use it for recognition.")
    if variante == "cpu" and nvidia_da:
        return "Found an NVIDIA GPU that this CPU-only image cannot use — the cuda image would."
    if variante == "gpu" and igpu_kaputt:
        return ("Your Intel GPU was found but did not bind with this image's current Intel "
                "runtime. If it is an older iGPU (Intel 6th–10th gen / UHD 6xx), the "
                "gpu-legacy image supports it; otherwise check the host driver.")
    if variante == "gpu-legacy" and igpu_kaputt:
        return ("Your Intel GPU was found but did not bind with the legacy runtime — a newer "
                "iGPU (Intel 11th gen or later) needs the regular gpu image.")
    if variante in ("gpu", "gpu-legacy") and not igpu_da and nvidia_da:
        return "Found an NVIDIA GPU — the cuda image would use it for recognition."
    # Umkehr-Faelle (User-Fund 05.08.): cuda/rocm-Image auf fremder Hardware
    # lief bisher ohne jeden Hinweis still auf CPU.
    render_da = os.path.exists("/dev/dri/renderD128")
    if variante == "cuda" and not nvidia_da:
        if render_da:
            return ("No NVIDIA GPU found, but a /dev/dri render device is present. "
                    "If that is an Intel iGPU, the gpu image would use it — this "
                    "cuda image runs recognition on the CPU here.")
        return ("No NVIDIA GPU found — this cuda image runs recognition on the "
                "CPU here; the cpu image does the same with a much smaller download.")
    if variante == "rocm" and nvidia_da:
        return "Found an NVIDIA GPU — the cuda image would use it for recognition."
    return None


def daten_mount_hinweis(data_dir):
    """Issue #13 (Tokn59, 03.08.): sein Compose hatte keinen volumes:-Eintrag, /data
    lag im Container — das Update ersetzte den Container und alle Daten waren weg.
    Warnt laut (Startlog UND UI-Banner, User-Vorgabe), wenn der Datenpfad im
    Container liegt, aber KEIN eigener Mount ist (weder Volume noch Bind) — dann
    stirbt er mit dem Container. Nur im Container pruefen (venv-Lauf hat
    naturgemaess keinen Mount); keine Diagnose moeglich = kein falscher Alarm."""
    if not (os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")):
        return None
    ziel = os.path.realpath(data_dir or "")
    if not ziel or ziel == "/":
        return None
    try:
        with open("/proc/self/mountinfo") as f:
            punkte = {z.split(" ")[4] for z in f if len(z.split(" ")) > 4}
    except Exception:
        return None
    if any(p != "/" and (ziel == p or ziel.startswith(p + "/")) for p in punkte):
        return None
    return (f"Your data is stored INSIDE the container: {ziel} is not a mounted "
            "volume, so people, events and settings are lost when the container is "
            "recreated (e.g. on update). Add a volumes entry like "
            "\"./suslik-data:/data\" to your compose file, then move your data in.")


def startup_selfcheck(svc):
    """Lesbarer, nummerierter Startup-Ablauf nach stdout (docker logs -f) + Log-Puffer (/log): je
    Schritt [i/N] WAS getan wird (config/hardware/backend/model/frigate/references) + darunter WAS
    gefunden/nutzbar ist ([ ok ]/[warn]/[FAIL]/[ ? ]/[info]). So sieht man beim Start sofort, was
    greift und was nicht (Fern-Support + Weiterentwicklung). Roadmap Phase 4/10."""
    import onnxruntime as _ort
    from face_audit import resolve_backend, aktuelles_modell, MODELLE, _ort_session   # dort def., nicht verifyd
    cfg, L = svc.cfg, svc.log

    N = 7

    def schritt(i, name, tut):                        # ein nummerierter Schritt: WAS wird getan
        _schritt_ctx.update(nr=i, name=name)
        L(f"[{i}/{N}] {name:<10} {tut} …")

    # SD1 minimal (P3.4/Anti-Selbstzweck-Schnitt): jede erg()-Zeile wird ZUSAETZLICH als
    # Record gesammelt und am Ende nach state/startup.json geschrieben (core/selfcheck) —
    # das Menschen-Log bleibt byte-identisch; /health leitet 'ok' aus den Records ab (B8).
    _records, _schritt_ctx = [], {"nr": 0, "name": "?"}

    def erg(mark, detail):                            # das Ergebnis darunter: WAS wurde gefunden
        _records.append({"schritt": _schritt_ctx["nr"], "name": _schritt_ctx["name"],
                         "mark": str(mark).strip(), "detail": str(detail)})
        L(f"         [{mark:^5}] {detail}")

    L(f"========== suslik {suslik_version()} startup ==========")
    # 1) Config
    dd = cfg.get("data_dir") or "?"
    schritt(1, "config", "reading yaml + store, checking data dir")
    try:
        _t = os.path.join(dd, ".writetest")
        with open(_t, "w") as f:
            f.write("x")
        os.remove(_t)
        erg("ok", f"data_dir={dd} (writable), model={aktuelles_modell()}")
    except Exception as e:
        erg("FAIL", f"data_dir={dd} NOT writable: {e}")
    # Issue #13: /data ohne Mount = Datenverlust beim naechsten Recreate — laut
    # sagen, im Log UND als stehender UI-Banner (gleiche Quelle, ein Text).
    svc.daten_hinweis = daten_mount_hinweis(dd)
    if svc.daten_hinweis:
        erg("warn", svc.daten_hinweis)
    # 2) Hardware (gruene Haken: gefunden + nutzbar / Treiber fehlt)
    schritt(2, "hardware", "probing accelerators — found + usable?")
    probe = hardware_probe(((getattr(svc, "cfg", None) or {}).get("placement_info") or {}).get("mess"))
    for mark, name, detail in probe:
        erg(mark, f"{name.replace('hw ', ''):<5} {detail}")
    # Task #13 (schlank): passt die Image-Variante zur gefundenen Hardware? Der Hinweis
    # erscheint im UI-Banner (_banner) UND hier im Startup-Log (Fern-Support).
    svc.varianten_hinweis = varianten_hinweis(os.environ.get("SUSLIK_VARIANT", ""), probe)
    if svc.varianten_hinweis:
        erg("hint", svc.varianten_hinweis)
    # Video-Encoder mit ECHTER Encode-Probe (Tester-Issue 26.07.): vorher fiel der Clip-Transcode
    # zu 100% still auf libx264/CPU zurueck (renderD128 hartcodiert, gpu-Image ohne Mediatreiber)
    # — hier sichtbar machen, sonst findet das wieder niemand. Erster Aufruf fuellt den Cache,
    # die Callsites (_telegram_clip/make_browser_copy) nutzen dann dasselbe Ergebnis.
    v_art, v_node = video_encoder()
    if v_art == "cpu":
        erg("warn", f"{'video':<5} libx264 (CPU) — {_VIDEO_PROBE_GRUND or 'no hw encoder'}; "
                    "clip transcode will cost CPU time")
    elif v_art == "nvenc-voll":
        erg("ok", f"{'video':<5} h264_nvenc — full-hw pipeline probe passed (decode+scale+encode)")
    elif v_art == "nvenc":
        erg("ok", f"{'video':<5} h264_nvenc — encode probe passed (decode/scale on CPU: "
                  "full-hw probe failed)")
    else:
        erg("ok", f"{'video':<5} h264_{v_art}{f' ({v_node})' if v_node else ''} — encode probe passed")
    dv = driver_versions()
    if dv:
        erg("info", f"Intel drivers: {dv}")
    cv = cuda_versions()
    if cv:
        erg("info", f"CUDA: {cv}")
    rv = rocm_versions()
    if rv:
        erg("info", f"ROCm: {rv}")
    # 3) Backend — ECHTES Device-Binding testen, nicht nur EP-Praesenz (sonst "ok" obwohl real CPU laeuft:
    #    die OpenVINO-EP kann DA sein, das Device 'GPU' aber "not available" -> onnxruntime faellt still
    #    auf CPU zurueck, erkennbar daran, dass der EP aus session.get_providers() rausfaellt).
    schritt(3, "backend", "selecting execution provider — does the device really bind?")
    try:
        kind, dev = resolve_backend(None)
        avail = _ort.get_available_providers()
        from core.registry import ep_von              # P3.1: EP-Soll aus der Registry —
        want = ep_von(kind)                           # ein neues kind kann hier nie mehr fehlen
        spec = f"{kind}{':' + dev if dev else ''}"
        if kind == "cpu":
            erg("ok", f"{spec} — providers: {', '.join(avail)}")
        elif not (want and want in avail):
            # EP fehlt ganz -> haeufigster Fehler: plain onnxruntime verdeckt onnxruntime-openvino.
            erg("warn", f"requested {spec} but {want} unavailable ({', '.join(avail)}) — CPU fallback")
            if kind == "openvino":
                erg("hint", "onnxruntime lacks the OpenVINO EP — a plain onnxruntime shadows "
                            "onnxruntime-openvino in this image; rebuild so the openvino build wins")
        else:
            # EP da -> harter Test: eine echte Session auf dem Device bauen (irgendein ONNX als Vehikel,
            # Device-Verfuegbarkeit ist modellunabhaengig). Bindet der EP -> gruen; sonst CPU-Fallback.
            onnx = next((v["onnx"] for v in MODELLE.values()
                         if v.get("onnx") and os.path.exists(v["onnx"])), None)
            if not onnx:
                erg("?", f"{spec} — EP present, engagement unconfirmed (no onnx model to probe)")
            elif dev == "MIXED":
                # P4: MIXED ist UNSER Untermodus (detector=GPU, recognition=NPU; face_audit
                # _to_backend verteilt) und KEIN OpenVINO-Device — eine device_type=MIXED-Probe
                # wuerde nie binden und der Check meldete faelschlich CPU-Fallback. Also je
                # Teil-Device einzeln proben.
                teile = []
                for d2, rolle in (("GPU", "detector"), ("NPU", "recognition")):
                    try:
                        s = _ort_session(kind, d2, onnx)
                        teile.append((rolle, d2, want in s.get_providers()))
                    except Exception:
                        teile.append((rolle, d2, False))
                if all(okk for _, _, okk in teile):
                    erg("ok", "openvino:MIXED — device engaged (detector=GPU, recognition=NPU)")
                else:
                    kaputt = ", ".join(f"{r}({d2})" for r, d2, okk in teile if not okk)
                    erg("warn", f"openvino:MIXED — {kaputt} did not bind — per-model "
                                f"fallback chain takes over (NPU→GPU→CPU)")
            else:
                try:
                    s = _ort_session(kind, dev, onnx)
                    if want in s.get_providers():
                        erg("ok", f"{spec} — device engaged")
                    else:
                        # Widerleger-Fund .66: ohne Geraeteknoten ist "mismatch?" irrefuehrend —
                        # die Plattform HAT das Geraet dann schlicht nicht (Issue-#6-Klasse).
                        import glob as _sglob
                        from face_audit import geraete_knoten_muster as _gkm
                        # migraphx/cuda: dev ist eine Geraetenummer ('0'), der Pflicht-Knoten ist
                        # /dev/kfd bzw. /dev/nvidia* — sonst liefe die Knoten-Vorpruefung ins Leere
                        # und meldete "mismatch?" obwohl die Plattform das Geraet schlicht nicht hat
                        # (Gen9-Klasse). P3.1: Familie+Muster aus der Registry.
                        from core.registry import knoten_familie
                        if kind in ("migraphx", "cuda"):
                            _kdev, _kn = knoten_familie(kind)
                        else:
                            _kdev, _kn = dev, _gkm(dev)
                        if _kn and not _sglob.glob(_kn):
                            erg("warn", f"requested {spec} but this host has no {_kdev} device "
                                        f"({_kn}) — running on CPU")
                        else:
                            erg("warn", f"requested {spec} but device not available — running on CPU "
                                        f"(GPU/NPU runtime vs. host driver version mismatch?)")
                except Exception as e:
                    erg("warn", f"requested {spec} but bind failed ({str(e)[:80]}) — CPU fallback")
        pi = (getattr(svc, "cfg", None) or {}).get("placement_info")
        if pi:
            _m = pi.get("mess") or {}
            erg("info", f"placement: {pi.get('backend')} ({pi.get('quelle')}; "
                        f"NPU cpu/inf {(_m.get('NPU') or {}).get('cpu_ms', '–')} ms, "
                        f"GPU cpu/inf {(_m.get('GPU') or {}).get('cpu_ms', '–')} ms — "
                        f"sticky in state/placement.json)")
        # Versionsstaende immer zeigen — passen Runtime + OpenVINO + Host-Treiber zusammen?
        try:
            import openvino as _ov
            ovv = getattr(_ov, "__version__", "?")
        except Exception:
            ovv = "not installed"
        ov_build = "OpenVINOExecutionProvider" in avail
        erg("info", f"runtime: onnxruntime {_ort.__version__}, OpenVINO EP built-in: "
                    f"{'yes' if ov_build else 'NO'}; standalone openvino pkg (probe helper only): {ovv}")
        # Welche GPU haengt eigentlich dran? (A1, Tester-Bestaetigung: Arc A380.) NUR melden, wenn der
        # Geraeteknoten wirklich in den Container gereicht wurde: /sys/class/drm zeigt sonst die
        # HOST-GPUs, die dieser Container gar nicht benutzen kann (Plan-QS am cpu-Image gemessen).
        # openvino ist hier bewusst nicht importierbar, also PCI-Kennungen aus sysfs — hart
        # belegbar, statt Modellnamen zu raten. Die Zuordnung renderD -> GPU.0/GPU.1 ist NICHT
        # garantiert (OpenVINO zaehlt selbst), deshalb wird sie auch nicht behauptet.
        try:
            knoten = sorted(k for k in os.listdir("/dev/dri") if k.startswith("renderD")) \
                if os.path.isdir("/dev/dri") else []
            teile = []
            for k in knoten:
                try:
                    with open(f"/sys/class/drm/{k}/device/vendor") as f1, \
                         open(f"/sys/class/drm/{k}/device/device") as f2:
                        v, d = f1.read().strip(), f2.read().strip()
                    her = {"0x8086": "Intel", "0x10de": "NVIDIA", "0x1002": "AMD"}.get(v, v)
                    teile.append(f"{k}={her} {d}")
                except OSError:
                    teile.append(k)
            if teile:
                erg("info", "GPU render nodes passed through: " + ", ".join(teile))
                if len(teile) > 1 and kind == "openvino":
                    erg("hint", "multiple GPUs — OpenVINO enumerates GPU.0/GPU.1 in its own "
                                "order; pick one with OV_DEVICE=GPU.0 or GPU.1 and check "
                                "which engages")
        except OSError:
            pass
    except Exception as e:
        erg("FAIL", str(e))
    # 4) Modell
    schritt(4, "model", "checking recognition model file")
    try:
        m = aktuelles_modell(); mspec = MODELLE.get(m, {})
        if mspec.get("art") == "onnx":
            okm = os.path.exists(mspec.get("onnx", ""))
            erg("ok" if okm else "FAIL", f"{m} — {'ONNX present' if okm else 'ONNX MISSING: ' + mspec.get('onnx', '')}")
        else:
            erg("ok", f"{m} (insightface)")
    except Exception as e:
        erg("FAIL", str(e))
    # 5) Frigate
    schritt(5, "frigate", "connecting to Frigate API")
    try:
        cams, err = frigate_cameras(cfg, force=True)
        host = (cfg.get("frigate_url") or "").split("://")[-1] or "(not set)"
        if not (cfg.get("frigate_url") or "").strip():
            # Erstlauf ohne URL ist der NORMALZUSTAND eines frischen Systems, kein Fehler —
            # vorher stand hier [FAIL], und seit S4 auf "[FAIL" greppt, waere jede frische
            # Installation im Gate rot (Plan-QS P.6).
            erg("info", "no Frigate URL configured yet — the setup wizard will ask for it")
        elif err or not cams:
            erg("FAIL", f"{host} unreachable: {err or 'no cameras'} — set it in the setup wizard")
        else:
            erg("ok", f"{host} — {len(cams)} cameras")
    except Exception as e:
        erg("FAIL", str(e))
    # 6) Referenzen + Web-UI
    schritt(6, "references", "loading face master, starting web UI")
    try:
        persons = master_persons(cfg)
        if persons:
            erg("ok", f"{len(persons)} person(s): {', '.join(persons[:8])}")
        else:
            erg("warn", "0 — empty master; enroll via the setup wizard")
    except Exception as e:
        erg("FAIL", str(e))
    # 7) Benchmark — Vertrauen: WAS habe ich getestet + wie schnell je Device (zeitbudgetiert -> bounded)
    schritt(7, "benchmark", "timing each usable backend on synthetic input")
    try:
        cache = os.path.join(cfg.get("data_dir") or "", "clips", "ov_cache")   # clips/ ist vom Backup ausgeschlossen (Cache = regenerierbar, NICHT in state/)
        try:
            os.makedirs(cache, exist_ok=True)
        except Exception:
            cache = None
        for mark, label, detail in hardware_benchmark(max_iters=20, budget_s=1.5, cache_dir=cache):
            erg(mark, f"{label:<16} {detail}")
    except Exception as e:
        erg("warn", f"benchmark skipped: {str(e)[:80]}")
    erg("info", f"web UI on http://0.0.0.0:{cfg.get('web_port')}/  "
                f"({'first run -> setup wizard' if not cfg.get('frigate_url') else 'ready'})")
    try:
        from core import selfcheck as _sc
        _, svc.startup_fails = _sc.schreiben(cfg["data_dir"],
                                             os.environ.get("SUSLIK_VERSION", "dev"), _records)
    except Exception as e:                            # Diagnose darf den Start nie reissen
        svc.startup_fails = 0
        L(f"selfcheck records not written: {e}")
    L("========== ready ==========")


def _sigterm(signum, frame):
    """SIGTERM/SIGINT sauber beenden. Im Container laeuft dieser Prozess als PID 1, und der Kernel
    liefert PID 1 KEINE Default-Signalbehandlung: ohne eigenen Handler ignoriert der Dienst
    'docker stop' komplett, wartet die volle Grace-Zeit ab und wird dann per SIGKILL hart
    abgeschossen — mitten in jedem laufenden Schreibvorgang. Mit Handler endet der Prozess
    geordnet (offene Dateien werden von CPython beim Exit geschlossen/geflusht)."""
    sys.stderr.write(f"\n[suslik] signal {signum} received — shutting down cleanly.\n")
    sys.stderr.flush()
    sys.exit(0)


def main():
    # umask 022 fuer den GANZEN Dienst-Baum (Kinder erben: Engine, Worker,
    # Wartung): der Container schreibt als root, und mit der Default-umask
    # entstanden 600er-Dateien, die der Host weder lesen noch sichern konnte
    # (Realfall 13.08.: Lernlauf-Referenzen + state-JSONs fehlten im
    # NAS-Backup; davor 11.08. dieselbe Klasse). Betriebsdaten im /data-Mount
    # muessen host-lesbar sein — Geheimnisse liegen dort keine (Credential-
    # Store maskiert, .env bleibt draussen).
    os.umask(0o022)
    for _sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(_sig, _sigterm)
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "verifyd.yaml"))
    ap.add_argument("--once", default=None, help="genau dieses Event verarbeiten, dann Ende (Test)")
    ap.add_argument("--dry-alert", action="store_true", help="Alerts nur loggen, nicht senden")
    ap.add_argument("--benchmark", action="store_true",
                    help="synthetischer Hardware-Benchmark je Backend (CPU/iGPU/NPU/CUDA), dann Ende")
    a = ap.parse_args()
    cfg = load_config(a.config)

    if a.benchmark:                               # on-demand: laeuft es wirklich + wie schnell je Device?
        cache = os.path.join(cfg.get("data_dir") or "", "clips", "ov_cache")   # clips/ ist vom Backup ausgeschlossen (Cache = regenerierbar, NICHT in state/)
        try:
            os.makedirs(cache, exist_ok=True)
        except Exception:
            cache = None
        print("========== suslik hardware benchmark ==========")
        for mark, label, detail in hardware_benchmark(max_iters=50, budget_s=5.0, cache_dir=cache):
            print(f"  [{mark:^4}] {label:<16} {detail}")
        print("===============================================")
        return

    svc = Service(cfg, dry_alert=a.dry_alert)
    svc.config_pfad = a.config

    if a.once:
        svc.start_publisher()                 # --once ist vollwertiger Testpfad (auch MQTT/Szenen)
        time.sleep(1)
        svc.processed.discard(a.once)
        entry = svc.process(a.once)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        svc.worker_stoppen()                  # W2: --once = start -> 1 Job -> geordnet beenden
        return                                # non-daemon Szenen-Timer haelt den Prozess ggf. karenz_s am Leben

    # Publisher VOR dem Webserver (Widerleger 11.08.): die differenzierte MQTT-Ampel
    # zeigte sonst in JEDEM Selfcheck-Fenster nach einem Config-Neustart minutenlang
    # CHECK "publisher not started", obwohl nichts kaputt ist. start_publisher haengt
    # nur an cfg und verbindet asynchron — es gibt keinen Grund, damit zu warten.
    svc.start_publisher()
    web = ThreadingHTTPServer(("0.0.0.0", int(cfg["web_port"])), make_handler(svc))
    threading.Thread(target=web.serve_forever, daemon=True).start()
    svc.log(f"Webview: http://0.0.0.0:{cfg['web_port']}/")
    startup_selfcheck(svc)                    # strukturierter Selbstcheck nach stdout (Roadmap 4/10)
    svc.start_wartung()
    svc.start_stoerungswaechter()
    svc.start_nachhol()                   # gescheiterte Analysen spaeter stumm nachholen
    svc.start_live_aufsicht()             # Phase 4: Live-Engine-Supervisor (Autostart, wenn
    #                                       ein Waechter enabled ist; Standalone-Erkennung)
    svc.start_stream_steckbriefe()        # .186: echte Stream-Aufloesung je Kamera proben
    #                                       (Kachel-Kopf ohne Quelltest-Klick, User 13.08.)
    svc.vision_waisen_start()             # .164: Laeufe schliessen, die der letzte
    #                                       Neustart mitten drin erwischt hat
    if not cfg["frigate_url"]:                 # frisch (Docker-Erstboot): erst der Setup-Wizard,
        svc.log("frigate_url empty — setup wizard (UI) only; Frigate poll starts after the wizard restart")
        while True:                            # Web-Thread laeuft weiter (Wizard); wir pollen nicht ins Leere
            time.sleep(60)
    elif cfg["trigger"] == "mqtt":
        svc.mqtt_loop()
    else:
        svc.poll_loop()


if __name__ == "__main__":
    main()
