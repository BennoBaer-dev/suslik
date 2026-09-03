"""core/frigate_auth — DER EINE HTTP-Griff nach Frigate (Vormerkung 5e).

Zweck: Frigates authentifizierter Port (8971) verlangt seit Frigate 0.14 einen
Login; der interne 5000er tut es nicht. suslik soll BEIDES koennen, ohne dass
eine Installation ohne Zugangsdaten irgendetwas anders macht als bisher.

Der Vertrag dieses Moduls, in dieser Reihenfolge:

 1. KENNUNG IMMER. Jeder Frigate-Request traegt `User-Agent: suslik/<version>`
    — mit und ohne Login. Ehrlich und stabil, weil Betreiber davor Proxys
    haben, die Nicht-Browser-Kennungen aussperren und eine Ausnahme auf genau
    diese Kennung eintragen (Anlass 26.08.: ein Proxy blockte `curl/...`, die
    IP war laengst frei — die Diagnose "403 = IP gesperrt" war ein eigener
    Testfehler). Die Version kommt aus SUSLIK_VERSION, nie als Literal.
    DAS ist die EINZIGE Aenderung an einer Installation ohne Zugangsdaten:
    vorher stand dort urllibs `Python-urllib/3.x`.

 2. OHNE ZUGANGSDATEN AENDERT SICH NICHTS. Kein /api/login, kein Cookie, kein
    eigener SSL-Kontext, dieselben Pfade, dieselben Timeouts, dieselbe
    Fehlerklasse. Das ist der Regressions-Vertrag der Vormerkung und der
    Grund, warum die Zugangsdaten OPTIONAL sind: Prod laeuft hier ueber den
    internen 5000er ohne Auth weiter.

 3. MIT ZUGANGSDATEN: `POST {basis}/api/login` mit JSON {"user":…,"password":…},
    Frigate antwortet 200 und setzt `frigate_token` als Cookie; jeder
    Folge-Request traegt das Cookie. Laeuft das Token ab, antwortet Frigate
    mit 401 — dann GENAU EIN Re-Login und GENAU EINE Wiederholung, danach
    ein ehrlicher Fehler. Nie eine Schleife: ein falsches Passwort wuerde
    sonst im Sekundentakt gegen die Anmeldung laufen.

 4. TLS. Frigates Auth-Port ist ab Werk SELBSTSIGNIERT. `frigate_tls_verify`
    (Default AN) darf das abschalten — bewusst und sichtbar, nur dann wird
    ueberhaupt ein eigener SSL-Kontext gebaut.

Konfigurations-Weg (dasselbe Muster wie FRIGATE_URL, s. verifyd load_config):
Der Dienst legt die Werte in die Prozess-Umgebung, jeder Subprozess erbt sie
ueber `dict(os.environ, …)` — Worker, analyze, sync_refs, anlernen. Fehlt die
Umgebung (docker-exec-Diagnoselauf), faellt das Modul auf den gespeicherten
Store zurueck, genau wie sync_refs._frigate() es fuer die URL tut.

Zustand ist PROZESSWEIT: jeder Prozess meldet sich selbst an und haelt sein
eigenes Token. Das ist Absicht — ein geteiltes Token waere ein Schreibweg
zwischen Prozessen, und Frigate erlaubt mehrere Anmeldungen.

Grenze, deklariert: `data` muss bytes sein (oder None). Ein Datei-artiges
`data` ueberlebte die EINE Wiederholung nach 401 nicht, weil der Strom dann
schon gelesen waere. Alle Aufrufer dieses Projekts reichen bytes.
"""
import collections
import http.cookies
import json
import os
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

