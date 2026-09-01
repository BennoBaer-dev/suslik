"""routes/systemstat — die Seite „System stats" (Bauplan
analysen/bauplan_systemstatistik.md §3.3).

Drei Bloecke: Hardware (CPU, RAM, Platte, GPU, NPU), Erkennung (Worker-Zustand,
Durchsatz, Rueckstau) und Live. Der zweite Block ist der Grund, warum diese
Seite mehr ist als eine Frigate-Kopie: die ernsten Feldfaelle dieses Jahres
waren Erkennungs-Stillstaende, bei denen CPU und GPU voellig unauffaellig
aussahen (ein Tester-System verlor den Analyse-Worker 114-mal an einem Tag).

Injektion pur (Muster routes/kameras.py): alles kommt als Parameter, dieses
Modul importiert verifyd nie und misst selbst nichts. Gerendert wird aus dem
RINGPUFFER — kein Live-Sammeln beim Seitenaufruf.

EHRLICHKEITS-REGEL (Bauplan §2, gilt hier fuer jede Kachel): ein Wert None ist
keine Null. Die Kachel bleibt stehen, zeigt „not available" und den Grund als
Satz. Eine fehlende Messung darf nie wie ein gemessener Ruhewert aussehen —
genau daran haette man auf dieser Anlage die gesperrte Intel-GPU-Auslastung
fuer einen schlafenden Beschleuniger halten koennen.

Keine Schwellen und keine Farbalarme (Bauplan §4): fuer Platte und Speicher
gibt es die bestehenden Wachen, und zwei Stellen mit eigenen Schwellen driften
auseinander. Die Balken tragen deshalb EINE Farbe.

Sprache: sichtbare Texte aus core/sprache.t(). Die Datumsformate (%H:%M)
bleiben in der Route (B19); „CPU", „RAM", „GPU", „NPU" sind Abkuerzungen und
bleiben literal (§8.6)."""
import datetime
import html

import webui

from core.sprache import t

# Balkenreihe: feste Zeichenflaeche, damit alle Kacheln dieselbe Zeitachse
# haben. 60 Werte = eine Stunde im 60-s-Takt; ein kuerzerer Puffer fuellt von
# rechts auf, damit „jetzt" immer am selben Rand steht.
_PLAETZE = 60
_BREITE = 4          # Balken 3 + Luecke 1
_HOEHE = 34

# Der EINE Kachel-Zustand, der „laeuft gerade" bedeutet. Bewusst als benannte
# Konstante mit Deckungs-Vertrag statt als Literal mitten im Zaehlausdruck: das
# Gate prueft, dass der Wert in registry.LIVE_ZUSTAENDE vorkommt — benennt die
# Registry ihre Zustaende um, faellt das hier auf, statt still 0 zu zaehlen.
LIVE_AKTIV = "active"


def _zahl(w, einheit="", stellen=0):
    if w is None:
        return "—"
    return f"{w:.{stellen}f}{einheit}"


def _balken(werte, max_wert=100.0):
    """Verlauf als Inline-SVG (kein Framework, keine CDNs — Projektregel).

    Ein Wert None erzeugt eine LUECKE, keinen Nullbalken: der Puffer haelt auch
    Zeilen, in denen genau diese Quelle nicht messbar war (erste Runde nach dem
    Start, kurzzeitig unlesbares sysfs), und die duerfen nicht wie Leerlauf
    aussehen. Werte oberhalb der Skala werden fuer die ZEICHNUNG gedeckelt, der
    Zahlenwert daneben bleibt ungedeckelt."""
    werte = list(werte)[-_PLAETZE:]
    if not any(w is not None for w in werte):
        return f'<div class="sst-kein">{html.escape(t("systemstat.verlauf.leer"))}</div>'
    vorlauf = _PLAETZE - len(werte)
    stuecke = []
    for i, w in enumerate(werte):
        if w is None:
            continue
        h = max(1.0, min(float(w), max_wert) / max_wert * (_HOEHE - 2))
        x = (vorlauf + i) * _BREITE
        stuecke.append(f'<rect x="{x}" y="{_HOEHE - h:.1f}" width="3" '
                       f'height="{h:.1f}" rx="1"/>')
    return (f'<svg class="sst-bal" viewBox="0 0 {_PLAETZE * _BREITE} {_HOEHE}" '
            f'preserveAspectRatio="none" role="img" aria-label="'
            f'{html.escape(t("systemstat.verlauf.aria"))}">'
            + "".join(stuecke) + "</svg>")


