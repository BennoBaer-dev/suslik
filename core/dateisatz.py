"""core/dateisatz — der Datei-Weg der Referenz-Quelle: aus einer Bilddatei (Foto-Upload, Frigate-Import) ein Satz.

HERKUNFT: Bauplan analysen/bauplan_refquelle_einbau.md, Stufe E3 Punkt 1, Schnitt E3a-4 (J10, Eigentuemer
08.10.2026 08:41:39 „ja zu beiden"; J6 mit der Ergaenzung zu O559 (1)); Entscheide 7 (Nachmessung am CPU-Zuschnitt,
wie im Nachtrag E3a-3 gebaut), 11 (Kandidaten sind Saetze), 16 (die Leser des Bestands sehen die neue Referenz erst
mit E3b), 21 (ref_id = Pruefsumme der 112er-Bytes, „schon da" heisst schon da); Stufe E2 Punkt 1 und Konzept
analysen/konzept_referenzquelle.md Abschnitt 2 c (Datei-Weg: die Originaldatei ist das Profilbild; Faktor,
Verfahren und Leinwand stehen in quelle.json; Box und Punkte in Koordinaten der Originaldatei).

ZWECK: der Hintergrund-Job `dateisatz` des Worker-Dienstes (worker_dienst._hintergrund) ruft `job`. Er nimmt eine
Datei unter dem Datenordner, sucht die Gesichter ueber den Bild-Weg der Engine (face_audit.Embedder() im
Dienst-Prozess liefert den Engine-Adapter bild_kern.EngineEmbedder), nimmt das groesste, misst es am CPU-Zuschnitt
nach (worker_kern.Bildvorrat._nachmessen, dieselben Messfunktionen wie die Worker-Saetze), schreibt den Satz ueber
core.harvest_set (SetWriter mit dem Datei-Weg als `_build`, also derselbe Schreibweg, dieselbe Sperre J6, derselbe
Fingerabdruck aus den 112er-Bytes) und bindet ihn ueber core.uebernahme.in_den_bestand an die Person (Status
referenz). Der Dienst baut den Auftrag in verifyd.Service.upload_referenz (Upload und Import); `upload_ablegen`
legt die Bytes eines Uploads unter state/upload/ ab.

REIHENFOLGE JE DATEI:
  1  Pfad pruefen (unter dem Datenordner des Job-Felds, Endung aus core.registry.BILD_ENDUNGEN), Bytes lesen, BGR;
  2  vergroessern wie der Bild-Weg der Engine fuer ein Einzelbild (bild_kern.EngineEmbedder.embed: kurze Kante
     mindestens KURZE_KANTE_MIN mit INTER_CUBIC), Gesichter suchen auf der Leinwand des Engine-Adapters (det 320);
  3  das groesste Gesicht (Flaeche der Box); mehrere stehen laut im Ergebnis und im Log;
  4  Nachmessung am CPU-Zuschnitt des vergroesserten Bildes (Guete e und t, Schaerfe, Kopfwinkel), ihr 112er-Warp
     ist der des Satzes;
  5  Satz mit Status kandidat ueber den Schreibweg, dann die Bindung (Person, aktiv, Status referenz).
Ohne erkennbares Gesicht entsteht kein Satz (eine Referenz ohne Fingerabdruck koennte nie erkennen); das Ergebnis
und das Log sagen es. Die Datei im Staging bleibt liegen (geloescht wird hier nichts).

DER RECHENTEIL (Bauauftrag E4-4a, Bauplan Stufe E4 Punkt 3): Schritte 2 bis 4 und der 112er mit dem Fingerabdruck
stehen an einer Stelle, `bild_lesen` (Bytes dekodieren, vergroessern) und `rechnen` (Suche, groesstes Gesicht,
Nachmessung, 112er, Fingerabdruck ueber die Fingerabdruck-Rechnung des Aufrufers). Der Job ruft sie mit
DateiSetWriter._fingerprint (Kennung und Variantenpruefung wie bisher), die Zeilenkarte des Pruefstands
(tools/k3_anker/zeilenkarte.py) mit core.harvest_set.fingerprint_from_112; ein zweiter Rechenweg entsteht nicht. Die
Nachrechnung des Altbestands, fuer die der Rechenteil herausgeloest wurde, liegt seit Fix 0.1.1.013 Stufe F1 im Archiv
(archiv/nachrechnung/); den Rechenschritt fuer fehlende Zahlen im Migrationsskript bringt Stufe F5.

EHRLICHE GRENZEN:
  - Die Regel „kurze Kante mindestens 224, INTER_CUBIC" steht im Haus schon zweimal (face_audit.Embedder.embed,
    bild_kern.EngineEmbedder.embed) und hier ein drittes Mal, weil der Adapter das vergroesserte Bild nicht
    herausgibt; aendert sich dort die Regel, muss sie hier mit.
  - Ein Satz des Datei-Wegs traegt keinen Personenausschnitt (Entscheid 2 kennt nur Kamerabilder): die Datei ist
    als Ganzes das Profilbild; der Grund steht in quelle.json.
  - Geprueft wird die Form der Datei (lesbar, Endung), nicht ob das Gesicht die gemeinte Person zeigt.
"""
import os
import time
import types
import uuid

