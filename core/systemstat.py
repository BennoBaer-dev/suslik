"""core/systemstat — DIE eine Quelle der Systemzahlen (Bauplan
analysen/bauplan_systemstatistik.md).

Warum ein eigenes Modul und keine Verteilung ueber den Dienst: die Seite, der
/health-Block und der 60-s-Schreiber muessen DIESELBEN Zahlen sehen. Zwei
Sammelstellen driften garantiert auseinander, und eine Systemseite, die etwas
anderes behauptet als /health, ist schlimmer als keine.

GRUNDREGEL (Bauplan §2, verbindlich): eine Quelle, die es auf DIESER Hardware
nicht gibt, liefert `None` plus einen Grund-Code — nie eine 0. Eine fehlende
Messung darf nie wie ein gemessener Ruhewert aussehen. Deshalb traegt jeder
Block neben dem Wert ein Feld `grund`; die Seite macht daraus einen Satz.

Was hier NICHT passiert (Bauplan §4): keine Aufteilung nach Prozess (Frigate
laeuft in einem anderen Container, `ps` findet dort nichts von ihm), keine
Schwellen und keine Alarme (dafuer gibt es die bestehenden Wachen — zwei
Stellen mit eigenen Schwellen driften auseinander), keine Historie ueber 48 h.

Messbarkeits-Befunde dieser Anlage (25.08.2026, im Prod-Container gemessen):
  CPU   /proc/stat — da. Im Container zeigt es den DOCKER-WIRT (hier 16 CPUs,
        waehrend der LXC 12 zugeteilt bekommt): also die Gesamtlast der
        Maschine, genau das, was die Seite zeigen soll.
  RAM   NUR ueber die eigene cgroup. /proc/meminfo im Container zeigt den
        Wirt (gemessen: 62 GiB statt der 16 GiB dieser Maschine) und ist
        deshalb VERBOTEN — dieselbe Falle, die die Doku wochenlang auf einer
        falschen Zahl hielt (wiki/maschinen.md).
  NPU   npu_busy_time_us, monotoner µs-Zaehler — da.
  GPU   Intel: i915-PMU vorhanden (6 *-busy-Events), perf_event_open aber
        EPERM — der Container hat kein CAP_PERFMON und perf_event_paranoid
        steht auf 4. In sysfs gibt es keinen Ersatz: max_busywait_duration_ns
        ist eine Stellschraube, kein Zaehler. Also KEINE Intel-GESAMT-
        Auslastung hier, und die Kachel sagt genau das.
        NACHTRAG zum Bauplan (§0 behauptete, fdinfo fuehre nur Speicher):
        i915 fuehrt sehr wohl drm-engine-<klasse>-Nanosekunden je Client
        (render/copy/video/video-enhance/compute, am laufenden Prod gesehen).
        Das taugt aber NICHT fuer diese Kachel: sichtbar sind nur die Clients
        im eigenen Namensraum, also nie die Gesamtlast der Maschine. Es ist
        der Weg fuer die im Bauplan vorgemerkte Stufe 2 ("unser eigener
        Anteil"), die hier bewusst nicht gebaut wird.
        NVIDIA: nvidia-smi. AMD: rocm-smi, hier ungeprueft (kein Geraet).

Dieses Modul liefert Zahlen, nie HTML und nie Urteile."""
import glob
import json
import os
import subprocess
import threading
import time

from core import registry as _reg

# Ringpuffer: eine Zeile je Takt, Aufbewahrung 48 h. Gekuerzt wird AUSSCHLIESSLICH
# im Nachtjob (verifyd Service.alt_aufraeumen) — kein zweiter Aufraeum-Ort, sonst
# raeumen zwei Stellen mit zwei Vorstellungen davon, was alt ist.
RING_TEILE = ("state", "systemstat.jsonl")
TAKT_S = 60
AUFBEWAHRUNG_H = 48
# Leseschutz gegen einen aufgeblaehten Puffer. GEMESSEN 25.08. (16 Kerne, keine
# Waechter): 996 Bytes je Zeile, also ~1,4 MB/Tag und ~2,8 MB fuer 48 h — der
# Bauplan hatte ~300 B/Zeile geschaetzt, die langen Klartext-Felder
# (Grenz-Quelle, Todesursache, Supervisor-Satz) wiederholen sich je Zeile.
# Der Deckel liegt bewusst deutlich darueber, damit auch eine Anlage mit vielen
# Waechtern die vollen 48 h am Stueck lesen kann. kuerzen() liest zeilenweise
# OHNE Deckel — das Stutzen bleibt also in jedem Fall vollstaendig.
LESE_DECKEL_B = 16 * 1024 * 1024

