"""core/frames — Zug 1 + 2 + 4 + 5 des Frame-Verteilers (konzept_frames.md v2).

TEIL A (Z1/Z2, §3.1) — EINE Clip-Beschaffung fuer alle Abnehmer:
cache_pfad() loest das Ablage-Verzeichnis in fester Rangfolge,
clip_holen() laedt atomar (.part) und setzt den PIN im selben Zug (kein
ungeschuetztes Fenster zwischen Download und Abnehmer-Start —
Widerleger-MUSS 4), pin()/frei() fuehren einen REFCOUNT je Halter
(<eid>.<pid>.<tid>.pin): zwei unabhaengige Halter (Worker-Analyse +
Dienst-Thread) koennen sich nie gegenseitig die Datei unter dem Size-Cap
wegraeumen lassen. gepinnt() ist die Auskunft fuer cleanup_cache.

TEIL B (Z4, §3.2) — DER VERTEILER: lauf(vid, abnehmer) faehrt EINEN
FrameIter und bedient jeden registrierten Abnehmer nach dessen
deklariertem Vertrag (Abnehmer, sechs Pflichtfelder). Bei EINEM Abnehmer
ist die Frame-Index-Menge dieselbe wie beim frueheren Einzellauf —
Neutralitaet per Konstruktion, nicht per Messung: der Verteiler baut den
Iterator mit dem fps_sample DES Abnehmers und waehlt selbst nie aus.

Z5 (§4/Z5) macht den ZWEITEN Abnehmer moeglich — den Koerper-Strang, der
seine Samples HAELT (bedarf='puffer') und seine Zeitachse gegen den
Frigate-Snapshot eicht (zeitbezug='wanduhr'). Damit faellt der
Doppel-Decode. Dazu drei Dinge, die Z4 offen liess: die Lauf-Wache
(Zeitwache Stufe b, killt die ffmpeg-Pipe), die Puffer-Wache (ein
haltender Abnehmer darf nie einen wiederverwendeten Puffer bekommen) und
LaufInfo.soll_samples (Vorab-Groesse fuer das RAM-Gate des Halters).

Dieses Modul liefert Dateien und Frames, nie Urteile."""
import os
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request


def cache_dir(data_dir=None):
    """Rangfolge (v2 §3.1, Widerleger-MUSS 5 — SCRATCH_DIR ist im
    DIENST-Prozess nicht gesetzt): explizites data_dir -> VERIFY_DATA_DIR
    -> SCRATCH_DIR (Worker-Umfeld) -> tempdir-Fallback.

    Der Ordnername ist <data_dir>/clips und NICHT frei waehlbar (v2 §3.1
    woertlich): genau dorthin zeigt SCRATCH_DIR der Kinder
    (verifyd.py:571/:621/:2629), dort liest make_browser_copy den Clip
    (verifyd.py:3768) und nur diesen Ordner raeumen cleanup_cache/
    clip_cache_bytes (:3823/:3838). Ein zweiter Ordner waere ein Cache,
    den niemand raeumt und aus dem niemand sonst liest."""
    for d in (os.path.join(data_dir, "clips") if data_dir else None,
              os.environ.get("VERIFY_DATA_DIR") and os.path.join(
                  os.environ["VERIFY_DATA_DIR"], "clips"),
              os.environ.get("SCRATCH_DIR")):
        if d:
            os.makedirs(d, exist_ok=True)
            return d
    d = os.path.join(tempfile.gettempdir(), "suslik-scratch")
    os.makedirs(d, exist_ok=True)
    return d


def cache_pfad(eid, data_dir=None):
    return os.path.join(cache_dir(data_dir),
                        str(eid).replace("/", "_") + ".mp4")


def _pin_pfad(pfad):
    return f"{pfad}.{os.getpid()}.{threading.get_native_id()}.pin"


def pin(eid, data_dir=None):
    """Refcount-Marke DIESES Halters setzen (idempotent je Halter)."""
    p = _pin_pfad(cache_pfad(eid, data_dir))
    open(p, "a").close()
    return p


def frei(eid, data_dir=None):
    """Marke DIESES Halters loesen; fremde Marken bleiben unberuehrt."""
    try:
        os.remove(_pin_pfad(cache_pfad(eid, data_dir)))
    except FileNotFoundError:
        pass


PIN_ABGESTANDEN_S = 1800     # v2 §3.1: aelter = Waise (aufgegebener Thread/
#                              Prozess) — zaehlt nicht mehr und wird geraeumt


def gepinnt(pfad):
    """Auskunft fuer cleanup_cache: haelt IRGENDWER diese Clip-Datei?
    (Glob ueber <pfad>.*.pin.) Abgestandene Pins (> PIN_ABGESTANDEN_S)
    zaehlen nicht und werden im selben Zug geraeumt — eine Waise darf
    den Size-Cap nie dauerhaft blocken (Widerleger-Rest aus Z2)."""
    import glob
    import time
    lebt = False
    for p in glob.glob(f"{pfad}.*.pin"):
        try:
            if time.time() - os.path.getmtime(p) > PIN_ABGESTANDEN_S:
                os.remove(p)
            else:
                lebt = True
        except OSError:
            lebt = True          # im Zweifel schuetzen, nie wegraeumen
    return lebt


# ================================================= Clip-Debug ([clipdbg]) ==
# .287 (User-Auftrag 18.08.; Frigate-Haenger-Klasse bewiesen, Task #11,
# verify_data/messungen/frigate_haenger_20260818_191803): Frigates 40er-API-
# Threadpool wird von akkumulierenden Clip-Leser-Threads erschoepft — beim
# naechsten Vorfall muss die suslik-Seite JEDER Clip-Interaktion lueckenlos
# belegt sein. Geschaltet wird ueber den EINEN bestehenden Schalter
# cfg['debug'] (verifyd.debug(), Whitelist-Key) — kein zweiter Schalter:
#   - DIENST-Prozess: verifyd haengt seine Senke in CLIP_DBG ein; sie prueft
#     cfg['debug'] je Zeile -> Umschalten wirkt sofort.
#   - WORKER-Prozess: der Dienst reicht den Schalter als Job-Feld 'clip_dbg'
#     durch (WorkerProzess.job, setdefault wie rss_max_mb); worker.py
#     armiert CLIP_DBG/CLIP_QUELLE/CLIP_ALTER_MIN je Job, die Zeilen landen
#     im Log DIESES Jobs (analyze.log/ernte.log).
#   - analyze-SUBPROZESS (Legacy-Weg ohne Worker): ENV SUSLIK_CLIP_DBG/
#     SUSLIK_CLIP_QUELLE/SUSLIK_CLIP_ALTER_MIN, gesetzt von run_analyze.
# JE EREIGNIS genau EINE kompakte Zeile (Beginn / Ende / Cache-Treffer),
# nie ein Roh-Dump. Nur Telemetrie — nie Verhalten.

