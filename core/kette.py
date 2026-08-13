"""core/kette — die ERKENNUNGSKETTE als eigenes Modul (Modulumbau R2, modulplan.md #2).

Byte-treu aus verifyd.py ausgezogen (Runde R-2026-08-11-modulbau-r2, Basis 35913fb):
das HEUTIGE Verhalten ist die eingefrorene Default-Kette — keine neue Semantik,
keine neuen Config-Schluessel. Beweis: tools/harnisch_r2.py (Logik-Harnisch,
Basis-Stand gegen Umbau-Stand ueber eine Fixture-Matrix, plus Mutations-Probe).

DIE EINE STRUKTUR (Andock-Ziel konzept_kette_seite.md): `DEFAULT_KETTE` traegt
Stufen, Reihenfolge und Bedingungen der heutigen Kette als Daten. Die spaetere
Ketten-Config-Seite wird reine UI auf dieses Modul: sie liest DEFAULT_KETTE
(welche Stufen, welcher Config-Schluessel, welche Bedingungs-Quelle, welcher
Entscheid-Zeitpunkt), zeigt `lage(cfg)` als Ist-Zustand und schreibt ueber den
bestehenden Config-Weg (CONFIG_WHITELIST, Enum KETTE_STUFEN) — ein Kern-Umbau
ist dafuer nicht mehr noetig. "Nur Vision"/freie Reihenfolge waeren dann
Ketten-DATEN; die Auslöse-Logik dazu ist bewusst NICHT Teil dieses Auszugs
(Charakterisierungs-Garantie: byte-identisch vertraegt keine zweite Semantik).

EINHAENGE-PUNKTE im Dienst (verifyd.py), unveraendert in Lage und Reihenfolge:
  (a) process() VOR der Analyse  — Quelle-Gate Person: stufe()=="aus" schaltet
      den Koerper-Strang an der Quelle ab (kein --koerper im Analyse-Job);
  (b) process() NACH der Analyse — entscheide() ueber das Person-Urteil
      (Bedingungs-Quelle ist das PASS-Urteil, Mehr-Personen-Regel B);
  (c1) _vision_anstossen — Quelle-Gate Vision: stufe()=="aus" verhindert den
      Debounce-Timer (die Stumm-Dedup-Map je Durchgang bleibt Service-Zustand);
  (c2) _vision_faellig — entscheide() am DURCHGANGS-Ende (erst dort steht das
      Pass-Urteil fest, Szenario-Prinzip).

INJEKTION PUR (Muster core/selfcheck.py): dieses Modul importiert verifyd NIE.
Config (dict), Log-Pfad, log/debug-Callables und die Store-/Mess-Funktionen des
Dienstes kommen als Parameter — genau die Schnittstelle, die die Ketten-Seite
spaeter liest/schreibt. Es haelt KEINE Locks und KEINEN eigenen Zustand;
insbesondere nimmt deckung_by_eid() self.lock des Dienstes NICHT (auf dieser
Invariante steht der with-Block von _deckung_korrektur in verifyd.py).
"""
import json
import os
import time


# Ketten-Schalter (Issue #21): die DREI Stufen je Erkennungs-Weg — EINE Quelle
# fuer Default-Pruefung (stufe), Whitelist-Enum und damit die Settings-UI
# (Deckungs-Vertrag statt Streu-Literal, qs_ebenen.md). Die Slugs bleiben
# deutsch, weil sie Datenwerte sind (Config-Store) — wie telegram_modus.
KETTE_STUFEN = ["immer", "nur_wenn_gesicht_leer", "aus"]


# Die Default-Kette als DATEN (heutiges Verhalten, eingefroren): je Stufe der
# Erkennungs-Weg, sein Config-Schalter (None = heute nicht abschaltbar), die
# erlaubten Stufen, die Scharf-Quelle (was der Weg zusaetzlich zum Schalter
# braucht, s. lage()), die Bedingungs-Quelle der Stufe "nur_wenn_gesicht_leer"
# (IMMER das Pass-Urteil, nie das Einzel-Event — Szenario-Prinzip) und der
# Zeitpunkt, zu dem der Entscheid faellt. Reihenfolge der Tupel = Reihenfolge
# der Kette. Verbraucher heute: stufe() (Schalter-Schluessel), die Doku der
# Einhaenge-Punkte oben; Verbraucher morgen: die Ketten-Config-Seite.
DEFAULT_KETTE = (
    {"stufe": "gesicht", "schalter": None, "stufen": ("immer",),
     "scharf_quelle": None, "bedingung": None, "zeitpunkt": "event"},
    {"stufe": "person", "schalter": "person_pfad", "stufen": tuple(KETTE_STUFEN),
     "scharf_quelle": "personmodell", "bedingung": "gesicht_pass_bestaetigt",
     "zeitpunkt": "event"},
    {"stufe": "vision", "schalter": "vision_pfad", "stufen": tuple(KETTE_STUFEN),
     "scharf_quelle": "vision_aktiv", "bedingung": "gesicht_pass_bestaetigt",
     "zeitpunkt": "durchgangs_ende"},
)

