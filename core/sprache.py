"""core/sprache — DIE eine Textauflösung der UI (konzept_sprache.md v2).

Architektur (Widerleger-Befunde B1-B7 eingearbeitet):
- Textquellen: core/texte/<code>.py, je ein flaches dict T; ENGLISCH ist
  die Referenz. Fehlt ein Schluessel in der aktiven Sprache, faellt t()
  LAUT (eine Log-Zeile je Prozess+Schluessel) auf Englisch zurueck; fehlt
  er auch dort, kommt der Schluessel selbst zurueck (sichtbar kaputt statt
  leise leer).
- Aktive Sprache: contextvar (B1) — gesetzt an den Eintrittspunkten
  (Request-Beginn, Meldetext-Bau, Waechter-Alert) via aktivieren(). Die
  Aufloesung dahinter liest den Config-Store ueber einen mtime-gecachten
  Reader (B2): store_sprache() parst <data_dir>/config.json nur, wenn sich
  die Datei geaendert hat — billig je Request, sofort wirksam, auch aus
  Prozessen ohne Dienst-Config (Live-Waechter).
- Formatiert wird NUR bei uebergebenen kwargs (B7 — literal { } in langen
  HTML-Texten bleibt heil). Plural: t_n(key, n) loest key+'.eins' bzw.
  key+'.viele'; die Formenwahl liegt JE SPRACHE in WAEHLER (B6 —
  formenzahl-variabel, Polnisch braeuchte spaeter drei Formen ohne
  API-Bruch).
- JS erreicht Texte NIE direkt: das Seitenskelett injiziert window.T als
  json.dumps ueber js_tabelle() (B3/B4). t_html() existiert seit Stufe 1
  (§8.1 hat den Vertrag vorgezogen), aber NUR fuer die in HTML_SCHLUESSEL
  deklarierten Schluessel — jeder andere Schluessel bleibt Plaintext, der
  Aufrufer escapt wie bisher mit html.escape.

Dieses Modul liefert Texte, nie Urteile und nie HTML."""
import contextvars
import json
import os
import threading

# Registrierte Sprachen — DIE Whitelist (Store-Wert, Schalter, Wizard-Schritt 0,
# Gate-Deckung via tools/texte_pruefen.py). Reihenfolge = Schalter-Reihenfolge.
# en/de/es/it/fr seit Sprach-Stufe 1 (Registrierung war bewusst der LETZTE
# Schritt: der Schalter blendet sich unter 2 Eintraegen selbst aus, nichts
# lief halb verdrahtet).
SPRACHEN = ("en", "de", "es", "it", "fr")
_STANDARD = "en"

# Eigennamen der Sprachen fuer den Schalter (konzept_sprache.md §6.1):
# jede Sprache nennt sich selbst, wird also NIE uebersetzt — deshalb hier
# als zentrale Tabelle und nicht als Text-Schluessel. Schluesselmenge ==
# moegliche SPRACHEN-Eintraege (Deckungs-Vertrag, Gate prueft Deckung).
NAMEN = {"en": "English", "de": "Deutsch", "es": "Español",
         "it": "Italiano", "fr": "Français"}

_aktiv = contextvars.ContextVar("suslik_sprache", default=None)

_tabellen = {}              # code -> dict (einmal importiert)
_tabellen_lock = threading.Lock()

_store = {"pfad": None, "mtime": None, "wert": _STANDARD}
_store_lock = threading.Lock()

_fallback_gemeldet = set()  # (code, key) — eine Log-Zeile je Prozess


def _lade(code):
    with _tabellen_lock:
        if code not in _tabellen:
            import importlib
            try:
                mod = importlib.import_module(f"core.texte.{code}")
                _tabellen[code] = dict(getattr(mod, "T", {}))
            except Exception:
                _tabellen[code] = {}
        return _tabellen[code]


def _store_pfad():
    # Der Config-Store liegt GENESTET unter config/config.json (Layout-
    # Umbau 22.07.; live verifiziert 19.08. — /data/config.json existiert
    # NICHT). Genau diese Datei sichert auch master_backup taeglich mit:
    # die Sprachwahl ueberlebt Backup/Restore automatisch (User-Auflage).
    d = os.environ.get("VERIFY_DATA_DIR")
    return os.path.join(d, "config", "config.json") if d else None


