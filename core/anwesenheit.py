"""core/anwesenheit — Anwesenheits-Marken: DIE eine Quelle dafuer, wann eine
Person in welcher Viertelstunde bestaetigt da war (analysen/anwesenheit_konzept.md,
Fassung 2 + User-Entscheide 02.09. ~11:00-11:15; Befunde in
anwesenheit_qs_befunde.md).

Warum ein eigenes Modul: die Frage "war P im Slot S des Tages T da?" stellen
KUENFTIG die Anwesenheitsseite (Z4) und beantworten HEUTE schon zwei Schreiber in
zwei Prozessen — der Dienst (Worker-Urteile, Anlern-Korrekturen, Lauf-Takt) und
die Live-Engine (Auftritte, dort aus zwei Threads). Beide muessen dieselben
Tagesgrenzen, dieselbe Slot-Regel und dieselbe Datei meinen, sonst zeigt die
Seite spaeter etwas anderes als das, was der Klick findet.

DATENMODELL (Konzept §2): Append-Datei je Kalendertag,
<data_dir>/state/anwesenheit/<JJJJ-MM-TT>.jsonl, eine Zeile je Marke:
  {"ts", "bis", "person", "kamera", "quelle", "eid"?}        Personen-Marke
  {"ts", "bis", "kamera", "art": "luecke", "eid"}             Luecken-Marke
  {"ts", "art": "lauf"}                                       Lauf-Marke
Personen- und Luecken-Marken tragen EREIGNISZEIT, nie die Analysezeit
(Rueckstau-Lehre 02.09.: ein um 13 Uhr nachanalysiertes Event von 10:14 faerbt
den 10:00-Slot) und IMMER eine Kamera (User 02.09.: die Seite filtert je
Kamera und je Area, Area = Partition ueber Kameras, loest sich beim Lesen
auf). Die Lauf-Marke ist SYSTEMWEIT (keine Kamera): eine Zeile je 15-min-
Slot, in dem der Dienst lief, geschrieben aus der Sweep-Schleife.

DREI ZUSTAENDE einer Zelle (User-Entscheid 02.09., woertlich: "wenn wir etwas
nicht gemessen haben oder das System das nicht betrachtet hat, dann sollten
wir keine Farbe darstellen, also auch kein Gruen, kein Rot, weil das System
ja nicht lief"):
  rot    = Personen-Marke (gewinnt IMMER, auch ohne Lauf-Marke)
  gruen  = Lauf-Marke, keine Luecke, keine Person ("analysiert, nicht da")
  LEER   = keine Lauf-Marke (vor der Installation, Ausfall, Nachhol-Fenster)
           oder Lauf-Marke mit Luecke ohne Person ("nicht hingesehen")
KEINE VERGANGENHEITSBETRACHTUNG (User 02.09.): die Historie beginnt mit der
Version, die diese Marken schreibt — es gibt keine Migration aus Akte, Archiv
oder Live-Protokoll. Aufbewahrung `anwesenheit_tage` (Config, 30).

APPEND-AUFLAGE (K8): je Marke open(pfad, "a") / write / close — kein
prozess- oder threadweit offener Handle, Zeilen weit unter 4 KB. Die beiden
bestehenden Akten (deckung.jsonl, meldungen.jsonl) haben je EINEN Schreiber und
taugen nicht als Praezedenz; hier schreiben zwei Prozesse und drei Threads.
POSIX-Append kleiner Zeilen ist damit atomar genug, und der Leser dedupliziert
auf (person, zelle) mit Set-Semantik: Live und Worker im selben Slot, mehrere
Kameras, mehrere Auftritte ergeben EINE rote Zelle ("nichts doppelt", User).
Die Gate-Probe (tools/gate/anwesenheit_probe.py) laesst zwei Prozesse
gleichzeitig je 5000 Zeilen anhaengen und zaehlt nach.

SLOT-REGEL (M4, EINE Regel): Tagesgrenzen EXAKT wie auftritte.py:337-344 —
lokale strptime(...).timestamp() und + timedelta(days=1). Slot = floor((ts −
tag0) / 900). Am Umstelltag hat der Tag 92 bzw. 100 Slots; die Leiste zeigt
trotzdem feste 96 ZELLEN: jede Zelle ist eine lokale Uhrzeit (Stunde*4 +
Minute//15), die doppelte Stunde faerbt dieselben vier Zellen, die fehlende
bleibt leer. Das Gate prueft genau das am 29.03. und 25.10.

FEHLER = Log-Zeile + Zaehler (M3), nie ein Ausfall: kein Schreibfehler hier
darf eine Analyse, einen Sweep oder einen Waechter kosten. Deckel je Tages-
datei 20 MB: EINE Log-Zeile je Datei und Prozess, weiter schreiben (Lese-
Deckel dieselbe Groesse, wie systemstat.LESE_DECKEL_B nur das Ende lesen).

Stdlib-only (wie core/systemstat.py): dieses Modul laeuft im Dienst UND in der
Live-Engine, und beide duerfen dafuer nichts Schweres laden."""
import datetime
import json
import math
import os
import re
import threading
import time

