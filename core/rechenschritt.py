"""core/rechenschritt — der Rechenschritt des Migrationsskripts: fehlende Zahlen eines Satzes aus seinem Profilbild.

HERKUNFT: Bauplan analysen/bauplan_fix_0113.md, Entscheid 5 und Stufe F5 Punkte 2 und 3 (X2, X7, X12, X20), Konzept
analysen/konzept_fix_0113.md Abschnitt 4.3; der Eigentuemer 12.10.2026 07:17:42 „Wenn sie noch nicht nach neu migriert
sind, muss ein Migrationsskript gestartet werden, das die Gesichter nach neu migriert und gegebenenfalls Werte
nachberechnet. Das muss alles in dem Migrationsskript erfolgen.", 09:25:15 „dann cpu" und 07:25:05 „es sind ja nur daten
aus den gesichter bibliotek die fehlen". Material: _satz und job der archivierten Nachrechnung
(archiv/nachrechnung/nachrechnung.py). Eigene Datei, weil das Modul core/refquelle nichts rechnet.

ZWECK: `anlernen.py umzug` ruft `lauf` nach dem gruenen Umzug oder bei schon umgezogenem Bestand, im eigenen Prozess vor
dem Worker-Start (der Dienst faehrt das Skript im Boot, verifyd.Service.referenzquelle_umzug_im_boot). Gerechnet wird
fuer jeden Satz der Auswahl core.refquelle.computable_sets (Profilbild da, kein Fingerabdruck, kein Vermerk des
Rechenschritts fuer dieses Modell); Quelle ist allein das Profilbild des Satzes.

JE SATZ: Profilbild ueber Lese-Stufe d (core.refquelle.read_image), dann der Rechenteil des Datei-Wegs
(core.dateisatz.bild_lesen und rechnen, Fingerabdruck ueber core.harvest_set.fingerprint_from_112), dann die
Vervollstaendigung im Modul (core.refquelle.complete_set: 112er, Fingerabdruck, Messwerte des Datei-Wegs mit der Kennung
des Rechenwerks, Herkunft, Geometrie in Koordinaten des Profilbilds, ref_id bleibt, Statuszeile referenz); ohne Gesicht
der Vermerk core.refquelle.note_no_face mit Kennung. Das Rechenwerk ist die Engine des Haus-Wegs fuer die CPU ueber
bild_kern.Fabrik (Muster tools/k3_anker/zeilenkarte.py rechenwerk), gebaut erst, wenn die Auswahl nicht leer ist.

STAND: die Standdatei core.refquelle.COMPUTE_STATE_FILE unter state/ (am Anfang mit offen = Zahl der Auswahl, dann
atomar nach jedem Satz: phase laeuft, fertig oder rot, gesamt, offen, erledigt, gerechnet, ohne_gesicht, schon_da,
fehler mit den ersten Gruenden, beginn, zeit, pid, modell); core.refquelle.migration_state liest allein sie fuer Log und
/health (Teil rechnung, Stufe F5 Punkt 6, N6: keine Katalog-Auswahl je Abfrage). Waehrend der Rechnung eine
INFO-Zeile im Minutentakt als Lebenszeichen, am Ende eine INFO-Zeile mit den Zahlen (gerechnet, ohne Gesicht, Fehler,
Sekunden). Ein Fehler des Rechenwerks ist eine ERROR-Zeile, der Stand wird rot, der Schritt endet mit Rueckgabe 1; der
Umzug bleibt gruen, der naechste Start rechnet weiter (der Satz ist der Stand: nur, was keine Zahl und keinen Vermerk
hat). Ein Fehler an einem Satz (Profilbild unlesbar, kein 112er, Satz abgelehnt) steht mit Grund im Stand und als
Vermerk Datenfehler mit gekuerztem Grund und Kennung am Satz (core.refquelle.note_data_failed, Stufe F5 Punkt 6, N4):
fuer dieses Modell wird er nicht wieder versucht, der Schritt geht weiter.

TEST-HILFE, nie Produktweg: steht SKIP_ENV auf „1", ueberspringt `anlernen.py umzug` den Rechenschritt mit einer
WARNING-Zeile (die Proben, die das echte Skript fahren, laden so kein Modell). Der Dienst setzt den Schalter nie.

EHRLICHE GRENZEN:
  - Gemessen ist die Dauer nur auf einem Image (0,45 s je Bild, Kopf der archivierten Nachrechnung, 11.10.2026); auf
    den anderen Images nicht (X20). Der Aufbau des Rechenwerks schreibt kein Lebenszeichen.
  - Die Zahl traegt die Kennung dieses Rechenwerks; der Worker auf der Karte liest sie als „fremd, gleiches Modell"
    (Nachtrag 4: das Modell-Sieb vergleicht die Pruefsumme der Quelldatei).
  - Ein Satz, der an seinen Daten scheitert, bleibt fuer dieses Modell ohne Zahl (Vermerk); erst ein anderes Modell
    rechnet ihn wieder. Lehnt das Modul den Vermerk ab (etwa Satz nicht sichtbar), wird er beim naechsten Start wieder
    versucht und bleibt im Stand unter offen.
  - Die eine Frist migration_timeout_s des Dienstes deckt Umzug und Rechenschritt; endet sie, beendet der Dienst den
    Prozess, der Stand bleibt laeuft ohne lebenden Prozess (migration_state zeigt offen und abgebrochen).
"""
import argparse
import os
import tempfile
import time
import types

