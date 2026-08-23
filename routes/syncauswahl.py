"""routes/syncauswahl — "Review & sync": die EINE Export-Strecke Master -> Frigate
(.133, User-Design 06.08.). Zeigt jeden Export-Kandidaten als Thumbnail, nach
Person gruppiert, mit dem Vorpruefungs-Urteil als Badge; der Nutzer hakt an, was
wirklich hochgeht. Bewusst Abgewaehltes wird gemerkt (eingeklappt, rueckholbar)
und auch vom automatischen Export uebersprungen. Nach dem Transfer steht je Bild
das ECHTE Ergebnis: hochgeladen oder Frigates Ablehnungsgrund.

.137 (User-Vorgabe 06.08.: "vorab ein Abgleich zwischen dem, was wir in Frigate
haben, dem, was wir nicht drin haben, dem, was wir uebertragen koennen und dem,
was wir nicht uebertragen koennen"): die Seite ist ein VIER-KLASSEN-ABGLEICH mit
ehrlichen Zaehlern und einer Aktion je Klasse — A in beiden · B nur in Frigate
(Import) · C uebertragbar (Auswahl+Transfer) · D nicht uebertragbar, aufgeteilt
in D1 in Frigate geloescht (Entscheidungsfall), D2 API-exportiert/umbenannt
(Gegenstelle unpruefbar) und D3 von Frigate abgelehnt (rotes Badge, nicht
vorgewaehlt, aber anklickbar). Die Klassen kommen fertig aus sync_refs.abgleich().

Kontrakt wie alle routes-Module: reiner Renderer, Daten als Parameter, kein
Dienst-/Netz-/Store-Zugriff — Klassen, Urteile, Abwahl, Live-Flag und Bericht
holt der Handler in verifyd.py.
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py (FR_AUS_HINWEIS aus sync_refs,
zwei Link-im-Satz-Reste literal).
"""
import datetime
import html
import urllib.parse

from core.sprache import t, t_n

# Der Schluessel '<Person>/<Datei>' kommt aus der EINEN Quelle (sync_refs), nie
# als Literal nachgebaut — Cache, Abwahl, Handler und Anzeige muessen zwingend
# denselben bilden (QS-Ebenen-Regel gegen Streu-Literale). Ebenso die Grund-
# Schluessel der D1-Klasse und der Schalt-Hinweis fuer die Live-Flag-Zeile.
from sync_refs import (D1_EXPORT, D1_IMPORT, FR_AUS_HINWEIS,
                       schluessel as _k)

STIL = ("<style>"
        ".sa-gitter{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}"
        ".sa-b{width:104px;text-align:center;font-size:11px;line-height:1.25}"
        ".sa-b img{width:100px;height:100px;object-fit:cover;border-radius:4px;display:block}"
        ".sa-b.sa-raus img{opacity:.45}"
        ".sa-b.sa-weit{width:150px}"
        ".sa-l{display:block;cursor:pointer;margin:2px 0}"
        ".sa-badge{display:block;border-radius:3px;padding:1px 3px;word-break:break-word}"
        ".sa-ok{color:var(--ok)}.sa-warn{color:var(--warn)}.sa-crit{color:var(--crit)}"
        ".sa-b .gtb{font-size:10px;padding:0 6px;margin-top:2px}"
        ".sa-namen{font-size:12px;line-height:1.5;word-break:break-all}"
        "</style>")


def _bildpfad(person, datei):
    """Thumbnail ueber die BESTEHENDE Referenzbild-Route der Known-Seite
    (/refs/<person>/<datei>, read-only + realpath-Containment) — kein zweiter
    Ausliefer-Weg fuer dieselben Dateien."""
    return f"/refs/{urllib.parse.quote(person)}/{urllib.parse.quote(datei)}"


def _daten(person, datei):
    """Person/Datei als data-Attribute statt in einen JS-String interpoliert:
    app.js liest sie aus dem Element (btn.dataset) — kein Quoting-Risiko bei
    Namen mit Apostroph oder Backslash."""
    return (f' data-person="{html.escape(person, quote=True)}"'
            f' data-datei="{html.escape(datei, quote=True)}"')


