"""core/umbenennen — Person umbenennen: EIN Zug ueber ALLE namenstragenden Bestaende.

ANLASS (Betreiber 21.08.2026, gebaut 18.09.2026 in .542): einen Tippfehler im
Personennamen korrigieren. Das Vorbild `/person_loeschen` (verifyd.py) ist
bewusst KEIN Muster: es nimmt die Person ganz weg (bis E3b-3b schob es ihren
Ordner in den Papierkorb, seit I1 des Bauplans
analysen/bauplan_refquelle_einbau.md wandert jeder ihrer Referenz-Saetze ins
Archiv), und alles andere filtert danach implizit ueber die Existenz.
Beim UMBENENNEN kehrt sich das um — die Person existiert weiter, nur unter
einem neuen Namen, und jeder Speicher mit dem Altnamen wird zur stillen
Waise. Die vier Stellen, die den Unterschied zwischen "funktioniert" und
"verliert still" machen: der Katalog der Referenz-Quelle
`refquelle/katalog.jsonl` (er allein bindet die Saetze an den Namen, die
Saetze selbst tragen keinen; bis E3b-3b war das `faces/refs_meta.jsonl` mit
dem einzigen Embedding-Vektor der Vorrats-Referenzen), die
Event-Crop-Dateinamen (fuenf reine Substring-Leser, kein Index daneben),
`state/lernlauf/B*/vorrat.jsonl` (offene Angebote samt Beiwert) und
`personlern/<P*>/manifest.jsonl` (das Trainings-Label — es erzeugt die
Alt-Klasse ohne jede Nutzeraktion wieder).

DECKUNGS-VERTRAG (die eigentliche Arbeit, K3-Regel aus CLAUDE.md /
qs_ebenen.md): `BESTAENDE` unten ist die EINE Aufzaehlung der
namenstragenden Speicher — Kennung, Ort, Urteil, zustaendiger Migrator.
Sie ist gleichzeitig die Probenliste der Gate-Probe
(`tools/gate/umbenennen_probe.py`). Ohne diesen Vertrag wird der naechste
neue Speicher genauso vergessen, wie `state/anwesenheit/` in der
Alt-Inventur vom 21.08. fehlte (es gab ihn damals noch nicht) — und ein
vergessener Speicher ist hier kein Schoenheitsfehler, sondern ein stiller
Verlust oder ein FALSCHER Name in einer Live-Meldung.

WAS DIESES MODUL NICHT TUT: zusammenfuehren. Existiert der Zielname schon
(case-INsensitiv, geprueft mit `core/benennung.namens_kollision`), lehnt der
Aufrufer ab. Ein Merge hat eine andere Semantik je Bestand (zwei
Referenz-Historien in einem Journal-Schluesselraum, zwei Galerien, zwei
Modell-Klassen) und ist ein eigener Zug.

REIHENFOLGE (bewusst, s. `umbenennen()`): der Katalog zuerst (ab da liefert
`master_persons` den neuen Namen, alle NEU startenden Analysen arbeiten
richtig), Akten-Append ZULETZT (er faengt die Zeilen mit, die eine waehrend
des Zugs noch laufende Analyse mit dem Altnamen geschrieben hat).

Stdlib + numpy; importiert NICHTS aus dem Dienst (Injektionsreinheit wie
core/kette.py). Alle Schreibwege laufen ueber `core/atomar` (tmp + fsync +
os.replace); unlesbare JSONL-Zeilen werden ROH weitergefuehrt (dieselbe
.83-Regel wie `core/anker.anker_lauf_schreiben`).
"""
import glob
import json
import os
import re
import time

from core import atomar as _atomar
from core import logbuch as _logbuch
_log = _logbuch.logger(__name__)

# Reservierte Namen: weder Quelle noch Ziel eines Umbenennens.
#   FREMD          — Klassenkennung des Koerper-Modells (core/personmodell,
#                    core/personlauf), kein Personenname.
# Seit E3b-3b (Bauplan analysen/bauplan_refquelle_einbau.md, Entscheid 6) ohne
# refs_meta.jsonl und refs_mess.json: ein Name ist kein Ordner mehr, der eine
# flache Katalogdatei in faces/ ueberschreiben koennte.
RESERVIERT = ("FREMD",)


