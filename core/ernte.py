"""core/ernte — Frontal-Ernte (E2 = Konzept §P1; Lern-Bauplan §2/E2).

EIGENER Ernte-Pfad, ausdruecklich AUCH fuer bekannte Personen (§1B: der Bestands-
Sammelpfad verwirft alles >= 0,42 zur naechsten bekannten Person — Anker-Aufwertung
waere damit unmoeglich). Er ersetzt den Bestand NICHT: anlernen._sammle_intern
bleibt byte-unangetastet (maschinell: qs-Stufe SAMMLE-CHARAKTERISIERUNG).

Gates (V0.5 GEMESSEN, kalibrierte Messreihe — Werte kommen als
AUSLIEFERUNGS-DEFAULTS aus der Config, hier steht KEINE Zahl [§2.4b]):
  L (Ernte-Einlass)  = NOT Objekt-Signatur (ist_fehldetektion; die fd_*-Schwellen
                       SIND die Stellschrauben von L). 98,8 % echter Gesichter passieren.
  M (bildwuerdig)    = L UND det >= m_det_min UND kante >= m_kante_min UND
                       sharp >= m_sharp_min — nur M-Kandidaten bekommen einen Crop.
  S (Anker-tauglich) = M UND det >= s_det_min UND |pitch|,|yaw|,|roll| <= s_winkel_max.
                       S wird hier nur AUSGEWERTET/gezaehlt — die Anker-BILDUNG ist E3.
GERUNDET WIRD VOR DEM GATE (Widerleger .75/L3: sonst ist die Entscheidung aus der
persistierten Zeile nicht reproduzierbar — realer Fall det 0,5995 -> Zeile 0,6/m:false,
Nachrechnung m:true). Zeile und Entscheidung rechnen mit DENSELBEN Werten.

Persistenz: JE EVENT eine eigene Datei kandidaten/<eid>.jsonl, beim (Wieder-)Ernten
NEU GESCHRIEBEN (Widerleger .75: append-only ernte.jsonl duplizierte das
unterbrochene Event beim Resume und liess Teilzeilen gescheiterter Jobs ungezaehlt
zurueck — die Stuetzzahl k>=5 der Anker haette das verfaelscht). pose = ECHTE
Vorzeichen-Winkel aus fc.pose [pitch, yaw, roll] (NICHT das analyze.py:242-
Altmuster), det/front DREI Nachkommastellen, kante eigenes Feld. Durchgangs-
Zuordnung traegt E3 nach (eid/kamera/ts/t je Zeile machen die Datei selbsttragend).

Kontrakt wie auftritte.py: reine Funktionen, Pfade/Schwellen als Parameter, kein
Dienst-Import; schwere Imports (cv2/decode/face_audit) LAZY in ernte_event.
"""
import glob
import json
import os

# Pflicht-Schwellen, die der Aufrufer aus der Config liefern MUSS (kein Default hier —
# Allgemeinheits-Wache §2.4b: fehlt einer, ist das ein Verdrahtungsfehler und faellt laut).
# det_thresh gehoert dazu (Widerleger .75: set_det_size resettet den SCRFD-Wert auf den
# Library-Default — ohne expliziten Re-Bind erntet der Lauf eine ANDERE Detektionsmenge
# als der Urteilspfad, waehrend der Wizard das Gegenteil anzeigt).
SCHWELLEN_PFLICHT = ("det_thresh", "fd_front_min", "fd_sharp_min", "fd_det_max",
                     "m_det_min", "m_kante_min", "m_sharp_min",
                     "s_det_min", "s_winkel_max")


def schwellen_pruefen(s):
    """-> Liste fehlender/leerer Schwellen-Keys (leer = vollstaendig)."""
    return [k for k in SCHWELLEN_PFLICHT if s.get(k) is None]


def front_aus_pose(pose):
    """Frontalitaet aus der Kopfpose — exakt die analyze.frontality-Pose-Formel
    (pose[0]/pose[1] als Betraege), damit die fd-Kalibrierung 1:1 gilt."""
    a, b = abs(float(pose[0])), abs(float(pose[1]))
    return max(0.0, 1.0 - (a + b) / 90.0)


def gate_l(fd):
    """L = Ernte-Einlass: NUR die NOT-Objekt-Signatur (V0.5: jede Zusatzschranke
    kostet mehr echte Gesichter als sie Objekte entfernt)."""
    return not fd