# Grund-Codes fuer fehlende Werte. DECKUNGS-VERTRAG: zu jedem Code gehoert ein
# Text-Schluessel "systemstat.grund.<code>" in core/texte/en.py, und umgekehrt.
# Das Gate prueft beide Richtungen — ein neuer Code ohne Satz wuerde sonst als
# nackter Bezeichner in der Oberflaeche landen.
GRUENDE = (
    "erster_lauf",        # Delta-Zaehler: die zweite Messung fehlt noch
    "kein_geraet",        # kein passender Geraeteknoten auf dieser Maschine
    "kein_zaehler",       # Geraet da, Treiber fuehrt keinen Auslastungszaehler
    "gesperrt",           # Quelle da, aber der Container darf sie nicht lesen
    "werkzeug_fehlt",     # das Abfrage-Werkzeug liegt nicht im Image
    "nicht_lesbar",       # Quelle da, Lesen/Auswerten scheiterte
    "kein_limit",         # kein Limit gesetzt, also kein Prozentsatz bildbar
    "kein_dienst",        # Kennzahl kennt nur der laufende Dienst
)

_LOCK = threading.Lock()
# Delta-Staende der monotonen Zaehler + die zuletzt gebaute Momentaufnahme.
# Der ERSTE Aufruf nach dem Start liefert fuer Delta-Werte None, nicht 0.
_STAND = {"cpu": None, "npu": None, "i915": None, "snap": None}
# Offene perf-fds der i915-PMU. Sie muessen ueber die Takte hinweg OFFEN bleiben:
# ein perf-Zaehler beginnt mit seinem fd bei 0, zwei Deltas ueber zwei fds waeren
# sinnlos. None = noch nicht versucht, {} = versucht und nichts bekommen.
_I915_FDS = None


# ------------------------------------------------------------------ kleine Helfer
def _text(pfad):
    with open(pfad, encoding="utf-8", errors="replace") as f:
        return f.read()


def _fehlt(grund, **rest):
    """Einheitlicher Fehl-Block: Wert None, Grund benannt."""
    d = {"prozent": None, "grund": grund}
    d.update(rest)
    return d


def _knoten_da(muster):
    """True, wenn zum Geraeteknoten-Muster der Registry hier etwas existiert."""
    return bool(muster) and bool(glob.glob(muster))


def _pflicht_knoten(kind):
    """Geraeteknoten-Muster des Default-Geraets eines Backend-kinds, aus
    core/registry (knoten_familie) — NIE als Literal in der Sonde.

    Projektregel: wer eine fachliche Angabe braucht, nimmt die zentrale
    Quelle. Ein in der Sonde abgeschriebenes Muster driftet still ab, sobald
    die Registry ihres aendert — die Kachel meldete dann 'kein Geraet' auf
    einer Maschine, die eines hat, und das ist genau die Sorte Luege, die
    diese Seite nicht erzaehlen darf. Das Gate prueft, dass hier kein
    Knoten-Literal zurueckkehrt."""
    return _reg.knoten_familie(kind)[1]


def geraete_lage():
    """-> {kind: (device-name, ...)} fuer jedes Backend-kind der Registry, dessen
    Geraeteknoten hier WIRKLICH liegt.

    Quelle ist ausschliesslich core/registry (BACKENDS/DEVICES) — die
    Projektregel verlangt fuer fachliche Aufzaehlungen die zentrale Quelle, nie
    ein weiteres verstreutes Literal. Ein kind ohne pruefbaren Knoten (cpu,
    MIXED) taucht mit leerem Tupel auf: es existiert, ist aber kein Geraet."""
    aus = {}
    for kind in _reg.BACKENDS:
        namen = []
        for dev in _reg.DEVICES.get(kind, ()):
            if _knoten_da(dev.get("knoten")):
                namen.append(dev["name"])
        aus[kind] = tuple(namen)
    return aus


# ------------------------------------------------------------------ CPU
def cpu_messen():
    """Gesamtauslastung der Maschine + je Kern, aus /proc/stat als Delta zweier
    Aufrufe. Erster Aufruf -> None (Grund erster_lauf).

    Bewusst /proc/stat und nicht die eigene cgroup: die Kachel zeigt die
    GESAMTlast (Bauplan §0/§1). Was suslik selbst davon verbraucht, ist die
    vorgemerkte Stufe 2 und steht hier absichtlich nicht."""
    def _lesen():
        werte = {}
        for z in _text("/proc/stat").splitlines():
            if not z.startswith("cpu"):
                break
            teile = z.split()
            name = teile[0]
            zahlen = [int(x) for x in teile[1:]]
            # user nice system idle iowait irq softirq steal guest guest_nice
            leer = zahlen[3] + (zahlen[4] if len(zahlen) > 4 else 0)
            werte[name] = (sum(zahlen), leer)
        return werte

    try:
        jetzt = _lesen()
    except Exception:                                        # noqa: BLE001
        return _fehlt("nicht_lesbar", kerne=None, n=None)
    if not jetzt.get("cpu"):
        return _fehlt("nicht_lesbar", kerne=None, n=None)
    with _LOCK:
        vorher = _STAND["cpu"]
        _STAND["cpu"] = jetzt
    if not vorher or "cpu" not in vorher:
        return _fehlt("erster_lauf", kerne=None, n=len(jetzt) - 1)

    def _last(name):
        if name not in vorher or name not in jetzt:
            return None
        d_ges = jetzt[name][0] - vorher[name][0]
        d_leer = jetzt[name][1] - vorher[name][1]
        if d_ges <= 0:                    # Zaehler-Ruecksetzer (Neustart des Wirts)
            return None
        return round(max(0.0, min(100.0, (d_ges - d_leer) * 100.0 / d_ges)), 1)

    # Kern-Namen aus der DATEI, nicht aus einem angenommenen Bereich cpu0..cpuN:
    # eine Luecke in der Nummerierung (offline genommener Kern) wuerde sonst alle
    # dahinter liegenden Kerne verschieben.
    namen = sorted((k for k in jetzt if k != "cpu"),
                   key=lambda k: int(k[3:]) if k[3:].isdigit() else 0)
    ges = _last("cpu")
    return {"prozent": ges, "kerne": [_last(k) for k in namen], "n": len(namen),
            "grund": None if ges is not None else "nicht_lesbar"}


