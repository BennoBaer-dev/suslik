"""Support-Dateiprobe: trennt eine langsame Ablage von einem langsamen Dienstprozess.

HERKUNFT: Bauplan analysen/bauplan_support_dateiprobe.md, Stufe D1, Entscheide 1 bis 5 (Eigentuemer 14.10.2026
14:54:08 „ok zu Fassung 1"). Anlass war ein Feldtester, bei dem jede Dateiarbeit je Ereignis unter Last langsam
wurde und Neustarts nur kurz halfen; was die Support-Schnittstelle bis dahin mass, lief im Dienstprozess selbst.

ZWECK: dieselben fuenf kleinen Dateioperationen (Config lesen, eigene Temp-Datei schreiben, clips/ auflisten,
freien Platz lesen, Config nur oeffnen) laufen je dreimal im Dienstprozess und einmal je dreimal in einem frisch
gestarteten Kindprozess; dazu die NFS-Zaehler des Datenordners aus /proc/self/mountstats, der freie Platz und der
Block `system` (Last, Druck, Prozesse im Container, Bauplan analysen/bauplan_startlesung.md Stufe S2b). Gerufen wird
`lauf(data_dir)` vom Endpunkt POST /support/dateiprobe in verifyd.py; der Kindweg ist `__main__` dieses Moduls.
Die Probe gibt keinen Dateiinhalt zurueck, nur Zahlen. Sie schreibt genau eine Datei (TEMP_TEIL) und entfernt
sie wieder; bleibt sie liegen, sagt die Antwort das. Daneben `nfs_abschnitt`: die NFS-Zaehler vor und nach einer
Lesung des Starts als eine DEBUG-Zeile (Stufe S2b Punkt 4), ohne Bezug zum Endpunkt.

EHRLICHE GRENZEN: eine einzelne Dateioperation, die im Kernel haengt, laesst sich im Dienstprozess nicht
abbrechen; die Frist greift zwischen den Operationen. Der Kindprozess laeuft im selben Container und Kernel:
er trennt Prozesszustand von Ablage, nicht Container von Wirt. Der Container sieht in /proc/self/mountstats
die NFS-Zaehler seines eigenen Mounts; belegt am 03.11.2026 an einer Feldinstallation, deren Dateiprobe den
Mount als nfs4 mit Zaehlern meldete. Sieht er sie nicht, sagt der Mount-Block „kein NFS" mit Grund. Die Zeile von
`nfs_abschnitt` zaehlt alles auf dem Mount in dieser Zeit, auch was andere Faeden und Prozesse tun.
"""
import contextlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import time

from core import logbuch as _logbuch
from core import registry as _registry
from core.pfade import WURZEL

_log = _logbuch.logger(__name__)

DURCHLAEUFE = 3                 # Bauplan Entscheid 2: „dreimal nacheinander"
DIENST_FRIST_S = 30             # Bauplan Entscheid 4: Frist der Dienst-Messung, die Probe endet nach T plus diese
CONFIG_TEIL = ("config", "config.json")
TEMP_TEIL = ("state", "dateiprobe.tmp")
CLIPS_TEIL = ("clips",)
OPERATIONEN = ("config_lesen", "temp_schreiben", "clips_listen", "platz_lesen", "config_oeffnen")
MOUNTINFO = "/proc/self/mountinfo"
MOUNTSTATS = "/proc/self/mountstats"
PROC = "/proc"                  # Wurzel des Blocks `system` (Bauplan analysen/bauplan_startlesung.md S2b Punkt 2c)
# Zeilenformate nach der Kernel-Quelle (torvalds/linux, gelesen 14.10.2026): net/sunrpc/stats.c
# _print_rpc_iostats, net/sunrpc/xprtsock.c xs_tcp_print_stats/xs_udp_print_stats,
# include/linux/nfs_iostat.h (Reihenfolge der Ereigniszaehler).
OP_FELDER = ("ops", "trans", "timeouts", "bytes_sent", "bytes_recv", "queue_ms", "rtt_ms", "execute_ms",
             "errors")
