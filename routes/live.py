"""routes/live — der Reiter "Live" (Live-Phase 2, live_reiter_bauplan.md §2).

Reines Rendern (Muster kameras/benachrichtigungen: Daten als Parameter, kein
Dienst-Import). Der Handler sammelt Kameras (verifyd.frigate_cameras — KEINE
zweite Kamera-Aufzaehlung, Deckungs-Regel), Guards + Engine-Quittung
(core.livewache: guards_lesen/status_lesen) und den abgeleiteten Zustand je
Kachel (livewache.ui_zustand) und reicht sie herein. Farbe und Label je
Zustand kommen aus registry.LIVE_ZUSTAENDE — die EINE Quelle, aus der auch
/health speist (K3). K1 in beide Richtungen: gerendert wird ausschliesslich
der abgeleitete Zustand, nie der Store-Wunsch.

GPU-only-Hinweis (User-Auflage 12.08., KEIN Versprechen): fester Text auf
Uebersicht und Detailseite — "Works with a GPU only for now — we are working
on a CPU option but can't promise it."

Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py; GPU_/CPU_HINWEIS wurden dafuer zu
Schluesseln (live.hinweis_gpu/_cpu, t() zur Render-Zeit — Modul-Konstanten
froeren die Sprachwahl auf den Import ein); die frueheren Schleifen-/
Textvariablen `t` sind umbenannt, damit sie t() nicht verschatten.
"""
import html
import time
import urllib.parse

from core.livewache import (URTEIL_T_S, HOEHEN_ALT, HOEHEN_ERLAUBT, quelle_fp,
                            quelle_maskiert)
from core.registry import LIVE_ZUSTAENDE
from core.sprache import t, t_n

# CPU-Runde 17.08. (User-Go nach Messung): auf der cpu-Variante ist Live
# BEGRENZT erlaubt — der Text (live.hinweis_cpu) sagt ehrlich, was gemessen
# ist, und verspricht keine Unter-einer-Sekunde-Reaktion.

DOKU_URL = "https://github.com/BennoBaer-dev/suslik/blob/main/docs/live-watchers.md"

_PHASEN = {"verbinden": "Connecting", "messen": "Measuring",
           "auswerten": "Evaluating", "abbruch": "Aborting"}

# Alters-Marke fuer gecachte Messwerte (UI-M6): ab so vielen Tagen traegt die
# Zeile ein sichtbares Alter — eine 14 Tage alte Messung las sich sonst wie
# eine frische.
_ALT_AB_TAGE = 1.0
# Ab hier ist der Quelltest nicht mehr nur ALT, sondern eine AUFFORDERUNG
# (User-Befund 31.08. an der deployten Seite: das Alter stand als graue Zeile
# da und sagte nicht, was zu tun ist). 7 Tage ist die im Haus schon benutzte
# Frist fuer "das ist nicht mehr frisch" (verifyd.py, Sichtungs-Fenster des
# Nachtjobs) — kein neu gewuerfelter Wert.
_TEST_ALT_TAGE = 7.0



def _fmt_fenster(wert):
    """Anzeige des W0-Urteils-Fensters: gespeicherter Wert oder der Default
    aus der EINEN Quelle (core.livewache.URTEIL_T_S) — ganzzahlig, wenn glatt."""
    z = float(URTEIL_T_S if wert is None else wert)
    return str(int(z)) if z == int(z) else str(z)

def _wann(ts):
    if not ts:
        return "?"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))


def _alter_marke(ts):
    try:
        tage = (time.time() - float(ts)) / 86400.0
    except (TypeError, ValueError):
        return ""
    if tage >= _ALT_AB_TAGE:
        return " " + t("live.zeile.alter", tage=f"{tage:.0f}")
    return ""


def _pill(zustand):
    z = LIVE_ZUSTAENDE.get(zustand) or {"farbe": "neutral", "label": zustand}
    return (f'<span class="pill lvp lvp-{z["farbe"]}">'
            f'{html.escape(z["label"])}</span>')


def _fp_veraltet(block, guard):
    """UI-M6: gilt der gecachte Block (test/messung) noch fuer die AKTUELLE
    Quelle? Ohne eigenen Fingerprint (Altbestand) gilt er als ungebunden."""
    if not block or not guard:
        return False
    fp = block.get("quelle_fp")
    return bool(fp) and fp != quelle_fp(guard)


def _test_tage(test):
    """Alter des gruenen Quelltests in Tagen -> float|None."""
    try:
        return (time.time() - float((test or {}).get("ts"))) / 86400.0
    except (TypeError, ValueError):
        return None


def _test_zeile(test, guard=None, auffordern=False):
    """Die Quelltest-Zeile. `auffordern` (Detailseite): ab _TEST_ALT_TAGE wird
    aus der grauen Alters-Notiz ein sichtbarer Hinweis MIT Handlungssatz —
    graue Zahlen beantworten nicht, was der Nutzer tun soll."""
    if not test or not test.get("ok"):
        return ""
    tage = _test_tage(test)
    alt = auffordern and tage is not None and tage >= _TEST_ALT_TAGE
    txt = (t("live.test.zeile", wann=_wann(test.get("ts")),
             aufloesung=test.get("aufloesung", "?"),
             skala=test.get("skala", "?"),
             bilder_s=test.get("bilder_s", "?"))
           # .196: Alt-Tests und Datei-Quellen tragen Durchsatz statt
           # Lieferrate — ehrlich kennzeichnen statt eine echte fps vorzugeben.
           + ("" if test.get("bilder_s_art") == "delivery"
              else " " + t("live.test.durchsatz"))
           + ", " + t("live.test.provider", provider=test.get("provider", "?"))
           + ("" if test.get("hw") else " " + t("live.test.sw"))
           + _alter_marke(test.get("ts"))
           + (" " + t("live.test.entwertet")
              if _fp_veraltet(test, guard) else ""))
    if alt:
        return (f'<div class="lv-zeile lv-hinweis">{html.escape(txt)}<br>'
                f'{html.escape(t("live.test.veraltet_bitte", tage=f"{tage:.0f}"))}'
                f'</div>')
    return f'<div class="dim lv-zeile">{html.escape(txt)}</div>'


def _test_fehler_zeile(tf):
    """UI-M3: der letzte FEHLGESCHLAGENE Quelltest, sichtbar (der gruene
    test-Block bleibt daneben stehen — er traegt den Enable-Riegel)."""
    if not tf or not tf.get("fehler"):
        return ""
    txt = t("live.test.fehlgeschlagen", wann=_wann(tf.get("ts")),
            fehler=tf["fehler"])
    return f'<div class="dim lv-zeile">{html.escape(txt)}</div>'


