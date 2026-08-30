"""verifyd Web-UI-Geruest (Plan v1.0 AP3): gemeinsames Layout, Navigation, Zustaende.
Kein Framework, keine CDNs — Server rendert Strings, Statik liegt in diesem Ordner."""
import html
import json
import os

from core import sprache as _sp
from core.sprache import t, t_html

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
#
# Sprach-Stufe 1: aus der Modul-Konstante NAV wurde die Funktion _nav() —
# t() darf NIE auf Modulebene laufen (§8.12, sonst friert die Sprachwahl auf
# den Import ein). Jeder Linktext-Schluessel liefert zugleich den Seitentitel
# der Seite (Stufe-1-Pflicht: Linktext == Seitentitel aus DEMSELBEN
# Schluessel; verifyd.py uebergibt an layout() dieselben nav.*-Literale).
def _nav():
    return [
        (t("nav.bereich.activity"), [("/heute", t("nav.heute")),
                                     ("/ereignisse", t("nav.ereignisse")),
                                     ("/offen", t("nav.offen"))]),
        # .220 (User 16.08., Mockup-Abnahme): der Gesichts-Bereich "eingedampft" —
        # People + Face-Learn verschmelzen zu FACES mit Kachel-Startseite
        # (Avatar-Leiste, gefuehrter Lern-Fluss). Easy sieht nur die Startseite,
        # Expert behaelt alle Detail-Blaetter als Unterreiter (NUR_EXPERT_BLAETTER
        # blendet aus, nichts wird geloescht; Erreichbarkeit fuer Easy laeuft ueber
        # die Kachel-Knoepfe — dasselbe Muster wie bei Configuration).
        (t("nav.bereich.faces"), [("/faces", t("nav.faces")),
                                  ("/gesichter", t("nav.gesichter")),
                                  ("/unbekannte", t("nav.unbekannte")),
                                  ("/qualitaet", t("nav.qualitaet"))]),
        # .254 (User 17.08.: "ich vermisse den Knopf fuer das Lernen oben im
        # Menue, er gehoert da rein"): Learn kehrt als Hauptbereich zurueck —
        # Startseite ist der NEUE gefuehrte Lernfluss (.246); Anchors/Suggestions
        # ziehen aus Faces mit (Expert-Unterreiter). Person learn bleibt bewusst
        # unter Person (fachliche Heimat, .220-Entscheid ungebrochen).
        (t("nav.bereich.learn"), [("/lernlauf", t("nav.lernlauf")),
                                  ("/lernlauf/anker", t("nav.anker")),
                                  ("/lernen", t("nav.lernen"))]),
        # Person als EIGENER Hauptbereich neben People (User 04.08. abend):
        # People zeigt die GESICHTER, Person die KOERPER-Bilder je Person.
        # Z8 (konzept_frames.md §7): "Judged images" = Kontroll-Speicher der
        # beurteilten Bilder je Durchgang. Sichtbar auch im Schlank-Modus, weil die
        # Seite dort erklaert, was der Schalter tut — ein Reiter, der je nach Config
        # verschwindet, ist schwerer zu finden als einer, der sich erklaert.
        (t("nav.bereich.person"), [("/person", t("nav.person")),
                                   ("/person/kontrolle", t("nav.person_kontrolle")),
                                   ("/person/modell", t("nav.person_modell")),
                                   # .220: Person learn zieht aus dem aufgeloesten
                                   # Learn-Bereich hierher — der Koerper-Lernlauf
                                   # gehoert fachlich zu Person.
                                   ("/personlauf", t("nav.personlauf"))]),
        # Vision detect zwischen Person und Area (konzept_vision.md v2 §4): der
        # dritte Erkennungspfad. V1 zeigt Verbindung + Test; Galerie-Wizard und
        # Status folgen. Der Reiter steht auch AUS sichtbar da — eine Seite, die
        # erklaert, was sie tut, ist leichter zu finden als eine, die je nach
        # Config verschwindet (dieselbe Begruendung wie bei "Judged images").
        (t("nav.bereich.vision"), [("/vision", t("nav.vision"))]),
        # Live direkt neben Vision (live_reiter_bauplan.md §2.1, User woertlich).
        # Der Reiter steht auch sichtbar da, wenn kein Waechter laeuft — dieselbe
        # Begruendung wie bei "Vision detect": eine Seite, die erklaert, was sie
        # tut, ist leichter zu finden als eine, die je nach Config verschwindet.
        # .200 (Fix 6, Usersicht-Review): die Ergebnis-Seite der Waechter war nur
        # ueber die Today-Seitenleiste erreichbar — "und wo sehe ich jetzt, was er
        # gesehen hat?" hatte keinen Menue-Weg.
        (t("nav.bereich.live"), [("/live", t("nav.live")),
                                 ("/live_alerts", t("nav.live_alerts"))]),
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
        (t("nav.bereich.frigate"), [("/frigate", t("nav.frigate")),
                                    ("/sync_auswahl", t("nav.sync_auswahl"))]),
        # .207 (User 16.08.: die Vier-Saeulen-Seite ist "die Startseite fuer die
        # Konfiguration"): /erkennung steht VORN — der Settings-Klick oben landet
        # direkt dort (Abschnitts-Link = kinder[0]). Die uebrigen Blaetter sind
        # Expert-Sicht (NUR_EXPERT_BLAETTER, Easy blendet ihre Unterreiter aus).
        # .210 (User 16.08.): der Reiter heisst "Configuration", nicht "Settings".
        (t("nav.bereich.configuration"), [
            ("/erkennung", t("nav.erkennung")),
            ("/kameras", t("nav.kameras")),
            ("/benachrichtigungen", t("nav.benachrichtigungen")),
            ("/areas", t("nav.areas")),   # .222: aus der Hauptnav hierher
            # .189 (User 13.08.: "vier Menuepunkte"): die Erkennungskette
            # als EIGENES Blatt VOR Advanced — sie ist Verhaltens-Config
            # erster Klasse, kein versteckter Tabellen-Parameter; seit
            # .207 Teil der Expert-Sicht (der User-Menue-Entscheid bleibt
            # dort erhalten, Easy blendet nur aus).
            ("/kette", t("nav.kette")),
            ("/konfiguration", t("nav.konfiguration"))]),
        # Recognition test als EIGENER Einstieg neben System (konzept_vision.md v2 §4,
        # User-Entscheid 08.08.): die Seite prueft einen Durchgang ueber ALLE DREI
        # Wege (Gesicht/Koerper/Vision) und ist damit kein Vision-Detail. EINE Seite,
        # zwei Einstiege — der Vision-Reiter verlinkt dieselbe Adresse.
        (t("nav.bereich.erkennungstest"), [("/erkennungstest", t("nav.erkennungstest"))]),
        # .341: der System-Bereich bekommt einen zweiten Unterreiter — die
        # Systemstatistik (Bauplan analysen/bauplan_systemstatistik.md). Damit
        # erscheint hier ueberhaupt zum ersten Mal eine zweite Ebene: layout()
        # zeigt sie erst ab zwei Kindern.
        (t("nav.bereich.system"), [("/system", t("nav.system")),
                                   ("/systemstat", t("nav.systemstat"))]),
    ]


