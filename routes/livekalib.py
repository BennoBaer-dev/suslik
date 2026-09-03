"""routes/livekalib — DIE Kalibrier-Seite EINER Kamera (/kalibrierung/<kamera>).

Seit dem Zentral-Umbau (31.08.) ist das die einzige Kalibrierseite je Kamera:
erreichbar aus der Uebersicht /kalibrierung (Menuepunkt oben in der
Hauptleiste) und aus der Erkennungs-Kachel von /live/<kamera>. Der alte
Pfad /live_kalibrierung/<kamera> leitet hierher um — ein Bedienweg, kein
zweiter. (Der Modulname bleibt: die Seite ist gewachsen, nicht ersetzt, und
mit ihm bleiben die schon fuenfsprachig gepflegten livekalib.*-Texte gueltig.)

DREI ABSCHNITTE — die Drei-Latten-Semantik (User 31.08.):

  1. ANZEIGE / MELDEN / VORRAT — det, Empfinden, Erkennbarkeit. Sie
     entscheiden, WELCHES Bild in Meldung und Anzeige geht und WAS in den
     Kalibrier-Vorrat kommt. Nicht mehr.
  2. KATALOG-AUFNAHME — eine EIGENE, strengere Latte: welches Bild dieser
     Kamera ueberhaupt Referenz werden darf. Sie greift an allen
     Uebernahme-Wegen (core/kamerakalib.py), niemals rueckwirkend.
  3. MATERIAL — der Vorrat dieser Kamera: Stand, Nachschub auf Knopfdruck,
     Loeschweg.

WARUM JE KAMERA und nicht einmal fuer alle: die Guete-Skalen sind
kameraabhaengig. Gemessen am 31.08. an Feldmaterial: Median fiqa_t 0,181 auf
der einen Kamera gegen 0,073 auf der anderen. Eine gemeinsame Zahl waere fuer
die eine grosszuegig und fuer die andere ein Kahlschlag.

WAS DIE SEITE EHRLICH SAGEN MUSS (User-Auflage, aus zwei Messungen desselben
Tages): die zwei Guete-Regler siegen NICHT die Erkennung. Wer vor dem
Namens-Voting siebt, verliert Bestaetigungen — ohne Siebe kamen 41 % mehr
zustande, und ausgerechnet die Pose korrelierte NEGATIV. Die Guete entscheidet
deshalb nur zweierlei: WELCHES Bild in die Meldung/Anzeige geht und WAS in den
Vorrat kommt. Genau das steht auch als Prosa an den Reglern; die Seite darf hier
nichts versprechen, was der Code nicht tut.

Rein lesend bis auf den Uebernehmen-POST — und der geht ueber /live_speichern,
also denselben Weg (mit denselben Riegeln und demselben Audit) wie jede andere
Aenderung an einem Waechter. Kein eigener Schreibweg hier. Weil ein FEHLENDES
Feld dort "behalten" heisst (live_speichern._wert), schickt diese Seite genau
ihre sechs Werte und laesst alles andere unangetastet.

POSE-REGLER (03.09., Stufe 1): der vierte Regler im Register "Erkennen"
arbeitet auf dem Kopf-Score p, den der Worker-Zulauf je Ring-Bild mitmisst.
Er wirkt HIER sofort (die Galerie dimmt mit, der Zaehler rechnet ihn mit) und
wird als `pose_min` je Kamera gespeichert. Was er NICHT tut: sieben. Weder
Worker noch Live-Weg fragen den gespeicherten Wert bisher — Stufe 2 folgt
nach User-Entscheid. Genau das sagt auch die Prosa am Regler; dieselbe
Auflage wie bei den zwei Guete-Reglern (nichts versprechen, was der Code
nicht tut).
"""
import html
import json
import time
import urllib.parse

from core.sprache import t


