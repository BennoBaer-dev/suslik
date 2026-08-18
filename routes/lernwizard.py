"""routes/lernwizard — der Anlern-Assistent + Lauf-Seiten-Geruest (E1 Baustein 4b,
seit E2 mit ECHTER Vorbereitung+Ernte; Konzept §P0/§2b/§4). Die Phasen ab
Gruppierung (E3) sind weiter Geruest und sagen das ehrlich.
Kontrakt wie alle routes-Module: reine Renderer, Daten als Parameter, kein
Dienst-Import; Seiteneffekte (Events holen, Messung anstossen, Lauf anlegen)
macht der Handler."""
import datetime
import html

from core.lernlauf import PHASEN

# Anzeige-Reihenfolge + Klartext je Phase (englische UI wie ueberall).
PHASEN_TEXT = {
    "vorbereitung": "Preparation", "ernte": "Harvest (collect faces)",
    "anker": "Grouping (anchors)", "benennung": "Naming (your step)",
    "neben_ansichten": "Side views", "ganzkoerper": "Full-body stock",
    "uebernahme": "Adoption into the master", "fertig": "Done",
}


def _dt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%a %d.%m. %H:%M") if ts else "—"


def _dauer(s):
    s = int(round(max(s, 0)))
    return f"{s//60} min {s%60} s" if s >= 60 else f"{s} s"


def wizard(personen_zahl, auswahl, bilanz, prognose, quelle, schwellen,
           messung_laeuft=False, gemessen_felder=(), alle=False, bestaetigen_ab=1000,
           max_events=40000, mess_wartet=False, mess_skip="", unbekannt_offen=0):
    """Wizard-Ansicht. auswahl = Event-Zahl (int) oder None; alle=True bei ?events=alle;
    quelle 'gemessen'|'rueckfall' + gemessen_felder = WIRKLICH gemessene Konstanten
    (Teil-Kennung, Widerleger F3.1); bestaetigen_ab: ab dieser Zahl verlangt der
    Start-Knopf den Bestaetigungs-Dialog MIT den Schaetz-Zahlen (User-Wunsch 3);
    unbekannt_offen = wartende Unbekannt-Cluster von heute (core/unbekanntpool,
    dieselbe Quelle wie die Today-Kachel — Baustein B 12.08.)."""
    lage = ("B — existing references/unknowns will be extended"
            if personen_zahl else "A — cold start, no faces yet")
    teile = ["<h2>Learn people — guided run</h2>",
             # .200 (Fix 4): "ships in the next updates" war seit E4b falsch und
             # widersprach der Phasen-Karte weiter unten auf derselben Seite.
             '<p class="sub">Plans a learning run over your own recordings. '
             "Preparation, harvest, grouping, naming and adoption into "
             "recognition all run for real.</p>"]
    if unbekannt_offen:
        # Baustein B (12.08., Realfall Besuch): der Querverweis, der fehlte — ein
        # Lernlauf ist fuer heutige unbekannte Besucher gar nicht noetig, ihre
        # Gesichter liegen schon gesammelt unter People -> Unknown.
        teile.append(
            '<div class="card"><span class="badge warn">unknown visitors</span> '
            f'<b>{int(unbekannt_offen)} unknown visitor'
            f'{"s are" if unbekannt_offen != 1 else " is"} waiting under '
            '<a href="/unbekannte">People &rarr; Unknown</a></b>'
            '<div class="dim">Faces collected today that match no known person — '
            'you can name, merge or mute them there right away; '
            'no learning run needed for that.</div></div>')
    teile.append(
             f'<div class="card"><b>Starting point</b><div>{html.escape(lage)}</div>'
             '<div class="dim">Clean-up switch for auto-collected unknowns: '
             "arrives with the naming stage.</div></div>")
    knoepfe = "".join(
        f'<a class="gtb{" on" if (auswahl == n and not alle) else ""}" '
        f'href="/lernlauf?events={n}">last {n}</a> '
        for n in (100, 300, 1000))
    knoepfe += (f'<a class="gtb{" on" if alle else ""}" href="/lernlauf?events=alle">'
                f'ALL reachable</a>')
    eigen = ('<form action="/lernlauf" method="get" style="display:inline;margin-left:10px">'
             f'<input name="events" type="number" min="1" max="{int(max_events)}" size="6" '
             f'value="{auswahl if (auswahl and not alle) else ""}" placeholder="own N"> '
             '<button class="gtb">go</button></form>')
    teile.append(f'<div class="card"><b>Scope (events, not days)</b>'
                 f'<div>{knoepfe}{eigen}</div>'
                 '<div class="dim">ALL walks the whole reachable history '
                 "(bounded by Frigate's retention — the balance below shows how far).</div></div>")
    if auswahl and bilanz:
        b = bilanz
        teile.append(
            f'<div class="card"><b>Your selection</b><div>last {b["n"]} person events '
            f'= back to {_dt(b["aeltester_ts"])} · {b["mit_clip"]} with an available clip'
            + (f' — <b>{b["ohne_clip"]} older ones without a clip will be skipped</b>'
               if b["ohne_clip"] else "") + "</div>"
            '<div class="dim">The cut is exact at N — completing selections to full '
            "passes arrives with the grouping stage.</div></div>")
        if prognose:
            if quelle == "gemessen":
                q = ("analysis speed measured on THIS machine; download estimate uses "
                     "defaults" if gemessen_felder else "measured on THIS machine")
            else:
                # Pflichtpunkt .172: Skip und Warten ehrlich benennen — "measuring
                # now" waere in beiden Faellen gelogen (K1, falsche Darstellung).
                if mess_skip:
                    zusatz = f", measurement skipped on this machine ({mess_skip})"
                elif mess_wartet:
                    zusatz = ", measurement waiting for a free analysis slot …"
                elif messung_laeuft:
                    zusatz = ", measuring now …"
                else:
                    zusatz = ""
                q = "fallback values — not yet measured here" + zusatz
            teile.append(
                f'<div class="card"><b>Estimated duration</b> <span class="dim">({html.escape(q)})</span>'
                f'<div>analysis ~{_dauer(prognose["analyse_s"])} · clip downloads '
                f'~{_dauer(prognose["download_s"])} · one-time warm-up {_dauer(prognose["kalt_s"])} '
                f'→ <b>total ~{_dauer(prognose["gesamt_s"])}</b></div></div>')
        s_html = "".join(f'<span class="dim" style="margin-right:10px">{html.escape(k)}='
                         f'{html.escape(str(v))}</span>' for k, v in (schwellen or []))
        teile.append(f'<div class="card"><b>Thresholds (adjustable in Advanced)</b>'
                     f'<div>{s_html or "—"}</div></div>')
        # Bestaetigungs-Dialog (User-Wunsch 3): bei ALLE oder grossem N traegt der
        # Knopf die ECHTEN Schaetz-Zahlen als data-Attribut — app.js zeigt sie im confirm.
        n_start = bilanz["n"]
        frage = ""
        if prognose and (alle or n_start >= bestaetigen_ab):
            frage = (f'Learn from all {n_start} events? Estimated duration '
                     f'~{_dauer(prognose["gesamt_s"])} (analysis {_dauer(prognose["analyse_s"])} '
                     f'+ downloads {_dauer(prognose["download_s"])}). '
                     f'The run can be aborted at any time.')
        # .90 (Task #11, Benchmark am eigenen Tuerkamera-Clip): PROMINENTE Abfrage
        # der Abtastrate als eigene Wizard-Karte, mit gemessener Abwaegung und live
        # mitskalierender Dauer-Schaetzung (app.js llFpsUpdate; Analyse-Anteil ~linear).
        p = prognose or {}
        teile.append(
            '<div class="card"><b>Analysis frames per second</b>'
            '<div><input id="ll-fps" type="number" min="1" max="30" step="0.5" value="3" '
            f'style="width:4.5em" oninput="llFpsUpdate(this)" '
            f'data-analyse="{p.get("analyse_s", 0)}" data-rest="'
            f'{(p.get("download_s", 0) or 0) + (p.get("kalt_s", 0) or 0)}"> '
            '<span id="ll-fps-est" class="dim"></span></div>'
            '<div class="dim">Measured on this installation (door-cam sweep 1&ndash;10/s): '
            'yield grows roughly linearly with compute time, so pick by patience — '
            '<b>3</b>/s is the calibrated default, <b>6</b>/s roughly doubles the '
            'anchor-ready faces, <b>10</b>/s is the maximum harvest (~4&#215; over 3/s '
            'for ~3&#215; the time). In-between values buy little: 4/s matched 3/s '
            'exactly, and 6, 7 and 8/s hit the same frames (sampling rounds to the '
            'feed rate). Asking for more than your camera feed delivers changes '
            'nothing — the reader then simply takes every frame.</div></div>')
        teile.append(f'<p><button class="gtb on" data-frage="{html.escape(frage, quote=True)}" '
                     f'onclick="lernlaufStart({n_start},this)">'
                     f'Create this run</button> <span id="ll-status" class="dim"></span></p>')
    return "".join(teile)


