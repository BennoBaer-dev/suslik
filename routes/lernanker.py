"""Anker-Ansicht (E3, read-only): die Cluster eines Lernlaufs MIT Gesichts-Crops —
der erste Blick auf das Ergebnis („durch die Cluster blättern"), VOR der
Benennungs-Phase. Reine Renderer-Funktion; Daten (anker_lesen) und Bild-Route
(/lernlauf/crop/... mit Containment) liefert verifyd.

Zeigt je Cluster die det-besten Crops (deterministisch sortiert), Eimer-Status
sichtbar aber NIE versteckt (zur Ansicht/hart = gedimmt + Grund) — Leitprinzip 3:
nichts verschwindet still, auch Mehrdeutiges bleibt sichtbar.
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe (siehe
Abschnitts-Kommentar in core/texte/en.py): Pills mit <b> mitten im Satz und
die JS-Texte mit Escape-Folgen bleiben literal; EIMER_TEXT/BIN_TITEL wurden
zu Funktionen (t() zur Render-Zeit, nie beim Import)."""
import html
import json

from core.sprache import t

CROPS_JE_CLUSTER = 12      # Anzeige-Deckel je Karte (74 Cluster x 12 = tragbare Seite)


# .224 (User-Fund am Screenshot): interne Eimer-Marken erschienen ROH in der
# englischen UI ("UNBESTAETIGT: ..."). Anzeige-Map, Tokens bleiben unberuehrt.
def _eimer_text():
    return {"ok": t("lernanker.eimer.ok"),
            "unbestaetigt": t("lernanker.eimer.unbestaetigt"),
            "zu_duenn": t("lernanker.eimer.zu_duenn"),
            "hart": t("lernanker.eimer.hart")}


def _badge(txt, dim=False):
    return f'<span class="pill{" dim" if dim else ""}">{html.escape(str(txt))}</span>'


def _thumb(m, lauf_id, dim):
    """Crop-Kachel; .83: KLICKBAR — oeffnet den Clip des Events, in dem das
    Gesicht steckt ('Gesicht in Gross UND Video'). Das Roh-Bild haengt am img selbst."""
    name = html.escape(str(m.get("datei", "")).rsplit("/", 1)[-1])
    ev = html.escape(str(m.get("event", "")))
    bild = (f'<img src="/lernlauf/crop/{html.escape(lauf_id)}/{name}" loading="lazy" '
            f'class="anker-thumb{" gedimmt" if dim else ""}">')
    # .33x DATEIQUELLE: eingespeiste Clips haben KEIN Frigate-Event — ein
    # /video/-Link liefe dort ins Leere. Kein Link ist besser als einer, der
    # 404 zeigt (Bauplan analysen/12, QS-Einwand B).
    if m.get("quelle") == "datei":
        return bild
    return (f'<a href="/video/{ev}" title="'
            + t("lernanker.kachel.attr_clip",
                kamera=html.escape(m.get("kamera", "?")), det=m.get("det")) + '">'
            + bild + '</a>')


def _thumb_w(m, lauf_id, dim, checked, grund=None):
    """E4a: Crop-Kachel MIT Auswahl-Checkbox (Label umschliesst Bild + Haken; der
    Clip-Link wandert auf ein kleines ▶, damit Klick aufs Bild = an-/abwaehlen)."""
    name = html.escape(str(m.get("datei", "")).rsplit("/", 1)[-1])
    ev = html.escape(str(m.get("event", "")))
    titel = html.escape(grund or t("lernanker.kachel.attr_kurz",
                                   kamera=m.get("kamera", "?"), det=m.get("det")))
    return (f'<label class="anker-w{" gedimmt" if dim else ""}" title="{titel}">'
            f'<input type="checkbox" name="sel" value="{name}"{" checked" if checked else ""}>'
            f'<img src="/lernlauf/crop/{html.escape(lauf_id)}/{name}" loading="lazy" '
            f'class="anker-thumb">'
            + ("" if m.get("quelle") == "datei" else      # .33x: s. _thumb
               f'<a class="anker-clip" href="/video/{ev}" title="{t("lernanker.kachel.attr_klick")}">&#9654;</a>')
            + (f'<span class="anker-grund">{html.escape(grund)}</span>' if grund else "")
            + '</label>')


