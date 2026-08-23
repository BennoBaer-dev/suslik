"""core/livewache — der ENGINE-KERN des Live-Waechters (Live-Phase 1, Bauplan
`live_reiter_bauplan.md`, Runde R-2026-08-12-live-phase1).

ARCHITEKTUR B (§11 Entscheid 1): EIN Prozess (`core/livewached`), EIN geteiltes
Detektor-Modell, N Kacheln (eine je Kamera). Je Kachel ein Leser-Thread (ffmpeg-
Kind + Takt/Burstwache + Filter), dazu EIN Detektor-Thread mit Einreihung
(Scheduler) und EIN Status-/Watchdog-Thread. Die Alarm-LOGIK bleibt je Kachel
autark (eigene Burstwache, eigene Karenzen, eigene Kanaele, eigener
Drossel-Zustand) — geteilt sind nur Prozess, Modell und Beobachtung.

HARTE GRENZEN (Bauplan §1, jede einzeln):
 1. KEIN URTEILER. Kachel-Frames sind auf 720p skaliert (AR-treu; scale_vaapi
    bei VAAPI, swscale bei NVDEC/SW — Wahl s. hw_wahl) und liegen
    AUSSERHALB des gepinnten Pixelpfads (decode.py:1-30). Sie werden NIE
    Urteils-Frames. Das Schnell-Urteil ("probably X (preliminary)") ist ein
    Hinweis in der Meldung und sonst nichts: nie ins Kontroll-Protokoll, nie
    ins Treffer-Buch, nie ins Anlernen, nie nach Frigate, keine Referenz,
    keine Anwesenheit, kein sub_label-Schreib.
 2. KEIN SZENARIO-BILDER. Eine Kachel kennt nur ihre eine Kamera; die
    kameraweite Zusammenfuehrung bleibt Aufgabe des Urteilspfads.
 3. KEIN REKORDER. Telegram bekommt ein kurzes Video aus den ohnehin
    gepufferten Bildern; nichts wird zusaetzlich von der Kamera geholt.
 4. KEIN FRIGATE-ERSATZ. Frigate-Kontakt nur ueber HTTP-API/go2rtc-Restream
    (Kameraliste injiziert der Startweg aus verifyd.frigate_cameras) —
    nie SSH/Dateisystem.

GEERBTER BLOCK: Die erprobte Logik stammt aus `prototyp/live_wache.py`
(Multi-Track-Stand, Runde R-2026-08-11-multitrack, Merge 4d791f5) und ist
hierher UMGEZOGEN — der Prototyp importiert sie seither von hier (eine Quelle,
Bauplan §9). Abweichungen vom woertlichen Umzug sind einzeln markiert
[ERBE-ANPASSUNG]: ENV-Defaults (LIVE_*) wurden zu expliziten Parametern bzw.
Modul-Literalen gehoben — die ENV-Welt bleibt dem Prototyp (Bauplan §3:
"Die ENV-Variablen des Prototyps bleiben dem Prototyp"). Der Verhaltens-Beweis
ist prototyp/harnisch_multitrack.py (Basis-Stand gegen Umbau-Stand, bildgenau).

ALLE FRISTEN MONOTON (§8 Uhrzeit-Sprung, Phase-1-Vorzieher): Burst-Fenster,
Karenzen, Watchdog, Reconnect-Backoff, Melde-Anker, Auftritts-Ende rechnen auf
time.monotonic(); nur ANZEIGE-Zeitstempel nehmen die Wanduhr.

INJEKTION (Muster core/melden.py): dieses Modul importiert verifyd NIE.
Config (dict), Log, Detektor, Melder, Frame-Quellen und Uhren kommen als
Parameter — genau dadurch ist der Logik-Harnisch (tools/harnisch_live1.py)
ohne Stream, ohne Modell und ohne CPU-Last moeglich.

BACKEND-/VARIANTEN-WELT (Deckungs-Vertrag tools/deckung_pruefen.py, K3-Regel —
die Mengen LEBEN in core.registry, hier vollstaendig genannt): kinds cpu,
openvino, cuda, migraphx · Image-Varianten gpu, cpu, cuda, gpu-legacy, rocm.
Welche Variante Live freischaltet, ist ein Phase-5-Entscheid ueber ein
Registry-Feld (Bauplan §8 K2); Phase 1 laeuft auf der gpu-Variante der
Autor-Maschine, der Startweg sperrt cpu-only (§11 Entscheid 3).
"""
import collections
import hashlib
import json
import os
import queue
import re
import select
import subprocess
import sys
import threading
import time

import cv2
import numpy as np

from core import registry as _reg      # MELDE_HERKUNFT-Bindung (stdlib-only, kein Zyklus)
from core import sprache as _sprache   # Sprach-Stufe 4: Waechter-Meldetexte (stdlib-only)

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- Rezept (gemessen)
# DIE gemessenen Vorgaben des Live-Rezepts — dieselben Werte wie Bauplan §3
# "defaults". Der Store-Block live.defaults darf sie ueberlagern (guards_lesen);
# hier stehen sie als EINE Code-Quelle, nie verstreut. Herkunft je Wert im
# Kommentar; ENV liest dieses Modul BEWUSST NICHT (Bauplan §3/§9).
WACH_HOEHE = 1080         # AR-treue Verkleinerung (GPU bei VAAPI, swscale sonst);
#                           Breite folgt der Quelle (wach_skala). 720 -> 1080
#                           (.194, User-Entscheid "default immer auf 1080p",
#                           messbasiert am 15:31-Gang: Name feuert bei 1080p
#                           2,4 s frueher, det-Netz bleibt gleich gross —
#                           Mehrkosten nur Decode/Scale, Last-Messung je
#                           Kachel liefert die echte Zahl).
DET_BASIS = 1280          # det-1280-Rezept (gemessen 10.08.: 320=blind, 1280=96 Funde)
MIN_SCORE = 0.60          # echte Funde 0.79-0.88, Phantome ~0.50 (det 1280)
POSE_KOPF = 0.70          # 54-Trigger-Eichung: Mensch 0.808-1.012, ohne max 0.594
PRUEF_RATE = 5            # Normaltakt: jedes 5. Bild
BURST_ANZAHL = 4          # 4 raeumlich konsistente Funde ...
BURST_FENSTER = 2.0       # ... binnen 2 s
BURST_TIMEOUT = 10.0      # INTERN (Deckel auf die Burst-Dauer je Track, ab Track-Start)
TRIGGER_KARENZ = 10.0     # INTERN (Ruhe der Burstwache je Track nach Trigger, §4)
BURST_IOU = 0.2           # Ueberlappung reicht ...
BURST_ABSTAND = 1.5       # ... oder Naehe in Boxbreiten
MAX_TRACKS = 8            # harter Track-Deckel (Multi-Track-Kontrolle 11.08.)
URTEIL_BILDER = 3         # beste N Burst-Bilder fuers Schnell-Urteil
VIDEO_SEK = 6.0           # Rueckblick fuers Telegram-Video
RECONNECT_WARTE = 5.0     # Reconnect: erster Versuch ...
RECONNECT_MAX = 60.0      # ... verdoppelnd bis Deckel
RECONNECT_STABIL = 30.0   # Backoff-Reset erst nach so lange getragener Verbindung
LOG_MAX_MB = 20.0         # Kachel-Log-Deckel, eine .1-Stufe (Prototyp-Muster)

# Die zwei User-Zeiten je Waechter (Bauplan §4) — Defaults + Plausibilitaets-Riegel.
ENDE_OHNE_GESICHT_S = 10       # (a) Inaktivitaets-Ende des Auftritts, Anker LETZTER Fund
ENDE_OHNE_GESICHT_MIN, ENDE_OHNE_GESICHT_MAX = 3, 120
WIEDER_SCHARF_S = 120          # (b) MELDE-ANKER (§11 Entscheid 6): Mindestabstand Meldungen
WIEDER_SCHARF_MIN, WIEDER_SCHARF_MAX = 0, 3600

# Betriebs-Konstanten der Engine (Phase 1; Werte begruendet, nicht gemessen —
# der Ein-Waechter-Realtest des Orchestrators liefert die Messbasis).
WATCHDOG_S = 15.0         # Liefer-Watchdog: ~3x Normaltakt-Intervall (Bauplan §8,
#                           Realbeleg 11.08. "lebt, liefert nichts")
HERZSCHLAG_S = 2.0        # Status-Schreibtakt, ALLE Kacheln in EINEM Schreiber (§7 QS-Fund)
VERBRAUCH_S = 60.0        # RSS-/Verbrauchszeile (Auflage aus dem Vorfall 10.08. 19:17)
VORSCHAU_S = 2.0          # Kachel-Vorschau-JPEG-Takt (User-Wunsch 13.08.: ~1-5 s,
#                           "sehen, was der Agent sieht" — Anzeige-Weg, nie Urteil)
HOEHEN_ERLAUBT = (360, 720, 1080, 1440, 2160)   # je-Kachel-Verarbeitungshoehe
#                           (.194, User 13.08.: 360-2160). Messbasis 15:31-
#                           Gang: 1080p = Sweet Spot (Name 2,4 s frueher als
#                           720p), 1440p flach, det-Netz bleibt ueber alle
#                           Stufen gleich gross (Basis 1280) — Mehrkosten
#                           stecken in Decode/Scale, die Last-Messung je
#                           Kachel liefert die echte Zahl. 360p =
#                           Schwach-GPU-Option.
NAME_STIMMEN = 2          # kontinuierliches Namens-Voting (User 13.08.: "PersonA,
#                           unbekannt, PersonA -> feuern"): so viele Funde ueber
#                           win_thresh fuer DIESELBE Person, dann Namens-Meldung
#                           (einmal je Auftritt+Person). Entspricht win_min der
#                           Analyse — Zeitkonsistenz statt Einzelbild-Glueck.
VORSCHAU_FRISCH_S = 60.0  # Auslieferungs-Frist des Dienst-Endpunkts /live_bild:
#                           aeltere Vorschau = Waechter aus/gestoert -> 404 statt
#                           eingefrorenes Bild als "live" servieren
# Dateiname je Kachel = Kameraname: NUR mit diesem Muster wird ueberhaupt ein
# Pfad gebaut (Frigate-Kameranamen sind Config-Schluessel, aber nie ungeprueft
# in einen Pfad interpolieren — dieselbe Vorsicht wie beim Dienst-Endpunkt).
VORSCHAU_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
# Vertrag Beweis-Medienpfad im Melde-Protokoll/-Endpunkt (.190, .195 um mp4
# erweitert fuer die Rueckblick-Videos der Auftritts-Ansicht): data_dir-
# relativ, exakt live/<kamera>/<datei>.(jpg|mp4) — Schreiber (_bild_rel,
# schreibt nur jpg) UND Dienst-Endpunkt /live_alarmbild pruefen an DIESEM
# einen Muster (kein Traversal, keine fremden Ordner). Beide Segmente
# MUESSEN alnum beginnen (.195, T23-Fund): die alte Zeichenklasse liess
# 'live/../x.jpg' durch — ein Punkt-Segment ist Traversal.
ALARMBILD_RE = re.compile(
    r"^live/[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*\.(jpg|mp4)$")
# Gleitendes Liefer-fps-Fenster (KANN-Rest M-D Gegenrichtung, Widerleger 12.08.
# gemessen: eine 3600 s verbundene Kachel mit nur 600 s Lieferung stand nach der
# ERHOLUNG noch lange bei 2,5 statt 15 fps — der Schnitt "seit dem Verbinden"
# kippte die Slot-Neubewertung zu optimistisch). Das Fenster haelt Stuetzpunkte
# (mono, bilder) aus dem Status-Takt; 5 Neubewertungs-Takte sind lang genug zum
# Glaetten und kurz genug, dass eine Erholung binnen Minuten ehrlich ankommt.
FPS_FENSTER_S = 5 * VERBRAUCH_S
STOERUNG_NACH_S = 300.0   # Stoerungs-Selbstmeldung nach so viel Dauer-Stoerung (§11
#                           Entscheid 2 laesst X offen; 300 s = deutlich ueber dem
#                           Reconnect-Deckel 60 s, damit ein einzelner Abriss nie pagt,
#                           und kurz genug, um vor dem naechsten Durchgang zu warnen)
STOERUNG_LOG_DROSSEL_S = 600.0   # Kanal-/Fehlerzeilen hoechstens 1x je 10 min je Quelle

# Last-Messung EINES Waechters (User-Auflage 12.08., praezisiert: Dauer 15 bis
# MAX 30 s; Entscheidungsgrundlage VOR dem Aktivieren — waehrenddessen stellt
# der Scheduler die anderen Kacheln still, das Modell bleibt geladen).
MESSUNG_DAUER_S = 20.0           # Default, wenn das Kommando keine Dauer nennt
MESSUNG_MIN_S, MESSUNG_MAX_S = 15.0, 30.0
# Not-Aus-Frist der Auftrags-Strecke (Engine-B1/KANN-1 Fix-Zyklus 12.08.):
# 420 s liegt BEWUSST UEBER dem Zeitbudget der bewachten Operationen, damit der
# Not-Aus ein letzter Rettungsanker ist und nie einen noch arbeitenden Auftrag
# toetet (die alte 180 riss ein normales Retry-Budget): quelle_testen im
# schlechtesten Fall ~400 s = steckbrief 2 Versuche (2x30+5 s) + masse im
# HW-Leser (4x30+35 s) + 6 s Probe + masse im SW-Rueckfall-Leser (nochmal
# 4x30+35 s) + 15 s Bildstrom-Frist. Alle Innen-Schritte sind selbst begrenzt
# (subprocess-timeouts + endliche Retries); die EINZIG unbegrenzte Stelle war
# der blockierende Frame-Read — der hat jetzt eine echte Wanduhr-Frist
# (bilder_yuv_frist, Mess-Queue) und der Not-Aus killt zusaetzlich die
# registrierte Mess-Verbindung (a["kill"]).
AUFTRAG_TIMEOUT_S = 420.0
# Nach dem Not-Aus-Kill: so lange darf der Auftrags-Thread noch brauchen, um
# WIRKLICH zu enden. Erst danach wird der Slot ZWANGS-geloest (Generation
# schuetzt den Nachfolger vor dem Zombie-finally) — vorher bleibt der Auftrag
# besetzt, damit NIE zwei Auftraege gleichzeitig laufen (Engine-B1).
AUFTRAG_ABBRUCH_GRACE_S = 30.0

# Ueberlast-Regel (Bauplan §7 QS-Auflage: Normaltakt ~442 ms/s Compute bei 5
# Waechtern, fuenf parallele Bursts sprengen die eine Engine). Schwellen sind
# DESIGN-Werte mit Begruendung, keine Messwerte — Phase 1 misst am Realtest:
#  - Budget 900 von 1000 ms/s: 10 % Reserve fuer Pose-Gate/Video/Fremdlast.
#  - hoch 0.85: darueber wird der Normaltakt gedrosselt, BEVOR die Queue kippt
#    (Rest ~150 ms/s = 2-3 Detektionen a 53 ms fuer einen anlaufenden Burst).
#  - runter 0.60: Hysterese — verglichen wird die um EINE Stufe hochgerechnete
#    Last (auslastung * 2, M-C Sched-R1): die Stufe loest, sobald der naechst-
#    niedrigere Takt truege. Zwei gemessene Vorstufen: (1) RUNTER an der
#    gedrosselten, RAUF an der rohen Last — kein Betriebspunkt im Band, 354
#    Stufenwechsel/h (5 Kacheln, fps 15, rate 5, det 53 ms: roh 0,795 > 0,765
#    hoch, gedrosselt 0,3975 < 0,54 runter). (2) VOLLE Hochrechnung
#    (auslastung * 2**stufe) — loeste erst, wenn Stufe 0 truege, parkte nach
#    einem Lastberg dauerhaft bis zu 3 Stufen zu hoch (Widerleger 12.08.:
#    det 53 ms blieb auf 1/8 statt 1/2). a * 2 ist beweisbar flatterfrei UND
#    findet die kleinste ausreichende Stufe (+1 Hysterese) wieder.
GPU_BUDGET_MS_JE_S = 900.0
DROSSEL_HOCH = 0.85
DROSSEL_RUNTER = 0.60
DROSSEL_MAX_STUFE = 3          # Normaltakt hoechstens jedes 8. Raster-Bild (Basis**3)
# EINE Stufenbasis-Quelle (K3, KANN-Rest des Fix-Zyklus 12.08.): der Takt-Faktor
# je Stufe (Basis**stufe) und die RUNTER-Hochrechnung (a * Basis) verdrahteten
# die 2 vorher als ZWEI getrennte Literale — wer eine Basis aendert, aenderte
# die andere nicht mit, und Abbau-Urteil und Takt liefen auseinander.
DROSSEL_STUFENBASIS = 2.0
DROSSEL_FENSTER_S = 10.0
# Haltezeit AN DAS FENSTER GEKOPPELT (Lens-A M4, gemessen: mit 2 s Haltezeit
# flatterte die Stufe im 5-Kachel-Betriebspunkt 440x je Stunde — das 10-s-
# Gleitfenster bildet einen Eingriff erst nach ~6 s ab, der naechste Wechsel
# darf also fruehestens kommen, wenn das Fenster die Wirkung VOLL zeigt).
DROSSEL_HALTEZEIT_S = DROSSEL_FENSTER_S
NORMAL_MAX_WARTE_S = 2.0       # Anti-Verhungern: aeltester Normal-Eintrag geht vor
#                                Burst, wenn er laenger als das wartet (Fairness-Ventil)

# Selbstvermessung/Slots (stand.md-Auflage 11.08.: Deckel dynamisch aus RAM- und
# GPU-Budget, hart max 4-5 — hier 5 als harte Wand, die Budgets kappen darunter).
HART_MAX_SLOTS = 5
# Anteil des GPU-Budgets, den der NORMALTAKT aller Slots belegen darf. Der Rest
# (40 %) ist Burst-/Pose-Reserve: eine volle Burst-Reserve in der Slot-Rechnung
# (fps x det_ms, mit den Seeds 15 x 53 = 795 ms/s) wuerde das Budget allein
# auffressen und liesse rechnerisch nur 1-2 Slots zu, obwohl real 5 Waechter
# liefen (442 ms/s Normaltakt gesamt, fdinfo 7,3-h-Lauf, Bauplan §7). Die
# Ueberlast deckt die Drossel zur LAUFZEIT (DROSSEL_*): sie nimmt dem
# Normaltakt Last weg, BEVOR die eine Compute-Engine kippt. Eine Slot-
# VORHERSAGE aus diesen Werten gibt es seit .196 nicht mehr (Kommentar am
# Vereinfachungs-Schnitt oben).
DET_MS_SEED = 53.0        # SEED, GEMESSEN auf der Autor-Maschine (stand.md: det-1280
#                           ~53 ms/Bild iGPU); wird im Betrieb durch die eigene
#                           EMA-Messung ersetzt und ist im Status als Seed markiert
# --- Vereinfachungs-Schnitt .196 (User 13.08.: "Entweder ist sie konsequent
# an oder aus" / "zu komplex, ueberfrachtet"): Messwerte INFORMIEREN, sie
# ENTSCHEIDEN nicht mehr, ob ein Waechter laufen darf. Das GPU-Budget-Urteil
# der Slot-Vergabe (Vorhersage aus geschaetzten fps + det-Seed) ist raus —
# es faellte je nach Zufalls-Zustand (Seed nach Neustart, Test-Durchsatz
# 79,6 bei real 15,5 fps, Vergabe-Reihenfolge) verschiedene Urteile ueber
# dieselbe Config. Ueberlast regelt die Drossel zur LAUFZEIT an der ECHTEN
# Last. Als Notbremsen bleiben nur der harte Deckel (HART_MAX_SLOTS) und
# der RAM-Boden (cgroup-Messwert, Thrashing-Vorfall 10.08.).
LIEFER_BURST_S = 1.0      # RTSP liefert den gepufferten GOP als Anfangs-Burst —
#                           Bilder dieses Fensters zaehlen NICHT zur Lieferrate
#                           (gemessen 13.08.: Durchsatz 79,6 bei realen 15,5 fps)
LIEFER_MESS_S = 5.0       # Mindest-Messfenster des Quelltests (wall-clock);
#                           erst damit ist bilder_s eine LIEFERRATE
RAM_REST_MIN_MB = 2048    # Restgrenze der RAM-Bilanz (Bauplan §2.3 Warnstufe):
#                           der Analyse-Worker allein laeuft warm ~1,9 GB
#                           (verifyd worker_rss_max_mb-Kommentar) — unter 2 GiB frei
#                           wird kein weiterer Slot vergeben

# Meldungs-Literale (EIN Literal je Zweck, Bauplan §6 — UI-Sprache englisch).
# Sprach-Stufe 4: WATCHER_TITEL bleibt ENGLISCH und literal — er ist die
# KENNUNG des Waechters im Meldungstitel (Invariante §6, core/registry.py:378:
# "Live watcher <kamera>: ..."), nicht Prosa. Uebersetzt wird der Rest des
# Titels: die meldung.wache.*-Schluessel tragen ihn als Platzhalter {wache}
# (Muster §8.13/§8.16 — Kennung intern, Anzeige als Schluessel).
WATCHER_TITEL = "Live watcher"
HERKUNFT = "live_wache"
# Bindung an die EINE Quelle (Lens-B M1, per Mutation bewiesen: ein verstelltes
# Literal fiele in melden.mqtt_herkunft STILL auf "live" zurueck — exakt das
# K3-Loch, das der Registry-Eintrag schliessen soll). Import-Wache statt
# Kommentar: eine Engine mit ungebundenem Absender darf gar nicht erst laden.
if HERKUNFT not in _reg.MELDE_HERKUNFT:
    raise ImportError(f"core/livewache: HERKUNFT {HERKUNFT!r} fehlt in "
                      f"core.registry.MELDE_HERKUNFT — Registry zuerst ergaenzen")

# Engine-LAUFZEIT-Zustaende je Kachel (EINE Quelle fuer Status/Log/Harnisch).
# BEWUSST getrennt von der UI-Kachel-Enum aus Bauplan §2.3 (LIVE_ZUSTAENDE,
# unconfigured/untested/...): die kommt mit der UI-Phase 2 in die Registry und
# LEITET den UI-Zustand aus Config + DIESEM Herzschlag ab.
KACHEL_ZUSTAENDE = ("startet", "aktiv", "gestoert", "verweigert", "gestoppt")

RENDER_NODE = os.environ.get("SUSLIK_HWDEC_DEVICE", "/dev/dri/renderD128")


def hw_wahl():
    """Die EINE HW-Decode-Wahl des Live-Lesers (Runde R-2026-08-13-cuda-nvdec):
    nach VERFUEGBARKEIT der Hardware statt fest VAAPI. Die Kriterien kommen aus
    decode.py (eine Quelle, kein zweites Rezept): Intel zuerst (decode.va_da —
    Render-Node + VALIDIERTER VA-Treiber iHD/i965; blosse /dev/dri-Existenz
    genuegt nicht, decode-Panel-Fund: cpu/cuda-Images tragen keinen Treiber),
    sonst NVIDIA/NVDEC (decode.nv_da — /dev/nvidiactl), sonst Software.
    Reihenfolge wie decode._hwdec im auto-Modus. Alle Leser-Wege (Kachel-
    Betrieb, Quelltest, Last-Messung) laufen ueber leser_mit_rueckfall und
    damit ueber DIESE Wahl. -> 'vaapi' | 'nvdec' | None (= SW-Decode)."""
    import decode
    if decode.va_da():
        return "vaapi"
    if decode.nv_da():
        return "nvdec"
    return None


# ======================================================================
# GEERBTER BLOCK — aus prototyp/live_wache.py umgezogen (Multi-Track-Stand).
# Woertlich bis auf die markierten [ERBE-ANPASSUNG]-Stellen (ENV -> Parameter).
# ======================================================================

def quelle_maskiert(url):
    """Zugangsdaten aus einer Stream-URL entfernen (fuer Log/Anzeige).
    [ERBE-ANPASSUNG] Muster [^/]* statt [^@/]* (Lens-B K4): ein Passwort MIT
    eigenem '@' (rtsp://u:p@ss@host) blieb sonst teilweise stehen — greedy bis
    zum LETZTEN '@' vor dem Pfad maskiert beides; URLs ohne Zugangsdaten
    bleiben unveraendert (kein '@' in der Authority -> kein Treffer)."""
    import re as _re
    return _re.sub(r"//[^/]*@", "//***@", url)


def masse(url, versuche=4):
    """Stream-Masse per ffprobe — MIT Wiederholung (11.08.): beim Start mehrerer
    Waechter gleichzeitig lieferte go2rtc transient leere Antworten, und die Wache
    starb VOR dem ersten Bild (der Abriss-Fix vom 10.08. schuetzt nur den Betrieb).
    Laut + verdoppelnd wie der Reconnect; nach dem letzten Versuch ein klarer Fehler
    statt des nackten ValueError."""
    for i in range(versuche):
        p = subprocess.run(["ffprobe", "-v", "error", "-rtsp_transport", "tcp",
                            "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", url],
                           capture_output=True, text=True, timeout=30)
        teile = p.stdout.strip().split(",")
        if len(teile) >= 2 and teile[0].strip().isdigit() and teile[1].strip().isdigit():
            return int(teile[0]), int(teile[1])
        if i + 1 < versuche:
            warte = 5 * (2 ** i)
            print(f"masse: ffprobe ohne Masse fuer {quelle_maskiert(url)} "
                  f"(Versuch {i + 1}/{versuche}) — neuer Versuch in {warte} s", flush=True)
            time.sleep(warte)
    raise RuntimeError(f"masse: ffprobe liefert nach {versuche} Versuchen keine "
                       f"Masse fuer {quelle_maskiert(url)}")


def wach_skala(breite, hoehe, ziel_hoehe=None):
    """Zielmasse der Verkleinerung (GPU- oder SW-Scale je nach Decode-Wahl):
    feste Hoehe, Breite SEITENVERHAELTNIS-TREU.

    Bis 10.08. stand ueberall fest (1280, 720). Bei 16:9-Quellen ist das genau
    richtig, bei 4:3-Quellen (z. B. 2560x1920) quetscht es das Bild auf 3:2 zusammen:
    Gesichter werden schmaler als sie sind, und der Detektor bekommt eine
    Geometrie zu sehen, die es in der Wirklichkeit nicht gibt — SCRFD ist auf
    unverzerrte Koepfe trainiert. Neu bleibt die Hoehe der Kostenanker und die
    Breite folgt der Quelle: 16:9 ergibt weiterhin exakt (1280, 720), 4:3 gibt
    (960, 720), 1080p gibt (1280, 720).

    Gerade Kantenlaenge, weil yuv420p die Chroma-Ebenen halbiert — eine ungerade
    Breite lehnt ffmpeg ab. Unbekannte Quellmasse -> der Bestandswert 1280
    (nie raten), Verhalten wie vor dem Umbau.
    [ERBE-ANPASSUNG] Default der Zielhoehe ist das Modul-Literal WACH_HOEHE
    statt der Prototyp-ENV LIVE_HOEHE (der Prototyp reicht seine ENV durch)."""
    zh = int(ziel_hoehe or WACH_HOEHE)
    if not breite or not hoehe:
        return (1280, zh)
    zb = int(round(zh * breite / float(hoehe)))
    return (max(2, zb - (zb % 2)), zh)


def leser(url, rate=1, skala=None, hw=True):
    """ffmpeg-Kommando nach dem Muster von decode.py._kommando. hw waehlt die
    Decode-Quelle: True = Wahl nach Verfuegbarkeit (hw_wahl) · 'vaapi'/'nvdec'
    = erzwungen · False/None = Software. VAAPI verkleinert auf der GPU
    (scale_vaapi VOR hwdownload); fuer NVDEC kennt das decode-Rezept KEIN
    GPU-Scale — dort skaliert swscale NACH dem Download (Anzeige-/Trigger-
    Frames, kein Urteils-Pfad; kein eigenes neues Rezept). Liefert
    (Popen, breite, hoehe).
    [ERBE-ANPASSUNG] R-2026-08-13-cuda-nvdec: hw war ein Bool und hiess fest
    VAAPI — die Wahl trifft jetzt hw_wahl() nach der Hardware."""
    b, h = masse(url)
    if hw is True:
        hw = hw_wahl()
    elif not hw:
        hw = None
    cmd = ["ffmpeg", "-v", "error"]
    if url.startswith("rtsp://"):
        # Nur fuer RTSP (Muster steckbrief_ermitteln): ffmpeg lehnt das
        # private Demuxer-Flag an file/http-Quellen HART ab ("Option not
        # found") — jede Nicht-RTSP-URL der url-Quelle starb damit sofort,
        # inklusive SW-Rueckfall (Realfall CUDA-NB 13.08., Fixpunkt-Clip).
        cmd += ["-rtsp_transport", "tcp"]
    if hw == "vaapi":
        cmd += ["-hwaccel", "vaapi", "-hwaccel_device", RENDER_NODE,
                "-hwaccel_output_format", "vaapi"]
    elif hw == "nvdec":
        cmd += ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
    cmd += ["-i", url, "-map", "0:v:0"]
    kette = [f"select='not(mod(n\\,{rate}))'"] if rate > 1 else []
    if skala and hw == "vaapi":
        kette.append(f"scale_vaapi=w={skala[0]}:h={skala[1]}")
        b, h = skala
    elif skala and not hw:
        kette.append(f"scale={skala[0]}:{skala[1]}")
        b, h = skala
    kette.append("hwdownload,format=nv12,format=yuv420p" if hw else "format=yuv420p")
    if skala and hw == "nvdec":
        # sw-scale nach dem Download; format-Pin dahinter, damit fsz (yuv420p)
        # nicht vom scale-Ausgabeformat abhaengt (Lens B2)
        kette.append(f"scale={skala[0]}:{skala[1]}")
        kette.append("format=yuv420p")
        b, h = skala
    cmd += ["-vf", ",".join(kette), "-fps_mode", "passthrough", "-f", "rawvideo", "-"]
    fsz = b * h * 3 // 2
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         bufsize=fsz * 2)
    return p, b, h


def bilder_yuv(p, b, h, sekunden):
    """Rohe YUV420-Puffer. Wichtig fuer das Bewegungs-Gate: die Y-Ebene (Helligkeit)
    sind die ersten h Zeilen, sie liegt also GRATIS vor. Erst wer sie braucht,
    zahlt die Farbumrechnung — bei Ruhe faellt die ganz weg."""
    fsz = b * h * 3 // 2
    t0 = time.time()
    while sekunden <= 0 or time.time() - t0 < sekunden:
        roh = p.stdout.read(fsz)
        if not roh or len(roh) < fsz:
            return
        yield np.frombuffer(roh, np.uint8).reshape(h * 3 // 2, b)


def bilder(p, b, h, sekunden):
    """sekunden <= 0 bedeutet: laufen, bis der Prozess beendet wird."""
    for yuv in bilder_yuv(p, b, h, sekunden):
        yield cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)