def _kachel(person, datei, urteil, ablehnung=None):
    """Eine Kandidaten-Kachel: Bild, Haken, Vorpruefungs-Badge, Skip-Knopf.
    urteil = {"ok": bool, "grund": str} oder None (noch nicht gerechnet);
    ablehnung = gemerkte FRIGATE-Ablehnung (D3) oder None.

    .137: Frigates eigenes Urteil schlaegt jedes Vorpruefungs-Badge — es ist die
    Wahrheit ueber dieses Bild. Der Haken startet aus (sonst rennt der Nutzer bei
    jedem Lauf dieselbe Wand an), bleibt aber anklickbar: genau wie bei der
    Vorpruefung darf kein Merker ein Bild endgueltig aussperren."""
    if ablehnung:
        badge = ('<span class="sa-badge sa-crit">'
                 + t("syncauswahl.kachel.frigate_abgelehnt",
                     fehler=html.escape(str(ablehnung.get("fehler")
                                            or t("syncauswahl.kachel.kein_grund"))[:160]))
                 + "</span>")
        an = False
    elif urteil is None:
        badge = f'<span class="sa-badge dim">{t("syncauswahl.kachel.pruefe")}</span>'
        an = True                       # ohne Urteil bleibt es beim alten Verhalten
    elif urteil.get("ok"):
        badge = f'<span class="sa-badge sa-ok">{t("syncauswahl.kachel.vorpruefung_ok")}</span>'
        an = True
    else:
        # User-Vorgabe: voraussichtliche Ablehnungen starten ABGEWAEHLT, bleiben
        # aber anklickbar — Frigates Urteil ist die Wahrheit, unser Detektor ist
        # ein anderes Modell und darf kein Bild endgueltig aussperren.
        badge = ('<span class="sa-badge sa-warn">'
                 + t("syncauswahl.kachel.wohl_abgelehnt",
                     grund=html.escape(str(urteil.get("grund")
                                           or t("syncauswahl.kachel.kein_gesicht"))))
                 + "</span>")
        an = False
    return (f'<span class="sa-b">'
            f'<img src="{_bildpfad(person, datei)}" alt="" loading="lazy">'
            f'<label class="sa-l"><input type="checkbox" class="sa-cb"'
            f'{_daten(person, datei)} onchange="syncAuswahlZaehlen()"'
            f'{" checked" if an else ""}> {t("syncauswahl.kachel.senden")}</label>'
            f'{badge}'
            f'<button class="gtb"{_daten(person, datei)} onclick="syncAbwahl(this,1)" '
            f'title="{t("syncauswahl.kachel.attr_skip")}">'
            f'{t("syncauswahl.kachel.knopf_skip")}</button></span>')


def _kachel_abgewaehlt(person, datei):
    return (f'<span class="sa-b sa-raus">'
            f'<img src="{_bildpfad(person, datei)}" alt="" loading="lazy">'
            f'<span class="sa-badge dim">{html.escape(person)}</span>'
            f'<button class="gtb"{_daten(person, datei)} onclick="syncAbwahl(this,0)" '
            f'title="{t("syncauswahl.kachel.attr_restore")}">'
            f'{t("syncauswahl.kachel.knopf_restore")}</button></span>')


def _knopf(person, datei, ruf, text, titel):
    """Aktions-Knopf einer Kachel. data-label traegt die Ruecksetz-Beschriftung:
    schlaegt der POST fehl, stellt app.js genau DIESEN Text wieder her (frueher
    stand danach immer 'skip' da, egal was auf dem Knopf gestanden hatte)."""
    return (f'<button class="gtb"{_daten(person, datei)} '
            f'data-label="{html.escape(text, quote=True)}" onclick="{ruf}" '
            f'title="{html.escape(titel, quote=True)}">{html.escape(text)}</button>')


