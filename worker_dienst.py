#!/usr/bin/env python3
"""worker_dienst — der DIENST-ANSCHLUSS des neuen Kerns (E2, 13.09.2026).

WAS DAS HIER IST: der kuenftige Worker-PROZESS. Er traegt dasselbe Job-Protokoll
wie `worker.py` (JSON-Zeilen auf WORKER_JOB_FD, seit .536 B1b — Rueckfall stdin
wenn die Variable fehlt —, Antworten auf WORKER_ANTWORT_FD) und
denselben Ergebnis-Kontrakt wie `analyze.py` (results.jsonl, Bilder,
kandidaten.jsonl, die Marken im Job-Log) — gerechnet wird darunter aber der neue
Kern (`worker_kern.py` + `engine_ov.py`/`engine_cuda.py`) in MEHREREN Threads
EINES Prozesses statt `runpy analyze.py` in einem Prozess je Job.

NICHT IN DIESER ETAPPE (E3): der Umzug an den endgueltigen Ort und die
verifyd-Verdrahtung. `worker.py`, `verifyd.py` und `analyze.py` bleiben in E2
unberuehrt; diese Datei wird noch von niemandem gestartet ausser von Hand und
vom E2-Gate.

--------------------------------------------------------------------- DIE ACHT STUECKE

1. JOB-PROTOKOLL, erweitert um MEHR-JOB-BETRIEB. Jede Antwort traegt eine
   Job-Id (`id`), mehrere analyze-Jobs laufen gleichzeitig in den Rechenstraengen
   des Kerns. Die uebrigen Job-Typen (ernte, norm, refqs, sammle, vorschlaege,
   passernte, rechenprobe, koerper, personlauf_ernte) laufen seit E2c MIT — auf
   einem eigenen Strang, EINER zur Zeit, parallel zu den Analyse-Straengen.
   Antwortfelder wie worker.py (ok/cpu_s/wall_s/rss_mb/vmhwm_mb/
   rss_spitze_mb/frame_rueckfaelle/fehler/verwurf_grund), dazu die neuen
   strukturierten Felder aus Punkt 3.

1b. E2c — DIE GESICHTS-RECHNUNG DER ALT-WEGE LIEGT AUF DER ENGINE. `engine_bauen`
   haengt `face_audit.Embedder` und `face_audit.NormMass` auf die Fabrik aus
   `bild_kern.py` um (dasselbe Muster wie worker._patch_embedder, worker.py:994).
   Damit rechnen Ernte, Norm, refqs, Vorschlaege, Pass-Ernte UND der
   refcache-Neubau auf demselben Kompilat wie die Live-Erkennung; onnxruntime-
   openvino wird in diesem Prozess nicht mehr geladen, und der gemessene
   E2-Blocker (Referenz-Neubau auf dem CPU-EP, bis 1,59e-02 je Embedding) ist weg.
   Die Job-Zweige selbst (hintergrund_lauf) rufen dieselben Funktionen mit
   denselben Argumenten wie worker.py; anlernen/core.ernte/core.normlauf/
   core.passernte sind UNVERAENDERT. Was NICHT umzieht: e/t (core/guete), p
   (pose_wache), StrukturMass und der Personen-Pfad — sie binden alle den
   CPU-Provider und vertragen sich mit dem OV-Kern (Fundstellen im bild_kern-Kopf).
   Offen fuer E3: die Rechenprobe liefert nur noch einen Bindungs-Bericht statt des
   Werte-Vergleichs je Modell (Begruendung bei Dienst.rechenprobe).

2. RESULTS-KONTRAKT je Event wie analyze.py: EINE Zeile je Label, Append,
   flush nach jeder Zeile; verifyd liest NUR die erste Zeile (verifyd.py:2346);
   Resume ueber done_labels; und die ABWESENHEIT einer Zeile bei 0 lesbaren
   Frames bleibt das Fehlersignal (W1-M11, SD4-Waechter). STRUKTUR-Treue, nicht
   Wert-Treue — die Werte sind die der abgenommenen v8-Basis. Was absichtlich
   fehlt, steht unten unter ABBAU.

3. LOG-WEGE NEU (W2-B1, dup2 ist im Mehr-Job-Betrieb unbrauchbar — die
   Umleitung von fd 1/2 gilt dem GANZEN Prozess, mit N Jobs also allen).
   Stattdessen: je Job eine Python-seitig geschriebene Logdatei (JobLog), in die
   dieser Prozess die Marken schreibt, die qs.sh und webui.bausteine.fehler_grund
   heben. C-Level-/Treiber-Ausgabe bleibt auf fd 1/2 und landet im PROZESS-Log.
   Die Marken, die verifyd heute aus analyze.log hebt (PROVIDER-GUARD,
   PLACEMENT-FALLBACK, Fehlergrund), stehen ZUSAETZLICH als strukturierte Felder
   in der Job-Antwort — eine Quelle statt Log-Parsing. Das Umhaengen der
   verifyd-Leser ist E3.

4. core.frames-ANBINDUNG OHNE MODULGLOBALS (W2-B2): clip_holen bekommt jeden
   Schalter als Argument; die Debug-Senke ueber den neuen `dbg=`-Parameter
   (thread-lokal, core/frames.py). Das Clip-Tor bleibt unveraendert, der
   frame_rueckfaelle-Zaehler wird wie in worker.py gemeldet.

5. DECODER-WACHE (W1-M9): der Engine-Decoder hat bis E1 NICHTS gezaehlt. Jetzt
   liegt hinter jedem Job eine `DecoderWache` mit Soll-Frame-Zaehler und den
   Formeln von decode.FrameIter (uebernommen, nicht nachgebaut) — unvollstaendig
   oder still verfaelscht heisst `frames_fehlen` in results und Antwort.

6. REFCACHE-SELBSTHEILUNG (W1-B3): `referenzen_laden` des Kerns bricht bei
   fehlendem/fremdem Cache ab. Der Dienst darf das nicht — er baut den Cache neu
   aus dem Referenz-Master, mit der vollen load_refs-Semantik von analyze.py
   (Datei-Listen-Pruefung je Person, Beiwert-Vorrang, atomarer Schrieb, Cache
   IMMER ueber ALLE Master-Personen).

7. WACHEN: Prozess-Speicher-Wache auf dem gemessenen Messweg (anon +
   cgroup-shmem statt der VmRSS-Luege der iGPU), Job-Frist-Waechter mit
   Kompilier-Ausnahme, ZUSTANDS-ENDE statt Leerlauf-Uhr (E2d: die Speicher-Wache
   bittet bei Schwellen-Riss um ein geordnetes Ende, vollzogen bei 0 offenen Jobs
   — s. Dienst.ende_bitten und main), Warmlauf-Barriere mit Frist,
   0-Gesichter-Anomalie-Zaehler.

8. --roundtrip: zwei analyze-Jobs (kalt+warm) ueber die echte Job-Mechanik,
   Antwort `{"lauf1":…,"lauf2":…}` nach stdout, die Marken „N Frames" und
   „bestes 3s-Fenster N" im Job-Log — genau das, was tools/qs.sh liest.

--------------------------------------------------------------------- ABBAU

Absichtlich NICHT mehr in results.jsonl (Konzept §3 „toter Output faellt weg",
Fundstellen-Beleg je Feld in der Inventur backups/analyse_0913/
inventur_worker_ersatz.md §A.13 — dort per grep ueber alle *.py/*.sh/*.html/*.js
nachgewiesen ohne Leser):
  persons.median, persons.n, persons.n_ge40, persons.n_ge50, persons.best_wh,
  persons.best_det, persons.best_t, persons.blick_t0,
  persons.best_front, persons.best_pose  (die zwei trug schon die v8-Basis nicht),
  hwdec  (ohne _fallback; steht jetzt als `frames.kette` in der Job-Antwort)
AUSDRUECKLICH GEBLIEBEN, gegen die v0.1-Abbauliste:
  decoder_fehler  (als AEQUIVALENT, W1-Korrektur — jetzt erstmals mit Inhalt)
  profil          (Gate-Stufe s11_m1 liest es, W1-K1)
  urteil_guete    (vollstaendig: es ist die Latten-Dokumentation des Laufs und
                   das Material der Schatten-Eichung E2b; ohne sie ist an
                   Bestandsdaten nicht entscheidbar, ob ein Fund an der Latte
                   oder an der Unmessbarkeit fiel, analyze.py:964-971)
  detektionen     (vollstaendig, W1-M1: faces_geprueft, max_bw, no_person,
                   gesicht_gut und stimm_idx haengen an dieser Liste)

--------------------------------------------------------------------- EHRLICHE GRENZEN

* `cpu_s` ist im Mehr-Job-Betrieb die CPU-Zeit DIESES Rechenstrangs
  (time.thread_time), nicht die des Prozesses: os.times() waere bei N Jobs die
  Summe aller und damit je Job eine Luege. Kindprozesse (ffmpeg) zaehlen wie in
  worker.py nicht mit.
* `rss_mb`/`vmhwm_mb`/`rss_spitze_mb` sind PROZESS-Werte und bei N > 1 keine
  Job-Groessen mehr — die Job-Zuordnung von Speicher ist bei Threads
  grundsaetzlich Schaetzung (Konzept §2). Deshalb bucht ein Wache-Abbruch auch
  ALLE offenen Jobs als fremdverschuldet, statt einen zu beschuldigen.
* Der Frist-Waechter macht eine gerissene Frist LAUT und zaehlt sie; toeten kann
  er einen haengenden Rechenstrang nicht, ohne die uebrigen Jobs mitzunehmen.
  Der Schuss liegt beim Dienst — GEBAUT in E3.3 (verifyd.WorkerDienst.kill_hart,
  `haenger=True`): Prozess schiessen, ALLE offenen Jobs als fremdverschuldet
  buchen, frisch starten, Kurzform der Start-Proben vorlegen, den Vorgang als
  `haenger_schuesse` in /health zaehlen. Ein gezielter Strang-Schuss wird
  ausdruecklich NICHT gebaut: ein Python-Thread ist von aussen nicht beendbar.
* ERLEDIGT in E3.1 (14.09.2026): die Job-Optionen kommen als Job-FELDER
  (`felder_lesen`), nicht mehr aus einer analyze-argv. Die Kommandozeile gibt es
  nur noch fuer `--roundtrip` (`argv_zu_job` uebersetzt sie EINMAL in Felder).
  ARGV_VORGABE bleibt als FUELLUNG fehlender Felder stehen — der Aufrufer schickt
  jede Latte, die er kennt; was fehlt, bekommt den belegten analyze.py-Wert.
* Der Referenz-NEUBAU laeuft ueber face_audit.Embedder (der alte ORT-Weg) und
  damit ueber einen ANDEREN Pixelweg als die Live-Embeddings der Engine. Das ist
  der Zustand, den schon die v8-Basis hatte (sie LAS denselben Cache); E2c zieht
  ihn auf die Engine um („Referenzen und Live-Embeddings aus EINER Quelle").
"""
import argparse
import collections
import contextlib
import gc                                                 # .531: Ringverweis Satz<->Geometrie loest nur der Sammler
import inspect
import json
import os
import queue
import socket
import sys
import tempfile
import threading
import time

# worker_kern ZUERST, VOR numpy — das ist keine Stilfrage, sondern eine
# Wert-Bedingung. Der Kern pinnt in seinem Kopf die BLAS-Thread-Zahl auf 1
# (os.environ.setdefault, worker_kern.py:61-78) und importiert erst DANACH numpy;
# OpenBLAS liest die Variable genau einmal, beim Laden. Stand hier vorher ein
# eigenes `import numpy` davor, lief der Score-Matmul mit dem vollen Thread-Pool:
# gemessen im E2-Gate 13.09. waren ZWEI identische Fuenf-Event-Laeufe danach nicht
# mehr byte-gleich (bis 0,005 in persons.max), weil ein mehrstraengiger Matmul je
# nach Lastverteilung in anderer Reihenfolge summiert — und E1 hatte schon
# gemessen, dass derselbe Pool +11/+12 % Wanduhr kostet.
import worker_kern as wk                                  # noqa: E402  Bootstrap + BLAS-Pin
import numpy as np                                        # noqa: E402  (schon vom Kern geladen)

import bild_kern                                          # noqa: E402  E2c: der Bild-Weg
import decode                                             # noqa: E402  _probe, toleranz, Wache-Formeln
import face_audit                                         # noqa: E402  Embedder (Referenz-Neubau)
from core import frames as clipcache                      # noqa: E402  Clip-Beschaffung
from core import guete as guete_mod                       # noqa: E402  verfuegbar()
from core import gpubudget as _gpubudget                  # noqa: E402  .531 Reserve/Leiter
from core import messkarte as mk_bilanz                   # noqa: E402  profil()
from core import registry as _registry                    # noqa: E402  .531 VRAM-Fehlertexte

# urlretrieve kennt kein timeout= — prozessweit wie worker.py:88 und analyze.py:27.
socket.setdefaulttimeout(120)

# Frist der Warmlauf-Barriere: die des Kerns, kein zweites Literal.
BARRIERE_FRIST = wk.BARRIERE_FRIST
# Wie lange dieser Prozess beim stdin-EOF noch auf laufende Jobs wartet, bevor er
# geht. EOF heisst „verifyd ist weg oder hat execv gemacht" (worker.py:1013); die
# offenen Jobs sollen ihre Antwort noch schreiben duerfen, sonst stuenden N
# Ereignisse ohne Grund auf Fehler.
EOF_FRIST_S = 60.0
# Takt der Prozess-Speicher-Wache. Reine Mess-Kadenz wie worker.WACHE_INTERVALL_S.
WACHE_TAKT_S = 1.0
# --- .531 KARTEN-SONDE ------------------------------------------------------
# Mindestabstand zwischen zwei nvidia-smi-Aufrufen der Wache. Der Aufruf ist ein
# FORK: im Sekundentakt waere er eine eigene Last, und der freie Kartenspeicher
# aendert sich nicht in Millisekunden. 2 s ist die Kadenz der Sonde, nicht die
# der Wache — der Container-Fussabdruck wird weiter je Sekunde gemessen.
KARTE_TAKT_S = 2.0
# Nach wie vielen Fehlversuchen IN FOLGE die Karte als „nicht messbar" gilt. Ein
# einzelner Ausfall (Timeout, kurzer Treiber-Hikel) darf die Anlage nicht
# umstellen; drei in Folge sind kein Zufall mehr.
KARTE_FEHLVERSUCHE_MAX = 3
# --- .532 ------------------------------------------------------------------
# Nach wie vielen Treffern am EIGENEN Arena-Deckel dieser Prozess um einen
# geordneten Neustart bittet. 1 waere zu scharf (ein einzelner Ausreisser bei
# einem besonders vollen Bild kostete die warmen Kompilate), 14 war zu stumpf:
# im Feld traf der Deckel am 15.09. nach SECHS Ereignissen, danach 14 mal
# hintereinander, und der Prozess fand ohne Neustart nie wieder heraus (er
# fiel auf einen Strang und blieb rot). Zwei Treffer sind kein Ausreisser mehr.
DECKEL_TREFFER_BIS_NEUSTART = 2
# Mindestabstand zwischen zwei Abfragen des EIGENEN Kartenanteils. Wie die
# Karten-Sonde ein Fork; sie laeuft je abgeschlossenem Analyse-Job, und im Feld
# dauert ein Ereignis 15-52 s — der Abstand schneidet damit nur den Fall ab, in
# dem mehrere Straenge fast gleichzeitig fertig werden.
KARTE_EIGEN_TAKT_S = 5.0

# .534 (B3): Stufung des RAM-VORSCHLAGS je Strang. Eine Anzeige-Stufung, kein
# Budget und keine Schwelle — der Vorschlag ist eine Messauskunft an den
# Betreiber, und eine Zahl wie „2687 MB" taeuscht eine Genauigkeit vor, die eine
# Spitzenmessung nicht hat. 256 MB ist die Stufung, in der `worker_rss_max_mb`
# ohnehin gesetzt wird.
RAM_VORSCHLAG_STUFE_MB = 256

# .535: HIER STANDEN `EICH_FASSUNG` und `EICH_FENSTER_WERK` — Dateiformat und
# Fensterbreite der Preis-Messung. Beide sind mit dem Ausbau der Messung
# entfallen; geplant wird aus der Messtabelle in `core.gpubudget`.
# Takt des Job-Frist-Waechters.
FRIST_TAKT_S = 5.0
# Vorgabe-Frist eines Jobs, wenn der Dienst keine mitgibt. Bewusst gross: sie ist
# nur die Reissleine fuer die MELDUNG, nicht der Deckel des Dienstes.
FRIST_VORGABE_S = 900.0
# Die Job-Typen, die NICHT die Analyse sind (E2c). Sie laufen EINER ZUR ZEIT auf einem
# eigenen Strang, parallel zu den Analyse-Straengen desselben Prozesses — genau wie
# heute, wo `verifyd` sie ueber `WorkerProzess.lock` serialisiert (Inventur §B.1) und
# ueber die Platz-Klassen gegen die Analyse stellt. Die Liste ist die des
# Job-Protokolls von `worker.py:18-60`; `ping` und `analyze` stehen bewusst nicht
# darin (der eine wird sofort beantwortet, der andere geht in die Rechenstraenge).
HINTERGRUND_TYPEN = ("sammle", "vorschlaege", "refqs", "ernte", "norm", "passernte",
                     "rechenprobe", "koerper", "personlauf_ernte",
                     # E3.4 (14.09.2026): die KURZFORM der Start-Proben (Konzept §4
                     # Schicht 1). Sie laeuft auf dem Hintergrund-Strang, weil sie
                     # rechnet — aber OHNE Exklusivfenster: die Vollform gehoert in
                     # den Boot, die Kurzform in jeden Betriebs-Neustart und hinter
                     # jede Anomalie-Meldung (s. Dienst.startprobe).
                     "startprobe")
# E3.3 (14.09.2026, W2-B29): wie viele Clip-GEOMETRIEN dieser Prozess hoechstens
# gleichzeitig haelt, wenn der Aufrufer keinen Deckel mitschickt. 0 = KEIN Deckel,
# und genau das ist die Vorgabe — eine hier hineingeschriebene Zahl waere auf jeder
# fremden Karte falsch (dieselbe Regel wie bei `fussabdruck_max_mb`, s. SpeicherWache).
# Den Wert rechnet verifyd aus der Speicher-Formel (`core.gpubudget.geometrien_deckel`)
# und schickt ihn als Job-Feld `geometrien_max`; fehlt er, sagt der Dienst das EINMAL
# laut und waechst unveraendert weiter wie bis E2d.
GEOMETRIEN_MAX_VORGABE = 0
# --- Kompilat-Probe (E2d) -------------------------------------------------------
# Die Eichmarke liegt im Arbeitsordner, nicht im Code: was ein Kompilat auf DIESER
# Maschine rechnet, ist eine Eigenschaft der Maschine (Treiber, OpenVINO, iGPU), keine
# Hauskonstante. Eine hier hineingeschriebene Zahl waere auf jedem fremden System falsch.
EICHMARKE_DATEI = "kompilat_eichmarke.json"
# Die Latten der Probe, aus der E2d-Messung und mit Abstand zu BEIDEN Seiten:
#   Rauschboden  gleiche Bau-Reihenfolge max|d| 0,0 - andere Reihenfolge 4,5e-08 (1-cos ~1e-16)
#   Defektfall   max|d| 4,2e-03 bis 8,4e-03, 1-cos bis 1,8e-03, ||f|| bis -1,07
# 1e-6 liegt rund Faktor 500 ueber dem Rauschen und Faktor 1000 unter dem Defekt.
EICH_COS_MAX = 1e-6          # groesstes zugelassenes 1 - cos der Pruef-Embeddings
EICH_NORM_MAX = 0.01         # groesste zugelassene Abweichung der Feature-Norm
# --- STAFFEL-SCHLOSS (.529, Feldvorfall 15.09.) ----------------------------------
# Ab welcher Wartezeit das Staffeln EINE Zeile wert ist. Reine Melde-Schwelle, kein
# Budget: gewartet wird so lange wie noetig, nur das Protokoll soll nicht bei jedem
# Treffer-Bau eine Zeile bekommen. Eine Sekunde, weil darunter kein echter Bau liegt
# (der kuerzeste gemessene Warm-up war 0,1 s, die echten Bauten 2,6-4,3 s).
STAFFEL_MELDE_S = 1.0
# Wie lange ein Strang HOECHSTENS auf das Staffel-Schloss wartet, bevor er ohne es
# weitermacht. Es ist die Frist der Warmlauf-Barriere des Kerns — kein zweites
# Literal, dieselbe Groessenordnung, dieselbe Begruendung: ein Bau, der laenger
# braucht, ist kein Bau mehr, sondern ein Haenger. Ohne diese Frist wuerde EIN
# haengender Bau alle uebrigen Straenge still mitnehmen, und die Frist-Wache saehe
# sie nicht (sie ueberspringt Jobs im Kompilat-Bau).
STAFFEL_FRIST_S = BARRIERE_FRIST


# ----------------------------------------------------------------- Prozess- und Job-Log
def einzeilig(text, deckel=600):
    """Beliebigen Text zu EINER Logzeile machen.

    Kein Schoenheitsgriff: ffmpeg-Fehler sind mehrzeilig (fuenf Zeilen beim
    gemessenen VAAPI-Teilabbruch), und beide Leser dieser Logs arbeiten ZEILENWEISE
    — webui.bausteine.fehler_grund nimmt die LETZTE mit „FEHLER" beginnende Zeile
    (webui/bausteine.py:110-112), und die User-Auflage lautet „eine Information im
    Log, aber nur einmal pro Event". Ein mehrzeiliger Eintrag waere beides nicht."""
    s = " ⏎ ".join(str(text).splitlines()).strip()
    return s if len(s) <= deckel else s[:deckel - 1] + "…"


def prozess_log(text):
    """Eine Zeile ins PROZESS-Log (fd 2). Hier landet, was dem Prozess gehoert und
    nicht einem Job: Aufbau, Wachen, Engine-Bindung. C-Level-Ausgabe von Treiber und
    Bibliotheken faellt ohne unser Zutun auf denselben fd — genau deshalb wird er im
    Mehr-Job-Betrieb NICHT mehr per dup2 in eine Job-Datei umgehaengt (W2-B1)."""
    try:
        os.write(2, (f"worker_dienst: {einzeilig(text)}\n").encode())
    except Exception:                                      # noqa: BLE001
        pass


class JobLog:
    """Die Logdatei EINES Jobs, Python-seitig geschrieben (W2-B1).

    Sie traegt genau die Marken, die heute jemand aus analyze.log hebt:
      „=== <label>  (<eid>) — N Frames, M Gesichter ===" (qs.sh:12045/12054, :311)
      „<person> max +0.xx … bestes 3s-Fenster N×≥…"      (qs.sh:12043/12072, :312)
      „FEHLER: …"                                         (webui/bausteine.py:110-112)
    Mehr nicht: was frueher an Rand-Ausgabe hineinlief (pthread-Spam, Provider-
    Marker), gehoert jetzt ins Prozess-Log bzw. in die strukturierte Antwort.

    Der Schreibzugriff ist gesperrt, weil ein Job mehrere Threads sieht (Rechen-
    strang, Wachen)."""

    def __init__(self, pfad, modus="a"):
        self.pfad = pfad
        self._schloss = threading.Lock()
        self._f = None
        if pfad and pfad != os.devnull:
            try:
                # Der Dienst legt den Ereignis-Ordner heute selbst an und leert
                # analyze.log vor dem Job (verifyd.py:2129). Verlassen wird sich
                # darauf nicht: faellt der Ordner weg, landet das ganze Job-Log
                # still im Prozess-Log, und der Ereignis-Ordner haette hinterher
                # kein analyze.log — die Oberflaeche verlinkt es aber
                # (routes/event.py:168-169).
                os.makedirs(os.path.dirname(pfad) or ".", exist_ok=True)
                self._f = open(pfad, modus, encoding="utf-8")
            except OSError as e:                           # noqa: BLE001
                prozess_log(f"job log {pfad!r} not writable ({e}) — logging to the process log")

    def zeile(self, text):
        # Mehrzeiliges wird EINE Zeile (s. einzeilig): die Leser dieses Logs
        # arbeiten zeilenweise. Die eigenen Marken enthalten bewusst ein fuehrendes
        # \n (analyze.py:811) — das bleibt als Leerzeile erhalten.
        fuehrend, text = ("\n", text[1:]) if str(text).startswith("\n") else ("", text)
        text = fuehrend + einzeilig(text)
        with self._schloss:
            if self._f is None:
                prozess_log(text)
                return
            try:
                self._f.write(text + "\n")
                self._f.flush()
            except OSError:
                pass

    def schliessen(self):
        with self._schloss:
            if self._f is not None:
                try:
                    self._f.close()
                except OSError:
                    pass
                self._f = None


class _LogSenke:
    """`sys.stdout` fuer die Dauer EINES Hintergrund-Jobs (E2c).

    Die Alt-Wege (anlernen.sammle, vorschlaege_person, pruefe_referenzen_lauf,
    core.ernte.ernte_event) drucken ihren Fortschritt mit `print` — sie haben kein
    `log=`-Argument, und sie bekommen auch keines: ihr Code bleibt unveraendert.
    `worker.py` fing das per dup2 ab (worker.py:615-631); das geht im Mehr-Job-Betrieb
    nicht mehr (W2-B1, die Umleitung gilt dem ganzen Prozess). Diese Senke sammelt
    stattdessen auf Python-Ebene: Teilstuecke bis zum Zeilenende, dann EINE Zeile ins
    Job-Log — sonst zerfiele ein `print(..., end="")`-Fortschrittsbalken in hunderte
    Zeilen."""

    def __init__(self, log):
        self.log = log
        self._rest = ""

    def write(self, text):
        self._rest += str(text)
        while "\n" in self._rest:
            zeile, self._rest = self._rest.split("\n", 1)
            if zeile.strip():
                self.log.zeile(zeile)
        return len(text)

    def flush(self):
        if self._rest.strip():
            self.log.zeile(self._rest)
        self._rest = ""

    def isatty(self):
        return False


# ----------------------------------------------------------------- Speicher-Messung
def _proc_mb(feld):
    """Ein Feld aus /proc/self/status in MB (-1 = nicht lesbar). Wortgleich
    worker._proc_mb — dieselbe Groesse, dieselbe Rechnung."""
    try:
        with open("/proc/self/status", encoding="ascii") as f:
            for z in f:
                if z.startswith(feld + ":"):
                    return int(z.split()[1]) // 1024
    except Exception:                                      # noqa: BLE001
        pass
    return -1


def rss_mb():
    return _proc_mb("VmRSS")


def vmhwm_mb():
    return _proc_mb("VmHWM")


def cgroup_stat():
    """Die cgroup-v2-Posten dieses Containers in MB. -> dict (leer = nicht lesbar)."""
    try:
        with open("/sys/fs/cgroup/memory.stat", encoding="ascii") as f:
            roh = dict(z.split()[:2] for z in f if len(z.split()) >= 2)
    except Exception:                                      # noqa: BLE001
        return {}
    aus = {}
    for k in ("anon", "file", "shmem"):
        if k in roh:
            aus[k] = int(roh[k]) // 1048576
    return aus


def fussabdruck_mb():
    """DER Speicher-Fussabdruck dieses Prozesses in MB — anon + cgroup-shmem.

    VmRSS allein LUEGT auf der iGPU: gemessen am 12.09. 1,9 GB RSS gegen 6,85 GB
    cgroup, weil die i915-Objekte der integrierten Grafik shmem-gestuetzt sind und
    im RSS des Prozesses nicht auftauchen (Gegenprobe: CPU-Kompilat 0,0 MB shmem,
    GPU-Kompilat 348,6 MB; Messfassung .suslik_tmp/gt5/proto_ram/). Genau darauf
    haette die alte rss_max_mb-Wache nie angeschlagen.

    EHRLICHE GRENZE, benannt: die cgroup ist die des CONTAINERS, nicht dieses
    Prozesses — laeuft noch etwas darin, zaehlt es mit. Solange der neue Worker
    der einzige grosse Rechner im Container ist, ist das die richtige Zahl; sonst
    ist sie eine Obergrenze. -1 = nicht lesbar, dann bleibt VmRSS."""
    s = cgroup_stat()
    if "anon" in s:
        return s["anon"] + s.get("shmem", 0)
    return rss_mb()


def cgroup_frei_mb():
    """Freier Speicher bis zur cgroup-Grenze, MemAvailable-artig; -1 = keine Grenze.
    EINE Quelle: die Rechnung von worker._cgroup_frei_mb (samt ihrer Begruendung,
    warum /proc/meminfo hier verboten ist und warum inactive_file abgezogen wird)."""
    from worker import _cgroup_frei_mb                     # noqa: PLC0415
    return _cgroup_frei_mb()


