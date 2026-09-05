"""core/einspielen — Testbett-Einspielung: EIN Szenario gezielt durch die
Erkennung EINER Kamera schicken (.416, User-Go 03.09.2026).

WOFUER: Beim Nachstellen eines fremden Systems (Klon-Testbett) muss man ein
BESTIMMTES Ereignis unter einem BESTIMMTEN Kameranamen durch die Erkennung
schicken koennen — ohne beim Original etwas auszuloesen und ohne einen
zweiten Erkennungspfad zu bauen. Quelle ist wahlweise ein echtes Event der
VERBUNDENEN Frigate (on demand statt Dauer-Poll, schont die Leitung) oder ein
Clip, der schon unter data_dir liegt.

DER TRICK, DER DEN EINGRIFF KLEIN HAELT (Muster core/dateiquelle): eine
Event-ID mit dem Praefix `einspiel-` hat drueben KEINE Entsprechung. Genau
zwei Haken lesen dieses Praefix:

  A  verifyd.Service.process()   — die Metadaten kommen aus
     <data_dir>/einspielen/<eid>.json statt aus /api/events/<id>;
  B  core.frames.clip_holen()    — der Clip kommt aus
     <data_dir>/einspielen/<eid>.mp4 statt aus einem Frigate-GET.

Alles danach ist der NORMALE Weg: Event-Queue, Kamera-/Zonen-Filter,
live_only-Uebersprung, Worker-Analyse, Akte und Today unter der eingesetzten
Kamera. Es entsteht KEIN zweiter Erkennungspfad — genau das ist der Zweck.

GRENZEN, ehrlich:
- Der Ordner <data_dir>/einspielen/ wird NICHT automatisch geraeumt. Die
  Clip-Retention raeumt <data_dir>/clips, nicht diese Vorlagen; wer aufraeumt,
  loescht dort von Hand (oder ueber den Support-Lesebaum sichtbar).
- Die Metadaten sind eine DATEI. Wer sie von Hand editiert, aendert damit,
  was die Erkennung sieht. meta_lesen() liest deshalb streng (dict, camera
  als nicht-leere Zeichenkette) und liefert sonst None — der Haken bricht
  dann LAUT mit einer Logzeile ab, statt mit halben Angaben weiterzulaufen.
- Geschrieben wird ausschliesslich unter data_dir. Richtung Frigate ist
  dieser Weg rein LESEND (ein GET auf /api/events/<id> und der normale
  Clip-Zug) — die Instanz drueben merkt nichts davon.
"""
import json
import os
import re
import secrets
import shutil
import time

from core import atomar as _atomar
# Dieselbe Kamera-Namensregel und derselbe ffprobe-Griff wie bei der
# Datei-Einspeisung — kein zweites verstreutes Literal, keine zweite
# Messstelle (CLAUDE.md: zentrale Quelle statt Streu-Literal).
from core.dateiquelle import KAMERA_RE, _ffprobe

