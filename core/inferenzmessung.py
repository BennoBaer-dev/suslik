#!/usr/bin/env python3
"""INFERENZ-MESSUNG — wie lange EINE eingereichte Inferenz stand und wie viele
gleichzeitig eingereicht waren (.546, 21.09.2026, Hang-Suche).

DER ANLASS, in Zahlen. Im Kernel-Journal des Wirts stehen seit dem 10.08. 45
`GPU HANG`-Eintraege, jeder mit `python` als schuldigem Prozess auf der
Compute-Engine `ccs0`; am 21.09. allein sechs, der letzte um 21:52:16 bei einem
Nachhol-Job mit EINEM Rechenstrang. Der i915 schickt alle `heartbeat_interval_ms`
(2500 ms) einen Herzschlag ueber die aktive Engine, hebt dessen Prioritaet in zwei
Stufen und resettet die Engine, wenn er danach die Compute-Preemptionsfrist
(`preempt_timeout_ms`, 7500 ms) nicht durchkommt. Die 14-17 s, die im Prod-Log vor
jedem Hang stehen, sind deshalb die LATENZ DES DETEKTORS und nicht die Laenge
unserer Rechnung (Herleitung: backups/prod_vorfall_0921/ursache_gpu_hang/
befund.md §5). Was dort als offene Frage stehenblieb: laeuft bei uns eine
Einreichung wirklich ueber diese Fristen? Der Fehler-Dump sagt nur
`avg 3012 ns-gemittelt ueber Kontextabschnitte` — das koennen hundert kurze
Inferenzen sein oder eine lange, und die beiden Faelle haben verschiedene Hebel.
Diese Datei misst genau die Zahl, die das entscheidet.

WAS GEMESSEN WIRD, und nichts darueber hinaus:
  * je Einreichung die WANDUHR-Startzeit (`time.time` — nur sie laesst sich gegen
    die Zeitstempel des Wirt-Journals legen), die DAUER (`perf_counter`, monoton)
    und die TIEFE: wie viele Anfragen dieses Prozesses in diesem Moment
    eingereicht und noch nicht abgeholt sind.
  * je Job eine Bilanz daraus (n, Groesstwert mit seiner Wanduhr-Zeit, p95,
    Mittel, groesste Tiefe) und je Einreichung ueber `INFERENZ_LANGSAM_MS` eine
    eigene Meldezeile — das ist die Zeile, die gegen ein „GPU HANG hh:mm:ss"
    gelegt wird.

EHRLICHE GRENZEN, benannt statt weggelassen:
  * Gemessen wird die WANDUHR um `start_async` + `wait`, nicht die Zeit, die der
    Kernel dem Kontext auf der Engine gegeben hat. Steht die Einreichung hinter
    fremder Last (unsere eigenen Live-Waechter, Frigates LPR), steckt deren
    Wartezeit mit drin. Eine Zahl von hier misst den Weg, den die Rechnung
    wirklich geht — sie ist keine Treiber-Messung.
  * Die Tiefe ist die dieses PROZESSES. Was ANDERE Prozesse gleichzeitig auf
    dieselbe Karte legen, sieht sie nicht; dafuer laeuft die `intel_gpu_top`-
    Aufzeichnung am Wirt.
  * Sie veraendert an der Rechnung NICHTS: kein Wert, keine Reihenfolge, kein
    Puffer. Faellt die Messung aus, laeuft die Inferenz weiter (jede Buchung und
    jede Meldung steht in einem eigenen try) — eine Auskunft darf nie ein Urteil
    kosten.
"""
import threading
import time
from core import logbuch as _logbuch
_log = _logbuch.logger(__name__)

