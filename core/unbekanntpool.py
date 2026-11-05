"""core/unbekanntpool — die EINE Ableitung "Unbekannt-Cluster mit Stuetzen im
Zeitfenster" (Runde R-2026-08-12-unbekannt-sichtbarkeit, Baustein A+B).

Anlass (Realfall 12.08., Besuch 13:12-15:02): der Unbekannt-Pool hatte frische
Cluster des Besuchs eingesammelt, aber die Today-Kachel zaehlte nur unerkannte
PASSES — Unbekannte, die MIT einer erkannten Person kommen (der haeufigste
Besuchsfall), verschwanden als Fussnote "not matched … normally the same people".
Diese Ableitung speist deshalb BEIDE neuen Sichtbarkeits-Stellen aus derselben
Quelle (QS-Ebenen-Regel: zentrale Quelle statt Streu-Aufzaehlung):
  - verifyd /heute: "N unknown person(s) today/on this day (M appearances)" in
    der Unidentified-Kachel, Link auf People->Unknown; dazu die Archiv-Zeile
    (tages_archiv) fuer den U155-Fall (Widerleger MUSS-2)
  - verifyd /lernlauf: Hinweis-Kasten "K unknown visitors are waiting"

Bewusst OHNE anlernen-Import: /heute liest den Pool schon heute als rohe Datei
(billig, kein cv2/Embedder im Request-Pfad); diese Datei-Leseart bleibt.

MITGLIEDER (Bauplan analysen/bauplan_verbraucher_unbekannt.md, Entscheid 10, Stufe V1c Punkt 2, W9): eine
Unbekannt-Identitaet besteht aus gebundenen Saetzen der Referenz-Quelle (core.refquelle.unknown_member_rows, Zeit und
Kamera aus dem Satz) und dem Altbestand, der Liste members ihrer Zeile (Pool-Zeilen, nur gelesen, nie neu befuellt;
altbestand). mitglieder ist der EINE Leser beider Teile fuer die Oberflaeche: Heute-Seite, /auftritte?u=, Unbekannt-Seite,
Faces-Zaehler, Lernlauf-Hinweis (ueber tages_cluster) und anlernen. Die Zeit eines Altbestand-Mitglieds steht nur in seiner
Kennung (Event-ID-Praefix, member_ts); ein Satz-Mitglied traegt sie in seiner Herkunft (Nebenbefund 11 des Faktenblatts).

SEITE „UNBEKANNTE“ ZUM BENENNEN (Bauplan analysen/bauplan_benennen.md Fassung 3, Stufe BN2 Punkte 1, 2 und 4, Entscheide
E1 und E2): offene_einheiten ist der Leser der offenen Einheiten (einzelne Identitaeten und Sammelbecken „ähnlich P“,
Status aktiv und kein objekt wie in tages_cluster) mit ihren Mitgliedern im Fenster (fenster: heute und die Tage davor,
lokal) und einem Status vollstaendig oder Teilmenge mit Grund; er oeffnet weder die Akte noch eine Stapel-Datei.
Nachzug BN2 (Eigentuemer 25.10.2026 18:39:34): Saetze, Zeit, Kamera und gespeicherte Norm kommen ueber mitglieder aus
core.refquelle.unknown_member_rows, ohne Kopie des Katalogs (kein read_catalog); deren Luecken (Satz-Ordner fehlt,
quelle.json oder Katalogzeile unlesbar) macht der Leser zur Teilmenge mit Grund (mitglieder, luecken). Identitaeten des
alten Wegs (Feld members) kommen mit ihren gebundenen Saetzen, ihre Pool-Mitglieder nicht (weder Norm noch Bild auf der
Seite). seite_waehlen schneidet Reiter und Seite zu, erst danach liest bildwahl
die Stapel-Dateien, nur fuer die gezeigten Kacheln (benennen_seite fuegt beides zusammen). Uebernehmbar ist ein Bild, wenn
seine gespeicherte Norm die hoehere aus Katalog-Latte und Erkennen-Latte seiner Kamera schafft (norm_latte, E1);
auswahl_pruefen prueft eine Auswahl beim Benennen genauso. Die Werte der Seite kommen aus der Config (benennen_werte,
Werkswerte core.registry.BENENNEN_WERK). Referenzen und ihre Messwerte nur ueber core.refquelle.
Stufe FU1 (Bauplan analysen/bauplan_fix_unbekannte.md): nach E0 zeigt, zaehlt und uebernimmt die Seite nur Saetze im
neuen Format (_neues_format, die eine Stelle; das Merkmal liefert core.refquelle.unknown_member_rows), die uebrigen zaehlt
offene_einheiten in einer INFO-Zeile, auswahl_pruefen lehnt sie mit dem Grund altformat ab. Nach E3 liefert benennbar die
Einheiten nur mit Bildern ueber der Latte (Seite, Sprung, Antworten). Stufe NL1 (Bauplan
analysen/bauplan_reiter_nicht_lernbar.md): eine Einheit ohne solches Bild steht im dritten Reiter REITER_NICHT_LERNBAR
mit allen Bildern und dem Grund je Bild (Entscheid 1: nur ganze Gruppen; schwache Einzelbilder anderer Gruppen bleiben weg).
GRUPPENNUMMERN (Bauplan analysen/bauplan_datenordner_klein.md, Stufe DK2 Punkt 4): next_group_id ist die eine Vergabe
fuer alle vier Stellen, die eine neue Gruppe anlegen; die hoechste je vergebene Nummer steht in GROUP_NUMBER_FILE, damit
eine aufgeloeste Gruppe ihre Nummer nie an eine neue weitergibt (note_group_ids vor dem Aufloesen).
Ehrliche Grenzen: die Mitglieder eines Ereignisses tragen dieselbe Zeit (Start des Ereignisses), die Bildzeit kommt aus
der Stapel-Datei und fehlt ohne sie; eine unlesbare Katalogzeile zaehlt fuer alle Einheiten (ob sie eine Bindung war, ist
nicht zu erkennen) und bleibt in der prozesslokalen Stoerungsliste der Referenz-Quelle, auch wenn der Katalog danach
ersetzt wird (dann Teilmenge bis zum Neustart); eine kaputte members-Liste einer offenen Identitaet macht eine Teilmenge,
obwohl die Seite deren Pool-Mitglieder nicht zeigt.
"""
import datetime
import json
import os
import re
import time
from core import atomar as _atomar
from core import logbuch as _logbuch
from core import registry as _registry
_log = _logbuch.logger(__name__)

