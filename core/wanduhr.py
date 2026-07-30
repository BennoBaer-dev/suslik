"""core/wanduhr — Selbstvermessung + Dauer-Hochrechnung des Lern-Laufs (E1 Baustein 3;
Konzept §P0.3, Zahlenbasis V0.4, interne Messreihe).

Modell (V0.4, Latte <±30 % je Event erfuellt):
    wall  = fixkosten_je_clip_s + k(aufloesung) * clip_s          (warm)
    kalt  = + kaltaufschlag_s EINMAL je Lauf (konstant, nicht je Clip)
    download = download_fix_s + download_s_je_mb * mb  (mb ~= mb_je_clipsekunde * clip_s)

ALLE Konstanten sind MESSGROESSEN je Maschine (Allgemeinheits-Prinzip §2.4b):
gemessen per Worker-Roundtrip (kalt+warm, wall_s seit 24b2fe8) + Download-Probe;
gespeichert KLEBRIG je hw_key+VERSION (placement.json-Muster — V0.4: ueber
Versionsgrenzen gemittelt waere der Bias -24 %). Die Autor-Zahlen unten sind NUR
Rueckfall fuer die Anzeige, solange noch nie gemessen wurde, und werden als
"quelle": "rueckfall" ausgewiesen — nie still als Messung ausgegeben.
Reine Funktionen, kein Dienst-Import; I/O nur ueber Parameter-Pfade.
"""
import json
import os
import tempfile

SCHEMA_VERSION = 1

# V0.4-Autorwerte (Core Ultra 9 285H, openvino:MIXED, 2026-07-28) — NUR Rueckfall/Anzeige.
RUECKFALL = {
    "kaltaufschlag_s": 14.78,
    "fixkosten_je_clip_s": 0.18,
    "k_je_aufloesung": {"1920x1080": 0.1764, "2560x1920": 0.2375, "3840x2160": 0.2442},
    "k_global": 0.2321,
    "download_fix_s": 0.214,
    "download_s_je_mb": 0.0263,
    "mb_je_clipsekunde": 0.75,
    "live_zuschlag": 1.12,
}
# E1-QS-Toleranz der Realitaets-Kopplung (V0.4: p90 intern 27,9 %, gegen Prod 23,5 %).
KOPPLUNG_TOLERANZ = 0.30


def _pfad(data_dir):
    return os.path.join(data_dir, "state", "wanduhr.json")


def lesen(data_dir, hw_key, version):
    """Gemessene Konstanten fuer GENAU diese Maschine+Version — sonst Rueckfall.
    -> (konstanten, quelle) mit quelle in ('gemessen', 'rueckfall')."""
    p = _pfad(data_dir)
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        if (d.get("schema") == SCHEMA_VERSION and d.get("hw_key") == hw_key
                and d.get("version") == version and isinstance(d.get("werte"), dict)):
            return d["werte"], "gemessen", list(d.get("gemessen") or [])
    except Exception:
        pass
    return dict(RUECKFALL), "rueckfall", []


GEMESSENE_FELDER_ROUNDTRIP = ("kaltaufschlag_s", "k_global", "k_je_aufloesung")


def schreiben(data_dir, hw_key, version, werte, mess_meta=None, gemessen=None):
    """Atomar (tmp+fsync+rename). werte = vollstaendiger Konstantensatz. gemessen =
    Liste der WIRKLICH gemessenen Felder (Widerleger F3.1: all-or-nothing-Kennung gab
    Autorwerte als Messung aus) — Leser zeigen den Rest ehrlich als Rueckfall an."""
    fehlt = [k for k in RUECKFALL if k not in werte]
    if fehlt:
        raise ValueError(f"konstanten unvollstaendig: {fehlt}")
    p = _pfad(data_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    d = {"schema": SCHEMA_VERSION, "hw_key": hw_key, "version": version,
         "werte": werte, "gemessen": list(gemessen or []),
         **({"mess": mess_meta} if mess_meta else {})}
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), prefix=".wanduhr-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return p


KONTROLL_MIN_CLIP_S = 15.0   # Widerleger .70/F2.5: kurze Clips kippen k bis +92 % —
#                              Mess- und Kontroll-Event brauchen Mindestlaenge.


def kontroll_event(events, min_clip_s=KONTROLL_MIN_CLIP_S):
    """Waehlt das juengste Event mit Clip UND Mindestlaenge als Mess-/Kontroll-Event.
    -> (event, clip_s) oder (None, None) — dann wird NICHT gemessen (Rueckfall bleibt,
    ehrlich gekennzeichnet), statt eine kippelige Zahl zu speichern."""
    for e in events:
        if not (e.get("has_clip") and e.get("end_time") and e.get("start_time")):
            continue
        clip_s = float(e["end_time"]) - float(e["start_time"])
        if clip_s >= min_clip_s:
            return e, clip_s
    return None, None


