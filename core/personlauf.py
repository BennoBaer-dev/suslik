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


def anlegen(data_dir, n_events, person="", tage=19):
    """Lauf anlegen: binden, Liste schreiben. person=""=alle."""
    el = _proto()
    je_eid, fremd, ev_index, api, bilanz = el.arbeit_bestimmen(tage)
    standort = el.standort_lesen()
    ab = time.time() - tage * 86400
    # Bestands-Skip (User-Frage 04.08.: hinzugefuegt, nie ueberschrieben —
    # und keine Duplikate): Events, die in FRUEHEREN Laeufen schon Bilder
    # mit Urteil haben, werden uebersprungen; GELOESCHTE Events duerfen
    # bewusst wiederkommen (Re-Lauf nach Loeschung).
    from core import personernte as pe
    belegt = set()
    for _lid, zeilen in pe.laeufe_lesen(data_dir):
        for z in zeilen:
            if "ausfall" not in z and z.get("status") in (
                    "abgenommen", "verworfen", "offen"):
                belegt.add(z["eid"])
    im_fenster = [e for e in je_eid if ev_index[e]["start"] >= ab
                  and (not person or je_eid[e][0] == person)]
    eids = sorted((e for e in im_fenster if e not in belegt),
                  key=lambda e: -ev_index[e]["start"])[:n_events]
    liste = []
    for eid in eids:
        p, bindung, pk = je_eid[eid]
        ev = ev_index[eid]
        phase, hoehe = el.lichtphase(ev["start"], standort)
        liste.append({"eid": eid, "person": p, "bindung": bindung,
                      "pass_key": pk, "kamera": ev["camera"],
                      "start": ev["start"],
                      "zones": (api.get(eid) or {}).get("zones"),
                      "lichtphase": phase, "sonnenhoehe": hoehe})
    lauf_id = "P" + time.strftime("%Y%m%d_%H%M%S")
    # Diagnose fuer die 0-Events-Erklaer-Karte (User-Fund 05.08., zwei
    # reale Referenz-Personen: Lauf endete stumm, Nutzer sah kein WARUM):
    # bindbar im Fenster vs. durch Bestands-Skip belegt; bei 0 bindbaren
    # zusaetzlich der letzte bestaetigte Auftritt aus der Akte (oder nie).
    diagnose = {"fenster_tage": tage, "gebunden_fenster": len(im_fenster),
                "durch_bestand": len(im_fenster) - len(
                    [e for e in im_fenster if e not in belegt])}
    if person and not im_fenster:
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