# Alterungs- UND Reaktivierungs-Fenster der Unbekannt-Cluster in Tagen — EINE
# Quelle (QS-Ebenen-Regel, kein Streu-Literal): anlernen._reconcile_intern
# archiviert Einmal-Gaenger, deren letzte Stuetze aelter ist, und reaktiviert
# Archiv-Cluster mit juengerer Stuetze (Widerleger MUSS-2, Realfall U155);
# tages_archiv unten misst Frische mit demselben Fenster.
ARCHIV_TAGE = 7

# Bauplan analysen/bauplan_datenordner_klein.md, Stufe DK2 Punkt 4 (Befund B2 der Codex-Pruefung): Gruppennummern werden
# nie wieder vergeben. Die hoechste je vergebene steht in dieser Zustandsdatei unter dem Datenordner; geschrieben wird sie
# nur unter anlernen.pool_lock, unter dem alle Stellen der Vergabe laufen (anlernen: Abgleich, Objekt-Reparatur, „nicht P“
# einer Auswahl, Aufloesen alter Gruppen; core/unbekannt_verbraucher: Deckung, dort ueber dieselbe Dateisperre mit Frist).
GROUP_NUMBER_FILE = os.path.join("learn", "unbekannt_nummer.json")
_GROUP_NUMBER_KEY = "hoechste"


def _group_number(uid):
    """Die Nummer einer Kennung 'U<n>'. -> int, 0 fuer jede andere Kennung"""
    return int(uid[1:]) if isinstance(uid, str) and uid[:1] == "U" and uid[1:].isdigit() else 0


def _highest_given(data_dir):
    """Die hoechste je vergebene Gruppennummer aus GROUP_NUMBER_FILE; ohne Datei 0.
    -> int; unlesbar: ERROR-Zeile und ValueError (nie still von vorn, sonst kaeme eine Nummer doppelt)"""
    try:
        with open(os.path.join(data_dir, GROUP_NUMBER_FILE), encoding="utf-8") as f:
            d = json.load(f)
    except FileNotFoundError:
        return 0
    except (OSError, ValueError) as e:
        d = f"{type(e).__name__}: {e}"
    n = d.get(_GROUP_NUMBER_KEY) if isinstance(d, dict) else None
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        _log.error(f"unknown groups: state file {GROUP_NUMBER_FILE} is not readable ({str(d)[:200]}) — no group number "
                   "given out")
        raise ValueError(f"group number state not readable: {GROUP_NUMBER_FILE}")
    return n


