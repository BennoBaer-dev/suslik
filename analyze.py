#!/usr/bin/env python3
"""Verify-Prototyp: bestes FRONTALES Gesicht je Person aus einem oder mehreren
Kamera-Videos desselben Durchgangs.

Kern des Verify-Layers. Statt Frigates schwachem Live-Crop sucht dieses Tool SELBST
ueber alle Frames (buffalo_l), bewertet jedes Gesicht nach FRONTALITAET (frontal
schlaegt schraeg/Profil), Schaerfe und Groesse und matcht per Nearest-Neighbor gegen
die Referenzpersonen. Mehrere Kamera-Winkel -> bester Winkel gewinnt.

Frontalitaet: primär aus den 5 Landmarks (Nasen-Versatz gegen Augenmitte = yaw-Proxy,
robust und versionsunabhaengig). buffalo_l fc.pose [.,.,.] wird zur Info roh mitgezeigt.

Read-only gegen Frigate. Referenz-Embeddings gecacht (SCRATCH/refcache.npz, teilt
sich den Cache mit classify.py).

Aufruf:
  analyze.py <eid> [<eid> ...] [--dir samples/TestN] [--persons NAME1 NAME2]
             [--labels CAM1 CAM2 CAM3] [--fps-sample 2.0]

Backend-Wahl via face_audit.resolve_backend/core.registry (alle kinds: cpu, openvino, cuda, migraphx).
"""
import os, sys, json, socket, urllib.request, argparse, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from face_audit import Embedder, fetch_image, ist_fehldetektion
import numpy as np, cv2

socket.setdefaulttimeout(120)   # urlretrieve kennt kein timeout=; ohne Default haengt ein TCP-Stall ewig

