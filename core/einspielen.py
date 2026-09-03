"""core/einspielen — Testbett-Einspielung: EIN Szenario gezielt durch die
Erkennung EINER Kamera schicken (.416, User-Go 03.09.2026).

WOFUER: Beim Nachstellen eines fremden Systems (Klon-Testbett) muss man ein
BESTIMMTES Ereignis unter einem BESTIMMTEN Kameranamen durch die Erkennung
schicken koennen — ohne beim Original etwas auszuloesen und ohne einen
zweiten Erkennungspfad zu bauen. Quelle ist wahlweise ein echtes Event der
VERBUNDENEN Frigate (on demand statt Dauer-Poll, schont die Leitung) oder ein
Clip, der schon unter data_dir liegt.

DER TRICK, DER DEN EINGRIFF KLEIN HAELT (Muster core/dateiquelle): eine
Event-ID mit dem Praefix `einspiel-` hat drueben KEINE Entsprechung. Genau
zwei Haken lesen dieses Praefix:

  A  verifyd.Service.process()   — die Metadaten kommen aus
     <data_dir>/einspielen/<eid>.json statt aus /api/events/<id>;
  B  core.frames.clip_holen()    — der Clip kommt aus
     <data_dir>/einspielen/<eid>.mp4 statt aus einem Frigate-GET.

Alles danach ist der NORMALE Weg: Event-Queue, Kamera-/Zonen-Filter,
live_only-Uebersprung, Worker-Analyse, Akte und Today unter der eingesetzten
Kamera. Es entsteht KEIN zweiter Erkennungspfad — genau das ist der Zweck.

GRENZEN, ehrlich:
- Der Ordner <data_dir>/einspielen/ wird NICHT automatisch geraeumt. Die
  Clip-Retention raeumt <data_dir>/clips, nicht diese Vorlagen; wer aufraeumt,
  loescht dort von Hand (oder ueber den Support-Lesebaum sichtbar).
- Die Metadaten sind eine DATEI. Wer sie von Hand editiert, aendert damit,
  was die Erkennung sieht. meta_lesen() liest deshalb streng (dict, camera
  als nicht-leere Zeichenkette) und liefert sonst None — der Haken bricht
  dann LAUT mit einer Logzeile ab, statt mit halben Angaben weiterzulaufen.
- Geschrieben wird ausschliesslich unter data_dir. Richtung Frigate ist
  dieser Weg rein LESEND (ein GET auf /api/events/<id> und der normale
  Clip-Zug) — die Instanz drueben merkt nichts davon.
"""
import json
import os
import re
import secrets
import shutil
import time

from core import atomar as _atomar
# Dieselbe Kamera-Namensregel und derselbe ffprobe-Griff wie bei der
# Datei-Einspeisung — kein zweites verstreutes Literal, keine zweite
# Messstelle (CLAUDE.md: zentrale Quelle statt Streu-Literal).
from core.dateiquelle import KAMERA_RE, _ffprobe

PRAEFIX = "einspiel-"
ORDNER = "einspielen"
# Die eid landet in Dateinamen und muss zu registry.EID_RE ([\w.\-]+) passen,
# damit ALLE Routen (Event-Seite, Crops, Logs) sie tragen.
EID_RE = re.compile(r"^einspiel-[\w.\-]{1,72}$")
DAUER_FALLBACK_S = 60.0    # ohne lesbare ffprobe-Dauer: eine Minute annehmen
VORLAUF_S = 25.0           # das eingespielte Ereignis liegt schon hinter uns
TOP_SCORE = 0.9            # ueber jeder ueblichen no_person-Latte
LABEL = "person"
# FENSTER-WEG (User 03.09. abends: "ab einem Zeitfenster, zum Beispiel 8 Uhr,
# die naechsten 5 Personen-Events von dieser Kamera"): bewusst GEDECKELT,
# damit ein Support-Aufruf nie einen ganzen Tag Events in die Queue kippt.
FENSTER_MAX_DEFAULT = 5    # "die naechsten 5" — der genannte Normalfall
FENSTER_DECKEL = 20        # harte Obergrenze je Aufruf
FENSTER_SUCHLIMIT = 100    # wie viele Events die Frigate-Abfrage maximal liefert


