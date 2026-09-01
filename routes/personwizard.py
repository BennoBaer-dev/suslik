"""routes/personwizard — Person-Learn-Assistent (PE1, stufe2.md: des Users
Schritt-1-Ablauf = Wunsch-N Events + gezielte Personen-Auswahl, danach
Klick-Abnahme; Erstlauf klein anfangen. Onboarding-Prosa 04.08.: der User
wird an die Hand genommen — was passiert, was entscheidet er, warum muss
erst mindestens eine Person gelernt sein, bevor der Strang aktiv wird).

Kontrakt wie alle routes-Module: reine Renderer, Daten als Parameter, kein
Dienst-Import; Seiteneffekte (Events zaehlen, Lauf anlegen, Thread/Worker)
macht der Handler in verifyd.py.

Design-Nachzug 20.08.: /personlauf (wizard) traegt jetzt DASSELBE Lauf-Design
wie der Gesichts-Lernlauf (routes/lernwizard.lauf_seite, Mockup-Abnahmen
17./18.08.) — Vier-Kachel-Fluss, Fortschritts-Saeule, Suchknopf mit
Einstellungs-Popup, Handlungs-Band. Das CSS-Blatt kommt aus DERSELBEN Quelle
(webui.bausteine.lauffluss_stil), die Klassen sind dieselben; es gibt keine
Parallel-Klassen und keine zweite Design-Fassung. Reine Darstellung: Weichen,
Zaehler, Texte und die Routen-/POST-Vertraege blieben unangetastet. Die
uebrigen Seiten dieses Moduls (abnahme_seite/kontrolle_seite/bestand_seite/
modell_seite) sind vom Nachzug NICHT beruehrt.

Sprach-Stufe 2 (Tranche C, konzept_sprache.md v2): sichtbare Texte aus
core/sprache.t()/t_n() — BYTE-TREU (Harnisch tools/harnisch_sprache.py).
Die reinen §8.1-Prosa-Saetze (<b>/<a>/<code> mitten im Satz) sind seit
Stufe 3 t_html-Schluessel. Verbleibende Grenzen (Kommentar je Fundstelle):
die 0-Events-Diagnose (KEIN reiner §8.1-Fall: konditionales Satzteil-
Splicing §8.3 + B19-Datumsformate + konditionaler Plural — der Ganz-Satz-
Umbau je Zweig ist eine BEWUSSTE Byte-Aenderung, eigener Zug), Inline-JS
der Abnahme-/Bestands-/Modell-Seite (confirm/alert-Texte, §8.4 Tranche D),
Datumsformate %d.%m./%d %b %Y/%a (B19); "FREMD" ist Speicher-Kennung und
wird nie uebersetzt (§8.2)."""
import datetime
import html
import json
import urllib.parse

from core.sprache import t, t_html, t_n
from webui.bausteine import js_literal, lauffluss_stil


def _wer_text(p):
    """.147: Anzeige-Name einer Lauf-Wahl — '' = alle, 'FREMD' = der
    reservierte Fremd-Sammel-Lauf, sonst der (escapte) Personenname."""
    if not p:
        return t("personwizard.wer.alle")
    if p == "FREMD":
        return t("personwizard.wer.fremde")
    return html.escape(p)


def _dt(ts):
    """Startzeit der Lauf-Kachel — dasselbe Format wie im Gesichts-Lernlauf
    (routes/lernwizard._dt); Datumsformat bleibt in der Route (B19-Stufe)."""
    return (datetime.datetime.fromtimestamp(ts).strftime("%a %d.%m. %H:%M")
            if ts else "—")


def _kachel(nr, zust, titel, inhalt):
    """Eine Fluss-Kachel (Bauform .246, Mockup-Abnahme 17.08.): Nummern-Kugel
    (bzw. Haken, wenn erledigt) + Titel + Inhalt. Spiegelt lernwizard._kachel
    Zeichen fuer Zeichen — dieselbe Bauform, damit beide Lernlaeufe gleich
    aussehen."""
    mark = "&#10003;" if zust == "fertig" else str(nr)
    return (f'<div class="lf-k {zust}"><h3><span class="nr">{mark}</span>'
            f'{titel}</h3>{inhalt}</div>')


def _seg(zust, label):
    """Phasen-Marke neben der Fortschritts-Saeule (Bauform lernwizard._seg_html):
    Haken = erledigt, Puls = laeuft gerade, Punkt = steht noch aus."""
    m = ('<span class="phok">&#10003;</span>' if zust == "ok" else
         ('<span class="lf-puls"></span>' if zust == "an" else
          '<span class="dim">&#183;</span>'))
    return f'<div class="{zust}">{m} {label}</div>'


def _erklaer_karte():
    """Das Onboarding aus der alten Kopf-Karte (04.08.) — im Fluss-Design
    Expert-Tiefe: die vier Schritte erzaehlen jetzt die vier Kacheln, der
    Langtext bleibt VOLL erhalten (nie loeschen, nur ausblenden — Muster
    lernwizard nur-expert)."""
    return (f'<div class="card nur-expert"><b>{t("personwizard.kopf.wie_titel")}</b>'
            f'<div>{t("personwizard.kopf.schritt1")}<br>'
            f'{t("personwizard.kopf.schritt2")}<br>'
            f'{t("personwizard.kopf.schritt3")}<br>'
            f'{t("personwizard.kopf.schritt4")}</div>'
            # Stufe 3 (t_html): der Staerke-Absatz mit <b>-Vorsatz + <b>many
            # different days</b> mitten im Satz.
            f'<div style="margin-top:6px">{t_html("personwizard.kopf.stark_satz")}</div>'
            f'<div class="dim" style="margin-top:6px">{t("personwizard.kopf.tempo")}</div>'
            f'<div class="dim">{t("personwizard.kopf.warum")}</div></div>')