def _messung_zeile(messung, guard=None):
    if messung and messung.get("ok"):
        txt = (t("live.messung.zeile", wann=_wann(messung.get("ts")),
                 text=messung.get("text", ""))
               + _alter_marke(messung.get("ts"))
               + (" " + t("live.messung.veraltet")
                  if _fp_veraltet(messung, guard) else ""))
        return f'<div class="dim lv-zeile">{html.escape(txt)}</div>'
    if messung and messung.get("fehler"):
        txt = t("live.messung.fehlgeschlagen",
                wann=_wann(messung.get("ts")), fehler=messung["fehler"])
        return f'<div class="dim lv-zeile">{html.escape(txt)}</div>'
    # Stufe-0-Grenze: <b>Measure load</b> mitten im Satz — bleibt literal.
    return ('<div class="dim lv-zeile">load not measured yet — use '
            '<b>Measure load</b> before enabling</div>')


def _zaehler_zeile(live):
    if not live:
        return ""
    teile = [t("live.zaehler.auftritte", n=live.get("auftritte", 0)),
             t("live.zaehler.trigger", n=live.get("trigger", 0)),
             t("live.zaehler.alerts", n=live.get("gemeldet", 0))]
    lt = live.get("letzter_trigger_ts")
    if lt:
        teile.append(t("live.zaehler.letzter",
                       zeit=time.strftime("%H:%M:%S",
                                          time.localtime(float(lt)))))
    return ('<div class="dim lv-zeile">'
            + html.escape(t("live.zaehler.kopf") + " " + " · ".join(teile))
            + "</div>")


def _engine_karte(engine_info, gesperrt, container_last=None):
    """Engine-Lage + RAM-Ehrlichkeit (§2.3: Messwerte dieser Maschine, nie
    Literaturwerte — ungemessen heisst sichtbar 'not yet measured')."""
    if gesperrt:
        return ""
    st = engine_info.get("status") or {}
    # Phase 4: Supervisor-Lage (Autostart/Standalone) aus DERSELBEN Quelle
    # wie /health (Service.live_aufsicht_status) — tolerant gegen fehlenden
    # Block (aeltere Aufrufer/Harnisch-Faelle reichen keinen herein).
    aufsicht = engine_info.get("aufsicht") or {}
    aufsicht_zeile = (f'<div class="dim lv-zeile">{html.escape(str(aufsicht.get("text")))}'
                      f'</div>' if aufsicht.get("text") else "")
    if not engine_info.get("frisch"):
        return (f'<div class="card"><b>{t("live.engine.titel_aus")}</b>'
                + aufsicht_zeile
                + f'<div class="dim">{t("live.engine.satz_aus")}</div></div>')
    slots = st.get("slots") or {}
    sch = st.get("scheduler") or {}
    je = slots.get("je_stream_mb")
    je_txt = (t("live.engine.je_stream", mb=f"{je:.0f}",
                quelle=slots.get("je_stream_quelle", ""))
              if je is not None else
              t("live.engine.je_stream_fehlt"))
    frei = slots.get("ram_frei_mb")
    rss = slots.get("rss_mb")
    # .252 (User: "worauf soll er entscheiden?"): die ECHTE momentane
    # CPU-Nutzung des ganzen suslik-Containers als erste Zeile — cgroup-
    # gemessen (einzige nicht-luegende Quelle im Container), mit Limit
    # falls eines gesetzt ist. Entscheidungsgrundlage fuer "noch ein
    # Waechter?", zusammen mit Measure load je Kamera.
    zeilen = []
    if container_last:
        _ck, _cl = container_last
        # B9: je Zweig ein GANZER Satz-Schluessel; {kerne}/{limit} kommen
        # vorformatiert (:g) aus der Route.
        zeilen.append(
            t("live.engine.cpu_mit_limit", kerne=f"{_ck:g}", limit=f"{_cl:g}")
            if _cl else
            t("live.engine.cpu_ohne_limit", kerne=f"{_ck:g}"))
    zeilen += [
        # UI-KANN 10: Python-Leerwert nie in die Karte ('RSS None MB').
        t("live.engine.rss", rss=rss if rss is not None else "?")
        + (" · " + t("live.engine.grundkosten",
                     mb=f'{slots.get("grundkosten_mb"):.0f}')
           if slots.get("grundkosten_mb") is not None else ""),
        je_txt,
        (t("live.engine.ram_frei", mb=f"{frei:.0f}",
           quelle=slots.get("ram_quelle", "?"))
         if frei is not None else t("live.engine.ram_unlesbar")),
        t("live.engine.detektor", ms=slots.get("det_ms", "?"),
          quelle=slots.get("det_ms_quelle", "?")),
        t("live.engine.drossel", stufe=sch.get("drossel_stufe", "?"),
          auslastung=sch.get("auslastung", "?")),
    ]
    # UI-M4 Rest-RAM-Ehrlichkeit (§2.3): was nach EINEM weiteren Stream
    # rechnerisch uebrig bliebe, mit Warnstufe unter der Restgrenze.
    rest = slots.get("rest_nach_slot_mb")
    if rest is not None:
        zeilen.append(t("live.engine.rest", mb=f"{rest:.0f}")
                      + (" " + t("live.engine.rest_warnung")
                         if slots.get("rest_warnung") else ''))
    # .196: der Deckel kommt nur noch aus den zwei Notbremsen (harter Deckel,
    # RAM-Boden als Messwert) — kein Lastmodell mehr (User: Messwerte
    # informieren, sie entscheiden nicht).
    emax = slots.get("effektiv_max")
    if emax is not None:
        zeilen.append(t("live.engine.kapazitaet", n=emax,
                        hart=slots.get("hart_max", "?"),
                        grund=slots.get("effektiv_grund") or "?"))
    else:
        zeilen.append(t("live.engine.hart", hart=slots.get("hart_max", "?")))
    # Standalone LAUT auf der Karte (Bauplan-Auftrag Phase 4): eine fremd
    # gestartete Engine liefert zwar Herzschlag, aber der Dienst startet
    # keine zweite und uebernimmt erst nach deren Ende.
    kopf = (t("live.engine.titel_standalone")
            if aufsicht.get("standalone") else t("live.engine.titel_an"))
    return (f'<div class="card"><b>{kopf}</b>'
            + aufsicht_zeile
            + "".join(f'<div class="dim lv-zeile">{html.escape(z)}</div>'
                      for z in zeilen)
            + '</div>')