PRAEFIX = "einspiel-"
ORDNER = "einspielen"
# Die eid landet in Dateinamen und muss zu registry.EID_RE ([\w.\-]+) passen,
# damit ALLE Routen (Event-Seite, Crops, Logs) sie tragen.
EID_RE = re.compile(r"^einspiel-[\w.\-]{1,72}$")
DAUER_FALLBACK_S = 60.0    # ohne lesbare ffprobe-Dauer: eine Minute annehmen
VORLAUF_S = 25.0           # das eingespielte Ereignis liegt schon hinter uns
TOP_SCORE = 0.9            # ueber jeder ueblichen no_person-Latte
LABEL = "person"
# FENSTER-WEG (User 03.09. abends: "ab einem Zeitfenster, zum Beispiel 8 Uhr,
# die naechsten 5 Personen-Events von dieser Kamera"): bewusst GEDECKELT,
# damit ein Support-Aufruf nie einen ganzen Tag Events in die Queue kippt.
FENSTER_MAX_DEFAULT = 5    # "die naechsten 5" — der genannte Normalfall
FENSTER_DECKEL = 20        # WERKS-Obergrenze je Aufruf (s. deckel_aus_config)
FENSTER_SUCHLIMIT = 100    # wie viele Events EINE Frigate-Abfrage liefert (Seite)
# .505 (05.09.2026, bauplan_0505 E1): die erlaubten Felder des Aufrufs an EINER
# Stelle. Anlass ist der Feldfall vom 04.09.: der Aufruf trug `anzahl` statt
# `max`, der Handler ignorierte das Feld STILL und der Werkswert 5 griff — der
# Bediener hielt einen Nachlauf ueber eine Stunde fuer gefahren, es waren fuenf
# Ereignisse. Ein unbekanntes Feld ist ab jetzt ein Fehler mit Namensnennung.
FELDER = ("kamera", "start", "ende", "max", "richtung", "event", "clip")
# Fensterweg: welches ENDE des Fensters genommen wird (User 05.09.: "alle
# Ereignisse ab Zeitpunkt X einer Kamera; oder rueckwaerts ab X bis Y").
RICHTUNGEN = ("vor", "zurueck")
RICHTUNG_DEFAULT = "vor"
# Der Deckel ist seit .503 STELLBAR (User-Auftrag 04.09.: einen Nachlauf ueber eine
# Stunde oder einen Tag fahren koennen, um zu sehen, ob alles sauber durchlaeuft).
# Er bleibt trotzdem ein Deckel: der Werkswert 20 gilt weiter fuer jede Anlage, die
# nichts einstellt, und eine Anlage, die ihn hebt, tut das bewusst. Grund fuer den
# Deckel ueberhaupt: ein einziger Support-Aufruf darf nie einen ganzen Tag Events in
# die Queue kippen — auf einer Anlage MIT Rueckstand konkurriert das mit dem Aufholen.
# .505 (05.09.2026): 2000 -> 5000. Der Betreiber fuhr am 04.09. einen Nachlauf
# ueber einen ganzen Vormittag; 2000 war dafuer zu wenig. Der Deckel bleibt ein
# Deckel (Werkswert 20), er darf nur weiter gehoben werden. Die Zwillingszahl
# steht in verifyd.CONFIG_WHITELIST["einspiel_deckel"] — beide gehoeren zusammen.
FENSTER_DECKEL_MAX = 5000  # was der Config-Wert hoechstens annehmen darf
# .505 E4 (05.09.2026, Widerleger E1+E2 G2/N5): Frigate vergleicht `before` und
# `after` EXKLUSIV — gemessen an der 0.17.2-Instanz im Feld: `start_time <
# before` bzw. `start_time > after`. Beides hat Folgen, und beide Male ist die
# Antwort dieselbe Bruchsekunde:
#   - blaettern: `before = aeltester start_time` laesst jedes ZWILLINGS-Ereignis
#     mit exakt demselben Zeitstempel aus, das auf der naechsten Seite laege
#     (85 von 5000 Ereignissen teilen dort ihren start_time; die Simulation
#     verlor 1 von 5000). Deshalb `+ EPS_S`.
#   - Untergrenze: "ab 09:00" soll das Ereignis um 09:00:00.000 EINSCHLIESSEN,
#     `after` schliesst es aber aus. Deshalb wird `start - EPS_S` gesendet.
# 1e-6 s liegt unter jeder Frigate-Zeitaufloesung und ueber der float-Genauigkeit
# einer Epoch-Sekunde (~2e-7 bei 1,76e9) — klein genug, um nie ein fremdes
# Ereignis einzufangen, gross genug, um nicht wegzurunden.
EPS_S = 1e-6


def deckel_aus_config(cfg):
    """Die EINE Aufloesung des Fenster-Deckels: Config vor Werkswert, hart geklemmt.
    Ein zweites `cfg.get("einspiel_deckel")` irgendwo waere genau das Streu-Literal,
    vor dem die QS-Ebenen-Regel warnt."""
    try:
        w = int((cfg or {}).get("einspiel_deckel") or FENSTER_DECKEL)
    except (TypeError, ValueError):
        w = FENSTER_DECKEL
    return max(1, min(w, FENSTER_DECKEL_MAX))


