"""core/normlauf — DER gebuendelte Feature-Norm-Schritt des Lernlaufs (.518).

USER-GO 10.09.2026 („so bauen"), sein Fluss im Wortlaut: „Ernter startet ->
Worker parallel mit den fuenf leichten Achsen -> DANN die Normierung als EIN
gebuendelter Schritt -> dann die Abarbeitung."

WOZU. Die Feature-Norm ist die sechste Achse des einen Siebs
(core.kamerakalib.SIEB_ACHSEN) und die einzige, die SCRFD-Fehldetektionen mit
hohem det-Score von echten Klein-Gesichtern trennt. Gemessen wird sie mit einer
eigenen adaface-Session (face_audit.NormMass), deren ERSTBAU mit 2700 MB
gemessen ist (worker._NORMMASS_BAUSPITZE_MB). Bis .517 lag dieser Bau IM
Ernte-Job — und seit die Ernte mit K Abholern faehrt (C2, 05.09.), war damit
jeder der K Ernte-Plaetze potenziell ein 2,7-GB-Platz. Die Analyse-Plaetze
waren also nicht mehr gleich schwer, und der Speicherbedarf des Laufs haing an
der Zahl der Abholer statt an der Arbeit.

Seit .518 sieben im Ernte-Job die FUENF leichten Achsen (kamerakalib
.ERNTE_ACHSEN), und die Norm misst dieser eine Job danach: EINE Session, EIN
Platz, alle Uebergabe-Kandidaten des Laufs am Stueck.

DIE MESSBASIS IST DIESELBE WIE VORHER, und das ist die Bedingung, unter der
der Umzug ueberhaupt zulaessig ist ([[ersatzmessungen-sind-hypothesen]]):
gemessen ist der 112er-Warp DES ERNTE-FRAMES (core.ernte.align112). Seit
E3a-1c (Bauplan analysen/bauplan_refquelle_einbau.md, J1 bis J3) liegt er
verlustfrei im Satz der Referenz-Quelle (rechen112.png, PNG: dieselben Pixel
wie die fruehere .npy-Kachel), und der Satz traegt die Norm daraus schon als
Messwert: core/harvest_set rechnet Fingerabdruck und Norm in EINEM Aufruf der
r-Stufe aus genau diesen Bytes, auf demselben Rechenwerk und mit derselben
Breite 1 wie `messen` hier (bild_kern.EngineNormMass.feature_norm ist
rechner.embeddings(...)[1]). Dieser Schritt nimmt deshalb die Norm aus dem
Satz; fehlt sie dort, rechnet er sie mit `messen` aus den 112er-Bytes des
Satzes (Lese-Stufe c), nie aus einer anderen Datei. Die BATCHGROESSE bleibt 1:
NormMass driftet zwischen Batchgroessen (Kopfkommentar dort). „Gebuendelt"
meint den JOB, nicht den Tensor.

ZWEI FRAGEN, EIN MESSWERT — beide fallen hier, weil beide an derselben Zahl
haengen und sie nie zweimal gerechnet werden darf:
  * die SIEB-ACHSE (Boden gegen zu schwaches Lernmaterial, Werkswert
    core.guete.norm_werk(), je Kamera ueber das Katalog-Register). Sie
    entscheidet, ob der Fund M bleibt.
  * die VORRATS-LINIE (Naehe-Frage, core.ernte.gate_v_norm, Werte
    vorrat_norm_min/_profil). Sie entscheidet das v-Flag.
  Beide Urteile gehen als Katalog-Nachtrag (Art nachtrag, Thema NACHTRAG_THEMA,
  mit Kennung) an die ref_id (J2); wer auf der Norm-Achse faellt, bekommt die
  Statuszeile verworfen (J3, Verfall nach aufbewahrung_tage) — geloescht wird
  hier nichts mehr.

HALTUNG, unveraendert aus dem Haus:
  * fail-closed je FUND: aktive Latte + kein Messwert = der Fund faellt
    (`n_unmessbar`, gezaehlt). Messbarkeit vor Stimme.
  * fail-open je MODELL: baut die Session nicht, laeuft der Lauf LAUT ohne
    diese Achse weiter (Latte 0) statt jeden Fund zu verwerfen — Blocker BL-1
    der Gegenpruefung W1.
  * RESUMEFEST: je Ereignis eine Buchung (norm_fertig.jsonl), ein
    Wiederaufnehmen misst nur Fehlendes. Die Kandidaten-Datei wird atomar
    getauscht, nie halb geschrieben.
  * KATALOG VOR DATEI: die Katalogzeilen eines Ereignisses entstehen vor dem
    Tausch seiner Kandidaten-Datei; ein Absturz dazwischen wiederholt das
    Ereignis, und die letzte Zeile je ref_id und Thema gilt.
  * DATENORT: der Job bekommt kein data_dir (verifyd.py baut den Auftrag ohne
    es, worker_dienst.py reicht keins durch); er nimmt es ueber
    core.lernlauf.datenort_cfg aus VERIFY_DATA_DIR, das der Dienst aus seiner
    Config setzt — fehlt es, faellt der Job laut.

KONTRAKT wie core/ernte.py: reine Funktionen, Pfade/Schwellen als Parameter,
kein Dienst-Import, keine schweren Imports im Modulkopf. Die MESSUNG selbst
kommt als Funktion herein (`messen`) — dieses Modul kennt weder onnxruntime
noch face_audit; der Worker reicht die budgetierte Session durch, der
Testharnisch stellt eine Zahl.
"""
import json
import os
import tempfile

