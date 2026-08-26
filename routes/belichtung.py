"""routes/belichtung — Kalibrierseite der Belichtungsachse (analysen/
bauplan_belichtung.md, Phase 1b; User-Idee 26.08.: "Abgleich Helligkeit" als
Knopf in der Lern-Karte). Phase 1 hat die Achse gebaut (Luma je Kandidat,
Belichtungsklasse in der Reihung, zwei Config-Schluessel) — hier kann der
Betreiber die beiden Linien an EIGENEN Bildern einstellen, statt zwei nackte
Zahlen im Konfigurationsblatt zu raten.

Kontrakt wie alle routes-Module: reiner Renderer, Daten als Parameter, kein
Dienst-Import, kein Netz-/Store-Zugriff. Das Lesen der Anker
(core.lernlauf.anker_lesen) und das Ableiten der Grenzen
(verifyd.luma_grenzen_aus_cfg) macht der Handler; die AUSWAHL der gezeigten
Cluster rechnet dieses Modul selbst — pur, ohne IO (Muster
routes/lernanker.anker_seite, das seine Crops ebenso selbst ordnet und
deckelt).

DREI Ehrlichkeits-Regeln der Seite:
 1. Die gezeigte Reihenfolge ist die SERVER-Reihung: core.benennung._reihung
    mit den AKTUELLEN Grenzen — dieselbe Funktion, die die Empfehlung ordnet
    (benennung.empfehlen ruft sie ebenso ohne norm_latte). Kein Zweit-Sortierer.
 2. Die Regler-Reaktion im Browser ist eine VORSCHAU-SIMULATION und sagt das
    auch (Vorschau-Zeile, sobald ein Regler von der gespeicherten Zahl
    abweicht). Ihre Klassenbildung ist eine bewusst deklarierte Kopie von
    core.benennung._belichtungsklasse (Begruendung am JS-Block).
 3. Gespeichert wird ueber den BESTEHENDEN Konfigurations-Schreibweg: die
    beiden Regler tragen die cfg-<key>-IDs des Konfigurationsblatts und
    webui/app.js konfigSpeichern() schickt sie an POST /konfig. Kein zweiter
    Schreibweg, keine zweite Validierung — nach dem Neustart laedt die Seite
    neu und zeigt die ECHTE Server-Reihung mit den neuen Zahlen.

Sprach-Stufe: sichtbare Texte aus core/sprache.t(); die JS-Texte kommen
server-seitig als json.dumps(t(...)) in den Block (Muster routes/lernanker)."""
import html
import json

from core.benennung import _reihung, belichtungs_lage
from core.sprache import t

CLUSTER_MAX = 8            # Anzeige-Deckel: mehr Reihen liest niemand mehr durch
BILDER_JE_CLUSTER = 24     # je Reihe, in Server-Reihung — der Rest bleibt ungezeigt
LUMA_TRAEGER_MIN = 4       # unter vier gemessenen Bildern zeigt eine Reihe keine Spanne


