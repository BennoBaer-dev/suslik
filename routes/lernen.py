"""routes/lernen — Enroll-Seite: offene Vorschlaege + Referenz-Galerie + Upload (M1b/S5,
byte-treu aus verifyd extrahiert; Muster auftritte.py). Der Handler liefert die offenen
Queue-Eintraege (svc._enroll_queue bleibt beim Dienst) und haengt die Drift-Warnung ans
Layout; hier wird NUR gerendert."""
import datetime
import html
import os
import urllib.parse

import webui


def render(offen, personen, data_dir):
    """-> Seiten-INHALT. offen = sortierte offene Queue-Eintraege (neueste zuerst),
    personen = master_persons(cfg)."""
    opts = "".join(f"<option>{html.escape(p)}</option>" for p in personen)
    karten = []
    for d in offen:
        ed = str(d["eid"]).replace("/", "_")
        bild = (f'<img src="/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(d["datei"])}" '
                f'style="height:150px">')
        wann = datetime.datetime.fromtimestamp(d.get("ts", 0)).strftime("%d.%m. %H:%M")
        met = (f"score {d.get('score')} · novelty {d.get('nn_eigen', '—')} · "
               f"{d.get('bw')}×{d.get('bh')}px · front {d.get('front')} · sharp {d.get('sharp'):.0f}"
               if d.get("sharp") is not None else f"score {d.get('score')}")
        kid = html.escape(d["id"], quote=True)
        vid = (f' <a href="/video/{urllib.parse.quote(ed)}">&#9654; Video</a>'
               if any(os.path.isfile(os.path.join(data_dir, "clips", ed + s))
                      for s in ("_review.mp4", ".mp4")) else "")
        if d.get("person"):
            p = html.escape(d["person"])
            aktion = (f'<button class="gtb on" onclick="enroll(\'{kid}\',\'aufnehmen\',null,this)">'
                      f'Add as {p}</button>')
        else:
            aktion = (f'<select id="sel-{kid}"><option value="">as person…</option>{opts}</select> '
                      f'<input id="neu-{kid}" placeholder="or new person" '
                      f'> '
                      f'<button class="gtb" onclick="enrollFremd(\'{kid}\',this)">Add</button>')
        karten.append(
            f'<div class="card" data-fade-on-label=1><b>{html.escape(d.get("person") or "Unknown/Stranger")}'
            f'</b> · {wann} · {html.escape(str(d.get("camera", "?")))} · {met}'
            f'<div class="crops">{bild}{vid}</div>'
            f'<div>{aktion} <button class="gtb" onclick="enroll(\'{kid}\',\'ablehnen\',null,this)">'
            f'Reject</button></div></div>')
    galerie = []
    for p in personen:
        d = os.path.join(data_dir, "faces", p)
        bilder = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        thumbs = "".join(
            f'<img src="/refs/{urllib.parse.quote(p)}/{urllib.parse.quote(b)}" title="{html.escape(b)}" '
            f'style="height:56px;margin:2px;border-radius:4px">' for b in bilder[:60])
        galerie.append(f"<details><summary><b>{html.escape(p)}</b> — {len(bilder)} references</summary>"
                       f"<div style='margin:8px 0'>{thumbs}</div></details>")
    upload = ("<div class='card'><b>Upload your own photo into the Master</b><br>"
              f"<select id='up-person'><option value=''>existing person…</option>{opts}</select> "
              "<input id='up-neu' placeholder='or new person' "
              "style='width:130px'> "
              "<input type='file' id='up-datei' accept='image/jpeg,image/png'> "
              "<button class='gtb' onclick='uploadRef()'>Upload</button> "
              "<span id='up-status' style='color:var(--dim)'></span><br>"
              "<small>New person (e.g. Alex): type the name into the free-text field. Gate: buffalo_l "
              "must find a face (otherwise an override prompt appears). PNG is converted to JPEG. "
              "Upload several photos from different angles one after another.</small></div>")
    return ("<h2>Suggestions — people to enroll</h2>"
            + (f"<h3>Suggestions ({len(karten)})</h3>" + "".join(karten) if karten else
               webui.leer("No open enrollment suggestions.",
                          "Good new faces (large, sharp, frontal, confidently recognized or clearly a stranger) "
                          "appear here automatically after the analysis."))
            + "<h3>Reference stock (Master)</h3>" + "".join(galerie)
            + "<h3>Upload</h3>" + upload)