from core import dateisatz as _ds
from core import harvest_set as _hs
from core import logbuch as _logbuch
from core import refquelle as _rq

_log = _logbuch.logger(__name__)

SKIP_ENV = "SUSLIK_UMZUG_OHNE_RECHNUNG"      # Test-Hilfe der Proben (Kopf), nie Produktweg
LEBENSZEICHEN_S = 60.0                        # Takt der Lebenszeichen waehrend der Rechnung
FEHLER_GEZEIGT = 10                           # so viele Gruende fehlgeschlagener Saetze traegt der Stand
COMPUTED, NO_FACE, ALREADY, FAILED = "gerechnet", "ohne_gesicht", "schon_da", "fehler"
RC_GREEN, RC_RED = 0, 1


def engine_bauen(tmp):
    """Das Rechenwerk auf der CPU: Engine, Bild-Weg und face_audit.Embedder ueber bild_kern.Fabrik eingehaengt (Muster
    tools/k3_anker/zeilenkarte.py rechenwerk); Kompilate unter tmp.
    -> (Embedder, Fingerabdruck-Rechnung b112 -> (fp, norm, grund), Kennung des Rechenwerks)"""
    import bild_kern                                          # noqa: PLC0415  schwer, nur bei nicht leerer Auswahl
    import engine_cpu                                         # noqa: PLC0415
    import face_audit                                         # noqa: PLC0415
    from core.pfade import WURZEL                             # noqa: PLC0415
    a = argparse.Namespace(wurzel=WURZEL, ov_cache=os.path.join(tmp, "ov_cache"), out=os.path.join(tmp, "out"),
                           threads=1)
    engine = engine_cpu.Engine(a)
    bild_kern.Fabrik(lambda: bild_kern.BildRechner(engine), engine_cpu.GERAET).einhaengen()
    emb = face_audit.Embedder()
    norm_mass = _hs.engine_norm_mass(emb)
    return emb, (lambda b112: _hs.fingerprint_from_112(emb, norm_mass, b112)), bild_kern.engine_identity(emb)


