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
"""
import html
import json
import time
import urllib.parse


def _zeit(ts):
    if not ts:
        return "never"
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
    schritte = ("pick a person", "pick a size", "check the proposal", "approve")
    zeile = " &rarr; ".join(
        (f"<b>{i + 1} {s}</b>" if i == schritt else
         f'<span class="dim">{i + 1} {s}</span>')
        for i, s in enumerate(schritte))
    return ("<h2>Build a gallery</h2>"
            '<p class="sub">A gallery is a small grid of pictures of one '
            "person &mdash; that is what the vision model compares a new "
            "picture against. It is built from body images you already "
            "approved; nothing new is recorded and no video is opened.</p>"
            f'<div class="card">{zeile}</div>')


def _personen(deckung, galerien, gewaehlt, rt):
    karten = []
    for d in deckung:
        g = (galerien or {}).get(d["person"])
        stand = (f'gallery approved {_zeit(g.get("abnahme_ts"))}' if g
                 else "no gallery yet")
        reihen = " &middot; ".join(
            f"{html.escape(rt.get(r, r))} {d['je_reihe'].get(r, 0)}"
            for r in ("vorn", "seitlich", "hinten"))
        if not d["max_groesse"]:
            karten.append(
                f'<div class="vw-pk" style="opacity:.6"><b>{html.escape(d["person"])}</b>'
                f'<span class="vw-pz">{d["gesamt"]} usable images &mdash; not '
                "enough for a gallery yet. Run Person learn on more "
                f'walk-throughs.<br>{reihen}</span></div>')
            continue
        karten.append(
            f'<button class="vw-pk{" on" if d["person"] == gewaehlt else ""}" '
            f'onclick="location.href=\'/vision/galerie?person='
            f'{urllib.parse.quote(d["person"])}\'">'
            f'<b>{html.escape(d["person"])}</b>'
            f'<span class="vw-pz">{stand}<br>{d["gesamt"]} usable images '
            f"&middot; {reihen}<br>largest grid this material supports: "
            f'{d["max_groesse"]}</span></button>')
    return ('<div class="card"><b>1 &middot; Which person</b>'
            '<div class="dim">Only people with a learned body model appear '
            "here, and the counts are the images that pass the size filter "
            "(at least 350 pixels tall) &mdash; not everything that was ever "
            "harvested.</div>"
            f'<div class="vw-p">{"".join(karten)}</div></div>')


def _groessen(groessen, gewaehlt, empfehlung, person):
    knoepfe = "".join(
        f'<a class="gtb{" on" if g == gewaehlt else ""}" '
        f'href="/vision/galerie?person={urllib.parse.quote(person)}&groesse={g}">'
        f"{g} cells</a> " for g in groessen)
    return ('<div class="card"><b>2 &middot; How many pictures</b>'
            f"<div>{knoepfe}</div>"
            '<div class="dim">Measured, honestly: the size was <b>not</b> the '
            "lever in any of the cases we ran &mdash; a bigger grid did not "
            "make the answers better, and it did not make them worse either. "
            "Take the larger one if your material carries it "
            f"(here: {empfehlung}), the smaller one if it does not. Both cost "
            "about the same, because the canvas is what costs tokens, not the "
            "number of cells.</div></div>")


def _zelle(z, i, rt):
    if not z:
        return ('<div class="vw-z leer">no more images for this row &mdash; '
                "and nothing left to borrow either</div>")
    # Die Begruendungszeile kommt FERTIG aus core/visiongalerie (Kurator, .161)
    # und wird hier nur ausgegeben. Sie wird NICHT hier zusammengesetzt: derselbe
    # Satz an zwei Stellen zu bauen (Server und Browser) hat in diesem Projekt
    # schon einmal zwei Fassungen erzeugt. Faellt sie aus, bleibt die alte
    # Kurzfassung als Rueckfallebene.
    meta = html.escape(str(z.get("begruendung") or "")) or " &middot; ".join(
        html.escape(str(t)) for t in (z.get("tag") or "?",
                                      z.get("camera") or "?",
                                      f"{z.get('hoehe')} px"))
    geliehen = ""
    if z.get("geliehen_aus"):
        geliehen = (f'<div class="vw-warn">from the '
                    f'{html.escape(rt.get(z["geliehen_aus"], z["geliehen_aus"]))}'
                    " row</div>")
    return (f'<div class="vw-z{" geliehen" if z.get("geliehen_aus") else ""}" '
            f'id="vwz_{i}">'
            f'<button class="vw-x" onclick="vwWeg({i})">does not fit</button>'
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
                f'<span class="vw-warn">{zl["geliehen"]} filled from another '
                "view &mdash; there were not enough clean "
                f'{reihen_text.get(zl["reihe"], zl["reihe"])} images</span>')
        if zl["luecken"]:
            anmerkung.append(f'<span class="vw-warn">{zl["luecken"]} cell(s) '
                             "could not be filled at all</span>")
        # Die Spreizung steht als ZAHL da (Kurator .161): der Nutzer sieht ohne
        # Nachzaehlen, ob die Reihe wirklich verschiedene Tage und Kameras zeigt
        # — das ist die Eigenschaft, die der gemessene Prompt den Modellen
        # zusagt ("taken on different days").
        spreiz = ""
        if zl.get("tage") or zl.get("kameras"):
            spreiz = (f'<span class="dim">{len(zl.get("tage") or [])} day(s), '
                      f'{len(zl.get("kameras") or [])} camera(s)</span>')
        stuecke.append(
            f'<div class="vw-reihe"><div class="vw-kopf">'
            f'<b>{reihen_text.get(zl["reihe"], zl["reihe"])} view</b>'
            f'<span class="dim">{zl["eigene"]} of {len(zl["zellen"])} from this '
            f"view</span>{spreiz}{' '.join(anmerkung)}</div>"
            f'<div class="vw-raster">{"".join(zellen)}</div></div>')
    gedaechtnis = ""
    if abgelehnt_n:
        gedaechtnis = ('<div class="dim">' + str(abgelehnt_n) + " image(s) you "
                       "rejected earlier are remembered and will not come back. "
                       '<a href="#" onclick="vwVergessen();return false">Forget '
                       "them</a> if you want to start over.</div>")
    return ('<div class="card"><b>3 &middot; Does this fit?</b>'
            '<div class="dim">One row per view: front, side, back. Pictures are '
            "picked by size and sharpness, how clearly the eyes and nose are "
            "there, how much light is blown out, how much of the crop is "
            "actually the person &mdash; and spread over different days, "
            "events and cameras. The line under each picture says what was "
            "measured on it. Click <b>does not fit</b> on anything unusable "
            "&mdash; the next best picture of the SAME view moves up. This "
            "does not touch your learning material; it only says &bdquo;not as "
            "a gallery cell&ldquo;.</div>"
            '<div class="dim">Honest limit: those are measurements of the '
            "picture, not of the moment. A picture where someone is tying "
            "their hair or bending down looks fine to every one of them "
            "&mdash; that is what your eyes are for.</div>"
            + gedaechtnis + "".join(stuecke)
            + '<div style="margin-top:14px">'
            '<button class="gtb on" onclick="vwAbnehmen(this)">Approve this '
            "gallery</button> "
            '<span id="vw-status" class="dim"></span></div>'
            '<div class="dim" style="margin-top:6px">Approving copies these '
            "pictures into the gallery folder. From then on the gallery is "
            "fixed: deleting an original later cannot punch holes into it "
            "&mdash; suslik only asks you to approve it again.</div></div>"
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
            f'{html.escape(rt.get(e.get("reihe"), e.get("reihe") or ""))}'
            f'{" &middot; borrowed" if e.get("geliehen_aus") else ""}</div></div>')
    warnung = ""
    if pruef.get("status") != "gut":
        warnung = f'<div class="vw-warn">{html.escape(pruef.get("text") or "")}</div>'
    return ('<div class="card"><b>Approved gallery</b>'
            f'<div>{g.get("groesse")} cells, approved '
            f'{_zeit(g.get("abnahme_ts"))}.</div>' + warnung
            + '<div class="dim">These are copies inside the gallery folder, '
            "with the origin of every picture (run, file, checksum) written "
            "next to them. They travel with your backup.</div>"
            f'<div class="vw-raster">{"".join(zeilen)}</div>'
            '<div style="margin-top:10px"><a class="gtb" '
            f'href="/vision/galerie?person={urllib.parse.quote(person)}&neu=1">'
            "Build it again from current material</a> "
            '<a class="gtb" href="/vision">Back to Vision detect</a></div>'
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
        # eine abgenommene Galerie aus.
        teile.append('<div class="card" style="border-left-color:var(--warn)">'
                     f"<b>New material available</b><div>{auffrischung}</div>"
                     '<div class="dim">Nothing changes on its own &mdash; the '
                     "gallery you approved stays exactly as it is until you "
                     "build and approve a new one.</div></div>")
    if fertig:
        teile.append(_fertig(fertig, pruefung or {}, person, rt))
        return "".join(teile)
    teile.append(_groessen(groessen, groesse, empfehlung, person))
    if vorschlag:
        teile.append(_vorschlag(vorschlag, person, abgelehnt_n, rt))
    return "".join(teile)
