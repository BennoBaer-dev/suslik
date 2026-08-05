"""E4a Zug 2a — reine Logik des Benennungs-Flusses (Bauplan §E4a-UI-Fluss v2).

Kontrakt wie core/anker.py: reine Funktionen, ALLE Schwellen kommen vom Aufrufer
(Allgemeinheits-Wache — Defaults kalibriert der Erstlauf mit dem User, nichts
wird hier erfunden). Kein Dienst-Import, kein Video-Decode: gerechnet wird
AUSSCHLIESSLICH mit den im Anker-Store persistierten Feldern (Zug 1: bbox/ts/
emb je Mitglied, zentroid je Anker). Fehlt emb/zentroid (Alt-Anker vor der
Persistierung), liefern die Funktionen ein LAUTES Flag statt stiller Nullen —
die K1-Regel der Widerleger-Bilanz (nie "0 Duplikate" ohne Pruefbarkeit).

REIHUNGS-BEGRIFF (der EINE, Bauplan-SOLL "zwei unvereinbare Guete-Begriffe"):
lexikografisch (front absteigend, sharp absteigend, det absteigend, id
aufsteigend) — parameterfrei, deterministisch, keine erfundene Formel; eine
gemessene Skalar-Guete kann ihn spaeter ersetzen, dann HIER, nirgendwo sonst."""
import numpy as np


def _reihung(m):
    """Sortier-Schluessel der Empfehlungs-Reihung (bester zuerst via sorted())."""
    return (-float(m.get("front") or 0.0), -float(m.get("sharp") or 0.0),
            -float(m.get("det") or 0.0), str(m.get("datei", "")))


def _cos(a, b):
    va, vb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    na, nb = float(np.linalg.norm(va)), float(np.linalg.norm(vb))
    if na <= 0.0 or nb <= 0.0 or not (np.isfinite(va).all() and np.isfinite(vb).all()):
        return None
    return float(np.dot(va, vb) / (na * nb))


def perspektiv_bin(pose, yaw_grenze):
    """Sub-Bin INNERHALB des Gate-S-Fensters (Bauplan: E4a-Sub-Bins ⊂ Gate S;
    die V0.7-Profil-Bins ±40-75° bleiben E5). pose = [pitch, yaw, roll]."""
    try:
        yaw = float(pose[1])
    except (TypeError, IndexError, ValueError):
        return "frontal"
    if yaw <= -float(yaw_grenze):
        return "links"
    if yaw >= float(yaw_grenze):
        return "rechts"
    return "frontal"


