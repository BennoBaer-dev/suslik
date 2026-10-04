"""Die Personenzahl eines Ereignisses: wie viele Menschen Frigate fuer die Spanne des Clips meldet (K3, KP3).

HERKUNFT: Bauplan analysen/bauplan_k3_produkt.md, Stufe KP3 Punkt 1, Regel nach dem Tuer-Konzept
(analysen/konzept_erkennung_tuer.md) Punkt 3.2 und Fehlerfall Punkt 3.5. Das Labor L5 rechnete die Zahl mit
einer festen Rueckblick-Spanne von 24 h und mit Vor- und Nachlauf (labor_k3_personenzahl, vorbereitung.py);
beides ist hier anders, siehe unten.

ZWECK: Der Worker beendet ein Ereignis frueh, sobald der Stapel so viele verschiedene Namen erkannt hat wie
diese Zahl und die Tuer zu ist (core.tuer); die Zahl ist ausserdem die Obergrenze des Stapels (core.stapel).
Eine zu kleine Zahl kostet Namen, eine zu grosse nur das fruehe Ende: im Zweifel zaehlt die Regel mehr.

DIE REGEL (Punkt 3.2): gezaehlt werden die person-Events derselben Kamera, deren Zeitraum die Spanne des
Clips beruehrt, das Ereignis selbst eingerechnet. Die Clip-Spanne ist die Spanne des Ereignisses, OHNE Vor-
und Nachlauf (gemessen in L5: Clip etwa gleich Event-Spanne; mit Vor- und Nachlauf zaehlte die Regel zu
viele). Ausgenommen sind die Events, die suslik selbst ueber die API anlegt (`data.type` "api",
core/frigateevents.py, Create-Endpunkt `/events/{camera_name}/{label}/create` in der OpenAPI der laufenden
0.18.0, belegt 04.10.2026 in backups/release3_bau/kp3/belege/); verfolgte Objekte tragen dort "object".
Ist ein solches api-Event selbst das analysierte Ereignis, zaehlt es mit wie jedes andere.

WARUM DREI ABFRAGEN: Frigate filtert nur nach der Startzeit, `after` und `before` exklusiv
(core.einspielen.EPS_S). Ein Event, das vor dem Clip begann, findet eine Abfrage ueber die Clip-Spanne nicht.
Die Rueckblick-Spanne R (der vorhandene Config-Wert `lookback_h`, mit dem auch der Sweep zurueckblickt) teilt
die Suche, ohne dass die Richtigkeit an ihr haengt:
  A  Start zwischen Clip-Anfang - R und Clip-Ende (geblaettert);
  B  Start vor Clip-Anfang - R und Dauer mindestens R (`min_length`): nur so ein Event kann von dort bis in
     den Clip reichen (Filter am 04.10. gegengeprueft: min_length 300 lieferte genau die Events ab 300 s);
  C  noch laufende Events (`in_progress=1`), gleich wann begonnen; sie haben keine Dauer fuer B.
Zusammen sind das alle Events, die den Clip beruehren koennen; ueberlappt wird danach hier geprueft.

FEHLERFALL (Punkt 3.5): Die Zahl ist unbrauchbar, wenn eine Abfrage scheitert, eine Abfrage nicht zu Ende
geblaettert werden konnte (Seiten-Deckel oder Seite ohne neue ID), das Ereignis keine Zeiten traegt oder
selbst nicht unter den Treffern ist. Dann gibt es kein fruehes Ende; die Tuer bleibt.

UNBEKANNT (Bauplan analysen/bauplan_pruefmaterial_k3.md, Stufe PM2): eine Einspielung darf die Zahl
ausdruecklich als UNBEKANNT ("unknown") angeben. Das Ereignis laeuft dann wie bei einer unbrauchbaren Zahl
ohne fruehes Ende, ist aber kein Fehler: verifyd.Service.process meldet es als INFO statt WARNING, und der
Zaehler fuer /health fuehrt es unter dem eigenen Grund UNBEKANNT.

EHRLICHE GRENZEN:
  - Frigates Zahl kann ueber der echten liegen (zwei Feldtester-Clips: 3 statt 2, 6 statt 3, Konzept K3
    Abschnitt 3.5). Das ist die sichere Richtung.
  - Ein eigenes "api"-Event, das zugleich das analysierte Ereignis ist, bleibt in den Treffern und zaehlt
    als eine Person mit; nur die uebrigen eigenen api-Events fallen heraus.
  - Wie Frigate `min_length` bei laufenden Events auswertet, ist nicht gemessen; C deckt sie unabhaengig.
"""
import collections
import threading
import urllib.parse

from core import einspielen as _einspiel

# Gruende einer unbrauchbaren Personenzahl (Produkt-Texte, /health und Log, englisch)
FEHLT, NULL, UNGUELTIG = "missing", "zero", "invalid"
OHNE_ZEITEN, ABFRAGE_FEHLER, UNVOLLSTAENDIG, EVENT_FEHLT = (
    "no_event_times", "query_failed", "query_incomplete", "event_not_found")
LOGIK_FEHLER = "logic_error"
# Bauplan Pruefmaterial K3, Stufe PM2: die Einspielung darf die Zahl ausdruecklich als unbekannt angeben.
# Dasselbe Wort ist Wert des Feldes, Wert in den Metadaten und Grund im Zaehler fuer /health; das Ereignis
# laeuft ohne fruehes Ende wie bei einer unbrauchbaren Zahl, gemeldet als INFO statt WARNING.
UNBEKANNT = "unknown"
# `data.type` der Events, die suslik selbst ueber Frigates Create-Endpunkt anlegt (core/frigateevents.py:36)
API_TYP = "api"

