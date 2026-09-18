"""core/umbenennen — Person umbenennen: EIN Zug ueber ALLE namenstragenden Bestaende.

ANLASS (Betreiber 21.08.2026, gebaut 18.09.2026 in .542): einen Tippfehler im
Personennamen korrigieren. Das Vorbild `/person_loeschen` (verifyd.py) ist
bewusst KEIN Muster: es verschiebt den Ordner in den Papierkorb, und alles
andere filtert danach implizit ueber die Existenz (die Person ist weg).
Beim UMBENENNEN kehrt sich das um — die Person existiert weiter, nur unter
einem neuen Namen, und jeder Speicher mit dem Altnamen wird zur stillen
Waise. Die vier Stellen, die den Unterschied zwischen "funktioniert" und
"verliert still" machen: `faces/refs_meta.jsonl` (traegt fuer Vorrats-
Referenzen den EINZIGEN Embedding-Vektor), die Event-Crop-Dateinamen (fuenf
reine Substring-Leser, kein Index daneben), `state/lernlauf/B*/vorrat.jsonl`
(offene Angebote samt Beiwert) und `personlern/<P*>/manifest.jsonl` (das
Trainings-Label — es erzeugt die Alt-Klasse ohne jede Nutzeraktion wieder).

DECKUNGS-VERTRAG (die eigentliche Arbeit, K3-Regel aus CLAUDE.md /
qs_ebenen.md): `BESTAENDE` unten ist die EINE Aufzaehlung der
namenstragenden Speicher — Kennung, Ort, Urteil, zustaendiger Migrator.
Sie ist gleichzeitig die Probenliste der Gate-Stufe
(`tools/gate/umbenennen_deckung.py`). Ohne diesen Vertrag wird der naechste
neue Speicher genauso vergessen, wie `state/anwesenheit/` in der
Alt-Inventur vom 21.08. fehlte (es gab ihn damals noch nicht) — und ein
vergessener Speicher ist hier kein Schoenheitsfehler, sondern ein stiller
Verlust oder ein FALSCHER Name in einer Live-Meldung.

WAS DIESES MODUL NICHT TUT: zusammenfuehren. Existiert der Zielname schon
(case-INsensitiv, geprueft mit `core/benennung.namens_kollision`), lehnt der
Aufrufer ab. Ein Merge hat eine andere Semantik je Bestand (zwei
Referenz-Historien in einem Journal-Schluesselraum, zwei Galerien, zwei
Modell-Klassen) und ist ein eigener Zug.

REIHENFOLGE (bewusst, s. `umbenennen()`): Ordner zuerst (ab da liefert
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

# Reservierte Namen: weder Quelle noch Ziel eines Umbenennens.
#   FREMD          — Klassenkennung des Koerper-Modells (core/personmodell,
#                    core/personlauf), kein Personenname.
#   refs_meta.jsonl / refs_mess.json — liegen FLACH in faces/ neben den
#                    Personenordnern; ein Personenordner mit diesem Namen
#                    wuerde den Katalog ueberschreiben.
RESERVIERT = ("FREMD", "refs_meta.jsonl", "refs_mess.json")


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
    ("faces_ordner",          "faces/<person>/",                    "muss",   "ordner_umbenennen"),
    ("refs_meta",             "faces/refs_meta.jsonl",              "muss",   "refs_meta_uebertragen"),
    ("refs_mess",             "faces/refs_mess.json",               "kann",   "refs_mess_umschreiben"),
    ("refcache",              "clips/refcache.npz",                 "muss",   "refcache_umschreiben"),
    ("refs_qs",               "learn/refs_qs.json",                 "muss",   "refs_qs_bereinigen"),
    ("vorschlaege",           "learn/vorschlaege_<person>.json",    "muss",   "vorschlaege_umbenennen"),
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
    ("sync_abwahl",           "state/sync_abwahl.json",             "muss",   "sync_merker_umschreiben"),
    ("sync_ablehnungen",      "state/sync_ablehnungen.json",        "muss",   "sync_merker_umschreiben"),
    ("sync_vorpruefung",      "state/sync_vorpruefung.json",        "kann",   "sync_merker_umschreiben"),
    ("sync_auswahl_lauf",     "state/sync_auswahl_lauf.json",       "kann",   "sync_merker_umschreiben"),
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
    ("backups_papierkorb",    "backups/master_*.tar.gz, trash/person_*",
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
                          "wertlos.",
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
        return standard


def _schluessel_tauschen(d, alt, neu):
    """dict-Schluessel `alt` -> `neu` (last-wins bei Kollision). -> True, wenn
    getauscht wurde."""
    if alt not in d:
        return False
    d[neu] = d.pop(alt)
    return True


# ---------------------------------------------------------- Migratoren: Referenzen
def ordner_umbenennen(data_dir, alt, neu, log=None):
    """faces/<alt> -> faces/<neu>. UEBER EINEN ZWISCHENNAMEN: auf einem
    case-INSENSITIVEN Volume (SMB-Share, Docker-Volume ueber einen macOS-/
    Windows-Wirt — bei fremden Installationen realistisch) ist
    os.rename("A", "a") je Plattform ein No-op oder ein Fehler. suslik wird
    als Companion veroeffentlicht; der Umweg kostet nichts und traegt dort."""
    q = os.path.join(data_dir, "faces", alt)
    z = os.path.join(data_dir, "faces", neu)
    if not os.path.isdir(q):
        raise FileNotFoundError(f"faces/{alt} fehlt")
    zwischen = os.path.join(data_dir, "faces", f".rename-{int(time.time())}-{os.getpid()}")
    os.rename(q, zwischen)
    try:
        os.rename(zwischen, z)
    except OSError:
        os.rename(zwischen, q)                      # zurueck, nichts halb Fertiges
        raise
    return 1


def refs_meta_uebertragen(data_dir, alt, neu, log=None):
    """faces/refs_meta.jsonl ist ein JOURNAL — Vertrag: "wird nur ANGEHAENGT,
    nie umgeschrieben" (sync_refs.py). Gelesen wird last-wins je
    (person, datei). Deshalb ANHAENGEN statt Rewrite: je Eintrag des Altnamens
    eine Zeile unter dem neuen Namen, `emb`/`emb_modell` MITGENOMMEN (fuer
    Vorrats-Referenzen ist das der EINZIGE Embedding-Vektor), und den
    Alt-Eintrag mit `aktiv: false` schliessen.
    TOMBSTONES ebenfalls uebernehmen: sonst holt der naechste Frigate-Import
    Bilder zurueck, die der Nutzer geloescht hat."""
    pfad = os.path.join(data_dir, "faces", "refs_meta.jsonl")
    if not os.path.exists(pfad):
        return 0
    letzte = {}
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            try:
                d = json.loads(zeile)
            except Exception:
                continue
            if d.get("person") == alt and d.get("datei"):
                letzte[d["datei"]] = d              # last-wins je Datei
    if not letzte:
        return 0
    ts = round(time.time(), 1)
    zeilen = []
    for datei, d in sorted(letzte.items()):
        neu_z = dict(d)
        neu_z["person"] = neu
        neu_z["ts"] = ts
        neu_z["umbenannt_von"] = alt
        zeilen.append(neu_z)
        if d.get("aktiv", True):
            # Alt-Schluessel schliessen, damit lade_meta ihn nicht mehr als
            # aktiv fuehrt (der Ordner ist weg, die Datei liegt jetzt unter neu).
            zeilen.append({"ts": ts, "person": alt, "datei": datei,
                           "aktiv": False, "grund": "renamed", "nach": neu})
    with open(pfad, "a", encoding="utf-8") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return len(letzte)


def refs_mess_umschreiben(data_dir, alt, neu, log=None):
    """faces/refs_mess.json: bilder[PERSON][DATEI] — Mess-Sidecar des Katalogs
    (core/refmess). Reiner Cache; re-key ist billiger als ein Neumesslauf."""
    pfad = os.path.join(data_dir, "faces", "refs_mess.json")
    d = _json_lesen(pfad, {})
    bilder = d.get("bilder")
    if not isinstance(bilder, dict) or alt not in bilder:
        return 0
    n = len(bilder.get(alt) or {})
    _schluessel_tauschen(bilder, alt, neu)
    _atomar.json_schreiben(pfad, d)
    return n


def refcache_umschreiben(data_dir, alt, neu, log=None):
    """clips/refcache.npz: Array-Schluessel + "§meta" (erwartete Dateiliste je
    Person) + "§rows" (Datei je Matrixzeile) re-keyen.

    PFLICHT, nicht Kuer: `core/livewache.referenzen_laden` prueft den Cache nur
    gegen "§modell", NICHT gegen die Dateilisten — ein stehen gelassener Cache
    liefert der Live-Engine also weiter die ALTEN Personen-Keys, und die Wache
    meldet den Altnamen samt MQTT-Payload und Beweisbild-Dateinamen. Dass die
    Engine ohnehin neu startet, genuegt nicht: sie liest denselben Cache.
    -> Zahl der uebertragenen Referenzzeilen; -1, wenn der Cache verworfen
    werden musste (der Aufrufer stoesst dann den Neuaufbau an)."""
    import numpy as np
    ziel = os.path.join(data_dir, "clips", "refcache.npz")
    if not os.path.exists(ziel):
        return 0
    try:
        z = np.load(ziel, allow_pickle=True)
        meta_roh = z["§meta"] if "§meta" in z.files else (
            z["meta"] if "meta" in z.files else None)
        meta = json.loads(str(meta_roh)) if meta_roh is not None else {}
        refs = {p: np.asarray(z[p], np.float32) for p in z.files
                if p not in ("meta", "§meta")}
        want = {k: list(w) for k, w in meta.items() if not str(k).startswith("§")}
        rows = meta.get("§rows")
        if alt not in refs and alt not in want:
            return 0                                # Person war nicht im Cache
        n = len(want.get(alt) or refs.get(alt, ()))
        _schluessel_tauschen(refs, alt, neu)
        _schluessel_tauschen(want, alt, neu)
        if isinstance(rows, dict):
            _schluessel_tauschen(rows, alt, neu)
        _neu = {**want, "§modell": str(meta.get("§modell", ""))}
        if isinstance(rows, dict):
            _neu["§rows"] = rows
        _atomar.schreiben(
            ziel, lambda f: np.savez(f, **{"§meta": json.dumps(_neu)}, **refs),
            suffix=".npz", binaer=True)
        return n
    except Exception as e:
        if log:
            log(f"rename: refcache re-key failed ({type(e).__name__}: {e}) — "
                f"cache discarded, it will be rebuilt")
        try:
            os.remove(ziel)
        except OSError:
            pass
        return -1


# --------------------------------------------------------------- Migratoren: learn
def refs_qs_bereinigen(data_dir, alt, neu, log=None):
    """learn/refs_qs.json: der Bericht ist person-keyed in neun Achsen
    (Deckungsvertrag QS_BERICHT_FELDER). Statt neun Achsen von Hand zu
    re-keyen, wird die Person mit dem VORHANDENEN chirurgischen Bereiniger
    aus dem Bericht genommen — der Aufrufer stoesst danach `qs_neu_starten()`
    an. Das ist der Weg, den /person_loeschen seit .511 schon geht; er kennt
    alle Achsen und bleibt beim naechsten Achsen-Zubau richtig."""
    import anlernen
    return 1 if anlernen.qs_bericht_bereinigen(alt) else 0


def vorschlaege_umbenennen(data_dir, alt, neu, log=None):
    """learn/vorschlaege_<person mit _>.json: der Name steckt im DATEINAMEN
    und im Feld "person". Die Abbildung ' ' -> '_' ist NICHT injektiv
    ("A B" und "A_B" teilen dieselbe Datei) — liegt am Zielpfad schon eine
    fremde Vorschlagsdatei, wird NICHT ueberschrieben, sondern gemeldet."""
    import anlernen
    return anlernen.vorschlaege_umbenennen(alt, neu, log=log)


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
            log(f"rename: gallery folder for the new name already exists — "
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
                continue
        beruehrt = False
        try:
            dateien = os.listdir(ordner)
        except OSError:
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
                        pass
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
                pass
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


# ------------------------------------------------------ Migratoren: Sync-Merker
def sync_merker_umschreiben(data_dir, alt, neu, log=None):
    """Die vier Frigate-Sync-Merker mit "<Person>/<Datei>"-Schluesseln
    (sync_refs.schluessel — der Schluessel wird NIE selbst zusammengebaut):

    - sync_abwahl.json     MUSS: ein bewusster Nutzer-Entscheid ("nie
      exportieren"), nicht regenerierbar. Ohne Migration schickt der naechste
      Auto-Export genau die Bilder nach Frigate, die zurueckgehalten wurden.
    - sync_ablehnungen.json MUSS: ohne Migration versucht der Export wieder und
      wieder dieselben Bilder, die Frigate deterministisch ablehnt.
    - sync_vorpruefung.json KANN: reiner Cache, invalidiert sich ueber den
      mtime-Lookup selbst — wird trotzdem umgehaengt, weil ein Neulauf einen
      vollen Embedder-Durchgang kostet.
    - sync_auswahl_lauf.json KANN: kurzlebiger Ein-Lauf-Zustand; er wird
      umgehaengt statt still fallen gelassen.
    -> {kennung: Zahl der umgehaengten Eintraege}"""
    import sync_refs
    erg = {}
    for name in ("sync_abwahl", "sync_ablehnungen", "sync_vorpruefung"):
        pfad = os.path.join(data_dir, "state", f"{name}.json")
        d = _json_lesen(pfad, {})
        if not d:
            erg[name] = 0
            continue
        n, raus = 0, {}
        for k, v in d.items():
            person, _, datei = str(k).partition("/")
            if person == alt and datei:
                raus[sync_refs.schluessel(neu, datei)] = (
                    {**v, "person": neu} if isinstance(v, dict) and "person" in v else v)
                n += 1
            else:
                raus[k] = v
        if n:
            _atomar.json_schreiben(pfad, raus)
        erg[name] = n
    pfad = os.path.join(data_dir, "state", "sync_auswahl_lauf.json")
    liste = _json_lesen(pfad, [])
    n = 0
    if liste:
        raus = []
        for e in liste:
            if isinstance(e, (list, tuple)) and len(e) == 2 and e[0] == alt:
                raus.append([neu, e[1]])
                n += 1
            else:
                raus.append(e)
        if n:
            _atomar.json_schreiben(pfad, raus)
    erg["sync_auswahl_lauf"] = n
    return erg


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
    "ordner_umbenennen",
    "refs_meta_uebertragen",
    "refcache_umschreiben",
    "refs_mess_umschreiben",
    "refs_qs_bereinigen",
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
    "sync_merker_umschreiben",
)


def umbenennen(data_dir, alt, neu, umfeld=None, puls=None, log=None):
    """DER Zug. Reihenfolge ist Absicht, nicht Geschmack:

    1. Live-Engine STOPPEN, bevor irgendetwas wandert. Sie laedt die
       Referenzen genau einmal beim Start (core/livewached) und hat KEINEN
       Reload-Weg; laeuft sie weiter, meldet sie den Altnamen samt
       MQTT-Payload und Beweisbild-Dateinamen. Ausserdem haengt sie an
       live/meldungen.jsonl an, das hier umgeschrieben wird.
    2. faces/<alt> -> faces/<neu> ZUERST: ab diesem Moment liefert
       master_persons den neuen Namen, also arbeiten alle NEU startenden
       Analysen und Subprozesse richtig. Alles Weitere haengt daran.
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
       (QS-Bericht, Koerper-Training, ggf. refcache-Neuaufbau).

    umfeld = Dienst-Griffe, alle optional (Injektionsreinheit — dieses Modul
    importiert nichts aus verifyd): akte_lock, akte_markieren, engine_stoppen,
    engine_starten, worker_stoppen, last_seen_umhaengen, qs_neu, training,
    refcache_neu. Fehlt ein Griff, wird der Schritt uebersprungen und das im
    Bericht vermerkt (`uebersprungen`) — nie still.
    -> Bericht (dict), der auch ins Protokoll geht."""
    u = dict(umfeld or {})
    start_ts = time.time()
    bericht = {"alt": alt, "neu": neu, "zahlen": {}, "fehler": {},
               "uebersprungen": [], "start": round(start_ts, 1)}

    def _melde(text):
        if log:
            log(f"rename {alt!r} -> {neu!r}: {text}")

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
            _melde(f"step {name} FAILED: {type(e).__name__}: {e}")
            if name == "ordner_umbenennen":
                # Ohne den Ordner gibt es die Person unter dem neuen Namen gar
                # nicht — weitermachen hiesse, den Bestand zu zerlegen.
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
    if bericht["zahlen"].get("refcache_umschreiben") == -1:
        g = _griff("refcache_neu")
        if g:
            try:
                g()
            except Exception as e:
                bericht["fehler"]["refcache_neu"] = f"{type(e).__name__}: {e}"
    _melde(f"done in {bericht['dauer_s']}s — {bericht['zahlen']}")
    return bericht
