# core/vision.py — Vision-Detect Zug V1: Adapter-Vertrag, Antwort-Auswertung,
# erzeugtes Testbild + synthetische Formprobe (konzept_vision.md v2 §5/§9/§13).
#
# Kontrakt wie core/registry.py (dort steht die Secret-/URL-Quelle): KEIN Import
# des Dienstes, KEIN Dienst-Zustand, reine Funktionen. verifyd.py haelt nur die
# duennen Routen; die Logik liegt hier, damit sie ohne laufenden Dienst pruefbar
# ist (beweis_v1) und der I1-Deckel nicht waechst.
#
# LEITPLANKE §11: dieses Modul liest NIE ein Video und startet NIE einen Decode —
# es importiert die Frame-Quelle und den Verteiler nicht einmal. Der bestehende
# Urteilspfad (analyze/worker/personlive/abnahme) importiert im Gegenzug NICHTS
# von hier; seit V4 haengt der VISION-Urteilspfad dran, aber nur in EINE
# Richtung: core/visionurteil.py benutzt diesen Adapter und liest ausschliesslich
# schon gespeicherte Bilder, und alles, was danach kommt (Kaskade, Karte,
# Protokoll), liest NUR das normierte Urteils-Objekt, nie den Antwort-Text.
#
# WAS HIER GEMESSEN IST UND WAS NICHT (§2.3/§2.5): seit V2 haengen Messwerte am
# MODELL, nicht an der Verbindung — sie stehen zentral in
# core/registry.VISION_MESSWERTE und erscheinen als Doppel-Angabe
# (erkennen/abweisen) an der Modell-Auswahl. Was dort nicht steht, heisst
# "untested here": keine Zahl, keine Empfehlung. Die fuenf Kacheln unten
# behaupten NICHTS ueber Qualitaet, sie beschreiben nur den Weg dorthin.
import base64
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from core import registry as _reg

# ------------------------------------------------------------------ Prompt
# GEMESSENER Wortlaut. Quelle byte-genau: scratchpad/ionos_vision_test.py FRAGE
# (identisch in den lokalen Messskripten, die ihn dort importieren). beweis_v1 prueft die Byte-Gleichheit
# gegen die Messskripte; wer den Text hier aendert, entwertet die Messungen.
#
# Zerlegt in KOPF (editierbar) + ANKER (nicht editierbar, §5, User-Entscheid 08.08.):
# der Anker ist die Ein-Wort-Zwangsansage, an der `beginnt_mit_wort` haengt.
MASCHINEN_ANKER = (
    "Answer FIRST with exactly one word: A or B or NEITHER. After that word, "
    "at most one short sentence. "
    "IMPORTANT: answer IMMEDIATELY and start with that single word. No "
    "thinking steps, no analysis, no preamble."
)

# E12 (User-Entscheid 08.08., folgt Empfehlung): der Consent-Satz des Messprompts ist im
# Produkt eine Behauptung im Namen eines fremden Nutzers. Er wird deshalb an die
# protokollierte Cloud-Bestaetigung (§9) GEBUNDEN: ohne Bestaetigung faellt die
# Klammer-Haelfte weg. Mit Bestaetigung steht wieder exakt der gemessene Satz da.
# SIEGER-SATZ des Prompt-Sweeps (08.08., scratchpad/ionos_prompt_sweep.py,
# Variante V2_symmetrisch): die KEINER-Normalisierung hob die Fremd-Abweisung
# des gemessenen 9B von 25 % auf 44 % bei unveraenderter Bekannten-Erkennung.
# Sie ersetzt seit V4 den frueheren Satz "Answer NEITHER only if the candidate
# clearly contradicts BOTH sets" als Default — die 44 % sind Modell-Decke (drei
# Umformulierungen konvergieren dort), der Tuersteher bleibt davon unberuehrt.
_KOPF_RUMPF = (
    " Forced choice: does the candidate "
    "show the person of reference set A, the person of reference set B, or "
    "NEITHER of them? Judge stable features (build, hair, posture, height, "
    "head shape). Different clothing and day-to-day variation are NORMAL and "
    "are NOT evidence against a match. If the candidate does not clearly match "
    "either person, answer NEITHER — it is a normal and expected answer."
)
PROMPT_KOPF_MIT_CONSENT = (
    "Recognition check for a private home security system (the operator's own "
    "cameras, with the operator's consent)." + _KOPF_RUMPF)
PROMPT_KOPF_OHNE_CONSENT = (
    "Recognition check for a private home security system (the operator's own "
    "cameras)." + _KOPF_RUMPF)


def prompt_default(cloud_bestaetigt=False):
    """Der editierbare Prompt-KOPF (ohne Anker) im Auslieferungszustand.
    cloud_bestaetigt=True nur, wenn die Cloud-Bestaetigung protokolliert ist —
    dann darf der gemessene Consent-Satz mitfahren (E12)."""
    return PROMPT_KOPF_MIT_CONSENT if cloud_bestaetigt else PROMPT_KOPF_OHNE_CONSENT


def prompt_voll(kopf, cloud_bestaetigt=False):
    """Kopf + Maschinen-Anker. Der Anker ist der nicht-editierbare Schlussteil:
    ein angepasster Prompt darf ihn NICHT entfernen (§5). Steht er schon (ganz
    oder teilweise) im Kopf, wird der Rest abgeschnitten und genau einmal
    angehaengt — kein Doppel-Anker, kein fehlender Anker."""
    k = str(kopf or "").strip()
    if not k:
        k = prompt_default(cloud_bestaetigt)
    # Anker (auch angefangen) hinten abschneiden: der erste Satz des Ankers ist
    # eindeutig genug und taucht im gemessenen Kopf nirgends auf.
    marke = "Answer FIRST with exactly one word"
    i = k.find(marke)
    if i >= 0:
        k = k[:i].rstrip()
    return (k + " " + MASCHINEN_ANKER) if k else MASCHINEN_ANKER


def prompt_ist_angepasst(kopf, cloud_bestaetigt=False):
    """True, wenn der Kopf vom Default abweicht -> Urteile werden im Status als
    'custom prompt' markiert (§5, Vertragsfeld custom_prompt). Beide
    Default-Fassungen zaehlen als Default (mit/ohne Consent-Satz, E12): sonst
    kippte dieselbe Formulierung allein durch die Cloud-Bestaetigung auf
    'custom'."""
    return str(kopf or "").strip() not in ("", prompt_default(False),
                                           prompt_default(True))


# Galerie-/Kandidaten-Labels, byte-genau aus ionos_sym_reihe.py (§2.1: B ist
# WOERTLICH eine andere Person — E10 haelt daran fest, FREMD-Gitter gibt es nicht).
def label_a(n):
    return (f"Reference set A: {n} images of ONE person, taken on different days "
            "(clothing varies between images).")


def label_b(n):
    return (f"Reference set B: a DIFFERENT person, {n} images, also different "
            "days.")


LABEL_K = "Candidate:"


def label_k(n=0):
    """Das Kandidaten-Label. Seit V4c ist der Kandidat EIN GITTER aus mehreren
    Bildern DESSELBEN Durchgangs (§7, Entscheid 08.08. spaetabend) — das Label
    muss deshalb woertlich sagen, was das Bild zeigt, sonst haelt das Modell die
    Zellen fuer verschiedene Personen. Unter zwei Zellen bleibt es beim
    gemessenen Einzelbild-Label (dann IST es ein Bild).

    Die Zahl kommt aus den WIRKLICH gefuellten Zellen, nie aus der Gitter-Groesse
    — eine falsche Zahl waere eine Behauptung ueber das Bild."""
    if int(n or 0) < 2:
        return LABEL_K
    return (f"Candidate: {int(n)} images of the SAME person, taken during ONE "
            "walk across the property (several cameras, minutes apart).")


# Wie viele Bilder EINE Urteils-Anfrage traegt: Galerie A + Galerie B +
# Kandidaten-Gitter. Steht hier als EINE Quelle, weil die Kachel-Vertraege
# (max_bilder_je_request) genau dagegen geprueft werden — Gate-Stufe PYVGIT.
BILDER_JE_ANFRAGE = 3

# ------------------------------------------------------------------ Kacheln
# FUENF KACHELN statt der V1-Preset-Tabelle (§5, User-Entscheid 08.08. abend,
# fix-forward): Gemini · GPT · Anthropic · Lokal · Custom. Der Unterschied ist
# nicht kosmetisch — die Preset-Tabelle liess den Nutzer eine URL tippen und
# behauptete Messwerte AN DER VERBINDUNG. Jetzt gilt:
#
#   * bei den drei Namens-Anbietern steht die offizielle API-URL FEST im Code
#     (oeffentlicher Endpunkt, kein privater Wert, kein Tippfehler-Risiko); der
#     Nutzer gibt NUR den Key ein,
#   * Lokal = IP + Port des eigenen Servers, Custom = beliebige OpenAI-kompatible
#     URL + optionaler Key (Dienste wie ein externer Model-Hub laufen hierueber,
#     ohne dass ein Anbietername im Code oder im UI steht),
#   * Messwerte haengen NICHT mehr an der Kachel, sondern am MODELL — sie kommen
#     aus core/registry.VISION_MESSWERTE und werden an der Modell-Auswahl
#     angezeigt (Doppel-Angabe erkennen/abweisen). Eine Kachel behauptet nichts.
#
# Faehigkeits-Flags je Kachel statt blind mitgeschickter Knoepfe (§5):
#   kann_think_schalter · reasoning_feld · think_tags · refusal_feld ·
#   max_bilder_je_request · leinwand · max_tokens · token_feld · temperature
#
# Alle Zahlen unten sind GEMESSEN (die Skripte hinter der Messwerte-Registry):
# `token_feld` und `temperature` sind keine Geschmacksfrage — die GPT-5er-Klasse
# nimmt `max_completion_tokens` und weist Sampling-Parameter zurueck, Anthropic
# ebenso; die Leinwand 1176x1008 ist die der vermessenen Gitter.
#
# E3/F12: hier steht KEINE private Adresse. Die Lokal-Kachel hat deshalb auch
# keinen Beispiel-Host, sondern zwei getrennte Felder (Host + Port) mit
# Platzhaltern — Nutzer kopieren woertlich (Support-Lehre).

