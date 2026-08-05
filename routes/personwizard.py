"""routes/personwizard — Person-Learn-Assistent (PE1, stufe2.md: des Users
Schritt-1-Ablauf = Wunsch-N Events + gezielte Personen-Auswahl, danach
Klick-Abnahme; Erstlauf klein anfangen. Onboarding-Prosa 04.08.: der User
wird an die Hand genommen — was passiert, was entscheidet er, warum muss
erst mindestens eine Person gelernt sein, bevor der Strang aktiv wird).

Kontrakt wie alle routes-Module: reine Renderer, Daten als Parameter, kein
Dienst-Import; Seiteneffekte (Events zaehlen, Lauf anlegen, Thread/Worker)
macht der Handler in verifyd.py."""
import datetime
import html
import json
import urllib.parse


def _kopf():
    return [
        "<h2>Learn people — body recognition</h2>",
        '<p class="sub">A second, independent recognition path: it learns '
        "what a person looks like as a WHOLE (build, hair, posture) so it "
        "can recognize residents even when no face is visible.</p>",
        '<div class="card"><b>How this works — you stay in control</b>'
        "<div>1 · You choose how many events to scan and WHO to learn "
        "(one person, or all known people).<br>"
        "2 · The run harvests full-body images from your own recordings. "
        "A picture is tied to a person only when a face-confirmed "
        "walk-through proves it — deliberately conservative.<br>"
        "3 · YOU review every harvested image; one click rejects a wrong "
        "one. Nothing is learned without your approval.<br>"
        "4 · Training then runs locally in seconds, and a decision "
        "threshold is measured so strangers stay below it.</div>"
        '<div class="dim" style="margin-top:6px">A note on speed: '
        "harvesting currently runs on the CPU, so please bear with a run "
        "taking a little while (roughly 15&ndash;30 s per event). Moving "
        "this to the GPU/NPU is planned for a later version.</div>"
        '<div class="dim">Why at least one person first: this path can only '
        "tell people apart after it has learned — and you have reviewed — "
        "what at least one resident looks like. Until then body recognition "
        "stays OFF and never sends an alert. When it does alert later "
        "(Pushover/Telegram), the message is marked as coming from person "
        "recognition, not from face recognition.</div></div>"]


