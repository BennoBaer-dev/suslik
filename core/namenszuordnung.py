"""Die Namenszuordnung: bei mehreren Personen bekommt jedes Frigate-Ereignis den Namen seiner verfolgten Person.

HERKUNFT: Bauplan analysen/bauplan_namenszuordnung.md, Stufe NZ2 (Eigentuemer 26.10.2026 15:15:37, Startwort
16:20:29). Die Regeln sind am Fall vom 26.10. gemessen (Machbarkeit
analysen/pruefungen/2026-10-26_1427_namenszuordnung_machbarkeit/, Nachrechnung der Regeln A und B
analysen/pruefungen/2026-10-26_1505_namenszuordnung_zusatzregeln/); die Werkswerte stehen allein in
core.registry.NAMENSZUORDNUNG_WERK und werden je Aufruf gelesen.

ZWECK: suslik schrieb in jedes Ereignis den staerksten Namen des ganzen Clips; bei mehreren Personen trugen dann
mehrere Ereignisse denselben Namen (O836). Hier wird nur gerechnet, aus Zahlen, die es schon gibt:
  - Eingabe: die Akten der Ereignisse einer Kamera im Durchgang (Format nach NZ1: `detektionen` mit `i`, `rahmen`,
    `det`, `bw`, `bh`, `fd`; `persons` mit `stimm_idx`; `bild` mit Breite, Hoehe, Bildrate) und Frigates Ereignisse
    dieser Kamera im Format der Ereignisliste (`start_time`, `data.box`, `data.path_data`,
    `data.snapshot_frame_time`). Keine Ein- und Ausgabe, keine Frigate-Abfrage, kein Log.
  - Startzeit: je Clip die Startzeit T0 auf Frigates Uhr, bei der die Gesichter am besten auf die Wege aller
    Ereignisse passen; ist das zweitbeste Minimum nicht deutlich teurer, gilt fuer das Ereignis des Clips der
    Ersatzweg.
  - Zuordnung: eine Stimme gehoert zu einem Ereignis, wenn ihr Gesicht im oberen Bereich seines an den zeitgleichen
    Fusspunkt versetzten Rahmens liegt, und das fuer genau ein Ereignis.
  - Regel A: bei einer Begegnung zweier Wege zaehlen fuer ein Ereignis nur die Stimmen auf der Seite seines
    Schnappschusses; Stimmen im Begegnungsfenster zaehlen fuer niemanden.
  - Regel B: bleiben genau ein bestaetigter Name und genau ein Ereignis ohne Namen, gehoeren sie zusammen, wenn die
    Zahl der bestaetigten Namen gleich der Zahl der Ereignisse ist.
  - Ergebnis je Ereignis: Name oder keiner, Grund, T0 und Schaerfe seines Clips, Stimmen je Seite als Beleg. Ohne
    Namen schreibt der Aufrufer wie bisher den staerksten Namen des Clips (Ersatzweg, Stufe NZ3).

EHRLICHE GRENZEN:
  - Alle Werte sind an einem Fall gemessen (vier Personen, eine Kamera, drei Clips).
  - Regel B zaehlt nur: eine erkannte Person ohne eigenes Ereignis plus ein Ereignis ohne erkennbares Gesicht ergeben
    gleiche Zahlen; Regel A laesst eine Stimme genuegen (Bauplan, Entscheid 1: getragen).
  - Vertauscht Frigate Spuren ohne messbare Begegnung, kann ein falscher Name entstehen.
  - Der Pixelabstand der Begegnung nimmt an, dass Frigates Bild dasselbe Seitenverhaeltnis hat wie der Clip.
  - Stimmen eines Clips ohne scharfe Startzeit haben keine Frigate-Zeit; sie zaehlen weder fuer ein Ereignis noch
    fuer die Bestaetigung eines Namens.
  - Gleiche Kamerabilder ueberlappender Clips zaehlen einmal; sagen ihre Kopien verschiedene Ereignisse, zaehlt das
    Bild fuer keins.
"""
import numpy as np