FRIGATE = os.environ.get("FRIGATE_URL", "")
SCRATCH = os.environ.get("SCRATCH_DIR") or os.path.join(tempfile.gettempdir(), "suslik-scratch")
from core.pfade import WURZEL as HERE   # M0-Anker (Falle 0): eine Pfad-Quelle
os.makedirs(SCRATCH, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("eids", nargs="+")
ap.add_argument("--dir", default=None, help="Ausgabe-Ordner fuer Crops")
ap.add_argument("--persons", nargs="+", required=True)   # kein Default-Name; Runtime/qs uebergeben immer die Master-Personen
ap.add_argument("--labels", nargs="+", default=None, help="Anzeigename je eid (z.B. Kamera)")
ap.add_argument("--fps-sample", type=float, default=2.0)
ap.add_argument("--win-thresh", type=float, default=0.40,
                help="Frame-Schwelle fuer das 3s-Fenster (Default 0.40; 16.07. per Backtest auf 0.38 kalibriert)")
ap.add_argument("--timeline", action="store_true", help="Score-Zeitreihe je Gesicht-Frame ausgeben")
# #42 Teil B: Fehldetektions-Signatur (kalibriert, s. face_audit.ist_fehldetektion) + der
# bislang unsichtbare insightface-Default det_thresh=0.5 als sichtbarer Parameter (KEINE
# Empfehlung zum Hochdrehen: det>=0.60 kostete 15,9 % echter Gesichter — nur steuerbar machen).
ap.add_argument("--fd-front-min", type=float, default=0.85)
ap.add_argument("--fd-sharp-min", type=float, default=1500.0)
ap.add_argument("--fd-det-max", type=float, default=0.70)
ap.add_argument("--det-thresh", type=float, default=0.5)
a = ap.parse_args()

emb = Embedder()
# #42 Teil B, KORRIGIERT (Review .52, kritisch): det_thresh wird NICHT hier gesetzt.
# Grund 1: jedes set_det_size() (Z.~150 + je Clip) laeuft ueber app.prepare() und setzt
# det_thresh auf den insightface-Default 0.5 zurueck — ein frueher Set ist wirkungslos.
# Grund 2: ein Set VOR load_refs() wuerde bei Cache-Miss die REFERENZ-Embeddings mit
# veraenderter Detektor-Schwelle rechnen (Urteilspfad!), waehrend der refcache-Key die
# Schwelle nicht kennt. Referenzen bleiben IMMER beim Default; der Schalter wirkt nur
# auf die Video-Detektion und wird deshalb JE CLIP nach set_det_size gesetzt (s.u.).
# Referenzen kommen seit v1.0/AP1 aus dem lokalen MASTER (verify_data/refs), nicht mehr
# live aus Frigate — Analyse laeuft damit auch bei Frigate-API-Ausfall. Sync: sync_refs.py.
from sync_refs import master_stand, MASTER
idx = master_stand()
if not idx:
    sys.exit("FEHLER: Referenz-Master leer (verify_data/refs) — sync_refs.py import ausfuehren.")

# --- Referenz-Einzelvektoren, gecacht (gleicher Cache wie classify.py) ---
# Der Metadaten-Block liegt unter '§meta': die npz-Keys sind sonst Personennamen, und eine
# Person namens "meta" kollidierte mit dem meta=-Keyword von np.savez (TypeError bei JEDEM
# Lauf). '§' ist per Namens-Regex kein gueltiger Personenname -> kollisionsfrei.
REFCACHE_META = "§meta"


def _refcache_meta(z):
    """Meta-Block aus dem refcache lesen; Alt-Caches mit dem frueheren Key 'meta' bleiben
    lesbar (sonst wuerde der Cache nach dem Update einmal unnoetig neu gerechnet)."""
    return json.loads(str(z[REFCACHE_META if REFCACHE_META in z.files else "meta"]))


def _refcache_schreiben(cache, meta, refs):
    """refcache atomar schreiben (tmp + flush + fsync + os.replace, Muster wie der Clip-Download
    unten): Leser (analyze/anlernen/verifyd) sehen nie eine halb geschriebene npz, ein Abbruch
    laesst nur die tmp-Datei zurueck. Fehler NICHT verschlucken — der Aufrufer meldet sie."""
    tmp = f"{cache}.tmp-{os.getpid()}"
    try:
        with open(tmp, "wb") as f:                 # Dateiobjekt statt Pfad: kein automatisches
            np.savez(f, **{REFCACHE_META: json.dumps(meta)}, **refs)   # .npz-Anhaengsel, fsync moeglich
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, cache)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def load_refs():
    cache = os.path.join(SCRATCH, "refcache.npz")
    want = {p: idx.get(p, []) for p in a.persons}
    if os.path.exists(cache):
        try:                                       # np.load MIT in den try: eine abgeschnittene/
            z = np.load(cache, allow_pickle=True)  # fremde npz darf den Lauf nicht abbrechen,
            meta = _refcache_meta(z)               # sondern nur den Cache verwerfen (neu rechnen)
            if str(meta.get("§modell", "")) == emb.modell and all(meta.get(p) == want[p] for p in a.persons):
                print("Referenz-Embeddings aus Cache.")
                return {p: z[p] for p in a.persons}
        except Exception as e:
            print(f"   (refcache unlesbar: {e} — wird neu berechnet)")
    print("Referenz-Embeddings werden berechnet (einmalig, dann gecacht) ...")
    refs = {}
    for p in a.persons:
        V = []
        for f in want[p]:
            img = cv2.imread(os.path.join(MASTER, p, f))
            if img is None: continue
            v = emb.embed(img)
            if v is not None: V.append(v.astype(np.float32))
        refs[p] = np.asarray(V, dtype=np.float32)
        print(f"   {p}: {len(V)} Vektoren")
    try:
        _refcache_schreiben(cache, {**want, "§modell": emb.modell}, refs)
    except Exception as e:                         # Cache ist regenerierbar -> Lauf nicht abbrechen,
        print(f"   (refcache nicht schreibbar: {e} — wird beim naechsten Lauf neu berechnet)")
    return refs

refs = load_refs()

def nn(v):
    v = np.asarray(v, np.float32)
    return {p: float((M @ v).max()) if len(M) else -1.0 for p, M in refs.items()}