from core import harvest_set as _hs
from core import logbuch as _logbuch
from core.registry import BILD_ENDUNGEN as _BILD_ENDUNGEN

_log = _logbuch.logger(__name__)

ARTEN = (_hs.ART_UPLOAD, _hs.ART_FRIGATE_IMPORT)
UPLOAD_DIR = os.path.join("state", "upload")
KURZE_KANTE_MIN = 224.0                   # bild_kern.EngineEmbedder.embed (Konzept Abschnitt 2 c)
VERFAHREN = ("cv2.resize INTER_CUBIC to a short edge of at least 224 px "
             "(the single-image way of bild_kern.EngineEmbedder.embed)")
PERSON_FILE = "file way: the original file is kept whole as the profile picture (no person area)"
NO_FACE = "no face recognisable in the image"             # Grund des Rechenteils ohne Fund (Job, Zeilenkarte)
NO_POINTS = "the face has no five face points, no 112 crop can be cut"
# Erkennung des Bildformats an den ersten Bytes (Upload ohne Dateinamen); die Endungen stehen in BILD_ENDUNGEN.
_MAGIC = ((b"\xff\xd8\xff", ".jpg"), (b"\x89PNG\r\n\x1a\n", ".png"))


def endung(daten):
    """Das Bildformat einer hochgeladenen Datei an ihren ersten Bytes erkennen (JPEG, PNG, WEBP).
    -> Endung aus core.registry.BILD_ENDUNGEN oder None (kein bekanntes Bildformat)"""
    if not isinstance(daten, bytes):
        return None
    for kopf, ext in _MAGIC:
        if daten.startswith(kopf):
            return ext
    if len(daten) >= 12 and daten[:4] == b"RIFF" and daten[8:12] == b"WEBP":
        return ".webp"
    return None


def upload_ablegen(data_dir, daten):
    """Die Bytes eines Foto-Uploads unveraendert unter state/upload/ ablegen (atomar, eindeutiger Name).
    -> (Pfad, None) oder (None, Grund), wenn die Bytes kein bekanntes Bildformat sind"""
    from core import atomar as _atomar                      # noqa: PLC0415
    ext = endung(daten)
    if ext is None:
        return None, "the upload is not a JPEG, PNG or WEBP image"
    name = f"upload_{time.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    pfad = os.path.join(data_dir, UPLOAD_DIR, name)
    _atomar.bytes_schreiben(pfad, daten)
    return pfad, None


def _unter(data_dir, pfad):
    """-> der echte Pfad, wenn er unter dem Datenordner liegt (realpath, auch ueber Verweise), sonst None."""
    basis = os.path.realpath(str(data_dir))
    echt = os.path.realpath(str(pfad))
    return echt if echt.startswith(basis + os.sep) else None


