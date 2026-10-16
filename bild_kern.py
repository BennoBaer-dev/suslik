#!/usr/bin/env python3
"""bild_kern — der BILD-Weg des neuen Kerns und die Adapter fuer die Alt-Jobs
(E2c, 13.09.2026).

WOZU ES DIESE DATEI GIBT (der gemessene Anlass). Der neue Worker haelt einen
OpenVINO-Kontext des eigenstaendigen `openvino`-Pakets. Die Hintergrund-Jobs
(ernte, norm, refqs, vorschlaege, passernte) rechnen ihre Gesichter bis heute ueber
`face_audit.Embedder`/`face_audit.NormMass`, also ueber onnxruntime-openvino. Beide
OpenVINO-Fassungen sind im SELBEN Prozess ABI-unvertraeglich (E1-Befund,
`undefined symbol: _ZN2ov3Any4Base9to_stringEv`); ORT faellt daneben LAUT auf den
CPU-Provider. Gemessen im E2-Gate: der refcache-Neubau landete so auf dem CPU-EP und
wich bis 1,59e-02 je Embedding von der GPU-Fassung ab — Referenzen und
Live-Embeddings stammten damit aus zwei verschiedenen Rechnungen. User-Entscheid
13.09.: „die Hintergrundjobs auch aufs Neue umziehen, durchgaengig, dann testen."

DAS MUSTER IST DAS VON worker.py, NICHT EIN UMBAU DER JOBS. `worker.py:351-364`
ersetzt `face_audit.Embedder` durch eine Fabrik, die einen warmen Embedder
wiederausgibt. Hier tut die Fabrik dasselbe — nur dass das Objekt, das sie
herausgibt, seine Modelle auf der ENGINE rechnet. `anlernen.py`, `core/ernte.py`,
`core/normlauf.py` und `core/passernte.py` bleiben Zeile fuer Zeile unveraendert.

WAS DER ADAPTER KANN, UND WARUM GENAU DAS. Die Konsumenten wurden am Code erhoben
(grep ueber die vier Dateien), nicht geraten:
    emb.modell                         anlernen.py (20 Stellen), Cache-/Beiwert-Schluessel
    emb.embed(img_bgr)                 anlernen.py:231/1355/3380/3454 (Referenz-Vektoren)
    emb.app.get(img)                   anlernen.py:441/610/1051/1535, core/ernte.py:1066
    emb.app.det_model.det_thresh = x   core/ernte.py:1018 (die det-Achse des Siebs)
    emb.ar_det_size(b, h)              core/ernte.py:1004, anlernen.py:439
    emb.set_det_size((w, h))           core/ernte.py:1004, anlernen.py:412/439
    emb.faces_mit_vorschranke(...)     core/ernte.py:946/1065 (die Ernte-Vorschranke)
    face.bbox .det_score .kps          alle vier
    face.normed_embedding              anlernen.py:447/464/616/1548, core/ernte.py:1293
    face.pose                          core/ernte.py:1071/1127/1290, anlernen.py:1553
    face.vorab_verworfen               core/ernte.py:1068 (Zaehler-Invariante)
Mehr nicht — und nichts davon ist hier neu erfunden: die Gesichter sind echte
`insightface.app.common.Face`-Objekte, also gilt `normed_embedding` (embedding/L2)
wortgleich wie bisher.

DREI STUFEN, NICHT FUENF. Der Adapter rechnet ueber die Engine nur det (SCRFD),
fd (1k3d68 -> `face.pose`) und r (Erkennung -> `face.normed_embedding` und die
Feature-Norm). e, t und p bleiben, wo sie sind: `core/guete.py:359-360` und
`prototyp/pose_wache.py:95` binden ausdruecklich den CPU-Provider, und
`face_audit.StrukturMass` ebenso (`face_audit.py:1787`) — ORT-CPU vertraegt sich mit
dem OV-Kern (E1-Beleg), es gibt also nichts umzuziehen. Was NICHT angefasst wird,
kann auch nichts verschieben.

DER PIXELWEG DES BILD-WEGS, ehrlich benannt. Die Katalog-Wege arbeiten auf
EINZELBILDERN (JPEG/BGR), nicht auf NV12-Video. Ihre Zuschnitte entstehen seit jeher
auf der CPU — `cv2.resize` in die Detektor-Leinwand (insightface SCRFD.
_detect_candidates), `face_align.norm_crop` fuer den 112er, der Landmark-Zuschnitt
fuer 1k3d68 —, und GENAU DIESE BYTES sind die Messbasis des vorhandenen Bestands.
Der Adapter behaelt sie deshalb und tauscht nur den RECHNER darunter. Das ist der
Unterschied zum Video-Weg, wo der Ausschnitt per GridSample auf der GPU faellt; die
beiden Wege sind deshalb NICHT bitgleich zueinander, und das war auch vorher so
(JPEG gegen Videoframe). Was E2c beseitigt, ist der Misch-Zustand INNERHALB einer
Rechnung: Referenz-Embeddings und Live-Embeddings kommen jetzt aus demselben
Modell-Kompilat auf demselben Geraet.

DIE HEILIGE REIHENFOLGE GILT UNVERAENDERT. Referenz- und Katalogbilder werden bei
det 320 eingebettet; im alten Worker sorgte dafuer die Fabrik, die jedem Bezieher
`set_det_size((320, 320))` mitgab (worker.py:363). Diese Fabrik tut dasselbe
(`EngineEmbedder.zuruecksetzen`), und `set_det_size` setzt — wie `app.prepare` im
Original — die det-Schwelle auf den Bibliotheks-Vorgabewert zurueck. Genau darauf
baut `core/ernte.py:1005-1018` („det_thresh NACH set_det_size neu binden").

BREITE 1. Die Stufen laufen je Gesicht einzeln. Der Grund ist die Feature-Norm: der
gebuendelte Norm-Schritt misst bewusst Batch 1 (`core/normlauf.py`, „NormMass driftet
zwischen Batchgroessen"), und eine andere Batchgroesse maesse etwas anderes als der
Bestand. Der Bild-Weg ist ausserdem kein Durchsatz-Pfad. Wer viele Gesichter je Bild
hat, zahlt dafuer Aufrufe — das ist bekannt und bewusst.
"""
import hashlib
import os
import threading