def wizard(personen, auswahl_n, person_wahl, bilanz=None, lauf=None,
           modell=None, max_events=40000):
    """Wizard-Ansicht Person Learn.
    personen     Liste bekannter Personen-Namen (aus dem Gesichts-Bestand)
    auswahl_n    gewaehlte Event-Zahl (int) oder None
    person_wahl  gewaehlte Person (Name) oder "" = alle
    bilanz       optional dict(n[, gebunden, fremd]) vom Handler
    lauf         personlauf.json-Zustand (dict) oder None

    Darstellung seit 20.08. = das Lauf-Design des Gesichts-Lernlaufs
    (.246/.259, Mockup-Abnahmen 17./18.08.): Vier-Kachel-Fluss (Lauf ->
    Sammeln -> Pruefen -> Fertig), Fortschritts-Saeule mit Phasen-Marken,
    EIN gruener Suchknopf mit Einstellungs-Popup, die offene Handlung als
    Band ueber die ganze Zeile. CSS-Klassen kommen aus DERSELBEN Quelle wie
    dort (webui.bausteine.lauffluss_stil) — keine Parallel-Klassen.

    Reine Darstellungs-Angleichung: Phasen-Weichen, Zaehler, Texte und die
    POST-/GET-Vertraege sind unveraendert. Insbesondere bleibt
      * die Auswahl-Strecke waehrend Lauf UND offenem Review ausgeblendet
        (gefuehrter Fluss, User 04.08. — frueher drei early-returns, jetzt
        die Weiche start_frei),
      * das Dropdown weiter id="pl-person" und die Statuszeile id="pl-status"
        (app.js personlaufStart liest beide),
      * der Umfangs-Klick ein GET auf /personlauf?events=N&person=… (die
        Person wird beim KLICK live aus dem Dropdown gelesen, User-Fund
        04.08.), der Start danach personlaufStart(N, this)."""
    lauf = lauf or {}
    phase = lauf.get("phase")
    laeuft = phase in ("vorbereitung", "ernte")
    review = phase == "abnahme"
    # 0-Events-Zweig: Bedingung woertlich wie vorher (Lauf lief, aber weder
    # geerntet noch beurteilt) — er bekommt seine eigene Erklaer-Karte.
    leer_lauf = (phase == "fertig" and not lauf.get("events")
                 and not lauf.get("abgenommen") and not lauf.get("verworfen"))
    fertig = phase == "fertig" and not leer_lauf
    start_frei = not (laeuft or review)
    hat_bilanz = bool(start_frei and auswahl_n and bilanz)
    wer_lauf = _wer_text(lauf.get("person"))

    # --- Kachel-Zustaende (dran | fertig | folgt) -------------------------
    if laeuft:
        kz = ["fertig", "dran", "folgt", "folgt"]
    elif review:
        kz = ["fertig", "fertig", "dran", "folgt"]
    elif fertig:
        kz = ["fertig", "fertig", "fertig", "dran"]
    elif leer_lauf:
        # Der Lauf lief und sammelte — nur gab es nichts zu binden; der
        # naechste Zug ist wieder ein Lauf.
        kz = ["dran", "fertig", "folgt", "folgt"]
    else:                          # kein Lauf / unterbrochen / fehler
        kz = ["dran", "folgt", "folgt", "folgt"]
    if hat_bilanz:
        # Umfang gewaehlt: der offene Zug ist der Start — genau EINE Kachel
        # traegt "dran" (Bauform-Regel des Fluss-Designs).
        kz = ["dran"] + ["fertig" if z == "dran" else z for z in kz[1:]]

    # --- Suchknopf + Einstellungs-Popup ----------------------------------
    # Wer + Umfang wohnen zusammen im Popup (Bauform .259): EIN Deck fuer die
    # ganze Seite, mehrere Oeffner. Die Feld-IDs bleiben die alten (pl-*),
    # damit der app.js-Vertrag unangetastet bleibt.
    opts = ([f'<option value="">{t("personwizard.auswahl.opt_alle")}</option>',
             '<option value="FREMD"'
             + (" selected" if person_wahl == "FREMD" else "")
             + f'>{t("personwizard.auswahl.opt_fremde")}</option>']
            + [f'<option value="{html.escape(p, quote=True)}"'
               f'{" selected" if p == person_wahl else ""}>'
               f"{html.escape(p)}</option>"
               for p in personen])
    # Presets/Formular lesen die Person beim KLICK live aus dem Dropdown —
    # der server-seitige Wert ist veraltet, sobald der User umwaehlt, und
    # warf die Auswahl sonst auf "alle" zurueck (User-Fund 04.08.).
    knoepfe = "".join(
        f'<a class="gtb{" on" if auswahl_n == n else ""}" '
        f'href="/personlauf?events={n}" onclick="this.href+='
        "'&person='+encodeURIComponent("
        "document.getElementById('pl-person').value)\">"
        f'{t("personwizard.umfang.knopf_letzte", n=n)}</a> '
        for n in (50, 100, 200))
    eigen = ('<form action="/personlauf" method="get" '
             'style="display:inline;margin-left:10px" onsubmit="'
             "this.person.value=document.getElementById('pl-person').value\">"
             f'<input name="events" type="number" min="1" max="{int(max_events)}"'
             f' size="6" value="{auswahl_n or ""}" placeholder="{t("personwizard.umfang.attr_eigen")}"> '
             f'<input type="hidden" name="person" value="'
             f'{html.escape(person_wahl or "", quote=True)}">'
             f'<button class="gtb">{t("personwizard.umfang.knopf_go")}</button></form>')
    such_deck = (
        '<div id="pl-deck" class="lf-deck" '
        'onclick="if(event.target===this)this.style.display=\'none\'">'
        f'<div class="lf-pop"><h3>{t("personwizard.such.titel")}</h3>'
        f'<div class="lf-popz"><b>{t("personwizard.auswahl.titel")}</b> '
        f'<select id="pl-person">{"".join(opts)}</select>'
        '<span class="lf-hint">' + t("personwizard.auswahl.satz") + '</span>'
        '<span class="lf-hint">' + t("personwizard.auswahl.fremde_satz")
        + '</span></div>'
        f'<div class="lf-popz"><b>{t("personwizard.umfang.titel")}</b>'
        f'<div style="flex-basis:100%">{knoepfe}{eigen}</div>'
        '<span class="lf-hint">' + t("personwizard.umfang.satz")
        + '</span></div>'
        '<div class="lf-popf"><span class="lf-spacer"></span>'
        # "Cancel" wortgleich aus dem Gesichts-Lernlauf (byte-identischer
        # EN-Text, dieselbe Rolle im selben Popup).
        '<button type="button" class="gtb" '
        'onclick="document.getElementById(\'pl-deck\').style.display=\'none\'">'
        + t("lernwizard.knopf_abbrechen") + '</button></div></div></div>')

    def _oeffner(klasse, text, klein=""):
        """Ein Popup-Oeffner. GROSS und gruen (.lf-such), solange das Popup
        die eine offene Handlung ist; als ruhiger .gtb, sobald der Start-Knopf
        im Band darunter die Hauptsache ist bzw. neben dem Ergebnis-Knopf der
        Fertig-Kachel steht (nie zwei grosse gruene Knoepfe auf einer Seite —
        der Blick soll EINE Handlung finden)."""
        return ('<button type="button" class="' + klasse + '" '
                'onclick="document.getElementById(\'pl-deck\')'
                '.style.display=\'grid\'">' + text
                + (('<small>' + klein + '</small>') if klein else "")
                + '</button>')

    such_knopf = _oeffner(
        "lf-such", "&#128269;&nbsp; " + t("personwizard.such.titel"),
        # Unterzeile wortgleich aus dem Gesichts-Lernlauf wiederverwendet
        # (byte-identischer EN-Text "looks back through your recordings").
        t("lernwizard.such.klein"))
    aendern_knopf = _oeffner("gtb", t("personwizard.such.titel"))
    neu_knopf = _oeffner("gtb", t("lernwizard.knopf_neuer_lauf"))

    # --- Kachel 1: der Lauf ----------------------------------------------
    if phase:
        # "Run started {wann}" wortgleich aus dem Gesichts-Lernlauf.
        k1 = ('<div><span class="phok">&#10003;</span> '
              + t("lernwizard.k1.gestartet", wann=_dt(lauf.get("ts")))
              + '</div>'
              '<div class="lf-satz nur-expert">'
              + t("lernwizard.k1.scope",
                  n=lauf.get("events", lauf.get("wunsch_n", "?")))
              + ' &middot; ' + wer_lauf + '</div>')
    else:
        k1 = f'<p class="lf-satz">{t("personwizard.k1.satz")}</p>'
    # Genau EIN Start-Weg je Zustand: der Oeffner wohnt in Kachel 1, solange
    # sie die aktive ist — steht der offene Zug woanders (Band, Fertig-Kachel),
    # tritt er dorthin zurueck bzw. wird ruhig.
    if start_frei and kz[0] == "dran":
        k1 += ('<div class="lf-rest">'
               + (aendern_knopf if hat_bilanz else such_knopf) + '</div>')

    # --- Kachel 2: die Saeule (Vorbereitung -> Ernte) ---------------------
    # Ehrliche Fuellung: Vorbereitung 0-15 % (die Bindung meldet keinen
    # Zaehler), Ernte 15-100 % proportional zum ECHTEN Event-Zaehler des
    # Lauf-Threads (fortschritt.events/von), danach voll. Nichts geraten.
    fs = lauf.get("fortschritt") or {}
    if phase == "vorbereitung":
        proz, seg_z = 8, ("an", "")
    elif phase == "ernte":
        von = fs.get("von") or lauf.get("events") or 0
        proz = (15 + int(85 * min(1.0, (fs.get("events") or 0) / von))
                if von else 15)
        seg_z = ("ok", "an")
    elif phase in ("abnahme", "fertig"):
        proz, seg_z = 100, ("ok", "ok")
    else:                          # kein Lauf / unterbrochen / fehler
        proz, seg_z = 0, ("", "")
    # "Prepare" wortgleich aus dem Gesichts-Lernlauf (dieselbe Phase, gleicher
    # Text); die zweite Marke traegt den Koerper-Wortschatz.
    saeule = ('<div class="lf-saeule-w"><div class="lf-saeule">'
              '<div class="marke" style="bottom:15%"></div>'
              f'<div class="fuell" style="height:{proz}%"></div></div>'
              '<div class="lf-phasen">'
              + _seg(seg_z[0], t("lernwizard.seg.vorbereiten"))
              + _seg(seg_z[1], t("personwizard.kachel.sammeln"))
              + '</div></div>')
    if phase == "vorbereitung":
        k2 = ('<div><span class="lf-puls"></span> '
              + t("personwizard.vorb.titel") + '</div>'
              + f'<p class="lf-satz">{t("personwizard.vorb.zeile", n=lauf.get("wunsch_n", "?"), wer=wer_lauf)}</p>')
    elif phase == "ernte":
        stand = (t("personwizard.ernte.stand", events=fs.get("events", 0),
                   von=fs.get("von", lauf.get("events", "?")),
                   bilder=fs.get("bilder", 0))
                 if fs else t("personwizard.ernte.startet"))
        k2 = ('<div><span class="lf-puls"></span> '
              + t("personwizard.ernte.titel") + '</div>'
              + f'<p class="lf-satz">{t("personwizard.ernte.zeile", wer=wer_lauf, stand=stand)}</p>')
    else:
        k2 = f'<p class="lf-satz">{t("personwizard.k2.satz")}</p>'
    k2 += saeule + '<div class="lf-rest">'
    if phase == "vorbereitung":
        k2 += f'<div class="lf-satz">{t("personwizard.vorb.satz")}</div>'
    elif phase == "ernte":
        k2 += (f'<div class="lf-satz">{t("personwizard.ernte.satz")}</div>'
               # .261-Bauform: der Abbruch wohnt an der Saeule, nicht am
               # Seitenende — derselbe personlaufAbbruch-Weg wie bisher.
               '<div style="margin-top:6px"><button class="gtb" '
               'onclick="personlaufAbbruch(this)">'
               + t("personwizard.ernte.knopf_abbruch") + '</button> '
               '<span class="dim">'
               + t("personwizard.ernte.abbruch_hinweis") + '</span></div>')
    k2 += "</div>"

    # --- Kachel 3: die Abnahme -------------------------------------------
    if review:
        # Gefuehrter Fluss (User 04.08.): solange das Review aussteht,
        # KEIN neuer Start — die Auswahl-Strecke ist ausgeblendet (start_frei).
        # json.dumps liefert "..." — im doppelt gequoteten onclick-Attribut
        # zerriss das den Aufruf (Knopf tot, User-Fund 04.08.): den ganzen
        # Aufruf als Attributwert escapen (&quot;), der Browser dekodiert
        # Attribute, bevor das JS laeuft.
        _lid = json.dumps(str(lauf.get("lauf_id") or ""))
        _dc = html.escape(f"personlaufVerwerfen({_lid})", quote=True)
        k3 = (f'<div><b>{t("personwizard.abnahme.titel")}</b></div>'
              f'<p class="lf-satz">{t("personwizard.abnahme.zeile", n=lauf.get("geerntet", 0), wer=wer_lauf, lauf=html.escape(str(lauf.get("lauf_id", ""))))}</p>'
              '<div class="lf-rest">'
              # DIE eine Handlung als grosser Knopf (Bauform .lf-such). Als
              # Link statt Button, damit /personlauf/abnahme ein normales Ziel
              # bleibt; text-decoration lokal aus (a:hover unterstreicht sonst).
              '<a class="lf-such" style="text-decoration:none" '
              'href="/personlauf/abnahme">'
              + t("personwizard.abnahme.knopf")
              + '<small>' + t("personwizard.abnahme.hinweis") + '</small></a>'
              # Verwerfen rechtsbuendig abgesetzt in ruhiger roter Umrandung
              # (Bauform .lf-del) — derselbe personlaufVerwerfen-Weg wie bisher.
              '<div class="lf-knoepfe" style="margin-top:8px">'
              '<span class="lf-spacer"></span>'
              f'<button type="button" class="lf-del" onclick="{_dc}">'
              + t("personwizard.abnahme.knopf_verwerfen") + '</button></div>'
              '<div class="lf-satz" style="text-align:right">'
              + t("personwizard.abnahme.verwerfen_hinweis") + '</div></div>')
    else:
        k3 = f'<p class="lf-satz">{t("personwizard.k3.satz")}</p>'

    # --- Kachel 4: Bilanz -------------------------------------------------
    if fertig:
        vw = (lauf.get("diagnose") or {}).get("verwaiste_labels") or {}
        vw_zeile = ("" if not vw else
                    '<div class="lf-satz">'
                    + t("personwizard.fertig.verwaist",
                        liste=", ".join(f"{html.escape(p)} ({n})"
                                        for p, n in vw.items()))
                    + "</div>")
        fremd_zeile = ""
        if lauf.get("person") == "FREMD":
            fremd_zeile = f'<div class="lf-satz">{t("personwizard.fertig.fremd", n=lauf.get("fremd_uebernommen", 0))}</div>'
        k4 = (f'<div><b>{t("personwizard.fertig.titel")}</b></div>'
              f'<div class="lf-satz">{t("personwizard.fertig.zeile", abgenommen=lauf.get("abgenommen", 0), verworfen=lauf.get("verworfen", 0), lauf=html.escape(str(lauf.get("lauf_id", ""))))}</div>'
              + fremd_zeile + vw_zeile
              # .200 (Fix 4): "ships with the next update" war seit PE3 falsch —
              # das Training laeuft automatisch nach jeder Abnahme (personmodell).
              # Stufe 3 (t_html): <a>Model status</a> mitten im Satz —
              # zitiert nav.person_modell (Kopplung am Schluessel).
              + f'<div class="lf-satz">{t_html("personwizard.fertig.training_satz")}</div>'
              '<div class="lf-rest"><a class="gtb on" href="/person">'
              + t("personwizard.fertig.knopf") + '</a>'
              # "start another run below" des Satzes darueber zeigt auf DIESEN
              # Knopf; ist der offene Zug schon woanders (Start-Band), bleibt
              # er weg — der Weg dorthin steht dann in Kachel 1.
              + (" " + neu_knopf if start_frei and kz[3] == "dran" else "")
              + '</div>')
    else:
        k4 = f'<p class="lf-satz">{t("personwizard.k4.satz")}</p>'

    fluss = ('<div class="lf-fluss">'
             # "Learning run" / "Done — they count" wortgleich aus dem
             # Gesichts-Lernlauf (gleiche Rolle, gleicher EN-Text).
             + _kachel(1, kz[0], t("lernwizard.kachel.lauf"), k1)
             + _kachel(2, kz[1], t("personwizard.kachel.sammeln"), k2)
             + _kachel(3, kz[2], t("personwizard.kachel.pruefen"), k3)
             + _kachel(4, kz[3], t("lernwizard.kachel.fertig"), k4)
             + "</div>")

    # --- Meldekarten UEBER dem Fluss (Zustand des letzten Laufs) ----------
    # Sie stehen bewusst oben: ihre Texte verweisen mit "below" auf den
    # Start-Weg, und der liegt im Fluss bzw. im Start-Band darunter.
    melde = []
    if phase == "unterbrochen":
        melde.append(
            f'<div class="card"><span class="badge warn">'
            f'{t("personwizard.unterbrochen.titel")}</span>'
            f'<div class="dim" style="margin-top:6px">'
            f'{t("personwizard.unterbrochen.satz")}</div></div>')
    elif phase == "fehler":
        melde.append(f'<div class="card"><b>{t("personwizard.fehler.titel")}</b>'
                     f'<div class="dim">{html.escape(str(lauf.get("fehler", "")))}'
                     "</div></div>")
    elif leer_lauf:
        # 0-Events-Erklaer-Karte (User-Fund 05.08., zwei reale Personen:
        # der Lauf endete stumm und sah wie ein Abbruch aus — der Nutzer
        # muss das WARUM sehen). Zaehler kommen aus personlauf.anlegen().
        dg = lauf.get("diagnose") or {}
        # Stufe-3-geprueft, BLEIBT literal: kein reiner §8.1-Fall. Der
        # grund/zeile-Bau splict konditionale Halbsaetze ineinander (§8.3),
        # traegt %d-%b-%Y-Datumsformate (B19) und einen konditionalen
        # Plural ("time"+"s") — der noetige Ganz-Satz-Umbau je Zweig ist
        # eine BEWUSSTE Byte-Aenderung und damit ein eigener Zug, nie Teil
        # eines byte-treuen Einzugs.
        wer = _wer_text(lauf.get("person") or "the selected people")
        # .142: Fenster kommt aus der Frigate-Retention (personlauf.anlegen
        # schreibt fenster_tage in die Diagnose); der Fallback-Wert deckt nur
        # Alt-Zustaende vor .119 ohne Diagnose — EINE Quelle, kein Literal.
        from core.personlauf import FENSTER_FALLBACK_TAGE
        tage = dg.get("fenster_tage", FENSTER_FALLBACK_TAGE)
        if dg.get("gebunden_fenster", 0) == 0:
            zl = dg.get("zuletzt_bestaetigt")
            if zl:
                zeile = ("last face-confirmed appearance: "
                         + datetime.datetime.fromtimestamp(zl).strftime("%d %b %Y"))
            else:
                schwach = dg.get("gesehen_schwach") or 0
                seit = dg.get("akte_seit")
                seit_txt = (datetime.datetime.fromtimestamp(seit).strftime("%d %b %Y")
                            if seit else "?")
                zeile = ("the event record (which starts " + seit_txt + " — "
                         "earlier visits are not in it) has "
                         + (("them appearing " + str(schwach) + " time"
                             + ("s" if schwach != 1 else "") + " BELOW the "
                             "confirmation threshold — present, but face "
                             "recognition never confirmed them") if schwach else
                            "no confirmed appearance for them"))
            grund = ("No face-confirmed walk-throughs for <b>" + wer + "</b> in "
                     "the last " + str(tage) + " days. The harvest can only tie "
                     "images to a person through a confirmed pass; " + zeile + ".")
        else:
            grund = ("All " + str(dg.get("gebunden_fenster")) + " bindable events "
                     "for <b>" + wer + "</b> are already part of your learning "
                     "material — there was nothing new to harvest. New "
                     "walk-throughs become harvestable automatically.")
        # Verwaiste Labels ausweisen (Issue #18, Zwei-Namen-Fall): Bestaetigungen
        # geloeschter Personen werden bewusst NICHT geerntet — sagen, nie still.
        vw = dg.get("verwaiste_labels") or {}
        vw_zeile = ""
        if vw:
            vw_zeile = ('<div class="dim">'
                        + t("personwizard.leer.verwaist",
                            liste=", ".join(f"{html.escape(p)} ({n})"
                                            for p, n in vw.items()))
                        + "</div>")
        melde.append(
            f'<div class="card"><b>{t("personwizard.leer.titel")}</b>'
            "<div>" + grund + "</div>" + vw_zeile
            + f'<div class="dim">{t("personwizard.leer.satz")}</div></div>')

    # --- Start-Band ueber die ganze Zeile (Bauform .lf-zw) ----------------
    # Der offene Zug bekommt die volle Breite — hier die Bindungs-Bilanz des
    # gewaehlten Umfangs und der eine Start-Knopf (POST-Vertrag unveraendert).
    band = ""
    if hat_bilanz:
        b = bilanz
        wer = _wer_text(person_wahl)
        if b.get("gebunden") is None:
            zeile = t("personwizard.bilanz.ohne", n=b["n"], wer=wer)
        else:
            # Zaehler mit hervorgehobener Zahl (§8.10): Split an der
            # <b>-Markup-Grenze; der Fremd-Zusatz ist ein abgeschlossener
            # konditionaler Anhang (§8.11).
            zeile = (t("personwizard.bilanz.zahl_vor", n=b["n"])
                     + f'<b>{b["gebunden"]}</b>'
                     + t("personwizard.bilanz.zahl_nach", wer=wer)
                     + (t("personwizard.bilanz.fremd", n=b.get("fremd", 0))
                        if b.get("fremd") else ""))
        if person_wahl == "FREMD":
            erkl = f'<div class="lf-satz">{t("personwizard.bilanz.erkl_fremd")}</div>'
        else:
            erkl = f'<div class="lf-satz">{t("personwizard.bilanz.erkl")}</div>'
        band = (f'<div class="lf-zw"><h3>{t("personwizard.bilanz.titel")}</h3>'
                f'<div>{zeile}</div>' + erkl
                + '<div class="lf-knoepfe" style="margin-top:10px">'
                '<button class="gtb on" onclick="personlaufStart('
                f'{int(b["n"])},this)">{t("personwizard.bilanz.knopf")}</button>'
                ' <span id="pl-status" class="dim"></span></div></div>')

    # Seiten-Kopf: Titel + der eine Erklaer-Satz + Anleitung (ek-hilfe wie
    # auf der Erkennungs-Kachel; derselbe Link-Text-Schluessel wie dort).
    kopf = (f"<h2>{t('personwizard.titel')}</h2>"
            f'<p class="sub">{t("personwizard.kopf.satz")}</p>'
            '<div class="ek-hilfe"><a href="/hilfe/koerper">'
            + t("erkennung.link_how") + '</a></div>')
    # Das Deck wird EINMAL gerendert (mehrere Oeffner teilen es) und nur,
    # wenn die Auswahl-Strecke ueberhaupt frei ist.
    return (lauffluss_stil() + kopf + "".join(melde) + fluss + band
            + (such_deck if start_frei else "")
            + (_modell_karte(modell) or "") + _erklaer_karte())


