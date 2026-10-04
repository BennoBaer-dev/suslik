"""Das zentrale Log fuer Dienst, Worker und Live-Engine (Log-Systematik, Stufe 2).

HERKUNFT: Bauplan `analysen/bauplan_logsystematik.md`, Stufe 2 Punkt 1, mit den
Entscheiden E1 bis E15 (Stufe 1 Teil B) und den Versprechen V1 bis V8. Der
Eigentuemer 26.09.2026 13:39:46: „eine zentrale Log-Funktion, die durchgaengig ist
ueber alle Systeme ... und wir haben verschiedene Log-Level."

ZWECK: dieses Modul richtet Pythons `logging` EINMAL je Prozess ein. Jede Zeile
bekommt den Kopf nach E4 und ist damit fuer Mensch und Maschine lesbar:

    2026-09-26 12:34:21.000 +0200 INFO     dienst/verifyd:Service.process | Text
    2026-09-26 12:34:21.000 +0200 ERROR    worker/worker_dienst:Dienst.arbeiter[rechner-0] +| Folgezeile

Zeitstempel mit Zone, Stufe auf acht Zeichen, Quelle `prozess/modul:funktion[strang]`,
dann ` | ` und der Text; jede Folgezeile eines mehrzeiligen Eintrags traegt
denselben Kopf und ` +| ` (Variante B der Inventur, Punkt 7). Das Zerlegemuster
dazu steht hier und NUR hier (`ZEILENMUSTER`); jeder Verbraucher liest es von hier.

KANAL JE PROZESS (G4): der Dienst schreibt nach fd 1, der Worker nach fd 2 (sein
stdout ist Datenkanal DK1), die Live-Engine nach fd 1. Geschrieben wird per
`os.write` auf die Nummer des Deskriptors, nicht auf ein Python-Dateiobjekt: so
folgt die Zeile jedem `dup2` (Tee, Sieb) und kein `redirect_stdout` lenkt sie um.
Den einen Schreiber der Dateien spielt weiter der Tee (`core/logdatei.py`, E3).

STUFE ZUR LAUFZEIT (E11): die Stufe der Produkt-Logger folgt dem Debug-Schalter.
Der Dienst schaltet sie dort, wo er heute den Schalter spiegelt; Worker und
Live-Engine lesen die Flaggendateien `state/debug_an` und `state/pruef_an` mit
2-s-Gedaechtnis (`logdatei.FLAGGE_TTL_S`). Jeder Wechsel schreibt die Wechselzeile
nach V7.

PRUEF-KANAL (E9): der benannte Logger `pruef` schreibt die Bestaetigungen des
Produkts (Text beginnt mit `PRUEF <thema>`), nur wenn der Schalter an ist. Der Tee
erkennt ihn am Modulfeld des Kopfs und legt die Zeilen in `logs/pruef.log`.

EHRLICHE GRENZEN: Ausgaben der C-Ebene, Abbruchmeldungen des Interpreters und das
Banner des Basis-Images tragen keinen Kopf (V5); das Modul faengt nur, was durch
Python geht. Ein Prozess, der `einrichten` nie ruft (Kommandozeilen-Einstiege, E7),
bleibt still: seine Produkt-Logger haengen an einem NullHandler, damit Pythons
Notfall-Ausgabe keine neuen Zeilen in Datenkanaele (DK1 bis DK10) mischt.
"""

import collections
import datetime
import logging
import os
import re
import sys
import threading
import time

from core import logdatei as _storage

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# E4, Inventur Punkt 7 (TSV `# Punkt 7: Zerlegemuster`): DIE eine Stelle.
ZEILENMUSTER = re.compile(
    r"^(?P<zeit>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} [+-]\d{4}) "
    r"(?P<stufe>DEBUG|INFO|WARNING|ERROR|CRITICAL) +"
    r"(?P<prozess>[a-z][a-z0-9-]*)/(?P<modul>[A-Za-z_][\w.]*):(?P<funktion>[\w.<>]+)"
    r"(?:\[(?P<strang>[\w-]+)\])? (?P<art>\||\+\|) (?P<text>.*)$")

