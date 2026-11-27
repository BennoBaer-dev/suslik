"""core/pass_mqtt — der reine Kern der Pass-Stufen (Snapshot, Bilder, Revision, Timer).

Kein MQTT-Versand, keine Vision, kein core.refquelle (liegt nicht im git): dieses Modul
lest Ereignis-Zeilen ueber die EINE Gruppierung in szenarien.szenarien_des_tages und
baut daraus deterministische Pass-/Segment-Snapshots. Neu-Code nach der E6c-Regel in
eigener Datei; Versand und Kontaktbild-Route gehoeren nicht hierher.
"""
import datetime
import hashlib
import json
import os
import re
import threading
import urllib.parse

from core import harvest_set as _hs
from core import registry as _reg
import szenarien as _sz

SCHEMA = "pass-v1"
HERKUNFT = "pass"
MAX_SEGMENT_S = 600
MAX_SEGMENT_EVENTS = 20
ZIEL_BILDER = 10
MAX_BILDER = 12
MIN_BILDER = 8

_REF_RE = re.compile(r"^[0-9a-f]{8,64}$")
_BILD_ENDUNGEN = (".jpg", ".jpeg", ".png", ".webp")


def _zahl(wert):
    """Zahl fuer Sortierung und Score, 0 bei Unsinn. -> float"""
    try:
        return float(wert)
    except (TypeError, ValueError):
        return 0.0


def _t(ev):
    """Zeit eines Szenario-Events (Akte kennt `t`, Rohzeile `start`/`ts`). -> float"""
    return ev.get("t") or ev.get("start") or ev.get("ts") or 0


def _dateien(verzeichnis):
    """Bilddateien eines Ereignis-Ordners, sortiert; kein Ordner = keine Bilder. -> list"""
    try:
        return sorted(d for d in os.listdir(verzeichnis)
                      if d.lower().endswith(_BILD_ENDUNGEN)
                      and os.path.isfile(os.path.join(verzeichnis, d)))
    except OSError:
        return []


def _event_url(eid, datei):
    """Bild-Adresse ohne jeden Dateisystem-Pfad. -> URL-Text"""
    return ("/events/" + urllib.parse.quote(str(eid), safe="") + "/"
            + urllib.parse.quote(str(datei), safe=""))


def _kameras(evs):
    """Kameras in Zeitfolge, aufeinanderfolgende Wiederholungen gefaltet. -> list"""
    aus = []
    for ev in sorted(evs, key=_t):
        cam = str(ev.get("cam") or ev.get("camera") or "")
        if cam and (not aus or aus[-1] != cam):
            aus.append(cam)
    return aus


def _richtung(kameras):
    """Erste -> letzte Kamera einer Folge. -> Text"""
    return f"{kameras[0] if kameras else ''}->{kameras[-1] if kameras else ''}"


def _personen(s, evs, by_h):
    """s['pers'] auf die gegebenen Events eingeschraenkt (Pass oder Segment). -> list"""
    eids = {str(e.get("eid") or "") for e in evs}
    aus = []
    for name, d in (s.get("pers") or {}).items():
        treffer = [e for e in evs if name in (e.get("conf") or [])]
        if not treffer and str(d.get("eid") or "") not in eids:
            continue
        if treffer:
            erst, letzt = min(treffer, key=_t), max(treffer, key=_t)
            erst_cam = str(erst.get("cam") or erst.get("camera") or "")
            letzt_cam = str(letzt.get("cam") or letzt.get("camera")
                             or d.get("letzt_cam") or "")
            anzahl = len(treffer)
        else:
            cam = str((by_h.get(d.get("eid")) or {}).get("camera") or "")
            erst_cam = letzt_cam = cam
            anzahl = 1
        best = _zahl(d.get("best"))
        for e in treffer:
            ours = (by_h.get(e.get("eid")) or {}).get("ours") or {}
            best = max(best, _zahl((ours.get(name) or {}).get("max")))
        aus.append({"name": name, "count": anzahl, "first_camera": erst_cam,
                    "last_camera": letzt_cam, "best_cos": best})
    return sorted(aus, key=lambda p: p["name"])


