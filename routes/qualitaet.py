"""routes/qualitaet — Qualitaets-Seite: Uebersicht (Klartext-Satz + Personen-
Liste) und je Person die GALERIE mit drei Reitern (Good / Check these /
Suggest removing). Die alten Unter-Tabs Verwechslung/Eignung/Doppel sind seit
.280 WEG (User 18.08., am kaputten Confusion-Layout: 'kann alles weg, kommt
an einen anderen Ort und optisch besser') — alle drei Befund-Arten leben in
der Galerie, Verwechslungs-Kacheln tragen das Gegenbild als Mini-Thumb.
Der Handler laedt das QS-JSON (anlernen.QS_PATH) und reicht es mit data_dir
herein; hier wird NUR gerendert (inkl. Existenz-Filter gegen tote Bild-Links,
User-Befund 19.07.).

Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py (Luecken-Block, filt-Zeile und
Funde-Ergebnis-Satz bleiben literal — Splicing/Inline-Markup)."""
import datetime
import html
import json  # seit Tranche D auch selbst genutzt (JS-Text-Injektion §8.4)
import os
import urllib.parse

import webui
from core.sprache import t

# Reiter der Personen-Galerie, in der Reihenfolge der Zuordnung. Der erste
# Eintrag ist der Rest-Reiter ("gut"), die vier danach sind BEFUND-Reiter.
REITER_ORDNUNG = ("gut", "check", "weg", "dubl", "noface")


def reiter_gruppe(k, noface, dubl_alle, verwechselt, dup_weg, urteil):
    """DIE EINE Reiter-Regel der Qualitaets-Seite -> ein Wert aus REITER_ORDNUNG.
    `k` ist der Bild-Schluessel (Dateiname in der Galerie, (Person, Datei) in der
    Uebersicht), `urteil` das Stufe-C-Wort dieses Bildes ('ok'/'auffaellig'/
    'raus'/'ungemessen'/None).

    EXKLUSIV: ein Bild steht in GENAU EINEM Reiter. Sonst zaehlte der
    Remove-Zaehler dieselbe Datei zweimal — und genau daraus entstanden die
    734 "Funde" auf 1185 Bildern, die der Feldtester am 09.09. sah.

    .512 (Feldtester-Meldung 09.09., Diagnose backups/katalog_diagnose_0909/
    blurry_diagnose_bericht.md): bis .511 entschied HIER noch die ALTE
    Pixel-Achse (`qs["ungeeignet"]`, `sharp < unscharf_max`) ueber Reiter UND
    Wort — und zwar VOR dem Stufe-C-Urteil, das deshalb nur noch als dim-Zusatz
    danebenstand. Folge auf dem Feldtester-Bestand: 103 Kacheln mit dem Wort
    "blurry" im Entfernen-Reiter, 12 davon haelt der kalibrierte Pruefer fuer
    `ok`, und in der Sichtpruefung waren mehrere davon fuer das Auge sichtbar
    scharf. Die Alt-Achse misst mit `sharp` weiter (Sidecar, Lern-Seiten,
    REF_LATTE — alles unveraendert), aber auf DIESER Seite urteilt sie nicht
    mehr: `sharp` trennt am Eichsatz mit AUC 0,48 nicht besser als ein
    Muenzwurf (core/refurteil.py, Stufe B §3d).

    Was hier weiterhin VOR dem Guete-Urteil kommt, sind die Befunde, die es
    nicht faellen KANN: kein Gesicht gefunden (keine einzige Messung),
    Byte-Kopien (Datei-Identitaet), Verwechslung und Nah-Dublette (beides
    Beziehungen zwischen zwei Bildern, keine Guete-Frage)."""
    if k in noface:
        return "noface"
    if k in dubl_alle:
        return "dubl"
    if k in verwechselt:
        return "check"
    if k in dup_weg:
        return "weg"
    if urteil == "raus":
        return "weg"
    if urteil == "auffaellig":
        return "check"
    return "gut"