ROOT_NAME = "suslik"             # Namensraum aller Produkt-Logger
PRUEF = "pruef"                  # Name des Pruef-Kanals im Modulfeld des Kopfs (E9)
PRUEF_NAME = f"{ROOT_NAME}.{PRUEF}"

# K03 bis K06 (E1): die Marke einer Startblock-Zeile sagt ihre Stufe.
MARK_LEVEL = {"ok": INFO, "info": INFO, "--": INFO, "?": INFO,
              "warn": WARNING, "FAIL": ERROR}

_STANDARD_LEVELS = (CRITICAL, ERROR, WARNING, INFO, DEBUG)
_UNNAMED_THREAD = re.compile(r"^(MainThread|Thread-\d+( \(.*\))?|Dummy-\d+)$")
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OWN_FILE = os.path.normcase(os.path.abspath(__file__))
_LOGGING_FILE = os.path.normcase(os.path.abspath(logging.__file__))
_PASS_THROUGH = set()            # Code-Objekte von Senken, die der Kopf ueberspringt

_state = {"process": None, "debug": False, "pruef": False,
          "takt_s": None, "start_no": None, "ring": None,
          "watch": None, "takt": None, "observer": None, "started": False}
_state_lock = threading.Lock()
_throttle = set()
_throttle_lock = threading.Lock()


def pass_through(fn):
    """Eine Senke (Kachel-Log, Job-Log) ueberspringt der Kopf, damit die Quelle
    der Ort des Aufrufs bleibt. -> fn unveraendert."""
    _PASS_THROUGH.add(fn.__code__)
    return fn


def _outside(frame):
    """Rahmen aus einer echten Datei ausserhalb des Projekts (Standardbibliothek)?"""
    name = frame.f_code.co_filename
    return os.path.isabs(name) and not os.path.abspath(name).startswith(_PROJECT + os.sep)


def _skip(frame):
    code = frame.f_code
    name = os.path.normcase(code.co_filename)
    return (name in (_OWN_FILE, _LOGGING_FILE) or code in _PASS_THROUGH
            or ("importlib" in name and "_bootstrap" in name))


class _Logger(logging.Logger):
    """Logger, dessen Funktionsname den Klassennamen traegt (co_qualname) und
    Senken dieses Moduls ueberspringt."""

    def findCaller(self, stack_info=False, stacklevel=1):
        """Der Ort des Aufrufs ausserhalb dieses Moduls und seiner Senken.
        -> (Datei, Zeile, Klasse.Funktion, Stapeltext oder None)."""
        frame, own = sys._getframe(1), None
        while frame is not None and _skip(frame):
            if os.path.normcase(frame.f_code.co_filename) == _OWN_FILE:
                own = frame
            frame = frame.f_back
        while frame is not None and stacklevel > 1:
            frame = frame.f_back
            if frame is not None and not _skip(frame):
                stacklevel -= 1
        if own is not None and (frame is None or _outside(frame)):
            frame = own                   # Zeile dieses Moduls selbst (Faden, Griff)
        if frame is None:
            return "(unknown file)", 0, "(unknown function)", None
        code = frame.f_code
        qual = getattr(code, "co_qualname", code.co_name).replace(".<locals>", "")
        sinfo = None
        if stack_info:
            import traceback
            sinfo = "Stack (most recent call last):\n" + "".join(
                traceback.format_stack(frame)).rstrip("\n")
        return code.co_filename, frame.f_lineno, qual, sinfo


logging.setLoggerClass(_Logger)
logging.getLogger(ROOT_NAME).addHandler(logging.NullHandler())


