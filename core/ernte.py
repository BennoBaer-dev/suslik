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
Dienst-Import; schwere Imports (cv2/core.frames/face_audit) LAZY in ernte_event.
"""
import glob
import json
import os
import time

# Pflicht-Schwellen, die der Aufrufer aus der Config liefern MUSS (kein Default hier —
# Allgemeinheits-Wache §2.4b: fehlt einer, ist das ein Verdrahtungsfehler und faellt laut).
# det_thresh gehoert dazu (Widerleger .75: set_det_size resettet den SCRFD-Wert auf den
# Library-Default — ohne expliziten Re-Bind erntet der Lauf eine ANDERE Detektionsmenge
# als der Urteilspfad, waehrend der Wizard das Gegenteil anzeigt).
SCHWELLEN_PFLICHT = ("det_thresh", "fd_front_min", "fd_sharp_min", "fd_det_max",
                     "m_det_min", "m_kante_min", "m_sharp_min",
                     "s_det_min", "s_winkel_max")

# Vorrats-Achsen (Bauplan bauplan_vorrat.md B2, 20.08.2026) — BEWUSST NICHT in
# SCHWELLEN_PFLICHT: alte Lernlauf-Manifeste ohne diese Keys muessen resumierbar
# bleiben (Widerleger-Falle 5); fehlen sie, ist das v-Gate aus, deklariert im
# Zaehler (v_aus). Der Ernte-Anteil braucht genau diese sechs; Konsens-/Katalog-
# Schwellen gehoeren der Vorrat-Phase (core/vorrat.py) und wandern nur zum
# Einfrieren mit ins Manifest.
VORRAT_SCHLUESSEL = ("vorrat_norm_min", "vorrat_norm_min_profil",
                     "vorrat_front_profil", "vorrat_kante_min",
                     "vorrat_sharp_min", "vorrat_rand_faktor")


def schwellen_pruefen(s):
    """-> Liste fehlender/leerer Schwellen-Keys (leer = vollstaendig)."""
    return [k for k in SCHWELLEN_PFLICHT if s.get(k) is None]


def vorrat_schwellen_da(s):
    """Sind ALLE Vorrats-Schwellen vorhanden? (Teil-Bestueckung zaehlt als AUS —
    ein halbes Gate waere schlimmer als keins.)"""
    return all(s.get(k) is not None for k in VORRAT_SCHLUESSEL)


def front_aus_pose(pose):
    """Frontalitaet aus der Kopfpose — exakt die analyze.frontality-Pose-Formel
    (pose[0]/pose[1] als Betraege), damit die fd-Kalibrierung 1:1 gilt."""
    a, b = abs(float(pose[0])), abs(float(pose[1]))
    return max(0.0, 1.0 - (a + b) / 90.0)


def front_aus_kps(kps):
    """Frontalitaets-Proxy aus den FUENF SCRFD-Keypoints (1.0 frontal, 0.0 Profil)
    — WORTGLEICH der kps-Zweig von analyze.frontality bzw. dem Vorrats-Prototyp:
    die Profil-Grenze 0.61 und die Profil-Norm-Schwelle 21.5 sind auf DIESER
    Skala gemessen (Pose-Schichtung 20.08.). Das pose-basierte `front` der Ernte
    (front_aus_pose, pitch+yaw) bleibt daneben unveraendert bestehen — zwei
    deklarierte Skalen, keine Vermischung (Bauplan B2)."""
    if kps is None or len(kps) < 3:
        return None
    le, re, nose = kps[0], kps[1], kps[2]
    eye_cx = (le[0] + re[0]) / 2.0
    eye_dx = abs(re[0] - le[0]) or 1.0
    yaw_off = abs(nose[0] - eye_cx) / eye_dx
    return float(max(0.0, 1.0 - yaw_off / 0.45))


def richtung_aus_kps(kps, front_kps, profil_grenze):
    """Blickrichtungs-Etikett links/frontal/rechts (Kopfdrehung aus Betrachter-
    sicht, Vorzeichen des Nasen-Versatzes) — fuer die pose-gruppierte Anzeige
    des Vorrats (User 20.08.)."""
    if kps is None or len(kps) < 3 or front_kps is None:
        return None
    if front_kps >= profil_grenze:
        return "frontal"
    le, re, nose = kps[0], kps[1], kps[2]
    return "links" if float(nose[0]) < (le[0] + re[0]) / 2.0 else "rechts"


def gate_l(fd):
    """L = Ernte-Einlass: NUR die NOT-Objekt-Signatur (V0.5: jede Zusatzschranke
    kostet mehr echte Gesichter als sie Objekte entfernt)."""
    return not fd


def gate_m_vor(det, kante, sharp, s):
    """Der fd-FREIE Teil von M. Eigene Funktion, weil ihn die Vorschranke (§1 des
    Baus 'Ernte beschleunigen') VOR Landmarken/Pose braucht — und weil die drei
    Schwellen dann genau EINMAL im Code stehen (QS-Ebenen-Regel: nie ein zweites
    verstreutes Literal). gate_m bleibt Wort fuer Wort dieselbe Konjunktion."""
    return (det >= s["m_det_min"] and kante >= s["m_kante_min"]
            and sharp >= s["m_sharp_min"])


def gate_m(fd, det, kante, sharp, s):
    return gate_l(fd) and gate_m_vor(det, kante, sharp, s)


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


def gate_v_vor(fd, det, kante, sharp, s):
    """Vorrats-VORPRUEFUNG ohne Inferenz (Bauplan B2, Widerleger W2.7/W2.8):
    die Norm ist die teuerste Achse (~0,3 s je Gesicht auf CPU) und als
    Gesicht/Nicht-Gesicht-Trenner nirgends kalibriert — deshalb kommen die
    billigen Achsen inkl. der DETEKTOR-Pflichtachse zuerst, und nur Passierer
    bezahlen die Norm-Inferenz."""
    return gate_l(fd) and gate_v_vor_ohne_fd(det, kante, sharp, s)


def gate_v_vor_ohne_fd(det, kante, sharp, s):
    """Der fd-FREIE Teil von gate_v_vor — dieselbe Rolle wie gate_m_vor fuer M.
    ACHTUNG, die Latten sind ANDERE als bei M (Kante 40 statt 60, Schaerfe 600
    statt 60): V haengt nicht unter M, deshalb muss die Vorschranke BEIDE
    Teilpruefungen kennen und darf nicht die eine fuer die andere nehmen."""
    return (det >= s["m_det_min"] and kante >= s["vorrat_kante_min"]
            and sharp >= s["vorrat_sharp_min"])


def vorschranke(det, kante, sharp, s, v_aktiv):
    """Die billige VORPRUEFUNG der Ernte (bauplan_ernte_tempo.md §1, QS-korrigiert).

    Beide Gates sind Konjunktionen mit fd als EINEM Glied: wer an det/kante/sharp
    scheitert, ist raus — unabhaengig davon, was die Pose spaeter zu fd sagt. Wer
    also WEDER den fd-freien Teil von M NOCH den von V bestehen kann, ist sicher
    weder bildwuerdig noch vorratstauglich; fuer ihn lohnt weder Landmarke noch
    Pose noch Embedding. Ist der Vorrat aus, faellt sein Zweig weg (dann waeren
    seine Schwellen gar nicht im Regime).

    KEINE neue Schranke: es passiert genau, wer heute auch passieren wuerde —
    die Reihenfolge wird nur so gedreht, dass die teure Arbeit spaeter kommt."""
    return (gate_m_vor(det, kante, sharp, s)
            or (bool(v_aktiv) and gate_v_vor_ohne_fd(det, kante, sharp, s)))


def gate_v_norm(norm, front_kps, s):
    """Vorrats-Norm-Achse: Profil-Zweig unter der kps-Frontalitaets-Grenze
    (Profile tragen bei gleicher Identitaetsstaerke systematisch ~1 Punkt
    weniger Norm — Pose-Schichtung 20.08.)."""
    if norm is None:
        return False
    grenze = (s["vorrat_norm_min_profil"]
              if (front_kps is not None and front_kps < s["vorrat_front_profil"])
              else s["vorrat_norm_min"])
    return norm >= grenze


def kandidat_zeile(eid, kamera, ts, t, bbox, det, front, sharp, kante, pose,
                   emb_vec, modell, m, s_flag, datei,
                   norm=None, front_kps=None, richtung=None, v=False, datei_v=None,
                   struktur=None, quelle=None, luma=None):
    """Eine Kandidaten-Zeile — die Rundungsregeln sind Teil des Vertrags (V0.5).
    det/front/sharp/pose kommen bereits GERUNDET herein (Gate == Zeile); die
    round()-Aufrufe hier sind idempotent und sichern den Vertrag am Rand ab.
    Die Vorrats-Felder (Bauplan B2) stehen am SIGNATUR-ENDE mit Defaults:
    alle bestehenden Aufrufer und Leser (anker, QS-Fixfaelle) bleiben gueltig."""
    return {"eid": eid, "kamera": kamera, "ts": round(float(ts), 1),
            "t": round(float(t), 2), "bbox": [int(v) for v in bbox],
            "kante": int(kante), "det": round(float(det), 3),
            "front": round(float(front), 3), "sharp": round(float(sharp), 1),
            "pose": [round(float(x), 1) for x in pose],
            "emb": [round(float(x), 5) for x in emb_vec], "modell": modell,
            "m": bool(m), "s": bool(s_flag), "datei": datei,
            "norm": None if norm is None else round(float(norm), 4),
            "front_kps": None if front_kps is None else round(float(front_kps), 4),
            "richtung": richtung, "v": bool(v), "datei_v": datei_v,
            "struktur": None if struktur is None else round(float(struktur), 4),
            # .33x DATEIQUELLE: Herkunft des Clips ("datei" oder None=Frigate).
            # Sie wandert bis in die Anker-Kachel, damit dort kein /video/-Link
            # auf ein Event angeboten wird, das es bei Frigate nie gab
            # (Bauplan analysen/12, QS-Einwand B). Am SIGNATUR-ENDE mit Default,
            # wie die Vorrats-Felder: Alt-Aufrufer und Alt-Leser bleiben gueltig.
            "quelle": quelle,
            # BELICHTUNG (analysen/bauplan_belichtung.md E2, 26.08.): mittlere
            # Helligkeit des Kandidaten-Ausschnitts, int 0..255. Steht am
            # DICT-ENDE, nicht zwischen den Messwerten — sonst zeigte der
            # Byte-Beweis-Diff eine Schluessel-Umsortierung statt einer
            # Ergaenzung. Altzeilen ohne das Feld bleiben gueltig und gelten
            # ueberall als UNBEWERTET (nie als dunkel), Muster norm/struktur.
            "luma": luma}


def zaehler_pruefen(z):
    """Summen-Invariante (E2-QS): jede Detektion landet in GENAU einer Kategorie.
    VIERTER Topf seit der Vorschranke: `vorab_verworfen` (an det/kante/sharp
    gescheitert, bevor Pose und fd ueberhaupt gerechnet wurden — sie koennen
    per Konstruktion weder fd noch ohne_pose sein). Alt-Zaehler ohne den
    Schluessel zaehlen mit 0 und bleiben gueltig.
    -> Fehlertext oder None."""
    soll = (z.get("fd", 0) + z.get("ohne_pose", 0) + z.get("vorab_verworfen", 0)
            + z.get("kandidaten", 0))
    if z.get("detektionen", 0) != soll:
        return (f"zaehler-invariante verletzt: detektionen {z.get('detektionen')} != "
                f"fd {z.get('fd')} + ohne_pose {z.get('ohne_pose')} + "
                f"vorab_verworfen {z.get('vorab_verworfen', 0)} + "
                f"kandidaten {z.get('kandidaten')}")
    if not (z.get("kandidaten", 0) >= z.get("m", 0) >= z.get("s", 0)):
        return f"gate-schachtelung verletzt: L {z.get('kandidaten')} >= M {z.get('m')} >= S {z.get('s')}"
    if z.get("v", 0) > z.get("kandidaten", 0):
        # v ist NICHT in M geschachtelt (eigene Achsen: Kante 40 < m_kante 60),
        # aber jeder v-Kandidat ist ein L-Passierer.
        return f"v-schachtelung verletzt: V {z.get('v')} > L {z.get('kandidaten')}"
    return None


def _eid_safe(eid):
    return str(eid).replace("/", "_")


def kandidaten_pfad(lauf_dir, eid):
    return os.path.join(lauf_dir, "kandidaten", _eid_safe(eid) + ".jsonl")


# ------------------------------------------------------------ Fortschritts-Anzeige
# Zeitanteile der drei Ernte-Schritte, GEMESSEN 25.08.2026 auf Prod (Profiler ueber
# EINEN Ernte-Lauf: 1426 gelesene Bilder, 476 untersucht, 160 Gesichter, 29,4 s):
#   Gesichtssuche SCRFD    19,3 s = 66 %
#   Landmarken/Pose         9,2 s = 31 %
#   Rest                            3 %  (Bilder holen, Dekodieren, Farbumrechnung,
#                                         AdaFace, blobFromImage — die Posten liegen
#                                         INEINANDER und werden dem Erkennungs-
#                                         Schritt zugeschlagen statt einzeln gezeigt:
#                                         einem Betreiber sagen sie nichts.)
# EINE Quelle fuer Balkenbreiten und Gewichtung (bauplan_ernte_tempo.md §4) — die
# Anzeige holt sie hier, nie als zweites Literal im Blatt.
FORTSCHRITT_GEWICHTE = (("suchen", 0.66), ("pose", 0.31), ("erkennen", 0.03))

PULS_TAKT_S = 1.0          # Mindestabstand zweier Puls-Schreibungen
PULS_ALTER_MAX_S = 20.0    # aelterer Puls = kein laufendes Event mehr


def puls_pfad(lauf_dir):
    return os.path.join(lauf_dir, "ernte_puls.json")


def puls_schreiben(lauf_dir, daten):
    """Zaehlerstand des LAUFENDEN Events fuer die Anzeige — atomar (tmp+replace),
    damit ein Leser nie eine halbe Datei sieht, und NIE fatal: ein Schreibfehler
    darf eine Ernte nicht anfassen, er kostet hoechstens einen Balken.

    KEINE zweite Buchfuehrung (Plan §4/Risiko 5): geschrieben werden ausschliesslich
    Zaehler, die die Schleife ohnehin fuehrt, und das hoechstens im PULS_TAKT_S-Takt.
    Im heissen Pfad bleibt davon EIN Zeitvergleich je FRAME (nicht je Gesicht)."""
    p = puls_pfad(lauf_dir)
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False)
        os.replace(tmp, p)
    except OSError:
        pass


def puls_loeschen(lauf_dir):
    """Nach dem Event weg — ein stehengebliebener Puls waere ein Balken, der
    Arbeit behauptet, die niemand mehr tut."""
    try:
        os.unlink(puls_pfad(lauf_dir))
    except OSError:
        pass


def puls_lesen(lauf_dir, jetzt=None):
    """-> Puls-Dict des laufenden Events, oder None (fehlt/unlesbar/zu alt).
    Der Alters-Deckel faengt den Fall 'Worker gestorben, Datei liegt noch da'."""
    try:
        with open(puls_pfad(lauf_dir), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    jetzt = time.time() if jetzt is None else jetzt
    if jetzt - float(d.get("ts") or 0) > PULS_ALTER_MAX_S:
        return None
    return d


def fortschritt_rechnen(i, n, puls):
    """Balkenstaende aus dem, was der Lauf ohnehin kennt.
    i/n = fertige/geplante Events, puls = puls_lesen() des laufenden Events.
    -> {"gesamt": 0..1, "puls_da": bool, "gruppen": [{k, gewicht, anteil,
    wert, von}]} | None. puls_da=False heisst: gerade kein tickendes Event
    (Clip-Beschaffung zwischen zwei Events) — die Anzeige sagt das, statt
    eingefroren zu wirken (EINE Regel fuer Pass-Check und Wizard).

    Die drei Schritte laufen JE FRAME verschraenkt (suchen -> Pose -> erkennen),
    nicht nacheinander — ihr Fortschritt ist deshalb derselbe Frame-Anteil. Was die
    Gewichte tragen, ist die ZEITAUFTEILUNG (66/31/Rest): sie bestimmt die Breite
    der drei Balken, damit sichtbar wird, wo die Minute hingeht. Ein Schritt, der
    noch keine Arbeit hatte (kein Gesicht gefunden), bleibt leer und heisst in der
    Anzeige 'wartet'; er haelt den Gesamtbalken NICHT auf — der folgt allein dem
    Frame-Anteil, sonst stuende er auf einem gesichtslosen Clip bei 66 % still."""
    n = int(n or 0)
    if n <= 0:
        return None
    anteil, frames, soll = 0.0, 0, 0
    posen = erkannt = 0
    if puls:
        frames = int(puls.get("frames") or 0)
        soll = int(puls.get("frames_soll") or 0)
        if soll > 0:
            anteil = min(1.0, max(0.0, frames / float(soll)))
        posen = int(puls.get("posen") or 0)
        erkannt = int(puls.get("erkannt") or 0)
    stand = {"suchen": (frames, soll or None, frames > 0),
             "pose": (posen, None, posen > 0),
             "erkennen": (erkannt, None, erkannt > 0)}
    gruppen = []
    for k, g in FORTSCHRITT_GEWICHTE:
        wert, von, laeuft = stand[k]
        gruppen.append({"k": k, "gewicht": g, "wert": wert, "von": von,
                        "anteil": round(anteil, 4) if laeuft else 0.0})
    return {"gesamt": round(min(1.0, (int(i or 0) + anteil) / n), 4),
            "puls_da": bool(puls), "gruppen": gruppen}


def event_aufraeumen(lauf_dir, eid):
    """Teil-Artefakte EINES Events entfernen (nach gescheitertem Job: die Zeilen/
    Crops eines abgebrochenen Jobs stuenden sonst gebucht-aber-ungezaehlt herum —
    Widerleger .75/L3 MUSS 1)."""
    es = _eid_safe(eid)
    try:
        os.unlink(kandidaten_pfad(lauf_dir, eid))
    except FileNotFoundError:
        pass
    # Schreiber und Raeumer teilen EINE Namensregel je Ablage: crops/<eid>~* fuer
    # M, vorrat/v_<eid>_* fuer V (Bauplan B2; ohne den zweiten Glob blieben
    # v-Crops nach Wieder-Ernten als Waisen liegen — Widerleger W1.9).
    for muster in (os.path.join(lauf_dir, "crops", es + "~*"),
                   os.path.join(lauf_dir, "vorrat", "v_" + es + "_*")):
        for c in glob.glob(muster):
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


# ------------------------------------------------------------------ Zaehler-Topf
# Der Rueckgabe-Topf von ernte_event als EINE Quelle. Anlass (.343 einmal, .346
# dreimal binnen 24 h): Dienst und Routen reichen diese Felder ueber feste
# Schluessellisten weiter — kommt ein Topf dazu, faellt er an jeder nicht
# mitgezogenen Liste STILL heraus, und fertig.jsonl-Zeilen verletzen danach ihre
# eigene Summen-Invariante. tools/deckung_pruefen.py (Regel SK3) entdeckt solche
# Listen in verifyd/routes und prueft sie gegen ZAEHLER_FELDER.
#
# Paar-Form statt zweier Listen, weil die Einfuege-Reihenfolge Aussenwirkung hat:
# der Topf geht per json.dumps in fertig.jsonl, und die Reihenfolge der Schluessel
# dort soll sich durch eine Umbau-Massnahme nicht aendern.
ZAEHLER_START = (("detektionen", 0), ("fd", 0), ("ohne_pose", 0),
                 ("vorab_verworfen", 0), ("kandidaten", 0), ("m", 0), ("s", 0),
                 ("v", 0), ("unlesbar", False), ("frames_gelesen", 0),
                 ("frames_soll", None), ("unvollstaendig", False),
                 ("letzter_m", None), ("ohne_struktur", 0),
                 ("struktur_aus", None))

# Die reinen ZAEHLER daraus (int-Startwert; bool ist in Python ein int und wird
# hier ausdruecklich ausgenommen — unlesbar/unvollstaendig sind Zustands-, keine
# Zaehlfelder). Das ist die Menge, die eine Transport-Liste decken muss.
ZAEHLER_FELDER = tuple(k for k, v in ZAEHLER_START
                       if isinstance(v, int) and not isinstance(v, bool))


def zaehler_start():
    """Frischer Zaehler-Topf mit den Startwerten des Vertrags oben."""
    return dict(ZAEHLER_START)


def ernte_event(vid, eid, kamera, ts, fps_sample, schwellen, lauf_dir, emb=None,
                ist_fd=None, norm_mass=None, struktur_mass=None, quelle=None):
    """Frontal-Ernte fuer EIN Event (1 Event je Job — Live-Vorrang, Leitprinzip 5).

    Schreibt die Kandidaten (alle L-Passierer) in kandidaten/<eid>.jsonl — die Datei
    wird NEU geschrieben, ein Wieder-Ernten ist damit idempotent (kein Duplikat,
    keine Teilzeilen-Leiche). M-Crops (enges Gesicht = Lern-Material fuer E4b) nach
    crops/. -> Zaehler-Dict; 'unlesbar' True = 0 Frames lesbar; frames_gelesen/
    frames_soll/unvollstaendig immer dabei (Teil-Verlust ist KEIN stiller Erfolg).

    VORSCHRANKE (.341): Gesichter, die schon an det/kante/sharp scheitern, bekommen
    keine Landmarken, keine Pose, kein Embedding und KEINE Zeile — sie zaehlen als
    `vorab_verworfen`. Die Invariante heisst seitdem
    detektionen == fd + ohne_pose + vorab_verworfen + kandidaten. Weil solche
    Gesichter das Landmarken-Modell nie sehen, koennen sie per Konstruktion nicht
    als `ohne_pose` erscheinen; die Vorschranke hat also Vorrang vor jenem Topf.

    emb/ist_fd/norm_mass/struktur_mass sind fuer Tests injizierbar; im Betrieb
    kommen sie aus face_audit (Worker-Factory haelt den Embedder warm).

    STRUKTUR-TEST (.32x, User-Entscheid 22.08.): `struktur_mass` misst je
    M-/V-Kandidat, OB der Ausschnitt ueberhaupt Gesichtsstruktur zeigt
    (face_audit.StrukturMass, analysen/06_ist_das_ein_gesicht.md). Liegt der Wert
    unter `struktur_min`, verliert das Bild M und S und den Vorrats-Weg: es kostet
    dann keinen Crop, keine Norm-Inferenz und keinen Anker-Platz. Die
    Kandidaten-ZEILE wird trotzdem geschrieben (Zaehler-Invariante bleibt heil,
    der Wert steht als `struktur` drin) — der Verlust ist damit protokolliert,
    nicht still. Ohne Messgrundlage (kein Modell, Messung scheitert) wird NIE
    gefiltert.

    Z6 (konzept_frames.md v2 §4): die Frames kommen als ABNEHMER vom Verteiler
    (core.frames.lauf) statt aus einem eigenen FrameIter — dieselbe Frame-Quelle
    mit demselben fps_sample, also dieselbe Index-Menge und dieselben Bytes; der
    Clip ist derselbe, den worker.py schon seit Z2 EINMAL beschafft. Geerntet
    wird deshalb Zeile fuer Zeile wie bis 0.1.0.152 (§10-Leitplanke: der
    Verteiler aendert nur, WOHER die Frames kommen, nie WIE gerechnet wird).
    NICHT betroffen ist die KOERPER-Ernte (core/personlauf.fahren): sie laeuft in
    einem anderen Prozess ueber eine andere Event-Liste und behaelt nur ihren
    Clip-Bezug ueber core.frames — eine Zusammenfuehrung schliesst §1 aus."""
    fehlt = schwellen_pruefen(schwellen)
    if fehlt:
        raise ValueError("ernte-schwellen unvollstaendig: " + ", ".join(fehlt))
    import cv2                      # lazy: Modul bleibt fuer Dienst/QS billig
    from core import frames as verteiler   # Z6: Abnehmer statt eigenem FrameIter
    if emb is None:
        import face_audit
        emb = face_audit.Embedder()
    if ist_fd is None:
        from face_audit import ist_fehldetektion as ist_fd
    # Vorrats-Gate (Bauplan B2): aktiv nur mit VOLLEN vorrat-Schwellen im
    # (Manifest-)Regime UND funktionierender NormMass. Fehlt eine Haelfte,
    # laeuft die Ernte unveraendert wie vor dem Einbau — DEKLARIERT im
    # Zaehler (v_aus), nie still anders.
    v_aktiv = vorrat_schwellen_da(schwellen) and norm_mass is not None \
        and getattr(norm_mass, "ok", False)
    # STRUKTUR-Schwelle: BEWUSST per .get() und NICHT in SCHWELLEN_PFLICHT — die
    # 27 bestehenden Lernlauf-Manifeste tragen den Schluessel nicht, und die
    # Schwellen kommen beim Resume IMMER aus dem eingefrorenen Manifest
    # (verifyd._lernlauf_ernten). Ein Subskript-Zugriff wuerde jeden Alt-Lauf
    # toeten (Widerleger-Falle 5, dieselbe Klasse wie bei den Vorrats-Achsen).
    struktur_min = schwellen.get("struktur_min")
    struktur_aus = None
    if struktur_min is None:
        struktur_aus = "no threshold in run regime (old manifest)"
    elif struktur_mass is None:
        struktur_aus = "strukturmass: not provided"
    elif not getattr(struktur_mass, "ok", False):
        struktur_aus = ("strukturmass: "
                        + (getattr(struktur_mass, "grund", "") or "not ok"))[:120]
    if v_aktiv:
        # LAZY erst hier (Gate-Fund .306: das Pruef-Python der QS-Stufen hat
        # kein insightface — der Modul-Kopf von ernte_event muss ohne laufen).
        from insightface.utils import face_align
    v_aus = None
    if vorrat_schwellen_da(schwellen) and not v_aktiv:
        v_aus = ("normmass: " + getattr(norm_mass, "grund", "not provided"))[:120]
    os.makedirs(os.path.join(lauf_dir, "crops"), exist_ok=True)
    os.makedirs(os.path.join(lauf_dir, "kandidaten"), exist_ok=True)
    if v_aktiv:
        os.makedirs(os.path.join(lauf_dir, "vorrat"), exist_ok=True)
    event_aufraeumen(lauf_dir, eid)     # Reste eines frueheren (Teil-)Laufs weg
    z = zaehler_start()      # Schluessel/Startwerte: ZAEHLER_START (EINE Quelle)
    # .341 Vorschranke: nur eine Kapsel, die eine Auswahl entgegennimmt, kann die
    # teure Arbeit auf die Ueberlebenden beschraenken (face_audit.Embedder). Fremde
    # oder injizierte Kapseln ohne diese Tuer laufen unveraendert den Alt-Weg —
    # dann bleibt vorab_verworfen 0 und die Invariante stimmt genauso.
    holen = getattr(emb, "faces_mit_vorschranke", None)
    takt = {"frames": 0, "t": 0.0, "soll": None}   # Puls: Zaehlerstaende der Anzeige
    z["struktur_aus"] = struktur_aus
    if v_aus:
        z["v_aus"] = v_aus
    eid_safe = _eid_safe(eid)
    pfad = kandidaten_pfad(lauf_dir, eid)
    modell = getattr(emb, "modell", "?")
    clip = {"fps": None}    # aus LaufInfo — frueher direkt frames.fps
    ausfall = []            # s. _laut()
    with open(pfad, "w", encoding="utf-8") as out:

        def _laut(f):
            """Der Abnehmer ist WEICH deklariert (§3.2 hart=False: sein Ausfall
            wirft nur ihn ab und laesst andere Abnehmer zu Ende laufen) — die
            ERNTE bleibt davon unberuehrt laut: die Original-Ausnahme wird hier
            festgehalten und nach dem Lauf unveraendert weitergeworfen. Ohne das
            waere aus dem 'crop nicht schreibbar'-Abbruch ein still verschluckter
            Teil-Lauf geworden, und verifyd buchte ok=true auf halbe Buecher
            (genau die Fehlerklasse .75/L3, die event_aufraeumen aufraeumt)."""
            def gekapselt(*a):
                try:
                    return f(*a)
                except BaseException as ex:
                    ausfall.append(ex)
                    raise
            return gekapselt

        def clip_start(info):
            """EINMAL vor dem ersten Frame — Inhalt UND Reihenfolge unveraendert
            (sie bleiben im Abnehmer, der Verteiler kennt keine Modell-Parameter)."""
            clip["fps"] = info.fps
            # Erwartete Sample-Zahl, bevor das erste Bild faellt (LaufInfo.soll_samples,
            # §Z5) — der Nenner des Such-Balkens. Reines Durchreichen, keine Rechnung.
            takt["soll"] = getattr(info, "soll_samples", None)
            if hasattr(emb, "ar_det_size"):
                emb.set_det_size(emb.ar_det_size(info.breite, info.hoehe))
            # det_thresh NACH set_det_size neu binden (prepare resettet auf den Library-
            # Default — exakt die analyze.py:226-Lehre; ohne das erntet der Lauf eine
            # andere Detektionsmenge als der Urteilspfad).
            if hasattr(emb, "app"):
                emb.app.det_model.det_thresh = float(schwellen["det_thresh"])

        def ernten(i, frame):
            """Abnehmer 'ernte' (Z6): frueher der Rumpf von `for i, frame in frames`.
            Zeile fuer Zeile derselbe Code — nur die Schleifenzeile ist weg, weil
            jetzt der Verteiler faehrt, und frames.fps heisst clip['fps'].

            .341 VORSCHRANKE (bauplan_ernte_tempo.md §1): die drei billigen Achsen
            det/kante/sharp entstehen VOR Landmarken/Pose/Embedding. Wer weder den
            fd-freien Teil von M noch den von V bestehen kann, ist sicher weder
            bildwuerdig noch vorratstauglich — fuer ihn faellt die teure Arbeit weg,
            und er bekommt WIE fd/ohne_pose keine Zeile, sondern den Zaehler
            `vorab_verworfen`. Der uebrige Rumpf ist unveraendert und rechnet mit
            DENSELBEN gerundeten Werten wie zuvor (Vertrag V0.5)."""
            takt["frames"] += 1
            werte = {}          # je Gesicht EINMAL gemessen, Lebensdauer: dieses Frame

            def _messen(fc):
                """Die drei billigen Achsen + Box + Crop — WORTGLEICH die Rechnung,
                die bis .341 im Rumpf stand, nur vorgezogen.

                BELICHTUNG (bauplan_belichtung.md E1): die Graustufen-Umrechnung,
                die die Schaerfe ohnehin braucht, traegt die Luma gleich mit —
                EINE Umrechnung je Gesicht, die zweite Messung kostet praktisch
                nichts. Die crop.size-Leerwache der Schaerfe gilt damit auch fuer
                die Luma (entartete bbox: Leer-Crop wirft sonst mitten im Lauf)."""
                x1, y1, x2, y2 = [max(0, int(v)) for v in fc.bbox]
                crop = frame[y1:y2, x1:x2]
                grau = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.size else None
                w = (x1, y1, x2, y2, min(x2 - x1, y2 - y1),
                     round(float(fc.det_score), 3),
                     round(float(cv2.Laplacian(grau, cv2.CV_64F).var())
                           if grau is not None else 0.0, 1),
                     crop,
                     None if grau is None else int(round(float(grau.mean()))))
                werte[id(fc)] = w
                return w

            def _vorpruefen(fc):
                w = _messen(fc)
                return vorschranke(w[5], w[4], w[6], schwellen, v_aktiv)

            for fc in (holen(frame, _vorpruefen) if holen is not None
                       else emb.app.get(frame)):
                z["detektionen"] += 1
                if getattr(fc, "vorab_verworfen", False):
                    z["vorab_verworfen"] += 1   # nie still: eigener Topf der Invariante
                    continue
                pose_roh = getattr(fc, "pose", None)
                if pose_roh is None or len(pose_roh) < 3:
                    z["ohne_pose"] += 1     # ohne Winkel keine fd-/S-Bewertung — nie still
                    continue
                # RUNDEN VOR DEM GATE: Zeile und Entscheidung rechnen mit denselben
                # Werten (sonst 1/309 nicht reproduzierbar, Widerleger .75/L3).
                pose = [round(float(w), 1) for w in pose_roh]
                x1, y1, x2, y2, kante, det, sharp, crop, luma = (werte.get(id(fc))
                                                                 or _messen(fc))
                front = round(front_aus_pose(pose), 3)
                fd = bool(ist_fd(front, sharp, det, schwellen["fd_front_min"],
                                 schwellen["fd_sharp_min"], schwellen["fd_det_max"]))
                if fd:
                    z["fd"] += 1
                    continue
                m = gate_m(fd, det, kante, sharp, schwellen)
                s_flag = gate_s(fd, det, kante, sharp, pose, schwellen)
                # --- STRUKTUR-TEST (.32x): "ist da ueberhaupt ein Gesicht?"
                # Gerechnet nur fuer Bilder, die sonst einen Weg gehen wuerden
                # (M-Crop oder Vorrats-Vorpruefung) — nicht fuer jede Detektion.
                # V haengt NICHT unter M (gate_v_vor hat eigene, niedrigere
                # Latten), deshalb steht der Test VOR beiden Zweigen.
                struktur = None
                if (struktur_mass is not None and getattr(struktur_mass, "ok", False)
                        and (m or (v_aktiv and gate_v_vor(fd, det, kante, sharp,
                                                          schwellen)))):
                    struktur = struktur_mass.streuung(frame[y1:y2, x1:x2])
                    if (struktur is not None and struktur_min is not None
                            and struktur < struktur_min):
                        # Kein Crop, kein Vorrat, kein Anker — aber die Zeile
                        # bleibt (Invariante) und traegt den Messwert.
                        z["ohne_struktur"] += 1
                        m = s_flag = False
                        struktur_sperrt = True
                    else:
                        struktur_sperrt = False
                else:
                    struktur_sperrt = False
                t = i / clip["fps"]
                datei = None
                if m:                       # nur Bildwuerdiges kostet Platte (Konzept §P1)
                    kid = f"{eid_safe}~{i}~{z['kandidaten']}"
                    datei = os.path.join("crops", kid + ".jpg")
                    if not cv2.imwrite(os.path.join(lauf_dir, datei), crop.copy()):
                        # volle Platte u.ae.: LAUT statt Zeile-mit-totem-Pfad
                        raise OSError(f"crop nicht schreibbar: {datei}")
                    z["letzter_m"] = {"kamera": kamera, "t": round(t, 1)}
                # ---- Vorrats-Achsen (Bauplan B2): kps-Frontalitaet/Richtung sind
                # billig und stehen fuer JEDE Zeile im Protokoll; die teure
                # Norm-Inferenz bezahlen NUR gate_v_vor-Passierer (W2.8 — je
                # Frame sind das typisch 0-2, Einzel-Inferenz statt Batch haelt
                # die Schleife wortgleich). Gerundet VOR dem Gate (.75/L3).
                kps = getattr(fc, "kps", None)
                front_kps = front_aus_kps(kps)
                if front_kps is not None:
                    front_kps = round(front_kps, 4)
                richtung = None
                norm = None
                v_flag = False
                datei_v = None
                if v_aktiv and not struktur_sperrt:
                    richtung = richtung_aus_kps(kps, front_kps,
                                                schwellen["vorrat_front_profil"])
                    if gate_v_vor(fd, det, kante, sharp, schwellen):
                        aligned = face_align.norm_crop(frame, landmark=kps,
                                                       image_size=112)
                        norm = round(float(norm_mass.feature_norm([aligned])[0]), 4)
                        v_flag = gate_v_norm(norm, front_kps, schwellen)
                    if v_flag:
                        # v-Crop MIT Umfeld-Rand, an Framegrenzen geklemmt —
                        # ANZEIGE fuers Auge, nie Embedding-Quelle (A2-Befund:
                        # 28/40 enge Klein-Crops sind fuer embed() tot, der
                        # Rand heilt das nicht). Name traegt die eid
                        # (Kollisions-Fund W2.2), keine Tilde, DATEI_RE-konform.
                        f = float(schwellen["vorrat_rand_faktor"])
                        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                        hb, hh = (x2 - x1) * f / 2.0, (y2 - y1) * f / 2.0
                        H, W = frame.shape[:2]
                        a1, b1 = max(0, int(cx - hb)), max(0, int(cy - hh))
                        a2, b2 = min(W, int(cx + hb)), min(H, int(cy + hh))
                        datei_v = os.path.join(
                            "vorrat", f"v_{eid_safe}_{i}_{z['kandidaten']}.jpg")
                        rand_crop = frame[b1:b2, a1:a2]
                        if not (rand_crop.size and cv2.imwrite(
                                os.path.join(lauf_dir, datei_v), rand_crop.copy())):
                            raise OSError(f"vorrat-crop nicht schreibbar: {datei_v}")
                zeile = kandidat_zeile(eid, kamera, ts, t, (x1, y1, x2, y2), det,
                                       front, sharp, kante, pose,
                                       fc.normed_embedding, modell, m, s_flag, datei,
                                       norm=norm, front_kps=front_kps,
                                       richtung=richtung, v=v_flag, datei_v=datei_v,
                                       struktur=struktur, quelle=quelle, luma=luma)
                out.write(json.dumps(zeile, ensure_ascii=False) + "\n")
                out.flush()
                z["kandidaten"] += 1
                z["m"] += 1 if m else 0
                z["s"] += 1 if s_flag else 0
                z["v"] += 1 if v_flag else 0
            # PULS fuer die Anzeige (§4): hoechstens im PULS_TAKT_S-Takt, und nur
            # Zaehler, die oben ohnehin stehen. Im heissen Pfad bleibt dieser EINE
            # Zeitvergleich je Frame — die Anzeige loest keine Arbeit aus (Risiko 5).
            jetzt = time.monotonic()
            if jetzt - takt["t"] >= PULS_TAKT_S:
                takt["t"] = jetzt
                puls_schreiben(lauf_dir, {
                    "eid": eid, "ts": round(time.time(), 1),
                    "frames": takt["frames"], "frames_soll": takt["soll"],
                    "detektionen": z["detektionen"],
                    # Pose gerechnet = alles, was die Vorschranke passiert hat
                    "posen": z["detektionen"] - z["vorab_verworfen"],
                    "erkannt": z["kandidaten"]})

        # Z6: EIN Lauf, EIN Abnehmer — alle sechs Vertragsfelder stehen HIER und
        # keins im Verteiler (§3.2). `frames` traegt danach dieselben Wache-Namen
        # wie frueher der FrameIter (gelesen/soll/unvollstaendig), die Auswertung
        # unten bleibt Wort fuer Wort.
        try:
            frames = verteiler.lauf(vid, [verteiler.Abnehmer(
                name="ernte",
                fps_sample=fps_sample,  # derselbe Wert wie zuvor -> derselbe step
                zeitbezug="clip",       # t = i/fps, kein Wanduhr-Anker
                bedarf="stream",        # haelt nichts: der Crop geht sofort auf Platte
                hart=False,             # §3.2: die Ernte darf keinen fremden Abnehmer
                                        # mit sich reissen — laut bleibt sie via _laut()
                wache_politik="nachrechnen",
                zeitwache_s=None,       # BEWUSST keins: heute deckelt allein der
                                        # Worker-Job-Timeout des Aufrufers
                                        # (verifyd nachhol_analyse_timeout_s). Ein
                                        # neuer Deckel hier waere eine
                                        # Verhaltensaenderung, kein Umzug.
                start=_laut(clip_start), frame=_laut(ernten))])["ernte"]
        finally:
            # Der Puls gehoert dem LAUFENDEN Event. Bleibt er nach Ende (auch nach
            # einem Abbruch) liegen, behauptet ein Balken Arbeit, die niemand tut.
            puls_loeschen(lauf_dir)
        if ausfall:
            raise ausfall[0]            # unveraendert: Typ und Text wie bisher
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
                    for k in ("kandidaten", "m", "s", "v", "fd", "ohne_pose",
                              "detektionen", "ohne_struktur"):
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
                    # v-Crops gehoeren zur selben Buecher-gegen-Platte-Wache
                    # (Widerleger W1.8: ein stilles imwrite-Loch waere sonst
                    # genau die Fehlerklasse 'stiller Verlust').
                    if d.get("v") and d.get("datei_v"):
                        if not os.path.exists(os.path.join(lauf_dir, d["datei_v"])):
                            befunde.append(f"{eid}: vorrat-crop fehlt ({d['datei_v']})")
        if zeilen != soll:
            befunde.append(f"{eid}: {zeilen} zeilen != {soll} gebucht")
    return befunde
