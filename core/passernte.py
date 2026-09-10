"""core/passernte — DER Identitaets-Schritt des Mini-Ernte-Laufs (.521).

USER-GO 10.09.2026 („Pass-Knopf = Mini-Erntelauf"): der Knopf an der
Personen-Karte prueft nicht mehr gespeicherte Event-Crops an einer eigenen
Pixel-Latte, sondern faehrt fuer DIESEN Durchgang einen kleinen Lernlauf —
Clips holen, ernten, mit dem Register „Face catalog" sieben, die Feature-Norm
gebuendelt nachmessen — und filtert erst DANACH auf die gewaehlte Person.

WOZU ein eigenes Modul. Die drei Schritte davor gibt es laengst und sie
bleiben unangetastet: `core/ernte.py` erntet und siebt (fuenf leichte Achsen
des Registers), `core/normlauf.py` misst die sechste. Was fehlte, war der
letzte Schritt: WELCHE der uebrig gebliebenen Uebergabe-Kandidaten gehoeren zu
der Person, auf deren Karte geklickt wurde. Genau das — und NICHTS anderes —
steht hier.

DIE ARBEITSTEILUNG IST DIE SECHS-ACHSEN-VERFASSUNG:
  * die QUALITAETS-Frage beantwortet AUSSCHLIESSLICH das Sieb des Registers
    (core.kamerakalib.sieb_ok, je Kamera aufgeloest). Wer hier ankommt, hat
    sie bestanden — `m == True` IST die Antwort. Dieses Modul stellt sie
    NICHT noch einmal: eine zweite Qualitaets-Latte waere die Doppel-Siebung,
    die die Verfassung verbietet (und sie war der Grund, warum die alte
    Pass-Pruefung 540 von 541 zugelassenen Bildern wieder wegwarf).
  * die IDENTITAETS-Frage beantwortet dieses Modul, mit den vier Zahlen aus
    `core.benennung.ID_LATTE` — Wort fuer Wort dieselbe Achse, die
    `anlernen.bild_stufe`/`vorschlaege_person` seit .257 fuehren. Fremde
    Personen fallen damit KONSTRUKTIONSBEDINGT heraus, nicht durch eine
    zusaetzliche Regel.

FAIL-VERHALTEN, beide Richtungen benannt:
  * KEINE REFERENZEN der Person -> KEIN Kandidat, und das laut. Dieselbe
    Haltung wie `vorschlaege_person` (dort ueberspringt die fehlende
    Referenz-Matrix die ganze Schleife). Die Alternative waere die
    `bild_stufe`-Regel „ohne eigene Referenz gilt die Identitaet als
    User-Wort" — die passt fuer eine Gruppen-Flaeche, in der der Mensch die
    Person gerade benannt hat, aber nicht fuer einen Knopf, der ungesehen
    Referenzen vorschlaegt.
  * EINE ZEILE OHNE EMBEDDING -> faellt mit eigenem Grund (`kein_emb`), nie
    still. Sie kann nicht beurteilt werden, und das ist ein Verlust, kein
    Durchlass.

DECKEL JE EVENT (BRUECKE_JE_EVENT-Semantik, .32x): hoechstens N Bilder je
Ereignis bekommen einen Haken; der Rest wird GRENZFALL und bleibt sichtbar —
nie stiller Verlust. Die Reihung innerhalb eines Ereignisses ist wortgleich
die von `vorschlaege_person` (empfohlen vor grenz, dann `sim` AUFSTEIGEND):
das Neueste zuerst, nicht das Aehnlichste — fuenf Bilder derselben Sekunde
bringen weniger als fuenf Blickwinkel.

KONTRAKT wie core/ernte.py und core/normlauf.py: reine Funktionen, Pfade und
Schwellen als Parameter, kein Dienst-Import, keine schweren Imports im
Modulkopf. Die REFERENZ-MATRIZEN kommen als Parameter herein — dieses Modul
kennt weder insightface noch den refcache; der Worker reicht sie durch, der
Testharnisch stellt Zahlen.
"""
import json
import os
import tempfile

from core import ernte as _ern         # Namensregeln der Lauf-Dateien
from core import messkarte as _mk      # Bilanz-Vertrag, EIN Vokabular