# --------------------------------------------------------------- Deckungs-Vertrag
# urteil: "muss"  = ohne Migration entsteht ein stiller Verlust oder ein
#                   FALSCHER Name (aktives Fehlergebnis)
#         "kann"  = Cache/Anzeige, regenerierbar oder mit eigenem Verfall;
#                   wird trotzdem migriert, weil es billiger ist als die
#                   Nebenwirkung
#         "lassen"= bewusst unberuehrt (Fremd-Tatsache, Protokoll, Beleg);
#                   Begruendung im Feld `grund`. Diese Eintraege brauchen
#                   KEINEN Migrator, muessen aber genannt sein — sonst ist
#                   nicht unterscheidbar, ob jemand sie geprueft oder
#                   vergessen hat.
BESTAENDE = (
    # Kennung                 Ort (relativ zu data_dir)             Urteil    Migrator
    # E3b-3b: Katalog ueber das Modul, Saetze lassen, kein Name — die Saetze unter
    # refquelle/<ref_id>/ tragen keinen Personennamen (I9), nur der Katalog bindet.
    ("katalog",               "refquelle/katalog.jsonl",            "muss",   "katalog_umbenennen"),
    ("vorschlaege",          "learn/vorschlaege_<person>.json",    "muss",   "vorschlaege_umbenennen"),
    ("gesichter_pool",        "learn/gesichter.jsonl",              "kann",   "gesichter_nn_umschreiben"),
    ("enroll_queue",          "learn/enroll/queue.jsonl",           "muss",   "enroll_queue_umschreiben"),
    ("anker",                 "state/anker.jsonl",                  "muss",   "anker_umschreiben"),
    ("uebernahmen",           "state/uebernahmen.jsonl",            "muss",   "uebernahmen_umschreiben"),
    ("lernlauf_manifeste",    "state/lernlauf/<lauf>/manifest.json", "muss",  "lernlauf_manifeste_umschreiben"),
    ("lernlauf_vorrat",       "state/lernlauf/<lauf>/vorrat.jsonl", "muss",   "lernlauf_vorrat_umschreiben"),
    ("personlern_manifeste",  "personlern/<lauf>/manifest.jsonl",   "muss",   "personlern_manifeste_umschreiben"),
    ("personlern_galerien",   "personlern/galerien/<person>/",      "muss",   "personlern_galerie_umbenennen"),
    ("personlern_status",     "personlern/modell/status.json",      "muss",   "personlern_status_umschreiben"),
    ("personlern_live",       "personlern/live_treffer.jsonl + live_fenster.json",
                                                                    "kann",   "personlern_live_umschreiben"),
    ("live_meldungen",        "live/meldungen.jsonl (+ .1)",        "kann",   "live_meldungen_umschreiben"),
    ("event_crops",           "events/<eid>/*_{best,show,enroll}_<person>_*",
                                                                    "muss",   "event_durchgang"),
    ("event_results",         "events/<eid>/results.jsonl",         "kann",   "event_durchgang"),
    ("event_kandidaten",      "events/<eid>/kandidaten.jsonl",      "muss",   "event_durchgang"),
    ("deckung",               "state/deckung.jsonl",                "muss",   "deckung_korrigieren"),
    ("ground_truth",          "state/ground_truth.jsonl",           "muss",   "ground_truth_korrigieren"),
    # --- bewusst LASSEN (Begruendung ist Teil des Vertrags) --------------------
    ("deckung_sublabel",      "state/deckung.jsonl (sublabel, frigate.label)",
                              "lassen", None),
    ("deckung_archiv",        "state/archiv/deckung_JJJJ-MM.jsonl", "lassen", None),
    ("sublabel_writes",       "state/sublabel_writes.jsonl",        "lassen", None),
    ("anwesenheit",           "state/anwesenheit/<Tag>.jsonl",      "lassen", None),
    ("unbekannte_pool",       "learn/unbekannte.jsonl",             "lassen", None),
    ("live_beweisbilder",     "live/<Kamera>/<ts>_NAME_<person>.jpg", "lassen", None),
    ("personlern_kontrolle",  "personlern/kontrolle/<pass>/*.jsonl", "lassen", None),
    ("protokolle",            "state/*.log, events/<eid>/analyze.log, logs/",
                              "lassen", None),
    ("backups_papierkorb",    "backups/master_*.tar.gz, trash/person_* (nur noch Altbestand)",
                              "lassen", None),
    ("messmaterial",          "state/kalibriersatz/*, messungen/*",  "lassen", None),
    ("frigate_gegenseite",    "Frigate: /api/faces, geschriebene sub_label",
                              "lassen", None),
    ("config_store",          "config/config.json",                 "lassen", None),
)

# Warum die "lassen"-Eintraege gelassen werden — je Kennung ein Satz. Getrennt
# vom Tupel gehalten, damit der Vertrag oben eine Tabelle bleibt; die Gate-Stufe
# prueft, dass JEDE "lassen"-Kennung hier einen Grund hat (sonst ist "lassen"
# ein bequemes Wort statt einer Entscheidung).
GRUENDE_LASSEN = {
    "deckung_sublabel": "Fremd-Tatsache: was damals nach/aus Frigate ging. "
                        "Umschreiben faelscht die Akte (wie _deckung_korrektur).",
    "deckung_archiv": "kein aktiver Leser im Produktcode belegt; reines "
                      "Rohmaterial spaeterer Auswertungen.",
    "sublabel_writes": "der Leser nimmt nur die eid-Menge (Echo-Freiheit), "
                       "der Name ist Protokoll.",
    "anwesenheit": "per Vertrag append-only (core/anwesenheit: 'nie eine Zeile "
                   "geaendert oder geloescht'), zwei Schreiber-Prozesse; "
                   "verfaellt mit anwesenheit_tage. Teil-Luecke, ausgewiesen.",
    "unbekannte_pool": "der Pool kennt bekannte Personen nicht namentlich "
                       "(label ist im Bestand durchgehend leer).",
    "live_beweisbilder": "der Name ist Beschriftung, nicht Schluessel — der "
                         "Zugriff laeuft ueber den Pfad im Melde-Protokoll; "
                         "Umbenennen wuerde genau die Pfade brechen.",
    "personlern_kontrolle": "Diagnose-Historie mit eigenem Verfall (TRIM_TAGE); "
                            "kein Entscheidungsweg haengt daran.",
    "protokolle": "Belege ueber Vergangenes; ihr Umschreiben faelscht die "
                  "Beweislage.",
    "backups_papierkorb": "Zeitschnitte — sie sollen den damaligen Zustand "
                          "zeigen, sonst sind sie als Wiederherstellungsquelle "
                          "wertlos. Der Papierkorb trash/ wird seit E3b-3b "
                          "nicht mehr beschrieben (I1: Referenzen gehen ins "
                          "Archiv, die Saetze dort tragen keinen Namen).",
    "messmaterial": "eingefrorene Messartefakte (Erb-Urteil-Regel: nicht "
                    "nachtraeglich glaetten).",
    "frigate_gegenseite": "die Frigate-API kennt kein Rename (nur create/"
                          "register/delete{ids}), und jede Faces-Mutation "
                          "antwortet 400, solange dort face_recognition aus "
                          "ist. Nur Dialog-Hinweis, kein stiller Nachzug.",
    "config_store": "am laufenden Store geprueft: keine personen-skalierte "
                    "Einstellung (kameras/areas/live/vision sind kamera- bzw. "
                    "kanalbezogen).",
}