_zaehler = collections.Counter()
_zaehler_lock = threading.Lock()


def gueltig(wert):
    """Ob eine Personenzahl brauchbar ist: eine ganze Zahl ab 1 (kein Wahrheitswert); das Wort UNBEKANNT
    ist keine Zahl, sein Grund ist UNBEKANNT. -> (Zahl oder None, Grund oder None)"""
    if wert is None:
        return None, FEHLT
    if wert == UNBEKANNT:
        return None, UNBEKANNT
    if isinstance(wert, bool) or not isinstance(wert, int):
        return None, UNGUELTIG
    if wert == 0:
        return None, NULL
    return (wert, None) if wert > 0 else (None, UNGUELTIG)


def _seiten(api_fn, kamera, before, after=None, **filter_):
    """Alle Events einer Abfrage, rueckwaerts geblaettert wie core.einspielen.fenster_sammeln.
    -> (Liste der Events, vollstaendig als bool)"""
    gesehen, aus = set(), []
    for _n in range(_einspiel.SEITEN_DECKEL):
        q = {"labels": _einspiel.LABEL, "cameras": kamera, "limit": _einspiel.FENSTER_SUCHLIMIT,
             "include_thumbnails": 0, "before": f"{before:.6f}", **filter_}
        if after is not None:
            q["after"] = f"{after:.6f}"
        seite = [e for e in (api_fn("/api/events?" + urllib.parse.urlencode(q)) or [])
                 if isinstance(e, dict) and e.get("id")]
        neu = [e for e in seite if str(e["id"]) not in gesehen]
        gesehen.update(str(e["id"]) for e in neu)
        aus += neu
        if len(seite) < _einspiel.FENSTER_SUCHLIMIT:
            return aus, True
        if not neu:
            return aus, False                     # volle Seite ohne neue ID: nicht zu Ende geblaettert
        before = min(float(e.get("start_time") or 0) for e in seite) + _einspiel.EPS_S
        if after is not None and before <= after:
            return aus, True
    return aus, False                             # Seiten-Deckel


def _beruehrt(e, kamera, anfang, ende):
    """Ob ein Event den Clip beruehrt (Grenzen eingeschlossen, im Zweifel mehr). -> bool"""
    if str(e.get("camera")) != str(kamera) or e.get("label") not in (None, _einspiel.LABEL):
        return False
    start, schluss = e.get("start_time"), e.get("end_time")
    return (start is not None and float(start) <= ende
            and (schluss is None or float(schluss) >= anfang))


def aus_frigate(api_fn, ev, rueckblick_s):
    """Die Personenzahl eines Frigate-Ereignisses nach Punkt 3.2 (drei Abfragen, Kopf dieser Datei).
    -> (Zahl oder None, Grund oder None, Teile fuer die DEBUG-Zeile)"""
    kamera, anfang, ende = ev.get("camera"), ev.get("start_time"), ev.get("end_time")
    try:
        anfang, ende, r = float(anfang), float(ende), max(0.0, float(rueckblick_s))
    except (TypeError, ValueError):
        return None, OHNE_ZEITEN, {}
    if not kamera:
        return None, OHNE_ZEITEN, {}
    grenze = anfang - r
    treffer, api_weg = {}, []
    try:
        a, a_ok = _seiten(api_fn, kamera, ende + _einspiel.EPS_S, after=grenze - _einspiel.EPS_S)
        b, b_ok = _seiten(api_fn, kamera, grenze + _einspiel.EPS_S, min_length=r - _einspiel.EPS_S)
        c, c_ok = _seiten(api_fn, kamera, ende + _einspiel.EPS_S, in_progress=1)
        for e in a + b + c:
            if not _beruehrt(e, kamera, anfang, ende):
                continue
            eid = str(e["id"])
            if ((e.get("data") or {}).get("type") == API_TYP) and eid != str(ev.get("id")):
                api_weg.append(eid)
                continue
            treffer[eid] = e
    except Exception as e:                                           # noqa: BLE001
        return None, ABFRAGE_FEHLER, {"fehler": f"{type(e).__name__}: {e}"[:200]}
    teile = {"ids": sorted(treffer), "api_ausgelassen": sorted(set(api_weg)),
             "abfragen": {"rueckblick": len(a), "frueher_begonnen": len(b), "laufend": len(c)},
             "rueckblick_s": r}
    if not (a_ok and b_ok and c_ok):
        return None, UNVOLLSTAENDIG, teile
    if str(ev.get("id")) not in treffer:
        return None, EVENT_FEHLT, teile
    return len(treffer), None, teile


def ohne_fruehes_ende_zaehlen(grund):
    """Ein Ereignis, das ohne fruehes Ende laeuft (Personenzahl unbrauchbar oder als UNBEKANNT eingespielt,
    oder Logik-Fehler im Worker), fuer /health je Grund zaehlen. -> None"""
    with _zaehler_lock:
        _zaehler[str(grund)] += 1


def stand():
    """Der Zaehler fuer /health: wie oft ein Ereignis seit dem Start ohne fruehes Ende lief, je Grund.
    -> dict"""
    with _zaehler_lock:
        je = dict(sorted(_zaehler.items()))
    return {"ohne_fruehes_ende": sum(je.values()), "gruende": je}
