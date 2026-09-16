#!/usr/bin/env python3
"""ENGINE OpenVINO/iGPU (Intel) — die Backend-Haelfte des Prototyp-Workers (E1).

HERKUNFT: herausgezogen aus dem abgenommenen v8-Prototyp `worker_gpu.py`
(md5 e8e6d7b4). Graph-Bau, Decoder-Anbindung, Speicher-Besitz (RemoteTensor),
Formstrategie und Optionen stehen hier; alles, was einen WERT entscheidet — Kaskade,
Latten, Thetas, Detektor-Nachverarbeitung, Scores, Zusammenfassung — liegt im
backend-freien `worker_kern.py`. Die Kopfabschnitte v2-v8 des Prototyps gelten
unveraendert weiter; sie sind die Herleitung dieses Graph-Baus.

PIXELWEG, die CPU fasst kein Pixel an:
  ffmpeg/VAAPI dekodiert, waehlt die Sample-Frames noch auf der GPU aus und gibt
  NV12 heraus (keine Farbumrechnung auf der CPU). OpenVINO-Graphen auf der iGPU:
    A    je Frame      NV12 -> RGB-Vollbild, daraus ZWEI Ausgaenge: die neun
                       Detektor-Ausgaenge (Leinwand wie insightface -> det_10g) und
                       'rgb', das Vollbild selbst
    fd   je Detektion  rgb -> Landmark-Ausschnitt -> 1k3d68, dazu die Laplace-Leinwand
    e    k bestanden   rgb -> Box-Ausschnitt -> fiqa
    t    e bestanden   rgb -> align112-Ausschnitt -> ediffiqa
    p    t bestanden   rgb -> Pose-Ausschnitt -> RTMPose + Kopf-Score
    r    p bestanden   rgb -> 112er-Ausschnitt -> Erkennung -> L2-Embedding + Norm
  Das RGB-Vollbild bleibt dabei auf der GPU: es ist ein OpenVINO-RemoteTensor, den der
  Vorverarbeitungs-Graph beschreibt und die Ausschnitt-Graphen lesen (v7). Zur CPU
  zurueck kommen nur Zahlen.

E1-AENDERUNG (Konzept §1c, MATMUL RAUS): die Erkennungs-Stufe gibt jetzt das
L2-normierte EMBEDDING [n, 512] und die Feature-Norm aus — die Referenz-Matrix ist
KEINE Graph-Konstante mehr, den Score-Matmul und das Maximum je Person rechnet der
Kern auf der CPU (worker_kern.scores_rechnen). Damit braucht ein Referenz-Wechsel
weder Rekompilat noch Prozess-Neustart; die Engine kennt die Referenzen gar nicht
mehr (erk_pruefen entfaellt ersatzlos, es gab nichts mehr zu schuetzen).

KEIN RUECKFALL: Geraet fest "GPU" (kein AUTO, HETERO, CPU, NPU). Die ffmpeg-Kette
endet mit hwdownload; ein Software-Decode laesst sie scheitern.

f32-WARP-FIX (14.09.2026, gemessen — runs/zerlegung_klein_20260914/): die
Ausschnitt-Graphen ALLER fuenf Stufen tragen jetzt den Praezisions-Hinweis f32 (bis
hierher nur fd, und dort aus dem Laplace-Grund), und hinter dem GridSample steht eine
uint8-Rundung. Anlass war der Schiedsrichter-Lauf desselben Tages: bei kleinen
Ferngesichtern lag der neue Weg 7/7 EINSEITIG unter der CPU-fp32-Referenz der alten
Kette (mittleres |d| 0,0701, Groesstwert 0,208), und die Zerlegung fand als dominante
Rechen-Achse den fp16-Warp. Herleitung und Zahlen stehen bei `graph_crop` und
`_u8_rundung`; der Hinweis kostet nichts, er war in 8/8 Faellen schneller als fp16.

NICHT BITGLEICH ZU PROD: NV12->RGB ist eine andere Umrechnung als cv2 YUV2BGR_I420,
und die Abtastung bleibt bilinear in Gleitkomma statt OpenCV-Festkomma (nur die
Quantisierung des Ergebnisses ist seit dem Fix dieselbe).
Der Prototyp misst Tempo; der gepinnte Pixelpfad (CLAUDE.md) gilt fuer ihn nicht.
"""
import os
import shutil
import sys
import threading
import time

import numpy as np

import worker_kern as wk                                 # noqa: E402  Bootstrap + Wert-Weg

import openvino as ov                                    # noqa: E402
# opset15 statt opset16: im Prod-Image steckt OpenVINO 2025.4.1 (in onnxruntime-openvino
# 1.24.1); dort ist erst opset15 ein Vollsatz, opset16 enthaelt nur die neuen Operationen.
# Alle hier benutzten Operationen gibt es in opset15 unter 2025.4.1 und 2026.3.1
# (geprueft 11.09.).
from openvino import opset15 as ops                      # noqa: E402

GERAET = "GPU"
# Die Namen der Geraete-Tensoren, ueber die die Graphen aneinanderhaengen. Sie stehen
# hier EINMAL, weil sie an drei Stellen zusammenpassen muessen: im Graph-Bau (set_names),
# beim Binden (set_tensor nimmt einen RemoteTensor nur ueber den Namen) und in der
# Kopfzeile.
NAME_RGB, NAME_CROP = "rgb", "crop"
# Die Namen der beiden Zahlen-Ausgaenge des fd-Ausschnitt-Graphen (Summe und Summe der
# Quadrate der Laplace-Werte ueber den engen Crop).
NAME_SL, NAME_SL2 = "s_lap", "s_lap2"
# Platzbedarf des Kompilat-Caches. Gemessen 12.09. an v2: 947 MB fuer die 17 Graphen EINER
# 4K-Geometrie. v7/v8 bauen je Geometrie sechs Graphen und je Prozess fuenf — der Bedarf
# faellt deutlich, die Wache bleibt aber auf dem alten Wert stehen: sie ist eine
# UNTERGRENZE fuer freien Platz, und zu viel verlangter Platz kostet nichts. Grund fuer die
# Wache: reicht der Platz nicht, schreibt OpenVINO den letzten Blob abgeschnitten OHNE
# Fehler, und erst der naechste Lauf scheitert beim Lesen ("Check 'written_size == size'
# failed", binary_buffer.hpp:27). Genau so passiert im 2-GB-tmpfs unter /tmp.
CACHE_BEDARF = 1200 * 1024 * 1024
# Der Pruefvektor der Kompilat-Probe (E2d): eine feste Pseudo-Zufallsfolge, aus der
# jede Stufe ihre Eingabe in ihrer eigenen Form schoepft. Er steht hier als ZAHL, nicht
# als Datei — eine Probe, die erst eine Datei braucht, laeuft im Feld nicht.
PROBE_SAAT = 20260913


# ------------------------------------------------------------------ Kompilieren
def _namen_festpinnen(modell):
    """Jedem Knoten des Graphen einen STABILEN Namen geben, abgeleitet aus seiner Stelle
    in der topologischen Folge. EINE Zeile Wirkung, eine gemessene Ursache dahinter:

    WARUM DAS SEIN MUSS (E2d, 13.09.2026, gemessen). Drei Kompilate dieser Engine
    entstehen, indem an ein von der Platte gelesenes Modell KNOTEN ANGEHAENGT werden
    (`modell_fd` -> lm_n, `modell_p` -> p_n, `modell_r` -> rec_n). Wer einem Knoten
    keinen Namen gibt, bekommt von OpenVINO `<Typ>_<prozessglobaler Zaehler>` —
    `Constant_123204`, `ShapeOf_123210`. Der Zaehler haengt daran, wie viele Knoten der
    PROZESS vorher gebaut hat, und das haengt daran, ob fruehere Kompilate aus dem Cache
    IMPORTIERT (wenige Knoten) oder KOMPILIERT wurden. Der Cache-Schluessel ist ein Hash
    ueber die Serialisierung, und die traegt diese Namen. Gemessen am selben rec_2-Graphen
    in zwei Prozesszustaenden: Gewichte bitgleich (md5 ae2f2559), alle 316 kleinen
    Konstanten wertgleich, NUR die Namen anders (`Constant_123204` gegen
    `Constant_69903`) — und damit ein anderer Schluessel.

    ZWEI SCHAEDEN, beide gemessen:
      * SCHLUESSEL-DRIFT (W2-B19): dieselbe Stufe landet unter immer neuen Namen im
        Cache. Im Rundordner der E2b-Eichung liegen drei r-Blobs mit 138 979 924 Byte
        und einer mit 138 983 732 — 4,4 GB in 68 Blobs waren dasselbe Muster.
      * FALSCHE WERTE: weil der Schluessel driftet, KOMPILIERT der warme Prozess die
        r-Stufe neu statt sie zu importieren, und ein Neu-Kompilat im importlastigen
        Prozesszustand rechnet messbar anders. Fester Pruefvektor durch rec_2:
        emb-md5 e9465a07 (alles selbst kompiliert, dreimal reproduziert) gegen c849940f
        bzw. 1226043b (warmer Cache); ||f|| 3470/3594 gegen 3422/3538 = -1,4 %. In der
        Akte waren das 0,441 -> 0,421 bei den Erkennungs-Scores und bis 6,58 bei
        best_norm — bei UNVERAENDERTEN Detektionen.

    Mit festen Namen ist der Schluessel eine Funktion des GRAPHEN allein: der warme
    Prozess findet sein Kompilat und IMPORTIERT es bitgleich, statt es neu zu rechnen.

    Was das NICHT anfasst: Tensor-Namen (`_benannt`, die Bindung der Remote-Tensoren)
    liegen in einem anderen Namensraum, und die Werte der Konstanten bleiben unberuehrt.
    Namen muessen in OpenVINO nicht eindeutig sein; gebraucht wird nur, dass sie fuer
    denselben Graphen IMMER dieselben sind. -> das Modell (derselbe Verweis)"""
    for i, node in enumerate(modell.get_ordered_ops()):
        node.set_friendly_name(f"k{i:05d}_{node.get_type_name()}")
    return modell