# Kennung des Eingangstors -> Textschluessel der Antwort. EINE Aufzaehlung, weil
# sie zwei Verbraucher hat: den HTTP-Handler (er waehlt daraus den Satz in der
# Sprache des Nutzers) und die Sprach-Deckungsstufe des Gates (sie liest diese
# Werte, statt Literale im Handler zu suchen — dieselbe Bauform wie
# `areas.kettung.<modus>` und `VERWURF_TEXT_PRAEFIX + code`). Wer eine neue
# Ablehnungs-Kennung ergaenzt, ergaenzt sie hier, und das Gate verlangt dann
# ihren Text in allen Sprachdateien; wer eine entfernt, faellt automatisch
# wieder in die Toten-Pruefung.
ANTWORT_TEXTE = {
    "gestartet": "antwort.person_umbenennen_laeuft",
    "unbekannt": "antwort.person_unbekannt",
    "leer": "antwort.person_name_ungueltig",
    "ungueltig": "antwort.person_name_ungueltig",
    "pfad": "antwort.person_name_ungueltig",
    "gleich": "antwort.person_name_gleich",
    "reserviert": "antwort.person_name_reserviert",
    "laeuft": "antwort.person_umbenennen_laeuft_schon",
    "blockiert": "antwort.person_umbenennen_blockiert",
    "kollision": "antwort.person_name_belegt",
}


def migratoren():
    """-> {kennung: migrator_name} der Bestaende, die migriert werden."""
    return {k: m for k, _o, u, m in BESTAENDE if u in ("muss", "kann")}


def bestaende_je_urteil(urteil):
    return tuple(k for k, _o, u, _m in BESTAENDE if u == urteil)


# ------------------------------------------------------------------- Hilfsmittel
def _jsonl_umschreiben(pfad, umschreiber):
    """JSONL atomar neu schreiben: `umschreiber(dict) -> dict|None` wird je
    lesbarer Zeile gerufen (None = Zeile unveraendert lassen). Unlesbare Zeilen
    laufen ROH mit. -> Zahl der GEAENDERTEN Zeilen (0 = Datei nicht angefasst)."""
    if not os.path.exists(pfad):
        return 0
    raus, n = [], 0
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            z = zeile.rstrip("\n")
            if not z.strip():
                continue
            try:
                d = json.loads(z)
            except Exception:
                raus.append(z)                      # unlesbar => roh erhalten
                continue
            neu = umschreiber(d) if isinstance(d, dict) else None
            if neu is None:
                raus.append(z)
            else:
                n += 1
                raus.append(json.dumps(neu, ensure_ascii=False))
    if n:
        _atomar.schreiben(pfad, lambda f: f.write("\n".join(raus) + "\n"))
    return n


def _feld_tauschen(alt, neu, *felder):
    """-> umschreiber fuer _jsonl_umschreiben: ersetzt `alt` durch `neu` in
    genau den genannten Feldern."""
    def _um(d):
        treffer = False
        for k in felder:
            if d.get(k) == alt:
                d[k] = neu
                treffer = True
        return d if treffer else None
    return _um


def _json_lesen(pfad, standard):
    try:
        with open(pfad, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, type(standard)) else standard
    except Exception:
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning standard")
        return standard


def _schluessel_tauschen(d, alt, neu):
    """dict-Schluessel `alt` -> `neu` (last-wins bei Kollision). -> True, wenn
    getauscht wurde."""
    if alt not in d:
        return False
    d[neu] = d.pop(alt)
    return True


# ---------------------------------------------------------- Migrator: Referenzen
def katalog_umbenennen(data_dir, alt, neu, log=None):
    """refquelle/katalog.jsonl ueber das Modul (Bauauftrag E3b-3b, Bauplan
    analysen/bauplan_refquelle_einbau.md, Entscheide 6 und 10, I9): je aktiver
    Referenz der Person eine Bindung-Zeile mit dem neuen Namen; kein Satz wird
    angefasst, die Saetze tragen keinen Namen. Ab dieser Zeile liefert
    master_persons den neuen Namen, und jeder Leser sieht die Aenderung ueber
    die Stand-Kennung des Katalogs (I2). Ohne aktive Referenz gibt es die Person
    nicht (wie frueher ohne Ordner): laut abgelehnt, der Zug bricht ab.
    -> Zahl der geschriebenen Bindung-Zeilen."""
    from core import refquelle as _rq
    n = _rq.rename_person({"data_dir": data_dir}, alt, neu)
    if not n:
        raise LookupError("the person has no active reference set in the catalog")
    return n


# --------------------------------------------------------------- Migratoren: learn
def vorschlaege_umbenennen(data_dir, alt, neu, log=None):
    """learn/vorschlaege_<person mit _>.json: der Name steckt im DATEINAMEN
    und im Feld "person". Die Abbildung ' ' -> '_' ist NICHT injektiv
    ("A B" und "A_B" teilen dieselbe Datei) — liegt am Zielpfad schon eine
    fremde Vorschlagsdatei, wird NICHT ueberschrieben, sondern gemeldet."""
    import anlernen
    # anlernen.py ist Kommandozeilen-Einstieg (E7) und ruft `log(text)`: es
    # bekommt die Methode des Loggers, Stufe der Zeile nach der Inventur (K99).
    return anlernen.vorschlaege_umbenennen(alt, neu, log=log.info if log else None)


