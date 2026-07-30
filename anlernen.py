#!/usr/bin/env python3
"""Anlernen — Face-Clustering-Enrollment (User-Konzept 19.07.).

Sammelt UNBEKANNTE Gesichter (die keiner bekannten Person sicher zuzuordnen sind) mit
ihrem 512-dim ArcFace-Embedding, gruppiert sie nach Selbst-Aehnlichkeit (Cosinus) und
laesst eine Gruppe als neue Person benennen. So entsteht eine Referenzbasis, OHNE dass
man vorher wissen muss, wer die Person ist (loest das Henne-Ei-Problem des Enrollments).

CLI:
  anlernen.py sammle [--tage N]   # unbekannte Gesichter aus Cache-Clips der letzten N Tage
  anlernen.py cluster [--sim S]   # Gruppen bilden + als JSON/Textreport ausgeben

Importierbar von verifyd: lade_gesichter(), benenne() u.a. — clustere() wird seit dem
Unknown-Reiter (22.07.) NUR noch intern gerufen (_reconcile_intern + CLI 'cluster');
Widerleger-Fund 30.07.: die alte Import-Behauptung fuehrte Reviews in die Irre.
Read-only gegen Frigate; schreibt nur in verify_data/anlernen/ (+ refs/ beim Benennen).
"""
import os, sys, json, time, argparse, collections, fcntl, threading
from contextlib import contextmanager
os.environ.setdefault("OV_DEVICE", "GPU")
from core.pfade import WURZEL as HERE   # M0-Anker (Falle 0): eine Pfad-Quelle
sys.path.insert(0, HERE)
import cv2
import numpy as np
from face_audit import Embedder, aktuelles_modell, ist_fehldetektion

DATA = os.environ.get("VERIFY_DATA_DIR") or os.path.join(HERE, "verify_data")  # von verifyd prozessweit gesetzt
MASTER = os.path.join(DATA, "faces")
CLIPS = os.path.join(DATA, "clips")
STATE = os.path.join(DATA, "state")
ANLERN = os.path.join(DATA, "learn")
GES_PATH = os.path.join(ANLERN, "gesichter.jsonl")
GEPRUEFT_PATH = os.path.join(ANLERN, "geprueft.jsonl")   # eid-Vermerk je Pruef-Kontext -> kein Re-Processing (User 21.07.)
POOL_LOCK_PATH = os.path.join(ANLERN, "pool.lock")       # prozessuebergreifender Lock fuer alle Pool-Schreiber
CROPS = os.path.join(ANLERN, "crops")


@contextmanager
def pool_lock():
    """Exklusiver, PROZESSUEBERGREIFENDER Lock (fcntl.flock) fuer ALLE Operationen, die den
    Unbekannt-Pool schreiben: sammle, migriere_und_pruefe_pool, reconcile_unbekannte, reorganisieren.
    Serialisiert szenario-getriggertes Sammeln, 06:00-Wartung, Reorganisieren-Button UND manuelle
    CLI-Laeufe gegeneinander (Review 21.07.: sonst truncaten zwei Laeufe gesichter.jsonl gleichzeitig
    -> verlorene/doppelte Gesichter). Blockierend: der zweite Aufrufer wartet, bis der erste fertig ist."""
    os.makedirs(ANLERN, exist_ok=True)
    f = open(POOL_LOCK_PATH, "w")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        finally:
            f.close()


def _schreibe_jsonl_atomar(pfad, zeilen):
    """Liste von dict-Zeilen atomar nach pfad (tmp + fsync + os.replace) — ein Crash/Neustart
    mitten im Schreiben laesst so nie eine halbe/leere Pool-Datei zurueck (Review 21.07.)."""
    tmp = f"{pfad}.tmp-{os.getpid()}-{threading.get_ident()}"   # pro Prozess UND Thread eindeutig
    with open(tmp, "w") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, pfad)


def _schreibe_json_atomar(pfad, obj):
    """JSON-Zwilling zu _schreibe_jsonl_atomar. Mehrere Dateien (refs_qs.json,
    vorschlaege_<person>.json) werden von ZWEI Seiten geschrieben — dem Dienst (HTTP-Thread) und
    einem Subprozess. Direkt auf den Zielpfad geschrieben, konnte ein Leser eine halbe Datei
    erwischen (json.load wirft -> Reiter leer) oder ein Abbruch sie dauerhaft zerstoeren.
    Fehler werden NICHT verschluckt: der Aufrufer entscheidet."""
    # PID *und* Thread-ID: der Dienst schreibt aus parallelen HTTP-Threads, die sich sonst denselben
    # tmp-Namen teilten und sich gegenseitig die Datei wegraeumten (im Test 8 von 15 Schreibern mit
    # Exception, obwohl das Ergebnis valide blieb).
    tmp = f"{pfad}.tmp-{os.getpid()}-{threading.get_ident()}"
    try:
        with open(tmp, "w") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, pfad)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

# Ein Gesicht gilt als UNBEKANNT, wenn sein bester Match gegen ALLE bekannten Personen
# darunter liegt (selbst sehr aehnliche Personen im Messsatz liegen bei ~0.31–0.36, also drunter).
UNBEKANNT_MAX = 0.42
# Qualitaets-Gate fuers Sammeln (Rauschen raushalten, aber grosszuegiger als das Enroll-Gate).
MIN_KANTE, MIN_DET = 70, 0.6
# #42 Teil B: Fehldetektions-Signatur (face_audit.ist_fehldetektion, kalibriert) — haelt
# Radkasten/Hecken-Crops aus dem Unbekannt-Pool. Werte kommen von verifyd per Env
# (gleiches Muster wie VERIFY_DATA_DIR); Defaults = die kalibrierten Config-Defaults.
FD_FRONT_MIN = float(os.environ.get("VERIFY_FD_FRONT_MIN", 0.85))
FD_SHARP_MIN = float(os.environ.get("VERIFY_FD_SHARP_MIN", 1500))
FD_DET_MAX = float(os.environ.get("VERIFY_FD_DET_MAX", 0.70))
# Cluster-Schwelle: ab dieser Cosinus-Aehnlichkeit zaehlen zwei Gesichter als dieselbe Person.
# Hebel 2 (21.07.): auf den modell-konsistenten Daten (nach Hebel 1) rekalibriert 0.45->0.50 —
# echte Cluster liegen >=0.55, Fehl-Merges verschiedener Personen bei 0.45-0.48; 0.50 trennt sie,
# haelt aber die Crew (16) ganz (0.55 zerlegte sie schon). Gegenseitiges Clustering war unnoetig.
SIM_DEFAULT = 0.50


# ---------------------------------------------------------------- Hilfen (aus analyze.py)
def frontality(fc):
    pose = getattr(fc, "pose", None)
    if pose is not None and len(pose) >= 2:
        a, b = abs(float(pose[0])), abs(float(pose[1]))
        return max(0.0, 1.0 - (a + b) / 90.0)
    return 0.0


def sharp(crop):
    if crop.size == 0:
        return 0.0
    return float(cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())


def frame_iter(vid, fps_sample=3):
    """Seit W1 (0.1.0.35) ein Wrapper ueber decode.FrameIter — EINE Frame-Quelle fuer alle
    drei Werkzeuge statt drei driftender Kopien (Plan-QS R5). Semantik unveraendert:
    yields (i/fps, frame) fuer jedes step-te Frame. Die Wache reagiert hier bewusst NICHT
    (Sammeln ist kein Urteilspfad; ein Teil-Clip liefert eben weniger Kandidaten)."""
    from decode import FrameIter
    it = FrameIter(vid, fps_sample)
    for i, frame in it:
        yield i / it.fps, frame


def ctx_crop(frame, x1, y1, x2, y2, faktor=2.5, max_kante=560):
    h, w = frame.shape[:2]
    bw, bh = x2 - x1, y2 - y1
    g = max(bw, bh)
    f = max(1.2, min(faktor, (max_kante / g) if g else faktor))
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    nw, nh = bw * f, bh * f
    a, b = int(max(0, cx - nw / 2)), int(max(0, cy - nh / 2))
    c, d = int(min(w, cx + nw / 2)), int(min(h, cy + nh / 2))
    return frame[b:d, a:c]


# ---------------------------------------------------------------- Referenz-Embeddings (det 320!)
def lade_master_refs(emb):
    """Embeddings aller bekannten Personen aus dem Master — MIT det 320 (kleine Ref-Crops),
    VOR dem Umschalten auf 1280 fuers Video (Memory-Regel: sonst brechen die Embeddings ein)."""
    refs = {}
    if not os.path.isdir(MASTER):
        return refs
    for p in sorted(os.listdir(MASTER)):
        pd = os.path.join(MASTER, p)
        if not os.path.isdir(pd):
            continue
        V = []
        for f in os.listdir(pd):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            img = cv2.imread(os.path.join(pd, f))
            if img is None:
                continue
            v = emb.embed(img)
            if v is not None:
                V.append(v.astype(np.float32))
        if V:
            refs[p] = np.asarray(V, dtype=np.float32)
    return refs