def note_group_ids(data_dir, ids):
    """Die hoechste je vergebene Gruppennummer mindestens auf die hoechste Nummer in ids heben (vor dem Entfernen von
    Gruppen, DK2 Punkt 4); der Aufrufer haelt anlernen.pool_lock. -> die hoechste je vergebene Nummer danach"""
    old = _highest_given(data_dir)
    high = max([old] + [_group_number(u) for u in ids])
    if high != old:
        _atomar.json_schreiben(os.path.join(data_dir, GROUP_NUMBER_FILE), {_GROUP_NUMBER_KEY: high})
    return high


def next_group_id(data_dir, ids):
    """Die naechste Gruppenkennung (DK2 Punkt 4): das Maximum aus den Nummern in ids (den vorhandenen Kennungen) und der
    hoechsten je vergebenen, plus eins; die vergebene wird atomar gemerkt, der Aufrufer haelt anlernen.pool_lock.
    -> 'U<n>'; unlesbare Zustandsdatei: ERROR-Zeile und ValueError"""
    n = max([_highest_given(data_dir)] + [_group_number(u) for u in ids]) + 1
    _atomar.json_schreiben(os.path.join(data_dir, GROUP_NUMBER_FILE), {_GROUP_NUMBER_KEY: n})
    return f"U{n}"


def member_ts(m):
    """Zeit einer Altbestand-Stuetze aus dem Event-ID-Praefix ('1786538554.456565-u3ocpl~2'), das Format der
    Pool-Mitglieder; ein Satz-Mitglied traegt seine Zeit im Satz (mitglieder). None bei Unlesbarem."""
    try:
        return float(str(m).split("-", 1)[0])
    except ValueError:
        return None


def pool_path(data_dir):
    """Der Pfad der Identitaetsdatei des Unbekannt-Pools (Bauplan analysen/bauplan_render_cache.md, Fassung 3 H4).
    -> Pfad <data_dir>/learn/unbekannte.jsonl"""
    return os.path.join(data_dir, "learn", "unbekannte.jsonl")


def _cluster_lesen(data_dir, zaehler=None):
    """Zeilenweiser Roh-Leser der unbekannte.jsonl — fehlende Datei/kaputte
    Zeilen fallen still raus (die Kacheln fallen dann auf die alte Anzeige
    zurueck, kein Fehler im Request-Pfad). Nur DICTS werden geliefert (eine
    nackte Zahl als JSON-Zeile traefe sonst jeden Konsumenten mit
    AttributeError — kc_unbekannt R-4). zaehler (dict, Stufe BN2): zaehlt
    uebersprungene Zeilen und nennt einen Lesefehler ausser einer fehlenden Datei."""
    pfad = pool_path(data_dir)
    try:
        f = open(pfad)
    except OSError as e:
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning None")
        if zaehler is not None and not isinstance(e, FileNotFoundError):
            zaehler["lesefehler"] = f"{type(e).__name__}: {e}"
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                _logbuch.swallowed(_log, _logbuch.WARNING, "skipped")
                d = None
            if isinstance(d, dict):
                yield d
            elif zaehler is not None:
                zaehler["uebersprungen"] = zaehler.get("uebersprungen", 0) + 1


def _fehler(log, text):
    """Eine Fehlerzeile ueber log (Logger mit error oder eine Funktion), ohne log ueber das Logbuch des Moduls."""
    (getattr(log, "error", log) if log else _log.error)(text)


def besuche_zaehlen(zeiten, gap_s):
    """Zeiten mit der Luecke gap_s zu Besuchen buendeln (dieselbe Regel wie Szenarien und Vorbesuche).
    -> Zahl der Besuche"""
    n, letzte = 0, None
    for t in sorted(zeiten):
        if letzte is None or t - letzte > gap_s:
            n += 1
        letzte = t
    return n


def identitaeten(data_dir, zaehler=None):
    """Die Identitaetszeilen der unbekannte.jsonl ueber den einen Roh-Leser, je Kennung (uid oder id); zaehler wie
    _cluster_lesen, eine Zeile ohne Kennung zaehlt als uebersprungen. -> {uid: Zeile}"""
    out = {}
    for d in _cluster_lesen(data_dir, zaehler):
        uid = d.get("uid") or d.get("id")
        if isinstance(uid, str) and uid:
            out[uid] = d
        elif zaehler is not None:
            zaehler["uebersprungen"] = zaehler.get("uebersprungen", 0) + 1
    return out


