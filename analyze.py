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
import os, sys, json, socket, time, urllib.request, argparse, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from face_audit import Embedder, fetch_image, ist_fehldetektion
import numpy as np, cv2

socket.setdefaulttimeout(120)   # urlretrieve kennt kein timeout=; ohne Default haengt ein TCP-Stall ewig

FRIGATE = os.environ.get("FRIGATE_URL", "")
SCRATCH = os.environ.get("SCRATCH_DIR") or os.path.join(tempfile.gettempdir(), "suslik-scratch")
from core.pfade import WURZEL as HERE   # M0-Anker (Falle 0): eine Pfad-Quelle
from core import frames as clipcache    # Z2: EINE Clip-Beschaffung fuer alle Wege
os.makedirs(SCRATCH, exist_ok=True)     # SCRATCH bleibt der refcache-Ort (Z.100)

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
# Z5 (konzept_frames.md v2 §4): der KOERPER-Abnehmer faehrt im selben
# Frame-Lauf mit — hier faellt der Doppel-Decode. Beide Werte sind
# JOB-PARAMETER und keine Selbst-Auskunft: ob der Koerper-Strang scharf ist,
# weiss der Dienst (personmodell-Status) und entscheidet es EINMAL vor dem
# Job; wie viel Speicher der Worker noch hat, weiss ebenfalls nur er
# (worker_rss_max_mb). Ohne --koerper laeuft alles exakt wie bis 0.1.0.151.
ap.add_argument("--koerper", action="store_true",
                help="Koerper-Bestbilder im selben Frame-Lauf mitziehen "
                     "(nur wenn der Koerper-Strang scharf geschaltet ist)")
ap.add_argument("--koerper-rss-max-mb", type=float, default=0.0,
                help="RSS-Deckel dieses Prozesses in MB (worker_rss_max_mb). "
                     "Der Koerper-Puffer darf nur in den Kopfraum darunter "
                     "(0 = unbekannt -> es wird NICHT gepuffert; §5 'RAM')")
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
    # .313 (Prod-Fund 21.08. 19:01): der Cache ist ein GEMEINSAMER Speicher aller Leser
    # (Urteil, Ernte, Sichtung, Live-Wache). Ein Lauf mit Teil-Personenliste (Wanduhr-
    # Roundtrip: --persons <eine Kontrollperson>) schrieb ihn mit GENAU dieser Teilmenge
    # zurueck — danach kannte die Ernte nur noch eine Person, die Sichtung verlor ihre
    # Referenzpruefung, bis das naechste volle Urteil ihn neu baute. Deshalb: der Cache
    # wird IMMER ueber ALLE Personen des Masters gefuehrt (+ die angefragten), zurueck
    # geht nur die angefragte Teilmenge.
    alle = sorted(set(idx.keys()) | set(a.persons))
    want = {p: idx.get(p, []) for p in alle}
    if os.path.exists(cache):
        try:                                       # np.load MIT in den try: eine abgeschnittene/
            z = np.load(cache, allow_pickle=True)  # fremde npz darf den Lauf nicht abbrechen,
            meta = _refcache_meta(z)               # sondern nur den Cache verwerfen (neu rechnen)
            if str(meta.get("§modell", "")) == emb.modell and all(meta.get(p) == want[p] for p in alle):
                print("Referenz-Embeddings aus Cache.")
                return {p: (z[p] if p in z.files else np.zeros((0, 512), np.float32)) for p in a.persons}
        except Exception as e:
            print(f"   (refcache unlesbar: {e} — wird neu berechnet)")
    print("Referenz-Embeddings werden berechnet (einmalig, dann gecacht) ...")
    # A2-Beiwert (core/refbeiwert-Vertrag Stelle 2, der URTEILSPFAD): Vorrats-
    # Referenzen tragen ihren Vektor im refs_meta-Beiwert — embed() auf der
    # kleinen Datei findet gemessen in 28/40 kein Gesicht, und dieser Neuaufbau
    # schriebe den Verlust in den refcache zurueck (Konzept-QS W1.1).
    from core.refbeiwert import beiwerte as _bw
    bw, _fremd = _bw(MASTER, emb.modell)
    if _fremd:
        print(f"   ({_fremd} Vorrats-Referenz(en) mit fremdem Modell-Beiwert — unbrauchbar)")
    refs = {}
    for p in alle:
        V = []
        for f in want[p]:
            b = bw.get((p, f))
            if b is not None:
                V.append(np.asarray(b["emb"], np.float32)); continue
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
    refs = {p: refs.get(p, np.zeros((0, 512), np.float32)) for p in a.persons}
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
# Seit Z4 (konzept_frames v2) haengt analyze NICHT mehr direkt am FrameIter, sondern
# ist Abnehmer am Verteiler (core.frames.lauf, s.u.) — der faehrt genau denselben
# FrameIter mit demselben fps_sample, damit dieselbe Index-Menge.


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


