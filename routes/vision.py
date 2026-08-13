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
"""
import html
import json
import time
import urllib.parse


def _zeit(ts):
    if not ts:
        return "never"
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
        '<h2>Vision detect <span id="vision-dirty-oben" class="vs-dirty-top" '
        'hidden>not saved</span></h2>' 
        '<p class="sub">A third recognition path next to face and body: a vision '
        "language model looks at one picture from a walk-through and says which "
        "of your learned people it shows &mdash; by comparing it against a small "
        "gallery of that person. It is an <b>extra voice</b>, never the "
        "doorkeeper: the forced choice answers &bdquo;A or B&ldquo;, so it can "
        "confirm a resident but it cannot turn a stranger away. That stays the "
        "job of the existing recognition.</p>")


def _hinweis():
    """Hinweisfeld: welches Modell, dass es auf einem EIGENEN Rechner im Netz
    laufen kann, und der ausdrueckliche Satz zur Host-Groesse (§4)."""
    return (
        '<div class="card"><b>What you need for this</b>'
        "<div>A vision model that can look at several pictures at once. You can "
        "use one of the online providers below, or run one yourself &mdash; the "
        "combination measured here is <b>llama.cpp</b> with a <b>Qwen3.5</b> "
        "vision model (the 4B is as good as the 9B on this task and needs about "
        "half the memory). It does <b>not</b> have to run on this machine.</div>"
        '<div class="dim" style="margin-top:6px"><b>This host is usually too '
        "small for a local model.</b> The 9B needs roughly 12 GB of working set, "
        "the 4B about 6.6 GB, and suslik plus the analysis worker already live "
        "here &mdash; the worker is the first thing the kernel kills when memory "
        "runs out. A second machine, or an online provider, is the sane setup."
        "</div>"
        '<div class="dim">A warning about measuring that memory: '
        "<code>docker stats</code> shows about 2.7 GiB for the model container "
        "because the weights are mapped, not copied. The real working set is "
        "~11.6 GiB. If you size <code>--memory</code> by what "
        "<code>docker stats</code> says, the model reloads its weights "
        "continuously and everything crawls.</div>"
        '<div class="dim">Speed and cost, measured, so nothing surprises you '
        "later: the whole walk-through goes in as <b>one candidate grid</b>, "
        "and each <b>compared pair of galleries is two requests</b> (the same "
        "question is asked again with the two galleries swapped, to catch a "
        "position bias). Usually one pair settles it. On a CPU-class machine "
        "that is about 7 minutes per pair; on the online endpoints measured "
        "here, seconds.</div></div>")


def _schalter(vor, aktiv, vcfg):
    """Schalter nach dem bestehenden armed-Muster; gesperrt, solange eine der
    drei Vorbedingungen fehlt (E4) — mit Klartext, was fehlt."""
    if vor.get("erfuellt"):
        knopf = (f'<button class="gtb{" on" if aktiv else ""}" '
                 f'onclick="visionSchalter({str(not aktiv).lower()})">'
                 f'{"Turn off" if aktiv else "Turn on"}</button>')
        rest = ""
    else:
        knopf = '<button class="gtb" disabled>Turn on</button>'
        rest = ('<div class="dim" style="margin-top:6px">Still missing:<ul>'
                + "".join(f"<li>{html.escape(f)}</li>" for f in vor["fehlt"])
                + "</ul></div>")
    zustand = "on" if aktiv else "off"
    return ('<div class="card"><b>Vision detect is ' + zustand + "</b> "
            + knopf + rest
            + '<div class="dim" style="margin-top:6px">While it is off nothing '
            "is sent anywhere and no image leaves this machine.</div>"
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
    return ('<div class="card"><b>How a comparison is asked</b>'
            + _kasten("vision_doppellauf",
                      "Ask each pair twice, with the galleries swapped",
                      "This is the position check. A in the first run and B in "
                      "the swapped run mean the SAME gallery, so a "
                      "contradiction exposes a model that simply prefers "
                      "whatever comes first. Measured here: every wrong answer "
                      "across all our test series was an &bdquo;A&ldquo;, "
                      "never a &bdquo;B&ldquo;. Turning it off halves the "
                      "requests &mdash; and a comparison then rests on a "
                      "single answer, with nothing to check it against.")
            + "</div>"
            '<div class="card"><b>Extra messages</b>'
            '<div class="dim">Both are off unless you turn them on, and '
            "neither changes the existing alarms: vision cannot raise one, "
            "cancel one, or overrule the face and body paths.</div>"
            + _kasten("vision_meldung", "Tell me when a walk-through has been "
                      "judged",
                      "A short note through your usual channels once the "
                      "verdict is in &mdash; with the real vote count. It "
                      "arrives after the pass is over, on a local model that "
                      "can be minutes later. Information, not an alarm.")
            + _kasten("vision_alarm_unbestaetigt", "Alert me when vision "
                      "contradicts the body recognition",
                      "Fires only when a run really happened, the model "
                      "answered, and it still confirmed nobody. It stays quiet "
                      "when there was simply not enough material &mdash; that "
                      "would be noise. Recognising people you taught it is the "
                      "strong side of this path, so a non-confirmation means "
                      "something; turning strangers away is the weak side, so "
                      "vision never votes in that direction.")
            + "</div>")


def _kacheln(kacheln, reihe, gewaehlt):
    """Die Anbieter-Reihe. Jede Kachel sagt, was sie von dir braucht — und die
    Anthropic-Kachel traegt ihren Klartext-Hinweis direkt daran (E7)."""
    was = {"key": "you enter an API key", "host_port": "you enter host and port",
           "url_key": "you enter a URL and an optional key"}
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
    return ('<div class="card"><b>Where the model runs</b>'
            '<p class="dim">Pick a provider. For the three named ones the '
            "official API address is already built in &mdash; you only enter "
            "your key. Nothing is sent anywhere until you press a button "
            "yourself.</p>"
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
    knopf = f"Check the {pruef_wort}"
    key_ph = ("&bull;&bull;&bull;&bull; stored &mdash; leave blank to keep it"
              if vcfg.get("api_key_gesetzt") else
              "paste your key here" if pflicht else
              "only if your server asks for one")
    # Die gewaehlte Kachel faehrt als verstecktes Feld mit: jeder Knopf auf
    # dieser Seite schickt EIN Formular, und die Kachel entscheidet, welche
    # Felder ueberhaupt gelten.
    felder = [f'<input type="hidden" id="vis-kachel" '
              f'value="{html.escape(kname, quote=True)}">']
    if k["eingabe"] == "host_port":
        felder.append(
            '<div class="vs-feld"><label>Host</label>'
            f'<input id="vis-host" size="26" value="{html.escape(vcfg.get("host") or "")}" '
            'placeholder="the name or address of that machine">'
            '<label style="min-width:auto">Port</label>'
            f'<input id="vis-port" size="6" value="{html.escape(str(vcfg.get("port") or ""))}" '
            'placeholder="8080"></div>'
            '<div class="dim">Just the machine &mdash; suslik adds the rest of '
            "the address itself. The example port is the one llama.cpp uses by "
            "default; use whatever yours listens on.</div>")
    elif k["eingabe"] == "url_key":
        # Vorbefuellt mit dem Beispiel-Endpunkt aus dem Kachel-Vertrag (EIN
        # Eintrag, kein Literal im Renderer) — ein GESPEICHERTER Wert gewinnt
        # immer.
        felder.append(
            '<div class="vs-feld"><label>Endpoint URL</label>'
            f'<input id="vis-endpunkt" size="46" '
            f'value="{html.escape(endpunkt_anzeige or k.get("beispiel_url") or "")}" '
            'placeholder="https://your-service.example/v1"></div>'
            + ("" if endpunkt_anzeige else
               '<div class="dim">That is an example of an OpenAI-compatible '
               "endpoint &mdash; replace it with yours if you use another "
               "provider.</div>")
            # .167: der Satz nennt die beiden Traeger, ohne das woertliche
            # Zugangsdaten-Muster auszuschreiben — das Datenschutz-Gate
            # (Stufe 10) sucht nach genau diesem Muster im Image, und es soll
            # weiter danach suchen duerfen. Die Aussage bleibt unveraendert.
            + '<div class="dim"><b>Put the key in the key field, not in the '
            "URL</b>: an endpoint that carries credentials in its address "
            "&mdash; in front of the host name, or as a query parameter "
            "&mdash; holds the same secret, and it shows up in far more "
            "places (status, log, backup).</div>"
            '<div class="vs-feld"><label>This endpoint is</label>'
            f'<select id="vis-betriebsart">'
            f'<option value="extern"{" selected" if vcfg.get("betriebsart") != "lokal" else ""}>'
            "on the internet</option>"
            f'<option value="lokal"{" selected" if vcfg.get("betriebsart") == "lokal" else ""}>'
            "in my own network</option></select></div>")
    else:
        felder.append(
            '<div class="vs-feld"><label>API address</label>'
            f'<code class="vs-url">{html.escape(k["basis"])}</code></div>'
            '<div class="dim">Built in &mdash; there is nothing to type wrong '
            "here.</div>")
    # Das Key-Feld steht bei JEDER Kachel — auch ein eigener Server kann einen
    # verlangen. Der Knopf daneben ist die Sofort-Pruefung: er holt die
    # Modell-Liste und ist damit zugleich der einzige Weg zur Modellwahl.
    felder.append(
        '<div class="vs-feld"><label>API key</label>'
        f'<input id="vis-api_key" size="46" value="" autocomplete="off" '
        f'placeholder="{key_ph}">'
        f'<button class="gtb on" onclick="visionSchluessel(this)">{knopf}'
        "</button>"
        '<span id="vision-key-status" class="dim"></span></div>'
        + ("" if pflicht else
           '<div class="dim">Optional here &mdash; most local servers do not '
           "ask for one. Press the button anyway: it also fetches the list of "
           "models your server has.</div>"))
    return ('<div class="card"><b>Connection</b>' + "".join(felder)
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
        vor = ("Enter your key above and press" if pruef_wort == "key" else
               "Fill in the fields above and press")
        return ('<div class="card"><b>Model</b>'
                '<div id="vision-modell-info" class="dim">Nothing to choose '
                f"yet. {vor} <b>Check the {html.escape(pruef_wort)}</b>: "
                "suslik connects to the endpoint, asks what is there, and "
                "shows you what it found. You pick from that list.</div>"
                + _klassen(klassen)
                + '<div id="vision-modell-wahl"></div>'
                '<span id="vision-modell-status" class="dim"></span></div>')
    if not prot.get("ok"):
        return ('<div class="card"><b>Model</b>'
                '<div id="vision-modell-info">'
                + _ampel_punkt("rot", prot.get("text")
                               or "the endpoint refused the connection")
                + f'</div><div class="dim">Checked {_zeit(prot.get("ts"))} '
                f'against <code class="vs-url">'
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
        opt.append('<option value="" selected>&mdash; pick one &mdash;</option>')
    for m in prot.get("modelle") or []:
        b = m.get("badge") or {}
        ist = m["id"] == gewaehlt
        gefunden = gefunden or ist
        anmerkung = b["text"] if b.get("gemessen") else "untested here"
        opt.append(f'<option value="{html.escape(m["id"], quote=True)}"'
                   + (" selected" if ist else "") + ">"
                   + html.escape(f'{m["id"]} — {anmerkung}') + "</option>")
    if gewaehlt and not gefunden:
        # Stiller Verlust waere die Alternative: die gespeicherte Wahl einfach
        # nicht mehr anzeigen. Sie bleibt sichtbar und sagt, was mit ihr ist.
        opt.insert(0, f'<option value="{html.escape(gewaehlt, quote=True)}" '
                   "selected>" + html.escape(gewaehlt)
                   + " — saved earlier, the endpoint does not list it now"
                   "</option>")
    unten = ('<div class="vs-detail dim">Pick one from the list &mdash; the '
             "note next to each name is ours, the names are the "
             "endpoint&rsquo;s.</div>")
    gb = next((m.get("badge") or {} for m in prot.get("modelle") or []
               if m["id"] == gewaehlt), None)
    if gewaehlt and gb is None:
        unten = ('<div class="vs-detail" style="color:var(--warn)">This model '
                 "is saved and still in use, but the endpoint did not list it "
                 "this time. Check the name, or pick one from the list.</div>")
    elif gb is not None and gb.get("gemessen"):
        extra = []
        if not gb.get("exakt"):
            extra.append("measured on another platform")
        if not gb.get("roh_archiviert"):
            extra.append("no raw result archived for this one")
        if gb.get("unvollstaendig"):
            extra.append(gb["unvollstaendig"])
        if gb.get("notiz"):
            extra.append(gb["notiz"])
        farbe = "var(--ok)" if gb.get("abweisen") == "✓" else "var(--warn)"
        unten = (f'<div class="vs-detail"><span style="color:{farbe}">'
                 f'{html.escape(gb["text"])}</span>'
                 f'<div class="vs-quelle">measured '
                 f'{html.escape(gb.get("datum") or "")} &middot; '
                 f'{html.escape(gb.get("quelle") or "")}'
                 + "".join(f"<br>{html.escape(x)}" for x in extra)
                 + "</div></div>")
    elif gb is not None:
        unten = ('<div class="vs-detail dim">Not measured here &mdash; that is '
                 "not a verdict, just honesty. Run the connection test below "
                 "before you rely on it.</div>")
    return ('<div class="card"><b>Model</b>'
            '<div id="vision-modell-info">'
            + _ampel_punkt("gruen", prot.get("text") or "")
            + f'</div><div class="dim">This is what the endpoint answered when '
            f'suslik asked it, {_zeit(prot.get("ts"))} &mdash; nothing here is '
            "a suggestion from us. Where we have measured a model, the note "
            "sits on that model. Two abilities are shown separately, because "
            "they fall apart: "
            "<b>residents</b> is picking the right one of two known people, "
            "<b>strangers</b> is answering &bdquo;neither&ldquo; for somebody "
            "you never taught it. A tick means every judgement of that kind in "
            "our measurement was right; the fraction next to it is the whole "
            "story. Models without a measurement here say <b>untested "
            f'here</b> &mdash; that is not a verdict, just honesty (measurements '
            f'from {html.escape(stand or "")}).</div>'
            + '<div id="vision-modell-wahl">'
            + '<select id="vision-modell" class="vs-sel" '
            'onchange="visionModell(this)">'
            + "".join(opt) + "</select></div>" + unten
            + _klassen(klassen)
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
    stand = ('<div class="dim">This is your own wording &mdash; verdicts made '
             "with it are marked <b>custom prompt</b>. Reset it to go back to "
             "the measured default.</div>" if eigen else
             '<div class="dim">This is the measured default wording. As long '
             "as you leave it exactly like this, verdicts are not marked as "
             "custom.</div>")
    return ('<div class="card"><b>The question suslik asks</b>'
            '<div class="dim">You can change the wording. The last paragraph is '
            "fixed: it is the one-word instruction the answer parser depends "
            "on, and it is what was measured.</div>" + stand
            + f'<textarea id="vis-prompt" rows="6" style="width:100%">'
            f"{html.escape(prompt)}</textarea>"
            '<div class="dim" style="white-space:pre-wrap;opacity:.75;'
            'border-left:3px solid var(--dim);padding-left:8px;margin-top:4px">'
            f"{html.escape(anker)}</div>"
            '<button class="gtb" onclick="visionPromptZurueck()">Reset to '
            "default</button>"
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
        denk = ('<div class="vs-feld"><label><input type="checkbox" '
                f'id="vis-think_aus"{" checked" if vcfg.get("think_aus") else ""}> '
                "Turn the model&rsquo;s thinking off</label></div>"
                '<div class="dim">Measured on a local setup: 2.7&times; faster '
                "with the same answers. On one online endpoint it was "
                "<b>worse</b> with thinking off. Strict endpoints reject the "
                "switch; suslik then repeats the request once without it and "
                "says so.</div>")
    return ('<div class="card"><b>Limits</b>'
            '<div class="vs-feld"><label>Max tokens per answer</label>'
            f'<input id="cfgv-vision_max_tokens" size="8" '
            f'value="{html.escape(str(vcfg.get("max_tokens") or ""))}">'
            "<label>Timeout per request (s)</label>"
            f'<input id="cfgv-vision_timeout_s" size="8" '
            f'value="{html.escape(str(vcfg.get("timeout_s") or ""))}"></div>'
            '<div class="dim">3000 tokens was measured to be not enough on one '
            "run &mdash; the answer was cut off and counted as no verdict, and "
            "the same question was right with 12000. A local model on a CPU "
            "machine needs minutes per request, an online one seconds.</div>"
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
            or "the endpoint you configure above")
    return ('<div class="card" style="border-left-color:var(--warn)">'
            "<b>Sending pictures to an outside service</b>"
            '<div class="dim">This sends pictures of people from your cameras '
            f'to <b class="vs-url">{html.escape(ziel)}</b>. '
            "Those pictures are not only of the people who live here: the "
            "uncertain cases are mostly strangers &mdash; visitors, delivery "
            "drivers, neighbours, passers-by. You are the one responsible for "
            "that, not the operator of the service. Your confirmation is "
            "written to the audit log with a timestamp; switching back to a "
            "local model withdraws it.</div>"
            '<label style="display:block;margin-top:6px"><input type="checkbox" '
            f'id="vis-cloud_ok"{" checked" if vcfg.get("cloud_ok") else ""}> '
            "I understand and confirm this"
            + (f' <span class="dim">(confirmed {_zeit(vcfg.get("cloud_ok_ts"))})</span>'
               if vcfg.get("cloud_ok") else "") + "</label></div>")


def _stufen_zeilen(stufen):
    """Das Testlog: je Stufe eine Zeile mit Ampel, Namen und den GEMESSENEN
    Werten. Keine Prosa-Glaettung — was gemessen wurde, steht da (Antwortzeit,
    n richtig von gesamt, Token gegen die Referenz)."""
    zeilen = []
    for s in stufen or []:
        werte = []
        if s.get("dauer_s") is not None:
            werte.append(f'{s["dauer_s"]} s')
        if s.get("treffer") is not None:
            werte.append(f'{s["treffer"]}/2 right')
        if s.get("ist") is not None:
            werte.append(f'{s["ist"]} tokens vs {s.get("soll")}')
            if s.get("anteil") is not None:
                werte.append(f'{int(round(float(s["anteil"]) * 100))}%')
        for l in s.get("laeufe") or []:
            werte.append(f'{l.get("arm")}: {l.get("wahl") or l.get("grund")}'
                         f'{"" if l.get("wahl") == l.get("soll") else " (wrong)"}')
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
    return ('<div class="vs-savebar" id="vision-savebar">'
            '<button class="gtb on vs-savebtn" onclick="visionSpeichern()">'
            "Save connection</button>"
            '<span id="vision-dirty" class="vs-dirty" hidden>unsaved changes '
            "&mdash; recognition still uses the saved connection</span>"
            '<span id="vision-status" class="vs-status"></span></div>')


def _test(prot):
    """Test-Knopf + Testlog als AMPEL-REIHE (§5, dreistufig).

    Die drei Stufen laufen seit V4 EINZELN (der Browser ruft sie nacheinander):
    lokal dauert eine Stufe Minuten, und ein Knopf, der minutenlang schweigt,
    sieht aus wie ein Haenger. Waehrend des Laufs schreibt der Browser in
    dieselben Log-Zeilen, die der Server danach rendert — es gibt nur EIN
    Log-Format, und es ueberlebt den Reload."""
    kopf = (
        '<div class="card"><b>Test this connection</b>'
        '<p class="dim">Three steps, because a plain reachability ping is not '
        "enough: one backend was reachable, had the model and answered quickly "
        "&mdash; and still got 5 of 12 comparison questions wrong, because it "
        "shrank the pictures before looking at them.<br>"
        "<b>1</b> reachability, model and response time, using a test image "
        "generated on the spot.<br>"
        "<b>2</b> a forced-choice run on generated shape grids where the right "
        "answer is known &mdash; this checks the answer format, the parser and "
        "the thinking switch.<br>"
        "<b>3</b> a token count against a measured reference, which is how "
        "image shrinking shows up.<br>"
        "<b>No picture of a person is used for this</b>, and there is no option "
        "to do so.</p>"
        '<button class="gtb on" onclick="visionTest(this)">Run the test</button> '
        '<span id="vision-test-status" class="dim"></span>')
    if not prot:
        # Die drei Zeilen stehen auch UNGETESTET schon da (als "not run") —
        # dann hat der Live-Fortschritt einen Platz zum Schreiben, und der
        # Leerzustand sagt trotzdem klar, dass noch nichts gelaufen ist.
        leer = [{"nr": nr, "name": name, "ampel": "grau", "text": "not run"}
                for nr, name in ((1, "reachability"), (2, "forced choice"),
                                 (3, "token audit"))]
        return (kopf + '<div class="dim" style="margin-top:8px">Not tested '
                "yet.</div>"
                f'<div class="vs-stufen">{_stufen_zeilen(leer)}</div></div>')
    return (kopf + f'<div style="margin-top:8px">Last run '
            f'{_zeit(prot.get("ts"))} against '
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
            kl, stand = "fertig", (
                f'approved {_zeit(g.get("abnahme_ts"))} &middot; '
                f'{g.get("groesse")} cells')
        elif g:
            kl, stand = "offen", html.escape(pruef.get("text") or "needs a look")
        elif d["max_groesse"]:
            kl, stand = "offen", "no gallery yet"
        else:
            kl, stand = "offen", ("not enough approved body images yet "
                                  f"({d['gesamt']} usable)")
        reihen = " &middot; ".join(
            f"{html.escape(rt.get(r, r))} {d['je_reihe'].get(r, 0)}"
            for r in ("vorn", "seitlich", "hinten"))
        knopf = ""
        if d["max_groesse"]:
            knopf = ('<div style="margin-top:6px"><a class="gtb" href="/vision/galerie?person='
                     + urllib.parse.quote(d["person"]) + '">'
                     + ("Refresh it" if g else "Build a gallery") + "</a></div>")
        karten.append(
            f'<div class="vs-d {kl}"><b>{html.escape(d["person"])}</b>'
            f"<div>{stand}</div>"
            f'<div class="vs-zahl">{d["gesamt"]} usable images &middot; '
            f"{reihen}</div>{knopf}</div>")
    return ('<div class="card"><b>Galleries</b>'
            f'<div>{n_fertig} galleries ready '
            f'({vor.get("galerien_min", 2)} required) '
            "&mdash; vision needs at least two, because it always compares one "
            "person against another.</div>"
            '<div class="dim">Only people with a learned body model can get a '
            "gallery; the images come from the body material you already "
            "approved. Vision only ever judges people who have one, and it "
            "says so on the verdict.</div>"
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
