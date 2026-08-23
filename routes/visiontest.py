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

Sprach-Stufe 2 (Tranche C, konzept_sprache.md v2): sichtbare Texte aus
core/sprache.t() — BYTE-TREU (Harnisch tools/harnisch_sprache.py). Die
beiden §8.1-Saetze (<b>face/person/vision</b>-Kopf, Vision-Einrichten-Link)
sind seit Stufe 3 t_html-Schluessel. Verbleibende Grenzen (Kommentar je
Fundstelle): Datumsformate %d.%m./%H:%M:%S (B19), Grund-/offen-Texte aus
core/vision bzw. core/visionurteil (zentrale Quellen). Die frueher modulweite
KOSTEN-Konstante ist nach §8.12 (t() nie auf Modulebene) in den
seite()-Aufruf gewandert — Muster "Funktion statt Konstante".
"""
import html
import time
import urllib.parse

from core.sprache import t, t_html

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
    # Datumsformate bleiben in der Route (B19-Stufe); "—" ist sprachneutral.
    if not ts:
        return "—"
    return time.strftime(form, time.localtime(float(ts)))


def _kopf(kosten):
    # Stufe 3 (t_html): der erste Satz mit <b>face/person/vision</b>.
    return (f"<h2>{t('visiontest.titel')}</h2>"
            f'<p class="sub">{t_html("visiontest.kopf.wege_satz")} '
            f'{t("visiontest.kopf.satz")}'
            f"</p><div class=\"card\">{kosten}</div>")


def _wer(p):
    """Wer in diesem Durchgang erkannt wurde &mdash; EINE Formulierung fuer die
    Kachel und fuer die Kopfzeile des gewaehlten Durchgangs."""
    return ", ".join(sorted(p.get("personen") or [])) or t("visiontest.wer.niemand")


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
            f'<small>{t("visiontest.wahl.kachel_zahlen", events=p.get("events") or 0, kameras=p.get("kameras") or 0)}'
            + (t("visiontest.wahl.vision_fertig") if p.get("vision") else "")
            + "</small></button>")
    if not karten:
        return (f'<div class="card"><b>{t("visiontest.wahl.titel")}</b>'
                f'<div class="dim">{t("visiontest.wahl.leer")}</div></div>')
    gew = next((p for p in passe or [] if p["pass_key"] == gewaehlt), None)
    if gew:
        # Die schmale Kopfzeile des gewaehlten Durchgangs. Genau die Angaben der
        # Kachel, nur in einer Zeile — nichts wird hier neu behauptet.
        kopf = (f'<b>{_zeit(gew.get("start"))} &middot; '
                f'{html.escape(_wer(gew))}</b>'
                f'<span class="rt-meta">{t("visiontest.wahl.kopf_zahlen", events=gew.get("events") or 0, kameras=gew.get("kameras") or 0)}</span>'
                f'<span class="rt-mehr">{t("visiontest.wahl.anderer")}</span>')
    elif gewaehlt:
        # Gewaehlt, aber nicht in der Liste (aelter als die gezeigten Tage):
        # dann behauptet die Kopfzeile nichts ueber ihn.
        kopf = (f'<b>{t("visiontest.wahl.titel")}</b>'
                f'<span class="rt-mehr">{t("visiontest.wahl.anderer")}</span>')
    else:
        kopf = (f'<b>{t("visiontest.wahl.titel_offen")}</b>'
                f'<span class="rt-meta">{t("visiontest.wahl.anzahl", n=len(karten))}</span>')
    return ('<div class="card">'
            f'<details class="rt-wahl"{"" if gewaehlt else " open"}>'
            f"<summary>{kopf}</summary>"
            f'<div class="dim">{t("visiontest.wahl.satz")}</div>'
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
        + (html.escape(str(b["person"])) if b.get("person")
           else t("visiontest.gesicht.kein_match"))
        + (f' {b["score"]:.2f}' if isinstance(b.get("score"), (int, float))
           else "")
        + "</figcaption></figure>"
        for b in zeigen if b.get("eid") and b.get("datei"))
    hinweise = []
    if len(kacheln) > len(zeigen):
        hinweise.append(t("visiontest.gesicht.gezeigt",
                          gezeigt=len(zeigen), gesamt=len(kacheln)))
    if unbek > ohne_name:
        fehlt = unbek - ohne_name
        hinweise.append(t("visiontest.gesicht.ohne_bild",
                          fehlt=fehlt, unbek=unbek))
    if not kacheln:
        hinweise.append(t("visiontest.gesicht.kein_bild"))
    return ((f'<div class="rt-b">{bilder}</div>' if bilder else "")
            + (f'<div class="rt-q">{" &middot; ".join(hinweise)}</div>'
               if hinweise else ""))


def _gesicht(g):
    if g.get("personen"):
        erg = ", ".join(html.escape(p["person"]) for p in g["personen"])
        kl = "ja"
    else:
        erg, kl = f'<span class="dim">{t("visiontest.gesicht.keines")}</span>', "nein"
    # {best} vorformatiert (:.2f) — Formatspezifika nie in Werte (§8.8).
    li = "".join(
        f'<li>{t("visiontest.gesicht.zeile", person=html.escape(p["person"]), events=p.get("events"))}'
        + (t("visiontest.gesicht.best", best=f'{p["best"]:.2f}')
           if isinstance(p.get("best"), float)
           else "") + "</li>" for p in g.get("personen") or [])
    rest = ""
    if g.get("unbekannt"):
        rest = (f'<div class="rt-q">{t("visiontest.gesicht.unbekannt", n=g["unbekannt"])}</div>')
    return (f'<div class="rt-s {kl}"><h3>{t("visiontest.gesicht.titel")}</h3>'
            f'<div class="rt-q">{t("visiontest.gesicht.quelle")}</div>'
            f'<div class="rt-erg">{erg}</div>'
            f'<ul class="rt-liste">{li}</ul>{rest}'
            + _gesichtskacheln(g) + "</div>")


def _koerper(k, pass_key):
    if k.get("treffer"):
        namen = sorted({tr["person"] for tr in k["treffer"]})
        erg, kl = ", ".join(html.escape(n) for n in namen), "ja"
    elif k.get("personen"):
        erg = ('<span class="dim">'
               + t("visiontest.koerper.kandidaten",
                   liste=", ".join(f"{html.escape(n)} ({c})"
                                   for n, c in sorted(k["personen"].items())))
               + "</span>")
        kl = "nein"
    else:
        erg, kl = f'<span class="dim">{t("visiontest.koerper.nichts")}</span>', "nein"
    li = "".join(
        f'<li>{t("visiontest.koerper.zeile", klasse=html.escape(str(b.get("klasse") or "?")), score=b.get("score"), schwelle=b.get("schwelle"), quelle=html.escape(str(b.get("quelle") or "")))}'
        + ("" if b.get("bild") else
           f' &middot; <span class="dim">{t("visiontest.koerper.bild_weg")}</span>') + "</li>"
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
    return (f'<div class="rt-s {kl}"><h3>{t("visiontest.koerper.titel")}</h3>'
            f'<div class="rt-q">{t("visiontest.koerper.quelle")}</div>'
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
             f'</span>{t("visiontest.log.warte")}'
             "</li>" if offen else "")
    return (f'<div class="rt-log"><b>{t("visiontest.log.titel")}</b>'
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
            + f'" alt="{t("visiontest.gitter.alt")}">'
            f'<figcaption>{t("visiontest.gitter.bildunterschrift")}</figcaption>'
            "</figure>")
    bilder = "".join(
        '<figure><img loading="lazy" src="/person/kontrolle/bild/'
        + urllib.parse.quote(pass_key) + "/" + urllib.parse.quote(b["datei"])
        + f'"><figcaption>{b.get("hoehe")} px</figcaption></figure>'
        for b in zellen[:12] if b.get("datei"))
    return (f'<div class="rt-q">{t("visiontest.gitter.zeile", n=n)}'
            + (t("visiontest.gitter.luecken", n=luecken) if luecken else "")
            + f"</div>{voll}"
            + f'<div class="rt-b">{bilder}</div>')


def _runden(z):
    """Die gefahrenen Vergleiche — je Runde ein Paar, zwei Anfragen."""
    zeilen = []
    # Grund-Klartexte kommen aus core/vision.grund_text (zentrale Quelle).
    for r in z.get("runden") or []:
        wer = {"A": r.get("a"), "B": r.get("b")}.get(r.get("wahl"))
        erg = (html.escape(str(wer)) if wer and not r.get("kein_votum")
               else t("visiontest.runden.kein_votum",
                      grund=html.escape(_vis.grund_text(r.get("grund")))))
        dauer = f' &middot; {r["dauer_s"]} s' if r.get("dauer_s") else ""
        zeilen.append(f'<li>{t("visiontest.runden.paar", a=html.escape(str(r.get("a"))), b=html.escape(str(r.get("b"))))} &middot; {erg}{dauer}'
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
                f'<b><span class="rt-lauf"></span>{t("visiontest.nach.laeuft")}</b>'
                f'<div class="rt-q">{t("visiontest.nach.stand", fertig=n.get("fertig", 0), gesamt=n.get("gesamt", 0))}</div></div>')
    if not _fehlt_material(sicht):
        return ""
    return ('<div class="rt-kopfknopf">'
            f'<b>{t("visiontest.nach.titel")}</b>'
            f'<div class="rt-q">{t("visiontest.nach.satz")}</div>'
            '<div style="margin-top:8px">'
            f'<button class="gtb on" onclick="rtNachanalyse(this)">{t("visiontest.nach.knopf")}</button> '
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
            f'<label>{t("visiontest.felder.zellen")}'
            f'<input type="number" id="rt-zellen" min="1" max="{z_max}" '
            f'value="{z}"></label>'
            f'<label>{t("visiontest.felder.voten")}'
            f'<input type="number" id="rt-voten" min="1" max="{v_max}" '
            f'value="{v}"></label>'
            f'<label><input type="checkbox" id="rt-doppel"{dl}> {t("visiontest.felder.doppel")}</label></div>'
            f'<div class="rt-q">{t("visiontest.felder.satz", material=lf.get("material", 0), galerien=lf.get("galerien", 0), voten_max=v_max)}</div>')


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
            erg = f'<span class="rt-nein">{t("visiontest.laeufe.abgebrochen")}</span>'
        else:
            erg = (f'<span class="rt-nein">{t("visiontest.laeufe.kein_urteil")}</span>'
                   + (f' &middot; {html.escape(str(e.get("grund") or ""))[:60]}'
                      if e.get("grund") else ""))
        zellen = e.get("zellen")
        # Die GEWUENSCHTE Zahl steht daneben, wenn sie gekappt wurde — sonst
        # sieht ein Versuch mit 8 Zellen aus wie einer mit 3.
        if e.get("zellen_gewollt") and e.get("zellen_gewollt") != zellen:
            zellen = f'{zellen} <span class="dim">{t("visiontest.laeufe.von", n=e["zellen_gewollt"])}</span>'
        voten_regel = e.get("min_voten_wirksam")
        if e.get("min_voten") and e.get("min_voten") != voten_regel:
            voten_regel = (f'{voten_regel} <span class="dim">'
                           f'{t("visiontest.laeufe.von", n=e["min_voten"])}</span>')
        # .165: ohne Tauschlauf gewertet — das gehoert an die Zeile, sonst
        # vergleicht man zwei Laeufe, die nach verschiedenen Regeln entstanden
        # sind, als waeren sie gleich. Alt-Zeilen (None) behaupten nichts.
        if e.get("doppellauf") is False:
            voten_regel = (f'{voten_regel} <span class="vw-warn">{t("visiontest.laeufe.ohne_tausch")}'
                           "</span>")
        zeilen.append(
            "<tr>"
            f'<td>{_zeit(e.get("ts"), "%d.%m. %H:%M:%S")}'
            + ("" if e.get("manuell") else f' <span class="dim">{t("visiontest.laeufe.auto")}</span>')
            + "</td>"
            f'<td>{zellen if zellen is not None else "&mdash;"}</td>'
            f'<td>{voten_regel if voten_regel is not None else "&mdash;"}</td>'
            f'<td>{html.escape(str(e.get("backend") or "&mdash;"))}</td>'
            f'<td class="rt-grund">{erg}</td>'

            f'<td>{e.get("voten") if e.get("voten") is not None else "&mdash;"}'
            f' / {e.get("vergleiche") if e.get("vergleiche") is not None else "&mdash;"}'
            + (f' <span class="vw-warn">{t("visiontest.laeufe.offen", n=e["offen"])}</span>'
               if e.get("offen") else "") + "</td>"
            f'<td>{e.get("anfragen") if e.get("anfragen") is not None else "&mdash;"}</td>'
            f'<td>{e.get("dauer_s") if e.get("dauer_s") is not None else "&mdash;"} s</td>'
            "</tr>")
    return (f'<div class="rt-hist"><b>{t("visiontest.laeufe.titel")}</b>'
            '<div class="rt-htab">'
            f"<table><tr><th>{t('visiontest.laeufe.kopf_wann')}</th>"
            f"<th>{t('visiontest.laeufe.kopf_zellen')}</th>"
            f"<th>{t('visiontest.laeufe.kopf_noetig')}</th>"
            f"<th>{t('visiontest.laeufe.kopf_backend')}</th>"
            f"<th>{t('visiontest.laeufe.kopf_urteil')}</th>"
            f"<th>{t('visiontest.laeufe.kopf_voten')}</th>"
            f"<th>{t('visiontest.laeufe.kopf_anfragen')}</th>"
            f"<th>{t('visiontest.laeufe.kopf_zeit')}</th></tr>"
            + "".join(zeilen) + "</table></div>"
            f'<div class="rt-q">{t("visiontest.laeufe.satz")}</div></div>')


def _vision(v, pass_key, laeuft, fehlt_material=False, lauffeld=None,
            laeufe=()):
    if not v.get("konfiguriert"):
        return (f'<div class="rt-s"><h3>{t("visiontest.vision.titel")}</h3>'
                f'<div class="rt-q">{t("visiontest.vision.quelle_kurz")}</div>'
                f'<div class="rt-erg"><span class="dim">{t("visiontest.vision.unkonfiguriert")}</span>'
                "</div>"
                # Stufe 3 (t_html): <a>-Link mitten im Satz; "Vision detect"
                # zitiert nav.vision (Kopplung am Schluessel).
                f'<div class="rt-q">{t_html("visiontest.vision.einrichten_satz")}</div></div>')
    z = v.get("zeile") or {}
    schritte = v.get("schritte") or []
    laeuft = bool(laeuft or v.get("laeuft"))
    # KNOPF-PRIORITAET (User 09.08.: "den Knopf uebersieht man leider").
    # Solange kein Material da ist, kann dieser Lauf nur scheitern — er wird
    # deshalb ausgegraut und sagt kurz, warum. Der gruene Primaer-Knopf ist
    # dann der zentrale "analyse again" im Kopf. Sobald Material da ist, ist
    # dieser hier wieder der gruene.
    if fehlt_material:
        knopf = (f'<button class="gtb" disabled title="{t("visiontest.vision.attr_nichts")}">{t("visiontest.vision.knopf")}</button> '
                 f'<span class="dim">{t("visiontest.vision.nichts_satz")}</span>')
    else:
        knopf = (_felder(lauffeld)
                 + f'<button class="gtb on" onclick="rtVision(this)">{t("visiontest.vision.knopf")}</button> '
                 '<span id="rt-vision-status" class="dim"></span>')
    if laeuft:
        knopf = f'<span class="dim">{t("visiontest.vision.laeuft_satz")}</span>'
    if laeuft:
        # LAUFEND: kein Urteil behaupten, sondern zeigen, wo der Lauf steht.
        letzte = (schritte[-1].get("text") if schritte else
                  t("visiontest.vision.startet"))
        return (f'<div class="rt-s"><h3>{t("visiontest.vision.titel")}</h3>'
                f'<div class="rt-q">{t("visiontest.vision.quelle")}</div>'
                '<div class="rt-erg"><span class="rt-lauf"></span>'
                f'{html.escape(str(letzte))}</div>'
                + _log(schritte, True)
                + f'<div style="margin-top:8px">{knopf}</div>'
                + _laeufe(laeufe) + "</div>")
    if not z:
        return (f'<div class="rt-s"><h3>{t("visiontest.vision.titel")}</h3>'
                f'<div class="rt-q">{t("visiontest.vision.quelle")}</div>'
                f'<div class="rt-erg"><span class="dim">{t("visiontest.vision.nicht_gelaufen")}</span></div>'
                f'<div style="margin-top:8px">{knopf}</div>'
                + _laeufe(laeufe) + "</div>")
    gegen = ""
    for r in reversed(z.get("runden") or []):
        if r.get("a"):
            gegen = ('<div class="rt-q">'
                     + t("visiontest.vision.verglichen",
                         a=html.escape(str(r["a"])), b=html.escape(str(r["b"])))
                     + "</div>")
            break
    if z.get("person"):
        erg, kl = html.escape(z["person"]), "ja"
    elif z.get("abgebrochen"):
        # .164: ein Lauf, den ein Dienst-Neustart mitten drin erwischt hat, ist
        # KEIN Fehlschlag der Erkennung — er ist gar nicht zu Ende gekommen.
        # Das gehoert als eigener Zustand hin, sonst liest man ein "kein
        # Urteil", das nie eines war.
        erg = f'<span class="dim">{t("visiontest.vision.abgebrochen")}</span>'
        kl = "nein"
    else:
        erg = ('<span class="dim">'
               + t("visiontest.vision.kein_urteil",
                   grund=html.escape(_vis.grund_text(z.get("grund"))))
               + "</span>")
        kl = "nein"
    s = z.get("sammlung") or {}
    quelle = z.get("reihenfolge_quelle")
    return (f'<div class="rt-s {kl}"><h3>{t("visiontest.vision.titel")}</h3>'
            f'<div class="rt-q">{t("visiontest.vision.quelle")}</div>'
            f'<div class="rt-erg">{erg}</div>{gegen}'
            + _gitter(z, pass_key)
            + _runden(z)
            + f'<div class="rt-q">{t("visiontest.vision.bilanz", voten=s.get("voten", 0), bilder=s.get("bilder", 0), anfragen=z.get("anfragen", 0), dauer=z.get("dauer_s"), zeit=_zeit(z.get("ts")))}'
            + (t("visiontest.vision.reihenfolge", quelle=html.escape(str(quelle))) if quelle else "")
            + (t("visiontest.vision.custom_prompt") if z.get("custom_prompt") else "")
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
    """Der Seiten-INHALT. `sicht` = core.visionurteil.dreiwege(...).
    Der Kosten-Text kommt seit Tranche C zur Laufzeit aus t() — nie mehr
    als Modulkonstante (§8.12, Muster "Funktion statt Konstante")."""
    teile = [STIL,
             _kopf(t("visiontest.kosten") if kosten is None else kosten),
             _passliste(passe, pass_key)]
    if not pass_key or not sicht:
        return "".join(teile)
    fehlt = _fehlt_material(sicht)
    teile.append(f'<div class="card"><b>{t("visiontest.drei.titel")}</b>'
                 f'<div class="dim">{t("visiontest.drei.satz")}</div>'
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