GRUPPEN = (("laufend", "Running"), ("bereit", "Ready"),
           ("rest", "Not set up"), ("versteckt", "Hidden"))


def gruppen(kacheln):
    """Kachel-Gruppierung des Reiters (User 13.08.: 'erst die aktiven sehen,
    dann die deaktivierten' — die Wand aus gleichwertigen Kacheln erschlug):
    Running = active UND disturbed (Stoerungen gehoeren nach OBEN; ein
    LAUFENDER Waechter ist NIE versteckt, auch wenn er auf der Versteck-
    Liste steht), Ready = tested, Hidden = Versteck-Liste, Rest = alles
    andere. Reine Funktion -> {gruppe: [kd]} (Harnisch T19)."""
    aus = {g: [] for g, _ in GRUPPEN}
    for kd in kacheln:
        z = kd.get("zustand")
        if z in ("active", "disturbed", "checking"):
            # checking (.362): sichtbar zu den Laufenden — ein Selbstheilungs-
            # Zustand darf nie im zugeklappten Rest-Abschnitt verschwinden
            # (Konzept-QS-Blocker 28.08.).
            aus["laufend"].append(kd)
        elif kd.get("versteckt"):
            aus["versteckt"].append(kd)
        elif z == "tested":
            aus["bereit"].append(kd)
        else:
            aus["rest"].append(kd)
    return aus


def kopf_aufloesung(kd):
    """Kopf-Aufloesung einer Kachel -> (text, echt). Rangfolge (User-Befund
    13.08., '800×600 fuer eine 4K-Kamera passt nicht'): (1) Quelltest —
    er misst die KONFIGURIERTE Quelle (auch eine Custom-URL); (2) Stream-
    Steckbrief des Dienst-Probelaufs (echter Restream, ohne Klick da);
    (3) Frigates detect-Substream-Groesse, ehrlich beschriftet. Reine
    Funktion (Harnisch T19)."""
    test = kd.get("test") or {}
    if test.get("aufloesung"):
        return str(test["aufloesung"]).replace("x", "×"), True
    brief = kd.get("steckbrief") or {}
    if brief.get("breite"):
        return f'{brief["breite"]}×{brief.get("hoehe")}', True
    cam = kd.get("cam") or {}
    if cam.get("width"):
        return f'{cam.get("width")}×{cam.get("height")} (detect)', False
    return "", False


def _karte(kd, gesperrt):
    """-> HTML EINER Kachel (aus uebersicht herausgeloest, .186)."""
    name = kd["name"]
    nid = html.escape(name, quote=True)
    z = kd["zustand"]
    farbe = (LIVE_ZUSTAENDE.get(z) or {}).get("farbe", "neutral")
    detail = (f'<div class="dim lv-zeile">{html.escape(kd["detail"])}</div>'
              if kd.get("detail") else "")
    fremd = ("" if kd.get("in_frigate")
             else f' <span class="pill warn" title="{t("live.kachel.attr_fremd")}">'
                  + t("live.kachel.pill_fremd") + '</span>')
    # "(detect)" ist Anzeige UND Ersetzungs-Token zugleich (Stufe-0-Grenze
    # Anzeige==Kennung) — bleibt literal, nur der title-Text ist Schluessel.
    res_text, res_echt = kopf_aufloesung(kd)
    res = (html.escape(res_text) if res_echt else
           html.escape(res_text).replace(
               "(detect)",
               f'<span title="{t("live.kachel.attr_detect")}">(detect)</span>'))
    knoepfe = [f'<a class="gtb" href="/live/{nid}">{t("live.knopf_konfigurieren")}</a>']
    if not gesperrt:
        g = kd.get("guard")
        if g is not None or kd.get("in_frigate"):
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveTest(\'{nid}\',this)">'
                           f'{t("live.knopf_test")}</button>')
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveMessung(\'{nid}\',this)">'
                           f'{t("live.knopf_messung")}</button>')
        if z in ("tested", "untested"):
            # untested seit .362 mit Enable-Knopf: das Enable testet selbst
            # (Selbstheilung .361) — vorher war der neue Pfad im UI gar
            # nicht erreichbar (Konzept-QS-Einwand).
            knoepfe.append(f'<button class="gtb on" '
                           f'onclick="liveSchalter(\'{nid}\',true,this)">'
                           f'{t("live.knopf_enable")}</button>')
        elif g is not None and g.get("enabled"):
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveSchalter(\'{nid}\',false,this)">'
                           f'{t("live.knopf_disable")}</button>')
    # Hide/Show (User 13.08.) — NICHT an laufenden Kacheln (die Running-
    # Gruppe zeigt immer alles; erst stoppen, dann verstecken).
    if kd["zustand"] not in ("active", "disturbed", "checking"):
        if kd.get("versteckt"):
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveVerstecken(\'{nid}\',false,this)">'
                           f'{t("live.knopf_zeigen")}</button>')
        else:
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveVerstecken(\'{nid}\',true,this)">'
                           f'{t("live.knopf_verstecken")}</button>')
    # Vorschau-Bild NUR fuer aktive Kacheln (User-Wunsch 13.08.): das JPEG
    # kommt aus dem Detektor-Thread der Engine (/live_bild, verarbeitete
    # Waechter-Skala) — man sieht, was der Waechter sieht. Refresh macht
    # der Poll in app.js ueber den data-kamera-Anker; onerror blendet aus
    # (Engine-Neustart/Frische-404), onload wieder ein.
    bild = (f'<img class="lv-vorschau" data-kamera="{nid}" alt="" '
            f'src="/live_bild/{nid}?t=0" '
            f'onerror="this.style.display=\'none\'" '
            f'onload="this.style.display=\'\'">'
            if z == "active" else "")
    return (
        f'<div class="card lv-kachel lv-{farbe}">'
        f'<div class="kamhead"><b>{html.escape(name)}</b>{fremd}'
        f'<span class="dim num">{res}</span>{_pill(z)}</div>'
        + bild
        + detail
        + _zaehler_zeile(kd.get("live"))
        + _test_zeile(kd.get("test"), kd.get("guard"))
        + _test_fehler_zeile(kd.get("test_fehler"))
        + (_messung_zeile(kd.get("messung"), kd.get("guard"))
           if not gesperrt else "")
        + f'<div class="lv-knoepfe">{" ".join(knoepfe)}</div>'
        + f'<div class="dim lv-zeile" id="lv-job-{nid}"></div>'
        + '</div>')


