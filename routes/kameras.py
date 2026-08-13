"""routes/kameras — Kamera-Blatt: Discovery + verwenden + Zonen (Phase 2b;
Modulumbau R1, byte-treu aus verifyd extrahiert; Muster auftritte.py — Daten als
Parameter, kein Dienst-Import). Der Handler holt frigate_cameras() und reicht
cams/err + die zwei Config-Bloecke (Store-Kamerablatt, required_zones) herein;
hier wird NUR gerendert (layout/banner bleiben beim Handler)."""
import html

import webui


def render(cams, err, kam_store, rz_cfg):
    """-> Seiten-INHALT inkl. Fehlerbanner."""
    fehlerbanner = (f'<div class="banner">Could not read the Frigate config: '
                    f'{html.escape(str(err))}</div>' if err else "")

    def _eff(name, cc):                              # aktueller Zustand: Store, sonst Seed
        if name in kam_store:
            k = kam_store[name]
            return bool(k.get("verwenden", True)), list(k.get("zonen") or [])
        return bool(cc["enabled"]), list(rz_cfg.get(name) or [])

    karten = []
    for name in sorted(cams):
        cc = cams[name]
        verw, zonen_akt = _eff(name, cc)
        nid = html.escape(name, quote=True)
        verwenden = (f'<label class="sw"><input type="checkbox" class="kam-verw" '
                     f'data-cam="{nid}"{" checked" if verw else ""}> use this camera</label>')
        if cc["zones"]:
            zboxes = " ".join(
                f'<label class="zbox"><input type="checkbox" class="kam-zone" '
                f'data-cam="{nid}" value="{html.escape(z, quote=True)}"'
                f'{" checked" if z in zonen_akt else ""}> {html.escape(z)}</label>'
                for z in cc["zones"])
            zonen_ui = (f'<div class="zbar">{zboxes}'
                        '<span class="dim">none ticked = all events</span></div>')
        else:
            zonen_ui = '<div class="zbar dim">no zones defined in Frigate — all events</div>'
        res = f'{cc["width"]}×{cc["height"]}' if cc["width"] else "?"
        rec = "rec ✓" if cc["record"] else "no rec"
        fen = "" if cc["enabled"] else ' <span class="pill warn">off in Frigate</span>'
        if not fen and not cc.get("detect_enabled", True):
            # Sichtkontrolle 12.08. (Realfall reiner Aufnahme-Klon): Frigate
            # faehrt auf diesem Stream KEINE Personen-Detektion — es koennen
            # hier nie Events ankommen. Quelle ist dieselbe Frigate-Config-
            # Ableitung wie das enabled-Badge (frigate_cameras), kein
            # eigenes Literal-Streufeld; die Checkbox bleibt bedienbar.
            fen = (' <span class="pill warn" title="Frigate runs no person '
                   'detection on this stream &mdash; no events can arrive '
                   'here">no detection in Frigate</span>')
        karten.append(
            f'<div class="card"><div class="kamhead"><b>{html.escape(name)}</b>{fen}'
            f'<span class="dim num">{res} · {rec}</span>{verwenden}</div>{zonen_ui}</div>')
    inhalt = ('<h2>Cameras</h2>'
              '<p class="sub">Read live from your Frigate config, nothing is hard-coded. '
              'Turn a camera <b>off</b> to stop looking for new faces on it; tick one or '
              'more <b>zones</b> to only analyze events that entered them (none ticked = '
              'all person events). Either way, if Frigate itself already claims a face, '
              'suslik still checks it, so Frigate\'s own mislabels never slip through. '
              '<a href="/kameras?refresh=1">Refresh</a>.</p>'
              + ("".join(karten) if cams else
                 webui.leer("No cameras found in Frigate.",
                            "Check that suslik can reach the Frigate API."))
              + ('<p style="margin-top:1rem"><button class="gtb on" '
                 'onclick="kamerasSpeichern(this)">Save cameras</button> '
                 '<span id="kam-status" style="color:var(--dim)"></span></p>' if cams else ""))
    return fehlerbanner + inhalt
