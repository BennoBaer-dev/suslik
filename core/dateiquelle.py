"""core/dateiquelle — Lernlauf aus eigenen Videodateien statt aus Frigate-Events.

WOFUER (Bauplan analysen/12): Aufnahmen, die nicht (mehr) in Frigates Aufbewahrung
liegen, sollen anlernbar sein. Typische Faelle: Retention abgelaufen, Umzug auf eine
neue Frigate-Instanz, Material aus einer anderen Quelle.

DER TRICK, DER DEN EINGRIFF KLEIN HAELT: `core.frames.clip_holen` laedt NUR, wenn die
Datei im Clip-Cache fehlt. Liegt sie dort, ist es ein Cache-Treffer ohne Netzverkehr.
Eine eingespeiste Datei unter dem erwarteten Namen durchlaeuft damit die KOMPLETTE
echte Kette (Ernte, Anker, Sichtung, Benennung, Uebernahme), ohne dass irgendein
Schritt dahinter angepasst werden muss. Es entsteht KEIN zweiter Erkennungspfad —
genau das war der Fehler des Handbetriebs, der an drei Systemannahmen scheiterte.

DAUERMARKE (QS-Einwand A): eingespeiste Clips bekommen `core.frames.behalten()`. Ohne
sie raeumt cleanup_cache sie nach clip_retention_d (2 Tage) weg — mitten in einem Lauf,
den jemand ueber Wochen bearbeitet. Der Pin taugt dafuer NICHT (verfaellt nach 30 min).

ZEITSTEMPEL (QS-Einwand D): `start` kommt aus der creation_time des Videos, denn er
steuert ueber `szenario_gap_min` die Durchgangsbildung. Fehlt sie, faellt der Import
auf die Datei-mtime zurueck und sagt das LAUT — nie stillschweigend "jetzt".

SICHERHEIT (QS-Einwand E): die Event-ID wird SELBST erzeugt, ein Dateiname landet
niemals in einem Pfad. Der Kameraname wird gegen ein festes Muster geprueft.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

from core import frames as _fr

# Wie eine Frigate-eid: "<unix.mikro>-<6 Zeichen>". Muss zu registry.EID_RE passen
# ([\w.\-]+), damit ALLE Routen greifen — die Crop-Route verlangt zusaetzlich eine
# Lauf-ID nach L-Muster, das bleibt Sache des Lernlaufs.
KAMERA_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
QUELLE_DATEI = "datei"


def _ffprobe(pfad):
    """-> dict mit dauer_s, breite, hoehe, codec, creation_time (oder None-Werte).
    Wirft nicht: ein unlesbares Video meldet der Aufrufer als Fehler."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,codec_name:format=duration",
             "-show_entries", "format_tags=creation_time",
             "-of", "json", pfad],
            capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout or "{}")
    except Exception:
        return {}
    st = (d.get("streams") or [{}])[0]
    fm = d.get("format") or {}
    ct = (fm.get("tags") or {}).get("creation_time")
    return {"breite": st.get("width"), "hoehe": st.get("height"),
            "codec": st.get("codec_name"),
            "dauer_s": float(fm["duration"]) if fm.get("duration") else None,
            "creation_time": ct}


def _startzeit(pfad, meta):
    """-> (start_ts, quelle_der_zeit). creation_time bevorzugt (steuert die
    Durchgangsbildung), sonst mtime — und das ist eine LAUTE Rueckfallebene."""
    ct = meta.get("creation_time")
    if ct:
        try:
            import datetime
            t = datetime.datetime.fromisoformat(str(ct).replace("Z", "+00:00"))
            return t.timestamp(), "creation_time"
        except Exception:
            pass
    try:
        return os.path.getmtime(pfad), "datei-mtime (creation_time fehlt)"
    except OSError:
        return time.time(), "JETZT (weder creation_time noch mtime lesbar)"


