"""Die Koerper-Marke: ob sich das Video eines Ereignisses fuer Koerperbilder eignet (Koerperweg neu, KW1).

HERKUNFT: Bauplan analysen/bauplan_koerperweg_neu.md, Stufe KW1 Punkt 3 (Konzept
analysen/konzept_koerperbilder_extralauf.md, Abschnitte 3 und 8). Der Eigentuemer 20.11.2026 11:28:47: der Worker wird
nur minimal geaendert, „ohne extra Modelle oder Berechnungen".

ZWECK: Der Worker legt drei Zahlen, die er ohnehin zaehlt, in seine Ergebniszeile (worker_dienst.results_zeile und der
Ereignis-Lauf): `stapel.gueltig`, `stapel.gestimmt` und `unbekannt_gruppen`. Der Dienst baut daraus mit
`marke_bauen` das Feld `koerper_marke` der Akte-Zeile (verifyd.Service.process); `eignet_sich` sagt aus einer
Akte-Zeile, ob der Cutter (Stufe KW3) aus dem Video Koerperbilder schneiden darf. Beide Funktionen sind rein: kein
Modell, kein Bild, keine Datei.

DIE REGEL (`eignet_sich`, alles muss gelten): Kategorie erkannt, genau ein bestaetigter Name, Personenzahl genau 1,
mindestens `koerper_auswahl_stimmen` Stimmen fuer diesen Namen, keine Stimme fuer einen anderen Namen, hoechstens ein
echtes Gesicht je Bild, keine Unbekannt-Gruppe und kein eingespieltes Ereignis (core.einspielen.ist_einspiel).
Gueltige Gesichter ohne Stimme sperren nicht (Stufe KW1 Punkt 8, Entscheid R mit Nachtrag, Eigentuemer 20.11.2026
22:50:11 „bauen weiter und passen die regel am ende an"); die Marke haelt ihre Zahl weiter im Feld `ohne_stimme` fest.

DIE AUSWAHL DES CUTTERS (Stufe KW3 Punkt 4, `cutter_fenster` und `cutter_auswahl`): der Dienst liest nur die Akte, ueber
core.akte.sicht(...).heute(von, bis) mit dem Fenster `koerper_max_tage`; `bis` ist der Beginn des naechsten Tags, damit
der heutige Tag mitgelesen wird (core/akte.py schliesst den Tag von `bis` aus). Genommen werden je Person die neuesten
Ereignisse mit `eignet_sich`, die juenger als `koerper_max_tage` und noch nicht bearbeitet sind (Merker: die
bearbeiteten Ereignisse der Schublade, core.refquelle.body_events, auch die ohne Bild). Die Person eines Ereignisses
ist sein einziger bestaetigter Name. Ohne Personenliste gilt der Lauf fuer alle Personen (Lesart der Stufe KW3). Den
Lauf startet `koerper_lauf` (Stufe KW13): von Hand, taeglich mit der Wartung (alle wartenden Ereignisse je Person,
n_je_person None) oder sofort nach jedem geeigneten Ereignis (dann ohne diese Auswahl, genau die vorgemerkten Kennungen).

DAS ERKENNEN NACH DEM ABSTAND (Stufe KW5): Hat ein Ereignis kein bestaetigtes Gesicht, stoesst der Dienst
(Service._person_live) eine Abfrage im Koerper-Prozess an, wenn `abfrage_noetig` ja sagt und die Schublade ein gueltiges
Bild hat (core.kette.koerper_scharf). Die Antwort (Fingerabdruecke der Abfragebilder) vergleicht `vergleichen` mit den
gueltigen Bildern der Schublade; eine reine Rechnung ohne Modell. Das Ergebnis geht als Zeile in die eigene Datei
`TREFFER_DATEI` (`treffer_buchen`); `treffer_karte` liefert daraus je Ereignis die letzte Zeile in der Form der alten
Karte (Felder person, score und stimmen), die szenarien.py je Durchgang verrechnet (Name ab `koerper_stimmen` Stimmen,
gesperrt durch das Fremd-Urteil).

DIE REGEL DER KOERPER-ERKENNUNG (Stufe KW12, R1 bis R3; Eigentuemer 21.11.2026 „genauso machen wie mit dem Gesicht"):
  R1. Stimmen: `vergleichen` zaehlt die Abfragebilder ueber der Schwelle (`stimmen`, ohne Namen 0); `treffer_buchen`
      schreibt sie in die Zeile. `stimmen_zaehlen` summiert sie; eine Zeile ohne das Feld (Bestand vor KW12) zaehlt
      eine Stimme.
  R2. Ein Koerper-Name gilt, sobald die Person im Durchgang `koerper_stimmen` Stimmen hat (Werk 3), gezaehlt ueber alle
      ihre Treffer-Ereignisse des Durchgangs; die geparkte Vision-Stimme zaehlt im Durchgang ohne Gesicht eine dazu.
  R3. `koerper_namen` sagt allein, fuer welche Ereignisse eines Durchgangs ein Koerper-Name gilt: ohne Gesichts-Namen
      die Ereignisse der Namen, die szenarien.py zeigt; mit Gesichts-Namen nur fuer eine Person, die das Gesicht nennt,
      auf den Ereignissen ohne eigenen Gesichts-Namen, wenn deren Stimmen `koerper_stimmen` erreichen.
Gemeldet wird nur auf Wunsch, je Weg ein Schalter aus `MELDE_SCHALTER` (ab Werk alle aus, dann nur Anzeige); die
Entscheidung je Durchgang und Person steht in `meldung_faellig`, der Merker in `MELDE_DATEI` (`meldung_merken`).

DIE SCHWELLE (`schwelle_bestimmen`, Entscheid S, Eigentuemer 20.11.2026 16:34:20 „Untergrenze 0,65"): das Groessere aus
dem Boden `koerper_schwelle` und der geeichten Schwelle (staerkster Kosinus zwischen gueltigen Bildern verschiedener
Personen plus `koerper_marge`; Regel core/personmodell._eichung auf den Abstand uebertragen, Konzept
analysen/konzept_abstandsprinzip.md). Die Eichung hebt nur an, nie senkt sie; mit nur einer Person gilt der Boden.

LESARTEN (wo der Plan offen ist, die engste; im Zweifel kein Name):
  1. Boden 0 heisst nur geeicht. Gibt es dann keinen geeichten Wert (gueltige Bilder nur einer Person), gibt es keine
     Schwelle und keinen Namen.
  2. Je Abfragebild nennt jede Person einen Namen, deren aehnlichstes gueltiges Bild den hoechsten Wert des Bilds traegt
     und die Schwelle erreicht (Grenze eingeschlossen). Tragen zwei Personen denselben hoechsten Wert, nennt das Bild
     beide, und es gibt keinen Namen (wie zwei Bilder mit verschiedenen Namen).
  3. Ein Abfragebild unter der Schwelle nennt keinen Namen und sperrt nichts; nennen die uebrigen genau einen Namen, gilt
     er. Wert der Zeile: der hoechste Wert des genannten Namens, ohne Namen der hoechste Wert ueberhaupt.
  4. Die Treffer-Datei bekommt eine Zeile je verglichenem Ereignis, auch ohne Namen (person null); die letzte Zeile je
     Ereignis gilt, so dass ein neuerer Vergleich ohne Namen einen alten Namen aufhebt; `treffer_karte` gibt nur Zeilen
     mit Namen weiter. Ausfaelle ohne Vergleich (kein Abfragebild, keine Antwort) schreiben keine Zeile. Beim
     Umbenennen einer Person haengt `treffer_umbenennen` (gerufen von core.umbenennen, Stufe KW2 Punkt 8) je Ereignis,
     dessen letzte Zeile den alten Namen traegt, dieselbe Zeile mit dem neuen Namen an; nichts wird umgeschrieben.
     Markiert der Nutzer einen Namen als falsch (Seite Benannte Personen, Stufe FN4), haengt `treffer_korrigieren`
     dieselbe Zeile mit person null und `falsch` = bisheriger Name an; danach uebergeht `treffer_karte` jede spaetere
     Zeile dieses Ereignisses, so dass kein neuer Vergleich und kein Umbenennen den Namen zurueckbringt.
  5. Ausloeser: Kategorie weder erkannt noch fehler und Frigate-Personenzahl genau 1; eine unbekannte Personenzahl
     (None) ist nicht 1.

EHRLICHE GRENZEN:
  - Was nicht gezaehlt werden konnte, gilt nicht als geeignet: eine Zeile ohne Marke (vor dieser Version, alte
    Ergebniszeile, Analyse ohne Ergebnis) und eine Marke mit `unbekannt_gruppen` null (Unbekannt-Stapel aus).
  - Ein zweiter Mensch, dessen Gesicht nie zu sehen war und den Frigate nicht zaehlt, bleibt unsichtbar (Bauplan,
    Abschnitt „Was zugesagt wird und was nicht").
  - Die Latte `koerper_auswahl_stimmen` (Werk 6) ist nicht gemessen (Konzept Abschnitt 8).
  - Der Boden 0,65 ist an einer Anlage gemessen (Entscheid S), anderswo nicht; liegt er dort zu hoch, gibt es keinen Namen
    statt eines falschen.
  - Die Treffer-Datei waechst ohne Kuerzung (eine Zeile je verglichenem Ereignis); jeder Leser liest sie ganz.
  - Die Merk-Datei der Meldungen (`MELDE_DATEI`, eine Zeile je Meldung: ts, start, person, eids, wege) kuerzt die
    taegliche Datenpflege nach `aufbewahrung_tage` (`meldungen_kuerzen`); die Regel braucht nur Zeilen des Tags. Eine
    Meldung gilt je Durchgang und Person einmal, abgeglichen ueber die Kennungen, und nach der Ruhezeit
    `anwesenheit_cooldown` seit der letzten Sichtung wieder.
"""
import collections
import datetime
import json
import os
import threading
import time