def altbestand(idents, log=None):
    """Der Altbestand-Leser (Entscheid 10, W1): die Liste members je Identitaet, nur gelesen; eine Zeile, deren members keine
    Liste von Kennungen ist, kostet nur sich selbst und wird laut gezaehlt. -> {uid: [Mitglied]}"""
    out, kaputt = {}, 0
    for uid, d in idents.items():
        mem = d.get("members")
        if mem is None:
            continue
        if not isinstance(mem, list) or not all(isinstance(m, str) for m in mem):
            kaputt += 1
            mem = [m for m in mem if isinstance(m, str)] if isinstance(mem, list) else []
        out[uid] = [{"id": m, "eid": m.split("~")[0], "ts": member_ts(m), "kamera": None, "ref_id": None,
                     "satz": False, "norm": None, "neues_format": False} for m in mem]
    if kaputt:
        _fehler(log, f"!! unbekannte.jsonl: {kaputt} unreadable cluster line(s) "
                     f"skipped on the unknown members — check the pool file")
    return out


def mitglieder(data_dir, idents=None, log=None, luecken=None):
    """Die Mitglieder jeder Unbekannt-Identitaet aus beiden Teilen: gebundene Saetze (core.refquelle) und Altbestand; Saetze
    an eine Kennung ohne Identitaetszeile zaehlen nicht (die raeumt der Verbraucher, W21). luecken (Liste, Nachzug BN2):
    nimmt je Grund einen englischen Text auf, wenn die Referenz-Quelle gebundene Saetze dieser Identitaeten uebersprungen
    oder nur unvollstaendig gelesen hat (eine unlesbare Katalogzeile zaehlt fuer alle). -> {uid: [Mitglied]} nach Zeit;
    Mitglied = {id, eid, ts, kamera, ref_id, satz, norm, neues_format}, id ist beim Satz die ref_id, beim Altbestand die
    Pool-Kennung; norm ist die gespeicherte Norm des Satzes (Zahl oder None), beim Altbestand None; neues_format ist das
    Merkmal nach E0 aus core.refquelle (Stufe FU1), beim Altbestand falsch"""
    idents = identitaeten(data_dir) if idents is None else idents
    out = {uid: [] for uid in idents}
    for uid, ms in altbestand(idents, log).items():
        out[uid].extend(ms)
    roh = []
    try:
        from core import refquelle as _rq           # noqa: PLC0415  schwer, nur bei Bedarf
        saetze = _rq.unknown_member_rows({"data_dir": data_dir}, roh)
    except Exception as e:                          # noqa: BLE001  laut, die Seite lebt weiter
        _fehler(log, f"!! unknown identities: bound sets not readable ({type(e).__name__}: {e}) "
                     f"— only the legacy members are shown")
        saetze = {}
    for uid, ms in saetze.items():
        if uid in out:
            out[uid].extend({"id": m["ref_id"], "eid": m["eid"], "ts": m["ts"], "kamera": m["kamera"],
                             "ref_id": m["ref_id"], "satz": True,
                             "norm": float(m["norm"]) if _zahl(m.get("norm")) else None,
                             "neues_format": m.get("neues_format") is True} for m in ms)
    for ms in out.values():
        ms.sort(key=lambda m: (not isinstance(m["ts"], (int, float)), m["ts"] or 0, m["id"]))
    if luecken is not None:
        zahl = {}
        for g in roh:
            if g["uid"] is None or g["uid"] in out:
                zahl[g["grund"]] = zahl.get(g["grund"], 0) + 1
        luecken.extend(f"reference source: {grund} ({n}x), bound sets missing or incomplete"
                       for grund, n in zahl.items())
    return out


def _zeiten(ms, von, bis):
    return [m["ts"] for m in ms if isinstance(m["ts"], (int, float)) and von <= m["ts"] < bis]


def _offen(d):
    """Die eine Regel „offen“ einer Identitaetszeile (tages_cluster und die Seite „Unbekannte“): Status aktiv, kein
    objekt. -> bool"""
    return not d.get("objekt") and d.get("status", "aktiv") == "aktiv"