import worker_kern as wk                                # noqa: E402  Bootstrap + BLAS-Pin
import numpy as np                                         # noqa: E402  (schon vom Kern geladen)
import cv2                                                 # noqa: E402  (ebenso)

import face_audit                                          # noqa: E402  Modell-Spec, ar_det_size
from core import logbuch as _logbuch
_log = _logbuch.logger(__name__)


def _det_thresh_vorgabe():
    """Die det-Schwelle, die `app.prepare` setzt — aus der Bibliothek gelesen, nicht
    als Zahl hier hingeschrieben. `face_audit.Embedder.set_det_size` ruft
    `self.app.prepare(ctx_id=0, det_size=...)`, und FaceAnalysis.prepare setzt dabei
    `det_thresh` auf seinen Vorgabewert zurueck. Die Ernte verlaesst sich darauf
    (core/ernte.py:1005-1018) — also muss der Adapter es auch tun, und zwar mit
    DERSELBEN Zahl. Faellt das Lesen aus, bleibt der dokumentierte Wert 0.5
    (insightface FaceAnalysis.prepare) mit einem Vermerk."""
    try:
        import inspect                                     # noqa: PLC0415
        from insightface.app import FaceAnalysis           # noqa: PLC0415
        w = inspect.signature(FaceAnalysis.prepare).parameters["det_thresh"].default
        return float(w)
    except Exception:                                      # noqa: BLE001
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning 0.5")
        return 0.5


def norm_anwenden(crops_bgr, vorschrift):
    """Zuschnitte (BGR, uint8 oder float) -> [n,3,h,w] float32 nach der Vorschrift des
    Kerns (`worker_kern.norm_schritte`).

    EINE QUELLE, kein zweites Rezept: die Engines bauen aus derselben Vorschrift ihre
    Graph-Knoten (`engine_ov._norm_bauer`), hier entsteht sie in numpy. Der Eingang der
    Graphen ist RGB (der Video-Weg kommt aus nv12_to_rgb), deshalb wird der BGR-Crop
    zuerst gedreht und die Vorschrift danach WORTGLEICH abgearbeitet — inklusive ihres
    eigenen 'bgr'-Schritts, der bei adaface wieder zurueckdreht. Das ist bewusst keine
    Abkuerzung: wer hier den Doppelschritt einspart, hat ein zweites Rezept."""
    schritte = wk.norm_schritte(vorschrift)
    X = np.stack([cv2.cvtColor(np.ascontiguousarray(c), cv2.COLOR_BGR2RGB)
                  for c in crops_bgr]).astype(np.float32)   # [n,h,w,3] RGB
    X = X.transpose(0, 3, 1, 2)                             # [n,3,h,w]
    for art, wert in schritte:
        if art == "bgr":
            X = X[:, ::-1, :, :]
        elif art == "sub":
            a = np.asarray(wert, np.float32)
            X = X - (a.reshape(1, 3, 1, 1) if a.size == 3 else a)
        else:
            a = np.asarray(wert, np.float32)
            X = X / (a.reshape(1, 3, 1, 1) if a.size == 3 else a)
    return np.ascontiguousarray(X, np.float32)


def det_leinwand(img_bgr, det_size):
    """Bild -> Detektor-Leinwand [1,3,det_h,det_w] float32 RGB (roh, 0..255) und die
    Skala, mit der die Boxen zurueckgerechnet werden.

    Zeile fuer Zeile insightface SCRFD._detect_candidates (scrfd.py) und
    SCRFD.forward: Seitenverhaeltnis halten, `cv2.resize`, oben links in eine schwarze
    Leinwand, dann RGB. Die Verkleinerungs-RECHNUNG selbst kommt aus
    `worker_kern.det_geometrie` — sie steht dort fuer beide Engines, und eine zweite
    Fassung hier waere die zweite Quelle, die dieses Haus verbietet.
    -> (leinwand, det_scale, (det_w, det_h))"""
    H, W = img_bgr.shape[:2]
    det_w, det_h = int(det_size[0]), int(det_size[1])
    if H / W > det_h / det_w:
        neu_h = det_h
        neu_w = int(neu_h / (H / W))
    else:
        neu_w = det_w
        neu_h = int(neu_w * (H / W))
    det_scale = neu_h / H
    klein = cv2.resize(img_bgr, (neu_w, neu_h))
    lw = np.zeros((det_h, det_w, 3), np.uint8)
    lw[:neu_h, :neu_w, :] = klein
    rgb = cv2.cvtColor(lw, cv2.COLOR_BGR2RGB).astype(np.float32)
    return rgb.transpose(2, 0, 1)[None], det_scale, (det_w, det_h)