import numpy as np

from core import einspielen as _einspiel
from core import logbuch as _logbuch

_log = _logbuch.logger(__name__)

TAG_S = 86400
TREFFER_DATEI = os.path.join("state", "koerper_treffer.jsonl")    # unter dem Datenordner, eigener Zustand des Koerperwegs
_TREFFER_SPERRE = threading.Lock()
TREFFER_BILD = "koerper_treffer.png"     # Bild eines Treffers mit Namen im Ereignisordner (treffer_bild_ablegen)
NUTZER_WERT = 1.0     # Wert eines Namens, den der Nutzer bei der Korrektur in Frigate setzt (Stufe FN4 Punkt 6)
MELDE_DATEI = os.path.join("state", "koerper_meldungen.jsonl")    # Merker der Meldungen je Durchgang und Person
_MELDE_SPERRE = threading.Lock()
# Die Melde-Schalter der Koerper-Erkennung (Stufe KW12 Punkt 1), eine Stelle: jeder Leser fragt ueber cfg.get. Der
# fuenfte (Stufe KW14) meldet nichts nach aussen, er schreibt Marken der Anwesenheit.
MELDE_SCHALTER = ("koerper_meldet_frigate", "koerper_meldet_pushover", "koerper_meldet_telegram", "koerper_meldet_ha",
                  "koerper_meldet_anwesenheit")