def gesichter_nn_umschreiben(data_dir, alt, neu, log=None):
    """learn/gesichter.jsonl, Feld "nn_person" (bester bekannter Treffer beim
    Sammeln). Anzeige ("aehnlich zu …"), wird beim naechsten Reconcile neu
    gerechnet — aber bis dahin geistert der Altname durch den Unbekannt-Reiter.
    MUSS unter anlernen.pool_lock laufen (sammle/reconcile/reorganisieren
    truncaten dieselbe Datei)."""
    import anlernen
    with anlernen.pool_lock():
        return _jsonl_umschreiben(
            os.path.join(data_dir, "learn", "gesichter.jsonl"),
            _feld_tauschen(alt, neu, "nn_person"))


def enroll_queue_umschreiben(data_dir, alt, neu, log=None):
    """learn/enroll/queue.jsonl, Felder "person" und "als".
    WIEDERAUFERSTEHUNGS-PFAD: `Service.enroll_entscheiden` prueft den
    Zielnamen nur gegen PERSON_RE, nicht gegen master_persons — ein offener
    Vorschlag mit dem Altnamen legt beim Annehmen faces/<alt>/ WIEDER an und
    dreht das Umbenennen still zurueck. Die Datensatz-ids ("<eid>:<person>:<t>")
    bleiben stehen: sie sind Dedup-Schluessel, kein Ziel."""
    import anlernen
    with anlernen.pool_lock():
        return _jsonl_umschreiben(
            os.path.join(data_dir, "learn", "enroll", "queue.jsonl"),
            _feld_tauschen(alt, neu, "person", "als"))


# ------------------------------------------------------ Migratoren: Anker/Lernlauf
def anker_umschreiben(data_dir, alt, neu, log=None):
    """state/anker.jsonl, Feld "person" bei status benannt/uebernommen.
    Schreibweg ausschliesslich `core/lernlauf.anker_aktualisieren` (in place,
    unter store_lock, mit Satz-Validierung) — ein eigener Rewrite waere ein
    zweiter Schreibweg auf einen gesicherten Store.
    WIEDERAUFERSTEHUNGS-PFAD: ein benannter Anker fuehrt beim Adopt ueber
    core/uebernahme.uebernehmen zu faces/<alt>/."""
    from core import lernlauf as _ll
    n = 0
    saetze, _kaputt = _ll.anker_lesen(data_dir)     # (saetze, kaputt_zahl)
    for a in saetze:
        if isinstance(a, dict) and a.get("person") == alt and a.get("anker_id"):
            _ll.anker_aktualisieren(data_dir, a["anker_id"], person=neu)
            n += 1
    return n


def uebernahmen_umschreiben(data_dir, alt, neu, log=None):
    """state/uebernahmen.jsonl, Feld "person" — Quelle des Dedups gegen frueher
    uebernommene Lern-Referenzen (core/uebernahme.adoptierte_embs). Ohne
    Migration liefert der Dedup eine leere Liste: eine still ausgeschaltete
    Schutzstufe, die Beinahe-Duplikate erneut in die Bibliothek kopiert."""
    return _jsonl_umschreiben(
        os.path.join(data_dir, "state", "uebernahmen.jsonl"),
        _feld_tauschen(alt, neu, "person"))


def lernlauf_manifeste_umschreiben(data_dir, alt, neu, log=None):
    """state/lernlauf/<B…>/manifest.json, Feld "person" (nur Bruecken-Laeufe
    tragen es). Ohne Migration findet die Ueberlapp-Suche den fertig geernteten
    Pass-Vorrat nicht und erntet denselben Pass erneut (Minuten GPU)."""
    n = 0
    for p in sorted(glob.glob(os.path.join(data_dir, "state", "lernlauf",
                                           "*", "manifest.json"))):
        d = _json_lesen(p, {})
        if d.get("person") == alt:
            d["person"] = neu
            _atomar.json_schreiben(p, d)
            n += 1
    return n


def lernlauf_vorrat_umschreiben(data_dir, alt, neu, log=None):
    """state/lernlauf/<B…>/vorrat.jsonl, Feld "person" je Angebotszeile.
    Die Zeilen tragen "emb" — beim Uebernehmen wandert der Vektor als
    A2-Beiwert in refs_meta. Die Datei ist also keine Wegwerf-Anzeige:
    ohne Migration verschwinden alle offenen Angebote der Person aus dem
    Overlay (aktiver Gleichheits-Filter), das Material bleibt unerreichbar."""
    n = 0
    for p in sorted(glob.glob(os.path.join(data_dir, "state", "lernlauf",
                                           "*", "vorrat.jsonl"))):
        n += _jsonl_umschreiben(p, _feld_tauschen(alt, neu, "person"))
    return n


# --------------------------------------------------- Migratoren: Koerper/Vision
def personlern_manifeste_umschreiben(data_dir, alt, neu, log=None):
    """personlern/<P…>/manifest.jsonl, Feld "person" = das TRAININGS-LABEL.
    Der unangenehmste Wiederauferstehungs-Pfad: das naechste Voll-Training
    erzeugt die Alt-Klasse OHNE jede Nutzeraktion, und der Koerperpfad meldet
    danach dauerhaft den alten Namen. Der reservierte Wert "FREMD" wird nie
    mitersetzt (RESERVIERT deckt das an der Eingangspruefung ab)."""
    n = 0
    for p in sorted(glob.glob(os.path.join(data_dir, "personlern",
                                           "*", "manifest.jsonl"))):
        n += _jsonl_umschreiben(p, _feld_tauschen(alt, neu, "person"))
    return n