# ------------------------------------------------------------------ RAM
def ram_messen():
    """Speicher aus der EIGENEN cgroup — /proc/meminfo ist hier verboten, es
    zeigt im Container den Docker-Wirt (Kopfkommentar, wiki/maschinen.md).

    genutzt = memory.current abzueglich des rueckholbaren Datei-Caches; das ist
    dieselbe Rechnung, die `docker stats` anstellt, und nicht unsere eigene
    Erfindung. Ohne gesetztes Limit (memory.max = 'max') gibt es keinen ehrlichen
    Prozentsatz: dann bleibt prozent None und der Grund sagt warum."""
    aus = {"prozent": None, "genutzt_mb": None, "limit_mb": None,
           "cache_mb": None, "grund": None}
    try:
        roh = int(_text("/sys/fs/cgroup/memory.current").strip())
    except Exception:                                        # noqa: BLE001
        return _fehlt("nicht_lesbar", genutzt_mb=None, limit_mb=None, cache_mb=None)
    inaktiv = 0
    try:
        for z in _text("/sys/fs/cgroup/memory.stat").splitlines():
            if z.startswith("inactive_file "):
                inaktiv = int(z.split()[1])
                break
    except Exception:                                        # noqa: BLE001
        inaktiv = 0
    aus["genutzt_mb"] = int(max(0, roh - inaktiv) / 1024 ** 2)
    aus["cache_mb"] = int(inaktiv / 1024 ** 2)
    # Aufschluesselung (User-Beobachtung 25.08.: "wirklich viel RAM, was ich auf
    # diesem System belege"). Die Gesamtzahl allein fuehrt in die Irre — auf einer
    # Maschine mit integrierter Grafik steckt ein grosser Teil in shmem, weil die
    # iGPU keinen eigenen Speicher hat und System-RAM benutzt. Gemessen auf Prod:
    # 2,1 GB Prozesse gegen 3,5 GB Grafik. Wer das nicht weiss, sucht ein Leck,
    # wo keins ist.
    teile = {}
    try:
        for z in _text("/sys/fs/cgroup/memory.stat").splitlines():
            k, _, w = z.partition(" ")
            if k in ("anon", "shmem", "file"):
                teile[k] = int(w)
    except Exception:                                        # noqa: BLE001
        teile = {}
    if teile:
        # file enthaelt shmem mit; der reine Datei-Cache ist die Differenz.
        aus["prozesse_mb"] = int(teile.get("anon", 0) / 1024 ** 2)
        aus["grafik_mb"] = int(teile.get("shmem", 0) / 1024 ** 2)
        aus["dateicache_mb"] = int(max(0, teile.get("file", 0) - teile.get("shmem", 0)) / 1024 ** 2)
    try:
        w = _text("/sys/fs/cgroup/memory.max").strip()
        if w != "max":
            aus["limit_mb"] = int(int(w) / 1024 ** 2)
    except Exception:                                        # noqa: BLE001
        pass
    if aus["limit_mb"]:
        aus["prozent"] = round(aus["genutzt_mb"] * 100.0 / aus["limit_mb"], 1)
    else:
        aus["grund"] = "kein_limit"
    return aus


