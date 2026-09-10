"""routes/livekalib — DIE Kalibrier-Seite EINER Kamera (/kalibrierung/<kamera>).

Seit dem Zentral-Umbau (31.08.) ist das die einzige Kalibrierseite je Kamera:
erreichbar aus der Uebersicht /kalibrierung (Menuepunkt oben in der
Hauptleiste) und aus der Erkennungs-Kachel von /live/<kamera>. Der alte
Pfad /live_kalibrierung/<kamera> leitet hierher um — ein Bedienweg, kein
zweiter. (Der Modulname bleibt: die Seite ist gewachsen, nicht ersetzt, und
mit ihm bleiben die schon fuenfsprachig gepflegten livekalib.*-Texte gueltig.)

DREI ABSCHNITTE — die Drei-Latten-Semantik (User 31.08.):

  1. ANZEIGE / MELDEN / VORRAT — det, Empfinden, Erkennbarkeit. Sie
     entscheiden, WELCHES Bild in Meldung und Anzeige geht und WAS in den
     Kalibrier-Vorrat kommt. Nicht mehr.
  2. KATALOG-AUFNAHME — eine EIGENE Latte: welches Bild dieser Kamera
     ueberhaupt Referenz werden darf. Sie greift an allen Uebernahme-Wegen
     (core/kamerakalib.py), niemals rueckwirkend. Seit .511 ist sie
     ausdruecklich LIBERAL (Werkswert 0,125/0,125, Regler-Skala ab 0,100):
     aufnehmen ist die weite Tuer, gesiebt wird im dritten Register.
  3. MATERIAL — der Vorrat dieser Kamera: Stand, Nachschub auf Knopfdruck,
     Loeschweg.

WARUM JE KAMERA und nicht einmal fuer alle: die Guete-Skalen sind
kameraabhaengig. Gemessen am 31.08. an Feldmaterial: Median fiqa_t 0,181 auf
der einen Kamera gegen 0,073 auf der anderen. Eine gemeinsame Zahl waere fuer
die eine grosszuegig und fuer die andere ein Kahlschlag.

WAS DIE SEITE EHRLICH SAGEN MUSS (User-Auflage, aus zwei Messungen desselben
Tages): die zwei Guete-Regler siegen NICHT die Erkennung. Wer vor dem
Namens-Voting siebt, verliert Bestaetigungen — ohne Siebe kamen 41 % mehr
zustande, und ausgerechnet die Pose korrelierte NEGATIV. Die Guete entscheidet
deshalb nur zweierlei: WELCHES Bild in die Meldung/Anzeige geht und WAS in den
Vorrat kommt. Genau das steht auch als Prosa an den Reglern; die Seite darf hier
nichts versprechen, was der Code nicht tut.

Rein lesend bis auf den Uebernehmen-POST — und der geht ueber /live_speichern,
also denselben Weg (mit denselben Riegeln und demselben Audit) wie jede andere
Aenderung an einem Waechter. Kein eigener Schreibweg hier. Weil ein FEHLENDES
Feld dort "behalten" heisst (live_speichern._wert), schickt diese Seite genau
ihre eigenen Regler-Werte und laesst alles andere unangetastet.

POSE-REGLER (03.09., Stufe 1): der vierte Regler im Register "Erkennen"
arbeitet auf dem Kopf-Score p, den der Worker-Zulauf je Ring-Bild mitmisst.
Er wirkt HIER sofort (die Galerie dimmt mit, der Zaehler rechnet ihn mit) und
wird als `pose_min` je Kamera gespeichert. Was er NICHT tut: sieben. Weder
Worker noch Live-Weg fragen den gespeicherten Wert bisher — Stufe 2 folgt
nach User-Entscheid. Genau das sagt auch die Prosa am Regler; dieselbe
Auflage wie bei den zwei Guete-Reglern (nichts versprechen, was der Code
nicht tut).

NORM-REGLER — NUR IM KATALOG-REGISTER (.517, User-Entscheid 10.09.2026 nach
Sichtung am Schieber). Die Feature-Norm ist die fuenfte Achse BEIDER Register
(Sechs-Achsen-Verfassung, core/kamerakalib.py), aber einen SCHIEBER hat sie nur
dort, wo sie auch gemessen wird:
  * Register KATALOG — hier siebt der Wert wirklich: der Lernlauf misst die
    Feature-Norm je Kandidat und fragt sie ueber core.kamerakalib.sieb_ok,
    genau wie ihre fuenf Geschwister. Regler `lk-kn`, Werksmarke 20
    (core.guete.norm_werk, kommt ueber KSTD vom Server), linker Anschlag seit
    .520 bei 18 (core.guete.NORM_REGLER_MIN, User-Entscheid 10.09.2026).
    KEINE Aus-Stellung mehr an diesem Regler: die Achse ist von dieser Seite
    aus nicht abschaltbar, sondern nur zwischen 18 und 35 einstellbar. Wer sie
    ganz aus haben will, nimmt den Config-Schluessel `katalog_guete_norm_min`
    (Store-Spanne unveraendert ab 0). Die zwei KANTEN-Regler behalten ihre
    Aus-Stellung — dort ist die 0 weiter der linke Anschlag.
  * Register ERKENNEN — KEIN Regler mehr. Der Erkennungs-Weg MISST die
    Feature-Norm nicht (sie braeuchte eine zweite Kopie des Erkennungs-Modells
    im Analyse-Worker — eine Speicher-Entscheidung, kein Regler), also gibt es
    dort nichts einzustellen: die Achse steht werksseitig auf 0/aus und bleibt
    es. .515/.516 hatten den Schieber dort mit einem Ehrlichkeits-Satz
    („gespeichert, aber siebt nicht"); ein Regler, der nichts bewirkt, ist
    schlechter als keiner — er laedt zum Einstellen ein und veraendert nichts.
    Der gespeicherte Wert (`norm_min`, globaler Rueckfall `urteil_norm_min`)
    bleibt unangetastet: diese Seite schickt das Feld nicht mehr mit, und ein
    fehlendes Feld heisst bei live_speichern „behalten".
Die Galerie kann den verbliebenen Regler nur an LERNLAUF-Bildern vorfuehren:
der Kalibrier-Ring fuehrt keine Norm. Steht keine im Material, sagt die Seite
das (ohne_norm), statt den Regler wortlos anzubieten.

KANTEN-REGLER (.515, Sensor 6): die Mindest-Kantenlaenge eines Gesichts in
PIXELN, ebenfalls in beiden Gruppen. Anders als bei der Norm siebt dieser Wert
auf BEIDEN Wegen wirklich:
  * Register ERKENNEN — er ist der Wert, den der Stimmweg bisher als eine
    globale Konstante `urteil_kante` (25 px) las. Werkswert und globaler
    Rueckfall sind unveraendert diese 25, der Regler macht sie nur je Kamera
    einstellbar. Ohne Kamera-Wert ist der Umbau damit WERTGLEICH.
  * Register KATALOG — dort ist die Kante eine NEUE Sieb-Achse des Lernlaufs.
    .514 hatte die alte Ernte-Kante (60 px) abgeloest, weil sie eine zweite,
    mit dem Erkennungs-Weg unvergleichbare Zahl war; jetzt kommt sie als
    Register-Achse mit dem Wert des Erkennungs-Wegs zurueck.
Werkswert (25) und Regler-Minimum (0) fallen hier auseinander — 0 muss
erreichbar bleiben, sonst waere sie nicht abschaltbar. Seit .520 ist die Kante
damit nicht mehr allein: die Katalog-Norm hat Werkswert 20 und Regler-Minimum
18, dort aber mit der umgekehrten Absicht (die Aus-Stellung soll gerade NICHT
erreichbar sein).
"""
import html
import json
import time
import urllib.parse