def _segmente(evs):
    """Chronologische Segmente: 600 s oder 20 Events, nie ueber Passgrenze. -> generator"""
    aktuell = []
    for ev in evs:
        if aktuell and (_t(ev) - _t(aktuell[0]) > MAX_SEGMENT_S
                        or len(aktuell) >= MAX_SEGMENT_EVENTS):
            yield aktuell
            aktuell = []
        aktuell.append(ev)
    if aktuell:
        yield aktuell


def _snapshot(cfg, s, pass_key, by_h, *, event_dir=None):
    """Ein Szenario -> Pass-Snapshot samt Segmenten. -> dict"""
    evs = sorted(s.get("evs") or [], key=_t)
    kams = _kameras(evs)
    eids = sorted(str(e.get("eid") or "") for e in evs if e.get("eid"))
    unbek = {str(e or "") for e in (s.get("unbek_eids") or [])}
    segmente = []
    for teil in _segmente(evs):
        seg_eids = sorted(str(e.get("eid") or "") for e in teil if e.get("eid"))
        leute = _personen(s, teil, by_h)
        seg_kams = _kameras(teil)
        frames = frames_fuer_segment(cfg, seg_eids, by_h=by_h, event_dir=event_dir)
        segmente.append({
            "index": len(segmente),
            "window": [_t(teil[0]), _t(teil[-1])],
            "eids": seg_eids,
            "counts": {"events": len(teil), "frames": len(frames),
                       "known_people": len({p["name"] for p in leute}),
                       "unknown": sum(1 for e in seg_eids if e in unbek)},
            "camera_sequence": seg_kams,
            "camera_first_seen": seg_kams[0] if seg_kams else "",
            "inferred_direction": _richtung(seg_kams),
            "people": leute,
            "categories": s.get("kat"),
            "frames": frames,
        })
    return {"pass_key": pass_key, "start": s.get("start"), "ende": s.get("ende"),
            "kette": s.get("kette"), "eids": eids, "categories": s.get("kat"),
            "kamera_first_seen": kams[0] if kams else "", "camera_sequence": kams,
            "inferred_direction": _richtung(kams), "people": _personen(s, evs, by_h),
            "segments": segmente}


def paesse(cfg, by_h, *, jetzt=None, gtmap=None, event_dir=None):
    """Pass-Snapshots aller lokalen Tage in by_h — Gruppierung nur in szenarien. -> list"""
    cfg, by_h = cfg or {}, by_h or {}
    tage = sorted({datetime.datetime.fromtimestamp(
        r.get("start") or r.get("ts") or 0).date() for r in by_h.values()})
    treffer = {}
    for tag in tage:
        t0 = datetime.datetime.combine(tag, datetime.time()).timestamp()
        t1 = datetime.datetime.combine(tag + datetime.timedelta(days=1),
                                       datetime.time()).timestamp()
        for s in _sz.szenarien_des_tages(by_h, t0, t1, cfg, gtmap or {}, now=jetzt):
            key = str(_sz._pass_schluessel(s["start"], s.get("kette")))
            if key not in treffer:
                treffer[key] = _snapshot(cfg, s, key, by_h, event_dir=event_dir)
    return [treffer[k] for k in sorted(treffer, key=lambda k: treffer[k]["start"])]