def _gesichter_je_bild(detektionen):
    """Die groesste Zahl echter Gesichter (ohne Fehldetektion) mit derselben Bildnummer.
    -> int, oder None, wenn einer echten Detektion die Bildnummer fehlt"""
    je_bild = collections.Counter()
    for d in detektionen or ():
        if d.get("fd"):
            continue
        if d.get("i") is None:
            return None
        je_bild[d["i"]] += 1
    return max(je_bild.values(), default=0)


def marke_bauen(res, personenzahl):
    """Die Koerper-Marke aus der Ergebniszeile des Workers und der Personenzahl des Ereignisses.
    -> {"pz", "stimmen", "ohne_stimme", "gesichter_je_bild", "unbekannt_gruppen"} oder None (keine Marke)"""
    if not isinstance(res, dict) or "unbekannt_gruppen" not in res:
        return None
    stapel = res.get("stapel")
    if not isinstance(stapel, dict) or not isinstance(stapel.get("stimmen"), dict):
        return None
    gueltig, gestimmt = stapel.get("gueltig"), stapel.get("gestimmt")
    if not isinstance(gueltig, int) or not isinstance(gestimmt, int):
        return None
    je_bild = _gesichter_je_bild(res.get("detektionen"))
    if je_bild is None:
        return None
    return {"pz": personenzahl,
            "stimmen": {n: z for n, z in stapel["stimmen"].items() if z > 0},
            "ohne_stimme": gueltig - gestimmt,
            "gesichter_je_bild": je_bild,
            "unbekannt_gruppen": res["unbekannt_gruppen"]}


