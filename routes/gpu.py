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
            passt_max=None, budget_js=None, leiter_satz=None, legacy=False):
    """Der Bedienteil — steht auf JEDER Variante der Seite.

    Fehler der ersten Fassung (User 04.09. am Screenshot): im Zweig „Speicher nicht
    messbar" (Intel) fehlte er ganz. Der Nutzer las „aktuell 4 Plaetze" und hatte keine
    Moeglichkeit, etwas daran zu tun — eine Seite, die einen Wert nennt und keinen Weg
    anbietet, ihn zu aendern, ist eine Sackgasse. Der Bedienteil haengt deshalb nicht
    mehr am Messbarkeits-Fall.

    .536 B5 (R7): DIES IST DIE EINE EINSTELLUNG. Gestellt werden die
    RECHENSTRAENGE (`worker_straenge`); die Analyseplaetze folgen ihnen im Dienst
    (`Service._plaetze_an_straenge`). `kapazitaet_jetzt` ist deshalb der
    eingestellte Strang-Wert (in der Automatik: der laufende), `vorschlag` die
    gerechnete Strangzahl hinter „automatisch", `laeuft_mit` das, was gerade
    wirklich rechnet.

    `legacy` (L-4): im Modus `worker: false` gibt es keinen Analyse-Worker und
    damit keine Rechenstraenge — der Regler sagt das in EINER Zeile, statt etwas
    zu versprechen, das der Modus nicht liefert. Ausgegraut wird nichts: der
    Nutzer darf den Wert stellen, er greift beim Umschalten.

    `kind` steht seit .536 nur noch in der Signatur: der Reglertext nennt die
    Hardware nicht mehr (der Messsatz mit `{hw}` ist zu `gpu.messwerte`
    gewandert). Der Parameter bleibt, weil alle drei Aufrufer ihn stellig
    uebergeben und ein Umbau der Signatur nichts gewinnt."""
    opt = []
    # .535: die Auswahl reicht bis `STRAENGE_MAX` (seit diesem Stand 6) und
    # nicht mehr bis zu einer fest hingeschriebenen 4 — sonst kann der Nutzer
    # eine Zahl gar nicht waehlen, die der Dienst annehmen wuerde.
    for i in range(0, _gb.STRAENGE_MAX + 1):
        wert = t("gpu.auto") if i == 0 else str(i)
        gewaehlt = " selected" if (auto and i == 0) or (not auto and i == kapazitaet_jetzt) else ""
        zusatz = f' — {t("gpu.vorschlag_ist", n=vorschlag)}' if i == 0 else ""
        opt.append(f'<option value="{i}"{gewaehlt}>{html.escape(wert)}{html.escape(zusatz)}</option>')
    # Laeuft gerade etwas anderes, als eingestellt ist? Das MUSS dastehen — der Wert
    # greift erst beim naechsten Start, und ohne diesen Satz haelt man den alten
    # Zustand fuer den neuen (User 04.09. an der Seite).
    abweich = ""
    if (laeuft_mit is not None and laeuft_mit != kapazitaet_jetzt
            and not leiter_satz):
        abweich = (f'<p class="warn gpuzeile">'
                   f'{html.escape(t("gpu.noch_alt", laeuft=laeuft_mit, gesetzt=kapazitaet_jetzt))}</p>')
    # .535 (Inhaber am Screenshot, 15.09. 18:0x): WO DIE LEITER SPRICHT, SPRICHT
    # SIE ALLEIN. Auf Karten-Backends standen zwei Saetze nebeneinander, die
    # sich widersprachen: der Leiter-Satz („der Dienst stellt auf 3 Plaetze =
    # 3 Rechenstraenge um") und der alte Plaetze-Satz („laeuft noch mit 2; 4 ist
    # eingestellt"). Die 4 ist die eingestellte OBERGRENZE, die 3 das, was die
    # Karte traegt — der alte Satz las sich wie ein zweites, konkurrierendes
    # Urteil. Er entfaellt deshalb, sobald die Leiter dasteht; sie nennt beide
    # Zahlen ohnehin (Soll und was bis zum naechsten Worker-Start laeuft).
    # Die Vorschau rechnet im Browser mit DENSELBEN Zahlen wie der Server (sie kommen
    # als Datensatz mit) — der Nutzer sieht beim Waehlen, was es kostet, statt
    # speichern/neu starten/nachsehen zu muessen.
    daten = (f' data-mb-worker="{budget_js.get("mb_worker")}"'
             f' data-frei="{budget_js.get("frei")}"'
             f' data-jetzt="{budget_js.get("jetzt")}"' if budget_js else "")
    if leiter_satz:
        # .534 (B10): auf Karten-Backends sagt die Leiter, wie viele Plaetze es
        # gibt — und dass die Einstellung eine OBERGRENZE ist. Die alte Zeile
        # rechnete Plaetze je Prozess und stimmt dort nicht mehr.
        grenze = f'<p class="gpuzeile">{html.escape(leiter_satz)}</p>'
    else:
        grenze = ("" if not passt_max else
                  f'<p class="gpuzeile">{html.escape(t("gpu.passt_hoechstens", n=passt_max))}</p>')
    # L-4: EINE Zeile, kein neuer Codeweg — der Legacy-Modus bekommt keine
    # eigene Seite und keinen eigenen Regler, nur die Wahrheit daneben.
    _leg = ("" if not legacy else
            f'<p class="gpuzeile warn">{html.escape(t("gpu.regler.legacy"))}</p>')
    return (f'<h3>{html.escape(t("gpu.regler.titel"))}</h3>'
            f'<p class="gpuzeile">{html.escape(t("gpu.regler.erklaerung"))}</p>{_leg}'
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
            #
            # .536 B6 (L-4, Randstueck): IM LEGACY-MODUS SCHWEIGT DIESE ZEILE.
            # „Active: the service is computing on 4 thread(s)" stand dort
            # direkt unter der Zeile, die sagt, dass es in diesem Modus gar
            # keine Rechenstraenge gibt — zwei Saetze, die einander widersprechen,
            # und die Zahl kam obendrein aus der Kapazitaet der Vergabestelle,
            # nicht aus einem laufenden Worker (den gibt es hier nicht). Die
            # Legacy-Zeile oben traegt die Wahrheit allein; eine ausstehende
            # Einstellung greift, sobald `worker` wieder an ist.
            + ("" if legacy else
               f'<p class="gpuzeile klein">{html.escape(t("gpu.neustart_noetig"))}</p>'
               if laeuft_mit is not None and laeuft_mit != kapazitaet_jetzt
               else f'<p class="gpuzeile klein ok">'
                    f'{html.escape(t("gpu.laeuft_wie_eingestellt", n=kapazitaet_jetzt))}</p>'))