def _quelle(r, img, faktor, kennung, version):
    """Die Felder fuer core.refquelle.complete_set aus dem Ergebnis von core.dateisatz.rechnen: Kennung, Herkunft (Quelle
    Datei, am CPU-Bild gemessen, Version), Geometrie in Koordinaten des Profilbilds, Datei-Weg, Messwerte wie der
    Datei-Weg (DateiSetWriter._datei_measures, die eine Stelle dieser Messwerte).
    -> dict rechenwerk, herkunft, geometrie, datei_weg, messwerte"""
    from core.refquelle.satz import MEASURED_ON, SOURCE_KINDS     # noqa: PLC0415  wie harvest_set._origin
    face, f = r["face"], float(faktor)
    shot = {"det": float(face.det_score), "werte": r["werte"], "gruende": r["gruende"], "leinwand": r["leinwand"]}
    traeger = types.SimpleNamespace(ident=dict(kennung))
    traeger._cpu_ids = lambda: _hs.SetWriter._cpu_ids(traeger)
    return {"rechenwerk": dict(kennung),
            "herkunft": {"quelle": SOURCE_KINDS[1], "gemessen_an": MEASURED_ON[0], "software_version": version,
                         "vollbild": [int(img.shape[1]), int(img.shape[0])], "leinwand": list(r["leinwand"])},
            "geometrie": {"box": [float(v) / f for v in face.bbox],
                          "punkte": [[float(p[0]) / f, float(p[1]) / f] for p in face.kps]},
            "datei_weg": {"faktor": f, "verfahren": _ds.VERFAHREN, "leinwand": list(r["leinwand"])},
            "messwerte": _ds.DateiSetWriter._datei_measures(traeger, shot, r["norm"], r["ohne"])}


def _satz(cfg, ref_id, rechnung, version):
    """Einen Satz rechnen und vervollstaendigen oder vermerken (Kopf: JE SATZ). Ein Fehler des Rechenwerks geht als
    Ausnahme hinaus. rechnung: (Embedder, Fingerabdruck-Rechnung, Kennung).
    -> (Art aus COMPUTED, NO_FACE, ALREADY, FAILED; Grund oder None)"""
    emb, fingerprint, kennung = rechnung
    bild = _rq.read_image(cfg, ref_id, "profil")
    daten = (bild or {}).get("daten")
    if bild is None or daten is None or bild.get("fehler"):
        return FAILED, ("the profile picture is not readable over read stage d ("
                        f"{(bild or {}).get('fehler') or (bild or {}).get('fehlt') or 'set not visible'})")
    img, gross, faktor = _ds.bild_lesen(daten)
    if gross is None:
        return FAILED, "the profile picture is not a readable image"
    r = _ds.rechnen(gross, emb, fingerprint)
    if r["fehler"] or isinstance(r["ausnahme"], RuntimeError):
        raise r["ausnahme"] or RuntimeError(r["fehler"])
    try:
        if r["grund"]:
            _rq.note_no_face(cfg, ref_id, kennung)
            return NO_FACE, None
        if r["satz_fehler"]:
            return FAILED, r["satz_fehler"]
        res = _rq.complete_set(cfg, ref_id, {"rechen112": r["b112"], "fingerabdruck": r["fp"]},
                               _quelle(r, img, faktor, kennung, version))
    except _rq.RefquelleError as e:
        return FAILED, f"RefquelleError: {e}"
    return (COMPUTED, None) if res["vervollstaendigt"] else (ALREADY, None)


def _write(path, stand):
    """Die Standdatei atomar schreiben (mit Zeit). -> None"""
    from core import atomar as _atomar                        # noqa: PLC0415
    stand["zeit"] = time.time()
    _atomar.json_schreiben(path, stand)


def _vermerken(cfg, ref_id, kennung, grund):
    """Einen Satzfehler als Rechen-Vermerk mit gekuerztem Grund an den Satz haengen (Stufe F5 Punkt 6, N4).
    -> True, wenn vermerkt; False, wenn das Modul ablehnt (dann steht die ERROR-Zeile schon im Log)"""
    try:
        _rq.note_data_failed(cfg, ref_id, kennung, grund)
    except _rq.RefquelleError:
        return False
    return True


