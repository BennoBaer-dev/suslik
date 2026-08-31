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

.380 (User-Entscheid 31.08.) — VOLLBAUM `data`: der Support erreicht den
GANZEN Datenordner read-only, nicht nur die benannten Bereiche. Anlass:
der Unbekannt-Pool eines Testers lag unter learn/ und war nicht abziehbar,
weil kein Bereich ihn nannte; jede kuenftige Ablage soll ohne Tabellen-
Pflege erreichbar sein. Der Sicherheits-Vertrag bleibt derselbe und
bekommt zwei Zusagen dazu:
 - Pfad-Wache: jeder Kandidat wird gegen den realpath von data_dir
   geankert (`..`, absoluter Pfad, hinausfuehrender Symlink -> nichts,
   der Aufrufer antwortet mit demselben generischen 404).
 - Maskier-Ordner: alles unter SUPPORT_MASKE_ORDNER (config/) geht NUR
   maskiert hinaus — einzeln UND im Verzeichnis-tar, denn dort liegen
   neben config.json die unmaskierten Alt-Store-Kopien config.json.vor_*.
   Was sich dort nicht als JSON deuten laesst, wird gar nicht roh
   ausgeliefert, sondern durch die Maske ersetzt (zu viel maskieren ist
   die sichere Richtung).