def abnahme_seite(lauf, zeilen, markiert):
    """PE2 Klick-Abnahme des letzten Laufs (Muster der Prototyp-Klick-Seite):
    Kachel je Bild, Klick = FALSCH (nicht diese Person / unbrauchbar),
    zweiter Klick nimmt es zurueck; jede Wahl wird sofort gespeichert."""
    lauf_id = str(lauf.get("lauf_id") or "")
    ok = [z for z in zeilen if "ausfall" not in z]
    je_person = {}
    for z in ok:
        je_person.setdefault(z["person"], []).append(z)
    bloecke, eintraege = [], []
    for person in sorted(je_person, key=lambda p: -len(je_person[p])):
        kacheln = []
        for z in sorted(je_person[person], key=lambda q: -q["start"]):
            i = len(eintraege)
            eintraege.append(z["datei"])
            # Datumsformat bleibt in der Route (B19-Stufe).
            wann = datetime.datetime.fromtimestamp(z["start"]) \
                .strftime("%d.%m. %H:%M")
            meta = " · ".join(str(x) for x in (
                z.get("camera"), z.get("lichtphase") or "?",
                z.get("blick") or "?"))
            mark = " markiert" if z["datei"] in markiert else ""
            src = ("/personlauf/bild/" + urllib.parse.quote(lauf_id)
                   + "/" + urllib.parse.quote(z["datei"]))
            kacheln.append(
                f'<div class="pl-k{mark}" id="plk_{i}" onclick="plKlick({i})">'
                f'<div class="pl-b"><img loading="lazy" src="{src}"></div>'
                f'<div class="pl-m">{wann}<br>{html.escape(meta)}</div>'
                f'<div class="pl-s">{t("personwizard.review.stempel")}</div></div>')
        bloecke.append(f"<h3>{t('personwizard.review.h_fremde') if person == 'FREMD' else html.escape(person)} "
                       f"({len(je_person[person])})</h3>"
                       f'<div class="pl-r">{"".join(kacheln)}</div>')
    # .147: beim FREMD-Lauf dreht sich die Frage um — markiert wird, wer
    # KEIN Fremder ist; Unmarkiertes wird bestaetigter Fremder im Pool.
    if lauf.get("person") == "FREMD":
        frage = t("personwizard.review.frage_fremd")
    else:
        frage = t("personwizard.review.frage")
    # Stufe 2 Tranche D (§8.4): die Script-Texte kommen server-seitig aus
    # Schluesseln — bausteine.js_literal haelt die einfach-quotierten
    # JS-Literale byte-treu; der Zaehler ist ein deklarierter §8.10-Split
    # (die tickende Zahl bleibt Code, §8.20), die confirm-Frage ein
    # Fragment-Split an den beiden Zahl-Grenzen (Muster setupwiz.import.*).
    return f"""<h2>{t("personwizard.review.titel")}</h2>
<p class="sub">{t("personwizard.review.kopf", lauf=html.escape(lauf_id), frage=frage)}</p>
<div class="card"><a class="gtb" href="/personlauf">{t("personwizard.review.zurueck")}</a> <span id="pl-stand" class="dim"></span>
<span style="float:right"><button class="gtb on" onclick="plFertig(this)">
{t("personwizard.review.knopf_fertig")}</button></span></div>
<style>
 .pl-r {{ display:flex; flex-wrap:wrap; gap:10px; }}
 .pl-k {{ width:170px; background:var(--karte,#303136); border-radius:8px;
         padding:8px; border:2px solid #3f9d55; cursor:pointer;
         position:relative; user-select:none; }}
 .pl-k.markiert {{ border-color:#e8b23c; }}
 .pl-k .pl-s {{ display:none; }}
 .pl-k.markiert .pl-s {{ display:block; position:absolute; top:40%; left:0;
   right:0; text-align:center; color:#e8b23c; font-weight:800;
   font-size:1.4rem; text-shadow:0 0 8px #000; transform:rotate(-14deg); }}
 .pl-b {{ width:154px; height:210px; display:flex; align-items:center;
         justify-content:center; background:rgba(0,0,0,.25);
         border-radius:6px; }}
 .pl-b img {{ max-width:100%; max-height:100%; border-radius:4px; }}
 .pl-m {{ font-size:.72rem; opacity:.75; line-height:1.35; margin-top:6px; }}
</style>
{"".join(bloecke)}
<script>
const PL_DATEIEN = {json.dumps(eintraege)};
const PL_LAUF = {json.dumps(lauf_id)};
function plZaehlen() {{
  document.getElementById('pl-stand').textContent =
    document.querySelectorAll('.pl-k.markiert').length +
    {js_literal(t("personwizard.review.js_zaehl", n=len(eintraege)))};
}}
async function plFertig(btn) {{
  const n = document.querySelectorAll('.pl-k.markiert').length;
  if (!confirm({js_literal(t("personwizard.review.js_frage_vor"))} + ({len(eintraege)} - n) +
      {js_literal(t("personwizard.review.js_frage_mitte"))} + n +
      {js_literal(t("personwizard.review.js_frage_nach"))})) return;
  btn.disabled = true;
  const r = await fetch('/personlauf/abnahme_fertig', {{ method: 'POST' }});
  if (r.ok) {{ location.href = '/personlauf'; return; }}
  btn.disabled = false;
}}
async function plKlick(i) {{
  const k = document.getElementById('plk_' + i);
  const neu = !k.classList.contains('markiert');
  await fetch('/personlauf/urteil', {{ method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ lauf_id: PL_LAUF, datei: PL_DATEIEN[i],
                            urteil: neu ? 'falsch' : 'ok' }}) }});
  k.classList.toggle('markiert', neu);
  plZaehlen();
}}
plZaehlen();
</script>"""


