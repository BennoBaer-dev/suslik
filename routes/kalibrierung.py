"""routes/kalibrierung — die ZENTRALE Kamera-Uebersicht der Kalibrierung
(User-Entscheid 31.08.: EIN Menuepunkt, IMMER pro Kamera).

Zwei Seiten leben hier:

  uebersicht()  /kalibrierung — je Kamera eine Kachel: Vorrats-Stand, letzte
                Aktualisierung, die geltenden Werte, und drei Knoepfe
                (Kalibrieren, frisches Material suchen, Vorrat loeschen).
                Von hier geht es je Kamera weiter auf /kalibrierung/<kamera>
                (routes/livekalib.py — DIE Kalibrierseite, seit dem
                Zentral-Umbau der einzige Weg dorthin).

  lauf()        /kalibrierung?lauf=1 — die GLOBALEN Guete-Werte am Material
                des letzten Lernlaufs. Das ist die .377-Seite; sie ist NICHT
                verschwunden, sondern hat ihren Platz gewechselt: sie stellt
                die Werte ein, die fuer Lernlauf-Sieb und Pool-Zulauf gelten
                (und als Rueckfall fuer Kameras ohne eigene Werte dienen).
                Der frueher an der Smart-naming-Kachel haengende Knopf fuehrt
                jetzt auf die Uebersicht — es gibt genau EINEN Einstieg.

WARUM ZWEI EBENEN und nicht eine Zahl fuer alles: die Gueteskalen sind
kameraabhaengig (Messung 31.08.: Median fiqa_t 0,181 gegen 0,073 an zwei
Kameras derselben Anlage). Was hier global bleibt, ist deshalb ausdruecklich
der RUECKFALL und die Latte der Lernlauf-Flaeche, nicht der Anspruch, fuer
jede Kamera zu passen.

Reines Rendern (Muster live/livekalib: Daten als Parameter, kein
Dienst-Import). Die Seiten liefern INHALT; den Rahmen setzt verifyd mit
webui.layout — dadurch traegt die Kamera-Seite denselben Rahmen wie die
Uebersicht, ohne dass dieses Modul etwas ueber die Navigation wissen muss.
"""
import html
import json
import time

from core.benennung import REF_LATTE
from core.sprache import t


def _wann(ts):
    """Zeitpunkt oder ein ehrliches Nichts — nie eine 1970er-Zahl."""
    if not ts:
        return ""
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))


def _zahl(w, stellen=3):
    return "—" if w is None else f"{float(w):.{stellen}f}"


def _quelle_wort(quelle):
    """Woher die geltende Katalog-Latte kommt. Die drei Schluessel stehen
    LITERAL hier (nicht zusammengesetzt): die Sprach-Deckungsstufe liest die
    t()-Aufrufe statisch und hielte einen erst zur Laufzeit gebauten
    Schluessel fuer tot (dieselbe Auflage wie in routes/live.py)."""
    return {"kamera": t("kalib.quelle.kamera"),
            "global": t("kalib.quelle.global"),
            "aus": t("kalib.quelle.aus")}.get(str(quelle), "")


