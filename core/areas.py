"""core/areas — Bereichs-Modell, Stufe 1 v2 (Design-Entscheide + Widerleger .91).

PARTITIONS-MODELL (ersetzt das n:m des Konzepts, Journal .92): eine Kamera gehoert zu
HOECHSTENS EINER Area (Partition). Alle nicht zugewiesenen Kameras sind automatisch
in "Default" (berechnet als Komplement, nie gespeichert — eine geloeschte Area gibt
ihre Kameras damit von selbst an Default zurueck). Meldungen sind dadurch eindeutig
(genau ein Area-Name je Kamera), und Stufe 2 hat keine Doppel-Feuer-Frage.

SICHT-SEMANTIK (Widerleger-MUSS .91, "Urteils-Splitter"): eine Area-Sicht WAEHLT
Paesse AUS (alles, was die Area beruehrt hat) — sie projiziert NICHT in den
Durchgang hinein. Urteil (erkannt/unbekannt), Personen, Zeiten, Kameras bleiben
immer property-weit (Szenario-Prinzip). Der Lernpfad bleibt komplett area-frei.

Reine Funktionen (Modul-Kontrakt webui/bausteine.py): kein Dienst-Import. Die
Lese-Seite (normalisieren) darf NIE werfen — der Restore-Pfad laesst areas
unvalidiert in den Store; die Schreib-Seite (validieren) lehnt laut ab.
"""
import re

# "All" und "Default" sind feste Sichten (?area=<name>) und als Area-Namen gesperrt;
# "unassigned" bleibt mitgesperrt (Altname der Komplement-Sicht aus .91).
RESERVIERT = ("all", "default", "unassigned")
# Gleiches Zeichen-Muster wie Personennamen (verifyd /upload), Laenge 1-32.
# Fuehrender Unterstrich verboten (Widerleger .91: '__proto__' als Name legt im
# Browser-Sammelobjekt keine eigene Eigenschaft an -> stiller Verlust).
NAME_RE = re.compile(r"^[\w \-]{1,32}$")


def normalisieren(roh):
    """Store-Rohwert -> {name: [kameras]} — fail-safe, wirft nie. Akzeptiert die
    Store-Form {name: {"cameras": [...]}} und tolerant auch {name: [...]};
    alles andere faellt still raus. PARTITION wird beim Lesen erzwungen: steht
    eine Kamera in mehreren Areas (Alt-/Restore-Bestand), gewinnt die erste."""
    if not isinstance(roh, dict):
        return {}
    out, vergeben = {}, set()
    for name, v in roh.items():
        if not isinstance(name, str) or not name.strip():
            continue
        name = name.strip()
        if (name.casefold() in RESERVIERT or name.startswith("_")
                or not NAME_RE.match(name)):
            continue
        cams = v.get("cameras") if isinstance(v, dict) else v
        if not isinstance(cams, (list, tuple)):
            cams = []
        sauber = []
        for c in cams:
            if isinstance(c, str) and c.strip() and c.strip() not in vergeben:
                sauber.append(c.strip())
                vergeben.add(c.strip())
        out[name] = sauber
    return out


def zugewiesen(areas):
    """Alle Kameras, die in irgendeiner Area stehen (areas = normalisierte Map)."""
    return {c for cams in areas.values() for c in cams}


def kamera_area(areas, cam):
    """Area einer Kamera oder None (Partition: hoechstens eine)."""
    for n, cams in areas.items():
        if cam in cams:
            return n
    return None


def kamera_areas(areas, cam):
    """Wie kamera_area, als Liste (0/1 Eintraege) — Form des additiven MQTT-Felds
    areas[] aus .91; die Listen-Form bleibt, damit HA-Automationen stabil sind."""
    a = kamera_area(areas, cam)
    return [a] if a else []


def sicht_aufloesen(areas, wert, beobachtet):
    """?area=<wert> -> (sicht_name, kamera_menge|None). None = keine Auswahl
    (All-Sicht). OHNE angelegte Areas gibt es KEINE Sichten — jede ?area=-URL
    faellt dann auf All zurueck (Widerleger .91: ein Lesezeichen auf eine
    Komplement-Sicht darf nach dem Loeschen der letzten Area keine 'Area view'
    mehr behaupten). 'Default' = Komplement ueber die BEOBACHTETEN Kameras.
    Area-Namen matchen case-insensitiv (validieren dedupliziert casefold,
    die Aufloesung ist also eindeutig); Unbekanntes faellt still auf All."""
    w = (wert or "").strip()
    if not areas or not w:
        return "All", None
    if w.casefold() in ("default", "unassigned"):       # Altname faellt weich auf Default
        return "Default", {str(k) for k in beobachtet} - zugewiesen(areas)
    for n in areas:
        if n.casefold() == w.casefold():
            return n, set(areas[n])
    return "All", None


def melde_zusatz(roh, cam):
    """Kamera -> Area-Name fuer Meldetexte ('' ohne Zuordnung). Partition: genau
    einer. Kameras ohne Area melden bewusst OHNE 'Default'-Zusatz — wer keine
    Areas nutzt, bekommt exakt die Meldungen von vorher."""
    return kamera_area(normalisieren(roh), cam) or ""


def validieren(roh):
    """POST-Body-Pruefung fuer /areas_speichern -> (True, store_form) | (False, msg).
    Store-Form: {name: {"cameras": [...]}}. Lehnt LAUT ab (anders als
    normalisieren): Namensmuster, reservierte Namen, Duplikate (casefold) und
    PARTITION (eine Kamera in zwei Areas ist ein Fehler, kein stiller Gewinner).
    Kameranamen werden bewusst NICHT gegen die Frigate-Live-Liste geprueft:
    eine gerade nicht erreichbare Frigate darf keine Zuordnung verwerfen."""
    if not isinstance(roh, dict):
        return False, "areas must be an object {name: {cameras: [...]}}"
    out, gesehen, vergeben = {}, set(), {}
    for name, v in roh.items():
        if not isinstance(name, str) or not name.strip():
            return False, "area name missing"
        name = name.strip()
        if name.startswith("_") or not NAME_RE.match(name):
            return False, f"area name '{name}': letters, digits, space, - and _ only (max 32, no leading _)"
        if name.casefold() in RESERVIERT:
            return False, f"'{name}' is a reserved view name"
        if name.casefold() in gesehen:
            return False, f"duplicate area name '{name}'"
        gesehen.add(name.casefold())
        cams = v.get("cameras") if isinstance(v, dict) else v
        if not isinstance(cams, (list, tuple)):
            return False, f"area '{name}': cameras must be a list"
        sauber = []
        for c in cams:
            if not isinstance(c, str) or not c.strip():
                return False, f"area '{name}': camera names must be non-empty strings"
            c = c.strip()
            if c in vergeben and vergeben[c] != name:
                return False, f"camera '{c}' is in two areas ('{vergeben[c]}' and '{name}') — one camera, one area"
            if c not in sauber:
                sauber.append(c)
            vergeben[c] = name
        out[name] = {"cameras": sauber}
    return True, out