def eignet_sich(entry, cfg):
    """Ob sich das Video dieser Akte-Zeile fuer Koerperbilder eignet (Regel im Kopf dieser Datei).
    -> (bool, Grund als englischer Text; bei geeignet "suitable")"""
    marke = entry.get("koerper_marke")
    if not isinstance(marke, dict):
        return False, "no body mark (record written before this version or without a worker result)"
    if marke.get("unbekannt_gruppen") is None:
        return False, "unknown faces were not counted (unknown-face groups switched off)"
    if entry.get("kategorie") != "erkannt":
        return False, f"category is {entry.get('kategorie')!r}, not recognised"
    namen = entry.get("bestaetigt") or []
    if len(namen) != 1:
        return False, f"{len(namen)} confirmed names, not exactly one"
    if marke.get("pz") != 1:
        return False, f"person count is {marke.get('pz')}, not 1"
    stimmen = marke.get("stimmen") or {}
    latte = int(cfg["koerper_auswahl_stimmen"])
    if stimmen.get(namen[0], 0) < latte:
        return False, f"{stimmen.get(namen[0], 0)} votes for the name, fewer than {latte}"
    if any(n != namen[0] for n in stimmen):
        return False, "another name got a vote"
    if marke.get("gesichter_je_bild", 0) > 1:
        return False, f"{marke.get('gesichter_je_bild')} real faces in one picture"
    if marke.get("unbekannt_gruppen") != 0:
        return False, f"{marke.get('unbekannt_gruppen')} unknown-face group(s)"
    if _einspiel.ist_einspiel(entry.get("eid")):
        return False, "injected event"
    return True, "suitable"


def cutter_fenster(jetzt, tage):
    """Das Lesefenster der Akte fuer den Cutter: von jetzt minus `tage` Tage bis zum Beginn des naechsten Tags (der
    heutige Tag wird mitgelesen). -> (von, bis) in Sekunden seit 1970"""
    morgen = (datetime.datetime.fromtimestamp(jetzt).replace(hour=0, minute=0, second=0, microsecond=0)
              + datetime.timedelta(days=1))
    return jetzt - int(tage) * TAG_S, morgen.timestamp()


def cutter_auswahl(zeilen, bearbeitet, cfg, personen, n_je_person, von):
    """Je Person die neuesten geeigneten, noch nicht bearbeiteten Ereignisse ab `von` (Kopf, DIE AUSWAHL DES CUTTERS);
    zeilen ist {eid: letzte Akte-Zeile}. -> Liste (Person, eid), je Person neueste zuerst, hoechstens n_je_person
    (None = alle, der taegliche Lauf)"""
    je_person = {}
    for eid, entry in zeilen.items():
        if eid in bearbeitet or not eignet_sich(dict(entry, eid=eid), cfg)[0]:
            continue
        zeit = entry.get("start") or entry.get("ts") or 0
        person = entry["bestaetigt"][0]
        if zeit >= von and (not personen or person in personen):
            je_person.setdefault(person, []).append((zeit, eid))
    out = []
    for person in sorted(je_person):
        reihe = sorted(je_person[person], reverse=True)
        out += [(person, eid) for _z, eid in (reihe if n_je_person is None else reihe[:int(n_je_person)])]
    return out


def abfrage_noetig(entry, personenzahl):
    """Ob ein Ereignis eine Koerper-Abfrage bekommt, ohne Blick in die Schublade (Kopf, Lesart 5).
    -> (bool, Grund als englischer Text; bei ja "query")"""
    kategorie = (entry or {}).get("kategorie")
    if kategorie in ("erkannt", "fehler"):
        return False, f"category is {kategorie!r}"
    if personenzahl != 1:
        return False, f"person count is {personenzahl}, not 1"
    return True, "query"


def _einheiten(abdruecke):
    """Fingerabdruecke als Matrix, jede Zeile auf Laenge 1 gebracht. -> numpy (n, dim)"""
    m = np.asarray(abdruecke, dtype=np.float64)
    return m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-12)