# Die Auswahl DIESES Laufs — eine Zeile je Kandidat, der die Identitaets-Achse
# bestanden hat. Sie ist zweierlei in einem, und beides mit Absicht an EINER
# Stelle: die Anzeige-Liste des Auswahl-Overlays UND der BEIWERT-Vorrat der
# Uebernahme (Embedding + Messwerte je Bild, Muster `core/vorrat.vorrat.jsonl`
# -> `anlernen.vorrat_aufnehmen`). Ohne den Beiwert entstuende bei der
# Uebernahme eine Referenz ohne Embedding — die tote Referenz aus dem
# 28/40-Befund.
AUSWAHL_DATEI = "auswahl.jsonl"

# Der Weg-Name der Bilanz (core.messkarte.bilanz_start).
WEG = "passernte"

# Die Stufen des Auswahl-Overlays. `empfohlen` kommt mit Haken, `grenz` ohne —
# der Mensch entscheidet am Bild (.231: Grenzfaelle werden nie verschwiegen).
STUFE_EMPFOHLEN = "empfohlen"
STUFE_GRENZ = "grenz"

# Die DIAGNOSE dieses Laufs (Kennungen + Zaehler), damit der Klick-Handler
# „warum nichts?" MIT ZAHLEN beantworten kann. Sie muss die Antwort ueberleben,
# die sie erzeugt hat: geerntet wird im Hintergrund-Thread, gelesen beim
# naechsten Poll — deshalb eine Datei und kein Prozess-Zustand.
DIAGNOSE_DATEI = "passernte.json"

# WARUM eine Zeile nicht in die Auswahl kam — EINE Aufzaehlung fuer Zaehler,
# Bilanz und Log (dieselbe Haltung wie core.kamerakalib.SIEB_GRUENDE; ein
# zweites Literal an der Zaehlstelle waere die K3-Falle).
#
# DIE KENNUNGEN SIND BEWUSST DIE DES BESTANDS (`anlernen.GRUND_KLASSE`, Anzeige
# `webui.bausteine.bruecke_grund`): dieselbe Frage bekommt denselben Namen und
# damit denselben Satz in allen fuenf Sprachen — ein eigenes Vokabular haette
# fuenf neue Uebersetzungen fuer eine Aussage gebraucht, die es laengst gibt.
GRUND_KEIN_EMB = _mk.GRUND_KEIN_GESICHT   # Zeile ohne Embedding: nicht messbar
GRUND_KEINE_REFS = "keine_referenzen"     # die Person hat keine Referenzen
GRUND_FREMD_NAEHER = "fremd_naeher"       # eine andere Person liegt naeher
GRUND_GEDECKT = "gedeckt"                 # Bestands-Duplikat (eigen >= sim_neu)
GRUND_ID_UNSICHER = "id_unsicher"         # zu weit weg / kein Abstand zum Fremden
GRUENDE = (GRUND_KEIN_EMB, GRUND_KEINE_REFS, GRUND_FREMD_NAEHER,
           GRUND_GEDECKT, GRUND_ID_UNSICHER)


def auswahl_pfad(lauf_dir):
    return os.path.join(lauf_dir, AUSWAHL_DATEI)


def auswahl_lesen(lauf_dir):
    """Die Auswahl eines Laufs -> Liste der Zeilen (leer, wenn es sie nicht
    gibt). Kaputte Zeilen werden uebersprungen — eine unlesbare Zeile darf die
    Anzeige der uebrigen nicht kosten."""
    p = auswahl_pfad(lauf_dir)
    aus = []
    if not os.path.exists(p):
        return aus
    with open(p, encoding="utf-8") as f:
        for roh in f:
            roh = roh.strip()
            if not roh:
                continue
            try:
                aus.append(json.loads(roh))
            except Exception:                       # noqa: BLE001
                continue
    return aus


def auswahl_schreiben(lauf_dir, zeilen):
    """Die Auswahl ATOMAR ablegen (tmp + fsync + os.replace, Bauform wie
    core.ernte.manifest_schreiben). Atomar, weil der Klick-Handler die Datei
    als FERTIG-MARKE liest: eine halb geschriebene Auswahl saehe fuer ihn aus
    wie ein fertiger Lauf mit zu wenig Bildern."""
    os.makedirs(lauf_dir, exist_ok=True)
    p = auswahl_pfad(lauf_dir)
    fd, tmp = tempfile.mkstemp(prefix="auswahl.", suffix=".tmp", dir=lauf_dir)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)
    return p