# ------------------------------------------------------------------ Platte
def platte_messen(data_dir, grenzen=None):
    """statvfs auf dem Datenverzeichnis. grenzen = das Tripel aus
    Service.speichergrenzen() (cache_max_gb, frei_min_gb, quelle) plus die
    aktuelle Cache-Groesse — der Dienst reicht es herein, damit die Seite
    dieselben WIRKSAMEN Grenzen zeigt wie die Platten-Wache und nicht ein
    zweites Mal rechnet."""
    aus = {"prozent": None, "gesamt_gb": None, "frei_gb": None, "genutzt_gb": None,
           "cache_gb": None, "cache_max_gb": None, "frei_min_gb": None,
           "grenz_quelle": None, "grund": None}
    try:
        s = os.statvfs(data_dir)
        gesamt = s.f_blocks * s.f_frsize
        frei = s.f_bavail * s.f_frsize
        if gesamt <= 0:
            return _fehlt("nicht_lesbar", **{k: None for k in aus if k not in ("prozent", "grund")})
        aus["gesamt_gb"] = round(gesamt / 1024 ** 3, 1)
        aus["frei_gb"] = round(frei / 1024 ** 3, 1)
        aus["genutzt_gb"] = round((gesamt - frei) / 1024 ** 3, 1)
        aus["prozent"] = round((gesamt - frei) * 100.0 / gesamt, 1)
    except Exception:                                        # noqa: BLE001
        return _fehlt("nicht_lesbar", **{k: None for k in aus if k not in ("prozent", "grund")})
    if grenzen:
        aus["cache_gb"] = grenzen.get("cache_gb")
        aus["cache_max_gb"] = grenzen.get("cache_max_gb")
        aus["frei_min_gb"] = grenzen.get("frei_min_gb")
        aus["grenz_quelle"] = grenzen.get("quelle")
    return aus


# ------------------------------------------------------------------ NPU
def npu_messen():
    """Intel-NPU: npu_busy_time_us ist ein monotoner µs-Zaehler, Auslastung =
    Δ/Δt. Erster Aufruf -> None."""
    treffer = sorted(glob.glob("/sys/bus/pci/devices/*/npu_busy_time_us"))
    if not treffer:
        return _fehlt("kein_geraet")
    try:
        us = int(_text(treffer[0]).strip())
    except Exception:                                        # noqa: BLE001
        return _fehlt("nicht_lesbar")
    jetzt = time.monotonic()
    with _LOCK:
        vorher = _STAND["npu"]
        _STAND["npu"] = (us, jetzt)
    if not vorher:
        return _fehlt("erster_lauf")
    d_us = us - vorher[0]
    d_t = jetzt - vorher[1]
    if d_t <= 0 or d_us < 0:              # Zaehler-Ruecksetzer / Uhr-Sprung
        return _fehlt("erster_lauf")
    return {"prozent": round(max(0.0, d_us / (d_t * 1_000_000) * 100.0), 1),
            "grund": None}


# ------------------------------------------------------------------ GPU-Sonden
# perf_event_open-Nummer x86_64/aarch64. Andere Architekturen: keine Nummer
# raten — dann bleibt die i915-Sonde aus (Grund werkzeug_fehlt).
_PERF_SYSCALL = {"x86_64": 298, "aarch64": 241}


def _i915_oeffnen():
    """i915-PMU-Zaehler oeffnen (einmalig, die fds bleiben offen).
    -> {engine: fd} oder {} mit gemerktem Grund in _STAND['i915'].

    GEMESSEN 25.08. im Prod-Container: perf_event_open liefert EPERM. Der
    Container hat kein CAP_PERFMON, perf_event_paranoid steht auf 4. Auf dieser
    Anlage ist die Intel-GPU-Auslastung damit NICHT messbar — die Kachel sagt
    das, statt eine Null zu zeigen. Der Weg bleibt trotzdem gebaut: auf einer
    Installation mit den noetigen Rechten liefert er echte Zahlen, und aus
    einer Maschine auf eine Regel zu schliessen waere geraten."""
    import ctypes
    import ctypes.util
    import errno
    import platform

    nr = _PERF_SYSCALL.get(platform.machine())
    if nr is None:
        _STAND["i915"] = {"grund": "werkzeug_fehlt"}
        return {}
    basis = "/sys/bus/event_source/devices/i915"
    try:
        typ = int(_text(os.path.join(basis, "type")).strip())
    except Exception:                                        # noqa: BLE001
        # kein_zaehler, NICHT kein_geraet (Widerleger-Fang 25.08.): hierher kommt
        # nur, wer den Geraeteknoten schon gefunden hat. Fehlt trotzdem die
        # i915-PMU, ist die GPU da und ihr Treiber fuehrt bloss keinen Zaehler —
        # der reale Fall ist der neuere Intel-Treiber 'xe' (Lunar Lake/Arc) und
        # jede andere DRM-Karte unter /dev/dri. "no such device on this machine"
        # waere dort schlicht falsch, und eine falsche Auskunft ist genau das,
        # was diese Seite nicht geben darf.
        _STAND["i915"] = {"grund": "kein_zaehler"}
        return {}

    class _Attr(ctypes.Structure):
        _fields_ = [("type", ctypes.c_uint32), ("size", ctypes.c_uint32),
                    ("config", ctypes.c_uint64), ("sample_period", ctypes.c_uint64),
                    ("sample_type", ctypes.c_uint64), ("read_format", ctypes.c_uint64),
                    ("flags", ctypes.c_uint64), ("wakeup_events", ctypes.c_uint32),
                    ("bp_type", ctypes.c_uint32), ("bp_addr", ctypes.c_uint64),
                    ("bp_len", ctypes.c_uint64), ("branch_sample_type", ctypes.c_uint64),
                    ("sample_regs_user", ctypes.c_uint64), ("sample_stack_user", ctypes.c_uint32),
                    ("clockid", ctypes.c_int32), ("sample_regs_intr", ctypes.c_uint64),
                    ("aux_watermark", ctypes.c_uint32), ("sample_max_stack", ctypes.c_uint16),
                    ("reserved_2", ctypes.c_uint16), ("aux_sample_size", ctypes.c_uint32),
                    ("reserved_3", ctypes.c_uint32)]

    libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)
    fds, letzter = {}, None
    for pfad in sorted(glob.glob(os.path.join(basis, "events", "*-busy"))):
        engine = os.path.basename(pfad)[:-len("-busy")]
        try:
            roh = _text(pfad).strip()                 # Form: "config=0x0"
            cfg = int(roh.split("=", 1)[1], 0)
        except Exception:                                    # noqa: BLE001
            continue
        a = _Attr()
        a.type, a.size, a.config = typ, ctypes.sizeof(_Attr), cfg
        # pid=-1 (systemweit), cpu=0: die i915-PMU ist an keine Aufgabe gebunden.
        fd = libc.syscall(nr, ctypes.byref(a), -1, 0, -1, 0)
        if fd < 0:
            letzter = ctypes.get_errno()
            continue
        fds[engine] = fd
    if not fds:
        _STAND["i915"] = {"grund": ("gesperrt" if letzter in (errno.EPERM, errno.EACCES)
                                    else "kein_zaehler" if letzter is None
                                    else "nicht_lesbar")}
    return fds