def render(ansicht, qs, data_dir, lauf=None, aktiv=False, person=None):
    """-> Seiten-INHALT (kopf+koerper; layout/banner bleiben beim Handler).
    ansicht ist seit .280 eine ignorierte Altlast (Deep-Links auf die alten
    Unter-Tabs landen auf der Uebersicht); Signatur bleibt Handler-Vertrag.
    lauf (.273): Fortschritts-/Fehler-Stand eines laufenden Bestands-QS
    (refs_qs_lauf.json), aktiv = frisch genug fuer 'laeuft gerade'.
    person (.273, Widerleger-Blocker): der Personen-Filter ist reine
    ANZEIGE — der Store traegt immer den vollen Befund, gefiltert wird
    ausschliesslich HIER."""
    stand = (datetime.datetime.fromtimestamp(qs["ts"]).strftime("%d.%m. %H:%M")
             if qs.get("ts") else "—")
    # Nur Eintraege zu noch EXISTIERENDEN Dateien rendern — nach einer Loeschung
    # zeigte die Seite sonst tote Bild-Links (Fragezeichen), bis der
    # Hintergrund-Neulauf fertig war (User-Befund 19.07.)
    refs_base = os.path.join(data_dir, "faces")

    def _da(person, datei):
        return os.path.isfile(os.path.join(refs_base, person, datei))
    paare = [p for p in qs.get("paare", [])
             if _da(p["a_person"], p["a_datei"]) and _da(p["b_person"], p["b_datei"])]
    ug = [u for u in qs.get("ungeeignet", []) if _da(u["person"], u["datei"])]
    if person:
        paare = [p for p in paare
                 if person in (p["a_person"], p["b_person"])]
        ug = [u for u in ug if u["person"] == person]
    # .512: die frueher hier gebildete Liste `krit` ist entfallen — die
    # Verwechslungs-Zahl der Uebersicht zaehlt seitdem BILDER (Teilmenge der
    # Reiter-Zuordnung) statt PAARE, s. _uebersicht_zaehlen().
    # .273 Bestands-QS: Doppel-Befunde + Personen-Kopftabelle + Lauf-Fortschritt.
    doppel = [d for d in qs.get("doppel", [])
              if _da(d["person"], d["datei"]) and _da(d["person"], d["behalten"])]
    if person:
        doppel = [d for d in doppel if d["person"] == person]
    lauf_zeile = ""
    if lauf and lauf.get("fehler"):
        # §8.14 Slice-vor-Format: {fehler} kommt escaped+gesliced ([:180]).
        lauf_zeile = ('<p style="color:var(--crit)">'
                      + t("qualitaet.lauf.fehler",
                          fehler=html.escape(str(lauf["fehler"])[:180]))
                      + '</p>')
    elif lauf and aktiv:
        # .310 (User 21.08.: 'eine kleine Leiste, die hochzaehlt, ohne den
        # Browser zu aktualisieren' — Lernlauf-Muster): Balken + Zaehler,
        # nachgefuehrt von qsFortschritt() (app.js, pollt /qualitaet/status);
        # EIN Reload erst, wenn der Lauf fertig ist — und NUR auf der Uebersicht:
        # die Personen-Galerie hat Haken/Reiter, die darf sich nie selbst neu
        # laden (.282-Lehre, Gate-Fang .310); dort zeigt das JS am Ende den
        # Hinweis 'reload this page afterwards' (data-fertig).
        _i, _n = int(lauf.get("i", 0)), int(lauf.get("n", 0))
        _pz = int(100 * _i / _n) if _n else 0
        lauf_zeile = ('<div id="qs-lauf" data-i="' + str(_i) + '" data-n="' + str(_n) + '" '
                      'data-reload="' + ("0" if person else "1") + '" '
                      'data-fertig="' + html.escape(t("qualitaet.lauf.reload_person"), quote=True) + '" '
                      'style="margin:8px 0 12px;max-width:520px">'
                      '<div class="dim" id="qs-lauf-text">&#9203; '
                      + t("qualitaet.lauf.checking", i=_i, n=_n) + '</div>'
                      '<div style="height:8px;border-radius:4px;background:var(--surface-2);'
                      'border:1px solid var(--border);overflow:hidden;margin-top:4px">'
                      '<div id="qs-lauf-balken" style="height:100%;width:' + str(_pz) + '%;'
                      'background:seagreen;transition:width .6s"></div></div></div>')
    elif lauf:
        lauf_zeile = ('<p style="color:var(--warn)">'
                      + t("qualitaet.lauf.abgebrochen") + '</p>')
    pers_tab = ""
    _pers_map = qs.get("personen") or {}
    if person:
        _pers_map = {p_: e for p_, e in _pers_map.items() if p_ == person}
    if _pers_map:
        zeilen = "".join(
            f'<tr><td><a href="/qualitaet?person='
            f'{urllib.parse.quote(p)}"><b>{html.escape(p)}</b></a></td>'
            f'<td>{e.get("n", 0)}</td>'
            f'<td>{e.get("gut", 0)}</td><td>{e.get("mindest", 0)}</td>'
            f'<td>{e.get("unter", 0) + e.get("unmessbar", 0)}</td>'
            f'<td>{e.get("links", "—")}</td><td>{e.get("frontal", "—")}</td>'
            f'<td>{e.get("rechts", "—")}</td>'
            f'<td>{e.get("redundant", 0)}</td><td>{e.get("kritisch", 0)}</td>'
            '</tr>'
            for p, e in sorted(_pers_map.items()))
        # .278 (User: 'die ganzen Zahlen bei Easy raus, rein bei Expert'):
        # Easy sieht je Person EINE Klartext-Zeile, Funde zuerst.
        easy_zeilen = []
        for p, e in sorted(_pers_map.items(),
                           key=lambda kv: (not kv[1].get("gemischt"),
                                           -(kv[1].get("kritisch", 0)
                                             + kv[1].get("redundant", 0)
                                             + kv[1].get("unter", 0)
                                             + kv[1].get("unmessbar", 0)))):
            funde_p = (e.get("kritisch", 0) + e.get("redundant", 0)
                       + e.get("unter", 0) + e.get("unmessbar", 0))
            if funde_p:
                status = (t("qualitaet.person.funde", n=funde_p)
                          + (' &middot; <span style="color:var(--crit)">'
                             + t("qualitaet.person.verwechselt") + '</span>'
                             if e.get("kritisch") else ""))
            else:
                status = ('<span style="color:seagreen">&#10003; '
                          + t("qualitaet.person.alles_gut") + '</span>')
            # Stufe C (.511): die PERSONEN-Warnung der Identitaets-Achse. Sie
            # steht hier und nicht als Bild-Marke, weil die Marge genau so
            # gemessen wurde: als Einzelbild-Signal lieferte sie fast nur, was
            # die Guete-Latte ohnehin liefert (63 von 65 Faellen), als
            # Personen-Muster den einzigen sauberen Fremdbild-Treffer.
            if e.get("gemischt"):
                status += (' &middot; <span style="color:var(--crit)">&#9888; '
                           + t("qualitaet.person.gemischt") + '</span>')
            easy_zeilen.append(
                f'<a href="/qualitaet?person={urllib.parse.quote(p)}" '
                'style="display:block;padding:9px 12px;margin:4px 0;'
                'border:1px solid var(--border);border-radius:8px;'
                'text-decoration:none;color:var(--text)">'
                f'<b>{html.escape(p)}</b> &mdash; {status}</a>')
        pers_easy = ('<div style="max-width:520px">' + "".join(easy_zeilen)
                     + '</div>')
        # .286 (S9-Fang am Prod-Datenbestand): die Zehn-Spalten-Tabelle ist
        # ~785 px breit und lief auf Handy-Breiten waagerecht ueber — sie
        # scrollt jetzt in ihrem eigenen Container statt die Seite zu
        # sprengen (Testbett-Daten haben keine personen-Map, dort war S9
        # blind fuer den Fall).
        pers_tab = ('<div style="overflow-x:auto">'
                    '<table style="margin:4px 0 8px"><tr>'
                    f'<th>{t("qualitaet.tabelle.kopf_person")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_bilder")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_gut")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_mittel")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_unter")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_links")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_front")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_rechts")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_doppel")}</th>'
                    f'<th>{t("qualitaet.tabelle.kopf_verwechslung")}</th>'
                    '</tr>' + zeilen + '</table></div>')
        # .273c (User: 'dass der User sieht: mir fehlen Bilder von der
        # Seite'): ehrliche Luecken-Hinweise je Person, kein Bandwurm.
        # Stufe-0-Grenze (§8.3): "no X and no Y yet …" spliced Satzteile
        # ueber " and no ".join — bleibt literal bis zum Ganz-Satz-Umbau.
        luecken = []
        for p, e in sorted(_pers_map.items()):
            if e.get("n", 0) < 3 or "links" not in e:
                continue
            fehlt = [w for w, k in (("side views (left)", "links"),
                                    ("frontal views", "frontal"),
                                    ("side views (right)", "rechts"))
                     if e.get(k, 0) == 0]
            if fehlt:
                luecken.append(f'<b>{html.escape(p)}</b>: no '
                               + " and no ".join(fehlt)
                               + ' yet &mdash; they come from passes close '
                                 'to a camera at that angle.')
        if luecken:
            pers_tab += ('<p class="dim" style="margin:0 0 10px">'
                         + "<br>".join(luecken) + "</p>")
        pers_tab = (pers_easy + '<div class="nur-expert">' + pers_tab
                    + '</div>')
    # Stufe-0-Grenze (§8.1): <b>-Name + <a>-Link mitten im Satz — literal.
    filt = (f' &middot; showing only <b>{html.escape(str(person))}</b> '
            f'(<a href="/qualitaet">show everyone</a>; '
            'checked against the whole library)'
            if person else "")
    # .273b (User: 'vom Ablauf muss es so sein, dass es jeder versteht'):
    # EIN Klartext-Ergebnis-Satz vor allen Tabellen — was wurde geprueft,
    # was ist zu tun. Zahlen kommen aus dem Bericht, nichts wird erfunden.
    def _uebersicht_zaehlen():
        """Die BEFUND-Zahlen der Uebersicht -> ({reiter: n}, n_verwechselt).

        .512 (Feldtester 09.09.): bis .511 addierte der Satz vier Groessen, die
        DIESELBEN Bilder mehrfach enthielten — `len(krit) + len(ug) +
        len(doppel) + vorschlag`. Auf dem Feldtester-Bestand ergab das 734
        "Funde" auf 1185 Bilder, obwohl nur 772 Kacheln ueberhaupt markiert
        waren: `ug` fuehrte 171 unscharf-Befunde, von denen der Stufe-C-Zweig
        110 noch einmal als `raus` zaehlte. Gezaehlt wird jetzt nach DERSELBEN
        exklusiven Reiter-Regel wie in der Galerie (`reiter_gruppe`) — jedes
        Bild genau einmal, die Summe der Gruppen ist die Zahl der markierten
        Bilder.

        Der Behalten-Kandidat einer Byte-Kopien-Gruppe zaehlt NICHT als Fund:
        er bleibt ja liegen. Deshalb steht unter "dubl" nur das Ueberzaehlige —
        genau die Menge, die auch der Reiter im Titel nennt."""
        noface_s = {(u["person"], u["datei"]) for u in ug
                    if u.get("hauptgrund") == "kein_gesicht"}
        verw_s, krit_s = set(), set()
        for pr in paare:
            beide = {(pr["a_person"], pr["a_datei"]),
                     (pr["b_person"], pr["b_datei"])}
            if person:
                beide = {k for k in beide if k[0] == person}
            verw_s |= beide
            if pr.get("kritisch"):
                krit_s |= beide
        dupw_s = {(d["person"], d["datei"]) for d in doppel}
        dubl_alle_s, dubl_extra_s = set(), set()
        for g in (qs.get("dubletten") or []):
            p_ = g.get("person")
            # Ohne Person ist die Gruppe nicht zuzuordnen — ueberspringen statt
            # _da(None, …) laufen zu lassen (Alt-/Fremdbericht, Klasse
            # "Nutzer-Zustand, den das Testbett nicht hat").
            if not p_ or not g.get("behalten"):
                continue
            if (person and p_ != person) or not _da(p_, g["behalten"]):
                continue
            weg_ = [d for d in (g.get("weg") or []) if _da(p_, d)]
            if not weg_:                    # Gruppe ohne Kopien ist keine Gruppe
                continue
            dubl_alle_s.add((p_, g["behalten"]))
            dubl_alle_s.update((p_, d) for d in weg_)
            dubl_extra_s.update((p_, d) for d in weg_)
        urteil = {}
        for p_, karte in (qs.get("pruefung") or {}).items():
            if (person and p_ != person) or not isinstance(karte, dict):
                continue
            for d_, z in karte.items():
                if isinstance(z, dict) and z.get("u") in ("raus", "auffaellig") \
                        and _da(p_, d_):
                    urteil[(p_, d_)] = z["u"]
        zahl = {g: 0 for g in REITER_ORDNUNG}
        n_verw = 0
        for k in (noface_s | dubl_alle_s | verw_s | dupw_s | set(urteil)):
            grp = reiter_gruppe(k, noface_s, dubl_alle_s, verw_s, dupw_s,
                                urteil.get(k))
            if grp == "dubl" and k not in dubl_extra_s:
                continue                    # Behalten-Kandidat: kein Fund
            zahl[grp] += 1
            if grp != "gut" and k in krit_s:
                n_verw += 1
        zahl.pop("gut", None)
        return zahl, n_verw

    ergebnis_satz = ""
    if qs.get("ts"):
        _zahl, _n_verw = _uebersicht_zaehlen()
        _funde = sum(_zahl.values())
        _np = len(qs.get("personen") or {}) or "?"
        if _funde == 0:
            # Die <b>-Grenze trennt zwei VOLLSTAENDIGE Saetze — B9-sicherer
            # Split an der Markup-Grenze.
            ergebnis_satz = (
                '<p style="font-size:15px">&#9989; <b>'
                + t("qualitaet.ergebnis.alles_gut") + '</b> '
                + t("qualitaet.ergebnis.alles_gut_satz",
                    n=qs.get("ref_count", "?"), np=_np)
                + '</p>')
        else:
            # Stufe-0-Grenze (§8.3): der Funde-Satz joint <b>-Zaehler-
            # Fragmente mit ", "/" and " — bleibt literal.
            # .512: die Fragmente sind jetzt die REITER der Galerie, in
            # derselben Reihenfolge und mit denselben Zahlen. Wer den Satz
            # liest und dann auf eine Person klickt, findet die Zahl wieder —
            # vorher nannte der Satz Klassen ("weak"), die es als Reiter gar
            # nicht gab, und zaehlte Bilder doppelt.
            # "(s)" statt Plural-Formen — dieselbe Bauform wie die uebrigen
            # Antworten dieser Familie (antwort.ref_batch_weg).
            _wort = {"check": "to check", "weg": "suggested for removal",
                     "dubl": "identical copy(s)", "noface": "with no face found"}
            teile = [f'<b>{_zahl[g]}</b> {_wort[g]}'
                     for g in REITER_ORDNUNG if g in _wort and _zahl[g]]
            # Die Verwechslungs-Zahl ist eine TEILMENGE der obigen (fast immer
            # von "to check") und steht deshalb als eigener Satz, nicht als
            # fuenfter Summand — sonst waere die Doppelzaehlung sofort zurueck.
            _mix = (f'<b>{_n_verw}</b> of those may be mixed up with another '
                    'person. ' if _n_verw else '')
            ergebnis_satz = (
                f'<p style="font-size:15px">&#128269; Checked '
                f'{qs.get("ref_count", "?")} pictures of {_np} people '
                f'&mdash; {" and ".join([", ".join(teile[:-1]), teile[-1]] if len(teile) > 1 else teile)}. '
                f'{_mix}Nothing is deleted unless you say so.</p>')
    kopf = (f'<h2>{t("qualitaet.kopf.titel")}</h2>' + lauf_zeile
            + ergebnis_satz
            + f'<p class="dim">{t("qualitaet.kopf.hinweis")}</p>'
            + pers_tab
            + '<p>' + t("qualitaet.kopf.stand", stand=stand,
                        n=qs.get("ref_count", "?")) + filt + ' '
            f'<button class="gtb on" onclick="refPruefNeu(this)">'
            f'{t("qualitaet.kopf.knopf_neu")}</button></p>')

    # .277 (User: 'Wie will ein User das verstehen? EINE Seite je Person,
    # alle Gesichter, schlechte markiert — nicht mit technischen Werten'):
    # die Personen-GALERIE ersetzt die frueheren drei Detail-Reiter (seit
    # .280 fuer ALLE — die Reiter sind weg).
    if person:
        pdir = os.path.join(refs_base, person)
        try:
            alle = sorted(f for f in os.listdir(pdir)
                          if f.lower().endswith((".jpg", ".jpeg", ".png",
                                                 ".webp")))
        except FileNotFoundError:
            alle = []
        stufen = (qs.get("stufen") or {}).get(person, {})
        gruende = {u["datei"]: u for u in ug if u["person"] == person}
        dup_weg = {d["datei"]: d for d in doppel}
        dup_kept = {d["behalten"] for d in doppel}
        verwechselt = {}          # datei -> (fremde Person, deren Bild)
        for pr in paare:
            if pr["a_person"] == person:
                verwechselt.setdefault(pr["a_datei"],
                                       (pr["b_person"], pr["b_datei"]))
            if pr["b_person"] == person:
                verwechselt.setdefault(pr["b_datei"],
                                       (pr["a_person"], pr["a_datei"]))
        # .279 (User: '97 Bilder erschlagen — drei Gruppen: gut / pruefen /
        # loeschen, als Registerkarten mit Select all/Deselect all, Knoepfe
        # nach OBEN'): Kacheln in drei Reitern statt einer Bandwurmliste.
        # Zuordnung folgt der bestehenden Befund-Semantik: Verwechslung =
        # Mensch muss draufschauen (check), Eignung/Doppel = Loesch-
        # VORSCHLAG (weg, nie vorgehakt), Rest = gut.
        # Stufe C (.511) haengt ZWEI Reiter an, beide nach dem Zuschnitt des Users
        # eigene Gruppen statt Marken in der Bandwurmliste:
        #   dubl   = BYTE-gleiche Dateien, als Satz gezeigt (der erste bleibt,
        #            die Kopien sind vorgewaehlt-faehig)
        #   noface = Bilder, in denen keine Detektion ein Gesicht fand — sie
        #            tragen keine einzige Messung und sind deshalb kein
        #            Guete-Fall, sondern ein Durchsicht-Fall.
        # Zuordnung ist EXKLUSIV (ein Bild steht in genau einem Reiter): sonst
        # zaehlte der Remove-Zaehler dieselbe Datei zweimal. Die Regel selbst
        # steht seit .512 in `reiter_gruppe` — EINE Quelle fuer Galerie UND
        # Uebersichts-Zaehlung.
        pruefung = (qs.get("pruefung") or {}).get(person, {})
        dubl_gruppen = [g for g in (qs.get("dubletten") or [])
                        if g.get("person") == person
                        and _da(person, g.get("behalten"))]
        for g in dubl_gruppen:
            g["weg"] = [d for d in (g.get("weg") or []) if _da(person, d)]
        # .512: Gruppen OHNE ueberzaehlige Kopie fallen VOR der Mengenbildung
        # weg. Bis .511 blieb ihr Behalten-Kandidat in `dubl_alle` — er bekam
        # den Reiter "dubl", wurde dort aber nicht gerendert (der Reiter zeigt
        # nur `dubl_gruppen`) und verschwand damit ganz von der Seite.
        dubl_gruppen = [g for g in dubl_gruppen if g["weg"]]
        dubl_alle, dubl_extra = set(), set()
        for g in dubl_gruppen:
            dubl_alle.add(g["behalten"])
            dubl_alle.update(g["weg"])
            dubl_extra.update(g["weg"])
        noface = {d for d, u in gruende.items()
                  if u.get("hauptgrund") == "kein_gesicht"}
        gruppen_k = {g: [] for g in REITER_ORDNUNG}
        dubl_kacheln = {}
        dubl_funde = 0

        def _kachel(f, rand, wort, zusatz, markiert, behalten=False):
            src = f'/refs/{urllib.parse.quote(person)}/{urllib.parse.quote(f)}'
            val = html.escape(person + "|" + f, quote=True)
            return (
                f'<label style="display:inline-block;text-align:center;'
                f'margin:5px;vertical-align:top;max-width:120px">'
                f'<img src="{src}" style="height:110px;border-radius:6px;'
                f'display:block;margin:0 auto 3px;border:3px solid {rand}">'
                f'<input type="checkbox" class="us-cb g-person" '
                + ('data-behalten="1" ' if behalten else "")
                + f'value="{val}"> <span class="{"dim" if not markiert else ""}"'
                f' style="font-size:12px">{wort or t("qualitaet.galerie.okay")}'
                f'{zusatz}'
                '</span></label>')

        for f in alle:
            rand, wort, zusatz = "var(--border)", "", ""
            pz = pruefung.get(f) or {}
            # Stufe C (.511): das zweistufige URTEIL auf den gemessenen Achsen.
            # Seit .512 ist es auf DIESER Seite das einzige Guete-Wort — die
            # alte Pixel-Achse (`gruende`: unscharf/zu_klein/defekt) urteilt
            # hier nicht mehr mit, s. reiter_gruppe().
            _u, _g = pz.get("u"), pz.get("g") or ""
            _uwort = ""
            if _u == "raus":
                _uwort = t("qualitaet.galerie.unter_beide")
            elif _u == "auffaellig":
                _uwort = (t("qualitaet.galerie.unter_norm") if _g == "norm"
                          else t("qualitaet.galerie.unter_guete"))
            grp = reiter_gruppe(f, noface, dubl_alle, verwechselt, dup_weg, _u)
            if grp == "noface":
                rand = "var(--warn)"
                wort = t("qualitaet.wort.kein_gesicht")
            elif grp == "dubl":
                if f in dubl_extra:
                    rand, wort = "var(--dim)", t("qualitaet.galerie.dubl_weg")
                else:
                    rand, wort = "seagreen", t("qualitaet.galerie.dubl_behalten")
            elif f in verwechselt:
                vp, vd = verwechselt[f]
                rand = "var(--crit)"
                # {name} kommt escaped (Muster lernanker {kamera}).
                wort = t("qualitaet.galerie.looks_like",
                         name=html.escape(vp))
                # .280: das GEGENBILD als Mini-Thumb — ersetzt den alten
                # Confusion-Tab (dort stand das Paar nebeneinander).
                zusatz = (f'<img src="/refs/{urllib.parse.quote(vp)}/'
                          f'{urllib.parse.quote(vd)}" '
                          f'title="{html.escape(vp)}" '
                          'style="height:34px;border-radius:4px;'
                          'vertical-align:middle;margin-left:4px;'
                          'border:1px solid var(--crit)">')
            elif f in dup_weg:
                rand = "var(--dim)"
                wort = t("qualitaet.galerie.doppel")
            elif _uwort:
                rand = "var(--warn)" if _u == "raus" else "var(--dim)"
                wort = _uwort
            if _uwort and wort != _uwort:
                # Beziehungs-Befund (Verwechslung/Dublette) traegt den Reiter,
                # die Guete-Marke steht als Zusatz daneben.
                zusatz += (f' <span class="dim" style="font-size:11px">'
                           f'&middot; {_uwort}</span>')
            if not wort and stufen.get(f) == "gut":
                rand, wort = "seagreen", t("qualitaet.galerie.gut")
            elif not wort and f in dup_kept:
                rand, wort = "seagreen", t("qualitaet.galerie.gut_behalten")
            # Virtuelle Qualitaetslinie (User 20.08.): die Feature-Norm jeder
            # messbaren Referenz als Mini-Zusatz auf der Kachel — dieselbe
            # Skala wie die Katalog-Linie; Vorrats-Referenzen (Beiwert)
            # tragen ihr Herkunfts-Wort.
            _nq = (qs.get("normen") or {}).get(person, {}).get(f)
            if f in set(qs.get("vorrat_refs") or []):
                zusatz += (f' <span class="dim" style="font-size:11px">'
                           f'{t("qualitaet.galerie.vorrat")}</span>')
            if _nq is not None:
                zusatz += (f' <span class="dim" style="font-size:11px">'
                           f'{t("qualitaet.galerie.norm", norm="%.1f" % _nq)}</span>')
            # Basispaket-Rang (ANZEIGE, nie eine Latte) und — nur in der
            # Expert-Sicht — die Identitaets-Marge als Info-Zahl sowie der
            # Hinweis, dass die Guete einer Vorrats-Referenz an ihrem
            # gespeicherten Ausschnitt gemessen wurde und nicht bei der Ernte.
            if pz.get("r") is not None:
                zusatz += (f' <span class="dim" style="font-size:11px">'
                           f'{t("qualitaet.galerie.rang", rang=int(pz["r"]))}</span>')
            if pz.get("m") is not None:
                zusatz += (f' <span class="dim nur-expert" style="font-size:11px">'
                           f'{t("qualitaet.galerie.marge", marge="%.2f" % pz["m"])}'
                           f'</span>')
            if pz.get("q") == "datei":
                zusatz += (f' <span class="dim nur-expert" style="font-size:11px">'
                           f'{t("qualitaet.galerie.guete_datei")}</span>')
            markiert = grp != "gut"
            _k = _kachel(f, rand, wort, zusatz, markiert,
                         behalten=(grp == "dubl" and f not in dubl_extra))
            gruppen_k[grp].append(_k)
            if grp == "dubl":
                dubl_kacheln[f] = _k
                if f in dubl_extra:
                    dubl_funde += 1
        # .512: EIN Bild = EIN Fund. Bis .511 stand hier `len(dubl_extra)` —
        # eine ueberzaehlige Byte-Kopie, in der auch kein Gesicht gefunden
        # wurde, sitzt aber im noface-Reiter und waere doppelt gezaehlt worden.
        # Gezaehlt wird jetzt, was wirklich in einem Befund-Reiter LIEGT.
        funde_n = (len(gruppen_k["check"]) + len(gruppen_k["weg"])
                   + dubl_funde + len(gruppen_k["noface"]))
        satz = (t("qualitaet.galerie.satz_gut", n=len(alle))
                if funde_n == 0 else
                t("qualitaet.galerie.satz_funde", funde=funde_n,
                  n=len(alle)))
        start = ("check" if gruppen_k["check"] else
                 "weg" if gruppen_k["weg"] else
                 "dubl" if gruppen_k["dubl"] else
                 "noface" if gruppen_k["noface"] else "gut")
        REITER = [("gut", t("qualitaet.reiter.gut",
                            n=len(gruppen_k['gut']))),
                  ("check", t("qualitaet.reiter.check",
                              n=len(gruppen_k['check']))),
                  ("weg", t("qualitaet.reiter.weg",
                            n=len(gruppen_k['weg']))),
                  ("dubl", t("qualitaet.reiter.dubl",
                             n=dubl_funde)),
                  ("noface", t("qualitaet.reiter.noface",
                               n=len(gruppen_k['noface'])))]
        leiste = ("".join(
            f'<button class="gtb{" on" if g == start else ""}" id="qgt-{g}" '
            f'onclick="qgTab(\'{g}\')">{txt}</button> '
            for g, txt in REITER)
            + '<span style="margin:0 6px;color:var(--border)">|</span>'
            '<button class="gtb" onclick="qgAlle(true)">'
            + t("qualitaet.galerie.knopf_alle") + '</button> '
            '<button class="gtb" onclick="qgAlle(false)">'
            + t("qualitaet.galerie.knopf_keine") + '</button> '
            # .512: der Knopf traegt den BESTAND dieser Person mit (Person +
            # Zahl). Daraus erkennt refBatchLoeschen, ob die Auswahl den
            # gesamten Rest umfasst, und fragt dann ein zweites Mal — mit Namen
            # und Anzahl. Die Zahl kommt von hier und nicht aus dem Abzaehlen
            # der Kacheln: im Kopien-Reiter steht nicht jede Datei einzeln.
            '<button class="gtb on" onclick="refBatchLoeschen(this)" '
            f'data-person="{html.escape(person, quote=True)}" '
            f'data-bestand="{len(alle)}">'
            + t("qualitaet.galerie.knopf_entfernen")
            + '</button> <span id="qg-n" class="dim"></span>')
        # Stufe C: die zwei neuen Reiter tragen einen eigenen Erklaersatz —
        # "identische Kopien" und "kein Gesicht gefunden" sind Befunde, die
        # ohne einen Satz Erklaerung wie ein Vorwurf aussehen.
        _kopfsatz = {"dubl": t("qualitaet.galerie.dubl_hinweis"),
                     "noface": t("qualitaet.galerie.noface_hinweis")}
        # Der Dubletten-Reiter zeigt SAETZE, nicht eine Bandwurmliste: je
        # md5-Gruppe der Behalten-Kandidat zuerst, die Kopien dahinter. Sonst
        # saehe der Nutzer 135 gleich aussehende Kacheln, ohne zu erkennen,
        # welche zu welcher gehoert.
        _dubl_html = "".join(
            '<div style="border:1px solid var(--border);border-radius:8px;'
            'padding:4px 6px;margin:6px 0;display:inline-block;'
            'vertical-align:top">'
            + "".join(dubl_kacheln.get(d, "")
                      for d in [g["behalten"]] + list(g["weg"]))
            + '</div>' for g in dubl_gruppen)

        def _box(g, ks):
            inhalt = (_dubl_html if g == "dubl" else "".join(ks))
            if not inhalt:
                return f'<p class="dim">{t("qualitaet.galerie.leer_gruppe")}</p>'
            satz_g = _kopfsatz.get(g)
            return ((f'<p class="dim" style="max-width:640px">{satz_g}</p>'
                     if satz_g else "") + inhalt)
        boxen = "".join(
            f'<div id="qg-{g}" style="margin-top:8px;'
            f'display:{"block" if g == start else "none"}">'
            + _box(g, ks) + '</div>' for g, ks in gruppen_k.items())
        # Der Zaehler neben Remove zaehlt ALLE Haken (auch in gerade
        # verdeckten Reitern) — refBatchLoeschen loescht genau diese Menge,
        # der Knopf darf nie weniger versprechen als er tut.
        # Stufe 2 Tranche D (§8.4): der Zaehler-Anhang kommt server-seitig
        # via json.dumps(t(...)) byte-treu in den Script-Text (§8.10-Split
        # an der Konkatenationsgrenze, tickende Zahl bleibt Code — §8.20).
        # Stufe C: die Reiter-Namen stehen an ZWEI Stellen im JS — deshalb als
        # EINE Konstante hinein (K3: ein Reiter, den nur qgTab kennt, waere fuer
        # 'Select all' unsichtbar). Der Schutz `data-behalten` ist die Sperre
        # gegen den einen Klick, der einen ganzen Dubletten-Satz leeren wuerde:
        # 'Alle auswaehlen' laesst im Kopien-Reiter genau den Behalten-
        # Kandidaten jeder Gruppe stehen — das ist der 'alle bis auf eines'-
        # Klick des Bauplans.
        _ks_js = json.dumps([g for g, _txt in REITER])
        js = ('<script>var QG_KS=' + _ks_js + ';\n'
              'function qgTab(g){QG_KS.forEach('
              'function(k){document.getElementById("qg-"+k).style.display='
              '(k===g)?"block":"none";document.getElementById("qgt-"+k)'
              '.className=(k===g)?"gtb on":"gtb";});}\n'
              'function qgZaehl(){var n=document.querySelectorAll('
              '".us-cb:checked").length;document.getElementById("qg-n")'
              '.textContent=n?n+'
              + json.dumps(t("qualitaet.galerie.js_gewaehlt")) + ':"";}\n'
              'function qgAlle(an){var ks=QG_KS,i,box=null;'
              'for(i=0;i<ks.length;i++){var el=document.getElementById('
              '"qg-"+ks[i]);if(el.style.display!=="none"){box=el;break;}}'
              'if(!box)return;var cbs=box.querySelectorAll(".us-cb");'
              'for(i=0;i<cbs.length;i++){if(an&&cbs[i].getAttribute('
              '"data-behalten")==="1")continue;cbs[i].checked=an;}qgZaehl();}\n'
              'document.addEventListener("change",function(e){if(e.target'
              '&&e.target.classList&&e.target.classList.contains("us-cb"))'
              'qgZaehl();});</script>')
        # Stufe C: die PERSONEN-Warnung der Identitaets-Achse steht ueber der
        # Galerie und nennt ihre Zahlen — "wirkt gemischt" ohne {neg} von {n}
        # waere ein Verdacht ohne Beleg. Sie schlaegt NICHTS zum Loeschen vor.
        _pe = (qs.get("personen") or {}).get(person) or {}
        gemischt_zeile = ""
        if _pe.get("gemischt"):
            gemischt_zeile = (
                '<p style="color:var(--crit);max-width:640px">&#9888; '
                + t("qualitaet.galerie.gemischt",
                    neg=int(_pe.get("marge_neg") or 0),
                    n=int(_pe.get("marge_n") or 0),
                    fremd=html.escape(str(_pe.get("fremd") or "?")))
                + '</p>')
        koerper = (
            f'<h2>{t("qualitaet.galerie.titel", name=html.escape(person))}</h2>'
            f'<p><a href="/qualitaet">{t("qualitaet.galerie.link_zurueck")}</a></p>'
            + lauf_zeile + gemischt_zeile
            + f'<p style="font-size:15px">{satz}</p>'
            + (f'<div style="margin:2px 0 4px">{leiste}</div>' + boxen + js
               if alle else
               f'<p>{t("qualitaet.galerie.leer_person")}</p>'))
        return koerper
    # .280: keine Unter-Tabs mehr — die Uebersicht IST die Seite; ohne
    # ersten Lauf ehrlich sagen, dass noch nichts berechnet wurde.
    if not qs.get("ts"):
        return kopf + webui.leer(t("qualitaet.leer.titel"),
                                 t("qualitaet.leer.hinweis"))
    return kopf
