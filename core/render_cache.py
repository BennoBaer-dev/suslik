"""Seitenspeicher fuer /heute und /anwesenheit: der fertige Seiteninhalt je Schluessel, gueltig, solange seine Quellen
unveraendert sind.

HERKUNFT: Bauplan `analysen/bauplan_render_cache.md`, Stufe RC1 (Fassungen 2 bis 4, Entscheide E1 bis E12). Anlass war
das Debug-Log des Feldtesters vom 04.11.2026: /heute im Median 2.480 ms, im Mittel 13,2 s je Aufruf, und jeder Aufruf
las alle Quellen neu. Der Eigentuemer am 04.11.2026 21:41:02: „eine smartte clevere lösung die nict ausufert“. Schalter
im Werkszustand an (E1, Eigentuemer 05.11.2026 07:22:02), Config-Schluessel `render_cache` ohne Oberflaeche (E2).

ZWECK: die Seitenzweige in `verifyd.make_handler.H.do_GET` fragen vor dem Bau `lookup`. Ein Treffer liefert Titel,
Inhalt und „ist heute“ (E3); Kopf, Banner und Takt baut der Zweig je Aufruf neu. Ein Fehltreffer baut wie bisher und
legt danach mit `store` ab, ausser waehrend ein Durchgang laeuft (E6). Der Speicher lebt je Prozess, haelt hoechstens
RENDER_CACHE_DECKEL Eintraege (E8, der am laengsten nicht benutzte faellt) und schreibt keine Datei.

SCHLUESSEL UND SIGNALE (E4, E12): der Schluessel ist Seitenkennung, gezeigter Tag, Datum heute, Sprache, Bereiche und
Kettung aus der Config, fuer /anwesenheit am heutigen Tag die Jetzt-Zelle (15-Minuten-Raster), dazu die Teile des
Aufrufers (Rohwerte der Abfrage, Update-Hinweis, roter Hinweis „ähnlich“). Die Signale sind je Quelle Geraet, Kennung,
Groesse und Aenderungszeit aus `os.stat`, nie durch Oeffnen; eine fehlende Datei ist ein eigener Wert. Sie werden vor
dem Bau gelesen und mit dem Eintrag abgelegt: aendert sich eine Quelle waehrend des Baus, ist der naechste Aufruf ein
Neubau. Die Pfade kommen aus den Modulen der Quellen; Akte und Ground-Truth-Datei reicht der Dienst herein. Die
Vision-Urteile haengen in Unterordner an und haben kein Dateisignal; dafuer zaehlt `poke` die Generation hoch (nur im
Dienstprozess, aus `core/visionurteil.protokoll_schreiben`). Ein Eintrag gilt hoechstens RENDER_CACHE_ALTER_S (E7).

SCHLOSS: `_LOCK` schuetzt nur Nachsehen und Setzen der Eintraege, die Zaehler und die Generation. Darin laeuft kein
`stat`, kein Bau, kein Log und kein Aufruf in den Dienst, und es wird nie zusammen mit `Service.lock`, `_cfg_lock`, dem
Schloss der Akten-Sicht oder den Schloessern der Referenz-Quelle gehalten; es nimmt kein anderes Schloss.

FEHLER (laut, nie still): jede Ausnahme in `lookup` und `store` ergibt eine gedrosselte WARNING ueber
`core/logbuch.swallowed`, zaehlt in `errors`, setzt `last_error` (Ort und Ausnahmetyp, ohne Text) und `red` bis zum
naechsten gelungenen Aufruf; /health `ok` ist dann falsch. Die Seite baut in diesem Fall direkt.

EHRLICHE GRENZEN: ohne Signal bleiben ein geloeschter Ereignisordner einer alten Sichtung, die Sieben-Tage-Grenze
archivierter Identitaeten und das Fenster der 80 juengsten Vision-Ordner; die Lebensdauer deckelt sie. Zwei
Schreibvorgaenge gleicher Groesse in derselben Zeitmarke sind nicht zu unterscheiden. Zwei Fehltreffer desselben
Schluessels bauen beide, der zuletzt fertige legt ab. Der Anstoss `poke` wirkt nur im eigenen Prozess.
"""

import collections
import json
import os
import sys
import threading
import time

from core import logbuch as _logbuch
from core import registry as _reg

_log = _logbuch.logger(__name__)

PAGE_TODAY = "/heute"
# Bauplan analysen/bauplan_today_seite.md, Stufe TY2 Punkt 4: der Reiter Durchgaenge hat eine eigene Seitenkennung (der
# Schluessel traegt sie vorn) und dieselben Quellen wie /heute.
PAGE_PASSES = "/durchgaenge"
PAGE_PRESENCE = "/anwesenheit"
REASON_NEW = "new"
REASON_EXPIRED = "expired"
REASON_POKED = "poked"
REASON_RUNNING = "running"