def tages_cluster(data_dir, von, bis, gap_s, log=None):
    """{uid: auftritte} aller AKTIVEN Nicht-Objekt-Identitaeten mit mindestens einem Mitglied in [von, bis) (Satz oder
    Altbestand, mitglieder). auftritte = mit gap_s zu Besuchen gebuendelte Mitglieder im Fenster (besuche_zaehlen).

    Zaehlt NIE: objekt=true (statische Objekte sind keine Besucher), status != "aktiv" (stillgestellte Besucher, Archiv —
    den U155-Fall "Archiv mit frischer Stuetze" zaehlt tages_archiv separat). Fehlender Pool -> {}. Eine kaputte Zeile
    kostet nur sich selbst, mit Fehlerzeile (log, altbestand), nie die Seite (kc_unbekannt R-4/KANN-6)."""
    idents = identitaeten(data_dir)
    out = {}
    for uid, ms in mitglieder(data_dir, idents, log).items():
        if not _offen(idents[uid]):
            continue
        ts = _zeiten(ms, von, bis)
        if ts:
            out[uid] = besuche_zaehlen(ts, gap_s)
    return out


def tages_archiv(data_dir, von, bis, log=None, ohne=()):
    """Anzahl ARCHIVIERTER Nicht-Objekt-Identitaeten mit mindestens einem Mitglied in [von, bis), dessen juengstes im Fenster
    frisch genug ist (< ARCHIV_TAGE alt). Der U155-Fall (Widerleger MUSS-2): die Kachel darf eine frische Sichtung in einer
    archivierten Identitaet nicht still verstecken. Alte Mitglieder auf alten Tagen zaehlen bewusst NICHT; status
    "besucher" zaehlt nie (User-Entscheid, bewusst stummgestellt). Toleranz je Zeile wie tages_cluster.
    ohne: Kennungen, die nicht als Unbekannte zaehlen (die Heute-Seite reicht die Identitaeten, die als „vermutlich P“ gelten,
    Bauplan analysen/bauplan_aehnlich.md Entscheid 19). -> Zahl"""
    idents = identitaeten(data_dir)
    frisch_ab = time.time() - ARCHIV_TAGE * 86400
    n = 0
    for uid, ms in mitglieder(data_dir, idents, log).items():
        d = idents[uid]
        if d.get("objekt") or d.get("status") != "archiviert" or uid in ohne:
            continue
        ts = _zeiten(ms, von, bis)
        if ts and max(ts) >= frisch_ab:
            n += 1
    return n


# ---------------------------------------------------------------- Seite „Unbekannte“ zum Benennen (Stufe BN2)
# Die drei Reiter der Seite: mit Vorschlag (vermutlich P), ohne, und seit Stufe NL1 (Bauplan
# analysen/bauplan_reiter_nicht_lernbar.md) die Gruppen ohne ein Bild ueber der Latte („nicht gut genug zum Lernen“);
# die Art einer Einheit; die Herkunft der Reihenfolge eines Bildes (mass aus der Stapel-Datei oder nur die Zeit).
REITER_NICHT_LERNBAR = "nicht_lernbar"
REITER = ("aehnlich", "unbekannt", REITER_NICHT_LERNBAR)
ART_BECKEN, ART_IDENTITAET = "becken", "identitaet"
RANG_MASS, RANG_ZEIT = "mass", "zeit"
# Gruende, aus denen ein Bild nicht uebernommen wird: je Grund der englische Text der Log-Zeile und der Textschluessel der
# Antwort (core/texte, Platzhalter n); die eine Aufzaehlung fuer benennbar, Pruefung der Auswahl und Endpunkt.
GRUND_FREMD, GRUND_OHNE_NORM, GRUND_UNTER_LATTE = "fremd", "ohne_norm", "unter_latte"
GRUND_ALTFORMAT = "altformat"           # Stufe FU1, Entscheid E0: ein Satz der Gruppe, aber nicht im neuen Format
BENENN_GRUENDE = {
    GRUND_FREMD: ("not in this group", "antwort.benennen_grund_fremd"),
    GRUND_ALTFORMAT: ("stored before the new face storage", "antwort.benennen_grund_altformat"),
    GRUND_OHNE_NORM: ("no stored feature norm", "antwort.benennen_grund_ohne_norm"),
    GRUND_UNTER_LATTE: ("feature norm below the bar", "antwort.benennen_grund_unter_latte"),
}


def benennen_werte(cfg):
    """Die fuenf Werte der Seite „Unbekannte“ aus der Config, ohne Schluessel der Werkswert aus core.registry.BENENNEN_WERK.
    -> {Schluessel: int}"""
    return {k: int(cfg.get(k, w)) for k, w in _registry.BENENNEN_WERK.items()}


