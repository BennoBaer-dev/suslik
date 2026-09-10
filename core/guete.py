"""Bildguete-Messung fuer die Kalibrier-Funktion (.377, User-Entscheid 30.08.).

Zwei Masse, beide EIN Skalar je Bild (Herkunft/Lizenz: models/LIZENZEN_GUETE.md):
  fiqa_t     eDifFIQA(T) — Erkennbarkeit aus Sicht eines Gesichts-Erkenners;
             bestraft auch Verdeckung (Messtag 30.08.: die zwei vom User
             beanstandeten Verdeckungs-Faelle lagen bei T weit unten, waehrend
             das Empfinden sie mochte). Input: das ALIGNED 112er-Crop, exakt
             das der Feature-Norm (norm_crop) — kein zweites Alignment.
  empfinden  Efficient-FIQA (EdgeNeXt-XXS) — Bild-Eindruck fuers Auge
             (Schaerfe-/Helligkeitsempfinden). Input: der ROHE Crop, 352er-
             Resize mit ImageNet-Normierung (Vorgabe des Modells).

Dieses Modul MISST nur. Die Schwellen leben in der Config (seit .514/.516
ausschliesslich als Achsen der zwei Register, core/kamerakalib.py) und werden
vom jeweiligen Verbraucher injiziert — Zahlen kommen nie von hier
(Haus-Regel, Muster norm_latte/REF_LATTE).

Messbasis der Modellwahl: Vierervergleich 30.08. an 714 Bildern eines
Feld-Lernlaufs (labor-Auswertung fiqa_vergleich.json): Laplacian-sharp
korreliert r=-0,06 mit dem FIQA-Urteil (als Qualitaetsmass widerlegt);
alle Kandidaten-Modelle sahen die vom alten sharp-Kriterium Aussortierten
im Median BESSER als die Uebernommenen. FROQ wurde gemessen und verworfen
(praktisch identisch mit der vorhandenen Feature-Norm, +0,05 Spearman).

Backend bewusst CPU: zusammen ~1,7+1,2 Mio Parameter, gemessen ~7 ms (T)
je Bild bei 4 Threads — laeuft nur im Lernlauf, je Kandidat einmal, und
konkurriert so nie mit der Erkennung um iGPU/NPU."""
import os
import threading

import numpy as np

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PFAD_T = os.path.join(HIER, "models", "ediffiqa_tiny_jun2024.onnx")
PFAD_E = os.path.join(HIER, "models", "fiqa_edgenext_xxs.onnx")
_IN_MEAN = np.array([0.485, 0.456, 0.406], np.float32)   # ImageNet (Efficient-FIQA-Vorgabe)
_IN_STD = np.array([0.229, 0.224, 0.225], np.float32)

