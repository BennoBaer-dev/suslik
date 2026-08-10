"""core/personlive — PE4: Live-Urteil des Koerper-Strangs (stufe2.md).

.148 (User 07.08.: 'wir holen die Bilder selbst — kein Mischmasch'):
das Live-Urteil nutzt DIESELBE Kette wie das Training — Clip laden,
3 fps abtasten, Pfad-gestuetzte Bestbild-Wahl (pfad_snapshots), Pose-
Zuschnitt wie die Ernte. Damit ist der Train/Serve-Unterschied der
.114-.147-Zeit (Training auf Clip-Frames, Urteil auf Snapshot-WebP)
geschlossen. Der Frigate-Snapshot bleibt NUR (a) Uhr-Anker INNERHALB
der Kette und (b) markierter NOTNAGEL (quelle='snapshot'), wenn kein
Clip abrufbar ist — Abdeckung vor Reinheit, sichtbar im Treffer-Buch.
Kette: eigene Frames -> Personen-Crop -> DINOv2-ONNX -> SVM-proba.

FEUER-REGEL (User-Anforderung): gemeldet wird erst, wenn im Fenster
mindestens feuer_ab Events derselben Person ueber der Schwelle lagen;
danach Karenz je Person. Fenster/Stuetzen/Karenz kommen seit .114 aus
dem Modell-Status (Model-status-Seite), die Konstanten hier sind nur
die Standardwerte. Zustand geflusht in personlern/live_fenster.json.

SCHWELLE: seit .114 nach jedem Training per Kreuzvalidierung GEMESSEN;
seit .139 gegen ECHTE Fremde, sobald der Fremd-Pool
(<data_dir>/personlern/fremd/) gefuellt ist — sonst weiter nur zwischen
den gelernten Personen. Vorrang user > eichung > standard;
SCHWELLE_STD=0.85 ist nur der letzte Fallback. Der Strang laeuft nur,
wenn der User ihn auf /person/modell scharf geschaltet hat.

FREMD-KLASSE (.139): traegt svm.pkl eine Fremd-Klasse, wird ein Crop mit
top-1=FREMD gar nicht erst zum Treffer — m["personen"] bleibt die reine
Personenliste, FREMD taucht nie in Meldungen oder Today auf."""
import io
import json
import os
import re
import shutil
import time
import urllib.request

import numpy as np

FENSTER_S = 600
FEUER_AB = 2
KARENZ_S = 900
SCHWELLE_STD = 0.85
RAND = 0.08                 # wie szenario_ernte.crop_holen (Framing!)

# DIE Aufbewahrungsfrist dieser Bildklasse (Treffer-Crops UND Kontroll-Bilder,
# s. kontrolle_raeumen): eine Zahl, eine Regel. Frueher stand die 30 als
# Literal nur im Buch-Trim; Z8 legt eine zweite Bildsorte in dieselbe Klasse
# und haette sonst eine zweite Aufbewahrungsregel danebengestellt.
TRIM_TAGE = 30

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


def _treffer_log(data_dir):
    return os.path.join(data_dir, "personlern", "live_treffer.jsonl")