def zweit_event(events, erster_eid, min_clip_s=KONTROLL_MIN_CLIP_S):
    """Ein ZWEITES, vom Mess-Event verschiedenes Kontroll-Event fuer die Realitaets-
    Kopplung (Widerleger F1.5: am Mess-Event selbst waere sie tautologisch)."""
    for e in events:
        if e.get("id") == erster_eid:
            continue
        if not (e.get("has_clip") and e.get("end_time") and e.get("start_time")):
            continue
        clip_s = float(e["end_time"]) - float(e["start_time"])
        if clip_s >= min_clip_s:
            return e, clip_s
    return None, None


def _k(werte, aufloesung):
    return (werte.get("k_je_aufloesung") or {}).get(aufloesung) or werte["k_global"]


def clip_prognose_s(werte, clip_s, aufloesung=None, im_cache=False):
    """Warm-Prognose fuer EINEN Clip inkl. Download-Posten (0 wenn im Cache)."""
    wall = werte["fixkosten_je_clip_s"] + _k(werte, aufloesung) * max(clip_s, 0.0)
    if not im_cache:
        mb = werte["mb_je_clipsekunde"] * max(clip_s, 0.0)
        wall += werte["download_fix_s"] + werte["download_s_je_mb"] * mb
    return wall


def lauf_prognose(werte, clips, live_last=False):
    """Gesamt-Prognose eines Laufs. clips = [{'clip_s':…, 'aufloesung':…, 'im_cache':bool}].
    -> dict mit analyse_s/download_s/kalt_s/gesamt_s (Wizard zeigt die Posten GETRENNT,
    Konzept §P0.3)."""
    analyse = download = 0.0
    for c in clips:
        cs = max(c.get("clip_s") or 0.0, 0.0)
        analyse += werte["fixkosten_je_clip_s"] + _k(werte, c.get("aufloesung")) * cs
        if not c.get("im_cache"):
            mb = werte["mb_je_clipsekunde"] * cs
            download += werte["download_fix_s"] + werte["download_s_je_mb"] * mb
    faktor = werte.get("live_zuschlag", 1.0) if live_last else 1.0
    kalt = werte["kaltaufschlag_s"]
    return {"analyse_s": analyse * faktor, "download_s": download,
            "kalt_s": kalt, "gesamt_s": analyse * faktor + download + kalt,
            "n_clips": len(clips)}


def kopplung_pruefen(werte, clip_s, aufloesung, echte_wall_s, toleranz=KOPPLUNG_TOLERANZ):
    """Realitaets-Kopplung (E1-QS): Prognose vs. echte Dauer EINES Kontroll-Events.
    -> (ok, abweichung_relativ). Ein luegender Benchmark faellt durch (|abw| > toleranz)."""
    prog = clip_prognose_s(werte, clip_s, aufloesung, im_cache=True)
    if prog <= 0:
        return False, float("inf")
    abw = (echte_wall_s - prog) / prog
    return abs(abw) <= toleranz, abw


def aus_roundtrip(kalt, warm, clip_s, aufloesung, download_probe=None, basis=None):
    """Konstanten aus EINER Kalt/Warm-Roundtrip-Messung ableiten (Mini-Messung des
    fremden Systems; Verfahren = Norm, V0.4-Formel-FORM bleibt): warm liefert k fuer
    DIESE Aufloesung (Fixkosten aus basis/Rueckfall — aus einem Punkt nicht trennbar,
    ehrlich dokumentiert), kalt-warm liefert den Kaltaufschlag. download_probe
    optional {'mb':…, 'wall_s':…}. -> vollstaendiger Konstantensatz."""
    b = dict(basis or RUECKFALL)
    kalt_w, warm_w = float(kalt["wall_s"]), float(warm["wall_s"])
    if clip_s <= 0 or warm_w <= 0 or kalt_w < warm_w:
        raise ValueError(f"unplausible Messung: kalt={kalt_w}, warm={warm_w}, clip_s={clip_s}")
    k = max((warm_w - b["fixkosten_je_clip_s"]) / clip_s, 0.001)
    b["kaltaufschlag_s"] = round(kalt_w - warm_w, 2)
    b["k_global"] = round(k, 4)
    kja = dict(b.get("k_je_aufloesung") or {})
    if aufloesung:
        kja[aufloesung] = round(k, 4)
    b["k_je_aufloesung"] = kja
    if download_probe and download_probe.get("mb", 0) > 0:
        mb, dw = float(download_probe["mb"]), float(download_probe["wall_s"])
        b["download_s_je_mb"] = round(max(dw - b["download_fix_s"], 0.01) / mb, 4)
    return b