def eigener_gpu_anteil():
    """Wieviel Rechenzeit verbrauchen UNSERE Prozesse auf der Grafikeinheit?

    Weg ueber DRM-fdinfo: der Kernel fuehrt je offenem Geraete-Handle einen
    ns-Zaehler pro Engine (drm-engine-<name>). Zwei Messungen, Differenz durch
    verstrichene Zeit, fertig — ohne CAP_PERFMON und ohne perf_event_paranoid
    zu senken, an denen die SYSTEMWEITE Messung hier scheitert.

    ABGRENZUNG, die auf die Kachel gehoert: sichtbar sind nur die eigenen
    Prozesse. Das ist NICHT die Last der Maschine, sondern der eigene Anteil.
    Frigate zeigt uebrigens genau dasselbe (fdinfo, eigene Prozesse) — dessen
    Prozentzahl ist Frigates Anteil, nicht die Gesamtlast der Karte.

    -> {"prozent": <busiest engine>, "engines": {name: prozent}} oder Grund.
    """
    import glob
    import re as _re
    muster = _re.compile(r"drm-engine-(\S+):\s+(\d+) ns")

    def _lesen():
        summe, gefunden = {}, False
        for fd in glob.glob("/proc/*/fdinfo/*"):
            try:
                text = open(fd).read()
            except OSError:
                continue                      # Prozess weg oder fremder Namensraum
            if "drm-engine" not in text:
                continue
            gefunden = True
            for m in muster.finditer(text):
                summe[m.group(1)] = summe.get(m.group(1), 0) + int(m.group(2))
        return summe, gefunden

    jetzt = time.monotonic()
    stand, gefunden = _lesen()
    if not gefunden:
        return _fehlt("kein_zaehler")
    vorher = _STAND.get("gpu_eigen")
    _STAND["gpu_eigen"] = {"ts": jetzt, "werte": stand}
    if not vorher:
        return _fehlt("erster_lauf")
    dt = jetzt - vorher["ts"]
    if dt <= 0:
        return _fehlt("erster_lauf")
    engines = {}
    for name, wert in stand.items():
        d = wert - (vorher["werte"].get(name) or 0)
        if d < 0:                             # Prozess neu gestartet: Zaehler faengt bei 0 an
            continue
        engines[name] = round(d / (dt * 1e9) * 100, 1)
    if not engines:
        return _fehlt("erster_lauf")
    # Gemeldet wird die BUSIESTE Engine, nicht das Mittel: fuenf schlafende
    # Engines wuerden eine ausgelastete rechnerisch harmlos aussehen lassen.
    return {"prozent": max(engines.values()), "engines": engines}


