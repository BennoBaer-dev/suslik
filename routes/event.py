"""routes/event — Einzel-Event-Detail /event/<eid> (Klick aus Today, User
22.07.), ME1 byte-treu aus verifyd extrahiert (Schnappschuss-Beweis
scratchpad/me1_schnappschuss.py; Muster ereignisliste: log_path + Daten als
Parameter, kein Dienst-Import). gt_schnellpersonen/master_persons bleiben im
Kern und kommen als CALLABLES herein (modulplan §2c, dritter Nutzer neben
/offen und /ereignisse). render liefert (status, inhalt): der 404-Zweig
(Event nicht im Log) gehoert zur Seite, Layout/Banner/Titel bleiben beim
Handler. szenarien/anlernen/core.vertrauen laden lazy im Render (wie vorher
im Handler-Zweig; anlernen nur fuer UNBEKANNT_MAX — der historische
UnboundLocalError-Kommentar am Import stammt aus der do_GET-Zeit und bleibt
als Entstehungsgeschichte stehen, seit ME1 ist render() der Funktions-Scope).
Sprachschicht unangetastet (event.*-Schluessel seit Tranche B)."""
import datetime
import html
import json
import os
import re
import urllib.parse

import webui
from core.sprache import t, t_n
from webui.bausteine import KAT_FARBE, bild_nn, gt_leiste
from webui.bausteine import fehler_grund as _fehler_grund
from webui.bausteine import kat_wort as _kat_wort, stufe_wort as _stufe_wort


