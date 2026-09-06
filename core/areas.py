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

# ---------------------------------------------------------------------------
# KETTUNGS-MODUS je Area (.507 B3b, Betreiber-Idee 05.09.2026: "Area buendelt
# fuer die Anzeige, betrachtet bei der Analyse aber jede Kamera einzeln")
# ---------------------------------------------------------------------------
# Die Durchgangs-Kettung war bis .506 rein zeitlich und grundstuecksweit: jedes
# Ereignis haengt an, solange sein Start hoechstens `szenario_gap_min` nach dem
# bisherigen Durchgangs-ENDE liegt — Kamera und Ort spielten keine Rolle. Auf
# einer Anlage im Dauerbetrieb reisst diese Kette praktisch nie (Feldbefund
# 05.09.: EIN Durchgang ueber neun Stunden mit 3423 Ereignissen). Der Modus
# waehlt deshalb, WORUEBER die Luecke gerechnet wird:
#
#   grundstueck  Werk — ALLE Kameras dieser Area teilen die EINE Kette des
#                Grundstuecks (byte-gleich das Verhalten bis .506).
#   area         die Kameras dieser Area ketten nur untereinander (richtig
#                dort, wo jemand durch eine Halle/einen Hof wirklich zieht).
#   kamera       jede Kamera dieser Area bildet ihre eigene Kette.
#
# Das ist EINE Aufzaehlung (qs_ebenen-Regel K3): Renderer, Validierung, Probe
# und die Kettung selbst lesen sie hier, nie ein zweites Streu-Literal.
KETTUNG_MODI = ("grundstueck", "area", "kamera")
KETTUNG_WERK, KETTUNG_AREA, KETTUNG_KAMERA = KETTUNG_MODI
# Die Default-Area ist das KOMPLEMENT und wird nie gespeichert (s. Kopf) — ihr
# Modus braucht deshalb einen eigenen Eintrag in derselben Karte. "default" ist
# als Area-Name gesperrt (RESERVIERT), eine Kollision mit einem echten Namen
# ist damit ausgeschlossen.
KETTUNG_DEFAULT_SCHLUESSEL = "default"


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


def kettung_normalisieren(roh):
    """Store-Rohwert (`areas_kettung`) -> {area_name|'default': modus} —
    fail-safe wie normalisieren, wirft NIE (der Restore-Pfad laesst den Wert
    unvalidiert in den Store). Unbekannte Modi, kaputte Typen und Namen, die
    keine Area sein KOENNEN (Namensmuster), fallen still raus; ein ausdrueckliches
    'grundstueck' faellt ebenfalls raus, weil es das Werk IST — eine Anlage ohne
    Eintrag und eine Anlage mit lauter Werk-Eintraegen verhalten sich damit
    identisch. Der Name behaelt seine Schreibweise (der Store bleibt lesbar), die
    Aufloesung ist case-insensitiv (kettung_modus)."""
    if not isinstance(roh, dict):
        return {}
    out = {}
    for name, modus in roh.items():
        if not isinstance(name, str) or not isinstance(modus, str):
            continue
        name, modus = name.strip(), modus.strip()
        if modus not in KETTUNG_MODI or modus == KETTUNG_WERK:
            continue
        if name.casefold() == KETTUNG_DEFAULT_SCHLUESSEL:
            out[KETTUNG_DEFAULT_SCHLUESSEL] = modus
        elif name and not name.startswith("_") and NAME_RE.match(name):
            out[name] = modus
    return out


def kettung_modus(modi, area_name):
    """Modus EINER Area (modi = normalisierte Karte). area_name None/'' meint
    die Default-Area (das Komplement). Alles Unbekannte faellt auf das Werk —
    eine geloeschte Area, ein Tippfehler oder ein Restore-Rest darf die Kettung
    nie in einen Zustand bringen, den niemand eingestellt hat."""
    if not modi:
        return KETTUNG_WERK
    gesucht = (area_name or KETTUNG_DEFAULT_SCHLUESSEL).strip().casefold()
    for name, modus in modi.items():
        if name.casefold() == gesucht and modus in KETTUNG_MODI:
            return modus
    return KETTUNG_WERK


def ketten_schluessel(areas, modi, cam):
    """DER Ketten-Schluessel einer Kamera fuer die Durchgangs-Bildung
    (szenarien.szenarien_des_tages) — die EINE Stelle, an der aus Area-Modus und
    Kameraname eine Kette wird. Gleicher Schluessel = die beiden Ereignisse
    koennen zu EINEM Durchgang zusammenwachsen (wenn die Luecke stimmt),
    verschiedener Schluessel = nie.

    Ohne eingestellte Modi ist die Antwort fuer JEDE Kamera dieselbe — genau die
    eine grundstuecksweite Kette bis .506, ohne dass die Areas ueberhaupt
    aufgeloest werden muessen."""
    if not modi:
        return KETTUNG_WERK
    area = kamera_area(areas, cam)                  # None = Default-Area
    modus = kettung_modus(modi, area)
    if modus == KETTUNG_KAMERA:
        return KETTUNG_KAMERA + ":" + str(cam)
    if modus == KETTUNG_AREA:
        return KETTUNG_AREA + ":" + (area or KETTUNG_DEFAULT_SCHLUESSEL)
    return KETTUNG_WERK


def kettung_validieren(roh, area_namen=()):
    """POST-Body-Pruefung fuer den Kettungs-Teil von /areas_speichern ->
    (True, store_form) | (False, msg). Lehnt LAUT ab (anders als
    kettung_normalisieren): Nicht-Objekt, Nicht-String, unbekannter Modus.

    ZWEI bewusst STILLE Faelle, beide keine Verluste:
      * ein Eintrag fuer eine Area, die es nach diesem Speichern nicht mehr gibt
        (der Browser schickt die Auswahl der geloeschten Area noch mit) —
        eine Einstellung ohne Gegenstand wird weggelassen, nicht beklagt;
      * ein Werk-Eintrag ('grundstueck') — er wird nicht gespeichert, damit eine
        unberuehrte Anlage weiter GAR KEINEN Store-Eintrag traegt."""
    if not isinstance(roh, dict):
        return False, "chaining must be an object {area: mode}"
    erlaubt = {str(n).strip().casefold() for n in (area_namen or ())}
    erlaubt.add(KETTUNG_DEFAULT_SCHLUESSEL)
    out = {}
    for name, modus in roh.items():
        if not isinstance(name, str) or not isinstance(modus, str):
            return False, "chaining: area name and mode must be strings"
        name, modus = name.strip(), modus.strip()
        if modus not in KETTUNG_MODI:
            return False, (f"chaining for '{name}': unknown mode '{modus}' — "
                           f"allowed: {', '.join(KETTUNG_MODI)}")
        if name.casefold() not in erlaubt or modus == KETTUNG_WERK:
            continue
        out[KETTUNG_DEFAULT_SCHLUESSEL
            if name.casefold() == KETTUNG_DEFAULT_SCHLUESSEL else name] = modus
    return True, out


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