# Regler-Untergrenzen der zwei Erkennen-Guete-Regler = absolute Stimm-Boeden
# (EINE Quelle, core/guete.STIMM_BODEN): darunter geht niemand
# (User-Entscheide 01.09. abends: t nie unter 0,2; e-Boden = Default 0,175).
from core.guete import STIMM_BODEN as _KB
from core.guete import POSE_BODEN as _PB
_BODEN_E = f"{_KB['empfinden']:.3f}"
_BODEN_T = f"{_KB['t']:.3f}"

# Skala des Pose-Reglers — fest wie bei den Nachbarn (Lehre der Lernlauf-Seite,
# s. JS-Kommentar unten). Gemessene Lage des Kopf-Scores: Mensch 0,77-1,04 am
# Klon-Material, das Live-Gate steht bei 0,70; die Skala laesst darueber Luft,
# ohne die Server-Spanne (livewache.POSE_MIN_MIN/MAX = 0-2) zu verlassen.
# 0 = AUS: unter dieser Stellung fehlt keinem Bild etwas.
_POSE_LO, _POSE_HI, _POSE_SCHRITT = f"{_PB:.2f}", "1.20", "0.01"   # Minimum = Werks-Boden (User 03.09.)


def _wann(ts):
    if not ts:
        return ""
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))


def _bilder(kamera, vorrat, lauf_bilder):
    """Die Galerie-Zeilen BEIDER Quellen in EINER Liste.

    Ring-Bilder (was die Kamera im Betrieb geliefert hat) und die Bilder des
    letzten Lernlaufs VON DIESER KAMERA. Der Lernlauf-Kontext bleibt damit
    erhalten (er war die Herkunft der .377-Seite), ohne einen zweiten
    Bedienweg zu oeffnen — jede Kachel sagt, woher sie stammt.

    -1 heisst "nicht gemessen" und laesst die zugehoerige Latte passieren
    (Lernlauf-Bilder tragen keinen det-Wert, Alt-Images keine Guete-Masse);
    sonst blendete eine fehlende Messung Material aus, das es gar nicht
    beurteilt."""
    kq = urllib.parse.quote(str(kamera), safe="")
    aus = []
    for e in vorrat or []:
        aus.append({"src": f"/live_kalib_bild?k={kq}&d="
                           + urllib.parse.quote(str(e["d"]), safe=""),
                    "det": float(e.get("det") or 0),
                    "e": (-1.0 if e.get("e") is None else float(e["e"])),
                    "t": (-1.0 if e.get("t") is None else float(e["t"])),
                    "p": (-1.0 if e.get("p") is None else float(e["p"])),
                    "q": "ring"})
    for b in lauf_bilder or []:
        aus.append({"src": f"/lernlauf/crop/{urllib.parse.quote(str(b['lid']), safe='')}/"
                           + urllib.parse.quote(str(b["d"]), safe=""),
                    "det": -1.0,
                    "e": float(b.get("e") if b.get("e") is not None else -1.0),
                    "t": float(b.get("t") if b.get("t") is not None else -1.0),
                    "q": "lauf"})
    return aus


def _quelle_wort(quelle):
    """Woher die geltende Katalog-Latte kommt — LITERALE Schluessel (die
    Sprach-Deckungsstufe liest t() statisch; ein zur Laufzeit gebauter
    Schluessel gilt ihr als tot, Auflage aus routes/live.py)."""
    return {"kamera": t("livekalib.katalog.quelle_kamera"),
            "global": t("livekalib.katalog.quelle_global"),
            "aus": t("livekalib.katalog.quelle_aus")}.get(str(quelle), "")


def _regler(kennung, titel, prosa, lo, hi, schritt, wert):
    # Prosa als Hover-Titel statt Textblock (User 31.08.: drei Schieber in
    # EINER Reihe, damit die Galerie mehr Bilder zeigt — der Platz gehoert
    # den Bildern, die Erklaerung bleibt am Titel erreichbar).
    return (f'<div class="kal-zeile" title="{html.escape(prosa, quote=True)}">'
            f'<b>{titel}</b>'
            f'<input type="range" id="{kennung}" min="{lo}" max="{hi}" '
            f'step="{schritt}" value="{wert}">'
            f'<span id="{kennung}-wert"></span></div>')