def koerper_abnehmer(eid):
    """Der Koerper-Abnehmer fuer DIESES Event, oder None (dann bleibt es bei
    der heutigen Kette im Dienst-Thread — Notnagel unveraendert).

    Der Import haengt an core.personlauf._proto: derselbe Einstieg, den auch
    der Dienst nimmt (sys.path auf prototyp/ + FRIGATE-ENV-Bruecke), damit im
    Container die gestagte Kette greift und es keine zweite Pfad-Wahrheit gibt.
    Rueckgabe (Koerper, Abnehmer, EVENT_ZEITWACHE_S)."""
    from core.personlauf import _proto, EVENT_ZEITWACHE_S
    from worker import _rss_mb, _cgroup_frei_mb   # EINE Quelle je Messgroesse
    _proto()
    import pfad_snapshots
    # Kopfraum JETZT, nicht aus zweiter Hand: dieses Skript laeuft IM Worker
    # (runpy), also ist sein eigener VmRSS der wahre Stand — ein vom Dienst
    # mitgegebener Messwert waere immer der von VORHIN (und bei einem frisch
    # gestarteten Worker gar keiner).
    rss = _rss_mb()                    # -1 = /proc nicht lesbar
    budget = (a.koerper_rss_max_mb - rss) if rss > 0 else 0.0
    # Zweiter Deckel (Fix 10.08.): die CGROUP-Grenze des Containers. Das
    # Budget oben ist nur POLITIK (worker_rss_max_mb minus eigener VmRSS,
    # die Neustart-Schwelle des Dienstes) — /proc/meminfo stand hier nie im
    # Spiel (im Container zeigt es den Wirt und waere eine Luege). Was den
    # Prozess aber wirklich toetet, ist die cgroup: bei Installationen mit
    # Docker-Memory-Limit darf der Puffer auch den REALEN Rest nicht
    # reissen. -1 = keine Grenze lesbar (Prod 10.08.: memory.max='max')
    # -> es bleibt beim Politik-Budget, geraten wird nichts.
    cg = _cgroup_frei_mb()
    if cg >= 0:
        budget = min(budget, float(cg))
    k = pfad_snapshots.Koerper(eid, ram_budget_mb=budget)
    # Die zwei Frigate-Artefakte JETZT holen: ohne path_data/box gibt es
    # keinen Koerper-Abnehmer, und dann soll der Verteiler auch nichts von
    # ihm wissen (eine Absage in start() waere teurer und lauter als noetig).
    k.vorbereiten()
    return k, k.abnehmer(zeitwache_s=EVENT_ZEITWACHE_S), EVENT_ZEITWACHE_S