from core import registry

# Gruende des Ergebnisses (Produkt-Texte, Zaehler je Grund in /health ab Stufe NZ3)
GRUND_SEITE = "schnappschuss_seite"
GRUND_AUSSCHLUSS = "ausschluss"
GRUND_EINE_PERSON = "eine_person"
ERSATZ = "ersatz:"
# Gruende des Ersatzwegs, hinter ERSATZ
KEIN_WEG = "kein_weg"                          # data.path_data oder data.box fehlt
KEIN_SCHNAPPSCHUSS = "kein_schnappschuss"      # data.snapshot_frame_time fehlt
KEINE_LAGE = "keine_lage"                      # Akte ohne Bildgroesse, Bildrate oder Gesicht mit Lage
STARTZEIT_UNSCHARF = "startzeit_unscharf"      # zweitbestes Minimum der Eichung nicht deutlich teurer
IN_BEGEGNUNG = "schnappschuss_in_begegnung"    # Schnappschuss im Begegnungsfenster, Regel A gibt keinen Namen
KEINE_STIMME = "keine_stimme"                  # keine bestaetigte Stimme auf der Schnappschuss-Seite
GLEICHSTAND = "gleichstand"                    # zwei bestaetigte Namen gleich stark auf der Schnappschuss-Seite
ERSATZ_GRUENDE = (KEIN_WEG, KEIN_SCHNAPPSCHUSS, KEINE_LAGE, STARTZEIT_UNSCHARF, IN_BEGEGNUNG, KEINE_STIMME,
                  GLEICHSTAND)
GRUENDE = (GRUND_SEITE, GRUND_AUSSCHLUSS, GRUND_EINE_PERSON) + tuple(ERSATZ + g for g in ERSATZ_GRUENDE)
FENSTER = "F"                                  # Kennung einer Seite, die ein Begegnungsfenster ist (F0, F1, ...)

_zaehler = {}                                  # Grund -> Zahl der gerechneten Ereignisse seit dem Start (/health)


def _werk():
    """Die Werkswerte, je Aufruf aus der Registry gelesen.
    -> dict"""
    return registry.NAMENSZUORDNUNG_WERK


def spur_lesen(ev):
    """Liest Weg, Rahmengroesse und Schnappschusszeit eines Frigate-Ereignisses.
    -> (Spur oder None, Ersatzgrund oder None)"""
    d = ev.get("data") or {}
    punkte, box = d.get("path_data") or [], d.get("box")
    if not punkte or not box or len(box) < 4 or box[2] <= 0 or box[3] <= 0:
        return None, KEIN_WEG
    reihe = sorted({(float(ts), float(xy[0]), float(xy[1])) for xy, ts in punkte})
    snap = d.get("snapshot_frame_time")
    return {"id": ev["id"], "t": np.array([p[0] for p in reihe]), "x": np.array([p[1] for p in reihe]),
            "y": np.array([p[2] for p in reihe]), "w": float(box[2]), "h": float(box[3]),
            "snap": None if snap is None else float(snap)}, (None if snap is not None else KEIN_SCHNAPPSCHUSS)


def _fuss(sp, zeit, w):
    """Der Fusspunkt einer Spur zu Frigate-Zeiten: zwischen Wegpunkten linear, am ersten und letzten Punkt gehalten.
    -> (x, y, gueltig) als Felder wie `zeit`"""
    fx = np.interp(zeit, sp["t"], sp["x"])
    fy = np.interp(zeit, sp["t"], sp["y"])
    ok = (zeit >= sp["t"][0] - w["halten_vor_s"]) & (zeit <= sp["t"][-1] + w["halten_nach_s"])
    return fx, fy, ok