from core import ernte as _ern         # Namensregeln (Pfade) + gate_v_norm
from core import messkarte as _mk      # Bilanz-Vertrag, EIN Vokabular
from core import logbuch as _logbuch
_log = _logbuch.logger(__name__)

# Buchung je Ereignis — dieselbe Bauform wie core.ernte.fertig.jsonl: eine
# Zeile je erledigtem Ereignis, angehaengt und geflusht. Sie ist die einzige
# Resume-Grundlage; die Kandidaten-Zeilen selbst tragen keinen „schon
# gemessen"-Schalter (ein Feld, das nur einen Zwischenstand beschreibt, waere
# ein zweiter Zustand neben dieser Datei).
FERTIG_DATEI = "norm_fertig.jsonl"

# Der Weg-Name der Bilanz (core.messkarte.bilanz_start). Er steht in der
# Lauf-Datei und in der Logzeile, damit eine Deckungs-Luecke ihren Ort nennt.
WEG = "norm"

# Das Thema des Katalog-Nachtrags (J2): Norm, Norm-Latte, Sieb-Urteil, V-Entscheidung und V-Linie.
NACHTRAG_THEMA = "norm_schritt"
QUELLE_SATZ = "Messwert des Satzes (rechen112, Schreibzeit)"
QUELLE_NEU = "rechen112 des Satzes, im Norm-Schritt gerechnet"


def fertig_pfad(lauf_dir):
    return os.path.join(lauf_dir, FERTIG_DATEI)


def fertig_lesen(lauf_dir):
    """Was dieser Lauf schon nachgemessen hat -> (eids, bilanz, v_ja, v_nein).

    Die Buchungen werden JE EREIGNIS zusammengezogen und dabei nach eid
    entdoppelt (letzte Zeile gewinnt): ein Absturz zwischen Datei-Tausch und
    Buchung laesst dasselbe Ereignis noch einmal laufen, und dann darf seine
    Bilanz nicht zweimal in der Summe stehen. Kaputte Zeilen werden
    uebersprungen — ihr Ereignis fehlt dann im Set und wird neu gemessen
    (idempotent, s. `_zeilen_nachtragen`), nie still als erledigt gebucht.

    EHRLICHE GRENZE der Entdopplung: laeuft ein Ereignis nach genau diesem
    Absturzfenster ein zweites Mal, sieht der zweite Durchgang nur noch die
    Zeilen, die beim ersten M geblieben sind — seine Bilanz ist also kleiner
    als die ersetzte. Die Lauf-Summe untertreibt dann fuer DIESES eine
    Ereignis. Das ist die harmlose Richtung (sie behauptet nie mehr Deckung,
    als es gab) und der Preis dafuer, dass die Buchung je Ereignis atomar
    bleibt."""
    p = fertig_pfad(lauf_dir)
    je_eid = {}
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    d = json.loads(zeile)
                    je_eid[str(d["eid"])] = d
                except Exception:                       # noqa: BLE001
                    _logbuch.swallowed(_log, _logbuch.WARNING, "skipped")
                    continue
    bilanzen = [d.get("bilanz") for d in je_eid.values() if d.get("bilanz")]
    v_ja = sum(int(d.get("v_ja") or 0) for d in je_eid.values())
    v_nein = sum(int(d.get("v_nein") or 0) for d in je_eid.values())
    return set(je_eid), _mk.bilanz_summe(bilanzen), v_ja, v_nein