from core import atomar as _atomar   # .411: eindeutige tmp beim atomaren Schreiben (stdlib-only)

ORDNER_TEILE = ("state", "anwesenheit")
FENSTER_DATEI = "fenster.json"    # Tagesfenster, einmal je Kalendertag (M6)
TAG_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl$")
SLOT_S = 900
ZELLEN_JE_TAG = 96
DECKEL_B = 20 * 1024 * 1024
LESE_DECKEL_B = DECKEL_B
# Eine Marke ist ein Auftritt, kein Kalender: laenger als einen Tag gibt es
# nicht — eine kaputte Endzeit (Jahr 2038, 0) darf keine Tausend Tagesdateien
# anlegen. Geklemmt wird LAUT (Log-Zeile), nie still.
SPANNE_MAX_S = 24 * 3600
# Deckungs-Vertrag der Quellen: der Renderer (Z4) und die Tooltips kennen genau
# diese Worte; eine dritte Quelle traegt sich hier ein, nicht in einem Literal.
QUELLEN = ("worker", "live")
ART_LUECKE = "luecke"
ART_LAUF = "lauf"

# Tagesfenster (Konzept §4, Fassung 2 gemessen): 2.–98. Perzentil der
# Marken-Uhrzeiten ueber die letzten 14 Kalendertage AB HEUTE (nicht ab dem
# angezeigten Tag — sonst wechselt die Geometrie beim Blaettern, M6), auf volle
# Stunden nach aussen, min 8 h, max 16 h (bei mehr wird abends gekappt: der
# Morgenbeginn ist der Schichtbeginn). Unter 20 Marken gilt der Werkswert
# 07–20 (an unseren 650 Marken gemessen: 07–20). Min/Max waere falsch: eine
# einzige Nachtsichtung riss das Fenster im Mockup auf 00–21.
FENSTER_TAGE = 14
FENSTER_MIN_MARKEN = 20
FENSTER_MIN_H = 8
FENSTER_MAX_H = 16
FENSTER_PERZENTILE = (2, 98)
WERK_VON, WERK_BIS = 7, 20

_LOCK = threading.Lock()
_ZAEHLER = {"marken": 0, "luecken": 0, "lauf": 0, "fehler": 0}
_DECKEL_GEMELDET = set()          # Tagesdateien, deren 20-MB-Zeile schon fiel
_FEHLER_LOG_MONO = [-1e18]        # Log-Drossel der Schreibfehler (1/min)
FEHLER_LOG_DROSSEL_S = 60.0
# Lauf-Marke: Dedup IM SCHREIBER ueber den zuletzt geschriebenen Slot-Anfang
# (User 02.09.: kein Lesen der Datei je Takt). Prozessweit — der Dienst hat
# genau eine Sweep-Schleife.
_LAUF_STAND = {"slot": None}


# ------------------------------------------------------------------ Pfade/Zeit
def ordner(cfg):
    return os.path.join((cfg or {}).get("data_dir") or "", *ORDNER_TEILE)


def tag_pfad(cfg, datum):
    return os.path.join(ordner(cfg), f"{datum}.jsonl")


def tagesgrenzen(datum):
    """-> (tag0, tag_ende) in Epoche-Sekunden. DIESELBE Rechnung wie
    auftritte.py:337-344 (lokal, strptime + timedelta) — damit Kopf-Navigation,
    Personensicht und Leiste denselben Tag meinen. Am Umstelltag ist die
    Spanne 23 bzw. 25 Stunden; das ist kein Fehler, das ist der Tag."""
    dt = datetime.datetime.strptime(datum, "%Y-%m-%d")
    return dt.timestamp(), (dt + datetime.timedelta(days=1)).timestamp()


def tag_von_ts(ts):
    """Kalendertag (lokal) eines Zeitstempels — das Gegenstueck zu tagesgrenzen."""
    return datetime.datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d")


def zelle_von_ts(ts):
    """Zelle 0..95 = lokale Uhrzeit des Zeitpunkts (Stunde*4 + Viertel). Am
    Umstelltag faellt die doppelte Stunde zweimal auf dieselben vier Zellen,
    die fehlende Stunde bekommt keine — genau die Deklaration aus §2."""
    lt = time.localtime(float(ts))
    return lt.tm_hour * 4 + lt.tm_min // 15