CLIP_DBG = ((lambda z: print(z, flush=True))
            if os.environ.get("SUSLIK_CLIP_DBG") else None)  # Senke | None=aus
CLIP_QUELLE = os.environ.get("SUSLIK_CLIP_QUELLE") or None   # ernte/vorlader/
#                                                              nachhol/live
CLIP_ALTER_MIN = os.environ.get("SUSLIK_CLIP_ALTER_MIN") or None
# .290 Erzeugungs-Modus-Defaults DIESES Prozesses/Jobs (gleiches Muster wie
# CLIP_QUELLE, aber VERHALTEN statt Telemetrie): der Analyze-Weg ruft
# clip_holen ohne eigene Parameter — worker.py armiert je Job aus den
# Job-Feldern, der Legacy-Subprozess aus diesen ENV-Variablen. Explizite
# clip_holen-Argumente (Ernte/Vorlader) gewinnen immer.
CLIP_ERZEUGUNG = bool(os.environ.get("SUSLIK_CLIP_ERZEUGUNG"))
CLIP_ERZEUGUNG_DECKEL_S = (
    float(os.environ["SUSLIK_CLIP_ERZEUGUNG_DECKEL_S"])
    if os.environ.get("SUSLIK_CLIP_ERZEUGUNG_DECKEL_S") else None)
# .292 VOD-Weg-Default (Config-Key clip_vod, Muster wie CLIP_ERZEUGUNG):
# True = Alt-Event-Clips zuerst ueber Frigates /vod/event/{id}/master.m3u8
# beschaffen (nginx-vod liefert die Segmente direkt, der bewiesen kranke
# Python-Erzeugungspfad in Frigate — ungelesene ffmpeg-stderr-Pipe, je Zug
# +1 Thread/+1 ffmpeg-Leiche, Discussion frigate#24029 — wird gar nicht
# betreten). Das Zusammenfuegen macht das LOKALE ffmpeg als reines
# Stream-Copy (bitgleiche Pakete, Pixelpfad-Invariante unberuehrt).
CLIP_VOD = os.environ.get("SUSLIK_CLIP_VOD", "1") != "0"


def clip_dbg(msg):
    """[clipdbg]-Zeile an die Prozess-Senke — das EINE Praefix an der EINEN
    Stelle. Eine kaputte Senke darf nie die Clip-Beschaffung reissen."""
    s = CLIP_DBG
    if s is None:
        return
    try:
        s(f"[clipdbg] {msg}")
    except Exception:
        pass


def _fehler_art(e, geladen):
    """Fehlerklasse fuer die [clipdbg]-Endzeile: 'http <code>' | 'timeout'
    (nie ein Byte angekommen) | 'stall' (Strom riss nach `geladen` Bytes ab —
    der .262-Socket-Timeout je Operation hat zugeschlagen) | 'error';
    .288: dazu die zwei Erzeugungs-Abbruch-Klassen (frigate_stoerung/
    erzeugung_deckel) mit ihrem Klassennamen."""
    if isinstance(e, ClipErzeugungAbbruch):
        return e.klasse
    if isinstance(e, urllib.error.HTTPError):
        return f"http {e.code}"
    grund = getattr(e, "reason", e)   # URLError verpackt den Socket-Fehler
    if isinstance(grund, TimeoutError) or "timed out" in str(grund).lower():
        return "stall" if geladen else "timeout"
    return "error"


# ==================================== Erzeugungs-Modus (.288, Task #11) ====
# GEMESSENE Grundlage (prototyp/frigate_leak_probe.py Serie E, 18.08. +
# Header-Messung .288): fordert man den Clip eines ALTEN Events an, muss
# Frigate ihn erst aus Aufnahme-Segmenten ERZEUGEN — die HTTP-Header kommen
# in <1 s (chunked), dann fliesst >30 s lang KEIN Byte. Unser 30-s-Socket-
# Timeout brach genau da ab, und JEDER solche Abbruch laesst drueben
# DAUERHAFT 1 API-Thread (anon_pipe_read) + 1 ffmpeg zurueck (Serie E:
# 19 Zuege = +19/+19, Ruhe raeumt nichts) — bis Frigates 40er-Threadpool
# erschoepft ist (die Totalhaenger 17./18.08.). Fertige Clips liefern
# dagegen in <1,2 s und sind in ALLEN Abbruch-Formen leakfrei (Serien A-D).
# Der Erzeugungs-Modus ersetzt deshalb NUR den Abbruch VOR dem ersten Byte
# durch eine Warte-Schleife: je 30-s-Stall EINE billige /api/version-Probe
# (6 s) — antwortet Frigate, ist es BESCHAEFTIGT (weiter warten, bis zum
# konfigurierten Ober-Deckel); antwortet es nicht, ist die Verbindung
# wirklich tot (Abbruch 'frigate_stoerung'). SOBALD Bytes fliessen, gilt
# unveraendert die strenge Zwischen-Byte-Stall-Logik (gemessen sauber).

class ClipErzeugungAbbruch(RuntimeError):
    """Abbruch der Clip-Beschaffung im Erzeugungs-Modus. klasse:
    'frigate_stoerung' (Version-Probe tot — echte tote Verbindung) |
    'erzeugung_deckel' (Ober-Deckel erreicht, Frigate antwortete zwar,
    lieferte aber nie ein Byte). Der Ernte-Pfad bucht solche Events NICHT
    als 'fehler' — sie bleiben ungebucht und ein spaeterer Lauf holt sie."""

    def __init__(self, klasse, msg):
        super().__init__(msg)
        self.klasse = klasse