# E7 FORTGESCHRIEBEN (User-Entscheid 08.08. abend: Kachel KOMMT; Fortschreibung
# 08.08. spaetabend: "der text kann weg"): die Anthropic-Kachel steht ohne jeden
# Nutzungsbedingungs-Text da — weder an der Kachel noch im Verbindungs-Block.
# Was BLEIBT, ist Verhalten statt Text: eine Verweigerung wertet der Adapter als
# "kein Votum" (Grund "refusal"), nie als Negativ-Beweis (antwort_auswerten).
KACHELN = {
    "gemini": {
        "label": "Gemini",
        "anbieter": "Google",
        "api": "gemini",
        "basis": "https://generativelanguage.googleapis.com/v1beta",
        "pfad": ":generateContent",       # Modellname steckt im Pfad
        "modelle_pfad": "/models",
        "eingabe": "key",
        "key_pflicht": True,
        "betriebsart": "extern",
        "hinweis": "",
        "max_tokens": 300,
        "token_feld": "maxOutputTokens",
        "temperature": 0.0,
        "leinwand": (1176, 1008),
        "kann_think_schalter": False,
        "reasoning_feld": None,
        "think_tags": False,
        "refusal_feld": None,
        "max_bilder_je_request": 3,
    },
    "gpt": {
        "label": "GPT",
        "anbieter": "OpenAI",
        "api": "openai",
        "basis": "https://api.openai.com/v1",
        "pfad": "/chat/completions",
        "modelle_pfad": "/models",
        "eingabe": "key",
        "key_pflicht": True,
        "betriebsart": "extern",
        "hinweis": "",
        "max_tokens": 2000,
        # GEMESSEN: die 5er-Klasse rechnet interne Reasoning-Token in dieses
        # Budget und kennt `max_tokens` nicht mehr; 300 waeren der
        # length-Abbruch, den wir anderswo schon einmal hatten.
        "token_feld": "max_completion_tokens",
        "temperature": None,
        "leinwand": (1176, 1008),
        "kann_think_schalter": False,
        "reasoning_feld": "reasoning_content",
        "think_tags": False,
        "refusal_feld": "refusal",
        "max_bilder_je_request": 3,
    },
    "anthropic": {
        "label": "Anthropic",
        "anbieter": "Anthropic",
        "api": "anthropic",
        "basis": "https://api.anthropic.com/v1",
        "pfad": "/messages",
        "modelle_pfad": "/models",
        "eingabe": "key",
        "key_pflicht": True,
        "betriebsart": "extern",
        "hinweis": "",
        "max_tokens": 300,
        "token_feld": "max_tokens",
        "temperature": None,
        "leinwand": (1176, 1008),
        "kann_think_schalter": False,
        "reasoning_feld": None,
        "think_tags": False,
        "refusal_feld": None,
        "max_bilder_je_request": 3,
    },
    "lokal": {
        "label": "Local model",
        "anbieter": "a machine in your own network",
        "api": "openai",
        "basis": "",                       # wird aus Host + Port gebaut
        "pfad": "/chat/completions",
        "modelle_pfad": "/models",
        "eingabe": "host_port",
        "key_pflicht": False,
        "betriebsart": "lokal",
        "hinweis": "",
        "max_tokens": 3000,
        "token_feld": "max_tokens",
        "temperature": 0.0,
        "leinwand": (1176, 1008),
        "kann_think_schalter": True,
        "reasoning_feld": "reasoning_content",
        "think_tags": True,
        "refusal_feld": None,
        "max_bilder_je_request": 3,
    },
    "custom": {
        "label": "Custom endpoint",
        "anbieter": "any OpenAI-compatible service",
        "api": "openai",
        "basis": "",                       # der Nutzer gibt die volle URL
        # VORBEFUELLT, aber frei ueberschreibbar (User-Entscheid 08.08.
        # spaetabend: "den Satz will ich nicht raussuchen muessen"). Das ist der
        # oeffentliche Endpunkt des Anbieters, gegen den unsere Messreihen
        # liefen — KEINE private Adresse, die F12-Regel bleibt unberuehrt (sie
        # verbietet private Hosts/IPs, nicht oeffentliche Anbieter-URLs). Die
        # Kachel heisst weiter "Custom": ein eigener Anbieter-Name im Code war
        # ausdruecklich nicht gewollt. Ein GESPEICHERTER Endpunkt gewinnt immer.
        "beispiel_url": "https://openai.inference.de-txl.ionos.com/v1",
        "pfad": "/chat/completions",
        "modelle_pfad": "/models",
        "eingabe": "url_key",
        "key_pflicht": False,
        "betriebsart": "extern",           # konservativ: Bestaetigung verlangen
        "hinweis": "",
        "max_tokens": 12000,
        # GEMESSEN: auf einem externen OpenAI-kompatiblen Dienst riss ein Lauf
        # bei 3000 Token ab (finish_reason=length, kein Votum), mit 12000 war
        # dieselbe Frage richtig.
        "token_feld": "max_tokens",
        "temperature": 0.0,
        "leinwand": (1176, 1008),
        "kann_think_schalter": True,
        "reasoning_feld": "reasoning_content",
        "think_tags": True,
        # GEMESSEN am oeffentlichen Endpunkt dieser Kachel (08.08.): mit VIER
        # Bildern je Anfrage (drei Galerien + Kandidat) kamen Antworten samt
        # Token-Zahlen zurueck (scratchpad/ionos_dreiwahl.json), mit FUENF
        # (vier Galerien + Kandidat) antwortete derselbe Endpunkt auf ALLE
        # sechs Anfragen mit HTTP 400 (scratchpad/ionos_vierwahl.json). Die
        # Grenze liegt damit gemessen bei 4 — nicht geraten, und genau deshalb
        # bleibt die Kaskade PAARWEISE: unser Urteil braucht drei Bilder
        # (BILDER_JE_ANFRAGE), eine Vier-Wahl braeuchte fuenf.
        "refusal_feld": None,
        "max_bilder_je_request": 4,
    },
}
# Reihenfolge der Kachel-Reihe im UI. Steht hier, nicht im Renderer: eine
# fachliche Aufzaehlung kommt aus EINER Quelle (qs_ebenen-Regel).
KACHEL_REIHE = ("gemini", "gpt", "anthropic", "lokal", "custom")
KACHEL_DEFAULT = "lokal"       # Produkt-Default bleibt lokal (§9, E3)

# Alt-Werte der V1-Preset-Tabelle -> Kachel. Eine Installation, die schon einen
# Vision-Block hat, verliert ihre Verbindung beim Update NICHT still; sie landet
# auf der Kachel, die denselben Weg fuehrt (der externe Model-Hub war nie ein
# eigener Anbieter im Code, er ist ein Custom-Endpunkt).
PRESET_ALT = {"llamacpp_qwen": "lokal", "ionos_qwen": "custom",
              "openai_kompatibel": "custom"}


def kachel(name):
    return KACHELN.get(str(name or "")) or KACHELN[KACHEL_DEFAULT]


def kachel_namen():
    return KACHEL_REIHE


def pruef_wort(k):
    """Was der Pruef-Knopf DIESER Kachel wirklich prueft (User-Fund 08.08. aus
    der Live-Nutzung): bei den drei Namens-Anbietern ist es der Schluessel, bei
    einem eigenen Server oder einem freien Endpunkt gibt es oft gar keinen — da
    heisst derselbe Knopf "Check the connection". Abgeleitet aus dem
    Kachel-Vertrag (`key_pflicht`), nie aus dem Kachel-NAMEN: sonst waere jede
    neue Kachel ein weiteres Streu-Literal im Renderer."""
    return "key" if (k or {}).get("key_pflicht") else "connection"


# ------------------------------------------------------------------ Body-Formen
def _bild_teil_openai(b64, mime="image/jpeg"):
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def _bild_teil_anthropic(b64, mime="image/jpeg"):
    return {"type": "image",
            "source": {"type": "base64", "media_type": mime, "data": b64}}


def _bild_teil_gemini(b64, mime="image/jpeg"):
    return {"inline_data": {"mime_type": mime, "data": b64}}


def body_openai(p, teile, *, modell, max_tokens, temperature=None, think_aus=False):
    """OpenAI-kompatibler Chat-Body (llama.cpp, vLLM, OpenAI selbst). Byte-gleich
    zu den Messskripten: model / Token-Feld / (temperature) / messages[0].content
    als Text-Bild-Wechselfolge.

    Zwei Stellen sind KEINE Geschmacksfrage, sondern gemessen: das Token-Feld
    heisst je nach Klasse `max_tokens` oder `max_completion_tokens` (die
    GPT-5er-Klasse kennt nur letzteres und rechnet Reasoning hinein), und
    `temperature` faehrt nur mit, wenn die Kachel sie hat — dieselbe Klasse
    weist Sampling-Parameter zurueck. Der think-Schalter ist eine
    llama.cpp/vLLM-ERWEITERUNG, kein OpenAI-Feld, und faehrt nur mit, wenn die
    Kachel ihn kann."""
    body = {"model": modell, p.get("token_feld", "max_tokens"): int(max_tokens)}
    if temperature is not None:
        body["temperature"] = float(temperature)
    if think_aus:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    body["messages"] = [{"role": "user", "content": _inhalt(p, teile, "openai")}]
    return body


def body_anthropic(p, teile, *, modell, max_tokens, temperature=None, think_aus=False):
    """Anthropic-Messages-Body, byte-gleich zum Messskript: content-Block
    {"type":"image","source":{"type":"base64","media_type":...}}, Header
    x-api-key + anthropic-version. `temperature` faehrt hier bewusst NICHT mit —
    die aktuellen Modelle weisen Sampling-Parameter zurueck; einen think-Schalter
    gibt es dort ebenfalls nicht (Faehigkeits-Flag = False)."""
    return {"model": modell, "max_tokens": int(max_tokens),
            "messages": [{"role": "user",
                          "content": _inhalt(p, teile, "anthropic")}]}


