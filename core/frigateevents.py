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

.534 — DAS ENDE MUSS ANKOMMEN (Feldbefund Lasttest 15.09.2026). Drei von 393
Backlog-Ereignissen der Feldanlage hatten kein `end_time`: von UNS per API
angelegt (`data.type = "api"`) und nie geschlossen. Im Dienst-Log stand zu
einem Teil `end failed (HTTP 404 … Event <id> not found)`, obwohl dasselbe
Ereignis spaeter per GET sehr wohl existierte — Frigate legt per API erzeugte
Ereignisse ASYNCHRON an, unser `/end` kam vor der Zeile in seiner Datenbank
und fiel auf 404. Bei einem der drei fehlte sogar die Fehlerzeile: das `/end`
meldete Erfolg und war trotzdem nicht wirksam. Die Folge traf nicht Frigate,
sondern uns: der Analyse-Weg lief in ein Ereignis ohne Ende, las dessen Clip
bis zur Job-Frist und riss den Worker mit (verifyd, B9a faengt das ab).

Vier Regeln daraus, und jede gegen einen belegten Fall:
  1. `/end` bei 404 WIEDERHOLEN, mit Abstand (END_BACKOFF_S) — das 404 ist
     kein Fehler, sondern ein Rennen.
  2. NACH jedem `/end` per GET NACHSEHEN, ob `end_time` wirklich steht. Ein
     gemeldeter Erfolg ist kein Beweis (Fall drei).
  3. Was danach noch offen ist, steht in einer PERSISTENTEN Merkliste
     (`state/frigate_events_offen.json`) und wird beim Start und im Takt
     nachgeschlossen — alles, was aelter ist als `api_event_max_min`.
  4. „beendet" wird erst gesagt, wenn es BESTAETIGT ist; vorher heisst es
     „Ende angefordert". Eine Logzeile, die etwas behauptet, was nicht
     stimmt, ist die teuerste Sorte Diagnose (K1).
