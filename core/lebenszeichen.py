"""Fortschrittsmarken der Arbeitsschleifen des Dienstes (Bauplan analysen/bauplan_lebenszeichen.md, Stufe LZ2).

HERKUNFT: der Eigentuemer am 06.11.2026 13:36:52: „Also im Kern müssen wir doch eigentlich eine prüfen, ob das noch
lebt, statt anhand der Zeit." und 13:46:26: „… dass wir nicht resetten, wenn es noch lebt". Bis LZ2 wusste die
Selbstwache nur, ob der Webserver antwortet; ob die Arbeit weiterlief, sah sie nicht.

ZWECK: jede Arbeitsschleife (Abholen, Plaetze, Melde-Spur, Vorlauf, Nachholen) ruft je Runde `setzen(name)`. Die
Selbstwache liest `lage(grenzen)` und nennt eine stehende Schleife mit Namen und Stelle; `zuletzt()` gibt ihr die
juengste Marke einer Arbeitsschleife, an der sie prueft, ob die Arbeit im Fenster von Entscheid 2 lebt. /health zeigt
dieselbe Lage als Block `lebenszeichen`. Die Grenzen baut `grenzen()` aus Config und core.registry.LEBENSZEICHEN.

KEINE ZUSAETZLICHE LAST (Eigentuemer 07.11.): eine Marke ist eine Zuweisung im Speicher. Kein eigener Faden, kein
Dateizugriff, keine Sperre. Die Stapelstelle eines Fadens kommt aus dem Speicher des Interpreters
(`sys._current_frames`, gelesen ueber core.support._stack_of), nur wenn eine Schleife steht.

EHRLICHE GRENZEN:
  - Eine Schleife, die sich dreht und dabei nichts schafft, lebt im Sinn der Marke (dafuer bleiben Fehlerserie und
    Stillstand zustaendig).
  - Eine Marke, die nie gesetzt wurde (Schleife aus oder noch im Anlauf), steht nicht: `alter_s` ist dann None.
  - `hoechst_s` ist das hoechste beim Lesen BEOBACHTETE Alter, nicht das hoechste wirkliche: zwischen zwei Lesungen
    kann eine Marke aelter gewesen sein. Ohne Sperre kann ein gleichzeitiger Leser eine Beobachtung ueberschreiben.
  - Setzen mehrere Faeden dieselbe Marke (ein Abholer je Platz), merkt sie sich den letzten.
"""
import sys
import threading
import time

from core import registry as _reg

# Name -> (monotone Zeit, Fadenkennung) der letzten Marke; eine Zuweisung je `setzen`.
_marken = {}
# Name -> hoechstes beobachtetes Alter in Sekunden seit dem Start des Prozesses.
_hoechst = {}
# Marken, die keine Arbeit sind: der Sammler von /health (Stufe LZ5) markiert nur, solange /health gelesen wird. Fuer
# den Abgangsmassstab (`zuletzt`, Entscheid 2) zaehlen sie nicht; `lage()` zeigt sie weiter (Bauplan LZ2b Fix-Stelle 5).
KEINE_ARBEIT = ("health-sammler",)


def setzen(name):
    """Legt fuer die Schleife `name` jetzt eine Marke ab (monotone Zeit und Fadenkennung, eine Zuweisung).
    -> None"""
    _marken[name] = (time.monotonic(), threading.get_ident())


def lage(grenzen):
    """Die Lage je Marke aus `grenzen` ({name: grenze_s}); merkt dabei das hoechste beobachtete Alter.
    -> {name: {"alter_s", "grenze_s", "steht", "hoechst_s"}}; alter_s None, solange die Marke nie gesetzt wurde"""
    jetzt = time.monotonic()
    aus = {}
    for name, grenze_s in grenzen.items():
        marke = _marken.get(name)
        alter_s = None if marke is None else jetzt - marke[0]
        if alter_s is not None and alter_s > _hoechst.get(name, 0.0):
            _hoechst[name] = alter_s
        hoechst_s = _hoechst.get(name)
        aus[name] = {"alter_s": None if alter_s is None else round(alter_s, 1), "grenze_s": grenze_s,
                     "steht": bool(alter_s is not None and grenze_s is not None and alter_s > grenze_s),
                     "hoechst_s": None if hoechst_s is None else round(hoechst_s, 1)}
    return aus


def zuletzt():
    """Die juengste Marke ueber alle Arbeitsschleifen, ohne die Marken in KEINE_ARBEIT (Bauplan LZ2b Fix-Stelle 5).
    -> {"name", "zeit" (monoton), "alter_s"} oder None, solange keine gesetzt wurde"""
    stand = [(name, marke) for name, marke in list(_marken.items()) if name not in KEINE_ARBEIT]
    if not stand:
        return None
    name, (zeit, _faden) = max(stand, key=lambda p: p[1][0])
    return {"name": name, "zeit": zeit, "alter_s": round(time.monotonic() - zeit, 1)}


def stelle(name, tiefe=3):
    """Die innersten `tiefe` Stellen des Fadens, der die Marke `name` zuletzt gesetzt hat, ohne Dateizugriff.
    -> Text „datei:zeile funktion < …“; leer, wenn die Marke fehlt oder der Faden nicht mehr laeuft"""
    marke = _marken.get(name)
    return faden_stelle(marke[1], tiefe) if marke else ""


def faden_stelle(ident, tiefe=3):
    """Die innersten `tiefe` Stellen des Fadens mit der Kennung `ident`, wie in der Fadenliste gelesen.
    -> Text „datei:zeile funktion < …“; leer, wenn der Faden nicht laeuft"""
    from core import support as _sup                     # spaet: nur wenn eine Schleife steht
    rahmen = sys._current_frames().get(ident)
    return " < ".join(f"{s['file']}:{s['line']} {s['function']}" for s in _sup._stack_of(rahmen)[:tiefe])


def grenzen(cfg, platz_stumm_s, vorlauf_takt_s):
    """Die Grenze je Marke aus Config und core.registry.LEBENSZEICHEN (Tabelle in Stufe LZ2 Punkt 3 des Bauplans).
    -> {name: grenze_s}; `platz_stumm_s` und `vorlauf_takt_s` reicht der Dienst aus seinen eigenen Konstanten"""
    w = _reg.LEBENSZEICHEN
    faktor = w["faktor"]
    abruf_s = w["abruf_grund_s"] + int(cfg["sweep_limit"]) // w["abruf_zuwachs_je"]
    if cfg.get("trigger") == "mqtt":
        abholen = faktor * (_reg.MQTT_STUMMWACHE["abgleich_s"] + abruf_s)
    else:
        abholen = faktor * (float(cfg["poll_interval"]) + abruf_s)
    # Im Altmodus ohne Worker pulst kein Platz; dort deckt die Analysefrist eine Runde des Abholers.
    plaetze = platz_stumm_s if cfg.get("worker", True) else float(cfg["analyse_timeout_s"])
    return {"abholen": abholen, "plaetze": plaetze,
            "melde-spur": faktor * (w["spur_warte_s"] + w["sende_max_s"]),
            "vorlauf": faktor * (vorlauf_takt_s + w["abruf_grund_s"]),
            "nachholen": faktor * (float(cfg["nachhol_intervall_s"]) + float(cfg["nachhol_analyse_timeout_s"]))}