def slot_start(ts):
    """Anfang des 15-min-Slots, in dem `ts` liegt (auf die Tagesgrenzen des
    Kalendertags ausgerichtet, nicht auf 900-Sekunden-Vielfache der Epoche —
    am Umstelltag ist das nicht dasselbe)."""
    ts = float(ts)
    tag0, _ende = tagesgrenzen(tag_von_ts(ts))
    return tag0 + math.floor((ts - tag0) / SLOT_S) * SLOT_S


def slots_im_tag(datum):
    """Zahl der 15-min-Slots des Tages (96; Umstelltag 92 oder 100)."""
    tag0, tag_ende = tagesgrenzen(datum)
    return int(round((tag_ende - tag0) / SLOT_S))


def zellen_im_tag(datum, ts_von, ts_bis):
    """Welche Zellen des Tages `datum` faerbt eine Marke [ts_von, ts_bis]?
    -> sortierte Liste ohne Doppelte. Ein Auftritt ueber Slot-Grenzen faerbt
    alle ueberdeckten Slots (F8). Der Lauf geht ueber ALIGNTE Slot-Anfaenge
    (tag0 + n*900): die Umstellung liegt immer auf einer Stundengrenze, also
    nie mitten in einem Slot — jeder Slot-Anfang hat damit genau eine Zelle."""
    tag0, tag_ende = tagesgrenzen(datum)
    von = max(float(ts_von), tag0)
    bis = min(float(ts_bis), tag_ende - 0.001)
    if bis < von:
        return []
    zellen = set()
    s = tag0 + math.floor((von - tag0) / SLOT_S) * SLOT_S
    while s <= bis:
        zellen.add(zelle_von_ts(s))
        s += SLOT_S
    return sorted(zellen)


def _spanne_klemmen(ts_von, ts_bis, log):
    ts_von = float(ts_von)
    try:
        ts_bis = float(ts_bis) if ts_bis is not None else ts_von
    except (TypeError, ValueError):
        ts_bis = ts_von
    if ts_bis < ts_von:
        ts_bis = ts_von
    if ts_bis - ts_von > SPANNE_MAX_S:
        if log:
            log(f"anwesenheit: span {ts_bis - ts_von:.0f} s clamped to "
                f"{SPANNE_MAX_S} s (broken end time)")
        ts_bis = ts_von + SPANNE_MAX_S
    return ts_von, ts_bis


def _tage_der_spanne(ts_von, ts_bis):
    """Alle Kalendertage, die eine Spanne beruehrt (hoechstens zwei bei einer
    geklemmten Spanne von einem Tag; der Lauf zaehlt in Tagesgrenzen, nicht
    in 86400-Sekunden-Schritten — Umstelltage)."""
    tage = []
    datum = tag_von_ts(ts_von)
    letzter = tag_von_ts(ts_bis)
    while True:
        tage.append(datum)
        if datum >= letzter or len(tage) > 3:
            break
        _t0, t_ende = tagesgrenzen(datum)
        datum = tag_von_ts(t_ende + 1)
    return tage


# ------------------------------------------------------------------ Schreiben
def _fehler_loggen(log, text):
    with _LOCK:
        _ZAEHLER["fehler"] += 1
        jetzt = time.monotonic()
        laut = jetzt - _FEHLER_LOG_MONO[0] >= FEHLER_LOG_DROSSEL_S
        if laut:
            _FEHLER_LOG_MONO[0] = jetzt
    if laut and log:
        log(f"anwesenheit: {text} ({_ZAEHLER['fehler']} write failures so far)")


def _zeile_schreiben(cfg, datum, zeile, log):
    """DIE eine Schreibstelle: open/write/close je Zeile (Kopfkommentar),
    danach der Deckel-Blick. -> True/False; ein Fehler kostet nur die Marke."""
    pfad = tag_pfad(cfg, datum)
    try:
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(pfad, "a", encoding="utf-8") as f:
            f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
    except Exception as e:                                   # noqa: BLE001
        _fehler_loggen(log, f"write to {os.path.basename(pfad)} failed: "
                            f"{type(e).__name__}: {e}")
        return False
    try:
        if os.path.getsize(pfad) > DECKEL_B:
            with _LOCK:
                neu = pfad not in _DECKEL_GEMELDET
                _DECKEL_GEMELDET.add(pfad)
            if neu and log:
                log(f"anwesenheit: {os.path.basename(pfad)} exceeds "
                    f"{DECKEL_B // (1024 * 1024)} MB — still appending, readers "
                    f"only see the last {LESE_DECKEL_B // (1024 * 1024)} MB")
    except OSError:
        pass
    return True