def treffer_buchen(data_dir, eintrag, kontrolle=None):
    """Treffer dauerhaft buchen (append, geflusht) — Today weist damit aus,
    WOHER eine Erkennung kam (face/person/beides). Trim: waechst die Datei
    ueber ~1 MB, fliegen Zeilen aelter TRIM_TAGE raus.

    kontrolle (Z8, optional): der Auftrag des Kontroll-Speichers. Sein Verfall
    haengt an DIESEM Trim (konzept_frames.md §Z8 woertlich: keine zweite
    Aufbewahrungsregel fuer dieselbe Bildklasse). None = kein Auftrag, dann
    wird am Kontroll-Speicher nichts angefasst."""
    p = _treffer_log(data_dir)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        if os.path.getsize(p) > 1_000_000:
            grenze = time.time() - TRIM_TAGE * 86400
            zeilen = []
            for z in open(p):
                try:
                    if (json.loads(z).get("ts") or 0) >= grenze:
                        zeilen.append(z)
                except ValueError:
                    pass
            tmp = p + ".tmp"
            with open(tmp, "w") as f:
                f.writelines(zeilen)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
            # verwaiste Treffer-Crops mit dem Buch-Trim raeumen
            bleiben = set()
            for z in zeilen:
                try:
                    e = json.loads(z).get("eid")
                    if e:
                        bleiben.add(str(e).replace("/", "_") + ".jpg")
                except ValueError:
                    pass
            tdir = os.path.join(data_dir, "personlern", "treffer")
            try:
                for fn in os.listdir(tdir):
                    if fn.endswith(".jpg") and fn not in bleiben:
                        os.remove(os.path.join(tdir, fn))
            except OSError:
                pass
            # Z8: der Kontroll-Speicher verfaellt im SELBEN Trim — dieselbe
            # Bildklasse, dieselbe Frist (TRIM_TAGE), dieselbe Waisen-Idee.
            kontrolle_raeumen(data_dir, kontrolle)
    except OSError:
        pass                       # Buchung ist Zusatznutzen, nie Urteils-Blocker


def treffer_karte(data_dir):
    """eid -> letzter Treffer {person, score, feuer} fuer die Today-Anzeige."""
    karte = {}
    try:
        for z in open(_treffer_log(data_dir)):
            try:
                d = json.loads(z)
                if d.get("eid"):
                    karte[d["eid"]] = d
            except ValueError:
                pass
    except OSError:
        pass
    return karte


# ------------------------------------------- Kontroll-Speicher (Z8, §7)
# konzept_frames.md §7 (User-Vorgabe 07.08., verbindlich) + §4/Z8: die BEURTEILTEN
# Bilder eines Durchgangs, mit Klasse, Score und quelle daneben — ZWEI
# Betriebsmodi ueber EINEN Schalter (Config `diagnostic_collection`):
#
#   SAMMEL  (true)   ALLE beurteilten Crops bleiben rollierend liegen und
#                    sind als Kachel-Seite anschaubar ("damit wir besser
#                    werden"). Verfall wie das Treffer-Buch: TRIM_TAGE.
#   SCHLANK (false)  Produkt-Default fuer fremde Installationen: die Bilder
#                    leben nur fuer die Laufzeit des Szenarios plus Karenz;
#                    danach bleiben nur Siegerbild (personlern/treffer/,
#                    unveraendert) und Urteils-Protokoll (urteile.jsonl).
#
# Abgelegt wird JE PASS, nie je Einzel-Event (Szenario-Prinzip, CLAUDE.md):
# <data_dir>/personlern/kontrolle/<pass_key>/. Den pass_key liefert der
# Aufrufer aus szenarien.pass_key — dieselbe Gruppierung wie /heute.
KONTROLLE_PROTOKOLL = "urteile.jsonl"
# V4 (konzept_vision.md §8): die Vision-Protokollzeile liegt NEBEN dem
# Kontroll-Protokoll desselben Passes und verfaellt ueber DENSELBEN Trim — kein
# zweites Aufbewahrungsregime. Beide Namen stehen hier zusammen, weil
# kontrolle_raeumen alles ohne Protokoll-Zeile als Waise loescht: ohne diese
# EINE Liste haette die Waisen-Raeumung die Vision-Zeilen mitgenommen (und ein
# zweites Literal in einem zweiten Modul waere die Streuklasse).
VISION_PROTOKOLL = "vision.jsonl"
PASS_PROTOKOLLE = (KONTROLLE_PROTOKOLL, VISION_PROTOKOLL)
_PASS_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z_.\-]{0,63}")


def kontrolle_dir(data_dir, pass_key=None):
    """<data_dir>/personlern/kontrolle[/<pass_key>]. Ein pass_key, der kein
    Ordnername sein darf (Pfadtrenner, '..', leer), gibt None — die Ablage
    faellt dann aus, statt irgendwohin zu schreiben."""
    w = os.path.join(data_dir, "personlern", "kontrolle")
    if pass_key is None:
        return w
    pk = str(pass_key)
    if not _PASS_RE.fullmatch(pk) or pk in (".", ".."):
        return None
    return os.path.join(w, pk)