# ENTFERNT MIT .516 (Alt-Latten-Abloesung, User 10.09.2026, Sechs-Achsen-
# Verfassung „keine Altlasten mitschleppen"): die Konstante `STARTWERTE`
# {"empfinden": 0.200, "t": 0.400} — die am Feldmaterial geeichten Werks-
# Startwerte der GLOBALEN Guete-Latte (Messtag 30.08., 714 Bilder).
#
# Ihre Geschichte in zwei Saetzen: bis .513 siebte sie den Lernlauf; .514 nahm
# ihr das ab (Register „Face catalog", core/kamerakalib.sieb_latten/sieb_ok),
# liess sie aber als load_config-Default der zwei Config-Werte
# `guete_empfinden_min`/`guete_t_min` stehen — und die versorgten weiter
# Gruppen-Flaeche, Sichtung, Reihung, Empfehlung, Pool-Zulauf und den Alt-Weg
# des Anker-Siebs. Der .514-Widerleger hat daraus den RISS gemessen: von 1385
# Bildern, die Ernte und Anker-Sieb durchliessen, verwarf diese Latte 1382, und
# beide Anker-Gruppen des Abnahmelaufs hatten 0 von 31 ankreuzbaren Bildern
# (gegen 15 von 15 auf .513). Die Doppel-Siebung war nicht aufgeloest, sondern
# eine Station weiter gerueckt.
#
# .516 haengt ALLE diese Verbraucher auf das Register um. Damit hat die
# Konstante keinen Leser mehr — und eine Zahl ohne Leser, die aussieht wie eine
# geltende Latte, ist genau die Altlast, die die Verfassung verbietet. Die
# GEMESSENEN Werte sind nicht verloren: sie stehen in analysen/todos_29_08.md
# Punkt 9 und im .514-Widerleger-Bericht.
# ---- KATALOG-Latte (Aufnahme in den Referenz-Katalog) ---------------------
# EIGENE Quelle seit .511 (User-Entscheid 08.09.2026 ~17:0x: "0,125 passt,
# bau es so"). Bis .510 lieh sich die Katalog-Latte die globalen Lernlauf-
# Startwerte (0,200/0,400, mit .516 entfernt) — die NAH-Eichung des Lernlaufs.
# Am Feldtester-Spiegel liess
# diese Latte 34 von 200 Kalibrier-Samples durch und wuergte damit genau die
# Automatik-Wege ab, die den Katalog fuellen sollen (Lernlauf-Uebernahme,
# Bestands-Vorschlag, Vorrat, Enrollment — core.kamerakalib.UEBERNAHME_STELLEN).
# ROLLEN-ZUSCHNITT, aus dem die neue Zahl folgt (User 08.09.): AUFNEHMEN ist
# liberal, gesiebt wird DANACH vom Bestands-Pruefer (core/refurteil.py, eigene
# Latte PRUEF_STARTWERTE). Eine strenge Aufnahme-Latte kostet Material, das
# der Pruefer spaeter ohnehin einzeln beurteilt — deshalb runter, nicht rauf.
# Die zwei Achsen bekommen bewusst DIESELBE Zahl: die Trennschaerfe steckt im
# Pruefer, hier steht nur noch der Boden gegen totes Material.
KATALOG_STARTWERTE = {"empfinden": 0.125, "t": 0.125}
# ANZEIGE_STARTWERTE (Vorgaben-Knopf der Kalibrierseite) ist seit 03.09. eine
# ABLEITUNG der Werks-Boeden und steht deshalb unten HINTER STIMM_DEFAULT —
# die eigenstaendigen 0,175/0,200 vom 31.08. sind mit dem Sync-Entscheid
# "Werkswert = Boden = Regler-Minimum" ueberholt (User 03.09.: "bei Default
# setzt er noch die alten Werte, da muesst ihr die neuen minimalen setzen").

