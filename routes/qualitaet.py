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
    krit = [p for p in paare if p.get("kritisch")]
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
                           key=lambda kv: -(kv[1].get("kritisch", 0)
                                            + kv[1].get("redundant", 0)
                                            + kv[1].get("unter", 0)
                                            + kv[1].get("unmessbar", 0))):
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
    ergebnis_satz = ""
    if qs.get("ts"):
        _funde = len(krit) + len(ug) + len(doppel)
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
            teile = []
            if krit:
                teile.append(f'<b>{len(krit)}</b> possibly mixed-up')
            if ug:
                teile.append(f'<b>{len(ug)}</b> weak')
            if doppel:
                teile.append(f'<b>{len(doppel)}</b> near-duplicate')
            ergebnis_satz = (
                f'<p style="font-size:15px">&#128269; Checked '
                f'{qs.get("ref_count", "?")} pictures of {_np} people '
                f'&mdash; {" and ".join([", ".join(teile[:-1]), teile[-1]] if len(teile) > 1 else teile)} '
                'picture(s) worth a look &mdash; nothing is deleted unless '
                'you say so.</p>')
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
        # Anzeige-Map zur Render-Zeit (Funktion statt Konstante, §8.12).
        WORT = {"defekt": t("qualitaet.wort.defekt"),
                "kein_gesicht": t("qualitaet.wort.kein_gesicht"),
                "zu_klein": t("qualitaet.wort.zu_klein"),
                "unscharf": t("qualitaet.wort.unscharf")}
        # .279 (User: '97 Bilder erschlagen — drei Gruppen: gut / pruefen /
        # loeschen, als Registerkarten mit Select all/Deselect all, Knoepfe
        # nach OBEN'): Kacheln in drei Reitern statt einer Bandwurmliste.
        # Zuordnung folgt der bestehenden Befund-Semantik: Verwechslung =
        # Mensch muss draufschauen (check), Eignung/Doppel = Loesch-
        # VORSCHLAG (weg, nie vorgehakt), Rest = gut.
        gruppen_k = {"gut": [], "check": [], "weg": []}
        for f in alle:
            src = f'/refs/{urllib.parse.quote(person)}/{urllib.parse.quote(f)}'
            rand, wort, grp, zusatz = "var(--border)", "", "gut", ""
            if f in verwechselt:
                vp, vd = verwechselt[f]
                rand = "var(--crit)"
                # {name} kommt escaped (Muster lernanker {kamera}).
                wort = t("qualitaet.galerie.looks_like",
                         name=html.escape(vp))
                grp = "check"
                # .280: das GEGENBILD als Mini-Thumb — ersetzt den alten
                # Confusion-Tab (dort stand das Paar nebeneinander).
                zusatz = (f'<img src="/refs/{urllib.parse.quote(vp)}/'
                          f'{urllib.parse.quote(vd)}" '
                          f'title="{html.escape(vp)}" '
                          'style="height:34px;border-radius:4px;'
                          'vertical-align:middle;margin-left:4px;'
                          'border:1px solid var(--crit)">')
            elif f in dup_weg:
                rand, grp = "var(--dim)", "weg"
                wort = t("qualitaet.galerie.doppel")
            elif f in gruende:
                rand, grp = "var(--warn)", "weg"
                wort = WORT.get(gruende[f]["hauptgrund"],
                                t("qualitaet.wort.schwach"))
            elif stufen.get(f) == "gut":
                rand, wort = "seagreen", t("qualitaet.galerie.gut")
            elif f in dup_kept:
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
            markiert = grp != "gut"
            val = html.escape(person + "|" + f, quote=True)
            gruppen_k[grp].append(
                f'<label style="display:inline-block;text-align:center;'
                f'margin:5px;vertical-align:top;max-width:120px">'
                f'<img src="{src}" style="height:110px;border-radius:6px;'
                f'display:block;margin:0 auto 3px;border:3px solid {rand}">'
                f'<input type="checkbox" class="us-cb g-person" '
                f'value="{val}"> <span class="{"dim" if not markiert else ""}"'
                f' style="font-size:12px">{wort or t("qualitaet.galerie.okay")}'
                f'{zusatz}'
                '</span></label>')
        funde_n = len(gruppen_k["check"]) + len(gruppen_k["weg"])
        satz = (t("qualitaet.galerie.satz_gut", n=len(alle))
                if funde_n == 0 else
                t("qualitaet.galerie.satz_funde", funde=funde_n,
                  n=len(alle)))
        start = ("check" if gruppen_k["check"] else
                 "weg" if gruppen_k["weg"] else "gut")
        REITER = [("gut", t("qualitaet.reiter.gut",
                            n=len(gruppen_k['gut']))),
                  ("check", t("qualitaet.reiter.check",
                              n=len(gruppen_k['check']))),
                  ("weg", t("qualitaet.reiter.weg",
                            n=len(gruppen_k['weg'])))]
        leiste = ("".join(
            f'<button class="gtb{" on" if g == start else ""}" id="qgt-{g}" '
            f'onclick="qgTab(\'{g}\')">{txt}</button> '
            for g, txt in REITER)
            + '<span style="margin:0 6px;color:var(--border)">|</span>'
            '<button class="gtb" onclick="qgAlle(true)">'
            + t("qualitaet.galerie.knopf_alle") + '</button> '
            '<button class="gtb" onclick="qgAlle(false)">'
            + t("qualitaet.galerie.knopf_keine") + '</button> '
            '<button class="gtb on" onclick="refBatchLoeschen(this)">'
            + t("qualitaet.galerie.knopf_entfernen")
            + '</button> <span id="qg-n" class="dim"></span>')
        boxen = "".join(
            f'<div id="qg-{g}" style="margin-top:8px;'
            f'display:{"block" if g == start else "none"}">'
            + ("".join(ks)
               or f'<p class="dim">{t("qualitaet.galerie.leer_gruppe")}</p>')
            + '</div>' for g, ks in gruppen_k.items())
        # Der Zaehler neben Remove zaehlt ALLE Haken (auch in gerade
        # verdeckten Reitern) — refBatchLoeschen loescht genau diese Menge,
        # der Knopf darf nie weniger versprechen als er tut.
        # Stufe 2 Tranche D (§8.4): der Zaehler-Anhang kommt server-seitig
        # via json.dumps(t(...)) byte-treu in den Script-Text (§8.10-Split
        # an der Konkatenationsgrenze, tickende Zahl bleibt Code — §8.20).
        js = ('<script>function qgTab(g){["gut","check","weg"].forEach('
              'function(k){document.getElementById("qg-"+k).style.display='
              '(k===g)?"block":"none";document.getElementById("qgt-"+k)'
              '.className=(k===g)?"gtb on":"gtb";});}\n'
              'function qgZaehl(){var n=document.querySelectorAll('
              '".us-cb:checked").length;document.getElementById("qg-n")'
              '.textContent=n?n+'
              + json.dumps(t("qualitaet.galerie.js_gewaehlt")) + ':"";}\n'
              'function qgAlle(an){var ks=["gut","check","weg"],i,box=null;'
              'for(i=0;i<ks.length;i++){var el=document.getElementById('
              '"qg-"+ks[i]);if(el.style.display!=="none"){box=el;break;}}'
              'if(!box)return;var cbs=box.querySelectorAll(".us-cb");'
              'for(i=0;i<cbs.length;i++)cbs[i].checked=an;qgZaehl();}\n'
              'document.addEventListener("change",function(e){if(e.target'
              '&&e.target.classList&&e.target.classList.contains("us-cb"))'
              'qgZaehl();});</script>')
        koerper = (
            f'<h2>{t("qualitaet.galerie.titel", name=html.escape(person))}</h2>'
            f'<p><a href="/qualitaet">{t("qualitaet.galerie.link_zurueck")}</a></p>'
            + lauf_zeile
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
