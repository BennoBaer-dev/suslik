"""routes/ereignisliste — die zwei Log-Listen /offen (Abend-Arbeitsliste) und
/ereignisse (Event-Tabelle mit Filtern), Modulumbau R1, byte-treu aus verifyd
extrahiert (Muster auftritte.py: log_path + Daten als Parameter, kein
Dienst-Import). gt_schnellpersonen/master_persons bleiben im Kern (dritter
Nutzer: /event/-Seite) und kommen als CALLABLES herein — modulplan §2c
(Callback-Injektion, nie Rueckimport) statt einer zweiten Quelle.
KAT_LABELS/KAT_FARBE kommen aus webui/bausteine (Helfer-Heimat, mit R1 dorthin
gezogen)."""
import datetime
import html
import json
import os
import urllib.parse

import webui
from core import areas as _areas_mod
from webui.bausteine import KAT_FARBE, KAT_LABELS, gt_leiste


def render_offen(cfg, log_path, qs, gt_schnellpersonen, master_persons):
    """-> Seiten-INHALT (layout/banner bleiben beim Handler)."""
    rows, gtmap = [], {}
    if os.path.exists(log_path):
        with open(log_path) as f:
            for l in f:
                try:
                    rows.append(json.loads(l))
                except Exception:
                    pass
    gtp = os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl")
    if os.path.exists(gtp):
        with open(gtp) as f:
            for l in f:
                try:
                    d = json.loads(l)
                    gtmap[d["eid"]] = d["label"]
                except Exception:
                    pass
    gt_schnell = gt_schnellpersonen(rows, cfg)
    andere = [p for p in master_persons(cfg) if p not in gt_schnell]
    by = {}
    for r in rows:                             # --once-Duplikate: letzter Eintrag gewinnt
        if r.get("eid"):
            by[r["eid"]] = r
    kand = [r for r in by.values()          # kategorien-agnostisch (Schema v1+v2, AP2)
            if r.get("faces_geprueft", r.get("faces", 0)) > 0 and not r.get("bestaetigt")
            and r["eid"] not in gtmap]      # #42 Teil B: gefilterte Zahl, faces-Fallback fuer Altzeilen
    # Zeitfenster-Kontext (User-Punkt 18.07.): wurde im ±3-min-Fenster auf
    # IRGENDEINER Kamera jemand bestaetigt? Nur ANZEIGE/Sortierung — kein
    # Verstecken (Postbote-waehrend-Gartenarbeit-Falle; echte Fusion = v1.1).
    bestaetigt_ts = [((r.get("start") or r.get("ts", 0)),
                      ", ".join(r.get("bestaetigt") or []), r.get("camera", "?"))
                     for r in by.values() if r.get("bestaetigt")]

    def _fenster_kontext(t):
        nahe = [(abs(t - bt), wer, cam) for bt, wer, cam in bestaetigt_ts
                if abs(t - bt) <= 180]
        if not nahe:
            return None
        _, wer, cam = min(nahe)
        return f"{wer} ({cam})"
    for r in kand:
        r["_kontext"] = _fenster_kontext(r.get("start") or r.get("ts", 0))
    # Issue #16: schwache Gesichter OHNE bestaetigten Kontext sind
    # fast immer Fehlausloeser — standardmaessig einklappen statt
    # den Nutzer zum Labeln zu bitten (?schwach=1 zeigt sie).
    zeige_schwach = (qs.get("schwach", ["0"])[0] == "1")
    schwach_n = 0
    if not zeige_schwach:
        schwach = [r for r in kand
                   if r.get("kategorie") == "unbekannt_schwach"
                   and not r.get("_kontext")]
        schwach_n = len(schwach)
        if schwach_n:
            sch_ids = {id(r) for r in schwach}
            kand = [r for r in kand if id(r) not in sch_ids]
    kand.sort(key=lambda r: (r["_kontext"] is not None,
                             -(r.get("start") or r.get("ts", 0))))
    # BLAETTERN (25.07.): vorher wurden ALLE Kandidaten gerendert — gemessen 564
    # Karten, 704 KB und rund 2800 Knoepfe auf einer Seite. Das ist keine Arbeitsliste
    # mehr, das ist eine Wand. 50 je Seite, dieselbe Groesse wie /ereignisse, damit
    # sich beide gleich anfuehlen.
    # Ehrliche Einschraenkung: geblaettert wird ueber die POSITION, nicht ueber einen
    # Zeitanker. Wer auf Seite 3 etwas labelt, verschiebt die Liste um einen Eintrag —
    # an der Seitengrenze kann dadurch beim naechsten Laden einer uebersprungen
    # erscheinen. Ein Zeitanker ginge hier nicht, weil zweistufig sortiert wird
    # (erst "hat Kontext im Zeitfenster", dann Zeit).
    offen_gesamt = len(kand)
    try:
        o_seite = max(1, int(qs.get("seite", ["1"])[0] or 1))
    except (ValueError, TypeError):
        o_seite = 1
    o_max = max(1, -(-offen_gesamt // 50))
    o_seite = min(o_seite, o_max)
    kand = kand[(o_seite - 1) * 50:o_seite * 50]
    cards = []
    for r in kand:
        eid = r["eid"]
        ed = eid.replace("/", "_")
        t = datetime.datetime.fromtimestamp(r.get("start") or r.get("ts", 0)).strftime("%d.%m %H:%M:%S")
        f = r.get("frigate") or {}
        ftxt = f"Frigate: {f.get('label')} {f['score']:.2f}" if f.get("label") and f.get("score") is not None else "Frigate: —"  # Frigate-Label bleibt wie geliefert
        ours = ", ".join(f"{p} {(v.get('max') or 0):+.2f}/{v.get('win3s', 0)}×" for p, v in
                         sorted((r.get("ours") or {}).items(),
                                key=lambda x: -(x[1].get("max") or 0))[:3]) or "—"
        edir = os.path.join(cfg["data_dir"], "events", ed)
        crop = ""
        if os.path.isdir(edir):
            jpgs = sorted((c for c in os.listdir(edir) if c.endswith(".jpg")),
                          key=lambda c: os.path.getsize(os.path.join(edir, c)), reverse=True)
            if jpgs:
                u = f"/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(jpgs[0])}"
                crop = f'<img src="{u}">'
        vid = (f' <a href="/video/{urllib.parse.quote(ed)}">&#9654; Video</a>'
               if any(os.path.isfile(os.path.join(cfg["data_dir"], "clips", ed + s))
                      for s in ("_review.mp4", ".mp4")) else "")
        gtb = gt_leiste(eid, gt_schnell, andere)
        ktx = (f' · <span style="color:var(--dim)">recognized in the same time window: '
               f'{html.escape(r["_kontext"])}</span>' if r.get("_kontext") else
               ' · <b style="color:var(--warn)">no confirmed recognition nearby</b>')
        cards.append(f"<div class=card data-fade-on-label=1>{t} · "
                     f"{html.escape(str(r.get('camera', '?')))} · "
                     f"{html.escape(ftxt)} · {r.get('faces_geprueft', r.get('faces', 0))} faces · best: {html.escape(ours)}{ktx}"
                     f"<div class=crops>{crop}{vid}</div><div>{gtb}</div></div>")
    _ol = lambda s, t: f'<a class="gtb" href="/offen?seite={s}">{t}</a>'
    o_blaettern = (" · ".join(
        ([_ol(o_seite - 1, "← newer")] if o_seite > 1 else []) +
        [f"Page {o_seite}/{o_max} ({offen_gesamt} open)"] +
        ([_ol(o_seite + 1, "older →")] if o_seite < o_max else []))
        if offen_gesamt > 50 else "")
    sch_hinweis = ""
    if schwach_n:
        sch_hinweis = (f'<p class="pnote">{schwach_n} weak-face event'
                       f'{"s" if schwach_n != 1 else ""} hidden — '
                       "likely no usable face (nothing confirmed "
                       'nearby either). <a href="/offen?schwach=1">'
                       "show them</a></p>")
    elif zeige_schwach:
        sch_hinweis = ('<p class="pnote">showing weak-face events too — '
                       '<a href="/offen">back to the worthwhile ones</a></p>')
    inhalt = (f"<h2>Open cases to label ({offen_gesamt})</h2>"
              "<p>Filled automatically: all events with faces that nobody confirmed "
              "and that you haven't labeled yet. Ones with nobody recognized nearby "
              "come first — those are the ones worth looking at. After labeling, the "
              "card fades and disappears on the next load.</p>" + sch_hinweis
              + (f'<p class="pnote">{o_blaettern}</p>' if o_blaettern else "")
              + ("".join(cards) if cards else
                 webui.leer("Nothing open — everything labeled.",
                            "New unconfirmed events with faces appear here automatically."))
              + (f'<p class="pnote">{o_blaettern}</p>' if o_blaettern else ""))
    return inhalt


def render_ereignisse(cfg, log_path, qs, gt_schnellpersonen, master_persons):
    """-> Seiten-INHALT (layout/banner bleiben beim Handler)."""
    by = {}
    if os.path.exists(log_path):
        with open(log_path) as f:
            for l in f:
                try:
                    r = json.loads(l)
                    if r.get("eid"):
                        by[r["eid"]] = r       # letzte Zeile pro Event gewinnt
                except Exception:
                    pass       # abgerissene Zeile (Crash mid-write) darf die UI nicht killen
    rows = sorted(by.values(), key=lambda r: -(r.get("start") or r.get("ts", 0)))
    f_kam = qs.get("kamera", [""])[0]
    f_per = qs.get("person", [""])[0]
    f_kat = qs.get("kategorie", [""])[0]
    f_tag = qs.get("tag", [""])[0]             # JJJJ-MM-TT
    if f_kam:
        rows = [r for r in rows if r.get("camera") == f_kam]
    if f_per:
        rows = [r for r in rows if f_per in (r.get("bestaetigt") or [])]
    if f_kat:
        rows = [r for r in rows if f_kat in (r.get("kategorie"), r.get("kategorie_v1"))]
    if f_tag:
        try:
            _d0 = datetime.datetime.strptime(f_tag, "%Y-%m-%d")
            t0 = _d0.timestamp()
            # Kalendertag statt fixer 86400 s (Review .54): an Zeitumstellungstagen
            # ist der lokale Tag 23/25 h — /heute rechnet kalendertaeglich, der
            # "Events analysed"-Link muss dieselbe Menge treffen.
            t1 = (_d0 + datetime.timedelta(days=1)).timestamp()
            rows = [r for r in rows if t0 <= (r.get("start") or r.get("ts", 0)) < t1]
        except ValueError:
            pass
    # Areas Stufe 1: Area = grober Filter (Kamera-Menge der Sicht), der Kamera-
    # Filter bleibt daneben (beide gesetzt = natuerliche Schnittmenge); die
    # Blaetter-Links tragen ?area= ueber _seitenlink automatisch mit. Anders als
    # auf /heute (Pass-AUSWAHL) filtert die Event-Liste je Zeile — eine Zeile
    # ist eine Kamera-Tatsache, kein Durchgangs-Urteil.
    _areas_e = _areas_mod.normalisieren(cfg.get("areas"))
    _ar_akt_e, _nk_e = _areas_mod.sicht_aufloesen(
        _areas_e, qs.get("area", [""])[0],
        {str(r.get("camera", "?")) for r in by.values()})
    _ar_werte = sorted(_areas_e) + ["Default"]
    if _nk_e is not None:
        rows = [r for r in rows if str(r.get("camera", "?")) in _nk_e]
    gesamt = len(rows)
    try:                                   # ?seite=abc riss sonst den Request-Thread ab
        seite = max(1, int(qs.get("seite", ["1"])[0] or 1))
    except (ValueError, TypeError):
        seite = 1
    rows = rows[(seite - 1) * 50: seite * 50]
    kameras = sorted({r.get("camera", "?") for r in by.values()})
    kats = sorted({k for r in by.values() for k in (r.get("kategorie"), r.get("kategorie_v1")) if k})
    def _opt(werte, aktiv, labels=None):   # labels: Slug->Anzeige (value bleibt der Slug/Filterwert)
        if labels is None:
            return "".join(f'<option{" selected" if w == aktiv else ""}>{html.escape(w)}</option>'
                           for w in werte)
        return "".join(f'<option value="{html.escape(w)}"{" selected" if w == aktiv else ""}>'
                       f'{html.escape(labels.get(w, w))}</option>' for w in werte)
    filterleiste = (
        '<form method="get" style="margin:8px 0">'
        + (f'<select name="area"><option value="">all areas</option>'
           f'{_opt(_ar_werte, _ar_akt_e, {w: w for w in _ar_werte})}</select> '
           if _areas_e else '')
        + f'<select name="kamera"><option value="">all cameras</option>{_opt(kameras, f_kam)}</select> '
        f'<select name="person"><option value="">all persons</option>'
        f'{_opt(master_persons(cfg), f_per)}</select> '
        f'<select name="kategorie"><option value="">all categories</option>{_opt(kats, f_kat, KAT_LABELS)}</select> '
        f'<input type="date" name="tag" value="{html.escape(f_tag)}" '
        '> '
        '<button class="gtb on">Filter</button> <a href="/ereignisse">reset</a></form>')
    def _seitenlink(n, txt):
        q = {k: v[0] for k, v in qs.items() if v and v[0]}
        q["seite"] = str(n)
        return f'<a href="/ereignisse?{urllib.parse.urlencode(q)}">{txt}</a>'
    blaettern = " · ".join(
        ([_seitenlink(seite - 1, "← newer")] if seite > 1 else []) +
        [f"Page {seite}/{max(1, -(-gesamt // 50))} ({gesamt} events)"] +
        ([_seitenlink(seite + 1, "older →")] if seite * 50 < gesamt else []))
    gt_schnell = gt_schnellpersonen(list(by.values()), cfg)
    andere = [p for p in master_persons(cfg) if p not in gt_schnell]
    gtmap = {}                                     # User-Labels: letzte Zeile pro eid gewinnt
    gtp = os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl")
    if os.path.exists(gtp):
        with open(gtp) as f:
            for l in f:
                try:
                    d = json.loads(l)
                    gtmap[d["eid"]] = d["label"]
                except Exception:
                    pass
    body = ["<h2>Events</h2>", filterleiste, f"<p>{blaettern}</p>",
            '<div class="tabelle-wrap"><table><tr><th>Time</th><th>Camera</th>'
            "<th>Frigate</th><th>suslik</th>",
            "<th>Category</th><th>Crop</th><th>Confirm or correct (GT)</th></tr>"]
    for r in rows:   # defensiv: alte/fremde Zeilen ohne heutige Pflichtfelder nicht crashen lassen
        t = datetime.datetime.fromtimestamp(r.get("start") or r.get("ts", 0)).strftime("%d.%m %H:%M:%S")
        f = r.get("frigate") or {}
        fs = f"{f['score']:.2f}" if f.get("score") is not None else "?"
        ftxt = f"{f.get('label')} {fs} (cos {f.get('cos')})" if f.get("label") else "—"
        ours = ", ".join(f"{p} {(v.get('max') or 0):+.2f}/{v.get('win3s', 0)}×" for p, v in
                         sorted((r.get("ours") or {}).items(),
                                key=lambda x: -(x[1].get("max") or 0))[:3]) or "—"
        ed = str(r.get("eid", "")).replace("/", "_")
        edir = os.path.join(cfg["data_dir"], "events", ed)
        crop = ""
        if ed and os.path.isdir(edir):
            jpgs = sorted((c for c in os.listdir(edir) if c.endswith(".jpg")),
                          key=lambda c: os.path.getsize(os.path.join(edir, c)), reverse=True)
            if jpgs:
                u = f"/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(jpgs[0])}"
                crop = f'<a href="{u}"><img src="{u}"></a>'
        k = str(r.get("kategorie", "?"))
        best = r.get("bestaetigt") or []
        lg = (f' <a href="/events/{urllib.parse.quote(ed)}/analyze.log" style="color:var(--accent)">log</a>'
              if ed and os.path.isfile(os.path.join(edir, "analyze.log")) else "")
        if ed and any(os.path.isfile(os.path.join(cfg["data_dir"], "clips", ed + s))
                      for s in ("_review.mp4", ".mp4")):
            lg += f' <a href="/video/{urllib.parse.quote(ed)}" style="color:var(--accent)">video</a>'
        eid = str(r.get("eid", ""))
        cur = gtmap.get(eid, "")
        gtb = gt_leiste(eid, gt_schnell, andere, cur) if eid else ""
        unv = (' <span title="clip incomplete — judged from the readable part">⚠</span>'
               if r.get("frames_fehlen") else "")     # W1-Telemetrie in der Liste
        body.append(f"<tr><td>{t}</td><td>{html.escape(str(r.get('camera', '?')))}</td>"
                    f"<td>{html.escape(ftxt)}</td><td>{html.escape(ours)}"
                    f"{' ✓' + html.escape(','.join(best)) if best else ''}</td>"
                    f"<td><span class=k style=background:{KAT_FARBE.get(k, '#666')}>{html.escape(KAT_LABELS.get(k, k))}</span>"
                    f"{' 📣' if r.get('alerted') else ''}{unv}{lg}</td><td>{crop}</td><td>{gtb}</td></tr>")
    body.append("</table>")
    return "".join(body) + "</table></div>"
