#!/usr/bin/env python3
"""ENGINE onnxruntime/CUDA (NVIDIA) — die Backend-Haelfte des Prototyp-Workers (E1).

HERKUNFT: herausgezogen aus dem abgenommenen v8-Prototyp `worker_cuda.py`
(md5 5e46e456). Session-Bau, ONNX-Graphen, Decoder-Anbindung, Speicher-Besitz
(IO-Binding), Formstrategie und Provider-Optionen stehen hier; alles, was einen WERT
entscheidet — Kaskade, Latten, Thetas, Detektor-Nachverarbeitung, Scores,
Zusammenfassung — liegt im backend-freien `worker_kern.py`. Die Kopfabschnitte v2-v8
des Prototyps gelten unveraendert weiter; sie sind die Herleitung dieses Session-Baus
(fp16 durchgaengig ausser GridSample und den Zahlen-Nachgraphen, feste Aufrufbreite,
prozessweite Modell-Ketten, Buendelstufen nur noch fuer p).

PIXELWEG, die CPU fasst kein Pixel an:
  ffmpeg/NVDEC dekodiert, waehlt die Sample-Frames vor dem Download aus und gibt NV12
  heraus. Auf der GPU (onnxruntime, CUDA-Provider):
    A    je Frame      NV12 -> RGB-Vollbild (fp16-Kette), daraus 'det_in' (verkleinert/
                       Leinwand/normiert) fuer det_10g und 'rgb' (fp32, GridSample-Zwang)
    fd   je Detektion  Landmark-Ausschnitt -> 1k3d68, dazu die Laplace-Leinwand
    e/t/p/r            wie im Kern beschrieben, je Stufe eine eigene Session
  Zwischen den Sessions bleiben die Tensoren per IO-Binding im GPU-Speicher; zur CPU
  kommen nur Zahlen.

E1-AENDERUNG (Konzept §1c, MATMUL RAUS): graph_rec_post traegt die Referenz-Matrix
NICHT mehr. Die Erkennungs-Stufe liefert das L2-normierte Embedding [n, 512] und die
Feature-Norm; Score-Matmul und Maximum je Person rechnet der Kern auf der CPU
(worker_kern.scores_rechnen). Damit braucht ein Referenz-Wechsel weder Rekompilat noch
Prozess-Neustart, und die Wachen erk_pruefen/erk-Bindung entfallen ersatzlos — sie
schuetzten die Graph-Konstante, die es nicht mehr gibt.

KEIN RUECKFALL: nur der CUDA-Provider, der CPU-Rueckfall ist abgeschaltet
(session.disable_cpu_ep_fallback). Alle Eingangsformen sind fest (je Geometrie bzw.
Buendel-Stufe), damit ORT die Form-Rechnungen beim Bau vorausrechnet. Die NVDEC-Kette
endet mit hwdownload; ein Software-Decode laesst sie scheitern.

f32-WARP-FIX (14.09.2026, gemessen — runs/zerlegung_klein_20260914/): hinter dem
GridSample ALLER Stufen steht jetzt eine uint8-Rundung (`_u8_rundung`), damit die
Ausschnitt-Bytes dieselbe Quantisierung haben wie der alte cv2-Weg, an dem die
Referenzen gemessen sind. Die PRAEZISIONS-Haelfte des Fixes betraf nur die
OpenVINO-Seite: dort tastete der Warp in fp16 und wurde auf f32 gehoben — hier
rechnet er seit v6 schon f32 (GridSample-Zwang des CUDA-EP), nachgeprueft an den
Typen und in der Kopf-Auskunft ausgewiesen.

NICHT BITGLEICH ZU PROD: GridSample/Resize bleiben bilinear in Gleitkomma statt
OpenCV-Festkomma (nur die Quantisierung des Ergebnisses ist seit dem Fix dieselbe),
und NV12->RGB ist eine andere Umrechnung als cv2 YUV2BGR_I420.
"""
import hashlib
import json
import os
import threading
import time

import numpy as np

import worker_kern as wk                                 # noqa: E402  Bootstrap + Wert-Weg

import onnx                                              # noqa: E402
import onnxruntime as ort                                # noqa: E402
from onnx import TensorProto, helper, numpy_helper       # noqa: E402

import face_audit                                        # noqa: E402  BATCH_STUFEN, Threads

EP = "CUDAExecutionProvider"
OPSET = 16                                              # GridSample braucht >= 16
# v3d: die beiden cuDNN-Stellschrauben als benannte Konstanten an EINER Stelle.
# HEURISTIC (Variante A) und Workspace 0 (Variante B) sind am 12.09. vermessen und
# verworfen worden: neutral in Zeit, VRAM und Werten. Sie stehen deshalb auf der
# EP-Vorgabe. "DEFAULT" ist bewusst nicht vorgesehen — der EP mappt es auf den
# FALLBACK-Modus des cuDNN-Frontends und warnt selbst mit „extremely slow".
CUDNN_ALGO_SUCHE = "EXHAUSTIVE"
CUDNN_MAX_WORKSPACE = "1"
# --- .531 KARTENHAUSHALT ---------------------------------------------------
# Der Kartenspeicher dieses Prozesses haengt an EINER Env-Arena (`Cuda` +
# `CudaPinned`, registriert VOR der ersten Session); mit cuDNN 9 kommt auch der
# Conv-Workspace aus dieser Arena, die beiden cuDNN-Schalter darueber sind fuer
# Conv wirkungslos (ORT-Recherche Q5).
# Ohne sie hat ein Prozess MEHRERE CUDA-Arenen: eine je Session-EP plus eine
# modulglobale fuer die IO-Binding-Puffer (pybind_mlvalue.cc:215-231) — keine
# davon gedeckelt. Genau das fuellte am 15.09. die 12-GB-Karte in unter einer
# Minute.
GERAET_ID = 0                    # EINE Quelle fuer Provider-Option und Allokator
ARENA_STRATEGIEN = {"kNextPowerOfTwo": 0, "kSameAsRequested": 1}   # ORT-Q2
# kSameAsRequested (gemessen 15.09., Proben C1-C4): jede Erweiterung waechst nur
# um das Angeforderte statt auf die naechste Zweierpotenz. Zeitkosten des Deckels
# +1,5 % bei 3072 MiB, +5,1 % bei 2048 MiB.
ARENA_STRATEGIE_VORGABE = "kSameAsRequested"
_ENV_ARENA = {"registriert": False, "deckel_mb": 0, "strategie": None,
              "geraet": None, "pinned": False, "geprueft": False,
              "gemeldet": False, "fehler": None}
# Schalter + einmal gebaute RunOptions fuer die Arena-Schrumpfung (s. _shrink_ro).
_ARENA_SHRINK = {"an": False, "ro": None}
# --- .532 MEMORY-PATTERN ----------------------------------------------------
# Auf CUDA ist der Memory-Pattern-Planer seit .532 AUS (Vorgabe; wieder
# einschaltbar ueber `--mem-pattern 1` bzw. den Config-Schluessel
# `worker_mem_pattern`). Grund: onnxruntime 1.26.0 — die Fassung im Image —
# allokiert den Pattern-Block eines Laufs auf einem DummyStream und meldet ihn
# nie als frei zurueck; laufen Laeufe DERSELBEN Session aus mehreren
# Rechenstraengen, waechst die BFC-Arena dadurch stetig (onnxruntime issue
# 29351, behoben erst in 1.29.0; der dort genannte Umweg ist genau dieser
# Schalter). GEMESSEN 15.09. auf der RTX 2060 an 4K-Material des Feldtesters
# (bis 205 Gesichter je Bild, Rundordner shrink4k_20260915/ergebnis.md §4.7):
# zwei Straenge +24 statt +62 MiB je Durchgang bei gleicher Zeit, ein Strang
# 1568 statt 1762 MiB Plateau (-11 %) bei +4 % Zeit — Urteile in allen Laeufen
# wertgleich (30/30 Clips).
_MEM_PATTERN = {"an": False, "gemeldet": False}
_ENV_ARENA_SCHLOSS = threading.Lock()


def _melden(text):
    """Eine Zeile ins Prozess-Log (fd 2) — dorthin, wo auch der Dienst seine
    Aufbau-Zeilen schreibt. Kein Import von `worker_dienst`: der importiert diese
    Datei, und ein Ringimport waere hier ein Startfehler statt einer Logzeile."""
    try:
        os.write(2, (f"engine_cuda: {str(text).strip()}\n").encode())
    except Exception:                                    # noqa: BLE001
        pass


def arena_strategie_name():
    """Der Name der gerade geltenden Arena-Strategie — EINE Quelle fuer die
    Provider-Option (Zeichenkette) und die Arena-Cfg (Zahl)."""
    return _ENV_ARENA["strategie"] or ARENA_STRATEGIE_VORGABE


def env_arena_registrieren(deckel_mb, strategie=None):
    """EINMAL je Prozess die geteilte, gedeckelte Arena auf der ORT-Umgebung.

    -> True, wenn ein Deckel steht. Muss VOR der ersten InferenceSession laufen:
    die Ersetzung der Session-Allokatoren passiert bei der Session-
    Initialisierung (inference_session.cc:2383-2388), eine spaeter registrierte
    Arena erreicht eine schon gebaute Session nicht mehr.

    `deckel_mb <= 0` heisst AUSDRUECKLICH „kein Deckel" (Verhalten vor .531) und
    wird gemeldet, nicht verschwiegen. `arena_cfg` ist nie None — der CUDA-Zweig
    dereferenziert sie ohne Pruefung (environment.cc:424)."""
    mb = max(0, int(deckel_mb or 0))
    strat = str(strategie or ARENA_STRATEGIE_VORGABE)
    if strat not in ARENA_STRATEGIEN:
        raise SystemExit(f"unknown arena_extend_strategy {strat!r}, known: "
                         f"{sorted(ARENA_STRATEGIEN)}")
    with _ENV_ARENA_SCHLOSS:
        if _ENV_ARENA["registriert"]:
            return True
        if mb <= 0:
            if not _ENV_ARENA["gemeldet"]:
                _ENV_ARENA["gemeldet"] = True
                _melden("no VRAM cap — arena unbounded (pre-.531 behaviour)")
            return False
        try:
            cfg = ort.OrtArenaCfg(mb * 1024 * 1024, ARENA_STRATEGIEN[strat], -1, -1)
            mi = ort.OrtMemoryInfo("Cuda", ort.OrtAllocatorType.ORT_ARENA_ALLOCATOR,
                                   GERAET_ID, ort.OrtMemType.DEFAULT)
            ort.create_and_register_allocator_v2(EP, mi, {}, cfg)
        except Exception as e:                           # noqa: BLE001
            # LAUT, aber nicht toedlich: ohne Deckel laeuft der Prozess wie vor
            # .531 weiter. Ein Prozess, der gar nicht startet, analysiert nichts —
            # und /health zeigt `env_arena: false`, der Betreiber sieht es.
            _ENV_ARENA["fehler"] = f"{type(e).__name__}: {e}"
            _melden(f"ERROR: VRAM cap {mb} MiB could NOT be registered "
                    f"({_ENV_ARENA['fehler']}) — running WITHOUT a cap "
                    f"(pre-.531 behaviour)")
            return False
        _ENV_ARENA.update({"registriert": True, "deckel_mb": mb,
                           "strategie": strat, "geraet": GERAET_ID})
        _melden(f"VRAM cap {mb} MiB registered on device {GERAET_ID} "
                f"({strat}, pid {os.getpid()}) — one shared arena for all sessions")
        # PINNED (Host-Speicher, NICHT Karte): ohne diese zweite Registrierung
        # behaelt jede Session ihre eigene Pinned-Arena. Der Zweig haengt
        # ausschliesslich am NAMEN "CudaPinned" (allocator.cc:264-268).
        # `max_mem = 0` heisst ORT-Vorgabe, also das heutige Verhalten: gedeckelt
        # werden soll hier nichts, gemeinsam benutzt schon. Pinned zaehlt in
        # `worker_rss_max_mb`, nie ins Kartenbudget.
        try:
            p_mi = ort.OrtMemoryInfo("CudaPinned",
                                     ort.OrtAllocatorType.ORT_DEVICE_ALLOCATOR,
                                     GERAET_ID, ort.OrtMemType.CPU_OUTPUT)
            ort.create_and_register_allocator_v2(EP, p_mi, {},
                                                 ort.OrtArenaCfg(0, -1, -1, -1))
            _ENV_ARENA["pinned"] = True
        except Exception as e:                           # noqa: BLE001
            _melden(f"WARN: pinned arena not registered ({type(e).__name__}: {e}) "
                    f"— each session keeps its own host-memory arena; that is "
                    f"host RAM, not card memory, so the card cap still holds")
        return True