def bilder_yuv_frist(p, b, h, frist_s, jetzt=time.monotonic):
    """Wie bilder_yuv, aber mit ECHTER Wanduhr-Frist (Engine-B1, Widerleger
    12.08. gemessen): bilder_yuv prueft seine Frist nur JE GELIEFERTEM Bild —
    der blockierende p.stdout.read() haelt eine lebende, stumme Quelle
    ('lebt, liefert nichts'-Klasse, Realbeleg 11.08.) fuer immer fest, und der
    Fehlertext 'no frames within Ns' versprach eine Frist, die es nicht gab.
    Hier: select + os.read am rohen fd — die Frist greift auch dann, wenn NIE
    ein Byte kommt. Rueckkehr ohne StopIteration-Grund = Frist um oder EOF."""
    fsz = b * h * 3 // 2
    fd = p.stdout.fileno()
    ende = jetzt() + float(frist_s)
    puffer = bytearray()
    while True:
        rest = ende - jetzt()
        if rest <= 0:
            return
        r, _, _ = select.select([fd], [], [], min(rest, 0.5))
        if not r:
            continue
        stueck = os.read(fd, fsz - len(puffer))
        if not stueck:
            return                              # EOF — ffmpeg-Ende/gekillt
        puffer += stueck
        if len(puffer) >= fsz:
            yield np.frombuffer(bytes(puffer[:fsz]), np.uint8).reshape(h * 3 // 2, b)
            del puffer[:fsz]


def bild_mit_box(frame, box, farbe=(0, 200, 255), dicke=2):
    """Beweisbild mit markierter Fundstelle (.313): Rechteck um `box`
    (x1, y1, x2, y2) auf einer KOPIE des Frames — das Original bleibt fuer
    Rueckblick/Video unberuehrt. Ohne Box: das Bild unveraendert."""
    if box is None or frame is None:
        return frame
    try:
        x1, y1, x2, y2 = [int(round(float(v))) for v in box[:4]]
    except (TypeError, ValueError):
        return frame
    h, w = frame.shape[:2]
    x1, x2 = max(0, min(w - 1, x1)), max(0, min(w - 1, x2))
    y1, y2 = max(0, min(h - 1, y1)), max(0, min(h - 1, y2))
    if x2 <= x1 or y2 <= y1:
        return frame
    aus = frame.copy()
    # Rand mitnehmen, damit ein 20-px-Gesicht nicht unter dem Strich verschwindet
    r = max(4, int(0.35 * max(x2 - x1, y2 - y1)))
    cv2.rectangle(aus, (max(0, x1 - r), max(0, y1 - r)),
                  (min(w - 1, x2 + r), min(h - 1, y2 + r)), farbe, dicke)
    return aus


def echtes_gesicht(f, frame, min_score=None):
    """Fehldetektions-Signatur (#42) + Geometrie-Plausibilitaet + Mindest-Score.

    #42: stehende Objekte (Hecke, Radkasten) liefern 'perfekt frontal' bei
    hoher Schaerfe und maessigem Score.

    MINDEST-SCORE (10.08., neue Fehlklasse): Mit dem 1280er-Netz loeste EINE Kamera
    fuenfmal ohne Person im Bild aus — Boxen um 30 px, det_score um 0,50, das
    Schnell-Urteil kam auf Kosinus 0,14-0,21 (also nichts Menschenaehnliches).
    Die #42-Signatur greift dort nicht: das UND aus frontal + scharf + maessig
    trifft nur stehende, kantenreiche Objekte, und ein flaches Phantom auf
    Karosserie/Rasen erfuellt die Schaerfe-Bedingung nicht. Der Score trennt die
    Klasse dagegen sauber: echte Funde derselben Kette liegen bei det 1280
    durchweg bei 0,79-0,88, die Phantome bei ~0,50. Deshalb 0,60 als Vorgabe.
    Wer die det-Basis aendert, muss die Schwelle mitaendern (bei det 320 lagen
    echte Funde bei 0,50-0,74).

    GEOMETRIE (Fehlalarm 09.08. 21:55, User-Fund): ein Lichtfleck auf dem Weg
    loeste mit Score 0,513 aus — die gemeldete Box war 696x995 px in einem
    720p-Bild und ragte 384 px UNTER den Bildrand. Deshalb zwei harte
    Geometrie-Regeln VOR der Signatur (kosten keine echten Treffer, saemtliche
    echten Funde des Tages lagen bei 36-55 px Hoehe, voll im Bild).

    [ERBE-ANPASSUNG] min_score ist Parameter (None -> Modul-Literal MIN_SCORE);
    der Prototyp reicht seine ENV-Schwelle durch, die Engine ihren Config-Wert."""
    from face_audit import ist_fehldetektion
    schwelle = MIN_SCORE if min_score is None else float(min_score)
    try:
        if float(f.det_score) < schwelle:
            return False                      # Phantom-Klasse, s. Kopf
        H = int(frame.shape[0])
        x1, y1, x2, y2 = [int(v) for v in f.bbox]
        bh = max(1, y2 - y1)
        sichtbar = min(y2, H) - max(y1, 0)
        if sichtbar / bh < 0.70:
            return False                      # ragt weit aus dem Bild
        if bh > 0.5 * H:
            return False                      # absurd gross fuers Szenenbild
        pose = getattr(f, "pose", None)
        winkel = (float(pose[0]) ** 2 + float(pose[1]) ** 2) ** 0.5 if pose is not None else 90.0
        front = float(np.exp(-winkel / 40.0))
        aus = frame[max(0, y1):max(1, y2), max(0, x1):max(1, x2)]
        sch = float(cv2.Laplacian(cv2.cvtColor(aus, cv2.COLOR_BGR2GRAY),
                                  cv2.CV_64F).var()) if aus.size else 0.0
        return not ist_fehldetektion(front, sch, float(f.det_score))
    except Exception:
        return True


def raeumlich_konsistent(a, b, iou_min=None, abstand_faktor=None):
    """Gehoeren zwei Funde zum SELBEN wandernden Objekt? (x1,y1,x2,y2 je Box)

    Zwei Wege reichen, ODER-verknuepft:
      1. Ueberlappung (IoU > iou_min) — der Normalfall bei 15 Bildern/s, ein
         Kopf bewegt sich zwischen zwei Bildern kaum.
      2. Naehe: Zentrumsabstand < abstand_faktor * mittlere Boxbreite. Faengt
         den Fall, dass der Detektor die Box zwischendurch anders zieht
         (halbes Profil, andere Groesse) und die Ueberlappung einbricht.
    BEWUSST KEINE Identitaet: hier wird kein Embedding gerechnet und kein Name
    geprueft — nur Geometrie. Rueckgabe (ja, iou, abstand_in_boxbreiten) fuers
    Log, damit man im Nachhinein sieht, WORAN eine Kette gerissen ist.
    [ERBE-ANPASSUNG] Defaults sind Modul-Literale statt Prototyp-ENV."""
    iou_min = BURST_IOU if iou_min is None else iou_min
    abstand_faktor = BURST_ABSTAND if abstand_faktor is None else abstand_faktor
    ax1, ay1, ax2, ay2 = [float(v) for v in a]
    bx1, by1, bx2, by2 = [float(v) for v in b]
    ib = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0.0, min(ay2, by2) - max(ay1, by1))
    schnitt = ib * ih
    fa = max(1.0, ax2 - ax1) * max(1.0, ay2 - ay1)
    fb = max(1.0, bx2 - bx1) * max(1.0, by2 - by1)
    iou = schnitt / max(fa + fb - schnitt, 1.0)
    breite = 0.5 * (max(1.0, ax2 - ax1) + max(1.0, bx2 - bx1))
    d = (((ax1 + ax2) - (bx1 + bx2)) ** 2 + ((ay1 + ay2) - (by1 + by2)) ** 2) ** 0.5 / 2.0
    rel = d / breite
    return (iou > iou_min or rel < abstand_faktor), iou, rel


class Burstwache:
    """Adaptive Pruefrate + raeumliche Ketten — die scharfe Trigger-Regel,
    seit dem Multi-Track-Umbau mit MEHREREN Ketten (Tracks) gleichzeitig.

    Zustand: RUHE (jedes rate-te Bild wird geprueft) oder BURST (jedes Bild).
    Der erste echte Fund schaltet auf BURST und eroeffnet einen TRACK; jeder
    weitere Fund wird per Geometrie (raeumlich_konsistent) dem am besten
    passenden Track zugeordnet — passt er zu keinem, eroeffnet er einen
    EIGENEN Track. So koennen zwei Personen im selben Bild getrennt gezaehlt
    werden und jede loest ihren eigenen Trigger aus. Ist die Kette eines
    Tracks 'anzahl' lang und passt sie in 'fenster' Sekunden, feuert dessen
    Trigger.

    EIN TRACK STIRBT (Kontroll-Runde 11.08., Widerleger-Befunde), wenn er
      a) laenger als 'fenster' keinen Fund bekam (grund 'verwaist'), oder
      b) 'timeout' Sekunden nach seinem Start nicht getriggert hat.
    RUHE beginnt, wenn kein Track mehr lebt. Gegen Streu-Anhaeufung steht
    zusaetzlich der harte Deckel max_tracks mit Verdraengung (gereifte
    unbestaetigte Tracks zuerst; frisch bediente sind geschuetzt).

    DOPPEL-DETEKTIONS-SIEB, KARENZ JE TRACK (1:1-Matching nach bester Passung)
    und ZAEHLER-EHRLICHKEIT wie im Prototyp dokumentiert — die vollstaendige
    Begruendungs-Historie steht am Multi-Track-Stand des Prototyps und in der
    Runden-Bilanz R-2026-08-11-multitrack.

    Bewusst OHNE Bildmaterial im Zustand: der Aufrufer haengt an jeden Fund
    seine Nutzlast (Frame, Gesicht) und entscheidet selbst, wie viel davon er
    im Speicher haelt. Dieselbe Klasse bedient Engine, Prototyp und Probe.
    [ERBE-ANPASSUNG] Defaults sind Modul-Literale statt Prototyp-ENV; neu sind
    die Felder iou_min/abstand_faktor (vorher Modul-ENV BURST_IOU/_ABSTAND),
    damit Prototyp-ENV und Engine-Config dieselbe Klasse speisen koennen."""

    def __init__(self, rate=None, anzahl=None, fenster=None, timeout=None, karenz=None,
                 deckel=None, max_tracks=None, iou_min=None, abstand_faktor=None):
        self.rate = int(rate or PRUEF_RATE)
        self.anzahl = int(anzahl or BURST_ANZAHL)
        # Nur die juengsten 'deckel' Kettenglieder JE TRACK behalten ihre Nutzlast.
        # Ohne das haelte ein 2-s-Fenster bei 15 Bildern/s bis zu 30 volle
        # 720p-Bilder im Speicher (rund 80 MB je Kamera) — gebraucht werden die
        # letzten 'anzahl'. Untergrenze anzahl: ein kleinerer Deckel wuerde
        # Nutzlasten der spaeteren Trigger-Kette nullen (TypeError im Aufrufer).
        self.deckel = max(int(deckel or self.anzahl), self.anzahl)
        self.fenster = float(fenster if fenster is not None else BURST_FENSTER)
        self.timeout = float(timeout if timeout is not None else BURST_TIMEOUT)
        self.karenz = float(karenz if karenz is not None else TRIGGER_KARENZ)
        self.max_tracks = int(max_tracks or MAX_TRACKS)
        self.iou_min = BURST_IOU if iou_min is None else float(iou_min)
        self.abstand_faktor = BURST_ABSTAND if abstand_faktor is None else float(abstand_faktor)
        self.tracks = []             # [{nr, start, kette, max_kette, geprueft}]
        self.karenzen = []           # [{nr, ruhe_bis, box}] — Merk-Box folgt der Person
        self.naechste_nr = 1         # Track-Nummern fortlaufend, fuer Logs eindeutig
        self.geprueft_im_burst = 0   # Bilder im Burst-Modus, global (nullt bei RUHE)
        self.bursts = 0
        self.treffer = 0
        self.risse = 0               # Track-Starts neben laufenden Tracks (s. Docstring)
        self.doppel_verworfen = 0    # Rest-Funde am Doppel-Detektions-Sieb
        self.deckel_verworfen = 0    # Rest-Funde am max_tracks-Deckel (kein Opfer frei)
        self.verdraengt = 0          # unbestaetigte Tracks, vom Deckel geraeumt

    @property
    def aktiv(self):
        return bool(self.tracks)

    def _passt(self, a, b):
        return raeumlich_konsistent(a, b, self.iou_min, self.abstand_faktor)

    def karenz_aufheben(self, track=None):
        """Ein Trigger wurde NACHTRAEGLICH verworfen (Pose-Gate) — die Ruhezeit
        gilt nicht. Ohne das waere die Wache nach jedem Katzen-/Phantom-Trigger
        karenz Sekunden lang blind fuer den naechsten echten Menschen, und genau
        die Fehlklassen loesen ja am haeufigsten aus. Der Trigger-Zaehler bleibt
        stehen: die Bilder liegen unter dieser Nummer auf der Platte.

        Mit 'track' (die nr aus der Trigger-info) faellt nur DESSEN Karenz —
        eine parallel laufende echte Person behaelt ihre. Ohne Argument fallen
        alle (das alte Verhalten, und der sichere Weg bei Unkenntnis)."""
        if track is None:
            self.karenzen = []
        else:
            self.karenzen = [k for k in self.karenzen if k["nr"] != track]

    def abriss_enden(self, zeit):
        """Stream-Abriss: alle offenen Tracks SOFORT beenden und ihre Infos
        zurueckgeben (der Aufrufer schreibt die Protokollzeilen zur Abriss-
        Zeit, nicht Stunden spaeter mit absurder Dauer). Ohne das hielte
        jeder offene Track seine Nutzlast-Frames ueber die gesamte
        Ausfallzeit (Realfall 10.08.: 3 h) und die ENDE-Zeilen truegen die
        Ausfalldauer als Track-Dauer. Karenzen bleiben: sie kosten nichts
        und laufen von selbst ab."""
        enden = [{"dauer": zeit - t["start"], "geprueft": t["geprueft"],
                  "max_kette": t["max_kette"], "track": t["nr"], "grund": "abriss"}
                 for t in self.tracks]
        self.tracks = []
        self.geprueft_im_burst = 0
        return enden

    def takt(self, n, zeit):
        """Soll Bild n (Zeit 'zeit') durch den Detektor? -> (pruefen, enden).

        enden ist None oder eine LISTE von Infos — je eine fuer jeden Track,
        der genau jetzt ohne Trigger endet (grund 'verwaist' = fenster ohne
        Fund-Nachschub, 'timeout' = Obergrenze ab Track-Start). Mehrere
        koennen im selben Bild enden; der Aufrufer schreibt die Zeilen."""
        enden = []
        for t in self.tracks:
            grund = None
            if zeit - t["start"] > self.timeout:
                grund = "timeout"
            elif zeit - t["kette"][-1][0] > self.fenster:
                grund = "verwaist"
            if grund:
                enden.append({"dauer": zeit - t["start"], "geprueft": t["geprueft"],
                              "max_kette": t["max_kette"], "track": t["nr"],
                              "grund": grund})
        if enden:
            tot = {e["track"] for e in enden}
            self.tracks = [t for t in self.tracks if t["nr"] not in tot]
        if self.tracks:
            self.geprueft_im_burst += 1
            for t in self.tracks:
                t["geprueft"] += 1
            return True, (enden or None)
        self.geprueft_im_burst = 0
        return (n % self.rate) == 0, (enden or None)

    def fund(self, zeit, box, nutzlast=None):
        """Ein einzelner ECHTER Fund — Kompatibilitaets-Huelle um fund_alle().

        -> (ereignis, info) mit ereignis in {None, 'start', 'trigger'}.
        Verdraengungs-Enden bleiben API-treu draussen (die alte Signatur
        kannte sie nicht); wer sie braucht, ruft fund_alle()."""
        for ereignis, info in self.fund_alle(zeit, [(box, nutzlast)]):
            if ereignis != "ende":
                return ereignis, info
        return None, None

    def fund_alle(self, zeit, funde):
        """ALLE echten Funde EINES Bilds (echtes_gesicht() hat sie durchgelassen),
        als Liste [(box, nutzlast)], nach det_score absteigend sortiert —
        VORBEDINGUNG des Aufrufers: bei Gleichstand der Geometrie-Guete
        entscheidet die Listenreihenfolge, und die soll den plausibelsten
        Fund vorn haben.

        -> Liste [(ereignis, info)], ereignis in {'start', 'trigger', 'ende'}
        ('ende' nur mit grund='verdraengt' — Timeout/Verwaist-Enden liefert
        takt()). Funde ohne Ereignis (Kette waechst, Karenz/Sieb/Deckel
        schluckt) tauchen nicht auf. Jede info traegt 'track'."""
        ereignisse = []
        self.karenzen = [k for k in self.karenzen if zeit < k["ruhe_bis"]]
        offen = list(funde)

        # 1) Karenz-Zuordnung als ECHTES 1:1-Matching (Widerleger-Zyklus 2):
        #    jede Karenz bekommt hoechstens EINEN Fund je Bild und jeder Fund
        #    hoechstens EINE Karenz — greedy ueber die beste Passung BEIDER
        #    Seiten. Erst nach dem Matching schlucken vergebene Karenzen
        #    uebrige passende Funde OHNE Box-Update (Doppel-Boxen derselben
        #    karenzierten Person duerfen keinen Track eroeffnen).
        kpaare = []
        for i, (box, _n) in enumerate(offen):
            for k in self.karenzen:
                ja, iou, rel = self._passt(k["box"], box)
                if ja:
                    kpaare.append((-iou, rel, i, id(k), k))
        # key= ist zwingend: die Tupel enthalten dicts, ein nackter
        # Tupel-Vergleich wuerde beim Gleichstand am dict scheitern.
        kpaare.sort(key=lambda p: (p[0], p[1]))
        geschluckt, karenz_bedient = set(), set()
        for _niou, _rel, i, kid, k in kpaare:
            if i in geschluckt or kid in karenz_bedient:
                continue
            geschluckt.add(i)
            karenz_bedient.add(kid)
            k["box"] = offen[i][0]
        for _niou, _rel, i, kid, k in kpaare:
            if i not in geschluckt:
                geschluckt.add(i)            # schlucken ohne Update
        offen = [f for i, f in enumerate(offen) if i not in geschluckt]

        # 2) Zuordnung zu laufenden Tracks: greedy nach bester Passung — je
        #    Track hoechstens EIN Fund je Bild, je Fund hoechstens EIN Track.
        paare = []
        for i, (box, _n) in enumerate(offen):
            for t in self.tracks:
                ja, iou, rel = self._passt(t["kette"][-1][1], box)
                if ja:
                    paare.append((-iou, rel, i, t))
        paare.sort(key=lambda p: (p[0], p[1]))   # key= zwingend, s. oben
        fund_vergeben, track_vergeben = set(), set()
        bedient = []                 # Tracks, die in DIESEM Bild einen Fund bekamen
        for _niou, _rel, i, t in paare:
            if i in fund_vergeben or t["nr"] in track_vergeben:
                continue
            fund_vergeben.add(i)
            track_vergeben.add(t["nr"])
            bedient.append(t)
            box, nutzlast = offen[i]
            ev = self._anhaengen(t, zeit, box, nutzlast)
            if ev is not None:
                ereignisse.append(ev)

        # 3) Rest-Funde: erst das Doppel-Detektions-Sieb (passt der Fund zu
        #    einem Track, der dieses Bild schon bedient wurde oder gerade
        #    eroeffnet ist, dann ist er die zweite Box desselben Kopfes),
        #    dann der harte Deckel, erst dann ein eigener Track.
        for i, (box, nutzlast) in enumerate(offen):
            if i in fund_vergeben:
                continue
            doppel = False
            for t in bedient:
                if t["kette"] and self._passt(t["kette"][-1][1], box)[0]:
                    doppel = True
                    break
            if doppel:
                self.doppel_verworfen += 1
                continue
            if len(self.tracks) >= self.max_tracks:
                # Deckel voll: NICHT den neuen Fund still fallen lassen (so
                # sperrten acht lebendige Flacker-Phantome eine echte Person
                # minutenlang aus, Widerleger-Zyklus 2), sondern den
                # schwaechsten Bestand raeumen. Schutzkriterium ist "in
                # DIESEM Bild bedient" — eine echte laufende Person ist immer
                # frisch, Flacker-Tracks haben alte letzte Funde. Opfer-Wahl:
                # unbestaetigte (Kette 1) vor bestaetigten, darin der aelteste
                # letzte Fund. Sind ALLE Tracks frisch bedient (echtes
                # 8-Objekte-Bild), faellt der Neue — gezaehlt, nie still.
                # Nur GEREIFTE Opfer (aelter als fenster/2): sonst raeumt
                # dichter Streu-Regen sich selbst staendig Platz frei und der
                # Deckel verliert seine Siebwirkung.
                opfer = [x for x in self.tracks if x not in bedient
                         and zeit - x["start"] > self.fenster / 2]
                if opfer:
                    opfer.sort(key=lambda x: (len(x["kette"]) > 1, x["kette"][-1][0]))
                    o = opfer[0]
                    self.tracks.remove(o)
                    self.verdraengt += 1
                    # Verdraengung hinterlaesst eine SPUR (alle drei Lenses:
                    # Track mit Start- aber ohne Ende-Zeile = stiller Verlust).
                    ereignisse.append(("ende", {"dauer": zeit - o["start"],
                                                "geprueft": o["geprueft"],
                                                "max_kette": o["max_kette"],
                                                "track": o["nr"],
                                                "grund": "verdraengt"}))
                else:
                    self.deckel_verworfen += 1
                    continue
            neben = len(self.tracks)
            if neben:
                self.risse += 1
            else:
                self.bursts += 1
            t = {"nr": self.naechste_nr, "start": zeit,
                 "kette": [(zeit, box, nutzlast)], "max_kette": 1, "geprueft": 1}
            self.naechste_nr += 1
            self.tracks.append(t)
            bedient.append(t)        # weitere Rest-Funde sieben auch gegen ihn
            if self.geprueft_im_burst == 0:
                self.geprueft_im_burst = 1
            ereignisse.append(("start", {"track": t["nr"], "neben": neben, "box": box}))
        return ereignisse

    def _anhaengen(self, t, zeit, box, nutzlast):
        """Fund in die Kette des Tracks; feuert dessen Trigger, wenn sie steht."""
        kette = t["kette"]
        while kette and zeit - kette[0][0] > self.fenster:
            kette.pop(0)
        kette.append((zeit, box, nutzlast))
        for j in range(max(0, len(kette) - self.deckel)):
            t_, bx_, _ = kette[j]
            kette[j] = (t_, bx_, None)           # Nutzlast freigeben, Zeit/Box bleiben
        t["max_kette"] = max(t["max_kette"], len(kette))
        if len(kette) >= self.anzahl:
            self.treffer += 1
            info = {"latenz_ms": 1000.0 * (zeit - t["start"]),
                    "spanne": zeit - kette[-self.anzahl][0],
                    "kette": list(kette[-self.anzahl:]),
                    "geprueft": t["geprueft"],
                    "track": t["nr"],
                    # Trigger-Nummer IN die info: zwei Trigger im selben Bild
                    # laesen sonst beide denselben Endstand von self.treffer ab
                    # (Dateinamen-Kollision).
                    "treffer": self.treffer}
            self.tracks = [x for x in self.tracks if x["nr"] != t["nr"]]
            self.karenzen.append({"nr": t["nr"], "ruhe_bis": zeit + self.karenz,
                                  "box": box})
            if not self.tracks:
                self.geprueft_im_burst = 0
            return ("trigger", info)
        return None


def referenzen_laden(app):
    """Gelernte Personen -> {Name: Nx512}. NICHTS nachgebaut: beide Wege sind die
    Bestands-Funktionen aus anlernen.py, die auch der Dienst nutzt.

    Weg 1 ist der Referenz-Cache (verify_data/clips/refcache.npz), den der Dienst
    ohnehin pflegt — Lesen kostet Millisekunden statt einen Embedder-Lauf ueber
    hunderte Referenzbilder. Weg 2 (Cache fehlt/leer/anderes Recognition-Modell)
    ist anlernen.lade_master_refs().

    DIE FALLE (gemessen, Projekt-Memory): Referenzen muessen mit det_size 320
    gerechnet werden — die Referenzbilder sind kleine Crops, bei 1280 findet der
    Detektor darin nichts und die Referenzmatrix bleibt STILL leer. Der Embedder
    steht nach __init__ auf 320, und diese Funktion laeuft VOR der Bildschleife.
    Wer hier spaeter ein set_det_size() fuers grosse Bild einbaut: NACH diesem
    Aufruf, nie davor."""
    import anlernen
    cache = os.path.join(anlernen.CLIPS, "refcache.npz")
    if os.path.exists(cache):
        try:
            z = np.load(cache, allow_pickle=True)
            if str(anlernen._cache_meta(z).get("§modell", "")) == app.modell:
                refs = {p: np.asarray(z[p], np.float32) for p in z.files
                        if p not in ("meta", "§meta")}
                if any(len(M) for M in refs.values()):
                    return refs, f"refcache ({app.modell})"
        except Exception:
            pass
    return anlernen.lade_master_refs(app), f"Master-Ordner ({app.modell})"


# Meldungs-Texte des Schnell-Urteils. Engine-Default englisch (UI-Sprache,
# Bauplan §1/§6); der Prototyp reicht seine deutschen Bestands-Texte durch,
# damit seine Meldungen byte-gleich bleiben. [ERBE-ANPASSUNG]
# Kosinus-raus (.249, User-Go 17.08.): Default-Texte sprechen WORTE aus der
# einen Quelle core/vertrauen ({wort} = Lage zur Messlatte); die Rohzahl
# haengt der Aufrufer nur im Stil 'worte_zahlen' an (alert_stil-Option).
#
# SPRACH-STUFE 4 — GRENZE, BEWUSST (der EINE echte Konflikt der Stufe):
# dieser Text ist DREIFACH genutzt und nicht ohne Struktur-Umbau teilbar —
# (1) er steht als WERT im MQTT-Payload (Engine._trigger:
#     payload["schnell_urteil"]["text"]), und die Additiv-Invariante sagt:
#     kein bestehendes MQTT-Feld aendert seine Bytes;
# (2) er steht in der Kachel-Log-Zeile (_klog) — Log bleibt englisch (B20);
# (3) er haengt am Push-/Telegram-Text (dort waere er sprachfaehig).
# Eine Trennung braucht eine zweite Rueckgabe aus schnell_urteil(), also
# einen Bruch des [ERBE-ANPASSUNG]-Kontrakts mit prototyp/live_wache.py
# (drei Aufrufstellen mit Tupel-Entpackung). Das ist ein eigener Zug mit
# User-Entscheid, nicht Teil des Einzugs — bis dahin bleibt der Text
# englisch, und mit ihm die Wortstufe darin (vertrauen.wort, Zeile ~891).
TEXT_URTEIL_TREFFER = "probably {name} (preliminary quick check — {wort})"
TEXT_URTEIL_UNSICHER = ("unknown/uncertain (preliminary — best candidate "
                        "{name} is {wort})")


def schnell_urteil(refs, kandidaten, schwelle, max_bilder=None,
                   text_treffer=TEXT_URTEIL_TREFFER, text_unsicher=TEXT_URTEIL_UNSICHER):
    """Vorlaeufiger Namens-Hinweis fuer die MELDUNG (nie fuer das Protokoll).

    kandidaten = [(det_score, face)] aus der Burst-Kette, die besten zuerst.
    Das Embedding ist bereits da: der Detektionslauf app.get() rechnet
    Landmarks + Recognition ohnehin in einem Zug, face.normed_embedding ist
    also ein FERTIGES Ergebnis und kein zweiter Modelllauf. Verglichen wird
    mit anlernen.nn() — derselbe Nearest-Neighbour ueber alle Referenzvektoren
    einer Person wie im Bestand, kein eigener Vergleich.

    -> (text, person_oder_None, cos). text ist IMMER als vorlaeufig markiert.
    [ERBE-ANPASSUNG] max_bilder ist Parameter (statt ENV LIVE_URTEIL_BILDER),
    die Texte sind Format-Parameter (Engine englisch, Prototyp deutsch)."""
    if not refs or schwelle is None:
        return None, None, None
    import anlernen
    mb = URTEIL_BILDER if max_bilder is None else int(max_bilder)
    bester_name, bester_cos = None, -1.0
    for _score, f in kandidaten[:max(1, mb)]:
        try:
            v = np.asarray(f.normed_embedding, np.float32)
        except Exception:
            continue
        if v.size != 512 or not np.all(np.isfinite(v)):
            continue
        p, s = anlernen.nn(refs, v)
        if s > bester_cos:
            bester_name, bester_cos = p, s
    if bester_name is None:
        return None, None, None
    from core import vertrauen as _vt
    _wort = _vt.wort(bester_cos, schwelle)
    if bester_cos >= schwelle:
        return (text_treffer.format(name=bester_name, cos=bester_cos,
                                    wort=_wort),
                bester_name, bester_cos)
    return (text_unsicher.format(cos=bester_cos, name=bester_name,
                                 schwelle=schwelle, wort=_wort),
            None, bester_cos)


_POSE = {"wache": None, "fehler": None}


def pose_wache():
    """RTMPose EINMALIG und erst beim ERSTEN Trigger laden (lazy).

    Warum nicht beim Start: das Modell (rtmpose-m, 146 MB ONNX) kostet dauerhaft
    Arbeitsspeicher (Vorfall 10.08. 19:17). Ein Waechter, der nie ausloest, soll
    das Modell nie im Speicher haben. Scheitert das Laden, wird der Fehler EINMAL
    gemerkt; die Wache laeuft dann ohne Gate weiter (lieber melden als blind).

    Import ueber die prototyp/-sys.path-Bruecke — dasselbe Muster wie
    core/personlive (prototyp/pose_wache.py ist via personlern_stage
    Produktionscode im Image, tools/risikoklasse.py A_IMPORTIERT).

    [ERBE-ANPASSUNG, DEKLARIERT (Lens-A M6/§6):] im Prototyp-Basisstand lag
    `from pose_wache import PoseWache` AUSSERHALB des try — ein fehlendes Modul
    flog beim ersten Trigger LAUT heraus und toetete den Waechter. Hier faengt
    das try auch den ImportError, BEWUSST: ein fehlendes Gate darf den Waechter
    nicht toeten (lieber ungefiltert melden als gar nicht). Der Preis — ohne
    Gate meldet jede Katze — darf dafuer NIE still bleiben: die Engine loggt
    den Ausfall LAUT je Trigger-Drosselfenster und schickt eine Stoerungs-
    Selbstmeldung (s. Engine._trigger). Der Prototyp erbt das Verhalten
    (deklariert in seiner pose_bestaetigt-Huelle)."""
    if _POSE["wache"] is None and _POSE["fehler"] is None:
        try:
            proto = os.path.join(WURZEL, "prototyp")
            if proto not in sys.path:
                sys.path.insert(0, proto)
            from pose_wache import PoseWache
            _POSE["wache"] = PoseWache()
        except Exception as e:
            _POSE["fehler"] = f"{type(e).__name__}: {str(e)[:80]}"
    return _POSE["wache"]


def person_region(bbox, breite, hoehe):
    """Aus der GESICHTSBOX die Region schaetzen, in der der zugehoerige Koerper
    stehen muesste — (x1, y1, x2, y2), Bildgrenzen bewusst NICHT geklemmt.

    RTMPose ist ein top-down-Modell: es braucht einen Ausschnitt, der eine
    Person zeigt, und legt sein Skelett IMMER hinein. Das ganze Kamerabild als
    Ausschnitt taugt deshalb nicht — gemessen an denselben 54 Triggern bleibt
    eine echte Person auf Distanz dort bei Kopf-Score 0,35-0,43 und liegt damit
    UNTER der Katze (0,29). Erst der Ausschnitt um die Fundstelle trennt sauber.

    Die Masse sind an dem Material gefittet, nicht hergeleitet: eine stehende
    Person ist rund acht Gesichtsboxen hoch, der Kopf sitzt oben. Genau
    stimmen muessen sie nicht — die Pose-Wache setzt selbst noch Polster 1.25
    dazu und rueckt das Seitenverhaeltnis auf 3:4 zurecht.
    Nicht geklemmt wird, weil skelett() den Ausschnitt ueber eine Affin-
    transformation holt: was ueber den Bildrand ragt, wird schwarz aufgefuellt.
    Ein Klemmen wuerde die Person stattdessen verzerren."""
    x1, y1, x2, y2 = [float(v) for v in bbox]
    bh = max(1.0, y2 - y1)
    cx = 0.5 * (x1 + x2)
    return (cx - 2.4 * bh, y1 - 0.6 * bh, cx + 2.4 * bh, y1 + 8.0 * bh)


def pose_bestaetigt(kette, log=print, kopf_schwelle=None):
    """Steht an der Fundstelle ein MENSCH? -> (ok, detail).

    Das Melde-Gate des Triggers: die 2-4 Bilder der Burst-Kette gehen EINMALIG
    durch die Pose-Wache, je Bild in der aus der Gesichtsbox gerechneten
    Personenregion. Findet KEINES ein Skelett mit brauchbarem Kopf-Score, war
    der Trigger kein Mensch — keine Meldung.

    ODER ueber die Bilder, nicht UND: ein Mensch im Durchgang dreht sich, wird
    halb verdeckt, laeuft aus dem Bild. Ein Bild mit klarem Skelett reicht als
    Beleg; die Fehlklassen (Katze, Karosserie-Phantom, Laub) liefern in KEINEM
    Bild eines, das ist ja ihr Wesen — sie sehen in jedem Bild gleich aus.

    GRENZE, bewusst: geprueft wird die AUSLOESENDE Fundstelle, nicht die Szene.
    [ERBE-ANPASSUNG] kopf_schwelle ist Parameter (None -> POSE_KOPF-Literal);
    der Prototyp reicht seine ENV-Schwelle durch."""
    schwelle = POSE_KOPF if kopf_schwelle is None else float(kopf_schwelle)
    w = pose_wache()
    if w is None:
        return True, {"grund": f"Pose-Wache nicht ladbar ({_POSE['fehler']}) — Gate aus"}
    from pose_wache import KOPF_IDX
    t0 = time.time()
    koepfe = []
    for _t, _bx, nutzlast in kette:
        bild = nutzlast[0] if nutzlast else None
        gesicht = nutzlast[1] if nutzlast and len(nutzlast) > 1 else None
        if bild is None or gesicht is None:
            continue
        h_, b_ = bild.shape[:2]
        try:
            _pts, sc = w.skelett(bild, bbox=person_region(gesicht.bbox, b_, h_))
            koepfe.append(float(max(sc[i] for i in KOPF_IDX)))
        except Exception as e:
            log(f"   Pose-Bestaetigung: Bild uebersprungen ({type(e).__name__}: {e})")
    ms = 1000.0 * (time.time() - t0)
    if not koepfe:
        # Kein Bild pruefbar (Nutzlast schon freigegeben): NICHT verwerfen.
        # Ein Gate, das mangels Material blockt, verschluckt echte Meldungen.
        return True, {"grund": "keine Bilder pruefbar — Gate uebersprungen", "ms": round(ms)}
    return (max(koepfe) >= schwelle,
            {"kopf_max": round(max(koepfe), 3), "kopf": [round(k, 3) for k in koepfe],
             "bilder": len(koepfe), "ms": round(ms), "schwelle": schwelle})