clock = time.time                   # die Uhr des Moduls (Lebensdauer, Jetzt-Zelle); Proben stellen sie

_LOCK = threading.Lock()
_entries = collections.OrderedDict()      # Schluessel -> _Entry, der zuletzt benutzte am Ende
_running = collections.OrderedDict()      # Schluessel, deren letzter Bau einen laufenden Durchgang zeigte
_stats = {"gen": 0, "hits": 0, "misses": {}, "evicted": 0, "errors": 0, "last_error": None, "red": False}

_Entry = collections.namedtuple("_Entry", "title content today_page signals gen built")


class Handle:
    """Ergebnis von `lookup`: Schluessel, Signale, Generation und Zeit von vor dem Bau; `hit` ist bei einem Treffer der
    gespeicherte Eintrag (title, content, today_page), sonst None, und `reason` nennt den Grund des Fehltreffers."""

    __slots__ = ("key", "signals", "gen", "built", "hit", "reason")

    def __init__(self, key, signals, gen, built, hit, reason):
        self.key, self.signals, self.gen, self.built, self.hit, self.reason = key, signals, gen, built, hit, reason


def enabled(cfg):
    """Ob der Seitenspeicher an ist: Config-Schluessel `render_cache`, sonst der Werkswert der Registry.
    -> bool"""
    return bool((cfg or {}).get("render_cache", _reg.RENDER_CACHE_AN))


def _stamp(path):
    """Signal einer Datei oder eines Ordners: (Geraet, Kennung, Groesse, Aenderungszeit), None, wenn sie fehlt.
    -> Tupel oder None; jeder andere OSError geht an den Aufrufer."""
    try:
        st = os.stat(path)
    except FileNotFoundError:
        return None
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)


def _sources(cfg, log_path, day, gt_path):
    """Die Dateien, aus denen /heute baut (E4, die eine Liste), mit den Pfaden aus den Modulen der Quellen.
    -> Tupel (Name, Pfad)"""
    import anlernen
    from core import anwesenheit, livewache, personlive, personmodell, unbekanntpool
    from core.refquelle import basis
    data = cfg["data_dir"]
    live = os.path.join(data, "live", livewache.MELDE_PROTOKOLL)
    return (("akte", log_path), ("katalog", basis.paths(cfg)["catalog"]),
            ("unbekannte", unbekanntpool.pool_path(data)), ("gesichter", anlernen.GES_PATH),
            ("ground_truth", gt_path), ("meldungen", live), ("meldungen.1", live + ".1"),
            ("anwesenheit", anwesenheit.tag_pfad(cfg, day)),
            ("fenster", os.path.join(anwesenheit.ordner(cfg), anwesenheit.FENSTER_DATEI)),
            ("live_treffer", personlive._treffer_log(data)),
            ("modell_status", os.path.join(personmodell.modell_dir(data), "status.json")))


def _sources_presence(cfg, log_path, day):
    """Die Dateien, aus denen /anwesenheit baut (Fassung 2, E12); der Ordner traegt die Liste der Tagesdateien.
    -> Tupel (Name, Pfad)"""
    from core import anwesenheit
    from core.refquelle import basis
    return (("akte", log_path), ("katalog", basis.paths(cfg)["catalog"]),
            ("anwesenheit", anwesenheit.tag_pfad(cfg, day)),
            ("fenster", os.path.join(anwesenheit.ordner(cfg), anwesenheit.FENSTER_DATEI)),
            ("anwesenheit_ordner", anwesenheit.ordner(cfg)))


def _key(page, cfg, day, today, parts):
    """Der Schluessel eines Aufrufs; die Seitenkennung steht vorn (H3).
    -> Text (JSON)"""
    from core import anwesenheit, sprache
    cell = anwesenheit.zelle_von_ts(clock()) if page == PAGE_PRESENCE and day == today else None
    return json.dumps([page, day, today, sprache.aktive(), cfg.get("areas"), cfg.get("areas_kettung"), cell,
                       list(parts)], sort_keys=True, default=repr)


def _look(key, signals, now, max_age):
    """Unter `_LOCK`: den Eintrag pruefen und die Zaehler fuehren.
    -> Handle"""
    gen = _stats["gen"]
    entry = _entries.get(key)
    if entry is None:
        reason = REASON_RUNNING if key in _running else REASON_NEW
    elif entry.signals != signals:
        reason = next((new[0] for new, old in zip(signals, entry.signals) if new != old), REASON_NEW)
    elif entry.gen != gen:
        reason = REASON_POKED
    elif now - entry.built > max_age:
        reason = REASON_EXPIRED
    else:
        reason = None
    if reason is None:
        _entries.move_to_end(key)
        _stats["hits"] += 1
    else:
        _stats["misses"][reason] = _stats["misses"].get(reason, 0) + 1
    _stats["red"] = False
    return Handle(key, signals, gen, now, entry if reason is None else None, reason)