def _gruppe_html(nach_area, cam_area, kds, gesperrt):
    """Kacheln EINER Gruppe rendern — optional nach Area unterteilt
    (?gruppe=area): je Area eine schmale Zwischenzeile, Kameras ohne Area
    unter 'No area' ans Ende. Ohne Schalter die Frigate-Reihenfolge."""
    if not nach_area:
        return '<div class="lv-grid">' + "".join(
            _karte(kd, gesperrt) for kd in kds) + '</div>'
    je_area = {}
    for kd in kds:
        je_area.setdefault((cam_area or {}).get(kd["name"]) or "", []).append(kd)
    teile = []
    for area in sorted(je_area, key=lambda a: (a == "", a)):
        teile.append(f'<div class="dim lv-areazeile">'
                     f'{html.escape(area) if area else t("live.gruppe.ohne_area")}</div>')
        teile.append('<div class="lv-grid">' + "".join(
            _karte(kd, gesperrt) for kd in je_area[area]) + '</div>')
    return "".join(teile)


def uebersicht(kacheln, engine_info, gesperrt, frigate_fehler=None,
               nach_area=False, cam_area=None, cpu_begrenzt=False,
               container_last=None):
    """-> Seiten-INHALT der Kachel-Uebersicht (.186: Zustands-Gruppen statt
    einer Wand; 'Not set up' und 'Hidden' eingeklappt)."""
    fehlerbanner = (f'<div class="banner">'
                    + t("live.banner.kameraliste",
                        fehler=html.escape(str(frigate_fehler))) + '</div>'
                    if frigate_fehler else "")
    grp = gruppen(kacheln)
    # Anzeige-Titel je Gruppe aus t(); die EN-Literale in GRUPPEN bleiben
    # als Kennungs-Kontrakt (harnisch_live1 iteriert die Paare) und als
    # Fallback — Deckungs-Vertrag: Map-Schluessel == GRUPPEN-Tokens.
    titel_t = {"laufend": t("live.gruppe.laufend"),
               "bereit": t("live.gruppe.bereit"),
               "rest": t("live.gruppe.rest"),
               "versteckt": t("live.gruppe.versteckt")}
    abschnitte = []
    for schluessel, titel in GRUPPEN:
        titel = titel_t.get(schluessel, titel)
        kds = grp[schluessel]
        if not kds:
            continue
        inhalt_g = _gruppe_html(nach_area, cam_area, kds, gesperrt)
        if schluessel in ("rest", "versteckt"):
            abschnitte.append(
                f'<details class="lv-abschnitt"><summary>{titel} '
                f'({len(kds)})</summary>{inhalt_g}</details>')
        else:
            abschnitte.append(
                f'<div class="lv-abschnitt"><div class="lv-kopfzeile">'
                f'{titel} ({len(kds)})</div>{inhalt_g}</div>')
    schalter = (f'<a class="gtb" href="/live" '
                f'onclick="liveAreaMerken(false)">{t("live.schalter.ungruppiert")}</a>'
                if nach_area else
                f'<a class="gtb" href="/live?gruppe=area" '
                f'onclick="liveAreaMerken(true)">{t("live.schalter.area")}</a>')
    sperr_karte = ""
    if cpu_begrenzt and not gesperrt:
        # Stufe-0-Grenze: der Satzrest mit <b>Measure load</b> bleibt literal.
        sperr_karte = (f'<div class="card"><b>{t("live.sperre.cpu_titel")}</b>'
                       f'<div class="dim">{html.escape(t("live.hinweis_cpu"))} '
                       'Use <b>Measure load</b> per camera and the load '
                       'line above before enabling more.</div></div>')
    if gesperrt:
        sperr_grund = (engine_info or {}).get("sperr_grund") or ""
        sperr_karte = (f'<div class="card"><b>{t("live.sperre.titel")}</b>'
                       f'<div class="dim">{t("live.sperre.satz")}'
                       + (f' {html.escape(sperr_grund)}.' if sperr_grund
                          else ' ' + t("live.sperre.cpu_only"))
                       + '</div></div>')
    # Erklaer-Kachel (User-Auflage 12.08. mittags, C2): oben, GESAMTE
    # Breite, KURZ — Zweck, Leistungs-Hinweis, Read-more-Link. Der fruehere
    # Kurz-Erklaertext (<p class="sub">) ist hierin aufgegangen.
    # Stufe-0-Grenze: Satz 2 traegt <b>Measure load</b> — bleibt literal.
    erklaer = (
        '<div class="card lv-erklaer">'
        f'<b>{t("live.erklaer.titel")}</b>'
        f'<div class="dim lv-zeile">{t("live.erklaer.satz1")}</div>'
        '<div class="dim lv-zeile">It is a fast trigger, not a verdict — the '
        'confirmed identification still comes from the normal analysis. '
        'Every active watcher draws real GPU/CPU capacity: pick the cameras '
        'that matter and use <b>Measure load</b> before enabling. '
        + html.escape(t("live.hinweis_cpu") if cpu_begrenzt
                      else t("live.hinweis_gpu")) + '</div>'
        f'<div class="dim lv-zeile"><a href="{DOKU_URL}" target="_blank" '
        f'rel="noopener">{t("live.erklaer.link")}</a></div>'
        '</div>')
    return (
        fehlerbanner
        + f'<h2>{t("live.titel")}</h2>'
        + erklaer
        + sperr_karte
        + _engine_karte(engine_info, gesperrt, container_last)
        + '<div class="dim lv-zeile" id="lv-auftrag"></div>'
        + (f'<div class="lv-schalterzeile">{schalter}</div>'
           if kacheln else "")
        + ("".join(abschnitte) if abschnitte else
           f'<div class="leer"><b>{t("live.leer.titel")}</b><br><small>'
           + t("live.leer.hinweis") + '</small></div>')
        + '<script>window._livePage=true;</script>')


def _save_knopf(gesperrt):
    """Save-Knopf der Detailseite — auf gesperrten Builds GAR NICHT rendern
    (rc_p2_ui KANN 4: die Kachel sagt 'Bedienelemente aus', der Server weist
    /live_speichern seit dem Fix-Zyklus ab — ein sichtbarer Knopf, der nur
    einen Fehler erzeugt, widersprach beidem). Eigener Baustein, damit der
    Mutations-Selbsttest die Sperre fassen kann."""
    if gesperrt:
        return ""
    return ('<button class="gtb on" onclick="liveSpeichern(this)">'
            + t("live.knopf_speichern") + '</button> ')


