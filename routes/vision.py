"""routes/vision — der Reiter "Vision detect" (konzept_vision.md v2 §4/§5).

Zug V2 loest die V1-Preset-Tabelle ab (fix-forward): oben eine Reihe aus FUENF
Anbieter-Kacheln (Gemini · GPT · Anthropic · Lokal · Custom), darunter genau die
Felder, die die gewaehlte Kachel wirklich braucht. Nach der Key-Eingabe prueft
ein Knopf den Schluessel per Modell-Listen-Abruf (kostenlos, kein Bild) und die
GEFUNDENEN Modelle erscheinen als Dropdown-Liste; die Mess-Anmerkung aus der
zentralen Registry haengt am Listeneintrag und ausfuehrlich unter der Wahl. Dazu die Galerie-Deckung je Person mit Sprung in den Wizard.

V4-Nacharbeit aus der Live-Nutzung (User 08.08. spaetabend): der Pruef-Knopf
heisst auf einer Kachel ohne Key-Pflicht "Check the connection" (Wort aus
core/vision.pruef_wort, nicht aus einer Namensliste), das Prompt-Feld zeigt
IMMER einen Wortlaut, und das Testlog steht mit drei Stufen-Zeilen auch dann
schon da, wenn noch nichts gelaufen ist. Der Klartext-Hinweis an der
Anthropic-Kachel ist ersatzlos entfallen (E7-Fortschreibung, User-Entscheid);
geblieben ist das Verhalten: eine Verweigerung ist "kein Votum".

Kontrakt wie alle routes-Module: reine Renderer, Daten als Parameter, kein
Dienst-Import; Seiteneffekte (Speichern, Test ausloesen, Audit) macht der
Handler in verifyd.py.

SECRET-REGEL (§9): der API-Key wird NIE im Klartext gerendert — Platzhalter wie
bei den Meldekanaelen, leer lassen behaelt den gespeicherten Wert. Die
Endpunkt-URL laeuft IMMER durch registry.endpunkt_anzeige(), auch in
Fehlermeldungen und im Testprotokoll (sie ist der zweite Key-Traeger).

OPTIK (User 08.08.: "das geht optisch besser"): Kacheln, Ampeln und Karten
liegen als Grid im bestehenden Farbsystem (--ok/--warn/--crit/--surface). KEIN
neues Framework und keine <table> fuer Layout — style.css setzt
table{width:100%}, das hat schon einmal eine Bilanz ueber die halbe Seite
gezogen. Die Stilblock-Konvention ist die der Abnahme-Seiten: ein knapper,
seiteneigener <style> direkt beim Markup.

Sprach-Stufe 2 (Tranche C, konzept_sprache.md v2): sichtbare Texte aus
core/sprache.t() — BYTE-TREU (Harnisch tools/harnisch_sprache.py). Die
Markup-Prosa (§8.1: Einleitung, Hinweis-Absaetze, Key-Ort, Modell-Leerzustand
und -Antwort, eigen-Prompt, Cloud-Satz, Drei-Stufen-Text) liegt seit Stufe 3
als t_html-Schluessel vor. Verbleibende Grenzen (Kommentar je Fundstelle):
die "Check the {pruef_wort}"-Rahmen von Knopf + Schluss-Satz (B9 — das Wort
kommt aus core/vision.pruef_wort, eigener Umbau-Zug; der Leerzustand ist
schon B9-konform je Wort geschluesselt), Inline-JS des Hand-ID-Blocks (§8.4,
Tranche D), Datumsformate (B19), Kachel-Vertrag (label/anbieter/basis) und
Badge-/Protokolltexte als Daten (eigene Quelle).
"""
import html
import json
import time
import urllib.parse

from core.sprache import t, t_html
from webui.bausteine import reihen_wort


def _zeit(ts):
    # Datumsformat bleibt in der Route (B19-Stufe); nur das Wort ist Text.
    if not ts:
        return t("vision.zeit.nie")
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))


def _ampel_farbe(a):
    return {"gruen": "var(--ok)", "gelb": "var(--warn)",
            "rot": "var(--crit, #c44)"}.get(a, "var(--dim)")


def _ampel_punkt(a, text=""):
    return (f'<span class="vs-amp" style="background:{_ampel_farbe(a)}"></span>'
            f"{html.escape(text)}")


