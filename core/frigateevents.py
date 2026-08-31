"""core/frigateevents — MANUELLE Frigate-Events aus der Live-Schiene,
asynchron (User-Design-Vorgabe 31.08., stand.md "Design-Vorgabe Manual-Events").

WAS: Erkennt ein Live-Waechter eine Person, kann suslik daraus ein EIGENES
Frigate-Event machen — `POST /api/events/{kamera}/{label}/create` mit dem Namen
im `sub_label`. Das ist ausdruecklich NICHT der bestehende sub_label-Weg
(nachtraegliches Beschriften von Frigate-eigenen Events, verifyd._sub_label):
dort haengt suslik sein Urteil an ein fremdes Ereignis, hier entsteht ein
eigenes, losgeloest von Frigates Detektion. Der Weg ist am 31.08. an
seiner Frigate 0.18 live bewiesen (zwei Person-Events auf einer Kamera, mit
Clip + Snapshot, duration selbstbeendend).

WARUM ASYNCHRON — die eine harte Anforderung: der Waechter wartet NIE auf
Frigate. Er legt den Auftrag ab und erkennt weiter. Ein haengendes Frigate
(die Threadpool-Klasse aus dem Feld, MEMORY frigate-018-threadpool-verdacht)
darf niemals die Erkennung anhalten. Deshalb:
  * ein EIGENER Thread mit einer beschraenkten Queue,
  * `put_nowait` — ist die Queue voll, faellt der Auftrag LAUT weg (gezaehlt,
    gedrosselt geloggt). Ein Rueckstau waere die schlimmere Fehlklasse:
    Live-Erkennung, die auf ein Fremdsystem wartet.
  * jeder HTTP-Fehler bleibt in diesem Thread; der Waechter erfaehrt ihn ueber
    den Zaehler, nie ueber eine Ausnahme.

WEGE NACH DRAUSSEN, ALLE ueber core/frigate_auth (Haus-Invariante
[[frigate-nur-api-kein-ssh]]: JEDE Frigate-Kommunikation ueber die HTTP-API,
und seit 5e ueber DEN einen Griff — Kennung `suslik/<version>`, optionaler
Login, TLS-Schalter). Kein eigener urllib-Aufruf, kein SSH, kein Dateisystem.

READ-ONLY IST DER RIEGEL: `frigate_read_only` (Default TRUE fuer alles, was
nicht diese Anlage ist) sperrt jeden Schreibzug hier — genau wie in
verifyd.api_post. Der Riegel wird bei JEDEM Auftrag geprueft, nicht einmal beim
Start: der Nutzer kann ihn im Betrieb umlegen.
"""
import json
import queue
import threading
import time
import urllib.error
import urllib.request

from core import frigate_auth as _fauth     # 5e: DER eine Frigate-HTTP-Griff

# Warteschlangen-Tiefe: grosszuegig genug fuer eine Frigate-Pause von einigen
# Minuten (ein Auftrag je erkannter Person je Kamera, gedrosselt durch den
# Frequenz-Deckel), klein genug, dass ein dauerhaft totes Frigate nicht
# unbegrenzt Speicher bindet.
TIEFE = 200
HTTP_TIMEOUT_S = 15.0
LOG_DROSSEL_S = 300.0      # eine Fehlerzeile je Ursache und 5 min (ein totes
#                            Frigate darf das Log nicht fluten)
LABEL = "person"           # Frigates Objekt-Label des Live-Wegs. Fest: der
#                            Waechter erkennt Gesichter von MENSCHEN; ein freies
#                            Label waere ein zweiter Wahrheitsbegriff im
#                            Frigate-Bestand (die Filter dort heissen 'person').


def read_only(cfg):
    """Derselbe Riegel wie verifyd.frigate_read_only, hier ohne verifyd-Import
    (dieses Modul laeuft im Engine-Prozess, der injektionsrein bleibt).
    Fehlt der Wert, gilt TRUE — nicht schreiben ist der sichere Ausgang."""
    return bool(cfg.get("frigate_read_only", True))