def render(kamera, vorrat, guard, standard, kat, lauf_bilder=(), deckel=0,
           fueller=(0, 0), hat_waechter=False, fueller_stand=None):
    """-> Seiten-INHALT.

    vorrat  = [{"d","ts","det","e","t"}, ...] aus livewache.kalib_lesen
    guard   = der normalisierte Waechter-Block (aktuelle Schwellen) oder {}
    standard= {"det","e","t"} die Werks-Startwerte (aus dem Code, nie hier)
    kat     = {"akt": {"e","t","quelle"}, "std": {"e","t"}} — geltende und
              Werks-Katalog-Latte (core.kamerakalib)
    lauf_bilder = Lernlauf-Bilder DIESER Kamera (kann leer sein)
    deckel  = live_kalib_max (0 = Vorrats-Sammlung aus)
    fueller = (ziel_bilder, deckel_events) des On-demand-Fuellers
    hat_waechter = gibt es fuer diese Kamera einen Waechter-Block? (nur fuer
              den Rueckweg — die Kalibrierung selbst braucht keinen)"""
    nid = html.escape(str(kamera), quote=True)
    g = guard or {}
    # Der Erklaersatz beschreibt das Schieben an der Galerie ("drag the sliders
    # until the selection looks right") — ohne ein einziges Bild waere er eine
    # Wegbeschreibung ins Leere (dieselbe Lehre wie beim Leer-Zweig der
    # Lernlauf-Kalibrierseite, Usersicht-Durchgang 31.08.). Titel steht immer,
    # der Satz nur mit Material.
    titel = f'<h1>{t("livekalib.titel", name=html.escape(str(kamera)))}</h1>'
    kopf = titel + f'<p class="hinweis">{t("livekalib.erklaerung")}</p>'
    zurueck = (f'<p><a href="/kalibrierung">{t("livekalib.zur_uebersicht")}</a>'
               + (f' &middot; <a href="/live/{nid}">{t("livekalib.zurueck")}</a>'
                  if hat_waechter else "")
               + '</p>')
    bilder = _bilder(kamera, vorrat, lauf_bilder)
    bilder.sort(key=lambda z: -z["det"])
    akt = {"det": (g.get("det_min") if g.get("det_min") is not None
                   else standard["det"]),
           "e": (g.get("guete_e_min") or 0.0),
           "t": (g.get("guete_t_min") or 0.0),
           # Pose: der gespeicherte Kamera-Wert oder 0 = aus. Kein Werks-Wert
           # dahinter — solange die Latte nichts siebt, waere jeder Startwert
           # ausser "aus" eine Behauptung.
           # unkalibriert zeigt der Regler den Werks-Boden (= was wirklich
           # siebt, User 03.09. "durchgaengig"), nicht mehr 0.
           "p": (g.get("pose_min") if g.get("pose_min") is not None else _PB)}
    kat_akt = kat.get("akt") or {}
    kat_std = kat.get("std") or {}
    # Fehlen die Guete-Modelle im Image, tragen ALLE Zeilen -1 — dann sind die
    # zwei Guete-Regler wirkungslos, und die Seite sagt das, statt sie
    # anzubieten und den Nutzer raten zu lassen.
    ohne_guete = bool(bilder) and all(b["e"] < 0 and b["t"] < 0 for b in bilder)
    # Dieselbe Ehrlichkeit fuer die Pose: traegt KEIN Bild einen Kopf-Score
    # (Bestands-Ring von vor der Messung, Bilder aus dem Live-/Ernte-Weg, ein
    # Image ohne ladbares Pose-Modell), dann bewegt der Regler hier nichts —
    # das sagt die Seite, statt ihn wortlos anzubieten.
    ohne_pose = bool(bilder) and all(b.get("p", -1.0) < 0 for b in bilder)

    # --- Abschnitt 3 zuerst gebaut (er wird unten eingehaengt) -------------
    if not deckel:
        material = f'<div class="dim lv-zeile">{t("livekalib.material.aus")}</div>'
    else:
        letzte = max((float(e.get("ts") or 0) for e in vorrat or []), default=0.0)
        material = (f'<div class="lv-zeile">'
                    f'{t("livekalib.material.stand", n=len(vorrat or []), deckel=deckel)}'
                    + (f' &middot; {t("livekalib.material.wann", wann=html.escape(_wann(letzte)))}'
                       if letzte else "") + '</div>')
    material += (f'<div class="dim lv-zeile">'
                 f'{t("livekalib.material.fuellen_prosa", ziel=int(fueller[0]), events=int(fueller[1]))}'
                 f'</div>'
                 f'<div class="dim lv-zeile kal-fuell" id="kf-{nid}"></div>'
                 f'<div class="lv-knoepfe">'
                 + (f'<button class="gtb" onclick="kalibFuellen(\'{nid}\',this)">'
                    f'{t("kalib.knopf_fuellen")}</button>' if deckel else "")
                 # DERSELBE Knopf-Text wie auf der Uebersicht (Usersicht-Fund:
                 # "Clear samples" hier gegen "Delete samples" dort — zwei
                 # Woerter fuer dieselbe Handlung auf zwei Seiten desselben
                 # Themas).
                 + (f'<button class="gtb" onclick="liveVorratLeeren(\'{nid}\',this)">'
                    f'{t("kalib.knopf_leeren")}</button>' if vorrat else "")
                 + '</div>')
    if len(lauf_bilder or []):
        material += (f'<div class="dim lv-zeile">'
                     f'{t("livekalib.material.lauf", n=len(lauf_bilder))}</div>')

    if not bilder:
        # Leer-Zweig ohne Regler (Muster der Lernlauf-Kalibrierseite): "schiebe,
        # bis dir die Grenze gefaellt" waere ohne ein einziges Bild eine
        # Wegbeschreibung ins Leere. Der Material-Abschnitt bleibt trotzdem
        # stehen — dort steht der Knopf, der die Leere beendet.
        return (titel + f'<div class="kal-leer">{t("livekalib.leer")}</div>'
                + f'<div class="card"><b>{t("livekalib.abschnitt.material")}'
                  f'</b>' + material + '</div>' + zurueck)

    # REIHENFOLGE (Usersicht-Durchgang 31.08.): erst das Material — "habe ich
    # ueberhaupt Bilder, und wie hole ich welche" ist die Frage vor jedem
    # Regler. Dann der EINE Regler-Block, und zwar KLEBEND und zusammen mit
    # Zaehlern und Uebernehmen: der erste Entwurf hatte die Regler in drei
    # Karten und den Zaehler darunter — man schob oben und die Wirkung stand
    # ausserhalb des Blicks. Die Galerie steht darunter und dimmt mit.
    # K1 (01.09.): laufender/letzter Fueller-Stand sichtbar — vorher wirkte
    # der Knopf wie tot, wenn der Worker belegt war (Feldtester-Klick ohne
    # jede Reaktion). Reine Anzeige aus kalibfueller.stand().
    fs = fueller_stand or {}
    fs_zeile = ""
    if fs:
        if fs.get("laeuft"):
            fs_zeile = (f'<div class="dim">{t("livekalib.fueller.laeuft")}: '
                        f'{int(fs.get("i") or 0)}/{int(fs.get("n") or 0)} · '
                        f'{int(fs.get("bilder") or 0)}/{int(fs.get("ziel") or 0)}'
                        + (f' — {html.escape(str(fs.get("notiz")))}'
                           if fs.get("notiz") else "") + "</div>")
        elif fs.get("grund") or fs.get("fehler"):
            fs_zeile = (f'<div class="dim">{t("livekalib.fueller.bilanz")}: '
                        f'{html.escape(str(fs.get("fehler") or fs.get("grund")))}'
                        f' · {int(fs.get("bilder") or 0)} '
                        f'{t("livekalib.fueller.bilder")}</div>')
    material_karte = (f'<div class="card"><b>{t("livekalib.abschnitt.material")}'
                      f'</b>' + material + fs_zeile + '</div>')
    regler = (
        # Zwei Register statt Dopplung (User 31.08.: "lieber zwei Register,
        # einmal fuer Erkennen und einmal fuer Lernen, und zwischen den
        # Registern schalten") — die Gruppen tragen dieselben Regler wie
        # zuvor, sichtbar ist immer genau EINE; der Vorgaben-Knopf bleibt
        # in der Aktionszeile beider Register.
        f'<div class="kal-tabs">'
        f'<button type="button" id="lk-tab-e" class="gtb on">'
        f'{t("livekalib.tab_erkennen")}</button>'
        f'<button type="button" id="lk-tab-l" class="gtb">'
        f'{t("livekalib.tab_lernen")}</button></div>'
        f'<div class="kal-gruppe" id="lk-reg-e"><b>{t("livekalib.abschnitt.anzeige")}</b>'
        f'<div class="kal-prosa">{t("livekalib.abschnitt.anzeige_prosa")}</div>'
        + _regler("lk-det", t("livekalib.regler_det"),
                  t("livekalib.regler_det_prosa"), "0.40", "0.60", "0.01", "0.4")
        + _regler("lk-e", t("livekalib.regler_e"),
                  t("livekalib.regler_e_prosa"), _BODEN_E, "1", "0.001", _BODEN_E)
        + _regler("lk-t", t("livekalib.regler_t"),
                  t("livekalib.regler_t_prosa"), _BODEN_T, "1", "0.001", _BODEN_T)
        + ('<div class="kal-prosa">' + t("livekalib.ohne_guete") + "</div>"
           if ohne_guete else "")
        # Der Pose-Regler steht NACH dem ohne_guete-Satz: der spricht von "den
        # unteren zwei Reglern" und meint die zwei Guete-Regler ueber ihm.
        + _regler("lk-p", t("livekalib.regler_p"),
                  t("livekalib.regler_p_prosa"), _POSE_LO, _POSE_HI,
                  _POSE_SCHRITT, _POSE_LO)
        + ('<div class="kal-prosa">' + t("livekalib.ohne_pose") + "</div>"
           if ohne_pose else "")
        + f'<div id="lk-stand"></div></div>'
        f'<div class="kal-gruppe" id="lk-reg-l" style="display:none">'
        f'<b>{t("livekalib.abschnitt.katalog")}</b>'
        f'<div class="kal-prosa">{t("livekalib.katalog.prosa")}</div>'
        f'<div class="kal-prosa">{t("livekalib.katalog.grenze")}</div>'
        f'<div class="dim lv-zeile">'
        f'{_quelle_wort(kat_akt.get("quelle") or "aus")}</div>'
        + _regler("lk-ke", t("livekalib.katalog.regler_e"),
                  t("livekalib.katalog.regler_e_prosa"), "0.175", "1", "0.001", "0.175")
        + _regler("lk-kt", t("livekalib.katalog.regler_t"),
                  t("livekalib.katalog.regler_t_prosa"), "0.375", "1", "0.001", "0.375")
        + '<div class="dim" id="lk-kstand"></div></div>')
    return kopf + material_karte + f"""
<div class="kal-regler">
{regler}
 <div class="kal-aktion">
  <button id="lk-std" class="gtb">{t("livekalib.standard")}</button>
  <button id="lk-save" class="gtb on">{t("livekalib.uebernehmen")}</button>
  <span id="lk-msg"></span>
 </div>
</div>
<div class="kal-g" id="lk-g"></div>
{zurueck}
<script>
const B = {json.dumps(bilder, ensure_ascii=False)};
const KAM = {json.dumps(str(kamera), ensure_ascii=False)};
const AKT = {json.dumps(akt)};
const STD = {json.dumps(standard)};
const KAKT = {json.dumps({"e": kat_akt.get("e"), "t": kat_akt.get("t")})};
const KSTD = {json.dumps({"e": kat_std.get("e"), "t": kat_std.get("t")})};
const T_TXT = {json.dumps({"genutzt": t("livekalib.js.genutzt"),
                           "katalog": t("livekalib.js.katalog"),
                           "gespeichert": t("livekalib.js.gespeichert"),
                           "fehler": t("livekalib.js.fehler"),
                           "lauf": t("livekalib.js.lauf")},
                          ensure_ascii=False)};
const g = document.getElementById("lk-g");
const karten = [];
for (const z of B) {{
  const k = document.createElement("div");
  k.className = "kal-k";
  const gw = (z.e < 0 && z.t < 0) ? ""
    : `${{z.e < 0 ? "?" : z.e.toFixed(2)}} / ${{z.t < 0 ? "?" : z.t.toFixed(2)}}`;
  const dw = (z.det < 0) ? T_TXT.lauf : z.det.toFixed(2);
  const pw = (z.p === undefined || z.p < 0) ? "" : ` &middot; p${{z.p.toFixed(2)}}`;
  k.innerHTML = `<img loading="lazy" src="${{z.src}}">`
    + `<div class="kal-w">${{dw}}${{gw ? " &middot; " + gw : ""}}${{pw}}</div>`;
  g.appendChild(k); karten.push([z, k]);
}}
/* Reglerskalen FEST (Lehre der Lernlauf-Kalibrierseite, Widerleger 30.08.):
   eine datenabhaengige Skala klemmte die geltende Schwelle ins Fenster des
   gerade sichtbaren Materials — die Seite zeigte dann eine andere Zahl, als
   wirklich galt, und der Uebernehmen-Klick schrieb sie auch so. Die Spannen
   hier sind exakt die, die der Server annimmt. */
function wert(id, stellen) {{
  const v = parseFloat(document.getElementById(id).value);
  const f = Math.pow(10, stellen);
  return Math.round((isNaN(v) ? 0 : v) * f) / f;
}}
function setz(id, v, lo, hi) {{
  const z = Number(v);
  document.getElementById(id).value = Math.min(Math.max(isNaN(z) ? lo : z, lo), hi);
}}
function malen() {{
  const d = wert("lk-det", 2), e = wert("lk-e", 3), tt = wert("lk-t", 3);
  const ke = wert("lk-ke", 3), kt = wert("lk-kt", 3), pp = wert("lk-p", 2);
  document.getElementById("lk-det-wert").textContent = d.toFixed(2);
  document.getElementById("lk-e-wert").textContent = e.toFixed(3);
  document.getElementById("lk-t-wert").textContent = tt.toFixed(3);
  document.getElementById("lk-p-wert").textContent = pp.toFixed(2);
  document.getElementById("lk-ke-wert").textContent = ke.toFixed(3);
  document.getElementById("lk-kt-wert").textContent = kt.toFixed(3);
  let drin = 0, kdrin = 0;
  for (const [z, k] of karten) {{
    /* UND-Logik wie auf der Lernlauf-Seite. Ein NICHT gemessener Wert (-1)
       laesst seine Latte passieren — sonst blendete ein fehlendes Guete-Modell
       (oder das fehlende det der Lernlauf-Bilder) den ganzen Vorrat aus und
       der Nutzer saehe eine leere Wand. */
    /* Die Pose-Latte urteilt nach DERSELBEN Regel: ein Bild ohne Kopf-Score
       (Feld fehlt = Bestand/Live-Weg, oder -1 = nicht gemessen) passiert sie.
       Sonst blendete der erste Zug am Regler den gesamten Alt-Bestand aus,
       ohne dass an ihm je etwas gemessen wurde. */
    const ok = (z.det < 0 || z.det >= d) && (z.e < 0 || z.e >= e)
               && (z.t < 0 || z.t >= tt)
               && (z.p === undefined || z.p < 0 || z.p >= pp);
    /* Die KATALOG-Latte urteilt getrennt und wird getrennt gezeigt: ein Bild
       kann fuer Anzeige/Vorrat taugen und trotzdem keine Referenz werden
       duerfen. Beides in einer Farbe waere eine Luege ueber zwei Latten. */
    const kok = (z.e < 0 || z.e >= ke) && (z.t < 0 || z.t >= kt);
    k.classList.toggle("raus", !ok);
    k.classList.toggle("katraus", ok && !kok);
    if (ok) drin++;
    if (kok) kdrin++;
  }}
  document.getElementById("lk-stand").textContent =
    T_TXT.genutzt.replace("{{n}}", drin).replace("{{gesamt}}", B.length);
  document.getElementById("lk-kstand").textContent =
    T_TXT.katalog.replace("{{n}}", kdrin).replace("{{gesamt}}", B.length);
}}
for (const id of ["lk-det", "lk-e", "lk-t", "lk-p", "lk-ke", "lk-kt"])
  document.getElementById(id).oninput = malen;
function registerZeigen(lernen) {{
  document.getElementById("lk-reg-e").style.display = lernen ? "none" : "";
  document.getElementById("lk-reg-l").style.display = lernen ? "" : "none";
  document.getElementById("lk-tab-e").classList.toggle("on", !lernen);
  document.getElementById("lk-tab-l").classList.toggle("on", lernen);
}}
document.getElementById("lk-tab-e").onclick = () => registerZeigen(false);
document.getElementById("lk-tab-l").onclick = () => registerZeigen(true);
document.getElementById("lk-std").onclick = () => {{
  setz("lk-det", STD.det, 0.40, 0.60); setz("lk-e", STD.e, 0, 1);
  setz("lk-t", STD.t, 0, 1);
  /* Pose-Vorgabe = AUS. Es gibt keinen Werks-Wert dafuer, solange die Latte
     nichts siebt — "Vorgaben" heisst hier also: der Regler stoert nicht. */
  setz("lk-p", {_POSE_LO}, {_POSE_LO}, {_POSE_HI});
  setz("lk-ke", KSTD.e === null ? 0.175 : KSTD.e, 0.175, 1);
  setz("lk-kt", KSTD.t === null ? 0.375 : KSTD.t, 0.375, 1); malen();
}};
document.getElementById("lk-save").onclick = async () => {{
  const m = document.getElementById("lk-msg");
  try {{
    /* Derselbe Schreibweg wie jede andere Waechter-Aenderung (/live_speichern,
       Riegel + Audit dort). Nur diese sechs Felder gehen mit — alles andere
       behaelt der Server (live_speichern: fehlendes Feld heisst behalten). */
    const r = await fetch("/live_speichern", {{method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify({{kamera: KAM, det_min: wert("lk-det", 2),
                            guete_e_min: wert("lk-e", 3),
                            guete_t_min: wert("lk-t", 3),
                            katalog_e_min: wert("lk-ke", 3),
                            katalog_t_min: wert("lk-kt", 3),
                            pose_min: wert("lk-p", 2)}})}});
    const d = await r.json().catch(() => ({{}}));
    m.textContent = r.ok ? T_TXT.gespeichert : (d.msg || T_TXT.fehler);
  }} catch (e) {{
    m.textContent = T_TXT.fehler;   /* abgerissene Verbindung ist kein stiller Erfolg */
  }}
}};
setz("lk-det", AKT.det, 0.40, 0.60); setz("lk-e", AKT.e, 0, 1);
setz("lk-t", AKT.t, 0, 1);
setz("lk-p", AKT.p, {_POSE_LO}, {_POSE_HI});
setz("lk-ke", KAKT.e === null ? 0.175 : KAKT.e, 0.175, 1);
setz("lk-kt", KAKT.t === null ? 0.375 : KAKT.t, 0.375, 1);
malen();
</script>"""
