"""core/harvest_set — der Satz-Schreibweg der Ernte: jedes gespeicherte Gesicht als Satz der Referenz-Quelle.

HERKUNFT: Bauplan analysen/bauplan_refquelle_einbau.md, Stufe E3 Punkt 1, Schnitt E3a-1b (Entscheide J2,
J4, J6 mit der Ergaenzung zu O559 (1), Eigentuemer 07.10.2026 11:40:41; Aufruf-Vertrag O559 (2) und (7));
Entscheide 2 (Personenausschnitt, Weg 1), 4 (Kennung an jeder Zahl), 11 (Kandidaten sind Saetze mit
Status), 21 (ref_id); Konzept analysen/konzept_referenzquelle.md Abschnitte 1, 2 und 4. Eigene Datei, weil
core/ernte.py schon 1518 Zeilen hat (offene Liste O557 c).

ZWECK: core/ernte.ernte_event ruft fuer JEDES Gesicht, das die Ernte speichert (ein M-Kandidat; seit
E3a-1c ist der Satz sein einziger Bild-Ort, nichts mehr unter crops/), `SetWriter.write`. Der Schreibweg entscheidet nichts darueber, WAS gespeichert
wird (das tut das Sieb der Ernte, unveraendert), und er rechnet keine Sieb-Achse: er schneidet die Teile,
rechnet Fingerabdruck und Norm aus den gespeicherten 112er-Bytes und uebergibt alles an core.refquelle.

REIHENFOLGE JE GESICHT ("erst Bild, dann Zahl", Konzept Abschnitt 1):
  a  der 112er auf der CPU (core.ernte.align112 = face_align.norm_crop mit den fuenf Punkten), als PNG-Bytes;
  b  Fingerabdruck und Norm aus GENAU diesen Bytes (wieder dekodiert), in EINEM Aufruf der r-Stufe
     (BildRechner.embeddings des EngineEmbedders liefert beide Ausgaenge, O562 b), nie aus dem
     Gesichtsobjekt der Suche; die EngineNormMass sagt nur, ob die Norm fuer das Modell geeicht ist
     (keine eigene Mess-Session: der 2,7-GB-Platz aus .518 entsteht nicht); die Rechenwerk-Kennung
     erst danach (O559 (2)), auf dem Engine-Weg ohne batch;
  c  Profilbild: Quadrat um die Mitte der Kommazahl-Box, Seite profil_faktor mal laengere Boxseite,
     unverkleinert, verlustfrei, am Bildrand beschnitten;
  d  Personenausschnitt in Originalpixeln, bemessen ueber core.livewache.person_region (die eine Regel),
     am Bildrand beschnitten; ist nichts davon im Bild, steht der Grund in quelle.json;
  e  quelle.json mit dem, was zur Schreibzeit vorliegt; V-Linie, Norm-Latte des gebuendelten Norm-Schritts
     und Umfeld des Vorrats entstehen spaeter und kommen nicht hierher (J2: Katalog-Nachtrag, E3a-1c);
     dann core.refquelle.write_set mit Status kandidat, Grund = Herkunftsart.

DAS JOB-FELD (J4): `FEED_FIELD` traegt FEED_KEYS; der Dienst baut es mit `feed()` an den drei Job-Bauten
(Lernlauf, Pass-Ernte, Kalibrier-Auffueller) und seit E3a-2 am Sammle-Job des Unbekannt-Pools. Fehlt das Feld oder ein Pflichtschluessel, schreibt der Job
keinen Satz, sagt es einmal als ERROR und in der Job-Antwort (`summary()`); die Funde behalten nur ihre
Zeile, ohne Bild (seit E3a-1c gibt es keinen zweiten Bild-Ort). Ein Werkswert fuer profil_faktor steht hier bewusst nicht (er steht seit E3a-1c in der Werkswert-
Liste und im Schema des Dienstes, verifyd.load_config und Service.CONFIG_WHITELIST).

DER WORKER (Schnitt E3a-3, Entscheid 7, J9): worker_kern.Bildvorrat.schreiben schreibt am Ereignis-Ende, nach dem
Urteil, je Uebernahme-Angebot (bestes Gesicht je Person ueber win_thresh, Anlern-Kandidat je Person, Fremd-Kandidat)
einen Satz mit der Herkunftsart worker ueber `write_held`: Eingang ist der gehaltene Sieger-Frame, nach BGR gewandelt
(worker_kern.nv12_bgr, `PIXEL_WORKER`), mit seiner Kommazahl-Box und den fuenf Punkten. SPEICHERN OHNE RECHNUNG (Bauplan
analysen/bauplan_fix_0113.md, Entscheid 3 und Stufe F3; aendert Entscheid 7 des Bauplans Referenz-Quelle): der Worker
uebergibt den Fingerabdruck der r-Stufe und die Zahlen der Erkennung (`GRAPH_MEASURES`: Score, Detektion, Guete e und t,
Norm, front, Schaerfe, Kopfwinkel der fd-Stufe) in voller Genauigkeit; der Schreiber traegt sie einmal als Werte des
Satzes mit der Kennung des Rechengraphen ein (Rechenweg `GRAPH_WAY`), die der Dienst beim Start holt und dem Schreiber
mitgibt (`kennung`). Er braucht dafuer kein Rechenwerk: keine r-Stufe, keine Norm-Messung, keine Nachmessung; gerechnet
wird nur Bildarbeit (112er auf der CPU, Profilbild, Personenausschnitt). Die Ernte bleibt bei "erst Bild, dann Zahl"
(`write` ohne `graph`). Die Zeilen der kandidaten.jsonl
des Ereignisses (`EVENT_FILE`) tragen die ref_id; eine Zeile mit `BEST_FIELD` ist das beste Gesicht einer Person,
gelesen wird die Datei nur ueber `event_rows`.

DER UNBEKANNT-STAPEL (Bauplan analysen/bauplan_fix_0113.md, Entscheide 6 und 7, Stufe F4): der Bildvorrat buendelt
die fremden Gesichter eines Clips zu Gruppen und schreibt je Gesicht einen Satz ueber `write_held` (Herkunftsart
worker, Status kandidat). Die Gruppen stehen NUR in der Stapel-Datei `UNKNOWN_FILE` im Ereignisordner (eine JSON-Zeile
je Clip, Anhaenge-Modus wie EVENT_FILE: Ereignis, Kamera, Zeit, Kennung, Latte, Gruppen mit ref_ids und bestem
Gesicht, Zahlen je Gesicht, rahmen_spitze), nie in EVENT_FILE, weil dort Lernvorschlag, Besucher-Pruefung und
Ereignis-Seite lesen (X9). Gelesen wird sie nur ueber `event_unknown`; `event_ref_ids` nimmt ihre ref_ids mit, damit das
Raeumen die Stapel-Saetze verwirft (X10). Der Dienst haengt nach der Buchung einen Zeiger an
state/unbekannt_schlange.jsonl; der Verbraucher dieser Schlange ist nicht Teil von F4.

DER UNBEKANNT-POOL (Schnitt E3a-2, Entscheid 11, J8): anlernen._sammle_intern schreibt jedes Gesicht, das
den Zulauf-Sieb besteht, mit der Herkunftsart pool (ohne Lauf-ID) ueber DIESEN Schreibweg; ein zweiter
Schreibweg entsteht nicht. Ein Sammle-Job rechnet viele Ereignisse, deshalb setzt der Pool je Ereignis die
Herkunft mit `for_event`; das Frame haelt er je Kandidat bis nach dem Sieb (wie vorher den Kontext-Ausschnitt).
Ohne Satz bekommt ein Pool-Gesicht keine Zeile (`kept_text`).

SPERREN (J6, O559 (1)): Saetze schreibt nur der Engine-Weg (bild_kern.EngineEmbedder, Worker-Dienst; der Worker-Weg
mit der Kennung des Rechengraphen ohne Rechenwerk, F3; ohne Kennung sperrt der Bildvorrat laut).
Ein anderer Embedder (face_audit.Embedder, also worker.py) ist laut gesperrt, weil seine Kennung Geraet
und Genauigkeit nicht immer nennen kann (O559 (1)); worker.py gibt dazu den eigenen Grund mit
(`LOCK_NOT_STARTED`: der Dienst startet worker.py seit E3.1 nicht mehr).

EHRLICHE GRENZEN:
  - Die Kennung von Detektion, Kopfwinkel und Norm ist die des Rechenwerks (Engine-Weg); fuer Guete e und t,
    Kopfhaltung und Struktur steht nur das Modell und der Ausschnitt da (diese Modelle binden laut
    bild_kern-Kopf den CPU-Provider; Geraet, Genauigkeit und Bibliothek liest hier niemand ab).
  - Die Herkunft der Startzeit einer eigenen Videodatei (core/dateiquelle: creation_time oder mtime) reist
    nicht im Ereignis mit; sie steht als "unbekannt" da.
  - Der Wert "vorrat" der Herkunftsart ist zur Schreibzeit nicht vergebbar: ob ein Fund Vorrat wird,
    entscheidet erst der Norm-Schritt (J2); Vorrats-Funde sind Saetze der Herkunftsart lernlauf.
  - Die Variante im Job-Feld wird gegen die Kennung des Rechenwerks gehalten; weichen sie ab, schreibt der
    Job keine Saetze mehr (laut). Beide lesen SUSLIK_VARIANT, im Dienst und im Worker-Prozess.
  - Worker-Satz (F3): der gespeicherte 112er ist der CPU-Zuschnitt des gehaltenen Frames, der Fingerabdruck der
    des Rechengraphen (dessen eigener Zuschnitt); der Satz traegt damit Bild und Zahl aus zwei Zuschnitten
    desselben Funds. Den L2-Betrag des uebergebenen Fingerabdrucks rechnet hier niemand nach, die Formpruefung
    des Moduls (write_set) lehnt eine Abweichung laut ab.
"""
import json
import math
import os
import sys
import time
import types

