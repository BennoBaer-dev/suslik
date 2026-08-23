#!/usr/bin/env python3
"""Referenz-Sync Master <-> Frigate (Plan v1.0 AP1).

Master = verify_data/refs/<Person>/*.jpg + refs_meta.jsonl (Herkunft, aktiv-Flag,
Tombstones). Frigate-Ablage = /opt/frigate/media/clips/faces/<Person>/.

  sync_refs.py status              # Diff beider Seiten + offene Entscheidungen
  sync_refs.py import [--dry-run]  # NEUE Frigate-Bilder -> Master (mit Gesichts-Gate;
                                   #   Tombstones werden NIE re-importiert)
  sync_refs.py export [--dry-run]  # aktive Master-Bilder, die Frigate fehlen -> HTTP-API:
                                   #   POST /api/faces/{name}/create (nur wenn die Person dort
                                   #   fehlt) + POST /api/faces/{name}/register (multipart,
                                   #   Feld "file"). NICHT POST /api/faces/{name} — den Endpunkt
                                   #   gibt es in Frigate 0.18 nicht (404, geprueft 05.08.).
                                   #   Der SSH/scp-Altweg ist seit 0.1.0.107 abgeloest
                                   #   (Invariante "nur API" + Shell-Injektion).
                                   #   --auswahl=<datei.json> = nur die dort gelisteten
                                   #   [[person, datei], …] (selektiver Sync, .133)
  sync_refs.py vorpruefung         # Vorpruefungs-Cache fuellen (nur neue/geaenderte Bilder),
                                   #   Grundlage der Auswahl-Seite "Review & sync"

Konfliktregel (Plan §AP1): in Frigate GELOESCHTE, im Master aktive Bilder werden NICHT
still re-exportiert — status meldet sie als offene Entscheidung (User loescht im Master
oder exportiert bewusst per --auch-extern-geloeschte).

abgleich() (.137) ist die reichere Sicht neben diff(): vier Klassen (in beiden · nur in
Frigate · nur bei uns uebertragbar · nur bei uns NICHT uebertragbar, letztere aufgeteilt
in extern geloescht / API-exportiert-umbenannt / von Frigate abgelehnt). Die Seite
"Review & sync" rendert daraus ihre Bilanz und die Aktionen je Klasse."""
import os, re, sys, json, time, urllib.parse, urllib.request, uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("VERIFY_DATA_DIR") or os.path.join(HERE, "verify_data")   # Container: /data
MASTER = os.path.join(DATA, "faces")
META = os.path.join(MASTER, "refs_meta.jsonl")
# SSH-Reste (LXC-Credentials, Remote-Faces-Pfad) mit 0.1.0.107 entfallen — der Export
# laeuft ueber die HTTP-API, s. api_upload(). Nichts hier braucht mehr Host-Zugang.


# Vertrag mit verifyd (.131): an DIESEM Marker erkennt der Dienst den
# Frigate-Erkennung-aus-Fall und zeigt dem Nutzer den Schalt-Hinweis im UI —
# nie ein zweites Literal streuen (QS-Ebenen-Regel).
FR_AUS_MARKER = "face recognition is disabled"
# .132: der Nutzer-Hinweis dazu — EINE Quelle, verifyd importiert ihn.
FR_AUS_HINWEIS = ("Frigate refused: its face recognition is switched off. To "
                  "write references to Frigate, enable face_recognition in "
                  "your Frigate config; importing FROM Frigate works without it.")
# Ergebnis-Bericht des letzten Export-Laufs (Diagnose-Paket, .132):
BERICHT = os.path.join(DATA, "state", "sync_export_bericht.json")
# .133 "Selektiver Sync" — drei Merker in state/, je EINE Quelle (Vertrag mit
# verifyd/routes.syncauswahl; nie ein zweites Literal streuen):
#   VORPRUEFUNG     Urteil je Bild, mit mtime gestempelt (Cache; nur neue oder
#                   geaenderte Bilder werden neu gerechnet),
#   VORPRUEF_STATUS Fortschritt des Hintergrund-Laufs fuer die Seite,
#   ABWAHL          bewusst abgewaehlte Bilder — eigener Merker, NICHT die
#                   refs_meta-Tombstones: ein Tombstone heisst "Bild ist weg",
#                   die Abwahl heisst "Bild bleibt, geht aber nicht nach Frigate".
VORPRUEFUNG = os.path.join(DATA, "state", "sync_vorpruefung.json")
VORPRUEF_STATUS = os.path.join(DATA, "state", "sync_vorpruefung_status.json")
ABWAHL = os.path.join(DATA, "state", "sync_abwahl.json")
# .137 "Ablehnungs-Gedaechtnis" — der vierte Merker, gleicher Vertrag wie ABWAHL:
#   ABLEHNUNGEN  {schluessel: {"fehler", "mtime", "ts", "art"}} — was FRIGATE
#                selbst je Bild abgelehnt hat. Ein Vorpruefungs-Urteil ist UNSER
#                Detektor und darf nie als Frigate-Ablehnung gemerkt werden.
#                mtime-gestempelt wie der Vorpruefungs-Cache: ein ausgetauschtes
#                Bild verliert seinen Merker von selbst. Wirkung: der AUTOMATIK-
#                Lauf ueberspringt Gemerktes still-gezaehlt (bericht
#                ['abgelehnt_n']), eine bewusste Auswahl versucht es trotzdem und
#                loescht den Merker bei Erfolg (Schleifen-Fix, Operator-Test
#                06.08.). WAS gemerkt wird, entscheidet _ablehnung_merken()
#                (.138 Panel-MUSS: ein globaler Frigate-Ausfall sperrte sonst den
#                ganzen Stapel dauerhaft aus):
#                  art='urteil' — 400 aus /register = deterministisches
#                                 Inhalts-Urteil ueber DIESES Bild, unbefristet;
#                  art='unklar' — 500 'could not process' kann Bild ODER
#                                 Frigate-Zustand sein -> verfaellt nach
#                                 ABLEHNUNG_UNKLAR_TTL_S und wird neu versucht;
#                  alles andere (Transport 408/413/429, /create-Fehler) sagt
#                  nichts ueber das Bild und wird NIE gemerkt. Eine erkannte
#                  WAND (3x gleicher Fehler) verwirft ihre Merker am Laufende.
ABLEHNUNGEN = os.path.join(DATA, "state", "sync_ablehnungen.json")
# Verfall der 'unklar'-Merker: lang genug, dass ein haengender Frigate-Zustand
# nicht bei jeder Runde neu angerannt wird, kurz genug, dass sich der Bestand
# nach einem Frigate-Neustart von selbst erholt (ein Wiederholungsversuch/Tag).
ABLEHNUNG_UNKLAR_TTL_S = 24 * 3600
# Protokoll-Vermerk 'ziel' der API-Aera. Das Praefix ist der BEWEIS, dass ein Bild
# ueber /register ging — und Frigate benennt dabei um (<Name>_<ts>.webp), womit der
# Dateiname fuer immer unvergleichbar wird. Eintraege OHNE dieses Praefix stammen aus
# der SSH-Aera (Dateiname blieb erhalten) und sind per Namen vergleichbar. EINE
# Quelle: cmd_export schreibt es, abgleich() liest es.
ZIEL_API = "api:"


class FrigateAntwortFehler(RuntimeError):
    """HTTP-Fehlerantwort der Frigate-API mit Code + Klartext-Detail — Basis der
    Export-Fehlerklassifizierung (.132: fatal vs. pro Bild). quelle = WELCHER
    Aufruf antwortete ('create'|'register', .138): nur ein register-Fehler ist
    ueberhaupt eine Aussage ueber das BILD — ein create-Fehler betrifft die
    Person und darf nie als Bild-Ablehnung gemerkt werden (Panel-Befund: er
    haette sonst ALLE Bilder der Person dauerhaft ausgesperrt)."""

    def __init__(self, code, detail, msg, quelle=""):
        super().__init__(msg)
        self.code = code
        self.detail = detail
        self.quelle = quelle


