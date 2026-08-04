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
    ("People",   [("/gesichter", "Known"), ("/unbekannte", "Unknown"),
                  ("/lernen", "Suggestions"), ("/qualitaet", "Quality")]),
    # Person als EIGENER Hauptbereich neben People (User 04.08. abend):
    # People zeigt die GESICHTER, Person die KOERPER-Bilder je Person.
    ("Person",   [("/person", "Body images"),
                  ("/person/modell", "Model status")]),
    # Areas als EIGENER Hauptbereich zwischen People und Learn (Design-Entscheid):
    # dort liegen Sicht-Einstieg UND Konfiguration (anlegen/loeschen/zuweisen).
    ("Areas",    [("/areas", "Areas")]),
    # .83: Learn als EIGENER Hauptbereich — Kernfunktion, nicht
    # laenger ein Anhaengsel der People-Seite.
    # PE1 (stufe2.md): Learn geteilt in Face learn (bisheriger Lernlauf)
    # und Person learn (Koerper-Strang) — User-Entscheid 04.08.
    ("Learn",    [("/lernlauf", "Face learn"), ("/lernlauf/anker", "Anchors"),
                  ("/personlauf", "Person learn")]),
    ("Settings", [("/kameras", "Cameras"), ("/benachrichtigungen", "Notifications"),
                  ("/konfiguration", "Advanced")]),
    ("System",   [("/system", "System")]),
]
# Blattseiten ohne eigenen Reiter ihrem Abschnitt zuordnen, damit oben trotzdem der richtige
# Bereich leuchtet (heute leuchtet auf /setup gar nichts).
BLATT = {"/setup": "/kameras", "/aehnliche": "/gesichter", "/event": "/heute", "/auftritte": "/heute"}

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
    unter = ("" if len(kinder) < 2 else
             '<div class="subnav"><div class="inner">' + "".join(
                 f'<a href="{p}"{" class=aktiv" if p == aktiv else ""}>{html.escape(n)}</a>'
                 for p, n in kinder) + "</div></div>")
    ver = os.environ.get("SUSLIK_VERSION", "")   # feste Image-Version (leer im rohen dev-Lauf)
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
    rechts = ('<span class="rechts"><span class="live"><span class="d"></span>Live</span>'
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
    from core.highlights import HIGHLIGHTS   # import-frei, kein Zyklus
    eintraege = [(v, t) for v, its in HIGHLIGHTS for t in its][:10]
    if not eintraege:
        return ""
    neueste = html.escape(HIGHLIGHTS[0][0], quote=True)
    li, letzte_v = [], None
    for i, (v, txt) in enumerate(eintraege):
        chip = f'<span class="wn-v">{html.escape(v)}</span>' if v != letzte_v else ""
        letzte_v = v
        li.append(f'<li{" class=wn-mehr" if i >= 3 else ""}>{chip}{html.escape(txt)}</li>')
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