def logger(name):
    """Den Logger eines Moduls holen (Quelle im Kopf kommt aus dem Aufruf-Rahmen).
    -> logging.Logger unter dem Namensraum `suslik`."""
    name = str(name or "modul")
    return logging.getLogger(name if name.startswith(ROOT_NAME + ".")
                             else f"{ROOT_NAME}.{name}")


def pruef_logger():
    """Der benannte Logger des Pruef-Kanals (E9).
    -> logging.Logger `suslik.pruef`."""
    return logging.getLogger(PRUEF_NAME)


# ------------------------------------------------------------------ Zeilenform
def _level_name(levelno):
    for lvl in _STANDARD_LEVELS:
        if levelno >= lvl:
            return logging.getLevelName(lvl)
    return "DEBUG"


def _module(record):
    if record.name == PRUEF_NAME:
        return PRUEF
    path = os.path.abspath(record.pathname or "")
    rel = os.path.relpath(path, _PROJECT) if path.startswith(_PROJECT + os.sep) else ""
    if rel.endswith(".py") and not rel.startswith(".."):
        return rel[:-3].replace(os.sep, ".")
    name = re.sub(r"[^\w.]", "_", record.name or "extern")
    return name if re.match(r"[A-Za-z_]", name) else "_" + name


def _thread(record):
    name = record.threadName or ""
    if not name or _UNNAMED_THREAD.match(name):
        return ""
    return "[" + re.sub(r"[^\w-]", "-", name) + "]"


def _head(created, levelno, process, module, function, thread=""):
    stamp = datetime.datetime.fromtimestamp(created).astimezone()
    function = re.sub(r"[^\w.<>]", "_", function or "?") or "?"
    return (f"{stamp:%Y-%m-%d %H:%M:%S}.{int(stamp.microsecond / 1000):03d} "
            f"{stamp:%z} {_level_name(levelno):<8} {process}/{module}:{function}{thread}")


def _join(head, text):
    lines = str(text).splitlines() or [""]
    return "\n".join([f"{head} | {lines[0]}"] + [f"{head} +| {z}" for z in lines[1:]])


class _Form(logging.Formatter):
    """Zeilenform nach E4, Folgezeilen mit ` +| ` (Variante B)."""

    def format(self, record):
        """Einen Eintrag in Kopf und Text setzen, Ausnahme- und Stapeltext als Folgezeilen.
        -> str ohne abschliessendes Zeilenende."""
        text = record.getMessage()
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            text = f"{text}\n{record.exc_text}"
        if record.stack_info:
            text = f"{text}\n{self.formatStack(record.stack_info)}"
        head = _head(record.created, record.levelno, _state["process"] or "prozess",
                     _module(record), record.funcName, _thread(record))
        return _join(head, text)


def format_line(levelno, module, function, text, when=None):
    """Eine fertige Zeile in der Form, fuer Schreiber ausserhalb von logging
    (Kopfzeile des Tees). -> str ohne Zeilenende."""
    head = _head(time.time() if when is None else when, levelno,
                 _state["process"] or "prozess", module, function)
    return _join(head, text)


def split(line):
    """Eine Zeile mit ZEILENMUSTER in Kopf und Text zerlegen.
    -> dict der Gruppen oder None (Zeile ohne Kopf)."""
    m = ZEILENMUSTER.match(line)
    return m.groupdict() if m else None


class _FdHandler(logging.Handler):
    """Schreibt jeden Eintrag mit einem os.write auf die Nummer des Kanals."""

    def __init__(self, fd):
        super().__init__()
        self.fd = fd

    def emit(self, record):
        """Den Eintrag mit os.write auf den Kanal schreiben, Teilschreiben fortsetzen.
        -> None; Fehler meldet logging ueber handleError."""
        try:
            data = (self.format(record) + "\n").encode("utf-8", "replace")
            while data:
                data = data[os.write(self.fd, data):]
        except Exception:
            self.handleError(record)


