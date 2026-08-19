"""routes/gesichter — "Known people": Personen-/Referenzverwaltung (M1b/S5, byte-treu
aus verifyd extrahiert; Muster auftritte.py — Daten als Parameter, kein Dienst-Import).
Sprach-Stufe 0 (.294, konzept_sprache.md): sichtbare Texte kommen aus
core/sprache.t() gegen die en-Referenz — BYTE-TREU (Harnisch
tools/harnisch_sprache.py beweist identisches Render gegen den git-Basis-Stand)."""
import html
import os
import urllib.parse

from core.sprache import t


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
            f'{t("gesichter.galerie.knopf_entfernen")}</button></span>' for b in bil)
        gal.append(
            f'<div class="card"><b>{html.escape(pp)}</b> — '
            f'{t("gesichter.galerie.bildzahl", n=len(bil))} &nbsp; '
            f'<a class="gtb" href="/aehnliche?person={urllib.parse.quote(pp)}">'
            f'{t("gesichter.galerie.knopf_aehnliche")}</a> '
            # .273c (User: Aufruf an mehreren Stellen, kontext-vorausgewaehlt):
            # startet den Bestands-Check und springt gefiltert auf die Person.
            f'<button class="gtb" onclick="qsPerson(\'{_js(pp)}\',this)">'
            f'{t("gesichter.galerie.knopf_qs")}</button> '
            f'<button class="gtb" style="color:var(--crit);border-color:var(--crit)" '
            f'onclick="personLoeschen(\'{_js(pp)}\',this)">'
            f'{t("gesichter.galerie.knopf_loeschen")}</button>'
            f'<div style="margin-top:8px">'
            f'{thumbs or "<i>" + t("gesichter.galerie.hinweis_leer") + "</i>"}</div></div>')
    upload = (f"<div class='card'><b>{t('gesichter.upload.titel')}</b><br>"
              f"<select id='up-person'><option value=''>"
              f"{t('gesichter.upload.attr_person')}</option>{opts}</select> "
              f"<input id='up-neu' placeholder='{t('gesichter.upload.attr_neu')}' "
              "style='width:130px'> "
              "<input type='file' id='up-datei' accept='image/jpeg,image/png'> "
              f"<button class='gtb' onclick='uploadRef()'>"
              f"{t('gesichter.upload.knopf')}</button> "
              "<span id='up-status' style='color:var(--dim)'></span><br>"
              f"<small>{t('gesichter.upload.hinweis')}</small></div>")
    frigate_import = (
        f"<div class='card'><b>{t('gesichter.import.titel')}</b><br>"
        f"<button class='gtb' onclick='gesImport(this)'>"
        f"{t('gesichter.import.knopf')}</button> "
        "<span id='ges-import-status' style='color:var(--dim)'></span><br>"
        f"<small>{t('gesichter.import.hinweis')}</small></div>")
    return (f"<h2>{t('gesichter.titel')}</h2>"
            f'<p><a class="gtb on" href="/lernlauf">'
            f'{t("gesichter.kopf.knopf_lernen")}</a> '
            f'<span class="dim">{t("gesichter.kopf.hinweis_lernen")}</span></p>'
            f"<p>{t('gesichter.kopf.satz')}</p>"
            + upload + frigate_import + "".join(gal))
