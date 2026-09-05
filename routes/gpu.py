"""routes/gpu — die Seite /gpu: was die Karte traegt, und wie man sie aufteilt.

User-Auftrag (User, 04.09.2026, woertlich): „Wir brauchen einen GPU-Knopf. Den nehmen
wir entweder rechts neben Praesenz oder links neben Easy. Wenn man darauf klickt, dann
sieht man, was fuer eine GPU gefunden wurde und auch, wie viel RAM die GPU hat. Und dann
gibt es Verteiler, damit man sagen kann, wie viel man auf der GPU laufen lassen moechte.
Und dann muessen wir einmal messen, wie viel RAM typischerweise ein Worker braucht und
wie viel ein Live-Agent braucht, und dann kann der Benutzer praktisch hin- und
herstellen, ob er mehr Live-Agenten oder mehr Worker moechte. Und wir muessen natuerlich
ein bisschen Reserve haben, damit er das nicht auf das letzte Byte ausfuellen kann."

ZWEI BALKEN, nicht einer (gemessen 04.09., Begruendung im Kopf von core/gpubudget.py):
Speicher verbrauchen Worker UND Waechter, Rechenzeit praktisch nur die Waechter. Ein
einzelner Regler „mehr Worker oder mehr Waechter" wuerde die falsche Groesse verteilen —
wer Waechter wegnimmt, gewinnt Speicher, aber wer Worker wegnimmt, gewinnt keine
Rechenzeit. Die Seite zeigt deshalb beide Waende und sagt, welche zuerst kommt.

Was die Seite NICHT tut: nachregeln. Sie zeigt, rechnet und speichert die Wahl des
Nutzers; die Zahl greift beim naechsten Dienststart. Ein selbsttaetiger Regler stuende
im Konzept als Stufe 3 und ist bewusst nicht gebaut.

ME1-Muster (routes/unbekannte.py): Daten als Parameter, kein Store-, kein Dateizugriff
im Renderer. Sprachschicht gpu.* (fuenf Sprachen, Deckungsvertrag; alle Schluessel
stehen woertlich im Code)."""
import html

import webui
from core import gpubudget as _gb
from core.sprache import t
# Die Verlaufs-Balken und die Kachel-Bauform der Systemlast-Seite werden hier
# WIEDERVERWENDET, nicht nachgebaut. Sonst haetten wir zwei Darstellungen derselben
# Sache, die auseinanderdriften (CLAUDE.md-Regel gegen Streu-Literale), und der
# Nutzer muesste zwei Bildsprachen lernen.
from routes.systemstat import _balken as _sst_balken, _kachel as _sst_kachel, _zahl as _sst_zahl

# EINE Quelle der Balken-Arten — QS-Ebenen-Regel: fachliche Aufzaehlungen nie als
# Streu-Literal (der Gate-Scanner und die Legende lesen dieselbe Liste).
BALKEN = ("speicher", "rechenzeit")


def _mb(n):
    """MiB menschenlesbar. Unter 1 GB in MB, darueber in GB mit einer Stelle."""
    n = int(n or 0)
    return f"{n} MB" if abs(n) < 1024 else f"{n / 1024:.1f} GB"


def _riegel(teile, gesamt):
    """Ein Balken als Folge farbiger Abschnitte -> HTML. `teile` ist
    [(klasse, mb, beschriftung)]; was ueber `gesamt` hinausgeht, faerbt sich rot
    (die Seite verschweigt eine Ueberbuchung nicht, sie zeigt sie)."""
    if gesamt <= 0:
        return '<div class="gpubar leer"></div>'
    st = []
    for klasse, mb, label in teile:
        if mb <= 0:
            continue
        breite = max(0.5, min(100.0, 100.0 * mb / gesamt))
        st.append(f'<span class="gpuseg {klasse}" style="width:{breite:.2f}%" '
                  f'title="{html.escape(label)}"></span>')
    return f'<div class="gpubar">{"".join(st)}</div>'


