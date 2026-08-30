"""core/support — der Support-Zugriff (analysen/support_api.md, 28.08.2026).

Lese-Endpunkte fuer den Fern-Support: benannte Bereiche aus SUPPORT_BEREICHE
(core/registry — DIE eine Quelle) als tar.gz-STREAM oder JSON. Entstanden aus
drei Feld-Beweisen vom 28.08.: /backup_voll scheitert hinter Reverse-Proxys
(Vorab-Packen -> 504), Einzel-Scraping reizt Bot-Filter, und der Support
brauchte real Logs/Faces/Lernlauf-Ergebnisse.

Sicherheits-Vertrag (Widerleger-Auflagen, alle 21 Befunde in analysen/
support_api.md):
 - Schalter support_zugriff + Token support_token werden je Request LIVE aus
   dem Store gelesen (Rotation wirkt sofort, kein Neustart noetig).
 - Token-Vergleich NUR hier (hmac.compare_digest); leerer Store-Token
   matcht NIE. Abweisung ist Sache des Aufrufers: er faellt in den
   GENERISCHEN 404 durch (kein eigener Zweig = kein Orakel).
 - realpath-Wachen ankern auf der FIXEN Wurzel (refs-Muster) — die Lauf-ID
   steht nur im Kandidaten, nie in der Basis.
 - EIN Abzug zur Zeit (Semaphore non-blocking), Freigabe im finally AUCH im
   Abbruch-Pfad (sonst sperrt der haeufigste Fehler den Kanal dauerhaft).
 - Stream-Fehler (Client weg, Datei waehrend des Packens verschwunden)
   enden LEISE als Abbruch-Log-Zeile, nie als Traceback-Serie (gemessen:
   tarfile reicht BrokenPipe/FileNotFoundError sonst ungefangen hoch, und
   das Prod-Log-Gate wuerde rot).
Store-IO wird injiziert (kein verifyd-Rueckimport, Muster core/melden.py).
"""
import hashlib
import hmac
import json
import os
import re
import tarfile
import threading
import time

from core.registry import SUPPORT_BEREICHE, SUPPORT_SECRET_MUSTER, LAUF_ID_RE

MASKE = "***"
_ABZUG = threading.Semaphore(1)          # ein Bereichs-Abzug zur Zeit
_ABWEIS_DROSSEL = {"bis": 0.0, "zaehler": 0}   # Audit: Abweisungen gedrosselt


def zugriff_ok(store, header_token):
    """DIE eine Pruefstelle: Schalter an UND Token stimmt (konstante Zeit).
    Ein leerer/fehlender Store-Token matcht NIE (auch nicht gegen leer)."""
    if not isinstance(store, dict) or not store.get("support_zugriff"):
        return False
    soll = str(store.get("support_token") or "")
    ist = str(header_token or "")
    if not soll or not ist:
        return False
    return hmac.compare_digest(soll.encode(), ist.encode())


def abweisung_zaehlen(log):
    """Audit der Abweisungen, gedrosselt (Widerleger 19): hoechstens EINE
    Zeile je Minute, mit Zaehler — Brute-Force bleibt sichtbar, kann aber
    keine echten Diagnosezeilen aus der 64-MB-Rotation rollen."""
    jetzt = time.time()
    _ABWEIS_DROSSEL["zaehler"] += 1
    if jetzt >= _ABWEIS_DROSSEL["bis"]:
        log(f"SUPPORT: {_ABWEIS_DROSSEL['zaehler']} rejected request(s) in "
            f"the last minute (switch off, or wrong/missing token)")
        _ABWEIS_DROSSEL["bis"] = jetzt + 60
        _ABWEIS_DROSSEL["zaehler"] = 0


def maskiert(wert, name=""):
    """Config-Export-Maskierung (Widerleger 1): rekursiv; ein Feld ist
    Secret, wenn sein Name eines der SUPPORT_SECRET_MUSTER enthaelt.
    Zu viel maskieren ist die sichere Richtung."""
    if isinstance(wert, dict):
        return {k: (MASKE if _geheim(k) and isinstance(v, (str, int, float))
                    and v not in ("", None)
                    else maskiert(v, k)) for k, v in wert.items()}
    if isinstance(wert, list):
        return [maskiert(v, name) for v in wert]
    return wert


def _geheim(name):
    n = str(name).lower()
    return any(m in n for m in SUPPORT_SECRET_MUSTER)


def lauf_id_ok(lauf_id):
    return bool(re.fullmatch(LAUF_ID_RE, str(lauf_id or "")))


def _wurzel(data_dir, bereich):
    return os.path.realpath(os.path.join(data_dir, *bereich["wurzel"]))