def nn(refs, v):
    v = np.asarray(v, np.float32)
    best_p, best_s = None, -1.0
    for p, M in refs.items():
        s = float((M @ v).max()) if len(M) else -1.0
        if s > best_s:
            best_p, best_s = p, s
    return best_p, best_s


# ---------------------------------------------------------------- Sammeln
def _unbekannt_eids(tage):
    """eids aus deckung.jsonl, die als unbekannt gewertet wurden und deren Clip im Cache liegt."""
    grenze = time.time() - tage * 86400
    out = []
    dp = os.path.join(DATA, "state", "deckung.jsonl")
    if not os.path.exists(dp):
        return out
    for line in open(dp):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if (d.get("ts") or 0) < grenze:
            continue
        if d.get("kategorie") not in ("fremd_verdacht", "unbekannt_schwach"):
            continue
        if d.get("faces_geprueft", d.get("faces") or 0) < 1:   # #42 Teil B: gefilterte Zahl, faces-Fallback
            continue
        eid = d["eid"]
        clip = os.path.join(CLIPS, eid.replace("/", "_") + ".mp4")
        if os.path.exists(clip):
            out.append((eid, d.get("camera", "?"), d.get("start") or d.get("ts")))
    return out


def _schon_gesammelt():
    done = set()
    if os.path.exists(GES_PATH):
        for line in open(GES_PATH):
            try:
                done.add(json.loads(line)["eid"])
            except Exception:
                pass
    return done


def _pruef_tag():
    """Pruef-Kontext: Modell + Sammel-Schwellen. Aendert er sich, gelten alte Abhak-Vermerke
    nicht mehr -> die Events werden nach einem Modell-/Schwellen-Wechsel automatisch neu geprueft."""
    return f"{aktuelles_modell()}|k{MIN_KANTE}|d{MIN_DET}|ff{FD_FRONT_MIN}|fs{FD_SHARP_MIN}|fx{FD_DET_MAX}"   # FD-Schwellen im Tag (Review .52: sonst wirkt eine Schwellenaenderung nie auf abgehakte Events)


def _schon_geprueft(tag):
    """eids, die mit DIESEM Pruef-Kontext schon angefasst wurden, EGAL ob ein Gesicht rauskam.
    Verhindert das teure Re-Processing der Nicht-Gesicht-Events (Gras/zu-klein/zu-schraeg wurde
    sonst bei JEDEM Lauf neu durch den Clip gerechnet, User-Befund 21.07.)."""
    done = set()
    if os.path.exists(GEPRUEFT_PATH):
        for line in open(GEPRUEFT_PATH):
            try:
                d = json.loads(line)
                if d.get("tag") == tag:
                    done.add(d["eid"])
            except Exception:
                pass
    return done


def sammle(tage=5.0, fps_sample=2, mit_migriere=True):
    """Gelockter Wrapper ums Sammeln (serialisiert gegen andere Pool-Schreiber, Review 21.07.).
    mit_migriere=False fuer das szenario-getriggerte Sofort-Sammeln (nur neue Gesichter, OHNE die
    teure Pool-Neupruefung/Referenz-Neueinbettung — die macht der Reorganisieren-Button)."""
    with pool_lock():
        return _sammle_intern(tage, fps_sample, mit_migriere)


def _sammle_intern(tage, fps_sample, mit_migriere):
    os.makedirs(CROPS, exist_ok=True)
    emb = Embedder()
    refs = lade_master_refs(emb)
    print(f"reference base: {sum(len(v) for v in refs.values())} vectors, {len(refs)} persons", flush=True)
    if mit_migriere:
        stat = migriere_und_pruefe_pool(emb, refs)          # Hebel 1: modell-konsistent + bekannte raus
        print(f"pool check: {stat}", flush=True)
    emb.set_det_size((1280, 1280))
    tag = _pruef_tag()                                     # Modell + Schwellen -> entwertet Vermerke bei Aenderung
    schon = _schon_gesammelt()                             # schon im Pool -> nie neu sammeln
    geprueft = _schon_geprueft(tag) | schon               # schon im Pool ODER (mit diesem tag) ohne Gesicht abgehakt
    evs = [e for e in _unbekannt_eids(tage) if e[0] not in geprueft]
    print(f"{len(evs)} events to check ({len(schon)} in the pool, "
          f"{len(geprueft) - len(schon)} already checked off without a face) [tag {tag}]", flush=True)
    neu = 0
    with open(GES_PATH, "a") as out, open(GEPRUEFT_PATH, "a") as gpr:
        for eid, camera, ts in evs:
            clip = os.path.join(CLIPS, eid.replace("/", "_") + ".mp4")
            # TOP-3 je Event statt EIN Bestes (Umbau 25.07., mit eigenen Augen belegt): die
            # guete-Formel bevorzugt systematisch das statische Objekt (gross, kantenreich,
            # scheinfrontal) — im Anlern-Testdurchgang 25.07. gewann zweimal der Anhaenger-Radkasten,
            # und die ECHTEN Gesichter desselben Events kamen NIE in den Pool. Mit drei
            # Plaetzen je Event kommen die Personen mit hinein; Objekt-Crops quarantaeniert
            # anschliessend die Objekt-Regel des Reconcile auf Cluster-Ebene (dort ist sie
            # trennscharf, auf Einzelbild-Ebene nachweislich nicht — Ueberlappung Person/Objekt im Testdurchgang).
            # Vielfaltsschutz: kein zweiter Platz fuer ein fast identisches Embedding
            # (>0.90), sonst waeren alle drei Plaetze derselbe Radkasten.
            kand = []                                    # laufende Top-Liste (max 8, guete-sortiert)
            from decode import FrameIter as _FI          # H4: det_size je Clip nach Seitenverhaeltnis
            _it = _FI(clip, fps_sample)
            emb.set_det_size(emb.ar_det_size(_it.breite, _it.hoehe))
            for t, frame in ((i / _it.fps, f) for i, f in _it):
                for fc in emb.app.get(frame):
                    x1, y1, x2, y2 = [int(v) for v in fc.bbox]
                    kante = min(x2 - x1, y2 - y1)
                    det = float(fc.det_score)
                    if kante < MIN_KANTE or det < MIN_DET:
                        continue
                    p, s = nn(refs, fc.normed_embedding)
                    if s >= UNBEKANNT_MAX:               # sicher eine bekannte Person -> nicht sammeln
                        continue
                    front = frontality(fc)
                    crop = frame[max(0, y1):y2, max(0, x1):x2]
                    schaerfe = sharp(crop)
                    # #42 Teil B: Objekt-Signatur gar nicht erst sammeln (U65/U66-Klasse:
                    # Gras/Hecke wurde zu Unbekannt-Identitaeten geclustert; die Cluster-
                    # Objekt-Regel unten griff dort nicht, weil Vegetations-Embeddings
                    # weniger selbstaehnlich sind als ein statisches Rad).
                    if ist_fehldetektion(front, schaerfe, det,
                                         FD_FRONT_MIN, FD_SHARP_MIN, FD_DET_MAX):
                        continue
                    guete = kante * (0.3 + front) * det * min(1.0, schaerfe / 80.0)
                    kand.append({"eid": eid, "camera": camera, "ts": ts, "t": round(t, 1),
                                 "kante": kante, "front": round(front, 2), "det": round(det, 2),
                                 "guete": guete, "nn_person": p, "nn_score": round(s, 3),
                                 "emb": [round(float(x), 5) for x in fc.normed_embedding],
                                 "modell": aktuelles_modell(),
                                 "ctx": ctx_crop(frame, x1, y1, x2, y2)})
                    kand.sort(key=lambda k: -k["guete"])
                    del kand[8:]                          # Speicher-Deckel
            gewaehlt = []
            for k in kand:                               # guete-Reihenfolge, Duplikate raus
                v = np.asarray(k["emb"], np.float32)
                if any(float(v @ np.asarray(g["emb"], np.float32)) > 0.90 for g in gewaehlt):
                    continue
                gewaehlt.append(k)
                if len(gewaehlt) >= 3:
                    break
            for lauf, best in enumerate(gewaehlt):
                gid = eid.replace("/", "_") + ("" if lauf == 0 else f"~{lauf + 1}")
                cv2.imwrite(os.path.join(CROPS, gid + ".jpg"), best.pop("ctx"))
                best["id"] = gid
                out.write(json.dumps(best, ensure_ascii=False) + "\n")
                out.flush()
                neu += 1
                print(f"  collected {gid} ({camera}) nearest={best['nn_person']} {best['nn_score']} "
                      f"kante={best['kante']} front={best['front']}", flush=True)
            best = gewaehlt[0] if gewaehlt else None      # fuers Abhaken darunter
            gpr.write(json.dumps({"eid": eid, "tag": tag, "gesicht": best is not None, "ts": ts},
                                 ensure_ascii=False) + "\n")   # jedes Event genau einmal abhaken (auch ohne Gesicht)
            gpr.flush()
    print(f"\n{neu} faces collected, {len(evs)} events checked -> {GES_PATH}", flush=True)
    return neu