def _innen(sp, zeit, cx, cy, w):
    """Ob Gesichter im oberen Bereich des an den Fusspunkt versetzten Rahmens liegen.
    -> bool-Feld wie `zeit`"""
    fx, fy, ok = _fuss(sp, zeit, w)
    oben = fy - sp["h"]
    return (ok & (np.abs(cx - fx) <= w["innen_breite"] * sp["w"])
            & (cy >= oben - w["innen_oben"] * sp["h"]) & (cy <= oben + w["innen_unten"] * sp["h"]))


def clip_lesen(akte):
    """Liest aus einer Akte die Gesichter fuer die Eichung und die Stimmen, je mit Clip-Zeit und Gesichtsmitte.
    -> (Clip oder None, Ersatzgrund oder None)"""
    w = _werk()
    bild = akte.get("bild") or {}
    fps, breite, hoehe = bild.get("fps"), bild.get("breite"), bild.get("hoehe")
    if not fps or not breite or not hoehe or fps <= 0 or breite <= 0 or hoehe <= 0:
        return None, KEINE_LAGE
    det = akte.get("detektionen") or []

    def lage(d):
        r = d.get("rahmen")
        if d.get("i") is None or not r or len(r) < 4:
            return None
        return d["i"] / fps, r[0] + r[2] / 2, r[1] + r[3] / 2

    eich = [lage(d) for d in det
            if d.get("fd") is False and d.get("det", 0) >= w["eich_det_min"]
            and min(d.get("bw", 0), d.get("bh", 0)) >= w["eich_kante_min_px"]]
    eich = [x for x in eich if x is not None]
    stimmen = []
    for name, p in sorted((akte.get("persons") or {}).items()):
        for k in (p or {}).get("stimm_idx") or []:
            x = lage(det[k]) if 0 <= k < len(det) else None
            if x is not None:
                stimmen.append((name,) + x)
    if not eich:
        return None, KEINE_LAGE
    return {"source": akte.get("source"), "verhaeltnis": hoehe / breite,
            "eich": tuple(np.array(v) for v in zip(*eich)), "stimmen": stimmen}, None


def startzeit_eichen(gesichter, spuren, start_time):
    """Sucht die Startzeit T0 des Clips auf Frigates Uhr, bei der die Gesichter am besten auf die Wege passen.
    -> {"t0", "kosten", "zweit", "schaerfe", "scharf"}"""
    w = _werk()
    zeit, cx, cy = gesichter
    n = int(round((w["eich_vor_s"] + w["eich_nach_s"]) / w["eich_schritt_s"]))
    raster = start_time - w["eich_vor_s"] + w["eich_schritt_s"] * np.arange(n + 1)
    tt = raster[:, None] + zeit[None, :]
    kosten = np.full(tt.shape, float(w["kosten_deckel"]))
    for sp in spuren:
        fx, fy, ok = _fuss(sp, tt, w)
        kopf_y = fy - sp["h"] + w["kopf_versatz"] * sp["h"]
        d = np.hypot((cx[None, :] - fx) / sp["w"], (cy[None, :] - kopf_y) / sp["h"])
        kosten = np.minimum(kosten, np.where(ok, np.minimum(d, w["kosten_deckel"]), w["kosten_deckel"]))
    kurve = kosten.mean(axis=1)
    b = int(np.argmin(kurve))
    innen = np.arange(1, len(kurve) - 1)
    lok = innen[(kurve[1:-1] <= kurve[:-2]) & (kurve[1:-1] <= kurve[2:])]
    fern = lok[np.abs(raster[lok] - raster[b]) > w["schaerfe_abstand_s"]]
    best = float(kurve[b])
    zweit = float(kurve[fern].min()) if len(fern) else None
    if zweit is None:
        scharf, schaerfe = True, None
    else:
        scharf = zweit > 0 and zweit >= w["schaerfe_min"] * best
        schaerfe = zweit / best if best > 0 else None
    return {"t0": float(raster[b]), "kosten": best, "zweit": zweit, "schaerfe": schaerfe, "scharf": scharf}


