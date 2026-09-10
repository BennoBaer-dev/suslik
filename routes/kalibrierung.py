"""routes/kalibrierung — die ZENTRALE Kamera-Uebersicht der Kalibrierung
(User-Entscheid 31.08.: EIN Menuepunkt, IMMER pro Kamera).

EINE Seite lebt hier:

  uebersicht()  /kalibrierung — je Kamera eine Kachel: Vorrats-Stand, letzte
                Aktualisierung, die geltenden Werte, und drei Knoepfe
                (Kalibrieren, frisches Material suchen, Vorrat loeschen).
                Von hier geht es je Kamera weiter auf /kalibrierung/<kamera>
                (routes/livekalib.py — DIE Kalibrierseite, seit dem
                Zentral-Umbau der einzige Weg dorthin).

AUSGEBAUT mit .516 (Alt-Latten-Abloesung, User 10.09.2026): die zweite Seite
`lauf()` unter /kalibrierung?lauf=1 — die .377-Seite mit den zwei GLOBALEN
Guete-Reglern am Material des letzten Lernlaufs. Sie stellte
`guete_empfinden_min`/`guete_t_min` ein, und genau diese zwei Werte sind
entfallen: der Lernlauf siebt seit .514 ueber das Register "Face catalog",
je Kamera. Die Seite versprach in fuenf Sprachen weiter, ihre Schwellen
entschieden, "welche Gesichter kuenftige Lernlaeufe behalten" — eine
Oberflaeche, die etwas zusagt, was der Code nicht tut, ist die Fehlerklasse,
die B1 fuer das Katalog-Register ausdruecklich verboten hat. Mit der Seite
fielen ihr Speicherweg (/kalibrierung_setzen) und ihre Texte.

WARUM JE KAMERA und nicht eine Zahl fuer alles: die Gueteskalen sind
kameraabhaengig (Messung 31.08.: Median fiqa_t 0,181 gegen 0,073 an zwei
Kameras derselben Anlage). Was global bleibt, ist deshalb ausdruecklich der
RUECKFALL fuer Kameras ohne eigene Werte, nicht der Anspruch, fuer jede
Kamera zu passen.

Reines Rendern (Muster live/livekalib: Daten als Parameter, kein
Dienst-Import). Die Seiten liefern INHALT; den Rahmen setzt verifyd mit
webui.layout — dadurch traegt die Kamera-Seite denselben Rahmen wie die
Uebersicht, ohne dass dieses Modul etwas ueber die Navigation wissen muss.
"""
import html
import json
import time

from core.sprache import t


def _wann(ts):
    """Zeitpunkt oder ein ehrliches Nichts — nie eine 1970er-Zahl."""
    if not ts:
        return ""
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))


def _zahl(w, stellen=3):
    return "—" if w is None else f"{float(w):.{stellen}f}"


def _quelle_wort(quelle):
    """Woher die geltende Katalog-Latte kommt. Die drei Schluessel stehen
    LITERAL hier (nicht zusammengesetzt): die Sprach-Deckungsstufe liest die
    t()-Aufrufe statisch und hielte einen erst zur Laufzeit gebauten
    Schluessel fuer tot (dieselbe Auflage wie in routes/live.py)."""
    return {"kamera": t("kalib.quelle.kamera"),
            "global": t("kalib.quelle.global"),
            "aus": t("kalib.quelle.aus")}.get(str(quelle), "")