def _grund_satz(code):
    """Grund-Code -> Satz.

    BEWUSST acht literale Schluessel statt eines zur Laufzeit aus Praefix und
    Code zusammengesetzten: die Sprach-Deckung des Gates liest die
    Schluessel STATISCH aus dem Quelltext. Ein zusammengesetzter Schluessel
    ist fuer sie unbekannt, und alle acht Saetze gaelten zugleich als tot —
    ein Tippfehler in einem davon fiele dann nirgends auf. Dass die Liste
    vollstaendig ist, sichert der Deckungs-Vertrag im Gate
    (systemstat.GRUENDE <-> die Schluessel hier), nicht die Bauform.
    Das dict entsteht IM Aufruf: t() darf nie auf Modulebene laufen (§8.12,
    sonst friert die Sprachwahl auf den Import ein)."""
    return {
        "erster_lauf": t("systemstat.grund.erster_lauf"),
        "kein_geraet": t("systemstat.grund.kein_geraet"),
        "kein_zaehler": t("systemstat.grund.kein_zaehler"),
        "gesperrt": t("systemstat.grund.gesperrt"),
        "werkzeug_fehlt": t("systemstat.grund.werkzeug_fehlt"),
        "nicht_lesbar": t("systemstat.grund.nicht_lesbar"),
        "kein_limit": t("systemstat.grund.kein_limit"),
        "kein_dienst": t("systemstat.grund.kein_dienst"),
    }.get(code, code)


def _grund(block, marke=None):
    """Grund-Code -> Satz. Der Vertrag (jeder Code in systemstat.GRUENDE hat
    einen Schluessel) wird im Gate geprueft; hier bleibt nur die Anzeige.

    marke: was genau fehlt. Vorgabe ist „not available" (die ganze Kachel hat
    keinen Wert). Kacheln, die trotzdem Zahlen zeigen und denen nur der
    Prozentsatz fehlt, uebergeben die kleinere Marke — sonst behauptet die
    Zeile einen Ausfall ueber Werten, die daneben stehen."""
    g = (block or {}).get("grund")
    if not g:
        return ""
    return (f'<div class="sst-fehlt">'
            f'{html.escape(marke or t("systemstat.nicht_verfuegbar"))}'
            f' <span class="dim">{html.escape(_grund_satz(g))}</span></div>')


def _kachel(titel, block, wert_html, verlauf, zeilen=(), marke=None):
    unten = "".join(f'<div class="sst-zl"><span>{html.escape(k)}</span>'
                    f'<b>{html.escape(v)}</b></div>' for k, v in zeilen if v)
    return (f'<div class="card sst-kachel"><div class="sst-kopf">'
            f'{html.escape(titel)}</div>'
            f'<div class="sst-wert">{wert_html}</div>'
            f'{_grund(block, marke)}{verlauf}{unten}</div>')


def _prozent_kachel(titel, block, reihe, zeilen=()):
    p = (block or {}).get("prozent")
    wert = (f'<span class="sst-gross">{_zahl(p)}</span>'
            f'<span class="sst-einheit">%</span>' if p is not None
            else '<span class="sst-gross dim">—</span>')
    return _kachel(titel, block, wert, _balken(reihe), zeilen)