def _kompilieren(core, modell, konfig=None):
    """DIE EINE Stelle, an der ein Graph dieser Engine kompiliert wird.

    Sie existiert, damit das Namens-Festpinnen (s. `_namen_festpinnen`) nicht an neun
    Aufrufstellen stehen muss und keine neue vergessen werden kann: wer hier nicht
    durchgeht, kommt nicht auf die GPU. -> CompiledModel"""
    return core.compile_model(_namen_festpinnen(modell), GERAET, konfig or {})


# ------------------------------------------------------------------ Pruefvektor
def probe_nv12(H, W):
    """Die NV12-Halbbilder des Pruefvektors — RECHNUNG, kein Zufallsgenerator und keine
    Datei: dieselben Bytes auf jeder Maschine, jeder numpy-Fassung und ohne Zugriff auf
    Bestandsdaten. Der Inhalt ist ein schraeges Streifenmuster mit Struktur in beiden
    Achsen; ein Grauwert-Flaechenbild waere als Probe wertlos, weil Faltungen darauf
    nahezu konstant antworten. -> (y [1,H,W,1], uv [1,H/2,W/2,2]) uint8"""
    i = np.arange(H, dtype=np.int32)[:, None]
    j = np.arange(W, dtype=np.int32)[None, :]
    y = (16 + ((i * 7 + j * 13 + ((i * j) >> 6) + PROBE_SAAT) % 220)).astype(np.uint8)
    ih = np.arange(H // 2, dtype=np.int32)[:, None]
    jh = np.arange(W // 2, dtype=np.int32)[None, :]
    u = (16 + ((ih * 11 + jh * 5 + PROBE_SAAT) % 225)).astype(np.uint8)
    v = (16 + ((ih * 3 + jh * 17 + PROBE_SAAT) % 225)).astype(np.uint8)
    return y[None, :, :, None], np.stack([u, v], axis=-1)[None]


def probe_box(W, H):
    """Die feste Pruef-Box im Frame (Anteile der Kanten, dann ganzzahlig wie eine echte
    Detektion). Sie liegt mittig und ist gross genug, dass alle fuenf Ausschnitte
    Bildinhalt sehen statt Polster. -> (x1, y1, x2, y2) int"""
    return (int(0.30 * W), int(0.22 * H), int(0.42 * W), int(0.52 * H))


def probe_kps(box):
    """Fuenf Pruef-Landmarken in der Box, in der Reihenfolge von insightface
    (Auge links, Auge rechts, Nase, Mund links, Mund rechts). Die Anteile sind die
    Lage-Verhaeltnisse eines frontalen Gesichts; gebraucht wird nur, dass sie FEST
    sind. -> [5,2] float32"""
    x1, y1, x2, y2 = (float(v) for v in box)
    w, h = x2 - x1, y2 - y1
    teile = ((0.32, 0.38), (0.68, 0.38), (0.50, 0.58), (0.36, 0.76), (0.64, 0.76))
    return np.array([[x1 + a * w, y1 + b * h] for a, b in teile], np.float32)


# ------------------------------------------------------------------ Decode
def _ffmpeg_nv12(clip, schritt, hw):
    """Die ffmpeg-Kette dieser Engine, EINMAL fuer beide Wege. Auswahl per ffmpeg-select
    VOR dem Download wie decode.FrameIter (decode.py:159-177), aber NV12 statt yuv420p
    und ohne cv2-Umrechnung. `hw=False` ist dieselbe Kette OHNE VAAPI und ohne
    hwdownload — der Software-Rueckfall; sie endet auf demselben `format=nv12` ueber
    demselben Decoder-Bild."""
    # .536 B1a: `-nostdin` — ffmpeg darf den fd 0 seines Elternprozesses nicht
    # pollen. Im Worker ist das die Job-Pipe (s. worker_kern.nv12_strom, dort
    # steht der Byte-Beweis). Aendert nichts am Decoder und nichts an den Pixeln.
    basis = ["ffmpeg", "-nostdin", "-v", "warning"]
    if hw:
        dev = os.environ.get("SUSLIK_HWDEC_DEVICE", "/dev/dri/renderD128")  # decode.py:168
        basis += ["-hwaccel", "vaapi", "-hwaccel_device", dev,
                  "-hwaccel_output_format", "vaapi"]
    rest = "hwdownload,format=nv12" if hw else "format=nv12"
    return basis + ["-i", clip, "-map", "0:v:0",
                    "-vf", f"select='not(mod(n\\,{schritt}))',{rest}",
                    "-fps_mode", "passthrough", "-f", "rawvideo", "-"]


def frames_nv12(clip, W, H, schritt, wache=None):
    """Sample-Frames als (i, y, uv) ueber VAAPI, MIT LAUTEM SOFTWARE-RUECKFALL (E2d).
    Regel und Begruendung stehen EINMAL in worker_kern.nv12_mit_rueckfall; der Byte-Weg
    dahinter (Leser-Thread, Vorlauf, Pipe-Kapazitaet) ist worker_kern.nv12_strom.
    `wache` (E2): dict fuer Kette/rc/decoder_fehler, dazu hwdec_fallback/hwdec_grund."""
    return wk.nv12_mit_rueckfall(_ffmpeg_nv12(clip, schritt, True),
                                 _ffmpeg_nv12(clip, schritt, False),
                                 W, H, schritt, "VAAPI", wache=wache)


# ------------------------------------------------------------------ Graphen
def _c(v):
    return ops.constant(np.float32(v))


def _c_kanal(werte):
    return ops.constant(np.asarray(werte, np.float32).reshape(1, 3, 1, 1))


def _i64(werte):
    return ops.constant(np.asarray(werte, np.int64))


def _benannt(knoten, name):
    """Einem Ergebnis- oder Parameter-Knoten einen TENSOR-Namen geben. Der Name ist der
    einzige Griff, ueber den ein RemoteTensor gebunden werden kann (set_tensor nimmt ihn
    nicht ueber den Port — Probe 12.09.). Vorhandene Namen bleiben erhalten."""
    t = knoten.output(0).get_tensor()
    t.set_names(set(t.get_names()) | {name})
    return knoten


def _nv12_rgb(H, W):
    """Parameter y/uv (uint8) -> RGB-Frame [1,3,H,W] float32, alles im GPU-Graphen."""
    y = ops.parameter([1, H, W, 1], np.uint8, name="y")
    uv = ops.parameter([1, H // 2, W // 2, 2], np.uint8, name="uv")
    rgb = ops.nv12_to_rgb(y, uv)                                   # [1,H,W,3] uint8
    return y, uv, ops.transpose(ops.convert(rgb, "f32"), _i64([0, 3, 1, 2]))


def _einhaengen(modell, node):
    """Den einzigen Eingang eines geladenen Modells durch `node` ersetzen."""
    par = modell.get_parameters()[0]
    for ziel in list(par.output(0).get_target_inputs()):
        ziel.replace_source_output(node.output(0))


def _seiten(modell):
    """(h, w) des Modell-Eingangs [N,3,h,w]."""
    ps = modell.inputs[0].get_partial_shape()
    return ps[2].get_length(), ps[3].get_length()


def graph_pre_det(core, H, W):
    """Graph A (v7): NV12 -> RGB-Vollbild, daraus ZWEI Ausgaenge —
      die neun Detektor-Ausgaenge (Verkleinern, Leinwand, Normieren, det_10g) und
      'rgb', das Vollbild [1,3,H,W] selbst, Eingang der fuenf Ausschnitt-Graphen.
    Bis v2 rechnete jeder Stufen-Graph die Umrechnung noch einmal selbst; hier entsteht
    sie einmal je Frame. Die Rechenreihenfolge ist unveraendert (erst die volle
    Aufloesung, dann Resize), der Detektor-Zweig haengt Knoten fuer Knoten am selben
    Tensor wie in v2 — 'rgb' wird nur zusaetzlich als Ausgang gefuehrt.
    Leinwand und Skala rechnet worker_kern.det_geometrie (backend-frei, EINE Quelle fuer
    beide Engines). -> (kompiliert, (det_w, det_h), det_scale, Zahl der Detektor-Ausgaenge)"""
    (det_w, det_h), (neu_w, neu_h), det_scale = wk.det_geometrie(W, H)
    y, uv, x = _nv12_rgb(H, W)
    r = ops.interpolate(x, _i64([neu_h, neu_w]), "linear_onnx", "sizes",
                        coordinate_transformation_mode="half_pixel", axes=_i64([2, 3]))
    lw = ops.pad(r, _i64([0, 0, 0, 0]), _i64([0, 0, det_h - neu_h, det_w - neu_w]),
                 "constant", _c(0.0))
    m = core.read_model(wk.modell_pfad("det_10g"))
    _einhaengen(m, ops.divide(ops.subtract(lw, _c(wk.DET_MEAN)), _c(wk.DET_STD)))
    det_aus = list(m.get_results())
    # Das Vollbild ZULETZT anhaengen, damit die Detektor-Ausgaenge die Indizes 0..8
    # behalten und die Ausgangs-Reihenfolge die von v2 ist.
    modell = ov.Model(det_aus + [_benannt(ops.result(x), NAME_RGB)], [y, uv], "pre_det_nv12")
    return _kompilieren(core, modell), (det_w, det_h), det_scale, len(det_aus)


def _ausschnitt(x, theta, n, h, w):
    """n Ausschnitte h x w aus dem Frame x [1,3,H,W] mit EINEM GridSample: die
    Gesichter liegen im Gitter uebereinander (der Frame wird je Gesicht nicht
    kopiert). theta [n,2,3] bildet Ausschnitt-Pixel (u, v, 1) auf
    GridSample-Koordinaten ab (align_corners=False)."""
    vv, uu = np.mgrid[0:h, 0:w].astype(np.float32)
    basis = np.stack([uu.ravel(), vv.ravel(), np.ones(h * w, np.float32)], axis=1)[None]
    g = ops.matmul(ops.constant(basis), theta, False, True)            # [n,h*w,2]
    g = ops.reshape(g, _i64([1, n * h, w, 2]), False)
    s = ops.grid_sample(x, g, {"align_corners": False, "mode": "bilinear",
                               "padding_mode": "zeros"})               # [1,3,n*h,w]
    s = ops.reshape(s, _i64([3, n, h, w]), False)
    return ops.transpose(s, _i64([1, 0, 2, 3]))                         # [n,3,h,w]


def _u8_rundung(s):
    """Den fertig getasteten Ausschnitt auf GANZE Graustufen zurueckholen, bevor die
    Stufen-Normierung ihn anfasst (f32-Warp-Fix, 14.09.2026).

    WARUM (gemessen, runs/zerlegung_klein_20260914/): der alte Weg schneidet mit
    cv2.warpAffine AUF DEM uint8-FRAME (insightface face_align.norm_crop) — sein
    Ergebnis ist per Konstruktion ganzzahlig. Der GPU-Warp tastet in Gleitkomma und
    gibt Zwischenwerte heraus; das allein ist schon ein Unterschied zur Messbasis
    aller Referenzen. In der Zerlegung stand diese Quantisierung als eigene Achse
    (Spalte 'u8' der Anteils-Tabelle, X0 gegen X0f): |d| bis 0,008 Score-Punkte, und
    an den Heilwegen abgelesen halbiert sie den Rest — CPU-Warp in f32 ergab gegen die
    CPU-Referenz mittleres |d| 0,0031 (F2), derselbe Warp mit uint8-Rundung 0,0015
    (F2c). Sie gehoert deshalb zum Fix dazu und nicht nur die Praezision.

    WO GENAU: nach dem GridSample, VOR der Normierung. Danach waere sie sinnlos (die
    Normierung verlaesst die 0..255-Skala), davor unmoeglich (der Frame IST schon
    ganzzahlig, gerundet werden muessen die interpolierten Zwischenwerte).

    floor(x + 0,5) statt einer Round-Operation, und zwar dieselbe Zeile wie in `_grau`:
    das ist die Rundung, die OpenCV in seinem Festkomma-Pfad macht (CV_DESCALE — halbe
    Einheit dazu, dann abschneiden), und sie ist in beiden Engines Knoten fuer Knoten
    dieselbe. ONNX-`Round` waere kaufmaennisch-gerade und damit eine ZWEITE Regel.

    Ein Klemmen auf 0..255 braucht es nicht: die Quelle ist ganzzahlig in 0..255, die
    bilineare Gewichtung ist konvex, und `padding_mode=zeros` haelt den Rand bei 0.
    -> der Ausschnitt, ganzzahlig"""
    return ops.floor(ops.add(s, _c(0.5)))


def _batch_frei(modell):
    """Reshape-Ziele mit fest eingebauter Batch 1 auf „Batch vom Eingang
    uebernehmen" umstellen (0 mit special_zero). fiqa_edgenext hat 21 davon;
    ohne die Umstellung scheitert reshape([n, ...]). Probe 11.09. auf der iGPU:
    4 Eingaben gebuendelt gegen einzeln, max |d| 4,5e-5. -> Anzahl umgestellt"""
    n = 0
    for node in modell.get_ordered_ops():
        if node.get_type_name() != "Reshape":
            continue
        src = node.input_value(1).get_node()
        if src.get_type_name() != "Constant":
            continue
        v = np.array(src.get_data()).astype(np.int64).copy()
        if v.size and v[0] == 1:
            v[0] = 0
            neu = ops.reshape(node.input_value(0), ops.constant(v), True)
            for ziel in list(node.output(0).get_target_inputs()):
                ziel.replace_source_output(neu.output(0))
            n += 1
    return n


def _norm_bauer(vorschrift):
    """Die Normierung EINER Stufe als OpenVINO-Knoten, aus der Vorschrift des Kerns
    (worker_kern.norm_vorschriften/norm_schritte). Bis E1 stand sie als _norm_e/_norm_t/
    _norm_p/_norm_r/_norm_lm fuenfmal hier und noch einmal in der CUDA-Fassung; die
    KNOTENFOLGE ist unveraendert — /255, Kanalfolge, -mean, /std, und ein Posten entsteht
    nur, wenn die Vorschrift ihn verlangt. Ein Skalar bleibt ein Skalar, ein 3er-Feld ein
    [1,3,1,1]-Block (genau wie zuvor, damit die Graphen dieselben bleiben)."""
    schritte = wk.norm_schritte(vorschrift)

    def konst(wert):
        a = np.asarray(wert, np.float32)
        return _c_kanal(a) if a.size == 3 else _c(float(a))

    def norm(s):
        for art, wert in schritte:
            if art == "bgr":
                s = ops.gather(s, _i64([2, 1, 0]), _i64(1))
            elif art == "sub":
                s = ops.subtract(s, konst(wert))
            else:
                s = ops.divide(s, konst(wert))
        return s
    return norm


def graph_crop(core, H, W, n, seiten, norm, marke):
    """Ausschnitt-Graph EINER Stufe (v7): das RGB-Vollbild als Eingang, n Ausschnitte
    h x w per EINEM GridSample, uint8-Rundung, danach die Normierung der Stufe. Ausgang
    'crop' [n,3,h,w] — ein Geraete-Tensor, den das Modell-Kompilat der Stufe liest.
    Das ist der einzige Graph-Teil, der die Clip-Geometrie kennt; deshalb bleibt er
    je Geometrie, waehrend das Modell dahinter prozessweit lebt.

    f32 STATT DER GPU-VORGABE fp16 (f32-Warp-Fix, 14.09.2026) — gemessen, nicht
    vorsichtshalber. Die Zerlegung des Score-Einbruchs bei kleinen Ferngesichtern
    (runs/zerlegung_klein_20260914/) hat den RECHEN-Rest zu rund 84 % an genau diesem
    GridSample festgemacht: in fp16 landen die Abtastpunkte bis 0,82 px neben ihrem
    Ziel (mit f32-Hinweis 0,0001 px), der Ausschnitt wird sichtbar verwaschen, und die
    Crop-Pixel weichen im Mittel bis 4,1 Graustufen ab (Spalte 'Warp fp16 vs cv2',
    Groesstwert 78,8) — mit f32 bleiben davon 0,0014 bzw. 0,049. Gegen die
    CPU-fp32-Referenz sank der mittlere Abstand der sieben Schiedsrichter-Faelle von
    0,0069 (fp16) auf 0,0030 Score-Punkte (Heilweg F1).

    DER HINWEIS IST HIER GRATIS, auch das gemessen: f32 war in 8 von 8 Faellen
    SCHNELLER als fp16 — Ausschnitt+Normierung 18,91 gegen 19,71 ms je Aufruf, der
    Warp allein 9,83 gegen 11,13 ms (kosten.txt desselben Rundordners). Die halbe
    Mantisse kauft auf dieser iGPU bei GridSample nichts ein.

    Er steht bewusst je AUSSCHNITT-Kompilat und nicht am ganzen Lauf: das Modell
    dahinter (e/t/p/r) bleibt in der Vorgabe der GPU, geaendert ist allein der
    Abtast-Schritt davor. -> kompiliert"""
    h, w = seiten
    rgb = _benannt(ops.parameter([1, 3, H, W], np.float32, name=NAME_RGB), NAME_RGB)
    th = _benannt(ops.parameter([n, 2, 3], np.float32, name="th"), "th")
    s = _u8_rundung(_ausschnitt(rgb, th, n, h, w))
    modell = ov.Model([_benannt(ops.result(norm(s)), NAME_CROP)], [rgb, th],
                      f"crop_{marke}_{n}")
    return _kompilieren(core, modell, {"INFERENCE_PRECISION_HINT": "f32"})


def _grau(s):
    """RGB [n,3,h,w] -> Graustufen [n,1,h,w] im OpenCV-Festkomma, mit derselben
    Rundung wie cv2.cvtColor(BGR2GRAY) (CV_DESCALE: +halbe Einheit, dann abschneiden)."""
    w = np.asarray(wk.GRAU_W, np.float32) / float(1 << wk.GRAU_SHIFT)
    g = ops.reduce_sum(ops.multiply(s, ops.constant(w.reshape(1, 3, 1, 1))), _i64([1]), True)
    return ops.floor(ops.add(g, _c(0.5)))


def _lap_summen(s, n, C, mu, mv):
    """Laplace ueber die Leinwand und daraus Summe und Summe der Quadrate ueber die
    gueltige Region. Der 3x3-Kern ohne Polster liefert [n,1,C-2,C-2]; Ausgabezeile i
    ist Leinwand-Zeile i+1, und genau dort liegt die erste Crop-Zeile (der Spiegelring
    sitzt auf Leinwand-Zeile 0). Die Region wird deshalb mit einem Praefix-Masken-
    Produkt gewaehlt: mu [n,C-2,1] Zeilen, mv [n,1,C-2] Spalten. -> (sL [n], sL2 [n])"""
    k = np.asarray(wk.LAPLACE_KERN, np.float32).reshape(1, 1, 3, 3)
    lap = ops.convolution(_grau(s), ops.constant(k), [1, 1], [0, 0], [0, 0], [1, 1])
    lap = ops.reshape(lap, _i64([n, C - 2, C - 2]), False)
    maske = ops.multiply(mu, mv)
    return (ops.reduce_sum(ops.multiply(lap, maske), _i64([1, 2])),
            ops.reduce_sum(ops.multiply(ops.multiply(lap, lap), maske), _i64([1, 2])))


def graph_crop_fd(core, H, W, n, seiten, norm, C=None):
    """Ausschnitt-Graph der fd-Stufe (v8) — EIN Aufruf, zwei Zuschnitte aus demselben
    RGB-Vollbild:
      'crop'            der Landmark-Ausschnitt [n,3,192,192] fuer 1k3d68 (Geraete-
                        Tensor wie bei e/t/p/r, affin per GridSample aus theta)
      's_lap'/'s_lap2'  die Laplace-Summen des ENGEN Crops, gerechnet auf einer
                        Leinwand CxC in NATIVER Pixelskala
    Die Leinwand wird per GATHER gezogen (Spalten mit jx, dann Zeilen mit iy) statt
    getastet: damit sind die Indizes ein EINGANG, und der Spiegel von
    BORDER_REFLECT_101 steckt in ihnen (worker_kern.leinwand_zug). Nebenbei ist es ein
    reiner Speicherzug ohne Interpolation.
    f32 statt der fp16-Vorgabe ist Pflicht, nicht Geschmack: L^2 laeuft bis rund 1e6 und
    liegt damit ausserhalb des fp16-Bereichs (65504) — in fp16 waere die Varianz Schrott.
    Seit dem f32-Warp-Fix (14.09.2026) ist derselbe Hinweis zugleich der, den e/t/p/r in
    `graph_crop` tragen; diese Stufe hatte ihn nur frueher und aus anderem Grund.
    Die uint8-Rundung des Landmark-Ausschnitts kommt mit dem Fix dazu (`_u8_rundung`):
    die fd-Rechnung tastet aus DEMSELBEN Warp, ihre Eingangs-Bytes sollen deshalb
    dieselbe Quantisierung haben wie die der uebrigen Stufen. Die Laplace-Leinwand
    daneben bleibt unberuehrt — sie wird GEZOGEN (Gather), nicht getastet, und ist
    damit ohnehin ganzzahlig.
    -> kompiliert"""
    C = wk.LEINWAND if C is None else C
    h, w = seiten
    rgb = _benannt(ops.parameter([1, 3, H, W], np.float32, name=NAME_RGB), NAME_RGB)
    th = _benannt(ops.parameter([n, 2, 3], np.float32, name="th"), "th")
    jx = _benannt(ops.parameter([n, C], np.int32, name="jx"), "jx")
    iy = _benannt(ops.parameter([n, C], np.int32, name="iy"), "iy")
    mu = _benannt(ops.parameter([n, C - 2, 1], np.float32, name="mu"), "mu")
    mv = _benannt(ops.parameter([n, 1, C - 2], np.float32, name="mv"), "mv")
    crop = _benannt(ops.result(norm(_u8_rundung(_ausschnitt(rgb, th, n, h, w)))),
                    NAME_CROP)
    teile = []
    for k in range(n):                                   # n ist die feste Aufrufbreite
        jk = ops.squeeze(ops.slice(jx, _i64([k]), _i64([k + 1]), _i64([1]), _i64([0])),
                         _i64([0]))
        ik = ops.squeeze(ops.slice(iy, _i64([k]), _i64([k + 1]), _i64([1]), _i64([0])),
                         _i64([0]))
        sp = ops.gather(rgb, jk, _i64(3))                # [1,3,H,C]  Spalten zuerst:
        teile.append(ops.gather(sp, ik, _i64(2)))        # [1,3,C,C]  weniger Zwischenwerte
    lein = ops.concat(teile, 0) if n > 1 else teile[0]
    sL, sL2 = _lap_summen(lein, n, C, mu, mv)
    modell = ov.Model([crop, _benannt(ops.result(sL), NAME_SL),
                       _benannt(ops.result(sL2), NAME_SL2)],
                      [rgb, th, jx, iy, mu, mv], f"crop_fd_{n}")
    return _kompilieren(core, modell, {"INFERENCE_PRECISION_HINT": "f32"})


def modell_fd(core, n, pfad, punkte):
    """Modell-Kompilat der fd-Stufe: 1k3d68 auf dem Landmark-Ausschnitt. Der Ausgang
    'fc1' traegt 3309 Zahlen = 1103 Punkte x 3; gebraucht werden die LETZTEN `punkte`
    (insightface landmark.Landmark.get: pred[-lmk_num:]). Der Schnitt liegt im Graphen,
    damit nur 68x3 statt 1103x3 Zahlen zur CPU kommen.

    GRENZEN DES SCHNITTS AUSGERECHNET, NICHT ANGEDEUTET: die erste Fassung schrieb das
    Ende als 2**31-1 („bis zum Schluss"). Damit rechnete der GPU-Treiber falsch — und
    zwar NICHT im eigenen Ausgang, sondern in den Scores der Erkennungs-Stufe, die
    danach lief (kchj4k 0,41 statt 0,711; Bisektion 13.09.: fd-Stufe ohne 1k3d68-Aufruf
    lieferte wieder die v7-Werte, mit Aufruf nicht). Die Punktzahl steht in der
    Modell-Form, also wird sie dort gelesen.

    GEMESSENE EIGENSCHAFT DIESER STUFE (E2c, 13.09.2026) — festgehalten, damit sie niemand
    neu suchen muss; GEAENDERT IST HIER NICHTS, die Stufe rechnet wie bisher in der
    GPU-Vorgabe (fp16). Was hinter dem Modell kommt, ist schlecht konditioniert: aus den
    68 Punkten schaetzt insightface eine 3D-Affine gegen die mittlere Form und zieht daraus
    die Winkel (estimate_affine_matrix_3d23d -> P2sRt -> matrix2angle), kleine Punktfehler
    werden dabei zu GRADEN. An 43 Katalog-Gesichtern mit IDENTISCHEN Zuschnitt-Bytes und
    derselben Winkel-Funktion (worker_kern.fd_winkel) auf beiden Seiten, gegen dasselbe
    ONNX auf onnxruntime/CPU (der Weg von face_audit):
        GPU fp16 (Vorgabe):  Punkte max|d| 0,1054  -> Winkel max 12,43 Grad, median 0,28
        GPU mit f32-Hinweis: Punkte max|d| 0,000012 -> Winkel max 0,001 Grad
    Die Stufe allein waere mit f32 also exakt, und sie bliebe dabei auf der GPU. ENDE ZU
    ENDE bringt das aber wenig, weil der Zuschnitt davor aus der DETEKTION kommt und die
    ebenfalls fp16 rechnet: ueber 248 Katalogbilder sank der Groesstwert nur von 17,2 auf
    7,9 Grad, p99 (5,17 -> 5,21) und Median (0,40) blieben. Preis: fd 1,82 -> 3,99 ms je
    Aufruf; die Detektion mitzuziehen kostet 11,28 -> 31,01 ms je Frame bei 1280x736
    (~2,75x auf der teuersten Stufe). Urteilswirkung im Bestand: 0 von 248 S-Kipper an
    s_winkel_max 30. Die Abwaegung gehoert damit dem User, nicht dieser Funktion. -> kompiliert"""
    m = core.read_model(pfad)
    _batch_frei(m)
    m.reshape([n, 3, *_seiten(m)])
    _benannt(m.get_parameters()[0], NAME_CROP)
    fc1 = m.get_results()[0].input_value(0)                                # [n,3309]
    gesamt = fc1.get_partial_shape()[1].get_length() // 3                  # 1103 Punkte
    alle = ops.reshape(fc1, _i64([n, gesamt, 3]), False)                   # [n,1103,3]
    letzte = ops.slice(alle, _i64([gesamt - punkte]), _i64([gesamt]), _i64([1]), _i64([1]))
    return _kompilieren(core, ov.Model([ops.result(letzte)], m.get_parameters(),
                                       f"lm_{n}"))


def modell_e(core, n, pfad):
    """Modell-Kompilat der Stufe e: Efficient-FIQA auf dem normierten Ausschnitt."""
    m = core.read_model(pfad)
    _batch_frei(m)
    m.reshape([n, 3, *_seiten(m)])
    _benannt(m.get_parameters()[0], NAME_CROP)
    return _kompilieren(core, m)


def modell_t(core, n, pfad):
    """Modell-Kompilat der Stufe t: eDifFIQA-T auf dem normierten align112-Ausschnitt."""
    m = core.read_model(pfad)
    m.reshape([n, 3, *_seiten(m)])
    _benannt(m.get_parameters()[0], NAME_CROP)
    return _kompilieren(core, m)


def modell_p(core, n, pfad):
    """Modell-Kompilat der Stufe p: RTMPose und daraus der Kopf-Score, auf der GPU.
    pose_wache.skelett: Score je Punkt = 0,5 * (max simcc_x + max simcc_y), Kopf =
    Maximum ueber KOPF_IDX (wie core/ernte.pose_kopf). -> kompiliert"""
    pw, ph = wk.pose_wache.INPUT_SIZE
    m = core.read_model(pfad)
    m.reshape([n, 3, ph, pw])
    _benannt(m.get_parameters()[0], NAME_CROP)
    aus = {r.input_value(0).get_any_name(): r.input_value(0) for r in m.get_results()}
    kp = ops.multiply(ops.add(ops.reduce_max(aus["simcc_x"], _i64([2])),
                              ops.reduce_max(aus["simcc_y"], _i64([2]))), _c(0.5))
    kopf = ops.reduce_max(ops.gather(kp, _i64(wk.pose_wache.KOPF_IDX), _i64(1)), _i64([1]))
    return _kompilieren(core, ov.Model([ops.result(kopf)], m.get_parameters(),
                                       f"p_{n}"))


def modell_r(core, n, pfad):
    """Modell-Kompilat der Erkennungs-Stufe: das konfigurierte Recognition-Modell
    (face_audit.aktuelles_modell) auf dem normierten norm_crop, Embedding L2-normiert
    wie face_audit._rec_infer. Zur CPU kommen [n, 512] und [n].

    E1 (Konzept §1c): Die Referenz-Matrix ist RAUS. Bis v8 hingen hier MatMul, Reshape
    und ReduceMax gegen eine Graph-Konstante mit allen Referenzen — jede Referenz-
    Aenderung haette damit ein Rekompilat und einen Prozess-Neustart verlangt (Lernlauf:
    15 Anker-Gruppen). Ausgang 0 ist jetzt das L2-normierte Embedding selbst; Scores und
    Maximum je Person rechnet worker_kern.scores_rechnen auf der CPU.

    Ausgang 1 ist die Feature-Norm ||f|| (v2). Als Guetemass ist sie belegt besser als die
    Laplace-Schaerfe des alten Workers (eigene Messung face_audit.NormMass AUC 0,731,
    verify_data/messungen/qualitaetsmass_20260820.json; ISO/IEC 29794-5 nimmt in der
    Referenzimplementierung OFIQ die MagFace-Magnitude als Gesamtguetewert).

    WO ||f|| WIRKLICH LIEGT (E2c, 13.09.2026 — gemessener Fehler, korrigiert). Bis hierher
    stand an Ausgang 1 der Betrag des GRAPH-AUSGANGS. Der adaface-Kopf endet aber selbst auf
      f -> ReduceL2 -> Div
    (am Modell abgelesen: der Erzeuger des Ergebnisses ist ein `Divide`, sein Eingang 1 die
    `ReduceL2`), liefert also bereits den normierten Vektor — sein Betrag ist per Konstruktion
    1. Gemessen kam an Ausgang 1 dann auch 1,0003 statt der Skala 15-30, auf der die Latten
    des Hauses geeicht sind (Sieb n=20,0 · vorrat_norm_min 22,0 · katalog_norm_min 24,0);
    in E2c siebte das 29 von 29 Ernte-Kandidaten aus. `face_audit.NormMass` holt denselben
    Wert seit jeher richtig, naemlich am Div-EINGANG (`_graph_bytes`: der eine Div-Knoten vor
    dem Graph-Ausgang, dessen input[0] f ist). Genommen wird hier der DIVISOR dieses Knotens
    — dieselbe Groesse, ohne sie ein zweites Mal zu rechnen.

    AUSGANG 0 BLEIBT, WIE ER WAR, und das ist Absicht: `face_audit` liefert als
    `normed_embedding` den Graph-Ausgang geteilt durch SEINEN eigenen Betrag (insightface
    Face.normed_embedding auf _rec_infer). Weil der Graph-Ausgang nicht exakt Laenge 1 hat
    (gemessen 1,0003), ist diese zweite Teilung kein Nulleffekt — sie ist der Bestand. Wer
    hier "vereinfacht" und den Graph-Ausgang durchreicht, verschiebt jedes Embedding um
    ~3e-04 gegen das ganze Haus. Geaendert wird deshalb NUR Ausgang 1.

    Hat ein fremder Erkennungskopf keine Div-Naht, bleibt es beim selbst gerechneten Betrag —
    dort IST er die Feature-Norm, weil der Kopf dann unnormiert ausgibt. -> kompiliert"""
    m = core.read_model(pfad)
    m.reshape([n, 3, *_seiten(m)])
    _benannt(m.get_parameters()[0], NAME_CROP)
    emb = m.get_results()[0].input_value(0)                               # [n, 512]
    betrag = ops.add(ops.sqrt(ops.reduce_sum(ops.multiply(emb, emb), _i64([1]), True)),
                     _c(1e-9))
    fertig = ops.divide(emb, betrag)                                       # [n, 512]
    erzeuger = emb.get_node()
    # Der Divisor des Modells selbst = ||f||; sonst (unnormierter Kopf) der eigene Betrag.
    quelle = (erzeuger.input_value(1) if erzeuger.get_type_name() == "Divide"
              else betrag)
    norm = ops.reshape(quelle, _i64([n]), False)                           # [n]
    modell = ov.Model([ops.result(fertig), ops.result(norm)], m.get_parameters(),
                      f"rec_{n}")
    return _kompilieren(core, modell)


# ------------------------------------------------------------------ Modelle prozessweit
class ModellBestand:
    """Die aufloesungsUNABHAENGIGEN Modell-Kompilate, EINMAL je Prozess (v7).

    Was hier liegt, kennt keine Frame-Form: die Eingangsformen kommen aus den
    Modell-Dateien selbst bzw. aus pose_wache.INPUT_SIZE. Geometrie-Abhaengig ist nur der
    Ausschnitt davor, und der bleibt deshalb bei der Geometrie.

    Gebaut wird FAUL, je Stufe beim ersten Bedarf — bei EINER Geometrie entsteht damit
    jedes Kompilat an genau der Stelle, an der v2 es gebaut haette.

    E1: der Bestand kennt die Referenzen NICHT mehr (Matmul raus, modell_r). Die Wache
    erk_pruefen entfaellt damit ersatzlos — sie schuetzte die Graph-Konstante, die es
    nicht mehr gibt."""

    def __init__(self, core):
        self.core = core
        self.spec = wk.rec_spec()
        self.pfade = wk.vorgabe_pfade(self.spec)
        self.norm_vorschrift = wk.norm_vorschriften(self.spec)
        # Die Crop-Seiten je Stufe kommen aus den Modell-Dateien, nicht aus der
        # Clip-Geometrie — genau deshalb gehoeren die Modelle hierher. Die Geometrie
        # uebernimmt sie unveraendert (Ausschnitt-Graphen und Affin-Matrizen).
        pw, ph = wk.pose_wache.INPUT_SIZE
        self.seiten = {"p": (ph, pw)}
        for k in (wk.FD, "e", "t", "r"):
            self.seiten[k] = _seiten(core.read_model(self.pfade[k]))
        # Die Punktzahl der Pose kommt aus der mittleren Form, an der sie geschaetzt wird
        # (68), nicht aus einer Zahl im Code.
        self.lm_punkte = len(wk.mean_lmk())
        self.norm = {k: _norm_bauer(self.norm_vorschrift[k]) for k in wk.STUFEN}
        self._bau = {
            wk.FD: lambda n: modell_fd(core, n, self.pfade[wk.FD], self.lm_punkte),
            "e": lambda n: modell_e(core, n, self.pfade["e"]),
            "t": lambda n: modell_t(core, n, self.pfade["t"]),
            "p": lambda n: modell_p(core, n, self.pfade["p"]),
            "r": lambda n: modell_r(core, n, self.pfade["r"])}
        self._kompilate = {}
        self._schloss = threading.Lock()
        self.bau_s = 0.0                                  # Summe der geteilten Bauzeit

    def kompilat(self, k, n):
        """Das GETEILTE Kompilat der Stufe k fuer Breite n: beim ersten Bedarf gebaut,
        danach dasselbe Objekt fuer jede weitere Geometrie und jeden Thread."""
        with self._schloss:
            c = self._kompilate.get((k, n))
            if c is None:
                t0 = time.monotonic()
                c = self._kompilate[(k, n)] = self._bau[k](n)
                self.bau_s += time.monotonic() - t0
            return c

    def kompilate_zaehlen(self):
        """Wie viele Kompilate der Bestand haelt — gezaehlt, nicht gerechnet."""
        return len(self._kompilate)


# ------------------------------------------------------------------ Lauf
class Satz:
    """Alles, was EIN Rechenstrang fuer sich braucht (v7): je Kompilat eine
    InferRequest und die Geraete-Tensoren, ueber die die Graphen aneinanderhaengen.

    Warum je Strang: ein CompiledModel ist thread-sicher, eine InferRequest NICHT —
    das ist das native OpenVINO-Muster (mehrere Anfragen auf demselben Kompilat).
    Zwei Threads mit EINER Anfrage wuerden sich den Frame unter der laufenden
    Rechnung austauschen, und der Fehler faellt nicht auf, er verschiebt nur Werte.

    Die Tensoren: 'rgb' (das Vollbild, 99,5 MB bei 4K) ist Ausgang der Vorverarbeitung
    und Eingang aller fuenf Ausschnitt-Graphen; je Stufe haengt dahinter ein kleiner
    'crop'-Tensor zwischen Ausschnitt und Modell. Beide bleiben auf der GPU, die CPU
    sieht sie nie."""

    def __init__(self, g):
        self.g = g
        self.rgb = g.ctx.create_tensor(ov.Type.f32, ov.Shape([1, 3, g.H, g.W]), {})
        self.det_req = g.pre.create_infer_request()
        self.det_req.set_tensor(NAME_RGB, self.rgb)
        # Die EINGANGS-Tensoren gehoeren der Anfrage und bleiben liegen; je Frame wird
        # nur noch hineingeschrieben. Warum nicht je Aufruf ein frischer Tensor bzw. das
        # numpy-Array direkt: start_async(dict) TEILT in der Python-Bindung den Speicher
        # des uebergebenen Arrays (anders als infer(), das kopiert). Der Frame-Puffer
        # gehoert aber dem Decoder-Leser und wird am Event-Ende frei — die Anfrage haelt
        # ihn bis zum naechsten Aufruf gebunden. GEMESSEN 12.09. genau so kaputtgegangen:
        # erster Frame des ZWEITEN Events, "[GPU] clFinish, error code: -5
        # CL_OUT_OF_RESOURCES" (Beleg runs/intel_v7_20260912/v7_a1/lauf.log, 22:43), und
        # davor einmal als stiller Haenger. Eine Kopie in einen bleibenden Tensor ist
        # dieselbe Datenbewegung, die infer() ohnehin macht, nur mit klarer Besitzlage.
        self.y_t = self.det_req.get_tensor("y")
        self.uv_t = self.det_req.get_tensor("uv")
        self.stufen = {}
        for k in wk.STUFEN:
            h, w = g.seiten[k]
            zwischen = g.ctx.create_tensor(
                ov.Type.f32, ov.Shape([wk.AUFRUF_BREITE, 3, h, w]), {})
            c_req = g.crop[k].create_infer_request()
            c_req.set_tensor(NAME_RGB, self.rgb)
            c_req.set_tensor(NAME_CROP, zwischen)
            m_req = g.modell[k].create_infer_request()
            m_req.set_tensor(NAME_CROP, zwischen)
            self.stufen[k] = (c_req, m_req, zwischen, len(g.modell[k].outputs),
                              c_req.get_tensor("th"))
        # Die fd-Stufe (v8) hat vier Eingaenge mehr — die Indizes und Masken der
        # Laplace-Leinwand — und ihre beiden Zahlen-Ausgaenge liegen am AUSSCHNITT-Graphen,
        # nicht am Modell. Sie stehen hier einmal, damit der Lauf nur noch hineinschreibt.
        fd_c = self.stufen[wk.FD][0]
        self.fd_ein = tuple(fd_c.get_tensor(t) for t in ("jx", "iy", "mu", "mv"))

    def det(self, y, uv):
        """Vorverarbeitung + Detektor fuer EINEN Frame. Das RGB-Vollbild bleibt im
        Geraete-Tensor liegen, die Ausschnitt-Graphen lesen es dort.
        start_async/wait statt infer(): der Remote-Ausgang laesst sich in Python nicht
        als numpy holen (Probe 12.09.). -> die neun Detektor-Ausgaenge"""
        np.copyto(self.y_t.data, y)
        np.copyto(self.uv_t.data, uv)
        self.det_req.start_async()
        self.det_req.wait()
        return [self.det_req.get_output_tensor(i).data for i in range(self.g.det_n)]

    def _ruf(self, k, thetas):
        """EIN Aufruf einer Stufe mit GENAU AUFRUF_BREITE Gesichtern: Ausschnitt auf
        der GPU, dann das prozessweite Modell auf demselben Geraete-Tensor.
        -> je Gesicht ein Tupel seiner Ausgabezeilen"""
        c_req, m_req, _zw, n_aus, th_t = self.stufen[k]
        np.copyto(th_t.data, np.stack(thetas))
        c_req.start_async()                              # Ausgang 'crop' ist ein
        c_req.wait()                                     # Geraete-Tensor
        m_req.start_async()
        m_req.wait()
        werte = [m_req.get_output_tensor(j).data for j in range(n_aus)]
        # Kopie: die Ausgaenge sind Sichten in die Tensoren der Anfrage, und der
        # naechste Aufruf ueberschreibt sie.
        return [tuple(np.array(w[i]) for w in werte) for i in range(len(thetas))]

    def stufe(self, k, thetas):
        """Eine Stufe fuer beliebig viele Gesichter, in Aufrufen FESTER Breite (v7).
        Der letzte Rest wird durch Wiederholen des letzten Gesichts aufgefuellt, sein
        Doppel verworfen — Zeile fuer Zeile das Polster-Muster, das v1 fuer die
        Buendelstufen benutzt hat, nur mit EINER Breite statt einer Stufenleiter.
        -> je Gesicht ein Tupel seiner Ausgabezeilen"""
        aus = []
        for start in range(0, len(thetas), wk.AUFRUF_BREITE):
            teil = thetas[start:start + wk.AUFRUF_BREITE]
            voll = teil + [teil[-1]] * (wk.AUFRUF_BREITE - len(teil))
            aus.extend(self._ruf(k, voll)[:len(teil)])
        return aus

    def _ruf_fd(self, thetas, zuege):
        """EIN Aufruf der fd-Stufe mit GENAU AUFRUF_BREITE Gesichtern: Landmark-Ausschnitt
        und Laplace-Leinwand in einem Graphen, danach 1k3d68 auf demselben Geraete-Tensor.
        Ausgang 0 des Ausschnitt-Graphen ist der Geraete-Tensor und wird NIE gelesen (in
        Python nicht als numpy holbar) — gelesen werden nur s_lap/s_lap2.
        -> je Gesicht (Punkte [68,3], sL, sL2)"""
        c_req, m_req, _zw, _n_aus, th_t = self.stufen[wk.FD]
        jx_t, iy_t, mu_t, mv_t = self.fd_ein
        np.copyto(th_t.data, np.stack(thetas))
        np.copyto(jx_t.data, np.stack([z[0] for z in zuege]))
        np.copyto(iy_t.data, np.stack([z[1] for z in zuege]))
        np.copyto(mu_t.data, np.stack([z[2] for z in zuege]))
        np.copyto(mv_t.data, np.stack([z[3] for z in zuege]))
        c_req.start_async()
        c_req.wait()
        sL = np.array(c_req.get_tensor(NAME_SL).data)
        sL2 = np.array(c_req.get_tensor(NAME_SL2).data)
        m_req.start_async()
        m_req.wait()
        pts = m_req.get_output_tensor(0).data
        return [(np.array(pts[i]), float(sL[i]), float(sL2[i])) for i in range(len(thetas))]

    def stufe_fd(self, thetas, zuege):
        """Die fd-Stufe fuer beliebig viele Gesichter, in Aufrufen fester Breite — dasselbe
        Polster-Muster wie stufe()."""
        aus = []
        for start in range(0, len(thetas), wk.AUFRUF_BREITE):
            b = wk.AUFRUF_BREITE
            t_teil, z_teil = thetas[start:start + b], zuege[start:start + b]
            fehlt = b - len(t_teil)
            aus.extend(self._ruf_fd(t_teil + [t_teil[-1]] * fehlt,
                                    z_teil + [z_teil[-1]] * fehlt)[:len(t_teil)])
        return aus

    def warm(self):
        """Jedes Kompilat einmal rechnen, bevor die Uhr laeuft — mit genau den Formen,
        die der Lauf ruft (eine je Stufe, seit der festen Aufrufbreite)."""
        y0 = np.zeros((1, self.g.H, self.g.W, 1), np.uint8)
        uv0 = np.full((1, self.g.H // 2, self.g.W // 2, 2), 128, np.uint8)
        self.det(y0, uv0)
        th0 = np.array([[1, 0, 0], [0, 1, 0]], np.float32)
        for k in wk.KASKADE:
            self._ruf(k, [th0] * wk.AUFRUF_BREITE)
        zug0 = wk.leinwand_zug([0, 0, wk.LEINWAND - 2, wk.LEINWAND - 2], self.g.W, self.g.H)
        self._ruf_fd([th0] * wk.AUFRUF_BREITE, [zug0] * wk.AUFRUF_BREITE)

    def probe(self, roh=False):
        """DIE KOMPILAT-PROBE (E2d): ein FESTER Pruefvektor durch ALLE Stufen dieses
        Satzes, Stufe fuer Stufe mit Fingerabdruck.

        WOZU. Am 13.09. hat ein Lauf ueber einen fremd beschriebenen Kompilat-Cache die
        ERKENNUNG falsch gerechnet, waehrend Detektionen, Frames und Guete-Werte
        unauffaellig blieben: Score 0,441 -> 0,421 (in der E2b-Eichung bis 0,073), und
        NICHTS im Lauf sagte etwas. Genau diese Klasse — „das geladene Kompilat rechnet
        anders als das gemessene" — darf nie wieder still sein. Der Pruefvektor haengt
        NICHT an Bildern, Clips oder Referenzen: er entsteht aus PROBE_SAAT und der
        Geometrie, ist also auf jeder Maschine derselbe.

        WAS SIE NICHT KANN, benannt: sie weiss nicht, welcher Wert RICHTIG ist. Sie
        liefert einen Fingerabdruck; die Aussage „gleich wie beim Bau" macht erst der
        Vergleich gegen die Eichmarke (worker_dienst). Auf anderer Hardware, anderem
        Treiber oder anderer OpenVINO-Fassung sind andere Zahlen richtig — deshalb
        traegt die Eichmarke ihr Umfeld mit sich.
        -> {stufe: md5 der Ausgabe-Bytes, 'r_norm': die zwei Feature-Normen}"""
        import hashlib                                      # noqa: PLC0415
        g = self.g
        y, uv = probe_nv12(g.H, g.W)
        box = probe_box(g.W, g.H)
        kps = probe_kps(box)
        aus = {}
        d = self.det(y, uv)
        aus["det"] = hashlib.md5(b"".join(np.ascontiguousarray(x, np.float32).tobytes()
                                          for x in d)).hexdigest()[:12]
        th = {"e": wk.theta_e(box, g.W, g.H, g.seiten["e"], g.nm),
              "t": wk.theta_t(kps, g.seiten["t"][0], g.nm),
              "p": wk.theta_p(box, g.W, g.H, g.nm),
              "r": wk.theta_t(kps, g.seiten["r"][0], g.nm)}
        for k in wk.KASKADE:
            werte = self._ruf(k, [th[k]] * wk.AUFRUF_BREITE)
            aus[k] = hashlib.md5(b"".join(np.ascontiguousarray(v, np.float32).tobytes()
                                          for zeile in werte for v in zeile)).hexdigest()[:12]
            if k == "r":
                # Die Feature-Norm als ZAHL dazu: sie ist die Groesse, an der die
                # Verschiebung vom 13.09. am deutlichsten hing (best_norm bis 6,58),
                # und eine Zahl liest ein Mensch, einen Hash nicht.
                aus["r_norm"] = [round(float(zeile[1]), 4) for zeile in werte]
                # Das Embedding selbst als VERGLEICHBARE Zahl: der Hash sagt nur
                # „anders", nicht „wie viel anders". Der Wert, der das Urteil traegt,
                # ist der Kosinus — also wird er gegen die Eichmarke gerechnet.
                if roh:
                    aus["_r_emb"] = np.asarray(werte[0][0], np.float64).tolist()
        th_fd, _M = wk.theta_fd(box, g.seiten[wk.FD][0], g.nm)
        zug = wk.leinwand_zug(box, g.W, g.H)
        werte = self._ruf_fd([th_fd] * wk.AUFRUF_BREITE, [zug] * wk.AUFRUF_BREITE)
        aus[wk.FD] = hashlib.md5(
            b"".join(np.ascontiguousarray(v, np.float32).tobytes()
                     for p, sL, sL2 in werte
                     for v in (p, np.float32(sL), np.float32(sL2)))).hexdigest()[:12]
        return aus


class Geometrie:
    """Die Kompilate EINER Clip-Geometrie (v7): der Vorverarbeitungs-Graph mit den
    Detektor-Ausgaengen und 'rgb', dazu je Stufe der Ausschnitt-Graph. Die Modelle
    dahinter kommen aus dem prozessweiten ModellBestand.

    Kein Frame-Zustand am Objekt: Anfragen und Geraete-Tensoren liegen im Satz, den
    sich jeder Rechenstrang einmal holt (satz()). Damit traegt dieselbe Klasse den
    Einzelstrang und die Mehrstrang-Fassung, ohne dass eine der beiden eine zweite
    Bauvorschrift braucht."""

    def __init__(self, core, ctx, W, H, best):
        t0 = time.monotonic()
        self.core, self.ctx, self.W, self.H = core, ctx, W, H
        self.pre, self.det_wh, self.det_scale, self.det_n = graph_pre_det(core, H, W)
        self.bestand, self.seiten = best, best.seiten
        geteilt0 = best.bau_s
        self.crop, self.modell = {}, {}
        for k in wk.STUFEN:
            if k == wk.FD:
                # Die fd-Stufe traegt neben ihrem Ausschnitt die Laplace-Leinwand im
                # selben Graphen (graph_crop_fd) — ein Aufruf statt zwei.
                self.crop[k] = graph_crop_fd(core, H, W, wk.AUFRUF_BREITE, best.seiten[k],
                                             best.norm[k])
            else:
                self.crop[k] = graph_crop(core, H, W, wk.AUFRUF_BREITE, best.seiten[k],
                                          best.norm[k], k)
            self.modell[k] = best.kompilat(k, wk.AUFRUF_BREITE)
        self.bau_geteilt_s = best.bau_s - geteilt0     # was DIESE Geometrie am Bestand zahlte
        self.nm = wk.gitter_norm(W, H)
        self.zentren = wk.zentren_fuellen(self.det_wh, self.det_scale)
        self._lokal = threading.local()
        self._satz_schloss = threading.Lock()
        self.saetze = 0
        self.bau_s = time.monotonic() - t0

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

    def kompilate_zaehlen(self):
        """Wie viele Kompilate diese Geometrie BENUTZT (eigene + geteilte) und wie viele
        ihr allein gehoeren — gezaehlt an den Objekten, nicht aus einer Formel."""
        eigen = 1 + len(self.crop)
        return eigen + len(self.modell), eigen


# ------------------------------------------------------------------ Bild-Weg (E2c)
def modell_det_bild(core, det_wh):
    """Der Detektor-Kopf des BILD-Wegs: det_10g auf einer FERTIGEN Leinwand.

    Unterschied zum Video-Weg (graph_pre_det) ist genau der Kopf davor: dort kommt der
    Frame als NV12 herein und Verkleinerung plus Leinwand entstehen im Graphen, hier
    liegt die Leinwand schon als [1,3,det_h,det_w] RGB-Rohbild (0..255) vor, weil die
    Katalog-Wege mit EINZELBILDERN arbeiten und ihr Resize seit jeher cv2 macht
    (insightface SCRFD.detect). Die Normierung (x - DET_MEAN) / DET_STD steht hier wie
    dort im Graphen, damit es sie nur einmal gibt.

    Warum der Bild-Weg NICHT ueber die Geometrie laeuft: eine Geometrie ist an (W, H)
    gebunden und baut sechs Graphen. Katalog-Bilder haben hunderte verschiedene
    Groessen — das waere ein Kompilat-Sturm. Der Bild-Weg haengt deshalb an der
    DETEKTOR-LEINWAND (det_size, wenige Werte: 320x320 im Katalog, ar_det_size des
    Clips in der Ernte) und nutzt sonst nur die prozessweiten Modell-Kompilate.
    -> (kompiliert, Zahl der Ausgaenge)"""
    det_w, det_h = det_wh
    lw = _benannt(ops.parameter([1, 3, det_h, det_w], np.float32, name="leinwand"),
                  "leinwand")
    m = core.read_model(wk.modell_pfad("det_10g"))
    _einhaengen(m, ops.divide(ops.subtract(lw, _c(wk.DET_MEAN)), _c(wk.DET_STD)))
    modell = ov.Model(list(m.get_results()), [lw], f"det_bild_{det_w}x{det_h}")
    return _kompilieren(core, modell), len(m.get_results())


class BildStufen:
    """Die Stufen der Engine auf CPU-GELIEFERTEN Ausschnitten (E2c, Bild-Weg).

    Der Video-Weg schneidet auf der GPU aus dem RGB-Vollbild (graph_crop + GridSample).
    Der Bild-Weg kann das nicht, ohne je Bildgroesse einen Satz Graphen zu bauen —
    und er MUSS es auch nicht: seine Ausschnitte entstehen seit jeher auf der CPU
    (insightface face_align.norm_crop bzw. der Landmark-Zuschnitt), und genau diese
    Bytes sind die Messbasis der bestehenden Referenzen. Neu ist allein, WER die
    Modelle rechnet: bis E2b onnxruntime-openvino (die ABI-Klemme, wegen der es E2c
    ueberhaupt gibt), jetzt dieselben Kompilate, auf denen auch die Analyse laeuft.

    GEBRAUCHT WERDEN NUR DREI STUFEN — det, fd (1k3d68) und r (Erkennung). e, t und p
    laufen in den Katalog-Wegen ueber core/guete bzw. pose_wache, und die binden
    ausdruecklich den CPU-Provider (core/guete.py:359-360, prototyp/pose_wache.py:95);
    der vertraegt sich mit dem OV-Kern (E1-Beleg) und bleibt deshalb unangetastet.

    BREITE 1, bewusst: die Feature-Norm des Lernlaufs misst Batch 1
    (core/normlauf.py, „NormMass driftet zwischen Batchgroessen"), und der Bild-Weg
    ist kein Durchsatz-Pfad. Eine feste Breite 1 haelt die Messbasis und spart die
    Polster-Frage; Mehrkosten zahlt nur, wer viele Gesichter je Bild hat."""

    BREITE = 1

    def __init__(self, engine):
        self.engine = engine
        self.core = engine.core
        if engine.bestand is None:
            engine.bestand = ModellBestand(engine.core)
        self.bestand = engine.bestand
        self.seiten = self.bestand.seiten
        self.norm_vorschrift = self.bestand.norm_vorschrift
        self.lm_punkte = self.bestand.lm_punkte
        self._det = {}                        # (det_w, det_h) -> (Anfrage, n_aus)
        self._stufen = {}                     # Stufe -> (Anfrage, n_aus)
        self._schloss = threading.Lock()

    def det(self, leinwand, det_wh):
        """Die neun Detektor-Ausgaenge fuer EINE fertige Leinwand [1,3,h,w] float32
        (RGB, 0..255 — die Normierung steckt im Graphen)."""
        with self._schloss:
            eintrag = self._det.get(tuple(det_wh))
            if eintrag is None:
                t0 = time.monotonic()
                komp, n_aus = modell_det_bild(self.core, det_wh)
                eintrag = self._det[tuple(det_wh)] = (komp.create_infer_request(), n_aus)
                self.bestand.bau_s += time.monotonic() - t0
            req, n_aus = eintrag
            t = req.get_tensor("leinwand")
            np.copyto(t.data, leinwand)
            req.start_async()
            req.wait()
            return [np.array(req.get_output_tensor(i).data) for i in range(n_aus)]

    def det_normiert(self):
        """Rechnet dieser Bild-Detektor die (x-mean)/std selbst? -> True; sie steht in
        modell_det_bild im Graphen, wie im Video-Weg. Die Frage steht als METHODE da,
        damit bild_kern sie nicht an der Engine-Sorte festmacht."""
        return True

    def stufe(self, k, X):
        """Eine Stufe auf FERTIG NORMIERTEN Ausschnitten X [n,3,h,w] float32.
        -> je Zeile ein Tupel ihrer Ausgabezeilen (Form wie Satz.stufe)"""
        with self._schloss:
            eintrag = self._stufen.get(k)
            if eintrag is None:
                komp = self.bestand.kompilat(k, self.BREITE)
                eintrag = self._stufen[k] = (komp.create_infer_request(),
                                             len(komp.outputs))
            req, n_aus = eintrag
            aus = []
            t = req.get_tensor(NAME_CROP)
            for zeile in np.asarray(X, np.float32):
                np.copyto(t.data, zeile[None])
                req.start_async()
                req.wait()
                aus.append(tuple(np.array(req.get_output_tensor(j).data[0])
                                 for j in range(n_aus)))
            return aus

    def auskunft(self):
        return {"engine": Engine.name, "geraet": GERAET, "breite": self.BREITE,
                "det_leinwaende": [f"{w}x{h}" for (w, h) in sorted(self._det)],
                "stufen": sorted(self._stufen)}


# ------------------------------------------------------------------ Die Engine
class Engine:
    """Die OpenVINO-Seite, wie der Kern sie sieht: Frames, Geometrien, Kopf-Auskunft."""

    name = "ov"
    stufen_folge = wk.STUFEN

    @staticmethod
    def argumente(ap):
        ap.add_argument("--cache", help="OpenVINO-Kompilat-Cache (Ordner). VORGABE AUS "
                                        "(E2d, gemessen — s. Engine._cache_setzen). Ein "
                                        "Ordner hier schaltet ihn AUSDRUECKLICH ein, nur "
                                        "fuer Messreihen: die Erkennungswerte haengen dann "
                                        "am Cache-Zustand.")

    def __init__(self, a):
        self.core = ov.Core()
        if GERAET not in self.core.available_devices:
            raise SystemExit(f"kein {GERAET}, kein Rueckfall")
        # Der Geraete-Kontext, aus dem die Remote-Tensoren stammen (v7). Er ist der
        # Vorgabe-Kontext derselben iGPU, auf der die Kompilate laufen — nur so darf ein
        # Tensor zwischen zwei Kompilaten wandern.
        self.ctx = self.core.get_default_context(GERAET)
        os.makedirs(a.out, exist_ok=True)
        self.cache, self.kalt, self.frei = self._cache_setzen(a)
        self.bestand = None

    def _cache_setzen(self, a):
        """Kompilat-Cache — SEIT E2d (13.09.2026) AUS, ausser jemand gibt ausdruecklich
        einen Ordner mit. Das ist die Umkehr des v2-Entscheids vom 12.09. („Cache als
        Vorgabe"), und sie hat einen gemessenen Grund:

        DER BEFUND. Ein Prozess, der einen TEIL seiner Kompilate aus dem Blob-Cache
        IMPORTIERT und den Rest neu KOMPILIERT, rechnet die ERKENNUNGS-Stufe anders.
        Gemessen am festen Pruefvektor (Satz.probe), zwei Geometrien, derselbe Code,
        dieselbe Maschine:
            alles selbst kompiliert   ||f|| 23,4062 / 24,3281
            warmer Cache (gemischt)   ||f|| 23,6406 / 23,2656
            Embedding dazu: max|d| 4,2e-03 bis 8,4e-03, 1-cos bis 1,8e-03
        In der Akte waren das 0,441 -> 0,421 bei den Scores, bis 6,58 bei best_norm, und
        Urteils-Wirkung (win3s 2 -> 1, Blick 6 -> 5) — bei UNVERAENDERTEN Detektionen,
        Frames und Guete-Werten. In der E2b-Eichung traf dieselbe Klasse einen Lauf mit
        77 % Namensverlust (Score 0,441 -> 0,073).

        WARUM DIE ZWEI NAHELIEGENDEN FIXE NICHT REICHEN, je gemessen:
          * GETRENNTE Cache-Ordner je Weg (Bild/Video): der Defekt tritt auch mit einem
            Cache auf, den ein reiner VIDEO-Lauf geschrieben hat — es ist keine Kollision
            zwischen den Wegen.
          * EINDEUTIGE NAMEN je Kompilat: die Knotennamen sind jetzt festgepinnt
            (`_namen_festpinnen`, eigener Wert fuer sich), aber der Cache-SCHLUESSEL
            haengt nicht an ihnen — er blieb Byte fuer Byte derselbe. Die Schluessel der
            drei angehaengten Stufen (lm_n, p_n, rec_n) driften trotzdem, sobald vorher
            importiert wurde.
        Sauber sind nur die zwei REINEN Faelle: alles kompilieren oder alles importieren.
        „Alles importieren" ist nicht entscheidbar, solange Geometrien zur LAUFZEIT
        entstehen (W2-B29) — der Prozess weiss beim Start nicht, welche Clip-Groessen
        kommen. Bleibt: alles kompilieren.

        DER PREIS, beziffert: der Aufbau kostet ohne Cache gemessen 24,6 s (Modelle +
        eine 4K-Geometrie) bzw. 30-36 s fuer zwei Geometrien, mit warmem Cache 10-18 s.
        Das ist EINMAL je Prozessleben; der Frist-Waechter kennt den Kompilat-Bau als
        Ausnahme. Gegenrechnung: ohne Cache ist der Lauf bitgleich reproduzierbar
        (max|d| 0,0 bei gleicher Bau-Reihenfolge, 4,5e-08 bei anderer).

        WEG ZURUECK (E3): wird die Geometrie-Liste deklarativ (Kameras sind bekannt),
        ist „alles oder nichts" entscheidbar und der Cache kann mit einem Manifest
        zurueckkommen. Bis dahin gilt: Werte vor Startzeit.

        SUSLIK_OV_CACHE wird ABSICHTLICH NICHT MEHR GELESEN: eine herumliegende
        Umgebungsvariable darf keine Erkennungswerte verschieben. Ist sie gesetzt, sagt
        das hier eine Zeile. -> (Ordner oder "", kalt?, freie Byte)"""
        cache = a.cache or ""
        umgebung = os.environ.get("SUSLIK_OV_CACHE")
        if umgebung and not cache:
            print(f"HINWEIS: SUSLIK_OV_CACHE={umgebung} wird ignoriert — der "
                  f"Kompilat-Cache ist seit E2d aus (Werte haengen sonst am "
                  f"Cache-Zustand). Mit --cache <ordner> ausdruecklich einschalten.",
                  file=sys.stderr, flush=True)
        kalt, frei = None, None
        if cache:
            os.makedirs(cache, exist_ok=True)
            kalt = not any(os.scandir(cache))
            frei = shutil.disk_usage(cache).free
            print(f"WARNUNG: Kompilat-Cache AUSDRUECKLICH EIN ({cache}). Gemessen "
                  f"(E2d): ein Prozess, der teils importiert und teils kompiliert, "
                  f"rechnet die Erkennung anders (1-cos bis 1,8e-03, ||f|| bis -1,07). "
                  f"Nur fuer Messreihen, nicht fuer Urteile.",
                  file=sys.stderr, flush=True)
            if kalt and frei < CACHE_BEDARF:
                # Lieber ohne Cache neu bauen als einen abgeschnittenen hinterlassen, an
                # dem der naechste Lauf hart scheitert (CACHE_BEDARF). Laut, nicht still.
                print(f"WARNUNG: Cache {cache} hat nur {frei // 1024 // 1024} MB frei, "
                      f"noetig sind rund {CACHE_BEDARF // 1024 // 1024} MB — Cache bleibt "
                      f"AUS. Ordner auf eine groessere Ablage legen (nicht ins tmpfs "
                      f"unter /tmp).", file=sys.stderr, flush=True)
                cache = ""
            else:
                self.core.set_property({"CACHE_DIR": cache})
        return cache, kalt, frei

    def frames(self, clip, W, H, schritt, wache=None):
        return frames_nv12(clip, W, H, schritt, wache=wache)

    def bild_stufen(self):
        """Der BILD-Weg dieser Engine (E2c), einmal je Prozess. -> BildStufen"""
        if getattr(self, "_bild", None) is None:
            self._bild = BildStufen(self)
        return self._bild

    def geometrie_bauen(self, geo):
        """Je Clip-Geometrie einmal die Kompilate. -> {(W, H): Geometrie}"""
        if self.bestand is None:
            self.bestand = ModellBestand(self.core)
        graphen = {}
        for W, H, _fps in geo.values():
            if (W, H) not in graphen:
                graphen[(W, H)] = Geometrie(self.core, self.ctx, W, H, self.bestand)
        return graphen

    def kopf_auskunft(self, graphen):
        """Was WIRKLICH gebaut wurde, an den Objekten gezaehlt — damit ein Lauf nicht als
        Variante durchgehen kann, die er nicht war."""
        g0 = next(iter(graphen.values()))
        best = self.bestand
        return {"kompilate_je_geometrie": {f"{g.W}x{g.H}": g.kompilate_zaehlen()[0]
                                           for g in graphen.values()},
                "kompilate_eigen": {f"{g.W}x{g.H}": g.kompilate_zaehlen()[1]
                                    for g in graphen.values()},
                "kompilate_bestand": best.kompilate_zaehlen(),
                "modell_pfade": {k: best.pfade[k] for k in sorted(best.pfade)},
                "det_onnx": wk.modell_pfad("det_10g"), "det_ausgaenge": g0.det_n,
                "geraet": GERAET, "openvino": ov.__version__,
                "cache": self.cache or None, "cache_kalt": self.kalt,
                "cache_frei_mb": (self.frei // 1024 // 1024) if self.frei is not None else None,
                # AM KOMPILAT ABGELESEN, nicht behauptet — je Stufe einzeln, seit dem
                # f32-Warp-Fix (14.09.2026) muessen es ALLE FUENF sein. Die Zeile ist der
                # einzige Beleg dafuer, dass der Hinweis nicht von der Laufzeit
                # verschluckt wurde; die fruehere Fassung fragte nur die fd-Stufe und
                # haette einen fp16-Rueckfall bei e/t/p/r nicht gesehen.
                "ausschnitt": {
                    "praezision": {k: str(g0.crop[k].get_property(
                        "INFERENCE_PRECISION_HINT")) for k in sorted(g0.crop)},
                    "u8_rundung": "floor(x+0.5) nach dem Warp, vor der Normierung"},
                # bleibt stehen, weil worker_kern.kopf den 'fd'-Block der Engine in
                # seinen eigenen mischt (Konsumenten lesen ihn dort)
                "fd": {"praezision":
                       str(g0.crop[wk.FD].get_property("INFERENCE_PRECISION_HINT"))}}