def koerper_ablegen(k, wache, outdir, eid, rest_s):
    """UEBERGABE an den Dienst: Top-K-Crops + koerper.json in event_dir.

    Der Verteiler liefert die Frames, die INFERENZ bleibt verteilt (§3.2 'Wo
    der Lauf wohnt'): DINOv2/SVM/PoseWache laufen weiter im Daemon-Thread des
    Dienstes (core/personlive), er holt sich hier nur die Bilder ab, statt
    denselben Clip ein zweites Mal zu dekodieren.

    PNG, nicht JPEG: diese Pixel gehen in die Erkennung. Eine verlustbehaftete
    Zwischenstufe waere eine stille Urteilsaenderung (Train/Serve-Bruch, den
    .148 gerade geschlossen hat) — die JPEG-Ablage im Treffer-Buch passiert
    erst NACH dem Urteil.

    koerper.json ist der ABSCHLUSS-Marker und wird atomar zuletzt geschrieben:
    der Dienst liest nie eine halb gelegte Uebergabe. 'ausfall' darin heisst
    'die Kette lief hier NICHT zu Ende' -> der Dienst faehrt seinen eigenen
    Weg wie bisher; 'top': [] heisst 'sie lief und fand nichts' -> genau wie
    heute uebernimmt der Snapshot-Notnagel."""
    import concurrent.futures as cf
    for alt in os.listdir(outdir):               # Reste eines Vorlaufs (Nachhol)
        if alt.startswith("koerper_") and alt.endswith(".png"):
            os.unlink(os.path.join(outdir, alt))
    ziel = os.path.join(outdir, "koerper.json")
    if os.path.exists(ziel):
        os.unlink(ziel)
    top, info, ausfall = None, "", None
    if wache is None or wache.abgeworfen:
        ausfall = (wache.ausfall if wache is not None else "kein Lauf")
    else:
        pool = cf.ThreadPoolExecutor(max_workers=1)
        try:                                     # Zeitwache wie im Dienst:
            fut = pool.submit(k.auswerten)       # haengt die Auswertung, ist
            top, info = fut.result(timeout=max(1.0, rest_s))   # sie ein Ausfall
        except Exception as ex:                  # noqa: BLE001
            ausfall = f"{type(ex).__name__}: {str(ex)[:120]}"
        finally:
            pool.shutdown(wait=False)
    dateien = []
    for n, (score, fi, crop, hoehe) in enumerate(top or []):
        fn = f"koerper_{n}.png"
        if cv2.imwrite(os.path.join(outdir, fn), crop):
            dateien.append({"datei": fn, "score": float(score),
                            "frame_i": int(fi), "hoehe": int(hoehe)})
    daten = {"eid": eid, "info": info, "top": dateien,
             "puffer_mb": round(k.puffer_mb, 1),
             # GEHALTENE Samples (Nachbesserung F6): vorher stand hier die
             # GELIEFERTE Zahl der Wache (bei Degradation 166), waehrend
             # puffer_mb die GEHALTENE abbildet (80 x 23,7 MB) — die
             # KOERPER-Zeile unten widersprach sich damit selbst. Die
             # gelieferte Zahl bleibt ueber 'degradiert' ("166->80") und die
             # verifyd-worker-Telemetrie sichtbar.
             "samples": int(getattr(k, "gehalten",
                                    wache.samples if wache is not None else 0)),
             # RAM-Gate-Degradation (Fix 10.08.): sichtbar machen, wenn der
             # Puffer auf das Budget heruntergeduennt wurde ("166->80").
             **({"degradiert": k.degradiert} if getattr(k, "degradiert", None) else {}),
             **({"ausfall": ausfall} if ausfall else {})}
    tmp = ziel + ".tmp"
    with open(tmp, "w") as f:
        json.dump(daten, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, ziel)
    print(f"KOERPER: {len(dateien)} Crops, {daten['samples']} Samples, "
          f"Puffer {daten['puffer_mb']:.0f} MB"
          + (f", AUSFALL {ausfall}" if ausfall else f" — {info}"))