class BildRechner:
    """Die drei Engine-Stufen des Bild-Wegs, EINMAL je Prozess.

    Er haelt nur, was sich nicht aus der Engine ergibt: den Anker-Cache der
    SCRFD-Nachverarbeitung je Detektor-Leinwand (`worker_kern.zentren_fuellen` — im
    Video-Weg liegt er an der Geometrie, hier gibt es keine) und die Normierungs-
    Vorschriften. Alles andere kommt aus `engine.bild_stufen()`."""

    def __init__(self, engine):
        self.engine = engine
        self.stufen = engine.bild_stufen()
        self.vorschrift = self.stufen.norm_vorschrift
        self.seiten = self.stufen.seiten
        self.lm_punkte = self.stufen.lm_punkte
        self._zentren = {}
        self._schloss = threading.Lock()

    def _zentren_fuer(self, det_wh, det_scale):
        with self._schloss:
            z = self._zentren.get((det_wh, round(det_scale, 9)))
            if z is None:
                z = self._zentren[(det_wh, round(det_scale, 9))] = wk.zentren_fuellen(
                    det_wh, det_scale)
            return z

    def detektieren(self, img_bgr, det_size, schwelle):
        """Detektion auf EINEM Bild -> (dets [m,5], kpss [m,5,2]).
        Die Nachverarbeitung ist die des Kerns (`worker_kern.detektor` = insightface
        SCRFD.forward + _detect_candidates + detect); neu ist nur, dass die neun
        Ausgaenge von der Engine kommen."""
        lw, det_scale, det_wh = det_leinwand(img_bgr, det_size)
        if not self.stufen.det_normiert():
            lw = (lw - wk.DET_MEAN) / wk.DET_STD
        outs = self.stufen.det(lw, det_wh)
        return wk.detektor(outs, det_wh, det_scale, float(schwelle),
                           self._zentren_fuer(det_wh, det_scale))

    def pose(self, img_bgr, box):
        """Die drei Vorzeichen-Winkel [rx, ry, rz] EINES Gesichts (1k3d68).

        Der Zuschnitt ist der von insightface `landmark.Landmark.get`: Mitte der
        FLOAT-Box, Skala seite/(max(w,h)*1,5), keine Drehung — die Matrix M rechnet
        `worker_kern.theta_fd`, damit sie nur einmal im Haus steht; `cv2.warpAffine`
        ist derselbe Griff wie dort. Die Winkel-Rechnung ist
        `worker_kern.fd_winkel`. -> np.float32[3] oder None"""
        H, W = img_bgr.shape[:2]
        seite = self.seiten[wk.FD][0]
        _th, M = wk.theta_fd(box, seite, wk.gitter_norm(W, H))
        crop = cv2.warpAffine(img_bgr, M, (seite, seite), borderValue=0.0)
        X = norm_anwenden([crop], self.vorschrift[wk.FD])
        aus = self.stufen.stufe(wk.FD, X)
        if not aus:
            return None
        return np.asarray(wk.fd_winkel(aus[0][0], M, seite), np.float32)

    def embeddings(self, crops112_bgr):
        """112er-Warps -> (Embeddings [n,512] L2-normiert, Feature-Normen [n]).
        Ein Aufruf je Crop (Breite 1, s. Kopf: die Norm-Messbasis ist Batch 1)."""
        if not len(crops112_bgr):
            return np.zeros((0, 512), np.float32), np.zeros((0,), np.float32)
        X = norm_anwenden(crops112_bgr, self.vorschrift["r"])
        aus = self.stufen.stufe("r", X)
        E = np.stack([np.asarray(w[0], np.float32).ravel() for w in aus])
        N = np.asarray([float(np.ravel(w[1])[0]) for w in aus], np.float32)
        return E, N


# ----------------------------------------------------------------- Der Embedder-Adapter
class _DetModell:
    """Das eine Attribut, das die Ernte am Detektor anfasst: `det_thresh`
    (core/ernte.py:1018). Mehr braucht kein Konsument — deshalb steht hier auch
    nicht mehr."""

    def __init__(self, det_thresh):
        self.det_thresh = float(det_thresh)


class _App:
    """Der `emb.app`-Griff, so weit die Konsumenten ihn benutzen: `get(img)` und
    `det_model.det_thresh`. `models` bleibt leer und ist absichtlich da — `hasattr`
    -Pruefungen im Bestand fragen nach `app`, nicht nach seinem Inhalt."""

    def __init__(self, emb):
        self._emb = emb
        self.det_model = _DetModell(_det_thresh_vorgabe())
        self.models = {}

    def get(self, img, max_num=0):
        return self._emb.gesichter(img, max_num=max_num)