def _frigate():
    """Frigate-Basis-URL zur AUFRUF-Zeit: ENV zuerst (#18-Bruecke des Dienstes,
    CLI via source .env), sonst FALLBACK auf die gespeicherte UI-Config
    (<data>/config/config.json — .132, carlsmith-Lehre: ein docker-exec-
    Diagnoselauf hat die Dienst-Umgebung NICHT und soll trotzdem laufen)."""
    url = os.environ.get("FRIGATE_URL", "")
    if url:
        return url
    try:
        with open(os.path.join(DATA, "config", "config.json")) as f:
            return str(json.load(f).get("frigate_url") or "")
    except Exception:
        return ""
PROGRESS = os.path.join(DATA, "state", "sync_progress.json")   # Fortschritt fuer die UI (X von Y)


def _progress(**d):
    """Fortschritt atomar in eine Statusdatei schreiben; die UI pollt sie (/sync_status)."""
    try:
        os.makedirs(os.path.dirname(PROGRESS), exist_ok=True)
        tmp = PROGRESS + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"ts": round(time.time(), 1), **d}, f)
        os.replace(tmp, PROGRESS)
    except Exception:
        pass


def schluessel(person, datei):
    """Der EINE Schluessel fuer Vorpruefungs-Cache und Abwahl-Gedaechtnis:
    '<Person>/<Datei>'. Vertrag mit verifyd und routes/syncauswahl.py — beide
    bauen ihn NIE selbst zusammen (QS-Ebenen-Regel: keine Streu-Literale)."""
    return f"{person}/{datei}"


def _json_lesen(pfad, standard):
    try:
        with open(pfad, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, type(standard)) else standard
    except Exception:
        return standard


def _json_schreiben(pfad, obj):
    """Merker atomar ablegen (tmp + os.replace). Ein halb geschriebener Merker
    waere beim naechsten Lesen kaputt — und eine vergessene Abwahl schickt
    genau die Bilder nach Frigate, die der Nutzer bewusst zurueckgehalten hat."""
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    tmp = f"{pfad}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, pfad)


def abwahl_lesen():
    """-> {schluessel: {"ts", "person", "datei"}} der bewusst abgewaehlten Bilder."""
    return _json_lesen(ABWAHL, {})


def abwahl_setzen(paare, an=True):
    """paare = [(person, datei), …] abwaehlen (an=True) oder zurueckholen.
    -> Zahl der WIRKLICH geaenderten Eintraege (Doppelklicks zaehlen nicht)."""
    d = abwahl_lesen()
    n = 0
    for person, datei in paare:
        k = schluessel(person, datei)
        if an:
            if k not in d:
                n += 1
            d[k] = {"ts": round(time.time(), 1), "person": person, "datei": datei}
        elif d.pop(k, None) is not None:
            n += 1
    _json_schreiben(ABWAHL, d)
    return n


def ablehnungen_lesen():
    """-> {schluessel: {"fehler", "mtime", "ts"}} — ROH, auch veraltete Eintraege."""
    return _json_lesen(ABLEHNUNGEN, {})


def ablehnungen_aktiv(cache=None):
    """Nur die Merker, deren Bild seit der Ablehnung UNVERAENDERT ist. Gleiche
    Invalidierung wie beim Vorpruefungs-Cache: wer ein Referenzbild austauscht,
    hat ein anderes Bild — das verdient einen neuen Versuch bei Frigate.
    .138: 'unklar'-Merker (500 'could not process' — kann Bild ODER Frigate-
    Zustand sein) verfallen zusaetzlich nach ABLEHNUNG_UNKLAR_TTL_S; Alt-
    Eintraege ohne art-Feld werden nach ihrem Fehlertext eingestuft."""
    cache = ablehnungen_lesen() if cache is None else cache
    aus = {}
    for k, e in cache.items():
        person, _, datei = str(k).partition("/")
        if not (person and datei) or not isinstance(e, dict):
            continue
        if e.get("mtime") != _mtime(os.path.join(MASTER, person, datei)):
            continue
        art = e.get("art") or ("unklar" if "could not process"
                               in str(e.get("fehler") or "").lower() else "urteil")
        if art == "unklar" and time.time() - float(e.get("ts") or 0) > ABLEHNUNG_UNKLAR_TTL_S:
            continue
        aus[k] = e
    return aus