def fenster(tage, jetzt=None):
    """Das Fenster der Seite: heute und die tage-1 lokalen Kalendertage davor, bis Mitternacht nach heute.
    -> (von, bis) in Sekunden seit 1970"""
    heute = datetime.date.fromtimestamp(time.time() if jetzt is None else jetzt)
    von = heute - datetime.timedelta(days=max(1, int(tage)) - 1)
    return time.mktime(von.timetuple()), time.mktime((heute + datetime.timedelta(days=1)).timetuple())


def _zahl(x):
    """Eine Zahl, aber kein Wahrheitswert. -> bool"""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _neues_format(m):
    """Die eine Entscheidung nach E0 (Stufe FU1): ein gebundener Satz mit dem Merkmal des neuen Formats aus
    core.refquelle.unknown_member_rows; nur solche Mitglieder zeigt, zaehlt und uebernimmt die Seite. -> bool"""
    return m["satz"] and m["neues_format"] is True


def _einheit(uid, d, drin):
    """Eine Einheit der Seite aus Identitaetszeile und Mitgliedern im Fenster (neuestes zuerst).
    -> dict"""
    from core import aehnlich as _aeh                       # noqa: PLC0415  aehnlich liest dieses Modul
    vor = _aeh.vermutlich(d)
    becken = _aeh.sammel_von(d)
    return {"uid": uid, "art": ART_BECKEN if becken else ART_IDENTITAET, "person": becken,
            "vorschlag": vor["person"] if vor else None, "merkmal": vor, "reiter": REITER[0] if vor else REITER[1],
            "mitglieder": [{"ref_id": m["ref_id"], "eid": m["eid"], "ts": m["ts"], "kamera": m["kamera"],
                            "norm": m["norm"]} for m in drin],
            "letzte": drin[0]["ts"]}


def offene_einheiten(data_dir, von, bis):
    """Die offenen Einheiten mit Mitgliedern in [von, bis): Status aktiv, kein objekt, auch Identitaeten des alten Wegs
    (Feld members) mit ihren gebundenen Saetzen, ohne deren Pool-Mitglieder; nur Saetze im neuen Format (E0,
    _neues_format), die uebrigen zaehlt eine INFO-Zeile; je Mitglied eid, ts, kamera, ref_id, norm; Vorschlag ueber
    core.aehnlich.vermutlich. Oeffnet weder Akte noch Stapel, ruft read_catalog nicht; meldet die Referenz-Quelle eine
    Luecke, ist das Ergebnis eine Teilmenge mit ihrem Grund.
    -> {"einheiten": [Einheit] nach juengstem Mitglied, "vollstaendig": bool, "gruende": [Text englisch]}"""
    gruende, zaehler = [], {}
    idents = identitaeten(data_dir, zaehler)
    if zaehler.get("lesefehler"):
        gruende.append(f"identity file not readable ({zaehler['lesefehler']})")
    if zaehler.get("uebersprungen"):
        gruende.append(f"{zaehler['uebersprungen']} unreadable line(s) of the identity file skipped")
    offene = {u: d for u, d in idents.items() if _offen(d)}
    alle = mitglieder(data_dir, offene, gruende.append, gruende) if offene else {}
    einheiten, alt = [], 0
    for uid, d in offene.items():
        ms = [m for m in alle.get(uid, []) if _neues_format(m)]
        alt += sum(1 for m in alle.get(uid, []) if m["satz"]) - len(ms)
        drin = sorted((m for m in ms if von <= m["ts"] < bis), key=lambda m: (-m["ts"], m["ref_id"]))
        if drin:
            einheiten.append(_einheit(uid, d, drin))
    if alt:
        _log.info(f"unknown page: {alt} bound picture(s) of open groups stored before the new face storage, left out")
    einheiten.sort(key=lambda e: (-e["letzte"], e["uid"]))
    return {"einheiten": einheiten, "vollstaendig": not gruende, "gruende": gruende}