# URTEILS-VORFILTER (User-Entscheide 01.09., nach den Tester-Fehlbenennungen:
# "es sollte doch immer durch die Kalibrierung vorgefiltert werden"): JEDE
# Namens-Stimme — Live-Watcher UND Szenario/Worker — muss die Erkennen-Latten
# der Kamera bestehen, bevor sie zaehlt.
# HOEHE (User-Entscheide 01.09. abends, verbindlich, an den Bildern der
# Drei-Clip-Belege entschieden): ERKENNBARKEIT "nie unter 0,2 — weder der
# User noch sonst was geht darunter", Default unkalibriert 0,225;
# BILDEINDRUCK Default 0,175, Boden 0,10 (User-Nachtrag: kalibrierte
# Kameras duerfen bis 0,10 runter) — der Default ist
# der Wert, der die dunklen Anschnitt-Gesichter aus dem Voting haelt,
# die die Erkennbarkeits-Latte zu Recht passieren laesst). Messbelege:
# die 0,10-Erstfassung liess 213 Muell-Stimmen durch (Kabel t 0,30,
# Hinterkoepfe t 0,16); t-only 0,25 holte eine echte Fehlbenennung zurueck
# (3 Anschnitt-Gesichter, e 0,14-0,18); das Paar killt alle drei.
# Dokumentierter Preis (vorgelegt, bewusst getragen): auf schwach messenden
# Kameras liegen auch KORREKTE Gesichter unter den Latten (4/7 Feld-Faelle)
# — dort wird ehrlich NICHT benannt statt falsch.
# GEMESSENE BOEDEN (03.09., ZWEI Eichungen am Testbett): Die Sicht-Eichung an
# 441 einzeln beurteilten Detektionen (vier Clips) ergab zunaechst e 0,120 /
# t 0,100. Die Ring-Sichtung der Fern-Kamera am selben Abend (54 Ring-Bilder
# einzeln beurteilt) WIDERLEGTE den e-Teil: auf Fern-Kameras misst e INVERS
# zur Gesichtsqualitaet (scharfe unbewegte Objekte e-Median 0,126 UEBER den
# klein-verwischten klaren Gesichtern 0,116) — der 0,12er-Boden graute 8 von
# 9 A-Bildern aus, darunter das einzige frisch erkennbare Material der Kamera
# (sim bis 0,60 auf eine Bestands-Person), und liess 5 von 6 Objekten durch.
# User-Entscheid 03.09. abends deshalb: e-Boden zurueck auf 0,10 — Objekte
# trennt NICHT e, sondern der Pose-Kopf. t 0,100 bestaetigt (der alte
# 0,200er-Boden warf 71 echte Gesichter weg, tiefstes klares Gesicht t 0,181).
# Belege: Testbett-Belege unter labor_frigate (gitignored): boedenmessung/ + Ring-Sichtung.
STIMM_BODEN = {"empfinden": 0.10, "t": 0.100}     # absolute Minima (klemmen alles)
# Pose-Kopf-Boden (User-Entscheid 03.09. abends, zweite Stufe nach der Ring-
# Sichtung): 0,60 liess das eine Objekt im Ring (p 0,612) durch; die Sichtung
# zeigte die saubere Luecke 0,612 (einziges Nicht-Gesicht unterhalb) / 0,722
# (naechstes echtes Bild). 0,65 wirft genau dieses Objekt raus und kostet
# dort null Gesichter. Rest-Risiko benannt: die 441er-Eichung sah D-Bilder
# bis 0,654 — Einzelobjekte im Band 0,650-0,654 passieren weiterhin (bewusst
# getragen, B-Untergrenze 0,701). Werkswert unkalibrierter Kameras, Regler-
# Minimum der Kalibrier-Seite UND Klemm-Untergrenze gesetzter pose_min-Werte.
# Feld-Folge unveraendert: Kameras, deren echte Menschen nur Kopf-Scores
# 0,2-0,3 liefern (ferne Deckensicht), sieben damit auch ohne Regler.
POSE_BODEN = 0.65
# DETEKTIONS-Boden (.514, Etappe 3 „ein Sieb"): die Untergrenze der det-Regler
# auf der Kalibrierseite und zugleich der Werkswert der det-Achse, wenn weder
# Kamera noch globaler Wert gesetzt ist. Die Zahl ist NICHT neu — sie stand
# seit dem Zentral-Umbau als Literal "0.40" in der Regler-Skala des Registers
# „Erkennen" (routes/livekalib.py) und ist der Wert, unter den ein Betreiber
# den Detektor-Score dort nie stellen kann. Sie steht seit .514 HIER, weil das
# Katalog-Register denselben Boden braucht und ein zweites Literal daneben
# genau die K3-Falle waere. Bewusst NICHT dasselbe wie livewache.DET_MIN_MIN
# (0,05): das ist die Annahme-Spanne des Store-Schreibwegs (Hand-Edit,
# API-Aufrufer), nicht die Regler-Skala.
DET_BODEN = 0.40
# NORM-Boden (.515, Sensor 5 „Norm-Boden, schaltbar"): die Feature-Norm ist
# seit .515 die FUENFTE Achse der Ein-Sieb-Mechanik (core/kamerakalib.py).
# Diese Null ist das REGLER-MINIMUM und zugleich die AUS-Stellung: 0 heisst
# nach der Haus-Invariante „dieser Anteil ist bewusst aus" (stimme_ok/
# achse_ok). Sie ist seit .516 NICHT mehr der Werkswert des Katalog-Registers
# — der steht in `norm_werk()` darunter (User-Entscheid 10.09.). Fuer das
# ERKENNEN-Register bleibt sie beides, Boden UND Werkswert: dort misst
# niemand die Feature-Norm, und eine Latte ohne Messung waere fail-closed.
NORM_BODEN = 0.0