def wizard(personen, auswahl_n, person_wahl, bilanz=None, lauf=None,
           modell=None, max_events=40000):
    """Wizard-Ansicht Person Learn.
    personen     Liste bekannter Personen-Namen (aus dem Gesichts-Bestand)
    auswahl_n    gewaehlte Event-Zahl (int) oder None
    person_wahl  gewaehlte Person (Name) oder "" = alle
    bilanz       optional dict(n[, gebunden, fremd]) vom Handler
    lauf         personlauf.json-Zustand (dict) oder None"""
    teile = _kopf()
    karte = _modell_karte(modell)
    if karte:
        teile.append(karte)
    phase = (lauf or {}).get("phase")
    if phase == "vorbereitung":
        wer = html.escape((lauf or {}).get("person") or "all known people")
        teile.append('<div class="card"><b>Preparing the run &hellip;</b>'
                     f'<div>tying the last {(lauf or {}).get("wunsch_n", "?")} '
                     f'events to {wer} via confirmed walk-throughs</div>'
                     '<div class="dim">This takes a minute or two — the page '
                     "refreshes on its own, harvesting starts right after."
                     "</div></div>")
        return "".join(teile)
    if phase == "ernte":
        f = (lauf or {}).get("fortschritt") or {}
        stand = (f'{f.get("events", 0)}/{f.get("von", lauf.get("events", "?"))}'
                 f' events · {f.get("bilder", 0)} images harvested'
                 if f else "starting …")
        wer = html.escape(lauf.get("person") or "all known people")
        teile.append('<div class="card"><b>A person-learn run is active</b>'
                     f'<div>learning {wer} · {stand}</div>'
                     '<div class="dim">This page refreshes on its own. '
                     "A new run can be started once it finishes.</div>"
                     '<div style="margin-top:8px"><button class="gtb" '
                     'onclick="personlaufAbbruch(this)">Abort run</button> '
                     '<span class="dim">harvested images are kept</span>'
                     "</div></div>")
        return "".join(teile)
    if phase == "unterbrochen":
        teile.append(
            '<div class="card"><b>Last run was interrupted</b>'
            '<div class="dim">Probably a service restart. Start the same '
            "run again below — already-harvested events are skipped "
            "automatically (resume), nothing is lost.</div></div>")
    if phase == "abnahme":
        # Gefuehrter Fluss (User 04.08.): solange das Review aussteht,
        # KEIN neuer Start — Formular bleibt ausgeblendet.
        # json.dumps liefert "..." — im doppelt gequoteten onclick-Attribut
        # zerriss das den Aufruf (Knopf tot, User-Fund 04.08.): den ganzen
        # Aufruf als Attributwert escapen (&quot;), der Browser dekodiert
        # Attribute, bevor das JS laeuft.
        _lid = json.dumps(str(lauf.get("lauf_id") or ""))
        _dc = html.escape(f"personlaufVerwerfen({_lid})", quote=True)
        teile.append(
            '<div class="card"><b>Last run finished — your review is next</b>'
            f'<div>{lauf.get("geerntet", 0)} images harvested for '
            f'{html.escape(lauf.get("person") or "all known people")} '
            f'(run {html.escape(str(lauf.get("lauf_id", "")))}).</div>'
            '<div style="margin-top:8px"><a class="gtb on" '
            'href="/personlauf/abnahme">Review the images now</a> '
            '<span class="dim">finish the review to unlock the next '
            "run</span> "
            f'<span style="float:right"><button class="gtb" onclick="{_dc}">'
            "Discard this run</button> <span class=\"dim\">bad result? "
            "throw it all away</span></span></div></div>")
        return "".join(teile)
    elif phase == "fertig" and not lauf.get("events") \
            and not lauf.get("abgenommen") and not lauf.get("verworfen"):
        # 0-Events-Erklaer-Karte (User-Fund 05.08., zwei reale Personen:
        # der Lauf endete stumm und sah wie ein Abbruch aus — der Nutzer
        # muss das WARUM sehen). Zaehler kommen aus personlauf.anlegen().
        dg = lauf.get("diagnose") or {}
        wer = html.escape(lauf.get("person") or "the selected people")
        tage = dg.get("fenster_tage", 19)
        if dg.get("gebunden_fenster", 0) == 0:
            zl = dg.get("zuletzt_bestaetigt")
            if zl:
                zeile = ("last face-confirmed appearance: "
                         + datetime.datetime.fromtimestamp(zl).strftime("%d %b %Y"))
            else:
                schwach = dg.get("gesehen_schwach") or 0
                seit = dg.get("akte_seit")
                seit_txt = (datetime.datetime.fromtimestamp(seit).strftime("%d %b %Y")
                            if seit else "?")
                zeile = ("the event record (which starts " + seit_txt + " — "
                         "earlier visits are not in it) has "
                         + (("them appearing " + str(schwach) + " time"
                             + ("s" if schwach != 1 else "") + " BELOW the "
                             "confirmation threshold — present, but face "
                             "recognition never confirmed them") if schwach else
                            "no confirmed appearance for them"))
            grund = ("No face-confirmed walk-throughs for <b>" + wer + "</b> in "
                     "the last " + str(tage) + " days. The harvest can only tie "
                     "images to a person through a confirmed pass; " + zeile + ".")
        else:
            grund = ("All " + str(dg.get("gebunden_fenster")) + " bindable events "
                     "for <b>" + wer + "</b> are already part of your learning "
                     "material — there was nothing new to harvest. New "
                     "walk-throughs become harvestable automatically.")
        teile.append(
            '<div class="card"><b>Run finished without images — here is why</b>'
            "<div>" + grund + "</div>"
            '<div class="dim">Nothing was changed; you can start another '
            "run below any time.</div></div>")
    elif phase == "fertig":
        teile.append(
            '<div class="card"><b>Review finished — material adopted</b>'
            f'<div>{lauf.get("abgenommen", 0)} images approved as learning '
            f'material, {lauf.get("verworfen", 0)} rejected '
            f'(run {html.escape(str(lauf.get("lauf_id", "")))}).</div>'
            '<div class="dim">Training on the approved material ships with '
            "the next update — your review is stored and nothing needs to "
            "be repeated. You can start another run below any time.</div>"
            '<div style="margin-top:8px"><a class="gtb" '
            'href="/person">View the learned material</a>'
            "</div></div>")
    elif phase == "fehler":
        teile.append('<div class="card"><b>Last run failed</b>'
                     f'<div class="dim">{html.escape(str(lauf.get("fehler", "")))}'
                     "</div></div>")
    # Personen-Auswahl (User: gezielt EINE Person oder alle)
    opts = ['<option value="">All known people</option>'] + [
        f'<option value="{html.escape(p, quote=True)}"'
        f'{" selected" if p == person_wahl else ""}>{html.escape(p)}</option>'
        for p in personen]
    teile.append('<div class="card"><b>Who to learn</b>'
                 f'<div><select id="pl-person">{"".join(opts)}</select></div>'
                 '<div class="dim">Pick one person to review in small, '
                 "focused batches — or all at once. People come from your "
                 "face collection; learning one at a time keeps the review "
                 "short.</div></div>")
    # Presets/Formular lesen die Person beim KLICK live aus dem Dropdown —
    # der server-seitige Wert ist veraltet, sobald der User umwaehlt, und
    # warf die Auswahl sonst auf "alle" zurueck (User-Fund 04.08.).
    knoepfe = "".join(
        f'<a class="gtb{" on" if auswahl_n == n else ""}" '
        f'href="/personlauf?events={n}" onclick="this.href+='
        "'&person='+encodeURIComponent("
        "document.getElementById('pl-person').value)\">"
        f'last {n}</a> '
        for n in (50, 100, 200))
    eigen = ('<form action="/personlauf" method="get" '
             'style="display:inline;margin-left:10px" onsubmit="'
             "this.person.value=document.getElementById('pl-person').value\">"
             f'<input name="events" type="number" min="1" max="{int(max_events)}"'
             f' size="6" value="{auswahl_n or ""}" placeholder="own N"> '
             f'<input type="hidden" name="person" value="'
             f'{html.escape(person_wahl or "", quote=True)}">'
             '<button class="gtb">go</button></form>')
    teile.append(f'<div class="card"><b>Scope (events, not days)</b>'
                 f'<div>{knoepfe}{eigen}</div>'
                 '<div class="dim">Start small (50) — you will review every '
                 "harvested image by hand.</div></div>")
    if auswahl_n and bilanz:
        b = bilanz
        wer = html.escape(person_wahl) if person_wahl else "all known people"
        if b.get("gebunden") is None:
            zeile = (f'last {b["n"]} person events for {wer} — the binding '
                     "balance is computed when the run is created")
        else:
            zeile = (f'last {b["n"]} person events · <b>{b["gebunden"]}</b> '
                     f'can be tied to {wer} via confirmed walk-throughs'
                     + (f' · {b.get("fremd", 0)} stranger candidates'
                        if b.get("fremd") else ""))
        teile.append(
            f'<div class="card"><b>Your selection</b><div>{zeile}</div>'
            '<div class="dim">Tying is conservative: only walk-throughs with '
            "exactly one face-confirmed person count. Everything you see "
            "afterwards can be rejected with one click.</div></div>")
        teile.append('<p><button class="gtb on" onclick="personlaufStart('
                     f'{int(b["n"])},this)">Create this run</button> '
                     '<span id="pl-status" class="dim"></span></p>')
    return "".join(teile)