STIL = """<style>
 .vs-kacheln { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
   gap:10px; margin-top:8px; }
 .vs-k { text-align:left; padding:10px 12px; border-radius:10px; cursor:pointer;
   background:var(--surface-2); border:1px solid var(--border);
   color:var(--text); font:inherit; }
 .vs-k:hover { border-color:var(--accent); }
 .vs-k.on { border-color:var(--ok); box-shadow:inset 0 0 0 1px var(--ok); }
 .vs-k b { display:block; font-size:15px; }
 .vs-k .vs-sub { color:var(--dim); font-size:12px; margin-top:2px; display:block; }
 .vs-k .vs-mark { color:var(--warn); font-size:12px; margin-top:4px; display:block; }
 .vs-amp { display:inline-block; width:10px; height:10px; border-radius:50%;
   margin-right:7px; vertical-align:baseline; }
 .vs-stufen { display:grid; grid-template-columns:auto auto 1fr; gap:4px 12px;
   align-items:baseline; margin-top:8px; }
 .vs-stufen .vs-nr { color:var(--dim); }
 .vs-sel { width:100%; max-width:640px; margin-top:8px; padding:7px 8px;
   border-radius:8px; background:var(--surface-2); color:var(--text);
   border:1px solid var(--border); font:inherit; }
 .vs-detail { margin-top:6px; font-size:13px; }
 .vs-detail .vs-quelle { font-size:11px; color:var(--dim); margin-top:2px; }
 .vs-deck { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
   gap:10px; margin-top:8px; }
 .vs-d { padding:10px; border-radius:8px; background:var(--surface-2);
   border:1px solid var(--border); border-left:3px solid var(--faint); }
 .vs-d.fertig { border-left-color:var(--ok); }
 .vs-d.offen { border-left-color:var(--warn); }
 .vs-d .vs-zahl { font-size:12px; color:var(--dim); }
 .vs-feld { display:flex; flex-wrap:wrap; gap:8px; align-items:center;
   margin:6px 0; }
 .vs-feld label { min-width:110px; color:var(--dim); }
 /* Endpunkt-Adressen sind lang und haben keine Trennstellen — ohne das hier
    schiebt eine offizielle API-URL die ganze Seite auf einem Telefon nach
    rechts (auf 360 px gemessen: 82 px Ueberlauf, Gate-Stufe S9). */
 .vs-url { overflow-wrap:anywhere; word-break:break-all; }
 /* Save-Leiste: klebt unten, solange die Seite offen ist. Bewusst KEIN
    Farbwechsel-Blinken — der Zustand steht als Text daneben. */
 .vs-savebar { position:sticky; bottom:0; z-index:5; display:flex;
   flex-wrap:wrap; gap:12px; align-items:center; margin:14px 0 0;
   padding:12px 14px; border-radius:10px; background:var(--surface);
   border:1px solid var(--border); box-shadow:0 -6px 18px rgba(0,0,0,.28); }
 .vs-savebtn { font-size:16px; padding:10px 22px; font-weight:600; }
 .vs-savebar.dirty { border-color:var(--warn); }
 .vs-savebar.dirty .vs-savebtn { box-shadow:0 0 0 2px var(--warn); }
 .vs-dirty { color:var(--warn); font-size:13px; }
 .vs-dirty-top { display:inline-block; vertical-align:middle; margin-left:10px;
   padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600;
   color:var(--warn); border:1px solid var(--warn); }
 .vs-status { color:var(--dim); font-size:13px; }
 /* Drei-Wege-Frage vor dem Test (Bestand hat nur confirm(), das kann zwei). */
 .vs-modal { position:fixed; inset:0; z-index:50; display:flex;
   align-items:center; justify-content:center; background:rgba(0,0,0,.55); }
 .vs-modal .vs-box { max-width:520px; margin:16px; padding:18px 20px;
   border-radius:12px; background:var(--surface); border:1px solid var(--border); }
 .vs-modal h4 { margin:0 0 8px; font-size:16px; }
 .vs-modal p { margin:0 0 12px; font-size:14px; line-height:1.5; }
 .vs-modal .vs-w { display:flex; flex-wrap:wrap; gap:8px; }
</style>"""


def _kopf():
    # Der "not saved"-Hinweis steht ZWEIMAL auf der Seite (User 08.08. abend:
    # "oben nicht gesichert"): hier neben der Ueberschrift und unten an der
    # klebenden Save-Leiste. Zwei Anzeigen, EIN Zustand — beide schaltet
    # dieselbe Stelle im Browser-Code.
    return (
        f'<h2>{t("vision.titel")} <span id="vision-dirty-oben" class="vs-dirty-top" '
        f'hidden>{t("vision.kopf.dirty")}</span></h2>'
        # Stufe 3 (t_html): Einleitungs-Absatz mit <b> mitten im Satz.
        f'<p class="sub">{t_html("vision.kopf.einleitung")}</p>')


def _hinweis():
    """Hinweisfeld: welches Modell, dass es auf einem EIGENEN Rechner im Netz
    laufen kann, und der ausdrueckliche Satz zur Host-Groesse (§4)."""
    return (
        f'<div class="card"><b>{t("vision.hinweis.titel")}</b>'
        # Stufe 3 (t_html): die vier Absaetze mit <b>/<code> mitten in der
        # Prosa — Produktnamen darin (llama.cpp, Qwen3.5, docker stats)
        # bleiben je Sprache wortgleich (§8.7, Kommentar am Schluessel).
        f'<div>{t_html("vision.hinweis.modell_satz")}</div>'
        '<div class="dim" style="margin-top:6px">'
        f'{t_html("vision.hinweis.host_satz")}</div>'
        f'<div class="dim">{t_html("vision.hinweis.mess_satz")}</div>'
        f'<div class="dim">{t_html("vision.hinweis.kosten_satz")}</div></div>')


def _schalter(vor, aktiv, vcfg):
    """Schalter nach dem bestehenden armed-Muster; gesperrt, solange eine der
    drei Vorbedingungen fehlt (E4) — mit Klartext, was fehlt."""
    if vor.get("erfuellt"):
        knopf = (f'<button class="gtb{" on" if aktiv else ""}" '
                 f'onclick="visionSchalter({str(not aktiv).lower()})">'
                 f'{t("vision.schalter.knopf_aus") if aktiv else t("vision.schalter.knopf_an")}</button>')
        rest = ""
    else:
        knopf = f'<button class="gtb" disabled>{t("vision.schalter.knopf_an")}</button>'
        # .362 (Feld-Fund Tester B): uebersetzte fehlt-Zeilen statt der
        # EN-Literale des Fach-Moduls. Drei LITERALE t()-Aufrufe (kein
        # dynamischer Key — der Sprach-Checker ist dafuer strukturell blind
        # und die Tote-Schluessel-Pruefung braucht die Literale; Gate-Fang
        # beim ersten Anlauf), lazy je Code (nur gebrauchte Keys formatieren).
        def _fehlt_text(code, params):
            if code == "galerien":
                return t("vision.schalter.fehlt_galerien", **params)
            if code == "test":
                return t("vision.schalter.fehlt_test")
            return t("vision.schalter.fehlt_kandidaten")
        rest = (f'<div class="dim" style="margin-top:6px">{t("vision.schalter.fehlt")}<ul>'
                + "".join(f'<li>{html.escape(_fehlt_text(c, p))}</li>'
                          for c, p in vor["fehlt_codes"])
                + "</ul></div>")
    # B9: je Zweig ein GANZER Titel-Satz statt "… is " + zustand.
    titel = (t("vision.schalter.titel_an") if aktiv
             else t("vision.schalter.titel_aus"))
    return ('<div class="card"><b>' + titel + "</b> "
            + knopf + rest
            + f'<div class="dim" style="margin-top:6px">{t("vision.schalter.aus_satz")}</div>'
            '<span id="vision-schalter-status" class="dim"></span></div>'
            + _meldungen(vcfg))