# ----------------------------------------------------------------- Job-argv lesen
# Die Vorgaben von analyze.py — je Wert mit der Fundstelle, an der er dort steht.
# SEIT E3.1 sind sie die FUELLUNG fehlender Job-Felder, nicht mehr das Register
# eines argv-Parsers: verifyd schickt jede Latte als Feld (`felder_lesen`), und was
# ein Aufrufer nicht schickt, bekommt hier den belegten Wert statt eines Absturzes.
ARGV_VORGABE = {
    # .540 K-Deckel: hoechstens so viele Sample-Frames je Ereignis, gleichmaessig
    # ueber die Cliplaenge (decode.sample_schritt). 0 = aus — und 0 ist hier
    # RICHTIG als Fuellwert: wer das Feld nicht schickt, bekommt das Verhalten von
    # vor .540, nie einen Deckel, den er nicht bestellt hat. Den Werkswert 240
    # setzt der Config-Store (verifyd.py), nicht diese Fuellung.
    "sample_deckel": 0,
    "fps_sample": 2.0,        # analyze.py:42
    "win_thresh": 0.40,       # analyze.py:43
    "urteil_kante": 0.0,      # analyze.py:45
    "urteil_guete_e": None,   # analyze.py:53   (-1 = „nicht gesetzt" -> STIMM_DEFAULT)
    "urteil_guete_t": None,   # analyze.py:54
    "blick_fenster_s": 45.0,  # analyze.py:67
    "urteil_anker": 0.45,     # analyze.py:72
    "urteil_pose": 0.0,       # analyze.py:91
    "fd_front_min": 0.85,     # analyze.py:95
    "fd_sharp_min": 1500.0,   # analyze.py:96
    "fd_det_max": 0.70,       # analyze.py:97
    "det_thresh": 0.5,        # analyze.py:98
}
# argv-Flagge -> Schluessel oben. Die Namen sind die von verifyd.run_analyze
# (verifyd.py:2036-2117), die Schluessel die von worker_kern.urteils_latten.
ARGV_FLAGGEN = {
    "--sample-deckel": "sample_deckel",                   # .540
    "--fps-sample": "fps_sample", "--win-thresh": "win_thresh",
    "--urteil-kante": "urteil_kante", "--urteil-guete-e": "urteil_guete_e",
    "--urteil-guete-t": "urteil_guete_t", "--blick-fenster": "blick_fenster_s",
    "--urteil-anker": "urteil_anker", "--urteil-pose": "urteil_pose",
    "--fd-front-min": "fd_front_min", "--fd-sharp-min": "fd_sharp_min",
    "--fd-det-max": "fd_det_max", "--det-thresh": "det_thresh",
}


def argv_lesen(argv):
    """Die analyze-argv eines Jobs -> {eids, labels, persons, dir, argv_fest}.

    Bewusst von Hand statt mit argparse: argparse wuerde bei einem unbekannten
    Schalter den PROZESS beenden (sys.exit) — in einem Dienst, der N Jobs haelt,
    waere das der Tod aller. Unbekannte Schalter werden hier gesammelt und mit dem
    Job beantwortet."""
    eids, labels, persons, out, unbekannt = [], [], [], None, []
    fest = dict(ARGV_VORGABE)
    koerper, debug = False, False
    kalib = {"deckel": 0, "data_dir": "", "kamera": ""}
    rest = list(argv)
    i = 0
    while i < len(rest):
        t = rest[i]
        if not t.startswith("--"):
            eids.append(t)
            i += 1
            continue
        if t in ARGV_FLAGGEN:
            schluessel = ARGV_FLAGGEN[t]
            w = float(rest[i + 1])
            # -1 heisst bei den zwei Guete-Schaltern „nicht gesetzt" (analyze.py:50-52);
            # urteils_latten erwartet dafuer None.
            if schluessel.startswith("urteil_guete") and w < 0:
                w = None
            fest[schluessel] = w
            i += 2
            continue
        if t in ("--labels", "--persons"):
            ziel = labels if t == "--labels" else persons
            i += 1
            while i < len(rest) and not rest[i].startswith("--"):
                ziel.append(rest[i])
                i += 1
            continue
        if t == "--dir":
            out = rest[i + 1]
            i += 2
            continue
        if t == "--kalib-deckel":
            kalib["deckel"] = int(float(rest[i + 1]))
            i += 2
            continue
        if t in ("--kalib-data-dir", "--kalib-kamera"):
            kalib[t[8:].replace("-", "_")] = rest[i + 1]
            i += 2
            continue
        if t == "--koerper":
            koerper = True
            i += 1
            continue
        if t == "--urteil-debug":
            debug = True
            i += 1
            continue
        if t in ("--koerper-rss-max-mb", "--timeline"):
            # bekannt, aber ohne Wirkung in dieser Etappe: der Koerper-Abnehmer haengt
            # am alten Frame-Verteiler (E3/E2c), --timeline ist reine Diagnose-Ausgabe.
            i += 2 if t == "--koerper-rss-max-mb" else 1
            continue
        unbekannt.append(t)
        i += 1
    return {"eids": eids, "labels": labels, "persons": persons, "dir": out,
            "argv_fest": fest, "koerper": koerper, "debug": debug, "kalib": kalib,
            "unbekannt": unbekannt}


def _clip_vod(job):
    """Der VOD-Schalter DIESES Jobs (E3.3, Bauplan 2f) -> True/False/None.

    Die Auslegung ist die des Hauses und steht genau einmal da: `clip_vod is not
    False` heisst „an, solange niemand ausdruecklich abschaltet" (verifyd.py:2171,
    :4343, worker.py:665). FEHLT das Feld ganz — ein aelterer Aufrufer, eine Probe,
    der Roundtrip —, wird hier NICHTS behauptet: `None` laesst `core.frames` seinen
    Prozess-Default nehmen, statt ihm ein `True` unterzuschieben, das der Aufrufer
    nie gesagt hat."""
    if "clip_vod" not in job:
        return None
    return job.get("clip_vod") is not False


def felder_lesen(job):
    """E3.1 (14.09.2026): die Job-OPTIONEN aus JOB-FELDERN — DER Weg im Dienst.

    Bis E2 schickte der Aufrufer eine analyze-ARGV und der Dienst zerlegte sie
    (`argv_lesen`). Das war der Kompromiss der Prototyp-Etappe und stand als offener
    Punkt im Kopf („EHRLICHE GRENZEN": die Vorgabewerte stehen dadurch ein zweites
    Mal da). Seit E3.1 uebergibt verifyd Felder; eine Kommandozeile wird zwischen
    zwei Prozessen nicht mehr gebaut und nicht mehr geparst.

    FELDER (die Namen sind die von worker_kern.urteils_latten, nicht die der alten
    Schalter — der Zwischenschritt „--urteil-guete-e" faellt damit ganz weg):
      eids/labels/persons/dir   wie die Positionen und --labels/--persons/--dir
      latten {schluessel: zahl} die Urteils-Latten; None heisst „nicht gesetzt"
      koerper (bool)            der Koerper-Abnehmer faehrt mit
      debug (bool)              Urteils-Debugzeilen
      kalib {deckel,data_dir,kamera}   der Kalibrier-Vorrat aus der Analyse

    UNBEKANNTE SCHLUESSEL fallen wie bei `argv_lesen` nicht still, sondern werden
    gesammelt und mit dem Job beantwortet — ein Dienst, der eine Vorgabe des
    Aufrufers stillschweigend verschluckt, rechnet mit anderen Latten als
    verlangt (das ist die K1-Klasse, nur eine Ebene tiefer).

    ARGV_VORGABE bleibt als FUELLUNG stehen und ist damit kein zweites Register
    mehr: verifyd schickt jede Latte, die es kennt; was fehlt (Probe, Kurzaufruf,
    aelterer Aufrufer), bekommt den dokumentierten analyze.py-Wert statt eines
    Absturzes."""
    fest = dict(ARGV_VORGABE)
    unbekannt = list(job.get("unbekannt_argv") or [])
    for k, w in (job.get("latten") or {}).items():
        if k not in ARGV_VORGABE:
            unbekannt.append(f"latte:{k}")
            continue
        if w is None:
            fest[k] = None                                 # „nicht gesetzt" (guete e/t)
            continue
        w = float(w)
        # -1 heisst bei den zwei Guete-Latten „nicht gesetzt" (analyze.py:50-52);
        # dieselbe Uebersetzung wie im argv-Weg, damit beide Wege dasselbe meinen.
        if k.startswith("urteil_guete") and w < 0:
            w = None
        fest[k] = w
    kal = job.get("kalib") or {}
    try:
        deckel = int(float(kal.get("deckel") or 0))
    except (TypeError, ValueError):
        deckel = 0
    return {"eids": list(job.get("eids") or []),
            "labels": list(job.get("labels") or []),
            "persons": list(job.get("persons") or []),
            "dir": job.get("dir"), "argv_fest": fest,
            "koerper": bool(job.get("koerper")), "debug": bool(job.get("debug")),
            "kalib": {"deckel": deckel,
                      "data_dir": str(kal.get("data_dir") or ""),
                      "kamera": str(kal.get("kamera") or "")},
            "unbekannt": unbekannt}


def argv_zu_job(argv):
    """Eine analyze-ARGV in die Job-FELDER uebersetzen — fuer die KOMMANDOZEILE.

    Der `--roundtrip`-Selbsttest bekommt seine Vorgaben als Kommandozeile (so ruft
    ihn tools/qs.sh, so rief ihn worker.py). Er uebersetzt sie hier EINMAL in
    Felder, statt dem Job-Weg einen zweiten Zweig zu geben: im Dienst gibt es seit
    E3.1 nur noch `felder_lesen`."""
    o = argv_lesen(argv)
    return {"eids": o["eids"], "labels": o["labels"], "persons": o["persons"],
            "dir": o["dir"], "latten": o["argv_fest"], "koerper": o["koerper"],
            "debug": o["debug"], "kalib": o["kalib"],
            "unbekannt_argv": o["unbekannt"]}


# ----------------------------------------------------------------- Latten
def latten_bauen(fest, log):
    """Die Urteils-Latten dieses Jobs plus die zwei LAUTEN Modell-Abschaltungen.

    Die Aufloesung selbst macht der Kern (worker_kern.urteils_latten — EINE Quelle,
    sie steht dort Zeile fuer Zeile wie analyze._latte_aufloesen). Was hier
    dazukommt, ist das Gegenstueck, das der Kern nicht hat und das die Invariante
    „Messbarkeit vor Stimme" (CLAUDE.md) ausdruecklich verlangt:

      fail-closed je FUND, aber fail-open je MODELL.

    Fehlt ein Messmodell, setzt der VERBRAUCHER seine Latte LAUT auf 0 (analyze.py:
    125-129 fuer die Guete, :137-153 fuer die Pose) — sonst schaltet eine fehlende
    ONNX-Datei die ganze Erkennung still ab. -> (lat, aus, pose_aus)"""
    pose_roh = max(0.0, float(fest.get("urteil_pose") or 0.0))
    lat = wk.urteils_latten({"argv_fest": fest})
    aus = ""
    if (lat["guete_e"] > 0 or lat["guete_t"] > 0):
        try:
            da = guete_mod.verfuegbar()
        except Exception as e:                             # noqa: BLE001
            da, _ = False, e
        if not da:
            aus = "guete-modelle nicht verfuegbar"
            log.zeile(f"URTEILS-VORFILTER AUS: {aus}")     # Wortlaut analyze.py:128
            lat["guete_e"] = lat["guete_t"] = 0.0
            # Der Kern haette die Pose mit den Guete-Latten zusammen abgeschaltet
            # (urteils_latten, analyze.py:197-201); das holen wir hier nach.
            if lat["pose"] > 0:
                lat["pose"] = 0.0
    pose_aus = ""
    if pose_roh > 0 and lat["pose"] <= 0:
        pose_aus = ("guete-latten aus — es entstehen keine stimm-kandidaten "
                    "und damit keine pose-messung")
        log.zeile(f"POSE-STIMM-SIEB AUS: {pose_aus}")      # Wortlaut analyze.py:152
    elif lat["pose"] > 0:
        try:
            from core.livewache import pose_verfuegbar     # noqa: PLC0415
            pose_da = pose_verfuegbar()
        except Exception as e:                             # noqa: BLE001
            pose_da = False
            log.zeile(f"   (pose-verfuegbarkeit nicht pruefbar: {type(e).__name__})")
        if not pose_da:
            pose_aus = "pose-modell nicht verfuegbar"
            log.zeile(f"POSE-STIMM-SIEB AUS: {pose_aus}")
            lat["pose"] = 0.0
    return lat, aus, pose_aus


# ----------------------------------------------------------------- Referenzen
REFCACHE_META = "§meta"


def _refcache_meta(z):
    """Meta-Block lesen; Alt-Caches mit dem frueheren Key 'meta' bleiben lesbar.
    Wortgleich analyze._refcache_meta (analyze.py:238-241)."""
    return json.loads(str(z[REFCACHE_META if REFCACHE_META in z.files else "meta"]))


def _refcache_schreiben(cache, meta, refs):
    """refcache atomar schreiben — tmp + flush + fsync + os.replace, wortgleich
    analyze._refcache_schreiben (analyze.py:244-260): Leser sehen nie eine halb
    geschriebene npz, ein Abbruch laesst nur die tmp-Datei zurueck."""
    tmp = f"{cache}.tmp-{os.getpid()}"
    try:
        with open(tmp, "wb") as f:
            np.savez(f, **{REFCACHE_META: json.dumps(meta)}, **refs)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, cache)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _refs_bauen(master, want, alle, modell, log):
    """Die Referenz-Matrizen aus dem Master rechnen — der Rumpf von
    analyze.load_refs (analyze.py:283-311), Schritt fuer Schritt:
    Vorrats-Referenzen kommen ueber core.refbeiwert (embed() findet auf der kleinen
    Datei gemessen in 28 von 40 Faellen kein Gesicht — ein Neuaufbau ohne diesen
    Vorrang schriebe den Verlust in den Cache zurueck, Konzept-QS W1.1), alles
    andere ueber den Embedder. -> (refs, zeilen)"""
    import cv2                                             # noqa: PLC0415
    from core.refbeiwert import beiwerte as _bw            # noqa: PLC0415
    bw, fremd = _bw(master, modell)
    if fremd:
        log.zeile(f"   ({fremd} Vorrats-Referenz(en) mit fremdem Modell-Beiwert — unbrauchbar)")
    emb = face_audit.Embedder()
    refs, zeilen = {}, {}
    for p in alle:
        V, N = [], []
        for f in want[p]:
            b = bw.get((p, f))
            if b is not None:
                V.append(np.asarray(b["emb"], np.float32))
                N.append(f)
                continue
            img = cv2.imread(os.path.join(master, p, f))
            if img is None:
                continue
            v = emb.embed(img)
            if v is not None:
                V.append(v.astype(np.float32))
                N.append(f)
        refs[p] = np.asarray(V, dtype=np.float32)
        zeilen[p] = N
        log.zeile(f"   {p}: {len(V)} Vektoren")
    return refs, zeilen


def referenzen_laden(pfad, log, master=None):
    """Referenzen laden — MIT SELBSTHEILUNG (W1-B3).

    Der Kern (worker_kern.referenzen_laden) wirft, wenn der Cache fehlt oder zu
    einem anderen Modell gehoert. Fuer einen Mess-Prototyp ist das richtig; fuer
    einen DIENST nicht: der Cache ist ein regenerierbares Artefakt, und es gibt
    Wege, die ihn absichtlich wegwerfen (anlernen.refcache_entfernen, Modellwechsel
    im UI). Faellt der Worker darueber aus, steht die Erkennung still, obwohl alles
    Noetige auf der Platte liegt.

    Gepruefte Bedingungen, wortgleich analyze.load_refs (analyze.py:263-315):
      1. Der Cache wird IMMER ueber ALLE Master-Personen gefuehrt (Prod-Fund
         21.08.: ein Lauf mit Teil-Personenliste schrieb ihn mit dieser Teilmenge
         zurueck und nahm Ernte und Sichtung ihre Referenzen).
      2. Er gilt nur, wenn '§modell' zum konfigurierten Modell passt UND die
         DATEI-LISTE je Person noch stimmt (analyze.py:278) — eine geloeschte oder
         hinzugekommene Referenz entwertet ihn.
      3. Sonst: neu rechnen und atomar zurueckschreiben. Ein nicht schreibbarer
         Cache ist kein Abbruch, nur ein langsamerer naechster Lauf.
    -> (alle, mit_refs, erk) in der Form, die der Kern erwartet."""
    from sync_refs import MASTER, master_stand             # noqa: PLC0415
    master = master or MASTER
    modell = face_audit.aktuelles_modell()
    idx = master_stand()
    if not idx:
        # Wortlaut wie analyze.py:229 — tools/qs.sh:12039 greift genau diesen Text,
        # und er unterscheidet „Testmaschine ohne Referenzen" von „Erkennung kaputt".
        raise SystemExit("FEHLER: Referenz-Master leer (verify_data/refs) — "
                         "sync_refs.py import ausfuehren.")
    alle = sorted(idx)
    want = {p: idx[p] for p in alle}
    refs, neu = None, False
    if os.path.exists(pfad):
        try:
            z = np.load(pfad, allow_pickle=True)
            meta = _refcache_meta(z)
            if (str(meta.get("§modell", "")) == modell
                    and all(meta.get(p) == want[p] for p in alle)):
                refs = {p: (z[p] if p in z.files else np.zeros((0, 512), np.float32))
                        for p in alle}
                log.zeile("Referenz-Embeddings aus Cache.")
            else:
                grund = ("Modell" if str(meta.get("§modell", "")) != modell
                         else "Datei-Liste")
                log.zeile(f"   (refcache passt nicht mehr: {grund} — wird neu berechnet)")
        except Exception as e:                             # noqa: BLE001
            log.zeile(f"   (refcache unlesbar: {e} — wird neu berechnet)")
    if refs is None:
        log.zeile("Referenz-Embeddings werden berechnet (einmalig, dann gecacht) ...")
        refs, zeilen = _refs_bauen(master, want, alle, modell, log)
        neu = True
        try:
            _refcache_schreiben(pfad, {**want, "§modell": modell, "§rows": zeilen}, refs)
        except Exception as e:                             # noqa: BLE001
            log.zeile(f"   (refcache nicht schreibbar: {e} — wird beim naechsten Lauf neu berechnet)")
    # Ab hier die Aufbereitung des Kerns (worker_kern.referenzen_laden:617-630):
    # EINE Matrix, je Person auf die groesste Anzahl aufgefuellt durch Wiederholen
    # der ersten Zeile (aendert ihr Maximum nicht).
    mats = {p: np.asarray(refs[p], np.float32) for p in alle if len(refs.get(p, []))}
    mit_refs = sorted(mats)
    if not mit_refs:
        raise SystemExit("FEHLER: keine einzige Referenz mit Vektoren — "
                         "kein Urteil moeglich")
    je = max(len(m) for m in mats.values())
    matrix = np.concatenate(
        [np.concatenate([mats[p], np.repeat(mats[p][:1], je - len(mats[p]), axis=0)])
         for p in mit_refs]).astype(np.float32)
    erk = {"refs": matrix, "refs_t": np.ascontiguousarray(matrix.T),
           "personen": len(mit_refs), "je_person": je, "neu_gebaut": neu}
    return alle, mit_refs, erk


# ----------------------------------------------------------------- Kompilat-Probe (E2d)
def _datei_md5(pfad):
    """md5 einer Datei, stueckweise gelesen. -> Hex (12) oder None."""
    import hashlib                                          # noqa: PLC0415
    try:
        h = hashlib.md5()
        with open(pfad, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()[:12]
    except OSError:
        return None


def eich_umfeld(engine):
    """WOGEGEN die Eichmarke gilt. Aendert sich hier etwas, sind andere Zahlen RICHTIG —
    dann wird die Marke erneuert statt Alarm geschlagen. Alles wird ABGELESEN, nichts
    behauptet: Fassung und Geraetename kommen aus OpenVINO, die Modelle ueber ihren
    Datei-md5 (ein getauschtes ONNX ist ein anderes Modell, auch bei gleichem Namen),
    der Code ueber den md5 der zwei Dateien, die den Graphen bauen."""
    aus = {"engine": getattr(engine, "name", "?")}
    try:
        # 0.1.0.542: NIE selbst importieren, nur nehmen was schon geladen IST.
        # Ein `import openvino` zerstoert den OpenVINO-EP der onnxruntime fuer den
        # Rest des Prozesses (ABI-Konflikt beider OV-Laufzeiten, gemessen 17.09. am
        # .541-cpu-Image) — und dieser Prozess baut seine Sessions teils erst
        # spaeter (engine_cpu._sitzung je Stufe/Geometrie). Wo OpenVINO die
        # Rechenquelle IST (engine_ov), liegt das Modul ohnehin in sys.modules;
        # wo nicht (engine_cpu/cuda/migraphx), gibt es hier auch nichts abzulesen.
        _ov = sys.modules.get("openvino")                   # noqa: PLC0415
        if _ov is None:
            raise LookupError("openvino not loaded in this process (by design)")
        aus["openvino"] = _ov.__version__
        aus["geraet"] = str(engine.core.get_property(
            getattr(sys.modules[type(engine).__module__], "GERAET", "GPU"),
            "FULL_DEVICE_NAME"))
    except Exception as e:                                  # noqa: BLE001
        aus["geraet"] = f"?{type(e).__name__}"
    try:
        aus["modelle"] = {k: _datei_md5(p)
                          for k, p in sorted(wk.vorgabe_pfade(wk.rec_spec()).items())}
        aus["modelle"]["det_10g"] = _datei_md5(wk.modell_pfad("det_10g"))
    except Exception as e:                                  # noqa: BLE001
        aus["modelle"] = f"?{type(e).__name__}"
    aus["code"] = {n: _datei_md5(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              n))
                   for n in ("engine_ov.py", "engine_cuda.py", "worker_kern.py")}
    return aus


def probe_vergleich(soll, ist):
    """Zwei Proben vergleichen. -> (urteil, Liste der Befunde)

    ZWEI SCHAERFEN, und der Unterschied ist Absicht (CLAUDE.md „Messbarkeit vor Stimme":
    fail-closed dort, wo ein falscher Wert still einen NAMEN kostet):
      * Die ERKENNUNGS-Stufe wird als ZAHL geprueft — Kosinus des Pruef-Embeddings und
        Feature-Norm gegen EICH_COS_MAX/EICH_NORM_MAX. Sie traegt das Urteil; eine
        Abweichung hier ist der Blocker vom 13.09. und muss den Prozess anhalten.
      * Die uebrigen Stufen (det, fd, e, t, p) werden als Fingerabdruck verglichen und
        eine Abweichung wird LAUT GEMELDET, aber nicht toedlich. Grund, gemessen: ihre
        Abnehmer runden auf 2-3 Stellen (front, sharp, pkopf), und ueber alle E2d-Laeufe
        bewegte sich dort nichts — waehrend die r-Stufe sich bewegte. Ein toedlicher
        Fingerabdruck-Vergleich waere hier eine Fehlalarm-Maschine ohne Gegenwert."""
    import math                                             # noqa: PLC0415
    befunde, hart = [], False
    for k in ("det", "fd", "e", "t", "p"):
        if soll.get(k) != ist.get(k):
            befunde.append(f"{k}: {soll.get(k)} -> {ist.get(k)}")
    sn, inn = soll.get("r_norm") or [], ist.get("r_norm") or []
    if len(sn) == len(inn) and sn:
        dn = max(abs(float(x) - float(y)) for x, y in zip(sn, inn))
        if dn > EICH_NORM_MAX:
            hart = True
            befunde.append(f"r_norm: {sn} -> {inn} (|d| {dn:.4f} > {EICH_NORM_MAX})")
    else:
        hart = True
        befunde.append(f"r_norm: Form {sn} -> {inn}")
    a, b = soll.get("_r_emb") or [], ist.get("_r_emb") or []
    if len(a) == len(b) and a:
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        cos = sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0
        if 1.0 - cos > EICH_COS_MAX:
            hart = True
            befunde.append(f"r_emb: 1-cos {1.0 - cos:.3e} > {EICH_COS_MAX:.0e}")
    else:
        hart = True
        befunde.append("r_emb: fehlt oder andere Laenge")
    if hart:
        return "abweichung", befunde
    return ("hinweis" if befunde else "ok"), befunde


# ----------------------------------------------------------------- Decoder-Wache
class DecoderWache:
    """Die Vollstaendigkeits-Wache EINES Jobs (W1-M9).

    Der Engine-Decoder der Prototypen zaehlte NICHTS — `frames_nv12` lieferte
    Frames und schwieg. Fuer eine Messung reicht das (der Clip ist bekannt), fuer
    den Dienst nicht: analyze.py meldet seit W1 `frames_gelesen`/`frames_soll`/
    `frames_fehlen`, verifyd wertet unter 50 % lesbar als Fehler
    (verifyd.py:13952-13993), und die Concealment-Klasse (ffmpeg dekodiert einen
    kaputten Clip mit rc=0 und vollem Zaehler DURCH, gemessen 61 % der Samples um
    median 33 Graustufen verfaelscht) sieht ohne die stderr-Zeilen niemand.

    Diese Klasse traegt deshalb dieselben Attributnamen wie decode.FrameIter und
    laesst die drei URTEILS-FORMELN von dort rechnen (core.frames._formel, dieselbe
    Hausregel wie beim Frame-Verteiler: eine zweite, driftende Formel gibt es
    nicht). Neu ist allein, WOHER die Zahlen kommen."""

    def __init__(self, clip, schritt):
        meta = decode._probe(clip) or {}
        self.soll = meta.get("pakete")       # Gesamt-Pakete des Clips (Wache-Basis)
        self.step = int(schritt)
        self.samples = 0                     # gelieferte Sample-Frames
        # .534 (B5): WANN das erste Bild kam. Die Zahl, die im Feld gefehlt hat —
        # zwischen „Clip liegt da" und „es wird gerechnet" steckt der
        # Decoder-Start (und auf Karten der Rueckfall von HW auf SW).
        self.t_erstes = None
        self.roh = {}                        # von nv12_strom gefuellt (kette/rc/fehler)
        self.teilabbruch = None              # Kette starb MITTEN im Clip (s. EngineTor)

    @property
    def decoder_fehler(self):
        return int(self.roh.get("decoder_fehler") or 0)

    @property
    def kette(self):
        return self.roh.get("kette")

    @property
    def hwdec_fallback(self):
        """Ist die Hardware-Kette ausgefallen und Software eingesprungen (E2d)?
        Die Engine setzt das Feld in `roh`; der Name ist der von decode.FrameIter, weil
        es dieselbe Sache ist."""
        return bool(self.roh.get("hwdec_fallback"))

    @property
    def hwdec_grund(self):
        return self.roh.get("hwdec_grund")

    @property
    def gelesen(self):
        """Fortschritt in ORIGINAL-Indizes, wie decode.FrameIter.gelesen (i + 1 des
        letzten gelieferten Frames, decode.py:203) — das ist die Zahl, die als
        `frames_gelesen` in die Akte geht."""
        return (self.samples - 1) * self.step + 1 if self.samples else 0

    @property
    def _soll_samples(self):
        return clipcache._formel(decode.FrameIter, "_soll_samples")(self)

    @property
    def verlust_pct(self):
        return clipcache._formel(decode.FrameIter, "verlust_pct")(self)

    @property
    def unvollstaendig(self):
        return clipcache._formel(decode.FrameIter, "unvollstaendig")(self)


class EngineTor:
    """Die Engine, wie EIN Job sie sieht: derselbe Decoder, aber mit Wache davor.

    Der Kern ruft `engine.frames(...)` — mehr braucht event_rechnen von der Engine
    nicht (worker_kern.py:924). Dieses Tor schiebt sich dazwischen, zaehlt die
    gelieferten Frames und reicht der Engine den wache-dict durch. Der Kern bleibt
    dabei unveraendert; er merkt vom Tor nichts."""

    def __init__(self, engine, wache):
        self._engine, self._wache = engine, wache
        self._mit_wache = "wache" in inspect.signature(engine.frames).parameters

    def frames(self, clip, W, H, schritt):
        """Die Frames dieses Jobs, gezaehlt — und mit der TEILABBRUCH-Regel.

        Warum die Regel sein MUSS (gemessen 13.09. an einem verfaelschten
        gt5-Clip): stirbt die VAAPI-Kette MITTEN im Clip, endet ffmpeg mit rc=251
        NACH Teillieferung (16 von 23 Samples, 5 Decoder-Zeilen). worker_kern.
        nv12_strom wirft daraufhin — richtig fuer einen Messlauf („kein
        Rueckfall"), falsch fuer den Dienst: die schon gelieferten Frames sind
        beim Verbraucher, und analyze.py hat diesen Fall seit der W1-Wache
        ausdruecklich als „urteile den lesbaren Teil, aber FLAGGE ihn" behandelt
        (decode.py:244-252 samt Herleitung, analyze.py:799-809). Ohne die Regel
        verlaere der neue Worker genau diese Ereignisse ganz, statt sie
        gekennzeichnet zu urteilen.

        0 Frames geliefert = der Fehler bleibt ein Fehler und fliegt weiter; dann
        gibt es ohnehin keine results-Zeile (W1-M11)."""
        w = self._wache
        strom = (self._engine.frames(clip, W, H, schritt, wache=w.roh)
                 if self._mit_wache else self._engine.frames(clip, W, H, schritt))
        try:
            for s in strom:
                if w.samples == 0:
                    w.t_erstes = time.monotonic()      # .534 (B5): das erste Bild
                w.samples += 1
                yield s
        except RuntimeError as e:
            if w.samples == 0:
                raise
            w.teilabbruch = str(e)[:400]

    def __getattr__(self, name):
        return getattr(self._engine, name)


