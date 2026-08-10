"""routes/visiontest — "Recognition test": EIN Durchgang, DREI Wege nebeneinander
(konzept_vision.md v2 §4, Zug V4).

Der User am 08.08.: "optimal waere eine allgemeine Erkennung durch alle
drei". Genau
das ist diese Seite — man waehlt einen ECHTEN vergangenen Durchgang und sieht
Gesicht, Koerper und Vision nebeneinander:

  * Gesicht und Koerper kommen aus den BUECHERN des Durchgangs. Hier wird nichts
    neu gerechnet, kein Clip geoeffnet, kein Frame dekodiert — die Spalten
    zeigen, was die Erkennung damals wirklich geurteilt hat.
  * Vision laeuft frisch, und zwar ueber den ECHTEN Urteilspfad (nie eine
    Kopie): was der Test zeigt, tut spaeter der Betrieb. Ein Testlauf zaehlt
    deshalb wie ein manueller Klick — er kostet echte Anfragen, und das steht
    auch so da.
  * Ohne konfiguriertes Vision funktioniert die Seite trotzdem: die
    Vision-Spalte sagt dann ehrlich "not configured", die anderen beiden nicht.

Die Seite hat ZWEI Einstiege (Kopfleiste + Vision-Reiter) und ist EINE
Implementierung. Kontrakt wie alle routes-Module: reiner Renderer, Daten als
Parameter, kein Dienst-Import.
"""
import html
import time
import urllib.parse

from core import vision as _vis   # nur die Klartext-Tabelle der Gruende (§8):
#   reine Daten, kein Dienst-Zustand — der routes-Kontrakt bleibt gewahrt.
from core import visionurteil as _vu   # nur NACHANALYSE_GRUENDE (reine Daten)

