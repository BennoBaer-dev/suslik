"""Dienst-Log auf die Platte (.354, User-Auftrag 27.08.).

WARUM: Bis .353 gab es das Log nur zweimal fluechtig — als 300-Zeilen-Ringpuffer
hinter /log und im `docker logs`-Puffer. Bei einem Feldtester deckte /log
dadurch nur 18,6 Minuten ab, der interessante Startblock war laengst
herausgerollt, und an `docker logs` kommt ein Nutzer ohne Shell-Zugang nicht
heran. Ein Fehler, der nach einer Stunde auffaellt, war damit nicht mehr
nachweisbar.

WAS: Alles, was der Dienst nach stdout/stderr schreibt, landet zusaetzlich in
`<data_dir>/logs/suslik.log`, wird taeglich und bei jedem Neustart gedreht, die
alten Staende gepackt und nach `behalten_tage` geloescht.

WARUM AUF DESKRIPTOR-EBENE (os.dup2) UND NICHT ALS sys.stdout-Huelle: GEMESSEN
27.08. an suslik-prod — von 624 Zeilen stammen 104 NICHT aus svc.log(), darunter
Ausgaben von onnxruntime ("Applied providers: ...") und insightface, die aus der
C-Ebene direkt auf Deskriptor 1 schreiben und an Pythons sys.stdout vorbeigehen.
Eine Python-Huelle haette genau die verloren, also ausgerechnet die Zeilen des
Startblocks, um den es geht. Der Deskriptor-Weg faengt zusaetzlich Kindprozesse,
die Deskriptor 1 erben.

DER PREIS UND WIE ER GEZAEHMT IST: Haengt der Lese-Faden, laeuft die Pipe voll
und der Dienst blockiert beim naechsten print(). Deshalb faengt die Leseschleife
JEDE Ausnahme und macht weiter; scheitert das Schreiben in die Datei, wird die
Datei aufgegeben und nur noch nach stdout durchgereicht. Der Dienst darf an
seinem eigenen Log nicht sterben.

REIHENFOLGE: start() laeuft VOR core.stderr_sieb.installieren(). Das Sieb
rettet sich beim Installieren den damaligen fd 2 und schreibt spaeter dorthin;
liefe es zuerst, floesse die gefilterte stderr-Ausgabe an dieser Datei vorbei.
Weil der Ordner erst nach dem Laden der Config feststeht, nimmt start() noch
keine Datei: bis ordner_setzen() gerufen wird, sammelt ein gedeckelter
Speicherpuffer die Bytes und wird dann in einem Stueck geschrieben.

EHRLICHE GRENZE: Ein `kill -9` kann die letzten, noch ungeschriebenen Bytes
kosten. Und Kindprozesse, die per dup2 ein eigenes Ziel setzen (Worker-Job-
Fenster), schreiben bewusst an dieser Datei vorbei in ihr Job-Log.

LOG-SYSTEMATIK (Stufe 2, E3, E6, E9): der Tee setzt die Brocken zu Zeilen
zusammen (wie das Sieb) und liest jede Zeile mit `core.logbuch.ZEILENMUSTER`. Er
zaehlt je Prozess WARNING, ERROR und CRITICAL, dazu Zeilen ohne Kopf, und merkt
sich die letzte Fehlerzeile (/health, Block `log`). Er bleibt der EINE Schreiber
beider Dateien: Zeilen des Pruef-Loggers gehen nach `pruef.log`, WARNING und
hoeher bei eingeschaltetem Pruef-Kanal zusaetzlich; alles andere nach
`suslik.log`. Sein eigenes Scheitern schreibt er nie ueber fd 1/2 (die Zeile
liefe in genau diesen Faden zurueck), sondern haelt es als Zustand und Zaehler
am Objekt; nur das Aufgeben der Datei meldet eine Zeile direkt an den geretteten
Original-Deskriptor.
"""

import datetime
import gzip
import os
import shutil
import threading
import time