def _auslastung(verlauf, gpu, npu, gpu_eigen, ram, kind):
    """Was die Karte GERADE tut — dieselbe Bauform wie die Systemlast-Seite.

    User 04.09.: „Der User moechte natuerlich gerne auch eine Grafik sehen. Wir
    sollten gucken, ob wir analog der Grafik auf dem Systemlast auch hier seine GPU
    darstellen, wie die gerade ausgelastet ist." Genau das: Auslastung, Speicher,
    Temperatur, je mit Stundenverlauf aus dem Ringpuffer.

    Auf Intel ist `gpu.prozent` gesperrt (i915 im Container nicht lesbar), dafuer
    traegt `gpu_eigen` den EIGENEN Anteil ueber DRM-fdinfo und `npu` die NPU. Die
    Seite zeigt, was messbar IST, statt eine Kachel leer zu lassen."""
    def reihe(block, feld="prozent"):
        return [((z.get(block) or {}).get(feld)) for z in (verlauf or [])]

    k = []
    # Auslastung: bei CUDA die Karte selbst, bei Intel der eigene Anteil + NPU
    if (gpu or {}).get("prozent") is not None:
        k.append(_sst_kachel(t("gpu.kachel.last"), gpu,
                             _sst_zahl(gpu.get("prozent"), " %"),
                             _sst_balken(reihe("gpu")),
                             unter=t("gpu.kachel.last_unter")))
    elif (gpu_eigen or {}).get("prozent") is not None:
        e = (gpu_eigen or {}).get("engines") or {}
        k.append(_sst_kachel(t("gpu.kachel.last_eigen"), gpu_eigen,
                             _sst_zahl(gpu_eigen.get("prozent"), " %"),
                             _sst_balken(reihe("gpu_eigen")),
                             zeilen=[(t("gpu.engine.render"), _sst_zahl(e.get("render"), " %")),
                                     (t("gpu.engine.compute"), _sst_zahl(e.get("compute"), " %")),
                                     (t("gpu.engine.video"), _sst_zahl(e.get("video"), " %"))],
                             unter=t("gpu.kachel.last_eigen_unter")))
    if (npu or {}).get("prozent") is not None:
        k.append(_sst_kachel(t("gpu.kachel.npu"), npu,
                             _sst_zahl(npu.get("prozent"), " %"),
                             _sst_balken(reihe("npu")),
                             unter=t("gpu.kachel.npu_unter")))
    # Speicher: auf der Karte (CUDA) oder im Arbeitsspeicher (iGPU teilt ihn sich)
    if (gpu or {}).get("speicher_max_mb"):
        g = gpu
        k.append(_sst_kachel(t("gpu.kachel.vram"), g,
                             f'{_mb(g.get("speicher_mb"))} / {_mb(g.get("speicher_max_mb"))}',
                             _sst_balken(reihe("gpu", "speicher_mb"),
                                         max_wert=float(g.get("speicher_max_mb") or 1)),
                             unter=t("gpu.kachel.vram_unter")))
    elif (ram or {}).get("prozesse_mb") is not None:
        k.append(_sst_kachel(t("gpu.kachel.ram"), ram,
                             _mb(ram.get("prozesse_mb")),
                             _sst_balken(reihe("ram", "prozesse_mb"),
                                         max_wert=float(ram.get("gesamt_mb") or 16384)),
                             unter=t("gpu.kachel.ram_unter")))
    if (gpu or {}).get("temperatur_c") is not None:
        k.append(_sst_kachel(t("gpu.kachel.temperatur"), gpu,
                             _sst_zahl(gpu.get("temperatur_c"), " °C"),
                             _sst_balken(reihe("gpu", "temperatur_c"), max_wert=100.0),
                             unter=t("gpu.kachel.temperatur_unter")))
    if not k:
        return ""
    return (f'<h3>{html.escape(t("gpu.abschnitt.jetzt"))}</h3>'
            f'<div class="sst-grid">{"".join(k)}</div>')


