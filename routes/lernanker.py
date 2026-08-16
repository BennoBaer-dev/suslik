"""Anker-Ansicht (E3, read-only): die Cluster eines Lernlaufs MIT Gesichts-Crops —
der erste Blick auf das Ergebnis („durch die Cluster blättern"), VOR der
Benennungs-Phase. Reine Renderer-Funktion; Daten (anker_lesen) und Bild-Route
(/lernlauf/crop/... mit Containment) liefert verifyd.

Zeigt je Cluster die det-besten Crops (deterministisch sortiert), Eimer-Status
sichtbar aber NIE versteckt (zur Ansicht/hart = gedimmt + Grund) — Leitprinzip 3:
nichts verschwindet still, auch Mehrdeutiges bleibt sichtbar."""
import html

CROPS_JE_CLUSTER = 12      # Anzeige-Deckel je Karte (74 Cluster x 12 = tragbare Seite)


# .224 (User-Fund am Screenshot): interne Eimer-Marken erschienen ROH in der
# englischen UI ("UNBESTAETIGT: ..."). Anzeige-Map, Tokens bleiben unberuehrt.
EIMER_TEXT = {"ok": "clean", "unbestaetigt": "unconfirmed",
              "zu_duenn": "thin", "hart": "mixed"}


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


def anker_detail_seite(s, kaputt=0, benennung=None, fluss=None):
    """.83: Detail-Ansicht EINES Clusters — alle Crops, klickbar zum Clip.
    E4a (Zug 2b): mit benennung={bewertet, flags, personen, vorschlag} wird die
    Seite zum Benennungs-Fluss (Bauplan §E4a-UI-Fluss v2): Empfohlen je
    Perspektive vorausgewaehlt, Nicht-empfohlen gedimmt MIT Grund (nichts
    verschwindet), Sammel-Schalter, Ziel neu/bestehend. Der POST laeuft gegen
    /lernlauf/benennen; Kollisions-Rueckfrage macht der Server (kollision-Feld).

    .224 (User: 'kein Fluss, der an die Hand nimmt'): fluss={pos, gesamt,
    naechster} macht die Easy-Sicht zur BENENNUNGS-KARTE — 'Group 2 of 7',
    EINE Frage (Who is this?), vorbereitete Antwort aus dem looks-like-
    Vorschlag, ein Klick benennt UND uebernimmt und springt zur naechsten
    Gruppe. Expert behaelt die volle Auswahl-Ansicht (nur-expert)."""
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
    # .224: Cluster-ID und Kenn-Badges sind Expert-Tiefe; die Easy-Karte traegt
    # ihren eigenen Kopf (Group x of y + die eine Frage).
    fluss = fluss or {}
    e_kopf = ""
    if fluss.get("pos"):
        _frage = (benennung is not None
                  and s.get("status") not in ("uebernommen", "verworfen"))
        e_kopf = ('<div class="nur-easy" style="margin:2px 0 6px">'
                  f'<div class="dim">Group {fluss["pos"]} of '
                  f'{fluss["gesamt"]}</div>'
                  + ('<h2 style="margin:2px 0">Who is this?</h2>'
                     if _frage else "") + "</div>")
    kopf = (e_kopf + f'<h2 class="nur-expert">{aid}</h2>'
            '<div class="card"><div class="nur-expert">'
            + _badge(EIMER_TEXT.get(q.get("eimer", "ok"),
                                    q.get("eimer", "ok")), dim=dim)
            + _badge(f'{q.get("stuetz", 0)} faces ({q.get("stuetz_phys", "?")} physical)')
            + _badge(f'{q.get("durchgaenge", 0)} passes')
            + _badge(f'{q.get("tage", 0)} day(s): {spanne}')
            + _badge(f'margin {q.get("marge")}') + "</div>")
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
    # .224: in abgeschlossenen Zustaenden fuehrt Easy zur naechsten Gruppe
    # weiter, statt den Nutzer in einer Sackgasse stehenzulassen.
    e_weiter = ""
    if fluss.get("naechster"):
        e_weiter = ('<p class="nur-easy"><a class="gtb on" '
                    f'href="/lernlauf/anker?a='
                    f'{html.escape(str(fluss["naechster"]))}">'
                    "Next group &#8230;</a></p>")
    if uebernommen:
        # E4b: uebernommene Anker sind abgeschlossen — Bilder bleiben sichtbar,
        # aber keine Auswahl/Umbenennung mehr (Referenz-Hygiene laeuft ueber die
        # Quality-Werkzeuge, nicht rueckwaerts durch den Lernlauf).
        thumbs = "".join(_thumb(m, lauf_id, False) for m in mitglieder)
        return (stil + kopf
                + f'<div class="pill">adopted as <b>{html.escape(str(s.get("person")))}</b>'
                  ' — these faces feed recognition now</div>' + e_weiter
                + '<div class="dim nur-expert"><a href="/lernlauf/anker">back to all clusters</a> · '
                  'reference upkeep lives on the Quality page</div>'
                + f'<div class="anker-reihe">{thumbs}</div></div>')
    if s.get("status") == "verworfen":
        # Dismiss mit Gedaechtnis: Crops sind geloescht, die Zeile traegt nur
        # noch das Erbschafts-Gedaechtnis — Direktaufruf ehrlich beantworten.
        return (stil + kopf
                + '<div class="pill">dismissed — images removed; the cluster is '
                  'remembered so re-harvests of the same events stay quiet</div>'
                + e_weiter
                + '<div class="dim nur-expert"><a href="/lernlauf/anker">back to all clusters</a></div>'
                + '</div>')
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
        _bek = ("already in your system" if {"referenz", "master"}
                & set(v.get("quellen") or []) else "named on another cluster")
        hinweis += (f'<div class="pill">looks like <b>{html.escape(v["name"])}</b> '
                    f'(similarity {v["sim"]}) — {_bek}; suggestion only</div>')
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
        # .224: die Nicht-empfohlen-Sektion ist Expert-Tiefe — Easy urteilt
        # ueber die empfohlene Auswahl (dieselben Checkboxen, gleiche Wirkung).
        sektionen.append('<div class="nur-expert">'
                         f'<h3>Not recommended ({len(nicht)}) — kept visible, '
                         'reason on each image</h3>'
                         f'<div class="anker-reihe">{kacheln}</div></div>')
    personen = benennung.get("personen") or []
    opts = "".join(f'<option value="{html.escape(p)}">' for p in personen)
    # .224: die Easy-Antwortzeile — vorbereitete Antwort aus dem Vorschlag,
    # ein Klick benennt UND uebernimmt (JS-Kette) und springt weiter. Ohne
    # Vorschlag fragt sie direkt nach dem Namen (dieselbe Eingabe wie Expert).
    naechster = fluss.get("naechster")
    weiter_url = (f'/lernlauf/anker?a={html.escape(str(naechster))}'
                  if naechster else "/lernlauf/anker")
    skip_text = ("Skip this group" if naechster else
                 "Skip — back to the groups")
    e_leiste = (
        '<div class="bn-leiste nur-easy">'
        + (f'<button type="button" id="bn-easy-ja" class="gtb on" '
           f'data-name="{html.escape(v["name"])}">'
           f'Yes, it&rsquo;s {html.escape(v["name"])}</button>'
           '<button type="button" id="bn-easy-andere">Someone else &#8230;'
           '</button>' if v else
           '<button type="button" id="bn-easy-andere" class="gtb on">'
           'Name this group &#8230;</button>')
        + f'<a class="gtb" href="{weiter_url}">{html.escape(skip_text)}</a>'
        + '<span id="bn-easy-status" class="dim"></span></div>')
    leiste = (
        '<div class="bn-leiste nur-expert" id="bn-expertleiste">'
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
    nx_js = (f'"{html.escape(str(naechster))}"' if naechster else "null")
    js = ('<script>(function(){'
          'var alle=document.getElementById("bn-alle"),keine=document.getElementById("bn-keine");'
          'function boxen(){return document.querySelectorAll(".anker-w input[name=sel]")}'
          'alle.onclick=function(){boxen().forEach(function(b){'
          'b.checked=!b.closest(".anker-w").classList.contains("gedimmt");});};'
          'keine.onclick=function(){boxen().forEach(function(b){b.checked=false;});};'
          'var save=document.getElementById("bn-save"),st=document.getElementById("bn-status");'
          'var est=document.getElementById("bn-easy-status");'
          f'var CHAIN=false,NX={nx_js};'
          'function melden(t){st.textContent=t;if(est)est.textContent=t;}'
          # .224: Uebernahme als eigene Funktion — Expert-Knopf UND Easy-Kette
          # nutzen denselben Weg; danach traegt die Kette zur naechsten Gruppe.
          'function adoptieren(best){melden("adopting\\u2026");'
          'fetch("/lernlauf/uebernehmen",{method:"POST",headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({anker_id:save.dataset.aid,bestaetigt:best})})'
          '.then(function(r){return r.json()}).then(function(d){'
          'if(d.tag_abweichung){if(confirm("Settings changed since naming:\\n"+'
          'd.tag_abweichung.join("\\n")+"\\nAdopt anyway with the named selection?"))'
          '{adoptieren(true);}else melden("not adopted");return;}'
          'if(!d.ok){melden("error: "+d.msg);return;}'
          'if(CHAIN){if(NX){melden("saved \\u2014 next group\\u2026");'
          'setTimeout(function(){location="/lernlauf/anker?a="+encodeURIComponent(NX)},500);}'
          'else{melden("All groups done \\u2014 the named pictures now count for recognition.");'
          'setTimeout(function(){location="/lernlauf/anker"},1600);}return;}'
          'melden(d.msg);setTimeout(function(){location.reload()},1200);})'
          '.catch(function(e){melden("error: "+e);});}'
          'function senden(name,bestaetigt){'
          'var sel=[];boxen().forEach(function(b){if(b.checked)sel.push(b.value);});'
          'melden("saving\\u2026");'
          'fetch("/lernlauf/benennen",{method:"POST",headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({anker_id:save.dataset.aid,person:name,gewaehlt:sel,'
          'bestaetigt:!!bestaetigt})}).then(function(r){return r.json()})'
          '.then(function(d){if(d.kollision){'
          'if(confirm("\\u2019"+name+"\\u2019 matches existing \\u2019"+d.kollision+'
          '"\\u2019 \\u2014 add to that person instead?"))senden(d.kollision,true);'
          'else melden("not saved");return;}'
          'if(!d.ok){melden("error: "+d.msg);return;}'
          'if(CHAIN){adoptieren(false);return;}'
          'melden(d.msg);setTimeout(function(){location.reload()},600);})'
          '.catch(function(e){melden("error: "+e);});}'
          'save.onclick=function(){senden(document.getElementById("bn-name").value,false);};'
          'var ad=document.getElementById("bn-adopt");'
          'if(ad)ad.onclick=function(){CHAIN=false;adoptieren(false);};'
          'var ja=document.getElementById("bn-easy-ja");'
          'if(ja)ja.onclick=function(){CHAIN=true;senden(ja.dataset.name,false);};'
          'var an=document.getElementById("bn-easy-andere");'
          'if(an)an.onclick=function(){CHAIN=true;'
          'var l=document.getElementById("bn-expertleiste");'
          'l.classList.remove("nur-expert");'
          'document.getElementById("bn-name").focus();};'
          '})();</script>')
    return (stil + kopf + hinweis
            + '<div class="dim nur-expert">click an image to select or deselect it · the little '
              '&#9654; opens the clip · <a href="/lernlauf/anker">back to all clusters</a></div>'
            + "".join(sektionen) + e_leiste + leiste + '</div>' + js)


def anker_seite(saetze, kaputt, vorschlaege=None, dubletten=None):
    """Anker-Datensaetze (anker_lesen-Reihenfolge) -> Seiten-HTML. saetze duerfen aus
    mehreren Laeufen stammen (Bild-URLs tragen die lauf_id je Satz).
    vorschlaege: anker_id -> Personen-Name (looks-like-Badge auf der Karte —
    dieselbe Empfehlung, die die Detail-Seite rechnet; User 05.08.).
    dubletten: anker_id -> anker_id des NEUEREN gleichen Clusters (Lauf-
    uebergreifende Wiederernte unbenannter Leute; alter wird gedimmt)."""
    vorschlaege = vorschlaege or {}
    dubletten = dubletten or {}
    # Lauf-Loeschen (User 05.08., 2. Fassung 'ganz loeschen, kein Papierkorb'):
    # die Ernte aendert sich in der Entwicklung, ein neuer Lauf ersetzt den
    # alten mitsamt Daten — ein Knopf je Lauf loescht ALLE seine Cluster
    # (auch benannte und verworfene) und den Lauf-Ordner endgueltig. Bereits
    # uebernommene Referenzen bleiben (Kopien in faces/); der Dialog sagt das.
    # Zaehlung auf ALLEN Zeilen VOR dem Verworfen-Anzeigefilter (Review .125:
    # sonst luegt die Dialog-Zahl und ein Nur-Verworfene-Lauf haette keinen Knopf).
    laeufe = {}
    for s in saetze:
        lid = str((s.get("lauf") or {}).get("lauf_id") or "")
        if lid:
            laeufe[lid] = laeufe.get(lid, 0) + 1
    lauf_zeile = ""
    if laeufe:
        knoepfe = "".join(
            f'<button class="gtb" onclick="laufLoeschen(\'{html.escape(lid)}\',this)" '
            f'data-frage="Delete run {html.escape(lid)} and all its data? This '
            f'permanently removes its {n} cluster(s) — including named and '
            'dismissed ones — and all harvested images. References already '
            'adopted into recognition stay. This cannot be undone.">'
            f'{html.escape(lid)} ({n})</button> '
            for lid, n in sorted(laeufe.items()))
        # Sammel-Knopf (User 05.08.): alle ALTEN Laeufe mit EINEM OK weg, der
        # neueste bleibt immer stehen (einen laufenden ueberspringt der Kern).
        alle_knopf = ""
        if len(laeufe) > 1:
            neuester = sorted(laeufe)[-1]
            alt_n = sum(n for lid, n in laeufe.items() if lid != neuester)
            alle_knopf = (
                f'<button class="gtb" onclick="alteLaeufeLoeschen(this)" '
                f'data-frage="Delete ALL {len(laeufe) - 1} old run(s) with their '
                f'{alt_n} cluster(s) and all harvested images? Only the newest '
                f'run {html.escape(neuester)} is kept. References already '
                'adopted into recognition stay. This cannot be undone.">'
                f'Delete all old runs (keep {html.escape(neuester)})</button>')
        lauf_zeile = ('<div class="card">Delete a run — permanently removes all '
                      'its clusters and harvested images (references you already '
                      f'adopted stay): {knoepfe}{alle_knopf}</div>')
    # Dismiss mit Gedaechtnis (User 05.08.): verworfene Cluster verschwinden aus
    # der Liste, ihre Zeilen bleiben als Erbschafts-Gedaechtnis — GEZAEHLT
    # ausgewiesen, nie still (Leitprinzip 3).
    verworfen_n = sum(1 for s in saetze if s.get("status") == "verworfen")
    saetze = [s for s in saetze if s.get("status") != "verworfen"]
    verworfen_hinweis = (
        f'<div class="dim">{verworfen_n} dismissed cluster(s) remembered — '
        're-harvests of the same events stay quiet</div>' if verworfen_n else "")
    if not saetze:
        return ("<h2>Anchor clusters</h2>" + verworfen_hinweis + lauf_zeile
                + '<div class="card">No anchors yet — a learning run builds them '
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
        dup_von = dubletten.get(s.get("anker_id"))
        dim = eimer != "ok" or bool(dup_von)
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
                       _badge(f'{EIMER_TEXT.get(eimer, eimer)}: '
                              f'{q.get("eimer_grund", "")}', dim=True))
        if dup_von:
            status_html += _badge(f"same cluster as {dup_von} \u2014 "
                                  "harvested again by a newer run; name it there",
                                  dim=True)
        _vs = vorschlaege.get(s.get("anker_id"))
        if _vs and s.get("status") not in ("benannt", "uebernommen"):
            # "kennen wir schon"-Semantik (User 05.08.): Referenz-/Master-Treffer
            # heisst, die Person IST im System — der Lauf liefert nur neues
            # Material fuer sie. Treffer aus bloss benannten Ankern sagen das
            # ehrlich schwaecher.
            _bek = ("already in your system" if {"referenz", "master"}
                    & set(_vs.get("quellen") or []) else "named on another cluster")
            status_html += ('<span class="pill" style="border-color:var(--ok)">'
                            f'looks like <b>{html.escape(str(_vs.get("name")))}</b> '
                            f'({_vs.get("sim")}) — {_bek}; naming the cluster '
                            'adds these faces to their references</span>')
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
        # Dismiss mit Gedaechtnis (User 05.08.): nur unbenannte Cluster —
        # Zeile+Zentroid bleiben, Wiederernten derselben Events erben still.
        verwerf = ('' if st_a in ("benannt", "uebernommen") else
                   f'<button class="gtb" onclick="ankerVerwerfen(\'{aid}\',this)" '
                   'data-frage="Dismiss this cluster? Its images are removed; '
                   'the cluster is remembered so re-harvests of the same events '
                   'stay quiet.">Dismiss</button>')
        knopf = (f'<div style="margin-top:6px"><a class="gtb on" href="/lernlauf/anker?a={aid}">'
                 f"{knopf_txt}</a> {verwerf}</div>")
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
            # .200 (Fix 4): E4b ist laengst gebaut (/lernlauf/uebernehmen) —
            # der Adopt-Knopf steht im benannten Cluster.
            'badge). Open a cluster to review and name it — named clusters are adopted '
            'into recognition right there (Adopt button). '
            '<a href="/lernlauf">Back to the learning run</a>.</div>'
            + verworfen_hinweis + lauf_zeile
            + kopf_warn + "".join(karten))
