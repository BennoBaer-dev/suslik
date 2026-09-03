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
import os, sys, json, time, argparse, collections, fcntl, tempfile, threading
from contextlib import contextmanager
os.environ.setdefault("OV_DEVICE", "GPU")
from core.pfade import WURZEL as HERE   # M0-Anker (Falle 0): eine Pfad-Quelle
sys.path.insert(0, HERE)
import cv2
import numpy as np
from face_audit import Embedder, aktuelles_modell, ist_fehldetektion
from core.unbekanntpool import ARCHIV_TAGE   # EINE Quelle: Archiv-/Reaktivierungs-Fenster (auch Today-Kachel)
from core.benennung import REF_LATTE         # .265 EINE Quelle: Referenz-Latte (auch _reihung/empfehlen)
from core import atomar as _atomar           # .411: eindeutige tmp beim atomaren Schreiben (refcache.npz)

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


def _latte_aus_env(name):
    """Eine Latte (Dict) aus der Prozess-Umgebung -> Dict, im Zweifel leer.
    LEER heisst 'Achse aus' und damit KEIN Ausschluss — dieselbe Regel, die
    core.benennung.harte_linie fuer fehlende Messwerte fuehrt. Kaputtes JSON
    darf den Sammler nie toeten, kostet aber die Achse."""
    try:
        d = json.loads(os.environ.get(name) or "{}")
    except Exception:                                   # noqa: BLE001
        d = None
    return d if isinstance(d, dict) else {}


# .380 (Beschluss 31.08. "Gruppenbildungs-Vereinheitlichung"): die Latten des
# POOL-ZULAUFS. verifyd reicht die FERTIGEN Dicts als JSON durch die Env
# (norm_latte_aus_cfg / guete_latte_aus_cfg) — hier wird bewusst KEIN
# Config-Schluessel ein zweites Mal ausgewaehlt, sonst haette der Pool seine
# eigene Auswahl und driftete gegen Lernlauf und Anzeige (K3-Regel).
# Vererbungs-Muster wie VERIFY_DATA_DIR/VERIFY_FD_*: Worker und Subprozess
# erben die Umgebung des Dienstes. Ohne Dienst (CLI, Gate-Fixtures) bleiben
# beide leer und der Zulauf verhaelt sich wie vor .380.
NORM_LATTE_ZULAUF = _latte_aus_env("VERIFY_NORM_LATTE")
GUETE_LATTE_ZULAUF = _latte_aus_env("VERIFY_GUETE_LATTE")
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
def lade_master_refs(emb, puls=None):
    """Embeddings aller bekannten Personen aus dem Master — MIT det 320 (kleine Ref-Crops),
    VOR dem Umschalten auf 1280 fuers Video (Memory-Regel: sonst brechen die Embeddings ein).
    Vorrats-Referenzen (A2, core/refbeiwert-Vertrag Stelle 1): ihr Vektor kommt
    aus dem refs_meta-Beiwert, NIE aus embed(datei) — die kleinen Crops sind
    fuer die Datei-Detektion gemessen tot (28/40).
    puls(i, n) (.311, optional): Fortschritt je Referenzbild — n wird VORAB
    gezaehlt, i laeuft ueber alle Bilddateien (Beiwert-Referenzen zaehlen mit,
    sie sind nur schneller). Reihenfolge und Ergebnis bleiben ohne Puls
    byte-gleich; der einzige Verbraucher ist refcache_aufbauen (Balken)."""
    from core import refbeiwert as _rb
    refs = {}
    if not os.path.isdir(MASTER):
        return refs
    endungen = (".jpg", ".jpeg", ".png", ".webp")
    i = n = 0
    if puls:
        for p in os.listdir(MASTER):
            pd = os.path.join(MASTER, p)
            if os.path.isdir(pd):
                n += sum(1 for f in os.listdir(pd) if f.lower().endswith(endungen))
        puls(0, n)
    bw, fremd = _rb.beiwerte(MASTER, emb.modell)
    if fremd:
        print(f"lade_master_refs: {fremd} stock reference(s) carry an embedding "
              f"for another model — not usable, re-learn them", flush=True)
    for p in sorted(os.listdir(MASTER)):
        pd = os.path.join(MASTER, p)
        if not os.path.isdir(pd):
            continue
        V = []
        for f in os.listdir(pd):
            if not f.lower().endswith(endungen):
                continue
            i += 1
            if puls:
                puls(i, n)
            b = bw.get((p, f))
            if b is not None:
                V.append(np.asarray(b["emb"], dtype=np.float32))
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
    # .380: die vier Zulauf-Linien gehoeren MIT in den Tag — sie entscheiden
    # jetzt ueber den Pool-Eintritt, also gilt fuer sie derselbe Satz wie fuer
    # die FD-Schwellen (Review .52: sonst wirkt eine Schwellenaenderung nie auf
    # abgehakte Events). Preis, bewusst: nach diesem Update laeuft das Fenster
    # einmal neu durch — genau das soll es, denn die Zeilen bekommen dabei ihre
    # Messwerte.
    _z = "/".join(str(x) for x in
                  (NORM_LATTE_ZULAUF.get("struktur"), NORM_LATTE_ZULAUF.get("veto"),
                   GUETE_LATTE_ZULAUF.get("empfinden_min"), GUETE_LATTE_ZULAUF.get("t_min")))
    return f"{aktuelles_modell()}|k{MIN_KANTE}|d{MIN_DET}|ff{FD_FRONT_MIN}|fs{FD_SHARP_MIN}|fx{FD_DET_MAX}|z{_z}"   # FD-Schwellen im Tag (Review .52: sonst wirkt eine Schwellenaenderung nie auf abgehakte Events)


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


_STRUKTURMASS = None


def _strukturmass_geteilt():
    """Die eine StrukturMass dieses Prozesses (.380) — lazy und bewusst NEBEN dem
    schon warmen Embedder gebaut: dort kostet sie gemessen 0 MB RSS und 0,2 s,
    in einem nackten Prozess dagegen +464 MB (Bauort-Regel im Docstring von
    face_audit.StrukturMass). ok=False -> None; die Struktur-Achse ist dann
    nicht gemessen, und nicht gemessen heisst nie 'schlecht'."""
    global _STRUKTURMASS
    if _STRUKTURMASS is None:
        from face_audit import StrukturMass
        _STRUKTURMASS = StrukturMass()
    return _STRUKTURMASS if _STRUKTURMASS.ok else None


def _zulauf_messen(k, sm):
    """Die Zulauf-Masse EINES Pool-Kandidaten in seine Zeile schreiben:
    `struktur` (StrukturMass am engen Crop) sowie `fiqa_t`/`empf` (core.guete).
    -> vergangene Sekunden (der Sammler bilanziert sie am Ende, nichts still).

    NUR HIER gemessen, und nur fuer Kandidaten, die tatsaechlich in den Pool
    eintreten wuerden — nicht fuer jede Detektion des Clips: der Sammler sieht
    je Event Hunderte, und die drei Netze gehoeren nicht in den heissen
    Analyse-Pfad (User-Auflage 31.08.).

    AUSSCHNITTE WORTGLEICH ZUR ERNTE (core/ernte.py): Struktur und Empfinden am
    ENGEN Gesichts-Crop, fiqa_t am ALIGNED 112er DERSELBEN Detektion. Ein
    zweiter Zuschnitt haette eine eigene Skala — die Regler der Kalibrier-Seite
    wuerden im Pool etwas anderes bedeuten als in der Gruppen-Flaeche.

    Drei Felder werden IMMER gesetzt, notfalls auf None: eine Pool-Zeile sagt
    damit selbst, ob sie gemessen ist. Ein Messfehler kostet nur den Wert, nie
    den Lauf; halb gemessen zaehlt als nicht gemessen (die Guete-Latte urteilt
    nur ueber Zeilen mit BEIDEN Massen)."""
    t0 = time.time()
    k["struktur"] = k["fiqa_t"] = k["empf"] = None
    crop, al = k.get("_crop"), k.get("_al")
    hat_crop = crop is not None and getattr(crop, "size", 0)
    if sm is not None and hat_crop:
        k["struktur"] = sm.streuung(crop)
    if hat_crop and al is not None:
        from core import guete as _guete
        if _guete.verfuegbar():
            try:
                k["fiqa_t"] = round(float(_guete.fiqa_t(al)), 4)
                k["empf"] = round(float(_guete.empfinden(crop)), 4)
            except Exception:                                  # noqa: BLE001
                k["fiqa_t"] = k["empf"] = None
    return time.time() - t0


def _zulauf_urteil(k):
    """core.benennung.pool_zulauf mit den Latten DIESES Prozesses — ein Griff,
    damit die beiden Env-Latten nicht an mehreren Stellen ausgepackt werden.
    Leeres Dict -> None weitergereicht: 'Achse aus', kein Ausschluss."""
    from core.benennung import pool_zulauf
    return pool_zulauf(k, NORM_LATTE_ZULAUF or None, GUETE_LATTE_ZULAUF or None)


def sammle(tage=5.0, fps_sample=2, mit_migriere=True, kalib_deckel=None):
    """Gelockter Wrapper ums Sammeln (serialisiert gegen andere Pool-Schreiber, Review 21.07.).
    mit_migriere=False fuer das szenario-getriggerte Sofort-Sammeln (nur neue Gesichter, OHNE die
    teure Pool-Neupruefung/Referenz-Neueinbettung — die macht der Reorganisieren-Button).
    kalib_deckel (.398, User-Fund 01.09. an einer leeren Kalibrier-Kachel:
    "eigentlich haette hier ein Szenario auswerten stattfinden muessen"):
    Ring-Deckel je Kamera (live_kalib_max). Ist er gesetzt (> 0), legt das
    Sammeln je Event sein BESTES Bild zusaetzlich in den Kalibrier-Ring der
    Kamera — dieselbe Nebenprodukt-Oekonomie wie die Ernte, kein eigener
    Rechenlauf. None/0 = aus (CLI-Altverhalten ohne den Wert)."""
    with pool_lock():
        return _sammle_intern(tage, fps_sample, mit_migriere, kalib_deckel)


