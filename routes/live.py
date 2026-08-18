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
"""
import html
import time

from core.livewache import quelle_fp, quelle_maskiert
from core.registry import LIVE_ZUSTAENDE

GPU_HINWEIS = ("Works with a GPU only for now — we are working on a CPU "
               "option but can't promise it.")
# CPU-Runde 17.08. (User-Go nach Messung): auf der cpu-Variante ist Live
# BEGRENZT erlaubt — der Text sagt ehrlich, was gemessen ist, und verspricht
# keine Unter-einer-Sekunde-Reaktion.
CPU_HINWEIS = ("CPU mode: watchers are expensive here — the quick check "
               "typically takes 1–2 s (a GPU build reacts in under a "
               "second), and additional watchers slow each other down. "
               "How many you run is your call; we recommend starting "
               "with one.")

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
        return f" ({tage:.0f} day(s) old)"
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
    t = (f'source test {_wann(test.get("ts"))}: '
         f'{test.get("aufloesung", "?")} → {test.get("skala", "?")}, '
         f'{test.get("bilder_s", "?")} frames/s'
         # .196: Alt-Tests und Datei-Quellen tragen Durchsatz statt
         # Lieferrate — ehrlich kennzeichnen statt eine echte fps vorzugeben.
         + ("" if test.get("bilder_s_art") == "delivery"
            else " (throughput, not delivery rate — rerun the source test)")
         + f', provider {test.get("provider", "?")}'
         + ("" if test.get("hw") else " (software decode)")
         + _alter_marke(test.get("ts"))
         + (" — INVALIDATED: source changed since this test"
            if _fp_veraltet(test, guard) else ""))
    return f'<div class="dim lv-zeile">{html.escape(t)}</div>'


def _test_fehler_zeile(tf):
    """UI-M3: der letzte FEHLGESCHLAGENE Quelltest, sichtbar (der gruene
    test-Block bleibt daneben stehen — er traegt den Enable-Riegel)."""
    if not tf or not tf.get("fehler"):
        return ""
    t = f'last source test FAILED ({_wann(tf.get("ts"))}): {tf["fehler"]}'
    return f'<div class="dim lv-zeile">{html.escape(t)}</div>'


def _messung_zeile(messung, guard=None):
    if messung and messung.get("ok"):
        t = (f'load measured on {_wann(messung.get("ts"))}: '
             f'{messung.get("text", "")}'
             + _alter_marke(messung.get("ts"))
             + (" — STALE: source changed since this measurement, measure "
                "again" if _fp_veraltet(messung, guard) else ""))
        return f'<div class="dim lv-zeile">{html.escape(t)}</div>'
    if messung and messung.get("fehler"):
        t = (f'last load measurement FAILED ({_wann(messung.get("ts"))}): '
             f'{messung["fehler"]}')
        return f'<div class="dim lv-zeile">{html.escape(t)}</div>'
    return ('<div class="dim lv-zeile">load not measured yet — use '
            '<b>Measure load</b> before enabling</div>')


def _zaehler_zeile(live):
    if not live:
        return ""
    teile = [f'{live.get("auftritte", 0)} appearances',
             f'{live.get("trigger", 0)} triggers',
             f'{live.get("gemeldet", 0)} alerts']
    lt = live.get("letzter_trigger_ts")
    if lt:
        teile.append("last trigger "
                     + time.strftime("%H:%M:%S", time.localtime(float(lt))))
    return ('<div class="dim lv-zeile">since engine start: '
            + html.escape(" · ".join(teile)) + "</div>")


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
        return ('<div class="card"><b>Live engine: not running</b>'
                + aufsicht_zeile
                + '<div class="dim">No heartbeat from the engine process. '
                'Tiles show the saved configuration; enabling, testing '
                'against a running watcher and load measurements need the '
                'engine — the service starts it automatically once at least '
                'one watcher is enabled.</div></div>')
    slots = st.get("slots") or {}
    sch = st.get("scheduler") or {}
    je = slots.get("je_stream_mb")
    je_txt = (f'{je:.0f} MB per stream ({slots.get("je_stream_quelle", "")})'
              if je is not None else
              "per-stream RAM not yet measured on this machine")
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
        zeilen.append(
            f'suslik CPU right now: {_ck:g}'
            + (f' of {_cl:g} allowed cores' if _cl else ' cores')
            + ' (whole container: watchers, analysis, service)')
    zeilen += [
        # UI-KANN 10: Python-Leerwert nie in die Karte ('RSS None MB').
        f'engine RSS {rss if rss is not None else "?"} MB'
        + (f' · base cost {slots.get("grundkosten_mb"):.0f} MB'
           if slots.get("grundkosten_mb") is not None else ""),
        je_txt,
        (f'{frei:.0f} MB RAM free ({slots.get("ram_quelle", "?")})'
         if frei is not None else "RAM: no container limit readable"),
        f'detector {slots.get("det_ms", "?")} ms/frame '
        f'({slots.get("det_ms_quelle", "?")})',
        f'throttle level {sch.get("drossel_stufe", "?")}, utilization '
        f'{sch.get("auslastung", "?")}',
    ]
    # UI-M4 Rest-RAM-Ehrlichkeit (§2.3): was nach EINEM weiteren Stream
    # rechnerisch uebrig bliebe, mit Warnstufe unter der Restgrenze.
    rest = slots.get("rest_nach_slot_mb")
    if rest is not None:
        zeilen.append(f'after one more stream: ~{rest:.0f} MB RAM would '
                      f'remain'
                      + (' — BELOW the safety floor, no further slot'
                         if slots.get("rest_warnung") else ''))
    # .196: der Deckel kommt nur noch aus den zwei Notbremsen (harter Deckel,
    # RAM-Boden als Messwert) — kein Lastmodell mehr (User: Messwerte
    # informieren, sie entscheiden nicht).
    emax = slots.get("effektiv_max")
    if emax is not None:
        zeilen.append(f'capacity: up to {emax} watcher(s) (hard cap '
                      f'{slots.get("hart_max", "?")}) — limited by: '
                      f'{slots.get("effektiv_grund") or "?"}')
    else:
        zeilen.append(f'hard cap {slots.get("hart_max", "?")} watchers')
    # Standalone LAUT auf der Karte (Bauplan-Auftrag Phase 4): eine fremd
    # gestartete Engine liefert zwar Herzschlag, aber der Dienst startet
    # keine zweite und uebernimmt erst nach deren Ende.
    kopf = ("Live engine: running (standalone engine detected)"
            if aufsicht.get("standalone") else "Live engine: running")
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
        if z in ("active", "disturbed"):
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
             else ' <span class="pill warn" title="configured here, but '
                  'this camera is not in Frigate right now">not in '
                  'Frigate</span>')
    res_text, res_echt = kopf_aufloesung(kd)
    res = (html.escape(res_text) if res_echt else
           html.escape(res_text).replace(
               "(detect)",
               '<span title="Frigate detect stream — the real stream '
               'resolution appears after the service probes the stream or '
               'a source test runs">(detect)</span>'))
    knoepfe = [f'<a class="gtb" href="/live/{nid}">Configure</a>']
    if not gesperrt:
        g = kd.get("guard")
        if g is not None or kd.get("in_frigate"):
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveTest(\'{nid}\',this)">'
                           f'Run source test</button>')
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveMessung(\'{nid}\',this)">'
                           f'Measure load</button>')
        if z == "tested":
            knoepfe.append(f'<button class="gtb on" '
                           f'onclick="liveSchalter(\'{nid}\',true,this)">'
                           f'Enable</button>')
        elif g is not None and g.get("enabled"):
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveSchalter(\'{nid}\',false,this)">'
                           f'Disable</button>')
    # Hide/Show (User 13.08.) — NICHT an laufenden Kacheln (die Running-
    # Gruppe zeigt immer alles; erst stoppen, dann verstecken).
    if kd["zustand"] not in ("active", "disturbed"):
        if kd.get("versteckt"):
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveVerstecken(\'{nid}\',false,this)">'
                           f'Show</button>')
        else:
            knoepfe.append(f'<button class="gtb" '
                           f'onclick="liveVerstecken(\'{nid}\',true,this)">'
                           f'Hide</button>')
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
                     f'{html.escape(area) if area else "No area"}</div>')
        teile.append('<div class="lv-grid">' + "".join(
            _karte(kd, gesperrt) for kd in je_area[area]) + '</div>')
    return "".join(teile)


def uebersicht(kacheln, engine_info, gesperrt, frigate_fehler=None,
               nach_area=False, cam_area=None, cpu_begrenzt=False,
               container_last=None):
    """-> Seiten-INHALT der Kachel-Uebersicht (.186: Zustands-Gruppen statt
    einer Wand; 'Not set up' und 'Hidden' eingeklappt)."""
    fehlerbanner = (f'<div class="banner">Could not read the Frigate camera '
                    f'list: {html.escape(str(frigate_fehler))}</div>'
                    if frigate_fehler else "")
    grp = gruppen(kacheln)
    abschnitte = []
    for schluessel, titel in GRUPPEN:
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
                f'onclick="liveAreaMerken(false)">ungrouped view</a>'
                if nach_area else
                f'<a class="gtb" href="/live?gruppe=area" '
                f'onclick="liveAreaMerken(true)">group by area</a>')
    sperr_karte = ""
    if cpu_begrenzt and not gesperrt:
        sperr_karte = ('<div class="card"><b>CPU mode</b>'
                       f'<div class="dim">{html.escape(CPU_HINWEIS)} '
                       'Use <b>Measure load</b> per camera and the load '
                       'line above before enabling more.</div></div>')
    if gesperrt:
        sperr_grund = (engine_info or {}).get("sperr_grund") or ""
        sperr_karte = ('<div class="card"><b>Not available on this build</b>'
                       '<div class="dim">Live watchers require a GPU build — '
                       'integrated Intel graphics (gpu / gpu-legacy images), '
                       'an NVIDIA card (cuda image) or an AMD card (rocm '
                       'image) all qualify.'
                       + (f' {html.escape(sperr_grund)}.' if sperr_grund
                          else ' They are not available on the CPU-only '
                               'image.')
                       + '</div></div>')
    # Erklaer-Kachel (User-Auflage 12.08. mittags, C2): oben, GESAMTE
    # Breite, KURZ — Zweck, Leistungs-Hinweis, Read-more-Link. Der fruehere
    # Kurz-Erklaertext (<p class="sub">) ist hierin aufgegangen.
    erklaer = (
        '<div class="card lv-erklaer">'
        '<b>Live watchers — instant reaction at the camera stream</b>'
        '<div class="dim lv-zeile">A live watcher connects straight to one '
        'camera stream and reacts while the person is still in the picture: '
        'the first face starts a check, and after the configured number of '
        'consistent detections a verified signal goes out — the goal is '
        'under one second (measured 199–801 ms on the reference setup). Use '
        'it to trigger home automations, e.g. via MQTT.</div>'
        '<div class="dim lv-zeile">It is a fast trigger, not a verdict — the '
        'confirmed identification still comes from the normal analysis. '
        'Every active watcher draws real GPU/CPU capacity: pick the cameras '
        'that matter and use <b>Measure load</b> before enabling. '
        + html.escape(CPU_HINWEIS if cpu_begrenzt else GPU_HINWEIS) + '</div>'
        f'<div class="dim lv-zeile"><a href="{DOKU_URL}" target="_blank" '
        f'rel="noopener">Read more: how live watchers work</a></div>'
        '</div>')
    return (
        fehlerbanner
        + '<h2>Live watchers</h2>'
        + erklaer
        + sperr_karte
        + _engine_karte(engine_info, gesperrt, container_last)
        + '<div class="dim lv-zeile" id="lv-auftrag"></div>'
        + (f'<div class="lv-schalterzeile">{schalter}</div>'
           if kacheln else "")
        + ("".join(abschnitte) if abschnitte else
           '<div class="leer"><b>No cameras found.</b><br><small>Configure '
           'the Frigate connection first — tiles appear per camera.'
           '</small></div>')
        + '<script>window._livePage=true;</script>')


def _save_knopf(gesperrt):
    """Save-Knopf der Detailseite — auf gesperrten Builds GAR NICHT rendern
    (rc_p2_ui KANN 4: die Kachel sagt 'Bedienelemente aus', der Server weist
    /live_speichern seit dem Fix-Zyklus ab — ein sichtbarer Knopf, der nur
    einen Fehler erzeugt, widersprach beidem). Eigener Baustein, damit der
    Mutations-Selbsttest die Sperre fassen kann."""
    if gesperrt:
        return ""
    return '<button class="gtb on" onclick="liveSpeichern(this)">Save</button> '


def detail(name, guard, kd, gesperrt):
    """-> Seiten-INHALT der Konfigurationsansicht /live/<kamera> (§2.4)."""
    nid = html.escape(name, quote=True)
    g = guard or {}
    quelle = g.get("quelle") or "proxy"
    radios = "".join(
        f'<label class="lv-radio"><input type="radio" name="lv-quelle" '
        f'value="{q}"{" checked" if quelle == q else ""}> {q} '
        f'<span class="dim">— {t}</span></label>'
        for q, t in (
            ("proxy", "go2rtc restream via Frigate (default, recommended)"),
            ("direct", "camera producer URL discovered via go2rtc"),
            ("url", "a stream URL you enter yourself")))
    # .194 (User: 360-2160, "default immer auf 1080p"): Verarbeitungshoehe je
    # Kachel. "default" = KEIN Guard-Feld -> der Fingerprint des laufenden
    # Tests bleibt beim blossen Speichern stabil (ein expliziter Wert zaehlt
    # als Quell-Aenderung und entwertet den Test ehrlich).
    hoehe_wert = g.get("hoehe")
    hoehen = "".join(
        f'<label class="lv-radio"><input type="radio" name="lv-hoehe" '
        f'value="{w}"{" checked" if hoehe_wert == (int(w) if w else None) else ""}>'
        f' {t}</label>'
        for w, t in (("", "default (1080p)"),
                     ("360", "360p — weak-GPU fallback, latest name fire (measured)"),
                     ("720", "720p — lighter decode, name fires later"),
                     ("1080", "1080p — sweet spot (measured: name ~2.4 s earlier than 720p)"),
                     ("1440", "1440p — no measured gain over 1080p"),
                     ("2160", "2160p — native 4K, marginal gain, highest decode cost")))
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
        if z == "tested":
            schalter = (f'<button class="gtb on" '
                        f'onclick="liveSchalter(\'{nid}\',true,this)">Enable'
                        f'</button>')
        elif an:
            schalter = (f'<button class="gtb" '
                        f'onclick="liveSchalter(\'{nid}\',false,this)">Disable'
                        f'</button>')
    return (
        f'<h2>Live watcher — {html.escape(name)} {_pill(z)}</h2>'
        + (f'<p class="sub">{html.escape(kd["detail"])}</p>'
           if kd.get("detail") else "")
        + f'<p class="sub">{html.escape(GPU_HINWEIS)}</p>'
        + f'<input type="hidden" id="lv-kamera" value="{nid}">'
        + '<div class="card"><b>Source</b>'
        + radios
        + '<div>Stream URL (source \'url\' only): '
          # C4 (Muster Notifications-Secrets): das Feld ist mit der
          # MASKIERTEN URL vorbelegt — das Credential erreicht das HTML nie;
          # bleibt die Maskierung unveraendert, behaelt der Server die
          # gespeicherte URL (live_speichern).
          f'<input id="lv-url" '
          f'value="{html.escape(quelle_maskiert(str(g.get("url") or "")), quote=True)}" '
          f'size="40" placeholder="rtsp://..." autocomplete="off"> '
          '<span class="dim">credentials in the URL are masked everywhere '
          'they are shown — leave the field as shown to keep the saved URL, '
          'or paste a new one</span></div>'
        + '<div class="dim lv-zeile">Changing the source invalidates the '
          'source test — run it again before enabling.</div></div>'
        + '<div class="card"><b>Processing resolution</b>'
        + '<div class="dim lv-zeile">The watcher analyzes the stream at this '
          'height (aspect-ratio kept). Higher = sharper face crops for the '
          'name check; the detection net stays the same size, extra cost is '
          'decode/scaling — use <b>Measure load</b> to see the real numbers '
          'on your hardware. Changing this invalidates the source test.</div>'
        + hoehen
        + '</div>'
        + '<div class="card"><b>Alarm chain</b>'
        + f'<div>End after no face (s): <input id="lv-ende" size="5" '
          f'value="{html.escape(str(g.get("ende_ohne_gesicht_s", 10)))}"> '
          f'<span class="dim">an appearance ends after this many seconds '
          f'without a face (3–120)</span></div>'
        + f'<div>Re-armed after (s): <input id="lv-scharf" size="5" '
          f'value="{html.escape(str(g.get("wieder_scharf_s", 120)))}"> '
          f'<span class="dim">minimum seconds between alerts — with someone '
          f'present it alerts again after this time; 0 = every trigger '
          f'alerts (0–3600)</span></div></div>'
        + '<div class="card"><b>Notification channels</b>'
        + kboxen
        # .197: der "quick verdict"-Haken ist weg (User: Enable heisst alles
        # laeuft) — die vorlaeufige Namens-Stufe gehoert seit dem Voting zu
        # jedem eingeschalteten Waechter, sofern Referenzen da sind.
        + '<div class="dim lv-zeile">Alerts include a preliminary name '
          'guess ("probably X") when the face matches a known person — '
          'never stored, never used for learning.</div>'
        + '<div class="dim lv-zeile">Channel credentials live on the '
          '<a href="/benachrichtigungen">Notifications</a> page — test them '
          'there.</div></div>'
        + '<div class="card"><b>Test &amp; measure</b>'
        + _test_zeile(g.get("test"), g)
        + _test_fehler_zeile(g.get("test_fehler"))
        + (_messung_zeile(g.get("messung"), g) if not gesperrt else "")
        # Issue #24 (Tokn59, 18.08.): im gesperrten Zustand fehlten die
        # Knoepfe KOMMENTARLOS — die Karte wirkte kaputt ('can not be
        # clicked or activated in any way'). Jetzt sagt sie, warum.
        + ('<div class="dim lv-zeile">testing and measuring are unavailable '
           'while live watching is locked on this machine — the note at the '
           'top of this page explains why.</div>' if gesperrt else
           f'<button class="gtb" onclick="liveTest(\'{nid}\',this)">Run '
           f'source test</button> '
           f'<button class="gtb" onclick="liveMessung(\'{nid}\',this)">'
           f'Measure load (15–30 s)</button> '
           '<span class="dim">the load measurement pauses the other watchers '
           'while it runs</span>')
        + f'<div class="dim lv-zeile" id="lv-job-{nid}"></div>'
        + '<div class="dim lv-zeile" id="lv-auftrag"></div></div>'
        + '<p>' + _save_knopf(gesperrt) + schalter
        + ' <span id="lv-status" style="color:var(--dim)"></span> '
        + f'&nbsp; <a href="/live">back to overview</a></p>'
        + '<script>window._livePage=true;</script>')
