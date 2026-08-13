"""core/liveaufsicht — der SUPERVISOR der Live-Engine im Dienst (Live-Phase 4,
Bauplan §8 "Engine-Prozess stirbt" / §10 Phase 4; Runde R-2026-08-12-live-phase34).

User-Entscheid 12.08. abends: der Dienst (verifyd) startet und ueberwacht die
Engine (`python -m core.livewached run`) als EIGENEN Prozess IM selben
Container — kein compose-Umbau fuer Nutzer. Dieses Modul ist die LOGIK dazu,
verifyd betreibt nur den Takt-Thread (`start_live_aufsicht`).

Verhalten (jede Regel hat einen Harnisch-Fall in tools/harnisch_phase34.py):
 * START nur, wenn (a) die Variante Live kann (gesperrt_fn False, dieselbe
   CPU-Sperre wie Engine/Kacheln), (b) KEIN fremder Prozess das Engine-flock
   haelt (lock_gehalten_fn, s. Standalone unten) und (c) mindestens ein
   enabled-Guard im Store steht (guards_aktiv_fn liest den STORE, nicht die
   Prozess-Sicht — Hand-Edits zaehlen).
 * UEBERWACHUNG doppelt: Prozess-Exit (poll) UND Herzschlag der
   live_status.json (status_frisch_fn = livewache.status_lesen-Frische).
   Ein lebendes Kind ohne frischen Herzschlag ueber die Frist hinaus gilt
   als haengend -> Prozessgruppe SIGKILL + Fehlstart-Verbuchung.
 * NEUSTART mit verdoppelndem Backoff (BACKOFF_START -> BACKOFF_MAX);
   ab FEHLSTART_GRENZE Fehlstarts IN FOLGE eine Stoerungsmeldung
   (stoerung_fn, beide Push-Kanaele des Dienstes) + PAUSE_S Pause —
   nie ein Endlos-Crash-Loop. Ein frischer Herzschlag setzt Kette und
   Backoff zurueck.
 * PROZESSGRUPPE, nie nur die Eltern-PID: die Engine forkt (ffmpeg-Leser),
   und die Kinder ERBEN das flock — Realbeleg dieser Runde: der Halter von
   state/live.lock war ein Fork, nicht die Engine selbst. Deshalb laeuft
   JEDES Beenden ueber killpg auf die Session des Kindes
   (start_new_session=True beim Spawn), und nach JEDEM Kind-Ende raeumt
   ein killpg(SIGKILL) etwaige Fork-Waisen, damit das flock frei wird.
 * STANDALONE-ERKENNUNG: haelt eine fremde (Hand-)Engine das flock, startet
   der Dienst KEINE zweite ("standalone engine detected" auf Live-Seite und
   /health), beobachtet nur lesend und uebernimmt erst, wenn die fremde weg
   ist. So bleibt der Hand-Start (Debug, Messlaeufe) ein gueltiger Betrieb.
 * ENABLE-ANSTOSS: das erste Enable bei nicht laufender Engine weckt den
   Takt sofort (anstossen() hebt Pause/Backoff auf — eine Nutzer-Handlung
   ist ein bewusster neuer Versuch). DISABLE des letzten Waechters stoppt
   die Engine BEWUSST NICHT: das naechste Enable ist dann in Sekunden
   wirksam statt einen Kaltstart (Modell-Laden) zu kosten, und eine leer
   laufende Engine kostet nur ihren Grundverbrauch — sichtbar im Status.

INJEKTION PUR (Muster core/melden.py): dieses Modul importiert verifyd NIE
und core/livewache NIE. Alle Aussenkontakte (Spawn, Lock-Blick, Status-
Frische, Store-Blick, Sperre, Stoerungsmeldung, Uhr, killpg) kommen als
Callables — genau dadurch laeuft der Harnisch mit Prozess-Stubs statt
echter Engine, ohne Modell, ohne Versand, ohne echte Prozesse.
"""
import os
import signal
import threading
import time

