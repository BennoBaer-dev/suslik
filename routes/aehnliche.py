"""routes/aehnliche — "Matching faces": passende Unbekannte + Bestands-Vorschlaege zu
einer Person (M1a, byte-treu aus verifyd extrahiert). Kontrakt: NUR rendern — die
Seiteneffekte (Suchlaeufe qs_neu_starten/vorschlaege_starten) loest der Handler aus,
BEVOR er render() ruft; hier entscheidet nur noch kand/vs None-oder-nicht ueber die
Platzhalter + refresh (15 s Quelle 1 / 20 s Quelle 2, wie im Bestand)."""
import datetime
import html
import os
import urllib.parse

import webui


def render(person, kand, vs, data_dir):
    """-> (inhalt, refresh). kand = anlernen.aehnliche_unbekannte(person) (None = laeuft),
    vs = anlernen.lade_vorschlaege(person) (None = laeuft)."""
    pe = html.escape(person)
    pj = html.escape(person.replace("\\", "\\\\").replace("'", "\\'"), quote=True)
    refresh = None
    teile = [f"<h2>Matching faces for {pe}</h2>"
             f"<p>Two sources: unknown faces that resemble {pe}, and new "
             f"faces from events in which {pe} was already confidently recognized. "
             f"Tick and apply. <a href='/gesichter'>back</a></p>"]
    # --- Quelle 1: unbekannte Gesichter ---
    teile.append("<h3>From unknown faces</h3>")
    if kand is None:
        refresh = 15
        teile.append(webui.leer("Search running — references are being re-read.",
                                "The page refreshes by itself.")
                     .replace("</b>", '</b> <span class="such-zaehler" '
                              'data-person="' + html.escape(person, quote=True) + '"></span>', 1))
    elif not kand:
        teile.append(webui.leer("No similar unknown faces in stock."))
    else:
        for g in kand:
            gid = html.escape(g["id"], quote=True)
            teile.append(
                f'<label class="card" style="display:inline-block;width:auto;'
                f'text-align:center;margin:4px;vertical-align:top">'
                f'<img src="/anlern/crops/{urllib.parse.quote(g["id"])}.jpg" '
                f'style="height:120px;border-radius:5px;display:block;margin-bottom:4px">'
                f'<input type="checkbox" class="ae-cb" value="{gid}"> '
                f'similarity {g["sim"]:.2f}</label>')
        teile.append(f'<div style="margin:6px 0 14px"><button class="gtb on" '
                     f'onclick="aehnlicheHinzu(\'{pj}\',this)">'
                     f'Add selected to {pe}</button></div>')
    # --- Quelle 2: Bestands-Suche in erkannten Events ---
    teile.append("<h3>New faces from recognized events (7 days)</h3>")
    if vs is None:
        refresh = refresh or 20
        teile.append(webui.leer("Search running — recognized events are being scanned.",
                                "The page refreshes by itself; result in "
                                "one or two minutes.")
                     .replace("</b>", '</b> <span class="such-zaehler" '
                              'data-person="' + html.escape(person, quote=True) + '"></span>', 1))
    else:
        ev_base = os.path.join(data_dir, "events")
        ks = [k for k in vs.get("kandidaten", [])
              if os.path.isfile(os.path.join(ev_base, str(k["eid"]).replace("/", "_"),
                                             k["datei"]))]
        stand_v = datetime.datetime.fromtimestamp(vs.get("ts", 0)).strftime("%H:%M")
        if ks:
            def _vs_kachel(k, rand="", cbcls=""):
                ed = urllib.parse.quote(str(k["eid"]).replace("/", "_"))
                val = html.escape(f'{k["eid"]}|{k["datei"]}', quote=True)
                wann = datetime.datetime.fromtimestamp(k.get("ts") or 0).strftime("%d.%m. %H:%M")
                return (
                    f'<label class="card" style="display:inline-block;width:auto;'
                    f'text-align:center;margin:4px;vertical-align:top{rand}">'
                    f'<img src="/events/{ed}/{urllib.parse.quote(k["datei"])}" '
                    f'style="height:120px;border-radius:5px;display:block;margin-bottom:4px">'
                    f'<input type="checkbox" class="vs-cb {cbcls}" value="{val}"> '
                    f'{wann} · {html.escape(str(k.get("camera") or "?"))} · sim {k["sim"]:.2f}</label>')
            # Zwei sichtbare Stufen (User 21.07.): Recommended + Neutral.
            # 'Not recommended' wird gar nicht erst geschrieben. Fallback fuer
            # alte JSONs, die noch 'sicher' statt 'stufe' fuehren.
            def _stufe(k):
                return k.get("stufe") or ("empfohlen" if k.get("sicher", True) else "neutral")
            empfohlen = [k for k in ks if _stufe(k) == "empfohlen"]
            neutral = [k for k in ks if _stufe(k) == "neutral"]
            if empfohlen:
                teile.append('<h4 style="margin:12px 0 4px">Recommended</h4>')
                for k in empfohlen:
                    teile.append(_vs_kachel(k, ";outline:2px solid #2a9d5a", "vs-cb-rec"))
            if neutral:
                teile.append(
                    '<h4 style="margin:14px 0 4px">Neutral — check the image before applying</h4>'
                    '<p style="color:var(--dim);font-size:13px;margin:0 0 6px">Clearly this person, but '
                    'either the match is below the confidence threshold or the crop is smaller / '
                    'less sharp — a look decides.</p>')
                for k in neutral:
                    teile.append(_vs_kachel(k, ";outline:2px dashed #b80"))
            auto_btn = (f'<button class="gtb on" onclick="vorschlaegeAlleEmpfohlen(\'{pj}\',this)">'
                        f'Apply all recommended ({len(empfohlen)})</button> ' if empfohlen else '')
            teile.append(
                f'<div style="margin-top:10px">{auto_btn}'
                f'<button class="gtb" onclick="vorschlagAufnehmen(\'{pj}\',this)">'
                f'Apply selected to {pe}</button> '
                f'<button class="gtb" onclick="vorschlagNeu(\'{pj}\',this)">search again</button> '
                f'<small style="color:var(--faint)">as of {stand_v} · recommended = confidently {pe} '
                f'+ reference quality</small></div>')
        else:
            teile.append(webui.leer("Nothing matching found in the recognized events.",
                                    "Criteria: unambiguously this person, novel compared to "
                                    "the stock, sufficiently large and sharp.")
                         + f'<p><button class="gtb" onclick="vorschlagNeu(\'{pj}\',this)">'
                         f'search again</button></p>')
    return "".join(teile), refresh