# ------------------------------------------------------------- Uebersicht
def _kachel(k, deckel, bilanz=None, frigate_weg=False):
    """EINE Kamera-Kachel. Sie beantwortet in dieser Reihenfolge: habe ich hier
    Material, wie alt ist es, welche Werte gelten — und dann erst die
    Knoepfe. Ein Kalibrier-Knopf ohne Material waere ein Weg ins Leere,
    deshalb sagt die Kachel den Stand VOR dem Knopf.

    `frigate_weg` (08.09.): Frigate antwortet gerade gar nicht (keine URL,
    keine Verbindung). Dann steht KEINE Kamera in Frigates Liste, und die
    alte Marke "not in Frigate" (Text: "Frigate no longer reports it") waere
    fuer jede Kachel eine Falschaussage — sie behauptete einen Verlust, wo
    nur die Verbindung fehlt. Ehrlich ist in diesem Fall: bekannt aus dem
    Store, Live-Zustand unbekannt."""
    nid = html.escape(k["name"], quote=True)
    name = html.escape(k["name"])
    marke = (f'<span class="pill lvp lvp-ok">{t("kalib.kachel.eigene")}</span>'
             if k["eigene"] else
             f'<span class="pill">{t("kalib.kachel.vorgabe")}</span>')
    if k.get("in_frigate"):
        fremd = ""
    elif frigate_weg:
        fremd = (f' <span class="pill" title="{html.escape(t("kalib.kachel.offline_tip"))}">'
                 f'{t("kalib.kachel.offline")}</span>')
    else:
        fremd = (f' <span class="pill warn" title="{html.escape(t("kalib.kachel.fremd_tip"))}">'
                 f'{t("kalib.kachel.fremd")}</span>')
    if not deckel:
        stand = f'<div class="dim lv-zeile">{t("kalib.kachel.vorrat_aus")}</div>'
    elif k["vorrat_n"]:
        # ZEITRAUM statt nur "zuletzt" (.507, derselbe Satz wie auf der
        # Kamera-Seite): erst er sagt, ob die Kachel einen Tagesquerschnitt
        # meint oder drei Minuten an einer belebten Kamera. Verglichen werden
        # die ANGEZEIGTEN Zeitpunkte (_wann rundet auf Minuten) — steht nur
        # einer da, bleibt es beim alten "zuletzt ...".
        von_txt = _wann(k.get("vorrat_ts_min"))
        bis_txt = _wann(k.get("vorrat_ts"))
        zeile = (t("livekalib.material.zeitraum",
                   von=html.escape(von_txt), bis=html.escape(bis_txt))
                 if von_txt and bis_txt != von_txt else
                 t("kalib.kachel.stand", wann=html.escape(bis_txt)))
        stand = (f'<div class="lv-zeile">'
                 f'{t("kalib.kachel.vorrat", n=k["vorrat_n"], deckel=deckel)}</div>'
                 f'<div class="dim lv-zeile">{zeile}</div>')
    else:
        # K6 (01.09., A4-Befund beim Feldtester: 27 von 31 Kameras ohne
        # Vorrat, die Kachel sagte nur "leer"): liegt eine Fueller-Bilanz
        # vor, erklaert die Kachel den leeren Vorrat ehrlich — kein Gesicht
        # gefunden (Uebersichts-/Distanz-Kamera), Gesichter zu klein/zu
        # schwach, oder Material da, aber die Vorrats-Guete nicht erreicht.
        hinweis = t("kalib.kachel.leer_hinweis")
        if isinstance(bilanz, dict) and int(bilanz.get("events") or 0) > 0:
            _ev = int(bilanz.get("events") or 0)
            if int(bilanz.get("detektionen") or 0) == 0:
                hinweis = t("kalib.kachel.bilanz_keine", ev=_ev)
            elif int(bilanz.get("m") or 0) == 0:
                hinweis = t("kalib.kachel.bilanz_klein", ev=_ev)
            else:
                hinweis = t("kalib.kachel.bilanz_zulauf", ev=_ev)
        stand = (f'<div class="lv-zeile">{t("kalib.kachel.leer")}</div>'
                 f'<div class="dim lv-zeile">{html.escape(hinweis)}</div>')
    werte = (f'<div class="dim lv-zeile">'
             f'{t("kalib.kachel.werte", det=_zahl(k["det"], 2), e=_zahl(k["e"]), tw=_zahl(k["t"]), p=_zahl(k.get("p"), 2))}'
             f'</div>'
             f'<div class="dim lv-zeile">'
             f'{t("kalib.kachel.katalog", e=_zahl(k["kat_e"]), tw=_zahl(k["kat_t"]))} '
             f'({_quelle_wort(k["kat_quelle"])})</div>')
    knoepfe = [f'<a class="gtb on" href="/kalibrierung/{nid}">'
               f'{t("kalib.knopf_kalibrieren")}</a>']
    if deckel:
        knoepfe.append(f'<button class="gtb" onclick="kalibFuellen(\'{nid}\',this)">'
                       f'{t("kalib.knopf_fuellen")}</button>')
    if k["vorrat_n"]:
        knoepfe.append(f'<button class="gtb" onclick="liveVorratLeeren(\'{nid}\',this)">'
                       f'{t("kalib.knopf_leeren")}</button>')
    # Kachel-Bauform WIE auf dem Live-Reiter (card + lv-kachel + kamhead):
    # dieselbe Sache soll gleich aussehen, egal aus welcher Richtung man kommt
    # — und die Groessen (Raster, Kopfzeile, Knopfzeile) bleiben so von selbst
    # konsistent, statt hier ein zweites Kachel-Design zu erfinden.
    return (f'<div class="card lv-kachel">'
            f'<div class="kamhead"><b>{name}</b>{fremd}{marke}</div>'
            f'{stand}{werte}'
            f'<div class="dim lv-zeile kal-fuell" id="kf-{nid}"></div>'
            f'<div class="lv-knoepfe">{"".join(knoepfe)}</div></div>')


