"""E3 Phase 2 — Anker-Bildung aus dem Ernte-Laufordner (Konzept §P2/§5, Design
Design-Leitplanken des Lern-Blocks).

Reine Funktionen ohne Dienst-Zustand; der Aufrufer (verifyd) reicht ALLE Schwellen
aus der Config-Whitelist herein — hier stehen KEINE Anlagen-Werte (Allgemeinheits-
Wache: die gemessenen Defaults leben in der Whitelist, nie im Pfad).

Zweistufig nach §P2: Stufe 1 clustert INNERHALB jedes Durchgangs (kleine Mengen,
staerkste Evidenz) und verdichtet jede Gruppe auf ihren ZENTROID-Vertreter
(V0.2b-Pflicht: NICHT das guete-beste Gesicht — das verlor 40 % der Zusammen-Paare,
der Zentroid 11 %). Stufe 2 clustert die Vertreter GEDECKELT (Konzept: Deckel je
Clusterung; die S7b-Widerleger-Messung 30.07. haelt den Deckel zwingend: ~50 B/n^2
Speicher, 60-s-Punkt ~2400)."""
import json
import os
import time

import numpy as np


# ------------------------------------------------------------------ B1: Durchgangs-Kette
def durchgaenge_bilden(events_liste, gap_min):
    """Events des Laufs -> Durchgaenge. DIESELBE Ketten-Regel wie
    szenarien.szenarien_des_tages (zeitlich sortiert, Luecke > gap => neuer
    Durchgang, Ende waechst mit); Ende = start + clip_s, weil der Lauf-Store kein
    Frigate-ende_ts traegt — clip_s ist die reale Cliplaenge. Der PYE3-Vektor haelt
    die Gruppierung an einem Fixfall deckungsgleich zur Live-Kette.
    -> Liste [{start, ende, eids, kameras}] in Zeitreihenfolge."""
    gap = float(gap_min) * 60.0
    evs = sorted((e for e in events_liste if e.get("start")), key=lambda e: e["start"])
    grp, cur = [], None
    for e in evs:
        t = float(e["start"])
        ende = t + float(e.get("clip_s") or 0.0)
        if cur and t - cur["ende"] <= gap:
            cur["eids"].append(e["eid"])
            cur["ende"] = max(cur["ende"], ende)
            cur["kameras"].add(str(e.get("kamera", "?")))
        else:
            cur = {"start": t, "ende": ende, "eids": [e["eid"]],
                   "kameras": {str(e.get("kamera", "?"))}}
            grp.append(cur)
    for g in grp:
        g["kameras"] = sorted(g["kameras"])
    return grp


# ------------------------------------------------------------------ B2: Stufe 1 je Durchgang
def s_kandidaten_lesen(lauf_dir, eids):
    """Anker-taugliche Zeilen (s==True) aus den Kandidaten-Dateien der Events.
    id = Crop-Dateiname ohne .jpg (stabil, kollisionsfrei, ueberlebt Resume).
    .83 (Widerleger): fehlende Dateien und unlesbare Zeilen werden GEZAEHLT
    zurueckgegeben, nie still uebersprungen (269 fehlende Dateien waren unsichtbar;
    EINE abgeschnittene Zeile toetete die Phase dauerhaft — Resume lief in denselben
    Fehler). Dateiname ueber core.ernte.kandidaten_pfad: Schreiber und Leser teilen
    EINE Namensregel (_eid_safe).
    -> (kands, fehlende_dateien, kaputte_zeilen)"""
    from core import ernte as _ern
    kands, fehlend, kaputt = [], 0, 0
    for eid in eids:
        pfad = _ern.kandidaten_pfad(lauf_dir, eid)
        if not os.path.exists(pfad):
            fehlend += 1
            continue
        with open(pfad) as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    z = json.loads(zeile)
                except Exception:
                    kaputt += 1
                    continue
                if z.get("s") and z.get("datei"):
                    z["id"] = os.path.basename(z["datei"])[:-4]
                    kands.append(z)
    return kands, fehlend, kaputt


