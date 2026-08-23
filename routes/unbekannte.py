"""routes/unbekannte — persistente Unbekannt-Identitaeten /unbekannte (User
20.07.), ME1 byte-treu aus verifyd extrahiert (Schnappschuss-Beweis
scratchpad/me1_schnappschuss.py). Daten als Parameter: die Pool-Staende laedt
der Handler ueber anlernen.lade_* und reicht sie herein — kein Pool-/Store-
Zugriff im Renderer (Muster kameras/benachrichtigungen); numpy laedt lazy im
Render (Kohaerenz-Matrix). Sprachschicht unangetastet (unbekannte.*-Schluessel
seit Tranche B) — der Auszug fasst keine Texte an."""
import datetime
import html
import urllib.parse

import webui
from core.sprache import t


def render(idents_roh, gesichter, vors, personen):
    """-> Seiten-INHALT (Layout/Banner bleiben beim Handler).
    idents_roh = anlernen.lade_unbekannte() (roh, der Kaputt-Zeilen-Filter
    wohnt HIER) · gesichter = anlernen.lade_gesichter() · vors =
    anlernen.lade_unbekannt_vorschlaege() · personen = master_persons(cfg)."""
    import numpy as _np
    # kaputte Pool-Zeilen duerfen die Seite nie toeten (kc_phase34 R-2):
    # nur Dicts mit Listen-members kommen in die Darstellung
    idents = [u for u in idents_roh
              if isinstance(u, dict) and isinstance(u.get("members"), list)]
    faces = {g["id"]: g for g in gesichter}
    opts = "".join(f"<option>{html.escape(p)}</option>" for p in personen)

    def _info(u):
        mids = [m for m in u.get("members", []) if m in faces]
        if not mids:
            return None
        cams = {}
        for m in mids:
            c = str(faces[m].get("camera", "?"))
            cams[c] = cams.get(c, 0) + 1
        tss = [faces[m]["ts"] for m in mids]
        rep = max(mids, key=lambda m: faces[m].get("guete", 0))
        coh = 1.0
        if len(mids) > 1:
            M = _np.asarray([faces[m]["emb"] for m in mids], dtype=_np.float32)
            M = M / (_np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
            S = M @ M.T
            coh = float((S.sum() - len(mids)) / (len(mids) * (len(mids) - 1)))
        return {"u": u, "mids": mids, "cams": cams, "von": min(tss), "bis": max(tss),
                "rep": rep, "coh": coh, "n": len(mids)}

    infos = [i for i in (_info(u) for u in idents) if i]
    # Statische Objekte (Radkasten, Lichtflecken — Objekt-Regel des Reconcile,
    # 25.07.) raus aus den Personen-Eimern: sie sind keine Besucher und duerfen
    # nirgends als "Unknown N" zum Anlernen angeboten werden. Eigener Eimer
    # unten, damit sichtbar bleibt, WAS aussortiert wurde (kein stiller Verlust).
    objekte = [i for i in infos if i["u"].get("objekt")]
    infos = [i for i in infos if not i["u"].get("objekt")]
    aktiv = sorted((i for i in infos if i["u"].get("status", "aktiv") == "aktiv"),
                   key=lambda i: -i["bis"])
    besucher = [i for i in infos if i["u"].get("status") == "besucher"]
    wieder = [i for i in aktiv if i["n"] >= 2]
    einzeln = [i for i in aktiv if i["n"] == 1]

    def _tag(t0, t1):
        # Datums-Hardcodes (%d.%m., B19): bleiben Code, bis die
        # Format-Schluessel-Stufe (format.datum_*) gebaut ist.
        d0 = datetime.datetime.fromtimestamp(t0)
        d1 = datetime.datetime.fromtimestamp(t1)
        if d0.date() == d1.date():
            s = d0.strftime("%d.%m. %H:%M")
            return s if t1 - t0 < 60 else f"{s}–{d1.strftime('%H:%M')}"
        return f"{d0.strftime('%d.%m.')}–{d1.strftime('%d.%m.')}"

    def _unb_name(uid_):
        # Anzeige != Kennung (§8.2): die ID ("U3", anlernen vergibt
        # U+Ziffern) bleibt intern, die Anzeige kommt als Schluessel
        # mit {nummer} — wie auftritte.unbek.name (Tranche A).
        return t("unbekannte.name", nummer=uid_[1:])

    def _kachel(i, besuch=False):
        u = i["u"]
        uid = html.escape(u["id"], quote=True)
        name = html.escape(_unb_name(u["id"]))
        thumbs = "".join(
            f'<img src="/anlern/crops/{urllib.parse.quote(m)}.jpg" alt="">'
            for m in sorted(i["mids"], key=lambda m: -faces[m].get("guete", 0))[:6])
        if i["coh"] >= 0.55:
            sicher = f'<span class="badge ok">{t("unbekannte.badge_eine")}</span>'
        elif i["n"] > 1:
            # Format-Spezifikum (:.2f) vorformatiert (§8.8)
            _coh_txt = t("unbekannte.badge_aehnlich",
                                  wert=f'{i["coh"]:.2f}')
            sicher = f'<span class="badge">{_coh_txt}</span>'
        else:
            sicher = f'<span class="badge">{t("unbekannte.badge_einmal")}</span>'
        cams = " · ".join(f'{html.escape(c)} {n}'
                          for c, n in sorted(i["cams"].items(), key=lambda x: -x[1]))
        andere = "".join(
            f'<option value="{html.escape(j["u"]["id"], quote=True)}">'
            f'{html.escape(_unb_name(j["u"]["id"]))}</option>'
            for j in aktiv if j["u"]["id"] != u["id"])
        if besuch:
            akt = (f'<button class="gtb" onclick="unbBesucher(\'{uid}\',false,this)">'
                   f'{t("unbekannte.knopf_reaktivieren")}</button>')
        else:
            akt = (f'<input id="nm-{uid}" placeholder="{t("unbekannte.attr_name")}" list="pers-list">'
                   f'<button class="gtb on" onclick="unbBenennen(\'{uid}\',this)">{t("unbekannte.knopf_zuweisen")}</button>'
                   f'<button class="gtb" onclick="unbBesucher(\'{uid}\',true,this)">{t("unbekannte.knopf_ignorieren")}</button>'
                   + (f'<select id="mg-{uid}"><option value="">{t("unbekannte.opt_merge")}</option>{andere}</select>'
                      f'<button class="gtb" onclick="unbMerge(\'{uid}\',this)">{t("unbekannte.knopf_ok")}</button>' if andere else ''))
        return (
            f'<div class="uk" id="uk-{uid}">'
            f'<div class="uk-kopf">'
            f'<img class="uk-face" src="/anlern/crops/{urllib.parse.quote(i["rep"])}.jpg" alt="">'
            f'<div style="min-width:0"><div class="uk-titel">{name}</div>'
            f'<div class="uk-meta"><span class="num">{i["n"]}</span>{t("unbekannte.meta_zeit", zeit=_tag(i["von"], i["bis"]))}</div>'
            f'<div class="chips">{sicher}<span class="chip">{cams}</span></div></div></div>'
            f'<div class="streifen">{thumbs}</div>'
            f'<div class="uk-akt">{akt}</div></div>')

    vors_html = ""
    # Vorschlag MIT Gesichtern (User 25.07., Screenshot: "welche Person soll same
    # person sein?" — eine Gleiche-Person-Frage ohne Bilder ist nicht beantwortbar).
    # Je Seite bis zu drei Crops, dazwischen ein Trenner; erst dann die Knoepfe.
    _mitglieder = {u["id"]: (u.get("members") or []) for u in idents}
    def _merge_thumbs(uid_):
        return "".join(
            f'<img src="/anlern/crops/{urllib.parse.quote(str(m))}.jpg" alt="">'
            for m in _mitglieder.get(uid_, [])[:3])
    for a, b in vors:
        if a in [i["u"]["id"] for i in aktiv] and b in [i["u"]["id"] for i in aktiv]:
            vors_html += (
                f'<div class="merge"><span class="badge warn">{t("unbekannte.badge_gleiche")}</span>'
                f'<span class="merge-seite"><b>{html.escape(_unb_name(a))}</b>'
                f'<span class="merge-thumbs">{_merge_thumbs(a)}</span></span>'
                '<span class="merge-vs">↔</span>'
                f'<span class="merge-seite"><b>{html.escape(_unb_name(b))}</b>'
                f'<span class="merge-thumbs">{_merge_thumbs(b)}</span></span>'
                f'<button class="gtb on" onclick="unbMergePaar(\'{html.escape(a, quote=True)}\','
                f'\'{html.escape(b, quote=True)}\',this)">{t("unbekannte.knopf_merge")}</button>'
                f'<button class="gtb" onclick="unbVerwerfen(\'{html.escape(a, quote=True)}\','
                f'\'{html.escape(b, quote=True)}\',this)">{t("unbekannte.knopf_verschieden")}</button></div>')

    # Kopf-Prosa: an den <b>-Grenzen gesplittet; die fett zitierten
    # Woerter sind DIE Knopf-Labels selbst (dieselben Schluessel —
    # Anzeige und Erklaerung koennen nicht auseinanderlaufen).
    kopf = (f'<h2>{t("unbekannte.titel")}</h2>'
            f'<p class="sub">{t("unbekannte.kopf_satz")} '
            f'<b>{t("unbekannte.knopf_zuweisen")}</b>{t("unbekannte.kopf_satz_zuweisen")} '
            f'<b>{t("unbekannte.knopf_ignorieren")}</b>{t("unbekannte.kopf_satz_ignorieren")} '
            f'{t("unbekannte.kopf_satz_auto")}</p>'
            f'<p><button class="gtb on" onclick="anlernWartungJetzt(this)">{t("unbekannte.knopf_reorg")}</button> '
            f'<span style="color:var(--dim);font-size:13px">{t("unbekannte.hinweis_reorg")}</span></p>'
            f'<datalist id="pers-list">{opts}</datalist>')
    inhalt = kopf + vors_html
    if wieder:
        inhalt += (f'<h3>{t("unbekannte.h_wieder")}</h3><div class="ukliste">'
                   + "".join(_kachel(i) for i in wieder) + '</div>')
    if einzeln:
        inhalt += (f'<details class="mehr"><summary>{t("unbekannte.h_einzeln", n=len(einzeln))}</summary><div class="ukliste">'
                   + "".join(_kachel(i) for i in einzeln) + '</div></details>')
    if besucher:
        inhalt += (f'<details class="mehr"><summary>{t("unbekannte.h_besucher", n=len(besucher))}</summary><div class="ukliste">'
                   + "".join(_kachel(i, besuch=True) for i in besucher) + '</div></details>')
    if objekte:
        inhalt += (f'<details class="mehr"><summary>{t("unbekannte.h_objekte", n=len(objekte))}</summary>'
                   f'<p class="dim">{t("unbekannte.satz_objekte")}</p><div class="ukliste">'
                   + "".join(_kachel(i, besuch=True) for i in objekte) + '</div></details>')
    if not (wieder or einzeln or besucher):
        inhalt += webui.leer(t("unbekannte.leer"),
                             t("unbekannte.leer_hinweis"))
    return inhalt