class EngineEmbedder:
    """DER Adapter: dieselbe Aufruf-API wie `face_audit.Embedder`, gerechnet auf der
    Engine (s. Kopf dieser Datei fuer die erhobene Konsumenten-Liste).

    NICHT nachgebaut ist alles, was am alten ONNX-Runtime-Aufbau haengt und keinen
    Konsumenten in den Hintergrund-Jobs hat: `_to_backend`, `_provider_guard`,
    `_session_kette`, `rec_geraet`, `BATCH_STUFEN`, die Zaehl-Wache `_LEBENDE`. Der
    Provider-Guard des neuen Wegs ist das Gelingen des Engine-Baus selbst
    (worker_dienst.engine_bauen: die Engines WERFEN statt still auf CPU zu fallen),
    und er steht als strukturiertes Feld in jeder Job-Antwort."""

    def __init__(self, rechner, modell=None):
        self.rechner = rechner
        self.modell = (modell or face_audit.aktuelles_modell()).lower()
        if self.modell not in face_audit.MODELLE:
            raise SystemExit(f"Unbekanntes Recognition-Modell '{self.modell}' "
                             f"(erlaubt: {list(face_audit.MODELLE)})")
        self._det_size = (320, 320)
        self.app = _App(self)

    # -------------------------------------------------- Form und Schwelle
    ar_det_size = staticmethod(face_audit.Embedder.ar_det_size)

    def set_det_size(self, det_size):
        """det_size setzen — und die det-Schwelle auf den Bibliotheks-Vorgabewert
        zuruecksetzen, weil `app.prepare` im Original genau das tut (face_audit.py:
        1116-1142). Die Ernte bindet ihre Schwelle deshalb NACH diesem Aufruf; ein
        Adapter, der die Schwelle stehen liesse, gaebe dem Ernte-Code ein anderes
        Verhalten als dem Bestand."""
        self._det_size = (int(det_size[0]), int(det_size[1]))
        self.app.det_model.det_thresh = _det_thresh_vorgabe()

    def zuruecksetzen(self):
        """Der frische Zustand, den jeder Bezieher erwartet — det 320 und die
        Vorgabe-Schwelle (worker.py:363, „die heilige Reihenfolge": Referenzbilder
        werden IMMER bei 320 eingebettet)."""
        self.set_det_size((320, 320))
        return self

    # -------------------------------------------------- Gesichter
    def _roh(self, img, max_num=0):
        """Detektion -> Liste leerer Face-Objekte (bbox, det_score, kps), in der
        Reihenfolge und Auswahl von insightface FaceAnalysis.get."""
        from insightface.app.common import Face             # noqa: PLC0415
        dets, kpss = self.rechner.detektieren(img, self._det_size,
                                              self.app.det_model.det_thresh)
        if max_num > 0 and len(dets) > max_num:
            dets, kpss = dets[:max_num], kpss[:max_num]
        return [Face(bbox=dets[i, 0:4], det_score=dets[i, 4],
                     kps=(kpss[i] if kpss is not None and len(kpss) else None))
                for i in range(len(dets))]

    def _nacharbeit(self, img, faces):
        """Pose und Embedding fuer die uebergebenen Gesichter — in der Reihenfolge,
        in der die Nach-Modelle bei insightface laufen (erst landmark_3d_68, dann die
        Erkennung; face_audit._get_gestaffelt/_get_mit_rec)."""
        if not faces:
            return
        for f in faces:
            f.pose = self.rechner.pose(img, f.bbox)
        mit_kps = [f for f in faces if f.kps is not None]
        if not mit_kps:
            return
        from insightface.utils import face_align             # noqa: PLC0415
        crops = [face_align.norm_crop(img, landmark=f.kps, image_size=112)
                 for f in mit_kps]
        E, _N = self.rechner.embeddings(crops)
        for f, e in zip(mit_kps, E):
            f.embedding = e

    def gesichter(self, img, max_num=0):
        """`app.get(img)`: alle Detektionen mit Pose und Embedding."""
        faces = self._roh(img, max_num=max_num)
        self._nacharbeit(img, faces)
        return faces

    def faces_mit_vorschranke(self, img, vorschranke, max_num=0):
        """Der Eintritt mit Auswahl (core/ernte.py:946/1065). Wortgleich zur Semantik
        von `face_audit._get_gestaffelt`: aussortierte Gesichter tragen die Marke
        `vorab_verworfen`, BLEIBEN in der Rueckgabe (die Ernte zaehlt jede Detektion
        — Invariante detektionen == fd + ohne_pose + vorab_verworfen + kandidaten,
        core/ernte.py:770-771) und haben weder Pose noch Embedding."""
        faces = self._roh(img, max_num=max_num)
        weiter = []
        for f in faces:
            if vorschranke is not None and not vorschranke(f):
                f.vorab_verworfen = True
                continue
            weiter.append(f)
        self._nacharbeit(img, weiter)
        return faces

    # -------------------------------------------------- Sammelbatch-Paar
    def sammelbatch_moeglich(self):
        """True: Detektion und Embedding sind hier von Natur aus getrennte Stufen."""
        return True

    def detektieren(self, img, max_num=0):
        """Detektion + Pose OHNE Embedding -> (faces, crops112), Gegenstueck zu
        `embeddings_batch` (face_audit.py:1066-1078)."""
        from insightface.utils import face_align             # noqa: PLC0415
        faces = self._roh(img, max_num=max_num)
        for f in faces:
            f.pose = self.rechner.pose(img, f.bbox)
        if not faces:
            return [], []
        return faces, [face_align.norm_crop(img, landmark=f.kps, image_size=112)
                       for f in faces if f.kps is not None]

    def embeddings_batch(self, crops_bgr):
        """112er-Crops -> L2-normierte Embeddings (face_audit.py:1080-1087)."""
        return self.rechner.embeddings(list(crops_bgr))[0]

    # -------------------------------------------------- Einzelbild
    def embed(self, img_bgr):
        """Ein Bild -> das Embedding des GROESSTEN Gesichts, float64, oder None.
        Zeile fuer Zeile `face_audit.Embedder.embed` (face_audit.py:1269-1279),
        inklusive der Vergroesserung auf kurze Kante >= 224 px."""
        h, w = img_bgr.shape[:2]
        scale = max(1.0, 224.0 / min(h, w))
        if scale > 1.0:
            img_bgr = cv2.resize(img_bgr, (round(w * scale), round(h * scale)),
                                 interpolation=cv2.INTER_CUBIC)
        faces = self.gesichter(img_bgr)
        if not faces:
            return None
        f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
        if f.normed_embedding is None:
            return None
        return np.asarray(f.normed_embedding, dtype=np.float64)