def nav_pfade():
    """Zentrale Seitenliste fuer Wachen (Seiten-Sweep im Gate, K3-Fang 19.08.:
    der Sweep las die fruehere Modul-Konstante NAV — als die zur Funktion
    _nav() wurde, brach sein Verbrauch). Laeuft ueber _nav() zur LAUFZEIT
    (§8.12: kein t() auf Modulebene); die Pfade sind sprachunabhaengig."""
    return sorted({p for _ab, kinder in _nav() for p, _n in kinder})


# Blattseiten ohne eigenen Reiter ihrem Abschnitt zuordnen, damit oben trotzdem der richtige
# Bereich leuchtet (heute leuchtet auf /setup gar nichts).
BLATT = {"/setup": "/kameras", "/aehnliche": "/gesichter", "/event": "/heute", "/auftritte": "/heute",
         # /hilfe: eigener aktiv-Pfad seit Stufe 1 (Widerleger P1 — die englischen
         # Anleitungen duerfen den Hinweis der uebersetzten /erkennung nicht erben);
         # Bereichs-Leuchte bleibt Configuration wie zuvor.
         "/hilfe": "/erkennung",
         # Phase 1b (26.08.): die Kalibrierseite der Belichtung haengt an der
         # Lern-Karte (Knopf in Kachel 1) und hat keinen eigenen Reiter —
         # ohne diesen Eintrag leuchtete oben der erste Bereich statt Learn.
         "/lernlauf/belichtung": "/lernlauf",
         # .374: /readme gehoert zu KEINEM Bereich — der Knopf steht in jeder
         # Kopfleiste, die Seite ist kein Blatt eines Reiters. None heisst
         # deshalb "kein Bereich": nichts leuchtet oben, keine Unterreiterzeile.
         # Ohne den Eintrag griff der Rueckfall nav_liste[0][0] und markierte
         # Activity als aktiv, samt dessen Unterreitern (Today/Events/To label)
         # — eine Zeile, in der kein einziger Reiter aktiv war, und 34 px mehr
         # klebende Kopfleiste ueber den Sprungzielen.
         "/readme": None}

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