def _schleife(cfg, offen, rechnung, stand, path):
    """Je Satz der Auswahl rechnen, den Stand nach jedem Satz schreiben, im Minutentakt ein Lebenszeichen.
    -> None; ein Fehler des Rechenwerks geht als Ausnahme hinaus"""
    version = os.environ.get("SUSLIK_VERSION") or _hs.UNKNOWN
    t0 = faellig = time.monotonic()
    for ref_id, _profil in offen:
        art, grund = _satz(cfg, ref_id, rechnung, version)
        vermerkt = art == FAILED and _vermerken(cfg, ref_id, rechnung[2], grund)
        stand[art] += 1
        stand["erledigt"] += 1
        if art != FAILED or vermerkt:                         # offen bleibt nur ein Satzfehler ohne Vermerk
            stand["offen"] -= 1
        if grund is not None and len(stand["fehler_gruende"]) < FEHLER_GEZEIGT:
            stand["fehler_gruende"].append({"ref_id": ref_id, "grund": grund})
        if grund is not None:
            _log.warning(f"reference source: compute step — set {ref_id} not computed ({grund}); "
                         + ("noted, it is not tried again for this model" if vermerkt
                            else "the note was refused, it is tried again at the next start"))
        _write(path, stand)
        if time.monotonic() - faellig >= LEBENSZEICHEN_S:
            faellig = time.monotonic()
            _log.info(f"reference source: compute step still running — {stand['erledigt']} of {stand['gesamt']} "
                      f"set(s) done after {time.monotonic() - t0:.0f} s")


def lauf(cfg, model, bauen=None):
    """Der Rechenschritt (Kopf dieser Datei) fuer das Modell model; bauen(tmp) baut das Rechenwerk (ohne Angabe
    engine_bauen dieses Moduls, zur Laufzeit gelesen: die Proben setzen eine Attrappe ein), gerufen nur bei nicht leerer
    Auswahl. -> RC_GREEN (fertig oder nichts zu rechnen) oder RC_RED (Fehler des Rechenwerks, Stand rot, Umzug
    unberuehrt)"""
    t0 = time.monotonic()
    path = os.path.join(str(cfg["data_dir"]), _rq.COMPUTE_STATE_FILE)
    offen = _rq.computable_sets(cfg, model)
    if not offen:
        if os.path.isfile(path):                              # ein alter Stand (rot, abgebrochen) gilt nicht mehr
            _write(path, {"phase": _rq.basis.COMPUTE_NONE, "gesamt": 0, "offen": 0, "erledigt": 0, "pid": os.getpid()})
        _log.info("reference source: compute step — no set without a fingerprint to compute")
        return RC_GREEN
    stand = {"phase": _rq.basis.COMPUTE_RUNNING, "gesamt": len(offen), "offen": len(offen), "erledigt": 0, COMPUTED: 0,
             NO_FACE: 0, ALREADY: 0, FAILED: 0, "fehler_gruende": [], "beginn": time.time(), "pid": os.getpid(),
             "modell": model}
    _write(path, stand)
    _log.info(f"reference source: compute step — {len(offen)} set(s) with a profile picture but without a fingerprint, "
              "computing their numbers on the CPU")
    try:
        with tempfile.TemporaryDirectory(prefix="suslik_rechenschritt_") as tmp:
            rechnung = (bauen or engine_bauen)(tmp)
            if rechnung[2].get("modell") != model:
                raise RuntimeError(f"the engine computes the model {rechnung[2].get('modell')!r}, not {model!r}")
            _schleife(cfg, offen, rechnung, stand, path)
    except Exception as e:                                    # noqa: BLE001  laut, Stand rot, Umzug bleibt gruen
        stand.update(phase=_rq.basis.COMPUTE_RED, grund=f"{type(e).__name__}: {e}")
        _write(path, stand)
        _log.error(f"reference source: compute step RED — the engine failed ({type(e).__name__}: {e}); "
                   f"{stand[COMPUTED]} computed, {stand[NO_FACE]} without face, {stand[FAILED]} error(s) before; the "
                   "migration stays green, recognition keeps the sets without numbers, the next start resumes")
        _rq.build_person_folders(cfg, follow=True)
        return RC_RED
    _rq.build_person_folders(cfg, follow=True)
    stand.update(phase=_rq.basis.COMPUTE_DONE, sekunden=round(time.monotonic() - t0, 1))
    _write(path, stand)
    (_log.warning if stand[FAILED] else _log.info)(
        f"reference source: compute step done — {stand[COMPUTED]} computed, {stand[NO_FACE]} without face, "
        f"{stand[FAILED]} error(s), {stand[ALREADY]} already complete, {stand['sekunden']} s")
    return RC_GREEN