def video_bauen(frames, pfad, fps):
    """Kurzer Rueckblick als MP4 (H.264, damit Telegram es abspielt). Erzeugt aus
    den gepufferten Bildern, es wird also NICHTS zusaetzlich von der Kamera geholt."""
    if not frames:
        return None
    h, b = frames[0].shape[:2]
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{b}x{h}", "-r", f"{max(fps, 1):.2f}", "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", pfad],
        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for f in frames:
            p.stdin.write(f.tobytes())
        p.stdin.close()
        p.wait(timeout=60)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass
        return None
    return pfad if os.path.exists(pfad) and os.path.getsize(pfad) > 0 else None


# ======================================================================
# NEU: Quelle aufloesen, Steckbrief, lauter HW-Rueckfall, Quell-Test (§5)
# ======================================================================

def producer_url(host, kamera, log=print):
    """Producer-URL einer Kamera aus der go2rtc-API (Quellentyp 'direct').
    Geerbt aus prototyp/live_wache.stream_url (der ENV-Schalter LIVE_QUELLE
    bleibt dem Prototyp; das Produkt entscheidet per Config). None = keiner."""
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://{host}:1984/api/streams", timeout=15) as r:
            d = json.load(r)
        for p in (d.get(kamera) or {}).get("producers") or []:
            u = str(p.get("url") or "")
            if u.startswith("rtsp://") and ":8554/" not in u:
                return u
    except Exception as e:
        log(f"  !! go2rtc-Lookup {type(e).__name__} fuer {kamera}")
    return None


def proxy_url(cfg, kamera):
    """Die EINE Proxy-URL-Formel (go2rtc-Restream) -> url|None. Verbraucher:
    quelle_aufloesen UND der Stream-Steckbrief-Lauf des Dienstes (13.08.) —
    K3: keine zweite Host-Zerlegung neben dieser."""
    host = (cfg.get("frigate_url") or "").split("//")[-1].split(":")[0].split("/")[0]
    if not host:
        return None
    return f"rtsp://{host}:8554/{kamera}"


def quelle_aufloesen(cfg, kamera, guard, streng=False, log=print):
    """Guard-Config -> (url, weg, fehler). Wege: proxy | direct | url.

    streng=True ist der TEST-MODUS (Bauplan §5 Stufe 1): der User hat 'direct'
    gewaehlt und soll erfahren, dass es nicht geht — KEIN stiller Proxy-
    Rueckfall. Im BETRIEB (streng=False) faellt 'direct' LAUT auf den Proxy
    zurueck (Reconnect-Verhalten des Prototyps: lieber Bilder als Stillstand,
    aber nie still)."""
    q = str(guard.get("quelle") or "proxy")
    if q == "url":
        u = str(guard.get("url") or "")
        if not u:
            return None, q, "source 'url' selected but no stream URL configured"
        return u, q, None
    proxy = proxy_url(cfg, kamera)
    if not proxy:
        return None, q, "no Frigate URL configured"
    host = proxy.split("//")[-1].split(":")[0]
    if q == "proxy":
        return proxy, q, None
    if q == "direct":
        u = producer_url(host, kamera, log)
        if u:
            return u, q, None
        if streng:
            return None, q, f"no go2rtc producer for {kamera}"
        log(f"  !! direct: no go2rtc producer for {kamera} — falling back to proxy (LOUD)")
        return proxy, "direct->proxy", None
    return None, q, f"unknown source type {q!r}"


def steckbrief_ermitteln(url, versuche=4, log=print):
    """Stream-Steckbrief per ffprobe: Aufloesung, echte Framerate, Codec,
    Bitrate wo ffprobe sie nennt (RTSP meist nicht — ehrliche Grenze; die
    volle Stream-Analyse mit Durchsatz-Sampling ist ein DIENST-Feature nach
    dem Modulumbau, stand.md-Praezisierung 11.08. — die Engine erbt deren
    Steckbriefe dann nur). Retry-Muster wie masse() (transiente leere
    go2rtc-Antworten beim Mehrfach-Start, 11.08.)."""
    cmd = ["ffprobe", "-v", "error"]
    if url.startswith("rtsp://"):
        cmd += ["-rtsp_transport", "tcp"]
    cmd += ["-select_streams", "v:0", "-show_entries",
            "stream=width,height,codec_name,avg_frame_rate,bit_rate",
            "-of", "json", url]
    for i in range(versuche):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            d = json.loads(p.stdout or "{}")
            st = (d.get("streams") or [{}])[0]
            b, h = int(st.get("width") or 0), int(st.get("height") or 0)
            if b and h:
                fps = None
                fr = str(st.get("avg_frame_rate") or "")
                if "/" in fr:
                    z, n = fr.split("/")
                    if float(n or 0):
                        fps = round(float(z) / float(n), 2)
                brate = st.get("bit_rate")
                return {"breite": b, "hoehe": h,
                        "fps": fps, "codec": st.get("codec_name") or "",
                        "bitrate_kbps": round(int(brate) / 1000) if brate else None}
        except Exception as e:
            log(f"steckbrief: {type(e).__name__} fuer {quelle_maskiert(url)} "
                f"(Versuch {i + 1}/{versuche})")
        if i + 1 < versuche:
            time.sleep(5 * (2 ** i))
    raise RuntimeError(f"steckbrief: ffprobe liefert nach {versuche} Versuchen "
                       f"nichts fuer {quelle_maskiert(url)}")


def leser_mit_rueckfall(url, skala, log=print, probe_s=6.0):
    """leser() MIT der HW-Wahl nach Verfuegbarkeit (hw_wahl) und lautem
    SW-Rueckfall (Bauplan §5 Stufe 3 — der geerbte leser() kennt keinen: eine
    gescheiterte HW-Pipe liefert dort einfach keine Bilder, stumm). Vorbild
    ist decode.FrameIter.hwdec_fallback (decode.py:243): scheitert die
    GEWAEHLTE HW-Pipe (kein Byte binnen probe_s oder ffmpeg-Ende), wird sie
    gekillt und LAUT auf SW-Decode gewechselt — gleiche Bytes, nur teurer.
    Ist gar keine HW verfuegbar, startet SW-Decode DIREKT (kein Probe-Umweg,
    keine Rueckfall-Zeile — es gab nichts, wovon zurueckzufallen waere).
    -> (Popen, b, h, hw): 'vaapi'/'nvdec' = HW-Pipe laeuft · None = SW-Decode
    direkt gewaehlt · False = HW angefordert und LAUT zurueckgefallen."""
    wahl = hw_wahl()
    if wahl is None:
        p, b, h = leser(url, rate=1, skala=skala, hw=False)
        return p, b, h, None
    p, b, h = leser(url, rate=1, skala=skala, hw=wahl)
    frist = time.monotonic() + probe_s
    while time.monotonic() < frist:
        if p.poll() is not None:
            break                                    # ffmpeg schon tot -> Rueckfall
        r, _, _ = select.select([p.stdout], [], [], 0.25)
        if r:
            return p, b, h, wahl                     # HW-Pipe liefert
    try:
        p.kill()
        p.wait()
    except Exception:
        pass
    log(f"  !! HW-Decode ({wahl}) liefert nicht ({quelle_maskiert(url)}) — "
        f"LAUTER Rueckfall auf Software-Decode (.hwdec_fallback-Muster)")
    p, b, h = leser(url, rate=1, skala=skala, hw=False)
    return p, b, h, False


def quelle_fp(guard):
    """Quell-Fingerprint (Bauplan §2.4/§5): Hash aus quelle+url — und seit
    .194 der EXPLIZIT gesetzten Verarbeitungshoehe (ein Hoehen-Wechsel
    aendert Skala/Netz/Last, der alte Test gilt dann nicht mehr). Guards
    OHNE eigenes hoehe-Feld behalten das alte Hash-Format — bestehende
    gruene Tests verfallen beim Update NICHT."""
    roh = f"{guard.get('quelle') or 'proxy'}|{guard.get('url') or ''}"
    if guard.get("hoehe"):
        roh += f"|{guard['hoehe']}"
    return hashlib.sha256(roh.encode()).hexdigest()[:16]


def test_gueltig(guard):
    """Enable-Riegel, SERVERSEITIG (Bauplan §2.4): (ok, grund). Ein Guard darf
    nur laufen, wenn ein gruener Test fuer GENAU diese Quell-Konfiguration
    vorliegt (Fingerprint-Vergleich)."""
    t = guard.get("test") or {}
    if not t.get("ok"):
        return False, "no successful source test recorded"
    if str(t.get("quelle_fp") or "") != quelle_fp(guard):
        return False, "source changed since last test — test invalidated"
    return True, ""


def lieferrate(frames, n_nach, dauer):
    """-> (rate, art) der Quelltest-Ratenmessung (.196). 'delivery' = Bilder
    NACH dem Burst-Fenster je Sekunde (die echte Lieferrate der Quelle);
    'throughput' = alles kam im Burst (Datei/kurzes Fenster) — dann ehrlich
    der alte Durchsatz-Wert, gekennzeichnet statt als fps ausgegeben."""
    if n_nach >= 3 and dauer > LIEFER_BURST_S + 0.5:
        return round(n_nach / (dauer - LIEFER_BURST_S), 1), "delivery"
    return round(frames / max(dauer, 0.001), 1), "throughput"


def quelle_testen(cfg, kamera, guard, detektor, log=print, det_basis=None,
                  hoehe=None, soll_frames=20, frist_s=15.0, kill_registrar=None,
                  mess_s=LIEFER_MESS_S):
    """Die Test-Strecke aus Bauplan §5 — vier Stufen, jede mit eigenem
    Fehlertext, nie Secrets in der Meldung. -> (ok, klartext, testblock|None).

    kill_registrar (Engine-B1): optionales Callable, dem der kill-Griff des
    ffmpeg-Kinds uebergeben wird — der Not-Aus der Engine kann damit eine
    haengende Test-Verbindung von aussen beenden (EOF loest jede Blockade)."""
    det_basis = int(det_basis or DET_BASIS)
    # 1) Quelle aufloesen — im Test STRENG (kein stiller Rueckfall).
    url, weg, fehler = quelle_aufloesen(cfg, kamera, guard, streng=True, log=log)
    if fehler:
        return False, f"step 1/4 (resolve source): {fehler}", None
    # 2) Sondieren.
    try:
        steck = steckbrief_ermitteln(url, versuche=2, log=log)
    except Exception as e:
        return False, (f"step 2/4 (probe): {type(e).__name__}: {str(e)[:120]}"), None
    skala = wach_skala(steck["breite"], steck["hoehe"], hoehe)
    from face_audit import Embedder
    netz = Embedder.ar_det_size(skala[0], skala[1], basis=det_basis)
    # 3) Bildstrom — mindestens soll_frames Bilder in hoechstens frist_s;
    #    HW-Rueckfall LAUT, Ergebnis traegt hw:false (Test besteht, aber sichtbar).
    #    FRIST ECHT (Engine-B1): bilder_yuv_frist statt bilder_yuv — eine
    #    lebende, stumme Quelle blockierte den blockierenden read() sonst weit
    #    ueber frist_s hinaus (die Frist griff nur je geliefertem Bild).
    p, b, h, hw = leser_mit_rueckfall(url, skala, log=log)
    if kill_registrar is not None:
        def _toeten():
            try:
                p.kill()
                p.wait()
            except Exception:
                pass
        kill_registrar(_toeten)
    frames = 0
    t0 = time.monotonic()
    frame_bgr = None
    n_nach = 0        # Bilder NACH dem Burst-Fenster -> LIEFERRATE (.196):
    #                   der alte Abbruch bei soll_frames mass den Decode-
    #                   DURCHSATZ des gepufferten Anfangs-GOP (79,6 "fps" bei
    #                   real 15,5) und liess den Slot-Riegel Fehlurteile
    #                   faellen. Jetzt laeuft der Strom mindestens mess_s
    #                   wall-clock, gezaehlt wird ab LIEFER_BURST_S.
    try:
        for yuv in bilder_yuv_frist(p, b, h, frist_s):
            frames += 1
            if frames == 1:
                frame_bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
            vergangen = time.monotonic() - t0
            if vergangen > LIEFER_BURST_S:
                n_nach += 1
            if frames >= soll_frames and vergangen >= mess_s:
                break
    finally:
        try:
            p.kill()
            p.wait()
        except Exception:
            pass
    dauer = max(time.monotonic() - t0, 0.001)
    if frames < soll_frames:
        return False, (f"step 3/4 (stream): only {frames}/{soll_frames} frames "
                       f"in {dauer:.1f}s"), None
    rate, rate_art = lieferrate(frames, n_nach, dauer)
    # 4) Detektor-Pass — ECHTER Provider aus der Session (K1-Lehre 09.08.:
    #    ohne die Kontrolle faellt onnxruntime lautlos auf CPU, Faktor ~150).
    try:
        detektor.erkennen(frame_bgr, netz)
        prov = detektor.provider()
    except Exception as e:
        return False, f"step 4/4 (detector): {type(e).__name__}: {str(e)[:120]}", None
    block = {"ok": True, "ts": round(time.time(), 1), "quelle_fp": quelle_fp(guard),
             "aufloesung": f"{steck['breite']}x{steck['hoehe']}",
             "skala": f"{b}x{h}", "bilder_s": rate, "bilder_s_art": rate_art,
             "provider": prov, "hw": bool(hw)}
    warn = ""
    if prov.startswith("CPU"):
        warn = " — WARNING: detector runs on CPU (expected a GPU provider)"
    if hw is False:
        warn += " — note: software decode (hardware pipe failed, works but costs more CPU)"
    elif hw is None:
        warn += " — note: software decode (no hardware decoder available)"
    text = (f"source OK ({weg}, {steck['breite']}x{steck['hoehe']}"
            + (f" @ {steck['fps']} fps" if steck.get("fps") else "")
            + (f", {steck['codec']}" if steck.get("codec") else "")
            + f" -> {b}x{h}, {rate} frames/s, provider {prov}){warn}")
    return True, text, block


# ======================================================================
# Engine-Bausteine: Scheduler, Selbstvermessung, Stoerungsmelder
# ======================================================================

class Scheduler:
    """EIN Detektor, N Kacheln (Architektur B, Bauplan §7).

    Einreihungs-Regeln (jede im Harnisch bewiesen, tools/harnisch_live1.py):
      * JE KACHEL EIN PLATZ, latest wins: reiht eine Kachel ein neues Bild ein,
        waehrend ihr altes noch wartet, ersetzt das neue das alte (das alte ist
        ohnehin veraltet). Ersetzungen werden GEZAEHLT (ueberlast_ersetzt) —
        messbare Degradation, nie stille (§7 QS-Auflage). Der EINREIH-Zeitpunkt
        des Platzes bleibt dabei stehen (s. Ventil).
      * BURST VOR NORMALTAKT, innerhalb der Klasse der aelteste PLATZ zuerst.
      * FAIRNESS-VENTIL gegen Verhungern — Bezugsgroesse ist die BELEGUNGS-
        DAUER des Platzes, nicht das Alter des aktuell wartenden Bildes
        (Lens-A M8, Semantik jetzt ehrlich benannt): ist der aelteste Normal-
        PLATZ laenger als NORMAL_MAX_WARTE_S belegt, kommt er VOR dem Burst
        dran. Genau diese Semantik macht min() ueber die Belegungsdauer zum
        FIFO und haelt den Scheduler auch bei fuenf Dauer-Bursts fair
        (Lens-A §5 Punkt 1 — deshalb bewusst NICHT auf Bild-Alter umgestellt).
      * UEBERLAST-DROSSEL: die gemessene Thread-Belegung (Gleitfenster)
        schaltet Stufen 0..max; Stufe s bedeutet Normaltakt nur jedes 2**s-te
        Raster-Bild. Bursts werden NIE gedrosselt (die 337-ms-Zusage gilt genau
        dann); der Eingriff steht im Status, statt still langsamer zu werden.
        RAUF entscheidet die GEMESSENE (gedrosselte) Last, RUNTER die um EINE
        Stufe hochgerechnete (a * 2) — sonst flattert die Stufe (Band ohne
        Betriebspunkt) oder sie parkt nach einem Lastberg dauerhaft zu hoch
        (M-C Sched-R1, beide Runden am DROSSEL_RUNTER-Literal; Fall t3c im
        Harnisch mit den echten Konstanten, inkl. Abstieg vom Lastberg).
      * NEBENLAEUFIGKEIT (Lens B1-Fix): `arbeit` (deque) wird NUR unter `_cv`
        beruehrt — Detektor-Thread (arbeit_melden) und Status-Thread
        (auslastung/status) teilen sie sich; das Lock ist reentrant, weil
        status() -> auslastung() verschachtelt."""

    def __init__(self, jetzt=time.monotonic, budget_ms_je_s=GPU_BUDGET_MS_JE_S,
                 hoch=DROSSEL_HOCH, runter=DROSSEL_RUNTER,
                 fenster_s=DROSSEL_FENSTER_S, max_stufe=DROSSEL_MAX_STUFE,
                 haltezeit_s=DROSSEL_HALTEZEIT_S,
                 normal_max_warte_s=NORMAL_MAX_WARTE_S,
                 stufenbasis=DROSSEL_STUFENBASIS):
        self.jetzt = jetzt
        self.budget_ms_je_s = float(budget_ms_je_s)
        self.hoch = float(hoch)
        self.runter = float(runter)
        self.fenster_s = float(fenster_s)
        self.max_stufe = int(max_stufe)
        self.haltezeit_s = float(haltezeit_s)
        self.normal_max_warte_s = float(normal_max_warte_s)
        # EINE Basis fuer Takt-Faktor UND Abbau-Hochrechnung (K3, s. Literal).
        self.stufenbasis = float(stufenbasis)
        # RLock: status() haelt das Lock und ruft auslastung(), die es erneut
        # nimmt (B1-Fix — vorher lag `arbeit` komplett ungeschuetzt).
        self._cv = threading.Condition(threading.RLock())
        self.plaetze = {}            # name -> [einreih_mono, burst, nutzlast]
        self.ersetzt = collections.Counter()
        self.arbeit = collections.deque()    # (mono, dauer_s)
        self.stufe = 0
        self._stufe_mono = -1e18

    def einreihen(self, name, burst, nutzlast, mono=None):
        mono = self.jetzt() if mono is None else mono
        with self._cv:
            if name in self.plaetze:
                self.ersetzt[name] += 1
                alt = self.plaetze[name]
                # latest wins; ein Burst-Platz bleibt Burst, auch wenn ein
                # Normal-Bild ihn ersetzt (die Kachel IST im Burst oder war es
                # gerade — Prioritaet nicht durch Ersetzen verlieren).
                self.plaetze[name] = [alt[0], burst or alt[1], nutzlast]
            else:
                self.plaetze[name] = [mono, bool(burst), nutzlast]
            self._cv.notify()

    def naechste(self, timeout=0.5):
        """-> (name, burst, nutzlast, einreih_mono) oder None (leer/Timeout)."""
        with self._cv:
            if not self.plaetze and timeout:
                self._cv.wait(timeout)
            if not self.plaetze:
                return None
            mono = self.jetzt()
            normal = [(v[0], n) for n, v in self.plaetze.items() if not v[1]]
            burst = [(v[0], n) for n, v in self.plaetze.items() if v[1]]
            # Fairness-Ventil auf BELEGUNGSDAUER (s. Klassen-Docstring).
            if normal and (not burst
                           or mono - min(normal)[0] > self.normal_max_warte_s):
                wahl = min(normal)[1]
            elif burst:
                wahl = min(burst)[1]
            else:
                wahl = min(normal)[1]
            einreih, b, nutzlast = self.plaetze.pop(wahl)
            return wahl, b, nutzlast, einreih

    def arbeit_melden(self, dauer_s, mono=None):
        """Thread-Belegung verbuchen (die GANZE Verarbeitungszeit eines Bilds,
        nicht nur erkennen() — Lens-B M5: Pose-Gate und JPEG-Ablage laufen im
        selben Thread und waren der Drossel unsichtbar); passt ggf. die
        Drossel-Stufe an. -> neue Stufe, wenn GEAENDERT, sonst None.
        Komplett unter `_cv` (B1-Fix: deque-Mutation gegen Iteration)."""
        mono = self.jetzt() if mono is None else mono
        with self._cv:
            self.arbeit.append((mono, float(dauer_s)))
            grenze = mono - self.fenster_s
            while self.arbeit and self.arbeit[0][0] < grenze:
                self.arbeit.popleft()
            if mono - self._stufe_mono < self.haltezeit_s:
                return None
            a = self.auslastung(mono)
            budget = self.hoch * (self.budget_ms_je_s / 1000.0)
            runter = self.runter * (self.budget_ms_je_s / 1000.0)
            neu = self.stufe
            # M-C (Sched-R1, zweistufig gemessen): RAUF sieht die gemessene
            # (gedrosselte) Last — weiter drosseln nur, wenn die GEDROSSELTE
            # Realitaet noch zu hoch ist. RUNTER rechnet die Last um genau
            # EINE Stufe hoch (a * 2): geloest wird, sobald der NAECHST-
            # niedrigere Takt traegt. Runde 1 (354 Stufenwechsel/h, sauber
            # periodisch 0->1->0->1): RUNTER sah die gedrosselte, RAUF die
            # rohe Last — kein Betriebspunkt im Band. Runde 2 (Widerleger
            # 12.08.): die VOLLE Hochrechnung (a * 2**stufe) loeste erst,
            # wenn Stufe 0 truege — nach einem Lastberg parkte die Drossel
            # dauerhaft bis zu 3 Stufen zu hoch (det 53 ms: Takt 1/8 statt
            # 1/2). a * 2 ist im selben Sweep flatterfrei (rauf verlangt
            # a > 0,765, runter a < 0,27 — schliessen sich aus) und findet
            # nach dem Berg die kleinste ausreichende Stufe (+1 Hysterese)
            # wieder. Burst-Anteile sind ungedrosselt und werden trotzdem
            # mit hochgerechnet — sichere Richtung; das Gleitfenster leert
            # den Burst binnen fenster_s.
            if a > budget and self.stufe < self.max_stufe:
                neu = self.stufe + 1
            elif a * self.stufenbasis < runter and self.stufe > 0:
                neu = self.stufe - 1
            if neu != self.stufe:
                self.stufe = neu
                self._stufe_mono = mono
                return neu
            return None

    def auslastung(self, mono=None):
        """Belegungs-Anteil (0..1 der Wanduhr) im Gleitfenster — unter `_cv`
        (B1-Fix), reentrant aus status() heraus."""
        mono = self.jetzt() if mono is None else mono
        with self._cv:
            grenze = mono - self.fenster_s
            return sum(d for t, d in self.arbeit if t >= grenze) / self.fenster_s

    def normal_faktor(self):
        # Dieselbe Basis wie die RUNTER-Hochrechnung (self.stufenbasis, K3):
        # Stufe s bedeutet Normaltakt nur jedes Basis**s-te Raster-Bild.
        return int(round(self.stufenbasis ** self.stufe))

    def raeumen(self):
        """Alle wartenden Plaetze verwerfen -> Anzahl. Fuer die Auftrags-Pause
        (Engine-M1): statt des 0,5-s-'Entwaesserns' (Zeitannahme, gemessen ab
        Rueckstand > 500 ms falsch) wird der Rueckstand VERWORFEN — latest
        wins heisst: die Bilder waeren beim Wiederanlauf ohnehin veraltet."""
        with self._cv:
            n = len(self.plaetze)
            self.plaetze.clear()
            return n

    def status(self):
        with self._cv:
            return {"drossel_stufe": self.stufe,
                    "normal_faktor": self.normal_faktor(),
                    "auslastung": round(self.auslastung(), 3),
                    "wartend": len(self.plaetze),
                    "ersetzt": dict(self.ersetzt)}


def ram_frei_mb():
    """(frei_mb, quelle). Ehrliche RAM-Quelle IM Container: cgroup v2, dann v1.
    /proc/meminfo ist im LXC der WIRT (Maschinen-Regel, CLAUDE.md) — nur als
    letzter Weg und dann ausdruecklich so beschriftet."""
    try:
        mx = open("/sys/fs/cgroup/memory.max").read().strip()
        cur = int(open("/sys/fs/cgroup/memory.current").read().strip())
        if mx != "max":
            return (int(mx) - cur) / 1048576.0, "cgroup2"
    except Exception:
        pass
    try:
        lim = int(open("/sys/fs/cgroup/memory/memory.limit_in_bytes").read().strip())
        use = int(open("/sys/fs/cgroup/memory/memory.usage_in_bytes").read().strip())
        if lim < 1 << 60:
            return (lim - use) / 1048576.0, "cgroup1"
    except Exception:
        pass
    try:
        for z in open("/proc/meminfo"):
            if z.startswith("MemAvailable:"):
                return int(z.split()[1]) / 1024.0, "meminfo (CAUTION: host view in LXC)"
    except Exception:
        pass
    return None, "unbekannt"


def rss_mb():
    """VmRSS des eigenen Prozesses in MB (immer ehrlich, auch im Container)."""
    try:
        for z in open("/proc/self/status"):
            if z.startswith("VmRSS:"):
                return round(int(z.split()[1]) / 1024.0, 1)
    except Exception:
        pass
    return None


class Selbstvermessung:
    """Slot-Mechanik (stand.md-Auflage 11.08.): der ANZAHL-Deckel aktiver
    Waechter kommt aus RAM- und GPU-Budget, hart max HART_MAX_SLOTS. Phase 1
    baut die MECHANIK als Engine-Faehigkeit (messen, Deckel bestimmen, Slots
    vergeben/verweigern MIT GRUND); die UI dafuer kommt in Phase 2.

    MESSUNG VOR LITERATUR (Bauplan §2.3/§7 'RAM erst messen, dann zitieren'):
     * det_ms: EMA der eigenen Detektions-Dauern; bis dahin der Seed 53 ms
       (stand.md, det-1280 iGPU) — als Seed MARKIERT.
     * je_stream_mb: RSS-Zuschlag je aktivem Stream — es gibt KEINEN
       Literatur-Seed (die ~700 MB des Prototyps sind je PROZESS und laut
       Bauplan §7 ausdruecklich Schaetzung, keine Messung). Bis zur ersten
       eigenen Messung kappt RAM deshalb NICHT ueber diesen Posten, sondern
       nur ueber die Restgrenze — und der Status sagt 'not yet measured'.
     * grundkosten_mb: RSS nach Modell-Aufbau, vor dem ersten Stream."""

    def __init__(self, rss_holen=rss_mb, ram_holen=ram_frei_mb,
                 hart_max=HART_MAX_SLOTS,
                 rest_min_mb=RAM_REST_MIN_MB):
        self.rss_holen = rss_holen
        self.ram_holen = ram_holen
        self.hart_max = int(hart_max)
        self.rest_min_mb = float(rest_min_mb)
        self.det_ms = None
        self.grundkosten_mb = None
        self.je_stream_mb = None
        self._mess_offen = None       # (rss_vorher, kacheln_dabei) einer laufenden Messung

    # ---- Messungen -------------------------------------------------------
    def det_messung(self, ms):
        self.det_ms = ms if self.det_ms is None else 0.9 * self.det_ms + 0.1 * ms

    def det_ms_wirksam(self):
        return (self.det_ms, "gemessen (EMA)") if self.det_ms is not None \
            else (DET_MS_SEED, "seed (53 ms, stand.md det-1280 iGPU — wird ersetzt)")

    def grundkosten_messen(self):
        self.grundkosten_mb = self.rss_holen()

    def stream_messung_start(self, n_aktiv):
        """VOR dem Start eines Streams aufrufen; abgeschlossen wird per
        stream_messung_ende() nach der Warmlauf-Frist. Nur EINE Messung
        gleichzeitig — ueberlappende Starts wuerden das Delta verfaelschen.
        EHRLICHE GRENZE (Lens-A M9): das 60-s-Fenster kann Fremdwachstum
        (z. B. das lazy geladene Pose-Modell nach einem fruehen Trigger)
        mitzaehlen — deshalb oeffnet die Engine die Messung NUR beim Start
        mit genau EINEM Stream, und die Quelle heisst 'naeherungsweise'."""
        if self._mess_offen is None:
            r = self.rss_holen()
            if r is not None:
                self._mess_offen = (r, n_aktiv)

    def stream_messung_ende(self):
        if self._mess_offen is None:
            return
        vorher, _n = self._mess_offen
        self._mess_offen = None
        nachher = self.rss_holen()
        if nachher is None or nachher <= vorher:
            return                                   # kein brauchbares Delta
        delta = nachher - vorher
        self.je_stream_mb = delta if self.je_stream_mb is None \
            else 0.7 * self.je_stream_mb + 0.3 * delta

    # ---- Budget-Rechnung -------------------------------------------------
    def slot_pruefen(self, n_belegt):
        """Darf ein weiterer Slot vergeben werden? -> (ok, grund).

        .196 (User: 'Messwerte sollen NICHT entscheiden, ob ein Waechter
        laufen kann'): KEIN GPU-Budget-Urteil mehr — die alte Vorhersage
        (geschaetzte fps x det-Seed gegen 60 % von 900 ms/s) faellte je
        nach Zufalls-Zustand verschiedene Urteile ueber dieselbe Config.
        Ueberlast faengt die Drossel zur LAUFZEIT an der echten Last.
        Es bleiben zwei NOTBREMSEN, beide ohne Schaetzwerte: der harte
        Deckel und der RAM-Boden (nur cgroup-MESSWERT, nie die Wirt-Sicht).
        Der Grund traegt immer die Zahlen der Entscheidung."""
        if n_belegt >= self.hart_max:
            return False, (f"hard cap: {self.hart_max} watchers maximum "
                           f"({n_belegt} already allocated)")
        frei, quelle = self.ram_holen()
        # Lens-B M7: /proc/meminfo zeigt im LXC den WIRT (CLAUDE.md-Maschinen-
        # regel; Thrashing-Vorfall 10.08.) — diese Quelle darf ANZEIGEN, aber
        # nie ENTSCHEIDEN: weder freigeben (16 GB "frei" waeren die Wirt-Sicht)
        # noch verweigern. Massgeblich sind nur Container-Limits (cgroup).
        massgeblich = frei is not None and not str(quelle).startswith("meminfo")
        if massgeblich:
            bedarf = self.je_stream_mb
            if bedarf is not None and frei - bedarf < self.rest_min_mb:
                return False, (f"RAM budget: {frei:.0f} MB free ({quelle}), "
                               f"one more stream costs ~{bedarf:.0f} MB (measured), "
                               f"would leave < {self.rest_min_mb:.0f} MB")
            if bedarf is None and frei < self.rest_min_mb:
                return False, (f"RAM budget: only {frei:.0f} MB free ({quelle}), "
                               f"below the {self.rest_min_mb:.0f} MB floor "
                               f"(per-stream cost not yet measured)")
        if massgeblich:
            ram_text = f", {frei:.0f} MB RAM free ({quelle})"
        elif frei is not None:
            ram_text = (", RAM not enforced (no container limit readable — "
                        "host view only)")
        else:
            ram_text = ", RAM not enforced (no memory source readable)"
        return True, (f"ok: slot {n_belegt + 1} of {self.hart_max}" + ram_text)

    def status(self):
        det, det_q = self.det_ms_wirksam()
        frei, quelle = self.ram_holen()
        # UI-M4 Rest-RAM-Ehrlichkeit (§2.3): was bliebe nach EINEM weiteren
        # Stream rechnerisch uebrig — mit Warnmarke unter der Restgrenze.
        rest = (frei - self.je_stream_mb
                if frei is not None and self.je_stream_mb is not None else None)
        return {"hart_max": self.hart_max,
                "det_ms": round(det, 1), "det_ms_quelle": det_q,
                "grundkosten_mb": self.grundkosten_mb,
                "je_stream_mb": (round(self.je_stream_mb, 1)
                                 if self.je_stream_mb is not None else None),
                "je_stream_quelle": ("eigene RSS-Delta-Messung (Ein-Stream-Start, "
                                     "naeherungsweise)"
                                     if self.je_stream_mb is not None
                                     else "not yet measured"),
                "ram_frei_mb": (round(frei) if frei is not None else None),
                "ram_quelle": quelle,
                "ram_massgeblich": (frei is not None
                                    and not str(quelle).startswith("meminfo")),
                "rest_nach_slot_mb": (round(rest) if rest is not None else None),
                "rest_warnung": bool(rest is not None and rest < self.rest_min_mb),
                "rss_mb": self.rss_holen()}