STIL = """<style>
 .rt-w { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
   gap:12px; margin-top:10px; align-items:start; }
 .rt-s { padding:12px; border-radius:10px; background:var(--surface-2);
   border:1px solid var(--border); border-top:3px solid var(--faint); }
 .rt-s.ja { border-top-color:var(--ok); }
 .rt-s.nein { border-top-color:var(--warn); }
 .rt-s h3 { margin:0 0 2px; font-size:15px; }
 .rt-s .rt-q { color:var(--dim); font-size:12px; }
 .rt-erg { font-size:17px; margin:8px 0 4px; }
 .rt-liste { margin:6px 0 0; padding:0; list-style:none; font-size:13px; }
 .rt-liste li { padding:3px 0; border-bottom:1px solid var(--border); }
 .rt-liste li:last-child { border-bottom:0; }
 /* Die Pass-Auswahl klappt zu, sobald ein Durchgang gewaehlt ist (User 10.08.:
    "der Auswahlblock erschlaegt"). Reines <details> — die Seite braucht dafuer
    kein Javascript, und ohne Vorauswahl startet sie offen. */
 .rt-wahl > summary { list-style:none; cursor:pointer; display:flex;
   flex-wrap:wrap; align-items:baseline; gap:4px 10px; }
 .rt-wahl > summary::-webkit-details-marker { display:none; }
 .rt-wahl .rt-meta { color:var(--dim); font-size:12px; }
 .rt-wahl .rt-mehr { margin-left:auto; font-size:12px; color:var(--accent); }
 .rt-wahl[open] .rt-mehr { color:var(--dim); }
 .rt-p { display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
 .rt-pk { text-align:left; padding:8px 10px; border-radius:8px; cursor:pointer;
   background:var(--surface-2); border:1px solid var(--border);
   color:var(--text); font:inherit; font-size:13px; }
 .rt-pk:hover { border-color:var(--accent); }
 .rt-pk.on { border-color:var(--ok); box-shadow:inset 0 0 0 1px var(--ok); }
 .rt-pk small { display:block; color:var(--dim); }
 .rt-b { display:grid; gap:8px; margin-top:8px;
   grid-template-columns:repeat(auto-fill,minmax(90px,120px)); }
 .rt-b figure { margin:0; border-radius:6px; overflow:hidden;
   background:rgba(0,0,0,.25); border:1px solid var(--border); }
 .rt-b img { width:100%; height:120px; object-fit:contain; display:block; }
 .rt-b figcaption { font-size:11px; color:var(--dim); padding:3px 4px; }
 /* Das GEFRAGTE Bild in voller Breite der Spalte — es ist das eine Bild, um das
    der ganze Lauf geht, und es steht ueber den Einzelzellen. `height:auto` haelt
    das Seitenverhaeltnis, `max-width` verhindert jeden Ueberlauf (S9). */
 .rt-gv { margin:8px 0 0; border-radius:8px; overflow:hidden;
   background:rgba(0,0,0,.25); border:1px solid var(--border); }
 .rt-gv img { width:100%; max-width:100%; height:auto; display:block; }
 .rt-gv figcaption { font-size:11px; color:var(--dim); padding:4px 5px; }
 .rt-log { margin-top:10px; border-top:1px solid var(--border); padding-top:8px; }
 .rt-log b { font-size:12px; color:var(--dim); text-transform:uppercase;
   letter-spacing:.04em; }
 .rt-logl { margin:6px 0 0; padding:0 0 0 2px; list-style:none; font-size:13px;
   line-height:1.45; }
 .rt-logl li { padding:3px 0; border-bottom:1px dotted var(--border); }
 .rt-logl li:last-child { border-bottom:0; }
 .rt-uhr { display:inline-block; min-width:66px; color:var(--dim);
   font-variant-numeric:tabular-nums; font-size:12px; }
 .rt-warte { color:var(--dim); font-style:italic; }
 /* Ruhige Laufmarke — kein Blinken: die Seite laedt sich ohnehin selbst nach. */
 .rt-lauf { display:inline-block; width:9px; height:9px; border-radius:50%;
   margin-right:7px; background:var(--warn); }
 /* Der zentrale Nachanalyse-Block ueber den drei Spalten (.162): er betrifft
    alle drei Wege, deshalb steht er im Kopf und nicht in einer Spalte. */
 .rt-kopfknopf { margin-top:10px; padding:10px 12px; border-radius:10px;
   background:var(--surface-2); border:1px solid var(--border);
   border-left:3px solid var(--ok); }
 .rt-kopfknopf.laeuft { border-left-color:var(--warn); }
 .rt-kopfknopf b { font-size:14px; }
 .rt-kopfknopf .rt-q { color:var(--dim); font-size:12px; margin-top:3px; }
 .rt-s .gtb[disabled] { opacity:.45; cursor:not-allowed; }
 /* Die zwei Felder des manuellen Testlaufs (.164) — klein, direkt am Knopf,
    damit man sie als Stellschrauben DIESES Laufs liest und nicht als
    Einstellung. */
 .rt-felder { display:flex; flex-wrap:wrap; gap:10px; margin:8px 0 6px; }
 .rt-felder label { font-size:12px; color:var(--dim); display:flex;
   align-items:center; gap:5px; }
 .rt-felder input { width:64px; padding:3px 5px; border-radius:6px;
   background:var(--surface); border:1px solid var(--border);
   color:var(--text); font:inherit; font-size:13px; }
 /* Vergleichsliste der bisherigen Laeufe dieses Durchgangs */
 .rt-hist { margin-top:10px; border-top:1px solid var(--border);
   padding-top:8px; }
 .rt-hist b { font-size:12px; color:var(--dim); text-transform:uppercase;
   letter-spacing:.04em; }
 /* Acht Spalten in einer schmalen Saeule: die Tabelle scrollt in ihrem EIGENEN
    Kasten, statt die Seite breit zu machen (S9-Geometrie). */
 .rt-hist .rt-htab { overflow-x:auto; margin-top:6px; }
 .rt-hist table { border-collapse:collapse; font-size:12px; min-width:100%;
   white-space:nowrap; }
 .rt-hist td.rt-grund { white-space:normal; max-width:170px; }
 .rt-hist th { text-align:left; color:var(--dim); font-weight:600;
   padding:2px 6px 4px 0; }
 .rt-hist td { padding:3px 6px 3px 0; border-top:1px solid var(--border);
   vertical-align:top; }
 .rt-hist .rt-ja { color:var(--ok); }
 .rt-hist .rt-nein { color:var(--dim); }
</style>"""


def _zeit(ts, form="%d.%m. %H:%M"):
    if not ts:
        return "—"
    return time.strftime(form, time.localtime(float(ts)))


KOSTEN = ("A test run costs real requests, exactly like normal operation: the "
          "whole walk-through goes in as one candidate grid, and each compared "
          "pair of galleries costs two requests, because every question is "
          "asked again with the galleries swapped. It counts as a manual "
          "click, so it does not eat your daily limit &mdash; but on a paid "
          "endpoint it is money, and on a local CPU model it takes minutes.")


def _kopf(kosten):
    return ("<h2>Recognition test</h2>"
            '<p class="sub">Pick one real walk-through and see what all three '
            "recognition paths make of it, side by side: <b>face</b>, "
            "<b>person</b> and <b>vision</b>. Face and person are read from "
            "what was recorded at the time &mdash; nothing is recomputed. Vision "
            "runs now, through exactly the same path it uses in normal "
            f"operation.</p><div class=\"card\">{kosten}</div>")


def _wer(p):
    """Wer in diesem Durchgang erkannt wurde &mdash; EINE Formulierung fuer die
    Kachel und fuer die Kopfzeile des gewaehlten Durchgangs."""
    return ", ".join(sorted(p.get("personen") or [])) or "nobody recognized"


