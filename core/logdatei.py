"""Dienst-Log auf die Platte (.354, User-Auftrag 27.08.).

WARUM: Bis .353 gab es das Log nur zweimal fluechtig — als 300-Zeilen-Ringpuffer
hinter /log und im `docker logs`-Puffer. Beim Feldtester Shaun deckte /log
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
"""

import datetime
import gzip
import os
import shutil
import threading

DATEI = "suslik.log"


class Logdatei:
    """Tee von stdout/stderr in eine gedrehte Datei. Nach start() laeuft ein
    Lese-Faden, der die Bytes an den ECHTEN stdout weiterreicht (damit
    `docker logs` unveraendert weiterlaeuft) und zusaetzlich in die Datei
    schreibt."""

    VORPUFFER = 256 * 1024                # Deckel, bis der Ordner feststeht

    def __init__(self, behalten_tage=14, max_mb=64):
        self.ordner = None
        self.behalten_tage = max(1, int(behalten_tage))
        self.max_bytes = max(1, int(max_mb)) * 1024 * 1024
        self.pfad = None
        self._fh = None
        self._tag = None
        self._vor = []                    # Bytes vor ordner_setzen()
        self._vor_bytes = 0
        self._schloss = threading.RLock()   # reentrant: _pruefen ruft _drehen unter dem Schloss
        self._orig = {}
        self._faeden = []
        self._aus = False

    # ---- Datei-Verwaltung -------------------------------------------------

    def _oeffnen(self):
        os.makedirs(self.ordner, exist_ok=True)
        self.pfad = os.path.join(self.ordner, DATEI)
        self._fh = open(self.pfad, "ab", buffering=0)
        self._tag = datetime.date.today()

    def _drehen(self, grund):
        """Aktuellen Stand wegpacken und neu anfangen. Fehler beim Drehen
        duerfen das Schreiben nicht kosten — im Zweifel weiter in die alte
        Datei."""
        with self._schloss:
            self._drehen_intern(grund)

    def _drehen_intern(self, grund):
        try:
            if self._fh:
                self._fh.close()
            if os.path.exists(self.pfad) and os.path.getsize(self.pfad) > 0:
                stempel = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # Der Stempel hat nur Sekunden-Aufloesung. Zwei Drehungen in
                # derselben Sekunde (Groessengrenze bei einem Ausgabe-Schwall)
                # wuerden dieselbe Datei ueberschreiben — STILLER VERLUST,
                # beim Selbsttest 27.08. genau so beobachtet. Deshalb ein
                # laufender Index, sobald der Name schon belegt ist.
                ziel = os.path.join(self.ordner, f"suslik-{stempel}.log.gz")
                n = 1
                while os.path.exists(ziel):
                    ziel = os.path.join(self.ordner, f"suslik-{stempel}-{n}.log.gz")
                    n += 1
                with open(self.pfad, "rb") as q, gzip.open(ziel, "wb") as z:
                    shutil.copyfileobj(q, z)
                os.remove(self.pfad)
            self._oeffnen()
            self._fh.write(f"--- neues Logstueck ({grund}) ---\n".encode())
            self._aufraeumen()
        except Exception:
            if not self._fh or self._fh.closed:
                try:
                    self._oeffnen()
                except Exception:
                    self._fh = None

    def _aufraeumen(self):
        """Gepackte Staende aelter als behalten_tage entfernen."""
        grenze = datetime.datetime.now().timestamp() - self.behalten_tage * 86400
        try:
            for n in os.listdir(self.ordner):
                if not (n.startswith("suslik-") and n.endswith(".log.gz")):
                    continue
                p = os.path.join(self.ordner, n)
                if os.path.getmtime(p) < grenze:
                    os.remove(p)
        except Exception:
            pass

    def _pruefen(self):
        if self._fh is None:
            return
        if datetime.date.today() != self._tag:
            self._drehen("Tageswechsel")
        elif self._fh.tell() >= self.max_bytes:
            self._drehen("Groessengrenze")

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
            t = threading.Thread(target=self._schleife, args=(r, echt),
                                 name=f"logdatei-fd{fd}", daemon=True)
            t.start()
            self._faeden.append(t)
        return self

    def ordner_setzen(self, ordner):
        """Ordner nachreichen (nach dem Laden der Config): Datei anlegen,
        drehen und den Vorpuffer hineinschreiben."""
        with self._schloss:
            self.ordner = ordner
            try:
                self._oeffnen()
            except Exception:
                self._fh = None
                return self
            vor = b"".join(self._vor)
            self._vor = []
            self._vor_bytes = 0
        self._drehen("Dienststart")
        if vor and self._fh:
            try:
                self._fh.write(vor)
            except Exception:
                pass
        return self

    def _schleife(self, lese, ziel):
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
                pass
            with self._schloss:                   # 2. dann in die Datei
                if self.ordner is None:
                    if self._vor_bytes < self.VORPUFFER:
                        self._vor.append(brocken)
                        self._vor_bytes += len(brocken)
                    continue
                if self._fh is None:
                    continue
                try:
                    self._fh.write(brocken)
                    self._pruefen()
                except Exception:
                    try:
                        self._fh.close()
                    except Exception:
                        pass
                    self._fh = None               # Datei aufgeben, Dienst laeuft


    def zuruecksetzen(self):
        """Vor einem os.execv: den Tee ABBAUEN — die geretteten Original-
        Deskriptoren zurueck auf 1/2, Datei schliessen.

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
        try:
            if self._fh:
                self._fh.close()
        except Exception:
            pass
        self._fh = None


def dateien(ordner):
    """Alle Logstuecke, juengstes zuerst -> [(name, bytes, mtime)]."""
    aus = []
    try:
        for n in sorted(os.listdir(ordner), reverse=True):
            if n == DATEI or (n.startswith("suslik-") and n.endswith(".log.gz")):
                p = os.path.join(ordner, n)
                aus.append((n, os.path.getsize(p), os.path.getmtime(p)))
    except Exception:
        pass
    return aus


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