# Die Whitelist-Schluessel, die DIESE Seite als Haken rendert — EINE Quelle.
# Der Dienst legt genau diese Werte in den Vision-Block, bevor er rendert.
# Grund (Live-Fund 09.08.): die Haken lasen aus dem Block, lagen aber nie darin
# — sie standen deshalb IMMER unangehakt da, obwohl im Store True stand. Wer
# das nur an den damals zwei Feldern repariert, baut denselben Fehler beim
# dritten wieder ein; deshalb steht die Menge hier und wird drueben GELESEN.
CFGV_HAKEN = ("vision_doppellauf", "vision_meldung",
              "vision_alarm_unbestaetigt")


def _meldungen(vcfg):
    """Die zwei OPTIONALEN Meldungen (User-Entscheide 08.08.), beide aus im
    Auslieferungszustand. Der Erklaertext sagt bei beiden die Wahrheit ueber
    ihre Grenze — Vision bekommt kein Stimmrecht ueber die bestehenden Alarme,
    kann keinen aufheben und keinen ausloesen, ausser diesem einen hier."""
    def _kasten(feld, titel, satz):
        an = " checked" if vcfg.get(feld) else ""
        return ('<label style="display:block;margin-top:8px">'
                f'<input type="checkbox" id="cfgv-{feld}"{an}> <b>{titel}</b>'
                f'</label><div class="dim">{satz}</div>')
    return (f'<div class="card"><b>{t("vision.frage.titel")}</b>'
            + _kasten("vision_doppellauf",
                      t("vision.frage.doppel_titel"),
                      t("vision.frage.doppel_satz"))
            + "</div>"
            f'<div class="card"><b>{t("vision.meld.titel")}</b>'
            f'<div class="dim">{t("vision.meld.satz")}</div>'
            + _kasten("vision_meldung", t("vision.meld.judged_titel"),
                      t("vision.meld.judged_satz"))
            + _kasten("vision_alarm_unbestaetigt",
                      t("vision.meld.alarm_titel"),
                      t("vision.meld.alarm_satz"))
            + "</div>")


def _kacheln(kacheln, reihe, gewaehlt):
    """Die Anbieter-Reihe. Jede Kachel sagt, was sie von dir braucht — und die
    Anthropic-Kachel traegt ihren Klartext-Hinweis direkt daran (E7)."""
    was = {"key": t("vision.kachel.was_key"),
           "host_port": t("vision.kachel.was_host"),
           "url_key": t("vision.kachel.was_url")}
    stuecke = []
    for name in reihe:
        k = kacheln[name]
        # Kachel-Flaeche bleibt nackt (User-Entscheid 08.08.): keine Anreisser-
        # Marke, kein Hinweis-Text — auch nicht nach der Wahl (E7 fortgeschrieben,
        # 08.08. spaetabend). Die Kacheln beschreiben nur den Weg, sie warnen und
        # behaupten nichts.
        mark = ""
        stuecke.append(
            f'<button class="vs-k{" on" if name == gewaehlt else ""}" '
            f'onclick="visionKachel(\'{html.escape(name, quote=True)}\')">'
            f'<b>{html.escape(k["label"])}</b>'
            f'<span class="vs-sub">{html.escape(k["anbieter"])}</span>'
            f'<span class="vs-sub">{html.escape(was.get(k["eingabe"], ""))}'
            f"</span>{mark}</button>")
    return (f'<div class="card"><b>{t("vision.kachel.titel")}</b>'
            f'<p class="dim">{t("vision.kachel.satz")}</p>'
            f'<div class="vs-kacheln">{"".join(stuecke)}</div></div>')