DATEI = "suslik.log"
PRUEF_DATEI = "pruef.log"          # E9: die Datei des Pruef-Kanals, gleicher Ordner
BEHALTEN_TAGE_WERK = 14            # Werkswerte der Drehung (Config: log_behalten_tage,
MAX_MB_WERK = 64                   # log_max_mb); gelten fuer beide Dateien des Tees
DIAGNOSE_MAX_MB = 20.0             # E3: Drehwert der Diagnose-Dateien (wache.log je
#                                    Kamera, meldungen.jsonl), eine .1-Stufe
RINGPUFFER_ZEILEN = 300            # E10: letzte Dienst-Zeilen fuer /log und /sync_diagnose
LETZTE_ERROR_ZEICHEN = 300         # E6: so lang steht die letzte Fehlerzeile in /health
ZEILE_MAX = 65536                  # Teilzeile ohne Zeilenende: ab hier durchreichen (wie das Sieb)
_GRUENDE = {"Dienststart": "service start", "Tageswechsel": "day change",
            "Groessengrenze": "size limit"}


class _Stueck:
    """EINE gedrehte Datei des Tees (suslik.log oder pruef.log). Die Grenzen
    (Tage, Bytes) liest sie beim Drehen vom Tee, damit main() sie nach dem
    Laden der Config an EINER Stelle setzt."""

    def __init__(self, tee, name):
        self.tee = tee
        self.name = name
        self.praefix = name[:-len(".log")]
        self.pfad = None
        self.fh = None
        self.tag = None
        self.aufgegeben = False

    def oeffnen(self):
        """Die Datei im Ordner des Tees zum Anhaengen oeffnen und den Tag merken.
        -> None; wirft, wenn der Ordner nicht nutzbar ist."""
        os.makedirs(self.tee.ordner, exist_ok=True)
        self.pfad = os.path.join(self.tee.ordner, self.name)
        self.fh = open(self.pfad, "ab", buffering=0)
        self.tag = datetime.date.today()

    def drehen(self, grund):
        """Aktuellen Stand wegpacken und neu anfangen. Fehler beim Drehen
        duerfen das Schreiben nicht kosten — im Zweifel weiter in die alte
        Datei; der Fehler zaehlt am Tee (dreh_fehler)."""
        try:
            if self.fh:
                self.fh.close()
            if os.path.exists(self.pfad) and os.path.getsize(self.pfad) > 0:
                stempel = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # Der Stempel hat nur Sekunden-Aufloesung. Zwei Drehungen in
                # derselben Sekunde (Groessengrenze bei einem Ausgabe-Schwall)
                # wuerden dieselbe Datei ueberschreiben — STILLER VERLUST,
                # beim Selbsttest 27.08. genau so beobachtet. Deshalb ein
                # laufender Index, sobald der Name schon belegt ist.
                ziel = os.path.join(self.tee.ordner, f"{self.praefix}-{stempel}.log.gz")
                n = 1
                while os.path.exists(ziel):
                    ziel = os.path.join(self.tee.ordner, f"{self.praefix}-{stempel}-{n}.log.gz")
                    n += 1
                with open(self.pfad, "rb") as q, gzip.open(ziel, "wb") as z:
                    shutil.copyfileobj(q, z)
                os.remove(self.pfad)
            self.oeffnen()
            self.fh.write(self.tee.eigene_zeile(
                "INFO", f"--- new log piece ({_GRUENDE.get(grund, grund)}) ---"))
            self.aufraeumen()
        except Exception:
            self.tee.dreh_fehler += 1
            if not self.fh or self.fh.closed:
                try:
                    self.oeffnen()
                except Exception as e:
                    self.fh = None
                    self.tee.aufgeben(self, f"reopen after rotation failed: {type(e).__name__}")

    def aufraeumen(self):
        """Gepackte Staende aelter als behalten_tage entfernen; Fehler zaehlt der Tee.
        -> None."""
        grenze = datetime.datetime.now().timestamp() - self.tee.behalten_tage * 86400
        try:
            for n in os.listdir(self.tee.ordner):
                if not (n.startswith(self.praefix + "-") and n.endswith(".log.gz")):
                    continue
                p = os.path.join(self.tee.ordner, n)
                if os.path.getmtime(p) < grenze:
                    os.remove(p)
        except Exception:
            self.tee.aufraeum_fehler += 1

    def schreiben(self, daten):
        """Bytes anhaengen, danach am Tageswechsel oder an der Groessengrenze drehen.
        -> None; wirft bei Schreibfehlern (der Tee gibt die Datei dann auf)."""
        if self.fh is None:
            return
        self.fh.write(daten)
        if datetime.date.today() != self.tag:
            self.drehen("Tageswechsel")
        elif self.fh.tell() >= self.tee.max_bytes:
            self.drehen("Groessengrenze")