# --- Fensterweg (.505, 05.09.2026 — bauplan_0505 E1) -------------------------
# Die Zuege des Fensterwegs stehen hier als REINE Funktionen, damit die
# Probe (tools/proben/s11_e1_fenster.py) sie ohne HTTP-Server und ohne Frigate
# fahren kann; der Handler in verifyd.py ist nur noch der Mantel darum.

def felder_pruefen(body):
    """Traegt der Aufruf ein Feld, das dieser Endpunkt nicht kennt?
    -> Fehlertext (mit Namensnennung) oder None.

    Der Feldfall vom 04.09.2026: `{"kamera": …, "start": …, "anzahl": 300}` —
    `anzahl` gibt es nicht, der Handler ignorierte es still, und der Werkswert
    `max`=5 griff. Ein still ignoriertes Feld ist die schlimmste Sorte Fehler,
    weil der Aufrufer eine Antwort mit ok:true bekommt und trotzdem etwas
    anderes passiert ist, als er wollte."""
    unbekannt = sorted(str(k) for k in (body or {}) if k not in FELDER)
    if not unbekannt:
        return None
    # .505 E4 (05.09.2026, Widerleger E1+E2 Notiz 8): ALLE Fremdfelder nennen,
    # nicht nur das erste. Wer zwei Felder falsch schreibt, korrigiert sonst
    # eines, schickt neu und bekommt denselben Fehler noch einmal.
    namen = ", ".join(f"'{k}'" for k in unbekannt)
    return (f"unknown {'field' if len(unbekannt) == 1 else 'fields'} {namen}; "
            f"known: " + ", ".join(FELDER))


def richtung_pruefen(wert):
    """-> (richtung, fehlertext|None). Fehlt die Angabe, gilt RICHTUNG_DEFAULT."""
    r = str(wert or RICHTUNG_DEFAULT)
    if r not in RICHTUNGEN:
        return RICHTUNG_DEFAULT, (f"unknown richtung '{r}'; known: "
                                  + ", ".join(RICHTUNGEN))
    return r, None


def deckel_klemmen(wunsch, deckel):
    """-> (wirksames max, geklemmt_auf|None). `geklemmt_auf` ist gesetzt, wenn
    der Wunsch groesser war als der Deckel — der Aufrufer bekommt das in der
    ANTWORT gesagt, nicht nur im Log: wer 5000 bestellt und 1000 bekommt, muss
    das sehen, sonst haelt er einen halben Nachlauf fuer einen ganzen."""
    d = max(1, int(deckel))
    w = int(wunsch)
    return max(1, min(w, d)), (d if w > d else None)


