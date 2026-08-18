"""core/schoner — der Frigate-Schoner (.264): Rueckzug statt Retry-Hammer.

Anlass 17.08. abends (Log-Beweis nginx frigate-trixi): Frigates interner
API-Prozess (5001) verklemmte um 21:29 — und DREI suslik-Instanzen hielten
den Stau mit stur weiterlaufenden 20-s-Retries satt, bis der User den
Container von Hand neu startete (8 min Totalausfall, auch fuer HA und
Browser). Ein hoeflicher Client weicht zurueck: nach `schwelle` NETZ-Fehlern
in Folge pausieren alle Frigate-Zugriffe fuer `pause_s`; waehrenddessen darf
alle `probe_s` genau EINE echte Probe raus, damit die Erholung erkennbar
bleibt. HTTP-Antworten (auch 4xx/5xx) zaehlen NIE als Fehler — ein 400
heisst: der Server lebt.

Kontrakt wie core/registry: reine Zustandsmaschine, kein Netz, keine
Dienst-Importe; Uhr injizierbar (Tests)."""
import threading
import time


class Schoner:
    def __init__(self, schwelle=3, pause_s=180, probe_s=30, log=None, uhr=None):
        self.schwelle = int(schwelle)
        self.pause_s = float(pause_s)
        self.probe_s = float(probe_s)
        self.log = log or (lambda m: None)
        self.uhr = uhr or time.monotonic
        self._lock = threading.Lock()
        self._n = 0                       # Netz-Fehler in Folge
        self._bis = 0.0                   # Sperre aktiv bis (uhr-Zeit)
        self._probe_ab = 0.0              # naechster Probe-Slot ab

    def gesperrt(self):
        with self._lock:
            return self.uhr() < self._bis

    def erlaubt(self):
        """Darf JETZT eine echte Anfrage raus? Ohne Sperre immer; waehrend
        der Sperre nur der Probe-Slot (alle probe_s EINE Anfrage)."""
        with self._lock:
            t = self.uhr()
            if t >= self._bis:
                return True
            if t >= self._probe_ab:
                self._probe_ab = t + self.probe_s
                return True
            return False

    def fehler(self):
        """EINEN Netz-Fehler buchen (Timeout/Connection — nie HTTP-Status).
        Ab schwelle beginnt bzw. verlaengert sich die Sperre (eine
        gescheiterte Probe schiebt sie um pause_s hinaus)."""
        with self._lock:
            self._n += 1
            t = self.uhr()
            neu = False
            if self._n >= self.schwelle:
                neu = t >= self._bis
                self._bis = t + self.pause_s
                if neu:
                    self._probe_ab = t + self.probe_s
            n = self._n
        if neu:
            self.log(f"FRIGATE PROTECTOR: {n} consecutive network failures — "
                     f"backing off {int(self.pause_s)} s, one probe every "
                     f"{int(self.probe_s)} s until Frigate answers again")

    def ok(self):
        """Eine echte Antwort kam an (auch ein HTTP-Fehlerstatus): Zaehler
        und Sperre fallen, laut wenn eine Sperre aktiv war."""
        with self._lock:
            war = self.uhr() < self._bis
            self._n = 0
            self._bis = 0.0
        if war:
            self.log("FRIGATE PROTECTOR: Frigate answers again — resuming "
                     "normal operation")
