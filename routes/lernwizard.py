"""routes/lernwizard — der Anlern-Assistent + Lauf-Seiten-Geruest (E1 Baustein 4b,
seit E2 mit ECHTER Vorbereitung+Ernte; Konzept §P0/§2b/§4). Die Phasen ab
Gruppierung (E3) sind weiter Geruest und sagen das ehrlich.
Kontrakt wie alle routes-Module: reine Renderer, Daten als Parameter, kein
Dienst-Import; Seiteneffekte (Events holen, Messung anstossen, Lauf anlegen)
macht der Handler.

Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py — u. a. bleiben die drei JS-Bloecke,
der JS-gekoppelte Mehr-Knopf, die sicht_zeile mit pruef_wort (qs.sh-.257-
Anker) und die Inline-Markup-Saetze literal. PHASEN_TEXT wurde zu
_phasen_text() (§8.12: t() nie auf Modulebene, Muster live.py)."""
import datetime
import html
import json

from core.lernlauf import PHASEN
from core.sprache import t, t_n
from webui.bausteine import js_literal, lauffluss_stil


def _phasen_text():
    """Anzeige-Reihenfolge + Klartext je Phase — Funktion statt Konstante
    (t() zur Render-Zeit, damit die Sprachwahl nicht am Import friert)."""
    return {
        "vorbereitung": t("lernwizard.phase.vorbereitung"),
        "ernte": t("lernwizard.phase.ernte"),
        "anker": t("lernwizard.phase.anker"),
        "benennung": t("lernwizard.phase.benennung"),
        "neben_ansichten": t("lernwizard.phase.neben_ansichten"),
        "ganzkoerper": t("lernwizard.phase.ganzkoerper"),
        "uebernahme": t("lernwizard.phase.uebernahme"),
        "fertig": t("lernwizard.phase.fertig"),
    }


def _dt(ts):
    # §8.9: Datumsformat bleibt in der Route (B19-Stufe).
    return datetime.datetime.fromtimestamp(ts).strftime("%a %d.%m. %H:%M") if ts else "—"