class ErzeugungsWarte:
    """Warte-Politik der Clip-Erzeugung — reine Entscheidungslogik, Uhr und
    Probe injizierbar (Kontrakt wie core/schoner: kein Netz im Test).
    entscheide() faellt nach JEDEM Null-Byte-Stall: erst der Deckel (die
    absolute Grenze), dann die Probe (lebt Frigate ueberhaupt noch?)."""

    def __init__(self, deckel_s, probe, uhr=None):
        self.deckel_s = float(deckel_s)
        self.probe = probe                    # callable -> bool (True=lebt)
        self.uhr = uhr or time.monotonic
        self.start = self.uhr()

    def gewartet_s(self):
        return self.uhr() - self.start

    def entscheide(self):
        """'warten' | raise ClipErzeugungAbbruch(erzeugung_deckel/
        frigate_stoerung)."""
        w = self.gewartet_s()
        if w >= self.deckel_s:
            raise ClipErzeugungAbbruch(
                "erzeugung_deckel",
                f"clip generation exceeded the {self.deckel_s:.0f}s cap "
                f"({w:.0f}s without a first byte) — aborted, the event "
                "stays unbooked for a later run")
        if not self.probe():
            raise ClipErzeugungAbbruch(
                "frigate_stoerung",
                f"no clip bytes after {w:.0f}s AND the /api/version probe "
                "does not answer — Frigate itself is unreachable")
        return "warten"


def _version_probe(basis):
    """Die billige Lebt-Frigate-Probe des Erzeugungs-Modus: GET /api/version
    mit kurzem Timeout auf einer EIGENEN Verbindung (die wartende Clip-
    Verbindung bleibt unberuehrt). Ein HTTP-Fehlerstatus zaehlt als LEBT —
    dieselbe Regel wie im Schoner (ein 4xx/5xx ist eine Antwort)."""
    def probe():
        try:
            with urllib.request.urlopen(f"{basis}/api/version", timeout=6) as r:
                r.read(64)
            return True
        except urllib.error.HTTPError:
            return True
        except Exception:
            return False
    return probe


def _ist_stall(e):
    """War diese Lese-Ausnahme ein Socket-Timeout (Stall)? Waehrend des
    BODY-Lesens wirft Python den rohen TimeoutError (socket.timeout),
    urllib verpackt nur die Verbindungsphase in URLError."""
    grund = getattr(e, "reason", e)
    return (isinstance(grund, TimeoutError)
            or "timed out" in str(grund).lower())


def _vod_holen(eid, teil, basis, deckel_s):
    """Alt-Event-Clip ueber Frigates VOD-Weg beschaffen (.292, Machbarkeit
    bewiesen in prototyp/frigate_vod_probe.py am ungefixten 0.18.0-beta3):
    /vod/event/{id}/master.m3u8 beantwortet das nginx-vod-Modul direkt aus
    den Segment-Dateien — Frigates kranker Python-Erzeugungspfad (frigate
    #24029) wird nicht betreten, serverseitig entsteht weder ffmpeg noch
    Pool-Thread. Das LOKALE ffmpeg fuegt per Stream-Copy zusammen (-c copy
    = bitgleiche Pakete). stderr geht bewusst nach DEVNULL — die Warnflut
    der Audio-degenerierten Segmente ist genau das, was drueben die
    ungelesene Pipe fuellte; wir bauen dieselbe Falle nicht nach. Ein
    Fehlschlag (aelteres Frigate ohne vod/event -> 404-Probe, ffmpeg-Fehler,
    Deckel) ist LAUT und liefert False — der Aufrufer faellt auf den
    gehaerteten clip.mp4-Weg zurueck."""
    url = f"{basis}/vod/event/{eid}/master.m3u8"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            if r.status != 200:
                clip_dbg(f"{eid}: vod probe HTTP {r.status} — falling back")
                return False
    except Exception as e:
        clip_dbg(f"{eid}: vod probe failed ({type(e).__name__}: "
                 f"{str(e)[:80]}) — falling back")
        return False
    t0 = time.monotonic()
    try:
        lauf = subprocess.run(
            ["ffmpeg", "-hide_banner", "-y", "-i", url,
             "-c", "copy", "-f", "mp4", teil],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=deckel_s)
    except subprocess.TimeoutExpired:
        clip_dbg(f"{eid}: vod remux hit cap ({deckel_s:.0f}s) — falling back")
        return False
    except Exception as e:
        clip_dbg(f"{eid}: vod remux failed ({type(e).__name__}: "
                 f"{str(e)[:80]}) — falling back")
        return False
    if (lauf.returncode != 0 or not os.path.exists(teil)
            or not os.path.getsize(teil)):
        clip_dbg(f"{eid}: vod remux exit {lauf.returncode} — falling back")
        return False
    clip_dbg(f"{eid}: vod fetch ok s={time.monotonic() - t0:.1f} "
             f"bytes={os.path.getsize(teil)} (local remux, no server-side "
             "clip generation)")
    return True


