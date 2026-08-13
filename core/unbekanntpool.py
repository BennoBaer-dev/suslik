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
"""
import json
import os
import time

# Alterungs- UND Reaktivierungs-Fenster der Unbekannt-Cluster in Tagen — EINE
# Quelle (QS-Ebenen-Regel, kein Streu-Literal): anlernen._reconcile_intern
# archiviert Einmal-Gaenger, deren letzte Stuetze aelter ist, und reaktiviert
# Archiv-Cluster mit juengerer Stuetze (Widerleger MUSS-2, Realfall U155);
# tages_archiv unten misst Frische mit demselben Fenster.
ARCHIV_TAGE = 7


def member_ts(m):
    """Zeit einer Pool-Stuetze aus dem Event-ID-Praefix ('1786538554.456565-u3ocpl~2')
    — dieselbe Leseart wie die /heute-Karten (_besuche_vorher). None bei Unlesbarem."""
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
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if isinstance(d, dict):
                yield d


def tages_cluster(data_dir, von, bis, gap_s, log=None):
    """{uid: auftritte} aller AKTIVEN Nicht-Objekt-Cluster mit mindestens einer
    Stuetze in [von, bis). auftritte = mit gap_s zu Besuchen gebuendelte Stuetzen
    im Fenster (gleiche Buendel-Regel wie die Szenario-/Vorbesuchs-Zaehlung).

    Zaehlt NIE: objekt=true (statische Objekte sind keine Besucher), status
    != "aktiv" (stillgestellte Besucher, Archiv — den U155-Fall "Archiv mit
    frischer Stuetze" zaehlt tages_archiv separat). Fehlender/kaputter Pool
    -> {} (die Kachel faellt dann auf die alte Pass-Zaehlung zurueck).

    Toleranz JE CLUSTER (kc_unbekannt R-4/KANN-6: {"members": 5} warf
    TypeError ungefangen im /heute-Request): eine kaputte Zeile kostet nur
    sich selbst, nie die Seite — mit Warnzeile (log), nie still."""
    out = {}
    kaputt = 0
    for d in _cluster_lesen(data_dir):
        try:
            uid = d.get("uid") or d.get("id")
            if not uid or d.get("objekt"):
                continue
            if d.get("status", "aktiv") != "aktiv":
                continue
            ts = sorted(t for t in (member_ts(m) for m in (d.get("members") or []))
                        if t is not None and von <= t < bis)
            if not ts:
                continue
            n, letzte = 0, None
            for t in ts:
                if letzte is None or t - letzte > gap_s:
                    n += 1
                letzte = t
            out[uid] = n
        except (TypeError, ValueError, AttributeError):
            kaputt += 1
    if kaputt and log:
        log(f"!! unbekannte.jsonl: {kaputt} unreadable cluster line(s) "
            f"skipped on the Today derivation — check the pool file")
    return out


def tages_archiv(data_dir, von, bis, log=None):
    """Anzahl ARCHIVIERTER Nicht-Objekt-Cluster mit mindestens einer Stuetze in
    [von, bis), deren juengste Fenster-Stuetze frisch genug fuer die Reaktivierung
    ist (< ARCHIV_TAGE alt). Das ist der U155-Fall (Widerleger MUSS-2): eine
    frische Besuchs-Stuetze landete in einem archivierten Cluster — der naechste
    Reconcile reaktiviert ihn (anlernen), aber bis dahin darf die Kachel ihn
    nicht still verstecken. Alte Stuetzen auf alten Tagen zaehlen bewusst NICHT
    (regulaer gealterte Einmal-Gaenger sind Geschichte, keine verdeckten Besucher);
    status "besucher" zaehlt nie (User-Entscheid, bewusst stummgestellt)."""
    n = 0
    kaputt = 0
    frisch_ab = time.time() - ARCHIV_TAGE * 86400
    for d in _cluster_lesen(data_dir):
        # Toleranz je Cluster wie tages_cluster (kc_unbekannt R-4: die
        # werfende Stelle war in BEIDEN Funktionen).
        try:
            uid = d.get("uid") or d.get("id")
            if not uid or d.get("objekt") or d.get("status") != "archiviert":
                continue
            ts = [t for t in (member_ts(m) for m in (d.get("members") or []))
                  if t is not None and von <= t < bis]
            if ts and max(ts) >= frisch_ab:
                n += 1
        except (TypeError, ValueError, AttributeError):
            kaputt += 1
    if kaputt and log:
        log(f"!! unbekannte.jsonl: {kaputt} unreadable cluster line(s) "
            f"skipped on the archive derivation — check the pool file")
    return n
