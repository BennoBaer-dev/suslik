"""stderr-Sieb gegen die eine bekannte Treiber-Flutzeile (User-Auftrag 24.08.,
"log ist immer noch voller fehlermeldungen": 64 identische rote Zeilen je Start).

Die Modell-Bibliothek baut ihre Sessions ohne Thread-Deckel; onnxruntime schreibt
dann je Thread eine [E:onnxruntime ... pthread_setaffinity_np failed]-Zeile auf
stderr — harmlos (die Rechnung stimmt, nur das Kern-Pinning entfaellt), aber sie
begraebt jede echte Meldung. Abstellen an der Quelle geht nicht ohne den
Klassen-Monkeypatch, den face_audit._ort_thread_opts seit der 0.1.0.13-Regression
ausdruecklich verbietet. Deshalb DIESES Muster (wie der abgenommene
det-size-stdout-Filter aus .335): ein fd-2-Sieb, das AUSSCHLIESSLICH die exakte
Musterzeile verwirft und ZAEHLT — alles andere fliesst byte-treu durch, und der
Aufrufer druckt EINE ehrliche Summenzeile statt der Flut.

Grenzen, ehrlich: das Sieb haengt am fd 2 des Prozesses, Kind-Prozesse erben es
(gewollt: auch deren Bau-Zeilen sind dieselbe Klasse); im Worker zeigen Job-Fenster
per dup2 auf die Job-Logdatei, dort greift es bewusst nicht (Job-Logs sind
Diagnose-Material, kein Docker-Log). Stirbt der Sieb-Thread, laeuft stderr ueber
den geretteten Original-fd weiter — Verlust ist ausgeschlossen, schlimmstenfalls
kommt die Flut zurueck."""

import os
import threading

_MUSTER = b"pthread_setaffinity_np failed"


class Sieb:
    def __init__(self, echt_fd):
        self.echt_fd = echt_fd      # geretteter Original-stderr (Docker-Log)
        self.anzahl = 0             # verworfene Musterzeilen seit Prozessstart

    def summe(self):
        return self.anzahl


def installieren():
    """fd 2 durch das Sieb leiten. -> Sieb-Objekt (anzahl waechst live).
    Idempotenz ist Aufgabe des Aufrufers (einmal, frueh in main())."""
    echt = os.dup(2)
    os.set_inheritable(echt, False)
    r, w = os.pipe()
    os.set_inheritable(r, False)
    sieb = Sieb(echt)
    os.dup2(w, 2)
    os.close(w)

    def _lauf():
        rest = b""
        while True:
            try:
                stueck = os.read(r, 65536)
            except OSError:
                break
            if not stueck:
                break
            rest += stueck
            while b"\n" in rest:
                zeile, rest = rest.split(b"\n", 1)
                if _MUSTER in zeile:
                    sieb.anzahl += 1
                else:
                    try:
                        os.write(echt, zeile + b"\n")
                    except OSError:
                        return
            # Teilzeile ohne Newline groesser 64k: durchreichen statt horten
            if len(rest) > 65536:
                try:
                    os.write(echt, rest)
                except OSError:
                    return
                rest = b""

    t = threading.Thread(target=_lauf, name="stderr-sieb", daemon=True)
    t.start()
    return sieb
