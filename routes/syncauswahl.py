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
"""
import datetime
import html
import urllib.parse

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
        badge = ('<span class="sa-badge sa-crit">Frigate rejected: '
                 + html.escape(str(ablehnung.get("fehler") or "no reason given")[:160])
                 + "</span>")
        an = False
    elif urteil is None:
        badge = '<span class="sa-badge dim">checking …</span>'
        an = True                       # ohne Urteil bleibt es beim alten Verhalten
    elif urteil.get("ok"):
        badge = '<span class="sa-badge sa-ok">pre-check ok</span>'
        an = True
    else:
        # User-Vorgabe: voraussichtliche Ablehnungen starten ABGEWAEHLT, bleiben
        # aber anklickbar — Frigates Urteil ist die Wahrheit, unser Detektor ist
        # ein anderes Modell und darf kein Bild endgueltig aussperren.
        badge = ('<span class="sa-badge sa-warn">would likely be rejected: '
                 + html.escape(str(urteil.get("grund") or "no face detectable"))
                 + "</span>")
        an = False
    return (f'<span class="sa-b">'
            f'<img src="{_bildpfad(person, datei)}" alt="" loading="lazy">'
            f'<label class="sa-l"><input type="checkbox" class="sa-cb"'
            f'{_daten(person, datei)} onchange="syncAuswahlZaehlen()"'
            f'{" checked" if an else ""}> send</label>'
            f'{badge}'
            f'<button class="gtb"{_daten(person, datei)} onclick="syncAbwahl(this,1)" '
            f'title="Never send this image — remembered, the automatic sync skips it too">'
            f'skip</button></span>')


def _kachel_abgewaehlt(person, datei):
    return (f'<span class="sa-b sa-raus">'
            f'<img src="{_bildpfad(person, datei)}" alt="" loading="lazy">'
            f'<span class="sa-badge dim">{html.escape(person)}</span>'
            f'<button class="gtb"{_daten(person, datei)} onclick="syncAbwahl(this,0)" '
            f'title="Put this image back on the candidate list">restore</button></span>')


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
    satz = ("came from Frigate and is gone there now" if grund == D1_IMPORT else
            "was sent under this exact name and is gone there now")
    return (f'<span class="sa-b sa-weit">'
            f'<img src="{_bildpfad(person, datei)}" alt="" loading="lazy">'
            f'<span class="sa-badge sa-warn">deleted in Frigate</span>'
            f'<span class="sa-badge dim">{html.escape(person)} — {satz}</span>'
            + _knopf(person, datei, "syncWiederAnbieten(this)", "offer again",
                     "Put it back on the candidate list — the next sync (manual "
                     "or automatic) sends it again")
            + _knopf(person, datei, "syncAbwahl(this,1)", "respect the deletion",
                     "Remember that this image should stay out of Frigate")
            + "</span>")


def _kachel_api(person, datei):
    """D2 — per API exportiert: Frigate fuehrt das Bild unter EIGENEM Namen, ein
    Namensabgleich kann nicht sagen, ob es drueben noch liegt. Nur eine Aktion."""
    return (f'<span class="sa-b sa-weit">'
            f'<img src="{_bildpfad(person, datei)}" alt="" loading="lazy">'
            f'<span class="sa-badge dim">{html.escape(person)} — sent earlier</span>'
            + _knopf(person, datei, "syncWiederAnbieten(this)", "offer again",
                     "Put it back on the candidate list (sends a second copy if "
                     "Frigate still has the first one)")
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
        return ('<div class="card"><b>Frigate face recognition: unknown</b><br>'
                '<span class="dim">suslik could not read it from Frigate just now — '
                + html.escape(str(detail)[:160]) + ". Sending may still work; "
                "Frigate has the last word either way.</span></div>")
    if an:
        return ('<div class="card"><b>Frigate face recognition: on</b> '
                '<span class="dim">(read from Frigate as this page loaded) — it '
                "accepts reference uploads.</span></div>")
    return ('<div class="card"><b>Frigate face recognition: off</b><br>'
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
    teile = [f'<b>{bilanz["gesamt"]}</b> reference images · '
             f'{len(bilanz["in_beiden"])} already in Frigate · '
             f'{n_c} ready to transfer']
    if n_abl:
        teile.append(f"{n_abl} rejected by Frigate")
    if bilanz["geloescht"]:
        teile.append(f'{len(bilanz["geloescht"])} deleted in Frigate')
    if bilanz["api_export"]:
        teile.append(f'{len(bilanz["api_export"])} sent earlier (Frigate renamed them)')
    if bilanz["abgewaehlt"]:
        teile.append(f'{len(bilanz["abgewaehlt"])} deselected')
    if bilanz["nur_frigate"]:
        teile.append(f'{len(bilanz["nur_frigate"])} only in Frigate')
    zeilen = ["<div>" + " · ".join(teile) + "</div>"]
    if mit_personen:
        je = [f'{html.escape(p)} {v["beide"]}/{v["gesamt"]}'
              for p, v in sorted(bilanz["je_person"].items()) if v["gesamt"]]
        if je:
            zeilen.append('<div class="dim">In Frigate, per person: ' + " · ".join(je)
                          + "</div>")
    return "".join(zeilen)


def _abschnitt_geloescht(bilanz):
    """D1-Abschnitt: Entscheidungsfaelle, nach Person sortiert."""
    if not bilanz or not bilanz["geloescht"]:
        return ""
    faelle = sorted(bilanz["geloescht"])
    return (f'<div class="card"><b>{len(faelle)} deleted in Frigate</b> — your decision'
            '<div class="dim">These are still in your library, but Frigate no longer '
            "has them under the name they were stored with. suslik never re-sends "
            "them without your decision: deleting a face in Frigate can be "
            "deliberate. Offer it again to make it a normal candidate — from then "
            "on the next sync, including the automatic one, uploads it. Respect "
            "the deletion to keep it out for good.</div>"
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
        vergleich.append(f'{html.escape(p)}: {n} sent this way · Frigate currently '
                         f'holds {v.get("frigate", 0)} images')
    return ('<div class="card"><details><summary><b>' + str(len(faelle))
            + " exported earlier — Frigate keeps these under its own names"
            "</b> — show</summary>"
            '<div class="dim">These went up through Frigate\'s API, and Frigate '
            "renames every reference it accepts. suslik therefore cannot tell by "
            "name whether they are still there — no count on this page can prove "
            "it either way. Nothing is re-sent automatically; if you know one is "
            "missing, offer it again (that sends a second copy if the first one "
            "is still there).</div>"
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
        zeilen.append(f'<b>{html.escape(p)}</b> — {len(namen)} image'
                      f'{"s" if len(namen) != 1 else ""}: '
                      + html.escape(", ".join(namen[:8]))
                      + (f" … and {len(namen) - 8} more" if len(namen) > 8 else ""))
    return (f'<div class="card"><b>{len(faelle)} only in Frigate</b>'
            '<div class="dim">Frigate has these reference images, suslik does not. '
            "Importing copies them into your library; nothing in Frigate changes.</div>"
            '<div class="sa-warn" style="margin-top:6px">This list may include your '
            "own uploads: Frigate renames every reference it accepts, so suslik "
            "cannot tell them apart from faces you added in Frigate directly. "
            "Importing those back would duplicate content.</div>"
            '<div class="sa-namen" style="margin-top:6px">' + "<br>".join(zeilen)
            + "</div><div style=\"margin-top:8px\">"
            '<button class="gtb" onclick="syncAktion(\'import\',this)">'
            "Import them into suslik</button></div></div>")


def _alter(ts):
    if not ts:
        return "age unknown"
    s = max(0, int(datetime.datetime.now().timestamp() - ts))
    if s < 90:
        return f"{s} s ago"
    if s < 3600:
        return f"{s // 60} min ago"
    return f"{s // 3600} h {s % 3600 // 60} min ago"


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
        zeilen.append('<div class="sa-crit"><b>stopped:</b> '
                      + html.escape(str(bericht["abbruch"])) + "</div>")
    if bericht.get("hinweis"):
        zeilen.append('<div class="sa-warn">' + html.escape(str(bericht["hinweis"])) + "</div>")
    if bericht.get("wand_verdacht"):
        zeilen.append('<div class="sa-warn">same error three times in a row: '
                      + html.escape(str(bericht["wand_verdacht"])) + "</div>")
    for e in hoch[:200]:
        zeilen.append('<div class="sa-ok">&#10003; uploaded — '
                      + html.escape(f'{e.get("person", "?")}/{e.get("datei", "?")}') + "</div>")
    for e in weg[:200]:
        zeilen.append('<div class="sa-crit">&#10007; '
                      + html.escape(f'{e.get("person", "?")}/{e.get("datei", "?")}')
                      + " — " + html.escape(str(e.get("fehler") or "?")) + "</div>")
    mehr = max(0, len(hoch) - 200) + max(0, len(weg) - 200)
    if mehr:
        zeilen.append(f'<div class="dim">… and {mehr} more (full list in the '
                      '<a href="/sync_diagnose" target="_blank">diagnosis</a>)</div>')
    bilanz = (f'{len(hoch)} uploaded · {len(weg)} not accepted'
              + (f' · of {bericht.get("auswahl_n")} selected'
                 if bericht.get("auswahl_n") else "")
              + (f' · {bericht.get("abgewaehlt_n")} deselected (skipped)'
                 if bericht.get("abgewaehlt_n") else ""))
    return ('<div class="card"><b>Last transfer</b> '
            f'<span class="dim">({_alter(bericht.get("ts"))}'
            + (f', took {bericht.get("dauer_s")} s' if bericht.get("dauer_s") is not None else "")
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
    teile = ["<h2>Review &amp; sync — references to Frigate</h2>",
             '<p class="sub">Frigate runs every uploaded reference through its own face '
             "detector and refuses images it finds no face in. This page checks the same "
             "thing first, shows you every candidate, and sends only what you tick.</p>"]
    if fehler:
        return (STIL + "".join(teile)
                + '<div class="card"><b>Candidates not available</b><br>'
                '<span class="dim">The candidate list needs a reachable Frigate — its '
                "face library is one half of the comparison.</span><br><small>"
                + html.escape(fehler[:200]) + "</small><br><small>"
                '<a href="/sync_diagnose" target="_blank">open the diagnosis</a> · '
                '<a href="/system">back to System</a></small></div>')

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
        pruef = ('<div class="sa-warn">pre-check could not run: '
                 + html.escape(str(pruef_status["fehler"])[:200])
                 + " — images without a verdict stay selected.</div>")
    elif n_offen:
        pruef = (f'<div id="sa-pruef" class="dim">checking {n_offen} image'
                 f'{"s" if n_offen != 1 else ""} … '
                 f'{pruef_status.get("fertig", 0)}/{pruef_status.get("gesamt", n_offen)}'
                 " (this page reloads when it is done)</div>")
    teile.append(
        '<div class="card"><b>Balance</b>'
        # Zuerst die GESAMT-Bilanz ueber alle Klassen (.137), darunter die
        # Detailzeile der Kandidaten — die eine erklaert den Bestand, die andere
        # den Knopf darunter.
        + bilanz_zeile(bilanz, ablehnungen)
        + f'<div>{len(kandidaten)} candidate{"s" if len(kandidaten) != 1 else ""} · '
        f'{n_ok} pass the pre-check · <b id="sa-gewaehlt">{vorgewaehlt}</b> selected · '
        f'{len(raus)} deselected</div>'
        + (f'<div class="dim">{n_raus_pruef} would likely be rejected by Frigate '
           "(unticked, but you can still send them).</div>" if n_raus_pruef else "")
        + (f'<div class="dim">{n_abl} were rejected by Frigate before (unticked; '
           "ticking one tries it again).</div>" if n_abl else "")
        + pruef + "</div>")

    if schreibsperre:
        teile.append('<div class="card"><b>Read-only mode is on</b><br>'
                     '<span class="dim">suslik does not write to Frigate right now. Turn '
                     'writing on with the switch on the <a href="/system">System page</a> '
                     "to transfer references.</span></div>")
    if aktive:
        teile.append(
            '<p><button class="gtb" onclick="syncAuswahlAlle(1)">Select all</button> '
            '<button class="gtb" onclick="syncAuswahlAlle(0)">Deselect all</button> '
            f'<button class="gtb on" id="sa-start" onclick="syncAuswahlStart(this)"'
            f'{" disabled" if schreibsperre else ""}>Transfer {vorgewaehlt} selected to '
            'Frigate</button> <span id="sa-status" class="dim"></span></p>')
    else:
        teile.append('<div class="leer"><b>Nothing to send</b><br><small>Every reference '
                     "either already reached Frigate or is deselected."
                     + (" The sections below list what cannot simply be transferred."
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
            f'<div class="card"><b>{html.escape(person)}</b> — {len(dateien)} candidate'
            f'{"s" if len(dateien) != 1 else ""} · {g_ok} pass the pre-check'
            + (f' · {g_raus} likely rejected' if g_raus else "")
            + (f' · {g_abl} rejected by Frigate' if g_abl else "")
            + (f' · {g_offen} still checking' if g_offen else "")
            + '<div class="sa-gitter">'
            + "".join(_kachel(person, d, urteile.get(_k(person, d)),
                              ablehnungen.get(_k(person, d))) for d in dateien)
            + "</div></div>")

    teile.append(_abschnitt_geloescht(bilanz))
    teile.append(_abschnitt_api(bilanz))
    teile.append(_abschnitt_import(bilanz))

    if raus:
        teile.append(
            f'<div class="card"><details><summary><b>{len(raus)} deselected</b> — show'
            "</summary><div class=\"dim\">Remembered on purpose: these stay in your "
            "library but are never sent to Frigate, not even by the automatic sync. "
            "Restore puts one back on the candidate list.</div>"
            '<div class="sa-gitter">'
            + "".join(_kachel_abgewaehlt(p, d) for p, d in sorted(raus))
            + "</div></details></div>")

    teile.append(ergebnis(bericht))
    teile.append('<p><a href="/system">back to System</a> · '
                 '<a href="/sync_diagnose" target="_blank">diagnosis</a></p>')
    return STIL + "".join(teile)
