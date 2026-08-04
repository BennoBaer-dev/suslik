"""core/personmodell — PE3: Training im Dienst (stufe2.md, User-Go 04.08.).

Trainiert nach jedem Review-Abschluss (und nach Loeschungen) aus dem
ABGENOMMENEN Material: DINOv2-ONNX-Embeddings (Einback-Etappe, onnxruntime,
kein torch) + SVM (Familien-Sieger der Messreihe) bei >=2 Personen; bei
EINER Person Referenz-Embeddings (Kosinus-Weg). Sekunden auf CPU.

EHRLICHE GRENZE (Status sagt es dem User): die Kipp-Schwelle braucht
Fremd-Negative — die sammelt der Fremd-Weg einer spaeteren Etappe. Bis
dahin ist der Modell-Stand vorbereitet, aber NICHT scharf (Aktivierungs-
Gate bleibt zu; der Live-Strang PE4 existiert ohnehin noch nicht).

Ablage: <data_dir>/personlern/modell/ (embeddings.npz, svm.pkl,
status.json — atomar)."""
import glob
import json
import os
import time

import numpy as np

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
GROESSE = (126, 252)          # Mess-Konvention der ganzen Stufe-2-Reihe


def modell_dir(data_dir):
    return os.path.join(data_dir, "personlern", "modell")


def status_lesen(data_dir):
    p = os.path.join(modell_dir(data_dir), "status.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def _dino_pfad():
    for k in (os.environ.get("SUSLIK_DINO") or "",
              "/app/modelle/dinov2_vits14_126x252.onnx",
              os.path.join(WURZEL, "modelle",
                           "dinov2_vits14_126x252.onnx")):
        if k and os.path.exists(k):
            return k
    raise RuntimeError("DINOv2-ONNX fehlt (modelle/)")


def _emb(pfade):
    import onnxruntime as ort
    from PIL import Image
    s = ort.InferenceSession(_dino_pfad(),
                             providers=["CPUExecutionProvider"])
    embs = []
    for i in range(0, len(pfade), 16):
        batch = []
        for p in pfade[i:i + 16]:
            im = np.asarray(Image.open(p).convert("RGB").resize(GROESSE),
                            dtype=np.float32) / 255.0
            batch.append(((im - MEAN) / STD).transpose(2, 0, 1))
        e = s.run(None, {"bild": np.stack(batch)})[0]
        embs.append(e / np.linalg.norm(e, axis=1, keepdims=True))
    return np.concatenate(embs) if embs else np.zeros((0, 384))


def trainieren(data_dir):
    """Voll-Training aus dem abgenommenen Bestand. Rueckgabe: status-dict."""
    from core import personernte as pe
    t0 = time.time()
    pfade, labels = [], []
    for lid, zeilen in pe.laeufe_lesen(data_dir):
        for z in zeilen:
            if "ausfall" in z or z.get("status") != "abgenommen":
                continue
            p = os.path.join(pe.lauf_dir(data_dir, lid), "crops",
                             z["datei"])
            if os.path.exists(p):
                pfade.append(p)
                labels.append(z["person"])
    md = modell_dir(data_dir)
    os.makedirs(md, exist_ok=True)
    personen = sorted(set(labels))
    alt = status_lesen(data_dir) or {}
    status = {"ts": time.time(), "bilder": len(pfade),
              "personen": {p: labels.count(p) for p in personen},
              # Scharf-Zustand + Schwelle UEBERLEBEN ein Re-Training —
              # aber nur, solange Material da ist (sonst zwangs-entschaerft)
              "scharf": bool(alt.get("scharf")) and bool(pfade),
              **({"schwelle": alt["schwelle"]} if alt.get("schwelle")
                 else {}),
              "hinweis": ("threshold not yet calibrated against stranger "
                          "material — alerts are a preview; arm/disarm "
                          "under Person → Model status")}
    if not pfade:
        status["modell"] = "leer"
    else:
        X = _emb(pfade)
        np.savez(os.path.join(md, "embeddings.npz"), X=X,
                 labels=np.array(labels))
        if len(personen) >= 2:
            from sklearn.svm import SVC
            import pickle
            y = np.array([personen.index(l) for l in labels])
            m = SVC(probability=True, class_weight="balanced",
                    random_state=7)
            m.fit(X, y)
            with open(os.path.join(md, "svm.pkl"), "wb") as f:
                pickle.dump({"personen": personen, "svm": m}, f)
            status["modell"] = f"svm ({len(personen)} classes)"
        else:
            for alt in glob.glob(os.path.join(md, "svm.pkl")):
                os.remove(alt)
            status["modell"] = "reference embeddings (1 person)"
    status["dauer_s"] = round(time.time() - t0, 1)
    tmp = os.path.join(md, "status.json.tmp")
    with open(tmp, "w") as f:
        json.dump(status, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, os.path.join(md, "status.json"))
    return status


def scharf_setzen(data_dir, an):
    """PE4 Aktivierungs-Gate: scharf nur mit vorhandenem Modell (>=1 Person
    gelernt+reviewed). Rueckgabe: (ok, status|fehlertext)."""
    status = status_lesen(data_dir)
    if an and not (status and status.get("bilder")):
        return False, "learn and review at least one person first"
    status = status or {}
    status["scharf"] = bool(an)
    md = modell_dir(data_dir)
    os.makedirs(md, exist_ok=True)
    tmp = os.path.join(md, "status.json.tmp")
    with open(tmp, "w") as f:
        json.dump(status, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, os.path.join(md, "status.json"))
    return True, status