def _verbindung(vcfg, kname, k, endpunkt_anzeige, pruef_wort):
    """Genau die Felder der gewaehlten Kachel — nicht mehr. Der Key steht nie
    im Wert, immer nur als Platzhalter.

    KACHELABHAENGIGE WORTE (User-Fund 08.08. aus der Live-Nutzung): auf einer
    Kachel ohne Key-Pflicht hiess der Knopf trotzdem "Check the key" und das
    Feld sagte "paste your key here" — beides suggerierte eine Pflicht, die es
    dort nicht gibt. Das Wort kommt aus core/vision.pruef_wort (abgeleitet aus
    `key_pflicht`), nicht aus einer Liste von Kachel-Namen."""
    pflicht = bool(k.get("key_pflicht"))
    # Stufe-2-Grenze (B9/§8.2): "Check the {pruef_wort}" ist ein Nomen-in-
    # Rahmen-Konstrukt, das Wort kommt aus core/vision.pruef_wort — der
    # Umbau auf Ganz-Satz-Schluessel je Wort ist ein eigener Zug.
    knopf = f"Check the {pruef_wort}"
    key_ph = (t("vision.verb.key_gespeichert")
              if vcfg.get("api_key_gesetzt") else
              t("vision.verb.key_pflicht_ph") if pflicht else
              t("vision.verb.key_frei_ph"))
    # Die gewaehlte Kachel faehrt als verstecktes Feld mit: jeder Knopf auf
    # dieser Seite schickt EIN Formular, und die Kachel entscheidet, welche
    # Felder ueberhaupt gelten.
    felder = [f'<input type="hidden" id="vis-kachel" '
              f'value="{html.escape(kname, quote=True)}">']
    if k["eingabe"] == "host_port":
        felder.append(
            f'<div class="vs-feld"><label>{t("vision.verb.host")}</label>'
            f'<input id="vis-host" size="26" value="{html.escape(vcfg.get("host") or "")}" '
            f'placeholder="{t("vision.verb.host_ph")}">'
            f'<label style="min-width:auto">{t("vision.verb.port")}</label>'
            f'<input id="vis-port" size="6" value="{html.escape(str(vcfg.get("port") or ""))}" '
            'placeholder="8080"></div>'
            f'<div class="dim">{t("vision.verb.host_satz")}</div>')
    elif k["eingabe"] == "url_key":
        # Vorbefuellt mit dem Beispiel-Endpunkt aus dem Kachel-Vertrag (EIN
        # Eintrag, kein Literal im Renderer) — ein GESPEICHERTER Wert gewinnt
        # immer.
        felder.append(
            f'<div class="vs-feld"><label>{t("vision.verb.endpunkt")}</label>'
            f'<input id="vis-endpunkt" size="46" '
            f'value="{html.escape(endpunkt_anzeige or k.get("beispiel_url") or "")}" '
            'placeholder="https://your-service.example/v1"></div>'
            + ("" if endpunkt_anzeige else
               f'<div class="dim">{t("vision.verb.endpunkt_satz")}</div>')
            # .167: der Satz nennt die beiden Traeger, ohne das woertliche
            # Zugangsdaten-Muster auszuschreiben — das Datenschutz-Gate
            # (Stufe 10) sucht nach genau diesem Muster im Image, und es soll
            # weiter danach suchen duerfen. Die Aussage bleibt unveraendert.
            # Stufe 3 (t_html): <b>-Vorsatz mitten im Satz.
            + f'<div class="dim">{t_html("vision.verb.key_ort")}</div>'
            f'<div class="vs-feld"><label>{t("vision.verb.betriebsart")}</label>'
            f'<select id="vis-betriebsart">'
            f'<option value="extern"{" selected" if vcfg.get("betriebsart") != "lokal" else ""}>'
            f'{t("vision.verb.betriebsart_extern")}</option>'
            f'<option value="lokal"{" selected" if vcfg.get("betriebsart") == "lokal" else ""}>'
            f'{t("vision.verb.betriebsart_lokal")}</option></select></div>')
    else:
        felder.append(
            f'<div class="vs-feld"><label>{t("vision.verb.adresse")}</label>'
            f'<code class="vs-url">{html.escape(k["basis"])}</code></div>'
            f'<div class="dim">{t("vision.verb.adresse_satz")}</div>')
    # Das Key-Feld steht bei JEDER Kachel — auch ein eigener Server kann einen
    # verlangen. Der Knopf daneben ist die Sofort-Pruefung: er holt die
    # Modell-Liste und ist damit zugleich der einzige Weg zur Modellwahl.
    felder.append(
        f'<div class="vs-feld"><label>{t("vision.verb.key")}</label>'
        f'<input id="vis-api_key" size="46" value="" autocomplete="off" '
        f'placeholder="{key_ph}">'
        f'<button class="gtb on" onclick="visionSchluessel(this)">{knopf}'
        "</button>"
        '<span id="vision-key-status" class="dim"></span></div>'
        + ("" if pflicht else
           f'<div class="dim">{t("vision.verb.key_frei_satz")}</div>'))
    # Stufe-2-Grenze (B9): der Schluss-Satz splict pruef_wort in einen
    # Rahmen — bleibt literal (s. knopf-Kommentar oben).
    return (f'<div class="card"><b>{t("vision.verb.titel")}</b>' + "".join(felder)
            + f'<div class="dim" style="margin-top:6px">Checking the '
            f"{html.escape(pruef_wort)} asks the endpoint which models it has. "
            "It costs nothing and no picture is sent.</div></div>")


def _klassen(hinweis):
    """Der Orientierungssatz zur Modellklasse (.165, User-Wunsch 09.08.).

    Er kommt FERTIG aus core.registry.vision_klassen_hinweis und wird hier nur
    ausgegeben — kein Anbieter-Satz steht in diesem Renderer. Waere er hier
    formuliert, wuerde er beim naechsten Messlauf still unwahr; so kann er das
    nicht, weil er aus denselben Zahlen entsteht wie die Badges."""
    h = dict(hinweis or {})
    if not h.get("hat"):
        return ""
    # .168: der ANKER steht vorn und hervorgehoben — das ist die Frage, die ein
    # Nutzer wirklich hat ("welches Modell muss ich mindestens nehmen"). Danach
    # die Zahlen, und zuletzt der Querschnitts-Satz zum Material: er
    # relativiert die Modellwahl und gehoert deshalb an JEDE Kachel.
    # Preise stehen hier bewusst NICHT (Entscheid 09.08.).
    st = ""
    if h.get("anker"):
        st += (f'<div class="vs-detail"><b>{html.escape(h["anker"])}</b></div>')
    st += f'<div class="vs-detail dim">{html.escape(h["text"])}</div>'
    if h.get("material"):
        st += f'<div class="vs-detail dim">{html.escape(h["material"])}</div>'
    return st