# ---------------------------------------------------------------- Clustern
def lade_gesichter():
    G = []
    if os.path.exists(GES_PATH):
        for line in open(GES_PATH):
            line = line.strip()
            if line:
                try:
                    G.append(json.loads(line))
                except Exception:
                    pass
    return G


def migriere_und_pruefe_pool(emb=None, refs=None):
    """Hebel 1 (User 21.07.): den Unbekannt-Pool sauber halten.
    (a) MODELL-KONSISTENZ: Gesichter, deren gespeichertes Embedding von einem ANDEREN
        Recognition-Modell stammt (Modell-Wechsel buffalo->adaface), sind orthogonal zum refcache
        und clustern falsch -> aus ihrem Crop mit dem aktuellen Modell neu einbetten.
    (b) NEUPRUEFUNG: Gesichter, die jetzt eine bekannte Person >= UNBEKANNT_MAX treffen (Referenzen
        wurden seit dem Sammeln besser), sind keine Unbekannten mehr -> raus.
    (c) tote Crops (kein Gesicht mehr detektierbar) -> raus.
    Laeuft im 06:00-Job aus sammle (mit dessen Embedder + Referenzen, det 320 vor dem 1280-Umschalten).
    Rueckgabe: Statistik-Dict."""
    if emb is None:
        emb = Embedder()
    if refs is None:
        refs = lade_master_refs(emb)
    modell = aktuelles_modell()

    def _rm(p):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass

    behalten, entfernt = [], {}
    reembedded = tot = 0
    for g in lade_gesichter():
        crop = os.path.join(CROPS, g["id"] + ".jpg")
        if g.get("modell") != modell:                       # anderes/kein Modell -> neu einbetten
            im = cv2.imread(crop)
            fc = emb.app.get(im) if im is not None else None
            if not fc:
                tot += 1
                _rm(crop)
                continue
            f = max(fc, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
            g["emb"] = [round(float(x), 5) for x in f.normed_embedding]
            g["modell"] = modell
            reembedded += 1
        p, s = nn(refs, np.asarray(g["emb"], dtype=np.float32))
        if s >= UNBEKANNT_MAX:                              # jetzt bekannt -> kein Unbekannter mehr
            entfernt[p] = entfernt.get(p, 0) + 1
            _rm(crop)
            continue
        behalten.append(g)
    _schreibe_jsonl_atomar(GES_PATH, behalten)              # atomar: tmp+fsync+os.replace (Review 21.07.: sonst Crash mid-rewrite = Pool weg)
    return {"behalten": len(behalten), "reembedded": reembedded,
            "entfernt_bekannt": entfernt, "tote_crops": tot}


def clustere(gesichter=None, sim=SIM_DEFAULT):
    """Average-Linkage-Gruppierung nach Cosinus-Aehnlichkeit. Liefert Liste von Clustern,
    jeder Cluster ist eine Liste von Gesicht-Dicts, das repraesentative (guete-beste) zuerst.

    Implementierung: inkrementelle SUMMEN-MATRIX (S7b, Entscheid B2) — gleicher
    Tie-Break-MECHANISMUS (erstes Maximum in (i,j)-Zeilenordnung) wie
    _clustere_referenz; die Werte sind identisch bis auf die float32-Rundung der
    Referenz (~1e-7; die Summen-Matrix rechnet in float64 und ist die GENAUERE —
    Widerleger 30.07.: Kipp-Intervalle am echten Pool zusammen 2e-6 breit,
    SIM_DEFAULT liegt in keinem). Statt je Paar S[np.ix_].mean() neu zu rechnen,
    werden beim Verschmelzen zwei Zeilen addiert — je nach Regime zwei bis drei
    Groessenordnungen schneller (Pool n=227: ~370x; V0.2b-Messreihe bis 718x).
    Die qs-Stufe PYS7B haelt beide Implementierungen am echten Pool auf
    Partitions-Gleichheit und friert die Referenz per sha256 ein.
    Nicht-endliche Embeddings (NaN/inf) werden VOR dem Clustern isoliert und als
    Einzel-Cluster angehaengt — dasselbe Endergebnis wie die Referenz, die solche
    Paare nie waehlt; ohne die Wache waehlt np.argmax NaN als Maximum und
    'best < sim' bricht nie ab -> der GESAMTE Pool kollabierte zu EINEM Cluster
    (Widerleger-MUSS 30.07., stiller Totalverlust der Unbekannt-Struktur)."""
    G = gesichter if gesichter is not None else lade_gesichter()
    if not G:
        return []
    M = np.asarray([g["emb"] for g in G], dtype=np.float32)
    kaputt_ix = [i for i in range(len(G)) if not np.all(np.isfinite(M[i]))]
    if kaputt_ix:
        heil = [g for i, g in enumerate(G) if i not in set(kaputt_ix)]
        cluster = clustere(heil, sim=sim) if heil else []
        cluster.extend([G[i]] for i in kaputt_ix)
        cluster.sort(key=lambda c: (-len(c), c[0].get("id") or ""))
        return cluster
    S = M @ M.T                                          # Cosinus (Embeddings sind normiert)
    SUM = S.astype(np.float64)                           # astype kopiert bereits
    del S, M                                             # Speicher: nur SUM lebt weiter (E3-Groessen)
    SIZE = np.ones(len(G), dtype=np.float64)
    idx = [[i] for i in range(len(G))]
    while len(idx) > 1:
        k = len(idx)
        MEAN = SUM / np.outer(SIZE, SIZE)
        iu = np.triu_indices(k, 1)
        vals = MEAN[iu]
        p = int(np.argmax(vals))                # erstes Maximum in Zeilenordnung = Tie-Break der Referenz-Schleife
        best = float(vals[p])
        bi, bj = int(iu[0][p]), int(iu[1][p])
        if best < sim:
            break
        idx[bi] = idx[bi] + idx[bj]
        SUM[bi, :] += SUM[bj, :]
        SUM[:, bi] += SUM[:, bj]                # SUM[bi,bi] ist danach die exakte Blocksumme des
        SIZE[bi] += SIZE[bj]                    # vereinigten Clusters (A+B+2C) — derzeit ungelesen
        SUM = np.delete(np.delete(SUM, bj, 0), bj, 1)   # (triu k=1); E3 kann daraus Cluster-
        SIZE = np.delete(SIZE, bj)                       # Kohaerenz gratis ziehen (Widerleger 30.07.)
        del idx[bj]
    # Repraesentanten-Tie-Break DETERMINISTISCH (E3-QS-Pflicht 'permutierte Reihenfolge =
    # identische Cluster'): bei guete-Gleichstand (9,7 % des Pools) hing Element 0 — die
    # UI-Kachel UND die benenne()-Referenzwahl — sonst an der Ladereihenfolge
    # (Widerleger 30.07.: Repraesentant kippte in 199/200 Permutationen).
    cluster = [sorted((G[i] for i in c), key=lambda g: (-g["guete"], g.get("id") or "")) for c in idx]
    cluster.sort(key=lambda c: (-len(c), c[0].get("id") or ""))
    return cluster


def _clustere_referenz(gesichter=None, sim=SIM_DEFAULT):
    """Referenz-Implementierung (bis 0.1.0.77 die produktive clustere()) — definiert die
    SEMANTIK des Clusterers und dient der qs-Stufe PYS7B als Partitions-Zwilling.
    Nicht im Produktionspfad aufrufen (O(n^3) mean-Aufrufe, ab ~300 Gesichtern Minuten)."""
    G = gesichter if gesichter is not None else lade_gesichter()
    if not G:
        return []
    M = np.asarray([g["emb"] for g in G], dtype=np.float32)
    S = M @ M.T                                          # Cosinus (Embeddings sind normiert)
    # AVERAGE-LINKAGE statt Greedy-Stern (Umbau 25.07., Backtest am echten Pool):
    # Der Stern verglich alles nur gegen EIN Seed-Gesicht — dieselbe Person zerfiel je nach
    # Seed in mehrere Identitaeten (gemessen: 29 Paare >=0.50 am selben Tag in getrennten
    # IDs, Spitze 0.91), und ein Radkasten-Seed fing Fremdes ein. Average-Linkage fuehrt
    # zusammen, solange die DURCHSCHNITTS-Aehnlichkeit zweier Gruppen >= sim bleibt —
    # im Backtest vereinigte das die Radkasten-Fragmente aus U34+U83 zu EINEM Cluster
    # und liess alle gesichtet-echten Personen (U19/U35/U64) unversehrt.
    idx = [[i] for i in range(len(G))]
    while len(idx) > 1:
        best, bi, bj = -1.0, -1, -1
        for i in range(len(idx)):
            for j in range(i + 1, len(idx)):
                v = float(S[np.ix_(idx[i], idx[j])].mean())
                if v > best:
                    best, bi, bj = v, i, j
        if best < sim:
            break
        idx[bi] = idx[bi] + idx[bj]
        del idx[bj]
    cluster = [sorted((G[i] for i in c), key=lambda g: -g["guete"]) for c in idx]
    cluster.sort(key=lambda c: -len(c))
    return cluster


# ---------------------------------------------------------------- Benennen (Cluster -> Referenzen)
def benenne(gesicht_ids, person, beste_n=5):
    """Die besten Gesichter eines Clusters als Referenzen fuer <person> in den Master legen.
    Legt refs/<person>/ an (neue Person moeglich), schreibt refs_meta, verwirft den refcache."""
    import re, shutil
    if not re.match(r"^[\w \-]{2,40}$", person or ""):
        return False, "ungueltiger Personenname"
    G = {g["id"]: g for g in lade_gesichter()}
    gewaehlt = [G[i] for i in gesicht_ids if i in G]
    gewaehlt.sort(key=lambda g: -g["guete"])
    gewaehlt = gewaehlt[:beste_n]
    if not gewaehlt:
        return False, "keine gueltigen Gesichter"
    zdir = os.path.join(MASTER, person)
    os.makedirs(zdir, exist_ok=True)
    meta = os.path.join(MASTER, "refs_meta.jsonl")
    n = 0
    with open(meta, "a") as mf:
        for g in gewaehlt:
            quelle = os.path.join(CROPS, g["id"] + ".jpg")
            if not os.path.exists(quelle):
                continue
            ziel = f"anlern_{int(time.time())}_{g['id'][-24:]}.jpg"
            shutil.copyfile(quelle, os.path.join(zdir, ziel))
            mf.write(json.dumps({"ts": round(time.time(), 1), "person": person, "datei": ziel,
                                 "herkunft": "anlernen", "eid": g["eid"], "aktiv": True},
                                ensure_ascii=False) + "\n")
            n += 1
        mf.flush()
    try:
        os.remove(os.path.join(CLIPS, "refcache.npz"))
    except FileNotFoundError:
        pass
    return True, f"{n} Referenzen fuer '{person}' angelegt"


# ---------------------------------------------------------------- Unbekannt-Identitaeten (persistent)
# User-Konzept 20.07.: der Unbekannt-Pool wird zu WIEDERKEHRENDEN Identitaeten (Unbekannt 1/2/3)
# gebuendelt, stabil ueber Tage. Der 06:00-Job pflegt sie (reconcile_unbekannte). Grenzfaelle
# (0.30-0.45; zwei verschiedene Fremde lagen auf unseren Daten bei 0.36) werden NICHT automatisch
# verschmolzen, sondern als "gleiche Person?"-Vorschlag gemeldet (Human-in-the-Loop).
UNB_PATH = os.path.join(ANLERN, "unbekannte.jsonl")
VORS_PATH = os.path.join(ANLERN, "unbekannte_vorschlaege.json")
VERWORFEN_PATH = os.path.join(ANLERN, "unbekannte_vorschlaege_verworfen.json")
# Zusammenlege-Vorschlaege: ab dieser Average-Linkage-Aehnlichkeit zwischen zwei Identitaeten
# wird gefragt "same person?". Gemessen 25.07. am echten Pool: die fuenf bekannten Echt-Paare
# (U19~U112/93/116/120, U1~U115) lagen bei 0.388-0.491, waehrend q99 ALLER aktiven Paare bei
# 0.411 lag und der Cluster-Cut bei 0.50 — das Band [0.38, Cut) faengt genau die Grenzfaelle,
# ohne die Seite zu fluten. Deckel haelt die Liste bedienbar (sortiert nach Aehnlichkeit).
VORSCHLAG_AB = 0.38
VORSCHLAG_MAX_N = 20


def lade_unbekannt_vorschlaege():
    if os.path.exists(VORS_PATH):
        try:
            return [(d["a"], d["b"]) for d in json.load(open(VORS_PATH))]
        except Exception:
            pass
    return []


def lade_verworfene_vorschlaege():
    """Vom User als 'Different' markierte Paare — als Menge ungeordneter Paare."""
    if os.path.exists(VERWORFEN_PATH):
        try:
            return {frozenset((d["a"], d["b"])) for d in json.load(open(VERWORFEN_PATH))}
        except Exception:
            pass
    return set()


def verwerfe_vorschlag(a, b):
    """'Different'-Klick persistent machen (Fix 25.07.): vorher blendete der Knopf die Zeile nur
    per display:none aus — nach dem naechsten Reload oder Reconcile stand dieselbe Frage wieder
    da. Jetzt: Paar in die Verworfen-Liste UND sofort aus der aktuellen Vorschlagsdatei nehmen;
    der Reconcile laesst verworfene Paare kuenftig aus."""
    a, b = str(a).strip(), str(b).strip()
    if not a or not b or a == b:
        return False
    with pool_lock():
        merk = lade_verworfene_vorschlaege()
        merk.add(frozenset((a, b)))
        tmp = VERWORFEN_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump([{"a": min(p), "b": max(p)} for p in merk], f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, VERWORFEN_PATH)
        rest = [(x, y) for x, y in lade_unbekannt_vorschlaege() if {x, y} != {a, b}]
        tmp = VORS_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump([{"a": x, "b": y} for x, y in rest], f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, VORS_PATH)
    return True


def lade_unbekannte():
    U = []
    if os.path.exists(UNB_PATH):
        for line in open(UNB_PATH):
            line = line.strip()
            if line:
                try:
                    U.append(json.loads(line))
                except Exception:
                    pass
    return U


def _speichere_unbekannte(idents):
    _schreibe_jsonl_atomar(UNB_PATH, idents)               # tmp+fsync+os.replace (Review 21.07.: fsync-Durability)


STATUS_PATH = os.path.join(ANLERN, "reconcile_status.json")


def _status(phase, done=0, total=0):
    """Fortschritt fuer die UI (Anforderung: laufende Arbeit muss sichtbar sein) —
    best effort, ein Fehlschlag hier darf nie die eigentliche Arbeit kosten."""
    try:
        tmp = STATUS_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"phase": phase, "done": done, "total": total, "ts": time.time()}, f)
        os.replace(tmp, STATUS_PATH)
    except Exception:
        pass


