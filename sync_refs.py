#!/usr/bin/env python3
"""Referenz-Sync Master <-> Frigate (Plan v1.0 AP1).

Master = die aktiven Referenz-Saetze der Referenz-Quelle (core/refquelle, Lese-Stufe b; seit
E3b-3a, Bauplan analysen/bauplan_refquelle_einbau.md, Entscheide 6, 10, I3), die Export-Merker
je ref_id im Katalog (Art export). Frigate-Ablage = Frigates /api/faces.

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
                                   #   [[person, ref_id], …] (selektiver Sync, .133)
  sync_refs.py vorpruefung         # Vorpruefungs-Cache fuellen (nur Saetze ohne Urteil),
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
# .133 "Selektiver Sync" — zwei Laufprotokolle in state/ (I3: ausserhalb des
# Moduls), je EINE Quelle (Vertrag mit verifyd/routes.syncauswahl; nie ein
# zweites Literal streuen):
#   VORPRUEFUNG     Urteil je ref_id (Cache; seit E3b-3a ohne mtime, ein Satz ist
#                   unveraenderlich — nur Saetze ohne Urteil werden gerechnet),
#   VORPRUEF_STATUS Fortschritt des Hintergrund-Laufs fuer die Seite.
VORPRUEFUNG = os.path.join(DATA, "state", "sync_vorpruefung.json")
VORPRUEF_STATUS = os.path.join(DATA, "state", "sync_vorpruefung_status.json")
# Die Export-Merker je ref_id stehen seit E3b-3a im Katalog der Referenz-Quelle
# (Art export, je merker gilt die letzte Zeile; Entscheid 10) statt in refs_meta,
# state/sync_abwahl.json und state/sync_ablehnungen.json. Die drei Merker-Namen
# und ihre Wert-Marken stehen nur hier:
#   MERKER_EXPORT    nach erfolgreichem /register: {ziel, person, ts}; "offer
#                    again" schreibt dieselbe Zeile mit {ZURUECK: True, grund}
#                    (der Satz ist wieder Kandidat).
#   MERKER_ABWAHL    {an: wahr|falsch, ts} — bewusst zurueckgehalten: der Satz
#                    bleibt Referenz, geht aber nicht nach Frigate.
#   MERKER_ABLEHNUNG {fehler, art, ts}; ein Erfolg schreibt {ERLEDIGT: True, ts}.
MERKER_EXPORT, MERKER_ABWAHL, MERKER_ABLEHNUNG = "exportiert", "abwahl", "ablehnung"
ZURUECK, ERLEDIGT = "zurueckgenommen", "erledigt"
# .137 "Ablehnungs-Gedaechtnis" (MERKER_ABLEHNUNG): was FRIGATE selbst je Bild
#                abgelehnt hat. Ein Vorpruefungs-Urteil ist UNSER
#                Detektor und darf nie als Frigate-Ablehnung gemerkt werden.
#                Wirkung: der AUTOMATIK-
#                Lauf ueberspringt Gemerktes still-gezaehlt (bericht
#                ['abgelehnt_n']), eine bewusste Auswahl versucht es trotzdem und
#                erledigt den Merker bei Erfolg (Schleifen-Fix, Operator-Test
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
# Verfall der 'unklar'-Merker: lang genug, dass ein haengender Frigate-Zustand
# nicht bei jeder Runde neu angerannt wird, kurz genug, dass sich der Bestand
# nach einem Frigate-Neustart von selbst erholt (ein Wiederholungsversuch/Tag).
ABLEHNUNG_UNKLAR_TTL_S = 24 * 3600
# Vermerk 'ziel' im Merker MERKER_EXPORT. Das Praefix ist der BEWEIS, dass ein Bild
# ueber /register ging — und Frigate benennt dabei um (<Name>_<ts>.webp), womit der
# Dateiname fuer immer unvergleichbar wird. Eintraege OHNE dieses Praefix stammen aus
# der SSH-Aera (Dateiname blieb erhalten, beim Satz der alte Dateiname, I9) und sind
# per Namen vergleichbar. EINE Quelle: cmd_export schreibt es, abgleich() liest es.
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
PROGRESS = os.path.join(DATA, "state", "sync_progress.json")   # Fortschritt fuer die UI (X von Y, Person, ref_id)


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


def schluessel(person, ref_id):
    """Der EINE Schluessel der Seite und des Exports fuer Abwahl, Ablehnungen, Urteile und
    Auswahl: '<Person>/<ref_id>' (seit E3b-3a die ref_id statt des Dateinamens). Vertrag mit
    verifyd und routes/syncauswahl.py — beide bauen ihn NIE selbst zusammen (QS-Ebenen-Regel:
    keine Streu-Literale)."""
    return f"{person}/{ref_id}"


def _rq_cfg():
    """Die Config der Referenz-Quelle fuer diesen Prozess (Datenordner aus VERIFY_DATA_DIR).
    -> {"data_dir": ...}"""
    return {"data_dir": DATA}


def _lesung():
    """Lese-Stufe b der Referenz-Quelle, die eine Lesung des Exports (E3b-3a).
    -> ({ref_id: Eintrag}, {Person: [ref_id der aktiven Referenzen]})"""
    from core import refquelle as _rq
    kat = _rq.read_catalog(_rq_cfg())
    return kat["eintraege"], kat["personen"]


def _merker(eintrag, name):
    """Die gueltigen Werte eines Export-Merkers am Katalogeintrag (je merker gilt die letzte Zeile).
    -> dict der Werte; leer, wenn der Satz diesen Merker nie bekam"""
    return dict(((eintrag.get("export") or {}).get(name) or {}).get("werte") or {})


def _merken(ref_id, name, werte):
    """Eine Merker-Zeile (Art export) ueber das Modul an den Katalog haengen, mit Zeitpunkt.
    -> None; ein abgelehnter Schreibversuch wirft RefquelleError (die ERROR-Zeile schreibt das Modul)"""
    from core import refquelle as _rq
    _rq.append(_rq_cfg(), ref_id, "export",
               {"merker": name, "werte": {**werte, "ts": round(time.time(), 1)}})


def _nur_aktive(paare, personen):
    """Fremdeingabe der Seite pruefen: jedes Paar muss eine aktive Referenz dieser Person sein.
    -> None; sonst ValueError mit Klartext, und es wird nichts geschrieben"""
    fremd = [(p, r) for p, r in paare if r not in personen.get(p, ())]
    if fremd:
        raise ValueError(f"{len(fremd)} selected image(s) are no active reference set of that person "
                         "(an old picture file name from before this version, or already removed) — "
                         "nothing changed")


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


def abwahl_lesen(eintraege=None, personen=None):
    """Die bewusst abgewaehlten aktiven Referenzen aus dem Merker MERKER_ABWAHL (letzte Zeile gilt);
    eintraege/personen = eine schon gemachte Lesung (_lesung), sonst selbst gelesen.
    -> {schluessel: {"ts", "person", "ref_id"}}"""
    if eintraege is None:
        eintraege, personen = _lesung()
    aus = {}
    for person, rids in personen.items():
        for rid in rids:
            w = _merker(eintraege[rid], MERKER_ABWAHL)
            if w.get("an") is True:
                aus[schluessel(person, rid)] = {"ts": w.get("ts"), "person": person, "ref_id": rid}
    return aus


def abwahl_setzen(paare, an=True):
    """paare = [(person, ref_id), …] abwaehlen (an=True) oder zurueckholen: je Satz eine Merker-Zeile
    MERKER_ABWAHL im Katalog, nur wenn sich der Stand aendert; ein Paar, das keine aktive Referenz
    dieser Person ist, lehnt den ganzen Aufruf laut ab (ValueError).
    -> Zahl der WIRKLICH geaenderten Eintraege (Doppelklicks zaehlen nicht)."""
    eintraege, personen = _lesung()
    _nur_aktive(paare, personen)
    n = 0
    for _person, rid in dict.fromkeys(paare):
        if (_merker(eintraege[rid], MERKER_ABWAHL).get("an") is True) != bool(an):
            _merken(rid, MERKER_ABWAHL, {"an": bool(an)})
            n += 1
    return n


def ablehnungen_aktiv(eintraege=None, personen=None):
    """Die gueltigen Frigate-Ablehnungen der aktiven Referenzen aus dem Merker MERKER_ABLEHNUNG: nicht
    erledigt, und 'unklar'-Merker (500 'could not process' — kann Bild ODER Frigate-Zustand sein,
    .138) nur bis ABLEHNUNG_UNKLAR_TTL_S. Seit E3b-3a ohne mtime: ein Satz ist unveraenderlich, ein
    neues Bild ist ein neuer Satz ohne Merker. eintraege/personen wie bei abwahl_lesen.
    -> {schluessel: {"fehler", "art", "ts"}}"""
    if eintraege is None:
        eintraege, personen = _lesung()
    aus = {}
    for person, rids in personen.items():
        for rid in rids:
            e = _merker(eintraege[rid], MERKER_ABLEHNUNG)
            if not e or e.get(ERLEDIGT) is True:
                continue
            if e.get("art") == "unklar" and time.time() - float(e.get("ts") or 0) > ABLEHNUNG_UNKLAR_TTL_S:
                continue
            aus[schluessel(person, rid)] = e
    return aus


def _ablehnungen_mischen(neu=None, weg=()):
    """Die Ablehnungen eines Laufs als Merker-Zeilen in den Katalog (anhaengend, unter der Sperre
    des Moduls: parallele Laeufe verlieren einander nichts, Lehre .134). neu = {ref_id: {"fehler",
    "art"}}, weg = ref_ids, deren Bild gerade doch durchging: ihre offene Ablehnung wird erledigt.
    -> None"""
    if not neu and not weg:
        return
    eintraege, _personen = _lesung()
    for rid, werte in (neu or {}).items():
        _merken(rid, MERKER_ABLEHNUNG, werte)
    for rid in weg:
        alt = _merker(eintraege.get(rid) or {}, MERKER_ABLEHNUNG)
        if alt and alt.get(ERLEDIGT) is not True:
            _merken(rid, MERKER_ABLEHNUNG, {ERLEDIGT: True})


def vorpruefung_lesen():
    """Der Laufstand der Vorpruefung (I3, ausserhalb des Moduls).
    -> {ref_id: {"ok": bool, "grund": str}}."""
    return _json_lesen(VORPRUEFUNG, {})


def vorpruefung_status():
    """-> {"ts", "laeuft", "gesamt", "fertig", "fehler"} des Hintergrund-Laufs."""
    return _json_lesen(VORPRUEF_STATUS, {})


def _vp_status(**d):
    try:
        _json_schreiben(VORPRUEF_STATUS, {"ts": round(time.time(), 1), **d})
    except Exception:
        pass


def vorpruefung_offen(kandidaten, cache=None):
    """Welche Kandidaten [(person, ref_id), …] haben (noch) KEIN Urteil? Seit E3b-3a ohne
    Dateianker: ein Satz ist unveraenderlich, ein neues Bild ist eine neue ref_id ohne Urteil.
    -> [(person, ref_id), …] ohne Urteil im Laufstand"""
    cache = vorpruefung_lesen() if cache is None else cache
    return [(person, rid) for person, rid in kandidaten if not cache.get(rid)]


ERLAUBTE_ENDUNGEN = (".jpg", ".jpeg", ".png", ".webp")
# Permissiv und UNICODE-bewusst: echte Namen wie "Müller" oder ein Doppelname mit Bindestrich muessen durch,
# sonst faellt ein legitimer Import STILL aus (Fehlerklasse C). Verboten sind nur die Zeichen,
# die Pfade aufbrechen. Die eigentliche Sicherheit macht das realpath-Containment darunter.
# Bis 03.08. stand hier nur "alles ausser / \\ NUL" — permissiver als JEDE Konsumenten-
# Pruefung. Folge (Sweep-Befund): ein Frigate-Gesicht "Anna.B"/"Tim+Bo" wurde importiert,
# war auf der Known-Seite sichtbar, aber unbedienbar (Thumbnails 404, Loeschen
# "ungueltiger Pfad"). Jetzt gilt derselbe Vertrag wie fuer die Verbraucher; was nicht
# passt, wird LAUT uebersprungen (Zeile im Import-Log) statt still unbrauchbar angelegt.
from core.registry import PERSON_RE as _PERSON_RE
from core import frigate_auth as _fauth      # 5e: DER eine Frigate-HTTP-Griff
_NAME_OK = re.compile(rf"^{_PERSON_RE}$", re.UNICODE)


def sicheres_ziel(person, datei, wurzel):
    """Schreibziel <wurzel>/<person>/<datei> fuer ein Referenzbild bauen — oder (None, Grund), wenn es
    unsicher ist. Die Wurzel nennt der Aufrufer (cmd_import: der Staging-Ordner des Laufs; seit E3c-1,
    Bauplan analysen/bauplan_refquelle_einbau.md, Stufe E3 Punkt 3, gibt es keinen Umweg ueber faces/).

    Die Namen kommen aus /api/faces der GEGENSTELLE und sind damit Fremdeingabe: die
    Frigate-URL ist ueber POST /sync_import frei setzbar. Ohne Pruefung landet person='../../app'
    per os.path.join ausserhalb der Wurzel — im Container als root, mit /app/verifyd.py als
    Ziel (Codeausfuehrung beim naechsten Neustart). Zwei Schichten, absichtlich redundant:
    1. Namens-/Endungs-Whitelist (faengt das Offensichtliche und haelt die Ablage sauber),
    2. realpath-Containment gegen die Wurzel (die eigentliche Garantie — greift auch bei Symlinks
       und bei allem, woran die Regex nicht gedacht hat).
    -> (Zielpfad, "") oder (None, Grund)"""
    if not person or not datei:
        return None, "leerer Name"
    if person in (".", "..") or datei in (".", ".."):
        return None, "Punkt-Eintrag"
    if not _NAME_OK.match(person) or not _NAME_OK.match(datei):
        return None, "unerlaubte Zeichen im Namen"
    if not datei.lower().endswith(ERLAUBTE_ENDUNGEN):
        return None, "unerlaubte Dateiendung"
    ziel = os.path.join(wurzel, person, datei)
    basis = os.path.realpath(wurzel)
    if not os.path.realpath(ziel).startswith(basis + os.sep):
        return None, "Pfad zeigt aus dem Staging-Ordner heraus"
    return ziel, ""


def frigate_stand():
    with _fauth.oeffnen(f"{_frigate()}/api/faces", timeout=20) as r:        # 5e
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
        with _fauth.oeffnen(f"{basis}/api/config", timeout=timeout) as r:   # 5e
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
    Ein Satz mit gueltigem Merker MERKER_EXPORT ist deshalb NIE wieder
    Export-Kandidat. Bekannte Grenze (Design-Entscheid offen): die von Frigate
    umbenannten Exporte erscheinen in nur_frigate als Import-Kandidaten —
    cmd_import ist manuell, nichts laeuft von allein.
    Seit E3b-3a (Bauplan Referenz-Quelle einbauen, Entscheide 6 und 10): die Master-Seite sind die
    aktiven Referenz-Saetze je Person aus Lese-Stufe b, ihre Klasse kommt aus dem Satz und seinen
    Merkern (_klasse), nicht aus Dateinamen in faces/ und refs_meta; nur_master und
    extern_geloescht fuehren (person, ref_id). nur_frigate wie seit E3a-4 (J10): eine
    Frigate-Datei gilt als vorhanden, wenn ihr Satz im Katalog steht, gleich mit welchem Status.
    -> (nur_frigate [(person, datei)], nur_master [(person, ref_id)], extern_geloescht [(person, ref_id)])"""
    f = frigate_stand()
    eintraege, personen = _lesung()
    nur_master, extern_geloescht = [], []
    for p in sorted(personen):
        for rid in sorted(personen[p]):
            # Kandidat · schon exportiert -> Frigate fuehrt es unter eigenem Namen,
            # NIE erneut senden · Herkunft Frigate-Import -> dort geloescht ·
            # Vorrat -> bleibt lokal.
            klasse, grund = _klasse(eintraege[rid], p, f)
            if klasse == "kandidaten":
                nur_master.append((p, rid))
            elif klasse == "geloescht" and grund == D1_IMPORT:
                extern_geloescht.append((p, rid))
    return _nur_frigate(f, eintraege), nur_master, extern_geloescht