def _ablehnungen_mischen(neu=None, weg=()):
    """Merker unter flock MISCHEN statt die Datei zu ersetzen (Lehre .134: zwei
    parallele Laeufe verloren sich sonst gegenseitig ihre Eintraege). neu = neue
    Ablehnungen, weg = Schluessel, deren Bild gerade doch durchging."""
    if not neu and not weg:
        return
    import fcntl
    os.makedirs(os.path.dirname(ABLEHNUNGEN), exist_ok=True)
    with open(ABLEHNUNGEN + ".lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            stand = ablehnungen_lesen()
            stand.update(neu or {})
            for k in weg:
                stand.pop(k, None)
            _json_schreiben(ABLEHNUNGEN, stand)
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def vorpruefung_lesen():
    """-> {schluessel: {"ok": bool, "grund": str, "mtime": float}}."""
    return _json_lesen(VORPRUEFUNG, {})


def vorpruefung_status():
    """-> {"ts", "laeuft", "gesamt", "fertig", "fehler"} des Hintergrund-Laufs."""
    return _json_lesen(VORPRUEF_STATUS, {})


def _vp_status(**d):
    try:
        _json_schreiben(VORPRUEF_STATUS, {"ts": round(time.time(), 1), **d})
    except Exception:
        pass


def _mtime(pfad):
    try:
        return round(os.path.getmtime(pfad), 3)
    except OSError:
        return None


def vorpruefung_offen(kandidaten, cache=None):
    """Welche Kandidaten haben (noch) KEIN gueltiges Urteil? Gueltig = Eintrag da
    UND mtime unveraendert — wird ein Referenzbild ersetzt, faellt sein Urteil
    von selbst weg (Cache-Invalidierung je Datei, kein globales Verfallsdatum)."""
    cache = vorpruefung_lesen() if cache is None else cache
    offen = []
    for person, datei in kandidaten:
        e = cache.get(schluessel(person, datei))
        if not e or e.get("mtime") != _mtime(os.path.join(MASTER, person, datei)):
            offen.append((person, datei))
    return offen


ERLAUBTE_ENDUNGEN = (".jpg", ".jpeg", ".png", ".webp")
# Permissiv und UNICODE-bewusst: echte Namen wie "Müller" oder "Anna-Lena" muessen durch,
# sonst faellt ein legitimer Import STILL aus (Fehlerklasse C). Verboten sind nur die Zeichen,
# die Pfade aufbrechen. Die eigentliche Sicherheit macht das realpath-Containment darunter.
# Bis 03.08. stand hier nur "alles ausser / \\ NUL" — permissiver als JEDE Konsumenten-
# Pruefung. Folge (Sweep-Befund): ein Frigate-Gesicht "Anna.B"/"Tim+Bo" wurde importiert,
# war auf der Known-Seite sichtbar, aber unbedienbar (Thumbnails 404, Loeschen
# "ungueltiger Pfad"). Jetzt gilt derselbe Vertrag wie fuer die Verbraucher; was nicht
# passt, wird LAUT uebersprungen (Zeile im Import-Log) statt still unbrauchbar angelegt.
from core.registry import PERSON_RE as _PERSON_RE
_NAME_OK = re.compile(rf"^{_PERSON_RE}$", re.UNICODE)


def sicheres_ziel(person, datei):
    """Schreibziel fuer ein Referenzbild bauen — oder (None, Grund), wenn es unsicher ist.

    Die Namen kommen aus /api/faces der GEGENSTELLE und sind damit Fremdeingabe: die
    Frigate-URL ist ueber POST /sync_import frei setzbar. Ohne Pruefung landet person='../../app'
    per os.path.join ausserhalb von MASTER — im Container als root, mit /app/verifyd.py als
    Ziel (Codeausfuehrung beim naechsten Neustart). Zwei Schichten, absichtlich redundant:
    1. Namens-/Endungs-Whitelist (faengt das Offensichtliche und haelt den Master sauber),
    2. realpath-Containment (die eigentliche Garantie — greift auch bei Symlinks und bei
       allem, woran die Regex nicht gedacht hat)."""
    if not person or not datei:
        return None, "leerer Name"
    if person in (".", "..") or datei in (".", ".."):
        return None, "Punkt-Eintrag"
    if not _NAME_OK.match(person) or not _NAME_OK.match(datei):
        return None, "unerlaubte Zeichen im Namen"
    if not datei.lower().endswith(ERLAUBTE_ENDUNGEN):
        return None, "unerlaubte Dateiendung"
    ziel = os.path.join(MASTER, person, datei)
    basis = os.path.realpath(MASTER)
    echt = os.path.realpath(ziel)
    if echt != basis and not echt.startswith(basis + os.sep):
        return None, "Pfad zeigt aus dem Master heraus"
    return ziel, ""


def lade_meta():
    aktiv, tomb = {}, set()
    if os.path.exists(META):
        for l in open(META):
            try:
                d = json.loads(l)
            except Exception:
                continue
            key = (d["person"], d["datei"])
            if d.get("aktiv", True):
                aktiv[key] = d
                tomb.discard(key)
            else:
                tomb.add(key)
                aktiv.pop(key, None)
    return aktiv, tomb


def meta_append(**d):
    with open(META, "a") as f:
        f.write(json.dumps({"ts": round(time.time(), 1), **d}, ensure_ascii=False) + "\n")
        f.flush()


def master_stand():
    out = {}
    for p in sorted(os.listdir(MASTER)):
        d = os.path.join(MASTER, p)
        if os.path.isdir(d):
            out[p] = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    return out


def frigate_stand():
    with urllib.request.urlopen(f"{_frigate()}/api/faces", timeout=20) as r:
        d = json.load(r)
    return {k: sorted(v) for k, v in d.items() if k != "train"}


def frigate_fr_status(timeout=5):
    """Laeuft Frigates EIGENE Gesichtserkennung gerade? LIVE aus
    GET /api/config gelesen (face_recognition.enabled, an der laufenden 0.18
    verifiziert) — nie aus einem gespeicherten Alt-Status. Anlass: im Operator-
    Test 06.08. las sich ein Stunden alter Sync-Status wie der Live-Zustand.
    -> (True|False|None, detail); None = nicht ermittelbar, detail traegt dann
    den Klartext-Grund (die Seite sagt 'unknown' statt zu raten)."""
    basis = _frigate().rstrip("/")
    if not basis:
        return None, "no Frigate URL configured"
    try:
        with urllib.request.urlopen(f"{basis}/api/config", timeout=timeout) as r:
            cfg = json.load(r)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    fr = cfg.get("face_recognition")
    if not isinstance(fr, dict) or "enabled" not in fr:
        return None, "Frigate's config has no face_recognition.enabled field"
    return bool(fr.get("enabled")), ""


def diff():
    """-> (nur_frigate, nur_master, extern_geloescht). EXPORT-DEDUP LAEUFT UEBERS
    PROTOKOLL, nicht ueber Frigate-Dateinamen (Live-Befund 05.08. am echten
    0.18.0: /register benennt JEDES Bild in <Name>_<timestamp>.webp um und
    verarbeitet asynchron — ein Namens-Abgleich saehe Exportiertes ewig als
    'fehlend' und wuerde es bei jedem Lauf erneut hochpumpen; mit dem alten
    SSH-Weg blieben die Namen erhalten, daher trug der Abgleich frueher).
    Ein Master-Bild mit aktivem export-Protokolleintrag ist deshalb NIE wieder
    Export-Kandidat. Bekannte Grenze (Design-Entscheid offen): die von Frigate
    umbenannten Exporte erscheinen in nur_frigate als Import-Kandidaten —
    cmd_import ist manuell, nichts laeuft von allein."""
    m, f = master_stand(), frigate_stand()
    aktiv, tomb = lade_meta()
    nur_frigate, nur_master, extern_geloescht = [], [], []
    for p in sorted(set(m) | set(f)):
        ms, fs = set(m.get(p, [])), set(f.get(p, []))
        for datei in sorted(fs - ms):
            if (p, datei) not in tomb:
                nur_frigate.append((p, datei))
        for datei in sorted(ms - fs):
            # Master-Bild fehlt in Frigate: nie exportiert (enrollment/upload) ->
            # Kandidat · schon exportiert -> Frigate fuehrt es unter eigenem
            # Namen, NIE erneut senden · Herkunft frigate-import -> dort geloescht.
            herkunft = (aktiv.get((p, datei)) or {}).get("herkunft", "?")
            if herkunft.startswith("frigate-import"):
                extern_geloescht.append((p, datei))
            elif herkunft == "vorrat":
                # Vorrats-Referenzen (bauplan_vorrat.md B4, W1.15): NIE
                # exportieren — ihre Wahrheit ist der Embedding-Beiwert, die
                # kleine Bilddatei kann Frigates eigene Anlern-Pipeline
                # gemessen oft nicht detektieren (28/40 tot). Bewusst KEIN
                # Kandidat, bleibt lokal (Registrieren-nach-Schaltern).
                pass
            elif herkunft != "export":
                nur_master.append((p, datei))
    return nur_frigate, nur_master, extern_geloescht


# Grund-Schluessel der Klasse D1 (in Frigate geloescht). KEIN Anzeigetext — die
# englischen Saetze macht der Renderer; hier steht nur, WORAUS der Befund folgt.
D1_IMPORT = "frigate-import"        # kam aus Frigate, dort inzwischen geloescht
D1_EXPORT = "export"                # von uns unter DIESEM Namen geschickt, dort weg


def abgleich():
    """Vier-Klassen-Abgleich Master <-> Frigate (.137, User-Vorgabe 06.08.: "was
    haben wir in Frigate, was nicht, was koennen wir uebertragen und was nicht").
    diff() bleibt UNVERAENDERT daneben stehen (drei Rueckgaben, alte Aufrufer) —
    diese Funktion ist die reichere Sicht, nicht ihr Ersatz.

    Anlass (Operator-Test 06.08.): 19 in Frigate von Hand geloeschte Bilder
    tauchten NIRGENDS auf. 14 davon trugen Herkunft 'export' und wurden von
    diff() pauschal uebersprungen (seit .128 dedupt der Export ueber das
    Protokoll), 5 waren API-Exporte, die Frigate umbenannt hat. Beides ist jetzt
    sichtbar und unterscheidbar — und nichts davon laeuft automatisch: eine
    Loeschung in Frigate kann Absicht sein (Konfliktregel Plan §AP1).

    -> dict, die Klassen sind DISJUNKT und decken jedes Master-Bild genau einmal:
       gesamt      == len(in_beiden) + len(kandidaten) + len(geloescht)
                      + len(api_export) + len(abgewaehlt) + len(vorrat_lokal)
      gesamt       Zahl aller Master-Referenzbilder (die ehrliche Bezugsgroesse),
      in_beiden    [(person, datei)] Name auf BEIDEN Seiten (A),
      je_person    {person: {"gesamt", "beide", "frigate"}} fuer die Zeilen je
                   Person (frigate = Zahl der Bilder, die Frigate dort fuehrt),
      nur_frigate  [(person, datei)] nur in Frigate = Import-Kandidaten (B),
      kandidaten   [(person, datei)] nur bei uns und uebertragbar (C),
      abgelehnt    {schluessel: merker} gemerkte FRIGATE-Ablehnungen (D3) —
                   Teilmenge von kandidaten, denn sie bleiben anklickbar,
      geloescht    [(person, datei, grund)] in Frigate geloescht, Name war
                   vergleichbar -> Entscheidungsfall (D1),
      api_export   [(person, datei)] frueher per API geschickt, Frigate fuehrt
                   sie unter eigenem Namen -> Gegenstelle unpruefbar (D2),
      abgewaehlt   [(person, datei)] bewusst zurueckgehalten (N),
      abgewaehlt_unpruefbar  Teilmenge von abgewaehlt: die Abwahl traf ein D1-/
                   D2-Bild ('respect the deletion'). cmd_vorpruefung erreicht
                   solche Bilder NIE (diff() ueberspringt die Herkuenfte) —
                   der Handler darf sie deshalb nicht als 'offen' zaehlen,
                   sonst startet der Vorpruefungs-Subprozess bei jedem
                   Seitenaufruf neu (.138 Panel-Befund, QS-Klasse K3:
                   Erzeuger- und Verbrauchermenge liefen auseinander)."""
    m, f = master_stand(), frigate_stand()
    aktiv, tomb = lade_meta()
    ab = abwahl_lesen()
    abl = ablehnungen_aktiv()
    erg = {"gesamt": 0, "in_beiden": [], "je_person": {}, "nur_frigate": [],
           "kandidaten": [], "abgelehnt": {}, "geloescht": [], "api_export": [],
           "abgewaehlt": [], "abgewaehlt_unpruefbar": [],
           # bauplan_vorrat.md B4 (Klassen-Invariante unten erweitert):
           # Vorrats-Referenzen sind NIE Export-Kandidaten — stuenden sie in
           # 'kandidaten', liefe die Erzeuger-Menge (diff() schliesst sie aus)
           # gegen die Verbraucher-Menge auseinander, exakt die K3-Klasse aus
           # dem .138-Panel-Befund.
           "vorrat_lokal": []}
    for p in sorted(set(m) | set(f)):
        ms, fs = set(m.get(p, [])), set(f.get(p, []))
        for datei in sorted(fs - ms):
            if (p, datei) not in tomb:
                erg["nur_frigate"].append((p, datei))
        beide = 0
        for datei in sorted(ms):
            erg["gesamt"] += 1
            if datei in fs:                       # A: derselbe Name auf beiden Seiten
                beide += 1
                erg["in_beiden"].append((p, datei))
                continue
            e = aktiv.get((p, datei)) or {}
            herkunft = str(e.get("herkunft") or "?")
            if herkunft.startswith("frigate-import"):
                klasse, grund = "geloescht", D1_IMPORT
            elif herkunft == "export":
                # Namensvergleichbarkeit AUS DEM PROTOKOLL: nur die SSH-Aera hat
                # den Dateinamen drueben erhalten. Ohne api:-Ziel heisst "Name
                # fehlt" also wirklich "extern geloescht" (D1), mit api:-Ziel
                # heisst es gar nichts (D2) — Frigate fuehrt es umbenannt.
                if str(e.get("ziel") or "").startswith(ZIEL_API):
                    klasse, grund = "api_export", None
                else:
                    klasse, grund = "geloescht", D1_EXPORT
            elif herkunft == "vorrat":            # V: Beiwert-Referenz, bleibt lokal
                klasse, grund = "vorrat_lokal", None
            else:                                 # C: nie geschickt -> uebertragbar
                klasse, grund = "kandidaten", None
            k = schluessel(p, datei)
            if k in ab:                           # N: bewusste Entscheidung schlaegt alles
                erg["abgewaehlt"].append((p, datei))
                if klasse != "kandidaten":
                    erg["abgewaehlt_unpruefbar"].append((p, datei))
                continue
            if klasse == "geloescht":
                erg["geloescht"].append((p, datei, grund))
            elif klasse == "api_export":
                erg["api_export"].append((p, datei))
            elif klasse == "vorrat_lokal":
                erg["vorrat_lokal"].append((p, datei))
            else:
                erg["kandidaten"].append((p, datei))
                if k in abl:
                    erg["abgelehnt"][k] = abl[k]
        erg["je_person"][p] = {"gesamt": len(ms), "beide": beide, "frigate": len(fs)}
    return erg


# Grund-Marker der offer-again-Journalzeile. refs_meta.jsonl hat ZWEI Leser
# (lade_meta hier, anlernen.aehnliche_unbekannte dort) — der Marker ist der
# Vertrag, an dem der zweite Leser die Zeile IGNORIERT: das Bild liegt weiter
# im Master, sein Anlern-Gesicht bleibt zugeordnet (.138 Panel-Befund: die
# Zeile gab das Gesicht sonst wieder als Unbekannt-Vorschlag frei, Weg zum
# exakten Duplikat-Anlernen).
GRUND_WIEDER_ANBIETEN = "offer-again"


def wieder_anbieten(paare):
    """"Nochmal anbieten" (.137): den aktiven Protokoll-Eintrag eines Bildes auf
    aktiv=False setzen, damit es wieder normaler Export-Kandidat wird. JOURNAL-
    Prinzip — refs_meta.jsonl wird nur ANGEHAENGT, nie umgeschrieben; die
    Geschichte des Bildes bleibt lesbar. -> Zahl der geschriebenen Zeilen.

    Nur fuer Bilder, die im Master WIRKLICH liegen (sonst waere die Zeile ein
    Tombstone ohne Datei). Wirkung der aktiv=False-Zeile: fuer lade_meta/diff/
    abgleich wird das Bild wieder Kandidat — und der NAECHSTE Sync (auch der
    automatische nach einem Enrollment) schickt es; die Seite sagt das am Knopf
    dazu. anlernen.aehnliche_unbekannte ueberspringt die Zeile am
    GRUND_WIEDER_ANBIETEN-Marker (.138: sie ist KEINE Loeschung, das Anlern-
    Gesicht bleibt zugeordnet). Ein erfolgreicher Re-Export haengt mit seinem
    aktiv=True-Eintrag alles zurueck."""
    aktiv, _t = lade_meta()
    n = 0
    for person, datei in paare:
        if not os.path.isfile(os.path.join(MASTER, person, datei)):
            continue
        alt = aktiv.get((person, datei))
        if alt is None:                       # schon Kandidat — nichts zu tun
            continue
        meta_append(person=person, datei=datei, herkunft=alt.get("herkunft", "?"),
                    aktiv=False, grund=GRUND_WIEDER_ANBIETEN)
        n += 1
    return n


def cmd_status():
    nf, nm, eg = diff()
    print(f"Neu in Frigate (Import-Kandidaten): {len(nf)}")
    for p, d in nf[:10]:
        print(f"  + {p}/{d}")
    print(f"Nur im Master, nie exportiert (Export-Kandidaten): {len(nm)}")
    for p, d in nm[:10]:
        print(f"  > {p}/{d}")
    print(f"EXTERN GELOESCHT (in Frigate weg, im Master aktiv) — Entscheidung offen: {len(eg)}")
    for p, d in eg[:10]:
        print(f"  ! {p}/{d}  (Master loeschen ODER bewusst re-exportieren)")
    # Ehrliche Zusatzzeile (nie stilles Verschwinden): schon Exportiertes fuehrt
    # Frigate 0.18 unter EIGENEM Namen (<Name>_<ts>.webp) — es fehlt im
    # Namens-Abgleich, ist aber KEIN Kandidat und KEIN Verlust.
    aktiv, _t = lade_meta()
    m, f = master_stand(), frigate_stand()
    n_exp = sum(1 for (p, d), e in aktiv.items()
                if e.get("herkunft") == "export"
                and d in set(m.get(p, [])) and d not in set(f.get(p, [])))
    if n_exp:
        print(f"Bereits exportiert, von Frigate unter eigenem Namen gefuehrt: {n_exp}")
    # .133: bewusst Abgewaehltes ist KEIN Kandidat mehr — das gehoert sichtbar in
    # die Bilanz, sonst wundert man sich ueber die Differenz zum Export-Ergebnis.
    ab = abwahl_lesen()
    n_ab = sum(1 for p, d in nm if schluessel(p, d) in ab)
    if n_ab:
        print(f"Davon bewusst abgewaehlt (gehen NICHT nach Frigate): {n_ab}")
    # .137: gemerkte FRIGATE-Ablehnungen — der Auto-Export laesst sie aus, die
    # Auswahl-Seite zeigt sie rot und anklickbar. Nie still unter den Tisch.
    n_abl = len(ablehnungen_aktiv())
    if n_abl:
        print(f"Von Frigate abgelehnt (gemerkt, Auto-Export laesst sie aus): {n_abl}")
    if not (nf or nm or eg):
        print("=> synchron.")


def cmd_import(dry):
    # Frigate-Referenzbilder sind bereits fertige Gesichts-Crops -> KEIN CPU-Face-Gate hier. Das war
    # redundant: nach dem Import rechnet der Dienst alle Embeddings ohnehin neu, und ZWAR auf der GPU
    # (refcache-Neuaufbau). Hier nur schnell herunterladen; die Rechenarbeit macht die GPU.
    nf, _, _ = diff()
    if not nf:
        _progress(phase="done", total=0, done=0, ok=0, gate=0)
        print("nichts zu importieren.")
        return
    total = len(nf)
    n_ok = n_dl = n_bad = 0
    for i, (p, datei) in enumerate(nf):
        _progress(phase="import", total=total, done=i, current=p, ok=n_ok, gate=n_dl)
        ziel, grund = sicheres_ziel(p, datei)      # Fremdeingabe: NIE ungeprueft in einen Pfad
        if ziel is None:
            n_bad += 1
            print(f"  ABGELEHNT: {p!r}/{datei!r} ({grund}) -> uebersprungen")
            continue
        if dry:
            n_ok += 1
            print(f"  [dry] importiere {p}/{datei}")
            continue
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        try:
            with urllib.request.urlopen(f"{_frigate()}/clips/faces/{urllib.parse.quote(p)}/{urllib.parse.quote(datei)}",
                                        timeout=20) as r:
                data = r.read()
            with open(ziel, "wb") as f:
                f.write(data)
        except Exception as e:
            # KEIN Tombstone: ein Timeout/500 ist transient, ein Tombstone waere permanent und
            # sperrte das Bild fuer alle kuenftigen Importe aus (lade_meta -> tomb). Nur zaehlen,
            # der naechste Lauf versucht es erneut.
            n_dl += 1
            print(f"  DOWNLOAD-FEHLER: {p}/{datei} ({str(e)[:40]}) -> uebersprungen (kein Tombstone, Retry beim naechsten Lauf)")
            continue
        n_ok += 1
        meta_append(person=p, datei=datei, herkunft="frigate-import", aktiv=True)
        print(f"  importiert: {p}/{datei}")
    _progress(phase="done", total=total, done=total, ok=n_ok, gate=n_dl, abgelehnt=n_bad)
    msg = f"=> {n_ok} importiert{' (dry)' if dry else ''}, {n_dl} Download-Fehler"
    if n_bad:
        msg += f", {n_bad} ABGELEHNT (unsichere Namen)"     # laut, nicht still
    print(msg)


# INVARIANTE: FRIGATE_FACES_API   (Marke: CLAUDE.md "Frigate-Zugriff: NUR ueber die HTTP-API")
def api_upload(person, datei, quelle, person_existiert=None):
    """Referenzbild ueber die Frigate-HTTP-API hochladen (Frigate 0.18.0, Endpunkte
    aus der OpenAPI der LAUFENDEN Instanz verifiziert, 05.08. — der fruehere
    POST /api/faces/{name} existiert dort NICHT, 404):
      1. unbekannter Name -> POST /api/faces/{name}/create (legt den Namen an),
      2. Bild             -> POST /api/faces/{name}/register (multipart, Feld `file`).
    person_existiert: vom Aufrufer gereichter Ist-Stand (spart je Datei einen
    /api/faces-Abruf); None = selbst nachschauen.

    WICHTIG: Frigate verweigert JEDE Faces-Mutation mit 400 'Face recognition is
    not enabled.', solange die hauseigene Gesichtserkennung aus ist — das wird
    hier als klarer Fehlertext gemeldet, nie als nackter HTTP-Fehler.

    Loest den SSH/scp-Altweg ab (CLAUDE.md-Invariante 'Frigate NUR ueber die
    HTTP-API'; Sicherheits-Fix Sweep 03.08.: der alte Weg interpolierte den
    Personen-Namen in eine Remote-Shell-Zeile — ueber die API ist der Name ein
    URL-Segment (quote) und ein Formularfeld, keine Shell im Spiel)."""
    if not _frigate():
        raise RuntimeError("FRIGATE_URL fehlt — Export ueber die API nicht moeglich")
    basis = _frigate().rstrip("/")
    pq = urllib.parse.quote(person, safe="")

    def _lesen(r):
        if r.status not in (200, 201):
            raise RuntimeError(f"Frigate-API antwortete HTTP {r.status}")
        return r.read()

    def _mutation(req, stelle):
        # stelle = 'create'|'register' wandert in den Fehler (.138): nur ein
        # register-Fehler ist eine Aussage ueber das Bild (Merker-Entscheid).
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return _lesen(r)
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read()).get("message", "")
            except Exception:
                pass
            if "not enabled" in detail.lower():
                raise FrigateAntwortFehler(
                    e.code, detail,
                    "Frigate refuses face changes: its own " + FR_AUS_MARKER
                    + " (face_recognition.enabled: false). Enable it in "
                    "Frigate to use the sync, or leave the sync off.",
                    quelle=stelle) from e
            raise FrigateAntwortFehler(
                e.code, detail,
                f"Frigate-API HTTP {e.code}: {detail or e.reason}",
                quelle=stelle) from e

    if person_existiert is None:
        person_existiert = person in frigate_stand()
    if not person_existiert:
        _mutation(urllib.request.Request(f"{basis}/api/faces/{pq}/create",
                                         data=b"", method="POST"), "create")
    grenze = uuid.uuid4().hex
    inhalt = open(quelle, "rb").read()
    typ = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
           "webp": "image/webp"}.get(datei.rsplit(".", 1)[-1].lower(), "application/octet-stream")
    body = (f"--{grenze}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{os.path.basename(datei)}\"\r\nContent-Type: {typ}\r\n\r\n").encode() \
        + inhalt + f"\r\n--{grenze}--\r\n".encode()
    _mutation(urllib.request.Request(
        f"{basis}/api/faces/{pq}/register",
        data=body, headers={"Content-Type": f"multipart/form-data; boundary={grenze}"}),
        "register")
    # INVARIANTE-ENDE: FRIGATE_FACES_API