def clip_holen(eid, data_dir=None, frigate_url=None, timeout=30,
               quelle=None, alter_min=None,
               erzeugung=None, erzeugung_deckel_s=None, warte=None):
    """Clip beschaffen: Cache-Treffer ODER atomarer Download (.part wie
    analyze.py — ein abgerissener Download darf nie als halbes Video
    durchgehen). Der PIN dieses Halters wird IM SELBEN ZUG gesetzt
    (Download UND Cache-Treffer). Rueckgabe: Pfad. Aufrufer ruft frei().
    Fehler raeumen .part-Waisen und den eigenen Pin.
    .262 Hebel 1 (gemessen am 300er-Lauf 17.08.: DREI Events liefen je in
    den prozessweiten 120-s-Socket-Default und frassen 6 der ersten 15 min;
    gesunde LAN-Downloads liefern in <1 s erste Bytes, gemessen 0.4-0.6 s
    je Clip): timeout wirkt je Socket-Operation — ein STALL (timeout s ohne
    Bytes) bricht ab, ein langsamer, aber FLIESSENDER Download nie. Der
    .part-Name traegt PID+TID (endet auf .part — cleanup_cache raeumt
    Waisen weiter): zwei parallele Beschaffer desselben Clips (Vorlader +
    Worker, Hebel 2) schrieben sonst in DIESELBE Teil-Datei.
    quelle/alter_min (.287, [clipdbg]): Herkunft (ernte/vorlader/nachhol/
    live) und Event-Alter in Minuten fuer die Debug-Zeilen — reine
    Telemetrie, nie Verhalten; ungesetzt greifen die Prozess-Defaults
    CLIP_QUELLE/CLIP_ALTER_MIN (Block oben).
    erzeugung (.288, Task #11 — Block oben): True = Alt-Event, Frigate muss
    den Clip erst ERZEUGEN. Dann ersetzt die Warte-Schleife den harten
    Abbruch, SOLANGE noch kein Byte floss: je Stall eine /api/version-Probe,
    weiter warten bis erzeugung_deckel_s (PFLICHT bei erzeugung=True — der
    Wert kommt aus der Dienst-Config, hier gibt es bewusst keinen zweiten
    Default). Ab dem ersten Byte gilt unveraendert die strenge Stall-Logik.
    .290: erzeugung=None (Default) uebernimmt die Prozess-/Job-Defaults
    CLIP_ERZEUGUNG/CLIP_ERZEUGUNG_DECKEL_S (Analyze-Weg: worker.py armiert
    je Job, Legacy-Subprozess via ENV) — explizite Argumente gewinnen.
    warte: injizierbare ErzeugungsWarte (Tests); None = echte Uhr + Probe."""
    if erzeugung is None:
        erzeugung = CLIP_ERZEUGUNG
    if erzeugung_deckel_s is None:
        erzeugung_deckel_s = CLIP_ERZEUGUNG_DECKEL_S
    erzeugung = bool(erzeugung)
    pfad = cache_pfad(eid, data_dir)
    pin(eid, data_dir)
    teil = f"{pfad}.{os.getpid()}.{threading.get_native_id()}.part"
    q = quelle or CLIP_QUELLE or "?"
    alter = alter_min if alter_min is not None else CLIP_ALTER_MIN
    t0 = time.monotonic()
    geladen = 0
    try:
        if not os.path.exists(pfad):
            clip_dbg(f"{eid}: GET clip.mp4 start src={q} "
                     f"age_min={alter if alter is not None else '?'}"
                     + (" erzeugung=1" if erzeugung else ""))
            basis = (frigate_url
                     or os.environ.get("FRIGATE_URL", "")).rstrip("/")
            if erzeugung and warte is None:
                if erzeugung_deckel_s is None:
                    raise ValueError(
                        "clip_holen(erzeugung=True) braucht erzeugung_"
                        "deckel_s aus der Config — kein Modul-Default")
                warte = ErzeugungsWarte(erzeugung_deckel_s,
                                        _version_probe(basis))
            # .292 VOD-Weg ZUERST — fuer JEDEN Clip-Zug (User-Auftrag 19.08.:
            # „jedes Mal, wenn wir ein Event holen", Lernlauf/Live/Nachhol/
            # Meldung gleichermassen; kranke Segment-Fenster koennen auch
            # frische Events treffen, z. B. direkt nach Frigate-Neustarts).
            # Gelingt der lokale Remux, ist der Zug hier fertig — Frigates
            # kranker Erzeugungspfad wird nie betreten. Jeder Fehlschlag ist
            # laut (clip_dbg in _vod_holen) und faellt auf den gehaerteten
            # clip.mp4-Weg darunter zurueck. Deckel: im Erzeugungs-Fall der
            # Config-Deckel, sonst das normale Socket-Fenster (VOD liefert
            # frisch in <1 s, gemessen).
            if CLIP_VOD and _vod_holen(
                    eid, teil, basis,
                    warte.deckel_s if (erzeugung and warte is not None)
                    else float(timeout)):
                os.replace(teil, pfad)
                return pfad
            # .289 (Haertungstest-Fang am Frisch-Event): Frigate schickt bei
            # der Erzeugung auch die RESPONSE-HEADER erst am Ende — der
            # strenge Verbindungs-Timeout brach dann VOR der Warte-Schleife
            # ab (exakt der 1:1-Leak-Trigger aus Serie E). Im Erzeugungs-
            # Modus wartet der Aufbau deshalb bis zum Deckel; direkt nach
            # den Headern stellt settimeout() das strenge Fenster zurueck.
            _aufbau_to = (warte.deckel_s if (erzeugung and warte is not None)
                          else timeout)
            with urllib.request.urlopen(f"{basis}/api/events/{eid}/clip.mp4",
                                        timeout=_aufbau_to) as r, \
                 open(teil, "wb") as f:
                if erzeugung:
                    # .290: Griff gehaertet — ein Antwort-Objekt OHNE fp
                    # (Test-Fake, exotischer Opener) liess den nackten
                    # r.fp-Zugriff mit AttributeError reissen statt laut
                    # zu degradieren (Gate-Fang beim Zusammenfuehren).
                    try:
                        _sock = r.fp.raw._sock
                    except AttributeError:
                        _sock = None
                    if _sock is not None:
                        _sock.settimeout(timeout)
                    else:
                        clip_dbg(f"{eid}: WARN kein Socket-Zugriff nach "
                                 f"Headern — Zwischen-Byte-Fenster bleibt "
                                 f"auf {_aufbau_to:.0f}s")
                # Byte-zaehlende 64k-Schleife (ehem. shutil.copyfileobj):
                # die [clipdbg]-Endzeile braucht bytes= — und nur der Zaehler
                # trennt 'stall' (Bytes kamen, dann riss der Strom) von
                # 'timeout' (nie ein Byte). read1 statt read, weil read(n)
                # im BufferedReader BLOCKIEREND auf volle n Bytes wartet:
                # ein Stall mitten im 64k-Chunk saehe sonst wie bytes=0 aus
                # (im Smoke-Test nachgestellt). read1 liefert, was der
                # Socket hergibt — gleiche Daten, gleicher Timeout je
                # Socket-Operation.
                leser = getattr(r, "read1", r.read)
                while True:
                    try:
                        stueck = leser(65536)
                    except Exception as le:
                        # .288 Erzeugungs-Warten: NUR solange kein Byte
                        # floss und NUR fuer echte Stalls — deckt den
                        # chunked-Fall (Header frueh, Bytes spaet); den
                        # gemessen haeufigeren Header-erst-am-Ende-Fall
                        # deckt seit .289 der Aufbau-Timeout oben. Die
                        # Verbindung bleibt OFFEN (ein Neuaufbau je Runde
                        # waere selbst der 1:1-Leak-Trigger aus Serie E).
                        # .291 (Direkttest-Fang, nginx-Beleg 31,9 s): bei der
                        # Erzeugung STREAMT Frigate haeppchenweise und die
                        # >30-s-Stille kommt am ENDE (MP4-Finalisierung) —
                        # gemessen 29 MB geflossen, Abbruch auf der
                        # Ziellinie. Im Erzeugungs-Modus traegt die Probe-
                        # Warte deshalb JEDEN Stall (nicht nur vor dem
                        # ersten Byte); ohne erzeugung bleibt der Stall
                        # nach Bytes die alte strenge Klasse.
                        if (warte is not None
                                and erzeugung and _ist_stall(le)):
                            clip_dbg(f"{eid}: wartet_auf_erzeugung src={q} "
                                     f"s={time.monotonic() - t0:.0f} "
                                     f"bytes={geladen} "
                                     f"(deckel {warte.deckel_s:.0f}s)")
                            warte.entscheide()   # raise bei tot/deckel
                            clip_dbg(f"{eid}: probe_ok src={q} — Frigate "
                                     "answers, still generating the clip")
                            continue
                        raise
                    if not stueck:
                        break
                    f.write(stueck)
                    geladen += len(stueck)
            os.replace(teil, pfad)
            clip_dbg(f"{eid}: GET clip.mp4 ok src={q} "
                     f"s={time.monotonic() - t0:.1f} bytes={geladen}")
        else:
            clip_dbg(f"{eid}: clip cache hit src={q} "
                     f"bytes={os.path.getsize(pfad)} — no Frigate request")
        return pfad
    except Exception as e:
        clip_dbg(f"{eid}: GET clip.mp4 {_fehler_art(e, geladen)} src={q} "
                 f"s={time.monotonic() - t0:.1f} bytes={geladen} "
                 f"({type(e).__name__}: {str(e)[:120]})")
        try:
            os.unlink(teil)
        except FileNotFoundError:
            pass
        frei(eid, data_dir)
        raise


