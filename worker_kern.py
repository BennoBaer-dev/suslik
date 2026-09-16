#!/usr/bin/env python3
"""Der WERT-KERN des Prototyp-Workers — backend-frei (E1, 13.09.2026).

HERKUNFT: Dieser Kern ist aus den beiden abgenommenen v8-Prototypen
`worker_gpu.py` (Intel/OpenVINO, md5 e8e6d7b4) und `worker_cuda.py` (NVIDIA/ORT,
md5 5e46e456) HERAUSGEZOGEN, nicht neu geschrieben. Die Funktionen stehen Zeile
fuer Zeile so da, wie sie dort standen; wo beide Dateien dieselbe Funktion trugen
(„wortgleich kopiert", Kopfzeile worker_cuda.py), steht sie jetzt EINMAL. Die
Kopfabschnitte v2-v8 der beiden Prototypen gelten unveraendert weiter — sie
beschreiben, WIE die Werte entstehen; diese Datei beschreibt nur noch, WO.

DER SCHNITT (analysen/worker_neubau.md §1):
  KERN (hier)     Kaskaden-Ablauf, Latten, Detektor-Nachverarbeitung, Thetas und
                  Normierungs-VORSCHRIFTEN, Referenzladen, Score-Rechnung,
                  Kandidaten-Gate, Bildvorrat, persons-Zusammenfassung, Kopfzeile,
                  Auftragsverwaltung (Einzel- und Mehrstrang).
  ENGINE          Graph-/Session-Bau, Decoder-Anbindung, Speicher-Besitz,
                  Formstrategie, Optionen — `engine_ov.py` bzw. `engine_cuda.py`.
Der Kern importiert WEDER openvino NOCH onnxruntime; die Engine kennt keine Latte.

DIE ENGINE-SCHNITTSTELLE, vollstaendig (mehr verlangt der Kern nicht):
  engine.argumente(ap)                  eigene CLI-Schalter anhaengen (Klassenmethode)
  engine.frames(clip, W, H, schritt)    Sample-Frames (i, y, uv) als NV12, kein Rueckfall
  engine.geometrie_bauen(geo)           -> {(W, H): Geometrie}
  engine.kopf_auskunft(graphen)         -> dict fuer die Kopfzeile (darf 'fd' tragen)
  engine.stufen_folge                   die Stufen in Bau-/Rechenreihenfolge
  Geometrie: .W .H .seiten .nm .det_wh .det_scale .zentren .bau_s .bau_geteilt_s
             .satz()   -> der Satz DIESES Rechenstrangs (thread-lokal)
  Satz:      .det(y, uv)              -> die Detektor-Ausgaenge dieses Frames
             .stufe(k, thetas)        -> je Gesicht ein Tupel seiner Ausgabezeilen
             .stufe_fd(thetas, zuege) -> je Gesicht (Punkte [68,3], s_lap, s_lap2)
             .warm()

MATMUL-RAUS (E1, Konzept §1c — die EINE fachliche Aenderung dieses Umbaus):
Die Erkennungs-Stufe der Prototypen trug die Referenz-Matrix als GRAPH-KONSTANTE
und gab fertige Scores zurueck. Damit haette jede Referenz-Aenderung ein Rekompilat
und einen Prozess-Neustart verlangt (Lernlauf: 15 Anker-Gruppen). Jetzt liefert die
r-Stufe nur noch das L2-normierte Embedding [n, 512] (und die Feature-Norm), und der
Score-Matmul samt Maximum je Person laeuft HIER auf der CPU (scores_rechnen, Zeile
fuer Zeile analyze.nn, analyze.py:319-321). Folge, bewusst und gemessen: die Scores
verschieben sich minimal (andere Rechenstelle, auf der iGPU vorher fp16), das
Embedding selbst nicht.

Aufruf: ueber die Huellen worker_gpu.py / worker_gpu_mt.py (Intel) bzw.
worker_cuda.py / worker_cuda_mt.py (CUDA). Deren Argumente sind unveraendert.
"""
import argparse
import collections
import ctypes
import fcntl
import inspect
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import types
import warnings                                          # .528: EINE Bibliotheks-Warnung daempfen, s. u.

# BLAS auf EINEN Thread, BEVOR numpy geladen wird (cv2 zieht es mit) — GEMESSEN im
# E1-Gate 13.09., nicht angenommen:
#   Basis (Matmul im Graphen)            11,77 s je gt5-Runde (1T)
#   Kern, Matmul auf der CPU             13,39 s   (+13,8 %, Band gerissen)
#   Kern, Matmul ersatzlos gestrichen    11,60 s   (= Basis; die Probe belegt, dass die
#                                                  ganze Differenz am Matmul haengt)
# Und sie haengt NICHT an der Rechnung selbst: der Score-Matmul ist 2 x 512 x 1400 =
# 1,4 MFLOP, mikrogemessen 0,074 ms Wanduhr. Sie haengt am THREAD-POOL von OpenBLAS
# (0.3.33, DYNAMIC_ARCH, MAX_THREADS=64): er weckt fuer diese Winz-Rechnung alle Kerne,
# und seine Arbeitsthreads SPINNEN danach im Leerlauf weiter (THREAD_TIMEOUT, rund 20 ms)
# — bei rund 90 Aufrufen je gt5-Runde nimmt das dem OpenVINO-Abgabethread und dem
# ffmpeg-Decoder genau die CPU weg, die sie brauchen. Sichtbar war es daran, dass ALLE
# Stufen langsamer wurden, auch der Detektor, der mit dem Matmul nichts zu tun hat
# (CPU-Zeit je Aufruf 0,373 ms bei freiem Pool gegen 0,228 ms mit einem Thread).
# setdefault, damit eine bewusste Vorgabe von aussen gewinnt.
for _blas in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
              "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_blas, "1")

import cv2                                              # noqa: E402  zieht numpy mit
import numpy as np                                      # noqa: E402


def _wurzel():
    """Projektwurzel: --wurzel (Aufruf mit fremdem Arbeitsordner), sonst der Ordner
    DIESER Datei.

    Seit dem R1-Umzug (E3.5, 14.09.2026) liegt worker_kern.py in der Projektwurzel
    neben verifyd.py/decode.py/face_audit.py — in jedem Image unter /app. Bis dahin
    lag sie in <repo>/prototyp/worker_gpu/ und die Zeile rechnete deshalb DREI
    dirname ab; wer das hier anfasst, muss beides zusammen denken.
    Muss VOR den Projekt-Importen feststehen — deshalb steht der Bootstrap hier und
    nicht in den Huellen: beide Engines und beide Huellen bekommen ihn ueber den
    Import dieser Datei, und es gibt ihn genau einmal."""
    if "--wurzel" in sys.argv:
        return sys.argv[sys.argv.index("--wurzel") + 1]
    return os.path.dirname(os.path.abspath(__file__))


