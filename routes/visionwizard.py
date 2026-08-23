"""routes/visionwizard — "Build a gallery" (konzept_vision.md v2 §6, Zug V2).

Der Wizard fuehrt in vier sichtbaren Schritten:

  1 Person waehlen — nur Leute MIT gelerntem Koerpermodell, und mit ehrlichen
    Deckungs-Zahlen daneben (wie viele Bilder je Ansicht wirklich da sind).
  2 Groesse waehlen — 6 oder 12 (E11; 9/15/18/24 entfallen, die Messreihe hat
    gezeigt, dass die Groesse in keinem Szenario der Hebel war). Vorbelegt ist,
    was das Material hergibt.
  3 Vorschlag pruefen — ein echtes Bild-Raster, ZEILE JE ANSICHT (vorn /
    seitlich / hinten), je Zeile nach Guete sortiert. Jede Zelle hat einen
    Klick "does not fit"; dann rueckt der naechstbeste Kandidat DERSELBEN
    Ansicht nach. Geliehene Zellen und Luecken stehen als Klartext an der
    Zeile, nie stillschweigend.
  4 Abnehmen — die Galerie wird als KOPIE gespeichert (§6.6), mit
    Herkunfts-Manifest und Hashes.

Kontrakt wie alle routes-Module: reiner Renderer, Daten als Parameter, kein
Dienst-Import. Die Bilder kommen ueber die BESTEHENDE Crop-Route des
Person-Learn-Bereichs — dafuer muss kein zweiter Auslieferungsweg entstehen.

Sprach-Stufe 2 (Tranche C, konzept_sprache.md v2): sichtbare Texte aus
core/sprache.t() — BYTE-TREU (Harnisch tools/harnisch_sprache.py). Die
§8.1-Saetze (<b>not</b>-Groessensatz, Forget-them-Link, does-not-fit-Absatz)
sind seit Stufe 3 t_html-Schluessel. Verbleibende Grenzen (Kommentar je
Fundstelle): Datumsformat %Y-%m-%d (B19), begruendung/auffrischung kommen
fertig aus core/visiongalerie bzw. vom Handler (zentrale Quellen).
Wiederverwendet: vision.zeit.nie, vision.galerien.keine,
vision.galerien.zahl (byte-identische Texte des Vision-Reiters).
"""
import html
import json
import time
import urllib.parse

from core.sprache import t, t_html
# Tranche D (Kennung/Anzeige-Trennung 3b): Reihen-ANZEIGE aus Schluesseln;
# die Kennungen (vorn/seitlich/hinten/unklar) und der reihen_text-Daten-
# Vertrag der Aufrufer bleiben unveraendert.
from webui.bausteine import reihen_wort


def _zeit(ts):
    # Datumsformat bleibt in der Route (B19-Stufe); nur das Wort ist Text.
    if not ts:
        return t("vision.zeit.nie")
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))


def _bild_src(lauf_id, datei):
    return ("/personlauf/bild/" + urllib.parse.quote(str(lauf_id)) + "/"
            + urllib.parse.quote(str(datei)))