def kontrolle_ablegen(data_dir, kontrolle, eid, crop, urteil):
    """EIN beurteiltes Bild in den Kontroll-Speicher legen. REINE ABLAGE, nie
    ein Urteil: kein Rueckgabewert von urteilen() haengt daran, und ein Fehler
    hier bleibt still (dieselbe Haltung wie die Treffer-Buchung).

    kontrolle=None -> es passiert NICHTS, es entsteht kein Ordner. Das ist der
    Rueckwaerts-Vertrag: ohne Auftrag verhaelt sich das Modul wie vor Z8.
    Rueckgabe: Pfad des abgelegten Bildes oder None."""
    if not kontrolle or crop is None:
        return None
    d = kontrolle_dir(data_dir, kontrolle.get("pass_key"))
    if d is None:
        return None
    datei = str(eid).replace("/", "_") + ".jpg"
    try:
        os.makedirs(d, exist_ok=True)
        crop.save(os.path.join(d, datei), "JPEG", quality=88)
        with open(os.path.join(d, KONTROLLE_PROTOKOLL), "a") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "eid": eid,
                                "datei": datei, **(urteil or {})},
                               ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except (OSError, ValueError, KeyError):
        return None
    # Raeumen gleich hier, weil erst HIER der laufende Pass bekannt ist: im
    # Schlank-Modus soll ein abgeschlossener Durchgang seine Bilder wieder
    # loswerden, ohne auf den 1-MB-Punkt des Treffer-Buchs zu warten. Es ist
    # dieselbe Funktion mit denselben Grenzen wie im Buch-Trim, keine zweite
    # Aufbewahrungsregel.
    kontrolle_raeumen(data_dir, kontrolle)
    return os.path.join(d, datei)


def kontrolle_raeumen(data_dir, kontrolle, jetzt=None):
    """DIE EINE Aufbewahrungsregel des Kontroll-Speichers (§7/Z8):

      * VERFALL   ein Pass-Ordner, dessen juengster Eintrag aelter als
                  TRIM_TAGE ist, faellt ganz weg — dieselbe Frist wie das
                  Treffer-Buch, aus dessen Trim diese Funktion mitgerufen wird.
      * WAISEN    ein Bild ohne Zeile im Urteils-Protokoll (abgerissene
                  Ablage) faellt weg — das Pendant zur Waisen-Raeumung der
                  Treffer-Crops im selben Trim.
      * SCHLANK   ist der Sammel-Modus aus, verlieren ABGESCHLOSSENE Paesse
                  (nicht der laufende, aelter als karenz_s) ihre Bilder;
                  Urteils-Protokoll und Siegerbild bleiben.

    kontrolle=None -> nichts anfassen (Rueckwaerts-Vertrag). Rueckgabe:
    {"passe": n, "bilder": n} als Abrechnung fuer Beweis und Log."""
    weg = {"passe": 0, "bilder": 0}
    if not kontrolle:
        return weg
    jetzt = time.time() if jetzt is None else jetzt
    sammeln = bool(kontrolle.get("sammeln"))
    aktiv = str(kontrolle.get("pass_key") or "")
    karenz = float(kontrolle.get("karenz_s") or 0)
    wurzel = kontrolle_dir(data_dir)
    try:
        ordner = sorted(os.listdir(wurzel))
    except OSError:
        return weg
    for pk in ordner:
        d = os.path.join(wurzel, pk)
        if not os.path.isdir(d):
            continue
        try:
            dateien = os.listdir(d)
        except OSError:
            continue
        gebucht, letzt = set(), 0.0
        try:
            for z in open(os.path.join(d, KONTROLLE_PROTOKOLL)):
                try:
                    e = json.loads(z)
                except ValueError:
                    continue
                if e.get("datei"):
                    gebucht.add(e["datei"])
                letzt = max(letzt, float(e.get("ts") or 0))
        except OSError:
            pass                   # Ordner ohne Protokoll: Alter aus den Dateien
        # Das abgelegte Kandidaten-Gitter des Vision-Laufs ist KEINE Waise: es
        # steht mit Namen in der Abschlusszeile des Vision-Protokolls
        # (`gitter_datei`, geschrieben von core.visionurteil.gitter_ablegen).
        # Gebucht wird genau dieses Feld — VERFALL und SCHLANK gelten
        # unveraendert weiter, es entsteht keine zweite Aufbewahrungsregel.
        try:
            for z in open(os.path.join(d, VISION_PROTOKOLL)):
                try:
                    e = json.loads(z)
                except ValueError:
                    continue
                if e.get("gitter_datei"):
                    gebucht.add(e["gitter_datei"])
        except OSError:
            pass
        for fn in dateien:
            try:
                letzt = max(letzt, os.path.getmtime(os.path.join(d, fn)))
            except OSError:
                pass
        if letzt and jetzt - letzt > TRIM_TAGE * 86400:
            shutil.rmtree(d, ignore_errors=True)
            weg["passe"] += 1
            continue
        # "Abgeschlossen" ist nicht "nicht der aktive": ein Pass ohne Auftrag
        # (Dienst-Neustart) darf nicht sofort ausgeraeumt werden, solange die
        # Karenz laeuft — dieselbe Karenz, die die Szenario-Gruppierung nutzt.
        fertig = pk != aktiv and (jetzt - letzt) > karenz
        for fn in dateien:
            if fn in PASS_PROTOKOLLE:
                continue
            if fn not in gebucht or (not sammeln and fertig):
                try:
                    os.remove(os.path.join(d, fn))
                    weg["bilder"] += 1
                except OSError:
                    pass
    return weg