def _passliste(passe, gewaehlt):
    """Der Auswahlblock &mdash; zugeklappt, sobald ein Durchgang gewaehlt ist.

    Der Fall dahinter (User 10.08.): wer die Seite mit einem Durchgang betritt
    (Deep-Link vom Event) oder gerade einen angeklickt hat, will das ERGEBNIS
    sehen und nicht zuerst durch zwei Dutzend Kacheln scrollen. Der gewaehlte
    Durchgang steht dann als eine Zeile da, die Auswahl bleibt einen Klick
    entfernt. Ohne Vorauswahl startet der Block offen, denn dann ist die Wahl
    das Einzige, was zu tun ist. Umgeschaltet wird an `gewaehlt`, also am
    Query-Parameter `?pass=` der Seite &mdash; kein zweiter Zustand."""
    karten = []
    for p in passe or []:
        karten.append(
            f'<button class="rt-pk{" on" if p["pass_key"] == gewaehlt else ""}" '
            f"onclick=\"location.href='/erkennungstest?pass="
            f'{urllib.parse.quote(p["pass_key"])}\'">'
            f'<b>{_zeit(p.get("start"))}</b>'
            f'<small>{html.escape(_wer(p))}</small>'
            f'<small>{p.get("events") or 0} events &middot; '
            f'{p.get("kameras") or 0} camera(s)'
            + (" &middot; vision done" if p.get("vision") else "")
            + "</small></button>")
    if not karten:
        return ('<div class="card"><b>1 &middot; Which walk-through</b>'
                '<div class="dim">No passes recorded yet. As soon as somebody '
                "walks across the property, they appear here.</div></div>")
    gew = next((p for p in passe or [] if p["pass_key"] == gewaehlt), None)
    if gew:
        # Die schmale Kopfzeile des gewaehlten Durchgangs. Genau die Angaben der
        # Kachel, nur in einer Zeile — nichts wird hier neu behauptet.
        kopf = (f'<b>{_zeit(gew.get("start"))} &middot; '
                f'{html.escape(_wer(gew))}</b>'
                f'<span class="rt-meta">{gew.get("events") or 0} event(s) '
                f'&middot; {gew.get("kameras") or 0} camera(s)</span>'
                '<span class="rt-mehr">choose another walk-through</span>')
    elif gewaehlt:
        # Gewaehlt, aber nicht in der Liste (aelter als die gezeigten Tage):
        # dann behauptet die Kopfzeile nichts ueber ihn.
        kopf = ('<b>1 &middot; Which walk-through</b>'
                '<span class="rt-mehr">choose another walk-through</span>')
    else:
        kopf = ('<b>1 &middot; Choose a walk-through</b>'
                f'<span class="rt-meta">{len(karten)} recent pass(es)</span>')
    return ('<div class="card">'
            f'<details class="rt-wahl"{"" if gewaehlt else " open"}>'
            f"<summary>{kopf}</summary>"
            '<div class="dim">The most recent passes, grouped exactly like on '
            "the Today page.</div>"
            f'<div class="rt-p">{"".join(karten)}</div>'
            "</details></div>")


MAX_GESICHTER = 12          # so viele Kacheln wie die Gitter-Vorschau zeigt


def _gesichtskacheln(g):
    """Die Gesichter DIESES Durchgangs als Bilder (User 10.08.: "auch bei Face
    die Bilder sehen &mdash; welche wurden gematcht und welche nicht").

    Die Spalte sagte bis dahin nur, WIE VIELE Events einen Namen trugen. Person
    und Vision zeigten daneben ihre Bilder, hier stand nur Text. Gezeigt wird
    jetzt, was die Analyse damals abgelegt hat: je Event der erkannte Crop mit
    seinem Score, und fuer ein Event ohne Namen derselbe Crop mit "not matched".

    Ehrlich bleibt die Spalte dadurch, dass sie das FEHLEN benennt: hat ein
    unerkanntes Event kein Bild hinterlassen, steht das als Satz da &mdash; die
    Zahlen daneben stammen aus der Akte und werden nicht an den Bildern
    nachgerechnet."""
    kacheln = list(g.get("bilder") or [])
    unbek = int(g.get("unbekannt") or 0)
    ohne_name = sum(1 for b in kacheln if not b.get("person"))
    zeigen = kacheln[:MAX_GESICHTER]
    bilder = "".join(
        '<figure><img loading="lazy" src="/events/'
        + urllib.parse.quote(str(b.get("eid") or "")) + "/"
        + urllib.parse.quote(str(b.get("datei") or "")) + '" alt="">'
        "<figcaption>"
        + (html.escape(str(b["person"])) if b.get("person") else "not matched")
        + (f' {b["score"]:.2f}' if isinstance(b.get("score"), (int, float))
           else "")
        + "</figcaption></figure>"
        for b in zeigen if b.get("eid") and b.get("datei"))
    hinweise = []
    if len(kacheln) > len(zeigen):
        hinweise.append(f"showing {len(zeigen)} of {len(kacheln)} picture(s)")
    if unbek > ohne_name:
        fehlt = unbek - ohne_name
        hinweise.append(f"{fehlt} of the {unbek} unmatched event(s) kept no "
                        "picture")
    if not kacheln:
        hinweise.append("no face picture was kept for this pass")
    return ((f'<div class="rt-b">{bilder}</div>' if bilder else "")
            + (f'<div class="rt-q">{" &middot; ".join(hinweise)}</div>'
               if hinweise else ""))