def _nur_frigate(f, eintraege):
    """Frigate-Dateien ohne Satz im Katalog (Import-Kandidaten, J10): ein Satz aus dem Frigate-Import
    (Herkunftsart frigate_import, Frigate-Person und -Datei) zaehlt mit jedem Status — wie bisher ein
    Tombstone holt ein Satz, den der Nutzer entfernt hat, nichts zurueck.
    -> [(person, datei)] sortiert"""
    from core.harvest_set import ART_FRIGATE_IMPORT
    im_katalog = {(e["frigate"]["person"], e["frigate"]["datei"]) for e in eintraege.values()
                  if e.get("herkunftsart") == ART_FRIGATE_IMPORT and e.get("frigate")}
    return [(p, d) for p in sorted(f) for d in f[p] if (p, d) not in im_katalog]


def _klasse(eintrag, person, f):
    """Die Klasse einer aktiven Referenz vor der Abwahl, nach den Regeln von diff und abgleich, aus dem
    Satz (Herkunftsart, Frigate-Angaben, alter Dateiname, Vorrats-Nachtrag) und dem Merker
    MERKER_EXPORT statt aus Dateinamen und refs_meta. f = Frigates Liste {Person: [Datei]}.
    -> (klasse, grund): in_beiden, kandidaten, geloescht (grund D1_IMPORT/D1_EXPORT), api_export,
    vorrat_lokal"""
    from core.harvest_set import ART_FRIGATE_IMPORT
    from core.vorrat import NACHTRAG_THEMA
    exp = _merker(eintrag, MERKER_EXPORT)
    aus_frigate = eintrag.get("frigate") if eintrag.get("herkunftsart") == ART_FRIGATE_IMPORT else None
    if aus_frigate and aus_frigate["datei"] in f.get(aus_frigate["person"], ()):
        return "in_beiden", None                 # A: derselbe Name auf beiden Seiten
    if exp and exp.get(ZURUECK) is not True:
        # Namensvergleichbarkeit AUS DEM MERKER: nur die SSH-Aera hat den Dateinamen
        # drueben erhalten (beim Satz der alte Dateiname, I9). Ohne api:-Ziel heisst
        # "Name fehlt" also wirklich "extern geloescht" (D1), mit api:-Ziel heisst es
        # gar nichts (D2) — Frigate fuehrt es umbenannt.
        if str(exp.get("ziel") or "").startswith(ZIEL_API):
            return "api_export", None
        if (eintrag.get("herkunft") or {}).get("alter_dateiname") in f.get(person, ()):
            return "in_beiden", None
        return "geloescht", D1_EXPORT
    if exp:                                      # "offer again": wieder normaler Kandidat
        return "kandidaten", None
    if aus_frigate:
        return "geloescht", D1_IMPORT
    if NACHTRAG_THEMA in (eintrag.get("nachtrag") or {}):
        # Vorrats-Referenzen (bauplan_vorrat.md B4, W1.15): NIE exportieren — ihre
        # Wahrheit ist der Fingerabdruck aus dem Ernte-Vollbild, die kleine Bilddatei
        # kann Frigates eigene Anlern-Pipeline gemessen oft nicht detektieren (28/40
        # tot). Bewusst KEIN Kandidat, bleibt lokal (Registrieren-nach-Schaltern).
        return "vorrat_lokal", None
    return "kandidaten", None                    # C: nie geschickt -> uebertragbar


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
                   Erzeuger- und Verbrauchermenge liefen auseinander).
    Seit E3b-3a: "Master-Bild" heisst aktive Referenz der Referenz-Quelle, die Paare tragen
    (person, ref_id) statt (person, datei) — nur nur_frigate fuehrt Frigates Dateinamen; die Klasse
    kommt aus _klasse (Satz und Merker), gesamt und je_person zaehlen Saetze. Ein Satz aus dem
    Frigate-Import ist "in beiden", solange Frigate seine Datei fuehrt (O572 d)."""
    f = frigate_stand()
    eintraege, personen = _lesung()
    ab = abwahl_lesen(eintraege, personen)
    abl = ablehnungen_aktiv(eintraege, personen)
    erg = {"gesamt": 0, "in_beiden": [], "je_person": {}, "nur_frigate": _nur_frigate(f, eintraege),
           "kandidaten": [], "abgelehnt": {}, "geloescht": [], "api_export": [],
           "abgewaehlt": [], "abgewaehlt_unpruefbar": [],
           # bauplan_vorrat.md B4 (Klassen-Invariante unten erweitert):
           # Vorrats-Referenzen sind NIE Export-Kandidaten — stuenden sie in
           # 'kandidaten', liefe die Erzeuger-Menge (diff() schliesst sie aus)
           # gegen die Verbraucher-Menge auseinander, exakt die K3-Klasse aus
           # dem .138-Panel-Befund.
           "vorrat_lokal": []}
    for p in sorted(set(personen) | set(f)):
        rids = sorted(personen.get(p, []))
        beide = 0
        for rid in rids:
            erg["gesamt"] += 1
            klasse, grund = _klasse(eintraege[rid], p, f)
            if klasse == "in_beiden":             # A: derselbe Name auf beiden Seiten
                beide += 1
                erg["in_beiden"].append((p, rid))
                continue
            k = schluessel(p, rid)
            if k in ab:                           # N: bewusste Entscheidung schlaegt alles
                erg["abgewaehlt"].append((p, rid))
                if klasse != "kandidaten":
                    erg["abgewaehlt_unpruefbar"].append((p, rid))
                continue
            if klasse == "geloescht":
                erg["geloescht"].append((p, rid, grund))
            elif klasse == "api_export":
                erg["api_export"].append((p, rid))
            elif klasse == "vorrat_lokal":
                erg["vorrat_lokal"].append((p, rid))
            else:
                erg["kandidaten"].append((p, rid))
                if k in abl:
                    erg["abgelehnt"][k] = abl[k]
        erg["je_person"][p] = {"gesamt": len(rids), "beide": beide, "frigate": len(f.get(p, []))}
    return erg


# Grund-Marker der offer-again-Zeile (seit E3b-3a als grund im Merker MERKER_EXPORT) — die
# Zeile ist keine Loeschung: das Bild bleibt aktive Referenz, sein Anlern-Gesicht bleibt
# zugeordnet (.138 Panel-Befund: die Zeile gab das Gesicht sonst wieder als
# Unbekannt-Vorschlag frei, Weg zum exakten Duplikat-Anlernen).
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
    aktiv=True-Eintrag alles zurueck.
    Seit E3b-3a: paare = [(person, ref_id), …]; statt der refs_meta-Zeile eine Merker-Zeile
    MERKER_EXPORT mit {ZURUECK: True, grund: GRUND_WIEDER_ANBIETEN} im Katalog (je merker gilt die
    letzte Zeile, der Satz bleibt, keine Loeschung). Nur fuer Saetze, die ein gueltiger Export-Merker
    oder ihre Herkunft aus Frigate ausserhalb der Kandidaten haelt; ein Paar, das keine aktive
    Referenz dieser Person ist, lehnt den Aufruf laut ab (ValueError)."""
    from core.harvest_set import ART_FRIGATE_IMPORT
    eintraege, personen = _lesung()
    _nur_aktive(paare, personen)
    n = 0
    for _person, rid in dict.fromkeys(paare):
        exp = _merker(eintraege[rid], MERKER_EXPORT)
        draussen = (exp.get(ZURUECK) is not True if exp
                    else eintraege[rid].get("herkunftsart") == ART_FRIGATE_IMPORT)
        if not draussen:                      # schon Kandidat — nichts zu tun
            continue
        _merken(rid, MERKER_EXPORT, {ZURUECK: True, "grund": GRUND_WIEDER_ANBIETEN})
        n += 1
    return n