def uebersicht(daten, kat_global, deckel,
               fueller=(0, 0), banner_leer="", bilanzen=None):
    """-> Seiten-INHALT der zentralen Uebersicht.

    daten        = core.kamerakalib.uebersicht_daten(...)
    kat_global   = die globale Zeile des Registers "Face catalog"
                   (core.kamerakalib.katalog_latten()["global"]). Sie ist seit
                   .516 der EINE Rueckfall — die zweite Karte mit den
                   abgeloesten globalen Guete-Werten ist mit ihnen entfallen.
    deckel       = live_kalib_max (0 = Vorrat aus; dann gibt es nichts zu
                   sammeln, und die Kacheln sagen das statt Knoepfe fuer
                   nichts anzubieten)
    fueller      = (ziel_bilder, deckel_events) des On-demand-Fuellers, damit
                   der Knopf-Text nicht behauptet, was die Config nicht sagt
    banner_leer  = Frigates Fehlertext (leer = Frigate hat geantwortet). Er
                   fuellt nicht nur den Leer-Zweig: solange er steht, ist die
                   Frigate-Liste als Ganzes nicht da, und die Kacheln sagen
                   "nicht verbunden" statt "nicht mehr in Frigate" (08.09.).
    """
    kopf = (f'<h1>{t("kalib.titel")}</h1>'
            f'<p class="hinweis">{t("kalib.uebersicht.erklaerung")}</p>')
    # Was die Kalibrierung NICHT tut, steht mit auf der Seite. Zwei Messungen
    # desselben Tages haben gezeigt, dass Sieben VOR dem Namens-Voting
    # Bestaetigungen kostet — wer hier Regler sieht, soll nicht glauben, er
    # stelle die Erkennung ein.
    grenze = (f'<div class="card"><b>{t("kalib.grenze.titel")}</b>'
              f'<div class="dim">{t("kalib.grenze.satz")}</div></div>')
    if not daten:
        return (kopf + grenze
                + f'<div class="leer"><b>{t("kalib.uebersicht.leer")}</b><br>'
                  f'<small>{html.escape(banner_leer or t("kalib.uebersicht.leer_hinweis"))}'
                  f'</small></div>')
    kacheln = '<div class="lv-grid">' + "".join(
        _kachel(k, deckel, (bilanzen or {}).get(k["name"]),
                frigate_weg=bool(banner_leer))
        for k in daten) + '</div>'
    # .516: EINE Karte, EIN Rueckfall. Bis .515 standen hier zwei Zeilen
    # untereinander — die globale Guete-Latte des Lernwegs und die
    # Katalog-Latte — und darunter ein Knopf auf die Seite, die die erste
    # einstellte. Die erste gibt es nicht mehr, also auch die Zeile und den
    # Knopf nicht: eine Uebersicht, die zwei Latten zeigt, wo eine wirkt,
    # laesst den Betreiber an der falschen drehen.
    glob = (f'<div class="card"><b>{t("kalib.global.titel")}</b>'
            f'<div class="dim lv-zeile">{t("kalib.global.satz")}</div>'
            f'<div class="lv-zeile">'
            f'{t("kalib.global.katalog", e=_zahl(kat_global.get("e")), tw=_zahl(kat_global.get("t")))}'
            f'</div></div>')
    js = ("<script>window._kalibFueller=" + json.dumps(
        {"ziel": int(fueller[0]), "events": int(fueller[1])}) + ";</script>")
    return kopf + grenze + kacheln + glob + js