# Betriebs-Konstanten (DESIGN-Werte mit Begruendung, keine Messwerte):
TAKT_S = 5.0              # Aufsichts-Takt des Dienst-Threads (Exit faellt binnen ~5 s auf)
BACKOFF_START = 5.0       # erster Neustart-Abstand ...
BACKOFF_MAX = 300.0       # ... verdoppelnd bis Deckel (Muster Reconnect §8: 5 -> 60;
#                           hier hoeher, weil ein Engine-Start Modell-Laden kostet)
FEHLSTART_FRIST_S = 30.0  # Exit frueher als das = Fehlstart (Crash beim Hochfahren)
FEHLSTART_GRENZE = 3      # ab so vielen Fehlstarts IN FOLGE: Stoerung + Pause
PAUSE_S = 900.0           # Crash-Loop-Pause (15 min) — danach neuer Versuchszyklus
ANLAUF_S = 180.0          # Toleranz bis zum ERSTEN Herzschlag (Detektor-/Referenz-
#                           Laden; grosszuegig fuer langsame Maschinen, K2-Klasse)
HERZSCHLAG_TOT_S = 60.0   # danach: lebendes Kind ohne frischen Status = haengend
#                           (30 verpasste 2-s-Takte; der Status-Thread schreibt
#                           auch im Fehlerfall weiter, s. livewache._status_lauf)
STOP_FRIST_S = 10.0       # SIGTERM-Frist beim Dienst-Stopp, danach SIGKILL

# Exit-Vertrag Kind -> Supervisor (Widerleger phase34 KANN-6-Fix): "kein
# enabled-Guard im Store" ist KEIN Absturz und darf nie als Fehlstart zaehlen
# (rc 0 nach 5 s war davon nicht unterscheidbar — 3x davon loeste eine
# Stoerungsmeldung aus). EINE Quelle fuer beide Seiten: core/livewached
# importiert DIESEN Wert (Richtung Kind -> Supervisor-Modul, das Modul
# selbst bleibt injektionsrein).
RC_NICHTS_ZU_TUN = 4