def cmd_status():
    """Abgleich beider Seiten auf der Konsole; seit E3b-3a zaehlt und nennt er Saetze (Person und
    die ersten zwoelf Zeichen der ref_id) statt Dateien. -> None"""
    nf, nm, eg = diff()
    print(f"Neu in Frigate (Import-Kandidaten): {len(nf)}")
    for p, d in nf[:10]:
        print(f"  + {p}/{d}")
    print(f"Nur bei uns, nie exportiert (Export-Kandidaten, Saetze): {len(nm)}")
    for p, rid in nm[:10]:
        print(f"  > {p}/{rid[:12]}")
    print(f"EXTERN GELOESCHT (in Frigate weg, bei uns aktiv) — Entscheidung offen: {len(eg)}")
    for p, rid in eg[:10]:
        print(f"  ! {p}/{rid[:12]}  (Referenz entfernen ODER bewusst re-exportieren)")
    # Ehrliche Zusatzzeile (nie stilles Verschwinden): schon Exportiertes fuehrt
    # Frigate 0.18 unter EIGENEM Namen (<Name>_<ts>.webp) — es fehlt im
    # Namens-Abgleich, ist aber KEIN Kandidat und KEIN Verlust.
    eintraege, personen = _lesung()
    f = frigate_stand()
    n_exp = sum(1 for p, rids in personen.items() for rid in rids
                if _klasse(eintraege[rid], p, f) in (("api_export", None), ("geloescht", D1_EXPORT)))
    if n_exp:
        print(f"Bereits exportiert, von Frigate unter eigenem Namen gefuehrt: {n_exp}")
    # .133: bewusst Abgewaehltes ist KEIN Kandidat mehr — das gehoert sichtbar in
    # die Bilanz, sonst wundert man sich ueber die Differenz zum Export-Ergebnis.
    ab = abwahl_lesen(eintraege, personen)
    n_ab = sum(1 for p, rid in nm if schluessel(p, rid) in ab)
    if n_ab:
        print(f"Davon bewusst abgewaehlt (gehen NICHT nach Frigate): {n_ab}")
    # .137: gemerkte FRIGATE-Ablehnungen — der Auto-Export laesst sie aus, die
    # Auswahl-Seite zeigt sie rot und anklickbar. Nie still unter den Tisch.
    n_abl = len(ablehnungen_aktiv(eintraege, personen))
    if n_abl:
        print(f"Von Frigate abgelehnt (gemerkt, Auto-Export laesst sie aus): {n_abl}")
    if not (nf or nm or eg):
        print("=> synchron.")