# ----------------------------------------------------------------- Der NormMass-Adapter
class EngineNormMass:
    """Die Feature-Norm ueber die r-Stufe der Engine — Ersatz fuer
    `face_audit.NormMass` in den Hintergrund-Jobs.

    DIE ZAHL IST DIESELBE GROESSE: NormMass haengt einen Zusatz-Ausgang an den
    adaface-Graphen und liest `f` VOR der L2-Division (face_audit._graph_bytes); die
    r-Stufe der Engine rechnet denselben Betrag als zweiten Ausgang
    (engine_ov.modell_r / engine_cuda.graph_rec_post). Gerechnet wird sie auf einem
    ANDEREN Geraete-Weg als bisher (Engine-Kompilat statt ORT-OV-Session, und die
    NORM_KETTE probierte zuerst die NPU) — die Werte liegen deshalb nahe beieinander,
    aber nicht bitgleich. Wie nahe, sagt das E2c-Gate, nicht dieser Kommentar.

    BATCH 1: `core/normlauf.py` misst ausdruecklich Batch 1, weil NormMass zwischen
    Batchgroessen driftet. `BildStufen.BREITE` ist 1, also bleibt es dabei.

    Die Latte ist an adaface geeicht (NormMass: „calibrated for 'adaface' only") —
    auf einem anderen Kopf bleibt der Adapter deshalb `ok=False`, mit demselben
    Grund-Text wie das Original, und der Verbraucher nimmt seine Latte LAUT heraus
    (fail-open je MODELL)."""

    def __init__(self, rechner, geraet, modell=None):
        self.rechner = rechner
        self.modell = (modell or face_audit.aktuelles_modell()).lower()
        self.device = str(geraet or "?")
        self.ok = False
        self.grund = ""
        spec = face_audit.MODELLE.get(self.modell) or {}
        if self.modell != "adaface" or spec.get("art") != "onnx":
            self.grund = (f"feature norm is calibrated for 'adaface' only "
                          f"(active model: '{self.modell}')")
            return
        self.ok = True

    def feature_norm(self, crops_bgr):
        """112er-Warps (BGR) -> Feature-Normen als np.float32[n]."""
        if not self.ok:
            raise RuntimeError(f"feature norm not available: {self.grund}")
        return self.rechner.embeddings(list(crops_bgr))[1]