def schwelle_bestimmen(gueltig, cfg):
    """Die Schwelle aus dem Boden koerper_schwelle und der Eichung ueber die gueltigen Bilder (Kopf, DIE SCHWELLE).
    -> (Schwelle oder None, geeichter Wert oder None)"""
    boden, marge = float(cfg["koerper_schwelle"]), float(cfg["koerper_marge"])
    geeicht = None
    personen = [b["person"] for b in gueltig]
    if len(set(personen)) >= 2:
        m = _einheiten([b["fingerabdruck"] for b in gueltig])
        fremd = np.asarray(personen)[:, None] != np.asarray(personen)[None, :]
        geeicht = float((m @ m.T)[fremd].max()) + marge
    werte = [w for w in ((boden if boden > 0 else None), geeicht) if w is not None]
    return (max(werte) if werte else None), geeicht


def vergleichen(abdruecke, gueltig, cfg):
    """Die Abfragebilder eines Ereignisses gegen die gueltigen Bilder der Schublade (Kopf, Lesarten 1 bis 3).
    -> dict person (None = kein Name), score, schwelle, geeicht, grund (englisch), stimmen (Bilder ueber der Schwelle,
    ohne Namen 0) und bild (Nummer des Abfragebilds mit dem Wert der Zeile, ohne Namen None)"""
    schwelle, geeicht = schwelle_bestimmen(gueltig, cfg)
    erg = {"person": None, "score": None, "schwelle": None if schwelle is None else round(schwelle, 4),
           "geeicht": None if geeicht is None else round(geeicht, 4), "stimmen": 0, "bild": None}
    if not gueltig or not abdruecke:
        return dict(erg, grund="no valid body image" if not gueltig else "no query image")
    personen = sorted({b["person"] for b in gueltig})
    zeilen = np.asarray([b["person"] for b in gueltig])
    werte = _einheiten(abdruecke) @ _einheiten([b["fingerabdruck"] for b in gueltig]).T
    je_person = np.stack([werte[:, zeilen == p].max(axis=1) for p in personen], axis=1)   # (Bilder, Personen)
    bester = je_person.max(axis=1)
    erg["score"] = round(float(bester.max()), 4)
    if schwelle is None:
        return dict(erg, grund="no threshold: floor 0 and valid images of fewer than two persons")
    namen, stimmen = {}, 0                       # namen: Person -> (bester Wert, Nummer seines Bilds)
    for i, wert in enumerate(bester):
        if wert >= schwelle:
            stimmen += 1
            for j in np.flatnonzero(je_person[i] == wert):
                if float(wert) > namen.get(personen[j], (0.0, None))[0]:
                    namen[personen[j]] = (float(wert), i)
    if len(namen) > 1:
        return dict(erg, grund="the query images name different persons")
    if not namen:
        return dict(erg, grund="below the threshold")
    (person, (wert, bild)), = namen.items()
    return dict(erg, person=person, score=round(wert, 4), grund="name", stimmen=stimmen, bild=bild)


def treffer_buchen(data_dir, eid, ergebnis):
    """Das Ergebnis eines Vergleichs als Zeile an die Treffer-Datei haengen (eid, person, score, schwelle, stimmen; ein
    Ergebnis ohne stimmen schreibt null). -> dict der Zeile"""
    zeile = {"ts": round(time.time(), 1), "eid": eid, "person": ergebnis.get("person"),
             "score": ergebnis.get("score"), "schwelle": ergebnis.get("schwelle"), "stimmen": ergebnis.get("stimmen")}
    pfad = os.path.join(data_dir, TREFFER_DATEI)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with _TREFFER_SPERRE, open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return zeile


def treffer_bild_ablegen(data_dir, eid, png):
    """Das Abfragebild eines Treffers mit Namen atomar als TREFFER_BILD in events/<eid>/ ablegen, eine vorhandene Datei
    ersetzen (Stufe FN3, Bauplan analysen/bauplan_feldnachzug_0110.md; Leser routes/koerpernamen). Die Endung ist nicht
    .jpg: die Leser der Gesichtsbilder (routes/event.py, core/visionurteil.py, verifyd) nehmen jede .jpg des Ordners. Kein
    Personenname im Dateinamen; aufgeraeumt wird mit dem Ereignisordner (Service.crops_retention). -> Pfad der Datei"""
    from core import atomar as _at
    pfad = os.path.join(data_dir, "events", eid, TREFFER_BILD)
    _at.bytes_schreiben(pfad, png)
    return pfad