# DIE SCHWELLE fuer die eigene Meldezeile je Einreichung, BEWUSST unter den
# Kernel-Fristen: der Herzschlag der Engine kommt alle 2500 ms, die
# Compute-Preemptionsfrist steht auf 7500 ms (Kernel-Vorgabe
# DRM_I915_PREEMPT_TIMEOUT_COMPUTE, am Wirt unveraendert gemessen). Eine Schwelle
# AUF diesen Fristen saehe nur noch den Hang selbst; bei 1000 ms faellt schon auf,
# wenn sich unsere Einreichungen der Frist naehern. Rauschen ist das nicht: der
# Normalbetrieb liegt zwei Groessenordnungen darunter (Startbenchmark 20.09. im
# Prod-Log: iGPU 24,7 ms je Inferenz, NPU 13,3 ms, CPU-OV 60,5 ms).
INFERENZ_LANGSAM_MS = 1000.0

# Wie viele Einzeldauern ein Buch behaelt, um p95 zu rechnen. Ein Ereignis bringt
# heute in der Groessenordnung tausend Einreichungen (bis 240 Sample-Frames mit je
# einem Detektor-Aufruf, dazu je Gesicht und Stufe ein Ausschnitt- und ein
# Modell-Aufruf). Der Deckel ist grosszuegig und begrenzt trotzdem, was eine
# Auskunft im Speicher halten darf; oberhalb zaehlen n/Groesstwert/Mittel
# unveraendert weiter, p95 kommt dann aus den ERSTEN Werten und die Bilanz sagt
# das mit `gekappt` — eine gekappte Zahl, die sich nicht als vollstaendig ausgibt.
DAUERN_MAX = 50000

# ---------------------------------------------------------------- Prozess-Zustand
# Die Tiefe gehoert dem PROZESS, nicht dem Strang: sie ist die Zahl der Anfragen,
# die in diesem Moment auf der Karte stehen, egal aus welchem Rechenstrang sie
# kommen. Deshalb ein Modul-Zaehler unter einem Schloss und nicht thread-lokal.
_schloss = threading.Lock()
_offen = 0
_lokal = threading.local()


def offene():
    """Wie viele Anfragen dieses Prozesses GERADE eingereicht und noch nicht
    abgeholt sind. -> int"""
    with _schloss:
        return _offen


def zeit_text(ts):
    """Ein Wanduhr-Zeitpunkt in der Form, in der das Kernel-Journal des Wirts
    gelesen wird (Ortszeit, Millisekunden) — nur so lassen sich die beiden
    Zeilen nebeneinanderlegen. -> 'hh:mm:ss.mmm' oder None"""
    if ts is None:
        return None
    return (time.strftime("%H:%M:%S", time.localtime(float(ts)))
            + f".{int((float(ts) % 1.0) * 1000):03d}")