def _klasse_name(art):
    """Anzeigename einer Platz-Klasse (`Analyseplaetze.ARTEN`).

    Die vier Schluessel stehen hier WOERTLICH in `t()`-Aufrufen — der Modul-Kopf sagt
    es, und die Gate-Stufe „Sprach-Deckung" liest genau diese Literale; ein
    zusammengesetzter Schluessel (Praefix plus Klassenname) waere dort blind und die
    Texte gaelten als tot. Eine unbekannte Klasse bekommt ihren ROHEN Namen statt einer
    falschen Beschriftung (K1: die Anzeige darf nicht behaupten, was sie nicht weiss).

    B1 (.507): `interaktiv` kommt dazu. Und `ernte` wird umbenannt statt neu
    beschriftet — unter dieser Klasse laufen Lernlauf UND Kalibrier-Auffueller,
    „Lernlauf" war also schon vorher nur die halbe Wahrheit (L9).

    .536 B4.2: `live` kommt dazu — das Koerper-Urteil, das eine laufende Analyse
    selbst anstoesst. Es hatte bis .535 gar keinen Platz und war deshalb auf
    dieser Kachel unsichtbar, obwohl es auf demselben Hintergrund-Strang rechnete
    wie Ernte und Sammeln."""
    if art == "analyse":
        return t("gpu.klasse.analyse")
    if art == "ernte":
        return t("gpu.klasse.ernte")
    if art == "bg":
        return t("gpu.klasse.bg")
    if art == "interaktiv":
        return t("gpu.klasse.interaktiv")
    if art == "live":
        return t("gpu.klasse.live")
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
            # .536 B5 (R7): der Regler schreibt die RECHENSTRAENGE. Der
            # Feldname ist derselbe wie im Config-Store und im Schema
            # (`worker_straenge`) — die Route reicht ihn durch
            # `config_schreiben`, es gibt keinen zweiten Weg in die Datei.
            "body:JSON.stringify({worker_straenge:parseInt(s.value,10)})});"
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
          klassen=None, straenge=None, mess_n=None, legacy=False):
    """Die ganze Seite als HTML. Reine Funktion — alle Daten kommen herein.

    gpu: dict aus /health.system.gpu ({"kind","speicher_mb","speicher_max_mb",...})
         oder None/leer, wenn keine Karte gefunden wurde.
    n_worker/n_waechter: was gerade laeuft (n_worker = die Platzzahl der
        Vergabestelle, seit .536 = die Zahl der laufenden Rechenstraenge).
    vorschlag (.536 B5): die GERECHNETE Strangzahl (`worker_straenge.formel_n`) —
        die Zahl hinter „automatisch". Bis .535 war es die gemessene Platzzahl;
        der Regler stellt seit R7 Straenge, und ein Vorschlag muss dieselbe
        Groesse meinen wie der Regler.
    kapazitaet_jetzt: der eingestellte Strang-Wert (in der Automatik der
        laufende, damit „laeuft noch mit X" nicht gegen eine 0 vergleicht).
    auto: True, wenn worker_straenge=0 (automatisch) gesetzt ist.
    mess_n (.536 B5): die auf dieser Hardware gemessene Zahl GLEICHZEITIGER
        ANALYSEN. Sie steuert seit R7 nichts mehr und steht deshalb bei den
        Messwerten statt im Reglertext (Bauplan B5.2: eine Zahl unter falschem
        Namen ist schlechter als keine).
    legacy (.536 B5, L-4): True im Modus `worker: false` — dort gibt es keinen
        Analyse-Worker, der Regler sagt es in einer Zeile.
    klassen: [(art, anzahl)] der BELEGTEN Plaetze aus derselben `zustand()`-Auskunft
        wie `belegt` (C1) — sagt, wer sie haelt: Analyse, Lernlauf, Hintergrund.
    straenge (.534 B10): der Strang-Block aus /health (`worker_straenge`) oder
        None. Auf Karten-Backends (`mass == "vram"`) kommt die Platzzahl seit
        .532 aus der STRANGZAHL der Leiter, nicht mehr aus einer Platz-je-Prozess-
        Rechnung. Die beiden Saetze dieser Seite, die noch so rechneten („at most
        N slot(s) fit into the memory", „Does not fit — X short") stimmten dort
        nicht mehr und schickten den Nutzer einen Waechter abschalten, der nichts
        geaendert haette. DIESELBE Quelle wie /health, nicht eine zweite Rechnung.
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
                f'{last}{_laeuft(n_worker, n_waechter, belegt, klassen)}'
                f'{_regler(vorschlag, kapazitaet_jetzt, auto, kind, laeuft_mit=n_worker, legacy=legacy)}'
                f'</div>{_JS(t("gpu.vorschau"), t("gpu.neustart_frage"), t("gpu.nicht_erreichbar"),
                            t("gpu.vorschau_zu_wenig"), t("gpu.speichern_gesperrt"))}')

    # --- Beschleuniger da, Speicher nicht messbar (Intel im Container) ------
    if not gesamt:
        return (f'<div class="kachel"><h2>{html.escape(t("gpu.titel"))}</h2>'
                f'<p class="gpukarte"><b>{html.escape(kopf_name)}</b></p>'
                f'<p class="hinweis">{html.escape(t("gpu.nicht_messbar"))}</p>'
                f'{last}{_laeuft(n_worker, n_waechter, belegt, klassen)}{zu_live}'
                f'{_regler(vorschlag, kapazitaet_jetzt, auto, kind, laeuft_mit=n_worker, legacy=legacy)}'
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

    # .535 (g1): DIE SPEICHERLEISTE ZEIGT DIE KARTE, WIE SIE GEMESSEN IST.
    #
    # Anlass ist der Screenshot der Feldtester-Anlage vom 15.09.: die Leiste sagte
    # „1,7 GB frei" und „1,8 GB Reserve", waehrend /health im selben Moment 7596
    # MiB gemessen frei und eine Reserve von 0 (Quelle config) fuehrte. Beide
    # Zahlen kamen aus `_gb.budget(...)` — der ANKER-Formel, die rechnet, was
    # eine 6-GB-Referenzkarte fuer n Worker und n Waechter braeuchte, und die
    # von der Karte, auf der wir stehen, nichts weiss. Auf der Seite, die dem
    # Nutzer sagt, wieviel Platz er hat, ist das die falsche Quelle.
    #
    # Gezeigt wird deshalb, wo es einen gemessenen Frei-Wert gibt, DIESELBE
    # Rechnung wie in /health (`worker_straenge`), und jedes Segment traegt
    # seine Herkunft:
    #   gemessen  der eigene Kartenanteil des laufenden Workers (Prozess-Sonde)
    #             und, als Differenz, was sonst noch belegt ist;
    #   Posten    Waechter und Dienst — die stehen weiter aus den Stuetzwerten,
    #             weil sie auf dieser Karte (noch) nicht je Prozess gemessen
    #             werden. Sie sind BESCHRIFTET, nicht als Messung getarnt.
    # Die Reserve nennt ihre Quelle (Einstellung oder Formel) — sie war der
    # zweite falsche Wert im Screenshot.
    #
    # NICHT ZUORDENBAR IST EINE AUSSAGE: nennt der Treiber im Container unsere
    # pid nicht (Feldfall `kein_eintrag`), gibt es kein Worker-Segment, sondern
    # ein beschriftetes „Anteil nicht zuordenbar" — und alles Belegte steht in
    # EINEM Segment. Eine 0 daneben waere die luegende Diagnose, die .535
    # ueberall abstellt.
    _stv = straenge if (straenge or {}).get("mass") == "vram" else None
    _gem_frei = int((_stv or {}).get("frei_gemessen_mb") or 0)
    if _stv and _gem_frei > 0:
        res = int(_stv.get("reserve_mb") or 0)
        # Die Schluessel stehen WOERTLICH da (Sprach-Deckung des Gates, s. u.).
        _q_res = (t("gpu.q.config") if str(_stv.get("reserve_quelle") or "") == "config"
                  else t("gpu.q.formel"))
        _w_mb = int(_stv.get("laufend_eigen_mb") or 0)
        _w_grund = _stv.get("laufend_eigen_grund")
        _belegt = max(0, gesamt - _gem_frei)
        # Die Posten werden am wirklich Belegten GEKLEMMT: ein Posten, der
        # groesser ist als das, was die Karte traegt, waere keine Schaetzung
        # mehr, sondern ein Widerspruch zur Messung daneben.
        _g_mb = min(int(_stv.get("waechter_mb") or 0), max(0, _belegt - _w_mb))
        _d_mb = min(int(_stv.get("dienst_mb") or 0),
                    max(0, _belegt - _w_mb - _g_mb))
        _rest = max(0, _belegt - _w_mb - _g_mb - _d_mb)
        _res_seg = min(res, _gem_frei)
        _frei_seg = max(0, _gem_frei - _res_seg)
        # WORKER, NICHT PLATZ: die Zahl ist der Anteil des EINEN Worker-Prozesses
        # mit all seinen Rechenstraengen und Decoder-Kindern, nicht der eines
        # Analyseplatzes. „n × Platz" waere hier die falsche Einheit.
        # .535: die Zahl kommt aus der MESSTABELLE — derselben, aus der die
        # Leiter plant. Was die Prozess-Sonde daneben misst, steht in /health
        # (`messung`) als Vergleich; die Leiste zeigt den HAUSHALT, und der
        # wird aus der Tabelle geplant. Zwei verschiedene Zahlen fuer dieselbe
        # Sache auf einer Seite waeren wieder die alte Falle.
        _lbl_w = (f'{t("gpu.worker_prozess")} ({t("gpu.q.tabelle")})' if _w_mb
                  else t("gpu.worker_unbekannt"))
        b1 = _riegel([("w", _w_mb, _lbl_w),
                      ("g", _g_mb, f'{n_waechter} × {t("gpu.waechter")} '
                                   f'({t("gpu.q.posten")})'),
                      ("d", _d_mb, f'{t("gpu.dienst")} ({t("gpu.q.posten")})'),
                      ("b", _rest, t("gpu.belegt_andere")),
                      ("f", _frei_seg, t("gpu.frei")),
                      ("r", _res_seg, t("gpu.reserve"))], gesamt)
        _teile = []
        if _w_mb:
            _teile.append(f'<span class="lg w"></span>'
                          f'{html.escape(t("gpu.worker_prozess"))} ({_mb(_w_mb)}, '
                          f'{html.escape(t("gpu.q.tabelle"))})')
        elif _w_grund and _w_grund != "kein_worker":
            # „kein_worker" ist kein Befund, sondern Ruhe: dann gibt es nichts
            # zu beschriften. Der Satz gilt dem LAUFENDEN Prozess, dessen
            # Anteil die Karte nicht hergibt.
            _teile.append(f'<span class="lg w"></span>'
                          f'{html.escape(t("gpu.worker_unbekannt"))}')
        if _g_mb:
            _teile.append(f'<span class="lg g"></span>{n_waechter} × '
                          f'{html.escape(t("gpu.waechter"))} ({_mb(_g_mb)}, '
                          f'{html.escape(t("gpu.q.posten"))})')
        if _d_mb:
            _teile.append(f'<span class="lg d"></span>'
                          f'{html.escape(t("gpu.dienst"))} ({_mb(_d_mb)}, '
                          f'{html.escape(t("gpu.q.posten"))})')
        if _rest:
            _teile.append(f'<span class="lg b"></span>'
                          f'{html.escape(t("gpu.belegt_andere"))} ({_mb(_rest)})')
        _teile.append(f'<span class="lg f"></span>{html.escape(t("gpu.frei"))} '
                      f'({_mb(_frei_seg)}, {html.escape(t("gpu.q.gemessen"))})')
        _teile.append(f'<span class="lg r"></span>'
                      f'{html.escape(t("gpu.reserve"))} ({_mb(_res_seg)}, '
                      f'{html.escape(_q_res)})')
        speicher = (
            f'<h3>{html.escape(t("gpu.balken.speicher"))}</h3>{b1}'
            f'<p class="gpuzeile">' + " &nbsp; ".join(_teile) + '</p>'
            f'<p class="gpuzeile klein">'
            f'{html.escape(t("gpu.leiste_gemessen"))}</p>')
    else:
        # OHNE gemessenen Frei-Wert bleibt es bei der Posten-Rechnung — dann ist
        # sie das Beste, was es gibt, und die Seite sagt mit `gpu.messwerte`
        # darunter ohnehin, dass es Richtwerte sind.
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
            f'<span class="lg d"></span>{html.escape(t("gpu.dienst"))} '
            f'({_mb(b["dienst_mb"])}) &nbsp; '
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
        # .535 (g1): WIEVIEL NOCH GEHT, SAGT DIE LEITER — nicht die Anker-Formel.
        # `worker_noch_moeglich` rechnet mit den Stuetzwerten einer fremden Karte
        # und einem Platz-je-Prozess-Modell; seit .532 vergibt der Dienst die
        # Plaetze aber aus der STRANGZAHL der Leiter (dieselbe Quelle wie
        # /health). Im Feld standen deshalb zwei verschiedene Zahlen auf einer
        # Seite. Wo die Leiter etwas sagt, gilt sie; sonst bleibt die Formel.
        if _stv and _stv.get("n"):
            moeglich = max(0, int(_stv["n"]) - int(n_worker or 0))
        else:
            moeglich = _gb.worker_noch_moeglich(gesamt, n_waechter, n_worker)
        eng = (t("gpu.engpass.speicher") if b["engpass"] == "speicher"
               else t("gpu.engpass.rechenzeit"))
        urteil = (f'<p class="ok">{html.escape(eng)} '
                  f'{html.escape(t("gpu.noch_moeglich", n=moeglich))}</p>')

    # .534 (B10): auf Karten-Backends kommt die Platzzahl aus der Leiter. Dann
    # steht hier deren Aussage — und die Browser-Vorschau bekommt BEWUSST keine
    # Daten mehr: sie rechnete „passt / passt nicht" nach der alten
    # Platz-je-Prozess-Formel und haette dem Nutzer weiter geraten, einen
    # Live-Waechter abzuschalten, wo das nichts aendert.
    _lsatz, _js = None, {"mb_worker": _gb.VRAM_JE_WORKER_MB,
                         "frei": max(0, b["frei_mb"]), "jetzt": n_worker}
    if (straenge or {}).get("mass") == "vram":
        _n = (straenge or {}).get("n")
        _aktiv = (straenge or {}).get("analyse_plaetze_aktiv") or _n
        # .536 B6: DER SATZ NENNT NUR NOCH RECHENSTRAENGE. Bis .535 stand hier
        # „Der Dienst faehrt 4 Plaetze = 4 Rechenstraenge" — zwei Namen fuer
        # dieselbe Sache, seit R7 auch noch fuer dieselbe ZAHL. Die Gleichung
        # war die Uebergangs-Formulierung aus .534, als die Plaetze der
        # Strangzahl erst nachgefuehrt wurden; jetzt SIND sie die Strangzahl
        # (`Service._plaetze_an_straenge`), und die Seite stellt seit .536 genau
        # eine Groesse ein. Die Plaetze-Woerter (`gpu.platz_ez/mz`) sind damit
        # ersatzlos entfallen — auf der GPU-Seite kommt „slot" nur noch im
        # Wartetext des ANALYSE-Kontos vor, wo es eine andere Sache meint.
        try:
            _ov = int((straenge or {}).get("analyse_plaetze") or 0)
        except (TypeError, ValueError):
            _ov = 0
        if _n:
            # EINZAHL IST KEINE SONDERBEHANDLUNG, sie ist der Normalfall (.534er
            # Abnahme-Befund: „1 Plaetze = 1 Rechenstraenge"). Das Wort kommt
            # deshalb aus dem Textwerk, je Zahl einzeln gewaehlt. Die Schluessel
            # stehen hier WOERTLICH, nicht als Variable: die Sprach-Deckung des
            # Gates liest den Code, und ein Schluessel, den sie nicht sieht,
            # gilt ihr als tot (und ist dann auch keiner mehr).
            _w_strang = (t("gpu.strang_ez") if int(_n or 0) == 1
                         else t("gpu.strang_mz"))
            # AUSSTEHENDER WECHSEL (.534 Abnahme-Befund B-5): die Vergabestelle
            # stellt erst beim naechsten Worker-Start um, und ohne diesen Zweig
            # nennt der Satz eine Zahl, die noch nicht gilt. Gemessen wird er an
            # der Kapazitaet der Vergabestelle — die ist seit .536 die
            # Strangzahl, ALSO nur dann, wenn kein Experten-Override im Spiel
            # ist: der deckelt die Plaetze UNTER die Straenge, dauerhaft und
            # gewollt, und ein „der Dienst stellt um" waere dort schlicht
            # falsch. Der Override meldet sich ohnehin selbst im Log.
            if _ov <= 0 and _aktiv and int(_aktiv) != int(_n):
                _w_jetzt = (t("gpu.strang_ez") if int(_aktiv or 0) == 1
                            else t("gpu.strang_mz"))
                _lsatz = t("gpu.leiter_plaetze_wartet", n=_n, jetzt=_aktiv,
                           strang=_w_strang, strang_jetzt=_w_jetzt)
            else:
                _lsatz = t("gpu.leiter_plaetze", n=_n, strang=_w_strang)
            _js = None
    # .536 B5: WO DIE LEITER SPRICHT, GILT IHRE ZAHL — auch beim Vorschlag hinter
    # „automatisch". `vorschlag_geklemmt` rechnet mit den Stuetzwerten einer
    # fremden Karte und einem Platz-je-Prozess-Modell; der Vorschlag kaeme dann
    # kleiner heraus als das, was die Automatik wirklich baut, und die Seite
    # naennte zwei Zahlen fuer dieselbe Sache (der Fehler, den .535 g1 an der
    # Speicherleiste abgestellt hat). `passt_max` bleibt unveraendert — die Zeile
    # dazu steht ohnehin nur, wo die Leiter schweigt.
    regler = _regler(vorschlag if _stv else vor_geklemmt,
                     kapazitaet_jetzt, auto, kind,
                     laeuft_mit=n_worker, passt_max=passt_max,
                     budget_js=_js, leiter_satz=_lsatz, legacy=legacy)
    # .536 B5.2: HIER lebt der Messsatz „gleichzeitige Analysen" weiter. Aus dem
    # Reglertext ist er heraus, weil der Regler seit R7 Rechenstraenge stellt und
    # die gemessene Zahl eine ANDERE Groesse meint (Bauplan B5.2); bei den
    # Messwerten steht sie als das, was sie ist — eine Messung.
    quelle = (f'<p class="gpuzeile klein">'
              f'{html.escape(t("gpu.messwerte", worker=_gb.VRAM_JE_WORKER_MB, erster=_gb.VRAM_ERSTER_WAECHTER_MB, weiterer=_gb.VRAM_JE_WEITEREM_WAECHTER_MB, hw=kind, n=int(mess_n or vorschlag or 1)))}'
              f'</p>')
    # REIHENFOLGE (User 04.09.: „damit der User nicht nach unten scrollen muss, um
    # etwas einzustellen"): zuerst das, was er TUN kann und wissen muss — Zustand,
    # Urteil, Regler. Die Grafiken kommen darunter und liegen NEBENEINANDER statt
    # langgezogen untereinander; sie erklaeren, sie werden nicht bedient.
    oben = (f'<div class="gpu-oben">'
            f'<div class="gpu-links">{urteil}'
            f'{_laeuft(n_worker, n_waechter, belegt, klassen)}{zu_live}</div>'
            f'<div class="gpu-rechts">{regler}</div></div>')
    balken = (f'<div class="gpu-zwei">'
              f'<div class="gpu-sp">{speicher}</div>'
              f'<div class="gpu-sp">{rechen}</div></div>')
    return (kopf + oben + balken + last + quelle + "</div>"
            + _JS(t("gpu.vorschau"), t("gpu.neustart_frage"), t("gpu.nicht_erreichbar"),
                            t("gpu.vorschau_zu_wenig"), t("gpu.speichern_gesperrt")))