def _gesicht(g):
    if g.get("personen"):
        erg = ", ".join(html.escape(p["person"]) for p in g["personen"])
        kl = "ja"
    else:
        erg, kl = '<span class="dim">no known face</span>', "nein"
    li = "".join(
        f'<li>{html.escape(p["person"])} &middot; {p.get("events")} event(s)'
        + (f' &middot; best {p["best"]:.2f}' if isinstance(p.get("best"), float)
           else "") + "</li>" for p in g.get("personen") or [])
    rest = ""
    if g.get("unbekannt"):
        rest = (f'<div class="rt-q">{g["unbekannt"]} event(s) with a face that '
                "was not matched</div>")
    return (f'<div class="rt-s {kl}"><h3>Face</h3>'
            '<div class="rt-q">embedding comparison against your reference '
            "faces &mdash; from the record of this pass</div>"
            f'<div class="rt-erg">{erg}</div>'
            f'<ul class="rt-liste">{li}</ul>{rest}'
            + _gesichtskacheln(g) + "</div>")


def _koerper(k, pass_key):
    if k.get("treffer"):
        namen = sorted({t["person"] for t in k["treffer"]})
        erg, kl = ", ".join(html.escape(n) for n in namen), "ja"
    elif k.get("personen"):
        erg = ('<span class="dim">candidates, none above the rule: '
               + ", ".join(f"{html.escape(n)} ({c})"
                           for n, c in sorted(k["personen"].items())) + "</span>")
        kl = "nein"
    else:
        erg, kl = '<span class="dim">nothing judged</span>', "nein"
    li = "".join(
        f'<li>{html.escape(str(b.get("klasse") or "?"))} &middot; '
        f'score {b.get("score")} of {b.get("schwelle")} &middot; '
        f'{html.escape(str(b.get("quelle") or ""))}'
        + ("" if b.get("bild") else ' &middot; <span class="dim">image '
           "expired</span>") + "</li>"
        for b in (k.get("bilder") or [])[:12])
    bilder = "".join(
        '<figure><img loading="lazy" src="/person/kontrolle/bild/'
        + urllib.parse.quote(pass_key) + "/" + urllib.parse.quote(b["datei"])
        + f'"><figcaption>{html.escape(str(b.get("klasse") or "?"))} '
        f'{b.get("score")}</figcaption></figure>'
        for b in (k.get("bilder") or [])[:8] if b.get("bild") and b.get("datei"))
    # SPALTEN-NAME (User 09.08.: "face, person und vision"). Nur die
    # ANZEIGE heisst so; die Codebezeichner bleiben `_koerper`/`koerper`, damit
    # der Bezug zum Koerper-Modell im Quelltext eindeutig bleibt.
    return (f'<div class="rt-s {kl}"><h3>Person</h3>'
            '<div class="rt-q">DINOv2 embedding + classifier on the judged '
            "images of this pass</div>"
            f'<div class="rt-erg">{erg}</div>'
            f'<ul class="rt-liste">{li}</ul>'
            f'<div class="rt-b">{bilder}</div></div>')


def _log(schritte, offen):
    """Das mitwachsende Erzaehl-Log (V4b, User 08.08.: "super waere es wenn man
    lesen koennte was passiert, so das man etwas mitgenommen wird").

    Ein lokaler Lauf braucht Minuten je Bild-Paar. Die Zeilen kommen aus dem
    Lauf-Protokoll — sie sind also schon geschrieben, wenn die Seite sie zeigt,
    und sie bleiben nach dem Lauf als Verlauf dieses Durchgangs stehen."""
    if not schritte:
        return ""
    zeilen = []
    for e in schritte:
        uhr = _zeit(e.get("ts"), "%H:%M:%S")
        zeilen.append(f'<li><span class="rt-uhr">{html.escape(uhr)}</span>'
                      f'{html.escape(str(e.get("text") or ""))}</li>')
    warte = ('<li class="rt-warte"><span class="rt-uhr">&middot;&middot;&middot;'
             "</span>waiting for the model &mdash; this page refreshes itself"
             "</li>" if offen else "")
    return ('<div class="rt-log"><b>What happened</b>'
            f'<ol class="rt-logl">{"".join(zeilen)}{warte}</ol></div>')


