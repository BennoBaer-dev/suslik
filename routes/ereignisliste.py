"""routes/ereignisliste — die Log-Liste /ereignisse (Event-Tabelle mit Filtern),
Modulumbau R1, byte-treu aus verifyd extrahiert. Die zweite Liste /offen
(Abend-Arbeitsliste, render_offen) ist mit Bauplan analysen/bauplan_benennen.md,
Stufe BN3 entfallen; die Adresse leitet auf /unbekannte um, der Code bleibt in git.
Muster auftritte.py: log_path + Daten als Parameter, kein Dienst-Import. gt_schnellpersonen/master_persons bleiben im Kern (dritter
Nutzer: /event/-Seite) und kommen als CALLABLES herein — modulplan §2c
(Callback-Injektion, nie Rueckimport) statt einer zweiten Quelle.
KAT_LABELS/KAT_FARBE kommen aus webui/bausteine (Helfer-Heimat, mit R1 dorthin
gezogen).
Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe (siehe
Abschnitts-Kommentar in core/texte/en.py): Produktnamen-Kopfzellen bleiben
literal; die Kategorie-ANZEIGE laeuft seit Tranche D ueber
bausteine.kat_map()/akte_kat_wort() (Kennung/Anzeige-Trennung, EN wortgleich zu
KAT_LABELS); die frueheren Zeitvariablen `t` sind umbenannt, damit sie t()
nicht verschatten."""
import datetime
import html
import json
import os
import urllib.parse

import szenarien
from core import areas as _areas_mod
from core import harvest_set as _hs
from core.lernlauf import bild_url
from core.sprache import t
from webui.bausteine import KAT_FARBE, akte_kat_wort, akte_live_name, bild_nn, gt_leiste, kat_map
from core import logbuch as _logbuch
_log = _logbuch.logger(__name__)



def _bild_url(ed, name):
    return f"/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(name)}"


def crop_zellen(cfg, ed, edir, bestaetigt, hinweis_leer):
    """Crop-Spalte der Events-Liste (.313, Tester-Fund 21.08.: die Zelle zeigte
    die GROESSTE JPG des Event-Ordners — bei kleinen Gesichtern ist das das
    Kontextbild (_show_), auf dem eine ganz andere Person im Vordergrund
    steht; neben dem Haken fuer zwei bestaetigte Namen stand so das Kind von
    hinten). Jetzt: je BESTAETIGTER Person ihr bestes Gesichts-Crop
    (_best_<Person>_, hoechster NN-Score), mit Namen darunter, Klick oeffnet
    das Kontextbild (_show_) oder das Crop selbst; ohne Bestaetigung das
    Gesichts-Crop mit dem hoechsten Score, sonst das Unbekannt-Gesicht
    (_enroll_), sonst ein Hinweis statt einer leeren Zelle. Koerper-Crops
    (koerper_*.png) nie. -> HTML der Zelle."""
    if not ed or not os.path.isdir(edir):
        return f'<span class="dim" title="{html.escape(hinweis_leer)}">—</span>'
    dateien = os.listdir(edir)
    best = [c for c in dateien if "_best_" in c and c.endswith(".jpg")]
    show = [c for c in dateien if "_show_" in c and c.endswith(".jpg")]

    def _score(c):
        return bild_nn(c) if bild_nn(c) is not None else -9.0

    # E3a-3 (Bauplan Referenz-Quelle einbauen): seit der Referenz-Quelle liegen das beste Gesicht je
    # Person und die Kandidaten als Saetze vor (kandidaten.jsonl, ref_id, Bild ueber Lese-Stufe d);
    # Ereignisse vor dieser Version zeigen weiter ihre _best_- und _enroll_-Dateien.
    # Gelesen wird die Datei nur fuer neue Ereignisse (ohne _best_-Datei), die alten zeigen wie bisher.
    kand_z, best_z = _hs.event_rows(edir) if not best else ([], {})
    satz_best = {p: z for p, z in best_z.items() if z.get("ref_id")}

    def _kachel(datei, person=None, src=None):
        ziel = datei
        if person is not None:
            kand = sorted((c for c in show if f"_show_{person}_" in c), key=_score)
            if kand:
                ziel = kand[-1]
        bild_src = src or _bild_url(ed, datei)
        link = _bild_url(ed, ziel) if ziel != datei or src is None else src
        bild = (f'<a href="{link}"><img src="{bild_src}" '
                f'alt="{html.escape(person or "")}"></a>')
        if person:
            bild += f'<div class="dim" style="font-size:11px">{html.escape(person)}</div>'
        return f'<div style="display:inline-block;text-align:center;margin-right:6px">{bild}</div>'

    def _satz_kachel(z, person=None):
        return _kachel(z["ref_id"], person, src=bild_url(z["ref_id"], None))
    zellen = []
    for person in bestaetigt[:3]:
        kand = sorted((c for c in best if f"_best_{person}_" in c), key=_score)
        if kand:
            zellen.append(_kachel(kand[-1], person))
        elif person in satz_best:
            zellen.append(_satz_kachel(satz_best[person], person))
    if not zellen and best:
        zellen.append(_kachel(sorted(best, key=_score)[-1]))
    if not zellen and satz_best:
        zellen.append(_satz_kachel(max(satz_best.values(), key=lambda z: z.get("score") or -9.0)))
    if not zellen:
        enroll = sorted(c for c in dateien if "_enroll_" in c and c.endswith(".jpg"))
        if enroll:
            zellen.append(_kachel(enroll[0]))
        elif any(z.get("ref_id") for z in kand_z):
            zellen.append(_satz_kachel(next(z for z in kand_z if z.get("ref_id"))))
    if not zellen:
        return f'<span class="dim" title="{html.escape(hinweis_leer)}">—</span>'
    return "".join(zellen)