def gate_m(fd, det, kante, sharp, s):
    return (gate_l(fd) and det >= s["m_det_min"] and kante >= s["m_kante_min"]
            and sharp >= s["m_sharp_min"])


def gate_s(fd, det, kante, sharp, pose, s):
    """S nur AUSWERTEN (E3 bildet die Anker). pose = [pitch, yaw, roll] mit
    Vorzeichen — als BELIEBIGE Zahlen-Sequenz (fc.pose ist ein numpy-Array; ein
    isinstance-list-Guard liess im Echtlauf .74 ALLE 38 S-Faelle zu False kippen)."""
    if not gate_m(fd, det, kante, sharp, s):
        return False
    try:
        winkel = [float(w) for w in pose]
    except (TypeError, ValueError):
        return False
    if len(winkel) != 3:
        return False
    return (det >= s["s_det_min"]
            and all(abs(w) <= s["s_winkel_max"] for w in winkel))


def kandidat_zeile(eid, kamera, ts, t, bbox, det, front, sharp, kante, pose,
                   emb_vec, modell, m, s_flag, datei):
    """Eine Kandidaten-Zeile — die Rundungsregeln sind Teil des Vertrags (V0.5).
    det/front/sharp/pose kommen bereits GERUNDET herein (Gate == Zeile); die
    round()-Aufrufe hier sind idempotent und sichern den Vertrag am Rand ab."""
    return {"eid": eid, "kamera": kamera, "ts": round(float(ts), 1),
            "t": round(float(t), 2), "bbox": [int(v) for v in bbox],
            "kante": int(kante), "det": round(float(det), 3),
            "front": round(float(front), 3), "sharp": round(float(sharp), 1),
            "pose": [round(float(x), 1) for x in pose],
            "emb": [round(float(x), 5) for x in emb_vec], "modell": modell,
            "m": bool(m), "s": bool(s_flag), "datei": datei}


def zaehler_pruefen(z):
    """Summen-Invariante (E2-QS): jede Detektion landet in GENAU einer Kategorie.
    -> Fehlertext oder None."""
    soll = z.get("fd", 0) + z.get("ohne_pose", 0) + z.get("kandidaten", 0)
    if z.get("detektionen", 0) != soll:
        return (f"zaehler-invariante verletzt: detektionen {z.get('detektionen')} != "
                f"fd {z.get('fd')} + ohne_pose {z.get('ohne_pose')} + "
                f"kandidaten {z.get('kandidaten')}")
    if not (z.get("kandidaten", 0) >= z.get("m", 0) >= z.get("s", 0)):
        return f"gate-schachtelung verletzt: L {z.get('kandidaten')} >= M {z.get('m')} >= S {z.get('s')}"
    return None


def _eid_safe(eid):
    return str(eid).replace("/", "_")


def kandidaten_pfad(lauf_dir, eid):
    return os.path.join(lauf_dir, "kandidaten", _eid_safe(eid) + ".jsonl")


def event_aufraeumen(lauf_dir, eid):
    """Teil-Artefakte EINES Events entfernen (nach gescheitertem Job: die Zeilen/
    Crops eines abgebrochenen Jobs stuenden sonst gebucht-aber-ungezaehlt herum —
    Widerleger .75/L3 MUSS 1)."""
    es = _eid_safe(eid)
    try:
        os.unlink(kandidaten_pfad(lauf_dir, eid))
    except FileNotFoundError:
        pass
    for c in glob.glob(os.path.join(lauf_dir, "crops", es + "~*")):
        try:
            os.unlink(c)
        except FileNotFoundError:
            pass