def body_gemini(p, teile, *, modell, max_tokens, temperature=None, think_aus=False):
    """Gemini-generateContent-Body, byte-gleich zum Messskript: contents[0].parts
    als Text-Bild-Wechselfolge, generationConfig mit temperature und
    maxOutputTokens. Der Modellname steckt bei dieser API im PFAD, nicht im
    Body — deshalb taucht `modell` hier nicht auf (url_bauen setzt ihn)."""
    cfg = {p.get("token_feld", "maxOutputTokens"): int(max_tokens)}
    if temperature is not None:
        cfg["temperature"] = float(temperature)
    return {"contents": [{"parts": _inhalt(p, teile, "gemini")}],
            "generationConfig": cfg}


BODY_FORMEN = {"openai": body_openai, "anthropic": body_anthropic,
               "gemini": body_gemini}


def _inhalt(p, teile, form):
    """teile = [("text", str) | ("bild", b64), ...] -> Content-Liste der Form."""
    if form == "gemini":
        return [{"text": w} if a == "text" else _bild_teil_gemini(w)
                for a, w in teile]
    bild = _bild_teil_openai if form == "openai" else _bild_teil_anthropic
    aus = []
    for art, wert in teile:
        aus.append({"type": "text", "text": wert} if art == "text" else bild(wert))
    return aus


def kopfzeilen(form, api_key):
    """Request-Header je Body-Form. NIE ins Log (Log-Vertrag §9).
    Gemini traegt den Key NICHT im Header, sondern als Query-Parameter — genau
    deshalb maskiert registry.endpunkt_anzeige auch `key=` (§9, zweiter
    Key-Traeger); die URL dieser Kachel darf nirgends roh erscheinen."""
    if form == "anthropic":
        h = {"content-type": "application/json",
             "anthropic-version": "2023-06-01"}
        if api_key:
            h["x-api-key"] = api_key
        return h
    if form == "gemini":
        return {"content-type": "application/json"}
    h = {"Content-Type": "application/json"}
    if api_key:
        h["Authorization"] = f"Bearer {api_key}"
    return h


def url_bauen(endpunkt, pfad, modell="", api_key="", form="openai"):
    """Endpunkt + Kachel-Pfad. Ein Endpunkt, der den Pfad schon traegt, wird
    nicht doppelt verlaengert (Nutzer kopieren die volle URL aus fremden Doku).
    Bei der Gemini-Form steckt der Modellname im Pfad und der Key in der Query —
    beides wird HIER gebaut, damit es genau eine Stelle gibt."""
    e = str(endpunkt or "").strip().rstrip("/")
    if not e:
        return ""
    if form == "gemini":
        u = f"{e}/models/{str(modell or '').strip()}{pfad}"
        return u + (f"?key={urllib.parse.quote(str(api_key))}" if api_key else "")
    p = str(pfad or "")
    return e if e.endswith(p) else e + p


def endpunkt_wirksam(vcfg):
    """Die URL, die wirklich gerufen wird — EINE Stelle. Bei den drei
    Namens-Kacheln ist sie FEST im Code hinterlegt (der Nutzer kann sie gar
    nicht falsch eintippen), bei Lokal wird sie aus Host + Port gebaut, bei
    Custom kommt sie aus dem Formular."""
    k = kachel(vcfg.get("kachel"))
    if k["eingabe"] == "key":
        return k["basis"]
    if k["eingabe"] == "host_port":
        host = str(vcfg.get("host") or "").strip().rstrip("/")
        port = str(vcfg.get("port") or "").strip()
        if not host:
            return ""
        if "://" not in host:
            host = "http://" + host
        return f"{host}:{port}/v1" if port else host + "/v1"
    return str(vcfg.get("endpunkt") or "").strip()


# ------------------------------------------------------------- Log-Vertrag §9
_KEY_MUSTER = (
    r"(?i)bearer\s+[A-Za-z0-9._\-]{6,}",
    r"(?i)x-api-key[\"'\s:=]+[A-Za-z0-9._\-]{6,}",
    r"sk-[A-Za-z0-9._\-]{8,}",
    r"(?i)\"?(api[_-]?key|access_token|token)\"?\s*[:=]\s*\"?[A-Za-z0-9._\-]{6,}",
)


def fehlertext_filtern(text, geheimnisse=(), n=120):
    """Fremder Antwortkoerper -> log-taugliche Kurzform. Manche Anbieter
    SPIEGELN den gesendeten Key in der Fehlermeldung, und unsere eigenen
    Messskripte protokollieren `HTTP {code}: {body[:200]}` genau so (§9).
    Deshalb: erst jedes bekannte Geheimnis ersetzen, dann Key-Muster, dann
    kuerzen. Niemals Header, niemals Request-Body, niemals roher Koerper."""
    t = str(text or "")
    for g in sorted({str(x) for x in (geheimnisse or ()) if str(x)}, key=len,
                    reverse=True):
        t = t.replace(g, "***")
    for m in _KEY_MUSTER:
        t = re.sub(m, "***", t)
    t = " ".join(t.split())
    return t[:n]


def fehler_kurz(code, rohtext, geheimnisse=(), n=120):
    """Statuscode plus gekuerzte, gefilterte Meldung — mehr geht nie ins Log."""
    kern = fehlertext_filtern(rohtext, geheimnisse, n)
    return f"HTTP {code}: {kern}" if kern else f"HTTP {code}"


# ---------------------------------------------------- Antwort -> Urteils-Objekt
_TOKEN = re.compile(r"^(NEITHER|NONE|A|B)\b")


def sichtbar_machen(text):
    """Sichtbarer Antwort-Text: abgeschlossene <think>-Bloecke raus, ein
    UNABGESCHLOSSENER Block schneidet den Rest ab (Muster der Messskripte,
    ionos_vision_test.parsen), danach Rand-Markup weg."""
    if not text:
        return ""
    s = re.sub(r"<think>.*?</think>", "", str(text), flags=re.S)
    if "<think>" in s:
        s = s.split("<think>")[0]
    return s.strip().strip("*# ").strip()


def urteil_leer(**felder):
    """Das normierte Urteils-Objekt — die EINZIGE Rueckgabe des Adapters.
    Kaskade, Status, Event-Karte und spaeter die Master-Waage lesen NUR dieses
    Objekt, nie den Antwort-Text (§5). Felder bewusst immer alle da, damit kein
    Leser ein fehlendes Feld als False missversteht."""
    o = {
        "wahl": None,             # "A" | "B" | "NEITHER" | None
        "person": None,           # aufgeloester Name (setzt die Kaskade in V4)
        "beginnt_mit_wort": False,  # Vertragsfeld aus den Messlaeufen
        "konsistent": None,       # aus dem Tausch-PAAR (V4), einzeln None
        "kein_votum": True,
        "grund": None,            # "format" | "length" | "refusal" | "fehler" | "leer"
        "arm": None,              # Galeriegroesse/Runde
        "galerie_stand": None,
        "dauer_s": None,
        "token": {"prompt": None, "completion": None, "total": None},
        "custom_prompt": False,
        "backend": "",
        "quelle": "",             # "local" | "cloud: <host>" (schon maskiert)
        "retry_ohne_zusatzfeld": False,
        "sichtbar": "",
    }
    o.update(felder)
    return o


def antwort_auswerten(roh, *, kachel_name="", arm=None, galerie_stand=None,
                      dauer_s=None, custom_prompt=False, backend="",
                      quelle="", retry_ohne_zusatzfeld=False):
    """Rohe Provider-Antwort -> normiertes Urteils-Objekt.

    Regeln, jede an einem Messbefund (§5):
      * finish_reason/stop_reason == length/max_tokens -> KEIN Votum, Grund
        "length". Das ist kein falsches Urteil, sondern ein technischer Abbruch
        (gemessen: ionos_vision_test D3/lindi_1 lieferte bei 3000 Token einen
        LEEREN Text, im Nachlauf mit 12000 war dasselbe Paar korrekt).
      * Verweigerung (stop_reason "refusal" oder gefuelltes refusal-Feld) ->
        KEIN Votum, Grund "refusal". Nie ein Negativ-Beweis.
      * Anker STRIKT: gewertet wird der ANTWORT-ANFANG. Steht das Wort nicht
        vorn, ist das ein Formfehler und kein Votum — `beginnt_mit_wort` ist
        Vertragsfeld, nicht Verzierung.
    """
    p = kachel(kachel_name)
    o = urteil_leer(arm=arm, galerie_stand=galerie_stand, dauer_s=dauer_s,
                    custom_prompt=bool(custom_prompt), backend=backend or p["label"],
                    quelle=quelle, retry_ohne_zusatzfeld=bool(retry_ohne_zusatzfeld))
    roh = roh or {}
    u = roh.get("usage") or {}
    # Drei Namensschulen fuer dieselbe Zahl (OpenAI/Anthropic/Gemini) — hier
    # zusammengefuehrt, damit das Urteils-Objekt EIN Token-Feld hat.
    o["token"] = {"prompt": u.get("prompt_tokens", u.get(
                      "input_tokens", u.get("promptTokenCount"))),
                  "completion": u.get("completion_tokens", u.get(
                      "output_tokens", u.get("candidatesTokenCount"))),
                  "total": u.get("total_tokens", u.get("totalTokenCount"))}
    if roh.get("fehler"):
        o["grund"] = "fehler"
        return o
    stop = str(roh.get("finish_reason") or roh.get("stop_reason") or "").lower()
    if str(roh.get("refusal") or "").strip() or stop in ("refusal", "safety",
                                                         "prohibited_content"):
        o["grund"] = "refusal"
        return o
    if stop in ("length", "max_tokens"):
        o["grund"] = "length"
        return o
    text = roh.get("text")
    if not str(text or "").strip():
        # Leerer sichtbarer Text bei sauberem Stop: das reasoning_feld hat alles
        # aufgesogen (llama.cpp liefert content='A' + reasoning_content lang;
        # ist content leer, gibt es schlicht kein Votum).
        o["grund"] = "leer"
        return o
    s = sichtbar_machen(text)
    o["sichtbar"] = s[:400]
    m = _TOKEN.match(s.upper())
    if not m:
        o["grund"] = "format"
        return o
    o["beginnt_mit_wort"] = True
    o["wahl"] = "NEITHER" if m.group(1) in ("NEITHER", "NONE") else m.group(1)
    o["kein_votum"] = False
    o["grund"] = None
    return o