_SCHALTER = {g["stufe"]: g["schalter"] for g in DEFAULT_KETTE if g["schalter"]}


def stufe(cfg, weg):
    """Ketten-Schalter (Issue #21): die konfigurierte Stufe eines
    Erkennungs-Wegs ("person" | "vision"). EINE Ausleseart fuer die
    Quell-Hooks UND /health (K1: die Anzeige speist sich aus derselben
    Quelle wie das Verhalten). Ein hand-editierter Store mit fremdem
    Wert faellt auf den Default "immer" zurueck — das ist das heutige
    Verhalten, nie ein stilles Abschalten."""
    w = str(cfg.get(_SCHALTER.get(weg, f"{weg}_pfad")) or "immer")
    return w if w in KETTE_STUFEN else "immer"


def koerper_scharf(data_dir):
    """Hat der User den Koerper-Strang scharf geschaltet? EINE Auskunft
    fuer beide Fragesteller: den Job-Parameter --koerper VOR der Analyse
    (Z5) und das Urteil danach (_person_live)."""
    try:
        from core import personmodell as pm
        st = pm.status_lesen(data_dir)
    except Exception:
        return False
    return bool(st and st.get("scharf"))


def lage(cfg):
    """K1-Auskunft fuer /health: je Erkennungs-Weg die konfigurierte
    Stufe UND die tatsaechliche Scharf-Lage. "wirksam" sagt, ob der Weg
    im Live-Betrieb ueberhaupt automatisch anlaufen kann — aus DENSELBEN
    Praedikaten, die die Quell-Hooks benutzen (stufe, koerper_scharf,
    vision.aktiv): keine zweite Wahrheit."""
    p, v = stufe(cfg, "person"), stufe(cfg, "vision")
    scharf = koerper_scharf(cfg["data_dir"])
    aktiv = bool((cfg.get("vision") or {}).get("aktiv"))
    return {"person": {"stufe": p, "modell_scharf": scharf,
                       "wirksam": scharf and p != "aus"},
            "vision": {"stufe": v, "aktiv": aktiv,
                       "wirksam": aktiv and v != "aus"}}


def entscheide(stufen_wert, pass_bestaetigt):
    """Der Stufen-Entscheid der Default-Kette an den zwei Pass-Urteil-Punkten
    (Einhaenge b und c2): "laufen" | "aus" | "gesicht_bestaetigt".
    `pass_bestaetigt` ist ein Callable und wird NUR fuer die Stufe
    "nur_wenn_gesicht_leer" ausgewertet (lazy — exakt die Auswertungs-
    Reihenfolge der frueheren Inline-Bedingungen in process()/_vision_faellig;
    "immer" und "aus" ruehren das Pass-Urteil nie an). Konservative Richtung
    bleibt erhalten: ein Fehler im Pass-Urteil liefert False -> "laufen"."""
    if stufen_wert == "aus":
        return "aus"
    if stufen_wert == "nur_wenn_gesicht_leer" and pass_bestaetigt():
        return "gesicht_bestaetigt"
    return "laufen"


def deckung_by_eid(log_path, entry=None):
    """deckung.jsonl als last-wins-Map je eid (dieselbe Leseart wie
    /heute) — EINE Quelle fuer alle Pass-Fragen (Kontroll-Speicher,
    Ketten-Schalter). `entry` ueberlagert die eigene, noch nicht
    geschriebene Zeile des laufenden Events."""
    by_eid = {}
    try:
        with open(log_path) as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if r.get("eid"):
                    by_eid[r["eid"]] = r      # last-wins je eid (wie /heute)
    except FileNotFoundError:
        pass
    if entry and entry.get("eid"):
        by_eid[entry["eid"]] = entry          # unsere Zeile wird erst NACH uns geschrieben
    return by_eid