# ------------------------------------------------------------- Uebersicht
def _kachel(k, deckel, bilanz=None):
    """EINE Kamera-Kachel. Sie beantwortet in dieser Reihenfolge: habe ich hier
    Material, wie alt ist es, welche Werte gelten — und dann erst die
    Knoepfe. Ein Kalibrier-Knopf ohne Material waere ein Weg ins Leere,
    deshalb sagt die Kachel den Stand VOR dem Knopf."""
    nid = html.escape(k["name"], quote=True)
    name = html.escape(k["name"])
    marke = (f'<span class="pill lvp lvp-ok">{t("kalib.kachel.eigene")}</span>'
             if k["eigene"] else
             f'<span class="pill">{t("kalib.kachel.vorgabe")}</span>')
    fremd = ("" if k.get("in_frigate") else
             f' <span class="pill warn" title="{html.escape(t("kalib.kachel.fremd_tip"))}">'
             f'{t("kalib.kachel.fremd")}</span>')
    if not deckel:
        stand = f'<div class="dim lv-zeile">{t("kalib.kachel.vorrat_aus")}</div>'
    elif k["vorrat_n"]:
        stand = (f'<div class="lv-zeile">'
                 f'{t("kalib.kachel.vorrat", n=k["vorrat_n"], deckel=deckel)}</div>'
                 f'<div class="dim lv-zeile">'
                 f'{t("kalib.kachel.stand", wann=html.escape(_wann(k["vorrat_ts"])))}</div>')
    else:
        # K6 (01.09., A4-Befund beim Feldtester: 27 von 31 Kameras ohne
        # Vorrat, die Kachel sagte nur "leer"): liegt eine Fueller-Bilanz
        # vor, erklaert die Kachel den leeren Vorrat ehrlich — kein Gesicht
        # gefunden (Uebersichts-/Distanz-Kamera), Gesichter zu klein/zu
        # schwach, oder Material da, aber die Vorrats-Guete nicht erreicht.
        hinweis = t("kalib.kachel.leer_hinweis")
        if isinstance(bilanz, dict) and int(bilanz.get("events") or 0) > 0:
            _ev = int(bilanz.get("events") or 0)
            if int(bilanz.get("detektionen") or 0) == 0:
                hinweis = t("kalib.kachel.bilanz_keine", ev=_ev)
            elif int(bilanz.get("m") or 0) == 0:
                hinweis = t("kalib.kachel.bilanz_klein", ev=_ev)
            else:
                hinweis = t("kalib.kachel.bilanz_zulauf", ev=_ev)
        stand = (f'<div class="lv-zeile">{t("kalib.kachel.leer")}</div>'
                 f'<div class="dim lv-zeile">{html.escape(hinweis)}</div>')
    werte = (f'<div class="dim lv-zeile">'
             f'{t("kalib.kachel.werte", det=_zahl(k["det"], 2), e=_zahl(k["e"]), tw=_zahl(k["t"]))}'
             f'</div>'
             f'<div class="dim lv-zeile">'
             f'{t("kalib.kachel.katalog", e=_zahl(k["kat_e"]), tw=_zahl(k["kat_t"]))} '
             f'({_quelle_wort(k["kat_quelle"])})</div>')
    knoepfe = [f'<a class="gtb on" href="/kalibrierung/{nid}">'
               f'{t("kalib.knopf_kalibrieren")}</a>']
    if deckel:
        knoepfe.append(f'<button class="gtb" onclick="kalibFuellen(\'{nid}\',this)">'
                       f'{t("kalib.knopf_fuellen")}</button>')
    if k["vorrat_n"]:
        knoepfe.append(f'<button class="gtb" onclick="liveVorratLeeren(\'{nid}\',this)">'
                       f'{t("kalib.knopf_leeren")}</button>')
    # Kachel-Bauform WIE auf dem Live-Reiter (card + lv-kachel + kamhead):
    # dieselbe Sache soll gleich aussehen, egal aus welcher Richtung man kommt
    # — und die Groessen (Raster, Kopfzeile, Knopfzeile) bleiben so von selbst
    # konsistent, statt hier ein zweites Kachel-Design zu erfinden.
    return (f'<div class="card lv-kachel">'
            f'<div class="kamhead"><b>{name}</b>{fremd}{marke}</div>'
            f'{stand}{werte}'
            f'<div class="dim lv-zeile kal-fuell" id="kf-{nid}"></div>'
            f'<div class="lv-knoepfe">{"".join(knoepfe)}</div></div>')