class Logdatei:
    """Tee von stdout/stderr in eine gedrehte Datei. Nach start() laeuft je
    Deskriptor ein Lese-Faden, der die Bytes an den ECHTEN Deskriptor
    weiterreicht (damit `docker logs` unveraendert weiterlaeuft), sie zu Zeilen
    zusammensetzt, zaehlt und in die Datei schreibt."""

    VORPUFFER = 256 * 1024                # Deckel, bis der Ordner feststeht

    def __init__(self, behalten_tage=BEHALTEN_TAGE_WERK, max_mb=MAX_MB_WERK):
        from core import logbuch as _lb   # spaet: logbuch importiert dieses Modul
        self._lb = _lb
        self.ordner = None
        self.behalten_tage = max(1, int(behalten_tage))
        self.max_bytes = max(1, int(max_mb)) * 1024 * 1024
        self._haupt = _Stueck(self, DATEI)
        self._pruef = _Stueck(self, PRUEF_DATEI)
        self._vor = []                    # Zeilen vor ordner_setzen()
        self._vor_bytes = 0
        self._schloss = threading.RLock()   # reentrant: schreiben ruft drehen unter dem Schloss
        self._orig = {}
        self._faeden = {}
        self._rest = {}
        self._aus = False
        # Zustand und Zaehler fuer /health (E2 Sonderfaelle, E6): nur zaehlen.
        self.dreh_fehler = 0
        self.aufraeum_fehler = 0
        self.vorpuffer_fehler = 0
        self.vorpuffer_verworfen_bytes = 0
        self.aussen_fehler = 0
        self.datei_aufgegeben = None
        self.zaehl_fehler = 0
        self.fremd_n = 0
        self.zaehler = {}
        self.letzte_error = None
        self.seit = time.time()

    @property
    def pfad(self):
        """Pfad der Hauptdatei suslik.log (wie vor der Log-Systematik).
        -> str oder None, solange kein Ordner gesetzt ist."""
        return self._haupt.pfad

    def eigene_zeile(self, stufe, text):
        """Eine Zeile des Tees selbst (Kopfzeile eines Stuecks) in der Form (E4).
        -> bytes mit Zeilenende."""
        return (self._lb.format_line(getattr(self._lb, stufe), "core.logdatei",
                                     "Logdatei", text) + "\n").encode("utf-8", "replace")

    def aufgeben(self, stueck, grund):
        """Eine Datei aufgeben (Dienst laeuft weiter). EINE Zeile direkt an den
        geretteten Original-Deskriptor, nie ueber fd 1/2 (E2)."""
        stueck.fh = None
        stueck.aufgegeben = True
        self.datei_aufgegeben = {"datei": stueck.name, "zeit": round(time.time(), 1),
                                 "grund": str(grund)[:200]}
        ziel = self._orig.get(1)
        if ziel is None:
            return
        try:
            os.write(ziel, self._lb.format_line(
                self._lb.ERROR, "core.logdatei", "Logdatei",
                f"log file {stueck.name} given up ({grund}) — the container log "
                f"keeps running").encode("utf-8", "replace") + b"\n")
        except OSError:
            self.aussen_fehler += 1

    # ---- Tee --------------------------------------------------------------

    def start(self):
        """stdout und stderr abgreifen. GETRENNTE Rohre, damit im Docker-Log
        weiter auf dem richtigen Kanal landet, was dort hingehoert."""
        for fd in (1, 2):
            echt = os.dup(fd)
            os.set_inheritable(echt, False)
            r, w = os.pipe()
            os.set_inheritable(r, False)
            os.dup2(w, fd)
            os.close(w)
            self._orig[fd] = echt
            self._rest[fd] = b""
            t = threading.Thread(target=self._schleife, args=(r, echt, fd),
                                 name=f"logdatei-fd{fd}", daemon=True)
            t.start()
            self._faeden[fd] = t
        return self

    def ordner_setzen(self, ordner):
        """Ordner nachreichen (nach dem Laden der Config): Datei anlegen,
        drehen und den Vorpuffer hineinschreiben."""
        with self._schloss:
            self.ordner = ordner
            try:
                self._haupt.oeffnen()
            except Exception as e:
                self._haupt.fh = None
                self.datei_aufgegeben = {"datei": DATEI, "zeit": round(time.time(), 1),
                                         "grund": f"log folder not usable: {type(e).__name__}"}
                return self
            vor = b"".join(self._vor)
            self._vor = []
            self._vor_bytes = 0
            self._haupt.drehen("Dienststart")
            if vor and self._haupt.fh:
                try:
                    self._haupt.fh.write(vor)
                except Exception:
                    self.vorpuffer_fehler += 1
            return self

    def _schleife(self, lese, ziel, fd):
        while not self._aus:
            try:
                brocken = os.read(lese, 65536)
            except Exception:
                break
            if not brocken:
                break
            try:                                  # 1. immer nach draussen
                os.write(ziel, brocken)
            except Exception:
                self.aussen_fehler += 1
            rest = self._rest.get(fd, b"") + brocken   # 2. Zeilen zusammensetzen
            while b"\n" in rest:
                zeile, rest = rest.split(b"\n", 1)
                self._zeile(zeile + b"\n")
            if len(rest) > ZEILE_MAX:
                self._zeile(rest)
                rest = b""
            self._rest[fd] = rest
        if self._rest.get(fd):
            self._zeile(self._rest.pop(fd))

    def _zeile(self, daten):
        """EINE Zeile zaehlen und in ihre Datei(en) legen (E6, E9)."""
        teile = self._zaehlen(daten)
        pruef_an = self._lb.pruef_on()
        laut = teile is not None and teile["stufe"] in ("WARNING", "ERROR", "CRITICAL")
        ist_pruef = teile is not None and teile["modul"] == self._lb.PRUEF
        with self._schloss:
            if not ist_pruef or laut or not pruef_an:
                self._haupt_schreiben(daten)
            if pruef_an and (ist_pruef or laut):
                self._pruef_schreiben(daten)

    def _haupt_schreiben(self, daten):
        if self.ordner is None:
            if self._vor_bytes < self.VORPUFFER:
                self._vor.append(daten)
                self._vor_bytes += len(daten)
            else:
                self.vorpuffer_verworfen_bytes += len(daten)
            return
        try:
            self._haupt.schreiben(daten)
        except Exception as e:
            try:
                self._haupt.fh.close()
            except Exception:
                pass
            self.aufgeben(self._haupt, f"write failed: {type(e).__name__}")

    def _pruef_schreiben(self, daten):
        if self.ordner is None or self._pruef.aufgegeben:
            return
        try:
            if self._pruef.fh is None:
                self._pruef.oeffnen()
                self._pruef.drehen("Dienststart")
            self._pruef.schreiben(daten)
        except Exception as e:
            self.aufgeben(self._pruef, f"write failed: {type(e).__name__}")

    def _zaehlen(self, daten):
        """Kopf lesen und zaehlen; wirft nie (zaehl_fehler). -> Gruppen oder None."""
        try:
            text = daten.decode("utf-8", "replace").rstrip("\n")
            m = self._lb.ZEILENMUSTER.match(text)
            if m is None:
                if text.strip():
                    self.fremd_n += 1
                return None
            g = m.groupdict()
            if g["art"] == "|" and g["stufe"] in ("WARNING", "ERROR", "CRITICAL"):
                je = self.zaehler.setdefault(g["prozess"], {
                    "warning_n": 0, "error_n": 0, "critical_n": 0})
                je[g["stufe"].lower() + "_n"] += 1
                if g["stufe"] != "WARNING":
                    quelle = f"{g['prozess']}/{g['modul']}:{g['funktion']}"
                    self.letzte_error = {"zeit": g["zeit"], "quelle": quelle,
                                         "text": g["text"][:LETZTE_ERROR_ZEICHEN]}
            return g
        except Exception:
            self.zaehl_fehler += 1
            return None

    def zaehler_stand(self):
        """Zaehler seit Dienststart je Prozess, fremde Zeilen, letzte Fehlerzeile (E6).
        -> dict, Kopie."""
        with self._schloss:
            return {"seit": round(self.seit, 1),
                    "zaehler": {p: dict(z) for p, z in self.zaehler.items()},
                    "fremd_n": self.fremd_n, "letzte_error": self.letzte_error,
                    "zaehl_fehler": self.zaehl_fehler}

    def zustand(self):
        """Zustand des Tees fuer /health (E2 Sonderfaelle): Faeden, Dateien, Zaehler.
        -> dict."""
        return {"datei": self._haupt.pfad if self._haupt.fh else None,
                "pruef_datei": self._pruef.pfad if self._pruef.fh else None,
                "faden_lebt": {f"fd{fd}": t.is_alive() for fd, t in self._faeden.items()},
                "datei_aufgegeben": self.datei_aufgegeben,
                "dreh_fehler": self.dreh_fehler, "aufraeum_fehler": self.aufraeum_fehler,
                "vorpuffer_fehler": self.vorpuffer_fehler,
                "vorpuffer_verworfen_bytes": self.vorpuffer_verworfen_bytes,
                "aussen_fehler": self.aussen_fehler}

    def zuruecksetzen(self):
        """Vor einem os.execv: den Tee ABBAUEN — die geretteten Original-
        Deskriptoren zurueck auf 1/2, Dateien schliessen.

        WARUM (Datenachsen-Fund 27.08., Klasse stiller Verlust): execv ersetzt
        das Prozessabbild, die Lese-Faeden sterben, aber fd 1/2 zeigen weiter
        auf die Schreibseite der alten Rohre. Deren Lese-Enden sind CLOEXEC und
        beim execv zugegangen — jedes write danach wirft BrokenPipe und wird
        geschluckt. BEWIESEN an einer Probe: nach dem execv kamen 0 von 3000
        Zeilen am aeusseren stdout an (docker logs STUMM), alle 3000 nur in
        der Datei. Ohne diesen Rueckbau ist das Container-Log nach jedem
        Wizard-Neustart tot. Der neue Prozess baut seinen Tee in main() frisch
        auf; dass hier die Datei geschlossen wird, ist richtig — beim Start
        wird ohnehin gedreht."""
        self._aus = True
        for fd, echt in self._orig.items():
            try:
                os.dup2(echt, fd)
            except Exception:
                pass
        for stueck in (self._haupt, self._pruef):
            try:
                if stueck.fh:
                    stueck.fh.close()
            except Exception:
                pass
            stueck.fh = None