def personlern_galerie_umbenennen(data_dir, alt, neu, log=None):
    """personlern/galerien/<person>/ — der ORDNERNAME ist die Person
    (core/visiongalerie.alle liest die Ordnernamen), herkunft.json traegt sie
    zusaetzlich im Feld "person". Ohne Migration faellt die Person aus dem
    Vision-Urteil heraus (sie ist im Kandidatenfeld nicht mehr vertreten) und
    der Wizard zeigt "noch keine Galerie". Der Kopien-Vertrag
    (quelle_hash/kopie_hash) bleibt gueltig: es wandert nur der Ordner."""
    basis = os.path.join(data_dir, "personlern", "galerien")
    q, z = os.path.join(basis, alt), os.path.join(basis, neu)
    if not os.path.isdir(q):
        return 0
    if os.path.exists(z):
        if log:
            log.info(f"rename: gallery folder for the new name already exists — "
                f"left untouched ({z})")
        return 0
    zwischen = os.path.join(basis, f".rename-{int(time.time())}-{os.getpid()}")
    os.rename(q, zwischen)
    try:
        os.rename(zwischen, z)
    except OSError:
        os.rename(zwischen, q)
        raise
    h = os.path.join(z, "herkunft.json")
    d = _json_lesen(h, {})
    if d.get("person") == alt:
        d["person"] = neu
        _atomar.json_schreiben(h, d)
    return 1


def personlern_status_umschreiben(data_dir, alt, neu, log=None):
    """personlern/modell/status.json, "personen": {Person: Bildzahl} — fuer
    core/visiongalerie.deckung ist das die MASSGEBLICHE Personenmenge.
    svm.pkl wird NICHT von Hand umgeschrieben: der Aufrufer faehrt nach den
    Manifesten `core/personmodell.trainieren(data_dir)`, das baut die
    Klassenliste neu, und core/personlive laedt per mtime-Pruefung selbst nach.
    Ein Pickle mit fremder Klassenliste von Hand zu flicken waere unnoetig
    riskant — das Statusfeld dagegen muss vor dem Training stimmen, sonst
    laufen Modell und Anzeige auseinander."""
    pfad = os.path.join(data_dir, "personlern", "modell", "status.json")
    d = _json_lesen(pfad, {})
    personen = d.get("personen")
    if not isinstance(personen, dict) or alt not in personen:
        return 0
    _schluessel_tauschen(personen, alt, neu)
    _atomar.json_schreiben(pfad, d)
    return 1


def personlern_live_umschreiben(data_dir, alt, neu, log=None):
    """personlern/live_treffer.jsonl (Feld "person", Today-Herkunftszeile) und
    live_fenster.json ("karenz": {Person: ts}, treffer[].person — die 900-s-
    Karenz). Beide verfallen von selbst (30 Tage bzw. Fenster), aber bis dahin
    zeigt Today eine inkonsistente Zeile und direkt nach dem Umbenennen kann
    eine Doppelmeldung rausgehen."""
    basis = os.path.join(data_dir, "personlern")
    n = _jsonl_umschreiben(os.path.join(basis, "live_treffer.jsonl"),
                           _feld_tauschen(alt, neu, "person"))
    pfad = os.path.join(basis, "live_fenster.json")
    d = _json_lesen(pfad, {})
    treffer = False
    if isinstance(d.get("karenz"), dict) and _schluessel_tauschen(d["karenz"], alt, neu):
        treffer = True
    for t in (d.get("treffer") or []):
        if isinstance(t, dict) and t.get("person") == alt:
            t["person"] = neu
            treffer = True
    if treffer:
        _atomar.json_schreiben(pfad, d)
        n += 1
    return n


def live_meldungen_umschreiben(data_dir, alt, neu, log=None):
    """live/meldungen.jsonl (+ rotiertes .1), Feld "person" — die Live-Historie
    der Today-Seite. Die Datei wird von einem ANDEREN Prozess (der Engine)
    angehaengt; der Rewrite gehoert deshalb in das Fenster, in dem die Engine
    ohnehin steht (der Aufrufer stoppt sie vorher, s. `umbenennen`)."""
    n = 0
    for name in ("meldungen.jsonl", "meldungen.jsonl.1"):
        n += _jsonl_umschreiben(os.path.join(data_dir, "live", name),
                                _feld_tauschen(alt, neu, "person"))
    return n


# ----------------------------------------------------------- Migratoren: Events
_CROP_ARTEN = ("_best_", "_show_", "_enroll_")