# ------------------------------------------------------------------ Mengen
# ZENTRALE Menge der Frigate-eigenen HTTP-Pfade. Sie ist KEINE gepflegte
# Stellen-Liste (das waere der K3-Fehlermodus), sondern der Wortschatz, an dem
# der Gate-Anker tools/frigate_deckung.py Frigate-Verkehr ERKENNT: eine Datei,
# die eines dieser Stuecke in einem HTTP-Aufruf traegt, muss durch dieses Modul
# gehen oder eine Ausnahme mit Grund tragen.
FRIGATE_PFADE = (
    "/api/version",
    "/api/config",
    "/api/faces",
    "/api/events",
    "/api/logs/frigate",
    "/api/login",
    "/clips/faces/",
    "/vod/event/",
    "snapshot-clean.webp",
    # MIT fuehrendem Schraegstrich: der Frigate-Pfad heisst
    # /api/events/{id}/clip.mp4. Das nackte "clip.mp4" ist mehrdeutig — es ist
    # auch der Anhang-DATEINAME, den core/melden.py an Telegram uebergibt, und
    # der hat mit Frigate nichts zu tun (Erst-Messung des Ankers 26.08. fing
    # genau diesen Falsch-Positiv).
    "/clip.mp4",
)

# Frigates Token-Cookie (Frigate 0.14+, an der laufenden 0.18.0 verifiziert).
COOKIE_NAME = "frigate_token"

LOGIN_PFAD = "/api/login"

# ------------------------------------------------------------------ Zustand
_sperre = threading.Lock()
_token = {"wert": "", "basis": ""}      # Token gilt je Frigate-Basis


def zuruecksetzen():
    """Token vergessen (Tests, Config-Wechsel). Kein Netzverkehr."""
    with _sperre:
        _token["wert"], _token["basis"] = "", ""


# ------------------------------------------------- Antwortzeit (Zeitschiene)
# ANLASS (Feldbefund 02.09., User-Wunsch "eine Zeitschiene, wie lange wir auf
# Frigate warten, dass man sieht, wenn das zu lange dauert"): die Event-API
# eines Testers antwortete 35 Minuten lang mit rund 120 s je Anfrage. Fuer den
# Nutzer war das UNSICHTBAR — der Dienst sah beschaeftigt aus, und nirgends
# stand, worauf er wartet. Deshalb misst der EINE Griff jetzt mit.
#
# KEINE eigene Schwelle, kein Alarm: die Zahl wird nur sichtbar gemacht (der
# Balkenverlauf zeigt Ausreisser von allein). Zwei Stellen mit eigenen
# Schwellen driften auseinander — dieselbe Regel wie auf der Systemseite.
#
# WAS gemessen wird: die Zeit, bis Frigate ANTWORTET (Verbindungsaufbau +
# erste Kopfzeilen), nicht die Uebertragung des Rumpfes — urlopen kehrt mit
# den Koepfen zurueck, den Rumpf liest der Aufrufer selbst. Genau das ist die
# Wartezeit, um die es geht: ein langsamer Clip-DOWNLOAD ist etwas anderes als
# ein haengender Server. Fehlversuche zaehlen MIT — ein Zug, der nach 20 s im
# Timeout endet, hat 20 s gewartet, und das ist die interessanteste Messung
# ueberhaupt.
#
# GRENZE, deklariert: der Ring ist PROZESSWEIT. Der Dienst sieht damit seine
# eigenen Zuege (Sweep, Event-Poll, Konfig, Snapshots) — NICHT die des
# Worker-Subprozesses und nicht die ffmpeg-Zuege des VOD-Weges (ffmpeg_kopf
# reicht nur Kopfzeilen weiter, den HTTP-Zug macht ffmpeg selbst). Der
# Feldfall lag im Dienst-Prozess, dort schaut die Seite hin.
ANTWORT_RING_MAX = 600        # ~10 min Historie bei einem Zug je Sekunde
ANTWORT_FENSTER_S = 60.0      # Rueckfall; der Dienst reicht core.systemstat.TAKT_S
_zeit_sperre = threading.Lock()
_zeiten = collections.deque(maxlen=ANTWORT_RING_MAX)   # (ts, dauer_s, klasse)


def zeiten_zuruecksetzen():
    """Ring leeren (Tests). Kein Netzverkehr."""
    with _zeit_sperre:
        _zeiten.clear()