class Stoerungsmelder:
    """Stoerungs-Selbstmeldung je Kachel (§11 Entscheid 2 — PFLICHT, Realbelege
    11.08.: Waechter-Tod CL_OUT_OF_RESOURCES, dazu 'lebt, liefert nichts').

    Reine Zustandsmaschine, monotone Zeit, KEIN Versand hier (der Aufrufer
    schickt) — dadurch im Harnisch ohne Kanaele beweisbar. Eine Stoerung wird
    genau EINMAL gemeldet (nach nach_s Dauer-Stoerung), die Entwarnung genau
    einmal bei Rueckkehr, und nur wenn vorher gemeldet wurde."""

    def __init__(self, nach_s=STOERUNG_NACH_S):
        self.nach_s = float(nach_s)
        self.seit = None
        self.gemeldet = False

    def stoerung(self, mono):
        """Im gestoerten Zustand je Takt aufrufen. -> 'melden' | None."""
        if self.seit is None:
            self.seit = mono
        if not self.gemeldet and mono - self.seit >= self.nach_s:
            self.gemeldet = True
            return "melden"
        return None

    def erholt(self, mono):
        """Im gesunden Zustand je Takt aufrufen. -> 'entwarnung' | None."""
        war = self.gemeldet
        self.seit = None
        self.gemeldet = False
        return "entwarnung" if war else None

    def dauer(self, mono):
        return 0.0 if self.seit is None else mono - self.seit


def melde_erlaubt(kachel, mono):
    """MELDE-ANKER (§11 Entscheid 6): fruehestens wieder_scharf_s nach der
    letzten MELDUNG wird wieder gemeldet (0 = jeder Trigger meldet). Modul-
    Funktion statt Methode, damit der Mutations-Selbsttest sie fassen kann."""
    return mono >= kachel.melde_bis_mono


def watchdog_faellige(kacheln, mono, schwelle=WATCHDOG_S):
    """Liefer-Watchdog (Bauplan §8, Phase-1-Vorzieher): Kacheln, die 'aktiv'
    sind, laenger als die Schwelle VERBUNDEN, und trotzdem ohne frisches Bild —
    dort lebt ffmpeg, liefert aber nichts ('lebt, liefert nichts'-Klasse). -> Liste.

    Zwei Lens-Fixes, beide gemessen:
     * Gnadenfrist AB VERBINDUNG (Lens-A M1): `letztes_bild_mono` traegt nach
       einem Abriss den Wert der VORIGEN Verbindung — ohne den Anker
       `verbunden_mono` war eine frische Verbindung sofort faellig und der
       Backoff verdoppelte sich grundlos.
     * 'hat NIE geliefert' (Lens-B M4): `letztes_bild_mono is None` war vorher
       ein Freifahrtschein — eine lebende, stumme Pipe (auch nach dem
       SW-Rueckfall) blieb ewig 'aktiv' ohne Watchdog."""
    aus = []
    for k in kacheln:
        if k.zustand != "aktiv" or k.verbunden_mono is None:
            continue
        if mono - k.verbunden_mono <= schwelle:
            continue                              # Gnadenfrist der frischen Verbindung
        if k.letztes_bild_mono is None or mono - k.letztes_bild_mono > schwelle:
            aus.append(k)
    return aus


def stoerung_takt(k, mono, watchdog_s=WATCHDOG_S):
    """EIN Beobachtungs-Takt der Stoerungs-Eskalation je Kachel
    -> 'melden' | 'entwarnung' | None.

    B2-FIX (Lens A, gemessen: 73-min-Reconnect-Zyklus = 0 Meldungen): 'gesund'
    heisst LIEFERN (ein echtes Bild juenger als watchdog_s), NICHT 'verbunden'.
    Der alte Anker am Momentanzustand nullte die 300-s-Frist bei jedem
    Reconnect (Zyklus ~21 s: aktiv 15 s -> gestoert ~6 s -> aktiv ...), die
    Selbstmeldung kam nie. Jetzt laeuft die Frist durch, solange keine Bilder
    kommen — egal wie oft der Reconnect dreht; die Entwarnung gibt es erst,
    wenn wirklich wieder ein Bild geflossen ist (ihr Text stimmt damit).
    Reine Logik (Harnisch simuliert sie mit den ECHTEN Konstanten)."""
    liefert = (k.zustand == "aktiv" and k.letztes_bild_mono is not None
               and mono - k.letztes_bild_mono <= watchdog_s)
    if liefert:
        return k.stoer.erholt(mono)
    return k.stoer.stoerung(mono)


def aktiv_fps(k, mono):
    """Reale Lieferrate einer AKTIVEN Kachel fuer die Slot-Neubewertung
    -> Bilder/s (float) oder Steckbrief-fps als Fallback.

    M-D (Sched-R2, Widerleger 12.08. gemessen: ffprobe-Nennrate 15 fps gegen
    real gelieferte ~8,3 fps = 81 % Ueberschaetzung — das Neubewertungs-
    Urteil kippte allein an dieser Eingangsgroesse): gezaehlte Bilder je
    Sekunde, seit dem Fix-Zyklus-Rest ueber ein GLEITENDES FENSTER
    (k.fps_fenster, Stuetzpunkte (mono, bilder) aus dem Status-Takt, Spanne
    FPS_FENSTER_S) statt "seit dem Verbinden" — der Verbindungs-Schnitt zog
    nach einer langen Stoerung noch Stunden nach der Erholung ein zu
    niedriges fps (gemessen 2,5 statt 15) und kippte die Neubewertung zu
    optimistisch (M-D Gegenrichtung). Fallback auf die Steckbrief-fps,
    solange das Fenster juenger als ein Neubewertungs-Takt (VERBRAUCH_S)
    ist oder noch nichts geliefert wurde — die Mindest-Beobachtungszeit ist
    zugleich der Schutz gegen die Division durch ~0. Modul-Funktion, damit
    der Mutations-Selbsttest sie fassen kann (Muster melde_erlaubt)."""
    fenster = getattr(k, "fps_fenster", None)
    if k.verbunden_mono is not None and fenster:
        alt_mono, alt_bilder = fenster[0]
        dauer = mono - alt_mono
        geliefert = k.bilder - alt_bilder
        if dauer >= VERBRAUCH_S and geliefert > 0:
            return geliefert / dauer
    return (k.steckbrief or {}).get("fps")


# ======================================================================
# UI-Zustand (Bauplan §2.3, Phase 2) + Store-Schreibwege (live_speichern)
# ======================================================================

def status_lesen(cfg, jetzt=time.time):
    """Engine-Quittung lesen: <data_dir>/state/live_status.json -> (dict|None,
    frisch). frisch = Herzschlag juenger als 3 Takte — dieselbe Schwelle wie
    livewached cmd_status (eine Frische-Wahrheit, K3)."""
    pfad = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                        "state", "live_status.json")
    try:
        with open(pfad) as f:
            d = json.load(f)
    except Exception:
        return None, False
    try:
        alter = jetzt() - float(d.get("ts") or 0)
    except (TypeError, ValueError):
        return d, False
    return d, alter <= 3 * HERZSCHLAG_S


def kommando_schreiben(cfg, aktion, kamera, **extra):
    """Dienst -> Engine: Auftrag (Quelltest `test` / Last-Messung `messung`)
    als atomare Kommando-Datei; die Engine liest sie im Status-Takt
    (_kommando_pruefen) und quittiert Fortschritt/Ergebnis im Status-JSON.
    -> ts des Kommandos (Eindeutigkeit; die Engine verarbeitet jedes ts
    genau einmal)."""
    pfad = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                        "state", "live_kommando.json")
    d = dict(extra, aktion=aktion, kamera=kamera, ts=round(time.time(), 3))
    _atomar_schreiben(pfad, d)
    return d["ts"]


def kommando_unverarbeitet(cfg, status):
    """Engine-M3 (stiller Kommando-Verlust, gemessen: zwei Klicks binnen eines
    Herzschlags — der zweite ueberschrieb den ersten SPURLOS): traegt die
    Kommando-Datei ein ts, das die Engine noch NICHT als verarbeitet quittiert
    hat (status.kommando_ts)? -> ts | None. Der Dienst weist einen weiteren
    Auftrag ab, solange hier ein ts haengt — ablehnen statt stumm
    ueberschreiben."""
    pfad = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                        "state", "live_kommando.json")
    try:
        with open(pfad) as f:
            ts = json.load(f).get("ts")
    except Exception:
        return None
    if ts is None or (status or {}).get("kommando_ts") == ts:
        return None
    return ts


# ------------------------------------------- Melde-Protokoll (Phase 4, Baustein B)
# Anlass (Sichtkontrolle .177, Befund 3): Live-Waechter-Pushes gingen real raus,
# tauchten aber in KEINEM Today-/System-Zaehler auf — der User bekam Meldungen,
# die die UI nicht kannte. EINE Quelle, kein Doppelzaehlen: die ENGINE schreibt
# je real rausgegangener Meldung genau eine Zeile in diese Datei (Schreiber),
# der DIENST liest und zeigt (melde_zaehler). Datei im data_dir — die Historie
# ueberlebt Dienst- UND Engine-Neustarts.
MELDE_PROTOKOLL = "meldungen.jsonl"


def melde_protokoll_zeile(live_dir, eintrag):
    """EINE Protokoll-Zeile anhaengen; rotiert am LOG_MAX_MB-Deckel (dieselbe
    eine Deckel-Quelle wie wache.log, K3). Wirft bei IO-Fehlern — der
    Engine-Aufrufer (_melde_protokoll) faengt und drosselt, eine Protokoll-
    Stoerung darf nie den Melde-Thread kosten."""
    os.makedirs(live_dir, exist_ok=True)
    pfad = os.path.join(live_dir, MELDE_PROTOKOLL)
    try:
        if os.path.getsize(pfad) > LOG_MAX_MB * 1024 * 1024:
            os.replace(pfad, pfad + ".1")
    except OSError:
        pass
    with open(pfad, "a") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
        f.flush()


def melde_protokoll_vorhanden(cfg):
    """Gibt es ueberhaupt Live-Melde-Historie? (Anzeige-Tor: ohne je eine
    Meldung und ohne Guards zeigt Today keine Dauer-0-Zeile.)"""
    live_dir = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                            "live")
    return any(os.path.exists(os.path.join(live_dir, MELDE_PROTOKOLL + s))
               for s in ("", ".1"))


def melde_liste(cfg, von, bis, kameras=None, max_gruppen=12):
    """Die Live-ALERTS eines Fensters ALS LISTE (.188, User 13.08.: Today
    soll separat zeigen, WAS live erkannt wurde — der Zaehler sagt nur wie
    viel). Ein Trigger meldet auf MEHREREN Kanaelen fast zeitgleich —
    Zeilen derselben Kamera binnen 2 s werden zu EINER Zeile gebuendelt
    (kanaele-Menge, erster zusatz gewinnt). -> (gruppen_neueste_zuerst
    gekappt auf max_gruppen, gesamtzahl_gruppen). Kaputte Zeilen fallen
    still raus (Anzeige-Pfad, wie melde_zaehler)."""
    live_dir = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                            "live")
    zeilen = []
    for endung in (".1", ""):
        try:
            f = open(os.path.join(live_dir, MELDE_PROTOKOLL + endung))
        except OSError:
            continue
        with f:
            for zeile in f:
                try:
                    d = json.loads(zeile)
                    ts = float(d["ts"])
                    if str(d["art"]) != "alert" or not von <= ts < bis:
                        continue
                    kamera = str(d.get("kamera") or "")
                    if kameras is not None and kamera not in kameras:
                        continue
                    zeilen.append((ts, kamera, str(d["kanal"]),
                                   str(d.get("zusatz") or ""),
                                   str(d.get("person") or ""),
                                   str(d.get("bild") or "")))
                except Exception:
                    continue
    zeilen.sort()
    gruppen = []
    for ts, kamera, kanal, zusatz, person, bild in zeilen:
        g = gruppen[-1] if gruppen else None
        if g and g["kamera"] == kamera and ts - g["ts_letzte"] <= 2.0:
            g["ts_letzte"] = ts
            if kanal not in g["kanaele"]:
                g["kanaele"].append(kanal)
            if zusatz and not g["zusatz"]:
                g["zusatz"] = zusatz
            if person and not g["person"]:
                g["person"] = person
            if bild and not g["bild"]:
                g["bild"] = bild
        else:
            gruppen.append({"ts": ts, "ts_letzte": ts, "kamera": kamera,
                            "kanaele": [kanal], "zusatz": zusatz,
                            "person": person, "bild": bild})
    gruppen.reverse()
    return gruppen[:max_gruppen], len(gruppen)


def auftritts_gruppen(gruppen, luecke=30.0):
    """Trigger-Gruppen (melde_liste, neueste zuerst) derselben Kamera binnen
    `luecke` Sekunden zu EINEM Auftritt buendeln (.195, User: die Live-Sicht
    soll den Auftritt zeigen wie die Pass-Ansicht, nicht Einzel-Trigger).
    Felder je Auftritt: ts/ts_letzte (Gesamtspanne), kamera, kanaele
    (Vereinigung), person/zusatz/bild (erster nicht-leerer gewinnt),
    trigger (Anzahl gebuendelter Gruppen). Reihenfolge bleibt neueste
    zuerst."""
    aus = []
    je_kamera = {}      # kamera -> juengste Auftritts-Karte: verschachtelte
    for g in sorted(gruppen, key=lambda g: g["ts"]):    # Kameras (K1-K2-K1,
        # der Normalfall eines Durchgangs) duerfen die Buendelung je Kamera
        # nicht zerreissen — nur der Zeitabstand JE KAMERA trennt (T23).
        a = je_kamera.get(g["kamera"])
        if a and g["ts"] - a["ts_letzte"] <= luecke:
            a["ts_letzte"] = max(a["ts_letzte"], g["ts_letzte"])
            a["trigger"] += 1
            for k in g["kanaele"]:
                if k not in a["kanaele"]:
                    a["kanaele"].append(k)
            # .313: Name und Bild kommen aus DERSELBEN Meldung — vorher
            # 'erster nicht-leerer gewinnt' je Feld, die Karte zeigte den Namen
            # der einen und das Bild einer anderen Meldung (bis 30 s auseinander,
            # Tester-Fund: 'Carl' auf leerem Garten).
            if g.get("person") and not a.get("person"):
                a["person"] = g["person"]
                if g.get("zusatz"):
                    a["zusatz"] = g["zusatz"]
                if g.get("bild"):
                    a["bild"] = g["bild"]
            elif not a.get("person"):
                for feld in ("zusatz", "bild"):
                    if g.get(feld) and not a.get(feld):
                        a[feld] = g[feld]
        else:
            neu = {"ts": g["ts"], "ts_letzte": g["ts_letzte"],
                   "kamera": g["kamera"], "kanaele": list(g["kanaele"]),
                   "person": g.get("person") or "",
                   "zusatz": g.get("zusatz") or "",
                   "bild": g.get("bild") or "", "trigger": 1}
            aus.append(neu)
            je_kamera[g["kamera"]] = neu
    aus.reverse()
    return aus


def auftritt_medien(cfg, kamera, von, bis, rand=6.0):
    """Alle gespeicherten Beweis-Medien eines Auftritts von der Platte
    (.195): Ketten-Crops, Namens-Bilder UND die Rueckblick-Videos aus
    <data_dir>/live/<kamera>/. Zuordnung ueber den Dateinamens-Stempel
    (Wanduhr des Ausloesers) im Fenster [von-rand, bis+rand] — bewusst von
    der Platte statt aus dem Protokoll, weil Karenz-Trigger Bilder
    schreiben, aber KEINE Meldezeile haben. verworfen_-Dateien (Pose-Sieb)
    bleiben draussen. -> (bilder_rel, videos_rel), chronologisch, jeder
    Pfad genuegt ALARMBILD_RE (Vertrag des /live_alarmbild-Endpunkts)."""
    ordner = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                          "live", kamera)
    bilder, videos = [], []
    try:
        dateien = sorted(os.listdir(ordner))
    except OSError:
        return bilder, videos
    for d in dateien:
        if d.startswith("verworfen"):
            continue
        try:
            t = time.mktime(time.strptime(d[:15], "%Y%m%d_%H%M%S"))
        except ValueError:
            continue
        if not (von - rand <= t <= bis + rand):
            continue
        rel = f"live/{kamera}/{d}"
        if not ALARMBILD_RE.match(rel):
            continue
        (videos if d.endswith(".mp4") else bilder).append(rel)
    return bilder, videos


def melde_zaehler(cfg, von, bis, kameras=None):
    """{(art, kanal): n} der REAL rausgegangenen Live-Meldungen mit
    von <= ts < bis. art: 'alert' (Personen-Meldung) | 'stoerung'
    (Stoerung/Entwarnung). Liest Datei + Rotations-Vorgaenger (.1); kaputte
    Zeilen fallen still raus (Anzeige-Pfad, nie ein Fehler im Request).
    kameras: optionale Kamera-Sicht (Areas) — Zeilen ohne Kamera (globale
    Engine-Stoerungen) zaehlen immer."""
    live_dir = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                            "live")
    aus = {}
    for endung in (".1", ""):
        try:
            f = open(os.path.join(live_dir, MELDE_PROTOKOLL + endung))
        except OSError:
            continue
        with f:
            for zeile in f:
                try:
                    d = json.loads(zeile)
                    ts = float(d["ts"])
                    art, kanal = str(d["art"]), str(d["kanal"])
                    kamera = str(d.get("kamera") or "")
                except Exception:
                    continue
                if not von <= ts < bis:
                    continue
                if kameras is not None and kamera and kamera not in kameras:
                    continue
                aus[(art, kanal)] = aus.get((art, kanal), 0) + 1
    return aus


def engine_lebt(cfg):
    """Engine-M4-Zusatzwache: haelt ein Prozess das Engine-flock
    (state/live.lock)? -> bool. Die 6-s-Herzschlag-Frische allein entschied
    bisher den Weg Engine/Helfer — im gemessenen 7-s-Reload-Fenster startete
    der Helfer ein ZWEITES Modell auf derselben iGPU (Vier-Waechter-Tod-
    Konstellation). Das flock ist unabhaengig vom Herzschlag: gehalten =
    Engine-Prozess lebt (auch wenn ihr Status gerade alt ist)."""
    import fcntl
    pfad = os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                        "state", "live.lock")
    try:
        f = open(pfad, "a+")
    except OSError:
        return False
    try:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return True                          # Lock gehalten -> Engine lebt
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return False
    finally:
        f.close()


def status_fuer_ui(status, frisch):
    """UI-B2 (Frische-Tor, gemessen: toter Engine-Prozess -> Countdown und
    Zaehler froren als Dauer-Luege ein): ALLE anzeigbaren Status-Inhalte
    laufen durch DIESES eine Tor — ohne frischen Herzschlag gibt es keinen
    Auftrag, keine Auftrags-Ergebnisse und keine Kachel-Zaehler zu zeigen
    (die Zustands-Ableitung ui_zustand hat ihr eigenes frisch-Urteil).
    Die Slot-Neubewertungs-Texte sind seit .196 weg — mit ihnen die ganze
    Budget-Vorhersage (User: Messwerte entscheiden nicht).
    -> (auftrag|None, auftraege{}, kacheln{})."""
    if not frisch:
        return None, {}, {}
    st = status or {}
    return (st.get("auftrag"), st.get("auftraege") or {},
            st.get("kacheln") or {})


def quelle_vollstaendig(guard):
    """Bauplan §2.3 'unconfigured': keine Quelle gewaehlt / unvollstaendig.
    proxy/direct brauchen guard-seitig nichts (der Host kommt aus der
    Frigate-URL des Dienstes); 'url' braucht die Stream-Adresse."""
    if guard is None:
        return False
    q = str(guard.get("quelle") or "proxy")
    if q not in QUELLEN_ERLAUBT:
        return False
    return q != "url" or bool(str(guard.get("url") or "").strip())


def ui_zustand(guard, kachel_status, engine_frisch, gesperrt=False,
               watchdog_s=WATCHDOG_S, verweigert_grund="", sperr_grund=""):
    """DER Kachel-Zustand des Live-Reiters -> (zustand, detail); zustand ist
    IMMER ein Schluessel aus core.registry.LIVE_ZUSTAENDE (eine Quelle fuer
    Kachel-Farbe, Kachel-Text und /health).

    K1 in BEIDE Richtungen (Bauplan §2.3/§8, Rundenauftrag):
     * 'active' kommt NIE aus der Config allein — massgeblich ist die
       QUITTUNG der Engine (frischer Herzschlag UND Kachel 'aktiv' UND
       letztes Bild juenger als der Watchdog).
     * Ein Config-Wunsch (enabled=true), den die Engine (noch) nicht
       quittiert hat — Engine aus, Reload noch nicht durch, Slot/Riegel
       verweigert — zeigt 'disturbed' MIT dem ehrlichen Grund, nie gruen.

    Und in der GEGENRICHTUNG genauso (§8 'Config-Aenderung im Betrieb'):
    ein Disable/eine Quell-Aenderung im Store kippt die Kachel erst, wenn
    die Engine den Stopp quittiert hat — solange der Waechter laut Status
    noch laeuft, zeigt die Kachel die ENGINE-Wahrheit mit dem Zusatz, dass
    die Aenderung gespeichert ist und auf die Uebernahme wartet.

    guard: normalisierter Guard (guards_lesen) oder None (keine Config).
    kachel_status: der Kachel-Block aus live_status.json oder None.
    engine_frisch: Herzschlag juenger als 3 Takte (status_lesen).
    gesperrt: Variante ohne Live-Freigabe (cpu-only-Sperre, §11 Entscheid 3).
    verweigert_grund: Grund aus status.verweigert (Slot-/Riegel-Verweigerung).
    sperr_grund: die EHRLICHE Sperr-Ursache aus _live_gesperrt (UI-KANN 3,
    RECHECK 12.08.: live_lage und live_health ueberschrieben den Text, der
    /live_status-Payload behielt die CPU-only-Fehldiagnose — jetzt kommt der
    Grund an der EINEN Ableitungsstelle herein statt an zwei von drei
    Verbrauchern als Patch)."""
    if gesperrt:
        return "unsupported", (sperr_grund
                               or "Live watchers are not available on this "
                                  "build (CPU-only image)")
    laeuft = (engine_frisch and kachel_status is not None
              and kachel_status.get("zustand") != "gestoppt")
    if not quelle_vollstaendig(guard):
        if laeuft:
            return _engine_wahrheit(kachel_status, watchdog_s,
                                    "change saved — waiting for the engine "
                                    "to apply it")
        return "unconfigured", "no source configured yet"
    ok, grund = test_gueltig(guard)
    if not ok:
        if laeuft:
            return _engine_wahrheit(kachel_status, watchdog_s,
                                    "source changed — waiting for the engine "
                                    "to stop this watcher (test invalidated)")
        return "untested", grund
    if not guard.get("enabled"):
        if laeuft:
            return _engine_wahrheit(kachel_status, watchdog_s,
                                    "disable saved — waiting for the engine "
                                    "to confirm the stop")
        return "tested", ""
    if not engine_frisch:
        return "disturbed", ("enabled, but the live engine is not running "
                             "(no heartbeat)")
    if kachel_status is None or kachel_status.get("zustand") == "gestoppt":
        if verweigert_grund:
            return "disturbed", verweigert_grund
        return "disturbed", ("enabled, but the engine has not confirmed this "
                             "watcher yet")
    return _engine_wahrheit(kachel_status, watchdog_s, "")


def _engine_wahrheit(kachel_status, watchdog_s, zusatz):
    """Der quittierte Engine-Zustand einer laufenden Kachel -> (zustand,
    detail). 'active' NUR mit frischem Bild (Watchdog-Schwelle), sonst
    'disturbed' mit dem Engine-Grund — plus dem ehrlichen Uebergangs-Zusatz
    (z. B. 'disable saved — waiting for the engine')."""
    alter = kachel_status.get("letztes_bild_alter_s")
    if (kachel_status.get("zustand") == "aktiv"
            and alter is not None and float(alter) <= watchdog_s):
        return "active", zusatz
    detail = kachel_status.get("grund") or ""
    z = kachel_status.get("zustand") or "unknown"
    if alter is not None:
        detail = (detail + (" — " if detail else "")
                  + f"last frame {float(alter):.0f}s ago")
    text = f"engine state '{z}'" + (f": {detail}" if detail else "")
    if zusatz:
        text = zusatz + " — " + text
    return "disturbed", text


QUELLEN_ERLAUBT = ("proxy", "direct", "url")

# Import-Wache (Deckungs-Vertrag, Muster HERKUNFT-Bindung oben): jeder
# Zustand, den ui_zustand liefern kann, MUSS in der Registry-Enum stehen —
# ein Modul mit ungebundenem Zustand darf gar nicht erst laden. Der Harnisch
# haelt zusaetzlich alle realen Rueckgaben gegen die Enum (T10).
_UI_ZUSTAENDE_GENUTZT = ("unsupported", "unconfigured", "untested", "tested",
                         "active", "disturbed")
for _z in _UI_ZUSTAENDE_GENUTZT:
    if _z not in _reg.LIVE_ZUSTAENDE:
        raise ImportError(f"core/livewache: ui_zustand-Wert {_z!r} fehlt in "
                          f"core.registry.LIVE_ZUSTAENDE — Registry zuerst "
                          f"ergaenzen")


def _audit_zeile(cfg, eintrag):
    """Eine Zeile ins config_audit.jsonl (derselbe Griff wie notif_speichern)."""
    os.makedirs(os.path.join(cfg["data_dir"], "config"), exist_ok=True)
    with open(os.path.join(cfg["data_dir"], "config", "config_audit.jsonl"), "a") as f:
        f.write(json.dumps(dict(eintrag, ts=round(time.time(), 1)),
                           ensure_ascii=False) + "\n")
        f.flush()


STECKBRIEF_CACHE = "stream_steckbriefe.json"    # <data_dir>/state/… (Dienst-Probelauf)


def _steckbrief_cache_pfad(cfg):
    return os.path.join(cfg.get("data_dir") or os.path.join(WURZEL, "verify_data"),
                        "state", STECKBRIEF_CACHE)


def steckbriefe_lesen(cfg):
    """Gecachte Stream-Steckbriefe des Dienst-Probelaufs -> {kamera: {...}}.
    Fail-safe leer (kaputte/fehlende Datei toetet nie die Seite)."""
    try:
        with open(_steckbrief_cache_pfad(cfg)) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def steckbrief_schreiben(cfg, kamera, brief):
    """EINEN Steckbrief in den Cache mergen — tmp+os.replace, Flush je Kamera
    (Absturz-Regel lange Laeufe: jeder fertige Posten ist sofort sicher)."""
    pfad = _steckbrief_cache_pfad(cfg)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    d = steckbriefe_lesen(cfg)
    d[str(kamera)] = brief
    tmp = pfad + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, pfad)


def versteckt_lesen(cfg):
    """Versteck-Liste des Live-Reiters (User 13.08.: Kacheln ausblendbar,
    Ausgeblendete unten eingeklappt) -> [kamera, ...]. Fail-safe leer."""
    v = (cfg.get("live") or {}).get("versteckt")
    if not isinstance(v, list):
        return []
    return [x for x in v if isinstance(x, str) and x.strip()]


def live_verstecken(cfg, kamera, versteckt, *, store_pfad, store_laden,
                    store_schreiben, log):
    """Hide/Show EINER Kachel -> (ok, msg). Reine Anzeige-Praeferenz, kein
    Riegel (der Waechter-Betrieb haengt nicht daran; ein LAUFENDER Waechter
    bleibt in der Running-Gruppe sichtbar, egal was hier steht — Regel im
    Renderer routes/live.gruppen). Store-Muster wie live_schalter."""
    kamera = str(kamera or "").strip()
    if not kamera:
        return False, "camera name missing"
    store = store_laden(cfg)
    blk = store.setdefault("live", {})
    liste = blk.get("versteckt")
    liste = ([x for x in liste if isinstance(x, str)]
             if isinstance(liste, list) else [])
    if versteckt and kamera not in liste:
        liste.append(kamera)
    if not versteckt:
        liste = [x for x in liste if x != kamera]
    blk["versteckt"] = liste
    store_schreiben(store_pfad(cfg), store)
    cfg["live"] = store["live"]                  # Prozess-Sicht sofort aktuell
    _audit_zeile(cfg, {"live_versteckt": {kamera: bool(versteckt)}})
    log(f"LIVE tile {kamera} {'hidden' if versteckt else 'shown'} via UI")
    return True, ("hidden" if versteckt else "shown")


def live_speichern(cfg, kamera, d, *, store_pfad, store_laden, store_schreiben,
                   log):
    """Detailseite 'Save' -> Guard-Block in den Config-Store. Muster
    core/melden.notif_speichern: der Dienst injiziert seine EINEN Store-IO-
    Wege (atomar + fsync unter _cfg_lock); dieselbe ehrliche Grenze wie dort
    (Read-Modify-Write ohne umgreifendes Lock — letzter Schreiber gewinnt).
    -> (ok, msg).

    ANDERS als notif_speichern: KEIN Dienst-Neustart. Den live-Block liest
    nur die Engine, und die uebernimmt Store-Aenderungen selbst (Reload auf
    Store-Mtime, nur der betroffene Waechter, Bauplan §8) — der Dienst
    braucht dafuer nichts neu zu laden; cfg wird im Prozess mitgezogen.

    Serverseitige ABWEISUNG statt Klemmen (Bauplan §4 Plausibilitaets-
    Riegel): die Klemm-Toleranz von guards_lesen gilt dem Hand-Edit im
    Store, ein Formular bekommt den Fehler gesagt. Audit: URL maskiert."""
    kamera = str(kamera or "").strip()
    if not kamera:
        return False, "camera name missing"
    store = store_laden(cfg)
    blk = store.setdefault("live", {}).setdefault("guards", {})
    alt = dict(blk.get(kamera) or {})

    def _wert(feld, standard):
        # .197 Felder-Fix (Vorfall 13.08.: ein API-Save OHNE ein Feld kippte
        # den Schnell-Urteil-Schalter still auf Default — Namens-Stufe war
        # unbemerkt aus): ein FEHLENDES Feld heisst BEHALTEN, nur ein
        # mitgesandtes Feld aendert. Dieselbe Halte-Logik, die die URL-
        # Maskierung (C4) fuer url schon immer hatte.
        return d[feld] if feld in d else alt.get(feld, standard)

    q = str(_wert("quelle", "proxy") or "proxy")
    if q not in QUELLEN_ERLAUBT:
        return False, f"'source': allowed {', '.join(QUELLEN_ERLAUBT)}"
    url = str(_wert("url", "") or "").strip()
    # C4 (User-Auflage, Muster Notifications-Secrets): das Formular ist mit
    # der MASKIERTEN URL vorbelegt (Credentials nie im HTML). Kommt die
    # Maskierung unveraendert zurueck, will der User die gespeicherte URL
    # BEHALTEN — nur eine WIRKLICH geaenderte Eingabe schreibt neu. Der
    # Fingerprint bleibt damit stabil (kein falscher Test-Verfall).
    alt_url = str(alt.get("url") or "")
    if url and alt_url and url != alt_url and url == quelle_maskiert(alt_url):
        url = alt_url
    if q == "url" and not url:
        return False, "source 'url' selected but no stream URL given"
    if url and "://" not in url:
        return False, "stream URL must be a full URL (e.g. rtsp://...)"
    try:
        ende_s = int(_wert("ende_ohne_gesicht_s", ENDE_OHNE_GESICHT_S))
        scharf_s = int(_wert("wieder_scharf_s", WIEDER_SCHARF_S))
    except (TypeError, ValueError):
        return False, "the two times must be whole seconds"
    if not (ENDE_OHNE_GESICHT_MIN <= ende_s <= ENDE_OHNE_GESICHT_MAX):
        return False, (f"'end after no face': allowed "
                       f"{ENDE_OHNE_GESICHT_MIN}-{ENDE_OHNE_GESICHT_MAX} s")
    if not (WIEDER_SCHARF_MIN <= scharf_s <= WIEDER_SCHARF_MAX):
        return False, (f"'re-armed after': allowed "
                       f"{WIEDER_SCHARF_MIN}-{WIEDER_SCHARF_MAX} s "
                       f"(0 = every trigger alerts)")
    kanaele = list(_wert("kanaele", []) or [])
    for kk in kanaele:
        if kk not in KANAELE_ERLAUBT:
            return False, (f"unknown channel {kk!r} "
                           f"(allowed: {', '.join(KANAELE_ERLAUBT)})")
    hoehe = _wert("hoehe", None)
    if hoehe not in (None, ""):
        try:
            hoehe = int(hoehe)
        except (TypeError, ValueError):
            hoehe = -1
        if hoehe not in HOEHEN_ERLAUBT:
            return False, (f"'resolution': allowed "
                           f"{', '.join(str(h) for h in HOEHEN_ERLAUBT)}")
    else:
        hoehe = None
    neu = dict(alt, quelle=q, url=url, ende_ohne_gesicht_s=ende_s,
               wieder_scharf_s=scharf_s, kanaele=kanaele, hoehe=hoehe)
    neu.pop("schnell_urteil", None)   # .197: Haken abgeschafft (Voting immer)
    blk[kamera] = neu
    store_schreiben(store_pfad(cfg), store)
    cfg["live"] = store["live"]                  # Prozess-Sicht sofort aktuell
    _audit_zeile(cfg, {"live": {kamera: {
        "quelle": q, "url": quelle_maskiert(url) if url else "",
        "ende_ohne_gesicht_s": ende_s, "wieder_scharf_s": scharf_s,
        "kanaele": kanaele, "hoehe": hoehe}}})
    log(f"LIVE guard {kamera} changed via UI (URL masked)")
    hinweis = ""
    alt_fp = (alt.get("test") or {}).get("quelle_fp")
    if alt_fp and alt_fp != quelle_fp(neu):
        hinweis = (" — source changed: the previous test is no longer valid, "
                   "run the source test again before enabling")
        if alt.get("enabled"):
            hinweis += " (a running watcher stops for this reason)"
    return True, "saved" + hinweis