# Deckel der Buendelstufen, NUR hier im Prototyp. None = die Stufen von
# face_audit.Embedder.BATCH_STUFEN unveraendert; eine Zahl laesst alles darueber weg.
# face_audit bleibt in jedem Fall unberuehrt, es ist Prod-Kernmodul.
# 4 (uebernommen 12.09.): die 8er-Stufe von p faellt weg — 210 MiB weniger VRAM-Plateau
# und drei Sessions weniger, Werte bitgleich.
BUENDEL_DECKEL = 4
BUENDEL = tuple(n for n in face_audit.Embedder.BATCH_STUFEN
                if BUENDEL_DECKEL is None or n <= BUENDEL_DECKEL)
# v3c/v8: Stufen mit offener n-Achse. p fehlt bewusst (RTMPose verlor mit variabler Form
# Rechnungen an die CPU). fd ist dabei — seine Modell-Kette ist gebaut wie e/t/r; sein
# AUSSCHNITT-Graph ist die Ausnahme: er traegt zusaetzlich die Laplace-Leinwand und
# braucht dafuer eine BEKANNTE Gesichterzahl (FD_BREITE).
DYN_STUFEN = (wk.FD, "e", "t", "r")
# v5/v8: welche Modell-Ketten prozessweit EINMAL gebaut werden statt je Geometrie.
GETEILTE_STUFEN = (wk.FD, "e", "t", "p", "r")
# v8: die Breite der fd-Stufe (immer eine Zahl, s. graph_crop_fd).
FD_BREITE = wk.AUFRUF_BREITE or 2
# v7: womit die dynamischen Ketten WIRKLICH gewaermt werden. Steht eine feste
# Aufrufbreite, gibt es genau eine Form — jede weitere zu waermen hiesse, Arena-Bloecke
# fuer eine Breite zu belegen, die im Lauf nicht mehr vorkommen KANN.
WARM_N = (1, 2)
WARM_DYN = WARM_N if wk.AUFRUF_BREITE is None else (wk.AUFRUF_BREITE,)
# v6: Rechentyp der NV12->RGB-Kette. True = die ganze Kette in fp16, der Ausgang 'rgb'
# per Cast wieder fp32 (GridSample gibt es auf dem CUDA-EP nur in fp32 — Op-Probe
# 12.09.). Es ist der EINE Schalter, der nicht aus einer Modell-Datei folgen kann:
# fuer die Farbumrechnung gibt es kein ONNX.
PIXEL_FP16 = True
# Die Namen der beiden Zahlen-Ausgaenge des fd-Ausschnitt-Graphen.
NAME_SL, NAME_SL2 = "s_lap", "s_lap2"
# NV12 -> RGB wie die OpenVINO-Operation der Intel-Version (Probe 11.09.2026):
#   R = 1,164 (Y-16)               + 1,596 (V-128)
#   G = 1,164 (Y-16) - 0,391 (U-128) - 0,813 (V-128)
#   B = 1,164 (Y-16) + 2,018 (U-128)
FARBE = np.array([[1.164, 0.0, 1.596], [1.164, -0.391, -0.813], [1.164, 2.018, 0.0]],
                 np.float32)
U8, F32, F16 = TensorProto.UINT8, TensorProto.FLOAT, TensorProto.FLOAT16

# Die Modell-Schalter (v6/v8) an EINER Stelle, damit Huellen und Engine nicht
# auseinanderlaufen. Jeder erwartet die offline konvertierte fp16-Fassung; der
# Rechentyp der Stufe folgt dann der DATEI, nicht einem Schalter.
MODELL_SCHALTER = (("r", "--rec-onnx", "rec_onnx",
                    "Erkennungs-ONNX (adaface) statt des Modell-Vertrags"),
                   ("e", "--fiqa-onnx", "fiqa_onnx",
                    "Guete-ONNX e (fiqa_edgenext) statt core/guete.PFAD_E"),
                   ("t", "--ediffiqa-onnx", "ediffiqa_onnx",
                    "Guete-ONNX t (ediffiqa) statt core/guete.PFAD_T"),
                   ("p", "--pose-onnx", "pose_onnx",
                    "RTMPose-ONNX statt pose_wache.MODELL_STD[0]"),
                   # v8: ACHTUNG BEIM KONVERTIEREN, gemessen 13.09.: die Vorgabe
                   # max_finite_val=1e4 des Werkzeugs klemmt den Initializer
                   # bn2_moving_var (244 von 256 Werten > 1e4, max 52808,9) und verschiebt
                   # front dadurch um bis zu 0,47 — eine fp16-Datei MUSS mit
                   # max_finite_val 65504 entstehen.
                   (wk.FD, "--lm-onnx", "lm_onnx",
                    "1k3d68-ONNX (Landmarks -> front) statt des Modell-Vertrags"))

# ------------------------------------------------- fp16-Artefakte AUS DEM IMAGE (E3.5)
# Bis zum E3-Schnitt kamen die fp16-Fassungen von aussen: die Messreihen reichten sie
# per --det-onnx/--rec-onnx/… herein, die Dateien lagen AUSSERHALB des Repos. Fuer ein
# Produkt-Image ist das kein Weg (Hausregel „self-contained": Modelle ins Image backen,
# nichts zur Laufzeit nachladen). Seit E3.5 erzeugt der cuda-Bau sie selbst
# (tools/fp16_backen.py) und legt sie mit einem MANIFEST hier ab.
#
# Das Manifest ist die EINE Liste — Stufe -> Datei + md5 + Werkzeug-Versionen. Diese
# Engine liest daraus ihre Vorgaben und PRUEFT vor dem Laden die md5 der AUSGELIEFERTEN
# Datei gegen das Manifest. Ein CLI-Schalter gewinnt weiterhin (Messbetrieb); was der
# Schalter nicht nennt, kommt aus dem Manifest; fehlt das Manifest, bleibt es bei der
# fp32-Vorgabe des Hauses — LAUT im Bericht, nie still.
FP16_ORDNER = os.path.join(wk.WURZEL, "models", "fp16")
FP16_MANIFEST = "manifest.json"


def _md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fp16_bestand(ordner=None):
    """Die gebackenen fp16-Dateien. -> ({stufe: pfad}, bericht)

    `bericht` ist das, was in die Job-Antwort/Rechenprobe geht: Zustand, Werkzeug-
    Versionen und je Stufe Datei + md5 + ob die md5 stimmt. Eine Datei mit falscher
    md5 wird NICHT benutzt (und der Bericht sagt warum) — die Alternative waere, mit
    einem Modell zu rechnen, von dem niemand mehr weiss, wie es entstanden ist."""
    ordner = ordner or FP16_ORDNER
    pfad = os.path.join(ordner, FP16_MANIFEST)
    if not os.path.exists(pfad):
        return {}, {"stand": "kein Manifest", "ordner": ordner}
    try:
        with open(pfad, encoding="utf-8") as f:
            man = json.load(f)
    except Exception as e:                                 # noqa: BLE001
        return {}, {"stand": f"Manifest unlesbar: {type(e).__name__}: {e}", "ordner": ordner}
    pfade, dateien = {}, {}
    for stufe, e in sorted((man.get("modelle") or {}).items()):
        p = os.path.join(ordner, e.get("datei") or "")
        eintrag = {"datei": e.get("datei"), "md5_soll": e.get("md5"),
                   "max_finite_val": e.get("max_finite_val"),
                   "zusaetzlich_gesperrt": e.get("zusaetzlich_gesperrt")}
        if not os.path.exists(p):
            eintrag["stand"] = "fehlt"
        else:
            ist = _md5(p)
            eintrag["md5_ist"] = ist
            if ist != e.get("md5"):
                eintrag["stand"] = "md5 weicht ab — NICHT benutzt"
            else:
                eintrag["stand"] = "ok"
                pfade[stufe] = p
        dateien[stufe] = eintrag
    schlecht = [k for k, v in dateien.items() if v["stand"] != "ok"]
    return pfade, {"stand": "ok" if not schlecht else f"unvollstaendig: {', '.join(schlecht)}",
                   "ordner": ordner, "werkzeug": man.get("werkzeug"), "dateien": dateien}


# ------------------------------------------------------------------ Decode
def _ffmpeg_nv12(clip, schritt, hw):
    """Die ffmpeg-Kette dieser Engine, EINMAL fuer beide Wege. Auswahl vor dem Download
    wie decode.FrameIter (decode.py:159-177), aber NV12 statt yuv420p und ohne
    cv2-Umrechnung. `hw=False` ist dieselbe Kette OHNE NVDEC und ohne hwdownload — der
    Software-Rueckfall; sie endet auf demselben `format=nv12`."""
    # .536 B1a: `-nostdin` — ffmpeg darf den fd 0 seines Elternprozesses nicht
    # pollen. Im Worker ist das die Job-Pipe (s. worker_kern.nv12_strom, dort
    # steht der Byte-Beweis). Aendert nichts am Decoder und nichts an den Pixeln.
    basis = ["ffmpeg", "-nostdin", "-v", "warning"]
    if hw:
        basis += ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
    rest = "hwdownload,format=nv12" if hw else "format=nv12"
    return basis + ["-i", clip, "-map", "0:v:0",
                    "-vf", f"select='not(mod(n\\,{schritt}))',{rest}",
                    "-fps_mode", "passthrough", "-f", "rawvideo", "-"]


def frames_nv12(clip, W, H, schritt, wache=None):
    """Sample-Frames als (i, y, uv) ueber NVDEC, MIT LAUTEM SOFTWARE-RUECKFALL (E2d).
    Regel und Begruendung stehen EINMAL in worker_kern.nv12_mit_rueckfall; der Byte-Weg
    dahinter ist worker_kern.nv12_strom. Der NVDEC-Byte-Beweis vom 12.09. deckt die
    HW-Kette; der Nachweis, dass die SW-Kette hier dieselben NV12-Bytes liefert, steht
    fuer die CUDA-Seite noch aus (auf dem NB zu messen, wie fuer VAAPI in E2d gemessen) —
    diese Fassung ist strukturell gleich, nicht gemessen.
    `wache` (E2): dict fuer Kette/rc/decoder_fehler, dazu hwdec_fallback/hwdec_grund."""
    return wk.nv12_mit_rueckfall(_ffmpeg_nv12(clip, schritt, True),
                                 _ffmpeg_nv12(clip, schritt, False),
                                 W, H, schritt, "NVDEC", wache=wache)


# ------------------------------------------------------------------ Modelle vorbereiten
def _eingang(m):
    inits = {i.name for i in m.graph.initializer}
    return [i for i in m.graph.input if i.name not in inits][0]


def _typ(m):
    """Rechentyp des Modell-EINGANGS (F16 oder F32) eines geladenen Modells. Der Typ
    wird immer aus der Datei GELESEN, die auch geladen wird — einen Schalter, der
    danebenlaufen kann, gibt es fuer die Modelle bewusst nicht (Prinzip aus v3b)."""
    return _eingang(m).type.tensor_type.elem_type


def _typ_datei(pfad):
    """_typ fuer eine Datei, ohne sie zu behalten."""
    return _typ(onnx.load(pfad, load_external_data=False))


def _typ_name(t):
    """Der Typ als Wort fuer die Kopfzeile."""
    return "fp16" if t == F16 else "fp32"


def _np_typ(t):
    return np.float16 if t == F16 else np.float32


def _batch_frei(m):
    """Reshape-Ziele mit fest eingebauter Batch 1 auf 0 stellen (ONNX-Reshape mit
    allowzero=0: 0 = Groesse vom Eingang). fiqa_edgenext braucht das fuer mehrere
    Gesichter je Aufruf. Jeder Reshape bekommt eine EIGENE Kopie der Konstante: im
    ONNX-Original teilen sich Reshape und Expand dieselbe Konstante, eine Aenderung an
    Ort und Stelle verbog das Expand (Bau scheiterte ab zwei Gesichtern, 11.09.).
    -> Anzahl umgestellt"""
    inits = {i.name: i for i in m.graph.initializer}
    consts = {n.output[0]: n for n in m.graph.node if n.op_type == "Constant"}
    n_um = 0
    for node in m.graph.node:
        if node.op_type != "Reshape" or len(node.input) < 2:
            continue
        if any(a.name == "allowzero" and a.i == 1 for a in node.attribute):
            continue
        name = node.input[1]
        if name in inits:
            quelle = inits[name]
        elif name in consts:
            quelle = next(a for a in consts[name].attribute if a.name == "value").t
        else:
            continue
        v = numpy_helper.to_array(quelle).astype(np.int64).copy()
        if v.size and v[0] == 1:
            v[0] = 0
            neu = f"{name}__batch_frei_{n_um}"
            m.graph.initializer.append(numpy_helper.from_array(v, neu))
            node.input[1] = neu
            n_um += 1
    return n_um