# ----------------------------------------------------------------- Results-Kontrakt
def detektionen_bauen(zeilen):
    """Die `detektionen`-Liste der Akte (analyze.py:943-953).

    VOLLSTAENDIG, W1-M1: jede Roh-Detektion, in derselben Reihenfolge wie gerechnet.
    Daran haengen faces_geprueft, max_bw, no_person, szenarien.gesicht_gut_zaehlen
    und — ueber den Index — stimm_idx.

    EIN UNTERSCHIED, bewusst: analyze schreibt guete_e/guete_t/pkopf nur fuer
    STIMM-Kandidaten („sonst waechst die Akte um jede Grasnarbe", analyze.py:934).
    Hier gilt die Regel des Konzepts — „Guete-Werte wo gemessen" (§3). Das ist
    dasselbe Sparziel auf dem neuen Weg: Fehldetektionen verlassen die Kaskade VOR
    der e-Stufe, eine Grasnarbe bekommt also gar keinen Wert."""
    aus = []
    for f in zeilen:
        d = {"t": round(f["zeit_s"], 1), "bw": f["bw"], "bh": f["bh"],
             "front": None if f["front"] is None else round(f["front"], 2),
             "det": round(f["det"], 2),
             "sharp": None if f["sharp"] is None else round(f["sharp"], 0),
             "fd": f["fd"]}
        if f["e"] is not None or f["t"] is not None or f["p"] is not None:
            d["guete_e"] = None if f["e"] is None else round(float(f["e"]), 3)
            d["guete_t"] = None if f["t"] is None else round(float(f["t"]), 3)
            d["pkopf"] = None if f["p"] is None else round(float(f["p"]), 3)
        aus.append(d)
    return aus


# Die persons-Schluessel, die ohne Leser sind und deshalb nicht mehr geschrieben
# werden (Kopf, ABBAU; Beleg Inventur §A.13).
PERSONS_ABBAU = ("median", "n", "n_ge40", "n_ge50", "best_wh", "best_det",
                 "best_t", "blick_t0")


def persons_fuer_akte(persons_voll, idx_karte):
    """Die persons-Kennwerte, wie sie in die Akte gehen.

    ZWEI Eingriffe gegenueber dem, was der Kern liefert:

    1. ABBAU: die Kennwerte ohne Leser fallen weg (PERSONS_ABBAU). Der Kern
       rechnet sie weiter — sie kosten nichts und der Bildvorrat braucht best_t
       fuer den Dateinamen —, sie stehen nur nicht mehr in der Akte.

    2. stimm_idx WIRD UMGERECHNET. Das ist ein echter Kontraktbruch der v8-Basis,
       gefunden beim Feld-fuer-Feld-Abgleich: worker_kern.zusammenfassen filtert
       seine Zeilen zuerst auf die Kaskaden-Ueberlebenden (`sc is not None`,
       worker_kern.py:1054) und zaehlt die Indizes DARIN. analyze zaehlt sie in
       `faces` — also in genau der Liste, die als `detektionen` in der Akte landet
       (analyze.py:869). Wer den Index spaeter benutzt, greift ins Leere:
       core.anwesenheit.marge_urteil trennt ueber stimm_idx + Detektions-
       Zeitstempel, ob zwei Kandidaten DASSELBE Gesicht deuten oder zwei Menschen
       sind (core/anwesenheit.py:524-542), und verifyd liest dazu
       `detektionen[stimm_idx].t` (verifyd.py:13952-13993). Mit der falschen
       Indexbasis urteilt die Marge-Sperre ueber fremde Gesichter.
       `idx_karte` ist die Abbildung Ueberlebenden-Index -> Index in detektionen."""
    aus = {}
    for person, rec in persons_voll.items():
        d = {k: v for k, v in rec.items() if k not in PERSONS_ABBAU}
        if "stimm_idx" in d:
            d["stimm_idx"] = [idx_karte[i] for i in d["stimm_idx"]]
        aus[person] = d
    return aus


def results_zeile(label, eid, zeilen, persons, wache, lat, stat, profil,
                  samples_moeglich=None, sample_deckel=0):
    """EINE results.jsonl-Zeile, Feld fuer Feld und in der REIHENFOLGE von
    analyze.py:940-1003. Die Reihenfolge ist kein Selbstzweck: die Akte wird
    gelesen, verglichen und von Menschen begutachtet, und ein Diff gegen Bestands-
    zeilen soll auf Feld-Unterschiede zeigen statt auf Umsortierung."""
    fd_n = sum(1 for f in zeilen if f["fd"])
    z = {"label": label, "source": eid, "faces": len(zeilen),
         "faces_geprueft": len(zeilen) - fd_n,
         "max_bw": max((f["bw"] for f in zeilen if not f["fd"]), default=0),
         "detektionen": detektionen_bauen(zeilen),
         "frames_gelesen": wache.gelesen, "frames_soll": wache.soll}
    # .540 DAS ZAHLENPAAR DES SAMPLE-BUDGETS. Bis hier stand die WIRKLICHE Zahl
    # abgetasteter Frames in KEINER Akte — nur im Klartext-Kopf der analyze.log
    # („=== <Kamera> (<eid>) — N Frames"), und `frames_gelesen`/`frames_soll`
    # meinen etwas anderes (Original-Frame-Index bzw. Paketzahl, also die
    # Clip-Laenge). Die K-Auswertung vom 17.09. musste die Zahl fuer den
    # Feld-Bestand deshalb aus `step` REKONSTRUIEREN. Das Feld schliesst die
    # Luecke und ist zugleich die Grundlage der spaeteren Auto-Kalibrierung:
    #   samples            wirklich abgetastete Frames (immer)
    #   samples_moeglich   was das Zeitraster allein ergeben haette (wenn die
    #                      Paketzahl bekannt war)
    #   sample_deckel      NUR gesetzt, wenn der Deckel wirklich gegriffen hat —
    #                      seine blosse Anwesenheit heisst „hier wurde gekappt"
    # Additiv und nur vorwaerts: Leser greifen per .get() zu, Bestandszeilen
    # bleiben unveraendert lesbar (dieselbe Politik wie Schema 3).
    z["samples"] = wache.samples
    if samples_moeglich is not None:
        z["samples_moeglich"] = int(samples_moeglich)
        if int(sample_deckel or 0) > 0 and wache.samples < int(samples_moeglich):
            z["sample_deckel"] = int(sample_deckel)
    if wache.unvollstaendig:
        z["frames_fehlen"] = True
    if wache.decoder_fehler:
        z["decoder_fehler"] = wache.decoder_fehler
    z["urteil_guete"] = {"e": lat["guete_e"], "t": lat["guete_t"],
                         "pose": lat["pose"], "kante": lat["urteil_kante"],
                         "anker": lat["urteil_anker"],
                         "win_thresh": lat["win_thresh"],
                         **stat}
    z["profil"] = profil
    z["persons"] = persons
    return z