class _RingHandler(logging.Handler):
    """Die letzten Zeilen des Dienstes ab INFO fuer /log und /sync_diagnose (E10)."""

    def __init__(self, maxlen):
        super().__init__(INFO)
        self.lines = collections.deque(maxlen=maxlen)

    def emit(self, record):
        """Die Zeilen des Eintrags an den Ringpuffer haengen (alte fallen heraus).
        -> None."""
        try:
            self.lines.extend(self.format(record).split("\n"))
        except Exception:
            self.handleError(record)


def ring_buffer():
    """Der Ringpuffer des Dienstes fuer /log und /sync_diagnose (E10).
    -> deque der Zeilen; ohne einrichten(ring=True) eine leere eigene."""
    ring = _state["ring"]
    return ring.lines if ring is not None else collections.deque(
        maxlen=_storage.RINGPUFFER_ZEILEN)


# ------------------------------------------------------------------ Einrichten
def einrichten(prozess, kanal, ring=False):
    """Pythons logging fuer diesen Prozess einrichten (einmal, frueh).
    -> der Logger `suslik` (Stufe INFO, Werkswert bis der Schalter spricht)."""
    root = logging.getLogger()
    with _state_lock:
        for h in list(root.handlers):
            if isinstance(h, (_FdHandler, _RingHandler)):
                root.removeHandler(h)
        form = _Form()
        out = _FdHandler(int(kanal))
        out.setFormatter(form)
        root.addHandler(out)
        if ring:
            rh = _RingHandler(_storage.RINGPUFFER_ZEILEN)
            rh.setFormatter(form)
            root.addHandler(rh)
            _state["ring"] = rh
        root.setLevel(WARNING)
        _state.update(process=str(prozess),
                      start_no=os.environ.get("SUSLIK_STARTNUMMER") or "1")
    logging.getLogger(ROOT_NAME).setLevel(INFO)
    logging.captureWarnings(True)
    sys.excepthook = _excepthook
    threading.excepthook = _thread_excepthook
    return logging.getLogger(ROOT_NAME)


def _excepthook(typ, value, tb):
    if issubclass(typ, KeyboardInterrupt):
        sys.__excepthook__(typ, value, tb)
        return
    logger("logbuch").error("unhandled exception, the process ends",
                            exc_info=(typ, value, tb))