from core import logbuch as _logbuch

_log = _logbuch.logger(__name__)

FEED_FIELD = "set_feed"
FEED_MUST = ("data_dir", "profil_faktor", "software_version", "image_variante", "herkunftsart")
FEED_KEYS = FEED_MUST + ("lauf_id",)    # lauf_id darf None sein: der Kalibrier-Auffueller hat keinen Lauf
ART_LERNLAUF, ART_PASSERNTE, ART_KALIBRIER, ART_POOL = "lernlauf", "passernte", "kalibrier", "pool"
ART_WORKER = "worker"                    # E3a-3: Uebernahme-Angebote der Ereignis-Analyse
# E3a-4 (J10): der Datei-Weg, Foto-Upload und Frigate-Import (core/dateisatz.py, Job dateisatz des Worker-Dienstes)
ART_UPLOAD, ART_FRIGATE_IMPORT = "upload", "frigate_import"
ARTEN = (ART_LERNLAUF, ART_PASSERNTE, ART_KALIBRIER, ART_POOL, ART_WORKER, ART_UPLOAD, ART_FRIGATE_IMPORT)
STATUS = "kandidat"
CLIP_FRIGATE, CLIP_FILE = "Frigate-Ereignis", "eigene Videodatei"
UNKNOWN = "unbekannt"
ERRORS_KEPT = 5                          # so viele Fehlertexte reisen in der Job-Antwort mit
LOCK_FACE_AUDIT = ("sets are written only on the engine way (worker_dienst.py); this harvest runs on another "
                   "embedder, whose engine identity cannot name device and precision (J6, O559)")
