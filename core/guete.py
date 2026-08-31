"""Bildguete-Messung fuer die Kalibrier-Funktion (.377, User-Entscheid 30.08.).

Zwei Masse, beide EIN Skalar je Bild (Herkunft/Lizenz: models/LIZENZEN_GUETE.md):
  fiqa_t     eDifFIQA(T) — Erkennbarkeit aus Sicht eines Gesichts-Erkenners;
             bestraft auch Verdeckung (Messtag 30.08.: die zwei vom User
             beanstandeten Verdeckungs-Faelle lagen bei T weit unten, waehrend
             das Empfinden sie mochte). Input: das ALIGNED 112er-Crop, exakt
             das der Feature-Norm (norm_crop) — kein zweites Alignment.
  empfinden  Efficient-FIQA (EdgeNeXt-XXS) — Bild-Eindruck fuers Auge
             (Schaerfe-/Helligkeitsempfinden). Input: der ROHE Crop, 352er-
             Resize mit ImageNet-Normierung (Vorgabe des Modells).

Dieses Modul MISST nur. Die Schwellen (guete_empfinden_min/guete_t_min)
leben in der Config und werden vom jeweiligen Verbraucher injiziert —
Zahlen kommen nie von hier (Haus-Regel, Muster norm_latte/REF_LATTE).

Messbasis der Modellwahl: Vierervergleich 30.08. an 714 Bildern eines
Feld-Lernlaufs (labor-Auswertung fiqa_vergleich.json): Laplacian-sharp
korreliert r=-0,06 mit dem FIQA-Urteil (als Qualitaetsmass widerlegt);
alle Kandidaten-Modelle sahen die vom alten sharp-Kriterium Aussortierten
im Median BESSER als die Uebernommenen. FROQ wurde gemessen und verworfen
(praktisch identisch mit der vorhandenen Feature-Norm, +0,05 Spearman).

Backend bewusst CPU: zusammen ~1,7+1,2 Mio Parameter, gemessen ~7 ms (T)
je Bild bei 4 Threads — laeuft nur im Lernlauf, je Kandidat einmal, und
konkurriert so nie mit der Erkennung um iGPU/NPU."""
import os
import threading

import numpy as np

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PFAD_T = os.path.join(HIER, "models", "ediffiqa_tiny_jun2024.onnx")
PFAD_E = os.path.join(HIER, "models", "fiqa_edgenext_xxs.onnx")
_IN_MEAN = np.array([0.485, 0.456, 0.406], np.float32)   # ImageNet (Efficient-FIQA-Vorgabe)
_IN_STD = np.array([0.229, 0.224, 0.225], np.float32)

# Werks-Startwerte der Guete-Latte — am Feldmaterial geeicht (Messtag
# 30.08., 714 Bilder, User-Slider; analysen/todos_29_08.md Punkt 9).
# EINE Quelle: load_config-Defaults UND der Standard-Knopf der
# Kalibrier-Seite lesen von HIER (K3-Regel gegen Zweit-Literale).
STARTWERTE = {"empfinden": 0.200, "t": 0.400}
# Anzeige-/Melde-Vorgaben der Kamera-Kalibrierseite (User-Vorgabe 31.08.:
# "Bildeindruck 0,175, Erkennbarkeit 0,200") — bewusst MILDER als die
# Katalog-STARTWERTE darueber: was zum Anzeigen reicht, reicht nicht
# automatisch zum Lernen. EINE Quelle, der Kalibrier-Handler liest von hier.
ANZEIGE_STARTWERTE = {"empfinden": 0.175, "t": 0.200}

_lock = threading.Lock()
_sess = {}


def _session(pfad):
    """Lazy, prozessweit einmal. Thread-Kappung ueber DEN einen Haus-Griff
    face_audit._ort_thread_opts (cgroup-bewusst; eine nackte Session baute
    ihren Pool nach HOST-Kernen — Gate-Stufe erzwingt den Griff)."""
    with _lock:
        s = _sess.get(pfad)
        if s is None:
            import onnxruntime as ort
            from face_audit import _ort_thread_opts
            # deckel=4 (.377b, GEMESSEN im Prod-Container unter Lauf-Last):
            # 12 Threads = 33+57 ms je Bild, 4 Threads = 4+13 ms — Mini-Netze
            # ersticken am Thread-Overhead. 4 ist das Messoptimum der Reihe
            # (1/2/4 Threads), nie mehr als die erlaubten Kerne.
            s = ort.InferenceSession(pfad, sess_options=_ort_thread_opts(deckel=4),
                                     providers=["CPUExecutionProvider"])
            _sess[pfad] = s
        return s


def verfuegbar():
    """Beide Modelldateien vorhanden? (Alt-Images ohne die Dateien laufen
    weiter — die Verbraucher fallen dann auf den Alt-Weg zurueck, laut.)"""
    return os.path.exists(PFAD_T) and os.path.exists(PFAD_E)


def fiqa_t(aligned_bgr112):
    """eDifFIQA(T) auf dem aligned 112x112-BGR-Crop -> float (hoch = gut)."""
    s = _session(PFAD_T)
    x = ((aligned_bgr112[:, :, ::-1].astype(np.float32) / 255.0) - 0.5) / 0.5
    return float(s.run(None, {s.get_inputs()[0].name:
                              x.transpose(2, 0, 1)[None]})[0].ravel()[0])


def empfinden(roh_bgr):
    """Efficient-FIQA auf dem rohen Crop (beliebige Groesse) -> float."""
    import cv2
    s = _session(PFAD_E)
    r = cv2.resize(roh_bgr, (352, 352))[:, :, ::-1].astype(np.float32) / 255.0
    x = (r - _IN_MEAN) / _IN_STD
    return float(s.run(None, {s.get_inputs()[0].name:
                              x.transpose(2, 0, 1)[None]})[0].ravel()[0])