def _thread_excepthook(args):
    if args.exc_type is SystemExit:
        return
    name = getattr(args.thread, "name", "?")
    logger("logbuch").error(f"unhandled exception in thread {name}, the thread ends",
                            exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


# ------------------------------------------------------------------ Logger-Ersatz
class _Null:
    """Null-Logger: jeder Aufruf tut nichts (E12, Stummschalter)."""

    def _drop(self, *_a, **_k):
        return None

    debug = info = warning = error = critical = log = _drop


NULL = _Null()


class CatchLogger:
    """Fang-Logger (E12): gibt den Text jedes Eintrags ab `level` an `target`.
    Fuer Proben und fuer Kommandozeilen-Aufrufer, die eine Funktion reichen (E7)."""

    def __init__(self, target, level=DEBUG):
        self.target = target
        self.level = level

    def log(self, level, msg, *args, **_kw):
        """Den Text ab der Stufe `self.level` an das Ziel geben.
        -> None."""
        if level >= self.level:
            self.target(str(msg) % args if args else str(msg))

    def debug(self, msg, *a, **k):
        """Eintrag der Stufe DEBUG.
        -> None."""
        self.log(DEBUG, msg, *a, **k)

    def info(self, msg, *a, **k):
        """Eintrag der Stufe INFO.
        -> None."""
        self.log(INFO, msg, *a, **k)

    def warning(self, msg, *a, **k):
        """Eintrag der Stufe WARNING.
        -> None."""
        self.log(WARNING, msg, *a, **k)

    def error(self, msg, *a, **k):
        """Eintrag der Stufe ERROR.
        -> None."""
        self.log(ERROR, msg, *a, **k)

    def critical(self, msg, *a, **k):
        """Eintrag der Stufe CRITICAL.
        -> None."""
        self.log(CRITICAL, msg, *a, **k)


class Adapter(CatchLogger):
    """Umleitung (E12): gibt Text UND Stufe an eine Senke weiter, etwa
    `Engine._klog(kachel, text, stufe=...)` oder `JobLog.zeile(text, stufe=...)`.
    `fixed` legt Schluesselwoerter fest (z.B. stufe=DEBUG fuer Diagnose-Zeilen);
    eine feste Stufe gilt nur fuer Zeilen unter WARNING, WARNING und hoeher
    behalten ihre eigene Stufe (V2: ein Scheitern bleibt laut)."""

    def __init__(self, sink, *args, **fixed):
        super().__init__(sink)
        self.args = args
        self.fixed = fixed

    def log(self, level, msg, *args, **_kw):
        """Text und Stufe an die Senke geben (feste Schluesselwoerter gewinnen,
        eine feste Stufe nur unter WARNING). -> None."""
        kw = {"stufe": level}
        kw.update(self.fixed)
        if level >= WARNING:
            kw["stufe"] = level
        self.target(*self.args, str(msg) % args if args else str(msg), **kw)


def as_logger(log):
    """Ein `log=`-Argument logger-faehig machen: Logger und Ersatz bleiben, eine
    reine Funktion (Kommandozeilen-Aufrufer, E7) wird ein Fang-Logger, None bleibt.
    -> Objekt mit debug/info/warning/error/critical oder None."""
    if log is None or hasattr(log, "warning"):
        return log
    return CatchLogger(log)


# ------------------------------------------------------------------ Stille Pfade
@pass_through
def swallowed(log, level, fallback, throttle=True):
    """Ein bisher stiller except-Block meldet sich (E2): Ausnahmetyp und
    Ersatzwert, gedrosselt einmal je Stelle je Prozessleben. -> None."""
    typ = sys.exc_info()[0]
    if throttle:
        key = logger("logbuch").findCaller()[:2]     # die Stelle: Datei und Zeile
        with _throttle_lock:
            if key in _throttle:
                return
            _throttle.add(key)
    name = typ.__name__ if typ is not None else "exception"
    (log or logger("logbuch")).log(level, f"{name} suppressed — {fallback}")


def level_from_mark(mark):
    """Stufe einer Startblock-Zeile aus ihrer Marke (K03 bis K06, E1).
    -> int (INFO, WARNING oder ERROR)."""
    return MARK_LEVEL.get(str(mark).strip(), INFO)


# ------------------------------------------------------------------ Schalter (V7, E9, E11)
def _on_off(value):
    return "on" if value else "off"


def _switch_text(prefix):
    level = "DEBUG" if _state["debug"] else "INFO"
    return (f"{prefix} level={level} debug={_on_off(_state['debug'])} "
            f"pruef={_on_off(_state['pruef'])} pruef_takt_s={_state['takt_s']} "
            f"version={os.environ.get('SUSLIK_VERSION', 'dev')} "
            f"start={_state['start_no']} pid={os.getpid()}")


def _apply(debug, pruef, takt_s):
    """Schalterstand uebernehmen; beim ersten Mal die Startzeile, danach je
    Wechsel die Wechselzeile (V7). -> True, wenn sich etwas geaendert hat."""
    with _state_lock:
        first = not _state["started"]
        old = (_state["debug"], _state["pruef"], _state["takt_s"])
        new = (bool(debug), bool(pruef), takt_s)
        if not first and old == new:
            return False
        _state.update(debug=new[0], pruef=new[1], takt_s=new[2], started=True)
    logging.getLogger(ROOT_NAME).setLevel(DEBUG if new[0] else INFO)
    text = _switch_text("log start:" if first else "log switch:")
    if not first:
        text += (f" (was: debug={_on_off(old[0])} pruef={_on_off(old[1])} "
                 f"pruef_takt_s={old[2]})")
    logger("logbuch").info(text)
    if new[1]:
        pruef_logger().info(_switch_text("PRUEF start" if first or not old[1]
                                         else "PRUEF switch"))
    return True


def set_switches(data_dir, debug, pruef, takt_s):
    """Dienst: Schalter anwenden und fuer Worker und Live-Engine in die
    Flaggendateien spiegeln (E9, E11). -> True bei Aenderung."""
    takt = int(takt_s) if takt_s else None
    _storage.debug_flagge_setzen(data_dir, bool(debug))
    _storage.pruef_flagge_setzen(data_dir, takt if pruef else None)
    return _apply(debug, pruef, takt)


def pruef_on():
    """Steht der Pruef-Kanal? (Lesen fuer den Tee.)
    -> bool."""
    return bool(_state["pruef"])


def _watch_loop(data_dir):
    while True:
        try:
            takt = _storage.pruef_flagge_lesen(data_dir)
            _apply(_storage.debug_flagge_an(data_dir), takt is not None,
                   takt if takt is not None else _state["takt_s"])
        except Exception:
            swallowed(logger("logbuch"), WARNING, "switches unchanged until the next read")
        time.sleep(_storage.FLAGGE_TTL_S)


def watch_flags(data_dir):
    """Worker und Live-Engine: die Flaggendateien des Dienstes mit 2-s-Gedaechtnis
    lesen und Stufe und Pruef-Kanal folgen lassen (E11). -> der Faden."""
    with _state_lock:
        if _state["watch"] is not None:
            return _state["watch"]
        t = threading.Thread(target=_watch_loop, args=(data_dir,),
                             name="logbuch-flags", daemon=True)
        _state["watch"] = t
    takt = _storage.pruef_flagge_lesen(data_dir)
    _apply(_storage.debug_flagge_an(data_dir), takt is not None, takt)
    t.start()
    return t


def _takt_loop():
    last_full = 0.0
    while True:
        time.sleep(_storage.FLAGGE_TTL_S)
        observer = _state["observer"]
        if observer is None or not _state["pruef"]:
            last_full = 0.0
            continue
        now = time.monotonic()
        full = now - last_full >= float(_state["takt_s"] or 0)
        try:
            lines = observer(not full) or []
        except Exception:
            swallowed(logger("logbuch"), WARNING, "no check lines in this cycle")
            continue
        if full:
            last_full = now
        for level, text in lines:
            pruef_logger().log(level, text)


def start_pruef_takt(observer):
    """Den Pruef-Takt starten (E9 Weg A und B): im Takt ruft er observer(False),
    dazwischen alle 2 s observer(True) fuer Aenderungen. observer liefert
    [(stufe, text)], nur lesend (G0). -> der Faden."""
    with _state_lock:
        _state["observer"] = observer
        if _state["takt"] is not None:
            return _state["takt"]
        t = threading.Thread(target=_takt_loop, name="pruef-takt", daemon=True)
        _state["takt"] = t
    t.start()
    return t


def switches():
    """Stand der Schalter fuer /health (V7).
    -> dict debug, pruef, pruef_takt_s."""
    return {"debug": bool(_state["debug"]), "pruef": bool(_state["pruef"]),
            "pruef_takt_s": _state["takt_s"]}


def health_block(tee, sieves, starts):
    """Der Block `log` fuer /health (E6): Zaehler des Tees je Prozess, Zustand
    von Tee und Sieben, Schalter, Startnummern. -> dict."""
    block = tee.zaehler_stand() if tee is not None else {
        "zaehler": {}, "fremd_n": 0, "letzte_error": None, "zaehl_fehler": 0}
    block["tee"] = tee.zustand() if tee is not None else None
    block["siebe"] = {f"fd{s.fd}": s.zustand() for s in sieves
                      if s is not None and hasattr(s, "zustand")}
    block.update(switches())
    block["startnummern"] = starts
    return block