LOCK_NOT_STARTED = ("this harvest runs in worker.py, which the service no longer starts since E3.1 "
                    "(WorkerProzess has no caller); sets are written only by worker_dienst.py (J6, O559)")
PERSON_MISSING = "the person area lies outside the frame"
KEPT_LINE = "the finding keeps its line, without picture (E3a-1c)"
KEPT_POOL = "the face is not collected into the unknown pool (E3a-2)"
KEPT_WORKER = "the event keeps its candidate line without picture and without reference set (E3a-3)"
KEPT_FILE = "the file stays in its staging folder and becomes no reference (E3a-4)"
# E3a-3: der Pixelweg des Worker-Eingangs (Herkunft, Entscheid 7) und die Ablage des Ereignisses.
PIXEL_WORKER = "worker NV12 -> BGR (worker_kern.nv12_bgr, cv2 COLOR_YUV2BGR_NV12)"
GRAPH_WAY = "rechengraph (worker_kern.event_rechnen)"
# Fix 0.1.1.013 F3: die Werte eines Worker-Satzes, so wie die Erkennung sie gerechnet hat (dazu der Fingerabdruck)
GRAPH_MEASURES = ("score", "detektion", "guete_e", "guete_t", "norm", "front", "schaerfe", "kopfwinkel")
# Nachtrag E3a-3 (O569 B): was der Datei-Weg am CPU-Zuschnitt nachmisst (worker_kern.Bildvorrat._nachmessen, Werte
# des Satzes); die Ausschnitt-Namen der Kennungen gelten fuer Ernte und Datei-Weg gleich.
CPU_MEASURES = ("guete_e", "guete_t", "schaerfe", "kopfwinkel")
CUT_NARROW, CUT_112 = "enge Box (ganzzahlig)", "rechen112"
NOT_MEASURED = "not measured (no reason given)"
EVENT_FILE = "kandidaten.jsonl"
# Fix 0.1.1.013 F4 (Entscheid 7): die Stapel-Datei des Unbekannt-Stapels im Ereignisordner, eine Zeile je Clip
UNKNOWN_FILE = "unbekannt_stapel.jsonl"
# Bauplan analysen/bauplan_verbraucher_unbekannt.md Stufe V1a Punkt 4 (F4 N4, W17): der Name der Schlange der
# Unbekannt-Stapel unter state/, ein Stueck je Tag (tag = JJJJ-MM-TT); Schreiber und Leser: core/unbekannt_verbraucher
QUEUE_FILE = "unbekannt_schlange-{tag}.jsonl"
BEST_FIELD = "bestbild"
# J9: ein Ereignis-Kandidat aus einer Analyse vor dieser Version hat keine ref_id; seine Uebernahme lehnt laut ab
# (Produkt-Text, englisch). Die Ereignis-Aufbewahrung nimmt ihn mit.
ALT_KANDIDAT_HINWEIS = ("this suggestion comes from an analysis made before this version (no reference set) and "
                        "cannot be adopted; reject it, the event retention removes it")