def kontrolle_seite(passe, sammeln):
    """Z8 (konzept_frames.md §7): Kontroll-Speicher der BEURTEILTEN Bilder —
    Kachel-Browser je Durchgang, mit Klasse, Score und Bildquelle daneben.
    View-only (v1): die Seite zeigt, was das Urteil gesehen hat, sie aendert
    nichts daran. Gruppiert wird je PASS, nie je Einzel-Event — nur im ganzen
    Durchgang laesst sich beurteilen, ob ein Urteil richtig war.

    passe   = core.personlive.kontrolle_lesen(...) (neueste zuerst)
    sammeln = Schalter diagnostic_collection; steuert nur den Erklaertext,
              nie den Inhalt (was da ist, wird gezeigt)."""
    # Fett-Vorsatz + Rest: Split an der Markup-Grenze (Muster §8.10 /
    # unbekannte.kopf_satz — beide Teile sind abgeschlossene Bausteine).
    modus = (f'<b>{t("personwizard.kontrolle.sammeln_titel")}</b>{t("personwizard.kontrolle.sammeln_rest")}'
             if sammeln else
             f'<b>{t("personwizard.kontrolle.schlank_titel")}</b>{t("personwizard.kontrolle.schlank_rest")}')
    kopf = [f"<h2>{t('personwizard.kontrolle.titel')}</h2>",
            f'<p class="sub">{t("personwizard.kontrolle.satz")}</p>',
            # Stufe 3 (t_html): <a>/<code> mitten im Schalter-Satz —
            # Zitat-Kopplung ("Settings &rarr; Advanced") am Schluessel.
            f'<div class="card">{modus}<div class="dim" '
            f'style="margin-top:6px">{t_html("personwizard.kontrolle.schalter_satz")}</div></div>']
    if not passe:
        # Stufe 3 (t_html): <a>Model status</a> mitten im Satz.
        kopf.append(f'<div class="card"><b>{t("personwizard.kontrolle.leer_titel")}</b>'
                    f'<div class="dim">{t_html("personwizard.kontrolle.leer_satz")}</div></div>')
        return "".join(kopf)
    bloecke = []
    for p in passe:
        wann = (datetime.datetime.fromtimestamp(p["start"]).strftime(
            "%d.%m. %H:%M") if p.get("start") else html.escape(p["pass_key"]))
        kacheln = []
        for z in p["zeilen"]:
            score = z.get("score")
            schwelle = z.get("schwelle")
            # Drei Zustaende, weil genau sie den Ausgang erklaeren: getroffen,
            # unter der Schwelle, oder als Fremder abgewiesen.
            if z.get("klasse") == "FREMD":
                kl, tag = "kz-fremd", t("personwizard.kontrolle.tag_fremd")
            elif (score is not None and schwelle is not None
                  and score >= schwelle):
                kl, tag = "kz-hit", t("personwizard.kontrolle.tag_drueber")
            else:
                kl, tag = "kz-unter", t("personwizard.kontrolle.tag_drunter")
            uhr = (datetime.datetime.fromtimestamp(z["ts"]).strftime("%H:%M:%S")
                   if z.get("ts") else "")
            if z.get("bild"):
                src = ("/person/kontrolle/bild/"
                       + urllib.parse.quote(p["pass_key"]) + "/"
                       + urllib.parse.quote(z["datei"]))
                bild = f'<img loading="lazy" src="{src}">'
            else:
                # "image expired" wiederverwendet (byte-identisch zur
                # visiontest-Personen-Spalte).
                bild = f'<span class="dim">{t("visiontest.koerper.bild_weg")}</span>'
            kacheln.append(
                f'<div class="kz-k {kl}"><div class="kz-b">{bild}</div>'
                f'<div class="kz-m"><b>{html.escape(str(z.get("klasse") or "?"))}</b>'
                f' {score if score is not None else "?"}'
                f'<br>{tag}{t("personwizard.kontrolle.schwelle", schwelle=schwelle) if schwelle is not None else ""}'
                f'<br>{uhr} &middot; {html.escape(str(z.get("quelle") or "?"))}</div></div>')
        # Echter Plural im Original — t_n loest .eins/.viele auf.
        bloecke.append(
            f'<h3>{t_n("personwizard.kontrolle.kopfzeile", p["bilder"], wann=wann, judged=p["n"])}</h3>'
            f'<div class="kz-r">{"".join(kacheln)}</div>')
    stil = """<style>
 .kz-r { display:flex; flex-wrap:wrap; gap:10px; }
 .kz-k { width:150px; background:var(--karte,#303136); border-radius:8px;
         padding:8px; border:2px solid #4a4b52; }
 .kz-k.kz-hit { border-color:#3f9d55; }
 .kz-k.kz-unter { border-color:#6b6c74; }
 .kz-k.kz-fremd { border-color:#e8b23c; }
 .kz-b { width:134px; height:180px; display:flex; align-items:center;
         justify-content:center; background:rgba(0,0,0,.25);
         border-radius:6px; font-size:.72rem; text-align:center; }
 .kz-b img { max-width:100%; max-height:100%; border-radius:4px; }
 .kz-m { font-size:.72rem; opacity:.85; line-height:1.35; margin-top:6px; }
</style>"""
    return "".join(kopf) + stil + "".join(bloecke)