def gesicht_pass_bestaetigt(cfg, log_path, debug, eid=None, entry=None, pass_key=None):
    """Ketten-Stufe "nur_wenn_gesicht_leer" (Issue #21): hat der
    GESICHTS-Weg diesen Durchgang restlos bestaetigt? Antwort aus dem
    Pass-Urteil der EINEN Szenario-Gruppierung (szenarien_des_tages,
    dieselbe Quelle wie /heute und der Kontroll-Speicher — kein zweites
    Streu-Urteil): bestaetigt heisst s["kat"] == "erkannt", also
    mindestens eine Person bestaetigt UND kein Event mit brauchbarem,
    aber unbestaetigtem Gesicht. Das IST Mehr-Personen-Regel B
    (stand.md-Empfehlung) auf PERSONEN-Ebene: laeuft neben der
    erkannten Person noch ein ungeklaertes Gesicht mit, ist der Pass
    "gemischt" und der teure Weg faehrt (Regel A wuerde ihn schon bei
    einer erkannten Person schlafen legen). Events OHNE brauchbares
    Gesicht zaehlen dabei nicht als zweite Person — dass eine erkannte
    Person auf anderen Kameras auch mal ohne Gesicht auftaucht, ist der
    Normalfall eines Durchgangs (Szenario-Prinzip: das Pass-Urteil
    traegt, nicht das Einzel-Event).
    "gemischt"/"unbekannt"/"motion", kein Durchgang bestimmbar oder
    Lesefehler -> False, der Weg faehrt. Konservativ in GENAU diese
    Richtung: lieber einmal zu viel gerechnet als eine unerkannte
    Person verpasst.
    Adressierbar per eid (Person-Weg, Event-Zeitpunkt) ODER pass_key
    (Vision-Weg, Durchgangs-Ende)."""
    try:
        import datetime as _dt
        import szenarien as _sz
        by_eid = deckung_by_eid(log_path, entry)
        if pass_key is not None:
            t0 = float(pass_key)
        else:
            r = by_eid.get(eid) or {}
            t0 = r.get("start") or r.get("ts") or 0
        if not t0:
            return False
        tag = _dt.datetime.fromtimestamp(t0).replace(
            hour=0, minute=0, second=0, microsecond=0)
        for s in _sz.szenarien_des_tages(
                by_eid, tag.timestamp(),
                (tag + _dt.timedelta(days=1)).timestamp(), cfg, {}):
            if (("%d" % round(s["start"])) == str(pass_key)
                    if pass_key is not None
                    else any(e.get("eid") == eid
                             for e in s.get("evs") or [])):
                return s.get("kat") == "erkannt"
        return False
    except Exception as e:
        debug(f"chain gate: face-pass check failed ({e}) — path runs")
        return False


def kontroll_speicher(cfg, log_path, debug, eid, entry=None):
    """Z8 (konzept_frames.md §7): der Auftrag an den Kontroll-Speicher fuer
    DIESES Event — Betriebsmodus aus der Config (diagnostic_collection;
    schlank ist der Produkt-Default) und der DURCHGANG, zu dem das Event
    gehoert. Der pass_key kommt aus szenarien.pass_key, also aus derselben
    Gruppierung wie /heute; die App leistet die Szenario-Bildung selbst,
    damit niemand je Einzel-Event nachsehen muss (Szenario-Prinzip).
    None = kein Durchgang bestimmbar -> lieber gar nichts ablegen als je
    Einzel-Event, das waere genau der Fehler, den das Prinzip verbietet."""
    try:
        import szenarien as _sz
        by_eid = deckung_by_eid(log_path, entry)      # EINE Leseart (s. dort)
        pk = _sz.pass_key(by_eid, eid, cfg)
        if not pk:
            return None
        return {"sammeln": bool(cfg.get("diagnostic_collection")),
                "pass_key": pk,
                "karenz_s": int(cfg.get("szenario_gap_min", 5)) * 60}
    except Exception as e:
        debug(f"{eid}: control store not addressable ({e})")
        return None


