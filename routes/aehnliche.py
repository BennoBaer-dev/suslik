"""routes/aehnliche — "Matching faces": passende Unbekannte + Bestands-Vorschlaege zu
einer Person (M1a, byte-treu aus verifyd extrahiert). Kontrakt: NUR rendern.

.510/J18 (d): der Seitenaufruf startet KEINE Suche mehr (bis .509 startete er
`qs_neu_starten` bei fehlendem refcache und `vorschlaege_starten` bei fehlender
Vorschlagsdatei — zwei Subprozesse, ausgeloest vom blossen Hinsehen). Damit
zerfaellt `None` in ZWEI verschiedene Lagen, die vorher eine waren:
  * es LAEUFT gerade eine Suche  -> Platzhalter + Zaehler + Selbst-Neuladen
    (refresh 15 s Quelle 1 / 20 s Quelle 2 wie im Bestand — jetzt aber ENDLICH:
    er hoert auf, sobald der Lauf vorbei ist);
  * es laeuft KEINE              -> ehrlicher Satz („noch nie gesucht" bzw.
    „zuletzt gesucht am …") plus der Knopf, der sie startet. KEIN Refresh.
Welche Lage vorliegt, sagt `stand` (verifyd.Service.such_stand) — diese Datei
raet es nicht aus den Daten.

Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py)."""
import datetime
import html
import os
import urllib.parse

import webui

from core.sprache import t


def _zaehler(inhalt, person):
    """Den mitlaufenden Sekundenzaehler in einen `webui.leer`-Kasten haengen
    (webui/app.js: `.such-zaehler` zaehlt hoch und pollt `/aehnliche_status`,
    laedt bei „fertig" sofort neu)."""
    return inhalt.replace(
        "</b>", '</b> <span class="such-zaehler" data-person="'
        + html.escape(person, quote=True) + '"></span>', 1)


def _lauf_hinweis(st, plaetze, belegt):
    """Der ehrliche Zwischenstand EINER laufenden Suche: wartet sie auf einen
    Platz oder rechnet sie schon? Bei einem Analyse-Platz ist genau das die
    Erklaerung fuer die Wartezeit — sie steht deshalb mit dabei."""
    if (st or {}).get("phase") == "wartet":
        return t("aehnliche.suche.wartet_platz", belegt=belegt, plaetze=plaetze)
    return t("aehnliche.suche.rechnet")


def _stand_text(ts):
    """Zeitpunkt der letzten Suche. HEUTE nur die Uhrzeit (wie bis .509), aelter
    MIT Datum: eine Vorschlagsdatei aus der alten Automatik kann Tage alt sein,
    und „as of 09:14" haette das verschwiegen (J18 (d), Altstaende)."""
    d = datetime.datetime.fromtimestamp(ts or 0)
    return d.strftime("%H:%M" if d.date() == datetime.date.today()
                      else "%d.%m. %H:%M")