def cluster_waehlen(saetze, luma_grenzen=None):
    """Anker-Datensaetze -> Anzeige-Cluster der Kalibrierseite (rein, kein IO).

    Genommen werden NUR Mitglieder MIT gemessener Luma: Altbestand (geerntet
    vor dem Einbau) traegt das Feld nicht und wuerde als "unbewertet" jede
    Reihe verwaessern — die Seite soll zeigen, was die Grenzen WIRKLICH tun.
    Cluster mit weniger als LUMA_TRAEGER_MIN solchen Bildern fallen raus,
    sortiert wird nach Luma-SPANNWEITE absteigend (die Reihe, in der hell und
    dunkel nebeneinanderliegen, sagt am meisten ueber die Linie aus).
    Verworfene Cluster bleiben draussen: ihre Crops sind geloescht, die Reihe
    zeigte lauter 404-Kaesten."""
    aus = []
    for s in saetze:
        if s.get("status") == "verworfen":
            continue
        lauf_id = str((s.get("lauf") or {}).get("lauf_id") or "")
        if not lauf_id:
            continue                       # ohne Lauf-Ordner gibt es keine Crop-URL
        mit = [m for m in (s.get("mitglieder") or [])
               if m.get("luma") is not None]
        if len(mit) < LUMA_TRAEGER_MIN:
            continue
        werte = []
        for m in mit:
            try:
                werte.append(float(m["luma"]))
            except (TypeError, ValueError):
                pass
        if len(werte) < LUMA_TRAEGER_MIN:
            continue
        # Angezeigt wird in der ECHTEN Server-Reihung (mit den aktuellen
        # Grenzen). Fuer die Vorschau bekommt jedes Bild zusaetzlich seinen
        # Platz in der LUMA-BLINDEN Reihung (dieselbe Funktion ohne Grenzen)
        # plus seine Lattenklasse — nur damit kann der Browser die Ordnung zu
        # anderen Reglerwerten NACHBILDEN: _reihung fuehrt (Latte,
        # Belichtung, Rest), und der blinde Rang IST der Rest-Rang innerhalb
        # der Latte. Ein Rang aus der klassen-gemischten Anzeige-Reihe waere
        # falsch (nachgemessen 26.08. im Browser: vier von fuenf
        # Regler-Stellungen wichen von der Server-Ordnung ab).
        blind = sorted(mit, key=lambda m: _reihung(m))
        rang_je = {id(m): i for i, m in enumerate(blind)}
        geordnet = sorted(mit, key=lambda m: _reihung(m, luma_grenzen=luma_grenzen))
        bilder = []
        for m in geordnet[:BILDER_JE_CLUSTER]:
            try:
                luma = int(round(float(m["luma"])))
            except (TypeError, ValueError):
                continue
            bilder.append({"datei": str(m.get("datei", "")).rsplit("/", 1)[-1],
                           "luma": luma, "rang": rang_je[id(m)],
                           "latte": _reihung(m)[0],
                           "lage": belichtungs_lage(m, luma_grenzen)})
        if not bilder:
            continue
        aus.append({"anker_id": str(s.get("anker_id") or ""),
                    "person": str(s.get("person") or ""),
                    "lauf_id": lauf_id,
                    "gesamt": len(mit),
                    "von": int(min(werte)), "bis": int(max(werte)),
                    "bilder": bilder})
    aus.sort(key=lambda c: (-(c["bis"] - c["von"]), c["anker_id"]))
    return aus[:CLUSTER_MAX]


def _stil():
    # Eigene Optik der Seite (Muster routes/lernanker: das Blatt bringt sein
    # CSS mit). Geometrie S9-tauglich: die Bild-REIHE ist bewusst EINE Zeile
    # (die Reihenfolge IST die Aussage) und scrollt auf schmalen Schirmen in
    # sich selbst — nie die Seite.
    return ('<style>.bx-reihe{display:flex;gap:5px;align-items:flex-start;'
            'overflow-x:auto;padding-bottom:4px}'
            '.bx-b{position:relative;display:block;flex:0 0 auto}'
            '.bx-b img{width:74px;height:74px;object-fit:cover;border-radius:6px;'
            'border:1px solid var(--border);display:block}'
            '.bx-b .bx-l{position:absolute;left:3px;bottom:3px;font-size:10px;'
            'line-height:1.4;padding:0 4px;border-radius:4px;'
            'background:var(--surface);color:var(--dim)}'
            '.bx-b.raus img{border-color:var(--crit);opacity:.55}'
            '.bx-b.raus .bx-l{background:var(--crit-bg);color:var(--crit)}'
            '.bx-kopf{display:flex;flex-wrap:wrap;gap:6px;align-items:baseline;'
            'font-size:13.5px;margin-bottom:4px}'
            '.bx-steuer{display:flex;flex-wrap:wrap;gap:14px;margin:10px 0 6px}'
            '.bx-steuer label{display:flex;align-items:center;gap:8px;'
            'flex:1 1 260px;font-size:14px}'
            '.bx-steuer input[type=range]{flex:1 1 120px;min-width:110px}'
            '.bx-steuer b{min-width:2.4em;text-align:right}'
            '.bx-vor{color:var(--warn)}'
            '.pill{display:inline-block;border:1px solid var(--rand,#8884);'
            'border-radius:10px;padding:0 8px;font-size:.85em}</style>')