def _modellwahl(prot, gewaehlt, stand, kname, pruef_wort="key",
                klassen=None):
    """Modell-Karten mit den Mess-Badges. Zwei Regeln tragen diese Funktion:

    HARTE REGEL (§5): hier wird NIE ein Modell vorab angezeigt. Jede Karte
    stammt aus dem Entdeckungs-Ergebnis DIESES Endpunkts; die Registry liefert
    nur die Anmerkung an einem gefundenen Modell, nie eine eigene Liste. Vor
    der ersten erfolgreichen Verbindung steht hier deshalb kein einziger
    Modellname — auch kein vermessener als Vorschlag.

    Ein Ergebnis einer ANDEREN Kachel gilt nicht: es wird verworfen, statt
    fremde Modelle als Auswahl anzubieten (Tiefenverteidigung — der Handler
    filtert bereits, dieser Renderer verlaesst sich nicht darauf).

    Kein Wort ueber Abos, Tarife oder Key-Quellen (User 08.08.: "das weiss der
    User") — das Feld heisst schlicht API key."""
    if prot and prot.get("kachel") and prot.get("kachel") != kname:
        prot = None
    if not prot:
        # Stufe 3 (t_html, B9-konform): je pruef_wort EIN ganzer Block-
        # Schluessel (Woerter aus core/vision.pruef_wort: key/connection,
        # Deckungs-Vertrag am Schluessel-Kommentar in en.py). Das Zitat
        # <b>Check the key/connection</b> haengt am noch literalen
        # Pruef-Knopf (B9-Grenze in _verbindung).
        leer = (t_html("vision.modell.leer_key") if pruef_wort == "key"
                else t_html("vision.modell.leer_verbindung"))
        return (f'<div class="card"><b>{t("vision.modell.titel")}</b>'
                f'<div id="vision-modell-info" class="dim">{leer}</div>'
                + _klassen(klassen)
                + '<div id="vision-modell-wahl"></div>'
                '<span id="vision-modell-status" class="dim"></span></div>')
    if not prot.get("ok"):
        return (f'<div class="card"><b>{t("vision.modell.titel")}</b>'
                '<div id="vision-modell-info">'
                + _ampel_punkt("rot", prot.get("text")
                               or t("vision.modell.verweigert"))
                + f'</div><div class="dim">{t("vision.modell.geprueft", zeit=_zeit(prot.get("ts")))} '
                f'<code class="vs-url">'
                f'{html.escape(prot.get("endpunkt") or "")}</code></div>'
                + _klassen(klassen)
                + '<div id="vision-modell-wahl"></div>'
                '<span id="vision-modell-status" class="dim"></span></div>')
    # Ein DROPDOWN der GEFUNDENEN Modelle (User 08.08.): der User sieht in der
    # Liste, was da ist, und waehlt eines aus. Ein <option> traegt kein Markup,
    # also steht die Registry-Anmerkung als Klartext am Eintrag (Modellname —
    # Badge-Text aus der Registry); die ausfuehrliche Fassung mit Datum, Quelle
    # und Vorbehalten steht farbig unter der getroffenen Wahl. Hier steht KEINE
    # Mess-Zahl, auch nicht als Beispiel im Kommentar — sie veraltet still.
    opt, gefunden = [], False
    if not gewaehlt:
        opt.append(f'<option value="" selected>{t("vision.modell.opt_wahl")}</option>')
    for m in prot.get("modelle") or []:
        b = m.get("badge") or {}
        ist = m["id"] == gewaehlt
        gefunden = gefunden or ist
        anmerkung = b["text"] if b.get("gemessen") else t("vision.modell.ungetestet")
        opt.append(f'<option value="{html.escape(m["id"], quote=True)}"'
                   + (" selected" if ist else "") + ">"
                   + html.escape(f'{m["id"]} — {anmerkung}') + "</option>")
    if gewaehlt and not gefunden:
        # Stiller Verlust waere die Alternative: die gespeicherte Wahl einfach
        # nicht mehr anzeigen. Sie bleibt sichtbar und sagt, was mit ihr ist.
        opt.insert(0, f'<option value="{html.escape(gewaehlt, quote=True)}" '
                   "selected>" + html.escape(gewaehlt)
                   + t("vision.modell.opt_verschollen")
                   + "</option>")
    unten = f'<div class="vs-detail dim">{t("vision.modell.wahl_satz")}</div>'
    gb = next((m.get("badge") or {} for m in prot.get("modelle") or []
               if m["id"] == gewaehlt), None)
    if gewaehlt and gb is None:
        unten = ('<div class="vs-detail" style="color:var(--warn)">'
                 f'{t("vision.modell.verschollen_satz")}</div>')
    elif gb is not None and gb.get("gemessen"):
        extra = []
        if not gb.get("exakt"):
            extra.append(t("vision.modell.fremde_plattform"))
        if not gb.get("roh_archiviert"):
            extra.append(t("vision.modell.kein_rohergebnis"))
        if gb.get("unvollstaendig"):
            extra.append(gb["unvollstaendig"])
        if gb.get("notiz"):
            extra.append(gb["notiz"])
        farbe = "var(--ok)" if gb.get("abweisen") == "✓" else "var(--warn)"
        unten = (f'<div class="vs-detail"><span style="color:{farbe}">'
                 f'{html.escape(gb["text"])}</span>'
                 f'<div class="vs-quelle">'
                 f'{t("vision.modell.gemessen", datum=html.escape(gb.get("datum") or ""), quelle=html.escape(gb.get("quelle") or ""))}'
                 + "".join(f"<br>{html.escape(x)}" for x in extra)
                 + "</div></div>")
    elif gb is not None:
        unten = f'<div class="vs-detail dim">{t("vision.modell.ungemessen_satz")}</div>'
    return (f'<div class="card"><b>{t("vision.modell.titel")}</b>'
            '<div id="vision-modell-info">'
            + _ampel_punkt("gruen", prot.get("text") or "")
            # Stufe 3 (t_html): Antwort-Prosa mit <b>-Inseln; {zeit}/{stand}
            # escapt t_html selbst (quote=True — deckt das bisherige
            # html.escape(stand) mit ab, _zeit liefert nur Ziffern/never).
            + f'</div><div class="dim">'
            f'{t_html("vision.modell.antwort_satz", zeit=_zeit(prot.get("ts")), stand=stand or "")}</div>'
            + '<div id="vision-modell-wahl">'
            + '<select id="vision-modell" class="vs-sel" '
            'onchange="visionModell(this)">'
            + "".join(opt) + "</select></div>" + unten
            + _klassen(klassen)
            # .213 (User 16.08.: manche Endpunkte listen nicht alles): eine
            # Hand-ID wird per Mini-Text-Anfrage REAL geprueft und wandert
            # erst dann in die Liste — die §5-Regel (nie Ungeprueftes
            # speichern) bleibt intakt, die Pruefung IST eine Entdeckung.
            + '<div class="vs-feld" style="margin-top:10px">'
              f'<label>{t("vision.modell.manuell")}</label>'
              '<input id="vis-modell-manuell" size="30" '
              f'placeholder="{t("vision.modell.manuell_ph")}">'
              '<button class="gtb" type="button" '
              f'onclick="visModellManuell(this)">{t("vision.modell.manuell_knopf")}</button>'
              '<span id="vis-mm-status" class="dim"></span></div>'
            + f'<div class="dim">{t("vision.modell.manuell_satz")}</div>'
            # Stufe 2 Tranche D (§8.4): die Script-Texte kommen server-
            # seitig via json.dumps(t(...)) byte-treu ("checking …" traegt
            # den Rohpunkt-Dreier — ensure_ascii=False wie das Original).
            + '<script>function visModellManuell(b){'
              'var f=document.getElementById("vis-modell-manuell");'
              'var s=document.getElementById("vis-mm-status");'
              'if(!f.value.trim()){s.textContent='
            + json.dumps(t("vision.modell.js_id_fehlt")) + ';return;}'
              'b.disabled=true;s.textContent='
            + json.dumps(t("vision.modell.js_prueft"), ensure_ascii=False)
            + ';'
              'fetch("/vision/modell_manuell",{method:"POST",'
              'body:JSON.stringify({modell:f.value.trim()})})'
              '.then(function(r){return r.json();})'
              '.then(function(d){s.textContent=d.msg;'
              'if(d.ok){setTimeout(function(){location.reload();},1200);}'
              'else{b.disabled=false;}})'
              '.catch(function(){s.textContent='
            + json.dumps(t("vision.modell.js_fehler"))
            + ';b.disabled=false;});}'
              '</script>'
            + '<span id="vision-modell-status" class="dim"></span></div>')