def treffer_karte(data_dir):
    """Je Ereignis die letzte Zeile der Treffer-Datei, nur wenn sie einen Namen traegt (Form der alten Karte: person,
    score; die Leser kennen nur Treffer). Nach einer Zeile mit `falsch` zaehlt keine spaetere Zeile des Ereignisses
    (Kopf, Lesart 4). -> {eid: Zeile}; ohne Datei leer"""
    karte, kaputt, korrigiert = {}, 0, set()
    try:
        with open(os.path.join(data_dir, TREFFER_DATEI), encoding="utf-8") as f:
            for z in f:
                try:
                    d = json.loads(z)
                except ValueError:
                    kaputt += 1
                    continue
                if isinstance(d, dict) and d.get("eid") and d["eid"] not in korrigiert:
                    karte[d["eid"]] = d
                    if d.get("falsch"):
                        korrigiert.add(d["eid"])
    except FileNotFoundError:
        return {}
    except OSError as e:
        _log.warning(f"body hits not readable ({type(e).__name__}: {e}) — no body names shown")
        return {}
    if kaputt:
        _log.warning(f"body hits: {kaputt} unreadable line(s) skipped")
    return {eid: d for eid, d in karte.items() if d.get("person")}


def treffer_umbenennen(data_dir, alt, neu):
    """Beim Umbenennen einer Person je Ereignis, dessen letzte Treffer-Zeile `alt` traegt, eine Zeile mit `neu` anhaengen.
    -> Zahl der angehaengten Zeilen; ohne Datei 0"""
    pfad = os.path.join(data_dir, TREFFER_DATEI)
    with _TREFFER_SPERRE:
        letzte, kaputt = {}, 0
        try:
            with open(pfad, encoding="utf-8") as f:
                for z in f:
                    try:
                        d = json.loads(z)
                    except ValueError:
                        kaputt += 1
                        continue
                    if isinstance(d, dict) and d.get("eid"):
                        letzte[d["eid"]] = d
        except FileNotFoundError:
            return 0
        if kaputt:
            _log.warning(f"body hits: {kaputt} unreadable line(s) skipped while renaming")
        neu_zeilen = [dict(d, person=neu) for d in letzte.values() if d.get("person") == alt]
        if neu_zeilen:
            with open(pfad, "a", encoding="utf-8") as f:
                for zeile in neu_zeilen:
                    f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
    return len(neu_zeilen)


def treffer_korrigieren(data_dir, eid, nicht=None):
    """Einen Koerper-Namen als falsch markieren (Stufe FN4 Punkt 1, Kopf Lesart 4): traegt die letzte Zeile des
    Ereignisses einen Namen ungleich `nicht`, dieselbe Zeile mit ts jetzt, person null und falsch = Name anhaengen.
    -> die neue Zeile; None ohne Datei, ohne Zeile, ohne Namen oder mit dem Namen `nicht`"""
    pfad = os.path.join(data_dir, TREFFER_DATEI)
    with _TREFFER_SPERRE:
        letzte, kaputt = None, 0
        try:
            with open(pfad, encoding="utf-8") as f:
                for z in f:
                    try:
                        d = json.loads(z)
                    except ValueError:
                        kaputt += 1
                        continue
                    if isinstance(d, dict) and d.get("eid") == eid:
                        letzte = d
        except FileNotFoundError:
            return None
        if kaputt:
            _log.warning(f"body hits: {kaputt} unreadable line(s) skipped while correcting")
        if not letzte or not letzte.get("person") or letzte["person"] == nicht:
            return None
        zeile = dict(letzte, ts=round(time.time(), 1), person=None, falsch=letzte["person"])
        with open(pfad, "a", encoding="utf-8") as f:
            f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    return zeile