from core.sprache import t


# Regler-Untergrenzen der zwei Erkennen-Guete-Regler = absolute Stimm-Boeden
# (EINE Quelle, core/guete.STIMM_BODEN): darunter geht niemand
# (User-Entscheide 01.09. abends: t nie unter 0,2; e-Boden = Default 0,175).
from core.guete import STIMM_BODEN as _KB
from core.guete import POSE_BODEN as _PB
_BODEN_E = f"{_KB['empfinden']:.3f}"
_BODEN_T = f"{_KB['t']:.3f}"

# Untergrenzen der zwei KATALOG-Regler — dieselbe Bauform, eigene Quelle
# (core.guete.KATALOG_BODEN, .511). Bis .510 standen hier 0,175 und 0,375 als
# Literale in HTML *und* JavaScript: der damalige Werkswert minus 0,025, also
# vier Zweit-Zahlen, die beim Senken der Latte haetten mitwandern muessen.
# Der Werkswert selbst (KSTD) kommt weiterhin vom Server durch — die Grenzen
# hier begrenzen nur, was der Regler ueberhaupt einstellen kann.
from core.guete import KATALOG_BODEN as _KATB
_KAT_LO_E = f"{_KATB['empfinden']:.3f}"
_KAT_LO_T = f"{_KATB['t']:.3f}"

# .514 (Etappe 3 „ein Sieb"): das Katalog-Register bekommt die zwei fehlenden
# Achsen — Detektion und Kopf-Pose. Skala und Boden sind DIESELBEN wie bei den
# Geschwistern im Erkennen-Register (es ist dieselbe Messgroesse, nur ein
# anderer Zweck); beide Boeden kommen aus core.guete, keine Zweit-Literale.
from core.guete import DET_BODEN as _DB
_DET_LO, _DET_HI, _DET_SCHRITT = f"{_DB:.2f}", "0.60", "0.01"

# Skala des Pose-Reglers — fest wie bei den Nachbarn (Lehre der Lernlauf-Seite,
# s. JS-Kommentar unten). Gemessene Lage des Kopf-Scores: Mensch 0,77-1,04 am
# Klon-Material, das Live-Gate steht bei 0,70; die Skala laesst darueber Luft,
# ohne die Server-Spanne (livewache.POSE_MIN_MIN/MAX = 0-2) zu verlassen.
# 0 = AUS: unter dieser Stellung fehlt keinem Bild etwas.
_POSE_LO, _POSE_HI, _POSE_SCHRITT = f"{_PB:.2f}", "1.20", "0.01"   # Minimum = Werks-Boden (User 03.09.)

# .515 (Sensor 5) — die NORM-Achse. Seit .517 hat sie nur noch EINEN Regler,
# den des KATALOG-Registers (Begruendung im Modulkopf). Skala und Grenzen kommen
# wie bei allen Nachbarn aus core.guete, keine Zweit-Literale.
# .520 (User-Entscheid 10.09.2026, „ich moechte dass das mini 18 ist und 20 als
# default"): das Regler-Minimum ist NICHT mehr NORM_BODEN (0 = aus), sondern die
# eigene Quelle core.guete.NORM_REGLER_MIN = 18. Damit entfaellt die
# AUS-STELLUNG an diesem Regler — die Norm-Achse des Katalog-Registers ist von
# dieser Seite aus nicht mehr abschaltbar (so gewollt; abschalten geht ueber den
# Config-Schluessel `katalog_guete_norm_min`, dessen Spanne unveraendert bei 0
# beginnt). NORM_BODEN bleibt, wo es hingehoert: bei der Sieb-/Aus-Semantik
# („Latte <= 0 = aus") und in der Store-Spanne (core.livewache.NORM_MIN_MIN).
# Die WERKSMARKE des Reglers ist 20 (core.guete.norm_werk seit .517); sie kommt
# vom Server durch (KSTD), nie als Literal hier. Obergrenze NORM_MAX = die
# Skala, auf der die Norm-Linien des Lernvorrats stehen (15-35).
from core.guete import NORM_REGLER_MIN as _NRM
from core.guete import NORM_MAX as _NH
_NORM_LO, _NORM_HI, _NORM_SCHRITT = f"{_NRM:.1f}", f"{_NH:.1f}", "0.5"

# .515 (Sensor 6) — die KANTEN-Achse, ebenfalls in BEIDEN Registern. Hier
# fallen Werkswert und Regler-Minimum als EINZIGE Achse auseinander, mit
# Absicht: das Minimum ist 0 (= aus, sonst waere die Achse nicht abschaltbar),
# der Werkswert ist core.guete.KANTE_WERK = 25 px — genau die Zahl, die bis
# .514 als Konstante `urteil_kante` im Stimmweg stand. Obergrenze KANTE_MAX
# (400), die Spanne, die die Konfigurationsseite dafuer seit jeher fuehrt.
from core.guete import KANTE_WERK as _KW
from core.guete import KANTE_MAX as _KH
_KANTE_LO, _KANTE_HI, _KANTE_SCHRITT = "0", f"{int(_KH)}", "1"


def _wann(ts):
    if not ts:
        return ""
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))


