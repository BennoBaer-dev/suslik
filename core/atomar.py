"""core/atomar — EIN Griff fuer atomares Schreiben: eindeutige tmp-Datei IM
Zielordner, flush + fsync, Rechte 0644, os.replace.

Anlass (.411, Tester-Log 02.09.): zwei Schreiber mit DEMSELBEN tmp-Namen.
`refcache_ergaenzen_viele` scheiterte 2x mit FileNotFoundError
'refcache.npz.tmp-1' -> 'refcache.npz' (zwei Laeufe im selben Prozess, PID 1
im Container), und die Live-Status-Runde warf denselben Fehler an
'live_status.json.tmp-<pid>' (zwei Threads desselben Prozesses). Muster war
ueberall `f"{ziel}.tmp-{os.getpid()}"`: der zweite Schreiber oeffnet dieselbe
tmp (truncate), der erste replace() nimmt sie weg, der zweite replace() findet
nichts mehr — und je nach Reihenfolge landet ein HALBER Stand unter dem
Zielnamen.

mkstemp statt Namens-Bastelei: O_EXCL + Zufallsname sind eindeutig ueber
Threads UND Prozesse, auch ueber zwei Container auf demselben Volume mit
derselben PID (pid+thread-ident deckte das nicht). Die tmp liegt IM Zielordner
(replace ist nur auf demselben Dateisystem atomar) und heisst
`.<zielname>.tmp-XXXXXX<suffix>`; ein Suffix ist fuer Werkzeuge, die das
Format an der Endung erkennen (cv2.imwrite, np.load). mkstemp erzeugt 0600 —
deshalb chmod 0644 VOR dem replace (Falle .309: Root-Dateien mit 600 fielen
still aus Backup und Werkzeugen, Memory root-dateien-fallen-aus-werkzeugen).

Stdlib-only, importiert nichts aus dem Dienst (Injektionsreinheit wie
core/kette.py): nutzbar aus verifyd, den core-Modulen, anlernen und der
Live-Engine im eigenen Prozess.
"""
import json
import os
import tempfile

MODUS = 0o644


def tmp_oeffnen(ziel, suffix=""):
    """-> (fd, tmp_pfad): eindeutige, exklusiv angelegte tmp-Datei im Ordner
    von `ziel` (Ordner wird angelegt). Der Aufrufer schliesst fd selbst."""
    ordner = os.path.dirname(ziel) or "."
    os.makedirs(ordner, exist_ok=True)
    return tempfile.mkstemp(dir=ordner,
                            prefix=f".{os.path.basename(ziel)}.tmp-",
                            suffix=suffix)


def schreiben(ziel, schreiber, suffix="", binaer=False, modus=MODUS):
    """`schreiber(f)` schreibt den GANZEN Inhalt in das offene Dateiobjekt;
    danach flush + fsync + chmod(modus) + os.replace(tmp, ziel). Scheitert
    irgendetwas, wird die tmp entfernt und der Fehler WEITERGEWORFEN — der
    Aufrufer entscheidet (loggen, zaehlen, ignorieren). Nie eine halbe
    Datei unter dem Zielnamen, nie eine tmp-Leiche.
    binaer=True oeffnet 'wb' (npz, JPEG-Bytes), sonst 'w' mit UTF-8."""
    fd, tmp = tmp_oeffnen(ziel, suffix)
    try:
        with os.fdopen(fd, "wb" if binaer else "w",
                       **({} if binaer else {"encoding": "utf-8"})) as f:
            schreiber(f)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, modus)
        os.replace(tmp, ziel)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def json_schreiben(ziel, obj, indent=1, ensure_ascii=False):
    """JSON atomar (Vorgabe wie die bisherigen Schreiber: indent=1,
    ensure_ascii=False)."""
    schreiben(ziel, lambda f: json.dump(obj, f, ensure_ascii=ensure_ascii,
                                        indent=indent))


def bytes_schreiben(ziel, daten, suffix=""):
    """Rohbytes atomar (z. B. ein fertig kodiertes JPEG)."""
    schreiben(ziel, lambda f: f.write(daten), suffix=suffix, binaer=True)