def uebersicht(daten, global_werte, kat_global, deckel, lauf_da,
               fueller=(0, 0), banner_leer="", bilanzen=None):
    """-> Seiten-INHALT der zentralen Uebersicht.

    daten        = core.kamerakalib.uebersicht_daten(...)
    global_werte = die globalen Guete-Werte (Rueckfall + Lernlauf-Latte)
    kat_global   = die globale Katalog-Latte
    deckel       = live_kalib_max (0 = Vorrat aus; dann gibt es nichts zu
                   sammeln, und die Kacheln sagen das statt Knoepfe fuer
                   nichts anzubieten)
    lauf_da      = gibt es ueberhaupt einen Lernlauf mit Guete-Werten?
    fueller      = (ziel_bilder, deckel_events) des On-demand-Fuellers, damit
                   der Knopf-Text nicht behauptet, was die Config nicht sagt
    """
    kopf = (f'<h1>{t("kalib.titel")}</h1>'
            f'<p class="hinweis">{t("kalib.uebersicht.erklaerung")}</p>')
    # Was die Kalibrierung NICHT tut, steht mit auf der Seite. Zwei Messungen
    # desselben Tages haben gezeigt, dass Sieben VOR dem Namens-Voting
    # Bestaetigungen kostet — wer hier Regler sieht, soll nicht glauben, er
    # stelle die Erkennung ein.
    grenze = (f'<div class="card"><b>{t("kalib.grenze.titel")}</b>'
              f'<div class="dim">{t("kalib.grenze.satz")}</div></div>')
    if not daten:
        return (kopf + grenze
                + f'<div class="leer"><b>{t("kalib.uebersicht.leer")}</b><br>'
                  f'<small>{html.escape(banner_leer or t("kalib.uebersicht.leer_hinweis"))}'
                  f'</small></div>')
    kacheln = '<div class="lv-grid">' + "".join(
        _kachel(k, deckel, (bilanzen or {}).get(k["name"]))
        for k in daten) + '</div>'
    glob = (f'<div class="card"><b>{t("kalib.global.titel")}</b>'
            f'<div class="dim lv-zeile">{t("kalib.global.satz")}</div>'
            f'<div class="lv-zeile">'
            f'{t("kalib.global.werte", e=_zahl(global_werte.get("e")), tw=_zahl(global_werte.get("t")))}'
            f'</div>'
            f'<div class="dim lv-zeile">'
            f'{t("kalib.global.katalog", e=_zahl(kat_global.get("e")), tw=_zahl(kat_global.get("t")))}'
            f'</div>'
            + (f'<div class="lv-knoepfe"><a class="gtb" href="/kalibrierung?lauf=1">'
               f'{t("kalib.global.knopf")}</a></div>'
               if lauf_da else
               f'<div class="dim lv-zeile">{t("kalib.global.kein_lauf")}</div>')
            + '</div>')
    js = ("<script>window._kalibFueller=" + json.dumps(
        {"ziel": int(fueller[0]), "events": int(fueller[1])}) + ";</script>")
    return kopf + grenze + kacheln + glob + js


# ------------------------------------------------- Globale Werte am Lernlauf
def _letzter_lauf(saetze):
    """Groesste lauf_id im Bestand. DIESELBE Hausregel wie core.lernlauf
    (alte_laeufe_loeschen: 'L<JJJJMMTT_HHMMSS> sortiert lexikalisch =
    chronologisch') — kein zweiter Zeitbegriff."""
    ids = {str((s.get("lauf") or {}).get("lauf_id") or "") for s in saetze or []}
    ids.discard("")
    return max(ids) if ids else ""