def kontrolle_lesen(data_dir, max_passe=40):
    """Was der Kontroll-Speicher haelt — je Pass die Urteile mit Klasse,
    Score und quelle, neueste zuerst. Reine Lesefunktion fuer die Anzeige;
    `bild` sagt, ob das Bild noch da ist (im Schlank-Modus ist es nach dem
    Durchgang weg, das Protokoll bleibt)."""
    wurzel = kontrolle_dir(data_dir)
    try:
        ordner = sorted(os.listdir(wurzel), reverse=True)
    except OSError:
        return []
    passe = []
    for pk in ordner:
        d = os.path.join(wurzel, pk)
        if not os.path.isdir(d) or len(passe) >= max_passe:
            continue
        zeilen = []
        try:
            for z in open(os.path.join(d, KONTROLLE_PROTOKOLL)):
                try:
                    e = json.loads(z)
                except ValueError:
                    continue
                e["bild"] = bool(e.get("datei")) and os.path.isfile(
                    os.path.join(d, e["datei"]))
                zeilen.append(e)
        except OSError:
            continue
        if not zeilen:
            continue
        zeilen.sort(key=lambda e: e.get("ts") or 0)
        passe.append({"pass_key": pk,
                      "start": float(pk) if pk.isdigit() else 0.0,
                      "n": len(zeilen),
                      "bilder": sum(1 for e in zeilen if e["bild"]),
                      "zeilen": zeilen})
    return passe


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
        # Thread-Kappung wie bei JEDER eigenen ORT-Session (face_audit._ort_thread_opts):
        # ohne explizite intra_op_num_threads baut onnxruntime seinen Pool nach den
        # HOST-Kernen und pinnt Thread i an Kern i -> pthread_setaffinity_np scheitert
        # fuer jeden Kern ausserhalb der cgroup-Maske mit EINVAL. Das kostete je
        # Vision-Lauf vier rote [E]-Zeilen im Prod-Log (.170). Kein Monkeypatch von
        # ort.InferenceSession -- die Optionen haengen nur an unserer eigenen Session.
        from face_audit import _ort_thread_opts
        _CACHE["sess"] = ort.InferenceSession(
            _dino_pfad(), providers=["CPUExecutionProvider"],
            sess_options=_ort_thread_opts())
    im = np.asarray(Image.fromarray(bild_rgb).resize(GROESSE),
                    dtype=np.float32) / 255.0
    x = ((im - MEAN) / STD).transpose(2, 0, 1)[None]
    e = _CACHE["sess"].run(None, {"bild": x.astype(np.float32)})[0]
    return (e / np.linalg.norm(e, axis=1, keepdims=True))[0]