def _laeufe(zeit, maske):
    """Zusammenhaengende Laeufe einer Maske im Zeitraster.
    -> [(von, bis), ...]"""
    aus, start = [], None
    for k, m in enumerate(maske):
        if m and start is None:
            start = k
        if not m and start is not None:
            aus.append((float(zeit[start]), float(zeit[k - 1])))
            start = None
    if start is not None:
        aus.append((float(zeit[start]), float(zeit[-1])))
    return aus


def begegnungen(spuren, verhaeltnis):
    """Findet die Begegnungsfenster je Wegpaar: Fussabstand in Pixeln unter Faktor mal kleinerer Rahmenbreite.
    -> {Ereignis: [(von, bis, Partner), ...] nach Beginn sortiert}"""
    w = _werk()
    fenster = {sp["id"]: [] for sp in spuren}
    for k, a in enumerate(spuren):
        for b in spuren[k + 1:]:
            lo, hi = max(a["t"][0], b["t"][0]), min(a["t"][-1], b["t"][-1])
            if lo > hi:
                continue
            n = int(round((hi - lo) / w["begegnung_schritt_s"]))
            tt = np.minimum(lo + w["begegnung_schritt_s"] * np.arange(n + 1), hi)
            dx = np.interp(tt, a["t"], a["x"]) - np.interp(tt, b["t"], b["x"])
            dy = (np.interp(tt, a["t"], a["y"]) - np.interp(tt, b["t"], b["y"])) * verhaeltnis
            nah = np.hypot(dx, dy) < w["begegnung_faktor"] * min(a["w"], b["w"])
            for von, bis in _laeufe(tt, nah):
                fenster[a["id"]].append((von, bis, b["id"]))
                fenster[b["id"]].append((von, bis, a["id"]))
    return {e: sorted(f) for e, f in fenster.items()}


def seite(fenster, zeit):
    """Die Seite eines Wegs zu einer Frigate-Zeit: Abschnitt zwischen den Begegnungen oder ein Fenster.
    -> "0", "1", ... oder "F0", "F1", ..."""
    k = 0
    for j, (von, bis, _partner) in enumerate(fenster):
        if von <= zeit <= bis:
            return f"{FENSTER}{j}"
        if zeit > bis:
            k = j + 1
    return str(k)


def _clip_stimmen(clip, spuren, w):
    """Ordnet die Stimmen eines geeichten Clips den Wegen zu: das eine Ereignis, in dessen Rahmen das Gesicht liegt.
    -> [(Name, Frigate-Zeit, Ereignis oder None), ...]"""
    if not clip["stimmen"]:
        return []
    namen = [s[0] for s in clip["stimmen"]]
    zeit = clip["t0"] + np.array([s[1] for s in clip["stimmen"]])
    cx = np.array([s[2] for s in clip["stimmen"]])
    cy = np.array([s[3] for s in clip["stimmen"]])
    treffer = [(sp["id"], _innen(sp, zeit, cx, cy, w)) for sp in spuren]
    aus = []
    for k, name in enumerate(namen):
        ziele = [e for e, m in treffer if m[k]]
        aus.append((name, float(zeit[k]), ziele[0] if len(ziele) == 1 else None))
    return aus


def stimmen_buendeln(clips, spuren):
    """Fasst die Stimmen aller geeichten Clips zu Kamerabildern zusammen, gleiche Bilder ueberlappender Clips einmal.
    -> [{"name", "t", "ziel"}, ...]; ziel nur, wenn alle Kopien dasselbe Ereignis nennen"""
    w = _werk()
    gruppen = []
    for clip in sorted(clips, key=lambda c: c["t0"]):
        for name, zeit, ziel in _clip_stimmen(clip, spuren, w):
            g = next((g for g in gruppen if g["name"] == name and clip["source"] not in g["clips"]
                      and abs(g["t"] - zeit) < w["bild_gleich_s"]), None)
            if g is None:
                g = {"name": name, "t": zeit, "clips": set(), "ziele": []}
                gruppen.append(g)
            g["clips"].add(clip["source"])
            g["ziele"].append(ziel)
    return [{"name": g["name"], "t": g["t"], "ziel": g["ziele"][0] if len(set(g["ziele"])) == 1 else None}
            for g in gruppen]


