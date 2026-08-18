"""verifyd Web-UI-Geruest (Plan v1.0 AP3): gemeinsames Layout, Navigation, Zustaende.
Kein Framework, keine CDNs — Server rendert Strings, Statik liegt in diesem Ordner."""
import html
import os

# Cache-Stempel fuer Statik (User-Fund 04.08.: Browser hielt nach einem
# Hotfix-Deploy DERSELBEN Version das alte app.js fest — Knoepfe ohne
# Funktion). Datei-Stand statt Versionsnummer: aendert sich mit jedem Build.


def _statik_stempel():
    st = []
    for n in ("app.js", "style.css"):
        p = os.path.join(os.path.dirname(__file__), n)
        try:
            st.append(str(int(os.path.getmtime(p))))
        except OSError:
            st.append("0")
    return "-".join(st)


_STATIK_STEMPEL = _statik_stempel()

# Zwei Ebenen statt elf gleichrangiger Reiter (User-Entscheid 25.07.). Grundlage ist die
# bewertete Navigations-Untersuchung: von drei Entwuerfen gewann dieser
# (7/5/8) und zerschneidet als einziger keine der 21 gemessenen Arbeitssitzungen.
# WICHTIG: alle Adressen bleiben unveraendert — Lesezeichen und Deep-Links brechen nicht, es
# aendert sich nur, wie sie gruppiert angezeigt werden.
#   Activity = was passiert ist (Zeitachse) · People = Identitaeten und ihre Referenzbilder
#   Settings = wie sich das System verhalten soll · System = wie es dem Dienst geht
# "Review" verschwindet als Wort: es meinte an drei Stellen Verschiedenes. Der Unterreiter heisst
# "To label", wie die Ueberschrift der Seite ohnehin schon lautet.
# "Settings" heisst als Unterreiter "Advanced": von den Werten dort ist die Haelfte keine
# Detection-Einstellung (szenario_gap_min, clip_retention_d, frigate_sync, debug …).
NAV = [
    ("Activity", [("/heute", "Today"), ("/ereignisse", "Events"), ("/offen", "To label")]),
    # .220 (User 16.08., Mockup-Abnahme): der Gesichts-Bereich "eingedampft" —
    # People + Face-Learn verschmelzen zu FACES mit Kachel-Startseite
    # (Avatar-Leiste, gefuehrter Lern-Fluss). Easy sieht nur die Startseite,
    # Expert behaelt alle Detail-Blaetter als Unterreiter (NUR_EXPERT_BLAETTER
    # blendet aus, nichts wird geloescht; Erreichbarkeit fuer Easy laeuft ueber
    # die Kachel-Knoepfe — dasselbe Muster wie bei Configuration).
    ("Faces",    [("/faces", "Faces"),
                  ("/gesichter", "Known"), ("/unbekannte", "Unknown"),
                  ("/qualitaet", "Quality")]),
    # .254 (User 17.08.: "ich vermisse den Knopf fuer das Lernen oben im
    # Menue, er gehoert da rein"): Learn kehrt als Hauptbereich zurueck —
    # Startseite ist der NEUE gefuehrte Lernfluss (.246); Anchors/Suggestions
    # ziehen aus Faces mit (Expert-Unterreiter). Person learn bleibt bewusst
    # unter Person (fachliche Heimat, .220-Entscheid ungebrochen).
    ("Learn",    [("/lernlauf", "Learning run"),
                  ("/lernlauf/anker", "Anchors"),
                  ("/lernen", "Suggestions")]),
    # Person als EIGENER Hauptbereich neben People (User 04.08. abend):
    # People zeigt die GESICHTER, Person die KOERPER-Bilder je Person.
    # Z8 (konzept_frames.md §7): "Judged images" = Kontroll-Speicher der
    # beurteilten Bilder je Durchgang. Sichtbar auch im Schlank-Modus, weil die
    # Seite dort erklaert, was der Schalter tut — ein Reiter, der je nach Config
    # verschwindet, ist schwerer zu finden als einer, der sich erklaert.
    ("Person",   [("/person", "Body images"),
                  ("/person/kontrolle", "Judged images"),
                  ("/person/modell", "Model status"),
                  # .220: Person learn zieht aus dem aufgeloesten Learn-Bereich
                  # hierher — der Koerper-Lernlauf gehoert fachlich zu Person.
                  ("/personlauf", "Person learn")]),
    # Vision detect zwischen Person und Area (konzept_vision.md v2 §4): der
    # dritte Erkennungspfad. V1 zeigt Verbindung + Test; Galerie-Wizard und
    # Status folgen. Der Reiter steht auch AUS sichtbar da — eine Seite, die
    # erklaert, was sie tut, ist leichter zu finden als eine, die je nach
    # Config verschwindet (dieselbe Begruendung wie bei "Judged images").
    ("Vision",   [("/vision", "Vision detect")]),
    # Live direkt neben Vision (live_reiter_bauplan.md §2.1, User woertlich).
    # Der Reiter steht auch sichtbar da, wenn kein Waechter laeuft — dieselbe
    # Begruendung wie bei "Vision detect": eine Seite, die erklaert, was sie
    # tut, ist leichter zu finden als eine, die je nach Config verschwindet.
    # .200 (Fix 6, Usersicht-Review): die Ergebnis-Seite der Waechter war nur
    # ueber die Today-Seitenleiste erreichbar — "und wo sehe ich jetzt, was er
    # gesehen hat?" hatte keinen Menue-Weg.
    ("Live",     [("/live", "Live watchers"), ("/live_alerts", "Live alerts")]),
    # Areas war .83-.221 ein eigener Hauptbereich; .222 (User): "kein extra
    # Punkt mehr" — das Blatt lebt als Expert-Unterreiter von Configuration,
    # Easy erreicht es ueber die Areas-Kachel der Property-set-up-Reihe.
    # .83-.219 stand hier "Learn" als eigener Hauptbereich; .220 loest ihn auf:
    # Face learn/Anchors leben unter FACES, Person learn unter PERSON.
    # .137: der Frigate-Abgleich bekam einen EIGENEN Hauptbereich (User 06.08.).
    # .216 (User 16.08.): der Bereich heisst "Frigate" und beginnt mit einer
    # Kachel-Startseite im /erkennung-Muster (Connection/Cameras/Sync/FR-Zustand);
    # die Sync-Seite bleibt als Unterreiter, in der Easy-Sicht ausgeblendet
    # (die Kachel fuehrt hin — dieselbe Mechanik wie bei Configuration).
    ("Frigate", [("/frigate", "Frigate"),
                 ("/sync_auswahl", "Frigate sync")]),
    # .207 (User 16.08.: die Vier-Saeulen-Seite ist "die Startseite fuer die
    # Konfiguration"): /erkennung steht VORN — der Settings-Klick oben landet
    # direkt dort (Abschnitts-Link = kinder[0]). Die uebrigen Blaetter sind
    # Expert-Sicht (NUR_EXPERT_BLAETTER, Easy blendet ihre Unterreiter aus).
    # .210 (User 16.08.): der Reiter heisst "Configuration", nicht "Settings".
    ("Configuration", [("/erkennung", "Recognition"),
                  ("/kameras", "Cameras"), ("/benachrichtigungen", "Notifications"),
                  ("/areas", "Areas"),          # .222: aus der Hauptnav hierher
                  # .189 (User 13.08.: "vier Menuepunkte"): die Erkennungskette
                  # als EIGENES Blatt VOR Advanced — sie ist Verhaltens-Config
                  # erster Klasse, kein versteckter Tabellen-Parameter; seit
                  # .207 Teil der Expert-Sicht (der User-Menue-Entscheid bleibt
                  # dort erhalten, Easy blendet nur aus).
                  ("/kette", "Recognition chain"),
                  ("/konfiguration", "Advanced")]),
    # Recognition test als EIGENER Einstieg neben System (konzept_vision.md v2 §4,
    # User-Entscheid 08.08.): die Seite prueft einen Durchgang ueber ALLE DREI
    # Wege (Gesicht/Koerper/Vision) und ist damit kein Vision-Detail. EINE Seite,
    # zwei Einstiege — der Vision-Reiter verlinkt dieselbe Adresse.
    ("Recognition test", [("/erkennungstest", "Recognition test")]),
    ("System",   [("/system", "System")]),
]
# Blattseiten ohne eigenen Reiter ihrem Abschnitt zuordnen, damit oben trotzdem der richtige
# Bereich leuchtet (heute leuchtet auf /setup gar nichts).
BLATT = {"/setup": "/kameras", "/aehnliche": "/gesichter", "/event": "/heute", "/auftritte": "/heute"}