def abnahme_seite(lauf, zeilen, markiert):
    """PE2 Klick-Abnahme des letzten Laufs (Muster der Prototyp-Klick-Seite):
    Kachel je Bild, Klick = FALSCH (nicht diese Person / unbrauchbar),
    zweiter Klick nimmt es zurueck; jede Wahl wird sofort gespeichert."""
    lauf_id = str(lauf.get("lauf_id") or "")
    ok = [z for z in zeilen if "ausfall" not in z]
    je_person = {}
    for z in ok:
        je_person.setdefault(z["person"], []).append(z)
    bloecke, eintraege = [], []
    for person in sorted(je_person, key=lambda p: -len(je_person[p])):
        kacheln = []
        for z in sorted(je_person[person], key=lambda q: -q["start"]):
            i = len(eintraege)
            eintraege.append(z["datei"])
            wann = datetime.datetime.fromtimestamp(z["start"]) \
                .strftime("%d.%m. %H:%M")
            meta = " · ".join(str(t) for t in (
                z.get("camera"), z.get("lichtphase") or "?",
                z.get("blick") or "?"))
            mark = " markiert" if z["datei"] in markiert else ""
            src = ("/personlauf/bild/" + urllib.parse.quote(lauf_id)
                   + "/" + urllib.parse.quote(z["datei"]))
            kacheln.append(
                f'<div class="pl-k{mark}" id="plk_{i}" onclick="plKlick({i})">'
                f'<div class="pl-b"><img loading="lazy" src="{src}"></div>'
                f'<div class="pl-m">{wann}<br>{html.escape(meta)}</div>'
                '<div class="pl-s">WRONG</div></div>')
        bloecke.append(f"<h3>{html.escape(person)} "
                       f"({len(je_person[person])})</h3>"
                       f'<div class="pl-r">{"".join(kacheln)}</div>')
    return f"""<h2>Review the harvest</h2>
<p class="sub">Run {html.escape(lauf_id)} — click every image that is WRONG
(not this person, or unusable). A second click takes it back. Everything is
saved instantly; unmarked images count as approved.</p>
<div class="card"><a class="gtb" href="/personlauf">&larr; back to the
wizard</a> <span id="pl-stand" class="dim"></span>
<span style="float:right"><button class="gtb on" onclick="plFertig(this)">
Finish review — adopt approved images</button></span></div>
<style>
 .pl-r {{ display:flex; flex-wrap:wrap; gap:10px; }}
 .pl-k {{ width:170px; background:var(--karte,#303136); border-radius:8px;
         padding:8px; border:2px solid #3f9d55; cursor:pointer;
         position:relative; user-select:none; }}
 .pl-k.markiert {{ border-color:#e8b23c; }}
 .pl-k .pl-s {{ display:none; }}
 .pl-k.markiert .pl-s {{ display:block; position:absolute; top:40%; left:0;
   right:0; text-align:center; color:#e8b23c; font-weight:800;
   font-size:1.4rem; text-shadow:0 0 8px #000; transform:rotate(-14deg); }}
 .pl-b {{ width:154px; height:210px; display:flex; align-items:center;
         justify-content:center; background:rgba(0,0,0,.25);
         border-radius:6px; }}
 .pl-b img {{ max-width:100%; max-height:100%; border-radius:4px; }}
 .pl-m {{ font-size:.72rem; opacity:.75; line-height:1.35; margin-top:6px; }}
</style>
{"".join(bloecke)}
<script>
const PL_DATEIEN = {json.dumps(eintraege)};
const PL_LAUF = {json.dumps(lauf_id)};
function plZaehlen() {{
  document.getElementById('pl-stand').textContent =
    document.querySelectorAll('.pl-k.markiert').length +
    ' of {len(eintraege)} marked wrong';
}}
async function plFertig(btn) {{
  const n = document.querySelectorAll('.pl-k.markiert').length;
  if (!confirm('Finish the review? ' + ({len(eintraege)} - n) +
      ' images will be adopted as learning material, ' + n +
      ' rejected.')) return;
  btn.disabled = true;
  const r = await fetch('/personlauf/abnahme_fertig', {{ method: 'POST' }});
  if (r.ok) {{ location.href = '/personlauf'; return; }}
  btn.disabled = false;
}}
async function plKlick(i) {{
  const k = document.getElementById('plk_' + i);
  const neu = !k.classList.contains('markiert');
  await fetch('/personlauf/urteil', {{ method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ lauf_id: PL_LAUF, datei: PL_DATEIEN[i],
                            urteil: neu ? 'falsch' : 'ok' }}) }});
  k.classList.toggle('markiert', neu);
  plZaehlen();
}}
plZaehlen();
</script>"""