def _fehler_einstufen(e):
    """Export-Fehler einordnen (.132, carlsmith-Lehre 'alles abfangen'):
    -> ('fatal'|'bild', kurztext).
      fatal = trifft zwangslaeufig JEDES Bild (Erkennung aus, Auth, Endpunkt
              fehlt, Verbindung/SSL/Timeout, Unerwartetes) -> sofort stoppen,
              nie 135x dieselbe Wand anrennen;
      bild  = Einzelfall (Inhalts-Ablehnung wie 'No face was detected',
              Quelldatei fehlt/unlesbar) -> ueberspringen, zaehlen, weiter."""
    if isinstance(e, FrigateAntwortFehler):
        if FR_AUS_MARKER in str(e):
            return "fatal", str(e)
        if e.code in (401, 403, 404, 405):
            return "fatal", f"HTTP {e.code}: {e.detail or 'no detail'}"
        if 500 <= e.code < 600:
            if "could not process request" in (e.detail or "").lower():
                # User-Realfall 06.08. + beta2-Quelle (embeddings/maintainer.py
                # _handle_request): dieser 500 wird von Frigate JE ANFRAGE gefangen,
                # der Prozess lebt weiter — z.B. kaputte Detektor-Box -> leerer
                # Zuschnitt -> imencode-Assert bei EINEM Bild. Also Bild-Fehler:
                # ueberspringen und weiter, nie den ganzen Lauf stoppen; eine echte
                # Dauerwand meldet die Wand-Wache.
                return "bild", f"HTTP {e.code} (Frigate could not process this image): {e.detail}"
            return "fatal", f"HTTP {e.code} (Frigate-side error): {e.detail or 'no detail'}"
        return "bild", f"HTTP {e.code}: {e.detail or 'no detail'}"
    if isinstance(e, (FileNotFoundError, IsADirectoryError, PermissionError)):
        return "bild", f"{type(e).__name__}: {e}"
    return "fatal", f"{type(e).__name__}: {e}"


