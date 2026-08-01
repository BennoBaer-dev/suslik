"""core/lernlauf — Zustand des Anlern-Laufs (E1, Lern-Bauplan; Konzept §3-§6).

Zwei Persistenzen, beide unter <data_dir>/state/:
  lernlauf.json  EIN Lauf-Zustand (Wizard-Parameter, Phase, Fortschritts-Zaehler,
                 Resume-Punkt) — atomar geschrieben (tmp+fsync+rename, das
                 placement.json-/Store-Muster), damit ein Absturz nie einen halben
                 Zustand hinterlaesst.
  anker.jsonl    Anker-Datensaetze (Konzept §5, VOLLSTAENDIGES Schema) — JSONL;
                 jeder Datensatz wird VOR dem Schreiben validiert (ein
                 Schema-Drift faellt sofort, nicht erst beim Leser). Seit E4a
                 gibt es GENAU EINEN Update-Weg fuer Einzel-Saetze
                 (anker_aktualisieren, in place + atomar + store_lock) — die
                 Benennung ist der erste Read-Modify-Write-Schreiber dieses
                 Stores (Widerleger-MUSS 01.08.).

Kontrakt wie auftritte.py: reine Funktionen, Pfade/Daten als Parameter, kein
Dienst-Import. KEINE anlagenspezifischen Konstanten (Allgemeinheits-Wache §2.4b) —
Schwellen/Benchmarks kommen vom Aufrufer aus Config/Messung.
"""
import json
import time
import os
import tempfile

SCHEMA_VERSION = 1

# Konzept §3: die Phasen-Kette des Laufs (P2b/Anzeige haengt sich hieran).
PHASEN = ("vorbereitung", "ernte", "anker", "benennung", "neben_ansichten",
          "ganzkoerper", "uebernahme", "fertig")

# Konzept §5: Pflichtfelder des Anker-Datensatzes (Typ-Skelett; None = beliebiger Typ).
_ANKER_PFLICHT = {
    "anker_id": str, "person": None, "status": str, "mitglieder": list,
    "durchgaenge": list, "qualitaet": dict, "quell_videos": list,
    "pose_abdeckung": dict, "mehrdeutig": list, "ganzkoerper": list,
    "groesse_bytes": int, "lauf": dict,
    # E4a-Datengrundlage (Widerleger-MUSS 01.08.): der Cluster-Zentroid wird
    # persistiert statt verworfen — Personen-Ebenen-Dedup und U-Zuordnung
    # rechnen rein lesend. Alt-Zeilen ohne das Feld bleiben lesbar (Pruefung
    # laeuft nur am Schreibweg); das UI weist dort "duplicate check
    # unavailable" aus, nie stumm "0 Duplikate".
    "zentroid": list,
}
_MITGLIED_PFLICHT = ("event", "datei", "t", "kamera", "front", "sharp", "det",
                     "kante", "pose",
                     # E4a: physischer Dedup-Schluessel (kamera+bbox, cross-event
                     # wie stuetz_phys) + Embedding fuer Fast-Duplikat/Vorschau —
                     # die Ernte-Kandidaten tragen alle drei Felder bereits.
                     "bbox", "ts", "emb")
ANKER_STATUS = ("unbenannt", "benannt", "uebernommen")

# E4a Namens-Ebene (Widerleger-MUSS): EINZIGE Namensquelle des Projekts —
# anlernen/verifyd ziehen bei ihrer naechsten Anfassung hierher nach, kein
# fuenftes Streu-Regex. Normalform: trimmen + Mehrfach-Leerzeichen buendeln.
PERSON_RE = r"^[\w \-]{2,40}$"


def person_norm(s):
    return " ".join(str(s or "").split())


def _pfad(data_dir, name):
    return os.path.join(data_dir, "state", name)


