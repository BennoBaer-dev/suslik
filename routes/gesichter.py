"""routes/gesichter — "Known people": Personen-/Referenzverwaltung (M1b/S5, byte-treu
aus verifyd extrahiert; Muster auftritte.py — Daten als Parameter, kein Dienst-Import)."""
import html
import os
import urllib.parse


def render(personen, data_dir):
    """-> Seiten-INHALT (layout/banner bleiben beim Handler). personen = master_persons(cfg)."""
    opts = "".join(f"<option>{html.escape(p)}</option>" for p in personen)

    def _js(s):        # JS-String-Kontext in onclick (s. Qualitaet-Route)
        return html.escape(s.replace("\\", "\\\\").replace("'", "\\'"), quote=True)
    gal = []
    for pp in personen:
        pdir = os.path.join(data_dir, "faces", pp)
        try:
            bil = sorted(f for f in os.listdir(pdir)
                         if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        except FileNotFoundError:
            bil = []
        thumbs = "".join(
            f'<span style="display:inline-block;text-align:center;margin:3px;vertical-align:top">'
            f'<img src="/refs/{urllib.parse.quote(pp)}/{urllib.parse.quote(b)}" '
            f'style="height:82px;border-radius:4px;display:block">'
            f'<button class="gtb" style="font-size:10px;padding:0 6px;margin-top:2px" '
            f'onclick="refEntfernen(\'{_js(pp)}\',\'{_js(b)}\',this)">'
            f'remove</button></span>' for b in bil)
        gal.append(
            f'<div class="card"><b>{html.escape(pp)}</b> — {len(bil)} images &nbsp; '
            f'<a class="gtb" href="/aehnliche?person={urllib.parse.quote(pp)}">'
            f'find matching faces</a> '
            f'<button class="gtb" style="color:var(--crit);border-color:var(--crit)" '
            f'onclick="personLoeschen(\'{_js(pp)}\',this)">Delete person…</button>'
            f'<div style="margin-top:8px">{thumbs or "<i>no images yet</i>"}</div></div>')
    upload = ("<div class='card'><b>Upload photo</b><br>"
              f"<select id='up-person'><option value=''>existing person…</option>{opts}</select> "
              "<input id='up-neu' placeholder='or new person' "
              "style='width:130px'> "
              "<input type='file' id='up-datei' accept='image/jpeg,image/png'> "
              "<button class='gtb' onclick='uploadRef()'>Upload</button> "
              "<span id='up-status' style='color:var(--dim)'></span><br>"
              "<small>New person: type the name into the free-text field. Gate: buffalo_l must find a "
              "face (otherwise an override prompt appears).</small></div>")
    return ("<h2>Known people</h2>"
            '<p><a class="gtb on" href="/lernlauf">Learn people</a> '
            '<span class="dim">guided learning run over your own recordings '
            "(foundation stage)</span></p>"
            "<p>All learned persons and their reference images. You can remove individual images, "
            "assign more from the unknown faces via the button per person, "
            "or upload a photo below, also for an entirely new person.</p>"
            + upload + "".join(gal))