# ======================================================= B: Verteiler ======
# Zug 4 (konzept_frames.md v2 §3.2 "Verteiler", §4/Z4, §9-Entscheide 2/3/6,
# §10-Leitplanke). Der Verteiler aendert nur, WOHER Frames kommen — nie, WIE
# gerechnet wird: er waehlt keine Frames aus (das tut die Frame-Quelle mit dem
# fps_sample des Abnehmers), er urteilt nicht, er setzt keine Modell-Parameter.
#
# Der Vertrag hat zwei Tabellen, und das ist Absicht: VERTRAG = was ein
# Abnehmer deklarieren DARF, GEBAUT = was der Verteiler heute wirklich kann.
# Ein Abnehmer, der etwas Deklariertes-aber-noch-nicht-Gebautes verlangt, wird
# LAUT abgewiesen statt still halb bedient (stiller Verlust ist die
# Fehlerklasse, die qs.md fuehrt).

ZEITBEZUG = ("clip", "wanduhr")
BEDARF = ("stream", "puffer")
WACHE_POLITIK = ("nachrechnen",)
# Z5: 'wanduhr' und 'puffer' sind jetzt GEBAUT (vorher laut abgewiesen).
# Die Abweisung bleibt als Mechanismus stehen — sie ist die Zusage, dass ein
# kuenftiger Vertragswert nie still halb bedient wird (qs.md: stiller Verlust).
GEBAUT = {"zeitbezug": ("clip", "wanduhr"), "bedarf": ("stream", "puffer"),
          "wache_politik": ("nachrechnen",)}
_NOCH_NICHT = {}

# §3.2 fps_sample: gemeinsam gedekodiert wird NUR bei step-Gleichheit
# (§9-Entscheid 3 "Rueckfall"). Zaehler + letzter Grund, damit der Rueckfall
# spaeter in /health ausweisbar ist, ohne dass hier ein Dienst-Zustand wohnt.
RUECKFAELLE = {"n": 0, "zuletzt": None}

# Testschalter (Z6-Vorgriff): None = decode.FrameIter. Die S2-Einheitstests
# patchen heute decode.FrameIter (tools/qs.sh) — ueber diese eine Stelle
# greift ein solcher Patch auch dann noch, wenn ein Abnehmer seine Frames
# nur noch ueber den Verteiler bezieht.
FRAME_QUELLE = None


def _frame_quelle():
    """DIE Frame-Quelle des Verteilers — lazy aufgeloest.

    Lazy, weil core.frames auch im DIENST-Prozess importiert wird
    (cleanup_cache, verifyd.py:3858) und `decode` cv2+numpy mitbraechte;
    injizierbar ueber FRAME_QUELLE (s.o.)."""
    if FRAME_QUELLE is not None:
        return FRAME_QUELLE
    from decode import FrameIter
    return FrameIter