def norm_werk():
    """Werks-Vorgabe der Norm-Achse im KATALOG-Register -> float.

    USER-ENTSCHEID 10.09.2026 nach Sichtung am Norm-Schieber (756
    Ernte-Bilder, Median 20,7): der Grundwert ist 20. Er steht als EINE
    Zahl HIER und nirgends sonst — wer ihn verschiebt, verschiebt ihn an
    dieser Stelle; Register, Config-Default, Regler-Vorgabe und Gate-Anker
    lesen alle diesen Griff (`kamerakalib.katalog_start`, `verifyd
    .load_config`, `routes.livekalib` ueber KSTD, `tools/qs.sh`).

    WOZU die Achse ueberhaupt AN ist (.516 R2, unveraendert): sie trennt
    SCRFD-Fehldetektionen mit hohem det-Score von echten Klein-Gesichtern —
    die einzige Achse, die das kann.

    HERKUNFT DER 20, und warum es jetzt eine eigene Zahl ist: .516 nahm als
    Werkswert den Verweis auf `core.benennung.NORM_LATTE["min"]` = 22,0, die
    SAMMEL-SCHWELLE des Lernvorrats vom 20.08.2026 — sie war die einzige
    bestehende Norm-Quelle, und der Auftrag lautete damals ausdruecklich
    „Quelle referenzieren, kein neues Literal". Das war ein GELIEHENER Wert:
    die Sammel-Schwelle beantwortet die Frage „was kommt in den Vorrat", die
    Register-Achse die Frage „was behaelt ein Lernlauf ueberhaupt". Die
    Sichtung des Users am Schieber hat die zweite Frage an eigenem Material beantwortet
    und liegt darunter. Die 22,0 bleibt, wo sie hingehoert (Vorrats-Boden,
    `vorrat_norm_min`); sie ist ab jetzt NICHT mehr die Quelle dieses Werts,
    und der Verweis darauf ist bewusst geloest — sonst zoege eine Aenderung
    dort still diese Achse mit. Beide stehen weiter auf DERSELBEN Skala
    (0..NORM_MAX = 35), es wird nichts umgerechnet.

    NICHT fuer das ERKENNEN-Register (`erkennen_start`): dort bleibt die Achse
    auf 0/aus, weil der Erkennungs-Weg die Feature-Norm heute gar nicht misst.
    Eine Latte ohne Messung waere fail-closed und schaltete die Erkennung ab —
    deshalb hat dieses Register seit .517 auch keinen Norm-Regler mehr
    (User-Entscheid 10.09., routes/livekalib.py)."""
    return 20.0