class Buch:
    """Die Inferenz-Messung EINES Jobs auf EINEM Rechenstrang.

    Aggregiert wird LAUFEND (n, Summe, Groesstwert, groesste Tiefe); die
    Einzeldauern liegen bis `DAUERN_MAX` daneben, weil p95 ohne die Verteilung
    nicht zu haben ist. Der `melder` bekommt jede Einreichung ueber der Schwelle
    SOFORT — nicht erst am Jobende: ein Prozess, den der Hang mitnimmt, schreibt
    keine Bilanz mehr, und genau seine letzte Einreichung ist die gesuchte."""

    def __init__(self, marke="", geraet=None, melder=None, langsam_ms=None,
                 dauern_max=None):
        self.marke = str(marke or "")
        self.geraet = geraet
        self.melder = melder
        self.langsam_ms = float(INFERENZ_LANGSAM_MS if langsam_ms is None
                                else langsam_ms)
        self.dauern_max = int(DAUERN_MAX if dauern_max is None else dauern_max)
        self.n = 0
        self.summe_ms = 0.0
        self.max_ms = 0.0
        self.max_ts = None            # Wanduhr-START der laengsten Einreichung
        self.max_stufe = None
        self.max_geo = None
        self.tiefe_max = 0
        self.langsam_n = 0
        self.geo = None               # zuletzt gesehene Geometrie
        self.dauern = []
        self.gekappt = False
        self._buch_schloss = threading.Lock()

    def buchen(self, stufe, geo, ts, ms, tiefe):
        """EINE gemessene Einreichung eintragen. Das Schloss ist da, weil ein Job
        seine Frames in einem Strang rechnet, die Warmlauf-Aufrufe aber aus
        demselben Buch kommen koennen."""
        with self._buch_schloss:
            self.n += 1
            self.summe_ms += ms
            if ms > self.max_ms:
                self.max_ms, self.max_ts = ms, ts
                self.max_stufe, self.max_geo = stufe, geo
            if tiefe > self.tiefe_max:
                self.tiefe_max = tiefe
            if geo:
                self.geo = geo
            if len(self.dauern) < self.dauern_max:
                self.dauern.append(ms)
            else:
                self.gekappt = True
            langsam = ms > self.langsam_ms
            if langsam:
                self.langsam_n += 1
        if langsam and self.melder is not None:
            # AUSSERHALB des Schlosses: der Melder schreibt in ein Log, und ein
            # Log-Schreiber gehoert nie unter ein Mess-Schloss.
            try:
                self.melder(zeile_langsam(self, stufe, geo, ts, ms, tiefe))
            except Exception:                                  # noqa: BLE001
                _logbuch.swallowed(_log, _logbuch.WARNING, "ignored")

    def p95_ms(self):
        """p95 nach NAECHSTEM RANG (kein Interpolieren): der kleinste gemessene
        Wert, unter dem 95 % der Einreichungen liegen. Eine interpolierte Zahl
        waere ein Wert, den keine Einreichung hatte — bei einer Frage nach der
        laengsten Submission ist das die falsche Sorte Genauigkeit. -> float|None"""
        with self._buch_schloss:
            werte = sorted(self.dauern)
        if not werte:
            return None
        rang = int(-(-95 * len(werte) // 100)) - 1            # ceil(0.95*n) - 1
        return werte[max(0, min(len(werte) - 1, rang))]

    def bilanz(self):
        """Die Zusammenfassung dieses Jobs. -> dict (nur Zahlen und kurze Texte,
        keine Bilddaten, keine Namen)"""
        p95 = self.p95_ms()
        with self._buch_schloss:
            n, summe = self.n, self.summe_ms
            return {"n": n,
                    "max_ms": round(self.max_ms, 1),
                    # UNGERUNDET: `max_zeit` schneidet die Millisekunden ab, eine
                    # gerundete Epoche daneben zeigte sonst eine andere
                    # Millisekunde als der Text — bei einer Zahl, die gegen
                    # Kernel-Zeitstempel gelegt wird, ist das genau die falsche
                    # Stelle zum Sparen.
                    "max_ts": float(self.max_ts) if self.max_ts else None,
                    "max_zeit": zeit_text(self.max_ts),
                    "max_stufe": self.max_stufe,
                    "p95_ms": round(p95, 1) if p95 is not None else None,
                    "mittel_ms": round(summe / n, 1) if n else None,
                    "summe_ms": round(summe, 1),
                    "inflight_max": self.tiefe_max,
                    "langsam_n": self.langsam_n,
                    "langsam_ms": self.langsam_ms,
                    "geraet": self.geraet,
                    "geometrie": self.max_geo or self.geo,
                    "gekappt": self.gekappt,
                    "marke": self.marke or None}


class Einreichung:
    """EINE eingereichte Inferenz, als Klammer um `start_async` + `wait`.

    Warum eine Klammer und nicht zwei Aufrufe: die Tiefe muss auch dann wieder
    fallen, wenn die Anfrage mit einer Ausnahme endet — und genau das ist der
    Fall, um den es geht (`CL_OUT_OF_RESOURCES` nach einem Reset der Engine).
    Ein Zaehler, der im Fehlerfall oben bleibt, wuerde jede spaetere Tiefe
    erfinden.

    KOSTEN, damit sie nicht geschaetzt werden muessen: zwei Uhrabfragen und zwei
    kurze Schloss-Abschnitte je Einreichung. Daneben stehen Einreichungen, die
    auf dieser Karte gemessen 11-25 ms dauern."""

    __slots__ = ("stufe", "geo", "tiefe", "ts", "_t0")

    def __init__(self, stufe, geo=None):
        self.stufe, self.geo = stufe, geo
        self.tiefe, self.ts, self._t0 = 0, None, None

    def __enter__(self):
        global _offen
        with _schloss:
            _offen += 1
            self.tiefe = _offen
        self.ts = time.time()                                  # Wanduhr, fuer den Abgleich
        self._t0 = time.perf_counter()                         # Dauer, monoton
        return self

    def __exit__(self, *_ausnahme):
        global _offen
        ms = (time.perf_counter() - self._t0) * 1000.0
        with _schloss:
            _offen -= 1
        buch = getattr(_lokal, "buch", None)
        if buch is not None:
            try:
                buch.buchen(self.stufe, self.geo, self.ts, ms, self.tiefe)
            except Exception:                                  # noqa: BLE001
                _logbuch.swallowed(_log, _logbuch.WARNING, "ignored")
        return False                                           # Ausnahmen laufen weiter


# ---------------------------------------------------------------- Buch je Strang
def buch_start(marke="", geraet=None, melder=None, langsam_ms=None):
    """Ein frisches Buch fuer DIESEN Rechenstrang aufschlagen. Je Job eines: die
    Frage lautet „wie lang war die laengste Einreichung DIESES Ereignisses", und
    ein Buch ueber die Prozess-Lebenszeit koennte sie nicht beantworten. -> Buch"""
    b = Buch(marke, geraet, melder, langsam_ms)
    _lokal.buch = b
    return b


def buch_laufend():
    """Das Buch dieses Strangs oder None — fuer Wachen, die nur hineinsehen."""
    return getattr(_lokal, "buch", None)


def buch_ende():
    """Das Buch dieses Strangs schliessen. -> Bilanz (dict) oder None"""
    b = getattr(_lokal, "buch", None)
    _lokal.buch = None
    if b is None:
        return None
    try:
        return b.bilanz()
    except Exception:                                          # noqa: BLE001
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning None")
        return None


# ---------------------------------------------------------------- Meldetexte
# Beide Zeilen entstehen HIER und nicht beim Aufrufer: sie werden nebeneinander
# gelesen (die Bilanz sagt, wie der Job lief, die Langsam-Zeile zeigt auf den
# Zeitpunkt), und zwei Bauformen an zwei Stellen liefen frueher oder spaeter
# auseinander. Englisch wie das uebrige Prozess-Log.
def zeile_langsam(buch, stufe, geo, ts, ms, tiefe):
    """Die Zeile JE Einreichung ueber der Schwelle — mit Wanduhr-Zeit, weil sie
    gegen `GPU HANG hh:mm:ss` aus dem Wirt-Journal gelegt wird."""
    teile = [t for t in (stufe, f"inflight {tiefe}", buch.geraet, geo,
                         f"job {buch.marke}" if buch.marke else None) if t]
    return (f"inference SLOW: {ms:.0f} ms at {zeit_text(ts)} "
            f"({', '.join(teile)}) — over the {buch.langsam_ms:.0f} ms mark")


def zeile_bilanz(b):
    """Die EINE Bilanzzeile je Ereignis, nach dem Muster der `zeit:`-Zeile des
    Dienstes: die Groessen in der Reihenfolge, in der man sie liest."""
    if not b or not b.get("n"):
        return None
    teile = [f"{b['n']} submissions",
             f"max {b['max_ms']:.0f} ms at {b.get('max_zeit') or 'n/a'}"
             + (f" ({b['max_stufe']})" if b.get("max_stufe") else ""),
             (f"p95 {b['p95_ms']:.0f} ms" if b.get("p95_ms") is not None
              else "p95 n/a"),
             (f"mean {b['mittel_ms']:.0f} ms" if b.get("mittel_ms") is not None
              else "mean n/a"),
             f"inflight max {b.get('inflight_max')}",
             f"{b.get('langsam_n', 0)} over {float(b.get('langsam_ms') or 0):.0f} ms"]
    schwanz = [t for t in (b.get("geraet"), b.get("geometrie"),
                           f"job {b['marke']}" if b.get("marke") else None) if t]
    return ("inference: " + ", ".join(teile)
            + (" | " + " ".join(schwanz) if schwanz else "")
            + (" [durations capped]" if b.get("gekappt") else ""))
