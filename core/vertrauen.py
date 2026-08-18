"""core/vertrauen — DIE eine Uebersetzung von Mess-Scores in Wortstufen
(Kosinus-raus-Umbau, User-Go 17.08., Konzept konzept_kosinus_usersicht.md §4).

Ehrlichkeits-Rahmen: der Kosinus ist KEINE Wahrscheinlichkeit, und die drei
Messwege (Gesicht=Kosinus, Koerper=predict_proba, Frigate=eigener Score)
haben verschiedene Skalen. Was das System ehrlich sagen kann, ist die LAGE
RELATIV ZUR EIGENEN MESSLATTE (selbstgeeicht: win_thresh/UNBEKANNT_MAX bzw.
die gegen Fremde kalibrierte Koerper-Schwelle). Genau das druecken die vier
Stufen aus — nie mehr.

Kontrakt wie core/registry.py: import-frei, reine Funktionen, KEINE
UI-/Dienst-Importe. Die vier Labels existieren GENAU HIER (QS-Ebenen-Regel:
kein Streu-Literal); HTML-Pills baut webui/bausteine.py aus dieser Quelle.
MQTT-Payloads bekommen die Stufe nur ADDITIV dazu (User-Auflage 17.08.:
bestehende Schluessel byte-gleich, nichts darf HA-Skripte brechen)."""

STUFEN = ("clear", "narrow", "below", "none")

# UI-Labels (bar-Sprache, User-Entscheid 17.08.: knuepft an den Hilfe-Text
# "the similarity clears a bar it has set for itself" an und verspricht
# nichts, was nicht gemessen ist).
LABELS = {"clear": "clear match",
          "narrow": "just above the bar",
          "below": "below the bar",
          "none": "no match"}

# Komfort-Band ueber/unter der Latte: >= schwelle+band -> clear, unterhalb
# schwelle aber >= schwelle-band -> below (Naehe), weiter drunter -> none.
# HEURISTIK, keine Messung (ehrlich benannt): wo eine Eichung existiert
# (Koerper: Abstand fremd_echt_max->Schwelle), reicht der Aufrufer sein
# eigenes band herein; dieser Default ist der EINE zentrale Fallback und
# ueber cfg 'vertrauen_band' uebersteuerbar (Aufrufer liest Config, nie hier).
BAND_DEFAULT = 0.10


def stufe(wert, schwelle, band=None):
    """Lage relativ zur Messlatte -> 'clear'|'narrow'|'below'|'none'.
    wert None/nicht-endlich oder schwelle None -> 'none' (nie raten)."""
    try:
        w, s = float(wert), float(schwelle)
    except (TypeError, ValueError):
        return "none"
    if w != w or s != s:                       # NaN-Wache
        return "none"
    b = BAND_DEFAULT if band is None else max(0.0, float(band))
    if w >= s + b:
        return "clear"
    if w >= s:
        return "narrow"
    if w >= s - b:
        return "below"
    return "none"


def label(st):
    """Stufe -> UI-Label; unbekannte Stufe faellt LAUT auf 'no match'
    zurueck (nie ein erfundenes Label)."""
    return LABELS.get(st, LABELS["none"])


def wort(wert, schwelle, band=None):
    """Bequemer Einzeiler fuer Meldetexte: stufe()+label() in einem."""
    return label(stufe(wert, schwelle, band))