def dateien(ordner):
    """Alle Logstuecke beider Dateien (suslik, pruef), juengstes zuerst
    -> [(name, bytes, mtime)]."""
    aus = []
    try:
        for n in sorted(os.listdir(ordner), reverse=True):
            if n in (DATEI, PRUEF_DATEI) or (n.startswith(("suslik-", "pruef-"))
                                             and n.endswith(".log.gz")):
                p = os.path.join(ordner, n)
                aus.append((n, os.path.getsize(p), os.path.getmtime(p)))
    except Exception:
        pass
    return aus


# --------------------------------------------------------- Debug-Schalter (.511)
# WARUM EINE DATEI UND NICHT DER CONFIG-STORE: der Live-Waechter laeuft als
# EIGENER Prozess (core/livewached, gestartet von core/liveaufsicht) und holt
# seine Config ueber `verifyd.load_config`. Genau dort steht seit B6 (24.08.)
# der Start-Reset "debug wird bei jedem Start auf aus gestellt" — der Store
# taugt deshalb NICHT als Traeger: jeder Reload der Engine bekaeme debug=False
# zurueck, egal was der Nutzer eben auf der Konfigurationsseite gesetzt hat.
# Also spiegelt der DIENST seinen laufenden Schalter in diese eine Datei
# (Existenz = an), und die Engine liest sie. Ein Schalter, eine Wahrheit, und
# der Start-Reset bleibt unangetastet: beim Start ist der Schalter aus, also
# loescht der Dienst die Datei.
# Muster wie state/live_kommando.json: der Dienst schreibt, die Engine liest.
FLAGGE = "debug_an"
PRUEF_FLAGGE = "pruef_an"          # E9: Pruef-Kanal an, Inhalt = Takt in Sekunden
FLAGGE_TTL_S = 2.0                 # E11: so lange gilt ein gelesener Flaggen-Stand
#                                    in Worker und Live-Engine (die Kachelzeilen
#                                    sind die haeufigsten der Anlage, gelesen wird
#                                    deshalb nicht je Zeile)