def pfadklasse(url):
    """Grobe Herkunft eines Zuges -> ein Stueck aus FRIGATE_PFADE oder
    "andere".

    Der Wortschatz kommt aus der ZENTRALEN Menge, nie aus einer zweiten
    Pfad-Liste (K3-Regel). Das LAENGSTE passende Stueck gewinnt, damit
    /api/events/<id>/clip.mp4 als "/api/events" zaehlt und nicht am kuerzeren
    "/clip.mp4" haengenbleibt.

    Gespeichert wird ausschliesslich diese Klasse, nie die URL: die traegt
    Host, Port und Event-IDs, und der Ring geht ueber die Systemseite in eine
    Datei, die 48 h liegen bleibt."""
    u = str(url or "")
    treffer = [p for p in FRIGATE_PFADE if p in u]
    return max(treffer, key=len) if treffer else "andere"


def _zeit_merken(url, dauer_s):
    """Eine Messung in den Ring. Wirft nie: die Messung ist Beiwerk, der
    HTTP-Zug ist die Aufgabe (dieselbe K-1-Haltung wie bei der
    Beweisbild-Ablage)."""
    try:
        with _zeit_sperre:
            _zeiten.append((time.time(), float(dauer_s), pfadklasse(url)))
    except Exception:                                       # noqa: BLE001
        pass


def antwortzeiten(fenster_s=ANTWORT_FENSTER_S):
    """Die Zeitschiene fuer die Systemseite -> dict.

    n / mittel_s / max_s beziehen sich auf das FENSTER (Vorgabe: der
    Sammel-Takt der Systemseite, damit "letzte Minute" genau der Balken ist,
    den die Seite zeichnet). `klassen` schluesselt dasselbe Fenster nach
    Pfadklasse auf — ein Durchlauf, also billig.

    letzte_s ist die zuletzt gemessene Antwortzeit UEBERHAUPT, mit ihrem
    Alter daneben: auf einer ruhigen Anlage liegt der letzte Zug oft laenger
    zurueck als ein Takt, und ein "—" waere dort weniger ehrlich als die
    letzte bekannte Zahl mit Altersangabe.

    Leerer Ring (dieser Prozess hat noch nie mit Frigate gesprochen) ->
    grund "keine_anfragen". Keine erfundene Null (Ehrlichkeits-Regel der
    Systemseite: ein fehlender Wert ist kein Ruhewert)."""
    jetzt = time.time()
    with _zeit_sperre:
        alle = list(_zeiten)
    fenster_s = float(fenster_s)
    if not alle:
        return {"grund": "keine_anfragen", "fenster_s": round(fenster_s, 1)}
    grenze = jetzt - fenster_s
    fenster = [(ts, d, k) for ts, d, k in alle if ts >= grenze]
    dauern = [d for _ts, d, _k in fenster]
    klassen = {}
    for _ts, d, k in fenster:
        e = klassen.setdefault(k, {"n": 0, "max_s": 0.0})
        e["n"] += 1
        e["max_s"] = round(max(e["max_s"], d), 2)
    letzte_ts, letzte_d, _lk = alle[-1]
    return {"grund": None,
            "fenster_s": round(fenster_s, 1),
            "n": len(dauern),
            "mittel_s": (round(sum(dauern) / len(dauern), 2) if dauern else None),
            "max_s": (round(max(dauern), 2) if dauern else None),
            "letzte_s": round(letzte_d, 2),
            "letzte_alter_s": round(max(0.0, jetzt - letzte_ts), 1),
            "klassen": klassen}


# ------------------------------------------------------------------ Konfig
def _store_wert(name):
    """Fallback auf den gespeicherten Store, wenn die Umgebung nichts sagt —
    dasselbe Muster wie sync_refs._frigate() (carlsmith-Lehre .132: ein
    docker-exec-Diagnoselauf hat die Dienst-Umgebung NICHT und soll trotzdem
    laufen). Fehlt der Store, ist das kein Fehler, sondern 'nicht gesetzt'."""
    data = os.environ.get("VERIFY_DATA_DIR") or "/data"
    try:
        with open(os.path.join(data, "config", "config.json")) as f:
            return str(json.load(f).get(name) or "")
    except Exception:
        return ""


def zugang():
    """-> (benutzer, passwort). Leere Strings = kein Login (Default)."""
    u = (os.environ.get("FRIGATE_USER") or "").strip() or _store_wert("frigate_user")
    p = os.environ.get("FRIGATE_PASSWORD") or _store_wert("frigate_password")
    return u.strip(), str(p or "")