def zentroid(embs):
    """Renormierter Mittelwert (Cosinus-Raum). -> Liste float, 5 Stellen (Pool-Vertrag).
    .83: NaN/inf-Wache — ein nicht-finites Embedding lieferte vorher einen NaN-Vektor
    (n < 1e-9 ist fuer NaN False), der die Margen-Bewertung blind machte und
    anker.jsonl zu Nicht-RFC-JSON gemacht haette."""
    m = np.asarray(embs, dtype=np.float32)
    if not np.all(np.isfinite(m)):
        return None
    m = m.mean(axis=0)
    n = float(np.linalg.norm(m))
    if n < 1e-9:                       # degeneriert (ausloeschende Embeddings): kein Vertreter
        return None
    return [round(float(x), 5) for x in (m / n)]


def stufe1_vertreter(kands, sim, clusterer):
    """Gruppen INNERHALB eines Durchgangs + Zentroid-Vertreter je Gruppe.
    clusterer = anlernen.clustere (injiziert, damit PYE3 mit Fixfunktionen testet).
    guete := det dient NUR der deterministischen Cluster-Sortierung — der Vertreter
    ist der Zentroid, nie das beste Einzelgesicht.
    .83: stuetz_phys = PHYSISCH verschiedene Detektionen (Dedup kamera+bbox) —
    zeitlich ueberlappende Frigate-Events derselben Kamera ernten denselben Frame
    mehrfach (gemessen Faktor 1,44; ein 'Cluster' mit 6 Zeilen konnte 3 echte
    Gesichter haben). Degenerierte Gruppen (NaN-Embedding) werden GEZAEHLT, ihre
    Zeilen tauchen im Fortschritts-Ausweis auf statt still zu verschwinden.
    -> (vertreter, degeneriert_zeilen)"""
    if not kands:
        return [], 0
    G = [{"id": k["id"], "emb": k["emb"], "guete": float(k.get("det") or 0.0)}
         for k in kands]
    by_id = {k["id"]: k for k in kands}
    vertreter, degeneriert = [], 0
    for gruppe in clusterer(G, sim=sim):
        mitglieder = [by_id[g["id"]] for g in gruppe]
        z = zentroid([m["emb"] for m in mitglieder])
        if z is None:
            degeneriert += len(mitglieder)
            continue
        yaws = [float(m["pose"][1]) for m in mitglieder]
        pitches = [float(m["pose"][0]) for m in mitglieder]
        phys = {(str(m.get("kamera", "?")), tuple(m.get("bbox") or ())) for m in mitglieder}
        vertreter.append({
            "emb": z, "stuetz": len(mitglieder), "stuetz_phys": len(phys),
            "mitglieder": mitglieder,
            "kameras": sorted({str(m.get("kamera", "?")) for m in mitglieder}),
            "yaw_spanne": [round(min(yaws), 1), round(max(yaws), 1)],
            "pitch_spanne": [round(min(pitches), 1), round(max(pitches), 1)],
        })
    return vertreter, degeneriert


