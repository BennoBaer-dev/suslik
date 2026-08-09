"""core/personmodell — PE3: Training im Dienst (stufe2.md, User-Go 04.08.).

Trainiert nach jedem Review-Abschluss (und nach Loeschungen) aus dem
ABGENOMMENEN Material: DINOv2-ONNX-Embeddings (Einback-Etappe, onnxruntime,
kein torch) + SVM (Familien-Sieger der Messreihe) bei >=2 Personen; bei
EINER Person Referenz-Embeddings (Kosinus-Weg). Sekunden auf CPU.

FREMD-KLASSE (.139, Erkennungs-Review Baustein 1): liegen unter
<data_dir>/personlern/fremd/ bestaetigte Fremd-Bilder, lernt das SVM sie
als EIGENE Klasse hinter den Personen (Label-Index len(personen)) und die
Schwelle wird gegen ECHTE Fremde geeicht statt nur zwischen den gelernten
Personen. Ohne dieses Material gilt unveraendert die alte Regel — der
Status sagt in beiden Faellen ehrlich, wogegen geeicht wurde.

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


def fremd_dir(data_dir):
    """Fremd-Pool (.139): flacher Ordner mit BESTAETIGTEN Fremd-Bildern —
    Negativ-Klasse des Personen-Pfads und Eich-Material der Schwelle."""
    return os.path.join(data_dir, "personlern", "fremd")


# Der Ordner ist HAND-befuellt (einziger user-beschriebener Bild-Ort im
# Personen-Pfad) — deshalb tolerant lesen: .jpg/.jpeg/.png in jeder
# Schreibung (.141 Panel-Hinweis: 55 Bilder als .JPG sahen aus wie ein
# leerer Ordner), nur echte Dateien (ein Unterordner 'x.jpg' zaehlt nicht).
FREMD_ENDUNGEN = (".jpg", ".jpeg", ".png")


def fremd_pfade(data_dir):
    """Sortiert = reproduzierbares Training (gleiche Reihenfolge, gleiches
    Modell). Flach — kein Unterordner-Vertrag."""
    d = fremd_dir(data_dir)
    try:
        namen = os.listdir(d)
    except OSError:
        return []
    return sorted(os.path.join(d, n) for n in namen
                  if n.lower().endswith(FREMD_ENDUNGEN)
                  and os.path.isfile(os.path.join(d, n)))


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
FREMD_MIN = 5                 # weniger bestaetigte Fremde fuellen die 5 Falten
                              # nicht -> sie bleiben KOMPLETT draussen (.141:
                              # Training UND Eichung — nie zwei Wahrheiten)
EICH_SEEDS = (7, 17, 27)      # drei feste Faltenaufteilungen gegen die
                              # Einzellos-Unruhe der Schwelle (.141)


def _eichung(X, y, k_max=5, k_fremd=None):
    """Schwellen-Eichung per Kreuz-Validierung AUF DEM GELERNTEN MATERIAL:
    je Haltefalte urteilt ein frisch trainiertes Modell ueber ungesehene
    Bilder.

    OHNE Fremd-Material (k_fremd=None, Rueckwaerts-Vertrag): fremd_max =
    staerkste Zuversicht fuer eine FALSCHE Person -> Schwelle = fremd_max
    + Marge. Ehrliche Grenze: das eicht nur ZWISCHEN den gelernten Personen.

    MIT Fremd-Klasse (.139, k_fremd = deren Label-Index): das CV enthaelt
    die Fremden als eigene Klasse; Schwelle = staerkste BEWOHNER-Zuversicht,
    die irgendein echter Fremder in einer Haltefalte bekam, + Marge. Dazu
    die ehrliche Kehrseite im Status: getragen_anteil zaehlt NUR ueber
    Bewohner-Samples, verwechslung_max/-_ueber_n sagen, wieviel Bewohner-
    Material unter dieser Latte einer FALSCHEN Person zugeschlagen wuerde.
    Unter FREMD_MIN Fremden fallen wir auf die alte Regel zurueck (Falten
    nicht fuellbar) und vermerken n_fremd, damit der Status nicht luegt."""
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.svm import SVC
    y = np.asarray(y)
    ist_fremd = (y == k_fremd) if k_fremd is not None \
        else np.zeros(len(y), dtype=bool)
    n_fremd = int(ist_fremd.sum())
    if k_fremd is not None and n_fremd < FREMD_MIN:
        e = _eichung(X[~ist_fremd], y[~ist_fremd], k_max)   # alte Regel
        if e:
            e["n_fremd"] = n_fremd
        return e
    klassen, anz = np.unique(y, return_counts=True)
    k = int(min(k_max, anz.min()))
    if len(klassen) < 2 or k < 2:
        return None
    lo, hi = REGEL_GRENZEN["schwelle"]
    if k_fremd is None:
        proba = cross_val_predict(
            SVC(probability=True, class_weight="balanced", random_state=7),
            X, y, method="predict_proba",
            cv=StratifiedKFold(k, shuffle=True, random_state=7))
        eigen = proba[np.arange(len(y)), y]
        falsch = proba.copy()
        falsch[np.arange(len(y)), y] = 0.0
        fremd_max = float(falsch.max())
        schwelle = round(min(max(fremd_max + EICH_MARGE, lo), hi), 3)
        return {"schwelle": schwelle, "fremd_max": round(fremd_max, 3),
                "getragen_anteil": round(float((eigen >= schwelle).mean()), 3),
                "folds": k, "n": int(len(y)), "art": "bewohner"}
    # .141 Panel-SOLL (Schwellen-Unruhe): die Schwelle hing am Maximum EINES
    # Fremd-Samples in EINER zufaelligen Faltenaufteilung (gemessen: Leave-
    # one-out bewegte die Abdeckung um >30 Punkte, zwei Laeufe derselben
    # Regel lagen 0.03 auseinander). Jetzt DREI feste Faltenaufteilungen:
    # fremd_echt_max = Maximum ueber alle drei (konservativ), die Bewohner-
    # Kennzahlen aus dem Mittel der drei Laeufe (glatter Schaetzer).
    # Spalten 0..k_fremd-1 sind die PERSONEN (Label-Index = Spalten-Index,
    # weil sklearn die Klassen sortiert und FREMD hinten haengt).
    probas = [cross_val_predict(
        SVC(probability=True, class_weight="balanced", random_state=seed),
        X, y, method="predict_proba",
        cv=StratifiedKFold(k, shuffle=True, random_state=seed))
        for seed in EICH_SEEDS]
    bew = ~ist_fremd
    y_bew = y[bew]
    fremd_echt_max = float(max(p[ist_fremd][:, :k_fremd].max()
                               for p in probas))
    schwelle = round(min(max(fremd_echt_max + EICH_MARGE, lo), hi), 3)
    p_bew = np.mean([p[bew][:, :k_fremd] for p in probas], axis=0)
    eigen = p_bew[np.arange(len(y_bew)), y_bew]
    falsch = p_bew.copy()
    falsch[np.arange(len(y_bew)), y_bew] = 0.0
    return {"schwelle": schwelle,
            "fremd_echt_max": round(fremd_echt_max, 3),
            "n_fremd": n_fremd,
            "getragen_anteil": round(float((eigen >= schwelle).mean()), 3),
            "verwechslung_max": round(float(falsch.max()), 3),
            "verwechslung_ueber_n": int((falsch.max(axis=1)
                                         >= schwelle).sum()),
            "folds": k, "n": int(len(y_bew)),
            "wiederholungen": len(EICH_SEEDS), "art": "fremd"}


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


def _bild_array(p):
    from PIL import Image
    im = np.asarray(Image.open(p).convert("RGB").resize(GROESSE),
                    dtype=np.float32) / 255.0
    return ((im - MEAN) / STD).transpose(2, 0, 1)


def _emb(pfade):
    """-> (X, ok_indices, uebersprungen). Je DATEI tolerant (.141 Panel-MUSS:
    eine einzige unlesbare Datei im hand-befuellten fremd/-Ordner — leere/
    abgebrochene Kopie, Nicht-Bild-Inhalt — legte sonst JEDES weitere
    Training still, und die Modell-Karte zeigte fuer immer den Alt-Stand als
    aktuell). Unlesbares wird uebersprungen und GEZAEHLT, nie ein stiller
    Verlust; der Aufrufer haelt seine Label-Liste ueber ok_indices synchron."""
    import onnxruntime as ort
    s = ort.InferenceSession(_dino_pfad(),
                             providers=["CPUExecutionProvider"])
    arrays, ok = [], []
    uebersprungen = 0
    for i, p in enumerate(pfade):
        try:
            arrays.append(_bild_array(p))
            ok.append(i)
        except Exception:
            uebersprungen += 1
    embs = []
    for i in range(0, len(arrays), 16):
        e = s.run(None, {"bild": np.stack(arrays[i:i + 16])})[0]
        embs.append(e / np.linalg.norm(e, axis=1, keepdims=True))
    X = np.concatenate(embs) if embs else np.zeros((0, 384))
    return X, ok, uebersprungen


def trainieren(data_dir):
    """Voll-Training aus dem abgenommenen Bestand. Rueckgabe: status-dict."""
    from core import personernte as pe
    t0 = time.time()
    pfade, labels = [], []
    for lid, zeilen in pe.laeufe_lesen(data_dir):
        for z in zeilen:
            if "ausfall" in z or z.get("status") != "abgenommen":
                continue
            if z.get("person") == "FREMD":
                # .147: bestaetigte Fremde traegt AUSSCHLIESSLICH der Pool
                # (fremd_pfade) — die Lauf-Zeile ist nur Beleg. Sonst
                # zaehlte dasselbe Bild doppelt (Personen-Klasse 'FREMD'
                # + Fremd-Klasse) und stuende als Person in der Tabelle.
                continue
            p = os.path.join(pe.lauf_dir(data_dir, lid), "crops",
                             z["datei"])
            if os.path.exists(p):
                pfade.append(p)
                labels.append(z["person"])
    md = modell_dir(data_dir)
    os.makedirs(md, exist_ok=True)
    personen = sorted(set(labels))
    fremde = fremd_pfade(data_dir)
    alt = status_lesen(data_dir) or {}
    status = {"ts": time.time(), "bilder": len(pfade),
              "personen": {p: labels.count(p) for p in personen},
              "fremd_bilder": len(fremde),
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
        X, ok, skip_p = _emb(pfade)
        labels = [labels[i] for i in ok]
        personen = sorted(set(labels))
        status["personen"] = {p: labels.count(p) for p in personen}
        status["bilder"] = len(labels)
        np.savez(os.path.join(md, "embeddings.npz"), X=X,
                 labels=np.array(labels))
        if len(personen) >= 2:
            from sklearn.svm import SVC
            import pickle
            y = np.array([personen.index(l) for l in labels])
            # .139: bestaetigte Fremde als EIGENE Klasse HINTER den Personen
            # (Label-Index len(personen)) — personen bleibt die reine
            # Personenliste, FREMD taucht nie in einer Meldung auf.
            # .141 Panel-SOLL: FREMD_MIN gilt fuer TRAINING UND Eichung —
            # vorher wurde die Klasse ab 1 Bild mittrainiert, die Schwelle
            # aber am Modell OHNE sie gemessen (gemessen: Karte versprach
            # 26.6% getragen, real waren es 7%). Unter der Grenze bleiben
            # die Fremden komplett draussen, Modell und Zahlen stimmen
            # wieder ueberein.
            skip_f = 0
            X_fr = np.zeros((0, X.shape[1] if len(X) else 384))
            if fremde:
                X_fr, _okf, skip_f = _emb(fremde)
            fremd_aktiv = len(X_fr) >= FREMD_MIN
            k_fremd = len(personen) if fremd_aktiv else None
            Xt, yt = X, y
            if fremd_aktiv:
                Xt = np.vstack([X, X_fr])
                yt = np.concatenate([y, np.full(len(X_fr), k_fremd)])
            m = SVC(probability=True, class_weight="balanced",
                    random_state=7)
            m.fit(Xt, yt)
            with open(os.path.join(md, "svm.pkl"), "wb") as f:
                pickle.dump({"personen": personen, "svm": m,
                             "fremd": fremd_aktiv}, f)
            status["modell"] = (f"svm ({len(personen)} classes"
                                + (" + strangers)" if fremd_aktiv else ")"))
            status["fremd_bilder"] = len(X_fr)
            status["fremd_trainiert"] = fremd_aktiv
            if skip_p or skip_f:
                status["unlesbar_uebersprungen"] = {"personen": skip_p,
                                                   "fremd": skip_f}
            status["eichung"] = _eichung(Xt, yt, k_fremd=k_fremd)
        else:
            for rest in glob.glob(os.path.join(md, "svm.pkl")):
                os.remove(rest)
            status["modell"] = "reference embeddings (1 person)"
            status["fremd_trainiert"] = False
    # Schwellen-Vorrang: user-gesetzt > Eichung > Standard (personlive)
    if alt.get("schwelle_quelle") == "user" and alt.get("schwelle"):
        status["schwelle"] = alt["schwelle"]
        status["schwelle_quelle"] = "user"
    elif status.get("eichung"):
        ei = status["eichung"]
        status["schwelle"] = ei["schwelle"]
        status["schwelle_quelle"] = "eichung"
        if "fremd_echt_max" in ei:
            status["hinweis"] = (
                f'threshold calibrated against {ei["n_fremd"]} confirmed '
                "strangers — no stranger in the cross-validation reached it; "
                "arm/disarm under Person → Model status")
        else:
            status["hinweis"] = (
                "threshold measured by cross-validation BETWEEN the learned "
                "people — real strangers are not in the training yet"
                + (f' ({status.get("fremd_bilder", 0)} stranger image(s) '
                   f"present, {FREMD_MIN} needed before they are trained "
                   "and calibrate the threshold)"
                   if status.get("fremd_bilder") else "")
                + ", so keep an eye on alerts; arm/disarm under Person → "
                  "Model status")
    elif alt.get("schwelle"):
        # .141 Panel-Hinweis: eine geerbte Eich-Schwelle OHNE frische Eichung
        # darf nicht weiter 'eichung' heissen — der Wert bleibt (Kontinuitaet),
        # die Quelle sagt ehrlich, dass er nicht auf DIESEM Modell gemessen ist.
        status["schwelle"] = alt["schwelle"]
        status["schwelle_quelle"] = ("user" if alt.get("schwelle_quelle")
                                     == "user" else "standard")
    status["dauer_s"] = round(time.time() - t0, 1)
    _status_schreiben(data_dir, status)
    return status


def fehler_vermerken(data_dir, text):
    """Ein fehlgeschlagener Trainingslauf wird SICHTBAR (.141 Panel-MUSS):
    vorher stand er nur als print im Container-Log, waehrend die Modell-Karte
    den alten Stand als aktuell zeigte ('deletions retrain automatically' —
    taten sie aber nicht mehr). Der Vermerk laesst alle Modell-Felder stehen
    (das ALTE Modell laeuft ja weiter) und wird vom naechsten erfolgreichen
    trainieren() geraeumt."""
    status = status_lesen(data_dir) or {}
    status["letzter_fehler"] = str(text)[:300]
    status["letzter_fehler_ts"] = round(time.time(), 1)
    _status_schreiben(data_dir, status)


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