def seiten_deckel(deckel, seitengroesse=FENSTER_SUCHLIMIT):
    """Wie viele Frigate-Seiten ein Aufruf hoechstens blaettern darf:
    ceil(deckel / seitengroesse) + 1. Die eine Extraseite ist die, auf der das
    Fenster erschoepft ist (len < seitengroesse) — ohne sie waere bei einem
    exakt aufgehenden Fenster nie klar, ob noch etwas kommt."""
    g = max(1, int(seitengroesse))
    return max(1, -(-max(1, int(deckel)) // g) + 1)


# .505 E4 (05.09.2026, Widerleger E1+E2 BLOCKIEREND B1): DER Seiten-Deckel haengt
# an der FENSTERGROESSE, nicht am `einspiel_deckel`. Der Bauplan hatte ihn an den
# Config-Wert gehaengt; beim Werkswert 20 waren das 2 Seiten = 200 Ereignisse, und
# ein Fenster mit mehr Ereignissen wurde STILL auf die 200 NEUESTEN gekappt —
# gemessen: "ab 24.08." lieferte den 04.09. 16:56 statt den 24.08. 17:24, und die
# Antwort sagte nichts davon. Das war genau der alte Fehler mit hoeherer Schwelle.
# `max` begrenzt seither nur noch die AUSWAHL, nie das Blaettern; gestoppt wird
# durch eine kurze Seite oder die Untergrenze. Der Deckel hier ist nur noch die
# Not-Bremse gegen eine Endlosschleife und traegt den groesstmoeglichen Fall
# (5000 / 100 + 1 = 51 Seiten); wird er wirklich erreicht, sagt die Antwort das
# mit `fenster_unvollstaendig`.
SEITEN_DECKEL = seiten_deckel(FENSTER_DECKEL_MAX)      # 51


def max_pruefen(wert):
    """Das `max` des Aufrufs pruefen -> (wirksames max, fehlertext|None).

    .505 E4 (05.09.2026, Widerleger E1+E2 Notiz 8): `max: 0` fiel bis hierher
    durch die `or`-Falle STILL auf den Werkswert 5 und `max: -5` auf 1 — der
    Bediener bekam ok:true und fuenf Ereignisse, wo er null bzw. eine Ansage
    erwartet hatte. Eine unsinnige Zahl ist ab jetzt ein Fehler mit Nennung.

    N1 (05.09.2026, Widerleger E4 Notiz 8): zwei Reste derselben Klasse.
    `true` ist in Python ein int und kam als `max: 1` durch (JSON-Bediener
    schicken so etwas) — ein Wahrheitswert ist hier keine Anzahl und wird
    abgewiesen. Und `int(float('inf'))`/`int(1e400)` wirft `OverflowError`, den
    `(TypeError, ValueError)` nicht faengt: der Fehler fiel in das Sammel-except
    des Handlers und der Bediener bekam 400 mit einem internen Text statt der
    Ansage, was an seiner Zahl falsch war."""
    if wert is None:
        return FENSTER_MAX_DEFAULT, None
    if isinstance(wert, bool):
        return FENSTER_MAX_DEFAULT, "max must be a number, not a boolean"
    try:
        n = int(wert)
    except (TypeError, ValueError, OverflowError):
        return FENSTER_MAX_DEFAULT, "bad window (start/ende/max numeric)"
    if n < 1:
        return FENSTER_MAX_DEFAULT, "max must be >= 1"
    return n, None


def fenster_sammeln(api_fn, kamera, start, ende, seitengroesse=FENSTER_SUCHLIMIT,
                    max_seiten=None, genug=None, log=None):
    """Alle Personen-Ereignisse eines Zeitfensters holen
    -> (events, seiten, unvollstaendig).

    `api_fn(pfad) -> Liste` ist injiziert (der Handler reicht `api(cfg, …)`
    herein, die Probe eine Attrappe). Die Rueckgabe ist AUFSTEIGEND nach
    start_time sortiert und je Ereignis-ID entdoppelt. `unvollstaendig` ist True,
    wenn der Seiten-Deckel gegriffen hat, das Fenster also MEHR enthaelt als hier
    steht — der Aufrufer sagt das in seiner Antwort (nie stillschweigend kappen).

    WARUM GEBLAETTERT WIRD (Feldfall 04.09.2026): Frigate liefert die NEUESTEN
    zuerst und hoechstens `limit` Stueck. Die alte Fassung holte EINE Seite und
    sortierte DANACH aufsteigend — "ab 09:00 die naechsten 100" lieferte damit
    die 100 neuesten des Tages, angezeigt ab 16:33. Richtig ist: rueckwaerts
    blaettern (`before` = aeltester start_time der letzten Seite), bis das
    Fenster erschoepft ist (Seite kuerzer als `limit`), `before` die Untergrenze
    erreicht oder der Seiten-Deckel greift; erst dann sortieren.

    Zeitstempel gehen mit Nachkommastellen in die Abfrage (`.6f`). Sekunden-
    Rundung war hier NICHT harmlos: `before` abgerundet ueberspringt jedes
    Ereignis in derselben Sekunde, aufgerundet liefert dieselbe Seite noch
    einmal und die Schleife kaeme nicht von der Stelle.

    DIE DREI ABBRUECHE (.505 E4, Widerleger E1+E2 G2 — beide Grenzen sind
    EXKLUSIV, s. EPS_S):
      1. kurze Seite (`len < limit`) = Fenster erschoepft,
      2. `before` unter der Untergrenze `start`,
      3. eine volle Seite ohne EINE einzige neue ID. Das ist die Pathologie, die
         `before = aeltestes + EPS_S` sonst offen liesse: eine ganze Seite mit
         demselben Zeitstempel wuerde bis zum Seiten-Deckel immer wieder geholt.
         Gezaehlt werden dabei ALLE gelieferten IDs, auch die, die der
         Kamera-Nachfilter verwirft — sonst braeche eine Instanz, die `cameras=`
         ignoriert, die Schleife nach der ersten Seite ab.
    Dazu der Seiten-Deckel als Not-Bremse (SEITEN_DECKEL).

    `unvollstaendig` setzen der Seiten-Deckel UND Abbruch 3 (N1, 05.09.2026,
    Widerleger E4 Punkt 1): Abbruch 3 loggte bis .505 nur und lieferte
    `ok:true, gefunden:100` ohne `fenster_unvollstaendig` — ein STILLER Verlust
    mit Erfolgsmeldung. Gemessen: eine Seite voller identischer Zeitstempel
    ergab gefunden=100 von 500. Derselbe Abbruch trifft jede Instanz bzw. jeden
    Proxy, der `before` ignoriert (Seite 2 = Seite 1 -> Ende nach einer Seite).
    Beide Male gilt genau das, was `unvollstaendig` sagt: das Fenster enthaelt
    mehr, als hier steht. Abbruch 1 (kurze Seite) und 2 (Untergrenze erreicht)
    sind vollstaendig und setzen es nicht.

    `genug` (.505 E4, Widerleger E1+E2 Notiz 4): sobald so viele Ereignisse
    beisammen sind, wird abgebrochen. Das nimmt NUR `richtung=zurueck` — dort
    stehen die gesuchten (die juengsten) auf Seite 1, und ohne den Abbruch
    blaetterte ein "die letzten 20" das ganze Fenster durch (50 Abfragen fuer
    20 Ereignisse). Bei `vor` MUSS das ganze Fenster geblaettert werden, die
    aeltesten stehen ja am anderen Ende. `gefunden` heisst deshalb bei `zurueck`
    "bis zum Abbruch gesehen", nicht "alle im Fenster".

    Ohne `kamera` gilt das Fenster fuer ALLE Kameras — dann faellt sowohl der
    `cameras=`-Parameter als auch der Nachfilter weg. MIT Kamera bleibt der
    Nachfilter: eine Instanz, die `cameras=` ignoriert, darf keine fremden
    Kameras in die Queue spuelen.

    `start` darf None sein (`richtung=zurueck` ohne Untergrenze, User 05.09.:
    "rueckwaerts ab X bis Y oder Anzahl"): dann faellt `after` aus der Abfrage
    und die Untergrenze ist allein der Seiten-Deckel."""
    if max_seiten is None:
        max_seiten = SEITEN_DECKEL
    max_seiten = max(1, int(max_seiten))
    g = max(1, int(seitengroesse))
    t0 = None if start is None else float(start)
    before = None if ende is None else float(ende)
    gesehen, treffer, seiten = set(), [], 0
    unvollstaendig = False

    def _sagen(zeile):
        if log:
            log(zeile)

    while True:
        if seiten >= max_seiten:
            unvollstaendig = True
            _sagen(f"einspielen: page limit of {max_seiten} pages reached after "
                   f"{len(treffer)} event(s) — the window holds more; the answer "
                   f"says fenster_unvollstaendig")
            break
        # `after` exklusiv (gemessen): `start - EPS_S` sorgt dafuer, dass ein
        # Ereignis EXAKT auf `start` im Fenster liegt ("ab 09:00" schliesst
        # 09:00:00.000 ein).
        q = (f"/api/events?labels={LABEL}&has_clip=1"
             f"&limit={g}&include_thumbnails=0")
        if t0 is not None:
            q += f"&after={t0 - EPS_S:.6f}"
        if kamera:
            q += f"&cameras={kamera}"
        if before is not None:
            q += f"&before={before:.6f}"
        seite = [e for e in (api_fn(q) or [])
                 if isinstance(e, dict) and e.get("id")]
        seiten += 1
        neue_ids = 0
        for e in seite:
            eid = str(e["id"])
            if eid in gesehen:
                continue                 # Randereignis der vorigen Seite
            gesehen.add(eid)
            neue_ids += 1
            if kamera and str(e.get("camera")) != str(kamera):
                continue
            treffer.append(e)
        if genug is not None and len(treffer) >= int(genug):
            break                        # richtung=zurueck: die Juengsten sind da
        if len(seite) < g:
            break                        # Fenster erschoepft
        if not neue_ids:
            # N1 (05.09.2026, Widerleger E4 Punkt 1): das Fenster ist hier NICHT
            # erschoepft, die Schleife kommt nur nicht weiter — also dieselbe
            # Auskunft wie beim Seiten-Deckel, sonst meldet der Handler ok:true
            # ueber eine stillschweigend gekappte Menge.
            unvollstaendig = True
            _sagen(f"einspielen: page {seiten} brought no new event id "
                   f"(identical timestamps or the instance ignores 'before') — "
                   f"stopping after {len(treffer)} event(s); the window holds "
                   f"more, the answer says fenster_unvollstaendig")
            break
        aeltestes = min(float(e.get("start_time") or 0) for e in seite)
        # +EPS_S: `before` ist exklusiv, `aeltestes` selbst wuerde jeden
        # Zeitstempel-Zwilling der naechsten Seite verschlucken (G2).
        neu_before = aeltestes + EPS_S
        if before is not None and neu_before >= before:
            break                        # kein Fortschritt -> nie eine Endlosschleife
        before = neu_before
        if t0 is not None and before <= t0:
            break                        # Untergrenze des Fensters erreicht
    treffer.sort(key=lambda e: float(e.get("start_time") or 0))
    return treffer, seiten, unvollstaendig


def auswahl(events, n, richtung=RICHTUNG_DEFAULT):
    """Aus dem aufsteigend sortierten Fenster die `n` Ereignisse waehlen, die
    der Aufrufer meint: `vor` = die aeltesten ab `start` (das ist der Nachlauf
    "ab 08:00 weiter"), `zurueck` = die juengsten vor `ende` (das ist "die
    letzten N vor diesem Zeitpunkt"). Beide Male kommt die Auswahl aufsteigend
    zurueck — eingereiht wird immer in der Reihenfolge, in der es passiert ist."""
    k = max(0, int(n))
    if not k:
        return []
    return list(events[-k:]) if richtung == "zurueck" else list(events[:k])


def je_kamera(events):
    """{Kameraname: Anzahl} ueber die AUSGEWAEHLTEN Ereignisse — die Antwort auf
    "was habe ich gerade eingereiht", wenn der Aufruf ohne Kamera lief."""
    z = {}
    for e in events or ():
        k = str((e or {}).get("camera") or "?")
        z[k] = z.get(k, 0) + 1
    return dict(sorted(z.items()))


def ist_einspiel(eid):
    """DIE eine Praefix-Frage. Beide Haken stellen sie hier — ein zweites
    startswith() irgendwo im Code waere genau das Streu-Literal, das der
    K3-Klasse (Erweiterung erreicht nicht alle Stellen) den Weg bahnt."""
    return str(eid or "").startswith(PRAEFIX)


def eid_ok(eid):
    """Taugt diese ID als Dateiname unter data_dir? Verhindert, dass eine
    von aussen gereichte 'einspiel-../..'-ID zu einem Pfad ausserhalb des
    Injektor-Ordners wird."""
    e = str(eid or "")
    return bool(EID_RE.match(e)) and ".." not in e


def neue_eid():
    """`einspiel-<epoch>-<kurz>` — sortierbar nach Zeit, kollisionsfrei
    durch den Zufallsteil (zwei Einspielungen in derselben Sekunde)."""
    return f"{PRAEFIX}{int(time.time())}-{secrets.token_hex(3)}"


def ordner(data_dir):
    return os.path.join(str(data_dir or ""), ORDNER)


def meta_pfad(data_dir, eid):
    """-> Pfad der Metadaten-Datei oder None (unzulaessige ID / kein
    data_dir). None ist fuer den Aufrufer 'gibt es nicht'."""
    if not data_dir or not eid_ok(eid):
        return None
    return os.path.join(ordner(data_dir), f"{eid}.json")


def clip_pfad(data_dir, eid):
    if not data_dir or not eid_ok(eid):
        return None
    return os.path.join(ordner(data_dir), f"{eid}.mp4")


def meta_lesen(data_dir, eid):
    """Injektor-Metadaten lesen -> dict wie ein /api/events/<id>-Objekt,
    oder None. WIRFT NIE: der Haken A sitzt mitten im Event-Weg, ein
    kaputtes Handeditat darf dort keinen Traceback ausloesen, sondern muss
    als 'nichts zu tun' mit Logzeile enden."""
    p = meta_pfad(data_dir, eid)
    if not p:
        return None
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    if not isinstance(d.get("camera"), str) or not d["camera"].strip():
        return None                      # ohne Kamera gibt es keinen Weg
    d["id"] = str(eid)                   # die ID gehoert dem DATEINAMEN,
    return d                             # nie dem (editierbaren) Inhalt


def bereitstellen(quelle, ziel):
    """Eine Videodatei unter `ziel` bereitstellen — HARDLINK, wenn moeglich
    (gleiche Platte, kein zweiter Datenblock), sonst Kopie. Immer ueber eine
    eindeutige tmp-Datei im Zielordner + os.replace: nie ein halbes Video
    unter dem Zielnamen, nie zwei Schreiber auf demselben tmp-Namen
    (core/atomar). Der Hardlink ist hier ungefaehrlich, weil beide Namen nur
    ATOMAR ersetzt und nie in place beschrieben werden."""
    os.makedirs(os.path.dirname(ziel) or ".", exist_ok=True)
    fd, tmp = _atomar.tmp_oeffnen(ziel, suffix=".mp4")
    os.close(fd)
    os.unlink(tmp)                       # link/copyfile brauchen den Namen frei
    try:
        try:
            os.link(quelle, tmp)         # gleicher Datenblock, kein Kopieren
        except OSError:                  # anderes Dateisystem, kein Hardlink
            shutil.copyfile(quelle, tmp)
            os.chmod(tmp, _atomar.MODUS)
        os.replace(tmp, ziel)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return ziel


def ablegen(data_dir, eid, meta, clip_quelle):
    """Metadaten + Clip als Injektor-Vorlage hinterlegen -> (meta_pfad,
    clip_pfad). Der CLIP zuerst, die Metadaten (atomar) zuletzt: so findet
    Haken A nie eine Metadaten-Datei, zu der noch kein Video gehoert."""
    mp, cp = meta_pfad(data_dir, eid), clip_pfad(data_dir, eid)
    if not mp or not cp:
        raise ValueError(f"unzulaessige Einspiel-ID: {eid!r}")
    bereitstellen(clip_quelle, cp)
    _atomar.json_schreiben(mp, meta)
    return mp, cp


def pfad_anker(data_dir, relpfad):
    """Einen vom Aufrufer genannten Clip-Pfad auf eine echte Datei UNTER
    data_dir abbilden (Muster core.support.baum_aufloesen). JEDER Ausbruch
    (fuehrender /, ../, Symlink nach draussen, Ordner statt Datei) endet als
    None; der Aufrufer antwortet darauf mit dem generischen 404 — nie mit
    einem Grund, sonst wird der Endpunkt zum Existenz-Orakel fuers
    Dateisystem."""
    if not data_dir:
        return None
    basis = os.path.realpath(data_dir)
    rel = str(relpfad or "")
    if not rel or rel.startswith("/") or "\x00" in rel:
        return None
    p = os.path.realpath(os.path.join(basis, rel))
    if not (p == basis or p.startswith(basis + os.sep)):
        return None
    return p if os.path.isfile(p) else None


def dauer_s(pfad):
    """Clip-Dauer in Sekunden -> float oder None (unlesbares Video)."""
    try:
        d = (_ffprobe(pfad) or {}).get("dauer_s")
        return float(d) if d else None
    except (TypeError, ValueError):
        return None


def meta_aus_clip(eid, kamera, dauer, jetzt=None):
    """Metadaten fuer einen LOKALEN Clip — so, wie Frigate ein
    Personen-Event beschreiben wuerde. Die Annahmen stehen hier an EINER
    Stelle (der Aufrufer loggt sie):
      label 'person'   — nur Personen-Events gehen diesen Weg,
      top_score 0.9    — ueber jeder ueblichen no_person-Latte,
      zones []         — der Clip gehoert zu keiner Zone der Ziel-Kamera;
                         hat die Kamera einen Zonen-Filter, ueberspringt
                         process() ihn folgerichtig (und sagt es in der Akte),
      sub_label None   — die Erkennung soll SELBST urteilen, nicht eine
                         mitgelieferte Behauptung bestaetigen,
      Zeitachse        — das Ereignis liegt gerade hinter uns:
                         end_time = jetzt - 25 s, start_time = end - Dauer."""
    t = float(jetzt if jetzt is not None else time.time())
    d = float(dauer or DAUER_FALLBACK_S)
    start = t - d - VORLAUF_S
    return {"id": str(eid), "camera": str(kamera), "label": LABEL,
            "sub_label": None, "start_time": start, "end_time": start + d,
            "zones": [], "has_clip": True, "data": {"top_score": TOP_SCORE},
            "quelle": "einspiel"}


def meta_aus_event(ev, eid, kamera):
    """Metadaten eines ECHTEN Frigate-Events unter neuer ID und neuer
    Kamera. Uebernommen wird alles Uebrige unveraendert (Zeitachse, Zonen,
    Scores) — geaendert werden genau drei Dinge, und jede Aenderung hat
    einen Grund:
      id       -> die neue Einspiel-ID (sonst kollidiert sie mit dem
                  Original in processed/Akte),
      camera   -> die Ziel-Kamera (das ist der ganze Zweck),
      sub_label-> None: Frigates Behauptung ueber die Person wird NICHT
                  mitgeschleppt. Sie wuerde sonst den Kamera-/Zonen-Filter
                  der Ziel-Kamera aushebeln (process(): 'not f_label') und
                  das Urteil gegen eine fremde Kamera-Wahrheit stellen."""
    d = dict(ev or {})
    d["id"] = str(eid)
    d["camera"] = str(kamera)
    d["sub_label"] = None
    if isinstance(d.get("data"), dict):
        d["data"] = {k: v for k, v in d["data"].items()
                     if k != "sub_label_score"}
    d["quelle"] = "einspiel"
    return d


def bestand(data_dir):
    """-> (anzahl, bytes) der hinterlegten Vorlagen. Fuer die Logzeile: der
    Ordner waechst mit jeder Einspielung und wird nicht automatisch
    geraeumt — das soll man sehen, nicht erst beim vollen Datentraeger."""
    n, b = 0, 0
    try:
        with os.scandir(ordner(data_dir)) as it:
            for e in it:
                if e.is_file(follow_symlinks=False):
                    n += 1
                    b += e.stat().st_size
    except OSError:
        return 0, 0
    return n, b