# ------------------------------------------------------------------ B3: gedeckelte Stufe 2
def stufe2_clustern(vertreter, sim, deckel, deckel_hart, clusterer, log=None):
    """Vertreter aller Durchgaenge -> Anker-Cluster.
    .83 (Widerleger A4/A5): solange n <= deckel_hart laeuft EINE Clusterung — das
    Runden-Verfahren verletzte messbar die Linkage-Invariante (A2<->A68 blieben bei
    avg 0,366 >= sim2 getrennt; 250er- vs 300er-Partition: 42 Gesichter wanderten),
    und der alte deckel=250 band 50 Vertreter UNTER der Speicher-Not. Runden gibt es
    nur noch OBERHALB von deckel_hart, DEKLARIERT als Naeherung (Tranchen-Groesse =
    deckel, stuetz-staerkste zuerst, Folge-Runden clustern Cluster-Zentroide mit).
    Laeuft eine Runde voll (Cluster-Zahl >= deckel), werden die restlichen Vertreter
    als EIGENE Cluster angehaengt statt die Phase mit ValueError zu toeten —
    deklariert im Log und in der Rueckgabe.
    -> (cluster_liste, runden, ungeclustert)  [runden=1 + ungeclustert=0 = exakter Lauf]."""
    if not vertreter:
        return [], 0, 0
    deckel, deckel_hart = int(deckel), int(deckel_hart)
    if deckel < 2 or deckel_hart < deckel:
        raise ValueError(f"unbrauchbarer Deckel {deckel}/{deckel_hart}")

    def _clustern(G_vertreter):
        G = [{"id": f"v{i}", "emb": v["emb"], "guete": float(v["stuetz"])}
             for i, v in enumerate(G_vertreter)]
        aus = []
        for grp in clusterer(G, sim=sim):
            vs = [G_vertreter[int(g["id"][1:])] for g in grp]
            z = zentroid([v["emb"] for v in vs]) or vs[0]["emb"]
            aus.append({"emb": z, "vs": vs})
        return aus

    if len(vertreter) <= deckel_hart:
        return [c["vs"] for c in _clustern(list(vertreter))], 1, 0

    if log:
        log(f"anker stage 2: {len(vertreter)} representatives exceed the hard cap "
            f"{deckel_hart} — round-based APPROXIMATION (linkage not exact)")
    rest = sorted(vertreter, key=lambda v: (-v["stuetz"], v["mitglieder"][0]["id"]))
    cluster, runden, ungeclustert = [], 0, 0
    while rest:
        runden += 1
        vorhanden = [{"id": f"c{i}", "emb": c["emb"], "guete": float(len(c["vs"]))}
                     for i, c in enumerate(cluster)]
        platz = deckel - len(vorhanden)
        if platz < 1:
            ungeclustert = len(rest)
            cluster.extend({"emb": v["emb"], "vs": [v]} for v in rest)
            if log:
                log(f"anker stage 2: round full at {len(vorhanden)} clusters — "
                    f"{ungeclustert} leftover representatives kept as single clusters (declared)")
            break
        tranche = rest[:platz]
        rest = rest[platz:]
        G = vorhanden + [{"id": f"v{i}", "emb": v["emb"], "guete": float(v["stuetz"])}
                         for i, v in enumerate(tranche)]
        alt, cluster = cluster, []
        for grp in clusterer(G, sim=sim):
            vs = []
            for g in grp:
                if g["id"][0] == "c":
                    vs.extend(alt[int(g["id"][1:])]["vs"])
                else:
                    vs.append(tranche[int(g["id"][1:])])
            z = zentroid([v["emb"] for v in vs]) or vs[0]["emb"]
            cluster.append({"emb": z, "vs": vs})
        if log and rest:
            log(f"anker stage 2: round {runden} done — {len(rest)} representatives remaining")
    return [c["vs"] for c in cluster], runden, ungeclustert