def aktiv():
    """Ist ein Login konfiguriert? Beides muss da sein — ein halber Zugang ist
    kein Zugang, und ein Login-Versuch mit leerem Passwort waere ein stiller
    Verhaltensunterschied gegenueber 'nicht konfiguriert'."""
    u, p = zugang()
    return bool(u and p)


def tls_pruefen():
    """Zertifikat pruefen? Default AN. Nur ein ausdrueckliches Aus schaltet ab
    (Frigates 8971 ist ab Werk selbstsigniert)."""
    w = os.environ.get("FRIGATE_TLS_VERIFY")
    if w is None or w == "":
        w = _store_wert("frigate_tls_verify")
    if w == "":
        return True
    return str(w).strip().lower() not in ("0", "false", "nein", "off", "aus")


def kennung():
    """Die ehrliche Client-Kennung. Version aus dem bestehenden Mechanismus
    (SUSLIK_VERSION setzt verifyd beim Start aus der VERSION-Datei), nie ein
    Literal — sonst zeigte die Kennung nach jedem Release auf eine Version,
    die niemand laeuft."""
    return f"suslik/{os.environ.get('SUSLIK_VERSION') or 'dev'}"


def _ssl_kontext():
    """None = urllibs Default-Verhalten, BYTE-GLEICH zu vorher. Ein eigener
    Kontext entsteht NUR, wenn die Pruefung ausdruecklich abgeschaltet ist."""
    if tls_pruefen():
        return None
    k = ssl.create_default_context()
    k.check_hostname = False
    k.verify_mode = ssl.CERT_NONE
    return k


def _urlopen(req, timeout):
    """Der eigentliche Ruf — und ein Stueck Regressions-Vertrag: solange die
    Zertifikats-Pruefung an ist (Default), wird `context` GAR NICHT uebergeben.
    Der Aufruf ist dann Argument fuer Argument derselbe wie vor 5e.

    Das ist nicht Kosmetik. Ein durchgereichtes `context=None` verhaelt sich
    zwar gleich, ist aber ein zusaetzliches Schluesselwort-Argument — und daran
    zerbricht jede Stelle, die urlopen ERSETZT. Der Gate-Lauf hat genau das
    gefangen (TypeError: fake_urlopen() got an unexpected keyword argument
    'context' in der .288-Stufe); der Fix gehoert hierher, nicht in die Stufe.
    Geprueft: der urlopen-Riegel in tools/koerper_fixpunkt.py war schon robust
    (*a, **kw), und tools/harnisch_r3.py fakt ein injiziertes Modul-Objekt der
    MELDEwege, nicht diesen Weg — betroffen war nur die eine Gate-Stufe.

    MESSPUNKT der Antwortzeit (.407): hier, und nur hier. JEDER Zug dieses
    Moduls geht durch diese Funktion — auch der Login und die eine
    Wiederholung nach 401, beide echte Zuege, beide einzeln gezaehlt. Der
    Messcode liegt UM den Ruf herum, nie darin: der Aufruf selbst bleibt
    Argument fuer Argument derselbe (Regressions-Vertrag oben), und ein
    Fehlversuch wird mit seiner gewarteten Zeit verbucht, bevor die Ausnahme
    weiterfliegt (finally)."""
    k = _ssl_kontext()
    _t0 = time.monotonic()
    try:
        if k is None:
            return urllib.request.urlopen(req, timeout=timeout)
        return urllib.request.urlopen(req, timeout=timeout, context=k)
    finally:
        _zeit_merken(getattr(req, "full_url", ""), time.monotonic() - _t0)


# ------------------------------------------------------------------ Login
def _basis_von(url):
    t = urllib.parse.urlsplit(url)
    return f"{t.scheme}://{t.netloc}" if t.scheme and t.netloc else ""


def _cookie_aus(antwort):
    """frigate_token aus den Set-Cookie-Koepfen holen. get_all, nicht get:
    Frigate darf mehrere Cookies setzen und das Token muss nicht das erste
    sein."""
    for roh in (antwort.headers.get_all("Set-Cookie") or []):
        try:
            c = http.cookies.SimpleCookie()
            c.load(roh)
        except Exception:
            continue
        if COOKIE_NAME in c:
            return c[COOKIE_NAME].value
    return ""