def _kachel_geloescht(person, datei, grund):
    """D1 — in Frigate geloescht, Name war vergleichbar: ein ENTSCHEIDUNGSFALL.
    Nichts passiert von allein (eine Loeschung drueben kann Absicht sein), der
    Nutzer waehlt: nochmal anbieten oder die Loeschung respektieren."""
    satz = (t("syncauswahl.geloescht.satz_import") if grund == D1_IMPORT else
            t("syncauswahl.geloescht.satz_export"))
    return (f'<span class="sa-b sa-weit">'
            f'<img src="{_bildpfad(person, datei)}" alt="" loading="lazy">'
            f'<span class="sa-badge sa-warn">{t("syncauswahl.geloescht.badge")}</span>'
            f'<span class="sa-badge dim">{html.escape(person)} — {satz}</span>'
            + _knopf(person, datei, "syncWiederAnbieten(this)",
                     t("syncauswahl.knopf_anbieten"),
                     t("syncauswahl.geloescht.attr_anbieten"))
            + _knopf(person, datei, "syncAbwahl(this,1)",
                     t("syncauswahl.geloescht.knopf_respekt"),
                     t("syncauswahl.geloescht.attr_respekt"))
            + "</span>")


def _kachel_api(person, datei):
    """D2 — per API exportiert: Frigate fuehrt das Bild unter EIGENEM Namen, ein
    Namensabgleich kann nicht sagen, ob es drueben noch liegt. Nur eine Aktion."""
    return (f'<span class="sa-b sa-weit">'
            f'<img src="{_bildpfad(person, datei)}" alt="" loading="lazy">'
            f'<span class="sa-badge dim">'
            + t("syncauswahl.api.badge", person=html.escape(person)) + '</span>'
            + _knopf(person, datei, "syncWiederAnbieten(this)",
                     t("syncauswahl.knopf_anbieten"),
                     t("syncauswahl.api.attr_anbieten"))
            + "</span>")


def _fr_zeile(fr):
    """Live-Zustand von Frigates EIGENER Gesichtserkennung. fr = (an, detail),
    frisch aus Frigates Config gelesen (Handler) — ein gespeicherter Alt-Status
    darf hier NIE stehen: im Operator-Test 06.08. las sich ein stundenalter
    Sync-Status wie der Live-Zustand."""
    if not fr:
        return ""
    an, detail = fr
    if an is None:
        return (f'<div class="card"><b>{t("syncauswahl.fr.titel_unbekannt")}</b><br>'
                '<span class="dim">'
                + t("syncauswahl.fr.satz_unbekannt",
                    detail=html.escape(str(detail)[:160])) + "</span></div>")
    if an:
        return (f'<div class="card"><b>{t("syncauswahl.fr.titel_an")}</b> '
                f'<span class="dim">{t("syncauswahl.fr.satz_an")}</span></div>')
    return (f'<div class="card"><b>{t("syncauswahl.fr.titel_aus")}</b><br>'
            '<span class="sa-warn">' + html.escape(FR_AUS_HINWEIS) + "</span></div>")


def bilanz_zeile(bilanz, ablehnungen, mit_personen=True):
    """Die ehrliche Gesamtbilanz ueber ALLE Klassen (.137). Anlass: "die ganzen
    Bilder fehlen doch" im Operator-Test — die Zahlen stimmten, nur sagte es
    niemand. Deshalb geht die Rechnung hier sichtbar auf:
    gesamt = in Frigate + uebertragbar + abgelehnt + geloescht + frueher
             exportiert + abgewaehlt.

    .138 (Panel-Befund): AUCH die System-Karte rendert ihre Sync-Zeile hierueber
    (mit_personen=False laesst die je-Person-Zeile weg) — vorher rechnete sie
    'ready to transfer' selbst und OHNE die gemerkten Ablehnungen, zwei Seiten
    zeigten unter identischer Beschriftung verschiedene Zahlen. Eine Quelle,
    nie ein zweites verstreutes Literal (QS-Ebenen-Regel)."""
    if not bilanz:
        return ""
    n_abl = len(ablehnungen or {})
    n_c = max(0, len(bilanz["kandidaten"]) - n_abl)
    # Stufe-0-Gattung (§8-Fund): die <b>-Zahl steht VOR dem Zaehlertext —
    # Split an der Markup-Grenze, der Schluessel beginnt mit dem Fragment.
    teile = [f'<b>{bilanz["gesamt"]}</b> '
             + t("syncauswahl.bilanz.hauptzeile",
                 beide=len(bilanz["in_beiden"]), bereit=n_c)]
    if n_abl:
        teile.append(t("syncauswahl.bilanz.abgelehnt", n=n_abl))
    if bilanz["geloescht"]:
        teile.append(t("syncauswahl.bilanz.geloescht", n=len(bilanz["geloescht"])))
    if bilanz["api_export"]:
        teile.append(t("syncauswahl.bilanz.exportiert", n=len(bilanz["api_export"])))
    if bilanz["abgewaehlt"]:
        teile.append(t("syncauswahl.bilanz.abgewaehlt", n=len(bilanz["abgewaehlt"])))
    if bilanz.get("vorrat_lokal"):
        # Vorrats-Referenzen (bauplan_vorrat.md B4): Beiwert-basiert, nie
        # Export-Kandidat — hier sichtbar statt still ausgelassen (K3).
        teile.append(t("syncauswahl.bilanz.vorrat", n=len(bilanz["vorrat_lokal"])))
    if bilanz["nur_frigate"]:
        teile.append(t("syncauswahl.bilanz.nur_frigate", n=len(bilanz["nur_frigate"])))
    zeilen = ["<div>" + " · ".join(teile) + "</div>"]
    if mit_personen:
        je = [f'{html.escape(p)} {v["beide"]}/{v["gesamt"]}'
              for p, v in sorted(bilanz["je_person"].items()) if v["gesamt"]]
        if je:
            zeilen.append(f'<div class="dim">{t("syncauswahl.bilanz.je_person")} '
                          + " · ".join(je) + "</div>")
    return "".join(zeilen)