class DateiSetWriter(_hs.SetWriter):
    """Der Schreibweg der Ernte mit dem Datei-Weg als Teil-Bau: Profilbild = Originaldatei, Quelle datei,
    Geometrie in Koordinaten der Originaldatei, Faktor, Verfahren und Leinwand in quelle.json."""

    def _build(self, _frame, fc, _aligned, shot):
        """Teile und Quelle eines Satzes auf dem Datei-Weg; 112er, Fingerabdruck und Norm hat der Rechenteil
        (`rechnen`, mit _fingerprint dieses Schreibwegs) schon gerechnet. shot: daten, endung, faktor, leinwand,
        vollbild, datei, det, frigate, werte, gruende, b112, fp, norm, ohne. -> (parts, source)"""
        kps = fc.kps
        b112, fp, norm, ohne = shot["b112"], shot["fp"], shot["norm"], shot["ohne"]
        f = float(shot["faktor"])
        parts = {"rechen112": b112, "fingerabdruck": fp, "profil": shot["daten"],
                 "profil_endung": shot["endung"], "person_fehlt": PERSON_FILE}
        geo = {"box": [float(v) / f for v in fc.bbox], "punkte": [[float(p[0]) / f, float(p[1]) / f] for p in kps]}
        herkunft = {"herkunftsart": self.feed["herkunftsart"], "quelle": "datei", "gemessen_an": "cpu_bild",
                    "software_version": self.feed["software_version"], "lauf_id": self.feed.get("lauf_id"),
                    "ausschnitt_name": shot["datei"], "vollbild": list(shot["vollbild"]),
                    "leinwand": list(shot["leinwand"])}
        if shot.get("frigate"):
            herkunft["frigate"] = dict(shot["frigate"])
        source = {"rechenwerk": dict(self.ident), "herkunft": herkunft, "geometrie": geo,
                  "datei_weg": {"faktor": f, "verfahren": VERFAHREN, "leinwand": list(shot["leinwand"])},
                  "messwerte": self._datei_measures(shot, norm, ohne)}
        return parts, source

    def _datei_measures(self, shot, norm, ohne):
        """Die Messwerte eines Datei-Satzes je mit Kennung: Detektion, Norm aus den 112er-Bytes, dazu Guete e und t,
        Schaerfe und Kopfwinkel aus der Nachmessung (fehlt ein Wert, steht sein Grund in der Kennung). -> dict"""
        from core.registry import MODELL_VERTRAG as _mv        # noqa: PLC0415
        datei = {v["task"]: v["datei"] for v in _mv.values() if v.get("task")}
        rw = {k: self.ident[k] for k in ("rechenweg", "image_variante", "geraet", "bibliothek")}
        nk = dict(self.ident)
        if norm is None:
            nk["grund"] = ohne
        aus = {"detektion": {"wert": float(shot["det"]),
                             "kennung": dict(rw, modell=datei.get("detection", _hs.UNKNOWN),
                                             leinwand=list(shot["leinwand"]))},
               "norm": {"wert": norm, "kennung": nk}}
        cpu, werte, gruende = self._cpu_ids(), shot["werte"], shot.get("gruende") or {}
        for k in _hs.CPU_MEASURES:
            v, kennung = werte.get(k), dict(cpu[k])
            if v is None:
                kennung["grund"] = gruende.get(k) or _hs.NOT_MEASURED
            aus[k] = {"wert": None if v is None else [float(x) for x in v] if k == "kopfwinkel" else float(v),
                      "kennung": kennung}
        return aus