def _prompt(vcfg, anker, prompt_std):
    """Der Urteils-Prompt. Das Feld zeigt IMMER einen Wortlaut (User-Fund
    08.08.): ohne eigenen Prompt stand hier bisher nichts, und niemand konnte
    sehen, was das System eigentlich fragt. Steht der Default drin und wird
    gespeichert, rechnet die Pruefung ihn wieder auf "kein eigener Prompt"
    zurueck — die Marke "custom prompt" gilt nur bei echt abweichendem
    Wortlaut."""
    eigen = bool(str(vcfg.get("prompt") or "").strip())
    prompt = vcfg.get("prompt") or prompt_std
    # Stufe 3 (t_html) im eigen-Zweig: <b>custom prompt</b> mitten im Satz —
    # zitiert die Urteils-Marke (visiontest.vision.custom_prompt).
    stand = (f'<div class="dim">{t_html("vision.prompt.eigen_satz")}</div>'
             if eigen else
             f'<div class="dim">{t("vision.prompt.standard_satz")}</div>')
    return (f'<div class="card"><b>{t("vision.prompt.titel")}</b>'
            f'<div class="dim">{t("vision.prompt.satz")}</div>' + stand
            + f'<textarea id="vis-prompt" rows="6" style="width:100%">'
            f"{html.escape(prompt)}</textarea>"
            '<div class="dim" style="white-space:pre-wrap;opacity:.75;'
            'border-left:3px solid var(--dim);padding-left:8px;margin-top:4px">'
            f"{html.escape(anker)}</div>"
            f'<button class="gtb" onclick="visionPromptZurueck()">{t("vision.prompt.knopf_zurueck")}</button>'
            # Der Default-WORTLAUT geht als Wert in die Seite (nicht als
            # zweiter Text im Browser-Code): der Zuruecksetzen-Knopf schreibt
            # genau ihn ins Feld. Quelle ist dieselbe Konstante, die auch der
            # Urteilspfad benutzt — kein zweites Literal.
            f"<script>const VIS_PROMPT_STD = {json.dumps(prompt_std)};</script>"
            "</div>")


def _zahlen(vcfg, k):
    """Die zwei Whitelist-Zahlen plus der think-Schalter, wenn die Kachel ihn
    kann (Faehigkeits-Flag statt blindem Knopf)."""
    denk = ""
    if k.get("kann_think_schalter"):
        # .211: der WIRKSAME Wert kommt aus der einen Quelle (Default an,
        # User-Entscheid 16.08. nach dem Token-Befund) — die Checkbox zeigt,
        # was wirklich gesendet wird, nicht den rohen Store-Wert.
        from core.vision import think_aus_wirksam
        denk = ('<div class="vs-feld"><label><input type="checkbox" '
                f'id="vis-think_aus"{" checked" if think_aus_wirksam(vcfg, k) else ""}> '
                f'{t("vision.zahlen.think")}</label></div>'
                f'<div class="dim">{t("vision.zahlen.think_satz")}</div>')
    return (f'<div class="card"><b>{t("vision.zahlen.titel")}</b>'
            f'<div class="vs-feld"><label>{t("vision.zahlen.max_tokens")}</label>'
            f'<input id="cfgv-vision_max_tokens" size="8" '
            f'value="{html.escape(str(vcfg.get("max_tokens") or ""))}">'
            f'<label>{t("vision.zahlen.timeout")}</label>'
            f'<input id="cfgv-vision_timeout_s" size="8" '
            f'value="{html.escape(str(vcfg.get("timeout_s") or ""))}"></div>'
            f'<div class="dim">{t("vision.zahlen.satz")}</div>'
            + denk + "</div>")