def _abschnitt_geloescht(bilanz):
    """D1-Abschnitt: Entscheidungsfaelle, nach Person sortiert."""
    if not bilanz or not bilanz["geloescht"]:
        return ""
    faelle = sorted(bilanz["geloescht"])
    return (f'<div class="card"><b>{t("syncauswahl.bilanz.geloescht", n=len(faelle))}</b> '
            + t("syncauswahl.geloescht.zusatz")
            + f'<div class="dim">{t("syncauswahl.geloescht.satz")}</div>'
            '<div class="sa-gitter">'
            + "".join(_kachel_geloescht(p, d, g) for p, d, g in faelle)
            + "</div></div>")


def _abschnitt_api(bilanz):
    """D2-Abschnitt: eingeklappt, mit dem ehrlichen Zaehler-Vergleich je Person.
    Aus einer Differenz folgt hier NICHTS automatisch — Frigates Namen sind
    andere, also ist jede Ableitung 'da fehlt eins' eine Vermutung."""
    if not bilanz or not bilanz["api_export"]:
        return ""
    faelle = sorted(bilanz["api_export"])
    personen = sorted({p for p, _d in faelle})
    vergleich = []
    for p in personen:
        v = bilanz["je_person"].get(p) or {}
        n = sum(1 for q, _d in faelle if q == p)
        vergleich.append(t("syncauswahl.api.vergleich", person=html.escape(p),
                           n=n, bestand=v.get("frigate", 0)))
    return ('<div class="card"><details><summary><b>'
            + t("syncauswahl.api.titel", n=len(faelle))
            + "</b> " + t("syncauswahl.aufklapp") + "</summary>"
            + f'<div class="dim">{t("syncauswahl.api.satz")}</div>'
            '<div class="dim" style="margin-top:6px">' + "<br>".join(vergleich)
            + "</div>"
            '<div class="sa-gitter">'
            + "".join(_kachel_api(p, d) for p, d in faelle)
            + "</div></details></div>")


def _abschnitt_import(bilanz):
    """B-Abschnitt: was NUR in Frigate liegt, ueber den BESTEHENDEN Import-Weg
    (syncAktion -> POST /sync_import, derselbe Job-Zweig wie bisher auf der
    System-Karte; von dort ist der Knopf hierher gezogen). Warnung statt
    Automatik: eigene, von Frigate umbenannte Exporte sind hier per Namen NICHT
    von fremden Frigate-Gesichtern zu unterscheiden — und der Import legt eine
    Kopie in der eigenen Bibliothek an, deshalb fragt der Knopf vorher nach."""
    if not bilanz or not bilanz["nur_frigate"]:
        return ""
    faelle = sorted(bilanz["nur_frigate"])
    gruppen = {}
    for p, d in faelle:
        gruppen.setdefault(p, []).append(d)
    zeilen = []
    for p in sorted(gruppen):
        namen = gruppen[p]
        zeilen.append(f'<b>{html.escape(p)}</b> — '
                      + t_n("syncauswahl.import.zeile", len(namen)) + ' '
                      + html.escape(", ".join(namen[:8]))
                      + (" " + t("syncauswahl.import.mehr", n=len(namen) - 8)
                         if len(namen) > 8 else ""))
    return (f'<div class="card"><b>{t("syncauswahl.bilanz.nur_frigate", n=len(faelle))}</b>'
            + f'<div class="dim">{t("syncauswahl.import.satz")}</div>'
            + '<div class="sa-warn" style="margin-top:6px">'
            + t("syncauswahl.import.warnung") + '</div>'
            '<div class="sa-namen" style="margin-top:6px">' + "<br>".join(zeilen)
            + "</div><div style=\"margin-top:8px\">"
            '<button class="gtb" onclick="syncAktion(\'import\',this)">'
            + t("syncauswahl.import.knopf") + "</button></div></div>")