def _reconcile_intern(archiv_tage=7, sim=SIM_DEFAULT):
    """Ordnet die gesammelten Unbekannt-Gesichter persistenten Identitaeten zu — bestehende IDs
    bleiben stabil (Mehrheitsentscheid je Cluster ueber die schon zugeordneten Gesichter), neue
    Identitaeten kommen dazu, Einmal-Gaenger altern raus. Zusammenlege-Vorschlaege entstehen
    bei jedem Lauf frisch: aus Clustern, die zwei bestehende IDs ueberspannen, UND aus der
    Average-Linkage-Aehnlichkeit aller aktiven Identitaets-Paare (>= VORSCHLAG_AB) — NIE
    automatisch gemergt, verworfene Paare bleiben draussen. Rueckgabe: (identitaeten, vorschlaege)."""
    faces = {g["id"]: g for g in lade_gesichter()}
    idents = {u["id"]: u for u in lade_unbekannte()}
    face2id = {}
    for u in idents.values():
        u["members"] = [m for m in u.get("members", []) if m in faces]   # geloeschte Gesichter raus
        for m in u["members"]:
            face2id[m] = u["id"]
    _status("clustern", 0, len(faces))
    clusters = clustere(list(faces.values()), sim=sim) if faces else []
    _status("zuordnen", len(faces), len(faces))
    nums = [int(k[1:]) for k in idents if k[:1] == "U" and k[1:].isdigit()]
    naechste = (max(nums) + 1) if nums else 1
    neu, vorschlaege = {}, []
    for c in clusters:
        mids = [g["id"] for g in c]
        stimmen = collections.Counter(face2id[m] for m in mids if m in face2id)
        if stimmen:
            zid = stimmen.most_common(1)[0][0]
            for other in stimmen:
                if other != zid:
                    vorschlaege.append((zid, other))          # Cluster spannt mehrere Alt-IDs
        else:
            zid = f"U{naechste}"; naechste += 1
        if zid in neu:                                        # Alt-ID auf zwei Cluster aufgespalten
            orig = zid
            zid = f"U{naechste}"; naechste += 1
            vorschlaege.append((orig, zid))
        alt = idents.get(zid, {})
        tss = [faces[m]["ts"] for m in mids]
        neu[zid] = {"id": zid, "created": alt.get("created", min(tss)),
                    "first_seen": min(tss), "last_seen": max(tss),
                    "status": alt.get("status", "aktiv"), "label": alt.get("label"),
                    "members": mids}
    # OBJEKT-REGEL (25.07., an gesichteten Identitaeten kalibriert): ein statisches Objekt
    # (Radkasten, Lichtfleck) verraet sich dadurch, dass seine Bilder einander extrem aehneln
    # UND keinem Menschen aehneln — p90 der Selbstaehnlichkeit >= 0.75 UND Median-NN zu den
    # Referenzen < 0.20. Gemessen: Radkasten 0.805/0.16, Lichtflecken 0.93/0.13 — alle echten
    # Personen lagen bei p90 0.59-0.63 und NN 0.23-0.36. Cluster-Ebene ist entscheidend:
    # auf Einzelbild-Ebene ueberlappen die Werte (Testdurchgang 25.07.), im Kollektiv nicht.
    # Objekt-Identitaeten bleiben ERHALTEN (Flag, kein Loeschen) — sie fangen kuenftige
    # Radkasten-Crops weiter ein und halten sie damit von den Personen-Karten fern.
    for u in neu.values():
        ms = [m for m in u["members"] if m in faces]
        if len(ms) >= 2:
            E = np.asarray([faces[m]["emb"] for m in ms], np.float32)
            ober = (E @ E.T)[np.triu_indices(len(ms), 1)]
            p90 = float(np.quantile(ober, 0.9))
            nnm = float(np.median([faces[m].get("nn_score", 0) for m in ms]))
            u["objekt"] = bool(p90 >= 0.75 and nnm < 0.20)
        else:
            u["objekt"] = bool(idents.get(u["id"], {}).get("objekt", False))
    for u in neu.values():                                    # Einmal-Gaenger altern raus
        if u["status"] == "aktiv" and len(u["members"]) <= 1 and \
           (time.time() - u["last_seen"]) > archiv_tage * 86400:
            u["status"] = "archiviert"
    # ZUSAMMENLEGE-VORSCHLAEGE — bei JEDEM Lauf frisch aus der Identitaets-Aehnlichkeit
    # abgeleitet (Fix 25.07.): vorher entstanden Vorschlaege NUR im Moment eines Cluster-
    # uebergriffs; der naechste automatische Reconcile (laeuft nach jedem Durchgang) fand
    # saubere 1:1-Cluster und ueberschrieb die Datei mit [] — die 17 Vorschlaege des Abends
    # verschwanden, bevor der User sie beantworten konnte. Jetzt: Average-Linkage zwischen
    # den Mitglieds-Embeddings jedes aktiven Nicht-Objekt-Paars, ab VORSCHLAG_AB wird
    # gefragt; Clusteruebergriffe bleiben zusaetzlich immer drin (starke Evidenz).
    # Vom User verworfene Paare ('Different') bleiben persistent draussen.
    verworfen = lade_verworfene_vorschlaege()
    _embm = {}
    for u in neu.values():
        ms = [m for m in u["members"] if m in faces]
        if ms and u["status"] == "aktiv" and not u.get("objekt"):
            _embm[u["id"]] = np.asarray([faces[m]["emb"] for m in ms], np.float32)
    kand = {}
    for a, b in vorschlaege:
        if a != b and a in _embm and b in _embm:
            kand[frozenset((a, b))] = float((_embm[a] @ _embm[b].T).mean())
    _ids = sorted(_embm)
    for _i in range(len(_ids)):
        for _j in range(_i + 1, len(_ids)):
            s = float((_embm[_ids[_i]] @ _embm[_ids[_j]].T).mean())
            if s >= VORSCHLAG_AB:
                kand.setdefault(frozenset((_ids[_i], _ids[_j])), s)
    vs = sorted(((p, s) for p, s in kand.items() if p not in verworfen), key=lambda t: -t[1])
    vs = [(min(p), max(p)) for p, _ in vs[:VORSCHLAG_MAX_N]]
    _speichere_unbekannte(list(neu.values()))
    try:
        tmp = VORS_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump([{"a": a, "b": b} for a, b in vs], f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, VORS_PATH)                          # atomar + fsync (Review 21.07.)
    except Exception:
        pass
    _status("fertig", len(faces), len(faces))
    return list(neu.values()), vs