summary = {}   # label -> {person -> best record}
for k, eid in enumerate(a.eids):
    label = a.labels[k] if a.labels and k < len(a.labels) else os.path.basename(eid).split(".")[0]
    if label in done_labels:
        print(f"\n=== {label} — bereits in results.jsonl, übersprungen ==="); continue
    if os.path.exists(eid):                       # lokaler Video-Pfad (z.B. VOD-Clip)
        vid, pin_eid = eid, None                  # nichts beschafft -> nichts zu loesen
    else:                                          # sonst als Frigate-Event-ID behandeln
        # Z2 (konzept_frames v2): EIN Download je Event fuer ALLE Abnehmer.
        # core.frames traegt Cache-Rangfolge, die .part-Atomik (ein bei
        # Kill/Reboot abgerissener Download darf beim Retry nie als gueltiges,
        # halbes Video durchgehen -> falsches Urteil) und setzt den Pin im
        # selben Zug; Dateiname und Ablage bleiben <cache>/<eid>.mp4.
        vid, pin_eid = clipcache.clip_holen(eid, frigate_url=FRIGATE), eid
    try:
        faces = []; sampled = 0
        show, nnctx = {}, {}   # person -> (flaeche, ctx-crop) bzw. (score, ctx-crop): Anzeige-Bilder
        # Streaming-argmax statt Crop-Sammlung (Bau 10.08. im Umfeld von Issue #20):
        # frueher hielt JEDE faces-Zeile ihren Crop bis Clip-Ende, verbraucht wird aber
        # nur EIN Crop je Person (Bestbild-JPG unten). best_crop haelt je Person genau
        # den Crop des bisher besten Frames (strikt > = erstes Maximum, exakt die
        # max()-Semantik) — Speicher O(#Personen) statt O(#Detektionen), Ergebnis
        # byte-identisch (Orakel-Test 288 Faelle / 158.515 Detektionen, 0 Abweichungen).
        # EHRLICHE EINORDNUNG (Kontrolle 10.08.): das ist eine Haltbarkeits-Verbesserung
        # im Gesichtspfad, NICHT die Ursache von Issue #20. Gemessen am 816-Detektionen-
        # 4K-Lauf: die alte Sammlung hielt 117,5 MB Crops; die Prozess-Spitze (~1,9 GB,
        # gesetzt vom ORT/OpenVINO-Aufbau) sinkt dadurch NICHT messbar. Der Melder hat
        # die Crop-Ursache selbst widerrufen (Issue #20, Kommentar 3, 08.08.): seine
        # 34-38 GB kamen von einem bei jedem Dienststart neu aufgenommenen Anker-
        # Lernlauf (phase=anker), nicht aus dieser Sammlung.
        best_crop = {}         # person -> (score, enger Crop des argmax-Gesichts)
        # Enrollment-Kandidaten (Plan AP4): pro Person das beste GATE-konforme Gesicht
        # (Kante>=100, front>=0.5, det>=0.7, sharp>=60, score>=0.45) und der beste
        # Fremd-Kandidat (grosses gutes Gesicht, bester Match ueberhaupt < 0.35).
        enroll = {}            # person -> (score, dict)
        fremd_kand = None      # (det*flaeche-Guete, dict)

        def clip_start(info):
            """EINMAL vor dem ersten Frame — alles, was die Clip-Metadaten braucht.
            Inhalt UND Reihenfolge unveraendert; sie bleiben bewusst HIER im
            Abnehmer und wandern nie in den Verteiler (konzept_frames v2 §4/Z4)."""
            global fps
            fps = info.fps
            # H4: det_size je Clip aus dem Seitenverhaeltnis (nach P1 ist der Wechsel attributsbillig;
            # /32-Regel und Begruendung in Embedder.ar_det_size).
            emb.set_det_size(emb.ar_det_size(info.breite, info.hoehe))
            # det_thresh NACH set_det_size (prepare resettet auf 0.5, Review .52); Referenzen
            # oben liefen bewusst mit dem Default. Guard-Muster: erster Frame prueft den REAL
            # gebundenen Wert — Marker wird von qs S5 gegriffen (Erfolg am Ground Truth).
            emb.app.det_model.det_thresh = a.det_thresh

        def gesicht(i, frame):
            """Abnehmer 'gesicht' (Z4): frueher der Rumpf von `for i, frame in frames`.
            Zeile fuer Zeile derselbe Code — nur die Schleifenzeile ist weg, weil jetzt
            der Verteiler faehrt. sampled/fremd_kand sind die einzigen Namen, die hier
            NEU GEBUNDEN werden; alles andere wird an Ort und Stelle veraendert."""
            global sampled, fremd_kand
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
                              # .313: genderage laeuft nicht mehr mit (ungenutzt) — Felder bleiben
                              # im Bestandsformat, jetzt '?'/-1 statt eines Modellwerts.
                              "sex": getattr(fc, "sex", None) or "?",
                              "age": int(getattr(fc, "age", None) if getattr(fc, "age", None) is not None else -1),
                              "pose": [round(float(x),0) for x in getattr(fc,"pose",[])] or None,
                              # KEIN "crop" mehr in faces: die Sammlung hielt jede Detektion
                              # als Kopie bis Clip-Ende (nach dem .copy()-Fix von 0.1.0.21
                              # ~100 kB statt ~11 MB je Gesicht, aber weiter linear in der
                              # Detektionszahl). Einziger Verbraucher war das Bestbild je
                              # Person — das haelt jetzt best_crop (streaming-argmax;
                              # Einordnung und Messung im best_crop-Kommentar oben).
                              "sc": sc, "p": p})
                # Anzeige-Tracking (nur solange der Frame vorliegt): pro Person das
                # GROESSTE verlaesslich erkannte Gesicht (score >= win-thresh) mit
                # Umfeld; Fallback fuer nie Bestaetigte: Umfeld des Match-besten.
                area = (x2 - x1) * (y2 - y1)
                for pp_, s_ in sc.items():
                    if s_ >= a.win_thresh and area > show.get(pp_, (0, None))[0]:
                        show[pp_] = (area, ctx_crop(frame, x1, y1, x2, y2))
                    if s_ > nnctx.get(pp_, (-1.0, None))[0]:
                        nnctx[pp_] = (s_, ctx_crop(frame, x1, y1, x2, y2))
                    # Bestbild-Crop je Person: strikt > haelt das ERSTE Maximum —
                    # dieselbe Zeile, die max(faces, key=sc[person]) unten gewaehlt
                    # haette. Sentinel -2.0: auch der Kein-Referenzen-Fall
                    # (nn() == -1.0) liefert deterministisch das erste Gesicht.
                    if s_ > best_crop.get(pp_, (-2.0,))[0]:
                        best_crop[pp_] = (s_, crop.copy())
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

        # Z5: der KOERPER-Abnehmer faehrt im selben Lauf mit — nur wenn der
        # Dienst ihn scharf gemeldet hat UND es ein echtes Frigate-Event ist
        # (ein lokaler Video-Pfad hat keine path_data). Jeder Fehlschlag hier
        # ist ein Verzicht, nie ein Abbruch: dann bleibt es fuer dieses Event
        # beim heutigen Weg (eigener Lauf im Dienst-Thread).
        koerper = koerper_ab = None
        koerper_wache_s = 0.0
        if a.koerper and pin_eid:
            t_koerper = time.monotonic()
            try:
                koerper, koerper_ab, koerper_wache_s = koerper_abnehmer(eid)
            except Exception as ex:                       # noqa: BLE001
                koerper = koerper_ab = None
                print(f"KOERPER: kein Abnehmer ({type(ex).__name__}: "
                      f"{str(ex)[:120]}) — der Dienst faehrt seinen eigenen Weg")
        # Z4: EIN Lauf, die Vertragsfelder stehen beim Abnehmer, keins steckt
        # im Verteiler — er soll nie fuer uns raten (§3.2).
        # `frames` traegt danach dieselben Wache-Namen wie frueher der
        # FrameIter (gelesen/soll/verlust_pct/unvollstaendig/decoder_fehler/
        # hwdec/hwdec_fallback), die Auswertung unten bleibt Wort fuer Wort.
        wachen = clipcache.lauf(vid, [clipcache.Abnehmer(
            name="gesicht",
            fps_sample=a.fps_sample,   # derselbe Wert wie zuvor -> derselbe step
            zeitbezug="clip",          # t = i/fps, kein Wanduhr-Anker
            bedarf="stream",           # haelt nur O(#Personen) Best-Crops, nie den Frame
            hart=True,                 # verifyd:3447-3452 haengt am Gesichtsurteil:
                                       # faellt es aus, ist der Lauf zu Ende
            wache_politik="nachrechnen",
            zeitwache_s=None,          # BEWUSST keins: heute deckelt allein der
                                       # Job-Timeout des Aufrufers (verifyd.py:548).
                                       # Ein neuer Deckel hier waere eine
                                       # Verhaltensaenderung, kein Umzug.
            start=clip_start, frame=gesicht)]
            + ([koerper_ab] if koerper_ab is not None else []))
        frames = wachen["gesicht"]
    finally:
        # Nutzungsende des Clips. Keine Pin-Waise hinterlassen: ein
        # liegenbleibender Pin haelt cleanup_cache ewig von dieser
        # Datei ab (Size-Cap kaeme nie mehr an sie heran).
        if pin_eid:
            clipcache.frei(pin_eid)
    if koerper is not None:
        # Sofort nach dem Lauf: der Frame-Puffer ist das teuerste Stueck RAM
        # im Prozess und wird in auswerten() losgelassen. Ein Fehler hier darf
        # das Gesichtsurteil nie beruehren — es haengt an results.jsonl unten.
        try:
            koerper_ablegen(koerper, wachen.get(koerper.NAME), outdir, eid,
                            koerper_wache_s - (time.monotonic() - t_koerper))
        except Exception as ex:                           # noqa: BLE001
            print(f"KOERPER: Uebergabe gescheitert ({type(ex).__name__}: "
                  f"{str(ex)[:120]}) — der Dienst faehrt seinen eigenen Weg")
        koerper = None
    # W1-Wache: unvollstaendig gelesene Clips LAUT machen (vorher: stiller Abbruch, Urteil
    # aus dem lesbaren Anfang). VOR dem Ergebnisblock ausgeben — qs S5 schneidet mit
    # tail -25 das ENDE des Outputs, die Ergebnis-/max-Zeilen muessen dort bleiben (R4).
    if frames.unvollstaendig:
        print(f"WARN: clip incomplete — read {frames.gelesen} of {frames.soll} frames "
              f"({frames.verlust_pct:.0f}% lost"
              + (f", {frames.decoder_fehler} decoder errors" if getattr(frames, "decoder_fehler", 0) else "")
              + "); judging the readable part (flagged)")
    if getattr(frames, "hwdec_fallback", False):
        # Panel-Auflage: der HW-Rueckfall war als 'laut' versprochen, hatte
        # aber keinen Konsumenten — jetzt Logzeile + Telemetrie-Feld.
        print("WARN: hardware decode incomplete/unavailable — software path "
              "covered the clip" if not frames.hwdec else
              "WARN: hardware decode aborted mid-clip — judged the readable part")
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
            # best_crop[person] existiert immer, wenn faces nicht leer ist (nn() liefert
            # jede Person in sc); der Crop ist byte-identisch zu best["crop"] von frueher.
            c = best_crop[person][1]
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
                              **({"hwdec": True} if getattr(frames, "hwdec", False) else {}),
                              **({"hwdec_fallback": True}
                                 if getattr(frames, "hwdec_fallback", False) else {}),
                              **({"decoder_fehler": frames.decoder_fehler}
                                 if getattr(frames, "decoder_fehler", 0) else {}),
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
