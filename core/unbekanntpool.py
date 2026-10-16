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
"""
import json
import os
import time
from core import logbuch as _logbuch
_log = _logbuch.logger(__name__)

# Alterungs- UND Reaktivierungs-Fenster der Unbekannt-Cluster in Tagen — EINE
# Quelle (QS-Ebenen-Regel, kein Streu-Literal): anlernen._reconcile_intern
# archiviert Einmal-Gaenger, deren letzte Stuetze aelter ist, und reaktiviert
# Archiv-Cluster mit juengerer Stuetze (Widerleger MUSS-2, Realfall U155);
# tages_archiv unten misst Frische mit demselben Fenster.
ARCHIV_TAGE = 7


def member_ts(m):
    """Zeit einer Altbestand-Stuetze aus dem Event-ID-Praefix ('1786538554.456565-u3ocpl~2'), das Format der
    Pool-Mitglieder; ein Satz-Mitglied traegt seine Zeit im Satz (mitglieder). None bei Unlesbarem."""
    try:
        return float(str(m).split("-", 1)[0])
    except ValueError:
        return None


def _cluster_lesen(data_dir):
    """Zeilenweiser Roh-Leser der unbekannte.jsonl — fehlende Datei/kaputte
    Zeilen fallen still raus (die Kacheln fallen dann auf die alte Anzeige
    zurueck, kein Fehler im Request-Pfad). Nur DICTS werden geliefert (eine
    nackte Zahl als JSON-Zeile traefe sonst jeden Konsumenten mit
    AttributeError — kc_unbekannt R-4)."""
    pfad = os.path.join(data_dir, "learn", "unbekannte.jsonl")
    try:
        f = open(pfad)
    except OSError:
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning None")
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
                continue
            if isinstance(d, dict):
                yield d


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


def identitaeten(data_dir):
    """Die Identitaetszeilen der unbekannte.jsonl ueber den einen Roh-Leser, je Kennung (uid oder id).
    -> {uid: Zeile}"""
    out = {}
    for d in _cluster_lesen(data_dir):
        uid = d.get("uid") or d.get("id")
        if isinstance(uid, str) and uid:
            out[uid] = d
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
                     "satz": False} for m in mem]
    if kaputt:
        _fehler(log, f"!! unbekannte.jsonl: {kaputt} unreadable cluster line(s) "
                     f"skipped on the unknown members — check the pool file")
    return out


def mitglieder(data_dir, idents=None, log=None):
    """Die Mitglieder jeder Unbekannt-Identitaet aus beiden Teilen: gebundene Saetze (core.refquelle) und Altbestand; Saetze
    an eine Kennung ohne Identitaetszeile zaehlen nicht (die raeumt der Verbraucher, W21). -> {uid: [Mitglied]} nach Zeit;
    Mitglied = {id, eid, ts, kamera, ref_id, satz}, id ist beim Satz die ref_id, beim Altbestand die Pool-Kennung"""
    idents = identitaeten(data_dir) if idents is None else idents
    out = {uid: [] for uid in idents}
    for uid, ms in altbestand(idents, log).items():
        out[uid].extend(ms)
    try:
        from core import refquelle as _rq           # noqa: PLC0415  schwer, nur bei Bedarf
        saetze = _rq.unknown_member_rows({"data_dir": data_dir})
    except Exception as e:                          # noqa: BLE001  laut, die Seite lebt weiter
        _fehler(log, f"!! unknown identities: bound sets not readable ({type(e).__name__}: {e}) "
                     f"— only the legacy members are shown")
        saetze = {}
    for uid, ms in saetze.items():
        if uid in out:
            out[uid].extend({"id": m["ref_id"], "eid": m["eid"], "ts": m["ts"], "kamera": m["kamera"],
                             "ref_id": m["ref_id"], "satz": True} for m in ms)
    for ms in out.values():
        ms.sort(key=lambda m: (not isinstance(m["ts"], (int, float)), m["ts"] or 0, m["id"]))
    return out


def _zeiten(ms, von, bis):
    return [m["ts"] for m in ms if isinstance(m["ts"], (int, float)) and von <= m["ts"] < bis]


def tages_cluster(data_dir, von, bis, gap_s, log=None):
    """{uid: auftritte} aller AKTIVEN Nicht-Objekt-Identitaeten mit mindestens einem Mitglied in [von, bis) (Satz oder
    Altbestand, mitglieder). auftritte = mit gap_s zu Besuchen gebuendelte Mitglieder im Fenster (besuche_zaehlen).

    Zaehlt NIE: objekt=true (statische Objekte sind keine Besucher), status != "aktiv" (stillgestellte Besucher, Archiv —
    den U155-Fall "Archiv mit frischer Stuetze" zaehlt tages_archiv separat). Fehlender Pool -> {}. Eine kaputte Zeile
    kostet nur sich selbst, mit Fehlerzeile (log, altbestand), nie die Seite (kc_unbekannt R-4/KANN-6)."""
    idents = identitaeten(data_dir)
    out = {}
    for uid, ms in mitglieder(data_dir, idents, log).items():
        d = idents[uid]
        if d.get("objekt") or d.get("status", "aktiv") != "aktiv":
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