def _bilder(kamera, vorrat, lauf_bilder):
    """Die Galerie-Zeilen BEIDER Quellen in EINER Liste.

    Ring-Bilder (was die Kamera im Betrieb geliefert hat) und die Bilder des
    letzten Lernlaufs VON DIESER KAMERA. Der Lernlauf-Kontext bleibt damit
    erhalten (er war die Herkunft der .377-Seite), ohne einen zweiten
    Bedienweg zu oeffnen — jede Kachel sagt, woher sie stammt.

    -1 heisst "nicht gemessen" und laesst die zugehoerige Latte passieren
    (Lernlauf-Bilder tragen keinen det-Wert, Alt-Images keine Guete-Masse);
    sonst blendete eine fehlende Messung Material aus, das es gar nicht
    beurteilt."""
    kq = urllib.parse.quote(str(kamera), safe="")
    aus = []
    for e in vorrat or []:
        aus.append({"src": f"/live_kalib_bild?k={kq}&d="
                           + urllib.parse.quote(str(e["d"]), safe=""),
                    "det": float(e.get("det") or 0),
                    "e": (-1.0 if e.get("e") is None else float(e["e"])),
                    "t": (-1.0 if e.get("t") is None else float(e["t"])),
                    "p": (-1.0 if e.get("p") is None else float(e["p"])),
                    # .515: der Ring fuehrt KEINE Feature-Norm — der Live-/
                    # Analyse-Weg misst sie nicht. -1 heisst wie ueberall
                    # „nicht gemessen" und passiert die Latte.
                    "n": -1.0,
                    # Ebenso die Kantenlaenge: der Ring-Index fuehrt sie nicht
                    # (er speichert Datei, Zeitstempel und die vier Messwerte).
                    "k": -1.0,
                    "q": "ring"})
    for b in lauf_bilder or []:
        aus.append({"src": f"/lernlauf/crop/{urllib.parse.quote(str(b['lid']), safe='')}/"
                           + urllib.parse.quote(str(b["d"]), safe=""),
                    "det": -1.0,
                    "e": float(b.get("e") if b.get("e") is not None else -1.0),
                    "t": float(b.get("t") if b.get("t") is not None else -1.0),
                    # .515: Lernlauf-Bilder tragen die Feature-Norm, wenn der
                    # Lauf sie gemessen hat — sie sind damit das einzige
                    # Material, an dem der Norm-Regler wirklich etwas zeigt.
                    "n": float(b.get("n") if b.get("n") is not None else -1.0),
                    # Lernlauf-Bilder tragen ihre Kantenlaenge in px
                    # (mitglieder_mit_guete liefert sie als `k`).
                    "k": float(b.get("k") if b.get("k") is not None else -1.0),
                    "q": "lauf"})
    return aus


def _quelle_wort(quelle):
    """Woher die geltende Katalog-Latte kommt — LITERALE Schluessel (die
    Sprach-Deckungsstufe liest t() statisch; ein zur Laufzeit gebauter
    Schluessel gilt ihr als tot, Auflage aus routes/live.py)."""
    return {"kamera": t("livekalib.katalog.quelle_kamera"),
            "global": t("livekalib.katalog.quelle_global"),
            "aus": t("livekalib.katalog.quelle_aus")}.get(str(quelle), "")


def _pruef_quelle_wort(quelle):
    """Dasselbe fuer die PRUEFER-Latte (.511 Stufe C) — eigene Schluessel, weil
    sie eine andere Frage beantwortet als die Katalog-Latte darueber und ein
    gemeinsamer Text beide Rollen verwischen wuerde."""
    return {"kamera": t("livekalib.pruefen.quelle_kamera"),
            "global": t("livekalib.pruefen.quelle_global"),
            "aus": t("livekalib.pruefen.quelle_aus")}.get(str(quelle), "")


def _regler(kennung, titel, prosa, lo, hi, schritt, wert):
    # Prosa als Hover-Titel statt Textblock (User 31.08.: drei Schieber in
    # EINER Reihe, damit die Galerie mehr Bilder zeigt — der Platz gehoert
    # den Bildern, die Erklaerung bleibt am Titel erreichbar).
    return (f'<div class="kal-zeile" title="{html.escape(prosa, quote=True)}">'
            f'<b>{titel}</b>'
            f'<input type="range" id="{kennung}" min="{lo}" max="{hi}" '
            f'step="{schritt}" value="{wert}">'
            f'<span id="{kennung}-wert"></span></div>')


