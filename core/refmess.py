"""core/refmess — der MESS-SIDECAR des Gesichtskatalogs (Stufe B, .511).

WOZU: die Bestands-QS (`anlernen.pruefe_referenzen`) hat bis .510 bei JEDEM Lauf
jede Referenzdatei neu gemessen — auf der Werkbank 1,10 s je Bild ohne
A2-Beiwert, 674 s von 872 s Gesamtlauf (Inventur §4.2). Dabei liefert dieselbe
Datei mit demselben Modell immer dasselbe Ergebnis. Dieses Modul haelt die teuren
Messwerte je Bild fest, damit ein zweiter Lauf nur noch LIEST.

ABGRENZUNG zu `refs_meta.jsonl` (bewusst zwei Dateien, Entscheid des Bauplans):
`refs_meta.jsonl` ist das HERKUNFTS-JOURNAL — append-only, last-wins, es sagt
WOHER eine Referenz kommt und ob sie noch aktiv ist (Tombstones!). Es bleibt
unangetastet Journal. Der Sidecar hier ist ein CACHE: ableitbar, jederzeit
loeschbar, ohne Verlust neu berechenbar. Ein Cache in einem Journal waere weder
das eine noch das andere (die Frage stand als Punkt 8 in Inventur §6).

WAS DRIN STEHT (je Bild): die Werte, die eine DATEI-MESSUNG kostet —
kante / sharp / norm / pose / fiqa_t / empf / wh — dazu die aufgeloeste Kamera.
NICHT drin steht das EMBEDDING: das lebt im refcache (`clips/refcache.npz`), der
es seit .511 zeilengenau ueber `§rows` zuordnet, bzw. im A2-Beiwert. Ein zweiter
Vektor-Speicher waere eine dritte Wahrheit ueber dasselbe.

FRISCHE-ANKER = (Dateigroesse, mtime_ns) + Modell-Kennung.
  Gewaehlt statt md5, mit Begruendung: (a) es ist der Anker, den das Haus fuer
  genau diese Frage schon fuehrt — `anlernen._cc_passt` prueft den Crop-Cache
  seit .3xx mit mtime+Groesse; zwei Anker-Bauarten fuer dieselbe Frage waeren ein
  K3-Verstoss. (b) Ein md5 ueber 1229 Referenzen kostet je Lauf das vollstaendige
  LESEN aller Dateien (~60 MB) — genau die Kosten, die dieser Sidecar abschaffen
  soll. (c) `os.stat` kostet nichts und faengt den realen Fall: Referenzbilder
  werden geschrieben, nie in-place editiert.
  EHRLICHE GRENZE, benannt statt versteckt: eine Datei, die extern durch eine
  ANDERE mit EXAKT gleicher Groesse UND erhaltener mtime ersetzt wird (rsync -t
  mit gleicher Groesse, tar mit -m), gilt weiter als frisch und behaelt ihre
  alten Werte. Umbenennen, neu schreiben, Groesse aendern, Modellwechsel — all
  das faellt auf. Wer den Verdacht hat, loescht den Sidecar: er baut sich beim
  naechsten Lauf neu auf.

SCHREIBWEG: immer die ganze Karte, atomar ueber `core.atomar` (mkstemp im
Zielordner, fsync, 0644, replace) — nie eine halbe Datei unter dem Zielnamen.
Zwischenstaende werden waehrend eines langen Erstlaufs mitgeschrieben
(`FLUSH_JE`), damit ein Abbruch nach 20 Minuten nicht 20 Minuten kostet.
"""
import json
import os
import re

from core import atomar as _atomar

SCHEMA = 1
DATEI = "refs_mess.json"
FLUSH_JE = 50          # Zwischenstand alle N frisch gemessenen Bilder

# DECKUNGS-VERTRAG der Sidecar-Zeile (QS-Ebenen-Regel: Aufzaehlung mit Vertrag
# statt Streu-Logik) — die EINE Liste der Felder, die eine DATEI-MESSUNG
# erzeugt und die ein Cache-Treffer zurueckliefert. Sie hat genau zwei
# Verbraucher in `anlernen.lade_master_bilder`: den Schreiber (Mess-Zweig) und
# den Leser (Cache-Zweig). Waeren das zwei getrennte Aufzaehlungen, kostete ein
# neues Feld genau den Fehler, gegen den dieser Sidecar gebaut ist: geschrieben,
# aber nie gelesen — der Lauf misst still weiter, und niemand merkt es an einer
# falschen Zahl, nur an der Zeit. Das Gate haelt beide dagegen.
# NICHT hier drin: `anker`, `camera`, `kam_stand`, `eid` — die haengen nicht an
# der Messung (der Anker IST die Frischefrage, die Kamera kommt aus Meta/Akte).
MESSFELDER = ("wh", "defekt", "gesicht", "kante", "sharp", "pose", "norm",
              "fiqa_t", "empf", "guete_da", "modell", "quelle", "ts")

# Kamera-Nachtrag (User-Entscheid Q2, 08.09.): wo `refs_meta` keine Kamera
# fuehrt, wird sie aus dem `eid`-Feld ueber die LOKALEN Akten aufgeloest. Die
# Reihenfolge ist die Fund-Reihenfolge; die erste Antwort gewinnt (die Akte ist
# je eid last-wins geschrieben, die Kamera eines Ereignisses aendert sich nicht).
_EID_CAM = re.compile(r'"eid":\s*"([^"]+)"')
_CAM = re.compile(r'"camera":\s*"([^"]*)"')


def pfad(master_dir):
    return os.path.join(master_dir, DATEI)