STIL = """<style>
 .vw-p { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
   gap:10px; margin-top:8px; }
 .vw-pk { text-align:left; padding:10px 12px; border-radius:10px; cursor:pointer;
   background:var(--surface-2); border:1px solid var(--border); color:var(--text);
   font:inherit; }
 .vw-pk:hover { border-color:var(--accent); }
 .vw-pk.on { border-color:var(--ok); box-shadow:inset 0 0 0 1px var(--ok); }
 .vw-pk b { font-size:15px; }
 .vw-pk .vw-pz { display:block; color:var(--dim); font-size:12px; margin-top:3px; }
 .vw-reihe { margin-top:14px; }
 .vw-kopf { display:flex; flex-wrap:wrap; gap:10px; align-items:baseline; }
 .vw-kopf b { font-size:15px; }
 /* Hochkant-Crops (~0,4) in breiten Zellen sahen aus wie Briefmarken in
    grauen Rahmen — die Zelle folgt deshalb ungefaehr dem Crop-Verhaeltnis
    (Deckel 170 px breit, 300 px hoch) statt der vollen Spaltenbreite. */
 .vw-raster { display:grid; gap:10px; margin-top:6px; justify-content:start;
   grid-template-columns:repeat(auto-fill,minmax(140px,170px)); }
 .vw-z { position:relative; border-radius:8px; overflow:hidden;
   background:var(--surface-2); border:2px solid var(--border); }
 .vw-z.geliehen { border-color:var(--warn); }
 .vw-z.leer { border-style:dashed; min-height:300px; display:flex;
   align-items:center; justify-content:center; text-align:center;
   color:var(--dim); font-size:12px; padding:10px; }
 .vw-b { height:300px; display:flex; align-items:center; justify-content:center;
   background:rgba(0,0,0,.25); }
 .vw-b img { max-width:100%; max-height:100%; }
 .vw-m { font-size:11px; color:var(--dim); padding:5px 6px; line-height:1.35; }
 .vw-x { position:absolute; top:4px; right:4px; border:0; border-radius:6px;
   padding:3px 7px; cursor:pointer; background:var(--surface);
   border:1px solid var(--border); color:var(--text); font-size:11px; }
 .vw-x:hover { border-color:var(--crit,#c44); color:var(--crit,#c44); }
 .vw-warn { color:var(--warn); font-size:12px; }
</style>"""


def _kopf(schritt):
    schritte = (t("visionwizard.schritt.person"), t("visionwizard.schritt.groesse"),
                t("visionwizard.schritt.vorschlag"), t("visionwizard.schritt.abnahme"))
    zeile = " &rarr; ".join(
        (f"<b>{i + 1} {s}</b>" if i == schritt else
         f'<span class="dim">{i + 1} {s}</span>')
        for i, s in enumerate(schritte))
    return (f"<h2>{t('visionwizard.titel')}</h2>"
            f'<p class="sub">{t("visionwizard.kopf.satz")}</p>'
            f'<div class="card">{zeile}</div>')


def _personen(deckung, galerien, gewaehlt, rt):
    karten = []
    for d in deckung:
        g = (galerien or {}).get(d["person"])
        # "no gallery yet" wiederverwendet (byte-identisch zum Vision-Reiter).
        stand = (t("visionwizard.person.stand_gut",
                   zeit=_zeit(g.get("abnahme_ts"))) if g
                 else t("vision.galerien.keine"))
        reihen = " &middot; ".join(
            f"{html.escape(reihen_wort(r))} {d['je_reihe'].get(r, 0)}"
            for r in ("vorn", "seitlich", "hinten"))
        if not d["max_groesse"]:
            karten.append(
                f'<div class="vw-pk" style="opacity:.6"><b>{html.escape(d["person"])}</b>'
                f'<span class="vw-pz">{t("visionwizard.person.zu_wenig", n=d["gesamt"])}'
                f'<br>{reihen}</span></div>')
            continue
        # Zahlen-Zeile wiederverwendet (vision.galerien.zahl, byte-identisch).
        karten.append(
            f'<button class="vw-pk{" on" if d["person"] == gewaehlt else ""}" '
            f'onclick="location.href=\'/vision/galerie?person='
            f'{urllib.parse.quote(d["person"])}\'">'
            f'<b>{html.escape(d["person"])}</b>'
            f'<span class="vw-pz">{stand}<br>{t("vision.galerien.zahl", n=d["gesamt"], reihen=reihen)}'
            f'<br>{t("visionwizard.person.max_gitter", n=d["max_groesse"])}</span></button>')
    return (f'<div class="card"><b>{t("visionwizard.person.titel")}</b>'
            f'<div class="dim">{t("visionwizard.person.satz")}</div>'
            f'<div class="vw-p">{"".join(karten)}</div></div>')


def _groessen(groessen, gewaehlt, empfehlung, person):
    knoepfe = "".join(
        f'<a class="gtb{" on" if g == gewaehlt else ""}" '
        f'href="/vision/galerie?person={urllib.parse.quote(person)}&groesse={g}">'
        f'{t("visionwizard.groesse.zellen", n=g)}</a> ' for g in groessen)
    # Stufe 3 (t_html): <b>not</b> mitten im Erklaersatz; {empfehlung}
    # escapt t_html selbst (Zahl aus dem Kurator).
    return (f'<div class="card"><b>{t("visionwizard.groesse.titel")}</b>'
            f"<div>{knoepfe}</div>"
            f'<div class="dim">{t_html("visionwizard.groesse.satz", empfehlung=empfehlung)}</div></div>')


