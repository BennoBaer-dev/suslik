"""core/vrampreise — was ein Rechenstrang auf DIESER Karte wirklich kostet.

WOZU ES DIESE DATEI GIBT, in Feldzahlen (Feldtester-Log 21.09.2026,
`dem Feldbefund vom 21.09.2026 (8-GB-Karte mit fuenf Waechtern; Analyse liegt im Repo unter analysen/, nicht im Image)` §4.1): seine GTX 1070 (8 GB) traegt fuenf
Live-Waechter und eine Frigate-Instanz. Die Strang-Leiter rechnete gegen die
Messtabelle aus `core.gpubudget` — 1940 MiB fuer den Prozess mit erster
Geometrie, 1235 fuer die zweite — und verweigerte JEDEN Rechenstrang (3175 MiB
Pflicht gegen 1929 MiB Budget). Die Erkennung war damit tot, und die Meldung
schickte den Betreiber in seine `config.json`. Diese Tabelle ist am 15.09. auf
einer RTX 2060 Mobile und einer RTX 3060 mit 4K-Clips entstanden; seine Kameras
liefern 2560x1920 und 1080p. Die Preise einer fremden Karte mit fremden
Bildgroessen als Mass der eigenen zu nehmen ist derselbe Fehler, den der
Arena-Deckel schon einmal bezahlt hat (gpubudget.arena_deckel_mb).

WAS HIER LIEGT: der KLEBRIGE Speicher der auf dieser Karte gemessenen Preise
(`<data_dir>/state/vram_preise.json`, Muster `placement.json`: atomar
geschrieben, Kopf mit Datum und Version) plus die Ableitung „aus
Konstellations-Messungen werden Posten-Preise". Was hier NICHT liegt: das Messen
selbst (das tut der Worker-Prozess mit der vorhandenen Sonde, s.
`worker_dienst.SpeicherWache._preis_buchen`) und die Arithmetik der Leiter (die
steht in `core.gpubudget`, und dort auch die Plausibilitaets-Regeln — EINE
Stelle je Frage).

DIE MESSGROESSE IST EIN PLATEAU, KEIN BAU-DELTA. Um einen Geometrie-Bau herum zu
messen ist GEMESSEN falsch: onnxruntime allokiert traege, der Zuwachs faellt erst
waehrend der ersten Analysen — 148 MiB gemessen gegen ~976 MiB wirklich
(Begruendung im Kopf von `worker_dienst._staffel`). Zu kleine Preise machen die
Leiter zu GROSS, also genau in die Richtung, die im Feld die Karte fuellt.
Gebucht wird deshalb das MAXIMUM, das der Prozess ueber sein Leben hielt, und
zwar je Konstellation (N Straenge x G gebaute Geometrien).

WAS DER PROZESS NICHT SIEHT, und was deshalb dazukommt: das NVDEC-ffmpeg je
Strang ist eine eigene pid (gpubudget.posten_ausserhalb_mb). Der gemessene
Prozess-Anteil traegt es nicht; die Konstellations-Summe hier rechnet den
gemessenen Decoder-Posten der Tabelle dazu (`DECODER_CUDA_MB`) und sagt das in
ihrem Beleg auch — eine halb gemessene Zahl, die sich ganz gemessen nennt, waere
die luegende Diagnose (K1).

Kontrakt wie `core.lernlauf`: reine Funktionen, Pfade/Daten als Parameter, kein
Dienst-Import, keine anlagenspezifischen Schwellen. Nichts hier wirft: eine
kaputte oder fehlende Preis-Datei heisst „es gilt die Tabelle", nie ein Ausfall.
"""
import json
import math
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
KONSTELLATIONEN_MAX = _gb.STRAENGE_MAX * 3


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
    („ist das schon ein Plateau?") macht `preise_ableiten` mit den Regeln aus
    `core.gpubudget`, damit es fuer dieselbe Frage nicht zwei Regeln gibt."""
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
        kons[k] = {"straenge": n, "geometrien": g,
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


def konstellations_preis_mb(mb, n_straenge):
    """WAS EINE KONSTELLATION KARTENWEIT KOSTET -> MB, aus dem gemessenen
    Prozess-Anteil.

    Zwei Zuschlaege, beide mit Quelle:
      * die 10 % Sicherheit, die der Inhaber-Entscheid vom 15.09. auf JEDEN
        Posten der Messtabelle gelegt hat (`gpubudget.PREIS_SICHERHEIT`) — ein
        gemessenes Maximum ist genauso ein Maximum;
      * je Strang das NVDEC-ffmpeg, das eine EIGENE pid hat und im
        Prozess-Anteil deshalb fehlt (`gpubudget.DECODER_CUDA_MB`, gemessen).
    Damit steht die Zahl im selben Mass wie die Tabellen-Summe: kartenweit,
    Decoder inbegriffen."""
    roh = math.ceil(int(mb or 0) * _gb.PREIS_SICHERHEIT)
    return int(roh) + max(1, int(n_straenge or 1)) * int(_gb.DECODER_CUDA_MB)


def preise_ableiten(stand, schluessel, gesamt_mb=0):
    """AUS KONSTELLATIONS-MESSUNGEN POSTEN-PREISE -> (preise, verworfen)

    `preise` ist das, was `gpubudget.preise_wirksam` erwartet:
    {"prozess": {"mb": …, "datum": …, "proben": …, "beleg": …}, …}. Fehlt ein
    Posten, bleibt er weg — dann gilt dort die Tabelle.

    NUR BENACHBARTE MESSUNGEN, nie Messung minus Tabellenwert:
        prozess    = K(1,1)                      (ein Strang, eine Geometrie)
        geometrie  = K(1,2) - K(1,1)             (dieselbe Strangzahl)
        strang     = K(n+1,g) - K(n,g)           (dieselbe Geometriezahl)
    Eine Differenz aus gemessen minus Tabelle waere eine halb gemessene Zahl,
    die niemand mehr einordnen kann — und sie koennte negativ werden.

    Jeder abgeleitete Preis laeuft durch `gpubudget.preis_pruefen` (Untergrenze,
    Kartengroesse, Mindest-Stuetzstellen). Was durchfaellt, steht in
    `verworfen` — mit Grund, damit der Aufrufer es LAUT sagen kann."""
    eintrag = ((stand or {}).get("karten") or {}).get(schluessel) or {}
    kons = eintrag.get("konstellationen") or {}
    if not kons:
        return {}, []

    def _k(n, g):
        t = kons.get(f"{n}x{g}")
        if not t or int(t.get("max_mb") or 0) <= 0:
            return None
        return t

    preise, verworfen = {}, []

    def _nimm(art, mb, quellen, beleg):
        proben = min(int((q.get("proben") or 0)) for q in quellen)
        datum = max(str(q.get("datum") or "") for q in quellen)
        ok, grund = _gb.preis_pruefen(art, mb, gesamt_mb, proben)
        if not ok:
            verworfen.append(f"{art}: {grund}")
            return
        preise[art] = {"mb": int(mb), "datum": datum, "proben": proben,
                       "beleg": beleg}

    basis = _k(1, 1)
    if basis is not None:
        _nimm("prozess", konstellations_preis_mb(basis["max_mb"], 1), [basis],
              "measured plateau of one thread with one geometry on this card "
              "(+10% safety, plus the table's decoder posten)")
    # Geometrie: dieselbe Strangzahl, eine Aufloesung mehr.
    for n in range(1, _gb.STRAENGE_MAX + 1):
        a, b = _k(n, 1), _k(n, 2)
        if a is None or b is None:
            continue
        _nimm("geometrie",
              konstellations_preis_mb(b["max_mb"], n)
              - konstellations_preis_mb(a["max_mb"], n), [a, b],
              f"difference between {n} thread(s) with two geometries and with "
              f"one, measured on this card")
        break
    # Strang: dieselbe Geometriezahl, ein Strang mehr.
    for g in (2, 1, 3):
        for n in range(1, _gb.STRAENGE_MAX):
            a, b = _k(n, g), _k(n + 1, g)
            if a is None or b is None:
                continue
            _nimm("strang",
                  konstellations_preis_mb(b["max_mb"], n + 1)
                  - konstellations_preis_mb(a["max_mb"], n), [a, b],
                  f"difference between {n + 1} and {n} thread(s) at {g} "
                  f"geometry/ies, measured on this card")
            break
        if "strang" in preise:
            break
    return preise, verworfen


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
                                    "datum": v.get("datum")}
                                for k, v in sorted(kons.items())},
            "karten_bekannt": len(((stand or {}).get("karten") or {}))}
