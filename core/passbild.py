"""Kontaktblatt je Pass-Segment: deterministisches JPEG aus den Frames eines Segments.

Der HA-Host kann keine Bilder rendern (kein ffmpeg/Pillow/ImageMagick), Suslik schon. Dieses Modul ist der
Offline-Renderer: EINGABE sind nur Index-Schluessel (pass_key, revision, segment) oder eine explizite
Frame-Liste, AUSGABE sind JPEG-Bytes. Kein Netz, kein MQTT, keine Datei auf der Platte, keine Biometrie.
Die Frame-Auswahl kommt, wenn nichts hereingereicht wird, aus einem einzigen Griff an core.pass_mqtt
(paesse + revision + bild_bytes) — derselben Quelle, aus der auch der MQTT-Text gebaut wird.
"""
import io
import json
import os
import re
import threading
from collections import OrderedDict

from PIL import Image, ImageDraw, ImageFont

_KEY = re.compile(r"[0-9A-Za-z][0-9A-Za-z_.-]{0,63}\Z")
_REV = re.compile(r"[0-9a-f]{12}\Z")
_SEG = re.compile(r"[0-9]+\Z")

_FONT = ImageFont.load_default()
_BG = (16, 16, 20)          # Blatt
_TILE_BG = (34, 34, 40)     # Briefkasten um das Bild
_STRIP_BG = (8, 8, 10)      # Beschriftungsstreifen
_FG = (232, 232, 236)
_W, _H, _STRIP = 512, 360, 24
_COLS, _MAX_TILES, _MAX_ROWS, _CACHE_CAP = 2, 12, 6, 128

_CACHE = OrderedDict()
_LOCK = threading.Lock()


def etag(revision):
    """HTTP-ETag des Blattes, oder None bei ungueltiger Revision. -> Text/None"""
    if isinstance(revision, str) and _REV.fullmatch(revision):
        return '"%s"' % revision
    return None


def cache_lesen(cache_key):
    """Ein Eintrag aus dem Prozess-Speicher (zuletzt benutzt nach vorn). -> Bytes/None"""
    with _LOCK:
        daten = _CACHE.get(cache_key)
        if daten is not None:
            _CACHE.move_to_end(cache_key)
        return daten


def cache_schreiben(cache_key, daten):
    """Eintrag in den Prozess-Speicher, aelteste fallen bei Ueberlauf. -> None"""
    if not isinstance(daten, (bytes, bytearray)) or not daten:
        return
    with _LOCK:
        if cache_key in _CACHE:
            _CACHE.move_to_end(cache_key)
        _CACHE[cache_key] = bytes(daten)
        while len(_CACHE) > _CACHE_CAP:
            _CACHE.popitem(last=False)


def _gueltig(pass_key, revision, segment):
    """Nur Index-Schluessel, nie Pfade. Keine Ausnahme darf hier raus. -> bool"""
    try:
        if not isinstance(pass_key, str) or not _KEY.fullmatch(pass_key):
            return False
        if not isinstance(revision, str) or not _REV.fullmatch(revision):
            return False
        nr = str(segment)
        return bool(_SEG.fullmatch(nr)) and 0 <= int(nr) < 64
    except (TypeError, ValueError):
        return False


def _deckung_by_h(cfg):
    """state/deckung.jsonl als last-wins-Map je eid — dieselbe Leseart wie core/kette.deckung_by_eid."""
    data_dir = (cfg or {}).get("data_dir") if isinstance(cfg, dict) else None
    if not data_dir:
        return {}
    by_h = {}
    try:
        with open(os.path.join(data_dir, "state", "deckung.jsonl"), encoding="utf-8") as f:
            for zeile in f:
                try:
                    d = json.loads(zeile)
                except (ValueError, TypeError):
                    continue
                if isinstance(d, dict) and d.get("eid"):
                    by_h[d["eid"]] = d
    except OSError:
        return {}
    return by_h