def markieren(cfg, person, ts_von, ts_bis, kamera, quelle, eid=None, log=None):
    """EINE Personen-Marke: Person P war von ts_von bis ts_bis auf `kamera`
    bestaetigt da (quelle aus QUELLEN). Kamera ist PFLICHT (Kamera-/Area-
    Filter der Seite): ohne Kamera wird abgewiesen und gezaehlt, nie still
    geschrieben. Beruehrt die Spanne zwei Kalendertage, bekommt jede
    Tagesdatei dieselbe Zeile; der Leser schneidet auf seinen Tag.
    -> True, wenn jede beruehrte Tagesdatei die Zeile bekam."""
    person = str(person or "").strip()
    kamera = str(kamera or "").strip()
    if not person:
        return False
    if not kamera:
        _fehler_loggen(log, f"{quelle} mark for a person without camera rejected")
        return False
    if quelle not in QUELLEN:
        _fehler_loggen(log, f"unknown source {quelle!r} (contract: {QUELLEN})")
        return False
    try:
        ts_von, ts_bis = _spanne_klemmen(ts_von, ts_bis, log)
    except (TypeError, ValueError) as e:
        _fehler_loggen(log, f"bad timestamps for {quelle} mark: {e}")
        return False
    zeile = {"ts": round(ts_von, 1), "bis": round(ts_bis, 1), "person": person,
             "kamera": kamera, "quelle": quelle}
    if eid:
        zeile["eid"] = str(eid)
    ok = True
    for datum in _tage_der_spanne(ts_von, ts_bis):
        ok = _zeile_schreiben(cfg, datum, zeile, log) and ok
    if ok:
        with _LOCK:
            _ZAEHLER["marken"] += 1
    return ok


def luecke(cfg, ts_von, ts_bis, kamera, eid, log=None):
    """Luecken-Marke (K1): ein Event wurde OHNE Analyse abgehakt (uebersprungen,
    fehler). Die Zelle bleibt dann LEER statt gruen — "nicht hingesehen" ist
    etwas anderes als "nicht da". Kamera ist Pflicht wie bei der Personen-
    Marke (die Seite filtert je Kamera/Area)."""
    kamera = str(kamera or "").strip()
    if not kamera:
        _fehler_loggen(log, "gap mark without camera rejected")
        return False
    try:
        ts_von, ts_bis = _spanne_klemmen(ts_von, ts_bis, log)
    except (TypeError, ValueError) as e:
        _fehler_loggen(log, f"bad timestamps for gap mark: {e}")
        return False
    zeile = {"ts": round(ts_von, 1), "bis": round(ts_bis, 1),
             "kamera": kamera, "art": ART_LUECKE, "eid": str(eid or "")}
    ok = True
    for datum in _tage_der_spanne(ts_von, ts_bis):
        ok = _zeile_schreiben(cfg, datum, zeile, log) and ok
    if ok:
        with _LOCK:
            _ZAEHLER["luecken"] += 1
    return ok


def lauf_marke(cfg, jetzt=None, log=None):
    """Lauf-Marke (User 02.09.): EINE Zeile je 15-min-Slot, in dem der Dienst
    lief — systemweit, ohne Kamera. Schreiber ist die Sweep-Schleife (der
    regelmaessige Frigate-Takt), beim Start sofort einmal. Dedup im
    Schreiber ueber den zuletzt geschriebenen Slot-Anfang: zwei Sweeps im
    selben Slot ergeben eine Zeile, der Slot-Wechsel eine neue, der
    Tageswechsel eine neue Datei — ohne die Datei je Takt zu lesen.
    -> True, wenn eine Zeile geschrieben wurde; False bei Dedup oder Fehler
    (Fehler gezaehlt + gedrosselt geloggt, nie geworfen)."""
    try:
        jetzt = time.time() if jetzt is None else float(jetzt)
        anfang = slot_start(jetzt)
    except (TypeError, ValueError, OverflowError, OSError) as e:
        _fehler_loggen(log, f"bad timestamp for run mark: {e}")
        return False
    with _LOCK:
        if _LAUF_STAND["slot"] == anfang:
            return False
    ok = _zeile_schreiben(cfg, tag_von_ts(anfang),
                          {"ts": round(anfang, 1), "art": ART_LAUF}, log)
    if ok:
        with _LOCK:
            _LAUF_STAND["slot"] = anfang
            _ZAEHLER["lauf"] += 1
    return ok