def _gitter(z, pass_key):
    """Die Vorschau des KANDIDATEN-GITTERS (V4c): die Zellen, aus denen das eine
    Bild gebaut wurde, mit ehrlicher Zellen-Zahl.

    Bis .159 stand hier eine Liste mit einem Urteil JE BILD — die gibt es nicht
    mehr, weil der ganze Durchgang als EIN Gitter gefragt wird. Gezeigt wird
    deshalb, was in das Gitter hineinging; das Urteil steht darunter, einmal.

    Seit .169 steht darueber das GERENDERTE Gitter selbst, sofern der Lauf es
    abgelegt hat (`gitter_datei`) — also genau das Bild, das der Urteiler sah.
    Ausgeliefert ueber den vorhandenen Kontroll-Bild-Weg, kein eigener
    Endpunkt. Alte Laeufe haben das Feld nicht; dann bleibt es bei den Zellen,
    es wird nichts behauptet."""
    zellen = z.get("bilder") or []
    if not zellen:
        return ""
    g = z.get("gitter") or {}
    n = int(g.get("zellen") or len(zellen))
    luecken = int(g.get("luecken") or 0)
    gd = z.get("gitter_datei")
    voll = ("" if not gd else
            '<figure class="rt-gv"><img loading="lazy" '
            'src="/person/kontrolle/bild/'
            + urllib.parse.quote(pass_key) + "/" + urllib.parse.quote(str(gd))
            + '" alt="the candidate grid of this run">'
            "<figcaption>the picture the model was actually shown</figcaption>"
            "</figure>")
    bilder = "".join(
        '<figure><img loading="lazy" src="/person/kontrolle/bild/'
        + urllib.parse.quote(pass_key) + "/" + urllib.parse.quote(b["datei"])
        + f'"><figcaption>{b.get("hoehe")} px</figcaption></figure>'
        for b in zellen[:12] if b.get("datei"))
    return (f'<div class="rt-q">candidate grid: {n} cell(s) from this '
            "walk-through, asked as ONE picture"
            + (f" ({luecken} cell(s) left empty)" if luecken else "")
            + f"</div>{voll}"
            + f'<div class="rt-b">{bilder}</div>')


def _runden(z):
    """Die gefahrenen Vergleiche — je Runde ein Paar, zwei Anfragen."""
    zeilen = []
    for r in z.get("runden") or []:
        wer = {"A": r.get("a"), "B": r.get("b")}.get(r.get("wahl"))
        erg = (html.escape(str(wer)) if wer and not r.get("kein_votum")
               else "no vote &mdash; "
               + html.escape(_vis.grund_text(r.get("grund"))))
        dauer = f' &middot; {r["dauer_s"]} s' if r.get("dauer_s") else ""
        zeilen.append(f'<li>{html.escape(str(r.get("a")))} vs '
                      f'{html.escape(str(r.get("b")))} &middot; {erg}{dauer}'
                      "</li>")
    return f'<ul class="rt-liste">{"".join(zeilen)}</ul>'


def _fehlt_material(sicht):
    """Fehlt fuer DIESEN Durchgang das beurteilte Material — und wuerde eine
    erneute Analyse etwas daran aendern?

    Die Frage haengt an `grund_art` aus core.visionurteil.NACHANALYSE_GRUENDE
    (EINE Quelle, kein Literal hier). Sie betrifft ausdruecklich nicht nur
    Vision: dieselben Bilder fuellen auch die Person-Spalte."""
    z = ((sicht or {}).get("vision") or {}).get("zeile") or {}
    return z.get("grund_art") in _vu.NACHANALYSE_GRUENDE


def _nachanalyse_kopf(sicht, nachanalyse):
    """Der Knopf "Analyse this walk-through again" — im KOPF der
    Durchgangs-Ansicht, nicht in der Vision-Spalte (User 09.08.: "der muesste
    zentraler sein, da er ja alle drei betrifft").

    Das ist keine Kosmetik: die erneute Analyse fuellt Gesicht, Person UND
    Vision gleichermassen, weil sie den ganzen Analyse-Weg noch einmal faehrt.
    In der Vision-Spalte sah er aus wie eine Vision-Funktion.

    Er erscheint nur, wenn der Sammel-Modus AN ist und trotzdem kein Material
    dieses Durchgangs da ist. Ist der Sammel-Modus AUS, bleibt es beim Hinweis
    in der Spalte: dann waere eine erneute Analyse Arbeit fuer nichts, weil die
    Bilder gleich wieder weggeraeumt wuerden."""
    n = dict(nachanalyse or {})
    if n.get("laeuft"):
        return ('<div class="rt-kopfknopf laeuft">'
                '<b><span class="rt-lauf"></span>Re-analysing this '
                "walk-through</b>"
                f'<div class="rt-q">{n.get("fertig", 0)} of '
                f'{n.get("gesamt", 0)} events done &mdash; the judged images '
                "are collected along the way, this takes a few minutes. It is "
                "quiet: no alerts, no notifications. This page refreshes "
                "itself.</div></div>")
    if not _fehlt_material(sicht):
        return ""
    return ('<div class="rt-kopfknopf">'
            '<b>Nothing was kept for this walk-through</b>'
            '<div class="rt-q">Analysing it again brings the judged images '
            "back &mdash; and that fills all three paths, not just vision. It "
            "runs the ordinary analysis over the events of this pass once "
            "more: quiet, without alerts, and it waits for live recognition "
            "instead of pushing it aside.</div>"
            '<div style="margin-top:8px">'
            '<button class="gtb on" onclick="rtNachanalyse(this)">Analyse this '
            "walk-through again</button> "
            '<span id="rt-nach-status" class="dim"></span></div></div>')