def _formel(klasse, name):
    """Die drei Wache-Formeln werden NICHT nachgebaut, sondern von der
    Frame-Quelle uebernommen (decode.FrameIter._soll_samples / verlust_pct /
    unvollstaendig sind properties). EINE Quelle, keine driftende
    Zweitformel — dieselbe Regel wie bei den Aufzaehlungen (qs_ebenen.md).
    Fehlt eine Formel, ist das ein Befund und kein Sonderfall."""
    p = getattr(klasse, name, None)
    if not isinstance(p, property):
        raise TypeError(
            f"Frame-Quelle {klasse.__name__} traegt die Wache-Formel "
            f"'{name}' nicht. Der Verteiler rechnet die Wache je Abnehmer "
            f"nach (§3.2 wache_politik) und uebernimmt die Formel dafuer von "
            f"der Quelle — eine zweite, eigene Formel ist nicht vorgesehen.")
    return p.fget


class LaufInfo:
    """Was ein Abnehmer VOR dem ersten Frame wissen muss (Clip-Metadaten).

    Bewusst nur Metadaten: was der Abnehmer daraus macht (det_size, Zeitachse,
    Fenstergroessen), bleibt beim Abnehmer — der Verteiler kennt keine
    Modell-Parameter und keine Reihenfolge-Regeln der Erkennung."""

    def __init__(self, vid, it):
        self.vid = vid
        self.fps = it.fps
        self.breite, self.hoehe = it.breite, it.hoehe
        self.step = getattr(it, "step", 1)
        self.soll = getattr(it, "soll", None)
        # Z5: erwartete Sample-ZAHL, bevor das erste Frame faellt. Ein
        # haltender Abnehmer (bedarf='puffer') kann daraus VOR dem Puffern
        # rechnen, wie gross der Puffer wuerde, und absagen statt den Prozess
        # in den OOM zu fahren (§5 'RAM'). Die Formel wird NICHT nachgebaut,
        # sondern von der Frame-Quelle uebernommen (s. _formel) — dieselbe
        # Regel wie bei der Wache. None = die Quelle kennt kein Soll.
        try:
            self.soll_samples = _formel(type(it), "_soll_samples")(it)
        except TypeError:
            self.soll_samples = None


class Abnehmer:
    """Der EINE Andock-Punkt (§3.2 + §7): wer Frames braucht, deklariert
    seinen Bedarf und bekommt sie geliefert — nie ein eigener Decode.

    Alle SECHS Vertragsfelder sind Pflicht, keins hat einen Default: ein
    weggelassenes Feld waere wieder eine Annahme IM VERTEILER statt einer
    Aussage des Abnehmers, und genau das soll der Vertrag beenden.

      fps_sample     Sampling-Wunsch. Gemeinsam gedekodiert wird nur, wenn
                     ALLE Abnehmer denselben step ergeben (§9-Entscheid 3);
                     sonst faehrt jeder seinen eigenen Lauf (ein Download
                     bleibt). Grund: die Wache haengt am step des LAUFS
                     (decode.py:240-247) — ein gemeinsamer, anderer step
                     verschoebe still `frames_fehlen`.
      zeitbezug      'clip' (t = i/fps) | 'wanduhr' (der Abnehmer eicht
                     seine Zeitachse selbst gegen snapshot-clean). Der
                     Verteiler rechnet KEINEN Anker — er kennt Frigate
                     nicht und urteilt nie; seine Zusage an einen
                     wanduhr-Abnehmer ist der ORIGINAL-Index i und die
                     unveraenderte fps in LaufInfo, aus denen der Abnehmer
                     eicht. Weil der Anker je Event genau EINMAL faellt
                     (§3.2), laesst der Verteiler nur EINEN wanduhr-
                     Abnehmer je Lauf zu — ein zweiter braeuchte einen
                     geteilten Anker und wird laut abgewiesen.
      bedarf         'stream' (haelt nichts) | 'puffer' (haelt alle
                     Samples). Bei einem Puffer-Abnehmer sichert der
                     Verteiler zu, dass zwei aufeinander folgende Frames
                     nie DENSELBEN Speicher benutzen (Puffer-Wache in
                     _fahren) — eine recycelnde Frame-Quelle wuerde einem
                     Halter sonst still alle Bilder gleich machen.
                     RAM ist SEINE Sache: LaufInfo.soll_samples + breite/
                     hoehe sagen ihm in start() vorab, wie gross sein
                     Puffer wuerde (§5 'RAM', 4K: 23,7 MiB je Sample).
      hart           True: ein Ausfall beendet den ganzen Lauf (die
                     Ausnahme geht unveraendert an den Aufrufer).
                     False: der Ausfall wird in der Wache vermerkt, der
                     Abnehmer abgeworfen, die uebrigen laufen zu Ende.
      wache_politik  'nachrechnen': der Verteiler rechnet Verlust und
                     Vollstaendigkeit aus der EIGENEN Sample-Zahl dieses
                     Abnehmers nach (ein abgeworfener hat weniger gesehen
                     als der Lauf) und reicht decoder_fehler/hwdec/
                     hwdec_fallback unveraendert durch. Er urteilt nie.
      zeitwache_s    Zeitbudget DIESES Abnehmers ueber alle Callbacks
                     zusammen. None = kein eigenes Budget; dann gilt
                     weiter der Deckel des Aufrufers. Ein weicher Abnehmer
                     ueber Budget wird abgeworfen, ein harter laeuft zu
                     Ende (der Riss steht in der Wache).
                     ZWEISTUFIG seit Z5 (§3.2): Stufe (a) ist diese
                     Abnehmer-Wache. Stufe (b) ist die LAUF-Wache — ein
                     Waechter-Thread, der die ffmpeg-Pipe beendet
                     (decode.FrameIter.abbrechen), weil zwischen zwei
                     Frames sonst gar keine Wache greift: ein blockierender
                     Pipe-Read haengt bis zum Job-Deckel des Aufrufers.
                     Sie laeuft NUR, wenn JEDER Abnehmer des Laufs ein
                     Budget nennt, und dann mit dem GROESSTEN davon. Denn
                     die Pipe gehoert allen: haette ein Abnehmer kein
                     Budget (der Gesichts-Pfad hat bewusst keins), wuerde
                     ihm ein fremdes Zeitmass den Clip mitten im Urteil
                     abschneiden. Ohne dieses Feld erbte der Koerper-Strang
                     umgekehrt den 1800-s-Deckel des Jobs (§5).

    frame(i, frame_bgr)   Pflicht-Callback je Sample-Frame.
    start(LaufInfo)       optional, EINMAL vor dem ersten Frame.

    FRAME-EIGENTUM: das gelieferte Bild ist LESEND. Wer ueber den Callback
    hinaus etwas behaelt, KOPIERT — ein numpy-View haelt sonst den ganzen
    dekodierten Frame am Leben (die .copy()-Lehre aus analyze.py:261-265,
    die dort einen OOM-Kill beendet hat)."""

    def __init__(self, name, fps_sample, zeitbezug, bedarf, hart,
                 wache_politik, zeitwache_s, frame, start=None):
        for feld, wert, erlaubt in (("zeitbezug", zeitbezug, ZEITBEZUG),
                                    ("bedarf", bedarf, BEDARF),
                                    ("wache_politik", wache_politik,
                                     WACHE_POLITIK)):
            if wert not in erlaubt:
                raise ValueError(
                    f"Abnehmer '{name}': {feld}={wert!r} steht nicht im "
                    f"Vertrag {erlaubt}")
            if wert not in GEBAUT[feld]:
                raise NotImplementedError(
                    f"Abnehmer '{name}': {feld}={wert!r} ist deklariert, "
                    f"aber im Verteiler NOCH NICHT GEBAUT — "
                    f"{_NOCH_NICHT.get(wert, 'kein Bauzug zugeordnet')}. "
                    f"Lieber laut abweisen als still anders bedienen.")
        if not callable(frame):
            raise TypeError(f"Abnehmer '{name}': frame-Callback fehlt")
        if start is not None and not callable(start):
            raise TypeError(f"Abnehmer '{name}': start ist nicht aufrufbar")
        if float(fps_sample) <= 0:
            raise ValueError(f"Abnehmer '{name}': fps_sample muss > 0 sein")
        self.name = name
        self.fps_sample = fps_sample
        self.zeitbezug = zeitbezug
        self.bedarf = bedarf
        self.hart = bool(hart)
        self.wache_politik = wache_politik
        self.zeitwache_s = zeitwache_s
        self.frame = frame
        self.start = start