# .207 (User 16.08.: "wenn der Schalter auf Basis ist, erscheint dieses Bild und
# nicht mehr die anderen zusaetzlich"): Blaetter, deren UNTERREITER nur im
# Expert-Modus sichtbar sind (CSS-Klasse nur-expert, body.easy versteckt).
# Nur ausgeblendet, nie gesperrt — die Seiten bleiben per URL erreichbar.
NUR_EXPERT_BLAETTER = {"/kameras", "/benachrichtigungen", "/kette", "/konfiguration",
                       "/sync_auswahl", "/areas",
                       # .220: die Faces-Detail-Blaetter — Easy fuehrt ueber
                       # die Kachel-Knoepfe der Startseite dorthin. .254:
                       # /lernlauf ist RAUS aus der Menge (eigener Learn-
                       # Hauptbereich, sein Unterreiter darf in Easy leuchten).
                       "/gesichter", "/unbekannte", "/lernen",
                       "/lernlauf/anker"}   # .273: /qualitaet ist EASY (Bestands-QS-Knopf)

# Die beiden Galerie-Links ("Review gallery", "Strangers gallery") sind am 25.07. entfernt worden:
# erzeugt wurden die Seiten von prototypes/backtest.py, das in keinem Image liegt. Fuer JEDE
# Neuinstallation standen damit auf JEDER Seite zwei Links, die dauerhaft eine nackte
# 404-Textzeile lieferten. Ein Link, der bei niemandem ausser dem Entwickler funktioniert,
# gehoert nicht in die Fusszeile.
# #53 Update-Hinweis: verifyd.update_check() setzt das nach jedem taeglichen Check
# ({"tag": "v0.1.0.x", "url": ...} oder None). Prozess-Zustand, Quelle state/update_check.json —
# das Layout bleibt zustandslos und muss nichts nachladen.
UPDATE_INFO = None

