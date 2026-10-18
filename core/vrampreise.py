"""Speichert eigene CUDA-Gesamtspitzen über den bestehenden Zustandsspeicher.

MS1 ersetzt abgeleitete Prozess-/Strang-/Geometriepreise durch tatsächliche
Gesamtzustände mit Formen und materialisierten Sätzen. Historische Einträge
bleiben erhalten, werden aber ausdrücklich als unpassend ausgewiesen.
Die bestehenden Zähler je Worker-Prozess und erlaubten Schreibzeitpunkte
bleiben unverändert; Lesen bucht und schreibt keine Messung.
"""
import json
import os
import tempfile
import time

from core import gpubudget as _gb
from core import logbuch as _logbuch
_log = _logbuch.logger(__name__)

SCHEMA_VERSION = 1
DATEI = "vram_preise.json"

# HAUSHALT, keine Messgroessen: beide Zahlen begrenzen eine DATEI, nicht eine
# Entscheidung. Der Schluessel traegt die suslik-Version (s. `hw_schluessel`),
# also entsteht bei jedem Update ein neuer Eintrag — vier bedeutet „die
# aktuelle und die drei davor"; was darunter faellt, ist ohnehin nicht mehr
# gefragt. Die Konstellations-Zahl kommt aus dem, was ein Prozess ueberhaupt
# annehmen kann: hoechstens `STRAENGE_MAX` Straenge (harter Riegel) und
# hoechstens drei Geometrien (mehr haelt ein Prozess nicht, s. Messtabelle) —
# abgeleitet, nicht gegriffen.
KARTEN_MAX = 4
KONSTELLATIONEN_MAX = _gb.STRAENGE_MAX * _gb.STRAENGE_MAX


def pfad(data_dir):
    return os.path.join(data_dir, "state", DATEI)


def hw_schluessel(kind, karte, gesamt_mb, version):
    """DIE KENNUNG, unter der Preise gelten -> str.

    Karte + Groesse + Backend + suslik-Version. Warum die VERSION dazugehoert,
    obwohl sie die Karte nicht aendert: was ein Prozess auf ihr belegt, haengt
    an den Modellen und der Laufzeit, die diese Version mitbringt — ein Update,
    das eine Session dazunimmt, macht jeden alten Preis zu klein. Nach einem
    Update gilt also wieder die Tabelle, bis diese Anlage neu gemessen hat: die
    vorsichtige Richtung, dieselbe wie bei `_placement_hw_key`.

    Warum NICHT `verifyd._placement_hw_key`: der traegt CPU und Geraeteliste,
    aber nicht die Karte, gegen deren Speicher hier geplant wird — und auf einer
    Maschine mit zwei verschiedenen Karten waere er derselbe."""
    return "|".join([str(karte or "unknown card"), f"{int(gesamt_mb or 0)}MiB",
                     str(kind or "?"), str(version or "dev")])


def lesen(data_dir):
    """Der gespeicherte Stand -> dict (leer, wenn es keinen gibt).

    Eine unlesbare Datei ist hier KEIN Fehlerfall, der jemanden aufhaelt: dann
    gilt die Tabelle wie vor .544. Gemeldet wird das vom Aufrufer, der auch
    weiss, wohin er meldet."""
    try:
        with open(pfad(data_dir), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:                                      # noqa: BLE001
        _logbuch.swallowed(_log, _logbuch.WARNING, "returning {}")
        return {}
    if not isinstance(d, dict) or int(d.get("schema") or 0) != SCHEMA_VERSION:
        return {}
    if not isinstance(d.get("karten"), dict):
        return {}
    return d


def schreiben(data_dir, stand):
    """Atomar wie jeder Zustands-Schrieb (tmp + fsync + rename). -> True|False"""
    p = pfad(data_dir)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), prefix=".vrampreise-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(stand, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return True
    except Exception:                                      # noqa: BLE001
        _logbuch.swallowed(_log, _logbuch.ERROR, "returning False", throttle=False)
        return False


def _jetzt_datum(ts=None):
    return time.strftime("%Y-%m-%d", time.localtime(ts or time.time()))