def _sonde_openvino():
    """Intel: i915-PMU je Engine, gemeldet wird die BUSIESTE (das ist die
    Aussage 'wie ausgelastet ist die GPU'; ein Mittel ueber sechs Engines,
    von denen fuenf schlafen, waere Beschoenigung)."""
    global _I915_FDS
    if not _knoten_da(_pflicht_knoten("openvino")):
        return _fehlt("kein_geraet")
    if _I915_FDS is None:
        try:
            _I915_FDS = _i915_oeffnen()
        except Exception:                                    # noqa: BLE001
            _I915_FDS = {}
            _STAND["i915"] = {"grund": "nicht_lesbar"}
    if not _I915_FDS:
        return _fehlt((_STAND.get("i915") or {}).get("grund") or "kein_zaehler")
    import struct
    jetzt = time.monotonic()
    stand = {}
    for engine, fd in _I915_FDS.items():
        try:
            # KEIN lseek davor: laut perf_event_open(2) liefert jedes read()
            # auf einem perf-fd den aktuellen Zaehlerstand im read_format —
            # es gibt keine Dateiposition, die zurueckgesetzt werden muesste.
            # Ein lseek waere im besten Fall wirkungslos und im schlechteren
            # eine OSError, die diese Kachel dauerhaft auf "nicht lesbar"
            # stellte — ausgerechnet auf einer Anlage, wo sie ginge.
            # (Nicht hier gemessen: perf_event_open ist auf dieser Maschine
            # auch fuer Selbstmessung gesperrt, s. Kopfkommentar.)
            stand[engine] = struct.unpack("Q", os.read(fd, 8))[0]
        except Exception:                                    # noqa: BLE001
            pass
    if not stand:
        return _fehlt("nicht_lesbar")
    vorher = (_STAND.get("i915") or {}).get("stand")
    v_t = (_STAND.get("i915") or {}).get("t")
    _STAND["i915"] = {"stand": stand, "t": jetzt, "grund": None}
    if not vorher or not v_t:
        return _fehlt("erster_lauf")
    d_t_ns = (jetzt - v_t) * 1e9
    if d_t_ns <= 0:
        return _fehlt("erster_lauf")
    bester, wert = None, None
    for engine, ns in stand.items():
        if engine not in vorher:
            continue
        d = ns - vorher[engine]
        if d < 0:
            continue
        p = d / d_t_ns * 100.0
        if wert is None or p > wert:
            bester, wert = engine, p
    if wert is None:
        return _fehlt("erster_lauf")
    return {"prozent": round(max(0.0, wert), 1), "grund": None, "engine": bester}


def _sonde_cuda():
    """NVIDIA: nvidia-smi. Die Auslastung ist dort GESAMT (je Prozess liefert
    nvidia-smi nur Speicher, keine Rechenzeit — Bauplan §0)."""
    if not _knoten_da(_pflicht_knoten("cuda")):
        return _fehlt("kein_geraet")
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,"
             "temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=8)
    except FileNotFoundError:
        return _fehlt("werkzeug_fehlt")
    except Exception:                                        # noqa: BLE001
        return _fehlt("nicht_lesbar")
    zeile = (r.stdout or "").strip().splitlines()
    if r.returncode != 0 or not zeile:
        return _fehlt("nicht_lesbar")
    teile = [x.strip() for x in zeile[0].split(",")]
    try:
        return {"prozent": float(teile[0]), "grund": None,
                "speicher_mb": int(float(teile[1])),
                "speicher_max_mb": int(float(teile[2])),
                "temperatur_c": int(float(teile[3]))}
    except Exception:                                        # noqa: BLE001
        return _fehlt("nicht_lesbar")