def detail(name, guard, kd, gesperrt, vorrat=0, deckel=0, regel=(2, 0),
           det_default=0.4, beweg_vorgabe=(30, 10)):
    """-> Seiten-INHALT der Konfigurationsansicht /live/<kamera>.

    UMGEBAUT am 31.08. (User-Befund: "Bandwurmseite"). Die Seite trug sechs
    gleichrangige Karten untereinander, in denen das Selten-Gebrauchte (Quelle,
    Aufloesung, Last-Messung) genauso viel Platz und Fliesstext bekam wie das
    Taegliche. Nichts ist weggefallen — jeder Wert steht noch hier, nur neu
    geordnet (Streich-Vorschlaege liegen dem User getrennt vor, nichts davon ist
    ohne sein Wort umgesetzt):

      Ankunft      Kopf mit Kameraname, Zustand, Vorschaubild des laufenden
                   Waechters ("sieht er ueberhaupt etwas?") — die Frage, mit der
                   man diese Seite betritt.
      Erster Blick vier Kacheln nebeneinander statt einer Spalte: Erkennung,
                   Melden, Frigate-Events, Quelltest.
      EINE Handlung der Primaer-Knopf oben (Enable, bzw. der Quelltest, solange
                   es keinen gruenen gibt) — vorher lag er ganz unten hinter
                   allem.
      Rest         alles Selten-Gebrauchte unter EINEM Aufklapper "Advanced".

    vorrat/deckel = Stand des Kalibrier-Vorrats dieser Kamera (Bilder / Deckel),
    regel = (n, t_s) der Erkannt-Regel — beide reicht der Handler herein
    (Daten als Parameter, Muster dieses Moduls; die Auslegung der Regel selbst
    kommt aus livewache.Engine.erkannt_regel, nie aus einer zweiten Rechnung).
    beweg_vorgabe = (schwelle, flaeche) der Bewegungs-Abtastung als
    Platzhalter-Text — ebenfalls vom Handler aus der EINEN Quelle
    (livewache.BEWEG_SCHWELLE/BEWEG_FLAECHE), damit die Seite keine zweite
    Zahl traegt."""
    nid = html.escape(name, quote=True)
    g = guard or {}
    quelle = g.get("quelle") or "proxy"
    # Die Quell-Tokens proxy/direct/url sind Anzeige==Kennung (radio-value
    # UND sichtbares Wort) und bleiben literal; nur die Erklaerung je
    # Zeile ist Schluessel.
    radios = "".join(
        f'<label class="lv-radio"><input type="radio" name="lv-quelle" '
        f'value="{q}"{" checked" if quelle == q else ""}> {q} '
        f'<span class="dim">— {beschr}</span></label>'
        for q, beschr in (
            ("proxy", t("live.quelle.proxy")),
            ("direct", t("live.quelle.direct")),
            ("url", t("live.quelle.url"))))
    # .194 (User: 360-2160, "default immer auf 1080p"): Verarbeitungshoehe je
    # Kachel. "default" = KEIN Guard-Feld -> der Fingerprint des laufenden
    # Tests bleibt beim blossen Speichern stabil (ein expliziter Wert zaehlt
    # als Quell-Aenderung und entwertet den Test ehrlich).
    hoehe_wert = g.get("hoehe")
    # Welle 1, Etappe C: 1440/2160 sind gestrichen (gemessen ohne Gewinn) und
    # stehen deshalb nicht mehr zur Wahl. Eine Kamera, die einen dieser Werte
    # GESPEICHERT hat, behaelt ihn im Store (sonst verfiele ihr Quelltest) —
    # die Seite sagt dann ehrlich, mit welcher Hoehe sie wirklich laeuft.
    hoehen = "".join(
        f'<label class="lv-radio"><input type="radio" name="lv-hoehe" '
        f'value="{w}"{" checked" if hoehe_wert == (int(w) if w else None) else ""}>'
        f' {beschr}</label>'
        for w, beschr in (("", t("live.hoehe.default")),
                          ("360", t("live.hoehe.h360")),
                          ("720", t("live.hoehe.h720")),
                          ("1080", t("live.hoehe.h1080"))))
    if hoehe_wert in HOEHEN_ALT:
        hoehen += (f'<div class="lv-zeile lv-hinweis">'
                   f'{html.escape(t("live.hoehe.alt_hinweis", alt=hoehe_wert, jetzt=max(HOEHEN_ERLAUBT)))}'
                   f'</div>')
    # .200 (Fix 3): kein eigenes Kanal-Literal mehr — gespeicherte Waechter kommen
    # normalisiert aus guards_lesen, NEUE bekommen die Vorbelegung im /live/-Handler
    # aus melden.konfigurierte_kanaele (die eine Quelle). Fehlt beides: nichts vorwaehlen.
    kanaele = g.get("kanaele") or []
    kboxen = "".join(
        f'<label class="lv-radio"><input type="checkbox" class="lv-kanal" '
        f'value="{k}"{" checked" if k in kanaele else ""}> {k}</label>'
        for k in ("pushover", "telegram", "mqtt"))
    z = kd["zustand"]
    an = bool(g.get("enabled"))
    schalter = ""
    if not gesperrt:
        if z in ("tested", "untested"):
            schalter = (f'<button class="gtb on" '
                        f'onclick="liveSchalter(\'{nid}\',true,this)">'
                        f'{t("live.knopf_enable")}</button>')
        elif an:
            schalter = (f'<button class="gtb" '
                        f'onclick="liveSchalter(\'{nid}\',false,this)">'
                        f'{t("live.knopf_disable")}</button>')
    # ANKUNFT (User-Befund 31.08. an der deployten Seite: die Kopfkarte war
    # fast leer und trug nur zwei Knoepfe): laeuft der Waechter, steht hier
    # sein Vorschaubild — dasselbe JPEG wie auf der Kachel, aus dem
    # Detektor-Thread in Waechter-Skala, also WAS DER WAECHTER SIEHT. Laeuft er
    # nicht, gibt es kein ehrliches Bild: der Vorschau-Endpunkt liefert
    # aelteres Material bewusst NICHT aus (VORSCHAU_FRISCH_S, sonst haenge ein
    # eingefrorenes Bild als "live" an der Seite). Statt eines Platzhalter-
    # Bildes ohne Aussagewert steht dort deshalb ein Feld mit dem ZUSTAND und
    # dem, was der letzte Quelltest an dieser Kamera gemessen hat.
    if z == "active":
        bild = (f'<img class="lv-vorschau" data-kamera="{nid}" alt="" '
                f'src="/live_bild/{nid}?t=0" '
                f'onerror="this.style.display=\'none\'" '
                f'onload="this.style.display=\'\'">')
    else:
        _tb = g.get("test") or {}
        _gemessen = (t("live.detail.kein_bild_test",
                       aufloesung=_tb.get("aufloesung", "?"),
                       skala=_tb.get("skala", "?"))
                     if _tb.get("ok") else t("live.detail.kein_bild_ohne_test"))
        bild = (f'<div class="lv-kein-bild">'
                f'<div class="lv-kein-bild-kopf">{t("live.detail.kein_bild")}</div>'
                f'<div class="dim lv-zeile">{html.escape(_gemessen)}</div></div>')
    # --- Kachel 1: Erkennung (Live-Umbau 31.08., alles je Kamera) ---------
    # §8.8: die Zahl kommt vorformatiert aus dem Code, der Schluessel kennt nur
    # {wert} und {marke} — keine Werks-Zahl im Uebersetzungstext (sie wuerde
    # beim naechsten Mess-Entscheid in fuenf Sprachen falsch stehen).
    det_wert = g.get("det_min")
    det_txt = f"{float(det_wert if det_wert is not None else det_default):.2f}"
    det_marke = "" if det_wert is not None else t("live.erkennung.det_vorgabe")
    def _latte(wert):
        return (f"{float(wert):.3f}" if wert is not None
                else t("live.erkennung.latte_aus"))

    # Schluessel LITERAL an der Aufrufstelle (nicht ueber eine Schleifen-
    # Variable): die Sprach-Deckungsstufe liest die Aufrufe statisch und haelt
    # einen so aufgeloesten Schluessel sonst fuer tot.
    guete_txt = (t("live.erkennung.latte_e", wert=_latte(g.get("guete_e_min")))
                 + " · "
                 + t("live.erkennung.latte_t", wert=_latte(g.get("guete_t_min"))))
    k_erkennung = (
        f'<div class="dim lv-zeile">'
        f'{t("live.erkennung.det_zeile", wert=det_txt, marke=det_marke)}</div>'
        f'<div class="lv-zeile">{t("live.erkennung.regel_vor")} '
        f'<input id="lv-erkannt-n" size="3" '
        f'value="{html.escape(str(g.get("erkannt_n") or regel[0]))}"> '
        f'{t("live.erkennung.regel_mitte")} '
        f'<input id="lv-erkannt-t" size="4" '
        f'value="{html.escape(str(int(g.get("erkannt_t_s") or 0)))}"> '
        f'{t("live.erkennung.regel_nach")}</div>'
        f'<div class="dim lv-zeile">{t("live.erkennung.regel_hinweis")}</div>'
        f'<div class="lv-zeile">{t("live.erkennung.fenster_vor")} '
        f'<input id="lv-erkannt-fenster" size="4" '
        f'value="{html.escape(_fmt_fenster(g.get("erkannt_fenster_s")))}"> '
        f'{t("live.erkennung.fenster_nach")}</div>'
        f'<div class="dim lv-zeile">{t("live.erkennung.fenster_hinweis")}</div>'
        + (f'<div class="dim lv-zeile">'
           f'{t("live.erkennung.vorrat_zeile", n=vorrat, deckel=deckel)}</div>'
           if deckel else
           f'<div class="dim lv-zeile">{t("live.erkennung.vorrat_aus")}</div>')
        # .407 (User-Spezifikation): der Schalter gegen die Doppelanalyse.
        # Er steht HIER, direkt neben dem Wächter-Verhalten dieser Kamera,
        # weil er nur zusammen mit einem LAUFENDEN Wächter etwas tut — die
        # Prosa darunter sagt genau das, damit niemand ihn für einen
        # Ausschalter der Erkennung hält.
        + f'<label class="lv-radio"><input type="checkbox" id="lv-worker-aus"'
        + f'{" checked" if bool(g.get("worker_aus")) else ""}> '
        + f'{t("live.workeraus.schalter")}</label>'
        + f'<div class="dim lv-zeile">{t("live.workeraus.erklaerung")}</div>'
        + f'<div class="lv-knoepfe">'
          # Zentral-Umbau 31.08.: die Kalibrierseite liegt unter /kalibrierung/
          # (eigener Menuepunkt). Der Knopf hier bleibt — er ist der kurze Weg
          # aus dem Waechter heraus —, zeigt aber auf DIE eine Adresse.
          f'<a class="gtb" href="/kalibrierung/{nid}">'
          f'{t("live.knopf_kalibrieren")}</a>'
        + (f'<button class="gtb" onclick="liveVorratLeeren(\'{nid}\',this)">'
           f'{t("live.knopf_vorrat_leeren")}</button>' if vorrat else "")
        + '</div>')
    # --- Kachel 2: Melden -------------------------------------------------
    k_melden = (
        # Zwei benannte Gruppen in EINER Kachel (die Ueberschriften sind die
        # beiden bisherigen Karten-Titel): Zeiten und Kanaele gehoeren zusammen
        # — man stellt sie in einem Zug ein —, bleiben aber unterscheidbar.
        f'<div class="dim lv-zeile"><b>{t("live.abschnitt.alarm")}</b></div>'
        f'<div class="lv-zeile">{t("live.detail.scharf_label")} '
        f'<input id="lv-scharf" size="5" '
        f'value="{html.escape(str(g.get("wieder_scharf_s", 120)))}"></div>'
        f'<div class="dim lv-zeile">{t("live.detail.scharf_hinweis")}</div>'
        f'<div class="lv-zeile">{t("live.detail.ende_label")} '
        f'<input id="lv-ende" size="5" '
        f'value="{html.escape(str(g.get("ende_ohne_gesicht_s", 10)))}"></div>'
        f'<div class="dim lv-zeile">{t("live.detail.ende_hinweis")}</div>'
        + f'<div class="dim lv-zeile"><b>{t("live.abschnitt.kanaele")}</b></div>'
        + kboxen
        # .197: der "quick verdict"-Haken ist weg (User: Enable heisst alles
        # laeuft) — die vorlaeufige Namens-Stufe gehoert seit dem Voting zu
        # jedem eingeschalteten Waechter, sofern Referenzen da sind.
        + f'<div class="dim lv-zeile">{t("live.detail.namensschaetzung")}</div>')
    # --- Abtastung (Welle 1, Etappe A): Werte fuer die Advanced-Karte -----
    bw_an = bool(g.get("bewegung_gate", True))
    ruhe_wert = g.get("ruhe_takt_s")
    bw_schwelle = g.get("bewegung_schwelle")
    bw_flaeche = g.get("bewegung_flaeche")
    # Die Vorgaben kommen als Parameter herein (Daten als Parameter, Muster
    # dieses Moduls) — nie als zweite Zahl im Renderer.
    bw_schwelle_vor, bw_flaeche_vor = beweg_vorgabe
    # --- Kachel 3: Frigate-Events (eigener Schalter, Vorgabe AUS) ---------
    fr_an = bool(g.get("frigate_events"))
    fr_abstand = g.get("frigate_abstand_s")
    k_frigate = (
        f'<label class="lv-radio"><input type="checkbox" id="lv-frigate"'
        f'{" checked" if fr_an else ""}> {t("live.frigate.schalter")}</label>'
        f'<div class="dim lv-zeile">{t("live.frigate.erklaerung")}</div>'
        f'<div class="lv-zeile">{t("live.frigate.abstand_label")} '
        f'<input id="lv-frigate-abstand" size="5" '
        f'value="{html.escape("" if fr_abstand is None else str(int(fr_abstand)))}" '
        f'placeholder="{html.escape(str(g.get("wieder_scharf_s", 120)))}"></div>'
        f'<div class="dim lv-zeile">{t("live.frigate.abstand_hinweis")}</div>')
    # --- Kachel 4: Quelltest (der Riegel vors Einschalten) ----------------
    k_test = (
        _test_zeile(g.get("test"), g, auffordern=True)
        + _test_fehler_zeile(g.get("test_fehler"))
        # Issue #24 (Tokn59, 18.08.): im gesperrten Zustand fehlten die
        # Knoepfe KOMMENTARLOS — die Karte wirkte kaputt ('can not be
        # clicked or activated in any way'). Jetzt sagt sie, warum.
        + (f'<div class="dim lv-zeile">{t("live.detail.gesperrt_hinweis")}</div>'
           if gesperrt else
           f'<div class="lv-knoepfe"><button class="gtb" '
           f'onclick="liveTest(\'{nid}\',this)">'
           f'{t("live.knopf_test")}</button></div>')
        + f'<div class="dim lv-zeile" id="lv-job-{nid}"></div>')

    def _kachel(titel, inhalt):
        return f'<div class="card lvk"><h3>{titel}</h3>{inhalt}</div>'

    # --- Advanced: alles Selten-Gebrauchte unter EINEM Aufklapper ---------
    # Stufe-0-Grenzen hier unveraendert: der Aufloesungs-Absatz (<b>Measure
    # load</b>) und die Credentials-Zeile (<a>-Link) bleiben literal; die
    # Kanal-Haekchen pushover/telegram/mqtt sind Anzeige==Kennung.
    erweitert = (
        f'<div class="card"><b>{t("live.abschnitt.quelle")}</b>'
        + radios
        + f'<div>{t("live.detail.url_label")} '
          # C4 (Muster Notifications-Secrets): das Feld ist mit der
          # MASKIERTEN URL vorbelegt — das Credential erreicht das HTML nie;
          # bleibt die Maskierung unveraendert, behaelt der Server die
          # gespeicherte URL (live_speichern).
          f'<input id="lv-url" '
          f'value="{html.escape(quelle_maskiert(str(g.get("url") or "")), quote=True)}" '
          f'size="40" placeholder="rtsp://..." autocomplete="off"> '
          f'<span class="dim">{t("live.detail.url_hinweis")}</span></div>'
        + f'<div class="dim lv-zeile">{t("live.detail.quelle_hinweis")}</div></div>'
        + f'<div class="card"><b>{t("live.abschnitt.aufloesung")}</b>'
        + '<div class="dim lv-zeile">The watcher analyzes the stream at this '
          'height (aspect-ratio kept). Higher = sharper face crops for the '
          'name check; the detection net stays the same size, extra cost is '
          'decode/scaling — use <b>Measure load</b> to see the real numbers '
          'on your hardware. Changing this invalidates the source test.</div>'
        + hoehen
        + '</div>'
        # --- Abtastung (Live-Performance Welle 1, Etappe A) ---------------
        # Selten gebraucht, deshalb unter "Advanced" — aber ein echter
        # Verhaltens-Schalter, deshalb sichtbar und nicht nur im Store.
        + f'<div class="card"><b>{t("live.abschnitt.abtastung")}</b>'
        + f'<label class="lv-radio"><input type="checkbox" id="lv-bewegung"'
        + f'{" checked" if bw_an else ""}> {t("live.abtastung.schalter")}</label>'
        + f'<div class="dim lv-zeile">{t("live.abtastung.erklaerung")}</div>'
        + f'<div class="lv-zeile">{t("live.abtastung.ruhe_label")} '
          f'<input id="lv-ruhe-takt" size="5" '
          f'value="{html.escape("" if ruhe_wert is None else str(int(ruhe_wert)))}" '
          f'placeholder="{html.escape(str(g.get("ende_ohne_gesicht_s", 10)))}"> '
          f'{t("live.abtastung.ruhe_einheit")}</div>'
        + f'<div class="dim lv-zeile">{t("live.abtastung.ruhe_hinweis")}</div>'
        # Die zwei Eich-Werte je Kamera: leer = Frigates Auslieferungs-Vorgabe.
        # Sie stehen HIER und nicht in einer globalen Schraube, weil jede
        # Anlage anders ist (User-Auflage 31.08.).
        + f'<div class="lv-zeile">{t("live.abtastung.schwelle_label")} '
          f'<input id="lv-bewegung-schwelle" size="4" '
          f'value="{html.escape("" if bw_schwelle is None else str(int(bw_schwelle)))}" '
          f'placeholder="{bw_schwelle_vor}"> '
          f'&middot; {t("live.abtastung.flaeche_label")} '
          f'<input id="lv-bewegung-flaeche" size="4" '
          f'value="{html.escape("" if bw_flaeche is None else str(int(bw_flaeche)))}" '
          f'placeholder="{bw_flaeche_vor}"></div>'
        + f'<div class="dim lv-zeile">{t("live.abtastung.eich_hinweis")}</div></div>'
        + f'<div class="card"><b>{t("live.abschnitt.guete")}</b>'
        + f'<div class="dim lv-zeile">{guete_txt}</div>'
        + f'<div class="dim lv-zeile">{t("live.erkennung.latte_hinweis")}</div></div>'
        + f'<div class="card"><b>{t("live.abschnitt.last")}</b>'
        + (_messung_zeile(g.get("messung"), g) if not gesperrt else "")
        + ("" if gesperrt else
           f'<div class="lv-knoepfe"><button class="gtb" '
           f'onclick="liveMessung(\'{nid}\',this)">'
           f'{t("live.knopf_messung_lang")}</button> '
           f'<span class="dim">{t("live.detail.messung_hinweis")}</span></div>')
        + '</div>'
        + f'<div class="card"><div class="dim lv-zeile">'
          f'{html.escape(t("live.hinweis_gpu"))}</div>'
          '<div class="dim lv-zeile">Channel credentials live on the '
          '<a href="/benachrichtigungen">Notifications</a> page — test them '
          'there.</div></div>')
    # KOPFZEILE: Titel, Zustand und der Rueckweg in EINER Zeile. Der Rueckweg
    # stand bis .383 als nackter Link ganz unten hinter allen Karten — dort
    # sucht ihn niemand, und auf dem Handy ist er drei Bildschirme entfernt
    # (User-Befund 31.08.).
    return (
        f'<div class="lv-titelzeile">'
        f'<h2>{t("live.detail.titel", name=html.escape(name))} {_pill(z)}</h2>'
        f'<a class="gtb" href="/live">{t("live.detail.link_zurueck")}</a>'
        f'</div>'
        + f'<input type="hidden" id="lv-kamera" value="{nid}">'
        # KOPFKARTE, kompakt (User-Befund 31.08.: "fast leer, nur Save/Enable
        # in einer riesigen Karte"): Bild bzw. Zustands-Feld LINKS, die beiden
        # Handlungen der Seite mit ihrer Antwort RECHTS daneben — statt
        # untereinander ueber die halbe Seite.
        + '<div class="card lv-kopfkarte"><div class="lv-kopfreihe">'
        + f'<div class="lv-kopfbild">{bild}</div>'
        + '<div class="lv-kopftext">'
        + (f'<div class="dim lv-zeile">{html.escape(kd["detail"])}</div>'
           if kd.get("detail") else "")
        # Beide Handlungen der Seite an EINER Stelle, oben, mit der Antwort
        # daneben: vorher stand der Schalter ganz unten hinter sechs Karten,
        # und die Erfolgsmeldung erschien dort, wo gerade niemand hinsah.
        + f'<div class="lv-knoepfe">{_save_knopf(gesperrt)}{schalter}'
        + ' <span id="lv-status" style="color:var(--dim)"></span></div>'
        + '<div class="dim lv-zeile" id="lv-auftrag"></div>'
        + '</div></div></div>'
        + '<div class="lvk-grid">'
        + _kachel(t("live.abschnitt.erkennung"), k_erkennung)
        + _kachel(t("live.abschnitt.melden"), k_melden)
        + _kachel(t("live.abschnitt.frigate"), k_frigate)
        + _kachel(t("live.abschnitt.test"), k_test)
        + '</div>'
        + f'<details class="lv-abschnitt"><summary>'
          f'{t("live.abschnitt.erweitert")}</summary>{erweitert}</details>'
        + '<script>window._livePage=true;</script>')