# Obergrenze der Norm-Skala. Sie ist keine neue Zahl, sondern die Spanne, die
# die Konfigurationsseite fuer die bestehenden Norm-Linien fuehrt
# (vorrat_norm_min/katalog_norm_min: 15-35). Sie steht HIER, weil Regler-Skala,
# Zahlen-Wache (kamerakalib._achse_hi) und die zwei neuen Config-Schluessel
# dieselbe Grenze brauchen — drei Literale nebeneinander waeren die K3-Falle.
NORM_MAX = 35.0
# REGLER-MINIMUM der Katalog-Norm (.520, USER-ENTSCHEID 10.09.2026, Wortlaut:
# „ich moechte dass das mini 18 ist und 20 als default"). Das ist der LINKE
# ANSCHLAG des Norm-Schiebers im Katalog-Register (routes/livekalib.py, Regler
# `lk-kn`) und sonst nichts:
#   * NICHT der Sieb-Boden — die Sieb-/Aus-Semantik haengt unveraendert an
#     NORM_BODEN (Latte <= 0 = dieser Anteil ist bewusst aus, core.guete
#     .achse_ok) und an der Store-Spanne (core.livewache.NORM_MIN_MIN = 0).
#   * NICHT der Werkswert — der steht in `norm_werk()` (20) und bleibt dort.
# Die Zahl steht HIER, weil die Seite sie nur noch LESEN darf; ein Literal 18
# in routes/ waere genau die K3-Falle (zweite Zahl neben norm_werk/NORM_MAX).
#
# KONSEQUENZ, VOM USER SO GEWOLLT: an diesem Regler entfaellt die Aus-Stellung
# — die Norm-Achse des Katalog-Registers ist VON DER KALIBRIER-SEITE AUS nicht
# mehr abschaltbar. Wer sie ausschalten will, nimmt den Config-Schluessel
# `katalog_guete_norm_min` (Spanne dort unveraendert 0..NORM_MAX). Die Seite
# ist damit ENGER als der Store — bewusst: 18 ist die Untergrenze, unter der
# der User am Schieber kein brauchbares Ernte-Material mehr gesehen hat (dieselbe
# Sichtung, aus der der Grundwert 20 kommt), und ein Regler, der bis 0 laeuft,
# laedt zum versehentlichen Abschalten der einzigen Achse ein, die
# Fehldetektionen mit hohem det-Score von echten Klein-Gesichtern trennt.
NORM_REGLER_MIN = 18.0
# KANTEN-Werkswert (.515, Sensor 6 „Kanten-Latte", User-Entscheid 10.09.2026):
# die Mindest-Kantenlaenge eines Gesichts in PIXELN als sechste Achse derselben
# Mechanik. Die 25 ist NICHT neu — sie stand seit .400 als Auslieferungswert des
# Config-Schluessels `urteil_kante` in verifyd.load_config und ist an Feldmaterial
# gemessen: richtige Stimmen leben auf Uebersichts-Kameras bei 30-49 px, die
# Unsinns-Faelle bei 11-19 px; 70 kippt die richtigen mit, 25 kostet keine. Sie
# steht seit .515 HIER, weil beide Register denselben Werkswert brauchen und ein
# zweites Literal daneben genau die K3-Falle waere.
#
# WERKSWERT UND REGLER-MINIMUM FALLEN HIER AUSEINANDER, und das mit Absicht:
# der Werkswert ist 25, das Regler-Minimum bleibt 0 — sonst waere die Achse nur
# hochziehbar und nicht abschaltbar, und „Latte <= 0 = aus" gaelte fuer sie
# nicht mehr. Bei det/Pose faellt beides zusammen, weil dort der gemessene
# Boden zugleich der Werkswert ist (User 03.09. „durchgaengig").
# Seit .520 ist die Kante nicht mehr die EINZIGE Achse mit dieser Spreizung:
# die Katalog-Norm hat Werkswert 20 (`norm_werk`) und Regler-Minimum 18
# (`NORM_REGLER_MIN`) — dort aber mit der GEGENTEILIGEN Absicht (der Regler
# soll die Achse gerade NICHT mehr abschalten koennen, User-Entscheid 10.09.).
# Zwei Spreizungen, zwei Begruendungen; keine davon ist ein Versehen.
KANTE_WERK = 25
# Obergrenze der Kanten-Skala = die Spanne, die die Konfigurationsseite fuer
# `urteil_kante` seit jeher fuehrt (0-400 px). Wie NORM_MAX keine neue Zahl,
# sondern die EINE Quelle fuer Regler, Store-Spanne und Config-Register.
KANTE_MAX = 400
# SYNC-FIX (User 03.09., Klon-Testbett-Befund am Referenz-Event): der Werkswert
# ohne Kalibrierung IST der Boden — vorher galt still 0,175/0,225, waehrend die
# Kalibrier-Seite einer unkalibrierten Kamera 0,100/0,200 zeigte (Anzeige und
# Urteil waren asynchron; 38 von 39 gueltigen Referenz-Stimmen starben am
# unsichtbaren 0,175er-e-Sieb). Wer schaerfer sieben will, kalibriert die Kamera.
STIMM_DEFAULT = dict(STIMM_BODEN)                 # Werkswerte ohne Kalibrierung = Boden
ANZEIGE_STARTWERTE = dict(STIMM_DEFAULT)          # Vorgaben-Knopf setzt die Werks-Boeden
# Regler-Untergrenze der KATALOG-Latte (.511): dieselbe gemessene Keller-Grenze
# wie bei den Stimm-Latten — unter 0,10 liegen nur noch Kopf-gesenkt/Augen-weg/
# Hinterkopf (Messung 01.09.), da ist nichts mehr, was ein Katalog braucht.
# ABLEITUNG statt eigener Zahl (K3): die Skala ist dieselbe, also ist es auch
# ihr Boden. Bis .510 stand die Regler-Skala bei 0,175/0,375 — das war der
# alte Werkswert minus 0,025 und damit ein Zweit-Literal in der Seite.
KATALOG_BODEN = dict(STIMM_BODEN)