def _sonde_migraphx():
    """AMD: rocm-smi. UNGEPRUEFT — auf dieser Anlage gibt es kein AMD-Geraet
    (Bauplan §2). Der Parser nimmt deshalb NUR eine Spalte an, deren Kopf
    ausdruecklich nach Auslastung in Prozent aussieht; passt das Format nicht,
    bleibt der Wert None. Lieber 'nicht verfuegbar' als eine geratene Zahl."""
    if not _knoten_da(_pflicht_knoten("migraphx")):
        return _fehlt("kein_geraet")
    try:
        r = subprocess.run(["rocm-smi", "--showuse", "--csv"],
                           capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        return _fehlt("werkzeug_fehlt")
    except Exception:                                        # noqa: BLE001
        return _fehlt("nicht_lesbar")
    zeilen = [z for z in (r.stdout or "").splitlines() if z.strip()]
    if r.returncode != 0 or len(zeilen) < 2:
        return _fehlt("nicht_lesbar")
    kopf = [x.strip().lower() for x in zeilen[0].split(",")]
    spalte = next((i for i, k in enumerate(kopf) if "use" in k and "%" in k), None)
    if spalte is None:
        return _fehlt("kein_zaehler")
    for z in zeilen[1:]:
        felder = [x.strip() for x in z.split(",")]
        if len(felder) <= spalte:
            continue
        try:
            return {"prozent": float(felder[spalte].rstrip("%")), "grund": None}
        except ValueError:
            continue
    return _fehlt("nicht_lesbar")


def _sonde_cpu():
    """kind 'cpu' hat definitionsgemaess keinen Beschleuniger. Der Eintrag
    existiert trotzdem, damit die Sonden-Tabelle die Registry LUECKENLOS deckt
    — ein kind ohne Sonde wuerde sonst stumm durchfallen."""
    return _fehlt("kein_geraet")


# DECKUNGS-VERTRAG: je Backend-kind der Registry genau eine Sonde. Das Gate
# prueft set(SONDEN) == set(registry.BACKENDS) — waechst die Registry um ein
# Backend, faellt es hier auf statt still zu fehlen (Projektregel: fachliche
# Aufzaehlungen kommen aus der zentralen Quelle oder tragen einen Vertrag).
SONDEN = {
    "cpu": _sonde_cpu,
    "openvino": _sonde_openvino,
    "cuda": _sonde_cuda,
    "migraphx": _sonde_migraphx,
}


def gpu_messen():
    """-> Block der GPU-Kachel. Reihenfolge: das erste kind, dessen Geraet hier
    liegt UND das eine Zahl liefert, gewinnt; liefert keins eine Zahl, gewinnt
    der Grund des ersten anwesenden Geraets. Ist gar kein Beschleuniger da,
    heisst der Grund kein_geraet."""
    lage = geraete_lage()
    erster = None
    for kind in sorted(lage):
        if not lage[kind]:                          # kein Geraeteknoten dieses kinds
            continue
        sonde = SONDEN.get(kind)
        if sonde is None:                           # vom Gate ausgeschlossen, defensiv
            continue
        try:
            d = sonde()
        except Exception:                                    # noqa: BLE001
            d = _fehlt("nicht_lesbar")
        d = dict(d, kind=kind)
        if d.get("prozent") is not None:
            return d
        if erster is None:
            erster = d
    return erster or _fehlt("kein_geraet", kind=None)


# ------------------------------------------------------------------ Erkennung
def durchsatz_messen(data_dir, jetzt=None):
    """Analysen je Stunde + mittlere Dauer aus der Akte state/deckung.jsonl.
    Gelesen wird nur das Ende der Datei (Deckel), nie der ganze Bestand.
    Es wandern AUSSCHLIESSLICH Zahlen in die Momentaufnahme — keine
    Personennamen, keine Event-IDs, keine Kameranamen."""
    jetzt = jetzt or time.time()
    p = os.path.join(data_dir, "state", "deckung.jsonl")
    aus = {"analysen_1h": 0, "analysen_24h": 0, "dauer_mittel_s": None,
           "grund": None}
    if not os.path.exists(p):
        # Frische Installation: die Akte entsteht mit der ersten Analyse. Null
        # Analysen ist hier die WAHRHEIT, kein Lesefehler — die beiden Faelle
        # duerfen sich nicht vermischen (sonst meldet jede Neuinstallation
        # einen Defekt, den es nicht gibt).
        return aus
    try:
        groesse = os.path.getsize(p)
        with open(p, "rb") as f:
            if groesse > LESE_DECKEL_B:
                f.seek(groesse - LESE_DECKEL_B)
                f.readline()                        # angeschnittene Zeile verwerfen
            roh = f.read().decode("utf-8", "replace")
    except Exception:                                        # noqa: BLE001
        return {"analysen_1h": None, "analysen_24h": None,
                "dauer_mittel_s": None, "grund": "nicht_lesbar"}
    dauern = []
    for z in roh.splitlines():
        try:
            d = json.loads(z)
        except Exception:                                    # noqa: BLE001
            continue
        ts = float(d.get("ts") or 0)
        if ts < jetzt - 86400:
            continue
        aus["analysen_24h"] += 1
        if ts >= jetzt - 3600:
            aus["analysen_1h"] += 1
        s = d.get("dauer_s")
        if isinstance(s, (int, float)) and s > 0:
            dauern.append(float(s))
    if dauern:
        aus["dauer_mittel_s"] = round(sum(dauern) / len(dauern), 1)
    return aus


# ------------------------------------------------------------------ Momentaufnahme
def momentaufnahme(cfg, dienst=None):
    """DIE Momentaufnahme. Jede Quelle einzeln in try/except: eine fehlende darf
    die anderen nie verschlucken (dieselbe Lehre wie beim Nachtjob-Rahmen).

    dienst: optionales dict mit dem, was NUR der laufende Dienst weiss —
    {"platte": {...}, "worker": {...}, "rueckstau": {...}, "live": {...}}.
    Fehlt es (Aufruf ohne Dienst, z. B. im Gate), tragen diese Bloecke den
    Grund kein_dienst und behaupten nichts."""
    dienst = dienst or {}
    dd = (cfg or {}).get("data_dir") or ""
    snap = {"ts": round(time.time(), 3)}
    for name, fn in (
            ("cpu", cpu_messen),
            ("ram", ram_messen),
            ("platte", lambda: platte_messen(dd, dienst.get("platte"))),
            ("gpu", gpu_messen),
            # .341b (User-Einwand 25.08.: Frigate zeige die GPU an, wir nicht):
            # der EIGENE Anteil ueber DRM-fdinfo. Er braucht keine Sonderrechte
            # und traegt deshalb dort, wo die systemweite Messung gesperrt ist.
            # Frigate misst genau denselben Weg — dessen Prozentzahl ist auch
            # nur Frigates eigener Anteil, nicht die Last der Karte.
            ("gpu_eigen", eigener_gpu_anteil),
            ("npu", npu_messen),
            ("durchsatz", lambda: durchsatz_messen(dd))):
        try:
            snap[name] = fn()
        except Exception as e:                               # noqa: BLE001
            snap[name] = _fehlt("nicht_lesbar", fehler=type(e).__name__)
    for name in ("worker", "rueckstau", "live"):
        snap[name] = dienst.get(name) or {"grund": "kein_dienst"}
    with _LOCK:
        _STAND["snap"] = snap
    return snap


def letzte():
    """Die zuletzt GESCHRIEBENE Momentaufnahme — der Leseweg fuer /health.

    Bewusst kein frisches Messen: die Delta-Zaehler (CPU, NPU, i915) haben je
    genau EINEN Vorstand. Wuerde /health nebenher messen, klaute jeder Abruf
    dem 60-s-Sammler seine Bezugsgroesse und beide bekaemen Unsinn. EIN
    Messer, ein Datenweg (Bauplan §3.4)."""
    with _LOCK:
        return _STAND["snap"]


# ------------------------------------------------------------------ Ringpuffer
def ring_pfad(cfg):
    return os.path.join((cfg or {}).get("data_dir") or "", *RING_TEILE)


def _schlank(snap):
    """Die Fassung fuer den Ringpuffer: OHNE die Kern-Einzelwerte.

    Gemessen 25.08. auf einer 16-Kern-Maschine: mit der Kern-Liste 1093 Bytes je
    Zeile statt der im Bauplan geschaetzten ~300 — auf einer 64-Kern-Maschine
    waere die Zeile das Vierfache. Gelesen wird die Liste aus der Datei nie: die
    Kern-Balken zeigen ausschliesslich die AKTUELLE Messung, und die kommt aus
    dem Prozessgedaechtnis (letzte()). 48 h Kern-Historie zu speichern, die
    niemand ansieht, waere genau die Sorte Datei, die dieser Release sonst
    aufraeumt. Die Gesamt-CPU und die Kernzahl bleiben drin."""
    if not isinstance(snap.get("cpu"), dict) or "kerne" not in snap["cpu"]:
        return snap
    schlank = dict(snap)
    schlank["cpu"] = {k: v for k, v in snap["cpu"].items() if k != "kerne"}
    return schlank


def schreiben(cfg, snap):
    """Eine Zeile anhaengen. Fehler sind leise — ein voller Datentraeger darf den
    Dienst nicht stoeren, und die Platten-Wache meldet ihn ohnehin."""
    p = ring_pfad(cfg)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(_schlank(snap), ensure_ascii=False) + "\n")
        return True
    except Exception:                                        # noqa: BLE001
        return False