def cmd_import(dry):
    # Frigate-Referenzbilder sind bereits fertige Gesichts-Crops -> KEIN CPU-Face-Gate hier. Hier nur
    # schnell herunterladen; die Rechenarbeit macht der Worker-Dienst.
    # E3a-4 (Bauplan Referenz-Quelle einbauen, J10): der Download landet im Staging-Ordner des Laufs
    # state/import/<lauf>/<person>/<datei>, nicht mehr unter faces/, und schreibt keine refs_meta-Zeile.
    # Den Satz schreibt danach der Dienst je geholter Datei ueber den Job dateisatz des Worker-Dienstes
    # (Bild-Weg der Engine); die Liste der geholten Dateien steht im Schluss-Fortschritt (lauf, geholt,
    # Pfade relativ zum Datenordner). Die Staging-Dateien bleiben liegen (geloescht wird hier nichts).
    nf, _, _ = diff()
    if not nf:
        _progress(phase="done", total=0, done=0, ok=0, gate=0)
        print("nichts zu importieren.")
        return
    lauf = f"{time.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:6]}"
    ablage = os.path.join(DATA, "state", "import", lauf)
    geholt = []
    total = len(nf)
    n_ok = n_dl = n_bad = 0
    for i, (p, datei) in enumerate(nf):
        _progress(phase="import", total=total, done=i, current=p, ok=n_ok, gate=n_dl)
        ziel, grund = sicheres_ziel(p, datei, ablage)   # Fremdeingabe: NIE ungeprueft in einen Pfad
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
            with _fauth.oeffnen(f"{_frigate()}/clips/faces/{urllib.parse.quote(p)}/{urllib.parse.quote(datei)}",
                                timeout=20) as r:          # 5e
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
        geholt.append({"person": p, "datei": datei, "pfad": os.path.relpath(ziel, DATA)})
        print(f"  geholt: {p}/{datei} -> {os.path.relpath(ziel, DATA)}")
    _progress(phase="done", total=total, done=total, ok=n_ok, gate=n_dl, abgelehnt=n_bad,
              lauf=None if dry else lauf, geholt=geholt)
    msg = f"=> {n_ok} importiert{' (dry)' if dry else ''}, {n_dl} Download-Fehler"
    if n_bad:
        msg += f", {n_bad} ABGELEHNT (unsichere Namen)"     # laut, nicht still
    print(msg)


