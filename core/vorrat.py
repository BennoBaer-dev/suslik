"""core/vorrat — Szenario-Konsens + Katalog-Angebots-Entscheid des Lernvorrats
(Bauplan bauplan_vorrat.md B3, 20.08.2026).

Reine Funktionen ohne Dienst-Zustand (Kontrakt wie ernte/anker): der Aufrufer
(verifyd, Lernlauf-Fluss INNERHALB der Anker-Phase — bewusst KEIN eigener
Phasenwert, Widerleger W2.1: PHASEN/lauf_abgeschlossen/verifyd-Literal haetten
den Wizard dauerhaft blockiert) reicht Schwellen, Events und Referenz-Matrizen
herein.

Der KONSENS ist das Szenario-Prinzip als Filter (Messbasis 20.08., Mittags-
Durchgang): echte Gesichter EINES Durchgangs aehneln einander ueber alle
Kameras (beste Paar-Aehnlichkeit 0,59-0,90), ein Fremdgesicht (Hund) schliesst
an niemanden an (0,15). Verglichen werden NUR die v-Kandidaten des Durchgangs
untereinander — gegen ALLE Detektionen wuerde die Hunde-Spur sich selbst
bestaetigen (58er-Eigencluster, gemessen). Konsens belegt KONSISTENZ, nicht
Identitaet (Widerleger W2.5) — deshalb verlangt das Angebot ZUSAETZLICH die
Identitaets-Stufe 'sicher' (eigen >= sim_min); das 0,30-0,45-Fenster der
Bestands-Suche ist hier GESPERRT (reale Fremd-Paare dieser Installation liegen
bei 0,27-0,31).

Ohne brauchbare Referenz-Matrizen wird NICHT geurteilt: der Aufrufer setzt die
Bewertung dann LAUT aus (W2.13 — mit leeren Matrizen waere jeder Kandidat
'empfohlen' fuer niemanden). Der Kaltstart einer Installation laeuft nicht
ueber den Vorrat, sondern ueber die Anker-/Unbekannt-Maschinerie."""
import json
import os
import tempfile

import numpy as np