def _dauer(s):
    s = int(round(max(s, 0)))
    return (t("lernwizard.dauer.lang", m=s // 60, s=s % 60) if s >= 60
            else t("lernwizard.dauer.kurz", s=s))


def wizard(personen_zahl, auswahl, bilanz, prognose, quelle, schwellen,
           messung_laeuft=False, gemessen_felder=(), alle=False, bestaetigen_ab=1000,
           max_events=40000, mess_wartet=False, mess_skip="", unbekannt_offen=0):
    """Wizard-Ansicht. auswahl = Event-Zahl (int) oder None; alle=True bei ?events=alle;
    quelle 'gemessen'|'rueckfall' + gemessen_felder = WIRKLICH gemessene Konstanten
    (Teil-Kennung, Widerleger F3.1); bestaetigen_ab: ab dieser Zahl verlangt der
    Start-Knopf den Bestaetigungs-Dialog MIT den Schaetz-Zahlen (User-Wunsch 3);
    unbekannt_offen = wartende Unbekannt-Cluster von heute (core/unbekanntpool,
    dieselbe Quelle wie die Today-Kachel — Baustein B 12.08.)."""
    lage = (t("lernwizard.wizard.lage_b")
            if personen_zahl else t("lernwizard.wizard.lage_a"))
    teile = [f'<h2>{t("lernwizard.wizard.titel")}</h2>',
             # .200 (Fix 4): "ships in the next updates" war seit E4b falsch und
             # widersprach der Phasen-Karte weiter unten auf derselben Seite.
             f'<p class="sub">{t("lernwizard.wizard.satz")}</p>']
    if unbekannt_offen:
        # Baustein B (12.08., Realfall Besuch): der Querverweis, der fehlte — ein
        # Lernlauf ist fuer heutige unbekannte Besucher gar nicht noetig, ihre
        # Gesichter liegen schon gesammelt unter People -> Unknown.
        # Echter Plural (is/are) — t_n; der Link im <b>-Satz bleibt als
        # Markup-Grenze literal, sein Text ist Schluessel.
        teile.append(
            '<div class="card"><span class="badge warn">'
            + t("lernwizard.badge.unbekannt") + '</span> '
            '<b>' + t_n("lernwizard.wizard.unbekannt_wartend",
                        int(unbekannt_offen)) + ' '
            '<a href="/unbekannte">' + t("lernwizard.link_unbekannte")
            + '</a></b>'
            f'<div class="dim">{t("lernwizard.wizard.unbekannt_hinweis")}'
            '</div></div>')
    teile.append(
             f'<div class="card"><b>{t("lernwizard.wizard.start_titel")}</b>'
             f'<div>{html.escape(lage)}</div>'
             f'<div class="dim">{t("lernwizard.wizard.start_hinweis")}'
             '</div></div>')
    knoepfe = "".join(
        f'<a class="gtb{" on" if (auswahl == n and not alle) else ""}" '
        f'href="/lernlauf?events={n}">{t("lernwizard.wizard.knopf_letzte", n=n)}</a> '
        for n in (100, 300, 1000))
    knoepfe += (f'<a class="gtb{" on" if alle else ""}" href="/lernlauf?events=alle">'
                f'{t("lernwizard.wizard.knopf_alle")}</a>')
    eigen = ('<form action="/lernlauf" method="get" style="display:inline;margin-left:10px">'
             f'<input name="events" type="number" min="1" max="{int(max_events)}" size="6" '
             f'value="{auswahl if (auswahl and not alle) else ""}" '
             f'placeholder="{t("lernwizard.wizard.attr_eigen")}"> '
             f'<button class="gtb">{t("lernwizard.wizard.knopf_go")}</button></form>')
    teile.append(f'<div class="card"><b>{t("lernwizard.wizard.scope_titel")}</b>'
                 f'<div>{knoepfe}{eigen}</div>'
                 f'<div class="dim">{t("lernwizard.wizard.scope_hinweis")}'
                 '</div></div>')
    if auswahl and bilanz:
        b = bilanz
        # Zaehler-Anhang im <b> (§8.10/§8.11): Split an der Markup-Grenze.
        teile.append(
            f'<div class="card"><b>{t("lernwizard.wizard.auswahl_titel")}</b>'
            '<div>'
            + t("lernwizard.wizard.auswahl_zeile", n=b["n"],
                wann=_dt(b["aeltester_ts"]), clips=b["mit_clip"])
            + (' — <b>'
               + t("lernwizard.wizard.auswahl_ohne_clip", n=b["ohne_clip"])
               + '</b>' if b["ohne_clip"] else "")
            + (('<br>' + t("lernwizard.wizard.auswahl_durchsucht", k=b["durchsucht"], n=b["n"]))
               if b.get("durchsucht") else "") + "</div>"
            f'<div class="dim">{t("lernwizard.wizard.auswahl_hinweis")}'
            '</div></div>')
        if prognose:
            if quelle == "gemessen":
                q = (t("lernwizard.wizard.q_teilgemessen") if gemessen_felder
                     else t("lernwizard.wizard.q_gemessen"))
            else:
                # Pflichtpunkt .172: Skip und Warten ehrlich benennen — "measuring
                # now" waere in beiden Faellen gelogen (K1, falsche Darstellung).
                # Konditionale Annotations-Anhaenge (§8.11): eigene Schluessel.
                if mess_skip:
                    zusatz = t("lernwizard.wizard.q_skip", grund=mess_skip)
                elif mess_wartet:
                    zusatz = t("lernwizard.wizard.q_wartet")
                elif messung_laeuft:
                    zusatz = t("lernwizard.wizard.q_laeuft")
                else:
                    zusatz = ""
                q = t("lernwizard.wizard.q_rueckfall") + zusatz
            teile.append(
                f'<div class="card"><b>{t("lernwizard.wizard.dauer_titel")}</b>'
                f' <span class="dim">({html.escape(q)})</span>'
                '<div>'
                + t("lernwizard.wizard.dauer_zeile",
                    analyse=_dauer(prognose["analyse_s"]),
                    download=_dauer(prognose["download_s"]),
                    kalt=_dauer(prognose["kalt_s"]))
                + ' → <b>'
                + t("lernwizard.wizard.dauer_gesamt",
                    gesamt=_dauer(prognose["gesamt_s"]))
                + '</b></div></div>')
        s_html = "".join(f'<span class="dim" style="margin-right:10px">{html.escape(k)}='
                         f'{html.escape(str(v))}</span>' for k, v in (schwellen or []))
        teile.append(f'<div class="card"><b>{t("lernwizard.wizard.schwellen_titel")}</b>'
                     f'<div>{s_html or "—"}</div></div>')
        # Bestaetigungs-Dialog (User-Wunsch 3): bei ALLE oder grossem N traegt der
        # Knopf die ECHTEN Schaetz-Zahlen als data-Attribut — app.js zeigt sie im confirm.
        n_start = bilanz["n"]
        frage = ""
        if prognose and (alle or n_start >= bestaetigen_ab):
            frage = t("lernwizard.wizard.frage", n=n_start,
                      gesamt=_dauer(prognose["gesamt_s"]),
                      analyse=_dauer(prognose["analyse_s"]),
                      download=_dauer(prognose["download_s"]))
        # .90 (Task #11, Benchmark am eigenen Tuerkamera-Clip): PROMINENTE Abfrage
        # der Abtastrate als eigene Wizard-Karte, mit gemessener Abwaegung und live
        # mitskalierender Dauer-Schaetzung (app.js llFpsUpdate; Analyse-Anteil ~linear).
        p = prognose or {}
        # Stufe-0-Grenze: der Erklaertext traegt <b>3</b>/s-Inseln mitten
        # im Satz (§8.1) — bleibt literal.
        teile.append(
            f'<div class="card"><b>{t("lernwizard.wizard.fps_titel")}</b>'
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
                     f'{t("lernwizard.wizard.knopf_start")}</button>'
                     ' <span id="ll-status" class="dim"></span></p>')
    return "".join(teile)


# .88/V3: welcher Fortschritts-Schluessel gehoert zu welcher Phase (Anzeige-Gruppierung).
# Stufe-0-Grenze (§8.2): die Eintraege sind KEYS des fortschritt-Dicts
# (Kennungen, vom Ernte-Thread geschrieben) — keine Anzeige-Schluessel.
_PHASEN_KEYS = {
    "vorbereitung": ("checking events", "already searched (skipped)"),
    "ernte": ("event", "analysing", "rest", "with clip", "skipped (no clip)",
              "candidates", "crop-worthy (M)", "anchor-ready (S)",
              "filtered early (size/sharpness)",
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
# Stufe 2 Tranche D (§8.4): Funktion statt Konstante (§8.12) — die JS-Texte
# kommen server-seitig via json.dumps(t(...)) BYTE-TREU in den Script-Text
# (ensure_ascii=True reproduziert die \uXXXX-Escapes des Originals).
# Zaehler-/Fragment-Splits an den Konkatenationsgrenzen sind deklariert
# (en.py-Abschnitt Tranche D). Stufe-2-Grenze (§8.18): der Take-Knopf
# ("Take N picture(s) for X") und die Pruef-Bilanz ("N good for X, …")
# bauen Laufzeit-Plural + Name im Browser zusammen — bleibt literal bis
# zum bewussten Ganz-Satz-Umbau (JS-Template, Byte-Aenderung).
def _zw_js():
    return (
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
    'n+' + json.dumps(t("lernwizard.zw.js_zaehl_mitte")) + '+a+'
    + json.dumps(t("lernwizard.zw.js_zaehl_nach")) + ';};'
    'lfZaehl();'
    'function adoptieren(best){melden('
    + json.dumps(t("lernanker.js.uebernimmt")) + ');'
    'fetch("/lernlauf/uebernehmen",{method:"POST",'
    'headers:{"Content-Type":"application/json"},'
    'body:JSON.stringify({anker_id:AID,bestaetigt:best})})'
    '.then(function(r){return r.json()}).then(function(d){'
    'if(d.tag_abweichung){if(confirm('
    + json.dumps(t("lernanker.js.tag_frage_vor")) + '+'
    'd.tag_abweichung.join("\\n")+'
    + json.dumps(t("lernanker.js.tag_frage_nach"))
    + '))adoptieren(true);else melden('
    + json.dumps(t("lernanker.js.nicht_uebernommen")) + ');return;}'
    'if(!d.ok){melden(' + json.dumps(t("lernanker.js.fehler") + " ")
    + '+d.msg);return;}'
    'melden(' + json.dumps(t("lernanker.js.weiter")) + ');'
    'setTimeout(function(){location="/lernlauf"},500);})'
    '.catch(function(e){melden(' + json.dumps(t("lernanker.js.fehler") + " ")
    + '+e);});}'
    'function takeText(name){'
    'var n=document.querySelectorAll(".lf-zwg input:checked").length,'
    'tk=document.getElementById("lf-take");'
    'tk.textContent="Take "+n+" picture"+(n==1?"":"s")+" for "+name;'
    'tk.disabled=!n;}'
    'function pruefen(name){NAME=name;'
    'melden(' + json.dumps(t("lernwizard.zw.js_gespeichert_vor"))
    + '+name+' + json.dumps(t("lernwizard.zw.js_gespeichert_nach")) + ');'
    'fetch("/lernlauf/benenn_pruefung",{method:"POST",'
    'headers:{"Content-Type":"application/json"},'
    'body:JSON.stringify({anker_id:AID})})'
    '.then(function(r){return r.json()}).then(function(d){'
    'if(!d.ok){melden(' + json.dumps(t("lernanker.js.fehler") + " ")
    + '+d.msg);return;}'
    'if(d.laden){melden(d.msg);'
    # .311: Balken auch in der Benenn-Pruefung (gleiche Warte-Antwort).
    'if(d.zustand&&window.ladeBalken)ladeBalken(st,d.i,d.n,d.zustand);'
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
    '.catch(function(e){melden(' + json.dumps(t("lernanker.js.fehler") + " ")
    + '+e);});}'
    'function senden(name,best,dann){var sel=[];'
    'document.querySelectorAll(".lf-zwg input:checked")'
    '.forEach(function(b){sel.push(b.value);});'
    'melden(' + json.dumps(t("lernanker.js.speichert")) + ');'
    'fetch("/lernlauf/benennen",{method:"POST",'
    'headers:{"Content-Type":"application/json"},'
    'body:JSON.stringify({anker_id:AID,person:name,gewaehlt:sel,'
    'bestaetigt:!!best})})'
    '.then(function(r){return r.json()}).then(function(d){'
    'if(d.kollision){if(confirm(' + json.dumps(t("lernanker.js.koll_vor"))
    + '+name+' + json.dumps(t("lernanker.js.koll_mitte"))
    + '+d.kollision+' + json.dumps(t("lernanker.js.koll_nach")) + '))'
    'senden(d.kollision,true,dann);else melden('
    + json.dumps(t("lernanker.js.nicht_gespeichert")) + ');return;}'
    'if(!d.ok){melden(' + json.dumps(t("lernanker.js.fehler") + " ")
    + '+d.msg);return;}'
    'dann(d.person||name);})'
    '.catch(function(e){melden(' + json.dumps(t("lernanker.js.fehler") + " ")
    + '+e);});}'
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
# Stufe 2 Tranche D (§8.4): Funktion statt Konstante (§8.12); der Fallback-
# Text kommt via json.dumps(t(...), ensure_ascii=False) byte-treu (das
# Original traegt den Gedankenstrich roh). Das "⏳ "-Praefix ist ein
# Symbol, keine Sprache — bleibt Code.
def _sicht_js():
    return (
    '<script>(function(){'
    'var aid=document.getElementById("lf-zw").getAttribute("data-aid");'
    'function los(){'
    'fetch("/lernlauf/sichtung",{method:"POST",'
    'body:JSON.stringify({anker_id:aid})})'
    '.then(function(r){return r.json()})'
    '.then(function(d){'
    'if(d.laden){var w=document.getElementById("lf-sicht-warte");'
    # .311: refcache-Neuaufbau meldet i/n/zustand — schmaler Balken + Zaehler
    # hinter dem Text (ladeBalken, app.js); Balken NUR im selben Zweig wie der
    # Text-Reset (textContent raeumt den vorigen Balken ab — sonst stapelte
    # jeder Poll einen weiteren an).
    'if(w&&d.msg){w.textContent="\\u23f3 "+d.msg;'
    'if(d.zustand&&window.ladeBalken)ladeBalken(w,d.i,d.n,d.zustand);}'
    'setTimeout(los,1200);return;}'
    'if(!d.ok){var w2=document.getElementById("lf-sicht-warte");'
    'if(w2)w2.textContent=d.msg||'
    + json.dumps(t("lernwizard.sicht.js_fehl"), ensure_ascii=False)
    + ';return;}'
    'location.reload();'
    '}).catch(function(){setTimeout(los,3000);});}'
    'los();})();</script>')


def lauf_status(zustand, puls=None):
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
    for i_s, lbl in ((0, t("lernwizard.seg.vorbereiten")),
                     (1, t("lernwizard.seg.sammeln")),
                     (2, t("lernwizard.seg.sortieren"))):
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
            zeit = t("lernwizard.status.laeuft_seit",
                     dauer=_dauer(max(0, datetime.datetime.now().timestamp()
                                      - z["ts"])))
            if f.get("rest"):
                zeit += " · " + t("lernwizard.status.rest", rest=f["rest"])
        elif akt and akt > z["ts"]:
            zeit = t("lernwizard.status.fertig_in",
                     dauer=_dauer(akt - z["ts"]))
    # .345 (User-Konsens 25.08., ersetzt die .344-Zaehler-TEXTZEILE): die drei
    # Unterbalken des Fortschritts-Blocks, render-fertig. Die Werte kommen aus
    # ernte.fortschritt_rechnen — DERSELBEN Quelle wie am Pass-Check; hier
    # kommen nur Uebersetzung und Zustands-Woerter dazu, das Widget-JS wendet
    # an und rechnet nichts (kein Zweit-Rechner). Zustaende je Zeile:
    # 'ok' = Ernte komplett durch (Haken), 'an' = tickt, '' = wartet/Clip.
    from core.ernte import fortschritt_rechnen
    fertig_alle = zustand is not None and idx > 1     # anker oder spaeter
    fs = fortschritt_rechnen(0, 1, puls if ph == "ernte" else None) or {}
    gr = {g["k"]: g for g in fs.get("gruppen") or []}
    balken = []
    for k, lbl in (("suchen", t("lernwizard.balken.suchen")),
                   ("pose", t("lernwizard.balken.pose")),
                   ("erkennen", t("lernwizard.balken.erkennen"))):
        g = gr.get(k) or {}
        if fertig_alle:
            b_proz, b_zust, b_zt = 100, "ok", t("lernwizard.balken.fertig")
        elif ph == "ernte" and fs.get("puls_da"):
            b_proz = int(round(100 * (g.get("anteil") or 0)))
            wert = int(g.get("wert") or 0)
            if k == "suchen":
                b_zust, b_zt = "an", t("lernwizard.balken.z_frames",
                                       f=wert, s=g.get("von") or "?")
            elif not wert:
                b_zust, b_zt = "", t("lernwizard.balken.wartet")
            elif k == "pose":
                b_zust, b_zt = "an", t_n("lernwizard.balken.z_posen", wert)
            else:
                b_zust, b_zt = "an", t_n("lernwizard.balken.z_erkannt", wert)
        elif ph == "ernte":
            # laufende Ernte ohne frischen Puls = Clip-Beschaffung zwischen
            # zwei Events (fortschritt_rechnen: puls_da) — sagen, nicht einfrieren.
            b_proz, b_zust = 0, ""
            b_zt = (t("lernwizard.balken.clip") if k == "suchen"
                    else t("lernwizard.balken.wartet"))
        else:
            b_proz, b_zust, b_zt = 0, "", t("lernwizard.balken.wartet")
        balken.append({"label": lbl, "proz": b_proz, "zust": b_zust,
                       "zaehler": b_zt})
    teile_z = []
    if laeuft:
        if f.get("event"):
            teile_z.append(t("lernwizard.status.aufnahmen", n=f["event"]))
        if f.get("candidates") is not None:
            teile_z.append(t("lernwizard.status.bilder", n=f["candidates"]))
    tickt = zustand is not None and (
        (ph in ("vorbereitung", "ernte")
         and (not st or st.startswith(("prepared", "harvesting", "waiting"))))
        or (ph == "anker"
            and not st.startswith(("anchors", "anchor stage failed"))))
    return {"proz": proz, "seg": seg, "balken": balken, "zeit": zeit,
            "zaehler": " · ".join(teile_z),
            "laeuft": bool(laeuft), "tickt": bool(tickt)}


def _seg_html(sg):
    m = ('<span class="phok">&#10003;</span>' if sg["zust"] == "ok" else
         ('<span class="lf-puls"></span>' if sg["zust"] == "an" else
          '<span class="dim">&#183;</span>'))
    return f'<div class="{sg["zust"]}">{m} {sg["label"]}</div>'


def _balken_html(sb):
    """.345: EINE Unterbalken-Zeile des Fortschritts-Blocks (Kachel 2) — das
    Widget-JS fuehrt Breite/Zaehler/Zustand an genau diesem Geruest nach
    (Spiegel-Paar wie _seg_html/mark; Klassen .fs-* aus style.css)."""
    ok = sb["zust"] == "ok"
    return (f'<div class="fs-row"><div class="fs-kopf"><span class="fs-lbl">'
            f'{html.escape(sb["label"])}</span>'
            f'<span class="fs-z{" ok" if ok else ""}">'
            + ('&#10003; ' if ok else '')
            + f'{html.escape(sb["zaehler"])}</span></div>'
            f'<span class="fs-bar"><span class="fs-fill" '
            f'style="width:{sb["proz"]}%"></span></span></div>')


# .260: das Saeule-Widget — pollt /lernlauf_status alle 3 s und bewegt NUR
# Saeule/Marken/Zeit/Zaehler (kein Flackern, kein Scroll-Sprung); wechselt
# der Lauf in die Benennung (tickt->False), laedt es genau EINMAL voll neu.
# mark() spiegelt _seg_html — beide bauen aus denselben lauf_status-Werten.
# Sprach-Pruefung Tranche D: das Widget traegt KEINE Sprache — die
# \u-Escapes sind Symbole (Haken/Punkt), Zeit-/Zaehlerzeile kommen fertig
# uebersetzt aus lauf_status(); nichts einzuziehen.
_WIDGET_JS = (
    '<script>(function(){'
    'function mark(z){return z=="ok"?\'<span class="phok">\\u2713</span>\':'
    '(z=="an"?\'<span class="lf-puls"></span>\':'
    '\'<span class="dim">\\u00b7</span>\');}'
    'var t=setInterval(function(){'
    'fetch("/lernlauf_status").then(function(r){return r.json()})'
    '.then(function(d){if(!d.ok)return;'
    'if(!d.tickt){clearInterval(t);location.reload();return;}'
    # .345: Gesamtbalken (waagerecht) + drei Unterbalken statt der Saeule —
    # nur Werte anwenden, das Geruest rendert _balken_html (Spiegel-Paar).
    'var fu=document.querySelector("#lf-fsb>.fs-total>.fs-fill");'
    'if(fu)fu.style.width=d.proz+"%";'
    'var seg=document.querySelectorAll("#lf-fsb .fs-phasen>div");'
    'd.seg.forEach(function(s,i){var el=seg[i];if(!el)return;'
    'el.className=s.zust;el.innerHTML=mark(s.zust)+" "+s.label;});'
    'var rows=document.querySelectorAll("#lf-fsb .fs-row");'
    '(d.balken||[]).forEach(function(b,i){var el=rows[i];if(!el)return;'
    'var bf=el.querySelector(".fs-bar>.fs-fill");'
    'if(bf)bf.style.width=b.proz+"%";'
    'var zz=el.querySelector(".fs-z");if(zz){'
    'zz.className="fs-z"+(b.zust=="ok"?" ok":"");'
    'zz.textContent=(b.zust=="ok"?"\\u2713 ":"")+b.zaehler;}});'
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
               sichtung=None, sichtung_gesamt=0, ernte_puls=None):
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
            puls = ('<div class="dim">&#9679; '
                    + t("lernwizard.puls.working", s=alter) + '</div>'
                    if alter <= 60 else
                    '<div class="dim">&#9888; '
                    + t("lernwizard.puls.stumm", s=alter) + '</div>')
    f = z.get("fortschritt") or {}
    st = str(f.get("status", ""))
    # Alt-Laeufe tragen den vor-E4a-Statustext im State — nur die ANZEIGE mappt
    # ihn auf den neuen Stand, die Datei bleibt unangetastet.
    # Stufe-0-Grenze (§8.2): beide Seiten des replace sind GESPEICHERTE
    # Statuswerte (Kennungen) — bleiben literal.
    st = st.replace("naming ships with the next update", "open a cluster to name it")
    # .88 / V3: Zaehler JE PHASE gruppiert unter ihrer Phasen-Zeile — jede
    # Phase zaehlt ihre eigenen Zahlen hoch und bekommt beim Abschluss den gruenen
    # Haken; die alte Misch-Kette ("anchors" hinter 13 Ernte-Zaehlern) entfaellt.
    idx = PHASEN.index(ph) if ph in PHASEN else 0
    anker_fertig = ph == "anker" and st.startswith(("anchors ready", "anchors: none"))
    zeilen = []
    ptxt = _phasen_text()
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
            name_link = (' <a href="/lernlauf/anker">'
                         + t("lernwizard.phase.link_benennen") + '</a>')
        zeilen.append(f'<div class="phz">{mark} {html.escape(ptxt[p])}'
                      + (' <span class="dim">'
                         + t("lernwizard.phase.aktuell") + '</span>'
                         if aktiv else "")
                      + name_link + det_html + "</div>")
    zugeordnet = {k for ks in _PHASEN_KEYS.values() for k in ks} | {"status"}
    rest = " · ".join(f"{k}: {f[k]}" for k in f if k not in zugeordnet)
    rest_html = f'<div class="dim">{html.escape(rest)}</div>' if rest else ""
    kaputt_html = (' · <b>' + t("lernwizard.zeile.kaputt", n=anker_kaputt)
                   + '</b>' if anker_kaputt else "")
    anker_link = (' · <a href="/lernlauf/anker">'
                  + t("lernwizard.zeile.anker_link", n=anker_zahl) + '</a>'
                  if anker_zahl else "")
    # .246: das Chip-/Vorschau-CSS der .223/.244-Fassung ist ersetzt — die
    # Kacheln, Queue und Flaeche unten sind jetzt die eine Darstellung.
    # 20.08.: das Blatt selbst wohnt seit dem /personlauf-Nachzug in
    # webui.bausteine.lauffluss_stil() — BEIDE Lauf-Seiten rendern dieselben
    # Klassen aus DERSELBEN Quelle (K3-Regel: nie ein zweites, wortgleiches
    # CSS-Blatt). Der Rueckgabestring ist byte-identisch zur alten Fassung
    # (Beweis harnisch_sprache, Fall lernwizard).
    stil = lauffluss_stil()
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
    # .295: verworfene Gruppen (Hand-Dismiss wie .294-End-Sichtung) sind
    # fuer Zaehler/Streifen unsichtbar — real existieren fuer den Nutzer
    # nur die behaltenen; einsehbar bleiben sie via Sammelzeile.
    weg_n = sum(1 for g in gruppen if g.get("status") == "verworfen")
    gruppen_sichtbar = [g for g in gruppen
                        if g.get("status") != "verworfen"]
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
    # .260: Balken/Zeit/Zaehler kommen aus lauf_status — DERSELBEN Rechnung,
    # die der /lernlauf_status-Endpunkt dem Widget liefert (eine Quelle).
    # ernte_puls reicht der Handler durch (lernlauf.lauf_puls), damit schon der
    # Seiten-Render die tickenden Unterbalken zeigt, nicht erst der Poll.
    # (BEWUSST nicht `puls` benannt: so heisst oben schon die working-Zeile.)
    s2 = lauf_status(zustand, puls=ernte_puls)
    ergebnis = ""
    if ph in ("vorbereitung", "ernte") or (ph == "anker" and not anker_fertig):
        ergebnis = s2["zaehler"]
    elif gruppen:
        # DREI echte Plurale in EINEM Zaehler-Satz: je Plural ein
        # t_n-Fragment, Trenner literal (§8.10 — Zaehler, keine Prosa).
        ergebnis = (t_n("lernwizard.ergebnis.bilder", n_bilder) + " "
                    + t_n("lernwizard.ergebnis.aufnahmen", n_events) + " · "
                    + t_n("lernwizard.ergebnis.gruppen",
                          len(gruppen_sichtbar))
                    + (" " + t("lernwizard.ergebnis.beiseite", n=weg_n)
                       if weg_n else ""))
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
            + t("lernwizard.pop.alle_gesichter") + '</label> '
            '<label><input type="radio" name="lf-wen" '
            'onchange="document.getElementById(\'lf-ziel\').disabled=false"> '
            + t("lernwizard.pop.eine_person") + '</label> '
            f'<select id="lf-ziel" disabled>{_opts}</select>'
            '<span class="lf-hint">' + t("lernwizard.pop.hint_person")
            + '</span></div>')
    such_knopf = (
        '<button class="lf-such" onclick="document.getElementById(\'lf-deck\')'
        '.style.display=\'grid\'">&#128269;&nbsp; '
        + t("lernwizard.such.titel")
        + '<small>' + t("lernwizard.such.klein") + '</small></button>')
    such_deck = (
        '<div id="lf-deck" class="lf-deck" '
        'onclick="if(event.target===this)this.style.display=\'none\'">'
        f'<div class="lf-pop"><h3>{t("lernwizard.such.titel")}</h3>'
        f'<p class="lf-satz">{t("lernwizard.pop.satz")}</p>'
        # .263 Wechselschalter (User: 'einmal ein ganzer Tag, einmal x
        # Events'): letzte-N ODER ein Kalendertag; das jeweils inaktive
        # Feld ist gesperrt, app.js liest den aktiven Modus.
        '<div class="lf-popz"><label><input type="radio" name="lf-um" '
        'id="lf-um-n" checked onchange="lfUmschalten()"> '
        + t("lernwizard.pop.label_letzte") + '</label> '
        f'<input id="lf-pop-n" type="number" min="1" max="{int(max_events)}" '
        f'value="{int(easy_events)}" style="width:6em"> '
        + t("lernwizard.pop.wort_events") +
        '<span class="lf-hint">'
        + t("lernwizard.pop.hint_n", max=int(max_events)) + '</span></div>'
        '<div class="lf-popz"><label><input type="radio" name="lf-um" '
        'id="lf-um-tag" onchange="lfUmschalten()"> '
        + t("lernwizard.pop.label_tag") + '</label> '
        '<input id="lf-pop-tag" type="date" disabled>'
        '<span class="lf-hint">' + t("lernwizard.pop.hint_tag")
        + '</span></div>'
        # Sprach-Pruefung Tranche D: reines Schalt-JS ohne Sprache —
        # nichts einzuziehen.
        '<script>function lfUmschalten(){'
        'var t=document.getElementById("lf-um-tag").checked;'
        'document.getElementById("lf-pop-n").disabled=t;'
        'document.getElementById("lf-pop-tag").disabled=!t;}</script>'
        '<div class="lf-popz"><input id="lf-pop-fps" type="number" min="1" '
        'max="30" step="0.5" value="3" style="width:5em"> '
        + t("lernwizard.pop.wort_fps") +
        '<span class="lf-hint">' + t("lernwizard.pop.hint_fps")
        + '</span></div>'
        # .262 Fortsetzungs-Suche (User: '5 x 100 statt 1 x 500'): Haken an
        # = schon Durchsuchtes ueberspringen, jeder Lauf wandert weiter in
        # die Vergangenheit; Haken ab = die neuesten nochmal.
        '<div class="lf-popz"><label><input type="checkbox" id="lf-weiter" '
        'checked> ' + t("lernwizard.pop.label_skip") + '</label>'
        '<span class="lf-hint">' + t("lernwizard.pop.hint_skip")
        + '</span></div>'
        + _wen +
        '<div class="lf-popf">'
        '<button class="gtb on" onclick="lernlaufPopupStart(this)">'
        + t("lernwizard.pop.knopf_start") + '</button>'
        '<button class="gtb" onclick="document.getElementById(\'lf-deck\')'
        '.style.display=\'none\'">' + t("lernwizard.knopf_abbrechen")
        + '</button>'
        '<span id="lf-pop-status" class="dim"></span></div></div></div>')

    # --- Reihe kleiner Klick-Felder in Kachel 1 (User 26.08. am Screenshot:
    # "zwischen Ergebnis-Zeile und dem grossen Such-Knopf, Platz fuer bis zu
    # DREI kleinere Felder"). Heute EINES belegt: der Abgleich der
    # Belichtungs-Grenzen (analysen/bauplan_belichtung.md Phase 1b).
    # ERWEITERBAR by construction: die Reihe ist ein flex-Container
    # (webui/style.css .lf-minis) — ein weiteres <a> in diese Liste genuegt,
    # bis drei stehen sie nebeneinander, danach bricht die Reihe um.
    mini_felder = ['<a href="/lernlauf/belichtung">'
                   + t("lernwizard.k1.mini_belichtung") + '</a>']
    mini_reihe = f'<div class="lf-minis">{"".join(mini_felder)}</div>'

    # --- Kachel 1: der Lauf ----------------------------------------------
    if zustand is None:
        hinweis_u = ""
        if unbekannt_offen:
            # Echter Plural — t_n; der Link bleibt Markup-Grenze.
            hinweis_u = ('<p class="lf-satz">'
                         + t_n("lernwizard.k1.unbekannt",
                               int(unbekannt_offen))
                         + ' <a href="/unbekannte">'
                         + t("lernwizard.link_unbekannte") + '</a></p>')
        # .246: an der Start-Stelle sagen, dass der Lauf nur fuer den Blick
        # ZURUECK noetig ist. .263 (User am Screenshot: 'vollgemuellt mit
        # Text'): auf EINEN Satz gekuerzt — der Leer-Zustand soll so schlank
        # aussehen wie die fertige Kachel.
        # Stufe-0-Grenze: <b>back</b> mitten im Satz — bleibt literal.
        k1 = ('<p class="lf-satz">Only needed to look <b>back</b> &mdash; '
              'day to day the system learns on its own.</p>' + hinweis_u
              + mini_reihe
              + '<div class="lf-rest">' + such_knopf + such_deck + '</div>')
    else:
        # .255/.259: der Neustart-Weg gehoert in die Kachel — seit .259 als
        # der EINE grosse Suchknopf mit Popup (Mockup-Abnahme), nur bei
        # abgeschlossenem Lauf (waehrend er laeuft, blockt der Server einen
        # Neustart ohnehin — Phasen-Wache).
        neu_form = ""
        if anker_fertig:
            neu_form = '<div class="lf-rest">' + such_knopf + such_deck + '</div>'
        k1 = ('<div><span class="phok">&#10003;</span> '
              + t("lernwizard.k1.gestartet", wann=_dt(z.get("ts")))
              + '</div>'
              + (f'<div class="lf-satz">{html.escape(ergebnis)}</div>'
                 if ergebnis and not laeuft else "")
              + '<div class="lf-satz nur-expert">'
              + t("lernwizard.k1.scope", n=z.get("events", "?"))
              + (' &middot; '
                 + t("lernwizard.k1.tag", tag=html.escape(str(z["tag"])))
                 if z.get("tag") else "") + '</div>'
              + mini_reihe
              + neu_form)

    # --- Kachel 2: der Fortschritts-Block --------------------------------
    # .345 (User 25.08., Bild-Konsens: "der Balken hier muss durch die neuen
    # ersetzt werden"): Gesamtbalken + Phasen-Zeile + DREI Unterbalken statt
    # der Saeule. Ehrliche Fuellung wie gehabt (Regeln in lauf_status, EINE
    # Quelle mit dem Widget-Endpunkt): Vorbereitung 0-15 %, Ernte 15-85 %
    # proportional zum echten Event-Zaehler, Sortierung = 85 %, fertig = 100 %.
    # .260: Zeit/Zaehler tragen IDs und werden waehrend des Laufs vom
    # Widget-JS in place nachgefuehrt (immer gerendert, ggf. leer).
    k2 = (f'<p class="lf-satz">{t("lernwizard.k2.satz")}</p>'
          '<div class="fs-block" id="lf-fsb">'
          f'<div class="fs-total"><span class="fs-fill" '
          f'style="width:{s2["proz"]}%"></span></div>'
          f'<div class="fs-phasen">{"".join(_seg_html(sg) for sg in s2["seg"])}'
          '</div>'
          + "".join(_balken_html(sb) for sb in s2["balken"])
          + '</div>'
          '<div class="lf-rest">'
          + (f'<div class="lf-satz" id="lf-zeit">{html.escape(s2["zeit"])}'
             '</div>' if s2["zeit"] or laeuft else "")
          + (f'<div class="lf-satz nur-expert" id="lf-zaehler">'
             f'{html.escape(ergebnis)}</div>' if laeuft else "")
          # .261 (User: 'ein Abbruch-Button waere auch nicht schlecht'):
          # direkt an der Saeule statt am Seitenende — derselbe
          # lernlaufAbbruch-Weg (app.js, mit Confirm).
          + ('<div style="margin-top:6px"><button class="gtb" '
             'onclick="lernlaufAbbruch(this)">'
             + t("lernwizard.k2.knopf_abort") + '</button></div>'
             if laeuft else "")
          + "</div>")

    # --- Kachel 3: die Gruppen-Queue -------------------------------------
    # .295 (User 19.08.): nur sichtbare Gruppen als Chips (s. Definition
    # oben bei wartend).
    reihe = sorted(gruppen_sichtbar,
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
                                  or t("lernwizard.chip.bilder", n=len(mg))))
        qchips.append(f'<a class="{cls}" href="{ziel_g}" '
                      f'title="{titel_g}">{bild}</a>')
    offen_n = len(wartend)
    if zustand is None or laeuft:
        k3 = f'<p class="lf-satz">{t("lernwizard.k3.satz_warten")}</p>'
    elif anker_fertig and not anker_zahl:
        k3 = (f'<p class="lf-satz">{t("lernwizard.k3.keine_gesichter")}</p>'
              '<div class="lf-rest">'
              '<a class="gtb" href="/lernlauf?neu=1">'
              + t("lernwizard.knopf_neuer_lauf") + '</a></div>')
    else:
        erledigt = len(gruppen_sichtbar) - offen_n
        k3 = ('<p class="lf-satz">'
              + (t("lernwizard.k3.gruppe_offen")
                 if kz[2] == "dran" else t("lernwizard.k3.alle_erledigt"))
              + '</p>'
              # .259: Zielperson-Suche sichtbar machen — passende Gruppen
              # stehen vorn, nichts wird versteckt.
              # Stufe-0-Grenze: <b>-Name mitten im Satz — bleibt literal.
              + (f'<p class="lf-satz">looking for <b>{html.escape(zielperson)}'
                 '</b> &mdash; matching groups are listed first.</p>'
                 if zielperson else "")
              + f'<div class="lf-q">{"".join(qchips)}</div>'
              # .295-Sammelzeile (qs.sh-PYAD-Anker): Text in en.py,
              # echter Plural via t_n, Einsicht-Link bleibt.
              + ('<p class="lf-satz dim">'
                 + t_n("lernwizard.k3.verworfen", weg_n)
                 + ' <a href="/lernlauf/anker">'
                 + t("lernwizard.k3.link_einsehen") + '</a></p>'
                 if weg_n else '')
              + '<div class="lf-rest"><div class="lf-satz">'
              # B9: je Zweig ein GANZER Satz-Schluessel; der done-Zaehler
              # rechnet weiter ueber die SICHTBAREN Gruppen.
              + ((t("lernwizard.k3.done_weiter", erledigt=erledigt, gesamt=len(gruppen_sichtbar))
                  if offen_n else
                  t("lernwizard.k3.done_punkt", erledigt=erledigt, gesamt=len(gruppen_sichtbar)))
                 if erledigt else
                 t_n("lernwizard.k3.wartend", offen_n))
              + (' &middot; <b>'
                 + t("lernwizard.zeile.kaputt", n=anker_kaputt) + '</b>'
                 if anker_kaputt else "")
              + '</div></div>')

    # --- Kachel 4: Bilanz -------------------------------------------------
    if kz[3] == "dran":
        if adoptiert and adoptiert.get("bilder"):
            _ab, _ap = adoptiert["bilder"], adoptiert.get("personen", 0)
            # ZWEI Plurale im <b>-Zaehler: zwei t_n-Fragmente (§8.10).
            btxt = ('<b>' + t_n("lernwizard.k4.adopt_bilder", _ab) + ' '
                    + t_n("lernwizard.k4.adopt_personen", _ap)
                    + '</b> &mdash; '
                    + t("lernwizard.k4.zaehlen_sofort") + ' '
                    # .273c: Kontext-Einstieg in den Bestands-Check direkt
                    # nach dem Hinzufuegen (User-Wunsch).
                    '<a href="/qualitaet">' + t("lernwizard.k4.link_qs")
                    + '</a>')
        else:
            btxt = t("lernwizard.k4.nichts")
        k4 = (f'<div><span class="phok">&#10003;</span> {btxt}</div>'
              f'<p class="lf-satz">{t("lernwizard.k4.wiederholen")}</p>'
              '<div class="lf-rest">'
              '<a class="gtb on" href="/faces">'
              + t("lernwizard.k4.knopf_faces") + '</a> '
              '<a class="gtb" href="/lernlauf?neu=1">'
              + t("lernwizard.knopf_neuer_lauf") + '</a></div>')
    else:
        k4 = f'<p class="lf-satz">{t("lernwizard.k4.hinweis")}</p>'

    fluss = ('<div class="lf-fluss">'
             + _kachel(1, kz[0], t("lernwizard.kachel.lauf"), k1)
             + _kachel(2, kz[1], t("lernwizard.kachel.sammeln"), k2)
             + _kachel(3, kz[2], t("lernwizard.kachel.benennen"), k3)
             + _kachel(4, kz[3], t("lernwizard.kachel.fertig"), k4)
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
                                           or t("lernwizard.zw.grund_maessig")))
                         + "</span>")
                return (f'<label class="{klasse}">'
                        f'<input type="checkbox" name="lfsel" value="{fn}"'
                        f'{" checked" if checked else ""} onchange="lfZaehl()">'
                        f'<img src="/lernlauf/crop/{lid}/{fn}" loading="lazy">'
                        f'<a class="lf-zwclip" href="/video/{ev}" '
                        f'title="{t("lernwizard.zw.attr_clip")}">&#9654;</a>{grund}</label>')

            # .271 (User-Zielbild): DREI beschriftete Reihen nach
            # Blickwinkel — je Reihe die optimalen dieses Winkels (gut vor
            # Grenzfall vor Double, Deckel 12); nichts Gutes versteckt sich
            # woanders, der Aufklapper traegt nur Rest + Aussortierte.
            gute = [s for s in sichtung if s.get("stufe") == "gut"]
            grenz = [s for s in sichtung if s.get("stufe") == "grenzfall"]
            reihen_html, rest, zeige_n = [], [], 0
            for blick, label in (("links", t("lernwizard.blick.links")),
                                 ("frontal", t("lernwizard.blick.frontal")),
                                 ("rechts", t("lernwizard.blick.rechts"))):
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
                        + t("lernwizard.blick.leer")
                        + '</span></fieldset>')
                    continue
                ks = [_kachel_s(s, "lf-neu" if s.get("stufe") == "gut"
                                else "lf-grenz", s.get("stufe") == "gut")
                      for s in zeile]
                reihen_html.append(
                    '<fieldset class="lf-blickbox">'
                    f'<legend>{label} <span class="dim">'
                    + t("lernwizard.blick.legende", gut=len(gb),
                        grenz=len(zb), n=len(im))
                    + '</span>'
                    f'</legend><div class="lf-zwg">{"".join(ks)}</div>'
                    '</fieldset>')
            kacheln_html = "".join(reihen_html)
            mehr = ""
            # Stufe 2 Tranche D (§8.17 Toggle-Label): BEIDE Fassungen kommen
            # fertig formatiert vom Server — im onclick als einfach-quotierte
            # JS-Literale (bausteine.js_literal, byte-treu; json.dumps
            # braeche mit Doppel-Quotes das Attribut), sichtbarer Knopftext
            # aus DEMSELBEN Schluessel.
            if rest:
                mk = [_kachel_s(s, "lf-grenz" if s.get("stufe") == "grenzfall"
                                else "lf-dup", False) for s in rest]
                _txt_zu = t("lernwizard.zw.js_verbergen", n=len(rest))
                _txt_auf = t("lernwizard.zw.js_zeigen", n=len(sichtung))
                mehr = (
                    '<button type="button" class="gtb" id="lf-mehr-knopf" '
                    'onclick="var m=document.getElementById(\'lf-mehr\');'
                    'var auf=m.style.display===\'none\';'
                    'm.style.display=auf?\'\':\'none\';'
                    'this.textContent=auf?' + js_literal(_txt_zu) + ':'
                    + js_literal(_txt_auf) + ';lfZaehl();">'
                    f'{html.escape(_txt_auf)}</button>'
                    f'<div class="lf-zwg" id="lf-mehr" style="display:none">'
                    + "".join(mk) + '</div>')
            # Stufe-0-Grenze (§8.3 + qs.sh-.257-Anker): pruef_wort wird in
            # zwei Saetze GESPLICED — sicht_zeile bleibt literal bis zum
            # Ganz-Satz-Umbau je Zweig.
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
        pos = len(gruppen_sichtbar) - len(wartend) + 1
        v = benennung.get("vorschlag")
        schon = aktuelle.get("status") == "benannt"
        opts = "".join(f'<option value="{html.escape(p)}">'
                       for p in (benennung.get("personen") or []))
        hin = ""
        if v:
            _bek = (t("lernwizard.bekannt.system") if {"referenz", "master"}
                    & set(v.get("quellen") or []) else
                    t("lernwizard.bekannt.anker"))
            # Stufe-0-Grenze: looks like <b>X</b> … — Markup um Daten mitten
            # im Satz (Muster lernanker), nur die _bek-Halbsaetze sind
            # Schluessel.
            hin = (f'<p class="lf-satz">looks like <b>{html.escape(v["name"])}'
                   f'</b> (similarity {v["sim"]}) &mdash; {_bek}; suggestion '
                   'only.</p>')
        if schon:
            # Stufe-0-Grenze: named <b>X</b> … — dito, bleibt literal.
            hin += (f'<p class="lf-satz">named <b>'
                    f'{html.escape(str(aktuelle.get("person")))}</b> &mdash; '
                    'adoption pending.</p>')
        skip_ziel = (f'/lernlauf?g={html.escape(str(naechste_id))}'
                     if naechste_id else "/lernlauf")
        if schon:
            ja = (f'<button type="button" class="gtb on" id="lf-adopt" '
                  f'data-person="{html.escape(str(aktuelle.get("person") or ""), quote=True)}">'
                  + t("lernwizard.zw.knopf_adopt",
                      name=html.escape(str(aktuelle.get("person"))))
                  + '</button>')
        elif v:
            ja = (f'<button type="button" class="gtb on" id="lf-ja" '
                  f'data-name="{html.escape(v["name"], quote=True)}">'
                  + t("lernwizard.zw.knopf_ja",
                      name=html.escape(v["name"])) + '</button>')
        else:
            ja = ""
        benenn_aktiv = True
        if sicht_fehler:
            mitte = ('<div class="lf-satz">&#9888; '
                     + t("lernwizard.zw.fehler") + '</div>')
            benenn_aktiv = False
        elif sicht_warte:
            mitte = ('<div class="lf-satz" id="lf-sicht-warte">&#9203; '
                     + t("lernwizard.zw.warte") + '</div>'
                     + _sicht_js())
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
            '<h3>' + t("lernwizard.zw.titel", pos=pos,
                       gesamt=len(gruppen_sichtbar)) + '</h3>'
            f'<p class="lf-satz">{t("lernwizard.zw.satz")}</p>' + hin
            + mitte
            + '<div class="lf-knoepfe" id="lf-knopfzeile-1">' + ja
            + (('<button type="button" class="gtb" id="lf-andere">'
                + t("lernwizard.zw.knopf_andere") + '</button>'
                '<input type="text" id="lf-name" list="lf-personen" '
                f'placeholder="{t("lernwizard.zw.attr_name")}" '
                'style="display:none" '
                f'value="{html.escape(str(aktuelle.get("person") or ""))}">'
                f'<datalist id="lf-personen">{opts}</datalist>'
                '<button type="button" class="gtb on" id="lf-save" '
                'style="display:none">' + t("lernwizard.zw.knopf_save")
                + '</button>')
               if benenn_aktiv else "")
            + (f'<a class="gtb" href="{skip_ziel}">'
               + t("lernwizard.zw.knopf_skip") + '</a>')
            # .259 (User: 'der Knopf delete the group fehlt'; Mockup-Abnahme
            # Variante A): Verwerfen mit Gedaechtnis, rechtsbuendig abgesetzt
            # in ruhiger roter Umrandung — derselbe ankerVerwerfen-Weg
            # (app.js) wie auf der Anker-Seite, mit Bestaetigung.
            + '<span class="lf-spacer"></span>'
            + f'<button type="button" class="lf-del" '
              f'onclick="ankerVerwerfen(\'{aid}\',this)" '
              f'data-frage="{t("lernwizard.zw.frage_delete")}">'
            + t("lernwizard.zw.knopf_delete") + '</button></div>'
            # .256: zweite Knopfzeile — erscheint NACH der Pruefung, mit der
            # ehrlichen Zahl auf dem Knopf; Cancel laedt neu (Auswahl-Reset).
            + '<div class="lf-knoepfe" id="lf-knopfzeile-2" '
              'style="display:none">'
              '<button type="button" class="gtb on" id="lf-take"></button>'
              '<button type="button" class="gtb" id="lf-cancel">'
            + t("lernwizard.knopf_abbrechen") + '</button></div>'
            + '<div class="lf-knoepfe"><span id="lf-status" class="dim">'
              '</span><span class="lf-satz" id="lf-zaehl" '
              'style="margin-left:auto"></span></div>'
            + '<div class="lf-satz nur-expert" style="margin-top:6px">'
              f'<a href="/lernlauf/anker?a={aid}">'
            + t("lernwizard.zw.link_detail") + '</a> '
            + t("lernwizard.zw.detail_zusatz") + '</div>'
            + '</div>' + _zw_js())
    easy = fluss + zuweisung
    # Seiten-Kopf: Titel + der eine Erklaer-Satz + Anleitung (ek-hilfe wie
    # auf den Kacheln — .244-Vertrag bleibt).
    # .255 (User am Screenshot): der Erklaer-Satz kostete nur Platz — weg.
    kopf = (f'<h2>{t("lernwizard.titel")}</h2>'
            '<div class="ek-hilfe"><a href="/hilfe/faces_lernlauf">'
            + t("lernwizard.link_how") + '</a></div>')
    if zustand is None:
        # Kein Lauf: nur der Fluss (Kachel 1 aktiv); der volle Planer haengt
        # als nur-expert dahinter (Handler-Komposition, Wizard bleibt Expert).
        return stil + kopf + easy
    # .88: den Nutzer ZUM ERGEBNIS fuehren — ohne diesen Block wuesste
    # niemand, dass die Bilder unter Anchors liegen.
    erfolg = ""
    if anker_fertig and anker_zahl:
        erfolg = ('<div class="card"><b><span class="phok">&#10003;</span> '
                  + t("lernwizard.erfolg.titel") + '</b> — '
                  + t_n("lernwizard.erfolg.cluster", anker_zahl)
                  + ' <a class="gtb on" href="/lernlauf/anker">'
                  + t("lernwizard.erfolg.knopf_anker") + '</a> '
                  '<span class="dim">' + t("lernwizard.erfolg.hinweis")
                  + '</span></div>')
    # .223/.246: der Fluss fuehrt fuer BEIDE Sichten (Expert = Easy plus
    # Details); Erfolgs-Banner, Phasen-Kette und Progress sind Expert-Tiefe.
    return (stil + kopf + easy
            + f'<div class="nur-expert">{erfolg}'
            + f'<div class="card"><b>{t("lernwizard.expert.phasen_titel")}</b>'
            f'{"".join(zeilen)}'
            f'<div class="dim">{t("lernwizard.expert.phasen_hinweis")}'
            '</div></div>'
            f'<div class="card"><b>{t("lernwizard.expert.progress_titel")}</b>'
            f'<div>{html.escape(st) if st else "—"}</div>{puls}{rest_html}'
            '<div class="dim">'
            + t("lernwizard.expert.anker_bisher", n=anker_zahl)
            + f'{anker_link}{kaputt_html} · '
            + t("lernwizard.expert.progress_rest", wann=_dt(z.get("ts")),
                n=z.get("events", "?"))
            + "</div></div></div>"
            + ('<p class="nur-expert"><a class="gtb" href="/lernlauf?neu=1">'
               + t("lernwizard.knopf_neuer_lauf") + '</a> '
               '<span class="dim">' + t("lernwizard.expert.lauf_bleibt")
               + '</span></p>'
               if anker_fertig else "")   # .261: Abort wohnt jetzt in Kachel 2
            + (_WIDGET_JS if s2["tickt"] else ""))