def kept_text(art):
    """Was mit einem Fund ohne Satz geschieht, je Herkunftsart (Log und Job-Antwort).
    -> Text"""
    return {ART_POOL: KEPT_POOL, ART_WORKER: KEPT_WORKER, ART_UPLOAD: KEPT_FILE,
            ART_FRIGATE_IMPORT: KEPT_FILE}.get(art, KEPT_LINE)


def event_rows(event_dir):
    """Die Zeilen der kandidaten.jsonl eines Ereignis-Ordners, getrennt nach Art (E3a-3); unlesbare Zeilen
    werden gezaehlt und gemeldet. -> (Kandidaten-Zeilen in Dateireihenfolge, {Person: Bestbild-Zeile})"""
    kand, best, kaputt = [], {}, 0
    try:
        with open(os.path.join(event_dir, EVENT_FILE), encoding="utf-8") as f:
            for zeile in f:
                if not zeile.strip():
                    continue
                try:
                    d = json.loads(zeile)
                except ValueError:
                    kaputt += 1
                    continue
                if not isinstance(d, dict):
                    kaputt += 1
                elif d.get(BEST_FIELD):
                    best[d.get("person")] = d
                else:
                    kand.append(d)
    except FileNotFoundError:
        return [], {}
    if kaputt:
        _log.warning(f"event folder {os.path.basename(event_dir)}: {kaputt} unreadable line(s) in "
                     f"{EVENT_FILE} skipped")
    return kand, best


def event_unknown(event_dir):
    """Die Zeilen der Stapel-Datei (UNKNOWN_FILE) eines Ereignis-Ordners, eine je geschriebenem Clip (Fix 0.1.1.013 F4);
    unlesbare Zeilen werden gezaehlt und gemeldet. -> Liste der Zeilen in Dateireihenfolge, ohne Datei leer"""
    zeilen, kaputt = [], 0
    try:
        with open(os.path.join(event_dir, UNKNOWN_FILE), encoding="utf-8") as f:
            for zeile in f:
                if not zeile.strip():
                    continue
                try:
                    d = json.loads(zeile)
                except ValueError:
                    kaputt += 1
                    continue
                if isinstance(d, dict):
                    zeilen.append(d)
                else:
                    kaputt += 1
    except FileNotFoundError:
        return []
    if kaputt:
        _log.warning(f"event folder {os.path.basename(event_dir)}: {kaputt} unreadable line(s) in "
                     f"{UNKNOWN_FILE} skipped")
    return zeilen


def event_ref_ids(event_dir):
    """Alle ref_ids eines Ereignis-Ordners (Kandidaten, Bestbilder und seit Fix 0.1.1.013 F4 die Gruppen der
    Stapel-Datei), fuer das Raeumen (J3 dritte Ergaenzung, X10). -> Liste ohne Doppel"""
    kand, best = event_rows(event_dir)
    ids = [z["ref_id"] for z in kand + list(best.values()) if z.get("ref_id")]
    ids += [r for z in event_unknown(event_dir) for g in (z.get("gruppen") or []) if isinstance(g, dict)
            for r in (g.get("ref_ids") or [])]
    return list(dict.fromkeys(ids))


def feed(cfg, art, lauf_id, version, variant):
    """Das Job-Feld der Config-Zufuhr (J4) aus der Config des Dienstes bauen, ohne Werkswert.
    -> dict mit FEED_KEYS (ein fehlender Config-Wert bleibt None und ist im Worker ein lauter Fehler)"""
    return {"data_dir": cfg.get("data_dir"), "profil_faktor": cfg.get("profil_faktor"),
            "software_version": version, "image_variante": variant, "herkunftsart": art,
            "lauf_id": lauf_id}


def feed_errors(f):
    """Pruefen, ob das Job-Feld vollstaendig und brauchbar ist.
    -> Liste der Fehler (leer = in Ordnung)"""
    if not isinstance(f, dict):
        return [f"job field '{FEED_FIELD}' is missing"]
    errs = [f"key '{k}' missing" for k in FEED_MUST if f.get(k) is None]
    errs += [f"key '{k}' unknown" for k in f if k not in FEED_KEYS]
    pf = f.get("profil_faktor")
    if pf is not None and (isinstance(pf, bool) or not isinstance(pf, (int, float))
                           or not math.isfinite(pf) or pf <= 0):
        errs.append(f"profil_faktor {pf!r} is not a positive number")
    if f.get("herkunftsart") is not None and f["herkunftsart"] not in ARTEN:
        errs.append(f"herkunftsart {f['herkunftsart']!r} (one of {', '.join(ARTEN)})")
    return errs