def empfehlen(mitglieder, k_je_bin, yaw_grenze, dup_sim):
    """Empfehlungs-Analyse eines Ankers -> (bewertet, flags).
    bewertet = Liste in Mitglieder-Reihenfolge: {datei, bin, empfohlen, grund}
    (grund nur bei nicht-empfohlen — Nicht-Loeschen-Prinzip: alles bleibt
    sichtbar, nur begruendet zurueckgestuft). Drei Stufen, deterministisch:
    1. PHYSISCHER Schluessel (kamera, bbox) UEBER ALLE Events (stuetz_phys-
       Regel; die realen Dubletten liegen cross-event) — je Gruppe bleibt der
       Reihungs-Beste.
    2. Embedding-Nachbarn ueber dup_sim: gierig entlang der Reihung, Naehe zu
       einem bereits Empfohlenen stuft zurueck. Ohne emb -> flags['emb_fehlt']
       (Anzeige "duplicate check unavailable ..."), NIE stilles 0.
    3. Perspektiv-Bins (yaw_grenze), je Bin bleiben die besten k_je_bin."""
    flags = {"emb_fehlt": any(not m.get("emb") for m in mitglieder)}
    geordnet = sorted(mitglieder, key=_reihung)
    ergebnis = {}                                     # datei -> (empfohlen, grund, bin)
    phys_gesehen, empfohlene, bin_zahl = set(), [], {}
    for m in geordnet:
        d = str(m.get("datei", ""))
        b = perspektiv_bin(m.get("pose") or [], yaw_grenze)
        schluessel = (str(m.get("kamera", "?")), tuple(m.get("bbox") or ()))
        if schluessel in phys_gesehen and schluessel[1]:
            ergebnis[d] = (False, "duplicate detection (same camera and box)", b)
            continue
        phys_gesehen.add(schluessel)
        naher = None
        if m.get("emb") and not flags["emb_fehlt"]:
            for e in empfohlene:
                s = _cos(m["emb"], e["emb"])
                if s is not None and s >= float(dup_sim):
                    naher = e
                    break
        if naher is not None:
            ergebnis[d] = (False, f"near-identical to {str(naher.get('datei','')).rsplit('/',1)[-1]}", b)
            continue
        if bin_zahl.get(b, 0) >= int(k_je_bin):
            ergebnis[d] = (False, f"bin limit reached ({int(k_je_bin)} kept)", b)
            continue
        bin_zahl[b] = bin_zahl.get(b, 0) + 1
        empfohlene.append(m)
        ergebnis[d] = (True, None, b)
    bewertet = [{"datei": str(m.get("datei", "")), "bin": ergebnis[str(m.get("datei", ""))][2],
                 "empfohlen": ergebnis[str(m.get("datei", ""))][0],
                 "grund": ergebnis[str(m.get("datei", ""))][1]}
                for m in mitglieder]
    return bewertet, flags


def referenz_zentroide(refcache_pfad, modell):
    """Zentroide der Master-Personen aus dem Referenz-Cache (refcache.npz,
    Layout analyze.load_refs: Personenname -> Nx512 L2-normierte Embeddings,
    Meta-Block '§meta' mit '§modell'). Gleiche Renormierungs-Regel wie
    anker.zentroid — damit vergleicht person_vorschlag im selben Raum.
    Modell-Gate: nur wenn der Cache mit dem aktiven Recognition-Modell
    gerechnet wurde (nach Modellwechsel wird er ohnehin neu gebaut).
    Fehler -> {} (der Vorschlags-Layer darf die Seite nie brechen)."""
    import json as _json
    try:
        z = np.load(refcache_pfad, allow_pickle=True)
        mk = "§meta" if "§meta" in z.files else "meta"
        meta = _json.loads(str(z[mk]))
        if str(meta.get("§modell", "")).lower() != str(modell or "").lower():
            return {}
        zents = {}
        for p in z.files:
            if p == mk:
                continue
            m = np.asarray(z[p], dtype=np.float32)
            if m.ndim != 2 or not len(m) or not np.all(np.isfinite(m)):
                continue
            c = m.mean(axis=0)
            n = float(np.linalg.norm(c))
            if n < 1e-9:
                continue
            zents[p] = [round(float(x), 5) for x in (c / n)]
        return zents
    except Exception:
        return {}


def personen_quelle(master_personen, anker_zeilen, norm, referenz=None):
    """VEREINIGUNG aus Master-Ordnern und benannten, nicht uebernommenen Ankern
    (laufuebergreifend, nach normalisiertem Namen zusammengefasst) — Bauplan-MUSS
    'Dedup sieht benannte-nicht-uebernommene Personen'. norm = lernlauf.person_norm
    (injiziert, EINE Namensquelle). referenz = {name: zentroid} aus
    referenz_zentroide() — gibt den Master-Personen Vergleichs-Zentroide,
    damit person_vorschlag auch auf Referenz-Personen zeigen kann (vorher
    standen Master nur als Namen ohne Zentroid drin und der Vorschlag konnte
    nur anker-benannte Personen treffen; User-Fund 05.08.: 100er-Lauf voller
    Bewohner-Cluster ohne einen einzigen Vorschlag).
    -> {casefold_name: {name, zentroide, quellen}}"""
    quelle = {}
    for p in master_personen:
        n = norm(p)
        if n:
            quelle.setdefault(n.casefold(), {"name": n, "zentroide": [], "quellen": set()})
            quelle[n.casefold()]["quellen"].add("master")
    for name, zent in (referenz or {}).items():
        n = norm(name)
        if not n or n.casefold() not in quelle:
            continue                    # Referenzen nur fuer echte Master-Personen
        e = quelle[n.casefold()]
        e["quellen"].add("referenz")
        e["zentroide"].append(zent)
    for a in anker_zeilen:
        if a.get("status") == "benannt" and a.get("person"):
            n = norm(a["person"])
            e = quelle.setdefault(n.casefold(), {"name": n, "zentroide": [], "quellen": set()})
            e["quellen"].add("benannt")
            if a.get("zentroid"):
                e["zentroide"].append(a["zentroid"])
    return quelle