def _personen_tabelle(modell):
    """Kompakte Lern-Bilanz als erster, dazwischengeschobener Block der
    /person-Seite (User 07.08.: kleine Tabelle, Platz gut nutzen — WER ist
    gelernt, wie viele Bilder, Fremd-Klasse als eigene Zeile, Hinweis wenn
    0 Fremde, dazu welches Modell/welche Einstellung aktiv ist; Global-
    Unterschied als Zeile darunter, User-Entscheid 07.08.). Alle Zahlen
    kommen aus DEMSELBEN Status-Dict wie _modell_karte/modell_seite —
    eine Quelle, keine zweite Rechnung (.138-Lehre Bilanz-Zeile)."""
    if not modell or not modell.get("bilder"):
        return ""
    # .144 (User 07.08., Screenshot): KEINE <table> — style.css setzt
    # table width:100%, jede Zeile lief ueber die volle Seitenbreite mit
    # Leerraum in der Mitte. Stattdessen ein Grid, das je nach Breite
    # mehrere Spalten fuellt (mehrspaltig = Platz genutzt).
    _z = ('<div style="display:flex;justify-content:space-between;gap:12px;'
          'padding:2px 0;border-bottom:1px solid rgba(128,128,128,.2)">')
    zellen = "".join(
        f"{_z}<span>{html.escape(p)}</span><b>{n}</b></div>"
        for p, n in sorted(modell.get("personen", {}).items(),
                           key=lambda kv: -kv[1]))
    n_fremd = modell.get("fremd_bilder") or 0
    zellen += (f'{_z[:-2]};opacity:.75"><span>{t("personwizard.tabelle.fremd_zeile")}</span>'
               f"<b>{n_fremd}</b></div>")
    raster = ('<div style="display:grid;grid-template-columns:'
              "repeat(auto-fit,minmax(190px,1fr));gap:2px 40px;"
              f'margin-top:6px">{zellen}</div>')
    hinweis = ""
    if not n_fremd:
        hinweis = ('<div style="color:var(--warn);margin-top:6px">'
                   f'{t("personwizard.tabelle.kein_fremd")}'
                   "</div>")
    # Status-Mapping (§8.19): je Kennung ein Schluessel; unbekannte
    # Kennungen zeigen sich selbst.
    quelle = modell.get("schwelle_quelle") or "standard"
    quelle_txt = {"eichung": t("personwizard.tabelle.q_eichung"),
                  "user": t("personwizard.tabelle.q_user"),
                  "standard": t("personwizard.tabelle.q_standard")}.get(quelle, quelle)
    schwelle = modell.get("schwelle")
    fakten_zellen = "".join(
        f'<div><span class="dim">{k}</span><br>{v}</div>' for k, v in (
            (t("personwizard.tabelle.f_modell"),
             html.escape(str(modell.get("modell", "")))),
            (t("personwizard.tabelle.f_schwelle"),
             f"<b>{schwelle}</b> ({quelle_txt})" if schwelle else "—"),
            # <b>YES</b>-Vorsatz: Split an der Markup-Grenze (§8.10).
            (t("personwizard.tabelle.f_scharf"),
             f'<b>{t("personwizard.tabelle.scharf_ja")}</b>{t("personwizard.tabelle.scharf_ja_rest")}'
             if modell.get("scharf") else t("personwizard.tabelle.scharf_nein")),
        ))
    fakten = ('<div style="display:grid;grid-template-columns:'
              "repeat(auto-fit,minmax(220px,1fr));gap:6px 40px;"
              f'margin-top:10px">{fakten_zellen}</div>')
    ei = modell.get("eichung") or {}
    konf = ei.get("verwechslung_max")
    konf_html = ""
    if konf is not None:
        # Zaehler mit hervorgehobener Zahl (§8.10): Split an der <b>-Grenze.
        konf_html = ('<div class="dim" style="margin-top:8px">'
                     f'{t("personwizard.tabelle.konf_vor")}'
                     f"<b>{konf}</b>{t('personwizard.tabelle.konf_nach')}</div>")
    return (f'<div class="card"><b>{t("personwizard.tabelle.titel")}</b>'
            + raster + fakten + konf_html + hinweis + "</div>")