def render_ereignisse(cfg, log_path, qs, gt_schnellpersonen, master_persons):
    """-> Seiten-INHALT (layout/banner bleiben beim Handler)."""
    by = {}
    if os.path.exists(log_path):
        with open(log_path) as f:
            for l in f:
                try:
                    r = json.loads(l)
                    if r.get("eid"):
                        by[r["eid"]] = r       # letzte Zeile pro Event gewinnt
                except Exception:
                    _logbuch.swallowed(_log, _logbuch.WARNING, "ignored")       # abgerissene Zeile (Crash mid-write) darf die UI nicht killen
    rows = sorted(by.values(), key=lambda r: -(r.get("start") or r.get("ts", 0)))
    f_kam = qs.get("kamera", [""])[0]
    f_per = qs.get("person", [""])[0]
    f_kat = qs.get("kategorie", [""])[0]
    f_tag = qs.get("tag", [""])[0]             # JJJJ-MM-TT
    if f_kam:
        rows = [r for r in rows if r.get("camera") == f_kam]
    if f_per:
        rows = [r for r in rows if f_per in (r.get("bestaetigt") or [])]
    if f_kat:
        rows = [r for r in rows if f_kat in (r.get("kategorie"), r.get("kategorie_v1"))]
    if f_tag:
        try:
            _d0 = datetime.datetime.strptime(f_tag, "%Y-%m-%d")
            t0 = _d0.timestamp()
            # Kalendertag statt fixer 86400 s (Review .54): an Zeitumstellungstagen
            # ist der lokale Tag 23/25 h — /heute rechnet kalendertaeglich, der
            # "Events analysed"-Link muss dieselbe Menge treffen.
            t1 = (_d0 + datetime.timedelta(days=1)).timestamp()
            rows = [r for r in rows if t0 <= (r.get("start") or r.get("ts", 0)) < t1]
        except ValueError:
            pass
    # Areas Stufe 1: Area = grober Filter (Kamera-Menge der Sicht), der Kamera-
    # Filter bleibt daneben (beide gesetzt = natuerliche Schnittmenge); die
    # Blaetter-Links tragen ?area= ueber _seitenlink automatisch mit. Anders als
    # auf /heute (Pass-AUSWAHL) filtert die Event-Liste je Zeile — eine Zeile
    # ist eine Kamera-Tatsache, kein Durchgangs-Urteil.
    _areas_e = _areas_mod.normalisieren(cfg.get("areas"))
    _ar_akt_e, _nk_e = _areas_mod.sicht_aufloesen(
        _areas_e, qs.get("area", [""])[0],
        {str(r.get("camera", "?")) for r in by.values()})
    _ar_werte = sorted(_areas_e) + ["Default"]
    if _nk_e is not None:
        rows = [r for r in rows if str(r.get("camera", "?")) in _nk_e]
    gesamt = len(rows)
    try:                                   # ?seite=abc riss sonst den Request-Thread ab
        seite = max(1, int(qs.get("seite", ["1"])[0] or 1))
    except (ValueError, TypeError):
        seite = 1
    rows = rows[(seite - 1) * 50: seite * 50]
    kameras = sorted({r.get("camera", "?") for r in by.values()})
    kats = sorted({k for r in by.values() for k in (r.get("kategorie"), r.get("kategorie_v1")) if k})
    def _opt(werte, aktiv, labels=None):   # labels: Slug->Anzeige (value bleibt der Slug/Filterwert)
        if labels is None:
            return "".join(f'<option{" selected" if w == aktiv else ""}>{html.escape(w)}</option>'
                           for w in werte)
        return "".join(f'<option value="{html.escape(w)}"{" selected" if w == aktiv else ""}>'
                       f'{html.escape(labels.get(w, w))}</option>' for w in werte)
    filterleiste = (
        '<form method="get" style="margin:8px 0">'
        + (f'<select name="area"><option value="">{t("ereignisliste.filter.alle_areas")}</option>'
           f'{_opt(_ar_werte, _ar_akt_e, {w: w for w in _ar_werte})}</select> '
           if _areas_e else '')
        + f'<select name="kamera"><option value="">{t("ereignisliste.filter.alle_kameras")}</option>{_opt(kameras, f_kam)}</select> '
        f'<select name="person"><option value="">{t("ereignisliste.filter.alle_personen")}</option>'
        f'{_opt(master_persons(cfg), f_per)}</select> '
        f'<select name="kategorie"><option value="">{t("ereignisliste.filter.alle_kategorien")}</option>{_opt(kats, f_kat, kat_map())}</select> '
        f'<input type="date" name="tag" value="{html.escape(f_tag)}" '
        '> '
        f'<button class="gtb on">{t("ereignisliste.filter.knopf")}</button> '
        f'<a href="/ereignisse">{t("ereignisliste.filter.reset")}</a></form>')
    def _seitenlink(n, txt):
        q = {k: v[0] for k, v in qs.items() if v and v[0]}
        q["seite"] = str(n)
        return f'<a href="/ereignisse?{urllib.parse.urlencode(q)}">{txt}</a>'
    blaettern = " · ".join(
        ([_seitenlink(seite - 1, t("ereignisliste.blaettern.neuer"))] if seite > 1 else []) +
        [t("ereignisliste.tabelle.blaettern_stand",
           seite=seite, max=max(1, -(-gesamt // 50)), n=gesamt)] +
        ([_seitenlink(seite + 1, t("ereignisliste.blaettern.aelter"))] if seite * 50 < gesamt else []))
    gt_schnell = gt_schnellpersonen(list(by.values()), cfg)
    andere = [p for p in master_persons(cfg) if p not in gt_schnell]
    # .313: EINE Lese-Quelle; gt_voll traegt die MENGE je eid fuer die Schalter-Leiste
    gt_voll = szenarien.gt_laden(os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl"),
                                 master_persons(cfg))
    gtmap = {k: v["label"] for k, v in gt_voll.items()}   # Altform (letzte Zeile gewinnt)
    # Kopfzellen "Frigate"/"suslik" sind reine Produktnamen (Stufe-0-Grenze).
    body = [f"<h2>{t('ereignisliste.titel')}</h2>", filterleiste, f"<p>{blaettern}</p>",
            f'<div class="tabelle-wrap ereignisse"><table><thead><tr><th>{t("ereignisliste.tabelle.kopf_zeit")}</th>'
            f'<th>{t("ereignisliste.tabelle.kopf_kamera")}</th>'
            "<th>Frigate</th><th>suslik</th>",
            f'<th>{t("ereignisliste.tabelle.kopf_kategorie")}</th>'
            f'<th>{t("ereignisliste.tabelle.kopf_crop")}</th>'
            f'<th>{t("ereignisliste.tabelle.kopf_gt")}</th></tr></thead><tbody>']
    for r in rows:   # defensiv: alte/fremde Zeilen ohne heutige Pflichtfelder nicht crashen lassen
        zeit = datetime.datetime.fromtimestamp(r.get("start") or r.get("ts", 0)).strftime("%d.%m %H:%M:%S")
        f = r.get("frigate") or {}
        fs = f"{f['score']:.2f}" if f.get("score") is not None else "?"
        live_name = akte_live_name(r)         # Bauplan Fixes FX5: der Name des Waechters steht bei suslik, nicht bei Frigate
        ftxt = (t("ereignisliste.tabelle.frigate_zelle",
                  label=f.get("label"), score=fs, cos=f.get("cos"))
                if f.get("label") and not live_name else "—")
        ours = live_name or ", ".join(f"{p} {(v.get('max') or 0):+.2f}/{v.get('win3s', 0)}×" for p, v in
                                      sorted((r.get("ours") or {}).items(),
                                             key=lambda x: -(x[1].get("max") or 0))[:3]) or "—"
        ed = str(r.get("eid", "")).replace("/", "_")
        edir = os.path.join(cfg["data_dir"], "events", ed)
        k = str(r.get("kategorie", "?"))
        best = r.get("bestaetigt") or []
        crop = crop_zellen(cfg, ed, edir, best,
                           t("ereignisliste.tabelle.attr_kein_crop"))
        lg = (f' <a href="/events/{urllib.parse.quote(ed)}/analyze.log" style="color:var(--accent)">'
              f'{t("ereignisliste.tabelle.link_log")}</a>'
              if ed and os.path.isfile(os.path.join(edir, "analyze.log")) else "")
        if ed and any(os.path.isfile(os.path.join(cfg["data_dir"], "clips", ed + s))
                      for s in ("_review.mp4", ".mp4")):
            lg += (f' <a href="/video/{urllib.parse.quote(ed)}" style="color:var(--accent)">'
                   f'{t("ereignisliste.tabelle.link_video")}</a>')
        eid = str(r.get("eid", ""))
        cur = (gt_voll.get(eid) or {}).get("personen", [])
        gtb = gt_leiste(eid, gt_schnell, andere, cur, vorschlag=best) if eid else ""
        unv = (f' <span title="{t("ereignisliste.tabelle.attr_unvollstaendig")}">⚠</span>'
               if r.get("frames_fehlen") else "")     # W1-Telemetrie in der Liste
        # .313: data-label je Zelle = derselbe Kopf-Schluessel — das Handy-Kartenlayout
        # (thead ausgeblendet) stellt ihn per CSS ::before voran (EINE Quelle).
        dl = {k_: html.escape(t(k_), quote=True) for k_ in (
            "ereignisliste.tabelle.kopf_zeit", "ereignisliste.tabelle.kopf_kamera",
            "ereignisliste.tabelle.kopf_kategorie", "ereignisliste.tabelle.kopf_crop",
            "ereignisliste.tabelle.kopf_gt")}
        body.append(f'<tr><td data-label="{dl["ereignisliste.tabelle.kopf_zeit"]}">{zeit}</td>'
                    f'<td data-label="{dl["ereignisliste.tabelle.kopf_kamera"]}">{html.escape(str(r.get("camera", "?")))}</td>'
                    f'<td data-label="Frigate">{html.escape(ftxt)}</td><td data-label="suslik">{html.escape(ours)}'
                    f"{' ✓' + html.escape(','.join(best)) if best else ''}</td>"
                    f'<td data-label="{dl["ereignisliste.tabelle.kopf_kategorie"]}"><span class=k style=background:{KAT_FARBE.get(k, "#666")}>{html.escape(akte_kat_wort(r))}</span>'
                    f"{' 📣' if r.get('alerted') else ''}{unv}{lg}</td>"
                    f'<td data-label="{dl["ereignisliste.tabelle.kopf_crop"]}">{crop}</td>'
                    f'<td data-label="{dl["ereignisliste.tabelle.kopf_gt"]}">{gtb}</td></tr>')
    body.append("</tbody></table>")
    return "".join(body) + "</div>"