WURZEL = _wurzel()
for _p in (WURZEL, os.path.join(WURZEL, "prototyp")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import decode                                           # noqa: E402  _probe: EIN Metadaten-Parser
import face_audit                                       # noqa: E402  ar_det_size, MODELLE, fd-Regel
import pose_wache                                       # noqa: E402  RTMPose-Vorverarbeitung
from core import guete                                  # noqa: E402  e/t-Modelle + Normierung
from core.livewache import person_region                # noqa: E402  Personenregion aus Gesichtsbox
from core.messkarte import QUELLE_ANALYSE as MK_QUELLE  # noqa: E402  Herkunft der Messkarte
from core.registry import MODELL_VERTRAG                # noqa: E402  Detektor- und 1k3d68-Pfad
from insightface.data import get_object as if_objekt    # noqa: E402  meanshape_68 fuer die Pose
from insightface.model_zoo.scrfd import SCRFD, distance2bbox, distance2kps  # noqa: E402
from insightface.utils import transform as if_transform  # noqa: E402  Pose aus 68 Punkten
from insightface.utils.face_align import estimate_norm, trans_points  # noqa: E402

# .528 — EINE Bibliotheks-Warnung daempfen, und nur diese eine.
# `estimate_norm` ruft intern skimage's `tform.estimate()`; skimage hat den Aufruf
# in 0.26 als FutureWarning markiert. Die Warnung steht damit an JEDEM Gesicht
# (_theta unten), nicht einmal je Prozess: die Intel-Abnahme vom 14.09. zaehlte 97
# Bloecke in 22 Minuten (Belegort .suslik_tmp/gt5/runs/abnahme_intel_527_20260914/,
# prod_log_vollstaendig.txt), gegen etwa eine je Tag unter .526. Das ist kein
# Befund, sondern Rauschen ueber genau dem Log, in dem eine Ferndiagnose die
# echten Zeilen suchen muss — und es geht um eine Umstellung INNERHALB von
# insightface, auf die wir keinen Zugriff haben (wir rufen `estimate` nirgends
# selbst).
# ENG, nicht global: genau diese Meldung und genau diese Kategorie. Ein
# `simplefilter("ignore")` wuerde auch die Warnungen verschlucken, die uns etwas
# sagen wollen — und es steht hier im WORKER-Modul, nicht im Dienst.
# EHRLICHE GRENZE: faellt die Meldung bei einem kuenftigen skimage anders aus,
# greift der Filter nicht mehr und das Rauschen ist zurueck. Lauter als eine
# stillschweigend zu breite Regel ist das allemal.
warnings.filterwarnings(
    "ignore", category=FutureWarning,
    message=r"`estimate` is deprecated since version")

# insightface SCRFD fuer det_10g (scrfd.py:87, :113-114, :121-128)
DET_MEAN, DET_STD = 127.5, 128.0
DET_STRIDES, DET_ANKER, DET_FMC, DET_NMS = (8, 16, 32), 2, 3, 0.4
# v7: die feste Breite JEDES Aufrufs der Mess-Stufen. Sie ersetzt die Buendelstufen
# face_audit.Embedder.BATCH_STUFEN (1, 2, 4, 8). Kuerzere Aufrufe werden gepolstert
# (das Doppel wird verworfen), laengere in Portionen dieser Breite zerlegt; mehr als
# vier Gesichter je Frame bleiben damit koennbar. 2 (Auftrag 12.09.): n = 1 und n = 2
# sind die einzigen Breiten, die in den fuenf Grundwahrheits-Events vorkommen.
# face_audit bleibt unberuehrt, es ist Prod-Kernmodul.
AUFRUF_BREITE = 2
# v8: der Name der fd-Stufe. Er steht hier EINMAL, weil er an fuenf Stellen
# zusammenpassen muss: Bau-Vorschrift, Stufenfolge, Satz, Kaskaden-Sprung, Zeitnehmer.
FD = "fd"
# Die Stufen in Bau- und Rechenreihenfolge. DIE zentrale Quelle dieser Aufzaehlung
# (Hausregel aus qs_ebenen.md): Engine-Bau, Warmlauf und Kopfzeile lesen sie hier,
# statt je ein eigenes Literal zu fuehren.
STUFEN = (FD, "e", "t", "p", "r")
# Die KASKADEN-Stufen, also die Folge ohne die fd-Vorstufe: fd entscheidet nicht ueber
# Stimmen, es sortiert Fehldetektionen vor den teuren Stufen aus.
KASKADE = tuple(k for k in STUFEN if k != FD)
# Decoder-Vorlauf (v2): so viele fertige Frames darf der Leser vorausholen, waehrend die
# GPU noch am vorigen rechnet. 4 * 12,4 MB (4K NV12) = rund 50 MB Vorrat.
VORLAUF = 4
# Kernel-Kapazitaet der ffmpeg-Pipe. 1 MiB ist auf .168 die Obergrenze fuer einen Prozess
# ohne CAP_SYS_RESOURCE (/proc/sys/fs/pipe-max-size, man 7 pipe; gemessen 12.09.: 12,4 MB
# gibt EPERM). Die Vorgabe einer frischen Pipe ist 64 KiB, also 0,5 % eines 4K-Frames.
PIPE_ZIEL = 1 << 20
# Kantenlaenge der Laplace-Leinwand. Sie muss max(Crop-Breite, Crop-Hoehe) + 2 fassen
# (der Spiegelring). Groessere Crops werden auf die Leinwand BESCHNITTEN (vorderer Teil,
# die Werte der gesampelten Region bleiben exakt) und laut gezaehlt
# (leinwand_beschnitten) — ein stilles Herunterskalieren waere eine andere Schaerfe.
# 320 ist User-Entscheid 2 der v8-Abnahme („320 bleibt, keine Stufen"), gemessen als die
# einzige Groesse, die das Tempo-Band +10 % haelt; Preis ist EIN beschnittener Crop von
# 122 (301x353 in a6eptk), dessen fd-Urteil sich dadurch nicht aendert.
LEINWAND = 320
# OpenCV cvtColor(BGR2GRAY) fuer 8 Bit: Festkomma-Gewichte bei yuv_shift 14 (color.hpp
# R2Y/G2Y/B2Y). Gegenprobe 13.09. gegen cv2 auf 4096 Zufallspixeln: 4085 identisch, die
# uebrigen 11 um genau 1 Graustufe daneben (SIMD-Pfad von OpenCV) — auf die Varianz
# wirkt das rund 0,05 von 1500.
GRAU_W, GRAU_SHIFT = (4899, 9617, 1868), 14
# cv2.Laplacian(ksize=1): rueckwaerts gemessen 13.09. per Impulsantwort.
LAPLACE_KERN = ((0.0, 1.0, 0.0), (1.0, -4.0, 1.0), (0.0, 1.0, 0.0))
# insightface landmark.Landmark.get: fest verdrahteter Polster-Faktor des Zuschnitts.
# Ein eigener Zuschnitt verschiebt die Skala (MODELL_VERTRAG['1k3d68'] eingang_notiz).
LM_POLSTER = 1.5
# Die Latten der fd-Regel kommen aus dem Messplan; fehlt eine, gilt die Vorgabe der
# Hausregel SELBST (face_audit.ist_fehldetektion) — kein zweites Literal daneben.
FD_VORGABE = {k: v.default for k, v in
              inspect.signature(face_audit.ist_fehldetektion).parameters.items()
              if v.default is not inspect.Parameter.empty}

# --- v8: Bestbilder und Kandidaten (Zahlen von analyze.py, dort im Klartext) -------
# Anzeige-Umfeld (analyze.ctx_crop, analyze.py:368)
CTX_FAKTOR, CTX_MAX_KANTE, CTX_AR = 3.0, 560, 4 / 3
# Kandidaten-Gate (analyze.py:711-712)
KAND_KANTE, KAND_FRONT, KAND_DET, KAND_SHARP = 100, 0.5, 0.7, 60
# Personen-Kandidat / Fremd-Kandidat / Neuheit (analyze.py:736-742, :1015)
KAND_SCORE_MIN, FREMD_UNTER, NEUHEIT_AB = 0.45, 0.35, 0.75

# Frist der Warmlauf-Barriere in Sekunden (offener v4-Einzeiler, Konzept §2 Punkt 4).
# OHNE Frist warten die uebrigen Threads EWIG, wenn einer im warm() stirbt (der
# gemessene Fall: BFC-OOM bei drei Threads) — der Prozess haengt dann still statt laut
# zu scheitern. Die Frist ist bewusst gross: ein KALTER Kompilat-Cache laesst den
# Warmlauf gemessen ueber 100 s dauern (v2-Aufbau 112 s), und eine Frist, die im
# Normalbetrieb zuschlaegt, waere schlimmer als keine.
BARRIERE_FRIST = 1800.0


# ------------------------------------------------------------------ Config
def cfg_lesen(pfad):
    """fps_sample, globale det-Schwelle und Kamera-Guards aus dem Config-Store,
    dieselben Schluessel wie verifyd.run_analyze (verifyd.py:2037, :2052)."""
    with open(pfad, encoding="utf-8") as f:
        d = json.load(f)
    guards = ((d.get("live") or {}).get("guards") or {})
    return float(d["fps_sample"]), float(d["det_thresh"]), guards


def det_schwelle(det_global, guards, kamera):
    """Kamera-det_min, sonst global, wie verifyd.run_analyze (verifyd.py:2052)."""
    v = (guards.get(kamera) or {}).get("det_min")
    return float(v) if v is not None else det_global


# ------------------------------------------------------------------ Decode-Plumbing
# glibc-Allokator: Parameter-Nummer aus malloc.h. -3 ist M_MMAP_THRESHOLD.
M_MMAP_THRESHOLD = -3
# Die Schwelle, ab der malloc() einen Block direkt per mmap holt statt aus einer Arena.
# KEINE selbst erfundene Zahl: 128 KiB ist glibc's eigener DEFAULT_MMAP_THRESHOLD, also
# der Wert, mit dem der Allokator startet. Wir nageln ihn nur fest (s. u.).
MMAP_SCHWELLE = 128 * 1024


def allokator_politik(schwelle=MMAP_SCHWELLE):
    """Die mmap-Schwelle des glibc-Allokators FESTNAGELN. Gegen den Speicherbefund
    vom 14.09. (E2d), und zwar an dessen bewiesener Ursache.

    WAS GEMESSEN WURDE (40 Jobs, mallinfo2 je Job, Rundordner e2d2_stabil_20260914):
    der Fussabdruck des Worker-Prozesses wuchs um +11,5 bis +11,7 MB je Job ohne
    Plateau (auf 170 Jobs in E2b: +45 MB/Job, bis die Speicher-Wache bei Job 150 zuschlug
    und 20 unschuldige Jobs als fremdverschuldet buchte). Die Zerlegung zeigt, dass das
    Programm NICHT leckt:
      uordblks (tatsaechlich BELEGT)          230 -> 230 MB   = +0,00 MB/Job
      fordblks (frei, aber nicht zurueck)    3128 -> 3458 MB  = +18,3 MB/Job
      arena    (vom Kern geholt)             3359 -> 3789 MB  = +18,3 MB/Job
      hblkhd   (per mmap geholt)                7 ->    7 MB  = +0,00 MB/Job
      keepcost (am Heap-Ende freigebbar)        0 ->    0 MB
    Es waechst ausschliesslich der Anteil, den der Allokator freigegeben, aber nicht
    an den Kern zurueckgegeben hat. malloc_trim(0) half gemessen NICHT (arena, fordblks,
    anon und VmRSS danach byte-gleich) — keepcost 0 sagt warum: das Freie liegt nicht am
    Heap-Ende, sondern MITTEN in den Arenen.

    DER MECHANISMUS: glibc passt die mmap-Schwelle dynamisch an. Jedes Mal, wenn ein
    per mmap geholter Block freigegeben wird, hebt glibc die Schwelle auf dessen Groesse
    (bis 32 MiB). Ein NV12-Frame ist 12,4 MB (4K), 7,4 MB (2560x1920) oder 3,1 MB
    (1080p) gross und wird je Sample-Frame neu geholt und wieder freigegeben. Nach den
    ersten Frames steht die Schwelle also ueber der Framegroesse, und ab da kommen alle
    weiteren Frame-Puffer aus den Arenen statt aus mmap — dort zerstueckeln sie den Heap
    und sind nie wieder am Ende. `hblkhd` = 7 MB flach ist der Beleg: es wird
    tatsaechlich nichts mehr gemappt.

    DER GRIFF: mallopt(M_MMAP_THRESHOLD, ...) schaltet laut glibc-Dokumentation die
    dynamische Anpassung AB. Damit geht jeder Frame-Puffer wieder per mmap und kommt
    beim free() per munmap SOFORT an den Kern zurueck — freigeben statt horten.
    GEMESSEN, gleiche 40 Jobs, nur diese eine Aenderung:
      Steigung  +11,50 / +11,72  ->  -0,06 / +0,00 MB je Job   (Plateau)
      Spitze    5036 MB          ->  2959 MB
      anon      2529 MB          ->   449 MB
    PREIS, beziffert: mehr mmap/munmap-Aufrufe und frisch genullte Seiten. Grobkontrolle
    derselben 40 Jobs (Prod lief daneben, deshalb KEINE Zeitwertung): Summe wall_s
    171,1 -> 185,6 s, Summe cpu_s 34,0 -> 44,9 s. Die saubere Zeitmessung gehoert auf
    eine ruhige Maschine (E3).

    EHRLICHE GRENZEN: (1) Der Griff gilt nur fuer glibc — auf musl ist mallopt ein
    No-op, dann faellt diese Politik still weg, und der Rueckgabewert sagt es.
    (2) Er wirkt erst auf Allokationen NACH dem Aufruf, gehoert also an den
    Prozess-Anfang. (3) Hat der Betreiber MALLOC_MMAP_THRESHOLD_ selbst gesetzt, ist die
    Schwelle bereits festgenagelt; dann wird seine Wahl NICHT ueberschrieben.
    -> dict fuer den Kopf/das Prozess-Log, nie eine Ausnahme."""
    aus = os.environ.get("MALLOC_MMAP_THRESHOLD_")
    if aus:
        return {"gesetzt": False, "quelle": "MALLOC_MMAP_THRESHOLD_", "schwelle": aus}
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        libc.mallopt.argtypes = [ctypes.c_int, ctypes.c_int]
        libc.mallopt.restype = ctypes.c_int
        rc = int(libc.mallopt(M_MMAP_THRESHOLD, int(schwelle)))
    except Exception as e:                                  # noqa: BLE001
        return {"gesetzt": False, "quelle": "mallopt", "fehler": f"{type(e).__name__}: {e}"}
    return {"gesetzt": bool(rc), "quelle": "mallopt", "schwelle": int(schwelle)}


def pipe_kapazitaet(fd, ziel=PIPE_ZIEL):
    """Kernel-Kapazitaet der Pipe hinter `fd` auf `ziel` heben. Ohne CAP_SYS_RESOURCE ist
    /proc/sys/fs/pipe-max-size die Obergrenze (man 7 pipe); darueber kommt EPERM und die
    Pipe behaelt ihre Vorgabe. Das ist kein Fehler, nur langsamer, deshalb Rueckgabe
    statt Ausnahme. -> (Kapazitaet in Byte, Fehlertext oder None)"""
    try:
        return fcntl.fcntl(fd, fcntl.F_SETPIPE_SZ, int(ziel)), None
    except OSError as e:
        try:
            return fcntl.fcntl(fd, fcntl.F_GETPIPE_SZ), f"{e.strerror} (ziel {ziel})"
        except OSError:
            return None, str(e)


def pipe_probe(ziel=PIPE_ZIEL):
    """Was diese Maschine einer Pipe erlaubt, einmal beim Start gemessen statt angenommen.
    -> {"vorgabe": Byte, "erreicht": Byte, "grenze": Text oder None}"""
    r, w = os.pipe()
    try:
        vorgabe = fcntl.fcntl(w, fcntl.F_GETPIPE_SZ)
        erreicht, fehler = pipe_kapazitaet(w, ziel)
        return {"vorgabe": vorgabe, "erreicht": erreicht, "grenze": fehler}
    finally:
        os.close(r)
        os.close(w)


def nv12_strom(cmd, W, H, schritt, kette, vorlauf=VORLAUF, wache=None):
    """Sample-Frames als (i, y, uv), y [1,H,W,1] und uv [1,H/2,W/2,2] uint8, aus der
    rawvideo-Pipe von `cmd`. Das ist der BYTE-Weg von frames_nv12 aus beiden
    Prototypen — er war dort wortgleich; unterschiedlich ist allein die ffmpeg-Kette
    (VAAPI gegen NVDEC) und der Fehlertext, und die bleiben bei der Engine.

    v2 (12.09.): Der Leser laeuft in einem eigenen Thread und holt bis zu `vorlauf`
    Frames voraus, waehrend die GPU noch am vorigen rechnet. Vorher lief beides
    abwechselnd im selben Thread, gemessen 0,84 s Wartezeit je Event auf der Pipe
    (analysen/worker_performance.md Abschnitt 11) — der groesste Einzelposten nach dem
    Detektor. Ueberlappen statt beschleunigen ist der von OpenVINO empfohlene Weg
    (General Optimizations, „hides the latency of capturing"). Dazu die Pipe-Kapazitaet
    auf PIPE_ZIEL; der eigentliche Puffer ist aber die Queue, nicht die Pipe. Bytes und
    Reihenfolge aendern sich dadurch nicht.

    KEIN RUECKFALL: faellt die Hardware-Kette aus, endet ffmpeg mit rc != 0 und der Lauf
    bricht ab, statt still langsamer (und mit anderen Pixeln) weiterzurechnen.

    E2 (13.09., W1-M9 „die Wache gegen still verfaelschte Clips"): `wache` ist ein dict,
    das dieser Strom mit dem fuellt, was NUR ER wissen kann — Kette, ffmpeg-Exitcode und
    die Zahl der Decoder-Kontext-Zeilen aus stderr. Die Zaehlregel ist die von
    decode.FrameIter (` @ 0x` bei -v warning, decode.py:222-227), nicht eine zweite
    Heuristik: ffmpeg dekodiert kaputte Clips mit rc=0 und vollem Zaehler DURCH und
    verfaelscht still die Bilder; ohne diese Zeilen sieht das niemand. Das URTEIL
    (Toleranz, frames_fehlen) faellt beim Aufrufer mit den Formeln der Frame-Quelle.
    None = das Verhalten von E1, Byte fuer Byte."""
    fsz = W * H * 3 // 2
    schlange, fehler, ENDE = queue.Queue(maxsize=max(1, vorlauf)), [], object()
    if wache is not None:
        wache["kette"] = kette
    with tempfile.TemporaryFile() as err:
        # .536 B1a: stdin=DEVNULL — DIE HAEUFIGSTE ffmpeg-STARTSTELLE DES WORKERS
        # (sie laeuft bei JEDEM analyze-Job). Ohne sie erbt ffmpeg den fd 0 des
        # Worker-Prozesses, und das war bis .535 die JOB-PIPE: ffmpeg pollt stdin
        # alle 100 ms auf einen Tastendruck (read(0,1)) und frisst dabei die
        # ersten Bytes einer gerade eintreffenden Job-Zeile. Belegt am Prod-Image
        # (ffmpeg 7.1.5, 16.09.: 200 Job-Zeilen, 2 s ffmpeg -> 2 Bytes fehlen,
        # erste Zeile beginnt mit id":"j1 statt {"id":"j1); Folge im Feld waren
        # zwei Worker-Tode (j26 08:02:56, j2325 12:26:10) — die verstuemmelte
        # Zeile kam als ID-lose Antwort zurueck, der Job haengte bis zur Frist
        # und der Job-Watchdog schoss den GANZEN Prozess. `-nostdin` in den
        # Kommandoketten (engine_ov/_ffmpeg_nv12, engine_cuda/_ffmpeg_nv12) ist
        # der zweite Riegel derselben Kette. An den PIXELN aendert beides nichts:
        # -nostdin schaltet nur den Tastatur-Poll ab, DEVNULL nur die Quelle des
        # fd 0 — der gepinnte Pixelpfad bleibt unberuehrt.
        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=err, bufsize=fsz * 2)
        pipe_kapazitaet(p.stdout.fileno())

        def lesen():
            k = 0
            try:
                while True:
                    b = p.stdout.read(fsz)
                    if len(b) < fsz:
                        return
                    a = np.frombuffer(b, np.uint8)
                    schlange.put((k * schritt, a[:W * H].reshape(1, H, W, 1),
                                  a[W * H:].reshape(1, H // 2, W // 2, 2)))
                    k += 1
            except BaseException as e:                      # noqa: BLE001  im Thread gefangen,
                fehler.append(e)                            # im Hauptthread geworfen
            finally:
                schlange.put(ENDE)

        th = threading.Thread(target=lesen, name="nv12-leser", daemon=True)
        th.start()
        vollstaendig = False
        try:
            while True:
                s = schlange.get()
                if s is ENDE:
                    vollstaendig = True
                    break
                yield s
        finally:
            if not vollstaendig:
                p.terminate()                               # Verbraucher hat abgebrochen
            while th.is_alive():                            # Leser aus einem put() loesen
                try:
                    schlange.get_nowait()
                except queue.Empty:
                    th.join(0.05)
            th.join()
            p.stdout.close()
            rc = p.wait()
        if wache is not None:
            wache["rc"] = rc
            try:
                err.seek(0)
                text = err.read(65536).decode("utf-8", "replace")
                # Zaehlregel wortgleich decode.FrameIter._pipe (decode.py:226-227):
                # bei -v warning ist JEDE Decoder-Kontext-Zeile eine Auffaelligkeit.
                wache["decoder_fehler"] = sum(1 for z in text.splitlines() if " @ 0x" in z)
            except OSError:
                pass
        if fehler:
            raise fehler[0]
        if rc != 0:
            err.seek(0)
            raise RuntimeError(f"{kette}-Kette rc={rc}: "
                               + err.read(4000).decode("utf-8", "replace").strip()[-400:])


def nv12_mit_rueckfall(hw_cmd, sw_cmd, W, H, schritt, kette, vorlauf=VORLAUF, wache=None):
    """Der Frame-Strom EINES Jobs MIT LAUTEM SOFTWARE-RUECKFALL (E2d, Konzept §4).

    Der Prototyp-Grundsatz „kein Rueckfall" war eine MESS-Auflage: eine Messung, die
    heimlich auf Software ausweicht, misst die falsche Sache. Im DIENST ist er falsch —
    10-bit-Kameras und AMD/mesa-VAAPI existieren im Feld, und `decode.FrameIter` hat
    genau dafuer seit jeher den lauten Rueckfall. Gemessen in der E2b-Eichung am
    Bestands-Clip …-exf13p (4K-Kamera): der ALTE Weg las ihn ueber den Rueckfall mit
    340/340 Frames und bestaetigte zwei Personen; der neue warf `RuntimeError` und
    verlor als einziges der 170 Ereignisse seine Namen.

    DIE REGEL IST DIE VON decode.FrameIter.__iter__ (decode.py:231-256), uebernommen
    statt nachgebaut — inklusive ihrer Unterscheidung:
      * Die HW-Kette lieferte NICHTS (0 Frames, egal ob mit Fehler oder ohne): kompletter
        NEUSTART auf Software. Es ist nichts beim Verbraucher, also gibt es nichts zu
        verlieren, und der SW-Weg liest 10-bit/fremde Profile, die die HW-Kette ablehnt.
      * Die HW-Kette lieferte SCHON FRAMES und starb dann (real: VAAPI rc=251 mitten im
        Clip): KEIN Neustart. Die gelieferten Frames sind beim Verbraucher und nicht
        rueckholbar; ein zweiter Durchlauf wuerde sie doppelt liefern. Der Fehler fliegt
        weiter, und der Aufrufer (worker_dienst.EngineTor) urteilt den lesbaren Teil und
        FLAGGT ihn — das ist die Behandlung, die analyze.py fuer diesen Fall hat.

    LAUT heisst: `wache['hwdec_fallback'] = True` plus `wache['hwdec_grund']`, und
    `wache['kette']` traegt danach die SOFTWARE-Kette. Eine Log-Zeile je Ereignis schreibt
    der Aufrufer daraus — hier wird nichts gedruckt, damit die Meldeform an EINER Stelle
    steht.

    BYTE-GLEICHHEIT ist Bedingung, nicht Hoffnung: beide Ketten enden auf `format=nv12`
    ueber demselben Decoder-Bild. Der Nachweis je Backend gehoert ins Gate (Konzept §4,
    W3-V9) — fuer VAAPI gemessen in E2d, s. Rundordner."""
    n = 0
    grund = None
    try:
        for s in nv12_strom(hw_cmd, W, H, schritt, kette, vorlauf=vorlauf, wache=wache):
            n += 1
            yield s
    except RuntimeError as e:
        if n:
            raise                      # Teilabbruch: der Aufrufer urteilt den Rest
        grund = str(e)[:300]
    if n:
        return
    if grund is None:
        grund = f"die {kette}-Kette lieferte 0 Frames"
    if wache is not None:
        wache["hwdec_fallback"] = True
        wache["hwdec_grund"] = grund
    yield from nv12_strom(sw_cmd, W, H, schritt, "SW", vorlauf=vorlauf, wache=wache)


# ------------------------------------------------------------------ Modelle und Normierung
def modell_pfad(schluessel):
    """Ein Modell aus dem MODELL_VERTRAG, im Image oder im Repo (die Fassung, die in
    beiden Prototypen als det_pfad_finden/fd_pfad_finden stand)."""
    v = MODELL_VERTRAG[schluessel]
    return next(p for p in (v["pfad_image"], os.path.join(WURZEL, v["pfad_repo"]))
                if os.path.exists(p))


def rec_spec():
    """Die Eingangs-Spezifikation des konfigurierten Recognition-Modells."""
    return face_audit.MODELLE[face_audit.aktuelles_modell()]


def vorgabe_pfade(spec):
    """Je Stufe die Modell-Datei, die das Haus vorgibt. Die Engine darf sie ersetzen
    (CUDA: die fp16-Fassungen ueber die CLI), rechnet aber immer mit der Datei, die sie
    WIRKLICH geladen hat."""
    return {FD: modell_pfad("1k3d68"), "e": guete.PFAD_E, "t": guete.PFAD_T,
            "p": pose_wache.MODELL_STD[0], "r": spec["onnx"]}


def norm_vorschriften(spec):
    """Die NORMIERUNGS-VORSCHRIFT je Stufe als reine Zahlen — die eine Quelle, aus der
    beide Engines ihre Knoten bauen (bis E1 stand sie als _norm_e/_norm_t/_norm_p/
    _norm_r/_norm_lm zweimal im Haus, je einmal in OpenVINO- und in ONNX-Knoten).

    Die Werte kommen unveraendert aus den Prod-Quellen, nicht aus Literalen hier:
      e   core/guete.empfinden (guete.py:379-386)  RGB/255, dann ImageNet je Kanal
      t   core/guete.fiqa_t   (guete.py:371-376)   RGB/255, dann (x-0,5)/0,5
      p   prototyp/pose_wache.skelett (:112-113)   (RGB-MEAN)/STD je Kanal
      r   face_audit.MODELLE                       Kanalfolge (bgr), dann (x-mean)/std
      fd  MODELL_VERTRAG['1k3d68']['eingang']      ROHE 0..255 (mean 0, std 1)
    REIHENFOLGE der Knoten, verbindlich fuer beide Engines und Zeile fuer Zeile die der
    Prototypen: erst /255, dann die Kanalfolge, dann -mean, dann /std. Ein Posten
    entsteht NUR, wenn die Vorschrift ihn verlangt — eine Subtraktion von 0 waere toter
    Rechenweg (Regel aus _norm_lm), und ein Skalar bleibt ein Skalar (t und r rechnen
    mit einer Zahl, e und p mit einem [1,3,1,1]-Block; das war in beiden Prototypen so
    und bleibt es, damit die Graphen Knoten fuer Knoten dieselben sind).
    -> {stufe: {"div255": bool, "bgr": bool, "mean": Zahl oder 3er-Feld, "std": ...}}"""
    lm = MODELL_VERTRAG["1k3d68"]["eingang"]
    return {
        FD: {"div255": False, "bgr": False,
             "mean": float(lm.get("mean", 0.0)), "std": float(lm.get("std", 1.0))},
        "e": {"div255": True, "bgr": False, "mean": guete._IN_MEAN, "std": guete._IN_STD},
        "t": {"div255": True, "bgr": False, "mean": 0.5, "std": 0.5},
        "p": {"div255": False, "bgr": False, "mean": pose_wache.MEAN, "std": pose_wache.STD},
        "r": {"div255": False, "bgr": bool(spec.get("bgr")),
              "mean": spec["mean"], "std": spec["std"]},
    }


def norm_schritte(v):
    """Die Vorschrift als Folge von Schritten, die eine Engine abarbeitet:
    [("div", 255.0), ("bgr", None), ("sub", mean), ("div", std)] — ohne die Schritte,
    die nichts tun. Damit steht die Auslassungs-Regel (kein Abzug von 0, keine Division
    durch 1) EINMAL und nicht in jeder Engine noch einmal."""
    schritte = []
    if v["div255"]:
        schritte.append(("div", 255.0))
    if v["bgr"]:
        schritte.append(("bgr", None))
    if not _ist(v["mean"], 0.0):
        schritte.append(("sub", v["mean"]))
    if not _ist(v["std"], 1.0):
        schritte.append(("div", v["std"]))
    return schritte


def _ist(wert, zahl):
    """Ist der Posten (Skalar oder 3er-Feld) ueberall genau `zahl`? Ein numpy-Feld
    direkt auf Wahrheit zu pruefen wirft ValueError — deshalb diese eine Stelle."""
    return bool(np.all(np.asarray(wert, np.float64) == zahl))


# ------------------------------------------------------------------ Detektor
def det_geometrie(W, H):
    """Leinwand und Skala des Detektor-Zweigs — die Rechnung stand in beiden Prototypen
    im Graph-Bau (graph_pre_det bzw. Geometrie.__init__) und ist reine Zahlenarbeit:
    det_size wie analyze.py:550, Seitenverhaeltnis halten und oben links in die Leinwand
    wie insightface SCRFD._detect_candidates (scrfd.py:278-289), Rest schwarz.
    -> ((det_w, det_h), (neu_w, neu_h), det_scale)"""
    det_w, det_h = face_audit.Embedder.ar_det_size(W, H)
    if H / W > det_h / det_w:
        neu_h = det_h
        neu_w = int(neu_h / (H / W))
    else:
        neu_w = det_w
        neu_h = int(neu_w * (H / W))
    return (det_w, det_h), (neu_w, neu_h), neu_h / H


_NMS = types.SimpleNamespace(nms_thresh=DET_NMS)


def detektor(outs, det_wh, det_scale, schwelle, zentren):
    """insightface SCRFD.forward + _detect_candidates + detect (scrfd.py:158-275),
    batched=False, max_num=0. -> (dets [m,5], kpss [m,5,2])"""
    det_w, det_h = det_wh
    s_l, b_l, k_l = [], [], []
    for idx, stride in enumerate(DET_STRIDES):
        scores = outs[idx]
        bbox = outs[idx + DET_FMC] * stride
        kps = outs[idx + 2 * DET_FMC] * stride
        h, w = det_h // stride, det_w // stride
        ac = zentren.get((h, w, stride))
        if ac is None:
            ac = (np.stack(np.mgrid[:h, :w][::-1], axis=-1).astype(np.float32)
                  * stride).reshape((-1, 2))
            ac = np.stack([ac] * DET_ANKER, axis=1).reshape((-1, 2))
            zentren[(h, w, stride)] = ac
        pos = np.where(scores >= schwelle)[0]
        s_l.append(scores[pos])
        b_l.append(distance2bbox(ac, bbox)[pos])
        k_l.append(distance2kps(ac, kps).reshape((-1, 5, 2))[pos])
    scores = np.vstack(s_l)
    if scores.size == 0:
        return np.empty((0, 5), np.float32), np.empty((0, 5, 2), np.float32)
    order = scores.ravel().argsort()[::-1]
    pre = np.hstack((np.vstack(b_l) / det_scale, scores)).astype(np.float32, copy=False)[order]
    kpss = (np.vstack(k_l) / det_scale)[order]
    order = pre[:, 4].argsort()[::-1]                               # detect(): noch einmal
    pre, kpss = pre[order], kpss[order]
    keep = SCRFD.nms(_NMS, pre)
    return pre[keep], kpss[keep]


def zentren_fuellen(det_wh, det_scale):
    """Den Anker-Cache der SCRFD-Nachverarbeitung VOR dem Lauf fuellen, damit er waehrend
    der Rechnung nur noch gelesen wird (dict-Lesen ist unter der GIL atomar, Schreiben
    faellt weg — das ist die Voraussetzung fuer mehrere Rechenstraenge auf derselben
    Geometrie).

    Gefuellt wird durch einen LEERLAUF von detektor(): neun Ausgaenge mit lauter Nullen in
    genau den Formen, die der Detektor liefert, und Schwelle 1,0 — damit kommt kein
    Kandidat durch, aber die Anker aller drei Strides entstehen an derselben Stelle wie im
    Betrieb. So gibt es die Ankerformel weiterhin nur einmal im Haus. -> zentren"""
    det_w, det_h = det_wh
    zentren = {}
    zeilen = [(det_h // s) * (det_w // s) * DET_ANKER for s in DET_STRIDES]
    outs = ([np.zeros((m, 1), np.float32) for m in zeilen]         # scores
            + [np.zeros((m, 4), np.float32) for m in zeilen]       # bbox-Distanzen
            + [np.zeros((m, 10), np.float32) for m in zeilen])     # kps-Distanzen
    dets, _kpss = detektor(outs, det_wh, det_scale, 1.0, zentren)
    if len(dets) or len(zentren) != len(DET_STRIDES):
        raise SystemExit(f"zentren-Vorlauf unerwartet: {len(dets)} Kandidaten, "
                         f"{len(zentren)} Anker-Saetze")
    return zentren


# ------------------------------------------------------------------ Matrizen (nur Zahlen)
def gitter_norm(W, H):
    """Frame-Pixel (x, y) -> GridSample-Koordinate bei align_corners=False."""
    return np.array([[2.0 / W, 0.0, 1.0 / W - 1.0], [0.0, 2.0 / H, 1.0 / H - 1.0],
                     [0.0, 0.0, 1.0]])


def _theta(minv, nm):
    """minv (2x3): Ausschnitt-Pixel -> Frame-Pixel. -> theta (2x3) fuer den Graphen."""
    return (nm @ np.vstack([minv, [0.0, 0.0, 1.0]]))[:2].astype(np.float32)


def theta_e(bb, W, H, seiten, nm):
    """guete.empfinden auf dem engen Crop frame[y1:y2, x1:x2] (analyze.py:568-569),
    cv2.resize INTER_LINEAR: Quellpunkt = (d + 0,5) * s - 0,5. None = leerer Crop."""
    x1, y1, x2, y2 = bb
    eh, ew = seiten
    cw, ch = min(x2, W) - x1, min(y2, H) - y1
    if cw <= 0 or ch <= 0:
        return None
    sx, sy = cw / ew, ch / eh
    return _theta(np.array([[sx, 0.0, x1 + 0.5 * sx - 0.5],
                            [0.0, sy, y1 + 0.5 * sy - 0.5]]), nm)


def theta_t(kps, seite, nm):
    """insightface norm_crop (face_align.py:27-30): Ziel = M * Quelle."""
    return _theta(cv2.invertAffineTransform(estimate_norm(kps, seite)), nm)


def theta_p(bbox, W, H, nm):
    """pose_wache.skelett (pose_wache.py:101-110) auf core/livewache.person_region."""
    x1, y1, x2, y2 = person_region(bbox, W, H)
    center = np.array([(x1 + x2) / 2, (y1 + y2) / 2], dtype=np.float32)
    scale = np.array([(x2 - x1) * 1.25, (y2 - y1) * 1.25], dtype=np.float32)
    w, h = pose_wache.INPUT_SIZE
    if scale[0] > scale[1] * (w / h):
        scale = np.array([scale[0], scale[0] / (w / h)], dtype=np.float32)
    else:
        scale = np.array([scale[1] * (w / h), scale[1]], dtype=np.float32)
    m = pose_wache.warp_matrix(center, scale, pose_wache.INPUT_SIZE)
    return _theta(cv2.invertAffineTransform(m), nm)


def theta_fd(box, seite, nm):
    """Landmark-Zuschnitt wie insightface landmark.Landmark.get + face_align.transform:
    Mitte der FLOAT-Box (nicht der ganzzahlig geklemmten!), Skala seite/(max(w,h)*1,5),
    keine Drehung. M bildet Frame-Pixel auf Ausschnitt-Pixel ab (das ist die Matrix, die
    warpAffine bekommt); der Graph braucht die Gegenrichtung, die Pose-Rueckrechnung
    spaeter M selbst. -> (theta fuer den Graphen, M)"""
    x1, y1, x2, y2 = (float(v) for v in box)
    s = seite / (max(x2 - x1, y2 - y1) * LM_POLSTER)
    halb = seite / 2.0
    M = np.array([[s, 0.0, halb - (x1 + x2) / 2.0 * s],
                  [0.0, s, halb - (y1 + y2) / 2.0 * s]])
    return _theta(cv2.invertAffineTransform(M), nm), M


def _spiegel_achse(start, laenge, C, grenze):
    """Indizes EINER Leinwand-Achse mit BORDER_REFLECT_101 an den Crop-Raendern:
    Position 0 ist der Spiegel VOR dem Crop (also die zweite Crop-Zeile/Spalte),
    1..laenge der Crop selbst, laenge+1 der Spiegel danach (die vorletzte). Der Rest
    wiederholt den letzten Spiegel und wird von der Maske ohnehin nicht gelesen.
    Bei laenge 1 fallen beide Spiegel auf den einzigen Pixel — genau wie in OpenCV.
    `grenze` ist die Bildkante: dass hier kein Index daneben liegt, wird geklemmt statt
    angenommen — ein Gather mit Index ausserhalb liest auf der GPU still Unsinn."""
    idx = np.empty(C, np.int32)
    idx[0] = start + min(1, laenge - 1)
    idx[1:1 + laenge] = start + np.arange(laenge, dtype=np.int32)
    idx[1 + laenge:] = start + max(0, laenge - 2)
    return np.clip(idx, 0, grenze - 1, out=idx)


def leinwand_zug(bb, W, H, C=LEINWAND):
    """Indizes und Masken der Laplace-Leinwand fuer EINEN engen Crop frame[y1:y2, x1:x2]
    (analyze.py:568-572: bb ist schon auf >= 0 geklemmt, das obere Ende klemmt numpy).
    -> (jx [C], iy [C], mu [C-2,1], mv [1,C-2], Pixelzahl, beschnitten?)
    Pixelzahl 0 heisst: leerer Crop — analyze.sharp gibt dort 0.0 zurueck, die Masken
    sind dann leer und die Summen werden nicht gelesen."""
    x1, y1, x2, y2 = bb
    cw, ch = min(x2, W) - x1, min(y2, H) - y1
    beschnitten = max(cw, ch) + 2 > C
    cw, ch = max(0, min(cw, C - 2)), max(0, min(ch, C - 2))
    mu = np.zeros((C - 2, 1), np.float32)
    mv = np.zeros((1, C - 2), np.float32)
    mu[:ch, 0] = 1.0
    mv[0, :cw] = 1.0
    return (_spiegel_achse(x1, max(cw, 1), C, W), _spiegel_achse(y1, max(ch, 1), C, H),
            mu, mv, cw * ch, beschnitten)


_MEAN_LMK = None


def mean_lmk():
    """Die mittlere 68-Punkt-Form, an der insightface die Pose schaetzt (meanshape_68.pkl,
    insightface landmark.Landmark.__init__). Einmal je Prozess geladen."""
    global _MEAN_LMK
    if _MEAN_LMK is None:
        _MEAN_LMK = if_objekt("meanshape_68.pkl")
    return _MEAN_LMK


def fd_winkel(punkte, M, seite):
    """Von der 1k3d68-Ausgabe zu den DREI VORZEICHEN-WINKELN — Zeile fuer Zeile
    insightface landmark.Landmark.get ab der Modellausgabe:
      Rohwerte ~ +-1  ->  (wert+1) * (seite//2), z ebenso  ->  zurueck ins Frame
      (trans_points3d mit der inversen Zuschnitt-Matrix)  ->  Affin-Fit gegen die
      mittlere Form  ->  s/R/t  ->  Winkel.
    Das ist reines numpy auf 68 Punkten und bleibt bewusst auf der CPU.

    E2c: HERAUSGELOEST aus fd_front, damit es die Rechnung genau EINMAL gibt. Der
    Bild-Weg des Dienstes (bild_kern.EngineEmbedder) braucht `face.pose` mit
    Vorzeichen — insightface setzt dort [rx, ry, rz] (landmark.Landmark.get), und
    core/ernte.py:80 liest ausdruecklich die Vorzeichen-Winkel. fd_front warf rz weg
    und nahm Betraege; eine zweite Fassung daneben waere eine zweite Quelle.
    -> (rx, ry, rz) in Grad"""
    pred = np.array(punkte, np.float32)
    halb = seite // 2
    pred[:, 0:2] += 1
    pred[:, 0:2] *= halb
    pred[:, 2] *= halb
    pred = trans_points(pred, cv2.invertAffineTransform(M))
    P = if_transform.estimate_affine_matrix_3d23d(mean_lmk(), pred)
    _s, R, _t = if_transform.P2sRt(P)
    rx, ry, rz = if_transform.matrix2angle(R)
    return float(rx), float(ry), float(rz)


def fd_front(punkte, M, seite):
    """Von der 1k3d68-Ausgabe zu front (analyze.frontality):
    front = 1 - (|pitch| + |yaw|) / 90, aus den Winkeln von fd_winkel.
    -> (front, |pitch|, |yaw|)"""
    rx, ry, _rz = fd_winkel(punkte, M, seite)
    a, b = abs(rx), abs(ry)
    return max(0.0, 1.0 - (a + b) / 90.0), a, b


def ctx_box(x1, y1, x2, y2, W, H):
    """Der Bildausschnitt von analyze.ctx_crop (analyze.py:380-397), Zeile fuer Zeile —
    Gesichtsbox um Umfeld erweitert, kurze Seite auf das Anzeige-Seitenverhaeltnis
    aufgezogen, Mitte in den Rahmen geschoben statt beschnitten. Hier nur die GEOMETRIE:
    geschnitten wird erst am Event-Ende, wenn der Frame ohnehin gewandelt wird.
    -> (a1, b1, a2, b2)"""
    g = max(x2 - x1, y2 - y1)
    f = max(1.2, min(CTX_FAKTOR, (CTX_MAX_KANTE / g) if g else CTX_FAKTOR))
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    w, h = (x2 - x1) * f, (y2 - y1) * f
    if h > 0 and CTX_AR:
        if w / h < CTX_AR:
            w = h * CTX_AR
        else:
            h = w / CTX_AR
    w, h = min(w, W), min(h, H)
    cx = min(max(cx, w / 2), W - w / 2)
    cy = min(max(cy, h / 2), H - h / 2)
    return (max(0, int(cx - w / 2)), max(0, int(cy - h / 2)),
            min(W, int(cx + w / 2)), min(H, int(cy + h / 2)))


def nv12_bgr(rahmen, W, H):
    """Der EINE Weg, auf dem ein Pixel zur CPU kommt (v8, nur am Event-Ende fuer die
    Bilder, die auch geschrieben werden): NV12-Puffer des Decoders -> BGR per cv2.
    Y-Ebene und die verschraenkte UV-Ebene liegen im Puffer schon so, wie cvtColor sie
    erwartet, sie muessen nur untereinander stehen."""
    y, uv = rahmen
    buf = np.empty((H * 3 // 2, W), np.uint8)
    buf[:H] = y.reshape(H, W)
    buf[H:] = np.ascontiguousarray(uv).reshape(H // 2, W)
    return cv2.cvtColor(buf, cv2.COLOR_YUV2BGR_NV12)


# ------------------------------------------------------------------ Referenzen und Scores
def referenzen_laden(pfad):
    """Referenzen aus dem refcache des alten Workers (analyze.load_refs, analyze.py:263-315):
    je Person eine Matrix L2-normierter Embeddings. Der Cache muss zum konfigurierten
    Modell passen (Kopf '§modell', gelesen wie analyze._refcache_meta), sonst Abbruch
    statt still falscher Scores. Personenliste = die Nicht-§-Schluessel im Kopf (der
    Worker fuehrt dort alle Master-Personen, analyze.py:272). Personen ohne Vektoren
    bekommen wie in analyze.nn den Score -1.0 und gehen nicht in die Matrix.
    Die Matrix ist [Personen * je_person, 512], je Person auf die groesste Anzahl
    aufgefuellt durch Wiederholen ihrer ersten Zeile (das aendert ihr Maximum nicht).
    -> (alle, mit_refs, erk)

    E1: 'refs_t' ist die transponierte Matrix, EINMAL zusammenhaengend gelegt — sie ist
    seit dem Matmul-Umbau der rechte Faktor der Score-Rechnung auf der CPU (vorher war
    sie eine Graph-Konstante, gelegt in graph_rec_post). 'refs' bleibt daneben stehen,
    weil der Kandidaten-Zweig zeilenweise darin liest (nn_eigen)."""
    z = np.load(pfad, allow_pickle=True)
    meta = json.loads(str(z["§meta" if "§meta" in z.files else "meta"]))  # wie analyze._refcache_meta
    modell = face_audit.aktuelles_modell()
    if str(meta.get("§modell", "")) != modell:
        raise SystemExit(f"refcache-Modell {meta.get('§modell')!r} passt nicht zu {modell!r}")
    alle = sorted(k for k in meta if not k.startswith("§"))
    mats = {p: z[p] for p in alle if p in z.files and len(z[p])}
    mit_refs = sorted(mats)
    je = max(len(m) for m in mats.values())
    refs = np.concatenate([np.concatenate([mats[p], np.repeat(mats[p][:1], je - len(mats[p]),
                                                               axis=0)])
                           for p in mit_refs]).astype(np.float32)
    return alle, mit_refs, {"refs": refs, "refs_t": np.ascontiguousarray(refs.T),
                            "personen": len(mit_refs), "je_person": je}


def scores_rechnen(emb, erk):
    """Score je Person = Maximum ueber ihre Referenzen, wie analyze.nn
    (analyze.py:319-321) — seit E1 HIER auf der CPU statt als Graph-Knoten
    (Konzept §1c: die Referenz-Matrix darf keine Graph-Konstante sein, sonst kostet
    jede Referenz-Aenderung ein Rekompilat und einen Prozess-Neustart).
    emb [n, 512] ist das L2-normierte Embedding, das die r-Stufe liefert; die Rechnung
    ist dieselbe wie im frueheren Graphen (MatMul -> Reshape -> ReduceMax), nur in
    numpy-float32 statt im Backend. -> [n, Personen]"""
    e = np.asarray(emb, np.float32)
    if e.ndim == 1:
        e = e.reshape(1, -1)
    s = e @ erk["refs_t"]                                    # [n, Personen * je_person]
    return s.reshape(e.shape[0], erk["personen"], erk["je_person"]).max(axis=2)


def urteils_latten(plan):
    """Die Urteils-Latten wie analyze.py:114-133 und :197-201. Werte aus dem Messplan
    (argv_fest = die argv, die verifyd.run_analyze baut): Kante, win_thresh,
    Blickfenster, Anker, Pose; die Guete-Latten wie analyze._latte_aufloesen (nicht
    gesetzt -> guete.STIMM_DEFAULT, gesetzt -> auf guete.STIMM_BODEN geklemmt)."""
    fest = plan["argv_fest"]

    def latte(schluessel, mass):
        w = fest.get(schluessel)
        return guete.STIMM_DEFAULT[mass] if w is None else max(float(w), guete.STIMM_BODEN[mass])

    lat = {"urteil_kante": float(fest["urteil_kante"]), "win_thresh": float(fest["win_thresh"]),
           "blick_fenster_s": float(fest["blick_fenster_s"]),
           "urteil_anker": float(fest["urteil_anker"]),
           "pose": max(0.0, float(fest["urteil_pose"])),
           "guete_e": latte("urteil_guete_e", "empfinden"), "guete_t": latte("urteil_guete_t", "t"),
           # v8: die Latten der fd-Regel. Die Schluessel kommen aus der Signatur von
           # face_audit.ist_fehldetektion selbst (FD_VORGABE), die Werte aus dem Messplan
           # unter den argparse-Namen von analyze (fd_front_min, fd_sharp_min, fd_det_max);
           # fehlt einer, gilt die Vorgabe der Hausregel.
           "fd": {k: float(fest.get("fd_" + k, v)) for k, v in FD_VORGABE.items()}}
    if lat["pose"] > 0 and lat["guete_e"] <= 0 and lat["guete_t"] <= 0:
        lat["pose"] = 0.0                                           # analyze.py:197-201
    return lat


# ------------------------------------------------------------------ Kandidaten und Bilder
def kand_gate(f):
    """Das Kandidaten-Gate von analyze.py:711-712 — UNABHAENGIG von der Kaskade. Es ist
    keine Teilmenge von ihr: ein Gesicht kann an e/t/p scheitern und trotzdem hier
    durchkommen (dann braucht es die Erkennungs-Stufe extra).
    Nebenbei: es trifft NIE eine Fehldetektion, denn fd verlangt det < fd_det_max (0,70)
    und das Gate det >= 0,7 — die beiden Mengen sind disjunkt, ohne dass hier gefiltert
    werden muss."""
    return (f["front"] is not None and f["sharp"] is not None
            and f["k"] >= KAND_KANTE and f["front"] >= KAND_FRONT
            and f["det"] >= KAND_DET and f["sharp"] >= KAND_SHARP)


class Bildvorrat:
    """Die drei Streaming-Argmaxe je Person und der Kandidaten-Vorrat EINES Events (v8).

    PUFFER-POLITIK: der Sieger-Frame wird nicht kopiert, sondern FESTGEHALTEN. Der
    Decoder-Strom legt je Frame ein eigenes bytes-Objekt aus der Pipe an und legt die
    beiden Sichten darauf (np.frombuffer), also hat jeder Frame seinen eigenen Puffer,
    den niemand ueberschreibt; die Engines KOPIEREN daraus in ihre Geraetepuffer und
    fassen den Host-Puffer nicht an. Eine Referenz kostet damit 0 Byte und 0 Zeit, sie
    haelt nur 12,4 MB (4K) laenger im Speicher. Mehrere Argmaxe auf demselben Frame
    teilen ihn; ein Zaehlwerk gibt ihn frei, sobald der letzte Argmax weiterzieht.

    Ausgewertet wird erst am Event-Ende (schreiben): nur Frames, die wirklich ein Bild
    liefern, werden nach BGR gewandelt — mit dem win_thresh-Gate von analyze.py:911 sind
    das ueblicherweise ein oder zwei je Event.
    """

    def __init__(self, W, H, lat, mit_refs, erk, modell):
        self.W, self.H, self.lat = W, H, lat
        self.mit_refs, self.erk, self.modell = mit_refs, erk, modell
        self.rahmen = {}          # Frame-Index -> [(y, uv), Haltezahl]
        self.rahmen_max = 0       # Spitze der gleichzeitig gehaltenen Frames
        self.best = {}            # Person -> (Score, Frame-Index, enge Box)
        self.show = {}            # Person -> (Flaeche, Frame-Index, Umfeld-Box)
        self.nnctx = {}           # Person -> (Score, Frame-Index, Umfeld-Box)
        self.enroll = {}          # Person -> (Score, Frame-Index, Kandidaten-Zeile)
        self.fremd = None         # (det*Flaeche, Frame-Index, Kandidaten-Zeile)

    def _halten(self, i, rahmen):
        e = self.rahmen.get(i)
        if e is None:
            self.rahmen[i] = [rahmen, 1]
            self.rahmen_max = max(self.rahmen_max, len(self.rahmen))
        else:
            e[1] += 1

    def _loesen(self, i):
        e = self.rahmen.get(i)
        if e is not None:
            e[1] -= 1
            if e[1] <= 0:
                del self.rahmen[i]

    def _tausch(self, d, schluessel, rang, i, rahmen, daten):
        """Neuen Sieger eintragen: erst den neuen Frame halten, dann den alten loesen —
        in dieser Reihenfolge, damit ein Sieger, der auf DEMSELBEN Frame bleibt, ihn nicht
        zwischenzeitlich verliert."""
        alt = d.get(schluessel)
        d[schluessel] = (rang, i, daten)
        self._halten(i, rahmen)
        if alt is not None:
            self._loesen(alt[1])

    def frame_zug(self, faces, i, rahmen, fps):
        """Die Argmaxe dieses Frames nachziehen (analyze.py:694-742). Reihenfolge und
        Vergleichszeichen sind die von analyze: strikt > haelt das ERSTE Maximum, und die
        Sentinel 0 / -1,0 / -2,0 stehen an derselben Stelle.

        UNTERSCHIED ZU ALT, bewusst: dort hat JEDE Detektion Scores, hier nur die
        Kaskaden-Ueberlebenden (und im Kandidaten-Zweig die Gate-Erfueller). Die Argmaxe
        laufen deshalb ueber dieselbe Menge, die auch zusammenfassen() sieht — sonst
        stuende im Dateinamen ein NN-Wert, den die Zusammenfassung nicht kennt."""
        wt = self.lat["win_thresh"]
        for f in faces:
            x1, y1, x2, y2 = f["_bb"]
            sc = f["sc"]
            if sc is not None:
                flaeche = (x2 - x1) * (y2 - y1)
                cbox = ctx_box(x1, y1, x2, y2, self.W, self.H)
                for pp, s in sc.items():
                    if s >= wt and flaeche > self.show.get(pp, (0,))[0]:
                        self._tausch(self.show, pp, flaeche, i, rahmen, cbox)
                    if s > self.nnctx.get(pp, (-1.0,))[0]:
                        self._tausch(self.nnctx, pp, s, i, rahmen, cbox)
                    if s > self.best.get(pp, (-2.0,))[0]:
                        self._tausch(self.best, pp, s, i, rahmen, f["_bb"])
            if not f["kand"]:
                continue
            ksc = f["sc"] if f["sc"] is not None else f.get("ksc")
            if not ksc or f["_emb"] is None:
                continue
            kd = {"t": round(i / fps, 1), "bw": f["bw"], "bh": f["bh"],
                  "front": round(f["front"], 2), "det": round(f["det"], 2),
                  "sharp": round(f["sharp"], 0),
                  "emb": [round(float(v), 5) for v in f["_emb"]],
                  # MESSKARTE (analyze.py:718-734): was die Kaskade in DIESEM Durchlauf
                  # ohnehin gemessen hat, nichts zusaetzlich. Kein Weg dorthin -> None.
                  "mk_fiqa_t": f["t"], "mk_empf": f["e"],
                  "mk_quelle": (MK_QUELLE if (f["t"] is not None and f["e"] is not None)
                                else None),
                  "mk_modell": self.modell}
            p = max(ksc, key=ksc.get)
            bester = max(ksc.values())
            if ksc[p] >= KAND_SCORE_MIN and ksc[p] == bester:
                if ksc[p] > self.enroll.get(p, (-1.0,))[0]:
                    self._tausch(self.enroll, p, ksc[p], i, rahmen,
                                 ({**kd, "person": p, "score": round(ksc[p], 3)}, f["_bb"]))
            elif bester < FREMD_UNTER:
                guete_wert = f["det"] * (x2 - x1) * (y2 - y1)
                if self.fremd is None or guete_wert > self.fremd[0]:
                    alt = self.fremd
                    self.fremd = (guete_wert, i,
                                  ({**kd, "person": None, "score": round(bester, 3)},
                                   f["_bb"]))
                    self._halten(i, rahmen)
                    if alt is not None:
                        self._loesen(alt[1])

    def _kandidaten(self):
        """Die Kandidaten-Zeilen des Events mit dem Neuheits-Kriterium (analyze.py:1011-1020).
        nn_eigen kommt aus dem Referenz-Block DIESER Person in erk['refs'] — er ist auf die
        groesste Anzahl aufgefuellt (Wiederholung der ersten Zeile), was das Maximum nicht
        aendert. REIHENFOLGE: sortiert statt Einfuegereihenfolge wie in analyze, damit die
        Datei bei gleichen Werten dieselbe Pruefsumme hat."""
        je = self.erk["je_person"]
        aus = []
        for p in sorted(self.enroll):
            _s, i, (kd, bb) = self.enroll[p]
            v = np.asarray(kd["emb"], np.float32)
            if p in self.mit_refs:
                q = self.mit_refs.index(p)
                nn_eigen = float((self.erk["refs"][q * je:(q + 1) * je] @ v).max())
            else:
                nn_eigen = 0.0
            if nn_eigen >= NEUHEIT_AB:
                continue                      # bringt keine Vielfalt
            aus.append((i, {**kd, "nn_eigen": round(nn_eigen, 3)}, bb))
        if self.fremd is not None:
            aus.append((self.fremd[1], self.fremd[2][0], self.fremd[2][1]))
        return aus

    def schreiben(self, ordner, label, eid, persons, alle):
        """Bestbilder, Anzeige-Bilder und Kandidaten dieses Events schreiben. Jeder
        gebrauchte Frame wird GENAU EINMAL nach BGR gewandelt; das win_thresh-Gate ist das
        von analyze.py:911 (ohne es truege ein Bild einen Personennamen, den die Zahlen
        nicht hergeben). -> Bilanz"""
        kand = self._kandidaten()
        bgr = {}

        def bild(i):
            b = bgr.get(i)
            if b is None:
                b = bgr[i] = nv12_bgr(self.rahmen[i][0], self.W, self.H)
            return b

        gebraucht = {i for i, _kd, _bb in kand}
        for person in alle:
            rec = persons.get(person)
            if rec and rec["max"] >= self.lat["win_thresh"]:
                for d in (self.best, self.show, self.nnctx):
                    if person in d:
                        gebraucht.add(d[person][1])
        if gebraucht:
            os.makedirs(ordner, exist_ok=True)
        bilanz = collections.Counter()
        for person in alle:
            rec = persons.get(person)
            if not rec or rec["max"] < self.lat["win_thresh"]:
                continue
            mx = rec["max"]
            eintrag = self.best.get(person)
            if eintrag is not None:
                x1, y1, x2, y2 = eintrag[2]
                c = bild(eintrag[1])[y1:y2, x1:x2]
                if c.size:
                    cv2.imwrite(os.path.join(
                        ordner, f"{label}_best_{person}_NN{mx:.2f}_t{rec['best_t']:.0f}s.jpg"), c)
                    bilanz["best"] += 1
            s = self.show.get(person) or self.nnctx.get(person)
            if s is not None:
                a1, b1, a2, b2 = s[2]
                c = bild(s[1])[b1:b2, a1:a2]
                if c.size:
                    cv2.imwrite(os.path.join(
                        ordner, f"{label}_show_{person}_NN{mx:.2f}.jpg"), c)
                    bilanz["show"] += 1
        if kand:
            with open(os.path.join(ordner, "kandidaten.jsonl"), "a", encoding="utf-8") as kf:
                for nr, (i, kd, bb) in enumerate(kand):
                    x1, y1, x2, y2 = bb
                    datei = f"{label}_enroll_{kd['person'] or 'FREMD'}_{nr}.jpg"
                    c = bild(i)[y1:y2, x1:x2]
                    if c.size:
                        cv2.imwrite(os.path.join(ordner, datei), c)
                    kf.write(json.dumps({**kd, "datei": datei, "label": label,
                                         "source": eid}, ensure_ascii=False) + "\n")
                    bilanz["kandidaten"] += 1
                kf.flush()
        return {**bilanz, "rahmen_gewandelt": len(bgr), "rahmen_spitze": self.rahmen_max}


# ------------------------------------------------------------------ Die Kaskade
def event_rechnen(engine, g, clip, schritt, schwelle, fps, alle, mit_refs, erk, lat,
                  zaehler, zeiten, vorrat=None):
    """EIN Event: decodieren, je Sample-Frame und Gesicht die fuenf Werte in fester
    Reihenfolge, Abbruch beim ersten Wert ausserhalb seiner Latte; die Erkennung
    bekommt nur ein Gesicht, das alle fuenf besteht (User 11.09.: „wenn einer der
    Messwerte ausserhalb der Range ist, macht es keinen Sinn weiterzumachen", „wir
    wollen einen besseren Worker"). -> (zeilen, frames)

    Kaskade, Latten wie im Worker (urteils_latten):
      det   det-Schwelle der Kamera: darunter liefert der Detektor nichts
      k     kurze Boxkante >= urteil_kante                      CPU, ohne Kosten   SIEBT
      e     Efficient-FIQA, Guete-Latte e                        GPU-Stufe e       misst
      t     eDifFIQA-T, Guete-Latte t                            GPU-Stufe t       misst
      p     RTMPose-Kopf-Score >= urteil_pose                    GPU-Stufe p       SIEBT
      Erkennung, Scores je Person                                GPU-Stufe r + CPU-Matmul
    SIEBT/misst ist der Entscheid vom 14.09.2026 (s. gpu_stufen unten): e und t
    MESSEN nur — ihr Wert siebt die STIMMEN in `zusammenfassen` (guete.stimme_ok),
    genau wie im alten Worker, aber nicht mehr das Bild und nicht mehr die Akte.
    Kante, fd und Pose sieben die Kaskade weiter; wer dort ausscheidet, bekommt
    keine Erkennung. Nicht messbar (leerer Box-Ausschnitt fuer e) verwirft die
    Stimme fail-closed (guete.stimme_ok), nimmt dem Fund aber keinen Score. Eine
    Latte <= 0 ist aus: der Wert wird nicht gemessen. Werte ungerundet; "abbruch"
    nennt die Stufe, an der ein Gesicht die KASKADE verliess; zaehler: wie viele
    Gesichter jede Stufe bestanden.

    v7: die Stufen laufen ueber den Satz dieses Rechenstrangs (satz.stufe), in
    Aufrufen fester Breite; das RGB-Vollbild entsteht einmal je Frame in satz.det()
    und bleibt dabei auf der GPU.

    v8: DREI Zusaetze. Die fd-Stufe RECHNET vor der k-Latte fuer jede Detektion
    (Nachzug 13.09.), nimmt ihre fd-Gesichter aber erst hinter der k-Latte aus der
    Kaskade — zwischen k und e; der Kandidaten-Zweig laeuft HINTER ihr und ist von ihrem
    Ergebnis unabhaengig (er kann eine eigene Erkennungs-Stufe ausloesen); die Argmaxe
    der Bestbilder wandern in den `vorrat`, der die Sieger-Frames festhaelt. `zeiten`
    sammelt die Stufenzeiten in Sekunden.

    E1: die r-Stufe liefert jetzt das Embedding, die Scores rechnet scores_rechnen auf
    der CPU (Kopf dieser Datei, Konzept §1c). Die Stelle im Ablauf ist dieselbe, und die
    Zeit dafuer bleibt im Zeitnehmer der Stufe."""
    satz = g.satz()
    zeilen, frames = [], 0
    ohne = {pn: -1.0 for pn in alle if pn not in mit_refs}              # wie analyze.nn
    fd_seite = g.seiten[FD][0]
    fd_latten = lat["fd"]
    # DIE WIRKSTELLE DER GUETE-LATTE (User-Entscheid 14.09.2026, Eich-Messung
    # runs/guete_eich_20260914). Das dritte Feld sagt, WAS eine Stufe siebt:
    #
    #   True  = sie siebt die KASKADE. Wer sie reisst, bekommt keine Erkennung, keinen
    #           Score, kein Bestbild und keine Akte-Kennwerte.
    #   False = sie MISST nur. Der Wert entsteht, er steht in der Akte, und er siebt
    #           allein die STIMMEN (`zusammenfassen.stimme` -> guete.stimme_ok).
    #
    # Warum e und t hier auf False stehen, und zwar GEMESSEN: im alten Worker
    # entstanden persons.max/median/best ueber ALLE Detektionen (analyze.py:831-833),
    # und die Guete-Latte siebte dort ausschliesslich die Stimmen (analyze.py:869-872).
    # Das Bild-Gate (analyze.py:915, `mx >= win_thresh`) hat die Guete-Latte deshalb
    # NIE gesehen. Der neue Kaskaden-Aufbau hat sie zum ersten Mal auch vor das Bild
    # und vor die Akte gestellt — dieselbe Zahl, eine andere Stelle. Die Rechnung
    # ueber alle 170 Ereignisse des Eich-Laufs beziffert den Preis genau:
    #   Person-Bilder   Prod-Akte 75 · mit der Latte in der Kaskade 65 · hier wieder 75
    #   Ereignisse mit >= 1 Bild   Akte 67 · mit der Latte in der Kaskade 59 · hier 67
    #   Namen anders als die Prod-Akte: 0 — kein Name kommt dazu, keiner faellt weg.
    # Die LATTE selbst bleibt unangetastet (0,10, core/guete); geaendert ist allein,
    # WORAUF sie wirkt. Die Pose-Stufe siebt weiter die Kaskade: sie stand auch im
    # alten Worker vor der Stimme, und die Eich-Messung lief genau so (Diagnose-Lauf
    # mit `--urteil-pose 0.65` und nicht-siebenden Guete-Latten).
    gpu_stufen = (
        ("e", lat["guete_e"], False,
         lambda f: theta_e(f["_bb"], g.W, g.H, g.seiten["e"], g.nm)),
        ("t", lat["guete_t"], False,
         lambda f: theta_t(f["_kp"], g.seiten["t"][0], g.nm)),
        ("p", lat["pose"], True,
         lambda f: theta_p(f["_box"], g.W, g.H, g.nm)))
    for i, y, uv in engine.frames(clip, g.W, g.H, schritt):
        frames += 1
        t0 = time.monotonic()
        dets, kpss = detektor(satz.det(y, uv), g.det_wh, g.det_scale, schwelle, g.zentren)
        zeiten["det"] += time.monotonic() - t0
        if len(dets) == 0:
            continue
        faces = []
        for d, kp in zip(dets, kpss):
            bb = [max(0, int(v)) for v in d[:4]]                    # wie analyze.py:568
            faces.append({"i": int(i), "zeit_s": i / fps, "det": float(d[4]),
                          "k": int(min(bb[2] - bb[0], bb[3] - bb[1])),
                          "bw": int(bb[2] - bb[0]), "bh": int(bb[3] - bb[1]),
                          "front": None, "sharp": None, "fd": None, "kand": False,
                          "e": None, "t": None, "p": None, "norm": None, "sc": None,
                          "abbruch": None, "_bb": bb, "_box": d[:4], "_kp": kp,
                          "_emb": None})
        zaehler["gesichter"] += len(faces)
        # --- fd-Stufe (v8): front (1k3d68) und sharp (Laplace) fuer JEDE Detektion, in
        #     EINEM Aufruf je Portion. SIE LAEUFT VOR DER K-LATTE (Nachzug 13.09., Users
        #     Entscheid 4 der v8-Abnahme): die Konsumenten der Signatur zaehlen ALLE
        #     Detektionen (faces_geprueft = len(faces) - fd_n, max_bw ueber die Nicht-fd;
        #     analyze.py:941-942), also darf keine Detektion ohne fd/front/sharp bleiben.
        #     Vorher liefen die Winz-Detektionen unter urteil_kante ohne diese Werte durch.
        #     Der KASKADEN-AUSTRITT der fd-Gesichter bleibt dagegen hinter der k-Latte
        #     (unten): wer schon an der Kante scheitert, behaelt sein Abbruch-Zeichen "k",
        #     und k_ok/fd_ok zaehlen dieselbe Menge wie zuvor.
        if faces:
            t0 = time.monotonic()
            th, matrizen, zuege = [], [], []
            for f in faces:
                t, M = theta_fd(f["_box"], fd_seite, g.nm)
                th.append(t)
                matrizen.append(M)
                zuege.append(leinwand_zug(f["_bb"], g.W, g.H))
            aus = satz.stufe_fd(th, zuege)
            for f, M, zug, (pts, sL, sL2) in zip(faces, matrizen, zuege, aus):
                npx = zug[4]
                f["front"] = fd_front(pts, M, fd_seite)[0]
                # analyze.sharp: leerer Crop -> 0.0. Sonst Varianz aus Summe und Summe der
                # Quadrate; das Klemmen auf 0 faengt nur die Rundung bei nahezu konstanten
                # Crops (cv2.var() kann nicht negativ werden).
                f["sharp"] = 0.0 if npx == 0 else max(0.0, sL2 / npx - (sL / npx) ** 2)
                f["fd"] = bool(face_audit.ist_fehldetektion(f["front"], f["sharp"],
                                                            f["det"], **fd_latten))
                if zug[5]:
                    zaehler["leinwand_beschnitten"] += 1
            zeiten[FD] += time.monotonic() - t0
        weiter = faces
        if lat["urteil_kante"] > 0:
            for f in weiter:
                if f["k"] < lat["urteil_kante"]:
                    f["abbruch"] = "k"
            weiter = [f for f in weiter if f["abbruch"] is None]
        zaehler["k_ok"] += len(weiter)
        # fd-Gesichter verlassen die Kaskade hier — gerechnet ist ihre Signatur schon oben,
        # gemessen ist sie auch dort; dies ist nur noch der Austritt.
        for f in weiter:
            if f["fd"]:
                f["abbruch"] = FD
        weiter = [f for f in weiter if f["abbruch"] is None]
        zaehler["fd_ok"] += len(weiter)
        for name, latte, siebt, theta in gpu_stufen:
            if latte <= 0 or not weiter:
                continue
            t0 = time.monotonic()
            th = [theta(f) for f in weiter]
            messbar = [(f, m) for f, m in zip(weiter, th) if m is not None]
            for f, m in zip(weiter, th):
                if m is None and siebt:
                    f["abbruch"] = name                             # nicht messbar
            if messbar:
                aus = satz.stufe(name, [m for _f, m in messbar])
                for (f, _m), w in zip(messbar, aus):
                    f[name] = float(np.ravel(w[0])[0])
                    if siebt and f[name] < latte:
                        f["abbruch"] = name
            # NUR eine siebende Stufe verkleinert die Kaskade. Eine messende laesst
            # `weiter` unveraendert — ihr Wert wirkt erst in der Stimm-Frage
            # (`zusammenfassen`). Ein nicht messbarer Wert verwirft dort die Stimme
            # fail-closed (guete.stimme_ok), er nimmt dem Fund aber nicht mehr seinen
            # Score: genau das ist der Unterschied, um den es hier geht.
            if siebt:
                weiter = [f for f in weiter if f["abbruch"] is None]
                zaehler[name + "_ok"] += len(weiter)
            else:
                # DER ZAEHLER BEHAELT SEINE BEDEUTUNG: „wie viele Gesichter haben
                # diese Stufe bestanden" (Kopf von event_rechnen). Bei einer
                # messenden Stufe ist das NICHT `len(weiter)` — dort laufen auch die
                # weiter, die die Latte reissen. Gezaehlt wird deshalb, wer sie
                # bestanden haette; sonst waere die Diagnose-Zeile nach diesem Umbau
                # still zu einer anderen Groesse geworden (K1).
                zaehler[name + "_ok"] += sum(1 for f in weiter if f[name] is not None
                                             and f[name] >= latte)
            zeiten[name] += time.monotonic() - t0
        if weiter:
            t0 = time.monotonic()
            aus = satz.stufe("r", [theta_t(f["_kp"], g.seiten["r"][0], g.nm)
                                   for f in weiter])
            # w[0]: L2-normiertes Embedding [512], w[1]: Feature-Norm (E1: die Stufe
            # liefert keine Scores mehr, die rechnet scores_rechnen hier)
            sc = scores_rechnen([w[0] for w in aus], erk)
            for q, (f, w) in enumerate(zip(weiter, aus)):
                f["sc"] = {**ohne, **{pn: float(sc[q][j]) for j, pn in enumerate(mit_refs)}}
                f["norm"] = float(np.ravel(w[1])[0])
                f["_emb"] = w[0]
            zeiten["r"] += time.monotonic() - t0
        # --- Kandidaten-Zweig (v8): Gate-Erfueller bekommen die Erkennung AUCH ohne
        #     Kaskade. Nur die, die sie nicht schon haben — die uebrigen Gate-Erfueller
        #     tragen ihr Embedding aus dem Aufruf oben.
        gate = [f for f in faces if kand_gate(f)]
        for f in gate:
            f["kand"] = True
        offen = [f for f in gate if f["_emb"] is None]
        if offen:
            t0 = time.monotonic()
            aus = satz.stufe("r", [theta_t(f["_kp"], g.seiten["r"][0], g.nm)
                                   for f in offen])
            ksc = scores_rechnen([w[0] for w in aus], erk)
            for q, (f, w) in enumerate(zip(offen, aus)):
                # NICHT in "sc": die Zusammenfassung rechnet ueber die Kaskade, ein
                # Kandidaten-Score wuerde ihre Kennwerte verschieben. Eigener Schluessel.
                f["ksc"] = {**ohne, **{pn: float(ksc[q][j]) for j, pn in enumerate(mit_refs)}}
                f["_emb"] = w[0]
            zeiten["kand"] += time.monotonic() - t0
            zaehler["kand_extra"] += len(offen)
        zaehler["kand_gate"] += len(gate)
        if vorrat is not None:
            t0 = time.monotonic()
            vorrat.frame_zug(faces, int(i), (y, uv), fps)
            zeiten["bilder"] += time.monotonic() - t0
        for f in faces:
            del f["_bb"], f["_box"], f["_kp"], f["_emb"]
        zeilen.extend(faces)
    return zeilen, frames


# ------------------------------------------------------------------ Zusammenfassung
def zusammenfassen(zeilen, personen, lat):
    """Zusammenfassung je Person wie analyze.py:824-899, die Kennwerte, aus denen verifyd
    das Urteil macht, ueber die Gesichter MIT Erkennung (also mit Score); max, median
    und best_* laufen ueber genau diese Menge. Die Stimm-Filter (Kante,
    guete.stimme_ok, Pose; analyze._stimme_zaehlt, analyze.py:156-170) stehen
    wortgleich drin und sieben die STIMMEN — nicht die Kennwerte.
    best_front/best_pose fehlen, bis die Landmarks eingebaut sind.

    WIRKSTELLE (User-Entscheid 14.09.2026): seit die Guete-Stufen e/t nur noch
    MESSEN und nicht mehr die Kaskade sieben (event_rechnen, gpu_stufen), ist diese
    Menge wieder die des alten Workers — alle Detektionen, die Kante, fd und Pose
    bestanden haben, mit ihrem Score. Die Guete-Latte trifft sie erst hier, in
    `stimme`, und damit genau dort, wo sie im alten Worker immer stand. Der Filter
    unten (`sc is not None`) ist deshalb keine Latten-Frage mehr, sondern nur noch
    die technische: hat dieser Fund ueberhaupt eine Erkennung bekommen."""
    zeilen = [f for f in zeilen if f["sc"] is not None]
    if not zeilen:
        return {}
    uk, wt = lat["urteil_kante"], lat["win_thresh"]
    bw_s, ank = lat["blick_fenster_s"], lat["urteil_anker"]

    def stimme(f):
        return (guete.stimme_ok(lat["guete_e"], lat["guete_t"], f["e"], f["t"])
                and (lat["pose"] <= 0 or (f["p"] is not None and f["p"] >= lat["pose"])))

    aus = {}
    for person in personen:
        sc_list = [f["sc"][person] for f in zeilen]
        best = max(zeilen, key=lambda f: f["sc"][person])
        ts = sorted((f["zeit_s"], f["sc"][person], fi) for fi, f in enumerate(zeilen)
                    if (uk <= 0 or min(f["bw"], f["bh"]) >= uk) and stimme(f))
        win = max((sum(1 for (t, s, _i) in ts if t0 <= t <= t0 + 3.0 and s >= wt)
                   for t0, _s0, _i0 in ts), default=0)
        stimm_idx = sorted(fi for (_t, s, fi) in ts if s >= wt)
        blick_n, blick_max, blick_t0 = 0, 0.0, None
        if bw_s > 0:
            st = [(t, s) for (t, s, _i) in ts if s >= wt]
            for (t0, _s0) in st:
                fen = [s for (t, s) in st if t0 <= t < t0 + bw_s]
                if ank > 0 and max(fen, default=0.0) < ank:
                    continue
                if len(fen) > blick_n:
                    blick_n, blick_max, blick_t0 = len(fen), max(fen), t0
        # n_ge40/n_ge50: dieselben Diagnose-Zaehler wie analyze.py:834
        aus[person] = {"max": round(float(max(sc_list)), 3),
                       "median": round(float(np.median(sc_list)), 3), "n": len(sc_list),
                       "n_ge40": int(sum(s >= 0.40 for s in sc_list)),
                       "n_ge50": int(sum(s >= 0.50 for s in sc_list)),
                       "win3s": win, "best_wh": f"{best['bw']}x{best['bh']}",
                       **({"blick_n": blick_n, "blick_max": round(blick_max, 3),
                           "blick_t0": round(blick_t0, 1) if blick_t0 is not None else None}
                          if bw_s > 0 else {}),
                       **({"stimm_idx": stimm_idx} if stimm_idx else {}),
                       "best_det": round(best["det"], 2), "best_t": round(best["zeit_s"], 1),
                       # Feature-Norm des besten Gesichts (v2): nur mitgeschrieben, in
                       # keinem Urteil benutzt — Material fuer die Eichung.
                       "best_norm": (round(best["norm"], 2) if best["norm"] is not None
                                     else None)}
    return aus


# ------------------------------------------------------------------ Aufbau und Kopfzeile
def kern_argumente(ap):
    """Die Argumente, die ALLE vier Huellen gemeinsam haben. An EINER Stelle, damit
    Einzel- und Mehrstrang-Fassung und die beiden Backends nicht auseinanderlaufen."""
    ap.add_argument("--config", required=True, help="Config-Store (config.json)")
    ap.add_argument("--clips", required=True, help="Ordner mit <eid>.mp4")
    ap.add_argument("--plan", required=True, help='JSON mit "events": [[eid, kamera], ...]')
    ap.add_argument("--out", required=True, help="Ergebnisordner")
    ap.add_argument("--refcache", required=True,
                    help="refcache.npz des alten Workers (Referenz-Embeddings je Person)")
    ap.add_argument("--bilder", help="Ordner fuer Bestbilder, Anzeige-Bilder, "
                                     "Kandidaten-Crops und kandidaten.jsonl (v8). "
                                     "Vorgabe: <out>/bilder, je Auftrag ein Unterordner.")


def mt_argumente(ap):
    """Die beiden Argumente der Mehrstrang-Huellen."""
    ap.add_argument("--threads", type=int, default=1,
                    help="Rechenstraenge in diesem Prozess (Vorgabe 1 = Einzelreihe)")
    ap.add_argument("--jobs", type=int, default=1,
                    help="Wiederholungen JE Plan-Event in der Schlange (Vorgabe 1). "
                         "Mehr als 1 ist eine DURCHSATZ-Messung.")


def clip_geometrien(clips, events):
    """(Breite, Hoehe, fps) je Event, aus den Metadaten. -> {eid: (W, H, fps)}"""
    geo = {}
    for eid, _kamera in events:
        meta = decode._probe(os.path.join(clips, eid + ".mp4"))
        geo[eid] = (int(meta["breite"]), int(meta["hoehe"]), meta["fps"] or 25)  # decode.py:146
    return geo


def kopf(engine, graphen, erk, alle, mit_refs, lat, extra=None):
    """Die Kopfzeile eines Laufs: was WIRKLICH gebaut wurde, an den Objekten gezaehlt.
    Damit kann ein Lauf nicht als Variante durchgehen, die er nicht war. Der Kern nennt,
    was backend-frei ist; was die Engine traegt, kommt aus ihrer Auskunft (sie darf einen
    eigenen 'fd'-Block mitgeben, der in den des Kerns einfliesst)."""
    g0 = next(iter(graphen.values()))
    auskunft = dict(engine.kopf_auskunft(graphen))
    fd = {"leinwand": LEINWAND, "punkte": len(mean_lmk()), "seiten": list(g0.seiten[FD]),
          "polster": LM_POLSTER,
          "grau": {"gewichte": list(GRAU_W), "schiebung": GRAU_SHIFT}}
    fd.update(auskunft.pop("fd", {}))
    return {"geometrien": [f"{w}x{h}" for w, h in graphen],
            "aufruf_breite": AUFRUF_BREITE, "stufen": list(engine.stufen_folge),
            "seiten": {k: list(v) for k, v in sorted(g0.seiten.items())},
            "bau_je_geometrie": {f"{g.W}x{g.H}": {"gesamt_s": round(g.bau_s, 2),
                                                  "bestand_s": round(g.bau_geteilt_s, 2),
                                                  "eigen_s": round(g.bau_s - g.bau_geteilt_s, 2)}
                                 for g in graphen.values()},
            "personen": len(alle), "mit_refs": len(mit_refs),
            "refs_je_person": erk["je_person"],
            # E1: die Referenz-Matrix ist keine Graph-Konstante mehr — der Score-Matmul
            # laeuft auf der CPU. Im Kopf, weil ein Lauf nicht als die andere Bauart
            # durchgehen soll.
            "score_matmul": "cpu",
            "vorlauf": VORLAUF, "pipe": pipe_probe(), "latten": lat,
            "fd": fd, **auskunft, **(extra or {})}


# ------------------------------------------------------------------ Auftragsverwaltung
def auftraege_bauen(events, wiederholungen):
    """Die Schlange: Runde fuer Runde ueber die Plan-Events (A B C A B C ...), damit bei
    mehreren Threads nicht alle gleichzeitig auf demselben Event sitzen.
    -> [(nr, eid, kamera, wdh, dateiname)]"""
    aus = []
    for w in range(wiederholungen):
        for eid, kamera in events:
            datei = f"{eid}.jsonl" if w == 0 else f"{eid}__w{w}.jsonl"
            aus.append((len(aus), eid, kamera, w, datei))
    return aus


def auftrag_rechnen(engine, graphen, geo, fest, eid, kamera, datei):
    """EIN Auftrag: Kaskade, Zusammenfassung, Bilder, Ergebnisdatei. Der Rumpf ist
    derselbe fuer Einzel- und Mehrstrang-Fassung und fuer beide Backends.
    -> (Auftragszeile ohne Thread-Felder, persons)"""
    W, H, fps = geo[eid]
    schritt = max(1, int(round(fps / fest["fps_sample"])))        # wie decode.py:148
    schwelle = det_schwelle(fest["det_global"], fest["guards"], kamera)
    zaehler, zeiten = collections.Counter(), collections.Counter()
    t_start = time.monotonic()
    # v8: Bildvorrat und Bilder-Ordner JE AUFTRAG (Stamm = der Name der Ergebnisdatei
    # ohne Endung). Damit schreiben zwei Threads nie in dieselbe kandidaten.jsonl und
    # eine Wiederholung (__w1) ueberschreibt nichts — Voraussetzung dafuer, dass zwei
    # 2T-Laeufe dieselben Pruefsummen tragen.
    vorrat = Bildvorrat(W, H, fest["lat"], fest["mit_refs"], fest["erk"], fest["modell"])
    zeilen, frames = event_rechnen(engine, graphen[(W, H)],
                                   os.path.join(fest["clips"], eid + ".mp4"),
                                   schritt, schwelle, fps, fest["alle"], fest["mit_refs"],
                                   fest["erk"], fest["lat"], zaehler, zeiten, vorrat)
    persons = zusammenfassen(zeilen, fest["alle"], fest["lat"])
    # Die Bilder und Kandidaten gehoeren IN die Messung: sie sind Teil der drei
    # Zusaetze, die ins Tempo-Band passen muessen.
    t_b = time.monotonic()
    bilanz = vorrat.schreiben(os.path.join(fest["bilder"], datei.rsplit(".", 1)[0]),
                              kamera, eid, persons, fest["alle"])
    zeiten["schreiben"] += time.monotonic() - t_b
    t_ende = time.monotonic()
    with open(os.path.join(fest["out"], datei), "w", encoding="utf-8") as ef:
        for z in zeilen:
            ef.write(json.dumps(z, ensure_ascii=False) + "\n")
    return ({"eid": eid, "kamera": kamera, "wall_s": round(t_ende - t_start, 2),
             "frames": frames, "gesichter": len(zeilen), "stufen": dict(zaehler),
             "schritt": schritt, "det_schwelle": schwelle, "geometrie": f"{W}x{H}",
             "zeiten_ms": {k: round(v * 1000) for k, v in sorted(zeiten.items())},
             "bilder": dict(bilanz)}, persons, t_start, t_ende)


def _fest_bauen(a, fps_sample, det_global, guards, alle, mit_refs, erk, lat, zf):
    """Alles, was jeder Auftrag unveraendert braucht, in einem dict — damit die
    Auftrags-Funktion eine Signatur behaelt, die man noch lesen kann."""
    return {"fps_sample": fps_sample, "det_global": det_global, "guards": guards,
            "alle": alle, "mit_refs": mit_refs, "lat": lat, "erk": erk, "zf": zf,
            "clips": a.clips, "out": a.out,
            "modell": face_audit.aktuelles_modell(),
            "bilder": a.bilder or os.path.join(a.out, "bilder")}


def _aufbau(a):
    """Config, Plan, Latten, Referenzen, Geometrien — der gemeinsame Vorlauf beider
    Fassungen. -> (fps_sample, det_global, guards, plan, lat, alle, mit_refs, erk, geo)"""
    fps_sample, det_global, guards = cfg_lesen(a.config)
    with open(a.plan, encoding="utf-8") as f:
        plan = json.load(f)
    lat = urteils_latten(plan)
    alle, mit_refs, erk = referenzen_laden(a.refcache)
    os.makedirs(a.out, exist_ok=True)
    geo = clip_geometrien(a.clips, plan["events"])
    return fps_sample, det_global, guards, plan, lat, alle, mit_refs, erk, geo


def lauf_einzel(engine, a):
    """Die Einzelreihe: ein Rechenstrang, jedes Plan-Event einmal. Aufbau (Graphen/
    Sessions und Warmlauf) VOR der Zeitmessung, wie in einem warmen Worker."""
    (fps_sample, det_global, guards, plan, lat, alle, mit_refs, erk, geo) = _aufbau(a)
    events = plan["events"]
    t_bau = time.monotonic()
    graphen = engine.geometrie_bauen(geo)
    t_graphen = time.monotonic() - t_bau
    for g in graphen.values():
        g.satz().warm()
    print(json.dumps(kopf(engine, graphen, erk, alle, mit_refs, lat,
                          {"aufbau_s": round(time.monotonic() - t_bau, 1),
                           "bau_s": round(t_graphen, 1), "threads": 1})), flush=True)

    with open(os.path.join(a.out, "zusammenfassung.jsonl"), "a", encoding="utf-8") as zf:
        fest = _fest_bauen(a, fps_sample, det_global, guards, alle, mit_refs, erk, lat, zf)
        for eid, kamera in events:
            s, persons, _t0, _t1 = auftrag_rechnen(engine, graphen, geo, fest, eid, kamera,
                                                   eid + ".jsonl")
            print(json.dumps(s, ensure_ascii=False), flush=True)
            zf.write(json.dumps({**s, "persons": persons}, ensure_ascii=False) + "\n")
            zf.flush()


def arbeiter(nr, schlange, engine, graphen, geo, fest, ergebnisse, barriere, t0_box,
             warm_schloss, schreib_schloss):
    """EIN Worker-Thread: erst den eigenen Satz je Geometrie anlegen und waermen, dann
    an der Barriere warten (die Zeitmessung beginnt fuer alle gemeinsam), dann
    Auftraege abarbeiten, bis die Schlange leer ist.

    t0 steht in einer Box statt als Wert im Aufruf: die Barriere setzt ihn in ihrer
    Freigabe-Aktion, also nachweislich nachdem alle gewaermt haben und bevor irgendein
    Thread weiterlaeuft."""
    for g in graphen.values():
        with warm_schloss:
            g.satz().warm()
    barriere.wait(BARRIERE_FRIST)
    t0 = t0_box["t0"]
    while True:
        try:
            job = schlange.get_nowait()
        except queue.Empty:
            return
        nr_job, eid, kamera, wdh, datei = job
        s, persons, t_start, t_ende = auftrag_rechnen(engine, graphen, geo, fest, eid,
                                                      kamera, datei)
        s = {**s, "job": nr_job, "wdh": wdh, "thread": nr, "datei": datei,
             "t_start_s": round(t_start - t0, 2), "t_ende_s": round(t_ende - t0, 2)}
        with schreib_schloss:
            ergebnisse.append(s)
            print(json.dumps({**s, "_": "job"}, ensure_ascii=False), flush=True)
            fest["zf"].write(json.dumps({**s, "persons": persons}, ensure_ascii=False) + "\n")
            fest["zf"].flush()


def lauf_mt(engine, a):
    """N Rechenstraenge in EINEM Prozess. Geteilt werden die Kompilate/Sessions, je
    Strang eigen ist der Satz (Anfragen und Geraetepuffer) — der Wert-Weg ist derselbe
    Code wie in der Einzelreihe, nur die Auftragsverwaltung ist eine andere.

    SCHLOSS-STELLEN, vollstaendig (mehr gibt es nicht):
      1. warm_schloss    um warm(). Die Threads waermen nacheinander statt gleichzeitig:
         das haelt die Reihenfolge der ersten Geraete-Allokationen fest und liegt vor
         der Zeitmessung, kostet im Lauf also nichts.
      2. schreib_schloss um das Schreiben der gemeinsamen zusammenfassung.jsonl und die
         Konsolen-Zeile. Reine Ausgabe, keine Rechnung.
    Kein globales Rechen-Schloss. Keine Stufe ist gesperrt."""
    if a.threads < 1 or a.jobs < 1:
        raise SystemExit("--threads und --jobs muessen >= 1 sein")
    (fps_sample, det_global, guards, plan, lat, alle, mit_refs, erk, geo) = _aufbau(a)
    events = plan["events"]
    t_bau = time.monotonic()
    graphen = engine.geometrie_bauen(geo)
    t_graphen = time.monotonic() - t_bau

    jobs = auftraege_bauen(events, a.jobs)
    schlange = queue.Queue()
    for j in jobs:
        schlange.put(j)
    ergebnisse = []
    warm_schloss, schreib_schloss = threading.Lock(), threading.Lock()
    # Die Barriere trennt Waermen von Messen: sie gibt erst frei, wenn alle Threads UND
    # der Hauptthread da sind, und setzt in ihrer Freigabe-Aktion den gemeinsamen
    # Nullpunkt — vor der Freigabe, also fuer alle derselbe Wert ohne Wettrennen.
    # MIT FRIST (BARRIERE_FRIST): stirbt ein Thread im Warmlauf, warten die uebrigen
    # sonst ewig und der Prozess haengt still (der offene v4-Einzeiler, Konzept §2).
    t0_box = {}
    barriere = threading.Barrier(a.threads + 1,
                                 action=lambda: t0_box.__setitem__("t0", time.monotonic()))

    with open(os.path.join(a.out, "zusammenfassung.jsonl"), "a", encoding="utf-8") as zf:
        fest = _fest_bauen(a, fps_sample, det_global, guards, alle, mit_refs, erk, lat, zf)
        threads = [threading.Thread(
            target=arbeiter,
            args=(i, schlange, engine, graphen, geo, fest, ergebnisse, barriere, t0_box,
                  warm_schloss, schreib_schloss),
            name=f"worker-{i}", daemon=False) for i in range(a.threads)]
        for th in threads:
            th.start()
        barriere.wait(BARRIERE_FRIST)                     # alle haben gewaermt
        t0 = t0_box["t0"]
        print(json.dumps(kopf(engine, graphen, erk, alle, mit_refs, lat,
                              {"aufbau_s": round(t0 - t_bau, 1),
                               "bau_s": round(t_graphen, 1),
                               "warm_s": round(t0 - t_bau - t_graphen, 1),
                               "threads": a.threads, "jobs_faktor": a.jobs,
                               "auftraege": len(jobs),
                               "saetze": {f"{g.W}x{g.H}": g.saetze
                                          for g in graphen.values()}})), flush=True)
        for th in threads:
            th.join()
        gesamt = time.monotonic() - t0
        ergebnisse.sort(key=lambda s: s["job"])
        je_thread = collections.Counter(s["thread"] for s in ergebnisse)
        print(json.dumps({
            "gesamt_s": round(gesamt, 2), "threads": a.threads, "auftraege": len(jobs),
            "fertig": len(ergebnisse),
            "summe_wall_s": round(sum(s["wall_s"] for s in ergebnisse), 2),
            "je_thread": {str(k): v for k, v in sorted(je_thread.items())},
            "saetze": {f"{g.W}x{g.H}": g.saetze for g in graphen.values()},
            "wall_je_job": [[s["job"], s["eid"][-6:], s["thread"], s["wall_s"],
                             s["t_start_s"], s["t_ende_s"]] for s in ergebnisse],
            "_": "gesamt"}, ensure_ascii=False), flush=True)
    if len(ergebnisse) != len(jobs):
        raise SystemExit(f"nur {len(ergebnisse)} von {len(jobs)} Auftraegen fertig")


def huelle(engine_klasse, beschreibung, mehrstrang):
    """Der EINE Rumpf jeder Huelle: CLI aufbauen (Kern-Argumente + die der Engine),
    Engine anlegen, Lauf starten. worker_gpu.py, worker_gpu_mt.py, worker_cuda.py und
    worker_cuda_mt.py bestehen seit E1 nur noch aus einem Aufruf dieser Funktion."""
    ap = argparse.ArgumentParser(description=beschreibung)
    kern_argumente(ap)
    engine_klasse.argumente(ap)
    if mehrstrang:
        mt_argumente(ap)
    a = ap.parse_args()
    engine = engine_klasse(a)
    (lauf_mt if mehrstrang else lauf_einzel)(engine, a)