def _ablehnung_merken(e):
    """Darf DIESER Fehler ins Ablehnungs-Gedaechtnis? -> ''|'urteil'|'unklar'
    (.138 Panel-MUSS: vorher wanderte JEDER nicht-fatale FrigateAntwortFehler in
    den Merker — ein globaler Frigate-Ausfall sperrte damit den ganzen Stapel
    dauerhaft aus, weil Referenzbilder ihre mtime nie aendern).
      'urteil' = 400 aus /register: Frigates deterministisches Inhalts-Urteil
                 ueber DIESES Bild ('No face was detected.') -> unbefristet;
      'unklar' = 500 'could not process' aus /register: kann ein kaputter
                 Zuschnitt DIESES Bildes sein ODER ein kranker Frigate-Zustand
                 (Embeddings-Prozess weg — dieselbe Antwort fuer jede Anfrage)
                 -> gemerkt, aber mit Verfall (ABLEHNUNG_UNKLAR_TTL_S);
      ''       = alles andere sagt nichts ueber das Bild: /create-Fehler
                 (betrifft die Person), Transportcodes (408/413/429), lokale
                 Datei-Fehler, unsere Vorpruefung."""
    if not isinstance(e, FrigateAntwortFehler) or getattr(e, "quelle", "") != "register":
        return ""
    if e.code == 400:
        return "urteil"
    if 500 <= e.code < 600 and "could not process request" in (e.detail or "").lower():
        return "unklar"
    return ""


