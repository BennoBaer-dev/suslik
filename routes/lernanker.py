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


def anker_detail_seite(s, kaputt=0):
    """.83: Detail-Ansicht EINES Clusters — alle Crops, klickbar zum Clip."""
    q = s.get("qualitaet") or {}
    lauf_id = (s.get("lauf") or {}).get("lauf_id", "")
    dim = q.get("eimer", "ok") not in ("ok",)
    mitglieder = sorted(s.get("mitglieder") or [],
                        key=lambda m: (-(m.get("det") or 0), str(m.get("datei"))))
    thumbs = "".join(_thumb(m, lauf_id, dim) for m in mitglieder)
    tage = q.get("tage_liste") or []
    spanne = f'{tage[0]} … {tage[-1]}' if len(tage) > 1 else (tage[0] if tage else "—")
    stil = ('<style>.anker-reihe{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}'
            '.anker-thumb{width:96px;height:96px;object-fit:cover;border-radius:4px}'
            '.anker-thumb.gedimmt{opacity:.45}'
            '.pill{display:inline-block;border:1px solid var(--rand,#8884);'
            'border-radius:10px;padding:0 8px;margin:0 4px 2px 0;font-size:.85em}'
            '.pill.dim{opacity:.6}</style>')
    return (stil + f'<h2>{html.escape(str(s.get("anker_id")))}</h2>'
            f'<div class="card">{_badge(q.get("eimer", "ok"), dim=dim)}'
            + _badge(f'{q.get("stuetz", 0)} faces ({q.get("stuetz_phys", "?")} physical)')
            + _badge(f'{q.get("durchgaenge", 0)} passes')
            + _badge(f'{q.get("tage", 0)} day(s): {spanne}')
            + _badge(f'margin {q.get("marge")}')
            + '<div class="dim">click a face to open its clip · '
              '<a href="/lernlauf/anker">back to all clusters</a></div>'
            + f'<div class="anker-reihe">{thumbs}</div></div>')


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
        karten.append(
            f'<div class="card"><b>{html.escape(str(s.get("anker_id")))}</b> {status_html} '
            + _badge(f'{q.get("stuetz", 0)} faces') + _badge(f'{q.get("durchgaenge", 0)} passes')
            + _badge(f'{q.get("tage", 0)} day(s): {spanne}')
            + _badge(", ".join(kams)) + _badge(f'margin {q.get("marge")}')
            + f'<div class="anker-reihe">{"".join(thumbs)}{mehr}</div></div>')
    stil = ('<style>.anker-reihe{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}'
            '.anker-thumb{width:72px;height:72px;object-fit:cover;border-radius:4px}'
            '.anker-thumb.gedimmt{opacity:.45}'
            '.pill{display:inline-block;border:1px solid var(--rand,#8884);'
            'border-radius:10px;padding:0 8px;margin:0 4px 2px 0;font-size:.85em}'
            '.pill.dim{opacity:.6}</style>')
    return (stil + "<h2>Anchor clusters</h2>"
            f'<div class="card">{len(saetze)} clusters from {ges} anchor-ready faces — '
            f'{ok_n} clean, {len(saetze) - ok_n} for review (dimmed, with the reason on the '
            'badge). Naming ships with the next update; nothing here changes recognition yet. '
            '<a href="/lernlauf">Back to the learning run</a>.</div>'
            + kopf_warn + "".join(karten))