def _modell_karte(modell):
    """Kompakte Status-Karte (Wizard + Person-Seite, EINE Quelle)."""
    if not modell or not modell.get("bilder"):
        return ""
    wann = datetime.datetime.fromtimestamp(modell["ts"]) \
        .strftime("%d.%m. %H:%M")
    je = " · ".join(f"{html.escape(p)} {n}" for p, n in
                    sorted(modell.get("personen", {}).items(),
                           key=lambda kv: -kv[1]))
    return ('<div class="card"><b>Model status</b>'
            f'<div>trained {wann} in {modell.get("dauer_s", "?")} s — '
            f'{modell["bilder"]} images: {je} · '
            f'{html.escape(str(modell.get("modell", "")))} · '
            '<a href="/person/modell">details</a></div>'
            f'<div class="dim">Not armed yet: '
            f'{html.escape(str(modell.get("hinweis", "")))}</div></div>')


def bestand_seite(laeufe, modell=None):
    """PE2b (User 04.08., Anchors-Pendant): je Person das ABGENOMMENE
    Material ueber alle Laeufe — mit Einzelbild-Loeschung und
    Ganzer-Lauf-Loeschung (danach ist ein Re-Lauf jederzeit moeglich).
    Oben die Modell-Status-Karte (User: auch bei Person sichtbar)."""
    je_person = {}
    for lid, zeilen in laeufe:
        for z in zeilen:
            if "ausfall" in z or z.get("status") != "abgenommen":
                continue
            je_person.setdefault(z["person"], {}) \
                .setdefault(lid, []).append(z)
    teile = ["<h2>Person material — what has been learned</h2>",
             '<p class="sub">Approved full-body images per person, grouped '
             "by learning run. Delete a single image (&times; on the tile) "
             "or a whole run — a new run can always re-harvest afterwards. "
             "Deletions take effect on the next training.</p>",
             _modell_karte(modell)]
    if not je_person:
        teile.append('<div class="card"><b>No approved material yet</b>'
                     '<div class="dim">Run <a href="/personlauf">Person '
                     "learn</a> and finish the review — approved images "
                     "appear here.</div></div>")
        return "".join(teile)
    eintraege = []
    for person in sorted(je_person, key=lambda p: -sum(
            len(v) for v in je_person[p].values())):
        gesamt = sum(len(v) for v in je_person[person].values())
        teile.append(f"<h3>{html.escape(person)} ({gesamt})</h3>")
        for lid in sorted(je_person[person], reverse=True):
            zs = sorted(je_person[person][lid], key=lambda q: -q["start"])
            tage = sorted({z["tag"] for z in zs})
            kacheln = []
            for z in zs:
                i = len(eintraege)
                eintraege.append({"lauf_id": lid, "datei": z["datei"]})
                wann = datetime.datetime.fromtimestamp(z["start"]) \
                    .strftime("%d.%m. %H:%M")
                meta = " · ".join(str(t) for t in (
                    z.get("camera"), z.get("lichtphase") or "?",
                    z.get("blick") or "?"))
                src = ("/personlauf/bild/" + urllib.parse.quote(lid)
                       + "/" + urllib.parse.quote(z["datei"]))
                kacheln.append(
                    f'<div class="pm-k" id="pmk_{i}">'
                    f'<button class="pm-x" title="delete this image" '
                    f'onclick="pmBild({i})">&times;</button>'
                    f'<div class="pm-b"><img loading="lazy" src="{src}">'
                    f'</div><div class="pm-m">{wann}<br>{html.escape(meta)}'
                    "</div></div>")
            teile.append(
                f'<div class="card"><b>Run {html.escape(lid)}</b> '
                f'<span class="dim">{len(zs)} images · '
                f'{html.escape(", ".join(tage))}</span> '
                f'<button class="gtb" style="float:right" '
                # gleiche Quoting-Falle wie beim Discard-Knopf (User-Fund 04.08.)
                f'onclick="{html.escape(f"pmLauf({json.dumps(lid)})", quote=True)}">Delete this run'
                "</button>"
                f'<div class="pm-r" style="margin-top:8px">'
                f'{"".join(kacheln)}</div></div>')
    return "".join(teile) + f"""
<style>
 .pm-r {{ display:flex; flex-wrap:wrap; gap:10px; }}
 .pm-k {{ width:150px; position:relative; }}
 .pm-x {{ position:absolute; top:2px; right:2px; z-index:2; border:0;
   border-radius:50%; width:24px; height:24px; cursor:pointer;
   background:#8c3434; color:#fff; font-weight:700; }}
 .pm-b {{ width:150px; height:200px; display:flex; align-items:center;
   justify-content:center; background:rgba(0,0,0,.25); border-radius:6px; }}
 .pm-b img {{ max-width:100%; max-height:100%; border-radius:4px; }}
 .pm-m {{ font-size:.7rem; opacity:.75; line-height:1.3; margin-top:4px; }}
</style>
<script>
const PM = {json.dumps(eintraege)};
async function pmBild(i) {{
  if (!confirm('Delete this image from the learning material?')) return;
  const r = await fetch('/personlauf/loeschen', {{ method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify(PM[i]) }});
  if (r.ok) document.getElementById('pmk_' + i).remove();
}}
async function pmLauf(lid) {{
  if (!confirm('Delete ALL images of run ' + lid +
      '? A new run can re-harvest afterwards.')) return;
  const r = await fetch('/personlauf/loeschen', {{ method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ lauf_id: lid }}) }});
  if (r.ok) location.reload();
}}
</script>"""