def _cloud(vcfg, endpunkt_anzeige, k):
    """Die Cloud-Bestaetigung (§9). Sie richtet sich nach der ANGEZEIGTEN
    Kachel, nicht nach der gespeicherten Betriebsart — sonst entsteht die
    Henne-Ei-Lage, die am 08.08. einen Nutzer blockiert hat: wer lokal
    gespeichert hat und auf einen externen Anbieter wechselt, bekam die
    Bestaetigungs-Karte nie zu sehen, waehrend das Speichern sie verlangte.
    Gezeigt wird sie bei jeder Kachel, die ins Internet fuehrt (die drei
    Namens-Anbieter fest, Custom konservativ); bei der Lokal-Kachel nie.
    ANGEHAKT ist sie nur, wenn die Bestaetigung wirklich gespeichert ist."""
    if k.get("betriebsart") != "extern":
        return ""
    ziel = (endpunkt_anzeige or k.get("basis") or k.get("beispiel_url")
            or t("vision.cloud.ziel_fallback"))
    # Stufe 3 (t_html) im ersten Satz: <b>{ziel}</b> mitten im Satz — {ziel}
    # escapt t_html selbst (quote=True, wie das bisherige html.escape).
    return ('<div class="card" style="border-left-color:var(--warn)">'
            f'<b>{t("vision.cloud.titel")}</b>'
            f'<div class="dim">{t_html("vision.cloud.sendet_satz", ziel=ziel)} '
            f'{t("vision.cloud.satz")}</div>'
            '<label style="display:block;margin-top:6px"><input type="checkbox" '
            f'id="vis-cloud_ok"{" checked" if vcfg.get("cloud_ok") else ""}> '
            + t("vision.cloud.bestaetigung")
            + (f' <span class="dim">{t("vision.cloud.bestaetigt", zeit=_zeit(vcfg.get("cloud_ok_ts")))}</span>'
               if vcfg.get("cloud_ok") else "") + "</label></div>")


def _stufen_zeilen(stufen):
    """Das Testlog: je Stufe eine Zeile mit Ampel, Namen und den GEMESSENEN
    Werten. Keine Prosa-Glaettung — was gemessen wurde, steht da (Antwortzeit,
    n richtig von gesamt, Token gegen die Referenz)."""
    zeilen = []
    # Stufe-2-Grenze: Stufen-NAME und -TEXT kommen als Daten aus dem
    # Testprotokoll (Dienst-Seite, eigene Quelle); "{n} s"/"%" sind
    # sprachneutrale Einheiten (§8.6).
    for s in stufen or []:
        werte = []
        if s.get("dauer_s") is not None:
            werte.append(f'{s["dauer_s"]} s')
        if s.get("treffer") is not None:
            werte.append(t("vision.test.treffer", n=s["treffer"]))
        if s.get("ist") is not None:
            werte.append(t("vision.test.tokens", ist=s["ist"], soll=s.get("soll")))
            if s.get("anteil") is not None:
                werte.append(f'{int(round(float(s["anteil"]) * 100))}%')
        for l in s.get("laeufe") or []:
            werte.append(f'{l.get("arm")}: {l.get("wahl") or l.get("grund")}'
                         f'{"" if l.get("wahl") == l.get("soll") else t("vision.test.falsch")}')
        mess = ((' <span class="dim">&middot; '
                 + " &middot; ".join(html.escape(str(w)) for w in werte)
                 + "</span>") if werte else "")
        zeilen.append(f'<div class="vs-nr">{s.get("nr")}</div>'
                      f'<div>{_ampel_punkt(s.get("ampel"), s.get("name") or "")}</div>'
                      f'<div id="vs-log-{s.get("nr")}">'
                      f'{html.escape(s.get("text") or "")}{mess}</div>')
    return "".join(zeilen)


def _speichern():
    """Der Save-Knopf (User-Fund 08.08. abend, woertlich: "Save wird leider
    vergessen, zu klein, zu unscheinbar" — er hat mehrfach konfiguriert,
    getestet und nie gespeichert; die echten Urteile liefen deshalb weiter
    gegen die ALTE Verbindung).

    Drei Aenderungen, alle aus diesem einen Fall:
      * der Knopf ist ein grosser Primaer-Knopf und klebt am unteren Rand,
        solange die Seite offen ist — er kann nicht mehr wegscrollen,
      * jede Aenderung faerbt ihn und schreibt "unsaved changes" daneben,
      * verlassen oder testen mit ungespeicherten Werten fragt vorher nach
        (der Test benutzt die TIPP-Werte, die Erkennung die GESPEICHERTEN —
        genau diese Verwechslung ist passiert)."""
    # ZITAT-FOLGE: js.vision.dirty_text aller fuenf Sprachen zitiert "Save"
    # sinngemaess ("press Save") — beim Uebersetzen dieses Knopfs nachziehen.
    return ('<div class="vs-savebar" id="vision-savebar">'
            '<button class="gtb on vs-savebtn" onclick="visionSpeichern()">'
            f'{t("vision.save.knopf")}</button>'
            f'<span id="vision-dirty" class="vs-dirty" hidden>{t("vision.save.dirty")}</span>'
            '<span id="vision-status" class="vs-status"></span></div>')