def v_zeilen_lesen(lauf_dir, eids):
    """v-Kandidaten (v==True, datei_v gesetzt) aus den Kandidaten-Dateien der
    Events — Fehlendes/Kaputtes GEZAEHLT, nie still (Muster s_kandidaten_lesen).
    -> (v_zeilen, fehlende_dateien, kaputte_zeilen)"""
    from core import ernte as _ern
    vz, fehlend, kaputt = [], 0, 0
    for eid in eids:
        pfad = _ern.kandidaten_pfad(lauf_dir, eid)
        if not os.path.exists(pfad):
            fehlend += 1
            continue
        with open(pfad, encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    z = json.loads(zeile)
                except Exception:
                    kaputt += 1
                    continue
                if z.get("v") and z.get("datei_v") and z.get("emb"):
                    vz.append(z)
    return vz, fehlend, kaputt


def konsens_rechnen(vz):
    """Je v-Kandidat die beste Cosinus-Aehnlichkeit zu einem ANDEREN
    v-Kandidaten desselben Durchgangs aus einem anderen Frame ((eid, t)
    verschieden — die Kandidaten-Zeile traegt keinen Frame-Index, t auf 2
    Stellen ist im 3-fps-Raster eindeutig je Frame).
    -> Liste gleicher Laenge: float oder None (= unbestimmbar, kein anderer
    Frame vorhanden)."""
    if not vz:
        return []
    E = np.asarray([z["emb"] for z in vz], np.float32)
    E /= (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
    S = E @ E.T
    frames = [(z["eid"], z["t"]) for z in vz]
    aus = []
    for i in range(len(vz)):
        andere = [float(S[i, j]) for j in range(len(vz))
                  if j != i and frames[j] != frames[i]]
        aus.append(round(max(andere), 4) if andere else None)
    return aus


def _identitaet(refs, v):
    """Bester Referenz-Treffer + bester Fremd-Treffer.
    -> (person, eigen, fremd) — person/eigen None ohne Matrizen."""
    best_p, best_s, zweit = None, -1.0, -1.0
    for p, M in refs.items():
        if not len(M):
            continue
        s = float((M @ v).max())
        if s > best_s:
            best_p, best_s, zweit = p, s, best_s
        elif s > zweit:
            zweit = s
    if best_p is None:
        return None, None, None
    return best_p, round(best_s, 4), (round(zweit, 4) if zweit > -1.0 else None)


def angebote_bewerten(lauf_dir, events_liste, schwellen, refs,
                      sim_min=0.45, sim_neu=0.75):
    """Durchgaenge bilden (EINE Gap-Regel: core.anker.durchgaenge_bilden — nie
    eine dritte Gap-Rechnung, szenarien.py:83), Konsens rechnen, Angebots-
    Entscheid faellen und <lauf_dir>/vorrat.jsonl ATOMAR NEU schreiben (die
    Bewertung laeuft einmal je Anker-Phase; ein Boot-Resume wiederholt sie
    idempotent, Alt-Zeilen eines Vorlaufs bleiben nie liegen).

    Entscheid je v-Kandidat (jede Ablehnung traegt ihren Grund):
      1. Konsens >= vorrat_konsens_min; unbestimmbar (einziger Frame) ist KEIN
         Ausschluss — dann traegt allein die Identitaets-Stufe (der Hund-Fall
         bleibt draussen: unverbunden UND unbekannt). Bestimmbar-und-drunter
         ist raus.
      2. Norm >= katalog_norm_min bzw. _profil (die Qualitaetslinie des Users —
         auf der NORM-Achse die einzige Grenze, kein Zahlen-Deckel).
      3. Identitaet 'sicher': eigen >= sim_min; fremd >= eigen -> raus;
         eigen >= sim_neu -> gedeckt (Bestands-Duplikat).
    -> Bilanz-Dict (v_gesamt, angebote, gruende, durchgaenge, fehlend, kaputt)."""
    from core.anker import durchgaenge_bilden
    dg = durchgaenge_bilden(events_liste, schwellen["szenario_gap_min"])
    zeilen, gruende = [], {}
    fehlend = kaputt = 0

    def _grund(name):
        gruende[name] = gruende.get(name, 0) + 1

    for d in dg:
        vz, dfehl, dkaputt = v_zeilen_lesen(lauf_dir, d["eids"])
        fehlend += dfehl
        kaputt += dkaputt
        kw = konsens_rechnen(vz)
        dg_zeilen = []
        for z, k in zip(vz, kw):
            person, eigen, fremd = _identitaet(refs, np.asarray(z["emb"], np.float32))
            linie = (schwellen["katalog_norm_min_profil"]
                     if (z.get("front_kps") is not None
                         and z["front_kps"] < schwellen["vorrat_front_profil"])
                     else schwellen["katalog_norm_min"])
            angebot, grund = False, None
            if k is not None and k < schwellen["vorrat_konsens_min"]:
                grund = "konsens"           # der Hund-Fall: kein Anschluss ans Szenario
            elif z["norm"] < linie:
                grund = "unter_linie"
            elif eigen is None:
                grund = "keine_referenzen"  # Aufrufer setzt eigentlich vorher aus
            elif fremd is not None and fremd >= eigen:
                grund = "fremd_naeher"
            elif eigen >= sim_neu:
                grund = "gedeckt"
            elif eigen < sim_min:
                grund = "id_unsicher"       # 0,30-Fenster BEWUSST gesperrt (W2.5)
            else:
                angebot = True
            if grund:
                _grund(grund)
            dg_zeilen.append({
                "eid": z["eid"], "kamera": z.get("kamera"), "t": z["t"],
                "ts": z.get("ts"), "datei_v": z["datei_v"], "kante": z["kante"],
                "sharp": z["sharp"], "norm": z["norm"],
                "front_kps": z.get("front_kps"), "richtung": z.get("richtung"),
                "konsens": k, "person": person, "sim": eigen, "fremd": fremd,
                "durchgang_start": round(float(d["start"]), 1),
                "auch_anker": bool(z.get("datei")),   # W1.23: markiert, nie verschwiegen
                "modell": z.get("modell"),
                "emb": z["emb"],                       # A2-Beiwert fuer die Uebernahme
                "angebot": angebot, "grund": grund})
        # Zwillings-Zusammenfassung (.307, User-Go 20.08.: 'Nachbar-Frame-
        # Zwillinge zusammenfassen'): innerhalb EINES Durchgangs behaelt von
        # nahezu identischen Angeboten (cos >= vorrat_zwilling_sim, gemessen:
        # Nachbar-Frames ~1,0, echte Vielfalt 0,41-0,70) das norm-staerkste
        # sein Angebot, die anderen fallen DEKLARIERT (grund 'zwilling',
        # zwilling_von zeigt aufs behaltene). Kein Key im Regime (Alt-Lauf)
        # -> keine Zusammenfassung, Alt-Verhalten.
        zw = schwellen.get("vorrat_zwilling_sim")
        if zw:
            behalten = []
            for z in sorted((x for x in dg_zeilen if x["angebot"]),
                            key=lambda x: -(x["norm"] or 0)):
                v = np.asarray(z["emb"], np.float32)
                v /= (np.linalg.norm(v) + 1e-9)
                naechster = None
                for b in behalten:
                    if float(v @ b[0]) >= float(zw):
                        naechster = b[1]
                        break
                if naechster is None:
                    behalten.append((v, z))
                else:
                    z["angebot"] = False
                    z["grund"] = "zwilling"
                    z["zwilling_von"] = naechster["datei_v"]
                    _grund("zwilling")
        zeilen.extend(dg_zeilen)
    # Atomar NEU schreiben (mkstemp-Muster wie anker_lauf_schreiben)
    fd, tmp = tempfile.mkstemp(dir=lauf_dir, prefix=".vorrat.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for z in zeilen:
                f.write(json.dumps(z, ensure_ascii=False, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, os.path.join(lauf_dir, "vorrat.jsonl"))
        # mkstemp-0600-Falle (Backup-Befund 17.08., hier 21.08. erneut gefunden):
        # lesbar fuer Backup und Host-Werkzeuge, nicht nur fuer den Dienst-User.
        os.chmod(os.path.join(lauf_dir, "vorrat.jsonl"), 0o644)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return {"v_gesamt": len(zeilen),
            "angebote": sum(1 for z in zeilen if z["angebot"]),
            "gruende": gruende, "durchgaenge": len(dg),
            "fehlend": fehlend, "kaputt": kaputt}


def angebote_lesen(data_dir, uebernommen=None):
    """Offene Katalog-Angebote ALLER noch existierenden Lernlaeufe — die
    Lebenszyklus-Loesung aus der Konzept-QS (W2.10): kein Misch-File, kein
    Lock; ein geloeschter/getrashter Lauf nimmt seine Angebote automatisch
    mit. uebernommen = {(eid, datei_v)} bereits uebernommener Angebote
    (aus refs_meta, Aufrufer liefert) wird ausgeblendet.
    -> Liste [{lauf_id, ...vorrat-Zeile ohne emb...}] neueste zuerst."""
    wurzel = os.path.join(data_dir, "state", "lernlauf")
    uebernommen = uebernommen or set()
    aus = []
    try:
        laeufe = sorted((d for d in os.listdir(wurzel)
                         if d.startswith(("L", "B")) and   # B = Bruecken-Laeufe (.308)
                         os.path.isfile(os.path.join(wurzel, d, "vorrat.jsonl"))),
                        reverse=True)
    except FileNotFoundError:
        return aus
    for lid in laeufe:
        with open(os.path.join(wurzel, lid, "vorrat.jsonl"), encoding="utf-8") as f:
            for zeile in f:
                try:
                    z = json.loads(zeile)
                except Exception:
                    continue
                if not z.get("angebot"):
                    continue
                if (z.get("eid"), z.get("datei_v")) in uebernommen:
                    continue
                if not os.path.isfile(os.path.join(wurzel, lid, z["datei_v"])):
                    continue                     # Datei weg -> Angebot weg, nie tote Kachel
                z = {k: v for k, v in z.items() if k != "emb"}   # Anzeige braucht den Vektor nicht
                z["lauf_id"] = lid
                aus.append(z)
    aus.sort(key=lambda z: -(z.get("norm") or 0))
    return aus


def beiwert_nachschlagen(data_dir, lauf_id, datei_v):
    """Der A2-Embedding-Beiwert eines Angebots, SERVERSEITIG aus der
    vorrat.jsonl des Laufs (nie aus dem Request — W2.11).
    -> (emb_liste, zeile) oder (None, None)."""
    p = os.path.join(data_dir, "state", "lernlauf", str(lauf_id), "vorrat.jsonl")
    if not os.path.isfile(p):
        return None, None
    with open(p, encoding="utf-8") as f:
        for zeile in f:
            try:
                z = json.loads(zeile)
            except Exception:
                continue
            if z.get("datei_v") == datei_v and z.get("emb"):
                return z["emb"], z
    return None, None