# RING-EINLASS (Kalibrier-Vorrat) — FIX 02.09. nach dem Tester-Befund: der
# Einlass nahm die alten globalen Lernlauf-Startwerte (t 0,400 = KATALOG-Latte
# auf der Datei-Skala, mit .516 entfernt) und
# verwarf beim Tester 73/73 Kandidaten eines Tages (e 0,16-0,20 / t 0,26-0,43)
# — der Vorrat blieb leer, kalibrieren war unmoeglich. Der Ring soll zeigen,
# was die Kamera WIRKLICH liefert (auch Mittelmaessiges, sonst gibt es nichts,
# woran der Nutzer die Latte setzen koennte); nur Totes bleibt draussen. Werks-
# Boden deshalb die gemessene Keller-Grenze (01.09.: unter 0,10 nur Kopf-
# gesenkt/Augen-weg/Hinterkopf). Menschen-Urteil liefert das Pose-Gate.
RING_BODEN = {"empfinden": 0.10, "t": 0.10}


def stimm_latten(guard):
    """Die zwei Stimm-Latten (e_min, t_min) einer Kamera: der kalibrierte
    Regler-Wert, nach unten auf STIMM_BODEN geklemmt (darunter geht niemand
    — User-Entscheid); ohne Kalibrierung STIMM_DEFAULT. guard ist das
    Kamera-Cfg-Dict (guete_e_min/guete_t_min) oder None."""
    g = guard or {}
    out = []
    for key, mass in (("guete_e_min", "empfinden"), ("guete_t_min", "t")):
        w = g.get(key)
        try:
            w = float(w) if w is not None else None
        except (TypeError, ValueError):
            w = None
        out.append(STIMM_DEFAULT[mass] if w is None else max(w, STIMM_BODEN[mass]))
    return out[0], out[1]


# INVARIANTE: STIMME_FAIL_CLOSED   (Marke: CLAUDE.md "Messbarkeit vor Stimme")
def stimme_ok(latte_e, latte_t, e, t):
    """Besteht ein Fund die Stimm-Latten? FAIL-CLOSED JE FUND — bei AKTIVER
    Latte (> 0) verwirft ein NICHT MESSBARER Wert (None) die Stimme DIESES
    Funds. Eine Stimme, deren Qualitaet niemand messen konnte, ist keine
    gemessene Stimme (User-Entscheid 07.09.2026: "nicht messbar = raus";
    Bauplan 0.1.0.510 B1, gebaut in .510).

    Latte <= 0 heisst UNVERAENDERT: dieser Anteil ist bewusst aus
    (Diagnose-/Altvergleichs-Laeufe) — dort passiert jeder Wert wie bisher.

    Der MODELL-Ausfall laeuft ausdruecklich NICHT ueber diese Funktion
    (Gegenpruefung W1, Befund M-1): fehlen die Messmodelle, setzen die
    VERBRAUCHER ihre Latten LAUT auf 0 (analyze.py URT_G_AUS;
    core/livewache._namens_stimmen) und landen damit im Latte-<=-0-Zweig.
    Kurzform der Regel: fail-closed je FUND, fail-open je MODELL. Wer diese
    Funktion einmal ohne das Modell-Gegenstueck ruft, schaltet bei fehlenden
    Modelldateien die ganze Erkennung still ab.

    Preis, beziffert und bewusst getragen (W1 BL-3, 173 Band-Faelle vom
    07.09.): t war bei 9 Faellen nicht messbar, davon 7 mit Richterurteil
    "richtig" — die fallen jetzt mit."""
    for latte, wert in ((latte_e, e), (latte_t, t)):
        if latte and latte > 0 and (wert is None or float(wert) < float(latte)):
            return False
    return True
# INVARIANTE-ENDE: STIMME_FAIL_CLOSED


