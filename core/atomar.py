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
Zielnamen. Den ersten Schreiber und seine Matrizen-Datei gibt es seit E3c-1
(Bauplan analysen/bauplan_refquelle_einbau.md) nicht mehr; Referenzen schreibt
core/refquelle, und auch das ueber diesen Griff.

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
import threading

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


# Bauplan analysen/bauplan_weniger_schreiben_d.md, Stufe D3 (Entscheid E3): ORDNER EINMAL JE PROZESS.
# Bis dahin rief jeder Pfadaufruf (Clip-Cache, Tor, Anwesenheitsmarke, Ereignisordner im Worker) ein
# os.makedirs auf einen laengst vorhandenen Ordner; das ist trotzdem ein mkdir je Aufruf, beim Feldtester
# auf NFS rund 1.800 je 100 Ereignisse. Und es heilte still: ein geloeschter Ordner kam ohne Meldung wieder.
# Jetzt legt `ordner_einmal` einen Ordner beim ersten Gebrauch je Prozess an und merkt sich den Pfad; das
# Schloss schuetzt nur diese Menge, angelegt wird ausserhalb. Fehlt der Ordner spaeter doch (jemand hat ihn
# geloescht), scheitert das Anlegen einer Datei darin mit FileNotFoundError; `mit_ordner` legt ihn dann LAUT
# neu an (eine WARNING, nur von dem Aufruf, der ihn wirklich anlegt; wer FileExistsError bekommt, war zu
# spaet und schweigt) und wiederholt die Anlage genau einmal. Ehrliche Grenze: ein Leser, der nur liest
# (Ordnerlauf), heilt nicht; er meldet seinen Fehler wie bisher, bis der naechste Schreiber den Ordner anlegt.
_ORDNER = set()
_ORDNER_SCHLOSS = threading.Lock()


def ordner_einmal(ordner):
    """Legt `ordner` beim ersten Gebrauch in diesem Prozess an (os.makedirs), danach ohne Plattenzugriff.
    -> ordner, unveraendert"""
    with _ORDNER_SCHLOSS:
        if ordner in _ORDNER:
            return ordner
    os.makedirs(ordner, exist_ok=True)
    with _ORDNER_SCHLOSS:
        _ORDNER.add(ordner)
    return ordner


def mit_ordner(ordner, anlage):
    """Ruft `anlage()` (legt eine Datei in `ordner` an); fehlt der Ordner, wird er laut neu angelegt und
    `anlage()` einmal wiederholt. -> Rueckgabe von `anlage()`; ein zweiter Fehlschlag steigt auf."""
    try:
        return anlage()
    except FileNotFoundError:
        _ordner_neu(ordner)
    return anlage()


def _ordner_neu(ordner):
    """Legt den fehlenden Ordner an und meldet das als WARNING, nur wenn dieser Aufruf ihn angelegt hat.
    -> None"""
    try:
        os.makedirs(ordner)
    except FileExistsError:
        return          # ein anderer Faden oder Prozess hat ihn angelegt und meldet; oder es fehlte etwas anderes
    # Bewusst erst hier geladen: das Modul bleibt beim Import stdlib-only (Kopf), core.logbuch braucht nur
    # dieser seltene Weg.
    from core import logbuch as _logbuch                       # noqa: PLC0415
    _logbuch.logger(__name__).warning(
        f"folder {ordner} was missing after its first use in this process — created it again")
    with _ORDNER_SCHLOSS:
        _ORDNER.add(ordner)