class Aufsicht:
    """Zustandsmaschine des Supervisors — takt()-getrieben, threadfrei
    (den Schleifen-Thread betreibt der Dienst; `weck` weckt ihn frueher).

    spawn_fn        () -> Prozess-Handle (.pid, .poll(), .wait(timeout))
    guards_aktiv_fn () -> bool  (mind. ein enabled-Guard im STORE)
    gesperrt_fn     () -> bool  (CPU-Sperre der Variante, fail-closed)
    lock_gehalten_fn() -> bool  (fremdes Engine-flock, livewache.engine_lebt)
    status_frisch_fn() -> bool  (Herzschlag juenger 3 Takte, status_lesen)
    stoerung_fn     (text)      (Dienst-Stoerungsmeldung, beide Push-Kanaele)
    killpg_fn       (pgid, sig) (os.killpg; der Harnisch zeichnet auf)
    """

    def __init__(self, log, *, spawn_fn, guards_aktiv_fn, gesperrt_fn,
                 lock_gehalten_fn, status_frisch_fn, stoerung_fn,
                 killpg_fn=os.killpg, jetzt=time.monotonic,
                 backoff_start=None, backoff_max=None, fehlstart_frist_s=None,
                 fehlstart_grenze=None, pause_s=None, anlauf_s=None,
                 herzschlag_tot_s=None, stop_frist_s=None):
        self.log = log
        self.spawn_fn = spawn_fn
        self.guards_aktiv_fn = guards_aktiv_fn
        self.gesperrt_fn = gesperrt_fn
        self.lock_gehalten_fn = lock_gehalten_fn
        self.status_frisch_fn = status_frisch_fn
        self.stoerung_fn = stoerung_fn
        self.killpg_fn = killpg_fn
        self.jetzt = jetzt
        # Konstanten zur INSTANZ-Zeit aus dem Modul lesen (nicht als Default-
        # Ausdruck einfrieren): der Mutations-Selbsttest des Harnischs
        # verstellt Modul-Werte und baut die Aufsicht danach neu.
        self.backoff_start = BACKOFF_START if backoff_start is None else float(backoff_start)
        self.backoff_max = BACKOFF_MAX if backoff_max is None else float(backoff_max)
        self.fehlstart_frist_s = FEHLSTART_FRIST_S if fehlstart_frist_s is None else float(fehlstart_frist_s)
        self.fehlstart_grenze = FEHLSTART_GRENZE if fehlstart_grenze is None else int(fehlstart_grenze)
        self.pause_s = PAUSE_S if pause_s is None else float(pause_s)
        self.anlauf_s = ANLAUF_S if anlauf_s is None else float(anlauf_s)
        self.herzschlag_tot_s = HERZSCHLAG_TOT_S if herzschlag_tot_s is None else float(herzschlag_tot_s)
        self.stop_frist_s = STOP_FRIST_S if stop_frist_s is None else float(stop_frist_s)
        self.proc = None
        self.start_mono = None
        self.backoff = self.backoff_start
        self.fehlstarts = 0
        self.warte_bis = -1e18
        self.pause_bis = -1e18
        self.standalone = False
        self.gestoppt = False
        self.weck = threading.Event()      # Dienst-Schleife wartet hierauf (TAKT_S)
        self._je_frisch = False            # dieses Kind hatte schon einen Herzschlag
        self._zuletzt_frisch = -1e18
        # Stopp/Spawn-Race (Widerleger phase34 KANN-3, gemessen E1): takt()
        # prueft gestoppt nur am Eingang; ein stop() aus einem anderen Thread
        # im Spawn-Fenster (~0,5 ms je Takt) fand proc noch None, toetete
        # nichts — und das frische Kind ueberlebte den Dienst-Stopp als Waise
        # MIT flock (der neu gestartete Dienst saehe dann dauerhaft
        # "standalone" und uebernaehme nie). Ein Lock serialisiert takt()
        # und stop(): stop wartet den laufenden Takt ab und raeumt DANACH
        # das dann sichtbare Kind. status() bleibt bewusst lock-frei
        # (Anzeige darf nie hinter einem wait(5 s) haengen).
        self._takt_lock = threading.Lock()

    # ---------------------------------------------------------------- Takt
    def takt(self):
        """EIN Aufsichts-Schritt -> Aktions-Wort (fuer Log/Harnisch):
        laeuft | startet | haengt_gekillt | exit_fehlstart | exit_stoerung_pause
        | exit_sauber | exit_nichts_zu_tun | gesperrt | standalone
        | keine_guards | pause | backoff | gestartet | spawn_fehler | gestoppt

        Unter _takt_lock (KANN-3-Fix): stop() aus einem fremden Thread wartet
        einen laufenden Takt ab — nie wieder ein Kind, das im Spawn-Fenster
        am Stopp vorbei entsteht."""
        with self._takt_lock:
            return self._takt_innen()

    def _takt_innen(self):
        if self.gestoppt:
            return "gestoppt"
        now = self.jetzt()
        p = self.proc
        if p is not None:
            if p.poll() is None:
                return self._lebend_pruefen(p, now)
            return self._exit_verbuchen(p, now, haengend=False)
        ok, grund = self._start_erlaubt(now)
        # Standalone ist ZUSTAND, nicht nur Grund: Live-Seite + /health zeigen ihn.
        neu_standalone = (grund == "standalone")
        if neu_standalone and not self.standalone:
            self.log("live supervisor: standalone engine detected (foreign "
                     "process holds state/live.lock) — not starting a second "
                     "engine, watching read-only until it exits")
        if self.standalone and not neu_standalone:
            self.log("live supervisor: standalone engine gone — taking over")
        self.standalone = neu_standalone
        if not ok:
            return grund
        return self._starten(now)

    def _start_erlaubt(self, now):
        """Start-Riegel in fester Reihenfolge -> (ok, grund). Sperre vor
        Lock vor Guards: die Sperr-Diagnose ist die grundsaetzlichste."""
        if self.gesperrt_fn():
            return False, "gesperrt"
        if self.lock_gehalten_fn():
            return False, "standalone"
        if not self.guards_aktiv_fn():
            return False, "keine_guards"
        if now < self.pause_bis:
            return False, "pause"
        if now < self.warte_bis:
            return False, "backoff"
        return True, ""

    def _starten(self, now):
        try:
            self.proc = self.spawn_fn()
        except Exception as e:
            self.log(f"!! live supervisor: engine spawn failed: "
                     f"{type(e).__name__}: {e}")
            self.proc = None
            self._fehlstart_verbuchen(now)
            return "spawn_fehler"
        self.start_mono = now
        self._je_frisch = False
        pid = getattr(self.proc, "pid", "?")
        self.log(f"live supervisor: engine started (pid {pid})")
        return "gestartet"

    def _lebend_pruefen(self, p, now):
        """Kind lebt: Herzschlag ist die zweite Wache (K1: 'Prozess da' allein
        ist keine Gesundheit — ein haengendes Kind zeigte sonst ewig gruen)."""
        if self.status_frisch_fn():
            self._je_frisch = True
            self._zuletzt_frisch = now
            # gesunder Betrieb setzt Fehlstart-Kette und Backoff zurueck
            self.fehlstarts = 0
            self.backoff = self.backoff_start
            self.standalone = False
            return "laeuft"
        if not self._herzschlag_tot(now):
            return "startet" if not self._je_frisch else "laeuft"
        self.log(f"!! live supervisor: engine (pid {getattr(p, 'pid', '?')}) "
                 f"alive but heartbeat dead ({'never fresh' if not self._je_frisch else 'stale'}) "
                 f"— killing the process group and restarting")
        self._killpg(p, signal.SIGKILL)
        try:
            p.wait(timeout=5)
        except Exception:
            pass
        erg = self._exit_verbuchen(p, now, haengend=True)
        # Der Haenger bleibt als eigenes Aktions-Wort sichtbar; nur die
        # Crash-Loop-Pause (3. Fehlstart) ueberstimmt ihn — sie traegt die
        # wichtigere Information.
        return "haengt_gekillt" if erg == "exit_fehlstart" else erg

    def _herzschlag_tot(self, now):
        """Haengt dieses Kind? Vor dem ERSTEN Herzschlag gilt die Anlauf-
        Toleranz (Modell-Laden), danach die Herzschlag-Frist."""
        if self._je_frisch:
            return now - self._zuletzt_frisch > self.herzschlag_tot_s
        return now - (self.start_mono if self.start_mono is not None else now) > self.anlauf_s

    def _exit_verbuchen(self, p, now, haengend):
        """Kind-Ende verbuchen: Fork-Waisen raeumen (flock!), Fehlstart-Kette
        fuehren, Backoff/Pause setzen. -> Aktions-Wort."""
        rc = p.poll()
        # IMMER die Gruppe raeumen: Fork-Waisen erben das flock (Realbeleg
        # dieser Runde) und blockierten sonst jeden Neustart.
        self._killpg(p, signal.SIGKILL)
        self.proc = None
        dauer = now - (self.start_mono if self.start_mono is not None else now)
        if not haengend and rc == RC_NICHTS_ZU_TUN:
            # Exit-Vertrag (KANN-6-Fix): das Kind fand keinen enabled-Guard —
            # geordnetes Ende, KEIN Fehlstart (das Disable-zwischen-Spawn-und-
            # Engine-Lesen-Fenster loeste sonst Fehlalarme aus). Neustart
            # regulaer, sobald guards_aktiv wieder wahr ist.
            self.log(f"live supervisor: engine ended: nothing to do (no "
                     f"enabled guard, rc={rc} after {dauer:.0f}s) — not a "
                     f"failed start; restarts once a watcher is enabled")
            self.fehlstarts = 0
            self.warte_bis = now + self.backoff_start
            return "exit_nichts_zu_tun"
        if haengend or rc != 0 or dauer < self.fehlstart_frist_s:
            self.log(f"!! live supervisor: engine ended "
                     f"({'hung' if haengend else f'rc={rc}'} after {dauer:.0f}s)")
            return self._fehlstart_verbuchen(now)
        self.log(f"live supervisor: engine ended cleanly (rc=0 after "
                 f"{dauer:.0f}s) — restart follows if guards are enabled")
        self.fehlstarts = 0
        self.warte_bis = now + self.backoff_start
        return "exit_sauber"

    def _fehlstart_verbuchen(self, now):
        self.fehlstarts += 1
        if self.fehlstarts >= self.fehlstart_grenze:
            text = (f"live engine failed to start {self.fehlstarts} times in "
                    f"a row — pausing restarts for {self.pause_s / 60:.0f} min "
                    f"(check the service log; enabling a watcher retries "
                    f"immediately)")
            self.log(f"!! live supervisor: {text}")
            try:
                self.stoerung_fn(text)
            except Exception as e:
                self.log(f"!! live supervisor: disturbance notice failed: "
                         f"{type(e).__name__}: {e}")
            self.pause_bis = now + self.pause_s
            self.fehlstarts = 0
            self.backoff = self.backoff_start
            return "exit_stoerung_pause"
        self.warte_bis = now + self.backoff
        self.backoff = min(self.backoff * 2, self.backoff_max)
        return "exit_fehlstart"

    # ---------------------------------------------------------------- Bedienung
    def anstossen(self):
        """Enable-Anstoss (Bauplan-Auftrag: das erste Enable startet die
        Engine): Pause/Backoff aufheben und den Takt-Thread wecken — eine
        Nutzer-Handlung ist ein bewusster neuer Versuch, auch waehrend der
        Crash-Loop-Pause. Die Fehlstart-Kette bleibt stehen (drei weitere
        Fehlstarts pausieren wieder)."""
        self.pause_bis = -1e18
        self.warte_bis = -1e18
        self.weck.set()

    def stop(self, grund="stop"):
        """Dienst-Stopp: SIGTERM auf die PROZESSGRUPPE (die Engine endet
        sauber, Kacheln schreiben den finalen Status), nach der Frist
        SIGKILL; abschliessend IMMER ein Gruppen-SIGKILL gegen Fork-Waisen
        (flock-Realbeleg). Idempotent.

        gestoppt+weck werden VOR dem Lock gesetzt (ein gerade wartender
        Takt-Thread bricht dann sofort ab); der Kill-Teil laeuft unter
        _takt_lock und sieht damit garantiert auch ein Kind, das ein
        LAUFENDER Takt gerade erst gespawnt hat (KANN-3-Race)."""
        self.gestoppt = True
        self.weck.set()
        with self._takt_lock:
            self._stop_innen(grund)

    def _stop_innen(self, grund):
        p = self.proc
        self.proc = None
        if p is None or p.poll() is not None:
            if p is not None:
                self._killpg(p, signal.SIGKILL)     # Waisen auch nach Exit
            return
        self.log(f"live supervisor: stopping engine (pid "
                 f"{getattr(p, 'pid', '?')}, {grund})")
        self._killpg(p, signal.SIGTERM)
        try:
            p.wait(timeout=self.stop_frist_s)
        except Exception:
            self.log("!! live supervisor: engine ignored SIGTERM — SIGKILL "
                     "on the process group")
            self._killpg(p, signal.SIGKILL)
            try:
                p.wait(timeout=5)
            except Exception:
                pass
        self._killpg(p, signal.SIGKILL)             # Fork-Waisen raeumen

    def _killpg(self, p, sig):
        try:
            self.killpg_fn(getattr(p, "pid", -1), sig)
        except Exception:
            pass

    # ---------------------------------------------------------------- Anzeige
    def status(self):
        """Anzeige-Block fuer /health und die Live-Seite — EINE Quelle fuer
        beide (K3). 'text' ist der englische UI-Satz."""
        now = self.jetzt()
        laeuft = self.proc is not None and self.proc.poll() is None
        d = {"laeuft": laeuft, "standalone": self.standalone,
             "fehlstarts": self.fehlstarts,
             "pid": getattr(self.proc, "pid", None) if laeuft else None}
        if self.standalone:
            d["text"] = ("standalone engine detected — started outside the "
                         "service; the service watches read-only and takes "
                         "over once it exits")
        elif laeuft:
            d["text"] = f"engine running under service supervision (pid {d['pid']})"
        elif self.gestoppt:
            d["text"] = "supervisor stopped"
        elif self._gesperrt_anzeige():
            # Widerleger phase34 MUSS-3: auf gesperrten Builds startet die
            # Engine NIE — "starts automatically once a watcher is enabled"
            # war dort eine Luege und widersprach der /live-Sperr-Karte.
            # /health, System-Karte und /live sagen jetzt dasselbe.
            d["text"] = ("engine not available on this build — live watchers "
                         "need a GPU build (see the Live page)")
        elif now < self.pause_bis:
            d["text"] = (f"engine start paused after repeated failures — next "
                         f"attempt in {max(0.0, self.pause_bis - now):.0f}s "
                         f"(enabling a watcher retries immediately)")
        elif now < self.warte_bis:
            d["text"] = (f"engine restart in "
                         f"{max(0.0, self.warte_bis - now):.0f}s")
        else:
            d["text"] = ("engine not running — starts automatically once a "
                         "watcher is enabled")
        return d

    def _gesperrt_anzeige(self):
        """Sperr-Blick NUR fuer die Anzeige — dasselbe injizierte Praedikat
        wie der Start-Riegel (_start_erlaubt), fail-closed dort; HIER ist ein
        Werfen kein Grund, die Anzeige zu toeten (status() muss immer einen
        Text liefern), darum falsch-negativ tolerant."""
        try:
            return bool(self.gesperrt_fn())
        except Exception:
            return False
