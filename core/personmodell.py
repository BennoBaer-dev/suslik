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


def _status_schreiben(data_dir, status):
    """Atomar + fsync — EIN Schreibweg fuer alle drei Schreiber
    (trainieren / scharf_setzen / einstellungen_setzen)."""
    md = modell_dir(data_dir)
    os.makedirs(md, exist_ok=True)
    tmp = os.path.join(md, "status.json.tmp")
    with open(tmp, "w") as f:
        json.dump(status, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, os.path.join(md, "status.json"))


# Feuer-Regel-Grenzen (Eingabe-Validierung der UI; Werte leben in status.json,
# die Standardwerte beim Weglassen definiert core/personlive)
REGEL_GRENZEN = {"schwelle": (0.50, 0.99), "fenster_s": (60, 3600),
                 "feuer_ab": (1, 10), "karenz_s": (0, 7200)}
EICH_MARGE = 0.02             # Abstand ueber dem staerksten Falsch-Wert


def _eichung(X, y, k_max=5):
    """Schwellen-Eichung per Kreuz-Validierung AUF DEM GELERNTEN MATERIAL:
    je Haltefalte urteilt ein frisch trainiertes Modell ueber ungesehene
    Bilder. fremd_max = staerkste Zuversicht fuer eine FALSCHE Person
    (deckt Fehlklassifikationen mit ab) -> Schwelle = fremd_max + Marge.
    EHRLICHE GRENZE: das eicht zwischen den GELERNTEN Personen — echte
    Fremde sind nicht im Material und bleiben ein offener Punkt."""
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.svm import SVC
    klassen, anz = np.unique(y, return_counts=True)
    k = int(min(k_max, anz.min()))
    if len(klassen) < 2 or k < 2:
        return None
    proba = cross_val_predict(
        SVC(probability=True, class_weight="balanced", random_state=7),
        X, y, method="predict_proba",
        cv=StratifiedKFold(k, shuffle=True, random_state=7))
    eigen = proba[np.arange(len(y)), y]
    falsch = proba.copy()
    falsch[np.arange(len(y)), y] = 0.0
    fremd_max = float(falsch.max())
    lo, hi = REGEL_GRENZEN["schwelle"]
    schwelle = round(min(max(fremd_max + EICH_MARGE, lo), hi), 3)
    return {"schwelle": schwelle, "fremd_max": round(fremd_max, 3),
            "getragen_anteil": round(float((eigen >= schwelle).mean()), 3),
            "folds": k, "n": int(len(y))}


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
              # Scharf-Zustand + Regel-Werte UEBERLEBEN ein Re-Training —
              # aber nur, solange Material da ist (sonst zwangs-entschaerft)
              "scharf": bool(alt.get("scharf")) and bool(pfade),
              **{k: alt[k] for k in ("fenster_s", "feuer_ab", "karenz_s")
                 if alt.get(k) is not None},
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
            status["eichung"] = _eichung(X, y)
        else:
            for rest in glob.glob(os.path.join(md, "svm.pkl")):
                os.remove(rest)
            status["modell"] = "reference embeddings (1 person)"
    # Schwellen-Vorrang: user-gesetzt > Eichung > Standard (personlive)
    if alt.get("schwelle_quelle") == "user" and alt.get("schwelle"):
        status["schwelle"] = alt["schwelle"]
        status["schwelle_quelle"] = "user"
    elif status.get("eichung"):
        status["schwelle"] = status["eichung"]["schwelle"]
        status["schwelle_quelle"] = "eichung"
        status["hinweis"] = (
            "threshold measured by cross-validation BETWEEN the learned "
            "people — real strangers are not in the material yet, so keep "
            "an eye on alerts; arm/disarm under Person → Model status")
    elif alt.get("schwelle"):
        status["schwelle"] = alt["schwelle"]
        status["schwelle_quelle"] = alt.get("schwelle_quelle") or "standard"
    status["dauer_s"] = round(time.time() - t0, 1)
    _status_schreiben(data_dir, status)
    return status


def einstellungen_setzen(data_dir, d):
    """Feuer-Regel + Schwelle aus der UI (Model-status-Seite). Leeres
    schwelle-Feld = zurueck auf Auto (Eichung, sonst Standard). Rueckgabe
    (ok, status|fehlertext)."""
    status = status_lesen(data_dir)
    if not status:
        return False, "no model yet — learn and review first"
    for k in ("fenster_s", "feuer_ab", "karenz_s", "schwelle"):
        if k not in d:
            continue
        v = d[k]
        if v in ("", None):                       # Feld geleert = Auto/Standard
            if k == "schwelle" and status.get("eichung"):
                status["schwelle"] = status["eichung"]["schwelle"]
                status["schwelle_quelle"] = "eichung"
            else:
                status.pop(k, None)
                if k == "schwelle":
                    status.pop("schwelle_quelle", None)
            continue
        try:
            v = float(v) if k == "schwelle" else int(v)
        except (TypeError, ValueError):
            return False, f"{k}: not a number"
        lo, hi = REGEL_GRENZEN[k]
        if not lo <= v <= hi:
            return False, f"{k}: allowed range {lo}–{hi}"
        status[k] = v
        if k == "schwelle":
            status["schwelle_quelle"] = "user"
    _status_schreiben(data_dir, status)
    return True, status


def scharf_setzen(data_dir, an):
    """PE4 Aktivierungs-Gate: scharf nur mit vorhandenem Modell (>=1 Person
    gelernt+reviewed). Rueckgabe: (ok, status|fehlertext)."""
    status = status_lesen(data_dir)
    if an and not (status and status.get("bilder")):
        return False, "learn and review at least one person first"
    status = status or {}
    status["scharf"] = bool(an)
    _status_schreiben(data_dir, status)
    return True, status