# Die Gruende des Urteils-Objekts sind INTERNE Marken (sie stehen im Protokoll
# und werden gezaehlt). Fuer die englische Oberflaeche gehoert genau EINE
# Uebersetzungstabelle daneben — sonst steht in der UI, was der Code denkt
# ("tausch_widerspruch"), und jeder Renderer erfindet seine eigene Fassung.
GRUND_TEXT = {
    "tausch_widerspruch": "the two runs disagreed when the galleries were "
                          "swapped",
    "neither": "the model said neither person",
    "length": "the answer was cut off — the token budget was too small",
    "format": "the answer did not start with the required single word",
    "refusal": "the model refused to answer",
    "fehler": "the request failed",
    "timeout": "the request ran past the deadline",
    "leer": "the model returned no visible answer",
    "deckel": "the request limit was reached",
    "zu_wenige_galerien": "fewer than two approved galleries",
}


def grund_text(g):
    """Interne Grund-Marke -> Klartext fuer die Oberflaeche. Unbekannte Marken
    kommen unveraendert zurueck (ehrlicher als ein glattes 'unknown')."""
    g = str(g or "")
    return GRUND_TEXT.get(g, g)


def paar_werten(u1, u2):
    """Tausch-Doppellauf -> EIN Urteil. Betrieblich zaehlt die Paar-Ausbeute
    (tausch-konsistent UND richtig), nicht die Anfrage-Quote (§2.5): A im
    untauschten Lauf und B im getauschten meinen DIESELBE Galerie. Widerspruch
    = kein Votum, nie ein Negativ-Beweis (§7)."""
    o = urteil_leer(arm=u1.get("arm"), galerie_stand=u1.get("galerie_stand"),
                    backend=u1.get("backend", ""), quelle=u1.get("quelle", ""),
                    custom_prompt=bool(u1.get("custom_prompt")))
    d1 = (u1.get("dauer_s") or 0) + (u2.get("dauer_s") or 0)
    o["dauer_s"] = round(d1, 1) if d1 else None
    for k in ("prompt", "completion", "total"):
        a, b = (u1.get("token") or {}).get(k), (u2.get("token") or {}).get(k)
        o["token"][k] = (a or 0) + (b or 0) if (a or b) else None
    if u1.get("kein_votum") or u2.get("kein_votum"):
        o["grund"] = u1.get("grund") or u2.get("grund")
        return o
    spiegel = {"A": "B", "B": "A", "NEITHER": "NEITHER"}
    o["konsistent"] = (spiegel.get(u1["wahl"]) == u2["wahl"])
    if not o["konsistent"]:
        o["grund"] = "tausch_widerspruch"
        return o
    if u1["wahl"] == "NEITHER":
        o["wahl"] = "NEITHER"
        o["grund"] = "neither"
        return o
    o["wahl"] = u1["wahl"]
    o["beginnt_mit_wort"] = True
    o["kein_votum"] = False
    return o


def einzel_werten(u1):
    """EINE Anfrage statt des Tausch-Doppellaufs (.165, abschaltbar).

    Der Tausch ist der Positions-Test: A im untauschten Lauf und B im
    getauschten meinen dieselbe Galerie, und ein Widerspruch entlarvt die
    Schlagseite (§2.5). Wer ihn abschaltet, halbiert die Anfragen und gibt
    genau diese Kontrolle auf — das Ergebnis ist dann das eine Antwort-Wort,
    nicht mehr. Deshalb ist `konsistent` hier NICHT True, sondern None: es
    wurde nichts auf Konsistenz geprueft, und ein True waere eine Behauptung
    ueber eine Pruefung, die gar nicht stattfand.

    NEITHER und jede unbrauchbare Antwort bleiben Enthaltung, wie beim Paar."""
    o = urteil_leer(arm=u1.get("arm"), galerie_stand=u1.get("galerie_stand"),
                    backend=u1.get("backend", ""), quelle=u1.get("quelle", ""),
                    custom_prompt=bool(u1.get("custom_prompt")))
    o["einzeln"] = True                 # der Ausweis: ohne Tauschlauf gewertet
    o["dauer_s"] = u1.get("dauer_s")
    for k in ("prompt", "completion", "total"):
        o["token"][k] = (u1.get("token") or {}).get(k)
    if u1.get("kein_votum") or u1.get("wahl") not in ("A", "B"):
        o["grund"] = (u1.get("grund")
                      or ("neither" if u1.get("wahl") == "NEITHER" else None))
        return o
    o["wahl"] = u1["wahl"]
    o["beginnt_mit_wort"] = bool(u1.get("beginnt_mit_wort"))
    o["kein_votum"] = False
    return o


# ------------------------------------------------------------------ Transport
class VisionFehler(Exception):
    """Traegt NUR die schon gefilterte Kurzmeldung (Log-Vertrag §9)."""

    def __init__(self, meldung, code=None):
        super().__init__(meldung)
        self.code = code