def render(person, kand, vs, data_dir, va=None, stand=None):
    """-> (inhalt, refresh). kand = anlernen.aehnliche_unbekannte(person)
    (None = kein refcache-Eintrag), vs = anlernen.lade_vorschlaege(person)
    (None = keine Vorschlagsdatei),
    va = offene Vorrats-Angebote der Person (core.vorrat.angebote_lesen,
    bauplan_vorrat.md B4) — None/leer: der Abschnitt erscheint gar nicht
    (Alt-Render byte-identisch).
    stand (.510/J18 d) = verifyd.Service.such_stand(person): welche Suche
    LAEUFT gerade und wie viele Analyse-Plaetze es gibt. Ohne `stand` (Alt-
    Aufrufer, Proben) gilt „nichts laeuft" — dann zeigt die Seite Knoepfe
    statt Platzhalter, nie einen Dauer-Refresh."""
    pe = html.escape(person)
    pj = html.escape(person.replace("\\", "\\\\").replace("'", "\\'"), quote=True)
    st = stand or {}
    st_vs = st.get("vorschlaege") or {}
    st_uk = st.get("unbekannt") or {}
    plaetze = int(st.get("plaetze") or 1)
    belegt = int(st.get("belegt") or 0)
    refresh = None
    teile = [f"<h2>{t('aehnliche.kopf.titel', person=pe)}</h2>"
             f"<p>{t('aehnliche.kopf.satz', person=pe)} "
             f"<a href='/gesichter'>{t('aehnliche.kopf.link_zurueck')}</a></p>"]
    # --- Quelle 1: unbekannte Gesichter ---
    teile.append(f"<h3>{t('aehnliche.unbekannt.titel')}</h3>")
    if kand is None and st_uk.get("laeuft"):
        refresh = 15
        teile.append(_zaehler(webui.leer(t("aehnliche.unbekannt.suche_titel"),
                                         t("aehnliche.suche.rechnet")), person))
    elif kand is None:
        # M-10 (W1): genau hier stand bis .509 der Dauer-Platzhalter mit 20-s-
        # Refresh fuer eine Suche, die niemand gestartet hatte. Quelle 1 haengt
        # am refcache; geschrieben wird der von der Referenz-Pruefung, und die
        # startet dieser Knopf (`refPruefNeu`, derselbe wie auf der Qualitaets-Seite).
        teile.append(webui.leer(t("aehnliche.unbekannt.kein_cache"),
                                t("aehnliche.unbekannt.kein_cache_hinweis"))
                     + f'<p><button class="gtb" onclick="refPruefNeu(this)">'
                     f'{t("aehnliche.unbekannt.knopf_pruefen")}</button></p>')
    elif not kand:
        teile.append(webui.leer(t("aehnliche.unbekannt.hinweis_leer")))
    else:
        for g in kand:
            gid = html.escape(g["id"], quote=True)
            sim_txt = t("aehnliche.unbekannt.aehnlichkeit", sim="%.2f" % g["sim"])
            teile.append(
                f'<label class="card" style="display:inline-block;width:auto;'
                f'text-align:center;margin:4px;vertical-align:top">'
                f'<img src="/anlern/crops/{urllib.parse.quote(g["id"])}.jpg" '
                f'style="height:120px;border-radius:5px;display:block;margin-bottom:4px">'
                f'<input type="checkbox" class="ae-cb" value="{gid}"> '
                f'{sim_txt}</label>')
        teile.append(f'<div style="margin:6px 0 14px"><button class="gtb on" '
                     f'onclick="aehnlicheHinzu(\'{pj}\',this)">'
                     f'{t("aehnliche.unbekannt.knopf_hinzu", person=pe)}</button></div>')
    # --- Quelle 2: Bestands-Suche in erkannten Events ---
    teile.append(f"<h3>{t('aehnliche.vorschlaege.titel')}</h3>")
    if st_vs.get("laeuft"):
        # Laeuft wirklich — Platzhalter samt Zwischenstand. Der Refresh endet
        # mit dem Lauf (bis .509 lief er ohne Ende, weil ihn nichts abstellte).
        refresh = refresh or 20
        teile.append(_zaehler(
            webui.leer(t("aehnliche.vorschlaege.suche_titel"),
                       _lauf_hinweis(st_vs, plaetze, belegt)), person))
    elif vs is None:
        teile.append(webui.leer(t("aehnliche.vorschlaege.nie_gesucht"),
                                t("aehnliche.vorschlaege.nie_gesucht_hinweis"))
                     + f'<p><button class="gtb on" onclick="vorschlagNeu(\'{pj}\',this)">'
                     f'{t("aehnliche.vorschlaege.knopf_neu")}</button></p>')
    else:
        ev_base = os.path.join(data_dir, "events")
        ks = [k for k in vs.get("kandidaten", [])
              if os.path.isfile(os.path.join(ev_base, str(k["eid"]).replace("/", "_"),
                                             k["datei"]))]
        # J18 (d), Altstaende: `ts` schreibt anlernen seit je mit; fehlt es in
        # einer alten Datei, gilt deren mtime — nie die Epoche (1970 als
        # „zuletzt gesucht" waere schlechter als keine Angabe).
        _ts = vs.get("ts")
        if not _ts:
            try:
                _ts = os.path.getmtime(os.path.join(data_dir, "learn",
                                                    "vorschlaege_"
                                                    + person.replace(" ", "_") + ".json"))
            except OSError:
                _ts = 0
        stand_v = _stand_text(_ts)
        if ks:
            def _vs_kachel(k, rand="", cbcls=""):
                ed = urllib.parse.quote(str(k["eid"]).replace("/", "_"))
                val = html.escape(f'{k["eid"]}|{k["datei"]}', quote=True)
                wann = datetime.datetime.fromtimestamp(k.get("ts") or 0).strftime("%d.%m. %H:%M")
                zeile = t("aehnliche.vorschlaege.kachel_zeile", wann=wann,
                          kamera=html.escape(str(k.get("camera") or "?")),
                          sim="%.2f" % k["sim"])
                return (
                    f'<label class="card" style="display:inline-block;width:auto;'
                    f'text-align:center;margin:4px;vertical-align:top{rand}">'
                    f'<img src="/events/{ed}/{urllib.parse.quote(k["datei"])}" '
                    f'style="height:120px;border-radius:5px;display:block;margin-bottom:4px">'
                    f'<input type="checkbox" class="vs-cb {cbcls}" value="{val}"> '
                    f'{zeile}</label>')
            # Zwei sichtbare Stufen (User 21.07.): Recommended + Neutral.
            # 'Not recommended' wird gar nicht erst geschrieben. Fallback fuer
            # alte JSONs, die noch 'sicher' statt 'stufe' fuehren.
            def _stufe(k):
                return k.get("stufe") or ("empfohlen" if k.get("sicher", True) else "neutral")
            empfohlen = [k for k in ks if _stufe(k) == "empfohlen"]
            neutral = [k for k in ks if _stufe(k) == "neutral"]
            if empfohlen:
                teile.append(f'<h4 style="margin:12px 0 4px">{t("aehnliche.vorschlaege.titel_empfohlen")}</h4>')
                for k in empfohlen:
                    teile.append(_vs_kachel(k, ";outline:2px solid #2a9d5a", "vs-cb-rec"))
            if neutral:
                teile.append(
                    f'<h4 style="margin:14px 0 4px">{t("aehnliche.vorschlaege.titel_neutral")}</h4>'
                    f'<p style="color:var(--dim);font-size:13px;margin:0 0 6px">'
                    f'{t("aehnliche.vorschlaege.hinweis_neutral")}</p>')
                for k in neutral:
                    teile.append(_vs_kachel(k, ";outline:2px dashed #b80"))
            auto_btn = (f'<button class="gtb on" onclick="vorschlaegeAlleEmpfohlen(\'{pj}\',this)">'
                        f'{t("aehnliche.vorschlaege.knopf_alle", n=len(empfohlen))}</button> ' if empfohlen else '')
            teile.append(
                f'<div style="margin-top:10px">{auto_btn}'
                f'<button class="gtb" onclick="vorschlagAufnehmen(\'{pj}\',this)">'
                f'{t("aehnliche.vorschlaege.knopf_gewaehlt", person=pe)}</button> '
                f'<button class="gtb" onclick="vorschlagNeu(\'{pj}\',this)">'
                f'{t("aehnliche.vorschlaege.knopf_neu")}</button> '
                f'<small style="color:var(--faint)">'
                f'{t("aehnliche.vorschlaege.fuss", stand=stand_v, person=pe)}</small></div>')
        else:
            # J18 (d): auch der leere Treffer traegt den Zeitpunkt — sonst steht
            # eine Woche alte „nichts gefunden"-Aussage wie eine frische da.
            teile.append(webui.leer(t("aehnliche.vorschlaege.hinweis_leer"),
                                    t("aehnliche.vorschlaege.hinweis_leer_kriterien"))
                         + f'<p><button class="gtb" onclick="vorschlagNeu(\'{pj}\',this)">'
                         f'{t("aehnliche.vorschlaege.knopf_neu")}</button> '
                         f'<small style="color:var(--faint)">'
                         f'{t("aehnliche.vorschlaege.stand_leer", stand=stand_v)}</small></p>')
    # --- Quelle 3: Vorrats-Angebote der Lernlaeufe (bauplan_vorrat.md B4) ---
    # Direkt aus vorrat.jsonl der EXISTIERENDEN Laeufe gerendert (kein Misch-
    # File, Konzept-QS W1.14/W2.10); eigener Draht ueber data-Attribute — der
    # eid|datei-Wert der Bestands-Suche kann den Lauf-Pfad nicht transportieren.
    if va:
        teile.append(f"<h3>{t('aehnliche.vorrat.titel')}</h3>"
                     f"<p style='color:var(--dim);font-size:13px;margin:0 0 6px'>"
                     f"{t('aehnliche.vorrat.hinweis')}</p>")
        for z in va:
            lid = urllib.parse.quote(str(z.get("lauf_id") or ""))
            basis = os.path.basename(str(z.get("datei_v") or ""))
            wann = datetime.datetime.fromtimestamp(
                (z.get("ts") or 0) + (z.get("t") or 0)).strftime("%d.%m. %H:%M")
            zeile = t("aehnliche.vorrat.kachel_zeile", wann=wann,
                      kamera=html.escape(str(z.get("kamera") or "?")),
                      sim="%.2f" % (z.get("sim") or 0),
                      norm="%.1f" % (z.get("norm") or 0))
            anker = (f' <span style="color:var(--dim);font-size:11px">'
                     f'{t("aehnliche.vorrat.auch_anker")}</span>'
                     if z.get("auch_anker") else "")
            teile.append(
                f'<label class="card" style="display:inline-block;width:auto;'
                f'text-align:center;margin:4px;vertical-align:top;'
                f'outline:2px solid #2a6db8">'
                f'<img src="/lernlauf/vorrat/{lid}/{urllib.parse.quote(basis)}" '
                f'style="height:120px;border-radius:5px;display:block;margin-bottom:4px">'
                f'<input type="checkbox" class="vo-cb" '
                f'data-lauf="{html.escape(str(z.get("lauf_id") or ""), quote=True)}" '
                f'data-datei="{html.escape(basis, quote=True)}" '
                f'data-eid="{html.escape(str(z.get("eid") or ""), quote=True)}"> '
                f'{zeile}{anker}</label>')
        teile.append(
            f'<div style="margin:6px 0 14px">'
            f'<button class="gtb on" onclick="vorratAufnehmen(\'{pj}\',this)">'
            f'{t("aehnliche.vorrat.knopf_gewaehlt", person=pe)}</button></div>')
    return "".join(teile), refresh