def store_sprache():
    """Sprache aus dem Config-Store, mtime-gecacht (B2). Ohne Store oder
    ohne Key gilt Englisch. Nie eine Exception nach aussen."""
    p = _store_pfad()
    if not p:
        return _STANDARD
    try:
        m = os.path.getmtime(p)
    except OSError:
        return _STANDARD
    with _store_lock:
        if _store["pfad"] == p and _store["mtime"] == m:
            return _store["wert"]
        try:
            with open(p, encoding="utf-8") as f:
                w = str(json.load(f).get("sprache") or _STANDARD)
        except Exception:
            w = _STANDARD
        if w not in SPRACHEN:
            w = _STANDARD
        _store.update(pfad=p, mtime=m, wert=w)
        return w


def validieren(roh):
    """Whitelist-Pruefung fuer den Store-Schreibweg (Areas-Muster, B12):
    (True, code) bei gueltigem Sprachcode, sonst (False, Klartext).
    Kein Cache-Eingriff noetig — store_sprache() liest mtime-basiert."""
    w = str(roh or "").strip().lower()
    if w in SPRACHEN:
        return True, w
    return False, f"unknown language '{w}' — allowed: {', '.join(SPRACHEN)}"


def aktivieren(code=None):
    """Aktive Sprache DIESES Kontexts setzen — an den Eintrittspunkten
    aufrufen (Request-Beginn, Meldetext-Bau, Waechter-Alert). Ohne Argument
    wird der Store gelesen."""
    w = code if code in SPRACHEN else store_sprache()
    _aktiv.set(w)
    return w


def aktive():
    w = _aktiv.get()
    return w if w in SPRACHEN else store_sprache()


def _roh(key, code):
    w = _lade(code).get(key)
    if w is not None:
        return w
    if code != _STANDARD:
        marke = (code, key)
        if marke not in _fallback_gemeldet:
            _fallback_gemeldet.add(marke)
            print(f"[sprache] {code}: key '{key}' fehlt — Fallback en",
                  flush=True)
        w = _lade(_STANDARD).get(key)
        if w is not None:
            return w
    marke = (_STANDARD, key)
    if marke not in _fallback_gemeldet:
        _fallback_gemeldet.add(marke)
        print(f"[sprache] key '{key}' fehlt in der Referenz", flush=True)
    return key


def t(key, **kw):
    """Plaintext-Schluessel aufloesen. Formatiert NUR bei kwargs (B7).
    Der Aufrufer escapt fuer HTML wie bisher (html.escape) — dieses Modul
    liefert nie markiertes HTML."""
    w = _roh(key, aktive())
    if kw:
        try:
            return w.format(**kw)
        except (KeyError, IndexError, ValueError):
            return w
    return w


# Plural-Formenwahl JE SPRACHE (B6): liefert das Suffix fuer t_n.
WAEHLER = {
    "en": lambda n: "eins" if n == 1 else "viele",
    "de": lambda n: "eins" if n == 1 else "viele",
    "es": lambda n: "eins" if n == 1 else "viele",
    "it": lambda n: "eins" if n == 1 else "viele",
    "fr": lambda n: "eins" if n in (0, 1) else "viele",
}


def t_n(key, n, **kw):
    form = WAEHLER.get(aktive(), WAEHLER[_STANDARD])(int(n))
    return t(f"{key}.{form}", n=n, **kw)