def _regler(vorschlag, kapazitaet_jetzt, auto, kind, laeuft_mit=None,
            passt_max=None, budget_js=None):
    """Der Bedienteil — steht auf JEDER Variante der Seite.

    Fehler der ersten Fassung (User 04.09. am Screenshot): im Zweig „Speicher nicht
    messbar" (Intel) fehlte er ganz. Der Nutzer las „aktuell 4 Plaetze" und hatte keine
    Moeglichkeit, etwas daran zu tun — eine Seite, die einen Wert nennt und keinen Weg
    anbietet, ihn zu aendern, ist eine Sackgasse. Der Bedienteil haengt deshalb nicht
    mehr am Messbarkeits-Fall."""
    opt = []
    for i in range(0, 5):
        wert = t("gpu.auto") if i == 0 else str(i)
        gewaehlt = " selected" if (auto and i == 0) or (not auto and i == kapazitaet_jetzt) else ""
        zusatz = f' — {t("gpu.vorschlag_ist", n=vorschlag)}' if i == 0 else ""
        opt.append(f'<option value="{i}"{gewaehlt}>{html.escape(wert)}{html.escape(zusatz)}</option>')
    # Laeuft gerade etwas anderes, als eingestellt ist? Das MUSS dastehen — der Wert
    # greift erst beim naechsten Start, und ohne diesen Satz haelt man den alten
    # Zustand fuer den neuen (User 04.09. an der Seite).
    abweich = ""
    if laeuft_mit is not None and laeuft_mit != kapazitaet_jetzt:
        abweich = (f'<p class="warn gpuzeile">'
                   f'{html.escape(t("gpu.noch_alt", laeuft=laeuft_mit, gesetzt=kapazitaet_jetzt))}</p>')
    # Die Vorschau rechnet im Browser mit DENSELBEN Zahlen wie der Server (sie kommen
    # als Datensatz mit) — der Nutzer sieht beim Waehlen, was es kostet, statt
    # speichern/neu starten/nachsehen zu muessen.
    daten = (f' data-mb-worker="{budget_js.get("mb_worker")}"'
             f' data-frei="{budget_js.get("frei")}"'
             f' data-jetzt="{budget_js.get("jetzt")}"' if budget_js else "")
    grenze = ("" if not passt_max else
              f'<p class="gpuzeile">{html.escape(t("gpu.passt_hoechstens", n=passt_max))}</p>')
    return (f'<h3>{html.escape(t("gpu.regler.titel"))}</h3>'
            f'<p class="gpuzeile">{html.escape(t("gpu.regler.erklaerung", n=vorschlag, hw=kind))}</p>'
            f'{grenze}{abweich}'
            f'<p><select id="gpu-plaetze"{daten}>{"".join(opt)}</select> '
            f'<button class="gtb" id="gpu-speichern">{html.escape(t("gpu.speichern"))}</button> '
            f'<span id="gpu-msg" class="gpuzeile"></span></p>'
            f'<p class="gpuzeile" id="gpu-vorschau"></p>'
            # Der Weg muss hier zu Ende gehen (User 04.09.): eine Seite, die einen
            # Neustart VERLANGT und keinen anbietet, schickt den Nutzer suchen. Der
            # Knopf ruft dieselbe Route wie der auf der Konfigurationsseite
            # (POST /neustart -> Service.neustart, re-exec, supervisor-unabhaengig) —
            # kein zweiter Neustart-Weg, nur ein zweiter Ort, an dem er erreichbar ist.
            f'<p class="gpuzeile"><button class="gtb" id="gpu-neustart">'
            f'{html.escape(t("gpu.neustart_knopf"))}</button> '
            f'<span id="gpu-nrstatus" class="gpuzeile klein"></span></p>'
            # Der Satz "wirkt ab dem naechsten Neustart" gehoert NUR hierhin, solange
            # wirklich etwas aussteht. Stand er immer da, las man ihn auch direkt nach
            # einem Neustart und fragte sich, ob die Einstellung nun greift oder nicht
            # (User 04.09. am Screenshot). Stimmen eingestellt und laufend ueberein,
            # sagt die Seite das stattdessen — eine Auskunft statt einer Daueransage.
            + (f'<p class="gpuzeile klein">{html.escape(t("gpu.neustart_noetig"))}</p>'
               if laeuft_mit is not None and laeuft_mit != kapazitaet_jetzt
               else f'<p class="gpuzeile klein ok">'
                    f'{html.escape(t("gpu.laeuft_wie_eingestellt", n=kapazitaet_jetzt))}</p>'))