def _engine_module(emb):
    """-> das geladene Modul bild_kern, wenn emb ein EngineEmbedder ist, sonst None.
    Ohne Import: wer bild_kern nicht geladen hat, haelt keinen EngineEmbedder."""
    bk = sys.modules.get("bild_kern")
    return bk if bk is not None and isinstance(emb, bk.EngineEmbedder) else None


def _png(img):
    """-> verlustfreie PNG-Bytes eines BGR-Bildes; lauter Fehler, wenn cv2 nicht kodiert."""
    import cv2                                            # noqa: PLC0415  lazy wie in core/ernte
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ValueError("PNG encoding failed")
    return buf.tobytes()


def _num(v):
    """-> v als float (numpy-Zahlen sind kein JSON) oder None."""
    return None if v is None else float(v)


def _pair(v):
    """-> ein Groessenpaar als Liste ganzer Zahlen oder None."""
    return None if v is None else [int(x) for x in v]


def _cut(frame, x1, y1, x2, y2):
    """Ein Rechteck in Kommazahlen auf ganze Pixel bringen (aussen abrunden) und am Bildrand beschneiden.
    -> (Ausschnitt oder None, (a1, b1, a2, b2))"""
    h, w = frame.shape[:2]
    a1, b1 = max(0, math.floor(x1)), max(0, math.floor(y1))
    a2, b2 = min(w, math.ceil(x2)), min(h, math.ceil(y2))
    if a2 <= a1 or b2 <= b1:
        return None, (a1, b1, a2, b2)
    return frame[b1:b2, a1:a2], (a1, b1, a2, b2)


def engine_norm_mass(emb):
    """Die Feature-Norm des Engine-Wegs fuer einen Embedder (bild_kern.EngineNormMass ueber dessen r-Stufe).
    -> EngineNormMass, oder None, wenn emb kein EngineEmbedder ist (dann gibt es keine Norm, J6)"""
    bk = _engine_module(emb)
    return bk.EngineNormMass(emb.rechner, None, modell=emb.modell) if bk is not None else None


def fingerprint_from_112(emb, norm_mass, b112):
    """Fingerabdruck und Norm aus den PNG-Bytes eines 112ers, ohne Kennung: der Rechenteil von SetWriter._fingerprint,
    an einer Stelle auch fuer den Datei-Weg ausserhalb des Workers aufrufbar (Bauauftrag E4-4a; heute die Zeilenkarte
    des Pruefstands, die Nachrechnung liegt seit Fix 0.1.1.013 F1 im Archiv).
    -> (Fingerabdruck float32 L2, Norm oder None, Grund ohne Norm); ValueError, wenn der Fingerabdruck keine Laenge hat"""
    import cv2                                                # noqa: PLC0415
    import numpy as np                                        # noqa: PLC0415
    img = cv2.imdecode(np.frombuffer(b112, np.uint8), cv2.IMREAD_COLOR)
    # O562 b (E3a-1c): EIN Aufruf der r-Stufe liefert beide Ausgaenge (Fingerabdruck
    # und Feature-Norm, BildRechner.embeddings); die EngineNormMass sagt nur noch, ob
    # die Norm fuer dieses Modell geeicht ist (ok/grund).
    werte, normen = emb.rechner.embeddings([img])
    e = np.asarray(werte[0], np.float32).ravel()
    lang = float(np.linalg.norm(e))
    if not (math.isfinite(lang) and lang > 0):
        raise ValueError("the fingerprint has no length")
    fp = (e / lang).astype(np.float32)
    norm, ohne = None, None
    if norm_mass is not None and getattr(norm_mass, "ok", False):
        norm = float(normen[0])
    else:
        ohne = getattr(norm_mass, "grund", None) or "no feature-norm measure on this job"
    return fp, norm, ohne


