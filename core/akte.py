"""Akten-Sicht: ein kleines Verzeichnis ueber state/deckung.jsonl, das der Datei folgt.

Bauplan analysen/bauplan_seitentempo.md, Stufe ST1. Anlass: /heute, /system und /anwesenheit lasen die ganze
Akte bei jedem Abruf (beim Feldtester 395 MB, ein Durchgang rund 3 s). Die Sicht liest die Akte beim ersten
Gebrauch einmal ganz, danach je Abruf nur die seither angehaengten ganzen Zeilen. Die Seiten lesen ueber sie nur
noch die Zeilen, die sie brauchen.

WAS SIE HAELT (ohne die Zeilen selbst):
  - je Ereignis die Byte-Stelle seiner ersten Zeile (fuer die Reihenfolge, die by_h in /heute hatte: ein dict
    behaelt den Platz der ersten Zeile), die Byte-Stelle seiner letzten Zeile, deren Tag (nach `start`, sonst
    `ts`, wie /heute) und deren Kamera (`str(camera or "?")` wie in /heute);
  - je Tag die Ereignisse, deren letzte Zeile dort liegt;
  - die Kameras der letzten Zeilen je Ereignis als Zaehler (Bereiche auf /heute);
  - die Kameras aller Zeilen (jeder gesetzte Wert als Text, /anwesenheit);
  - je Person die letzte bestaetigte Sichtung mit Zeit und Byte-Stelle (streng groesser ersetzt, wie /heute);
  - die Byte-Stelle des letzten Eintrags ohne `nachhol` (/system).
Eine Annahme ueber die Reihenfolge der Zeilen gibt es nicht: die Akte ist nicht nach Buchungszeit sortiert.

FOLGEN: nur ganze Zeilen (bis zum letzten Zeilenende); eine unfertige letzte Zeile kommt beim naechsten Abruf.
Ist die Datei kuerzer geworden, hat sie eine andere Kennung (Geraet, Inode) oder stimmt die zuletzt gelesene
Zeile nicht mehr an ihrer Stelle, liest die Sicht einmal neu. Ein Abruf liest alles ueber EINEN geoeffneten
Datei-Griff: wird die Datei waehrend des Lesens ersetzt, liest er den alten Stand zu Ende (wie die alten
Vollleser), der naechste Abruf sieht die neue Kennung. Passt eine Zeile an ihrer Byte-Stelle nicht (Datei an Ort
und Stelle umgeschrieben), liest die Sicht einmal neu und versucht es noch einmal.

FADEN: ein eigenes Schloss je Sicht, nie Service.lock.

EHRLICHE GRENZEN: der erste Abruf nach dem Start liest die Akte einmal ganz. Eine Aenderung mitten in der Datei
bei gleicher Kennung, gleicher oder groesserer Laenge und unveraenderter letzter Zeile sieht die Sicht nicht;
die Schreiber der Akte haengen nur an oder ersetzen die Datei.

AUSGELASSENE ZEILEN (Stufe ST1b, laut statt still): eine kaputte Zeile (auch zu tief verschachteltes JSON,
RecursionError), eine Zeile, die kein JSON-Objekt ist, und eine Ereigniszeile, deren Zeit (`start`, sonst `ts`)
keine Zahl ist, zaehlen in keinem Wert; jede Art meldet sich mit einer gedrosselten WARNING
(`core/logbuch.swallowed`, einmal je Stelle und Prozessleben).
"""
import datetime
import json
import os
import sys
import threading
import zlib
from collections import Counter

from core import logbuch as _logbuch

_log = _logbuch.logger(__name__)

_SICHTEN = {}                      # absoluter Pfad -> AktenSicht
_SICHTEN_SCHLOSS = threading.Lock()


class _Verrutscht(Exception):
    """Eine Zeile passt nicht an ihre Byte-Stelle (die Datei wurde an Ort und Stelle veraendert)."""


def sicht(pfad):
    """Die eine Sicht je Akten-Datei, beim ersten Gebrauch angelegt.
    -> AktenSicht"""
    schluessel = os.path.abspath(pfad)
    with _SICHTEN_SCHLOSS:
        s = _SICHTEN.get(schluessel)
        if s is None:
            s = _SICHTEN[schluessel] = AktenSicht(schluessel)
        return s


def _tag(t):
    """Kalendertag (Ortszeit) eines Zeitwerts als Ordinalzahl; None, wenn der Wert keine Zeit ist."""
    try:
        return datetime.date.fromtimestamp(t).toordinal()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