def _klasse_name(art):
    """Anzeigename einer Platz-Klasse (`Analyseplaetze.ARTEN`).

    Die drei Schluessel stehen hier WOERTLICH in `t()`-Aufrufen — der Modul-Kopf sagt
    es, und die Gate-Stufe „Sprach-Deckung" liest genau diese Literale; ein
    zusammengesetzter Schluessel (Praefix plus Klassenname) waere dort blind und die
    Texte gaelten als tot. Eine unbekannte Klasse bekommt ihren ROHEN Namen statt einer
    falschen Beschriftung (K1: die Anzeige darf nicht behaupten, was sie nicht weiss)."""
    if art == "analyse":
        return t("gpu.klasse.analyse")
    if art == "ernte":
        return t("gpu.klasse.ernte")
    if art == "bg":
        return t("gpu.klasse.bg")
    return art


def _klassen_text(klassen):
    """„ (1 analysis, 1 harvest)" — WER die belegten Plaetze haelt, oder "" wenn
    keiner belegt ist.

    C1 (05.09.2026, bauplan_0505.md §1): seit .505 halten ALLE GPU-Verbraucher einen
    Platz, nicht nur die Ereignis-Analyse — der Lernlauf (`ernte`) und die
    Hintergrund-Jobs Sammeln/Wanduhr (`bg`) ebenso. „2 von 4 belegt" allein liesse den
    Nutzer im Unklaren, ob seine Analysen laufen oder ob der Lernlauf die Karte haelt.
    Reihenfolge und Vollstaendigkeit kommen vom Aufrufer aus `Analyseplaetze.ARTEN`
    (die eine Aufzaehlung), damit die Seite keine Klasse still verschluckt, die die
    Vergabestelle kennt."""
    if not klassen:
        return ""
    teile = [f"{n} {_klasse_name(art)}"
             for art, n in (klassen.items() if isinstance(klassen, dict) else klassen)
             if n]
    return f' ({", ".join(teile)})' if teile else ""


def _laeuft(n_worker, n_waechter, belegt, klassen=None):
    """Was gerade arbeitet — auf JEDER Variante, auch ohne Speichermessung.
    Ohne diese Zeile weiss der Nutzer nicht, ob seine Einstellung ueberhaupt greift."""
    return (f'<p class="gpuzeile"><b>{html.escape(t("gpu.laeuft.titel"))}</b> '
            f'{html.escape(t("gpu.laeuft.zeile", plaetze=n_worker, belegt=belegt, waechter=n_waechter, klassen=_klassen_text(klassen)))}</p>')