# ---------------------------------------- Lernlauf-Material der Kamera-Seite
# Was hier noch steht, gehoert NICHT mehr zu einer eigenen Seite: die zwei
# Funktionen liefern der Kamera-Kalibrierseite (routes/livekalib.render) die
# Bilder des letzten Lernlaufs als Anschauungsmaterial fuer ihre Regler.
def _letzter_lauf(saetze):
    """Groesste lauf_id im Bestand. DIESELBE Hausregel wie core.lernlauf
    (alte_laeufe_loeschen: 'L<JJJJMMTT_HHMMSS> sortiert lexikalisch =
    chronologisch') — kein zweiter Zeitbegriff."""
    ids = {str((s.get("lauf") or {}).get("lauf_id") or "") for s in saetze or []}
    ids.discard("")
    return max(ids) if ids else ""


def mitglieder_mit_guete(saetze, kamera=None):
    """Mitglieder mit BEIDEN Massen, je mit Gruppe — aus dem LETZTEN Lauf.

    Zwei bewusste Filter (Widerleger-Fund 30.08.): der Store traegt alle
    Laeufe (anker_lesen liest die ganze anker.jsonl, und
    alte_anker_aufraeumen laesst benannt/uebernommen/verworfen
    laufuebergreifend stehen). Ohne Lauf-Filter mischte die Seite Bilder
    mehrerer Laeufe, obwohl Erklaertext und Zaehler den einen Lauf meinen.
    Und verworfene Gruppen sind doppelt falsch: der Nutzer hat sie schon
    weggeworfen, UND anker_verwerfen loescht ihre Crops — sie waeren
    404-Kacheln, die er bewerten soll, ohne sie zu sehen.

    `kamera` (Zentral-Umbau 31.08.): auf EINE Kamera filtern. So kann die
    Kamera-Seite die Lernlauf-Bilder DIESER Kamera als zusaetzliches Material
    zeigen — der Lernlauf-Kontext bleibt erhalten, ohne einen zweiten
    Bedienweg aufzumachen."""
    lauf = _letzter_lauf(saetze)
    aus = []
    for s in saetze or []:
        if str((s.get("lauf") or {}).get("lauf_id") or "") != lauf:
            continue
        if s.get("status") == "verworfen":
            continue
        wer = s.get("person") or s.get("anker_id") or "?"
        for m in s.get("mitglieder") or []:
            ft, ew = m.get("fiqa_t"), m.get("empf")
            if ft is None or ew is None:
                continue
            if kamera is not None and str(m.get("kamera") or "") != str(kamera):
                continue
            aus.append({"d": str(m.get("datei", "")).rsplit("/", 1)[-1],
                        "lid": lauf, "t": float(ft), "e": float(ew),
                        "k": float(m.get("kante") or 0),
                        # .515 (Sensor 5): die Feature-Norm des Mitglieds, wenn
                        # der Lauf sie gemessen hat. Sie ist das EINZIGE
                        # Material, an dem der neue Norm-Regler ueberhaupt
                        # etwas zeigen kann — der Kalibrier-Ring fuehrt keine
                        # Norm (der Live-/Analyse-Weg misst sie nicht). None =
                        # nicht gemessen und passiert jede Latte, wie ueberall.
                        "n": (None if m.get("norm") is None
                              else float(m["norm"])),
                        "kam": str(m.get("kamera") or ""),
                        "g": bool(m.get("gewaehlt")), "p": str(wer)})
    return aus