# ------------------------------------------------------------------ Stufe KW12: Regel und Meldung
def stimmen_zaehlen(zeilen):
    """Die Summe der Stimmen von Treffer-Zeilen (R1); eine Zeile ohne das Feld stimmen oder mit null zaehlt eine Stimme.
    -> int"""
    return sum(1 if z.get("stimmen") is None else int(z["stimmen"]) for z in zeilen)


def koerper_namen(durchgang, karte, ab):
    """Fuer welche Ereignisse eines Durchgangs (aus szenarien.szenarien_des_tages) ein Koerper-Name gilt (R3); karte aus
    treffer_karte, ab = koerper_stimmen. -> {Person: [Kennungen]}; leer, wenn keiner gilt"""
    pers = durchgang.get("pers") or {}
    gesicht = [p for p, d in pers.items() if d.get("quelle") != "koerper"]
    ohne = [(x["eid"], karte[x["eid"]]) for x in durchgang.get("evs") or ()
            if not x.get("conf") and x.get("eid") in karte]       # nur Ereignisse ohne eigenen Gesichts-Namen
    out = {}
    for p in gesicht or [p for p, d in pers.items() if d.get("quelle") == "koerper"]:
        eigene = [(e, z) for e, z in ohne if z.get("person") == p]
        if eigene and (not gesicht or stimmen_zaehlen(z for _e, z in eigene) >= ab):
            out[p] = [e for e, _z in eigene]
    return out


def _zeit(z):
    """Die Zeit ts einer Zeile, wenn sie eine Zahl ist. -> Zahl oder None"""
    ts = z.get("ts") if isinstance(z, dict) else None
    return ts if isinstance(ts, (int, float)) and not isinstance(ts, bool) else None


def moegliche_personen(karte, t0, ab):
    """Der Vorfilter eines Tags (Stufe KW12 Punkt 3b): die Personen, deren Stimmen in Treffer-Zeilen ab t0 (eine Zeile
    ohne lesbare Zeit zaehlt mit) plus eine moegliche Vision-Stimme mindestens ab erreichen. -> Menge"""
    summe = collections.Counter()
    for z in karte.values():
        if _zeit(z) is None or _zeit(z) >= t0:
            summe[z["person"]] += stimmen_zaehlen((z,))
    return {p for p, n in summe.items() if n + 1 >= ab}


def koerper_sichtungen(tag, namen):
    """Je Person die Beginne der Ereignisse, fuer die ihr Koerper-Name in einem Durchgang des Tags gilt, mit dem Start
    des Durchgangs; namen ist koerper_namen je Durchgang in der Reihenfolge von tag. -> {Person: [(Beginn, Start)]}"""
    out = {}
    for d, n in zip(tag, namen):
        beginn = {x.get("eid"): x.get("t") or 0 for x in d.get("evs") or ()}
        for p, eids in n.items():
            out.setdefault(p, []).extend((beginn.get(e, 0), d["start"]) for e in eids)
    return out


def meldung_faellig(durchgang, namen, gemeldet, gesehen, sichtungen, ruhe_s):
    """Ob je Name eines Durchgangs eine Meldung faellig ist: kein gemeldeter Eintrag der Person teilt Kennungen mit dem
    Durchgang, und seit der letzten Sichtung (gesehen: letzte Gesichts-Sichtung je Person; sichtungen: Koerper-Sichtungen
    anderer Durchgaenge vor dem Start) liegen mehr als ruhe_s bis zum Start. -> Liste (Person, Kennungen, neu)"""
    start = durchgang["start"]
    im_durchgang = {x.get("eid") for x in durchgang.get("evs") or ()}
    out = []
    for p, eids in sorted(namen.items()):
        schon = any(g.get("person") == p and im_durchgang & set(g.get("eids") or ()) for g in gemeldet)
        letzt = max([gesehen.get(p, 0)] + [t for t, s in sichtungen.get(p, ()) if s != start and t < start])
        out.append((p, eids, not schon and start - letzt > ruhe_s))
    return out