_VORPRUEFER = None


def _gesicht_pruefen(pfad):
    """Vorpruefung analog Frigates register (.132, User-Entscheid): Frigate
    laesst jeden Upload durch SEINEN Gesichtsdetektor (beta2 face.py, Schwelle
    0.5) und lehnt sonst mit 'No face was detected.' ab. Wir pruefen vorab mit
    UNSEREM Detektor (buffalo_l/SCRFD, CPU, nur Detektions-Modul) und schicken
    nur, was bestehen duerfte — anderes Modell, kein identisches Urteil,
    Frigates Antwort bleibt die Wahrheit (der Bild-Fehlerpfad faengt
    Rest-Ablehnungen weiter ab). Detektor-Ladefehler = fail-open mit Ansage
    (die Vorpruefung ist Optimierung, nie Blocker). -> (True, '')/(False, grund)."""
    global _VORPRUEFER
    if _VORPRUEFER is None:
        try:
            import onnxruntime as ort
            ort.set_default_logger_severity(3)
            from insightface.app import FaceAnalysis
            app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"],
                               allowed_modules=["detection"])
            app.prepare(ctx_id=-1, det_size=(320, 320))
            # Thread-Kappung (#21) wie Embedder._to_backend auf cpu: die prepare()-Session
            # kaeme sonst mit ungekapptem Default-Pool (hardware_concurrency des Wirts).
            # Ersatz NACH prepare() aus der zentralen Quelle. EIGENER try (Widerleger
            # 11.08.): die Kappung ist Optimierung — scheitert sie, laeuft der Vorpruefer
            # UNGEKAPPT weiter statt sich ganz abzuschalten (das umgebende except wuerde
            # sonst jede Vorpruefung opfern und unnoetige Frigate-Ablehnungen einkaufen).
            try:
                from face_audit import _ort_session
                for _model in app.models.values():
                    _s = _ort_session("cpu", None, _model.model_file)
                    _model.session = _s
                    _model.input_name = _s.get_inputs()[0].name
                    _model.output_names = [o.name for o in _s.get_outputs()]
            except Exception as _e:
                print(f"  (Vorpruefung ungekappt — Session-Ersatz scheiterte: "
                      f"{type(_e).__name__}: {_e})", file=sys.stderr)
            _VORPRUEFER = app
        except Exception as e:
            print(f"  (Vorpruefung ohne Detektor — fail-open: {type(e).__name__}: {e})",
                  file=sys.stderr)
            _VORPRUEFER = "aus"
    if _VORPRUEFER == "aus":
        return True, ""
    try:
        import cv2
        img = cv2.imread(pfad)
        if img is None:
            return False, "unreadable image file"
        gesichter = _VORPRUEFER.get(img)
        if not gesichter:
            return False, "no face detectable (Frigate would reject it)"
        return True, ""
    except Exception:
        # Einzelfehler: fail-open, Frigate urteilt. Sentinel statt leerem Grund
        # (.134 Hinweis-Fix): ein fail-open-Urteil darf NIE als 'bestanden'
        # in den Cache einfrieren.
        return True, "__failopen__"


def _pruefen_gecacht(person, datei, cache, neu=None):
    """Vorpruefungs-Urteil je Bild AUS dem Cache, wenn die Datei seit der Messung
    unveraendert ist, sonst frisch gerechnet (.133). Frisch Gerechnetes landet im
    neu-Dict des AUFRUFERS (.134 Review-SOLL: nie mehr die ganze Cache-Datei
    zurueckschreiben — _cache_mischen mischt unter Lock, parallele Laeufe
    verlieren einander nichts mehr). Fail-open-Urteile (Detektor nicht ladbar,
    Einzelfehler) werden NIE gemerkt."""
    quelle = os.path.join(MASTER, person, datei)
    k = schluessel(person, datei)
    mt = _mtime(quelle)
    alt = cache.get(k) or (neu or {}).get(k)
    if alt and mt is not None and alt.get("mtime") == mt:
        return bool(alt.get("ok", True)), str(alt.get("grund") or "")
    ok_bild, grund = _gesicht_pruefen(quelle)
    if grund == "__failopen__":
        return True, ""
    if _VORPRUEFER != "aus" and mt is not None and neu is not None:
        neu[k] = {"ok": ok_bild, "grund": grund, "mtime": mt}
    return ok_bild, grund