def _test(prot):
    """Test-Knopf + Testlog als AMPEL-REIHE (§5, dreistufig).

    Die drei Stufen laufen seit V4 EINZELN (der Browser ruft sie nacheinander):
    lokal dauert eine Stufe Minuten, und ein Knopf, der minutenlang schweigt,
    sieht aus wie ein Haenger. Waehrend des Laufs schreibt der Browser in
    dieselben Log-Zeilen, die der Server danach rendert — es gibt nur EIN
    Log-Format, und es ueberlebt den Reload."""
    kopf = (
        f'<div class="card"><b>{t("vision.test.titel")}</b>'
        # Stufe 3 (t_html): der Drei-Stufen-Text mit <br>/<b>-Gliederung.
        f'<p class="dim">{t_html("vision.test.stufen_satz")}</p>'
        f'<button class="gtb on" onclick="visionTest(this)">{t("vision.test.knopf")}</button> '
        '<span id="vision-test-status" class="dim"></span>')
    if not prot:
        # Die drei Zeilen stehen auch UNGETESTET schon da (als "not run") —
        # dann hat der Live-Fortschritt einen Platz zum Schreiben, und der
        # Leerzustand sagt trotzdem klar, dass noch nichts gelaufen ist.
        leer = [{"nr": nr, "name": name, "ampel": "grau",
                 "text": t("vision.test.nicht_gelaufen")}
                for nr, name in ((1, t("vision.test.stufe1")),
                                 (2, t("vision.test.stufe2")),
                                 (3, t("vision.test.stufe3")))]
        return (kopf + f'<div class="dim" style="margin-top:8px">{t("vision.test.ungetestet")}</div>'
                f'<div class="vs-stufen">{_stufen_zeilen(leer)}</div></div>')
    return (kopf + f'<div style="margin-top:8px">'
            f'{t("vision.test.letzter", zeit=_zeit(prot.get("ts")))} '
            f'<code class="vs-url">{html.escape(prot.get("endpunkt") or "")}</code> &mdash; '
            f'{_ampel_punkt(prot.get("ampel"), str(prot.get("ampel") or "").upper())}'
            "</div>"
            f'<div class="vs-stufen">{_stufen_zeilen(prot.get("stufen"))}</div>'
            "</div>")


def _galerien(deckung, galerien, vor, rt):
    """Deckungs-Anzeige je Person mit gelerntem Koerpermodell (§4) und der
    Einstieg in den Wizard. Der Nenner ist der des Koerpermodells — die
    Gesichts-Sammlung hat einen anderen, und beide nebeneinander haben hier
    schon einmal Verwirrung gestiftet."""
    n_fertig = len(galerien or {})
    karten = []
    for d in deckung or []:
        g = (galerien or {}).get(d["person"])
        pruef = (g or {}).get("pruefung") or {}
        if g and pruef.get("status") == "gut":
            kl, stand = "fertig", t("vision.galerien.stand_gut",
                                    zeit=_zeit(g.get("abnahme_ts")),
                                    zellen=g.get("groesse"))
        elif g:
            kl, stand = "offen", html.escape(pruef.get("text")
                                             or t("vision.galerien.pruefen"))
        elif d["max_groesse"]:
            kl, stand = "offen", t("vision.galerien.keine")
        else:
            kl, stand = "offen", t("vision.galerien.zu_wenig",
                                   n=d['gesamt'])
        # Tranche D (Kennung/Anzeige-Trennung 3b): Anzeige-Wort aus dem
        # Schluessel (bausteine.reihen_wort), die Kennung bleibt Datenwert;
        # der reihen_text-Parameter bleibt als Daten-Vertrag unveraendert.
        reihen = " &middot; ".join(
            f"{html.escape(reihen_wort(r))} {d['je_reihe'].get(r, 0)}"
            for r in ("vorn", "seitlich", "hinten"))
        knopf = ""
        if d["max_groesse"]:
            knopf = ('<div style="margin-top:6px"><a class="gtb" href="/vision/galerie?person='
                     + urllib.parse.quote(d["person"]) + '">'
                     + (t("vision.galerien.knopf_auffrischen") if g
                        else t("vision.galerien.knopf_bauen")) + "</a></div>")
        karten.append(
            f'<div class="vs-d {kl}"><b>{html.escape(d["person"])}</b>'
            f"<div>{stand}</div>"
            f'<div class="vs-zahl">{t("vision.galerien.zahl", n=d["gesamt"], reihen=reihen)}</div>{knopf}</div>')
    return (f'<div class="card" id="galerien"><b>{t("vision.galerien.titel")}</b>'
            f'<div>{t("vision.galerien.stand", n=n_fertig, min=vor.get("galerien_min", 2))}</div>'
            f'<div class="dim">{t("vision.galerien.satz")}</div>'
            f'<div class="vs-deck">{"".join(karten)}</div></div>')


def seite(vcfg, kacheln, kachel_reihe, vorbedingungen, testprotokoll,
          schluesselprotokoll, anker, prompt_std, endpunkt_anzeige, deckung,
          galerien, messwerte_stand="", reihen_text=None, pruef_wort="key",
          klassen_hinweis=None):
    """Der Seiten-INHALT (ohne layout/banner — die bleiben beim Handler).

    `pruef_wort` kommt aus core/vision.pruef_wort(kachel) und entscheidet, ob
    der Pruef-Knopf vom Schluessel oder von der Verbindung spricht — der
    Renderer leitet das NICHT selbst aus dem Kachel-Namen ab."""
    kname = vcfg.get("kachel") or "lokal"
    k = kacheln.get(kname) or kacheln["lokal"]
    return (STIL + _kopf()
            + _schalter(vorbedingungen, bool(vcfg.get("aktiv")), vcfg)
            + _hinweis()
            + _kacheln(kacheln, kachel_reihe, kname)
            + _verbindung(vcfg, kname, k, endpunkt_anzeige, pruef_wort)
            + _modellwahl(schluesselprotokoll, vcfg.get("modell"),
                          messwerte_stand, kname, pruef_wort,
                          klassen_hinweis)
            + _cloud(vcfg, endpunkt_anzeige, k)
            + _zahlen(vcfg, k)
            + _prompt(vcfg, anker, prompt_std)
            + _speichern()
            + _test(testprotokoll)
            + _galerien(deckung, galerien, vorbedingungen,
                        dict(reihen_text or {})))