def _felder(lf):
    """Die zwei Stellschrauben DIESES Laufs (.164, User 09.08.): Zellenzahl und
    Bestaetigungen.

    Sie sind bewusst KEINE Einstellung — sie werden nirgends gespeichert, die
    Automatik faehrt weiter mit den Werten aus den Einstellungen. Deshalb steht
    "for this run" an beiden und der Hinweis darunter. Vorbelegt sind beide mit
    genau den Config-Werten.

    OBERGRENZEN (.170): die Bestaetigungen deckelt die Wirklichkeit dieses
    Durchgangs — mehr Vergleiche, als es Herausforderer-Galerien gibt, kann
    niemand fahren. Die ZELLENZAHL deckelt sie nicht mehr: bis .169 war ihr
    Maximum die Zahl der brauchbaren Bilder, und ein Durchgang mit einem
    einzigen Bild belegte das Feld mit 1 — der Testlauf fuhr dann `cells=1/1`,
    obwohl die Automatik denselben Durchgang mit dem Config-Wert gefahren
    haette (User-Fund 09.08.). Ein Test, der stillschweigend andere Regeln
    faehrt als der Betrieb, taugt nicht zum Vergleich. Zuwenig Material
    verschwindet dadurch nicht aus der Anzeige: der Satz darunter nennt die
    brauchbaren Bilder, und das Gitter wird schlicht kleiner."""
    lf = dict(lf or {})
    if not lf:
        return ""
    z_max = int(lf.get("zellen_max") or 1)
    v_max = int(lf.get("voten_max") or 1)
    z = max(1, min(z_max, int(lf.get("zellen") or 1)))
    v = max(1, min(v_max, int(lf.get("voten") or 1)))
    dl = " checked" if lf.get("doppellauf", True) else ""
    return (f'<div class="rt-felder">'
            f'<label>grid cells for this run'
            f'<input type="number" id="rt-zellen" min="1" max="{z_max}" '
            f'value="{z}"></label>'
            f'<label>confirmations needed for this run'
            f'<input type="number" id="rt-voten" min="1" max="{v_max}" '
            f'value="{v}"></label>'
            f'<label><input type="checkbox" id="rt-doppel"{dl}> ask each pair '
            "twice (swap check)</label></div>"
            f'<div class="rt-q">All three apply to THIS run only &mdash; nothing is '
            f"saved and normal operation keeps its own settings. This "
            f'walk-through has {lf.get("material", 0)} usable picture(s) '
            "&mdash; asking for more cells than that is fine, the grid just "
            f'gets smaller. {lf.get("galerien", 0)} approved galleries allow '
            f"at most {v_max} "
            "comparison(s). With the swap check on, a comparison costs two "
            "requests; without it, one &mdash; and it then rests on a single "
            "answer.</div>")