def zeitspanne_akte(zeile):
    """Ereigniszeit einer Akte-Zeile (deckung.jsonl) -> (von, bis). EINE Regel
    (§2): start, sonst ts; Ende ende_ts, sonst start + dauer_s; fehlt beides,
    nur der Start-Slot."""
    von = zeile.get("start") or zeile.get("ts") or 0
    von = float(von)
    bis = zeile.get("ende_ts")
    if not bis:
        try:
            d = float(zeile.get("dauer_s") or 0)
        except (TypeError, ValueError):
            d = 0.0
        bis = von + max(0.0, d)
    return von, float(bis)


def akte_zeile_markieren(cfg, zeile, log=None):
    """Der Worker-Griff (Konzept §3, Quelle A): EINE Akte-Zeile -> Marken.
    kategorie uebersprungen/fehler -> Luecken-Marke; sonst je bestaetigter
    Person eine Marke, Kamera = Kamera des Events. Wird von JEDER Stelle
    gerufen, die `bestaetigt` setzt oder erweitert (Deckungs-Vertrag,
    Gate-Inventar) — process() nachhol-unabhaengig und _deckung_korrektur.
    -> Zahl der geschriebenen Marken."""
    if not isinstance(zeile, dict):
        return 0
    try:
        von, bis = zeitspanne_akte(zeile)
    except (TypeError, ValueError) as e:
        _fehler_loggen(log, f"record without usable time: {e}")
        return 0
    kamera = zeile.get("camera") or zeile.get("kamera") or ""
    eid = zeile.get("eid")
    if zeile.get("kategorie") in ("uebersprungen", "fehler"):
        return 1 if luecke(cfg, von, bis, kamera, eid, log=log) else 0
    n = 0
    for p in zeile.get("bestaetigt") or []:
        if markieren(cfg, p, von, bis, kamera, "worker", eid=eid, log=log):
            n += 1
    return n


def zaehler():
    """Prozess-Zaehler (Marken/Luecken/Lauf/Fehler) fuer die Systemstatus-Auskunft."""
    with _LOCK:
        return dict(_ZAEHLER)


def marge_sperrt(maxima, marge):
    """Die Marge-Regel des Urteils (.400, verdict_v2): stehen MEHRERE Kandidaten
    ueber der Latte und liegt der Abstand von Platz 1 zu Platz 2 unter der
    Marge, wird NIEMAND bestaetigt. 0 = aus. Hier als EINE Funktion, weil die
    Live-Marke (K4, User-Entscheid §9.2) dieselbe Regel auf die Kandidaten
    eines Auftritts anwendet — der WERT kommt bei beiden aus cfg['urteil_marge'],
    die Regel steht nur hier."""
    try:
        marge = float(marge or 0)
    except (TypeError, ValueError):
        return False
    werte = sorted((float(x or 0) for x in maxima), reverse=True)
    return bool(marge) and len(werte) > 1 and (werte[0] - werte[1]) < marge