def event_durchgang(data_dir, alt, neu, log=None, puls=None, nur_ab_mtime=None):
    """Der grosse Durchgang ueber events/<eid>/: Crop-DATEINAMEN
    (*_best_<person>_*, *_show_<person>_*, *_enroll_<person>_*), results.jsonl
    ("persons": {Name: …}) und kandidaten.jsonl (Feld "person").

    Die Crop-Dateinamen sind der teuerste MUSS des ganzen Zugs: fuenf Leser
    matchen den Namen als SUBSTRING des Dateinamens (Auftritte-Seite,
    Ereignisliste, Event-Seite, Bestands-Suche, Vision-Kandidatenbau) — es gibt
    keinen Index daneben. Ohne Migration verschwindet die ganze Bildspur der
    Person, und die Bestands-Suche zaehlt jedes Event als "kein_crop" und
    liefert null Vorschlaege, obwohl das Material daliegt.

    Ersetzt wird nur der NAMENSTEIL zwischen den Markern, nie ein Teil-Treffer
    im uebrigen Dateinamen. `nur_ab_mtime` beschraenkt den Lauf auf Ordner, die
    seit diesem Zeitpunkt geschrieben wurden — die zweite Runde, die Ereignisse
    einer waehrend des Zugs noch laufenden Analyse einsammelt.
    -> {"ordner": n, "dateien": n, "results": n, "kandidaten": n}"""
    basis = os.path.join(data_dir, "events")
    erg = {"ordner": 0, "dateien": 0, "results": 0, "kandidaten": 0}
    try:
        eids = sorted(os.listdir(basis))
    except FileNotFoundError:
        return erg
    ges = len(eids)
    for i, eid in enumerate(eids):
        if puls:
            puls(i, ges)
        ordner = os.path.join(basis, eid)
        if not os.path.isdir(ordner):
            continue
        if nur_ab_mtime is not None:
            try:
                if os.path.getmtime(ordner) < nur_ab_mtime:
                    continue
            except OSError:
                _logbuch.swallowed(_log, _logbuch.WARNING, "skipped")
                continue
        beruehrt = False
        try:
            dateien = os.listdir(ordner)
        except OSError:
            _logbuch.swallowed(_log, _logbuch.WARNING, "skipped")
            continue
        for d in dateien:
            for art in _CROP_ARTEN:
                marke = f"{art}{alt}_"
                if marke in d:
                    neu_name = d.replace(marke, f"{art}{neu}_", 1)
                    try:
                        os.rename(os.path.join(ordner, d),
                                  os.path.join(ordner, neu_name))
                        erg["dateien"] += 1
                        beruehrt = True
                    except OSError:
                        _logbuch.swallowed(_log, _logbuch.ERROR, "ignored", throttle=False)
                    break
        def _res(z):
            p = z.get("persons")
            if isinstance(p, dict) and alt in p:
                _schluessel_tauschen(p, alt, neu)
                return z
            return None
        r = _jsonl_umschreiben(os.path.join(ordner, "results.jsonl"), _res)
        erg["results"] += r
        k = _jsonl_umschreiben(os.path.join(ordner, "kandidaten.jsonl"),
                               _feld_tauschen(alt, neu, "person"))
        erg["kandidaten"] += k
        if beruehrt or r or k:
            erg["ordner"] += 1
    if puls:
        puls(ges, ges)
    return erg


# ------------------------------------------------------------ Migratoren: Akten
def deckung_korrigieren(data_dir, alt, neu, log=None, lock=None, markieren=None):
    """state/deckung.jsonl: die Akte wird LAST-WINS JE EID gelesen
    (core/kette.deckung_by_eid) — eine Korrektur ist deshalb ein APPEND, kein
    Rewrite. Das ist das Hausmuster `_deckung_korrektur` (verifyd.py), und es
    ist hier nicht nur billiger, sondern richtiger: ein Rewrite muesste den
    Akte-Mutex ueber die ganze Datei halten, waehrend parallele Analysen
    anhaengen.

    Umgeschrieben werden `bestaetigt[]`, die Schluessel von `ours` und
    `korrektur.person`. NICHT angetastet: `sublabel` und `frigate.label`
    (Fremd-Tatsachen — was damals nach/aus Frigate ging) sowie
    `alerted`/`presence_push` (historische Wahrheit; sonst faelschte die
    Korrektur die Alarm-Tageszahl). Genau dieselbe Grenze zieht
    _deckung_korrektur.

    `lock` = der Akte-Mutex des Dienstes (svc.lock), `markieren(zeile)` = die
    Anwesenheits-Marke (core/anwesenheit.akte_zeile_markieren) — beides wird
    injiziert, damit dieses Modul nichts aus dem Dienst importiert."""
    import contextlib
    pfad = os.path.join(data_dir, "state", "deckung.jsonl")
    if not os.path.exists(pfad):
        return 0
    letzte = {}
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            try:
                d = json.loads(zeile)
            except Exception:
                _logbuch.swallowed(_log, _logbuch.WARNING, "skipped")
                continue
            if d.get("eid"):
                letzte[d["eid"]] = d                # last-wins je eid
    ts = round(time.time(), 1)
    neu_zeilen = []
    for eid, d in letzte.items():
        best = list(d.get("bestaetigt") or [])
        ours = d.get("ours") if isinstance(d.get("ours"), dict) else {}
        korr = d.get("korrektur") if isinstance(d.get("korrektur"), dict) else {}
        if alt not in best and alt not in ours and korr.get("person") != alt:
            continue
        z = dict(d)
        z["ts"] = ts
        if alt in best:
            z["bestaetigt"] = sorted({neu if p == alt else p for p in best})
        if alt in ours:
            o = dict(ours)
            _schluessel_tauschen(o, alt, neu)
            z["ours"] = o
        if korr.get("person") == alt:
            k = dict(korr)
            k["person"] = neu
            z["korrektur"] = k
        z["umbenannt"] = {"von": alt, "nach": neu, "ts": ts}
        neu_zeilen.append(z)
    if not neu_zeilen:
        return 0
    with (lock or contextlib.nullcontext()):
        with open(pfad, "a", encoding="utf-8") as f:
            for z in neu_zeilen:
                f.write(json.dumps(z, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    if markieren:
        for z in neu_zeilen:
            try:
                markieren(z)
            except Exception:
                _logbuch.swallowed(_log, _logbuch.WARNING, "ignored")
    return len(neu_zeilen)


def ground_truth_korrigieren(data_dir, alt, neu, log=None):
    """state/ground_truth.jsonl: Nutzer-Urteile ueber die IDENTITAET einer
    Person (Feld "label", bei Mehrfach-Marken "personen"), gelesen last-wins
    je eid -> APPEND. Der Bezug bleibt derselbe, nur der Name aendert sich.
    VORSICHT: "label" traegt auch Nicht-Personen-Marken (Unbekannt,
    Fehltrigger) — nur EXAKTE Treffer auf den Altnamen werden gehoben."""
    pfad = os.path.join(data_dir, "state", "ground_truth.jsonl")
    if not os.path.exists(pfad):
        return 0
    letzte = {}
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            try:
                d = json.loads(zeile)
            except Exception:
                _logbuch.swallowed(_log, _logbuch.WARNING, "skipped")
                continue
            if d.get("eid"):
                letzte[d["eid"]] = d
    ts = round(time.time(), 1)
    raus = []
    for eid, d in letzte.items():
        personen = d.get("personen")
        treffer_liste = isinstance(personen, list) and alt in personen
        if d.get("label") != alt and not treffer_liste:
            continue
        z = dict(d)
        z["ts"] = ts
        if z.get("label") == alt:
            z["label"] = neu
        if treffer_liste:
            z["personen"] = [neu if p == alt else p for p in personen]
        z["umbenannt"] = {"von": alt, "nach": neu, "ts": ts}
        raus.append(z)
    if not raus:
        return 0
    with open(pfad, "a", encoding="utf-8") as f:
        for z in raus:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return len(raus)


# Migratoren: Sync-Merker — entfallen mit E3b-3a (Bauplan analysen/bauplan_refquelle_einbau.md,
# Entscheid 10, I3): Abwahl, Frigate-Ablehnung und Export-Merker haengen als Katalogzeilen an der
# ref_id, nicht am Namen; der Laufstand der Vorpruefung ist je ref_id geschluesselt; Bericht,
# Fortschritt und Auswahl eines Exportlaufs tragen den Personennamen nur als Anzeige bzw. fuer
# genau einen Lauf. Ein Umbenennen hat dort nichts umzuhaengen.


# ------------------------------------------------------------------- Protokoll
def protokoll_anhaengen(data_dir, eintrag):
    """state/umbenennungen.jsonl (Muster state/uebernahmen.jsonl): WAS
    passiert ist, mit Zahlen je Bestand. /person_loeschen ist bewusst
    umkehrbar (Papierkorb); ein reiner os.rename hinterlaesst keine Spur.
    Mit dem Protokoll ist erstens nachvollziehbar, was der Zug angefasst hat,
    zweitens laesst sich ein Rueckweg bauen, drittens faellt auf, wenn ein
    Bestand beim naechsten Ausbau vergessen wird."""
    pfad = os.path.join(data_dir, "state", "umbenennungen.jsonl")
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": round(time.time(), 1), **eintrag},
                           ensure_ascii=False) + "\n")
        f.flush()
    return True