class Wache:
    """Wache-Werte JE ABNEHMER (§3.2 'wache_politik').

    Traegt bewusst dieselben Namen wie decode.FrameIter (gelesen/soll/
    samples/verlust_pct/unvollstaendig/decoder_fehler/hwdec/hwdec_fallback):
    ein Abnehmer, der frueher direkt am FrameIter haing, liest danach
    unveraendert weiter. `samples`/`gelesen` sind die des ABNEHMERS (ein
    abgeworfener hat weniger gesehen als der Lauf), die drei Stream-
    Eigenschaften kommen unveraendert vom Lauf."""

    def __init__(self, name, it):
        self.name = name
        self._quelle = type(it)
        self.fps = it.fps
        self.breite, self.hoehe = it.breite, it.hoehe
        self.step = getattr(it, "step", 1)
        self.soll = getattr(it, "soll", None)
        self.samples = 0
        self.gelesen = 0
        self.decoder_fehler = 0
        self.hwdec = False
        self.hwdec_fallback = False
        self.cb_s = 0.0            # in den Callbacks verbrachte Zeit
        self.abgeworfen = False    # weicher Abnehmer: Ausfall/Budget
        self.budget_gerissen = False
        self.ausfall = None        # repr der Ausnahme bzw. Budget-Grund
        self.lauf_wache_gerissen = False   # Z5: Stufe (b) hat die Pipe beendet

    def _durchreichen(self, it):
        """decoder_fehler/hwdec/hwdec_fallback sind Eigenschaften des
        STREAMS, nicht des Abnehmers — unveraendert durchgereicht (§3.2)."""
        self.decoder_fehler = getattr(it, "decoder_fehler", 0)
        self.hwdec = getattr(it, "hwdec", False)
        self.hwdec_fallback = getattr(it, "hwdec_fallback", False)

    # Formeln der Frame-Quelle, nicht nachgebaut (s. _formel).
    @property
    def _soll_samples(self):
        return _formel(self._quelle, "_soll_samples")(self)

    @property
    def verlust_pct(self):
        return _formel(self._quelle, "verlust_pct")(self)

    @property
    def unvollstaendig(self):
        return _formel(self._quelle, "unvollstaendig")(self)


def lauf(vid, abnehmer, log=print):
    """EIN Decode fuer alle registrierten Abnehmer. Rueckgabe: {name: Wache}.

    NEUTRALITAET PER KONSTRUKTION: bei EINEM Abnehmer entsteht genau EIN
    Iterator mit dessen fps_sample — dieselbe Frame-Index-Menge wie beim
    frueheren Einzellauf. Der Verteiler filtert nie selbst."""
    if not abnehmer:
        raise ValueError("lauf() ohne Abnehmer — es gibt nichts zu liefern")
    namen = [a.name for a in abnehmer]
    if len(set(namen)) != len(namen):
        raise ValueError(f"Abnehmer-Namen nicht eindeutig: {namen}")
    uhren = [a.name for a in abnehmer if a.zeitbezug == "wanduhr"]
    if len(uhren) > 1:
        raise NotImplementedError(
            f"zwei wanduhr-Abnehmer in einem Lauf ({uhren}): der Anker faellt "
            f"je Event genau EINMAL (§3.2 zeitbezug). Einen geteilten Anker "
            f"gibt es noch nicht — lieber laut abweisen als zweimal eichen.")
    Q = _frame_quelle()
    # Je Abnehmer EIN Iterator (nur ffprobe, KEIN Decode): so kommt jeder
    # step aus der einen Formel der Frame-Quelle (decode.py:140) statt aus
    # einer zweiten Rechnung hier. Bei step-Gleichheit faehrt der erste und
    # die uebrigen werden verworfen (bei einem Abnehmer: kein Zusatzaufwand).
    iters = [Q(vid, a.fps_sample) for a in abnehmer]
    steps = {getattr(it, "step", 1) for it in iters}
    if len(steps) == 1:
        return _fahren(vid, abnehmer, iters[0])
    RUECKFAELLE["n"] += 1
    RUECKFAELLE["zuletzt"] = {
        "vid": os.path.basename(str(vid)),
        "steps": {a.name: getattr(it, "step", 1)
                  for a, it in zip(abnehmer, iters)}}
    log("WARN: frame distributor falls back to separate decodes — consumers "
        f"ask for different steps {RUECKFAELLE['zuletzt']['steps']}. One "
        "download stays, but a shared step would silently move the "
        "completeness watch (it is computed against the step of the run, "
        "decode.py:240-247) and with it frames_fehlen.")
    ergebnis = {}
    for a, it in zip(abnehmer, iters):
        ergebnis.update(_fahren(vid, [a], it))
    return ergebnis