# .88/V3: welcher Fortschritts-Schluessel gehoert zu welcher Phase (Anzeige-Gruppierung).
_PHASEN_KEYS = {
    "vorbereitung": ("checking events", "already searched (skipped)"),
    "ernte": ("event", "analysing", "rest", "with clip", "skipped (no clip)",
              "candidates", "crop-worthy (M)", "anchor-ready (S)",
              "objects filtered (fd rule)", "without a face", "clip not readable",
              "clips partly readable", "no pose data", "counter mismatch",
              "worker errors", "last find", "files vs counters"),
    "anker": ("anchors", "ok", "hart", "thin", "unconfirmed", "merge suggestions",
              "passes with material", "events without harvest data",
              "unreadable candidate lines", "degenerate embeddings skipped",
              "leftover single clusters (cap)", "stage-2 rounds (approximation)"),
}


# .246: Benenn-Kette der Zuweisungs-Flaeche — DIESELBEN Endpunkte wie die
# Benennungs-Karte (/lernlauf/benennen -> /lernlauf/uebernehmen, inkl.
# Kollisions- und Tag-Abweichungs-Dialog); nach Erfolg laedt /lernlauf neu
# und serviert die naechste offene Gruppe.
# .256 (User-Go 17.08. abends, Bruecken-Muster): der Ja-Klick benennt
# SOFORT, meldet "checking the pictures" und holt die Pruefung
# (/lernlauf/benenn_pruefung, read-only) — Kacheln bekommen Rahmen+Grund,
# dann bestaetigt EIN Klick ("Take N pictures for X") mit der SICHTBAREN
# Auswahl (re-benennen bestaetigt + uebernehmen). Nichts verschwindet still.
# .257 (User-Fang: 12 schlechte Bilder passierten mit gruenem Rahmen): die
# Pruefung ist jetzt die ECHTE Bruecken-Latte (gut/grenzfall/raus je Bild,
# warmes Modell mit laden-Nachfrage wie das Bruecken-Overlay); Grenzfaelle
# kommen abgehakt in goldenrod und sind wieder anhakbar, der Take-Knopf
# zaehlt live die Haken.
_ZW_JS = (
    '<script>(function(){'
    'var zw=document.getElementById("lf-zw");if(!zw)return;'
    'var AID=zw.dataset.aid,st=document.getElementById("lf-status"),'
    'NAME=null;'
    'function melden(t){st.textContent=t;}'
    'window.lfZaehl=function(){'
    # .268: sichtbare Kacheln zaehlen (der zugeklappte Aufklapper zaehlt
    # nicht mit); angehakte zaehlen IMMER — auch eingeklappt Gewaehltes
    # wird uebernommen, das darf die Zahl nie verschweigen.
    'var a=Array.from(document.querySelectorAll(".lf-zwg input"))'
    '.filter(function(b){return b.closest("label").offsetParent!==null})'
    '.length,'
    'n=document.querySelectorAll(".lf-zwg input:checked").length;'
    'document.getElementById("lf-zaehl").textContent='
    'n+" of "+a+" pictures selected";};'
    'lfZaehl();'
    'function adoptieren(best){melden("adopting\\u2026");'
    'fetch("/lernlauf/uebernehmen",{method:"POST",'
    'headers:{"Content-Type":"application/json"},'
    'body:JSON.stringify({anker_id:AID,bestaetigt:best})})'
    '.then(function(r){return r.json()}).then(function(d){'
    'if(d.tag_abweichung){if(confirm("Settings changed since naming:\\n"+'
    'd.tag_abweichung.join("\\n")+"\\nAdopt anyway with the named selection?"'
    '))adoptieren(true);else melden("not adopted");return;}'
    'if(!d.ok){melden("error: "+d.msg);return;}'
    'melden("saved \\u2014 next group\\u2026");'
    'setTimeout(function(){location="/lernlauf"},500);})'
    '.catch(function(e){melden("error: "+e);});}'
    'function takeText(name){'
    'var n=document.querySelectorAll(".lf-zwg input:checked").length,'
    'tk=document.getElementById("lf-take");'
    'tk.textContent="Take "+n+" picture"+(n==1?"":"s")+" for "+name;'
    'tk.disabled=!n;}'
    'function pruefen(name){NAME=name;'
    'melden("saved as "+name+" \\u2014 checking the pictures \\u2026");'
    'fetch("/lernlauf/benenn_pruefung",{method:"POST",'
    'headers:{"Content-Type":"application/json"},'
    'body:JSON.stringify({anker_id:AID})})'
    '.then(function(r){return r.json()}).then(function(d){'
    'if(!d.ok){melden("error: "+d.msg);return;}'
    'if(d.laden){melden(d.msg);'
    'setTimeout(function(){pruefen(name)},1500);return;}'
    'var bew={};var g=0,gz=0,rs=0;'
    # .266: Zaehler aus der ANTWORT (alle gesichteten Kandidaten) — die
    # Flaeche rendert raus-Bilder nicht mehr, gezaehlt werden sie trotzdem.
    '(d.bewertung||[]).forEach(function(b){bew[b.datei]=b;'
    'if(b.stufe=="gut")g++;else if(b.stufe=="grenzfall")gz++;else rs++;});'
    # .267 (Widerleger): Haken nur anfassen, wenn sich das URTEIL geaendert
    # hat (Personen-Wechsel) — die Handauswahl des Users bleibt sonst stehen.
    'document.querySelectorAll(".lf-zwg label").forEach(function(l){'
    'var b=l.querySelector("input");if(!b)return;'
    'var e=bew[b.value];if(!e)return;'
    'var vorher=l.classList.contains("lf-neu")?"gut":'
    '(l.classList.contains("lf-grenz")?"grenzfall":'
    '(l.classList.contains("lf-dup")?"raus":""));'
    'l.classList.remove("lf-neu","lf-grenz","lf-dup");'
    'var alt=l.querySelector(".lf-zwgrund");if(alt)alt.remove();'
    'if(e.grund){var s=document.createElement("span");'
    's.className="lf-zwgrund";s.textContent=e.grund;l.appendChild(s);}'
    'l.classList.add(e.stufe=="gut"?"lf-neu":'
    '(e.stufe=="grenzfall"?"lf-grenz":"lf-dup"));'
    'if(vorher!==e.stufe){b.checked=(e.stufe=="gut");}});'
    'lfZaehl();'
    'melden(g+" good for "+name'
    '+(gz?(", "+gz+" borderline (tick to keep)"):"")'
    '+(rs?(", "+rs+" rejected"):""));'
    'document.getElementById("lf-knopfzeile-1").style.display="none";'
    'takeText(name);'
    'document.querySelectorAll(".lf-zwg input").forEach(function(b){'
    'b.onchange=function(){lfZaehl();takeText(name);};});'
    'document.getElementById("lf-knopfzeile-2").style.display="flex";})'
    '.catch(function(e){melden("error: "+e);});}'
    'function senden(name,best,dann){var sel=[];'
    'document.querySelectorAll(".lf-zwg input:checked")'
    '.forEach(function(b){sel.push(b.value);});'
    'melden("saving\\u2026");'
    'fetch("/lernlauf/benennen",{method:"POST",'
    'headers:{"Content-Type":"application/json"},'
    'body:JSON.stringify({anker_id:AID,person:name,gewaehlt:sel,'
    'bestaetigt:!!best})})'
    '.then(function(r){return r.json()}).then(function(d){'
    'if(d.kollision){if(confirm("\\u2019"+name+"\\u2019 matches existing '
    '\\u2019"+d.kollision+"\\u2019 \\u2014 add to that person instead?"))'
    'senden(d.kollision,true,dann);else melden("not saved");return;}'
    'if(!d.ok){melden("error: "+d.msg);return;}'
    'dann(d.person||name);})'
    '.catch(function(e){melden("error: "+e);});}'
    'var ja=document.getElementById("lf-ja");'
    'if(ja)ja.onclick=function(){senden(ja.dataset.name,false,pruefen);};'
    'var ad=document.getElementById("lf-adopt");'
    'if(ad)ad.onclick=function(){pruefen(ad.dataset.person||"");};'
    'var an=document.getElementById("lf-andere"),'
    'nm=document.getElementById("lf-name"),'
    'sv=document.getElementById("lf-save");'
    'an.onclick=function(){nm.style.display="inline-block";'
    'sv.style.display="inline-block";nm.focus();};'
    'sv.onclick=function(){if(nm.value.trim())'
    'senden(nm.value.trim(),false,pruefen);};'
    'var tk=document.getElementById("lf-take");'
    'if(tk)tk.onclick=function(){'
    'senden(NAME,true,function(){adoptieren(false);});};'
    'var cx=document.getElementById("lf-cancel");'
    'if(cx)cx.onclick=function(){location.reload();};'
    '})();</script>')