def _div_naht(m):
    """Der EINE Div-Knoten, der einen Graph-Ausgang speist — oder None.

    Wortgleich die Naht, die `face_audit.NormMass._graph_bytes` sucht: der adaface-Kopf
    endet auf `f -> ReduceL2 -> Div`, also ist input[0] dieses Knotens f und input[1]
    sein Betrag ||f||. Genau dieser Betrag ist die Feature-Norm auf der Skala 15-30, auf
    der die Latten des Hauses geeicht sind. Ist die Naht nicht eindeutig (fremder Kopf,
    mehrere Div-Ausgaenge), gibt es sie fuer uns nicht — dann bleibt es beim selbst
    gerechneten Betrag, und der ist bei einem UNNORMIERTEN Kopf der richtige Wert."""
    aus = {o.name for o in m.graph.output}
    div = [nd for nd in m.graph.node
           if nd.op_type == "Div" and nd.output and nd.output[0] in aus]
    return div[0] if len(div) == 1 else None


def _fest(pfad, form, batch_frei=False, norm_aus=False):
    """Modell mit fester Eingangsform -> bytes. Fest, damit ORT die Form-Rechnungen
    beim Bau vorausrechnet und nichts auf die CPU legen muss.

    v3c: None an einer Stelle von `form` laesst diese Achse OFFEN (dim_param 'n'). Damit
    baut dieselbe Funktion die festen Ketten (Stufe p, Detektor) und die dynamischen
    (fd, e, t, r). Die CPU-Wache in _sitzung bleibt scharf; scheitert eine Session daran,
    ist das der Befund.

    norm_aus (E2c): den Divisor des Erkennungs-Kopfs zusaetzlich als Ausgang `f_norm`
    herausfuehren (s. `_div_naht`). Der Cast nach fp32 ist Absicht und keine Formsache —
    bei einem fp16-adaface waere die Norm sonst fp16, und `graph_rec_post` erwartet
    fp32 (dieselbe Linie wie der fp16-Schutz dort: Reduktionen rechnen fp32)."""
    m = onnx.load(pfad)
    if batch_frei:
        _batch_frei(m)
    if norm_aus:
        div = _div_naht(m)
        if div is not None:
            m.graph.node.append(onnx.helper.make_node(
                "Cast", [div.input[1]], ["f_norm"], name="f_norm_naht",
                to=onnx.TensorProto.FLOAT))
            m.graph.output.append(onnx.helper.make_tensor_value_info(
                "f_norm", onnx.TensorProto.FLOAT, None))
    for d, v in zip(_eingang(m).type.tensor_type.shape.dim, form):
        if v is None:
            d.ClearField("dim_value")
            d.dim_param = "n"
            continue
        d.ClearField("dim_param")
        d.dim_value = int(v)
    del m.graph.value_info[:]
    for o in m.graph.output:                        # Ausgangsformen haengen an der Eingangsform
        o.type.tensor_type.ClearField("shape")
    return m.SerializeToString()


def cuda_optionen():
    """Die CUDA-Provider-Optionen JEDER Session, an einer Stelle.
    kSameAsRequested: jede Session-Arena waechst nur um das Angeforderte statt auf die
    naechste Zweierpotenz; reine Zuteilungsregel, keine Wirkung auf die Werte.
    Neues dict je Aufruf: was ORT damit macht, ist nicht zugesagt.
    .531: Geraet und Strategie stehen je genau EINMAL (GERAET_ID bzw.
    `arena_strategie_name()`) — sonst koennte die Env-Arena auf Geraet 0 stehen,
    waehrend die Sessions Geraet 1 binden, und der Deckel waere still wirkungslos."""
    return {"device_id": GERAET_ID,
            "arena_extend_strategy": arena_strategie_name(),
            "cudnn_conv_algo_search": CUDNN_ALGO_SUCHE,
            "cudnn_conv_use_max_workspace": CUDNN_MAX_WORKSPACE}


def _sitzung(modell_bytes):
    """Session nur auf CUDA, CPU-Rueckfall abgeschaltet: legt ORT einen Knoten auf die
    CPU, scheitert der Bau laut."""
    so = face_audit._ort_thread_opts()              # feste Threadzahl: sonst Affinitaets-Fehler
    so.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    # .532: MEMORY-PATTERN AUS ist hier die Vorgabe (s. Modulkopf, Messung vom
    # 15.09.). Gemeldet wird EINMAL je Prozess, beim ersten Session-Bau — ein
    # Schalter, der die Kartenbelegung aendert, darf nicht unsichtbar sein.
    if not _MEM_PATTERN["an"]:
        so.enable_mem_pattern = False
        if not _MEM_PATTERN["gemeldet"]:
            _MEM_PATTERN["gemeldet"] = True
            _melden(f"mem-pattern: off (pid {os.getpid()})")
    # .531: nur wenn die Env-Arena wirklich steht. Ohne Registrierung waere der
    # Schluessel eine Zusage ohne Deckung.
    if _ENV_ARENA["registriert"]:
        so.add_session_config_entry("session.use_env_allocators", "1")
    # sess_options AUSDRUECKLICH benannt (E3.5): die ORT-Kappungs-Wache in S1
    # (tools/qs.sh) erkennt die Thread-Kappung nur am Schluesselwort. Wertgleich
    # zum Positions-Argument, das hier bis zum R1-Umzug stand — mit dem Umzug in
    # die Wurzel ist diese Datei Auslieferungscode und faellt unter die Wache.
    s = ort.InferenceSession(modell_bytes, sess_options=so,
                             providers=[(EP, cuda_optionen())])
    if EP not in s.get_providers():
        raise SystemExit("CUDA-Provider bindet nicht, kein Rueckfall")
    # .531 GERAETE-WACHE, genau einmal je Prozess: registriert ist die Arena fuer
    # EIN Geraet. Binden die Sessions ein anderes, greift der Deckel still nicht —
    # und „still nicht" ist die Klasse von Fehler, die den 15.09. gekostet hat.
    if _ENV_ARENA["registriert"] and not _ENV_ARENA["geprueft"]:
        try:
            _dev = int((s.get_provider_options().get(EP) or {})
                       .get("device_id", GERAET_ID))
        except (TypeError, ValueError):
            _dev = GERAET_ID
        if _dev != _ENV_ARENA["geraet"]:
            raise SystemExit(f"VRAM cap registered for device "
                             f"{_ENV_ARENA['geraet']}, sessions bind device "
                             f"{_dev} — the cap would be silently inactive")
        _ENV_ARENA["geprueft"] = True
    return s


# ------------------------------------------------------------------ Vorverarbeitungs-Graphen
class _Bau:
    """Kleiner ONNX-Graph-Bauer (opset 16)."""

    def __init__(self):
        self.knoten, self.inits, self.n = [], [], 0

    def c(self, wert, dtype=np.float32):
        self.n += 1
        name = f"c{self.n}"
        self.inits.append(numpy_helper.from_array(np.asarray(wert, dtype), name))
        return name

    def op(self, typ, ein, **attr):
        self.n += 1
        aus = f"t{self.n}"
        self.knoten.append(helper.make_node(typ, ein, [aus], **attr))
        return aus

    def raus(self, name, t):
        self.knoten.append(helper.make_node("Identity", [t], [name]))

    def modell(self, ein, aus):
        g = helper.make_graph(self.knoten, "vorverarbeitung",
                              [helper.make_tensor_value_info(*e) for e in ein],
                              [helper.make_tensor_value_info(*a) for a in aus],
                              initializer=self.inits)
        return helper.make_model(g, opset_imports=[helper.make_opsetid("", OPSET)]).SerializeToString()


def _rgb(b, H, W, typ=F32):
    """y [1,H,W,1] + uv [1,H/2,W/2,2] (uint8) -> RGB [1,3,H,W] float wie OV nv12_to_rgb.

    typ (v6): der Rechentyp der GANZEN Kette. In fp16 wechselt nur der Typ, nicht die
    Knotenfolge — dieselben Operationen auf denselben Bytes, halbe Mantisse. Die
    Resize-Skalen bleiben in jedem Fall float32: ONNX schreibt fuer 'scales'
    tensor(float) vor, unabhaengig vom Typ des Bildes."""
    np_typ = _np_typ(typ)
    y = b.op("Reshape", [b.op("Cast", ["y"], to=typ), b.c([1, 1, H, W], np.int64)])
    uv = b.op("Transpose", [b.op("Cast", ["uv"], to=typ)], perm=[0, 3, 1, 2])
    uv = b.op("Resize", [uv, "", b.c([1, 1, 2, 2])], mode="nearest",   # je 2x2-Block
              coordinate_transformation_mode="asymmetric", nearest_mode="floor")
    yuv = b.op("Sub", [b.op("Concat", [y, uv], axis=1),
                       b.c(np.array([16, 128, 128]).reshape(1, 3, 1, 1), np_typ)])
    rgb = b.op("Conv", [yuv, b.c(FARBE.reshape(3, 3, 1, 1), np_typ)])  # 1x1: Farbmatrix
    return b.op("Round", [b.op("Clip", [rgb, b.c(0.0, np_typ), b.c(255.0, np_typ)])])


