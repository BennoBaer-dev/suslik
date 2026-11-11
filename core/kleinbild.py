"""Kleine Kachelbilder fuer die Seite Today (Bauplan analysen/bauplan_today_seite.md, Stufe TY1 Punkt 1).

HERKUNFT: der Eigentuemer am 10.11.2026 09:13:58 zur Seite Today: „Auch ist die sehr langsam". Beim Feldtester lud der
Browser dort 20 Bilder mit zusammen 3.620 KB; 3.233 KB davon waren zwei Beweisbilder in voller Groesse, gezeigt als
Kachel von 54 px Breite (Befund im Bauplan, gemessen am 10.11.2026).

ZWECK: die Bild-Routen liefern mit dem Abfrageteil `klein=1` ein Bild von hoechstens `KACHELBILD_BREITE` Pixeln Breite
(core/registry.py), Seitenverhaeltnis wie das Original, immer als JPEG. Ohne `klein=1` bleibt jede Route, wie sie war.
Ein Speicher im Prozess haelt die verkleinerten Bilder, hoechstens `KACHELBILD_SPEICHER_BYTES` Bytes, der aelteste
Eintrag faellt zuerst; geschrieben wird keine Datei. Der Schluessel eines Eintrags kommt vom Aufrufer und wechselt,
wenn sich das Bild aendert (`datei_schluessel`: Pfad, Aenderungszeit, Groesse; `inhalt_schluessel` fuer Bilder, die
nicht als Datei vorliegen).

EHRLICHE GRENZEN: laesst sich ein Bild nicht lesen, geht das Original mit seinem Bildtyp raus und eine gedrosselte
WARNING ins Log (einmal je Stelle und Prozess, core/logbuch.swallowed). Ein Bild, das schon hoechstens so breit ist,
geht unveraendert raus; der Speicher merkt sich das ohne Bytes. Ein Bild, das nicht gelesen werden konnte, merkt er sich
nicht. Ein Alpha-Kanal faellt beim Umwandeln nach JPEG weg.
"""
import collections
import hashlib
import os
import threading

from core import logbuch as _logbuch
from core import registry as _reg

_log = _logbuch.logger(__name__)
_SPEICHER = collections.OrderedDict()   # Schluessel -> JPEG-Bytes, oder None fuer „schon schmal genug"
_GEHALTEN = [0]                         # Summe der gehaltenen Bytes
_SCHLOSS = threading.Lock()


def verlangt(qs):
    """Ob die Anfrage das kleine Bild verlangt (Abfrageteil klein=1, aus urllib.parse.parse_qs).
    -> bool"""
    return (qs.get("klein") or [""])[0] == "1"


def adresse(url):
    """Eine Bild-Adresse fuer ein HTML-Attribut um klein=1 ergaenzen (mit ? oder &amp;, je nach Adresse).
    -> Text"""
    return f"{url}{'&amp;' if '?' in url else '?'}klein=1"


def datei_schluessel(pfad):
    """Schluessel fuer ein Bild aus einer Datei: Pfad, Aenderungszeit und Groesse.
    -> Tupel, oder None, wenn die Datei nicht mehr da ist (dann wird nichts gemerkt)"""
    try:
        st = os.stat(pfad)
    except OSError:
        return None
    return ("datei", pfad, st.st_mtime_ns, st.st_size)


def inhalt_schluessel(name, daten):
    """Schluessel fuer ein Bild, das nicht als Datei vorliegt: Name, Groesse und Pruefsumme der Bytes.
    -> Tupel"""
    return ("inhalt", name, len(daten), hashlib.blake2b(daten, digest_size=16).digest())


def _merken(schluessel, klein_daten):
    """Ein Ergebnis in den Speicher legen, aelteste Eintraege fallen bis unter den Deckel. -> None"""
    groesse = len(klein_daten) if klein_daten is not None else 0
    if schluessel is None or groesse > _reg.KACHELBILD_SPEICHER_BYTES:
        return
    with _SCHLOSS:
        alt = _SPEICHER.pop(schluessel, None)
        _GEHALTEN[0] -= len(alt) if alt is not None else 0
        _SPEICHER[schluessel] = klein_daten
        _GEHALTEN[0] += groesse
        while _GEHALTEN[0] > _reg.KACHELBILD_SPEICHER_BYTES:
            _alt_schluessel, weg = _SPEICHER.popitem(last=False)
            _GEHALTEN[0] -= len(weg) if weg is not None else 0


def _verkleinern(daten):
    """Ein Bild dekodieren und auf die Breite aus der Registry bringen.
    -> JPEG-Bytes, None wenn es schon schmal genug ist; wirft, wenn es nicht lesbar ist"""
    import cv2
    import numpy as np
    bild = cv2.imdecode(np.frombuffer(daten, np.uint8), cv2.IMREAD_COLOR)
    if bild is None:
        raise ValueError("image not decodable")
    hoehe, breite = bild.shape[:2]
    ziel = _reg.KACHELBILD_BREITE
    if breite <= ziel:
        return None
    klein_bild = cv2.resize(bild, (ziel, max(1, round(hoehe * ziel / breite))), interpolation=cv2.INTER_AREA)
    ok, puffer = cv2.imencode(".jpg", klein_bild)
    if not ok:
        raise ValueError("JPEG encoding failed")
    return puffer.tobytes()


def klein(daten, schluessel, bildtyp):
    """Das Kachelbild zu einem Bild (JPEG oder PNG als Bytes), aus dem Speicher oder frisch verkleinert.
    -> (Bytes, Bildtyp): verkleinert als JPEG; das Original mit seinem Bildtyp, wenn es schmal genug oder unlesbar ist"""
    with _SCHLOSS:
        if schluessel is not None and schluessel in _SPEICHER:
            treffer = _SPEICHER[schluessel]
            return (treffer, "image/jpeg") if treffer is not None else (daten, bildtyp)
    try:
        klein_daten = _verkleinern(daten)
    except Exception:
        _logbuch.swallowed(_log, _logbuch.WARNING, "sending the original image instead of the small one")
        return daten, bildtyp
    _merken(schluessel, klein_daten)
    return (klein_daten, "image/jpeg") if klein_daten is not None else (daten, bildtyp)