def _login(basis, timeout=20):
    """Anmelden und das Token merken. -> Token (nicht leer) oder Ausnahme.
    Laeuft NICHT ueber oeffnen() (das wuerde sich selbst aufrufen), traegt aber
    dieselbe Kennung und denselben SSL-Kontext."""
    benutzer, passwort = zugang()
    if not (benutzer and passwort):
        raise RuntimeError("Frigate login requested without credentials")
    req = urllib.request.Request(
        basis + LOGIN_PFAD,
        data=json.dumps({"user": benutzer, "password": passwort}).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": kennung()},
        method="POST")
    with _urlopen(req, timeout) as r:
        tok = _cookie_aus(r)
        r.read(1024)          # Body leeren, damit die Verbindung sauber endet
    if not tok:
        # Laut werden statt weiterlaufen: ohne Cookie waere JEDER Folge-Request
        # ein 401 und die Ursache stuende nirgends.
        raise RuntimeError(
            f"Frigate accepted the login but sent no {COOKIE_NAME} cookie "
            f"— check whether this really is a Frigate 0.14+ auth port")
    with _sperre:
        _token["wert"], _token["basis"] = tok, basis
    return tok


def _token_fuer(basis, erneuern=False, timeout=20):
    with _sperre:
        gut = _token["wert"] and _token["basis"] == basis
        vorhanden = _token["wert"] if gut else ""
    if vorhanden and not erneuern:
        return vorhanden
    return _login(basis, timeout=timeout)


