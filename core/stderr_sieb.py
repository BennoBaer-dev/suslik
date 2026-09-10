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
kommt die Flut zurueck.

.525 (Prod-Pruefung 10.09., Feldnutzer-Falle 1): DASSELBE Sieb traegt jetzt auch
fd 1. Anlass ist die zweite bekannte Bibliotheks-Flut — der insightface-INIT
druckt je Modelldatei des buffalo_l-Bundles eine Zeile
`Applied providers: ['CPUExecutionProvider'] …` auf STDOUT (insightface
model_zoo.ModelRouter.get_model), dazu `find model:`, `model ignore:` und
`set det-size:`. Fuenf CPU-Zeilen direkt hinter der Startzusage "device engaged"
lesen sich fuer einen Feldnutzer wie "laeuft doch nicht auf der GPU" — dabei sind
das die WEGWERF-Sessions des Detektor-Bundles, die `face_audit.Embedder._to_backend`
unmittelbar danach durch die echten Backend-Sessions ersetzt.

WARUM HIER UND NICHT AN DER QUELLE (Muster `face_audit.set_det_size`, .335):
an der Quelle (redirect_stdout um den insightface-Init) waere die Ausgabe in ALLEN
Prozessen weg — auch in den Job-Fenstern des Workers, und genau die zaehlt das
Gate (`grep -c "Applied providers"` auf `analyze.log` = CPU-Sessions je Lauf; und
die S5-Stufe liest daraus den gebundenen Provider). Das Sieb endet dagegen exakt
an der Grenze, die dieses Modul fuer fd 2 schon zieht: Dienst-Log ja, Job-Log
nein. Der Nutzer sieht die Flut nicht mehr, die Messung behaelt ihr Material.

DER DEBUG-SCHALTER: das fd-1-Sieb fragt vor jeder Zeile den `durchlass`-Griff des
Aufrufers (verifyd reicht den vorhandenen `debug`-Schalter durch). Steht debug,
wird NICHTS gefiltert — dieselbe Zusage wie bei allen .511-Zeilen."""

import os
import threading

_MUSTER = b"pthread_setaffinity_np failed"

# .525: die informativen Zeilen des insightface-INITS auf stdout. Bewusst NICHT
# dabei sind `model not recognized:` und `duplicated model task type` — die
# melden ein echtes Problem im Modellordner und muessen sichtbar bleiben.
INSIGHTFACE_INIT = (b"find model:", b"model ignore:", b"set det-size:")
# Die Provider-Zeile wird nur verworfen, wenn die Liste GENAU die eine
# CPU-Hilfssession ist (insightface druckt sie woertlich so:
# `Applied providers: ['CPUExecutionProvider'], with options: …`). Jede andere
# Liste ist eine Aussage darueber, worauf etwas gebunden hat, und bleibt stehen
# — deshalb der exakte Praefix-Vergleich statt einer Aufzaehlung fremder
# Rechenwege (die waere ein zweites Varianten-Literal, s. Deckungs-Vertrag).
_PROVIDER_CPU = b"Applied providers: ['CPUExecutionProvider']"


def insightface_init_zeile(zeile):
    """Ist `zeile` (bytes, ohne \\n) reines insightface-Init-Geschwaetz?
    -> bool. EINE Stelle fuer die Entscheidung, damit die Probe genau das
    pruefen kann, was der Sieb-Faden tut."""
    if zeile.startswith(_PROVIDER_CPU):
        return True
    return any(zeile.startswith(m) for m in INSIGHTFACE_INIT)


class Sieb:
    def __init__(self, echt_fd):
        self.echt_fd = echt_fd      # geretteter Original-Deskriptor (Docker-Log)
        self.anzahl = 0             # verworfene Musterzeilen seit Prozessstart

    def summe(self):
        return self.anzahl


def installieren(fd=2, passt=None, durchlass=None):
    """`fd` durch das Sieb leiten. -> Sieb-Objekt (anzahl waechst live).
    Idempotenz ist Aufgabe des Aufrufers (einmal, frueh in main()).

    passt(zeile: bytes) -> bool: was verworfen wird. Vorgabe ist die
      Treiber-Flutzeile auf fd 2 (Verhalten der Fassungen vor .525).
    durchlass() -> bool: sagt True, bleibt das Sieb fuer diese Zeile AUS
      (nichts wird verworfen). Vorgabe: keiner, das Sieb siebt immer.
      Ausnahmen im Griff werden geschluckt und gelten als 'nicht offen' —
      ein Diagnose-Schalter darf das Log nicht kosten."""
    if passt is None:
        def passt(zeile):
            return _MUSTER in zeile
    echt = os.dup(fd)
    os.set_inheritable(echt, False)
    r, w = os.pipe()
    os.set_inheritable(r, False)
    sieb = Sieb(echt)
    os.dup2(w, fd)
    os.close(w)

    def _offen():
        """Sieb aus? Ein kaputter Griff darf nie das Log kosten."""
        if durchlass is None:
            return False
        try:
            return bool(durchlass())
        except Exception:
            return False

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
                if passt(zeile) and not _offen():
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

    t = threading.Thread(target=_lauf, name=f"sieb-fd{fd}", daemon=True)
    t.start()
    return sieb