def _frac(s):
    """'12/50' -> (12, 50) oder None — Zaehlerformat der Ernte (verifyd fs['event'])."""
    try:
        a, b = str(s).split("/", 1)
        a, b = int(a), int(b)
        return (a, b) if b > 0 else None
    except (ValueError, AttributeError):
        return None


# .266: Erst-Sichtung anstossen (Cache fehlt) — Warm-Lade-Schleife wie die
# Bruecke, danach EIN Reload; die Flaeche rendert dann aus dem Ergebnis.
_SICHT_JS = (
    '<script>(function(){'
    'var aid=document.getElementById("lf-zw").getAttribute("data-aid");'
    'function los(){'
    'fetch("/lernlauf/sichtung",{method:"POST",'
    'body:JSON.stringify({anker_id:aid})})'
    '.then(function(r){return r.json()})'
    '.then(function(d){'
    'if(d.laden){var w=document.getElementById("lf-sicht-warte");'
    'if(w&&d.msg)w.textContent="\\u23f3 "+d.msg;'
    'setTimeout(los,1200);return;}'
    'if(!d.ok){var w2=document.getElementById("lf-sicht-warte");'
    'if(w2)w2.textContent=d.msg||"check failed — reload to retry";return;}'
    'location.reload();'
    '}).catch(function(){setTimeout(los,3000);});}'
    'los();})();</script>')


def lauf_status(zustand):
    """.260 Saeule-Widget: EINE Quelle fuer den Seiten-Render UND den
    /lernlauf_status-Endpunkt — render-fertige Werte (Fuell-Prozent,
    Phasen-Marken, Zeit- und Zaehler-Zeile, tickt). Das Browser-JS wendet
    die Werte nur an und rechnet NICHTS nach (QS-Ebenen-Regel: kein
    Zweit-Rechner neben der Saeulen-Logik). tickt uebernimmt die alte
    meta-refresh-Regel aus dem verifyd-Handler unveraendert (steht bei
    'anchor stage failed' still statt ewig zu pollen)."""
    z = zustand or {}
    ph = z.get("phase")
    f = z.get("fortschritt") or {}
    st = str(f.get("status", ""))
    idx = PHASEN.index(ph) if ph in PHASEN else 0
    anker_fertig = ph == "anker" and st.startswith(("anchors ready",
                                                    "anchors: none"))
    laeuft = (ph in ("vorbereitung", "ernte")
              or (ph == "anker" and not anker_fertig))
    proz = 0
    if zustand is not None:
        if ph == "vorbereitung":
            fr = _frac(f.get("checking events"))
            proz = int(15 * fr[0] / fr[1]) if fr else 5
        elif ph == "ernte":
            fr = _frac(f.get("event"))
            proz = (15 + int(70 * fr[0] / fr[1])) if fr else 15
        elif ph == "anker" and not anker_fertig:
            proz = 85
        else:
            proz = 100
    seg = []
    for i_s, lbl in ((0, "Prepare"), (1, "Collect faces"),
                     (2, "Sort into groups")):
        done = zustand is not None and (
            (i_s == 0 and idx > 0) or (i_s == 1 and idx > 1)
            or (i_s == 2 and (anker_fertig or idx > 2)))
        aktiv = zustand is not None and not done and (
            (i_s == 0 and ph == "vorbereitung")
            or (i_s == 1 and ph == "ernte")
            or (i_s == 2 and ph == "anker"))
        seg.append({"label": lbl,
                    "zust": "ok" if done else ("an" if aktiv else "")})
    akt = z.get("aktualisiert")
    zeit = ""
    if zustand is not None and z.get("ts"):
        if laeuft:
            zeit = ("running for "
                    + _dauer(max(0, datetime.datetime.now().timestamp()
                                 - z["ts"])))
            if f.get("rest"):
                zeit += f' · {f["rest"]} remaining'
        elif akt and akt > z["ts"]:
            zeit = f'finished in {_dauer(akt - z["ts"])}'
    teile_z = []
    if laeuft:
        if f.get("event"):
            teile_z.append(f'recordings: {f["event"]}')
        if f.get("candidates") is not None:
            teile_z.append(f'{f["candidates"]} pictures collected so far')
    tickt = zustand is not None and (
        (ph in ("vorbereitung", "ernte")
         and (not st or st.startswith(("prepared", "harvesting", "waiting"))))
        or (ph == "anker"
            and not st.startswith(("anchors", "anchor stage failed"))))
    return {"proz": proz, "seg": seg, "zeit": zeit,
            "zaehler": " · ".join(teile_z),
            "laeuft": bool(laeuft), "tickt": bool(tickt)}


def _seg_html(sg):
    m = ('<span class="phok">&#10003;</span>' if sg["zust"] == "ok" else
         ('<span class="lf-puls"></span>' if sg["zust"] == "an" else
          '<span class="dim">&#183;</span>'))
    return f'<div class="{sg["zust"]}">{m} {sg["label"]}</div>'


# .260: das Saeule-Widget — pollt /lernlauf_status alle 3 s und bewegt NUR
# Saeule/Marken/Zeit/Zaehler (kein Flackern, kein Scroll-Sprung); wechselt
# der Lauf in die Benennung (tickt->False), laedt es genau EINMAL voll neu.
# mark() spiegelt _seg_html — beide bauen aus denselben lauf_status-Werten.
_WIDGET_JS = (
    '<script>(function(){'
    'function mark(z){return z=="ok"?\'<span class="phok">\\u2713</span>\':'
    '(z=="an"?\'<span class="lf-puls"></span>\':'
    '\'<span class="dim">\\u00b7</span>\');}'
    'var t=setInterval(function(){'
    'fetch("/lernlauf_status").then(function(r){return r.json()})'
    '.then(function(d){if(!d.ok)return;'
    'if(!d.tickt){clearInterval(t);location.reload();return;}'
    'var fu=document.querySelector(".lf-saeule .fuell");'
    'if(fu)fu.style.height=d.proz+"%";'
    'var seg=document.querySelectorAll(".lf-phasen>div");'
    'd.seg.forEach(function(s,i){var el=seg[i];if(!el)return;'
    'el.className=s.zust;el.innerHTML=mark(s.zust)+" "+s.label;});'
    'var ze=document.getElementById("lf-zeit");'
    'if(ze)ze.textContent=d.zeit;'
    'var zl=document.getElementById("lf-zaehler");'
    'if(zl)zl.textContent=d.zaehler;'
    '}).catch(function(){});},3000);'
    '})();</script>')