def manifest_lesen(lauf_dir):
    p = os.path.join(lauf_dir, "manifest.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def manifest_schreiben(lauf_dir, manifest):
    """Das REGIME des Laufs einfrieren (Widerleger .75/L3+L4: ohne Manifest liest
    ein Resume die Schwellen frisch aus der Config — eine Datei truege dann zwei
    Gate-Regime ohne jede Spur, und .74-Altdaten waeren von .75 nicht
    unterscheidbar). Resume nutzt IMMER das Manifest, nie die aktuelle Config."""
    os.makedirs(lauf_dir, exist_ok=True)
    p = os.path.join(lauf_dir, "manifest.json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)
    return p


def ernte_event(vid, eid, kamera, ts, fps_sample, schwellen, lauf_dir, emb=None,
                ist_fd=None):
    """Frontal-Ernte fuer EIN Event (1 Event je Job — Live-Vorrang, Leitprinzip 5).

    Schreibt die Kandidaten (alle L-Passierer) in kandidaten/<eid>.jsonl — die Datei
    wird NEU geschrieben, ein Wieder-Ernten ist damit idempotent (kein Duplikat,
    keine Teilzeilen-Leiche). M-Crops (enges Gesicht = Lern-Material fuer E4b) nach
    crops/. -> Zaehler-Dict; 'unlesbar' True = 0 Frames lesbar; frames_gelesen/
    frames_soll/unvollstaendig immer dabei (Teil-Verlust ist KEIN stiller Erfolg).

    emb/ist_fd sind fuer Tests injizierbar; im Betrieb kommen sie aus face_audit
    (Worker-Factory haelt den Embedder warm)."""
    fehlt = schwellen_pruefen(schwellen)
    if fehlt:
        raise ValueError("ernte-schwellen unvollstaendig: " + ", ".join(fehlt))
    import cv2                      # lazy: Modul bleibt fuer Dienst/QS billig
    from decode import FrameIter    # CPU-Referenzpfad (Invariante: Analyse-Decode CPU)
    if emb is None:
        import face_audit
        emb = face_audit.Embedder()
    if ist_fd is None:
        from face_audit import ist_fehldetektion as ist_fd
    os.makedirs(os.path.join(lauf_dir, "crops"), exist_ok=True)
    os.makedirs(os.path.join(lauf_dir, "kandidaten"), exist_ok=True)
    event_aufraeumen(lauf_dir, eid)     # Reste eines frueheren (Teil-)Laufs weg
    frames = FrameIter(vid, fps_sample)
    if hasattr(emb, "ar_det_size"):
        emb.set_det_size(emb.ar_det_size(frames.breite, frames.hoehe))
    # det_thresh NACH set_det_size neu binden (prepare resettet auf den Library-
    # Default — exakt die analyze.py:226-Lehre; ohne das erntet der Lauf eine
    # andere Detektionsmenge als der Urteilspfad).
    if hasattr(emb, "app"):
        emb.app.det_model.det_thresh = float(schwellen["det_thresh"])
    z = {"detektionen": 0, "fd": 0, "ohne_pose": 0, "kandidaten": 0, "m": 0, "s": 0,
         "unlesbar": False, "frames_gelesen": 0, "frames_soll": None,
         "unvollstaendig": False, "letzter_m": None}
    eid_safe = _eid_safe(eid)
    pfad = kandidaten_pfad(lauf_dir, eid)
    modell = getattr(emb, "modell", "?")
    with open(pfad, "w", encoding="utf-8") as out:
        for i, frame in frames:
            for fc in emb.app.get(frame):
                z["detektionen"] += 1
                pose_roh = getattr(fc, "pose", None)
                if pose_roh is None or len(pose_roh) < 3:
                    z["ohne_pose"] += 1     # ohne Winkel keine fd-/S-Bewertung — nie still
                    continue
                # RUNDEN VOR DEM GATE: Zeile und Entscheidung rechnen mit denselben
                # Werten (sonst 1/309 nicht reproduzierbar, Widerleger .75/L3).
                pose = [round(float(w), 1) for w in pose_roh]
                x1, y1, x2, y2 = [max(0, int(v)) for v in fc.bbox]
                kante = min(x2 - x1, y2 - y1)
                det = round(float(fc.det_score), 3)
                front = round(front_aus_pose(pose), 3)
                crop = frame[y1:y2, x1:x2]
                sharp = round(float(cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY),
                                                  cv2.CV_64F).var()) if crop.size else 0.0, 1)
                fd = bool(ist_fd(front, sharp, det, schwellen["fd_front_min"],
                                 schwellen["fd_sharp_min"], schwellen["fd_det_max"]))
                if fd:
                    z["fd"] += 1
                    continue
                m = gate_m(fd, det, kante, sharp, schwellen)
                s_flag = gate_s(fd, det, kante, sharp, pose, schwellen)
                t = i / frames.fps
                datei = None
                if m:                       # nur Bildwuerdiges kostet Platte (Konzept §P1)
                    kid = f"{eid_safe}~{i}~{z['kandidaten']}"
                    datei = os.path.join("crops", kid + ".jpg")
                    if not cv2.imwrite(os.path.join(lauf_dir, datei), crop.copy()):
                        # volle Platte u.ae.: LAUT statt Zeile-mit-totem-Pfad
                        raise OSError(f"crop nicht schreibbar: {datei}")
                    z["letzter_m"] = {"kamera": kamera, "t": round(t, 1)}
                zeile = kandidat_zeile(eid, kamera, ts, t, (x1, y1, x2, y2), det,
                                       front, sharp, kante, pose,
                                       fc.normed_embedding, modell, m, s_flag, datei)
                out.write(json.dumps(zeile, ensure_ascii=False) + "\n")
                out.flush()
                z["kandidaten"] += 1
                z["m"] += 1 if m else 0
                z["s"] += 1 if s_flag else 0
        out.flush()
        os.fsync(out.fileno())              # gleiche Durabilitaet wie fertig.jsonl
    z["frames_gelesen"] = frames.gelesen
    z["frames_soll"] = frames.soll
    z["unvollstaendig"] = bool(frames.unvollstaendig)
    if frames.gelesen == 0:
        z["unlesbar"] = True
    return z