def holen(url, kopf, timeout_s, geheimnisse=()):
    """EIN lesender HTTP-Aufruf (GET). Getrennt von `senden`, weil hier NIE ein
    Bild mitfaehrt: der Modell-Listen-Abruf ist der Key-Test, und er ist bei
    allen drei API-Formen kostenlos. Fehler kommen als VisionFehler mit
    gefilterter Kurzmeldung heraus."""
    req = urllib.request.Request(url, headers=kopf, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as ex:
        try:
            koerper = ex.read()[:400].decode("utf-8", "replace")
        except Exception:
            koerper = ""
        raise VisionFehler(fehler_kurz(ex.code, koerper, geheimnisse), ex.code)
    except urllib.error.URLError as ex:
        raise VisionFehler(f"connection failed: "
                           f"{fehlertext_filtern(getattr(ex, 'reason', ex), geheimnisse, 80)}")
    except json.JSONDecodeError:
        raise VisionFehler("the endpoint answered, but not with JSON — "
                           "is this really an API base URL?")
    except Exception as ex:
        raise VisionFehler(
            f"{type(ex).__name__}: {fehlertext_filtern(ex, geheimnisse, 80)}")


def senden(url, kopf, body, timeout_s, geheimnisse=()):
    """EIN HTTP-Aufruf. Rueckgabe: (status, dekodiertes JSON).
    Fehler kommen als VisionFehler mit gefilterter Kurzmeldung heraus — der
    rohe Koerper verlaesst diese Funktion nie."""
    daten = json.dumps(body).encode()
    req = urllib.request.Request(url, data=daten, headers=kopf)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as ex:
        try:
            koerper = ex.read()[:400].decode("utf-8", "replace")
        except Exception:
            koerper = ""
        raise VisionFehler(fehler_kurz(ex.code, koerper, geheimnisse), ex.code)
    except urllib.error.URLError as ex:
        raise VisionFehler(f"connection failed: "
                           f"{fehlertext_filtern(getattr(ex, 'reason', ex), geheimnisse, 80)}")
    except json.JSONDecodeError:
        raise VisionFehler("the endpoint answered, but not with JSON — "
                           "is this really an API base URL?")
    except Exception as ex:
        raise VisionFehler(
            f"{type(ex).__name__}: {fehlertext_filtern(ex, geheimnisse, 80)}")


def senden_mit_deadline(url, kopf, body, timeout_s, deadline_s, geheimnisse=()):
    """ZWEISTUFIGE REISSLEINE (§7, Zug V4): Socket-Timeout PLUS Gesamt-Deadline.

    Warum zwei Stufen: `timeout_s` ist ein SOCKET-Timeout — er schlaegt nur an,
    wenn laengere Zeit gar nichts kommt. Eine Antwort, die alle paar Sekunden ein
    Byte troepfelt, laeuft daran beliebig lange vorbei; genau das ist der Fall,
    der einen Hintergrundlauf fuer Stunden festhaelt.

    Und warum die Verbindung geschlossen wird statt "aufgeben": ein Thread laesst
    sich in Python nicht toeten, `pool.shutdown(wait=False)` beendet ihn NICHT —
    der Leser bliebe im read() haengen und der Prozess sammelte bei jedem
    Zeitablauf einen weiteren Dauerlaeufer. Das Schliessen der Antwort reisst
    dessen read() ab, der Hilfsthread endet wirklich (der Beweis prueft genau
    das: is_alive() nach dem Zeitablauf).

    Rueckgabe wie `senden`: (status, dekodiertes JSON)."""
    import threading
    daten = json.dumps(body).encode()
    req = urllib.request.Request(url, data=daten, headers=kopf)
    kasten, fertig = {}, threading.Event()

    def _lesen():
        try:
            r = urllib.request.urlopen(req, timeout=timeout_s)
            kasten["resp"] = r                     # Griff fuer die Reissleine
            with r:
                kasten["daten"] = r.read()
                kasten["status"] = r.status
        except BaseException as ex:                # auch der Abriss durch close()
            kasten["fehler"] = ex
        finally:
            fertig.set()

    t = threading.Thread(target=_lesen, daemon=True, name="vision-anfrage")
    t.start()
    if not fertig.wait(max(1.0, float(deadline_s))):
        r = kasten.get("resp")
        if r is not None:
            try:
                r.close()                          # bricht das laufende read() ab
            except Exception:
                pass
        t.join(10)
        raise VisionFehler(
            "no vision verdict (timeout) — the endpoint answered, but kept "
            f"trickling past the overall deadline of {int(deadline_s)} s",
            "deadline")
    ex = kasten.get("fehler")
    if ex is not None:
        if isinstance(ex, urllib.error.HTTPError):
            try:
                koerper = ex.read()[:400].decode("utf-8", "replace")
            except Exception:
                koerper = ""
            raise VisionFehler(fehler_kurz(ex.code, koerper, geheimnisse), ex.code)
        if isinstance(ex, urllib.error.URLError):
            raise VisionFehler(
                "connection failed: "
                f"{fehlertext_filtern(getattr(ex, 'reason', ex), geheimnisse, 80)}")
        raise VisionFehler(
            f"{type(ex).__name__}: {fehlertext_filtern(ex, geheimnisse, 80)}")
    try:
        return kasten.get("status"), json.loads(kasten.get("daten") or b"{}")
    except json.JSONDecodeError:
        raise VisionFehler("the endpoint answered, but not with JSON — "
                           "is this really an API base URL?")


def anfrage(vcfg, teile, *, prompt_kopf=None, timeout_s=None, think_aus=None,
            deadline_s=None):
    """Eine Vision-Anfrage nach dem Adapter-Vertrag.

    GENAU EIN Wiederholversuch ohne die Zusatzfelder bei HTTP 400 (§5): der
    think-Schalter (`chat_template_kwargs`) ist eine llama.cpp/vLLM-Erweiterung,
    KEIN OpenAI-Feld — strikte Endpunkte antworten darauf mit 400. Der Retry
    laeuft nur einmal, nur bei 400 und nur, wenn ueberhaupt ein Zusatzfeld
    mitfuhr; er wird protokolliert (`retry_ohne_zusatzfeld`) und ist im Status
    sichtbar. Bei jedem anderen Code gibt es KEINEN Retry (401/403/429 wuerden
    sonst gegen den Deckel zaehlen, §7).

    `deadline_s` schaltet die ZWEITE Reissleinen-Stufe zu (§7, V4): der
    Socket-Timeout bleibt, zusaetzlich gilt eine Gesamt-Deadline ueber die ganze
    Anfrage. Ohne den Wert verhaelt sich der Adapter wie in V1/V2 — der
    Test-Knopf laesst bewusst auch einen langen Kaltstart durchlaufen.

    Rueckgabe: (roh, meta) — roh ist die auf den Vertrag reduzierte Antwort,
    meta traegt Dauer, Retry-Flag und die maskierte Quelle."""
    p = kachel(vcfg.get("kachel"))
    form = p["api"]
    modell = str(vcfg.get("modell") or "").strip()
    max_tokens = int(vcfg.get("max_tokens") or p["max_tokens"])
    timeout_s = int(timeout_s or vcfg.get("timeout_s") or 900)
    if think_aus is None:
        think_aus = bool(vcfg.get("think_aus")) and bool(p["kann_think_schalter"])
    else:
        think_aus = bool(think_aus) and bool(p["kann_think_schalter"])
    kopf_text = prompt_voll(prompt_kopf if prompt_kopf is not None
                            else vcfg.get("prompt"),
                            bool(vcfg.get("cloud_ok")))
    voll = list(teile) + [("text", kopf_text)]
    key = str(vcfg.get("api_key") or "")
    basis = endpunkt_wirksam(vcfg)
    url = url_bauen(basis, p["pfad"], modell, key, form)
    geheim = _reg.vision_geheimnisse(dict(vcfg, endpunkt=basis))
    kopfzeile = kopfzeilen(form, key)
    bauer = BODY_FORMEN[form]

    def _schicken(body):
        if deadline_s:
            return senden_mit_deadline(url, kopfzeile, body, timeout_s,
                                       deadline_s, geheim)
        return senden(url, kopfzeile, body, timeout_s, geheim)

    t0 = time.monotonic()
    retry = False
    try:
        body = bauer(p, voll, modell=modell, max_tokens=max_tokens,
                     temperature=p.get("temperature"), think_aus=think_aus)
        _, d = _schicken(body)
    except VisionFehler as ex:
        if ex.code != 400 or not think_aus:
            raise
        # GENAU EIN Wiederholversuch, ohne die Zusatzfelder.
        retry = True
        body = bauer(p, voll, modell=modell, max_tokens=max_tokens,
                     temperature=p.get("temperature"), think_aus=False)
        _, d = _schicken(body)
    dauer = round(time.monotonic() - t0, 1)
    roh = _antwort_lesen(d, form, p)
    host = urllib.parse.urlsplit(_reg.endpunkt_anzeige(basis)).netloc
    quelle = "local" if vcfg.get("betriebsart") == "lokal" else f"cloud: {host}"
    return roh, {"dauer_s": dauer, "retry_ohne_zusatzfeld": retry,
                 "quelle": quelle, "prompt_angepasst": prompt_ist_angepasst(
                     vcfg.get("prompt"), bool(vcfg.get("cloud_ok")))}


def _antwort_lesen(d, form, p):
    """Provider-Antwort -> Vertragsfelder (text/reasoning/stop/usage/refusal).
    Text-Extraktion ist eigener Vertragsteil (§5) — dort haengen die Messwerte."""
    d = d or {}
    if form == "anthropic":
        text = "".join(b.get("text") or "" for b in (d.get("content") or [])
                       if isinstance(b, dict) and b.get("type") == "text")
        return {"text": text, "reasoning": None,
                "stop_reason": d.get("stop_reason"),
                "refusal": (d.get("stop_details") or {}).get("explanation")
                if str(d.get("stop_reason")) == "refusal" else None,
                "usage": d.get("usage")}
    if form == "gemini":
        kand = (d.get("candidates") or [{}])[0] or {}
        text = "".join(t.get("text") or "" for t in
                       ((kand.get("content") or {}).get("parts") or [])
                       if isinstance(t, dict))
        # promptFeedback.blockReason ist die Verweigerung dieser API — sie wird
        # wie jede andere behandelt: kein Votum, nie ein Negativ-Beweis.
        sperre = (d.get("promptFeedback") or {}).get("blockReason")
        return {"text": text, "reasoning": None,
                "stop_reason": kand.get("finishReason"),
                "refusal": sperre, "usage": d.get("usageMetadata")}
    wahl = (d.get("choices") or [{}])[0] or {}
    msg = wahl.get("message") or {}
    rf = p.get("reasoning_feld") or "reasoning_content"
    return {"text": msg.get("content"), "reasoning": msg.get(rf),
            "finish_reason": wahl.get("finish_reason"),
            "refusal": msg.get(p["refusal_feld"]) if p.get("refusal_feld") else msg.get("refusal"),
            "usage": d.get("usage")}


# ------------------------------------------- Modell-Liste = die Key-Sofortpruefung
# §5: "sofort nach Key-Eingabe prueft die App den Key per Modell-Listen-Abruf der
# jeweiligen API-Form (OpenAI-kompatibel GET /models, Anthropic /v1/models, Gemini
# models?key=; kostenlos, kein Bild verlaesst das Haus)". Genau drei Leser, weil es
# genau drei Antwort-Formen gibt — und KEIN Bild, in keiner davon.
def _modelle_lesen(d, form):
    """Provider-Antwort -> [(id, label)] in der Reihenfolge des Anbieters."""
    d = d or {}
    aus = []
    if form == "gemini":
        for m in d.get("models") or []:
            if not isinstance(m, dict):
                continue
            # Nur Modelle, die ueberhaupt generateContent koennen — sonst stuenden
            # Einbettungs- und TTS-Modelle in einer Auswahl, die Bilder vergleichen
            # soll. Fehlt das Feld, wird das Modell mitgenommen (nicht ausgesiebt).
            arten = m.get("supportedGenerationMethods")
            if arten and "generateContent" not in arten:
                continue
            name = str(m.get("name") or "")
            kurz = name.split("/", 1)[1] if name.startswith("models/") else name
            if kurz:
                aus.append((kurz, str(m.get("displayName") or kurz)))
        return aus
    for m in d.get("data") or []:
        if not isinstance(m, dict):
            continue
        mid = str(m.get("id") or "")
        if mid:
            aus.append((mid, str(m.get("display_name") or mid)))
    return aus


def modelle_holen(vcfg, timeout_s=30):
    """Modell-Liste des konfigurierten Anbieters holen. Rueckgabe: Liste von
    dicts mit id/label/badge — das Badge kommt aus der zentralen
    Messwerte-Registry (core/registry), NIE als Literal aus dem UI. Wirft
    VisionFehler bei ungueltigem Key oder toter Verbindung."""
    k = kachel(vcfg.get("kachel"))
    kname = str(vcfg.get("kachel") or KACHEL_DEFAULT)
    key = str(vcfg.get("api_key") or "")
    basis = endpunkt_wirksam(vcfg)
    if not basis:
        raise VisionFehler("no endpoint configured yet")
    if k["key_pflicht"] and not key:
        raise VisionFehler("this provider needs an API key")
    url = basis.rstrip("/") + k["modelle_pfad"]
    if k["api"] == "gemini" and key:
        url += "?key=" + urllib.parse.quote(key)
    geheim = _reg.vision_geheimnisse(dict(vcfg, endpunkt=basis))
    _, d = holen(url, kopfzeilen(k["api"], key), int(timeout_s), geheim)
    roh = _modelle_lesen(d, k["api"])
    aus = []
    for mid, label in roh:
        badge = _reg.vision_badge(mid, kname)
        aus.append({"id": mid, "label": label, "badge": badge,
                    "gemessen": badge["gemessen"]})
    # Vermessene zuerst (der Nutzer soll sehen, wofuer wir Zahlen haben), sonst
    # in der Reihenfolge des Anbieters — nie eine erfundene Rangfolge.
    aus.sort(key=lambda e: (0 if e["gemessen"] else 1,))
    return aus


def modelle_gueltig(prot, vcfg):
    """HARTE REGEL (§5, User-Nacharbeit 08.08. spaetabends): es werden NIE
    Modelle vorab angezeigt. Der Weg ist immer
    verbinden -> entdecken -> anzeigen was GEFUNDEN wurde -> User waehlt.

    Ein gespeichertes Entdeckungs-Ergebnis gilt deshalb nur fuer GENAU die
    Verbindung, an der es entstanden ist: dieselbe Kachel und derselbe
    Endpunkt. Ohne diese Pruefung ueberlebte die Liste einen Kachel-Wechsel und
    die Seite haette Modelle eines FREMDEN Anbieters als Auswahl angeboten —
    genau die Vorab-Anzeige, die der Entscheid verbietet."""
    prot = prot or {}
    if not (prot.get("ok") and prot.get("modelle")):
        return False
    if prot.get("kachel") != (vcfg.get("kachel") or KACHEL_DEFAULT):
        return False
    return prot.get("endpunkt") == _reg.endpunkt_anzeige(endpunkt_wirksam(vcfg))


def schluessel_pruefen(vcfg, timeout_s=30):
    """Der Sofort-Test nach der Key-Eingabe. JSON-festes Protokoll ohne
    Geheimnisse (Ampel gruen/rot + Klartext + Modell-Liste); es landet im Store
    und auf der Seite. Kein Bild, keine Kosten — nur die Modell-Liste."""
    kname = str(vcfg.get("kachel") or KACHEL_DEFAULT)
    prot = {"ts": time.time(), "kachel": kname,
            "endpunkt": _reg.endpunkt_anzeige(endpunkt_wirksam(vcfg)),
            "ok": False, "ampel": "rot", "text": "", "modelle": [],
            "gewaehlt": str(vcfg.get("modell") or "")}
    try:
        modelle = modelle_holen(vcfg, timeout_s)
    except VisionFehler as ex:
        prot["text"] = str(ex)
        return prot
    prot["modelle"] = modelle
    prot["ok"] = True
    prot["ampel"] = "gruen"
    n_mess = sum(1 for m in modelle if m["gemessen"])
    prot["text"] = (f"key accepted — {len(modelle)} models available"
                    + (f", {n_mess} of them measured here" if n_mess else
                       ", none of them measured here"))
    return prot


# --------------------------------------------- Erzeugte Bilder (§9: kein Asset)
# Ein testbild.jpg im Image risse zwei Gate-Stufen gleichzeitig (Stufe 2:
# erlaubte Endungen unter /app; Stufe 5: JEDE Bilddatei ist rot) und fiele aus
# tools/source_export.sh — der veroeffentlichte Quelltext waere nicht mehr
# baubar. `.jpg` freizugeben waere genau die Aufweichung, die CLAUDE.md
# verbietet. Also: alles wird ZUR LAUFZEIT deterministisch erzeugt, mit numpy +
# cv2 (beide in docker/requirements.txt gepinnt). NIE Bewohner-Bilder, auch
# nicht auf Wunsch (§5, Teil-Ablehnung von F06).
LEINWAND_PROBE = (1176, 1008)      # Preset-Wert der gemessenen Qwen-Gitter


def _cv():
    import cv2
    import numpy as np
    return cv2, np


def testbild(breite=640, hoehe=480):
    """Stufe 1: deterministisches Testbild (Farbbalken + Ziffernraster).
    Keine Person, kein Kamerabild, keine Datei — nur Rechnung."""
    cv2, np = _cv()
    img = np.zeros((hoehe, breite, 3), dtype=np.uint8)
    farben = [(40, 40, 40), (200, 200, 200), (60, 120, 200), (60, 180, 90),
              (200, 160, 60), (170, 70, 160)]
    b = max(1, breite // len(farben))
    for i, f in enumerate(farben):
        img[:, i * b:(i + 1) * b] = f
    for i in range(6):
        cv2.putText(img, str(i + 1), (18 + i * b, hoehe - 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3,
                    cv2.LINE_AA)
    cv2.rectangle(img, (2, 2), (breite - 3, hoehe - 3), (255, 255, 255), 2)
    return _jpeg(img)


def _jpeg(img, q=92):
    cv2, _ = _cv()
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), q])
    if not ok:
        raise VisionFehler("could not encode the generated test image")
    return base64.b64encode(buf.tobytes()).decode()