def ist_einspiel(eid):
    """DIE eine Praefix-Frage. Beide Haken stellen sie hier — ein zweites
    startswith() irgendwo im Code waere genau das Streu-Literal, das der
    K3-Klasse (Erweiterung erreicht nicht alle Stellen) den Weg bahnt."""
    return str(eid or "").startswith(PRAEFIX)


def eid_ok(eid):
    """Taugt diese ID als Dateiname unter data_dir? Verhindert, dass eine
    von aussen gereichte 'einspiel-../..'-ID zu einem Pfad ausserhalb des
    Injektor-Ordners wird."""
    e = str(eid or "")
    return bool(EID_RE.match(e)) and ".." not in e


def neue_eid():
    """`einspiel-<epoch>-<kurz>` — sortierbar nach Zeit, kollisionsfrei
    durch den Zufallsteil (zwei Einspielungen in derselben Sekunde)."""
    return f"{PRAEFIX}{int(time.time())}-{secrets.token_hex(3)}"


def ordner(data_dir):
    return os.path.join(str(data_dir or ""), ORDNER)


def meta_pfad(data_dir, eid):
    """-> Pfad der Metadaten-Datei oder None (unzulaessige ID / kein
    data_dir). None ist fuer den Aufrufer 'gibt es nicht'."""
    if not data_dir or not eid_ok(eid):
        return None
    return os.path.join(ordner(data_dir), f"{eid}.json")


def clip_pfad(data_dir, eid):
    if not data_dir or not eid_ok(eid):
        return None
    return os.path.join(ordner(data_dir), f"{eid}.mp4")


def meta_lesen(data_dir, eid):
    """Injektor-Metadaten lesen -> dict wie ein /api/events/<id>-Objekt,
    oder None. WIRFT NIE: der Haken A sitzt mitten im Event-Weg, ein
    kaputtes Handeditat darf dort keinen Traceback ausloesen, sondern muss
    als 'nichts zu tun' mit Logzeile enden."""
    p = meta_pfad(data_dir, eid)
    if not p:
        return None
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    if not isinstance(d.get("camera"), str) or not d["camera"].strip():
        return None                      # ohne Kamera gibt es keinen Weg
    d["id"] = str(eid)                   # die ID gehoert dem DATEINAMEN,
    return d                             # nie dem (editierbaren) Inhalt


def bereitstellen(quelle, ziel):
    """Eine Videodatei unter `ziel` bereitstellen — HARDLINK, wenn moeglich
    (gleiche Platte, kein zweiter Datenblock), sonst Kopie. Immer ueber eine
    eindeutige tmp-Datei im Zielordner + os.replace: nie ein halbes Video
    unter dem Zielnamen, nie zwei Schreiber auf demselben tmp-Namen
    (core/atomar). Der Hardlink ist hier ungefaehrlich, weil beide Namen nur
    ATOMAR ersetzt und nie in place beschrieben werden."""
    os.makedirs(os.path.dirname(ziel) or ".", exist_ok=True)
    fd, tmp = _atomar.tmp_oeffnen(ziel, suffix=".mp4")
    os.close(fd)
    os.unlink(tmp)                       # link/copyfile brauchen den Namen frei
    try:
        try:
            os.link(quelle, tmp)         # gleicher Datenblock, kein Kopieren
        except OSError:                  # anderes Dateisystem, kein Hardlink
            shutil.copyfile(quelle, tmp)
            os.chmod(tmp, _atomar.MODUS)
        os.replace(tmp, ziel)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return ziel


def ablegen(data_dir, eid, meta, clip_quelle):
    """Metadaten + Clip als Injektor-Vorlage hinterlegen -> (meta_pfad,
    clip_pfad). Der CLIP zuerst, die Metadaten (atomar) zuletzt: so findet
    Haken A nie eine Metadaten-Datei, zu der noch kein Video gehoert."""
    mp, cp = meta_pfad(data_dir, eid), clip_pfad(data_dir, eid)
    if not mp or not cp:
        raise ValueError(f"unzulaessige Einspiel-ID: {eid!r}")
    bereitstellen(clip_quelle, cp)
    _atomar.json_schreiben(mp, meta)
    return mp, cp