# ----------------------------------------------------------------- Wachen
class SpeicherWache:
    """Die PROZESS-Speicher-Wache (W2-B12/B13/B18, Konzept §2).

    Drei Unterschiede zur In-Job-Wache von worker.py, alle drei gemessen begruendet:

    1. SIE MISST anon + cgroup-shmem, nicht VmRSS (s. fussabdruck_mb) — auf der
       iGPU ist VmRSS um den Faktor 3 zu niedrig, die alte Wache haette bei einem
       echten Speicherleck nie ausgeloest.
    2. SIE IST EINE PROZESS-WACHE, keine Job-Wache. Bei N Rechenstraengen ist die
       Zuordnung von Speicher zu einem Job Schaetzung; deshalb wird hier nichts
       geschaetzt. ZWEI STUFEN, seit E2d (14.09.) in dieser Reihenfolge:
       * Fussabdruck ueber der Politik-Grenze -> `Dienst.ende_bitten`: der Prozess
         geht GEORDNET, sobald kein Job mehr offen ist. Das kostet keinen Job.
       * Container fast voll (Wachstum je Takt >= freier Rest) -> `abbruch_alle`:
         ALLE offenen Jobs als FREMDVERSCHULDET (`fremdverschuldet: true` in der
         Antwort, mit Job-Id) — W2-B4/B7: sonst stuenden unschuldige Ereignisse
         nach drei Kollisionen auf `tot`, weil der Nachhol-Zaehler sie mitzaehlt.
         Hart, weil der OOM-Killer des Kerns nicht auf den letzten Job wartet.
    3. Die Politik-Grenze kommt aus dem Job-Feld `fussabdruck_max_mb` — und
       AUSDRUECKLICH NICHT aus `rss_max_mb`. Das ist der Fehler, den diese Wache im
       eigenen Gate am 13.09. gemacht hat: sie nahm den alten Wert (4096, aus
       worker_rss_max_mb) und maass dagegen den neuen Fussabdruck. Der ist auf der
       iGPU um ein Mehrfaches groesser als VmRSS — der Prototyp braucht gemessen
       3,9-4,9 GiB —, also riss die Wache SOFORT und buchte drei unschuldige Jobs
       als fremdverschuldet. Eine Zahl, die fuer ein anderes Mass geeicht ist, darf
       nicht auf ein neues uebertragen werden (dieselbe Klasse wie die
       Migrations-Klemme W2-B16: 4 Prozesse sind nicht 4 Threads). Fehlt das Feld,
       bleibt die Politik-Regel AUS — laut gesagt — und es wacht nur die
       cgroup-Regel. E3 liefert den Wert aus der Speicher-Formel.
       NACHTRAG .528 (Feldfund NB-Abnahme 14.09.): DIESELBE Uebertragung ist am
       anderen Ende noch einmal passiert, diesmal in der Formel selbst. Auf
       Backends, deren Formel Kartenspeicher rechnet (cuda/cpu/migraphx), gab
       `gpubudget.wache_grenze_mb` bis .527 die KONFIGURIERTE worker_rss_max_mb
       als `fussabdruck_max_mb` weiter — eine Je-Worker-Zahl (4096, geeicht auf
       VmRSS) gegen genau dieses Container-Mass. Auf dem CUDA-Notebook trug der
       Container ohne Worker schon 3310 MB; der Geometriebau eines 4K-Clips kam
       auf 5108 MB und die Wache schoss den Worker im Catch-up-Takt alle 600 s
       geordnet ab, ohne dass irgendetwas leckte. Seit .528 RECHNET
       `gpubudget.wache_grenze_rechnung` die Grenze dort aus gemessenen
       Container-Posten (Dienst + Live-Engine + Waechter-Decoder, s.
       CONTAINER_RAM_POSTEN) PLUS dem konfigurierten Je-Worker-Budget; die
       Quelle heisst dann `config+posten`, und die Posten stehen in /health.
       NACHTRAG .529 (Feldvorfall Feldtester-Anlage 15.09.): diese Summe haengt
       an der WAECHTERZAHL und am Budget, nicht an der Maschine. Mit fuenf
       Waechtern stand sie bei 10350 MB, der Container hielt 10384 und die Wache
       fuhr den Worker geordnet herunter — auf einem Wirt mit rund 48 GB RAM.
       Ist der Maschinen-RAM lesbar, ist die Grenze seitdem Maschine minus
       Reserve (Quelle `wirt-reserve`); die Postensumme bleibt der ERSATZ fuer
       Container ohne lesbares Speicher-Limit, und ein bewusst gesetzter
       `worker_rss_max_mb` schlaegt beides (Quelle `config`).
       Die Regel dieses Absatzes bleibt damit dieselbe: was hier ankommt, muss
       fuer DIESES Mass gerechnet sein.

    .531 — ZWEI MASSE AUF CUDA: neben dem Container-Fussabdruck (anon+shmem)
    fuehrt diese Wache alle 2 s gemerkt den KARTENWEIT freien Speicher mit. Der
    Anteil des eigenen Prozesses ist im Container nicht verlaesslich zuordenbar;
    was die Karte meldet, ist die Gesamtlage — und genau die zeigt FREMDEN Druck,
    gegen den ein eigener Deckel nichts ausrichtet. Die beiden Masse werden nie
    gegeneinander gerechnet: Kartenspeicher ist kein Systemspeicher, und diese
    Uebertragung ist in diesem Modul schon zweimal teuer gewesen (s. o.).

    EHRLICHE GRENZEN: die cgroup umfasst den ganzen Container (s. fussabdruck_mb);
    die Wache tastet im Takt ab, eine einzelne Allokation schneller als ein
    Intervall faengt nur der Kernel; und sie senkt keinen Bedarf — sie macht den
    Schaden endlich und laut."""

    def __init__(self, dienst, takt_s=WACHE_TAKT_S):
        self.dienst = dienst
        self.takt = float(takt_s)
        self.spitze = -1
        self.grenze = 0                       # MB, 0 = Politik unbekannt
        # .534 (B3): die GRUNDLAST des Containers, wie der Dienst sie gerechnet
        # hat (Job-Feld `fussabdruck_grundlast_mb`). Sie ist kein Budget und
        # keine Schwelle — sie ist der Abzugsposten, ohne den aus dem gemessenen
        # Maximum kein Vorschlag je Strang wird. 0 = der Dienst hat keinen
        # gerechnet (Intel-Zweig, kein Container-Mass), dann gibt es auch keinen
        # Vorschlag und das Feld bleibt leer statt zu raten.
        self.grundlast = 0
        self._stop = threading.Event()
        self._t = None
        self._gemeldet = False
        self._alt_gemeldet = False            # Hinweis auf das alte rss_max_mb: einmal
        # --- .531: DAS ZWEITE MASS. Auf CUDA fuehrt diese Wache den kartenweiten
        # freien Speicher MIT — gemerkt, mit Alter, im eigenen Takt. Der Anteil des
        # EIGENEN Prozesses ist im Container nicht verlaesslich zuordenbar; was die
        # Karte sagt, ist die Gesamtlage, und genau die zeigt FREMDEN Druck.
        self._karte = {"mb": 0, "gesamt": 0, "ts": 0.0, "fehl": 0,
                       "grund": "noch_nicht_gemessen"}
        self._karte_schloss = threading.Lock()
        self._karte_gemeldet = False
        # --- .532: DER EIGENE ANTEIL. Die Karten-Sonde oben sagt die
        # GESAMTLAGE; was davon dieser Prozess haelt, stand bisher nirgends —
        # und genau das fehlte, als im Feld der eigene Deckel voll war, die
        # Karte aber noch 2 GB frei hatte. Gemessen wird ueber
        # `--query-compute-apps`, gefiltert auf die eigene pid. EHRLICHE
        # GRENZE: ob der Treiber im Container die CONTAINER-pid meldet, ist
        # eine Eigenschaft von Treiber und Laufzeit — hier gemessen ja
        # (Labor 15.09.), zugesagt ist es nicht. Findet sich kein Eintrag,
        # steht `None` da und nicht 0: 0 hiesse „belegt nichts".
        self._eigen = {"mb": None, "vorher": None, "max": 0, "ts": 0.0,
                       "grund": "noch_nicht_gemessen", "gemeldet": False}
        self._eigen_schloss = threading.Lock()

    def grenze_melden(self, job):
        """Die Politik-Grenze eines Jobs anmelden (Feld `fussabdruck_max_mb`, s. o.).
        Es gilt die GROESSTE angemeldete Grenze: sie ist die Zusage des Dienstes an
        den PROZESS, nicht an den Job — eine kleinere Zusage eines zweiten Jobs darf
        den ersten nicht nachtraeglich enger machen."""
        try:
            mb = int(float(job.get("fussabdruck_max_mb") or 0))
        except (TypeError, ValueError):
            mb = 0
        if mb > self.grenze:
            self.grenze = mb
        # .534: derselbe Weg, dieselbe Regel („die groesste angemeldete gilt")
        # fuer den Grundlast-Posten. Er wandert mit, weil dieser Prozess die
        # Waechterzahl nicht kennt und sie auch nicht raten soll — genauso, wie
        # der Eich-Schluessel seit .531 mitwandert.
        try:
            gl = int(float(job.get("fussabdruck_grundlast_mb") or 0))
        except (TypeError, ValueError):
            gl = 0
        if gl > self.grundlast:
            self.grundlast = gl
        if not mb and not self._alt_gemeldet and job.get("rss_max_mb"):
            self._alt_gemeldet = True
            prozess_log(
                f"job carries rss_max_mb={job['rss_max_mb']} — that is a VmRSS limit, "
                f"and this guard measures anon+shmem, which is a different quantity "
                f"(measured 12.09.: 1.9 GB RSS vs 6.85 GB cgroup on the iGPU). The "
                f"policy rule therefore stays OFF; only the cgroup rule guards. E3 "
                f"passes fussabdruck_max_mb from the memory formula.")

    def karte_frei_mb(self, frisch=False):
        """Der kartenweit freie Speicher, GEMERKT (.531). -> (mb, alter_s, grund)

        `frisch=True` uebergeht den Merker (.534): die Eichung braucht die zwei
        Punkte EINES Baus, und ein bis zu KARTE_TAKT_S alter Wert waere dort kein
        Messpunkt, sondern eine Erinnerung. Der Aufruf kostet denselben Fork wie
        sonst auch und traegt den `timeout` der vorhandenen Sonde — keine zweite
        Sonde, keine neue Frist.

        `grund is None` heisst „frischer, guter Wert". Haengt oder fehlt die Sonde,
        kommt der LETZTE gute Wert mit seinem ALTER zurueck — nie `None` und nie
        `0`: eine 0 hiesse „Karte voll" und waere ein luegender Diagnosewert (K1).
        Erst nach KARTE_FEHLVERSUCHE_MAX Fehlversuchen IN FOLGE gilt die Karte als
        nicht messbar, und dann sagt sie das mit eigenem Grund.

        EINE SONDE: dieselbe wie die Systemstatistik (`core.systemstat.SONDEN`),
        kein zweiter nvidia-smi-Aufruf mit eigenem Parser."""
        jetzt = time.monotonic()
        with self._karte_schloss:
            alt = dict(self._karte)
        if not frisch and alt["ts"] and (jetzt - alt["ts"]) < KARTE_TAKT_S:
            return alt["mb"], round(jetzt - alt["ts"], 2), alt["grund"]
        mb, gesamt, grund = 0, 0, None
        try:
            from core import systemstat as _st              # noqa: PLC0415
            sonde = _st.SONDEN.get("cuda")
            d = (sonde() or {}) if sonde else {}
            gesamt = int(d.get("speicher_max_mb") or 0)
            belegt = int(d.get("speicher_mb") or 0)
            if gesamt <= 0 or belegt < 0 or belegt > gesamt:
                grund = str(d.get("grund") or "nicht_lesbar")
            else:
                mb = max(0, gesamt - belegt)
        except Exception as e:                             # noqa: BLE001
            grund = f"sonde_fehler: {type(e).__name__}"
        with self._karte_schloss:
            if grund is None:
                self._karte.update({"mb": mb, "gesamt": gesamt, "ts": jetzt,
                                    "fehl": 0, "grund": None})
                return mb, 0.0, None
            self._karte["fehl"] += 1
            fehl = self._karte["fehl"]
            letzte = self._karte["mb"]
            ts = self._karte["ts"]
        if fehl >= KARTE_FEHLVERSUCHE_MAX:
            return 0, (round(jetzt - ts, 2) if ts else 0.0), "nicht_messbar"
        # Der letzte gute Wert MIT Alter — der Aufrufer soll wissen, wie alt die
        # Auskunft ist, statt sie fuer frisch zu halten.
        return letzte, (round(jetzt - ts, 2) if ts else 0.0), grund

    def karte_stand(self):
        """Was die Karten-Sonde zuletzt wusste — fuer /health und die Antwort."""
        with self._karte_schloss:
            alt = dict(self._karte)
        return {"frei_mb": alt["mb"], "gesamt_mb": alt["gesamt"],
                "fehlversuche": alt["fehl"], "grund": alt["grund"],
                "alter_s": (round(time.monotonic() - alt["ts"], 2)
                            if alt["ts"] else None)}

    def karte_eigen_mb(self):
        """Der Kartenanteil DIESES Prozesses (.532). -> (mb|None, delta|None, grund)

        `grund is None` heisst „frisch gemessen"; `delta` ist der Unterschied
        zur vorigen MESSUNG (None beim ersten Wert und auf dem Merker-Weg).
        Gefragt wird hoechstens alle KARTE_EIGEN_TAKT_S — der Aufruf ist ein
        Fork wie die Karten-Sonde.

        WARUM EIN ZWEITER AUFRUF UND NICHT DIE SONDE VON OBEN: das sind zwei
        verschiedene Fragen an dieselbe Karte. `--query-gpu` sagt, was die KARTE
        traegt (Waechter, Anzeige-Transcode, Fremde inbegriffen);
        `--query-compute-apps` sagt, was ein PROZESS haelt. Im Feld war am
        15.09. genau der Unterschied die Auskunft, die fehlte: der eigene
        Deckel war voll, die Karte hatte noch Luft.

        KEINE ERFUNDENE ZAHL: findet sich kein Eintrag fuer die eigene pid,
        kommt `None` mit Grund zurueck, nie 0 — 0 hiesse „dieser Prozess
        belegt nichts" und waere ein luegender Diagnosewert (K1)."""
        jetzt = time.monotonic()
        with self._eigen_schloss:
            alt = dict(self._eigen)
        if alt["ts"] and (jetzt - alt["ts"]) < KARTE_EIGEN_TAKT_S:
            return alt["mb"], None, (alt["grund"] or "gemerkt")
        mb, grund = None, None
        try:
            from core import systemstat as _st              # noqa: PLC0415
            mb, grund = _st.prozess_karte_mb(os.getpid())
        except Exception as e:                             # noqa: BLE001
            mb, grund = None, f"sonde_fehler: {type(e).__name__}"
        with self._eigen_schloss:
            if grund is None:
                vorher = self._eigen["mb"]
                self._eigen.update({"mb": mb, "vorher": vorher, "ts": jetzt,
                                    "grund": None,
                                    "max": max(int(self._eigen["max"] or 0), mb)})
                return mb, (None if vorher is None else mb - vorher), None
            self._eigen.update({"ts": jetzt, "grund": grund})
            erstmals = not self._eigen["gemeldet"]
            self._eigen["gemeldet"] = True
        if erstmals:
            # EINMAL laut, danach still: die Frage wird je Job gestellt, und
            # eine Zeile je Job waere Rauschen statt Auskunft.
            prozess_log(f"vram own: cannot be attributed ({grund}) — this "
                        f"process does not report its own card share; the "
                        f"card-wide numbers in /health are unaffected")
        return None, None, grund

    def ram_stand(self, n_straenge=1):
        """DER CONTAINER-FUSSABDRUCK DIESES PROZESSES (.534, B3). -> dict

        Nur ZAHLEN, kein Automatismus: `own_mb` jetzt, `own_max_mb` als Maximum
        ueber die Prozess-Lebenszeit (die Wache misst es ohnehin je Takt, hier
        wird es nur herausgereicht), `grundlast_mb` als der Posten, den der
        Dienst gerechnet hat, und `vorschlag_mb` als das, was daraus JE STRANG
        uebrig bleibt.

        WOZU: der Werkswert `worker_rss_max_mb` (4096) ist die Je-Worker-Zahl aus
        der Zeit eigener Prozesse, auf VmRSS geeicht. Was ein Rechenstrang dieses
        Prozesses in DIESEM Mass (anon+shmem) wirklich braucht, hat bisher
        niemand gemessen — im Feldtest der .533 wurde die Zahl von Hand gesetzt,
        weil es keine gab. Der Vorschlag ist die Messgrundlage fuer diesen
        Entscheid, NICHT sein Ersatz: er wird gemeldet und sonst nichts.

        KEIN NEUER SCHWELLWERT: `max(0, own_max - grundlast) / straenge`, auf 256
        MB AUFgerundet (nach oben, weil ein zu kleines Budget die Wache reissen
        laesst — dieselbe Vorsichtsrichtung wie bei den Karten-Posten). Ohne
        Grundlast-Posten gibt es keinen Vorschlag, nur die Messwerte."""
        jetzt = fussabdruck_mb()
        if jetzt >= 0:
            self.spitze = max(self.spitze, jetzt)
        spitze = int(self.spitze) if self.spitze >= 0 else None
        grund = int(self.grundlast or 0)
        n = max(1, int(n_straenge or 0))
        vorschlag = None
        if spitze is not None and grund > 0:
            roh = max(0, spitze - grund) / n
            vorschlag = int(-(-roh // RAM_VORSCHLAG_STUFE_MB) * RAM_VORSCHLAG_STUFE_MB)
        return {"own_mb": jetzt if jetzt >= 0 else None,
                "own_max_mb": spitze,
                "grundlast_mb": grund or None,
                "straenge": n,
                "grenze_mb": int(self.grenze) or None,
                "vorschlag_mb": vorschlag}

    def eigen_stand(self):
        """Der eigene Kartenanteil fuer /health und die Job-Antwort (.532)."""
        with self._eigen_schloss:
            alt = dict(self._eigen)
        return {"own_mb": alt["mb"],
                "own_delta_mb": (None if alt["vorher"] is None or alt["mb"] is None
                                 else alt["mb"] - alt["vorher"]),
                "own_max_mb": int(alt["max"] or 0) or None,
                "own_grund": alt["grund"]}

    def _karte_takt(self):
        """DRUCK-SIGNAL 1 (.531): faellt der kartenweit freie Speicher unter die
        Reserve, drueckt jemand — und weil unser eigener Anteil gedeckelt ist, ist
        dieser Jemand in aller Regel ein FREMDER (Anzeige-Transcode, zweiter
        Companion, ein anderer Container). Auf Nicht-CUDA laeuft hier nichts.

        Die Reserve ist KEINE neue Zahl: es ist dieselbe `reserve_strang_mb`, mit
        der der Dienst drueben sein Budget gerechnet hat."""
        if not self.dienst.auf_karte():
            return
        frei, _alter, grund = self.karte_frei_mb()
        if grund is not None:
            return
        with self._karte_schloss:
            gesamt = int(self._karte["gesamt"] or 0)
        if gesamt <= 0:
            return
        res = _gpubudget.reserve_strang_mb(gesamt)
        if 0 <= frei < res:
            self.dienst.druck_buchen(
                "fremd",
                f"free card memory {frei} MiB below the {res} MiB reserve "
                f"(card {gesamt} MiB) — a consumer outside this process")

    def __enter__(self):
        self._t = threading.Thread(target=self._lauf, daemon=True, name="speicher-wache")
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._t is not None:
            self._t.join(timeout=self.takt + 2)
        return False

    def _lauf(self):
        vor = fussabdruck_mb()
        while not self._stop.wait(self.takt):
            jetzt = fussabdruck_mb()
            # Der vermerkte Ende-Wunsch wird JE TAKT geprueft, nicht nur im Moment des
            # Risses: der Riss faellt fast immer WAEHREND eines Jobs (s. ende_pruefen).
            self.dienst.ende_pruefen()
            self._karte_takt()
            if jetzt < 0:
                continue
            if vor < 0:
                vor = jetzt
            self.spitze = max(self.spitze, jetzt)
            if self.grenze and jetzt > self.grenze:
                # SCHWELLEN-RISS -> GEORDNETES ENDE (E2d). Erste Stufe der Leiter: der
                # Prozess ist ueber dem, was die Politik ihm zusagt, aber es ist noch
                # Zeit. Er geht, sobald der letzte Job beantwortet ist — kein Job geht
                # dabei verloren, und verifyd startet einen frischen.
                if not self._gemeldet:
                    self._gemeldet = True
                    prozess_log(f"WARN: footprint {jetzt} MB (anon+shmem) exceeds the "
                                f"policy limit {self.grenze} MB while "
                                f"{self.dienst.offen_n()} job(s) are running")
                self.dienst.ende_bitten(
                    f"footprint {jetzt} MB (anon+shmem) is above the policy limit "
                    f"{self.grenze} MB")
            # HIER STAND BIS 14.09. EINE ZWEITE, HARTE REGEL auf derselben Groesse:
            # „gewachsen um mehr als die ganze Politik-Grenze" -> abbruch_alle. Sie ist
            # RAUS, aus zwei gemessenen Gruenden.
            # (1) Ihr Nullpunkt war falsch. Er wurde beim Start dieser Wache genommen,
            #     also BEVOR die erste Geometrie gebaut war — Geometrien entstehen zur
            #     Laufzeit (W2-B29). Der voellig normale Aufbau des ersten Jobs sah
            #     damit wie ein Leck aus: Provokationsprobe p1 am 14.09., Grenze 2400,
            #     „grew by 2489 MB" beim ERSTEN Job, footprint 2576 MB — ein Prozess,
            #     der nie mehr als sein Soll belegt hat, wurde als Leck erschossen.
            # (2) Sie war gegenueber der Regel darueber ohnehin nur strenger
            #     (jetzt-start > grenze ist jetzt > grenze + start), konnte also nur
            #     NACH ihr reissen — und nahm ihr damit genau das weg, was sie leisten
            #     soll: geordnet gehen, ohne einen Job zu verlieren. In p1 rissen beide
            #     im SELBEN Takt, und der harte Weg gewann.
            # Was bleibt, ist die Leiter, die der Sache entspricht: ueber der Zusage ->
            # geordnet (oben); Container fast voll -> hart (unten), denn dann wartet der
            # OOM-Killer des Kerns nicht auf das Ende des letzten Jobs.
            frei = cgroup_frei_mb()
            wachstum = jetzt - vor if vor >= 0 else 0
            if frei >= 0 and 0 < wachstum >= frei:
                self.dienst.abbruch_alle(
                    f"process memory guard: container memory almost exhausted "
                    f"({frei} MB free, this worker grew {wachstum} MB in the last "
                    f"{self.takt:.0f}s — the kernel OOM killer would strike next), "
                    f"footprint {jetzt} MB")
            vor = jetzt


class FristWache:
    """Der Job-Frist-Waechter (Konzept §2, W3-V7).

    Er meldet einen Job, der seine Frist reisst — EINMAL, mit Job-Id, ins
    Prozess-Log; der Job traegt danach `frist_gerissen: true` in seiner Antwort.

    DIE KOMPILIER-AUSNAHME ist der eigentliche Grund fuer diese Wache: Geometrien
    entstehen zur LAUFZEIT (W2-B29), und ein Kompilat-Bau dauert auf kaltem Cache
    gemessen ueber 100 s (v2-Aufbau 112 s; auf MIGraphX sind 63 s bis 2 min je
    Modell gemessen). Ohne die Ausnahme wuerde genau der erste Job nach einem
    Image-Wechsel als Haenger gemeldet und — im Dienst — in eine Neustart-Schleife
    laufen, in der jeder Neustart wieder kompiliert.

    EHRLICHE GRENZE: toeten kann diese Wache nichts. Ein Python-Thread laesst sich
    von aussen nicht beenden, und den Prozess zu schiessen naehme die N-1
    unschuldigen Jobs mit. Der Schuss bleibt beim Dienst (E3), diese Wache liefert
    ihm den Grund."""

    def __init__(self, dienst, takt_s=FRIST_TAKT_S):
        self.dienst = dienst
        self.takt = float(takt_s)
        self.gerissen = 0
        self._stop = threading.Event()
        self._t = None

    def __enter__(self):
        self._t = threading.Thread(target=self._lauf, daemon=True, name="frist-wache")
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._t is not None:
            self._t.join(timeout=self.takt + 2)
        return False

    def _lauf(self):
        while not self._stop.wait(self.takt):
            jetzt = time.monotonic()
            for lauf in self.dienst.offene_jobs():
                if lauf.gemeldet or lauf.kompiliert:
                    continue
                # .531: GEMESSEN WIRD AB RECHENBEGINN, sobald er feststeht. Sonst
                # laeuft die Wartezeit in der Schlange gegen die Frist des Jobs:
                # bei vier Plaetzen auf zwei Rechenstraengen stehen zwei Jobs
                # regulaer an, und nach 600 s haette der Dienst sie fuer Haenger
                # gehalten und den GANZEN Prozess geschossen — mitsamt den beiden,
                # die wirklich rechneten. Vor dem Rechenbeginn gilt weiter `t0`,
                # sonst waere ein Job, der nie drankommt, unsichtbar.
                alter = jetzt - (lauf.t_lauf0 or lauf.t0)
                if alter > lauf.frist_s:
                    lauf.gemeldet = True
                    self.gerissen += 1
                    prozess_log(f"WARN: job {lauf.id} ({lauf.typ}) has been "
                                f"{'computing' if lauf.t_lauf0 else 'queued'} "
                                f"{alter:.0f}s, past its {lauf.frist_s:.0f}s deadline "
                                f"— it is not compiling; the service decides what to do")


# ----------------------------------------------------------------- Der Lauf eines Jobs
class JobLauf:
    """Der Zustand EINES laufenden Jobs — das, was die Wachen von aussen sehen."""

    def __init__(self, job, nr):
        self.job = job
        self.id = str(job.get("id") or f"j{nr}")
        self.typ = job.get("typ")
        # t0 = ANNAHME (hier, im Lese-Thread). Daran misst der Frist-Waechter: fuer
        # den Dienst drueben beginnt die Frist, wenn er den Job abgibt, nicht wenn
        # ein Rechenstrang frei wird.
        self.t0 = time.monotonic()
        # t_lauf0/cpu0 setzt der RECHENSTRANG, nicht dieser Thread. time.thread_time
        # zaehlt je Thread — ein hier genommener Startwert gehoerte dem Lese-Thread
        # und haette mit der CPU-Zeit des Jobs nichts zu tun.
        self.t_lauf0 = None
        self.cpu0 = None
        self.frist_s = float(job.get("frist_s") or job.get("timeout_s") or FRIST_VORGABE_S)
        self.kompiliert = False     # steht dieser Job gerade im Kompilat-Bau?
        self.gemeldet = False       # Frist schon gemeldet?
        self.rueckfaelle = set()    # Arten, fuer die schon EINE Zeile geschrieben wurde
        self.log = None
        # --- E3.3 (W2-B29): der Kompilat-/Geometrie-Bau wird DIESEM Job GEBUCHT.
        # Bis E2d war `kompiliert` nur eine Frist-AUSNAHME: die Wache schwieg, und
        # damit war die Zeit fuer alle unsichtbar. Geometrien entstehen aber zur
        # LAUFZEIT, und der erste Job einer neuen Clip-Groesse zahlt sie ganz allein
        # (gemessen 24-36 s ohne Cache, v2-Aufbau 112 s). Wer das nicht bucht, sieht
        # spaeter einen „langsamen Job" statt eines Bauschritts — und ordnet den
        # Speicher-Sprung derselben Analyse zu.
        self.kompilat_s = 0.0       # Sekunden, die dieser Job im Kompilat-Bau stand
        self.kompilat_mb = 0        # Fussabdruck-ZUWACHS waehrend dieser Bauten
        self.kompilat_n = 0         # wie viele Bauten (Geometrie + Satz-Waermung)
        # --- .529: Sekunden, die dieser Job auf das STAFFEL-Schloss gewartet hat,
        # also auf den Bau eines ANDEREN Strangs. Bewusst NICHT in `kompilat_s`:
        # das ist die Zeit des eigenen Baus, und wer beides in einen Topf wirft,
        # kann hinterher nicht mehr unterscheiden, ob ein Job lange gebaut oder
        # lange gewartet hat. Gebucht wird trotzdem, denn unsichtbar waere die
        # Wartezeit als Analysezeit gezaehlt worden.
        self.staffel_s = 0.0
        self.staffel_n = 0          # wie oft dieser Job gestaffelt wurde
        self.geo = None             # Geometrie-Schluessel (W, H), den er gerade haelt
        # --- .534 (B5) DIE ZEITEN DIESES EREIGNISSES, gemessen dort, wo sie
        # entstehen. Der Dienst drueben kann sie nicht sehen: der Clip-Abruf und
        # der Decoder laufen in DIESEM Prozess. Im Feld waren am 15.09. rund
        # 40 % der Platzzeit Abruf und Uebergabe und nicht Rechnung — genau die
        # Spalten, die bis .533 nirgends standen.
        self.abruf_s = None         # Clip aus Frigate holen (None = Cache/Datei)
        self.abruf_bytes = None
        self.abruf_quelle = None    # "frigate" | "cache" | "datei"
        self.erstes_bild_s = None   # vom Ende des Abrufs bis zum ersten Frame
        self.decoder = None         # welche Kette das erste Bild geliefert hat


# ----------------------------------------------------------------- Der Dienst
class Dienst:
    """Der Prozess: Engine, Geometrien, Rechenstraenge, Protokoll, Wachen."""

    def __init__(self, a, antwort_out):
        self.a = a
        self.out = antwort_out
        self.threads = max(1, int(a.threads))
        self.scratch = a.scratch
        self.refcache = a.refcache
        self._schreib = threading.Lock()
        self._geo_schloss = threading.Lock()
        self._warm_schloss = threading.Lock()
        # --- STAFFEL-SCHLOSS (.529, Feldvorfall 15.09.) ---------------------------
        # EIN Riegel um ALLE Bauschritte des Prozesses: Geometrie-Bau UND Warmlauf.
        # Bis .528 lagen die beiden unter GETRENNTEN Schloessern (`_geo_schloss` und
        # `_warm_schloss`) — nacheinander lief damit nur, was dasselbe Schloss nahm.
        # Strang A konnte seine Geometrie bauen, waehrend Strang B einen Satz waermte,
        # und beide zusammen forderten im selben Moment 4K-Puffer an: auf der
        # Feldtester-Anlage endete das im CUDA-BFC-OOM am 99,5-MB-Cast-Puffer und
        # riss den Container-Fussabdruck ueber die Politik-Grenze (Belegort
        # .suslik_tmp/gt5/runs/feldtester_baseline_526_20260914/roh/log_live_2150.log,
        # 15.09. 05:38-05:46 lokal). Die Werkbank-Lehre vom 12.09. („gleichzeitiger
        # Kaltstart zweier Worker passt nicht — Starts staffeln") galt bis dahin nur
        # zwischen PROZESSEN; seit E3.1 stecken die Straenge in EINEM Prozess und
        # brauchen dieselbe Staffelung.
        #
        # WAS GESTAFFELT WIRD, und was ausdruecklich NICHT: nur der BAU. Das Rechnen
        # bleibt voll parallel — ein Strang, der eine fertige Geometrie mit einem
        # gewaermten Satz vorfindet, nimmt dieses Schloss gar nicht erst.
        #
        # SCHLOSS-REIHENFOLGE, damit es keine Verklemmung gibt: `_bau_schloss` wird
        # IMMER VOR `_geo_schloss` und `_warm_schloss` genommen, nie umgekehrt. Kein
        # Pfad haelt eines der beiden inneren Schloesser, waehrend er auf dieses
        # wartet.
        self._bau_schloss = threading.Lock()
        # .535: HIER STAND DER ZUSTAND DER PREIS-MESSUNG (Plateau-Fenster,
        # Grundlinie, Eich-Schluessel, Fenstergroesse, Waechterzahl). Die
        # Messung ist ausgebaut — die Preise stehen in der Messtabelle.
        self._offen = {}                       # Job-Id -> JobLauf
        self._offen_schloss = threading.Lock()
        self._nr = 0
        self.graphen = {}                      # (W, H) -> Geometrie
        # E3.3 (W2-B29): Benutzungs-Reihenfolge der Geometrien, aelteste zuerst.
        # Sie traegt den VERFALL — mehr dazu in `geometrie`/`_geometrien_stutzen`.
        self.geo_reihe = []
        # .531: ein Start-Argument gewinnt ueber die Vorgabe; das Job-Feld darf
        # danach in BEIDE Richtungen nachziehen (s. `annehmen`).
        self.geometrien_max = int(getattr(a, "geometrien_max", 0) or 0) \
            or GEOMETRIEN_MAX_VORGABE
        self._geo_deckel_gemeldet = False
        # --- .531 KARTENHAUSHALT ------------------------------------------------
        self.vram_deckel_mb = max(0, int(getattr(a, "vram_deckel_mb", 0) or 0))
        self.arena_strategie = getattr(a, "arena_strategie", None) or None
        self.arena_shrink = bool(int(getattr(a, "arena_shrink", 0) or 0))
        # .532: der Memory-Pattern-Schalter reist mit, damit /health und jede
        # Job-Antwort sagen koennen, WIE dieser Prozess rechnet. Gestellt wird
        # er in der Engine (engine_cuda.mem_pattern_setzen).
        self.mem_pattern = bool(int(getattr(a, "mem_pattern", 0) or 0))
        # Der Neustart wird HOECHSTENS EINMAL je Prozess erbeten: den Abstand
        # zwischen zwei Neustarts haelt der Dienst drueben (er allein weiss, wann
        # der letzte war), dieser Prozess kennt nur sich selbst.
        self._vram_neustart_gebeten = False
        self._vram_wiederholt = set()          # Job-Ids, die schon einmal liefen
        self._vram_letzter_text = None
        # .532 EIGENER DECKEL, ZWEITER TREFFER: der Zaehler gehoert dem PROZESS,
        # nicht dem Job — im Feld kamen die Treffer aus zwei Rechenstraengen
        # binnen Sekunden. Das eigene Schloss haelt genau diese Entscheidung
        # zusammen (`collections.Counter` ist nicht atomar).
        self._vram_druck_schloss = threading.Lock()
        self._vram_deckel_treffer = 0
        self._vram_straenge_senken = False
        self.engine = None
        self.alle = self.mit_refs = self.erk = None
        self.modell = None
        self.bindung = {}
        self.speicher = SpeicherWache(self)
        self.frist = FristWache(self)
        self.schlange = queue.Queue()
        self.bg_schlange = queue.Queue()       # E2c: die Nicht-Analyse-Jobs, EINER zur Zeit
        self._arbeiter = []
        self._bg_arbeiter = None
        self._ende = threading.Event()
        # E2d: das GEORDNETE Prozess-Ende aus einem ZUSTAND (s. ende_bitten). Es ersetzt
        # die Leerlauf-Uhr; gesetzt wird es erst, wenn kein Job mehr offen ist.
        self.ende = threading.Event()
        self.ende_grund = None
        self.ende_schluessel = None            # .531: Grund-Schluessel des Endes
        self.zaehler = collections.Counter()
        self.null_serie = 0                    # 0-Gesichter-Ereignisse IN FOLGE
        self.fabrik = None                     # E2c: Embedder/NormMass auf der Engine
        self._bild = None
        self._bild_schloss = threading.Lock()
        self._werk = {}                        # warme Werkzeuge (PoseWache, StrukturMass)
        self._eich_schloss = threading.Lock()  # E2d: Eichmarke der Kompilat-Probe
        self._eich_umfeld = None
        self.kompilat_bericht = {"stand": "ungeprueft"}
        # E3.4: die letzte KURZFORM der Start-Proben (Bindung + Pruefbild). Wie der
        # Kompilat-Bericht: strukturiert in jede Job-Antwort, nicht nur ins Log.
        self.startprobe_bericht = {"stand": "nicht gelaufen"}

    # ---------------------------------------------------------- Aufbau
    def engine_bauen(self):
        """Die Engine anlegen und ihre BINDUNG festhalten.

        Das ist das Aequivalent des PROVIDER-GUARD von face_audit (face_audit.py:
        1170/1175, gehoben in verifyd.py:13936-13942): dort prueft eine Wache nach
        dem Session-Bau, ob der Beschleuniger WIRKLICH gebunden hat, weil ORT sonst
        still auf CPU faellt und weiterrechnet. Die beiden Engines hier binden hart
        („kein Rueckfall", engine_ov.py:651 / engine_cuda.py:965) — sie WERFEN,
        statt still zu wechseln. Der Guard ist damit das Gelingen des Baus selbst;
        er wandert als strukturiertes Feld in jede Job-Antwort, statt als Textmarke
        in ein Log."""
        name = self.a.engine
        if name == "ov":
            import engine_ov as eng                        # noqa: PLC0415
        elif name == "cuda":
            import engine_cuda as eng                      # noqa: PLC0415
        elif name == "migraphx":
            # E6 (17.09.2026): die AMD/ROCm-Seite. Sie WIRFT nicht, wenn das Geraet
            # fehlt — sie faellt je Stufe LAUT auf die CPU und meldet den Zustand in
            # `kopf_auskunft`/`/health` (Begruendung im Kopf von engine_migraphx und
            # in `engine_migraphx._sitzung`). Der Guard unten prueft deshalb bei
            # diesem Backend nicht das Gelingen des Baus, sondern liest die Bindung
            # aus der Engine (s. `bindung_ergaenzen` weiter unten).
            import engine_migraphx as eng                  # noqa: PLC0415
        elif name == "cpu":
            # E4 (17.09.2026): die CPU-Seite — der universelle Rueckfall, und auf dem
            # cpu-Image das SOLL. Sie wirft ebenfalls nicht: hier gibt es kein Geraet,
            # das fehlen koennte. Was sie meldet, ist der STACK (OpenVINO-CPU-Laufzeit
            # gegen nacktes onnxruntime, gemessen 3-7x auseinander), nicht ein
            # Fehlzustand.
            import engine_cpu as eng                       # noqa: PLC0415
        else:
            raise SystemExit(f"unbekannte Engine {name!r} (ov|cuda|migraphx|cpu)")
        ap = argparse.ArgumentParser(add_help=False)
        eng.Engine.argumente(ap)
        vorgabe, _rest = ap.parse_known_args(self.a.engine_argv)
        for k, v in vars(vorgabe).items():
            setattr(self.a, k, v)
        self.a.out = self.scratch
        # .534 (B4): S0 — DER PREIS DES SESSION-SATZES, auf DIESER Karte gemessen.
        # Hier und nur hier, weil der Session-Bau der einzige Bauschritt ist, der
        # nicht durch den Staffel-Riegel laeuft (er passiert VOR dem ersten Job).
        # Zu diesem Zeitpunkt rechnet nichts anderes in diesem Prozess — die
        # Messung ist per Bauart sauber.
        _basis_vor = None
        if self.auf_karte():
            _mb, _a, _g = self.speicher.karte_frei_mb(frisch=True)
            if _g is None:
                _basis_vor = _mb
        try:
            self.engine = eng.Engine(self.a)
            self.bindung = {"engine": eng.Engine.name, "geraet": getattr(eng, "GERAET", None)
                            or getattr(eng, "EP", None), "gebunden": True}
        except SystemExit as e:
            self.bindung = {"engine": name, "geraet": None, "gebunden": False,
                            "grund": str(e)}
            raise
        # E6/E4: auf den beiden Engines, die NICHT werfen, ist „die Engine steht"
        # nicht dasselbe wie „das gewuenschte Geraet rechnet" — auf migraphx, weil
        # EP oder /dev/kfd fehlen koennen, auf cpu, weil zwei verschiedene
        # Rechen-Stacks in Frage kommen. Was daran wahr ist, weiss nur die Engine.
        #
        # E4 (17.09.2026) HAT DIESE STELLE GENERISCH GEMACHT: bis .540 stand hier ein
        # `hasattr(engine, 'ep_gelistet')`-Sonderfall mit MIGraphX-Texten IM DIENST,
        # und der naechste Backend-Sonderfall haette einen zweiten danebengestellt.
        # Jetzt fragt der Dienst EINE Methode; die Texte stehen dort, wo die Tatsache
        # herkommt (K1: eine Diagnose, die „gebunden" sagt, waehrend etwas anderes
        # rechnet, ist die teuerste Sorte Luege).
        _erg = getattr(self.engine, "bindung_ergaenzen", None)
        if _erg is not None:
            _erg(self.bindung)
        prozess_log(f"engine {eng.Engine.name} bound ({self.bindung['geraet']}), "
                    f"{self.threads} compute thread(s)")
        # HIER WURDE BIS ZUR NB-ABNAHME DER SESSION-SATZ GEMESSEN. Das ist RAUS:
        # zur Bauzeit belegt er auf der Karte nichts (gemessen „card did not
        # shrink: 5530 -> 5530"), weil onnxruntime traege allokiert. Sein Anteil
        # steckt im PLATEAU der ersten Konstellation und wird dort abgeleitet.
        _ = _basis_vor
        # E3.4 (Befund Live-Test 14.09.): OB DIESE ENGINE EINE KOMPILAT-WACHE HAT,
        # steht ab sofort SOFORT fest und LAUT — nicht erst beim ersten Geometrie-Bau
        # und nicht nur als stiller Ueberschlag in `kompilat_pruefen`. `def probe`
        # existiert heute allein in engine_ov (engine_ov.py:786); auf CUDA ist die
        # Wache damit PER BAUART AUS. Ein Betreiber, der in /health „kompilat_probe:
        # ok" sucht und dort nichts findet, muss den Unterschied zwischen „noch nicht
        # geprueft" und „diese Engine kann es gar nicht" sehen koennen — sonst ist die
        # Diagnose stumm und der Nutzer haelt eine ungewachte Anlage fuer gewacht (K1).
        # Die Kurzform der Start-Proben (`startprobe`) ist auf CUDA der Ersatz: sie
        # rechnet den Erkennungs-Vektor des BILD-Wegs gegen dieselbe Eichmarke.
        _satz_kl = getattr(eng, "Satz", None)
        _hat_probe = hasattr(_satz_kl, "probe")
        self.bindung["kompilat_wache"] = "an" if _hat_probe else "aus"
        if not _hat_probe:
            self.kompilat_bericht = {"stand": "keine probe in dieser engine",
                                     "engine": eng.Engine.name, "wache": "aus",
                                     "ersatz": "startprobe (bild-weg gegen dieselbe "
                                               "eichmarke)"}
            prozess_log(f"WARN: engine {eng.Engine.name} has no compiled-model probe "
                        f"(only engine_ov implements Satz.probe) — the per-geometry "
                        f"compiled-model guard is OFF by design on this backend; the "
                        f"short start proof (startprobe) covers the recognition stage "
                        f"instead. This is reported in /health, not swallowed.")
        else:
            self.kompilat_bericht = {"stand": "ungeprueft", "engine": eng.Engine.name,
                                     "wache": "an"}
        # E2c: von hier an rechnen AUCH die Alt-Wege ihre Gesichter auf dieser Engine.
        # Der Griff ist der von worker.py (dort `_patch_embedder`, worker.py:994-999):
        # `face_audit.Embedder` wird auf eine Fabrik umgebogen, damit ihn auch die
        # Aufrufer treffen, die tief in `anlernen` stehen und kein `emb` durchreichen.
        # `face_audit.NormMass` kommt dazu — sie ist der zweite ORT-OV-Nutzer der
        # Hintergrund-Jobs (die einzigen beiden; e/t/p binden CPU, s. bild_kern-Kopf).
        # SOFORT, nicht erst beim ersten Hintergrund-Job: der Referenz-Neubau unten
        # laeuft ueber `face_audit.Embedder()` und MUSS die Engine treffen — genau das
        # ist der E2-Blocker (CPU-EP, max 1,59e-02 je Embedding).
        self.fabrik = bild_kern.Fabrik(self.bild_rechner,
                                       self.bindung.get("geraet")).einhaengen()

    def bild_rechner(self):
        """Der Bild-Weg dieses Prozesses, beim ersten Bedarf angelegt (E2c).
        Faul, weil er den Modell-Bestand der Engine anlegt — ein Prozess ohne
        Hintergrund-Jobs und ohne Referenz-Neubau soll das nicht bezahlen."""
        with self._bild_schloss:
            if self._bild is None:
                t0 = time.monotonic()
                self._bild = bild_kern.BildRechner(self.engine)
                prozess_log(f"image path ready on the engine in "
                            f"{time.monotonic() - t0:.1f}s")
            return self._bild

    def referenzen(self, log):
        """Referenzen EINMAL je Prozess laden (mit Selbstheilung).

        REIHENFOLGE IST HIER EINE HARTE BEDINGUNG, gemessen im E2-Gate 13.09.:
        diese Funktion wird NACH engine_bauen() gerufen, nie davor. In E2 war der
        Grund der ABI-Befund aus E1 (die OpenVINO-Fassung im onnxruntime-openvino-
        Paket und das eigenstaendige openvino-Paket vertragen sich in EINEM Prozess
        nicht, `undefined symbol: _ZN2ov3Any4Base9to_stringEv`; im Gate real
        getreten, Beleg runs/e2_dienst_20260913/p5_refcache/prozess.log).

        E2c hat den Grund GEAENDERT, die Reihenfolge bleibt: `engine_bauen` haengt
        jetzt die Bild-Fabrik in `face_audit.Embedder` ein, und erst DANACH darf ein
        Referenz-Neubau laufen — sonst baute er sich noch den alten ORT-Embedder.
        Der Neubau rechnet seitdem auf DEMSELBEN Kompilat wie die Live-Erkennung; der
        gemessene E2-Blocker (Neubau auf dem CPU-EP, bis 1,59e-02 je Embedding
        Abweichung zur GPU-Fassung) ist damit weg, und ORT-OV wird in diesem Prozess
        gar nicht mehr geladen."""
        self.alle, self.mit_refs, self.erk = referenzen_laden(self.refcache, log)
        self.modell = face_audit.aktuelles_modell()
        # In JEDE Job-Antwort, nicht nur ins Log: auf welchem Weg die Referenzen
        # entstanden sind, muss ein Betreiber sehen koennen — es ist die Frage, ob
        # Referenz- und Live-Embeddings aus EINER Quelle kommen.
        self.bindung["referenzen"] = {
            "neu_gebaut": bool(self.erk.get("neu_gebaut")),
            "personen_mit_vektoren": len(self.mit_refs),
            **({"weg": "engine (E2c: dasselbe Kompilat wie die Live-Erkennung)"}
               if self.erk.get("neu_gebaut") else {})}
        if self.erk.get("neu_gebaut"):
            prozess_log(f"reference cache rebuilt from the master "
                        f"({len(self.mit_refs)} person(s) with vectors) on the engine "
                        f"— references and live embeddings now come from the same "
                        f"compiled model (E2c)")

    def geometrie(self, W, H, fps, lauf):
        """Die Geometrie dieser Clip-Groesse — gebaut, wenn sie neu ist (W2-B29:
        Geometrien entstehen zur LAUFZEIT, nicht beim Start). Der Bau laeuft unter
        einem Schloss, ist fuer die Frist-Wache als Kompilat-Bau MARKIERT und wird
        seit E3.3 dem Job auch GEBUCHT (`_kompilat_buchen`).

        SEIT .529 LIEGT UEBER BEIDEN BAUSCHRITTEN — Geometrie UND Warmlauf — DAS
        STAFFEL-SCHLOSS (`_bau_schloss`, Begruendung dort). Die Bauart ist deshalb
        zweistufig: erst der SCHNELLWEG unter `_geo_schloss` (nur ein Blick in die
        Tabelle), und nur wenn wirklich gebaut werden muss, der Staffel-Riegel. Ein
        Strang, der eine fertige und gewaermte Geometrie vorfindet, wartet auf
        nichts — das Rechnen bleibt parallel.

        DOPPELPRUEFUNG NACH DEM WARTEN, beide Male: wer hinter dem Staffel-Schloss
        ankommt, sieht eine andere Welt als davor — der Vorgaenger hat genau das
        gebaut, worauf gewartet wurde. Ohne die zweite Pruefung baute der Zweite
        dasselbe noch einmal, und der Speicher waere doppelt weg."""
        lauf.geo = (W, H)
        with self._geo_schloss:                      # Schnellweg: nur die Tabelle
            g = self.graphen.get((W, H))
            if g is not None:
                self._geo_gebraucht(W, H)
        if g is None:
            with self._staffel(lauf, f"geometry {W}x{H}"):
                with self._geo_schloss:
                    g = self.graphen.get((W, H))     # in der Wartezeit gebaut?
                if g is None:
                    with self._kompilat_buchen(lauf, f"geometry {W}x{H}"):
                        neu = self.engine.geometrie_bauen({"x": (W, H, fps)})
                    with self._geo_schloss:
                        g = self.graphen[(W, H)] = neu[(W, H)]
                        self.zaehler["geometrien"] += 1
                with self._geo_schloss:
                    self._geo_gebraucht(W, H)
        # Der Satz DIESES Rechenstrangs; der erste Zugriff legt ihn an und waermt
        # ihn. Nacheinander (warm_schloss) wie im Kern: das haelt die Reihenfolge
        # der ersten Geraete-Allokationen fest. Der Staffel-Riegel darum haelt ihn
        # zusaetzlich vom Geometrie-Bau eines ANDEREN Strangs getrennt — das ist
        # die Ueberlappung, an der die Karte am 15.09. ueberlief.
        #
        # EHRLICHE GRENZE, benannt: `g.satz()` selbst liegt NOCH VOR dem Riegel.
        # Er legt die beiden Frame-Puffer des Strangs an (engine_cuda.Satz.__init__:
        # y und uv, bei 4K zusammen rund 12 MB) — klein gegen den Bau, aber nicht
        # null, und zwei Straenge koennen das gleichzeitig tun. Der Posten, an dem
        # die Karte am 15.09. ueberlief, war ein anderer (99,5 MB Cast-Puffer aus
        # dem Lauf INNERHALB von `warm()`), und der steht jetzt unter dem Riegel.
        # Ihn mitzunehmen hiesse, „hat dieser Strang diese Geometrie schon
        # gewaermt" neben dem thread-lokalen Satz ein zweites Mal zu fuehren —
        # eine zweite Wahrheit, die nach einem Geometrie-Verfall falsch waere.
        satz = g.satz()
        if not getattr(satz, "_dienst_warm", False):
            with self._staffel(lauf, f"warm-up {W}x{H}"):
                with self._warm_schloss:
                    if not getattr(satz, "_dienst_warm", False):
                        with self._kompilat_buchen(lauf, f"warm-up {W}x{H}"):
                            satz.warm()
                            self.kompilat_pruefen(g, satz, lauf)
                        satz._dienst_warm = True
        return g

    def _geo_gebraucht(self, W, H):
        """BENUTZUNGS-REIHENFOLGE fortschreiben und den Deckel anwenden — auch beim
        Treffer. Aufrufer haelt `self._geo_schloss`.

        Ohne den Treffer-Fall waere „zuletzt gebaut" gemeint, nicht „zuletzt
        gebraucht", und der Verfall wuerfe die Dauerbrenner-Aufloesung der Anlage
        weg statt der Eintagsfliege. Bis .528 stand das mitten in `geometrie`; seit
        der Staffelung wird es aus zwei Zweigen gerufen und ist deshalb ein eigener
        Griff — dieselbe Rechnung, eine Stelle."""
        if (W, H) in self.geo_reihe:
            self.geo_reihe.remove((W, H))
        self.geo_reihe.append((W, H))
        self._geometrien_stutzen()

    @contextlib.contextmanager
    def _staffel(self, lauf, was):
        """DER STAFFEL-RIEGEL um EINEN Bauschritt (.529). Siehe `_bau_schloss`.

        DREI DINGE AUF EINMAL, und jedes hat seinen Grund:

        1. WARTEN UNTER FRIST-AUSNAHME. Solange ein Strang hier wartet, steht
           `lauf.kompiliert` auf True, und die `FristWache` ueberspringt ihn. Ohne
           das wuerde die Wartezeit auf den Bau eines ANDEREN Strangs als Analyse-
           zeit gegen die Frist dieses Jobs laufen — er wuerde als Haenger gemeldet,
           obwohl er auf genau das wartet, was ihn spaeter schneller macht. Der
           vorherige Wert wird gemerkt und zurueckgesetzt, nie hart auf False:
           `_kompilat_buchen` laeuft INNERHALB dieser Klammer, und ein hartes False
           an dessen Ende naehme der Klammer ihre Ausnahme.

        2. GEBUCHT WIRD DIE WARTEZEIT GETRENNT (`lauf.staffel_s`), nicht als
           Bauzeit. Wer beides in `kompilat_s` wirft, kann hinterher nicht mehr
           unterscheiden, ob ein Job lange gebaut oder lange gewartet hat — und
           genau diese Unterscheidung ist der Beweis, dass gestaffelt wurde.

        3. MIT FRIST (STAFFEL_FRIST_S). Kommt das Schloss nicht frei, macht der
           Strang OHNE es weiter und sagt es LAUT. Ein haengender Bau darf nicht
           alle uebrigen Straenge still mitnehmen — und weil die Frist-Wache die
           Wartenden ueberspringt (Punkt 1), saehe sie niemand. Der Preis ist
           benannt: in diesem Fall bauen wieder zwei gleichzeitig, also genau die
           Lage vom 15.09. — aber laut und mit Grund im Log statt stumm."""
        t0 = time.monotonic()
        vorher = lauf.kompiliert
        lauf.kompiliert = True                       # Frist-Ausnahme schon fuers Warten
        gehalten = self._bau_schloss.acquire(timeout=STAFFEL_FRIST_S)
        warte = time.monotonic() - t0
        # HIER WURDE BIS ZUR NB-ABNAHME DER .534 GEMESSEN — um den Bauschritt
        # herum, die Karte vorher und nachher. Das ist RAUS, und der Grund ist
        # gemessen: onnxruntime allokiert seine Arena TRAEGE. Beim Bau bewegt
        # sich die Karte kaum; der Zuwachs faellt waehrend der ersten Analysen.
        # Auf dem CUDA-Notebook ergab das 148 MiB fuer eine 4K-Geometrie, wo die
        # Nachtmessung ~976 sah — und mit so kleinen Preisen baute die Leiter
        # DREI Straenge auf einer 6-GB-Karte. Zu kleine Preise machen die Leiter
        # zu GROSS, also genau in die Richtung, die im Feld die Karte gefuellt
        # hat. Seit .535 wird ueberhaupt nicht mehr gemessen, um zu planen: die
        # Preise stehen in der Messtabelle (`core.gpubudget`).
        try:
            if not gehalten:
                self.zaehler["staffel_frist"] += 1
                prozess_log(f"WARN: waited {warte:.0f}s for the build lock before "
                            f"{was} (job {lauf.id}) and gave up — another thread's "
                            f"build is not finishing. Building WITHOUT staggering "
                            f"now: two concurrent builds can exhaust the accelerator "
                            f"(this is the 15.09. field case). Check the log above "
                            f"for a build that never completed.")
            elif warte > 0:
                # GEBUCHT WIRD JEDE echte Wartezeit, GEMELDET nur die, die ein
                # Mensch sehen soll. Die Schwelle ist eine Protokoll-Schwelle,
                # kein Budget: eine kurze Wartezeit ist genauso Staffelung wie
                # eine lange, sie ist nur keine Logzeile wert.
                lauf.staffel_s += warte
                lauf.staffel_n += 1
                self.zaehler["staffel_wartezeiten"] += 1
                if warte >= STAFFEL_MELDE_S:
                    prozess_log(f"staggered {was} (job {lauf.id}): waited "
                                f"{warte:.1f}s for another thread's build — builds "
                                f"run one at a time, computing stays parallel")
            yield
        finally:
            if gehalten:
                self._bau_schloss.release()
            lauf.kompiliert = vorher

    def bg_offen_n(self):
        """Wie viele HINTERGRUND-Jobs gerade offen sind (.534). Sie rechnen im
        eigenen Strang auf derselben Karte und verfaelschen jedes Plateau."""
        with self._offen_schloss:
            return sum(1 for x in self._offen.values()
                       if getattr(x, "typ", None) != "analyze")

    # .535: HIER STANDEN `_plateau_waechter_gleich`, `_plateau_takt`,
    # `plateau_stand`, `plateau_schreiben`, `_stufen_ableiten`, `_eich_lesen`
    # und `_eich_speichern` — die Preis-Messung im Betrieb. Sie ist ausgebaut.
    # Was der Prozess auf der Karte haelt, meldet weiterhin `eigen_stand()`
    # (.532, eine Momentaufnahme je Job); was er halten DARF, sagt die
    # Messtabelle in `core.gpubudget`.

    @contextlib.contextmanager
    def _kompilat_buchen(self, lauf, was):
        """Die Klammer um EINEN Kompilat-Bau (W2-B29, E3.3): Frist-Ausnahme UND
        Buchung in einem Griff.

        Bis E2d stand hier nur `lauf.kompiliert = True/False` — eine reine AUSNAHME
        fuer den Frist-Waechter. Damit war der Bau fuer alle anderen unsichtbar: die
        Sekunden liefen als Analysezeit in die Antwort, und der Speicher-Sprung
        (jede Geometrie kostet gemessen ~700 MiB auf CUDA, s. gpubudget-Stuetzwerte)
        landete beim Job, der gerade zufaellig der erste war. Beides gehoert
        ZUGEORDNET, sonst sucht ein Betreiber einen langsamen Job und einen
        Speicherfresser, wo in Wahrheit ein einmaliger Bauschritt stand.

        GEMESSEN WIRD, WAS MESSBAR IST, und nicht mehr: die Wanduhr des Baus und die
        DIFFERENZ des Prozess-Fussabdrucks ueber den Bau. Die Differenz ist bei N
        Rechenstraengen eine Naeherung (ein anderer Strang kann in derselben Zeit
        Frames ziehen) — sie steht deshalb als `fussabdruck_delta_mb` in der Antwort
        und nirgends als „dieser Job belegt X". Negative Differenzen werden auf 0
        geklemmt: ein Bau gibt keinen Speicher zurueck, ein Minus ist die Messung des
        Nachbarn."""
        vor = fussabdruck_mb()
        t0 = time.monotonic()
        # .529: den vorherigen Wert MERKEN statt hart auf False zurueckzusetzen.
        # Seit dem Staffel-Riegel laeuft diese Klammer INNERHALB von `_staffel`,
        # das die Frist-Ausnahme schon gesetzt hat; ein hartes False am Ende naehme
        # der aeusseren Klammer ihre Ausnahme, und der wartende Strang liefe wieder
        # in die Frist-Meldung. Ohne Verschachtelung ist `vorher` False und das
        # Verhalten unveraendert.
        vorher = lauf.kompiliert
        lauf.kompiliert = True
        try:
            yield
        finally:
            lauf.kompiliert = vorher
            dauer = time.monotonic() - t0
            nach = fussabdruck_mb()
            zuwachs = max(0, nach - vor) if (vor >= 0 and nach >= 0) else 0
            lauf.kompilat_s += dauer
            lauf.kompilat_mb += zuwachs
            lauf.kompilat_n += 1
            self.zaehler["kompilat_bauten"] += 1
            prozess_log(f"built {was} in {dauer:.1f}s (job {lauf.id}, footprint "
                        f"{vor} -> {nach} MB, +{zuwachs} MB booked to this build, "
                        f"not to the analysis)")

    def _geometrien_stutzen(self):
        """DER DECKEL UND DER VERFALL der Geometrie-Puffersaetze (W2-B29, E3.3).
        Aufrufer haelt `self._geo_schloss`.

        DAS PROBLEM, unbestritten: `self.graphen` wuchs MONOTON. Jede neue
        Clip-Groesse legte ihre Kompilate an, dazu je Rechenstrang einen Satz mit
        seinen Geraete-Tensoren — und nichts gab je etwas zurueck. In einer Anlage
        mit drei Kamera-Aufloesungen ist das ein einmaliger Posten; in einer mit
        wechselnden Substreams, nachtraeglich umgestellten Kameras oder
        eingespielten Fremd-Clips ist es ein Leck, das die Speicher-Formel nie
        eingeplant hat (sie rechnet `g_zusatz`, nicht `beliebig viele`).

        DER DECKEL KOMMT NICHT VON HIER. `self.geometrien_max` ist das Job-Feld
        `geometrien_max`, das verifyd aus der Speicher-Formel rechnet
        (`core.gpubudget.geometrien_deckel`): wie viele Geometrien neben Straengen,
        Waechtern und Reserve auf DIESER Karte Platz haben. 0 heisst „kein Deckel
        bekannt" — dann wird NICHTS geworfen und der Dienst sagt das einmal laut.
        Eine hier hineingeschriebene Zahl waere auf jeder fremden Karte falsch.

        DER VERFALL ist die Benutzungs-Reihenfolge: geworfen wird die am laengsten
        nicht mehr gebrauchte Geometrie. Eine Geometrie, die gerade ein Job HAELT
        (`lauf.geo`), wird nie geworfen — ihre Graphen liegen mitten im Lauf.

        EHRLICHE GRENZE: das Wegwerfen gibt den Speicher erst frei, wenn auch die
        Saetze der Rechenstraenge fallen. Sie haengen in einem `threading.local()`
        AN der Geometrie (engine_ov.Geometrie._lokal) und gehen mit ihr — aber erst,
        wenn der Sammler sie holt. Der Deckel wirkt also mit Verzoegerung; er
        verhindert unbegrenztes Wachstum, nicht jede Spitze.
        .531 nimmt dem Sammler die Ausrede (`del` + `gc.collect()`, s. u.). Was
        damit NICHT belegt ist: dass ORT den GERAETE-Speicher einer beendeten
        Session an die Karte zurueckgibt. Dafuer gibt es keine Quelle, und
        gemessen ist am 15.09. das Gegenteil (im Leerlauf gab der Prozess ueber
        drei Minuten nichts zurueck). Der erste wirkliche Rueckgabeweg bleibt
        deshalb der geordnete NEUSTART, nicht dieser Verfall."""
        deckel = int(self.geometrien_max or 0)
        if deckel <= 0:
            if not self._geo_deckel_gemeldet and len(self.graphen) > 1:
                self._geo_deckel_gemeldet = True
                prozess_log("no geometry cap configured (job field 'geometrien_max' "
                            "missing) — compiled geometries are kept without a limit, "
                            "as before E3.3. The cap comes from the memory formula in "
                            "verifyd, never from a constant in here.")
            return
        # In Gebrauch = ein offener Job haelt sie gerade. `offene_jobs` nimmt sein
        # eigenes Schloss, nicht dieses — keine Verschraenkung.
        gehalten = {l.geo for l in self.offene_jobs() if l.geo is not None}
        while len(self.graphen) > deckel:
            opfer = next((k for k in self.geo_reihe
                          if k in self.graphen and k not in gehalten), None)
            if opfer is None:
                # Alle ueberzaehligen Geometrien sind gerade in Arbeit. Das ist kein
                # Fehler, nur ein spaeterer Zeitpunkt: der naechste Bau raeumt auf.
                return
            weg = self.graphen.pop(opfer, None)
            self.geo_reihe.remove(opfer)
            self.zaehler["geometrien_verfallen"] += 1
            # .531: die Verweise wirklich fallen lassen UND den Sammler bitten.
            # Satz und Geometrie halten einander (engine_cuda: der thread-lokale
            # Satz zeigt auf seine Geometrie und umgekehrt) — einen Ringverweis
            # loest die Referenzzaehlung nicht, nur der Sammler. Ohne ihn bleibt
            # der Speicher bis zum naechsten zufaelligen Sammellauf liegen.
            del weg
            gc.collect()
            prozess_log(f"geometry {opfer[0]}x{opfer[1]} dropped (least recently "
                        f"used, cap {deckel}) — its compiled graphs and per-thread "
                        f"buffers are released")

    def kompilat_pruefen(self, g, satz, lauf):
        """DIE KOMPILAT-PROBE gegen die Eichmarke (E2d).

        Der Anlass steht in `engine_ov.Engine._cache_setzen`: am 13.09. rechnete die
        Erkennungs-Stufe nach einem Kompilat-Wechsel messbar anders, und nichts im Lauf
        sagte es — Detektionen, Frames und Guete-Werte blieben unauffaellig, nur die
        Namen fielen weg. Der Cache ist seitdem aus; DIESE Probe ist die Wache dahinter,
        denn die Klasse „das geladene Kompilat rechnet anders als das gemessene" hat mehr
        Quellen als den Cache (Treiberwechsel, fremdes Image, getauschtes ONNX).

        ABLAUF: fester Pruefvektor durch alle Stufen (engine_ov.Satz.probe), Vergleich
        gegen die Marke im Arbeitsordner. Kennt die Marke dieses UMFELD nicht (andere
        OpenVINO-Fassung, anderer Treiber, anderes Modell, anderer Engine-Code), wird sie
        LAUT erneuert — dort sind andere Zahlen richtig. Ist das Umfeld dasselbe und die
        Erkennungs-Stufe weicht ab, endet der Job mit Fehler; der Prozess produziert
        keine Namen aus einem Kompilat, das nachweislich anders rechnet.

        EHRLICHE GRENZEN: (1) die Marke entsteht beim ERSTEN Lauf auf dieser Maschine —
        sie sagt „so wie damals", nicht „richtig"; die Richtigkeit belegt der
        Werte-Abgleich der Etappen-Gates. (2) Sie gilt je Geometrie: eine neue
        Clip-Groesse bringt ihre eigene Zeile mit und ist beim ersten Mal ungeprueft.
        (3) Engines ohne `probe` (CUDA heute) werden uebersprungen, und das steht so in
        der Antwort statt als stilles „ok"."""
        if not hasattr(satz, "probe"):
            # E3.4: der Bericht steht schon seit `engine_bauen` (dort LAUT, mit dem
            # Ersatz-Hinweis). Hier wird er NICHT ueberschrieben — sonst verlöre er
            # genau die zwei Felder, an denen /health „aus per Bauart" von „noch nicht
            # geprueft" unterscheidet.
            return
        t0 = time.monotonic()
        ist = satz.probe(roh=True)
        marke = f"{g.W}x{g.H}"
        # E3.4: die Marken-Mechanik (lesen, Umfeld pruefen, laut erneuern, eichen)
        # liegt seitdem in `_eichen` — die Kurzform der Start-Proben braucht exakt
        # dieselbe fuer ihren eigenen Schluessel, und zweimal dieselbe Vorschrift
        # waere die Streuung, die die Hausregel verbietet.
        urteil, befunde = self._eichen(marke, ist)
        if urteil == "geeicht":
            self.kompilat_bericht = {"stand": "geeicht", "wache": "an",
                                     "engine": self.bindung.get("engine"),
                                     "geometrie": marke,
                                     "r_norm": ist.get("r_norm"),
                                     "probe_s": round(time.monotonic() - t0, 2)}
            prozess_log(f"compiled-model probe {marke}: calibration mark written "
                        f"(||f|| {ist.get('r_norm')})")
            return
        self.kompilat_bericht = {"stand": urteil, "wache": "an",
                                 "engine": self.bindung.get("engine"),
                                 "geometrie": marke,
                                 "r_norm": ist.get("r_norm"),
                                 "probe_s": round(time.monotonic() - t0, 2)}
        if befunde:
            self.kompilat_bericht["befunde"] = befunde
        if urteil == "abweichung":
            self.zaehler["kompilat_abweichung"] += 1
            text = ("compiled-model probe FAILED for " + marke + ": this process computes "
                    "the recognition stage differently than the calibrated one — "
                    + " | ".join(befunde))
            prozess_log("FATAL: " + text)
            lauf.log.zeile("FEHLER: " + text)
            raise RuntimeError(text)
        if urteil == "hinweis":
            prozess_log(f"WARN: compiled-model probe {marke} differs outside the "
                        f"recognition stage (not fatal): {' | '.join(befunde)}")

    # ---------------------------------------------------------- Buchhaltung
    def offen_n(self):
        with self._offen_schloss:
            return len(self._offen)

    def offene_jobs(self):
        with self._offen_schloss:
            return list(self._offen.values())

    def _anmelden(self, job):
        with self._offen_schloss:
            self._nr += 1
            lauf = JobLauf(job, self._nr)
            self._offen[lauf.id] = lauf
        return lauf

    def _abmelden(self, lauf):
        with self._offen_schloss:
            self._offen.pop(lauf.id, None)

    def antworten(self, antwort):
        """EINE Antwort-Zeile auf die Antwort-Pipe. Gesperrt, weil N Rechenstraenge
        gleichzeitig fertig werden koennen und eine halb geschriebene Zeile den
        Leser drueben aus dem Tritt braechte."""
        with self._schreib:
            try:
                self.out.write(json.dumps(antwort, ensure_ascii=False) + "\n")
                self.out.flush()
            except Exception as e:                         # noqa: BLE001
                prozess_log(f"answer pipe broken ({type(e).__name__}: {e})")

    # ------------------------------------------------- .531 Kartenhaushalt
    def auf_karte(self):
        """Laeuft dieser Dienst auf einem Backend mit eigenem Kartenspeicher?

        Mit `getattr` gelesen, und das ist kein Schlendrian: die Proben stellen
        absichtlich nur die Stuecke des Dienstes auf, die sie pruefen
        (tools/proben/e3_2_staffel.py). Ein Kartenhaushalt, der eine
        Teil-Buehne zum Absturz braechte, wuerde genau dort nicht mehr geprueft."""
        return getattr(getattr(self, "a", None), "engine", None) == "cuda"

    def vram_bericht(self):
        """Was dieser Prozess ueber seinen Kartenhaushalt weiss — fuer /health.

        Nur ZAEHLER und der Stand der Sonde: was er selbst belegt, weiss er nicht
        (der eigene Anteil ist im Container nicht verlaesslich zuordenbar), und
        eine Zahl, die das behauptet, waere eine luegende Diagnose."""
        if not self.auf_karte():
            return None
        z = self.zaehler
        return {"deckel_mb": self.vram_deckel_mb,
                "arena_strategie": self.arena_strategie,
                "arena_shrink": self.arena_shrink,
                # .532: wie dieser Prozess rechnet, nicht was gewuenscht war.
                "mem_pattern": self.mem_pattern,
                "geometrien_max": self.geometrien_max,
                "geometrien_jetzt": len(self.graphen),
                "karte": self.speicher.karte_stand(),
                # .532: der EIGENE Anteil an der Karte (own_mb/own_delta_mb/
                # own_max_mb/own_grund) — die Zahl, die im Feld gefehlt hat.
                **self.speicher.eigen_stand(),
                # .532: wie oft der eigene Deckel schon getroffen hat und ob
                # deshalb ein Strang weniger verlangt ist. Der DIENST liest das
                # und senkt beim naechsten Start (er allein kennt die Reihe).
                "deckel_treffer": int(self._vram_deckel_treffer),
                "straenge_senken": bool(self._vram_straenge_senken),
                "straenge": int(getattr(self, "threads", 0) or 0),
                "druck": {"deckel": int(z.get("vram_druck_deckel") or 0),
                          "karte_voll": int(z.get("vram_druck_karte_voll") or 0),
                          "fremd": int(z.get("vram_druck_fremd") or 0),
                          "hwdec": int(z.get("vram_druck_hwdec") or 0),
                          "cuda_fehler": int(z.get("vram_druck_cuda_fehler") or 0)},
                "wiederholungen": int(z.get("vram_wiederholungen") or 0),
                "neustarts": int(z.get("vram_neustarts") or 0),
                "geometrien_verfallen": int(z.get("geometrien_verfallen") or 0),
                "letzter_druck": self._vram_letzter_text}

    def ram_bericht(self):
        """Was dieser Prozess ueber seinen CONTAINER-Fussabdruck weiss (.534 B3).

        Auf JEDEM Backend, nicht nur auf der Karte: die RAM-Frage stellt sich
        ueberall, und im Feld liefert die Karten-Sonde ohnehin nichts (dort meldet
        der Treiber dem Prozess seine eigene Belegung nicht). Diese Auskunft haengt
        deshalb an nichts ausser der Wache, die ohnehin je Sekunde misst."""
        return self.speicher.ram_stand(getattr(self, "threads", 1))

    def ram_eigen_melden(self, lauf):
        """EINE Zeile je abgeschlossenem Analyse-Job: was dieser Prozess im
        Container belegt (.534 B3).

        Gleiche Kadenz wie die Karten-Zeile (`vram_eigen_melden`) — je Job eine —,
        aber ausdruecklich UNABHAENGIG von ihr: auf der Feldmaschine liefert die
        Karten-Sonde je Prozess nichts, und genau dort wird die RAM-Zahl
        gebraucht."""
        st = self.ram_bericht()
        if st.get("own_mb") is None:
            return
        prozess_log(f"ram own: {st['own_mb']} MB container (max "
                    f"{st['own_max_mb']}, threads={st['straenge']}, job {lauf.id})"
                    + (f" — limit {st['grenze_mb']} MB, base {st['grundlast_mb']} "
                       f"MB, suggestion {st['vorschlag_mb']} MB per thread"
                       if st.get("vorschlag_mb") is not None else ""))

    def vram_druck_art(self, text):
        """Welche Art von Kartendruck steht in diesem Ausnahmetext? -> str|None

        ERKANNT WIRD AN DER DATEI `bfc_arena.cc`, nie am Satz allein: der Satz
        aendert sich mit der ORT-Fassung, die Datei nicht. Die beiden SAETZE
        unterscheiden dann die beiden Lagen — eigener Deckel zu klein gegen Karte
        voll. Beide Muster stehen in core.registry, damit das Gate und diese
        Laufzeit-Erkennung DIESELBE Quelle lesen (qs_ebenen.md)."""
        s = str(text or "")
        if _registry.VRAM_DRUCK_DATEI not in s:
            if "out of memory" in s.lower() or "CUBLAS" in s:
                return "cuda_fehler"
            return None
        for art, satz in _registry.VRAM_DRUCK_TEXTE.items():
            if satz in s:
                return art
        return "karte_voll"

    def druck_buchen(self, art, text):
        """EIN Kartendruck-Ereignis buchen und darauf antworten (.531).

        Vier Arten, drei Antworten:
          `deckel`      unser eigener Deckel war zu klein -> der Job wird EINMAL
                        wiederholt, aber erst nach einem Geometrie-Verfall (ohne
                        den traefe die Wiederholung dieselbe Arithmetik).
          `karte_voll`  die Karte ist fremd voll -> geordneter Neustart mit
                        kleinerem Budget, gedeckelt.
          `fremd`       freier Kartenspeicher unter der Reserve -> dasselbe.
          `hwdec`       der Hardware-Decoder fiel zurueck -> Kartendruck
                        AUSSERHALB der Arena; gezaehlt und gemeldet, der Neustart
                        ist derselbe gedeckelte Weg.
        Gezaehlt wird IMMER und je Art getrennt: eine Zahl, die zwei Lagen
        zusammenwirft, kann der Betreiber nicht lesen."""
        art = str(art or "")
        self.zaehler[f"vram_druck_{art}"] += 1
        self.zaehler["vram_druck"] += 1
        self._vram_letzter_text = einzeilig(text, 300)
        if art == "deckel":
            prozess_log(f"vram pressure: ORT allocation failed inside our own cap "
                        f"({_registry.VRAM_DRUCK_DATEI}, "
                        f"\"{_registry.VRAM_DRUCK_TEXTE['deckel']}\") — {text}")
            # .532 DER AUSWEG, den .531 nicht hatte: ein EINZELNER Treffer
            # bleibt ein Fall fuer den Geometrie-Verfall und die eine
            # Wiederholung (s. o.). Beim ZWEITEN ist es kein Ausreisser mehr,
            # sondern der Betriebspunkt — dann hilft nur ein frischer Prozess
            # mit weniger Straengen, denn der Arena-Deckel steht fuer die
            # Lebenszeit fest (bfc_arena.cc:39). Im Feld traf der Deckel am
            # 15.09. nach sechs Ereignissen und danach 14 mal hintereinander;
            # der Prozess fiel auf einen Strang und fand nie wieder heraus.
            # DER ZAEHLER GEHOERT DEM PROZESS, nicht dem Job: die Treffer kamen
            # aus zwei Rechenstraengen binnen Sekunden.
            with self._vram_druck_schloss:
                self._vram_deckel_treffer += 1
                treffer = self._vram_deckel_treffer
                senken = (treffer >= DECKEL_TREFFER_BIS_NEUSTART
                          and not self._vram_straenge_senken)
                if senken:
                    self._vram_straenge_senken = True
            if not senken:
                return
            prozess_log(f"vram pressure: our own arena cap was hit {treffer} "
                        f"times in this process — asking for an ordered restart "
                        f"with ONE COMPUTE THREAD LESS; the cap itself is fixed "
                        f"for the lifetime of a process, so a smaller footprint "
                        f"is only reachable through a fresh one")
            self.vram_neustart_bitten(art, text)
            return
        if art == "fremd":
            # Nur die ERSTE Meldung je Prozess ins Log: die Wache taktet im
            # Sekundenrhythmus, und ein anhaltender Fremdverbraucher schriebe
            # sonst eine Zeile je Sekunde.
            if not self.speicher._karte_gemeldet:
                self.speicher._karte_gemeldet = True
                prozess_log(f"vram pressure: {text}")
        elif art == "hwdec":
            prozess_log(f"vram pressure: hardware decode fell back ({text}) — "
                        f"card pressure outside the arena")
            # ABWEICHUNG VOM BAUPLAN, bewusst und hier begruendet: ein
            # Decoder-Rueckfall ist ein VERDACHT auf Kartendruck, kein Beweis —
            # er kommt auch von einem Codec, den NVDEC nicht kann, oder von einem
            # Treiber. Ein Neustart je Rueckfall waere im Feld alle zehn Minuten
            # einer, und jeder kostet die warmen Kompilate (24-36 s). Der Neustart
            # wird deshalb nur erbeten, wenn die Karte im selben Moment WIRKLICH
            # eng ist; gezaehlt und gemeldet wird er immer.
            _frei, _a, _g = self.speicher.karte_frei_mb()
            with self.speicher._karte_schloss:
                _ges = int(self.speicher._karte["gesamt"] or 0)
            if _g is None and _ges > 0 and _frei < _gpubudget.reserve_strang_mb(_ges):
                self.vram_neustart_bitten(art, text)
            return
        else:
            prozess_log(f"vram pressure: ORT allocation failed with the card full "
                        f"({_registry.VRAM_DRUCK_DATEI}, "
                        f"\"{_registry.VRAM_DRUCK_TEXTE['karte_voll']}\") — {text}")
        self.vram_neustart_bitten(art, text)

    def vram_neustart_bitten(self, art, text):
        """Den geordneten Neustart wegen Kartendruck erbitten — hoechstens EINMAL
        je Prozess.

        Der Deckel steht bei der Konstruktion der Arena fest (bfc_arena.cc:39) und
        ist im Lauf NICHT senkbar; ein kleinerer Deckel ist nur ueber einen neuen
        Prozess zu haben. Ob der Neustart wirklich kommt, entscheidet der Dienst:
        er kennt den Abstand zum letzten (gpubudget.DRUCK_NEUSTART_ABSTAND_S) und
        haelt ihn ein. Dieser Prozess kennt nur sich selbst."""
        if self._vram_neustart_gebeten:
            return
        self._vram_neustart_gebeten = True
        self.zaehler["vram_neustarts"] += 1
        self.ende_bitten(f"card memory pressure ({art}): "
                         f"{einzeilig(text, 200)} — a smaller arena cap is only "
                         f"reachable through a fresh process",
                         schluessel="vram_druck")

    def vram_eigen_melden(self, lauf):
        """EINE Zeile je abgeschlossenem Analyse-Job: was DIESER Prozess auf
        der Karte haelt (.532).

        Mit der Konstellation daneben (Straenge, lebende Geometrien, Geometrie
        dieses Jobs), weil der Grundbedarf genau daran haengt: im Feld war der
        Deckel nach SECHS Ereignissen voll — bei zwei Straengen und zwei
        lebenden Geometrien (1080p UND 4K gemischt); im Labor kam dieselbe
        Zahl Straenge mit EINER Geometrie auf 2228 MiB. Ohne die Konstellation
        in der Zeile ist die Zahl nicht vergleichbar.

        Kein Wert, keine Zeile: der Grund steht dann EINMAL im Log (s.
        `SpeicherWache.karte_eigen_mb`)."""
        mb, delta, grund = self.speicher.karte_eigen_mb()
        if mb is None:
            return
        with self._geo_schloss:
            geos = len(self.graphen)
        geo = getattr(lauf, "geo", None)
        d_text = (f"{delta:+d} MiB" if delta is not None
                  else ("n/a (probe throttled)" if grund else "n/a (first)"))
        prozess_log(f"vram own: {mb} MiB (pid {os.getpid()}, job {lauf.id}, "
                    f"delta {d_text} vs prev, threads={self.threads}, "
                    f"geos={geos}, geo="
                    + (f"{geo[0]}x{geo[1]}" if geo else "-") + ")")

    def vram_verfall_erzwingen(self, lauf):
        """Die aelteste NICHT gehaltene Zusatz-Geometrie zwangsweise verfallen
        lassen (.531 C5). -> True, wenn wirklich eine gefallen ist.

        Nur fuer die Wiederholung nach einem Deckel-Treffer: ohne frei gewordenen
        Platz traefe der zweite Anlauf dieselbe Arithmetik wie der erste. Die
        Geometrien, die in den Ankern schon stecken, bleiben unangetastet — sie
        sind kein Zusatz, sondern der Betriebspunkt (ein Wechsel zwischen 1080p
        und 4K kostet sonst bei jedem Clip einen Neubau von 24-36 s)."""
        with self._geo_schloss:
            if len(self.graphen) <= _gpubudget.GEOMETRIEN_IN_ANKERN:
                return False
            gehalten = {x.geo for x in self.offene_jobs() if x.geo is not None}
            opfer = next((k for k in self.geo_reihe
                          if k in self.graphen and k not in gehalten), None)
            if opfer is None:
                return False
            weg = self.graphen.pop(opfer, None)
            self.geo_reihe.remove(opfer)
            self.zaehler["geometrien_verfallen"] += 1
            del weg
            gc.collect()
            prozess_log(f"geometry {opfer[0]}x{opfer[1]} dropped under card "
                        f"pressure (job {lauf.id}) — least recently used")
            return True

    def ende_bitten(self, grund, schluessel=None):
        """Das GEORDNETE Prozess-Ende aus einem ZUSTAND heraus (E2d, User-Auflage
        13.09.: „Prozess lebt solange gesund").

        Es ersetzt den Leerlauf-Exit. Der alte Weg war eine UHR: nach WORKER_IDLE_S
        ohne neue Zeile ging der Prozess, egal wie es ihm ging. Das ist die falsche
        Frage — ein gesunder Prozess soll stehen bleiben (sein Kompilat-Bau kostet
        ohne Cache gemessen 24-36 s), und ein ungesunder soll gehen, auch wenn gerade
        Betrieb ist.

        DER UNTERSCHIED ZU `abbruch_alle` IST DER PREIS: dieser Weg kostet KEINEN
        JOB. Deshalb wird der Wunsch nur VERMERKT, solange noch etwas offen ist, und
        erst vollzogen, wenn der letzte Job beantwortet ist. `abbruch_alle` bleibt fuer
        den Fall, in dem dafuer keine Zeit mehr ist (der OOM-Killer des Kerns wartet
        nicht).

        Der Grund steht EINMAL im Prozess-Log — er ist die Auskunft, die verifyd
        braucht, um den frischen Prozess nicht fuer einen Absturz zu halten."""
        if self.ende_grund is None:
            self.ende_grund = grund
            # .531: der GRUND-SCHLUESSEL reist als eigenes Feld mit, nicht nur im
            # Fliesstext. Der Dienst drueben bucht daran den Backoff — aus einem
            # Satz muesste er ihn wieder herausparsen, und genau diese
            # Rekonstruktion beendet der Log-Kontrakt.
            self.ende_schluessel = schluessel
            prozess_log("orderly shutdown requested: " + grund
                        + (f" [{schluessel}]" if schluessel else ""))
        self.ende_pruefen()

    def ende_pruefen(self):
        """Den vermerkten Wunsch vollziehen, sobald kein Job mehr offen ist.

        DER WUNSCH IST BLEIBEND — das ist der Unterschied, den die Probe p2 am 14.09.
        erzwungen hat. Dort riss die Grenze WAEHREND eines Jobs (Spitze 2756 MB gegen
        die Zusage 2600 beim Bau der 4K-Geometrie), fiel im naechsten Takt auf 2565
        zurueck, und weil der Vollzug damals an der noch anliegenden Ueberschreitung
        hing, blieb der Wunsch fuer immer liegen: 10 von 10 Jobs liefen durch, der
        Prozess ging erst am stdin-EOF. Ein Prozess, der seine Zusage schon einmal
        ueberschritten hat, ist aber nicht deshalb wieder gesund, weil die Spitze
        vorbei ist — beim naechsten Mal kann sie den Container reissen. Deshalb wird
        hier NUR noch auf die offenen Jobs geschaut, nicht mehr auf den Messwert."""
        if self.ende_grund is not None and not self.offen_n():
            self.ende.set()

    def abbruch_alle(self, grund):
        """Der Abbruch der Speicher-Wache: ALLE offenen Jobs als FREMDVERSCHULDET
        beantworten, dann sterben. Fremdverschuldet heisst „dieser Job hat nichts
        falsch gemacht" — der Dienst darf ihn deshalb ohne Strafe nachholen
        (W2-B4/B5: der write-ahead-Nachholzaehler wird fuer diese Klasse NICHT
        erhoeht, sonst stehen unschuldige Ereignisse nach drei Kollisionen auf
        `tot`). Die Job-Id steht in JEDER dieser Zeilen — die Todesursache gehoert
        je Job gebucht, nicht je Prozess (W2-B6).

        E3.3: dazu die Todesursache als FELD (`todesursache`), nicht nur im Fliesstext
        des `fehler`. Der Aufrufer drueben bucht sie je Job-Id (WorkerDienst._buchen);
        aus dem Text liesse sie sich nur wieder herausparsen — dieselbe Rekonstruktion,
        die der Log-Kontrakt beendet."""
        prozess_log("FATAL: " + grund)
        for lauf in self.offene_jobs():
            self.antworten({
                "id": lauf.id, "ok": False, "fehler": grund,
                "fremdverschuldet": True,
                "todesursache": "speicher-wache: container fast voll",
                "todesursache_text": einzeilig(grund, 300),
                # KEIN cpu_s: diese Zeile schreibt der WACHE-Thread, und
                # time.thread_time zaehlt je Thread — eine Zahl von hier waere die
                # CPU-Zeit der Wache, nicht die des Jobs. Lieber kein Feld als ein
                # falsches (der Dienst liest beides mit .get()).
                "wall_s": round(time.monotonic() - (lauf.t_lauf0 or lauf.t0), 1),
                "rss_mb": rss_mb(), "vmhwm_mb": vmhwm_mb(),
                "rss_spitze_mb": max(self.speicher.spitze, rss_mb()),
                "fussabdruck_mb": fussabdruck_mb()})
        try:
            self.out.flush()
        except Exception:                                  # noqa: BLE001
            pass
        os._exit(1)

    def koerper_budget(self, job):
        """DAS RAM-BUDGET EINES KOERPER-/PERSONLAUF-JOBS, GETEILT (W2-B11, E3.3).

        `worker._koerper_budget` rechnet die Politik-Grenze des Jobs minus dem VmRSS
        des PROZESSES (und, wenn lesbar, gegen den cgroup-Rest). Das war richtig,
        solange ein Prozess EINEN Job hielt: der Rest gehoerte ihm ganz. Im Dienst
        halten N Rechenstraenge gleichzeitig Jobs — dieselbe Zahl wuerde jedem von
        ihnen den GANZEN Rest zusagen. Zwei Koerper-Zuege, die beide „du hast 2 GB"
        hoeren, belegen 4: genau die Ueberbuchung, gegen die W2-B11 geschrieben ist.

        Geteilt wird durch die Zahl der GERADE offenen Jobs, nicht durch die
        Strang-Zahl: ein Prozess mit vier Straengen, in dem nur dieser eine Job
        laeuft, soll nicht ein Viertel bekommen. Der Boden ist der des Originals —
        `worker._NORMMASS_MARGE_MB`, dieselbe Marge, die dort als Budget-Boden steht
        (worker.py:125). Eine zweite 256 gibt es hier nicht.

        EHRLICHE GRENZE: die Teilung ist eine ANNAHME ueber Gleichverteilung. Ein
        Analyse-Job neben einem Koerper-Job braucht nicht dasselbe. Sie ist trotzdem
        richtiger als die Zusage des vollen Rests an jeden, denn die ist nachweislich
        falsch — und ein zu kleines Budget lehnt `Koerper._start` LAUT ab, ein zu
        grosses erzeugt den OOM."""
        from worker import _koerper_budget, _NORMMASS_MARGE_MB   # noqa: PLC0415
        voll = float(_koerper_budget(job))
        halter = max(1, self.offen_n())
        return max(voll / halter, float(_NORMMASS_MARGE_MB))

    def rueckfall_melden(self, lauf, art, text):
        """Ein Rueckfall auf CPU/Software — EINE Zeile je Ereignis (User-Auflage
        13.09.: „Bei Rueckfall auf CPU eine Information im Log, aber nur einmal pro
        Event") plus Zaehler.

        STAND DER DINGE, ehrlich: BENUTZT wird heute genau eine Art — `hwdec`, der
        SW-Decode-Rueckfall beider Engines (worker_kern.nv12_mit_rueckfall, E2d).
        Die GERAETE-Bindung hat weiterhin keinen Rueckfall: sie wirft, statt still
        auf CPU zu wechseln. Fuer `engine_cpu` als lauten Rueckfall (Konzept §4)
        steht dieser Weg bereit, damit die Meldeform nicht je Engine neu erfunden
        wird."""
        if art in lauf.rueckfaelle:
            return
        lauf.rueckfaelle.add(art)
        self.zaehler["rueckfall_" + art] += 1
        (lauf.log or self).zeile(f"WARN: fell back to {art} — {text}")

    def zeile(self, text):                                 # Notnagel, wenn kein JobLog
        prozess_log(text)

    # ---------------------------------------------------------- Jobs
    def annehmen(self, job):
        """Einen Job entgegennehmen. analyze-Jobs gehen in die Schlange der
        Rechenstraenge, `ping` wird sofort beantwortet (verifyd nutzt ihn als
        Lebenszeichen, er darf nie hinter einer Analyse warten)."""
        typ = job.get("typ")
        if typ == "ping":
            self.antworten({"id": str(job.get("id") or "ping"), "ok": True,
                            "rss_mb": rss_mb(), "fussabdruck_mb": fussabdruck_mb(),
                            "offene_jobs": self.offen_n(),
                            # E3.4: der Lebenszeichen-Job traegt auch den Stand der
                            # zwei Selbstbeweis-Wachen. Sonst zeigte /health fuer
                            # einen frisch gestarteten Prozess, der noch keinen
                            # Rechen-Job hatte, gar nichts — und „nichts" liest sich
                            # wie „in Ordnung".
                            "bindung": dict(self.bindung),
                            "kompilat_probe": dict(self.kompilat_bericht),
                            "startprobe": dict(self.startprobe_bericht),
                            # .531: der Kartenhaushalt reist mit dem Lebenszeichen
                            # nach /health — der Betreiber soll den Druck sehen,
                            # ohne dass jemand dafuer eine Analyse anstossen muss.
                            "vram": self.vram_bericht(),
                            # .534 (B3): derselbe Weg fuer den CONTAINER-Speicher.
                            # Er haengt an keiner Karte und kommt deshalb auf
                            # JEDEM Backend mit.
                            "ram": self.ram_bericht(),
                            **({"beendet_sich": True,
                                "ende_schluessel": self.ende_schluessel}
                               if self.ende_grund else {})})
            return
        if self.ende_grund is not None:
            # ES IST SCHON ENTSCHIEDEN, DASS DIESER PROZESS GEHT (s. ende_bitten).
            # Ihn jetzt noch rechnen zu lassen, hiesse: das Ende hinauszoegern, obwohl
            # er ueber seiner Speicher-Zusage steht. Der Job wird deshalb SOFORT und
            # ALS FREMDVERSCHULDET zurueckgegeben — er hat nichts falsch gemacht, der
            # Dienst darf ihn ohne Strafe auf dem frischen Prozess wiederholen
            # (W2-B4/B5, dieselbe Klasse wie bei abbruch_alle).
            # DASS ES DIESEN ZWEIG BRAUCHT, HAT DIE PROBE p3 AM 14.09. GEZEIGT: dort
            # kam der naechste Job im Fenster zwischen „Ende beschlossen" und „Prozess
            # weg" an, wurde noch angenommen, aber nicht mehr fertig — 1 Job still
            # verloren. Still verlorene Jobs sind genau die Klasse, gegen die W2-B4
            # geschrieben wurde.
            self.antworten({"id": str(job.get("id") or "?"), "ok": False,
                            "fehler": "worker is shutting down in an orderly way: "
                                      + self.ende_grund,
                            "fremdverschuldet": True,
                            # E3.3: je Job-Id, als FELD (s. abbruch_alle).
                            "todesursache": "geordnetes ende angefordert",
                            "todesursache_text": einzeilig(self.ende_grund, 300),
                            # .531: der GRUND-SCHLUESSEL als eigenes Feld. Der
                            # Dienst bucht daran den Neustart-Abstand; aus dem
                            # Fliesstext muesste er ihn herausparsen.
                            "ende_schluessel": self.ende_schluessel,
                            "rss_mb": rss_mb(), "fussabdruck_mb": fussabdruck_mb()})
            return
        lauf = self._anmelden(job)
        if typ not in ("analyze",) + HINTERGRUND_TYPEN:
            # Sauber absagen statt still nichts zu tun — ein Dienst, der einen Job
            # verschluckt, laesst den Aufrufer in seine Frist laufen.
            self._abmelden(lauf)
            self.antworten({
                "id": lauf.id, "ok": False,
                "fehler": f"unbekannter typ '{typ}'",
                "cpu_s": 0.0, "wall_s": 0.0, "rss_mb": rss_mb(),
                "vmhwm_mb": vmhwm_mb(), "rss_spitze_mb": max(self.speicher.spitze, rss_mb())})
            return
        self.speicher.grenze_melden(job)
        # E3.3 (W2-B29): der Geometrie-Deckel reist wie die Speicher-Grenze als
        # Job-FELD mit und gilt als GROESSTE angemeldete Zusage — dieselbe Regel und
        # dieselbe Begruendung wie bei `grenze_melden`: der Deckel ist eine Zusage an
        # den PROZESS, ein zweiter Job darf ihn nicht nachtraeglich enger machen.
        # .531 KEHRT DIESE REGEL FUER DEN GEOMETRIE-DECKEL UM (Defekt 4): der
        # Job-Wert gilt, auch wenn er KLEINER ist. Der Grund ist, dass er seit .531
        # aus derselben Leiter kommt wie die Strang-Zahl und den JETZIGEN
        # Kartenstand abbildet — ein zugeschalteter Live-Waechter macht den Platz
        # fuer Geometrien wirklich enger, und eine Zusage von vorhin waere dann
        # keine Zusage mehr, sondern eine Erinnerung. Fuer `fussabdruck_max_mb`
        # bleibt „die groesste gewinnt" (s. `grenze_melden`): anderes Mass,
        # anderer Sachverhalt — dort ist die Zahl eine Politik-Grenze gegen ein
        # Leck, hier ein Platz auf der Karte.
        # DER ARENA-DECKEL ist damit ausdruecklich NICHT gemeint: er steht bei der
        # Konstruktion der Arena fest (bfc_arena.cc:39) und wirkt erst ab dem
        # naechsten Prozess-Start.
        try:
            _gm = int(float(job.get("geometrien_max") or 0))
        except (TypeError, ValueError):
            _gm = 0
        if _gm > 0 and _gm != self.geometrien_max:
            if _gm < self.geometrien_max:
                prozess_log(f"geometry cap lowered {self.geometrien_max} -> {_gm} "
                            f"(job {job.get('id')}): the service recomputed it "
                            f"against the card as it is NOW")
            self.geometrien_max = _gm
        # .535: HIER STANDEN die Job-Felder der Preis-Messung (`eich_schluessel`,
        # `eich_fenster`, `eich_waechter_n`, `vram_grundlinie_mb`). Mit dem
        # Ausbau der Messung braucht der Worker keines davon mehr.
        # E2c: die Nicht-Analyse-Jobs gehen auf IHRE Schlange. Sie laufen dort EINER
        # zur Zeit (ein Strang), parallel zu den Analyse-Straengen — dieselbe
        # Gleichzeitigkeit, die der Dienst heute ueber getrennte Prozesse und
        # Platz-Klassen herstellt, nur ohne den zweiten GPU-Kontext.
        (self.schlange if typ == "analyze" else self.bg_schlange).put(lauf)

    def arbeiter(self, nr):
        """EIN Rechenstrang: Jobs aus der Schlange holen, rechnen, antworten."""
        self._schlange_fahren(self.schlange)

    def bg_arbeiter(self):
        """DER Hintergrund-Strang (E2c): Ernte, Norm, refqs, Vorschlaege, Sammeln,
        Pass-Ernte, Rechenprobe, Koerper — einer nach dem anderen."""
        self._schlange_fahren(self.bg_schlange)

    def _schlange_fahren(self, schlange):
        while True:
            lauf = schlange.get()
            if lauf is None:
                return
            try:
                antwort = self.job_rechnen(lauf)
            except BaseException as e:                     # noqa: BLE001
                antwort = {"id": lauf.id, "ok": False,
                           "fehler": f"{type(e).__name__}: {e}"}
            finally:
                self._abmelden(lauf)
            self.antworten(antwort)

    def job_rechnen(self, lauf):
        """EIN Job. Die Antwortfelder sind die von worker._job_ausfuehren
        (worker.py:968-991), damit der Dienst nichts umlernen muss; dazu die neuen
        strukturierten Felder (Punkt 3)."""
        job = lauf.job
        lauf.t_lauf0, lauf.cpu0 = time.monotonic(), time.thread_time()
        lauf.log = JobLog(job.get("log") or os.devnull)
        ok, fehler, verwurf = True, None, None
        zusatz = {}
        opt = {"unbekannt": []}
        # .531 EIN ZWEITER ANLAUF, und nur EINER: trifft der eigene Arena-Deckel,
        # bringt ein sofortiger Wiederholungsversuch nichts — er traefe dieselbe
        # Arithmetik. Erst muss Platz entstehen (Verfall der aeltesten
        # Zusatz-Geometrie), dann lohnt der zweite Anlauf. Der Wiederanlauf ist
        # verlustfrei, weil die Analyse ueber `results.jsonl` fortsetzt und
        # bereits geschriebene Labels nicht neu rechnet.
        for _versuch in (1, 2):
            ok, fehler, verwurf = True, None, None
            zusatz = {}
            try:
                if lauf.typ != "analyze":
                    zusatz = self.hintergrund_lauf(lauf, job)
                else:
                    opt = felder_lesen(job)                # E3.1: Felder statt argv
                    if opt["unbekannt"]:
                        raise ValueError("unbekannte Job-Vorgaben: "
                                         + " ".join(opt["unbekannt"]))
                    zusatz = self.analyse_lauf(lauf, opt, job)
            except SystemExit as e:                        # kontrollierter Abbruch
                ok, fehler = (e.code in (0, None)), f"exit {e.code}"
                if not ok:
                    lauf.log.zeile(f"FEHLER: {e.code}")
            except Exception as e:                         # noqa: BLE001
                ok, fehler = False, einzeilig(f"{type(e).__name__}: {e}")
                lauf.log.zeile(f"FEHLER: {fehler}")
                # E-P7 (.507): die Einordnung der Clip-Ausnahmen lebt in
                # core.frames — die Akte trennt damit „Frigate hat den Clip nicht
                # (mehr)" vom allgemeinen Abbruch. Eine Einordnung darf nie die
                # Antwort kosten.
                try:
                    verwurf = clipcache.verwurf_grund(e)
                except Exception:                          # noqa: BLE001
                    verwurf = None
                art = self.vram_druck_art(f"{type(e).__name__}: {e}")
                if art:
                    self.druck_buchen(art, f"job {lauf.id}: {fehler}")
                    verwurf = verwurf or "speicher_knapp"
                    if (art == "deckel" and _versuch == 1
                            and lauf.id not in self._vram_wiederholt
                            and self.vram_verfall_erzwingen(lauf)):
                        self._vram_wiederholt.add(lauf.id)
                        self.zaehler["vram_wiederholungen"] += 1
                        prozess_log(f"vram pressure: job {lauf.id} retried after "
                                    f"the oldest extra geometry expired — the "
                                    f"analysis resumes from results.jsonl")
                        continue
            break
        lauf.log.schliessen()
        antwort = {"id": lauf.id, "ok": ok,
                   "cpu_s": round(time.thread_time() - lauf.cpu0, 1),
                   "wall_s": round(time.monotonic() - lauf.t_lauf0, 1),
                   "rss_mb": rss_mb(), "vmhwm_mb": vmhwm_mb()}
        # Wartezeit in der Schlange ist KEINE Analysezeit. Der Dienst rechnet sie
        # heute schon heraus, wenn er sie kennt (verifyd.py Nachbesserung W7: sonst
        # erfindet die Events-Anzeige eine Analysedauer und die Watchdog-Einstufung
        # kippt) — mit N Rechenstraengen entsteht sie hier und muss von hier kommen.
        antwort["warte_s"] = round(lauf.t_lauf0 - lauf.t0, 1)
        antwort["rss_spitze_mb"] = max(self.speicher.spitze, antwort["rss_mb"])
        antwort["fussabdruck_mb"] = fussabdruck_mb()
        # Der Verteiler-Rueckfall auf GETRENNTE Laeufe faellt HIER an, nicht im
        # Dienst (worker.py:976-984) — kumulativ ueber die Lebenszeit des Prozesses.
        antwort["frame_rueckfaelle"] = int(clipcache.RUECKFAELLE.get("n") or 0)
        # Die drei Marken, die verifyd heute aus dem Log hebt — strukturiert.
        antwort["bindung"] = dict(self.bindung)
        # E2c: worauf die Gesichts-Rechnung der ALT-Wege laeuft. Solange niemand sie
        # gebraucht hat, steht hier `gebaut: false` — eine Behauptung ueber Stufen,
        # die es noch nicht gibt, waere genau die Diagnose-Luege (K1).
        if self.fabrik is not None:
            antwort["bindung"]["bild_weg"] = self.fabrik.auskunft()
        antwort["provider_guard"] = "ok" if self.bindung.get("gebunden") else "failed"
        # E2d: was die Kompilat-Probe zuletzt gesagt hat — strukturiert, nicht im Log.
        antwort["kompilat_probe"] = dict(self.kompilat_bericht)
        # E3.4: dasselbe fuer die Kurzform der Start-Proben. Sie steht in JEDER
        # Antwort, nicht nur in der ihres eigenen Jobs — die Frage „hat dieser
        # Prozess seinen Selbstbeweis bestanden?" gehoert zu jedem Urteil, das er
        # faellt, nicht nur zum Probe-Job.
        antwort["startprobe"] = dict(self.startprobe_bericht)
        # .532: der EIGENE Kartenanteil wird HIER gemessen — nach der Analyse,
        # vor dem Bericht, damit die frische Zahl in der Antwort steht. Nur fuer
        # Analyse-Jobs: ein Hintergrund-Job rechnet nicht auf der Karte, und
        # eine Zeile je Ping waere Rauschen.
        if lauf.typ == "analyze" and self.auf_karte():
            try:
                self.vram_eigen_melden(lauf)
            except Exception as e:                         # noqa: BLE001
                prozess_log(f"vram own: could not be reported "
                            f"({type(e).__name__}: {e})")
        # .534 (B3): dieselbe Kadenz fuer den CONTAINER-Speicher, aber OHNE die
        # Karten-Bedingung — auf der Feldmaschine liefert die Karten-Sonde je
        # Prozess nichts, und genau dort fehlt die RAM-Zahl.
        if lauf.typ == "analyze":
            try:
                self.ram_eigen_melden(lauf)
            except Exception as e:                         # noqa: BLE001
                prozess_log(f"ram own: could not be reported "
                            f"({type(e).__name__}: {e})")
        # E6 (17.09.2026): dieselbe Kadenz fuer die AMD-Speicherlage aus sysfs.
        # Sie ist auf diesem Backend die EINZIGE Karten-Auskunft — der
        # MIGraphX-EP kennt keinen auswertbaren Speicherdeckel (Provider-Optionen
        # `migraphx_mem_limit`/`migraphx_arena_extend_strategy` sind in 1.27.1
        # wirkungslos), also gibt es nichts zu deckeln, nur zu beobachten. Die
        # Engine liefert die Zahlen; `worker_dienst` muss nichts ueber amdgpu
        # wissen. Nicht lesbar -> genau EINE laute Zeile, dann still (dort).
        _spei = getattr(self.engine, "speicher_melden", None)
        if lauf.typ == "analyze" and _spei is not None:
            try:
                _spei(f"after job {lauf.id}")
            except Exception as e:                         # noqa: BLE001
                prozess_log(f"gpu memory: could not be reported "
                            f"({type(e).__name__}: {e})")
        # .531: derselbe Kartenhaushalt wie im Lebenszeichen. Er gehoert zu jedem
        # Urteil, das dieser Prozess faellt — ein Ereignis, das unter Kartendruck
        # gerechnet wurde, ist etwas anderes als eines aus dem Normalbetrieb.
        _vb = self.vram_bericht()
        if _vb is not None:
            antwort["vram"] = _vb
        # .534 (B3): der Container-Speicher gehoert zu jedem Urteil genauso wie
        # der Kartenspeicher — und er ist die Zahl, aus der der Basiswert
        # `worker_rss_max_mb` kuenftig gemessen statt geschaetzt wird.
        antwort["ram"] = self.ram_bericht()
        # .534 (B5): die Zeiten, die NUR dieser Prozess kennt. Der Dienst legt
        # seine eigenen daneben (Warten in der Schlange, Uebergabe, Schreiben)
        # und schreibt daraus EINE Bilanzzeile je Ereignis.
        if lauf.typ == "analyze":
            antwort["zeiten"] = {"abruf_s": lauf.abruf_s,
                                 "abruf_bytes": lauf.abruf_bytes,
                                 "abruf_quelle": lauf.abruf_quelle,
                                 "erstes_bild_s": lauf.erstes_bild_s,
                                 "decoder": lauf.decoder,
                                 "kompilat_s": round(lauf.kompilat_s, 2) or None,
                                 "staffel_s": round(lauf.staffel_s, 2) or None}
        # E3.3 / Bauplan 2e — DER FELDSCHNITT: `placement_fallback` ist die Liste
        # DIESES Jobs, nicht mehr die des Prozesses.
        #
        # Bis E3.1 stand hier die kumulative Menge aller Rueckfall-Arten, die der
        # PROZESS je gesehen hat. Der Leser drueben (verifyd.py, Ereignis-Weg)
        # schreibt daraus je Ereignis eine Zeile „fell back to software/CPU for X" —
        # mit der Prozess-Menge behauptet er das ab dem ersten Rueckfall fuer JEDES
        # weitere Ereignis desselben Prozesses, auch fuer die hundert, die sauber auf
        # der Hardware liefen. Das ist genau die luegende Diagnose (K1), und zwar in
        # der teuersten Richtung: sie macht den echten Rueckfall unauffindbar, weil
        # die Zeile ohnehin immer dasteht. `lauf.rueckfaelle` fuehrt `rueckfall_melden`
        # ohnehin schon je Job (eine Zeile je Art und Ereignis, User-Auflage 13.09.);
        # sie war nur nie die Quelle des Feldes.
        antwort["placement_fallback"] = sorted(lauf.rueckfaelle)
        # Die Prozess-Summe bleibt DANEBEN erhalten — sie ist die Groesse, die in
        # /health gehoert („wie oft ist dieser Worker insgesamt zurueckgefallen"),
        # und sie hat einen anderen Namen, weil sie eine andere Frage beantwortet.
        antwort["placement_fallback_prozess"] = sorted(
            k[len("rueckfall_"):] for k in self.zaehler if k.startswith("rueckfall_"))
        if lauf.kompilat_n:
            # E3.3 (W2-B29): der Kompilat-/Geometrie-Bau, DIESEM Job gebucht. Ohne das
            # Feld steckt der Bauschritt unsichtbar in `wall_s` und `fussabdruck_mb`.
            antwort["kompilat_bau"] = {"n": lauf.kompilat_n,
                                       "s": round(lauf.kompilat_s, 1),
                                       "fussabdruck_delta_mb": lauf.kompilat_mb}
        if lauf.staffel_n:
            # .529: die Zeit, die dieser Job auf den Bau eines ANDEREN Strangs
            # gewartet hat. Sie steckt in `wall_s`, gehoert aber weder zur Analyse
            # noch zum eigenen Bau — ohne dieses Feld sieht der Betreiber einen
            # langsamen Job und nicht die Staffelung, die ihn davor bewahrt hat,
            # gemeinsam mit dem Nachbarn die Karte zu sprengen.
            antwort["staffel"] = {"n": lauf.staffel_n,
                                  "s": round(lauf.staffel_s, 1)}
        if lauf.gemeldet:
            antwort["frist_gerissen"] = True
        antwort.update(zusatz)
        if fehler:
            antwort["fehler"] = fehler
        if verwurf:
            antwort["verwurf_grund"] = verwurf
        return antwort

    # ---------------------------------------------------------- Hintergrund-Jobs (E2c)
    def hintergrund_lauf(self, lauf, job):
        """EIN Nicht-Analyse-Job — Zweig fuer Zweig die Aufrufe aus
        `worker._job_ausfuehren` (worker.py:694-947).

        WAS HIER GLEICH BLEIBT: die Aufrufe selbst, ihre Argumente, ihre
        Antwortfelder. `anlernen.py`, `core/ernte.py`, `core/normlauf.py` und
        `core/passernte.py` sind unveraendert; sie bekommen ihren Embedder wie immer
        ueber `face_audit.Embedder()`, nur liefert die Fabrik jetzt den Engine-Adapter
        (engine_bauen -> bild_kern.Fabrik). Das ist derselbe Griff, mit dem der alte
        Worker seit 0.1.0.38 seinen warmen Embedder untergeschoben hat.

        WAS WEGFAELLT, und warum es wegfallen DARF: die NormMass-Budget-Mechanik
        (`worker._normmass_fuer_ernte`, Bauspitze 2700 MB samt Anmeldung bei der
        RSS-Wache, worker.py:113-203). Sie schuetzte den ERSTBAU einer zweiten
        adaface-Session mit ihren eigenen Kompilaten. Den gibt es nicht mehr: die
        Feature-Norm ist der zweite Ausgang der r-Stufe, die dieser Prozess fuer die
        Analyse ohnehin haelt. Was der Bild-Weg zusaetzlich kostet, ist das
        Breite-1-Kompilat derselben Modelle — beziffert im E2c-Gate, nicht geschaetzt.

        WAS BLEIBT, WO ES IST: `core/guete` (e/t), `pose_wache` (p),
        `face_audit.StrukturMass` und der Personen-Pfad binden alle den CPU-Provider
        (Fundstellen im Kopf von bild_kern.py) — ORT-CPU vertraegt sich mit dem
        OV-Kern, also wird dort nichts angefasst.

        EHRLICHE GRENZE der Log-Umleitung: diese Wege drucken ihren Fortschritt nach
        stdout (sie haben kein `log=`-Argument); `worker.py` fing das per dup2 ab, was
        im Mehr-Job-Betrieb nicht geht (W2-B1). Hier wird stattdessen `sys.stdout` fuer
        die Dauer des Jobs auf das Job-Log gelegt. Das ist prozessweit — druckt in
        derselben Zeit ein Analyse-Strang nach stdout, landet seine Zeile im Job-Log
        dieses Jobs. Heute druckt dort keiner (die Analyse schreibt ueber JobLog), und
        Hintergrund-Jobs laufen einer zur Zeit; die Grenze steht trotzdem hier."""
        typ = lauf.typ
        with contextlib.redirect_stdout(_LogSenke(lauf.log)):
            return self._hintergrund(lauf, job, typ)

    def _hintergrund(self, lauf, job, typ):
        if typ == "sammle":
            import anlernen                                # noqa: PLC0415
            # .536 B3: die Bilanz des Haeppchens reist als ANTWORTFELD zurueck —
            # bis .535 fischte der Dienst seine Summe mit einem regulaeren
            # Ausdruck aus dem Log-Text („N faces collected"). Das Feld traegt
            # ausserdem, was der Dienst fuer die naechsten Haeppchen braucht:
            # `offen` (was der Zeit-Deckel liegen liess), `dauer_s`/`prolog_s`/
            # `clip_s` fuer den Rechenfaktor und `cache` fuer die kalte
            # Prolog-Reserve.
            erg = anlernen.sammle(float(job.get("tage", 0.1)),
                                  mit_migriere=bool(job.get("mit_migriere", False)),
                                  kalib_deckel=job.get("kalib_deckel"),
                                  nur_eids=job.get("nur_eids"),
                                  zeit_deckel_s=job.get("zeit_deckel_s"))
            return {"sammle": erg if isinstance(erg, dict) else {"neu": int(erg or 0)}}
        if typ == "vorschlaege":
            import anlernen                                # noqa: PLC0415
            _kw = {}
            if job.get("minkante") is not None:
                _kw["min_kante"] = int(job["minkante"])
            if job.get("unscharf") is not None:
                _kw["unscharf_max"] = int(job["unscharf"])
            if job.get("tage") is not None:
                _kw["tage"] = float(job["tage"])
            _dg = {}
            anlernen.vorschlaege_person(
                job["person"], norm_latte=job.get("norm_latte"),
                emb=face_audit.Embedder(), diagnose=_dg, **_kw)
            return {"vorschlaege": {
                "person": job["person"],
                "events": int(_dg.get("events") or 0),
                "geprueft": int(_dg.get("geprueft") or 0),
                "cache_treffer": int(_dg.get("cache_treffer") or 0),
                "cache_neu": int(_dg.get("cache_neu") or 0),
                "empfohlen": int(_dg.get("empfohlen") or 0),
                "neutral": int(_dg.get("neutral") or 0),
                "gedeckelt": bool(_dg.get("gedeckelt")),
                "dominant": _dg.get("dominant")}}
        if typ == "refqs":
            import anlernen                                # noqa: PLC0415
            _dg, _kw = {}, {}
            if job.get("minkante") is not None:
                _kw["min_kante"] = int(job["minkante"])
            if job.get("unscharf") is not None:
                _kw["unscharf_max"] = int(job["unscharf"])
            if job.get("dupsim") is not None:
                _kw["dup_sim"] = float(job["dupsim"])
            anlernen.pruefe_referenzen_lauf(
                person=None,                               # der Lauf ist IMMER ungefiltert
                norm_latte=job.get("norm_latte"),
                pruef_latten=job.get("pruef_latten"),
                emb=face_audit.Embedder(), diagnose=_dg, **_kw)
            return {"refqs": {
                "gesamt": int(_dg.get("gesamt") or 0),
                "gemessen": int(_dg.get("gemessen") or 0),
                "guete_nachgemessen": int(_dg.get("guete_nachgemessen") or 0),
                "guete_deckung": int(_dg.get("guete_deckung") or 0),
                "aus_speicher": int(_dg.get("aus_speicher") or 0),
                "beiwert": int(_dg.get("beiwert") or 0),
                "kamera_gesucht": int(_dg.get("kamera_gesucht") or 0),
                "kamera_gefunden": int(_dg.get("kamera_gefunden") or 0),
                "guete_da": bool(_dg.get("guete_da"))}}
        if typ == "ernte":
            from core import ernte as _ernte                # noqa: PLC0415
            eid = job["eid"]
            # Clip-Beschaffung wie im Analyse-Zweig: jeder Schalter als ARGUMENT
            # (W2-B2), kein Modulglobal. `clip_erzeugung`/`clip_tor` kommen aus dem
            # Job wie bei worker.py:796-798.
            vid = clipcache.clip_holen(
                eid, frigate_url=os.environ.get("FRIGATE_URL", ""),
                quelle=job.get("clip_quelle"), alter_min=job.get("clip_alter_min"),
                erzeugung=bool(job.get("clip_erzeugung")),
                erzeugung_deckel_s=job.get("clip_erzeugung_deckel_s"),
                tor_n=int(job.get("clip_tor") or 0),
                tor_deckel_s=job.get("clip_tor_deckel_s"),
                # E3.3 (Bauplan 2f, Deckungsluecke aus E2c): der VOD-Weg als
                # ARGUMENT je Job — s. die Fundstelle im Analyse-Zweig.
                vod=_clip_vod(job),
                dbg=((lambda z: lauf.log.zeile(z)) if job.get("clip_dbg") else None))
            try:
                return _ernte.ernte_event(
                    vid, eid, job.get("kamera"), float(job.get("ts") or 0),
                    float(job.get("fps_sample") or 3), job["schwellen"],
                    job["lauf_dir"], emb=face_audit.Embedder(),
                    nachmess=bool(job.get("nachmess")),
                    struktur_mass=(self.strukturmass()
                                   if job["schwellen"].get("struktur_min") else None),
                    quelle=job.get("quelle"), kalib=job.get("kalib"),
                    sieb=job.get("sieb"))
            finally:
                clipcache.frei(eid)                        # nie eine Pin-Waise
        if typ == "norm":
            from core import normlauf as _nl                # noqa: PLC0415
            nm = face_audit.NormMass()
            _messen = None
            if nm is not None and getattr(nm, "ok", False):
                # BATCH 1, unveraendert: `BildStufen.BREITE` ist 1, der Adapter
                # rechnet je Warp einen Aufruf. Die Messbasis bleibt damit die des
                # Bestands (core/normlauf.py, „NormMass driftet zwischen
                # Batchgroessen").
                def _messen(warp, _nm=nm):
                    return float(_nm.feature_norm([warp])[0])
            else:
                lauf.log.zeile(f"   (Feature-Norm nicht verfuegbar: "
                               f"{getattr(nm, 'grund', '?')} — Lauf ohne diese Achse)")
            return {"norm": _nl.norm_job(
                job["lauf_dir"], job.get("eids") or [],
                job.get("schwellen") or {}, job.get("latten") or {},
                messen=_messen, log=lauf.log.zeile)}
        if typ == "passernte":
            import anlernen as _al_pe                       # noqa: PLC0415
            from core import passernte as _pe               # noqa: PLC0415
            _emb_pe = face_audit.Embedder()
            _refs_pe = _al_pe.refs_matrix(_emb_pe)
            if not len(_refs_pe.get(job["person"], [])):
                _refs_pe = _al_pe.lade_master_refs(_emb_pe)
            return {"passernte": _pe.passernte_job(
                job["lauf_dir"], job.get("eids") or [], job["person"],
                _refs_pe, job.get("id_werte") or {},
                int(job.get("je_event") or 0), log=lauf.log.zeile)}
        if typ == "rechenprobe":
            return self.rechenprobe(lauf, job)
        if typ == "startprobe":
            return self.startprobe(lauf, job)
        if typ == "koerper":
            from core import personlive as _plv             # noqa: PLC0415
            return {"u": _plv.urteilen(
                job["data_dir"], os.environ.get("FRIGATE_URL", ""),
                job["eid"], kontrolle=job.get("kontrolle"),
                still=bool(job.get("still")),
                ram_budget_mb=self.koerper_budget(job))}    # E3.3: je Prozess geteilt
        if typ == "personlauf_ernte":
            from core.personlauf import _proto              # noqa: PLC0415
            from core import personernte as _pe             # noqa: PLC0415
            _proto()
            import pfad_snapshots                           # noqa: PLC0415
            if self._werk.get("wache") is None:
                from pose_wache import PoseWache            # noqa: PLC0415
                self._werk["wache"] = PoseWache()
            budget = self.koerper_budget(job)               # E3.3: je Prozess geteilt

            def _extraktor(eid):
                return pfad_snapshots.event_verarbeiten({"eid": eid},
                                                        ram_budget_mb=budget)

            return {"r": _pe.ernte_event(job["data_dir"], job["lauf_id"], job["job"],
                                         self._werk["wache"], _extraktor)}
        raise ValueError(f"unbekannter typ '{typ}'")

    def strukturmass(self):
        """Die warme StrukturMass dieses Prozesses (worker._strukturmass_holen,
        worker.py:317-332): LAZY, ohne Budget-Pruefung — ihr 5-MB-Modell kostet neben
        einer schon warmen Session gemessen 0 MB. Sie bindet den CPU-Provider
        (face_audit.py:1787) und bleibt deshalb in E2c unveraendert."""
        if self._werk.get("struktur") is None:
            self._werk["struktur"] = face_audit.StrukturMass()
        return self._werk["struktur"]

    def rechenprobe(self, lauf, job):
        """Die Rechenprobe — in E2c MINIMAL angeschlossen, und das mit Ansage.

        Was sie heute tut (worker.py:904-909 -> core.rechenprobe.messen): jedes Modell
        des MODELL_VERTRAGs auf seinem Betriebs-Geraet gegen die CPU rechnen, mit einem
        eigenen ORT-Session-Bauer (worker._rechenprobe_bauer). Genau dieser Bauer ist
        der ORT-OV-Weg, den E2c abschafft — ihn hier zu rufen hiesse, die ABI-Klemme
        wieder aufzumachen.

        Was sie ihn E2c tut: sie MELDET, worauf dieser Prozess wirklich rechnet — die
        Engine-Bindung, die Geraete, die gebauten Stufen des Bild-Wegs. Das ist die
        Frage, fuer die verifyd sie im Boot-Selbstcheck ruft („rechnet der
        Beschleuniger, oder luegt die Diagnose"), und sie wird damit beantwortet,
        ohne dass ein zweiter Kontext entsteht.

        WAS FEHLT, benannt fuer E3: der WERTE-Vergleich Geraet gegen CPU je Modell.
        Ihn auf der Engine nachzubauen heisst, jedes Vertrags-Modell zusaetzlich als
        CPU-Graph zu bauen — ein eigener Bauschritt mit eigenem Speicher-Posten, nicht
        ein Anhaengsel dieser Etappe. Solange er fehlt, liefert die Antwort KEINE
        Mess-Zeilen und sagt das; ein leeres `rechenprobe` ist im Dienst bereits ein
        bekannter Zustand (Budget zu knapp, worker.py:303-307)."""
        grund = ("compute probe reduced to a binding report (E2c): the value "
                 "comparison per model still runs on the old onnxruntime stack and "
                 "would reopen the ABI clash that E2c removes — rebuilding it on the "
                 "engine is an E3 step")
        lauf.log.zeile("   (" + grund + ")")
        aus = {"rechenprobe": [], "rechenprobe_grund": grund,
               "engine_geraete": dict(self.bindung)}
        try:
            aus["engine_geraete"]["bild_weg"] = (self.fabrik.auskunft()
                                                 if self.fabrik else None)
        except Exception as e:                             # noqa: BLE001
            aus["engine_geraete"]["bild_weg"] = f"{type(e).__name__}: {e}"
        # E3.5: WELCHE MODELL-DATEIEN DIESER PROZESS WIRKLICH HAT. Die cuda-Engine
        # backt ihre fp16-Artefakte seit E3.5 ins Image und prueft deren md5 gegen das
        # mitgelieferte Manifest (engine_cuda.fp16_bestand). Der Bericht gehoert genau
        # hierher: die Rechenprobe ist die Stelle, an der verifyd fragt „rechnet der
        # Beschleuniger, oder luegt die Diagnose" — und sie muss die AUSGELIEFERTEN
        # Dateien nennen, nicht die fp32-Originale. Engines ohne fp16-Bestand (ov)
        # haben das Feld nicht; dann steht es auch nicht im Bericht.
        bericht = getattr(self.engine, "fp16_bericht", None)
        if bericht is not None:
            aus["engine_geraete"]["fp16"] = bericht
        return aus

    # ---------------------------------------------------------- Selbstbeweis (E3.4)
    def pruefbild(self):
        """DER PRUEFVEKTOR DER KURZFORM: ein fester 112er-Ausschnitt, durch die
        ERKENNUNGS-Stufe des Bild-Wegs gerechnet. -> (embedding-Liste, feature-norm)

        WARUM NICHT `Satz.probe`: die haengt an einer gebauten Video-GEOMETRIE. Nach
        einem Betriebs-Neustart gibt es keine — der erste Clip baut sie erst, und bis
        dahin waere die Kurzform blind. Der Bild-Weg dagegen steht ohne Clip und ohne
        Geometrie; er rechnet DIESELBEN Modelle (E2c: eine Fabrik, ein Kompilat).

        DAS BILD IST KEIN BILD, sondern eine Rechenvorschrift: `engine_ov.PROBE_SAAT`
        — dieselbe Saat, aus der die Kompilat-Probe ihren NV12-Pruefvektor baut. Eine
        zweite Saat (oder gar eine JPEG-Datei im Image) gibt es bewusst nicht: eine
        Konserve waere Material im Release (verboten) und eine zweite Zahl im Haus.
        Die Formel ist die von `engine_ov.probe_nv12`, auf BGR uebertragen; sie ist
        deterministisch und auf jeder Maschine dieselbe."""
        try:
            from engine_ov import PROBE_SAAT                 # noqa: PLC0415
        except Exception:                                    # noqa: BLE001
            # Auf einem Backend ohne engine_ov (CUDA-Image) liegt die Saat nicht
            # daneben. Sie ist eine reine ZAHL, kein OpenVINO-Ding — deshalb hier der
            # dokumentierte Rueckfall auf denselben Wert statt eines zweiten Literals
            # irgendwo im Haus.
            PROBE_SAAT = 20260913                            # engine_ov.py:87
        i, j = np.meshgrid(np.arange(112), np.arange(112), indexing="ij")
        b = (16 + ((i * 7 + j * 13 + ((i * j) >> 6) + PROBE_SAAT) % 220)).astype(np.uint8)
        g = (16 + ((i * 11 + j * 5 + PROBE_SAAT) % 225)).astype(np.uint8)
        r = (16 + ((i * 3 + j * 17 + PROBE_SAAT) % 225)).astype(np.uint8)
        crop = np.stack([b, g, r], axis=2)
        E, N = self.bild_rechner().embeddings([crop])
        return np.asarray(E[0], np.float64).tolist(), round(float(N[0]), 4)

    def startprobe(self, lauf, job):
        """DIE KURZFORM DER START-PROBEN (Konzept §4 Schicht 1, E3.4).

        Die VOLLFORM laeuft im Boot-Exklusivfenster (verifyd ruft dort die
        Rechenprobe als Job). Sie kann das, weil dort nichts anderes auf der Karte
        rechnet. Ein BETRIEBS-Neustart hat dieses Fenster nicht — der Prozess steht
        neben Live-Waechtern und laufenden Jobs wieder auf. Trotzdem darf er nicht
        stumm wieder Namen liefern: die belegten Im-Lauf-Klassen (Haenger nach 36-111
        Aufrufen, stilles 0-Gesichter-Ergebnis, CL_OUT_OF_RESOURCES beim zweiten
        Event) entstehen genau in solchen Neustarts, und „ein Neustart ist kein
        Ausweg" ist der Satz, an dem dieses Konzept haengt.

        DIE KURZFORM BRAUCHT KEINE EXKLUSIVITAET, weil sie nichts MISST, was von der
        Nachbarlast abhinge — sie fragt zwei Dinge:
          1. BIND-CHECK: haelt die Geraete-Bindung, und sind Referenzen mit Vektoren
             da? (Beides ist Zustand, keine Messung.)
          2. PRUEFBILD: rechnet die ERKENNUNGS-Stufe noch dasselbe wie bei der
             Eichung? Der Vektor ist deterministisch (s. `pruefbild`), der Vergleich
             derselbe wie bei der Kompilat-Probe (`probe_vergleich` gegen die
             Eichmarke, Kosinus + Feature-Norm, unter demselben Umfeld-Vorbehalt).
             Auf CUDA ist das der EINZIGE Kompilat-Nachweis ueberhaupt: `Satz.probe`
             gibt es dort nicht (s. engine_bauen).

        EIN HARTER BEFUND BEENDET DEN JOB MIT FEHLER — der Prozess produziert keine
        Namen aus einem Kompilat, das nachweislich anders rechnet. Ein Umfeld-Wechsel
        (andere OpenVINO-Fassung, anderer Treiber, getauschtes ONNX) erneuert die
        Marke LAUT, statt Alarm zu schlagen; dort sind andere Zahlen richtig."""
        t0 = time.monotonic()
        grund = str(job.get("grund") or "?")
        bericht = {"stand": "?", "grund": grund,
                   "gebunden": bool(self.bindung.get("gebunden")),
                   "geraet": self.bindung.get("geraet"),
                   "engine": self.bindung.get("engine"),
                   "kompilat_wache": self.bindung.get("kompilat_wache"),
                   "personen_mit_vektoren": len(self.mit_refs or [])}
        if not bericht["gebunden"]:
            bericht["stand"] = "bindung weg"
            self.startprobe_bericht = bericht
            lauf.log.zeile("FEHLER: short start proof: the accelerator is no longer "
                           "bound — this process must not produce names")
            raise RuntimeError("short start proof: accelerator not bound")
        emb, norm = self.pruefbild()
        endlich = all(np.isfinite(emb)) and len(emb) == 512 and norm > 0
        bericht["pruefbild"] = {"dim": len(emb), "norm": norm, "endlich": endlich}
        if not endlich:
            bericht["stand"] = "pruefbild unbrauchbar"
            self.startprobe_bericht = bericht
            lauf.log.zeile(f"FEHLER: short start proof: the check image produced an "
                           f"unusable embedding (dim {len(emb)}, norm {norm})")
            raise RuntimeError("short start proof: unusable check embedding")
        # Gegen DIESELBE Eichmarke wie die Kompilat-Probe, unter dem Schluessel
        # „bild": `probe_vergleich` vergleicht die Erkennungs-Stufe als ZAHL
        # (Kosinus + Feature-Norm) und die uebrigen Stufen als Fingerabdruck — die
        # fehlen hier auf beiden Seiten und sind damit gleich.
        ist = {"r_norm": [norm], "_r_emb": emb}
        urteil, befunde = self._eichen("bild", ist)
        bericht["stand"] = urteil
        if befunde:
            bericht["befunde"] = befunde
        bericht["probe_s"] = round(time.monotonic() - t0, 2)
        self.startprobe_bericht = bericht
        if urteil == "abweichung":
            self.zaehler["startprobe_abweichung"] += 1
            text = ("short start proof FAILED: this process computes the recognition "
                    "stage differently than the calibrated one — " + " | ".join(befunde))
            prozess_log("FATAL: " + text)
            lauf.log.zeile("FEHLER: " + text)
            raise RuntimeError(text)
        prozess_log(f"short start proof ({grund}): {urteil} — bound to "
                    f"{bericht['geraet']}, {bericht['personen_mit_vektoren']} "
                    f"person(s) with vectors, ||f|| {norm}"
                    + (f", notes: {' | '.join(befunde)}" if befunde else ""))
        return {"startprobe": bericht}

    def _eichen(self, marke, ist):
        """Einen Proben-Fingerabdruck gegen die Eichmarke halten -> (urteil, befunde).

        HERAUSGEZOGEN aus `kompilat_pruefen` (E3.4): dort stand die Marken-Mechanik
        — Datei lesen, Umfeld vergleichen, bei neuem Umfeld LAUT erneuern, bei
        fehlender Zeile eichen — mitten in der Geometrie-Probe. Die Kurzform braucht
        genau dieselbe Mechanik fuer ihren eigenen Schluessel; sie ein zweites Mal
        hinzuschreiben waere die Streuung, gegen die die Hausregel steht.
        -> ("geeicht", []) heisst „diese Zeile gab es noch nicht, sie steht jetzt"."""
        pfad = os.path.join(self.scratch, EICHMARKE_DATEI)
        with self._eich_schloss:
            eich = {}
            if os.path.exists(pfad):
                try:
                    eich = json.load(open(pfad, encoding="utf-8"))
                except Exception as e:                      # noqa: BLE001
                    prozess_log(f"calibration mark unreadable ({e}) — starting a new one")
                    eich = {}
            umfeld = self._eich_umfeld or eich_umfeld(self.engine)
            self._eich_umfeld = umfeld
            neu = eich.get("umfeld") != umfeld
            if neu and eich:
                prozess_log("compute environment changed (OpenVINO/driver/model/engine "
                            "code) — renewing the compiled-model calibration mark; other "
                            "numbers are correct here")
            if neu:
                eich = {"umfeld": umfeld, "geometrien": {}}
            soll = (eich.get("geometrien") or {}).get(marke)
            if soll is None:
                eich.setdefault("geometrien", {})[marke] = ist
                try:
                    with open(pfad, "w", encoding="utf-8") as f:
                        json.dump(eich, f, ensure_ascii=False, indent=1)
                except OSError as e:                        # noqa: BLE001
                    prozess_log(f"calibration mark not writable ({e}) — the probe "
                                f"cannot compare on the next start")
                return "geeicht", []
        return probe_vergleich(soll, ist)

    def analyse_lauf(self, lauf, opt, job):
        """Die Ereignis-Analyse eines Jobs: je eid ein Durchgang, results.jsonl,
        Bilder, Kandidaten. Der Rahmen ist der von analyze.py (Resume, Reihenfolge,
        Abbruchregeln), gerechnet wird mit dem Kern."""
        outdir = opt["dir"] or os.path.join(wk.WURZEL, "samples", "analyze")
        os.makedirs(outdir, exist_ok=True)
        results_pfad = os.path.join(outdir, "results.jsonl")
        # RESUME wie analyze.py:351-357: ein Label, das schon in results.jsonl steht,
        # wird uebersprungen. Daran haengen vier Stellen im Dienst (Re-Analyse legt
        # die Akte beiseite, Nachhol-Runde loescht sie, Roundtrip loescht sie
        # zwischen den Laeufen, qs.sh raeumt vorher auf) — der Resume MUSS bleiben.
        done = set()
        if os.path.exists(results_pfad):
            with open(results_pfad, encoding="utf-8") as f:
                for z in f:
                    try:
                        done.add(json.loads(z)["label"])
                    except Exception:                      # noqa: BLE001
                        pass
            if done:
                lauf.log.zeile(f"Resume: {len(done)} Clips bereits in results.jsonl, "
                               f"werden übersprungen.")
        lat, g_aus, pose_aus = latten_bauen(opt["argv_fest"], lauf.log)
        profil = mk_bilanz.profil(mk_bilanz.ZWECK_ANALYSE, {
            "det_min": float(opt["argv_fest"]["det_thresh"]),
            "guete_e_min": lat["guete_e"], "guete_t_min": lat["guete_t"],
            "pose_min": lat["pose"], "kante_min": lat["urteil_kante"]})
        personen = list(opt["persons"])
        # Jede angefragte Person muss einen Score bekommen, auch ohne Referenzen
        # (analyze.nn liefert dort -1.0) — der Kern baut sein `ohne`-dict aus dieser
        # Liste (worker_kern.py:917).
        alle = sorted(set(self.alle) | set(personen))
        bilanz = collections.Counter()
        frames_info = {}
        for k, eid in enumerate(opt["eids"]):
            label = (opt["labels"][k] if k < len(opt["labels"])
                     else os.path.basename(eid).split(".")[0])
            if label in done:
                lauf.log.zeile(f"\n=== {label} — bereits in results.jsonl, übersprungen ===")
                continue
            info = self.event_lauf(lauf, opt, job, eid, label, lat, g_aus, pose_aus,
                                   profil, personen, alle, outdir, results_pfad)
            for kk, vv in info.get("bilanz", {}).items():
                bilanz[kk] += vv
            frames_info = info.get("frames", frames_info)
        aus = {"frames": frames_info, "bilder": dict(bilanz)}
        if self.null_serie:
            # LAUF-WACHE, Rohsignal (Konzept §4 Schicht 3): „N Ereignisse in Folge
            # 0 Gesichter bei voller Frame-Zahl". Der Zaehler steht in der Antwort;
            # das URTEIL darueber (ab wann laut, Kurzprobe ausloesen) faellt beim
            # Dienst, der die Ereignisse ueber die Zeit sieht — nicht hier.
            aus["null_gesichter_serie"] = self.null_serie
        return aus

    def event_lauf(self, lauf, opt, job, eid, label, lat, g_aus, pose_aus, profil,
                   personen, alle, outdir, results_pfad):
        """EIN Event: Clip holen, rechnen, Bilder, Akte-Zeile."""
        fest = opt["argv_fest"]
        pin = None
        _t_abruf = time.monotonic()
        # .534 (Abnahme-Befund 15.09.): WOHER der Clip kam, wird VOR dem Abruf
        # festgestellt — danach liegt er in beiden Faellen im Cache, und die
        # Zeile „abruf 0.0 s" saehe fuer einen frischen Frigate-Zug genauso aus
        # wie fuer einen Treffer. Genau diese Unterscheidung wollte der Inhaber
        # sehen.
        _cache_vorher = False
        if not os.path.exists(eid):
            try:
                _cache_vorher = os.path.exists(clipcache.cache_pfad(eid))
            except Exception:                              # noqa: BLE001
                _cache_vorher = False
        if os.path.exists(eid):                            # lokaler Videopfad (analyze.py:510)
            vid = eid
            lauf.abruf_quelle = "datei"
        else:
            # W2-B2: alles als ARGUMENT, nichts ueber Modulglobals — inklusive der
            # Debug-Senke, die als einzige bisher nur prozessweit ging.
            vid = clipcache.clip_holen(
                eid, frigate_url=os.environ.get("FRIGATE_URL", ""),
                quelle=job.get("clip_quelle"), alter_min=job.get("clip_alter_min"),
                erzeugung=bool(job.get("clip_erzeugung")),
                erzeugung_deckel_s=job.get("clip_erzeugung_deckel_s"),
                tor_n=int(job.get("clip_tor") or 0),
                tor_deckel_s=job.get("clip_tor_deckel_s"),
                # E3.3 (Bauplan 2f): DIE LETZTE ARMIERUNG, die bis hier nur ueber ein
                # Modulglobal ging. `verifyd` schickt `clip_vod` seit .292 als
                # Job-Feld (verifyd.py:2171 fuer die Analyse, 11746/12018/13545 fuer
                # die Ernte) — `worker.py` armierte damit `core.frames.CLIP_VOD`
                # prozessweit (worker.py:665). Im Mehr-Job-Betrieb ist das ein
                # Wettrennen: zwei Jobs mit verschiedenem Schalter ziehen ihn sich
                # gegenseitig weg, und der VOD-Weg ist VERHALTEN, nicht Telemetrie
                # (er entscheidet, ob Frigates kranker Erzeugungspfad betreten wird).
                # Deshalb als Argument, dasselbe Muster wie `dbg=` in E2 (W2-B2).
                vod=_clip_vod(job),
                dbg=((lambda z: lauf.log.zeile(z)) if job.get("clip_dbg") else None))
            pin = eid
            # .534 (B5): WAS DER ABRUF GEKOSTET HAT. Ein Cache-Treffer misst hier
            # nahe null — und genau das ist die Auskunft, um die es geht: wie oft
            # der Platz wirklich auf Frigate wartet. Die Bytes stehen daneben,
            # weil eine Sekunde fuer 4 MB etwas anderes heisst als fuer 75.
            lauf.abruf_s = round(time.monotonic() - _t_abruf, 2)
            lauf.abruf_quelle = "cache" if _cache_vorher else "frigate"
            try:
                lauf.abruf_bytes = int(os.path.getsize(vid))
            except OSError:
                lauf.abruf_bytes = None
        _t_nach_abruf = time.monotonic()
        try:
            meta = decode._probe(vid) or {}
            W, H = int(meta.get("breite") or 0), int(meta.get("hoehe") or 0)
            fps = meta.get("fps") or 25
            if not (W and H):
                raise RuntimeError(f"keine Videogeometrie fuer {eid}")
            # .540 K-DECKEL: DIE Schrittweite kommt aus der EINEN Formel
            # (decode.sample_schritt — Herleitung, Messbasis und ehrliche Grenzen
            # stehen dort, nicht hier). Sie deckelt die Zahl der Sample-Frames je
            # Ereignis, indem sie die Schrittweite vergroessert: der Clip wird bis
            # zum Ende abgetastet, nur weiter auseinander. KEIN Frueh-Stopp — die
            # letzte Minute eines langen Auftritts bleibt genauso dicht abgetastet
            # wie die erste. `meta["pakete"]` ist die Clip-Laenge und kommt aus
            # DEMSELBEN ffprobe-Lauf eine Zeile hoeher (kein zweiter Parser).
            # Ohne Deckel (0, Vorgabe) ist `schritt` bitgleich zu vor .540.
            _deckel = int(float(fest.get("sample_deckel") or 0))
            schritt, _s_moegl, _s_verw = decode.sample_schritt(
                fps, float(fest["fps_sample"]), meta.get("pakete"), _deckel)
            _gekappt = (_s_moegl is not None and _s_verw is not None
                        and _s_verw < _s_moegl)
            g = self.geometrie(W, H, fps, lauf)
            wache = DecoderWache(vid, schritt)
            tor = EngineTor(self.engine, wache)
            vorrat = wk.Bildvorrat(W, H, lat, self.mit_refs, self.erk, self.modell)
            zaehler, zeiten = collections.Counter(), collections.Counter()
            zeilen, _frames = wk.event_rechnen(
                tor, g, vid, schritt, float(fest["det_thresh"]), fps,
                alle, self.mit_refs, self.erk, lat, zaehler, zeiten, vorrat)
            # .534 (B5): vom fertigen Clip bis zum ERSTEN gelieferten Bild. Darin
            # steckt der Decoder-Start und — wenn eine Geometrie erst gebaut
            # werden musste — der Bau; der steht als `kompilat_s` daneben, damit
            # beides unterscheidbar bleibt.
            if wache.t_erstes is not None:
                lauf.erstes_bild_s = round(wache.t_erstes - _t_nach_abruf, 2)
            lauf.decoder = (("sw (hw fell back)" if wache.hwdec_fallback
                             else wache.kette) or None)
        finally:
            if pin:
                clipcache.frei(pin)                        # nie eine Pin-Waise
        # --- Wachen-Zeilen VOR dem Ergebnisblock (analyze.py:796-809: qs schneidet
        #     mit tail das ENDE, die Ergebniszeilen muessen dort bleiben)
        if _gekappt:
            # .540: EINE kompakte Zeile je Ereignis, an dem der Deckel wirklich
            # gegriffen hat — kein Rauschen auf den 96 % der Ereignisse, die
            # darunter bleiben. Kein WARN: das hier ist eine bestellte Einstellung,
            # die tut, was sie soll, kein Ausfall. Die Zahlen daneben sind die, die
            # eine spaetere Auto-Kalibrierung braucht (und sie stehen zusaetzlich
            # in der Akte, s. results_zeile).
            self.zaehler["sample_gekappt"] += 1
            lauf.log.zeile(
                f"  sample budget: capped to {_s_verw} of {_s_moegl} sample frames "
                f"(cap {_deckel}, every {schritt}th frame instead of every "
                f"{max(1, int(round(fps / float(fest['fps_sample']))))}th, "
                f"spread evenly over the whole clip)")
        if wache.hwdec_fallback:
            # E2d, Konzept §4: LAUT, aber genau EINMAL je Ereignis (User 13.09.).
            # `rueckfall_melden` fuehrt den Zaehler und traegt die Art in
            # `placement_fallback` der Antwort — dieselbe Meldeform wie fuer jeden
            # anderen Rueckfall, kein zweiter Weg.
            self.rueckfall_melden(lauf, "hwdec", wache.hwdec_grund or "")
            # .531 DRUCK-SIGNAL 4: der NVDEC-ffmpeg liegt AUSSERHALB jeder
            # ORT-Arena (eigener Prozess). Faellt er zurueck, kann das an der
            # Karte liegen — und ein Deckel auf unserer Arena sieht davon nichts.
            if self.auf_karte():
                self.druck_buchen("hwdec", einzeilig(wache.hwdec_grund or "", 200))
            lauf.log.zeile(
                f"WARN: hardware decode unavailable — fell back to software decode "
                f"(same NV12 bytes, slower): {einzeilig(wache.hwdec_grund or '', 200)}")
        if wache.teilabbruch:
            # EINE Zeile je Ereignis (User 13.09.), Wortlaut wie analyze.py:809.
            self.rueckfall_melden(lauf, "hwdec", wache.teilabbruch)
            if self.auf_karte():
                self.druck_buchen("hwdec", einzeilig(wache.teilabbruch, 200))
            lauf.log.zeile("WARN: hardware decode aborted mid-clip — judged the readable part")
        if wache.unvollstaendig:
            lauf.log.zeile(
                f"WARN: clip incomplete — read {wache.gelesen} of {wache.soll} frames "
                f"({wache.verlust_pct:.0f}% lost"
                + (f", {wache.decoder_fehler} decoder errors" if wache.decoder_fehler else "")
                + "); judging the readable part (flagged)")
        fd_n = sum(1 for f in zeilen if f["fd"])
        lauf.log.zeile(
            f"\n=== {label}  ({eid}) — {wache.samples} Frames, {len(zeilen)} Gesichter ==="
            + (f"  [{fd_n} als Fehldetektion gefiltert (Zaehlung/Pool, nicht Urteil)]"
               if fd_n else ""))
        if wache.samples == 0:
            # DAS FEHLERSIGNAL (W1-M11): keine results-Zeile. verifyd wertet das als
            # `fehler` statt `unknown` (verifyd.py:2339-2342), und der SD4-
            # Fehlerserien-Waechter haengt daran. Der Wortlaut ist der von
            # analyze.py:814 — webui.bausteine.fehler_grund liest die letzte mit
            # „FEHLER" beginnende Zeile.
            lauf.log.zeile("  FEHLER: keine Frames lesbar — kein results-Eintrag fuer dieses Label")
            return {"frames": {"gelesen": 0, "soll": wache.soll, "samples": 0,
                               "kette": wache.kette, "leer": True,
                               **({"hwdec_fallback": True} if wache.hwdec_fallback else {})}}
        # --- Zusammenfassung und die Umrechnung der Indexbasis
        persons_voll = wk.zusammenfassen(zeilen, personen, lat)
        idx_karte = [i for i, f in enumerate(zeilen) if f["sc"] is not None]
        bilanz = vorrat.schreiben(outdir, label, eid, persons_voll, personen)
        for person in personen:
            rec = persons_voll.get(person)
            if not rec:
                continue
            # Die Marke, die qs.sh:12043/12072 und :312 greifen. Wortlaut und
            # Zahlenformat wie analyze.py:904-905, soweit die Kennwerte noch da sind.
            bl = (f"  Blick {rec.get('blick_n', 0)}×≥{lat['win_thresh']:.2f}"
                  f"/Anker≥{lat['urteil_anker']:.2f}" if lat["blick_fenster_s"] > 0 else "")
            lauf.log.zeile(
                f"  {person:<6} max {rec['max']:+.2f}  median {rec['median']:+.2f}  "
                f"n≥.4 {rec['n_ge40']}/{rec['n']}  "
                f"bestes 3s-Fenster {rec['win3s']}×≥{lat['win_thresh']:.2f}{bl}   "
                f"(bestes {rec['best_wh']} t={rec['best_t']:.0f}s)")
        stat = self.stat_bauen(zeilen, lat, g_aus, pose_aus)
        zeile = results_zeile(label, eid, zeilen, persons_fuer_akte(persons_voll, idx_karte),
                              wache, lat, stat, profil,
                              samples_moeglich=_s_moegl, sample_deckel=_deckel)
        # pro Clip SOFORT persistieren, geflusht (analyze.py:925-1004)
        with open(results_pfad, "a", encoding="utf-8") as rf:
            rf.write(json.dumps(zeile, default=float, ensure_ascii=False) + "\n")
            rf.flush()
        if bilanz.get("kandidaten"):
            lauf.log.zeile(f"  Enrollment-Kandidaten: {bilanz['kandidaten']}")
        # 0-Gesichter-Anomalie: volle Frame-Zahl, aber nichts gefunden.
        if len(zeilen) == 0 and not wache.unvollstaendig:
            self.null_serie += 1
            self.zaehler["null_gesichter"] += 1
        else:
            self.null_serie = 0
        return {"bilanz": bilanz,
                "frames": {"gelesen": wache.gelesen, "soll": wache.soll,
                           "samples": wache.samples, "kette": wache.kette,
                           "decoder_fehler": wache.decoder_fehler,
                           # .540: dasselbe Zahlenpaar wie in der Akte, damit es
                           # auch auf dem Rueckweg steht (der Rueckweg ist eine
                           # WEISSE LISTE, s. verifyd.py — was hier fehlt, ist
                           # drueben still weg).
                           **({"samples_moeglich": int(_s_moegl)}
                              if _s_moegl is not None else {}),
                           **({"sample_deckel": _deckel} if _gekappt else {}),
                           # E2d: das Feld, das decode.FrameIter seit jeher fuehrt —
                           # „HW angefordert, Software hat geliefert" (Konzept §4).
                           **({"hwdec_fallback": True,
                               "hwdec_grund": einzeilig(wache.hwdec_grund or "", 200)}
                              if wache.hwdec_fallback else {}),
                           **({"fehlen": True} if wache.unvollstaendig else {}),
                           **({"teilabbruch": wache.teilabbruch} if wache.teilabbruch else {})}}

    @staticmethod
    def stat_bauen(zeilen, lat, g_aus, pose_aus):
        """URT_G_STAT der Akte (analyze.py:130, :972-979).

        DIE BASIS IST EINE ANDERE, und das gehoert gesagt: analyze zaehlt je
        STIMM-KANDIDAT (Kante ok und irgendein Personen-Score ueber win_thresh) —
        eine Menge, die es auf dem Kaskaden-Weg nicht gibt, weil Scores erst NACH
        den Guete-Stufen entstehen. Gezaehlt wird deshalb je Fund, der die
        Guete-Stufen ueberhaupt erreicht hat:
          gemessen   ein Guete-Wert wurde wirklich gemessen
          fehler     0 — der Kern kennt keinen Mess-AUSNAHME-Weg; was sich nicht
                     messen laesst, faellt unter unmessbar (unten)
          stimmen_verworfen_unmessbar
                     der Fund verliert seine Stimme, WEIL ein Wert nicht messbar
                     war: er verliess die Kaskade an einer aktiven Latte, ohne dass
                     dort ein Wert entstand. Das ist die Zahl, die verifyd in die
                     Akte hebt (verifyd.py:14077-14081) und die den Preis der
                     Invariante „Messbarkeit vor Stimme" beziffert."""
        gemessen = sum(1 for f in zeilen if f["e"] is not None or f["t"] is not None)
        unmessbar = 0
        for f in zeilen:
            # E3.3 / Wirkstellen-Entscheid 14.09.: die Guete-Stufen e und t sieben die
            # KASKADE nicht mehr, sie messen nur (worker_kern.gpu_stufen). Ein nicht
            # messbarer Guete-Wert traegt deshalb kein `abbruch`-Zeichen mehr — er
            # kostet die Stimme erst in `zusammenfassen` (guete.stimme_ok,
            # fail-closed je Fund). Wuerde dieser Zaehler weiter nur auf `abbruch`
            # schauen, faellt er still auf 0, und der Preis der Invariante
            # „Messbarkeit vor Stimme" (CLAUDE.md) waere unsichtbar — genau das, was
            # er beziffern soll. Er fragt jetzt die Sache selbst: hat dieser Fund
            # eine AKTIVE Latte, deren Wert fehlt?
            ab = f["abbruch"]
            if ab not in (None, "p"):
                # An Kante oder Fehldetektion ausgeschieden: der Fund war nie ein
                # Stimm-Kandidat, seine fehlenden Guete-Werte sind kein Verlust.
                # (Dass e/t keine Abbruch-Stufe mehr sein koennen, macht diese
                # Abfrage zu dem, was sie meint: „hat er die Guete-Stufen ueberhaupt
                # erreicht?")
                continue
            if any(lat.get(k, 0) > 0 and f[w] is None
                   for k, w in (("guete_e", "e"), ("guete_t", "t"))):
                unmessbar += 1
                continue
            if ab == "p" and f["p"] is None and lat.get("pose", 0) > 0:
                unmessbar += 1
        stat = {"gemessen": gemessen, "fehler": 0,
                "stimmen_verworfen_unmessbar": unmessbar}
        if g_aus:
            stat["aus"] = g_aus
        if pose_aus:
            stat["pose_aus"] = pose_aus
        return stat

    # ---------------------------------------------------------- Lebenszyklus
    def start(self, log):
        self.engine_bauen()                                # ZUERST, s. referenzen()
        self.referenzen(log)
        self.speicher.__enter__()
        self.frist.__enter__()
        for i in range(self.threads):
            t = threading.Thread(target=self.arbeiter, args=(i,), name=f"rechner-{i}",
                                 daemon=False)
            t.start()
            self._arbeiter.append(t)
        # E2c: EIN Strang fuer alle Nicht-Analyse-Jobs — sie laufen damit einer zur
        # Zeit, wie heute ueber den Job-Lock des Dienstes (Inventur §B.1), aber
        # parallel zu den Analyse-Straengen im selben Prozess und Kontext.
        self._bg_arbeiter = threading.Thread(target=self.bg_arbeiter, name="hintergrund",
                                             daemon=False)
        self._bg_arbeiter.start()

    def beenden(self, frist_s=EOF_FRIST_S):
        """Geordnet enden: keine neuen Jobs, laufende zu Ende fuehren, dann die
        Rechenstraenge entlassen. Mit Frist — ein haengender Job darf das Ende nicht
        beliebig aufhalten, sonst bleibt nach einem verifyd-execv eine Waise."""
        ende = time.monotonic() + float(frist_s)
        while self.offen_n() and time.monotonic() < ende:
            time.sleep(0.2)
        for _ in self._arbeiter:
            self.schlange.put(None)
        if self._bg_arbeiter is not None:
            self.bg_schlange.put(None)
        for t in self._arbeiter + ([self._bg_arbeiter] if self._bg_arbeiter else []):
            t.join(timeout=max(1.0, ende - time.monotonic()))
        self.frist.__exit__()
        self.speicher.__exit__()


# ----------------------------------------------------------------- Aufruf
def argumente():
    ap = argparse.ArgumentParser(
        description="worker_dienst — Dienst-Anschluss des neuen Kerns (E2)")
    ap.add_argument("--engine", default=None,
                    choices=("ov", "cuda", "migraphx", "cpu"),
                    help="Backend-Engine. Vorgabe: aus VERIFY_BACKEND/OV_DEVICE "
                         "(face_audit.resolve_backend), wie im Dienst.")
    ap.add_argument("--threads", type=int, default=int(os.environ.get("SUSLIK_WORKER_THREADS", "1")),
                    help="Rechenstraenge in diesem Prozess (Vorgabe 1). Die ZAHL kommt "
                         "in E3 aus der Platz-Formel, nicht aus dem alten "
                         "analyse_plaetze (W2-B16: 4 Prozesse != 4 Threads).")
    ap.add_argument("--scratch", default=None,
                    help="Arbeitsordner (Kompilat-Cache, refcache). Vorgabe SCRATCH_DIR.")
    ap.add_argument("--refcache", default=None,
                    help="refcache.npz. Vorgabe <scratch>/refcache.npz wie analyze.py:264.")
    # --- .531 KARTENHAUSHALT. Der PRODUKTWEG ist das Start-Argument; verifyd
    # rechnet die Zahlen aus der Leiter und gibt sie hier herein. Die
    # Umgebungsvariable ist NUR der Vorgabewert fuer Proben und Container-Versuche
    # und wird von einem gesetzten Argument immer geschlagen.
    ap.add_argument("--vram-deckel-mb", type=int,
                    default=int(os.environ.get("SUSLIK_VRAM_DECKEL_MB", "0") or 0),
                    help="Obergrenze der GETEILTEN ORT-Arena dieses Prozesses in MB "
                         "(0 = kein Deckel, Verhalten vor .531). Kommt aus der "
                         "Leiter in core.gpubudget; gilt fuer die ganze "
                         "Prozess-Lebenszeit und ist im Lauf nicht senkbar.")
    ap.add_argument("--geometrien-max", type=int, default=0,
                    help="Wie viele Clip-Geometrien der Prozess gleichzeitig haelt "
                         "(0 = es gilt das Job-Feld 'geometrien_max').")
    ap.add_argument("--arena-strategie", default=None,
                    help="Wachstumsregel der ORT-Arena "
                         "(kSameAsRequested|kNextPowerOfTwo). Die gueltige Liste "
                         "steht in engine_cuda.ARENA_STRATEGIEN und wird DORT "
                         "geprueft — dieser Parser darf kein CUDA-Modul laden, er "
                         "laeuft auch auf Intel-Images.")
    ap.add_argument("--arena-shrink", type=int, default=0,
                    help="1 = nach jedem Erkennungslauf ORT die Arena schrumpfen "
                         "lassen (RunOptions memory.enable_memory_arena_shrinkage). "
                         "Gemessen 15.09.: Worker-Maximum 2278 -> 1820 MiB (-20 %), "
                         "Zeitkosten +9-12 %, Werte unveraendert. Vorgabe 0 — der "
                         "Betreiber entscheidet, ob ihm der Tausch wert ist.")
    ap.add_argument("--mem-pattern", type=int, default=0, choices=(0, 1),
                    help="1 = den Memory-Pattern-Planer von onnxruntime "
                         "eingeschaltet lassen. Vorgabe 0 = AUS: in der "
                         "Fassung im Image waechst die Arena sonst mit jedem "
                         "Lauf aus einem zweiten Rechenstrang weiter "
                         "(Begruendung und Messung im Kopf von engine_cuda). "
                         "Wirkt nur auf CUDA; der Intel-Zweig liest den Wert "
                         "nicht.")
    ap.add_argument("--roundtrip", action="store_true",
                    help="QS-Selbsttest: zwei analyze-Jobs (kalt+warm) ueber die "
                         "echte Job-Mechanik; Rest der Kommandozeile = die argv.")
    a, rest = ap.parse_known_args()
    a.engine_argv = rest if not a.roundtrip else []
    a.roundtrip_argv = rest if a.roundtrip else []
    if a.scratch is None:
        a.scratch = os.environ.get("SCRATCH_DIR") or os.path.join(
            tempfile.gettempdir(), "suslik-scratch")        # wie analyze.py:30
    os.makedirs(a.scratch, exist_ok=True)
    if a.refcache is None:
        a.refcache = os.path.join(a.scratch, "refcache.npz")
    if a.engine is None:
        kind, _dev = face_audit.resolve_backend()
        # E4 (17.09.2026): `cpu` hat jetzt eine eigene Engine (engine_cpu), die
        # Abbildung ist damit VOLLSTAENDIG — jedes kind der Registry hat einen
        # Rechenweg. Der Zweig darunter bleibt trotzdem: er faengt den Fall
        # „unbekanntes/neues kind" und vor allem den Fall, den das gpu-legacy-Image
        # am 17.09. gezeigt hat (Treiber bindet nicht, resolve_backend faellt
        # zurueck). Nur ist der Text jetzt ein anderer: es fehlt keine Engine mehr,
        # sondern ein GERAET.
        a.engine = {"openvino": "ov", "cuda": "cuda",
                    "migraphx": "migraphx", "cpu": "cpu"}.get(kind)
        if a.engine is None:
            # .540: DIESE ZEILE LIEST EIN NUTZER. Bis .539 stand hier ein deutscher
            # Halbsatz mit einer internen Etappen-Nummer — und zwar an der Stelle,
            # an der die Anlage aufhoert zu rechnen.
            #
            # .541 (E4) HAT IHREN ANWENDUNGSFALL VERSCHOBEN, und das ist wichtig
            # genug fuer einen eigenen Absatz: der Fall, der sie geboren hat (das
            # gpu-legacy-Image, dessen Legacy-Treiber auf einer Gen12+-iGPU nicht
            # bindet, `resolve_backend` faellt auf `cpu`), kommt hier NICHT MEHR AN —
            # `cpu` hat jetzt eine Engine und rechnet. Damit der Befund trotzdem
            # nicht still wird, meldet ihn `engine_cpu` selbst: dort weiss man, dass
            # `SUSLIK_VARIANT` eine GPU-Variante nennt, waehrend die CPU rechnet, und
            # die Warnung geht ueber `bindung` in jede Job-Antwort und nach /health.
            # Der Unterschied ist bewusst: eine Anlage, die langsam analysiert, ist
            # besser als eine, die gar nicht analysiert — aber sie muss es SAGEN.
            #
            # Was hier ankommt, ist jetzt allein ein kind der Registry OHNE Eintrag
            # in der Abbildung oben (ein neues Backend, ein Tippfehler im Config-Wert,
            # den `resolve_backend` als unbekannt zurueckgibt). Das ist ein echter
            # Abbruchgrund: wir wissen nicht, womit wir rechnen sollen.
            # Die Liste der gueltigen Werte kommt aus der EINEN Quelle (Registry),
            # nicht als Literal in einem Fehlertext — sonst nennt sie nach dem
            # naechsten Backend etwas Falsches (qs_ebenen K3).
            from core.registry import alle_wizard_werte    # noqa: PLC0415
            raise SystemExit(
                f"no analysis engine for backend {kind!r}: suslik does not know this "
                f"backend. Check the 'backend' value in your configuration — the "
                f"values this build knows are "
                f"{', '.join(alle_wizard_werte())}. "
                f"'suslik --benchmark' inside the container shows what it sees.")
    return a


def main(a):
    """Die Leitung: Jobs lesen und annehmen, bis EOF oder bis der Prozess nicht mehr
    gesund ist.

    KEINE LEERLAUF-UHR MEHR (E2d, User-Auflage 13.09.). Bis hierher ging der Prozess
    nach WORKER_IDLE_S ohne neue Zeile von selbst — eine Uhr, die die falsche Frage
    stellt. Ein Worker, der eine Stunde nichts zu tun hatte, ist nicht kaputt; er hat
    seine neun Kompilate gebaut (ohne Cache gemessen 24-36 s) und ist genau deshalb
    wertvoll. Und umgekehrt half die Uhr nicht gegen den Fall, der wirklich weh tut:
    einen Prozess, der ueber seine Speicher-Zusage waechst, WAEHREND er arbeitet.
    Der Ersatz ist deshalb ZUSTANDSBASIERT und liegt bei den Wachen:
      * Speicher ueber der Politik-Grenze -> `Dienst.ende_bitten`, vollzogen bei 0
        offenen Jobs (kein Job geht verloren), Grund im Prozess-Log;
      * Speicher katastrophal / Container fast voll -> `Dienst.abbruch_alle` (hart,
        offene Jobs als fremdverschuldet — der OOM-Killer wartet nicht);
      * haengender Job -> Frist-Waechter;
      * verifyd weg oder execv -> EOF der Job-Pipe, unveraendert.
    `WORKER_IDLE_S` wird nicht mehr gelesen; es gibt keinen Uhr-Pfad mehr im Code.

    DIE JOB-PIPE LIEGT SEIT .536 NICHT MEHR AUF fd 0 (B1b). `WORKER_JOB_FD`
    nennt den Deskriptor, den verifyd per `pass_fds` hereinreicht; fehlt die
    Variable, wird wie bis .535 `sys.stdin` gelesen (alter Aufrufer, fremder
    Starter, Selbsttest). DER GRUND ist gemessen: ein Kind des Workers erbt
    dessen fd 0, und ffmpeg pollt ihn alle 100 ms auf einen Tastendruck
    (read(0,1)). Lag dort die Job-Pipe, frass es die ersten Bytes einer gerade
    eintreffenden Job-Zeile; die Zeile kam unlesbar an (unten), verifyd bekam
    eine Antwort ohne `id`, der Job haengte bis zu seiner Frist und der
    Job-Watchdog schoss den GANZEN Prozess. Am 16.09. zweimal passiert (j26
    08:02:56, j2325 12:26:10). Auf einem eigenen Deskriptor kann kein Kind die
    Job-Pipe mehr erben; `stdin=DEVNULL` an den Kindern (B1a) ist der zweite
    Riegel derselben Kette.

    KEIN select() AUF stdin — das war der erste Fehler dieser Etappe, im Gate am
    13.09. mit dem Wachhund gefangen: worker.py durfte `select` benutzen, weil
    verifyd ihm IMMER nur einen Job schickte und auf die Antwort wartete. Im
    Mehr-Job-Betrieb schickt der Dienst N Zeilen auf einmal; die liegen nach dem
    ersten readline() im PUFFER des BufferedReader und nicht mehr in der Pipe.
    select() sah die leere Pipe, meldete „nichts zu tun" und wartete — vier von
    fuenf Jobs blieben ungelesen im Puffer liegen, obwohl sie laengst angekommen
    waren. Deshalb: ein LESE-THREAD mit blockierendem readline (der Puffer ist
    dort kein Problem, er wird ja leergelesen); der Hauptthread wartet auf EOF und
    auf das Zustands-Ende."""
    fd = int(os.environ["WORKER_ANTWORT_FD"])
    out = os.fdopen(fd, "w", buffering=1)
    # .536 B1b: die Jobs kommen vom eigenen Deskriptor, mit Rueckfall auf stdin
    # (s. Docstring). EIN Codeweg, zwei Quellen — kein zweiter Leser.
    _jfd = os.environ.get("WORKER_JOB_FD")
    try:
        jobs = os.fdopen(int(_jfd), "r") if _jfd else sys.stdin
    except (TypeError, ValueError, OSError) as e:
        prozess_log(f"WORKER_JOB_FD={_jfd!r} is not usable "
                    f"({type(e).__name__}: {e}) — reading jobs from stdin")
        jobs = sys.stdin
    prozess_log("job source: " + ("WORKER_JOB_FD" if jobs is not sys.stdin
                                  else "stdin (no WORKER_JOB_FD)"))
    d = Dienst(a, out)
    d.start(JobLog(None))                                  # Aufbau-Meldungen ins Prozess-Log
    eof = threading.Event()

    def lesen():
        try:
            for zeile in jobs:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    job = json.loads(zeile)
                except Exception as e:                     # noqa: BLE001
                    # .536 B1c1: die Zeile ging bis hierher SPURLOS verloren —
                    # verifyd sah nur eine Antwort ohne `id` und konnte nicht
                    # sagen, was ankam. Jetzt reisen die ersten 200 Zeichen mit
                    # (Antwortfeld `roh`) UND stehen im Prozess-Log; genau daran
                    # ist die Ursache am 16.09. erkennbar geworden (die Zeile
                    # begann mit id":"j1 statt {"id":"j1 — ffmpeg hatte zwei
                    # Bytes gefressen). 200 Zeichen sind der Schnitt, nicht der
                    # ganze Job: mehr braucht niemand, um den Bissrand zu sehen.
                    roh = zeile[:200]
                    prozess_log(f"job line unreadable ({type(e).__name__}) — "
                                f"first 200 chars: {roh}")
                    d.antworten({"id": None, "ok": False,
                                 "fehler": "job unlesbar", "roh": roh})
                    continue
                d.annehmen(job)
        finally:
            eof.set()                                      # verifyd weg/execv

    threading.Thread(target=lesen, name="job-leser", daemon=True).start()
    while True:
        if eof.wait(1.0):
            d.beenden()
            return
        # ZUSTANDS-ENDE. `Dienst.ende` setzt die Speicher-Wache, und sie setzt es
        # ausdruecklich erst bei 0 offenen Jobs (W2-B9: mit N Rechenstraengen kann die
        # Leitung still sein, waehrend N Jobs laufen — ein Exit naehme sie mit).
        # Hier wird deshalb nichts mehr geprueft, nur noch vollzogen.
        if d.ende.is_set():
            d.beenden(1.0)
            prozess_log("orderly shutdown: " + (d.ende_grund or "state"))
            return


def roundtrip(a):
    """QS-Selbsttest: zwei analyze-Jobs (kalt+warm) ueber die ECHTE Job-Mechanik.

    Antwortform `{"lauf1":…,"lauf2":…}` mit `wall_s` je Lauf — die liest die
    Wanduhr-ETA (W1-K6), und tools/qs.sh:304 liest daraus `ok` und `cpu_s`. Die
    Marken „N Frames" und „bestes 3s-Fenster N" stehen im Job-Log, das qs.sh
    danach greift (tools/qs.sh:311-312).

    Wie bei worker.roundtrip (worker.py:1029-1035) wird results.jsonl zwischen den
    Laeufen geloescht — sonst resumte Lauf 2 ueber done_labels und liefe LEER;
    genau diese Falle hat das Gate am 23.07. bei sich selbst gefunden. Der
    Clip-Cache bleibt bewusst stehen: Lauf 2 soll die warme ANALYSE messen."""
    log = os.path.join(a.scratch, "worker_roundtrip.log")
    open(log, "w").close()
    # Kein verifyd, keine Antwort-Pipe: die zwei Antworten gehen als JSON nach
    # stdout (unten). Die Senke braucht es nur, falls eine Wache abbricht.
    out = open(os.devnull, "w")
    d = Dienst(a, out)
    d.start(JobLog(log))
    argv = a.roundtrip_argv
    # E3.1: die Kommandozeile wird EINMAL in Job-Felder uebersetzt; der Job-Weg
    # selbst kennt keine argv mehr (s. felder_lesen/argv_zu_job).
    felder = argv_zu_job(argv)

    def einmal(nr):
        lauf = d._anmelden({"typ": "analyze", **felder, "log": log, "id": f"rt{nr}"})
        try:
            return d.job_rechnen(lauf)
        finally:
            d._abmelden(lauf)

    eins = einmal(1)
    if "--dir" in argv:
        rj = os.path.join(argv[argv.index("--dir") + 1], "results.jsonl")
        if os.path.exists(rj):
            os.unlink(rj)
    zwei = einmal(2)
    d.beenden(5.0)
    out.close()
    print(json.dumps({"lauf1": eins, "lauf2": zwei}, ensure_ascii=False))
    sys.exit(0 if (eins.get("ok") and zwei.get("ok")) else 1)


if __name__ == "__main__":
    # ZUERST, vor allem anderen: die Allokator-Politik. Sie wirkt nur auf Allokationen
    # NACH dem Aufruf, und der Speicherbefund vom 14.09. haengt genau an den grossen
    # Frame-Puffern, die gleich danach zu fliessen beginnen. Begruendung und Messung
    # stehen EINMAL in worker_kern.allokator_politik.
    prozess_log("allocator policy: " + json.dumps(wk.allokator_politik(),
                                                  ensure_ascii=False))
    _a = argumente()
    if _a.roundtrip:
        roundtrip(_a)
    else:
        main(_a)
