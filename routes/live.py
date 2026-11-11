"""routes/live — der Reiter "Live" (Live-Phase 2, live_reiter_bauplan.md §2; seit LS2 eine Seite mit Plaetzen).

Reines Rendern (Muster kameras/benachrichtigungen: Daten als Parameter, kein
Dienst-Import). Der Handler sammelt Kameras (verifyd.frigate_cameras — KEINE
zweite Kamera-Aufzaehlung, Deckungs-Regel), Guards + Engine-Quittung
(core.livewache: guards_lesen/status_lesen) und den abgeleiteten Zustand je
Kamera (livewache.ui_zustand) und reicht sie herein. Farbe und Label je
Zustand kommen aus registry.LIVE_ZUSTAENDE — die EINE Quelle, aus der auch
/health speist (K3). K1 in beide Richtungen: gerendert wird ausschliesslich
der abgeleitete Zustand, nie der Store-Wunsch.

Seit Stufe LS2 (Bauplan analysen/bauplan_live_seite.md) gibt es keine Kachel-Uebersicht mehr: `seite` zeigt oben
die Platz-Leiste (so viele Plaetze wie die Obergrenze der Engine, mindestens bis zur hoechsten vergebenen Nummer)
und darunter den gewaehlten Platz, belegt mit den Einstellungen der Kamera (`detail`) oder frei zum Zuweisen. Die
Wahl des Platzes rechnen `plaetze_ordnen` und `platz_waehlen`, der Handler ruft sie nur auf.

Sprach-Stufe 0 (konzept_sprache.md v2): sichtbare Texte aus core/sprache.t()
— BYTE-TREU (Harnisch tools/harnisch_sprache.py). Grenzen dieser Stufe:
Abschnitts-Kommentar in core/texte/en.py; der CPU-Hinweis ist ein Schluessel
(live.hinweis_cpu, t() zur Render-Zeit — Modul-Konstanten froeren die
Sprachwahl auf den Import ein); die frueheren Schleifen-/Textvariablen `t`
sind umbenannt, damit sie t() nicht verschatten.
"""
import html
import time
import urllib.parse

from core import logbuch
from core.livewache import (BEWEG_FLAECHE_MAX, BEWEG_FLAECHE_MIN, BEWEG_SCHWELLE_MAX, BEWEG_SCHWELLE_MIN,
                            ENDE_OHNE_GESICHT_MAX, ENDE_OHNE_GESICHT_MIN, MQTT_EVENTS, RUHE_TAKT_MAX,
                            RUHE_TAKT_MIN, VIDEO_S_MAX, VIDEO_S_MIN, WIEDER_SCHARF_MAX, WIEDER_SCHARF_MIN,
                            guards_lesen, quelle_fp, quelle_maskiert)