def lauf_seite(zustand, anker_zahl=0, anker_kaputt=0, gruppen=None, adoptiert=None,
               benennung=None, aktuelle=None, naechste_id=None,
               easy_events=300, unbekannt_offen=0, max_events=40000,
               personen=None, zielperson="", reihenfolge=None,
               sichtung=None, sichtung_gesamt=0):
    """.246 (Lernfluss-Redesign, Mockup b_lernfluss, User-Abnahme 17.08.):
    EINE Fluss-Seite mit vier Kacheln (Start / Saeule / Benennen / Fertig) und
    der Zuweisungs-Flaeche ueber die ganze Zeile. zustand darf None sein
    (kein Lauf: Kachel 1 mit Easy-Start-Knopf; der volle Planer haengt als
    nur-expert dahinter — Handler-Komposition). benennung/aktuelle: der
    Benennungs-Kontext der aktuell offenen Gruppe (benennungs_kontext),
    naechste_id = Skip-Ziel. Bestehende Vertraege bleiben: Zaehler/Phasen-
    Kette als Expert-Tiefe, Mutationen NUR ueber /lernlauf/benennen +
    /lernlauf/uebernehmen (dieselben Endpunkte wie die Benennungs-Karte).
    .86: 'working'-Puls; .244: Ergebnis-Zeile/Bilanz aus echten Zaehlern."""
    z = zustand or {}
    ph = z.get("phase")
    akt = z.get("aktualisiert")
    puls = ""
    if akt and ph in ("vorbereitung", "ernte", "anker"):
        alter = max(0, int(datetime.datetime.now().timestamp() - akt))
        st = str((zustand.get("fortschritt") or {}).get("status", ""))
        laeuft = not st.startswith(("anchors", "anchor stage failed", "prepared", "planned"))
        if laeuft:
            puls = (f'<div class="dim">&#9679; working — updated {alter}s ago</div>'
                    if alter <= 60 else
                    f'<div class="dim">&#9888; no update for {alter}s — a long clip '
                    'can take minutes; if this keeps growing, check /log</div>')
    f = z.get("fortschritt") or {}
    st = str(f.get("status", ""))
    # Alt-Laeufe tragen den vor-E4a-Statustext im State — nur die ANZEIGE mappt
    # ihn auf den neuen Stand, die Datei bleibt unangetastet.
    st = st.replace("naming ships with the next update", "open a cluster to name it")
    # .88 / V3: Zaehler JE PHASE gruppiert unter ihrer Phasen-Zeile — jede
    # Phase zaehlt ihre eigenen Zahlen hoch und bekommt beim Abschluss den gruenen
    # Haken; die alte Misch-Kette ("anchors" hinter 13 Ernte-Zaehlern) entfaellt.
    idx = PHASEN.index(ph) if ph in PHASEN else 0
    anker_fertig = ph == "anker" and st.startswith(("anchors ready", "anchors: none"))
    zeilen = []
    for p in PHASEN:
        pi = PHASEN.index(p)
        fertig = pi < idx or (p == "anker" and anker_fertig)
        aktiv = p == ph and not fertig
        mark = ('<span class="phok">&#10003;</span>' if fertig
                else ("&#9654;" if aktiv else '<span class="dim">&#183;</span>'))
        keys = [k for k in _PHASEN_KEYS.get(p, ()) if k in f]
        det = " · ".join(f"{k}: {f[k]}" for k in keys)
        det_html = f'<div class="phdet dim">{html.escape(det)}</div>' if det else ""
        # E4a (Zug 2b): die Benennung ist LIVE — sobald die Anker stehen, ist
        # 'Naming' der aktive, VERLINKTE Schritt statt eines toten Punkts.
        name_link = ""
        if p == "benennung" and anker_fertig:
            mark = "&#9654;"
            name_link = (' <a href="/lernlauf/anker">open the clusters and '
                         'name them</a>')
        zeilen.append(f'<div class="phz">{mark} {html.escape(PHASEN_TEXT[p])}'
                      + (' <span class="dim">(current)</span>' if aktiv else "")
                      + name_link + det_html + "</div>")
    zugeordnet = {k for ks in _PHASEN_KEYS.values() for k in ks} | {"status"}
    rest = " · ".join(f"{k}: {f[k]}" for k in f if k not in zugeordnet)
    rest_html = f'<div class="dim">{html.escape(rest)}</div>' if rest else ""
    kaputt_html = (f' · <b>{anker_kaputt} unreadable lines counted</b>' if anker_kaputt else "")
    anker_link = (f' · <a href="/lernlauf/anker">view the {anker_zahl} anchor clusters</a>'
                  if anker_zahl else "")
    # .246: das Chip-/Vorschau-CSS der .223/.244-Fassung ist ersetzt — die
    # Kacheln, Queue und Flaeche unten sind jetzt die eine Darstellung.
    stil = ('<style>.phok{color:seagreen;font-weight:bold}'
            '.phz{margin:2px 0}.phdet{margin:0 0 4px 1.4em;font-size:.9em}'
            # .246: Vier-Kachel-Fluss + Saeule + Zuweisungs-Flaeche (Mockup
            # b_lernfluss, User-Abnahme 17.08.)
            '.lf-fluss{display:grid;grid-template-columns:repeat(4,1fr);'
            'gap:14px;margin:14px 0}'
            '@media(max-width:1000px){.lf-fluss{grid-template-columns:1fr 1fr}}'
            '@media(max-width:560px){.lf-fluss{grid-template-columns:1fr}}'
            '.lf-k{position:relative;background:var(--surface);'
            'border:1px solid var(--border);border-radius:12px;'
            'padding:14px 14px 12px;min-height:220px;display:flex;'
            'flex-direction:column;gap:7px}'
            '.lf-k.dran{border-color:var(--accent);'
            'box-shadow:0 0 0 1px var(--accent)}'
            '.lf-k.folgt{opacity:.45}'
            '.lf-k.fertig{border-color:seagreen}'
            '.lf-k h3{margin:0;font-size:15px;display:flex;align-items:center;gap:8px}'
            '.lf-k .nr{width:23px;height:23px;border-radius:50%;'
            'background:var(--border);display:grid;place-items:center;'
            'font-size:12px;font-weight:bold;flex:0 0 23px}'
            '.lf-k.dran .nr{background:var(--accent);color:#fff}'
            '.lf-k.fertig .nr{background:seagreen;color:#fff}'
            '.lf-satz{font-size:13.5px;color:var(--dim);margin:0}'
            '.lf-rest{margin-top:auto}'
            '.lf-saeule-w{display:flex;gap:12px;align-items:stretch;flex:1}'
            '.lf-saeule{width:32px;height:150px;border:1px solid var(--border);'
            'border-radius:8px;position:relative;overflow:hidden;'
            'background:var(--bg);flex:0 0 32px;align-self:flex-end}'
            '.lf-saeule .fuell{position:absolute;bottom:0;left:0;right:0;'
            'background:linear-gradient(180deg,var(--accent),seagreen)}'
            '.lf-saeule .marke{position:absolute;left:0;right:0;'
            'border-top:1px dashed var(--border)}'
            '.lf-phasen{display:flex;flex-direction:column-reverse;'
            'justify-content:space-between;font-size:12.5px;height:150px;'
            'align-self:flex-end;padding:2px 0}'
            '.lf-phasen div{display:flex;gap:6px;align-items:center;color:var(--dim)}'
            '.lf-phasen .an{color:var(--text);font-weight:bold}'
            '.lf-phasen .ok{color:seagreen}'
            '.lf-puls{display:inline-block;width:8px;height:8px;'
            'border-radius:50%;background:var(--accent);'
            'animation:lfpu 1.2s infinite}'
            '@keyframes lfpu{50%{opacity:.25}}'
            '.lf-q{display:flex;flex-wrap:wrap;gap:6px;margin:2px 0}'
            '.lf-q a{position:relative;display:block;width:44px;height:44px}'
            '.lf-q img{width:44px;height:44px;object-fit:cover;border-radius:8px;'
            'border:1px solid var(--border)}'
            '.lf-q .jetzt img{outline:2px solid var(--accent);outline-offset:2px}'
            '.lf-q .done::after{content:"\\2713";position:absolute;inset:0;'
            'display:grid;place-items:center;background:#1f7a5fd9;color:#fff;'
            'border-radius:8px;font-size:18px}'
            '.lf-q .skip::after{content:"\\2013";position:absolute;inset:0;'
            'display:grid;place-items:center;background:#555c66d9;color:#fff;'
            'border-radius:8px;font-size:18px}'
            '.lf-zw{background:var(--surface);border:1px solid var(--accent);'
            'border-radius:12px;box-shadow:0 0 0 1px var(--accent);'
            'padding:14px 16px;margin:0 0 16px}'
            '.lf-zw h3{margin:0 0 2px;font-size:16px}'
            '.lf-zwg{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 12px}'
            '.lf-zwg label{position:relative;display:block;cursor:pointer}'
            '.lf-zwg input{position:absolute;top:4px;left:4px;z-index:2}'
            '.lf-zwg img{width:84px;height:84px;object-fit:cover;border-radius:8px}'
            '.lf-zwg input:not(:checked)+img{opacity:.4}'
            '.lf-zwg input:checked+img{outline:2px solid var(--accent);'
            'outline-offset:2px}'
            # .258: Pfeil INS Bild gelegt (top statt bottom) — seit die
            # Grund-Zeile unter dem Bild haengt, ueberlappte er sie.
            '.lf-zwclip{position:absolute;right:4px;top:62px;font-size:11px;'
            'background:var(--surface);border-radius:4px;padding:0 4px;'
            'text-decoration:none}'
            # .257: Pruef-Rahmen — gut=seagreen (angehakt), Grenzfall=goldenrod
            # (abgehakt, wieder anhakbar wie im Bruecken-Overlay), raus
            # gedimmt mit Grund.
            '.lf-zwg .lf-neu input:checked+img{outline-color:seagreen}'
            '.lf-zwg .lf-grenz input:checked+img{outline-color:goldenrod}'
            '.lf-zwg .lf-grenz .lf-zwgrund{color:goldenrod}'
            '.lf-zwg .lf-dup img{opacity:.3}'
            '.lf-zwgrund{display:block;max-width:84px;font-size:10px;'
            'color:var(--dim);line-height:1.2;padding-top:2px}'
            '.lf-knoepfe{display:flex;gap:8px;flex-wrap:wrap;align-items:center}'
            # .258: gesperrter Take-Knopf (0 Haken) sieht auch gesperrt aus.
            '.lf-knoepfe button.gtb:disabled{opacity:.45;cursor:default;'
            'filter:grayscale(.6)}'
            # .259 (Mockup b_suchknopf, Variante A): grosser gruener
            # Suchknopf, Einstellungs-Popup, Delete rechtsbuendig rot umrandet.
            '.lf-such{display:block;width:100%;margin-top:auto;'
            'padding:13px 14px;font-size:15.5px;font-weight:600;'
            'border-radius:9px;cursor:pointer;text-align:center;'
            'background:var(--ok);border:1px solid var(--ok);'
            'color:var(--on-ink)}'
            '.lf-such small{display:block;font-weight:400;font-size:12px;'
            'opacity:.85;margin-top:2px}'
            '.lf-such:hover{filter:brightness(1.08)}'
            '.lf-deck{position:fixed;inset:0;background:#000a;display:none;'
            'place-items:center;z-index:9}'
            '.lf-pop{background:var(--surface);'
            'border:1px solid var(--border-strong,var(--border));'
            'border-radius:12px;padding:18px 20px;width:min(440px,92vw);'
            'box-shadow:0 12px 40px #000a;text-align:left;font-weight:400}'
            '.lf-pop h3{margin:0 0 4px}'
            '.lf-popz{margin:12px 0;font-size:14px;display:flex;'
            'align-items:center;gap:8px;flex-wrap:wrap}'
            '.lf-hint{color:var(--dim);font-size:12px;flex-basis:100%}'
            '.lf-popf{display:flex;gap:8px;margin-top:16px;'
            'align-items:center}'
            '.lf-spacer{flex:1}'
            # .271/.271b: Blickwinkel-Kaesten mit Rahmen + Legende
            '.lf-blickbox{border:1px solid var(--border-strong,var(--border));'
            'border-radius:10px;padding:6px 10px 10px;margin:10px 0}'
            '.lf-blickbox legend{font-weight:600;font-size:13px;'
            'padding:0 6px}'
            '.lf-blickbox.lf-leer{opacity:.6}'
            '.lf-del{background:transparent;border:1px solid var(--crit);'
            'color:var(--crit);border-radius:6px;padding:6px 12px;'
            'cursor:pointer}'
            '.lf-del:hover{background:var(--crit);color:#fff}'
            '</style>')
    # .223 (User 16.08.: "hier verlieren wir den User komplett — er weiss gar
    # nicht, was er wo klicken soll"): die EASY-Sicht ist ein gefuehrter Fluss
    # aus Schritt-Balken, EINEM Klartext-Satz und EINEM Knopf. Keine Anker-/
    # Cluster-/Harvest-Sprache; Phasen-Kette und Roh-Zaehler bleiben VOLL
    # erhalten, aber als Expert-Sicht (nur-expert — ausblenden, nie loeschen).
    # .246: vier Fluss-KACHELN statt Chip-Balken (Mockup-Abnahme); Reihung
    # der Gruppen = dieselbe wie der Benennungs-Fluss (Stuetz absteigend,
    # dann anker_id), damit Queue, Flaeche und Anker-Liste EINE Geschichte
    # erzaehlen. Zaehler-Formate: fs['event']='12/50', fs['rest']='~X min'
    # (verifyd-Ernte-Thread) — nur echte Werte, nichts erfinden.
    gruppen = gruppen or []
    wartend = sorted(
        (g for g in gruppen
         if g.get("status") not in ("uebernommen", "verworfen")),
        key=lambda g: (-(g.get("qualitaet") or {}).get("stuetz", 0),
                       str(g.get("anker_id"))))
    if reihenfolge:
        # .259 (Zielperson-Suche): der Handler hat die Queue nach Aehnlichkeit
        # zur Zielperson geordnet — Chips, aktuelle Gruppe und Skip-Ziel
        # erzaehlen dieselbe Reihenfolge (EINE Quelle: die Handler-Liste).
        _ri = {a: i for i, a in enumerate(reihenfolge)}
        wartend.sort(key=lambda g: _ri.get(g.get("anker_id"), len(_ri)))
    n_bilder = sum(len(g.get("mitglieder") or []) for g in gruppen)
    n_events = len({str(m.get("event")) for g in gruppen
                    for m in (g.get("mitglieder") or []) if m.get("event")})
    # .260: Saeule/Zeit/Zaehler kommen aus lauf_status — DERSELBEN Rechnung,
    # die der /lernlauf_status-Endpunkt dem Widget liefert (eine Quelle).
    s2 = lauf_status(zustand)
    ergebnis = ""
    if ph in ("vorbereitung", "ernte") or (ph == "anker" and not anker_fertig):
        ergebnis = s2["zaehler"]
    elif gruppen:
        ergebnis = (f"collected {n_bilder} picture{'s' if n_bilder != 1 else ''} "
                    f"from {n_events} recording{'s' if n_events != 1 else ''} · "
                    f"sorted into {len(gruppen)} "
                    f"group{'s' if len(gruppen) != 1 else ''}")
    fertig_alle = bool(anker_fertig and anker_zahl and gruppen and not wartend)
    laeuft = (ph in ("vorbereitung", "ernte")
              or (ph == "anker" and not anker_fertig))
    # --- Kachel-Zustaende (dran | fertig | folgt) -------------------------
    if zustand is None:
        kz = ("dran", "folgt", "folgt", "folgt")
    elif laeuft:
        kz = ("fertig", "dran", "folgt", "folgt")
    elif fertig_alle or ph in ("uebernahme", "fertig"):
        kz = ("fertig", "fertig", "fertig", "dran")
    else:                                  # Gruppen warten / keine Gesichter
        kz = ("fertig", "fertig", "dran", "folgt")

    def _kachel(nr, zust, titel, inhalt):
        mark = "&#10003;" if zust == "fertig" else str(nr)
        return (f'<div class="lf-k {zust}"><h3><span class="nr">{mark}</span>'
                f'{titel}</h3>{inhalt}</div>')

    # --- Suchknopf + Einstellungs-Popup (.259, Mockup-Abnahme b_suchknopf,
    # Variante A gruen): der EINE grosse Knopf am Kachel-Fuss oeffnet das
    # Popup mit Events-Zahl, Bilder/s und der Wahl alle-Gesichter/eine
    # Person; Start via app.js lernlaufPopupStart -> /lernlauf_start.
    _opts = "".join(f'<option>{html.escape(p)}</option>'
                    for p in (personen or []))
    _wen = ""
    if _opts:
        _wen = (
            '<div class="lf-popz">'
            '<label><input type="radio" name="lf-wen" checked '
            'onchange="document.getElementById(\'lf-ziel\').disabled=true"> '
            'All faces</label> '
            '<label><input type="radio" name="lf-wen" '
            'onchange="document.getElementById(\'lf-ziel\').disabled=false"> '
            'Only one person:</label> '
            f'<select id="lf-ziel" disabled>{_opts}</select>'
            '<span class="lf-hint">with one person chosen, matching groups '
            'are listed first &mdash; nothing is hidden</span></div>')
    such_knopf = (
        '<button class="lf-such" onclick="document.getElementById(\'lf-deck\')'
        '.style.display=\'grid\'">&#128269;&nbsp; Search events for faces'
        '<small>looks back through your recordings</small></button>')
    such_deck = (
        '<div id="lf-deck" class="lf-deck" '
        'onclick="if(event.target===this)this.style.display=\'none\'">'
        '<div class="lf-pop"><h3>Search events for faces</h3>'
        '<p class="lf-satz">Looks back through your recordings and collects '
        'faces. Day to day the system keeps learning on its own.</p>'
        # .263 Wechselschalter (User: 'einmal ein ganzer Tag, einmal x
        # Events'): letzte-N ODER ein Kalendertag; das jeweils inaktive
        # Feld ist gesperrt, app.js liest den aktiven Modus.
        '<div class="lf-popz"><label><input type="radio" name="lf-um" '
        'id="lf-um-n" checked onchange="lfUmschalten()"> '
        'Look back through the last</label> '
        f'<input id="lf-pop-n" type="number" min="1" max="{int(max_events)}" '
        f'value="{int(easy_events)}" style="width:6em"> events'
        f'<span class="lf-hint">how many recent recordings to check '
        f'(up to {int(max_events)})</span></div>'
        '<div class="lf-popz"><label><input type="radio" name="lf-um" '
        'id="lf-um-tag" onchange="lfUmschalten()"> One whole day:</label> '
        '<input id="lf-pop-tag" type="date" disabled>'
        '<span class="lf-hint">every recording of that day, however many '
        'there are</span></div>'
        '<script>function lfUmschalten(){'
        'var t=document.getElementById("lf-um-tag").checked;'
        'document.getElementById("lf-pop-n").disabled=t;'
        'document.getElementById("lf-pop-tag").disabled=!t;}</script>'
        '<div class="lf-popz"><input id="lf-pop-fps" type="number" min="1" '
        'max="30" step="0.5" value="3" style="width:5em"> pictures per second'
        '<span class="lf-hint">more pictures find more angles, but the '
        'search takes longer</span></div>'
        # .262 Fortsetzungs-Suche (User: '5 x 100 statt 1 x 500'): Haken an
        # = schon Durchsuchtes ueberspringen, jeder Lauf wandert weiter in
        # die Vergangenheit; Haken ab = die neuesten nochmal.
        '<div class="lf-popz"><label><input type="checkbox" id="lf-weiter" '
        'checked> Skip events already searched</label>'
        '<span class="lf-hint">each search continues further into the past '
        '&mdash; untick to search the newest events again</span></div>'
        + _wen +
        '<div class="lf-popf">'
        '<button class="gtb on" onclick="lernlaufPopupStart(this)">'
        'Start search</button>'
        '<button class="gtb" onclick="document.getElementById(\'lf-deck\')'
        '.style.display=\'none\'">Cancel</button>'
        '<span id="lf-pop-status" class="dim"></span></div></div></div>')

    # --- Kachel 1: der Lauf ----------------------------------------------
    if zustand is None:
        hinweis_u = ""
        if unbekannt_offen:
            hinweis_u = (f'<p class="lf-satz">{int(unbekannt_offen)} unknown '
                         f'visitor{"s" if unbekannt_offen != 1 else ""} from '
                         'today: <a href="/unbekannte">People &rarr; '
                         'Unknown</a></p>')
        # .246: an der Start-Stelle sagen, dass der Lauf nur fuer den Blick
        # ZURUECK noetig ist. .263 (User am Screenshot: 'vollgemuellt mit
        # Text'): auf EINEN Satz gekuerzt — der Leer-Zustand soll so schlank
        # aussehen wie die fertige Kachel.
        k1 = ('<p class="lf-satz">Only needed to look <b>back</b> &mdash; '
              'day to day the system learns on its own.</p>' + hinweis_u
              + '<div class="lf-rest">' + such_knopf + such_deck + '</div>')
    else:
        # .255/.259: der Neustart-Weg gehoert in die Kachel — seit .259 als
        # der EINE grosse Suchknopf mit Popup (Mockup-Abnahme), nur bei
        # abgeschlossenem Lauf (waehrend er laeuft, blockt der Server einen
        # Neustart ohnehin — Phasen-Wache).
        neu_form = ""
        if anker_fertig:
            neu_form = '<div class="lf-rest">' + such_knopf + such_deck + '</div>'
        k1 = (f'<div><span class="phok">&#10003;</span> Run started '
              f'{_dt(z.get("ts"))}</div>'
              + (f'<div class="lf-satz">{html.escape(ergebnis)}</div>'
                 if ergebnis and not laeuft else "")
              + f'<div class="lf-satz nur-expert">scope '
                f'{z.get("events", "?")} events'
                + (f' &middot; day {html.escape(str(z["tag"]))}'
                   if z.get("tag") else "") + '</div>'
              + neu_form)

    # --- Kachel 2: die Saeule --------------------------------------------
    # Ehrliche Fuellung (Regeln in lauf_status, EINE Quelle mit dem
    # Widget-Endpunkt): Vorbereitung 0-15 %, Ernte 15-85 % proportional zum
    # echten Event-Zaehler, Sortierung = 85 % mit Puls, fertig = 100 %.
    # .260: Zeit/Zaehler tragen IDs und werden waehrend des Laufs vom
    # Widget-JS in place nachgefuehrt (immer gerendert, ggf. leer).
    k2 = ('<p class="lf-satz">Runs on its own &mdash; you can close this '
          'page and come back.</p>'
          '<div class="lf-saeule-w"><div class="lf-saeule">'
          '<div class="marke" style="bottom:15%"></div>'
          '<div class="marke" style="bottom:85%"></div>'
          f'<div class="fuell" style="height:{s2["proz"]}%"></div></div>'
          f'<div class="lf-phasen">{"".join(_seg_html(sg) for sg in s2["seg"])}'
          '</div></div>'
          '<div class="lf-rest">'
          + (f'<div class="lf-satz" id="lf-zeit">{html.escape(s2["zeit"])}'
             '</div>' if s2["zeit"] or laeuft else "")
          + (f'<div class="lf-satz nur-expert" id="lf-zaehler">'
             f'{html.escape(ergebnis)}</div>' if laeuft else "")
          # .261 (User: 'ein Abbruch-Button waere auch nicht schlecht'):
          # direkt an der Saeule statt am Seitenende — derselbe
          # lernlaufAbbruch-Weg (app.js, mit Confirm).
          + ('<div style="margin-top:6px"><button class="gtb" '
             'onclick="lernlaufAbbruch(this)">Abort run</button></div>'
             if laeuft else "")
          + "</div>")

    # --- Kachel 3: die Gruppen-Queue -------------------------------------
    reihe = sorted(gruppen,
                   key=lambda g: (-(g.get("qualitaet") or {}).get("stuetz", 0),
                                  str(g.get("anker_id"))))
    akt_id = (aktuelle or {}).get("anker_id")
    qchips = []
    for g in reihe:
        aid_g = html.escape(str(g.get("anker_id")))
        lid_g = html.escape(str((g.get("lauf") or {}).get("lauf_id", "")))
        mg = sorted(g.get("mitglieder") or [],
                    key=lambda m: (-(m.get("det") or 0), str(m.get("datei"))))
        bild = ""
        if mg and lid_g:
            fn = html.escape(str(mg[0].get("datei", "")).rsplit("/", 1)[-1])
            bild = (f'<img src="/lernlauf/crop/{lid_g}/{fn}" '
                    'loading="lazy" alt="">')
        stg = g.get("status")
        cls = ("done" if stg == "uebernommen" else
               "skip" if stg == "verworfen" else
               "jetzt" if g.get("anker_id") == akt_id else "")
        ziel_g = (f'/lernlauf/anker?a={aid_g}'
                  if stg in ("uebernommen", "verworfen")
                  else f'/lernlauf?g={aid_g}')
        titel_g = html.escape(str(g.get("person")
                                  or f'{len(mg)} pictures'))
        qchips.append(f'<a class="{cls}" href="{ziel_g}" '
                      f'title="{titel_g}">{bild}</a>')
    offen_n = len(wartend)
    if zustand is None or laeuft:
        k3 = ('<p class="lf-satz">The only step that needs you: one group '
              'should be one person &mdash; say who it is, or skip it.</p>')
    elif anker_fertig and not anker_zahl:
        k3 = ('<p class="lf-satz">No new faces this time &mdash; nothing to '
              'name. That is fine: it just means the recordings held nobody '
              'new.</p><div class="lf-rest">'
              '<a class="gtb" href="/lernlauf?neu=1">Start a new run</a></div>')
    else:
        erledigt = len(gruppen) - offen_n
        k3 = ('<p class="lf-satz">'
              + ('The current group is open below, full width.'
                 if kz[2] == "dran" else 'All groups are handled.') + '</p>'
              # .259: Zielperson-Suche sichtbar machen — passende Gruppen
              # stehen vorn, nichts wird versteckt.
              + (f'<p class="lf-satz">looking for <b>{html.escape(zielperson)}'
                 '</b> &mdash; matching groups are listed first.</p>'
                 if zielperson else "")
              + f'<div class="lf-q">{"".join(qchips)}</div>'
              '<div class="lf-rest"><div class="lf-satz">'
              + (f'{erledigt} of {len(gruppen)} done'
                 + (' &mdash; the next one is ready.' if offen_n else '.')
                 if erledigt else
                 f'{offen_n} group{"s are" if offen_n != 1 else " is"} '
                 'waiting for you.')
              + (f' &middot; <b>{anker_kaputt} unreadable lines counted</b>'
                 if anker_kaputt else "")
              + '</div></div>')

    # --- Kachel 4: Bilanz -------------------------------------------------
    if kz[3] == "dran":
        if adoptiert and adoptiert.get("bilder"):
            _ab, _ap = adoptiert["bilder"], adoptiert.get("personen", 0)
            btxt = (f'<b>{_ab} picture{"s" if _ab != 1 else ""} adopted for '
                    f'{_ap} {"person" if _ap == 1 else "people"}</b> &mdash; '
                    'they count for recognition right away. '
                    # .273c: Kontext-Einstieg in den Bestands-Check direkt
                    # nach dem Hinzufuegen (User-Wunsch).
                    '<a href="/qualitaet">quality-check the library '
                    '&#8230;</a>')
        else:
            btxt = ("no new pictures were adopted this time (groups skipped "
                    "or already covered).")
        k4 = (f'<div><span class="phok">&#10003;</span> {btxt}</div>'
              '<p class="lf-satz">Repeat every few days, or let the day view '
              'top up known people in between.</p>'
              '<div class="lf-rest">'
              '<a class="gtb on" href="/faces">Back to Faces</a> '
              '<a class="gtb" href="/lernlauf?neu=1">Start a new run</a></div>')
    else:
        k4 = ('<p class="lf-satz">Named pictures become references and '
              'count for recognition right away.</p>')

    fluss = ('<div class="lf-fluss">'
             + _kachel(1, kz[0], "Learning run", k1)
             + _kachel(2, kz[1], "Collect &amp; sort", k2)
             + _kachel(3, kz[2], "Name the groups", k3)
             + _kachel(4, kz[3], "Done &mdash; they count", k4)
             + "</div>")

    # --- Zuweisungs-Flaeche (ganze Zeile, nur wenn eine Gruppe offen) -----
    zuweisung = ""
    if aktuelle is not None and benennung is not None and kz[2] == "dran":
        aid = html.escape(str(aktuelle.get("anker_id")))
        lid = html.escape(str((aktuelle.get("lauf") or {}).get("lauf_id", "")))
        # .266 'Sicht = Pruefergebnis' (User 18.08.: 'erst ein Schnellcheck,
        # welche Bilder wirklich gut sind, und DAVON die Anzeige'): die
        # Kacheln kommen aus der Crop-Sichtung — GUTE zuerst (angehakt),
        # Grenzfaelle dahinter (abgehakt, mit Grund), 'raus' erscheint
        # nicht; Deckel = zwei Reihen. Ohne Cache: checking-Zustand, das
        # JS stoesst die Sichtung an und laedt neu.
        ev_je = {str(m.get("datei", "")).rsplit("/", 1)[-1]:
                 str(m.get("event", ""))
                 for m in (aktuelle.get("mitglieder") or [])}
        sicht_zeile, sicht_warte, sicht_fehler = "", False, False
        if sichtung is False:
            # .267 (Widerleger): Render-FEHLER ist nicht 'kein Cache' — hier
            # nie die Sichtungs-/Reload-Schleife drehen, sondern es sagen.
            sicht_fehler = True
            kacheln = []
        elif sichtung is None:
            sicht_warte = True
            kacheln = []
        else:
            def _kachel_s(s, klasse, checked):
                fn = html.escape(str(s.get("datei", "")))
                ev = html.escape(ev_je.get(str(s.get("datei", "")), ""))
                grund = ("" if not s.get("grund") and klasse == "lf-neu" else
                         '<span class="lf-zwgrund">'
                         + html.escape(str(s.get("grund")
                                           or "picture quality only fair"))
                         + "</span>")
                return (f'<label class="{klasse}">'
                        f'<input type="checkbox" name="lfsel" value="{fn}"'
                        f'{" checked" if checked else ""} onchange="lfZaehl()">'
                        f'<img src="/lernlauf/crop/{lid}/{fn}" loading="lazy">'
                        f'<a class="lf-zwclip" href="/video/{ev}" '
                        f'title="open the clip">&#9654;</a>{grund}</label>')

            # .271 (User-Zielbild): DREI beschriftete Reihen nach
            # Blickwinkel — je Reihe die optimalen dieses Winkels (gut vor
            # Grenzfall vor Double, Deckel 12); nichts Gutes versteckt sich
            # woanders, der Aufklapper traegt nur Rest + Aussortierte.
            gute = [s for s in sichtung if s.get("stufe") == "gut"]
            grenz = [s for s in sichtung if s.get("stufe") == "grenzfall"]
            reihen_html, rest, zeige_n = [], [], 0
            for blick, label in (("links", "Looking left"),
                                 ("frontal", "Frontal"),
                                 ("rechts", "Looking right")):
                im = [s for s in sichtung
                      if (s.get("blick") or "frontal") == blick]
                gb = [s for s in im if s.get("stufe") == "gut"]
                zb = [s for s in im if s.get("stufe") == "grenzfall"]
                zb.sort(key=lambda s: bool(s.get("dup")))
                zeile = (gb + zb)[:12]
                rest += (gb + zb)[12:] + [s for s in im
                                          if s.get("stufe") == "raus"]
                zeige_n += len(zeile)
                if not zeile:
                    # .271b (User: Rahmen je Blickwinkel, 'dass jeder weiss,
                    # welche Bilder was sind und warum links drei, rechts
                    # fuenf'): auch die leere Reihe bekommt ihren Kasten.
                    reihen_html.append(
                        '<fieldset class="lf-blickbox lf-leer">'
                        f'<legend>{label}</legend><span class="dim">'
                        'no usable pictures of this angle in the group'
                        '</span></fieldset>')
                    continue
                ks = [_kachel_s(s, "lf-neu" if s.get("stufe") == "gut"
                                else "lf-grenz", s.get("stufe") == "gut")
                      for s in zeile]
                reihen_html.append(
                    '<fieldset class="lf-blickbox">'
                    f'<legend>{label} <span class="dim">({len(gb)} good, '
                    f'{len(zb)} borderline of {len(im)} checked)</span>'
                    f'</legend><div class="lf-zwg">{"".join(ks)}</div>'
                    '</fieldset>')
            kacheln_html = "".join(reihen_html)
            mehr = ""
            if rest:
                mk = [_kachel_s(s, "lf-grenz" if s.get("stufe") == "grenzfall"
                                else "lf-dup", False) for s in rest]
                mehr = (
                    '<button type="button" class="gtb" id="lf-mehr-knopf" '
                    'onclick="var m=document.getElementById(\'lf-mehr\');'
                    'var auf=m.style.display===\'none\';'
                    'm.style.display=auf?\'\':\'none\';'
                    f'this.textContent=auf?\'Hide the other {len(rest)} '
                    f'checked pictures\':\'Show all {len(sichtung)} checked '
                    'pictures\';lfZaehl();">'
                    f'Show all {len(sichtung)} checked pictures</button>'
                    f'<div class="lf-zwg" id="lf-mehr" style="display:none">'
                    + "".join(mk) + '</div>')
            pruef_wort = ("reference check" if aktuelle.get("person")
                          else "picture check")
            sicht_zeile = (
                f'<p class="lf-satz">{int(sichtung_gesamt)} pictures in this '
                f'group; checked the best {len(sichtung)}: '
                f'<b>{len(gute)}</b> pass the {pruef_wort}, '
                f'{len(grenz)} borderline'
                + (f' &mdash; showing the best {zeige_n}'
                   if len(gute) + len(grenz) > zeige_n else "")
                + '; the rest are near-duplicates or below the bar.</p>')
            if not zeige_n:
                sicht_zeile += ('<p class="lf-satz">nothing here passes the '
                                f'{pruef_wort} &mdash; skip or delete this '
                                'group.</p>')
        pos = len(gruppen) - len(wartend) + 1
        v = benennung.get("vorschlag")
        schon = aktuelle.get("status") == "benannt"
        opts = "".join(f'<option value="{html.escape(p)}">'
                       for p in (benennung.get("personen") or []))
        hin = ""
        if v:
            _bek = ("already in your system" if {"referenz", "master"}
                    & set(v.get("quellen") or []) else
                    "named on another cluster")
            hin = (f'<p class="lf-satz">looks like <b>{html.escape(v["name"])}'
                   f'</b> (similarity {v["sim"]}) &mdash; {_bek}; suggestion '
                   'only.</p>')
        if schon:
            hin += (f'<p class="lf-satz">named <b>'
                    f'{html.escape(str(aktuelle.get("person")))}</b> &mdash; '
                    'adoption pending.</p>')
        skip_ziel = (f'/lernlauf?g={html.escape(str(naechste_id))}'
                     if naechste_id else "/lernlauf")
        if schon:
            ja = (f'<button type="button" class="gtb on" id="lf-adopt" '
                  f'data-person="{html.escape(str(aktuelle.get("person") or ""), quote=True)}">'
                  f'Adopt as {html.escape(str(aktuelle.get("person")))}'
                  '</button>')
        elif v:
            ja = (f'<button type="button" class="gtb on" id="lf-ja" '
                  f'data-name="{html.escape(v["name"], quote=True)}">'
                  f'Yes, it&rsquo;s {html.escape(v["name"])}</button>')
        else:
            ja = ""
        benenn_aktiv = True
        if sicht_fehler:
            mitte = ('<div class="lf-satz">&#9888; the picture check could '
                     'not run (see /log) &mdash; reload to retry; Skip and '
                     'Delete still work.</div>')
            benenn_aktiv = False
        elif sicht_warte:
            mitte = ('<div class="lf-satz" id="lf-sicht-warte">&#9203; '
                     'checking this group&rsquo;s pictures against the '
                     'reference bar &mdash; a few seconds &hellip;</div>'
                     + _SICHT_JS)
            benenn_aktiv = False
        else:
            mitte = kacheln_html + mehr + sicht_zeile
        if not benenn_aktiv:
            # .267 (Widerleger): im Warte-/Fehlerzustand ALLE Benenn-Wege
            # sperren — 'Someone else' haette sonst eine LEERE Auswahl
            # persistiert; Skip und Delete bleiben.
            ja = ""
        zuweisung = (
            f'<div class="lf-zw" id="lf-zw" data-aid="{aid}">'
            f'<h3>Group {pos} of {len(gruppen)} &mdash; who is this?</h3>'
            '<p class="lf-satz">One group should be one person. Tap a '
            'picture to leave it out &mdash; then say who it is, or skip '
            'the group.</p>' + hin
            + mitte
            + '<div class="lf-knoepfe" id="lf-knopfzeile-1">' + ja
            + (('<button type="button" class="gtb" id="lf-andere">'
                'Someone else &#8230;</button>'
                '<input type="text" id="lf-name" list="lf-personen" '
                'placeholder="person name (new or existing)" '
                'style="display:none" '
                f'value="{html.escape(str(aktuelle.get("person") or ""))}">'
                f'<datalist id="lf-personen">{opts}</datalist>'
                '<button type="button" class="gtb on" id="lf-save" '
                'style="display:none">Save name</button>')
               if benenn_aktiv else "")
            + f'<a class="gtb" href="{skip_ziel}">Skip this group</a>'
            # .259 (User: 'der Knopf delete the group fehlt'; Mockup-Abnahme
            # Variante A): Verwerfen mit Gedaechtnis, rechtsbuendig abgesetzt
            # in ruhiger roter Umrandung — derselbe ankerVerwerfen-Weg
            # (app.js) wie auf der Anker-Seite, mit Bestaetigung.
            + '<span class="lf-spacer"></span>'
            + f'<button type="button" class="lf-del" '
              f'onclick="ankerVerwerfen(\'{aid}\',this)" '
              'data-frage="Delete this group? Its pictures are removed and a '
              'pending naming is discarded; the group is remembered so '
              're-harvests of the same events stay quiet.">'
              'Delete this group</button></div>'
            # .256: zweite Knopfzeile — erscheint NACH der Pruefung, mit der
            # ehrlichen Zahl auf dem Knopf; Cancel laedt neu (Auswahl-Reset).
            + '<div class="lf-knoepfe" id="lf-knopfzeile-2" '
              'style="display:none">'
              '<button type="button" class="gtb on" id="lf-take"></button>'
              '<button type="button" class="gtb" id="lf-cancel">Cancel'
              '</button></div>'
            + '<div class="lf-knoepfe"><span id="lf-status" class="dim">'
              '</span><span class="lf-satz" id="lf-zaehl" '
              'style="margin-left:auto"></span></div>'
            + '<div class="lf-satz nur-expert" style="margin-top:6px">'
              f'<a href="/lernlauf/anker?a={aid}">full detail view</a> '
              '(all pictures with reasons, expert selection)</div>'
            + '</div>' + _ZW_JS)
    easy = fluss + zuweisung
    # Seiten-Kopf: Titel + der eine Erklaer-Satz + Anleitung (ek-hilfe wie
    # auf den Kacheln — .244-Vertrag bleibt).
    # .255 (User am Screenshot): der Erklaer-Satz kostete nur Platz — weg.
    kopf = ('<h2>Learning run</h2>'
            '<div class="ek-hilfe"><a href="/hilfe/faces_lernlauf">'
            'How it works &#8230;</a></div>')
    if zustand is None:
        # Kein Lauf: nur der Fluss (Kachel 1 aktiv); der volle Planer haengt
        # als nur-expert dahinter (Handler-Komposition, Wizard bleibt Expert).
        return stil + kopf + easy
    # .88: den Nutzer ZUM ERGEBNIS fuehren — ohne diesen Block wuesste
    # niemand, dass die Bilder unter Anchors liegen.
    erfolg = ""
    if anker_fertig and anker_zahl:
        erfolg = (f'<div class="card"><b><span class="phok">&#10003;</span> Grouping done</b> '
                  f'— {anker_zahl} face cluster{"s" if anker_zahl != 1 else ""} ready: '
                  f'<a class="gtb on" href="/lernlauf/anker">View the anchor clusters</a> '
                  f'<span class="dim">open a cluster to name it</span></div>')
    # .223/.246: der Fluss fuehrt fuer BEIDE Sichten (Expert = Easy plus
    # Details); Erfolgs-Banner, Phasen-Kette und Progress sind Expert-Tiefe.
    return (stil + kopf + easy
            + f'<div class="nur-expert">{erfolg}'
            + f'<div class="card"><b>Phases</b>{"".join(zeilen)}'
            '<div class="dim">Preparation, Harvest, Grouping, Naming and adoption into '
            "the master run for real in this build — side views and the full-body "
            "stock activate with the coming updates.</div></div>"
            f'<div class="card"><b>Progress</b>'
            f'<div>{html.escape(st) if st else "—"}</div>{puls}{rest_html}'
            f'<div class="dim">anchors so far: {anker_zahl}{anker_link}{kaputt_html} · created '
            f'{_dt(z.get("ts"))} · scope {z.get("events", "?")} events · '
            "survives restarts (resume built in)</div></div></div>"
            + ('<p class="nur-expert"><a class="gtb" href="/lernlauf?neu=1">'
               'Start a new run</a> '
               '<span class="dim">this run stays — its anchors remain available</span></p>'
               if anker_fertig else "")   # .261: Abort wohnt jetzt in Kachel 2
            + (_WIDGET_JS if s2["tickt"] else ""))