def frontality(fc):
    """Frontalitaet aus buffalo_l 3D-Kopfpose (faengt Drehung UND Neigung, anders als
    ein reiner 2D-Nasenversatz, der ein nach unten geneigtes Gesicht faelschlich als
    frontal einstuft). pose=[a,b,roll] Grad; frontal = beide Kopfwinkel klein.
    Fallback auf kps-Nasenversatz nur, wenn pose fehlt."""
    pose = getattr(fc, "pose", None)
    if pose is not None and len(pose) >= 2:
        a, b = abs(float(pose[0])), abs(float(pose[1]))
        return max(0.0, 1.0 - (a + b) / 90.0), a, b   # (5+5)->0.89 (18+18)->0.6 (45+45)->0
    kps = getattr(fc, "kps", None)
    if kps is None or len(kps) < 5:
        return None, None, None
    le, re, nose = kps[0], kps[1], kps[2]
    eye_cx = (le[0] + re[0]) / 2.0
    eye_dx = abs(re[0] - le[0]) or 1.0
    yaw_off = abs(nose[0] - eye_cx) / eye_dx
    return max(0.0, 1.0 - yaw_off / 0.45), yaw_off, 0.0

def sharp(crop):
    if crop.size == 0: return 0.0
    return float(cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())

emb.set_det_size((1280, 1280))   # NICHT app.prepare() direkt: das wuerde die OpenVINO-Sessions auf CPU zuruecksetzen
outdir = a.dir or os.path.join(HERE, "samples", "analyze")
os.makedirs(outdir, exist_ok=True)
try: sys.stdout.reconfigure(line_buffering=True)   # Ausgabe sofort auf Platte (Absturzsicherheit)
except Exception: pass
results_path = os.path.join(outdir, "results.jsonl")
done_labels = set()
if os.path.exists(results_path):
    with open(results_path) as _rf:
        for _line in _rf:
            try: done_labels.add(json.loads(_line)["label"])
            except Exception: pass
    if done_labels: print(f"Resume: {len(done_labels)} Clips bereits in results.jsonl, werden übersprungen.")

# frame_iter lebt seit W1 (0.1.0.35) in decode.py — EINE Quelle fuer analyze/anlernen/
# abnahme (vorher drei driftende Kopien, Plan-QS R5) plus Vollstaendigkeits-WACHE gegen
# den stillen Abbruch bei defekten Clips. Semantik (i, step, fps-Quelle) ist bit-exakt
# unveraendert; der 18.07.-VAAPI-Verwurf ist dort im Modul-Docstring dokumentiert.
from decode import FrameIter


def ctx_crop(frame, x1, y1, x2, y2, faktor=3.0, max_kante=560, ziel_ar=4 / 3):
    """Gesichts-Box um Umfeld erweitert (Kopf+Schultern) aus dem Original-Frame —
    fuers Push-/Anzeige-Bild (User 17.07.: enge 58x90-Box unbrauchbar klein; ×3 bei
    grossen Gesichtern aber zu wuchtig -> Kante gedeckelt: kleine Gesichter viel
    Kontext, grosse automatisch weniger).

    ANZEIGE-SEITENVERHAELTNIS (User 25.07.): Vorher wurden Breite und Hoehe mit
    DEMSELBEN Faktor vergroessert — das Bild erbte damit das Seitenverhaeltnis der
    Detektionsbox. Gemessen an echten Push-Bildern: 138x225 (0.61), 221x560 (0.39).
    Pushover fuellt so etwas links und rechts mit unscharfen Balken auf ("das Bild
    ist verschlankt und rechts und links verwaschen"). Jetzt wird die KURZE Seite
    auf ziel_ar aufgezogen, soweit der Frame es hergibt — es wird also mehr Umfeld
    gezeigt, nie das Gesicht beschnitten. Reicht der Rand nicht (Person am Bildrand),
    bleibt das Bild schmaler statt zu verzerren; ehrlicher als Strecken."""
    H, W = frame.shape[:2]
    g = max(x2 - x1, y2 - y1)
    f = max(1.2, min(faktor, (max_kante / g) if g else faktor))
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    w, h = (x2 - x1) * f, (y2 - y1) * f
    if h > 0 and ziel_ar:                      # kurze Seite auf das Zielverhaeltnis aufziehen
        if w / h < ziel_ar:
            w = h * ziel_ar
        else:
            h = w / ziel_ar
    w, h = min(w, W), min(h, H)                # nie groesser als das Bild selbst
    cx = min(max(cx, w / 2), W - w / 2)        # Mitte in den Rahmen schieben statt abzuschneiden,
    cy = min(max(cy, h / 2), H - h / 2)        # damit am Bildrand kein einseitiger Schnitt entsteht
    a1, b1 = max(0, int(cx - w / 2)), max(0, int(cy - h / 2))
    a2, b2 = min(W, int(cx + w / 2)), min(H, int(cy + h / 2))
    return frame[b1:b2, a1:a2].copy()