def fertig_anhaengen(lauf_dir, eintrag):
    """Ein Ereignis als nachgemessen festhalten (geflusht + fsync — ein
    Absturz kostet hoechstens die Wiederholung DIESES Ereignisses)."""
    os.makedirs(lauf_dir, exist_ok=True)
    with open(fertig_pfad(lauf_dir), "a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def offene_events(lauf_dir, eids):
    """Die Ereignisse, die noch nachzumessen sind (Reihenfolge wie geliefert).
    Ereignisse ohne Kandidaten-Datei fallen weg — sie sind entweder nie
    geerntet worden oder ihr Job ist gescheitert (dann hat
    core.ernte.event_aufraeumen aufgeraeumt)."""
    schon, _b, _j, _n = fertig_lesen(lauf_dir)
    return [e for e in (eids or [])
            if str(e) not in schon
            and os.path.exists(_ern.kandidaten_pfad(lauf_dir, e))]


def _latte_fuer(latten, kamera):
    """Die Norm-Latte DIESER Kamera -> Zahl oder None.

    Der Dienst loest die Latten je Kamera auf (core.kamerakalib.sieb_latten)
    und legt sie fertig in den Job — der Worker greift nie selbst in die
    Config. `""` traegt die globale Zeile als Rueckfall fuer eine Kamera, die
    beim Bauen des Jobs noch nicht bekannt war (ein Ereignis, dessen Kamera
    inzwischen umbenannt wurde). Ohne jede Zeile gibt es keine Latte — und
    keine Latte heisst nach der Haus-Invariante: diese Achse siebt nicht."""
    l = latten or {}
    satz = l.get(str(kamera or "")) or l.get("") or {}
    return satz.get("n")


def _norm_aus_satz(cfg, ref_id, messen):
    """Die Norm eines Uebergabe-Kandidaten aus seinem Satz (Lese-Stufe c): der Messwert norm des Satzes,
    sonst `messen` auf seinen 112er-Bytes. -> (Wert oder None, Kennung oder None); fail-closed je Fund."""
    import math
    from core import refquelle as _rq
    s = _rq.read_set(cfg, ref_id) if ref_id else None
    if s is None:
        return None, None
    q = s["quelle"] or {}
    nw = ((q.get("messwerte") or {}).get("norm") or {})
    wert = nw.get("wert")
    if isinstance(wert, (int, float)) and not isinstance(wert, bool) and math.isfinite(wert):
        return float(wert), dict(nw.get("kennung") or {}, quelle=QUELLE_SATZ)
    name = (q.get("teile") or {}).get("rechen112")
    roh = s["dateien"].get(name)
    if roh is None or name in s["fehler"]:
        return None, None
    import cv2
    import numpy as np
    try:
        # BATCH 1, bewusst: NormMass driftet zwischen Batchgroessen.
        wert = messen(cv2.imdecode(np.frombuffer(roh, np.uint8), cv2.IMREAD_COLOR))
    except Exception:                                   # noqa: BLE001
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning None")
        return None, None
    return (None if wert is None else float(wert)), dict(q.get("rechenwerk") or {}, quelle=QUELLE_NEU)


def zeile_nachtragen(zeile, latte, wert, schwellen, bilanz):
    """EINE Kandidaten-Zeile mit ihrer Norm abschliessen -> ("v_ja"|"v_nein"|
    "v_aus"|"verworfen"|None) fuer die Vorrats-Zaehlung und den Katalog.

    Sie trifft GENAU die Entscheidungen, die bis .517 im Ernte-Rumpf fielen,
    in derselben Reihenfolge und mit denselben Funktionen:

      1. der Messwert kommt in die Zeile (`norm`, vier Nachkommastellen wie
         zuvor — Zeile und Entscheidung rechnen mit DENSELBEN Werten, Vertrag
         V0.5);
      2. die SIEB-ACHSE urteilt ueber core.kamerakalib.sieb_ok — dieselbe
         Mechanik, dasselbe Grund-Vokabular (`n_unter`/`n_unmessbar`), kein
         zweiter Vergleich mit denselben Zahlen;
      3. faellt der Fund, verliert er M und S ("verworfen": der Aufrufer
         schreibt seinem Satz die Statuszeile verworfen, J3; geloescht wird
         nichts — die Anker-Phase nimmt nur Zeilen mit m UND ref_id);
      4. bleibt er, entscheidet die VORRATS-LINIE (core.ernte.gate_v_norm) das
         v-Flag fuer Zeilen mit Richtung (die V-Frage der Ernte). AUSSER das
         Lauf-Regime traegt die Vorrats-Achsen gar nicht (seit .521 der
         Normalfall am Pass-Knopf): dann faellt hier KEINE v-Entscheidung, die
         Zeile bleibt unangetastet und meldet sich als "v_aus" (.522, P-1).

    IDEMPOTENT: ein Ereignis, dessen Datei-Tausch gelang und dessen Buchung
    ein Absturz verschluckt hat, laeuft noch einmal durch. Dann tragen seine
    Zeilen bereits ihr Ergebnis (m=False oder v gesetzt) — eine gefallene Zeile
    wird nicht neu beurteilt, eine gebliebene liest dieselbe Norm aus ihrem Satz
    noch einmal (s. `_zeilen_nachtragen`)."""
    from core import kamerakalib as _kk
    norm = None if wert is None else round(float(wert), 4)
    zeile["norm"] = norm
    _mk.bilanz_zaehlen(bilanz, norm is not None,
                       None if norm is not None else _mk.GRUND_WARP_FEHLT)
    ok, grund = _kk.sieb_ok({"n": latte}, n=norm)
    _mk.sieb_zaehlen(bilanz, ok, grund)
    if not ok:
        zeile["m"] = False
        zeile["s"] = False
        zeile["sieb_grund"] = grund
        zeile["v"] = False
        return "verworfen"
    if zeile.get("richtung") is None or not zeile.get("ref_id"):
        return None                     # keine V-Frage der Ernte oder kein Satz
    if not _ern.vorrat_schwellen_da(schwellen):
        # ALTZEILE IM NEUEN REGIME (.522, Widerleger-Befund P-1): die Zeile
        # traegt ein Vorrats-Bild, aber DIESER Lauf entscheidet die
        # Vorrats-Linie gar nicht — sein Regime traegt die Achsen nicht (der
        # Pass-Knopf popt sie seit .521 bewusst). Bis .521 lief das trotzdem in
        # `gate_v_norm` hinein und starb dort am fehlenden Schluessel; der
        # Worker-Job riss, der Dienst wiederholte ihn fuenfmal, und das
        # Ereignis blieb ungemessen zurueck.
        # Behandelt wird die Zeile jetzt ENDLICH und unbeschaedigt: `v`
        # bleibt, wie es ist (wer nicht entscheidet, aendert nichts), und der
        # Aufrufer zaehlt den Fall, damit er im Log auftaucht statt still zu
        # bleiben.
        return "v_aus"
    v = bool(_ern.gate_v_norm(norm, zeile.get("front_kps"), schwellen))
    zeile["v"] = v
    return "v_ja" if v else "v_nein"


def _katalog_zeile(zeile, latte, schwellen, marke, kennung):
    """Der Katalog-Nachtrag (J2) und, wenn der Fund faellt, die Statuszeile (J3) einer Zeile mit Satz.
    -> (ref_id, Nachtrag-Felder, Grund fuer verworfen oder None)"""
    linie = ({k: schwellen.get(k) for k in ("vorrat_norm_min", "vorrat_norm_min_profil",
                                            "vorrat_front_profil")}
             if _ern.vorrat_schwellen_da(schwellen) else None)
    werte = {"norm": zeile.get("norm"), "latte_n": latte, "sieb_ok": marke != "verworfen",
             "sieb_grund": zeile.get("sieb_grund"),
             "v": zeile.get("v") if marke in ("v_ja", "v_nein") else None, "vorrat_linie": linie}
    felder = {"thema": NACHTRAG_THEMA, "werte": werte,
              "kennung": kennung or {"quelle": "no norm source (no set or no readable 112 crop)"}}
    grund = f"norm step: {zeile.get('sieb_grund')}" if marke == "verworfen" else None
    return zeile["ref_id"], felder, grund


def _zeilen_nachtragen(lauf_dir, eid, latten, schwellen, messen, cfg):
    """Ein Ereignis komplett nachmessen -> (zeilen, bilanz, v_ja, v_nein,
    v_aus, katalog). `v_aus` (.522) sind die Zeilen mit V-Frage, deren Linie dieser
    Lauf gar nicht entscheidet (Regime ohne Vorrats-Achsen, s.
    `zeile_nachtragen`) — sie sind kein Verlust, aber sie gehoeren ins Log.
    `katalog` (E3a-1c, J2/J3) sind die Katalogzeilen je Satz, die der Aufrufer
    VOR dem Datei-Tausch schreibt. Schreibt NICHTS — der Aufrufer tauscht die
    Datei atomar."""
    bilanz = _mk.bilanz_start(WEG)
    v_ja = v_nein = v_aus = 0
    zeilen, katalog = [], []
    with open(_ern.kandidaten_pfad(lauf_dir, eid), encoding="utf-8") as f:
        for roh in f:
            roh = roh.strip()
            if not roh:
                continue
            try:
                z = json.loads(roh)
            except Exception:                           # noqa: BLE001
                # Eine kaputte Zeile wird NICHT weggeworfen: sie zaehlt in der
                # Buecher-gegen-Platte-Wache (core.ernte.bestand_pruefen) mit,
                # und ein stilles Verschwinden waere genau der Verlust, den
                # jene Wache aufdecken soll. Sie geht unveraendert durch.
                zeilen.append(roh)
                continue
            if not z.get("m"):
                # Kein Uebergabe-Kandidat (das Ernte-Sieb hat ihn schon
                # verworfen, oder eine fruehere Runde dieses Jobs). Nichts zu
                # messen, nichts zu entscheiden — die Zeile bleibt, wie sie ist.
                zeilen.append(z)
                continue
            # E3a-1c: die Norm kommt aus dem Satz (Kopf dieser Datei); eine Zeile
            # ohne Satz hat keine Messbasis und faellt fail-closed (n_unmessbar).
            wert, kennung = _norm_aus_satz(cfg, z.get("ref_id"), messen)
            latte = _latte_fuer(latten, z.get("kamera"))
            marke = zeile_nachtragen(z, latte, wert, schwellen, bilanz)
            if marke == "v_ja":
                v_ja += 1
            elif marke == "v_nein":
                v_nein += 1
            elif marke == "v_aus":
                v_aus += 1
            if z.get("ref_id"):
                katalog.append(_katalog_zeile(z, latte, schwellen, marke, kennung))
            zeilen.append(z)
    return zeilen, bilanz, v_ja, v_nein, v_aus, katalog


def _katalog_schreiben(cfg, katalog):
    """Die Katalogzeilen eines Ereignisses schreiben: Nachtrag je Satz (J2), verworfen fuer die
    gefallenen (J3, nur Kandidaten ohne Bindung). -> Zahl der Statuszeilen verworfen"""
    from core import lernlauf as _ll
    from core import refquelle as _rq
    weg = {}
    for ref_id, felder, grund in katalog:
        _rq.append(cfg, ref_id, "nachtrag", felder)
        if grund:
            weg.setdefault(grund, []).append(ref_id)
    return sum(_ll.saetze_verwerfen(cfg, ids, grund) for grund, ids in weg.items())


def _zeilen_schreiben(lauf_dir, eid, zeilen):
    """Die Kandidaten-Datei ATOMAR tauschen (tmp + fsync + os.replace).

    Bauform wie core.ernte.manifest_schreiben, inklusive mkstemp: ein FESTER
    tmp-Name kollidiert, sobald zwei Aufrufer denselben Ordner beschreiben —
    genau der S2-Fehler vom 01.09. Ein halb geschriebener Kandidaten-Bestand
    waere hier besonders teuer: er traegt die Embeddings des ganzen
    Ereignisses."""
    p = _ern.kandidaten_pfad(lauf_dir, eid)
    fd, tmp = tempfile.mkstemp(prefix="kandidaten.", suffix=".tmp",
                               dir=os.path.dirname(p))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for z in zeilen:
            f.write((z if isinstance(z, str)
                     else json.dumps(z, ensure_ascii=False)) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def norm_job(lauf_dir, eids, schwellen, latten, messen=None, log=_log,
             abbruch=None):
    """DER gebuendelte Norm-Schritt eines Laufs -> Ergebnis-Dict.

    lauf_dir  Lauf-Verzeichnis (dieselben Namensregeln wie core.ernte).
    eids      die Ereignisse des Laufs, in Reihenfolge.
    schwellen das eingefrorene Lauf-Regime (Manifest) — daraus kommen die
              Vorrats-Linien (vorrat_norm_min/_profil/_front_profil).
    latten    {kamera: sieb_latten-Satz, "": globale Zeile} — vom DIENST je
              Kamera aufgeloest; der Worker greift nie selbst in die Config.
    messen    f(bgr112) -> float. None = die Session ist nicht da; dann
              laeuft der Lauf LAUT ohne diese Achse weiter (fail-open je
              MODELL, Blocker BL-1) und misst NICHTS nach. Gerufen nur fuer
              einen Satz, der keine Norm traegt (Kopf dieser Datei).
    abbruch   f() -> bool: der Job endet nach dem laufenden Ereignis. Alles
              Gebuchte bleibt gebucht, der Rest wartet auf die Wiederaufnahme.

    -> {"events", "offen", "bilanz", "v_ja", "v_nein", "v_aus", "verworfen",
        "achse_aus": Grund|None, "abgebrochen": bool,
        "warp_kandidaten", "warp_fehlt"}  (warp_*: Uebergabe-Kandidaten und die ohne
        Messbasis — seit E3a-1c ohne Satz oder ohne lesbaren 112er; Name wie bisher,
        der Dienst liest `warp_fehlt`)

    `v_aus` (.522): Zeilen mit Vorrats-Bild, deren Linie dieser Lauf gar nicht
    entscheidet — sein Regime traegt die Vorrats-Achsen nicht (Pass-Knopf seit
    .521). Kein Verlust, aber eine Ansage: bis .521 riss an dieser Stelle ein
    KeyError den ganzen Job.
    """
    log = _logbuch.as_logger(log)      # E7: der Kommandozeilen-Weg (worker.py) reicht eine Funktion
    offen = offene_events(lauf_dir, eids)
    if messen is None:
        # FAIL-OPEN JE MODELL. Nichts wird angefasst: die Zeilen tragen
        # `norm: null`, die Achse laesst damit alles durch (Latte-<=-0-Zweig
        # gilt hier nicht — es gibt schlicht keinen Vergleich); eine
        # Wiederaufnahme mit funktionierender Session misst spaeter nach.
        grund = ("feature-norm session not available — this run keeps every "
                 "finding on the norm axis and decides no stock line")
        log.error(f"norm step: SIEVE AXIS OFF (n) — {grund}")
        return {"events": 0, "offen": len(offen), "bilanz": None,
                "v_ja": 0, "v_nein": 0, "v_aus": 0, "verworfen": 0,
                "achse_aus": grund, "abgebrochen": False,
                "warp_kandidaten": 0, "warp_fehlt": 0}
    from core import lernlauf as _ll
    cfg = _ll.datenort_cfg()            # laut, wenn der Datenort fehlt (Kopf: DATENORT)
    fertig_n = verworfen_g = 0
    v_aus_g = 0
    abgebrochen = False
    for eid in offen:
        if abbruch is not None and abbruch():
            abgebrochen = True
            break
        zeilen, bilanz, v_ja, v_nein, v_aus, katalog = _zeilen_nachtragen(
            lauf_dir, eid, latten, schwellen, messen, cfg)
        verworfen_g += _katalog_schreiben(cfg, katalog)
        _zeilen_schreiben(lauf_dir, eid, zeilen)
        fertig_anhaengen(lauf_dir, {"eid": eid, "bilanz": bilanz,
                                    "v_ja": v_ja, "v_nein": v_nein})
        fertig_n += 1
        v_aus_g += v_aus
    _eids, summe, v_ja_g, v_nein_g = fertig_lesen(lauf_dir)
    # DECKUNG aus der Bilanz statt aus einem zweiten Datei-Durchgang: ein Fund
    # ohne Messwert hat GENAU einen Grund (Name `warp_fehlt` wie bis E3a-1b).
    w_kand = int((summe or {}).get("gesehen") or 0)
    w_fehlt = int(((summe or {}).get("gruende") or {}).get(
        _mk.GRUND_WARP_FEHLT) or 0)
    if w_fehlt:
        log.error(f"norm step: {w_fehlt} of {w_kand} handover candidate(s) had no "
            f"reference set with a readable 112 crop — they could not be measured and "
            f"fell on the norm axis (fail-closed per finding)")
    if v_aus_g:
        # NIE STILL (.522, P-1): Zeilen tragen die V-Frage der Ernte,
        # dieser Lauf entscheidet die
        # Vorrats-Linie aber nicht (sein Regime traegt die Achsen nicht). Bis
        # .521 riss genau das den Job mit einem KeyError — jetzt laeuft er
        # durch und sagt, was er nicht entschieden hat.
        log.warning(f"norm step: {v_aus_g} candidate line(s) carry the stock "
            f"question of their harvest, but this run's regime has no stock "
            f"thresholds — their stock line stays untouched (no v decision on "
            f"this path)")
    return {"events": fertig_n, "offen": len(offen) - fertig_n,
            "bilanz": summe, "v_ja": v_ja_g, "v_nein": v_nein_g,
            "v_aus": v_aus_g, "verworfen": verworfen_g, "achse_aus": None,
            "abgebrochen": abgebrochen,
            "warp_kandidaten": w_kand, "warp_fehlt": w_fehlt}


def bilanz_satz(erg):
    """DIE eine Logzeile des Schritts (englisch wie alle Dienst-Logzeilen).

    Sie beantwortet genau die vier Fragen, die der User am Schritt gestellt hat:
    wie viel wurde gemessen, wie viel ist gefallen, wie viel war nicht
    messbar — und ob die Achse ueberhaupt gewirkt hat."""
    if not erg:
        return ""
    if erg.get("achse_aus"):
        return f"norm step: axis off — {erg['achse_aus']}"
    b = erg.get("bilanz") or {}
    s = b.get("sieb") or {}
    teile = [f"norm step: {erg.get('events', 0)} event(s), "
             f"{b.get('gemessen', 0)} of {b.get('gesehen', 0)} handover "
             f"candidate(s) measured, {s.get('gesiebt', 0)} fell on the norm "
             f"axis, {b.get('unmessbar', 0)} unmeasurable"]
    if erg.get("v_ja") or erg.get("v_nein"):
        teile.append(f"stock line: {erg.get('v_ja', 0)} kept, "
                     f"{erg.get('v_nein', 0)} rejected")
    if erg.get("verworfen"):
        teile.append(f"{erg['verworfen']} set(s) set to discarded")
    if erg.get("abgebrochen"):
        teile.append(f"stopped early, {erg.get('offen', 0)} event(s) left "
                     f"for the next run")
    return " | ".join(teile)