# ------------------------------------------------------------------ Eingangstor
def ziel_pruefen(neu, alt, personen_kanonisch, person_re):
    """Die Eingangspruefung des Zielnamens — VOR jeder Schreibhandlung.
    personen_kanonisch = Callable(name) -> kanonischer Bestandsname oder None
    (core/benennung.namens_kollision gegen personen_quelle, MIT dem eigenen
    Altnamen herausgenommen: sonst meldet jede reine Gross-/Klein-
    schreibungs-Korrektur eine Kollision mit sich selbst).
    -> (ok, kennung, kanonisch). kennung ist ein Textschluessel fuer die
    Antwort, nie ein fertiger Satz (die Sprache waehlt der Aufrufer)."""
    if not neu:
        return False, "leer", None
    if neu == alt:
        return False, "gleich", None
    if neu in RESERVIERT or alt in RESERVIERT:
        return False, "reserviert", None
    if os.sep in neu or "/" in neu or neu in (".", ".."):
        return False, "pfad", None
    if not re.fullmatch(person_re, neu):
        return False, "ungueltig", None
    kanon = personen_kanonisch(neu)
    if kanon:
        return False, "kollision", kanon
    return True, "ok", None


# ----------------------------------------------------------------- Orchestrierung
# Die Schritte in der Reihenfolge, in der sie laufen. Je Eintrag:
# (kennung, Migrator-Name, Sammel-Kennung fuers Protokoll). Die Liste IST der
# Ablauf — wer einen Bestand ergaenzt, ergaenzt ihn hier UND im Vertrag oben,
# und die Gate-Stufe haelt beides gegeneinander.
ABLAUF = (
    "katalog_umbenennen",
    "vorschlaege_umbenennen",
    "gesichter_nn_umschreiben",
    "enroll_queue_umschreiben",
    "anker_umschreiben",
    "uebernahmen_umschreiben",
    "lernlauf_manifeste_umschreiben",
    "lernlauf_vorrat_umschreiben",
    "personlern_manifeste_umschreiben",
    "personlern_galerie_umbenennen",
    "personlern_status_umschreiben",
    "personlern_live_umschreiben",
    "live_meldungen_umschreiben",
)