def _sammle_intern(tage, fps_sample, mit_migriere, kalib_deckel=None):
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
    # .380: DER eine 112er-Warp des Hauses, nicht ein zweiter hier (core/ernte).
    # Lazy wie ueberall — der Modul-Kopf soll ohne insightface tragen.
    from core.ernte import align112 as _align112
    neu = 0
    mess_ges, mess_n = 0.0, 0                             # Bilanz des Zulauf-Siebs
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
                                 "ctx": ctx_crop(frame, x1, y1, x2, y2),
                                 # .380: die beiden Ausschnitte, an denen der
                                 # Zulauf gleich MISST — enger Crop und der
                                 # aligned 112er DIESER Detektion. Sie muessen
                                 # hier entstehen (das Frame lebt nur in dieser
                                 # Schleife) und werden vor dem Schreiben wieder
                                 # entfernt; gemessen wird erst unten, fuer die
                                 # wenigen Kandidaten, die in den Pool wollen.
                                 "_crop": crop.copy(),
                                 "_al": (_align112(frame, fc.kps)
                                         if getattr(fc, "kps", None) is not None else None)})
                    kand.sort(key=lambda k: -k["guete"])
                    del kand[8:]                          # Speicher-Deckel
            # .380 ZULAUF-SIEB (Beschluss 31.08.): erst sieben, dann gruppieren —
            # dieselbe Reihenfolge wie im Lernlauf, und mit derselben Quelle
            # (core.benennung.pool_zulauf). Bis .379 entschied ueber den Pool
            # allein kante/det/Fehldetektions-Signatur; die Qualitaets-Linien
            # kannte erst die Anzeige. Ein Tester bekam so auf seinem
            # Betriebsgelaende Unbekannt-Gruppen aus Laub angeboten.
            # Gemessen wird JE KANDIDAT, nicht je Detektion, und erst hier: nur
            # wer den Dublettentest ueberlebt hat, wuerde ueberhaupt eintreten.
            # Ein Durchgefallener belegt KEINEN der drei Plaetze — der naechste
            # aus der guete-Reihe rueckt nach (max. 8, der Speicher-Deckel oben).
            # Genau das holt die echten Gesichter zurueck, die frueher hinter
            # einem Laub-Ausschnitt auf Platz 1 unsichtbar blieben.
            gewaehlt, verworfen, mess_s = [], {}, 0.0
            sm = _strukturmass_geteilt()
            for k in kand:                               # guete-Reihenfolge, Duplikate raus
                v = np.asarray(k["emb"], np.float32)
                if any(float(v @ np.asarray(g["emb"], np.float32)) > 0.90 for g in gewaehlt):
                    continue
                mess_s += _zulauf_messen(k, sm)
                grund = _zulauf_urteil(k)
                if grund:
                    verworfen[grund] = verworfen.get(grund, 0) + 1
                    continue
                gewaehlt.append(k)
                if len(gewaehlt) >= 3:
                    break
            if verworfen:
                # Nie still: was der Pool abweist, steht mit Grund im Log
                # (dieselbe Zusage wie die Ernte-Zaehler ohne_struktur/fd).
                print(f"  sieved {eid} ({camera}): "
                      + ", ".join(f"{n}x {g}" for g, n in sorted(verworfen.items())),
                      flush=True)
            mess_ges += mess_s
            mess_n += sum(verworfen.values()) + len(gewaehlt)
            if gewaehlt and kalib_deckel:
                # .398 Ring-Zulauf: das beste Bild des Events speist den
                # Kalibrier-Ring der Kamera — der Kachel-Satz "Bilder kommen
                # ... aus den Ereignis-Analysen" stimmt damit auch fuer den
                # Szenario-Weg (K3-Loch: der Zentral-Umbau 31.08. erreichte
                # nur Ernte-Jobs). mensch_ok=True als deklarierte Grenze wie
                # beim Ernte-Zulauf: hier siebt das Zulauf-Urteil
                # (Fehldetektions-Signatur + pool_zulauf), ein
                # Pose-Skelett-Urteil gibt es auf diesem Weg nicht.
                try:
                    from core import livewache as _lw_ring
                    _b0 = gewaehlt[0]
                    _lw_ring.kalib_schreiben(
                        {"data_dir": DATA}, _b0.get("camera") or "",
                        _b0["ctx"], {"det": _b0.get("det"),
                                     "e": _b0.get("empf"),
                                     "t": _b0.get("fiqa_t")},
                        deckel=int(kalib_deckel),
                        log=lambda z: print("  " + z, flush=True))
                except Exception as _e_ring:              # noqa: BLE001
                    print(f"  calibration ring feed failed "
                          f"({type(_e_ring).__name__}: {_e_ring})", flush=True)
            for lauf, best in enumerate(gewaehlt):
                gid = eid.replace("/", "_") + ("" if lauf == 0 else f"~{lauf + 1}")
                cv2.imwrite(os.path.join(CROPS, gid + ".jpg"), best.pop("ctx"))
                best.pop("_crop", None)                   # Arbeits-Ausschnitte gehoeren
                best.pop("_al", None)                     # nicht in die Pool-Zeile
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
    if mess_n:
        # Der Preis des Siebs, beziffert statt behauptet (Haus-Regel: Posten
        # ehrlich nennen). ms JE POOL-KANDIDAT, nicht je Detektion.
        print(f"inflow measurement: {mess_n} candidate(s), "
              f"{mess_ges * 1000 / mess_n:.1f} ms each ({mess_ges:.1f} s total)", flush=True)
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
    Rueckgabe: Statistik-Dict.

    BESTANDSSCHUTZ (.380, Beschluss 31.08. Punkt 3): das Zulauf-Sieb von
    _sammle_intern wirkt hier bewusst NICHT nach. Gesichter, die vor .380 in den
    Pool kamen, tragen keine struktur-/fiqa_t-/empf-Werte; sie nachtraeglich an
    einer Latte zu messen, die sie nie gesehen haben, waere ein rueckwirkender
    stiller Verlust — und ein Urteil ohne Messgrundlage ist im ganzen Haus
    verboten. Alt-Zeilen urteilen also weiter alt. Wer sie wirklich neu bewerten
    will, hat dafuer den Weg ueber die Oberflaeche (Objekt-Flag, Zusammenlegen,
    Loeschen von Hand)."""
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
def benenne(gesicht_ids, person, beste_n=5, emb=None):
    """Die besten Gesichter eines Clusters als Referenzen fuer <person> in den Master legen.
    Legt refs/<person>/ an (neue Person moeglich), schreibt refs_meta; mit emb wird
    der refcache EINGEPFLEGT (.313), ohne emb verworfen wie bisher.

    KEINE Katalog-Latte auf diesem Weg (User-Entscheid 01.09., Screenshot
    'Wer ist das?': "Wenn ich sage hinzufuegen, dann hinzufuegen"): jeder
    Aufrufer dieser Funktion ist eine HAND-Auswahl je Bild (Today-Karte,
    Cluster, Unbekannt-Benennung, Lern-Bruecke) — der bewusste Klick ist die
    Pruefung, Aussieben danach kann der Quality-Check. Die Latte gilt weiter
    auf den Automatik-Wegen (Lernlauf plan_bauen, Pool-Zulauf); Inventar in
    core.kamerakalib.AUSNAHMEN. Von .385 bis .396 siebte auch dieser Weg
    (kat_latten-Parameter) — bewusst zurueckgebaut."""
    import re, shutil
    from core.registry import PERSON_RE
    if not re.fullmatch(PERSON_RE, person or ""):
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
    neue = []
    with open(meta, "a") as mf:
        for g in gewaehlt:
            quelle = os.path.join(CROPS, g["id"] + ".jpg")
            if not os.path.exists(quelle):
                continue
            ziel = f"anlern_{int(time.time())}_{g['id'][-24:]}.jpg"
            shutil.copyfile(quelle, os.path.join(zdir, ziel))
            # .401 Messwerte-Durchreichung (User-Linie 01.09.: "die
            # Kalibrierung laeuft immer"): Kamera + Guete-Masse der
            # Pool-Zeile wandern MIT in die Katalog-Zeile — ohne sie war
            # der Bestand fuer jede spaetere Latte/QS blind (Feldbefund:
            # 1505 Nach-Update-Referenzen ohne Messwerte). Fehlt ein Mass
            # (Alt-Pool), steht None — ehrlich ungemessen, Nachmessung
            # holt es nach.
            mf.write(json.dumps({"ts": round(time.time(), 1), "person": person, "datei": ziel,
                                 "herkunft": "anlernen", "eid": g["eid"], "aktiv": True,
                                 "camera": g.get("camera"),
                                 "fiqa_t": g.get("fiqa_t"), "empf": g.get("empf"),
                                 "kante": g.get("kante")},
                                ensure_ascii=False) + "\n")
            neue.append((os.path.join(zdir, ziel), ziel))
            n += 1
        mf.flush()
    if not refcache_ergaenzen_viele(person, neue, emb):
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


def _reconcile_intern(archiv_tage=ARCHIV_TAGE, sim=SIM_DEFAULT):
    """Ordnet die gesammelten Unbekannt-Gesichter persistenten Identitaeten zu — bestehende IDs
    bleiben stabil (Mehrheitsentscheid je Cluster ueber die schon zugeordneten Gesichter), neue
    Identitaeten kommen dazu, Einmal-Gaenger altern raus. Zusammenlege-Vorschlaege entstehen
    bei jedem Lauf frisch: aus Clustern, die zwei bestehende IDs ueberspannen, UND aus der
    Average-Linkage-Aehnlichkeit aller aktiven Identitaets-Paare (>= VORSCHLAG_AB) — NIE
    automatisch gemergt, verworfene Paare bleiben draussen. Rueckgabe: (identitaeten, vorschlaege)."""
    faces = {g["id"]: g for g in lade_gesichter()}
    idents = {u["id"]: u for u in lade_unbekannte()}
    # OBJEKT-EINFRIERUNG (Baustein C 12.08., Klasse stiller Verlust — Realfall U132:
    # der seit 20.07. als Objekt gemutete Cluster zog am 12.08. fuenf Besucher-Crops
    # an und versteckte sie im eingeklappten "not people"-Bereich): ein als Objekt
    # eingestufter Cluster nimmt KEINE neuen Members mehr an. Seine Members verlassen
    # das Clustering (der Cluster selbst bleibt unveraendert stehen, nur geloeschte
    # Gesichter fallen weiter raus); neue Funde, die zu ihm passen wuerden, bilden
    # frische U-Cluster und bleiben damit normal sichtbar (User-Grundsatz: nicht
    # loeschen, Mehrdeutigkeit aufloesen). Frueher faelschlich verschluckte Members
    # loest das CLI-Kommando objekt_reparatur heraus — bewusst kein Automatismus.
    eingefroren = {}
    for _uid in [k for k, u in idents.items() if u.get("objekt")]:
        u = idents.pop(_uid)
        u["members"] = [m for m in u.get("members", []) if m in faces]
        eingefroren[_uid] = u
    fest = {m for u in eingefroren.values() for m in u["members"]}
    frei = {fid: g for fid, g in faces.items() if fid not in fest}
    face2id = {}
    for u in idents.values():
        u["members"] = [m for m in u.get("members", []) if m in frei]   # geloeschte + eingefrorene Gesichter raus
        for m in u["members"]:
            face2id[m] = u["id"]
    _status("clustern", 0, len(frei))
    clusters = clustere(list(frei.values()), sim=sim) if frei else []
    _status("zuordnen", len(frei), len(frei))
    nums = [int(k[1:]) for k in list(idents) + list(eingefroren)
            if k[:1] == "U" and k[1:].isdigit()]
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
        if u["objekt"]:
            # Zeitanker der Einstufung (Baustein C): objekt_reparatur loest spaeter
            # genau die Members heraus, die JUENGER als dieser Anker sind. Bestehender
            # Anker bleibt, neue Einstufung stempelt jetzt.
            u["objekt_seit"] = idents.get(u["id"], {}).get("objekt_seit") or time.time()
    for u in neu.values():                                    # Einmal-Gaenger altern raus …
        # … und Rueckkehrer wachen LAUT wieder auf (Widerleger MUSS-2/KANN-4, Realfall
        # U155: ein archivierter Einmal-Gaenger zog am 12.08. eine frische Besuchs-
        # Stuetze an und blieb archiviert -> in Kachel UND /unbekannte unsichtbar).
        # "archiviert" ist eine MASCHINEN-Entscheidung (Alterung), die die Maschine
        # bei neuer Evidenz zuruecknehmen darf — anders als "besucher" (User-Entscheid,
        # bleibt unangetastet). Bewusst KEINE Einfrierung wie bei Objekt-Clustern:
        # ein Wiederkehrer soll seine persistente U-Identitaet behalten, nicht als
        # frischer Cluster fragmentieren (Unbekannte-Reiter-Konzept).
        if u["status"] == "archiviert" and \
           (time.time() - u["last_seen"]) <= archiv_tage * 86400:
            u["status"] = "aktiv"
            print(f"  {u['id']}: archived cluster got a fresh member -> reactivated",
                  flush=True)
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
    alle = list(neu.values()) + list(eingefroren.values())   # Objekt-Cluster unveraendert zurueck
    _speichere_unbekannte(alle)
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
    return alle, vs


def reconcile_unbekannte(archiv_tage=ARCHIV_TAGE, sim=SIM_DEFAULT):
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
                u["objekt_seit"] = time.time()   # Zeitanker fuer objekt_reparatur (Baustein C)
                geaendert += 1
                print(f"  {u['id']}: all {len(bewertet)} assessable member crop(s) match the "
                      f"non-face signature -> flagged as object", flush=True)
        if geaendert:
            _speichere_unbekannte(idents)
    print(f"fd re-check: {geaendert} identities flagged as objects", flush=True)
    return geaendert


def objekt_reparatur(uid=None, seit=None):
    """Einmalige Reparatur (Baustein C 12.08., Realfall U132: 5 Besucher-Crops vom
    12.08. steckten in einem seit 20.07. gemuteten Objekt-Cluster): Members eines
    Objekt-Clusters, die JUENGER sind als seine Objekt-Einstufung, herausloesen und
    untereinander geclustert als frische U-Cluster sichtbar machen (User-Grundsatz:
    nicht loeschen, Mehrdeutigkeit aufloesen — alle Crops bleiben erhalten, sie
    werden nur wieder sichtbar; ob ein herausgeloester Cluster doch ein Objekt ist,
    entscheidet der naechste Reconcile mit der EINEN Objekt-Regel neu). Bewusst NUR
    als CLI-Kommando, nie automatisch beim Start.

    uid=None: alle Objekt-Cluster. seit (epoch): Zeitanker der Einstufung; ohne
    Angabe zaehlt das gespeicherte objekt_seit des Clusters — fehlt beides, wird der
    Cluster LAUT uebersprungen (nie raten, wann die Einstufung war; Altbestand vor
    dieser Runde traegt noch kein objekt_seit). Nach dem Lauf traegt der Cluster den
    benutzten Anker als objekt_seit; zusammen mit der Einfrierung im Reconcile ist
    das idempotent (es kommen keine juengeren Members mehr nach).
    Rueckgabe: Liste der neu angelegten Identitaeten."""
    with pool_lock():
        faces = {g["id"]: g for g in lade_gesichter()}
        U = lade_unbekannte()
        ziele = [u for u in U if u.get("objekt") and (uid is None or u["id"] == uid)]
        if not ziele:
            print(f"objekt_reparatur: object cluster {uid!r} not found" if uid
                  else "objekt_reparatur: no object clusters in the pool", flush=True)
            return []
        nums = [int(u["id"][1:]) for u in U
                if u["id"][:1] == "U" and u["id"][1:].isdigit()]
        naechste = (max(nums) + 1) if nums else 1
        angelegt, geaendert = [], False
        for u in ziele:
            anker = seit if seit is not None else u.get("objekt_seit")
            if anker is None:
                print(f"  {u['id']}: no objekt_seit stored and no --seit given — "
                      f"skipped (pass --seit; guessing the classification time "
                      f"is not allowed)", flush=True)
                continue
            wann = time.strftime("%Y-%m-%d %H:%M", time.localtime(anker))
            jung = [m for m in u.get("members", [])
                    if m in faces and (faces[m].get("ts") or 0) > anker]
            if not jung:
                if u.get("objekt_seit") != anker:
                    u["objekt_seit"] = anker            # Anker festschreiben (Altbestand)
                    geaendert = True
                print(f"  {u['id']}: no members younger than {wann} — nothing to extract",
                      flush=True)
                continue
            weg = set(jung)
            rest = [m for m in u.get("members", []) if m not in weg]
            for c in clustere([faces[m] for m in jung], sim=SIM_DEFAULT):
                mids = [g["id"] for g in c]
                tss = [faces[m]["ts"] for m in mids]
                nid = f"U{naechste}"; naechste += 1
                neu = {"id": nid, "created": min(tss), "first_seen": min(tss),
                       "last_seen": max(tss), "status": "aktiv", "label": None,
                       "members": mids, "objekt": False}
                U.append(neu)
                angelegt.append(neu)
                print(f"  {u['id']} -> {nid}: {len(mids)} member(s) extracted "
                      f"({', '.join(mids[:4])}{'…' if len(mids) > 4 else ''})", flush=True)
            u["members"] = rest
            u["objekt_seit"] = anker
            geaendert = True
            resttss = [faces[m]["ts"] for m in rest if m in faces]
            if resttss:
                u["first_seen"], u["last_seen"] = min(resttss), max(resttss)
            print(f"  {u['id']}: {len(jung)} member(s) younger than {wann} released, "
                  f"{len(rest)} kept as object", flush=True)
        if geaendert:
            _speichere_unbekannte(U)
        print(f"objekt_reparatur: {len(angelegt)} new identities out of "
              f"{len(ziele)} object cluster(s)", flush=True)
        return angelegt


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


def unbekannt_objekt(uid, an=True):
    """Gelockter Wrapper (Handknopf 'no person', .380)."""
    with pool_lock():
        return _unbekannt_objekt_intern(uid, an)


def _unbekannt_objekt_intern(uid, an=True):
    """Identitaet von Hand als statisches Objekt markieren bzw. zurueck auf Person.

    Bisher setzte NUR der Reconcile das objekt-Flag (Objekt-Regel 25.07.); was er
    uebersah — der Radkasten, der Lichtfleck, das Laub — blieb dauerhaft im
    Personen-Eimer und musste bei jedem Durchgang wieder weggeschaut werden. Der
    Handknopf schreibt DASSELBE Flag, das der Reconcile schreibt (kein zweiter
    Begriff): der Cluster friert damit ein (nimmt keine neuen Members mehr an) und
    wird ueber den Filter ausgeblendet. Umkehrbar (an=False) — nichts wird
    geloescht, die Stuetzen bleiben im Pool (User-Grundsatz: nicht loeschen,
    Mehrdeutigkeit aufloesen)."""
    U = lade_unbekannte()
    ok = False
    for u in U:
        if u.get("id") == uid:
            if an:
                u["objekt"] = True
            else:
                u.pop("objekt", None)
            ok = True
    if ok:
        _speichere_unbekannte(U)
    return ok


def unbekannt_merge(uid_a, uid_b):
    """Gelockter Wrapper (Review 21.07.)."""
    with pool_lock():
        return _unbekannt_merge_intern(uid_a, uid_b)


def unbekannt_merge_viele(uids):
    """n:1-Zusammenlegen (.380): alle angetickten Identitaeten in EINEM gelockten
    Zug auf die kleinste ID ziehen. Ersetzt das Reihum-Klicken der frueheren
    Merge-Dropdowns (je Kachel eine Auswahlliste ALLER anderen Gruppen — bei 95
    Gruppen 9056 <option>-Elemente in einer Seite).

    Reihenfolge ist bewusst 'kleinste ID zuerst': _unbekannt_merge_intern behaelt
    immer die kleinere Nummer, damit wandern alle Paare auf dasselbe Ziel. Jeder
    Schritt liest den Pool frisch, ein Fehlschlag (ID inzwischen weg) kostet nur
    diesen einen Partner. Rueckgabe (ziel, n_gemergt) bzw. (None, 0)."""
    ids = [str(u) for u in (uids or []) if str(u)]
    ids = list(dict.fromkeys(ids))
    if len(ids) < 2:
        return None, 0
    ids.sort(key=lambda k: int(k[1:]) if k[1:].isdigit() else 0)
    ziel, n = ids[0], 0
    with pool_lock():
        for weiterer in ids[1:]:
            if _unbekannt_merge_intern(ziel, weiterer):
                n += 1
    return (ziel, n) if n else (None, 0)


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


def _pool_abzug_intern(mids):
    """Der EINE Pool-Abzug nach dem Anlernen (Issue #19): angelernte Gesichter aus
    gesichter.jsonl nehmen (atomar), ihre Crops loeschen und ihre Mitgliedschaften aus
    ALLEN Unbekannt-Identitaeten austragen; dabei leergezogene Identitaeten entfallen.
    Ersetzt das alte `del U[uid]` aus _unbekannt_benennen_intern; am ECHTEN Pool
    identisch, in vier konstruierten Kanten bewusst ANDERS und besser (Widerleger
    11.08.): geteilte mid verlaesst BEIDE Identitaeten (vorher Karteileiche), eine nur
    noch aus toten members bestehende Identitaet entfaellt, members-loses Dict bekommt
    [], doppelte uid-Zeilen ueberleben (vorher dedupte das dict still eine weg).
    Wiederverwendet von _unbekannt_benennen_intern UND benenne_mit_abzug — vorher zog
    nur der Unbekannt-Reiter ab; die Today-Karte ("Add selected faces") liess die
    Gesichter im Pool zurueck, die Unknown-Karte blieb stehen. NUR unter pool_lock rufen."""
    weg = set(mids)
    G = [g for g in lade_gesichter() if g["id"] not in weg]
    _schreibe_jsonl_atomar(GES_PATH, G)                     # atomar + gelockt (Review 21.07.)
    for mid in weg:
        try:
            os.remove(os.path.join(CROPS, mid + ".jpg"))
        except FileNotFoundError:
            pass
    U = lade_unbekannte()
    behalten = []
    for u in U:
        alte = u.get("members", [])
        u["members"] = [m for m in alte if m not in weg]
        if u["members"] or not alte:                        # nur LEERGEZOGENE entfallen
            behalten.append(u)
    _speichere_unbekannte(behalten)


def _pool_sicherung(mids):
    """eid+Embedding+Modell der Pool-Eintraege VOR dem Abzug sichern — Futter fuer die
    Event-Nachpruefung (nachpruefe_events), die nach dem Abzug nicht mehr an die
    Embeddings kaeme. NUR unter pool_lock rufen (konsistenter Stand)."""
    G = {g["id"]: g for g in lade_gesichter()}
    return [{"eid": G[m]["eid"], "emb": G[m]["emb"], "modell": G[m].get("modell")}
            for m in mids if m in G]


def benenne_mit_abzug(gesicht_ids, person, beste_n=None, emb=None):
    """Anlern-Weg der Today-Karte und des Cluster-Anlernens (/anlernen_benennen,
    Issue #19): benenne() + Pool-Abzug in EINEM gelockten Zug, damit angelernte
    Gesichter nicht wieder als unbekannt clustern und die Unknown-Karte verschwindet.
    beste_n = ALLE uebergebenen (Widerleger 11.08.): der User hat jedes Gesicht
    EINZELN angekreuzt ("Tick the faces that really belong") — mit dem alten
    beste_n=5 wurden bei 8 Haekchen 3 Gesichter abgezogen UND vernichtet, ohne je
    Referenz zu werden. WICHTIG zur Grenze dieses Wegs: der Schutz vor einem
    fehl-angekreuzten FREMDEN ist das bewusste Anklicken selbst — die Referenz-QS
    danach meldet nur Verwechslungen mit BESTEHENDEN Personen, einen niemandem
    aehnlichen Fremden sieht sie konstruktiv nicht (Widerleger-Recheck 11.08.).
    Abgezogen werden NUR ids, deren Crop real existiert (struktureller Guard statt
    Meldungstext: bei Teilausfall — Crop-Dateien fehlen — bleiben genau diese im
    Pool statt ersatzlos vernichtet zu werden; ohne einen einzigen Crop passiert
    GAR nichts, auch kein leerer Personen-Ordner).
    Rueckgabe (ok, msg, betroffen); betroffen fuer verifyd.anlern_nachpruefung_starten."""
    with pool_lock():
        mit_crop = [i for i in gesicht_ids
                    if os.path.isfile(os.path.join(CROPS, str(i) + ".jpg"))]
        if not mit_crop:
            return False, "keine Crop-Dateien zu den gewaehlten Gesichtern — nichts angelernt", []
        # Katalog-Latte hier ZURUECKGEBAUT (User-Entscheid 01.09.): der
        # Nutzer hat jedes Bild einzeln angekreuzt — Hand schlaegt Latte,
        # Begruendung im benenne()-Docstring.
        betroffen = _pool_sicherung(mit_crop)
        ok, msg = benenne(mit_crop, person, emb=emb,
                          beste_n=beste_n if beste_n else max(1, len(mit_crop)))
        if not ok:
            return False, msg, []
        _pool_abzug_intern(mit_crop)
        if len(mit_crop) < len(gesicht_ids):
            msg += (f" — {len(gesicht_ids) - len(mit_crop)} von "
                    f"{len(gesicht_ids)} ohne Crop-Datei, bleiben im Pool")
    return True, msg, betroffen


def _person_refs(emb, person):
    """Referenz-Embeddings EINER Person (det 320) — die gezielte Variante von
    lade_master_refs. Die Nachpruefung (Issue #19) brauchte anfangs die ganze
    Bibliothek und kostete damit 650+ s auf CPU (Widerleger 11.08.); fuer das
    "traegt die NEUE Referenz das Event?"-Urteil zaehlt nur die eine Person."""
    from core import refbeiwert as _rb
    V = []
    pd = os.path.join(MASTER, person)
    if os.path.isdir(pd):
        bw, _fremd = _rb.beiwerte(MASTER, emb.modell)   # A2-Vertrag Stelle 3
        for f in sorted(os.listdir(pd)):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            b = bw.get((person, f))
            if b is not None:
                V.append(np.asarray(b["emb"], dtype=np.float32))
                continue
            img = cv2.imread(os.path.join(pd, f))
            if img is None:
                continue
            v = emb.embed(img)
            if v is not None:
                V.append(v.astype(np.float32))
    return np.asarray(V, dtype=np.float32) if V else None


def nachpruefe_events(person, faces):
    """Issue #19 Teil 2: nach dem Anlernen die EVENTS der abgezogenen Gesichter gegen die
    NEUEN Referenzen der Person pruefen — bewusst KEINE Video-Neuanalyse (auf 2C/4T-
    Hardware genau falsch, Clip oft schon weg; ein Fehlschlag wuerde per last-wins eine
    gute Zeile degradieren), sondern Embedding-Vergleich der gesicherten Pool-Embeddings.
    Je Event zaehlt sein BESTES Gesicht. Gate ist die zentrale UNBEKANNT_MAX — exakt die
    "jetzt bekannt"-Semantik von migriere_und_pruefe_pool (b), kein neues Streu-Literal.
    Pool-Embeddings eines ANDEREN Recognition-Modells werden uebersprungen (Vergleich
    waere bedeutungslos; fail-safe Richtung "Karte bleibt stehen").
    faces = [{eid, emb, modell}, ...]; Rueckgabe {eid: {"sim": float, "bestaetigt": bool}}."""
    emb = Embedder()
    R = _person_refs(emb, person)
    modell = aktuelles_modell()
    out = {}
    for f in faces:
        eid, v = f.get("eid"), f.get("emb")
        if not eid or v is None:
            continue
        if f.get("modell") is not None and f["modell"] != modell:
            print(f"  {eid}: pool embedding from model '{f['modell']}' != active "
                  f"'{modell}' — skipped (card stays)", flush=True)
            continue
        s = float((R @ np.asarray(v, np.float32)).max()) if R is not None and len(R) else -1.0
        alt = out.get(eid)
        if alt is None or s > alt["sim"]:
            out[eid] = {"sim": round(s, 3), "bestaetigt": bool(s >= UNBEKANNT_MAX)}
    return out


def unbekannt_benennen(uid, person, beste_n=6, emb=None, ids=None):
    """Gelockter Wrapper (Review 21.07.: serialisiert gegen das kontinuierliche Sammeln, das
    dieselbe gesichter.jsonl schreibt)."""
    with pool_lock():
        return _unbekannt_benennen_intern(uid, person, beste_n, emb=emb,
                                          ids=ids)


def _unbekannt_benennen_intern(uid, person, beste_n=6, emb=None, ids=None):
    """Eine Unbekannt-Identitaet zu einer bekannten Person machen: beste Gesichter als Referenzen
    anlegen, die Gesichter aus dem Unbekannt-Pool entfernen (Crops + gesichter.jsonl), Identitaet
    entfernen. Ab dem naechsten Event wird die Person erkannt und taucht nicht mehr als unbekannt
    auf. Rueckgabe (ok, msg, betroffen) — betroffen wie benenne_mit_abzug fuer die
    Event-Nachpruefung (Issue #19: auch dieser Weg liess die Event-Akten alt).

    ids = TEILMENGE der Mitglieder (.380, Klasse stiller Verlust): ein Unbekannt-Cluster
    ist nicht immer eine Person. Der Weg ohne ids zieht die GANZE Gruppe aus dem Pool und
    loescht ihre Crops — wer sie fuer die eine erkannte Person zuwies, vernichtete damit
    still die Stuetzen der ZWEITEN Person, die im selben Cluster lag; sie tauchte danach
    weder unter Unknown noch sonstwo wieder auf. Mit ids gilt strikt: nur die angetickten
    Stuetzen werden Referenz UND abgezogen, jede nicht gewaehlte bleibt im Pool und damit
    in ihrer (jetzt kleineren) Identitaet stehen — der naechste Reconcile clustert den Rest
    neu. beste_n gilt dann nicht: der Nutzer hat jedes Bild einzeln angehakt (dieselbe
    Lehre wie benenne_mit_abzug, Widerleger 11.08.), eine zweite Auswahl darueber wuerde
    Angehaktes wieder wegwerfen. Crop-Guard wie dort: abgezogen wird nur, was real als
    Crop-Datei existiert."""
    U = {u["id"]: u for u in lade_unbekannte()}
    if uid not in U:
        return False, "Identitaet nicht gefunden", []
    mids = U[uid].get("members", [])
    if ids is None:
        # GANZE Gruppe: der Abzug umfasst wie bisher ALLE Mitglieder (auch die,
        # die beste_n nicht erreichen) — daran aendert die Katalog-Latte
        # nichts, sie entscheidet nur, welche davon Referenz werden. benenne()
        # siebt und sagt es in seiner Meldung.
        betroffen = _pool_sicherung(mids)
        ok, msg = benenne(mids, person, beste_n=beste_n, emb=emb)
        if not ok:
            return False, msg, []
        _pool_abzug_intern(mids)                            # Pool + Crops + Identitaet(en)
        return True, msg, betroffen
    gewuenscht = {str(i) for i in ids}
    gewaehlt = [m for m in mids if m in gewuenscht]
    mit_crop = [m for m in gewaehlt
                if os.path.isfile(os.path.join(CROPS, str(m) + ".jpg"))]
    if not mit_crop:
        return False, "keine Crop-Dateien zu den gewaehlten Gesichtern — nichts angelernt", []
    # TEILAUSWAHL: hier hat der Nutzer jedes Bild einzeln angetickt. Was die
    # Katalog-Latte ablehnt, wird deshalb NICHT abgezogen (und damit nicht
    # geloescht) — es bleibt in seiner Gruppe stehen. Der Preis ist, dass es
    # beim naechsten Mal wieder auftaucht; die Alternative waere, ein Bild zu
    # vernichten, das nie Referenz wurde (Widerleger-Fehlerklasse 11.08.).
    # Katalog-Latte ZURUECKGEBAUT (User-Entscheid 01.09.): jedes Bild ist
    # einzeln angetickt — Hand schlaegt Latte (Begruendung: benenne()).
    betroffen = _pool_sicherung(mit_crop)
    ok, msg = benenne(mit_crop, person, beste_n=max(1, len(mit_crop)), emb=emb)
    if not ok:
        return False, msg, []
    _pool_abzug_intern(mit_crop)                            # NUR die gewaehlten
    bleibt = len(mids) - len(mit_crop)
    if bleibt > 0:
        msg += f" — {bleibt} weitere Stuetze(n) bleiben im Pool"
    return True, msg, betroffen


# ---------------------------------------------------------------- Referenz-QS (Verwechslungs-Check)
QS_PATH = os.path.join(ANLERN, "refs_qs.json")


_NORMMASS = None


def _normmass_geteilt():
    """Die eine NormMass des Prozesses (User 20.08.: die virtuelle Qualitaets-
    linie gehoert auch in die Bestands-QS) — lazy, Neubau nur bei Modellwechsel;
    ok=False (fremdes Modell) liefert None und die Messung laeuft ohne Norm
    weiter, deklariert je Zeile (norm=None)."""
    global _NORMMASS
    from face_audit import NormMass, aktuelles_modell
    m = aktuelles_modell()
    if _NORMMASS is None or _NORMMASS.modell != m:
        _NORMMASS = NormMass(modell=m)
    return _NORMMASS if _NORMMASS.ok else None


def bild_metriken(emb, img, mit_pose=False, mit_norm=False):
    """QS-Metriken eines Einzelbilds (det 320): (embedding|None, gesichts_kante_orig|None,
    sharp[, pose|None][, norm|None]). kante = Gesichtsgroesse in ORIGINAL-Pixeln (Upscaling wie
    Embedder.embed herausgerechnet). Eine Quelle fuer Eignungspruefung UND Bestands-
    Suche — was die Suche vorschlaegt, besteht damit garantiert auch die Pruefung.
    mit_pose (.273c, Blick-Statistik): liefert zusaetzlich fc.pose (Widerleger-
    Befund: die Pose wurde bisher weggeworfen) — als 4. Wert, damit die drei
    Bestands-Aufrufer unveraendert bleiben. mit_norm (User 20.08.: virtuelle
    Qualitaetslinie auch in der Bestands-QS): Feature-Norm DERSELBEN Detektion
    als weiterer Wert, None wenn NormMass nicht traegt (fremdes Modell)."""
    h, w = img.shape[:2]
    sh = float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    scale = max(1.0, 224.0 / min(h, w))
    gross = cv2.resize(img, (round(w * scale), round(h * scale)),
                       interpolation=cv2.INTER_CUBIC) if scale > 1.0 else img
    faces = emb.app.get(gross)
    if not faces:
        leer = [None, None, round(sh, 0)]
        if mit_pose:
            leer.append(None)
        if mit_norm:
            leer.append(None)
        return tuple(leer)
    fc = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
    x1, y1, x2, y2 = fc.bbox
    kante = round(min(x2 - x1, y2 - y1) / scale)
    v = np.asarray(fc.normed_embedding, dtype=np.float32)
    aus = [v, kante, round(sh, 0)]
    if mit_pose:
        pose = getattr(fc, "pose", None)
        aus.append([round(float(x), 1) for x in pose] if pose is not None else None)
    if mit_norm:
        # KEINE zweite Detektion: dieselbe fc, dasselbe Alignment wie der
        # Urteilspfad; nm=None (fremdes Modell) -> None, deklariert.
        norm = None
        nm = _normmass_geteilt()
        if nm is not None:
            try:
                from insightface.utils import face_align
                c112 = face_align.norm_crop(gross, landmark=fc.kps, image_size=112)
                norm = round(float(nm.feature_norm([c112])[0]), 2)
            except Exception:
                pass                          # Zusatz-Auskunft, nie Blocker
        aus.append(norm)
    return tuple(aus)


def lade_master_bilder(emb, fortschritt=None):
    """Alle Referenzbilder EINZELN mit Eignungs-Metriken (det 320, Ref-Crops). Liefert AUCH
    Bilder ohne detektierbares Gesicht (emb None) und defekte Dateien — genau die gehoeren
    in die Eignungspruefung, nicht stillschweigend uebersprungen.
    fortschritt (.273 Bestands-QS): Callback (i, n) je gemessenem Bild —
    die Dateiliste steht vorab, damit n von Anfang an stimmt."""
    if not os.path.isdir(MASTER):
        return []
    dateien = []
    for p in sorted(os.listdir(MASTER)):
        pd = os.path.join(MASTER, p)
        if not os.path.isdir(pd):
            continue
        dateien += [(p, f) for f in sorted(os.listdir(pd))
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    from core import refbeiwert as _rb
    bw, _fremd = _rb.beiwerte(MASTER, emb.modell)   # A2-Vertrag Stelle 5
    if _fremd:
        print(f"lade_master_bilder: {_fremd} stock reference(s) with foreign-model "
              f"embedding — measured from file instead (will show as unusable)",
              flush=True)
    out = []
    for i, (p, f) in enumerate(dateien, 1):
        b = bw.get((p, f))
        if b is not None:
            # Beiwert-Referenz: VOLLWERTIGE Messzeile aus den Lauf-Messwerten
            # (Konzept-QS W2.6 — vorher waere sie mit emb=None aus Verwechs-
            # lungs-Matrix UND refcache-Schrieb gefallen und als 'kein_gesicht'
            # zum Loesch-Kandidaten geworden). Die Datei wird NIE gemessen.
            # .313b: Beiwerte schreibt neben dem Vorrats-Weg auch die Lernlauf-
            # Uebernahme (Ernte-Messung). NUR die Vorrats-Herkunft bekommt das
            # vorrat-Flag (eigene Achsen, nie Loesch-Kandidat); eine Lernlauf-
            # Referenz laeuft mit ihren Ernte-Werten (kante/sharp/norm, gleiche
            # Skalen) an der regulaeren Latte wie eine gemessene Datei.
            img = cv2.imread(os.path.join(MASTER, p, f))
            out.append({"person": p, "datei": f,
                        "emb": np.asarray(b["emb"], np.float32),
                        "sharp": float(b.get("sharp") or 0.0),
                        "kante": b.get("kante"), "pose": b.get("pose"),
                        "wh": (f"{img.shape[1]}x{img.shape[0]}"
                               if img is not None else "?"),
                        "defekt": False,
                        "vorrat": str(b.get("herkunft") or "vorrat") == "vorrat",
                        "norm": b.get("norm")})
        else:
            img = cv2.imread(os.path.join(MASTER, p, f))
            if img is None:
                out.append({"person": p, "datei": f, "emb": None, "sharp": 0.0,
                            "kante": None, "wh": "?", "defekt": True})
            else:
                # Virtuelle Qualitaetslinie AUCH fuer den Alt-Bestand (User
                # 20.08.): jede messbare Referenz bekommt ihre Feature-Norm —
                # dieselbe Skala wie Vorrat/Katalog-Linie, aus DERSELBEN
                # Detektion (mit_norm, keine Doppelmessung).
                v, kante, sh, pose, norm = bild_metriken(emb, img, mit_pose=True,
                                                         mit_norm=True)
                out.append({"person": p, "datei": f, "emb": v, "sharp": sh,
                            "kante": kante, "pose": pose, "norm": norm,
                            "wh": f"{img.shape[1]}x{img.shape[0]}",
                            "defekt": False})
        if fortschritt:
            fortschritt(i, len(dateien))
    return out


def pruefe_referenzen(flag_sim=0.30, top=40,
                      unscharf_max=REF_LATTE["unscharf_max"],
                      min_kante=REF_LATTE["min_kante"],
                      kante_gut=REF_LATTE["kante_gut"],
                      sharp_gut=REF_LATTE["sharp_gut"],
                      dup_sim=0.75, person=None, emb=None, fortschritt=None,
                      norm_latte=None):
    """Referenz-QS (.273 zum Bestands-QS-Knopf ausgebaut, Konzept
    konzept_bestandsqs.md) in VIER Teilen: (1) EIGNUNG jedes einzelnen
    Bildes — defekt / kein Gesicht / zu klein / unscharf (Loesch-Kandidaten,
    nach Grund gruppiert) + Qualitaets-STUFE gut/mindest/unter aus der
    REF_LATTE (eine Quelle mit Bruecke/Sichtung); (2) Cross-Person-
    VERWECHSLUNG ('kritisch' bei hoher Fremd-Aehnlichkeit oder fremd >=
    eigen-Kohaerenz = Fehllabel-Verdacht); (3) DOPPELTE innerhalb jeder
    Person (>= dup_sim, greedy entlang Latten-Klasse+Schaerfe: der beste
    bleibt Vertreter, der Rest ist redundant — VORSCHLAG, kein Auto-
    Loeschen); (4) ZUSAMMENFASSUNG je Person fuer die Kopf-Tabelle.
    person: filtert NUR den Bericht — gemessen und verglichen wird IMMER
    der Gesamtbestand (die Verwechslungs-Achse braucht alle als Gegenseite).
    emb: warmer Dienst-Embedder (det 320) statt Neubau; fortschritt(i, n)
    fuer die Anzeige. Ergebnis -> refs_qs.json fuer die Qualitaets-Seite."""
    emb = emb or Embedder()                       # det 320 default — genau richtig fuer Ref-Crops
    B = lade_master_bilder(emb, fortschritt=fortschritt)
    # .273 Qualitaets-Stufe je Bild (REF_LATTE = eine Quelle mit Bruecke/
    # Sichtung): unmessbar / unter / mindest / gut.
    # .308 (User-Go 21.08. — 'auch der QS-Knopf aufs neue Regelwerk'):
    # NORM-WEG in der Einstufung — dieselbe Alternativ-Regel wie bild_stufe
    # (.307): Norm >= gut-Linie = GUT, Norm >= Sammel-Schwelle = mindest,
    # jeweils mit den Vorrats-Boeden fuer Kante/Schaerfe. Ohne norm_latte
    # (Vorrat aus) urteilt die Stufe BYTE-GLEICH wie .306. Messbasis der
    # Entscheidung (Prod 20.08., 296 Referenzen): 50 Bilder mit Norm >= 24
    # trugen nur 'mindest'/'unter', und 30 von 39 Loeschkandidaten der
    # Pixel-Latte hatten Norm >= 22 (bis 25,1) — die Latte haette
    # identitaetsstarke Fern-Referenzen zum Loeschen vorgeschlagen.
    _nl = norm_latte or {}

    def _norm_stufe(b):
        """'gut'|'mindest'|None ueber den Norm-Weg (None = nicht qualifiziert)."""
        n = b.get("norm")
        if n is None or _nl.get("min") is None:
            return None
        if (b.get("kante") or 0) < (_nl.get("kante") or 0) or b["sharp"] < (_nl.get("sharp") or 0):
            return None
        if _nl.get("gut") is not None and n >= _nl["gut"]:
            return "gut"
        if n >= _nl["min"]:
            return "mindest"
        return None

    for b in B:
        if b.get("vorrat"):
            # Vorrats-Referenz (A2): an ihren EIGENEN Achsen qualifiziert
            # (Norm-Linie + Konsens + Schaerfe 600) — die Pixel-Latte gilt
            # fuer sie nicht. Klasse 'gut' statt neuem Enum-Wert (kein
            # unbekannter stufe-Wert fuer bestehende Leser), das
            # vorrat-Flag traegt die Transparenz.
            b["stufe"] = "gut"
        elif b.get("defekt") or b["emb"] is None:
            b["stufe"] = "unmessbar"
        elif ((b["kante"] or 0) >= kante_gut and b["sharp"] >= sharp_gut) \
                or _norm_stufe(b) == "gut":
            b["stufe"] = "gut"
        elif ((b["kante"] or 0) >= min_kante and b["sharp"] >= unscharf_max) \
                or _norm_stufe(b) == "mindest":
            b["stufe"] = "mindest"
        else:
            b["stufe"] = "unter"
        if _norm_stufe(b) and not ((b.get("kante") or 0) >= min_kante
                                   and (b.get("sharp") or 0) >= unscharf_max):
            b["norm_traegt"] = True        # Transparenz: Stufe kommt vom Norm-Weg
    PRIO = ("defekt", "kein_gesicht", "zu_klein", "unscharf")
    ungeeignet = []
    for b in B:
        if b.get("vorrat"):
            # W1.16: eine Vorrats-Referenz darf NIE als Loesch-Kandidat der
            # Pixel-Latte gefuehrt werden — ihre Achsen sind Norm/Konsens/
            # Schaerfe-600, und die Latten-Messung an der Datei waere ohnehin
            # die tote Nach-Detektion (28/40-Befund).
            continue
        if b.get("norm_traegt"):
            # .308: am Norm-Weg qualifiziert -> KEIN Loeschkandidat der
            # Pixel-Latte (zu_klein/unscharf), egal wie klein die Kante.
            continue
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
                               "stufe": b["stufe"],
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
    # .273 Achse 3: DOPPELTE innerhalb jeder Person — greedy entlang
    # Latten-Klasse + Schaerfe (bester bleibt Vertreter); Embeddings sind
    # L2-normiert (bild_metriken), dot == Cosinus. VORSCHLAG, nie Auto-Loeschen.
    from core.benennung import _lattenklasse as _lk273
    doppel = []
    _je_p = {}
    for b in BE:
        _je_p.setdefault(b["person"], []).append(b)
    for _p, _bs in sorted(_je_p.items()):
        vertreter = []
        for b in sorted(_bs, key=lambda x: (_lk273(x), -x["sharp"])):
            naher, nsim = None, -1.0
            for v in vertreter:
                s = float(np.dot(b["emb"], v["emb"]))
                if s >= float(dup_sim) and s > nsim:
                    naher, nsim = v, s
            if naher is None:
                vertreter.append(b)
                continue
            doppel.append({"person": _p, "datei": b["datei"],
                           "behalten": naher["datei"],
                           "sim": round(nsim, 3), "stufe": b["stufe"]})
    # .273 Achse 4: Zusammenfassung je Person (Kopf-Tabelle der Seite)
    from core.benennung import perspektiv_bin as _pb273
    personen = {}
    for b in B:
        e = personen.setdefault(b["person"], {"n": 0, "gut": 0, "mindest": 0,
                                              "unter": 0, "unmessbar": 0,
                                              "links": 0, "frontal": 0,
                                              "rechts": 0})
        e["n"] += 1
        e[b["stufe"]] += 1
        if b.get("emb") is not None:
            # .273c (User: 'wie viele Bilder von jeder Seite'): Blick-Zaehler
            # je Person — dieselbe Bin-Regel wie Lern-Sichtung (15 Grad).
            e[_pb273(b.get("pose") or [], 15.0)] += 1
    _red = collections.Counter(d["person"] for d in doppel)
    _krit = collections.Counter()
    for pr in paare:
        if pr.get("kritisch"):
            _krit[pr["a_person"]] += 1
            _krit[pr["b_person"]] += 1
    for _p, e in personen.items():
        e["redundant"] = _red.get(_p, 0)
        e["kritisch"] = _krit.get(_p, 0)
    # Widerleger-Blocker (Konzept-QS 18.08.): der Personen-Filter wird NIE
    # persistiert — ein Ein-Person-Lauf haette sonst den Bericht ALLER
    # anderen geloescht. refs_qs.json traegt IMMER den vollen Befund; der
    # Filter wirkt allein auf die RUECKGABE (und die Seite filtert beim
    # Rendern ueber ?person=...).
    os.makedirs(ANLERN, exist_ok=True)
    _schreibe_json_atomar(QS_PATH, {"ts": time.time(), "ref_count": len(B), "flag_sim": flag_sim,
                                    "unscharf_max": unscharf_max, "min_kante": min_kante,
                                    "kante_gut": kante_gut, "sharp_gut": sharp_gut,
                                    "dup_sim": dup_sim,
                                    "modell": emb.modell, "personen": personen,
                                    "doppel": doppel,
                                    "stufen": {p_: {b["datei"]: b["stufe"]
                                               for b in B if b["person"] == p_}
                                               for p_ in personen},
                                    # Virtuelle Qualitaetslinie (User 20.08.):
                                    # Feature-Norm je messbarer Referenz —
                                    # dieselbe Skala wie Vorrat/Katalog-Linie;
                                    # vorrat=True markiert Beiwert-Referenzen.
                                    "normen": {p_: {b["datei"]: b.get("norm")
                                               for b in B if b["person"] == p_
                                               and b.get("norm") is not None}
                                               for p_ in personen},
                                    "vorrat_refs": sorted(
                                        b["datei"] for b in B if b.get("vorrat")),
                                    "norm_latte": _nl or None,
                                    "norm_traegt": sorted(
                                        b["datei"] for b in B if b.get("norm_traegt")),
                                    "paare": paare, "ungeeignet": ungeeignet})
    if person:
        ungeeignet = [u for u in ungeeignet if u["person"] == person]
        doppel = [d for d in doppel if d["person"] == person]
        paare = [pr for pr in paare
                 if person in (pr["a_person"], pr["b_person"])]
        personen = {p_: e for p_, e in personen.items() if p_ == person}
    # refcache im analyze-Format gleich mitschreiben (identische det-320-Embeddings, meta =
    # sortierte Dateilisten wie sync_refs.master_stand): /aehnliche und analyze funktionieren
    # damit SOFORT nach Loeschungen/Anlernen, ohne auf das naechste Kamera-Event zu warten
    # (User-Befund 19.07.: "Referenz-Cache wird gerade neu aufgebaut" nach dem Aufraeumen)
    try:
        # Widerleger-Blocker (Konzept-QS 18.08.): waehrend der Messung kann
        # der User Referenzen GELOESCHT haben — der Cache darf sie nicht
        # wiederbeleben (Sichtungs-/Vorschlags-Geister). Existenz frisch
        # pruefen, unmittelbar vor dem Schreiben.
        def _lebt(b):
            return os.path.isfile(os.path.join(MASTER, b["person"], b["datei"]))
        want = {}
        refs = {}
        for b in B:
            if not _lebt(b):
                continue
            want.setdefault(b["person"], []).append(b["datei"])
            refs.setdefault(b["person"], [])
        for b in BE:
            if _lebt(b):
                refs[b["person"]].append(b["emb"])
        os.makedirs(CLIPS, exist_ok=True)
        # Atomar (tmp + fsync + os.replace) wie in analyze.py: analyze LIEST diesen Cache, waehrend
        # dieser Lauf ihn schreibt — direkt aufs Ziel geschrieben, konnte der Leser eine halbe npz
        # erwischen (BadZipFile -> Event "fehler"). Meta unter '§meta' statt dem Keyword meta=:
        # eine Person namens "meta" haette sonst mit np.savez kollidiert (TypeError bei JEDEM Lauf).
        ziel = os.path.join(CLIPS, "refcache.npz")
        # .411: eindeutige tmp ueber core.atomar (mkstemp im Zielordner) — vier
        # Schreiber dieser Datei teilten sich `refcache.npz.tmp-<pid>`
        # (Tester-Log 02.09.: FileNotFoundError beim replace, 2x).
        _atomar.schreiben(
            ziel,
            lambda f: np.savez(f, **{"§meta": json.dumps({**want, "§modell": emb.modell})},
                               **{p: (np.asarray(v, np.float32) if v else np.zeros((0, 512), np.float32))
                                  for p, v in refs.items()}),
            suffix=".npz", binaer=True)
    except Exception as e:
        print(f"refcache not written: {e}", flush=True)   # Cache ist Beschleunigung, kein Muss —
                                                                # aber nicht mehr STILL scheitern
    return {"paare": paare, "ungeeignet": ungeeignet,
            "doppel": doppel, "personen": personen}


def entferne_referenz(person, datei):
    """Ein einzelnes Referenzbild aus dem Master loeschen — Datei weg, TOMBSTONE in refs_meta
    (aktiv:false; NICHT die Zeile entfernen: ohne Tombstone wuerde sync_refs das in Frigate
    noch vorhandene Bild als 'neu' re-importieren), QS-Liste sofort bereinigen (die Seite
    zeigte sonst tote Bild-Links, bis der Hintergrund-Neulauf fertig ist), refcache verworfen.
    Nur innerhalb refs/ (Containment)."""
    import re
    from core.registry import DATEI_RE, PERSON_RE   # Vertrag (Issue #12 + Sweep 03.08.)
    if not re.fullmatch(PERSON_RE, person or "") or not re.fullmatch(DATEI_RE, datei or ""):
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


def aehnliche_unbekannte(person, max_n=12, min_sim=0.28, abstand=0.10):
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
    # .310 (User-Fund 21.08.: die Liste bot fuer eine Bewohnerin drei Gesichter
    # einer ANDEREN Bewohnerin an, Sim 0,28-0,30): dieselbe Identitaets-Regel
    # wie ueberall (bild_stufe): ist eine andere Person naeher oder fehlt der
    # Abstand, ist das Gesicht KEIN Vorschlag fuer diese Person.
    fremd_M = {p: np.asarray(z[p], np.float32) for p in z.files
               if p not in ("meta", "§meta", person) and len(z[p])}
    # pro (person,datei): aktiv-Status aus der LETZTEN Zeile, eid aus IRGENDEINER Zeile des
    # Keys — spaetere Zeilen ohne eid (z.B. der Export-Vermerk von sync_refs) duerfen die
    # benenne-Zuordnung nicht verdraengen (Review-Finding 19.07.); ein geloeschtes
    # Referenzbild (Tombstone) gibt sein Gesicht wieder fuer Vorschlaege frei.
    # AUSNAHME (.138 Panel-Befund): die offer-again-Zeile der Sync-Seite ist KEINE
    # Loeschung — das Bild liegt weiter im Master und zaehlt als Referenz. Sie wird
    # am Marker aus der EINEN Quelle uebersprungen, sonst taucht das angelernte
    # Gesicht wieder als Unbekannt-Vorschlag auf (Weg zum exakten Duplikat).
    from sync_refs import GRUND_WIEDER_ANBIETEN as _GRUND_WA
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
            if not d.get("aktiv", True) and d.get("grund") == _GRUND_WA:
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
            fremd = max((float((M @ v).max()) for M in fremd_M.values()), default=None)
            if fremd is not None and (fremd >= s or (s - fremd) < abstand):
                continue                      # fremd naeher / zu wenig Abstand -> raus
            out.append({"id": g["id"], "camera": g.get("camera"), "ts": g.get("ts"),
                        "nn_person": g.get("nn_person"), "nn_score": g.get("nn_score"),
                        "sim": round(s, 3), "fremd": (round(fremd, 3) if fremd is not None else None)})
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


# .230 (User 17.08.: "der Check ist sehr sehr langsam" — GEMESSEN: 11-13 s
# Embedder-Aufbau bei JEDEM Aufruf, refcache-Lesen 0,01 s): der Embedder der
# Vorschlags-/Bruecken-Strecke wird prozessweit EINMAL gebaut und danach
# wiederverwendet. Bewusst stehende Belegung statt wiederkehrender
# Lade-Spitzen (nach der OOM-Jagd die vorhersagbarere Form); Lock gegen
# parallele Erst-Initialisierung (Nachlern-Timer + Bruecken-Klick).
_EMB_CACHE = None
_EMB_LOCK = threading.Lock()
_EMB_LETZTE = 0.0
# .232 (User-Entwurf 17.08.: "wenn jemand auf Today klickt, das Modell
# vorbereiten und nach einer gewissen Zeit aus dem Speicher nehmen"):
# Leerlauf-Freigabe statt Dauerbelegung — gemessen 379 MB RSS; auf 24 GiB
# egal, auf kleinen Produkt-Kisten nicht. Der Waechter prueft alle 5 min.
EMB_LEERLAUF_S = 15 * 60
_EMB_WAECHTER = False


def _emb_waechter():
    global _EMB_CACHE, _EMB_WAECHTER
    with _EMB_LOCK:
        if _EMB_CACHE is not None and time.time() - _EMB_LETZTE > EMB_LEERLAUF_S:
            _EMB_CACHE = None              # laufende Nutzer halten ihre lokale
            _EMB_WAECHTER = False          # Referenz; Neu-Aufbau beim naechsten
            return                         # Griff. Waechter endet mit dem Cache.
    t = threading.Timer(300, _emb_waechter)
    t.daemon = True
    t.start()


def _embedder_geteilt():
    global _EMB_CACHE, _EMB_LETZTE, _EMB_WAECHTER
    with _EMB_LOCK:
        _EMB_LETZTE = time.time()
        if _EMB_CACHE is None:
            _EMB_CACHE = Embedder()
        if not _EMB_WAECHTER:
            _EMB_WAECHTER = True
            t = threading.Timer(300, _emb_waechter)
            t.daemon = True
            t.start()
        return _EMB_CACHE


def embedder_vorwaermen():
    """Nicht-blockierender Vorwaerm-Anstoss (Today-/Auftritts-Klick): baut den
    geteilten Embedder im Hintergrund auf, damit der erste Check sofort
    antwortet. Mehrfach-Anstoesse laufen auf das Lock und sind harmlos."""
    threading.Thread(target=_embedder_geteilt, daemon=True).start()


def embedder_warm():
    """Ist der geteilte Embedder aufgebaut? (Fuer die ehrliche
    'model wird geladen'-Antwort des Pruef-Endpunkts, User-Idee 17.08.)"""
    return _EMB_CACHE is not None


# D1 (.30x, User-Fund 20.08.: der Pass-Knopf meldete "nothing to take …
# (that is fine)", obwohl ALLE 149 Gesichter unter der Groessen-Latte lagen):
# die Gruende von bild_stufe als EINE benannte Quelle. Ein Eintrag traegt
# beides — den UI-Text (Wortlaut UNVERAENDERT) und die sprachneutrale
# Diagnose-KENNUNG (§8.19). Ohne die Tabelle muesste die Diagnose die Texte
# raten: eine zweite verstreute Aufzaehlung genau der Klasse, die die
# QS-Ebenen-Regel verbietet (K3).
GRUND_TEXT = {
    "zu_klein_unscharf": "too small or too blurry for a reference",
    "gedeckt":           "already covered (near-identical to a reference)",
    "fremd_naeher":      "closer to someone else",
    "id_unsicher":       "identity not certain enough",
    "beides_schwach":    "neither quality nor identity strong enough",
    # .316 (User 22.08.): Veto der virtuellen Qualitaetslinie. Der Text nennt die
    # Zahl nicht — die haengt die Flaeche an (wie bei 'zu_klein_unscharf').
    "unter_linie":       "not a face by the quality measure",
    # .32x: Struktur-Test — der Ausschnitt zeigt keine Gesichtsstruktur (Nacken,
    # Ohr, Hinterkopf, Vegetation). Die Zahl haengt die Flaeche an.
    "keine_struktur": "no face structure in this crop",
    # .377 (Kalibrier-Funktion): die vom Nutzer kalibrierte Guete-Latte hat das
    # Bild verworfen. EIGENER Grund statt 'zu_klein_unscharf', weil der alte
    # Text von Groesse und Schaerfe spricht — beides ist auf diesem Weg gerade
    # NICHT das Kriterium (Messtag 30.08.: r=-0,06). Die Zahlen haengt die
    # Flaeche an, wie bei 'zu_klein_unscharf'.
    "guete_zu_schwach": "image quality too low for a reference",
    # BELICHTUNG (bauplan_belichtung.md E5b, Issue 26): der Ausschnitt liegt
    # ausserhalb der Belichtungsgrenzen. Beides sind GRENZFALL-Gruende, nie
    # 'raus' — bewusste Zuwahl bleibt moeglich (Memory 'nicht loeschen,
    # Mehrdeutigkeit aufloesen'). Die Zahlen haengt die Flaeche an.
    "zu_dunkel":         "too dark for a reference",
    "ueberbelichtet":    "overexposed for a reference",
    # Die zwei Grade der Stufe 'neutral' (kein Ausschluss) — der
    # Vollstaendigkeit halber hier, damit bild_stufe KEINEN Text
    # ausserhalb dieser Tabelle bildet.
    "nur_qualitaet":     "quality only fair",
    "nur_identitaet":    "identity not fully certain",
}
GRUND_KLASSE = {text: kennung for kennung, text in GRUND_TEXT.items()}


def bild_stufe(eigen, fremd, kante, sh, *,
               min_kante=REF_LATTE["min_kante"],
               unscharf_max=REF_LATTE["unscharf_max"],
               sim_min=0.45, sim_neu=0.75, sim_unsicher=0.30, abstand=0.10,
               kante_gut=REF_LATTE["kante_gut"],
               sharp_gut=REF_LATTE["sharp_gut"],
               norm=None, norm_gut=None, norm_min=None,
               norm_kante_min=None, norm_sharp_min=None,
               fiqa_t=None, empf=None,
               guete_t_min=None, guete_empfinden_min=None):
    """.257: die Zwei-Achsen-Bewertung der Bruecke als EINE QUELLE (QS-Ebenen-
    Regel; Anlass: die Benenn-Pruefung der Zuweisungs-Flaeche hatte nur den
    Dedup und liess 12 matschige Bilder als 'neu' durch — User-Fang am
    Screenshot). Identitaet: eigen>=sim_min sicher / eigen>=sim_unsicher mit
    Abstand wahrscheinlich / sonst raus; eigen>=sim_neu = Bestands-Duplikat;
    fremd>=eigen = raus. Qualitaet: Mindest-Gate kante/sharp, GUT ab
    kante_gut/sharp_gut. eigen=None (Person ohne Referenzen, Kaltstart der
    Gruppe): Identitaet gilt als User-Wort, nur die Qualitaets-Achse traegt.
    NORM-WEG (.307, User-Go 20.08. — Screenshot-Fund: 27 scharfe Bilder an
    'needs 70 px' abgelehnt): tragen die norm_*-Parameter Werte (Aufrufer
    liefert sie aus der Config, nur bei vorrat_aktiv) und ist eine
    Feature-Norm gemessen, qualifiziert sie ALTERNATIV zur Pixel-Latte:
    norm >= norm_min als Mindest-Gate, norm >= norm_gut als GUT-Stufe,
    jeweils mit den Vorrats-Boeden norm_kante_min/norm_sharp_min. Ohne die
    Parameter (Default) urteilt die Funktion UNVERAENDERT (.257-Gate-Vektoren).
    GUETE-WEG (.377, User-Entscheid 30.08.): traegt das Bild beide Ernte-Masse
    (fiqa_t/empf) UND sind beide Schwellen gesetzt, urteilt die kalibrierte
    Guete-Latte statt der Laplacian-Schaerfe — siehe unten.
    -> (stufe 'empfohlen'|'neutral'|None, grund_englisch fuer die UI)."""
    _norm_ok = (norm is not None and norm_min is not None
                and kante is not None and sh is not None
                and norm >= norm_min
                and kante >= (norm_kante_min or 0)
                and sh >= (norm_sharp_min or 0))
    # .377 GUETE-WEG — DIESELBE Staffelung wie core.benennung._lattenklasse
    # (Vorauswahl): GUT ab Kante/Empfinden/Erkennbarkeit, darunter bleibt der
    # Norm-Alternativweg, dessen sharp-Boden hier bewusst entfaellt (das Mass
    # ist abgeloest), waehrend der Kanten-Boden bleibt. Anlass (QS-Befund
    # 30.08.): das Sieb der Gruppenbildung urteilte seit .377 nach der Guete,
    # die Flaeche und diese LETZTE Instanz vor der Uebernahme weiter nach der
    # Schaerfe — am Feldmaterial fielen 540 von 541 neu zugelassenen Bildern
    # hier wieder durch, der Nutzer bekam Gruppen ohne ein einziges
    # ankreuzbares Bild (die .367-Fehlerklasse).
    # Fehlt eines der vier Stuecke (Alt-Laeufe, Alt-Images ohne die Modelle,
    # Lern-Bruecke am frisch gemessenen Crop), urteilt der Alt-Weg darunter
    # Zeile fuer Zeile unveraendert weiter (.257-Gate-Vektoren).
    _g_da = (fiqa_t is not None and empf is not None
             and guete_t_min is not None and guete_empfinden_min is not None)
    _g_gut = False
    if _g_da:
        # .379 (User-Entscheid 30.08.): allein die kalibrierte Latte — die
        # Norm-Rettung nach oben ist raus (Begruendung: core.benennung.
        # _lattenklasse, dieselbe Aenderung im selben Zug).
        _g_gut = (kante is not None and kante >= min_kante
                  and float(empf) >= float(guete_empfinden_min)
                  and float(fiqa_t) >= float(guete_t_min))
        if not _g_gut:
            return None, GRUND_TEXT["guete_zu_schwach"]
    elif ((kante is None or sh is None or kante < min_kante or sh < unscharf_max)
            and not _norm_ok):
        return None, GRUND_TEXT["zu_klein_unscharf"]
    if eigen is not None:
        if eigen >= sim_neu:
            return None, GRUND_TEXT["gedeckt"]
        if fremd is not None and fremd >= eigen:
            return None, GRUND_TEXT["fremd_naeher"]
        if eigen >= sim_min:
            id_sicher = True
        elif eigen >= sim_unsicher and (fremd is None
                                        or (eigen - fremd) >= abstand):
            id_sicher = False
        else:
            return None, GRUND_TEXT["id_unsicher"]
    else:
        id_sicher = True
    if _g_da:
        # GUT im Guete-Weg = Klasse 0 von _lattenklasse: die kalibrierte
        # Latte, sonst nichts (.379) — wer bis hier kommt, hat sie bestanden.
        qual_gut = _g_gut
    else:
        qual_gut = (kante >= kante_gut and sh >= sharp_gut) or (
            norm is not None and norm_gut is not None and norm >= norm_gut
            and kante >= (norm_kante_min or 0) and sh >= (norm_sharp_min or 0))
    if id_sicher and qual_gut:
        return "empfohlen", ""
    if id_sicher or qual_gut:
        return "neutral", (GRUND_TEXT["nur_qualitaet"] if not qual_gut
                           else GRUND_TEXT["nur_identitaet"])
    return None, GRUND_TEXT["beides_schwach"]


def refs_matrix_roh(modell):
    """Referenz-Matrizen je Person aus dem refcache OHNE Embedder (.266,
    Seiten-Render): der modell-String kommt vom Aufrufer (cfg['modell']).
    Kein Master-Fallback — der braeuchte das Modell; eine fehlende Person
    heisst fuer die Matrix: Identitaet ist das User-Wort."""
    refs = {}
    cache = os.path.join(CLIPS, "refcache.npz")
    if os.path.exists(cache):                      # pruefe_referenzen haelt ihn frisch
        try:
            z = np.load(cache, allow_pickle=True)
            if str(_cache_meta(z).get("§modell", "")) != str(modell):
                raise ValueError("refcache anderes Recognition-Modell")   # -> frisch aus Master
            refs = {p: np.asarray(z[p], np.float32) for p in z.files if p not in ("meta", "§meta")}
        except Exception:
            refs = {}
    return refs


def refs_matrix(emb):
    """Referenz-Matrizen je Person: refcache wenn modellgleich, sonst Master.
    .257 extrahiert aus vorschlaege_person (EINE Quelle — Bruecke UND
    Benenn-Pruefung laden identisch); .266 duenner Mantel um refs_matrix_roh."""
    return refs_matrix_roh(emb.modell)


def diagnose_dominant(dg):
    """D1 (.30x): DIE eine Klasse, die den Ausgang einer Bestands-/Pass-Pruefung
    erklaert. Zuerst die Faelle, die die Zaehlung selbst erklaeren (Person ohne
    Referenzen / kein Event im Scope / kein einziges gemessenes Bild), danach
    der haeufigste Ausschlussgrund. Gleichstand loest alphabetisch auf, damit
    dieselben Zahlen immer denselben Satz ergeben (kein Zufall aus der
    dict-Reihenfolge). -> Kennung|None (None = nichts zu erklaeren)."""
    if not dg:
        return None
    if dg.get("keine_referenzen"):
        return "keine_referenzen"
    if not dg.get("events"):
        return "keine_events"
    if not dg.get("geprueft"):
        return "kein_crop"
    klassen = dg.get("klassen") or {}
    if not klassen:
        return None
    return max(sorted(klassen), key=lambda k: klassen[k])


def vorschlaege_person(person, tage=7.0, max_n=16,
                       min_kante=REF_LATTE["min_kante"],
                       unscharf_max=REF_LATTE["unscharf_max"],
                       sim_min=0.45, sim_neu=0.75, sim_unsicher=0.30, abstand=0.10,
                       kante_gut=REF_LATTE["kante_gut"],
                       sharp_gut=REF_LATTE["sharp_gut"], max_pruef=80,
                       nur_eids=None, schreiben=True, emb=None,
                       diagnose=None, norm_latte=None):
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
    Neueste Events zuerst, hoechstens max_pruef Bild-Messungen. Ergebnis -> vorschlaege_*.json.
    diagnose (D1, .30x): OPTIONALES dict des Aufrufers, das hier BEFUELLT wird —
    je Ausschlussklasse ein Zaehler plus die Bestwerte (kante_max/sharp_max) und
    die geltenden Schwellen. Reine Berichts-Erweiterung: die Entscheidung, wer
    durchkommt, ist unveraendert; gezaehlt wird nur, WORAN es lag. Ohne dict
    kostet sie ein paar Additionen und sonst nichts."""
    # .235: uebergebene Instanz (svc.embedder, OV-schnell) hat Vorrang —
    # die Bruecke lief sonst auf einer zweiten CPU-Instanz (~2 s je Bild).
    emb = emb or _embedder_geteilt()
    refs = refs_matrix(emb)                        # .257: EINE Ladequelle
    if not len(refs.get(person, [])):
        refs = lade_master_refs(emb)
    kand = []
    # D1: der Diagnose-Satz wird IMMER mitgefuehrt (billig) und nur am Ende in
    # das dict des Aufrufers gespiegelt. 'klassen' sind Kennungen, keine Texte.
    dg = {"person": person, "events": 0, "geprueft": 0, "klassen": {},
          "kante_max": None, "sharp_max": None,
          "min_kante": int(min_kante), "unscharf_max": int(unscharf_max),
          "keine_referenzen": not len(refs.get(person, [])),
          "gedeckelt": False, "empfohlen": 0, "neutral": 0}

    def _zaehl(klasse):
        dg["klassen"][klasse] = dg["klassen"].get(klasse, 0) + 1

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
            # .225 (Lern-Bruecke): auf die Events EINES Durchgangs gescoped —
            # dieselben Siebe, nur die Quelle ist der eine Pass.
            if nur_eids is not None and eid not in nur_eids:
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
        dg["events"] = len(eventliste)
        # 2) teure Bild-Messung nur auf die neuesten max_pruef Events mit Crop
        geprueft = 0
        gedeckelt = False
        for d in eventliste:
            ed = os.path.join(DATA, "events", d["eid"].replace("/", "_"))
            if not os.path.isdir(ed):
                _zaehl("kein_crop")
                continue
            # D3 (.30x): EXAKT dieselbe Wahl wie die Auftritte-Seite
            # (auftritte._crop_url: sorted + [-1]). Vorher entschied
            # os.listdir()[0], also die Verzeichnisreihenfolge — die Pruefung
            # konnte ein ANDERES Bild messen als der Nutzer auf der Seite
            # sieht. Ziel ist die Deckungsgleichheit, nicht eine bessere
            # Formel: dass die Sortierung bei mehreren label-Praefixen im
            # Namen nicht streng nach dem NN-Score geht, ist eine Eigenschaft
            # BEIDER Stellen und bleibt hier unangetastet (Wahl waere sonst
            # wieder verschieden).
            js = (sorted(f for f in os.listdir(ed) if f"_show_{person}_" in f) or
                  sorted(f for f in os.listdir(ed) if f"_best_{person}_NN" in f))
            if not js:
                _zaehl("kein_crop")
                continue
            if geprueft >= max_pruef:
                gedeckelt = True
                dg["gedeckelt"] = True
                break
            datei = js[-1]
            img = cv2.imread(os.path.join(ed, datei))
            if img is None:
                _zaehl("kein_crop")
                continue
            geprueft += 1
            dg["geprueft"] = geprueft
            # .308: Norm aus DERSELBEN Detektion — der Norm-Weg qualifiziert
            # alternativ zur Pixel-Latte (norm_latte aus der Dienst-Config).
            v, kante, sh, norm = bild_metriken(emb, img, mit_norm=True)
            _nl = norm_latte or {}
            _norm_ok = (norm is not None and _nl.get("min") is not None
                        and kante is not None and norm >= _nl["min"]
                        and kante >= (_nl.get("kante") or 0) and sh >= (_nl.get("sharp") or 0))
            if kante is not None:
                dg["kante_max"] = max(dg["kante_max"] or 0, int(kante))
            if sh is not None:
                dg["sharp_max"] = max(dg["sharp_max"] or 0, int(sh))
            # Bildqualitaet-Mindest-Gate: zu klein/unscharf -> unbrauchbare Referenz.
            # D1: dieselbe Reihenfolge derselben drei Bedingungen wie vorher
            # (v/kante -> min_kante -> unscharf_max), nur benannt statt gebuendelt —
            # die Entscheidung ist Zeile fuer Zeile dieselbe.
            if v is None or kante is None:
                _zaehl("kein_gesicht")
                continue
            if kante < min_kante and not _norm_ok:
                _zaehl("zu_klein")
                continue
            if sh < unscharf_max and not _norm_ok:
                _zaehl("zu_unscharf")
                continue
            eigen = float((refs[person] @ v).max())
            fremd = max((float((M @ v).max()) for p2, M in refs.items()
                         if p2 != person and len(M)), default=-1.0)
            # .257: Zwei-Achsen-Matrix aus der EINEN Quelle (bild_stufe) —
            # identische Semantik wie die Inline-Fassung davor.
            stufe, grund = bild_stufe(
                eigen, fremd, kante, sh, min_kante=min_kante,
                unscharf_max=unscharf_max, sim_min=sim_min, sim_neu=sim_neu,
                sim_unsicher=sim_unsicher, abstand=abstand,
                kante_gut=kante_gut, sharp_gut=sharp_gut,
                norm=norm, norm_gut=_nl.get("gut"), norm_min=_nl.get("min"),
                norm_kante_min=_nl.get("kante"), norm_sharp_min=_nl.get("sharp"))
            if stufe is None:
                # D1: der Grund wurde hier bisher weggeworfen (_grund) — genau
                # deshalb konnte die Bruecke "nichts Brauchbares" melden, ohne
                # sagen zu koennen woran es lag. Kennung statt Text (§8.19).
                _zaehl(GRUND_KLASSE.get(grund, "sonstiges"))
                continue
            kand.append({"eid": d["eid"], "datei": datei, "sim": round(eigen, 3),
                         "fremd": round(fremd, 3), "kante": kante, "sharp": sh,
                         "norm": norm,
                         "stufe": stufe, "sicher": (stufe == "empfohlen"),
                         "camera": d.get("camera"), "ts": d.get("start") or d.get("ts")})
        kand.sort(key=lambda k: (0 if k["stufe"] == "empfohlen" else 1, k["sim"]))
        kand = kand[:max_n]
        dg["empfohlen"] = sum(1 for k in kand if k["stufe"] == "empfohlen")
        dg["neutral"] = sum(1 for k in kand if k["stufe"] == "neutral")
        if gedeckelt:
            print(f"vorschlaege {person}: cap of {max_pruef} image measurements reached, "
                  f"older events unchecked", flush=True)
    dg["dominant"] = diagnose_dominant(dg)
    if diagnose is not None:
        diagnose.update(dg)
    if schreiben:
        os.makedirs(ANLERN, exist_ok=True)
        _schreibe_json_atomar(_vorschlaege_pfad(person),
                              {"ts": time.time(), "person": person, "tage": tage,
                               "kandidaten": kand})
    return kand


def refcache_ergaenzen(person, bild_pfad, datei, emb, emb_vec=None, emb_modell=None):
    """.236 (User-Befund: nach einer Uebernahme war die naechste Pruefung
    wieder langsam, OHNE Lade-Hinweis — das Modell war warm, aber der
    verworfene refcache zwang einen vollen Inline-Neuaufbau ueber ~300
    Referenzbilder): EIN neues Bild wird in den Cache EINGEPFLEGT statt ihn
    zu verwerfen — Embedding anhaengen + Datei-Liste im §meta nachziehen,
    atomar (tmp+fsync+replace wie pruefe_referenzen). False = Aufrufer
    verwirft wie bisher (kein Cache, Modell-Mismatch, Lesefehler)."""
    ziel = os.path.join(CLIPS, "refcache.npz")
    try:
        if not os.path.exists(ziel):
            return False
        z = np.load(ziel, allow_pickle=True)
        meta = _cache_meta(z)
        if emb_vec is not None:
            # A2-Vertrag Stelle 6 (Vorrats-Uebernahme): der Vollbild-Beiwert
            # ist der Vektor — embed(datei) waere die tote Nach-Detektion.
            if str(meta.get("§modell", "")) != str(emb_modell or ""):
                return False
            v = np.asarray(emb_vec, dtype=np.float64)
        else:
            if emb is None or str(meta.get("§modell", "")) != emb.modell:
                return False
            img = cv2.imread(bild_pfad)
            v = emb.embed(img) if img is not None else None
            if v is None:
                return False
        refs = {p: np.asarray(z[p], np.float32) for p in z.files
                if p not in ("meta", "§meta")}
        alt = refs.get(person)
        neu = v.astype(np.float32)[None, :]
        refs[person] = np.vstack([alt, neu]) if alt is not None and len(alt) else neu
        want = {k: list(w) for k, w in meta.items() if not str(k).startswith("§")}
        want.setdefault(person, []).append(datei)
        want[person] = sorted(set(want[person]))
        # .309: im Beiwert-Zweig gibt es kein emb — das Modell kommt aus dem
        # (bereits geprueften) Meta-Block; emb.modell warf hier einen
        # AttributeError -> False -> Cache verworfen -> Voll-Neuaufbau je
        # Uebernahme (User-Fund 21.08. 'Referenzen werden neu aufgebaut').
        # .411: eindeutige tmp ueber core.atomar (Kollision refcache.npz.tmp-<pid>).
        _atomar.schreiben(
            ziel,
            lambda f: np.savez(f, **{"§meta": json.dumps({**want, "§modell": str(meta.get("§modell", ""))})},
                               **refs),
            suffix=".npz", binaer=True)
        return True
    except Exception:
        return False


def refcache_ergaenzen_viele(person, bilder, emb, modell=None):
    """.313 (User-Fund 21.08. am Lernlauf: nach JEDER Gruppen-Benennung lief ein
    Voll-Neuaufbau ueber ~327 Referenzen, weil die Uebernahme den Cache verwarf):
    MEHRERE neue Referenzen einer Person in EINEM Zug einpflegen — Gruppen-
    Uebernahme im Lernlauf, Unbekannt-Benennung, Enrollment, Upload. Liest die
    npz einmal, schreibt einmal atomar (tmp+fsync+replace).
    bilder: [(bild_pfad, datei)] ODER [(bild_pfad, datei, emb_vec)] — mit
    Vektor (.313b: A2-Beiwert der Lernlauf-Uebernahme = Ernte-Messung) wird
    die Datei NICHT gemessen (fuer randlose Klein-Crops ist die Datei-Detektion
    gemessen tot, 28/40 — lade_master_refs nimmt fuer Beiwert-Referenzen
    ebenfalls den Beiwert, Ergebnis gleich zum Neuaufbau); ohne Vektor wird
    wie bisher auf demselben Weg wie lade_master_refs embeddet.
    modell: Modell-Kennung, wenn KEIN Embedder da ist (nur Beiwert-Zeilen).
    -> True = Cache konsistent: eingepflegt, oder es gab keinen Cache (dann baut
       ihn die naechste Pruefung ohnehin). False = Aufrufer verwirft den Cache
       wie bisher (kein Embedder UND kein Vektor, Modell-Mismatch, Lese-/
       Schreibfehler).
    Dateien ohne Nach-Detektion (embed -> None) werden uebersprungen — der
    Neuaufbau liesse sie genauso aus (lade_master_refs: 'if v is not None')."""
    ziel = os.path.join(CLIPS, "refcache.npz")
    try:
        if not os.path.exists(ziel):
            return True
        eintraege = [tuple(b) for b in bilder]
        if emb is None and any(len(b) < 3 or b[2] is None for b in eintraege):
            return False
        modell = str(emb.modell if emb is not None else (modell or aktuelles_modell())).lower()
        z = np.load(ziel, allow_pickle=True)
        meta = _cache_meta(z)
        if str(meta.get("§modell", "")) != modell:
            return False
        neue = []
        for b in eintraege:
            bild_pfad, datei = b[0], b[1]
            if len(b) >= 3 and b[2] is not None:
                v = np.asarray(b[2], np.float32)
            else:
                img = cv2.imread(bild_pfad)
                v = emb.embed(img) if img is not None else None
            if v is not None:
                neue.append((datei, v.astype(np.float32)))
        refs = {p: np.asarray(z[p], np.float32) for p in z.files
                if p not in ("meta", "§meta")}
        want = {k: list(w) for k, w in meta.items() if not str(k).startswith("§")}
        if neue:
            alt = refs.get(person)
            M = np.vstack([v[None, :] for _, v in neue])
            refs[person] = np.vstack([alt, M]) if alt is not None and len(alt) else M
        # Datei-Liste traegt ALLE neuen Dateien (auch ohne Vektor) — wie want in
        # lade_master_refs/refcache_aufbauen: sync_refs.master_stand vergleicht
        # Dateilisten, nicht Vektoren.
        want.setdefault(person, []).extend(b[1] for b in eintraege)
        want[person] = sorted(set(want[person]))
        # .411: eindeutige tmp ueber core.atomar — genau DIESE Stelle warf beim
        # Tester (02.09.) 2x FileNotFoundError 'refcache.npz.tmp-1' -> refcache.npz
        # (zwei Laeufe im selben Prozess, gleicher tmp-Name).
        _atomar.schreiben(
            ziel,
            lambda f: np.savez(f, **{"§meta": json.dumps({**want, "§modell": modell})}, **refs),
            suffix=".npz", binaer=True)
        return True
    except Exception as e:
        print(f"refcache_ergaenzen_viele failed: {type(e).__name__}: {e}", flush=True)
        return False


_REFCACHE_BAU = threading.Lock()
# .311 (User 21.08., Lernlauf-Karte: 'hier koennte man auch so einen kleinen
# Balken bauen, damit der User ein Gefuehl bekommt, dass noch etwas im
# Hintergrund passiert'): EIN Modul-Stand fuer den Hintergrund-Neuaufbau —
# refcache_aufbauen pulst i/n hinein, refcache_fortschritt liest ihn, die drei
# Warte-Antworten (Bruecke, Sichtung, Benenn-Pruefung) reichen ihn durch.
_REFCACHE_STAND = {"laeuft": False, "i": 0, "n": 0, "fehler": 0, "fehler_ts": 0.0}
# Fehler-Pause (Widerleger .311, beide Linsen): scheitert der Bau zweimal in
# Folge (Platte voll, Rechte, Ordner weg), startete sonst JEDER Poll alle
# 2,5 s einen neuen Voll-Neuaufbau, und die Blaetter pollten endlos (der
# 60-s-Deckel des Auftritte-Blatts greift auf dem zustand-Ast nicht). In der
# Pause laeuft kein Bau, die Warte-Antwort wird ok:false -> Schleifen enden.
REFCACHE_FEHLER_PAUSE_S = 600


def _refcache_puls(i, n):
    # n zieht mit i nach: waechst MASTER waehrend des Baus (Uebernahme ohne
    # Bau-Lock), liefe i sonst ueber das vorab gezaehlte n hinaus ('313/312').
    _REFCACHE_STAND["i"], _REFCACHE_STAND["n"] = int(i), max(int(n), int(i))


def refcache_fortschritt():
    """Fortschritt des refcache-Neuaufbaus: {laeuft, i, n, fehler, pause} —
    i/n sind 0/0, solange noch gezaehlt wird (Blatt zeigt den leeren Balken);
    pause=True heisst: zwei Fehlschlaege in Folge, Bau ruht fuer
    REFCACHE_FEHLER_PAUSE_S (die Warte-Antwort meldet dann einen Fehler)."""
    s = _REFCACHE_STAND
    pause = (s["fehler"] >= 2
             and time.time() - s["fehler_ts"] < REFCACHE_FEHLER_PAUSE_S)
    return {"laeuft": bool(s["laeuft"]), "i": int(s["i"]), "n": int(s["n"]),
            "fehler": int(s["fehler"]), "pause": bool(pause)}


def refcache_aufbauen(emb):
    """.236: refcache im HINTERGRUND neu aufbauen (fuer die Faelle, die weiter
    voll invalidieren: Undo, Loeschung, Cluster-benenne) — die Bruecke meldet
    solange ehrlich 'updating …' statt den Neuaufbau inline zu zahlen.
    Nicht-blockierend fuer Zweitaufrufer (Lock non-blocking). .311: pulst
    i/n in _REFCACHE_STAND, meldet Fehlschlaege LAUT und haelt nach zwei
    Fehlschlaegen in Folge die Fehler-Pause ein (kein dritter Voll-Neuaufbau
    je Poll); der naechste Erfolg setzt den Zaehler zurueck."""
    if refcache_fortschritt()["pause"]:
        return False
    if not _REFCACHE_BAU.acquire(blocking=False):
        return False
    _REFCACHE_STAND.update(laeuft=True, i=0, n=0)
    try:
        refs = lade_master_refs(emb, puls=_refcache_puls)
        want = {}
        for p in sorted(refs):
            pd = os.path.join(MASTER, p)
            want[p] = sorted(f for f in os.listdir(pd)
                             if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        ziel = os.path.join(CLIPS, "refcache.npz")
        # .411: eindeutige tmp ueber core.atomar (Kollision refcache.npz.tmp-<pid>).
        _atomar.schreiben(
            ziel,
            lambda f: np.savez(f, **{"§meta": json.dumps({**want, "§modell": emb.modell})},
                               **refs),
            suffix=".npz", binaer=True)
        _REFCACHE_STAND["fehler"] = 0
        return True
    except Exception as e:
        _REFCACHE_STAND["fehler"] += 1
        _REFCACHE_STAND["fehler_ts"] = time.time()
        print(f"refcache_aufbauen failed ({_REFCACHE_STAND['fehler']}x in a row): "
              f"{type(e).__name__}: {e}", flush=True)
        return False
    finally:
        _REFCACHE_STAND["laeuft"] = False
        _REFCACHE_BAU.release()


def vorschlag_aufnehmen(person, eid, datei, emb=None, kat_latten=None):
    """Einen Bestands-Vorschlag als Referenz uebernehmen: Event-Crop -> Master (Containment),
    refs_meta, refcache-Invalidierung; Vorschlags-JSON um den Eintrag bereinigen.

    kat_latten: die Katalog-Latte der Kamera (Zentral-Umbau 31.08.). EHRLICHE
    GRENZE dieses Wegs: die Vorschlags-Zeile traegt `camera`, aber KEINE
    Guete-Masse — dieser Pfad misst kante/sharp/norm am Event-Crop, nicht
    fiqa_t/empf. Die Latte wird trotzdem gefragt (Deckungs-Vertrag: jede
    Uebernahme-Stelle fragt dieselbe Funktion) und laesst ungemessene Bilder
    durch. Sobald diese Zeilen die zwei Masse tragen, beisst sie hier ohne
    weitere Aenderung."""
    import re, shutil
    from core import kamerakalib as _kk
    from core.registry import DATEI_RE, PERSON_RE   # Vertrag statt Streu-Literal (Sweep 03.08.)
    if not re.fullmatch(PERSON_RE, person or "") or not re.fullmatch(rf"{DATEI_RE}\.jpg", datei or "", re.I):
        return False, "ungueltige Angaben"
    v = lade_vorschlaege(person)
    _kand = next((k for k in (v or {}).get("kandidaten", [])
                  if k.get("eid") == eid and k.get("datei") == datei), {})
    _kok, _kgrund = _kk.katalog_ok(kat_latten, _kand.get("camera"),
                                   _kand.get("empf"), _kand.get("fiqa_t"))
    if not _kok:
        return False, _kgrund
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
        # .401: camera durchreichen (Guete-Masse hat dieser Weg nicht —
        # die Nachmessung des Bestands holt sie nach)
        f.write(json.dumps({"ts": round(time.time(), 1), "person": person, "datei": ziel,
                            "herkunft": "bestands-suche", "eid": eid, "aktiv": True,
                            "camera": (_kand.get("camera") if isinstance(_kand, dict) else None)},
                           ensure_ascii=False) + "\n")
        f.flush()
    if v:
        v["kandidaten"] = [k for k in v.get("kandidaten", [])
                           if not (k.get("eid") == eid and k.get("datei") == datei)]
        _schreibe_json_atomar(_vorschlaege_pfad(person), v)   # parallel zum vorschlaege-Subprozess
    # .236: mit uebergebenem Embedder wird der Cache EINGEPFLEGT statt
    # verworfen (sonst zahlt die naechste Pruefung den vollen Neuaufbau).
    if not refcache_ergaenzen(person, os.path.join(zdir, ziel), ziel, emb):
        try:
            os.remove(os.path.join(CLIPS, "refcache.npz"))
        except FileNotFoundError:
            pass
    # .225: der ZIEL-Dateiname als zweiter Wert (Lern-Bruecke braucht ihn fuer
    # das Undo via entferne_referenz); der /lernen-Aufrufer ignoriert ihn.
    return True, ziel


def vorrat_aufnehmen(person, lauf_id, datei, eid, data_dir=None,
                     kat_latten=None):
    """Ein Vorrats-Angebot als Referenz uebernehmen (bauplan_vorrat.md B4;
    EIGENER Zweig neben vorschlag_aufnehmen — der Event-Crop-Draht kann den
    Vorrats-Pfad nicht transportieren, Konzept-QS W1.13):
    v-Crop -> Master (eigene Containment-Basis state/lernlauf/<lid>/vorrat),
    refs_meta MIT A2-Beiwert (emb + emb_modell + Lauf-Messwerte, serverseitig
    aus der vorrat.jsonl des Laufs nachgeschlagen — W2.11), refcache-Einpflege
    ueber den Beiwert. -> (ok, ziel_oder_fehler)."""
    import re, shutil
    from core.registry import PERSON_RE, DATEI_RE   # Namens-Vertrag statt Streu-Literal
    from core import vorrat as _vor
    dd = data_dir or DATA
    if (not re.fullmatch(PERSON_RE, person or "")
            or not re.fullmatch(r"[LB]\w+", str(lauf_id or ""))   # L = Lernlauf, B = Bruecke
            or not str(datei or "").startswith("v_")
            or not re.fullmatch(rf"{DATEI_RE}\.jpg", str(datei or ""), re.I)):
        return False, "ungueltige Angaben"
    basis = os.path.realpath(os.path.join(dd, "state", "lernlauf",
                                          str(lauf_id), "vorrat"))
    quelle = os.path.realpath(os.path.join(basis, datei))
    if not quelle.startswith(basis + os.sep) or not os.path.isfile(quelle):
        return False, "Vorrats-Crop nicht gefunden (Lauf geloescht?)"
    emb_vec, zeile = _vor.beiwert_nachschlagen(dd, lauf_id,
                                               os.path.join("vorrat", datei))
    if emb_vec is None:
        # Ohne Beiwert keine Uebernahme: die Datei allein waere die tote
        # Referenz aus dem 28/40-Befund — LAUT ablehnen statt still anlegen.
        return False, "kein Embedding-Beiwert im Lauf (vorrat.jsonl fehlt/alt)"
    if str(zeile.get("eid") or "") != str(eid or ""):
        return False, "Angebot passt nicht zum Event"
    # KATALOG-LATTE (Zentral-Umbau 31.08.), dieselbe EINE Funktion wie an den
    # anderen Uebernahme-Stellen. Die Vorrats-Zeile traegt `kamera`, aber
    # keine Guete-Masse (der v-Zweig misst Norm, nicht fiqa_t/empf) — die
    # Latte laesst sie deshalb heute durch und beisst hier, sobald die Zeile
    # gemessen ist. Gefragt wird sie trotzdem: der Deckungs-Vertrag kennt
    # keine Ausnahme "hat gerade keine Werte".
    from core import kamerakalib as _kk
    _kok, _kgrund = _kk.katalog_ok(kat_latten, zeile.get("kamera"),
                                   zeile.get("empf"), zeile.get("fiqa_t"))
    if not _kok:
        return False, _kgrund
    zdir = os.path.join(MASTER, person)
    os.makedirs(zdir, exist_ok=True)
    ed = str(eid).replace("/", "_")
    ziel = f"vorrat_{int(time.time())}_{ed[-10:]}_{re.sub(r'[^\w.-]', '_', datei)[-30:]}"
    shutil.copyfile(quelle, os.path.join(zdir, ziel))
    with open(os.path.join(MASTER, "refs_meta.jsonl"), "a") as f:
        f.write(json.dumps({"ts": round(time.time(), 1), "person": person,
                            "datei": ziel, "herkunft": "vorrat", "eid": eid,
                            "aktiv": True, "emb": emb_vec,
                            "emb_modell": zeile.get("modell"),
                            "kante": zeile.get("kante"),
                            "sharp": zeile.get("sharp"),
                            "norm": zeile.get("norm"),
                            "camera": zeile.get("kamera"),
                            "fiqa_t": zeile.get("fiqa_t"),
                            "empf": zeile.get("empf"),
                            "lauf_id": lauf_id, "datei_v": zeile.get("datei_v")},
                           ensure_ascii=False) + "\n")
        f.flush()
    if not refcache_ergaenzen(person, os.path.join(zdir, ziel), ziel, None,
                              emb_vec=emb_vec, emb_modell=zeile.get("modell")):
        try:
            os.remove(os.path.join(CLIPS, "refcache.npz"))
        except FileNotFoundError:
            pass
    return True, ziel


def lernbruecke_pruefen(person, eids, emb=None, diagnose=None, norm_latte=None):
    """Lern-Bruecke Schritt 1 (User 16.08., zweite Fassung: 'erst pruefen,
    welche Bilder uebernommen werden sollen — dann ist der gleiche Schalter:
    uebernehme diese Bilder'): dieselben Siebe wie die Bestands-Suche
    (Identitaet/Qualitaet/Neuheit), gescoped auf die Pass-Events. UEBERNIMMT
    NICHTS — liefert nur, was Stufe 'empfohlen' erreicht hat, damit der
    Nutzer es sieht und entscheidet. -> (kandidaten, zurueckgehalten).
    diagnose (D1, .30x): OPTIONALES dict, das mit den Zahlen der Pruefung
    befuellt wird (Klassen-Zaehler, Bestwerte, Schwellen, 'dominant'). Der
    Aufrufer beantwortet damit die Frage 'warum nichts?' mit Zahlen statt
    mit dem Pauschal-Satz — die Auswahl selbst ist unveraendert."""
    eids = {str(e) for e in (eids or []) if e}
    if not eids:
        if diagnose is not None:
            diagnose.update({"person": person, "events": 0, "geprueft": 0,
                             "klassen": {}, "kante_max": None, "sharp_max": None,
                             "min_kante": int(REF_LATTE["min_kante"]),
                             "unscharf_max": int(REF_LATTE["unscharf_max"]),
                             "keine_referenzen": False, "gedeckelt": False,
                             "empfohlen": 0, "neutral": 0,
                             "dominant": "keine_events"})
        return [], []
    kand = vorschlaege_person(person, nur_eids=eids, schreiben=False, norm_latte=norm_latte, emb=emb,
                              diagnose=diagnose)
    # .32x DECKEL JE EVENT (User-Fund 22.08. am Overlay: "sieht aus als wenn es
    # 5 mal die gleichen Gesichter sind"). Nachgemessen an den zuletzt
    # uebernommenen Referenzen: vier von sechs kamen aus EINEM Event, aus den
    # Frames 30/45/50/55 — bei 3 fps also die Sekunden 10 bis 18 derselben
    # Aufnahme, gleiche Pose, gleicher Hintergrund. Weder das Dedup (0,97) noch
    # die Zwillings-Erkennung des Vorrats (0,95) fassen das an: die Embeddings
    # liegen bei 0,75-0,85 auseinander, das Auge sieht keinen Unterschied.
    # Fuer den Lernvorrat zaehlt aber Vielfalt, nicht Menge — fuenf Bilder einer
    # Sekunde bringen weniger als fuenf Blickwinkel.
    # Deshalb: je Event hoechstens BRUECKE_JE_EVENT Bilder, die BESTEN zuerst
    # (vorschlaege_person liefert bereits nach Guete sortiert). Der Rest der
    # Auswahl fuellt sich aus den anderen Events des Durchgangs. Kein Bild geht
    # verloren — was der Deckel abschneidet, bleibt Grenzfall und damit im
    # Overlay sichtbar, nur ohne Haken.
    _je_event = {}
    nehmen, ueberzaehlig = [], []
    for k in kand:
        if k.get("stufe") != "empfohlen":
            continue
        e = str(k.get("eid"))
        _je_event[e] = _je_event.get(e, 0) + 1
        (nehmen if _je_event[e] <= BRUECKE_JE_EVENT else ueberzaehlig).append(
            {"eid": k["eid"], "datei": k["datei"]})
    # .231 (User-Go nach dem Pass-3-Befund: 8 sichere Identitaeten fielen
    # still an der Gut-Qualitaet): die Stufe 'neutral' wird nicht mehr
    # verschwiegen, sondern als GRENZFAELLE mitgegeben — das Overlay zeigt
    # sie OHNE Haken, der Nutzer entscheidet am Bild.
    grenz = [{"eid": k["eid"], "datei": k["datei"]}
             for k in kand if k.get("stufe") == "neutral"] + ueberzaehlig
    if diagnose is not None:
        diagnose["je_event_deckel"] = BRUECKE_JE_EVENT
        diagnose["ueberzaehlig"] = len(ueberzaehlig)
    return nehmen, grenz


BRUECKE_JE_EVENT = 2   # .32x: wie viele Bilder die Pass-Pruefung je EVENT
#                        vorschlaegt. Zwei statt einem, weil ein zweites Bild
#                        derselben Szene durchaus einen anderen Winkel zeigen
#                        kann; alles darueber ist gemessen dieselbe Sekunde.
#                        Was der Deckel abschneidet, wird Grenzfall (sichtbar,
#                        ohne Haken) — nie stiller Verlust.
SICHTUNG_JE_BLICK = 14   # .271: Pruef-Kandidaten je Blickwinkel-Reihe
SICHTUNG_WAHL = "blick-rr-ernte-struktur-luma-guete"  # Cache-Kennung der Sichtung.
                                   # Alt-Tags ('blick-rr-norm2' = Crop-Nachmessung bis .313,
                                   # 'blick-rr-ernte' = ohne Gruppen-Konsens,
                                   # 'blick-rr-ernte-struktur' = ohne Belichtung,
                                   # 'blick-rr-ernte-struktur-luma' = ohne Bildguete) -> neu sichten.
                                   # Der Bump gehoert zu JEDER Aenderung am bilder-Dict:
                                   # sonst liefert der Cache eines bestehenden Laufs Bilder
                                   # OHNE das neue Feld, und die neue Achse bliebe dort
                                   # dauerhaft blind (bauplan_belichtung.md E5, Befund 7).
SICHTUNG_DECKEL = 40   # (Alt-Kommentar) Pruef-Kandidaten je Gruppe;
#                        haelt die Erst-Sichtung mit warmem Modell bei wenigen
#                        Sekunden — die Flaeche zeigt ohnehin maximal zwei
#                        Reihen, der Rest waere Messung ohne Abnehmer.


BLICK_REIHEN = ("links", "frontal", "rechts")


def _ueber_qualitaetslinie(x, norm_latte):
    """.314b (User-Auflage 21.08.): besteht dieses Mitglied die Qualitaetslinie?
    Mit gemessener Feature-Norm entscheidet die virtuelle Linie (norm_latte:
    Norm ueber `min`, dazu die Boeden kante/sharp) — das ist die Achse, die der
    User meint. Ohne Norm (Alt-Anker, Laeufe vor der Vorrats-Einfuehrung) tritt
    die Pixel-Latte an ihre Stelle, damit die Frage ueberhaupt beantwortbar
    bleibt; eine Norm-Nachmessung nur zum Sortieren waere hier zu teuer (sie
    laeuft spaeter in gruppen_sichtung fuer die Bilder, bei denen sie das
    Urteil noch drehen kann)."""
    nl = norm_latte or {}
    n, k, sh = x.get("norm"), x.get("kante") or 0, x.get("sharp") or 0
    if nl.get("min") is not None and n is not None:
        return (n >= nl["min"] and k >= (nl.get("kante") or 0)
                and sh >= (nl.get("sharp") or 0))
    return k >= REF_LATTE["min_kante"] and sh >= REF_LATTE["unscharf_max"]


def _norm_lohnt(kante, sharp, norm_latte):
    """.314b: lohnt eine Norm-Nachmessung fuer dieses Mitglied? Nur wenn (a) der
    Norm-Weg ueberhaupt aktiv ist, (b) das Bild seine Boeden erfuellt und (c) es
    an der PIXEL-Latte scheitern wuerde — nur dann kann die Norm das Urteil noch
    drehen. Ohne diese drei Bedingungen waere die Messung reine Arbeit."""
    nl = norm_latte or {}
    if nl.get("min") is None or kante is None or sharp is None:
        return False
    if kante < (nl.get("kante") or 0) or sharp < (nl.get("sharp") or 0):
        return False
    return kante < REF_LATTE["min_kante"] or sharp < REF_LATTE["unscharf_max"]


def _norm_nachmessen(lauf_dir, rel, emb=None):
    """.314b: NUR die Feature-Norm eines Crops nachmessen (Detektion + Alignment
    wie bild_metriken, gleiche Skala wie die Ernte-Norm — gemessen Median 0,12
    Versatz). None, wenn die Detektion auf dem randlosen Crop scheitert (56 %
    der Faelle) oder die Datei fehlt: dann urteilt die Pixel-Latte."""
    try:
        img = cv2.imread(os.path.join(lauf_dir, rel))
        if img is None:
            return None
        e = emb or _embedder_geteilt()
        return bild_metriken(e, img, mit_norm=True)[3]
    except Exception:
        return None                       # Zusatz-Auskunft, nie Blocker


def _sichtungs_kandidaten(mitglieder, deckel_je_blick, yaw_grenze, norm_latte=None,
                          luma_grenzen=None, guete_latte=None):
    """.271 (User-Zielbild: 'eine Reihe links, eine frontal, eine rechts —
    und das sind schon die optimalen'): Kandidaten-Wahl JE BLICKWINKEL-BIN
    (perspektiv_bin) und darin JE EVENT verteilt (Round-Robin, innerhalb
    des Events nach _reihung; latten-taugliche Frames zuerst, Unter-Latte
    fuellt nur nach — Lehren aus .269/.270: Top-N am Stueck = Serien-Frames,
    reines Event-RR = schwache Events fressen Plaetze).
    .314b: der Deckel begrenzt nur noch die VORDEREN Plaetze je Bin; dahinter
    folgen die uebrigen Mitglieder, die die QUALITAETSLINIE bestehen (User
    21.08.: "aber nur wenn sie ueber der Normierung sind") — vorher fielen sie
    ersatzlos aus der Sichtung, im Lauf L20260821_154851 waren das 79 von 121
    Bildern EINER Gruppe. -> Liste von (mitglied, blick)."""
    from core.benennung import _reihung, _lattenklasse, perspektiv_bin
    import functools
    # .308: Reihung UND Tauglichkeits-Schnitt kennen den Norm-Weg (norm_latte
    # aus der Dienst-Config; None = Pixel-Latte allein wie bisher).
    # bauplan_belichtung.md E4: dieselbe Reihung traegt seit 26.08. die
    # Belichtungsklasse — gut belichtete Bilder stehen VORNE in den drei
    # Blickwinkel-Reihen. Der Tauglichkeits-Schnitt (_lk) bleibt unberuehrt:
    # Belichtung entscheidet ueber die REIHENFOLGE, nie ueber die Menge.
    _rk = functools.partial(_reihung, norm_latte=norm_latte,
                            luma_grenzen=luma_grenzen, guete_latte=guete_latte)
    # .377: derselbe Guete-Weg im Tauglichkeits-Schnitt — Zeilen ohne die
    # Guete-Felder (Alt-Laeufe) urteilen unveraendert nach der Pixel-Latte.
    _lk = functools.partial(_lattenklasse, norm_latte=norm_latte,
                            guete_latte=guete_latte)
    kand = []
    for blick in BLICK_REIHEN:
        im_bin = [x for x in sorted(mitglieder, key=_rk)
                  if perspektiv_bin(x.get("pose") or [], yaw_grenze) == blick]
        je_event = {}
        for x in im_bin:
            je_event.setdefault(str(x.get("event", "")), []).append(x)
        n0 = len(kand)
        for nur_tauglich in (True, False):
            reihen = [[x for x in r
                       if (_lk(x) <= 1) == nur_tauglich]
                      for r in je_event.values()]
            while len(kand) - n0 < int(deckel_je_blick) and any(reihen):
                for r in reihen:
                    if r:
                        kand.append((r.pop(0), blick))
                        if len(kand) - n0 >= int(deckel_je_blick):
                            break
            if len(kand) - n0 >= int(deckel_je_blick):
                break
    # .314b (User 21.08.: "bei einem Lauf immer die Bilder sehen"; Widerleger
    # HOCH): der Deckel entschied bis hier, welche Bilder es ueberhaupt auf die
    # Seite schaffen — im Lauf L20260821_154851 erschienen 79 von 121 Bildern
    # einer Gruppe NIRGENDS, auch nicht im "show all"-Aufklapper. Der Deckel war
    # ein KOSTEN-Deckel fuer die Crop-Nachmessung; seit die Sichtung die
    # Ernte-Messung nimmt (.314), kostet ein weiteres Mitglied weder Bild-I/O
    # noch Modell. Also: die uebrigen Mitglieder kommen HINTEN dran (Reihung
    # unveraendert), die Flaeche zeigt sie im Rest. Der Deckel bestimmt jetzt
    # nur noch, was VORNE in den drei Blickwinkel-Reihen landet.
    drin = {id(x) for x, _b in kand}
    for blick in BLICK_REIHEN:
        for x in sorted(mitglieder, key=_rk):
            if id(x) in drin:
                continue
            if perspektiv_bin(x.get("pose") or [], yaw_grenze) != blick:
                continue
            # User-Auflage 21.08. ("aber nur wenn sie ueber der Normierung
            # sind"): der Nachzug ist kein Alles-Zeigen — er holt genau die
            # Bilder dazu, die die QUALITAETSLINIE bestehen. Was darunter
            # liegt, bleibt wie bisher aus der Sichtung heraus.
            if not _ueber_qualitaetslinie(x, norm_latte):
                continue
            kand.append((x, blick))
            drin.add(id(x))
    return kand


def gruppen_sichtung(satz, lauf_dir, emb=None,
                     deckel_je_blick=SICHTUNG_JE_BLICK, yaw_grenze=15.0,
                     norm_latte=None, luma_grenzen=None, guete_latte=None):
    """.266 'Sicht = Pruefergebnis' (User 18.08.: 'erst ein Schnellcheck,
    welche Bilder wirklich gut sind, und DAVON die Anzeige'): die besten
    `deckel` Mitglieder der Gruppe (Reihung `_reihung`) werden gesichtet
    und das Ergebnis samt Embedding im Lauf-Ordner gecacht
    (`sichtung_<anker>.json`, modell-gebunden, faellt mit dem Lauf;
    Neuaufbau wenn sich die Mitglieder-Zahl aendert). Flaeche UND
    Benenn-Pruefung zehren daraus — EINE Messung je Bild, nie zwei Massstaebe.
    .313b (User 21.08.: 'bei einem Lauf immer die Bilder sehen'): die EINE
    Messung ist die ERNTE-Messung des Mitglieds (emb/kante/sharp/norm aus der
    Vollbild-Detektion, im Anker-Satz hinterlegt) — nicht mehr eine zweite
    Detektion auf dem eng geschnittenen Crop. Gemessen (Lauf L20260821_210230,
    A/B .312 = .313): die Crop-Nachmessung fand in 11 von 13 Crops (61–98 px,
    randlos) KEIN Gesicht, obwohl die Ernte dieselben Gesichter im 4K-Bild mit
    det 0,72–0,87 hatte; ueber den Tag fielen so 30–60 % der Sichtungsbilder
    als 'no measurable face' aus der Flaeche (bekannte Klasse: anlernen.py
    lade_master_refs, 'kleine Crops sind fuer die Datei-Detektion gemessen
    tot, 28/40' — fuer Vorrats-Referenzen per A2-Beiwert geloest, hier nie).
    Die Crop-Nachmessung (`bild_metriken`, det 320) bleibt NUR als Fallback
    fuer Alt-Mitglieder ohne Ernte-Embedding; der Embedder wird erst dann
    gebaut. kante bleibt Original-Pixel, sharp die Laplace-Varianz des Crops,
    norm die Feature-Norm derselben Detektion — dieselben Skalen wie zuvor.
    -> {"modell", "gesamt", "bilder": [{datei, kante, sharp, norm, luma,
    fiqa_t, empf, emb|None, grund?}...]} in Reihungs-Ordnung.
    luma (bauplan_belichtung.md E5): DRITTER Kopierschritt der Ernte-Messung
    (Kandidatenzeile -> Anker-Mitglied -> hier). Ohne ihn saehe
    sichtung_bewerten die Belichtung nie, weil sie ausschliesslich aus DIESEM
    Cache rechnet."""
    from core.benennung import _reihung
    aid = str(satz.get("anker_id"))
    pfad = os.path.join(lauf_dir, f"sichtung_{aid}.json")
    m = satz.get("mitglieder") or []
    # Modell-Bindung ohne Embedder-Aufbau: Ernte-Mitglieder tragen 'modell';
    # sonst der uebergebene Embedder, sonst das konfigurierte Modell.
    modell = str(emb.modell if emb is not None else
                 next((x.get("modell") for x in m if x.get("modell")), None)
                 or aktuelles_modell()).lower()
    try:
        with open(pfad, encoding="utf-8") as f:
            d = json.load(f)
        if (d.get("modell") == modell and d.get("gesamt") == len(m)
                and d.get("wahl") == SICHTUNG_WAHL):   # .313b: Alt-Caches (Crop-Nachmessung) -> neu
            return d
    except (OSError, ValueError):
        pass
    bilder = []
    for x, blick in _sichtungs_kandidaten(m, deckel_je_blick, yaw_grenze,
                                          norm_latte=norm_latte,
                                          luma_grenzen=luma_grenzen,
                                          guete_latte=guete_latte):
        rel = str(x.get("datei", ""))
        v = x.get("emb")
        if v is not None and str(x.get("modell") or modell).lower() == modell:
            # Ernte-Messung (Vollbild-Detektion) = DIE eine Messung.
            _k, _s = x.get("kante"), float(x.get("sharp") or 0.0)
            _n = x.get("norm")
            if _n is None and _norm_lohnt(_k, _s, norm_latte):
                # .314b (Widerleger-Blocker): die Ernte schreibt die Norm NUR
                # fuer Vorrats-Kandidaten (core/ernte gate_v_vor) und in Laeufen
                # vor .308 gar nicht — ein Anker-Mitglied ohne Norm haette den
                # .307/.308-Norm-Weg still verloren und waere an der Pixel-Latte
                # gescheitert, obwohl die Crop-Messung bis .313 eine Norm lieferte
                # (gemessen: 78 von 833 Kandidaten der offenen Anker betroffen).
                # Deshalb NUR die Norm nachmessen — emb/kante/sharp bleiben die
                # Ernte-Werte, es gibt weiterhin genau EINE Identitaets-/
                # Qualitaetsquelle. Skalen-Beleg (150 Proben mit bekannter
                # Ernte-Norm): diese Nachmessung liegt im Median 0,12 daneben,
                # 1 Kipper an der 22,0-Linie von 66; sie gelingt aber nur in 44 %
                # (Detektion auf dem randlosen Crop) — sonst bleibt norm None und
                # die Pixel-Latte urteilt wie in .313 auch. Ein Resize-Weg OHNE
                # Detektion waere immer verfuegbar, kippt aber 25 % (kein
                # Alignment) und ist deshalb bewusst NICHT genommen.
                emb = emb or _embedder_geteilt()   # erst JETZT, nie fuer den Normalfall
                _n = _norm_nachmessen(lauf_dir, rel, emb)
            bilder.append({"datei": rel, "blick": blick,
                           "kante": _k, "sharp": _s, "norm": _n,
                           # .32x: die Struktur kommt aus der Ernte mit (core/anker
                           # kopiert sie ins Mitglied). Fehlt sie — Alt-Anker vor
                           # dem Struktur-Test —, bleibt sie None und die Anzeige
                           # filtert nicht darauf: ein Urteil ohne Messgrundlage
                           # waere ein stiller Verlust.
                           "struktur": x.get("struktur"),
                           # bauplan_belichtung.md E5: die Luma kommt aus der
                           # Ernte mit (core/anker kopiert sie ins Mitglied).
                           # Fehlt sie — Alt-Anker vor dem Einbau —, bleibt sie
                           # None und die Belichtungsachse urteilt NICHT.
                           "luma": x.get("luma"),
                           # .377: VIERTER Kopierschritt derselben Kette
                           # (Kandidatenzeile -> Anker-Mitglied -> hier) fuer
                           # die zwei Guete-Masse. Ohne ihn urteilte
                           # sichtung_bewerten weiter nach der abgeloesten
                           # Laplacian-Schaerfe, waehrend das Sieb der
                           # Gruppenbildung schon nach der Guete siebt — die
                           # Bewertung rechnet ausschliesslich aus DIESEM
                           # Cache. Fehlen sie (Alt-Anker, Alt-Images ohne die
                           # Modelle), bleiben sie None und die Guete-Achse
                           # urteilt NICHT.
                           "fiqa_t": x.get("fiqa_t"), "empf": x.get("empf"),
                           "emb": [round(float(t), 5) for t in v],
                           "quelle": "ernte" if x.get("norm") is not None
                                     else ("ernte+norm" if _n is not None else "ernte")})
            continue
        # Fallback (Alt-Mitglied ohne Ernte-Embedding): Crop-Nachmessung wie bis .313.
        img = cv2.imread(os.path.join(lauf_dir, rel))
        if img is None:
            bilder.append({"datei": rel, "blick": blick, "kante": None,
                           "sharp": 0.0, "emb": None,
                           "grund": "crop not readable"})
            continue
        emb = emb or _embedder_geteilt()
        v, kante, sh, norm = bild_metriken(emb, img, mit_norm=True)
        bilder.append({"datei": rel, "blick": blick, "kante": kante,
                       "sharp": sh, "norm": norm, "struktur": None,
                       # Auch der Alt-Weg traegt die Luma, falls das Mitglied
                       # sie hat (die Crop-Nachmessung misst sie NICHT nach —
                       # ohne Wert bleibt die Belichtungsachse hier still).
                       "luma": x.get("luma"),
                       # dasselbe fuer die Guete-Masse: durchgereicht, wenn das
                       # Mitglied sie traegt, sonst None (die Crop-Nachmessung
                       # misst sie nicht nach — Alt-Weg bleibt Alt-Weg).
                       "fiqa_t": x.get("fiqa_t"), "empf": x.get("empf"),
                       "emb": ([round(float(t), 5) for t in v]
                               if v is not None else None),
                       "quelle": "crop"})
    d = {"modell": modell, "gesamt": len(m), "wahl": SICHTUNG_WAHL,
         "bilder": bilder,
         "ts": round(time.time(), 1)}
    fd, tmp = tempfile.mkstemp(dir=lauf_dir, prefix=".sichtung.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, pfad)
    os.chmod(pfad, 0o644)          # mkstemp-0600-Falle (Backup-Befund 17.08.)
    return d


def sichtung_lesen(satz, lauf_dir, modell):
    """Nur-Lese-Zugriff auf den Sichtungs-Cache (fuer den Seiten-Render,
    der weder Modell noch Embedder anfassen darf): None wenn kein gueltiger
    Cache liegt — dann zeigt die Flaeche den 'checking pictures'-Zustand
    und das JS stoesst die Sichtung an."""
    aid = str(satz.get("anker_id"))
    try:
        with open(os.path.join(lauf_dir, f"sichtung_{aid}.json"),
                  encoding="utf-8") as f:
            d = json.load(f)
        if (d.get("modell") == str(modell)
                and d.get("gesamt") == len(satz.get("mitglieder") or [])
                and d.get("wahl") == SICHTUNG_WAHL):   # .269: Alt-Cache = neu sichten
            return d
    except (OSError, ValueError):
        pass
    return None


def sichtung_hat_sichtbare(satz, lauf_dir, modell, refs, dup_sim,
                           norm_latte=None, luma_grenzen=None, guete_latte=None):
    """.318 (User 22.08.: "da brauchst du sie auch gar nicht erst als Gruppe
    angezeigt werden beim Aufrufen"): traegt diese Gruppe nach der Bewertung noch
    EIN Bild im Rahmen? Rein lesend — Sichtungs-Cache + Matrix, kein Modell, keine
    Bild-I/O; der Aufrufer sortiert damit leere Gruppen ans Ende, statt sie dem
    User als erstes vorzulegen.
    -> True/False, oder None wenn (noch) kein Cache liegt: dann ist es UNBEKANNT
    und der Aufrufer behandelt die Gruppe wie eine volle (nie wegen fehlender
    Messung nach hinten schieben).
    Die Gruppe wird dadurch NICHT verworfen und verliert nichts (.313-Regel) —
    sie steht weiter im Streifen und ueber ?g=<anker_id> direkt an."""
    si = sichtung_lesen(satz, lauf_dir, modell)
    if si is None:
        return None
    bew = sichtung_bewerten(satz.get("person") or None, si, refs, dup_sim, [],
                            norm_latte=norm_latte, luma_grenzen=luma_grenzen,
                            guete_latte=guete_latte)
    return any(b.get("stufe") != "raus" for b in bew)


def sichtung_bewerten(person, sichtung, refs, dup_sim, adoptierte,
                      norm_latte=None, luma_grenzen=None, guete_latte=None):
    """Matrix-Anwendung auf die GECACHTEN Sichtungs-Messwerte (.266): keine
    Bild-I/O, kein Modell — Identitaets-Achse gegen `refs` (Matrizen je
    Person; person=None oder ohne Referenzen -> Identitaet ist das
    User-Wort, nur Qualitaet traegt, wie bild_stufe eigen=None), Qualitaet
    aus kante/sharp der Sichtung, Dedup innerhalb der Reihung; Naehe zu
    adoptierten/Katalog-Referenzen wird seit .313b nur ANGESAGT, nie
    versteckt (die Doppel-Uebernahme faengt plan_bauen).
    norm_latte["veto"] (.316): gemessene Feature-Norm AUF ODER UNTER diesem Wert
    schliesst aus — die einzige Achse, die SCRFD-Fehldetektionen mit hohem
    det_score von echten Klein-Gesichtern trennt.
    norm_latte["struktur"] (.32x): gemessene Gesichts-STRUKTUR unter diesem Wert
    schliesst aus — der Ausschnitt zeigt kein Gesicht (Nacken, Ohr, Hinterkopf,
    Vegetation). Ersetzt den .316b-Gruppen-Konsens, der ersatzlos entfaellt.
    guete_latte {empfinden_min, t_min} (.377): traegt das Sichtungsbild beide
    Guete-Masse der Ernte, urteilt die vom Nutzer kalibrierte Latte ueber die
    Qualitaets-Achse statt der Laplacian-Schaerfe (bild_stufe, DIESELBE
    Staffelung wie core.benennung._lattenklasse in der Vorauswahl). Ohne die
    Masse oder ohne die Schwellen urteilt der Alt-Weg unveraendert.
    luma_grenzen {min, max} (bauplan_belichtung.md E5b, Issue 26): ein Bild
    ausserhalb der Belichtungsgrenzen wird GRENZFALL mit Grund — nie 'raus'
    (Nicht-Loeschen-Prinzip; bewusste Zuwahl bleibt moeglich). Die Achse kann
    also nur ZURUECKstufen, nie hochstufen und nie ausschliessen. Ohne Grenzen
    oder ohne gemessene Luma passiert nichts.
    -> Liste in
    Sichtungs-Ordnung: {datei, stufe 'gut'|'grenzfall'|'raus', grund}."""
    from core.uebernahme import _cos
    # EINE Quelle der Belichtungs-Einordnung (core.benennung) — die Worte
    # daraus bildet diese Funktion selbst (GRUND_TEXT), weil Wizard-Sichtung
    # und Anker-Detailseite verschiedene Vokabulare fuehren.
    from core.benennung import belichtungs_lage as _bn_belichtung
    from core.benennung import harte_linie as _bn_harte_linie
    eigen_refs = refs.get(person) if person else None
    if eigen_refs is not None and not len(eigen_refs):
        eigen_refs = None
    # .313b: `gesehen` startet LEER — Naehe zu adoptierten Referenzen ist
    # seither eine Ansage (schon_gelernt unten), kein Double 'zu einem hier
    # gezeigten Bild'; das Dedup innerhalb der Reihung bleibt.
    aus, gesehen = [], []
    for b in (sichtung or {}).get("bilder", []):
        datei = os.path.basename(str(b.get("datei", "")))
        if b.get("emb") is None:
            aus.append({"datei": datei, "stufe": "raus",
                        "grund": b.get("grund")
                        or "no measurable face in this crop",
                        "blick": b.get("blick") or "frontal"})
            continue
        v = np.asarray(b["emb"], dtype=np.float32)
        eigen = (float((eigen_refs @ v).max())
                 if eigen_refs is not None else None)
        fremd = (max((float((M @ v).max()) for p2, M in refs.items()
                      if p2 != person and len(M)), default=None)
                 if person else None)
        _nl = norm_latte or {}
        # .316 VETO DER QUALITAETSLINIE (User 22.08., nach dem Gras-Fund in
        # L20260821_230529-A1): eine gemessene Feature-Norm AUF ODER UNTER der Linie
        # schliesst das Bild aus — bis .315 qualifizierte die Norm nur ZUSAETZLICH
        # zur Pixel-Latte und konnte nie ausschliessen. Anlass: SCRFD hielt 19
        # Hecken-Ausschnitte fuer Gesichter (det 0,74-0,85, front bis 0,91), die
        # Pixel-Latte liess sie durch (73-89 px, scharf), und der Objekt-Filter
        # ist_fehldetektion greift dort per Konstruktion nicht (er sucht det NIEDRIG).
        # Die Norm sah es als Einzige: Median 20,5 gegen 22,1/23,6 der echten Gruppen.
        # GEMESSEN zur Wahl der Schwelle: <= 22,0 faengt 15 der 19 Gras-Bilder und
        # kostet in den echten Gruppen 3 von 13 bzw. 4 von 10; <= 23,0 faengt alle 19,
        # traefe aber 47 % der Norm-Werte der 348 bestaetigten Bestands-Referenzen
        # (Median 23,1) — deshalb 22,0 (User-Entscheid).
        # NUR mit gemessener Norm: fehlt sie (Alt-Anker vor der Vorrats-Einfuehrung,
        # Norm-Nachmessung gescheitert), urteilt die Pixel-Latte wie bisher — ein Veto
        # ohne Messgrundlage waere ein stiller Verlust.
        # .32x STRUKTUR-TEST (User-Entscheid 22.08.) — ERSTE Frage, vor allen
        # Qualitaets-Achsen: zeigt der Ausschnitt ueberhaupt ein Gesicht?
        # Er ersetzt den .316b-Gruppen-Konsens. Der urteilte ueber die GRUPPE und
        # bestrafte damit gute Bilder fuer ihre schlechten Nachbarn: gemessen kippte
        # er neun Gruppen, davon FUENF mit erkannter Person und fast durchweg
        # brauchbaren Bildern (bis 18/18 ueber der Struktur-Linie) — darunter der
        # Anlassfall: eine Gruppe mit erkannter Person, aus der der Lauf NULL
        # Bilder anbot.
        # Die beiden echten Fehlerkennungen leert der Struktur-Test vollstaendig
        # (0/7 und 0/19), er braucht die Gruppen-Regel also nicht.
        # OHNE gemessene Struktur wird NIE gefiltert (Alt-Mitglieder, gescheiterte
        # Messung) — ein Test ohne Messgrundlage waere ein stiller Verlust.
        # .367: die beiden harten Linien kommen aus core.benennung.harte_linie —
        # DIESELBE Funktion, die das Sieb der Gruppenbildung fragt. Vorher standen
        # sie nur hier, und Phase 1 baute deshalb Gruppen aus Material, das hier
        # komplett durchfiel. Die WORTE bleiben hier: die Wizard-Sichtung und die
        # Anker-Detailseite fuehren verschiedene Vokabulare.
        _hart = _bn_harte_linie(b, norm_latte)
        if _hart == "struktur":
            aus.append({"datei": datei, "stufe": "raus",
                        "grund": f"{GRUND_TEXT['keine_struktur']} "
                                 f"(structure {b['struktur']} — needs {_nl.get('struktur')}+)",
                        "blick": b.get("blick") or "frontal"})
            continue
        if _hart == "norm":
            aus.append({"datei": datei, "stufe": "raus",
                        "grund": f"{GRUND_TEXT['unter_linie']} "
                                 f"(face quality {b['norm']} — needs more than {_nl.get('veto')})",
                        "blick": b.get("blick") or "frontal"})
            continue
        # .377: die Guete-Masse des Sichtungsbildes UND die kalibrierten
        # Schwellen gehen mit in die EINE Bewertung — sonst siebt die
        # Gruppenbildung nach der Guete und die Flaeche verwirft nach der
        # Schaerfe (QS-Befund 30.08., .367-Fehlerklasse).
        _gl = guete_latte or {}
        stufe, grund = bild_stufe(eigen, fremd, b.get("kante"), b.get("sharp"),
                                  norm=b.get("norm"),
                                  norm_gut=_nl.get("gut"), norm_min=_nl.get("min"),
                                  norm_kante_min=_nl.get("kante"),
                                  norm_sharp_min=_nl.get("sharp"),
                                  fiqa_t=b.get("fiqa_t"), empf=b.get("empf"),
                                  guete_t_min=_gl.get("t_min"),
                                  guete_empfinden_min=_gl.get("empfinden_min"))
        # .313b (User 21.08.): 'gedeckt' (eigen >= sim_neu, Bestands-Duplikat)
        # ist fuer die Bruecke ein Nicht-Vorschlag, fuer die Gruppen-Flaeche
        # aber ein SICHTBARER Grenzfall — schon zugewiesene Bilder bleiben im
        # Rahmen (abgehakt, mit Grund), statt im zugeklappten Rest zu liegen.
        # bild_stufe selbst bleibt unveraendert (.257-Gate-Vektoren der Bruecke).
        gedeckt_sichtbar = False
        if stufe is None and grund == GRUND_TEXT["gedeckt"]:
            stufe, gedeckt_sichtbar = "neutral", True
        # .276 (User-Bauchgefuehl vs Messung, Werte-Tabelle 18.08.): Zahlen an die
        # Gate-Urteile — 'too small or too blurry' allein erklaert einem
        # scharfen 58-px-Gesicht nichts.
        if stufe is None and grund and grund.startswith("too small"):
            _n_txt = ""
            if _nl.get("min") is not None:
                _n_txt = (f", face quality "
                          f"{b.get('norm') if b.get('norm') is not None else '?'}"
                          f" — needs {_nl['min']}+")
            grund = (f"too small or too blurry for a reference "
                     f"({b.get('kante') if b.get('kante') is not None else '?'} px, "
                     f"sharpness {int(b.get('sharp') or 0)} — needs "
                     f"{REF_LATTE['min_kante']} px / {REF_LATTE['unscharf_max']}"
                     f"{_n_txt})")
        # .377: dieselbe Regel fuer den Guete-Weg — der Grund nennt die zwei
        # gemessenen Werte und die zwei kalibrierten Linien. Ohne die Zahlen
        # saehe der Nutzer nur "image quality too low" und wuesste nicht, an
        # welchem der beiden Regler er drehen muss.
        if stufe is None and grund == GRUND_TEXT["guete_zu_schwach"]:
            grund = (f"{GRUND_TEXT['guete_zu_schwach']} "
                     f"(quality {b.get('empf')} / recognisability "
                     f"{b.get('fiqa_t')} — needs {_gl.get('empfinden_min')} / "
                     f"{_gl.get('t_min')}; "
                     f"{b.get('kante') if b.get('kante') is not None else '?'} px "
                     f"— needs {REF_LATTE['min_kante']} px)")
        # .313b (User 21.08., 'bei einem Lauf immer die Bilder sehen, egal ob
        # ich die schon mal zugewiesen habe'): SCHON GELERNT versteckt nicht
        # mehr. Bis .313 nahm die .267-Regel ein Double einer adoptierten
        # Referenz aus der Flaeche ('raus'), und die .313-Katalog-Regel tat
        # dasselbe fuer Doubles zu IRGENDEINER Referenz — gemessen am
        # 15:48-Lauf verschwanden so 23 von 226 Bildern, genau die schon
        # zugewiesenen. Jetzt: Stufe bleibt das Qualitaets-/Identitaets-
        # Urteil, die Naehe wird nur als Grund ANGESAGT (Kachel bleibt im
        # Rahmen, angehakt wie ihre Stufe); die Doppel-Uebernahme faengt
        # weiterhin plan_bauen ab (Dedup gegen die Bestands-Embeddings).
        # Dup INNERHALB der Auswahl wird weiter GRENZFALL (.267) — sonst
        # verdraengt ein abgewaehltes Bild sein besseres Double endgueltig.
        schon_gelernt = None
        if stufe is not None and any(
                (s := _cos(v, e)) is not None and s >= float(dup_sim)
                for e in (adoptierte or [])):
            schon_gelernt = "already learned as a reference (near-identical)"
        elif stufe is not None and any(
                len(M) and float((M @ v).max()) >= float(dup_sim)
                for M in (refs or {}).values()):
            schon_gelernt = "already in the catalog (near-identical reference exists)"
        if schon_gelernt and grund != GRUND_TEXT["gedeckt"]:
            grund = f"{grund} — {schon_gelernt}" if grund else schon_gelernt
        if schon_gelernt and stufe == "empfohlen":
            # .314b (Widerleger, HOCH — die schlimmste Nebenwirkung von .314):
            # SICHTBAR heisst nicht VORGESCHLAGEN. Die Kacheln der Stufe 'gut'
            # sind in der Flaeche VORAUSGEWAEHLT (routes/lernwizard._kachel_s,
            # checked = stufe 'gut'); ein Bild, das beinahe-identisch zu einer
            # schon gelernten Referenz ist, wanderte damit per Ein-Klick-Take
            # in den Referenzordner — bei einer Gruppe, die auf einen NEUEN
            # Namen getauft wird, sogar das Gesicht einer ANDEREN Person
            # (gemessen an L20260821_154851-A2: 5 Mitglieder mit Kosinus
            # 0,942-0,975 zu den Referenzen einer anderen Person, und
            # plan_bauen dedupliziert nur gegen die Referenzen DIESER Person).
            # Also: Stufe auf 'neutral' deckeln — die Kachel bleibt im Rahmen
            # sichtbar und traegt ihren Grund, aber ohne Haken.
            stufe = "neutral"
        dup = False
        if stufe is not None and any(
                (s := _cos(v, e)) is not None and s >= float(dup_sim)
                for e in gesehen):
            # .268: Beinahe-Double INNERHALB der Auswahl — als ALTERNATIVE
            # markiert (dup=True); die Flaeche reiht sie ganz nach hinten,
            # damit Serien-Frames nicht die zwei Reihen fluten (User-
            # Screenshot 18.08.: 19 von 24 Kacheln waren Doubles).
            stufe, dup = "neutral", True
            grund = "near-identical alternative to a picture shown here"
        # BELICHTUNG (bauplan_belichtung.md E5b, Issue 26: die Empfehlung
        # waehlte sichtbar zu dunkle Bilder). ZULETZT, damit die Achse nur noch
        # zurueckstufen kann: aus 'gut' wird 'grenzfall' mit Grund, ein bereits
        # zurueckgestuftes Bild behaelt seine Stufe und bekommt den Grund dazu,
        # und ein 'raus'-Urteil der Qualitaets-/Identitaets-Achsen bleibt
        # unberuehrt. NIE 'raus' aus Belichtung allein — das Bild bleibt im
        # Rahmen und ist bewusst zuwaehlbar (Memory 'nicht loeschen,
        # Mehrdeutigkeit aufloesen'). Klassifiziert wird in core.benennung
        # (EINE Quelle fuer beide Oberflaechen), benannt wird hier.
        _lage = _bn_belichtung(b, luma_grenzen)
        if _lage is not None and stufe is not None:
            _lg = luma_grenzen or {}
            _bgr = (f"{GRUND_TEXT['zu_dunkel']} "
                    f"(brightness {b.get('luma')} — needs {_lg.get('min')}+)"
                    if _lage == "dunkel" else
                    f"{GRUND_TEXT['ueberbelichtet']} "
                    f"(brightness {b.get('luma')} — needs {_lg.get('max')} or less)")
            grund = f"{grund} — {_bgr}" if grund else _bgr
            if stufe == "empfohlen":
                stufe = "neutral"
        blick = b.get("blick") or "frontal"
        if stufe is None:
            aus.append({"datei": datei, "stufe": "raus", "grund": grund,
                        "blick": blick})
            continue
        if not gedeckt_sichtbar:
            # .314b (Widerleger): ein nur zur ANSICHT hochgestuftes 'gedecktes'
            # Bild darf kein Dedup-Saatkorn werden — sonst verdraengt es sein
            # noch ungelerntes Double in den Alternativ-Rang, obwohl es selbst
            # gar nicht uebernommen werden soll (bis .313 verliess es die
            # Schleife vor gesehen.append).
            gesehen.append(v.tolist())
        aus.append({"datei": datei,
                    "stufe": "gut" if stufe == "empfohlen" else "grenzfall",
                    "grund": grund, "blick": blick,
                    **({"dup": True} if dup else {})})
    return aus


def benennung_bewerten(person, satz, dup_sim, adoptierte, lauf_dir, emb=None,
                       norm_latte=None, luma_grenzen=None, guete_latte=None):
    """.257/.266: DIESELBE Pruefung wie die Lern-Bruecke, identisch by
    construction (User-Auflage 17.08.: nie zwei verschiedene Pruefungen fuer
    dasselbe Bild). Seit .266 zehrt sie aus dem Sichtungs-Cache
    (gruppen_sichtung = die EINE Messung je Bild; seit .313b ist das die
    ERNTE-Messung des Mitglieds aus der Vollbild-Detektion — die fruehere
    Crop-Nachmessung mit det 320 fand auf randlosen 61–98-px-Crops meist
    kein Gesicht; dieselbe Messung traegt die Uebernahme als A2-Beiwert in
    refs_meta, damit Bestands-QS und refcache nie die Datei messen)
    und wendet nur noch die Matrix an (sichtung_bewerten:
    bild_stufe + Uebernahme-Dedup). Beurteilt werden die GEWAEHLTEN
    Mitglieder; Gewaehlte ausserhalb der Sichtungs-Kandidaten (Deckel)
    fallen EHRLICH mit Grund. Kein Schrieb ausser dem Sichtungs-Cache.
    -> Liste {datei, stufe 'gut'|'grenzfall'|'raus', grund}."""
    emb = emb or _embedder_geteilt()
    refs = refs_matrix(emb)
    if not len(refs.get(person, [])) and os.path.isdir(os.path.join(MASTER, person)):
        refs = lade_master_refs(emb)               # Cache kennt die Person noch nicht
    sicht = gruppen_sichtung(satz, lauf_dir, emb=emb, norm_latte=norm_latte,
                             guete_latte=guete_latte,
                             luma_grenzen=luma_grenzen)
    # .267 (Widerleger-Blocker): beurteilt werden ALLE Sichtungs-Kandidaten —
    # exakt die Menge, aus der die Flaeche rendert. Die frueher persistierte
    # gewaehlt-Auswahl ist fuer die Pruefung bedeutungslos (sie wird beim
    # Take ohnehin mit der SICHTBAREN Auswahl neu geschrieben); sie zu
    # filtern liess Pruefung und Anzeige wieder auseinanderlaufen.
    # .377: guete_latte MIT durchreichen — diese Pruefung ist die LETZTE Instanz
    # vor der Uebernahme. Ohne sie urteilte sie als einzige Stelle noch nach der
    # abgeloesten Schaerfe, waehrend Sichtung und Anzeige daneben schon die
    # kalibrierte Latte nahmen (QS-Befund 30.08.: 'nie zwei verschiedene
    # Pruefungen fuer dasselbe Bild', User-Auflage 17.08.).
    return sichtung_bewerten(person, sicht, refs, dup_sim, adoptierte,
                             norm_latte=norm_latte, luma_grenzen=luma_grenzen,
                             guete_latte=guete_latte)


def lernbruecke_uebernehmen(person, items, emb=None):
    """Lern-Bruecke Schritt 2: genau die geprueften Bilder uebernehmen (der
    Nutzer hat sie gesehen und bestaetigt). Containment/Format prueft
    vorschlag_aufnehmen. -> Ziel-Dateinamen (fuers Undo via
    entferne_referenz)."""
    dateien = []
    for it in (items or [])[:50]:
        ok, ziel = vorschlag_aufnehmen(person, str(it.get("eid") or ""),
                                       str(it.get("datei") or ""), emb=emb)
        if ok:
            dateien.append(ziel)
    return dateien


# ---------------------------------------------------------------- CLI
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("sammle"); s.add_argument("--tage", type=float, default=5.0)
    s.add_argument("--kein-migriere", action="store_true")   # szenario-getriggert: nur sammeln, keine Pool-Neupruefung
    sub.add_parser("reorganisieren")                         # Button/Wartung: migriere + reconcile (kein neues Sammeln)
    sub.add_parser("fd-nachpruefung")                        # #42 Teil B: Alt-Pool einmalig gegen die Fehldetektions-Signatur
    orp = sub.add_parser("objekt_reparatur")                 # Baustein C 12.08.: verschluckte Besucher-Crops
    orp.add_argument("--uid", default=None)                  #   aus Objekt-Clustern herausloesen (nur juenger als Anker)
    orp.add_argument("--seit", default=None,
                     help="Zeitanker der Objekt-Einstufung (epoch oder YYYY-MM-DD[THH:MM]); "
                          "ohne Angabe zaehlt das gespeicherte objekt_seit")
    np_ = sub.add_parser("nachpruefen")                      # Issue #19: Events nach dem Anlernen
    np_.add_argument("person"); np_.add_argument("faces_json")
    c = sub.add_parser("cluster"); c.add_argument("--sim", type=float, default=SIM_DEFAULT)
    pr = sub.add_parser("pruefe"); pr.add_argument("--sim", type=float, default=0.30)
    pr.add_argument("--unscharf", type=int, default=REF_LATTE["unscharf_max"])
    pr.add_argument("--minkante", type=int, default=REF_LATTE["min_kante"])
    pr.add_argument("--person", default=None)      # .273: Bericht-Filter
    pr.add_argument("--dupsim", type=float, default=0.75)
    # .308 Norm-Weg (Vorrat aktiv): Werte aus der Dienst-Config, None = aus
    pr.add_argument("--norm-gut", type=float, default=None)
    pr.add_argument("--norm-min", type=float, default=None)
    pr.add_argument("--norm-kante", type=int, default=None)
    pr.add_argument("--norm-sharp", type=int, default=None)
    vo = sub.add_parser("vorschlaege"); vo.add_argument("person")
    vo.add_argument("--tage", type=float, default=7.0)
    vo.add_argument("--unscharf", type=int, default=350)
    vo.add_argument("--minkante", type=int, default=70)
    vo.add_argument("--norm-gut", type=float, default=None)    # .308 Norm-Weg
    vo.add_argument("--norm-min", type=float, default=None)
    vo.add_argument("--norm-kante", type=int, default=None)
    vo.add_argument("--norm-sharp", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "sammle":
        # Ring-Deckel im CLI-/Subprozess-Weg via Env (verifyd setzt ihn im
        # Fallback-Aufruf mit) — ohne den Wert sammelt die CLI wie bisher.
        sammle(a.tage, mit_migriere=not a.kein_migriere,
               kalib_deckel=int(os.environ.get("VERIFY_KALIB_DECKEL") or 0) or None)
    elif a.cmd == "reorganisieren":
        reorganisieren()
    elif a.cmd == "fd-nachpruefung":
        fd_nachpruefung()
    elif a.cmd == "objekt_reparatur":
        seit = None
        if a.seit is not None:
            try:
                seit = float(a.seit)
            except ValueError:
                import datetime as _dt
                for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                    try:
                        seit = _dt.datetime.strptime(a.seit, fmt).timestamp()
                        break
                    except ValueError:
                        pass
                if seit is None:
                    sys.exit(f"--seit '{a.seit}' not parseable (epoch or YYYY-MM-DD[THH:MM])")
        objekt_reparatur(uid=a.uid, seit=seit)
    elif a.cmd == "nachpruefen":
        # Ergebnis in DATEI statt stdout: insightface druckt beim Modell-Laden auf stdout,
        # der Aufrufer (verifyd.anlern_nachpruefung_starten) braucht einen sauberen Kanal.
        faces = json.load(open(a.faces_json))
        erg = nachpruefe_events(a.person, faces)
        _schreibe_json_atomar(a.faces_json + ".ergebnis",
                              {"schwelle": UNBEKANNT_MAX, "events": erg})
        for eid, e in sorted(erg.items()):
            print(f"  {eid}: sim={e['sim']} {'CONFIRMED' if e['bestaetigt'] else 'not confirmed'}",
                  flush=True)
    elif a.cmd == "cluster":
        cl = clustere(sim=a.sim)
        print(f"\n{len(cl)} groups (sim>={a.sim}):")
        for k, c in enumerate(cl):
            rep = c[0]
            print(f"  group {k}: {len(c)} face(s) | representative {rep['id']} "
                  f"({rep['camera']}, nearest known: {rep['nn_person']} {rep['nn_score']}) | "
                  f"cameras: {sorted(set(g['camera'] for g in c))}")
    elif a.cmd == "pruefe":
        # .273 Bestands-QS: Fortschritt fuer die Seite (refs_qs_lauf.json —
        # existiert nur waehrend des Laufs bzw. nach einem Fehlschlag mit
        # 'fehler'; Erfolg raeumt sie weg).
        _lp = os.path.join(ANLERN, "refs_qs_lauf.json")
        os.makedirs(ANLERN, exist_ok=True)

        def _fs(i, n):
            if i == 1 or i % 5 == 0 or i == n:
                _schreibe_json_atomar(_lp, {"i": i, "n": n,
                                            "ts": round(time.time(), 1),
                                            "person": a.person})
        try:
            _nl_cli = ({"gut": a.norm_gut, "min": a.norm_min,
                        "kante": a.norm_kante, "sharp": a.norm_sharp}
                       if a.norm_min is not None else None)
            erg = pruefe_referenzen(a.sim, unscharf_max=a.unscharf,
                                    min_kante=a.minkante, person=a.person,
                                    dup_sim=a.dupsim, fortschritt=_fs,
                                    norm_latte=_nl_cli)
            try:
                os.unlink(_lp)
            except FileNotFoundError:
                pass
        except Exception as e:
            _schreibe_json_atomar(_lp, {"fehler": f"{type(e).__name__}: {e}",
                                        "ts": round(time.time(), 1)})
            raise
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
                                  unscharf_max=a.unscharf,
                                  norm_latte=({"gut": a.norm_gut, "min": a.norm_min,
                                               "kante": a.norm_kante, "sharp": a.norm_sharp}
                                              if a.norm_min is not None else None))
        print(f"\n{len(kand)} reference suggestions for {a.person}:")
        for k in kand:
            print(f"  sim={k['sim']} fremd={k['fremd']} kante={k['kante']} sharp={k['sharp']:.0f} "
                  f"{k['camera']} {k['eid']}")
    else:
        ap.print_help()