def mitglieder_mit_guete(saetze, kamera=None):
    """Mitglieder mit BEIDEN Massen, je mit Gruppe — aus dem LETZTEN Lauf.

    Zwei bewusste Filter (Widerleger-Fund 30.08.): der Store traegt alle
    Laeufe (anker_lesen liest die ganze anker.jsonl, und
    alte_anker_aufraeumen laesst benannt/uebernommen/verworfen
    laufuebergreifend stehen). Ohne Lauf-Filter mischte die Seite Bilder
    mehrerer Laeufe, obwohl Erklaertext und Zaehler den einen Lauf meinen.
    Und verworfene Gruppen sind doppelt falsch: der Nutzer hat sie schon
    weggeworfen, UND anker_verwerfen loescht ihre Crops — sie waeren
    404-Kacheln, die er bewerten soll, ohne sie zu sehen.

    `kamera` (Zentral-Umbau 31.08.): auf EINE Kamera filtern. So kann die
    Kamera-Seite die Lernlauf-Bilder DIESER Kamera als zusaetzliches Material
    zeigen — der Lernlauf-Kontext bleibt erhalten, ohne einen zweiten
    Bedienweg aufzumachen."""
    lauf = _letzter_lauf(saetze)
    aus = []
    for s in saetze or []:
        if str((s.get("lauf") or {}).get("lauf_id") or "") != lauf:
            continue
        if s.get("status") == "verworfen":
            continue
        wer = s.get("person") or s.get("anker_id") or "?"
        for m in s.get("mitglieder") or []:
            ft, ew = m.get("fiqa_t"), m.get("empf")
            if ft is None or ew is None:
                continue
            if kamera is not None and str(m.get("kamera") or "") != str(kamera):
                continue
            aus.append({"d": str(m.get("datei", "")).rsplit("/", 1)[-1],
                        "lid": lauf, "t": float(ft), "e": float(ew),
                        "k": float(m.get("kante") or 0),
                        "kam": str(m.get("kamera") or ""),
                        "g": bool(m.get("gewaehlt")), "p": str(wer)})
    return aus


