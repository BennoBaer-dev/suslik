"""Anker-Ansicht (E3, read-only): die Cluster eines Lernlaufs MIT Gesichts-Crops —
der erste Blick auf das Ergebnis („durch die Cluster blättern"), VOR der
Benennungs-Phase. Reine Renderer-Funktion; Daten (anker_lesen) und Bild-Route
(/lernlauf/crop/... mit Containment) liefert verifyd.

Zeigt je Cluster die det-besten Crops (deterministisch sortiert), Eimer-Status
sichtbar aber NIE versteckt (zur Ansicht/hart = gedimmt + Grund) — Leitprinzip 3:
nichts verschwindet still, auch Mehrdeutiges bleibt sichtbar."""
import html

CROPS_JE_CLUSTER = 12      # Anzeige-Deckel je Karte (74 Cluster x 12 = tragbare Seite)


def _badge(txt, dim=False):
    return f'<span class="pill{" dim" if dim else ""}">{html.escape(str(txt))}</span>'


def _thumb(m, lauf_id, dim):
    """Crop-Kachel; .83: KLICKBAR — oeffnet den Clip des Events, in dem das
    Gesicht steckt ('Gesicht in Gross UND Video'). Das Roh-Bild haengt am img selbst."""
    name = html.escape(str(m.get("datei", "")).rsplit("/", 1)[-1])
    ev = html.escape(str(m.get("event", "")))
    return (f'<a href="/video/{ev}" title="{html.escape(m.get("kamera", "?"))} · '
            f'det {m.get("det")} · click opens the clip">'
            f'<img src="/lernlauf/crop/{html.escape(lauf_id)}/{name}" loading="lazy" '
            f'class="anker-thumb{" gedimmt" if dim else ""}"></a>')


def _thumb_w(m, lauf_id, dim, checked, grund=None):
    """E4a: Crop-Kachel MIT Auswahl-Checkbox (Label umschliesst Bild + Haken; der
    Clip-Link wandert auf ein kleines ▶, damit Klick aufs Bild = an-/abwaehlen)."""
    name = html.escape(str(m.get("datei", "")).rsplit("/", 1)[-1])
    ev = html.escape(str(m.get("event", "")))
    titel = html.escape(grund or f'{m.get("kamera", "?")} · det {m.get("det")}')
    return (f'<label class="anker-w{" gedimmt" if dim else ""}" title="{titel}">'
            f'<input type="checkbox" name="sel" value="{name}"{" checked" if checked else ""}>'
            f'<img src="/lernlauf/crop/{html.escape(lauf_id)}/{name}" loading="lazy" '
            f'class="anker-thumb">'
            f'<a class="anker-clip" href="/video/{ev}" title="open the clip">&#9654;</a>'
            + (f'<span class="anker-grund">{html.escape(grund)}</span>' if grund else "")
            + '</label>')


BIN_TITEL = {"frontal": "Frontal", "links": "Looking left", "rechts": "Looking right"}


