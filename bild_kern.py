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
import threading

import worker_kern as wk                                 # noqa: E402  Bootstrap + BLAS-Pin
import numpy as np                                         # noqa: E402  (schon vom Kern geladen)
import cv2                                                 # noqa: E402  (ebenso)

import face_audit                                          # noqa: E402  Modell-Spec, ar_det_size


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