def frames_fuer_segment(cfg, eids, *, by_h=None, event_dir=None):
    """Deterministische Bildauswahl eines Segments (max 12, Ziel 10, 2 pro Ereignis). -> list"""
    cfg, by_h = cfg or {}, by_h or {}
    daten = str(cfg.get("data_dir") or "")
    bw_pro_kamera = {}
    for eid in eids:
        row = by_h.get(eid) or {}
        cam = str(row.get("camera") or "")
        bw = _zahl(row.get("max_bw"))
        if cam and (cam not in bw_pro_kamera or bw > bw_pro_kamera[cam][1]):
            bw_pro_kamera[cam] = (eid, bw)
    kand, gesehen = [], set()
    for eid in sorted(str(e) for e in eids):
        if not eid:
            continue
        row = by_h.get(eid) or {}
        cam = str(row.get("camera") or "")
        ts = row.get("start") or row.get("ts") or 0
        ordner = event_dir if event_dir is not None else os.path.join(daten, "events", eid)
        dateien = _dateien(ordner)

        def hinzu(src, key, url, score, prio):
            fid = f"{eid}|{src}|{key}"
            if fid in gesehen:
                return
            gesehen.add(fid)
            wert = _zahl(score)
            kand.append((prio, -wert, fid,
                         {"id": fid, "eid": eid, "camera": cam, "ts": ts,
                          "kind": src, "url": url, "score": wert}))

        kand_rows, best_rows = _hs.event_rows(ordner)
        for z in list(kand_rows) + list(best_rows.values()):
            rid = str(z.get("ref_id") or "")
            if _REF_RE.fullmatch(rid):
                score = next((_zahl(z[k]) for k in ("score", "mass", "cos")
                              if z.get(k) is not None), 0.0)
                hinzu("ref", rid, f"/lernlauf/satz/{rid}?klein=1", score, 0)
        try:
            weitere = _hs.event_ref_ids(ordner)
        except OSError:
            weitere = []
        for rid in weitere:
            rid = str(rid or "")
            if _REF_RE.fullmatch(rid):
                hinzu("ref", rid, f"/lernlauf/satz/{rid}?klein=1", 0, 0)
        genutzt = set()
        for name, info in (row.get("ours") or {}).items():
            datei = next((d for d in dateien if f"_show_{name}_" in d), None)
            if datei is None:
                continue
            genutzt.add(datei)
            hinzu("person", str(name), _event_url(eid, datei),
                  (info or {}).get("max"), 1)
        if bw_pro_kamera.get(cam, (None, None))[0] == eid:
            datei = next((d for d in dateien if "_show_" in d and d not in genutzt), None)
            if datei:
                genutzt.add(datei)
                hinzu("camera", cam, _event_url(eid, datei), bw_pro_kamera[cam][1], 2)
        for datei in dateien:
            if "_show_" in datei and datei not in genutzt:
                hinzu("event", datei, _event_url(eid, datei), 0, 3)
    kand.sort(key=lambda c: (c[0], c[1], c[2]))
    aus, rest, pro_eid = [], [], {}
    for _prio, _neg, _fid, frame in kand:
        if len(aus) >= MAX_BILDER:
            break
        e = frame["eid"]
        if len(aus) < ZIEL_BILDER and pro_eid.get(e, 0) >= 2:
            rest.append(frame)          # unter der Zielzahl sonst verworfen — als Reserve
            continue
        pro_eid[e] = pro_eid.get(e, 0) + 1
        aus.append(frame)
    if len(aus) < MIN_BILDER:            # ein Ereignis allein darf trotzdem acht Bilder liefern
        for frame in rest:
            if len(aus) >= MIN_BILDER or len(aus) >= MAX_BILDER:
                break
            aus.append(frame)
    return sorted(aus, key=lambda f: f["id"])


def _lesen(pfad):
    """Bytes einer Datei, None wenn sie nicht lesbar ist. -> bytes|None"""
    try:
        with open(pfad, "rb") as f:
            return f.read()
    except OSError:
        return None


def bild_bytes(cfg, frame):
    """Ein Frame nur ueber seine URL laden — realpath-Containment, keine Rohpfade. -> bytes|None"""
    if not isinstance(frame, dict):
        return None
    url = str(frame.get("url") or "")
    if not url.startswith("/") or url.startswith("//") or "\\" in url or "%2f" in url.lower():
        return None
    teile = urllib.parse.urlsplit(url)
    if teile.scheme or teile.netloc or teile.query not in ("", "klein=1"):
        return None
    daten = os.path.realpath(str((cfg or {}).get("data_dir") or ""))
    m = re.fullmatch(r"/events/([^/]+)/([^/]+)", teile.path)
    if m:
        eid = urllib.parse.unquote(m.group(1))
        datei = urllib.parse.unquote(m.group(2))
        if ".." in eid or ".." in datei:
            return None
        if not re.fullmatch(_reg.EID_RE, eid) or not re.fullmatch(_reg.DATEI_RE, datei):
            return None
        basis = os.path.realpath(os.path.join(daten, "events"))
        pfad = os.path.realpath(os.path.join(basis, eid, datei))
        if not pfad.startswith(basis + os.sep):
            return None
        return _lesen(pfad)
    m = re.fullmatch(r"/lernlauf/satz/([0-9a-f]{8,64})", teile.path)
    if m:
        # ohne core.refquelle: der Satz liegt als <hex>.* irgendwo unter state/.
        basis = os.path.realpath(os.path.join(daten, "state"))
        treffer = []
        for wurzel, _dirs, dateien in os.walk(basis):
            for datei in dateien:
                if datei.startswith(m.group(1) + "."):
                    pfad = os.path.realpath(os.path.join(wurzel, datei))
                    if pfad.startswith(basis + os.sep) and os.path.isfile(pfad):
                        treffer.append(pfad)
        return _lesen(sorted(treffer)[0]) if treffer else None
    return None