def einbetten(bild_rgb):
    """DAS eine Koerper-Embedding dieses Projekts (DINOv2-ONNX, CPU, normiert).

    Oeffentlicher Griff fuer den Vision-Urteilspfad (V4): dessen Kaskade
    ordnet die Galerie-Personen nach Zentroid-Abstand IM SELBEN Raum, in dem
    auch das Live-Urteil rechnet (§7/E2). Ein zweiter Embedding-Weg waere die
    Streuklasse — und er wuerde eine andere Reihenfolge liefern als die
    Erkennung, die er erklaeren soll."""
    return _emb1(bild_rgb)


def _uebergabe_dir(data_dir, eid):
    return os.path.join(data_dir, "events", str(eid).replace("/", "_"))


def _uebergabe_raeumen(d):
    """Die Uebergabe ist ein Briefkasten, kein Archiv: gelesen = geleert.
    (Der Kontroll-Speicher der beurteilten Bilder ist ein eigener Zug mit
    eigenem Schalter — konzept_frames.md §7/Z8; bis dahin waeren liegen
    bleibende Vollbild-PNGs nur stiller Plattenverbrauch bis zur
    60-Tage-Crops-Retention.)"""
    try:
        for fn in os.listdir(d):
            if (fn.startswith("koerper_") and fn.endswith(".png")) \
                    or fn == "koerper.json":
                os.remove(os.path.join(d, fn))
    except OSError:
        pass


def _uebergabe_lesen(data_dir, eid):
    """Z5: die Top-K-Crops, die der GEMEINSAME Frame-Lauf (analyze.py als
    Abnehmer 'koerper') schon gelegt hat — dann muss dieser Clip hier nicht
    ein zweites Mal dekodiert werden.

    Rueckgabe wie pfad_snapshots: Liste (score, frame_i, crop_bgr, hoehe).
    LEERE Liste = die Kette lief und fand nichts (dann uebernimmt der
    Snapshot-Notnagel, exakt wie heute). None = es liegt keine brauchbare
    Uebergabe -> der eigene Weg gilt unveraendert."""
    if not data_dir:
        return None
    d = _uebergabe_dir(data_dir, eid)
    try:
        with open(os.path.join(d, "koerper.json")) as f:
            daten = json.load(f)
    except (OSError, ValueError):
        return None
    try:
        if daten.get("ausfall"):
            return None            # Kette lief dort NICHT zu Ende
        import cv2
        top = []
        for e in daten.get("top") or []:
            bild = cv2.imread(os.path.join(d, e["datei"]))
            if bild is None:       # halbe Uebergabe: lieber selbst fahren
                return None
            top.append((float(e.get("score") or 0.0),
                        int(e.get("frame_i") or 0), bild,
                        int(e.get("hoehe") or bild.shape[0])))
        return top
    finally:
        _uebergabe_raeumen(d)