def diagnose_pfad(lauf_dir):
    return os.path.join(lauf_dir, DIAGNOSE_DATEI)


def diagnose_schreiben(lauf_dir, d):
    """Die Diagnose des Laufs ablegen (Anzeige-Grund + Bilanz). Ein
    Schreibfehler ist NIE fatal: er kostet den Grund-Satz, nicht die Auswahl."""
    try:
        os.makedirs(lauf_dir, exist_ok=True)
        with open(diagnose_pfad(lauf_dir), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except OSError:
        pass


def diagnose_lesen(lauf_dir):
    """-> die Diagnose des Laufs oder {} (Alt-Ordner, Lesefehler)."""
    try:
        with open(diagnose_pfad(lauf_dir), encoding="utf-8") as f:
            return json.load(f) or {}
    except (OSError, ValueError):
        return {}


def diagnose_bauen(person, zeilen, bilanz, keine_refs):
    """Die Diagnose in der Form, die `anlernen.diagnose_dominant` und
    `webui.bausteine.bruecke_grund` schon lesen koennen -> dict.

    KEIN neues Vokabular und keine zweite Anzeige-Tabelle: die Kennungen sind
    die des Bestands (s. GRUENDE oben), also greift die vorhandene
    Satz-Auswahl samt ihren fuenf Uebersetzungen unveraendert. `events` und
    `geprueft` sind hier die Zahlen DIESES Wegs — Ereignisse mit Material und
    beurteilte Funde —, damit `diagnose_dominant` seine Vorab-Faelle („kein
    Event im Scope", „kein einziges gemessenes Bild") richtig trifft."""
    s = (bilanz or {}).get("sieb") or {}
    return {"person": person,
            "events": len({str(z.get("eid")) for z in (zeilen or [])}),
            "geprueft": int((bilanz or {}).get("gemessen") or 0),
            "klassen": dict(s.get("gruende") or {}),
            "keine_referenzen": bool(keine_refs),
            "empfohlen": 0, "neutral": 0,
            # Die zwei Pixel-Schwellen des Bestands-Wegs gibt es hier NICHT —
            # auf diesem Weg siebt das Register. `bruecke_grund` fuellt sie
            # dann mit "?" statt eine Zahl zu behaupten, die nicht gewirkt hat.
            "min_kante": None, "unscharf_max": None,
            "kante_max": None, "sharp_max": None}


def id_stufe(eigen, fremd, id_werte):
    """DIE Identitaets-Achse -> (STUFE_EMPFOHLEN|STUFE_GRENZ|None, grund).

    Wort fuer Wort der Identitaets-Zweig von `anlernen.bild_stufe`, in
    derselben Reihenfolge derselben Vergleiche: Bestands-Duplikat raus,
    naeherer Fremder raus, `sim_min` = sicher, `sim_unsicher` MIT `abstand` =
    wahrscheinlich, sonst raus. Die vier Zahlen kommen vom Aufrufer
    (core.benennung.ID_LATTE) — dieses Modul erfindet keine Latte.

    Der Unterschied zu `bild_stufe` ist AUSSCHLIESSLICH die fehlende
    Qualitaets-Achse: die hat auf diesem Weg das Register schon beantwortet
    (Modulkopf). Deshalb heisst „sicher" hier direkt `empfohlen` und
    „wahrscheinlich" direkt `grenz` — dort entsteht dieselbe Stufe aus der
    UND-Verknuepfung beider Achsen."""
    w = id_werte or {}
    sim_min = w.get("sim_min")
    sim_neu = w.get("sim_neu")
    sim_unsicher = w.get("sim_unsicher")
    abstand = w.get("abstand")
    if eigen is None:
        # Keine Referenz-Naehe messbar. Auf diesem Weg heisst das RAUS und
        # nicht „Identitaet gilt als User-Wort" (Begruendung im Modulkopf).
        return None, GRUND_KEINE_REFS
    if sim_neu is not None and eigen >= sim_neu:
        return None, GRUND_GEDECKT
    if fremd is not None and fremd >= eigen:
        return None, GRUND_FREMD_NAEHER
    if sim_min is not None and eigen >= sim_min:
        return STUFE_EMPFOHLEN, None
    if (sim_unsicher is not None and eigen >= sim_unsicher
            and (fremd is None or abstand is None
                 or (eigen - fremd) >= abstand)):
        return STUFE_GRENZ, None
    return None, GRUND_ID_UNSICHER


def naehe(emb_vec, refs, person, np_mod):
    """Referenz-Naehe EINES Embeddings -> (eigen, fremd).

    Dieselbe Rechnung wie `vorschlaege_person` (Matrix-Produkt gegen die
    normierten Referenz-Embeddings, Maximum je Person): `eigen` = beste
    Aehnlichkeit zur gewaehlten Person, `fremd` = beste zu irgendeiner
    anderen (None, wenn es keine andere gibt). eigen None = die Person hat
    keine Referenz-Matrix."""
    M = (refs or {}).get(person)
    if M is None or not len(M):
        return None, None
    v = np_mod.asarray(emb_vec, dtype="float32")
    eigen = float((M @ v).max())
    fremde = [float((M2 @ v).max()) for p2, M2 in (refs or {}).items()
              if p2 != person and M2 is not None and len(M2)]
    return eigen, (max(fremde) if fremde else None)


def _anzeige_datei(zeile):
    """Das ANZEIGE-Bild einer Kandidaten-Zeile -> lauf-relativer Pfad oder None.

    Der M-Crop (`datei`) ist die Wahl, und zwar dieselbe wie beim
    Kalibrier-Vorrat (`core.ernte.kalib_vorrat_speisen`): die Messwerte der
    Zeile gehoeren zu GENAU diesem Ausschnitt. Das Vorratsbild mit Rand
    (`datei_v`) gibt es auf diesem Weg gar nicht — die Vorrats-Linie wird hier
    nicht entschieden (der Mini-Lauf ist fluechtig und speist nie den
    Lernvorrat)."""
    return zeile.get("datei") or None


def kandidaten(lauf_dir, eids):
    """Die UEBERGABE-KANDIDATEN des Laufs -> Liste der Zeilen mit Bild.

    „Uebergabe-Kandidat" heisst genau das, was es im Lernlauf heisst: `m` ist
    nach Ernte-Sieb UND Norm-Schritt noch True. Zeilen, die eine der sechs
    Achsen verworfen hat, tragen `m: False` (der Norm-Schritt setzt es und
    loescht ihre Bilder) — sie kommen hier gar nicht mehr an.

    Ereignisse ohne Kandidaten-Datei fallen weg: sie sind entweder nie
    geerntet worden oder ihr Job ist gescheitert (dann hat
    `core.ernte.event_aufraeumen` aufgeraeumt)."""
    aus = []
    for eid in eids or []:
        p = _ern.kandidaten_pfad(lauf_dir, eid)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for roh in f:
                roh = roh.strip()
                if not roh:
                    continue
                try:
                    z = json.loads(roh)
                except Exception:                   # noqa: BLE001
                    continue
                if not z.get("m") or not _anzeige_datei(z):
                    continue
                aus.append(z)
    return aus


def _item(zeile, person, stufe, eigen, fremd):
    """Eine Auswahl-Zeile: Anzeige-Daten UND Beiwert in einem (s. AUSWAHL_DATEI).

    Die Messwerte reisen ueber den EINEN Griff der Messkarte mit
    (`core.messkarte.uebernehmen`) statt ueber eine abgeschriebene Feldliste —
    das ist der Kopierschritt, an dem `core/vorrat.py` seine Guete-Masse
    verloren hat (core/messkarte.py, Inventur §I-3)."""
    rel = _anzeige_datei(zeile)
    return _mk.uebernehmen(
        {"eid": zeile.get("eid"), "kamera": zeile.get("kamera"),
         "person": person, "stufe": stufe,
         "datei": os.path.basename(str(rel)), "datei_rel": rel,
         "sim": None if eigen is None else round(eigen, 3),
         "fremd": None if fremd is None else round(fremd, 3),
         "richtung": zeile.get("richtung"), "ts": zeile.get("ts"),
         "t": zeile.get("t"),
         # BEIWERT der Uebernahme (Muster core/vorrat): das Embedding wurde am
         # ERNTE-FRAME gemessen, nicht am gespeicherten JPEG — es darf nie neu
         # aus dem Crop gerechnet werden ([[ersatzmessungen-sind-hypothesen]]).
         "emb": zeile.get("emb"), "modell": zeile.get("modell")},
        zeile)


def auswahl_bilden(zeilen, person, refs, id_werte, je_event, np_mod):
    """Die Auswahl EINES Laufs -> (zeilen_der_auswahl, bilanz).

    Reihenfolge der Arbeit: Naehe messen -> Identitaets-Achse -> Deckel je
    Ereignis. Der Deckel ist bewusst der LETZTE Schritt und kein Filter davor:
    was er abschneidet, wird GRENZFALL (sichtbar, ohne Haken) und faellt nicht
    heraus."""
    bilanz = _mk.bilanz_start(WEG)
    treffer = []
    for z in zeilen:
        emb = z.get("emb")
        if not emb:
            _mk.bilanz_zaehlen(bilanz, False, GRUND_KEIN_EMB)
            _mk.sieb_zaehlen(bilanz, False, GRUND_KEIN_EMB)
            continue
        _mk.bilanz_zaehlen(bilanz, True)
        eigen, fremd = naehe(emb, refs, person, np_mod)
        stufe, grund = id_stufe(eigen, fremd, id_werte)
        _mk.sieb_zaehlen(bilanz, stufe is not None, grund)
        if stufe is None:
            continue
        treffer.append((stufe, eigen, fremd, z))
    # REIHUNG wortgleich `vorschlaege_person`: empfohlen vor grenz, dann `sim`
    # AUFSTEIGEND — das Neueste zuerst, nicht das Aehnlichste. Der Deckel
    # unten nimmt damit je Ereignis die zwei Bilder, die dem Bestand am
    # WENIGSTEN gleichen (.32x: „fuer den Lernvorrat zaehlt Vielfalt, nicht
    # Menge"). Der eid-Schluessel am Ende macht die Reihung deterministisch —
    # zwei Bilder mit derselben Naehe sollen nicht je Lauf die Plaetze tauschen.
    treffer.sort(key=lambda p: (0 if p[0] == STUFE_EMPFOHLEN else 1,
                                p[1] if p[1] is not None else 0.0,
                                str(p[3].get("datei") or "")))
    je = {}
    aus = []
    deckel = int(je_event or 0)
    for stufe, eigen, fremd, z in treffer:
        e = str(z.get("eid"))
        if stufe == STUFE_EMPFOHLEN:
            je[e] = je.get(e, 0) + 1
            if deckel and je[e] > deckel:
                # NIE STILLER VERLUST: der ueberzaehlige Kandidat bleibt in der
                # Auswahl, nur ohne Haken (BRUECKE_JE_EVENT-Semantik).
                stufe = STUFE_GRENZ
        aus.append(_item(z, person, stufe, eigen, fremd))
    bilanz["deckel_je_event"] = deckel
    return aus, bilanz


def passernte_job(lauf_dir, eids, person, refs, id_werte, je_event, log=print):
    """DER Identitaets-Schritt eines Mini-Ernte-Laufs -> Ergebnis-Dict.

    lauf_dir   Lauf-Verzeichnis (dieselben Namensregeln wie core.ernte).
    eids       die Ereignisse des Durchgangs, in Reihenfolge.
    person     die Person, auf deren Karte geklickt wurde.
    refs       {person: normierte Referenz-Matrix} — vom Worker gereicht.
    id_werte   core.benennung.ID_LATTE, vom DIENST gelesen (der Worker greift
               nie selbst in die Config; hier ist es eine Code-Quelle, aber
               dieselbe Richtung: der Job bekommt seine Zahlen fertig).
    je_event   Deckel der Empfehlungen je Ereignis (anlernen.BRUECKE_JE_EVENT).

    -> {"kandidaten", "empfohlen", "grenz", "bilanz", "keine_refs"}

    KEINE REFERENZEN heisst LAUT und leer (Modulkopf): der Lauf schreibt eine
    leere Auswahl (die Fertig-Marke des Klick-Handlers) und sagt im Log, dass
    die Person keine Referenz hat, an der er messen koennte."""
    import numpy as _np                 # lazy wie ueberall im Haus
    zeilen = kandidaten(lauf_dir, eids)
    M = (refs or {}).get(person)
    keine_refs = M is None or not len(M)
    if keine_refs:
        log(f"pass check: {person} has no reference of their own yet — the "
            f"identity axis cannot judge {len(zeilen)} harvested candidate(s); "
            f"nothing is proposed (teach one picture first)")
    aus, bilanz = auswahl_bilden(zeilen, person, refs, id_werte, je_event, _np)
    auswahl_schreiben(lauf_dir, aus)
    n_e = sum(1 for z in aus if z.get("stufe") == STUFE_EMPFOHLEN)
    dg = diagnose_bauen(person, zeilen, bilanz, keine_refs)
    dg["empfohlen"], dg["neutral"] = n_e, len(aus) - n_e
    diagnose_schreiben(lauf_dir, {"person": person, "diagnose": dg,
                                  "bilanz": bilanz})
    return {"kandidaten": len(zeilen), "empfohlen": n_e,
            "grenz": len(aus) - n_e, "bilanz": bilanz,
            "diagnose": dg, "keine_refs": bool(keine_refs)}


def bilanz_satz(erg, ernte_summe=None, norm_erg=None):
    """DIE eine Bilanz-Zeile des Mini-Ernte-Laufs (englisch wie alle
    Dienst-Logzeilen).

    Sie beantwortet die Kette in EINER Zeile, weil genau das die Frage ist,
    die ein Betreiber am Knopf stellt: wie viel wurde geerntet, was hat das
    REGISTER weggesiebt (je Achse), was die Feature-Norm, was die Identitaet —
    und was bleibt uebrig. Die drei Vorstufen liefert der Aufrufer als das,
    was sie sind (Ernte-Zaehler, Norm-Ergebnis), damit hier keine zweite
    Buchfuehrung entsteht."""
    e = ernte_summe or {}
    teile = [f"harvest: {int(e.get('detektionen') or 0)} detection(s), "
             f"{int(e.get('kandidaten') or 0)} candidate(s), "
             f"{int(e.get('gesiebt') or 0)} sieved out by the catalogue "
             f"register"]
    gr = ((e.get("mkbilanz") or {}).get("sieb") or {}).get("gruende") or {}
    # .525 (Prod-Pruefung 10.09., Befund B-3): der FEHLENDE POSTEN der
    # Achsen-Aufzaehlung. Die Achsen zaehlen das SIEB-URTEIL, `gesiebt` zaehlt
    # das ERGEBNIS — ein struktur-gesperrter Fund hat das Sieb BESTANDEN und
    # faellt trotzdem (core/ernte.py, Zaehler `ohne_struktur`, dort ausdruecklich
    # so dokumentiert). Ohne diesen Posten summierten sich die vier Achsen nicht
    # auf die genannte Sieb-Zahl (real gemessen 468 statt 512, Delta genau die 44
    # struktur-gesperrten Funde), und wer nachrechnete, hielt die Bilanz fuer
    # kaputt. Zahlen unveraendert, der Posten wird nur genannt.
    _ohne = int(e.get("ohne_struktur") or 0)
    if gr or _ohne:
        _posten = [f"{k} {v}" for k, v in sorted(gr.items())]
        if _ohne:
            _posten.append(f"plus {_ohne} without face structure")
        teile.append("by axis: " + ", ".join(_posten))
    if norm_erg:
        nb = (norm_erg.get("bilanz") or {}).get("sieb") or {}
        if norm_erg.get("achse_aus"):
            teile.append("feature norm: axis off")
        else:
            teile.append(f"feature norm: {int(nb.get('gesiebt') or 0)} fell, "
                         f"{int(nb.get('durch') or 0)} kept")
    r = erg or {}
    ib = (r.get("bilanz") or {}).get("sieb") or {}
    igr = ib.get("gruende") or {}
    teile.append(f"identity: {int(ib.get('gesiebt') or 0)} of "
                 f"{int(r.get('kandidaten') or 0)} rejected"
                 + ("; " + ", ".join(f"{k} {v}" for k, v in sorted(igr.items()))
                    if igr else ""))
    teile.append(f"result: {int(r.get('empfohlen') or 0)} recommended / "
                 f"{int(r.get('grenz') or 0)} borderline")
    return "pass harvest | " + " | ".join(teile)