def meldung_inhalt(durchgang, eids, anstoesse, karte):
    """Das Ereignis einer Meldung (Stufe KW12 Punkt 3b): unter den Kennungen der Person das mit dem spaetesten Beginn,
    das Bild aus seinem Koerper-Anstoss, sonst aus einem anderen Koerper-Anstoss dieser Kennungen, sonst keins.
    -> dict eid, camera, ts (Beginn), png (Bytes oder None), score (Wert der Treffer-Zeile)"""
    beginn = {x.get("eid"): (x.get("t") or 0, x.get("cam")) for x in durchgang.get("evs") or ()}
    eid = max(eids, key=lambda e: beginn.get(e, (0, None))[0])
    pngs = {a.get("eid"): a.get("png") for a in anstoesse if a.get("art") == "koerper" and a.get("png")}
    png = pngs.get(eid) or next((pngs[e] for e in eids if e in pngs), None)
    t, cam = beginn.get(eid, (0, None))
    return {"eid": eid, "camera": cam, "ts": t, "png": png, "score": (karte.get(eid) or {}).get("score")}


def _merk_lesen(pfad):
    """Die lesbaren Zeilen der Merk-Datei. -> Liste von dict; ohne Datei leer"""
    try:
        with open(pfad, encoding="utf-8") as f:
            roh = f.readlines()
    except FileNotFoundError:
        return []
    out = []
    for z in roh:
        try:
            d = json.loads(z)
        except ValueError:
            continue
        if isinstance(d, dict):
            out.append(d)
    return out


def _merk_anhaengen(pfad, zeilen):
    """Zeilen an die Merk-Datei haengen, synchronisiert. -> None"""
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "a", encoding="utf-8") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def meldung_merken(data_dir, durchgang, namen, gesehen, sichtungen, ruhe_s, wege):
    """Unter der Melde-Sperre die Merk-Datei lesen, meldung_faellig rechnen und je faelliger Person eine Zeile (ts, start,
    person, eids, wege) anhaengen; versendet wird erst danach. -> Liste (Person, Kennungen, neu)"""
    pfad = os.path.join(data_dir, MELDE_DATEI)
    with _MELDE_SPERRE:
        tripel = meldung_faellig(durchgang, namen, _merk_lesen(pfad), gesehen, sichtungen, ruhe_s)
        neu = [{"ts": round(time.time(), 1), "start": durchgang["start"], "person": p, "eids": list(eids),
                "wege": list(wege)} for p, eids, ja in tripel if ja]
        if neu:
            _merk_anhaengen(pfad, neu)
    return tripel


def meldungen_umbenennen(data_dir, alt, neu):
    """Beim Umbenennen einer Person je Zeile der Merk-Datei mit `alt` eine gleiche Zeile mit `neu` anhaengen.
    -> Zahl der angehaengten Zeilen; ohne Datei 0"""
    pfad = os.path.join(data_dir, MELDE_DATEI)
    with _MELDE_SPERRE:
        neu_zeilen = [dict(z, person=neu) for z in _merk_lesen(pfad) if z.get("person") == alt]
        if neu_zeilen:
            _merk_anhaengen(pfad, neu_zeilen)
    return len(neu_zeilen)


def meldungen_kuerzen(data_dir, jetzt, tage, rq_cfg):
    """Die Merk-Datei kuerzen: Zeilen mit ts aelter als `tage` Tage Byte fuer Byte in den Papierkorb, der Rest atomar
    neu; eine Zeile ohne lesbare Zeit bleibt. -> dict zeilen, behalten, entfernt; ohne Datei alles 0, keine Datei"""
    from core import atomar as _at
    from core import refquelle as _rq
    pfad = os.path.join(data_dir, MELDE_DATEI)
    frist = jetzt - float(tage) * TAG_S
    with _MELDE_SPERRE:
        try:
            with open(pfad, "rb") as f:
                roh = [z for z in f.read().split(b"\n") if z]
        except FileNotFoundError:
            return {"zeilen": 0, "behalten": 0, "entfernt": 0}

        def alt(z):
            try:
                ts = _zeit(json.loads(z))
            except ValueError:
                return False
            return ts is not None and ts < frist
        raus = [z for z in roh if alt(z)]
        if raus:
            _rq.trash_lines(rq_cfg, jetzt, os.path.splitext(os.path.basename(pfad))[0], raus)
            _at.bytes_schreiben(pfad, b"".join(z + b"\n" for z in roh if not alt(z)))
    return {"zeilen": len(roh), "behalten": len(roh) - len(raus), "entfernt": len(raus)}