def anker_detail_seite(s, kaputt=0, benennung=None):
    """.83: Detail-Ansicht EINES Clusters — alle Crops, klickbar zum Clip.
    E4a (Zug 2b): mit benennung={bewertet, flags, personen, vorschlag} wird die
    Seite zum Benennungs-Fluss (Bauplan §E4a-UI-Fluss v2): Empfohlen je
    Perspektive vorausgewaehlt, Nicht-empfohlen gedimmt MIT Grund (nichts
    verschwindet), Sammel-Schalter, Ziel neu/bestehend. Der POST laeuft gegen
    /lernlauf/benennen; Kollisions-Rueckfrage macht der Server (kollision-Feld)."""
    q = s.get("qualitaet") or {}
    lauf_id = (s.get("lauf") or {}).get("lauf_id", "")
    aid = html.escape(str(s.get("anker_id")))
    dim = q.get("eimer", "ok") not in ("ok",)
    mitglieder = sorted(s.get("mitglieder") or [],
                        key=lambda m: (-(m.get("det") or 0), str(m.get("datei"))))
    tage = q.get("tage_liste") or []
    spanne = f'{tage[0]} … {tage[-1]}' if len(tage) > 1 else (tage[0] if tage else "—")
    stil = ('<style>.anker-reihe{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}'
            '.anker-thumb{width:96px;height:96px;object-fit:cover;border-radius:4px}'
            '.anker-thumb.gedimmt,.anker-w.gedimmt img{opacity:.45}'
            '.anker-w{position:relative;display:inline-block;cursor:pointer}'
            '.anker-w input{position:absolute;top:4px;left:4px;z-index:2}'
            '.anker-w input:not(:checked)+img{outline:none;opacity:.55}'
            '.anker-w input:checked+img{outline:2px solid var(--accent)}'
            '.anker-clip{position:absolute;right:4px;bottom:4px;font-size:11px;'
            'background:var(--surface);border-radius:4px;padding:0 4px;text-decoration:none}'
            '.anker-grund{display:block;max-width:96px;font-size:10px;color:var(--dim);'
            'line-height:1.2;padding-top:2px}'
            '.pill{display:inline-block;border:1px solid var(--rand,#8884);'
            'border-radius:10px;padding:0 8px;margin:0 4px 2px 0;font-size:.85em}'
            '.pill.dim{opacity:.6}'
            '.bn-leiste{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px}'
            '.bn-leiste input[type=text]{padding:4px 8px;min-width:180px}</style>')
    kopf = (f'<h2>{aid}</h2>'
            f'<div class="card">{_badge(q.get("eimer", "ok"), dim=dim)}'
            + _badge(f'{q.get("stuetz", 0)} faces ({q.get("stuetz_phys", "?")} physical)')
            + _badge(f'{q.get("durchgaenge", 0)} passes')
            + _badge(f'{q.get("tage", 0)} day(s): {spanne}')
            + _badge(f'margin {q.get("marge")}'))
    if not benennung:
        thumbs = "".join(_thumb(m, lauf_id, dim) for m in mitglieder)
        return (stil + kopf
                + '<div class="dim">click a face to open its clip · '
                  '<a href="/lernlauf/anker">back to all clusters</a></div>'
                + f'<div class="anker-reihe">{thumbs}</div></div>')
    # ---- Benennungs-Modus (E4a Zug 2b) ------------------------------------
    bew = {b["datei"]: b for b in benennung.get("bewertet") or []}
    flags = benennung.get("flags") or {}
    schon = s.get("status") == "benannt"
    uebernommen = s.get("status") == "uebernommen"
    if uebernommen:
        # E4b: uebernommene Anker sind abgeschlossen — Bilder bleiben sichtbar,
        # aber keine Auswahl/Umbenennung mehr (Referenz-Hygiene laeuft ueber die
        # Quality-Werkzeuge, nicht rueckwaerts durch den Lernlauf).
        thumbs = "".join(_thumb(m, lauf_id, False) for m in mitglieder)
        return (stil + kopf
                + f'<div class="pill">adopted as <b>{html.escape(str(s.get("person")))}</b>'
                  ' — these faces feed recognition now</div>'
                + '<div class="dim"><a href="/lernlauf/anker">back to all clusters</a> · '
                  'reference upkeep lives on the Quality page</div>'
                + f'<div class="anker-reihe">{thumbs}</div></div>')
    hinweis = ""
    if schon:
        hinweis = (f'<div class="pill">named <b>{html.escape(str(s.get("person")))}</b>'
                   ' — adoption pending (naming can still be changed)</div>')
    if flags.get("emb_fehlt"):
        hinweis += ('<div class="pill dim">duplicate check unavailable '
                    '(anchor predates embedding persistence) — physical duplicates '
                    'are still filtered</div>')
    v = benennung.get("vorschlag")
    if v:
        hinweis += (f'<div class="pill">looks like <b>{html.escape(v["name"])}</b> '
                    f'(similarity {v["sim"]}) — suggestion only</div>')
    # gewaehlt-Vorbelegung: persistierte Auswahl (Reload) schlaegt die Empfehlung.
    hat_persist = any("gewaehlt" in m for m in mitglieder)
    sektionen = []
    empf = [m for m in mitglieder
            if bew.get(str(m.get("datei", "")), {}).get("empfohlen")]
    nicht = [m for m in mitglieder if m not in empf]
    for bin_key in ("frontal", "links", "rechts"):
        ms = [m for m in empf if bew.get(str(m.get("datei", "")), {}).get("bin") == bin_key]
        if not ms:
            continue          # leerer Bin = Normalzustand (Bauplan), keine leere Sektion
        kacheln = "".join(_thumb_w(
            m, lauf_id, False,
            checked=(m.get("gewaehlt", False) if hat_persist else True)) for m in ms)
        sektionen.append(f'<h3>Recommended — {BIN_TITEL[bin_key]} ({len(ms)})</h3>'
                         f'<div class="anker-reihe">{kacheln}</div>')
    if nicht:
        kacheln = "".join(_thumb_w(
            m, lauf_id, True,
            checked=bool(m.get("gewaehlt", False)) if hat_persist else False,
            grund=bew.get(str(m.get("datei", "")), {}).get("grund") or "not rated")
            for m in nicht)
        sektionen.append(f'<h3>Not recommended ({len(nicht)}) — kept visible, '
                         'reason on each image</h3>'
                         f'<div class="anker-reihe">{kacheln}</div>')
    personen = benennung.get("personen") or []
    opts = "".join(f'<option value="{html.escape(p)}">' for p in personen)
    leiste = (
        '<div class="bn-leiste">'
        '<button type="button" id="bn-alle">Select all recommended</button>'
        '<button type="button" id="bn-keine">Deselect all</button>'
        '<span class="dim">·</span>'
        f'<input type="text" id="bn-name" list="bn-personen" '
        f'placeholder="person name (new or existing)" '
        f'value="{html.escape(str(s.get("person") or ""))}">'
        f'<datalist id="bn-personen">{opts}</datalist>'
        f'<button type="button" id="bn-save" data-aid="{aid}">Name this cluster</button>'
        + (f'<button type="button" id="bn-adopt" data-aid="{aid}" class="gtb on">'
           'Adopt into recognition</button>' if schon else "")
        + '<span id="bn-status" class="dim"></span></div>')
    js = ('<script>(function(){'
          'var alle=document.getElementById("bn-alle"),keine=document.getElementById("bn-keine");'
          'function boxen(){return document.querySelectorAll(".anker-w input[name=sel]")}'
          'alle.onclick=function(){boxen().forEach(function(b){'
          'b.checked=!b.closest(".anker-w").classList.contains("gedimmt");});};'
          'keine.onclick=function(){boxen().forEach(function(b){b.checked=false;});};'
          'var save=document.getElementById("bn-save"),st=document.getElementById("bn-status");'
          'function senden(name,bestaetigt){'
          'var sel=[];boxen().forEach(function(b){if(b.checked)sel.push(b.value);});'
          'st.textContent="saving\\u2026";'
          'fetch("/lernlauf/benennen",{method:"POST",headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({anker_id:save.dataset.aid,person:name,gewaehlt:sel,'
          'bestaetigt:!!bestaetigt})}).then(function(r){return r.json()})'
          '.then(function(d){if(d.kollision){'
          'if(confirm("\\u2019"+name+"\\u2019 matches existing \\u2019"+d.kollision+'
          '"\\u2019 \\u2014 add to that person instead?"))senden(d.kollision,true);'
          'else st.textContent="not saved";return;}'
          'st.textContent=d.ok?d.msg:("error: "+d.msg);'
          'if(d.ok)setTimeout(function(){location.reload()},600);})'
          '.catch(function(e){st.textContent="error: "+e;});}'
          'save.onclick=function(){senden(document.getElementById("bn-name").value,false);};'
          'var ad=document.getElementById("bn-adopt");'
          'if(ad)ad.onclick=function(){var best=false;'
          'function los(){st.textContent="adopting\\u2026";'
          'fetch("/lernlauf/uebernehmen",{method:"POST",headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({anker_id:ad.dataset.aid,bestaetigt:best})})'
          '.then(function(r){return r.json()}).then(function(d){'
          'if(d.tag_abweichung){if(confirm("Settings changed since naming:\\n"+'
          'd.tag_abweichung.join("\\n")+"\\nAdopt anyway with the named selection?"))'
          '{best=true;los();}else st.textContent="not adopted";return;}'
          'st.textContent=d.ok?d.msg:("error: "+d.msg);'
          'if(d.ok)setTimeout(function(){location.reload()},1200);})'
          '.catch(function(e){st.textContent="error: "+e;});}los();};'
          '})();</script>')
    return (stil + kopf + hinweis
            + '<div class="dim">click an image to select or deselect it · the little '
              '&#9654; opens the clip · <a href="/lernlauf/anker">back to all clusters</a></div>'
            + "".join(sektionen) + leiste + '</div>' + js)