# ----------------------------------------------------------------- Die Fabrik
class Fabrik:
    """Die Embedder-FABRIK des Dienstes — dasselbe Muster wie `worker._factory`
    (worker.py:351-364) und derselbe Vertrag: EIN warmer Adapter je Prozess, Neubau
    nur bei Modellwechsel (das Modell kann ueber Config/UI wechseln), und
    `det 320` je Ausgabe.

    Sie wird in `face_audit.Embedder` eingehaengt (`einhaengen`), damit jeder
    bestehende Aufruf `face_audit.Embedder()` sie trifft — auch die, die tief in
    `anlernen` stehen und keinen `emb`-Parameter durchreichen. Das ist exakt der
    Griff, den der alte Worker seit 0.1.0.38 benutzt."""

    def __init__(self, rechner_holen, geraet):
        # FAUL, und das ist eine Bedingung, keine Bequemlichkeit: `BildRechner` legt
        # den Modell-Bestand der Engine an (Formen lesen, mittlere Landmark-Form).
        # Ein Prozess, der nur Analyse-Jobs bekommt, soll diese Arbeit NICHT beim
        # Start bezahlen — sonst verschoebe der Umzug die E2-Tempo-Messung, ohne
        # dass an der Analyse etwas anders waere.
        self._holen = rechner_holen
        self.geraet = geraet
        self._rechner = None
        self._emb = None
        self._nm = None
        self._echt = None
        self._schloss = threading.Lock()

    @property
    def rechner(self):
        if self._rechner is None:
            self._rechner = self._holen()
        return self._rechner

    def embedder(self, *_a, **kw):
        with self._schloss:
            modell = str(kw.get("modell") or face_audit.aktuelles_modell()).lower()
            if self._emb is None or self._emb.modell != modell:
                self._emb = EngineEmbedder(self.rechner, modell=modell)
            return self._emb.zuruecksetzen()

    def normmass(self, *_a, **kw):
        with self._schloss:
            modell = str(kw.get("modell") or face_audit.aktuelles_modell()).lower()
            if self._nm is None or self._nm.modell != modell:
                self._nm = EngineNormMass(self.rechner, self.geraet, modell=modell)
            return self._nm

    def einhaengen(self):
        """`face_audit.Embedder` und `face_audit.NormMass` auf diese Fabrik umbiegen.
        Rueckgabe: die eingehaengte Fabrik (fuer die Auskunft in der Job-Antwort).

        DIE KLASSEN-ATTRIBUTE MUESSEN MITKOMMEN, und das ist kein Schoenheitsgriff:
        `worker_kern.det_geometrie` ruft zur LAUFZEIT `face_audit.Embedder
        .ar_det_size(W, H)` — steht dort nach dem Umbiegen eine nackte Funktion, stirbt
        der Bau JEDER Geometrie an einem AttributeError, also der Analyse-Weg an einem
        Umbau, der ihn gar nicht betrifft. Gehaengt werden deshalb die Attribute, die
        im Haus an der KLASSE gelesen werden (grep ueber *.py): `ar_det_size`,
        `instanzen` (tools/qs_live_stufe.py:414) und auf der Norm-Seite
        `kette_fuer_backend`/`NORM_KETTE` (core/rechenprobe). Sie zeigen auf die
        ECHTEN Originale — sie sind reine Zahlen- und Namens-Auskunft und haben mit
        dem Rechenweg nichts zu tun."""
        if self._echt is not None:
            return self
        echt_emb, echt_nm = face_audit.Embedder, face_audit.NormMass
        self._echt = (echt_emb, echt_nm)

        def _emb_fabrik(*a, **kw):
            return self.embedder(*a, **kw)

        def _nm_fabrik(*a, **kw):
            return self.normmass(*a, **kw)

        for name in ("ar_det_size", "instanzen", "BATCH_STUFEN"):
            if hasattr(echt_emb, name):
                setattr(_emb_fabrik, name, getattr(echt_emb, name))
        for name in ("kette_fuer_backend", "NORM_KETTE", "NORM_KREUZ_MAX"):
            if hasattr(echt_nm, name):
                setattr(_nm_fabrik, name, getattr(echt_nm, name))
        face_audit.Embedder = _emb_fabrik
        face_audit.NormMass = _nm_fabrik
        return self

    def auskunft(self):
        """Was der Bild-Weg WIRKLICH haelt — an den Objekten abgelesen. Solange
        niemand ihn gebraucht hat, steht hier `gebaut: false`, nicht eine Behauptung
        ueber Stufen, die es noch gar nicht gibt."""
        if self._rechner is None:
            return {"embedder": "engine", "normmass": "engine", "gebaut": False}
        return {"embedder": "engine", "normmass": "engine", "gebaut": True,
                "modell": (self._emb.modell if self._emb else None),
                **self._rechner.stufen.auskunft()}