XPRT_FELDER = {
    "tcp": ("srcport", "bind_count", "connect_count", "connect_time_s", "idle_time_s", "sends", "recvs",
            "bad_xids", "req_u", "bklog_u", "max_slots", "sending_u", "pending_u"),
    "udp": ("srcport", "bind_count", "sends", "recvs", "bad_xids", "req_u", "bklog_u", "max_slots",
            "sending_u", "pending_u"),
}
EREIGNIS_NAMEN = ("inoderevalidate", "dentryrevalidate", "datainvalidate", "attrinvalidate", "vfsopen",
                  "vfslookup", "vfsaccess", "vfsupdatepage", "vfsreadpage", "vfsreadpages", "vfswritepage",
                  "vfswritepages", "vfsgetdents", "vfssetattr", "vfsflush", "vfsfsync", "vfslock",
                  "vfsrelease", "congestionwait", "setattrtrunc", "extendwrite", "sillyrename", "shortread",
                  "shortwrite", "delay", "pnfs_read", "pnfs_write")


def _groessen():
    """Die drei Groessen der Probe aus der Registry (eine Stelle).
    -> (anhang_bytes, eintraege, kind_deckel_s)."""
    g = _registry.SUPPORT_DATEIPROBE
    return int(g["anhang_bytes"]), int(g["eintraege"]), float(g["kind_deckel_s"])


def _ms_seit(t0):
    """Vergangene Zeit seit `t0` (monotonic) in Millisekunden.
    -> float."""
    return (time.monotonic() - t0) * 1000.0


def _config_lesen(data_dir):
    """Config-Store oeffnen, ganz lesen, schliessen; der Inhalt bleibt hier.
    -> (dauer_ms, bytes)."""
    t0 = time.monotonic()
    with open(os.path.join(data_dir, *CONFIG_TEIL), "rb") as f:
        n = len(f.read())
    return _ms_seit(t0), n


def _config_oeffnen(data_dir):
    """Den Config-Store oeffnen und wieder schliessen; gemessen wird nur das Oeffnen (Bauplan
    analysen/bauplan_startlesung.md S2b Punkt 2b: trennt das Oeffnen vom Lesen).
    -> (dauer_ms, None)."""
    t0 = time.monotonic()
    fd = os.open(os.path.join(data_dir, *CONFIG_TEIL), os.O_RDONLY)
    dauer = _ms_seit(t0)
    os.close(fd)
    return dauer, None


