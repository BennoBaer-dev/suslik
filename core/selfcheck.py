# core/selfcheck.py — SD1 minimal (Paket 3 Zug B, Bauplan v2 / Anti-Selbstzweck-Schnitt):
# nimmt die im Startup-Selbstcheck gesammelten Records entgegen und schreibt sie ATOMAR
# nach state/startup.json. KEIN Rendering, KEINE verifyd-Importe (Injektion pur) — das
# Menschen-Log bleibt unveraendert die Quelle fuer Leser; die Records sind die Quelle
# fuer Maschinen: /health leitet 'ok' daraus ab (B8-Fang: Selbstcheck-FAIL und health-ok
# koennen nie wieder gleichzeitig wahr sein) und Tester-startup.json wird auswertbar.
import json
import os
import time
from core import logbuch as _logbuch
_log = _logbuch.logger(__name__)


def dateisystem_typ(pfad, mounts="/proc/mounts"):
    """Auf WELCHEM Dateisystem liegt dieser Pfad? -> "ext4", "nfs4", "fuse.shfs"
    … oder "?" (nicht ermittelbar).

    .509 J13 (f), Feldbefund 06.09.2026: bei einem Nutzer verschwand die
    Lauf-Zustandsdatei fuer Momente, obwohl sie atomar (mkstemp+fsync+replace im
    selben Ordner) geschrieben wird — auf einem POSIX-Dateisystem ist das
    unmoeglich. Der Verdacht (FUSE/Netz-Ablage mit nicht-atomarem Rename) liess
    sich aus der Ferne nicht belegen, weil im Startlog nirgends stand, WORAUF
    /data liegt. Jetzt steht es dort, und der naechste Support-Log beantwortet
    die Frage ohne Rueckfrage beim Nutzer.

    Regel: der LAENGSTE Mountpunkt, der den Pfad praefixt (so gewinnt /data
    gegen /). Unlesbar oder kein Treffer -> "?" — nie raten."""
    try:
        ziel = os.path.realpath(pfad or "")
    except Exception:                                         # noqa: BLE001
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning '?'")
        return "?"
    if not ziel:
        return "?"
    try:
        with open(mounts, encoding="utf-8", errors="replace") as f:
            zeilen = f.readlines()
    except Exception:                                         # noqa: BLE001
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning '?'")
        return "?"
    treffer, laenge = "?", -1
    for z in zeilen:
        teile = z.split()
        if len(teile) < 3:
            continue
        # /proc/mounts maskiert Leerzeichen u. ae. oktal (\040) — sonst passte
        # ein Mountpunkt mit Leerzeichen nie.
        punkt = (teile[1].replace("\\040", " ").replace("\\011", "\t")
                 .replace("\\012", "\n").replace("\\134", "\\"))
        if ziel == punkt or (punkt == "/" or ziel.startswith(punkt.rstrip("/") + "/")):
            # .509 Review-SOLL: `>=`, nicht `>`. Bei GESTAPELTEN Mounts (zwei
            # Zeilen mit demselben Mountpunkt, „Overmount") ist der ZULETZT
            # gelistete der wirksame; mit `>` gewann der erste. Nachgestellt:
            # '/dev/sdb1 /data ext4' gefolgt von 'unraid /data fuse.shfs'
            # lieferte 'ext4' — und genau diese Zeile soll den Feldfall aus
            # der Ferne zuordnen (FUSE-Ablage, Netzlaufwerk, Unraid-Share).
            if len(punkt) >= laenge:
                treffer, laenge = teile[2], len(punkt)
    return treffer


def startup_path(data_dir):
    """Der Pfad der Startdatei state/startup.json, an dieser einen Stelle (schreiben und add_fail).
    -> Pfad"""
    return os.path.join(data_dir, "state", "startup.json")


def schreiben(data_dir, version, records):
    """records = Liste {schritt, name, mark, detail}. -> (pfad, fails)."""
    fails = sum(1 for r in records if str(r.get("mark", "")).strip().upper() == "FAIL")
    d = {"ts": round(time.time(), 1), "version": version,
         "fails": fails, "records": records}
    pfad = startup_path(data_dir)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    tmp = pfad + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, pfad)
    return pfad, fails


def add_fail(data_dir, name, detail):
    """Einen FAIL-Eintrag an state/startup.json anhaengen und ueber `schreiben` neu zaehlen (Bauplan
    analysen/bauplan_perf_katalog.md, Stufe PK2: ein gescheitertes Vorwaermen zaehlt wie ein gescheiterter Startschritt).
    -> (pfad, fails); ist die Datei nicht lesbar oder nicht schreibbar, geht der Fehler an den Aufrufer"""
    with open(startup_path(data_dir), encoding="utf-8") as f:
        d = json.load(f)
    records = list(d["records"]) + [{"schritt": None, "name": name, "mark": "FAIL", "detail": detail}]
    return schreiben(data_dir, d.get("version"), records)