# ----------------------------------------------------------------- Die Rechenwerk-Kennung
# Bauplan analysen/bauplan_refquelle_einbau.md, Stufe E3 Punkt 1, Schnitt E3a-1a (Entscheid J5,
# O555 d); Felder und Vergleich: core/refquelle/basis.py ENGINE_FIELDS und ENGINE_COMPARED.
# WARUM HIER: diese Datei kennt beide Rechenwege — den Engine-Weg (EngineEmbedder, ueber die
# Bild-Stufen der Engine) und face_audit.Embedder, den sie selbst als Vorbild nachbaut;
# face_audit kennt den Engine-Weg nicht. Der Helfer liest nur die Engine-Auskunft
# (`BildStufen.identity()` jeder der vier Engine-Dateien) und die Attribute des Embedders, er
# importiert keine Engine-Datei und rechnet nichts ausser der Pruefsumme der Modelldatei.
#
# DIE TEXTFORMEN (EINE Stelle; erzeugt werden sie in den Engines bzw. unten fuer face_audit).
# Der Kennungsvergleich des Moduls vergleicht Texte: zwei Prozesse mit gleichem Rechenwerk
# liefern denselben Text, ein anderes Rechenwerk einen anderen.
#   Feld         ov (gpu, gpu-legacy)          cuda                        rocm (migraphx)
#   genauigkeit  Typname am r-Kompilat         Typ der geladenen r-Datei   Typ der geladenen r-Datei
#                (INFERENCE_PRECISION_HINT):   „fp16“ / „fp32“             „fp16“ / „fp32“
#                „f16“, „f32“
#   bibliothek   „openvino <Version>“          „onnxruntime <Version> <Provider der r-Session>“ (beide)
#   geraet       „GPU“ (kein Rueckfall)        „<Provider>:<device_id>“    „migraphx:<Nummer>“, Teil auf
#                                              der r-Session               der CPU „…+cpu“, sonst „cpu“
#   batch        Breite des Bild-Wegs (1)      dito                        dito
#   Feld         cpu                                   face_audit (alle Varianten)
#   genauigkeit  precision-Option des OpenVINO-CPU-    OpenVINO-Provider: precision-Option der
#                Providers („FP32“), abgelehnt         Session, ohne Option „Voreinstellung <Geraet>“,
#                „Voreinstellung CPU“, nackter CPU-    stellt die Session keine Optionen aus:
#                Provider: Typ der r-Datei („fp32“)    „unbekannt“; andere Provider: Eingangstyp der
#                                                      Session („tensor(float)“, „tensor(float16)“)
#   bibliothek   „onnxruntime <Version> <Provider>“    „onnxruntime <Version> <Provider der Session>“
#   geraet       „openvino:CPU“ oder „cpu“             „<Provider>:<device_type oder device_id>“,
#                                                      CPU-Provider „CPUExecutionProvider“, nicht
#                                                      lesbar „<Provider>:unbekannt“
#   batch        Breite des Bild-Wegs (1)              Parameter des Aufrufers, sonst „unbekannt“
# Alle Wege: modell = emb.modell; modell_sha256 = sha256 der geladenen r-Datei; modell_quelle_sha256 =
# sha256 der Quelldatei des Modells aus der Registry (Fix 0.1.1.013 Nachtrag 4: fuer jedes Rechenwerk
# gleich, auch wenn es eine abgeleitete Fassung laedt; das Modell-Sieb vergleicht sie); rechenweg
# „engine“ bzw. „face_audit“ (nie die Marke des Altbestands, die vergibt nur der Umzug);
# image_variante = SUSLIK_VARIANT, ohne sie „ohne Image“.
#
# EHRLICHE GRENZEN:
#   - „unbekannt“ (gemessen 07.10.2026 an onnxruntime-openvino 1.24.1): eine Session auf dem
#     OpenVINO-Provider gibt ihre Optionen nicht heraus (`get_provider_options()` liefert fuer
#     ihn ein leeres dict). Auf dem face_audit-Weg mit OpenVINO sind Geraet und Genauigkeit
#     deshalb nicht ablesbar; dort stehen sie als „unbekannt“, und zwei solche Rechenwerke auf
#     verschiedenen Intel-Geraeten saehe der Vergleich als gleich.
#   - Die Bibliothek nennt Paket und Provider, nicht Treiber oder CUDA/cuDNN-Stand.
#   - Die Pruefsumme gilt fuer den Pfad: wird die Datei waehrend des Prozesses ersetzt, bleibt
#     die erste Summe stehen (einmal je Prozess und Pfad, O555 d).
WAY_ENGINE, WAY_FACE_AUDIT = "engine", "face_audit"
UNKNOWN = "unbekannt"
NO_IMAGE = "ohne Image"
VARIANT_ENV = "SUSLIK_VARIANT"
ENGINE_INFO_KEYS = ("genauigkeit", "bibliothek", "modell_pfad", "geraet", "breite")
OV_PROVIDER, CPU_PROVIDER = "OpenVINOExecutionProvider", "CPUExecutionProvider"
_MODEL_SHA = {}                                           # absoluter Pfad -> sha256 (Hex)
_MODEL_SHA_LOCK = threading.Lock()


def _identity_fail(text):
    """Laut ablehnen: ERROR ins Log, dann RuntimeError mit Grund. -> kehrt nie zurueck"""
    _log.error(text)
    raise RuntimeError(text)


def _model_sha256(path):
    """sha256 der Modelldatei, einmal je Prozess und Pfad gerechnet und gemerkt (O555 d).
    -> Hex-Text"""
    key = os.path.abspath(path)
    with _MODEL_SHA_LOCK:
        if key not in _MODEL_SHA:
            h = hashlib.sha256()
            try:
                with open(key, "rb") as f:
                    for block in iter(lambda: f.read(1 << 20), b""):
                        h.update(block)
            except OSError as e:
                _identity_fail(f"engine identity: model file {key} not readable "
                               f"({type(e).__name__}: {e})")
            _MODEL_SHA[key] = h.hexdigest()
            _log.info(f"engine identity: checksum of the model file {key} computed "
                      f"(once per process)")
        return _MODEL_SHA[key]


def _model_source_sha256(modell):
    """Pruefsumme der Quelldatei eines Erkennungsmodells (Fix 0.1.1.013 Nachtrag 4, Eigentuemer 12.10.2026 20:09:55): der
    Eintrag der Registry mit task recognition und diesem modell_schluessel, die Datei im Image, sonst im Repo
    (worker_kern.modell_pfad), fuer jedes Rechenwerk gleich; einmal je Prozess und Pfad gerechnet wie _model_sha256.
    -> Hex-Text; kein Eintrag oder keine Datei: lauter Fehler (RuntimeError mit Grund)"""
    from core.registry import MODELL_VERTRAG as _mv          # noqa: PLC0415  nur die Pfade der Modelle
    keys = [k for k, v in _mv.items() if v.get("task") == "recognition" and v.get("modell_schluessel") == modell]
    if len(keys) != 1:
        _identity_fail(f"engine identity: the registry names {len(keys)} recognition model file(s) for the model "
                       f"{modell!r} (needs exactly one)")
    try:
        path = wk.modell_pfad(keys[0])
    except StopIteration:
        _identity_fail(f"engine identity: the source file of the model {modell!r} ({keys[0]}) lies neither in the "
                       "image nor in the repository")
    return _model_sha256(path)