def debug_flagge_pfad(data_dir):
    return os.path.join(str(data_dir or ""), "state", FLAGGE)


def debug_flagge_setzen(data_dir, an):
    """Den LAUFENDEN debug-Stand des Dienstes in die Flaggendatei spiegeln.
    Nie laut scheitern: ein read-only /data (Erststart-Fall aus B6) darf den
    Dienst nicht kosten — dann bleibt die Engine eben still. -> bool(an)."""
    p = debug_flagge_pfad(data_dir)
    try:
        if an:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write("1\n")
        else:
            try:
                os.remove(p)
            except FileNotFoundError:
                pass
    except OSError:
        pass
    return bool(an)


def debug_flagge_an(data_dir):
    """Steht der Schalter? (Existenz der Flaggendatei.) Fail-closed: was nicht
    gelesen werden kann, gilt als aus — ein Diagnose-Schalter darf nie durch
    einen IO-Fehler ANgehen."""
    try:
        return os.path.exists(debug_flagge_pfad(data_dir))
    except OSError:
        return False


def pruef_flagge_setzen(data_dir, takt_s):
    """Den Pruef-Kanal des Dienstes fuer Worker und Live-Engine spiegeln (E9):
    Datei mit dem Takt = an, keine Datei = aus. Nie laut scheitern, wie die
    debug-Flagge. -> takt_s."""
    p = os.path.join(str(data_dir or ""), "state", PRUEF_FLAGGE)
    try:
        if takt_s:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(f"{int(takt_s)}\n")
        else:
            try:
                os.remove(p)
            except FileNotFoundError:
                pass
    except OSError:
        pass
    return takt_s


def pruef_flagge_lesen(data_dir):
    """Steht der Pruef-Kanal? Fail-closed wie debug_flagge_an.
    -> Takt in Sekunden oder None (aus)."""
    try:
        with open(os.path.join(str(data_dir or ""), "state", PRUEF_FLAGGE)) as f:
            return max(1, int(f.read().strip() or 0)) or None
    except (OSError, ValueError):
        return None


def schwanz(pfad, zeilen=2000):
    """Die letzten `zeilen` Zeilen der laufenden Datei, ohne sie ganz zu lesen."""
    try:
        groesse = os.path.getsize(pfad)
        block = min(groesse, max(65536, zeilen * 200))
        with open(pfad, "rb") as f:
            f.seek(groesse - block)
            roh = f.read()
        text = roh.decode("utf-8", "replace")
        if block < groesse:
            text = text.split("\n", 1)[-1]
        return "\n".join(text.splitlines()[-zeilen:])
    except Exception:
        return ""
