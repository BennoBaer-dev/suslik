"""core/personlauf — PE1 Baustein 3b: Lauf anlegen + fahren (Person Learn).

anlegen() bindet EINMAL (Architektur-Entscheid stand.md): nutzt die
Prototyp-Kette (prototyp/ernte_lauf: arbeit_bestimmen, standort/lichtphase)
— auf der Projektmaschine identische Datenlage (deckung.jsonl im
data_dir/state, Frigate via FRIGATE_URL). Fuer den Versand-Build wird der
Import spaeter durch den eingebackenen Port ersetzt (stufe2.md PE1/5).

fahren() laeuft die events_liste inline ab (Selbst-Simulation, User-Mandat
04.08.) — dieselbe Funktion kann der Dienst spaeter je Event als Worker-Job
ausfuehren. Zustand: <data_dir>/state/personlauf.json (atomar, schema 1)."""
import json
import os
import sys
import time

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _proto():
    # Container-Bruecke: die gestagte Kette liest die Werkstatt aus ENV
    # (SUSLIK_WERKSTATT, Volume-Pfad) — Verzeichnis anlegen, bevor die
    # Module es beim Import nutzen. Lokal greift der Prototyp-Pfad.
    d = os.environ.get("SUSLIK_WERKSTATT") \
        or os.path.join(WURZEL, "prototyp", "daten")
    os.makedirs(os.path.realpath(d), exist_ok=True)
    sys.path.insert(0, os.path.join(WURZEL, "prototyp"))
    import ernte_lauf as el
    # ENV-Bruecke (#18): szenario_ernte friert FRIGATE beim Import ein — hier
    # bei jedem Eintritt auf den aktuellen ENV-Stand heben (der Dienst
    # exportiert die im UI gespeicherte URL beim Config-Laden nach os.environ).
    el.se.FRIGATE = (os.environ.get("FRIGATE_URL", "")
                     or el.se.FRIGATE).rstrip("/")
    return el


def zustand_pfad(data_dir):
    return os.path.join(data_dir, "state", "personlauf.json")