def _frames_aus_cfg(cfg, by_h, revision, segment):
    """Dieselbe Segment-Auswahl wie im MQTT-Text: revision(pass_key, index, segment)."""
    from core import pass_mqtt as pm                     # absichtlich spaet (Modul entsteht parallel)
    if by_h is None:
        by_h = _deckung_by_h(cfg)
    for p in pm.paesse(cfg, by_h) or []:
        if not isinstance(p, dict):
            continue
        segs = p.get("segments")
        if segs is None:
            segs = p.get("segmente")
        if not isinstance(segs, (list, tuple)) or segment >= len(segs):
            continue
        seg = segs[segment]
        if not isinstance(seg, dict):
            continue
        # Das Segment bleibt unveraendert der Schnappschuss; people/categories stehen im Pass,
        # aber wir erfinden keine Felder und leiten keine URLs aus Rohpfaden ab.
        try:
            rev = pm.revision(p.get("pass_key"), segment, seg)
        except Exception:
            continue
        if rev != revision:
            continue
        frames = seg.get("frames")
        if frames:
            return list(frames)
    return None


def _frame_bytes(cfg, frame):
    """Ein Bild NUR ueber core.pass_mqtt.bild_bytes (realpath-Containment dort). -> Bytes/None"""
    try:
        from core import pass_mqtt as pm
        daten = pm.bild_bytes(cfg, frame)
    except Exception:
        return None
    return bytes(daten) if isinstance(daten, (bytes, bytearray)) and daten else None


def _erstes(frame, schluessel):
    for s in schluessel:
        wert = frame.get(s)
        if isinstance(wert, (str, int, float)) and str(wert):
            return str(wert)
    return ""


def _label(frame, nr):
    if isinstance(frame, dict):
        kamera = _erstes(frame, ("kamera", "camera", "cam")) or "?"
        zeit = _erstes(frame, ("zeit", "timestamp", "ts", "start"))
        art = _erstes(frame, ("art", "kind", "typ", "label"))
    elif isinstance(frame, str):
        kamera, zeit, art = os.path.basename(frame), "", ""
    else:
        kamera, zeit, art = "?", "", ""
    return " ".join(str(x) for x in ("#%d" % nr, kamera, zeit, art) if x)[:80]


def _tile(cfg, frame, nr):
    tile = Image.new("RGB", (_W, _H + _STRIP), _BG)
    bild = Image.new("RGB", (_W, _H), _TILE_BG)
    daten = _frame_bytes(cfg, frame)
    if daten:
        try:
            mit = Image.open(io.BytesIO(daten))
            mit.load()
            mit = mit.convert("RGB")
            mit.thumbnail((_W, _H), Image.Resampling.LANCZOS)
            bild.paste(mit, ((_W - mit.width) // 2, (_H - mit.height) // 2))
        except Exception:
            daten = None                                 # Platzhalter bleibt stehen
    if not daten:
        ImageDraw.Draw(bild).text((_W // 2 - 4, _H // 2 - 8), "?", fill=_FG, font=_FONT)
    tile.paste(bild, (0, 0))
    d = ImageDraw.Draw(tile)
    d.rectangle((0, _H, _W, _H + _STRIP), fill=_STRIP_BG)
    d.text((4, _H + 4), _label(frame, nr), fill=_FG, font=_FONT)
    return tile


def _render(cfg, frames):
    n = min(_MAX_TILES, len(frames))
    zeilen = min(_MAX_ROWS, (n + 1) // 2)
    blatt = Image.new("RGB", (_COLS * _W, zeilen * (_H + _STRIP)), _BG)
    for i, frame in enumerate(frames[:_MAX_TILES]):
        blatt.paste(_tile(cfg, frame, i + 1),
                    ((i % _COLS) * _W, (i // _COLS) * (_H + _STRIP)))
    puffer = io.BytesIO()
    blatt.save(puffer, format="JPEG", quality=85, subsampling=0)
    return puffer.getvalue()


def contact_sheet(cfg, pass_key, revision, segment, *, frames=None, by_h=None):
    """Deterministisches Kontaktblatt (JPEG-Bytes) oder None. Nie eine Ausnahme fuer schlechte Schluessel.

    Ohne `frames` wird dieselbe Auswahl wie im MQTT-Text getroffen: deckung.jsonl last-wins by_h,
    core.pass_mqtt.paesse, Revision + Segmentindex, dann deren frames.
    """
    if not _gueltig(pass_key, revision, segment):
        return None
    nr = int(segment)
    cache_key = (pass_key, revision, nr)
    treffer = cache_lesen(cache_key)
    if treffer is not None:
        return treffer
    try:
        if frames is None:
            frames = _frames_aus_cfg(cfg, by_h, revision, nr)
        if not frames:
            return None
        jpeg = _render(cfg, list(frames))
    except Exception:
        return None
    cache_schreiben(cache_key, jpeg)
    return jpeg