def fertig_lesen(lauf_dir):
    """Resume-Grundlage: bereits geerntete Events (fertig.jsonl) -> (eids, zaehler_summe).
    Kaputte Zeilen werden gezaehlt UND ihre eids fehlen im Set -> die Events werden
    neu geerntet (idempotent dank Datei-je-Event), nie still uebersprungen."""
    p = os.path.join(lauf_dir, "fertig.jsonl")
    eids, summe, kaputt = set(), {}, 0
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    d = json.loads(zeile)
                    eids.add(d["eid"])
                    for k in ("kandidaten", "m", "s", "fd", "ohne_pose", "detektionen"):
                        summe[k] = summe.get(k, 0) + int(d.get(k) or 0)
                    for k in ("unlesbar", "ohne_gesicht", "fehler", "unvollstaendig"):
                        summe[k] = summe.get(k, 0) + (1 if d.get(k) else 0)
                except Exception:
                    kaputt += 1
    summe["kaputt"] = kaputt
    return eids, summe


def fertig_anhaengen(lauf_dir, eintrag):
    """Ein Event als erledigt festhalten (geflusht — Absturz kostet hoechstens das
    laufende Event, das beim Resume idempotent NEU geerntet wird, Konzept §4)."""
    os.makedirs(lauf_dir, exist_ok=True)
    p = os.path.join(lauf_dir, "fertig.jsonl")
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def bestand_pruefen(lauf_dir):
    """Datei-gegen-Zaehler-Wache (Widerleger .75/L3: zaehler_pruefen prueft ein Dict
    gegen sich selbst — DIESE Funktion prueft die Buecher gegen die Platte).
    -> Liste Befund-Texte (leer = konsistent). Prueft je ok-Event: Zeilenzahl der
    Kandidaten-Datei == gebuchte kandidaten; jeder m-Crop existiert."""
    befunde = []
    eids_ok = {}
    p = os.path.join(lauf_dir, "fertig.jsonl")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for zeile in f:
                try:
                    d = json.loads(zeile)
                except Exception:
                    continue
                if d.get("ok"):
                    eids_ok[d["eid"]] = int(d.get("kandidaten") or 0)
    for eid, soll in eids_ok.items():
        kp = kandidaten_pfad(lauf_dir, eid)
        zeilen = 0
        if os.path.exists(kp):
            with open(kp, encoding="utf-8") as f:
                for zeile in f:
                    if not zeile.strip():
                        continue
                    zeilen += 1
                    try:
                        d = json.loads(zeile)
                    except Exception:
                        befunde.append(f"{eid}: kandidaten-zeile unlesbar")
                        continue
                    if d.get("m") and d.get("datei"):
                        if not os.path.exists(os.path.join(lauf_dir, d["datei"])):
                            befunde.append(f"{eid}: crop fehlt ({d['datei']})")
        if zeilen != soll:
            befunde.append(f"{eid}: {zeilen} zeilen != {soll} gebucht")
    return befunde
