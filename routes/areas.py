"""routes/areas — Areas-Hauptbereich: Sicht-Chips + Verwaltung (Stufe 1 v2).

Partitions-Modell: (eine Kamera -> hoechstens eine Area), alle nicht
zugewiesenen Kameras automatisch in "Default". Die Zuweisung ist deshalb ein
Dropdown je Kamera (ein Wert = Partition per Konstruktion), nicht laenger eine
Checkbox-Matrix. Loeschen einer Area gibt ihre Kameras von selbst an Default
zurueck (Default ist Komplement, wird nie gespeichert).

Renderer nach dem Modul-Kontrakt (webui/bausteine.py): Daten als Parameter, kein
Dienst-Import. R4-Abweichung deklariert (Architektur-Journal). Chips
sind reine LINKS: lesezeichenfaehig, ohne JS bedienbar, S9-messbar.
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe (siehe
Abschnitts-Kommentar in core/texte/en.py): "All"/"Default" sind Anzeige UND
Sicht-Kennung zugleich und bleiben literal; zwei Markup-Saetze ebenso."""
import html
import urllib.parse

from core.sprache import t, t_n


def chips(areas, aktiv, pfad, fest=None):
    """Sicht-Umschalter: All · <Areas alphabetisch> · Default. Rendert NUR, wenn
    Areas angelegt sind — ohne Areas bleibt jede Seite unveraendert (Konzept §6).
    fest = Query-Parameter, die die Sicht ueberleben muessen (z.B. tag, person)."""
    if not areas:
        return ""

    def _link(txt, wert):
        q = dict(fest or {})
        if wert:
            q["area"] = wert
        qs = urllib.parse.urlencode(q)
        kl = "gtb on" if txt == aktiv else "gtb"
        return f'<a class="{kl}" href="{pfad}{"?" + qs if qs else ""}">{html.escape(txt)}</a>'

    teile = ([_link("All", "")] + [_link(n, n) for n in sorted(areas)]
             + [_link("Default", "Default")])
    return f'<div class="arbar">{"".join(teile)}</div>'


def verwaltung(areas, live_cams):
    """Verwaltungs-Block der /areas-Seite: Areas anlegen/loeschen, dann je Kamera
    ein Dropdown 'welche Area' (Vorgabe Default). Speichern OHNE Dienst-Neustart
    (JS areasSpeichern -> POST /areas_speichern -> reload).
    Kamera-Grundmenge = Frigate-Live-Liste VEREINIGT mit allem, was in Areas
    steht: eine umbenannte/entfallene Kamera faellt NIE still raus, sie wird als
    'not seen' markiert (Fehlerklasse stiller Verlust, Konzept §4)."""
    beobachtet = sorted(set(live_cams) | {c for cams in areas.values() for c in cams})
    namen = sorted(areas)

    ak = []
    for name in namen:
        nid = html.escape(name, quote=True)
        n_c = len(areas[name])
        ak.append(
            f'<span class="ar-pill" data-area="{nid}"><b>{html.escape(name)}</b> '
            f'<span class="dim num">{t_n("areas.verwaltung.camzahl", n_c)}</span> '
            f'<button class="gtb" title="{t("areas.verwaltung.attr_entfernen")}" '
            f'onclick="areaEntfernen(this)">×</button></span>')
    leiste = ('<div class="ar-liste">' + "".join(ak) + '</div>' if ak else
              '<p class="dim">No areas yet — every camera is in <b>Default</b>. Add an '
              'area below, then assign cameras to it.</p>')

    zeilen = []
    for c in beobachtet:
        cid = html.escape(c, quote=True)
        akt = next((n for n in namen if c in areas[n]), "")
        opts = '<option value="">Default</option>' + "".join(
            f'<option value="{html.escape(n, quote=True)}"'
            f'{" selected" if n == akt else ""}>{html.escape(n)}</option>' for n in namen)
        weg = ('' if c in live_cams else
               f' <span class="pill warn" title="{t("areas.verwaltung.attr_nicht_gesehen")}">'
               f'{t("areas.verwaltung.pill_nicht_gesehen")}</span>')
        zeilen.append(
            f'<div class="camrow ar-zeile"><div class="camname"><span class="dot"></span>'
            f'{html.escape(c)}{weg}</div>'
            f'<select class="ar-wahl" data-cam="{cid}">{opts}</select></div>')
    tabelle = ('<div class="card">' + "".join(zeilen) + '</div>' if zeilen else
               f'<p class="dim">{t("areas.verwaltung.hinweis_keine_kameras")}</p>')

    return (f'<h3 style="margin-top:1rem">{t("areas.verwaltung.titel")}</h3>'
            + leiste +
            '<p style="margin:.6rem 0">'
            f'<input id="ar-neu" placeholder="{t("areas.verwaltung.attr_neu")}" maxlength="32"> '
            f'<button class="gtb" onclick="areaAnlegen(this)">{t("areas.verwaltung.knopf_anlegen")}</button></p>'
            f'<h3>{t("areas.verwaltung.titel_zuweisen")}</h3>'
            f'<p class="sub">{t("areas.verwaltung.satz_zuweisen")}</p>'
            + tabelle +
            '<p style="margin-top:.6rem">'
            f'<button class="gtb on" onclick="areasSpeichern(this)">{t("areas.verwaltung.knopf_speichern")}</button> '
            '<span id="ar-status" style="color:var(--dim)"></span></p>')


def uebersicht(areas, live_cams):
    """/areas — eigener Hauptbereich (eigener Nav-Bereich zwischen People und Learn):
    oben der Sprung in die Sichten, darunter die Konfiguration."""
    kopf = (f'<h2>{t("areas.titel")}</h2>'
            '<p class="sub">Group cameras into parts of your property (driveway, '
            'backyard, …). An area is a <b>view</b>: passes are always grouped and '
            'judged across the whole property — an area picks the passes that '
            'touched it. The same chips sit on Today, Appearances and Events'
            + (', and alerts name the area of the camera' if areas else '') + '.</p>')
    sprung = ((f'<p class="sub" style="margin-top:.4rem">{t("areas.kopf.sprung")}</p>'
               + chips(areas, "", "/heute")) if areas else '')
    return kopf + sprung + verwaltung(areas, live_cams)