# ------------------------------------------------------------------ Griff
def _bauen(ziel, data, headers, method):
    if isinstance(ziel, urllib.request.Request):
        req = ziel
    else:
        req = urllib.request.Request(ziel, data=data, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    req.add_header("User-Agent", kennung())      # add_header ersetzt gleichnamige
    return req


# ------------------------------------------------------------- Speicherweg
# Die drei Schluessel, die dieses Thema besitzt. EINE Quelle fuer den
# Speicherweg, die Seiten-Sektion und den Ausschluss aus der generischen
# Tabelle — nie ein zweites verstreutes Literal (CLAUDE.md, Deckungs-Regel).
SEKTIONS_SCHLUESSEL = ("frigate_user", "frigate_password", "frigate_tls_verify")
GEHEIME_SCHLUESSEL = ("frigate_password",)


def werte_uebernehmen(d, alt):
    """Formularwerte des Konfigurationsblatts ueber den gespeicherten Stand
    legen -> (ok, block|fehlertext). Reine Rechnung, kein IO — der Dienst
    schreibt (Muster core/melden.notif_speichern, Injektion pur).

    Secret-Semantik wie bei den Meldekanaelen: ein LEERES Passwortfeld
    BEHAELT den gespeicherten Wert, es loescht ihn nicht. Ohne diese Regel
    loeschte jeder Save der Seite das Passwort, denn die Seite rendert es
    nie im Klartext und postet deshalb immer leer.

    Loeschen geht ueber den leeren BENUTZER: ohne Benutzer gibt es keinen
    Login mehr (aktiv() verlangt beides), und das Passwort wird dann
    mitgeloescht statt als Waise liegenzubleiben."""
    neu = dict(alt or {})
    if "frigate_user" in d:
        neu["frigate_user"] = str(d.get("frigate_user") or "").strip()
    if "frigate_password" in d:
        p = str(d.get("frigate_password") or "")
        if p:                                  # leer = behalten
            neu["frigate_password"] = p
    if "frigate_tls_verify" in d:
        neu["frigate_tls_verify"] = str(d.get("frigate_tls_verify")).strip().lower() \
            in ("1", "true", "ja", "on")
    if not neu.get("frigate_user"):
        neu["frigate_user"] = ""
        neu["frigate_password"] = ""           # keine Passwort-Waise
    neu.setdefault("frigate_password", "")
    neu.setdefault("frigate_tls_verify", True)
    return True, neu


def ffmpeg_kopf(url, timeout=20):
    """Die EINE deklarierte Zweitstelle: der VOD-Weg (core/frames._vod_holen)
    reicht die Frigate-URL an das LOKALE ffmpeg weiter, das seinen HTTP-Zug
    selbst macht — dieses Modul kann ihn nicht wickeln. Damit auch dieser Zug
    Kennung und Cookie traegt, liefert die Funktion die passenden
    ffmpeg-Argumente. -> Liste, die VOR '-i url' eingefuegt wird.

    Ohne Zugang ist es nur die Kennung (derselbe Vertrag wie oeffnen: eine
    Installation ohne Login sieht als einzige Aenderung den User-Agent).
    Scheitert die Anmeldung, tragen wir wenigstens die Kennung ein und lassen
    ffmpeg an Frigates 401 scheitern — der Aufrufer faellt dann LAUT auf den
    clip.mp4-Weg zurueck, der ueber oeffnen() laeuft und den echten Fehler
    zeigt. TLS: ffmpeg prueft Server-Zertifikate ohne 'tls_verify 1' ohnehin
    nicht, ein selbstsigniertes 8971 stoert es also nicht."""
    argumente = ["-user_agent", kennung()]
    if not aktiv():
        return argumente
    basis = _basis_von(url)
    if not basis or basis != frigate_basis():
        # .354: NUR an das konfigurierte Frigate. Der VOD-Weg baut seine URL
        # ohnehin daraus, aber der Live-Waechter nimmt eine vom NUTZER
        # eingetragene Adresse (meist dessen eigene Kamera) — ohne diese
        # Fessel gingen Benutzername und Passwort per Login-POST an genau
        # den fremden Host, den jemand in seinen Waechter schreibt. Gleiche
        # Fehlerklasse wie B1 (geloeschte Zugangsdaten an fremden Host).
        return argumente
    try:
        tok = _token_fuer(basis, timeout=timeout)
    except Exception:
        return argumente
    return argumente + ["-headers", f"Cookie: {COOKIE_NAME}={tok}\r\n"]


def frigate_basis():
    """scheme://host:port des KONFIGURIERTEN Frigate ('' = nicht gesetzt).
    Eine Quelle fuer alle, die pruefen muessen, ob eine Adresse ueberhaupt
    unser Frigate ist (ffmpeg_kopf, Live-Waechter)."""
    u = (os.environ.get("FRIGATE_URL") or "").strip() or _store_wert("frigate_url")
    return _basis_von(u.strip())


def oeffnen(ziel, data=None, timeout=None, headers=None, method=None):
    """DER Frigate-Griff. Signatur und Rueckgabe wie urllib.request.urlopen:
    das echte Antwort-Objekt, als Kontextmanager verwendbar, mit .read/.status/
    .headers und dem rohen Socket darunter (der Clip-Weg in core/frames.py
    greift ihn fuer sein Zwischen-Byte-Fenster — deshalb wird hier NICHTS
    umgepackt).

    ziel: URL-String ODER ein fertiges urllib.request.Request-Objekt (der
    multipart-Upload in sync_refs baut seines selbst).

    Ohne konfigurierten Zugang genau ein Unterschied zu vorher: der
    User-Agent. Mit Zugang: Cookie dran, bei 401 genau ein Re-Login und genau
    eine Wiederholung."""
    req = _bauen(ziel, data, headers, method)
    if not aktiv():
        return _urlopen(req, timeout)
    basis = _basis_von(req.full_url)
    if not basis:
        return _urlopen(req, timeout)
    req.add_header("Cookie", f"{COOKIE_NAME}={_token_fuer(basis, timeout=timeout or 20)}")
    try:
        return _urlopen(req, timeout)
    except urllib.error.HTTPError as e:
        if e.code != 401:
            raise
        # EIN Re-Login, EINE Wiederholung. Was danach kommt, geht ehrlich
        # nach oben — ein falsches Passwort ist keine Sache, die sich durch
        # Wiederholen loest.
        try:
            e.close()
        except Exception:
            pass
        req.add_header("Cookie",
                       f"{COOKIE_NAME}={_token_fuer(basis, erneuern=True, timeout=timeout or 20)}")
        return _urlopen(req, timeout)