def person_vorschlag(anker_zentroid, quelle, schwelle):
    """Personen-Ebenen-Vorschlag ('looks like X — add there?'): bester Cosinus des
    Anker-Zentroids gegen die Zentroide der Vereinigung, nur ueber Schwelle.
    VORSCHLAG, nie Zwang; Bauplan-SOLL-Vorbehalt: das Zentroid-Cosinus-Mass ist
    am .83-Echtmaterial skalen-verschoben — Schwelle konservativ kalibrieren.
    Ohne anker_zentroid oder ohne Vergleichs-Zentroide -> (None, 'unpruefbar')."""
    if not anker_zentroid:
        return None, "unpruefbar (anchor predates embedding persistence)"
    best, best_sim, pruefbar = None, -1.0, False
    for e in quelle.values():
        for z in e["zentroide"]:
            s = _cos(anker_zentroid, z)
            if s is None:
                continue
            pruefbar = True
            if s > best_sim:
                best, best_sim = e, s
    if not pruefbar:
        return None, "unpruefbar (no comparable centroids)"
    if best_sim >= float(schwelle):
        return {"name": best["name"], "sim": round(best_sim, 3),
                "quellen": sorted(best["quellen"])}, None
    return None, None


def namens_kollision(name, quelle, norm):
    """Namens-Ebene (dritte Schutzebene): casefold-Treffer in der Vereinigung ->
    kanonischer Bestandsname (fuer \"'jane doe' matches existing 'Jane Doe'\"), sonst None."""
    n = norm(name)
    e = quelle.get(n.casefold()) if n else None
    return e["name"] if e else None


def benennungs_kontext(satz, alle_saetze, master_personen, werte, norm,
                       referenz=None):
    """Glue fuer die Benennungs-Seite (EIN Aufruf je Detail-GET, rein lesend):
    Empfehlung + Personen-Vereinigung (ohne den eigenen Anker) + Vorschlag.
    werte = {k_je_bin, yaw_grenze, dup_sim, vorschlag_schwelle} aus der
    Config-Whitelist (nichts hardcoden). Vorschlag rechnet gegen die Zentroide
    BENANNTER Anker UND (seit dem Referenz-Ausbau, User-Fund 05.08.) gegen die
    referenz-Zentroide der Master-Personen (referenz_zentroide(), Aufrufer
    laedt) — damit zeigt 'looks like' auch auf Personen, die nur ueber
    Referenzen im System sind."""
    bewertet, flags = empfehlen(satz.get("mitglieder") or [], werte["k_je_bin"],
                                werte["yaw_grenze"], werte["dup_sim"])
    quelle = personen_quelle(
        master_personen,
        [a for a in alle_saetze if a.get("anker_id") != satz.get("anker_id")],
        norm, referenz=referenz)
    vorschlag, _note = person_vorschlag(satz.get("zentroid"), quelle,
                                        werte["vorschlag_schwelle"])
    return {"bewertet": bewertet, "flags": flags,
            "personen": sorted(e["name"] for e in quelle.values()),
            "vorschlag": vorschlag}
