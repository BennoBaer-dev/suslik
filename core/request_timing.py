"""Zeitprotokoll je Seitenaufruf: Stoppuhr, Schritte, laufende Aufrufe, zaehlender Schreiber.

HERKUNFT: Bauplan `analysen/bauplan_seitenzeit.md`, Stufe SZ1 (Fassung 3). Der Eigentuemer am 22.10.2026
13:19:53: „Locken wir denn, wenn jemand auf eine Seite raufklickt, was er sehen möchte und bis das Ergebnis
angezeigt wird und was er dazwischen alles tut?" Bis dahin protokollierte der Webserver keinen Aufruf.

ZWECK: der Handler in `verifyd.make_handler` beginnt je Aufruf eine Stoppuhr (`begin`), setzt nach dem Parsen
Methode und Route (`set_request`), vermerkt den Status aus `send_response` (`note_status`) und schliesst im
`finally` ab (`finish`). Die Seitenzweige klammern ihre schweren Schritte mit `step(name)`. Der Handler ersetzt
`self.wfile` durch `CountingWriter`, der jede erfolgreich geschriebene Byte-Menge zaehlt und den ersten
Sendefehler vermerkt. Die Zeile selbst schreibt der Handler ueber `core/logbuch.py`.

ROUTE STATT PFAD: Zeile und /health nennen nie den rohen Pfad, sondern eine Route aus der festen Liste in
`core/registry.py` (WEB_ROUTES, WEB_ROUTE_PREFIXES); alles Unbekannte heisst WEB_ROUTE_OTHER, jede Methode
ausserhalb von WEB_METHODS heisst WEB_METHOD_OTHER. So kommen keine Namen aus Pfaden oder Abfragen ins Log.

SCHLOSS: `_lock` schuetzt nur Eintragen, Austragen und Kopieren der laufenden Aufrufe und den Zaehler der
Sendefehler; darin wird nicht geloggt, keine Datei gelesen und kein Dienst gerufen, und es wird nie zusammen mit
`Service.lock` oder `_ev_wecker` gehalten. Schritte, Status und Bytes gehoeren dem Faden des Aufrufs.

EHRLICHE GRENZEN: ein Sendefehler heisst, das Betriebssystem meldete beim Schreiben einen Fehler; dass eine
Antwort ohne Fehler auch ankam, belegt nichts hier. Gezaehlt werden nur erfolgreich geschriebene Bytes; wie viel
ein gescheiterter Schreibvorgang noch uebertrug, ist unbekannt. Zeit ausserhalb der Schritte steht nur in der
Gesamtdauer. Neue Routen ohne Eintrag in der Liste erscheinen als `other`.
"""

import contextlib
import threading
import time
import urllib.parse

from core import registry as _reg

_local = threading.local()          # der laufende Aufruf dieses Fadens
_lock = threading.Lock()            # nur Eintragen, Austragen, Kopieren, Zaehler
_running = {}                       # id(Aufruf) -> Aufruf
_send_errors = [0]                  # Antworten mit Sendefehler seit dem Start


class _Call:
    """Ein laufender Aufruf: Beginn, Methode, Route, Status, Bytes, Sendefehler, Ausnahme, Schritte."""

    __slots__ = ("start", "method", "route", "status", "bytes", "send_error", "exc_type", "steps")

    def __init__(self):
        self.start = time.monotonic()
        self.method = _reg.WEB_METHOD_OTHER
        self.route = _reg.WEB_ROUTE_OTHER
        self.status = None
        self.bytes = 0
        self.send_error = None
        self.exc_type = None
        self.steps = {}             # Name -> Sekunden; Reihenfolge = erster Aufruf


class Result:
    """Die Zahlen der Zeile eines abgeschlossenen Aufrufs (`finish`)."""

    __slots__ = ("method", "route", "status", "ms", "bytes", "send_error", "exc_type", "steps", "debug")

    def __init__(self, call, now):
        self.method, self.route, self.status = call.method, call.route, call.status
        self.ms = round((now - call.start) * 1000)
        self.bytes, self.send_error, self.exc_type = call.bytes, call.send_error, call.exc_type
        self.steps = [(name, round(s * 1000)) for name, s in call.steps.items()]
        self.debug = _debug_route(call.route)

    def steps_text(self):
        """Die gemessenen Schritte als Anhang der Zeile, in Aufrufreihenfolge.
        -> str (leer ohne Schritte, sonst ', steps: name=ms …')."""
        if not self.steps:
            return ""
        return ", steps: " + " ".join(f"{name}={ms}" for name, ms in self.steps)


def _debug_route(route):
    return route in _reg.WEB_DEBUG_ROUTES


def method_of(command):
    """Die Methode aus der festen Liste (WEB_METHODS), sonst WEB_METHOD_OTHER.
    -> str."""
    return command if isinstance(command, str) and command in _reg.WEB_METHODS else _reg.WEB_METHOD_OTHER


def route_of(path):
    """Die Route eines Anfragepfads aus der festen Liste: genaue Route, Praefix ohne variablen Teil oder
    WEB_ROUTE_OTHER; der Abfrageteil faellt immer weg. -> str."""
    if not isinstance(path, str):
        return _reg.WEB_ROUTE_OTHER
    try:
        p = urllib.parse.unquote(urllib.parse.urlsplit(path).path)
    except ValueError:
        return _reg.WEB_ROUTE_OTHER
    if p in _reg.WEB_ROUTES:
        return p
    for prefix in _reg.WEB_ROUTE_PREFIXES:
        if p.startswith(prefix):
            return prefix
    return _reg.WEB_ROUTE_OTHER


