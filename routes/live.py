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

from core.livewache import quelle_fp, quelle_maskiert
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


def _test_zeile(test, guard=None):
    if not test or not test.get("ok"):
        return ""
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


def detail(name, guard, kd, gesperrt):
    """-> Seiten-INHALT der Konfigurationsansicht /live/<kamera> (§2.4)."""
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
    hoehen = "".join(
        f'<label class="lv-radio"><input type="radio" name="lv-hoehe" '
        f'value="{w}"{" checked" if hoehe_wert == (int(w) if w else None) else ""}>'
        f' {beschr}</label>'
        for w, beschr in (("", t("live.hoehe.default")),
                          ("360", t("live.hoehe.h360")),
                          ("720", t("live.hoehe.h720")),
                          ("1080", t("live.hoehe.h1080")),
                          ("1440", t("live.hoehe.h1440")),
                          ("2160", t("live.hoehe.h2160"))))
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
    # Stufe-0-Grenzen hier: der Aufloesungs-Absatz (<b>Measure load</b>) und
    # die Credentials-Zeile (<a>-Link) bleiben literal; die Kanal-Haekchen
    # pushover/telegram/mqtt sind Anzeige==Kennung + Produktnamen.
    return (
        f'<h2>{t("live.detail.titel", name=html.escape(name))} {_pill(z)}</h2>'
        + (f'<p class="sub">{html.escape(kd["detail"])}</p>'
           if kd.get("detail") else "")
        + f'<p class="sub">{html.escape(t("live.hinweis_gpu"))}</p>'
        + f'<input type="hidden" id="lv-kamera" value="{nid}">'
        + f'<div class="card"><b>{t("live.abschnitt.quelle")}</b>'
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
        + f'<div class="card"><b>{t("live.abschnitt.alarm")}</b>'
        + f'<div>{t("live.detail.ende_label")} <input id="lv-ende" size="5" '
          f'value="{html.escape(str(g.get("ende_ohne_gesicht_s", 10)))}"> '
          f'<span class="dim">{t("live.detail.ende_hinweis")}</span></div>'
        + f'<div>{t("live.detail.scharf_label")} <input id="lv-scharf" size="5" '
          f'value="{html.escape(str(g.get("wieder_scharf_s", 120)))}"> '
          f'<span class="dim">{t("live.detail.scharf_hinweis")}</span></div></div>'
        + f'<div class="card"><b>{t("live.abschnitt.kanaele")}</b>'
        + kboxen
        # .197: der "quick verdict"-Haken ist weg (User: Enable heisst alles
        # laeuft) — die vorlaeufige Namens-Stufe gehoert seit dem Voting zu
        # jedem eingeschalteten Waechter, sofern Referenzen da sind.
        + f'<div class="dim lv-zeile">{t("live.detail.namensschaetzung")}</div>'
        + '<div class="dim lv-zeile">Channel credentials live on the '
          '<a href="/benachrichtigungen">Notifications</a> page — test them '
          'there.</div></div>'
        + f'<div class="card"><b>{t("live.abschnitt.test")}</b>'
        + _test_zeile(g.get("test"), g)
        + _test_fehler_zeile(g.get("test_fehler"))
        + (_messung_zeile(g.get("messung"), g) if not gesperrt else "")
        # Issue #24 (Tokn59, 18.08.): im gesperrten Zustand fehlten die
        # Knoepfe KOMMENTARLOS — die Karte wirkte kaputt ('can not be
        # clicked or activated in any way'). Jetzt sagt sie, warum.
        + (f'<div class="dim lv-zeile">{t("live.detail.gesperrt_hinweis")}</div>'
           if gesperrt else
           f'<button class="gtb" onclick="liveTest(\'{nid}\',this)">'
           f'{t("live.knopf_test")}</button> '
           f'<button class="gtb" onclick="liveMessung(\'{nid}\',this)">'
           f'{t("live.knopf_messung_lang")}</button> '
           f'<span class="dim">{t("live.detail.messung_hinweis")}</span>')
        + f'<div class="dim lv-zeile" id="lv-job-{nid}"></div>'
        + '<div class="dim lv-zeile" id="lv-auftrag"></div></div>'
        + '<p>' + _save_knopf(gesperrt) + schalter
        + ' <span id="lv-status" style="color:var(--dim)"></span> '
        + f'&nbsp; <a href="/live">{t("live.detail.link_zurueck")}</a></p>'
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
