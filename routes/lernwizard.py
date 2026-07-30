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
           max_events=40000):
    """Wizard-Ansicht. auswahl = Event-Zahl (int) oder None; alle=True bei ?events=alle;
    quelle 'gemessen'|'rueckfall' + gemessen_felder = WIRKLICH gemessene Konstanten
    (Teil-Kennung, Widerleger F3.1); bestaetigen_ab: ab dieser Zahl verlangt der
    Start-Knopf den Bestaetigungs-Dialog MIT den Schaetz-Zahlen (User-Wunsch 3)."""
    lage = ("B — existing references/unknowns will be extended"
            if personen_zahl else "A — cold start, no faces yet")
    teile = ["<h2>Learn people — guided run</h2>",
             '<p class="sub">Plans a learning run over your own recordings. '
             "Preparation and the face harvest run for real; grouping, naming and "
             "adoption ship in the next updates and will light up here.</p>",
             f'<div class="card"><b>Starting point</b><div>{html.escape(lage)}</div>'
             '<div class="dim">Clean-up switch for auto-collected unknowns: '
             "arrives with the naming stage.</div></div>"]
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
                q = ("fallback values — not yet measured here"
                     + (", measuring now …" if messung_laeuft else ""))
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
    "vorbereitung": ("checking events",),
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


def lauf_seite(zustand, anker_zahl=0, anker_kaputt=0):
    """Lauf-Seiten-Geruest: Phasen-Kette mit aktueller Phase, Zaehler, Resume-Hinweis.
    .86: 'working · updated Xs ago'-Puls — sichtbar, DASS gerechnet wird."""
    ph = zustand.get("phase")
    akt = zustand.get("aktualisiert")
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
    f = zustand.get("fortschritt") or {}
    st = str(f.get("status", ""))
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
        zeilen.append(f'<div class="phz">{mark} {html.escape(PHASEN_TEXT[p])}'
                      + (' <span class="dim">(current)</span>' if aktiv else "")
                      + det_html + "</div>")
    zugeordnet = {k for ks in _PHASEN_KEYS.values() for k in ks} | {"status"}
    rest = " · ".join(f"{k}: {f[k]}" for k in f if k not in zugeordnet)
    rest_html = f'<div class="dim">{html.escape(rest)}</div>' if rest else ""
    kaputt_html = (f' · <b>{anker_kaputt} unreadable lines counted</b>' if anker_kaputt else "")
    anker_link = (f' · <a href="/lernlauf/anker">view the {anker_zahl} anchor clusters</a>'
                  if anker_zahl else "")
    stil = ('<style>.phok{color:seagreen;font-weight:bold}'
            '.phz{margin:2px 0}.phdet{margin:0 0 4px 1.4em;font-size:.9em}</style>')
    # .88: den Nutzer ZUM ERGEBNIS fuehren — ohne diesen Block wuesste
    # niemand, dass die Bilder unter Anchors liegen.
    erfolg = ""
    if anker_fertig and anker_zahl:
        erfolg = (f'<div class="card"><b><span class="phok">&#10003;</span> Grouping done</b> '
                  f'— {anker_zahl} face cluster{"s" if anker_zahl != 1 else ""} ready: '
                  f'<a class="gtb on" href="/lernlauf/anker">View the anchor clusters</a></div>')
    return (stil + "<h2>Learning run</h2>" + erfolg +
            f'<div class="card"><b>Phases</b>{"".join(zeilen)}'
            '<div class="dim">Preparation, Harvest and Grouping run for real in this '
            "build — Naming and the later phases activate with the coming updates.</div></div>"
            f'<div class="card"><b>Progress</b>'
            f'<div>{html.escape(st) if st else "—"}</div>{puls}{rest_html}'
            f'<div class="dim">anchors so far: {anker_zahl}{anker_link}{kaputt_html} · created '
            f'{_dt(zustand.get("ts"))} · scope {zustand.get("events", "?")} events · '
            "survives restarts (resume built in)</div></div>"
            + ('<p><a class="gtb on" href="/lernlauf?neu=1">Start a new run</a> '
               '<span class="dim">this run stays — its anchors remain available</span></p>'
               if anker_fertig else
               '<p><button class="gtb" onclick="lernlaufAbbruch(this)">Abort run</button> '
               '<span id="ll-status" class="dim"></span></p>'))