def achse_ok(latte, wert):
    """EINE Achse gegen ihre Latte — GENAU der Vergleich, den `stimme_ok`
    darueber fuer seine zwei Achsen fuehrt, nur fuer eine.

    WOZU (.514, Etappe 3 „ein Sieb"): das Lern-Sieb urteilt auf VIER Achsen
    (det, Empfinden, Erkennbarkeit, Kopfpose). Die zwei Guete-Achsen hat
    `stimme_ok`; det und Pose brauchen dieselbe Regel, und die haette sonst als
    zweites Literal danebengestanden (K3). `stimme_ok` selbst bleibt Wort fuer
    Wort unangetastet — es ist eine eingefrorene Invariante (tools/
    invarianten.freeze); die Gate-Stufe haelt beide gegeneinander, damit sie
    nie auseinanderlaufen.

    Die Regel, ausgeschrieben: Latte <= 0 oder nicht gesetzt = diese Achse ist
    AUS, jeder Wert passiert. Latte > 0 = fail-closed JE FUND — ein nicht
    messbarer Wert (None) faellt, genau wie ein zu kleiner.

    EINZIGER Unterschied zu `stimme_ok`, benannt: eine UNLESBARE Zahl. Dort
    wirft der float()-Cast (der Fall kommt auf dem Stimm-Weg nicht vor, die
    Werte sind Messergebnisse); hier faellt ein unlesbarer WERT (nicht messbar
    ist nicht messbar) und eine unlesbare LATTE siebt nicht (Muster
    kamerakalib._zahl: eine kaputte Zahl darf keine Bilder verwerfen).

    Fail-open je MODELL bleibt Sache des VERBRAUCHERS: fehlt ein Messmodell,
    setzt er seine Latte laut auf 0 und landet damit im Aus-Zweig hier."""
    if latte is None:
        return True
    try:
        l = float(latte)
    except (TypeError, ValueError):
        return True                 # unlesbare Latte siebt nie (Muster _zahl)
    if l <= 0:
        return True
    if wert is None:
        return False
    try:
        return float(wert) >= l
    except (TypeError, ValueError):
        return False


_lock = threading.Lock()
_sess = {}


def _session(pfad):
    """Lazy, prozessweit einmal. Thread-Kappung ueber DEN einen Haus-Griff
    face_audit._ort_thread_opts (cgroup-bewusst; eine nackte Session baute
    ihren Pool nach HOST-Kernen — Gate-Stufe erzwingt den Griff)."""
    with _lock:
        s = _sess.get(pfad)
        if s is None:
            import onnxruntime as ort
            from face_audit import _ort_thread_opts
            # deckel=4 (.377b, GEMESSEN im Prod-Container unter Lauf-Last):
            # 12 Threads = 33+57 ms je Bild, 4 Threads = 4+13 ms — Mini-Netze
            # ersticken am Thread-Overhead. 4 ist das Messoptimum der Reihe
            # (1/2/4 Threads), nie mehr als die erlaubten Kerne.
            s = ort.InferenceSession(pfad, sess_options=_ort_thread_opts(deckel=4),
                                     providers=["CPUExecutionProvider"])
            _sess[pfad] = s
        return s


def verfuegbar():
    """Beide Modelldateien vorhanden? (Alt-Images ohne die Dateien laufen
    weiter — die Verbraucher fallen dann auf den Alt-Weg zurueck, laut.)"""
    return os.path.exists(PFAD_T) and os.path.exists(PFAD_E)


def fiqa_t(aligned_bgr112):
    """eDifFIQA(T) auf dem aligned 112x112-BGR-Crop -> float (hoch = gut)."""
    s = _session(PFAD_T)
    x = ((aligned_bgr112[:, :, ::-1].astype(np.float32) / 255.0) - 0.5) / 0.5
    return float(s.run(None, {s.get_inputs()[0].name:
                              x.transpose(2, 0, 1)[None]})[0].ravel()[0])


def empfinden(roh_bgr):
    """Efficient-FIQA auf dem rohen Crop (beliebige Groesse) -> float."""
    import cv2
    s = _session(PFAD_E)
    r = cv2.resize(roh_bgr, (352, 352))[:, :, ::-1].astype(np.float32) / 255.0
    x = (r - _IN_MEAN) / _IN_STD
    return float(s.run(None, {s.get_inputs()[0].name:
                              x.transpose(2, 0, 1)[None]})[0].ravel()[0])