def reconcile_unbekannte(archiv_tage=7, sim=SIM_DEFAULT):
    """Gelockter Wrapper: serialisiert das Neu-Ordnen der Identitaeten gegen sammle/migriere und
    gegen ein zweites reconcile (Review 21.07.: sonst Last-Writer-Wins auf unbekannte.jsonl)."""
    with pool_lock():
        return _reconcile_intern(archiv_tage, sim)


def fd_nachpruefung():
    """#42 Teil B, einmalige Wartung: BESTEHENDE Unbekannt-Identitaeten gegen die
    Fehldetektions-Signatur nachpruefen (die U65/U66-Klasse: Gras/Hecke als Identitaet).
    Kennwerte der Altbestaende sind nicht persistiert -> Re-Detektion auf den
    gespeicherten Kontext-Crops (det 320). SICHERHEIT VOR WIRKUNG: ein Mitglied ohne
    wiederfindbares Gesicht zaehlt als NICHT beurteilbar (None), nie als Fehldetektion —
    ein kleines echtes Gesicht, das die Re-Detektion verfehlt, darf keine echte Person
    quarantaenieren. Geflaggt wird nur, wenn ALLE beurteilbaren Mitglieder die Signatur
    tragen; Flag = bestehendes objekt-Feld (Identitaet bleibt erhalten, faengt weitere
    Objekt-Crops, erscheint nicht als Person). Rest raeumt der User per UI bzw. die Zeit."""
    emb = Embedder()
    faces = {g["id"]: g for g in lade_gesichter()}
    geaendert = 0
    with pool_lock():
        idents = lade_unbekannte()
        for u in idents:
            if u.get("status") != "aktiv" or u.get("objekt"):
                continue
            urteile = []
            for m in u.get("members", []):
                if m not in faces:
                    continue
                pfad = os.path.join(CROPS, m + ".jpg")
                img = cv2.imread(pfad) if os.path.exists(pfad) else None
                if img is None:
                    urteile.append(None)
                    continue
                dets = emb.app.get(img)
                if not dets:
                    urteile.append(None)                   # nicht beurteilbar, NICHT fd
                    continue
                fc = max(dets, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                x1, y1, x2, y2 = [max(0, int(t)) for t in fc.bbox]
                crop = img[y1:y2, x1:x2]
                if not crop.size:
                    urteile.append(None)
                    continue
                urteile.append(ist_fehldetektion(frontality(fc), sharp(crop),
                                                 float(fc.det_score),
                                                 FD_FRONT_MIN, FD_SHARP_MIN, FD_DET_MAX))
            bewertet = [x for x in urteile if x is not None]
            if bewertet and all(bewertet):
                u["objekt"] = True
                geaendert += 1
                print(f"  {u['id']}: all {len(bewertet)} assessable member crop(s) match the "
                      f"non-face signature -> flagged as object", flush=True)
        if geaendert:
            _speichere_unbekannte(idents)
    print(f"fd re-check: {geaendert} identities flagged as objects", flush=True)
    return geaendert


def reorganisieren():
    """Reorganisieren-Button (User 21.07.): Pool-Neupruefung (migriere: Modell-Konsistenz + bekannt
    gewordene raus + tote Crops) und Identitaeten/Cluster neu bilden (reconcile). KEIN neues Sammeln
    (das laeuft kontinuierlich szenario-getriggert). Haelt den pool_lock, pausiert also das Sammeln,
    solange die Reorganisation laeuft ('Fleck', User 21.07.). Rueckgabe: (stat, identitaeten, vorschlaege)."""
    with pool_lock():
        emb = Embedder()
        refs = lade_master_refs(emb)
        stat = migriere_und_pruefe_pool(emb, refs)
        print(f"pool check: {stat}", flush=True)
    idents, vs = reconcile_unbekannte()                    # eigener Lock-Zyklus (kein Nesting)
    print(f"Reorganized: {len(idents)} identities, {len(vs)} suggestions", flush=True)
    return stat, idents, vs


def unbekannt_besucher(uid, an=True):
    """Gelockter Wrapper (Review 21.07.: serialisiert gegen reconcile/andere Pool-Schreiber)."""
    with pool_lock():
        return _unbekannt_besucher_intern(uid, an)


def _unbekannt_besucher_intern(uid, an=True):
    """Identitaet als bekannten Besucher markieren (ruhigstellen) bzw. zurueck auf aktiv."""
    U = lade_unbekannte()
    ok = False
    for u in U:
        if u["id"] == uid:
            u["status"] = "besucher" if an else "aktiv"
            ok = True
    if ok:
        _speichere_unbekannte(U)
    return ok


def unbekannt_merge(uid_a, uid_b):
    """Gelockter Wrapper (Review 21.07.)."""
    with pool_lock():
        return _unbekannt_merge_intern(uid_a, uid_b)


def _unbekannt_merge_intern(uid_a, uid_b):
    """Zwei Unbekannt-Identitaeten zusammenlegen (die kleinere ID bleibt)."""
    U = {u["id"]: u for u in lade_unbekannte()}
    if uid_a not in U or uid_b not in U or uid_a == uid_b:
        return False
    keep, drop = sorted([uid_a, uid_b], key=lambda k: int(k[1:]) if k[1:].isdigit() else 0)
    a, b = U[keep], U[drop]
    a["members"] = list(dict.fromkeys(a.get("members", []) + b.get("members", [])))
    a["first_seen"] = min(a.get("first_seen", 1e18), b.get("first_seen", 1e18))
    a["last_seen"] = max(a.get("last_seen", 0), b.get("last_seen", 0))
    del U[drop]
    _speichere_unbekannte(list(U.values()))
    return True


def unbekannt_benennen(uid, person, beste_n=6):
    """Gelockter Wrapper (Review 21.07.: serialisiert gegen das kontinuierliche Sammeln, das
    dieselbe gesichter.jsonl schreibt)."""
    with pool_lock():
        return _unbekannt_benennen_intern(uid, person, beste_n)


def _unbekannt_benennen_intern(uid, person, beste_n=6):
    """Eine Unbekannt-Identitaet zu einer bekannten Person machen: beste Gesichter als Referenzen
    anlegen, die Gesichter aus dem Unbekannt-Pool entfernen (Crops + gesichter.jsonl), Identitaet
    entfernen. Ab dem naechsten Event wird die Person erkannt und taucht nicht mehr als unbekannt auf."""
    U = {u["id"]: u for u in lade_unbekannte()}
    if uid not in U:
        return False, "Identitaet nicht gefunden"
    mids = U[uid].get("members", [])
    ok, msg = benenne(mids, person, beste_n=beste_n)
    if not ok:
        return False, msg
    # Gesichter aus dem Pool nehmen, damit sie nicht wieder als unbekannt clustern
    weg = set(mids)
    G = [g for g in lade_gesichter() if g["id"] not in weg]
    _schreibe_jsonl_atomar(GES_PATH, G)                     # atomar + gelockt (Review 21.07.)
    for mid in mids:
        try:
            os.remove(os.path.join(CROPS, mid + ".jpg"))
        except FileNotFoundError:
            pass
    del U[uid]
    _speichere_unbekannte(list(U.values()))
    return True, msg


# ---------------------------------------------------------------- Referenz-QS (Verwechslungs-Check)
QS_PATH = os.path.join(ANLERN, "refs_qs.json")


def bild_metriken(emb, img):
    """QS-Metriken eines Einzelbilds (det 320): (embedding|None, gesichts_kante_orig|None,
    sharp). kante = Gesichtsgroesse in ORIGINAL-Pixeln (Upscaling wie Embedder.embed
    herausgerechnet). Eine Quelle fuer Eignungspruefung UND Bestands-Suche — was die Suche
    vorschlaegt, besteht damit garantiert auch die Pruefung."""
    h, w = img.shape[:2]
    sh = float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    scale = max(1.0, 224.0 / min(h, w))
    gross = cv2.resize(img, (round(w * scale), round(h * scale)),
                       interpolation=cv2.INTER_CUBIC) if scale > 1.0 else img
    faces = emb.app.get(gross)
    if not faces:
        return None, None, round(sh, 0)
    fc = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
    x1, y1, x2, y2 = fc.bbox
    kante = round(min(x2 - x1, y2 - y1) / scale)
    return np.asarray(fc.normed_embedding, dtype=np.float32), kante, round(sh, 0)


def lade_master_bilder(emb):
    """Alle Referenzbilder EINZELN mit Eignungs-Metriken (det 320, Ref-Crops). Liefert AUCH
    Bilder ohne detektierbares Gesicht (emb None) und defekte Dateien — genau die gehoeren
    in die Eignungspruefung, nicht stillschweigend uebersprungen."""
    out = []
    if not os.path.isdir(MASTER):
        return out
    for p in sorted(os.listdir(MASTER)):
        pd = os.path.join(MASTER, p)
        if not os.path.isdir(pd):
            continue
        for f in sorted(os.listdir(pd)):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            img = cv2.imread(os.path.join(pd, f))
            if img is None:
                out.append({"person": p, "datei": f, "emb": None, "sharp": 0.0,
                            "kante": None, "wh": "?", "defekt": True})
                continue
            v, kante, sh = bild_metriken(emb, img)
            out.append({"person": p, "datei": f, "emb": v, "sharp": sh,
                        "kante": kante, "wh": f"{img.shape[1]}x{img.shape[0]}", "defekt": False})
    return out


def pruefe_referenzen(flag_sim=0.30, top=40, unscharf_max=350, min_kante=70):
    """Referenz-QS in zwei Teilen: (1) EIGNUNG jedes einzelnen Bildes — defekt / kein
    Gesicht detektierbar / Gesicht zu klein / unscharf (alles Loesch-Kandidaten, nach
    Grund gruppiert); (2) Cross-Person-VERWECHSLUNG ueber die Bilder mit Embedding
    ('kritisch' bei hoher Fremd-Aehnlichkeit oder fremd >= eigen = Fehllabel-Verdacht).
    Ergebnis -> refs_qs.json fuer den Qualitaet-Reiter."""
    emb = Embedder()                              # det 320 default — genau richtig fuer Ref-Crops
    B = lade_master_bilder(emb)
    PRIO = ("defekt", "kein_gesicht", "zu_klein", "unscharf")
    ungeeignet = []
    for b in B:
        gruende = []
        if b.get("defekt"):
            gruende.append("defekt")
        elif b["emb"] is None:
            gruende.append("kein_gesicht")
        elif b["kante"] is not None and b["kante"] < min_kante:
            gruende.append("zu_klein")
        if not b.get("defekt") and b["sharp"] < unscharf_max:
            gruende.append("unscharf")
        if gruende:
            ungeeignet.append({"person": b["person"], "datei": b["datei"],
                               "gruende": gruende, "hauptgrund": next(g for g in PRIO if g in gruende),
                               "sharp": b["sharp"], "kante": b["kante"], "wh": b["wh"]})
    ungeeignet.sort(key=lambda u: (PRIO.index(u["hauptgrund"]), u["kante"] or 0, u["sharp"]))
    BE = [b for b in B if b["emb"] is not None]
    paare = []
    if len(BE) >= 2:
        M = np.asarray([b["emb"] for b in BE], np.float32)
        S = M @ M.T
        pers = [b["person"] for b in BE]
        roh = []
        for i in range(len(BE)):
            best_j, best_s, eigen = -1, -1.0, []
            for j in range(len(BE)):
                if j == i:
                    continue
                if pers[j] == pers[i]:
                    eigen.append(S[i, j])
                elif S[i, j] > best_s:
                    best_j, best_s = j, S[i, j]
            if best_j < 0:
                continue
            # koh None bei Ein-Bild-Personen: sonst waere JEDES ihrer Paare automatisch
            # "fehllabel_verdacht" (best_s >= 0.0 stimmt immer, Review-Finding 19.07.)
            koh = float(np.mean(eigen)) if eigen else None
            fehllabel = bool(koh is not None and best_s >= koh)
            roh.append({"a_person": pers[i], "a_datei": BE[i]["datei"],
                        "b_person": pers[best_j], "b_datei": BE[best_j]["datei"],
                        "sim": round(float(best_s), 3),
                        "eigen_koh": round(koh, 3) if koh is not None else None,
                        "kritisch": bool(best_s >= flag_sim or fehllabel),
                        "fehllabel_verdacht": fehllabel})
        seen = {}                                 # symmetrische Paare (A-B == B-A) zusammenfassen
        for pr in sorted(roh, key=lambda x: -x["sim"]):
            key = tuple(sorted([pr["a_person"] + "/" + pr["a_datei"],
                                pr["b_person"] + "/" + pr["b_datei"]]))
            if key not in seen:
                seen[key] = pr
        paare = sorted(seen.values(), key=lambda x: (-int(x["kritisch"]), -x["sim"]))[:top]
    os.makedirs(ANLERN, exist_ok=True)
    _schreibe_json_atomar(QS_PATH, {"ts": time.time(), "ref_count": len(B), "flag_sim": flag_sim,
                                    "unscharf_max": unscharf_max, "min_kante": min_kante,
                                    "paare": paare, "ungeeignet": ungeeignet})
    # refcache im analyze-Format gleich mitschreiben (identische det-320-Embeddings, meta =
    # sortierte Dateilisten wie sync_refs.master_stand): /aehnliche und analyze funktionieren
    # damit SOFORT nach Loeschungen/Anlernen, ohne auf das naechste Kamera-Event zu warten
    # (User-Befund 19.07.: "Referenz-Cache wird gerade neu aufgebaut" nach dem Aufraeumen)
    try:
        want = {}
        refs = {}
        for b in B:
            want.setdefault(b["person"], []).append(b["datei"])
            refs.setdefault(b["person"], [])
        for b in BE:
            refs[b["person"]].append(b["emb"])
        os.makedirs(CLIPS, exist_ok=True)
        # Atomar (tmp + fsync + os.replace) wie in analyze.py: analyze LIEST diesen Cache, waehrend
        # dieser Lauf ihn schreibt — direkt aufs Ziel geschrieben, konnte der Leser eine halbe npz
        # erwischen (BadZipFile -> Event "fehler"). Meta unter '§meta' statt dem Keyword meta=:
        # eine Person namens "meta" haette sonst mit np.savez kollidiert (TypeError bei JEDEM Lauf).
        ziel = os.path.join(CLIPS, "refcache.npz")
        tmp = f"{ziel}.tmp-{os.getpid()}"
        try:
            with open(tmp, "wb") as f:
                np.savez(f, **{"§meta": json.dumps({**want, "§modell": emb.modell})},
                         **{p: (np.asarray(v, np.float32) if v else np.zeros((0, 512), np.float32))
                            for p, v in refs.items()})
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, ziel)
        except Exception:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise
    except Exception as e:
        print(f"refcache not written: {e}", flush=True)   # Cache ist Beschleunigung, kein Muss —
                                                                # aber nicht mehr STILL scheitern
    return {"paare": paare, "ungeeignet": ungeeignet}