def lesen(cfg, seit_ts=None):
    """-> Liste der Momentaufnahmen ab seit_ts (aelteste zuerst). Liest nur das
    Ende der Datei; eine kaputte Zeile wird uebersprungen, nie geraten."""
    p = ring_pfad(cfg)
    try:
        groesse = os.path.getsize(p)
        with open(p, "rb") as f:
            if groesse > LESE_DECKEL_B:
                f.seek(groesse - LESE_DECKEL_B)
                f.readline()
            roh = f.read().decode("utf-8", "replace")
    except Exception:                                        # noqa: BLE001
        return []
    aus = []
    for z in roh.splitlines():
        try:
            d = json.loads(z)
        except Exception:                                    # noqa: BLE001
            continue
        if seit_ts and float(d.get("ts") or 0) < seit_ts:
            continue
        aus.append(d)
    return aus


def kuerzen(cfg, stunden=AUFBEWAHRUNG_H):
    """Ringpuffer auf die Aufbewahrung stutzen. EINZIGER Aufrufer ist der
    Nachtjob (Service.alt_aufraeumen) — kein zweiter Aufraeum-Ort.
    -> (behalten, verworfen) oder (0, 0), wenn es nichts zu tun gab."""
    p = ring_pfad(cfg)
    if not os.path.exists(p):
        return (0, 0)
    grenze = time.time() - stunden * 3600
    behalten, weg = [], 0
    with open(p, encoding="utf-8", errors="replace") as f:
        for z in f:
            try:
                if float(json.loads(z).get("ts") or 0) >= grenze:
                    behalten.append(z)
                else:
                    weg += 1
            except Exception:                                # noqa: BLE001
                weg += 1                       # unlesbare Zeile faellt mit heraus
    if not weg:
        return (len(behalten), 0)
    tmp = p + ".neu"
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(behalten)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)
    return (len(behalten), weg)


def sammler_starten(cfg, dienst_fn=None, log=None):
    """Schreib-Thread: alle TAKT_S Sekunden eine Zeile.

    Der Puffer wird beim Start NICHT geleert — ein Neustart soll die Kurve nicht
    abschneiden (Bauplan §3.2). Die erste Runde laeuft sofort und setzt nur die
    Bezugsgroessen der Delta-Zaehler; ihre Werte sind ehrlich None."""
    melde = log or (lambda m: None)

    def lauf():
        while True:
            try:
                snap = momentaufnahme(cfg, dienst_fn() if dienst_fn else None)
                schreiben(cfg, snap)
            except Exception as e:                           # noqa: BLE001
                melde(f"systemstat sampler: {type(e).__name__}: {e}")
            time.sleep(TAKT_S)

    threading.Thread(target=lauf, daemon=True).start()