def _segment(snapshot, index):
    """Segment eines Pass-Snapshots (ein nacktes Segment wird auch akzeptiert). -> dict"""
    segs = snapshot.get("segments") if isinstance(snapshot, dict) else None
    return segs[index] if segs and index < len(segs) else snapshot


def revision(pass_key, segment_index, snapshot):
    """Kurz-Hash ueber die kanonische Segment-Menge — gleichbleibend bei identischem Pass. -> str"""
    seg = _segment(snapshot, segment_index)
    kanonisch = {"schema": SCHEMA, "pass_key": pass_key, "segment": segment_index,
                 "window": seg["window"], "eids": sorted(seg["eids"]),
                 "frame_ids": sorted(f["id"] for f in seg["frames"]),
                 "people": seg["people"], "categories": seg["categories"],
                 "counts": seg["counts"]}
    text = json.dumps(kanonisch, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def payload(snapshot, segment_index, status, rev):
    """MQTT-Nutzlast genau mit dem vereinbarten Schluessel-Satz. -> dict"""
    seg = _segment(snapshot, segment_index)
    segs = snapshot.get("segments") if isinstance(snapshot, dict) else None
    return {
        "schema": SCHEMA, "herkunft": HERKUNFT, "pass_key": snapshot.get("pass_key"),
        "segment": int(segment_index), "segments": len(segs) if segs else 1,
        "status": status, "revision": rev,
        "window": seg["window"], "eids": seg["eids"], "counts": seg["counts"],
        "camera_sequence": seg["camera_sequence"],
        "camera_first_seen": seg["camera_first_seen"],
        "inferred_direction": seg["inferred_direction"], "people": seg["people"],
        "categories": seg["categories"], "frames": seg["frames"],
        "contact_url": ("/pass/" + urllib.parse.quote(str(snapshot.get("pass_key") or ""), safe="")
                        + f"/{rev}/{segment_index}/contact.jpg"),
    }


class PassTimer:
    """Karenz-Timer je Pass im Speicher — kein Start-Timer, keine Persistenz."""

    def __init__(self, cfg, fire, *, timer_factory=None):
        self.cfg = cfg or {}
        self.fire = fire
        self.factory = timer_factory or threading.Timer
        self._laufend = {}

    def antossen(self, pass_key):
        """Vorherigen Timer desselben Passes abbrechen und neu starten. -> bool"""
        self.cancel(pass_key)
        dauer = self.cfg.get("szene_karenz_s", 90)
        halt = []

        def ausloesen(_key, _timer):
            self.feuer(pass_key, halt[0] if halt else None)

        t = self.factory(dauer, ausloesen, args=(pass_key, None))
        halt.append(t)
        try:
            t.daemon = True
        except (AttributeError, TypeError):
            pass
        self._laufend[pass_key] = t
        try:
            t.start()
        except Exception:  # noqa: BLE001  kein Timer = kein pass: kein Status
            self._laufend.pop(pass_key, None)
            return False
        return True

    def feuer(self, pass_key, mein_timer):
        """Nur der aktuelle Timer zaehlt und wird entfernt. -> bool"""
        aktuell = self._laufend.get(pass_key)
        if aktuell is None or mein_timer is not aktuell:
            return False
        del self._laufend[pass_key]
        self.fire(pass_key, mein_timer)
        return True

    def cancel(self, pass_key=None):
        """Ein Timer oder alle abbrechen und vergessen. -> None"""
        keys = list(self._laufend) if pass_key is None else [pass_key]
        for key in keys:
            t = self._laufend.pop(key, None)
            if t is not None:
                try:
                    t.cancel()
                except (AttributeError, TypeError):
                    pass