def _laeufe(laeufe):
    """Die bisherigen Laeufe dieses Durchgangs nebeneinander (.164).

    Damit sieht man, was eine andere Zellenzahl oder eine andere Zahl von
    Bestaetigungen wirklich geaendert hat — vorher stand immer nur der letzte
    Lauf da, und der Vergleich lag im Kopf des Nutzers."""
    if not laeufe:
        return ""
    zeilen = []
    for e in laeufe:
        if e.get("person"):
            erg = f'<span class="rt-ja">{html.escape(str(e["person"]))}</span>'
        elif e.get("abgebrochen"):
            erg = '<span class="rt-nein">aborted (service restarted)</span>'
        else:
            erg = ('<span class="rt-nein">no verdict</span>'
                   + (f' &middot; {html.escape(str(e.get("grund") or ""))[:60]}'
                      if e.get("grund") else ""))
        zellen = e.get("zellen")
        # Die GEWUENSCHTE Zahl steht daneben, wenn sie gekappt wurde — sonst
        # sieht ein Versuch mit 8 Zellen aus wie einer mit 3.
        if e.get("zellen_gewollt") and e.get("zellen_gewollt") != zellen:
            zellen = f'{zellen} <span class="dim">of {e["zellen_gewollt"]}</span>'
        voten_regel = e.get("min_voten_wirksam")
        if e.get("min_voten") and e.get("min_voten") != voten_regel:
            voten_regel = (f'{voten_regel} <span class="dim">of '
                           f'{e["min_voten"]}</span>')
        # .165: ohne Tauschlauf gewertet — das gehoert an die Zeile, sonst
        # vergleicht man zwei Laeufe, die nach verschiedenen Regeln entstanden
        # sind, als waeren sie gleich. Alt-Zeilen (None) behaupten nichts.
        if e.get("doppellauf") is False:
            voten_regel = (f'{voten_regel} <span class="vw-warn">no swap'
                           "</span>")
        zeilen.append(
            "<tr>"
            f'<td>{_zeit(e.get("ts"), "%d.%m. %H:%M:%S")}'
            + ("" if e.get("manuell") else ' <span class="dim">auto</span>')
            + "</td>"
            f'<td>{zellen if zellen is not None else "&mdash;"}</td>'
            f'<td>{voten_regel if voten_regel is not None else "&mdash;"}</td>'
            f'<td>{html.escape(str(e.get("backend") or "&mdash;"))}</td>'
            f'<td class="rt-grund">{erg}</td>'

            f'<td>{e.get("voten") if e.get("voten") is not None else "&mdash;"}'
            f' / {e.get("vergleiche") if e.get("vergleiche") is not None else "&mdash;"}'
            + (f' <span class="vw-warn">+{e["offen"]} open</span>'
               if e.get("offen") else "") + "</td>"
            f'<td>{e.get("anfragen") if e.get("anfragen") is not None else "&mdash;"}</td>'
            f'<td>{e.get("dauer_s") if e.get("dauer_s") is not None else "&mdash;"} s</td>'
            "</tr>")
    return ('<div class="rt-hist"><b>Runs on this walk-through</b>'
            '<div class="rt-htab">'
            "<table><tr><th>when</th><th>cells</th><th>needed</th>"
            "<th>backend</th><th>verdict</th><th>votes</th><th>req</th>"
            "<th>time</th></tr>"
            + "".join(zeilen) + "</table></div>"
            '<div class="rt-q">Newest first. Only what was really run &mdash; '
            "the list comes from this walk-through's own log and disappears "
            "with it.</div></div>")


