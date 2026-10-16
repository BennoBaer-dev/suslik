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

from core import refquelle
from core.lernlauf import bild_url
from core.sprache import t


def _js(s):
    """JS-String-Kontext in onclick — das HAUSMUSTER (routes/gesichter.py,
    routes/aehnliche.py), nicht `html.escape` allein.

    .512 (Feldtester-Meldung 09.09., zweiter Fall derselben Klasse): die
    Vorschlags-Kennung traegt den PERSONENNAMEN woertlich
    (verifyd._enroll_uebernehmen: f"{eid}:{person}:{t}"), und `PERSON_RE`
    laesst genau ein gefaehrliches Zeichen zu — den Apostroph. `html.escape`
    macht daraus `&#x27;`; der HTML-Parser des Browsers dekodiert das im
    Attributwert zurueck, BEVOR der JS-Compiler die Zeile sieht. Der bekam dann
    (synthetisches Beispiel) `enroll('…:O'Test:10.3','ablehnen',null,this)` und
    brach mit SyntaxError ab: weder "Reject" noch "Add as …" feuerten, die Karte
    war fuer diese eine Person tot. Erst maskieren wir also fuer JS, dann fuer
    HTML. Probe: tools/proben/s11_k1_onclick_js.py."""
    return html.escape(s.replace("\\", "\\\\").replace("'", "\\'"), quote=True)


def render(offen, personen, data_dir):
    """-> Seiten-INHALT. offen = sortierte offene Queue-Eintraege (neueste zuerst),
    personen = master_persons(cfg)."""
    opts = "".join(f"<option>{html.escape(p)}</option>" for p in personen)
    karten = []
    for d in offen:
        # Stufe V1b (Bauplan analysen/bauplan_verbraucher_unbekannt.md, Entscheid 12): der Lernvorschlag ohne Person
        # (FREMD) ist abgebaut; alte offene Eintraege ohne Person bleiben in der Queue liegen und werden nicht gezeichnet.
        if not d.get("person"):
            continue
        ed = str(d["eid"]).replace("/", "_")
        # E3a-3 (Bauplan Referenz-Quelle einbauen): ein Vorschlag mit ref_id zeigt das Profilbild seines
        # Satzes (Lese-Stufe d), ein alter (J9) seinen Ausschnitt im Ereignis-Ordner.
        src = (bild_url(d["ref_id"], None) if d.get("ref_id")
               else f'/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(d.get("datei") or "")}')
        bild = (f'<img src="{html.escape(src)}" '
                f'style="height:150px">')
        wann = datetime.datetime.fromtimestamp(d.get("ts", 0)).strftime("%d.%m. %H:%M")
        met = (t("lernen.karte.metrik_voll", score=d.get("score"),
                 novelty=d.get("nn_eigen", "—"), bw=d.get("bw"), bh=d.get("bh"),
                 front=d.get("front"), sharp=f"{d.get('sharp'):.0f}")
               if d.get("sharp") is not None
               else t("lernen.karte.metrik_kurz", score=d.get("score")))
        kid = _js(d["id"])
        vid = (f' <a href="/video/{urllib.parse.quote(ed)}">&#9654; {t("lernen.karte.link_video")}</a>'
               if any(os.path.isfile(os.path.join(data_dir, "clips", ed + s))
                      for s in ("_review.mp4", ".mp4")) else "")
        p = html.escape(d["person"])
        aktion = (f'<button class="gtb on" onclick="enroll(\'{kid}\',\'aufnehmen\',null,this)">'
                  f'{t("lernen.karte.knopf_add_person", person=p)}</button>')
        karten.append(
            f'<div class="card" data-fade-on-label=1>'
            f'<b>{html.escape(d["person"])}'
            f'</b> · {wann} · {html.escape(str(d.get("camera", "?")))} · {met}'
            f'<div class="crops">{bild}{vid}</div>'
            f'<div>{aktion} <button class="gtb" onclick="enroll(\'{kid}\',\'ablehnen\',null,this)">'
            f'{t("lernen.karte.knopf_ablehnen")}</button></div></div>')
    # E3b-2a (Bauplan analysen/bauplan_refquelle_einbau.md, Stufe E3 Punkt 2): die Galerie sind die
    # Referenz-Saetze je Person aus der Referenz-Quelle (Lese-Stufe b, juengste Bindung zuerst), das Bild
    # ueber /lernlauf/satz/<ref_id> (Lese-Stufe d); kein Lesen von faces/.
    saetze = refquelle.read_catalog({"data_dir": data_dir})["personen"]
    galerie = []
    for p in personen:
        bilder = saetze.get(p, [])
        thumbs = "".join(
            f'<img src="{html.escape(bild_url(b, None))}" title="{html.escape(b)}" '
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