def live_schalter(cfg, kamera, enabled, *, store_pfad, store_laden,
                  store_schreiben, log):
    """Enable/Disable EINES Waechters — der Enable-Riegel SERVERSEITIG
    (Bauplan §2.4: nicht nur UI-Grau; ein direkter POST kommt hier genauso
    vorbei): Enable nur mit gruenem Quelltest fuer GENAU diese Quell-
    Konfiguration (test_gueltig, Fingerprint-Vergleich). -> (ok, msg).
    Die Engine uebernimmt den Schalter selbst (Store-Reload); die Kachel
    zeigt den neuen Zustand erst mit der Engine-QUITTUNG (K1).

    HARTER AKTIVIER-RIEGEL (User 12.08. mittags, ERSETZT das Verweigert-
    Modell im Normalweg): es koennen nur so viele Waechter AKTIVIERT werden,
    wie die gemessene Kapazitaet hergibt (slots.effektiv_max aus der
    Selbstvermessung/greedy-Rechnung der laufenden Engine) — das Enable
    darueber hinaus wird HIER abgewiesen, mit Zahl. Kein 'enabled aber
    wartend' im Normalweg mehr; der Verweigert-Zustand bleibt NUR als
    Randfall (Engine-Neustart misst weniger, als der Store an enabled
    traegt — dann ehrliche Kachel). Laeuft die Engine nicht (kein frischer
    Herzschlag), gibt es keine Kapazitaets-Wahrheit — dann gilt der
    Randfall-Weg beim naechsten Engine-Start."""
    kamera = str(kamera or "").strip()
    store = store_laden(cfg)
    guard = ((store.get("live") or {}).get("guards") or {}).get(kamera)
    if not isinstance(guard, dict):
        return False, f"no live configuration saved for {kamera!r} yet"
    if enabled:
        ok, grund = test_gueltig(guard)
        if not ok:
            return False, f"enable refused: {grund}"
        if not guard.get("enabled"):
            status, frisch = status_lesen(cfg)
            slots = (status or {}).get("slots") or {}
            emax = slots.get("effektiv_max")
            if frisch and emax is not None:
                # UI-KANN 5 (RECHECK 12.08.): ein unbrauchbarer Wert (Hand-
                # Edit/Fremdschreiber im Status) darf NIE die HTTP-Antwort
                # verschlucken — Riegel LAUT aussetzen, es gilt der Randfall-
                # Weg (Engine verweigert dann selbst mit ehrlicher Kachel).
                try:
                    emax_i = int(emax)
                except (TypeError, ValueError):
                    emax_i = None
                    log(f"!! live_schalter: slots.effektiv_max unbrauchbar "
                        f"({emax!r}) — Kapazitaets-Riegel uebersprungen, "
                        f"Randfall-Weg gilt")
                blk = (store.get("live") or {}).get("guards") or {}
                an = sum(1 for g_ in blk.values()
                         if isinstance(g_, dict) and g_.get("enabled"))
                if emax_i is not None and an + 1 > emax_i:
                    msg = (f"enable refused: your GPU can run up to "
                           f"{emax_i} watcher(s) with the current "
                           f"measurements ({an} already enabled)")
                    # UI-KANN 6: bei Kapazitaet 0 gibt es nichts zu
                    # disablen — stattdessen den gemessenen Grund nennen.
                    if emax_i > 0:
                        msg += " — disable one first"
                    elif slots.get("effektiv_grund"):
                        msg += f" — {slots.get('effektiv_grund')}"
                    return False, msg
    guard["enabled"] = bool(enabled)
    store_schreiben(store_pfad(cfg), store)
    cfg["live"] = store["live"]
    _audit_zeile(cfg, {"live": {kamera: {"enabled": bool(enabled)}}})
    log(f"LIVE guard {kamera} {'enabled' if enabled else 'disabled'} via UI")
    if enabled:
        return True, ("enabled — the engine picks this up within a few "
                      "seconds; the tile turns green only once the engine "
                      "confirms frames are flowing")
    return True, ("disabled — the engine stops this watcher within a few "
                  "seconds")


# Deckungs-Vertrag (M-B Fix-Zyklus 12.08.; QS-Ebenen-Regel "Aufzaehlungen nie
# als Streu-Literal"): die Menge der NICHT-wachenden Verben des Prototyp-
# Dispatches. QUELLE ist prototyp/live_wache.py (NICHT_WACHEN_VERBEN dort, am
# __main__-Block) — der Harnisch (tools/harnisch_live1.py, t_verb_vertrag)
# haelt beide Mengen UND den Dispatch-Text gegeneinander. Im Dispatch gilt:
# JEDES andere Verb (auch Tippfehler wie 'wachn', '--help', 'test') faellt
# ins else und startet wachen(); OHNE Argument gilt 'messen' (kein Waechter).
PROTOTYP_NICHT_WACHEN_VERBEN = (b"messen", b"auswerten", b"gate", b"probe")


def ist_prototyp_waechter(cmdline):
    """Ist diese /proc-cmdline ein laufender Prototyp-WAECHTER? -> bool.

    M-B (Betrieb-R2), zwei gemessene Fehlklassen:
     * UEBER-warnen (Erstbefund): der Koeder 'tail -f prototyp/live_wache.py'
       erzeugte FUENF falsche Warnzeilen — Editor, grep, tail und Shell-
       Huellen tragen den Dateinamen genauso in der cmdline. Darum zaehlen
       nur python-Prozesse (argv[0]) mit dem Dateinamen als eigenem Element.
     * UNTER-warnen (Widerleger 12.08., gemessen: 5 von 10 realen Start-
       formen unsichtbar): der Prototyp-Dispatch startet wachen() fuer
       JEDES Verb ausser messen/auswerten/gate/probe — auch 'test',
       Tippfehler wie 'wachn' und '--help'. Eine Weissliste auf 'wachen'
       war deshalb blind. Jetzt SCHWARZLISTE (PROTOTYP_NICHT_WACHEN_VERBEN,
       Deckungs-Vertrag s. o.): Waechter ist, wessen erstes Argument NACH
       dem Skript-Element NICHT in der Menge liegt. KEIN Argument heisst im
       Dispatch 'messen', also kein Waechter. Das Verb wird nie an fester
       argv-Position gesucht (G3-Klasse: 'python -u live_wache.py wachen 0'
       traegt es an Position 3).
     * `-m`-STARTFORM (KANN-Rest des Fix-Zyklus 12.08., dort belegt lauffaehig
       und unsichtbar): `python -m prototyp.live_wache wachen 0` traegt KEINEN
       Dateinamen in argv — das Modul-Element steht als eigenes Element hinter
       einem `-m`-Flag. Erkannt werden die zwei sauberen Formen
       (`prototyp.live_wache` und `live_wache` bei cwd=prototyp/); die
       angeklebte Form `-mprototyp.live_wache` bleibt eine dokumentierte
       Luecke (keine reale Startform, Praezision vor Rate-Raten).
    cmdline: roher Inhalt von /proc/<pid>/cmdline (NUL-getrennt, bytes)."""
    argv = [a for a in cmdline.split(b"\0") if a]
    if not argv or b"python" not in argv[0]:
        return False
    skript = next((i for i, a in enumerate(argv) if b"live_wache.py" in a), None)
    if skript is None:
        skript = next((i + 1 for i, a in enumerate(argv[:-1])
                       if a == b"-m" and argv[i + 1] in (b"prototyp.live_wache",
                                                         b"live_wache")), None)
    if skript is None:
        return False
    verb = argv[skript + 1] if len(argv) > skript + 1 else b"messen"
    return verb not in PROTOTYP_NICHT_WACHEN_VERBEN


# ======================================================================
# Kachel + Engine
# ======================================================================

def _klemmen(wert, std, lo, hi, log, name, feld):
    try:
        w = int(wert if wert is not None else std)
    except Exception:
        log(f"live: {name}.{feld}={wert!r} ungueltig — Default {std}")
        return std
    if w < lo or w > hi:
        g = min(max(w, lo), hi)
        log(f"live: {name}.{feld}={w} ausserhalb {lo}-{hi} — geklemmt auf {g}")
        return g
    return w


def _bool_lesen(wert, std, log, feld):
    """Bool-Riegel (Lens-B M2: `pose_gate: "false"` wurde per bool("false")
    still zu True — der User schaltete AUS und bekam AN). Nur eindeutige
    Schreibweisen zaehlen, alles andere ist LAUT + Default."""
    if isinstance(wert, bool):
        return wert
    w = str(wert).strip().lower()
    if w in ("1", "true", "ja", "on", "yes"):
        return True
    if w in ("0", "false", "nein", "off", "no", ""):
        return False
    log(f"live: {feld}={wert!r} ungueltig (bool erwartet) — Default {std}")
    return std


def _zahl_lesen(wert, std, lo, hi, log, feld):
    """Zahlen-Riegel fuer den defaults-Block (Lens-B M2: `rate: "schnell"` war
    ein Traceback bis in cmd_run — Hand-Edit darf klemmen, nie crashen)."""
    try:
        w = type(std)(wert)
    except (TypeError, ValueError):
        log(f"live: {feld}={wert!r} ungueltig — Default {std}")
        return std
    if w < lo or w > hi:
        g = min(max(w, lo), hi)
        log(f"live: {feld}={w} ausserhalb {lo}-{hi} — geklemmt auf {g}")
        return g
    return w


# Wertebereiche des defaults-Blocks (Riegel, nicht Empfehlung): weit genug fuer
# jedes sinnvolle Rezept, eng genug gegen Tippfehler-Extreme.
_DEFAULTS_GRENZEN = {"hoehe": (2, 4320), "det_basis": (32, 4096),
                     "min_score": (0.0, 1.0), "pose_kopf": (0.0, 2.0),
                     "burst_anzahl": (2, 30), "burst_fenster_s": (0.2, 30.0),
                     "rate": (1, 60)}
KANAELE_ERLAUBT = ("pushover", "telegram", "mqtt")

# DECKUNGS-VERTRAG Guard-Felder (UI-B1, Fix-Zyklus 12.08. — gemessen: die
# Streu-Feldliste in guards_lesen liess `messung` FALLEN, die Last-Messung
# wurde deshalb NIE angezeigt). DIE eine Quelle fuer die Struktur eines
# Guard-Blocks im Config-Store: wer ein Feld schreibt (live_speichern,
# live_schalter, live_quittungen_uebernehmen des Dienstes), traegt es HIER
# ein; guards_lesen normalisiert GENAU diese Menge und meldet fremde Felder
# laut. Der Harnisch haelt den Vertrag: jedes Feld muss die Normalisierung
# ueberleben (tools/harnisch_live1.py, Render-/Vertrags-Block).
GUARD_USER_FELDER = ("enabled", "quelle", "url", "ende_ohne_gesicht_s",
                     "wieder_scharf_s", "kanaele", "hoehe")
# .197: "schnell_urteil" ist KEIN Guard-Feld mehr — die Namens-Stufe laeuft
# fuer jeden eingeschalteten Waechter (User: "Enable heisst alles laeuft";
# der Haken stammte aus der Zeit, als das Urteil extra Rechenzeit kostete).
# Alte Stores mit dem Feld sind gueltig: guards_lesen ignoriert es still,
# der naechste Save raeumt es weg.
GUARD_QUITTUNG_FELDER = ("test", "test_fehler", "messung")
GUARD_FELDER = GUARD_USER_FELDER + GUARD_QUITTUNG_FELDER


def _hoehe_lesen(wert, log, name):
    """Je-Kachel-Verarbeitungshoehe (.194): nur HOEHEN_ERLAUBT; None =
    NICHT gesetzt (dann gilt die Default-Kette live.defaults.hoehe ->
    WACH_HOEHE beim Verbraucher). Ungueltiges faellt LAUT auf None — nie
    klemmen (eine krumme Hoehe waere ein stilles anderes Rechenverhalten,
    keine Naeherung)."""
    if wert in (None, ""):
        return None
    try:
        h = int(wert)
    except (TypeError, ValueError):
        h = None
    if h in HOEHEN_ERLAUBT:
        return h
    log(f"live.guards.{name}.hoehe: {wert!r} unbekannt — Default gilt")
    return None


def guards_lesen(cfg, log=print):
    """Config-Store-Block `live` -> (defaults, guards). Bauplan §3: Defaults
    sind die GEMESSENEN Werte (hier die Modul-Literale), der Store ueberlagert;
    ein Guard traegt nur die echten User-Entscheide.

    FAIL-SAFE + LAUT (Lens-B M2/M3, Phase 1 ist ausdruecklich hand-editiert):
    kein Hand-Edit darf hier crashen oder still kippen — ungueltige Werte
    werden geklemmt/verworfen und JEDER Eingriff wird geloggt. Ein Waechter,
    dessen Kanalliste nach dem Sieb LEER ist, wird ausdruecklich benannt
    (er wuerde sonst still nirgendwo melden — die Fehlklasse im Reinformat)."""
    live = cfg.get("live") or {}
    if not isinstance(live, dict):
        log(f"live: Config-Block ist kein Objekt ({type(live).__name__}) — "
            f"ignoriert, Defaults gelten, keine Waechter")
        live = {}
    d = {"hoehe": WACH_HOEHE, "det_basis": DET_BASIS, "min_score": MIN_SCORE,
         "pose_gate": True, "pose_kopf": POSE_KOPF, "burst_anzahl": BURST_ANZAHL,
         "burst_fenster_s": BURST_FENSTER, "rate": PRUEF_RATE}
    roh_defaults = live.get("defaults") or {}
    if not isinstance(roh_defaults, dict):
        log("live.defaults: kein Objekt — ignoriert")
        roh_defaults = {}
    for k, v in roh_defaults.items():
        if k not in d:
            log(f"live.defaults: unbekannter Schluessel {k!r} — ignoriert")
            continue
        if isinstance(d[k], bool):
            d[k] = _bool_lesen(v, d[k], log, f"live.defaults.{k}")
        else:
            lo, hi = _DEFAULTS_GRENZEN[k]
            d[k] = _zahl_lesen(v, d[k], lo, hi, log, f"live.defaults.{k}")
    guards = {}
    roh_guards = live.get("guards") or {}
    if not isinstance(roh_guards, dict):
        log(f"live.guards: kein Objekt ({type(roh_guards).__name__}) — "
            f"ignoriert, keine Waechter")
        roh_guards = {}
    for name, g in roh_guards.items():
        if not isinstance(g, dict):
            log(f"live.guards.{name}: kein Objekt — ignoriert")
            continue
        roh_kanaele = g.get("kanaele")
        if roh_kanaele is None:
            # .200 (Fix 3, Usersicht-Review): Default = die REAL konfigurierten
            # Kanaele (EINE Quelle: melden.konfigurierte_kanaele) statt hart
            # ['pushover']. Der harte Default baute Waechter, die ausloesen und
            # nirgendwo melden, wenn Pushover nie eingerichtet war. Bewusst zur
            # LESE-Zeit ausgewertet: richtet der Nutzer spaeter einen Kanal ein,
            # meldet ein Default-Waechter ab dann von selbst dorthin.
            from core import melden as _melden
            roh_kanaele = _melden.konfigurierte_kanaele(cfg)
            if not roh_kanaele:
                log(f"!! live.guards.{name}: kein Meldekanal konfiguriert — der "
                    f"Waechter triggert und erscheint unter Live alerts (.245), "
                    f"aber es geht KEINE Benachrichtigung raus "
                    f"(Notifications-Seite)")
        if isinstance(roh_kanaele, str):
            # YAML-/Hand-Edit-Klassiker: String statt Liste — tolerant lesen, laut.
            log(f"live.guards.{name}.kanaele ist ein String ({roh_kanaele!r}) — "
                f"als Ein-Element-Liste gelesen")
            roh_kanaele = [roh_kanaele]
        kanaele = []
        for kk in roh_kanaele:
            if kk in KANAELE_ERLAUBT:
                kanaele.append(kk)
            else:
                log(f"live.guards.{name}.kanaele: unbekannter Kanal {kk!r} "
                    f"verworfen (erlaubt: {', '.join(KANAELE_ERLAUBT)})")
        if not kanaele and roh_kanaele:
            log(f"!! live.guards.{name}: nach dem Kanal-Sieb ist KEIN Meldekanal "
                f"uebrig — der Waechter triggert und erscheint unter Live alerts "
                f"(.245), aber es geht KEINE Benachrichtigung raus")
        guards[name] = {
            "enabled": _bool_lesen(g.get("enabled"), False, log,
                                   f"live.guards.{name}.enabled"),
            "quelle": str(g.get("quelle") or "proxy"),
            "url": str(g.get("url") or ""),
            "ende_ohne_gesicht_s": _klemmen(g.get("ende_ohne_gesicht_s"),
                                            ENDE_OHNE_GESICHT_S, ENDE_OHNE_GESICHT_MIN,
                                            ENDE_OHNE_GESICHT_MAX, log, name,
                                            "ende_ohne_gesicht_s"),
            "wieder_scharf_s": _klemmen(g.get("wieder_scharf_s"), WIEDER_SCHARF_S,
                                        WIEDER_SCHARF_MIN, WIEDER_SCHARF_MAX,
                                        log, name, "wieder_scharf_s"),
            "kanaele": kanaele,
            "hoehe": _hoehe_lesen(g.get("hoehe"), log, name),
        }
        # Quittungs-Bloecke (GUARD_QUITTUNG_FELDER) unveraendert durchreichen —
        # UI-B1: `messung` fehlte hier und die Last-Messung war unsichtbar.
        # Der Deckungs-Vertrag GUARD_FELDER ist die eine Quelle, nie wieder
        # eine Streu-Liste; fremde Felder (Hand-Edit/Tippfehler) LAUT melden.
        for feld in GUARD_QUITTUNG_FELDER:
            w = g.get(feld)
            guards[name][feld] = dict(w) if isinstance(w, dict) else {}
        for fremd in sorted(set(g) - set(GUARD_FELDER)):
            log(f"live.guards.{name}: unbekanntes Feld {fremd!r} — ignoriert "
                f"(Vertrag GUARD_FELDER)")
    return d, guards


def _atomar_schreiben(pfad, daten):
    """Status-Datei atomar (tmp + fsync + os.replace) — der _store_schreiben-
    Griff, hier ohne verifyd-Import nachgezogen (Injektionsreinheit)."""
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    tmp = f"{pfad}.tmp-{os.getpid()}"
    try:
        with open(tmp, "w") as f:
            json.dump(daten, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, pfad)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


class Kachel:
    """Der autarke Zustand EINES Waechters (Alarm-Logik je Kamera)."""

    def __init__(self, name, guard, defaults):
        self.name = name
        self.cfg = guard
        self.zustand = "startet"                 # aus KACHEL_ZUSTAENDE
        self.zustand_grund = ""
        self.stop_ev = threading.Event()         # Einzel-Stopp (Reload je Waechter,
        #                                          Bauplan §8; stop() setzt alle)
        self.thread = None                       # der Leser-Thread dieser Kachel
        self.pausiert = 0                        # Bilder, die eine laufende Messung
        #                                          still stellte (ehrlich gezaehlt)
        self.eingereiht = 0                      # vom Leser eingereihte Bilder
        self.verarbeitungs_fehler = 0            # B4: IO-/Befund-Fehler (nie Engine-Ende)
        self.lock = threading.Lock()             # Burstwache + Episode + Rueckblick
        self.burst = Burstwache(rate=defaults["rate"], anzahl=defaults["burst_anzahl"],
                                fenster=defaults["burst_fenster_s"])
        self.netz = None
        self.steckbrief = {}
        self.hw = None
        self.kill = None                         # kill-Callable des laufenden Lesers
        self.stoer = Stoerungsmelder()
        self.rueckblick = collections.deque(maxlen=max(4, int(VIDEO_SEK * 4)))
        # Zaehler (Status/Log)
        self.bilder = 0
        self.geprueft = 0                        # WIRKLICH detektierte Bilder (Lens-A M2)
        self.funde = 0
        self.gemeldet = 0
        self.verworfen_pose = 0
        self.gedrosselt = 0
        self.watchdog_kills = 0
        self.abrisse = 0
        self.reconnect_fehler = 0
        self.normal_zaehler = 0
        # Zeiten (monoton fuer Fristen, Wanduhr nur Anzeige)
        self.letztes_bild_mono = None
        self.letztes_bild_wand = None
        self.letzter_trigger_wand = None
        self.verbunden_mono = None
        self.verbunden_bilder = 0                # k.bilder-Stand beim Verbinden (M-D)
        self.vorschau_mono = 0.0                 # letzter Vorschau-JPEG-Schrieb (Drossel)
        self.fps_fenster = collections.deque()   # (mono, bilder)-Stuetzpunkte des
        #                                          Status-Takts — gleitende Liefer-fps
        #                                          (aktiv_fps, Spanne FPS_FENSTER_S)
        self.melde_bis_mono = -1e18
        # K-3 (Sched-R3): Mindestabstand der Stoerungs-/Entwarnungs-Pushes je
        # Kachel — eine Sporadik-Kamera (1 Bild je 400 s) erzeugte gemessen
        # 18 Pushes/h. Zurueckgehaltenes wird gezaehlt und zusammengefasst
        # nachgereicht (_stoerung_senden + Flush in _status_runde).
        self.stoer_sende_mono = -1e18            # letzter WIRKLICH gesendeter Push
        self.stoer_unterdrueckt = 0              # seither zurueckgehaltene Ereignisse
        self.stoer_letzter_text = None           # juengstes zurueckgehaltenes Ereignis
        # Auftritt (User-Zeit a, Anker LETZTER Fund — neu gebaut, Bauplan §4a)
        self.auftritt = None                     # {"seit_mono","letzter_fund_mono","funde","trigger"}
        self.auftritte = 0


class Melder:
    """Die ECHTEN Meldewege ueber core/melden (R3-Andock-API) — je Engine EIN
    Objekt. Kanalausfall ist nie Waechterausfall: jeder Weg faengt selbst,
    der Aufrufer drosselt die Fehlerzeilen. Der Harnisch stubbt diese Klasse.

    Waechter-Kennung im Titel (Invariante §6): EIN Literal WATCHER_TITEL fuer
    Pushover-Titel UND Telegram-Caption, damit die vorlaeufige Waechter-Meldung
    nie mit dem bestaetigten suslik-Urteil verwechselt wird. herkunft ist
    IMMER `live_wache` (core.registry.MELDE_HERKUNFT; MQTT-Feld traegt sie).

    SPRACH-STUFE 4: diese Klasse IST der Alert-Pfad des Live-Waechters —
    Eintrittspunkt (c) der Sprachaufloesung (konzept_sprache.md §2). Sie
    laeuft im eigenen livewached-Prozess UND in eigenen Melde-Threads (je
    Thread ein frischer contextvar-Kontext), deshalb aktiviert JEDE
    Melde-Methode selbst, unmittelbar vor dem Titel-Bau
    (`_sprache.aktivieren()` ist dieselbe Funktion wie
    `melden.sprache_aktivieren()`, dort steht ihre Begruendung)."""

    def __init__(self, cfg, log=print, pub=None):
        self.cfg = cfg
        self.log = log
        self.pub = pub                            # paho-Client des Startwegs (oder None)

    def push(self, kamera, text, bild=None):
        from core import melden
        _sprache.aktivieren()                     # Eintrittspunkt (c)
        return melden.push(self.cfg,
                           _sprache.t("meldung.wache.titel_person",
                                      wache=WATCHER_TITEL, kamera=kamera),
                           text, attachment=bild, herkunft=HERKUNFT)

    def telegram(self, kamera, video, text, bild=None):
        from core import melden
        _sprache.aktivieren()                     # Eintrittspunkt (c)
        return melden.telegram_video(self.cfg, video,
                                     _sprache.t("meldung.wache.caption",
                                                wache=WATCHER_TITEL,
                                                kamera=kamera, text=text),
                                     crop=bild, herkunft=HERKUNFT)

    def mqtt(self, kamera, payload):
        from core import melden
        t = melden.topic(self.cfg, f"live/{kamera}")
        # Retained: nein — ein Trigger ist ein Ereignis, kein Zustand (§6).
        return melden.mqtt_pub(self.pub, self.log, t,
                               json.dumps(payload, ensure_ascii=False),
                               retain=False, herkunft=HERKUNFT)

    def stoerung_kachel(self, kamera, text, kanaele):
        """Stoerung/Entwarnung EINES Waechters ueber SEINE Kanaele (§11 E2).
        -> (gesendet, fehler): Kanaele, die die Meldung ANGENOMMEN haben
        (Baustein B: nur die landen im Melde-Protokoll/den Dienst-Zaehlern),
        und Fehlertexte. Der Engine-Aufrufer parst tolerant — Harnisch-Stubs
        mit blosser Fehlerliste bleiben gueltig.

        SPRACH-STUFE 4 — GRENZE, BEWUSST: nur der TITEL ist sprachfaehig.
        `text` ist die technische Stoerungs-Diagnose der Engine ("detector
        failure: …", "engine state 'x': …"), die wortgleich auch ins Log
        geht — Log bleibt englisch/maschinenlesbar (§4 B20)."""
        from core import melden
        _sprache.aktivieren()                     # Eintrittspunkt (c)
        gesendet, fehler = [], []
        if "pushover" in kanaele:
            try:
                if melden.push(self.cfg,
                               _sprache.t("meldung.wache.titel_stoerung",
                                          wache=WATCHER_TITEL, kamera=kamera),
                               text, herkunft=HERKUNFT):
                    gesendet.append("pushover")
            except Exception as e:
                fehler.append(f"pushover: {e}")
        if "telegram" in kanaele:
            try:
                if melden.telegram_video(self.cfg, None,
                                         _sprache.t("meldung.wache.caption",
                                                    wache=WATCHER_TITEL,
                                                    kamera=kamera, text=text),
                                         herkunft=HERKUNFT):
                    gesendet.append("telegram")
            except Exception as e:
                fehler.append(f"telegram: {e}")
        if "mqtt" in kanaele:
            try:
                if self.mqtt(kamera, {"ts": round(time.time(), 1),
                                      "kamera": kamera, "stoerung": text}):
                    gesendet.append("mqtt")
            except Exception as e:
                fehler.append(f"mqtt: {e}")
        return gesendet, fehler

    def stoerung_global(self, text):
        """Engine-weite Stoerung (Detektor tot o. ae.): beide Push-Kanaele
        (stoerung_melden-Bestand, P3.5) — MIT Herkunft (Lens-B M8: die
        Docstring-Zusage 'herkunft ist IMMER live_wache' galt sonst nicht
        fuer genau diese Meldung). -> (gesendet, fehler) wie stoerung_kachel
        (Baustein B; `bericht` liefert je Kanal die ehrliche Annahme)."""
        from core import melden
        bericht = []
        fehler = melden.stoerung_melden(self.cfg, text, herkunft=HERKUNFT,
                                        bericht=bericht)
        return [kanal for kanal, ok in bericht if ok], fehler


class _DetektorMitLock:
    """Huelle um den geteilten Detektor (Engine-M1): erkennen() laeuft NUR
    unter dem Engine-Detektor-Lock — auch der Quelltest-Pass ist damit gegen
    den Detektor-Thread serialisiert (zwei Threads auf einer Session = die
    CL_OUT_OF_RESOURCES-Klasse vom 11.08.)."""

    def __init__(self, det, lock):
        self.det = det
        self.lock = lock

    def erkennen(self, frame_bgr, netz):
        with self.lock:
            return self.det.erkennen(frame_bgr, netz)

    def provider(self):
        return self.det.provider()