summary = {}   # label -> {person -> best record}
for k, eid in enumerate(a.eids):
    label = a.labels[k] if a.labels and k < len(a.labels) else os.path.basename(eid).split(".")[0]
    if label in done_labels:
        print(f"\n=== {label} — bereits in results.jsonl, übersprungen ==="); continue
    if os.path.exists(eid):                       # lokaler Video-Pfad (z.B. VOD-Clip)
        vid = eid
    else:                                          # sonst als Frigate-Event-ID behandeln
        vid = os.path.join(SCRATCH, eid.replace("/", "_") + ".mp4")
        if not os.path.exists(vid):
            # atomar via .part: ein bei Kill/Reboot abgerissener Download darf beim
            # Retry nicht als gueltiges (halbes) Video durchgehen -> falsches Urteil
            urllib.request.urlretrieve(f"{FRIGATE}/api/events/{eid}/clip.mp4", vid + ".part")
            os.replace(vid + ".part", vid)
    frames = FrameIter(vid, a.fps_sample)
    fps = frames.fps
    # H4: det_size je Clip aus dem Seitenverhaeltnis (nach P1 ist der Wechsel attributsbillig;
    # /32-Regel und Begruendung in Embedder.ar_det_size).
    emb.set_det_size(emb.ar_det_size(frames.breite, frames.hoehe))
    # det_thresh NACH set_det_size (prepare resettet auf 0.5, Review .52); Referenzen
    # oben liefen bewusst mit dem Default. Guard-Muster: erster Frame prueft den REAL
    # gebundenen Wert — Marker wird von qs S5 gegriffen (Erfolg am Ground Truth).
    emb.app.det_model.det_thresh = a.det_thresh
    faces = []; sampled = 0
    show, nnctx = {}, {}   # person -> (flaeche, ctx-crop) bzw. (score, ctx-crop): Anzeige-Bilder
    # Enrollment-Kandidaten (Plan AP4): pro Person das beste GATE-konforme Gesicht
    # (Kante>=100, front>=0.5, det>=0.7, sharp>=60, score>=0.45) und der beste
    # Fremd-Kandidat (grosses gutes Gesicht, bester Match ueberhaupt < 0.35).
    enroll = {}            # person -> (score, dict)
    fremd_kand = None      # (det*flaeche-Guete, dict)
    for i, frame in frames:
        if sampled == 0 and abs(float(emb.app.det_model.det_thresh) - a.det_thresh) > 1e-9:
            print(f"DET-THRESH-MISMATCH: gefordert={a.det_thresh} gebunden={float(emb.app.det_model.det_thresh)}")
        sampled += 1
        for fc in emb.app.get(frame):
            front, yaw, pitch = frontality(fc)
            if front is None: continue
            x1, y1, x2, y2 = [max(0, int(t)) for t in fc.bbox]
            crop = frame[y1:y2, x1:x2]
            sc = nn(fc.normed_embedding)
            p = max(sc, key=sc.get)
            schaerfe0 = sharp(crop)
            # #42 Teil B: Fehldetektions-Flag je Detektion (Zaehlung/Anzeige/Pool —
            # NICHT das Urteil: sc/summary rechnen weiter ueber ALLE Detektionen).
            fd = ist_fehldetektion(front, schaerfe0, float(fc.det_score),
                                   a.fd_front_min, a.fd_sharp_min, a.fd_det_max)
            faces.append({"t": i/fps, "bw": x2-x1, "bh": y2-y1, "front": front, "fd": fd,
                          "yaw": yaw, "det": float(fc.det_score), "sharp": schaerfe0,
                          "sex": getattr(fc, "sex", "?"), "age": int(getattr(fc, "age", -1)),
                          "pose": [round(float(x),0) for x in getattr(fc,"pose",[])] or None,
                          # .copy(): frame[y1:y2, x1:x2] ist ein numpy-VIEW und haelt den KOMPLETTEN
                          # dekodierten Frame am Leben, solange er in faces liegt (bis Clip-Ende).
                          # Bei 4 MP sind das ~11 MB pro Gesicht statt ~100 kB fuer den Crop —
                          # lange Events mit dauerhaft sichtbarer Person liefen so in den OOM-Kill
                          # (Analyse "fehler", Nachholversuche scheiterten identisch).
                          "sc": sc, "p": p, "crop": crop.copy()})
            # Anzeige-Tracking (nur solange der Frame vorliegt): pro Person das
            # GROESSTE verlaesslich erkannte Gesicht (score >= win-thresh) mit
            # Umfeld; Fallback fuer nie Bestaetigte: Umfeld des Match-besten.
            area = (x2 - x1) * (y2 - y1)
            for pp_, s_ in sc.items():
                if s_ >= a.win_thresh and area > show.get(pp_, (0, None))[0]:
                    show[pp_] = (area, ctx_crop(frame, x1, y1, x2, y2))
                if s_ > nnctx.get(pp_, (-1.0, None))[0]:
                    nnctx[pp_] = (s_, ctx_crop(frame, x1, y1, x2, y2))
            kante = min(x2 - x1, y2 - y1)
            schaerfe = schaerfe0
            gate = (kante >= 100 and front >= 0.5 and float(fc.det_score) >= 0.7
                    and schaerfe >= 60)
            if gate:
                kd = {"t": round(i / fps, 1), "bw": x2 - x1, "bh": y2 - y1,
                      "front": round(front, 2), "det": round(float(fc.det_score), 2),
                      "sharp": round(schaerfe, 0), "crop": crop.copy(),
                      "emb": [round(float(x), 5) for x in fc.normed_embedding]}
                bester = max(sc.values())
                if sc[p] >= 0.45 and sc[p] == bester:      # Personen-Kandidat (p = bester Match)
                    if sc[p] > enroll.get(p, (-1, None))[0]:
                        enroll[p] = (sc[p], {**kd, "person": p, "score": round(sc[p], 3)})
                elif bester < 0.35:                        # Fremd-Kandidat: gut sichtbar, niemand
                    guete = float(fc.det_score) * area
                    if fremd_kand is None or guete > fremd_kand[0]:
                        fremd_kand = (guete, {**kd, "person": None, "score": round(bester, 3)})
    # W1-Wache: unvollstaendig gelesene Clips LAUT machen (vorher: stiller Abbruch, Urteil
    # aus dem lesbaren Anfang). VOR dem Ergebnisblock ausgeben — qs S5 schneidet mit
    # tail -25 das ENDE des Outputs, die Ergebnis-/max-Zeilen muessen dort bleiben (R4).
    if frames.unvollstaendig:
        print(f"WARN: clip incomplete — read {frames.gelesen} of {frames.soll} frames "
              f"({frames.verlust_pct:.0f}% lost); judging the readable part (flagged)")
    fd_n = sum(1 for f in faces if f.get("fd"))
    print(f"\n=== {label}  ({eid}) — {sampled} Frames, {len(faces)} Gesichter ==="
          + (f"  [{fd_n} als Fehldetektion gefiltert (Zaehlung/Pool, nicht Urteil)]" if fd_n else ""))
    if sampled == 0:                 # Video fehlt/defekt: KEIN Ergebnis schreiben, damit der
        print("  FEHLER: keine Frames lesbar — kein results-Eintrag fuer dieses Label")
        continue                     # Aufrufer (verifyd) das als "fehler" statt "unknown" wertet
    if a.timeline and faces:
        pp = a.persons[-1]   # Balken fuer die letzte --persons (i.d.R. die gesuchte Person)
        print(f"  Zeitreihe ({'/'.join(a.persons)} scores | Balken = {pp}):")
        for f in sorted(faces, key=lambda x: x["t"]):
            scs = "  ".join(f"{p} {f['sc'][p]:+.2f}" for p in a.persons)
            bar = "#" * int(max(0.0, f["sc"][pp]) * 50)
            print(f"    t={f['t']:5.1f}s  {scs}   {bar}")

    summary[label] = {}
    if not faces:
        print("  (kein Gesicht im Event)")
    for person in a.persons:
        if not faces: continue
        # ZEITLICHE AGGREGATION: Verteilung der Match-Scores ueber ALLE Gesicht-Frames.
        # max = bester Einzelframe; median + n>=Schwelle = Konsistenz (robust gg. Ausreisser).
        sc_list = [f["sc"][person] for f in faces]
        best = max(faces, key=lambda f: f["sc"][person])
        mx = float(max(sc_list)); med = float(np.median(sc_list)); ntot = len(sc_list)
        n40 = int(sum(s >= 0.40 for s in sc_list)); n50 = int(sum(s >= 0.50 for s in sc_list))
        # bestes 3s-Fenster: max Anzahl Frames >= win-thresh in einem gleitenden 3-Sekunden-Fenster.
        # Zeitliche Konsistenz statt Event-median -> robust gg. lange Events mit nur kurzer Sicht.
        ts = sorted((f["t"], f["sc"][person]) for f in faces)
        win = max((sum(1 for (t, s) in ts if t0 <= t <= t0 + 3.0 and s >= a.win_thresh) for t0, _ in ts), default=0)
        summary[label][person] = {"max": round(mx, 3), "median": round(med, 3), "n": ntot,
            "n_ge40": n40, "n_ge50": n50, "win3s": win, "best_wh": f"{best['bw']}x{best['bh']}",
            "best_front": round(best["front"], 2), "best_det": round(best["det"], 2),
            "best_t": round(best["t"], 1), "best_pose": best["pose"]}
        pv = f" pose{best['pose']}" if best['pose'] else ""
        print(f"  {person:<6} max {mx:+.2f}  median {med:+.2f}  n≥.4 {n40}/{ntot}  "
              f"bestes 3s-Fenster {win}×≥{a.win_thresh:.2f}   (bestes {best['bw']}x{best['bh']}{pv} t={best['t']:.0f}s)")
        # Bilder nur fuer Personen, die die Analyse selbst stuetzt: erreicht KEIN Frame
        # win-thresh, behauptet ein Bild mit Personennamen etwas, das die Zahlen nicht
        # hergeben. Vorher schrieb die Schleife 2 Bilder je MASTER-Person ohne jede
        # Schwelle — bei 10 Personen 20 Bilder je Event, auch wenn niemand da war (Galerie
        # zeigte EIN Rad, mit 10 Personennamen beschriftet; User-Befund 25.07.).
        # Vermessen an allen 290 Events / 3.960 Bildern des 24./25.07.: 92,5 % der Bilder
        # entfallen (rund 1 statt 20 je Event), Verlust NULL — kein Bild einer bestaetigten
        # Person, und 0 von 131 bestaetigten Auftritten bleibt ohne Bild (niedrigster NN
        # einer bestaetigten Person 0.410, 99. Perzentil der uebrigen 0.370).
        if mx >= a.win_thresh:
            c = best["crop"]
            if c.size:
                fn = os.path.join(outdir, f"{label}_best_{person}_NN{mx:.2f}_t{best['t']:.0f}s.jpg")
                cv2.imwrite(fn, c)
            sctx = (show.get(person) or nnctx.get(person) or (None, None))[1]
            if sctx is not None and sctx.size:            # Anzeige-Bild fuer Push/Galerie
                cv2.imwrite(os.path.join(outdir, f"{label}_show_{person}_NN{mx:.2f}.jpg"), sctx)
    # pro Clip SOFORT persistieren (Absturzsicherheit, geflusht)
    with open(results_path, "a") as _rf:
        # #42 Teil B: faces bleibt die ROHE Zahl (Bestandsdatenfeld, rueckwirkende Vergleiche);
        # faces_geprueft daneben ist die gefilterte — Leser greifen per .get() mit
        # faces-Fallback zu. max_bw speist fremd_verdacht und wird ab jetzt gefiltert
        # (im Messsatz sank es in den Fehldetektions-Events von 90/91/92 auf 0/59/47).
        # detektionen = Kennwerte je Detektion (ohne Embedding/Crop, ~35 kB/Event):
        # macht kuenftige Schwellenaenderungen an Bestandsdaten simulierbar statt neu rechnen.
        _rf.write(json.dumps({"label": label, "source": eid, "faces": len(faces),
                              "faces_geprueft": len(faces) - fd_n,
                              "max_bw": max((f["bw"] for f in faces if not f.get("fd")), default=0),
                              "detektionen": [{"t": round(f["t"], 1), "bw": f["bw"], "bh": f["bh"],
                                               "front": round(f["front"], 2), "det": round(f["det"], 2),
                                               "sharp": round(f["sharp"], 0), "fd": f["fd"]}
                                              for f in faces],
                              # W1-Telemetrie: Vollstaendigkeit in die Akte (Schema 3) —
                              # verifyd uebernimmt die Felder in deckung.jsonl und wertet
                              # <50 % lesbar als 'fehler' (E1-Entscheid).
                              "frames_gelesen": frames.gelesen, "frames_soll": frames.soll,
                              **({"frames_fehlen": True} if frames.unvollstaendig else {}),
                              "persons": summary.get(label, {})}, default=float, ensure_ascii=False) + "\n")
        _rf.flush()
    # Enrollment-Kandidaten persistieren (AP4): enger Crop (wird ggf. Referenz) +
    # Metriken + Embedding (fuer Fremd-Wiedervorlage) -> Dienst uebernimmt in die Queue.
    kand_liste = []
    for p_, (_, kd) in enroll.items():
        v = np.asarray(kd["emb"], dtype=np.float32)
        nn_eigen = float((refs[p_] @ v).max()) if len(refs.get(p_, [])) else 0.0
        if nn_eigen >= 0.75:
            continue                     # Neuheits-Kriterium: bringt keine Vielfalt
        kd["nn_eigen"] = round(nn_eigen, 3)
        kand_liste.append(kd)
    if fremd_kand:
        kand_liste.append(fremd_kand[1])
    if kand_liste:
        with open(os.path.join(outdir, "kandidaten.jsonl"), "a") as kf:
            for k_, kd in enumerate(kand_liste):
                kcrop = kd.pop("crop")
                fn = f"{label}_enroll_{kd['person'] or 'FREMD'}_{k_}.jpg"
                cv2.imwrite(os.path.join(outdir, fn), kcrop)
                kf.write(json.dumps({**kd, "datei": fn, "label": label, "source": eid},
                                    ensure_ascii=False) + "\n")
            kf.flush()
        print(f"  Enrollment-Kandidaten: {len(kand_liste)}")

# --- Gesamturteil je Person ueber alle Winkel -------------------------
print("\n" + "="*60 + "\nZusammenfassung je Person (bestes Event nach max-Score):")
for person in a.persons:
    cands = [(lbl, d[person]) for lbl, d in summary.items() if person in d]
    if not cands: continue
    lbl, rec = max(cands, key=lambda x: x[1]["max"])
    print(f"  {person:<6} bestes Event '{lbl}': max {rec['max']:+.2f}  median {rec['median']:+.2f}  "
          f"3s-Fenster {rec['win3s']}×≥.4")
print(f"\nresults.jsonl + Crops -> {outdir}")