def _zelle(z, i, rt):
    if not z:
        return f'<div class="vw-z leer">{t("visionwizard.zelle.leer")}</div>'
    # Die Begruendungszeile kommt FERTIG aus core/visiongalerie (Kurator, .161)
    # und wird hier nur ausgegeben. Sie wird NICHT hier zusammengesetzt: derselbe
    # Satz an zwei Stellen zu bauen (Server und Browser) hat in diesem Projekt
    # schon einmal zwei Fassungen erzeugt. Faellt sie aus, bleibt die alte
    # Kurzfassung als Rueckfallebene.
    meta = html.escape(str(z.get("begruendung") or "")) or " &middot; ".join(
        html.escape(str(x)) for x in (z.get("tag") or "?",
                                      z.get("camera") or "?",
                                      f"{z.get('hoehe')} px"))
    geliehen = ""
    if z.get("geliehen_aus"):
        geliehen = ('<div class="vw-warn">'
                    f'{t("visionwizard.zelle.geliehen", reihe=html.escape(reihen_wort(z["geliehen_aus"])))}'
                    "</div>")
    return (f'<div class="vw-z{" geliehen" if z.get("geliehen_aus") else ""}" '
            f'id="vwz_{i}">'
            f'<button class="vw-x" onclick="vwWeg({i})">{t("visionwizard.zelle.knopf_weg")}</button>'
            f'<div class="vw-b"><img loading="lazy" '
            f'src="{_bild_src(z["lauf_id"], z["datei"])}"></div>'
            f'<div class="vw-m">{meta}{geliehen}</div></div>')


def _vorschlag(v, person, abgelehnt_n, reihen_text):
    stuecke, flach, i = [], [], 0
    for zl in v["zeilen"]:
        zellen = []
        for z in zl["zellen"]:
            zellen.append(_zelle(z, i, reihen_text))
            flach.append({"reihe": zl["reihe"], "spalte": z["spalte"] if z else None,
                          "schluessel": (f'{z["lauf_id"]}/{z["datei"]}'
                                         if z else None)})
            i += 1
        anmerkung = []
        if zl["geliehen"]:
            anmerkung.append(
                f'<span class="vw-warn">{t("visionwizard.reihe.geliehen", n=zl["geliehen"], reihe=reihen_wort(zl["reihe"]))}</span>')
        if zl["luecken"]:
            anmerkung.append(f'<span class="vw-warn">{t("visionwizard.reihe.luecken", n=zl["luecken"])}</span>')
        # Die Spreizung steht als ZAHL da (Kurator .161): der Nutzer sieht ohne
        # Nachzaehlen, ob die Reihe wirklich verschiedene Tage und Kameras zeigt
        # — das ist die Eigenschaft, die der gemessene Prompt den Modellen
        # zusagt ("taken on different days").
        spreiz = ""
        if zl.get("tage") or zl.get("kameras"):
            spreiz = (f'<span class="dim">{t("visionwizard.reihe.spreizung", tage=len(zl.get("tage") or []), kameras=len(zl.get("kameras") or []))}</span>')
        stuecke.append(
            f'<div class="vw-reihe"><div class="vw-kopf">'
            f'<b>{t("visionwizard.reihe.kopf", reihe=reihen_wort(zl["reihe"]))}</b>'
            f'<span class="dim">{t("visionwizard.reihe.eigene", eigene=zl["eigene"], gesamt=len(zl["zellen"]))}</span>{spreiz}{" ".join(anmerkung)}</div>'
            f'<div class="vw-raster">{"".join(zellen)}</div></div>')
    gedaechtnis = ""
    if abgelehnt_n:
        # Stufe 3 (t_html): der Forget-them-Satz mit <a>-Link mitten im
        # Satz (onclick-Attribut ist Teil der gepinnten Tag-Folge).
        gedaechtnis = ('<div class="dim">'
                       + t("visionwizard.vorschlag.abgelehnt", n=abgelehnt_n)
                       + f' {t_html("visionwizard.vorschlag.vergessen_satz")}</div>')
    # Stufe 3 (t_html): <b>does not fit</b> mitten im Erklaerabsatz —
    # zitiert visionwizard.zelle.knopf_weg (Kopplung am Schluessel).
    return (f'<div class="card"><b>{t("visionwizard.vorschlag.titel")}</b>'
            f'<div class="dim">{t_html("visionwizard.vorschlag.satz")}</div>'
            f'<div class="dim">{t("visionwizard.vorschlag.grenze")}</div>'
            + gedaechtnis + "".join(stuecke)
            + '<div style="margin-top:14px">'
            f'<button class="gtb on" onclick="vwAbnehmen(this)">{t("visionwizard.vorschlag.knopf")}</button> '
            '<span id="vw-status" class="dim"></span></div>'
            f'<div class="dim" style="margin-top:6px">{t("visionwizard.vorschlag.kopie_satz")}</div></div>'
            f'<script>const VW_PERSON = {json.dumps(person)};'
            f'const VW_GROESSE = {v["groesse"]};'
            f'const VW_ZELLEN = {json.dumps(flach)};</script>')