# HTML-Schluessel-Vertrag (B4; §8.1 zieht ihn in Stufe 1 vor): NUR die hier
# deklarierten Schluessel duerfen Markup tragen, t_html() ist ihr einziger
# Leseweg. kwargs werden VOR dem Einsetzen escapt (quote=True, also auch
# href-tauglich) — Aufrufer geben Rohwerte. Tag-Whitelist + Balance prueft
# die Gate-Stufe Sprach-Deckung; tools/texte_pruefen.py verlangt je
# Uebersetzung die IDENTISCHE Tag-Folge wie in en.py.
#
# Tag-Whitelist (DIE zentrale Quelle — qs.sh/PYSPR liest sie hier, kein
# Zweit-Literal, QS-Ebenen-Regel): b/i/code/small/br/a seit Stufe 1;
# "p" seit Stufe 3 — die /hilfe-Anleitungen sind Absatz-Prosa, dort ist
# der <p>-Absatz selbst die Schluessel-Einheit (ein Absatz = ein
# Schluessel, B9-Granularitaet) und traegt sein Tag im Wert.
HTML_TAGS = frozenset({"b", "i", "code", "small", "br", "a", "p"})
HTML_SCHLUESSEL = frozenset({
    "ui.upd.satz",
    # ---- Anleitungen /hilfe (Stufe 3): je Seite die Absatz-Schluessel ----
    "hilfe.live.satz1", "hilfe.live.satz2", "hilfe.live.satz3",
    "hilfe.live.satz4", "hilfe.live.satz5",
    "hilfe.gesicht.satz1", "hilfe.gesicht.satz2", "hilfe.gesicht.satz3",
    "hilfe.gesicht.satz4", "hilfe.gesicht.satz5", "hilfe.gesicht.satz6",
    "hilfe.koerper.satz1", "hilfe.koerper.satz2", "hilfe.koerper.satz3",
    "hilfe.koerper.satz4",
    "hilfe.vision.satz1", "hilfe.vision.satz2", "hilfe.vision.satz3",
    "hilfe.vision.satz4",
    "hilfe.faces_bekannt.satz1", "hilfe.faces_bekannt.satz2",
    "hilfe.faces_bekannt.satz3",
    "hilfe.faces_lernen.satz1", "hilfe.faces_lernen.satz2",
    "hilfe.faces_lernen.satz3",
    "hilfe.faces_unbekannt.satz1", "hilfe.faces_unbekannt.satz2",
    "hilfe.faces_qualitaet.satz1", "hilfe.faces_qualitaet.satz2",
    "hilfe.faces_lernlauf.satz1", "hilfe.faces_lernlauf.satz2",
    "hilfe.faces_lernlauf.satz3", "hilfe.faces_lernlauf.satz4",
    # ---- §8.1-Nachzuegler (Stufe 3): Markup-Prosa der Tranchen B/C ----
    "setupwiz.backend.system_satz", "setupwiz.fertig.wieder_satz",
    "system.sync.diagnose_satz", "system.sync.diagnose_kurz",
    "vision.kopf.einleitung", "vision.hinweis.modell_satz",
    "vision.hinweis.host_satz", "vision.hinweis.mess_satz",
    "vision.hinweis.kosten_satz", "vision.verb.key_ort",
    "vision.modell.leer_key", "vision.modell.leer_verbindung",
    "vision.modell.antwort_satz", "vision.prompt.eigen_satz",
    "vision.cloud.sendet_satz", "vision.test.stufen_satz",
    "visiontest.kopf.wege_satz", "visiontest.vision.einrichten_satz",
    "visionwizard.groesse.satz", "visionwizard.vorschlag.vergessen_satz",
    "visionwizard.vorschlag.satz",
    "personwizard.kopf.stark_satz", "personwizard.fertig.training_satz",
    "personwizard.kontrolle.schalter_satz",
    "personwizard.kontrolle.leer_satz", "personwizard.bestand.leer_satz",
    "personwizard.bestand.stark_satz", "personwizard.bestand.fremd_satz",
    "personwizard.bestand.fremd_erklaerung",
    "personwizard.modell.leer_satz", "personwizard.modell.material_satz",
})


def t_html(key, **kw):
    """Deklarierter HTML-Schluessel: liefert Markup, das der Aufrufer OHNE
    weiteres Escaping einbettet. Nicht deklarierte Schluessel sind ein
    Programmierfehler (laut, nicht leise)."""
    if key not in HTML_SCHLUESSEL:
        raise KeyError(f"t_html: '{key}' ist nicht als HTML-Schluessel deklariert")
    import html as _html
    w = _roh(key, aktive())
    if kw:
        try:
            return w.format(**{k: _html.escape(str(v), quote=True)
                               for k, v in kw.items()})
        except (KeyError, IndexError, ValueError):
            return w
    return w


def js_tabelle(praefix="js."):
    """Fuer das Seitenskelett: alle Schluessel mit dem js.-Praefix als
    json.dumps-fertiges dict (B3/B4 — Escaping loest json.dumps beim
    Einbetten als window.T). VERTRAG (Stufe 1): webui/app.js liest Texte
    AUSSCHLIESSLICH aus js.*-Schluesseln (TT() mit englischem Fallback),
    und jeder js.*-Schluessel wird von app.js benutzt — beide Richtungen
    prueft die Gate-Stufe Sprach-Deckung. Iteriert wird ueber die
    en-Referenz; fehlende Uebersetzungen fallen je Schluessel laut auf
    Englisch zurueck (_roh)."""
    code = aktive()
    return {k: _roh(k, code) for k in _lade(_STANDARD) if k.startswith(praefix)}