def _modell_karte(modell):
    """Kompakte Status-Karte (Wizard + Person-Seite, EINE Quelle).
    .141: der Vorsatz kommt aus dem ECHTEN scharf-Zustand — 'Not armed yet'
    stand hier als Festtext vor JEDEM Hinweis, auch bei scharfem Modell
    (Operator-Fund am Screenshot 06.08.). Ein Trainings-Fehlschlag steht
    ROT dabei (Panel-MUSS: nie den Alt-Stand als aktuell ausgeben)."""
    if not modell or not modell.get("bilder"):
        return ""
    # Datumsformat bleibt in der Route (B19-Stufe).
    wann = datetime.datetime.fromtimestamp(modell["ts"]) \
        .strftime("%d.%m. %H:%M")
    je = " · ".join(f"{html.escape(p)} {n}" for p, n in
                    sorted(modell.get("personen", {}).items(),
                           key=lambda kv: -kv[1]))
    vorsatz = (t("personwizard.karte.scharf") if modell.get("scharf")
               else t("personwizard.karte.unscharf"))
    fehler = ""
    if modell.get("letzter_fehler"):
        fehler = ('<div style="color:var(--crit)">'
                  + t("personwizard.karte.fehler",
                      fehler=html.escape(str(modell["letzter_fehler"])))
                  + "</div>")
    return (f'<div class="card"><b>{t("personwizard.karte.titel")}</b>'
            f'<div>{t("personwizard.karte.zeile", wann=wann, dauer=modell.get("dauer_s", "?"), bilder=modell["bilder"], je=je, modell=html.escape(str(modell.get("modell", ""))))}'
            f'<a href="/person/modell">{t("personwizard.karte.link")}</a></div>'
            + fehler +
            f'<div class="dim">{vorsatz}: '
            f'{html.escape(str(modell.get("hinweis", "")))}</div></div>')


def bestand_seite(laeufe, modell=None, wer="", fremd=None):
    """PE2b (User 04.08., Anchors-Pendant): das ABGENOMMENE Material.
    .145 (User 07.08.): Galerie NACH PERSON statt nach Lauf ('mich
    interessiert nicht welcher Run'), Bilder NUR fuer die gewaehlte
    Gruppe (keine Bandwurmseite) und die Fremd-Bilder als eigener
    Eintrag (Ansicht; Pflege weiter ueber personlern/fremd/).
    wer   = gewaehlte Person, 'strangers' fuer den Fremd-Pool, ''=keine
    fremd = Dateinamen des Fremd-Pools (vom Handler gelistet)."""
    je_person = {}
    for lid, zeilen in laeufe:
        for z in zeilen:
            if "ausfall" in z or z.get("status") != "abgenommen":
                continue
            if z.get("person") == "FREMD":
                # .147: bestaetigte Fremde leben im POOL (Chip Strangers)
                # — die Lauf-Zeile bleibt nur Beleg/Bestands-Skip, sonst
                # stuende dasselbe Bild doppelt auf der Seite.
                continue
            je_person.setdefault(z["person"], []).append(
                dict(z, lauf_id=lid))
    fremd = fremd or []
    teile = [f"<h2>{t('personwizard.bestand.titel')}</h2>",
             f'<p class="sub">{t("personwizard.bestand.satz")}</p>',
             _personen_tabelle(modell),
             _modell_karte(modell)]
    if not je_person and not fremd:
        # Stufe 3 (t_html): <a>Person learn</a> mitten im Satz.
        teile.append(f'<div class="card"><b>{t("personwizard.bestand.leer_titel")}</b>'
                     f'<div class="dim">{t_html("personwizard.bestand.leer_satz")}</div></div>')
        return "".join(teile)
    # .141 (User-Vorgabe 06.08.: 'ganz deutlicher Hinweis, dass wir moeglichst
    # viele Daten brauchen'): der gemessene Hebel ist VIELFALT, nicht Menge —
    # mehr TAGE (Outfits, Licht) schlagen mehr Bilder desselben Durchgangs
    # (Prototyp-Messung: mehrtaegige Bloecke drueckten die Verwechslung von
    # 3/5 auf 1/5). Deshalb je Person Bilder+Tage+Kameras mit ehrlichem
    # Marker bei duenner Tage-Basis, dazu die Fremd-Erklaerung.
    # Stufe 3 (t_html): <b>many different days</b> und der
    # <b>Strangers:</b>-Absatz mit <code>; {n} escapt t_html selbst.
    teile.append(
        f'<div class="card"><b>{t("personwizard.bestand.stark_titel")}</b>'
        f'<div class="dim">{t_html("personwizard.bestand.stark_satz")}</div>'
        + (('<div class="dim" style="margin-top:4px">'
            f'{t_html("personwizard.bestand.fremd_satz", n=modell.get("fremd_bilder", 0))}'
            "</div>") if modell else "")
        + "</div>")
    # Auswahl-Chips: eine Gruppe oeffnen statt alles untereinander
    # (Bandwurm); der Fremd-Pool haengt als eigener Eintrag hinten dran.
    namen = sorted(je_person, key=lambda p: -len(je_person[p]))
    chips = [
        f'<a class="gtb{" on" if wer == p else ""}" '
        f'href="/person?wer={urllib.parse.quote(p)}">'
        f"{html.escape(p)} ({len(je_person[p])})</a>"
        for p in namen]
    if fremd:
        chips.append(f'<a class="gtb{" on" if wer == "strangers" else ""}" '
                     f'href="/person?wer=strangers">{t("personwizard.bestand.chip_fremde", n=len(fremd))}</a>')
    teile.append(f'<div class="card"><b>{t("personwizard.bestand.zeigen_titel")}</b>'
                 f'<div style="margin-top:6px">{" ".join(chips)}</div>'
                 f'<div class="dim">{t("personwizard.bestand.zeigen_satz")}</div></div>')
    eintraege = []
    if wer in je_person:
        zs = sorted(je_person[wer], key=lambda q: -q["start"])
        p_tage = sorted({z.get("tag") for z in zs if z.get("tag")})
        p_kams = {z.get("camera") for z in zs if z.get("camera")}
        marker = ""
        if len(p_tage) < 3:
            # Echter Plural im Original ("day"/"days") — t_n je Zweig.
            marker = (' <span style="color:var(--warn)">'
                      f'{t_n("personwizard.bestand.marker_tage", len(p_tage))}</span>')
        kacheln = []
        for z in zs:
            i = len(eintraege)
            eintraege.append({"lauf_id": z["lauf_id"], "datei": z["datei"]})
            # Datumsformat bleibt in der Route (B19-Stufe).
            wann = datetime.datetime.fromtimestamp(z["start"]) \
                .strftime("%d.%m. %H:%M")
            meta = " · ".join(str(x) for x in (
                z.get("camera"), z.get("lichtphase") or "?",
                z.get("blick") or "?"))
            src = ("/personlauf/bild/" + urllib.parse.quote(z["lauf_id"])
                   + "/" + urllib.parse.quote(z["datei"]))
            kacheln.append(
                f'<div class="pm-k" id="pmk_{i}">'
                f'<button class="pm-x" title="{t("personwizard.bestand.attr_loeschen")}" '
                f'onclick="pmBild({i})">&times;</button>'
                f'<div class="pm-b"><img loading="lazy" src="{src}">'
                f'</div><div class="pm-m">{wann}<br>{html.escape(meta)}'
                "</div></div>")
        # Zaehler-Zeile: drei unabhaengige Plurale — je Baustein ein
        # Schluessel bzw. t_n-Paar, die " · "-Fugen bleiben Code (§8.10:
        # Zaehler sind keine Prosa).
        teile.append(
            f"<h3>{html.escape(wer)} ({len(zs)})</h3>"
            f'<div class="dim">{t("personwizard.bestand.z_bilder", n=len(zs))} · '
            f'{t_n("personwizard.bestand.z_tage", len(p_tage))} · '
            f'{t_n("personwizard.bestand.z_kameras", len(p_kams))}{marker}</div>'
            f'<div class="pm-r" style="margin-top:8px">'
            f'{"".join(kacheln)}</div>')
    elif wer == "strangers" and fremd:
        # .146 (User: 'fremde muessen auch geloescht werden koennen'):
        # gleiche Kachel-Mechanik wie bei Personen — PM-Eintrag {"fremd":
        # datei}, derselbe pmBild-Knopf, derselbe Loesch-Endpunkt.
        kacheln = []
        for f in fremd:
            i = len(eintraege)
            eintraege.append({"fremd": f})
            kacheln.append(
                f'<div class="pm-k" id="pmk_{i}">'
                f'<button class="pm-x" title="{t("personwizard.bestand.attr_loeschen")}" '
                f'onclick="pmBild({i})">&times;</button>'
                '<div class="pm-b"><img loading="lazy" '
                f'src="/personlauf/fremdbild/{urllib.parse.quote(f)}"></div>'
                f'<div class="pm-m">{html.escape(f)}</div></div>')
        # Stufe 3 (t_html): <code>personlern/fremd/</code> mitten im Satz.
        teile.append(
            f"<h3>{t('personwizard.bestand.chip_fremde', n=len(fremd))}</h3>"
            f'<div class="dim">{t_html("personwizard.bestand.fremd_erklaerung")}</div>'
            f'<div class="pm-r" style="margin-top:8px">'
            f'{"".join(kacheln)}</div>')
    return "".join(teile) + f"""
<style>
 .pm-r {{ display:flex; flex-wrap:wrap; gap:10px; }}
 .pm-k {{ width:150px; position:relative; }}
 .pm-x {{ position:absolute; top:2px; right:2px; z-index:2; border:0;
   border-radius:50%; width:24px; height:24px; cursor:pointer;
   background:#8c3434; color:#fff; font-weight:700; }}
 .pm-b {{ width:150px; height:200px; display:flex; align-items:center;
   justify-content:center; background:rgba(0,0,0,.25); border-radius:6px; }}
 .pm-b img {{ max-width:100%; max-height:100%; border-radius:4px; }}
 .pm-m {{ font-size:.7rem; opacity:.75; line-height:1.3; margin-top:4px; }}
</style>
<script>
const PM = {json.dumps(eintraege)};
async function pmBild(i) {{
  if (!confirm('Delete this image from the learning material?')) return;
  const r = await fetch('/personlauf/loeschen', {{ method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify(PM[i]) }});
  if (r.ok) document.getElementById('pmk_' + i).remove();
}}
</script>"""


