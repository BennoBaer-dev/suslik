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
# Sprach-Stufe 2 Tranche D (Kennung/Anzeige-Trennung): die UI zeigt die
# Wortstufen ueber webui/bausteine.stufe_wort() (baustein.stufe.*-Schluessel,
# EN wortgleich zu dieser Tabelle — Beweis tranche_d_beweis). DIESE Tabelle
# bleibt die englische Quelle fuer Meldetexte (core/melden, livewache,
# verifyd-push — Stufe 4) und Logs; label()/wort() bleiben unangetastet.
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


# --- Sprach-Stufe 4: dieselbe Stufe, in der gewaehlten Sprache -------------
# konzept_sprache.md §6.4 (User-Entscheid 19.08.): "Wortstufen in Meldungen
# (Pushover/Telegram): uebersetzt in die gewaehlte Sprache."
#
# DIE Kennung->Anzeige-Aufloesung der vier Stufen steht GENAU HIER — vorher
# lag sie in webui/bausteine.stufe_wort (Tranche D, nur UI). Mit dem
# Meldeweg kam ein zweiter Leser dazu (core/livewache, verifyd), und
# core/* darf webui/* nicht importieren; eine zweite Liste derselben vier
# Schluessel waere genau das verstreute Literal, das die K3-Regel verbietet
# (CLAUDE.md/qs_ebenen.md). bausteine.stufe_wort() liest jetzt HIER.
#
# Der Import liegt in der Funktion (nicht am Modulkopf): dieses Modul ist
# per Kontrakt import-frei, und t() darf ohnehin nie auf Modulebene laufen
# (§8.12 — sonst friert die Sprachwahl auf den Import ein).
# LABELS bleibt die englische Quelle: Fallback dieses Wegs und
# EN-Deckungsvertrag der baustein.stufe.*-Schluessel (Beweis Tranche D).
def label_sprachig(st):
    """Stufe -> UI-/Meldewort in der aktiven Sprache; unbekannte Stufe
    faellt wie label() auf das none-Wort (nie ein erfundenes Label)."""
    from core import sprache as _sprache
    m = {"clear": _sprache.t("baustein.stufe.clear"),
         "narrow": _sprache.t("baustein.stufe.narrow"),
         "below": _sprache.t("baustein.stufe.below"),
         "none": _sprache.t("baustein.stufe.none")}
    return m.get(st) or m["none"]


def wort_sprachig(wert, schwelle, band=None):
    """wort() in der aktiven Sprache — der Meldeweg-Einzeiler der Stufe 4."""
    return label_sprachig(stufe(wert, schwelle, band))