def entferne_referenz(person, datei):
    """Ein einzelnes Referenzbild aus dem Master loeschen — Datei weg, TOMBSTONE in refs_meta
    (aktiv:false; NICHT die Zeile entfernen: ohne Tombstone wuerde sync_refs das in Frigate
    noch vorhandene Bild als 'neu' re-importieren), QS-Liste sofort bereinigen (die Seite
    zeigte sonst tote Bild-Links, bis der Hintergrund-Neulauf fertig ist), refcache verworfen.
    Nur innerhalb refs/ (Containment)."""
    import re
    if not re.match(r"^[\w \-]{1,40}$", person or "") or not re.match(r"^[\w .\-]+$", datei or ""):
        return False, "ungueltiger Pfad"
    base = os.path.realpath(MASTER)
    ziel = os.path.realpath(os.path.join(base, person, datei))
    if not ziel.startswith(base + os.sep) or not os.path.isfile(ziel):
        return False, "Bild nicht gefunden"
    os.remove(ziel)
    with open(os.path.join(MASTER, "refs_meta.jsonl"), "a") as f:
        f.write(json.dumps({"ts": round(time.time(), 1), "person": person, "datei": datei,
                            "aktiv": False, "grund": "ui-entfernt"}, ensure_ascii=False) + "\n")
        f.flush()
    try:
        qs = json.load(open(QS_PATH))
        qs["paare"] = [p for p in qs.get("paare", [])
                       if not ((p["a_person"] == person and p["a_datei"] == datei) or
                               (p["b_person"] == person and p["b_datei"] == datei))]
        qs["ungeeignet"] = [u for u in qs.get("ungeeignet", [])
                            if not (u["person"] == person and u["datei"] == datei)]
        qs.pop("unscharf", None)
        _schreibe_json_atomar(QS_PATH, qs)     # 2. Schreiber (Dienst); der 1. ist der pruefe-Subprozess
    except Exception:
        pass
    try:
        os.remove(os.path.join(CLIPS, "refcache.npz"))
    except FileNotFoundError:
        pass
    return True, f"{person}/{datei} entfernt"