FUSS = ('<a href="/log">Service log</a> · '
        '<a href="https://github.com/BennoBaer-dev/suslik" target="_blank" rel="noopener noreferrer">Docs</a> · '
        '<a href="/health">health</a>')


def layout(titel, aktiv, inhalt, banner=None, refresh=None):
    """Seiten-Huelle: Nav + optionaler Warn-Banner + Inhalt + Fusszeile.
    refresh=N laedt die Seite alle N Sekunden neu (offener Tab bleibt aktuell)."""
    # Aktiven Abschnitt aus dem Pfad ableiten — die Seiten uebergeben weiterhin ihren eigenen
    # Pfad, keine Seite muss etwas ueber die Gruppierung wissen.
    a = BLATT.get(aktiv, aktiv)
    abschnitt = next((t for t, kinder in NAV if any(p == a for p, _ in kinder)), NAV[0][0])
    nav = "".join(
        f'<a href="{kinder[0][0]}"{" class=aktiv" if t == abschnitt else ""}>{t}</a>'
        for t, kinder in NAV)
    kinder = next((k for t, k in NAV if t == abschnitt), [])
    # Zweite Ebene nur zeigen, wenn es dort mehr als eine Seite gibt (System hat nur sich selbst).
    # Unterreiter nur markieren, wenn die Seite WIRKLICH die des Reiters ist (Plan-QS M7):
    # BLATT bildet /setup auf /kameras ab, damit oben "Settings" leuchtet — aber der
    # Unterreiter "Cameras" leuchtete dadurch MIT, obwohl man gar nicht auf /kameras ist.
    # Der Abschnitt kommt aus dem gemappten Pfad (a), der Unterreiter aus dem echten (aktiv).
    def _u_klasse(p):
        k = (["aktiv"] if p == aktiv else []) \
            + (["nur-expert"] if p in NUR_EXPERT_BLAETTER else [])
        return f' class="{" ".join(k)}"' if k else ""
    unter = ("" if len(kinder) < 2 else
             '<div class="subnav"><div class="inner">' + "".join(
                 f'<a href="{p}"{_u_klasse(p)}>{html.escape(n)}</a>'
                 for p, n in kinder) + "</div></div>")
    ver = os.environ.get("SUSLIK_VERSION", "")   # feste Image-Version (leer im rohen dev-Lauf)
    # Issue #24 (Tokn59, 18.08.): die VOLLE installierte Variante zeigen
    # ('0.1.0.X-gpu') — SUSLIK_VARIANT steckt seit den Varianten-Builds im
    # Image; im rohen dev-Lauf fehlen beide, dann bleibt der Kopf nackt.
    _vari = os.environ.get("SUSLIK_VARIANT", "")
    if ver and _vari:
        ver = f"{ver}-{_vari}"
    # Update-Marke (#53): fest im Kopf, aber leise — ein kleiner Link neben der Version,
    # kein Banner, kein Blinken (User-Vorgabe "fest auf der Startseite, nicht zu aufdringlich").
    upd = ""
    if UPDATE_INFO and UPDATE_INFO.get("tag"):
        upd = (f' <a class="upd" href="{html.escape(UPDATE_INFO.get("url") or "")}" target="_blank" '
               f'rel="noopener noreferrer" title="A newer suslik version is available on GitHub">'
               f'update {html.escape(UPDATE_INFO["tag"])}</a>')
    b = f'<div class="banner">{html.escape(banner)}</div>' if banner else ""
    r = f'<meta http-equiv="refresh" content="{int(refresh)}">' if refresh else ""
    mark = ('<svg viewBox="0 0 32 32" fill="none" aria-hidden="true">'
            '<rect x="2.5" y="2.5" width="27" height="27" rx="8" stroke="var(--accent)" stroke-width="2.2"/>'
            '<circle cx="16" cy="13.5" r="4" stroke="var(--accent)" stroke-width="2.2"/>'
            '<path d="M9 24c1.6-3.4 4-5 7-5s5.4 1.6 7 5" stroke="var(--accent)" stroke-width="2.2" stroke-linecap="round"/></svg>')
    # Der Umschalter trug bisher nur das Zeichen ◐ mit einem Tooltip — der User hat ihn nicht
    # gefunden ("sollten wir nicht darauf hinweisen, dass es beide gibt"). Ein Bedienelement,
    # das der Betreiber uebersieht, existiert praktisch nicht. Jetzt mit sichtbarer Beschriftung,
    # die den ZIELzustand nennt (nicht den aktuellen — sonst raet man, was der Klick tut).
    # Easy/Expert-Schalter (.204, User 15.08.: "links neben Live, deutlich erkennbar",
    # Optik analog Theme-Knopf): Zwei-Segment-Pille zeigt BEIDE Modi, der aktive traegt
    # die Akzentfarbe — Zustand und Klickziel in einem, nichts zum Raten (◐-Lehre oben).
    # AKTUELL NUR DER SCHALTER: Modus wird gemerkt (localStorage, analog Theme) und
    # steht als body-Klasse "easy" bereit; die Seiten ziehen ihre Easy-Ansichten
    # Schritt fuer Schritt nach (stand.md Easy-Umbau).
    rechts = ('<span class="rechts">'
              '<span class="modus" id="ui-modus" '
              'title="Easy shows the core pages — Expert shows everything. '
              'Nothing is deleted, Easy only hides.">'
              '<button type="button" data-m="easy">Easy</button>'
              '<button type="button" data-m="expert">Expert</button></span>'
              '<span class="live"><span class="d"></span>Live</span>'
              '<button class="toggle" id="theme-toggle" '
              'title="Switch between light and dark" aria-label="Switch colour theme">'
              '<span class="tg-ico" aria-hidden="true">◐</span>'
              '<span class="tg-txt">Theme</span></button></span>')
    # Themenwahl (25.07.): OHNE eigene Wahl folgt die Oberflaeche dem Betriebssystem. Vorher war
    # Dunkel fest voreingestellt — User: "es ist ja alles sehr dunkel und faende ich nicht so
    # willkommen". Wer den Umschalter benutzt, ueberstimmt das System dauerhaft; das OS ueberschreibt
    # eine ausdrueckliche Wahl NIE. Inline und vor dem Stylesheet, damit nichts kurz aufblitzt.
    themejs = ('<script>try{var t=localStorage.getItem("vd-theme");'
               'if(!t&&window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches)t="light";'
               'if(t)document.documentElement.setAttribute("data-theme",t);}catch(e){}</script>')
    return ("<!doctype html><meta charset=utf-8>" + r +
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(titel)} — suslik{(' ' + ver) if ver else ''}</title>"
            f'<link rel="stylesheet" href="/static/style.css?v={_STATIK_STEMPEL}">'
            + themejs +
            f'<script src="/static/app.js?v={_STATIK_STEMPEL}" defer></script>'
            # Beide Leisten in EINEN klebenden Block (Fund der Nachpruefung 25.07.): einzeln
            # klebend brauchte die zweite Ebene einen Festwert fuer die Hoehe der ersten, und der
            # wurde falsch, sobald die erste umbrach — s. .kopf in style.css.
            f'<div class="kopf"><nav><div class="inner"><span class="marke">{mark}suslik'
            f'{f" <small>{html.escape(ver)}</small>" if ver else ""}{upd}</span>{nav}{rechts}</div></nav>'
            f"{unter}</div>"
            f"<main>{b}{inhalt}</main>"
            f"<footer>{FUSS}</footer>")