def _bild_holen(frigate_url, eid, data_dir=None):
    """.148: Urteilsbild aus EIGENEN Clip-Frames — dieselbe Kette wie das
    Training (pfad_snapshots: 3 fps, Pfad-Bestbilder; Pose-Zuschnitt wie
    ernte_event, aber OHNE harte Gates: das Live-Urteil braucht Abdeckung,
    ein Teil-Koerper wird geurteilt statt verworfen). Rueckgabe
    (PIL-Image RGB oder None, quelle 'frames'|'snapshot').
    NOTNAGEL: scheitert die Kette (kein Clip/path_data/Haenger), urteilt
    der alte Snapshot-Weg EINMALIG weiter — sichtbar als quelle='snapshot'
    im Treffer-Buch, nie still.
    Z5: liegt eine UEBERGABE aus dem gemeinsamen Frame-Lauf vor, kommen die
    Bestbilder von dort — gleiche Kette, gleiche Frames, nur EIN Decode. Die
    INFERENZ (PoseWache, Zuschnitt, DINOv2, SVM) bleibt hier im Dienst."""
    from PIL import Image
    try:
        from core.personlauf import _proto, EVENT_ZEITWACHE_S
        _proto()                       # sys.path + FRIGATE-ENV-Bruecke; auch
        #                                der Uebergabe-Weg braucht sie gleich
        #                                fuer pose_wache/ernte_lauf
        top = _uebergabe_lesen(data_dir, eid)
        if top is None:
            import concurrent.futures as cf
            import pfad_snapshots
            pool = cf.ThreadPoolExecutor(max_workers=1)
            fut = pool.submit(pfad_snapshots.event_verarbeiten, {"eid": eid})
            try:
                top, _info = fut.result(timeout=EVENT_ZEITWACHE_S)
            finally:
                pool.shutdown(wait=False)
        if top:
            if _CACHE.get("wache") is None:
                from pose_wache import PoseWache
                _CACHE["wache"] = PoseWache()
            from ernte_lauf import person_zuschnitt, blick_bestimmen
            beste, beste_px, beste_mess = None, 0, {}
            for _score, _fi, crop_bgr, hoehe in top[:2]:
                if hoehe < 60:
                    continue
                zug = crop_bgr
                # pose_erkannt ist ausdruecklich FALSE und nicht bloss "Feld
                # fehlt": ein Altbild von vor dieser Version traegt den
                # Schluessel gar nicht und darf deshalb nicht wie ein Bild
                # ohne Skelett behandelt werden. Genau diese Unterscheidung
                # braucht die Kandidaten-Auswahl.
                mess = {"pose_erkannt": False}
                try:
                    _komplett, det = _CACHE["wache"].pruefen(crop_bgr)
                    if det.get("punkte") is not None:
                        zug, anteil, zbox = person_zuschnitt(
                            crop_bgr, det["punkte"], det["scores"])
                        # Die Pose-Wache laeuft hier ohnehin, ihre Messwerte
                        # wurden bisher weggeworfen (User-Fund 09.08.: "wir
                        # nehmen alle Bilder, bei denen die Person optimal zu
                        # sehen ist"). Genau dafuer ist `person_anteil` da —
                        # Skelett-Box-Flaeche am Crop, also wie viel Person
                        # ueberhaupt im Bild ist. Ohne ihn bewertet die
                        # Kandidaten-Auswahl belaubte Buesche als "scharf".
                        # FELDNAMEN WIE IM ERNTE-MANIFEST (core/personernte.py),
                        # damit die Kurator-Bewertung sie ohne Umweg liest —
                        # keine zweite Struktur fuer dieselbe Sache.
                        blick, blick_mess = blick_bestimmen(det, crop_bgr.shape[0])
                        mess = {"pose_erkannt": True,
                                "person_anteil": anteil, "zuschnitt": zbox,
                                "blick": blick, "blick_mess": blick_mess,
                                "wache": {"kopf": det.get("kopf"),
                                          "knoechel": det.get("knoechel"),
                                          "fuesse": det.get("fuesse")}}
                except Exception:
                    pass               # Zuschnitt ist Politur, nie Blocker
                px = zug.shape[0] * zug.shape[1]
                if px > beste_px:
                    beste, beste_px, beste_mess = zug, px, mess
            if beste is not None:
                return Image.fromarray(beste[:, :, ::-1]), "frames", beste_mess
    except Exception:
        pass
    # Notnagel: Snapshot + Frigate-Box (Alt-Weg bis .147)
    try:
        with urllib.request.urlopen(
                f"{frigate_url.rstrip('/')}/api/events/{eid}",
                timeout=15) as r:
            ev = json.loads(r.read())
        box = (ev.get("data") or {}).get("box")
        if not box:
            return None, "snapshot", {}
        with urllib.request.urlopen(
                f"{frigate_url.rstrip('/')}/api/events/{eid}"
                "/snapshot-clean.webp", timeout=15) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGB")
        W, H = im.size
        x, y, w, h = box
        l = max(0, int((x - RAND * w) * W))
        t = max(0, int((y - RAND * h) * H))
        rt = min(W, int((x + w * (1 + RAND)) * W))
        bb = min(H, int((y + h * (1 + RAND)) * H))
        if bb - t < 60:
            return None, "snapshot", {}
        return im.crop((l, t, rt, bb)), "snapshot", {}
    except Exception:
        return None, "snapshot", {}