def _cache_meta(z):
    """Meta-Block des refcache lesen — '§meta' (neu) mit Fallback 'meta' (Alt-Cache).
    MUSS analyze._refcache_meta spiegeln. Fund 25.07. (User: "Neu suchen tut nichts"):
    analyze schreibt seit Welle 3 unter '§meta', die Leser hier fragten noch z["meta"] ab —
    der KeyError landete im except und machte aehnliche_unbekannte() DAUERHAFT None. Die
    /aehnliche-Seite zeigte deshalb fuer immer "Search running", ohne je fertig zu werden.
    Vertragsbruch zwischen zwei Dateien: der Schreiber wurde geaendert, die Leser nicht."""
    key = "§meta" if "§meta" in z.files else "meta"
    return json.loads(str(z[key]))


def aehnliche_unbekannte(person, max_n=12, min_sim=0.28):
    """Umgedrehter Weg (User 19.07.): gesammelte UNBEKANNTE Gesichter, sortiert nach Aehnlichkeit
    zu den vorhandenen Referenzen von <person>. Nutzt den refcache (von analyze gepflegt, det 320)
    — schnell, kein Embedder. Rueckgabe: Liste (evtl. leer), oder None wenn der Cache die Person
    noch nicht kennt (frisch invalidiert -> Aufrufer zeigt Hinweis)."""
    cache = os.path.join(CLIPS, "refcache.npz")
    if not os.path.exists(cache):
        return None
    try:
        z = np.load(cache)
    except Exception:
        return None
    try:                                              # Modell-Mix verhindern: Cache eines anderen
        if str(_cache_meta(z).get("§modell", "")) != aktuelles_modell():
            return None                               # Recognition-Modells ist unvergleichbar
    except Exception:
        return None
    if person not in z.files:
        return None
    R = np.asarray(z[person], np.float32)
    if len(R) == 0:
        return []
    # pro (person,datei): aktiv-Status aus der LETZTEN Zeile, eid aus IRGENDEINER Zeile des
    # Keys — spaetere Zeilen ohne eid (z.B. der Export-Vermerk von sync_refs) duerfen die
    # benenne-Zuordnung nicht verdraengen (Review-Finding 19.07.); ein geloeschtes
    # Referenzbild (Tombstone) gibt sein Gesicht wieder fuer Vorschlaege frei
    status_aktiv, eids = {}, {}
    meta = os.path.join(MASTER, "refs_meta.jsonl")
    if os.path.exists(meta):
        for line in open(meta):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if not (d.get("person") and d.get("datei")):
                continue
            key = (d["person"], d["datei"])
            status_aktiv[key] = d.get("aktiv", True)
            if d.get("eid"):
                eids[key] = str(d["eid"]).replace("/", "_")
    zugeordnet = {eids[k] for k, ak in status_aktiv.items() if ak and k in eids}
    out = []
    for g in lade_gesichter():
        if g["id"] in zugeordnet:
            continue
        v = np.asarray(g["emb"], np.float32)
        s = float((R @ v).max())
        if s >= min_sim:
            out.append({"id": g["id"], "camera": g.get("camera"), "ts": g.get("ts"),
                        "nn_person": g.get("nn_person"), "nn_score": g.get("nn_score"),
                        "sim": round(s, 3)})
    out.sort(key=lambda x: -x["sim"])
    return out[:max_n]


# ---------------------------------------------------------------- Bestands-Suche (bekannte Personen)
def _vorschlaege_pfad(person):
    return os.path.join(ANLERN, "vorschlaege_" + person.replace(" ", "_") + ".json")


def lade_vorschlaege(person):
    p = _vorschlaege_pfad(person)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:
        return None