def render(cfg, log_path, eid, gt_schnellpersonen, master_persons):
    """-> (status, seiten-INHALT); status 404 = Event nicht im Log."""
    row, rows_all = None, []
    if os.path.exists(log_path):
        with open(log_path) as f:
            for l in f:
                try:
                    r = json.loads(l)
                except Exception:
                    continue
                rows_all.append(r)
                if r.get("eid") == eid:
                    row = r                    # letzter Eintrag pro eid gewinnt
    if not row:
        # EINE Quelle mit der Pass-Seite (gleicher 404-Text):
        # auftritte.pass.leer_event* wiederverwendet, kein Duplikat.
        return 404, webui.leer(t("auftritte.pass.leer_event"),
                               t("auftritte.pass.leer_event_hinweis"))
    ed = eid.replace("/", "_")
    edir = os.path.join(cfg["data_dir"], "events", ed)
    # Datums-Hardcode (%d.%m.%Y, B19): bleibt Code bis zur Format-Schluessel-Stufe.
    # (ME1: lokale Variable von `t` auf `zeit` umbenannt — sie beschattete
    # sonst core.sprache.t in der ganzen Funktion; Muster ereignisliste.)
    zeit = datetime.datetime.fromtimestamp(row.get("start") or row.get("ts", 0)).strftime("%d.%m.%Y %H:%M:%S")
    cam = html.escape(str(row.get("camera", "?")))
    kat = str(row.get("kategorie", "?"))
    fr = row.get("frigate") or {}
    ftxt = (f"{fr.get('label')} {fr['score']:.2f}" if fr.get("label") and fr.get("score") is not None
            else "—")
    ours = ", ".join(f"{p} {(v.get('max') or 0):+.2f}/{v.get('win3s', 0)}×" for p, v in
                     sorted((row.get("ours") or {}).items(), key=lambda x: -(x[1].get("max") or 0))) or "—"
    # .249 (Kosinus-raus U3): Easy sieht Worte an der Messlatte,
    # die Rohzahlen-Zeile bleibt als Expert-Tiefe erhalten.
    # .250: nur echte Kandidaten (Stufe != none) ausgeschrieben —
    # der no-match-Schwanz aller Personen wird GEZAEHLT statt
    # aufgezaehlt (nichts verschwindet still, nichts lullt).
    from core import vertrauen as _vt
    _ow, _ow_rest = [], 0
    for p, v in sorted((row.get("ours") or {}).items(),
                       key=lambda x: -(x[1].get("max") or 0)):
        _st9 = _vt.stufe(v.get("max"), cfg.get("win_thresh"))
        if _st9 == "none":
            _ow_rest += 1
            continue
        # Tranche D (3d): Wortstufe uebersetzt (bausteine.stufe_wort)
        # statt des englischen Meldetext-Labels _vt.label().
        _ow.append(t_n("event.ours_zeile", v.get("win3s", 0),
                                person=p, stufe=_stufe_wort(_st9)))
    ours_wort = (", ".join(_ow) or t("event.ours_keiner")) + (
        t_n("event.ours_rest", _ow_rest)
        if _ow and _ow_rest else "")
    best = row.get("bestaetigt") or []
    if os.path.isdir(edir):
        # PRO PERSON gruppiert (User 25.07., Screenshot-Befund: "die Bilder eines
        # Events sind voellig unordentlich und durcheinander — es haette pro Gesicht
        # geordnet angezeigt werden muessen"). Vorher war das Raster EINE flache
        # Liste ueber alle Personen des Events; bei dreien ein Durcheinander. Die
        # Zuordnung steckt im Dateinamen (…_best_<Person>_NN… / …_show_<Person>_NN…),
        # es braucht keine neue Analyse. Abschnitte nach bestem NN sortiert,
        # innerhalb wie gehabt NN und dann Groesse; Bilder ohne Zuordnung
        # (z.B. Enrollment-Crops) zuletzt.
        def _gal_rang(c):
            nn = bild_nn(c)
            return (nn if nn is not None else -9.0,
                    os.path.getsize(os.path.join(edir, c)))
        def _gal_person(c):
            m2 = re.search(r"_(?:best|show)_(.+?)_NN", c)
            return m2.group(1) if m2 else None
        jpgs = sorted((c for c in os.listdir(edir) if c.endswith(".jpg")),
                      key=_gal_rang, reverse=True)
        gruppen = {}
        for c in jpgs:
            gruppen.setdefault(_gal_person(c), []).append(c)
        def _grp_rang(pn):
            return max((bild_nn(c) or -9.0) for c in gruppen[pn])
        # SICHTBARE GRENZE sicher/unsicher (User-Befund an einer Tuerkamera:
        # "hier sollte eine deutliche sichtbare Grenze sein — das habe ich klar
        # erkannt, und diese koennten ggf. als falsche Person erkannt werden").
        # Grenze = anlernen.UNBEKANNT_MAX: unterhalb davon haelt suslik ein Gesicht
        # selbst fuer "unbekannt" — eine Namenszuordnung darunter ist also nur eine
        # Vermutung (+0.41, Hinterkopf), keine Erkennung (+0.70). Beurteilt
        # wird die GRUPPE an ihrem besten Bild: traegt eine Person EIN starkes Bild,
        # sind ihre schwaecheren Zusatz-Crops mitbelegt und gehoeren nicht unter den
        # Strich. Import HIER noetig: do_GET importiert anlernen an anderer Stelle
        # lokal, damit ist der Name in der GANZEN Funktion lokal — ohne diesen
        # Import flog auf jeder Event-Seite ein UnboundLocalError (Prod 25.07. 21:30).
        import anlernen
        _grenze_nn = anlernen.UNBEKANNT_MAX
        teile_gal, _unter_grenze = [], False
        _namen = sorted((k for k in gruppen if k is not None), key=_grp_rang,
                        reverse=True)
        _klar = [p for p in _namen if _grp_rang(p) >= _grenze_nn]
        _vage = [p for p in _namen if _grp_rang(p) < _grenze_nn]
        for pn in _klar + _vage + ([None] if None in gruppen else []):
            if not _unter_grenze and (pn in _vage or pn is None):
                # Format-Spezifikum (:.2f) vorformatiert (§8.8)
                teile_gal.append(
                    f'<div class="evgrenze">{t("event.grenze", wert=f"{_grenze_nn:.2f}")}</div>')
                _unter_grenze = True
            zellen = "".join(
                f'<a href="/events/{urllib.parse.quote(ed)}/{urllib.parse.quote(c)}" '
                f'class="evimg"><img src="/events/{urllib.parse.quote(ed)}/'
                f'{urllib.parse.quote(c)}" alt="{html.escape(c)}"></a>'
                for c in gruppen[pn])
            titel = html.escape(pn) if pn else t("event.gruppe_ohne")
            _b = (f' <span class="badge warn">{t("event.badge_unsicher")}</span>'
                  if pn in _vage else "")
            teile_gal.append(
                f'<h4 class="evgrp">{titel} <span class="cnt">{len(gruppen[pn])}'
                f'</span>{_b}</h4><div class="evgal">{zellen}</div>')
        galerie = "".join(teile_gal) if teile_gal                         else webui.leer(t("event.leer_crops"))
    else:
        galerie = webui.leer(t("event.leer_crops"))
    vid = ""
    # W3: /video baut die Browser-Kopie lazy beim Klick (Spinner) bzw. leitet auf die
    # fertige Kopie weiter. Link zeigen, solange EINE der beiden Dateien lebt — die
    # Kopie ueberlebt ihren Quell-Clip um bis zu clip_retention_d (Review-Fund).
    if any(os.path.isfile(os.path.join(cfg["data_dir"], "clips", ed + s))
           for s in ("_review.mp4", ".mp4")):
        vid = f'<a class="btn" href="/video/{urllib.parse.quote(ed)}">{t("event.knopf_video")}</a>'
    logl = (f'<a class="btn" href="/events/{urllib.parse.quote(ed)}/analyze.log">{t("event.knopf_log")}</a>'
            if os.path.isfile(os.path.join(edir, "analyze.log")) else "")
    import szenarien as _szen
    gt_voll = _szen.gt_laden(os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl"),
                             master_persons(cfg))            # .313: EINE Lese-Quelle
    gtmap = {k: v["label"] for k, v in gt_voll.items()}     # Altform fuer szenarien_des_tages
    gt_schnell = gt_schnellpersonen(rows_all, cfg)
    andere = [p for p in master_persons(cfg) if p not in gt_schnell]
    gtb = gt_leiste(eid, gt_schnell, andere, (gt_voll.get(eid) or {}).get("personen", []),
                    vorschlag=row.get("bestaetigt") or [])
    kbadge = (f'<span class=k style=background:{KAT_FARBE.get(kat, "#666")}>'
              f'{html.escape(_kat_wort(kat))}</span>')
    if row.get("frames_fehlen"):   # W1: unvollstaendig gelesener Clip sichtbar machen
        kbadge += (' <span class=k style="background:#8a6d1a" '
                   f'title="{t("event.attr_unvollstaendig", gelesen=row.get("frames_gelesen"), soll=row.get("frames_soll"))}"'
                   f'>{t("event.badge_unvollstaendig")}</span>')
    conf = (' · <b style="color:var(--ok)">✓ ' + html.escape(", ".join(best)) + '</b>') if best else ''
    # Haeppchen 2: Szenario-Leiste — das Event im Kontext seines Durchgangs
    # (Szenario-Prinzip als Navigation: view pass + prev/next INNERHALB des
    # Durchgangs). Faellt still weg, wenn das Event keinem Durchgang angehoert.
    passleiste = ""
    try:
        import szenarien as _szn
        _t0 = row.get("start") or row.get("ts") or 0
        _tagd = datetime.datetime.fromtimestamp(_t0).replace(
            hour=0, minute=0, second=0, microsecond=0)
        _byh = {}
        for _r in rows_all:
            if _r.get("eid"):
                _byh[_r["eid"]] = _r
        # Kalendertag statt 86400 s (Review .55 — DST-Klasse wie .54/ereignisse)
        _sz = _szn.szenarien_des_tages(_byh, _tagd.timestamp(),
                                       (_tagd + datetime.timedelta(days=1)).timestamp(),
                                       cfg, gtmap)
        _s = next((x for x in _sz
                   if any(e.get("eid") == eid for e in x.get("evs") or [])), None)
        if _s:
            # Auch bei n==1 (Issue #9-Nachbefund .173): die Leiste ist der
            # einzige Weg zur Pass-Seite und damit zum Analyse-Grund — ein
            # EINZELNES Fehler-Event (genau Tokn59s Screenshot-Fall) hatte
            # vorher keinen. prev/next entfallen bei n==1 von selbst.
            _evs = [e for e in _s.get("evs") or [] if e.get("eid")]
            _i = next((k for k, e in enumerate(_evs) if e["eid"] == eid), None)
            _pl = (f'<a class="gtb" href="/event/{urllib.parse.quote(str(_evs[_i-1]["eid"]))}">{t("event.pass_zurueck")}</a>'
                   if _i and _i > 0 else '')
            _nl = (f'<a class="gtb" href="/event/{urllib.parse.quote(str(_evs[_i+1]["eid"]))}">{t("event.pass_weiter")}</a>'
                   if _i is not None and _i + 1 < len(_evs) else '')
            passleiste = (
                f'<div class="card passleiste">{t("event.pass_teil")} '
                f'<span class="num">{datetime.datetime.fromtimestamp(_s["start"]).strftime("%H:%M")}'
                f'&ndash;{datetime.datetime.fromtimestamp(_s["ende"]).strftime("%H:%M")}</span>'
                f' · {t_n("event.pass_events", _s["n"])} · '
                f'<a class="gtb" href="/pass/{urllib.parse.quote(eid)}">{t("event.pass_knopf")}</a> {_pl}{_nl}</div>')
    except Exception:
        passleiste = ""               # Leiste ist Komfort, nie ein Seitenkiller
    # Issue #9 (Tokn59, 31.07., Zusage endlich eingeloest .173): der GRUND
    # eines Fehler-Events steht DIREKT auf der Event-Seite. Quelle ist die
    # EINE Helferin webui.bausteine.fehler_grund (auch die Pass-Seite liest
    # sie — Widerleger 11.08.: drei Streu-Antworten auf dieselbe Frage,
    # zwei zeigten Nachspann statt Ursache). Ohne Log ein ehrlicher
    # Verweis statt gar nichts (genau sein Screenshot-Fall).
    fehlergrund = ""
    if kat == "fehler":
        _lp = os.path.join(cfg["data_dir"], "events", ed, "analyze.log")
        try:
            _g = _fehler_grund(_lp)
            _hat_log = os.path.isfile(_lp)
        except Exception:
            _g, _hat_log = "", False   # Grund-Zeile ist Komfort, nie ein Seitenkiller
        # Zwei ehrliche Fallbacks (Widerleger-Recheck): ein VORHANDENES Log
        # ohne Grund-Zeile darf nicht als "kein Log" ausgegeben werden.
        fehlergrund = (
            f'<div class="evrow"><span class="lab">{t("event.label_grund")}</span>'
            + (f'<span>{html.escape(_g)}</span></div>' if _g else
               (f'<span class="dim">{t("event.grund_ohne_zeile")}</span></div>' if _hat_log else
                f'<span class="dim">{t("event.grund_ohne_log")}</span></div>')))
    # Zeilenlabels "Frigate"/"suslik" bleiben literal: reine
    # Produktnamen, in JEDER Sprache wortgleich (§8.6).
    inhalt = (
        f'<div class="evhead"><a href="/heute" class="back">{t("event.zurueck")}</a>'
        f'<h2>{cam} · <span class="num">{zeit}</span></h2></div>'
        f'{passleiste}'
        f'<div class="card evmeta"><div class="evbadges">{kbadge}{conf}</div>'
        f'<div class="evrow"><span class="lab">Frigate</span><span>{html.escape(ftxt)}</span></div>'
        f'<div class="evrow"><span class="lab">suslik</span><span>{html.escape(ours_wort)}'
        f' <span class="dim nur-expert">· {html.escape(ours)}</span></span></div>'
        f'{fehlergrund}'
        f'<div class="evactions">{vid}{logl}</div>'
        f'<div class="evgt"><span class="lab">{t("event.label_korrektur") if best else t("event.label_wer")}</span>{gtb}</div></div>'
        f'<h3>{t("event.h_bilder")}</h3>{galerie}')
    return 200, inhalt