# ------------------------------------------------------------------ B5: Eimer-Achsen (.83)
def margen_bewerten(cluster, zents, hart_schwelle, k_min):
    """Status-Achsen je Cluster (.83, Widerleger-Linse 2 — alles am 74er-Echtmaterial
    GEMESSEN statt von der V0.6-Score-Ebene uebertragen):
    - 'hart' NUR bei KO-PRAESENZ: Zentroid-cos >= hart_schwelle UND die beiden
      Cluster teilen >= 1 gemeinsamen Frame (event + t) — bewiesene Gleichzeitigkeit
      zweier Personen. Der Zentroid-Cosinus allein ist skalen-verschoben (Norm-
      Schrumpfung der Mittelwerte, gemessen Faktor bis 1,86): er markierte exakt die
      drei stuetz-staerksten Cluster falsch, waehrend ihre ECHTE Average-Linkage
      (0,28-0,37) sauber getrennt war.
    - Paare >= hart_schwelle OHNE Ko-Praesenz sind VERSCHMELZUNGS-VORSCHLAEGE
      (vorschlaege-Feld; nie Eimer — nicht-loeschen-Prinzip).
    - 'zu_duenn': stuetz_phys < k_min (PHYSISCHE Detektionen; S-Zeilen zaehlten
      durch ueberlappende Events bis 1,44x doppelt).
    - 'unbestaetigt': nur 1 Durchgang — ein Auftritt liefert EINE Beobachtung, egal
      wie viele Frames; das ist eine AUTOMATIK-Achse (wartet auf den naechsten
      Auftritt), kein User-Pruefauftrag.
    - Die alte Warn-Margen-Schwelle ist GESTRICHEN: auf Zentroid-Ebene strukturell
      unerreichbar (kleinste gemessene Marge 0,46 bei Schwelle 0,15 — 0 Treffer je);
      marge/bester_fremd bleiben als Zahlen im Ausweis.
    -> Liste [{status, bester_fremd, marge, grund, vorschlaege:[cluster_index,...]}]."""
    n = len(cluster)
    if n == 0:
        return []
    M = np.asarray(zents, dtype=np.float32)
    S = M @ M.T
    np.fill_diagonal(S, -1.0)
    frames = []                                    # je Cluster: {(event, t)} fuer Ko-Praesenz
    for c in cluster:
        frames.append({(m["eid"] if "eid" in m else m.get("event"), round(float(m["t"]), 1))
                       for v in c for m in v["mitglieder"]})
    aus = []
    for i in range(n):
        fremd = float(S[i].max()) if n > 1 else -1.0
        marge = round(1.0 - fremd, 3) if n > 1 else 1.0
        nahe = [j for j in range(n) if j != i and S[i, j] >= hart_schwelle]
        ko = [j for j in nahe if frames[i] & frames[j]]
        vorschlaege = [j for j in nahe if j not in ko]
        stuetz_phys = len({(str(m.get("kamera", "?")), tuple(m.get("bbox") or ()))
                           for v in cluster[i] for m in v["mitglieder"]})
        durchgaenge = len({v["durchgang_start"] for v in cluster[i]})
        if ko:
            st, grund = "hart", (f"{len(ko)} co-present neighbour(s) at centroid-cos "
                                 f">= {hart_schwelle} (shared frames)")
        elif stuetz_phys < k_min:
            st, grund = "zu_duenn", f"{stuetz_phys} physical detections < k_min {k_min}"
        elif durchgaenge < 2:
            st, grund = "unbestaetigt", "single pass so far — waiting for the next appearance"
        else:
            st, grund = "ok", ""
        aus.append({"status": st, "bester_fremd": round(fremd, 3), "marge": marge,
                    "grund": grund, "vorschlaege": vorschlaege,
                    "stuetz_phys": stuetz_phys, "durchgaenge_n": durchgaenge})
    return aus