def vorschlaege_person(person, tage=7.0, max_n=16, min_kante=70, unscharf_max=350,
                       sim_min=0.45, sim_neu=0.75, sim_unsicher=0.30, abstand=0.10,
                       kante_gut=120, sharp_gut=700, max_pruef=80):
    """Bestands-Suche (User 19.07.): durchsucht die Events der Person aus den letzten Tagen
    nach referenz-tauglichen NEUEN Gesichtern. Quelle sind Events, in denen die Person
    bestaetigt ist ODER (User 21.07.) ihr bestes Match ist — so tauchen auch SCHWACH
    erkannte frische Gesichter auf, die knapp unter der Erkennungsschwelle blieben (bester
    Nachlern-Stoff bei duenn angelernten Personen). Zwei Achsen (User 21.07.):
      Identitaet   = sicher (eigen>=sim_min) / wahrscheinlich (eigen>=sim_unsicher &
                     eigen-fremd>=abstand) / unsicher (raus)
      Bildqualitaet= gut (kante>=kante_gut & sharp>=sharp_gut) / maessig (>= Mindest-Gate
                     kante>=min_kante & sharp>=unscharf_max) / unbrauchbar (raus)
    Stufe: sicher&gut -> 'empfohlen'; genau eins von beiden -> 'neutral'; sonst -> raus
    ('Not recommended' wird NICHT angezeigt). Neuheit: eigen<sim_neu, sonst Duplikat.
    Neueste Events zuerst, hoechstens max_pruef Bild-Messungen. Ergebnis -> vorschlaege_*.json."""
    emb = Embedder()
    refs = {}
    cache = os.path.join(CLIPS, "refcache.npz")
    if os.path.exists(cache):                      # pruefe_referenzen haelt ihn frisch
        try:
            z = np.load(cache, allow_pickle=True)
            if str(_cache_meta(z).get("§modell", "")) != emb.modell:
                raise ValueError("refcache anderes Recognition-Modell")   # -> frisch aus Master
            refs = {p: np.asarray(z[p], np.float32) for p in z.files if p not in ("meta", "§meta")}
        except Exception:
            refs = {}
    if not len(refs.get(person, [])):
        refs = lade_master_refs(emb)
    kand = []
    if len(refs.get(person, [])):
        grenze = time.time() - tage * 86400
        dp = os.path.join(DATA, "state", "deckung.jsonl")
        # 1) billiger Vorfilter (kein Embedder): Events, in denen die Person bestaetigt ist
        #    ODER ihr bestes Match ist (schwach erkannt, User 21.07.). Neueste zuerst.
        seen = set()
        eventliste = []
        for line in (open(dp) if os.path.exists(dp) else []):
            try:
                d = json.loads(line)
            except Exception:
                continue
            eid = d.get("eid")
            if not eid or eid in seen or (d.get("ts") or 0) < grenze:
                continue
            if person not in (d.get("bestaetigt") or []):
                ours = d.get("ours") or {}
                if not ours:
                    continue
                top = max(ours, key=lambda p: (ours[p] or {}).get("max", 0) or 0)
                if top != person:
                    continue
            seen.add(eid)
            eventliste.append(d)
        eventliste.sort(key=lambda d: -(d.get("start") or d.get("ts") or 0))   # neueste zuerst
        # 2) teure Bild-Messung nur auf die neuesten max_pruef Events mit Crop
        geprueft = 0
        gedeckelt = False
        for d in eventliste:
            ed = os.path.join(DATA, "events", d["eid"].replace("/", "_"))
            if not os.path.isdir(ed):
                continue
            js = ([f for f in os.listdir(ed) if f"_show_{person}_" in f] or
                  [f for f in os.listdir(ed) if f"_best_{person}_NN" in f])
            if not js:
                continue
            if geprueft >= max_pruef:
                gedeckelt = True
                break
            img = cv2.imread(os.path.join(ed, js[0]))
            if img is None:
                continue
            geprueft += 1
            v, kante, sh = bild_metriken(emb, img)
            # Bildqualitaet-Mindest-Gate: zu klein/unscharf -> unbrauchbare Referenz
            if v is None or kante is None or kante < min_kante or sh < unscharf_max:
                continue
            eigen = float((refs[person] @ v).max())
            fremd = max((float((M @ v).max()) for p2, M in refs.items()
                         if p2 != person and len(M)), default=-1.0)
            if eigen >= sim_neu or fremd >= eigen:        # Duplikat des Bestands oder naeher an fremd
                continue
            # Achse 1 Identitaet: sicher / wahrscheinlich (HITL, Grenzfall 19.07.) / unsicher(raus)
            if eigen >= sim_min:
                id_sicher = True
            elif eigen >= sim_unsicher and (eigen - fremd) >= abstand:
                id_sicher = False
            else:
                continue                                   # unsicher -> Not recommended, nicht zeigen
            # Achse 2 Bildqualitaet gut/maessig (Mindest-Gate ist schon bestanden)
            qual_gut = kante >= kante_gut and sh >= sharp_gut
            # Zwei-Achsen-Matrix -> nur die oberen zwei Stufen behalten (User 21.07.)
            if id_sicher and qual_gut:
                stufe = "empfohlen"
            elif id_sicher or qual_gut:
                stufe = "neutral"
            else:
                continue                                   # wahrscheinlich + maessig -> raus
            kand.append({"eid": d["eid"], "datei": js[0], "sim": round(eigen, 3),
                         "fremd": round(fremd, 3), "kante": kante, "sharp": sh,
                         "stufe": stufe, "sicher": (stufe == "empfohlen"),
                         "camera": d.get("camera"), "ts": d.get("start") or d.get("ts")})
        kand.sort(key=lambda k: (0 if k["stufe"] == "empfohlen" else 1, k["sim"]))
        kand = kand[:max_n]
        if gedeckelt:
            print(f"vorschlaege {person}: cap of {max_pruef} image measurements reached, "
                  f"older events unchecked", flush=True)
    os.makedirs(ANLERN, exist_ok=True)
    _schreibe_json_atomar(_vorschlaege_pfad(person),
                          {"ts": time.time(), "person": person, "tage": tage, "kandidaten": kand})
    return kand


def vorschlag_aufnehmen(person, eid, datei):
    """Einen Bestands-Vorschlag als Referenz uebernehmen: Event-Crop -> Master (Containment),
    refs_meta, refcache-Invalidierung; Vorschlags-JSON um den Eintrag bereinigen."""
    import re, shutil
    if not re.match(r"^[\w \-]{2,40}$", person or "") or not re.match(r"^[\w .\-]+\.jpg$", datei or "", re.I):
        return False, "ungueltige Angaben"
    ed = str(eid).replace("/", "_")
    basis = os.path.realpath(os.path.join(DATA, "events"))
    quelle = os.path.realpath(os.path.join(basis, ed, datei))
    if not quelle.startswith(basis + os.sep) or not os.path.isfile(quelle):
        return False, "Vorschlags-Crop nicht gefunden"
    zdir = os.path.join(MASTER, person)
    os.makedirs(zdir, exist_ok=True)
    ziel = f"bestand_{int(time.time())}_{ed[-10:]}_{re.sub(r'[^\w.-]', '_', datei)[-30:]}"
    shutil.copyfile(quelle, os.path.join(zdir, ziel))
    with open(os.path.join(MASTER, "refs_meta.jsonl"), "a") as f:
        f.write(json.dumps({"ts": round(time.time(), 1), "person": person, "datei": ziel,
                            "herkunft": "bestands-suche", "eid": eid, "aktiv": True},
                           ensure_ascii=False) + "\n")
        f.flush()
    v = lade_vorschlaege(person)
    if v:
        v["kandidaten"] = [k for k in v.get("kandidaten", [])
                           if not (k.get("eid") == eid and k.get("datei") == datei)]
        _schreibe_json_atomar(_vorschlaege_pfad(person), v)   # parallel zum vorschlaege-Subprozess
    try:
        os.remove(os.path.join(CLIPS, "refcache.npz"))
    except FileNotFoundError:
        pass
    return True, f"{ziel} aufgenommen"


# ---------------------------------------------------------------- CLI
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("sammle"); s.add_argument("--tage", type=float, default=5.0)
    s.add_argument("--kein-migriere", action="store_true")   # szenario-getriggert: nur sammeln, keine Pool-Neupruefung
    sub.add_parser("reorganisieren")                         # Button/Wartung: migriere + reconcile (kein neues Sammeln)
    sub.add_parser("fd-nachpruefung")                        # #42 Teil B: Alt-Pool einmalig gegen die Fehldetektions-Signatur
    c = sub.add_parser("cluster"); c.add_argument("--sim", type=float, default=SIM_DEFAULT)
    pr = sub.add_parser("pruefe"); pr.add_argument("--sim", type=float, default=0.30)
    pr.add_argument("--unscharf", type=int, default=350)
    pr.add_argument("--minkante", type=int, default=70)
    vo = sub.add_parser("vorschlaege"); vo.add_argument("person")
    vo.add_argument("--tage", type=float, default=7.0)
    vo.add_argument("--unscharf", type=int, default=350)
    vo.add_argument("--minkante", type=int, default=70)
    a = ap.parse_args()
    if a.cmd == "sammle":
        sammle(a.tage, mit_migriere=not a.kein_migriere)
    elif a.cmd == "reorganisieren":
        reorganisieren()
    elif a.cmd == "fd-nachpruefung":
        fd_nachpruefung()
    elif a.cmd == "cluster":
        cl = clustere(sim=a.sim)
        print(f"\n{len(cl)} groups (sim>={a.sim}):")
        for k, c in enumerate(cl):
            rep = c[0]
            print(f"  group {k}: {len(c)} face(s) | representative {rep['id']} "
                  f"({rep['camera']}, nearest known: {rep['nn_person']} {rep['nn_score']}) | "
                  f"cameras: {sorted(set(g['camera'] for g in c))}")
    elif a.cmd == "pruefe":
        erg = pruefe_referenzen(a.sim, unscharf_max=a.unscharf, min_kante=a.minkante)
        paare, ug = erg["paare"], erg["ungeeignet"]
        import collections
        print(f"\nSUITABILITY: {len(ug)} images flagged:",
              dict(collections.Counter(u["hauptgrund"] for u in ug)))
        kanten = sorted(u["kante"] for u in ug if u["kante"] is not None)
        if kanten:
            print(f"  face edges of the flagged: min {kanten[0]} / median "
                  f"{kanten[len(kanten)//2]} / max {kanten[-1]} px")
        krit = [p for p in paare if p["kritisch"]]
        print(f"\nCONFUSION: {len(krit)} critical pairs "
              f"(of {len(paare)} top cross-similarities considered):")
        for p in paare[:15]:
            flag = "!! " if p["kritisch"] else "   "
            fl = " <- MISLABEL SUSPECT" if p["fehllabel_verdacht"] else ""
            ek = f"{p['eigen_koh']:.2f}" if p["eigen_koh"] is not None else "—"
            print(f"  {flag}{p['sim']:.2f}  {p['a_person']}/{p['a_datei'][:22]} <-> "
                  f"{p['b_person']}/{p['b_datei'][:22]}  (own {ek}){fl}")
    elif a.cmd == "vorschlaege":
        kand = vorschlaege_person(a.person, tage=a.tage, min_kante=a.minkante,
                                  unscharf_max=a.unscharf)
        print(f"\n{len(kand)} reference suggestions for {a.person}:")
        for k in kand:
            print(f"  sim={k['sim']} fremd={k['fremd']} kante={k['kante']} sharp={k['sharp']:.0f} "
                  f"{k['camera']} {k['eid']}")
    else:
        ap.print_help()