def lauf(saetze, cfg, defaults):
    """-> Seiten-INHALT der GLOBALEN Guete-Kalibrierung am letzten Lernlauf
    (die .377-Seite). cfg liefert die AKTUELLEN Schwellen, defaults die
    Werks-Startwerte (beides aus verifyd — nichts hardcoden)."""
    bilder = mitglieder_mit_guete(saetze)
    bilder.sort(key=lambda z: -z["e"])
    e_akt = float(cfg.get("guete_empfinden_min") or 0)
    t_akt = float(cfg.get("guete_t_min") or 0)
    zurueck = (f'<p><a href="/kalibrierung">{t("kalib.zurueck")}</a></p>')
    if not bilder:
        # Ohne Regler und ohne Galerie waere die Regler-Anleitung eine
        # Wegbeschreibung ins Leere ("schiebe, bis ...", "unten stehen ...",
        # "gelber Rahmen ..."): der Leer-Zweig traegt deshalb NUR den Titel
        # und die Auskunft, warum hier nichts steht.
        return (f'<h1>{t("kalib.lauf.titel")}</h1>'
                f'<div class="kal-leer">{t("kalib.leer")}</div>' + zurueck)
    inhalt = (f'<h1>{t("kalib.lauf.titel")}</h1>'
              f'<p class="hinweis">{t("kalib.erklaerung")}</p>') + f"""
<div class="kal-regler">
 <div class="kal-zeile"><b>{t("kalib.regler_e")}</b>
  <div class="kal-prosa">{t("kalib.regler_e_prosa")}</div>
  <input type="range" id="kal-e" min="0.175" max="1" step="0.001" value="0.175">
  <span id="kal-e-wert"></span></div>
 <div class="kal-zeile"><b>{t("kalib.regler_t")}</b>
  <div class="kal-prosa">{t("kalib.regler_t_prosa")}</div>
  <input type="range" id="kal-t" min="0.375" max="1" step="0.001" value="0.375">
  <span id="kal-t-wert"></span></div>
 <div id="kal-stand"></div>
 <button id="kal-std" class="gtb">{t("kalib.standard")}</button>
 <button id="kal-save" class="gtb on">{t("kalib.uebernehmen")}</button>
 <span id="kal-msg"></span>
</div>
<div class="kal-g" id="kal-g"></div>
{zurueck}
<script>
const B = {json.dumps(bilder, ensure_ascii=False)};
// .379: der feste Kanten-Boden der echten Latte (REF_LATTE.min_kante) —
// ohne ihn zaehlte die Seite Bilder als "behalten", die die Auswahl am
// Boden verwirft. Kein Regler: er ist keine Geschmacksfrage.
const MINK = {json.dumps(float(REF_LATTE["min_kante"]))};
const AKT = {json.dumps({"e": e_akt, "t": t_akt})};
const STD = {json.dumps(defaults)};
const T_TXT = {json.dumps({"genutzt": t("kalib.js.genutzt"),
                           "gespeichert": t("kalib.js.gespeichert"),
                           "fehler": t("kalib.js.fehler")},
                          ensure_ascii=False)};
const g = document.getElementById("kal-g");
const karten = [];
for (const z of B) {{
  const k = document.createElement("div");
  k.className = "kal-k" + (z.g ? " uebern" : "");
  k.innerHTML = `<img loading="lazy" src="/lernlauf/crop/${{z.lid}}/${{encodeURIComponent(z.d)}}">`
    + `<div class="kal-w">${{z.e.toFixed(2)}} / ${{z.t.toFixed(2)}} &middot; ${{z.p.replace(/</g, "&lt;")}}</div>`;
  g.appendChild(k); karten.push([z, k]);
}}
// Reglerskala FEST 0..1 mit Feinschritt 0,001 — die Spanne des Materials
// darf sie nicht bestimmen (Widerleger-Fund 30.08.): eine datenabhaengige
// Skala klemmte die aktuelle Schwelle und den Werks-Startwert ins Fenster
// des Laufs, die Seite zeigte dann eine andere Zahl als die geltende und
// der Uebernehmen-Klick schrieb sie auch so. 0..1 ist zugleich die Spanne
// der beiden Whitelist-Eintraege, es ist also nichts erreichbar, was der
// Config-Weg ablehnen wuerde. Auf 3 Stellen gerundet, damit die angezeigte
// Zahl EXAKT die gespeicherte ist.
function wert(id) {{
  const v = parseFloat(document.getElementById(id).value);
  return Math.round((isNaN(v) ? 0 : v) * 1000) / 1000;
}}
function setz(id, v) {{
  const z = Number(v);
  document.getElementById(id).value = Math.min(Math.max(isNaN(z) ? 0 : z, 0), 1);
}}
function malen() {{
  const e = wert("kal-e"), tt = wert("kal-t");
  document.getElementById("kal-e-wert").textContent = e.toFixed(3);
  document.getElementById("kal-t-wert").textContent = tt.toFixed(3);
  let drin = 0;
  for (const [z, k] of karten) {{
    const ok = z.k >= MINK && z.e >= e && z.t >= tt;
    k.classList.toggle("raus", !ok);
    if (ok) drin++;
  }}
  document.getElementById("kal-stand").textContent =
    T_TXT.genutzt.replace("{{n}}", drin).replace("{{gesamt}}", B.length);
}}
document.getElementById("kal-e").oninput = malen;
document.getElementById("kal-t").oninput = malen;
document.getElementById("kal-std").onclick = () => {{
  setz("kal-e", STD.e); setz("kal-t", STD.t); malen();
}};
document.getElementById("kal-save").onclick = async () => {{
  const m = document.getElementById("kal-msg");
  try {{
    const r = await fetch("/kalibrierung_setzen", {{method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify({{empfinden: wert("kal-e"), t: wert("kal-t")}})}});
    m.textContent = r.ok ? T_TXT.gespeichert : T_TXT.fehler;
    // User-Wunsch 30.08.: nach dem Uebernehmen zurueck zum Lernlauf, um den
    // Lauf weiterzuverarbeiten. Die Antwort kommt erst, wenn der Server den
    // Lauf mit den neuen Schwellen NEU BEWERTET hat (.378, kein Neustart
    // mehr) — die kurze Pause laesst nur die Meldung lesbar stehen.
    if (r.ok) setTimeout(() => {{ location.href = "/lernlauf"; }}, 1200);
  }} catch (e) {{
    m.textContent = T_TXT.fehler;      // abgerissene Verbindung ist kein stiller Erfolg
  }}
}};
setz("kal-e", AKT.e); setz("kal-t", AKT.t); malen();
</script>"""
    return inhalt