def modell_seite(status, regeln=None):
    """PE3-Status als eigene Seite im Person-Bereich (User 04.08.:
    'Model status neben Person'). regeln = Standardwerte + Grenzen der
    Feuer-Regel (vom Handler aus core geliefert, kein Streu-Literal)."""
    regeln = regeln or {}
    teile = [f"<h2>{t('personwizard.modell.titel')}</h2>",
             f'<p class="sub">{t("personwizard.modell.satz")}</p>']
    if not status or not status.get("bilder"):
        # Stufe 3 (t_html): <a>Person learn</a> mitten im Satz.
        teile.append(f'<div class="card"><b>{t("personwizard.modell.leer_titel")}</b>'
                     f'<div class="dim">{t_html("personwizard.modell.leer_satz")}</div></div>')
        return "".join(teile)
    # Datumsformat inkl. %a-Wochentag bleibt in der Route (B19-Stufe).
    wann = datetime.datetime.fromtimestamp(status["ts"]) \
        .strftime("%a %d.%m. %H:%M")
    scharf = status.get("scharf")
    st = "border-spacing:14px 4px"
    # .139/.141: gegen ECHTE Fremde geeicht oder nur zwischen den gelernten
    # Personen? Quelle sind EXPLIZITE Status-Felder (eichung.art +
    # fremd_trainiert), nie mehr das Text-Literal '+ strangers)' und nie
    # eine Negativ-Ableitung (.141 Panel: der vierte Zustand log, wenn die
    # Eichung aus einem ANDEREN Grund fehlte). Alt-Status vor .141 ohne die
    # Felder: einmalige Rueckfall-Ableitung.
    from core.personmodell import FREMD_MIN as _FREMD_MIN
    ei = status.get("eichung") or {}
    gegen_fremde = (ei.get("art") == "fremd" if "art" in ei
                    else "fremd_echt_max" in ei)
    ft = status.get("fremd_trainiert")
    if ft is None:                                 # Status aus .139/.140
        ft = str(status.get("modell", "")).endswith("+ strangers)")
    n_fremd = status.get("fremd_bilder") or 0
    if not n_fremd:
        fremd_txt = t("personwizard.modell.fremd_keine")
    elif not ft:
        fremd_txt = t("personwizard.modell.fremd_gesammelt",
                      n=n_fremd, min=_FREMD_MIN)
    elif gegen_fremde:
        fremd_txt = t("personwizard.modell.fremd_geeicht", n=n_fremd)
    else:
        fremd_txt = t("personwizard.modell.fremd_ungeeicht", n=n_fremd)
    # "Armed" als Zeilen-Label wiederverwendet (personwizard.tabelle.f_scharf,
    # byte-identisch); "{s} s (CPU)" bleibt literal (Einheiten, §8.6).
    fakten = "".join(
        f'<tr><td class="dim">{k}</td><td><b>{v}</b></td></tr>' for k, v in (
            (t("personwizard.modell.f_trainiert"), wann),
            (t("personwizard.modell.f_dauer"),
             f'{status.get("dauer_s", "?")} s (CPU)'),
            (t("personwizard.modell.f_modell"),
             html.escape(str(status.get("modell", "")))),
            (t("personwizard.modell.f_bilder"), status["bilder"]),
            (t("personwizard.modell.f_personen"),
             len(status.get("personen", {}))),
            (t("personwizard.modell.f_fremd"), fremd_txt),
            (t("personwizard.tabelle.f_scharf"),
             t("personwizard.modell.scharf_ja") if scharf
             else t("personwizard.modell.scharf_nein")),
        ))
    # .141 Panel-MUSS: ein fehlgeschlagener Trainingslauf steht auf der Karte
    # (rot, mit Zeit), nicht nur im Container-Log — sonst wirkt der Alt-Stand
    # als aktuell und 'deletions retrain automatically' ist eine Luege.
    fehler_html = ""
    if status.get("letzter_fehler"):
        ft2 = datetime.datetime.fromtimestamp(
            status.get("letzter_fehler_ts") or 0).strftime("%d.%m. %H:%M")
        fehler_html = ('<div class="sa-crit" style="color:var(--crit)">'
                       + t("personwizard.modell.fehler", zeit=ft2,
                           fehler=html.escape(str(status["letzter_fehler"])))
                       + "</div>")
    teile.append(f'<div class="card"><b>{t("personwizard.modell.aktuell_titel")}</b>'
                 f'<table style="{st}">{fakten}</table>'
                 + fehler_html +
                 f'<div class="dim">{html.escape(str(status.get("hinweis", "")))}'
                 "</div></div>")
    zeilen = "".join(
        f'<tr><td>{html.escape(p)}</td><td style="text-align:right">{n}'
        "</td><td style='text-align:right'>"
        f'{round(100 * n / max(1, status["bilder"]))}%</td></tr>'
        for p, n in sorted(status.get("personen", {}).items(),
                           key=lambda kv: -kv[1]))
    # Stufe 3 (t_html): <a>Body images</a> mitten im Pflege-Satz —
    # zitiert nav.person (Kopplung am Schluessel).
    teile.append(
        f'<div class="card"><b>{t("personwizard.modell.material_titel")}</b>'
        f'<table style="{st}">'
        f'<tr><th style="text-align:left">{t("personwizard.modell.kopf_person")}</th>'
        f'<th style="text-align:right">{t("personwizard.modell.kopf_bilder")}</th>'
        f'<th style="text-align:right">{t("personwizard.modell.kopf_anteil")}</th></tr>'
        f'{zeilen}<tr><td><b>{t("personwizard.modell.summe")}</b></td><td style="text-align:right"><b>'
        f'{status["bilder"]}</b></td><td></td></tr></table>'
        f'<div class="dim">{t_html("personwizard.modell.material_satz")}</div></div>')
    # .114: Schwelle (geeicht/eigen) + Feuer-Regel einstellbar
    gr = regeln.get("grenzen", {})
    eff_schwelle = status.get("schwelle") or regeln.get("schwelle_std", "?")
    quelle = status.get("schwelle_quelle") or "standard"
    # Status-Mapping (§8.19); "set by you"/"built-in default" wieder-
    # verwendet (byte-identisch zur Lern-Bilanz-Tabelle).
    quelle_txt = {"eichung": t("personwizard.modell.q_eichung"),
                  "user": t("personwizard.tabelle.q_user"),
                  "standard": t("personwizard.tabelle.q_standard")}.get(quelle, quelle)
    ei_txt = ""
    if ei and gegen_fremde:
        # {pct} vorformatiert (round) aus der Route (§8.8).
        ei_txt = ('<div class="dim">'
                  + t("personwizard.modell.eich_fremd",
                      folds=ei.get("folds", "?"), n=ei.get("n", "?"),
                      n_fremd=ei.get("n_fremd", "?"),
                      max=ei.get("fremd_echt_max", "?"),
                      schwelle=ei.get("schwelle", "?"),
                      pct=round(100 * (ei.get("getragen_anteil") or 0)),
                      ueber=ei.get("verwechslung_ueber_n", "?"),
                      vmax=ei.get("verwechslung_max", "?"))
                  + "</div>")
    elif ei:
        ei_txt = ('<div class="dim">'
                  + t("personwizard.modell.eich_intern",
                      folds=ei.get("folds", "?"), n=ei.get("n", "?"),
                      max=ei.get("fremd_max", "?"),
                      schwelle=ei.get("schwelle", "?"),
                      pct=round(100 * (ei.get("getragen_anteil") or 0)))
                  + "</div>")

    def _feld(fid, label, wert, einheit=""):
        lo, hi = gr.get(fid, ("", ""))
        return (f'<tr><td class="dim">{label}</td>'
                f'<td><input id="pe-{fid}" type="number" size="6" '
                f'value="{wert}" min="{lo}" max="{hi}" '
                f'{"step=0.01" if fid == "schwelle" else ""}> {einheit} '
                f'<span class="dim">({lo}–{hi})</span></td></tr>')

    # Stufe-2-Grenze (Tranche D, Fachschicht): j.msg im Save-Skript sind
    # Server-Antworten aus core/personmodell.einstellungen_setzen — die
    # msg entsteht in der Fachschicht, ihr Einzug ist ein eigener Zug.
    # Zaehler-Split an der <b>-Grenze (§8.10) in der Schwellen-Zeile.
    teile.append(
        f'<div class="card"><b>{t("personwizard.modell.regeln_titel")}</b>'
        f'<div>{t("personwizard.modell.schwelle_vor")}<b>{eff_schwelle}</b> '
        f'<span class="dim">({quelle_txt})</span></div>' + ei_txt
        + f'<table style="{st}">'
        + _feld("schwelle", t("personwizard.tabelle.f_schwelle"),
                status.get("schwelle") if quelle == "user" else "")
        + _feld("fenster_s", t("personwizard.modell.r_fenster"),
                status.get("fenster_s") or regeln.get("fenster_s", ""), "s")
        + _feld("feuer_ab", t("personwizard.modell.r_feuer"),
                status.get("feuer_ab") or regeln.get("feuer_ab", ""))
        + _feld("karenz_s", t("personwizard.modell.r_karenz"),
                status.get("karenz_s") or regeln.get("karenz_s", ""), "s")
        + "</table>"
        f'<div class="dim">{t("personwizard.modell.regeln_satz")}</div>'
        '<div style="margin-top:8px"><button class="gtb on" '
        f'onclick="personRegeln(this)">{t("personwizard.modell.knopf_speichern")}</button> '
        '<span id="pe-status" class="dim"></span></div></div>'
        "<script>async function personRegeln(btn){btn.disabled=true;"
        "const d={};for(const k of['schwelle','fenster_s','feuer_ab',"
        "'karenz_s']){d[k]=document.getElementById('pe-'+k).value;}"
        "const r=await fetch('/person/einstellungen',{method:'POST',"
        "headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});"
        "const j=await r.json();document.getElementById('pe-status')"
        ".textContent=j.msg||'';if(j.ok){location.reload();}"
        "btn.disabled=false;}</script>")
    # PE4-Schalter (Aktivierungs-Gate): Arm/Disarm direkt hier.
    # .141 Panel-SOLL: der Satz beschreibt die WIRKSAME Schwelle — hat der
    # User sie selbst gesetzt, darf hier nicht 'calibrated' stehen, waehrend
    # oben 'set by you' steht (drei Aussagen, eine Seite).
    # Schwellen-Satz: Basis-Satz je Zweig (B9) + abgeschlossene konditionale
    # Anhaenge (§8.11 — Eich-Zusatz und Fremd-Drop-Satz); der Schlusspunkt
    # des user-Zweigs bleibt Code (er schliesst Basis+Anhang gemeinsam).
    if quelle == "user":
        schwelle_satz = (t("personwizard.modell.satz_user", schwelle=eff_schwelle)
                         + (t("personwizard.modell.satz_user_eich",
                              n=n_fremd, alt=ei.get("schwelle"))
                            if gegen_fremde and ei.get("schwelle") else "")
                         + ".")
    elif gegen_fremde:
        schwelle_satz = t("personwizard.modell.satz_geeicht", n=n_fremd)
    else:
        schwelle_satz = t("personwizard.modell.satz_ungeeicht")
    if ft:
        schwelle_satz += t("personwizard.modell.satz_fremd_drop")
    teile.append(
        f'<div class="card"><b>{t("personwizard.modell.live_titel")}</b>'
        + (f'<div>{t("personwizard.modell.live_an")}</div>' if scharf else
           f'<div>{t("personwizard.modell.live_aus")}</div>')
        + (f'<div class="dim">{t("personwizard.modell.live_hinweis")} '
           + schwelle_satz + "</div>")
        + '<div style="margin-top:8px"><button class="gtb'
        + ("" if scharf else " on")
        + f'" onclick="personSchalter({str(not scharf).lower()},this)">'
        + (t("personwizard.modell.knopf_disarm") if scharf
           else t("personwizard.modell.knopf_arm"))
        + "</button></div></div>"
        # Stufe 2 Tranche D (§8.4): der 'error '-Vorsatz kommt aus dem
        # Schluessel (js_literal, byte-treu; der Status-Code bleibt Code).
        + "<script>async function personSchalter(an,btn){btn.disabled=true;"
          "const r=await fetch('/person/schalter',{method:'POST',"
          "headers:{'Content-Type':'application/json'},"
          "body:JSON.stringify({scharf:an})});"
          "if(r.ok){location.reload();return;}"
          "const d=await r.json().catch(function(){return{};});"
          "alert(d.msg||(" + js_literal(t("personwizard.modell.js_fehler"))
        + "+r.status));btn.disabled=false;}</script>")
    return "".join(teile)