def _clips_eichen(akten, spuren, ereignisse):
    """Liest und eicht jeden Clip, dessen Ereignis im Durchgang steht.
    -> ({Ereignis: Eichung oder Ersatzgrund}, [geeichte Clips], Seitenverhaeltnis oder None)"""
    start = {e["id"]: float(e["start_time"]) for e in ereignisse if e.get("start_time") is not None}
    je_akte = {a.get("source"): a for a in akten}
    eichung, geeicht, verhaeltnis = {}, [], None
    for eid, akte in je_akte.items():
        if eid not in start:
            continue
        clip, grund = clip_lesen(akte)
        if clip is None or not spuren:
            eichung[eid] = grund or KEIN_WEG
            continue
        verhaeltnis = clip["verhaeltnis"] if verhaeltnis is None else verhaeltnis
        e = startzeit_eichen(clip["eich"], spuren, start[eid])
        eichung[eid] = e
        if e["scharf"]:
            geeicht.append({**clip, "t0": e["t0"]})
    return eichung, geeicht, verhaeltnis


def _je_seite(gruppen, eid, fenster):
    """Die Stimmen eines Ereignisses je Seite seines Wegs (Beleg).
    -> {Seite: {Name: Stimmen}}"""
    aus = {}
    for g in gruppen:
        if g["ziel"] == eid:
            s = seite(fenster, g["t"])
            aus.setdefault(s, {})
            aus[s][g["name"]] = aus[s].get(g["name"], 0) + 1
    return {s: dict(sorted(v.items())) for s, v in sorted(aus.items())}


def regel_a(sp, je_seite, fenster, bestaetigt):
    """Regel A: der bestaetigte Name mit den meisten Stimmen auf der Schnappschuss-Seite, mindestens einer, eindeutig.
    -> (Name oder None, Seite des Schnappschusses, Grund ohne Namen oder None)"""
    s = seite(fenster, sp["snap"])
    if s.startswith(FENSTER):
        return None, s, IN_BEGEGNUNG
    zahl = {n: k for n, k in je_seite.get(s, {}).items() if n in bestaetigt}
    if not zahl:
        return None, s, KEINE_STIMME
    top = max(zahl.values())
    sieger = [n for n, k in zahl.items() if k == top]
    if len(sieger) > 1:
        return None, s, GLEICHSTAND
    return sieger[0], s, None


def regel_b(erg, bestaetigt, zahl_ereignisse):
    """Regel B: genau ein bestaetigter Name ohne Ereignis und genau ein Ereignis ohne Namen gehoeren zusammen, wenn
    die Zahl der bestaetigten Namen gleich der Zahl der Ereignisse ist. -> None (traegt in `erg` ein)

    Die Bedingung aus NZ2, dass der Begegnungspartner nicht selbst ueber den Ausschluss benannt wurde, ist entfallen
    (Bauplan Nachtrag 3, Stufe NZ3 Punkt 7): Regel B benennt hoechstens ein Ereignis, sie konnte nie greifen."""
    frei = [n for n in bestaetigt if n not in {r["name"] for r in erg.values()}]
    ohne = [e for e, r in erg.items() if r["name"] is None]
    if len(frei) != 1 or len(ohne) != 1 or len(bestaetigt) != zahl_ereignisse:
        return
    e = ohne[0]
    if erg[e]["vorab"] is not None:
        return
    erg[e]["name"], erg[e]["grund"] = frei[0], GRUND_AUSSCHLUSS


def _bestaetigt(gruppen, stapel_stimmen):
    """Die im Durchgang bestaetigten Namen: alle Stimmen, gleiche Kamerabilder einmal, mindestens `stapel_stimmen`.
    -> {Name: Stimmen}"""
    zahl = {}
    for g in gruppen:
        zahl[g["name"]] = zahl.get(g["name"], 0) + 1
    return {n: k for n, k in sorted(zahl.items()) if k >= stapel_stimmen}