# Sprach-Stufe 1, Deckungs-Vertrag Mischzustand (konzept_sprache.md §4.1):
# Seiten, deren INHALT noch nicht auf der Sprachschicht liegt — sie tragen
# bei nicht-englischer Sprache eine kleine Hinweiszeile (selbst ein
# Schluessel). Eintraege sind AKTIV-Pfade (der layout()-Parameter, nicht die
# URL): /heute deckt so auch /auftritte, /pass/<id> und /event/<id> mit ab.
# Die Menge schrumpft je Stufe-2-Tranche und wird beim Einzug der jeweiligen
# Seite im selben Commit gepflegt.
# .298 (Tranche A): /heute ist RAUS — auftritte.py (Today/Durchgaenge) ist
# uebersetzt (damit hing auch /event/<id> hinweislos an aktiv="/heute"; seit
# Tranche B ist die Event-Seite selbst uebersetzt, die Luecke ist zu).
# .299 (Tranche B): /setup, /unbekannte, /live_alerts und /video sind RAUS —
# die verifyd-Innenseiten (Wizard, Unbekannte, Live-Alerts, Event, Video,
# Banner, Leer-Zustaende) liegen auf der Sprachschicht.
# .300 (Tranche C): /person*, /personlauf, /vision, /erkennungstest und
# /system sind RAUS — die Routen-Module (system/vision/visiontest/
# visionwizard/personwizard/bausteine) liegen auf der Sprachschicht
# (/personlauf rendert seinen Inhalt aus personwizard.wizard()).
# Sprach-Stufe 3: /hilfe ist RAUS (Anleitungen via t_html). Der Vertrag
# bleibt bestehen: eine Seite, deren Inhalt (noch) nicht auf der
# Sprachschicht liegt, traegt ihren AKTIV-Pfad hier ein und bekommt die
# Hinweiszeile, bis ihr Einzug sie wieder streicht.
# Der Mischsprach-Hinweis auf /heute ist am 25.08. ersatzlos entfernt worden
# (User-Entscheid: "der irritiert nur"). Grund: der Seitenrahmen IST uebersetzt —
# Navigation, Reiter, Sprachschalter, Was-ist-neu-Box —, englisch bleiben nur die
# Auswertungen im Inhaltsbereich. Ein Satz, der oben auf einer sichtbar deutschen
# Seite behauptet, sie sei nicht uebersetzt, liest sich als Fehler statt als
# Auskunft. Der ehrliche Weg ist der /heute-Einzug (Etappe ME2), nicht ein Schild
# davor. Bis dahin bleibt die Mischsprache stumm sichtbar.


# Die beiden Galerie-Links ("Review gallery", "Strangers gallery") sind am 25.07. entfernt worden:
# erzeugt wurden die Seiten von prototypes/backtest.py, das in keinem Image liegt. Fuer JEDE
# Neuinstallation standen damit auf JEDER Seite zwei Links, die dauerhaft eine nackte
# 404-Textzeile lieferten. Ein Link, der bei niemandem ausser dem Entwickler funktioniert,
# gehoert nicht in die Fusszeile.
# #53 Update-Hinweis: verifyd.update_check() setzt das nach jedem taeglichen Check
# ({"tag": "v0.1.0.x", "url": ...} oder None). Prozess-Zustand, Quelle state/update_check.json —
# das Layout bleibt zustandslos und muss nichts nachladen.
UPDATE_INFO = None


def _fuss():
    # Sprach-Stufe 1: Funktion statt Konstante (§8.12) — erscheint auf jeder
    # Seite (B11). "Docs" fuehrt aufs englische GitHub-Repo und bleibt trotzdem
    # ein Schluessel: die Sprachen duerfen das Wort selbst waehlen.
    return (f'<a href="/log">{html.escape(t("ui.fuss.log"))}</a> · '
            '<a href="https://github.com/BennoBaer-dev/suslik" target="_blank" '
            f'rel="noopener noreferrer">{html.escape(t("ui.fuss.docs"))}</a> · '
            f'<a href="/health">{html.escape(t("ui.fuss.health"))}</a>')