def anker_seite(saetze, kaputt):
    """Anker-Datensaetze (anker_lesen-Reihenfolge) -> Seiten-HTML. saetze duerfen aus
    mehreren Laeufen stammen (Bild-URLs tragen die lauf_id je Satz)."""
    if not saetze:
        return ("<h2>Anchor clusters</h2>"
                '<div class="card">No anchors yet — a learning run builds them '
                '(Preparation → Harvest → Grouping). '
                '<a href="/lernlauf">Open the learning run page</a>.</div>')
    ok_n = sum(1 for s in saetze if (s.get("qualitaet") or {}).get("eimer") == "ok")
    ges = sum((s.get("qualitaet") or {}).get("stuetz", 0) for s in saetze)
    kopf_warn = (f'<div class="card"><b>{kaputt} unreadable anchor lines counted</b> '
                 "— they are never dropped silently.</div>" if kaputt else "")
    karten = []
    for s in sorted(saetze, key=lambda x: (-(x.get("qualitaet") or {}).get("stuetz", 0),
                                           str(x.get("anker_id")))):
        q = s.get("qualitaet") or {}
        lauf_id = (s.get("lauf") or {}).get("lauf_id", "")
        eimer = q.get("eimer", "ok")
        dim = eimer != "ok"
        mitglieder = s.get("mitglieder") or []
        beste = sorted(mitglieder, key=lambda m: (-(m.get("det") or 0), str(m.get("datei"))))
        thumbs = [_thumb(m, lauf_id, dim) for m in beste[:CROPS_JE_CLUSTER]]
        rest = len(mitglieder) - len(beste[:CROPS_JE_CLUSTER])
        # .83: '+N more faces' oeffnet die Cluster-Detail-Seite mit ALLEN Crops.
        aid = html.escape(str(s.get("anker_id")))
        mehr = (f'<a class="pill" href="/lernlauf/anker?a={aid}">+{rest} more faces</a>'
                if rest > 0 else "")
        tage = q.get("tage_liste") or []
        spanne = f'{tage[0]} … {tage[-1]}' if len(tage) > 1 else (tage[0] if tage else "—")
        kams = sorted({m.get("kamera", "?") for m in mitglieder})
        status_html = (_badge("clean") if not dim else
                       _badge(f'{eimer}: {q.get("eimer_grund", "")}', dim=True))
        # E4a (User-Vorgabe 01.08.): der Klick-Weg zum Benennen muss auf der Karte SICHTBAR
        # sein — ein Knopf je Cluster, unter den Gesichtern. Benannte tragen den
        # Namen als Badge und der Knopf wechselt auf "Review naming".
        st_a = s.get("status")
        benannt_pill = (f'<span class="pill">named: <b>{html.escape(str(s.get("person")))}</b>'
                        ' — adoption pending</span>' if st_a == "benannt" else
                        (f'<span class="pill">adopted: <b>{html.escape(str(s.get("person")))}</b></span>'
                         if st_a == "uebernommen" else ""))
        knopf_txt = ("Review naming" if st_a == "benannt" else
                     ("View cluster" if st_a == "uebernommen" else
                      f'Name these {q.get("stuetz", 0)} faces'))
        knopf = (f'<div style="margin-top:6px"><a class="gtb on" href="/lernlauf/anker?a={aid}">'
                 f"{knopf_txt}</a></div>")
        karten.append(
            f'<div class="card"><b>{html.escape(str(s.get("anker_id")))}</b> {status_html} '
            + benannt_pill
            + _badge(f'{q.get("stuetz", 0)} faces') + _badge(f'{q.get("durchgaenge", 0)} passes')
            + _badge(f'{q.get("tage", 0)} day(s): {spanne}')
            + _badge(", ".join(kams)) + _badge(f'margin {q.get("marge")}')
            + f'<div class="anker-reihe">{"".join(thumbs)}{mehr}</div>{knopf}</div>')
    stil = ('<style>.anker-reihe{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}'
            '.anker-thumb{width:72px;height:72px;object-fit:cover;border-radius:4px}'
            '.anker-thumb.gedimmt{opacity:.45}'
            '.pill{display:inline-block;border:1px solid var(--rand,#8884);'
            'border-radius:10px;padding:0 8px;margin:0 4px 2px 0;font-size:.85em}'
            '.pill.dim{opacity:.6}</style>')
    return (stil + "<h2>Anchor clusters</h2>"
            f'<div class="card">{len(saetze)} clusters from {ges} anchor-ready faces — '
            f'{ok_n} clean, {len(saetze) - ok_n} for review (dimmed, with the reason on the '
            'badge). Open a cluster to review and name it; adoption into recognition ships with E4b. '
            '<a href="/lernlauf">Back to the learning run</a>.</div>'
            + kopf_warn + "".join(karten))