def _JS(vorschau_text="", frage="", nicht_erreichbar="", zu_wenig_text="",
        zu_wenig_titel=""):
    # Die Vorschau erscheint NUR, wo es etwas vorherzusagen gibt. Ohne messbaren
    # Grafikspeicher (Intel im Container) fehlt `data-mb-worker`, und dann rechnete
    # die erste Fassung stur 0 - 0 = 0 und behauptete „wuerde 0 MB frei lassen"
    # (User 04.09. an der Seite). Eine Zahl ohne Grundlage ist schlechter als keine.
    v = ("var s=document.getElementById('gpu-plaetze');"
         "var vp=document.getElementById('gpu-vorschau');"
         "if(s&&vp&&s.dataset.mbWorker){var f=function(){"
         "var n=parseInt(s.value,10);var jetzt=parseInt(s.dataset.jetzt||'0',10);"
         "if(isNaN(n)||n===0){vp.textContent='';return;}"
         "var mb=parseInt(s.dataset.mbWorker,10);"
         "var frei=parseInt(s.dataset.frei||'0',10);"
         "var d=(n-jetzt)*mb;var rest=frei-d;"
         # Eine NEGATIVE Zahl als "frei" anzuzeigen ist irrefuehrend ("wuerde -180 MB
         # frei lassen", User 04.09. am Screenshot). Passt es nicht, sagt die Zeile das
         # und nennt, wie viel FEHLT — dieselbe Zahl, aber als Aussage, die stimmt.
         "var f=function(x){return x>=1024?(x/1024).toFixed(1)+' GB':x+' MB';};"
         # Bei Ueberbuchung ist der Speichern-Knopf GESPERRT (User-Entscheid 04.09.).
         # Er wird nur dort gesperrt, wo wirklich gerechnet werden kann: ohne
         # `data-mb-worker` (Intel, Speicher nicht auslesbar) laeuft dieser ganze
         # Zweig nicht, und der Knopf bleibt bedienbar — eine Sperre auf Basis
         # fehlender Zahlen waere vorgetaeuschte Sicherheit.
         "var sb=document.getElementById('gpu-speichern');"
         "if(rest<0){vp.textContent=" + repr(zu_wenig_text) + ".replace('{fehlt}',f(-rest));"
         "vp.className='gpuzeile warn';"
         "if(sb){sb.disabled=true;sb.title=" + repr(zu_wenig_titel) + ";}}else{"
         "vp.textContent=" + repr(vorschau_text) + ".replace('{rest}',f(rest));"
         "vp.className='gpuzeile';"
         "if(sb){sb.disabled=false;sb.title='';}}};"
         # Alte Statusmeldungen ("gespeichert", "Neustart laeuft", "nicht erreichbar")
         # bleiben sonst stehen und behaupten einen Zustand, der laengst vorbei ist.
         # Wer neu waehlt, faengt neu an.
         "s.addEventListener('change',function(){"
         "var m=document.getElementById('gpu-msg');if(m)m.textContent='';"
         "var st=document.getElementById('gpu-nrstatus');if(st)st.textContent='';"
         "f();});f();}")
    return ("<script>(function(){" + v +
            "var b=document.getElementById('gpu-speichern');if(!b)return;"
            "b.onclick=async function(){var s=document.getElementById('gpu-plaetze');"
            "var m=document.getElementById('gpu-msg');m.textContent='…';"
            "try{var r=await fetch('/gpu_speichern',{method:'POST',"
            "headers:{'Content-Type':'application/json'},"
            "body:JSON.stringify({analyse_plaetze:parseInt(s.value,10)})});"
            "var d=await r.json();m.textContent=d.ok?d.msg||'ok':(d.fehler||'error');"
            # Nach dem Speichern den Neustart-Knopf hervorheben — jetzt ist er der
            # naechste sinnvolle Schritt, vorher war er nur eine Moeglichkeit.
            "var nb=document.getElementById('gpu-neustart');"
            "if(nb&&d.ok){nb.classList.add('an');}}"
            # `TypeError: Load failed` heisst im Browser schlicht „Server nicht
            # erreichbar" — nach einem Neustart der Normalfall. Ein Nutzer kann mit
            # dem Wortlaut nichts anfangen, deshalb ein Satz statt der Ausnahme.
            "catch(e){m.textContent=" + repr(nicht_erreichbar) + ";}};"
            "var nb=document.getElementById('gpu-neustart');"
            "if(nb){nb.onclick=function(){"
            "if(!confirm(" + repr(frage) + "))return;"
            "var st=document.getElementById('gpu-nrstatus');st.textContent='…';"
            "fetch('/neustart',{method:'POST'}).then(function(r){return r.json();})"
            ".then(function(d){st.textContent=d.msg||'';})"
            ".catch(function(){st.textContent='';});};}"
            "})();</script>")