def inventar(data_dir, version):
    """JSON-Einstieg: was ist holbar, wie gross. Liest NUR die Registry-
    Tabelle (Deckungs-Vertrag)."""
    aus = {"version": version, "bereiche": {}}
    for code, b in SUPPORT_BEREICHE.items():
        e = {"art": b["art"], "hinweis": b["text"]}
        if b["art"] == "tar" and not b.get("je_lauf"):
            n = groesse = 0
            wurz = _wurzel(data_dir, b)
            dateien = b.get("dateien")
            if os.path.isdir(wurz):
                if dateien:
                    for d in dateien:
                        p = os.path.join(wurz, d)
                        if os.path.isfile(p):
                            n += 1
                            groesse += os.path.getsize(p)
                else:
                    for w, _dirs, fs in os.walk(wurz):
                        if any(a in w for a in b.get("ausschluss", ())):
                            continue
                        for f in fs:
                            try:
                                n += 1
                                groesse += os.path.getsize(os.path.join(w, f))
                            except OSError:
                                pass
            e["dateien"] = n
            e["bytes"] = groesse
        if b.get("je_lauf"):
            wurz = _wurzel(data_dir, b)
            try:
                e["laeufe"] = sorted(
                    d for d in os.listdir(wurz)
                    if re.fullmatch(LAUF_ID_RE, d)
                    and os.path.isdir(os.path.join(wurz, d)))
            except OSError:
                e["laeufe"] = []
        aus["bereiche"][code] = e
    return aus


def tar_streamen(data_dir, code, wfile, log, lauf_id=None):
    """EINEN Bereich als tar.gz in den offenen Response-Stream schreiben.
    -> (ok, grund). Der Aufrufer hat die Header schon gesendet; Fehler ab
    hier koennen nur noch den Stream beenden, nie den Status aendern —
    deshalb enden sie als EINE Log-Zeile (nie Traceback, Prod-Log-Gate)."""
    b = SUPPORT_BEREICHE.get(code)
    if not b or b["art"] != "tar":
        return False, "unknown area"
    basis = _wurzel(data_dir, b)
    if b.get("je_lauf"):
        if not lauf_id_ok(lauf_id):
            return False, "bad run id"
        kand = os.path.realpath(os.path.join(basis, lauf_id))
        # Wache auf der FIXEN Wurzel (Widerleger 8): auch ein Symlink
        # state/lernlauf/<id> -> / fuehrt nicht hinaus.
        if not kand.startswith(basis + os.sep) or not os.path.isdir(kand):
            return False, "no such run"
        start, arc0 = kand, lauf_id
    else:
        if not os.path.isdir(basis):
            return False, "area empty"
        start, arc0 = basis, code
    # Die Ein-Abzug-Sperre haelt der AUFRUFER (abzug_sperren/-freigeben,
    # Widerleger 13): er muss VOR den HTTP-Headern 429 sagen koennen —
    # nach gesendeten 200-Headern gaebe es nur noch leere Archive.
    t0, gepackt, uebersprungen = time.monotonic(), 0, 0
    try:
        with tarfile.open(fileobj=wfile, mode="w|gz",
                          bufsize=512 * 1024) as tar:
            dateien = b.get("dateien")
            if dateien:
                kandidaten = [(os.path.join(start, d),
                               f"{arc0}/{d}") for d in dateien]
            else:
                kandidaten = []
                for w, _dirs, fs in os.walk(start):
                    if any(a in w for a in b.get("ausschluss", ())):
                        continue
                    for f in sorted(fs):
                        p = os.path.join(w, f)
                        kandidaten.append(
                            (p, arc0 + "/" + os.path.relpath(p, start)))
            for p, arc in kandidaten:
                # je Mitglied ein eigener Fang: eine Datei, die zwischen
                # Listing und add verschwindet (Log-Drehung!), kostet
                # nie den ganzen Abzug.
                try:
                    tar.add(p, arcname=arc, recursive=False)
                    gepackt += 1
                except (FileNotFoundError, PermissionError, OSError):
                    uebersprungen += 1
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
        log(f"SUPPORT: {code} stream aborted by client after "
            f"{gepackt} file(s) ({type(e).__name__})")
        return False, "aborted"
    log(f"SUPPORT: {code}{('/' + lauf_id) if lauf_id else ''} served — "
        f"{gepackt} file(s)"
        + (f", {uebersprungen} skipped" if uebersprungen else "")
        + f", {time.monotonic() - t0:.1f}s")
    return True, ""


def abzug_sperren():
    """Ein Bereichs-Abzug zur Zeit — non-blocking (Widerleger 13: check-
    then-act waere unter ThreadingHTTPServer ein Rennen). -> bool."""
    return _ABZUG.acquire(blocking=False)


def abzug_freigeben():
    _ABZUG.release()