def formprobe_gitter(form, zellen=6, leinwand=None):
    """Stufe 2: ein synthetisches Galerie-Gitter aus EINER Form ('kreis' oder
    'dreieck'), Zellen im Crop-Seitenverhaeltnis (hochkant, wie die echten
    Personen-Crops). Sollantwort ist damit BEKANNT — das ist der Punkt: der
    Test prueft Format-Treue, Parser, think-Schalter und Verweigerung, ohne
    dass ein Kamerabild das Haus verlaesst."""
    cv2, np = _cv()
    lw, lh = leinwand or LEINWAND_PROBE
    spalten = 2 if zellen <= 6 else 3
    reihen = max(1, -(-zellen // spalten))
    zb, zh = lw // spalten, lh // reihen
    img = np.full((zh * reihen, zb * spalten, 3), 245, dtype=np.uint8)
    for i in range(zellen):
        r, c = divmod(i, spalten)
        x0, y0 = c * zb, r * zh
        cv2.rectangle(img, (x0 + 2, y0 + 2), (x0 + zb - 3, y0 + zh - 3),
                      (210, 210, 210), 2)
        cx, cy = x0 + zb // 2, y0 + zh // 2
        rad = min(zb, zh) // 3
        # Leichte, deterministische Variation je Zelle (wie "verschiedene Tage")
        d = (i % 3) - 1
        if form == "kreis":
            cv2.circle(img, (cx + d * 6, cy), rad, (40, 90, 190), -1)
        else:
            pkt = np.array([[cx + d * 6, cy - rad],
                            [cx - rad + d * 6, cy + rad],
                            [cx + rad + d * 6, cy + rad]], dtype=np.int32)
            cv2.fillPoly(img, [pkt], (50, 160, 70))
    return _jpeg(img)


def formprobe_kandidat(form, leinwand=None):
    """Der Kandidat der Formprobe: EINE Zelle derselben Form, andere Groesse
    und Position — damit es kein Pixelvergleich, sondern eine Formfrage ist."""
    cv2, np = _cv()
    lw, lh = leinwand or LEINWAND_PROBE
    b, h = lw // 3, lh // 2
    img = np.full((h, b, 3), 245, dtype=np.uint8)
    cx, cy, rad = b // 2, h // 2, min(b, h) // 3
    if form == "kreis":
        cv2.circle(img, (cx, cy), rad, (40, 90, 190), -1)
    else:
        pkt = np.array([[cx, cy - rad], [cx - rad, cy + rad],
                        [cx + rad, cy + rad]], dtype=np.int32)
        cv2.fillPoly(img, [pkt], (50, 160, 70))
    return _jpeg(img)


FORMPROBE_KOPF = (
    "Shape check. Forced choice: does the candidate image show the shape of "
    "reference set A, the shape of reference set B, or NEITHER of them? "
    "Set A and set B each show one shape repeated. Judge the shape only, not "
    "its size or position.")


def formprobe_labels(n):
    return (f"Reference set A: {n} images of ONE shape.",
            f"Reference set B: a DIFFERENT shape, {n} images.")


# GEMESSENER Sollwert des Token-Audits (Stufe 3). Er gehoert zu DIESEN erzeugten
# Bildern auf DIESER Leinwand, nicht zu den Personen-Gittern; die Zahl wird beim
# Bau gegen den lokalen Modell-Server gemessen und mit Datum + Quelle eingetragen.
# Der Vergleich ist bewusst GELB und nicht ROT: fuer ein Backend, das anders
# kachelt als Qwen-ViT, ist der Sollwert nicht bindend (§5).
FORMPROBE_TOKEN_SOLL = {
    "wert": 2705,                  # gemessen, nicht gerechnet: beide Formproben-
    #                                Laeufe meldeten exakt 2705 prompt_tokens
    "gemessen": "2026-08-08",
    "quelle": ("llama.cpp b10326 / Qwen3.5-9B Q8_0 (eigene Anlage), "
               "scratchpad/beweis_v1_test.json"),
    "leinwand": LEINWAND_PROBE,
    "zellen": 6,
}
TOKEN_AUDIT_ANTEIL = 0.60          # darunter = GELB "this backend shrinks images"


# ------------------------------------------------------- Dreistufiger Test §5
# Der Test besteht aus DREI Stufen, und seit V4 ist jede einzeln aufrufbar
# (User-Feedback 08.08.: "ich will sehen, welche Stufe gerade laeuft, und am
# Ende ein Testlog"). Eine lokale Stufe dauert Minuten — ein einziger Aufruf,
# der schweigend minutenlang laeuft, sieht wie ein Haenger aus. Der Browser ruft
# deshalb Stufe fuer Stufe und fuellt das Log mit; SERVER-Zustand entsteht
# dabei keiner: das Protokoll faehrt vollstaendig hin und zurueck und liegt am
# Ende dort, wo es vorher auch lag (state/vision_test.json).
STUFEN = ((1, "reachability"), (2, "forced choice"), (3, "token audit"))
STUFE_OFFEN = "grau"               # Ampel-Wert "noch nicht gelaufen"


def test_protokoll(vcfg):
    """Frisches Protokoll mit drei PLATZHALTER-Stufen ("not run"). Damit zeigt
    die Seite von Anfang an, was kommt — und ein Abbruch in Stufe 2 laesst
    Stufe 3 sichtbar als "not run" stehen, statt sie verschwinden zu lassen."""
    kname = str(vcfg.get("kachel") or KACHEL_DEFAULT)
    p = kachel(kname)
    modell = str(vcfg.get("modell") or "")
    return {"ts": time.time(), "kachel": kname, "kachel_label": p["label"],
            "endpunkt": _reg.endpunkt_anzeige(endpunkt_wirksam(vcfg)),
            "modell": modell,
            "modell_badge": _reg.vision_badge(modell, kname) if modell else None,
            "stufen": [{"nr": nr, "name": name, "ampel": STUFE_OFFEN,
                        "text": "not run"} for nr, name in STUFEN],
            "ampel": "offen"}


def ampel_gesamt(prot):
    """Die Gesamt-Ampel aus den Stufen. "offen" heisst: noch nicht alles
    gelaufen — und weil der E4-Schalter auf "gruen" prueft, kann ein halb
    gefahrener Test den Scharf-Schalter niemals freigeben."""
    a = [s.get("ampel") for s in (prot or {}).get("stufen") or []]
    if not a:
        return "rot"
    if "rot" in a:
        return "rot"
    if STUFE_OFFEN in a:
        return "offen"
    return "gelb" if "gelb" in a else "gruen"


def _stufe_setzen(prot, nr, ampel, text, **rest):
    for i, s in enumerate(prot["stufen"]):
        if s["nr"] == nr:
            prot["stufen"][i] = dict(nr=nr, name=s["name"], ampel=ampel,
                                     text=text, **rest)
            break
    prot["ampel"] = ampel_gesamt(prot)
    return prot


def _stufe1(vcfg, prot, timeout_s):
    """Erreichbarkeit + Modell + Zeitmessung, mit dem ERZEUGTEN Testbild."""
    p = kachel(vcfg.get("kachel"))
    if not endpunkt_wirksam(vcfg):
        return _stufe_setzen(prot, 1, "rot", "no endpoint configured yet")
    if p.get("key_pflicht") and not str(vcfg.get("api_key") or "").strip():
        return _stufe_setzen(prot, 1, "rot", "this provider needs an API key")
    if not str(vcfg.get("modell") or ""):
        return _stufe_setzen(prot, 1, "rot",
                             "no model picked yet — check the connection "
                             "first, then choose one from the list")
    try:
        b64 = testbild()
    except Exception as ex:
        return _stufe_setzen(prot, 1, "rot",
                             f"could not build the test image: {ex}")
    teile = [("text", "Test image. Answer with exactly one word: OK"),
             ("bild", b64)]
    t0 = time.monotonic()
    try:
        roh, meta = anfrage(vcfg, teile, prompt_kopf="", timeout_s=timeout_s)
    except VisionFehler as ex:
        return _stufe_setzen(prot, 1, "rot", str(ex))
    dauer = round(time.monotonic() - t0, 1)
    u = antwort_auswerten(roh, kachel_name=vcfg.get("kachel"), dauer_s=dauer,
                          quelle=meta["quelle"],
                          retry_ohne_zusatzfeld=meta["retry_ohne_zusatzfeld"])
    return _stufe_setzen(
        prot, 1, "gruen",
        f"{prot.get('modell') or 'the model'} answered in {dauer} s"
        + (" (one retry without the thinking switch — this endpoint rejects it)"
           if meta["retry_ohne_zusatzfeld"] else ""),
        dauer_s=dauer, token=u["token"], antwort=u["sichtbar"][:80],
        retry_ohne_zusatzfeld=meta["retry_ohne_zusatzfeld"])


def _stufe2(vcfg, prot, timeout_s, zellen):
    """Zwangswahl-Formprobe auf synthetischen Gittern mit bekannter Sollantwort
    — Format-Treue, Parser, think-Schalter und Verweigerung, ohne dass ein
    Kamerabild das Haus verlaesst."""
    p = kachel(vcfg.get("kachel"))
    try:
        g_kreis = formprobe_gitter("kreis", zellen, p.get("leinwand"))
        g_drei = formprobe_gitter("dreieck", zellen, p.get("leinwand"))
        k_kreis = formprobe_kandidat("kreis", p.get("leinwand"))
    except Exception as ex:
        return _stufe_setzen(prot, 2, "rot",
                             f"could not build the probe grids: {ex}")
    la, lb = formprobe_labels(zellen)
    laeufe, tokens = [], []
    for name, pos_a, pos_b, soll in (("plain", g_kreis, g_drei, "A"),
                                     ("swapped", g_drei, g_kreis, "B")):
        teile = [("text", la), ("bild", pos_a), ("text", lb), ("bild", pos_b),
                 ("text", LABEL_K), ("bild", k_kreis)]
        try:
            roh, meta = anfrage(vcfg, teile, prompt_kopf=FORMPROBE_KOPF,
                                timeout_s=timeout_s)
        except VisionFehler as ex:
            return _stufe_setzen(prot, 2, "rot", str(ex), laeufe=laeufe)
        u = antwort_auswerten(roh, kachel_name=vcfg.get("kachel"),
                              dauer_s=meta["dauer_s"], quelle=meta["quelle"],
                              retry_ohne_zusatzfeld=meta["retry_ohne_zusatzfeld"])
        laeufe.append({"arm": name, "soll": soll, "wahl": u["wahl"],
                       "beginnt_mit_wort": u["beginnt_mit_wort"],
                       "kein_votum": u["kein_votum"], "grund": u["grund"],
                       "dauer_s": u["dauer_s"], "token": u["token"],
                       "sichtbar": u["sichtbar"][:120]})
        if (u["token"] or {}).get("prompt"):
            tokens.append(u["token"]["prompt"])
    treffer = sum(1 for l in laeufe if l["wahl"] == l["soll"])
    formtreu = all(l["beginnt_mit_wort"] for l in laeufe)
    if treffer == 2 and formtreu:
        return _stufe_setzen(prot, 2, "gruen",
                             f"{treffer} of 2 probe runs right, both in the "
                             "required one-word form (swap included)",
                             laeufe=laeufe, treffer=treffer, token_prompt=tokens)
    if treffer == 2:
        return _stufe_setzen(prot, 2, "gelb",
                             f"{treffer} of 2 probe runs right, but not in the "
                             "required one-word form — verdicts from this "
                             "backend may not parse",
                             laeufe=laeufe, treffer=treffer, token_prompt=tokens)
    return _stufe_setzen(prot, 2, "rot",
                         f"{treffer} of 2 probe runs were right — this backend "
                         "cannot do the forced choice reliably",
                         laeufe=laeufe, treffer=treffer, token_prompt=tokens)


def _stufe3(prot):
    """Token-Audit gegen den gemessenen Sollwert — so faellt ein Backend auf,
    das Bilder staucht (der einzige gemessene Totalausfall lief an einem reinen
    Erreichbarkeits-Ping vorbei). Bewusst GELB statt ROT: fuer ein Backend, das
    anders kachelt, ist der Sollwert nicht bindend."""
    soll = FORMPROBE_TOKEN_SOLL
    tokens = []
    for s in prot.get("stufen") or []:
        if s["nr"] == 2:
            tokens = list(s.get("token_prompt") or [])
    if not soll["wert"]:
        return _stufe_setzen(prot, 3, "gelb",
                             "no measured reference value for these probe "
                             "images yet — image shrinking cannot be checked",
                             soll=None)
    if not tokens:
        return _stufe_setzen(prot, 3, "gelb",
                             "the backend reports no prompt_tokens — image "
                             "shrinking cannot be checked here",
                             soll=soll["wert"])
    ist = min(tokens)
    anteil = ist / soll["wert"]
    if anteil < TOKEN_AUDIT_ANTEIL:
        return _stufe_setzen(prot, 3, "gelb",
                             "this backend shrinks images — grid verdicts are "
                             f"unreliable here ({ist} prompt tokens against "
                             f"about {soll['wert']} measured on the reference "
                             "setup)", ist=ist, soll=soll["wert"],
                             anteil=round(anteil, 2))
    return _stufe_setzen(prot, 3, "gruen",
                         f"{ist} prompt tokens — in the measured range (about "
                         f"{soll['wert']})", ist=ist, soll=soll["wert"],
                         anteil=round(anteil, 2))


def test_stufe(vcfg, nr, prot=None, *, timeout_s=None, zellen=6):
    """EINE Stufe fuer sich, mit dem Protokoll als durchgereichtem Zustand.
    Rueckgabe: (prot, weiter) — `weiter` ist False, sobald eine Stufe ROT ist;
    die Folgestufen bleiben dann als "not run" stehen."""
    prot = prot or test_protokoll(vcfg)
    t = int(timeout_s or vcfg.get("timeout_s") or 900)
    nr = int(nr)
    if nr == 1:
        prot = _stufe1(vcfg, prot, t)
    elif nr == 2:
        prot = _stufe2(vcfg, prot, t, zellen)
    elif nr == 3:
        prot = _stufe3(prot)
    else:
        raise VisionFehler(f"unknown test step {nr}")
    ist = next((s for s in prot["stufen"] if s["nr"] == nr), {})
    return prot, ist.get("ampel") != "rot"


def test_lauf(vcfg, *, timeout_s=None, zellen=6):
    """Alle drei Stufen nacheinander (ein Aufruf) — derselbe Weg wie der
    Browser ihn Stufe fuer Stufe geht, damit es nur EINE Test-Logik gibt.

      1 Erreichbarkeit + Modell + Zeitmessung mit dem ERZEUGTEN Testbild
      2 Zwangswahl-Formprobe auf synthetischen Gittern mit bekannter Sollantwort
      3 Token-Audit gegen den gemessenen Sollwert, GELB bei Stauchung

    Rueckgabe: Protokoll-dict (JSON-fest, ohne Geheimnisse)."""
    prot = test_protokoll(vcfg)
    for nr, _name in STUFEN:
        prot, weiter = test_stufe(vcfg, nr, prot, timeout_s=timeout_s,
                                  zellen=zellen)
        if not weiter:
            break
    return prot


# ---------------------------------------------------- Config: reine Validierung
# Der Vision-Block liegt als EIN Top-Level-Schluessel im /data-Store (Muster der
# Meldekanaele telegram/pushover/mqtt), geschrieben ueber genau einen Weg. Die
# beiden reinen Zahlenwerte liegen zusaetzlich als Whitelist-PAAR in verifyd
# (§5: Default in load_config UND Eintrag in CONFIG_WHITELIST).
VISION_FELDER = ("kachel", "betriebsart", "endpunkt", "host", "port", "api_key",
                 "modell", "prompt", "think_aus", "cloud_ok", "cloud_ok_ts",
                 "aktiv")
BETRIEBSARTEN = ("lokal", "extern")


def block_migrieren(alt):
    """Ein Vision-Block aus V1 (Feld `preset`) auf die Kachel-Welt ziehen.
    Ohne das verloere eine bestehende Installation beim Update still ihre
    Verbindung — dieselbe Fehlerklasse, die der Config-Export-Vertrag schon
    einmal gefangen hat. Reine Logik, idempotent."""
    a = dict(alt or {})
    if a.get("kachel") or not a.get("preset"):
        return a
    p = str(a.pop("preset"))
    a["kachel"] = PRESET_ALT.get(p, KACHEL_DEFAULT)
    if a["kachel"] == "lokal" and a.get("endpunkt") and not a.get("host"):
        # http://host:port/v1 -> Host + Port (die Lokal-Kachel hat zwei Felder)
        teile = urllib.parse.urlsplit(str(a.get("endpunkt")))
        if teile.hostname:
            a["host"] = f"{teile.scheme or 'http'}://{teile.hostname}"
            a["port"] = str(teile.port or "")
    return a


def werte_pruefen(neu, alt=None, cloud_gate=True):
    """Formularwerte -> (ok, neuer Block | Fehlertext). REINE Logik.
    Leeres Secret-Feld behaelt den gespeicherten Wert (Muster notif_speichern:
    nie mit Leer ueberschreiben). `aktiv` kommt NICHT von hier — der Schalter
    laeuft ueber sein eigenes Gate (E4).

    `cloud_gate=False` ist AUSSCHLIESSLICH fuer die Key-Sofortpruefung da: sie
    holt nur die Modell-Liste, es verlaesst kein einziges Bild das Haus, und
    ihr Ergebnis wird NIE als Config gespeichert. Die Cloud-Bestaetigung (§9)
    gilt fuer das Speichern und fuer jeden Weg, auf dem Bilder rausgehen — dort
    steht der Vorgabewert True, und die Gate-Stufe prueft genau den."""
    alt = block_migrieren(alt)
    a = dict(alt)

    p = str(neu.get("kachel") or alt.get("kachel") or KACHEL_DEFAULT).strip()
    if p not in KACHELN:
        return False, f"unknown provider '{p}'"
    a["kachel"] = p
    k = KACHELN[p]

    # Betriebsart ist bei vier von fuenf Kacheln KEINE Wahl mehr, sondern eine
    # Tatsache: die drei Namens-Anbieter sind Internet-Dienste, die Lokal-Kachel
    # ist es nicht. Nur Custom darf sie setzen — und steht konservativ auf
    # extern, weil wir eine fremde URL nicht zuverlaessig einordnen koennen
    # (die IP-Selbstpruefung ist in Container-/NAT-Lagen nicht verlaesslich).
    if k["eingabe"] == "url_key":
        art = str(neu.get("betriebsart") or alt.get("betriebsart")
                  or k["betriebsart"]).strip()
        if art not in BETRIEBSARTEN:
            return False, f"mode must be one of {', '.join(BETRIEBSARTEN)}"
    else:
        art = k["betriebsart"]
    a["betriebsart"] = art

    # Endpunkt: nur Custom traegt eine freie URL. Bei den Namens-Kacheln steht
    # sie FEST im Code (der Nutzer kann sie nicht eintippen und nicht
    # verstellen), bei Lokal wird sie aus Host + Port gebaut.
    if k["eingabe"] == "url_key":
        ep = str(neu.get("endpunkt") if neu.get("endpunkt") is not None
                 else alt.get("endpunkt") or "").strip()
        if ep and not re.match(r"^https?://[^\s/]+", ep):
            return False, "the endpoint must start with http:// or https://"
        a["endpunkt"], a["host"], a["port"] = ep, "", ""
    elif k["eingabe"] == "host_port":
        host = str(neu.get("host") if neu.get("host") is not None
                   else alt.get("host") or "").strip().rstrip("/")
        port = str(neu.get("port") if neu.get("port") is not None
                   else alt.get("port") or "").strip()
        if host and not re.match(r"^(https?://)?[\w.\-]+$", host):
            return False, ("the host is just a name or an address, like "
                           "my-server or 10.x.x.x — no path, no key")
        if port and not (port.isdigit() and 1 <= int(port) <= 65535):
            return False, "the port must be a number between 1 and 65535"
        a["host"], a["port"], a["endpunkt"] = host, port, ""
    else:
        a["endpunkt"], a["host"], a["port"] = k["basis"], "", ""

    key_neu = str(neu.get("api_key") or "").strip()
    a["api_key"] = key_neu or str(alt.get("api_key") or "")
    if k["key_pflicht"] and not a["api_key"]:
        return False, "this provider needs an API key"

    a["modell"] = str(neu.get("modell") if neu.get("modell") is not None
                      else alt.get("modell") or "").strip()
    a["think_aus"] = str(neu.get("think_aus", alt.get("think_aus", False))
                         ).lower() in ("1", "true", "ja", "on", "yes")
    if a["think_aus"] and not k["kann_think_schalter"]:
        a["think_aus"] = False        # Flag statt blindem Knopf (§5)

    # Cloud-Bestaetigung: nur SETZEN per ausdruecklicher Bestaetigung, und sie
    # faellt automatisch weg, sobald wieder lokal gefahren wird (Widerruf =
    # Schalter aus, §9). Der Zeitstempel wandert zusaetzlich ins Audit-Log.
    if art != "extern":
        a["cloud_ok"], a["cloud_ok_ts"] = False, None
    elif str(neu.get("cloud_ok", "")).lower() in ("1", "true", "ja", "on", "yes"):
        if not alt.get("cloud_ok"):
            a["cloud_ok_ts"] = round(time.time(), 1)
        a["cloud_ok"] = True
    else:
        a["cloud_ok"] = bool(alt.get("cloud_ok"))
        a["cloud_ok_ts"] = alt.get("cloud_ok_ts")
    if cloud_gate and art == "extern" and not a["cloud_ok"]:
        return False, ("external mode needs the cloud confirmation — images of "
                       "people, including visitors and passers-by, would leave "
                       "your house")

    # Prompt: nur der KOPF wird gespeichert; der Anker kommt beim Bauen dazu und
    # ist nicht entfernbar. NORMALISIERUNG (User-Fund 08.08.): das Feld zeigt
    # jetzt IMMER einen Wortlaut — also kommt der Default-Wortlaut auch wieder
    # zurueck, sobald jemand speichert, ohne etwas geaendert zu haben. Er wird
    # deshalb hier auf "" zurueckgerechnet, sonst haette jeder zweite Nutzer
    # ohne eigenes Zutun die Marke "custom prompt" an seinen Urteilen. Verglichen
    # wird gegen BEIDE Default-Fassungen (mit und ohne Consent-Satz, E12) —
    # sonst waere derselbe Text vor und nach der Cloud-Bestaetigung einmal
    # Default und einmal "custom". Beide Fassungen kommen aus der EINEN Quelle
    # (prompt_default), die auch der Urteilspfad benutzt.
    roh = neu.get("prompt")
    if roh is None:
        a["prompt"] = alt.get("prompt", "")
    else:
        kopf = str(roh).strip()
        if kopf:
            marke = "Answer FIRST with exactly one word"
            i = kopf.find(marke)
            if i >= 0:
                kopf = kopf[:i].rstrip()
        a["prompt"] = "" if kopf in ("", prompt_default(False),
                                     prompt_default(True)) else kopf

    a.setdefault("aktiv", bool(alt.get("aktiv")))
    return True, {k: a.get(k) for k in VISION_FELDER}


# ------------------------------------------------- Vorbedingungen (E4, §4/§3.1)
GALERIEN_MIN = 2                # E4 fortgeschrieben: >=2, nicht >=1 (E10)


def vorbedingungen(data_dir, vcfg, testprotokoll=None):
    """Die DREI Vorbedingungen des Schalters, je mit Klartext-Grund. Seit V2
    gibt es den Galerie-Bau — gezaehlt werden aber nur ABGENOMMENE Galerien
    (Ordner mit Herkunfts-Manifest), nie ein angefangener Ordner.

    Die Kandidaten-Quelle wird an der TATSACHE auf der Platte gemessen, nicht am
    Config-Schalter: `diagnostic_collection` liest im ganzen Dienst genau EINE
    Stelle (Z8-Vertrag, `_kontroll_speicher` — ein zweiter Lesegriff waere die
    Streu-Literal-Klasse). Ob der Ordner im Schlank-Modus nach der Karenz wieder
    leer laeuft, sagt der Hinweistext."""
    import os
    wurz = os.path.join(str(data_dir or ""), "personlern", "galerien")
    galerien = []
    try:
        galerien = sorted(
            n for n in os.listdir(wurz)
            if os.path.isfile(os.path.join(wurz, n, "herkunft.json")))
    except OSError:
        pass
    test_gruen = bool((testprotokoll or {}).get("ampel") == "gruen")
    try:
        kontrolle = bool(os.listdir(os.path.join(str(data_dir or ""), "personlern",
                                                 "kontrolle")))
    except OSError:
        kontrolle = False
    fehlt = []
    if len(galerien) < GALERIEN_MIN:
        fehlt.append(f"{len(galerien)} of {GALERIEN_MIN} approved galleries — "
                     "build one under 'Build a gallery'")
    if not test_gruen:
        fehlt.append("a green connection test")
    if not kontrolle:
        fehlt.append("judged images to pick a candidate from — they appear "
                     "while a pass is running; turn on 'diagnostic collection' "
                     "under Person if you want them to stay")
    return {"galerien": galerien, "galerien_min": GALERIEN_MIN,
            "test_gruen": test_gruen, "kandidatenquelle": kontrolle,
            "fehlt": fehlt, "erfuellt": not fehlt}