def buchen(stand, schluessel, kopf, proben, gesamt_mb=0, jetzt=None):
    """Die Preis-Toepfe EINES Worker-Prozesses in den Stand legen.
    -> (stand, gebucht, verworfen)

    `proben` ist, was der Prozess gemeldet hat: {"1x2": {"straenge": 1,
    "geometrien": 2, "max_mb": …, "proben": …}, …}. Gefuehrt wird je
    Konstellation das MAXIMUM ueber alle Prozesse dieser Kennung und die Summe
    der Proben — ein zweiter Prozess mit denselben Bildern misst dasselbe noch
    einmal, und mehr Stuetzstellen sind hier immer die bessere Auskunft.

    `verworfen` traegt, was NICHT gebucht wurde, mit Grund. Verworfen wird
    grob-falsches (0, negativ, groesser als die Karte) — die feine Bewertung
    und die Zustandszuordnung prüft `gesamtzustaende`; eine Nachbarpreis-
    oder Drei-Proben-Freigabe gibt es für CUDA nicht mehr."""
    d = dict(stand or {})
    d["schema"] = SCHEMA_VERSION
    karten = dict(d.get("karten") or {})
    eintrag = dict(karten.get(schluessel) or {})
    eintrag.update({k: v for k, v in (kopf or {}).items() if v is not None})
    eintrag["gesehen"] = round(float(jetzt or time.time()), 1)
    kons = dict(eintrag.get("konstellationen") or {})
    gebucht, verworfen = 0, []
    for k, topf in sorted((proben or {}).items()):
        try:
            n = max(1, int((topf or {}).get("straenge") or 0))
            g = max(1, int((topf or {}).get("geometrien") or 0))
            mb = int((topf or {}).get("max_mb") or 0)
            pn = max(0, int((topf or {}).get("proben") or 0))
        except (TypeError, ValueError, AttributeError):
            verworfen.append(f"{k}: unreadable measurement")
            continue
        if mb <= 0:
            verworfen.append(f"{k}: {mb} MiB is not a measurement")
            continue
        if gesamt_mb and mb > int(gesamt_mb):
            verworfen.append(f"{k}: {mb} MiB is larger than the whole card "
                             f"({int(gesamt_mb)} MiB)")
            continue
        alt = dict(kons.get(k) or {})
        kons[k] = {"messart": topf.get("messart"), "formen": topf.get("formen"),
                   "straenge": n, "geometrien": g,
                   "max_mb": max(int(alt.get("max_mb") or 0), mb),
                   "proben": int(alt.get("proben") or 0) + pn,
                   "zuerst": alt.get("zuerst") or round(float(jetzt or time.time()), 1),
                   "zuletzt": round(float(jetzt or time.time()), 1),
                   "datum": _jetzt_datum(jetzt)}
        gebucht += 1
    if len(kons) > KONSTELLATIONEN_MAX:
        for k in sorted(kons, key=lambda x: kons[x].get("zuletzt") or 0
                        )[:len(kons) - KONSTELLATIONEN_MAX]:
            kons.pop(k, None)
    eintrag["konstellationen"] = kons
    karten[schluessel] = eintrag
    if len(karten) > KARTEN_MAX:
        for k in sorted(karten, key=lambda x: (karten[x] or {}).get("gesehen") or 0
                        )[:len(karten) - KARTEN_MAX]:
            karten.pop(k, None)
    d["karten"] = karten
    d["geschrieben"] = _jetzt_datum(jetzt)
    return d, gebucht, verworfen


def counters_merge(alt, proben, jetzt=None):
    """Die Meldung EINES Worker-Prozesses in seine Zaehler legen (Bauplan Feldtempo, T-E4).
    -> (zaehler, geaendert): {"proben": {konstellation: topf}, "ts": …} und ob sich eine Zahl geaendert hat.

    Der Worker meldet mit jeder Antwort die Summe seit SEINEM Start, also wiederholt sich
    dieselbe Zahl. Gefuehrt wird deshalb je Konstellation nur der HOECHSTE Probenzaehler und
    das HOECHSTE `max_mb`: eine wiederholte oder verspaetete Meldung mit kleinerem oder gleichem
    Zaehler aendert nichts. `ts` ist der Moment der letzten Aenderung, nicht der letzten
    Meldung — ein Zeitstempel allein ist keine neue Zahl (T-E6). Ein unlesbarer Topf wird so
    abgelegt, wie er kam; verworfen wird er mit Grund in `buchen`, an EINER Stelle."""
    toepfe = {k: dict(v) if isinstance(v, dict) else v
              for k, v in ((alt or {}).get("proben") or {}).items()}
    geaendert = False
    for k, topf in (proben or {}).items():
        vorher = toepfe.get(k)
        try:
            mb = int((topf or {}).get("max_mb") or 0)
            pn = int((topf or {}).get("proben") or 0)
            neu = dict(topf, max_mb=max(mb, int((vorher or {}).get("max_mb") or 0)),
                       proben=max(pn, int((vorher or {}).get("proben") or 0)))
        except (TypeError, ValueError, AttributeError):
            neu = topf
        if neu != vorher:
            toepfe[k] = neu
            geaendert = True
    ts = (round(float(jetzt or time.time()), 1) if geaendert
          else (alt or {}).get("ts"))
    return {"proben": toepfe, "ts": ts}, geaendert