"""
import hashlib
import hmac
import io
import json
import mimetypes
import os
import re
import tarfile
import threading
import time

from core.registry import (SUPPORT_BEREICHE, SUPPORT_MASKE_ORDNER,
                           SUPPORT_SECRET_MUSTER, LAUF_ID_RE)

MASKE = "***"
# Bereichs-Code des Vollbaums — EINE Quelle fuer Handler, Route und Gate
# (K3: kein zweites Literal in verifyd). Die Registry deckt ihn als
# Bereich der Art "baum"; das Gate prueft genau diese Zuordnung.
BAUM_CODE = "data"
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


# ---------------------------------------------------------------- Vollbaum
def _drin(pfad, basis):
    """Liegt ein REALPATH innerhalb der Basis (oder ist sie selbst)?
    DIE eine Containment-Frage des Moduls — Listing, Einzeldatei und
    tar-Mitglied stellen sie alle hier."""
    return pfad == basis or pfad.startswith(basis + os.sep)


def maske_noetig(rel):
    """Muss diese Datei (Pfad RELATIV zu data_dir) maskiert ausgeliefert
    werden? Entscheidend ist der ORDNER (SUPPORT_MASKE_ORDNER), nicht der
    Dateiname: unter config/ liegen neben config.json auch Alt-Store-
    Kopien mit denselben Secrets unter anderem Namen."""
    teile = [t for t in str(rel or "").replace("\\", "/").split("/") if t]
    return bool(teile) and teile[0] in SUPPORT_MASKE_ORDNER


def maskierte_bytes(roh):
    """Inhalt einer Maskier-Datei -> die Bytes, die hinausgehen duerfen.
    Ganzes JSON (config.json) und JSON-Lines (config_audit.jsonl) werden
    feldweise ueber dieselbe Heuristik maskiert wie der config-Bereich.
    Was sich NICHT deuten laesst, geht NICHT roh hinaus, sondern als
    Maske — die Datei bleibt damit sichtbar (kein stiller Verlust), ihr
    Inhalt bleibt drin."""
    txt = roh.decode("utf-8", "replace")
    try:
        return (json.dumps(maskiert(json.loads(txt)), ensure_ascii=False,
                           indent=1) + "\n").encode()
    except ValueError:
        pass
    zeilen = []
    for z in txt.splitlines():
        s = z.strip()
        if not s:
            continue
        try:
            zeilen.append(json.dumps(maskiert(json.loads(s)),
                                     ensure_ascii=False))
        except ValueError:
            return (MASKE + "\n").encode()
    if not zeilen:
        return (MASKE + "\n").encode()
    return ("\n".join(zeilen) + "\n").encode()


def baum_listen(data_dir):
    """Vollstaendiges Metadaten-Listing des Datenordners: je Datei Pfad,
    Bytes, mtime — NIE Inhalte. Bewusst ohne Kappung (auch grosse Baeume
    werden ganz gelistet, es sind nur Metadaten).
    Zwei Wachen: Symlinks, die aus data_dir hinausfuehren, kommen nicht
    ins Listing (sie sind auch nicht holbar), und Ordner werden ueber
    ihren realpath entdoppelt — ein Symlink auf einen Vorfahren wuerde
    den Lauf sonst nie beenden."""
    basis = os.path.realpath(data_dir)
    dateien, summe, uebersprungen = [], 0, 0
    gesehen, stapel = {basis}, [basis]
    while stapel:
        try:
            eintraege = list(os.scandir(stapel.pop()))
        except OSError:
            uebersprungen += 1
            continue
        for e in eintraege:
            try:
                if e.is_symlink() and not _drin(os.path.realpath(e.path),
                                                basis):
                    uebersprungen += 1
                    continue
                if e.is_dir(follow_symlinks=True):
                    rp = os.path.realpath(e.path)
                    if rp not in gesehen:
                        gesehen.add(rp)
                        stapel.append(e.path)
                    continue
                if not e.is_file(follow_symlinks=True):
                    continue
                st = e.stat(follow_symlinks=True)
            except OSError:
                uebersprungen += 1
                continue
            dateien.append({"pfad": os.path.relpath(e.path, basis),
                            "bytes": st.st_size,
                            "mtime": int(st.st_mtime)})
            summe += st.st_size
    dateien.sort(key=lambda d: d["pfad"])
    return {"n": len(dateien), "bytes": summe,
            "uebersprungen": uebersprungen, "dateien": dateien}


def baum_aufloesen(data_dir, relpfad):
    """Einen /support/data/<relpfad> auf eine echte Stelle abbilden.
    -> ("datei"|"ordner", abspfad) oder (None, grund). JEDER Ausbruch
    (fuehrender /, ../, Symlink nach draussen) endet als None; der
    Aufrufer antwortet darauf mit dem generischen 404 — dieselbe
    Semantik wie bei einem unbekannten Bereich, kein Orakel."""
    basis = os.path.realpath(data_dir)
    rel = str(relpfad or "")
    if not rel or rel.startswith("/") or "\x00" in rel:
        return None, "bad path"
    p = os.path.realpath(os.path.join(basis, rel))
    if not _drin(p, basis):
        return None, "outside data dir"
    if os.path.isdir(p):
        return "ordner", p
    if os.path.isfile(p):
        return "datei", p
    return None, "not found"


def datei_vorbereiten(data_dir, pfad):
    """Was der Aufrufer VOR den HTTP-Headern wissen muss:
    -> (inhalt|None, bytes, content-type, maskiert?). Maskier-Dateien
    werden hier fertig maskiert (Config-Groessen, unkritisch im
    Speicher); alles andere wird spaeter gestreamt, damit auch grosse
    Dateien nicht in den RAM gehen. OSError faellt zum Aufrufer durch
    (verschwundene/gesperrte Datei -> 404, nie ein Traceback)."""
    rel = os.path.relpath(os.path.realpath(pfad), os.path.realpath(data_dir))
    if maske_noetig(rel):
        with open(pfad, "rb") as f:
            b = maskierte_bytes(f.read())
        return b, len(b), "text/plain; charset=utf-8", True
    ct = mimetypes.guess_type(pfad)[0] or "application/octet-stream"
    return None, os.path.getsize(pfad), ct, False


def datei_streamen(pfad, wfile, log, kennung, inhalt=None):
    """EINE Datei in den offenen Response-Stream (1-MB-Haeppchen).
    Fehlerregel wie bei tar_streamen: ab hier ist der Status raus, also
    endet ein Abbruch als EINE Log-Zeile, nie als Traceback-Serie."""
    t0, n = time.monotonic(), 0
    try:
        if inhalt is not None:
            wfile.write(inhalt)
            n = len(inhalt)
        else:
            with open(pfad, "rb") as f:
                while True:
                    stueck = f.read(1 << 20)
                    if not stueck:
                        break
                    wfile.write(stueck)
                    n += len(stueck)
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
        log(f"SUPPORT: {kennung} stream aborted after {n} byte(s) "
            f"({type(e).__name__})")
        return False, "aborted"
    log(f"SUPPORT: {kennung} served — {n} byte(s)"
        + (", masked" if inhalt is not None else "")
        + f", {time.monotonic() - t0:.1f}s")
    return True, ""


def download_name(rel, endung=""):
    """Content-Disposition-Name aus einem FREIEN Relativpfad. Anders als
    die Bereichs-Codes ist er nicht vorvalidiert — ein Anfuehrungszeichen
    darin wuerde den Header aufbrechen, deshalb bleibt nur Harmloses."""
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(rel or "")).strip("._")
    return f"suslik-support-{s or BAUM_CODE}{endung}"


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
        if b["art"] == "baum":
            # BEWUSST ohne Zaehlung: im Datenordner liegen clips/ und
            # events/, ein Walk wuerde den Einstieg zaeh machen. Wer
            # Zahlen braucht, holt das Listing (reine Metadaten).
            e["listing"] = f"/support/{code}"
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
    return _tar_schreiben(data_dir, start, arc0,
                          f"{code}/{lauf_id}" if lauf_id else code,
                          wfile, log, dateien=b.get("dateien"),
                          ausschluss=b.get("ausschluss", ()))


def baum_tar_streamen(data_dir, pfad, wfile, log):
    """EINEN Ordner aus dem Datenbaum als tar.gz streamen — derselbe
    Schreiber wie die benannten Bereiche (kein Parallelweg: Maskierung,
    Symlink-Wache und Fehler-Ebenen gelten damit hier automatisch mit).
    `pfad` ist bereits durch baum_aufloesen gegangen."""
    basis = os.path.realpath(data_dir)
    rel = os.path.relpath(pfad, basis)
    arc0 = os.path.basename(pfad.rstrip(os.sep)) or BAUM_CODE
    return _tar_schreiben(data_dir, pfad, arc0, f"{BAUM_CODE}/{rel}",
                          wfile, log)


def _tar_schreiben(data_dir, start, arc0, kennung, wfile, log,
                   dateien=None, ausschluss=()):
    """DER eine tar-Schreiber (Bereiche wie Vollbaum). Zwei Wachen je
    Mitglied, beide auf dem realpath: was aus data_dir hinausfuehrt,
    kommt nicht mit, und was in einem Maskier-Ordner liegt, kommt nur
    maskiert mit (sonst waere der Vollbaum-tar der Umweg um die
    Maskierung des Einzelabrufs)."""
    basis = os.path.realpath(data_dir)
    t0, gepackt, uebersprungen, maskiert_n = time.monotonic(), 0, 0, 0
    try:
        with tarfile.open(fileobj=wfile, mode="w|gz",
                          bufsize=512 * 1024) as tar:
            if dateien:
                kandidaten = [(os.path.join(start, d),
                               f"{arc0}/{d}") for d in dateien]
            else:
                kandidaten = []
                for w, _dirs, fs in os.walk(start):
                    if any(a in w for a in ausschluss):
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
                    rp = os.path.realpath(p)
                    if not _drin(rp, basis):
                        uebersprungen += 1
                        continue
                    if maske_noetig(os.path.relpath(rp, basis)):
                        with open(p, "rb") as fh:
                            roh = maskierte_bytes(fh.read())
                        ti = tarfile.TarInfo(arc)
                        ti.size = len(roh)
                        ti.mtime = int(os.path.getmtime(p))
                        ti.mode = 0o600
                        tar.addfile(ti, io.BytesIO(roh))
                        maskiert_n += 1
                    else:
                        tar.add(p, arcname=arc, recursive=False)
                    gepackt += 1
                except (FileNotFoundError, PermissionError, OSError):
                    uebersprungen += 1
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
        log(f"SUPPORT: {kennung} stream aborted by client after "
            f"{gepackt} file(s) ({type(e).__name__})")
        return False, "aborted"
    log(f"SUPPORT: {kennung} served — {gepackt} file(s)"
        + (f", {maskiert_n} masked" if maskiert_n else "")
        + (f", {uebersprungen} skipped" if uebersprungen else "")
        + f", {time.monotonic() - t0:.1f}s")
    return True, ""


def abzug_sperren():
    """Ein Bereichs-Abzug zur Zeit — non-blocking (Widerleger 13: check-
    then-act waere unter ThreadingHTTPServer ein Rennen). -> bool."""
    return _ABZUG.acquire(blocking=False)


def abzug_freigeben():
    _ABZUG.release()