def _cache_mischen(neu):
    """Frisch gerechnete Urteile in den Cache MISCHEN statt die Datei zu ersetzen
    (.134 Review-SOLL: Vorpruefungs- und Export-Lauf parallel verloren sonst
    gegenseitig ihre Urteile — Lost Update der Gesamtdatei). flock-Sidecar +
    read-merge-write, atomar via _json_schreiben."""
    if not neu:
        return
    import fcntl
    os.makedirs(os.path.dirname(VORPRUEFUNG), exist_ok=True)
    with open(VORPRUEFUNG + ".lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            stand = vorpruefung_lesen()
            stand.update(neu)
            _json_schreiben(VORPRUEFUNG, stand)
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def cmd_vorpruefung():
    """Vorpruefungs-Cache fuellen (.133, Grundlage der Auswahl-Seite): rechnet NUR
    neue oder geaenderte Bilder und schreibt seinen Fortschritt fuer die UI mit.
    Der Dienst startet das im Hintergrund, sobald die Seite Kandidaten ohne
    Urteil sieht; die erste Runde ueber >100 Bilder dauert ~10-15 s, danach ist
    das Urteil sofort da. Schreibt NIE nach Frigate — reines Lesen + Rechnen."""
    try:
        _nf, nm, _eg = diff()
    except Exception as e:
        kurz = f"cannot read the Frigate face list: {type(e).__name__}: {e}"
        _vp_status(laeuft=False, gesamt=0, fertig=0, fehler=kurz)
        print(f"PRE-CHECK STOPPED: {kurz}", file=sys.stderr)
        sys.exit(1)
    cache = vorpruefung_lesen()
    offen = vorpruefung_offen(nm, cache)
    _vp_status(laeuft=True, gesamt=len(offen), fertig=0)
    neu = {}
    for i, (person, datei) in enumerate(offen):
        _pruefen_gecacht(person, datei, cache, neu)
        if _VORPRUEFER == "aus":
            # Detektor nicht ladbar (.134 Review-SOLL: vorher lief die Seite in
            # ein Endlos-Karussell aus Reload + neuem Subprozess): ABSCHLUSS-
            # Vermerk 'detektor: aus' — die Seite startet damit NICHT neu,
            # alle Bilder gelten als schickbar, Frigate urteilt selbst.
            _cache_mischen(neu)
            _vp_status(laeuft=False, gesamt=len(offen), fertig=i, detektor="aus",
                       fehler="pre-check unavailable: the face detector could not "
                              "load (fail-open — Frigate will judge each image)")
            print("=> Detektor nicht ladbar — Vorpruefung fail-open beendet")
            return
        if (i + 1) % 10 == 0:              # geflusst: ein Abbruch verliert nur den Rest
            _cache_mischen(neu)
            neu = {}
            _vp_status(laeuft=True, gesamt=len(offen), fertig=i + 1)
    _cache_mischen(neu)
    _vp_status(laeuft=False, gesamt=len(offen), fertig=len(offen))
    print(f"=> {len(offen)} geprueft, {len(vorpruefung_lesen())} Urteile im Cache")


def _read_only_cli():
    """read-only-Riegel fuer den CLI-Weg (.132 Review-SOLL): der Config-Fallback
    in _frigate() macht docker-exec-Laeufe erst schreibfaehig — sie muessen den
    veroeffentlichten Sicherheits-Default (frigate_read_only, Default True)
    genauso achten wie der Dienst. Der Dienst prueft mit voller Config selbst
    und ruft deshalb mit --force auf."""
    try:
        with open(os.path.join(DATA, "config", "config.json")) as f:
            return bool(json.load(f).get("frigate_read_only", True))
    except Exception:
        return True


def cmd_export(dry, auch_extern=False, force=False, auswahl=None):
    """.132 (carlsmith-Lehre): fehlertolerant je Bild, Fatal stoppt sofort mit
    Klartext, Bericht nach BERICHT als Diagnose-Grundlage. dry = reine VORSCHAU
    und schreibt NICHTS (Review-MUSS: ein dry-Lauf darf den Fehler-Beleg des
    letzten echten Laufs nie ueberschreiben). Exit 0 nur ohne Fatal-Abbruch.

    .133 auswahl = [(person, datei), …] -> SELEKTIVER Sync: nur diese Kandidaten,
    Reihenfolge, Toleranz und Bericht sonst identisch (die Auswahl-Seite schickt
    das, was der Nutzer angehakt hat). auswahl=None = Voll-/Auto-Export; der
    ueberspringt die bewusst ABGEWAEHLTEN Bilder still, aber gezaehlt
    (bericht['abgewaehlt_n'] — nie ein stiller Verlust)."""
    t0 = time.time()
    bericht = {"ts": round(t0, 1), "modus": "export", "total": 0, "exportiert": 0,
               "exportiert_liste": [], "abgewaehlt_n": 0, "abgelehnt_n": 0,
               "uebersprungen": [], "abbruch": None, "hinweis": ""}

    def bericht_schreiben():
        if dry:
            return                                 # Vorschau: Beleg NIE anfassen
        bericht["dauer_s"] = round(time.time() - t0, 1)
        try:
            os.makedirs(os.path.dirname(BERICHT), exist_ok=True)
            tmp = BERICHT + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(bericht, f, ensure_ascii=False, indent=1)
            os.replace(tmp, BERICHT)
        except Exception as e:                     # Review-SOLL: Schreibfehler darf
            print(f"  (Bericht nicht schreibbar: {e})", file=sys.stderr)
            # weder Klartext-STOPP noch Erfolg zerstoeren

    def fatal(kurz):
        bericht["abbruch"] = kurz
        if FR_AUS_MARKER in kurz:
            bericht["hinweis"] = FR_AUS_HINWEIS
        bericht_schreiben()
        if not dry:                                # Vorschau laesst auch den Status stehen
            _progress(phase="error", modus="export", total=bericht["total"],
                      done=bericht["exportiert"], msg="export stopped",
                      detail=kurz, hinweis=bericht["hinweis"])
        print(f"EXPORT-STOPP: {kurz}", file=sys.stderr)
        sys.exit(1)

    # Vorpruefungen mit Klartext (nie mit nacktem Traceback sterben):
    if not dry and not force and _read_only_cli():
        fatal("read-only guard is on (frigate_read_only) — nothing is written to "
              "Frigate; use --force to override deliberately, or --dry-run to preview")
    if not _frigate():
        fatal("no Frigate URL configured (settings or FRIGATE_URL)")
    if not os.path.isdir(MASTER):
        fatal(f"reference master not found: {MASTER} (data dir wrong? "
              "inside the container it is /data)")
    try:
        nf, nm, eg = diff()
    except Exception as e:
        fatal(f"cannot read the Frigate face list: {type(e).__name__}: {e}")
    kandidaten = nm + (eg if auch_extern else [])
    abl = ablehnungen_aktiv()              # .137: was FRIGATE selbst abgelehnt hat
    if auswahl is None:
        # Voll-/Auto-Export: bewusst Abgewaehltes bleibt liegen (Gedaechtnis .133).
        ab = abwahl_lesen()
        vorher = len(kandidaten)
        kandidaten = [(p, d) for p, d in kandidaten if schluessel(p, d) not in ab]
        bericht["abgewaehlt_n"] = vorher - len(kandidaten)
        # .137 Schleifen-Fix (Operator-Test 06.08.): was Frigate schon einmal
        # abgelehnt hat, rennt die AUTOMATIK nicht bei jeder Runde erneut an —
        # uebersprungen, aber GEZAEHLT (nie ein stiller Verlust). Der bewusste
        # Klick auf der Auswahl-Seite versucht es weiterhin (Zweig unten).
        vorher = len(kandidaten)
        kandidaten = [(p, d) for p, d in kandidaten if schluessel(p, d) not in abl]
        bericht["abgelehnt_n"] = vorher - len(kandidaten)
    else:
        # Auswahl FILTERT die echte Kandidatenliste — was dort nicht (mehr) steht,
        # wird nie gesendet, egal was in der Auswahl-Datei steht (die Liste kommt
        # vom Browser und ist damit Fremdeingabe).
        gewollt = {schluessel(p, d) for p, d in auswahl}
        kandidaten = [(p, d) for p, d in kandidaten if schluessel(p, d) in gewollt]
        bericht["auswahl_n"] = len(gewollt)
    bericht["total"] = len(kandidaten)
    if not kandidaten:
        bericht_schreiben()
        if not dry:
            _progress(phase="done", modus="export", total=0, done=0, ok=0, gate=0)
        print("nichts zu exportieren."
              + (f" ({bericht['abgewaehlt_n']} bewusst abgewaehlt)" if bericht["abgewaehlt_n"] else "")
              + (f" ({bericht['abgelehnt_n']} zuvor von Frigate abgelehnt)" if bericht["abgelehnt_n"] else "")
              + (f" ({len(eg)} extern geloeschte nur mit --auch-extern-geloeschte)" if eg else ""))
        return
    total = len(kandidaten)
    try:
        vorhanden = set(frigate_stand())  # einmal geholt: wer braucht /create?
    except Exception as e:
        fatal(f"cannot read the Frigate face list: {type(e).__name__}: {e}")
    cache = vorpruefung_lesen()            # .133: Urteile wiederverwenden, nicht neu rechnen
    neu_urteile = {}
    neu_abl, weg_abl = {}, []              # .137: Ablehnungs-Gedaechtnis pflegen
    gleiche_folge, letzter_kurz = 0, None
    for i, (p, datei) in enumerate(kandidaten):
        if not dry:
            _progress(phase="export", modus="export", total=total, done=i, current=p)
        quelle = os.path.join(MASTER, p, datei)
        # Protokoll-Vermerk: WOHIN exportiert wurde. Das ZIEL_API-Praefix ist der
        # Beweis der API-Aera (Frigate benennt um) — abgleich() liest es (.137).
        ziel = f"{ZIEL_API}/api/faces/{p}"
        if dry:
            print(f"  [dry] exportiere {p}/{datei}")
            continue
        # .134 Review-MUSS: die Vorpruefung filtert NUR den Voll-/Auto-Export.
        # Ein auf der Auswahl-Seite bewusst angehaktes Bild schlaegt sie IMMER —
        # 'Frigates Urteil ist die Wahrheit, unser Detektor darf kein Bild
        # endgueltig aussperren' (Seiten-Versprechen); Ablehnungen faengt der
        # Bild-Fehlerpfad darunter mit Frigates echtem Grund.
        if auswahl is None:
            ok_bild, grund = _pruefen_gecacht(p, datei, cache, neu_urteile)
            if not ok_bild:                        # Vorpruefung: gar nicht erst senden
                bericht["uebersprungen"].append({"person": p, "datei": datei,
                                                 "fehler": f"pre-check: {grund}"})
                print(f"  uebersprungen {p}/{datei}: pre-check: {grund}", file=sys.stderr)
                continue
        try:
            api_upload(p, datei, quelle, person_existiert=p in vorhanden)
        except SystemExit:
            raise
        except Exception as e:
            art, kurz = _fehler_einstufen(e)
            if art == "fatal":
                fatal(kurz)
            bericht["uebersprungen"].append({"person": p, "datei": datei, "fehler": kurz})
            print(f"  uebersprungen {p}/{datei}: {kurz}", file=sys.stderr)
            merk = _ablehnung_merken(e)
            if merk:
                # .137/.138: NUR ein echtes Bild-Urteil aus /register wird
                # gemerkt (400 unbefristet, 500-unklar mit Verfall) — nie ein
                # Vorpruefungs-Skip, kein lokaler Datei-, create- oder
                # Transportfehler (Panel-MUSS: sonst sperrt ein Frigate-
                # Ausfall den ganzen Stapel dauerhaft aus).
                neu_abl[schluessel(p, datei)] = {"fehler": kurz, "mtime": _mtime(quelle),
                                                 "ts": round(time.time(), 1), "art": merk}
            # Wand-VERDACHT statt Abbruch (Review-MUSS: ein Abbruch blockierte die
            # Warteschlange dauerhaft — uebersprungene Bilder stehen beim naechsten
            # Lauf wieder VORNE, alles dahinter waere nie drangekommen). Bild-Fehler
            # sind schnelle 4xx/Lokalfehler, weiterlaufen kostet nichts; der Verdacht
            # wird im Bericht ausgewiesen. 'No face was detected.' zaehlt nicht mal
            # als Verdacht (laut beta2-Quelle beweisbar BILD-abhaengig).
            if "No face was detected" not in kurz:
                gleiche_folge = gleiche_folge + 1 if kurz == letzter_kurz else 1
                letzter_kurz = kurz
                if gleiche_folge == 3 and not bericht.get("wand_verdacht"):
                    bericht["wand_verdacht"] = kurz
                    print(f"  WAND-VERDACHT (3x gleicher Fehler in Folge, laufe "
                          f"weiter): {kurz}", file=sys.stderr)
            continue
        gleiche_folge, letzter_kurz = 0, None
        vorhanden.add(p)
        weg_abl.append(schluessel(p, datei))    # .137: geklappt -> Merker faellt
        bericht["exportiert"] += 1
        # .133: WELCHE Bilder durchkamen, nicht nur wie viele — die Auswahl-Seite
        # zeigt je Bild 'uploaded' bzw. Frigates Ablehnungsgrund aus dem Bericht.
        bericht["exportiert_liste"].append({"person": p, "datei": datei})
        meta_append(person=p, datei=datei, herkunft="export", aktiv=True, ziel=ziel)
        print(f"  exportiert: {p}/{datei}")
    if dry:
        print(f"=> {len(kandidaten)} exportierbar (dry, nichts geschrieben)")
        return
    try:                                   # frisch gerechnete Urteile MISCHEN (.134:
        _cache_mischen(neu_urteile)        # nie mehr die Gesamtdatei ersetzen)
    except Exception as e:
        print(f"  (Vorpruefungs-Cache nicht schreibbar: {e})", file=sys.stderr)
    if bericht.get("wand_verdacht"):
        # .138 Panel-MUSS: eine WAND (3x derselbe Fehler in Folge) ist kein
        # Bild-Urteil, sondern ein Zustand der Gegenstelle — ihre Merker werden
        # verworfen, sonst schlaegt der Schleifen-Fix in ein 'nie wieder' um.
        # Nur die Wand-Eintraege fallen; ein echtes 'No face'-Urteil aus
        # demselben Lauf (zaehlt nie als Wand) bleibt gemerkt.
        wand = [k for k, v in neu_abl.items() if v["fehler"] == bericht["wand_verdacht"]]
        for k in wand:
            neu_abl.pop(k)
        if wand:
            bericht["ablehnungen_verworfen"] = len(wand)
            print(f"  ({len(wand)} Ablehnungs-Merker verworfen — Wand-Verdacht, "
                  "kein Bild-Urteil)", file=sys.stderr)
    try:
        _ablehnungen_mischen(neu_abl, weg_abl)
    except Exception as e:
        print(f"  (Ablehnungs-Merker nicht schreibbar: {e})", file=sys.stderr)
    bericht_schreiben()
    n_skip = len(bericht["uebersprungen"])
    _progress(phase="done", modus="export", total=total, done=total,
              ok=bericht["exportiert"], gate=n_skip,
              abgewaehlt=bericht["abgewaehlt_n"], abgelehnt=bericht["abgelehnt_n"])
    print(f"=> {bericht['exportiert']} exportiert, {n_skip} uebersprungen"
          + (f", {bericht['abgewaehlt_n']} abgewaehlt" if bericht["abgewaehlt_n"] else "")
          + (f", {bericht['abgelehnt_n']} zuvor abgelehnt (uebersprungen)"
             if bericht["abgelehnt_n"] else ""))


if __name__ == "__main__":
    import urllib.parse
    modus = sys.argv[1] if len(sys.argv) > 1 else "status"
    dry = "--dry-run" in sys.argv
    if modus == "status":
        cmd_status()
    elif modus == "import":
        cmd_import(dry)
    elif modus == "export":
        # .133: die Auswahl kommt als DATEI, nie als argv — hunderte Personen-/
        # Dateinamen sprengen jede Kommandozeile (und der Dienst muesste sie
        # quoten). Fehlt/kaputt = Klartext-Stopp, nie ein nackter Traceback.
        _aus = None
        _apfad = next((a.split("=", 1)[1] for a in sys.argv[2:]
                       if a.startswith("--auswahl=")), "")
        if _apfad:
            try:
                with open(_apfad, encoding="utf-8") as _af:
                    _aus = [(str(x[0]), str(x[1])) for x in json.load(_af) if len(x) >= 2]
            except Exception as _e:
                print(f"EXPORT-STOPP: selection file unusable ({_apfad}): "
                      f"{type(_e).__name__}: {_e}", file=sys.stderr)
                sys.exit(1)
        cmd_export(dry, auch_extern="--auch-extern-geloeschte" in sys.argv,
                   force="--force" in sys.argv, auswahl=_aus)
    elif modus == "vorpruefung":
        cmd_vorpruefung()
    else:
        print(__doc__)