def seite(gpu, n_worker, n_waechter, vorschlag, kapazitaet_jetzt, auto,
          belegt=0, npu=None, gpu_eigen=None, ram=None, cpu=None, verlauf=None,
          klassen=None):
    """Die ganze Seite als HTML. Reine Funktion — alle Daten kommen herein.

    gpu: dict aus /health.system.gpu ({"kind","speicher_mb","speicher_max_mb",...})
         oder None/leer, wenn keine Karte gefunden wurde.
    n_worker/n_waechter: was gerade laeuft.
    vorschlag: die auf dieser Hardware gemessene Platzzahl (P4).
    kapazitaet_jetzt: die aktuell eingestellte Platzzahl.
    auto: True, wenn analyse_plaetze=0 (automatisch) gesetzt ist.
    klassen: [(art, anzahl)] der BELEGTEN Plaetze aus derselben `zustand()`-Auskunft
        wie `belegt` (C1) — sagt, wer sie haelt: Analyse, Lernlauf, Hintergrund.
    """
    gesamt = int((gpu or {}).get("speicher_max_mb") or 0)
    kind = (gpu or {}).get("kind") or "cpu"
    kopf_name = (gpu or {}).get("name") or kind.upper()
    last = _auslastung(verlauf, gpu, npu, gpu_eigen, ram, kind)
    # Der Weg zu den Waechtern gehoert auf DIESE Seite: sie sagt, dass die Waechter
    # Speicher und Rechenzeit kosten — die naheliegende Handlung waere, einen
    # abzuschalten, und dafuer musste man bisher erst suchen, wo das geht.
    zu_live = (f'<p class="gpuzeile"><a class="gtb" href="/live">'
               f'{html.escape(t("gpu.zu_live"))}</a></p>')

    # --- kein Beschleuniger: ehrlich sagen, aber bedienbar bleiben ----------
    if not gesamt and (not kind or kind == "cpu"):
        return (f'<div class="kachel"><h2>{html.escape(t("gpu.titel"))}</h2>'
                f'<p class="hinweis">{html.escape(t("gpu.keine_karte"))}</p>'
                f'<p>{html.escape(t("gpu.keine_karte_cpu"))}</p>'
                f'{last}{_laeuft(kapazitaet_jetzt, n_waechter, belegt, klassen)}'
                f'{_regler(vorschlag, kapazitaet_jetzt, auto, kind, laeuft_mit=n_worker)}'
                f'</div>{_JS(t("gpu.vorschau"), t("gpu.neustart_frage"), t("gpu.nicht_erreichbar"),
                            t("gpu.vorschau_zu_wenig"), t("gpu.speichern_gesperrt"))}')

    # --- Beschleuniger da, Speicher nicht messbar (Intel im Container) ------
    if not gesamt:
        return (f'<div class="kachel"><h2>{html.escape(t("gpu.titel"))}</h2>'
                f'<p class="gpukarte"><b>{html.escape(kopf_name)}</b></p>'
                f'<p class="hinweis">{html.escape(t("gpu.nicht_messbar"))}</p>'
                f'{last}{_laeuft(kapazitaet_jetzt, n_waechter, belegt, klassen)}{zu_live}'
                f'{_regler(vorschlag, kapazitaet_jetzt, auto, kind, laeuft_mit=n_worker)}'
                f'</div>{_JS(t("gpu.vorschau"), t("gpu.neustart_frage"), t("gpu.nicht_erreichbar"),
                            t("gpu.vorschau_zu_wenig"), t("gpu.speichern_gesperrt"))}')

    # --- volle Anzeige -----------------------------------------------------
    b = _gb.budget(gesamt, n_worker, n_waechter)
    res = b["reserve_mb"]
    vor_geklemmt, passt_max = _gb.vorschlag_geklemmt(vorschlag, gesamt, n_waechter)
    _temp = (gpu or {}).get("temperatur_c")
    _tempstr = "" if _temp is None else f", {_temp} °C"
    kopf = (f'<div class="kachel"><h2>{html.escape(t("gpu.titel"))}</h2>'
            f'<p class="gpukarte"><b>{html.escape(kopf_name)}</b>'
            f' — {_mb(gesamt)} {html.escape(t("gpu.speicher_gesamt"))}{_tempstr}</p>')

    b1 = _riegel([("w", b["worker_mb"], f'{n_worker} × {t("gpu.worker")}'),
                  ("g", b["waechter_mb"], f'{n_waechter} × {t("gpu.waechter")}'),
                  ("d", b["dienst_mb"], t("gpu.dienst")),
                  ("f", max(0, b["frei_mb"]), t("gpu.frei")),
                  ("r", res, t("gpu.reserve"))], gesamt)
    speicher = (
        f'<h3>{html.escape(t("gpu.balken.speicher"))}</h3>{b1}'
        f'<p class="gpuzeile">'
        f'<span class="lg w"></span>{n_worker} × {html.escape(t("gpu.worker"))} '
        f'({_mb(b["worker_mb"])}) &nbsp; '
        f'<span class="lg g"></span>{n_waechter} × {html.escape(t("gpu.waechter"))} '
        f'({_mb(b["waechter_mb"])}) &nbsp; '
        f'<span class="lg f"></span>{html.escape(t("gpu.frei"))} '
        f'({_mb(max(0, b["frei_mb"]))}) &nbsp; '
        f'<span class="lg r"></span>{html.escape(t("gpu.reserve"))} ({_mb(res)})</p>')

    med, hoch = b["rechen_median"], b["rechen_max"]
    b2 = _riegel([("g", int(min(1.0, med) * 1000), t("gpu.rechen.median")),
                  ("gh", int(min(1.0, max(0.0, hoch - med)) * 1000), t("gpu.rechen.spitze")),
                  ("f", int(max(0.0, 1.0 - hoch) * 1000), t("gpu.frei"))], 1000)
    rechen = (
        f'<h3>{html.escape(t("gpu.balken.rechenzeit"))}</h3>{b2}'
        f'<p class="gpuzeile">{html.escape(t("gpu.rechen.erklaerung"))}</p>'
        f'<p class="gpuzeile"><span class="lg g"></span>{med:.0%} '
        f'{html.escape(t("gpu.rechen.median"))} &nbsp; '
        f'<span class="lg gh"></span>{html.escape(t("gpu.rechen.bis"))} {hoch:.0%}</p>')

    if not b["passt"]:
        urteil = f'<p class="warn">{html.escape(t("gpu.passt_nicht"))}</p>'
    else:
        moeglich = _gb.worker_noch_moeglich(gesamt, n_waechter, n_worker)
        eng = (t("gpu.engpass.speicher") if b["engpass"] == "speicher"
               else t("gpu.engpass.rechenzeit"))
        urteil = (f'<p class="ok">{html.escape(eng)} '
                  f'{html.escape(t("gpu.noch_moeglich", n=moeglich))}</p>')

    regler = _regler(vor_geklemmt, kapazitaet_jetzt, auto, kind,
                     laeuft_mit=n_worker, passt_max=passt_max,
                     budget_js={"mb_worker": _gb.VRAM_JE_WORKER_MB,
                                "frei": max(0, b["frei_mb"]), "jetzt": n_worker})
    quelle = (f'<p class="gpuzeile klein">'
              f'{html.escape(t("gpu.messwerte", worker=_gb.VRAM_JE_WORKER_MB, erster=_gb.VRAM_ERSTER_WAECHTER_MB, weiterer=_gb.VRAM_JE_WEITEREM_WAECHTER_MB))}'
              f'</p>')
    # REIHENFOLGE (User 04.09.: „damit der User nicht nach unten scrollen muss, um
    # etwas einzustellen"): zuerst das, was er TUN kann und wissen muss — Zustand,
    # Urteil, Regler. Die Grafiken kommen darunter und liegen NEBENEINANDER statt
    # langgezogen untereinander; sie erklaeren, sie werden nicht bedient.
    oben = (f'<div class="gpu-oben">'
            f'<div class="gpu-links">{urteil}'
            f'{_laeuft(kapazitaet_jetzt, n_waechter, belegt, klassen)}{zu_live}</div>'
            f'<div class="gpu-rechts">{regler}</div></div>')
    balken = (f'<div class="gpu-zwei">'
              f'<div class="gpu-sp">{speicher}</div>'
              f'<div class="gpu-sp">{rechen}</div></div>')
    return (kopf + oben + balken + last + quelle + "</div>"
            + _JS(t("gpu.vorschau"), t("gpu.neustart_frage"), t("gpu.nicht_erreichbar"),
                            t("gpu.vorschau_zu_wenig"), t("gpu.speichern_gesperrt")))