def pfad_anker(data_dir, relpfad):
    """Einen vom Aufrufer genannten Clip-Pfad auf eine echte Datei UNTER
    data_dir abbilden (Muster core.support.baum_aufloesen). JEDER Ausbruch
    (fuehrender /, ../, Symlink nach draussen, Ordner statt Datei) endet als
    None; der Aufrufer antwortet darauf mit dem generischen 404 — nie mit
    einem Grund, sonst wird der Endpunkt zum Existenz-Orakel fuers
    Dateisystem."""
    if not data_dir:
        return None
    basis = os.path.realpath(data_dir)
    rel = str(relpfad or "")
    if not rel or rel.startswith("/") or "\x00" in rel:
        return None
    p = os.path.realpath(os.path.join(basis, rel))
    if not (p == basis or p.startswith(basis + os.sep)):
        return None
    return p if os.path.isfile(p) else None


def dauer_s(pfad):
    """Clip-Dauer in Sekunden -> float oder None (unlesbares Video)."""
    try:
        d = (_ffprobe(pfad) or {}).get("dauer_s")
        return float(d) if d else None
    except (TypeError, ValueError):
        return None


def meta_aus_clip(eid, kamera, dauer, jetzt=None):
    """Metadaten fuer einen LOKALEN Clip — so, wie Frigate ein
    Personen-Event beschreiben wuerde. Die Annahmen stehen hier an EINER
    Stelle (der Aufrufer loggt sie):
      label 'person'   — nur Personen-Events gehen diesen Weg,
      top_score 0.9    — ueber jeder ueblichen no_person-Latte,
      zones []         — der Clip gehoert zu keiner Zone der Ziel-Kamera;
                         hat die Kamera einen Zonen-Filter, ueberspringt
                         process() ihn folgerichtig (und sagt es in der Akte),
      sub_label None   — die Erkennung soll SELBST urteilen, nicht eine
                         mitgelieferte Behauptung bestaetigen,
      Zeitachse        — das Ereignis liegt gerade hinter uns:
                         end_time = jetzt - 25 s, start_time = end - Dauer."""
    t = float(jetzt if jetzt is not None else time.time())
    d = float(dauer or DAUER_FALLBACK_S)
    start = t - d - VORLAUF_S
    return {"id": str(eid), "camera": str(kamera), "label": LABEL,
            "sub_label": None, "start_time": start, "end_time": start + d,
            "zones": [], "has_clip": True, "data": {"top_score": TOP_SCORE},
            "quelle": "einspiel"}


def meta_aus_event(ev, eid, kamera):
    """Metadaten eines ECHTEN Frigate-Events unter neuer ID und neuer
    Kamera. Uebernommen wird alles Uebrige unveraendert (Zeitachse, Zonen,
    Scores) — geaendert werden genau drei Dinge, und jede Aenderung hat
    einen Grund:
      id       -> die neue Einspiel-ID (sonst kollidiert sie mit dem
                  Original in processed/Akte),
      camera   -> die Ziel-Kamera (das ist der ganze Zweck),
      sub_label-> None: Frigates Behauptung ueber die Person wird NICHT
                  mitgeschleppt. Sie wuerde sonst den Kamera-/Zonen-Filter
                  der Ziel-Kamera aushebeln (process(): 'not f_label') und
                  das Urteil gegen eine fremde Kamera-Wahrheit stellen."""
    d = dict(ev or {})
    d["id"] = str(eid)
    d["camera"] = str(kamera)
    d["sub_label"] = None
    if isinstance(d.get("data"), dict):
        d["data"] = {k: v for k, v in d["data"].items()
                     if k != "sub_label_score"}
    d["quelle"] = "einspiel"
    return d


def bestand(data_dir):
    """-> (anzahl, bytes) der hinterlegten Vorlagen. Fuer die Logzeile: der
    Ordner waechst mit jeder Einspielung und wird nicht automatisch
    geraeumt — das soll man sehen, nicht erst beim vollen Datentraeger."""
    n, b = 0, 0
    try:
        with os.scandir(ordner(data_dir)) as it:
            for e in it:
                if e.is_file(follow_symlinks=False):
                    n += 1
                    b += e.stat().st_size
    except OSError:
        return 0, 0
    return n, b