def _leer(grund):
    """Ein Ergebnis ohne Namen und ohne Belege.
    -> dict"""
    return {"name": None, "grund": grund, "t0": None, "schaerfe": None, "schnappschuss_seite": None,
            "stimmen": {}, "begegnungen": []}


def _runden(x, stellen):
    """Rundet eine Zahl fuer die Belege, None bleibt None.
    -> float oder None"""
    return None if x is None else round(x, stellen)


def zuordnen(akten, ereignisse, stapel_stimmen):
    """Ordnet jedem Frigate-Ereignis einer Kamera im Durchgang den Namen seiner verfolgten Person zu.
    -> {Ereignis: {"name", "grund", "t0", "schaerfe", "schnappschuss_seite", "stimmen", "begegnungen"}}"""
    if len(ereignisse) < 2:
        return {e["id"]: _leer(GRUND_EINE_PERSON) for e in ereignisse}
    spuren, vorab = [], {}
    for ev in ereignisse:
        sp, grund = spur_lesen(ev)
        vorab[ev["id"]] = grund
        if sp is not None:
            spuren.append(sp)
    eichung, geeicht, verhaeltnis = _clips_eichen(akten, spuren, ereignisse)
    fenster = begegnungen(spuren, verhaeltnis) if verhaeltnis is not None else {sp["id"]: [] for sp in spuren}
    gruppen = stimmen_buendeln(geeicht, spuren)
    bestaetigt = _bestaetigt(gruppen, stapel_stimmen)
    je_spur = {sp["id"]: sp for sp in spuren}
    erg = {}
    for ev in ereignisse:
        eid = ev["id"]
        r = _leer(None)
        e = eichung.get(eid)
        if isinstance(e, dict):
            r["t0"], r["schaerfe"] = _runden(e["t0"], 3), _runden(e["schaerfe"], 2)
            if not e["scharf"] and vorab[eid] is None:
                vorab[eid] = STARTZEIT_UNSCHARF
        elif e is not None and vorab[eid] is None:
            vorab[eid] = e
        f = fenster.get(eid, [])
        r["begegnungen"] = [[round(v, 2), round(b, 2), p] for v, b, p in f]
        r["stimmen"] = _je_seite(gruppen, eid, f)
        r["vorab"] = vorab[eid]
        if vorab[eid] is None:
            r["name"], r["schnappschuss_seite"], a_grund = regel_a(je_spur[eid], r["stimmen"], f, bestaetigt)
            r["grund"] = GRUND_SEITE if r["name"] else ERSATZ + a_grund
        else:
            r["grund"] = ERSATZ + vorab[eid]
        erg[eid] = r
    regel_b(erg, bestaetigt, len(ereignisse))
    for r in erg.values():
        del r["vorab"]
    return erg


def zaehlen(grund):
    """Ein Ereignis, fuer das der Dienst die Zuordnung gerechnet hat, fuer /health unter seinem Grund zaehlen.
    -> None

    Ohne eigenes Schloss (das Modul importiert nur numpy und core.registry, Probe e3_76 Fall g): der Dienst ruft
    `zaehlen` nur unter seinem kleinen Schloss `_nz_klein`, das alle Kameras teilen (verifyd.Service.process, Stufe
    NZ3; seit Stufe FS2 des Bauplans analysen/bauplan_frigate_schreiber.md gilt die Sperre der Zuordnung je Kamera)."""
    _zaehler[str(grund)] = _zaehler.get(str(grund), 0) + 1


def stand():
    """Der Zaehler fuer /health: wie oft der Dienst seit dem Start eine Zuordnung gerechnet hat, je Grund.
    -> {"ereignisse": Summe, "gruende": {Grund: Zahl}}"""
    je = dict(sorted(dict(_zaehler).items()))       # dict(...) kopiert in einem Schritt, auch neben `zaehlen`
    return {"ereignisse": sum(je.values()), "gruende": je}