KETTE_AUTO_MARKER = "kette_auto.json"          # klebriger Erst-Boot-Entscheid (Muster placement.json)
KETTE_AUTO_WERTE = {"person_pfad": "nur_wenn_gesicht_leer", "vision_pfad": "aus"}
# Neutralwerte der drei Auto-Schalter — die user_gesetzt-Erkennung vergleicht den
# WIRKSAMEN cfg-Wert (Store UND yaml) gegen genau diese Defaults. cpu_threads gehoert
# seit dem Tokn59-Befund dazu (#21: der Deckel senkt ohne gesetzten Wert nichts,
# weil die Affinitaets-Maske auf 2C/4T schon 4 meldet — erst der Wert 'physische
# Kerne' drueckt die Pools wirklich); sein Auto-Wert ist die MESSUNG selbst.
KETTE_AUTO_DEFAULTS = {"person_pfad": "immer", "vision_pfad": "immer", "cpu_threads": 0}


def auto_default(cfg, log_path, log, *, store_pfad, store_laden, store_schreiben,
                 phys_kerne, min_kerne_default):
    """Auto-Default der Ketten-Schalter aus der MESSUNG statt aus der Image-Variante
    (.173, User-Go 10.08./11.08.): eine Maschine, die schwach misst, bekommt beim
    ERSTEN Start dieser Version person_pfad='nur_wenn_gesicht_leer',
    vision_pfad='aus' und cpu_threads=<gemessene physische Kerne> vorbelegt — der
    teuerste lokale Posten ist der Person-Weg, Vision laeuft ueberwiegend extern,
    und die Image-Variante sagt ueber die Leistung nichts (cpu-Image kann auf
    12 Kernen laufen). cpu_threads dazu (#21-Befund): der 0-Default kappt nur auf
    die Affinitaets-Maske und senkt auf SMT-Kisten nichts. Schwach =
    phys_kerne() < wanduhr_min_kerne (Config-Paar, Default = Struktur-Axiom
    WANDUHR_MIN_KERNE, dieselbe Quelle wie das Wanduhr-Gate) — ein tieferer
    Betriebsmesswert existiert beim allerersten Boot noch nicht, und gerade
    unter dieser Grenze wird die Wanduhr nie messen. Der Entscheid faellt GENAU
    EINMAL (Marker state/kette_auto.json haelt ihn fest, auch den Nicht-Eingriff)
    und NUR wenn der User keinen der drei Schalter je gesetzt hat (Store oder
    yaml). REVISION User 11.08.: das fruehere Bestandskriterium
    (deckung.jsonl/setup_done) ist BEWUSST raus — die Zielgruppe sind gerade die
    BESTANDS-Tester (Tokn59-Klasse, 2C/4T laeuft seit Wochen), das Feature kommt
    mit .173 zum ersten Mal, alte Detect-Werte kann es nicht geben; 'nicht still'
    traegt die SICHTBARKEIT, nicht das Installations-Alter. bestand steht nur
    noch als Doku im Marker. Sichtbar: laute Startlog-Zeile, config_audit-Zeile mit
    auto-Vermerk und der Settings-Hinweis aus auto_hinweise, solange der
    Auto-Wert unveraendert steht. Scheitern ist laut und folgenlos (Defaults
    bleiben, wie sie sind).

    Modulumbau R2: Injektion pur — store_pfad/store_laden/store_schreiben und
    phys_kerne sind die EINEN Dienst-Funktionen (verifyd reicht sie herein,
    keine Duplikate), min_kerne_default ist das Struktur-Axiom WANDUHR_MIN_KERNE."""
    angewendet = False
    tmp = None
    try:
        marker = os.path.join(cfg["data_dir"], "state", KETTE_AUTO_MARKER)
        if os.path.exists(marker):
            return
        store_datei = store_pfad(cfg)
        store = store_laden(cfg)
        # BLOCKER-Wache (Widerleger 11.08.): existiert die Store-Datei, liest sich aber
        # leer, ist sie UNLESBAR (load_config warnt dann bereits: "do NOT let the store
        # be overwritten!") — dann NICHTS schreiben, auch keinen Marker: der Entscheid
        # faellt ehrlich neu, wenn der Store wieder lesbar ist. Sonst zerstoerte der
        # Auto-Default hier die komplette Config samt Meldekanal-Secrets (os.replace,
        # kein Rueckweg) — stiller Verlust in genau der Zielpopulation dieses Features.
        if not store and os.path.exists(store_datei):
            log("chain auto-default skipped: config store exists but reads empty/"
                "unreadable — not touching it (no marker; decision retried next boot)")
            return
        # User-Wille = WERT weicht vom Neutralwert ab — in Store ODER yaml (Widerleger
        # E1 + Revisions-Recheck 2a): blosse Schluessel-Praesenz im Store zaehlt NICHT,
        # denn der Settings-Save schreibt ALLE Whitelist-Keys mit ihren aktuellen
        # (Neutral-)Werten in den Store; sonst fiele der Auto-Default fuer jeden aus,
        # der je auf Save geklickt hat — ausgerechnet die aktiven Bestands-Tester.
        # Preis (bewusst): wer ausdruecklich den Neutralwert waehlt, ist von 'nie
        # angefasst' nicht unterscheidbar und wird auf schwacher Maschine umgestellt —
        # sichtbar, einmalig, in Settings sofort zurueckstellbar.
        # GANZ-ODER-GAR-NICHT: EIN abweichender Schalter = nichts vorbelegen.
        user_gesetzt = sorted(
            k for k, neutral in KETTE_AUTO_DEFAULTS.items()
            if store.get(k, neutral) != neutral
            or (cfg.get(k) if cfg.get(k) is not None
                else neutral) != neutral)
        # bestand ist seit der Revision (User 11.08.) NUR NOCH Doku im Marker —
        # der Entscheid haengt allein an user_gesetzt + schwach (s. Docstring).
        bestand = os.path.exists(log_path) or bool(store.get("setup_done"))
        # Dieselbe Quelle wie das Wanduhr-Gate (Widerleger F1): das Config-Paar
        # wanduhr_min_kerne (Default = Struktur-Axiom WANDUHR_MIN_KERNE) — wer die
        # Grenze bewusst senkt, senkt sie fuer BEIDE Verbraucher.
        min_kerne = int(cfg.get("wanduhr_min_kerne") or min_kerne_default)
        kerne = phys_kerne()
        schwach = kerne < min_kerne
        info = {"ts": round(time.time(), 1), "kerne": kerne,
                "min_kerne": min_kerne, "schwach": schwach,
                "bestand": bestand, "user_gesetzt": user_gesetzt, "gesetzt": {}}
        if schwach and not user_gesetzt:
            # cpu_threads = die gemessenen PHYSISCHEN Kerne (#21): der 0-Default kappt
            # nur auf die Affinitaets-Maske, die auf SMT-Maschinen die Threads zaehlt
            # (2C/4T -> 4); erst der Kern-Wert drueckt die ORT-Pools real.
            info["gesetzt"] = {**KETTE_AUTO_WERTE, "cpu_threads": kerne}
            store.update(info["gesetzt"])
            store_schreiben(store_datei, store)
            angewendet = True                          # erst NACH dem realen Schreiben (D1)
            cfg.update(info["gesetzt"])                # sofort wirksam, kein Neustart noetig
            # ENV nachziehen: __init__ hat SUSLIK_CPU_THREADS mit dem alten cfg-Wert 0
            # NICHT gesetzt (der cpu_threads-Block dort laeuft vor diesem Aufruf); ohne
            # Nachzug wirkte der Deckel erst nach dem naechsten Neustart.
            os.environ["SUSLIK_CPU_THREADS"] = str(kerne)
            # Kappungs-Cache zuruecksetzen (Recheck-Fund): placement_aufloesen laeuft in
            # load_config VOR diesem Entscheid und kann _ORT_THREADS bereits auf die
            # Affinitaets-Maske eingefroren haben (2C/4T: 4 statt 2). Der Reset laesst
            # alle KUENFTIGEN In-Prozess-Sessions den neuen Deckel ziehen; der gelaufene
            # Placement-Benchmark bleibt unberuehrt. Worker-Subprozesse erben die ENV ohnehin.
            try:
                import face_audit as _fa
                _fa._ORT_THREADS = None
            except Exception:
                pass
            log(f"chain defaults set: measured {kerne} usable physical core(s), "
                f"below the floor of {min_kerne} (wanduhr_min_kerne), first start "
                f"of this version -> person_pfad=nur_wenn_gesicht_leer, "
                f"vision_pfad=aus, cpu_threads={kerne} — defaulted because this "
                f"machine measured weak; change it in Settings anytime")
            # AUDIT VOR dem Marker (Recheck MUSS 1): der Marker ist aus der Audit-Zeile
            # rekonstruierbar (Nachhol-Pfad unten), umgekehrt nicht — scheiterte frueher
            # der Marker, fand der naechste Boot keine Herkunft und schrieb den Entscheid
            # dem User zu. kerne/min_kerne stehen MIT in der Zeile (Recheck MUSS 2):
            # eine Rekonstruktion zitiert die HISTORISCHE Messung, nie die heutige.
            try:
                audit = os.path.join(cfg["data_dir"], "config", "config_audit.jsonl")
                os.makedirs(os.path.dirname(audit), exist_ok=True)
                with open(audit, "a") as f:
                    f.write(json.dumps({"ts": info["ts"], "aenderungen": info["gesetzt"],
                                        "auto": "weak-machine first-boot default",
                                        "kerne": kerne, "min_kerne": min_kerne},
                                       ensure_ascii=False) + "\n")
                    f.flush()
            except Exception as e:
                log(f"chain auto-default: audit line not written "
                    f"({type(e).__name__}: {e}) — values are in place; if the "
                    f"marker write below also fails, the Settings note is lost")
        elif user_gesetzt:
            # Nachhol-Pfad (Widerleger C1-C7): ein frueherer Boot hat die Werte gesetzt,
            # aber der Marker fehlte (Teilfehler). Die Audit-Zeile mit auto-Vermerk ist
            # die ehrliche Quelle — steht sie da UND deckt sie exakt die als user_gesetzt
            # erkannten Schalter, traegt der Nachhol-Marker die gesetzt-Info samt
            # DAMALIGER Messung (Recheck MUSS 2) und der Settings-Hinweis bleibt
            # erhalten. Deckt sie sie nicht, bleibt user_gesetzt die ehrliche Deutung.
            try:
                ap = os.path.join(cfg["data_dir"], "config", "config_audit.jsonl")
                if os.path.exists(ap):
                    with open(ap) as af:
                        for line in af:
                            try:
                                d = json.loads(line)
                            except Exception:
                                continue   # eine zerrissene Zeile darf die Suche nicht killen (Recheck-KANN)
                            if d.get("auto") and set(d.get("aenderungen") or {}) == set(user_gesetzt):
                                info["gesetzt"] = dict(d["aenderungen"])
                                info["nachgeholt"] = True
                                if d.get("kerne") is not None and d.get("min_kerne") is not None:
                                    info["kerne"], info["min_kerne"] = d["kerne"], d["min_kerne"]
                                else:
                                    # Alt-Audit ohne Messfelder: lieber KEINE Zahlen als
                                    # die heutigen (der Hinweis laesst die Klammer weg)
                                    info.pop("kerne", None)
                                    info.pop("min_kerne", None)
                                info["schwach"] = True   # der Alt-Entscheid setzte nur bei schwach
            except Exception:
                pass
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        tmp = f"{marker}.tmp-{os.getpid()}"
        with open(tmp, "w") as f:
            json.dump(info, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, marker)
        tmp = None
    except Exception as e:
        # Ehrlich je nach REALEM Fortschritt (D1): angewendet wird erst nach dem
        # erfolgreichen Store-Schreiben wahr.
        was = ("values are set, only the sticky marker failed"
               if angewendet else "defaults unchanged")
        log(f"chain auto-default incomplete ({type(e).__name__}: {e}) — {was}")
    finally:
        if tmp:
            try:
                os.remove(tmp)                         # keine .tmp-Leiche (Widerleger)
            except OSError:
                pass


def auto_hinweise(cfg):
    """Settings-Sichtbarkeit des Auto-Defaults: {key: hinweistext} fuer Schalter, die
    der Erst-Boot-Entscheid gesetzt hat und die der User seither NICHT geaendert hat
    (sonst waere der Hinweis eine Falschaussage ueber den aktuellen Wert)."""
    out = {}
    try:
        mk = json.load(open(os.path.join(cfg["data_dir"], "state",
                                         KETTE_AUTO_MARKER)))
        zahlen = (f" ({mk.get('kerne')} usable physical core(s) < {mk.get('min_kerne')})"
                  if mk.get("kerne") is not None and mk.get("min_kerne") is not None
                  else "")   # nachgeholter Marker ohne historische Zahlen: Klammer weg
        for k, v in (mk.get("gesetzt") or {}).items():
            if cfg.get(k) == v:
                out[k] = (f"auto-defaulted at first start because this machine "
                          f"measured weak{zahlen} — change it here anytime")
    except Exception:
        pass
    return out