def _fertig(g, pruef, person, rt):
    zeilen = []
    for e in g.get("zellen") or []:
        if e.get("leer"):
            continue
        zeilen.append(
            f'<div class="vw-z"><div class="vw-b"><img loading="lazy" '
            f'src="/vision/galerie/bild/{urllib.parse.quote(person)}/'
            f'{urllib.parse.quote(e["datei"])}"></div>'
            f'<div class="vw-m">'
            f'{html.escape(reihen_wort(e["reihe"]) if e.get("reihe") else "")}'
            f'{t("visionwizard.fertig.geliehen") if e.get("geliehen_aus") else ""}</div></div>')
    warnung = ""
    if pruef.get("status") != "gut":
        warnung = f'<div class="vw-warn">{html.escape(pruef.get("text") or "")}</div>'
    return (f'<div class="card"><b>{t("visionwizard.fertig.titel")}</b>'
            f'<div>{t("visionwizard.fertig.stand", zellen=g.get("groesse"), zeit=_zeit(g.get("abnahme_ts")))}</div>' + warnung
            + f'<div class="dim">{t("visionwizard.fertig.satz")}</div>'
            f'<div class="vw-raster">{"".join(zeilen)}</div>'
            '<div style="margin-top:10px"><a class="gtb" '
            f'href="/vision/galerie?person={urllib.parse.quote(person)}&neu=1">'
            f'{t("visionwizard.fertig.knopf_neu")}</a> '
            f'<a class="gtb" href="/vision">{t("visionwizard.fertig.knopf_zurueck")}</a></div>'
            "</div>")


def seite(deckung, galerien, person="", groesse=None, vorschlag=None,
          groessen=(6, 12), empfehlung=0, abgelehnt_n=0, fertig=None,
          pruefung=None, auffrischung="", reihen_text=None):
    """Der Seiten-INHALT. `fertig` = das Herkunfts-Manifest, wenn diese Person
    schon eine abgenommene Galerie hat und nicht gerade neu gebaut wird."""
    rt = dict(reihen_text or {})
    if not person:
        return STIL + _kopf(0) + _personen(deckung, galerien, person, rt)
    teile = [STIL, _kopf(2 if vorschlag else 1),
             _personen(deckung, galerien, person, rt)]
    if auffrischung:
        # Angebot, kein Automatismus (§6.6): neue Lernlaeufe tauschen NIE still
        # eine abgenommene Galerie aus. Der auffrischung-Text kommt fertig vom
        # Handler (zentrale Quelle, eigene Tranche).
        teile.append('<div class="card" style="border-left-color:var(--warn)">'
                     f"<b>{t('visionwizard.neu.titel')}</b><div>{auffrischung}</div>"
                     f'<div class="dim">{t("visionwizard.neu.satz")}</div></div>')
    if fertig:
        teile.append(_fertig(fertig, pruefung or {}, person, rt))
        return "".join(teile)
    teile.append(_groessen(groessen, groesse, empfehlung, person))
    if vorschlag:
        teile.append(_vorschlag(vorschlag, person, abgelehnt_n, rt))
    return "".join(teile)