# ------------------------------------------------------------------ B4: Anker-Datensaetze (§5)
def anker_datensaetze(cluster, margen, lauf_id, schwellen, version):
    """Stufe-2-Cluster + Margen-Bewertung -> Schema-§5-Datensaetze (validierbar mit
    core.lernlauf.anker_pruefen; geschrieben wird ueber anker_anhaengen — atomar
    geflusht je Zeile, Resume = anker.jsonl je Lauf neu [ein Lauf schreibt seine
    Anker EINMAL am Stueck nach der Ernte, Teil-Laeufe raeumt der Abbruch->trash-Weg]).
    anker_id = <lauf_id>-A<nr> in stuetz-absteigender, id-gebrochener Ordnung
    (deterministisch; .79-Tie-Break)."""
    saetze = []
    reihen = sorted(range(len(cluster)),
                    key=lambda i: (-sum(v["stuetz"] for v in cluster[i]),
                                   cluster[i][0]["mitglieder"][0]["id"]))
    id_von_idx = {i: f"{lauf_id}-A{nr}" for nr, i in enumerate(reihen, start=1)}
    for nr, i in enumerate(reihen, start=1):
        c, m = cluster[i], margen[i]
        # E4a-Datengrundlage (Widerleger-MUSS 01.08.): bbox/ts/emb wandern MIT in
        # den Datensatz (die Kandidaten-Zeilen tragen sie laengst) — physischer
        # Dedup-Schluessel, Zeitbezug und Fast-Duplikat-Pruefung rechnen damit
        # rein lesend am Store, ohne Rueckgriff auf den trash-gefaehrdeten
        # Kandidaten-Ordner. modell fuettert den Bedingungs-Tag der Benennung.
        mitglieder = [{"event": mm["eid"], "datei": mm["datei"], "t": mm["t"],
                       "kamera": mm["kamera"], "front": mm["front"], "sharp": mm["sharp"],
                       "det": mm["det"], "kante": mm["kante"], "pose": mm["pose"],
                       "bbox": mm.get("bbox") or [], "ts": mm.get("ts", 0),
                       "emb": mm.get("emb") or [], "modell": mm.get("modell", ""),
                       # .308: Vorrats-Messwerte wandern MIT (Norm-Weg der
                       # Sichtungs-Vorauswahl/Reihung liest sie hier; Alt-Anker
                       # ohne norm urteilen weiter ueber die Pixel-Latte).
                       "norm": mm.get("norm"), "front_kps": mm.get("front_kps"),
                       "richtung": mm.get("richtung"),
                       # .32x: der Struktur-Messwert wandert MIT — sonst muesste
                       # die Sichtung ihn fuer JEDES Mitglied neu messen (Bild-I/O
                       # plus Inferenz im Dienst-Prozess), nicht nur fuer
                       # Alt-Mitglieder. Dieselbe Falle wie bei norm in .308.
                       "struktur": mm.get("struktur"),
                       # BELICHTUNG (bauplan_belichtung.md E3, 26.08.): die Luma
                       # des Ernte-Ausschnitts wandert MIT — Reihung und
                       # Sichtung lesen sie hier, statt jedes Mitglied neu zu
                       # messen. Alt-Mitglieder ohne das Feld bleiben None und
                       # gelten als UNBEWERTET (sie werden nie abgewertet).
                       # Bewusst NICHT in _MITGLIED_PFLICHT: Alt-Zeilen im
                       # anker.jsonl muessen gueltig bleiben.
                       "luma": mm.get("luma")}
                      for v in c for mm in v["mitglieder"]]
        z_ank = zentroid([v["emb"] for v in c])
        dgs = sorted({round(float(v["durchgang_start"]), 1) for v in c})
        tage = sorted({time.strftime("%Y-%m-%d", time.localtime(t)) for t in dgs})
        yaws = [y for v in c for y in v["yaw_spanne"]]
        pitches = [p for v in c for p in v["pitch_spanne"]]
        # .83: Verschmelzungs-Vorschlaege als anker_ids (nicht-loeschen-Prinzip —
        # nahe Cluster OHNE Ko-Praesenz sind eine Frage an die Benennung, kein Eimer).
        vorschlaege = sorted(id_von_idx[j] for j in m.get("vorschlaege", []))
        saetze.append({
            "anker_id": id_von_idx[i],
            "person": None, "status": "unbenannt",
            "mitglieder": mitglieder,
            "durchgaenge": dgs,
            "qualitaet": {"stuetz": len(mitglieder),
                          "stuetz_phys": m.get("stuetz_phys", len(mitglieder)),
                          "durchgaenge": len(dgs),
                          "tage": len(tage), "tage_liste": tage,     # Stammgast-Ausweis
                          "marge": m["marge"], "bester_fremd": m["bester_fremd"],
                          "eimer": m["status"], "eimer_grund": m["grund"]},
            "quell_videos": sorted({mm["event"] for mm in mitglieder}),
            # Persistiert statt verworfen (E4a): Personen-Dedup + U-Zuordnung
            # lesen den Cluster-Zentroid direkt aus dem Store.
            "zentroid": [round(float(x), 5) for x in z_ank] if z_ank is not None else [],
            "pose_abdeckung": {"yaw": [min(yaws), max(yaws)],
                               "pitch": [min(pitches), max(pitches)]},
            "mehrdeutig": ([m["grund"]] if m["status"] not in ("ok",) else [])
                          + [f"merge suggestion: {v}" for v in vorschlaege],
            "ganzkoerper": [],
            "groesse_bytes": 0,
            "lauf": {"lauf_id": lauf_id, "version": version, "schwellen": schwellen},
        })
    return saetze


