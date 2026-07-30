"""routes/qualitaet — Qualitaets-Seite: Verwechslung + Eignung als Unter-Tabs (M1a,
byte-treu aus verifyd extrahiert; Muster auftritte.py). Der Handler laedt das QS-JSON
(anlernen.QS_PATH) und reicht es zusammen mit ansicht + data_dir herein; hier wird NUR
gerendert (inkl. Existenz-Filter gegen tote Bild-Links, User-Befund 19.07.)."""
import datetime
import html
import json  # noqa: F401 (Kontrakt-Naehe zum Bestand; Laden macht der Handler)
import os
import urllib.parse

import webui


def render(ansicht, qs, data_dir):
    """-> Seiten-INHALT (kopf+koerper; layout/banner bleiben beim Handler).
    ansicht ist vom Handler normalisiert ('verwechslung'|'eignung')."""
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
    krit = [p for p in paare if p.get("kritisch")]

    def _tab(name, txt):
        # War eine dritte Aktiv-Sprache auf derselben Seite: ein fest verdrahtetes
        # #2a9d5a (3.46:1) neben der Nav-Markierung und der .gtb.on-Fuellung. Jetzt
        # dieselbe Klasse wie ueberall, damit "aktiv" ueberall gleich aussieht — und
        # damit die Tinte aus --on-ink kommt statt aus einem festen Weiss.
        return (f'<a class="gtb{" on" if ansicht == name else ""}" '
                f'href="/qualitaet?ansicht={name}">{txt}</a>')
    kopf = (f"<h2>Quality — reference library</h2>"
            f'<div style="margin:6px 0 14px">'
            f'{_tab("verwechslung", f"Confusion ({len(krit)} critical)")} '
            f'{_tab("eignung", f"Suitability ({len(ug)} suggestions)")}</div>'
            f'<p>As of: {stand} · {qs.get("ref_count", "?")} references '
            f'<button class="gtb on" onclick="refPruefNeu(this)">Re-check now</button></p>')

    def _js(s):        # JS-String-Kontext in onclick: der Browser dekodiert HTML-
        # Entities VOR dem JS-Parsen, html.escape allein reicht dort nicht
        return html.escape(s.replace("\\", "\\\\").replace("'", "\\'"), quote=True)
    if ansicht == "verwechslung":
        karten = []
        for p in paare:
            rand = "#c0392b" if p.get("kritisch") else "#556"
            fl = ' · <b style="color:var(--warn)">suspected mislabel</b>' if p.get("fehllabel_verdacht") else ""
            def _fig(person, datei):
                src = f'/refs/{urllib.parse.quote(person)}/{urllib.parse.quote(datei)}'
                return (f'<figure style="margin:0;text-align:center">'
                        f'<img src="{src}" style="height:120px;border-radius:5px">'
                        f'<figcaption>{html.escape(person)}</figcaption></figure>')
            aa, da = _js(p["a_person"]), _js(p["a_datei"])
            ab, db = _js(p["b_person"]), _js(p["b_datei"])
            karten.append(
                f'<div class="card" style="border-left:5px solid {rand}">'
                f'<b>Similarity {p["sim"]:.2f}</b> between two different persons '
                f'(own coherence {p.get("eigen_koh") if p.get("eigen_koh") is not None else "—"}){fl}'
                f'<div class="crops" style="align-items:center;gap:12px">'
                f'{_fig(p["a_person"], p["a_datei"])}<span style="font-size:22px">↔</span>'
                f'{_fig(p["b_person"], p["b_datei"])}</div>'
                f'<div><button class="gtb" onclick="refEntfernen(\'{aa}\',\'{da}\',this)">'
                f'Remove {html.escape(p["a_person"])} image</button> '
                f'<button class="gtb" onclick="refEntfernen(\'{ab}\',\'{db}\',this)">'
                f'Remove {html.escape(p["b_person"])} image</button></div></div>')
        hinweis = ("<p>Reference images of different persons that resemble each other too strongly. A high "
                   "value plus a suspected mislabel = possibly assigned wrong, then remove. "
                   "Otherwise a genuine resemblance (e.g. siblings). Red-outlined = critical. "
                   f"<b>{len(krit)} critical</b>.</p>")
        if not qs:
            koerper = webui.leer("No check computed yet.", "Click Re-check now above.")
        elif paare:
            koerper = hinweis + "".join(karten)
        else:
            koerper = hinweis + webui.leer("No confusion pairs above the threshold.")
    else:
        GRUPPEN = [
            ("defekt", "Corrupt files", "Not readable — delete."),
            ("kein_gesicht", "No detectable face",
             "buffalo_l finds no face — worthless as a reference (pure noise), "
             "deletion recommended."),
            ("zu_klein", f"Face too small (below {qs.get('min_kante', '?')} px)",
             "Too little image information — weak, error-prone reference."),
            ("unscharf", f"Blurry (sharpness below {qs.get('unscharf_max', '?')})",
             "Noisy embedding — can produce false matches."),
        ]
        bloecke = []
        for gkey, titel, erkl in GRUPPEN:
            items = [u for u in ug if u.get("hauptgrund") == gkey]
            if not items:
                continue
            kacheln = []
            for u in items:
                val = html.escape(u["person"] + "|" + u["datei"], quote=True)
                gr = ", ".join(u.get("gruende", []))
                info = (f'{html.escape(u["person"])} · '
                        f'{u.get("kante") if u.get("kante") is not None else "—"} px · '
                        f'sharpness {u["sharp"]:.0f}')
                bild = ("" if gkey == "defekt" else
                        f'<img src="/refs/{urllib.parse.quote(u["person"])}/'
                        f'{urllib.parse.quote(u["datei"])}" '
                        f'style="height:104px;border-radius:5px;display:block;margin-bottom:3px">')
                kacheln.append(
                    f'<label style="display:inline-block;text-align:center;margin:5px;'
                    f'vertical-align:top" title="{html.escape(gr)}">{bild}'
                    f'<input type="checkbox" class="us-cb g-{gkey}" value="{val}"> {info}</label>')
            bloecke.append(
                f'<h3>{titel} ({len(items)})</h3><p>{erkl} '
                f'<button class="gtb" onclick="usAlle(\'g-{gkey}\')">select all</button></p>'
                + "".join(kacheln))
        if not qs or "ungeeignet" not in qs:   # leer ODER Alt-Format vor dem ersten Neulauf
            koerper = webui.leer("No check computed yet.", "Click Re-check now above.")
        elif bloecke:
            koerper = ("<p>Reference images suggested for deletion, grouped by reason. "
                       "For persons with few images, don't delete everything blindly — "
                       "look first.</p>" + "".join(bloecke)
                       + '<div style="margin-top:14px"><button class="gtb on" '
                       'onclick="refBatchLoeschen(this)">Delete selected</button></div>')
        else:
            koerper = webui.leer("All reference images pass the suitability check.")
    return kopf + koerper