def lauf_lesen(data_dir):
    """Lauf-Zustand oder None (kein Lauf). Kaputte Datei -> None + Fehlertext
    (der Aufrufer entscheidet laut; NIE stilles Weiterlaufen auf halbem Zustand)."""
    p = _pfad(data_dir, "lernlauf.json")
    if not os.path.exists(p):
        return None, None
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("schema") != SCHEMA_VERSION:
            return None, f"lernlauf.json schema {d.get('schema')!r} != {SCHEMA_VERSION}"
        if d.get("phase") not in PHASEN:
            return None, f"unbekannte phase {d.get('phase')!r}"
        return d, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def lauf_schreiben(data_dir, zustand):
    """Atomar (tmp + fsync + rename ins selbe Verzeichnis). zustand MUSS phase
    aus PHASEN tragen; schema wird gesetzt."""
    if zustand.get("phase") not in PHASEN:
        raise ValueError(f"phase {zustand.get('phase')!r} nicht in {PHASEN}")
    zustand = dict(zustand, schema=SCHEMA_VERSION)
    p = _pfad(data_dir, "lernlauf.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), prefix=".lernlauf-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(zustand, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return p


def anker_pruefen(a):
    """Schema-Validierung eines Anker-Datensatzes (Konzept §5) -> Fehlerliste
    (leer = gueltig). Prueft Pflichtfelder+Typen, status-Werte, Mitglieds-Felder
    und die ECHTE-Vorzeichen-Pose (Liste [pitch, yaw, roll] aus Zahlen — die
    analyze.py:242-Falle [Betraege/vertauscht] soll hier frueh auffallen: drei
    nicht-negative Ganzzahl-Betraege in Folge sind verdaechtig, echte Winkel
    tragen Vorzeichen; das ist eine WARNUNG, kein Fehler)."""
    fehler = []
    for k, typ in _ANKER_PFLICHT.items():
        if k not in a:
            fehler.append(f"feld fehlt: {k}")
        elif typ is not None and not isinstance(a[k], typ):
            fehler.append(f"feld {k}: {type(a[k]).__name__} statt {typ.__name__}")
    if a.get("status") not in ANKER_STATUS:
        fehler.append(f"status {a.get('status')!r} nicht in {ANKER_STATUS}")
    if a.get("status") == "unbenannt" and a.get("person") is not None:
        fehler.append("status unbenannt aber person gesetzt")
    # E4a (Widerleger-MUSS): die Wache greift in BEIDE Richtungen — benannt/
    # uebernommen verlangt einen gueltigen Namen in Normalform, nicht nur
    # unbenannt verbietet einen.
    if a.get("status") in ("benannt", "uebernommen"):
        import re as _re
        p = a.get("person")
        if not (isinstance(p, str) and person_norm(p)
                and _re.match(PERSON_RE, person_norm(p))):
            fehler.append("status benannt aber person leer/ungueltig")
    for i, m in enumerate(a.get("mitglieder") or []):
        for k in _MITGLIED_PFLICHT:
            if k not in m:
                fehler.append(f"mitglied[{i}]: feld fehlt: {k}")
        pose = m.get("pose")
        if not (isinstance(pose, (list, tuple)) and len(pose) == 3
                and all(isinstance(x, (int, float)) for x in pose)):
            fehler.append(f"mitglied[{i}]: pose muss [pitch, yaw, roll] aus Zahlen sein")
    return fehler


def benannte_zaehlen(data_dir, lauf_id):
    """Zeilen DIESES Laufs mit Nutzer-Benennung (status != unbenannt) — Grundlage
    des Resume-/Abbruch-Schutzes (E4a). Unlesbare Zeilen zaehlen nicht (sie
    tragen beweisbar keine Benennung, die verloren gehen koennte)."""
    p = _pfad(data_dir, "anker.jsonl")
    n = 0
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for zeile in f:
                try:
                    d = json.loads(zeile)
                except Exception:
                    continue
                if ((d.get("lauf") or {}).get("lauf_id") == lauf_id
                        and d.get("status") not in (None, "unbenannt")):
                    n += 1
    return n


def anker_aktualisieren(data_dir, anker_id, **felder):
    """E4a-Schreibweg (Widerleger-MUSS): GENAU EIN Satz in state/anker.jsonl in
    place ersetzen — nie anhaengen (anker_id bleibt eindeutig), atomar
    (mkstemp+os.replace) und UNTER store_lock; unlesbare Zeilen werden roh
    weitergefuehrt (dieselbe .83-Regel wie anker_lauf_schreiben). Der geaenderte
    Satz wird VOR dem Schreiben validiert (anker_pruefen; person laeuft durch
    person_norm). KeyError, wenn die anker_id nicht existiert.
    -> der aktualisierte Satz (dict)."""
    p = _pfad(data_dir, "anker.jsonl")
    if "person" in felder and felder["person"] is not None:
        felder["person"] = person_norm(felder["person"])
    with store_lock(data_dir):
        if not os.path.exists(p):
            raise KeyError(f"anker.jsonl fehlt — {anker_id} nicht aktualisierbar")
        zeilen, neu, gefunden = [], None, False
        with open(p, encoding="utf-8") as f:
            for zeile in f:
                z = zeile.rstrip("\n")
                if not z.strip():
                    continue
                try:
                    d = json.loads(z)
                except Exception:
                    zeilen.append(z)               # unlesbar => roh erhalten
                    continue
                if d.get("anker_id") == anker_id:
                    gefunden = True
                    d.update(felder)
                    fehler = anker_pruefen(d)
                    if fehler:
                        raise ValueError(f"{anker_id}: " + "; ".join(fehler))
                    neu = d
                    zeilen.append(json.dumps(d, ensure_ascii=False, allow_nan=False))
                else:
                    zeilen.append(z)
        if not gefunden:
            raise KeyError(f"anker_id {anker_id} nicht in anker.jsonl")
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), prefix=".anker.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("\n".join(zeilen) + "\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    return neu


def store_lock(data_dir):
    """.87 (Forensik-Fund 5/6): flock-Sidecar um JEDEN Store-Zugriff der Klasse
    lesen+mischen+schreiben bzw. loeschen — lauf_fortschreiben war ein ungesichertes
    Read-Modify-Write ueber den KOMPLETTEN Store (Interleave zweier Threads konnte
    einen frisch angelegten Lauf mit dem alten Zustand ueberschreiben; der Abbruch
    konnte ins Schreib-Fenster eines Arbeits-Threads fallen und als Zombie
    wiederauferstehen). Context-Manager; die Lock-Datei lebt neben dem Store."""
    import contextlib
    import fcntl

    @contextlib.contextmanager
    def _cm():
        p = _pfad(data_dir, "lernlauf.lock")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    return _cm()


def lauf_fortschreiben(data_dir, **updates):
    """Teil-Update des Lauf-Zustands (liest, mischt, schreibt atomar UNTER store_lock).
    fortschritt-Dicts werden GEMISCHT statt ersetzt; .87: ein fortschritt-Wert None
    LOESCHT den Schluessel (Forensik-Fund 7: 'analysing' klebte am fertigen Lauf,
    weil es keinen Loesch-Weg gab). -> neuer Zustand oder None (kein Lauf)."""
    with store_lock(data_dir):
        return _fortschreiben_ungeschuetzt(data_dir, updates)


def _fortschreiben_ungeschuetzt(data_dir, updates):
    zustand, fehler = lauf_lesen(data_dir)
    if zustand is None:
        return None
    for k, v in updates.items():
        if k == "fortschritt" and isinstance(v, dict):
            f = zustand.setdefault("fortschritt", {})
            for fk, fv in v.items():
                if fv is None:
                    f.pop(fk, None)
                else:
                    f[fk] = fv
        else:
            zustand[k] = v
    # .86: jeder Fortschritts-Schrieb stempelt 'aktualisiert' (working-Puls).
    zustand["aktualisiert"] = round(time.time(), 1)
    lauf_schreiben(data_dir, zustand)
    return zustand


def anker_warnungen(a):
    """WARNUNGEN (kein Fehler) zum Anker-Datensatz — vor allem die pose-Betrags-Wache
    (Widerleger F1.7: war nur angekuendigt): drei nicht-negative GANZZAHLEN in Folge
    sehen nach dem analyze.py:242-Altmuster aus (Betraege, vertauscht) — echte Winkel
    tragen Vorzeichen und Streuung. Heuristik, deshalb Warnkanal statt Ablehnung."""
    warn = []
    for i, m in enumerate(a.get("mitglieder") or []):
        pose = m.get("pose")
        if (isinstance(pose, (list, tuple)) and len(pose) == 3
                and all(isinstance(x, int) and x >= 0 for x in pose)
                and any(x > 0 for x in pose)):
            warn.append(f"mitglied[{i}]: pose {list(pose)} — nur nicht-negative "
                        f"Ganzzahlen (Betrags-Altmuster analyze.py:242?)")
    return warn


def anker_anhaengen(data_dir, a):
    """Validieren + als JSONL-Zeile anhaengen (geflusht). Ungueltig -> ValueError
    mit Fehlerliste (nichts wird geschrieben)."""
    fehler = anker_pruefen(a)
    if fehler:
        raise ValueError("anker ungueltig: " + "; ".join(fehler))
    p = _pfad(data_dir, "anker.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(a, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return p


def anker_lesen(data_dir):
    """Alle Anker-Datensaetze; kaputte Zeilen werden GEZAEHLT zurueckgegeben,
    nie still uebersprungen (Leitprinzip 3: nichts verschwindet still)."""
    p = _pfad(data_dir, "anker.jsonl")
    saetze, kaputt = [], 0
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    saetze.append(json.loads(zeile))
                except Exception:
                    kaputt += 1
    return saetze, kaputt