def total(start, schluessel, kopf, prozesse, gesamt_mb=0):
    """DIE EINE SUMME aus dem Stand beim Dienststart und den Zaehlern aller Prozesse (T-E5).
    -> (stand, verworfen); `start` und `prozesse` bleiben unveraendert.

    Dieselbe Rechnung fuer Planung und Datei: die Planung rechnet damit ohne Dateizugriff, und
    in die Datei kommt genau diese Summe — nie das Buchen eines einzelnen Prozesses. Eine
    Meldung, die nach einem Schreiben noch fuer einen alten Prozess ankommt, ist beim naechsten
    Schreiben dabei, und nichts zaehlt doppelt, weil `start` waehrend der Lebenszeit des
    Dienstes derselbe bleibt. `prozesse` ist {startnummer: zaehler aus `counters_merge`}."""
    stand, verworfen = start or {}, []
    for nr in sorted(prozesse or {}):
        z = (prozesse or {}).get(nr) or {}
        if not z.get("proben"):
            continue
        stand, _gebucht, v = buchen(stand, schluessel, kopf, z["proben"],
                                    gesamt_mb=gesamt_mb, jetzt=z.get("ts"))
        verworfen.extend(v)
    return stand, verworfen


def numbers(stand):
    """Die Zahlen eines Stands ohne Zeitstempel und Kopf (T-E6) -> dict.
    Gleich heisst: ein Schreiben aenderte keine Zahl in der Datei."""
    aus = {}
    for s, eintrag in ((stand or {}).get("karten") or {}).items():
        kons = (eintrag or {}).get("konstellationen") or {}
        if kons:
            aus[s] = {k: tuple((t or {}).get(f) for f in ("straenge", "geometrien",
                                                         "max_mb", "proben"))
                      for k, t in kons.items()}
    return aus


def stand_zeigen(stand, schluessel):
    """Was in /health ueber diesen Speicher stehen soll -> dict.
    Nur Zahlen und Herkunft; entschieden wird hier nichts."""
    eintrag = ((stand or {}).get("karten") or {}).get(schluessel) or {}
    kons = eintrag.get("konstellationen") or {}
    return {"schluessel": schluessel,
            "karte": eintrag.get("karte"),
            "geschrieben": (stand or {}).get("geschrieben"),
            "konstellationen": {k: {"max_mb": v.get("max_mb"),
                                    "proben": v.get("proben"),
                                    "datum": v.get("datum"),
                                    "messart": v.get("messart") or "historical",
                                    "formen": v.get("formen")}
                                for k, v in sorted(kons.items())},
            "karten_bekannt": len(((stand or {}).get("karten") or {}))}


def gesamtzustaende(stand, schluessel, gesamt_mb):
    """Liest gültige eigene CUDA-Gesamtspitzen ohne Zuschlag oder Nachbarpaare.
    -> (Zustände, Gründe); historische unmarkierte Messungen bleiben erhalten."""
    kons = ((((stand or {}).get("karten") or {}).get(schluessel) or {})
            .get("konstellationen") or {})
    states, rejected = {}, []
    for key, value in kons.items():
        mb = value.get("max_mb")
        forms = value.get("formen")
        valid_forms = (isinstance(forms, list) and len(forms) == value.get("geometrien")
                       and all(isinstance(form, (list, tuple)) and len(form) == 3
                               and all(type(v) is int for v in form)
                               and form[0] > 0 and form[1] > 0
                               and 0 <= form[2] <= _gb.STRAENGE_MAX for form in forms)
                       and max((form[2] for form in forms), default=0) == value.get("straenge"))
        if (not valid_forms or value.get("messart") != "cuda_total_v1" or not value.get("formen")
                or type(mb) is not int or not 0 < mb <= gesamt_mb):
            rejected.append(f"{key}: historical, incompatible or invalid total state")
            continue
        states[key] = dict(value)
    return {"zustaende": states}, rejected