# INVARIANTE: FRIGATE_FACES_API   (Marke: CLAUDE.md "Frigate-Zugriff: NUR ueber die HTTP-API")
# 5e (26.08.): der HTTP-Griff heisst seither core.frigate_auth.oeffnen statt roh
# urllib — dieselben Endpunkte, dasselbe Protokoll, kein neuer Weg. Die
# Invariante wird dadurch nicht geschwaecht, sondern erst tragfaehig: auf einer
# Frigate mit Anmeldung (authentifizierter Port 8971) beantwortete der rohe
# API-Weg JEDE Mutation mit 401 — und ein Nutzer, dem der API-Weg nicht
# funktioniert, sucht sich einen anderen. Genau den soll es nie geben.
def api_upload(person, datei, inhalt, person_existiert=None):
    """Referenzbild ueber die Frigate-HTTP-API hochladen (Frigate 0.18.0, Endpunkte
    aus der OpenAPI der LAUFENDEN Instanz verifiziert, 05.08. — der fruehere
    POST /api/faces/{name} existiert dort NICHT, 404):
      1. unbekannter Name -> POST /api/faces/{name}/create (legt den Namen an),
      2. Bild             -> POST /api/faces/{name}/register (multipart, Feld `file`).
    inhalt: die Bytes des Bildes (seit E3b-3a die Profilbild-Bytes eines Satzes, Lese-Stufe d,
    statt eines Pfads), datei: der Dateiname im Formular (<ref_id>.<Endung>).
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
            with _fauth.oeffnen(req, timeout=60) as r:      # 5e
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
    typ ={"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
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
    dauerhaft aus, weil sich ein Referenzbild nie aendert; seit E3b-3a ist der
    Merker eine Katalogzeile je ref_id ohne mtime, ein Satz ist unveraenderlich).
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


def _gesicht_pruefen(daten):
    """Vorpruefung analog Frigates register (.132, User-Entscheid): Frigate
    laesst jeden Upload durch SEINEN Gesichtsdetektor (beta2 face.py, Schwelle
    0.5) und lehnt sonst mit 'No face was detected.' ab. Wir pruefen vorab mit
    UNSEREM Detektor (buffalo_l/SCRFD, CPU, nur Detektions-Modul) und schicken
    nur, was bestehen duerfte — anderes Modell, kein identisches Urteil,
    Frigates Antwort bleibt die Wahrheit (der Bild-Fehlerpfad faengt
    Rest-Ablehnungen weiter ab). Detektor-Ladefehler = fail-open mit Ansage
    (die Vorpruefung ist Optimierung, nie Blocker). Seit E3b-3a urteilt sie auf den
    Bytes des Profilbilds (daten, Lese-Stufe d) statt auf einer Datei.
    -> (True, '')/(False, grund)."""
    global _VORPRUEFER
    if _VORPRUEFER is None:
        try:
            import onnxruntime as ort
            ort.set_default_logger_severity(3)
            from insightface.app import FaceAnalysis
            # .505 (E3c, 05.09.2026, Widerleger W-E3 SCHWER 1): derselbe
            # Init-Griff wie in face_audit.Embedder — FaceAnalysis UND prepare
            # in die zentrale Kappungs-Klammer. insightface baut seine
            # Modell-Sessions ohne SessionOptions, onnxruntime nimmt dann
            # hardware_concurrency() des WIRTS statt der erlaubten Kerne und
            # pinnt Thread i an Kern i (pthread_setaffinity-EINVAL je fremdem
            # Kern). allowed_modules hilft dagegen NICHT: FaceAnalysis ruft
            # get_model fuer JEDE der fuenf ONNX-Dateien und wirft die nicht
            # erlaubten Modelle erst NACH dem Session-Bau weg — hier entstehen
            # also fuenf Pools, von denen vier sofort sterben. Der Ersatz nach
            # prepare() (unten, _ort_session) bleibt unveraendert; neu ist nur,
            # dass die zu grossen Pools gar nicht erst gebaut werden.
            # Import lokal an der Stelle: face_audit importiert sync_refs NICHT
            # (kein Zirkel, geprueft), und sync_refs holt sich face_audit ohnehin
            # schon lazy fuer _ort_session ein paar Zeilen weiter unten — ein
            # Modul-Import auf Dateiebene wuerde dem CLI-Start dieses Werkzeugs
            # numpy/cv2/insightface aufladen, auch wenn nur exportiert wird.
            #
            # EIGENER try (.505 E4, 05.09.2026, Widerleger W-E3c Notiz 3): dieselbe
            # Regel wie beim Session-Ersatz unten, und aus demselben Grund. Die
            # Kappung ist KOMFORT (kein zu grosser Thread-Pool im Init), der
            # Vorpruefer ist FUNKTION (er spart Frigate-Ablehnungen). Lag der
            # Import im umgebenden try — so kam er aus E3c heraus —, dann schaltete
            # ein gescheiterter Import (Image-Variante ohne diese Abhaengigkeit,
            # Zirkel in einer fremden Umgebung) den Vorpruefer GANZ ab
            # (_VORPRUEFER = "aus") statt ihn ungekappt laufen zu lassen. Genau
            # diese Regression hatte der Widerleger vom 11.08. schon einmal
            # geschlossen. Rueckfall ist die leere Klammer.
            try:
                from face_audit import _insightface_sessions_gekappt
            except Exception as _ke:                      # noqa: BLE001
                import contextlib as _ctx
                print(f"  (Vorpruefung ungekappt — Kappungs-Klammer nicht "
                      f"ladbar: {type(_ke).__name__}: {_ke})", file=sys.stderr)

                def _insightface_sessions_gekappt():
                    return _ctx.nullcontext()
            with _insightface_sessions_gekappt():
                app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"],
                                   allowed_modules=["detection"])
                app.prepare(ctx_id=-1, det_size=(320, 320))
            # Thread-Kappung (#21) wie Embedder._to_backend auf cpu: die prepare()-Session
            # kaeme sonst mit ungekapptem Default-Pool (hardware_concurrency des Wirts).
            # Ersatz NACH prepare() aus der zentralen Quelle. EIGENER try (Widerleger
            # 11.08.): der Ersatz ist Optimierung — scheitert er, laeuft der Vorpruefer
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
        import numpy as np
        img = cv2.imdecode(np.frombuffer(daten, np.uint8), cv2.IMREAD_COLOR)
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


def _profilbild(ref_id):
    """Die Bytes des Profilbilds eines Satzes (Lese-Stufe d, geprueft) und sein Dateiname fuer Frigate.
    -> (Bytes, '<ref_id>.<Endung des Profilbilds>'); fehlt das Bild oder stimmt seine Pruefsumme nicht:
    FileNotFoundError mit Klartext (ein Bild-Fehler, _fehler_einstufen)"""
    from core import refquelle as _rq
    bild = _rq.read_image(_rq_cfg(), ref_id, "profil") or {}
    if bild.get("daten") is None or bild.get("fehler"):
        grund = bild.get("fehler") or bild.get("fehlt") or "set not visible"
        raise FileNotFoundError(f"profile picture of reference set {ref_id[:12]} not readable ({grund})")
    return bild["daten"], ref_id + os.path.splitext(bild["datei"])[1]


def _pruefen_gecacht(ref_id, cache, neu=None):
    """Vorpruefungs-Urteil je Satz AUS dem Cache (Schluessel ref_id; seit E3b-3a ohne mtime, ein Satz
    ist unveraenderlich), sonst frisch auf den Profilbild-Bytes gerechnet (.133). Frisch Gerechnetes
    landet im neu-Dict des AUFRUFERS (.134 Review-SOLL: nie mehr die ganze Cache-Datei
    zurueckschreiben — _cache_mischen mischt unter Lock, parallele Laeufe
    verlieren einander nichts mehr). Fail-open-Urteile (Detektor nicht ladbar,
    Einzelfehler) und ein nicht lesbares Profilbild werden NIE gemerkt.
    -> (ok, grund)"""
    alt = cache.get(ref_id) or (neu or {}).get(ref_id)
    if alt:
        return bool(alt.get("ok", True)), str(alt.get("grund") or "")
    try:
        daten, _name = _profilbild(ref_id)
    except FileNotFoundError as e:
        return False, str(e)
    ok_bild, grund = _gesicht_pruefen(daten)
    if grund == "__failopen__":
        return True, ""
    if _VORPRUEFER != "aus" and neu is not None:
        neu[ref_id] = {"ok": ok_bild, "grund": grund}
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
    Saetze ohne Urteil (je ref_id, auf den Profilbild-Bytes; seit E3b-3a) und schreibt seinen
    Fortschritt fuer die UI mit.
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
    for i, (_person, rid) in enumerate(offen):
        _pruefen_gecacht(rid, cache, neu)
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

    .133 auswahl = [(person, ref_id), …] -> SELEKTIVER Sync: nur diese Kandidaten,
    Reihenfolge, Toleranz und Bericht sonst identisch (die Auswahl-Seite schickt
    das, was der Nutzer angehakt hat). auswahl=None = Voll-/Auto-Export; der
    ueberspringt die bewusst ABGEWAEHLTEN Bilder still, aber gezaehlt
    (bericht['abgewaehlt_n'] — nie ein stiller Verlust).
    Seit E3b-3a: Kandidaten sind Saetze (person, ref_id); gesendet werden die Profilbild-Bytes des
    Satzes als <ref_id>.<Endung>; nach erfolgreichem register eine Merker-Zeile MERKER_EXPORT im
    Katalog; Bericht und Fortschritt fuehren Person und ref_id."""
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
    for i, (p, rid) in enumerate(kandidaten):
        if not dry:
            _progress(phase="export", modus="export", total=total, done=i, current=p, ref_id=rid)
        # Merker-Vermerk: WOHIN exportiert wurde. Das ZIEL_API-Praefix ist der
        # Beweis der API-Aera (Frigate benennt um) — abgleich() liest es (.137).
        ziel = f"{ZIEL_API}/api/faces/{p}"
        if dry:
            print(f"  [dry] exportiere {p}/{rid[:12]}")
            continue
        # .134 Review-MUSS: die Vorpruefung filtert NUR den Voll-/Auto-Export.
        # Ein auf der Auswahl-Seite bewusst angehaktes Bild schlaegt sie IMMER —
        # 'Frigates Urteil ist die Wahrheit, unser Detektor darf kein Bild
        # endgueltig aussperren' (Seiten-Versprechen); Ablehnungen faengt der
        # Bild-Fehlerpfad darunter mit Frigates echtem Grund.
        if auswahl is None:
            ok_bild, grund = _pruefen_gecacht(rid, cache, neu_urteile)
            if not ok_bild:                        # Vorpruefung: gar nicht erst senden
                bericht["uebersprungen"].append({"person": p, "ref_id": rid,
                                                 "fehler": f"pre-check: {grund}"})
                print(f"  uebersprungen {p}/{rid[:12]}: pre-check: {grund}", file=sys.stderr)
                continue
        try:
            daten, name = _profilbild(rid)
            api_upload(p, name, daten, person_existiert=p in vorhanden)
        except SystemExit:
            raise
        except Exception as e:
            art, kurz = _fehler_einstufen(e)
            if art == "fatal":
                fatal(kurz)
            bericht["uebersprungen"].append({"person": p, "ref_id": rid, "fehler": kurz})
            print(f"  uebersprungen {p}/{rid[:12]}: {kurz}", file=sys.stderr)
            merk = _ablehnung_merken(e)
            if merk:
                # .137/.138: NUR ein echtes Bild-Urteil aus /register wird
                # gemerkt (400 unbefristet, 500-unklar mit Verfall) — nie ein
                # Vorpruefungs-Skip, kein lokaler Datei-, create- oder
                # Transportfehler (Panel-MUSS: sonst sperrt ein Frigate-
                # Ausfall den ganzen Stapel dauerhaft aus). Zeitpunkt: _merken.
                neu_abl[rid] = {"fehler": kurz, "art": merk}
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
        weg_abl.append(rid)                     # .137: geklappt -> Merker erledigt
        bericht["exportiert"] += 1
        # .133: WELCHE Bilder durchkamen, nicht nur wie viele — die Auswahl-Seite
        # zeigt je Bild 'uploaded' bzw. Frigates Ablehnungsgrund aus dem Bericht.
        bericht["exportiert_liste"].append({"person": p, "ref_id": rid})
        _merken(rid, MERKER_EXPORT, {"ziel": ziel, "person": p})
        print(f"  exportiert: {p}/{rid[:12]}")
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
        # .133: die Auswahl kommt als DATEI, nie als argv — hunderte Paare
        # [Person, ref_id] (seit E3b-3a, Laufprotokoll I3) sprengen jede
        # Kommandozeile (und der Dienst muesste sie quoten). Fehlt/kaputt =
        # Klartext-Stopp, nie ein nackter Traceback.
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