def urteilen(data_dir, frigate_url, eid, schwelle=None, kontrolle=None,
             still=False):
    """EIN Event beurteilen. Rueckgabe: dict(person, score, feuer:bool)
    oder None (kein Modell / kein Bild / unter Schwelle ohne Feuer).
    feuer=True heisst: Feuer-Regel erfuellt UND Karenz frei -> MELDEN.

    kontrolle (Z8, optional): Auftrag an den Kontroll-Speicher —
    {"sammeln": bool, "pass_key": str, "karenz_s": int}. None = kein Auftrag:
    dann laeuft hier exakt dieselbe Kette wie vor Z8, es entsteht kein Ordner
    und kein zusaetzliches Bild.

    still (0.1.0.163, LIVE-BUG 09.08.): der STUMME Lauf fuer die Nachanalyse
    eines VERGANGENEN Durchgangs. Diese Funktion hat ZWEI Wirkungen — sie legt
    das beurteilte Bild ab UND sie fuehrt den Live-Strang (Treffer-Bild,
    Zeitfenster, Karenz, Treffer-Buch, Melde-Objekt). Die Nachanalyse braucht
    nur die erste. Als der Nachanalyse-Knopf in .161 diese Funktion scharf
    schaltete, wurde nur an die erste gedacht: ein Durchgang von GESTERN lief
    in das Live-Fenster, buchte einen Treffer mit der Uhrzeit von JETZT und
    loeste eine Telegram-Meldung aus ("recognized by body"), als stuende die
    Person gerade vor der Tuer.

    `still=True` heisst deshalb: Kontroll-Bild ablegen — und sonst NICHTS. Kein
    Treffer-Bild, kein Buchen, kein Anfassen von Zeitfenster und Karenz. Die
    Rueckgabe ist dann IMMER None: ein stiller Lauf kann konstruktiv gar kein
    Melde-Objekt erzeugen, also kann auch kein Aufrufer versehentlich eines
    weiterreichen. (Nebenwirkung, bewusst: der Verfalls-Trim des
    Kontroll-Speichers haengt an `treffer_buchen` und laeuft hier nicht mit —
    der naechste LIVE-Lauf holt ihn nach.)"""
    from core.personmodell import status_lesen
    status = status_lesen(data_dir)
    if not status or not status.get("scharf"):
        return None
    m = _svm(data_dir)
    if m is None:
        return None
    schwelle = float(schwelle or status.get("schwelle") or SCHWELLE_STD)
    crop, quelle, mess = _bild_holen(frigate_url, eid, data_dir)
    if crop is None:
        return None
    e = _emb1(np.asarray(crop))
    proba = m["svm"].predict_proba(e[None])[0]
    k = int(np.argmax(proba))
    # Kontroll-Speicher (§7/Z8): das BEURTEILTE Bild mit Klasse, Score und
    # quelle ablegen — VOR jeder Urteils-Verzweigung, damit auch die
    # verworfenen Faelle sichtbar bleiben (FREMD-Abweisung gleich unten,
    # unter der Schwelle weiter unten). Genau die sind interessant, wenn
    # jemand wissen will, WARUM ein Durchgang nicht gemeldet wurde.
    # `mess` sind die Pose-Messwerte aus derselben Kette (person_anteil, blick,
    # wache) — sie kosten nichts extra und beantworten die Frage, auf die es bei
    # der Kandidaten-Auswahl ankommt: wie viel PERSON ist im Bild, statt wie
    # viel Kantenstruktur. Beim Notnagel-Weg (quelle='snapshot') ist `mess` leer;
    # fehlende Werte erzeugen in der Bewertung weder Bonus noch Abzug.
    kontrolle_ablegen(data_dir, kontrolle, eid, crop,
                      {"klasse": (m["personen"][k] if k < len(m["personen"])
                                  else "FREMD"),
                       "score": round(float(proba[k]), 3), "quelle": quelle,
                       "schwelle": round(float(schwelle), 3), **(mess or {})})
    if still:
        # HIER endet der stille Lauf — vor JEDEM Live-Anteil. Der Schnitt liegt
        # bewusst direkt hinter dem Ablegen und nicht weiter unten: alles ab
        # hier (Treffer-Bild, Fenster, Karenz, Buchung, Rueckgabe-Objekt) ist
        # Gegenwart, und ein vergangener Durchgang hat in der Gegenwart nichts
        # zu suchen.
        return None
    # .139: hat das Modell eine FREMD-Klasse gelernt, liegt sie HINTER den
    # Personen (Spalte len(personen)). Gewinnt sie, ist das Urteil "kein
    # Bewohner" — kein Treffer, nichts gebucht, kein Bild abgelegt. Der
    # Index-Vergleich taugt auch fuer alte svm.pkl ohne Fremd-Spalte.
    if k >= len(m["personen"]):
        return None
    person, score = m["personen"][k], float(proba[k])
    if score < schwelle:
        return None
    # Treffer-Bild je Event ablegen — beim Feuern gewinnt das BESTE Bild des
    # Fensters (groesster Crop), nicht das zufaellige Bild des Feuer-Moments
    # (User-Fund 04.08.: Meldung trug einen 60x140-Fernkamera-Crop, waehrend
    # derselbe Durchgang 312x791 hatte — Szenario-Prinzip gilt auch hier).
    # Tagesbestaendig statt Fenster-fluechtig (User 05.08.: der Today-Chip
    # eines koerper-zugeschriebenen Passes soll das BESTE Koerper-Bild des
    # Durchgangs zeigen — also leben die Crops jetzt neben dem Treffer-Buch
    # und werden mit dessen 30-Tage-Trim geraeumt, nicht mit dem Fenster).
    bild_dir = os.path.join(data_dir, "personlern", "treffer")
    os.makedirs(bild_dir, exist_ok=True)
    bild = os.path.join(bild_dir, str(eid).replace("/", "_") + ".jpg")
    try:
        crop.save(bild, "JPEG", quality=88)
        px = crop.size[0] * crop.size[1]
    except OSError:
        bild, px = None, 0
    # Feuer-Regel-Werte aus dem Modell-Status (UI: Model status), sonst
    # die Standardwerte hier — konfigurierbar seit .114 (User-Wunsch 04.08.)
    fenster_s = int(status.get("fenster_s") or FENSTER_S)
    feuer_ab = int(status.get("feuer_ab") or FEUER_AB)
    karenz_s = int(status.get("karenz_s") or KARENZ_S)
    jetzt = time.time()
    f = _fenster_lesen(data_dir)
    raus = [t2 for t2 in f["treffer"] if jetzt - t2["ts"] > fenster_s]
    f["treffer"] = [t2 for t2 in f["treffer"]
                    if jetzt - t2["ts"] <= fenster_s]
    f["treffer"].append({"ts": jetzt, "person": person, "eid": eid,
                         "score": round(score, 3), "bild": bild, "px": px})
    n = sum(1 for t2 in f["treffer"] if t2["person"] == person)
    karenz_bis = float(f["karenz"].get(person) or 0)
    feuer = n >= feuer_ab and jetzt >= karenz_bis
    if feuer:
        f["karenz"][person] = jetzt + karenz_s
        beste = max((t2 for t2 in f["treffer"]
                     if t2["person"] == person and t2.get("bild")
                     and os.path.isfile(t2["bild"])),
                    key=lambda t2: t2.get("px", 0), default=None)
        if beste:
            bild = beste["bild"]
    _fenster_schreiben(data_dir, f)
    treffer_buchen(data_dir, {"ts": round(jetzt, 1), "eid": eid,
                              "person": person, "score": round(score, 3),
                              "feuer": feuer, "bild": bool(bild),
                              "quelle": quelle}, kontrolle=kontrolle)
    return {"person": person, "score": round(score, 3), "stuetzen": n,
            "feuer": feuer, "bild": bild, "quelle": quelle}