def render(kamera, vorrat, guard, standard, kat, pruef=None, erk=None,
           lauf_bilder=(), deckel=0,
           fueller=(0, 0), hat_waechter=False, fueller_stand=None):
    """-> Seiten-INHALT.

    vorrat  = [{"d","ts","det","e","t"}, ...] aus livewache.kalib_lesen
    guard   = der normalisierte Waechter-Block (aktuelle Schwellen) oder {}
    standard= {"det","e","t"} die Werks-Startwerte (aus dem Code, nie hier)
    kat     = {"akt": {"e","t","quelle"}, "std": {"e","t"}} — geltende und
              Werks-Katalog-Latte (core.kamerakalib)
    pruef   = {"akt": {"t","quelle"}, "std": {"t"}} — geltende und Werks-Latte
              der BESTANDS-PRUEFUNG (core.refurteil, .511 Stufe C). Drittes
              Register: es urteilt ueber schon vorhandene Katalogbilder und
              nimmt keines auf. None = wie vor Stufe C (Register faellt weg)
    erk     = {"akt": {...,"quelle"}, "std": {...}} — die .515-Achsen des
              ERKENNEN-Registers (core.kamerakalib.erk_latten/erkennen_start).
              Sie loesen wie die Katalog-Achsen auf (Kamera -> global ->
              Werks-Boden) und sind deshalb NICHT im `guard` ablesbar. None =
              wie vor .515 (der Regler steht dann auf seinem Boden).
              Seit .517 nutzt die Seite davon nur noch die KANTE: die
              Norm-Achse hat im Erkennen-Register keinen Regler mehr, weil
              dort niemand die Feature-Norm misst. Der Aufrufer darf `n`
              weiter mitschicken, die Seite liest es nicht
    lauf_bilder = Lernlauf-Bilder DIESER Kamera (kann leer sein)
    deckel  = live_kalib_max (0 = Vorrats-Sammlung aus)
    fueller = (ziel_bilder, deckel_events) des On-demand-Fuellers
    hat_waechter = gibt es fuer diese Kamera einen Waechter-Block? (nur fuer
              den Rueckweg — die Kalibrierung selbst braucht keinen)"""
    nid = html.escape(str(kamera), quote=True)
    g = guard or {}
    # Der Erklaersatz beschreibt das Schieben an der Galerie ("drag the sliders
    # until the selection looks right") — ohne ein einziges Bild waere er eine
    # Wegbeschreibung ins Leere (dieselbe Lehre wie beim Leer-Zweig der
    # Lernlauf-Kalibrierseite, Usersicht-Durchgang 31.08.). Titel steht immer,
    # der Satz nur mit Material.
    titel = f'<h1>{t("livekalib.titel", name=html.escape(str(kamera)))}</h1>'
    kopf = titel + f'<p class="hinweis">{t("livekalib.erklaerung")}</p>'
    zurueck = (f'<p><a href="/kalibrierung">{t("livekalib.zur_uebersicht")}</a>'
               + (f' &middot; <a href="/live/{nid}">{t("livekalib.zurueck")}</a>'
                  if hat_waechter else "")
               + '</p>')
    bilder = _bilder(kamera, vorrat, lauf_bilder)
    bilder.sort(key=lambda z: -z["det"])
    akt = {"det": (g.get("det_min") if g.get("det_min") is not None
                   else standard["det"]),
           "e": (g.get("guete_e_min") or 0.0),
           "t": (g.get("guete_t_min") or 0.0),
           # Pose: der gespeicherte Kamera-Wert oder 0 = aus. Kein Werks-Wert
           # dahinter — solange die Latte nichts siebt, waere jeder Startwert
           # ausser "aus" eine Behauptung.
           # unkalibriert zeigt der Regler den Werks-Boden (= was wirklich
           # siebt, User 03.09. "durchgaengig"), nicht mehr 0.
           "p": (g.get("pose_min") if g.get("pose_min") is not None else _PB),
           # .517: die Norm-Achse steht hier NICHT mehr — das Erkennen-Register
           # hat keinen Norm-Regler mehr (User-Entscheid 10.09., Modulkopf).
           # Der gespeicherte Wert bleibt, er wird von dieser Seite nur weder
           # gezeigt noch geschrieben.
           # Kante: aufgeloest hereingereicht (Kamera -> global -> Werks-Boden)
           # statt aus dem Guard-Block, und hier ist das besonders wichtig —
           # der geltende Wert kommt fast immer aus dem GLOBALEN `urteil_kante`
           # und nicht aus dem Guard-Block.
           "k": float((erk or {}).get("akt", {}).get("k") or 0)}
    kat_akt = kat.get("akt") or {}
    kat_std = kat.get("std") or {}
    pruef_akt = (pruef or {}).get("akt") or {}
    pruef_std = (pruef or {}).get("std") or {}
    erk_std = (erk or {}).get("std") or {}
    # Fehlen die Guete-Modelle im Image, tragen ALLE Zeilen -1 — dann sind die
    # zwei Guete-Regler wirkungslos, und die Seite sagt das, statt sie
    # anzubieten und den Nutzer raten zu lassen.
    ohne_guete = bool(bilder) and all(b["e"] < 0 and b["t"] < 0 for b in bilder)
    # Dieselbe Ehrlichkeit fuer die Pose: traegt KEIN Bild einen Kopf-Score
    # (Bestands-Ring von vor der Messung, Bilder aus dem Live-/Ernte-Weg, ein
    # Image ohne ladbares Pose-Modell), dann bewegt der Regler hier nichts —
    # das sagt die Seite, statt ihn wortlos anzubieten.
    ohne_pose = bool(bilder) and all(b.get("p", -1.0) < 0 for b in bilder)
    # Dieselbe Ehrlichkeit fuer die Norm (.515): traegt KEIN Bild eine
    # Feature-Norm, bewegt der Regler an dieser Galerie nichts. Das ist der
    # Normalfall auf einer Kamera, deren Material nur aus dem Ring kommt —
    # gemessen wird die Norm im LERNLAUF, nicht im Live-/Analyse-Weg. Der
    # Regler bleibt trotzdem bedienbar: er stellt einen WERT ein, die Galerie
    # ist nur die Vorschau darauf.
    ohne_norm = bool(bilder) and all(b.get("n", -1.0) < 0 for b in bilder)
    # Und fuer die Kante: der Ring fuehrt sie nicht, Lernlauf-Bilder schon.
    ohne_kante = bool(bilder) and all(b.get("k", -1.0) < 0 for b in bilder)

    # --- Abschnitt 3 zuerst gebaut (er wird unten eingehaengt) -------------
    if not deckel:
        material = f'<div class="dim lv-zeile">{t("livekalib.material.aus")}</div>'
    else:
        # ZEITRAUM statt nur "zuletzt" (.507): "200 von hoechstens 200" sagt
        # nichts darueber, ob der Ring einen Tagesquerschnitt traegt oder in
        # drei Minuten an einer belebten Kamera vollgelaufen ist (Feldmessung
        # 04.09.). Beide Zeitpunkte kommen aus DERSELBEN Vorrats-Liste, kein
        # zweiter Lesegriff. min/max statt "erste/letzte Zeile": der Index ist
        # nach Schreib-Reihenfolge sortiert, eine Uhr-Korrektur bricht sie.
        # ts 0 = kein Zeitstempel und deshalb kein Zeitpunkt (s. _wann).
        _ts = [z for z in (float(e.get("ts") or 0) for e in vorrat or []) if z > 0]
        # Verglichen werden die ANGEZEIGTEN Zeitpunkte, nicht die rohen
        # Sekunden: _wann() rundet auf Minuten, und zwei Bilder derselben
        # Minute ergaeben sonst "von X bis X" — eine Spanne, die der Nutzer
        # nicht sieht. Steht nur ein Zeitpunkt da, bleibt es beim "zuletzt ...".
        von_txt, bis_txt = _wann(min(_ts, default=0.0)), _wann(max(_ts, default=0.0))
        if von_txt and bis_txt != von_txt:
            spanne = t("livekalib.material.zeitraum",
                       von=html.escape(von_txt), bis=html.escape(bis_txt))
        elif bis_txt:
            spanne = t("livekalib.material.wann", wann=html.escape(bis_txt))
        else:
            spanne = ""
        material = (f'<div class="lv-zeile">'
                    f'{t("livekalib.material.stand", n=len(vorrat or []), deckel=deckel)}'
                    + (f' &middot; {spanne}' if spanne else "") + '</div>')
    material += (f'<div class="dim lv-zeile">'
                 f'{t("livekalib.material.fuellen_prosa", ziel=int(fueller[0]), events=int(fueller[1]))}'
                 f'</div>'
                 f'<div class="dim lv-zeile kal-fuell" id="kf-{nid}"></div>'
                 f'<div class="lv-knoepfe">'
                 + (f'<button class="gtb" onclick="kalibFuellen(\'{nid}\',this)">'
                    f'{t("kalib.knopf_fuellen")}</button>' if deckel else "")
                 # DERSELBE Knopf-Text wie auf der Uebersicht (Usersicht-Fund:
                 # "Clear samples" hier gegen "Delete samples" dort — zwei
                 # Woerter fuer dieselbe Handlung auf zwei Seiten desselben
                 # Themas).
                 + (f'<button class="gtb" onclick="liveVorratLeeren(\'{nid}\',this)">'
                    f'{t("kalib.knopf_leeren")}</button>' if vorrat else "")
                 + '</div>')
    if len(lauf_bilder or []):
        material += (f'<div class="dim lv-zeile">'
                     f'{t("livekalib.material.lauf", n=len(lauf_bilder))}</div>')

    if not bilder:
        # Leer-Zweig ohne Regler (Muster der Lernlauf-Kalibrierseite): "schiebe,
        # bis dir die Grenze gefaellt" waere ohne ein einziges Bild eine
        # Wegbeschreibung ins Leere. Der Material-Abschnitt bleibt trotzdem
        # stehen — dort steht der Knopf, der die Leere beendet.
        return (titel + f'<div class="kal-leer">{t("livekalib.leer")}</div>'
                + f'<div class="card"><b>{t("livekalib.abschnitt.material")}'
                  f'</b>' + material + '</div>' + zurueck)

    # REIHENFOLGE (Usersicht-Durchgang 31.08.): erst das Material — "habe ich
    # ueberhaupt Bilder, und wie hole ich welche" ist die Frage vor jedem
    # Regler. Dann der EINE Regler-Block, und zwar KLEBEND und zusammen mit
    # Zaehlern und Uebernehmen: der erste Entwurf hatte die Regler in drei
    # Karten und den Zaehler darunter — man schob oben und die Wirkung stand
    # ausserhalb des Blicks. Die Galerie steht darunter und dimmt mit.
    # K1 (01.09.): laufender/letzter Fueller-Stand sichtbar — vorher wirkte
    # der Knopf wie tot, wenn der Worker belegt war (Feldtester-Klick ohne
    # jede Reaktion). Reine Anzeige aus kalibfueller.stand().
    fs = fueller_stand or {}
    fs_zeile = ""
    if fs:
        if fs.get("laeuft"):
            fs_zeile = (f'<div class="dim">{t("livekalib.fueller.laeuft")}: '
                        f'{int(fs.get("i") or 0)}/{int(fs.get("n") or 0)} · '
                        f'{int(fs.get("bilder") or 0)}/{int(fs.get("ziel") or 0)}'
                        + (f' — {html.escape(str(fs.get("notiz")))}'
                           if fs.get("notiz") else "") + "</div>")
        elif fs.get("grund") or fs.get("fehler"):
            fs_zeile = (f'<div class="dim">{t("livekalib.fueller.bilanz")}: '
                        f'{html.escape(str(fs.get("fehler") or fs.get("grund")))}'
                        f' · {int(fs.get("bilder") or 0)} '
                        f'{t("livekalib.fueller.bilder")}</div>')
    material_karte = (f'<div class="card"><b>{t("livekalib.abschnitt.material")}'
                      f'</b>' + material + fs_zeile + '</div>')
    regler = (
        # Zwei Register statt Dopplung (User 31.08.: "lieber zwei Register,
        # einmal fuer Erkennen und einmal fuer Lernen, und zwischen den
        # Registern schalten") — die Gruppen tragen dieselben Regler wie
        # zuvor, sichtbar ist immer genau EINE; der Vorgaben-Knopf bleibt
        # in der Aktionszeile beider Register.
        f'<div class="kal-tabs">'
        f'<button type="button" id="lk-tab-e" class="gtb on">'
        f'{t("livekalib.tab_erkennen")}</button>'
        f'<button type="button" id="lk-tab-l" class="gtb">'
        f'{t("livekalib.tab_lernen")}</button>'
        f'<button type="button" id="lk-tab-p" class="gtb">'
        f'{t("livekalib.tab_pruefen")}</button></div>'
        f'<div class="kal-gruppe" id="lk-reg-e"><b>{t("livekalib.abschnitt.anzeige")}</b>'
        f'<div class="kal-prosa">{t("livekalib.abschnitt.anzeige_prosa")}</div>'
        + _regler("lk-det", t("livekalib.regler_det"),
                  t("livekalib.regler_det_prosa"), _DET_LO, _DET_HI,
                  _DET_SCHRITT, _DET_LO)
        + _regler("lk-e", t("livekalib.regler_e"),
                  t("livekalib.regler_e_prosa"), _BODEN_E, "1", "0.001", _BODEN_E)
        + _regler("lk-t", t("livekalib.regler_t"),
                  t("livekalib.regler_t_prosa"), _BODEN_T, "1", "0.001", _BODEN_T)
        + ('<div class="kal-prosa">' + t("livekalib.ohne_guete") + "</div>"
           if ohne_guete else "")
        # Der Pose-Regler steht NACH dem ohne_guete-Satz: der spricht von "den
        # unteren zwei Reglern" und meint die zwei Guete-Regler ueber ihm.
        + _regler("lk-p", t("livekalib.regler_p"),
                  t("livekalib.regler_p_prosa"), _POSE_LO, _POSE_HI,
                  _POSE_SCHRITT, _POSE_LO)
        + ('<div class="kal-prosa">' + t("livekalib.ohne_pose") + "</div>"
           if ohne_pose else "")
        # .517 (User-Entscheid 10.09.): HIER stand bis .516 der Norm-Regler
        # `lk-n`. Er ist raus — die Feature-Norm wird auf dem Erkennungs-Weg
        # gar nicht gemessen, der Regler stellte also einen Wert ein, der nie
        # ein Urteil beruehrt hat. Die ACHSE bleibt (Sechs-Achsen-Verfassung:
        # `norm_min` im Guard-Block, globaler Rueckfall `urteil_norm_min`,
        # Aufloesung ueber kamerakalib.erk_latten) und steht werksseitig auf
        # 0 = aus. Ihr Regler lebt im Register „Face catalog" weiter, wo die
        # Norm wirklich gemessen wird und wirklich siebt.
        # .515 (Sensor 6): die Kanten-Latte. Sie steht ganz unten, obwohl ihre
        # MESSUNG nichts kostet — die Reihenfolge hier ist die des Anbaus, und
        # ein Umsortieren der bestehenden Regler waere eine Aenderung an einer
        # Seite, die der Nutzer kennt. Die Kostenordnung des URTEILS steht in
        # core.kamerakalib.SIEB_ACHSEN, nicht in dieser Spalte.
        + _regler("lk-k", t("livekalib.regler_k"),
                  t("livekalib.regler_k_prosa"), _KANTE_LO, _KANTE_HI,
                  _KANTE_SCHRITT, _KANTE_LO)
        + ('<div class="kal-prosa">' + t("livekalib.ohne_kante") + "</div>"
           if ohne_kante else "")
        + f'<div id="lk-stand"></div></div>'
        f'<div class="kal-gruppe" id="lk-reg-l" style="display:none">'
        f'<b>{t("livekalib.abschnitt.katalog")}</b>'
        f'<div class="kal-prosa">{t("livekalib.katalog.prosa")}</div>'
        f'<div class="kal-prosa">{t("livekalib.katalog.grenze")}</div>'
        f'<div class="dim lv-zeile">'
        f'{_quelle_wort(kat_akt.get("quelle") or "aus")}</div>'
        + _regler("lk-ke", t("livekalib.katalog.regler_e"),
                  t("livekalib.katalog.regler_e_prosa"), _KAT_LO_E, "1",
                  "0.001", _KAT_LO_E)
        + _regler("lk-kt", t("livekalib.katalog.regler_t"),
                  t("livekalib.katalog.regler_t_prosa"), _KAT_LO_T, "1",
                  "0.001", _KAT_LO_T)
        # .514: die zwei neuen Achsen. Sie stehen HINTER den zwei Guete-
        # Reglern, weil das die Reihenfolge des Urteils ist (billig zuerst,
        # die teure Pose zuletzt — core.kamerakalib.SIEB_ACHSEN) und weil der
        # ohne_guete-Satz des Nachbar-Registers dieselbe Ordnung hat.
        + _regler("lk-kd", t("livekalib.katalog.regler_det"),
                  t("livekalib.katalog.regler_det_prosa"), _DET_LO, _DET_HI,
                  _DET_SCHRITT, _DET_LO)
        + _regler("lk-kp", t("livekalib.katalog.regler_p"),
                  t("livekalib.katalog.regler_p_prosa"), _POSE_LO, _POSE_HI,
                  _POSE_SCHRITT, _POSE_LO)
        + ('<div class="kal-prosa">' + t("livekalib.ohne_pose") + "</div>"
           if ohne_pose else "")
        # .515: die Norm-Achse. Seit .517 ist das ihr EINZIGER Regler im Haus
        # (im Nachbar-Register wird die Norm nicht gemessen, dort gibt es
        # nichts einzustellen). Hier siebt sie wirklich — der Lernlauf fragt
        # sie ueber core.kamerakalib.sieb_ok. Werksmarke 20 ueber KSTD, linker
        # Anschlag seit .520 bei 18 (core.guete.NORM_REGLER_MIN) statt bei 0 —
        # dieser Regler kann die Achse also nicht mehr ausschalten.
        + _regler("lk-kn", t("livekalib.katalog.regler_n"),
                  t("livekalib.katalog.regler_n_prosa"), _NORM_LO, _NORM_HI,
                  _NORM_SCHRITT, _NORM_LO)
        + ('<div class="kal-prosa">' + t("livekalib.ohne_norm") + "</div>"
           if ohne_norm else "")
        + _regler("lk-kk", t("livekalib.katalog.regler_k"),
                  t("livekalib.katalog.regler_k_prosa"), _KANTE_LO, _KANTE_HI,
                  _KANTE_SCHRITT, _KANTE_LO)
        + ('<div class="kal-prosa">' + t("livekalib.ohne_kante") + "</div>"
           if ohne_kante else "")
        + '<div class="dim" id="lk-kstand"></div></div>'
        # DRITTES Register (.511 Stufe C): die Latte des BESTANDS-Pruefers.
        # Sie steht bewusst hier — dieselbe Seite, dieselbe Galerie, dieselbe
        # Skala — und trotzdem als eigener Regler: Aufnehmen und Nachpruefen
        # sind zwei Fragen, und ein Zug am einen darf den anderen nicht still
        # mitziehen (der Rollen-Zuschnitt des Users 08.09.). Nur EIN Regler: die
        # Guete-Achse des Pruefers ist fiqa_t, die zweite Achse ist der
        # bestehende Norm-Boden des Lernvorrats aus der Konfigurationsseite.
        f'<div class="kal-gruppe" id="lk-reg-p" style="display:none">'
        f'<b>{t("livekalib.abschnitt.pruefen")}</b>'
        f'<div class="kal-prosa">{t("livekalib.pruefen.prosa")}</div>'
        f'<div class="kal-prosa">{t("livekalib.pruefen.grenze")}</div>'
        f'<div class="dim lv-zeile">'
        f'{_pruef_quelle_wort(pruef_akt.get("quelle") or "aus")}</div>'
        + _regler("lk-pt", t("livekalib.pruefen.regler_t"),
                  t("livekalib.pruefen.regler_t_prosa"), "0", "1", "0.001",
                  f'{float(pruef_std.get("t") or 0.0):.3f}')
        + '<div class="dim" id="lk-pstand"></div></div>')
    return kopf + material_karte + f"""
<div class="kal-regler">
{regler}
 <div class="kal-aktion">
  <button id="lk-std" class="gtb">{t("livekalib.standard")}</button>
  <button id="lk-save" class="gtb on">{t("livekalib.uebernehmen")}</button>
  <span id="lk-msg"></span>
 </div>
</div>
<div class="kal-g" id="lk-g"></div>
{zurueck}
<script>
const B = {json.dumps(bilder, ensure_ascii=False)};
const KAM = {json.dumps(str(kamera), ensure_ascii=False)};
const AKT = {json.dumps(akt)};
const STD = {json.dumps(standard)};
const KAKT = {json.dumps({"e": kat_akt.get("e"), "t": kat_akt.get("t"),
                          "det": kat_akt.get("det"), "p": kat_akt.get("p"),
                          "n": kat_akt.get("n"), "k": kat_akt.get("k")})};
const KSTD = {json.dumps({"e": kat_std.get("e"), "t": kat_std.get("t"),
                          "det": kat_std.get("det"), "p": kat_std.get("p"),
                          "n": kat_std.get("n"), "k": kat_std.get("k")})};
/* .515: die WERKS-Vorgabe der Erkennen-Achsen dieses Registers — sie kommt vom
   Server (core.kamerakalib.erkennen_start), damit der Vorgaben-Knopf keine
   zweite Zahl kennt. Seit .517 nur noch die Kante (core.guete.KANTE_WERK):
   die Norm-Achse hat hier keinen Regler mehr, also auch keine Vorgabe zu
   setzen — ihr Wert im Store bleibt unberuehrt. */
const ESTD = {json.dumps({"k": erk_std.get("k")})};
const PAKT = {json.dumps({"t": pruef_akt.get("t")})};
const PSTD = {json.dumps({"t": pruef_std.get("t")})};
const T_TXT = {json.dumps({"genutzt": t("livekalib.js.genutzt"),
                           "katalog": t("livekalib.js.katalog"),
                           "pruefen": t("livekalib.js.pruefen"),
                           "gespeichert": t("livekalib.js.gespeichert"),
                           "fehler": t("livekalib.js.fehler"),
                           "lauf": t("livekalib.js.lauf"),
                           "aus": t("livekalib.js.aus")},
                          ensure_ascii=False)};
const g = document.getElementById("lk-g");
const karten = [];
for (const z of B) {{
  const k = document.createElement("div");
  k.className = "kal-k";
  const gw = (z.e < 0 && z.t < 0) ? ""
    : `${{z.e < 0 ? "?" : z.e.toFixed(2)}} / ${{z.t < 0 ? "?" : z.t.toFixed(2)}}`;
  const dw = (z.det < 0) ? T_TXT.lauf : z.det.toFixed(2);
  const pw = (z.p === undefined || z.p < 0) ? "" : ` &middot; p${{z.p.toFixed(2)}}`;
  k.innerHTML = `<img loading="lazy" src="${{z.src}}">`
    + `<div class="kal-w">${{dw}}${{gw ? " &middot; " + gw : ""}}${{pw}}</div>`;
  g.appendChild(k); karten.push([z, k]);
}}
/* Reglerskalen FEST (Lehre der Lernlauf-Kalibrierseite, Widerleger 30.08.):
   eine datenabhaengige Skala klemmte die geltende Schwelle ins Fenster des
   gerade sichtbaren Materials — die Seite zeigte dann eine andere Zahl, als
   wirklich galt, und der Uebernehmen-Klick schrieb sie auch so. Die Spannen
   hier sind exakt die, die der Server annimmt. */
function wert(id, stellen) {{
  const v = parseFloat(document.getElementById(id).value);
  const f = Math.pow(10, stellen);
  return Math.round((isNaN(v) ? 0 : v) * f) / f;
}}
function setz(id, v, lo, hi) {{
  const z = Number(v);
  document.getElementById(id).value = Math.min(Math.max(isNaN(z) ? lo : z, lo), hi);
}}
function malen() {{
  const d = wert("lk-det", 2), e = wert("lk-e", 3), tt = wert("lk-t", 3);
  const ke = wert("lk-ke", 3), kt = wert("lk-kt", 3), pp = wert("lk-p", 2);
  const kd = wert("lk-kd", 2), kp = wert("lk-kp", 2);
  const kn = wert("lk-kn", 1);   /* .517: nur noch der Katalog-Norm-Regler */
  const kk = wert("lk-k", 0), kkk = wert("lk-kk", 0);
  const pt = wert("lk-pt", 3);
  document.getElementById("lk-det-wert").textContent = d.toFixed(2);
  document.getElementById("lk-e-wert").textContent = e.toFixed(3);
  document.getElementById("lk-t-wert").textContent = tt.toFixed(3);
  document.getElementById("lk-p-wert").textContent = pp.toFixed(2);
  document.getElementById("lk-ke-wert").textContent = ke.toFixed(3);
  document.getElementById("lk-kt-wert").textContent = kt.toFixed(3);
  document.getElementById("lk-kd-wert").textContent = kd.toFixed(2);
  document.getElementById("lk-kp-wert").textContent = kp.toFixed(2);
  /* .520 (User-Entscheid 10.09.): der Norm-Regler hat KEINE Aus-Stellung
     mehr — sein linker Anschlag ist 18 (core.guete.NORM_REGLER_MIN), die 0 ist
     von dieser Seite aus nicht mehr einstellbar. Der frueher hier stehende
     aus-Zweig (`kn > 0 ? … : T_TXT.aus`) ist deshalb raus: er waere ein Wort
     fuer einen Zustand, den der Regler nicht mehr erzeugen kann, und tote
     Zweige lassen die Seite ehrlicher aussehen, als sie ist. Die zwei
     KANTEN-Regler darunter behalten ihre 0 und damit ihren aus-Zweig. */
  document.getElementById("lk-kn-wert").textContent = kn.toFixed(1);
  /* Kante: ganze Pixel, und 0 heisst auch hier AUS. */
  document.getElementById("lk-k-wert").textContent =
    kk > 0 ? kk + " px" : T_TXT.aus;
  document.getElementById("lk-kk-wert").textContent =
    kkk > 0 ? kkk + " px" : T_TXT.aus;
  document.getElementById("lk-pt-wert").textContent = pt.toFixed(3);
  let drin = 0, kdrin = 0, pdrin = 0;
  for (const [z, k] of karten) {{
    /* UND-Logik wie auf der Lernlauf-Seite. Ein NICHT gemessener Wert (-1)
       laesst seine Latte passieren — sonst blendete ein fehlendes Guete-Modell
       (oder das fehlende det der Lernlauf-Bilder) den ganzen Vorrat aus und
       der Nutzer saehe eine leere Wand. */
    /* Die Pose-Latte urteilt nach DERSELBEN Regel: ein Bild ohne Kopf-Score
       (Feld fehlt = Bestand/Live-Weg, oder -1 = nicht gemessen) passiert sie.
       Sonst blendete der erste Zug am Regler den gesamten Alt-Bestand aus,
       ohne dass an ihm je etwas gemessen wurde. */
    /* .517: die Norm steht in dieser Zeile NICHT mehr — das Erkennen-Register
       hat keinen Norm-Regler mehr, und ein Sieb ohne Regler waere ein
       unsichtbares Urteil. Im Katalog-Zaehler darunter urteilt sie weiter. */
    const ok = (z.det < 0 || z.det >= d) && (z.e < 0 || z.e >= e)
               && (z.t < 0 || z.t >= tt)
               && (z.p === undefined || z.p < 0 || z.p >= pp)
               && (z.k === undefined || z.k < 0 || z.k >= kk);
    /* Die KATALOG-Latte urteilt getrennt und wird getrennt gezeigt: ein Bild
       kann fuer Anzeige/Vorrat taugen und trotzdem keine Referenz werden
       duerfen. Beides in einer Farbe waere eine Luege ueber zwei Latten. */
    /* .514: die Katalog-Latte urteilt seit dem Ein-Sieb-Zug auf VIER Achsen.
       Die zwei neuen folgen derselben fail-open-Regel wie die anderen: was
       nicht gemessen wurde (-1, oder das fehlende det der Lernlauf-Bilder),
       passiert. WICHTIG, damit die Seite nicht luegt: das LERN-SIEB im
       Worker ist an derselben Stelle fail-CLOSED (ein nicht messbarer Wert
       bei aktiver Latte verwirft den Fund). Die Galerie zeigt Bestands-
       material ohne Messwerte, das Sieb sieht frisch Gemessenes — deshalb
       ist die Zahl hier ein Anhalt, keine Vorhersage. */
    const kok = (z.e < 0 || z.e >= ke) && (z.t < 0 || z.t >= kt)
                && (z.det < 0 || z.det >= kd)
                && (z.p === undefined || z.p < 0 || z.p >= kp)
                && (z.n === undefined || z.n < 0 || z.n >= kn)
                && (z.k === undefined || z.k < 0 || z.k >= kkk);
    /* Die PRUEFER-Latte zaehlt, was sie MARKIEREN wuerde — nicht, was
       durchkaeme. Das ist die Frage, die hier zaehlt: der Nutzer stellt eine
       Latte ein, an der Bilder AUFFALLEN sollen, nicht eine, die sie
       durchlaesst. Ungemessenes (-1) faellt nie auf (fail-open wie ueberall). */
    const praus = (pt > 0 && z.t >= 0 && z.t < pt);
    k.classList.toggle("raus", !ok);
    k.classList.toggle("katraus", ok && !kok);
    if (ok) drin++;
    if (kok) kdrin++;
    if (praus) pdrin++;
  }}
  document.getElementById("lk-stand").textContent =
    T_TXT.genutzt.replace("{{n}}", drin).replace("{{gesamt}}", B.length);
  document.getElementById("lk-kstand").textContent =
    T_TXT.katalog.replace("{{n}}", kdrin).replace("{{gesamt}}", B.length);
  document.getElementById("lk-pstand").textContent =
    T_TXT.pruefen.replace("{{n}}", pdrin).replace("{{gesamt}}", B.length);
}}
for (const id of ["lk-det", "lk-e", "lk-t", "lk-p", "lk-k", "lk-ke",
                  "lk-kt", "lk-kd", "lk-kp", "lk-kn", "lk-kk", "lk-pt"])
  document.getElementById(id).oninput = malen;
function registerZeigen(welches) {{
  const G = {{e: "lk-reg-e", l: "lk-reg-l", p: "lk-reg-p"}};
  for (const k in G) {{
    document.getElementById(G[k]).style.display = (k === welches) ? "" : "none";
    document.getElementById("lk-tab-" + k).classList.toggle("on", k === welches);
  }}
}}
document.getElementById("lk-tab-e").onclick = () => registerZeigen("e");
document.getElementById("lk-tab-l").onclick = () => registerZeigen("l");
document.getElementById("lk-tab-p").onclick = () => registerZeigen("p");
document.getElementById("lk-std").onclick = () => {{
  setz("lk-det", STD.det, 0.40, 0.60); setz("lk-e", STD.e, 0, 1);
  setz("lk-t", STD.t, 0, 1);
  /* Pose-Vorgabe = AUS. Es gibt keinen Werks-Wert dafuer, solange die Latte
     nichts siebt — "Vorgaben" heisst hier also: der Regler stoert nicht. */
  setz("lk-p", {_POSE_LO}, {_POSE_LO}, {_POSE_HI});
  setz("lk-ke", KSTD.e === null ? {_KAT_LO_E} : KSTD.e, {_KAT_LO_E}, 1);
  setz("lk-kt", KSTD.t === null ? {_KAT_LO_T} : KSTD.t, {_KAT_LO_T}, 1);
  setz("lk-kd", KSTD.det === null ? {_DET_LO} : KSTD.det, {_DET_LO}, {_DET_HI});
  setz("lk-kp", KSTD.p === null ? {_POSE_LO} : KSTD.p, {_POSE_LO}, {_POSE_HI});
  /* Norm-Vorgabe: nur noch im Katalog-Register, seit .517 der Werkswert 20
     (core.guete.norm_werk). Er kommt vom Server durch (KSTD), nie als Literal
     hier. Das Erkennen-Register hat keinen Norm-Regler mehr — dort wird die
     Norm nicht gemessen, es gibt nichts vorzugeben. Die Klemm-Spanne ist seit
     .520 18..35 (NORM_REGLER_MIN..NORM_MAX); der Werkswert 20 liegt darin, der
     Vorgaben-Knopf zeigt ihn also unveraendert. */
  setz("lk-kn", KSTD.n === null ? {_NORM_LO} : KSTD.n, {_NORM_LO}, {_NORM_HI});
  /* Kanten-Vorgabe ist NICHT die Aus-Stellung, sondern der Werkswert 25 px
     (core.guete.KANTE_WERK) — die Zahl, die der Stimmweg seit .400 nutzt.
     Sie kommt vom Server durch (ESTD/KSTD), nie als Literal hier. */
  setz("lk-k", ESTD.k === null ? 0 : ESTD.k, {_KANTE_LO}, {_KANTE_HI});
  setz("lk-kk", KSTD.k === null ? 0 : KSTD.k, {_KANTE_LO}, {_KANTE_HI});
  setz("lk-pt", PSTD.t === null ? 0 : PSTD.t, 0, 1); malen();
}};
document.getElementById("lk-save").onclick = async () => {{
  const m = document.getElementById("lk-msg");
  try {{
    /* Derselbe Schreibweg wie jede andere Waechter-Aenderung (/live_speichern,
       Riegel + Audit dort). Nur die Felder DIESER Regler gehen mit — alles
       andere behaelt der Server (live_speichern: fehlendes Feld heisst
       behalten). */
    const r = await fetch("/live_speichern", {{method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify({{kamera: KAM, det_min: wert("lk-det", 2),
                            guete_e_min: wert("lk-e", 3),
                            guete_t_min: wert("lk-t", 3),
                            katalog_e_min: wert("lk-ke", 3),
                            katalog_t_min: wert("lk-kt", 3),
                            katalog_det_min: wert("lk-kd", 2),
                            katalog_pose_min: wert("lk-kp", 2),
                            katalog_norm_min: wert("lk-kn", 1),
                            /* .517: `norm_min` (Erkennen-Register) geht NICHT
                               mehr mit — die Seite hat dafuer keinen Regler
                               mehr, und ein fehlendes Feld heisst bei
                               live_speichern „unveraendert behalten". Ein
                               gespeicherter Wert bleibt damit stehen. */
                            katalog_kante_min: wert("lk-kk", 0),
                            kante_min: wert("lk-k", 0),
                            pruef_t_min: wert("lk-pt", 3),
                            pose_min: wert("lk-p", 2)}})}});
    const d = await r.json().catch(() => ({{}}));
    m.textContent = r.ok ? T_TXT.gespeichert : (d.msg || T_TXT.fehler);
  }} catch (e) {{
    m.textContent = T_TXT.fehler;   /* abgerissene Verbindung ist kein stiller Erfolg */
  }}
}};
setz("lk-det", AKT.det, 0.40, 0.60); setz("lk-e", AKT.e, 0, 1);
setz("lk-t", AKT.t, 0, 1);
setz("lk-p", AKT.p, {_POSE_LO}, {_POSE_HI});
setz("lk-ke", KAKT.e === null ? {_KAT_LO_E} : KAKT.e, {_KAT_LO_E}, 1);
setz("lk-kt", KAKT.t === null ? {_KAT_LO_T} : KAKT.t, {_KAT_LO_T}, 1);
setz("lk-kd", KAKT.det === null ? {_DET_LO} : KAKT.det, {_DET_LO}, {_DET_HI});
setz("lk-kp", KAKT.p === null ? {_POSE_LO} : KAKT.p, {_POSE_LO}, {_POSE_HI});
/* .520, BENANNTE KANTE der neuen Untergrenze: `setz` klemmt nur die ANZEIGE.
   Ein GESPEICHERTER Wert unter 18 (mit einem aelteren Stand am Regler auf 0
   gestellt, oder von Hand/ueber die API in `katalog_norm_min` geschrieben —
   die Store-Spanne beginnt unveraendert bei 0) bleibt im Store stehen, und das
   SIEB urteilt weiter mit ihm. Der Regler zeigt dann 18,0; wer auf dieser
   Seite „Uebernehmen" drueckt, schreibt diese 18 und hebt den Wert damit
   an — sichtbar, nicht still. Ohne jeden gesetzten Wert steht der Regler am
   linken Anschlag; dass die Katalog-Latte dann gar nicht gesetzt ist, sagt die
   Quellen-Zeile ueber den Reglern (`_quelle_wort` -> "aus"). */
setz("lk-kn", KAKT.n === null ? {_NORM_LO} : KAKT.n, {_NORM_LO}, {_NORM_HI});
setz("lk-k", AKT.k, {_KANTE_LO}, {_KANTE_HI});
setz("lk-kk", KAKT.k === null ? 0 : KAKT.k, {_KANTE_LO}, {_KANTE_HI});
/* Die geltende Pruefer-Latte (Kamera-Wert oder globaler Rueckfall) steht am
   Regler; ist gar keine gesetzt, zeigt er 0 = "diese Achse urteilt nicht". */
setz("lk-pt", PAKT.t === null ? 0 : PAKT.t, 0, 1);
malen();
</script>"""