def anker(bild_pfad):
    """(groesse, mtime_ns) der Datei -> Frische-Anker; None wenn nicht lesbar."""
    try:
        st = os.stat(bild_pfad)
    except OSError:
        return None
    return [int(st.st_size), int(st.st_mtime_ns)]


def lesen(master_dir):
    """Den Sidecar laden -> (bilder, kopf). `bilder` ist {person: {datei: zeile}},
    leer bei fehlender/unlesbarer/fremder Datei — ein kaputter Cache darf nie
    einen Lauf abbrechen, er kostet dann nur eine Neumessung."""
    try:
        with open(pfad(master_dir), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:                                    # noqa: BLE001
        return {}, {}
    if not isinstance(d, dict) or int(d.get("schema") or 0) != SCHEMA:
        return {}, {}
    b = d.get("bilder")
    if not isinstance(b, dict):
        return {}, {}
    return b, {k: v for k, v in d.items() if k != "bilder"}


def schreiben(master_dir, bilder, kopf=None):
    """Die ganze Karte atomar schreiben. Wirft NICHT: der Sidecar ist eine
    Beschleunigung, sein Ausfall darf keinen QS-Lauf kosten (er meldet sich
    aber, sonst waere der naechste Lauf still wieder teuer)."""
    d = {"schema": SCHEMA, **(kopf or {}), "bilder": bilder}
    try:
        _atomar.schreiben(pfad(master_dir),
                          lambda f: json.dump(d, f, ensure_ascii=False))
        return True
    except Exception as e:                               # noqa: BLE001
        print(f"reference measurement store not written: "
              f"{type(e).__name__}: {e}", flush=True)
        return False


def frisch(zeile, ank, modell=None):
    """Gilt diese Sidecar-Zeile noch fuer DIESE Datei? (Anker + optional Modell)

    `modell=None` fragt nur den Datei-Anker — fuer die modell-unabhaengigen
    Felder (`wh`, `camera`). Mit Modell-Kennung wird zusaetzlich verlangt, dass
    die Messung mit DEM Erkennungsmodell entstand, das jetzt laeuft: die
    Feature-Norm haengt daran, und das aligned 112er (Grundlage von `fiqa_t`)
    an der Detektion desselben Laufs. Konservativ mit Absicht — lieber einmal
    zu viel messen als eine Zahl aus einer anderen Modellwelt weiterreichen."""
    if not isinstance(zeile, dict) or not ank:
        return False
    a = zeile.get("anker")
    if not (isinstance(a, list) and len(a) == 2
            and int(a[0]) == int(ank[0]) and int(a[1]) == int(ank[1])):
        return False
    if modell is not None and str(zeile.get("modell") or "") != str(modell):
        return False
    return True


def akten_anker(data_dir):
    """Frische-Anker der Deckungs-Akte (state/deckung.jsonl) — der Stellvertreter
    fuer 'die lokalen Akten haben sich geaendert'. Nur damit ein Bild, dessen
    Kamera schon einmal ERFOLGLOS gesucht wurde, die 0,9-s-Kartenbildung nicht
    bei JEDEM Lauf erneut ausloest, sondern erst wenn die Akte gewachsen ist.
    Die Archiv-Dateien wachsen nur bei der Rotation, und die schreibt dieselbe
    Akte neu — der eine Anker deckt beide."""
    return anker(os.path.join(data_dir, "state", "deckung.jsonl"))


def kamera_karte(data_dir, eids):
    """{eid: kamera} fuer die gefragten eids aus den LOKALEN Akten.

    Quellen (alle ohne Netz, alle in jeder Installation vorhanden):
      state/deckung.jsonl            die laufende Ereignis-Akte
      state/archiv/deckung_*.jsonl   deren Monats-Archive (Rotation AP7)
      learn/gesichter.jsonl          der Unbekannt-Pool (Kamera je Gesicht)

    BEWUSST OHNE FRIGATE-API: `GET /api/events/<eid>` kaeme an mehr Kameras
    heran, macht aus einem reinen Mess-Lauf aber einen Netz-Lauf (fremder
    Dienst, Auth, Timeouts, Frigate-Schoner) — und fuer alte Ereignisse hat
    Frigate den Eintrag oft selbst nicht mehr. Was lokal nicht auffindbar ist,
    bleibt ohne Kamera und faellt auf die GLOBALE Latte zurueck (User-Entscheid
    Q2). Gemessen am Feldtester-Bestand: 404 von 463 kameralosen Referenzen mit
    eid werden so aufgeloest, die Deckung steigt von 692/1229 auf 1096/1229.

    Gelesen wird ZEILENWEISE mit Regex statt json.loads: 64 568 Zeilen kosten
    so 0,10 s statt 0,92 s, und gebraucht werden genau zwei Felder."""
    gesucht = set(eids or ())
    if not gesucht:
        return {}
    aus = {}
    quellen = [os.path.join(data_dir, "state", "deckung.jsonl")]
    adir = os.path.join(data_dir, "state", "archiv")
    try:
        quellen += sorted(os.path.join(adir, f) for f in os.listdir(adir)
                          if f.startswith("deckung_") and f.endswith(".jsonl"))
    except OSError:
        pass
    quellen.append(os.path.join(data_dir, "learn", "gesichter.jsonl"))
    for q in quellen:
        try:
            with open(q, encoding="utf-8", errors="replace") as f:
                for zeile in f:
                    m = _EID_CAM.search(zeile)
                    if m is None or m.group(1) not in gesucht or m.group(1) in aus:
                        continue
                    c = _CAM.search(zeile)
                    if c is not None and c.group(1):
                        aus[m.group(1)] = c.group(1)
        except OSError:
            continue
        if len(aus) == len(gesucht):
            break
    return aus