def marge_urteil(kandidaten, marge, trennung):
    """FUNDSTELLEN-BEWUSSTE Marge (03.09. spaet, User-Go am Familien-Fall:
    zwei echte Menschen in einem Event, beide sauber erkannt, die alte Regel
    benannte NIEMANDEN — und bei 3+ Personen leerte ein einziges nahes Paar
    die komplette Bestaetigten-Liste).

    kandidaten: [{"p": name, "max": bester_kosinus, "fund": [(idx, t_s),
    ...]|None, "bestaetigt": bool}] — fund sind die Stimm-Detektionen
    (Index in der Akte-detektionen-Liste + Frame-Zeit); bestaetigt sind
    die, die die Erkennungs-Regel bestanden haben, unbestaetigte Eintraege
    die Vergleichs-Kandidaten (>= win_thresh) der Rest-Regel.
    -> (set der Personen, die benannt werden, [Sperr-Tupel (a, ca, b, cb)]).

    KONKURRENZ-Frage je Paar (die Physik dahinter, geeicht 03.09. an den
    Referenz-Faellen — Familien-Duo nacheinander vs. Alternier-Deutung
    EINES Unbekannten):
      1. Stammen die Stimmen zu einem Anteil >= `trennung` aus DENSELBEN
         Detektionen (Anteil an der kleineren Menge)? -> dasselbe Gesicht,
         zweifach gedeutet: KONKURRENZ (gemessen: echte Doppel-Deutungen
         0,86-1,0, getrennte Menschen <= 0,17).
      2. Sind die Stimm-ZEITintervalle disjunkt? -> nacheinander im Bild,
         zwei Menschen: KEINE Konkurrenz (Familien-Fall).
      3. Gibt es KO-PRAESENZ (derselbe Frame-Zeitstempel, VERSCHIEDENE
         Detektionen)? -> beweisbar zwei Gesichter gleichzeitig: KEINE
         Konkurrenz.
      4. Sonst (zeitlich verzahnt, ohne Ko-Praesenz-Beweis): die
         Deutungen ALTERNIEREN auf demselben Menschen -> KONKURRENZ
         (der WSIN-Fall: Index-Ueberlapp nur 0,07, aber verzahnt).
    Gesperrt wird PAARWEISE — ein unbeteiligter Dritter bleibt benannt.
    Fehlendes fund (Alt-Akten, Live bis zum Track-Umbau) gilt als
    konkurrierend — exakt das alte Verhalten. trennung <= 0 = Trennung
    aus (alles konkurriert, wie marge_sperrt + Rest-Regel)."""
    try:
        m = float(marge or 0)
    except (TypeError, ValueError):
        m = 0.0
    try:
        tr = float(trennung or 0)
    except (TypeError, ValueError):
        tr = 0.0

    def _zu_nah(ca, cb):
        # K4: die ABSTANDS-Frage rechnet NUR marge_sperrt (dieselbe eine
        # Regel wie ueberall) — hier faellt nie ein eigener '< marge'-Vergleich.
        return marge_sperrt([ca, cb], m)

    def _konkurrieren(a, b):
        fa, fb = a.get("fund"), b.get("fund")
        if tr <= 0 or not fa or not fb:
            return True                       # aus/ohne Fundstellen: altes Verhalten
        A, B = {i for i, _t in fa}, {i for i, _t in fb}
        if len(A & B) / max(1, min(len(A), len(B))) >= tr:
            return True                       # dasselbe Gesicht doppelt gedeutet
        za, zb = [t for _i, t in fa], [t for _i, t in fb]
        if min(max(za), max(zb)) < max(min(za), min(zb)):
            return False                      # disjunkte Zeitintervalle: nacheinander
        ta, tb = {}, {}
        for i, t in fa:
            ta.setdefault(round(t, 2), set()).add(i)
        for i, t in fb:
            tb.setdefault(round(t, 2), set()).add(i)
        for t in set(ta) & set(tb):
            if ta[t] - tb[t] and tb[t] - ta[t]:
                return False                  # Ko-Praesenz: zwei Gesichter im selben Frame
        return True                           # verzahnt ohne Beweis: Alternier-Deutung

    best = [k for k in kandidaten if k.get("bestaetigt")]
    rest = [k for k in kandidaten if not k.get("bestaetigt")]
    raus, sperren = set(), []
    for i, a in enumerate(best):
        for b in best[i + 1:]:
            if _konkurrieren(a, b) and _zu_nah(float(a["max"]), float(b["max"])):
                raus.add(a["p"]); raus.add(b["p"])
                sperren.append((a["p"], float(a["max"]), b["p"], float(b["max"])))
    for a in best:
        if a["p"] in raus:
            continue
        for r in rest:
            if not _konkurrieren(a, r):
                continue
            if (float(r["max"]) >= float(a["max"])
                    or _zu_nah(float(a["max"]), float(r["max"]))):
                raus.add(a["p"])
                sperren.append((a["p"], float(a["max"]), r["p"], float(r["max"])))
                break
    return {k["p"] for k in best} - raus, sperren


# ------------------------------------------------------------------ Lesen
def _zeilen_lesen(pfad):
    """-> (roh_zeilen, groesse_gekappt). Liest nur das Ende einer aufgeblaehten
    Datei; die angeschnittene erste Zeile wird verworfen."""
    try:
        groesse = os.path.getsize(pfad)
        with open(pfad, "rb") as f:
            gekappt = groesse > LESE_DECKEL_B
            if gekappt:
                f.seek(groesse - LESE_DECKEL_B)
                f.readline()
            roh = f.read().decode("utf-8", "replace")
    except FileNotFoundError:
        return [], False
    except Exception:                                        # noqa: BLE001
        return [], False
    return roh.splitlines(), gekappt