class AktenSicht:
    """Verzeichnis ueber eine Akten-Datei (Kopf des Moduls)."""

    def __init__(self, pfad):
        self._pfad = pfad
        self._schloss = threading.Lock()
        self._leeren(None)

    def _leeren(self, kennung):
        """Alles vergessen; die Sicht beginnt fuer die Datei mit `kennung` bei Byte 0."""
        self._kennung = kennung
        self._pos = 0
        self._schluss = None              # (Byte-Stelle, Laenge, crc32) der zuletzt gelesenen ganzen Zeile
        self._ev = {}                     # eid -> (erste Stelle, letzte Stelle, Tag, Kamera)
        self._tage = {}                   # Tag -> Menge der eids, deren letzte Zeile dort liegt
        self._kam_letzte = Counter()      # Kamera der letzten Zeile je Ereignis -> Anzahl Ereignisse
        self._kam_alle = set()            # jeder gesetzte Kamerawert aller Zeilen als Text
        self._personen = {}               # Person -> (Zeit, Byte-Stelle der Zeile)
        self._letzter = None              # Byte-Stelle des letzten Eintrags ohne nachhol

    # ------------------------------------------------------------------ oeffentliche Abrufe
    def heute(self, heute0, tag_ende):
        """Die letzten Zeilen der Ereignisse im Zeitfenster [heute0, tag_ende) in der Reihenfolge der Akte,
        die Personen-Historie und die Kameras der letzten Zeilen. -> (by_h, {Person: (Zeit, Zeile)}, Menge)"""
        def arbeit(f):
            return self._tag_lesen(f, heute0, tag_ende), self._personen_lesen(f), set(self._kam_letzte)
        return self._abruf(arbeit, ({}, {}, set()))

    def letzter_eintrag(self):
        """Der letzte Eintrag der Akte ohne `nachhol` (Dateireihenfolge).
        -> dict oder None"""
        def arbeit(f):
            if self._letzter is None:
                return None
            return self._zeile_an(f, self._letzter)
        return self._abruf(arbeit, None)

    def kameras(self):
        """Jeder gesetzte Kamerawert aller Zeilen der Akte als Text.
        -> Menge"""
        return self._abruf(lambda _f: set(self._kam_alle), set())

    # ------------------------------------------------------------------ Lesen
    def _abruf(self, arbeit, leer):
        """Datei oeffnen, der Datei folgen, `arbeit(f)` ueber denselben Griff; bei verrutschter Zeile einmal neu."""
        with self._schloss:
            try:
                f = open(self._pfad, "rb")
            except FileNotFoundError:
                self._leeren(None)
                return leer
            with f:
                self._folgen(f, neu=False)
                try:
                    return arbeit(f)
                except _Verrutscht as e:
                    _log.warning(f"deckung.jsonl view: {e}; reading the file again")
                self._folgen(f, neu=True)
                return arbeit(f)

    def _folgen(self, f, neu):
        """Die seit dem letzten Abruf angehaengten ganzen Zeilen aufnehmen; neu lesen, wenn die Datei anders ist."""
        st = os.fstat(f.fileno())
        kennung = (st.st_dev, st.st_ino)
        grund = ("forced" if neu else "first read" if self._kennung is None
                 else "other file" if kennung != self._kennung
                 else "file shorter" if st.st_size < self._pos
                 else "" if self._schluss_stimmt(f) else "last line changed")
        if grund:
            if self._kennung is not None:
                _log.info(f"deckung.jsonl view: reading the whole file again ({grund})")
            self._leeren(kennung)
        f.seek(self._pos)
        pos, letzte = self._pos, None
        for zeile in f:
            if not zeile.endswith(b"\n"):
                break                     # unfertige letzte Zeile: kommt beim naechsten Abruf
            self._aufnehmen(zeile, pos)
            letzte = (pos, zeile)
            pos += len(zeile)
        if letzte is not None:
            self._schluss = (letzte[0], len(letzte[1]), zlib.crc32(letzte[1]))
        self._pos = pos

    def _schluss_stimmt(self, f):
        """Steht die zuletzt gelesene ganze Zeile unveraendert an ihrer Stelle? -> bool"""
        if self._schluss is None:
            return self._pos == 0
        stelle, laenge, crc = self._schluss
        f.seek(stelle)
        zeile = f.readline()
        return len(zeile) == laenge and stelle + laenge == self._pos and zlib.crc32(zeile) == crc

    def _aufnehmen(self, zeile, stelle):
        """Eine ganze Zeile in das Verzeichnis eintragen (Regeln der alten Vollleser)."""
        try:
            d = json.loads(zeile)
        except (ValueError, RecursionError):           # ST1b: zu tief verschachtelt gilt als kaputte Zeile
            _logbuch.swallowed(_log, _logbuch.WARNING, "ignored")
            return
        if not isinstance(d, dict):
            _logbuch.swallowed(_log, _logbuch.WARNING, "line is no JSON object, skipped")
            return
        t = d.get("start") or d.get("ts", 0)
        eid = d.get("eid")
        tag = _tag(t) if eid else None
        if eid and tag is None:
            _logbuch.swallowed(_log, _logbuch.WARNING, "event line skipped, its time (start, else ts) is no number")
            return
        c = d.get("camera")
        if c:
            self._kam_alle.add(str(c))
        if not d.get("nachhol"):
            self._letzter = stelle
        try:
            for p in d.get("bestaetigt") or []:
                if t > self._personen.get(p, (0, None))[0]:
                    self._personen[p] = (t, stelle)
        except TypeError:
            _logbuch.swallowed(_log, _logbuch.WARNING, "person history skipped for this line")
        if eid:
            try:
                self._ereignis(eid, stelle, tag, sys.intern(str(d.get("camera", "?"))))
            except TypeError:
                _logbuch.swallowed(_log, _logbuch.WARNING, "line with unusable eid skipped")

    def _ereignis(self, eid, stelle, tag, kam):
        """Die letzte Zeile eines Ereignisses umsetzen (Tag und Kamera der alten letzten Zeile austragen)."""
        alt = self._ev.get(eid)
        if alt is None:
            erst = stelle
        else:
            erst = alt[0]
            menge = self._tage[alt[2]]
            menge.discard(eid)
            if not menge:
                del self._tage[alt[2]]
            self._kam_letzte[alt[3]] -= 1
            if not self._kam_letzte[alt[3]]:
                del self._kam_letzte[alt[3]]
        self._ev[eid] = (erst, stelle, tag, kam)
        self._tage.setdefault(tag, set()).add(eid)
        self._kam_letzte[kam] += 1

    def _zeile_an(self, f, stelle):
        """Die ganze Zeile an einer Byte-Stelle als dict. -> dict (_Verrutscht, wenn dort keine passt)"""
        if stelle >= self._pos:
            raise _Verrutscht(f"byte {stelle} lies behind the read position")
        f.seek(stelle)
        zeile = f.readline()
        if not zeile.endswith(b"\n"):
            raise _Verrutscht(f"no whole line at byte {stelle}")
        try:
            d = json.loads(zeile)
        except (ValueError, RecursionError):
            raise _Verrutscht(f"no JSON line at byte {stelle}") from None
        if not isinstance(d, dict):
            raise _Verrutscht(f"no JSON object at byte {stelle}")
        return d

    def _tag_lesen(self, f, heute0, tag_ende):
        """by_h fuer das Zeitfenster: nur die letzten Zeilen der Ereignisse der betroffenen Tage, in der Reihenfolge
        der ersten Zeile je Ereignis; gefiltert nach `start`, sonst `ts`, wie /heute. -> dict"""
        von, bis = _tag(heute0), _tag(tag_ende)
        if von is None:
            return {}
        tage = range(von, max(bis if bis is not None else von, von + 1))
        eintraege = sorted((self._ev[e] + (e,) for t in tage for e in self._tage.get(t, ())),
                           key=lambda x: x[1])
        zeilen = []
        for erst, stelle, _t, _k, eid in eintraege:     # in Datei-Reihenfolge lesen
            d = self._zeile_an(f, stelle)
            if d.get("eid") != eid:
                raise _Verrutscht(f"line at byte {stelle} belongs to another event")
            zeit = d.get("start") or d.get("ts", 0)
            try:
                im_fenster = heute0 <= zeit < tag_ende
            except TypeError:
                _logbuch.swallowed(_log, _logbuch.WARNING, "event line skipped, its time is no number")
                im_fenster = False
            if im_fenster:
                zeilen.append((erst, eid, d))
        zeilen.sort(key=lambda x: x[0])
        return {eid: d for _erst, eid, d in zeilen}

    def _personen_lesen(self, f):
        """Die Personen-Historie mit den Zeilen ihrer letzten Sichtung. -> {Person: (Zeit, Zeile)}"""
        return {p: (t, self._zeile_an(f, stelle)) for p, (t, stelle) in self._personen.items()}