def _zeiger(frame):
    """Speicher-Adresse eines Frames (fuer die Puffer-Wache). None = das
    Objekt sagt nichts darueber (fremde Test-Quelle) -> keine Aussage."""
    try:
        return frame.__array_interface__["data"][0]
    except Exception:                                # noqa: BLE001
        return None


def _fahren(vid, abnehmer, it):
    """EIN Iterator, Bedienung in Registrierungs-Reihenfolge, harte zuerst."""
    reihenfolge = ([a for a in abnehmer if a.hart]
                   + [a for a in abnehmer if not a.hart])
    wachen = {a.name: Wache(a.name, it) for a in abnehmer}
    aktiv = []
    for a in reihenfolge:
        if a.start is None:
            aktiv.append(a)
            continue
        try:
            a.start(LaufInfo(vid, it))
        except Exception as ex:                      # noqa: BLE001
            if a.hart:
                raise
            w = wachen[a.name]
            w.ausfall, w.abgeworfen = repr(ex), True
            continue
        aktiv.append(a)
    if not aktiv:
        # Alle weichen Abnehmer haben schon in start() abgesagt (z.B. der
        # Koerper-Abnehmer am RAM-Gate). Dann gar nicht erst dekodieren:
        # ffmpeg zu starten, um beim ersten Frame abzubrechen, waere genau
        # die verschwendete Arbeit, die dieser Zug einsparen soll.
        for w in wachen.values():
            w._durchreichen(it)
        return wachen
    # Zeitwache Stufe (b), die LAUF-Wache (§3.2): nur wenn JEDER Abnehmer ein
    # Budget nennt — die Pipe gehoert allen, und ein Abnehmer ohne eigenes
    # Zeitmass (der Gesichts-Pfad) darf nie durch das eines anderen
    # abgeschnitten werden. Dann gilt das GROESSTE Budget.
    budgets = [a.zeitwache_s for a in abnehmer]
    lauf_budget = (max(budgets) if budgets and None not in budgets else None)
    fertig, waechter = threading.Event(), None
    if lauf_budget is not None and hasattr(it, "abbrechen"):
        def _lauf_wache():
            if fertig.wait(lauf_budget):
                return                     # Lauf war rechtzeitig durch
            if it.abbrechen():             # ffmpeg beenden -> read() bekommt EOF
                for w in wachen.values():
                    w.lauf_wache_gerissen = True
        waechter = threading.Thread(target=_lauf_wache, daemon=True,
                                    name="frames-laufwache")
        waechter.start()
    # Puffer-Wache (§3.2 bedarf): haelt ein Abnehmer die Frames, darf die
    # Quelle keinen Speicher wiederverwenden. Geprueft wird gegen das
    # VORHERIGE Frame, das dafuer eine Runde lang festgehalten wird — nur so
    # ist Adressgleichheit beweisend (freigegebener Speicher darf dieselbe
    # Adresse wiederbekommen, festgehaltener nicht).
    haelt = any(a.bedarf == "puffer" for a in abnehmer)
    letztes, vor_zeiger = [None], None      # [0] haelt das vorherige Frame fest
    gen = iter(it)
    try:
        for i, frame in gen:
            if not aktiv:
                break            # niemand mehr da, den der Decode bedient
            if haelt:
                z = _zeiger(frame)
                if z is not None and z == vor_zeiger:
                    raise RuntimeError(
                        "Frame-Quelle liefert wiederverwendeten Speicher, ein "
                        "Abnehmer haelt aber die Samples (bedarf='puffer'): "
                        "alle gehaltenen Bilder waeren dasselbe. Die Quelle "
                        "muss je Sample ein eigenes Bild liefern.")
                letztes[0], vor_zeiger = frame, z
            for a in list(aktiv):
                w = wachen[a.name]
                t0 = time.monotonic()
                try:
                    a.frame(i, frame)
                except Exception as ex:              # noqa: BLE001
                    if a.hart:
                        raise                        # Ausfall beendet den Lauf
                    w.ausfall, w.abgeworfen = repr(ex), True
                    aktiv.remove(a)
                    continue
                finally:
                    w.cb_s += time.monotonic() - t0
                w.samples += 1
                w.gelesen = i + 1
                if a.zeitwache_s is not None and w.cb_s > a.zeitwache_s:
                    w.budget_gerissen = True
                    if not a.hart:
                        w.ausfall = (f"Zeitwache {a.zeitwache_s}s gerissen "
                                     f"({w.cb_s:.1f}s in {w.samples} Frames)")
                        w.abgeworfen = True
                        aktiv.remove(a)
    finally:
        fertig.set()                 # Lauf-Wache abbestellen (Z5, Stufe b)
        if waechter is not None:
            waechter.join(timeout=5)
        letztes[0] = None            # letzte Puffer-Wache-Referenz loslassen
        # Deterministisch schliessen: das finally IN der Frame-Quelle
        # (ffmpeg-Pipe zu, rc lesen, stderr auswerten) muss auch dann laufen,
        # wenn wir vorzeitig aussteigen — sonst faehrt die Wache ohne
        # decoder_fehler heim. decode.FrameIter.__iter__ ist ein Generator und
        # hat close(); eine einfache Testquelle liefert evtl. nur einen
        # gewoehnlichen Iterator — dort gibt es nichts zu schliessen.
        if hasattr(gen, "close"):
            gen.close()
        for w in wachen.values():
            w._durchreichen(it)
    return wachen