def tag_lesen(cfg, datum, kameras=None):
    """Die Marken EINES Tages, dedupliziert auf (person, zelle).
    kameras: optionaler Filter (Menge von Kameranamen) — None = alle. Mit
    Menge zaehlen nur Personen-/Luecken-Marken dieser Kameras; Lauf-Marken
    zaehlen IMMER (sie sind systemweit). Die Area-Sicht loest der Aufrufer
    ueber core/areas in eine Kameramenge auf; hier gibt es kein Area-Feld.
    -> {"personen": {person: {zelle: {"quellen": [...], "kameras": [...],
                                       "eids": [...]}}},
        "zellen": {0..95: {"lauf": bool, "luecke_n": n}},
        "kaputt": n, "zeilen": n, "gekappt": bool, "n_slots": 92|96|100}
    Renderer-Semantik (Kopfkommentar): Person -> rot; sonst lauf und
    luecke_n == 0 -> gruen; sonst LEER.
    Je Zeile fehlertolerant (S3): eine kaputte Zeile wird gezaehlt, nie
    geworfen — ein Schreiber und ein Leser koennen sich an einer halben
    Zeile begegnen. Kein Cache: Z4 ruft es je Filter einmal."""
    zeilen, gekappt = _zeilen_lesen(tag_pfad(cfg, datum))
    filter_set = None if kameras is None else {str(k) for k in kameras}
    personen = {}
    zellen = {c: {"lauf": False, "luecke_n": 0} for c in range(ZELLEN_JE_TAG)}
    kaputt = n = 0
    for z in zeilen:
        if not z.strip():
            continue
        try:
            d = json.loads(z)
            von = float(d["ts"])
        except Exception:                                    # noqa: BLE001
            kaputt += 1
            continue
        n += 1
        art = d.get("art")
        if art == ART_LAUF:
            c = zelle_von_ts(von)
            if c in zellen:
                zellen[c]["lauf"] = True
            continue
        try:
            bis = float(d.get("bis") if d.get("bis") is not None else von)
        except (TypeError, ValueError):
            kaputt += 1
            continue
        kamera = str(d.get("kamera") or "")
        if filter_set is not None and kamera not in filter_set:
            continue
        cs = zellen_im_tag(datum, von, bis)
        if art == ART_LUECKE:
            for c in cs:
                zellen[c]["luecke_n"] += 1
            continue
        p = str(d.get("person") or "")
        if not p:
            kaputt += 1
            continue
        je_zelle = personen.setdefault(p, {})
        for c in cs:
            e = je_zelle.setdefault(c, {"quellen": set(), "kameras": set(), "eids": set()})
            if d.get("quelle"):
                e["quellen"].add(str(d["quelle"]))
            if kamera:
                e["kameras"].add(kamera)
            if d.get("eid"):
                e["eids"].add(str(d["eid"]))
    for p in personen.values():
        for e in p.values():
            for k in ("quellen", "kameras", "eids"):
                e[k] = sorted(e[k])
    return {"personen": personen, "zellen": zellen, "kaputt": kaputt,
            "zeilen": n, "gekappt": gekappt, "n_slots": slots_im_tag(datum)}


def tage_vorhanden(cfg):
    """Sortierte Liste der Kalendertage, fuer die eine Tagesdatei liegt (Z4,
    .409): der aelteste ist die untere Blaetter-Grenze der Seite — es gibt
    keine Vergangenheit davor (User 02.09.: keine Migration, die Historie
    beginnt mit der schreibenden Version) — und zugleich das
    "Aufzeichnung seit"-Datum im Kopf. Dieselbe Namens-Regel wie kuerzen
    (TAG_RE): fenster.json und Fremddateien zaehlen nicht."""
    o = ordner(cfg)
    try:
        namen = os.listdir(o)
    except OSError:
        return []
    return sorted(m.group(1) for m in (TAG_RE.match(n) for n in namen) if m)


# ------------------------------------------------------------------ Tagesfenster
def fenster_override(cfg):
    """Nutzer-Vorgabe anwesenheit_tag_von/-bis (Whitelist-Paar). -1 = nicht
    gesetzt = Automatik. Gilt nur, wenn BEIDE gesetzt sind und bis > von."""
    try:
        von = int((cfg or {}).get("anwesenheit_tag_von", -1))
        bis = int((cfg or {}).get("anwesenheit_tag_bis", -1))
    except (TypeError, ValueError):
        return None
    if 0 <= von <= 23 and 1 <= bis <= 24 and bis > von:
        return von, bis
    return None


def _stundenbruch(ts):
    lt = time.localtime(float(ts))
    return lt.tm_hour + lt.tm_min / 60.0


