"""routes/gesichter — "Known people": Personen-/Referenzverwaltung (M1b/S5, byte-treu
aus verifyd extrahiert; Muster auftritte.py — Daten als Parameter, kein Dienst-Import).
Sprach-Stufe 0 (.294, konzept_sprache.md): sichtbare Texte kommen aus
core/sprache.t() gegen die en-Referenz — BYTE-TREU (Harnisch
tools/harnisch_sprache.py beweist identisches Render gegen den git-Basis-Stand)."""
import html
import os
import urllib.parse

from core.sprache import t


def render(personen, data_dir, gefiltert=False, alle=None, pruefung=None):
    """-> Seiten-INHALT (layout/banner bleiben beim Handler). personen = master_persons(cfg).

    .507 B4 (Faces -> Klick fuehrte ins Leere): bei ?person= reicht der Handler
    die geprueft Ein-Element-Liste herein und setzt gefiltert=True — dann steht
    der Weg zurueck ("show all faces") ganz oben und die Galerie VOR den
    personenunabhaengigen Karten (Upload/Import bleiben sichtbar, E-P11: wer
    aus dem Avatar-Gitter kommt, will zuerst die Bilder DIESER Person sehen).
    alle = volle Personenliste fuer das Auswahlfeld der Upload-Karte (None =
    wie personen). Die Karte ist personenunabhaengig; schruempfte ihr Feld
    still auf die gefilterte Person, verloere die Seite eine Faehigkeit, ohne
    es zu sagen (Fehlerklasse "stiller Verlust").

    .511 Stufe C: `pruefung` ist die Kopf-Tabelle des Bestands-Pruefers
    (refs_qs.json -> personen). Daraus stehen auf der Personen-Karte zwei
    Dinge: die Zahl der Entfernen-VORSCHLAEGE (mit Weg zum Check) und die
    Warnung "catalogue looks mixed", wenn mehr als die Haelfte der Bilder
    dieser Person naeher an einer fremden Person liegt als an ihr selbst.
    Beides ist Anzeige — auf DIESER Seite wird nichts vorgeschlagen und nichts
    angehakt, der Weg dahin ist der Quality-check-Knopf, den es schon gibt.
    Fehlt der Bericht (noch kein Lauf), bleibt die Karte wie bisher."""
    opts = "".join(f"<option>{html.escape(p)}</option>"
                   for p in (personen if alle is None else alle))

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
            # .507 B4/F3: eine Person kann dutzende Referenzen haben, die
            # volle Liste hunderte — bis .506 luden sie alle sofort (Hoehe
            # steht im style, der Umbruch bleibt also gleich).
            f'style="height:82px;border-radius:4px;display:block" loading="lazy">'
            f'<button class="gtb" style="font-size:10px;padding:0 6px;margin-top:2px" '
            f'onclick="refEntfernen(\'{_js(pp)}\',\'{_js(b)}\',this)">'
            f'{t("gesichter.galerie.knopf_entfernen")}</button></span>' for b in bil)
        _pe = (pruefung or {}).get(pp) or {}
        _marken = ""
        if _pe.get("vorschlag"):
            _marken += (
                f' &middot; <a class="dim" style="font-size:12px" '
                f'href="/qualitaet?person={urllib.parse.quote(pp)}">'
                f'{t("gesichter.galerie.vorschlag", n=int(_pe["vorschlag"]))}'
                f'</a>')
        if _pe.get("gemischt"):
            _marken += (' &middot; <span style="color:var(--crit);'
                        'font-size:12px">&#9888; '
                        + t("gesichter.galerie.gemischt") + '</span>')
        gal.append(
            # .507 B4: id= je Personenkarte — bis .506 hatte die Galerie keine
            # Sprungmarke, das #-Fragment von /faces lief deshalb ins Leere.
            f'<div class="card" id="p-{urllib.parse.quote(pp, safe="")}">'
            f'<b>{html.escape(pp)}</b> — '
            f'{t("gesichter.galerie.bildzahl", n=len(bil))}{_marken} &nbsp; '
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
    titel = f"<h2>{t('gesichter.titel')}</h2>"
    kopf = (f'<p><a class="gtb on" href="/lernlauf">'
            f'{t("gesichter.kopf.knopf_lernen")}</a> '
            f'<span class="dim">{t("gesichter.kopf.hinweis_lernen")}</span></p>'
            f"<p>{t('gesichter.kopf.satz')}</p>")
    if gefiltert:
        # .507 B4: der Weg zurueck steht VOR der Galerie — sonst sieht der
        # Nutzer einen Ausschnitt, ohne zu erkennen, dass es einer ist.
        return (titel
                + f'<p><a class="gtb" href="/gesichter">'
                  f'{t("gesichter.alle_zeigen")}</a></p>'
                + "".join(gal) + kopf + upload + frigate_import)
    return titel + kopf + upload + frigate_import + "".join(gal)