# Miniatur-Flaggen fuer den Sprachschalter (User-Entscheid §6.1: SVG-Flaggen +
# Sprachname). Fest eingebettet — Emoji-Flaggen zerfallen auf Windows zu
# Buchstabenkuerzeln (B14). FESTE Farben statt Theme-Variablen: Flaggenfarben
# wechseln nicht mit hell/dunkel. Vereinfachte Zeichnungen (ES ohne Wappen);
# Deckungs-Vertrag: je moeglichem SPRACHEN-Eintrag eine Flagge (Gate prueft
# gegen core/sprache.NAMEN).
_FLAGGEN = {
    "en": ('<svg class="flg" viewBox="0 0 60 40" aria-hidden="true">'
           '<rect width="60" height="40" fill="#012169"/>'
           '<path d="M0 0 60 40M60 0 0 40" stroke="#fff" stroke-width="8"/>'
           '<path d="M0 0 60 40M60 0 0 40" stroke="#C8102F" stroke-width="4"/>'
           '<path d="M30 0V40M0 20H60" stroke="#fff" stroke-width="13"/>'
           '<path d="M30 0V40M0 20H60" stroke="#C8102F" stroke-width="8"/></svg>'),
    "de": ('<svg class="flg" viewBox="0 0 60 40" aria-hidden="true">'
           '<rect width="60" height="13.4" fill="#000"/>'
           '<rect y="13.3" width="60" height="13.4" fill="#D00"/>'
           '<rect y="26.6" width="60" height="13.4" fill="#FFCE00"/></svg>'),
    "es": ('<svg class="flg" viewBox="0 0 60 40" aria-hidden="true">'
           '<rect width="60" height="40" fill="#AA151B"/>'
           '<rect y="10" width="60" height="20" fill="#F1BF00"/></svg>'),
    "it": ('<svg class="flg" viewBox="0 0 60 40" aria-hidden="true">'
           '<rect width="60" height="40" fill="#CE2B37"/>'
           '<rect width="40" height="40" fill="#fff"/>'
           '<rect width="20" height="40" fill="#009246"/></svg>'),
    "fr": ('<svg class="flg" viewBox="0 0 60 40" aria-hidden="true">'
           '<rect width="60" height="40" fill="#EF4135"/>'
           '<rect width="40" height="40" fill="#fff"/>'
           '<rect width="20" height="40" fill="#0055A4"/></svg>'),
}


def sprache_knoepfe():
    """Sprachwahl-Knoepfe (Flagge + Eigenname) je registrierter Sprache —
    geteilt vom Kopfleisten-Menue und Wizard-Schritt 0. Der Eigenname kommt
    aus core/sprache.NAMEN (nie uebersetzt: jede Sprache nennt sich selbst).
    Klick laeuft ueber spracheSetzen() in app.js -> POST /sprache_speichern
    (Areas-Muster, kein Neustart) -> Reload."""
    akt = _sp.aktive()
    return "".join(
        f'<button type="button" class="sp-knopf{" an" if c == akt else ""}" data-s="{c}">'
        f'{_FLAGGEN.get(c, "")}<span>{html.escape(_sp.NAMEN.get(c, c))}</span></button>'
        for c in _sp.SPRACHEN)


def _sprach_schalter():
    # Unsichtbar, solange nur eine Sprache registriert ist — der Schalter
    # erscheint erst mit der Registrierung in core/sprache.SPRACHEN (letzter
    # Schritt der Stufe 1), nie halb verdrahtet.
    if len(_sp.SPRACHEN) < 2:
        return ""
    akt = _sp.aktive()
    return ('<details class="sprache" id="sprache-wahl">'
            f'<summary title="{html.escape(t("ui.sprache.tooltip"))}">'
            f'{_FLAGGEN.get(akt, "")}'
            f'<span class="sp-txt">{html.escape(_sp.NAMEN.get(akt, akt))}</span>'
            '</summary>'
            f'<div class="sp-menu">{sprache_knoepfe()}</div></details>')


