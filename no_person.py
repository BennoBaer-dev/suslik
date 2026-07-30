# no_person.py — automatische Klasse "no person found (likely false trigger)"
# Konzept: konzept_no_person.md (ABGENOMMEN 27.07.; A1 geaendert 28.07.: Retro-Backtest
# statt 7-Tage-Shadow, bei GRUEN direkt scharf). Masterbauplan S2.
#
# Kernproblem: "kein brauchbares Gesicht" hat zwei Ursachen, die NIE dieselbe Klasse
# bekommen duerfen — (1) kein Mensch da (Frigate-Fehltrigger: Busch, Anhaenger, Radkasten)
# -> no_person; (2) Mensch da, Gesicht unbrauchbar (von hinten, Nacht, zu klein — Klasse
# dokumentierter GT-Fall 17:11) -> bleibt unbekannt/fremd_verdacht. Deshalb entscheiden DREI Signale
# GEMEINSAM, immer ueber den GANZEN Durchgang (Szenario-Prinzip, nie je Einzel-Event):
#   S1  faces_geprueft == 0 ueber ALLE Events des Durchgangs (#42-Filterpfad)
#   S2  kein Roh-face ueber der kalibrierten det-Schwelle (SCRFD-Rauschen ~0, echte-aber-
#       schlechte Gesichter deutlich darueber)
#   S3  Frigate selbst unsicher: bestes person-Objekt-Score des Durchgangs unter Schwelle
#       (Tester-Fall Issue #4: Objekt-Score 0.06-0.09)
# S1 ohne S2/S3 -> KEIN no_person (Fall 2). Fehlt ein Signal (None), zaehlt es als
# NICHT erfuellt — Sicherheits-Semantik: im Zweifel bleibt der Durchgang sichtbar.
#
# Schwellen kommen IMMER aus der Config (np_det_max, np_frigate_max) und sind vom
# Retro-Backtest kalibriert — hier gibt es KEINE eingebauten Zahlen-Defaults
# (Faktenregel: nicht raten). Solange eine Schwelle fehlt/None ist, klassifiziert
# dieses Modul NICHTS als no_person (aktiviert wird per Config beim Scharfschalten).

def klassifiziere(events, np_det_max=None, np_frigate_max=None):
    """Beurteilt EINEN Durchgang (Liste von Event-Dicts) -> (ist_no_person, begruendung).

    Erwartete Felder je Event (Aufrufer uebersetzt aus results/deckung-Zeilen):
      faces_geprueft  int|None   — gefilterte Gesichtszahl (#42); None = Altbestand
      detektionen     list|None  — Roh-Detektionen [{"det": float, ...}, ...] (seit .52)
      frigate_score   float|None — Frigate-Objekt-Score des Events

    Rueckgabe: (bool, dict) — dict traegt je Signal erfuellt/Wert fuer Log/UI/Backtest.
    Sicherheits-Semantik: jedes fehlende Signal (None/leer) -> False.
    """
    beg = {"s1_faces": None, "s2_det_max": None, "s3_frigate_max": None,
           "np_det_max": np_det_max, "np_frigate_max": np_frigate_max}
    if not events or np_det_max is None or np_frigate_max is None:
        return False, beg

    # S1: faces_geprueft muss fuer JEDES Event vorhanden UND 0 sein. Ein Altbestands-
    # Event ohne das Feld macht den Durchgang un-klassifizierbar (nicht "wohl 0").
    fg = [e.get("faces_geprueft") for e in events]
    if any(v is None for v in fg):
        return False, beg
    beg["s1_faces"] = sum(fg)
    if beg["s1_faces"] != 0:
        return False, beg

    # S2: hoechster Roh-det-Score ueber alle Detektionen aller Events. Events ohne
    # persistierte detektionen-Liste (Altbestand vor .52) -> un-klassifizierbar.
    dets = []
    for e in events:
        dl = e.get("detektionen")
        if dl is None:
            return False, beg
        dets += [d.get("det") for d in dl if d.get("det") is not None]
    beg["s2_det_max"] = max(dets) if dets else 0.0
    if beg["s2_det_max"] >= np_det_max:
        return False, beg

    # S3: bestes Frigate-Objekt-Score des Durchgangs. Fehlt es bei allen Events,
    # ist Frigates eigene Sicherheit unbekannt -> un-klassifizierbar (kein Urteil
    # auf halber Datenlage).
    fs = [e.get("frigate_score") for e in events if e.get("frigate_score") is not None]
    if not fs:
        return False, beg
    beg["s3_frigate_max"] = max(fs)
    if beg["s3_frigate_max"] >= np_frigate_max:
        return False, beg

    return True, beg