def _alter(ts):
    if not ts:
        return t("syncauswahl.alter.unbekannt")
    s = max(0, int(datetime.datetime.now().timestamp() - ts))
    if s < 90:
        return t("syncauswahl.alter.sekunden", s=s)
    if s < 3600:
        return t("syncauswahl.alter.minuten", m=s // 60)
    return t("syncauswahl.alter.stunden", h=s // 3600, m=s % 3600 // 60)


def ergebnis(bericht):
    """Ergebnis des letzten Transfers je Bild — gruen hochgeladen, rot mit dem
    Grund, den FRIGATE genannt hat (bzw. dem der Vorpruefung). Quelle ist der
    Export-Bericht, nicht die Kandidatenliste: erfolgreich Exportiertes ist
    danach ja gerade KEIN Kandidat mehr."""
    if not bericht:
        return ""
    hoch = bericht.get("exportiert_liste") or []
    weg = bericht.get("uebersprungen") or []
    if not (hoch or weg or bericht.get("abbruch")):
        return ""
    zeilen = []
    if bericht.get("abbruch"):
        zeilen.append(f'<div class="sa-crit"><b>{t("syncauswahl.ergebnis.stopp")}</b> '
                      + html.escape(str(bericht["abbruch"])) + "</div>")
    if bericht.get("hinweis"):
        zeilen.append('<div class="sa-warn">' + html.escape(str(bericht["hinweis"])) + "</div>")
    if bericht.get("wand_verdacht"):
        zeilen.append('<div class="sa-warn">'
                      + t("syncauswahl.ergebnis.wand",
                          fehler=html.escape(str(bericht["wand_verdacht"]))) + "</div>")
    for e in hoch[:200]:
        zeilen.append('<div class="sa-ok">&#10003; '
                      + t("syncauswahl.ergebnis.hochgeladen",
                          bild=html.escape(f'{e.get("person", "?")}/{e.get("datei", "?")}'))
                      + "</div>")
    for e in weg[:200]:
        zeilen.append('<div class="sa-crit">&#10007; '
                      + html.escape(f'{e.get("person", "?")}/{e.get("datei", "?")}')
                      + " — " + html.escape(str(e.get("fehler") or "?")) + "</div>")
    mehr = max(0, len(hoch) - 200) + max(0, len(weg) - 200)
    if mehr:
        # Stufe-0-Grenze: <a>-Link mitten im Satz — bleibt literal.
        zeilen.append(f'<div class="dim">… and {mehr} more (full list in the '
                      '<a href="/sync_diagnose" target="_blank">diagnosis</a>)</div>')
    bilanz = (t("syncauswahl.ergebnis.zaehler", hoch=len(hoch), weg=len(weg))
              + (" · " + t("syncauswahl.ergebnis.auswahl", n=bericht.get("auswahl_n"))
                 if bericht.get("auswahl_n") else "")
              + (" · " + t("syncauswahl.ergebnis.uebersprungen", n=bericht.get("abgewaehlt_n"))
                 if bericht.get("abgewaehlt_n") else ""))
    return (f'<div class="card"><b>{t("syncauswahl.ergebnis.titel")}</b> '
            f'<span class="dim">({_alter(bericht.get("ts"))}'
            + (", " + t("syncauswahl.ergebnis.dauer", n=bericht.get("dauer_s"))
               if bericht.get("dauer_s") is not None else "")
            + f')</span><div>{bilanz}</div>'
            f'<div style="margin-top:6px;max-height:340px;overflow:auto">{"".join(zeilen)}</div>'
            "</div>")


def render(kandidaten, urteile, abwahl, pruef_status, bericht=None, fehler="",
           schreibsperre=False, bilanz=None, ablehnungen=None, fr=None):
    """kandidaten = [(person, datei), …] ALLE Export-Kandidaten (inkl. abgewaehlter);
    urteile = {schluessel: {"ok", "grund"}} nur GUELTIGE Urteile (mtime passt);
    abwahl  = {schluessel: …} bewusst Abgewaehltes;
    pruef_status = {"laeuft", "gesamt", "fertig", "fehler"} des Hintergrund-Laufs;
    bericht = letzter Export-Bericht oder None; fehler = Klartext, wenn die
    Kandidaten gar nicht ermittelbar waren; schreibsperre = frigate_read_only;
    bilanz = sync_refs.abgleich()-Ergebnis oder None (.137 — ohne es rendert die
    Seite genau wie in .133/.134, die Vier-Klassen-Abschnitte entfallen dann);
    ablehnungen = {schluessel: merker} gemerkte FRIGATE-Ablehnungen (D3);
    fr = (an, detail) Live-Zustand von Frigates Gesichtserkennung."""
    ablehnungen = ablehnungen or {}
    teile = [f"<h2>{t('syncauswahl.titel')}</h2>",
             f'<p class="sub">{t("syncauswahl.kopf.satz")}</p>']
    if fehler:
        return (STIL + "".join(teile)
                + f'<div class="card"><b>{t("syncauswahl.fehler.titel")}</b><br>'
                f'<span class="dim">{t("syncauswahl.fehler.satz")}</span><br><small>'
                + html.escape(fehler[:200]) + "</small><br><small>"
                f'<a href="/sync_diagnose" target="_blank">{t("syncauswahl.link_diagnose_auf")}</a> · '
                f'<a href="/system">{t("syncauswahl.link_system")}</a></small></div>')

    teile.append(_fr_zeile(fr))
    aktive = [(p, d) for p, d in kandidaten if _k(p, d) not in abwahl]
    raus = [(p, d) for p, d in kandidaten if _k(p, d) in abwahl]
    n_ok = n_offen = n_abl = 0
    for p, d in aktive:
        if _k(p, d) in ablehnungen:      # Frigates eigenes Urteil steht ueber allem
            n_abl += 1
            continue
        u = urteile.get(_k(p, d))
        if u is None:
            n_offen += 1
        elif u.get("ok"):
            n_ok += 1
    n_raus_pruef = len(aktive) - n_ok - n_offen - n_abl
    # Erst-Auswahl = bestandene Vorpruefung; Ungepruefte zaehlen mit, solange kein
    # Urteil vorliegt (genau das macht auch _kachel — eine Regel, zwei Orte).
    # Gemerkte Frigate-Ablehnungen starten aus (.137 Schleifen-Fix).
    vorgewaehlt = n_ok + n_offen

    pruef = ""
    if pruef_status.get("fehler"):
        pruef = ('<div class="sa-warn">'
                 + t("syncauswahl.pruef.fehler",
                     fehler=html.escape(str(pruef_status["fehler"])[:200]))
                 + "</div>")
    elif n_offen:
        pruef = ('<div id="sa-pruef" class="dim">'
                 + t_n("syncauswahl.pruef.laeuft", n_offen,
                       fertig=pruef_status.get("fertig", 0),
                       gesamt=pruef_status.get("gesamt", n_offen))
                 + "</div>")
    teile.append(
        f'<div class="card"><b>{t("syncauswahl.bilanz.titel")}</b>'
        # Zuerst die GESAMT-Bilanz ueber alle Klassen (.137), darunter die
        # Detailzeile der Kandidaten — die eine erklaert den Bestand, die andere
        # den Knopf darunter.
        + bilanz_zeile(bilanz, ablehnungen)
        + f'<div>{t_n("syncauswahl.bilanz.kandidaten", len(kandidaten))} · '
        + t("syncauswahl.bilanz.vorpruefung", n=n_ok)
        + f' · <b id="sa-gewaehlt">{vorgewaehlt}</b> {t("syncauswahl.bilanz.gewaehlt_wort")} · '
        + t("syncauswahl.bilanz.abgewaehlt", n=len(raus)) + '</div>'
        + (f'<div class="dim">{t("syncauswahl.bilanz.wohl_abgelehnt", n=n_raus_pruef)}</div>'
           if n_raus_pruef else "")
        + (f'<div class="dim">{t("syncauswahl.bilanz.frueher_abgelehnt", n=n_abl)}</div>'
           if n_abl else "")
        + pruef + "</div>")

    if schreibsperre:
        # Stufe-0-Grenze: der Satzrest mit <a>-Link bleibt literal.
        teile.append(f'<div class="card"><b>{t("syncauswahl.sperre.titel")}</b><br>'
                     f'<span class="dim">{t("syncauswahl.sperre.satz")} Turn '
                     'writing on with the switch on the <a href="/system">System page</a> '
                     "to transfer references.</span></div>")
    if aktive:
        teile.append(
            f'<p><button class="gtb" onclick="syncAuswahlAlle(1)">{t("syncauswahl.knopf_alle")}</button> '
            f'<button class="gtb" onclick="syncAuswahlAlle(0)">{t("syncauswahl.knopf_keine")}</button> '
            f'<button class="gtb on" id="sa-start" onclick="syncAuswahlStart(this)"'
            f'{" disabled" if schreibsperre else ""}>'
            + t("syncauswahl.knopf_transfer", n=vorgewaehlt)
            + '</button> <span id="sa-status" class="dim"></span></p>')
    else:
        teile.append(f'<div class="leer"><b>{t("syncauswahl.leer.titel")}</b><br><small>'
                     + t("syncauswahl.leer.satz")
                     + (" " + t("syncauswahl.leer.zusatz")
                        if bilanz and (bilanz["geloescht"] or bilanz["api_export"]) else "")
                     + "</small></div>")

    gruppen = {}
    for p, d in aktive:
        gruppen.setdefault(p, []).append(d)
    for person in sorted(gruppen):
        dateien = gruppen[person]
        g_abl = sum(1 for d in dateien if _k(person, d) in ablehnungen)
        g_ok = sum(1 for d in dateien if _k(person, d) not in ablehnungen
                   and (urteile.get(_k(person, d)) or {}).get("ok"))
        g_offen = sum(1 for d in dateien if _k(person, d) not in ablehnungen
                      and urteile.get(_k(person, d)) is None)
        g_raus = len(dateien) - g_ok - g_offen - g_abl
        teile.append(
            f'<div class="card"><b>{html.escape(person)}</b> — '
            + t_n("syncauswahl.bilanz.kandidaten", len(dateien))
            + ' · ' + t("syncauswahl.bilanz.vorpruefung", n=g_ok)
            + (' · ' + t("syncauswahl.gruppe.wohl_abgelehnt", n=g_raus) if g_raus else "")
            + (' · ' + t("syncauswahl.bilanz.abgelehnt", n=g_abl) if g_abl else "")
            + (' · ' + t("syncauswahl.gruppe.prueft", n=g_offen) if g_offen else "")
            + '<div class="sa-gitter">'
            + "".join(_kachel(person, d, urteile.get(_k(person, d)),
                              ablehnungen.get(_k(person, d))) for d in dateien)
            + "</div></div>")

    teile.append(_abschnitt_geloescht(bilanz))
    teile.append(_abschnitt_api(bilanz))
    teile.append(_abschnitt_import(bilanz))

    if raus:
        teile.append(
            f'<div class="card"><details><summary><b>'
            + t("syncauswahl.bilanz.abgewaehlt", n=len(raus)) + '</b> '
            + t("syncauswahl.aufklapp")
            + f'</summary><div class="dim">{t("syncauswahl.raus.satz")}</div>'
            '<div class="sa-gitter">'
            + "".join(_kachel_abgewaehlt(p, d) for p, d in sorted(raus))
            + "</div></details></div>")

    teile.append(ergebnis(bericht))
    teile.append(f'<p><a href="/system">{t("syncauswahl.link_system")}</a> · '
                 f'<a href="/sync_diagnose" target="_blank">{t("syncauswahl.link_diagnose")}</a></p>')
    return STIL + "".join(teile)