def _vision(v, pass_key, laeuft, fehlt_material=False, lauffeld=None,
            laeufe=()):
    if not v.get("konfiguriert"):
        return ('<div class="rt-s"><h3>Vision</h3>'
                '<div class="rt-q">a vision model comparing this pass against '
                "your galleries</div>"
                '<div class="rt-erg"><span class="dim">not configured</span>'
                "</div>"
                '<div class="rt-q">Set it up under <a href="/vision">Vision '
                "detect</a>: a model, a green connection test and at least two "
                "approved galleries. The other two columns work without "
                "it.</div></div>")
    z = v.get("zeile") or {}
    schritte = v.get("schritte") or []
    laeuft = bool(laeuft or v.get("laeuft"))
    # KNOPF-PRIORITAET (User 09.08.: "den Knopf uebersieht man leider").
    # Solange kein Material da ist, kann dieser Lauf nur scheitern — er wird
    # deshalb ausgegraut und sagt kurz, warum. Der gruene Primaer-Knopf ist
    # dann der zentrale "analyse again" im Kopf. Sobald Material da ist, ist
    # dieser hier wieder der gruene.
    if fehlt_material:
        knopf = ('<button class="gtb" disabled title="there is nothing to '
                 'compare yet">Run vision on this pass</button> '
                 '<span class="dim">nothing to compare yet &mdash; analyse '
                 "this walk-through again first (button above)</span>")
    else:
        knopf = (_felder(lauffeld)
                 + '<button class="gtb on" onclick="rtVision(this)">Run vision '
                 "on this pass</button> "
                 '<span id="rt-vision-status" class="dim"></span>')
    if laeuft:
        knopf = ('<span class="dim">a run is going right now &mdash; the log '
                 "below grows as it works</span>")
    if laeuft:
        # LAUFEND: kein Urteil behaupten, sondern zeigen, wo der Lauf steht.
        letzte = (schritte[-1].get("text") if schritte else
                  "starting &mdash; nothing reported yet")
        return ('<div class="rt-s"><h3>Vision</h3>'
                '<div class="rt-q">forced choice against your galleries: the '
                "whole walk-through goes in as ONE candidate grid, and "
                "every pair is asked twice with the galleries swapped"
                "</div>"
                '<div class="rt-erg"><span class="rt-lauf"></span>'
                f'{html.escape(str(letzte))}</div>'
                + _log(schritte, True)
                + f'<div style="margin-top:8px">{knopf}</div>'
                + _laeufe(laeufe) + "</div>")
    if not z:
        return ('<div class="rt-s"><h3>Vision</h3>'
                '<div class="rt-q">forced choice against your galleries: the '
                "whole walk-through goes in as ONE candidate grid, and "
                "every pair is asked twice with the galleries swapped"
                "</div>"
                '<div class="rt-erg"><span class="dim">not run for this '
                "pass</span></div>"
                f'<div style="margin-top:8px">{knopf}</div>'
                + _laeufe(laeufe) + "</div>")
    gegen = ""
    for r in reversed(z.get("runden") or []):
        if r.get("a"):
            gegen = ('<div class="rt-q">compared '
                     + html.escape(str(r["a"])) + " against "
                     + html.escape(str(r["b"]))
                     + " &mdash; it says nothing about anyone else</div>")
            break
    if z.get("person"):
        erg, kl = html.escape(z["person"]), "ja"
    elif z.get("abgebrochen"):
        # .164: ein Lauf, den ein Dienst-Neustart mitten drin erwischt hat, ist
        # KEIN Fehlschlag der Erkennung — er ist gar nicht zu Ende gekommen.
        # Das gehoert als eigener Zustand hin, sonst liest man ein "kein
        # Urteil", das nie eines war.
        erg = ('<span class="dim">run aborted &mdash; the service '
               "restarted</span>")
        kl = "nein"
    else:
        erg = ('<span class="dim">no verdict &mdash; '
               + html.escape(_vis.grund_text(z.get("grund"))) + "</span>")
        kl = "nein"
    s = z.get("sammlung") or {}
    quelle = z.get("reihenfolge_quelle")
    return (f'<div class="rt-s {kl}"><h3>Vision</h3>'
            '<div class="rt-q">forced choice against your galleries: the whole '
            "walk-through goes in as ONE candidate grid, and every pair is "
            "asked twice with the galleries swapped</div>"
            f'<div class="rt-erg">{erg}</div>{gegen}'
            + _gitter(z, pass_key)
            + _runden(z)
            + f'<div class="rt-q">{s.get("voten", 0)} of {s.get("bilder", 0)} '
            f'comparison(s) gave an answer &middot; {z.get("anfragen", 0)} '
            f'requests &middot; {z.get("dauer_s")} s &middot; run '
            f'{_zeit(z.get("ts"))}'
            + (f' &middot; order: {html.escape(str(quelle))}' if quelle else "")
            + (" &middot; custom prompt" if z.get("custom_prompt") else "")
            + "</div>"
            + _offen(z)
            + _log(schritte, False)
            + f'<div style="margin-top:8px">{knopf}</div>'
            + _laeufe(laeufe) + "</div>")


def _offen(z):
    """Die unentschiedenen Vergleiche (.162). Seit die Kaskade bei einer
    Enthaltung weiterlaeuft, kann neben einem Urteil ein Paar stehen, das gar
    nichts entschieden hat — das gehoert sichtbar daneben, nicht nur ins Log.
    Der Wortlaut kommt aus core.visionurteil.offen_satz (EINE Quelle)."""
    offen = z.get("offen") or []
    if not offen:
        return ""
    return (f'<div class="vw-warn rt-q">{html.escape(_vu.offen_satz(offen))}'
            "</div>")


def seite(passe, pass_key="", sicht=None, laeuft=False, kosten=None,
          nachanalyse=None, lauffeld=None, laeufe=()):
    """Der Seiten-INHALT. `sicht` = core.visionurteil.dreiwege(...)."""
    teile = [STIL, _kopf(KOSTEN if kosten is None else kosten),
             _passliste(passe, pass_key)]
    if not pass_key or not sicht:
        return "".join(teile)
    fehlt = _fehlt_material(sicht)
    teile.append('<div class="card"><b>2 &middot; What the three paths say'
                 "</b>"
                 '<div class="dim">Same pass, three independent judgements. '
                 "They are allowed to disagree &mdash; that is the point of "
                 "looking at them together.</div>"
                 # Der zentrale Knopf steht im KOPF des Durchgangs, ueber den
                 # drei Spalten (User 09.08.) — er betrifft alle drei Wege.
                 + _nachanalyse_kopf(sicht, nachanalyse)
                 + '<div class="rt-w">'
                 + _gesicht(sicht["gesicht"])
                 + _koerper(sicht["koerper"], pass_key)
                 + _vision(sicht["vision"], pass_key, laeuft, fehlt,
                           lauffeld, laeufe)
                 + "</div></div>"
                 f'<script>const RT_PASS = "{html.escape(pass_key, quote=True)}";'
                 "</script>")
    return "".join(teile)