def _temp_schreiben(pfad, anhang_bytes):
    """Die Temp-Datei anlegen, `anhang_bytes` anhaengen, fsync, schliessen.
    -> dauer_ms."""
    daten = b"\0" * anhang_bytes
    t0 = time.monotonic()
    fd = os.open(pfad, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    try:
        os.write(fd, daten)
        os.fsync(fd)
    finally:
        os.close(fd)
    return _ms_seit(t0)


def _clips_listen(data_dir, eintraege, frist):
    """clips/ per scandir lesen, stat je Eintrag, nach `eintraege` Eintraegen oder an der Frist abbrechen.
    -> (dauer_ms je Eintrag oder None ohne Eintrag, gezaehlte Eintraege)."""
    n = 0
    t0 = time.monotonic()
    with os.scandir(os.path.join(data_dir, *CLIPS_TEIL)) as it:
        for e in it:
            e.stat(follow_symlinks=False)
            n += 1
            if n >= eintraege or time.monotonic() > frist:
                break
    dauer = _ms_seit(t0)
    return (dauer / n if n else None), n


def _platz_lesen(data_dir):
    """shutil.disk_usage des Datenordners und des Wurzelverzeichnisses.
    -> (dauer_ms, {"data_dir": {...}, "wurzel": {...}})."""
    t0 = time.monotonic()
    d, w = shutil.disk_usage(data_dir), shutil.disk_usage("/")
    dauer = _ms_seit(t0)
    return dauer, {k: {"gesamt_bytes": u.total, "belegt_bytes": u.used, "frei_bytes": u.free}
                   for k, u in (("data_dir", d), ("wurzel", w))}


def _zusammenfassen(werte):
    """Minimum und Median einer Messreihe in Millisekunden.
    -> {"min_ms", "median_ms", "n"} (Werte None ohne Messung)."""
    w = [x for x in werte if x is not None]
    if not w:
        return {"min_ms": None, "median_ms": None, "n": 0}
    return {"min_ms": round(min(w), 3), "median_ms": round(statistics.median(w), 3), "n": len(w)}


def _ein_durchlauf(data_dir, temp, reihen, extra, frist):
    """Die fuenf Operationen einmal; je Operation ein Messwert oder ein Fehlertext.
    -> True, wenn die Frist vorher abgelaufen war (dann nichts gemessen)."""
    anhang, eintraege, _deckel = _groessen()
    schritte = (
        ("config_lesen", lambda: _config_lesen(data_dir)),
        ("temp_schreiben", lambda: (_temp_schreiben(temp, anhang), anhang)),
        ("clips_listen", lambda: _clips_listen(data_dir, eintraege, frist)),
        ("platz_lesen", lambda: _platz_lesen(data_dir)),
        ("config_oeffnen", lambda: _config_oeffnen(data_dir)),
    )
    for op, fn in schritte:
        if time.monotonic() > frist:
            return True
        try:
            dauer, zusatz = fn()
        except OSError as e:
            extra[op]["fehler"] = f"{type(e).__name__}: {e.strerror or e}"
            continue
        reihen[op].append(dauer)
        extra[op]["wert"] = zusatz
    return False


def messen(data_dir, frist_s):
    """Die fuenf Messungen (Entscheid 2, Bauplan analysen/bauplan_startlesung.md S2b), DURCHLAEUFE-mal, mit Frist
    `frist_s` zwischen den Operationen.
    -> Block {pid, durchlaeufe, <operation>: {min_ms, median_ms, n, ...}, platz, [fehler], [temp_liegt]}."""
    frist = time.monotonic() + float(frist_s)
    temp = os.path.join(data_dir, *TEMP_TEIL)
    reihen = {op: [] for op in OPERATIONEN}
    extra = {op: {} for op in OPERATIONEN}
    block = {"pid": os.getpid(), "durchlaeufe": 0}
    try:
        for _ in range(DURCHLAEUFE):
            if _ein_durchlauf(data_dir, temp, reihen, extra, frist):
                block["fehler"] = "frist"
                break
            block["durchlaeufe"] += 1
    finally:
        try:
            os.remove(temp)
        except FileNotFoundError:
            pass
        except OSError as e:
            block["temp_liegt"] = os.path.join(*TEMP_TEIL)
            _log.error(f"SUPPORT: dateiprobe could not remove its temp file "
                       f"{os.path.join(*TEMP_TEIL)} — {type(e).__name__}: {e.strerror or e}")
    for op in OPERATIONEN:
        block[op] = _zusammenfassen(reihen[op])
        if "fehler" in extra[op]:
            block[op]["fehler"] = extra[op]["fehler"]
    if "wert" in extra["config_lesen"]:
        block["config_lesen"]["bytes"] = extra["config_lesen"]["wert"]
    if "wert" in extra["temp_schreiben"]:
        block["temp_schreiben"]["bytes"] = extra["temp_schreiben"]["wert"]
    block["clips_listen"]["einheit"] = "ms je Eintrag"
    block["clips_listen"]["eintraege"] = extra["clips_listen"].get("wert", 0)
    block["platz"] = extra["platz_lesen"].get("wert")
    return block


def kind_argv(data_dir):
    """Die Kommandozeile des Kindprozesses nach Bauplan Entscheid 2 (berichtigt 14.10.2026): `-E -s` statt `-I`,
    weil `-I` seit Python 3.11 `-P` einschliesst und das Paket `core` dann nicht findet; Arbeitsverzeichnis ist der
    Programmordner (`cwd=WURZEL` in `kind_messen`).
    -> Liste fuer subprocess."""
    return [sys.executable, "-E", "-s", "-m", "core.dateiprobe", data_dir]


def kind_messen(data_dir, deckel_s):
    """Dieselben Messungen in einem frisch gestarteten Kindprozess, gedeckelt auf `deckel_s` Sekunden.
    -> Block wie `messen` plus start_bis_ende_ms, oder {"fehler": ...} (Deckel, Rueckgabewert, kein JSON)."""
    t0 = time.monotonic()
    try:
        r = subprocess.run(kind_argv(data_dir), cwd=WURZEL, env=dict(os.environ), stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=float(deckel_s))
    except subprocess.TimeoutExpired:
        return {"fehler": "deckel", "deckel_s": deckel_s, "start_bis_ende_ms": round(_ms_seit(t0), 3)}
    except OSError as e:
        return {"fehler": f"start: {type(e).__name__}: {e.strerror or e}"}
    dauer = round(_ms_seit(t0), 3)
    if r.returncode != 0:
        letzte = (r.stderr or "").strip().splitlines()[-1:] or [""]
        return {"fehler": f"rc {r.returncode}", "stderr": letzte[0][-300:], "start_bis_ende_ms": dauer}
    try:
        block = json.loads(r.stdout)
    except ValueError:
        return {"fehler": "keine JSON-Antwort", "start_bis_ende_ms": dauer}
    if not isinstance(block, dict):
        return {"fehler": "keine JSON-Antwort", "start_bis_ende_ms": dauer}
    block["start_bis_ende_ms"] = dauer
    return block


def _entmaskieren(feld):
    """Oktal-Maskierung des Kernels in Pfaden aufloesen (\\040 fuer Leerzeichen usw.).
    -> str."""
    teile = feld.split("\\")
    aus = [teile[0]]
    for t in teile[1:]:
        if len(t) >= 3 and all(c in "01234567" for c in t[:3]):
            aus.append(chr(int(t[:3], 8)) + t[3:])
        else:
            aus.append("\\" + t)
    return "".join(aus)


def mountpunkt_finden(pfad, mountinfo_text):
    """Den laengsten Mountpunkt aus mountinfo, unter dem `pfad` liegt.
    -> {"mountpunkt", "fstype", "quelle"} oder None."""
    best = None
    for zeile in mountinfo_text.splitlines():
        teile = zeile.split(" - ", 1)
        links = teile[0].split()
        if len(teile) != 2 or len(links) < 5:
            continue
        mp = _entmaskieren(links[4])
        rechts = teile[1].split()
        drin = pfad == mp or mp == "/" or pfad.startswith(mp.rstrip("/") + "/")
        if drin and (best is None or len(mp) >= len(best["mountpunkt"])):
            best = {"mountpunkt": mp, "fstype": rechts[0] if rechts else "",
                    "quelle": rechts[1] if len(rechts) > 1 else ""}
    return best


def _zahlen(text):
    """Leerzeichen-getrennte ganze Zahlen; Unlesbares faellt heraus.
    -> Liste int."""
    return [int(x) for x in text.split() if x.lstrip("-").isdigit()]


def _op_zeile(werte):
    """Eine per-op-Zeile benennen und die Mittel je Operation rechnen.
    -> dict."""
    d = dict(zip(OP_FELDER, werte))
    ops = d.get("ops") or 0
    for k in ("queue_ms", "rtt_ms", "execute_ms"):
        d[k.replace("_ms", "_mittel_ms")] = round(d[k] / ops, 3) if ops and k in d else None
    return d


def _block_finden(text, mountpunkt):
    """Die Zeilen des mountstats-Blocks zu `mountpunkt` (Kopfzeile zuerst).
    -> Liste der Zeilen oder None."""
    zeilen, drin = [], False
    for z in text.splitlines():
        if z.startswith("device "):
            if drin:
                break
            kopf = z.split(" mounted on ", 1)
            if len(kopf) == 2 and _entmaskieren(kopf[1].split(" with fstype ", 1)[0]) == mountpunkt:
                drin = True
        if drin:
            zeilen.append(z)
    return zeilen or None


def mountstats_lesen(text, mountpunkt):
    """Den mountstats-Block eines Mountpunkts lesen (Text als Argument, damit eine Probe ihn pruefen kann); `ops` traegt
    jede Anfrageart mit mindestens einem Aufruf (Bauplan analysen/bauplan_startlesung.md S2b Punkt 2a).
    -> {"nfs": True, fstype, alter_s, ops, xprt, ereignisse, ...} oder {"nfs": False, "grund"}."""
    zeilen = _block_finden(text, mountpunkt)
    if not zeilen:
        return {"nfs": False, "grund": f"no mountstats entry for {mountpunkt}"}
    fstype = zeilen[0].split(" with fstype ", 1)[-1].split()[0] if " with fstype " in zeilen[0] else ""
    if not fstype.startswith("nfs"):
        return {"nfs": False, "grund": f"filesystem type {fstype or 'unknown'}", "fstype": fstype}
    aus = {"nfs": True, "mountpunkt": mountpunkt, "fstype": fstype, "alter_s": None, "ops": {},
           "xprt": None, "ereignisse": None}
    per_op = False
    for z in zeilen[1:]:
        s = z.strip()
        if s.startswith("age:"):
            werte = _zahlen(s[4:])
            aus["alter_s"] = werte[0] if werte else None
        elif s.startswith("events:"):
            werte = _zahlen(s[7:])
            aus["ereignisse"] = dict(zip(EREIGNIS_NAMEN, werte))
            aus["ereignisse_roh"] = werte
        elif s.startswith("xprt:"):
            teile = s[5:].split()
            proto = teile[0] if teile else ""
            werte = _zahlen(" ".join(teile[1:]))
            aus["xprt"] = {"protokoll": proto, "roh": werte}
            aus["xprt"].update(dict(zip(XPRT_FELDER.get(proto, ()), werte)))
        elif s.startswith("per-op statistics"):
            per_op = True
        elif per_op and ":" in s:
            name, rest = s.split(":", 1)
            werte = _zahlen(rest)
            if werte and werte[0] >= 1:
                aus["ops"][name] = _op_zeile(werte)
    return aus


def _lesen(pfad):
    """Eine /proc-Datei als Text lesen.
    -> (text, None) oder (None, Grund)."""
    try:
        with open(pfad, encoding="utf-8", errors="replace") as f:
            return f.read(), None
    except OSError as e:
        return None, f"{pfad} not readable ({type(e).__name__})"


def mount_lesen(data_dir):
    """Mount des Datenordners finden und dessen NFS-Zaehler lesen (Bauplan Entscheid 3).
    -> Mount-Block; kein NFS ist {"nfs": False, "grund": ...}, nie ein Fehler."""
    real = os.path.realpath(data_dir)
    info, grund = _lesen(MOUNTINFO)
    if info is None:
        return {"nfs": False, "grund": grund}
    mp = mountpunkt_finden(real, info)
    if mp is None:
        return {"nfs": False, "grund": f"no mount found for {real}"}
    if not mp["fstype"].startswith("nfs"):
        return {"nfs": False, "grund": f"filesystem type {mp['fstype']}", **mp}
    stats, grund = _lesen(MOUNTSTATS)
    if stats is None:
        return {"nfs": False, "grund": grund, **mp}
    aus = mountstats_lesen(stats, mp["mountpunkt"])
    aus.setdefault("quelle", mp["quelle"])
    return aus


def _nfs_stand(data_dir):
    """Der Stand der NFS-Zaehler des Datenordners fuer `nfs_abschnitt`, nur bei aktivem DEBUG (sonst kein Zugriff auf /proc);
    ein Fehler kostet nur die Zeile.
    -> Mount-Block oder None (kein DEBUG, kein NFS oder Fehler)."""
    if not _log.isEnabledFor(_logbuch.DEBUG):
        return None
    try:
        stand = mount_lesen(data_dir)
    except Exception:                                   # noqa: BLE001  ein Fehler kostet nur die Zeile (Bauplan S2b Punkt 4)
        _logbuch.swallowed(_log, _logbuch.DEBUG, "no nfs counter line")
        return None
    return stand if stand.get("nfs") else None


def _nfs_zeile(name, dauer_s, vorher, nachher):
    """Die Zeile aus zwei Zaehlerstaenden: Dauer, sends je Sekunde, je Anfrageart mit Aufrufen in der Zeit Zahl, mittlere
    Rundreise und Ausfuehrungszeit, die meisten Aufrufe zuerst.
    -> str."""
    s0, s1 = (vorher.get("xprt") or {}).get("sends"), (nachher.get("xprt") or {}).get("sends")
    sends = f"{(s1 - s0) / dauer_s:.1f}/s" if s0 is not None and s1 is not None else "unknown"
    arten = []
    for op, z in nachher["ops"].items():
        alt = vorher["ops"].get(op) or {}
        n = z["ops"] - alt.get("ops", 0)
        if n > 0:
            arten.append((n, op, (z["rtt_ms"] - alt.get("rtt_ms", 0)) / n, (z["execute_ms"] - alt.get("execute_ms", 0)) / n))
    teile = [f"{op} {n} calls rtt {rtt:.2f} ms execute {aus:.2f} ms"
             for n, op, rtt, aus in sorted(arten, key=lambda a: (-a[0], a[1]))]
    return f"nfs counters for {name}: {dauer_s:.1f} s, sends {sends}; {'; '.join(teile) or 'no requests'}"


@contextlib.contextmanager
def nfs_abschnitt(data_dir, name):
    """Um einen Abschnitt herum die NFS-Zaehler lesen und eine DEBUG-Zeile schreiben (Bauplan analysen/bauplan_startlesung.md
    S2b Punkt 4); ohne DEBUG oder ohne NFS tut sie nichts, ein Fehler kostet nur die Zeile, nie den Abschnitt.
    -> Kontextmanager ohne Wert; ein Fehler des Abschnitts selbst geht unveraendert weiter."""
    vorher = _nfs_stand(data_dir)
    t0 = time.monotonic()
    try:
        yield
    finally:
        if vorher is not None:
            nachher = _nfs_stand(data_dir)
            if nachher is not None:
                try:
                    _log.debug(_nfs_zeile(name, time.monotonic() - t0, vorher, nachher))
                except Exception:                       # noqa: BLE001  ein Fehler kostet nur die Zeile (Bauplan S2b Punkt 4)
                    _logbuch.swallowed(_log, _logbuch.DEBUG, "no nfs counter line")


def _aus_proc(teil, auswerten):
    """Eine Datei unter PROC lesen und auswerten; fehlt sie oder ist sie nicht lesbar, steht ihr Grund im Ergebnis.
    -> Ergebnis von `auswerten` oder {"grund": ...}."""
    pfad = os.path.join(PROC, *teil)
    text, grund = _lesen(pfad)
    if text is None:
        return {"grund": grund}
    try:
        return auswerten(text)
    except (ValueError, IndexError, KeyError) as e:
        return {"grund": f"{pfad} not parsable ({type(e).__name__})"}


def _loadavg(text):
    """Inhalt von /proc/loadavg.
    -> {"avg1", "avg5", "avg15", "laufend_von_gesamt"}."""
    t = text.split()
    return {"avg1": float(t[0]), "avg5": float(t[1]), "avg15": float(t[2]), "laufend_von_gesamt": t[3]}


def _stat(text):
    """Die zwei Prozesszahlen aus /proc/stat.
    -> {"procs_running", "procs_blocked"}; fehlt eine: KeyError."""
    werte = dict(z.split()[:2] for z in text.splitlines() if z.startswith("procs_"))
    return {k: int(werte[k]) for k in ("procs_running", "procs_blocked")}


def _pressure(text):
    """Inhalt einer Datei unter /proc/pressure.
    -> {"some": {avg10, avg60, avg300, total}, "full": {...}}; was der Kernel nennt."""
    aus = {}
    for z in text.splitlines():
        art, *felder = z.split()
        aus[art] = {k: (int(v) if k == "total" else float(v)) for k, v in (f.split("=", 1) for f in felder)}
    if not aus:
        raise ValueError("empty")
    return aus


def _prozess_zeile(pid):
    """Eine Zeile der Prozessliste aus /proc/<pid>/stat, nur comm, Zustand, Zahl der Faeden und CPU-Ticks (utime plus
    stime); Kommandozeile und Umgebung werden nie gelesen. Das Feldformat steht in proc_pid_stat(5).
    -> dict; {"grund": ...} bei nicht auswertbarer Zeile; None, wenn der Prozess schon weg ist."""
    pfad = os.path.join(PROC, pid, "stat")
    text, _grund = _lesen(pfad)
    if text is None:
        return None
    vorn, _klammer, hinten = text.rpartition(")")     # comm darf Klammern und Leerzeichen tragen, die letzte zaehlt
    felder = hinten.split()
    try:
        return {"comm": vorn.partition("(")[2], "zustand": felder[0], "faeden": int(felder[17]),
                "cpu_ticks": int(felder[11]) + int(felder[12])}
    except (ValueError, IndexError) as e:
        return {"grund": f"{pfad} not parsable ({type(e).__name__})"}


def _prozesse():
    """Die Prozessliste des Containers.
    -> Liste der Zeilen oder {"grund": ...}."""
    try:
        namen = os.listdir(PROC)
    except OSError as e:
        return {"grund": f"{PROC} not readable ({type(e).__name__})"}
    zeilen = (_prozess_zeile(n) for n in sorted(namen) if n.isdigit())
    return [z for z in zeilen if z is not None]


def system_lesen():
    """Der Block `system` der Probe: Last, Prozesszahlen, Druck und die Prozesse im Container (Bauplan
    analysen/bauplan_startlesung.md S2b Punkt 2c); fehlt eine Quelle, steht dort ihr Grund, `ok` bleibt davon unberuehrt.
    -> {"loadavg", "stat", "pressure_io", "pressure_cpu", "prozesse"}."""
    return {"loadavg": _aus_proc(("loadavg",), _loadavg), "stat": _aus_proc(("stat",), _stat),
            "pressure_io": _aus_proc(("pressure", "io"), _pressure),
            "pressure_cpu": _aus_proc(("pressure", "cpu"), _pressure), "prozesse": _prozesse()}


def faktor(dienst, kind):
    """Faktor Dienst zu Kind je Operation aus den Medianen.
    -> {operation: float oder None}."""
    aus = {}
    for op in OPERATIONEN:
        d = (dienst.get(op) or {}).get("median_ms")
        k = (kind.get(op) or {}).get("median_ms")
        aus[op] = round(d / k, 3) if d is not None and k else None
    return aus


def _medianen(block):
    """Die Mediane eines Blocks als kurzer Logtext.
    -> str."""
    if "fehler" in block and not any(op in block for op in OPERATIONEN):
        return f"failed ({block['fehler']})"
    return " / ".join(f"{op} {(block.get(op) or {}).get('median_ms')}" for op in OPERATIONEN)


def lauf(data_dir):
    """Die ganze Probe: Dienst-Messung, Kind-Messung, Faktor, Mount, Platz (Bauplan Entscheid 4), System (Bauplan
    analysen/bauplan_startlesung.md S2b).
    -> Antwort {"ok", "ts", "dauer_s", "dienst", "kind", "faktor", "mount", "platz", "system"}."""
    t0 = time.monotonic()
    _anhang, _eintraege, deckel_s = _groessen()
    dienst = messen(data_dir, DIENST_FRIST_S)
    kind = kind_messen(data_dir, deckel_s)
    platz = dienst.pop("platz", None)
    kind.pop("platz", None)
    mount = mount_lesen(data_dir)
    system = system_lesen()
    ok = not any(k in b for b in (dienst, kind) for k in ("fehler", "temp_liegt"))
    ok = ok and not any("fehler" in (b.get(op) or {}) for b in (dienst, kind) for op in OPERATIONEN)
    antwort = {"ok": ok, "ts": round(time.time(), 3), "dauer_s": round(time.monotonic() - t0, 3),
               "dienst": dienst, "kind": kind, "faktor": faktor(dienst, kind), "mount": mount,
               "platz": platz, "system": system}
    if "fehler" in kind:
        _log.error(f"SUPPORT: dateiprobe child process failed — {kind['fehler']}")
    if "fehler" in dienst:
        _log.error(f"SUPPORT: dateiprobe service measurement failed — {dienst['fehler']}")
    _log.info(f"SUPPORT: dateiprobe served — service median ms {_medianen(dienst)}; child median ms "
              f"{_medianen(kind)}; nfs {mount.get('nfs')}; took {antwort['dauer_s']} s")
    return antwort


def _haupt(argv):
    """Kindweg: die Messungen fuer den Datenordner aus argv[1], ein JSON auf stdout.
    -> Rueckgabewert 0, 2 bei fehlendem Argument."""
    if len(argv) != 2:
        print(json.dumps({"fehler": "usage: python3 -E -s -m core.dateiprobe <data_dir>"}))
        return 2
    _anhang, _eintraege, deckel_s = _groessen()
    print(json.dumps(messen(argv[1], deckel_s)))
    return 0


if __name__ == "__main__":
    sys.exit(_haupt(sys.argv))