def leer(text, hinweis=""):
    """Definierter Leerzustand (AP3-Abnahmekriterium)."""
    h = f"<br><small>{html.escape(hinweis)}</small>" if hinweis else ""
    return f'<div class="leer"><b>{html.escape(text)}</b>{h}</div>'


def whatsnew_block():
    """Task #16 (User-Vorgabe 01.08.): What's-new-Box auf der Startseite — die letzten
    Release-Highlights aus der EINEN Quelle core/highlights.py. Eingeklappt die
    ersten 3, auf Klick alle (Deckel 10), wegklickbar je Version. Der Merker
    liegt im localStorage wie die Theme-Wahl (kein Server-Zustand); die Box
    startet hidden und zeigt sich erst, wenn der Merker NICHT passt — wer sie
    weggeklickt hat, sieht sie bis zur naechsten Version nie aufblitzen."""
    from core.highlights import BETONT, HIGHLIGHTS   # import-frei, kein Zyklus
    eintraege = [(v, t) for v, its in HIGHLIGHTS for t in its][:10]
    if not eintraege:
        return ""
    neueste = html.escape(HIGHLIGHTS[0][0], quote=True)
    li, letzte_v = [], None
    for i, (v, txt) in enumerate(eintraege):
        chip = f'<span class="wn-v">{html.escape(v)}</span>' if v != letzte_v else ""
        letzte_v = v
        # .168: ein markierter Eintrag wird fett und in Warnfarbe gesetzt (der
        # Vorab-Hinweis eines Releases). Die Marke wird abgenommen, der Text
        # bleibt escaped — hier kommt kein Markup aus der Quelle durch.
        betont = txt.startswith(BETONT)
        if betont:
            txt = txt[len(BETONT):]
        kl = " ".join(x for x in (("wn-mehr" if i >= 3 else ""),
                                  ("wn-betont" if betont else "")) if x)
        li.append(f'<li{f' class="{kl}"' if kl else ""}>{chip}'
                  + html.escape(txt) + "</li>")
    mehr = len(eintraege) - 3
    toggle = (f'<button class="wn-toggle" data-n="{mehr}">Show all ({len(eintraege)})</button>'
              if mehr > 0 else "")
    return (
        f'<div class="wnblock" id="wnblock" hidden><div class="wn-kopf">'
        f'<span class="wn-t">What&#8217;s new</span>'
        f'<button class="wn-x" title="Hide until the next version" aria-label="Dismiss">&times;</button></div>'
        f'<ul class="wn-liste">{"".join(li)}</ul>{toggle}</div>'
        '<script>(function(){var b=document.getElementById("wnblock");if(!b)return;'
        f'var v="{neueste}";'
        'try{if(localStorage.getItem("vd-wn-seen")===v){b.remove();return;}}catch(e){}'
        'b.hidden=false;var t=b.querySelector(".wn-toggle");'
        'if(t)t.onclick=function(){var o=b.classList.toggle("wn-open");'
        't.textContent=o?"Show fewer":"Show all ("+(3+parseInt(t.dataset.n,10))+")";};'
        'b.querySelector(".wn-x").onclick=function(){'
        'try{localStorage.setItem("vd-wn-seen",v)}catch(e){}b.remove();};})();</script>')


def update_block():
    """#53: sachlicher, DEUTLICHER Hinweis-Block fuer die Startseite (User 26.07.: 'exklusiv
    dargestellt … sachlich hingewiesen, aber schon deutlich' — kein Blinken, kein Erschlagen).
    Ergaenzt die leise Kopf-Marke; leer, wenn kein Update bekannt ist."""
    if not (UPDATE_INFO and UPDATE_INFO.get("tag")):
        return ""
    tag = html.escape(UPDATE_INFO["tag"])
    url = html.escape(UPDATE_INFO.get("url") or "")
    return (f'<div class="updblock"><span class="updb-t">Update available</span>'
            f'<span class="updb-x">A newer suslik image (<b>{tag}</b>) is on GitHub — '
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">release notes</a>. '
            f'Pull the new image and restart to update; your data and settings are kept.</span></div>')