from core.registry import LIVE_AKTIV, LIVE_ZUSTAENDE
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
    # .502 (User 04.09.): Reihenfolge = Verarbeitungskette. Erst der Auftritt,
    # dann die darin gefundenen Gesichter, daraus die Trigger, daraus die
    # Meldungen. Ein Stand ohne die Fund-Zahl liess offen, ob eine Kamera
    # nichts SIEHT oder nur nichts MELDET.
    teile = [t("live.zaehler.auftritte", n=live.get("auftritte", 0)),
             t("live.zaehler.funde", n=live.get("funde", 0)),
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


def _engine_klapp(stand, innen, rot=False):
    """Eingeklappter Block „Engine und Auslastung“ ganz unten auf der Seite (LS2 Punkt 1); die Kopfzeile nennt den
    Stand der Engine, rot, wenn sie nicht laeuft; stand ist ein Text aus t() und kommt wie frueher in der Karte
    unmaskiert herein (die Uebersetzungen tragen &nbsp;). -> HTML"""
    return (f'<details class="card lvs-abschnitt lvs-klapp" data-abschnitt="engine"><summary>'
            f'<b class="lvs-titel">{html.escape(t("live.abschnitt.engine"))}</b>'
            f'<span class="lvs-stand{" lvs-rot" if rot else ""}">{stand}</span></summary>'
            + innen + '</details>')


def _engine_karte(engine_info, gesperrt, container_last=None):
    """Engine-Lage + RAM-Ehrlichkeit (§2.3: Messwerte dieser Maschine, nie
    Literaturwerte — ungemessen heisst sichtbar 'not yet measured').
    Seit LS2 der eingeklappte Block unten (_engine_klapp) mit den Zeilen der frueheren Engine-Karte."""
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
        return _engine_klapp(t("live.engine.titel_aus"), aufsicht_zeile
                             + f'<div class="dim lv-zeile">{t("live.engine.satz_aus")}</div>', rot=True)
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
    return _engine_klapp(kopf, aufsicht_zeile
                         + "".join(f'<div class="dim lv-zeile">{html.escape(z)}</div>' for z in zeilen))


def _save_knopf(gesperrt):
    """Save-Knopf der Detailseite — auf gesperrten Builds GAR NICHT rendern
    (rc_p2_ui KANN 4: die Kachel sagt 'Bedienelemente aus', der Server weist
    /live_speichern seit dem Fix-Zyklus ab — ein sichtbarer Knopf, der nur
    einen Fehler erzeugt, widersprach beidem). Eigener Baustein, damit der
    Mutations-Selbsttest die Sperre fassen kann."""
    if gesperrt:
        return ""
    return ('<button class="gtb on" id="lv-speichern" onclick="liveSpeichern(this)">'
            + t("live.knopf_speichern") + '</button> ')


# Die Knoepfe der Einstellseite lesen den Kameranamen aus dem versteckten Feld lv-kamera, nie als Text im
# Klickaufruf: ein Apostroph im Namen braeche sonst den Aufruf und liesse fremdes JavaScript zu (Codex WS2, B1).
_KAMERA_JS = "document.getElementById('lv-kamera').value"


def _werkswerte():
    """Werkswerte eines Waechters ohne gespeicherte Werte, gelesen wie Engine und Seite sie lesen (eine Quelle).
    -> dict Feld -> Wert"""
    return guards_lesen({"live": {"guards": {"_": {"kanaele": []}}}}, logbuch.NULL)[1]["_"]


def _wert(g, werk, feld):
    """Gespeicherter Wert eines Felds, sonst der Werkswert. -> Wert"""
    w = g.get(feld)
    return werk.get(feld) if w is None else w


def _alter_text(tage):
    """Alter in Tagen als Text der Seite („heute“, „vor 1 Tag“, „vor N Tagen“); dieselbe gerundete ganze Zahl waehlt
    die Form und steht im Text. -> str"""
    if tage < 1:
        return t("live.alter.heute")
    return t_n("live.alter.tage", int(round(tage)))


def _zustand_text(z):
    """Zustand eines Waechters in der Sprache des Nutzers; die Schluessel stehen woertlich da, damit die
    Sprach-Deckung sie statisch findet. -> str (unbekannte Kennung: die Kennung selbst)"""
    texte = {"unconfigured": t("live.zustand.unconfigured"), "untested": t("live.zustand.untested"),
             "checking": t("live.zustand.checking"), "tested": t("live.zustand.tested"),
             "active": t("live.zustand.active"), "disturbed": t("live.zustand.disturbed"),
             "unsupported": t("live.zustand.unsupported")}
    return texte.get(z, z)


def _zeile(name, ctl, hinweis="", *, label=False, klasse="", attr=""):
    """Eine Zeile der Seite: links Beschriftung mit hoechstens einem gedaempften Satz, rechts das Bedienelement.
    -> HTML; label=True macht die ganze Zeile klickbar (Schalter, Radiofelder). Eine Liste als hinweis gibt einen
    Satz und darunter Punkte (Push-Pause, LS2)."""
    tag = "label" if label else "div"
    if isinstance(hinweis, list):
        hn = (f'<span class="lvs-hn">{hinweis[0]}</span>'
              + "".join(f'<span class="lvs-hn lvs-pkt">{h}</span>' for h in hinweis[1:]))
    else:
        hn = f'<span class="lvs-hn">{hinweis}</span>' if hinweis else ""
    return (f'<{tag} class="lvs-zeile{" " + klasse if klasse else ""}"{attr}>'
            f'<span class="lvs-lbl"><span class="lvs-name">{name}</span>{hn}</span>'
            f'<span class="lvs-ctl">{ctl}</span></{tag}>')


def _kipp(an, *, eid="", kanal=""):
    """Kippschalter als echtes Kontrollkaestchen (Aussehen aus .ek-kipp). -> HTML eines <input>"""
    ident = f' id="{eid}"' if eid else ""
    wert = f' class="ek-kipp lvs-kipp lv-kanal" value="{kanal}"' if kanal else ' class="ek-kipp lvs-kipp"'
    return f'<input type="checkbox"{wert}{ident}{" checked" if an else ""}>'


def _zahl(eid, wert, lo, hi, platzhalter=None, sekunden=True):
    """Zahlenfeld mit Spanne aus den Konstanten, auf Wunsch mit der Einheit Sekunden. -> HTML"""
    w = "" if wert is None else str(int(wert))
    ph = "" if platzhalter is None else f' placeholder="{html.escape(str(platzhalter), quote=True)}"'
    return (f'<input type="number" class="lvs-num" id="{eid}" min="{lo}" max="{hi}" step="1" '
            f'value="{html.escape(w, quote=True)}"{ph}>'
            + (f'<span class="lvs-einheit">{html.escape(t("live.einheit.s"))}</span>' if sekunden else ""))


def _kopf_test(g, gesperrt):
    """Quelltest-Zeile des Kopfs mit Alter, Marke bei einem gescheiterten Test und „erneut pruefen“. -> HTML"""
    test = g.get("test") or {}
    tage = _test_tage(test) if test.get("ok") else None
    if tage is None:
        txt, verweis = t("live.kopf.kein_test"), t("live.kopf.jetzt")
    else:
        txt, verweis = t("live.kopf.test", wann=_alter_text(tage)), t("live.kopf.erneut")
    klasse = "lv-hinweis" if tage is not None and tage >= _TEST_ALT_TAGE else "lvs-hn"
    marke = (f' <span class="lvs-marke">{html.escape(t("live.kopf.test_fehler"))}</span>'
             if (g.get("test_fehler") or {}).get("fehler") else "")
    knopf = ("" if gesperrt else
             f', <button type="button" class="lvs-link" onclick="liveTest({_KAMERA_JS},this)">'
             f'{html.escape(verweis)}</button>')
    zeile = f'<div class="{klasse}">{html.escape(txt)}{marke}{knopf}</div>'
    if gesperrt:
        zeile += f'<div class="lvs-hn">{html.escape(t("live.detail.gesperrt_hinweis"))}</div>'
    return zeile


def _kopf_bild(nid, g, z):
    """Vorschaubild des laufenden Waechters, sonst das Feld ohne Bild mit dem Stand des letzten Quelltests. -> HTML"""
    if z == "active":
        return (f'<img class="lv-vorschau" data-kamera="{nid}" alt="" src="/live_bild/{nid}?t=0" '
                f'onerror="this.style.display=\'none\'" onload="this.style.display=\'\'">')
    tb = g.get("test") or {}
    gemessen = (t("live.detail.kein_bild_test", aufloesung=tb.get("aufloesung", "?"), skala=tb.get("skala", "?"))
                if tb.get("ok") else t("live.detail.kein_bild_ohne_test"))
    return (f'<div class="lvs-kein-bild"><div>{html.escape(t("live.detail.kein_bild"))}</div>'
            f'<div>{html.escape(gemessen)}</div></div>')


def _kopf_wahl(name, platz, kamerawahl):
    """Kamerawahl und „Platz leeren“ im Kopf eines belegten Platzes (LS2 Punkt 7); die Auswahl zaehlt nicht als
    geaenderte Einstellung. -> HTML, leer ohne Platz"""
    if platz is None:
        return ""
    optionen = "".join(f'<option value="{html.escape(k, quote=True)}"{" selected" if k == name else ""}>'
                       f'{html.escape(k)}</option>' for k in (name, *kamerawahl))
    return (f'<div class="lvs-wahl">{html.escape(t("live.kopf.kamera"))} '
            f'<select id="lv-kamerawahl" class="lvs-auswahl" onchange="liveKameraWechsel(this)">{optionen}</select> '
            f'<button type="button" class="lvs-link" onclick="liveLeeren(this)">{html.escape(t("live.knopf_leeren"))}'
            f'</button><input type="hidden" id="lv-platz" value="{int(platz)}"></div>')


def _kopf(name, g, kd, gesperrt, platz=None, kamerawahl=()):
    """Kopf des belegten Platzes: Bild, Name mit Zustand und Bildrate, „nicht in Frigate“, Kamerawahl, Zaehler,
    Quelltest, rechts Speichern und Ein/Aus. -> HTML des Abschnitts kopf"""
    nid = html.escape(name, quote=True)
    z = kd["zustand"]
    farbe = (LIVE_ZUSTAENDE.get(z) or {}).get("farbe", "neutral")
    fps = (((kd.get("live") or {}).get("steckbrief") or {}).get("fps")
           or (kd.get("steckbrief") or {}).get("fps"))
    try:
        fps = f"{round(float(fps), 1):g}" if fps else ""
    except (TypeError, ValueError):
        fps = ""
    zustand = (t("live.kopf.zustand_fps", zustand=_zustand_text(z), fps=fps) if fps else _zustand_text(z))
    schalter = ""
    if not gesperrt:
        if z in ("tested", "untested"):
            schalter = (f'<button class="gtb" onclick="liveSchalter({_KAMERA_JS},true,this)">'
                        f'{t("live.knopf_enable")}</button>')
        elif g.get("enabled"):
            schalter = (f'<button class="gtb" onclick="liveSchalter({_KAMERA_JS},false,this)">'
                        f'{t("live.knopf_disable")}</button>')
    # LS2 Punkt 4: „nicht in Frigate“ steht im Kopf des Platzes (frueher als Marke auf der Kachel).
    fremd = ("" if kd.get("in_frigate", True) else
             f'<span class="lvs-zustand lvp-gelb" title="{html.escape(t("live.kachel.attr_fremd"), quote=True)}">'
             f'{html.escape(t("live.kachel.pill_fremd"))}</span>')
    detail_z = (f'<div class="lvs-hn">{html.escape(kd["detail"])}</div>' if kd.get("detail") else "")
    rechts = (f'<div class="lvs-rechts"><span id="lv-ungespeichert" class="lvs-ungespeichert" hidden>'
              f'{html.escape(t("live.ungespeichert"))}</span>{_save_knopf(gesperrt)}{schalter}'
              f'<span id="lv-status" class="lvs-hn"></span></div>')
    return (f'<section class="card lvs-abschnitt lvs-kopf" data-abschnitt="kopf">'
            f'<div class="lvs-bild">{_kopf_bild(nid, g, z)}</div>'
            f'<div class="lvs-mitte"><div class="lvs-kamera"><b>{html.escape(name)}</b>'
            f'<span class="lvs-zustand lvp-{farbe}">{html.escape(zustand)}</span>{fremd}</div>'
            + _kopf_wahl(name, platz, kamerawahl) + detail_z + _zaehler_zeile(kd.get("live")) + _kopf_test(g, gesperrt)
            + f'<div class="dim lv-zeile" id="lv-job-{nid}"></div></div>'
            + rechts + '</section>')


def _mqtt(g, topic):
    """Abschnitt Home Assistant (MQTT): Zweck, Schalter „An Home Assistant senden“ und das Topic mit dem Verweis auf
    die Meldungen (E1). -> HTML"""
    kanaele = g.get("kanaele") or []
    broker = (f'{html.escape(t("live.mqtt.broker"))} '
              f'<a href="/benachrichtigungen">{html.escape(t("nav.benachrichtigungen"))}</a>')
    top = f'<code class="lvs-mono">{html.escape(topic)}</code>' if topic else ""
    meldungen = f'<a href="/readme#rm-mqtt">{html.escape(t("live.mqtt.meldungen", n=len(MQTT_EVENTS)))}</a>'
    return (f'<section class="card lvs-abschnitt" data-abschnitt="mqtt">'
            f'<h3>{html.escape(t("live.abschnitt.mqtt"))}</h3>'
            f'<p class="lvs-zweck">{html.escape(t("live.mqtt.zweck"))}</p>'
            + _zeile(html.escape(t("live.mqtt.nutzen")), _kipp("mqtt" in kanaele, kanal="mqtt"), broker, label=True)
            + _zeile(html.escape(t("live.mqtt.topic")), meldungen, top)
            + '</section>')


def _push_tabelle(g, werk):
    """Tabelle der Push-Nachrichten (LS2 Punkt 3): Zeilen Erkannte Person, Unbekannte Person, Bild und Video, Spalten
    Pushover und Telegram mit ihrem Schalter; dieselben Felder wie vorher (WV1). -> HTML"""
    kanaele = g.get("kanaele") or []

    def kipp(feld, eid):
        return _kipp(bool(_wert(g, werk, feld)), eid=eid)

    def zeile(name, hinweis, pushover, telegram):
        return (f'<tr><td><span class="lvs-name">{html.escape(name)}</span>'
                f'<span class="lvs-hn">{html.escape(hinweis)}</span></td>'
                f'<td class="lvs-spalte lvs-p">{pushover}</td><td class="lvs-spalte lvs-t">{telegram}</td></tr>')

    # Die Kanalnamen Pushover und Telegram sind Eigennamen und bleiben woertlich.
    kopf = ('<thead><tr><th></th>'
            + "".join(f'<th><label class="lvs-kanalkopf">{n}{_kipp(k in kanaele, kanal=k)}</label></th>'
                      for n, k in (("Pushover", "pushover"), ("Telegram", "telegram")))
            + '</tr></thead>')
    laenge = (f'<span class="lvs-dauer" title="{html.escape(t("live.push.videolaenge"), quote=True)}">'
              + _zahl("lv-video-s", _wert(g, werk, "video_s"), VIDEO_S_MIN, VIDEO_S_MAX) + '</span>')
    # Schluessel woertlich an der Aufrufstelle, damit die Sprach-Deckung sie statisch findet.
    return ('<table class="lvs-tabelle">' + kopf + '<tbody>'
            + zeile(t("live.push.bekannte"), t("live.push.bekannte_hinweis"),
                    kipp("pushover_known", "lv-pushover-known"), kipp("telegram_known", "lv-telegram-known"))
            + zeile(t("live.push.unbekannte"), t("live.push.unbekannte_hinweis"),
                    kipp("pushover_unknown", "lv-pushover-unknown"), kipp("telegram_unknown", "lv-telegram-unknown"))
            + zeile(t("live.push.bild"), t("live.push.bild_hinweis"),
                    kipp("pushover_image", "lv-pushover-image"), kipp("telegram_image", "lv-telegram-image"))
            + zeile(t("live.push.video"), t("live.push.video_hinweis"),
                    f'<span class="lvs-nur">{html.escape(t("live.push.nur_telegram"))}</span>',
                    f'<span class="lvs-video">{kipp("telegram_video", "lv-telegram-video")}{laenge}</span>')
            + '</tbody></table>')


def _push(g, werk):
    """Abschnitt Push-Nachrichten: Tabelle, „Unbekannte auch neben Erkannten melden“ und die Push-Pause mit ihren drei
    Punkten (WV1, WV3). -> HTML"""
    neben = _zeile(html.escape(t("live.push.neben")),
                   _kipp(bool(_wert(g, werk, "unknown_with_known")), eid="lv-unknown-with-known"),
                   html.escape(t("live.push.neben_hinweis")), label=True)
    pause = _zeile(html.escape(t("live.detail.scharf_label")),
                   _zahl("lv-scharf", _wert(g, werk, "wieder_scharf_s"), WIEDER_SCHARF_MIN, WIEDER_SCHARF_MAX),
                   [html.escape(t("live.pause.kopf")), html.escape(t("live.pause.besuche")),
                    html.escape(t("live.pause.name")), html.escape(t("live.detail.scharf_hinweis"))])
    return (f'<section class="card lvs-abschnitt" data-abschnitt="push">'
            f'<h3>{html.escape(t("live.abschnitt.push"))}</h3>'
            f'<p class="lvs-zweck">{html.escape(t("live.push.zweck"))} '
            f'<a href="/benachrichtigungen">{html.escape(t("live.push.zugang"))}</a></p>'
            + _push_tabelle(g, werk) + neben + pause + '</section>')


def _besuch(g, werk, global_werte):
    """Abschnitt Besuch: Zweck, „Besuch endet nach“ und die zwei globalen Werte als ein Satz mit Verweis (E2).
    -> HTML"""
    zeilen = _zeile(html.escape(t("live.detail.ende_label")),
                    _zahl("lv-ende", _wert(g, werk, "ende_ohne_gesicht_s"), ENDE_OHNE_GESICHT_MIN,
                          ENDE_OHNE_GESICHT_MAX),
                    html.escape(t("live.detail.ende_hinweis")))
    if global_werte is not None:
        fps, stimmen = ("–" if w is None else str(w) for w in global_werte)
        zeilen += _zeile("", f'<a href="/konfiguration">{html.escape(t("nav.bereich.configuration"))}</a>',
                         html.escape(t("live.besuch.global", fps=fps, stimmen=stimmen)),
                         attr=' data-global="fps_sample stapel_stimmen"')
    return (f'<section class="card lvs-abschnitt" data-abschnitt="besuch">'
            f'<h3>{html.escape(t("live.abschnitt.besuch"))}</h3>'
            f'<p class="lvs-zweck">{html.escape(t("live.besuch.zweck"))}</p>' + zeilen + '</section>')


def _frigate(g, werk):
    """Abschnitt Frigate, optional: eigenes Ereignis je erkanntem Namen und Abstand je Person. -> HTML"""
    return (f'<section class="card lvs-abschnitt" data-abschnitt="frigate">'
            f'<h3>{html.escape(t("live.abschnitt.frigate"))}</h3>'
            + _zeile(html.escape(t("live.frigate.schalter")),
                     _kipp(bool(_wert(g, werk, "frigate_events")), eid="lv-frigate"),
                     html.escape(t("live.frigate.erklaerung")), label=True)
            + _zeile(html.escape(t("live.frigate.abstand_label")),
                     _zahl("lv-frigate-abstand", g.get("frigate_abstand_s"), WIEDER_SCHARF_MIN, WIEDER_SCHARF_MAX,
                           _wert(g, werk, "wieder_scharf_s")),
                     html.escape(t("live.frigate.abstand_hinweis")))
            + '</section>')


def _gruppe(titel):
    """Zwischenueberschrift mit Linie innerhalb eines eingeklappten Abschnitts. -> HTML"""
    return f'<div class="lvs-gruppe">{html.escape(t(titel))}</div>'


def _erweitert(g, werk, beweg_vorgabe):
    """Abschnitt Erweitert (eingeklappt): Verbindung, Sparbetrieb, Zusatzanalyse; die Kopfzeile zeigt den Stand (WV5).
    -> HTML"""
    quelle = g.get("quelle") or "proxy"
    spar, ersetzt = bool(_wert(g, werk, "bewegung_gate")), bool(_wert(g, werk, "worker_aus"))
    an_aus = {True: t("live.wert.an"), False: t("live.wert.aus")}
    stand = t("live.erweitert.kopf", quelle=quelle, spar=an_aus[spar], ersetzt=an_aus[ersetzt])
    # Die Quell-Kennungen proxy/direct/url sind Anzeige und Wert zugleich und bleiben woertlich.
    radios = "".join(
        _zeile(q, f'<input type="radio" name="lv-quelle" value="{q}"{" checked" if quelle == q else ""}>',
               html.escape(beschr), label=True)
        for q, beschr in (("proxy", t("live.quelle.proxy")), ("direct", t("live.quelle.direct")),
                          ("url", t("live.quelle.url"))))
    # Das Feld traegt die MASKIERTE URL; bleibt sie unveraendert, behaelt der Server die gespeicherte (live_speichern).
    url = (f'<input id="lv-url" class="lvs-url" value="{html.escape(quelle_maskiert(str(g.get("url") or "")), quote=True)}"'
           f' placeholder="rtsp://..." autocomplete="off">')
    schwelle_vor, flaeche_vor = beweg_vorgabe
    return (f'<details class="card lvs-abschnitt lvs-klapp" data-abschnitt="erweitert"><summary>'
            f'<b class="lvs-titel">{html.escape(t("live.abschnitt.erweitert"))}</b>'
            f'<span class="lvs-stand">{html.escape(stand)}</span></summary>'
            + '<div class="lvs-spalten lvs-drei"><div>'
            + _gruppe("live.abschnitt.quelle") + radios
            + _zeile(html.escape(t("live.detail.url_label")), url, html.escape(t("live.detail.url_hinweis")))
            + f'<p class="lvs-notiz">{html.escape(t("live.detail.quelle_hinweis"))}</p></div><div>'
            + _gruppe("live.abschnitt.abtastung")
            + _zeile(html.escape(t("live.abtastung.schalter")), _kipp(spar, eid="lv-bewegung"),
                     html.escape(t("live.abtastung.erklaerung")), label=True)
            + _zeile(html.escape(t("live.abtastung.ruhe_label")),
                     _zahl("lv-ruhe-takt", g.get("ruhe_takt_s"), RUHE_TAKT_MIN, RUHE_TAKT_MAX,
                           _wert(g, werk, "ende_ohne_gesicht_s")),
                     html.escape(t("live.abtastung.ruhe_hinweis")))
            + _zeile(html.escape(t("live.abtastung.schwelle_label")),
                     _zahl("lv-bewegung-schwelle", g.get("bewegung_schwelle"), BEWEG_SCHWELLE_MIN,
                           BEWEG_SCHWELLE_MAX, schwelle_vor, sekunden=False),
                     html.escape(t("live.abtastung.eich_hinweis")))
            + _zeile(html.escape(t("live.abtastung.flaeche_label")),
                     _zahl("lv-bewegung-flaeche", g.get("bewegung_flaeche"), BEWEG_FLAECHE_MIN,
                           BEWEG_FLAECHE_MAX, flaeche_vor, sekunden=False))
            + '</div><div>' + _gruppe("live.abschnitt.zusatz")
            + _zeile(html.escape(t("live.workeraus.schalter")), _kipp(ersetzt, eid="lv-worker-aus"),
                     html.escape(t("live.workeraus.erklaerung")), label=True)
            + _zeile(html.escape(t("live.eigenepruefen.schalter")),
                     _kipp(bool(_wert(g, werk, "eigene_pruefen")), eid="lv-eigene-pruefen"),
                     html.escape(t("live.eigenepruefen.erklaerung")), label=True)
            + '</div></div></details>')


def _diagnose_stand(g, vorrat, deckel):
    """Kopfzeile der Diagnose: Lastmessung und Bildvorrat (WV5). -> str"""
    m = g.get("messung") or {}
    if m.get("ok"):
        tage = _test_tage(m)
        messung = (t("live.diagnose.messung_entwertet") if _fp_veraltet(m, g)
                   else _alter_text(tage) if tage is not None else t("live.diagnose.messung_fehlt"))
    elif m.get("fehler"):
        messung = t("live.diagnose.messung_fehler")
    else:
        messung = t("live.diagnose.messung_fehlt")
    bestand = t("live.diagnose.vorrat", n=vorrat, deckel=deckel) if deckel else t("live.wert.aus")
    return t("live.diagnose.kopf", messung=messung, vorrat=bestand)


def _diagnose(nid, g, gesperrt, vorrat, deckel, det_default):
    """Abschnitt Diagnose (eingeklappt): Quelltest, Lastmessung, Kalibrierwerte, Bildvorrat. -> HTML"""
    det_wert = g.get("det_min")
    det_txt = f"{float(det_wert if det_wert is not None else det_default):.2f}"
    det_marke = "" if det_wert is not None else t("live.erkennung.det_vorgabe")

    def _latte(wert):
        return f"{float(wert):.3f}" if wert is not None else t("live.erkennung.latte_aus")

    # Schluessel woertlich an der Aufrufstelle, damit die Sprach-Deckung sie statisch findet.
    guete = (t("live.erkennung.latte_e", wert=_latte(g.get("guete_e_min"))) + " · "
             + t("live.erkennung.latte_t", wert=_latte(g.get("guete_t_min"))))
    test = (_test_zeile(g.get("test"), g, auffordern=True) + _test_fehler_zeile(g.get("test_fehler"))
            + ("" if gesperrt else f'<div class="lv-knoepfe"><button class="gtb" '
               f'onclick="liveTest({_KAMERA_JS},this)">{t("live.knopf_test")}</button></div>'))
    last = ("" if gesperrt else
            _messung_zeile(g.get("messung"), g)
            + f'<div class="lv-knoepfe"><button class="gtb" onclick="liveMessung({_KAMERA_JS},this)">'
              f'{t("live.knopf_messung_lang")}</button> '
              f'<span class="dim lv-zeile">{html.escape(t("live.detail.messung_hinweis"))}</span></div>')
    kalib = (f'<div class="dim lv-zeile">{html.escape(t("live.erkennung.det_zeile", wert=det_txt, marke=det_marke))}</div>'
             f'<div class="dim lv-zeile">{html.escape(guete)}</div>'
             f'<div class="dim lv-zeile">{html.escape(t("live.erkennung.latte_hinweis"))}</div>'
             f'<div class="lv-knoepfe"><a class="gtb" href="/kalibrierung/{nid}">{t("live.knopf_kalibrieren")}</a></div>')
    bestand = (t("live.erkennung.vorrat_zeile", n=vorrat, deckel=deckel) if deckel
               else t("live.erkennung.vorrat_aus"))
    leeren = ("" if gesperrt or not vorrat else
              f'<div class="lv-knoepfe"><button class="gtb" onclick="liveVorratLeeren({_KAMERA_JS},this)">'
              f'{t("live.knopf_vorrat_leeren")}</button></div>')
    return (f'<details class="card lvs-abschnitt lvs-klapp" data-abschnitt="diagnose"><summary>'
            f'<b class="lvs-titel">{html.escape(t("live.abschnitt.diagnose"))}</b>'
            f'<span class="lvs-stand">{html.escape(_diagnose_stand(g, vorrat, deckel))}</span></summary>'
            + '<div class="lvs-spalten lvs-vier"><div>' + _gruppe("live.abschnitt.test") + test
            + '</div><div>' + _gruppe("live.abschnitt.last") + last
            + '</div><div>' + _gruppe("live.abschnitt.guete") + kalib
            + '</div><div>' + _gruppe("live.abschnitt.vorrat") + f'<div class="dim lv-zeile">{html.escape(bestand)}</div>'
            + leeren + '</div></div></details>')


def detail(name, guard, kd, gesperrt, vorrat=0, deckel=0, *,
           det_default, beweg_vorgabe=(30, 10), mqtt_topic="", global_werte=None, platz=None, kamerawahl=()):
    """-> HTML der Einstellungen eines belegten Platzes der Live-Seite (Bauplan analysen/bauplan_live_seite.md, Stufe
    LS2; vorher die Einstellseite /live/<kamera> aus WS2).

    Nach der Vorlage vom 10.11.2026: Kopf, darunter zwei Spalten (links Push-Nachrichten, rechts Home Assistant,
    Besuch und Frigate), dann eingeklappt Erweitert und Diagnose mit dem Stand der wichtigsten Werte in der
    Kopfzeile. Jedes Feld der frueheren Seite ist noch da, mit seiner ID; gespeichert wird ueber denselben Weg
    (webui/app.js _liveFelder liest die IDs, WV3).

    vorrat/deckel = Stand des Kalibrier-Vorrats dieser Kamera, beweg_vorgabe = (schwelle, flaeche) der
    Bewegungs-Abtastung als Platzhalter, mqtt_topic = das echte Topic des Waechters, global_werte =
    (fps_sample, stapel_stimmen) aus der Config — alles vom Handler aus der einen Quelle, damit die Seite
    keine zweite Zahl traegt. platz = Nummer des Platzes (dann zeigt der Kopf Kamerawahl und „Platz leeren“),
    kamerawahl = die Kameras ohne Platz fuer die Auswahl im Kopf."""
    nid = html.escape(name, quote=True)
    g = guard or {}
    werk = _werkswerte()
    return (f'<div class="lvs-einstellungen"><input type="hidden" id="lv-kamera" value="{nid}">'
            + _kopf(name, g, kd, gesperrt, platz, kamerawahl)
            + '<div class="lvs-spalten lvs-zwei"><div>' + _push(g, werk) + '</div><div>'
            + _mqtt(g, mqtt_topic) + _besuch(g, werk, global_werte) + _frigate(g, werk) + '</div></div>'
            + _erweitert(g, werk, beweg_vorgabe)
            + _diagnose(nid, g, gesperrt, vorrat, deckel, det_default)
            + '</div>')


def plaetze_ordnen(kacheln, obergrenze):
    """Ordnet die Kameras den Plaetzen der Live-Seite zu, ueber das Feld platz des Waechters (Stufe LS1).
    -> (belegung {nr: Kachel-Daten}, Zahl der Plaetze, Namen der Kameras ohne Platz)

    Gezeigt werden so viele Plaetze wie die Obergrenze der Engine, mindestens aber bis zur hoechsten vergebenen
    Nummer (LS2 Punkt 2; eine Nummer ueber der Obergrenze aus der Uebernahme laesst sich so leeren)."""
    belegung, freie = {}, []
    for kd in kacheln:
        nr = (kd.get("guard") or {}).get("platz")
        if nr is None:
            freie.append(kd["name"])
        elif nr not in belegung:
            belegung[nr] = kd
    return belegung, max([int(obergrenze), *belegung]), freie


def platz_waehlen(belegung, anzahl, wunsch=None, kamera=None):
    """Waehlt den gezeigten Platz (LS2 Punkt 2): fuer /live die Nummer aus ?platz=, sonst den ersten belegten, sonst
    Platz 1; fuer /live/<kamera> den Platz dieser Kamera, sonst den ersten freien mit ihr vorgewaehlt.
    -> (nr, vorgewaehlte Kamera oder "", Kamera, fuer die kein Platz frei ist, oder "")"""
    standard = min(belegung) if belegung else 1
    if kamera is None:
        gueltig = isinstance(wunsch, int) and 1 <= wunsch <= anzahl
        return (wunsch if gueltig else standard), "", ""
    eigen = next((nr for nr, kd in belegung.items() if kd["name"] == kamera), None)
    if eigen is not None:
        return eigen, "", ""
    frei = next((nr for nr in range(1, anzahl + 1) if nr not in belegung), None)
    if frei is None:
        return standard, "", kamera
    return frei, kamera, ""


def _platz_farbe(kd):
    """Farbwort des Platz-Knopfs aus registry.LIVE_ZUSTAENDE; eine Kamera, die nicht in Frigate ist, wird gelb,
    ausser sie ist gestoert (rot bleibt rot, LS2 Punkt 4). -> str"""
    farbe = (LIVE_ZUSTAENDE.get(kd["zustand"]) or {}).get("farbe", "neutral")
    return "gelb" if farbe != "rot" and not kd.get("in_frigate", True) else farbe


def _platz_leiste(belegung, anzahl, nr):
    """Die Platz-Leiste: je Platz ein Knopf mit Nummer, Kamera und Zustand, frei als „Live N“. Der Wechsel ist ein
    Seitenaufruf; webui/app.js livePlatzWechsel haelt ihn bei geaenderten Feldern an (LS2 Punkt 7). -> HTML"""
    knoepfe = []
    for n in range(1, anzahl + 1):
        kd = belegung.get(n)
        if kd is None:
            klasse, name, unten, titel = " lvs-frei", t("live.platz.name", n=n), html.escape(t("live.platz.frei")), ""
        else:
            farbe = _platz_farbe(kd)
            klasse, name = f" lvs-f-{farbe}", kd["name"]
            unten = f'<i class="lvs-punkt lvs-f-{farbe}"></i>{html.escape(_zustand_text(kd["zustand"]))}'
            titel = ("" if kd.get("in_frigate", True) else
                     f' title="{html.escape(t("live.kachel.attr_fremd"), quote=True)}"')
        aktuell = ' aria-current="page"' if n == nr else ""
        knoepfe.append(f'<a class="lvs-platz{klasse}{" lvs-gewaehlt" if n == nr else ""}" href="/live?platz={n}"'
                       f'{aktuell}{titel} onclick="return livePlatzWechsel(this)"><span class="lvs-nr">{n}</span>'
                       f'<span class="lvs-tx"><b>{html.escape(name)}</b><small>{unten}</small></span></a>')
    return '<div class="lvs-plaetze">' + "".join(knoepfe) + '</div>'


def _frei(nr, freie, vorwahl, ohne_kameras):
    """Ein freier Platz: Titel, Satz und die Auswahl der Kameras ohne Platz mit „Kamera zuweisen“. -> HTML"""
    if freie:
        optionen = "".join(f'<option value="{html.escape(k, quote=True)}"{" selected" if k == vorwahl else ""}>'
                           f'{html.escape(k)}</option>' for k in freie)
        wahl = (f'<div class="lvs-wahl"><select id="lv-neu" class="lvs-auswahl">{optionen}</select> '
                f'<button type="button" class="gtb on" onclick="liveZuweisen({int(nr)},this)">'
                f'{html.escape(t("live.knopf_zuweisen"))}</button></div>')
    elif ohne_kameras:
        wahl = (f'<p class="lvs-zweck"><b>{html.escape(t("live.leer.titel"))}</b> '
                f'{html.escape(t("live.leer.hinweis"))}</p>')
    else:
        wahl = f'<p class="lvs-zweck">{html.escape(t("live.frei.keine"))}</p>'
    return (f'<section class="card lvs-abschnitt lvs-leer" data-abschnitt="frei">'
            f'<h3>{html.escape(t("live.frei.titel", n=nr))}</h3>'
            f'<p class="lvs-zweck">{html.escape(t("live.frei.satz"))}</p>{wahl}'
            f'<div id="lv-frei-status" class="lvs-hn"></div></section>')


def _marke(engine_info, gesperrt, kacheln):
    """Marke der Titelzeile: Engine laeuft (gruen, mit der Zahl der aktiven Waechter), Engine aus (rot, ED008) oder
    auf diesem Build nicht verfuegbar (grau). Die Titel kommen wie frueher unmaskiert aus t() (&nbsp; im
    Franzoesischen). -> HTML"""
    if gesperrt:
        farbe, text = "neutral", t("live.sperre.titel")
    elif not engine_info.get("frisch"):
        farbe, text = "rot", t("live.engine.titel_aus")
    else:
        aktiv = sum(1 for kd in kacheln if kd.get("zustand") == LIVE_AKTIV)
        kopf = (t("live.engine.titel_standalone") if (engine_info.get("aufsicht") or {}).get("standalone")
                else t("live.engine.titel_an"))
        farbe, text = "gruen", kopf + " · " + html.escape(t("live.marke.aktiv", n=aktiv))
    return f'<span class="lvs-marke-engine"><i class="lvs-punkt lvs-f-{farbe}"></i>{text}</span>'


def _sperr_karte(engine_info, gesperrt, cpu_begrenzt):
    """Karte ueber der Platz-Leiste: „nicht verfuegbar“ auf dem CPU-Image oder der CPU-Hinweis (LS2 Punkt 4, Texte
    unveraendert aus der frueheren Uebersicht). -> HTML, leer ohne Anlass"""
    if gesperrt:
        sperr_grund = (engine_info or {}).get("sperr_grund") or ""
        return (f'<div class="card"><b>{t("live.sperre.titel")}</b>'
                f'<div class="dim">{t("live.sperre.satz")}'
                + (f' {html.escape(sperr_grund)}.' if sperr_grund else ' ' + t("live.sperre.cpu_only"))
                + '</div></div>')
    if cpu_begrenzt:
        # Stufe-0-Grenze: der Satzrest mit <b>Measure load</b> bleibt literal.
        return (f'<div class="card"><b>{t("live.sperre.cpu_titel")}</b>'
                f'<div class="dim">{html.escape(t("live.hinweis_cpu"))} '
                'Use <b>Measure load</b> per camera and the load '
                'line above before enabling more.</div></div>')
    return ""


def _warnleiste(nr):
    """Warnleiste fuer den Platzwechsel mit ungespeicherten Feldern (LS2 Punkt 7, Entscheid 09:09:41): Speichern und
    wechseln, Verwerfen, Hier bleiben; webui/app.js blendet sie ein. -> HTML"""
    knoepfe = "".join(f'<button type="button" class="gtb" data-wahl="{w}" onclick="liveWarnAntwort(\'{w}\')">'
                      f'{html.escape(text)}</button>'
                      for w, text in (("speichern", t("live.warnung.speichern")),
                                      ("verwerfen", t("live.warnung.verwerfen")),
                                      ("bleiben", t("live.warnung.bleiben"))))
    return (f'<div class="lvs-warnung" id="lv-warnung" hidden><span>{html.escape(t("live.warnung.satz", n=nr))}'
            f'</span>{knoepfe}</div>')


def seite(kacheln, engine_info, gesperrt, belegung, anzahl, nr, *, einstellungen=None, vorwahl="", voll="",
          freie=(), frigate_fehler=None, cpu_begrenzt=False, container_last=None):
    """Seiten-INHALT von /live und /live/<kamera> (Bauplan analysen/bauplan_live_seite.md, Stufe LS2).
    -> HTML: Titelzeile mit Engine-Marke, Satz mit Link, Hinweise, Platz-Leiste und darunter der gewaehlte Platz,
    ganz unten eingeklappt „Engine und Auslastung“.

    belegung/anzahl/nr aus plaetze_ordnen und platz_waehlen; einstellungen = HTML von detail() fuer einen belegten
    Platz, sonst None (freier Platz mit vorwahl vorgewaehlt); voll = Kamera aus /live/<kamera>, fuer die kein
    Platz frei ist; freie = Kameras ohne Platz."""
    banner = ('<div class="banner">' + t("live.banner.kameraliste", fehler=html.escape(str(frigate_fehler)))
              + '</div>' if frigate_fehler else "")
    kein_platz = (f'<div class="lv-hinweis lvs-satz">{html.escape(t("live.kein_platz", kamera=voll))}</div>'
                  if voll else "")
    platz = einstellungen if einstellungen is not None else _frei(nr, freie, vorwahl, not kacheln)
    return (banner
            + f'<div class="lvs-titelzeile"><h2>{t("live.titel")}</h2>'
            + _marke(engine_info, gesperrt, kacheln) + '</div>'
            + f'<p class="lvs-intro">{html.escape(t("live.intro"))} <a href="{DOKU_URL}" target="_blank" '
              f'rel="noopener">{html.escape(t("live.intro_link"))}</a></p>'
            + _sperr_karte(engine_info, gesperrt, cpu_begrenzt) + kein_platz
            + _platz_leiste(belegung, anzahl, nr)
            + (_warnleiste(nr) if einstellungen is not None else "")
            + '<div class="dim lv-zeile" id="lv-auftrag"></div>'
            + platz
            + _engine_karte(engine_info, gesperrt, container_last)
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
            # PW5 (E18, Punkt 3): "nicht gesendet" nur, wenn die Karte keinen anderen Kanal hat.
            f' · {html.escape("+".join(t("livealerts.kanal_keiner") if _kn == "none" else _kn for _kn in [_k for _k in a["kanaele"] if _k != "none"] or a["kanaele"]))}</span></div>'
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