def seite_waehlen(einheiten, reiter, nr, je_seite):
    """Reiter und Seite zuschneiden (Seiten ab 1, eine Seite ausserhalb wird auf die naechste gueltige gesetzt).
    -> {"reiter", "nr", "seiten", "zahl": {Reiter: Zahl}, "einheiten": [Einheit der Seite]}"""
    if reiter not in REITER:
        raise ValueError(f"unknown tab {reiter!r} (one of {', '.join(REITER)})")
    liste = [e for e in einheiten if e["reiter"] == reiter]
    je = max(1, int(je_seite))
    seiten = max(1, -(-len(liste) // je))
    nr = min(max(1, int(nr)), seiten)
    return {"reiter": reiter, "nr": nr, "seiten": seiten,
            "zahl": {r: sum(1 for e in einheiten if e["reiter"] == r) for r in REITER},
            "einheiten": liste[(nr - 1) * je:nr * je]}


def norm_latte(cfg, kamera, guards=None):
    """Die Norm-Latte beim Uebernehmen (Entscheid E1): die hoehere aus Katalog-Latte und Erkennen-Latte dieser Kamera,
    beide ueber core.kamerakalib aufgeloest (Kamera, global, Werk). -> float"""
    from core import kamerakalib as _kk                     # noqa: PLC0415
    g = _kk.guards(cfg) if guards is None else guards
    return max(float(_kk.sieb_latten(_kk.katalog_latten(cfg), kamera)["n"]),
               float(_kk.erk_latten(cfg, g.get(kamera))["n"]))


def _grund(norm, latte):
    """Warum ein Bild nicht uebernommen wird, oder None, wenn seine gespeicherte Norm die Latte schafft.
    -> Grund aus BENENN_GRUENDE oder None"""
    if not _zahl(norm):
        return GRUND_OHNE_NORM
    return None if norm >= latte else GRUND_UNTER_LATTE


def _stapel_rang(data_dir, eid):
    """mass und Bildzeit je ref_id aus der Stapel-Datei des Ereignisses (bei mehreren Zeilen das groesste mass).
    -> {ref_id: (mass, bildzeit oder None)}, None ohne lesbare Datei"""
    from core.harvest_set import UNKNOWN_FILE              # noqa: PLC0415  der eine Name der Stapel-Datei
    if not (isinstance(eid, str) and re.fullmatch(_registry.EID_RE, eid) and eid not in (".", "..")):
        return None
    try:
        f = open(os.path.join(data_dir, "events", eid, UNKNOWN_FILE), encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning None")
        return None
    out = {}
    with f:
        for zeile in f:
            try:
                z = json.loads(zeile)
            except ValueError:
                _logbuch.swallowed(_log, _logbuch.WARNING, "skipped")
                continue
            for g in (z.get("gruppen") or []) if isinstance(z, dict) else []:
                for x in (g.get("gesichter") or []) if isinstance(g, dict) else []:
                    if isinstance(x, dict) and x.get("ref_id") and _zahl(x.get("mass")) \
                            and x["mass"] > out.get(x["ref_id"], (float("-inf"),))[0]:
                        out[x["ref_id"]] = (float(x["mass"]), x["bildzeit"] if _zahl(x.get("bildzeit")) else None)
    return out


def bildwahl(cfg, einheit, ereignisse, bilder):
    """Die Bilder einer gezeigten Kachel aus den Mitgliedern einer Einheit von benennbar (nur Bilder ueber der Latte, im
    Reiter REITER_NICHT_LERNBAR alle mit ihrem grund; je Mitglied mit latte): die besten nach mass aus den Stapel-Dateien
    der juengsten `ereignisse` Ereignisse (ohne Eintrag nach Zeit, Rang zeit), hoechstens `bilder`, gezeigt nach Zeit mit
    dem neuesten zuerst.
    -> [Mitglied mit mass, bildzeit, zeit, rang, latte]"""
    eids = list(dict.fromkeys(m["eid"] for m in einheit["mitglieder"]))[:max(1, int(ereignisse))]
    rang = {e: _stapel_rang(cfg["data_dir"], e) for e in eids}
    kand = []
    for m in einheit["mitglieder"]:
        if m["eid"] in rang:
            r = (rang[m["eid"]] or {}).get(m["ref_id"])
            b = dict(m, mass=r[0] if r else None, bildzeit=r[1] if r else None, rang=RANG_MASS if r else RANG_ZEIT)
            b["zeit"] = b["ts"] + (b["bildzeit"] or 0.0)
            kand.append(b)
    kand.sort(key=lambda b: (b["mass"] is None, -(b["mass"] or 0.0), -b["zeit"], b["ref_id"]))
    return sorted(kand[:max(0, int(bilder))], key=lambda b: (-b["zeit"], b["ref_id"]))


def benennbar(cfg, jetzt=None):
    """Die Einheiten der Seite im eingestellten Fenster (Stufe FU1, Entscheid E3; Stufe NL1), fuer die Seite, den Sprung
    und die Antworten der Handlungen: je Einheit nur Mitglieder, deren gespeicherte Norm die Latte ihrer Kamera schafft
    (norm_latte, je Mitglied als latte), nach Zeit, das neueste zuerst; eine Einheit ohne solches Mitglied steht mit allen
    Mitgliedern (je mit latte und grund aus _grund) im Reiter REITER_NICHT_LERNBAR. Daten bleiben unveraendert.
    -> {"werte", "einheiten": [Einheit] nach juengstem Mitglied, "vollstaendig", "gruende"}"""
    from core import kamerakalib as _kk                     # noqa: PLC0415
    w = benennen_werte(cfg)
    leser = offene_einheiten(cfg["data_dir"], *fenster(w["benennen_tage"], jetzt))
    g, latten = _kk.guards(cfg), {}
    einheiten = []
    for e in leser["einheiten"]:
        gut, schwach = [], []
        for m in e["mitglieder"]:
            if m["kamera"] not in latten:
                latten[m["kamera"]] = norm_latte(cfg, m["kamera"], g)
            grund = _grund(m["norm"], latten[m["kamera"]])
            if grund is None:
                gut.append(dict(m, latte=latten[m["kamera"]]))
            else:
                schwach.append(dict(m, latte=latten[m["kamera"]], grund=grund))
        if gut:
            einheiten.append(dict(e, mitglieder=gut, letzte=gut[0]["ts"]))
        else:
            einheiten.append(dict(e, mitglieder=schwach, reiter=REITER_NICHT_LERNBAR))
    einheiten.sort(key=lambda e: (-e["letzte"], e["uid"]))
    return {"werte": w, "einheiten": einheiten, "vollstaendig": leser["vollstaendig"], "gruende": leser["gruende"]}


def benennen_seite(cfg, reiter, nr=1, jetzt=None):
    """Die Daten einer Seite „Unbekannte“: die Einheiten (benennbar), Reiter und Seite, dann die Bildwahl nur fuer die
    Kacheln dieser Seite; alle Werte aus der Config (benennen_werte).
    -> {"werte", "vollstaendig", "gruende", "reiter", "nr", "seiten", "zahl", "karten": [Einheit mit bilder]}"""
    b = benennbar(cfg, jetzt)
    w = b["werte"]
    s = seite_waehlen(b["einheiten"], reiter, nr, w["benennen_karten_je_seite"])
    karten = [dict(e, bilder=bildwahl(cfg, e, w["benennen_ereignisse_je_karte"], w["benennen_bilder_je_karte"]))
              for e in s.pop("einheiten")]
    return dict(s, werte=w, vollstaendig=b["vollstaendig"], gruende=b["gruende"], karten=karten)


def auswahl_pruefen(cfg, uid, ids):
    """Eine Auswahl beim Benennen pruefen: nur gebundene Saetze der Identitaet uid im neuen Format (E0, sonst Grund
    altformat), deren gespeicherte Norm die Latte nach E1 schafft; ein Lesefehler geht an den Aufrufer.
    -> {"gut": [ref_id], "abgelehnt": [{ref_id, grund, norm, latte}]}"""
    from core import kamerakalib as _kk                     # noqa: PLC0415
    data_dir, fehler = cfg["data_dir"], []
    idents = identitaeten(data_dir)
    eigen = {}
    if uid in idents:
        eigen = {m["ref_id"]: m for m in mitglieder(data_dir, {uid: idents[uid]}, fehler.append).get(uid, [])
                 if m["satz"]}
    if fehler:
        raise RuntimeError("; ".join(fehler))
    g = _kk.guards(cfg)
    gut, abgelehnt = [], []
    for rid in dict.fromkeys(ids):
        m = eigen.get(rid)
        neu = bool(m) and _neues_format(m)
        norm, latte = (m["norm"] if m else None), (norm_latte(cfg, m["kamera"], g) if neu else None)
        grund = GRUND_FREMD if not m else GRUND_ALTFORMAT if not neu else _grund(norm, latte)
        if grund is None:
            gut.append(rid)
        else:
            abgelehnt.append({"ref_id": rid, "grund": grund, "norm": norm, "latte": latte})
    return {"gut": gut, "abgelehnt": abgelehnt}


def gruende_zaehlen(abgelehnt):
    """Die abgelehnten Bilder je Grund gezaehlt, in der Reihenfolge von BENENN_GRUENDE.
    -> [(Grund, Zahl)] nur mit Zahl ueber 0"""
    return [(g, n) for g in BENENN_GRUENDE if (n := sum(1 for a in abgelehnt if a["grund"] == g))]
