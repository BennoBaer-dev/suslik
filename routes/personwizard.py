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


def _wer_text(p):
    """.147: Anzeige-Name einer Lauf-Wahl — '' = alle, 'FREMD' = der
    reservierte Fremd-Sammel-Lauf, sonst der (escapte) Personenname."""
    if not p:
        return "all known people"
    if p == "FREMD":
        return "strangers"
    return html.escape(p)


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
        '<div style="margin-top:6px"><b>What makes the model strong:</b> '
        "variety beats volume. Images from <b>many different days</b> "
        "(outfits, light, cameras) help far more than many images from one "
        "walk — run the harvest again on new days rather than harvesting "
        "one day deeper. Confirmed stranger images sharpen the decision "
        "threshold the same way.</div>"
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
        wer = _wer_text((lauf or {}).get("person"))
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
        wer = _wer_text(lauf.get("person"))
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
            f'{_wer_text(lauf.get("person"))} '
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
        wer = _wer_text(lauf.get("person") or "the selected people")
        # .142: Fenster kommt aus der Frigate-Retention (personlauf.anlegen
        # schreibt fenster_tage in die Diagnose); der Fallback-Wert deckt nur
        # Alt-Zustaende vor .119 ohne Diagnose — EINE Quelle, kein Literal.
        from core.personlauf import FENSTER_FALLBACK_TAGE
        tage = dg.get("fenster_tage", FENSTER_FALLBACK_TAGE)
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
        # Verwaiste Labels ausweisen (Issue #18 Carl/Rose): Bestaetigungen
        # geloeschter Personen werden bewusst NICHT geerntet — sagen, nie still.
        vw = dg.get("verwaiste_labels") or {}
        vw_zeile = ""
        if vw:
            vw_zeile = ('<div class="dim">Skipped on purpose: '
                        + ", ".join(f"{html.escape(p)} ({n})" for p, n in vw.items())
                        + " — these names were deleted from your people; their old "
                          "confirmed events stay as history but are not harvested.</div>")
        teile.append(
            '<div class="card"><b>Run finished without images — here is why</b>'
            "<div>" + grund + "</div>" + vw_zeile
            + '<div class="dim">Nothing was changed; you can start another '
            "run below any time.</div></div>")
    elif phase == "fertig":
        vw = (lauf.get("diagnose") or {}).get("verwaiste_labels") or {}
        vw_zeile = ("" if not vw else
                    '<div class="dim">Skipped on purpose: '
                    + ", ".join(f"{html.escape(p)} ({n})" for p, n in vw.items())
                    + " — deleted people; their old confirmed events are not "
                      "harvested.</div>")
        fremd_zeile = ""
        if lauf.get("person") == "FREMD":
            fremd_zeile = (f'<div>{lauf.get("fremd_uebernommen", 0)} '
                           "confirmed stranger images moved into the "
                           "stranger pool — the next training uses them "
                           "right away.</div>")
        teile.append(
            '<div class="card"><b>Review finished — material adopted</b>'
            f'<div>{lauf.get("abgenommen", 0)} images approved as learning '
            f'material, {lauf.get("verworfen", 0)} rejected '
            f'(run {html.escape(str(lauf.get("lauf_id", "")))}).</div>'
            + fremd_zeile + vw_zeile
            + '<div class="dim">Training on the approved material ships with '
            "the next update — your review is stored and nothing needs to "
            "be repeated. You can start another run below any time.</div>"
            '<div style="margin-top:8px"><a class="gtb" '
            'href="/person">View the learned material</a>'
            "</div></div>")
    elif phase == "fehler":
        teile.append('<div class="card"><b>Last run failed</b>'
                     f'<div class="dim">{html.escape(str(lauf.get("fehler", "")))}'
                     "</div></div>")
    # Personen-Auswahl (User: gezielt EINE Person oder alle; .147 dazu der
    # reservierte FREMD-Lauf — Fremd-Kandidaten sammeln statt Bewohner)
    opts = (['<option value="">All known people</option>',
             '<option value="FREMD"'
             + (" selected" if person_wahl == "FREMD" else "")
             + ">Strangers — collect stranger images</option>"]
            + [f'<option value="{html.escape(p, quote=True)}"'
               f'{" selected" if p == person_wahl else ""}>'
               f"{html.escape(p)}</option>"
               for p in personen])
    teile.append('<div class="card"><b>Who to learn</b>'
                 f'<div><select id="pl-person">{"".join(opts)}</select></div>'
                 '<div class="dim">Pick one person to review in small, '
                 "focused batches — or all at once. People come from your "
                 "face collection; learning one at a time keeps the review "
                 "short.</div>"
                 '<div class="dim">Strangers: harvests walk-throughs where '
                 "nobody was recognized (street-only passes, unconfirmed "
                 "visitors). You confirm in the review which really are "
                 "strangers — they go into the stranger pool and sharpen "
                 "the decision threshold.</div></div>")
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
        wer = _wer_text(person_wahl)
        if b.get("gebunden") is None:
            zeile = (f'last {b["n"]} person events for {wer} — the binding '
                     "balance is computed when the run is created")
        else:
            zeile = (f'last {b["n"]} person events · <b>{b["gebunden"]}</b> '
                     f'can be tied to {wer} via confirmed walk-throughs'
                     + (f' · {b.get("fremd", 0)} stranger candidates'
                        if b.get("fremd") else ""))
        if person_wahl == "FREMD":
            erkl = ('<div class="dim">Candidates are walk-throughs where '
                    "nobody was recognized — street-only passes and "
                    "unconfirmed visitors. Everything is a SUSPICION until "
                    "your review; mark anyone who is NOT a stranger there."
                    "</div>")
        else:
            erkl = ('<div class="dim">Tying is conservative: only '
                    "walk-throughs with exactly one face-confirmed person "
                    "count. Everything you see afterwards can be rejected "
                    "with one click.</div>")
        teile.append(
            f'<div class="card"><b>Your selection</b><div>{zeile}</div>'
            + erkl + "</div>")
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
        bloecke.append(f"<h3>{'Strangers' if person == 'FREMD' else html.escape(person)} "
                       f"({len(je_person[person])})</h3>"
                       f'<div class="pl-r">{"".join(kacheln)}</div>')
    # .147: beim FREMD-Lauf dreht sich die Frage um — markiert wird, wer
    # KEIN Fremder ist; Unmarkiertes wird bestaetigter Fremder im Pool.
    if lauf.get("person") == "FREMD":
        frage = ("click every image that is NOT a stranger (a resident, a "
                 "known visitor) or unusable. A second click takes it back. "
                 "Everything is saved instantly; unmarked images are adopted "
                 "as confirmed strangers and sharpen the decision threshold.")
    else:
        frage = ("click every image that is WRONG (not this person, or "
                 "unusable). A second click takes it back. Everything is "
                 "saved instantly; unmarked images count as approved.")
    return f"""<h2>Review the harvest</h2>
<p class="sub">Run {html.escape(lauf_id)} — {frage}</p>
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


def kontrolle_seite(passe, sammeln):
    """Z8 (konzept_frames.md §7): Kontroll-Speicher der BEURTEILTEN Bilder —
    Kachel-Browser je Durchgang, mit Klasse, Score und Bildquelle daneben.
    View-only (v1): die Seite zeigt, was das Urteil gesehen hat, sie aendert
    nichts daran. Gruppiert wird je PASS, nie je Einzel-Event — nur im ganzen
    Durchgang laesst sich beurteilen, ob ein Urteil richtig war.

    passe   = core.personlive.kontrolle_lesen(...) (neueste zuerst)
    sammeln = Schalter diagnostic_collection; steuert nur den Erklaertext,
              nie den Inhalt (was da ist, wird gezeigt)."""
    modus = ("<b>Collect mode is ON</b> — every judged image is kept for 30 "
             "days so you can check the decisions later. Expect roughly "
             "20&ndash;40 MB a day."
             if sammeln else
             "<b>Lean mode (default)</b> — judged images only live while a "
             "pass is running; afterwards only the winning image and the "
             "verdict log below remain. This is the privacy-friendly "
             "default for a fresh installation.")
    kopf = ["<h2>Judged images</h2>",
            '<p class="sub">What body recognition actually looked at, one '
            "block per walk-through: the image it judged, the class it came "
            "out with, the score, and where the picture came from. Useful "
            "when a person was missed, or someone was recognized who "
            "should not have been.</p>",
            f'<div class="card">{modus}<div class="dim" '
            'style="margin-top:6px">Switch it under '
            '<a href="/konfiguration">Settings &rarr; Advanced</a>, key '
            "<code>diagnostic_collection</code>. Images and log expire "
            "together with the hit log after 30 days &mdash; nothing here "
            "is kept longer than the recognition record itself.</div></div>"]
    if not passe:
        kopf.append('<div class="card"><b>Nothing recorded yet</b>'
                    '<div class="dim">Entries appear once body recognition '
                    "is armed on <a href=\"/person/modell\">Model status</a> "
                    "and a person walks through.</div></div>")
        return "".join(kopf)
    bloecke = []
    for p in passe:
        wann = (datetime.datetime.fromtimestamp(p["start"]).strftime(
            "%d.%m. %H:%M") if p.get("start") else html.escape(p["pass_key"]))
        kacheln = []
        for z in p["zeilen"]:
            score = z.get("score")
            schwelle = z.get("schwelle")
            # Drei Zustaende, weil genau sie den Ausgang erklaeren: getroffen,
            # unter der Schwelle, oder als Fremder abgewiesen.
            if z.get("klasse") == "FREMD":
                kl, tag = "kz-fremd", "stranger"
            elif (score is not None and schwelle is not None
                  and score >= schwelle):
                kl, tag = "kz-hit", "above threshold"
            else:
                kl, tag = "kz-unter", "below threshold"
            uhr = (datetime.datetime.fromtimestamp(z["ts"]).strftime("%H:%M:%S")
                   if z.get("ts") else "")
            if z.get("bild"):
                src = ("/person/kontrolle/bild/"
                       + urllib.parse.quote(p["pass_key"]) + "/"
                       + urllib.parse.quote(z["datei"]))
                bild = f'<img loading="lazy" src="{src}">'
            else:
                bild = '<span class="dim">image expired</span>'
            kacheln.append(
                f'<div class="kz-k {kl}"><div class="kz-b">{bild}</div>'
                f'<div class="kz-m"><b>{html.escape(str(z.get("klasse") or "?"))}</b>'
                f' {score if score is not None else "?"}'
                f'<br>{tag}{f" &middot; thr {schwelle}" if schwelle is not None else ""}'
                f'<br>{uhr} &middot; {html.escape(str(z.get("quelle") or "?"))}</div></div>')
        bloecke.append(
            f'<h3>{wann} — {p["n"]} judged, {p["bilder"]} '
            f'{"image" if p["bilder"] == 1 else "images"} kept</h3>'
            f'<div class="kz-r">{"".join(kacheln)}</div>')
    stil = """<style>
 .kz-r { display:flex; flex-wrap:wrap; gap:10px; }
 .kz-k { width:150px; background:var(--karte,#303136); border-radius:8px;
         padding:8px; border:2px solid #4a4b52; }
 .kz-k.kz-hit { border-color:#3f9d55; }
 .kz-k.kz-unter { border-color:#6b6c74; }
 .kz-k.kz-fremd { border-color:#e8b23c; }
 .kz-b { width:134px; height:180px; display:flex; align-items:center;
         justify-content:center; background:rgba(0,0,0,.25);
         border-radius:6px; font-size:.72rem; text-align:center; }
 .kz-b img { max-width:100%; max-height:100%; border-radius:4px; }
 .kz-m { font-size:.72rem; opacity:.85; line-height:1.35; margin-top:6px; }
</style>"""
    return "".join(kopf) + stil + "".join(bloecke)


def _personen_tabelle(modell):
    """Kompakte Lern-Bilanz als erster, dazwischengeschobener Block der
    /person-Seite (User 07.08.: kleine Tabelle, Platz gut nutzen — WER ist
    gelernt, wie viele Bilder, Fremd-Klasse als eigene Zeile, Hinweis wenn
    0 Fremde, dazu welches Modell/welche Einstellung aktiv ist; Global-
    Unterschied als Zeile darunter, User-Entscheid 07.08.). Alle Zahlen
    kommen aus DEMSELBEN Status-Dict wie _modell_karte/modell_seite —
    eine Quelle, keine zweite Rechnung (.138-Lehre Bilanz-Zeile)."""
    if not modell or not modell.get("bilder"):
        return ""
    # .144 (User 07.08., Screenshot): KEINE <table> — style.css setzt
    # table width:100%, jede Zeile lief ueber die volle Seitenbreite mit
    # Leerraum in der Mitte. Stattdessen ein Grid, das je nach Breite
    # mehrere Spalten fuellt (mehrspaltig = Platz genutzt).
    _z = ('<div style="display:flex;justify-content:space-between;gap:12px;'
          'padding:2px 0;border-bottom:1px solid rgba(128,128,128,.2)">')
    zellen = "".join(
        f"{_z}<span>{html.escape(p)}</span><b>{n}</b></div>"
        for p, n in sorted(modell.get("personen", {}).items(),
                           key=lambda kv: -kv[1]))
    n_fremd = modell.get("fremd_bilder") or 0
    zellen += (f'{_z[:-2]};opacity:.75"><span>Strangers (extra class)</span>'
               f"<b>{n_fremd}</b></div>")
    raster = ('<div style="display:grid;grid-template-columns:'
              "repeat(auto-fit,minmax(190px,1fr));gap:2px 40px;"
              f'margin-top:6px">{zellen}</div>')
    hinweis = ""
    if not n_fremd:
        hinweis = ('<div style="color:var(--warn);margin-top:6px">'
                   "No stranger class yet — recognition works much better "
                   "with one: confirmed stranger images teach the model what "
                   "does NOT belong and calibrate the decision threshold."
                   "</div>")
    quelle = modell.get("schwelle_quelle") or "standard"
    quelle_txt = {"eichung": "measured", "user": "set by you",
                  "standard": "built-in default"}.get(quelle, quelle)
    schwelle = modell.get("schwelle")
    fakten_zellen = "".join(
        f'<div><span class="dim">{k}</span><br>{v}</div>' for k, v in (
            ("Active model", html.escape(str(modell.get("modell", "")))),
            ("Threshold", f"<b>{schwelle}</b> ({quelle_txt})"
             if schwelle else "—"),
            ("Armed", "<b>YES</b> — judging live" if modell.get("scharf")
             else "no — not armed"),
        ))
    fakten = ('<div style="display:grid;grid-template-columns:'
              "repeat(auto-fit,minmax(220px,1fr));gap:6px 40px;"
              f'margin-top:10px">{fakten_zellen}</div>')
    ei = modell.get("eichung") or {}
    konf = ei.get("verwechslung_max")
    konf_html = ""
    if konf is not None:
        konf_html = ('<div class="dim" style="margin-top:8px">Largest '
                     "cross-group confusion in the calibration: "
                     f"<b>{konf}</b> — the strongest score any image "
                     "reached for the WRONG group; the closer to 1, the "
                     "closer two groups are.</div>")
    return ('<div class="card"><b>Learned groups</b>'
            + raster + fakten + konf_html + hinweis + "</div>")


def _modell_karte(modell):
    """Kompakte Status-Karte (Wizard + Person-Seite, EINE Quelle).
    .141: der Vorsatz kommt aus dem ECHTEN scharf-Zustand — 'Not armed yet'
    stand hier als Festtext vor JEDEM Hinweis, auch bei scharfem Modell
    (Operator-Fund am Screenshot 06.08.). Ein Trainings-Fehlschlag steht
    ROT dabei (Panel-MUSS: nie den Alt-Stand als aktuell ausgeben)."""
    if not modell or not modell.get("bilder"):
        return ""
    wann = datetime.datetime.fromtimestamp(modell["ts"]) \
        .strftime("%d.%m. %H:%M")
    je = " · ".join(f"{html.escape(p)} {n}" for p, n in
                    sorted(modell.get("personen", {}).items(),
                           key=lambda kv: -kv[1]))
    vorsatz = ("Armed" if modell.get("scharf") else "Not armed yet")
    fehler = ""
    if modell.get("letzter_fehler"):
        fehler = ('<div style="color:var(--crit)">Last training attempt '
                  "FAILED: " + html.escape(str(modell["letzter_fehler"]))
                  + " — this card shows the previous model.</div>")
    return ('<div class="card"><b>Model status</b>'
            f'<div>trained {wann} in {modell.get("dauer_s", "?")} s — '
            f'{modell["bilder"]} images: {je} · '
            f'{html.escape(str(modell.get("modell", "")))} · '
            '<a href="/person/modell">details</a></div>'
            + fehler +
            f'<div class="dim">{vorsatz}: '
            f'{html.escape(str(modell.get("hinweis", "")))}</div></div>')


def bestand_seite(laeufe, modell=None, wer="", fremd=None):
    """PE2b (User 04.08., Anchors-Pendant): das ABGENOMMENE Material.
    .145 (User 07.08.): Galerie NACH PERSON statt nach Lauf ('mich
    interessiert nicht welcher Run'), Bilder NUR fuer die gewaehlte
    Gruppe (keine Bandwurmseite) und die Fremd-Bilder als eigener
    Eintrag (Ansicht; Pflege weiter ueber personlern/fremd/).
    wer   = gewaehlte Person, 'strangers' fuer den Fremd-Pool, ''=keine
    fremd = Dateinamen des Fremd-Pools (vom Handler gelistet)."""
    je_person = {}
    for lid, zeilen in laeufe:
        for z in zeilen:
            if "ausfall" in z or z.get("status") != "abgenommen":
                continue
            if z.get("person") == "FREMD":
                # .147: bestaetigte Fremde leben im POOL (Chip Strangers)
                # — die Lauf-Zeile bleibt nur Beleg/Bestands-Skip, sonst
                # stuende dasselbe Bild doppelt auf der Seite.
                continue
            je_person.setdefault(z["person"], []).append(
                dict(z, lauf_id=lid))
    fremd = fremd or []
    teile = ["<h2>Person material — what has been learned</h2>",
             '<p class="sub">Approved full-body images per person. Pick a '
             "group below to see its images; delete a single image "
             "(&times; on the tile) — a new run can always re-harvest "
             "afterwards. Deletions take effect on the next training.</p>",
             _personen_tabelle(modell),
             _modell_karte(modell)]
    if not je_person and not fremd:
        teile.append('<div class="card"><b>No approved material yet</b>'
                     '<div class="dim">Run <a href="/personlauf">Person '
                     "learn</a> and finish the review — approved images "
                     "appear here.</div></div>")
        return "".join(teile)
    # .141 (User-Vorgabe 06.08.: 'ganz deutlicher Hinweis, dass wir moeglichst
    # viele Daten brauchen'): der gemessene Hebel ist VIELFALT, nicht Menge —
    # mehr TAGE (Outfits, Licht) schlagen mehr Bilder desselben Durchgangs
    # (Prototyp-Messung: mehrtaegige Bloecke drueckten die Verwechslung von
    # 3/5 auf 1/5). Deshalb je Person Bilder+Tage+Kameras mit ehrlichem
    # Marker bei duenner Tage-Basis, dazu die Fremd-Erklaerung.
    teile.append(
        '<div class="card"><b>What makes this model strong</b>'
        '<div class="dim">Variety beats volume: images from <b>many '
        "different days</b> (outfits, light) help far more than many images "
        "from one walk. Aim for several days per person and let the "
        "harvest cover all your cameras.</div>"
        + (('<div class="dim" style="margin-top:4px"><b>Strangers:</b> '
            f'{modell.get("fremd_bilder", 0)} confirmed stranger images '
            "calibrate the decision threshold — the more strangers the "
            "model has seen, the more reliable that line is. "
            "(Collected in <code>personlern/fremd/</code>; a page for "
            "growing this set from your own street traffic is planned.)"
            "</div>") if modell else "")
        + "</div>")
    # Auswahl-Chips: eine Gruppe oeffnen statt alles untereinander
    # (Bandwurm); der Fremd-Pool haengt als eigener Eintrag hinten dran.
    namen = sorted(je_person, key=lambda p: -len(je_person[p]))
    chips = [
        f'<a class="gtb{" on" if wer == p else ""}" '
        f'href="/person?wer={urllib.parse.quote(p)}">'
        f"{html.escape(p)} ({len(je_person[p])})</a>"
        for p in namen]
    if fremd:
        chips.append(f'<a class="gtb{" on" if wer == "strangers" else ""}" '
                     f'href="/person?wer=strangers">Strangers '
                     f"({len(fremd)})</a>")
    teile.append('<div class="card"><b>Show images of</b>'
                 f'<div style="margin-top:6px">{" ".join(chips)}</div>'
                 '<div class="dim">Pick a group — its images open below, '
                 "newest first.</div></div>")
    eintraege = []
    if wer in je_person:
        zs = sorted(je_person[wer], key=lambda q: -q["start"])
        p_tage = sorted({z.get("tag") for z in zs if z.get("tag")})
        p_kams = {z.get("camera") for z in zs if z.get("camera")}
        marker = ""
        if len(p_tage) < 3:
            marker = (' <span style="color:var(--warn)">only '
                      f'{len(p_tage)} day{"s" if len(p_tage) != 1 else ""} — '
                      "recognition improves most with images from more days, "
                      "outfits and light</span>")
        kacheln = []
        for z in zs:
            i = len(eintraege)
            eintraege.append({"lauf_id": z["lauf_id"], "datei": z["datei"]})
            wann = datetime.datetime.fromtimestamp(z["start"]) \
                .strftime("%d.%m. %H:%M")
            meta = " · ".join(str(t) for t in (
                z.get("camera"), z.get("lichtphase") or "?",
                z.get("blick") or "?"))
            src = ("/personlauf/bild/" + urllib.parse.quote(z["lauf_id"])
                   + "/" + urllib.parse.quote(z["datei"]))
            kacheln.append(
                f'<div class="pm-k" id="pmk_{i}">'
                f'<button class="pm-x" title="delete this image" '
                f'onclick="pmBild({i})">&times;</button>'
                f'<div class="pm-b"><img loading="lazy" src="{src}">'
                f'</div><div class="pm-m">{wann}<br>{html.escape(meta)}'
                "</div></div>")
        teile.append(
            f"<h3>{html.escape(wer)} ({len(zs)})</h3>"
            f'<div class="dim">{len(zs)} images · {len(p_tage)} day'
            f'{"s" if len(p_tage) != 1 else ""} · {len(p_kams)} camera'
            f'{"s" if len(p_kams) != 1 else ""}{marker}</div>'
            f'<div class="pm-r" style="margin-top:8px">'
            f'{"".join(kacheln)}</div>')
    elif wer == "strangers" and fremd:
        # .146 (User: 'fremde muessen auch geloescht werden koennen'):
        # gleiche Kachel-Mechanik wie bei Personen — PM-Eintrag {"fremd":
        # datei}, derselbe pmBild-Knopf, derselbe Loesch-Endpunkt.
        kacheln = []
        for f in fremd:
            i = len(eintraege)
            eintraege.append({"fremd": f})
            kacheln.append(
                f'<div class="pm-k" id="pmk_{i}">'
                f'<button class="pm-x" title="delete this image" '
                f'onclick="pmBild({i})">&times;</button>'
                '<div class="pm-b"><img loading="lazy" '
                f'src="/personlauf/fremdbild/{urllib.parse.quote(f)}"></div>'
                f'<div class="pm-m">{html.escape(f)}</div></div>')
        teile.append(
            f"<h3>Strangers ({len(fremd)})</h3>"
            '<div class="dim">Confirmed stranger images — they train the '
            "extra class and calibrate the decision threshold. Deleting "
            "one retrains the model right away (files live in "
            "<code>personlern/fremd/</code>).</div>"
            f'<div class="pm-r" style="margin-top:8px">'
            f'{"".join(kacheln)}</div>')
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
    # .139/.141: gegen ECHTE Fremde geeicht oder nur zwischen den gelernten
    # Personen? Quelle sind EXPLIZITE Status-Felder (eichung.art +
    # fremd_trainiert), nie mehr das Text-Literal '+ strangers)' und nie
    # eine Negativ-Ableitung (.141 Panel: der vierte Zustand log, wenn die
    # Eichung aus einem ANDEREN Grund fehlte). Alt-Status vor .141 ohne die
    # Felder: einmalige Rueckfall-Ableitung.
    from core.personmodell import FREMD_MIN as _FREMD_MIN
    ei = status.get("eichung") or {}
    gegen_fremde = (ei.get("art") == "fremd" if "art" in ei
                    else "fremd_echt_max" in ei)
    ft = status.get("fremd_trainiert")
    if ft is None:                                 # Status aus .139/.140
        ft = str(status.get("modell", "")).endswith("+ strangers)")
    n_fremd = status.get("fremd_bilder") or 0
    if not n_fremd:
        fremd_txt = "none yet — threshold measured between your people only"
    elif not ft:
        fremd_txt = (f"{n_fremd} collected — {_FREMD_MIN} needed before "
                     "they are trained and calibrate the threshold")
    elif gegen_fremde:
        fremd_txt = (f"{n_fremd} in training · threshold calibrated against "
                     "real strangers")
    else:
        fremd_txt = (f"{n_fremd} in training — the threshold calibration "
                     "did not run (see the note below)")
    fakten = "".join(
        f'<tr><td class="dim">{k}</td><td><b>{v}</b></td></tr>' for k, v in (
            ("Trained", wann),
            ("Training time", f'{status.get("dauer_s", "?")} s (CPU)'),
            ("Model", html.escape(str(status.get("modell", "")))),
            ("Images total", status["bilder"]),
            ("Persons", len(status.get("personen", {}))),
            ("Stranger negatives", fremd_txt),
            ("Armed", "YES — live judging active" if scharf
             else "no — not armed yet"),
        ))
    # .141 Panel-MUSS: ein fehlgeschlagener Trainingslauf steht auf der Karte
    # (rot, mit Zeit), nicht nur im Container-Log — sonst wirkt der Alt-Stand
    # als aktuell und 'deletions retrain automatically' ist eine Luege.
    fehler_html = ""
    if status.get("letzter_fehler"):
        ft2 = datetime.datetime.fromtimestamp(
            status.get("letzter_fehler_ts") or 0).strftime("%d.%m. %H:%M")
        fehler_html = ('<div class="sa-crit" style="color:var(--crit)">'
                       f"Last training attempt FAILED ({ft2}): "
                       + html.escape(str(status["letzter_fehler"]))
                       + " — the model shown here is the previous one and "
                       "does not include your latest changes.</div>")
    teile.append(f'<div class="card"><b>Current model</b>'
                 f'<table style="{st}">{fakten}</table>'
                 + fehler_html +
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
    ei_txt = ""
    if ei and gegen_fremde:
        ei_txt = (f'<div class="dim">Measured by {ei.get("folds", "?")}-fold '
                  f'cross-validation over {ei.get("n", "?")} held-out images '
                  f'of your people plus {ei.get("n_fremd", "?")} confirmed '
                  "strangers: the strongest resident confidence any real "
                  f'stranger reached was {ei.get("fremd_echt_max", "?")} '
                  f'&rarr; threshold {ei.get("schwelle", "?")}; '
                  f'{round(100 * (ei.get("getragen_anteil") or 0))}% of the '
                  "genuine images pass. The other side of the coin: "
                  f'{ei.get("verwechslung_ueber_n", "?")} of your own images '
                  "would reach that threshold for the WRONG person "
                  f'(strongest {ei.get("verwechslung_max", "?")}).</div>')
    elif ei:
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
    # PE4-Schalter (Aktivierungs-Gate): Arm/Disarm direkt hier.
    # .141 Panel-SOLL: der Satz beschreibt die WIRKSAME Schwelle — hat der
    # User sie selbst gesetzt, darf hier nicht 'calibrated' stehen, waehrend
    # oben 'set by you' steht (drei Aussagen, eine Seite).
    if quelle == "user":
        schwelle_satz = (f"The decision threshold is set by you "
                         f"({eff_schwelle})"
                         + (f" — the calibration against {n_fremd} confirmed "
                            f'strangers would be {ei.get("schwelle")}'
                            if gegen_fremde and ei.get("schwelle") else "")
                         + ".")
    elif gegen_fremde:
        schwelle_satz = ("The decision threshold is calibrated against "
                         f"{n_fremd} confirmed stranger images.")
    else:
        schwelle_satz = ("The decision threshold is not yet calibrated "
                         "against stranger material — treat alerts as a "
                         "preview and keep an eye on them.")
    if ft:
        schwelle_satz += (" A body the model reads as a stranger is dropped "
                          "before it can become a hit.")
    teile.append(
        '<div class="card"><b>Live switch</b>'
        + ('<div>ARMED — the body path judges live events and may alert.'
           "</div>" if scharf else
           "<div>Not armed — the body path stays silent.</div>")
        + ('<div class="dim">Alerts carry the note &quot;person recognition, '
           "not face&quot;. " + schwelle_satz + "</div>")
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