def zustand_schreiben(data_dir, z):
    p = zustand_pfad(data_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(z, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def zustand_lesen(data_dir):
    p = zustand_pfad(data_dir)
    if not os.path.exists(p):
        return None
    return json.load(open(p))


FENSTER_FALLBACK_TAGE = 19   # historischer Festwert bis .141 — greift nur
                             # noch, wenn die Frigate-Config nicht lesbar ist
                             # (diagnose.fenster_quelle = 'fallback')


def _kamera_tage(knoten):
    """Ernte-Grenze eines Config-Knotens (Kamera oder global) in Tagen.
    Die Ernte braucht je Event Snapshot UND Clip (pfad_snapshots:
    snapshot-clean.webp + Record-Clip) — massgeblich ist das MINIMUM aus
    Snapshot-Retention (objects.person-Override VOR default; an der
    laufenden 0.18 verifiziert 06.08.) und Record-Retention
    (alerts/detections). None = nichts Verwertbares im Knoten."""
    werte = []
    sr = (knoten.get("snapshots") or {}).get("retain") or {}
    sp = (sr.get("objects") or {}).get("person")
    werte.append(sp if sp is not None else sr.get("default"))
    rec = knoten.get("record") or {}
    for art in ("alerts", "detections"):
        werte.append(((rec.get(art) or {}).get("retain") or {}).get("days"))
    werte = [w for w in werte
             if isinstance(w, (int, float)) and not isinstance(w, bool)
             and w > 0]
    return max(1, int(min(werte))) if werte else None


def _fenster_aus_config(c):
    """(fenster_tage, je_kamera) aus einer /api/config-Antwort.
    Frigate 0.18 liefert die Kamera-Knoten fertig aufgeloest (Globals
    einkopiert) — je Kamera ihre eigene Grenze; das Gesamtfenster ist das
    MAXIMUM (eine kurz vorhaltende Kamera beschneidet nur sich selbst,
    nie die anderen). Ohne Kamera-Knoten: globale Werte."""
    je_kamera = {}
    for name, cam in (c.get("cameras") or {}).items():
        t = _kamera_tage(cam or {})
        if t:
            je_kamera[name] = t
    if je_kamera:
        return max(je_kamera.values()), je_kamera
    return _kamera_tage(c), {}


def fenster_bestimmen(timeout=10):
    """Ernte-Fenster = was Frigate noch VORHAELT (User-Entscheid 06.08.:
    der Wunsch-N ist der einzige Regler; das Fenster ist ein Retention-
    Waechter, kein zweiter — der Festwert 19 schnitt bei Retention 30
    Material ab und erntete bei person-Snapshots 15 tote Tage).
    Rueckgabe (tage, quelle, je_kamera); nicht lesbar -> Fallback."""
    basis = (os.environ.get("FRIGATE_URL") or "").rstrip("/")
    if basis:
        try:
            import urllib.request
            with urllib.request.urlopen(basis + "/api/config",
                                        timeout=timeout) as r:
                tage, je_kamera = _fenster_aus_config(json.load(r))
            if tage:
                return tage, "frigate-config", je_kamera
        except Exception:
            pass
    return FENSTER_FALLBACK_TAGE, "fallback", {}


def anlegen(data_dir, n_events, person="", tage=None):
    """Lauf anlegen: binden, Liste schreiben. person=""=alle.
    person="FREMD" (.147, reservierter Name): statt der bestaetigten
    Durchgaenge wird der FREMD-Topf der Einordnung geerntet (Quellen
    fremd_verdacht / zonenlos_ohne_anker / strasse_pur — alles VERDACHT,
    der User stempelt in der Abnahme). tage=None -> Fenster aus der
    Frigate-Retention; expliziter Wert (CLI/Tests) gilt unveraendert."""
    if tage is None:
        tage, fenster_quelle, je_kamera = fenster_bestimmen()
    else:
        fenster_quelle, je_kamera = "aufruf", {}
    el = _proto()
    je_eid, fremd, ev_index, api, bilanz = el.arbeit_bestimmen(tage)
    standort = el.standort_lesen()
    jetzt = time.time()
    ab = jetzt - tage * 86400
    # Bestands-Skip (User-Frage 04.08.: hinzugefuegt, nie ueberschrieben —
    # und keine Duplikate): Events, die in FRUEHEREN Laeufen schon Bilder
    # mit Urteil haben, werden uebersprungen; GELOESCHTE Events duerfen
    # bewusst wiederkommen (Re-Lauf nach Loeschung).
    from core import personernte as pe
    fremd_lauf = person == "FREMD"
    belegt = set()
    for _lid, zeilen in pe.laeufe_lesen(data_dir):
        for z in zeilen:
            if "ausfall" not in z and z.get("status") in (
                    "abgenommen", "verworfen", "offen"):
                belegt.add(z["eid"])
    if fremd_lauf:
        # Alt-Bestand des Pools ohne Lauf-Zeile (prototyp-Aera): die
        # Pool-Dateinamen tragen die eid (<tag>_<eid>~N.<ext>) — solche
        # Events nicht erneut anbieten.
        try:
            for f in os.listdir(os.path.join(data_dir, "personlern",
                                             "fremd")):
                belegt.add(f.split("_", 1)[-1].split("~")[0])
        except FileNotFoundError:
            pass
    # Verwaiste Labels (Issue #18, Carl/Rose-Fall): Bestaetigungen GELOESCHTER
    # Personen bleiben als Historie in der Akte — die Alle-Ernte bietet sie
    # aber NICHT mehr an. Personen-Universum = Referenz-Master (faces/), die-
    # selbe Quelle wie die Wizard-Auswahl (master_persons). Uebersprungenes
    # wird GEZAEHLT ausgewiesen (diagnose.verwaiste_labels), nie still. Eine
    # EXPLIZIT gewaehlte Person filtert nicht (der Wizard bietet nur
    # Existierende an; ein bewusster Direkt-Aufruf bleibt moeglich).
    try:
        _fd = os.path.join(data_dir, "faces")
        vorhanden = {p for p in os.listdir(_fd)
                     if os.path.isdir(os.path.join(_fd, p))}
    except FileNotFoundError:
        vorhanden = set()
    verwaist = {}
    im_fenster = []
    topf = fremd if fremd_lauf else je_eid
    for e in topf:
        ev = ev_index[e]
        if ev["start"] < ab:
            continue
        # Kamera-eigene Grenze: wo die eigene Retention kuerzer ist als das
        # Gesamtfenster, waeren aeltere Events garantierte Ausfaelle
        # (Snapshot/Clip schon geraeumt) — nur DIESE Kamera schneidet sie.
        grenze = je_kamera.get(ev["camera"])
        if grenze and ev["start"] < jetzt - grenze * 86400:
            continue
        if not fremd_lauf:
            p = je_eid[e][0]
            if person:
                if p != person:
                    continue
            elif p not in vorhanden:
                verwaist[p] = verwaist.get(p, 0) + 1
                continue
        im_fenster.append(e)
    eids = sorted((e for e in im_fenster if e not in belegt),
                  key=lambda e: -ev_index[e]["start"])[:n_events]
    liste = []
    for eid in eids:
        p, bindung, pk = topf[eid]
        ev = ev_index[eid]
        phase, hoehe = el.lichtphase(ev["start"], standort)
        liste.append({"eid": eid,
                      # FREMD einheitlich (Gruppierung/Training); der
                      # Durchgang bleibt ueber pass_key rekonstruierbar,
                      # die Quelle steht in bindung.
                      "person": "FREMD" if fremd_lauf else p,
                      "bindung": bindung,
                      "pass_key": pk, "kamera": ev["camera"],
                      "start": ev["start"],
                      "zones": (api.get(eid) or {}).get("zones"),
                      "lichtphase": phase, "sonnenhoehe": hoehe})
    lauf_id = "P" + time.strftime("%Y%m%d_%H%M%S")
    # Diagnose fuer die 0-Events-Erklaer-Karte (User-Fund 05.08., zwei
    # reale Referenz-Personen: Lauf endete stumm, Nutzer sah kein WARUM):
    # bindbar im Fenster vs. durch Bestands-Skip belegt; bei 0 bindbaren
    # zusaetzlich der letzte bestaetigte Auftritt aus der Akte (oder nie).
    diagnose = {"fenster_tage": tage, "fenster_quelle": fenster_quelle,
                "gebunden_fenster": len(im_fenster),
                "durch_bestand": len(im_fenster) - len(
                    [e for e in im_fenster if e not in belegt])}
    if len(set(je_kamera.values())) > 1:
        diagnose["fenster_je_kamera"] = dict(sorted(je_kamera.items()))
    if verwaist:
        diagnose["verwaiste_labels"] = dict(sorted(verwaist.items()))
    if person and not fremd_lauf and not im_fenster:
        # Ehrlichkeits-Nachschau (User-Einwand 05.08., zwei reale Faelle:
        # 'die waren doch da'): (a) Akten-Beginn ausweisen — aeltere
        # Besuche KENNT die Akte nicht; (b) 'gesehen, aber unter der
        # Bestaetigungs-Schwelle' zaehlen — da gewesen ist nicht bestaetigt.
        zuletzt, akte_seit, schwach = 0, 0, 0
        try:
            with open(os.path.join(data_dir, "state", "deckung.jsonl")) as f:
                for zeile in f:
                    try:
                        d = json.loads(zeile)
                    except ValueError:
                        continue
                    t0 = d.get("start") or d.get("ts") or 0
                    if t0:
                        akte_seit = min(akte_seit or t0, t0)
                    if person in (d.get("bestaetigt") or []):
                        zuletzt = max(zuletzt, t0)
                    else:
                        o = (d.get("ours") or {}).get(person) or {}
                        if (o.get("max") or 0) >= 0.3:
                            schwach += 1
        except OSError:
            pass
        diagnose["zuletzt_bestaetigt"] = zuletzt or None
        diagnose["akte_seit"] = akte_seit or None
        diagnose["gesehen_schwach"] = schwach
    z = {"schema": 1, "lauf_id": lauf_id, "person": person,
         "wunsch_n": n_events, "phase": "ernte",
         "events": len(liste), "events_liste": liste,
         "bilanz": {k: int(v) for k, v in bilanz.items()},
         "diagnose": diagnose,
         "ts": time.time()}
    zustand_schreiben(data_dir, z)
    return z


EVENT_ZEITWACHE_S = 120   # haengende Events (User-Fund 04.08.: Lauf fror bei
                          # 0% CPU ein) werden Ausfall statt Lauf-Blockade


def fahren(data_dir, z, fortschritt=None):
    """events_liste inline abarbeiten (Resume ueber Manifest-eids).
    Je Event eine ZEITWACHE (Extraktion im Hilfs-Thread, hartes Timeout —
    der haengende Thread bleibt als Daemon zurueck, der Lauf lebt weiter
    und das Manifest nennt den Haenger). Abbruch: Seite setzt phase=
    'abbruch', wird vor jedem Event gelesen; Geerntetes bleibt."""
    import concurrent.futures as cf
    from core import personernte as pe
    el = _proto()
    import pfad_snapshots
    from pose_wache import PoseWache
    wache = PoseWache()

    def extraktor(eid):
        pool = cf.ThreadPoolExecutor(max_workers=1)
        fut = pool.submit(pfad_snapshots.event_verarbeiten, {"eid": eid})
        try:
            return fut.result(timeout=EVENT_ZEITWACHE_S)
        except cf.TimeoutError:
            pool.shutdown(wait=False)
            raise RuntimeError(f"Zeitwache {EVENT_ZEITWACHE_S}s (Event haengt)")
        finally:
            pool.shutdown(wait=False)

    fertig = pe.fertig_eids(data_dir, z["lauf_id"])
    offen = [j for j in z["events_liste"] if j["eid"] not in fertig]
    ok = bilder = 0
    abgebrochen = False
    for k, job in enumerate(offen, 1):
        akt = zustand_lesen(data_dir) or {}
        if akt.get("phase") == "abbruch":
            abgebrochen = True
            break
        r = pe.ernte_event(data_dir, z["lauf_id"], job, wache, extraktor)
        ok += 1 if r["ok"] else 0
        bilder += r.get("bilder", 0)
        if fortschritt:
            # jedes Event melden (User-Fund 04.08.: bei ~20 s je Event war
            # der 5er-Takt minutenlang stumm)
            fortschritt(k, len(offen), ok, bilder)
    # 0 Bilder = nichts zu reviewen -> direkt fertig, Wizard bleibt frei
    # (User-Fund 04.08.: 0er-Lauf sperrte das Formular hinter einem
    # sinnlosen Review)
    z["phase"] = "abnahme" if bilder else "fertig"
    z["geerntet"] = bilder
    if not bilder:
        z["abgenommen"] = 0
        z["verworfen"] = 0
    if abgebrochen:
        z["abgebrochen"] = True
    zustand_schreiben(data_dir, z)
    return {"events": len(offen), "ok": ok, "bilder": bilder,
            "abgebrochen": abgebrochen}


if __name__ == "__main__":
    dd = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WURZEL,
                                                           "verify_data")
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    person = sys.argv[3] if len(sys.argv) > 3 else ""
    z = anlegen(dd, n, person)
    print(f"Lauf {z['lauf_id']}: {z['events']} Events fuer "
          f"'{person or 'alle'}'", flush=True)
    r = fahren(dd, z, lambda k, n2, ok, b: print(
        f"  {k}/{n2} Events, {b} Bilder", flush=True))
    print(f"FERTIG: {r}", flush=True)