def _wort(wert):
    return str(wert) if wert else t("belichtung.aus_wort")


def seite(saetze, luma_grenzen=None):
    """-> Seiten-INHALT (der Handler legt webui.layout darum).
    luma_grenzen = verifyd.luma_grenzen_aus_cfg(cfg) (None = Achse ganz aus).
    """
    lo = (luma_grenzen or {}).get("min") or 0
    hi = (luma_grenzen or {}).get("max") or 0
    try:
        lo, hi = int(lo), int(hi)
    except (TypeError, ValueError):        # Store-Altwert: lieber "aus" zeigen
        lo, hi = 0, 0                      # als die Seite an einer Zahl zerreissen
    cluster = cluster_waehlen(saetze, luma_grenzen)
    kopf = (f'<h2>{t("belichtung.titel")}</h2>')
    zurueck = ('<p class="sub"><a href="/lernlauf">'
               + t("belichtung.zurueck") + '</a></p>')
    if not cluster:
        # LEERE Datenlage (reiner Altbestand: kein Mitglied traegt luma) —
        # ehrlich erklaeren statt eine leere Flaeche zeigen. Die Werte
        # entstehen ab dem naechsten Lauf, nicht rueckwirkend (Bauplan §3:
        # kein Nachmessen von Altbestand im Renderer).
        return (_stil() + kopf
                + '<div class="card"><p>' + t("belichtung.leer_satz") + '</p>'
                + f'<p class="sub">{t("belichtung.leer_hinweis")}</p></div>'
                + zurueck)
    reihen, n_raus, n_ges = [], 0, 0
    for c in cluster:
        kacheln = []
        for b in c["bilder"]:
            n_ges += 1
            raus = bool(b["lage"])
            n_raus += 1 if raus else 0
            titel = (t("belichtung.lage_dunkel") if b["lage"] == "dunkel" else
                     t("belichtung.lage_hell") if b["lage"] == "hell" else
                     t("belichtung.lage_ok"))
            kacheln.append(
                f'<span class="bx-b{" raus" if raus else ""}" '
                f'data-luma="{b["luma"]}" data-rang="{b["rang"]}" '
                f'data-latte="{b["latte"]}" title="{html.escape(titel)}">'
                f'<img src="/lernlauf/crop/{html.escape(c["lauf_id"])}/'
                f'{html.escape(b["datei"])}" loading="lazy" alt="">'
                f'<span class="bx-l">{b["luma"]}</span></span>')
        reihen.append(
            '<div class="card"><div class="bx-kopf">'
            f'<b>{html.escape(c["anker_id"])}</b>'
            + (f'<span class="pill">{html.escape(c["person"])}</span>'
               if c["person"] else "")
            + '<span class="dim">'
            + t("belichtung.reihe_info", n=len(c["bilder"]),
                gesamt=c["gesamt"], von=c["von"], bis=c["bis"])
            + '</span></div>'
            f'<div class="bx-reihe">{"".join(kacheln)}</div></div>')
    steuer = (
        '<div class="bx-steuer">'
        f'<label>{t("belichtung.regler_min")} '
        f'<input type="range" id="cfg-reihung_luma_min" min="0" max="255" '
        f'step="1" value="{lo}"> <b id="bx-wmin">{html.escape(_wort(lo))}</b>'
        '</label>'
        f'<label>{t("belichtung.regler_max")} '
        f'<input type="range" id="cfg-reihung_luma_max" min="0" max="255" '
        f'step="1" value="{hi}"> <b id="bx-wmax">{html.escape(_wort(hi))}</b>'
        '</label></div>'
        f'<div class="sub">{t("belichtung.regler_hinweis")}</div>'
        f'<div id="bx-bilanz">{t("belichtung.bilanz", n=n_raus, m=n_ges)}</div>'
        '<div id="bx-vorschau" class="bx-vor" style="display:none">'
        + t("belichtung.vorschau") + '</div>'
        '<p><button class="gtb on" onclick="konfigSpeichern()">'
        + t("belichtung.knopf_speichern") + '</button> '
        '<span id="cfg-status" class="dim"></span></p>'
        # Bestaetigungszeile: was JETZT gilt — nach dem Speichern+Neustart
        # laedt konfigSpeichern die Seite neu, und diese Zeile traegt die
        # neuen Zahlen (samt der Reihen darunter, vom Server sortiert).
        + '<div class="dim">'
        + t("belichtung.jetzt", von=html.escape(_wort(lo)),
            bis=html.escape(_wort(hi)))
        + ('' if (lo or hi) else ' ' + t("belichtung.hinweis_aus"))
        + '</div>')
    # ---- VORSCHAU-SIMULATION (bewusst deklarierte Kopie) -------------------
    # klasse() unten ist die JS-Fassung von core.benennung._belichtungsklasse
    # (0 = belichtet ODER unbewertet, 1 = ausserhalb; je Seite gilt 0 = aus).
    # Sie ist die EINZIGE erlaubte Zweitstelle dieser Regel und ordnet NUR die
    # Vorschau. Sortiert wird nach (data-latte, Klasse, data-rang) — genau die
    # Reihenfolge der Achsen in _reihung: die Lattenklasse steht davor, der
    # blinde Rang traegt alles dahinter (Norm/Front/Sharp/Det/Name), und beides
    # aendert sich mit den Reglern nicht. Gerechnet wird nach dem Speichern
    # wieder auf dem Server; solange ein Regler abweicht, steht die
    # Vorschau-Zeile oben.
    js = ('<script>(function(){'
          'var mn=document.getElementById("cfg-reihung_luma_min"),'
          'mx=document.getElementById("cfg-reihung_luma_max"),'
          'wn=document.getElementById("bx-wmin"),'
          'wx=document.getElementById("bx-wmax"),'
          'bil=document.getElementById("bx-bilanz"),'
          'vor=document.getElementById("bx-vorschau");'
          f'var LO0={lo},HI0={hi},'
          'BILANZ=' + json.dumps(t("belichtung.bilanz", n="{n}", m="{m}")) + ','
          'AUS=' + json.dumps(t("belichtung.aus_wort")) + ';'
          'function klasse(l,lo,hi){if(isNaN(l))return 0;'
          'if(lo>0&&l<lo)return 1;if(hi>0&&l>hi)return 1;return 0;}'
          'function neu(){var lo=+mn.value,hi=+mx.value,raus=0,ges=0;'
          'wn.textContent=lo?lo:AUS;wx.textContent=hi?hi:AUS;'
          'var reihen=document.querySelectorAll(".bx-reihe");'
          'for(var i=0;i<reihen.length;i++){'
          'var kinder=[].slice.call(reihen[i].children);'
          'kinder.forEach(function(k){'
          'var kl=klasse(parseFloat(k.getAttribute("data-luma")),lo,hi);'
          'k._k=kl;ges++;if(kl)raus++;'
          'if(kl)k.classList.add("raus");else k.classList.remove("raus");});'
          'kinder.sort(function(a,b){'
          'return (+a.getAttribute("data-latte")-+b.getAttribute("data-latte"))'
          '||(a._k-b._k)||'
          '(+a.getAttribute("data-rang")-+b.getAttribute("data-rang"));});'
          'kinder.forEach(function(k){reihen[i].appendChild(k);});}'
          'bil.textContent=BILANZ.split("{n}").join(raus).split("{m}").join(ges);'
          'vor.style.display=(lo!==LO0||hi!==HI0)?"":"none";}'
          'mn.oninput=neu;mx.oninput=neu;'
          '})();</script>')
    return (_stil() + kopf
            + f'<div class="card"><p>{t("belichtung.satz")}</p>' + steuer
            + '</div>' + "".join(reihen) + zurueck + js)
