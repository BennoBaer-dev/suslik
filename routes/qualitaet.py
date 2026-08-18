"""routes/qualitaet — Qualitaets-Seite: Uebersicht (Klartext-Satz + Personen-
Liste) und je Person die GALERIE mit drei Reitern (Good / Check these /
Suggest removing). Die alten Unter-Tabs Verwechslung/Eignung/Doppel sind seit
.280 WEG (User 18.08., am kaputten Confusion-Layout: 'kann alles weg, kommt
an einen anderen Ort und optisch besser') — alle drei Befund-Arten leben in
der Galerie, Verwechslungs-Kacheln tragen das Gegenbild als Mini-Thumb.
Der Handler laedt das QS-JSON (anlernen.QS_PATH) und reicht es mit data_dir
herein; hier wird NUR gerendert (inkl. Existenz-Filter gegen tote Bild-Links,
User-Befund 19.07.)."""
import datetime
import html
import json  # noqa: F401 (Kontrakt-Naehe zum Bestand; Laden macht der Handler)
import os
import urllib.parse

import webui


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
        lauf_zeile = ('<p style="color:var(--crit)">last check FAILED: '
                      f'{html.escape(str(lauf["fehler"])[:180])} &mdash; '
                      'start it again.</p>')
    elif lauf and aktiv:
        # .282 (User: 'Banner springt immer wieder zurueck'): die GALERIE
        # refresht sich NIE selbst — der 3-s-Reload warf Reiter-Wahl und
        # gesetzte Haken weg. Nur die Uebersicht (ohne Checkboxen) darf.
        lauf_zeile = (f'<p>&#9203; checking picture {int(lauf.get("i", 0))} '
                      f'of {int(lauf.get("n", 0))} &hellip; '
                      + ('reload this page afterwards for the fresh '
                         'result.</p>' if person else
                         'the page refreshes on its own.</p>'))
    elif lauf:
        lauf_zeile = ('<p style="color:var(--warn)">the last check did not '
                      'finish (service restart or it was stopped) &mdash; '
                      'start it again.</p>')
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
                status = (f'{funde_p} picture(s) worth a look'
                          + (' &middot; <span style="color:var(--crit)">maybe '
                             'mixed-up</span>' if e.get("kritisch") else ""))
            else:
                status = '<span style="color:seagreen">&#10003; all good</span>'
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
                    '<table style="margin:4px 0 8px"><tr><th>person</th>'
                    '<th>pictures</th><th>good</th><th>fair</th>'
                    '<th>below bar</th><th>&larr; left</th><th>front</th>'
                    '<th>right &rarr;</th><th>duplicates</th>'
                    '<th>confusion</th></tr>' + zeilen + '</table></div>')
        # .273c (User: 'dass der User sieht: mir fehlen Bilder von der
        # Seite'): ehrliche Luecken-Hinweise je Person, kein Bandwurm.
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
            ergebnis_satz = (
                f'<p style="font-size:15px">&#9989; <b>All good.</b> Checked '
                f'{qs.get("ref_count", "?")} pictures of {_np} people &mdash; '
                'nothing needs your attention.</p>')
        else:
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
    kopf = (f"<h2>Quality — reference library</h2>" + lauf_zeile
            + ergebnis_satz
            + '<p class="dim">tap a person below to see all their '
            'pictures with the weak ones marked.</p>'
            + pers_tab
            + f'<p>As of: {stand} · {qs.get("ref_count", "?")} references{filt} '
            f'<button class="gtb on" onclick="refPruefNeu(this)">Re-check now</button></p>')

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
        WORT = {"defekt": "broken file", "kein_gesicht": "no face found",
                "zu_klein": "too small", "unscharf": "blurry"}
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
                wort = f"looks like {html.escape(vp)}"
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
                wort = "duplicate — the kept one covers it"
            elif f in gruende:
                rand, grp = "var(--warn)", "weg"
                wort = WORT.get(gruende[f]["hauptgrund"], "weak picture")
            elif stufen.get(f) == "gut":
                rand, wort = "seagreen", "good"
            elif f in dup_kept:
                rand, wort = "seagreen", "good — kept of its duplicates"
            markiert = grp != "gut"
            val = html.escape(person + "|" + f, quote=True)
            gruppen_k[grp].append(
                f'<label style="display:inline-block;text-align:center;'
                f'margin:5px;vertical-align:top;max-width:120px">'
                f'<img src="{src}" style="height:110px;border-radius:6px;'
                f'display:block;margin:0 auto 3px;border:3px solid {rand}">'
                f'<input type="checkbox" class="us-cb g-person" '
                f'value="{val}"> <span class="{"dim" if not markiert else ""}"'
                f' style="font-size:12px">{wort or "okay"}{zusatz}'
                '</span></label>')
        funde_n = len(gruppen_k["check"]) + len(gruppen_k["weg"])
        satz = (f"All {len(alle)} pictures look fine." if funde_n == 0 else
                f"{funde_n} of {len(alle)} pictures are worth a look — "
                "the two right-hand tabs hold them. Tick what you want to "
                "remove — nothing happens without your click.")
        start = ("check" if gruppen_k["check"] else
                 "weg" if gruppen_k["weg"] else "gut")
        REITER = [("gut", f"Good ({len(gruppen_k['gut'])})"),
                  ("check", f"Check these ({len(gruppen_k['check'])})"),
                  ("weg", f"Suggest removing ({len(gruppen_k['weg'])})")]
        leiste = ("".join(
            f'<button class="gtb{" on" if g == start else ""}" id="qgt-{g}" '
            f'onclick="qgTab(\'{g}\')">{txt}</button> '
            for g, txt in REITER)
            + '<span style="margin:0 6px;color:var(--border)">|</span>'
            '<button class="gtb" onclick="qgAlle(true)">Select all</button> '
            '<button class="gtb" onclick="qgAlle(false)">Deselect all'
            '</button> '
            '<button class="gtb on" onclick="refBatchLoeschen(this)">'
            'Remove selected</button> <span id="qg-n" class="dim"></span>')
        boxen = "".join(
            f'<div id="qg-{g}" style="margin-top:8px;'
            f'display:{"block" if g == start else "none"}">'
            + ("".join(ks) or '<p class="dim">nothing in this group.</p>')
            + '</div>' for g, ks in gruppen_k.items())
        # Der Zaehler neben Remove zaehlt ALLE Haken (auch in gerade
        # verdeckten Reitern) — refBatchLoeschen loescht genau diese Menge,
        # der Knopf darf nie weniger versprechen als er tut.
        js = ('<script>function qgTab(g){["gut","check","weg"].forEach('
              'function(k){document.getElementById("qg-"+k).style.display='
              '(k===g)?"block":"none";document.getElementById("qgt-"+k)'
              '.className=(k===g)?"gtb on":"gtb";});}\n'
              'function qgZaehl(){var n=document.querySelectorAll('
              '".us-cb:checked").length;document.getElementById("qg-n")'
              '.textContent=n?n+" selected":"";}\n'
              'function qgAlle(an){var ks=["gut","check","weg"],i,box=null;'
              'for(i=0;i<ks.length;i++){var el=document.getElementById('
              '"qg-"+ks[i]);if(el.style.display!=="none"){box=el;break;}}'
              'if(!box)return;var cbs=box.querySelectorAll(".us-cb");'
              'for(i=0;i<cbs.length;i++)cbs[i].checked=an;qgZaehl();}\n'
              'document.addEventListener("change",function(e){if(e.target'
              '&&e.target.classList&&e.target.classList.contains("us-cb"))'
              'qgZaehl();});</script>')
        koerper = (
            f'<h2>{html.escape(person)} — picture quality</h2>'
            f'<p><a href="/qualitaet">&larr; back to the overview</a></p>'
            + lauf_zeile
            + f'<p style="font-size:15px">{satz}</p>'
            + (f'<div style="margin:2px 0 4px">{leiste}</div>' + boxen + js
               if alle else '<p>no pictures for this person.</p>'))
        return koerper
    # .280: keine Unter-Tabs mehr — die Uebersicht IST die Seite; ohne
    # ersten Lauf ehrlich sagen, dass noch nichts berechnet wurde.
    if not qs.get("ts"):
        return kopf + webui.leer("No check computed yet.",
                                 "Click Re-check now above.")
    return kopf