class Engine:
    """Die Live-Engine: N Kacheln, EIN Detektor-Kontext, EIN Status-Herzschlag.

    Injektion (Harnisch-Vertrag):
      detektor       .erkennen(frame_bgr, netz)->faces, .provider()->str
      detektor_fabrik optionaler Neubau nach hartem Detektor-Tod (CL_OUT_OF_
                      RESOURCES-Klasse, Realbeleg 11.08.)
      melder         Melder-artig (s. o.); der Harnisch zeichnet nur auf
      frames_fabrik  (kachel)->(frames_iter, kill, steckbrief_dict) — die echte
                     Fabrik verbindet ffmpeg, der Harnisch liefert Kunst-Takte
      kameras        Feed-Inventar (dict aus verifyd.frigate_cameras, injiziert)
      refs/win_thresh  Schnell-Urteil-Zutaten (None -> Schnell-Urteil aus)
      jetzt/wanduhr  Uhren (monoton fuer Fristen / Wanduhr fuer Anzeige)"""

    def __init__(self, cfg, log=print, *, detektor=None, detektor_fabrik=None,
                 melder=None, frames_fabrik=None, kameras=None,
                 refs=None, win_thresh=None,
                 jetzt=time.monotonic, wanduhr=time.time,
                 status_pfad=None, live_dir=None, lock_pfad=None,
                 scheduler=None, vermessung=None, watchdog_s=WATCHDOG_S,
                 neubau_warte_s=5.0,
                 config_quelle=None, store_pfad=None,
                 quelltest_fn=None, mess_min_s=MESSUNG_MIN_S,
                 mess_max_s=MESSUNG_MAX_S, kommando_pfad=None):
        self.cfg = cfg
        self.log = log
        self.jetzt = jetzt
        self.wanduhr = wanduhr
        data_dir = cfg.get("data_dir") or os.path.join(WURZEL, "verify_data")
        self.status_pfad = status_pfad or os.path.join(data_dir, "state", "live_status.json")
        self.live_dir = live_dir or os.path.join(data_dir, "live")
        self.lock_pfad = lock_pfad or os.path.join(data_dir, "state", "live.lock")
        self.detektor = detektor
        self.detektor_fabrik = detektor_fabrik
        self.melder = melder
        self.frames_fabrik = frames_fabrik or self._echte_quelle
        self.kameras = kameras
        self.refs = refs or {}
        self.win_thresh = win_thresh
        self.watchdog_s = float(watchdog_s)
        self.neubau_warte_s = float(neubau_warte_s)
        self.scheduler = scheduler or Scheduler(jetzt=jetzt)
        self.vermessung = vermessung or Selbstvermessung()
        self.defaults, self.guards = guards_lesen(cfg, log)
        self.kacheln = {}
        self.verweigert = {}          # name -> grund (Slot-/Riegel-Verweigerung)
        self.stop_ev = threading.Event()
        self.threads = []
        self.engine_fehler = ""
        self._lock_handle = None
        self._fehler_drossel = {}     # (quelle) -> letzter Log mono
        self._stoer_global_mono = -1e18
        self._start_mono = None
        self._start_wand = None
        self._gestoppt = False        # stop()-Idempotenz UNABHAENGIG von stop_ev
        #                               (der Todespfad setzt stop_ev selbst — stop()
        #                               muss danach trotzdem joinen + final schreiben)
        self._melde_lock = threading.Lock()
        self._melde_threads = []      # Melde-/Stoerungs-Threads (M5: stop() joint sie)
        self._mess_start_mono = None  # offenes Ein-Stream-RSS-Messfenster
        # --- Phase 2: Store-Reload + Auftrags-Strecke (Quelltest/Last-Messung)
        self.config_quelle = config_quelle    # callable -> frische cfg (livewached)
        self.store_pfad = store_pfad          # Config-Store-Datei (Mtime-Wache)
        self._store_mtime = None
        self.quelltest_fn = quelltest_fn or quelle_testen
        self.mess_min_s = float(mess_min_s)
        self.mess_max_s = float(mess_max_s)
        self.kommando_pfad = kommando_pfad or os.path.join(
            data_dir, "state", "live_kommando.json")
        self._kommando_ts = None      # letztes verarbeitetes Kommando (ts)
        self._pause_ausser = None     # Kamera-Name: alle ANDEREN Leser stellen still
        self._auftrag = None          # laufender Auftrag (Phase/Frist) fuer den Status
        self._auftrag_lock = threading.Lock()
        self._auftrag_serie = 0       # Generations-Zaehler (B1: Zombie-finally
        #                               darf NIE den Nachfolger-Auftrag raeumen)
        self.auftrag_ergebnisse = {}  # kamera -> {"test": {...}, "messung": {...}}
        # DER Detektor-Mutex (Engine-M1, gemessen: das 0,5-s-Entwaessern liess
        # ab Rueckstand > 500 ms ZWEI Threads auf die eine Detektor-Session —
        # CL_OUT_OF_RESOURCES-Klasse). JEDE erkennen()-Benutzung (Detektor-
        # Thread, Mess-Thread, Quelltest) laeuft unter diesem Lock; das ist
        # auch die einzige Absicherung, die einen Not-Aus ueberlebt.
        self._det_lock = threading.Lock()

    # ---------------------------------------------------------------- Start/Stop
    def start(self):
        """Kacheln nach Riegel + Slot-Pruefung starten; Threads hochziehen.
        -> True, wenn die Engine laeuft (auch mit 0 Kacheln — Status lebt)."""
        if not self._flock_nehmen():
            self.log(f"live: another engine holds {self.lock_pfad} — refusing "
                     f"(zwei Engines = doppelte Meldungen, Bauplan §8)")
            return False
        self._start_mono = self.jetzt()
        self._start_wand = self.wanduhr()
        self._prototyp_warnung()
        self._feed_inventar()
        self.vermessung.grundkosten_messen()
        # Alt-Kommando aus einer frueheren Sitzung NICHT nachspielen (ein vor
        # Stunden geklickter Mess-Knopf darf beim Neustart nichts ausloesen).
        try:
            with open(self.kommando_pfad) as f:
                self._kommando_ts = json.load(f).get("ts")
        except Exception:
            pass
        if self.store_pfad:
            try:
                self._store_mtime = os.path.getmtime(self.store_pfad)
            except OSError:
                pass
        for name, guard in self.guards.items():
            if not guard["enabled"]:
                continue
            self._kachel_aufnehmen(name, guard, start_sofort=False)
        # Ein-Stream-RSS-Messung NUR beim Start mit genau EINER Kachel oeffnen
        # (Lens-A M9: VOR dem Stream, und nie mit Nachbar-Streams im Fenster).
        if len(self.kacheln) == 1:
            self.vermessung.stream_messung_start(0)
            self._mess_start_mono = self.jetzt()
        for ziel, nm in ((self._detektor_lauf, "live-detektor"),
                         (self._status_lauf, "live-status")):
            t = threading.Thread(target=ziel, name=nm, daemon=True)
            self.threads.append(t)
        for t in self.threads:
            t.start()
        self.log(f"live engine up: {len(self.kacheln)} watcher(s), "
                 f"{len(self.verweigert)} refused, heartbeat {HERZSCHLAG_S:g}s, "
                 f"watchdog {self.watchdog_s:g}s")
        return True

    def stop(self, grund="stop"):
        """Sauberes SIGTERM-Ende: Leser killen, Threads einsammeln (auch die
        Melde-Threads — Lens-A M5: eine angestossene Meldung darf beim Neustart
        nicht still verloren gehen), letzter Status-Schreib. Idempotent ueber
        _gestoppt, NICHT ueber stop_ev — den setzt auch der Todespfad, und
        danach muss stop() trotzdem noch joinen und den Status abschliessen."""
        if self._gestoppt:
            return
        self._gestoppt = True
        self.log(f"live engine stopping ({grund})")
        self.stop_ev.set()
        for k in list(self.kacheln.values()):
            k.stop_ev.set()
            if k.kill:
                try:
                    k.kill()
                except Exception:
                    pass
            k.zustand = "gestoppt"
        for t in list(self.threads):       # Kopie: Aufraeum-Threads (M4) entfernen parallel
            try:
                t.join(timeout=10)
            except RuntimeError:
                pass                       # Signal traf zwischen append und start (K11)
        with self._melde_lock:
            offene = list(self._melde_threads)
        for t in offene:
            try:
                t.join(timeout=10)
            except RuntimeError:
                pass
        try:
            self._status_schreiben(self.jetzt())
        except Exception:
            pass
        if self._lock_handle:
            try:
                self._lock_handle.close()
            except Exception:
                pass
        self.log("live engine stopped")

    def warten(self):
        """Blockiert bis stop() (Signal-Handler des Startwegs ruft stop())."""
        while not self.stop_ev.wait(1.0):
            pass

    def _flock_nehmen(self):
        """Exklusives flock auf state/live.lock (Muster anlernen.pool_lock) —
        gegen Doppelstart (Supervisor + Hand-Start, Bauplan §8)."""
        import fcntl
        try:
            os.makedirs(os.path.dirname(self.lock_pfad), exist_ok=True)
            # "a+" statt "w" (Lens K1/K3-Befund): "w" trunkiert VOR dem flock —
            # ein abgewiesener Zweitstart leerte die PID des Gewinners.
            f = open(self.lock_pfad, "a+")
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            f.seek(0)
            f.truncate()
            f.write(str(os.getpid()))
            f.flush()
            self._lock_handle = f
            return True
        except OSError:
            return False

    def _prototyp_warnung(self):
        """Bauplan §9: auf laufende Prototyp-Waechter pruefen und WARNEN —
        mehr nicht (kein fremdes Killen). Doppel-Push ist sonst bekannt.

        Lens-B M9 (real gemessen: 4 von 5 laufenden Waechtern unsichtbar,
        darunter der Realtest-Waechter des Orchestrator-Plans): wache.pid wird nur
        beim Start geschrieben, nie geraeumt, und ein spaeterer Lauf derselben
        Kamera ueberschreibt sie — PID-Dateien sind als Erkennungsweg
        unbrauchbar. Stattdessen /proc-Scan auf die cmdline: findet JEDEN
        laufenden Prototyp-WAECHTER, unabhaengig von PID-Dateien; das
        Praedikat (python + Dateiname + Verb-SCHWARZLISTE) steht in
        ist_prototyp_waechter (M-B: der blosse Dateinamen-Match hielt auch
        tail/grep/Editoren fuer Waechter; die 'wachen'-Weissliste uebersah
        umgekehrt 5 von 10 realen Startformen — Widerleger 12.08.).
        Die Kamera kommt, wo lesbar, aus LIVE_KAMERA im environ."""
        try:
            eigene = os.getpid()
            for eintrag in os.listdir("/proc"):
                if not eintrag.isdigit() or int(eintrag) == eigene:
                    continue
                try:
                    cmd = open(f"/proc/{eintrag}/cmdline", "rb").read()
                except OSError:
                    continue
                if not ist_prototyp_waechter(cmd):
                    continue
                kamera = ""
                try:
                    env = open(f"/proc/{eintrag}/environ", "rb").read()
                    for teil in env.split(b"\0"):
                        if teil.startswith(b"LIVE_KAMERA="):
                            kamera = teil.split(b"=", 1)[1].decode("utf-8", "replace")
                            break
                except OSError:
                    pass
                self.log(f"!! WARNING: prototype watcher RUNNING (pid {eintrag}"
                         + (f", {kamera}" if kamera else "")
                         + ") — double alerts possible until it is stopped "
                           "(no shared alert throttle between prototype and engine)")
        except OSError:
            self.log("!! prototype check unavailable (/proc not readable)")

    def _feed_inventar(self):
        """Feed-Inventar-Auflage (stand.md 11.08.): beim Start ein Inventar
        aller gefundenen Kameras/Feeds loggen — Name, Guard-Status, Detect-
        Aufloesung aus Frigate; die maskierte Quelle und die Verarbeitungs-
        Aufloesung folgen je Kachel in der WACHE-START-Zeile (erst nach dem
        Verbinden sind sie Messwerte statt Annahmen)."""
        if not self.kameras:
            self.log("live feed inventory: no Frigate camera list injected")
            return
        for name, info in sorted(self.kameras.items()):
            g = self.guards.get(name)
            zu = ("watcher enabled" if g and g["enabled"]
                  else ("configured, disabled" if g else "no watcher configured"))
            self.log(f"live feed: {name} detect {info.get('width')}x{info.get('height')}"
                     f" — {zu}")
        for name in self.guards:
            if name not in self.kameras:
                self.log(f"live feed: {name} — configured but NOT in Frigate "
                         f"(camera renamed/removed? guard kept, Bauplan §3)")

    # ------------------------------------------------- Kachel-Lebenszyklus (Reload)
    def _kachel_aufnehmen(self, name, guard, start_sofort=True):
        """Riegel + Notbremsen fuer EINEN Waechter; bei Erfolg Kachel +
        Leser-Thread. EIN Weg fuer Boot (start(), start_sofort=False — die
        Threads starten dort gesammelt) und Store-Reload (start_sofort=True).
        -> True bei Start, None sonst.

        Enable-Riegel SERVERSEITIG (§2.4): nicht nur UI-Grau. Seit .196
        entscheidet KEIN Lastmodell mehr (User: enabled = laeuft) — nur
        harter Deckel + RAM-Boden (slot_pruefen)."""
        ok, grund = test_gueltig(guard)
        if not ok:
            self.verweigert[name] = f"enable refused: {grund}"
            self.log(f"live {name}: {self.verweigert[name]}")
            return None
        ok, grund = self.vermessung.slot_pruefen(len(self.kacheln))
        if not ok:
            self.verweigert[name] = f"slot refused: {grund}"
            self.log(f"live {name}: {self.verweigert[name]}")
            return None
        self.log(f"live {name}: slot granted ({grund})")
        self.verweigert.pop(name, None)
        k = Kachel(name, guard, self.defaults)
        self.kacheln[name] = k
        t = threading.Thread(target=self._kachel_lauf, args=(k,),
                             name=f"live-{name}", daemon=True)
        k.thread = t
        self.threads.append(t)
        if start_sofort:
            t.start()
        return True

    def _kachel_stoppen(self, name, grund):
        """EINEN Waechter beenden (Reload-Weg, §8 'nur der betroffene startet
        neu'): Einzel-Stopp-Event; Kill + Join laufen in einem AUFRAEUM-Thread
        (Engine-M4, gemessen: der synchrone join(5) im Herzschlag-Thread riss
        eine 7,1-s-Status-Luecke — die Engine galt als tot, gesunde Kacheln
        zeigten 'disturbed', und im Fenster startete der Helfer-Weg ein
        ZWEITES Modell auf der iGPU; ein D-State-Kill haette den Herzschlag
        sogar unbegrenzt gehalten). Der Stopp steht sofort in der Status-
        QUITTUNG (Kachel aus dem dict = aus dem Status) — erst dann darf die
        Kachel im UI kippen (K1 in beide Richtungen)."""
        k = self.kacheln.pop(name, None)
        if k is None:
            return
        k.stop_ev.set()
        k.zustand = "gestoppt"
        k.zustand_grund = grund
        self._klog(k, f"WACHE STOPP ({grund})")

        def aufraeumen():
            if k.kill:
                try:
                    k.kill()
                except Exception:
                    pass
            if k.thread:
                k.thread.join(timeout=10)
                try:
                    self.threads.remove(k.thread)
                except ValueError:
                    pass
        self._thread_starten(f"live-stopp-{name}", aufraeumen)

    def _store_leere_echt(self):
        """Engine-B2-Plausibilitaetsboden als EIGENER Baustein (MUSS-N2b,
        RECHECK 12.08.: der Boden war unbewacht — ein Refactoring im Reload
        haette ihn geraeuschlos wieder mitgenommen; jetzt fasst ihn der
        Harnisch als eigenen Mutanten): '0 Guards, wo eben welche liefen'
        ist nur dann eine ECHTE Loeschung, wenn der Store parsebar und
        wirklich ein (guard-leeres) Objekt ist. -> (echt_leer, probe_fehler)."""
        try:
            with open(self.store_pfad) as f:
                probe = json.load(f)
            if isinstance(probe, dict):
                return True, ""
            return False, f"Store-Inhalt ist {type(probe).__name__}, kein Objekt"
        except Exception as e:
            return False, f"{type(e).__name__}: {str(e)[:120]}"

    def _config_pruefen(self):
        """Store-Mtime-Reload (Bauplan §8 'Config-Aenderung im Betrieb'):
        NUR der betroffene Waechter startet neu; leichte Aenderungen (die
        zwei User-Zeiten, Kanaele, Schnell-Urteil) uebernimmt die laufende
        Kachel OHNE Neustart. Defaults-Aenderungen brauchen weiterhin einen
        Engine-Neustart (laut geloggt, nie still).

        NACHSTART-Hinweis (C1; .196 vereinfacht): der Slot-Neuversuch beim
        Store-Schreib (unten, k is None) deckt den Randfall, dass eine
        Notbremse (RAM-Boden/Deckel) beim letzten Versuch griff — ein
        Lastmodell entscheidet seit .196 nicht mehr."""
        if not (self.config_quelle and self.store_pfad):
            return
        try:
            mt = os.path.getmtime(self.store_pfad)
        except OSError:
            mt = None
        if mt == self._store_mtime:
            return
        try:
            cfg_neu = self.config_quelle()
        except Exception as e:
            # Engine-M2: die Mtime-Kante NICHT verbrauchen — ein transienter
            # Ladefehler (EMFILE/ENOMEM-Klasse) darf eine Config-Aenderung
            # (z. B. ein Disable) nicht ENDGUELTIG verlieren; naechster Takt
            # versucht es erneut (Log gedrosselt). Eigener Drossel-Schluessel
            # je Ereignisklasse (KANN-N3, RECHECK 12.08.: der Sammel-
            # Schluessel ('reload',) schluckte die B2-Zeile, wenn kurz zuvor
            # ein Ladefehler lief — dieselbe Kollisions-Klasse wie Lens-A B3).
            self._fehler_log(("reload", "laden"),
                             f"Config-Reload fehlgeschlagen: "
                             f"{type(e).__name__}: {e} — "
                             f"naechster Versuch am naechsten Takt")
            return
        defaults_neu, guards_neu = guards_lesen(cfg_neu, self.log)
        # Engine-B2 (gemessen: EIN unlesbarer Store — halber Hand-Edit,
        # EMFILE, Datei kurz weg — stoppte ALLE Waechter mit dem FALSCHEN
        # Grund 'guard removed from store', ohne eine laute Zeile):
        # '0 Guards, wo eben welche liefen' ist ein LOESCH-VerDACHT, kein
        # Loeschbefehl. Der Store selbst wird direkt gegengeprueft: nur wenn
        # er PARSEBAR und wirklich guard-leer ist, ist die Leere echt. Sonst
        # laut + Stoerung + alten Guard-Stand BEHALTEN, Kante nicht
        # verbrauchen (Retry am naechsten Takt).
        if self.kacheln and not guards_neu:
            echt_leer, probe_fehler = self._store_leere_echt()
            if not echt_leer:
                self._fehler_log(("reload", "store"),
                                 f"Config-Store NICHT lesbar ({probe_fehler}) — "
                                 f"{len(self.kacheln)} laufende Waechter werden "
                                 f"BEHALTEN (das ist KEINE Guard-Loeschung); "
                                 f"naechster Versuch am naechsten Takt")
                self._stoerung_global(
                    f"config store unreadable ({probe_fehler}) — keeping "
                    f"{len(self.kacheln)} running watcher(s), fix the store file")
                return
        self._store_mtime = mt              # Kante erst NACH erfolgreichem Laden (M2)
        if defaults_neu != self.defaults:
            self.log("live: defaults changed in the store — guards reload "
                     "live, defaults need an engine restart (unchanged in "
                     "this process, LOUD by design)")
        # Melder/_echte_quelle halten eine Referenz auf DIESES dict — in
        # place aktualisieren, damit alle dieselbe Config-Wahrheit sehen
        # (Identitaets-Wache: liefert die Quelle dasselbe Objekt, wuerde
        # clear() die Config selbst ausloeschen).
        if cfg_neu is not self.cfg:
            self.cfg.clear()
            self.cfg.update(cfg_neu)
        self.guards = guards_neu
        for name in [n for n in self.kacheln if n not in guards_neu]:
            self._kachel_stoppen(name, "guard removed from store")
            self.verweigert.pop(name, None)
        for name, g in guards_neu.items():
            k = self.kacheln.get(name)
            if not g["enabled"]:
                self.verweigert.pop(name, None)
                if k is not None:
                    self._kachel_stoppen(name, "disabled via store")
                continue
            if k is None:
                self._kachel_aufnehmen(name, g)      # neu ODER Nachstart-Versuch
                continue
            ok, grund = test_gueltig(g)
            if not ok:
                # Quelle geaendert -> Test entwertet -> Stopp MIT Grund (§2.4/§8).
                self._kachel_stoppen(name, f"stopped: {grund}")
                self.verweigert[name] = f"enable refused: {grund}"
                continue
            if quelle_fp(g) != quelle_fp(k.cfg):
                # Neue Quelle MIT gruenem Test: gezielter Einzel-Neustart.
                self._kachel_stoppen(name, "source changed — restarting")
                self._kachel_aufnehmen(name, g)
                continue
            leichte = ("ende_ohne_gesicht_s", "wieder_scharf_s", "kanaele")
            if any(k.cfg.get(f) != g.get(f) for f in leichte):
                self._klog(k, "Konfig uebernommen ohne Neustart "
                              "(Zeiten/Kanaele/Schnell-Urteil)")
            k.cfg = g                                # atomarer dict-Tausch

    # ---------------------------------------------------------------- Leser je Kachel
    def _echte_quelle(self, k):
        """Default-Frame-Fabrik: Quelle aufloesen, Steckbrief, ffmpeg-Leser mit
        lautem HW-Rueckfall. -> (frames_iter, kill, steckbrief)."""
        url, weg, fehler = quelle_aufloesen(self.cfg, k.name, k.cfg,
                                            streng=False, log=self.log)
        if fehler:
            raise RuntimeError(fehler)
        steck = steckbrief_ermitteln(url, log=self.log)
        skala = wach_skala(steck["breite"], steck["hoehe"],
                           k.cfg.get("hoehe") or self.defaults["hoehe"])
        p, b, h, hw = leser_mit_rueckfall(url, skala, log=self.log)

        def kill():
            try:
                p.kill()
                p.wait()
            except Exception:
                pass
        # pid des ffmpeg-Kinds fuer die Last-Messung (Decode-CPU getrennt
        # ausweisen); Stub-Fabriken liefern keins — die Messung sagt das dann.
        steck = dict(steck, skala_b=b, skala_h=h, weg=weg,
                     quelle=quelle_maskiert(url), hw=hw, pid=p.pid)
        return bilder_yuv(p, b, h, 0), kill, steck

    def _warte_kachel(self, k, s):
        """Warten mit BEIDEN Stopp-Wegen (globales stop_ev + Einzel-Stopp der
        Kachel, Reload-Weg) -> True = aufhoeren."""
        ende = time.monotonic() + s
        while True:
            rest = ende - time.monotonic()
            if rest <= 0:
                return self.stop_ev.is_set() or k.stop_ev.is_set()
            if self.stop_ev.wait(min(0.2, rest)):
                return True
            if k.stop_ev.is_set():
                return True

    def _kachel_lauf(self, k):
        """Leser-Thread einer Kachel: Reconnect-Muster des Prototyps (5 s
        verdoppelnd bis 60 s, Reset erst nach >= 30 s getragener Verbindung),
        monotone Fristen, Exception-Fang JE KACHEL (Stoerungs-Selbstmeldung
        statt stillem Thread-Tod)."""
        warte = RECONNECT_WARTE
        try:
            while not (self.stop_ev.is_set() or k.stop_ev.is_set()):
                try:
                    frames, kill, steck = self.frames_fabrik(k)
                except Exception as e:
                    k.zustand = "gestoert"
                    k.zustand_grund = f"connect: {type(e).__name__}: {str(e)[:80]}"
                    k.reconnect_fehler += 1
                    self._klog(k, f"Verbindung fehlgeschlagen ({k.zustand_grund}) "
                                  f"— neuer Versuch in {warte:g}s")
                    if self._warte_kachel(k, warte):
                        break
                    warte = min(warte * 2, RECONNECT_MAX)
                    continue
                k.kill = kill
                k.steckbrief = steck
                k.hw = steck.get("hw")
                from face_audit import Embedder
                k.netz = Embedder.ar_det_size(steck.get("skala_b") or 1280,
                                              steck.get("skala_h") or WACH_HOEHE,
                                              basis=self.defaults["det_basis"])
                k.verbunden_mono = self.jetzt()
                k.verbunden_bilder = k.bilder    # M-D: Basis der realen Liefer-fps
                k.zustand = "aktiv"
                k.zustand_grund = ""
                # Feed-Steckbrief in die Startzeile (stand.md-Auflage):
                # Original -> verarbeitet, fps/Codec/Bezugsweg, Bandbreite wo da.
                self._klog(k, f"WACHE START {k.name} (Quelle "
                              f"{steck.get('breite')}x{steck.get('hoehe')}"
                              + (f" @ {steck.get('fps')} fps" if steck.get("fps") else "")
                              + (f", {steck.get('codec')}" if steck.get("codec") else "")
                              + (f", ~{steck.get('bitrate_kbps')} kbit/s"
                                 if steck.get("bitrate_kbps") else "")
                              + f" -> verarbeitet {steck.get('skala_b')}x{steck.get('skala_h')}, "
                              + (f"HW-Decode ({steck.get('hw')})" if steck.get("hw")
                                 else ("SW-Decode (Rueckfall)"
                                       if steck.get("hw") is False else "SW-Decode"))
                              + f", Netz {k.netz[0]}x{k.netz[1]}, Weg {steck.get('weg')}, "
                              + f"Quelle {steck.get('quelle')})")
                n_vorher = k.bilder
                try:
                    for yuv in frames:
                        if self.stop_ev.is_set() or k.stop_ev.is_set():
                            break
                        k.bilder += 1
                        mono = self.jetzt()
                        k.letztes_bild_mono = mono
                        k.letztes_bild_wand = self.wanduhr()
                        with k.lock:
                            pruefen, enden = k.burst.takt(k.bilder, mono)
                            burst_aktiv = k.burst.aktiv
                        for ende in (enden or []):
                            self._ende_loggen(k, ende)
                        if not pruefen:
                            continue
                        # Ueberlast-Drossel NUR fuer den Normaltakt (§7-Auflage):
                        # Bursts bleiben ungebremst, der Eingriff wird gezaehlt
                        # und steht im Status.
                        if not burst_aktiv:
                            f = self.scheduler.normal_faktor()
                            if f > 1:
                                k.normal_zaehler += 1
                                if k.normal_zaehler % f != 0:
                                    k.gedrosselt += 1
                                    continue
                        # Auftrags-Pause (User-Auflage 12.08.): waehrend einer
                        # Last-Messung/eines Quelltests stellt der Scheduler
                        # die ANDEREN Kacheln still — der Leser laeuft weiter
                        # (ffmpeg lebt, Modell bleibt geladen, Zaehler/Watchdog
                        # bleiben ehrlich), nur eingereiht wird nichts.
                        if self._pause_ausser and k.name != self._pause_ausser:
                            k.pausiert += 1
                            continue
                        # Lens-A M2: hier wird EINGEREIHT, nicht geprueft —
                        # geprueft zaehlt erst die echte Detektion (latest wins
                        # kann Eingereihtes noch ersetzen, gezaehlt im Status).
                        k.eingereiht += 1
                        self.scheduler.einreihen(k.name, burst_aktiv, (yuv, mono), mono)
                finally:
                    try:
                        kill()
                    except Exception:
                        pass
                if self.stop_ev.is_set() or k.stop_ev.is_set():
                    break
                # Stream-Abriss (oder Watchdog-Kill): Prototyp-Rezept.
                k.abrisse += 1
                mono = self.jetzt()
                stand_s = mono - (k.verbunden_mono or mono)
                if k.bilder > n_vorher and stand_s >= RECONNECT_STABIL:
                    warte = RECONNECT_WARTE
                k.zustand = "gestoert"
                k.zustand_grund = "stream ended / no frames"
                with k.lock:
                    enden = k.burst.abriss_enden(mono)
                for ende in enden:
                    self._ende_loggen(k, ende)
                self._klog(k, f"STREAM-ABRISS nach {k.bilder} Bildern "
                              f"({k.bilder - n_vorher} auf dieser Verbindung, "
                              f"{stand_s / 60:.1f} min) — Neuverbindung in {warte:g}s "
                              f"[Abriss #{k.abrisse}]")
                if self._warte_kachel(k, warte):
                    break
                warte = min(warte * 2, RECONNECT_MAX)
        except Exception as e:
            # Exception-Fang JE KACHEL: der Waechter-Thread darf nie still
            # sterben (Fehlklasse stiller Verlust; Realbeleg Waechter-Tod 11.08.).
            import traceback
            k.zustand = "gestoert"
            k.zustand_grund = f"thread died: {type(e).__name__}: {str(e)[:120]}"
            self._klog(k, f"!! Waechter-Thread gestorben: {k.zustand_grund}")
            self.log(traceback.format_exc())
            self._stoerung_senden(k, f"watcher thread died: {type(e).__name__}: "
                                     f"{str(e)[:120]}")
        finally:
            if self.stop_ev.is_set() or k.stop_ev.is_set():
                k.zustand = "gestoppt"

    # ------------------------------------------- Auftraege (Quelltest/Last-Messung)
    def _kommando_pruefen(self):
        """Kommando-Datei des Dienstes lesen (verifyd schreibt sie atomar,
        kommando_schreiben) — hoechstens EIN Auftrag gleichzeitig; jedes
        Kommando traegt ein ts und wird genau einmal verarbeitet."""
        try:
            with open(self.kommando_pfad) as f:
                cmd = json.load(f)
        except Exception:
            return
        ts = cmd.get("ts")
        if ts is None or ts == self._kommando_ts:
            return
        self._kommando_ts = ts
        art = str(cmd.get("aktion") or "")
        kamera = str(cmd.get("kamera") or "")
        if art not in ("messung", "test") or not kamera:
            self.log(f"live: unbekanntes Kommando {art!r}/{kamera!r} — ignoriert")
            return
        self._auftrag_starten(art, kamera, cmd)

    def _auftrag_starten(self, art, kamera, cmd):
        with self._auftrag_lock:
            if self._auftrag is not None:
                laeuft = f"{self._auftrag.get('art')} {self._auftrag.get('kamera')}"
                self.log(f"live {art} {kamera}: refused — another job is "
                         f"running ({laeuft})")
                self.auftrag_ergebnisse.setdefault(kamera, {})[art] = {
                    "ok": False, "ts": round(self.wanduhr(), 1), "art": art,
                    # vorab: ABWEISUNG vor dem Lauf — die UI zeigt sie im
                    # Poll, aber sie ersetzt NIE ein gespeichertes Ergebnis.
                    "vorab": True,
                    "fehler": f"another job is already running ({laeuft})"}
                return
            # KANN-4 (Engine-Lens): der Kameraname kommt roh aus dem POST —
            # ein freier String pausierte sonst alle Waechter, bis die
            # Quellaufloesung nach Minuten scheitert. Bekannt ist, wer einen
            # Guard hat oder in der Frigate-Liste steht; ohne injizierte
            # Liste (Frigate beim Start nicht erreichbar) bleibt die alte
            # Toleranz.
            if (kamera not in self.guards and self.kameras
                    and kamera not in self.kameras):
                self.log(f"live {art} {kamera}: refused — unknown camera")
                self.auftrag_ergebnisse.setdefault(kamera, {})[art] = {
                    "ok": False, "ts": round(self.wanduhr(), 1), "art": art,
                    "vorab": True,
                    "fehler": (f"unknown camera {kamera!r} — not in Frigate "
                               f"and no saved watcher")}
                return
            dauer = None
            if art == "messung":
                try:
                    dauer = float(cmd.get("dauer_s") or MESSUNG_DAUER_S)
                except (TypeError, ValueError):
                    dauer = MESSUNG_DAUER_S
                dauer = min(max(dauer, self.mess_min_s), self.mess_max_s)
            # Auftrags-GENERATION (Engine-B1): jeder Auftrag traegt sein
            # eigenes dict + lauf_id; finally/Not-Aus raeumen nur die EIGENE
            # Generation — ein Zombie kann den Nachfolger nie abraeumen.
            self._auftrag_serie += 1
            a = {"art": art, "kamera": kamera, "phase": "verbinden",
                 "start_mono": self.jetzt(), "dauer_s": dauer,
                 "bis_mono": None, "start_ts": round(self.wanduhr(), 1),
                 "lauf_id": self._auftrag_serie, "kill": None,
                 "abbruch": threading.Event(), "abbruch_mono": None,
                 "thread": None}
            self._auftrag = a
        a["thread"] = self._thread_starten(f"live-auftrag-{kamera}",
                                           lambda: self._auftrag_lauf(a))

    def _auftrag_phase(self, phase, bis_mono=None):
        with self._auftrag_lock:
            if self._auftrag:
                self._auftrag["phase"] = phase
                self._auftrag["bis_mono"] = bis_mono

    def _auftrag_pause_setzen(self, kamera, art):
        """ALLE Kacheln stillstellen — auch eine aktive Kachel DERSELBEN
        Kamera (Sentinel statt Kameraname: matcht keine Kachel): die Messung
        laeuft auf einer EIGENEN Verbindung, und ihre Last-Zahlen sind nur
        ohne Fremdbilder ehrlich. Der wartende Scheduler-Rueckstand wird
        VERWORFEN statt 'entwaessert' (Engine-M1: die 0,5-s-Zeitannahme war
        ab Rueckstand > 500 ms falsch — die harte Detektor-Serialisierung
        leistet seither self._det_lock, nicht die Pause). Leser laufen
        weiter (ffmpeg lebt, Modell bleibt geladen), nur Einreihen steht
        still — Wiederanlauf ist ein No-Op."""
        pausiert = sorted(self.kacheln)
        self._pause_ausser = "\x00auftrag"
        verworfen = self.scheduler.raeumen()
        self.log(f"live {art} {kamera}: watchers paused for measurement: "
                 f"{', '.join(pausiert) or '(none)'}"
                 + (f" — {verworfen} queued frame(s) dropped (stale by design)"
                    if verworfen else ""))

    def _auftrag_lauf(self, a):
        """EIN Auftrag (Quelltest oder Last-Messung) — ABBRUCH-SICHER, jetzt
        GENERATIONS-GEBUNDEN (Engine-B1, gemessen: das alte bedingungslose
        finally raeumte nach einem Not-Aus den NACHFOLGER-Auftrag ab —
        Countdown weg, Doppel-Start moeglich, 2 parallele erkennen()):
        finally raeumt Pause und Auftrags-Slot NUR, wenn dieser Lauf ihn noch
        besitzt (self._auftrag is a). Ein per Not-Aus abgebrochener Lauf
        schreibt auch kein spaetes Ergebnis mehr ueber die Timeout-Quittung."""
        kamera, art = a["kamera"], a["art"]
        try:
            guard = self.guards.get(kamera) or {"quelle": "proxy", "url": ""}
            if art == "test":
                ergebnis = self._quelltest_ausfuehren(kamera, guard, a)
            else:
                ergebnis = self._messung_ausfuehren(kamera, guard,
                                                    a["dauer_s"], a)
        except Exception as e:
            ergebnis = {"ok": False,
                        "fehler": f"{type(e).__name__}: {str(e)[:120]}"}
        finally:
            with self._auftrag_lock:
                if self._auftrag is a:
                    self._auftrag = None
                    self._pause_ausser = None
        if a["abbruch"].is_set():
            # Not-Aus hat abgebrochen und quittiert — das Spaet-Ergebnis
            # dieses Laufs (unter Abbruch entstanden) ueberschreibt weder
            # die Timeout-Quittung noch ein Nachfolger-Ergebnis.
            self.log(f"live {art} {kamera}: aborted job thread ended "
                     f"(late result discarded)")
            return
        ergebnis["ts"] = round(self.wanduhr(), 1)
        ergebnis["art"] = art
        self.auftrag_ergebnisse.setdefault(kamera, {})[art] = ergebnis
        self.log(f"live {art} {kamera}: "
                 f"{'ok' if ergebnis.get('ok') else 'FEHLER'} — "
                 f"{ergebnis.get('text') or ergebnis.get('fehler') or ''}")
        try:
            self._status_schreiben(self.jetzt())     # Ende sofort quittieren
        except Exception:
            pass

    def _quelltest_ausfuehren(self, kamera, guard, a=None):
        """§5-Quelltest ueber den GETEILTEN Detektor der Engine (kein zweites
        Modell auf der iGPU — Lehre aus dem Vier-Waechter-Tod 11.08., als
        Gate-Container und Waechter auf derselben iGPU kollidierten).
        OHNE Kachel-Pause (Fix-Zyklus 12.08.): die Serialisierung des einen
        Detektor-Passes leistet _det_lock (M1) — pausiert wird nur die
        MESSUNG, deren Zahlen Fremdlast nicht vertragen. Der kill-Griff der
        Test-Verbindung wird im Auftrag registriert, damit der Not-Aus eine
        haengende Verbindung von aussen beenden kann (B1)."""
        self._auftrag_phase("messen")
        det = (_DetektorMitLock(self.detektor, self._det_lock)
               if self.detektor is not None else None)
        reg = None
        if a is not None:
            def reg(toeten):
                a["kill"] = toeten
        ok, text, block = self.quelltest_fn(
            self.cfg, kamera, guard, det, log=self.log,
            det_basis=self.defaults["det_basis"],
            hoehe=guard.get("hoehe") or self.defaults["hoehe"],
            kill_registrar=reg)
        return {"ok": ok, "text": text, "block": block}

    @staticmethod
    def _proc_cpu_s(pid):
        """utime+stime eines Prozesses in Sekunden (None wenn unlesbar)."""
        try:
            felder = open(f"/proc/{pid}/stat").read().rsplit(") ", 1)[1].split()
            return (int(felder[11]) + int(felder[12])) / os.sysconf("SC_CLK_TCK")
        except Exception:
            return None

    def _messung_ausfuehren(self, kamera, guard, dauer_s, a=None):
        """Last-Messung EINES Waechters (User-Auflage 12.08.): eigene
        Verbindung, Detektion im Normaltakt, 15-30 s — misst CPU des
        Engine-Prozesses, Decode-CPU des ffmpeg-Kinds (getrennt), det-ms,
        GPU-Budget-Anteil und RSS-Delta. Ergebnis ist eine MESSUNG dieser
        Maschine, kein Literaturwert (§2.3).

        FRIST ECHT (Engine-B1, gemessen: eine lebende, stumme Quelle hielt
        die Messung UNBEGRENZT — die Frist wurde nur je geliefertem Bild
        geprueft, und das ffmpeg-Kind leckte, weil das finally nie lief):
        ein Zulieferer-Thread zieht die Frames, die Mess-Schleife liest mit
        WANDUHR-Deadline aus einer Queue — die bestellte Dauer gilt auch,
        wenn NIE ein Bild kommt; kill() im finally wird damit immer erreicht.
        Die PAUSE der anderen Kacheln beginnt erst MIT der Messphase (nicht
        schon beim Verbinden — dessen begrenzte Retries dauerten sonst
        Minuten Pause); Fremdbilder haelt zusaetzlich scheduler.raeumen()
        plus _det_lock fern (M1)."""
        rss_vor = rss_mb()
        # Phase 1: Verbinden (Quelle aufloesen + eigener Leser; Frame-Quelle
        # ist die injizierte Fabrik — der Harnisch misst damit ohne Stream).
        tempk = Kachel(kamera, dict(guard, kanaele=[]), self.defaults)
        frames, kill, steck = self.frames_fabrik(tempk)
        if a is not None:
            a["kill"] = kill              # Not-Aus kann die Verbindung beenden
        fertig = threading.Event()
        q = queue.Queue(maxsize=32)
        ENDE = object()

        def zulieferer():
            try:
                for yuv in frames:
                    while not fertig.is_set():
                        try:
                            q.put(yuv, timeout=0.25)
                            break
                        except queue.Full:
                            continue
                    if fertig.is_set():
                        return
            finally:
                try:
                    q.put_nowait(ENDE)
                except queue.Full:
                    pass
        zt = threading.Thread(target=zulieferer,
                              name=f"live-mess-zulieferer-{kamera}", daemon=True)
        try:
            from face_audit import Embedder
            netz = Embedder.ar_det_size(steck.get("skala_b") or 1280,
                                        steck.get("skala_h") or WACH_HOEHE,
                                        basis=self.defaults["det_basis"])
            kind_pid = steck.get("pid")
            self._auftrag_pause_setzen(kamera, "messung")
            zt.start()
            ende = self.jetzt() + float(dauer_s)
            self._auftrag_phase("messen", ende)
            cpu_vor = os.times()
            kind_cpu_vor = self._proc_cpu_s(kind_pid) if kind_pid else None
            rate = int(self.defaults["rate"]) or 1
            n = 0
            det_ms = []
            t0 = self.jetzt()
            while True:
                if self.stop_ev.is_set():
                    return {"ok": False, "fehler": "engine stopping"}
                if a is not None and a["abbruch"].is_set():
                    return {"ok": False, "fehler": "aborted (job timeout)"}
                rest = ende - self.jetzt()
                if rest <= 0:
                    break
                try:
                    yuv = q.get(timeout=min(rest, 0.5))
                except queue.Empty:
                    continue              # Wanduhr-Frist laeuft auch ohne Bilder
                if yuv is ENDE:
                    break                 # Quelle endete frueher (EOF/Abriss)
                n += 1
                if n % rate:
                    continue
                t1 = self.jetzt()
                frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
                try:
                    if self.detektor:
                        with self._det_lock:              # M1: nie 2 erkennen()
                            self.detektor.erkennen(frame, netz)
                except Exception as e:
                    return {"ok": False, "fehler": f"detector: "
                                                   f"{type(e).__name__}: {str(e)[:80]}"}
                det_ms.append((self.jetzt() - t1) * 1000.0)
            dauer_real = max(self.jetzt() - t0, 0.001)
            if n == 0:
                return {"ok": False,
                        "fehler": f"no frames within {dauer_s:.0f}s "
                                  f"(source unreachable or silent)"}
            # Phase 3: Auswerten.
            self._auftrag_phase("auswerten")
            cpu_nach = os.times()
            cpu_s = ((cpu_nach.user - cpu_vor.user)
                     + (cpu_nach.system - cpu_vor.system))
            kind_cpu_nach = self._proc_cpu_s(kind_pid) if kind_pid else None
            rss_nach = rss_mb()
            fps = n / dauer_real
            dm = (sum(det_ms) / len(det_ms)) if det_ms else None
            gpu_ms = (fps / rate) * dm if dm is not None else None
            e = {"ok": True, "dauer_s": round(dauer_real, 1),
                 # UI-M6: die Messung ist an GENAU diese Quelle gebunden —
                 # nach einem Quellwechsel kennzeichnet die UI sie als
                 # entwertet (derselbe Fingerprint-Griff wie beim Test).
                 "quelle_fp": quelle_fp(guard),
                 "fps": round(fps, 1),
                 "det_ms": round(dm, 1) if dm is not None else None,
                 # CPU des ENGINE-Prozesses im Messfenster (Konvertierung +
                 # Detektions-CPU-Anteil; andere Waechter pausierten) ...
                 "cpu_prozent": round(100.0 * cpu_s / dauer_real, 1),
                 # ... und der DECODE-Posten des ffmpeg-Kinds GETRENNT.
                 "decode_cpu_prozent": (
                     round(100.0 * (kind_cpu_nach - kind_cpu_vor) / dauer_real, 1)
                     if kind_cpu_vor is not None and kind_cpu_nach is not None
                     else None),
                 "gpu_ms_je_s": round(gpu_ms, 1) if gpu_ms is not None else None,
                 "gpu_budget_anteil": (round(gpu_ms / GPU_BUDGET_MS_JE_S, 3)
                                       if gpu_ms is not None else None),
                 "rss_mb": rss_nach,
                 "rss_delta_mb": (round(max(0.0, rss_nach - rss_vor), 1)
                                  if rss_vor is not None and rss_nach is not None
                                  else None),
                 "hw": steck.get("hw"),
                 "aufloesung": f"{steck.get('breite')}x{steck.get('hoehe')}",
                 "skala": f"{steck.get('skala_b')}x{steck.get('skala_h')}"}
            e["text"] = (f"{e['fps']} frames/s, detector "
                         f"{e['det_ms'] if e['det_ms'] is not None else '?'} ms, "
                         f"engine CPU {e['cpu_prozent']}%"
                         + (f" + decode {e['decode_cpu_prozent']}%"
                            if e["decode_cpu_prozent"] is not None else "")
                         # .252 (User-Fund am cpu-Build: "GPU budget share"
                         # auf einer CPU-Maschine ist gelogen): das Budget
                         # ist das DETEKTOR-Zeitbudget, backend-neutral.
                         + (f", detector budget share "
                            f"{e['gpu_budget_anteil']:.0%}"
                            if e["gpu_budget_anteil"] is not None else "")
                         + (f", RSS +{e['rss_delta_mb']} MB"
                            if e["rss_delta_mb"] is not None else ""))
            return e
        finally:
            fertig.set()
            try:
                kill()                    # beendet ffmpeg -> Zulieferer laeuft aus
            except Exception:
                pass
            if zt.is_alive():
                zt.join(timeout=5)

    # ---------------------------------------------------------------- Detektor
    def _detektor_lauf(self):
        """DER eine Detektor-Thread (Architektur B), mit FEHLER-KLASSIFIKATION
        (Lens-A B4, gemessen: eine volle Platte beendete als 'detector failure'
        nach 3 sinnlosen Modell-Neubauten ALLE Waechter):
         * Frame-Konvertierung scheitert  -> Kachel-Fehler, weiter.
         * detektor.erkennen() scheitert  -> DETEKTOR-Tod-Pfad (CL_OUT_OF_
           RESOURCES-Klasse, Realbeleg 11.08.): melden, neu bauen, bei
           endgueltigem Tod Engine LAUT beenden — die Todes-Meldung geht
           DROSSELFREI raus (Lens-A B3: sie fiel sonst in die eigene Drossel).
         * _befund/_trigger scheitert (IO: JPG, Platte, Pose) -> KACHEL-
           Stoerung mit Grund, nie Engine-Ende.
        Die Drossel bekommt die GANZE Thread-Belegung des Bilds gemeldet
        (inkl. Konvertierung, Filter, Pose-Gate, JPEG — Lens-B M5); die
        det_ms-EMA fuer die Slot-Mathe bleibt die reine erkennen()-Zeit."""
        neubauten = 0
        while not self.stop_ev.is_set():
            z = self.scheduler.naechste(timeout=0.5)
            if z is None:
                continue
            name, burst, (yuv, mono), _einreih = z
            k = self.kacheln.get(name)
            if k is None:
                continue
            t0 = self.jetzt()
            try:
                frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
            except Exception as e:
                self._kachel_fehler(k, "frame", f"Frame-Konvertierung: "
                                                f"{type(e).__name__}: {str(e)[:120]}")
                continue
            try:
                # M1: erkennen() NUR unter dem Detektor-Lock — der Auftrags-
                # Thread (Messung/Quelltest) nimmt dasselbe Lock; zwei Threads
                # auf einer Session sind damit by construction unmoeglich.
                if self.detektor:
                    with self._det_lock:
                        faces = self.detektor.erkennen(frame, k.netz)
                else:
                    faces = []
                det_dauer = self.jetzt() - t0
            except Exception as e:
                import traceback
                self.log(f"!! live detector failure: {type(e).__name__}: {e}")
                self.log(traceback.format_exc())
                self._stoerung_global(f"detector failure: {type(e).__name__}: "
                                      f"{str(e)[:120]}")
                if self.detektor_fabrik and neubauten < 3:
                    neubauten += 1
                    if self.stop_ev.wait(self.neubau_warte_s * neubauten):
                        return
                    try:
                        self.detektor = self.detektor_fabrik()
                        self.log(f"live detector rebuilt (attempt {neubauten})")
                        continue
                    except Exception as e2:
                        self.log(f"!! detector rebuild failed: {e2}")
                if neubauten >= 3 or not self.detektor_fabrik:
                    self.engine_fehler = (f"detector dead after {neubauten} rebuild "
                                          f"attempts: {type(e).__name__}")
                    # B3: die Todes-Meldung MUSS raus — an der Drossel vorbei
                    # (die erste failure-Meldung eben hat sie sonst geschluckt).
                    self._stoerung_global(f"live engine STOPPING: {self.engine_fehler}",
                                          drosselfrei=True)
                    self.stop_ev.set()
                    return
                continue
            neubauten = 0
            self.vermessung.det_messung(det_dauer * 1000.0)
            k.geprueft += 1                      # Lens-A M2: WIRKLICH detektiert
            try:
                self._befund(k, frame, faces or [], mono, burst, yuv=yuv)
                self._vorschau_schreiben(k, frame, mono)
            except Exception as e:
                # B4: IO-/Verarbeitungs-Fehler sind KACHEL-Stoerungen — nie
                # Engine-Ende, nie Modell-Neubau, nie still.
                k.verarbeitungs_fehler += 1
                self._kachel_fehler(k, "verarbeitung",
                                    f"{type(e).__name__}: {str(e)[:120]}")
            finally:
                stufe = self.scheduler.arbeit_melden(self.jetzt() - t0, self.jetzt())
                if stufe is not None:
                    self.log(f"live overload rule: throttle level {stufe} "
                             f"(normal rate x{self.scheduler.normal_faktor()}, "
                             f"utilization {self.scheduler.auslastung():.2f}) — "
                             f"bursts stay at full rate")

    def _befund(self, k, frame, faces, mono, burst, yuv=None):
        """Detektions-Befund einer Kachel verarbeiten (Filter, Burstwache,
        Trigger). Laeuft im Detektor-Thread; Burstwache/Episode unter k.lock
        (der Leser-Thread ruft takt() auf demselben Objekt)."""
        echte = [f for f in faces
                 if echtes_gesicht(f, frame, self.defaults["min_score"])]
        if not burst:
            with k.lock:
                # Rueckblick als YUV statt BGR (Lens-B K8: halbiert den
                # Dauer-Puffer, 1,5 statt 3 Byte/px — 24 Frames 720p ~33 statt
                # 66 MB je Kachel); konvertiert wird erst beim Video-Bau, und
                # der laeuft nur je Meldung.
                k.rueckblick.append((mono, yuv if yuv is not None else frame))
        if not echte:
            return
        echte.sort(key=lambda x: -float(x.det_score))
        k.funde += len(echte)
        # setdefault statt comprehension: bei bit-identischen Boxen gewinnt der
        # score-beste (echte ist absteigend sortiert), kein stilles Ueberschreiben.
        je_box = {}
        for g in echte:
            je_box.setdefault(tuple(float(v) for v in g.bbox), g)
        with k.lock:
            # Auftritt (User-Zeit a): Anker ist der LETZTE echte Fund (§4a —
            # neu gebaut; der Prototyp kannte diese Stelle nicht).
            if k.auftritt is None:
                k.auftritte += 1
                k.auftritt = {"seit_mono": mono, "letzter_fund_mono": mono,
                              "funde": 0, "trigger": 0}
                self._klog(k, f"Auftritt #{k.auftritte} beginnt")
            k.auftritt["letzter_fund_mono"] = mono
            k.auftritt["funde"] += len(echte)
            ereignisse = k.burst.fund_alle(mono, [
                (bx, (frame, g, float(g.det_score))) for bx, g in je_box.items()])
        for ereignis, info in ereignisse:
            if ereignis == "ende":
                self._ende_loggen(k, dict(info, grund="verdraengt"))
            elif ereignis == "start":
                g = je_box.get(info.get("box"))
                s_ = float(g.det_score) if g is not None else float(echte[0].det_score)
                self._klog(k, f"Track T{info['track']} START (Score {s_:.2f})"
                              + (f" — neben {info['neben']} Track(s)"
                                 if info["neben"] else " — ab jetzt jedes Bild"))
            elif ereignis == "trigger":
                self._trigger(k, info, mono)
        # Stufe 2 (.193, User 13.08.): kontinuierliches Namens-Voting ueber
        # den GANZEN Auftritt — nicht nur die 4 Trigger-Ketten-Bilder.
        if self.refs and self.win_thresh is not None:
            self._namens_stimmen(k, frame, je_box)

    def _namens_stimmen(self, k, frame, je_box):
        """KONTINUIERLICHES Namens-Voting je Auftritt (.193, User: 'PersonA,
        unbekannt, PersonA, PersonA -> feuern'): jedes echte Gesicht traegt sein
        FERTIGES Embedding (der Detektionslauf rechnet Recognition mit, kein
        zweiter Modelllauf) — hier faellt nur der NN-Vergleich an
        (Mikrosekunden). Ab NAME_STIMMEN Funden >= win_thresh fuer DIESELBE
        Person feuert die Namens-Meldung, EINMAL je Auftritt und Person.
        Der Anwesenheits-Trigger (Stufe 1) bleibt unberuehrt — er meldet
        weiterhin sofort JEDEN Menschen, auch Fremde."""
        import anlernen
        # .313 (Tester-Fund 21.08., 8x 'Carl' auf leerem Garten): EINE Stimme je
        # Person je Frame — vorher zaehlten zwei Boxen desselben Bildes doppelt,
        # NAME_STIMMEN=2 war damit aus einem einzigen Frame erreichbar.
        treffer = {}
        for g in je_box.values():
            try:
                v = np.asarray(g.normed_embedding, np.float32)
            except Exception:
                continue
            if v.size != 512 or not np.all(np.isfinite(v)):
                continue
            p, s = anlernen.nn(self.refs, v)
            if p is not None and s >= self.win_thresh:
                if p not in treffer or float(s) > treffer[p][0]:
                    treffer[p] = (float(s), tuple(float(x) for x in g.bbox))
        if not treffer:
            return
        with k.lock:
            a = k.auftritt
            if a is None:
                return
            st = a.setdefault("stimmen", {})
            for p, (s, box) in treffer.items():
                zaehler = st.setdefault(p, [0, 0.0, None])
                zaehler[0] += 1
                if s >= zaehler[1]:
                    zaehler[1] = s
                    zaehler[2] = box          # Box des besten Fundes (Beweisbild)
        self._namens_pending_feuern(k, frame)

    def _namens_pending_feuern(self, k, frame):
        """Namens-Meldungen, deren Stimmenzahl reicht, feuern — aber NUR, wenn
        der Auftritt schon einen pose-bestaetigten Trigger hat (.313: die
        Namens-Stufe lief bis dahin OHNE die Menschen-Pruefung der Stufe 1;
        docs/live-watchers.md versprach sie vor jeder Meldung). Ohne Pose-Gate
        (Config aus) gilt die Stimmenzahl allein. Aufgerufen je Frame aus
        _namens_stimmen und aus _trigger, sobald der Mensch bestaetigt ist."""
        feuern = []
        with k.lock:
            a = k.auftritt
            if a is None:
                return
            if self.defaults.get("pose_gate") and not a.get("mensch_bestaetigt"):
                return
            st = a.get("stimmen") or {}
            genannt = a.setdefault("genannt", set())
            for p, zaehler in st.items():
                if zaehler[0] >= NAME_STIMMEN and p not in genannt:
                    genannt.add(p)
                    feuern.append((p, zaehler[0], zaehler[1], zaehler[2]))
        for p, n, cos, box in feuern:
            self._namens_meldung(k, p, n, cos, frame, box=box)

    def _namens_meldung(self, k, person, stimmen, cos, frame, box=None):
        """Die Namens-Meldung der zweiten Stufe: eigene Nachricht NEBEN der
        Anwesenheits-Meldung.

        .319 MELDE-ANKER AUCH HIER (User 22.08., gemessen): bis dahin galt die
        Karenz der Stufe 1 hier bewusst NICHT — mit der Begruendung, der Name
        sei "genau EINE zusaetzliche Nachricht je Auftritt und Person" (das
        Einmal-Tor haelt _namens_stimmen ueber a['genannt']). Im Betrieb stimmt
        das nicht: das Tor gilt je AUFTRITT, und derselbe Mensch erzeugt auf
        derselben Kamera viele Auftritte hintereinander. Gemessen an
        verify_data/live/meldungen.jsonl (1030 Pushover, 13.-22.08.): die
        Namens-Meldung lief an der Drossel vorbei, weil _namens_pending_feuern
        VOR der melde_erlaubt-Pruefung des Triggers laeuft. Mit demselben Anker
        blieben 494 statt 1030 Meldungen (-52 %) — mehr Wirkung als jedes
        Sammelfenster, ohne Verzoegerung und ohne neuen Config-Wert.
        GEDROSSELT WIRD NUR DER VERSAND an die Push-Kanaele. Nicht gedrosselt:
        (a) MQTT — Home Assistant liest verifyd/live/<kamera> und die
        Additiv-Invariante verbietet, bestehende Ereignisse wegfallen zu
        lassen; (b) das Melde-Protokoll — die Live-Sicht und die Today-Zaehler
        zehren daraus, sie duerfen keine Auftritte verlieren. Der Anker ist
        derselbe wie beim Trigger (k.melde_bis_mono / wieder_scharf_s je
        Kachel, melde_erlaubt) — bewusst KEIN dritter Drossel-Begriff
        (qs_ebenen-Regel gegen verstreute Literale).

        SPRACH-STUFE 4: der Meldetext ist sprachfaehig (Eintrittspunkt (c)).
        Der MQTT-Payload unten bleibt byte-gleich — er traegt nur Kennungen
        (person/cosine/stimmen/preliminary/stufe), keinen Anzeigetext; genau
        deshalb ist diese Meldung teilbar, das Schnell-Urteil (§ oben) nicht.
        Der Text landet zusaetzlich im Melde-Protokoll (`zusatz`), das die
        UI nur ANZEIGT (html.escape, gekappt) — dort steht kuenftig die
        Sprache, in der wirklich gemeldet wurde."""
        _sprache.aktivieren()         # Eintrittspunkt (c), s. melden.sprache_aktivieren()
        self._klog(k, f"NAME [{person}]: {stimmen} Funde >= Schwelle, bester "
                      f"Kosinus {cos:.2f} — Namens-Meldung (preliminary)")
        # .245 (User-Go 17.08.): OHNE Meldekanal kein frueher Abbruch mehr —
        # das Ergebnis wird trotzdem journalt (kanal 'none', Anzeige ja,
        # Versand nein); vorher sah eine kanal-lose Installation NIE, was
        # live erkannt wurde. Fehlt nur der Versandapparat, bleibt es beim
        # alten Verhalten.
        if not self.melder and k.cfg["kanaele"]:
            return
        # .249 (Kosinus-raus): Worte aus der einen Quelle; Rohzahl nur im
        # Stil 'worte_zahlen' (alert_stil, Notifications-Option).
        from core import vertrauen as _vt
        text = _sprache.t("meldung.wache.name_satz", name=person,
                          wort=_vt.wort_sprachig(cos, self.win_thresh),
                          n=stimmen)
        if str(self.cfg.get("alert_stil") or "worte") == "worte_zahlen":
            # §8.8: Format-Spezifika (:.2f) NIE in den Textwert — hier
            # vorformatieren, der Schluessel kennt nur {cos}.
            text += " " + _sprache.t("meldung.wache.name_zahl",
                                     cos=f"{cos:.2f}")
        bild = None
        ablage = self._ablage_sichern(k)
        if ablage:
            stempel = time.strftime("%Y%m%d_%H%M%S",
                                    time.localtime(self.wanduhr()))
            sauber = re.sub(r"[^A-Za-z0-9._-]", "_", person)[:40]
            # .313: die Fundstelle sichtbar machen — Rechteck um die Box des
            # besten Fundes (vorher: unmarkiertes Vollbild, bei 20-px-Gesichtern
            # sah der Nutzer einen leeren Garten).
            bild = self._bild_schreiben(
                k, os.path.join(ablage, f"{stempel}_NAME_{sauber}.jpg"),
                bild_mit_box(frame, box))
        payload = {"ts": round(self.wanduhr(), 1), "kamera": k.name,
                   "art": "name",
                   # "stufe" ADDITIV (.249, User-Auflage: bestehende
                   # Schluessel byte-gleich — HA-Skripte duerfen nie brechen).
                   "schnell_urteil": {"person": person,
                                      "cosine": round(cos, 3),
                                      "stimmen": stimmen,
                                      "preliminary": True,
                                      "stufe": _vt.stufe(cos,
                                                         self.win_thresh)}}
        if not k.cfg["kanaele"]:
            # .245: Journal-Zeile statt Versand — EINE Zeile, kanal 'none'
            # (nie aus Config waehlbar, KANAELE_ERLAUBT bleibt ohne 'none').
            self._melde_protokoll(k.name, "alert", "none", zusatz=text,
                                  person=person, bild=self._bild_rel(bild))
            return

        # .319: Push-Kanaele nur, wenn der Melde-Anker offen ist; MQTT immer.
        # Der Anker wird hier NICHT neu gesetzt — das bleibt allein Sache des
        # Triggers (_trigger), sonst verschoebe eine Namens-Meldung die Ruhe
        # der Stufe 1 und die beiden Stufen wuerden sich gegenseitig
        # aushungern. Gelesen wird derselbe Wert, den der Trigger setzt.
        mono_jetzt = self.jetzt()
        push_offen = melde_erlaubt(k, mono_jetzt)
        if not push_offen:
            self._klog(k, f"NAME [{person}]: push suppressed, quiet for "
                          f"{k.melde_bis_mono - mono_jetzt:.0f} s more "
                          f"(MQTT and journal unaffected)")

        def job():
            for kanal in k.cfg["kanaele"]:
                if kanal != "mqtt" and not push_offen:
                    continue                  # gedrosselt: nur der Versand
                try:
                    if self._kanal_senden(k, kanal, text, bild, None, payload):
                        self._melde_protokoll(k.name, "alert", kanal,
                                              zusatz=text, person=person,
                                              bild=self._bild_rel(bild))
                except Exception as e:
                    self._fehler_log((kanal, k.name),
                                     f"{k.name}: {kanal} failed (Name): "
                                     f"{type(e).__name__}: {e}")
            if not push_offen:
                # Die Live-Sicht darf den Auftritt nicht verlieren (QS-Auflage):
                # eine Journal-Zeile mit kanal 'none' wie im kanallosen Fall.
                self._melde_protokoll(k.name, "alert", "none", zusatz=text,
                                      person=person, bild=self._bild_rel(bild))
        self._thread_starten(f"live-name-{k.name}", job)

    def _trigger(self, k, info, mono):
        stempel = time.strftime("%Y%m%d_%H%M%S", time.localtime(self.wanduhr()))
        t_nr = info["treffer"]
        kandidaten = sorted(((sc, fc) for _t, _bx, (_fr, fc, sc) in info["kette"]
                             if _fr is not None),
                            key=lambda x: -x[0])
        with k.lock:
            if k.auftritt:
                k.auftritt["trigger"] += 1
        p_ok, p_det = True, None
        if self.defaults["pose_gate"]:
            p_ok, p_det = pose_bestaetigt(info["kette"], log=lambda z: self._klog(k, z),
                                          kopf_schwelle=self.defaults["pose_kopf"])
            if p_det and "grund" in p_det and "kopf_max" not in p_det:
                # Pose-Gate laeuft NICHT (Modell nicht ladbar o. ae.) — LAUT
                # statt der stillen "[Pose-Kopf None]"-Zeile (Lens-A M6):
                # gedrosselte Log-Warnung + Engine-Stoerungs-Selbstmeldung.
                self._fehler_log(("pose_gate",),
                                 f"Pose-Gate laeuft NICHT ({p_det['grund']}) — "
                                 f"Trigger melden UNGEFILTERT (jede Katze meldet)")
                self._stoerung_global(f"pose gate unavailable: {p_det['grund']}")
        praefix = "" if p_ok else "verworfen_"
        # .32x (User 22.08.: "gar nicht erst schreiben"): der Pose-Sieb-Ausschuss
        # ist reine Nachpruef-Diagnose — die Anzeige zeigt ihn nie, und er ist der
        # groesste Einzelposten unter <data_dir>/live/ (gemessen 1068 Dateien
        # hier, auf der Testanlage 61 GB in neun Tagen). Er wird deshalb per
        # Vorgabe nur noch GEZAEHLT (k.verworfen_pose, /live und Protokoll), nicht
        # gespeichert. Wer eine Fehlersuche fuehrt, schaltet ihn mit
        # live_verworfen_speichern wieder an.
        if not p_ok and not self.cfg.get("live_verworfen_speichern"):
            with k.lock:
                k.burst.karenz_aufheben(info["track"])
            k.verworfen_pose += 1
            self._klog(k, f"TRIGGER #{t_nr} [T{info['track']}] VERWORFEN (kein "
                          f"Mensch im Bild): Pose-Kopf hoechstens "
                          f"{(p_det or {}).get('kopf_max')} — keine Meldung, keine "
                          f"Karenz, kein Bild (live_verworfen_speichern=off)")
            return
        # K-1 (Sched-R4): die Beweisbild-Ablage darf die MELDUNG nie kosten —
        # volle Platte (ENOSPC-Klasse) schlug hier VOR _meldung_starten zu,
        # und der Alarm zu diesem Trigger ging verloren. Lokal gefangen:
        # ohne Ablage geht die Meldung trotzdem raus, nur ohne Beweisbild.
        ablage = self._ablage_sichern(k)
        bestes = None
        for nr, (_t, _bx, nutzlast) in enumerate(info["kette"], 1):
            if ablage is None:
                break
            if not nutzlast or nutzlast[0] is None:
                continue
            pfad = self._bild_schreiben(
                k, os.path.join(ablage, f"{praefix}{stempel}_T{t_nr}_{nr}.jpg"),
                bild_mit_box(nutzlast[0], _bx))     # .313: Fundstelle markiert
            if pfad:
                bestes = pfad
        if not p_ok:
            with k.lock:
                k.burst.karenz_aufheben(info["track"])
            k.verworfen_pose += 1
            self._klog(k, f"TRIGGER #{t_nr} [T{info['track']}] VERWORFEN (kein "
                          f"Mensch im Bild): Pose-Kopf hoechstens "
                          f"{(p_det or {}).get('kopf_max')} — keine Meldung, keine Karenz")
            return
        # .313: ab hier ist ein Mensch bestaetigt (Pose-Gate bestanden oder aus) —
        # die Namens-Stufe darf fuer diesen Auftritt feuern (aufgelaufene
        # Stimmen sofort, spaetere je Frame).
        with k.lock:
            if k.auftritt is not None:
                k.auftritt["mensch_bestaetigt"] = True
        _kf = next((nl[0] for _t, _bx, nl in reversed(info["kette"]) if nl and nl[0] is not None), None)
        if _kf is not None:
            self._namens_pending_feuern(k, _kf)
        u_text, u_person = None, None
        if self.refs and self.win_thresh is not None:
            try:
                u_text, u_person, _c = schnell_urteil(self.refs, kandidaten,
                                                      self.win_thresh)
            except Exception as e:
                self._klog(k, f"Schnell-Urteil entfaellt: {type(e).__name__}: {e}")
        beste_score = kandidaten[0][0] if kandidaten else 0.0
        pose_zusatz = ""
        if p_det:
            if "kopf_max" in p_det:
                pose_zusatz = f" [Pose-Kopf {p_det['kopf_max']}]"
            else:
                pose_zusatz = f" [Pose-Gate AUS: {p_det.get('grund')}]"
        self._klog(k, f"TRIGGER #{t_nr} [T{info['track']}]: {len(info['kette'])} "
                      f"konsistente Funde in {info['spanne']:.2f} s, Latenz "
                      f"{info['latenz_ms']:.0f} ms, bester Score {beste_score:.2f}"
                      + pose_zusatz
                      + (f" — {u_text}" if u_text else ""))
        k.letzter_trigger_wand = self.wanduhr()
        if not melde_erlaubt(k, mono):
            self._klog(k, f"Meldung unterdrueckt (min interval, noch "
                          f"{k.melde_bis_mono - mono:.0f} s)")
            return
        k.melde_bis_mono = mono + k.cfg["wieder_scharf_s"]
        # .251 (Kosinus-raus M6, User-Screenshot 17.08.): Detektions-Score +
        # Latenz sind Technik-Zahlen — im Worte-Stil raus aus dem Push, im
        # Stil 'worte_zahlen' bleiben sie dran (Payload traegt sie IMMER).
        # Sprach-Stufe 4 (Eintrittspunkt (c)): der PUSH-Text ist sprachfaehig;
        # {n} war schon im Original ein echter Plural (face/faces) -> t_n.
        # §8.8: Sekunden/Score/Latenz kommen vorformatiert aus dem Code.
        _sprache.aktivieren()
        text = _sprache.t_n("meldung.wache.funde", len(info["kette"]),
                            sek=f"{info['spanne']:.1f}")
        if str(self.cfg.get("alert_stil") or "worte") == "worte_zahlen":
            text += " " + _sprache.t("meldung.wache.funde_zahl",
                                     score=f"{beste_score:.2f}",
                                     ms=f"{info['latenz_ms']:.0f}")
        if u_text:
            # u_text bleibt ENGLISCH (Schnell-Urteil, s. TEXT_URTEIL_*-
            # Grenz-Marker: derselbe String ist MQTT-Payload-Wert).
            text += f" — {u_text}"
        payload = {"ts": round(self.wanduhr(), 1), "kamera": k.name,
                   "score": round(beste_score, 3), "bild_anzahl": len(info["kette"])}
        if u_text:
            # .190: person ALS FELD (Today-Kartenreihe + MQTT-Konsumenten) —
            # None bei "unknown"; das preliminary-Flag bleibt die Wahrheit.
            payload["schnell_urteil"] = {"text": u_text, "preliminary": True,
                                         "person": u_person}
        with k.lock:
            rb = list(k.rueckblick)
        # Video-Pfad unabhaengig von der Ablage-Pruefung bauen (K-1): scheitert
        # der Ordner, faengt video_bauen im Melde-Thread das selbst (vid=None).
        self._meldung_starten(k, text, bestes, rb, payload,
                              os.path.join(self.live_dir, k.name,
                                           f"{stempel}_T{t_nr}.mp4"))
        k.gemeldet += 1

    def _ablage_sichern(self, k):
        """Beweisbild-Ordner der Kachel anlegen -> Pfad oder None. K-1 (Sched-
        R4): ein Platten-/IO-Fehler hier ist eine Log-Zeile, nie der Verlust
        der Personen-Meldung — der Aufrufer meldet dann ohne Beweisbild."""
        ablage = os.path.join(self.live_dir, k.name)
        try:
            os.makedirs(ablage, exist_ok=True)
            return ablage
        except OSError as e:
            self._klog(k, f"Bild-Ablage nicht moeglich ({e}) — Meldung geht "
                          f"ohne Beweisbild raus")
            return None

    def _bild_schreiben(self, k, pfad, bild):
        """EIN Beweisbild schreiben -> Pfad bei ERFOLG, sonst None (geloggt).
        K-1-Rest (Widerleger 12.08., gemessen): im haeufigeren ENOSPC-Verlauf
        existiert der Ordner laengst und erst der SCHREIB scheitert —
        cv2.imwrite WIRFT dann nicht, sondern liefert False. Ohne die
        Rueckgabe-Pruefung truege die Meldung einen Pfad auf eine nicht
        existierende Datei und der Ausfall waere voellig still."""
        try:
            if cv2.imwrite(pfad, bild, [cv2.IMWRITE_JPEG_QUALITY, 90]):
                return pfad
            fehler = f"imwrite=False ({pfad})"
        except Exception as e:
            fehler = str(e)
        # GEDROSSELT statt _klog je Bild (K-1-Rest, Fix-Zyklus 12.08.): bei
        # voller Platte schrieb jeder Trigger bis zu kette-viele ungedrosselte
        # Zeilen — eine je Drosselfenster reicht, der Ausfall bleibt laut.
        self._fehler_log(("bild_ablage", k.name),
                         f"live {k.name}: Bild-Ablage fehlgeschlagen: {fehler}")
        return None

    def _vorschau_schreiben(self, k, frame, mono):
        """Vorschau-JPEG je Kachel fuer den Live-Reiter (User-Wunsch 13.08.:
        sehen, WAS DER WAECHTER SIEHT — deshalb der VERARBEITETE Frame in
        Waechter-Skala aus dem Detektor-Thread, nicht Frigates Bild).
        Anzeige-Weg, nie Urteils-Pfad. Gedrosselt auf VORSCHAU_S; atomar per
        tmp+os.replace (ein halb geschriebenes JPEG waere ein kaputtes <img>
        im Reiter); Fehler laufen in die GEDROSSELTE Fehlerzeile
        (ENOSPC-Klasse wie _bild_schreiben, nie Engine-Ende)."""
        if mono - k.vorschau_mono < VORSCHAU_S:
            return
        if not VORSCHAU_NAME_RE.match(k.name):
            return                     # nie einen Pfad aus Fremdnamen bauen
        k.vorschau_mono = mono
        try:
            d = os.path.join(self.cfg.get("data_dir")
                             or os.path.join(WURZEL, "verify_data"),
                             "live", "preview")
            os.makedirs(d, exist_ok=True)
            ok, buf = cv2.imencode(".jpg", frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, 78])
            if not ok:
                raise RuntimeError("imencode=False")
            tmp = os.path.join(d, f".{k.name}.tmp")
            with open(tmp, "wb") as f:
                f.write(buf.tobytes())
            os.replace(tmp, os.path.join(d, f"{k.name}.jpg"))
        except Exception as e:
            self._fehler_log(("vorschau", k.name),
                             f"live {k.name}: Vorschau-Bild fehlgeschlagen: "
                             f"{type(e).__name__}: {str(e)[:120]}")

    def _thread_starten(self, name, ziel):
        """Melde-/Stoerungs-Thread starten UND registrieren (Lens-A M5:
        stop() joint die Registrierten — eine angestossene Meldung geht beim
        SIGTERM nicht mehr still verloren). Tote werden dabei ausgekehrt."""
        t = threading.Thread(target=ziel, name=name, daemon=True)
        with self._melde_lock:
            self._melde_threads = [x for x in self._melde_threads if x.is_alive()]
            self._melde_threads.append(t)
        t.start()
        return t

    def _meldung_starten(self, k, text, bild, rueckblick, payload, video_pfad):
        """Versand im Thread (Transcode+Upload blockieren die Detektion nicht,
        telegram_melden-Muster). Kanalausfall ist nie Waechterausfall.
        .245 (User-Go 17.08.): ohne Meldekanal wird das Ergebnis JOURNALT
        statt verworfen (kanal 'none' — Anzeige ja, Versand nein); die
        Recognized-live-Reihe und /live_alerts lesen genau dieses Protokoll
        und blieben auf kanal-losen Installationen sonst fuer immer leer."""
        if not k.cfg["kanaele"]:
            sp = payload.get("schnell_urteil") or {}
            self._melde_protokoll(k.name, "alert", "none", zusatz=text,
                                  person=sp.get("person") or "",
                                  bild=self._bild_rel(bild))
            return
        if not self.melder:
            return

        def job():
            vid = None
            if "telegram" in k.cfg["kanaele"] and len(rueckblick) > 1:
                try:
                    zeiten = [t for t, _ in rueckblick]
                    fps = (len(zeiten) - 1) / max(zeiten[-1] - zeiten[0], 0.1)
                    # Rueckblick liegt als YUV (K8) — Konvertierung erst hier,
                    # je Meldung statt je Frame.
                    frames = [cv2.cvtColor(y, cv2.COLOR_YUV2BGR_I420)
                              if y.ndim == 2 else y for _, y in rueckblick]
                    vid = video_bauen(frames, video_pfad, fps)
                except Exception as e:
                    self._fehler_log(("video", k.name), f"{k.name}: Rueckblick-Video "
                                                        f"fehlgeschlagen: {e}")
            for kanal in k.cfg["kanaele"]:
                try:
                    if self._kanal_senden(k, kanal, text, bild, vid, payload):
                        # Baustein B: NUR die real angenommene Meldung landet
                        # im Protokoll (eine Quelle, kein Doppelzaehlen).
                        # Einzige Ausnahme seit .245: kanal-lose Installation
                        # -> EINE 'none'-Zeile (oben, vor dem job).
                        sp = payload.get("schnell_urteil") or {}
                        self._melde_protokoll(k.name, "alert", kanal,
                                              zusatz=text,
                                              person=sp.get("person") or "",
                                              bild=self._bild_rel(bild))
                except Exception as e:
                    # gedrosselt, nicht je Trigger neu (§6)
                    self._fehler_log((kanal, k.name),
                                     f"{k.name}: {kanal} failed: {type(e).__name__}: {e}")
        self._thread_starten(f"live-melde-{k.name}", job)

    def _kanal_senden(self, k, kanal, text, bild, vid, payload):
        """EINEN Kanal einer Personen-Meldung senden -> True NUR, wenn der
        Kanal sie ANGENOMMEN hat (Sender-Rueckgabe; False auch bei fehlender
        Konfiguration). Eigener Baustein, damit der Mutations-Selbsttest die
        ok-Wahrheit fassen kann (Baustein B: kein Zaehlen von Fehlversand)."""
        if kanal == "pushover":
            return bool(self.melder.push(k.name, text, bild))
        if kanal == "telegram":
            return bool(self.melder.telegram(k.name, vid, text, bild))
        if kanal == "mqtt":
            return bool(self.melder.mqtt(k.name, payload))
        return False

    def _melde_protokoll(self, kamera, art, kanal, zusatz="", person="",
                         bild=""):
        """Buchhaltungs-Zeile je real rausgegangener Meldung (Baustein B:
        Today-/System-Zaehler des Dienstes lesen diese EINE Quelle).
        IO-Fehler kosten nie die Meldung — nur eine gedrosselte Logzeile.
        zusatz (.188): Meldetext gekappt. person/bild (.190, User: die
        Today-Reihe 'Recognized live' braucht WEN und das Beweisbild):
        Schnell-Urteils-Name und der DATA-DIR-RELATIVE Bildpfad (Vertrag
        ALARMBILD_RE — der Dienst-Endpunkt serviert nur, was dem Muster
        genuegt). Alte Zeilen ohne die Felder bleiben gueltig."""
        try:
            eintrag = {"ts": round(self.wanduhr(), 1),
                       "kamera": kamera, "art": art, "kanal": kanal}
            if zusatz:
                eintrag["zusatz"] = str(zusatz)[:140]
            if person:
                eintrag["person"] = str(person)[:60]
            if bild and ALARMBILD_RE.match(bild):
                eintrag["bild"] = bild
            melde_protokoll_zeile(self.live_dir, eintrag)
        except Exception as e:
            self._fehler_log(("melde_protokoll",),
                             f"Melde-Protokoll fehlgeschlagen: {e}")

    def _bild_rel(self, pfad):
        """Beweisbild-Pfad -> data_dir-relativ ('live/<kamera>/<datei>.jpg')
        fuer das Melde-Protokoll; None/fremde Pfade -> '' (nie raten)."""
        if not pfad:
            return ""
        wurzel = self.cfg.get("data_dir") or os.path.join(WURZEL, "verify_data")
        try:
            rel = os.path.relpath(pfad, wurzel)
        except ValueError:
            return ""
        return rel if ALARMBILD_RE.match(rel) else ""

    # ---------------------------------------------------------------- Status/Watchdog
    def _status_lauf(self):
        """EIN Schreiber je 2 s fuer ALLE Kacheln (§7 QS-Fund: nie je Bild,
        nie je Kachel einzeln); dazu Watchdog, Auftritts-Ende, Stoerungs-
        Selbstmeldung und die 60-s-Verbrauchszeile.

        Das try liegt IN der Schleife (Lens B1-Folgefix, gemessen: eine einzige
        Exception beendete vorher Herzschlag, Watchdog, Stoerungs-Selbstmeldung
        und Verbrauch ENDGUELTIG, die Engine lief blind weiter). Ein Fehler
        kostet jetzt eine Runde und wird gedrosselt geloggt; haeufen sich die
        Fehler, meldet sich der Beobachtungs-Thread DROSSELFREI selbst — er
        verstummt nie still. Der finally-Schreib haelt die Status-Wahrheit
        auch auf dem Todespfad aktuell (B3: engine:'ok' nach Engine-Tod)."""
        letzter_verbrauch = -1e18
        fehler_serie = 0
        try:
            while not self.stop_ev.wait(HERZSCHLAG_S):
                try:
                    mono = self.jetzt()
                    self._config_pruefen()       # Store-Reload je Waechter (§8)
                    self._kommando_pruefen()     # Auftraege des Dienstes (UI)
                    self._status_runde(mono)
                    if mono - letzter_verbrauch >= VERBRAUCH_S:
                        letzter_verbrauch = mono
                        self._verbrauch_zeile()
                    self._status_schreiben(mono)
                    fehler_serie = 0
                except Exception as e:
                    import traceback
                    fehler_serie += 1
                    self._fehler_log(("status_runde",),
                                     f"Status-Runde fehlgeschlagen "
                                     f"({fehler_serie}. Mal in Folge): "
                                     f"{type(e).__name__}: {e}")
                    self.log(traceback.format_exc())
                    # K-2-Rest (Fix-Zyklus 12.08.): bei DAUERdefekt nicht genau
                    # EINE Selbstmeldung — die dritte in Folge geht drosselfrei,
                    # danach meldet jeder weitere Fehltakt ueber die normale
                    # Drossel (1x je STOERUNG_LOG_DROSSEL_S) WEITER, solange
                    # der Defekt anhaelt. Der Beobachtungs-Thread verstummt
                    # damit auch ueber Stunden nie endgueltig.
                    if fehler_serie >= 3:
                        self._stoerung_global(
                            f"status/watchdog loop failing repeatedly "
                            f"({fehler_serie} rounds in a row): "
                            f"{type(e).__name__}: {str(e)[:120]}",
                            drosselfrei=(fehler_serie == 3))
        finally:
            try:
                self._status_schreiben(self.jetzt())
            except Exception:
                pass

    def _status_runde(self, mono):
        """Der Inhalt EINER Beobachtungs-Runde (getrennt, damit ein Fehler
        genau eine Runde kostet — s. _status_lauf)."""
        # Liefer-Watchdog: "kein Bild" ist IMMER ein behandelter Zustand.
        for k in watchdog_faellige(self.kacheln.values(), mono, self.watchdog_s):
            k.watchdog_kills += 1
            # Ehrlicher Alterswert (Lens-A M1: vorher stand die Ausfalldauer
            # der VORIGEN Verbindung in der Zeile): Zeit ohne Bild AUF DIESER
            # Verbindung, nie laenger als die Verbindung selbst.
            anker = max(k.letztes_bild_mono or -1e18, k.verbunden_mono or -1e18)
            self._klog(k, f"WATCHDOG: kein Bild seit {mono - anker:.0f} s auf "
                          f"dieser Verbindung — Leser wird gekillt, Reconnect "
                          f"uebernimmt")
            if k.kill:
                try:
                    k.kill()
                except Exception:
                    pass
        for k in self.kacheln.values():
            # Stuetzpunkt des gleitenden Liefer-fps-Fensters (aktiv_fps):
            # (mono, bilder) je Status-Takt, Spanne FPS_FENSTER_S.
            k.fps_fenster.append((mono, k.bilder))
            while k.fps_fenster and mono - k.fps_fenster[0][0] > FPS_FENSTER_S:
                k.fps_fenster.popleft()
            # Auftritts-Ende (User-Zeit a, Anker letzter Fund).
            with k.lock:
                a = k.auftritt
                if a and mono - a["letzter_fund_mono"] > k.cfg["ende_ohne_gesicht_s"]:
                    self._klog(k, f"Auftritt #{k.auftritte} beendet "
                                  f"({a['funde']} Funde, {a['trigger']} Trigger, "
                                  f"{mono - a['seit_mono']:.0f} s)")
                    k.auftritt = None
            # Stoerungs-Selbstmeldung (§11 Entscheid 2) + Entwarnung — Anker
            # ist LIEFERUNG, nicht Verbindungszustand (B2-Fix, stoerung_takt).
            ereignis = stoerung_takt(k, mono, self.watchdog_s)
            if ereignis == "melden":
                self._stoerung_senden(
                    k, f"disturbed: no frames for {k.stoer.dauer(mono):.0f}s "
                       f"(state {k.zustand}"
                       + (f", {k.zustand_grund}" if k.zustand_grund else "")
                       + f"), reconnect attempts {k.abrisse + k.reconnect_fehler}")
            elif ereignis == "entwarnung":
                self._stoerung_senden(k, "recovered — frames flowing again")
            # K-3: haengt ein zurueckgehaltenes Stoerungs-Ereignis nach Ablauf
            # des Mindestabstands noch, geht es JETZT (mit Flatter-Zaehler)
            # raus — sonst bliebe z. B. eine unterdrueckte Entwarnung fuer
            # immer aus und der letzte gemeldete Zustand waere eine Luege.
            if (k.stoer_letzter_text is not None
                    and mono - k.stoer_sende_mono >= STOERUNG_LOG_DROSSEL_S):
                self._stoerung_senden(k, k.stoer_letzter_text)
        # Ein-Stream-RSS-Messfenster schliessen (geoeffnet in start(), M9).
        if self._mess_start_mono is not None and mono - self._mess_start_mono >= 60.0:
            self.vermessung.stream_messung_ende()
            self._mess_start_mono = None
        # NOT-AUS der Auftrags-Strecke (Engine-B1, eigener Baustein — auch
        # damit der Harnisch ihn fassen kann).
        self._auftrag_notaus(mono)

    def _auftrag_notaus(self, mono):
        """NOT-AUS der Auftrags-Strecke (Engine-B1, Messreihe des Widerlegers:
        der alte Not-Aus raeumte nur die BUCHHALTUNG — der Thread lief weiter,
        ein zweiter Auftrag startete, 2 gleichzeitige erkennen(), und das
        Zombie-finally raeumte den Nachfolger ab). Drei Stufen:
         1. Frist um -> Mess-/Test-Verbindung KILLEN (a['kill']) + Abbruch-
            Signal + Fehler-Quittung. Der Auftrag bleibt BESETZT: kein
            zweiter Start, solange der Thread nicht WIRKLICH geendet hat.
         2. Der Thread endet (Queue-Deadline/EOF nach dem Kill) — sein
            generations-gebundenes finally raeumt Slot + Pause selbst.
         3. Endet er trotz Kill nicht binnen AUFTRAG_ABBRUCH_GRACE_S, wird
            der Slot ZWANGS-geloest (die Generation schuetzt den Nachfolger
            vor dem Zombie-finally) — LAUT + Stoerung, Waechter laufen weiter.
        Ausserdem: Pause ohne lebenden Auftrag wird aufgeraeumt (Randfall).

        DROSSEL-SCHLUESSEL JE STUFE (MUSS-N1, RECHECK 12.08. gemessen: alle
        drei Stufen teilten ('auftrag',) — zwischen Stufe 2 und 3 liegen nur
        AUFTRAG_ABBRUCH_GRACE_S, weit unter der 600-s-Drossel, die ZWANGS-
        Zeile erschien deshalb NIE; mit Engine-Stoerungs-Vorgeschichte fiel
        auch der Push in die Drossel. Das ist die Lens-A-B3-Klasse, fuer die
        drosselfrei=True erfunden wurde: die Zwangs-Loesung ist ein
        terminales, seltenes Ereignis wie die Todes-Meldung — Log UND Push
        muessen raus)."""
        with self._auftrag_lock:
            a = self._auftrag
        if a is None:
            if self._pause_ausser:
                self._pause_ausser = None
                self._fehler_log(("auftrag", "pause"),
                                 "live: Pause ohne laufenden Auftrag vorgefunden "
                                 "— aufgehoben (Waechter laufen weiter)")
            return
        if mono - a["start_mono"] <= AUFTRAG_TIMEOUT_S:
            return
        if a["abbruch_mono"] is None:
            a["abbruch_mono"] = mono
            a["abbruch"].set()
            if a.get("kill"):
                try:
                    a["kill"]()
                except Exception:
                    pass
            self._auftrag_phase("abbruch")
            self.auftrag_ergebnisse.setdefault(a["kamera"], {})[a["art"]] = {
                "ok": False, "art": a["art"], "ts": round(self.wanduhr(), 1),
                "fehler": (f"job timed out after {AUFTRAG_TIMEOUT_S:.0f}s "
                           f"— aborted, watchers resume when the job thread "
                           f"has ended")}
            self._fehler_log(("auftrag", "abbruch"),
                             f"live {a['art']} {a['kamera']}: haengt seit "
                             f"{AUFTRAG_TIMEOUT_S:.0f} s — ABBRUCH (Verbindung "
                             f"gekillt), warte auf das echte Thread-Ende")
            return
        t = a.get("thread")
        if t is not None and t.is_alive():
            if mono - a["abbruch_mono"] > AUFTRAG_ABBRUCH_GRACE_S:
                with self._auftrag_lock:
                    if self._auftrag is a:
                        self._auftrag = None
                        self._pause_ausser = None
                self._fehler_log(("auftrag", "zwang"),
                                 f"live {a['art']} {a['kamera']}: Thread endet "
                                 f"trotz Kill nicht — Slot ZWANGS-geloest "
                                 f"(Zombie bleibt generations-isoliert), "
                                 f"Waechter laufen weiter")
                self._stoerung_global(
                    f"live job thread for {a['kamera']} did not end after "
                    f"abort — detached as zombie, watchers resumed",
                    drosselfrei=True)
            return
        # Thread ist beendet; falls sein finally uebersprungen wurde
        # (Interpreter-Abriss), hier generations-gebunden nachraeumen.
        with self._auftrag_lock:
            if self._auftrag is a:
                self._auftrag = None
                self._pause_ausser = None

    def _status_schreiben(self, mono):
        # K-2 (Sched-R5): das try umfasst den GANZEN Aufbau, nicht nur den
        # Schreib — ein unerwarteter Kachel-Zustand machte den Wahrheits-
        # Schreib sonst STILL wirkungslos (der finally-Aufrufer in
        # _status_lauf faengt alles weg). Der Fehlschlag wird geloggt
        # (gedrosselt) UND WEITERGEWORFEN (Fix-Zyklus 12.08.): die
        # Beobachtungs-Schleife muss ihn ZAEHLEN, sonst blieben fehler_serie
        # auf 0 und die drosselfreie Selbstmeldung nach 3 Fehlern in Folge
        # aus (B1b-Fix der Vorrunde; Widerleger gemessen: 0 statt 1 Selbst-
        # meldungen). Die Schluck-Aufrufer (finally in _status_lauf, stop())
        # fangen den Wurf selbst — die Logzeile ist dort schon geschrieben.
        try:
            self._status_schreiben_innen(mono)
        except Exception as e:
            self._fehler_log(("status",), f"Status-Schreib fehlgeschlagen: {e}")
            raise

    def _kapazitaet(self):
        """-> (anzahl, grund). Seit .196 ohne Lastmodell (User: Messwerte
        informieren, sie entscheiden nicht): der Deckel ist die harte Wand
        bzw. der RAM-Boden (echter cgroup-Messwert) — dieselben zwei
        Notbremsen wie in slot_pruefen, per Aufzaehlung bis zur ersten
        Verweigerung."""
        n = sum(1 for k in self.kacheln.values()
                if k.zustand in ("aktiv", "gestoert"))
        grund = ""
        while True:
            ok, grund = self.vermessung.slot_pruefen(n)
            if not ok:
                break
            n += 1
        return n, grund

    def _status_schreiben_innen(self, mono):
        slots = self.vermessung.status()
        emax, egrund = self._kapazitaet()
        slots["effektiv_max"] = emax          # dynamischer Deckel (UI-M4/C1)
        slots["effektiv_grund"] = egrund      # die Grenze, mit Zahlen
        d = {"ts": round(self.wanduhr(), 1), "pid": os.getpid(),
             "start_ts": round(self._start_wand or 0, 1),
             "herzschlag_s": HERZSCHLAG_S,
             "engine": ("fehler: " + self.engine_fehler) if self.engine_fehler else "ok",
             # Quittung des zuletzt VERARBEITETEN Kommandos (Engine-M3): der
             # Dienst weist weitere Auftraege ab, solange die Kommando-Datei
             # ein ts traegt, das hier noch nicht steht — nie wieder stilles
             # Ueberschreiben im 2-s-Fenster.
             "kommando_ts": self._kommando_ts,
             "scheduler": self.scheduler.status(),
             "slots": slots,
             "verweigert": dict(self.verweigert),
             "kacheln": {}}
        # Laufender Auftrag (Quelltest/Last-Messung): Phase + Restsekunden
        # fuer den UI-Countdown (User-Auflage: der User sieht jederzeit, WAS
        # laeuft und wie lange noch) + die pausierten Waechter, ehrlich —
        # pausiert nur, wenn die Pause WIRKLICH steht (Quelltests pausieren
        # seit dem Fix-Zyklus nicht mehr; UI-KANN 11).
        with self._auftrag_lock:
            a = dict(self._auftrag) if self._auftrag else None
        if a:
            rest = None
            if a.get("bis_mono") is not None:
                rest = max(0.0, round(a["bis_mono"] - mono, 1))
            d["auftrag"] = {"art": a["art"], "kamera": a["kamera"],
                            "phase": a["phase"], "rest_s": rest,
                            "dauer_s": a.get("dauer_s"),
                            "start_ts": a.get("start_ts"),
                            "pausiert": (sorted(self.kacheln)
                                         if self._pause_ausser else [])}
        if self.auftrag_ergebnisse:
            d["auftraege"] = {kam: dict(erg) for kam, erg
                              in self.auftrag_ergebnisse.items()}
        for k in self.kacheln.values():
            alter = (round(mono - k.letztes_bild_mono, 1)
                     if k.letztes_bild_mono is not None else None)
            d["kacheln"][k.name] = {
                "zustand": k.zustand, "grund": k.zustand_grund,
                "letztes_bild_ts": k.letztes_bild_wand,
                "letztes_bild_alter_s": alter,
                "letzter_trigger_ts": k.letzter_trigger_wand,
                "bilder": k.bilder, "eingereiht": k.eingereiht,
                "geprueft": k.geprueft,          # WIRKLICH detektiert (Lens-A M2)
                "trigger": k.burst.treffer, "gemeldet": k.gemeldet,
                "verworfen_pose": k.verworfen_pose,
                "verarbeitungs_fehler": k.verarbeitungs_fehler,
                "auftritte": k.auftritte, "auftritt_aktiv": k.auftritt is not None,
                "abrisse": k.abrisse, "reconnect_fehler": k.reconnect_fehler,
                "watchdog_kills": k.watchdog_kills,
                "gedrosselt": k.gedrosselt,
                "pausiert": k.pausiert,
                "ueberlast_ersetzt": self.scheduler.ersetzt.get(k.name, 0),
                "hw": k.hw, "steckbrief": k.steckbrief,
                "kanaele": k.cfg["kanaele"],
            }
        _atomar_schreiben(self.status_pfad, d)

    def _verbrauch_zeile(self):
        """RSS je 60 s in die Verbrauchsbilanz (Auflage aus 19:17; Prototyp-
        Muster verbrauch.csv) — KEIN Selbst-Abschalten bei Schwellwert, aber
        lautes Warnen uebernimmt der Status/health (§8)."""
        try:
            os.makedirs(self.live_dir, exist_ok=True)
            pfad = os.path.join(self.live_dir, "verbrauch.csv")
            neu = not os.path.exists(pfad)
            with open(pfad, "a") as f:
                if neu:
                    f.write("zeit,epoch,rss_mb,ram_frei_mb,kacheln,auslastung,"
                            "drossel_stufe,det_ms\n")
                frei, _q = self.vermessung.ram_holen()
                det, _dq = self.vermessung.det_ms_wirksam()
                jetzt_w = self.wanduhr()
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(jetzt_w))},"
                        f"{jetzt_w:.1f},{rss_mb()},"
                        f"{round(frei) if frei is not None else ''},"
                        f"{sum(1 for k in self.kacheln.values() if k.zustand == 'aktiv')},"
                        f"{self.scheduler.auslastung():.3f},{self.scheduler.stufe},"
                        f"{det:.1f}\n")
        except Exception as e:
            self._fehler_log(("verbrauch",), f"Verbrauchszeile fehlgeschlagen: {e}")

    # ---------------------------------------------------------------- Hilfen
    def _stoerung_senden(self, k, text):
        """Stoerung/Entwarnung eines Waechters ueber SEINE Kanaele — im Thread,
        damit der Status-Takt nicht am Kanal haengt.

        K-3 (Sched-R3, gemessen: Sporadik-Kamera mit 1 Bild je 400 s = 18
        Pushes/h): Mindestabstand je Kachel = STOERUNG_LOG_DROSSEL_S —
        dieselbe Konstante, die schon _stoerung_global und die Fehlerzeilen
        drosselt (kein neues Literal, K3-Regel; die Groessenordnung liegt wie
        vom Lens-Bericht verlangt im Minuten-Bereich von wieder_scharf_s).
        Die ERSTE Meldung geht immer sofort; Zurueckgehaltenes wird GEZAEHLT
        und beim naechsten Push als Flatter-Zusammenfassung mitgesandt.
        Haengt ein Ereignis nach Ablauf noch, flusht der Status-Takt es
        (_status_runde) — eine Entwarnung geht nie endgueltig verloren.

        Ehrliche Grenze (Widerleger 12.08., gemessen): der Mindestabstand
        kann auch die ERSTE Meldung einer ECHTEN Stoerung verzoegern — lag
        der letzte Push (z. B. eine Entwarnung) kurz zurueck, kommt
        'disturbed' erst bis zu ~600 s nach dem letzten Bild statt ~302 s
        (Watchdog + STOERUNG_NACH_S). Worst case ~10 statt ~5 Minuten;
        bewusst hingenommen, Preis der 18-Pushes/h-Deckelung."""
        mono = self.jetzt()
        if mono - k.stoer_sende_mono < STOERUNG_LOG_DROSSEL_S:
            k.stoer_unterdrueckt += 1
            k.stoer_letzter_text = text
            self._klog(k, f"STOERUNGS-MELDUNG zurueckgehalten (Mindestabstand "
                          f"{STOERUNG_LOG_DROSSEL_S:.0f} s, "
                          f"#{k.stoer_unterdrueckt}): {text}")
            return
        if k.stoer_unterdrueckt:
            text += (f" (flapping: {k.stoer_unterdrueckt} earlier disturbance/"
                     f"recovery events suppressed)")
        k.stoer_sende_mono = mono
        k.stoer_unterdrueckt = 0
        k.stoer_letzter_text = None
        self._klog(k, f"STOERUNGS-MELDUNG: {text}")
        if not self.melder:
            return

        def job():
            try:
                r = self.melder.stoerung_kachel(k.name, text, k.cfg["kanaele"])
                # tolerant: echte Melder liefern (gesendet, fehler), aeltere
                # Harnisch-Stubs nur die Fehlerliste (Baustein B, additiv).
                gesendet, fehler = (r if isinstance(r, tuple) and len(r) == 2
                                    else ([], r or []))
                for kanal in gesendet:
                    self._melde_protokoll(k.name, "stoerung", kanal)
                for fz in fehler or []:
                    self._fehler_log(("stoerung", k.name), f"{k.name}: {fz}")
            except Exception as e:
                self._fehler_log(("stoerung", k.name), f"{k.name}: {e}")
        self._thread_starten(f"live-stoer-{k.name}", job)

    def _stoerung_global(self, text, drosselfrei=False):
        """Engine-weite Stoerung, hoechstens 1x je 10 min — AUSSER drosselfrei:
        die Todes-/Beobachtungs-Ausfall-Meldung MUSS raus (Lens-A B3, gemessen:
        die 'Engine tot'-Meldung fiel in die Drossel der Sekunden zuvor
        gesendeten failure-Meldung und ging NIE raus)."""
        mono = self.jetzt()
        if not drosselfrei and mono - self._stoer_global_mono < STOERUNG_LOG_DROSSEL_S:
            return
        self._stoer_global_mono = mono
        self.log(f"!! STOERUNG (engine): {text}")
        if not self.melder:
            return

        def job():
            try:
                r = self.melder.stoerung_global(f"live engine: {text}")
                gesendet = (r[0] if isinstance(r, tuple) and len(r) == 2
                            else [])           # Stub-Toleranz wie stoerung_kachel
                for kanal in gesendet:
                    self._melde_protokoll("", "stoerung", kanal)
            except Exception as e:
                self._fehler_log(("stoerung", "global"), f"global: {e}")
        self._thread_starten("live-stoer-global", job)

    def _kachel_fehler(self, k, quelle, text):
        """B4-Klassifikation: IO-/Verarbeitungsfehler einer Kachel — Stoerung
        MIT Grund an der Kachel (Log + Selbstmeldung ueber IHRE Kanaele,
        gedrosselt), NIE Engine-Ende, NIE Detektor-Neubau."""
        k.zustand_grund = f"{quelle}: {text}"[:160]
        mono = self.jetzt()
        schluessel = ("kachel_fehler", k.name, quelle)
        if mono - self._fehler_drossel.get(schluessel, -1e18) < STOERUNG_LOG_DROSSEL_S:
            return
        self._fehler_drossel[schluessel] = mono
        self._klog(k, f"!! Verarbeitungs-Fehler ({quelle}): {text}")
        self._stoerung_senden(k, f"processing error ({quelle}): {text}")

    def _fehler_log(self, quelle, zeile):
        mono = self.jetzt()
        if mono - self._fehler_drossel.get(quelle, -1e18) < STOERUNG_LOG_DROSSEL_S:
            return
        self._fehler_drossel[quelle] = mono
        self.log(f"!! {zeile}")

    def _ende_loggen(self, k, ende):
        self._klog(k, f"Track T{ende['track']} ENDE ohne Trigger ({ende['grund']}) "
                      f"nach {ende['dauer']:.1f} s (laengste Kette "
                      f"{ende['max_kette']}/{k.burst.anzahl})")

    def _klog(self, k, zeile):
        """Kachel-Log: Engine-Log UND je Kachel eine wache.log im Datenordner
        (rotiert am Deckel, Prototyp-Muster — Zaehler laufen im Prozess weiter)."""
        self.log(f"live {k.name}: {zeile}")
        try:
            ablage = os.path.join(self.live_dir, k.name)
            os.makedirs(ablage, exist_ok=True)
            pfad = os.path.join(ablage, "wache.log")
            try:
                if os.path.getsize(pfad) > LOG_MAX_MB * 1024 * 1024:
                    os.replace(pfad, pfad + ".1")
            except OSError:
                pass
            with open(pfad, "a") as f:
                f.write(f"{time.strftime('%d.%m %H:%M:%S', time.localtime(self.wanduhr()))} "
                        f"{zeile}\n")
        except Exception:
            pass