def lookup(page, cfg, log_path, day, today, parts, gt_path=None):
    """Schluessel und Signale bilden (ohne Schloss) und im Speicher nachsehen; ein Fehler ist laut.
    -> Handle (Treffer in `hit`) oder None nach einem Fehler: dann baut die Seite direkt und legt nichts ab."""
    try:
        if page in (PAGE_TODAY, PAGE_PASSES):
            names = _sources(cfg, log_path, day, gt_path)
        elif page == PAGE_PRESENCE:
            names = _sources_presence(cfg, log_path, day)
        else:
            raise ValueError("unknown page")
        key = _key(page, cfg, day, today, parts)
        signals = tuple((name, _stamp(path)) for name, path in names)
        max_age = float(_reg.RENDER_CACHE_ALTER_S)
        now = clock()
        with _LOCK:
            return _look(key, signals, now, max_age)
    except Exception:                                   # noqa: BLE001  laut ueber _failed, die Seite kommt trotzdem
        _logbuch.swallowed(_log, _logbuch.WARNING, "page built directly")
        _failed("lookup")
        return None


def _put(key, entry, cap):
    """Unter `_LOCK`: ablegen (entry) oder den laufenden Durchgang vermerken (None); der Deckel gilt fuer beides.
    -> None"""
    _entries.pop(key, None)
    _running.pop(key, None)
    if entry is None:
        _running[key] = True
        while len(_running) > cap:
            _running.popitem(last=False)
    else:
        _entries[key] = entry
        while len(_entries) > cap:
            _entries.popitem(last=False)
            _stats["evicted"] += 1
    _stats["red"] = False


def store(handle, title, content, today_page, running):
    """Den fertigen Inhalt mit den Signalen von vor dem Bau ablegen, ausser waehrend ein Durchgang laeuft (E6).
    -> None; ohne Griff (Fehler in lookup) wirkungslos, ein Fehler ist laut."""
    if handle is None:
        return
    try:
        cap = int(_reg.RENDER_CACHE_DECKEL)
        entry = None if running else _Entry(title, content, bool(today_page), handle.signals, handle.gen,
                                            handle.built)
        with _LOCK:
            _put(handle.key, entry, cap)
    except Exception:                                   # noqa: BLE001  laut ueber _failed, die Seite kommt trotzdem
        _logbuch.swallowed(_log, _logbuch.WARNING, "entry not kept")
        _failed("store")


def _failed(where):
    """Einen Fehler zaehlen, Ort und Ausnahmetyp merken (ohne Text, keine Pfade oder Namen) und rot setzen.
    -> None"""
    typ = sys.exc_info()[0]
    with _LOCK:
        _stats["errors"] += 1
        _stats["last_error"] = f"{where}: {typ.__name__ if typ else 'error'}"
        _stats["red"] = True


def poke(reason):
    """Alle Eintraege ungueltig machen, weil sich eine Quelle ohne Dateisignal geaendert hat (E4: nur die Vision-Urteile).
    -> None; eine DEBUG-Zeile nennt Anlass und neue Generation."""
    with _LOCK:
        _stats["gen"] += 1
        gen = _stats["gen"]
    _log.debug(f"render cache: entries invalidated ({reason}), generation {gen}")


def red():
    """Ob der letzte Aufruf von lookup oder store scheiterte (rot bis zum naechsten gelungenen).
    -> bool"""
    with _LOCK:
        return _stats["red"]


def state(cfg):
    """Der Block `render_cache` fuer /health, nur aus dem Speicher.
    -> dict enabled, entries, cap, max_age_s, hits, misses (je Grund), evicted, errors, last_error, red"""
    with _LOCK:
        snap = {"entries": len(_entries), "hits": _stats["hits"], "misses": dict(sorted(_stats["misses"].items())),
                "evicted": _stats["evicted"], "errors": _stats["errors"], "last_error": _stats["last_error"],
                "red": _stats["red"]}
    return {"enabled": enabled(cfg), "entries": snap["entries"], "cap": _reg.RENDER_CACHE_DECKEL,
            "max_age_s": _reg.RENDER_CACHE_ALTER_S, "hits": snap["hits"], "misses": snap["misses"],
            "evicted": snap["evicted"], "errors": snap["errors"], "last_error": snap["last_error"],
            "red": snap["red"]}