def _bin_titel():
    return {"frontal": t("lernanker.bin.frontal"),
            "links": t("lernanker.bin.links"),
            "rechts": t("lernanker.bin.rechts")}


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
    stil = ('<style>.anker-reihe{display:flex;flex-wrap:wrap;gap:4px;align-items:flex-start;margin-top:6px}'
            '.anker-thumb{max-width:96px;max-height:96px;border-radius:4px;display:block}'
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
                  f'<div class="dim">'
                  + t("lernanker.detail.gruppe",
                      pos=fluss["pos"], gesamt=fluss["gesamt"]) + '</div>'
                  + (f'<h2 style="margin:2px 0">{t("lernanker.detail.frage")}</h2>'
                     if _frage else "") + "</div>")
    kopf = (e_kopf + f'<h2 class="nur-expert">{aid}</h2>'
            '<div class="card"><div class="nur-expert">'
            + _badge(_eimer_text().get(q.get("eimer", "ok"),
                                       q.get("eimer", "ok")), dim=dim)
            + _badge(t("lernanker.badge.stuetz", n=q.get("stuetz", 0),
                       phys=q.get("stuetz_phys", "?")))
            + _badge(t("lernanker.badge.durchgaenge", n=q.get("durchgaenge", 0)))
            + _badge(t("lernanker.badge.tage", n=q.get("tage", 0), spanne=spanne))
            + _badge(t("lernanker.badge.marge", marge=q.get("marge"))) + "</div>")
    if not benennung:
        thumbs = "".join(_thumb(m, lauf_id, dim) for m in mitglieder)
        return (stil + kopf
                + f'<div class="dim">{t("lernanker.detail.hinweis_klick")} · '
                  f'<a href="/lernlauf/anker">{t("lernanker.link_zurueck")}</a></div>'
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
                    + t("lernanker.detail.weiter") + "</a></p>")
    if uebernommen:
        # E4b: uebernommene Anker sind abgeschlossen — Bilder bleiben sichtbar,
        # aber keine Auswahl/Umbenennung mehr (Referenz-Hygiene laeuft ueber die
        # Quality-Werkzeuge, nicht rueckwaerts durch den Lernlauf).
        # Stufe-0-Grenze: adopted-Pill traegt <b> mitten im Satz — literal.
        thumbs = "".join(_thumb(m, lauf_id, False) for m in mitglieder)
        return (stil + kopf
                + f'<div class="pill">adopted as <b>{html.escape(str(s.get("person")))}</b>'
                  ' — these faces feed recognition now</div>' + e_weiter
                + f'<div class="dim nur-expert"><a href="/lernlauf/anker">{t("lernanker.link_zurueck")}</a> · '
                + t("lernanker.detail.pflege_hinweis") + '</div>'
                + f'<div class="anker-reihe">{thumbs}</div></div>')
    if s.get("status") == "verworfen":
        # Dismiss mit Gedaechtnis: Crops sind geloescht, die Zeile traegt nur
        # noch das Erbschafts-Gedaechtnis — Direktaufruf ehrlich beantworten.
        return (stil + kopf
                + f'<div class="pill">{t("lernanker.detail.verworfen")}</div>'
                + e_weiter
                + f'<div class="dim nur-expert"><a href="/lernlauf/anker">{t("lernanker.link_zurueck")}</a></div>'
                + '</div>')
    hinweis = ""
    if schon:
        # Stufe-0-Grenze: named-Pill traegt <b> mitten im Satz — literal.
        hinweis = (f'<div class="pill">named <b>{html.escape(str(s.get("person")))}</b>'
                   ' — adoption pending (naming can still be changed)</div>')
    if flags.get("emb_fehlt"):
        hinweis += (f'<div class="pill dim">{t("lernanker.detail.dublette_hinweis")}</div>')
    v = benennung.get("vorschlag")
    if v:
        _bek = (t("lernanker.bekannt.system") if {"referenz", "master"}
                & set(v.get("quellen") or []) else t("lernanker.bekannt.anker"))
        # Stufe-0-Grenze: looks-like-Pill traegt <b> mitten im Satz — literal.
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
        sektionen.append(f'<h3>{t("lernanker.detail.empfohlen", bin=_bin_titel()[bin_key], n=len(ms))}</h3>'
                         f'<div class="anker-reihe">{kacheln}</div>')
    if nicht:
        kacheln = "".join(_thumb_w(
            m, lauf_id, True,
            checked=bool(m.get("gewaehlt", False)) if hat_persist else False,
            grund=bew.get(str(m.get("datei", "")), {}).get("grund")
            or t("lernanker.kachel.grund_fehlt"))
            for m in nicht)
        # .224: die Nicht-empfohlen-Sektion ist Expert-Tiefe — Easy urteilt
        # ueber die empfohlene Auswahl (dieselben Checkboxen, gleiche Wirkung).
        sektionen.append('<div class="nur-expert">'
                         f'<h3>{t("lernanker.detail.nicht_empfohlen", n=len(nicht))}</h3>'
                         f'<div class="anker-reihe">{kacheln}</div></div>')
    personen = benennung.get("personen") or []
    opts = "".join(f'<option value="{html.escape(p)}">' for p in personen)
    # .224: die Easy-Antwortzeile — vorbereitete Antwort aus dem Vorschlag,
    # ein Klick benennt UND uebernimmt (JS-Kette) und springt weiter. Ohne
    # Vorschlag fragt sie direkt nach dem Namen (dieselbe Eingabe wie Expert).
    naechster = fluss.get("naechster")
    weiter_url = (f'/lernlauf/anker?a={html.escape(str(naechster))}'
                  if naechster else "/lernlauf/anker")
    skip_text = (t("lernanker.detail.skip_weiter") if naechster else
                 t("lernanker.detail.skip_zurueck"))
    e_leiste = (
        '<div class="bn-leiste nur-easy">'
        + (f'<button type="button" id="bn-easy-ja" class="gtb on" '
           f'data-name="{html.escape(v["name"])}">'
           + t("lernanker.detail.knopf_ja", name=html.escape(v["name"]))
           + '</button>'
           f'<button type="button" id="bn-easy-andere">{t("lernanker.detail.knopf_andere")}'
           '</button>' if v else
           '<button type="button" id="bn-easy-andere" class="gtb on">'
           + t("lernanker.detail.knopf_benennen_easy") + '</button>')
        + f'<a class="gtb" href="{weiter_url}">{html.escape(skip_text)}</a>'
        + '<span id="bn-easy-status" class="dim"></span></div>')
    leiste = (
        '<div class="bn-leiste nur-expert" id="bn-expertleiste">'
        f'<button type="button" id="bn-alle">{t("lernanker.detail.knopf_alle")}</button>'
        f'<button type="button" id="bn-keine">{t("lernanker.detail.knopf_keine")}</button>'
        '<span class="dim">·</span>'
        f'<input type="text" id="bn-name" list="bn-personen" '
        f'placeholder="{t("lernanker.detail.attr_name")}" '
        f'value="{html.escape(str(s.get("person") or ""))}">'
        f'<datalist id="bn-personen">{opts}</datalist>'
        f'<button type="button" id="bn-save" data-aid="{aid}">{t("lernanker.detail.knopf_benennen")}</button>'
        + (f'<button type="button" id="bn-adopt" data-aid="{aid}" class="gtb on">'
           + t("lernanker.detail.knopf_adopt") + '</button>' if schon else "")
        + '<span id="bn-status" class="dim"></span></div>')
    nx_js = (f'"{html.escape(str(naechster))}"' if naechster else "null")
    # Stufe 2 Tranche D (§8.4): ALLE JS-Texte kommen server-seitig aus
    # Schluesseln — json.dumps(t(...)) reproduziert die \u-/\n-Escapes des
    # Originals byte-treu (ensure_ascii=True); die drei Alt-Kurztexte
    # behalten ihr frigate.js-Interpolations-Muster. Kollisions-/Tag-Frage:
    # deklarierte Fragment-Splits an den Konkatenationsgrenzen (en.py
    # Tranche-D-Kommentar), wortgleich mit der Zuweisungs-Flaeche
    # (routes/lernwizard._zw_js — gemeinsame lernanker.js.*-Schluessel).
    js = ('<script>(function(){'
          'var alle=document.getElementById("bn-alle"),keine=document.getElementById("bn-keine");'
          'function boxen(){return document.querySelectorAll(".anker-w input[name=sel]")}'
          'alle.onclick=function(){boxen().forEach(function(b){'
          'b.checked=!b.closest(".anker-w").classList.contains("gedimmt");});};'
          'keine.onclick=function(){boxen().forEach(function(b){b.checked=false;});};'
          'var save=document.getElementById("bn-save"),st=document.getElementById("bn-status");'
          'var est=document.getElementById("bn-easy-status");'
          # .349 (Issue 26, Tokn59): ADOPT kettet Uebernehmen HINTER das
          # Benennen mit den LIVE-Haekchen — der alte bn-adopt-Direktweg
          # schickte nur die anker_id, die persistierte (ggf. leere) Auswahl
          # entschied, und die Seite zeigte Empfehlungs-Haekchen, die der
          # Server nie gesehen hatte ("nothing selected whilst images are
          # selected"). CHAIN bleibt die Easy-Weiterleitung zur naechsten Gruppe.
          f'var CHAIN=false,ADOPT=false,NX={nx_js};'
          'function melden(t){st.textContent=t;if(est)est.textContent=t;}'
          # .224: Uebernahme als eigene Funktion — Expert-Knopf UND Easy-Kette
          # nutzen denselben Weg; danach traegt die Kette zur naechsten Gruppe.
          'function adoptieren(best){melden('
          + json.dumps(t("lernanker.js.uebernimmt")) + ');'
          'fetch("/lernlauf/uebernehmen",{method:"POST",headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({anker_id:save.dataset.aid,bestaetigt:best})})'
          '.then(function(r){return r.json()}).then(function(d){'
          'if(d.tag_abweichung){if(confirm('
          + json.dumps(t("lernanker.js.tag_frage_vor")) + '+'
          'd.tag_abweichung.join("\\n")+'
          + json.dumps(t("lernanker.js.tag_frage_nach")) + '))'
          '{adoptieren(true);}else melden("' + t("lernanker.js.nicht_uebernommen")
          + '");return;}'
          'if(!d.ok){melden("' + t("lernanker.js.fehler") + ' "+d.msg);return;}'
          'if(CHAIN){if(NX){melden(' + json.dumps(t("lernanker.js.weiter")) + ');'
          'setTimeout(function(){location="/lernlauf/anker?a="+encodeURIComponent(NX)},500);}'
          'else{melden(' + json.dumps(t("lernanker.js.alle_fertig")) + ');'
          'setTimeout(function(){location="/lernlauf/anker"},1600);}return;}'
          'melden(d.msg);setTimeout(function(){location.reload()},1200);})'
          '.catch(function(e){melden("' + t("lernanker.js.fehler") + ' "+e);});}'
          'function senden(name,bestaetigt){'
          'var sel=[];boxen().forEach(function(b){if(b.checked)sel.push(b.value);});'
          'melden(' + json.dumps(t("lernanker.js.speichert")) + ');'
          'fetch("/lernlauf/benennen",{method:"POST",headers:{"Content-Type":"application/json"},'
          'body:JSON.stringify({anker_id:save.dataset.aid,person:name,gewaehlt:sel,'
          'bestaetigt:!!bestaetigt})}).then(function(r){return r.json()})'
          '.then(function(d){if(d.kollision){'
          'if(confirm(' + json.dumps(t("lernanker.js.koll_vor")) + '+name+'
          + json.dumps(t("lernanker.js.koll_mitte")) + '+d.kollision+'
          + json.dumps(t("lernanker.js.koll_nach"))
          + '))senden(d.kollision,true);'
          'else{ADOPT=false;melden("' + t("lernanker.js.nicht_gespeichert") + '");}return;}'
          'if(!d.ok){ADOPT=false;melden("' + t("lernanker.js.fehler") + ' "+d.msg);return;}'
          'if(ADOPT){ADOPT=false;adoptieren(false);return;}'
          'if(CHAIN){adoptieren(false);return;}'
          'melden(d.msg);setTimeout(function(){location.reload()},600);})'
          '.catch(function(e){ADOPT=false;melden("' + t("lernanker.js.fehler") + ' "+e);});}'
          'save.onclick=function(){ADOPT=false;'
          'senden(document.getElementById("bn-name").value,false);};'
          'var ad=document.getElementById("bn-adopt");'
          # .349: Uebernehmen laeuft ueber senden() mit den Live-Haekchen und
          # dem Feldnamen (bei benannten Clustern vorbelegt), nie mehr direkt.
          'if(ad)ad.onclick=function(){CHAIN=false;ADOPT=true;'
          'senden(document.getElementById("bn-name").value,false);};'
          'var ja=document.getElementById("bn-easy-ja");'
          'if(ja)ja.onclick=function(){CHAIN=true;senden(ja.dataset.name,false);};'
          'var an=document.getElementById("bn-easy-andere");'
          'if(an)an.onclick=function(){CHAIN=true;'
          'var l=document.getElementById("bn-expertleiste");'
          'l.classList.remove("nur-expert");'
          'document.getElementById("bn-name").focus();};'
          '})();</script>')
    return (stil + kopf + hinweis
            + f'<div class="dim nur-expert">{t("lernanker.detail.hinweis_auswahl")} · '
            + t("lernanker.detail.hinweis_pfeil")
            + f' · <a href="/lernlauf/anker">{t("lernanker.link_zurueck")}</a></div>'
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
            f'data-frage="'
            + t("lernanker.liste.frage_lauf", lid=html.escape(lid), n=n) + '">'
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
                f'data-frage="'
                + t("lernanker.liste.frage_alle", alt=len(laeufe) - 1,
                    n=alt_n, neuester=html.escape(neuester)) + '">'
                + t("lernanker.liste.knopf_alte",
                    neuester=html.escape(neuester)) + '</button>')
        lauf_zeile = (f'<div class="card">{t("lernanker.liste.lauf_zeile")}'
                      f' {knoepfe}{alle_knopf}</div>')
    # Dismiss mit Gedaechtnis (User 05.08.): verworfene Cluster verschwinden aus
    # der Liste, ihre Zeilen bleiben als Erbschafts-Gedaechtnis — GEZAEHLT
    # ausgewiesen, nie still (Leitprinzip 3).
    verworfen_n = sum(1 for s in saetze if s.get("status") == "verworfen")
    saetze = [s for s in saetze if s.get("status") != "verworfen"]
    verworfen_hinweis = (
        f'<div class="dim">{t("lernanker.liste.verworfen", n=verworfen_n)}</div>'
        if verworfen_n else "")
    if not saetze:
        return (f"<h2>{t('lernanker.titel')}</h2>" + verworfen_hinweis + lauf_zeile
                + f'<div class="card">{t("lernanker.liste.leer")} '
                  f'<a href="/lernlauf">{t("lernanker.liste.leer_link")}</a>.</div>')
    ok_n = sum(1 for s in saetze if (s.get("qualitaet") or {}).get("eimer") == "ok")
    ges = sum((s.get("qualitaet") or {}).get("stuetz", 0) for s in saetze)
    # Stufe-0-Grenze: <b>-Satzteil der Kaputt-Warnung bleibt literal.
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
        mehr = (f'<a class="pill" href="/lernlauf/anker?a={aid}">'
                f'{t("lernanker.liste.mehr", n=rest)}</a>'
                if rest > 0 else "")
        tage = q.get("tage_liste") or []
        spanne = f'{tage[0]} … {tage[-1]}' if len(tage) > 1 else (tage[0] if tage else "—")
        kams = sorted({m.get("kamera", "?") for m in mitglieder})
        status_html = (_badge(t("lernanker.eimer.ok")) if not dim else
                       _badge(f'{_eimer_text().get(eimer, eimer)}: '
                              f'{q.get("eimer_grund", "")}', dim=True))
        if dup_von:
            status_html += _badge(t("lernanker.liste.dublette", anker=dup_von),
                                  dim=True)
        _vs = vorschlaege.get(s.get("anker_id"))
        if _vs and s.get("status") not in ("benannt", "uebernommen"):
            # "kennen wir schon"-Semantik (User 05.08.): Referenz-/Master-Treffer
            # heisst, die Person IST im System — der Lauf liefert nur neues
            # Material fuer sie. Treffer aus bloss benannten Ankern sagen das
            # ehrlich schwaecher. Stufe-0-Grenze: der looks-like-Pill traegt
            # <b> mitten im Satz — Rahmen literal, _bek-Halbsatz Schluessel.
            _bek = (t("lernanker.bekannt.system") if {"referenz", "master"}
                    & set(_vs.get("quellen") or []) else t("lernanker.bekannt.anker"))
            status_html += ('<span class="pill" style="border-color:var(--ok)">'
                            f'looks like <b>{html.escape(str(_vs.get("name")))}</b> '
                            f'({_vs.get("sim")}) — {_bek}; naming the cluster '
                            'adds these faces to their references</span>')
        # E4a (User-Vorgabe 01.08.): der Klick-Weg zum Benennen muss auf der Karte SICHTBAR
        # sein — ein Knopf je Cluster, unter den Gesichtern. Benannte tragen den
        # Namen als Badge und der Knopf wechselt auf "Review naming".
        st_a = s.get("status")
        # Stufe-0-Grenze: named-/adopted-Pill (<b> im Satz) bleibt literal.
        benannt_pill = (f'<span class="pill">named: <b>{html.escape(str(s.get("person")))}</b>'
                        ' — adoption pending</span>' if st_a == "benannt" else
                        (f'<span class="pill">adopted: <b>{html.escape(str(s.get("person")))}</b></span>'
                         if st_a == "uebernommen" else ""))
        knopf_txt = (t("lernanker.liste.knopf_review") if st_a == "benannt" else
                     (t("lernanker.liste.knopf_view") if st_a == "uebernommen" else
                      t("lernanker.liste.knopf_benennen", n=q.get("stuetz", 0))))
        # Dismiss mit Gedaechtnis (User 05.08.): Zeile+Zentroid bleiben,
        # Wiederernten derselben Events erben still. Seit .259 auch fuer
        # BENANNTE Cluster (Endpunkt-Erweiterung mit der Zuweisungs-Flaeche
        # — nichts ist im Master, die Benennung wird mit verworfen); nur
        # uebernommene nie. B9: je Zweig ein GANZER Satz-Schluessel.
        frage = (t("lernanker.liste.frage_verwerfen_benannt")
                 if st_a == "benannt" else t("lernanker.liste.frage_verwerfen"))
        verwerf = ('' if st_a == "uebernommen" else
                   f'<button class="gtb" onclick="ankerVerwerfen(\'{aid}\',this)" '
                   f'data-frage="{frage}">'
                   + t("lernanker.liste.knopf_verwerfen") + '</button>')
        knopf = (f'<div style="margin-top:6px"><a class="gtb on" href="/lernlauf/anker?a={aid}">'
                 f"{knopf_txt}</a> {verwerf}</div>")
        karten.append(
            f'<div class="card"><b>{html.escape(str(s.get("anker_id")))}</b> {status_html} '
            + benannt_pill
            + _badge(t("lernanker.badge.faces", n=q.get("stuetz", 0)))
            + _badge(t("lernanker.badge.durchgaenge", n=q.get("durchgaenge", 0)))
            + _badge(t("lernanker.badge.tage", n=q.get("tage", 0), spanne=spanne))
            + _badge(", ".join(kams)) + _badge(t("lernanker.badge.marge", marge=q.get("marge")))
            + f'<div class="anker-reihe">{"".join(thumbs)}{mehr}</div>{knopf}</div>')
    stil = ('<style>.anker-reihe{display:flex;flex-wrap:wrap;gap:4px;align-items:flex-start;margin-top:6px}'
            '.anker-thumb{max-width:72px;max-height:72px;border-radius:4px;display:block}'
            '.anker-thumb.gedimmt{opacity:.45}'
            '.pill{display:inline-block;border:1px solid var(--rand,#8884);'
            'border-radius:10px;padding:0 8px;margin:0 4px 2px 0;font-size:.85em}'
            '.pill.dim{opacity:.6}</style>')
    # .200 (Fix 4): E4b ist laengst gebaut (/lernlauf/uebernehmen) —
    # der Adopt-Knopf steht im benannten Cluster.
    return (stil + f"<h2>{t('lernanker.titel')}</h2>"
            f'<div class="card">'
            + t("lernanker.liste.kopf", n=len(saetze), ges=ges, ok=ok_n,
                rest=len(saetze) - ok_n)
            + f' <a href="/lernlauf">{t("lernanker.liste.kopf_link")}</a>.</div>'
            + verworfen_hinweis + lauf_zeile
            + kopf_warn + "".join(karten))