def umbenennen(data_dir, alt, neu, umfeld=None, puls=None, log=None):
    """DER Zug. Reihenfolge ist Absicht, nicht Geschmack:

    1. Live-Engine STOPPEN, bevor irgendetwas wandert. Sie laedt die
       Referenzen genau einmal beim Start (core/livewached) und hat KEINEN
       Reload-Weg; laeuft sie weiter, meldet sie den Altnamen samt
       MQTT-Payload und Beweisbild-Dateinamen. Ausserdem haengt sie an
       live/meldungen.jsonl an, das hier umgeschrieben wird.
    2. Der Katalog ZUERST (seit E3b-3b ueber das Modul, Bindung-Zeilen mit dem
       neuen Namen, kein Satz angefasst): ab diesem Moment liefert
       master_persons den neuen Namen, also arbeiten alle NEU startenden
       Analysen und Subprozesse richtig; der Worker liest die Referenzen bei
       neuer Stand-Kennung selbst neu. Alles Weitere haengt daran.
    3. Die uebrigen Bestaende in der Reihenfolge von `ABLAUF`.
    4. Der Event-Durchgang in ZWEI Runden: erst alle Ordner, dann noch einmal
       nur die, die seit dem Start des Zugs geschrieben wurden. Das faengt
       Ereignisse einer Analyse mit, die beim Start noch mit der alten
       Personenliste lief (bei mehreren Analyseplaetzen laufen sie parallel).
    5. Die AKTEN (deckung, ground_truth) ZULETZT und per Append. Sie werden
       last-wins je eid gelesen; wer sie zuletzt anfasst, erfasst auch die
       Zeilen, die eine nachlaufende Analyse waehrend des Zugs mit dem
       Altnamen geschrieben hat.
    6. Protokoll, dann Engine wieder starten und die Nachlaeufe anstossen
       (QS-Bericht, Koerper-Training).

    umfeld = Dienst-Griffe, alle optional (Injektionsreinheit — dieses Modul
    importiert nichts aus verifyd): akte_lock, akte_markieren, engine_stoppen,
    engine_starten, worker_stoppen, last_seen_umhaengen, qs_neu, training.
    Fehlt ein Griff, wird der Schritt uebersprungen und das im
    Bericht vermerkt (`uebersprungen`) — nie still.
    -> Bericht (dict), der auch ins Protokoll geht."""
    u = dict(umfeld or {})
    start_ts = time.time()
    bericht = {"alt": alt, "neu": neu, "zahlen": {}, "fehler": {},
               "uebersprungen": [], "start": round(start_ts, 1)}

    def _melde(text, stufe=_logbuch.INFO):
        if log:
            log.log(stufe, f"rename {alt!r} -> {neu!r}: {text}")

    def _griff(name):
        g = u.get(name)
        if g is None:
            bericht["uebersprungen"].append(name)
        return g

    g = _griff("engine_stoppen")
    if g:
        try:
            g()
            _melde("live engine stopped (it loads references only at start)")
        except Exception as e:
            bericht["fehler"]["engine_stoppen"] = f"{type(e).__name__}: {e}"

    for i, name in enumerate(ABLAUF):
        if puls:
            puls("bestaende", i, len(ABLAUF))
        fn = globals()[name]
        try:
            bericht["zahlen"][name] = fn(data_dir, alt, neu, log=log)
        except Exception as e:
            bericht["fehler"][name] = f"{type(e).__name__}: {e}"
            _melde(f"step {name} FAILED: {type(e).__name__}: {e}", stufe=_logbuch.ERROR)
            if fn is katalog_umbenennen:
                # Ohne die Bindung im Katalog gibt es die Person unter dem neuen
                # Namen gar nicht — weitermachen hiesse, den Bestand zu zerlegen.
                bericht["abbruch"] = name
                return bericht

    g = _griff("last_seen_umhaengen")
    if g:
        try:
            g(alt, neu)
        except Exception as e:
            bericht["fehler"]["last_seen_umhaengen"] = f"{type(e).__name__}: {e}"
    g = _griff("worker_stoppen")
    if g:
        try:
            g()                        # baut sich lazy neu auf, liest Refs je Lauf
        except Exception as e:
            bericht["fehler"]["worker_stoppen"] = f"{type(e).__name__}: {e}"

    try:
        bericht["zahlen"]["event_durchgang"] = event_durchgang(
            data_dir, alt, neu, log=log,
            puls=(lambda i, n: puls("events", i, n)) if puls else None)
    except Exception as e:
        bericht["fehler"]["event_durchgang"] = f"{type(e).__name__}: {e}"
    try:
        # Zweite Runde: nur Ordner, die seit dem Start geschrieben wurden.
        bericht["zahlen"]["event_nachlauf"] = event_durchgang(
            data_dir, alt, neu, log=log, nur_ab_mtime=start_ts,
            puls=(lambda i, n: puls("events_nachlauf", i, n)) if puls else None)
    except Exception as e:
        bericht["fehler"]["event_nachlauf"] = f"{type(e).__name__}: {e}"

    try:
        bericht["zahlen"]["deckung_korrigieren"] = deckung_korrigieren(
            data_dir, alt, neu, log=log, lock=u.get("akte_lock"),
            markieren=u.get("akte_markieren"))
    except Exception as e:
        bericht["fehler"]["deckung_korrigieren"] = f"{type(e).__name__}: {e}"
    try:
        bericht["zahlen"]["ground_truth_korrigieren"] = ground_truth_korrigieren(
            data_dir, alt, neu, log=log)
    except Exception as e:
        bericht["fehler"]["ground_truth_korrigieren"] = f"{type(e).__name__}: {e}"

    bericht["dauer_s"] = round(time.time() - start_ts, 1)
    try:
        protokoll_anhaengen(data_dir, bericht)
    except Exception as e:
        bericht["fehler"]["protokoll"] = f"{type(e).__name__}: {e}"

    for name in ("engine_starten", "qs_neu", "training"):
        g = _griff(name)
        if g:
            try:
                g()
            except Exception as e:
                bericht["fehler"][name] = f"{type(e).__name__}: {e}"
    _melde(f"done in {bericht['dauer_s']}s — {bericht['zahlen']}")
    return bericht
