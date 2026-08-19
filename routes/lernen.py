"""routes/lernen — Enroll-Seite: offene Vorschlaege + Referenz-Galerie + Upload (M1b/S5,
byte-treu aus verifyd extrahiert; Muster auftritte.py). Der Handler liefert die offenen
Queue-Eintraege (svc._enroll_queue bleibt beim Dienst) und haengt die Drift-Warnung ans
Layout; hier wird NUR gerendert.
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte kommen aus core/sprache.t()
gegen die en-Referenz — BYTE-TREU (Harnisch tools/harnisch_sprache.py)."""
import datetime
import html
import os
import urllib.parse

import webui

from core.sprache import t


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
        met = (t("lernen.karte.metrik_voll", score=d.get("score"),
                 novelty=d.get("nn_eigen", "—"), bw=d.get("bw"), bh=d.get("bh"),
                 front=d.get("front"), sharp=f"{d.get('sharp'):.0f}")
               if d.get("sharp") is not None
               else t("lernen.karte.metrik_kurz", score=d.get("score")))
        kid = html.escape(d["id"], quote=True)
        vid = (f' <a href="/video/{urllib.parse.quote(ed)}">&#9654; {t("lernen.karte.link_video")}</a>'
               if any(os.path.isfile(os.path.join(data_dir, "clips", ed + s))
                      for s in ("_review.mp4", ".mp4")) else "")
        if d.get("person"):
            p = html.escape(d["person"])
            aktion = (f'<button class="gtb on" onclick="enroll(\'{kid}\',\'aufnehmen\',null,this)">'
                      f'{t("lernen.karte.knopf_add_person", person=p)}</button>')
        else:
            aktion = (f'<select id="sel-{kid}"><option value="">'
                      f'{t("lernen.karte.attr_person")}</option>{opts}</select> '
                      f'<input id="neu-{kid}" placeholder="{t("lernen.karte.attr_neu")}" '
                      f'> '
                      f'<button class="gtb" onclick="enrollFremd(\'{kid}\',this)">'
                      f'{t("lernen.karte.knopf_add")}</button>')
        karten.append(
            f'<div class="card" data-fade-on-label=1>'
            f'<b>{html.escape(d.get("person") or t("lernen.karte.unbekannt"))}'
            f'</b> · {wann} · {html.escape(str(d.get("camera", "?")))} · {met}'
            f'<div class="crops">{bild}{vid}</div>'
            f'<div>{aktion} <button class="gtb" onclick="enroll(\'{kid}\',\'ablehnen\',null,this)">'
            f'{t("lernen.karte.knopf_ablehnen")}</button></div></div>')
    galerie = []
    for p in personen:
        d = os.path.join(data_dir, "faces", p)
        bilder = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        thumbs = "".join(
            f'<img src="/refs/{urllib.parse.quote(p)}/{urllib.parse.quote(b)}" title="{html.escape(b)}" '
            f'style="height:56px;margin:2px;border-radius:4px">' for b in bilder[:60])
        galerie.append(f"<details><summary><b>{html.escape(p)}</b> — "
                       f"{t('lernen.galerie.bildzahl', n=len(bilder))}</summary>"
                       f"<div style='margin:8px 0'>{thumbs}</div></details>")
    upload = (f"<div class='card'><b>{t('lernen.upload.titel')}</b><br>"
              f"<select id='up-person'><option value=''>"
              f"{t('lernen.upload.attr_person')}</option>{opts}</select> "
              f"<input id='up-neu' placeholder='{t('lernen.upload.attr_neu')}' "
              "style='width:130px'> "
              "<input type='file' id='up-datei' accept='image/jpeg,image/png'> "
              f"<button class='gtb' onclick='uploadRef()'>{t('lernen.upload.knopf')}</button> "
              "<span id='up-status' style='color:var(--dim)'></span><br>"
              f"<small>{t('lernen.upload.hinweis')}</small></div>")
    return (f"<h2>{t('lernen.titel')}</h2>"
            + (f"<h3>{t('lernen.kopf.titel_offen', n=len(karten))}</h3>" + "".join(karten)
               if karten else
               webui.leer(t("lernen.leer.titel"),
                          t("lernen.leer.hinweis")))
            + f"<h3>{t('lernen.galerie.titel')}</h3>" + "".join(galerie)
            + f"<h3>{t('lernen.upload.titel_abschnitt')}</h3>" + upload)