def modell_seite(status, regeln=None):
    """PE3-Status als eigene Seite im Person-Bereich (User 04.08.:
    'Model status neben Person'). regeln = Standardwerte + Grenzen der
    Feuer-Regel (vom Handler aus core geliefert, kein Streu-Literal)."""
    regeln = regeln or {}
    teile = ["<h2>Person model — status</h2>",
             '<p class="sub">The body-recognition model, trained from your '
             "approved images. It retrains automatically after every "
             "finished review and after deletions.</p>"]
    if not status or not status.get("bilder"):
        teile.append('<div class="card"><b>No model yet</b>'
                     '<div class="dim">Run <a href="/personlauf">Person '
                     "learn</a> and finish a review — training starts "
                     "automatically afterwards.</div></div>")
        return "".join(teile)
    wann = datetime.datetime.fromtimestamp(status["ts"]) \
        .strftime("%a %d.%m. %H:%M")
    scharf = status.get("scharf")
    st = "border-spacing:14px 4px"
    fakten = "".join(
        f'<tr><td class="dim">{k}</td><td><b>{v}</b></td></tr>' for k, v in (
            ("Trained", wann),
            ("Training time", f'{status.get("dauer_s", "?")} s (CPU)'),
            ("Model", html.escape(str(status.get("modell", "")))),
            ("Images total", status["bilder"]),
            ("Persons", len(status.get("personen", {}))),
            ("Armed", "YES — live judging active" if scharf
             else "no — not armed yet"),
        ))
    teile.append(f'<div class="card"><b>Current model</b>'
                 f'<table style="{st}">{fakten}</table>'
                 f'<div class="dim">{html.escape(str(status.get("hinweis", "")))}'
                 "</div></div>")
    zeilen = "".join(
        f'<tr><td>{html.escape(p)}</td><td style="text-align:right">{n}'
        "</td><td style='text-align:right'>"
        f'{round(100 * n / max(1, status["bilder"]))}%</td></tr>'
        for p, n in sorted(status.get("personen", {}).items(),
                           key=lambda kv: -kv[1]))
    teile.append(
        f'<div class="card"><b>Learning material per person</b>'
        f'<table style="{st}">'
        '<tr><th style="text-align:left">person</th>'
        '<th style="text-align:right">approved images</th>'
        '<th style="text-align:right">share</th></tr>'
        f'{zeilen}<tr><td><b>total</b></td><td style="text-align:right"><b>'
        f'{status["bilder"]}</b></td><td></td></tr></table>'
        '<div class="dim">Manage the images under '
        '<a href="/person">Body images</a> — deletions retrain the model '
        "automatically.</div></div>")
    # .114: Schwelle (geeicht/eigen) + Feuer-Regel einstellbar
    gr = regeln.get("grenzen", {})
    eff_schwelle = status.get("schwelle") or regeln.get("schwelle_std", "?")
    quelle = status.get("schwelle_quelle") or "standard"
    quelle_txt = {"eichung": "measured on your material",
                  "user": "set by you",
                  "standard": "built-in default"}.get(quelle, quelle)
    ei = status.get("eichung")
    ei_txt = ""
    if ei:
        ei_txt = (f'<div class="dim">Measured by {ei.get("folds", "?")}-fold '
                  f'cross-validation over {ei.get("n", "?")} held-out images: '
                  "strongest confidence for a WRONG person "
                  f'{ei.get("fremd_max", "?")} &rarr; threshold '
                  f'{ei.get("schwelle", "?")}; '
                  f'{round(100 * (ei.get("getragen_anteil") or 0))}% of the '
                  "genuine images pass. Honest limit: this calibrates "
                  "BETWEEN your learned people — real strangers are not in "
                  "the material yet.</div>")

    def _feld(fid, label, wert, einheit=""):
        lo, hi = gr.get(fid, ("", ""))
        return (f'<tr><td class="dim">{label}</td>'
                f'<td><input id="pe-{fid}" type="number" size="6" '
                f'value="{wert}" min="{lo}" max="{hi}" '
                f'{"step=0.01" if fid == "schwelle" else ""}> {einheit} '
                f'<span class="dim">({lo}–{hi})</span></td></tr>')

    teile.append(
        '<div class="card"><b>Judgment settings</b>'
        f'<div>Decision threshold: <b>{eff_schwelle}</b> '
        f'<span class="dim">({quelle_txt})</span></div>' + ei_txt
        + f'<table style="{st}">'
        + _feld("schwelle", "Threshold",
                status.get("schwelle") if quelle == "user" else "")
        + _feld("fenster_s", "Fire window",
                status.get("fenster_s") or regeln.get("fenster_s", ""), "s")
        + _feld("feuer_ab", "Supporting events to fire",
                status.get("feuer_ab") or regeln.get("feuer_ab", ""))
        + _feld("karenz_s", "Cool-down after an alert",
                status.get("karenz_s") or regeln.get("karenz_s", ""), "s")
        + "</table>"
        '<div class="dim">Leave the threshold empty to follow the measured '
        "value automatically (it re-measures with every training). The fire "
        "rule: alert only after this many supporting events inside the "
        "window, then stay quiet for the cool-down.</div>"
        '<div style="margin-top:8px"><button class="gtb on" '
        'onclick="personRegeln(this)">Save settings</button> '
        '<span id="pe-status" class="dim"></span></div></div>'
        "<script>async function personRegeln(btn){btn.disabled=true;"
        "const d={};for(const k of['schwelle','fenster_s','feuer_ab',"
        "'karenz_s']){d[k]=document.getElementById('pe-'+k).value;}"
        "const r=await fetch('/person/einstellungen',{method:'POST',"
        "headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});"
        "const j=await r.json();document.getElementById('pe-status')"
        ".textContent=j.msg||'';if(j.ok){location.reload();}"
        "btn.disabled=false;}</script>")
    # PE4-Schalter (Aktivierungs-Gate): Arm/Disarm direkt hier
    teile.append(
        '<div class="card"><b>Live switch</b>'
        + ('<div>ARMED — the body path judges live events and may alert.'
           "</div>" if scharf else
           "<div>Not armed — the body path stays silent.</div>")
        + '<div class="dim">Alerts carry the note &quot;person recognition, '
          "not face&quot;. The decision threshold is not yet calibrated "
          "against stranger material — treat alerts as a preview and keep "
          "an eye on them.</div>"
        + '<div style="margin-top:8px"><button class="gtb'
        + ("" if scharf else " on")
        + f'" onclick="personSchalter({str(not scharf).lower()},this)">'
        + ("Disarm" if scharf else "Arm body recognition")
        + "</button></div></div>"
        + "<script>async function personSchalter(an,btn){btn.disabled=true;"
          "const r=await fetch('/person/schalter',{method:'POST',"
          "headers:{'Content-Type':'application/json'},"
          "body:JSON.stringify({scharf:an})});"
          "if(r.ok){location.reload();return;}"
          "const d=await r.json().catch(function(){return{};});"
          "alert(d.msg||('error '+r.status));btn.disabled=false;}</script>")
    return "".join(teile)