def layout(titel, aktiv, inhalt, banner=None, refresh=None, banner_aktion=None,
           hinweis=None, hinweis_id=None):
    """Seiten-Huelle: Nav + optionaler Warn-Banner + Inhalt + Fusszeile.
    refresh=N laedt die Seite alle N Sekunden neu (offener Tab bleibt aktuell).

    hinweis: dezenter Merksatz UNTER dem Banner (User 25.08.). Bewusst eine
    zweite, leisere Ebene: der Banner meldet Stoerungen, der Hinweis erklaert
    nur etwas. Wer beides gleich laut macht, entwertet den Banner."""
    # Aktiven Abschnitt aus dem Pfad ableiten — die Seiten uebergeben weiterhin ihren eigenen
    # Pfad, keine Seite muss etwas ueber die Gruppierung wissen.
    nav_liste = _nav()
    a = BLATT.get(aktiv, aktiv)
    # a is None: Seite ohne Bereich (BLATT-Eintrag "/readme") — dann leuchtet
    # oben nichts und die zweite Ebene bleibt weg, statt dass der Rueckfall
    # den ERSTEN Bereich behauptet.
    abschnitt = None if a is None else next(
        (ab for ab, kinder in nav_liste
         if any(p == a for p, _ in kinder)), nav_liste[0][0])
    nav = "".join(
        f'<a href="{kinder[0][0]}"{" class=aktiv" if ab == abschnitt else ""}>{html.escape(ab)}</a>'
        for ab, kinder in nav_liste)
    kinder = next((k for ab, k in nav_liste if ab == abschnitt), [])
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
               f'rel="noopener noreferrer" title="{html.escape(t("ui.upd.tooltip"))}">'
               f'{html.escape(t("ui.upd.link", tag=UPDATE_INFO["tag"]))}</a>')
    # banner_aktion: FERTIGES Markup des Aufrufers (heute nur der Nachhol-Knopf auf
    # /heute). Der Banner-TEXT bleibt escaped — Markup kommt nie aus dem Text.
    b = (f'<div class="banner">{html.escape(banner)}{banner_aktion or ""}</div>'
         if banner else "")
    # .341 (User 25.08.: "gegebenenfalls per Klick noch den Hinweis haben, diesen
    # Text nicht nochmal zeigen zu lassen"): wegklickbar wie die What's-new-Box —
    # Merker im localStorage, kein Server-Zustand. Wie dort startet die Zeile
    # hidden und zeigt sich erst, wenn der Merker NICHT passt; wer sie weggeklickt
    # hat, sieht sie nie wieder aufblitzen. Der Merker traegt den Schluesselnamen,
    # damit ein spaeterer zweiter Hinweis nicht denselben Merker erbt.
    hw = ""
    if hinweis:
        _hid = "vd-hinweis-" + (hinweis_id or "allgemein")
        hw = (f'<div class="hinweis" id="hinweisz" hidden>{html.escape(hinweis)}'
              f'<button class="hinweis-x" title="{html.escape(t("ui.hinweis.x_tooltip"))}" '
              f'aria-label="{html.escape(t("ui.hinweis.x_aria"))}">&times;</button></div>'
              '<script>(function(){var h=document.getElementById("hinweisz");if(!h)return;'
              f'var k={json.dumps(_hid)};'
              'try{if(localStorage.getItem(k)==="1"){h.remove();return;}}catch(e){}'
              'h.hidden=false;h.querySelector(".hinweis-x").onclick=function(){'
              'try{localStorage.setItem(k,"1")}catch(e){}h.remove();};})();</script>')
    r = f'<meta http-equiv="refresh" content="{int(refresh)}">' if refresh else ""
    # .371 (User 29.08.: "muss einmal als Knopf deutlich sichtbar sein, am besten
    # ueberall"): deshalb hier im Layout und nicht auf einer einzelnen Seite.
    # Neben der Navigation, mit eigener Farbe — wer zum ersten Mal vor der
    # Oberflaeche sitzt, soll ihn finden, ohne zu suchen.
    rmk = (f'<a class="rmk" href="/readme" title="{html.escape(t("readme.titel"))}">'
           f'{html.escape(t("readme.knopf"))}</a>')
    # Und das Aufgehen von selbst: die Seite fragt EINMAL nach, ob die Marke
    # fehlt (also seit dem letzten Dienststart noch niemand geschlossen hat),
    # und holt sich den Inhalt dann nach. Entkoppelt, damit es auf JEDER Seite
    # greift — der Nutzer landet nicht zwingend zuerst auf der Startseite.
    # .371 (User 30.08.): "Wir machen es so, dass das nicht beim Start automatisch
    # der Text angezeigt wird, sondern einfach der Knopf ist da und jeder kann das
    # lesen." Das selbsttaetige Overlay ist damit RAUS — der Knopf oben bleibt und
    # fuehrt auf /readme. Grund war nicht nur der Geschmack: der User kam aus dem
    # Overlay nicht mehr heraus. Die Marker-Mechanik in core/readmefirst.py bleibt
    # bestehen (Routen /readme_noetig und /readme_gesehen antworten weiter), damit
    # ein spaeteres "einmal nach dem Neustart zeigen" nur diese Zeilen braucht.
    rmjs = ""
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
    # Sprach-Stufe 1: der Sprachschalter steht NEBEN dem Theme-Knopf (User-
    # Vorgabe "oben in der Kopfleiste, neben Theme").
    # .371 (User 29.08.): "Der Schalter sollte am besten oben in der Leiste sein,
    # wo wir auch Tag und Nacht umschalten. Vielleicht gleich als Erstes, neben dem
    # Experten-Schalter, dass der Benutzer das auch sieht." Der Knopf steht deshalb
    # als ERSTES in der rechten Gruppe. Er ist im Markup immer da und wird von
    # catchupPruefen() (app.js) nur eingeblendet, wenn wirklich etwas wartet — ein
    # dauerhaft sichtbarer Knopf fuer nichts waere eine Dauerfrage ohne Anlass.
    catchup = ('<button class="toggle catchup" id="catchup-knopf" hidden '
               f'title="{html.escape(t("catchup.knopf.tooltip"))}" '
               'onclick="catchupStarten()">'
               '<span class="tg-ico" aria-hidden="true">\u21bb</span>'
               f'<span class="tg-txt">{html.escape(t("catchup.knopf"))}</span>'
               '<span class="cu-n" id="catchup-zahl"></span></button>')
    # Der Dialog beim Druecken (User 29.08.: "Beim Druecken des Knopfes koennte eine
    # Frage sein, wie weit sollen wir zurueckgehen, wie viele Events sollen wir
    # maximal holen"). Bauform wie die Lernlauf-Frage (Zahlenfeld + Hinweis), damit
    # die Oberflaeche nicht zwei Sprachen fuer dieselbe Frage spricht. Spanne und
    # Vorgaben setzt catchupPruefen() aus /health — hier steht keine Zahl.
    catchup_dlg = (
        '<dialog id="catchup-dlg" class="cu-dlg">'
        f'<h3>{html.escape(t("catchup.dlg.titel"))}</h3>'
        f'<p class="cu-satz" id="catchup-satz"></p>'
        '<div class="cu-z"><label for="cu-h">'
        f'{html.escape(t("catchup.dlg.label_stunden"))}</label>'
        '<input id="cu-h" type="number" step="1"> '
        f'<span>{html.escape(t("catchup.dlg.wort_stunden"))}</span>'
        f'<span class="cu-hint" id="cu-h-hint"></span></div>'
        '<div class="cu-z"><label for="cu-n">'
        f'{html.escape(t("catchup.dlg.label_limit"))}</label>'
        '<input id="cu-n" type="number" step="10"> '
        f'<span>{html.escape(t("catchup.dlg.wort_events"))}</span>'
        f'<span class="cu-hint" id="cu-n-hint"></span></div>'
        f'<p class="cu-fuss">{html.escape(t("catchup.dlg.fuss"))}</p>'
        '<div class="cu-akt">'
        '<button type="button" class="gtb-l" onclick="catchupSchliessen()">'
        f'{html.escape(t("catchup.dlg.abbrechen"))}</button>'
        '<button type="button" class="gtb" onclick="catchupLos()">'
        f'{html.escape(t("catchup.dlg.los"))}</button></div>'
        '</dialog>')
    # .371 (User 30.08.): "lass uns erstmal den neuen Knopf Nachholen der letzten
    # Events ausblenden, wir bauen das spaeter etwas anders wieder ein." Knopf und
    # Dialog werden oben weiter GEBAUT, aber in nichts mehr eingesetzt — bewusst
    # tote Locals, damit der Wiedereinbau ein Einhaengen ist und kein Neubau.
    # WICHTIG dazu: der Schalter start_catchup steht wieder auf "on" (load_config),
    # denn ohne Knopf haette der Modus "ask" Ereignisse zurueckgehalten, an die
    # niemand mehr herankommt — genau der stille Verlust, gegen den die Probe steht.
    # .374 (Widerleger-Fund 30.08.): der Default allein reichte NICHT. "ask" war
    # auf dem Advanced-Blatt weiter WAEHLBAR, und der Hilfetext dort beschrieb
    # diesen Knopf hier als vorhanden ("a button appears in the header") und "ask"
    # als Default — wer dem folgte, hielt Ereignisse fest, an die kein Bedienweg
    # mehr fuehrt. Deshalb ist "ask" aus der Auswahlliste der CONFIG_WHITELIST
    # heraus, solange dieser Block tot ist; beides gehoert beim Wiedereinbau
    # zusammen zurueck (verifyd.py, Whitelist-Eintrag "start_catchup").
    rechts = ('<span class="rechts">'
              '<span class="modus" id="ui-modus" '
              f'title="{html.escape(t("ui.modus.tooltip"))}">'
              f'<button type="button" data-m="easy">{html.escape(t("ui.modus.easy"))}</button>'
              f'<button type="button" data-m="expert">{html.escape(t("ui.modus.expert"))}</button></span>'
              f'<span class="live"><span class="d"></span>{html.escape(t("ui.live.chip"))}</span>'
              # .341b (User 25.08.): Direktweg zur Auslastung aus JEDER Seite, in der
              # Kopfleiste neben Live. Der Unterreiter unter System bleibt bestehen und
              # heisst dort ausgeschrieben — hier oben zaehlt die Kuerze.
              f'<a class="toggle" href="/systemstat" '
              f'title="{html.escape(t("ui.last.tooltip"))}">'
              f'<span class="tg-txt">{html.escape(t("ui.last.knopf"))}</span></a>'
              + _sprach_schalter() +
              '<button class="toggle" id="theme-toggle" '
              f'title="{html.escape(t("ui.theme.tooltip"))}" '
              f'aria-label="{html.escape(t("ui.theme.aria"))}">'
              '<span class="tg-ico" aria-hidden="true">◐</span>'
              f'<span class="tg-txt">{html.escape(t("ui.theme.knopf"))}</span></button></span>')
    # Themenwahl (25.07.): OHNE eigene Wahl folgt die Oberflaeche dem Betriebssystem. Vorher war
    # Dunkel fest voreingestellt — User: "es ist ja alles sehr dunkel und faende ich nicht so
    # willkommen". Wer den Umschalter benutzt, ueberstimmt das System dauerhaft; das OS ueberschreibt
    # eine ausdrueckliche Wahl NIE. Inline und vor dem Stylesheet, damit nichts kurz aufblitzt.
    themejs = ('<script>try{var t=localStorage.getItem("vd-theme");'
               'if(!t&&window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches)t="light";'
               'if(t)document.documentElement.setAttribute("data-theme",t);}catch(e){}</script>')
    # Sprach-Stufe 1 (B3): window.T traegt die js.*-Schluessel der aktiven
    # Sprache — json.dumps loest das Escaping; "</" und "<!--" werden
    # zusaetzlich gebrochen (script-Parser-Zustaende). EHRLICH (Widerleger
    # P6): by construction sicher wird das erst ZUSAMMEN mit der Gate-Stufe,
    # die <> in Nicht-HTML_SCHLUESSEL-Werten verbietet — die Ersetzungen hier
    # sind die zweite Verteidigungslinie. VOR app.js (defer liest es erst
    # nach dem Parsen, Inline-Handler zur Laufzeit).
    tjs = ('<script>window.T=' +
           json.dumps(_sp.js_tabelle(), ensure_ascii=False)
           .replace("</", "<\\/").replace("<!--", "<\\!--") +
           '</script>')
    # <html lang> (B21): ohne die Marke bietet Chrome die Auto-Uebersetzung
    # der schon uebersetzten Seite an. Erste explizite <html>-Marke des
    # Skeletts; der Browser schliesst sie selbst (kein <body>-Umbau noetig).
    return (f'<!doctype html><html lang="{_sp.aktive()}"><meta charset=utf-8>' + r +
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(titel)} — suslik{(' ' + ver) if ver else ''}</title>"
            f'<link rel="stylesheet" href="/static/style.css?v={_STATIK_STEMPEL}">'
            + themejs + tjs +
            f'<script src="/static/app.js?v={_STATIK_STEMPEL}" defer></script>'
            # Beide Leisten in EINEN klebenden Block (Fund der Nachpruefung 25.07.): einzeln
            # klebend brauchte die zweite Ebene einen Festwert fuer die Hoehe der ersten, und der
            # wurde falsch, sobald die erste umbrach — s. .kopf in style.css.
            f'<div class="kopf"><nav><div class="inner"><span class="marke">{mark}suslik'
            f'{f" <small>{html.escape(ver)}</small>" if ver else ""}{upd}</span>{nav}{rmk}{rechts}</div></nav>'
            f"{unter}</div>"
            f"<main>{b}{hw}{inhalt}</main>"
            f"<footer>{_fuss()}</footer>{rmjs}</html>")


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
    weggeklickt hat, sieht sie bis zur naechsten Version nie aufblitzen.
    Sprach-Stufe 1: die BESCHRIFTUNGEN sind Schluessel; die EINTRAEGE selbst
    kommen aus core/highlights.py und werden je Release 5-sprachig gepflegt
    (§6.3) — bis dahin englisch."""
    from core.highlights import BETONT, HIGHLIGHTS   # import-frei, kein Zyklus
    eintraege = [(v, tx) for v, its in HIGHLIGHTS for tx in its][:10]
    if not eintraege:
        return ""
    neueste = html.escape(HIGHLIGHTS[0][0], quote=True)
    li, letzte_v = [], None
    code = _sp.aktive()
    for i, (v, txt) in enumerate(eintraege):
        chip = f'<span class="wn-v">{html.escape(v)}</span>' if v != letzte_v else ""
        letzte_v = v
        # .168: ein markierter Eintrag wird fett und in Warnfarbe gesetzt (der
        # Vorab-Hinweis eines Releases). Die Marke wird abgenommen, der Text
        # bleibt escaped — hier kommt kein Markup aus der Quelle durch.
        # Seit .298 (§6.3) sind Eintraege mehrsprachig: dict {en,de,es,it,fr
        # [,betont]} mit en-Fallback; Alt-Eintraege bleiben str (nur englisch),
        # dort traegt weiter das BETONT-Praefix die Marke.
        if isinstance(txt, dict):
            betont = bool(txt.get("betont"))
            txt = txt.get(code) or txt["en"]
        else:
            betont = txt.startswith(BETONT)
            if betont:
                txt = txt[len(BETONT):]
        kl = " ".join(x for x in (("wn-mehr" if i >= 3 else ""),
                                  ("wn-betont" if betont else "")) if x)
        li.append(f'<li{f' class="{kl}"' if kl else ""}>{chip}'
                  + html.escape(txt) + "</li>")
    mehr = len(eintraege) - 3
    toggle = (f'<button class="wn-toggle" data-n="{mehr}">'
              f'{html.escape(t("ui.wn.mehr", n=len(eintraege)))}</button>'
              if mehr > 0 else "")
    # Toggle-Labels (Show all/fewer) via json.dumps ins Inline-JS — der
    # Schalter wechselt den textContent im Browser (Toggle-Label-Muster,
    # §8-Nachtrag Stufe 1); beide Fassungen kommen fertig vom Server.
    _wn_mehr_js = json.dumps(t("ui.wn.mehr", n=len(eintraege)), ensure_ascii=False)
    _wn_weniger_js = json.dumps(t("ui.wn.weniger"), ensure_ascii=False)
    return (
        f'<div class="wnblock" id="wnblock" hidden><div class="wn-kopf">'
        f'<span class="wn-t">{html.escape(t("ui.wn.titel"))}</span>'
        f'<button class="wn-x" title="{html.escape(t("ui.wn.x_tooltip"))}" '
        f'aria-label="{html.escape(t("ui.wn.x_aria"))}">&times;</button></div>'
        f'<ul class="wn-liste">{"".join(li)}</ul>{toggle}</div>'
        '<script>(function(){var b=document.getElementById("wnblock");if(!b)return;'
        f'var v="{neueste}";'
        'try{if(localStorage.getItem("vd-wn-seen")===v){b.remove();return;}}catch(e){}'
        'b.hidden=false;var t=b.querySelector(".wn-toggle");'
        'if(t)t.onclick=function(){var o=b.classList.toggle("wn-open");'
        f't.textContent=o?{_wn_weniger_js}:{_wn_mehr_js};}};'
        'b.querySelector(".wn-x").onclick=function(){'
        'try{localStorage.setItem("vd-wn-seen",v)}catch(e){}b.remove();};})();</script>')


def update_block():
    """#53: sachlicher, DEUTLICHER Hinweis-Block fuer die Startseite (User 26.07.: 'exklusiv
    dargestellt … sachlich hingewiesen, aber schon deutlich' — kein Blinken, kein Erschlagen).
    Ergaenzt die leise Kopf-Marke; leer, wenn kein Update bekannt ist.
    Sprach-Stufe 1: der Satz ist der erste deklarierte t_html-Schluessel
    (Inline-Markup in Prosa, §8.1) — tag/url escapt t_html selbst."""
    if not (UPDATE_INFO and UPDATE_INFO.get("tag")):
        return ""
    return (f'<div class="updblock"><span class="updb-t">{html.escape(t("ui.upd.titel"))}</span>'
            f'<span class="updb-x">'
            + t_html("ui.upd.satz", tag=UPDATE_INFO["tag"], url=UPDATE_INFO.get("url") or "")
            + '</span></div>')