class Warteschlange:
    """Der Hintergrund-Schreiber. Ein Thread, eine Queue, drei Zaehler."""

    def __init__(self, cfg, log=print, tiefe=TIEFE):
        self.cfg = cfg
        self.log = log
        self.q = queue.Queue(maxsize=int(tiefe))
        self.stop_ev = threading.Event()
        self.thread = None
        self.gesendet = 0
        self.fehler = 0
        self.verworfen = 0                # Auftraege, die die volle Queue traf
        self._letzte_zeile = {}           # (art) -> mono der letzten Log-Zeile

    # ---------------------------------------------------------- Lebenszyklus
    def start(self):
        if self.thread is not None:
            return self
        self.thread = threading.Thread(target=self._lauf, name="frigate-events",
                                       daemon=True)
        self.thread.start()
        return self

    def stop(self, frist=3.0):
        """Beenden: Signal + kurzer Join. Bewusst KURZ — ein haengender
        HTTP-Aufruf darf das Herunterfahren der Engine nicht aufhalten; der
        Thread ist daemon, ein Rest stirbt mit dem Prozess."""
        self.stop_ev.set()
        try:
            self.q.put_nowait(None)
        except queue.Full:
            pass
        if self.thread is not None:
            self.thread.join(timeout=frist)

    def status(self):
        return {"sent": self.gesendet, "failed": self.fehler,
                "dropped": self.verworfen, "waiting": self.q.qsize()}

    # ------------------------------------------------------------ Auftraege
    def create(self, kamera, person, score=None, quittung=None):
        """Manuelles Event ANLEGEN (asynchron). `quittung` ist ein Callable
        (event_id) — die Engine merkt sich damit das offene Event fuer das
        spaetere Ende. Rueckgabe: True = eingereiht, False = verworfen."""
        return self._einreihen({"art": "create", "kamera": str(kamera),
                                "person": str(person), "score": score,
                                "quittung": quittung, "ts": time.time()})

    def end(self, event_id):
        """Offenes Event BEENDEN (asynchron)."""
        return self._einreihen({"art": "end", "event_id": str(event_id),
                                "ts": time.time()})

    def _einreihen(self, auftrag):
        try:
            self.q.put_nowait(auftrag)
            return True
        except queue.Full:
            self.verworfen += 1
            self._laut("voll", f"frigate events: queue full ({self.q.maxsize}) "
                               f"— {self.verworfen} order(s) dropped so far; "
                               f"the watchers keep running (they never wait "
                               f"for Frigate)")
            return False

    # ----------------------------------------------------------------- Lauf
    def _lauf(self):
        while not self.stop_ev.is_set():
            try:
                a = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            if a is None:
                break
            try:
                self._ausfuehren(a)
            except Exception as e:                            # noqa: BLE001
                self.fehler += 1
                self._laut(f"{a.get('art')}",
                           f"frigate events: {a.get('art')} failed "
                           f"({type(e).__name__}: {e})")

    def _ausfuehren(self, a):
        if read_only(self.cfg):
            # Kein Fehler, sondern die eingeschaltete Politik — EINE ruhige
            # Zeile je Drosselfenster, damit niemand stundenlang sucht, warum
            # in Frigate nichts ankommt.
            self._laut("readonly", "frigate events: read-only mode is on — "
                                   "no manual events are written (System page)")
            return
        if a["art"] == "create":
            self._create(a)
        elif a["art"] == "end":
            self._end(a)

    def _create(self, a):
        nutzlast = {"sub_label": a["person"],
                    # Aufnahme mitschneiden: ohne sie waere das Event in der
                    # Frigate-UI ein Eintrag ohne Bild — genau das, was die
                    # Live-Probe am 31.08. als brauchbar bestaetigt hat.
                    "include_recording": True,
                    # duration=None heisst OFFEN: das Ende setzt der Waechter
                    # selbst, wenn der Auftritt vorbei ist (PUT .../end). So
                    # deckt das Event den ganzen Durchgang, nicht ein
                    # willkuerliches Zeitfenster.
                    "duration": None}
        if a.get("score") is not None:
            nutzlast["score"] = round(float(a["score"]), 3)
        pfad = f"/api/events/{_quote(a['kamera'])}/{LABEL}/create"
        antwort = self._post(pfad, nutzlast)
        self.gesendet += 1
        eid = None
        if isinstance(antwort, dict):
            eid = antwort.get("event_id") or antwort.get("id")
        if eid and a.get("quittung"):
            try:
                a["quittung"](str(eid))
            except Exception:                                 # noqa: BLE001
                pass
        if not eid:
            # Ehrliche Grenze statt Schweigen: ohne Kennung koennen wir das
            # Event spaeter nicht beenden — Frigate schliesst es dann selbst.
            self._laut("keine_id", "frigate events: create answered without an "
                                   "event id — the event stays open until "
                                   "Frigate closes it")

    def _end(self, a):
        self._put(f"/api/events/{_quote(a['event_id'])}/end",
                  {"end_time": time.time()})
        self.gesendet += 1

    # ------------------------------------------------------------ HTTP-Wege
    def _post(self, pfad, nutzlast):
        return self._http(pfad, nutzlast, "POST")

    def _put(self, pfad, nutzlast):
        return self._http(pfad, nutzlast, "PUT")

    def _http(self, pfad, nutzlast, methode):
        basis = self.cfg.get("frigate_url") or ""
        if not basis:
            raise RuntimeError("no frigate_url configured")
        req = urllib.request.Request(
            basis + pfad, data=json.dumps(nutzlast).encode(),
            headers={"Content-Type": "application/json"}, method=methode)
        try:
            with _fauth.oeffnen(req, timeout=HTTP_TIMEOUT_S) as r:
                roh = r.read(4096)
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read(200).decode("utf-8", "replace").strip()
            except Exception:                                 # noqa: BLE001
                pass
            raise RuntimeError(f"HTTP {e.code} on {pfad}"
                               + (f": {detail}" if detail else "")) from None
        try:
            return json.loads(roh or b"{}")
        except ValueError:
            return {}

    def _laut(self, art, zeile):
        """Gedrosselte Fehlerzeile (Muster livewache._fehler_log): ein totes
        Frigate schreibt sonst je Auftritt eine Zeile ins Log."""
        jetzt = time.monotonic()
        if jetzt - self._letzte_zeile.get(art, -1e18) < LOG_DROSSEL_S:
            return
        self._letzte_zeile[art] = jetzt
        self.log(f"!! {zeile}")


def _quote(s):
    """Pfad-Segment sicher machen. Kameranamen und Event-Kennungen sind
    Fremddaten — nie ungeprueft in eine URL (dieselbe Vorsicht wie bei den
    Datei-Pfaden der Live-Schiene)."""
    import urllib.parse
    return urllib.parse.quote(str(s), safe="")
