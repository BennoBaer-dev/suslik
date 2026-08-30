"""routes/kameras — Kamera-Blatt: Discovery + verwenden + Zonen (Phase 2b;
Modulumbau R1, byte-treu aus verifyd extrahiert; Muster auftritte.py — Daten als
Parameter, kein Dienst-Import). Der Handler holt frigate_cameras() und reicht
cams/err + die zwei Config-Bloecke (Store-Kamerablatt, required_zones) herein;
hier wird NUR gerendert (layout/banner bleiben beim Handler).
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte kommen aus
core/sprache.t() gegen die en-Referenz — BYTE-TREU (Harnisch
tools/harnisch_sprache.py). Der Einleitungs-Absatz (sub) traegt Inline-Markup
mitten im Satz und bleibt deshalb bewusst literal (Stufe-0-Grenze: Plaintext-
Schluessel ohne HTML; Aufloesung kommt mit dem t_html-Weg spaeterer Stufen)."""
import html
import json

import webui

from core.sprache import t


def render(cams, err, kam_store, rz_cfg, steckbriefe=None):
    """-> Seiten-INHALT inkl. Fehlerbanner.
    steckbriefe (.368, User 29.08.): der Stream-Steckbrief-Cache je Kamera.
    Der Dienst ermittelt die Aufloesung seit .368 nur noch fuer Kameras OHNE
    Eintrag; hier steht der Stand und der Knopf, der ihn verwirft. Ohne den
    Parameter (Alt-Aufrufer) faellt der Block ersatzlos weg."""
    fehlerbanner = (f'<div class="banner">'
                    f'{t("kameras.banner.config_fehler", fehler=html.escape(str(err)))}'
                    f'</div>' if err else "")

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
                     f'data-cam="{nid}"{" checked" if verw else ""}> '
                     f'{t("kameras.karte.verwenden")}</label>')
        if cc["zones"]:
            zboxes = " ".join(
                f'<label class="zbox"><input type="checkbox" class="kam-zone" '
                f'data-cam="{nid}" value="{html.escape(z, quote=True)}"'
                f'{" checked" if z in zonen_akt else ""}> {html.escape(z)}</label>'
                for z in cc["zones"])
            zonen_ui = (f'<div class="zbar">{zboxes}'
                        f'<span class="dim">{t("kameras.karte.zonen_hinweis")}</span></div>')
        else:
            zonen_ui = f'<div class="zbar dim">{t("kameras.karte.zonen_keine")}</div>'
        res = f'{cc["width"]}×{cc["height"]}' if cc["width"] else "?"
        rec = t("kameras.karte.rec_an") if cc["record"] else t("kameras.karte.rec_aus")
        fen = ("" if cc["enabled"] else
               f' <span class="pill warn">{t("kameras.karte.pill_aus")}</span>')
        if not fen and not cc.get("detect_enabled", True):
            # Sichtkontrolle 12.08. (Realfall reiner Aufnahme-Klon): Frigate
            # faehrt auf diesem Stream KEINE Personen-Detektion — es koennen
            # hier nie Events ankommen. Quelle ist dieselbe Frigate-Config-
            # Ableitung wie das enabled-Badge (frigate_cameras), kein
            # eigenes Literal-Streufeld; die Checkbox bleibt bedienbar.
            fen = (f' <span class="pill warn" '
                   f'title="{t("kameras.karte.pill_keine_detektion_titel")}">'
                   f'{t("kameras.karte.pill_keine_detektion")}</span>')
        karten.append(
            f'<div class="card"><div class="kamhead"><b>{html.escape(name)}</b>{fen}'
            f'<span class="dim num">{res} · {rec}</span>{verwenden}</div>{zonen_ui}</div>')
    inhalt = (f'<h2>{t("kameras.titel")}</h2>'
              '<p class="sub">Read live from your Frigate config, nothing is hard-coded. '
              'Turn a camera <b>off</b> to stop looking for new faces on it; tick one or '
              'more <b>zones</b> to only analyze events that entered them (none ticked = '
              'all person events). Either way, if Frigate itself already claims a face, '
              'suslik still checks it, so Frigate\'s own mislabels never slip through. '
              '<a href="/kameras?refresh=1">Refresh</a>.</p>'
              + ("".join(karten) if cams else
                 webui.leer(t("kameras.leer.titel"),
                            t("kameras.leer.hinweis")))
              + (f'<p style="margin-top:1rem"><button class="gtb on" '
                 f'onclick="kamerasSpeichern(this)">{t("kameras.fuss.knopf_speichern")}</button> '
                 '<span id="kam-status" style="color:var(--dim)"></span></p>' if cams else "")
              + _steckbrief_block(cams, steckbriefe))
    return fehlerbanner + inhalt


def _steckbrief_block(cams, steckbriefe):
    """Stand der Stream-Angaben plus Auffrisch-Knopf (.368). Der Knopf verwirft
    den Cache; ermittelt wird beim naechsten Dienststart, weil das Proben
    Minuten dauern kann und nicht in einen Klick gehoert (auf einer Instanz mit
    unerreichbaren Kameras gemessen: 15 Kameras a ~30 s Timeout)."""
    if steckbriefe is None or not cams:
        return ""
    n_ok = sum(1 for k in cams if (steckbriefe.get(k) or {}).get("breite"))
    n_fehl = sum(1 for k in cams if (steckbriefe.get(k) or {}).get("fehler"))
    return ('<p style="margin-top:1.2rem" class="sub">'
            + t("kameras.steckbrief.hinweis")
            + f'<br><span class="dim num">'
            + t("kameras.steckbrief.stand", n=n_ok, ges=len(cams), fehler=n_fehl)
            + '</span><br><button class="gtb" id="kam-sb" '
              'onclick="steckbriefeNeu(this)">'
            + t("kameras.steckbrief.knopf") + '</button> '
              '<span id="kam-sb-status" style="color:var(--dim)"></span></p>'
              '<script>function steckbriefeNeu(b){'
              'b.disabled=true;'
              'document.getElementById("kam-sb-status").textContent='
            + json.dumps(t("kameras.steckbrief.laeuft"))
            + ';fetch("/kameras/steckbriefe_neu",{method:"POST"})'
              '.then(function(r){return r.json()}).then(function(d){'
              'document.getElementById("kam-sb-status").textContent='
              'd.ok?' + json.dumps(t("kameras.steckbrief.fertig")) + ':d.msg;'
              '}).catch(function(e){b.disabled=false;'
              'document.getElementById("kam-sb-status").textContent=""+e;});}</script>')