class SetWriter:
    """Der Satz-Schreibweg EINES Ernte-Jobs: Zufuhr und Weg einmal pruefen, dann je Gesicht `write`."""

    def __init__(self, set_feed, emb, ctx, lock=None, struktur_mass=None, art=None, kennung=None):
        """ctx: eid, kamera, ts, quelle (Feld der Kandidaten-Zeile), latten (die Latten des Funds).
        lock: ein Sperrgrund des Aufrufers (worker.py, LOCK_NOT_STARTED; Worker ohne Job-Feld oder ohne Kennung).
        art: die Herkunftsart fuer den Text eines Funds ohne Satz, wenn das Job-Feld fehlt (E3a-3).
        kennung: die Rechenwerk-Kennung des Rechengraphen (Worker-Weg, Fix 0.1.1.013 F3); mit ihr schreibt der Weg
        ohne Rechenwerk (emb None), Fingerabdruck und Werte kommen vom Aufrufer (`write_held`)."""
        self.feed, self.emb, self.ctx = set_feed, emb, ctx
        self.struktur_mass = struktur_mass
        self.bk = _engine_module(emb)
        self.norm_mass = engine_norm_mass(emb)
        self.ident = None if kennung is None else dict(kennung)
        self.n = {"geschrieben": 0, "schon_da": 0, "abgelehnt": 0, "gesperrt": 0}
        self.fehler, self.zeiten = [], []
        weg = self.bk is not None or self.ident is not None
        errs = [] if lock or not weg else feed_errors(set_feed)
        self.grund = lock or (None if weg else LOCK_FACE_AUDIT) or (
            f"set feed unusable: {'; '.join(errs)}" if errs else None)
        if self.grund is None and self.ident is not None:
            import bild_kern as _bk                            # noqa: PLC0415  im Worker-Prozess schon geladen
            self.grund = self._variant_reason(_bk.NO_IMAGE)
        self.ohne = kept_text(set_feed.get("herkunftsart") if isinstance(set_feed, dict) else art)
        if self.grund:
            _log.error(f"harvest {ctx.get('eid')}: NO reference set is written in this job — {self.grund}; "
                       f"{self.ohne}")

    def for_event(self, ctx, struktur_mass=None):
        """Herkunft (eid, kamera, ts, quelle, latten) und Struktur-Mass des naechsten Ereignisses setzen, wenn ein
        Job mit EINEM Schreibweg viele Ereignisse schreibt (Unbekannt-Pool, E3a-2). -> self"""
        self.ctx, self.struktur_mass = dict(ctx), struktur_mass
        return self

    def _refuse(self, text):
        """Einen Fund ohne Satz laut buchen (Log, Job-Antwort). -> None"""
        self.n["abgelehnt"] += 1
        if len(self.fehler) < ERRORS_KEPT:
            self.fehler.append(text)
        _log.error(f"harvest {self.ctx.get('eid')}: reference set not written — {text}; {self.ohne}")

    def write(self, frame, fc, aligned, shot):
        """Den Satz eines gespeicherten Gesichts schreiben (Reihenfolge a bis e im Kopf).
        shot: nr, bildzeit, leinwand, datei, werte. -> ref_id oder None (gesperrt oder abgelehnt, laut)"""
        if self.grund:
            self.n["gesperrt"] += 1
            return None
        t0 = time.perf_counter()
        from core import refquelle as _rq                       # noqa: PLC0415
        try:
            parts, source = self._build(frame, fc, aligned, shot)
            if self.grund:                                      # Variante weicht ab (laut gemeldet)
                self.n["gesperrt"] += 1
                return None
            r = _rq.write_set({"data_dir": self.feed["data_dir"]}, parts, source, STATUS,
                              reason=self.feed["herkunftsart"])
        except (_rq.RefquelleError, RuntimeError, ValueError) as e:
            self._refuse(f"{type(e).__name__}: {e}")
            return None
        self.n["geschrieben" if r["neu"] else "schon_da"] += 1
        self.zeiten.append(time.perf_counter() - t0)
        return r["ref_id"]

    def write_held(self, frame, box, kps, shot):
        """Eingang des Workers (E3a-3; Fix 0.1.1.013 F3, Speichern ohne Rechnung): der gehaltene Sieger-Frame als BGR
        mit Kommazahl-Box und fuenf Punkten; shot: nr, bildzeit, datei, graph (die Zahlen der Erkennung nach
        GRAPH_MEASURES und der Fingerabdruck der r-Stufe, vom Aufrufer uebergeben). Gerechnet wird nur Bildarbeit.
        -> ref_id oder None (gesperrt oder abgelehnt, laut)"""
        fund = types.SimpleNamespace(bbox=[float(v) for v in box], kps=kps)
        return self.write(frame, fund, None, dict(shot, leinwand=None))

    def _variant_reason(self, no_image):
        """Die Variante des Job-Felds gegen die Kennung halten (Ernte nach der ersten Kennung, Worker beim Anlegen).
        -> Grund der Sperre oder None"""
        want = self.feed["image_variante"] or no_image
        if self.ident["image_variante"] == want:
            return None
        return (f"image variant of the job field ({want}) differs from the engine identity "
                f"({self.ident['image_variante']})")

    def _fingerprint(self, b112):
        """Teil b: Fingerabdruck und Norm aus den PNG-Bytes (fingerprint_from_112), danach die Kennung (einmal je Job).
        -> (Fingerabdruck float32 L2, Norm oder None, Grund ohne Norm)"""
        fp, norm, ohne = fingerprint_from_112(self.emb, self.norm_mass, b112)
        if self.ident is None:
            self.ident = self.bk.engine_identity(self.emb)
            self.grund = self._variant_reason(self.bk.NO_IMAGE)
            if self.grund:
                _log.error(f"harvest {self.ctx.get('eid')}: NO further reference set in this job — "
                           f"{self.grund}")
        return fp, norm, ohne

    def _build(self, frame, fc, aligned, shot):
        """Teile und Quelle eines Satzes. -> (parts, source); ValueError, wenn ein Teil nicht entsteht"""
        kps = getattr(fc, "kps", None)
        if kps is None:
            raise ValueError("the finding has no five face points, no 112 crop can be cut")
        if aligned is None:
            from core import ernte as _ern                    # noqa: PLC0415
            aligned = _ern.align112(frame, kps)
        b112 = _png(aligned)
        graph = shot.get("graph")
        if graph is None:                                       # Ernte: erst Bild, dann Zahl
            fp, norm, ohne = self._fingerprint(b112)
        else:                                                   # Worker (F3): die Zahl der Erkennung, keine Rechnung
            import numpy as np                                # noqa: PLC0415
            fp = None if graph.get("fingerabdruck") is None else np.asarray(graph["fingerabdruck"], np.float32).ravel()
        x1, y1, x2, y2 = (float(v) for v in fc.bbox)
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        half = float(self.feed["profil_faktor"]) * max(x2 - x1, y2 - y1) / 2.0
        quadrat = [cx - half, cy - half, cx + half, cy + half]
        profil, (a1, b1, _a2, _b2) = _cut(frame, *quadrat)
        if profil is None:
            raise ValueError("the profile square lies outside the frame")
        from core.livewache import person_region as _region   # noqa: PLC0415  die eine Regel
        h, w = frame.shape[:2]
        bereich = [float(v) for v in _region(fc.bbox, w, h)]
        person, (p1, q1, p2, q2) = _cut(frame, *bereich)
        parts = {"rechen112": b112, "fingerabdruck": fp, "profil": _png(profil), "profil_endung": ".png"}
        if person is None:
            parts["person_fehlt"] = PERSON_MISSING
        else:
            parts["person"] = _png(person)
        geo = {"box": [x1 - a1, y1 - b1, x2 - a1, y2 - b1],
               "punkte": [[float(p[0]) - a1, float(p[1]) - b1] for p in kps],
               "versatz": [a1, b1], "profil_faktor": float(self.feed["profil_faktor"]),
               "profil_quadrat": quadrat, "person_bereich": bereich,
               "person_ausschnitt": None if person is None else [p1, q1, p2, q2]}
        messwerte = self._graph_measures(graph) if graph is not None else self._measures(shot, norm, ohne)
        source = {"rechenwerk": dict(self.ident), "herkunft": self._origin(frame, shot), "geometrie": geo,
                  "messwerte": messwerte, "latten": dict(self.ctx.get("latten") or {})}
        return parts, source

    def _origin(self, frame, shot):
        """Die Herkunft zur Schreibzeit (Konzept Abschnitt 2 d); gemessen_an: Ernte am CPU-Bild, Worker (F3) am
        Rechengraphen, die Werte aus core.refquelle.satz.MEASURED_ON. -> dict"""
        from core.refquelle.satz import MEASURED_ON as _gemessen   # noqa: PLC0415  wie der Import in write
        cpu_bild, rechengraph = _gemessen
        h, w = frame.shape[:2]
        datei = bool(self.ctx.get("quelle"))
        clip = {"art": CLIP_FILE if datei else CLIP_FRIGATE,
                "startzeit_herkunft": UNKNOWN if datei else CLIP_FRIGATE}
        worker = shot.get("graph") is not None
        if worker:
            clip["pixelweg"] = PIXEL_WORKER                    # E3a-3, Entscheid 7
        return {"ereignis_id": self.ctx.get("eid"), "kamera": self.ctx.get("kamera"),
                "clip_quelle": clip,
                "ereignis_start": _num(self.ctx.get("ts")), "bildzeit": _num(shot["bildzeit"]),
                "bildnummer": int(shot["nr"]),
                "vollbild": [w, h], "leinwand": _pair(shot["leinwand"]), "lauf_id": self.feed.get("lauf_id"),
                "herkunftsart": self.feed["herkunftsart"],
                "software_version": self.feed["software_version"], "quelle": "kamerabild",
                "gemessen_an": rechengraph if worker else cpu_bild, "ausschnitt_name": shot["datei"]}

    def _cpu_ids(self):
        """Die Kennungen der Messungen am CPU-Bild (CPU_MEASURES), fuer Ernte und Worker an einer Stelle
        (Nachtrag E3a-3). -> dict Name -> Kennung"""
        from core import guete as _guete                       # noqa: PLC0415
        from core.registry import MODELL_VERTRAG as _mv        # noqa: PLC0415
        datei = {v["task"]: v["datei"] for v in _mv.values() if v.get("task")}
        rw = {k: self.ident[k] for k in ("rechenweg", "image_variante", "geraet", "bibliothek")}
        return {"kopfwinkel": dict(rw, modell=datei.get("landmark_3d_68", UNKNOWN)),
                "guete_t": {"modell": os.path.basename(_guete.PFAD_T), "ausschnitt": CUT_112},
                "guete_e": {"modell": os.path.basename(_guete.PFAD_E), "ausschnitt": CUT_NARROW},
                "schaerfe": {"verfahren": "Laplace-Varianz", "ausschnitt": CUT_NARROW}}

    def _measures(self, shot, norm, ohne):
        """Die Messwerte von damals, je mit Kennung (Entscheid 4). -> dict Name -> {wert, kennung}"""
        from core.registry import MODELL_VERTRAG as _mv        # noqa: PLC0415
        datei = {v["task"]: v["datei"] for v in _mv.values() if v.get("task")}
        rw = {k: self.ident[k] for k in ("rechenweg", "image_variante", "geraet", "bibliothek")}
        cpu = self._cpu_ids()
        pose_mod = sys.modules.get("pose_wache")
        pose_name = (os.path.basename(os.path.dirname(pose_mod.MODELL_STD[0]))
                     if pose_mod is not None and getattr(pose_mod, "MODELL_STD", None) else UNKNOWN)
        w = {k: (_num(v) if k != "kopfwinkel" else None if v is None else [float(x) for x in v])
             for k, v in shot["werte"].items()}
        nk = dict(self.ident)
        if norm is None:
            nk["grund"] = ohne
        enge = CUT_NARROW
        return {
            "detektion": {"wert": w["det"], "kennung": dict(rw, modell=datei.get("detection", UNKNOWN),
                                                           leinwand=_pair(shot["leinwand"]))},
            "kopfwinkel": {"wert": w["kopfwinkel"], "kennung": cpu["kopfwinkel"]},
            "norm": {"wert": norm, "kennung": nk},
            "guete_t": {"wert": w["guete_t"], "kennung": cpu["guete_t"]},
            "guete_e": {"wert": w["guete_e"], "kennung": cpu["guete_e"]},
            "kopfhaltung": {"wert": w["kopfhaltung"], "kennung": {"modell": pose_name,
                                                                 "ausschnitt": "Personenbereich"}},
            "struktur": {"wert": w["struktur"], "kennung": {
                "modell": getattr(type(self.struktur_mass), "MODELL_DATEI", None) or UNKNOWN,
                "ausschnitt": enge}},
            "schaerfe": {"wert": w["schaerfe"], "kennung": cpu["schaerfe"]},
            "helligkeit": {"wert": w["helligkeit"], "kennung": {"verfahren": "Graustufen-Mittel",
                                                               "ausschnitt": enge}}}

    def _graph_measures(self, graph):
        """Die Messwerte eines Worker-Satzes (Fix 0.1.1.013 F3, Entscheid 3): die Zahlen der Erkennung (GRAPH_MEASURES)
        wie uebergeben, je einmal mit der Kennung des Rechengraphen; der Kopfwinkel auf eine Nachkommastelle wie
        core.ernte; fehlt ein Wert, steht der Grund in seiner Kennung. -> dict Name -> {wert, kennung}"""
        from core import guete as _guete                       # noqa: PLC0415
        from core.registry import MODELL_VERTRAG as _mv        # noqa: PLC0415
        datei = {v["task"]: v["datei"] for v in _mv.values() if v.get("task")}
        rw = {k: self.ident[k] for k in ("image_variante", "geraet", "bibliothek")}
        rw["rechenweg"] = GRAPH_WAY
        lmk = datei.get("landmark_3d_68", UNKNOWN)
        modelle = {"score": self.ident["modell"], "detektion": datei.get("detection", UNKNOWN),
                   "guete_e": os.path.basename(_guete.PFAD_E), "guete_t": os.path.basename(_guete.PFAD_T),
                   "norm": self.ident["modell"], "front": lmk, "kopfwinkel": lmk}
        aus = {}
        for k in GRAPH_MEASURES:
            v = graph.get(k)
            kennung = dict(rw, **({"modell": modelle[k]} if k in modelle
                                  else {"verfahren": "Laplace-Varianz, Leinwand der fd-Stufe"}))
            if v is None:
                kennung["grund"] = NOT_MEASURED
            aus[k] = {"wert": None if v is None else [round(float(x), 1) for x in v] if k == "kopfwinkel"
                      else _num(v), "kennung": kennung}
        return aus

    def summary(self):
        """Die Bilanz des Schreibwegs fuer die Job-Antwort (z["refquelle"] in core/ernte).
        -> dict aktiv, grund, Zaehler, Fehlertexte, Zeit je Satz in Millisekunden"""
        ms = [round(s * 1000.0, 1) for s in self.zeiten]
        return {"aktiv": self.grund is None, "grund": self.grund, **self.n, "fehler": list(self.fehler),
                "zeit_ms_mittel": round(sum(ms) / len(ms), 1) if ms else None,
                "zeit_ms_max": max(ms) if ms else None}