def graph_pre_det(H, W, det_wh, neu_wh, pixel_typ=F32, det_typ=F32):
    """Vorverarbeitung A mit ZWEI Ausgaengen (v3a): NV12 -> RGB-Vollbild, daraus
      det_in  verkleinern -> Leinwand -> normieren, der Detektor-Eingang,
      rgb     das RGB-Vollbild [1,3,H,W] selbst, fuer die Ausschnitt-Stufen.
    Die Rechenreihenfolge bleibt: erst NV12 -> RGB in voller Aufloesung, dann Resize.

    pixel_typ (v6): der Rechentyp der Vollbild-Kette. In fp16 rechnet die ganze
    NV12->RGB-Umrechnung mit halber Mantisse; der AUSGANG 'rgb' wird danach per Cast
    wieder fp32, weil GridSample auf dem CUDA-EP nur fp32 kennt. Der Cast steht genau
    hier, also einmal je Frame, statt in jeder der sechs Ausschnitt-Sessions.
    det_typ (v3b/v6): der DETEKTOR-ZWEIG rechnet in dem Typ, den das Detektor-ONNX
    erwartet. Stimmt er mit pixel_typ ueberein, entfaellt jeder Cast."""
    (det_w, det_h), (neu_w, neu_h) = det_wh, neu_wh
    b = _Bau()
    rgb = _rgb(b, H, W, pixel_typ)
    # ab hier der Detektor-Zweig; wechselt nur der Rechentyp, nicht die Folge
    np_typ = _np_typ(det_typ)
    zweig = rgb if det_typ == pixel_typ else b.op("Cast", [rgb], to=det_typ)
    r = b.op("Resize", [zweig, "", "", b.c([1, 3, neu_h, neu_w], np.int64)],
             mode="linear", coordinate_transformation_mode="half_pixel")
    p = b.op("Pad", [r, b.c([0, 0, 0, 0, 0, 0, det_h - neu_h, det_w - neu_w], np.int64),
                     b.c(0.0, np_typ)], mode="constant")
    b.raus("det_in", b.op("Div", [b.op("Sub", [p, b.c(wk.DET_MEAN, np_typ)]),
                                  b.c(wk.DET_STD, np_typ)]))
    # zuletzt angehaengt, damit der Detektor-Zweig Knoten fuer Knoten der v2-Fassung
    # entspricht und ORT ihn gleich sieht
    b.raus("rgb", rgb if pixel_typ == F32 else b.op("Cast", [rgb], to=F32))
    return b.modell([("y", U8, [1, H, W, 1]), ("uv", U8, [1, H // 2, W // 2, 2])],
                    [("det_in", det_typ, [1, 3, det_h, det_w]),
                     ("rgb", F32, [1, 3, H, W])])


def _raster(h, w):
    """Abtastpunkte (u, v, 1) eines h x w Ausschnitts in Ausschnitt-Pixeln."""
    vv, uu = np.mgrid[0:h, 0:w].astype(np.float32)
    return np.stack([uu.ravel(), vv.ravel(), np.ones(h * w, np.float32)], axis=1)[None]


def _u8_rundung(b, s):
    """Den fertig getasteten Ausschnitt auf GANZE Graustufen zurueckholen, bevor die
    Stufen-Normierung ihn anfasst (f32-Warp-Fix, 14.09.2026).

    Wortgleich zu `engine_ov._u8_rundung`, dort steht die gemessene Begruendung
    (runs/zerlegung_klein_20260914/): der alte Weg schneidet mit cv2.warpAffine auf
    dem uint8-Frame und ist damit per Konstruktion ganzzahlig; der GPU-Warp gibt
    Zwischenwerte heraus. An den Heilwegen abgelesen halbiert die Rundung den Rest
    gegen die CPU-fp32-Referenz (F2 0,0031 -> F2c 0,0015 Score-Punkte).

    floor(x + 0,5) und nicht ONNX-`Round`: `Round` rundet kaufmaennisch-gerade,
    OpenCV rundet in seinem Festkomma-Pfad die halbe Einheit nach oben (CV_DESCALE,
    dieselbe Zeile wie in `_grau`) — und beide Engines sollen HIER dieselbe Regel
    haben, sonst waere der Backend-Vergleich um eine Rundungsart verschoben.

    WARUM HIER NUR DIE RUNDUNG UND KEIN PRAEZISIONS-SCHALTER: auf dieser Seite ist
    der Warp bereits f32, und zwar nicht als Hinweis, sondern per Typ-Deklaration —
    'rgb' verlaesst die Vorverarbeitung seit v6 als F32 (GridSample gibt es auf dem
    CUDA-EP nur in fp32), 'th' ist als F32 deklariert, das Abtast-Raster ist eine
    float32-Konstante, und damit rechnen MatMul, GridSample und die Normierung in
    float32. Erst danach steht der eine Cast auf den Typ, den das MODELL der Stufe
    erwartet. Es gibt an dieser Achse also nichts zu heben. -> der Ausschnitt, ganzzahlig
    """
    return b.op("Floor", [b.op("Add", [s, b.c(0.5)])])


def _norm_bauer(vorschrift):
    """Die Normierung EINER Stufe als ONNX-Knoten, aus der Vorschrift des Kerns
    (worker_kern.norm_vorschriften/norm_schritte). Bis E1 stand sie als _norm_e/_norm_t/
    _norm_p/_norm_r/_norm_lm fuenfmal hier und noch einmal in der OpenVINO-Fassung; die
    KNOTENFOLGE ist unveraendert — /255, Kanalfolge, -mean, /std, und ein Posten entsteht
    nur, wenn die Vorschrift ihn verlangt. Ein Skalar bleibt ein Skalar, ein 3er-Feld ein
    [1,3,1,1]-Block (genau wie zuvor, damit die Graphen dieselben bleiben)."""
    schritte = wk.norm_schritte(vorschrift)

    def konst(b, wert):
        a = np.asarray(wert, np.float32)
        return b.c(a.reshape(1, 3, 1, 1)) if a.size == 3 else b.c(float(a))

    def norm(b, s):
        for art, wert in schritte:
            if art == "bgr":
                s = b.op("Gather", [s, b.c([2, 1, 0], np.int64)], axis=1)
            elif art == "sub":
                s = b.op("Sub", [s, konst(b, wert)])
            else:
                s = b.op("Div", [s, konst(b, wert)])
        return s
    return norm


def graph_crop(H, W, n, seite, norm, aus_typ=F32):
    """Ausschnitt einer Stufe fuer n Gesichter: aus dem RGB-Frame n Ausschnitte h x w
    per EINEM GridSample (Gesichter im Gitter uebereinander), dann normieren.

    n = None (v3c): die Gesichter-Achse bleibt offen; die beiden Reshape-Ziele nennen sie
    als -1. Es ist dieselbe Knotenfolge, nur die beiden Konstanten unterscheiden sich.

    Ausschneiden und Normieren bleiben in JEDEM Fall fp32 (v6): 'rgb' und das Gitter sind
    fp32, weil der CUDA-EP GridSample nur so kennt. aus_typ ist der Typ, den das MODELL
    der Stufe erwartet — passt er nicht, steht hier der eine Cast zu ihm hin.

    f32-WARP-FIX (14.09.2026): dazwischen steht jetzt die uint8-Rundung (`_u8_rundung`).
    Die Praezisions-Haelfte des Fixes betrifft diese Engine nicht — sie rechnet den Warp
    schon in f32, nachgeprueft an den Typen (Raster-Konstante float32, 'th' F32, 'rgb'
    F32); auf der Intel-Seite war genau das der Fehler und musste per Hinweis geholt
    werden. Der Cast auf den Modell-Typ bleibt, wo er war: hinter der Normierung."""
    h, w = seite
    achse = "n" if n is None else n
    b = _Bau()
    g = b.op("MatMul", [b.c(_raster(h, w)), b.op("Transpose", ["th"], perm=[0, 2, 1])])
    g = b.op("Reshape", [g, b.c([1, -1 if n is None else n * h, w, 2], np.int64)])
    s = b.op("GridSample", ["rgb", g], mode="bilinear", padding_mode="zeros", align_corners=0)
    s = b.op("Transpose", [b.op("Reshape", [s, b.c([3, -1 if n is None else n, h, w],
                                                   np.int64)])], perm=[1, 0, 2, 3])
    c = norm(b, _u8_rundung(b, s))
    b.raus("crop", c if aus_typ == F32 else b.op("Cast", [c], to=aus_typ))
    return b.modell([("rgb", F32, [1, 3, H, W]), ("th", F32, [achse, 2, 3])],
                    [("crop", aus_typ, [achse, 3, h, w])])


def _grau(b, s):
    """RGB [n,3,h,w] -> Graustufen [n,1,h,w] im OpenCV-Festkomma, mit derselben Rundung
    wie cv2.cvtColor(BGR2GRAY) (CV_DESCALE: +halbe Einheit, dann abschneiden)."""
    w = np.asarray(wk.GRAU_W, np.float32) / float(1 << wk.GRAU_SHIFT)
    g = b.op("ReduceSum", [b.op("Mul", [s, b.c(w.reshape(1, 3, 1, 1))]),
                           b.c([1], np.int64)], keepdims=1)
    return b.op("Floor", [b.op("Add", [g, b.c(0.5)])])


def _lap_summen(b, s, n, C):
    """Laplace ueber die Leinwand und daraus Summe und Summe der Quadrate ueber die
    gueltige Region. Der 3x3-Kern ohne Polster liefert [n,1,C-2,C-2]; Ausgabezeile i ist
    Leinwand-Zeile i+1, und genau dort liegt die erste Crop-Zeile (der Spiegelring sitzt
    auf Leinwand-Zeile 0). Die Region wird deshalb mit einem Praefix-Masken-Produkt
    gewaehlt: mu [n,C-2,1] Zeilen, mv [n,1,C-2] Spalten. -> (s_lap [n], s_lap2 [n])"""
    k = np.asarray(wk.LAPLACE_KERN, np.float32).reshape(1, 1, 3, 3)
    lap = b.op("Conv", [_grau(b, s), b.c(k)])                  # [n,1,C-2,C-2], pads 0
    lap = b.op("Reshape", [lap, b.c([n, C - 2, C - 2], np.int64)])
    maske = b.op("Mul", ["mu", "mv"])                          # [n,C-2,C-2]
    sl = b.op("ReduceSum", [b.op("Mul", [lap, maske]), b.c([1, 2], np.int64)], keepdims=0)
    sl2 = b.op("ReduceSum", [b.op("Mul", [b.op("Mul", [lap, lap]), maske]),
                             b.c([1, 2], np.int64)], keepdims=0)
    return sl, sl2


def graph_crop_fd(H, W, n, seite, norm, aus_typ=F32, C=None):
    """Ausschnitt-Graph der fd-Stufe (v8) — EIN Aufruf, zwei Zuschnitte aus demselben
    RGB-Vollbild:
      'crop'            der Landmark-Ausschnitt [n,3,192,192] fuer 1k3d68
      's_lap'/'s_lap2'  die Laplace-Summen des ENGEN Crops auf einer Leinwand CxC in
                        NATIVER Pixelskala
    Die Leinwand wird per GATHER gezogen (Spalten mit jx, dann Zeilen mit iy) statt
    getastet: damit sind die Indizes ein EINGANG, und der Spiegel von BORDER_REFLECT_101
    steckt in ihnen (worker_kern.leinwand_zug).

    f32 IST HIER KEIN SCHALTER, sondern schon da: 'rgb' erreicht die Ausschnitt-Sessions
    seit v6 als fp32 (GridSample-Zwang), und der Laplace-Zweig haengt direkt an diesem
    fp32-Eingang. Das ist Pflicht: L^2 laeuft bis rund 1e6 und liegt ausserhalb von fp16.

    f32-WARP-FIX (14.09.2026): der Landmark-Ausschnitt bekommt die uint8-Rundung wie die
    uebrigen Stufen (`_u8_rundung`) — die fd-Rechnung tastet aus DEMSELBEN Warp, ihre
    Eingangs-Bytes sollen dieselbe Quantisierung haben. Die Laplace-Leinwand daneben
    bleibt unberuehrt: sie wird GEZOGEN (Gather), nicht getastet, und ist ohnehin
    ganzzahlig.

    n ist eine ZAHL, keine offene Achse: die Leinwand braucht je Gesicht ein eigenes
    Gather-Paar, und n solche Paare lassen sich nur bei bekanntem n bauen."""
    C = wk.LEINWAND if C is None else C
    h, w = seite
    b = _Bau()
    g = b.op("MatMul", [b.c(_raster(h, w)), b.op("Transpose", ["th"], perm=[0, 2, 1])])
    g = b.op("Reshape", [g, b.c([1, n * h, w, 2], np.int64)])
    s = b.op("GridSample", ["rgb", g], mode="bilinear", padding_mode="zeros", align_corners=0)
    s = b.op("Transpose", [b.op("Reshape", [s, b.c([3, n, h, w], np.int64)])],
             perm=[1, 0, 2, 3])
    c = norm(b, _u8_rundung(b, s))
    b.raus("crop", c if aus_typ == F32 else b.op("Cast", [c], to=aus_typ))
    teile = []
    for k in range(n):                                   # n ist die feste Aufrufbreite
        jk = b.op("Squeeze", [b.op("Slice", ["jx", b.c([k], np.int64), b.c([k + 1], np.int64),
                                             b.c([0], np.int64)]), b.c([0], np.int64)])
        ik = b.op("Squeeze", [b.op("Slice", ["iy", b.c([k], np.int64), b.c([k + 1], np.int64),
                                             b.c([0], np.int64)]), b.c([0], np.int64)])
        sp = b.op("Gather", ["rgb", jk], axis=3)         # [1,3,H,C]  Spalten zuerst:
        teile.append(b.op("Gather", [sp, ik], axis=2))   # [1,3,C,C]  weniger Zwischenwerte
    lein = b.op("Concat", teile, axis=0) if n > 1 else teile[0]
    sl, sl2 = _lap_summen(b, lein, n, C)
    b.raus(NAME_SL, sl)
    b.raus(NAME_SL2, sl2)
    return b.modell([("rgb", F32, [1, 3, H, W]), ("th", F32, [n, 2, 3]),
                     ("jx", TensorProto.INT32, [n, C]), ("iy", TensorProto.INT32, [n, C]),
                     ("mu", F32, [n, C - 2, 1]), ("mv", F32, [n, 1, C - 2])],
                    [("crop", aus_typ, [n, 3, h, w]), (NAME_SL, F32, [n]),
                     (NAME_SL2, F32, [n])])


def graph_rec_post(n, dim, emb_typ=F32, norm_eingang=False):
    """Embedding [n, D] -> L2-normiert wie face_audit._rec_infer, dazu die Feature-Norm.
    Zur CPU kommen [n, D] und [n].

    E1 (Konzept §1c): MatMul, Reshape und ReduceMax gegen die Referenz-Matrix sind RAUS.
    Bis v8 lag hier die gesamte Erkennungs-Matrix als Graph-Konstante — jede
    Referenz-Aenderung haette ein Rekompilat und einen Prozess-Neustart verlangt. Den
    Score und das Maximum je Person rechnet jetzt worker_kern.scores_rechnen auf der CPU.
    Die AUSGANGSREIHENFOLGE (emb_n, norm) ist dieselbe wie in engine_ov.modell_r, damit
    der Kern w[0]/w[1] in beiden Engines gleich liest.

    emb_typ (v6): kommt das Embedding aus einem fp16-adaface, wird es als ERSTE Handlung
    auf fp32 gehoben; alles dahinter rechnet unveraendert fp32. Bewusst konservativ:
    L2-Betrag ist eine Reduktion ueber 512 Dimensionen, und Reduktionen sind der
    fp16-Risikofall. Der Graph kostet weder Zeit noch Speicher, der Schutz ist gratis.

    norm_eingang (E2c, 13.09.2026 — dieselbe Korrektur wie engine_ov.modell_r): woher die
    FEATURE-NORM kommt. `emb` ist der Graph-AUSGANG des adaface-Kopfs, und der endet selbst
    auf `f -> ReduceL2 -> Div` — sein Betrag ist per Konstruktion 1 (auf Intel gemessen:
    1,0003 statt der Skala 15-30, auf der die Latten 20/22/23,5/24 geeicht sind). Traegt die
    Erkennungs-Session deshalb den Divisor als Zusatz-Ausgang `f_norm` (`_fest(norm_aus=
    True)`, dieselbe Naht wie face_audit.NormMass._graph_bytes), wird ER durchgereicht;
    sonst bleibt es beim selbst gerechneten Betrag — bei einem unnormierten Kopf IST der
    die Feature-Norm. AUSGANG 0 bleibt in beiden Faellen `emb/||emb||`: face_audit liefert
    als `normed_embedding` genau diese zweite Teilung, und weil `emb` nicht exakt Laenge 1
    hat, ist sie kein Nulleffekt.

    NICHT AUF CUDA-HARDWARE NACHGEMESSEN (E2c lief auf Intel). Die ONNX-Naht selbst ist
    geprueft (tools-loser Strukturtest am selben adaface-File); die CUDA-Laufzeit steht aus."""
    b = _Bau()
    achse = "n" if n is None else n
    emb = "emb" if emb_typ == F32 else b.op("Cast", ["emb"], to=F32)   # v6: Naht
    betrag = b.op("Add", [b.op("Sqrt", [b.op("ReduceSum", [b.op("Mul", [emb, emb]),
                                                           b.c([1], np.int64)], keepdims=1)]),
                          b.c(1e-9)])                                # [n, 1]
    v = b.op("Div", [emb, betrag])
    b.raus("emb_n", v)
    quelle = "f_norm" if norm_eingang else betrag
    b.raus("norm", b.op("Reshape", [quelle, b.c([-1] if n is None else [n], np.int64)]))
    eingaenge = [("emb", emb_typ, [achse, dim])]
    if norm_eingang:
        eingaenge.append(("f_norm", F32, [achse, 1]))
    return b.modell(eingaenge,
                    [("emb_n", F32, [achse, dim]), ("norm", F32, [achse])])


def graph_kopf(n, x_breite, y_breite, punkte, simcc_typ=F32):
    """RTMPose-Ausgaenge -> Kopf-Score je Gesicht, auf der GPU: Score je Punkt
    0,5 * (max simcc_x + max simcc_y), Kopf = Maximum ueber KOPF_IDX
    (pose_wache.skelett, core/ernte.pose_kopf). Groessen, die das RTMPose-ONNX nicht als
    feste Zahl deklariert (dim_value 0), bleiben offen; ORT kennt sie zur Laufzeit.

    simcc_typ (v6): liefert ein fp16-RTMPose, werden beide simcc-Baender als erste
    Handlung auf fp32 gehoben; die Auswertung dahinter bleibt Knoten fuer Knoten die
    fp32-Rechnung."""
    b = _Bau()
    sx = "simcc_x" if simcc_typ == F32 else b.op("Cast", ["simcc_x"], to=F32)   # v6: Naht
    sy = "simcc_y" if simcc_typ == F32 else b.op("Cast", ["simcc_y"], to=F32)
    mx = b.op("ReduceMax", [sx], axes=[2], keepdims=0)
    my = b.op("ReduceMax", [sy], axes=[2], keepdims=0)
    kp = b.op("Mul", [b.op("Add", [mx, my]), b.c(0.5)])
    kg = b.op("Gather", [kp, b.c(wk.pose_wache.KOPF_IDX, np.int64)], axis=1)
    b.raus("kopf", b.op("ReduceMax", [kg], axes=[1], keepdims=0))
    pk = punkte or "punkte"
    return b.modell([("simcc_x", simcc_typ, [n, pk, x_breite or "x_breite"]),
                     ("simcc_y", simcc_typ, [n, pk, y_breite or "y_breite"])],
                    [("kopf", F32, [n])])


# ------------------------------------------------------------------ Aufrufe
def _lauf(s, eingabe, auf_cpu):
    """Session mit einem GPU-Tensor als Eingang; Ausgaenge auf CPU (Zahlen) oder GPU."""
    b = s.io_binding()
    b.bind_ortvalue_input(s.get_inputs()[0].name, eingabe)
    for o in s.get_outputs():
        b.bind_output(o.name, "cpu" if auf_cpu else "cuda")
    s.run_with_iobinding(b)
    return b.copy_outputs_to_cpu() if auf_cpu else b.get_outputs()


def arena_shrink_setzen(an):
    """Den Shrink-Schalter dieses Prozesses stellen (.531, Start-Argument
    `--arena-shrink`). EINMAL je Prozess, aus `Engine.__init__`."""
    _ARENA_SHRINK["an"] = bool(an)


def mem_pattern_setzen(an):
    """Den Memory-Pattern-Schalter dieses Prozesses stellen (.532,
    Start-Argument `--mem-pattern`, Vorgabe 0 = aus — Begruendung und Messung
    im Modulkopf). EINMAL je Prozess, aus `Engine.__init__`: die
    Session-Optionen werden beim BAU gelesen, spaeter gestellt erreicht der
    Schalter keine gebaute Session mehr."""
    _MEM_PATTERN["an"] = bool(an)


def _shrink_ro():
    """RunOptions mit `memory.enable_memory_arena_shrinkage = gpu:0`, einmal
    gebaut. None, wenn der Schalter aus ist oder die Option nicht existiert.

    WAS DAS TUT (ORT-Recherche Q6): am ENDE eines Run gibt ORT die
    Allokationsregionen zurueck, in denen kein Chunk mehr in Gebrauch ist. Was
    lebt, bleibt — die geteilten Modellketten und die Puffer der Rechenstraenge
    pinnen ihre Regionen weiter. Es ist also kein Aufraeumen, sondern ein
    Zurueckgeben des ungenutzten Randes.
    GEMESSEN 15.09. (RTX 2060, Probe D): Worker-Maximum 2278 -> 1820 MiB (-20 %),
    30/30 Urteile unveraendert, Zeitkosten +9-12 %. Deshalb ein SCHALTER und keine
    Automatik: auf einer Karte mit Luft ist der Tausch schlecht, auf einer engen
    gut, und diese Abwaegung gehoert dem Betreiber."""
    if not _ARENA_SHRINK["an"]:
        return None
    if _ARENA_SHRINK["ro"] is None:
        try:
            ro = ort.RunOptions()
            ro.add_run_config_entry("memory.enable_memory_arena_shrinkage", "gpu:0")
            _ARENA_SHRINK["ro"] = ro
            _melden("arena shrink on: card memory is handed back after every "
                    "recognition chain (measured -20 % peak, +9-12 % time)")
        except Exception as e:                           # noqa: BLE001
            _ARENA_SHRINK["ro"] = False
            _melden(f"WARN: arena shrink not available ({type(e).__name__}: {e}) "
                    f"— running without it")
    return _ARENA_SHRINK["ro"] or None


def _weiter(s, werte, namen, auf_cpu):
    """Session s mit den GPU-Tensoren der vorigen Session als Eingang: nach Namen, wenn
    sie passen (RTMPose -> Kopf), sonst in Reihenfolge. -> (Ausgangsnamen, Ausgaenge)"""
    b = s.io_binding()
    paare = dict(zip(namen, werte))
    for i, e in enumerate(s.get_inputs()):
        b.bind_ortvalue_input(e.name, paare.get(e.name, werte[i]))
    for o in s.get_outputs():
        b.bind_output(o.name, "cpu" if auf_cpu else "cuda")
    # .531: geschrumpft wird NUR am letzten Glied einer Kette (`auf_cpu`), nicht an
    # jedem der acht Laeufe — genau so ist die Messung entstanden, und jeder
    # zusaetzliche Schrumpflauf kostet wieder Zeit.
    _ro = _shrink_ro() if auf_cpu else None
    if _ro is not None:
        s.run_with_iobinding(b, _ro)
    else:
        s.run_with_iobinding(b)
    return ([o.name for o in s.get_outputs()],
            b.copy_outputs_to_cpu() if auf_cpu else b.get_outputs())


def buendelweise(stufe, rgb, thetas):
    """Eine Stufe fuer mehrere Gesichter in festen Buendeln (BUENDEL). Seit v3c nur noch
    fuer die Stufe p (RTMPose); fd, e, t und r laufen ueber quantisiert().
    stufe[n] = (Ausschnitt-Session, [Modell-Sessions]); der Ausschnitt geht per IO-Binding
    von Session zu Session, zur CPU kommen die Ausgaenge der letzten. Aufgefuellt wird mit
    dem letzten Gesicht, dessen Doppel verworfen wird.
    -> je Gesicht ein Tupel seiner Ausgabezeilen"""
    aus = []
    for start in range(0, len(thetas), BUENDEL[-1]):
        teil = thetas[start:start + BUENDEL[-1]]
        n = next(b for b in BUENDEL if b >= len(teil))
        voll = teil + [teil[-1]] * (n - len(teil))
        s_aus, kette = stufe[n]
        b = s_aus.io_binding()
        b.bind_ortvalue_input("rgb", rgb)
        b.bind_cpu_input("th", np.stack(voll))
        b.bind_output("crop", "cuda")
        s_aus.run_with_iobinding(b)
        namen, werte = ["crop"], b.get_outputs()
        for k, s in enumerate(kette):
            namen, werte = _weiter(s, werte, namen, k == len(kette) - 1)
        aus.extend(tuple(w[j] for w in werte) for j in range(len(teil)))
    return aus


def dynamisch(stufe, rgb, thetas):
    """Eine Stufe mit offener n-Achse fuer ALLE Gesichter des Aufrufs in EINER Rechnung
    (v3c). stufe = (Ausschnitt-Session, [Modell-Sessions]) wie bei buendelweise, nur ohne
    Buendel-Ebene: nicht aufgefuellt, nicht zerlegt, n = len(thetas).
    -> je Gesicht ein Tupel seiner Ausgabezeilen, gleiche Form wie bei buendelweise."""
    s_aus, kette = stufe
    b = s_aus.io_binding()
    b.bind_ortvalue_input("rgb", rgb)
    b.bind_cpu_input("th", np.stack(thetas))
    b.bind_output("crop", "cuda")
    s_aus.run_with_iobinding(b)
    namen, werte = ["crop"], b.get_outputs()
    for k, s in enumerate(kette):
        namen, werte = _weiter(s, werte, namen, k == len(kette) - 1)
    return [tuple(w[j] for w in werte) for j in range(len(thetas))]


def quantisiert(stufe, rgb, thetas):
    """Eine dynamische Stufe in Aufrufen FESTER Breite (v7, worker_kern.AUFRUF_BREITE).

    Die Kette ist dieselbe wie bei dynamisch() — ein Ausschnitt-Graph und Modelle mit
    offener n-Achse —, nur wird sie nie wieder mit wechselnder Breite gerufen: der letzte
    Rest wird durch Wiederholen des letzten Gesichts aufgefuellt, dessen Doppel verworfen
    wird. Warum das Polstern und nicht ein zweiter, fest gebauter Graph fuer n = 1: eine
    zweite Form ist genau das, was v7 abschaffen will.
    AUFRUF_BREITE = None: der v6-Weg, ein Aufruf ueber alle Gesichter."""
    if wk.AUFRUF_BREITE is None:
        return dynamisch(stufe, rgb, thetas)
    aus = []
    for start in range(0, len(thetas), wk.AUFRUF_BREITE):
        teil = thetas[start:start + wk.AUFRUF_BREITE]
        voll = teil + [teil[-1]] * (wk.AUFRUF_BREITE - len(teil))
        aus.extend(dynamisch(stufe, rgb, voll)[:len(teil)])
    return aus


def dynamisch_fd(stufe, rgb, thetas, zuege, punkte):
    """EIN Aufruf der fd-Stufe (v8) mit GENAU so vielen Gesichtern, wie ihr Graph gebaut
    ist (FD_BREITE). Wie dynamisch(), nur mit vier Eingaengen und zwei Ausgaengen mehr:
    der Ausschnitt-Graph liefert neben dem Landmark-Crop (GPU-Tensor, geht in 1k3d68) die
    beiden Laplace-Summen, und die kommen sofort zur CPU — dort wird nur noch geteilt.

    DER SCHNITT DER PUNKTE LIEGT AUF DER CPU, nicht im Graphen: 1k3d68 gibt 3309 Zahlen
    (1103 Punkte x 3) aus, gebraucht sind die LETZTEN `punkte`. Es ist ein reiner Slice
    ohne Reduktion, also gewinnt ein Graph-Knoten dafuer nichts; er kostete eine Session
    mehr auf einer Karte, die bei zwei Threads schon 4,3 von 6,1 GB haelt. UNTERSCHIED ZU
    engine_ov (dort steckt der Schnitt im Kompilat) — und zugleich der Grund, aus dem der
    Intel-Fehler dieser Klasse hier nicht auftreten kann: die Grenze wird in numpy aus der
    Modellform gerechnet, nicht als Graph-Konstante gesetzt.
    -> je Gesicht (Punkte [punkte,3] float32, s_lap, s_lap2)"""
    s_aus, kette = stufe
    b = s_aus.io_binding()
    b.bind_ortvalue_input("rgb", rgb)
    b.bind_cpu_input("th", np.stack(thetas))
    b.bind_cpu_input("jx", np.stack([z[0] for z in zuege]))
    b.bind_cpu_input("iy", np.stack([z[1] for z in zuege]))
    b.bind_cpu_input("mu", np.stack([z[2] for z in zuege]))
    b.bind_cpu_input("mv", np.stack([z[3] for z in zuege]))
    b.bind_output("crop", "cuda")
    b.bind_output(NAME_SL, "cpu")
    b.bind_output(NAME_SL2, "cpu")
    s_aus.run_with_iobinding(b)
    aus = dict(zip([o.name for o in s_aus.get_outputs()], b.get_outputs()))
    sl, sl2 = aus[NAME_SL].numpy(), aus[NAME_SL2].numpy()
    namen, werte = ["crop"], [aus["crop"]]
    for k, s in enumerate(kette):
        namen, werte = _weiter(s, werte, namen, k == len(kette) - 1)
    # fc1 [n, 3309] -> je Gesicht die letzten `punkte` Punkte. np.asarray hebt eine
    # fp16-Ausgabe auf float32 (bei fp32 ist es ein No-Op ohne Kopie), genau wie in
    # det(); fd_front rechnet danach in float32 wie auf Intel.
    roh = np.asarray(werte[0], np.float32)
    gesamt = roh.shape[1] // 3
    pts = roh.reshape(-1, gesamt, 3)[:, gesamt - punkte:, :]
    return [(pts[j], float(sl[j]), float(sl2[j])) for j in range(len(thetas))]


def quantisiert_fd(stufe, rgb, thetas, zuege, punkte):
    """Die fd-Stufe fuer beliebig viele Gesichter, in Aufrufen fester Breite (FD_BREITE) —
    dasselbe Polster-Muster wie quantisiert(), nur mit den Leinwand-Zuegen im Gleichschritt
    zu den Matrizen."""
    aus = []
    for start in range(0, len(thetas), FD_BREITE):
        t_teil, z_teil = thetas[start:start + FD_BREITE], zuege[start:start + FD_BREITE]
        fehlt = FD_BREITE - len(t_teil)
        aus.extend(dynamisch_fd(stufe, rgb, t_teil + [t_teil[-1]] * fehlt,
                                z_teil + [z_teil[-1]] * fehlt, punkte)[:len(t_teil)])
    return aus


# ------------------------------------------------------------------ Modelle prozessweit
class ModellBestand:
    """Die aufloesungsUNABHAENGIGEN Modell-Ketten, EINMAL je Prozess (v5).

    Was hier liegt, kennt keine Frame-Form: die Eingangsformen der fuenf Modelle kommen
    aus den Modell-Dateien selbst bzw. aus pose_wache.INPUT_SIZE. Geometrie-Abhaengig ist
    allein die Zuschneide-Stufe davor, und die bleibt deshalb je Geometrie.

    Gebaut wird FAUL, je (Stufe, Breite) beim ersten Bedarf.

    E1: der Bestand kennt die Referenzen NICHT mehr (Matmul raus, graph_rec_post). Die
    Wache erk_pruefen entfaellt damit ersatzlos; pfade_pruefen bleibt, denn die Modell-
    DATEIEN traegt die geteilte Kette weiterhin."""

    def __init__(self, pfade=None):
        self.spec = wk.rec_spec()
        # v6: je Stufe der Pfad, der WIRKLICH geladen wird — die Vorgabe des Hauses oder
        # die per CLI uebergebene fp16-Fassung. Crop-Seiten und Rechentyp werden danach
        # aus DIESER Datei gelesen, nie aus einer Annahme ueber sie.
        self.pfade = self._aufloesen(pfade)
        mfd = onnx.load(self.pfade[wk.FD], load_external_data=False)
        me = onnx.load(self.pfade["e"], load_external_data=False)
        mt = onnx.load(self.pfade["t"], load_external_data=False)
        mp = onnx.load(self.pfade["p"], load_external_data=False)
        mr = onnx.load(self.pfade["r"], load_external_data=False)
        dim = lambda m, i: _eingang(m).type.tensor_type.shape.dim[i].dim_value  # noqa: E731
        pw, ph = wk.pose_wache.INPUT_SIZE
        # v6: Rechentyp je Stufe, aus der Modell-Datei gelesen.
        self.typ = {wk.FD: _typ(mfd), "e": _typ(me), "t": _typ(mt), "p": _typ(mp),
                    "r": _typ(mr)}
        self.seiten = {wk.FD: (dim(mfd, 2), dim(mfd, 3)),
                       "e": (dim(me, 2), dim(me, 3)), "t": (dim(mt, 2), dim(mt, 3)),
                       "p": (ph, pw), "r": (dim(mr, 2), dim(mr, 3))}
        # E1: die Laenge des Embeddings kommt aus dem Erkennungs-Modell selbst (bis v8 kam
        # sie aus der Referenz-Matrix, die es im Graphen nicht mehr gibt). Steht sie dort
        # nicht als Zahl, bleibt die Achse offen — geraten wird sie nicht.
        rd = [d.dim_value for d in mr.graph.output[0].type.tensor_type.shape.dim]
        self.emb_dim = rd[1] if len(rd) > 1 and rd[1] > 0 else "d"
        # E2c: traegt dieser Erkennungs-Kopf die Div-Naht, aus der die echte Feature-Norm
        # kommt? EINMAL am Modell abgelesen, damit Session und Post-Graph DIESELBE Antwort
        # benutzen — zwei getrennte Pruefungen koennten auseinanderlaufen.
        self.norm_naht = _div_naht(mr) is not None
        del mr
        # v8: die Punktzahl der Pose kommt aus der mittleren Form, an der sie geschaetzt
        # wird (68). Die GESAMTZAHL der Punkte im Ausgang wird gelesen und geprueft, nicht
        # angenommen — der Schnitt in dynamisch_fd rechnet mit ihr. (Intel-Lehre 13.09.:
        # eine geratene Schnittgrenze verfaelschte dort STILL die nachfolgende Stufe.)
        self.lm_punkte = len(wk.mean_lmk())
        lm_aus = [d.dim_value for d in mfd.graph.output[0].type.tensor_type.shape.dim]
        if len(lm_aus) != 2 or lm_aus[1] <= 0 or lm_aus[1] % 3 or lm_aus[1] // 3 < self.lm_punkte:
            raise SystemExit(f"1k3d68-Ausgang {mfd.graph.output[0].name!r} hat Form {lm_aus} "
                             f"— erwartet [N, 3*Punkte] mit Punkten >= {self.lm_punkte}")
        self.lm_gesamt = lm_aus[1] // 3
        self.norm_vorschrift = wk.norm_vorschriften(self.spec)
        self.norm = {k: _norm_bauer(self.norm_vorschrift[k]) for k in wk.STUFEN}
        aus_p = {o.name: [d.dim_value for d in o.type.tensor_type.shape.dim]
                 for o in mp.graph.output}
        punkte, x_breite, y_breite = aus_p["simcc_x"][1], aus_p["simcc_x"][2], aus_p["simcc_y"][2]
        self._bau = {
            # v8: die fd-Stufe steht VORNE, wie in engine_ov — dieselbe Bau- und
            # Rechenreihenfolge in beiden Engines. Ihre Kette ist EINE Session: 1k3d68.
            wk.FD: lambda n: [_sitzung(_fest(self.pfade[wk.FD], (n, 3, *self.seiten[wk.FD])))],
            "e": lambda n: [_sitzung(_fest(self.pfade["e"], (n, 3, *self.seiten["e"]),
                                           batch_frei=True))],
            "t": lambda n: [_sitzung(_fest(self.pfade["t"], (n, 3, *self.seiten["t"])))],
            "p": lambda n: [_sitzung(_fest(self.pfade["p"], (n, 3, ph, pw))),
                            _sitzung(graph_kopf(n, x_breite, y_breite, punkte,
                                                self.typ["p"]))],
            "r": lambda n: [_sitzung(_fest(self.pfade["r"], (n, 3, *self.seiten["r"]),
                                           norm_aus=self.norm_naht)),
                            _sitzung(graph_rec_post(n, self.emb_dim, self.typ["r"],
                                                    norm_eingang=self.norm_naht))]}
        self._ketten = {}
        self._schloss = threading.Lock()
        self.bau_s = 0.0                                 # Summe der geteilten Bauzeit

    def _aufloesen(self, pfade):
        """Die fuenf Modell-Pfade je Stufe: was uebergeben wurde, sonst die Vorgabe des
        Hauses (worker_kern.vorgabe_pfade). EINE Stelle, damit __init__ und pfade_pruefen
        dieselbe Rechnung machen."""
        p = dict(pfade or {})
        vorgabe = wk.vorgabe_pfade(self.spec)
        return {k: (p.get(k) or vorgabe[k]) for k in wk.STUFEN}

    def bauen(self, k, n):
        """Eine FRISCHE Modell-Kette der Stufe k fuer Breite n (n = None: offene Achse).
        Fuer Stufen, die nicht geteilt werden; sie gehoert dann dem Aufrufer allein."""
        return self._bau[k](n)

    def kette(self, k, n):
        """Die GETEILTE Kette der Stufe k fuer Breite n: beim ersten Bedarf gebaut,
        danach dasselbe Session-Objekt fuer jede weitere Geometrie."""
        with self._schloss:
            s = self._ketten.get((k, n))
            if s is None:
                t0 = time.monotonic()
                s = self._ketten[(k, n)] = self._bau[k](n)
                self.bau_s += time.monotonic() - t0
            return s

    def pfade_pruefen(self, pfade):
        """Die geteilten Ketten tragen die Dateien der ERSTEN Geometrie. Kaeme eine zweite
        mit anderen, rechnete sie still mit den ersten — ein fp32-Aufruf, der unbemerkt
        fp16-Gewichte benutzt, waere genau der Fehler, den diese Pruefung verhindert."""
        soll = self._aufloesen(pfade)
        if soll != self.pfade:
            raise SystemExit(f"ModellBestand: zweite Modell-Auswahl weicht ab — "
                             f"{self.pfade} steht, verlangt wurde {soll}")

    def sessions_zaehlen(self):
        """Wie viele ort.InferenceSession der Bestand haelt — gezaehlt, nicht gerechnet."""
        return sum(len(k) for k in self._ketten.values())


# ------------------------------------------------------------------ Lauf
class Satz:
    """Alles, was EIN Rechenstrang fuer sich braucht: die beiden Geraetepuffer fuer y/uv,
    die gehaltene Bindung der Vorverarbeitung und der RGB-Tensor des AKTUELLEN Frames.

    Warum je Strang (v4-Inventur): ort.InferenceSession.run_with_iobinding ist je Session
    thread-sicher und jede IoBinding entsteht ohnehin frisch je Aufruf — gefaehrlich ist
    allein dieser Frame-Zustand. Zwei Threads wuerden sich sonst den Frame unter der
    laufenden Vorverarbeitung austauschen, und der Fehler faellt nicht auf, er verschiebt
    nur Werte. Die Sessions selbst bleiben geteilt, genau das ist der Zweck."""

    def __init__(self, g):
        self.g = g
        self.y_gpu = ort.OrtValue.ortvalue_from_numpy(
            np.zeros((1, g.H, g.W, 1), np.uint8), "cuda", 0)
        self.uv_gpu = ort.OrtValue.ortvalue_from_numpy(
            np.zeros((1, g.H // 2, g.W // 2, 2), np.uint8), "cuda", 0)
        self.pre_bindung, self.rgb = None, None

    def det(self, y, uv):
        """y und uv EINMAL je Frame auf die GPU (v2), dann die Vorverarbeitung EINMAL
        (v3a): 'det_in' geht sofort in den Detektor, 'rgb' bleibt als GPU-Tensor liegen
        und wird von den Ausschnitt-Stufen gelesen. Die Bindung bleibt mit ihm liegen, bis
        der naechste Frame sie ersetzt, damit der GPU-Tensor lebt.
        -> die neun Detektor-Ausgaenge

        v3b: Mit dem fp16-Detektor kommen sie als float16 herunter; sie werden hier sofort
        auf float32 gehoben, damit die SCRFD-Nachverarbeitung unveraendert in float32
        rechnet (bei fp32 ist np.asarray ein No-Op ohne Kopie)."""
        g = self.g
        self.y_gpu.update_inplace(np.ascontiguousarray(y))
        self.uv_gpu.update_inplace(np.ascontiguousarray(uv))
        b = g.s_pre_det.io_binding()
        b.bind_ortvalue_input("y", self.y_gpu)
        b.bind_ortvalue_input("uv", self.uv_gpu)
        for name in g.pre_aus:
            b.bind_output(name, "cuda")
        g.s_pre_det.run_with_iobinding(b)
        aus = dict(zip(g.pre_aus, b.get_outputs()))
        self.pre_bindung, self.rgb = b, aus["rgb"]
        return [np.asarray(o, np.float32)
                for o in _lauf(g.s_det, aus["det_in"], True)]

    def stufe(self, k, thetas):
        """Eine Stufe fuer die uebergebenen Gesichter, ohne dass der Aufrufer wissen muss,
        ob sie dynamisch (fd, e, t, r) oder in festen Buendeln (p) laeuft.
        -> je Gesicht ein Tupel seiner Ausgabezeilen"""
        if self.rgb is None:
            raise RuntimeError("stufe() vor det()")
        if k in self.g.stufen_dyn:
            return quantisiert(self.g.stufen_dyn[k], self.rgb, thetas)
        return buendelweise(self.g.stufen[k], self.rgb, thetas)

    def stufe_fd(self, thetas, zuege):
        """Die fd-Stufe (v8): eigener Weg, weil sie vier Eingaenge und zwei Ausgaenge mehr
        hat als die uebrigen. -> je Gesicht (Punkte [68,3], s_lap, s_lap2)"""
        if self.rgb is None:
            raise RuntimeError("stufe_fd() vor det()")
        return quantisiert_fd(self.g.stufen_dyn[wk.FD], self.rgb, thetas, zuege,
                              self.g.bestand.lm_punkte)

    def warm(self):
        """Jede Session einmal rechnen, bevor die Uhr laeuft — mit genau den Formen, die
        der Lauf ruft. Die Threads waermen nacheinander (der Kern haelt das Schloss): das
        haelt die erste Allokation und die cuDNN-Algorithmensuche je Form in fester
        Reihenfolge."""
        g = self.g
        y0 = np.zeros((1, g.H, g.W, 1), np.uint8)
        uv0 = np.full((1, g.H // 2, g.W // 2, 2), 128, np.uint8)
        self.det(y0, uv0)
        rgb = self.rgb
        th0 = np.array([[1, 0, 0], [0, 1, 0]], np.float32)
        for stufe in g.stufen.values():                  # feste Buendel: jede Stufe einmal
            for n in BUENDEL:
                buendelweise(stufe, rgb, [th0] * n)
        # v7: ueber quantisiert() gewaermt, also mit genau der Form, die der Lauf ruft —
        # dieselbe Funktion statt einer zweiten Vorschrift daneben.
        for k, stufe in g.stufen_dyn.items():
            if k == wk.FD:
                continue                                 # eigener Weg, unten
            for n in WARM_DYN:
                quantisiert(stufe, rgb, [th0] * n)
        # v8: die fd-Stufe mit einem gueltigen Leinwand-Zug waermen (die Gather-Indizes
        # muessen im Bild liegen, sonst laese sie Unsinn).
        zug0 = wk.leinwand_zug([0, 0, wk.LEINWAND - 2, wk.LEINWAND - 2], g.W, g.H)
        quantisiert_fd(g.stufen_dyn[wk.FD], rgb, [th0] * FD_BREITE, [zug0] * FD_BREITE,
                       g.bestand.lm_punkte)


class Geometrie:
    """Die Sessions EINER Clip-Geometrie, einmal gebaut.
    v3c: fd, e, t und r je EINE Kette mit offener n-Achse (stufen_dyn), p weiterhin je
    Buendelgroesse eine eigene (stufen). Beide Male (Ausschnitt-Session, [Modell-Sessions]).
    v5: die Modell-Sessions dieser Paare kommen fuer die geteilten Stufen aus dem
    prozessweiten ModellBestand — die Geometrie baut dann nur noch die Ausschnitt-Session
    davor.

    Kein Frame-Zustand am Objekt (v4): y/uv-Puffer, Bindung und rgb liegen im Satz, den
    sich jeder Rechenstrang einmal holt. Damit traegt dieselbe Klasse den Einzelstrang und
    die Mehrstrang-Fassung."""

    def __init__(self, W, H, best, det_onnx=None):
        t_bau0 = time.monotonic()
        self.W, self.H = W, H
        (det_w, det_h), (neu_w, neu_h), det_scale = wk.det_geometrie(W, H)
        self.det_wh, self.det_scale = (det_w, det_h), det_scale
        det_pfad = det_onnx or wk.modell_pfad("det_10g")
        # v3b: Der Rechentyp des Detektor-Zweigs folgt dem MODELL, er wird nicht
        # geschaltet. So kann derselbe Code das fp32- und das fp16-Detektor-ONNX fahren,
        # ohne dass ein Schalter und die Datei auseinanderlaufen koennen.
        self.det_pfad = det_pfad
        self.det_typ = _typ_datei(det_pfad)
        self.det_fp16 = self.det_typ == F16
        self.pixel_typ = F16 if PIXEL_FP16 else F32
        self.s_pre_det = _sitzung(graph_pre_det(H, W, (det_w, det_h), (neu_w, neu_h),
                                                self.pixel_typ, self.det_typ))
        # v3a: die Ausgangsnamen der Vorverarbeitung einmal merken. Gebunden wird in genau
        # dieser Reihenfolge, dann passt get_outputs() dazu, ohne eine Annahme ueber die
        # Reihenfolge zu machen.
        self.pre_aus = [o.name for o in self.s_pre_det.get_outputs()]
        for _n in ("det_in", "rgb"):
            if _n not in self.pre_aus:
                raise SystemExit(f"Vorverarbeitung ohne Ausgang {_n!r}: {self.pre_aus}")
        self.s_det = _sitzung(_fest(det_pfad, (1, 3, det_h, det_w)))
        self.bestand = best
        self.seiten = best.seiten
        geteilt0 = best.bau_s
        self.geteilt = tuple(k for k in wk.STUFEN if k in GETEILTE_STUFEN)
        self.stufen, self.stufen_dyn = {}, {}
        for k in wk.STUFEN:
            hol = best.kette if k in GETEILTE_STUFEN else best.bauen
            if k == wk.FD:
                # v8: die fd-Stufe traegt neben ihrem Landmark-Ausschnitt die
                # Laplace-Leinwand im SELBEN Graphen — ein Aufruf statt zwei. Ihr
                # Ausschnitt-Graph ist auf FD_BREITE gebaut, ihre Modell-Kette bleibt wie
                # e/t/r auf der offenen n-Achse.
                self.stufen_dyn[k] = (_sitzung(graph_crop_fd(H, W, FD_BREITE, self.seiten[k],
                                                             best.norm[k], best.typ[k])),
                                      hol(k, None))
            elif k in DYN_STUFEN:
                self.stufen_dyn[k] = (_sitzung(graph_crop(H, W, None, self.seiten[k],
                                                          best.norm[k], best.typ[k])),
                                      hol(k, None))
            else:
                self.stufen[k] = {
                    n: (_sitzung(graph_crop(H, W, n, self.seiten[k], best.norm[k],
                                            best.typ[k])),
                        hol(k, n))
                    for n in BUENDEL}
        self.bau_geteilt_s = best.bau_s - geteilt0    # was DIESE Geometrie am Bestand zahlte
        self.nm = wk.gitter_norm(W, H)
        self.zentren = wk.zentren_fuellen(self.det_wh, self.det_scale)
        if not hasattr(ort.OrtValue, "update_inplace"):
            raise SystemExit("OrtValue.update_inplace fehlt in dieser onnxruntime-Fassung")
        self._lokal = threading.local()
        self._satz_schloss = threading.Lock()
        self.saetze = 0
        self.bau_s = time.monotonic() - t_bau0

    def satz(self):
        """Der Satz DIESES Rechenstrangs; beim ersten Aufruf angelegt, danach kostet er
        nur noch einen Attributzugriff. Das Schloss schuetzt allein die Anlage."""
        s = getattr(self._lokal, "satz", None)
        if s is not None:
            return s
        with self._satz_schloss:
            s = Satz(self)
            self.saetze += 1
        self._lokal.satz = s
        return s

    def sessions_zaehlen(self):
        """Wie viele ort.InferenceSession diese Geometrie BENUTZT — gezaehlt an den
        gebauten Objekten, nicht aus BUENDEL hochgerechnet. Die geteilten sind mitgezaehlt;
        was ihr allein gehoert, sagt sessions_eigen()."""
        n = 2                                            # Vorverarbeitung + Detektor
        for _s_aus, kette in self.stufen_dyn.values():
            n += 1 + len(kette)
        for je_n in self.stufen.values():
            for _s_aus, kette in je_n.values():
                n += 1 + len(kette)
        return n

    def sessions_eigen(self):
        """Wie viele Sessions NUR dieser Geometrie gehoeren (v5)."""
        n = 2
        for k, (_s_aus, kette) in self.stufen_dyn.items():
            n += 1 + (0 if k in self.geteilt else len(kette))
        for k, je_n in self.stufen.items():
            for _s_aus, kette in je_n.values():
                n += 1 + (0 if k in self.geteilt else len(kette))
        return n

    def cuda_optionen_ist(self):
        """Was ORT fuer die gebaute Detektor-Session als CUDA-Optionen ZURUECKMELDET,
        nicht was wir gesetzt haben (v3d). Ein Schalter, den die Laufzeit verschluckt,
        waere sonst als Messung getarnt."""
        ist = (self.s_det.get_provider_options() or {}).get(EP, {})
        return {k: ist.get(k) for k in cuda_optionen()}


# ------------------------------------------------------------------ Bild-Weg (E2c)
class BildStufen:
    """Die Stufen der Engine auf CPU-GELIEFERTEN Ausschnitten (E2c, Bild-Weg) —
    Gegenstueck zu engine_ov.BildStufen, gleiche Schnittstelle, gleiche Begruendung
    (siehe dort: Katalog-Wege arbeiten auf Einzelbildern, ihre Ausschnitte entstehen
    seit jeher auf der CPU, gebraucht werden nur det, fd und r).

    UNTERSCHIED ZUM VIDEO-WEG dieser Engine: keine IO-Bindung, keine GPU-Tensoren
    zwischen den Sessions. Der Bild-Weg reicht numpy hinein und holt numpy heraus —
    er ist ein Katalog-Pfad mit wenigen Aufrufen je Klick, kein Durchsatz-Pfad, und
    eine zweite Bindungs-Mechanik waere Aufwand ohne Ertrag. Die SESSIONS sind
    dieselben geteilten Ketten, auf denen auch die Analyse rechnet (bestand.kette) —
    darum geht es in E2c.

    EHRLICHE GRENZE: dieser Zweig ist auf dieser Maschine NICHT gefahren worden (das
    E2c-Gate lief auf Intel, das CUDA-Testnotebook gehoert zu E5). Er ist die
    symmetrische Fassung des Intel-Wegs, damit der Dienst auf beiden Backends
    dieselbe Schnittstelle findet; seine Abnahme steht aus."""

    BREITE = 1

    def __init__(self, engine):
        self.engine = engine
        if engine.bestand is None:
            engine.bestand = ModellBestand(engine.pfade)
        self.bestand = engine.bestand
        self.seiten = self.bestand.seiten
        self.norm_vorschrift = self.bestand.norm_vorschrift
        self.lm_punkte = self.bestand.lm_punkte
        self._det = {}                        # (det_w, det_h) -> Session
        self._ketten = {}                     # Stufe -> [Session, ...]
        self._schloss = threading.Lock()

    def det(self, leinwand, det_wh):
        """Die neun Detektor-Ausgaenge fuer EINE fertige Leinwand [1,3,h,w] float32
        (RGB, 0..255). Die Normierung steht hier NICHT im Graphen — anders als bei
        engine_ov, wo der Bild-Detektor als eigenes Kompilat entsteht; hier wird
        dasselbe Detektor-ONNX geladen, das auch der Video-Weg fuehrt, und die
        Normierung rechnet bild_kern davor auf der CPU."""
        det_w, det_h = det_wh
        with self._schloss:
            s = self._det.get((det_w, det_h))
            if s is None:
                t0 = time.monotonic()
                pfad = self.engine.det_onnx or wk.modell_pfad("det_10g")
                s = self._det[(det_w, det_h)] = _sitzung(
                    _fest(pfad, (1, 3, det_h, det_w)))
                self.bestand.bau_s += time.monotonic() - t0
        x = np.asarray(leinwand, _np_typ(_typ_datei(self.engine.det_onnx
                                                    or wk.modell_pfad("det_10g"))))
        aus = s.run(None, {s.get_inputs()[0].name: x})
        return [np.asarray(a, np.float32) for a in aus]

    def det_normiert(self):
        """Rechnet dieser Bild-Detektor die (x-mean)/std selbst? -> False.
        engine_ov baut sie in sein Kompilat, hier muss bild_kern sie liefern. Die
        Frage steht als METHODE da, damit bild_kern sie nicht an der Engine-Sorte
        festmacht."""
        return False

    def stufe(self, k, X):
        """Eine Stufe auf FERTIG NORMIERTEN Ausschnitten X [n,3,h,w] float32.
        -> je Zeile ein Tupel ihrer Ausgabezeilen (Form wie Satz.stufe)"""
        with self._schloss:
            kette = self._ketten.get(k)
            if kette is None:
                kette = self._ketten[k] = self.bestand.kette(k, self.BREITE)
        aus = []
        for zeile in np.asarray(X, np.float32):
            werte = [np.asarray(zeile[None], _np_typ(self.bestand.typ[k]))]
            namen = [kette[0].get_inputs()[0].name]
            for s in kette:
                paare = dict(zip(namen, werte))
                eingabe = {e.name: paare.get(e.name, werte[i])
                           for i, e in enumerate(s.get_inputs())}
                werte = s.run(None, eingabe)
                namen = [o.name for o in s.get_outputs()]
            if k == wk.FD:
                # fc1 [1, 3309] -> die letzten `lm_punkte` Punkte, gerechnet aus der
                # Modellform wie dynamisch_fd — nie als Konstante.
                roh = np.asarray(werte[0], np.float32)
                gesamt = roh.shape[1] // 3
                werte = [roh.reshape(-1, gesamt, 3)[:, gesamt - self.lm_punkte:, :]]
            aus.append(tuple(np.asarray(w, np.float32)[0] for w in werte))
        return aus

    def auskunft(self):
        return {"engine": Engine.name, "geraet": EP, "breite": self.BREITE,
                "det_leinwaende": [f"{w}x{h}" for (w, h) in sorted(self._det)],
                "stufen": sorted(self._ketten)}


def _crop_sessions(g):
    """Je Stufe EINE Ausschnitt-Session dieser Geometrie, egal ob sie auf der offenen
    n-Achse (fd, e, t, r) oder in festen Buendeln liegt (p). Sie existiert, damit die
    Kopf-Auskunft die Typen ALLER FUENF Stufen ablesen kann: die fruehere Fassung
    fragte nur `stufen_dyn` und haette einen abweichenden p-Ausschnitt nicht gesehen.
    Bei den Buendel-Stufen genuegt die erste Groesse — alle Buendel entstehen aus
    demselben `graph_crop`-Aufruf, nur mit anderem n. -> {stufe: Session}"""
    aus = {k: s_aus for k, (s_aus, _kette) in g.stufen_dyn.items()}
    for k, je_n in g.stufen.items():
        n0 = sorted(je_n)[0]
        aus[f"{k}[n={n0}]"] = je_n[n0][0]
    return aus


# ------------------------------------------------------------------ Die Engine
class Engine:
    """Die CUDA-Seite, wie der Kern sie sieht: Frames, Geometrien, Kopf-Auskunft."""

    name = "cuda"
    stufen_folge = wk.STUFEN

    @staticmethod
    def argumente(ap):
        ap.add_argument("--wurzel", help="Projektwurzel (im Image /app)")
        ap.add_argument("--det-onnx", dest="det_onnx",
                        help="Detektor-ONNX statt des Modells aus dem Modell-Vertrag "
                             "(v3b: die offline konvertierte fp16-Fassung von det_10g). "
                             "Erwartet das Modell fp16, rechnet auch der Detektor-Zweig "
                             "der Vorverarbeitung in fp16.")
        for _k, flagge, ziel, hilfe in MODELL_SCHALTER:
            ap.add_argument(flagge, dest=ziel,
                            help=hilfe + " (Vorgabe seit E3.5: die im Image gebackene "
                                         "fp16-Fassung aus models/fp16 laut Manifest; "
                                         "dieser Schalter ueberschreibt sie)")

    def __init__(self, a):
        if a.det_onnx and not os.path.exists(a.det_onnx):
            raise SystemExit(f"--det-onnx {a.det_onnx!r} gibt es nicht")
        # E3.5: die gebackenen fp16-Dateien sind die VORGABE, ein CLI-Schalter gewinnt.
        # Reihenfolge ist Absicht: erst lesen+pruefen, dann fuellen — so steht der
        # Bericht auch dann, wenn nichts gefunden wurde.
        self.fp16_pfade, self.fp16_bericht = fp16_bestand()
        self.det_onnx = a.det_onnx or self.fp16_pfade.get("det")
        self.pfade = self._modell_pfade(a)
        for k, p in self.fp16_pfade.items():
            if k != "det":
                self.pfade.setdefault(k, p)
        if EP not in ort.get_available_providers():
            raise SystemExit("kein CUDA-Provider, kein Rueckfall")
        # .531: HIER, nicht in `geometrie_bauen`. Diese Stelle laeuft in
        # `worker_dienst.engine_bauen` vor jedem Job und damit sicher vor der
        # ersten InferenceSession; `geometrie_bauen` liefe erst danach und der
        # Reihenfolge-Vertrag der Env-Arena waere gebrochen.
        env_arena_registrieren(getattr(a, "vram_deckel_mb", 0) or 0,
                               getattr(a, "arena_strategie", None)
                               or ARENA_STRATEGIE_VORGABE)
        arena_shrink_setzen(getattr(a, "arena_shrink", 0))
        # .532: fehlt das Argument (Proben, fremde Aufrufer), gilt die Vorgabe
        # AUS — dasselbe, was ein Start ohne Schalter bedeutet.
        mem_pattern_setzen(getattr(a, "mem_pattern", 0))
        os.makedirs(a.out, exist_ok=True)
        self.bestand = None

    @staticmethod
    def _modell_pfade(a):
        """Die genannten Dateien als Stufen-dict {stufe: pfad}; ungenannte fehlen darin
        und bleiben bei der Vorgabe des Hauses. Was genannt ist, muss es geben — ein
        Tippfehler im Pfad soll hier scheitern und nicht still die fp32-Vorgabe fahren."""
        aus = {}
        for k, flagge, ziel, _hilfe in MODELL_SCHALTER:
            p = getattr(a, ziel, None)
            if not p:
                continue
            if not os.path.exists(p):
                raise SystemExit(f"{flagge} {p!r} gibt es nicht")
            aus[k] = p
        return aus

    def frames(self, clip, W, H, schritt, wache=None):
        return frames_nv12(clip, W, H, schritt, wache=wache)

    def bild_stufen(self):
        """Der BILD-Weg dieser Engine (E2c), einmal je Prozess. -> BildStufen"""
        if getattr(self, "_bild", None) is None:
            self._bild = BildStufen(self)
        return self._bild

    def geometrie_bauen(self, geo):
        """Je Clip-Geometrie einmal die Sessions. -> {(W, H): Geometrie}"""
        if self.bestand is None:
            self.bestand = ModellBestand(self.pfade)
        else:
            self.bestand.pfade_pruefen(self.pfade)
        graphen = {}
        for W, H, _fps in geo.values():
            if (W, H) not in graphen:
                graphen[(W, H)] = Geometrie(W, H, self.bestand, self.det_onnx)
        return graphen

    def kopf_auskunft(self, graphen):
        """Was WIRKLICH geladen und gebaut wurde — gelesen aus den gebauten Objekten,
        nicht aus den CLI-Wuenschen; ein verschluckter Schalter faellt damit im Bericht
        auf, statt als Variante durchzugehen (Regel aus v3d)."""
        g0 = next(iter(graphen.values()))
        best = self.bestand
        fd_aus = g0.stufen_dyn[wk.FD][0]
        return {"provider": EP, "ort": ort.__version__,
                # E3.5: was das IMAGE an fp16-Artefakten mitbringt und ob die
                # AUSGELIEFERTEN Dateien ihre Manifest-md5 halten. Steht neben
                # `modell_pfade`/`modell_typen`, die am gebauten Objekt abgelesen sind —
                # zusammen belegen die drei, dass wirklich die gebackenen Dateien
                # rechnen und nicht still die fp32-Vorgabe.
                "fp16": self.fp16_bericht,
                "det_onnx": g0.det_pfad,
                "det_fp16": {f"{g.W}x{g.H}": g.det_fp16 for g in graphen.values()},
                "dyn_stufen": sorted(g0.stufen_dyn), "fest_stufen": sorted(g0.stufen),
                "warm_n": list(WARM_DYN),
                "sessions": {f"{g.W}x{g.H}": g.sessions_zaehlen() for g in graphen.values()},
                "geteilte_stufen": list(GETEILTE_STUFEN),
                "sessions_eigen": {f"{g.W}x{g.H}": g.sessions_eigen()
                                   for g in graphen.values()},
                "sessions_bestand": best.sessions_zaehlen(),
                # AN DEN GEBAUTEN SESSIONS ABGELESEN, nicht behauptet (f32-Warp-Fix
                # 14.09.2026): welchen Typ der Ausschnitt-Graph je Stufe an seinen
                # Eingaengen fuehrt und was er ausgibt. Der Warp rechnet f32, solange
                # 'rgb' und 'th' fp32 sind — genau das steht hier je Stufe.
                "ausschnitt": {
                    "ein_typ": {k: {e.name: e.type for e in s.get_inputs()
                                    if e.name in ("rgb", "th")}
                                for k, s in sorted(_crop_sessions(g0).items())},
                    "aus_typ": {k: {o.name: o.type for o in s.get_outputs()
                                    if o.name == "crop"}
                                for k, s in sorted(_crop_sessions(g0).items())},
                    "u8_rundung": "floor(x+0.5) nach dem Warp, vor der Normierung"},
                "pixel_typ": _typ_name(g0.pixel_typ), "pixel_fp16_soll": PIXEL_FP16,
                "det_typ": _typ_name(g0.det_typ),
                "modell_typen": {k: _typ_name(t) for k, t in sorted(best.typ.items())},
                "modell_pfade": {k: best.pfade[k] for k in sorted(best.pfade)},
                "emb_dim": best.emb_dim,
                "cudnn_soll": cuda_optionen(), "cudnn_ist": g0.cuda_optionen_ist(),
                # .531: aus `_ENV_ARENA` GELESEN, nicht aus dem Wunsch — ein
                # verschluckter Deckel faellt damit im Bericht auf, statt als
                # Variante durchzugehen (dieselbe Regel wie oben).
                "vram_deckel_mb": _ENV_ARENA["deckel_mb"],
                "arena_strategie": arena_strategie_name(),
                "arena_shrink": bool(_ARENA_SHRINK["an"]),
                # .532: AN den Sessions wirksam, nicht nur gewuenscht — der
                # Schalter steht vor dem ersten Bau fest und aendert sich
                # danach nicht mehr.
                "mem_pattern": bool(_MEM_PATTERN["an"]),
                "env_arena": {"registriert": _ENV_ARENA["registriert"],
                              "geraet": _ENV_ARENA["geraet"],
                              "pinned": _ENV_ARENA["pinned"],
                              "fehler": _ENV_ARENA["fehler"]},
                "buendel_deckel": BUENDEL_DECKEL, "buendel": list(BUENDEL),
                # v8: was die fd-Stufe wirklich traegt, an den gebauten Objekten
                # abgelesen. Die Typen des Ausschnitt-Graphen sind der Beleg, dass der
                # Laplace-Zweig in fp32 rechnet — behauptet wird hier nichts.
                "fd": {"breite": FD_BREITE, "punkte_im_ausgang": best.lm_gesamt,
                       "crop_ein": {e.name: e.type for e in fd_aus.get_inputs()},
                       "crop_aus": {o.name: o.type for o in fd_aus.get_outputs()}}}