def eid_erzeugen(pfad, start_ts):
    """Event-ID im Frigate-Format, aus dem Dateiinhalt abgeleitet und damit
    stabil: dieselbe Datei ergibt dieselbe eid (zweimaliges Einspeisen legt
    keinen zweiten Clip an). Der DATEINAME geht NICHT ein (QS-Einwand E)."""
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        h.update(f.read(1024 * 1024))          # erstes MB reicht zur Unterscheidung
        h.update(str(os.path.getsize(pfad)).encode())
    kurz = h.hexdigest()[:6]
    return f"{start_ts:.6f}-{kurz}"


def einspeisen(pfad, kamera, data_dir, log=print, kopieren=True, lauf_id=None):
    """EINE Videodatei in den Clip-Cache einspeisen.

    -> Pseudo-Event-dict wie es die events_liste des Lernlaufs erwartet, plus
       'quelle': 'datei' — daran erkennen spaetere Stufen, dass es kein
       Frigate-Event ist (QS-Einwand B: keine toten /video/-Links anbieten).
    Wirft ValueError mit Klartext, wenn die Datei nicht taugt."""
    if not os.path.isfile(pfad):
        raise ValueError(f"keine Datei: {pfad}")
    if not KAMERA_RE.match(str(kamera or "")):
        raise ValueError(f"Kameraname unzulaessig (erlaubt: A-Z a-z 0-9 _ -): {kamera!r}")
    meta = _ffprobe(pfad)
    if not meta.get("dauer_s") or not meta.get("breite"):
        raise ValueError(f"kein lesbares Video (ffprobe liefert nichts): {os.path.basename(pfad)}")
    start, zeitquelle = _startzeit(pfad, meta)
    if zeitquelle != "creation_time":
        log(f"file source: {os.path.basename(pfad)} — Startzeit aus {zeitquelle}; "
            "die Durchgangsbildung haengt daran (szenario_gap_min)")
    eid = eid_erzeugen(pfad, start)
    ziel = _fr.cache_pfad(eid, data_dir)
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    if not os.path.exists(ziel):
        if kopieren:
            tmp = f"{ziel}.einspeisen.part"
            shutil.copyfile(pfad, tmp)
            os.replace(tmp, ziel)              # atomar: nie ein halbes Video im Cache
        else:
            os.link(pfad, ziel)
    _fr.behalten(eid, data_dir, lauf_id=lauf_id)   # Dauermarke, s. Kopf; lauf_id
                                               # = Freigabe-Bezug (.334, Audit)
    log(f"file source: {os.path.basename(pfad)} -> {eid} "
        f"({meta['breite']}x{meta['hoehe']}, {meta['dauer_s']:.0f}s, {meta['codec']}, "
        f"camera {kamera})")
    return {"eid": eid, "kamera": kamera, "start": start,
            "clip_s": round(float(meta["dauer_s"]), 1), "hat_clip": True,
            "quelle": QUELLE_DATEI}


def ordner_einspeisen(ordner, data_dir, kamera_aus_name=None, log=print,
                      lauf_id=None):
    """Alle Videos eines Ordners einspeisen. kamera_aus_name(dateiname) -> Kamera;
    ohne Funktion wird der Dateiname ohne Endung genommen (auf das erlaubte Muster
    zurechtgestutzt). -> (events, fehler) — fehlerhafte Dateien stoppen den Rest NIE."""
    events, fehler = [], []
    for name in sorted(os.listdir(ordner)):
        if not name.lower().endswith((".mp4", ".mkv", ".mov")):
            continue
        p = os.path.join(ordner, name)
        kam = (kamera_aus_name(name) if kamera_aus_name
               else re.sub(r"[^A-Za-z0-9_\-]", "_", os.path.splitext(name)[0])[:64])
        try:
            events.append(einspeisen(p, kam, data_dir, log=log, lauf_id=lauf_id))
        except Exception as e:                                    # noqa: BLE001
            fehler.append((name, f"{type(e).__name__}: {e}"))
            log(f"file source: SKIPPED {name} — {e}")
    return events, fehler
