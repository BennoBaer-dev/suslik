"""core/personlive — PE4: Live-Urteil des Koerper-Strangs (stufe2.md).

Bewusst LEICHT: kein Clip-Decode im Live-Weg — je Event EIN Urteil aus
Frigates snapshot-clean + data.box (dieselbe Quelle wie die Prototyp-Kette).
Kette: Personen-Crop -> DINOv2-ONNX (Session gecacht) -> SVM-proba.

FEUER-REGEL (User-Anforderung): gemeldet wird erst, wenn im Fenster
(FENSTER_S) mindestens FEUER_AB Events derselben Person ueber der Schwelle
lagen; danach Karenz je Person (KARENZ_S). Zustand liegt geflusht in
<data_dir>/personlern/live_fenster.json — uebersteht Neustarts.

EHRLICHE GRENZE: die Schwelle ist noch NICHT an Fremd-Material geeicht
(Standard konservativ 0.85, konfigurierbar ueber status.json/schwelle).
Der Strang laeuft nur, wenn der User ihn auf /person/modell scharf
geschaltet hat (Aktivierungs-Gate)."""
import io
import json
import os
import time
import urllib.request

import numpy as np

FENSTER_S = 600
FEUER_AB = 2
KARENZ_S = 900
SCHWELLE_STD = 0.85
RAND = 0.08                 # wie szenario_ernte.crop_holen (Framing!)

_CACHE = {"sess": None, "svm": None, "svm_mtime": None}


def _fenster_pfad(data_dir):
    return os.path.join(data_dir, "personlern", "live_fenster.json")


def _fenster_lesen(data_dir):
    p = _fenster_pfad(data_dir)
    if not os.path.exists(p):
        return {"treffer": [], "karenz": {}}
    try:
        return json.load(open(p))
    except (ValueError, OSError):
        return {"treffer": [], "karenz": {}}


def _fenster_schreiben(data_dir, f):
    p = _fenster_pfad(data_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(f, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)


def _svm(data_dir):
    import pickle
    from core.personmodell import modell_dir
    p = os.path.join(modell_dir(data_dir), "svm.pkl")
    if not os.path.exists(p):
        return None
    mt = os.path.getmtime(p)
    if _CACHE["svm"] is None or _CACHE["svm_mtime"] != mt:
        with open(p, "rb") as f:
            _CACHE["svm"] = pickle.load(f)
        _CACHE["svm_mtime"] = mt
    return _CACHE["svm"]


def _emb1(bild_rgb):
    from core.personmodell import _dino_pfad, MEAN, STD, GROESSE
    from PIL import Image
    if _CACHE["sess"] is None:
        import onnxruntime as ort
        _CACHE["sess"] = ort.InferenceSession(
            _dino_pfad(), providers=["CPUExecutionProvider"])
    im = np.asarray(Image.fromarray(bild_rgb).resize(GROESSE),
                    dtype=np.float32) / 255.0
    x = ((im - MEAN) / STD).transpose(2, 0, 1)[None]
    e = _CACHE["sess"].run(None, {"bild": x.astype(np.float32)})[0]
    return (e / np.linalg.norm(e, axis=1, keepdims=True))[0]


def urteilen(data_dir, frigate_url, eid, schwelle=None):
    """EIN Event beurteilen. Rueckgabe: dict(person, score, feuer:bool)
    oder None (kein Modell / kein Snapshot / unter Schwelle ohne Feuer).
    feuer=True heisst: Feuer-Regel erfuellt UND Karenz frei -> MELDEN."""
    from core.personmodell import status_lesen
    status = status_lesen(data_dir)
    if not status or not status.get("scharf"):
        return None
    m = _svm(data_dir)
    if m is None:
        return None
    schwelle = float(schwelle or status.get("schwelle") or SCHWELLE_STD)
    try:
        from PIL import Image
        with urllib.request.urlopen(
                f"{frigate_url.rstrip('/')}/api/events/{eid}", timeout=15) as r:
            ev = json.loads(r.read())
        box = (ev.get("data") or {}).get("box")
        if not box:
            return None
        with urllib.request.urlopen(
                f"{frigate_url.rstrip('/')}/api/events/{eid}/snapshot-clean.webp",
                timeout=15) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGB")
    except Exception:
        return None
    W, H = im.size
    x, y, w, h = box
    l = max(0, int((x - RAND * w) * W))
    t = max(0, int((y - RAND * h) * H))
    rt = min(W, int((x + w * (1 + RAND)) * W))
    bb = min(H, int((y + h * (1 + RAND)) * H))
    if bb - t < 60:
        return None
    crop = im.crop((l, t, rt, bb))
    e = _emb1(np.asarray(crop))
    proba = m["svm"].predict_proba(e[None])[0]
    k = int(np.argmax(proba))
    person, score = m["personen"][k], float(proba[k])
    if score < schwelle:
        return None
    # Treffer-Bild je Event ablegen — beim Feuern gewinnt das BESTE Bild des
    # Fensters (groesster Crop), nicht das zufaellige Bild des Feuer-Moments
    # (User-Fund 04.08.: Meldung trug einen 60x140-Fernkamera-Crop, waehrend
    # derselbe Durchgang 312x791 hatte — Szenario-Prinzip gilt auch hier).
    bild_dir = os.path.join(data_dir, "personlern", "live_fenster")
    os.makedirs(bild_dir, exist_ok=True)
    bild = os.path.join(bild_dir, str(eid).replace("/", "_") + ".jpg")
    try:
        crop.save(bild, "JPEG", quality=88)
        px = crop.size[0] * crop.size[1]
    except OSError:
        bild, px = None, 0
    jetzt = time.time()
    f = _fenster_lesen(data_dir)
    raus = [t2 for t2 in f["treffer"] if jetzt - t2["ts"] > FENSTER_S]
    f["treffer"] = [t2 for t2 in f["treffer"]
                    if jetzt - t2["ts"] <= FENSTER_S]
    for t2 in raus:                     # Crop-Dateien ausgelaufener Treffer
        if t2.get("bild"):
            try:
                os.remove(t2["bild"])
            except OSError:
                pass
    f["treffer"].append({"ts": jetzt, "person": person, "eid": eid,
                         "score": round(score, 3), "bild": bild, "px": px})
    n = sum(1 for t2 in f["treffer"] if t2["person"] == person)
    karenz_bis = float(f["karenz"].get(person) or 0)
    feuer = n >= FEUER_AB and jetzt >= karenz_bis
    if feuer:
        f["karenz"][person] = jetzt + KARENZ_S
        beste = max((t2 for t2 in f["treffer"]
                     if t2["person"] == person and t2.get("bild")
                     and os.path.isfile(t2["bild"])),
                    key=lambda t2: t2.get("px", 0), default=None)
        if beste:
            bild = beste["bild"]
    _fenster_schreiben(data_dir, f)
    return {"person": person, "score": round(score, 3), "stuetzen": n,
            "feuer": feuer, "bild": bild}
