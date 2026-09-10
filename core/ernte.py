"""core/ernte — Frontal-Ernte (E2 = Konzept §P1; Lern-Bauplan §2/E2).

EIGENER Ernte-Pfad, ausdruecklich AUCH fuer bekannte Personen (§1B: der Bestands-
Sammelpfad verwirft alles >= 0,42 zur naechsten bekannten Person — Anker-Aufwertung
waere damit unmoeglich). Er ersetzt den Bestand NICHT: anlernen._sammle_intern
bleibt byte-unangetastet (maschinell: qs-Stufe SAMMLE-CHARAKTERISIERUNG).

Gates seit 0.1.0.514 — EIN SIEB (Etappe 3, User-Entscheid 09.09.2026, Wortlaut:
„ein system!!!! nur unterschiedliche werte je normalmodus und ernte bzw.
lernmodus was das gleiche ist"):
  L (Ernte-Einlass)  = NOT Objekt-Signatur (ist_fehldetektion; die fd_*-Schwellen
                       SIND die Stellschrauben von L). 98,8 % echter Gesichter
                       passieren. UNVERAENDERT — die Echtheits-Frage beantwortet
                       keine der vier Achsen (Konzept §2 Stufe 2).
  M (bildwuerdig)    = L UND das SIEB (core.kamerakalib.sieb_ok): det,
                       KANTENLAENGE, Bildeindruck, Erkennbarkeit und Kopf-Pose
                       gegen die Werte des Katalog-Registers DIESER Kamera —
                       seit .518 genau diese FUENF (core.kamerakalib
                       .ERNTE_ACHSEN). Nur M-Kandidaten bekommen einen Crop.
                       Die Kante ist seit .515 zurueck im Sieb — .514 hatte
                       `m_kante_min` (60 px) abgeloest, weil es eine zweite,
                       nirgends mit dem Erkennungs-Weg vergleichbare Zahl war;
                       seit .515 ist sie eine Achse des Registers und traegt
                       den WERT des Erkennungs-Wegs (25 px).
  NORM (.518)        = die SECHSTE Achse siebt NICHT mehr hier. Sie braucht
                       eine eigene adaface-Session (NormMass, gemessene
                       Bauspitze 2700 MB) und machte damit jeden der K
                       parallelen Ernte-Plaetze potenziell zu einem
                       2,7-GB-Platz. Seit .518 misst sie EIN gebuendelter Job
                       NACH der Ernte (core/normlauf.py, User-Go 10.09.2026:
                       „Ernter startet -> Worker parallel mit den fuenf
                       leichten Achsen -> DANN die Normierung als EIN
                       gebuendelter Schritt -> dann die Abarbeitung").
                       Damit dieser Schritt auf DERSELBEN Messbasis rechnet
                       wie zuvor (Frame-Warp, nicht ein re-dekodierter Crop —
                       [[ersatzmessungen-sind-hypothesen]]), konserviert die
                       Ernte je Uebergabe-Kandidat den 112er-Warp als rohe
                       .npy-Kachel (`datei_w`).
  S (Anker-tauglich) = M UND |pitch|,|yaw|,|roll| <= s_winkel_max. S wird hier nur
                       AUSGEWERTET/gezaehlt — die Anker-BILDUNG ist E3.
  V (vorratstauglich)= M UND die Norm-LINIE (gate_v_norm). ACHTUNG, zwei Dinge
                       mit demselben Messwert und verschiedenen Fragen: die
                       Norm-LINIE beantwortet die NAEHE-Frage (Konzept §2 Stufe 3,
                       Profil-Zweig, Werte 22,0/21,5); die Norm-ACHSE des Siebs
                       ist der BODEN gegen zu schwaches Lernmaterial (Werkswert
                       core.guete.norm_werk()). Beide haengen am SELBEN Messwert,
                       und der faellt seit .518 im gebuendelten Norm-Schritt —
                       DORT wird deshalb auch die V-Linie entschieden
                       (core/normlauf.py). Die Ernte legt dafuer das
                       Vorrats-Bild (Rand-Ausschnitt) schon an und laesst
                       `v` offen; der Norm-Job setzt es und raeumt die Bilder
                       der Nicht-Passierer weg. Ohne gebuendelten Schritt
                       (Kalibrier-Auffueller, Bruecke) gibt es kein v — laut
                       deklariert ueber `v_aus`, nie still.

ABGELOEST mit .514 (sie standen bis .513 hier und siebten mit eigenen, nirgends
mit dem Erkennungs-Weg vergleichbaren Zahlen): m_det_min/m_kante_min/m_sharp_min,
s_det_min, vorrat_kante_min/vorrat_sharp_min und der eigene det_thresh-Schnitt.
`sharp` wird WEITER GEMESSEN und steht in jeder Zeile (Messkarte, Reihung,
Alt-Weg der Sichtung) — es siebt hier nicht mehr. `kante` ebenso, aber es siebt
seit .515 wieder: als Register-Achse mit dem Wert des Erkennungs-Wegs. Anlass ist der
Pruefbericht vom 09.09.: von den vier Reglern des Hauses wirkte im Ernte-Modus
KEIN einziger, waehrend eine nachgelagerte Latte 1120 von 1123 Bildern verworfen
haette — zwei Systeme, die sich widersprachen.

GERUNDET WIRD VOR DEM GATE (Widerleger .75/L3: sonst ist die Entscheidung aus der
persistierten Zeile nicht reproduzierbar — realer Fall det 0,5995 -> Zeile 0,6/m:false,
Nachrechnung m:true). Zeile und Entscheidung rechnen mit DENSELBEN Werten.

JEDER L-Passierer bekommt weiterhin SEINE ZEILE, auch wenn das Sieb ihn verwirft
(dieselbe Haltung wie beim Struktur-Test seit .32x): die Zaehler-Invariante
bleibt heil, die Messwerte samt Verwurfsgrund stehen im Protokoll, und eine
Latten-Aenderung ist am Bestand nachrechenbar statt blind. Gesiebt wird am
AUSGANG — hinter dem Messen, vor dem Speichern (Konzept E14).

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
import tempfile
import time

from core import messkarte as _mk     # nur Vertrag/Feldnamen, keine schweren Imports

# Pflicht-Schwellen, die der Aufrufer aus der Config liefern MUSS (kein Default hier —
# Allgemeinheits-Wache §2.4b: fehlt einer, ist das ein Verdrahtungsfehler und faellt laut).
#
# .514 GESCHRUMPFT: die Qualitaets-Achsen (det_thresh, m_det_min, m_kante_min,
# m_sharp_min, s_det_min) sind ins Katalog-Register gewandert und kommen jetzt als
# `sieb` herein (SIEB_PFLICHT unten). Uebrig bleiben hier die Fehldetektions-
# Signatur — sie beantwortet die ECHTHEITS-Frage, die keine der vier Achsen stellt —
# und das Winkelfenster des S-Flags. Alt-Manifeste tragen die abgeloesten Keys
# weiter; sie werden gelesen und nicht mehr gefragt, ein Resume laeuft also durch.
SCHWELLEN_PFLICHT = ("fd_front_min", "fd_sharp_min", "fd_det_max", "s_winkel_max")

# Die Sieb-Achsen, die der Aufrufer JE KAMERA aufloest und in den Job legt
# (core.kamerakalib.sieb_latten). Sie kommen ausdruecklich NICHT aus dem
# eingefrorenen Manifest, sondern LIVE aus der Kalibrier-Seite — Entscheid E10
# vom 09.09.: „kein Einfrieren mehr, wir haben jederzeit variable Startpunkte";
# nachvollziehbar bleibt es, weil je Lauf mitgeschrieben wird, was galt.
# .515: „n" (Feature-Norm) und „k" (Kantenlaenge in px) sind dazugekommen. Sie
# stehen in der PFLICHT wie die anderen — ein Job ohne eine Achse soll laut
# sterben statt still mit einer Werks-Annahme zu laufen; dass der Werkswert der
# Norm 0 (= aus) ist, aendert daran nichts: 0 ist eine ENTSCHEIDUNG, ein
# fehlendes Feld ist ein Verdrahtungsfehler. Reihenfolge = SIEB_ACHSEN.
#
# .518: die PFLICHT bleibt bei ALLEN SECHS, obwohl im Ernte-Job nur fuenf
# sieben. Das ist Absicht und kein Rest: der Latten-Satz des Jobs ist die EINE
# Zeile, aus der auch der gebuendelte Norm-Schritt seine Latte liest (der
# Dienst legt sie je Kamera dorthin), und er steht im Rueckgabe-Topf
# (z["sieb"]) als Protokoll dessen, was fuer dieses Ereignis GALT. Welche der
# sechs im Ernte-Job wirklich sieben, sagt `ernte_sieb` unten.
SIEB_PFLICHT = ("det", "k", "e", "t", "p", "n")

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


def sieb_pruefen(sieb):
    """-> Liste fehlender Sieb-Achsen (leer = vollstaendig). Dieselbe Haltung
    wie schwellen_pruefen: ein fehlender Wert ist ein VERDRAHTUNGSFEHLER und
    faellt laut. Kein Default hier — ein stillschweigend eingesetzter Werks-Boden
    saehe aus wie eine Entscheidung und waere keine."""
    s = sieb or {}
    return [k for k in SIEB_PFLICHT if s.get(k) is None]


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


def ernte_sieb(sieb):
    """Die Achsen, die IM ERNTE-JOB sieben -> Latten-Dict ohne die
    Nachmess-Achsen (.518).

    EINE Quelle: `core.kamerakalib.ERNTE_ACHSEN` (abgeleitet aus SIEB_ACHSEN
    minus NACHMESS_ACHSEN). Der Job traegt weiter ALLE sechs Latten
    (SIEB_PFLICHT) — der gebuendelte Norm-Schritt liest seine aus derselben
    Zeile —, gesiebt wird hier aber nur mit diesen fuenf.

    Warum eine eigene Funktion und keine Auslassung an der Aufrufstelle: die
    Aufzaehlung „welche Achse siebt wo" darf genau EINMAL im Code stehen. Eine
    sechste Achse, die still wieder im Ernte-Sieb landet, ist der Rueckfall in
    genau den 2,7-GB-Platz, den .518 aufloest — die s11-Probe haelt diese
    Menge deshalb gegen kamerakalib.ERNTE_ACHSEN."""
    from core import kamerakalib as _kk
    s = sieb or {}
    return {a: s.get(a) for a in _kk.ERNTE_ACHSEN}


def sieb_urteil(sieb, det, e, t, p, n=None, k=None):
    """DAS Sieb dieses Laufs -> (ok, grund). Duennschale um DIE eine Mechanik
    (core.kamerakalib.sieb_ok), damit in der Ernte kein zweiter Vergleich mit
    denselben Zahlen entsteht und der Erkennungs-Weg spaeter an dieselbe
    Funktion andocken kann. Lazy importiert wie alles Schwere hier — der
    Modulkopf muss ohne Config-/Store-Kette laufen."""
    from core import kamerakalib as _kk
    return _kk.sieb_ok(sieb, det=det, e=e, t=t, p=p, n=n, k=k)


def gate_m(fd, sieb, det, e, t, p, n=None, k=None):
    """M = bildwuerdig: L (keine Objekt-Signatur) UND das Sieb. -> (ok, grund).
    grund ist None bei ok, "fd" bei der Fehldetektions-Signatur, sonst der
    Achsen-Grund aus kamerakalib.SIEB_GRUENDE."""
    if not gate_l(fd):
        return False, "fd"
    return sieb_urteil(sieb, det, e, t, p, n, k)


def gate_s(m_ok, pose, s):
    """S nur AUSWERTEN (E3 bildet die Anker): M UND das Winkelfenster.
    pose = [pitch, yaw, roll] mit Vorzeichen — als BELIEBIGE Zahlen-Sequenz
    (fc.pose ist ein numpy-Array; ein isinstance-list-Guard liess im Echtlauf
    .74 ALLE 38 S-Faelle zu False kippen).

    .514: die eigene Detektionslatte `s_det_min` ist raus — sie war eine
    ZWEITE Zahl auf derselben Achse, die das Sieb schon fuehrt. Das
    Winkelfenster bleibt: es misst die insightface-Kopfwinkel und beantwortet
    damit eine andere Frage als der RTMPose-Kopfscore der p-Achse
    ([[ersatzmessungen-sind-hypothesen]] — zwei Skalen, nicht vermischen)."""
    if not m_ok:
        return False
    try:
        winkel = [float(w) for w in pose]
    except (TypeError, ValueError):
        return False
    if len(winkel) != 3:
        return False
    return all(abs(w) <= s["s_winkel_max"] for w in winkel)


def vorschranke(det, sieb):
    """Die billige VORPRUEFUNG der Ernte (bauplan_ernte_tempo.md §1): wer schon
    an der det-Achse scheitert, braucht weder Landmarken noch Pose noch
    Embedding — er kann per Konstruktion kein M werden, denn det ist ein Glied
    der Sieb-Konjunktion.

    .514: sie prueft nur noch die det-Achse — und das bleibt auch mit der
    .515-Kanten-Achse so, obwohl deren Messwert hier schon vorlaege. Grund ist
    der Entscheid von .514: gesiebt wird am AUSGANG, damit JEDE Zeile ihre
    Messwerte und ihren Verwurfsgrund behaelt. Wer die Kante hier vorzoege,
    liesse kleine Gesichter wieder ohne eine einzige Zahl herausfallen — und
    genau daran war die alte Kanten-Latte nicht eichbar. Die zwei Guete-Masse
    brauchen ohnehin den 112er-Warp, also Landmarken —
    vor ihnen laesst sich nichts sparen. EHRLICHE FOLGE, beziffert im
    Bau-Bericht: weil der Aufrufer den Detektor auf DIESELBE Zahl bindet
    (clip_start unten), passiert hier praktisch jede Detektion, und der
    Vorschranken-Ersparnis von rund der Haelfte aller Detektionen entfaellt.
    Die Funktion bleibt trotzdem stehen — sie ist die Stelle, an der eine
    strengere Kamera-Latte als der Detektor-Schnitt wieder greift."""
    from core import guete as _guete
    return _guete.achse_ok((sieb or {}).get("det"), det)


def gate_v_norm(norm, front_kps, s):
    """Vorrats-Norm-Achse: Profil-Zweig unter der kps-Frontalitaets-Grenze
    (Profile tragen bei gleicher Identitaetsstaerke systematisch ~1 Punkt
    weniger Norm — Pose-Schichtung 20.08.).

    .522 (Widerleger-Befund P-1, MITTEL-HOCH): ein Regime OHNE Vorrats-Achsen
    ist seit .521 ein REGULAERER Betriebszustand — der Pass-Knopf faehrt einen
    fluechtigen Mini-Ernte-Lauf und popt die Vorrats-Schluessel aus seinem
    Regime, weil dieser Lauf die Vorrats-Linie gar nicht entscheidet. Trifft so
    ein Regime auf eine ALTE Kandidaten-Zeile (Bruecken-Ordner aus <= .516: die
    tragen noch `datei_v` und eine gemessene `norm`), stand hier bis .521 ein
    blanker `KeyError: 'vorrat_front_profil'` — mitten im gebuendelten
    Norm-Schritt, also starb der Worker-Job, der Dienst wiederholte ihn fuenfmal
    und die Norm-Achse blieb fuer das ganze Ereignis offen. Im Log sah das aus
    wie ein Worker-Problem.
    Fehlt auch nur eine der Zahlen, gibt es deshalb KEINE Vorrats-Frage
    (dieselbe Haltung wie `vorrat_schwellen_da`: ein halbes Gate waere
    schlimmer als keins) -> False. Wer die Vorrats-Linie WIRKLICH entscheiden
    will, bringt ein vollstaendiges Regime mit."""
    if norm is None:
        return False
    if not vorrat_schwellen_da(s):
        return False
    grenze = (s["vorrat_norm_min_profil"]
              if (front_kps is not None and front_kps < s["vorrat_front_profil"])
              else s["vorrat_norm_min"])
    return norm >= grenze


def kandidat_zeile(eid, kamera, ts, t, bbox, det, front, sharp, kante, pose,
                   emb_vec, modell, m, s_flag, datei,
                   norm=None, front_kps=None, richtung=None, v=False, datei_v=None,
                   struktur=None, quelle=None, luma=None,
                   fiqa_t=None, empf=None,
                   mk_fiqa_t=None, mk_empf=None, mk_quelle=None, mk_pose=None,
                   sieb_grund=None, datei_w=None):
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
            # Bildguete (.377, Kalibrier-Funktion): additiv am Ende, Alt-Leser
            # bleiben gueltig. None = nicht gemessen (kein m-Crop, Modell fehlt
            # im Alt-Image, oder Messfehler — Zaehler guete_fehler).
            "fiqa_t": None if fiqa_t is None else round(float(fiqa_t), 4),
            "empf": None if empf is None else round(float(empf), 4),
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
            "luma": luma,
            # MESSKARTE (.513, Etappe 1 „Messkern"): die Kandidaten-Zeile IST
            # die Quelle der Karte — hier entstehen die Werte, alle anderen
            # Stationen reichen sie nur weiter (core/messkarte.uebernehmen).
            # Die BESTAND-Achsen der Karte stehen bereits oben; hier kommen
            # die zwei Guete-Masse unter ihren EIGENEN Namen dazu, plus die
            # Herkunft. Warum eigene Namen und nicht fiqa_t/empf: jene zwei
            # Felder sind kein Datum, sondern ein SCHALTER — ihr blosses
            # Vorhandensein entscheidet in core.benennung.guete_weg_aktiv und
            # in anlernen.bild_stufe, WELCHE Latten-Generation urteilt, und
            # drei Uebernahme-Stellen fragen mit genau diesen Namen ihre
            # katalog_ok-Latte. Die Ernte misst seit .513 auch fuer
            # v-Kandidaten (B2); haetten die Werte denselben Namen, aenderte
            # sich damit sofort das Urteil an vier Stellen, ohne dass eine
            # Latte angefasst waere. Etappe 1 darf das nicht (Bauplan:
            # „keine Latte, kein Sieb, kein Urteil aendern") — Etappe 3 haengt
            # die Verbraucher bewusst um. Ausfuehrlich: core/messkarte.py.
            "mk_fiqa_t": None if mk_fiqa_t is None else round(float(mk_fiqa_t), 4),
            "mk_empf": None if mk_empf is None else round(float(mk_empf), 4),
            "mk_quelle": mk_quelle, "mk_modell": modell,
            # .514 (Etappe 3): der RTMPose-Kopfscore — die vierte Achse des
            # Siebs, am Ernte-Material vorher gar nicht vorhanden. None heisst
            # „nicht gemessen": Latte aus (dann kostet sie niemanden etwas),
            # Modell fehlt, oder der Fund fiel schon an einer billigeren Achse.
            "mk_pose": None if mk_pose is None else round(float(mk_pose), 4),
            # .514: WARUM diese Zeile kein M wurde — '<achse>_unter' bzw.
            # '<achse>_unmessbar' (core.kamerakalib.SIEB_GRUENDE), 'fd' fuer die
            # Objekt-Signatur, None wenn sie durchkam. Er steht in der Zeile und
            # nicht nur im Zaehler, damit eine Latten-Aenderung am BESTAND
            # nachrechenbar ist statt nur an einer Summe.
            "sieb_grund": sieb_grund,
            # .518 WARP-KONSERVIERUNG: der 112er-Warp DIESES Funds als rohe
            # .npy-Kachel (~37 KB), relativ zum Lauf-Verzeichnis. Er ist die
            # MESSBASIS des gebuendelten Norm-Schritts — dieselben Pixel, die
            # bis .517 sofort gemessen wurden, nur spaeter. Roh und nicht als
            # JPEG, weil eine Kompression die Zahl verschoebe und die Messung
            # damit eine Ersatzmessung waere ([[ersatzmessungen-sind-
            # hypothesen]]). Am DICT-ENDE wie luma/mk_*: ein Byte-Diff zweier
            # Laeufe soll eine Ergaenzung zeigen, keine Umsortierung. None =
            # kein Warp (kein Nachmess-Schritt auf diesem Weg, oder der Fund
            # hatte keine Landmarken). Der Norm-Job LOESCHT die Kachel nach
            # der Messung und setzt das Feld wieder auf None — ein gesetztes
            # `datei_w` heisst also immer: die Kachel liegt wirklich da
            # (Buecher-gegen-Platte, bestand_pruefen).
            "datei_w": datei_w}


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
    if z.get("v", 0) > z.get("m", 0):
        # .514: V haengt jetzt UNTER M — beide stellen dieselbe Qualitaets-Frage
        # (das eine Sieb), getrennt werden sie nur noch durch die Norm-Linie.
        # Bis .513 hatte V eigene, niedrigere Achsen (Kante 40 < m_kante 60) und
        # die Wache konnte nur gegen L pruefen.
        return f"v-schachtelung verletzt: V {z.get('v')} > M {z.get('m')}"
    if z.get("gesiebt", 0) and (z.get("m", 0) + z.get("gesiebt", 0)
                                != z.get("kandidaten", 0)):
        # .514: jede geschriebene Zeile ist entweder M oder gesiebt.
        return (f"sieb-invariante verletzt: M {z.get('m')} + gesiebt "
                f"{z.get('gesiebt')} != kandidaten {z.get('kandidaten')}")
    return None


def _eid_safe(eid):
    return str(eid).replace("/", "_")


def kandidaten_pfad(lauf_dir, eid):
    return os.path.join(lauf_dir, "kandidaten", _eid_safe(eid) + ".jsonl")


# .518: die dritte Ablage neben crops/ und vorrat/ — die konservierten
# 112er-Warps des gebuendelten Norm-Schritts. EIGENER Ordner statt einer Datei
# je Event, weil Schreiber (Ernte, je Fund) und Raeumer (Norm-Job, je Event;
# event_aufraeumen, je Wieder-Ernte) dieselbe Namensregel brauchen: der
# Dateiname ist die Crop-Kennung `<eid>~<frame>~<n>` — derselbe Schluessel,
# unter dem der Crop liegt.
WARP_ORDNER = "warp"
WARP_ENDUNG = ".npy"


def warp_rel(kid):
    """Der lauf-relative Pfad der Warp-Kachel EINER Crop-Kennung."""
    return os.path.join(WARP_ORDNER, kid + WARP_ENDUNG)


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
    # .518: warp/<eid>~* als DRITTE Ablage — ohne diesen Glob bliebe nach einem
    # Wieder-Ernten die Warp-Kachel des alten Durchlaufs liegen, und der
    # Norm-Job maesse eine Kachel, deren Zeile es nicht mehr gibt (dieselbe
    # Waisen-Klasse wie W1.9, nur teurer: 37 KB je Stueck).
    for muster in (os.path.join(lauf_dir, "crops", es + "~*"),
                   os.path.join(lauf_dir, "vorrat", "v_" + es + "_*"),
                   os.path.join(lauf_dir, WARP_ORDNER, es + "~*")):
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
    # S2-Fix 01.09. (199x FileNotFoundError beim Feldtester): ein FESTER
    # tmp-Name kollidiert, wenn zwei Aufrufer denselben lauf_dir beschreiben
    # (Bulk-Benennung: mehrere Personen desselben Durchgangs) — der zweite
    # os.replace fand die tmp des ersten nicht mehr. mkstemp macht den
    # Zwischennamen einzigartig; os.replace bleibt atomar.
    fd, tmp = tempfile.mkstemp(prefix="manifest.", suffix=".tmp", dir=lauf_dir)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
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
                 ("struktur_aus", None),
                 # .514: wie viele Kandidaten-Zeilen das Sieb verwarf (= kein
                 # M). Als ZAEHLER und nicht nur in der Bilanz, weil die feste
                 # Transport-Liste seit .505 ZAEHLER_FELDER liest — ein neuer
                 # Topf reist damit von selbst bis in fertig.jsonl. Er ist eine
                 # TEILMENGE von `kandidaten` (kandidaten = m + gesiebt) und
                 # beruehrt die Summen-Invariante nicht.
                 ("gesiebt", 0))

# Die reinen ZAEHLER daraus (int-Startwert; bool ist in Python ein int und wird
# hier ausdruecklich ausgenommen — unlesbar/unvollstaendig sind Zustands-, keine
# Zaehlfelder). Das ist die Menge, die eine Transport-Liste decken muss.
ZAEHLER_FELDER = tuple(k for k, v in ZAEHLER_START
                       if isinstance(v, int) and not isinstance(v, bool))


def zaehler_start():
    """Frischer Zaehler-Topf mit den Startwerten des Vertrags oben."""
    return dict(ZAEHLER_START)


def align112(frame, kps):
    """DER eine 112er-Warp des Hauses (insightface norm_crop) — Vorrats-Norm UND
    Bildguete messen damit am SELBEN Ausschnitt (core/guete.py: 'Input: das
    ALIGNED 112er-Crop, exakt das der Feature-Norm — kein zweites Alignment').

    Seit .380 public und mit einem zweiten Verbraucher: der Unbekannt-Pool misst
    seinen Zulauf mit denselben Massen wie der Lernlauf (anlernen._zulauf_messen).
    Ein eigener Zuschnitt dort haette eine eigene Skala — die Regler der
    Kalibrier-Seite bedeuteten im Pool dann etwas anderes als in der Flaeche.

    LAZY importiert wie im ganzen Haus (anlernen.py, face_audit.py): der
    Modul-Kopf von ernte_event muss ohne insightface laufen (Gate-Fund .306,
    das Pruef-Python der QS-Stufen hat es nicht). Als EIN Griff statt zweier
    Bindungen, weil die zwei Verbraucher an verschiedenen Gates haengen — die
    Norm am Vorrats-Gate, die Guete an M; eine Bindung im Vorrats-Zweig war
    genau der NameError-Befund vom 30.08."""
    from insightface.utils import face_align
    return face_align.norm_crop(frame, landmark=kps, image_size=112)


def pose_kopf(frame, bbox):
    """Der Kopf-Score der Pose-Wache fuer EIN Gesicht -> float oder None.

    EXAKT dieselbe Messung wie im Erkennungs-Weg (analyze.py: rtmpose auf der
    aus der Gesichtsbox geschaetzten PERSONENREGION des Vollbilds, Maximum
    ueber die Kopf-Gelenke) und ueber dieselbe Funktion
    (core.livewache.pose_wache/person_region). Das ist der Kern des
    Ein-Sieb-Zugs: die Pose-Latte des Registers bedeutet auf beiden Wegen
    dasselbe, weil beide Wege dieselbe Zahl messen. Eine eigene, „bessere"
    Ernte-Messung (etwa auf dem Gesichts-Crop statt der Personenregion) waere
    eine ZWEITE Skala und damit genau das, was dieser Zug abschafft —
    Konsistenz vor Perfektion (User-Auflage 09.09.).

    None heisst „nicht messbar": kein Modell, nicht ladbar, oder die Messung
    warf. Was daraus folgt, entscheidet der Aufrufer — je FUND fail-closed
    (das Sieb verwirft ihn), je MODELL fail-open (der Aufrufer nimmt die Latte
    laut heraus). Die Unterscheidung trifft `core.livewache.pose_verfuegbar`."""
    try:
        from core.livewache import (pose_wache as _pw, person_region as _pr)
        w = _pw()
        if w is None:
            return None
        from pose_wache import KOPF_IDX as _KIDX
        h, b = frame.shape[:2]
        _pts, sc = w.skelett(frame, bbox=_pr(bbox, b, h))
        return float(max(sc[j] for j in _KIDX))
    except Exception:                                          # noqa: BLE001
        return None


def kalib_vorrat_speisen(lauf_dir, kamera, best, kalib, log=print):
    """EIN Bild dieses Events in den Kalibrier-Vorrat SEINER Kamera legen.

    WARUM HIER (User-Entscheid 31.08., Zentral-Umbau der Kalibrierung): der
    Vorrat soll NICHT nur aus dem Live-Waechter kommen. Wer keine Live-Wache
    betreibt, haette sonst eine Kalibrierseite ohne ein einziges Bild — der
    Kaltstart, den der Entscheid ausdruecklich loesen soll. Die Ernte ist die
    Stelle des Event-/Szenario-Wegs, an der Crops MIT Kamera-Zuordnung und mit
    den beiden Guete-Massen bereits vorliegen; ein zweiter Messweg entsteht
    dadurch nicht.

    DROSSEL wie auf dem Live-Weg: EIN Bild je Event (das det-staerkste
    M-Crop), nie je Frame. Ring, Deckel und Loeschweg sind unveraendert die
    des Live-Vorrats (core.livewache.kalib_schreiben ist der EINE Schreibweg,
    dort greift auch der Deckel).

    Das Bild ist der gespeicherte M-Crop (enger Ausschnitt), waehrend der
    Live-Weg mit Rand schneidet. Das ist bewusst so: die Guete-ZAHLEN der
    Zeile gehoeren zu genau diesem Ausschnitt, und eine zweite Messung an
    einem zweiten Zuschnitt haette eine andere Skala (dieselbe Auflage wie
    beim Pool-Zulauf).

    Ein Fehlschlag ist NIE ein Ernte-Fehler: der Vorrat ist Beiwerk, das Event
    ist geerntet. -> True, wenn ein Bild abgelegt wurde."""
    if not kalib or not best or not kamera:
        return False
    deckel = int((kalib or {}).get("deckel") or 0)
    if not deckel:
        return False                      # Vorrats-Sammlung aus (live_kalib_max 0)
    try:
        import cv2
        from core import livewache as _lw   # lazy: der Modulkopf bleibt billig
        bild = cv2.imread(os.path.join(lauf_dir, str(best["datei"])))
        if bild is None:
            return False
        return bool(_lw.kalib_schreiben(
            {"data_dir": kalib.get("data_dir")}, kamera, bild,
            {"det": best.get("det"), "e": best.get("e"), "t": best.get("t"),
             "p": best.get("p")},
            deckel=deckel, log=log,
            # S5: der Ernte-Einlass (Formel L) hat ist_fehldetektion bereits
            # gesiebt — ein Pose-Skelett-Urteil gibt es auf diesem Weg nicht;
            # das mensch_ok=True ist die deklarierte Grenze dieses Zulaufs.
            mensch_ok=True))
    except Exception as e:                                    # noqa: BLE001
        log(f"ernte: Kalibrier-Vorrat nicht beschickt "
            f"({type(e).__name__}: {e})")
        return False


def ernte_event(vid, eid, kamera, ts, fps_sample, schwellen, lauf_dir, emb=None,
                ist_fd=None, struktur_mass=None, quelle=None,
                kalib=None, sieb=None, nachmess=False):
    """Frontal-Ernte fuer EIN Event (1 Event je Job — Live-Vorrang, Leitprinzip 5).

    Schreibt die Kandidaten (alle L-Passierer) in kandidaten/<eid>.jsonl — die Datei
    wird NEU geschrieben, ein Wieder-Ernten ist damit idempotent (kein Duplikat,
    keine Teilzeilen-Leiche). M-Crops (enges Gesicht = Lern-Material fuer E4b) nach
    crops/. -> Zaehler-Dict; 'unlesbar' True = 0 Frames lesbar; frames_gelesen/
    frames_soll/unvollstaendig immer dabei (Teil-Verlust ist KEIN stiller Erfolg).

    `sieb` (.514, PFLICHT; seit .515 FUENF Achsen) = die aufgeloesten Latten
    DIESER Kamera aus dem
    Katalog-Register, vom DIENST hereingereicht (core.kamerakalib.sieb_latten;
    der Worker greift nie selbst in die Config). Sie kommen aus dem JOB und
    NICHT aus dem eingefrorenen Manifest — dieselbe Regel wie beim
    Kalibrier-Vorrat: die Latte ist eine laufende Entscheidung des Betreibers,
    keine Lauf-Bedingung (Entscheid E10 vom 09.09.). Fehlt eine Achse, ist das
    ein Verdrahtungsfehler und faellt laut, wie bei den Schwellen.

    VORSCHRANKE (.341, seit .514 det-only): Gesichter unter der det-Achse bekommen
    keine Landmarken, keine Pose, kein Embedding und KEINE Zeile — sie zaehlen als
    `vorab_verworfen`. Die Invariante heisst seitdem
    detektionen == fd + ohne_pose + vorab_verworfen + kandidaten. Weil solche
    Gesichter das Landmarken-Modell nie sehen, koennen sie per Konstruktion nicht
    als `ohne_pose` erscheinen; die Vorschranke hat also Vorrang vor jenem Topf.

    emb/ist_fd/struktur_mass sind fuer Tests injizierbar; im Betrieb kommen sie
    aus face_audit (Worker-Factory haelt den Embedder warm). `norm_mass` ist
    mit .518 ERSATZLOS GESTRICHEN — der Ernte-Job haelt keine NormMass mehr
    (Bauspitze 2700 MB je Platz), die Feature-Norm misst der gebuendelte
    Norm-Schritt danach (core/normlauf.py).

    `nachmess` (.518) = „auf diesem Weg folgt der gebuendelte Norm-Schritt".
    Nur der LERNLAUF setzt es. Es entscheidet zweierlei, und beides waere ohne
    den Folgeschritt reine Platten-Verschwendung: ob je M-Kandidat der
    112er-Warp konserviert wird (`datei_w`), und ob das Vorrats-Bild schon
    angelegt wird, damit der Norm-Job die V-Linie entscheiden kann. Ohne
    `nachmess` laeuft die Ernte mit fuenf Achsen und OHNE v — beides
    deklariert (`sieb_aus`/`v_aus`), nie still.

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
    Clip-Bezug ueber core.frames — eine Zusammenfuehrung schliesst §1 aus.

    kalib={"data_dir","deckel"} (Zentral-Umbau 31.08.): speist den
    Kalibrier-Vorrat DIESER Kamera mit EINEM Bild je Event
    (kalib_vorrat_speisen). None = aus, dann laeuft die Ernte wie zuvor.
    Der Wert kommt aus dem Job und NICHT aus dem eingefrorenen Manifest: der
    Ring-Deckel ist eine laufende Config-Entscheidung, keine Lauf-Bedingung."""
    fehlt = schwellen_pruefen(schwellen)
    if fehlt:
        raise ValueError("ernte-schwellen unvollstaendig: " + ", ".join(fehlt))
    fehlt_s = sieb_pruefen(sieb)
    if fehlt_s:
        raise ValueError("ernte-sieb unvollstaendig: " + ", ".join(fehlt_s))
    import cv2                      # lazy: Modul bleibt fuer Dienst/QS billig
    from core import frames as verteiler   # Z6: Abnehmer statt eigenem FrameIter
    if emb is None:
        import face_audit
        emb = face_audit.Embedder()
    if ist_fd is None:
        from face_audit import ist_fehldetektion as ist_fd
    import numpy as _np                # .518: rohe Warp-Kachel, lazy wie cv2
    # Vorrats-Gate (Bauplan B2): aktiv nur mit VOLLEN vorrat-Schwellen im
    # (Manifest-)Regime. .518: die zweite Haelfte der Bedingung war „und eine
    # funktionierende NormMass" — die haelt dieser Prozess nicht mehr. An ihre
    # Stelle tritt `nachmess`: das Vorrats-Bild wird HIER angelegt, die
    # V-Entscheidung faellt im gebuendelten Norm-Schritt. Fehlt der Schritt,
    # laeuft die Ernte ohne v — DEKLARIERT im Zaehler (v_aus), nie still.
    v_aktiv = vorrat_schwellen_da(schwellen) and bool(nachmess)
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
    # BILDGUETE (.377): der Griff steht AUSSERHALB des Vorrats-Zweigs, denn
    # gemessen wird je BILDWUERDIGEM Kandidaten (unten), nicht je Vorratsbild.
    # Als Bindung im v_aktiv-Zweig starb die Ernte mit NameError, sobald das
    # Vorrats-Gate aus war (QS-Befund 30.08.) — und das ist kein Randfall: jedes
    # Alt-Manifest ohne die vorrat_*-Keys, jede NormMass mit ok=False (etwa ein
    # anderes Erkennungs-Modell als adaface) und jeder Container ohne Budget fuer
    # den NormMass-Bau laufen so. Das Modul misst mit onnxruntime/numpy und
    # braucht kein insightface; den 112er-Warp holt es sich ueber align112 (public, seit .380 auch vom Pool-Zulauf genutzt).
    # EINMAL gefragt statt je Kandidat: die Antwort gilt fuer den ganzen Lauf
    # und traegt unten die Aussetzungs-Meldung.
    from core import guete as _guete
    guete_da = _guete.verfuegbar()
    # SIEB-LATTEN dieses Laufs, mit dem MODELL-Gegenstueck (.514, CLAUDE.md
    # „Messbarkeit vor Stimme": fail-closed je FUND, fail-open je MODELL).
    # Ohne diesen Block schaltete eine fehlende ONNX-Datei die ganze Ernte
    # stumm: jeder Fund traege None auf einer aktiven Achse und fiele — das
    # ist genau der Blocker BL-1 der Gegenpruefung W1, und die Invariante
    # verlangt, dass der VERBRAUCHER seine Latte dann laut auf 0 setzt.
    # Wortgleich zu analyze.py (URT_G_AUS / _pose_sieb_aus), nur hier.
    sieb_w = {k: sieb.get(k) for k in SIEB_PFLICHT}
    sieb_aus = {}
    # .518: der Latten-Satz des Jobs traegt weiter ALLE sechs Achsen (Protokoll
    # + Quelle des Norm-Schritts). Gesiebt wird HIER mit `sieb_e` — den fuenf
    # leichten Achsen aus der EINEN Quelle (kamerakalib.ERNTE_ACHSEN). Der
    # Aufbau steht VOR dem Modell-Gegenstueck, damit dessen Abschaltungen
    # (e/t, p) auf beiden Dicts wirken: `sieb_e` ist eine SICHT auf `sieb_w`
    # und wird unten nach jeder Abschaltung neu gezogen.
    sieb_nach = {}
    if not guete_da and ((sieb_w["e"] or 0) > 0 or (sieb_w["t"] or 0) > 0):
        sieb_aus["e_t"] = ("quality models missing ("
                           + os.path.basename(_guete.PFAD_T) + ", "
                           + os.path.basename(_guete.PFAD_E) + ")")
        sieb_w["e"] = sieb_w["t"] = 0.0
    if (sieb_w["p"] or 0) > 0:
        # .516 R3c (Widerleger-Befund B2, Datenverlust-Klasse): hier stand bis
        # .515 NUR die Datei-Probe `pose_verfuegbar()`. Die sagt „Modell da",
        # nicht „Session baut" — ihr eigener Docstring nennt diese Grenze. Ist
        # die Datei vorhanden und der Aufbau scheitert erst beim Laden, gab
        # `ernte.pose_kopf` fuer JEDES Bild None zurueck (es schluckt den
        # Ladefehler), die Achse blieb aktiv, und der Lauf verlor sein GESAMTES
        # Material dieses Events als `p_unmessbar` — ohne die zugesagte
        # „SIEVE AXIS OFF"-Zeile. Erst ab dem ZWEITEN Event griff
        # `pose_verfuegbar()` ueber den gemerkten Fehler. Ein Event je
        # Worker-Leben, still.
        # Deshalb wird das Modell hier EINMAL wirklich angefasst, genau wie es
        # `analyze.py` tut (Zeile 621-628: `_w = _pw(); if _w is None:
        # _pose_sieb_aus(...)`). Kosten: keine — bei aktiver Achse laedt das
        # Modell ohnehin beim ersten Gesicht, und `pose_wache()` ist gemerkt.
        _pose_grund = None
        try:
            from core.livewache import pose_verfuegbar as _pose_da_f
            from core.livewache import pose_wache as _pose_w_f
            if not bool(_pose_da_f()):
                _pose_grund = "pose model not available"
            elif _pose_w_f() is None:
                _pose_grund = "pose model present but not loadable"
        except Exception as _e_pose:                           # noqa: BLE001
            _pose_grund = f"pose model unusable ({type(_e_pose).__name__})"
        if _pose_grund:
            sieb_aus["p"] = _pose_grund
            sieb_w["p"] = 0.0
    # .518 NORM-ACHSE: sie siebt hier NICHT mehr. Bis .517 stand an dieser
    # Stelle ihr Modell-Gegenstueck („keine NormMass -> Achse laut auf 0"). Das
    # Gegenstueck ist nicht verschwunden, es ist UMGEZOGEN: der gebuendelte
    # Norm-Schritt haelt die eine Session und nimmt die Achse dort laut heraus,
    # wenn sie nicht baut (core/normlauf.py, derselbe Blocker BL-1).
    #
    # Was hier bleibt, ist die EHRLICHKEIT: eine aktive Norm-Latte auf einem
    # Ernte-Weg OHNE gebuendelten Schritt (Kalibrier-Auffueller, Bruecke) wirkt
    # nirgends. Das wird gesagt, nicht verschwiegen — sonst waere aus dem Umbau
    # ein stiller Verlust geworden.
    if (sieb_w["n"] or 0) > 0:
        sieb_nach["n"] = ("measured after the harvest by the bundled "
                          "feature-norm step" if nachmess else
                          "NOT measured on this harvest path (no bundled "
                          "feature-norm step follows it)")
    # Kostet die Pose-Achse ueberhaupt etwas? Nur bei aktiver Latte wird der
    # RTMPose-Lauf je Kandidat faellig — die teure Achse zahlt niemand, der sie
    # nicht eingeschaltet hat. (Die Norm-Achse kostet hier seit .518 gar
    # nichts mehr; ihre Rechnung steht im gebuendelten Schritt.)
    pose_noetig = (sieb_w["p"] or 0) > 0
    v_aus = None
    if vorrat_schwellen_da(schwellen) and not v_aktiv:
        v_aus = ("no bundled feature-norm step on this harvest path — "
                 "the stock line cannot be decided here")[:120]
    os.makedirs(os.path.join(lauf_dir, "crops"), exist_ok=True)
    os.makedirs(os.path.join(lauf_dir, "kandidaten"), exist_ok=True)
    if v_aktiv:
        os.makedirs(os.path.join(lauf_dir, "vorrat"), exist_ok=True)
    if nachmess:
        os.makedirs(os.path.join(lauf_dir, WARP_ORDNER), exist_ok=True)
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
    # E10: an jedem Ergebnis steht, WAS galt — die wirkenden Werte und, wenn
    # eine Achse wegen eines fehlenden Modells herausgenommen wurde, warum.
    # Beides als Dict im Rueckgabe-Topf (kein neuer Zaehler-Schluessel).
    z["sieb"] = dict(sieb_w)
    if sieb_aus:
        z["sieb_aus"] = sieb_aus
    if sieb_nach:
        # .518: WO eine Achse gemessen wird, wenn nicht hier. Eigener Topf und
        # nicht `sieb_aus`: „aus" und „spaeter" sind verschiedene Aussagen, und
        # nur eine davon ist ein Verlust.
        z["sieb_nach"] = sieb_nach
    # .518: DIE fuenf Achsen, mit denen dieser Job wirklich siebt. Erst HIER
    # gezogen, also NACH allen Modell-Abschaltungen oben — sonst siebte eine
    # laut herausgenommene Achse in der Sicht weiter.
    sieb_e = ernte_sieb(sieb_w)
    eid_safe = _eid_safe(eid)
    pfad = kandidaten_pfad(lauf_dir, eid)
    modell = getattr(emb, "modell", "?")
    clip = {"fps": None}    # aus LaufInfo — frueher direkt frames.fps
    ausfall = []            # s. _laut()
    # Bestes M-Crop des Events fuer den Kalibrier-Vorrat (Zentral-Umbau 31.08.).
    # Topf statt Variable, weil der Abnehmer `ernten` eine Closure ist.
    kalib_topf = {"best": None}
    # B4: die Mess-Bilanz DIESES Events. Sie reist im Rueckgabe-Topf mit (kein
    # neuer ZAEHLER — sie ist ein Dict, ZAEHLER_FELDER bleibt unberuehrt und
    # die festen Transport-Listen decken unveraendert).
    bilanz = _mk.bilanz_start("ernte")
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
            # .514: gebunden wird die det-ACHSE DES SIEBS, nicht mehr der eigene
            # `det_thresh` des Ernte-Regimes. Damit sieht die Ernte genau die
            # Detektionsmenge, ueber die sie danach urteilt — vorher schnitt der
            # Detektor bei 0,5 und das Gate bei 0,6, und der Bestand hatte in der
            # Spanne 0,40-0,60 kein einziges Bild (Pruefbericht 09.09.: „wer die
            # det-Achse eichen will, braucht Material aus einem Lauf mit
            # niedrigerem ernte_m_det_min"). Genau derselbe Griff wie im
            # Erkennungs-Weg, wo verifyd den Kamera-Regler als --det-thresh
            # durchreicht.
            if hasattr(emb, "app"):
                emb.app.det_model.det_thresh = float(sieb_w["det"])

        def ernten(i, frame):
            """Abnehmer 'ernte' (Z6): frueher der Rumpf von `for i, frame in frames`.
            Zeile fuer Zeile derselbe Code — nur die Schleifenzeile ist weg, weil
            jetzt der Verteiler faehrt, und frames.fps heisst clip['fps'].

            .341 VORSCHRANKE (bauplan_ernte_tempo.md §1, seit .514 det-only): die
            billigen Achsen entstehen VOR Landmarken/Pose/Embedding. Wer die
            det-Achse des Siebs nicht besteht, kann per Konstruktion kein M werden
            — fuer ihn faellt die teure Arbeit weg, und er bekommt WIE fd/ohne_pose
            keine Zeile, sondern den Zaehler `vorab_verworfen`.

            .514 REIHENFOLGE DES URTEILS (die Kostenordnung, User-Entscheid
            03.09. fuer den Erkennungs-Weg, hier wortgleich): det (schon da)
            -> fd -> die zwei Guete-Masse (~17 ms) -> die Pose (RTMPose, die
            teuerste Achse; nur fuer Kandidaten, die die drei billigen bestanden
            haben, und nur bei aktiver Pose-Latte). Gerechnet wird mit DENSELBEN
            gerundeten Werten wie in der Zeile (Vertrag V0.5)."""
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
                return vorschranke(w[5], sieb_e)

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
                # ================= DAS EINE SIEB (.514) ====================
                # Reihenfolge = Kostenordnung (SIEB_ACHSEN): det liegt schon
                # vor, fd ist gerechnet, jetzt die zwei Guete-Masse, und erst
                # fuer deren Passierer die teure Pose. Gemessen wird fuer JEDEN
                # L-Passierer — bis .513 nur fuer M/V, und genau daran scheiterte
                # die Kalibrierbarkeit: ein Bild, das das alte Gate nicht nahm,
                # hatte auch keine Zahl, mit der man das Gate haette pruefen
                # koennen.
                kps = getattr(fc, "kps", None)
                front_kps = front_aus_kps(kps)
                if front_kps is not None:
                    front_kps = round(front_kps, 4)
                aligned = None                    # der EINE 112er-Warp je Fund
                mk_fiqa_t_w = mk_empf_w = None    # Messkarte: die volle Messung
                mk_quelle_w = None
                mk_grund = None                   # B4: warum NICHT gemessen
                if not guete_da:
                    mk_grund = _mk.GRUND_MODELL_FEHLT
                elif kps is None:
                    mk_grund = _mk.GRUND_KPS_FEHLT
                else:
                    mk_quelle_w = _mk.QUELLE_M
                    try:
                        aligned = align112(frame, kps)
                        mk_fiqa_t_w = _guete.fiqa_t(aligned)
                        mk_empf_w = _guete.empfinden(crop)
                    except Exception:
                        z["guete_fehler"] = z.get("guete_fehler", 0) + 1
                        mk_fiqa_t_w = mk_empf_w = None
                        mk_quelle_w = None
                        mk_grund = _mk.GRUND_MESSFEHLER
                # POSE: die teuerste Achse. Nur bei aktiver Latte, und nur fuer
                # Kandidaten, die die drei billigen Achsen schon bestanden haben
                # (Reihenfolge-Entscheid des Users 03.09., dort fuer den
                # Erkennungs-Weg — hier wortgleich). Wer schon an der
                # Erkennbarkeit faellt, kostet keinen RTMPose-Lauf; sein
                # Verwurfsgrund bleibt die Achse, an der er wirklich scheiterte.
                p_w = None
                if pose_noetig and sieb_urteil(dict(sieb_e, p=0.0), det,
                                               mk_empf_w, mk_fiqa_t_w, None,
                                               k=kante)[0]:
                    p_w = pose_kopf(frame, fc.bbox)
                # .518: HIER stand bis .517 die Norm-Inferenz — die letzte und
                # teuerste Achse, eine eigene adaface-Session je Ernte-Platz.
                # Sie ist ersatzlos weg; gemessen wird nach der Ernte, EINMAL,
                # aus dem konservierten Warp (core/normlauf.py). Das Sieb
                # urteilt deshalb auf den fuenf leichten Achsen.
                m_ok, sieb_grund = gate_m(fd, sieb_e, det, mk_empf_w,
                                          mk_fiqa_t_w, p_w, k=kante)
                _mk.sieb_zaehlen(bilanz, m_ok, sieb_grund)
                m = m_ok
                # --- STRUKTUR-TEST (.32x): "ist da ueberhaupt ein Gesicht?"
                # Gerechnet nur fuer Bilder, die sonst einen Weg gehen wuerden —
                # seit .514 ist das genau die Sieb-Menge (V haengt jetzt unter M,
                # weil beide dieselbe Qualitaets-Frage stellen; nur die
                # Norm-Linie trennt sie noch).
                struktur = None
                struktur_sperrt = False
                if (struktur_mass is not None and getattr(struktur_mass, "ok", False)
                        and m):
                    struktur = struktur_mass.streuung(frame[y1:y2, x1:x2])
                    if (struktur is not None and struktur_min is not None
                            and struktur < struktur_min):
                        # Kein Crop, kein Vorrat, kein Anker — aber die Zeile
                        # bleibt (Invariante) und traegt den Messwert.
                        z["ohne_struktur"] += 1
                        m = False
                        struktur_sperrt = True
                s_flag = gate_s(m, pose, schwellen)
                if not m:
                    # ZWEI Zahlen, zwei Fragen — mit Absicht verschieden:
                    # `gesiebt` zaehlt das ERGEBNIS (diese Zeile bekommt kein
                    # Bild), die Sieb-Bilanz oben zaehlt das SIEB-URTEIL. Ein
                    # struktur-gesperrter Fund hat das Sieb bestanden und faellt
                    # trotzdem — er steht deshalb in `gesiebt` UND in
                    # `ohne_struktur`, aber in der Bilanz unter „durch". Wer die
                    # Latten justieren will, liest die Bilanz; wer wissen will,
                    # was auf der Platte landet, liest die Zaehler.
                    z["gesiebt"] += 1
                t = i / clip["fps"]
                datei = None
                datei_w = None
                if m:                       # nur Bildwuerdiges kostet Platte (Konzept §P1)
                    kid = f"{eid_safe}~{i}~{z['kandidaten']}"
                    datei = os.path.join("crops", kid + ".jpg")
                    if not cv2.imwrite(os.path.join(lauf_dir, datei), crop.copy()):
                        # volle Platte u.ae.: LAUT statt Zeile-mit-totem-Pfad
                        raise OSError(f"crop nicht schreibbar: {datei}")
                    z["letzter_m"] = {"kamera": kamera, "t": round(t, 1)}
                    # .518 WARP-KONSERVIERUNG: die MESSBASIS des gebuendelten
                    # Norm-Schritts, roh (np.save) und nicht als JPEG — eine
                    # Kompression verschoebe die Zahl, und dann maesse der
                    # Schritt etwas anderes als bis .517 gemessen wurde
                    # ([[ersatzmessungen-sind-hypothesen]]). Groessenordnung
                    # 112*112*3 = 36,75 KB je Kachel plus 128 B npy-Kopf.
                    # `aligned` ist genau der Warp, an dem oben schon die
                    # Erkennbarkeit gemessen wurde — kein zweites Alignment.
                    # Fehlt er (keine Landmarken, oder die Guete-Messung warf),
                    # bekommt dieser Fund KEINE Kachel: der Norm-Schritt
                    # beurteilt ihn dann fail-closed als `n_unmessbar` — genau
                    # das Urteil, das bis .517 an dieser Stelle fiel.
                    if nachmess:
                        if aligned is None:
                            z["warp_fehlt"] = z.get("warp_fehlt", 0) + 1
                        else:
                            datei_w = warp_rel(kid)
                            try:
                                _np.save(os.path.join(lauf_dir, datei_w), aligned)
                            except OSError as _e_w:
                                # Dieselbe Haltung wie beim Crop: volle Platte
                                # ist LAUT, nicht eine Zeile mit totem Pfad.
                                raise OSError(f"warp nicht schreibbar: "
                                              f"{datei_w} ({_e_w})")
                # ---- Vorrats-Achsen (Bauplan B2): kps-Frontalitaet/Richtung sind
                # billig und stehen fuer JEDE Zeile im Protokoll; die teure
                # Norm-Inferenz bezahlen NUR Sieb-Passierer (W2.8 — je Frame sind
                # das typisch 0-2, Einzel-Inferenz statt Batch haelt die Schleife
                # wortgleich). Gerundet VOR dem Gate (.75/L3).
                # .514: die Vorpruefung heisst jetzt `m` — die eigenen
                # Vorrats-Latten kante 40 / sharp 600 sind abgeloest (sharp
                # trennt nachweislich nicht: AUC 0,480, Konzept §1.8). Was
                # bleibt, ist die NORM-Linie: sie beantwortet die Naehe-Frage,
                # nicht die Qualitaets-Frage, und gehoert deshalb nicht ins Sieb.
                richtung = None
                # .518: die Norm steht hier NOCH NICHT in der Zeile — sie faellt
                # im gebuendelten Schritt und wird von dort nachgetragen. `None`
                # heisst also bis dahin ehrlich „noch nicht gemessen", nicht
                # „nicht messbar".
                norm = None
                # .518 V-LINIE: die Entscheidung braucht die Norm und faellt
                # deshalb ebenfalls im Norm-Schritt. Was HIER passiert, ist die
                # Vorbereitung: das Vorrats-Bild wird fuer JEDEN M-Kandidaten
                # angelegt, weil es nur solange geschnitten werden kann, wie der
                # FRAME lebt. Der Norm-Schritt setzt danach `v` und raeumt die
                # Bilder der Nicht-Passierer weg (core/normlauf.py). Der Preis
                # ist Platte auf Zeit, der Gewinn ist, dass die Ernte-Plaetze
                # keine 2,7-GB-Session mehr halten.
                v_flag = False
                datei_v = None
                if v_aktiv and not struktur_sperrt:
                    richtung = richtung_aus_kps(kps, front_kps,
                                                schwellen["vorrat_front_profil"])
                    if m and kps is not None:
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
                        # `v` bleibt hier BEWUSST False: das Bild liegt, das
                        # Urteil fehlt. Der Norm-Schritt ist die einzige Stelle,
                        # die es faellen kann — und `core.vorrat` nimmt nur
                        # Zeilen mit v==True, ein unentschiedener Zwischenstand
                        # kann also nirgends als Angebot durchgehen.
                # ---- LEGACY-Paar `fiqa_t`/`empf`: gefuellt fuer genau das
                # Material, das den Weg nimmt (bis .513 „nur m", seit .514 „nur
                # was das Sieb passiert hat" — dieselbe Menge, neu bestimmt).
                #
                # Es ist kein zweites Datum, sondern ein SCHALTER
                # (core/messkarte.py): sein blosses Vorhandensein entscheidet in
                # core.benennung.guete_weg_aktiv und in anlernen.bild_stufe,
                # WELCHE Latten-Generation ueber eine Zeile urteilt, und die drei
                # Katalog-Uebernahmen fragen mit genau diesen Namen ihre
                # katalog_ok-Latte. Die Gruppen-Flaeche, der Pool-Zulauf und die
                # Uebernahme-Stellen haengen also weiter daran — sie sind
                # ausdruecklich nicht Teil dieses Zugs. Das ANKER-SIEB dagegen
                # liest seit .514 die Messkarte (`mk_*`, B3), damit Ernte und
                # Anker-Phase dieselben Zahlen gegen dieselben Latten halten.
                fiqa_t_w = empf_w = None
                if m:
                    fiqa_t_w, empf_w = mk_fiqa_t_w, mk_empf_w
                # KALIBRIER-VORRAT (Zentral-Umbau 31.08.): das det-staerkste
                # M-Crop dieses Events merken — EIN Bild je Event, nicht je
                # Frame (dieselbe Drossel wie der Live-Weg, der je Auftritt
                # eines ablegt). Gemerkt wird nur der Pfad, geschrieben wird
                # EINMAL nach dem Lauf: waehrend der Schleife haelt der
                # Vergleich nichts als drei Zahlen.
                # (Topf statt Variable: `ernten` ist eine Closure, eine
                # Zuweisung machte den Namen lokal — dieselbe Bauform wie
                # `clip` und `takt` darueber.)
                if m and datei is not None and (
                        kalib_topf["best"] is None
                        or det > kalib_topf["best"]["det"]):
                    # POSE-KOPF fuer den Kalibrier-Vorrat (03.09.,
                    # Widerleger-Befund 3 am Regler-Bau: p-lose Ernte-Bilder
                    # machten den Pose-Regler an genau den Stoerer-Karten
                    # blind). .514: derselbe Griff wie das Sieb (pose_kopf) —
                    # und wenn das Sieb schon gemessen hat, wird der Wert
                    # WIEDERVERWENDET statt ein zweites Mal gerechnet. Steht
                    # die Pose-Latte auf 0, misst hier weiterhin EIN Bild je
                    # Event, damit die Kalibrier-Seite ihren Regler behaelt.
                    kalib_topf["best"] = {
                        "datei": datei, "det": det, "e": empf_w, "t": fiqa_t_w,
                        "p": p_w if p_w is not None else pose_kopf(frame, fc.bbox)}
                zeile = kandidat_zeile(eid, kamera, ts, t, (x1, y1, x2, y2), det,
                                       front, sharp, kante, pose,
                                       fc.normed_embedding, modell, m, s_flag, datei,
                                       norm=norm, front_kps=front_kps,
                                       richtung=richtung, v=v_flag, datei_v=datei_v,
                                       struktur=struktur, quelle=quelle, luma=luma,
                                       fiqa_t=fiqa_t_w, empf=empf_w,
                                       # MESSKARTE (.513/.514): die VOLLE
                                       # Messung — seit .514 fuer JEDEN
                                       # L-Passierer, vor dem Sieb und damit
                                       # auch fuer das, was faellt. `mk_quelle`
                                       # sagt, an welchem Ausschnitt sie
                                       # entstand, `sieb_grund`, woran es lag.
                                       mk_fiqa_t=mk_fiqa_t_w, mk_empf=mk_empf_w,
                                       mk_quelle=mk_quelle_w, mk_pose=p_w,
                                       sieb_grund=sieb_grund,
                                       # .518: die Messbasis des gebuendelten
                                       # Norm-Schritts (None = keine Kachel).
                                       datei_w=datei_w)
                # BILANZ (.513, Etappe 1 B4 — das Messbarkeit-vor-Stimme-
                # Gegenstueck fuer den LERNPFAD, Inventur §I-7): je Fund EINE
                # Buchung. Ohne sie gibt es keine Zahl dafuer, wie viel des
                # Materials die Guete-Latte ueberhaupt beurteilen KONNTE — und
                # eine spaetere strengere Latte waere blind, weil niemand sieht,
                # ob sie greift oder nur schlaeft.
                _mk.bilanz_zaehlen(bilanz,
                                   mk_fiqa_t_w is not None and mk_empf_w is not None,
                                   mk_grund)
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
    # GUETE-AUSSETZUNG LAUT (.377, QS-Befund 30.08.): der Zaehler guete_fehler
    # lebt nur im Rueckgabe-Topf, den keine Transport-Liste traegt, und ein
    # fehlendes Modell sagte bisher GAR NICHTS — der Lauf meldete ok, alle Zeilen
    # trugen fiqa_t=None, und die Kalibrier-Seite blieb ohne jede Erklaerung
    # leer. Also EINE Zeile je Event-Ernte ins Job-Log (nie je Kandidat), und
    # nur wenn es etwas auszusetzen gab: dieselbe Haltung wie v_aus/
    # struktur_aus — eine Aussetzung wird deklariert, nie verschwiegen.
    # BEWUSST kein neuer Zaehler-Topf: ZAEHLER_START bleibt unberuehrt, damit
    # die festen Transport-Listen (Regel SK3) unveraendert decken.
    # B4: die Bilanz reist mit (der Dienst zieht die Lauf-Summe daraus und
    # schreibt EINE Zeile je Lauf — nicht je Event, sonst waere sie Rauschen).
    z["mkbilanz"] = bilanz
    if z.get("guete_fehler") or (not guete_da and bilanz["gesehen"]):
        grund = (f"{z['guete_fehler']} measurement error(s)"
                 if z.get("guete_fehler") else
                 f"models missing ({os.path.basename(_guete.PFAD_T)}, "
                 f"{os.path.basename(_guete.PFAD_E)})")
        print(f"ernte {eid}: no image-quality scores for "
              f"{bilanz['unmessbar']} of {bilanz['gesehen']} finding(s) — {grund}; "
              f"those lines carry no quality scores and the calibration page "
              f"cannot use them", flush=True)
    # .514: eine Achse, die wegen eines fehlenden MODELLS herausgenommen wurde,
    # wird nie verschwiegen (fail-open je Modell, aber laut). Dieselbe Haltung
    # wie v_aus/struktur_aus und wortgleich zum Erkennungs-Weg
    # (analyze.py „URTEILS-VORFILTER AUS" / „POSE-STIMM-SIEB AUS").
    for _achse, _grund in (sieb_aus or {}).items():
        print(f"ernte {eid}: SIEVE AXIS OFF ({_achse}) — {_grund}; "
              f"this axis lets everything through for this run", flush=True)
    # .518: eine Achse, die NACH der Ernte gemessen wird, ist keine
    # abgeschaltete Achse — aber eine, fuer die es auf DIESEM Weg gar keinen
    # Nachmess-Schritt gibt, wirkt nirgends. Nur diesen zweiten Fall meldet der
    # Ernte-Job; die regulaere Verschiebung bilanziert der Norm-Job selbst
    # (EINE Zeile je Lauf statt einer je Ereignis).
    if not nachmess:
        for _achse, _grund in (sieb_nach or {}).items():
            print(f"ernte {eid}: SIEVE AXIS NOT APPLIED ({_achse}) — {_grund}; "
                  f"this axis lets everything through on this path", flush=True)
    # KALIBRIER-VORRAT: nach dem Lauf, EIN Bild. BEWUSST kein neuer Zaehler im
    # Rueckgabe-Topf — ZAEHLER_START und die festen Transport-Listen (Regel
    # SK3) bleiben unberuehrt; wer wissen will, wie viele Bilder ankamen,
    # zaehlt den Ring (der On-demand-Fueller tut genau das).
    kalib_vorrat_speisen(lauf_dir, kamera, kalib_topf["best"], kalib)
    return z


def fertig_lesen(lauf_dir):
    """Resume-Grundlage: bereits geerntete Events (fertig.jsonl) -> (eids, zaehler_summe).
    Kaputte Zeilen werden gezaehlt UND ihre eids fehlen im Set -> die Events werden
    neu geerntet (idempotent dank Datei-je-Event), nie still uebersprungen."""
    p = os.path.join(lauf_dir, "fertig.jsonl")
    eids, summe, kaputt = set(), {}, 0
    bilanzen = []                       # B4: Mess-Bilanzen der Events
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
                              "detektionen", "ohne_struktur", "gesiebt"):
                        summe[k] = summe.get(k, 0) + int(d.get(k) or 0)
                    for k in ("unlesbar", "ohne_gesicht", "fehler", "unvollstaendig"):
                        summe[k] = summe.get(k, 0) + (1 if d.get(k) else 0)
                    if d.get("mkbilanz"):
                        bilanzen.append(d["mkbilanz"])
                except Exception:
                    kaputt += 1
    summe["kaputt"] = kaputt
    # B4: die Lauf-Bilanz aus den Event-Bilanzen. Sie ueberlebt damit ein
    # Resume (fertig.jsonl ist die Buchung) und braucht keinen zweiten Speicher.
    summe["mkbilanz"] = _mk.bilanz_summe(bilanzen)
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
                    # .518 WARP-KONSERVIERUNGS-VERTRAG: ein gesetztes `datei_w`
                    # behauptet eine liegende Messbasis. Fehlt die Kachel,
                    # verliert der gebuendelte Norm-Schritt genau diesen Fund
                    # (er faellt dann fail-closed als `n_unmessbar`) — das ist
                    # ein stiller Verlust, wenn es niemand nachrechnet. Der
                    # Norm-Job LOESCHT die Kachel erst, NACHDEM er das Feld
                    # geleert hat; ein gesetztes Feld ohne Datei ist deshalb
                    # immer ein Befund, nie ein normaler Zwischenstand.
                    if d.get("datei_w"):
                        if not os.path.exists(os.path.join(lauf_dir, d["datei_w"])):
                            befunde.append(f"{eid}: warp fehlt ({d['datei_w']})")
        if zeilen != soll:
            befunde.append(f"{eid}: {zeilen} zeilen != {soll} gebucht")
    return befunde