"""
import json
import os
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

# .534 — die Abstaende der Ende-Wiederholung. Sie sind KEINE Schwellwerte,
# sondern die Antwort auf ein Anlege-Rennen: Frigate braucht einen Moment, bis
# ein per API erzeugtes Ereignis in seiner Datenbank steht. Vier Anlaeufe ueber
# gut sechs Minuten; danach uebernimmt der periodische Nachschluss, der ohnehin
# laeuft — aufgegeben wird nie.
END_BACKOFF_S = (5.0, 15.0, 60.0, 300.0)
# Wie oft die Merkliste durchgesehen wird und ab welchem Alter ein offenes
# eigenes Ereignis nachgeschlossen wird (Vorgabe, `api_event_max_min` in der
# Config sticht). 30 min sind grosszuegig: ein Auftritt dauert Sekunden bis
# Minuten, und ein noch LAUFENDER Auftritt soll nicht abgeschnitten werden.
NACHSCHLUSS_TAKT_S = 300.0
API_EVENT_MAX_MIN = 30
MERKDATEI = "frigate_events_offen.json"
# Der Nachschluss laeuft im SELBEN Thread wie die Live-Auftraege der Waechter.
# Deshalb ist er in Zahl UND Zeit gedeckelt: Aufraeum-Arbeit darf die laufende
# Arbeit nie verdraengen, und der Rest kommt im naechsten Takt dran.
NACHSCHLUSS_JE_TAKT = 10
NACHSCHLUSS_BUDGET_S = 60.0
# Wie oft ein Eintrag nachgeschlossen wird, bevor er LAUT aufgegeben wird. Ohne
# diesen Deckel bliebe ein Ereignis, das Frigate nie annimmt, fuer immer in der
# Liste und kostete je Takt Zuege.
NACHSCHLUSS_VERSUCHE_MAX = 5
# Wie viele eigene offene Ereignisse die Liste hoechstens traegt. Sie ist eine
# Arbeitsliste, kein Verzeichnis.
OFFEN_MAX = 500


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
        # --- .534: die MERKLISTE eigener offener Ereignisse. Sie ist der Kern
        # des Bausteins: ohne sie ist jedes verlorene `/end` endgueltig.
        # id -> {"kamera", "erstellt_ts", "versuche", "faellig_mono"}
        self._offen = {}
        self._offen_schloss = threading.Lock()
        self.nachgeschlossen = 0
        self.aufgegeben = 0
        self._letzter_takt = 0.0
        self._offen_geladen = False

    # ---------------------------------------------------------- Lebenszyklus
    def start(self):
        if self.thread is not None:
            return self
        # .534: DIE MERKLISTE ZUERST — sie ist der Grund, warum ein Neustart
        # zwischen `create` und `end` das Ereignis nicht mehr fuer immer offen
        # laesst. Der erste Takt laeuft gleich danach im Thread (`_letzter_takt`
        # steht auf 0), also beim Engine-Start.
        self._offen_laden()
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
        with self._offen_schloss:
            offen = len(self._offen)
        return {"sent": self.gesendet, "failed": self.fehler,
                "dropped": self.verworfen, "waiting": self.q.qsize(),
                # .534: wie viele EIGENE Ereignisse in Frigate noch offen sind
                # und wie viele davon nachtraeglich geschlossen wurden. Eine
                # Zahl, die still waechst, ist die Ansage, dass etwas klemmt.
                "api_events_offen": offen,
                "api_events_nachgeschlossen": self.nachgeschlossen,
                "api_events_aufgegeben": self.aufgegeben}

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
            # .534: der Nachschluss-Takt laeuft in DIESEM Thread mit — er ist
            # dieselbe Arbeit an derselben Schnittstelle, und ein zweiter Thread
            # waere ein zweiter Schreiber auf derselben Merkliste.
            self._takt()
            try:
                a = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            if a is None:
                break
            # .534: ein Auftrag mit Abstand (Ende-Wiederholung nach 404) wartet,
            # ohne den Thread anzuhalten — er geht zurueck in die Schlange. Ein
            # `sleep` hier haette jeden anderen Auftrag mitgebremst, und genau
            # das darf die Live-Schiene nie.
            if a.get("faellig_mono") and time.monotonic() < a["faellig_mono"]:
                try:
                    self.q.put_nowait(a)
                except queue.Full:
                    self.verworfen += 1
                time.sleep(0.2)
                continue
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
        if eid:
            # .534: ab hier ist es UNSER offenes Ereignis. Es steht in der
            # Merkliste, bis sein Ende BESTAETIGT ist — nicht, bis wir ein Ende
            # geschickt haben.
            self._offen_setzen(str(eid), a["kamera"])
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
        """Ein eigenes Ereignis beenden — mit Wiederholung und Bestaetigung.

        DREI AUSGAENGE, und keiner davon ist „vermutlich gut":
          * bestaetigt  -> aus der Merkliste, EINE Zeile „beendet"
          * 404         -> Anlege-Rennen, derselbe Auftrag noch einmal mit
                           Abstand (END_BACKOFF_S); danach uebernimmt der Takt
          * kein Ende   -> bleibt in der Merkliste, der Takt versucht es weiter
        """
        eid = str(a["event_id"])
        versuch = int(a.get("versuch") or 0)
        try:
            self._put(f"/api/events/{_quote(eid)}/end", {"end_time": time.time()})
            self.gesendet += 1
        except RuntimeError as e:
            if "HTTP 404" not in str(e):
                # KEIN 404, also kein Anlege-Rennen — aber auch kein Grund, bis
                # zum naechsten Takt (bis zu 5 min) zu warten (Pruefbericht H-9).
                # EIN kurzer zweiter Anlauf, danach traegt die Merkliste den Fall.
                if versuch == 0 and self._einreihen(
                        {"art": "end", "event_id": eid, "versuch": 1,
                         "ts": time.time(),
                         "faellig_mono": time.monotonic() + END_BACKOFF_S[0]}):
                    self._laut("end_fehler",
                               f"frigate events: end failed "
                               f"({type(e).__name__}: {e}) — one more try in "
                               f"{END_BACKOFF_S[0]:g}s, then the periodic sweep")
                    return
                raise
            # DAS 404 IST KEIN FEHLER, SONDERN EIN RENNEN: Frigate legt per API
            # erzeugte Ereignisse asynchron an; unser Ende war schneller als
            # seine Datenbank. Gemessen im Feld am 15.09.
            if versuch < len(END_BACKOFF_S):
                abstand = END_BACKOFF_S[versuch]
                # RUECKGABEWERT PRUEFEN (Pruefbericht H-8): bei voller Queue wird
                # der Auftrag verworfen, und eine Zeile „trying again" waere dann
                # genau die luegende Diagnose, gegen die dieser Baustein gebaut
                # ist. Die Merkliste faengt den Fall ohnehin — sie sagt es nur.
                if self._einreihen({"art": "end", "event_id": eid,
                                    "versuch": versuch + 1, "ts": time.time(),
                                    "faellig_mono": time.monotonic() + abstand}):
                    self._laut(f"end404:{versuch}",
                               f"frigate events: end for an own event was "
                               f"answered with 404 (Frigate creates API events "
                               f"asynchronously) — trying again in "
                               f"{abstand:g}s ({versuch + 1}/"
                               f"{len(END_BACKOFF_S)})")
                else:
                    self._laut("end404_voll",
                               f"frigate events: the retry of an end could not "
                               f"be queued (queue full) — the event stays on the "
                               f"list of own open events, the periodic sweep "
                               f"closes it")
                return
            self.fehler += 1
            self._laut("end404_aus",
                       f"frigate events: end still 404 after "
                       f"{len(END_BACKOFF_S)} tries — the event stays on the "
                       f"list of own open events and the periodic sweep keeps "
                       f"trying")
            return
        # DIE BESTAETIGUNG. Ein gemeldeter Erfolg ist keiner: im Feld blieb ein
        # Ereignis offen, obwohl das `/end` 200 antwortete.
        _b = self._ende_bestaetigt(eid)
        if _b is None:
            # Es gibt das Ereignis in Frigate nicht (mehr) — nichts mehr zu tun.
            self._offen_loeschen(eid)
            return
        if _b:
            self._offen_loeschen(eid)
            self.log(f"frigate events: own event beendet ({eid})")
            return
        self._laut("end_unbestaetigt",
                   f"frigate events: end was accepted but the event still has "
                   f"no end_time — kept on the list of own open events, the "
                   f"periodic sweep closes it")

    # --------------------------------------------- .534 Merkliste + Nachschluss
    def _ende_bestaetigt(self, eid):
        """Steht in Frigate wirklich ein `end_time`? -> True | False | None

        `None` heisst „dieses Ereignis gibt es dort gar nicht (mehr)" — ein GET
        mit 404. Das ist KEIN unbestaetigtes Ende, sondern ein erledigter Fall:
        wer nicht existiert, kann nicht offen sein. Ohne diese Unterscheidung
        blieb ein geloeschtes Ereignis fuer immer auf der Merkliste und kostete
        je Takt Zuege gegen Frigate (Pruefbericht E-7).

        Jede ANDERE Stoerung (Zeitueberschreitung, 500, unlesbare Antwort) gilt
        als „nicht bestaetigt" — die vorsichtige Seite: ein Ereignis zu oft auf
        der Liste zu haben kostet einen Versuch, eines zu wenig kostet den
        Worker."""
        try:
            d = self._get(f"/api/events/{_quote(eid)}")
        except RuntimeError as e:
            return None if "HTTP 404" in str(e) else False
        except Exception:                                     # noqa: BLE001
            return False
        if not isinstance(d, dict):
            return False
        return d.get("end_time") not in (None, "")

    def _merkdatei(self):
        """Wo die Liste eigener offener Ereignisse liegt. -> Pfad|None

        Der Zustandsordner wird ANGELEGT, wenn er fehlt (Pruefbericht H-10):
        vorher gab dieser Griff still None zurueck, und die ganze Merkliste war
        auf einer frischen Installation wirkungslos — ohne ein Wort darueber."""
        basis = self.cfg.get("data_dir") or ""
        if not basis:
            return None
        ordner = os.path.join(basis, "state")
        try:
            os.makedirs(ordner, exist_ok=True)
        except Exception:                                     # noqa: BLE001
            return None
        return os.path.join(ordner, MERKDATEI)

    def _offen_laden(self):
        """Die Merkliste vom letzten Lauf holen. Ein Neustart zwischen `create`
        und `end` liess das Ereignis bis .533 fuer immer offen."""
        self._offen_geladen = True
        pfad = self._merkdatei()
        if not pfad or not os.path.exists(pfad):
            return
        try:
            with open(pfad) as f:
                d = json.load(f) or {}
            eintraege = d.get("offen") if isinstance(d, dict) else None
            if not isinstance(eintraege, dict):
                return
            with self._offen_schloss:
                for eid, wert in eintraege.items():
                    if isinstance(wert, dict):
                        self._offen[str(eid)] = {
                            "kamera": str(wert.get("kamera") or ""),
                            "erstellt_ts": float(wert.get("erstellt_ts") or 0),
                            "versuche": int(wert.get("versuche") or 0)}
            if self._offen:
                self.log(f"frigate events: {len(self._offen)} own event(s) from "
                         f"an earlier run are still open in Frigate — they are "
                         f"closed as soon as they are older than the limit")
        except Exception as e:                                # noqa: BLE001
            self._laut("merk_lesen",
                       f"frigate events: the list of own open events could not "
                       f"be read ({type(e).__name__}: {e}) — starting with an "
                       f"empty one")

    def _offen_schreiben(self):
        pfad = self._merkdatei()
        if not pfad:
            return
        try:
            with self._offen_schloss:
                d = {"offen": {k: dict(v) for k, v in self._offen.items()}}
            tmp = pfad + ".neu"
            with open(tmp, "w") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
            os.replace(tmp, pfad)
        except Exception as e:                                # noqa: BLE001
            self._laut("merk_schreiben",
                       f"frigate events: the list of own open events could not "
                       f"be written ({type(e).__name__}: {e})")

    def _versuch_zaehlen(self, eid, grund):
        """Einen erfolglosen Nachschluss-Versuch buchen und nach
        NACHSCHLUSS_VERSUCHE_MAX aufgeben — LAUT (Pruefbericht E-7).

        Ohne diesen Zaehler blieb ein Eintrag, den Frigate nie annimmt, fuer
        immer in der Liste, in der Datei und in /health, und kostete je Takt
        Zuege gegen dasselbe Frigate, das diese Anlage ohnehin schont."""
        with self._offen_schloss:
            w = self._offen.get(eid)
            if w is None:
                return
            w["versuche"] = int(w.get("versuche") or 0) + 1
            aus = w["versuche"] >= NACHSCHLUSS_VERSUCHE_MAX
            if aus:
                self._offen.pop(eid, None)
        self._offen_schreiben()
        if aus:
            self.aufgegeben += 1
            self.log(f"!! frigate events: giving up on an own open event after "
                     f"{NACHSCHLUSS_VERSUCHE_MAX} attempts ({grund}) — it stays "
                     f"open in Frigate and is no longer tracked here")

    def _offen_setzen(self, eid, kamera):
        voll = False
        with self._offen_schloss:
            if len(self._offen) >= OFFEN_MAX and eid not in self._offen:
                # Arbeitsliste, kein Verzeichnis: der aelteste Eintrag geht.
                aeltester = min(self._offen,
                                key=lambda k: float(
                                    self._offen[k].get("erstellt_ts") or 0))
                self._offen.pop(aeltester, None)
                voll = True
            self._offen[eid] = {"kamera": str(kamera), "erstellt_ts": time.time(),
                                "versuche": 0}
        if voll:
            self._laut("offen_voll",
                       f"frigate events: the list of own open events hit its "
                       f"limit of {OFFEN_MAX} — the oldest entry was dropped; "
                       f"something is keeping these events from closing")
        self._offen_schreiben()

    def _offen_loeschen(self, eid):
        with self._offen_schloss:
            weg = self._offen.pop(eid, None)
        if weg is not None:
            self._offen_schreiben()

    def _takt(self):
        """DER NACHSCHLUSS: alles, was zu lange offen ist, wird geschlossen.

        Er ist das Netz unter allen anderen Wegen — verlorenes `/end`, Neustart
        dazwischen, 404 ueber alle Anlaeufe hinweg. Er laeuft beim Start (der
        Merker steht auf 0) und danach alle NACHSCHLUSS_TAKT_S."""
        jetzt = time.monotonic()
        if jetzt - self._letzter_takt < NACHSCHLUSS_TAKT_S:
            return
        self._letzter_takt = jetzt
        if read_only(self.cfg):
            return
        try:
            grenze_min = float(self.cfg.get("api_event_max_min")
                               or API_EVENT_MAX_MIN)
        except (TypeError, ValueError):
            grenze_min = API_EVENT_MAX_MIN
        schwelle = time.time() - max(1.0, grenze_min) * 60.0
        with self._offen_schloss:
            faellig = [(eid, dict(w)) for eid, w in self._offen.items()
                       if float(w.get("erstellt_ts") or 0) <= schwelle]
        # GEDECKELT IN ZAHL UND ZEIT (Pruefbericht E-8): dieser Takt laeuft im
        # SELBEN Thread wie die Live-Auftraege der Waechter. Ohne Deckel stuende
        # er bei N Leichen und haengendem Frigate bis zu N x 45 s, waehrend
        # `create`/`end` am Queue-Deckel verworfen wuerden — die Aufraeum-Arbeit
        # duerfte nie die laufende Arbeit verdraengen. Der Rest kommt im
        # naechsten Takt dran.
        ende_mono = time.monotonic() + NACHSCHLUSS_BUDGET_S
        for eid, _w in faellig[:NACHSCHLUSS_JE_TAKT]:
            if self.stop_ev.is_set() or time.monotonic() > ende_mono:
                return
            # ERST NACHSEHEN, dann schliessen: die allermeisten sind laengst zu
            # (Frigate schliesst per `duration` oder der Nutzer hat es getan),
            # und ein `/end` auf ein geschlossenes Ereignis waere ein Schreibzug
            # ohne Anlass.
            _b = self._ende_bestaetigt(eid)
            if _b or _b is None:
                self._offen_loeschen(eid)
                continue
            try:
                self._put(f"/api/events/{_quote(eid)}/end",
                          {"end_time": time.time()})
                self.gesendet += 1
            except Exception as e:                            # noqa: BLE001
                self._versuch_zaehlen(eid, str(e))
                self._laut("nachschluss",
                           f"frigate events: could not close an own open event "
                           f"({type(e).__name__}: {e}) — trying again next time")
                continue
            if self._ende_bestaetigt(eid) is True:
                self._offen_loeschen(eid)
                self.nachgeschlossen += 1
                self.log(f"frigate events: own event nachgeschlossen ({eid}) — "
                         f"it had stayed open for more than {grenze_min:g} min")
            else:
                self._versuch_zaehlen(eid, "end not confirmed")

    # ------------------------------------------------------------ HTTP-Wege
    def _get(self, pfad):
        """Lesender Zug ueber denselben Griff (.534, fuer die Ende-Bestaetigung).
        Kein zweiter HTTP-Weg — [[frigate-nur-api-kein-ssh]] gilt hier wie
        ueberall, und `core/frigate_auth` ist DER eine Griff dafuer."""
        basis = self.cfg.get("frigate_url") or ""
        if not basis:
            raise RuntimeError("no frigate_url configured")
        req = urllib.request.Request(basis + pfad, method="GET")
        try:
            with _fauth.oeffnen(req, timeout=HTTP_TIMEOUT_S) as r:
                roh = r.read(65536)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code} on {pfad}") from None
        try:
            return json.loads(roh or b"{}")
        except ValueError:
            return {}

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