def alerts_tag(eintraege, gesamt, t0):
    """-> Seiten-INHALT der Tages-Uebersicht /live_alerts (ME1, byte-treu aus
    verifyd extrahiert; Schnappschuss-Beweis scratchpad/me1_schnappschuss.py).
    eintraege = [(auftritt, bilder, videos), ...] — die Medien-Suche je
    Auftritt (livewache.auftritt_medien + Platte-schon-aufgeraeumt-Fallback)
    bleibt beim Handler (Daten als Parameter, Muster dieses Moduls); gesamt =
    Trigger-Zahl aus melde_liste, t0 = Tagesanfang (Epoche)."""
    karten = []
    for a, bilder, videos in eintraege:
        thumbs = "".join(
            f'<a href="/live_alarmbild?p={urllib.parse.quote(b)}"'
            f' target="_blank" rel="noopener">'
            f'<img class="lv-thumb" loading="lazy" '
            f'src="/live_alarmbild?p={urllib.parse.quote(b)}" '
            f'alt=""></a>' for b in bilder)
        vlinks = " ".join(
            f'<a href="/live_alarmbild?p={urllib.parse.quote(v)}"'
            f' target="_blank" rel="noopener">'
            f'{t("livealerts.link_video", n=i + 1)}</a>'
            for i, v in enumerate(videos))
        _bis = (f'&ndash;{time.strftime("%H:%M:%S", time.localtime(a["ts_letzte"]))}'
                if a["ts_letzte"] - a["ts"] >= 1 else "")
        karten.append(
            f'<div class="card lv-auftrittkarte" id="a{int(a["ts"])}">'
            f'<div><b>{html.escape(a.get("person") or t("livealerts.person_unbekannt"))}</b>'
            f' <span class="dim">'
            f'{time.strftime("%H:%M:%S", time.localtime(a["ts"]))}{_bis}'
            f' · {html.escape(a["kamera"])}'
            f' · {t_n("livealerts.trigger", a["trigger"])}'
            f' · {html.escape("+".join(t("livealerts.kanal_keiner") if _kn == "none" else _kn for _kn in a["kanaele"]))}</span></div>'
            + (f'<div class="dim">{html.escape(a["zusatz"][:90])}'
               f'</div>' if a.get("zusatz") else '')
            + (f'<div class="lv-medienreihe">{thumbs}</div>'
               if thumbs else
               f'<div class="dim">{t("livealerts.keine_bilder")}</div>')
            + (f'<div class="dim">{vlinks}</div>' if vlinks else '')
            + '</div>')
    # Zaehler-Splits (§8.10) via t_n; der Satz-Rest ist EIN
    # Ganz-Schluessel mit {tag} (ISO-Datum bleibt Code).
    inhalt = (
        f'<h2>{t("livealerts.titel")}</h2>'
        f'<p class="sub">{t_n("livealerts.kopf.auftritte", len(eintraege))}'
        f' ({t_n("livealerts.trigger", gesamt)})'
        f'{t("livealerts.kopf.satz", tag=time.strftime("%Y-%m-%d", time.localtime(t0)))}'
        f' {t("livealerts.kopf.satz_alt")}</p>'
        + ("".join(karten) if karten else
           f'<div class="leer"><b>{t("livealerts.leer")}</b></div>'))
    return inhalt