def _ergebnis(datei, t0, **kw):
    """-> das Ergebnis eines Jobs mit allen Feldern (fehlende None), Zeit in Millisekunden"""
    aus = {"datei": datei, "ref_id": None, "satz_neu": None, "bindung": None, "gesichter": None,
           "fehlende_werte": {}, "grund": None, "fehler": None}
    aus.update(kw)
    aus["zeit_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
    return aus


def _ablehnen(datei, t0, grund, fehler=False, **kw):
    """Eine Datei ohne Satz laut buchen (WARNING, bei einem Fehler ERROR). -> Ergebnis"""
    (_log.error if fehler else _log.warning)(f"file reference {datei}: NO reference set — {grund}")
    return _ergebnis(datei, t0, **({"fehler": grund} if fehler else {"grund": grund}), **kw)


def _eingang(auftrag):
    """Job-Feld, Person, Herkunftsart, Frigate-Angaben und Pfad pruefen. -> (feed, person, frigate, echter Pfad,
    None) oder (..., Grund)"""
    feed, person, frigate = auftrag.get(_hs.FEED_FIELD), auftrag.get("person"), auftrag.get("frigate")
    errs = _hs.feed_errors(feed)
    if not errs and feed["herkunftsart"] not in ARTEN:
        errs.append(f"herkunftsart {feed['herkunftsart']!r} is not a file way ({', '.join(ARTEN)})")
    if errs:
        return feed, person, frigate, None, f"set feed unusable: {'; '.join(errs)}"
    if not (isinstance(person, str) and person.strip()):
        return feed, person, frigate, None, "no person given"
    if (feed["herkunftsart"] == _hs.ART_FRIGATE_IMPORT) != isinstance(frigate, dict) or (
            isinstance(frigate, dict) and not all(isinstance(frigate.get(k), str) and frigate[k]
                                                  for k in ("person", "datei"))):
        return feed, person, frigate, None, "a Frigate import needs the Frigate person and file (and only it)"
    echt = _unter(feed["data_dir"], auftrag.get("pfad") or "")
    if echt is None:
        return feed, person, frigate, None, "the file lies outside the data folder"
    if os.path.splitext(echt)[1].lower() not in _BILD_ENDUNGEN:
        return feed, person, frigate, None, f"the file ending is not one of {', '.join(_BILD_ENDUNGEN)}"
    return feed, person, frigate, echt, None


def bild_lesen(daten):
    """Die Bytes einer Bilddatei dekodieren und fuer die Suche vergroessern (Schritt 2, erster Teil des Rechenteils;
    der Job dateisatz und die Zeilenkarte des Pruefstands rufen ihn vor `rechnen`).
    -> (Original BGR, vergroessertes BGR, Faktor); dreimal None, wenn die Bytes kein lesbares Bild sind"""
    import cv2                                                # noqa: PLC0415
    import numpy as np                                        # noqa: PLC0415
    img = cv2.imdecode(np.frombuffer(daten, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None, None, None
    h, w = img.shape[:2]
    faktor = max(1.0, KURZE_KANTE_MIN / min(h, w))
    gross = (cv2.resize(img, (round(w * faktor), round(h * faktor)), interpolation=cv2.INTER_CUBIC)
             if faktor > 1.0 else img)
    return img, gross, faktor


def rechnen(gross, emb, fingerprint):
    """Der Rechenteil des Datei-Wegs auf dem vergroesserten Bild (Schritte 2 bis 4 und Teil b des Schreibwegs), eine
    Stelle fuer den Job dateisatz und die Zeilenkarte des Pruefstands (Bauauftrag E4-4a; die Nachrechnung liegt seit
    Fix 0.1.1.013 F1 im Archiv): Gesichter suchen
    (Leinwand des Engine-Adapters), das groesste (Flaeche der Box), Nachmessung am CPU-Zuschnitt
    (worker_kern.Bildvorrat._nachmessen), 112er (deren Warp, sonst core.ernte.align112), Fingerabdruck und Norm aus den
    112er-Bytes ueber fingerprint(b112) -> (Fingerabdruck, Norm oder None, Grund ohne Norm).
    -> dict gesichter, face, leinwand, aligned, werte, gruende, b112, fp, norm, ohne; dazu hoechstens eines von grund
    (kein Gesicht), fehler (der Adapter nennt keine Leinwand) oder satz_fehler (112er oder Fingerabdruck, Text
    „<Ausnahme>: <Grund>", die Ausnahme selbst in ausnahme); ohne Befund alle None"""
    aus = dict.fromkeys(("face", "leinwand", "aligned", "b112", "fp", "norm", "ohne", "grund", "fehler",
                         "satz_fehler", "ausnahme"))
    aus.update(gesichter=0, werte={}, gruende={})
    faces = emb.detektieren(gross)[0]
    if not faces:
        aus["grund"] = NO_FACE
        return aus
    face = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
    aus.update(gesichter=len(faces), face=face)
    leinwand = getattr(emb, "_det_size", None)
    if not (isinstance(leinwand, tuple) and len(leinwand) == 2):
        aus["fehler"] = "the engine adapter names no detector canvas"
        return aus
    aus["leinwand"] = leinwand
    aligned = None
    if face.kps is not None:
        import worker_kern as _wk                             # noqa: PLC0415  die Nachmessung der Worker-Saetze
        fund = {"box": [float(v) for v in face.bbox], "kps": face.kps}
        aligned, aus["werte"], aus["gruende"] = _wk.Bildvorrat._nachmessen(gross, fund, emb)
    try:
        if face.kps is None:
            raise ValueError(NO_POINTS)
        if aligned is None:
            from core import ernte as _ern                    # noqa: PLC0415
            aligned = _ern.align112(gross, face.kps)
        aus["aligned"] = aligned
        aus["b112"] = _hs._png(aligned)
        aus["fp"], aus["norm"], aus["ohne"] = fingerprint(aus["b112"])
    except (RuntimeError, ValueError) as e:                   # wie bisher im Schreibweg (SetWriter.write)
        aus["satz_fehler"], aus["ausnahme"] = f"{type(e).__name__}: {e}", e
    return aus


def job(auftrag, emb_holen):
    """Der Job `dateisatz`: aus der Datei des Auftrags einen Satz schreiben und an die Person binden (Reihenfolge
    1 bis 5 im Kopf); emb_holen ist die Fabrik des Rechenwerks und wird erst nach der Eingangspruefung gerufen.
    -> Ergebnis: datei, ref_id, satz_neu, bindung, gesichter, fehlende_werte, grund oder fehler, zeit_ms"""
    t0 = time.perf_counter()
    datei = os.path.basename(str(auftrag.get("pfad") or "")) or "?"
    feed, person, frigate, echt, grund = _eingang(auftrag)
    if grund:
        return _ablehnen(datei, t0, grund, fehler=True)
    with open(echt, "rb") as fh:
        daten = fh.read()
    img, gross, faktor = bild_lesen(daten)
    if img is None:
        return _ablehnen(datei, t0, "the file is not a readable image")
    try:
        emb = emb_holen()
    except Exception as e:                                    # noqa: BLE001  laut als Fehler (wie Bildvorrat)
        return _ablehnen(datei, t0, f"no engine for the reference set ({type(e).__name__}: {e})", fehler=True)
    weg = DateiSetWriter(feed, emb, {"eid": datei, "kamera": None, "ts": None, "quelle": echt})
    if weg.grund:
        return _ablehnen(datei, t0, weg.grund, fehler=True)
    r = rechnen(gross, emb, weg._fingerprint)
    if r["grund"]:
        return _ablehnen(datei, t0, r["grund"], gesichter=0)
    if r["gesichter"] > 1:
        _log.warning(f"file reference {datei}: {r['gesichter']} faces found, the largest one is taken")
    if r["fehler"]:
        return _ablehnen(datei, t0, r["fehler"], fehler=True)
    if r["satz_fehler"]:
        weg._refuse(r["satz_fehler"])                         # wie bisher im Schreibweg: ERROR, Zaehler abgelehnt
    face, gruende = r["face"], r["gruende"]
    shot = {"daten": daten, "endung": os.path.splitext(echt)[1].lower(), "faktor": faktor,
            "leinwand": r["leinwand"], "vollbild": [img.shape[1], img.shape[0]], "datei": datei,
            "det": float(face.det_score), "frigate": frigate, "werte": r["werte"], "gruende": gruende,
            "b112": r["b112"], "fp": r["fp"], "norm": r["norm"], "ohne": r["ohne"]}
    rid = None if r["satz_fehler"] else weg.write(
        gross, types.SimpleNamespace(bbox=[float(v) for v in face.bbox], kps=face.kps), r["aligned"], shot)
    if rid is None:
        return _ablehnen(datei, t0, "; ".join(weg.fehler) or weg.grund or "the set was not written",
                         fehler=True, gesichter=r["gesichter"])
    from core import refquelle as _rq                         # noqa: PLC0415
    from core import uebernahme as _ue                        # noqa: PLC0415
    art = feed["herkunftsart"]
    try:
        gebunden = _ue.in_den_bestand(feed["data_dir"], [rid], person,
                                      f"{art}{' run ' + str(feed['lauf_id']) if feed.get('lauf_id') else ''}")
    except (ValueError, _rq.RefquelleError) as e:
        return _ablehnen(datei, t0, f"the set {rid} was not bound to the person: {e}", fehler=True,
                         ref_id=rid, satz_neu=bool(weg.n["geschrieben"]), gesichter=r["gesichter"])
    bindung = "neu" if rid in gebunden["neu"] else "schon_da"
    if gruende:
        _log.warning(f"file reference {datei}: re-measurement on the CPU cut incomplete — "
                     + "; ".join(f"{k} ({g})" for k, g in sorted(gruende.items())))
    _log.info(f"file reference {datei}: set {rid} ({'written' if weg.n['geschrieben'] else 'already there'}) "
              f"bound to the person as reference ({bindung})")
    return _ergebnis(datei, t0, ref_id=rid, satz_neu=bool(weg.n["geschrieben"]), bindung=bindung,
                     gesichter=r["gesichter"], fehlende_werte=dict(gruende))