def render(verlauf, jetzt, takt_s, aufbewahrung_h):
    """-> Seiten-INHALT /systemstat.

    verlauf: Liste der Momentaufnahmen der letzten Stunde (aelteste zuerst).
    jetzt:   die zuletzt geschriebene Momentaufnahme (dieselbe, die /health
             ausgibt) oder None, solange der Sammler noch keine hat.
    """
    kopf = (f'<h2>{html.escape(t("systemstat.titel"))}</h2>'
            f'<p class="sub">{html.escape(t("systemstat.sub", takt=takt_s, stunden=aufbewahrung_h))}</p>')
    if not jetzt:
        return kopf + webui.leer(t("systemstat.leer.titel"),
                                 t("systemstat.leer.hinweis", takt=takt_s))

    def _reihe(block, feld="prozent"):
        return [(z.get(block) or {}).get(feld) for z in verlauf]

    # ---------------------------------------------------------- Block A
    cpu = jetzt.get("cpu") or {}
    kerne = cpu.get("kerne") or []
    kern_reihe = ""
    if any(k is not None for k in kerne):
        # Je Kern ein schmaler Balken der AKTUELLEN Messung — die Verteilung
        # ueber die Kerne ist die Aussage, die eine Gesamtzahl verschluckt
        # (ein einzelner ausgelasteter Kern sieht in der Summe harmlos aus).
        breite = max(2, int(_PLAETZE * _BREITE / max(1, len(kerne))) - 1)
        st = []
        for i, k in enumerate(kerne):
            if k is None:
                continue
            h = max(1.0, k / 100.0 * (_HOEHE - 2))
            st.append(f'<rect x="{i * (breite + 1)}" y="{_HOEHE - h:.1f}" '
                      f'width="{breite}" height="{h:.1f}" rx="1"/>')
        kern_reihe = (f'<div class="sst-zl2">{html.escape(t("systemstat.cpu.kerne"))}</div>'
                      f'<svg class="sst-bal sst-kerne" viewBox="0 0 '
                      f'{len(kerne) * (breite + 1)} {_HOEHE}" preserveAspectRatio="none" '
                      f'role="img" aria-label="{html.escape(t("systemstat.cpu.kerne"))}">'
                      + "".join(st) + "</svg>")
    k_cpu = _kachel("CPU", cpu,
                    (f'<span class="sst-gross">{_zahl(cpu.get("prozent"))}</span>'
                     f'<span class="sst-einheit">%</span>' if cpu.get("prozent") is not None
                     else '<span class="sst-gross dim">—</span>'),
                    _balken(_reihe("cpu")) + kern_reihe,
                    ((t("systemstat.cpu.anzahl"), str(cpu.get("n")) if cpu.get("n") else ""),))

    ram = jetzt.get("ram") or {}
    ram_zeilen = (
        (t("systemstat.ram.genutzt"), _zahl(ram.get("genutzt_mb"), " MB")
         if ram.get("genutzt_mb") is not None else ""),
        (t("systemstat.ram.prozesse"), _zahl(ram.get("prozesse_mb"), " MB")
         if ram.get("prozesse_mb") is not None else ""),
        (t("systemstat.ram.grafik"), _zahl(ram.get("grafik_mb"), " MB")
         if ram.get("grafik_mb") else ""),
        (t("systemstat.ram.limit"), _zahl(ram.get("limit_mb"), " MB")
         if ram.get("limit_mb") else ""),
        (t("systemstat.ram.cache"), _zahl(ram.get("cache_mb"), " MB")
         if ram.get("cache_mb") is not None else ""))
    if ram.get("prozent") is None and ram.get("genutzt_mb") is not None:
        # Ohne Container-Speichergrenze gibt es keinen Prozentsatz, aber sehr
        # wohl eine gemessene Belegung. Die grosse Zahl zeigt sie dann in GB;
        # ein „—" waere hier falsch, es gibt ja eine Messung.
        # Der Verlauf zeichnet dann die BELEGUNG, skaliert auf ihren eigenen
        # Hoechstwert im Fenster: eine Prozentreihe gibt es hier nicht, und
        # eine leere Reihe waere eine verschenkte Aussage.
        mb = _reihe("ram", "genutzt_mb")
        k_ram = _kachel("RAM", ram,
                        f'<span class="sst-gross">{ram["genutzt_mb"] / 1024:.1f}</span>'
                        f'<span class="sst-einheit">GB</span>',
                        _balken(mb, max(1.0, max((w for w in mb if w is not None),
                                                 default=1.0))),
                        ram_zeilen, marke=t("systemstat.kein_prozent"))
    else:
        k_ram = _prozent_kachel("RAM", ram, _reihe("ram"), ram_zeilen)

    pl = jetzt.get("platte") or {}
    k_platte = _prozent_kachel(t("systemstat.kachel.platte"), pl, _reihe("platte"), (
        (t("systemstat.platte.frei"), _zahl(pl.get("frei_gb"), " GB", 1)
         if pl.get("frei_gb") is not None else ""),
        (t("systemstat.platte.gesamt"), _zahl(pl.get("gesamt_gb"), " GB", 1)
         if pl.get("gesamt_gb") is not None else ""),
        # Cache-Deckel und Mindestfrei kommen aus Service.speichergrenzen() —
        # dieselbe Quelle wie die Platten-Wache, damit die Seite nie eine
        # andere Grenze zeigt als die, nach der wirklich geraeumt wird.
        (t("systemstat.platte.cache"),
         (f'{_zahl(pl.get("cache_gb"), " GB", 1)} / {_zahl(pl.get("cache_max_gb"), " GB", 1)}'
          if pl.get("cache_gb") is not None and pl.get("cache_max_gb") is not None else "")),
        (t("systemstat.platte.frei_min"), _zahl(pl.get("frei_min_gb"), " GB", 1)
         if pl.get("frei_min_gb") is not None else "")))

    # EINE GPU-Kachel, kein Nebeneinander von zwei (User 25.08.: "sonst kommen die
    # durcheinander"). Zwei Quellen, klar getrennte Aussage:
    #   Gesamtlast der Karte  -> wo lesbar (NVIDIA), das ist die staerkere Auskunft
    #   eigener Anteil        -> ueber DRM-fdinfo, ohne Sonderrechte, traegt ueberall
    # Ist die Gesamtlast da, fuehrt sie; sonst tritt der eigene Anteil an ihre Stelle,
    # und die Beschriftung sagt WELCHE der beiden Zahlen dort steht — eine Kachel, die
    # mal das eine und mal das andere zeigt, ohne es zu sagen, waere die schlimmere Variante.
    gpu = jetzt.get("gpu") or {}
    ge = jetzt.get("gpu_eigen") or {}
    eng = ge.get("engines") or {}
    eig_zeilen = tuple((n, _zahl(w, " %", 1)) for n, w in
                       sorted(eng.items(), key=lambda x: -x[1])[:3] if w > 0)
    if gpu.get("prozent") is not None:
        # Gesamtlast fuehrt; unser Anteil steht als erste Detailzeile darunter
        zeilen = ((t("systemstat.gpu_eigen.zeile"),
                   _zahl(ge.get("prozent"), " %", 1) if ge.get("prozent") is not None else ""),
                  (t("systemstat.gpu.engine"), str(gpu.get("engine") or "")),
                  (t("systemstat.gpu.speicher"),
                   (f'{_zahl(gpu.get("speicher_mb"), " MB")} / {_zahl(gpu.get("speicher_max_mb"), " MB")}'
                    if gpu.get("speicher_mb") is not None else "")),
                  (t("systemstat.gpu.temperatur"), _zahl(gpu.get("temperatur_c"), " °C")
                   if gpu.get("temperatur_c") is not None else ""))
        k_gpu = _prozent_kachel("GPU", gpu, _reihe("gpu"), zeilen)
    else:
        # Keine Gesamtlast auf dieser Maschine: der eigene Anteil IST die Kachel.
        # Der Grund, warum die Gesamtzahl fehlt, steht als Zeile darunter — nicht
        # als eigene leere Kachel daneben.
        quelle = ge if (ge.get("prozent") is not None or not gpu.get("grund")) else gpu
        k_gpu = _prozent_kachel(
            t("systemstat.gpu_eigen.titel"), quelle, _reihe("gpu_eigen"),
            eig_zeilen + (((t("systemstat.gpu.gesamt"), _grund_satz(gpu.get("grund"))),)
                          if gpu.get("grund") else ()))

    npu = jetzt.get("npu") or {}
    k_npu = _prozent_kachel("NPU", npu, _reihe("npu"))

    # ---------------------------------------------------------- Block B
    wk = jetzt.get("worker") or {}
    du = jetzt.get("durchsatz") or {}
    rs = jetzt.get("rueckstau") or {}
    wk_wert = ('<span class="sst-gross dim">—</span>' if wk.get("grund") else
               f'<span class="sst-mittel">'
               f'{html.escape(t("systemstat.worker.laeuft") if wk.get("laeuft") else t("systemstat.worker.ruht"))}'
               f'</span>')
    tod_zeit = ""
    if wk.get("letzter_tod_ts"):
        tod_zeit = f'{datetime.datetime.fromtimestamp(wk["letzter_tod_ts"]):%H:%M}'
    k_worker = _kachel(t("systemstat.kachel.worker"), wk, wk_wert, "", (
        (t("systemstat.worker.tode"), (str(wk.get("tode_24h"))
                                       if wk.get("tode_24h") is not None else "")),
        (t("systemstat.worker.zuletzt"), tod_zeit),
        # Die Ursache ist eine Kurzform aus _todesursache ("signal 9 = SIGKILL
        # — most likely the kernel out-of-memory killer"). Sie bleibt englisch:
        # es ist ein Diagnose-Befund fuer den Supportfall, kein Bedientext.
        (t("systemstat.worker.ursache"), str(wk.get("letzte_ursache") or ""))))
    k_durchsatz = _kachel(t("systemstat.kachel.durchsatz"), du,
                          (f'<span class="sst-gross">{du.get("analysen_1h")}</span>'
                           f'<span class="sst-einheit">/h</span>'
                           if du.get("analysen_1h") is not None
                           else '<span class="sst-gross dim">—</span>'),
                          _balken(_reihe("durchsatz", "analysen_1h"),
                                  max(1.0, max((z.get("durchsatz") or {}).get("analysen_1h") or 0
                                               for z in verlauf) if verlauf else 1.0)), (
        (t("systemstat.durchsatz.tag"), (str(du.get("analysen_24h"))
                                         if du.get("analysen_24h") is not None else "")),
        (t("systemstat.durchsatz.dauer"), _zahl(du.get("dauer_mittel_s"), " s", 1)
         if du.get("dauer_mittel_s") is not None else "")))
    offen = None
    if not rs.get("grund"):
        offen = max(0, int(rs.get("gesamt") or 0) - int(rs.get("fertig") or 0))
    k_stau = _kachel(t("systemstat.kachel.rueckstau"), rs,
                     (f'<span class="sst-gross">{offen}</span>' if offen is not None
                      else '<span class="sst-gross dim">—</span>'), "", (
        (t("systemstat.rueckstau.laeuft"),
         t("systemstat.ja") if rs.get("aktiv") else t("systemstat.nein")),
        (t("systemstat.rueckstau.fenster"), (f'{rs.get("stunden")} h'
                                             if rs.get("stunden") else ""))))

    # W3 Stufe 1 (.399, User-Wunsch: "sehen, dass das System lebt"): die
    # Event-Warteschlange als eigene Kachel — aktuelle Laenge gross, Verlauf
    # als Balkenreihe aus dem 60-s-Ring, dazu Alter des aeltesten Wartenden
    # und die Melde-Spur (offen/gesendet/Fehler).
    q_n = rs.get("queue_n")
    k_queue = _kachel(t("systemstat.kachel.queue"), rs,
                      (f'<span class="sst-gross">{int(q_n)}</span>'
                       if q_n is not None and not rs.get("grund")
                       else '<span class="sst-gross dim">—</span>'),
                      _balken(_reihe("rueckstau", "queue_n"),
                              max(1.0, max(((z.get("rueckstau") or {}).get("queue_n") or 0)
                                           for z in verlauf) if verlauf else 1.0)), (
        (t("systemstat.queue.aeltester"),
         _zahl(rs.get("queue_aeltester_s"), " s", 0)
         if rs.get("queue_aeltester_s") else ""),
        (t("systemstat.queue.spur"),
         (f'{rs.get("spur_n", 0)} · {rs.get("spur_gesendet", 0)} ✓ · '
          f'{rs.get("spur_fehler", 0)} ✗')
         if rs.get("spur_gesendet") is not None else "")))

    # ---------------------------------------------------------- Block C
    lv = jetzt.get("live") or {}
    wa = lv.get("watchers") or {}
    an = sum(1 for w in wa.values() if (w or {}).get("state") == LIVE_AKTIV)
    sup = lv.get("supervisor")
    if isinstance(sup, dict):                       # live_aufsicht_status()
        sup = sup.get("text") or ""
    k_live = _kachel(t("systemstat.kachel.live"), lv,
                     (f'<span class="sst-mittel">{html.escape(str(lv.get("engine") or ""))}</span>'
                      if not lv.get("grund") else '<span class="sst-gross dim">—</span>'), "", (
        (t("systemstat.live.waechter"), (f"{an} / {len(wa)}" if wa else "")),
        # ROH uebergeben: _kachel escapt jeden Zeilenwert selbst (ein zweites
        # escape hier machte aus & ein &amp;amp;).
        (t("systemstat.live.supervisor"), str(sup or ""))))

    stand = f'{datetime.datetime.fromtimestamp(jetzt.get("ts") or 0):%H:%M:%S}'
    return (kopf
            + f'<div class="ek-abschnitt">{html.escape(t("systemstat.block.hardware"))}</div>'
            + f'<div class="sst-gitter">{k_cpu}{k_ram}{k_platte}{k_gpu}{k_npu}</div>'
            + f'<div class="ek-abschnitt">{html.escape(t("systemstat.block.erkennung"))}</div>'
            + f'<div class="sst-gitter">{k_worker}{k_durchsatz}{k_stau}{k_queue}</div>'
            + f'<div class="ek-abschnitt">{html.escape(t("systemstat.block.live"))}</div>'
            + f'<div class="sst-gitter">{k_live}</div>'
            + f'<p class="sub sst-stand">{html.escape(t("systemstat.stand", zeit=stand))}</p>')