def _engine_side(emb):
    """Der Engine-Weg: die Auskunft der Bild-Stufen, unveraendert uebernommen.
    -> dict modell_pfad, rechenweg, geraet, genauigkeit, bibliothek, batch"""
    ask = getattr(emb.rechner.stufen, "identity", None)
    if ask is None:
        _identity_fail("engine identity: the image path of this engine gives no identity "
                       "(BildStufen.identity missing)")
    info = ask()
    missing = [k for k in ENGINE_INFO_KEYS if info.get(k) in (None, "")]
    if missing:
        _identity_fail(f"engine identity: the engine identity lacks {', '.join(missing)}")
    return {"modell_pfad": info["modell_pfad"], "rechenweg": WAY_ENGINE,
            "geraet": info["geraet"], "genauigkeit": info["genauigkeit"],
            "bibliothek": info["bibliothek"], "batch": info["breite"]}


def _face_audit_session(emb):
    """Die Erkennungs-Session, die face_audit.Embedder wirklich haelt, und ihre Modelldatei:
    eigener Kopf (adaface, `_rec`) oder das insightface-Modell `recognition` (buffalo).
    -> (Session, Pfad)"""
    if getattr(emb, "_rec", None) is not None:
        return emb._rec, emb._rec_spec["onnx"]
    rec = emb.app.models.get("recognition")
    sess, path = getattr(rec, "session", None), getattr(rec, "model_file", None)
    if sess is None or not path:
        _identity_fail("engine identity: this face_audit embedder holds no recognition session")
    return sess, path


def _face_audit_side(emb, batch):
    """Der face_audit-Weg: Provider, Optionen und Eingangstyp an der Erkennungs-Session.
    -> dict modell_pfad, rechenweg, geraet, genauigkeit, bibliothek, batch"""
    import onnxruntime as ort                              # noqa: PLC0415  die Session ist schon da
    sess, path = _face_audit_session(emb)
    provider = sess.get_providers()[0]
    opts = (sess.get_provider_options() or {}).get(provider) or {}
    device = opts.get("device_type") or opts.get("device_id")
    if provider == OV_PROVIDER:
        precision = (opts.get("precision") or f"Voreinstellung {device or UNKNOWN}") if opts \
            else UNKNOWN
    else:
        precision = sess.get_inputs()[0].type
    geraet = (provider if provider == CPU_PROVIDER
              else f"{provider}:{device if device not in (None, '') else UNKNOWN}")
    return {"modell_pfad": path, "rechenweg": WAY_FACE_AUDIT, "geraet": geraet,
            "genauigkeit": precision, "bibliothek": f"onnxruntime {ort.__version__} {provider}",
            "batch": UNKNOWN if batch is None else batch}


def engine_identity(emb, batch=None):
    """Die Rechenwerk-Kennung eines Embedders (EngineEmbedder oder face_audit.Embedder) mit den
    neun Feldern aus core/refquelle/basis.py ENGINE_FIELDS, keins davon None oder leer.
    -> dict; ein Rechenwerk, das die Auskunft nicht geben kann, ist ein lauter Fehler
    (RuntimeError mit Grund). `batch` nur auf dem face_audit-Weg (Stufe und aufgefuellte
    Zeilen je Aufruf, wie `_rec_infer` sie bildet); auf dem Engine-Weg kommt die Breite aus der
    Engine, ein mitgegebener Wert ist dort ein Fehler."""
    if isinstance(emb, EngineEmbedder):
        if batch is not None:
            _identity_fail("engine identity: on the engine way the batch comes from the engine, "
                           "not from the caller")
        side = _engine_side(emb)
    elif type(emb).__name__ == "Embedder" and type(emb).__module__ == face_audit.__name__:
        if batch is not None and (isinstance(batch, bool) or batch == ""
                                  or not isinstance(batch, (int, str))):
            _identity_fail(f"engine identity: batch must be a number or a text, not {batch!r}")
        side = _face_audit_side(emb, batch)
    else:
        _identity_fail(f"engine identity: unknown embedder {type(emb).__module__}."
                       f"{type(emb).__name__}")
    if not emb.modell:
        _identity_fail("engine identity: the embedder names no model")
    return {"modell": emb.modell, "modell_sha256": _model_sha256(side["modell_pfad"]),
            "modell_quelle_sha256": _model_source_sha256(emb.modell),
            "rechenweg": side["rechenweg"],
            "image_variante": os.environ.get(VARIANT_ENV) or NO_IMAGE,
            "geraet": side["geraet"], "genauigkeit": side["genauigkeit"],
            "bibliothek": side["bibliothek"], "batch": side["batch"]}


def model_identity(modell):
    """Die Modell-Kennung eines Erkennungsmodells ohne Engine und ohne Bau: genau die zwei Felder, nach denen das
    Modell-Sieb entscheidet (Name, Pruefsumme der Quelldatei aus der Registry; wie in engine_identity).
    -> dict modell, modell_quelle_sha256; ohne Namen, Registry-Eintrag oder Datei ein lauter Fehler (RuntimeError)

    Bauplan analysen/bauplan_fix_erststart.md, Stufe K1 Punkt 1: der Worker liest beim Start mit dieser Kennung, damit
    vor der ersten Geometrie kein Bild-Weg und kein Kompilat entsteht. Der Name wird klein geschrieben wie im
    EngineEmbedder, damit er dem Feld modell der Rechenwerk-Kennung gleicht."""
    name = str(modell or "").strip().lower()
    if not name:
        _identity_fail("model identity: no model name given")
    return {"modell": name, "modell_quelle_sha256": _model_source_sha256(name)}