def _current():
    return getattr(_local, "call", None)


def begin():
    """Eine Stoppuhr fuer den Aufruf dieses Fadens beginnen und ihn als laufend eintragen.
    -> None."""
    call = _Call()
    _local.call = call
    with _lock:
        _running[id(call)] = call


def set_request(command, path):
    """Methode und Route des laufenden Aufrufs aus Anfragewort und Pfad setzen (feste Listen).
    -> None; ohne laufenden Aufruf wirkungslos."""
    call = _current()
    if call is None:
        return
    method, route = method_of(command), route_of(path)
    with _lock:
        call.method, call.route = method, route


def note_status(code):
    """Den ersten gesendeten Status des laufenden Aufrufs vermerken (aus send_response).
    -> None; ohne laufenden Aufruf wirkungslos."""
    call = _current()
    if call is not None and call.status is None:
        call.status = int(code)


def note_exception(exc):
    """Den Typ einer Ausnahme vermerken, die den Messrahmen erreicht hat.
    -> None; ohne laufenden Aufruf wirkungslos."""
    call = _current()
    if call is not None and call.exc_type is None:
        call.exc_type = type(exc).__name__


@contextlib.contextmanager
def step(name):
    """Einen Teilschritt des laufenden Aufrufs messen; gleiche Namen summieren sich.
    -> Kontext (auch als Dekorator nutzbar); ohne laufenden Aufruf wirkungslos."""
    call = _current()
    if call is None:
        yield
        return
    t0 = time.monotonic()
    try:
        yield
    finally:
        call.steps[name] = call.steps.get(name, 0.0) + (time.monotonic() - t0)


def finish(request_line):
    """Den Aufruf dieses Fadens abschliessen und austragen; ein Sendefehler zaehlt fuer /health.
    -> Result, oder None ohne laufenden Aufruf oder ohne Anfragezeile (`request_line` falsch)."""
    call = _current()
    _local.call = None
    if call is None:
        return None
    with _lock:
        _running.pop(id(call), None)
        if request_line and call.send_error is not None:
            _send_errors[0] += 1
    if not request_line:
        return None
    return Result(call, time.monotonic())


def running_calls():
    """Kopie der laufenden Aufrufe aller Faeden.
    -> Liste (Methode, Route, Alter in Sekunden), aelteste zuerst."""
    now = time.monotonic()
    with _lock:
        rows = [(c.method, c.route, c.start) for c in _running.values()]
    return [(m, r, round(now - s, 3)) for m, r, s in sorted(rows, key=lambda x: x[2])]


def other_running_calls():
    """Kopie der laufenden Aufrufe aller Faeden ohne den Aufruf dieses Fadens; unter dem Schloss nur kopieren.
    -> Liste (Methode, Route, Alter in Sekunden), aelteste zuerst (Fadenliste, Bauplan Fadenliste FL1)."""
    own = _current()
    now = time.monotonic()
    with _lock:
        rows = [(c.method, c.route, c.start) for c in _running.values() if c is not own]
    return [(m, r, round(now - s, 3)) for m, r, s in sorted(rows, key=lambda x: x[2])]


def health_block():
    """Der Block `web` fuer /health: laufende Aufrufe und Route und Alter des aeltesten, ohne /health selbst,
    dazu die Antworten mit Sendefehler seit dem Start. -> dict."""
    rows = [r for r in running_calls() if r[1] != "/health"]
    with _lock:
        errors = _send_errors[0]
    oldest = rows[0] if rows else None
    return {"running": len(rows),
            "oldest_route": oldest[1] if oldest else None,
            "oldest_age_s": oldest[2] if oldest else None,
            "send_errors": errors}


def _count(n):
    call = _current()
    if call is not None:
        call.bytes += n


def _note_send_error(exc):
    call = _current()
    if call is not None and call.send_error is None:
        call.send_error = type(exc).__name__


class CountingWriter:
    """Duenne Huelle um `self.wfile`: reicht write, flush, closed und close unveraendert weiter, zaehlt die
    erfolgreich geschriebenen Bytes und vermerkt den ersten Sendefehler, bevor er ihn unveraendert weiterwirft."""

    def __init__(self, raw):
        self._raw = raw

    def write(self, data):
        """Schreiben und zaehlen; ein Fehler des Betriebssystems wird vermerkt und weitergeworfen.
        -> was der innere Schreiber zurueckgibt."""
        try:
            n = self._raw.write(data)
        except OSError as exc:       # umfasst BrokenPipeError, ConnectionResetError, TimeoutError
            _note_send_error(exc)
            raise
        _count(n if isinstance(n, int) else memoryview(data).nbytes)
        return n

    def flush(self):
        """Den inneren Schreiber leeren; ein Fehler wird vermerkt und weitergeworfen.
        -> was der innere Schreiber zurueckgibt."""
        try:
            return self._raw.flush()
        except OSError as exc:
            _note_send_error(exc)
            raise

    @property
    def closed(self):
        """Ob der innere Schreiber geschlossen ist.
        -> bool."""
        return self._raw.closed

    def close(self):
        """Den inneren Schreiber schliessen.
        -> was der innere Schreiber zurueckgibt."""
        return self._raw.close()