# ------------------------------------------------------------------ B6: komplette Phase
def anker_lauf_schreiben(data_dir, saetze, lauf_id):
    """state/anker.jsonl atomar NEU schreiben: Zeilen ANDERER Laeufe bleiben, von
    DIESEM Lauf werden nur UNBENANNTE Zeilen ersetzt (Benannte-Anker-Schutz E4a:
    Nutzer-Benennungen ueberleben Wiederholung und Abbruch, Rueckgabe zaehlt sie)
    — eine wiederholte Anker-Phase (Boot-Resume nach Crash) erzeugt nie Duplikate.
    Laeuft KOMPLETT unter lernlauf.store_lock; Aufrufer duerfen das Lock NICHT
    bereits halten. Jeder neue Satz wird vorher validiert
    (lernlauf.anker_pruefen; ungueltig => ValueError, NICHTS wird geschrieben).
    -> (uebernommene_fremd_und_benannte, kaputt, benannt_behalten).
    .83 (Widerleger A1): UNLESBARE Zeilen werden ROH weitergefuehrt statt vernichtet
    (vorher warf das Neuschreiben sie weg und die Anzeige 'counted' log); Temp-Datei
    per mkstemp (fester .tmp-Name konnte bei zwei Schreibern ein Ergebnis verlieren);
    json.dumps mit allow_nan=False als letzte NaN-Wache vor der Platte."""
    from core import lernlauf as _ll
    import tempfile
    for s in saetze:
        fehler = _ll.anker_pruefen(s)
        if fehler:
            raise ValueError(f"{s.get('anker_id')}: " + "; ".join(fehler))
    p = os.path.join(data_dir, "state", "anker.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    # E4a (Widerleger-MUSS): das RMW laeuft UNTER store_lock — hier IN der
    # Funktion, damit JEDER Aufrufer abgedeckt ist (verifyd-Abbruch lag ausserhalb
    # des .87-Lock-Blocks). Kein Aufrufer haelt das Lock bereits (flock auf
    # zweitem fd wuerde sonst blockieren) — der Kontrakt steht am Funktionskopf.
    with _ll.store_lock(data_dir):
        bleib, kaputt, benannt_behalten = [], 0, 0
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for zeile in f:
                    z = zeile.rstrip("\n")
                    if not z.strip():
                        continue
                    try:
                        d = json.loads(z)
                        lid = (d.get("lauf") or {}).get("lauf_id")
                    except Exception:
                        kaputt += 1
                        bleib.append(z)          # unlesbar => IMMER erhalten
                        continue
                    if lid != lauf_id:
                        bleib.append(z)
                    elif d.get("status") not in (None, "unbenannt"):
                        # Benannte-Anker-Schutz (E4a): das Neuschreiben eines
                        # Laufs ersetzt NUR unbenannte Zeilen — Nutzer-Benennungen
                        # ueberleben Abbruch und Boot-Resume. GEZAEHLT, nie still.
                        benannt_behalten += 1
                        bleib.append(z)
        # .313 (User 21.08., 'nicht automatisch rausnehmen, nur weil ich die
        # schon mal geprueft habe'): die VERWORFEN-ERBSCHAFT von .105 (ein neuer
        # Anker, der einen frueher verworfenen wieder-erntet, erbte das
        # Verworfen still und verlor seine Crops) ist ABGESCHALTET. Jede
        # geerntete Gruppe bleibt unbenannt stehen, bis der User sie benennt,
        # ueberspringt oder loescht; verworfene Zeilen frueherer Laeufe bleiben
        # als Zeile erhalten, urteilen aber nicht mehr ueber neue.
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), prefix=".anker.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for z in bleib:
                    f.write(z + "\n")
                for a in saetze:
                    f.write(json.dumps(a, ensure_ascii=False, allow_nan=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    return len(bleib), kaputt, benannt_behalten


def anker_phase_fahren(data_dir, lauf_dir, lauf_id, events_liste, schwellen, clusterer,
                       version, log, fortschreiben):
    """Die komplette Anker-Phase, dienst-frei (verifyd reicht Config-Schwellen,
    Clusterer und Callbacks herein). fortschreiben(**updates) -> zustand | None;
    None heisst 'Lauf wurde abgebrochen' => sofort aussteigen (Ernte-Semantik).
    -> Ergebnis-Dict oder None bei Abbruch. Wirft NICHT (Fehler faengt der Aufrufer)."""
    t0 = time.time()
    if int(schwellen["anker_deckel"]) > int(schwellen["anker_deckel_hart"]):
        # .83: Fehl-Konfiguration faellt am ANFANG mit Klartext, nicht am Phasen-Ende
        fortschreiben(phase="anker", fortschritt={
            "status": f"anchor stage failed: anker_deckel ({schwellen['anker_deckel']}) "
                      f"must not exceed anker_deckel_hart ({schwellen['anker_deckel_hart']}) "
                      "— fix the two values in Settings"})
        return None
    if fortschreiben(phase="anker", fortschritt={"status": "grouping starting"}) is None:
        return None
    dg = durchgaenge_bilden(events_liste, schwellen["szenario_gap_min"])
    alle_v, s_ges = [], 0
    fehlend = kaputt_zeilen = degeneriert = 0
    dg_mit_material = 0
    for i, d in enumerate(dg):
        kands, dfehl, dkaputt = s_kandidaten_lesen(lauf_dir, d["eids"])
        s_ges += len(kands)
        fehlend += dfehl
        kaputt_zeilen += dkaputt
        if kands:
            dg_mit_material += 1
        vs, ddeg = stufe1_vertreter(kands, sim=schwellen["anker_sim1"], clusterer=clusterer)
        degeneriert += ddeg
        for v in vs:
            v["durchgang_start"] = d["start"]
        alle_v.extend(vs)
        if (i + 1) % 5 == 0:     # .85: 5er-Schritte — bei kleinen Laeufen feuerte der 25er nie
            if fortschreiben(fortschritt={"status": f"grouping pass {i + 1}/{len(dg)}"}) is None:
                return None
    if s_ges == 0 and fehlend > 0:
        # .83 (Widerleger A2): Material WEG ist ein FEHLER, kein 0-Fund — der alte Text
        # schob es auf Kameras/Zonen des Nutzers und ein Neuschreiben haette die
        # bestehenden Anker dieses Laufs geloescht. Alt-Anker bleiben unangetastet.
        fortschreiben(fortschritt={
            "status": f"anchor stage failed: {fehlend} candidate file(s) missing — "
                      "harvest data is gone (aborted run? trashed folder?); "
                      "keeping the existing anchors untouched"})
        log(f"anchor stage failed (run {lauf_id}): harvest data missing "
            f"({fehlend} candidate files) — existing anchors kept")
        return None
    cl, runden, ungeclustert = stufe2_clustern(
        alle_v, sim=schwellen["anker_sim2"], deckel=schwellen["anker_deckel"],
        deckel_hart=schwellen["anker_deckel_hart"], clusterer=clusterer, log=log)
    zents = [zentroid([v["emb"] for v in c]) or c[0]["emb"] for c in cl]
    margen = margen_bewerten(cl, zents, hart_schwelle=schwellen["anker_hart"],
                             k_min=schwellen["anker_k_min"])
    saetze = anker_datensaetze(cl, margen, lauf_id, schwellen, version)
    # .83 (Widerleger B1): Abbruch-Check DIREKT vor dem Schreiben — vorher konnte ein
    # Abort waehrend Stufe 2 noch 74 Zeilen mit Pfaden ins frisch getrashte Material
    # persistieren und 'finished' melden.
    if fortschreiben(fortschritt={"status": "writing anchors"}) is None:
        log(f"anchor stage aborted before writing (run {lauf_id}) — nothing persisted")
        return None
    fremde, kaputt, benannt_behalten = anker_lauf_schreiben(data_dir, saetze, lauf_id)
    if benannt_behalten:
        log(f"anchor stage: {benannt_behalten} named anchors kept (never rewritten)")
    dauer = round(time.time() - t0, 1)
    st_zahl = {}
    for m in margen:
        st_zahl[m["status"]] = st_zahl.get(m["status"], 0) + 1
    vorschlaege_n = sum(1 for m in margen if m.get("vorschlaege"))
    basis = {"passes with material": f"{dg_mit_material}/{len(dg)}",
             "analysing": None}                # .87: Ernte-Rest nie am Anker-Ergebnis kleben lassen
    if fehlend:
        basis["events without harvest data"] = fehlend
    if kaputt_zeilen:
        basis["unreadable candidate lines"] = kaputt_zeilen
    if degeneriert:
        basis["degenerate embeddings skipped"] = degeneriert
    if ungeclustert:
        basis["leftover single clusters (cap)"] = ungeclustert
    if runden > 1:
        basis["stage-2 rounds (approximation)"] = runden
    if not saetze:
        grund = ("no events in this run" if not events_liste else
                 "no anchor-ready faces (S) in the harvest — the events carry no frontal "
                 "faces that pass the anchor gates (det/edge/sharpness/pose); a camera or "
                 "zone that sees faces head-on would change that")
        fortschreiben(fortschritt=dict(basis, status=f"anchors: none — {grund}"))
        log(f"anchor stage finished (run {lauf_id}): 0 clusters ({grund})")
    else:
        fortschreiben(fortschritt=dict(
            basis, status="anchors ready — open a cluster to name it",
            anchors=len(saetze), ok=st_zahl.get("ok", 0),
            hart=st_zahl.get("hart", 0), thin=st_zahl.get("zu_duenn", 0),
            unconfirmed=st_zahl.get("unbestaetigt", 0),
            **({"merge suggestions": vorschlaege_n} if vorschlaege_n else {})))
        log(f"anchor stage finished (run {lauf_id}): {len(saetze)} clusters "
            f"(ok {st_zahl.get('ok', 0)} / hart {st_zahl.get('hart', 0)} / "
            f"thin {st_zahl.get('zu_duenn', 0)} / unconfirmed {st_zahl.get('unbestaetigt', 0)}"
            f"{f' / {vorschlaege_n} merge suggestions' if vorschlaege_n else ''}) "
            f"from {dg_mit_material}/{len(dg)} passes / {s_ges} anchor-ready faces; "
            f"stage2 n={len(alle_v)} rounds={runden} in {dauer}s"
            + (f"; NOTE {kaputt} unreadable anchor lines carried over" if kaputt else ""))
    return {"anker": len(saetze), "status_zahlen": st_zahl, "durchgaenge": len(dg),
            "durchgaenge_mit_material": dg_mit_material, "s": s_ges,
            "vertreter": len(alle_v), "runden": runden, "ungeclustert": ungeclustert,
            "fehlend": fehlend, "kaputt_zeilen": kaputt_zeilen, "dauer_s": dauer}