def fenster_rechnen(cfg, heute):
    """Perzentil-Fenster ueber die letzten FENSTER_TAGE Kalendertage ab
    `heute` (Datum-String). Jede Personen-Marke traegt ihren Anfang UND ihr
    Ende bei (ein 40-min-Live-Auftritt zaehlt also an beiden Enden); Luecken-
    und Lauf-Marken zaehlen nicht (keine Person).
    -> dict mit von/bis/quelle/marken."""
    proben, marken = [], 0
    dt = datetime.datetime.strptime(heute, "%Y-%m-%d")
    for i in range(FENSTER_TAGE):
        datum = (dt - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        zeilen, _g = _zeilen_lesen(tag_pfad(cfg, datum))
        for z in zeilen:
            try:
                d = json.loads(z)
                if d.get("art") or not d.get("person"):
                    continue
                von = float(d["ts"])
                bis = float(d.get("bis") if d.get("bis") is not None else von)
            except Exception:                                # noqa: BLE001
                continue
            marken += 1
            proben.append(_stundenbruch(von))
            proben.append(_stundenbruch(bis))
    if marken < FENSTER_MIN_MARKEN:
        return {"von": WERK_VON, "bis": WERK_BIS, "quelle": "werk", "marken": marken}
    proben.sort()
    n = len(proben)
    p_lo, p_hi = FENSTER_PERZENTILE
    lo = proben[min(n - 1, int(round(p_lo / 100.0 * (n - 1))))]
    hi = proben[min(n - 1, int(round(p_hi / 100.0 * (n - 1))))]
    von = int(math.floor(lo))
    bis = int(math.ceil(hi))
    von = max(0, min(23, von))
    bis = max(von + 1, min(24, bis))
    if bis - von < FENSTER_MIN_H:
        bis = min(24, von + FENSTER_MIN_H)
        if bis - von < FENSTER_MIN_H:
            von = max(0, bis - FENSTER_MIN_H)
    if bis - von > FENSTER_MAX_H:
        bis = von + FENSTER_MAX_H          # abends kappen (Morgen = Schichtbeginn)
    return {"von": von, "bis": bis, "quelle": "auto", "marken": marken}


def fenster(cfg, heute=None, log=None):
    """Das geltende Tagesfenster -> {"von", "bis", "quelle", "marken", "datum"}.
    Override zuerst; sonst einmal je Kalendertag gerechnet und in
    state/anwesenheit/fenster.json abgelegt (M6: 14 Dateien bei jedem Klick
    waren gemessen 47 ms — nicht je Seitenaufruf). Der Nachtjob ruft es, das
    erste Lesen eines neuen Tages ebenso."""
    heute = heute or tag_von_ts(time.time())
    ov = fenster_override(cfg)
    if ov:
        return {"von": ov[0], "bis": ov[1], "quelle": "override", "marken": None,
                "datum": heute}
    pfad = os.path.join(ordner(cfg), FENSTER_DATEI)
    try:
        with open(pfad, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and d.get("datum") == heute and "von" in d and "bis" in d:
            return d
    except Exception:                                        # noqa: BLE001
        pass
    d = fenster_rechnen(cfg, heute)
    d["datum"] = heute
    try:
        # .411: eindeutige tmp (core.atomar) — am Tageswechsel rechnen mehrere
        # Threads (HTTP, Takt, Nachtjob) das Fenster gleichzeitig neu und
        # schrieben bis dahin alle auf `<pfad>.tmp-<pid>` (Kollisionsklasse
        # des Tester-Logs 02.09.).
        _atomar.json_schreiben(pfad, d, indent=None, ensure_ascii=True)   # Bytes wie bisher
    except Exception as e:                                   # noqa: BLE001
        if log:
            log(f"anwesenheit: window file not written: {type(e).__name__}: {e}")
    return d


# ------------------------------------------------------------------ Nachtjob
def _grenz_datum(tage, heute=None):
    """Aeltester Tag, der bei `tage` Aufbewahrung noch dazugehoert."""
    heute = heute or tag_von_ts(time.time())
    dt = datetime.datetime.strptime(heute, "%Y-%m-%d")
    return (dt - datetime.timedelta(days=max(1, int(tage)))).strftime("%Y-%m-%d")


def kuerzen(cfg, tage, log=None, heute=None):
    """Nachtjob: Tagesdateien aelter als `tage` loeschen — NUR <datum>.jsonl;
    fenster.json und alles andere im Ordner bleibt stehen (S3). Die
    Aufbewahrung kommt aus der Config (anwesenheit_tage), nie von hier.
    -> (behalten, weg)."""
    o = ordner(cfg)
    if not os.path.isdir(o):
        return (0, 0)
    grenze = _grenz_datum(tage, heute)
    behalten = weg = 0
    for name in sorted(os.listdir(o)):
        m = TAG_RE.match(name)
        if not m:
            continue
        if m.group(1) < grenze:
            try:
                os.remove(os.path.join(o, name))
                weg += 1
            except OSError as e:
                if log:
                    log(f"anwesenheit: trim could not remove {name}: {e}")
                behalten += 1
        else:
            behalten += 1
    return (behalten, weg)
