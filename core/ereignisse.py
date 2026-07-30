"""core/ereignisse — Frigate-Event-Abruf mit ECHTER Pagination (E1; Konzept §P0.2:
der Bestand fragte mit limit=200 ohne Folgeseiten — genau diese Luecke schliesst
dieses Modul). Reine Logik: der HTTP-Zugriff kommt als hole(pfad)-Callable herein
(im Dienst: api(cfg, pfad)), dadurch ohne Netz testbar."""


MAX_SEITEN = 200          # Deckel (Widerleger F2.1): 200 Seiten x 200 = 40.000 Events —
#                           mehr zieht kein Lernlauf; schuetzt Request-Threads + Frigate.


def person_events(hole, anzahl=None, kameras=None, seite=200, max_seiten=MAX_SEITEN):
    """Die juengsten `anzahl` person-Events (None = ALLE bis Historien-Ende), notfalls
    ueber MEHRERE Seiten (before-Cursor auf start_time). -> (events, seiten_geholt).
    Duplikat-sicher UND verlustfrei am Gleichstand-Cursor (Widerleger F2.6: Frigate
    filtert before strikt '<'; Cursor = min + 1 µs, Duplikate faengt die id-Menge).
    max_seiten deckelt hart — nie unbegrenzt im Request-Thread (F2.1)."""
    events, gesehen, seiten = [], set(), 0
    before, limit = None, min(seite, 1000)
    ziel = anzahl if anzahl is not None else float("inf")
    while len(events) < ziel and seiten < max_seiten:
        pfad = f"/api/events?labels=person&limit={limit}"
        if kameras:
            pfad += "&cameras=" + ",".join(kameras)
        if before is not None:
            pfad += f"&before={before}"
        batch = hole(pfad) or []
        seiten += 1
        neu = [e for e in batch if e.get("id") not in gesehen]
        for e in neu:
            gesehen.add(e.get("id"))
        events.extend(neu)
        if len(batch) < limit:
            break                                   # Historien-Ende
        if not neu:
            # Volle Seite, nichts Neues: Gleichstand-Gruppe groesser als das Fenster
            # (Widerleger F2.6-Nachspiel: der Epsilon-Cursor allein bliebe hier stehen).
            # Fenster eskalieren, bis die Gruppe hineinpasst; 1000 ist das API-Maximum.
            if limit >= 1000:
                break                               # absurder Grenzfall: >1000 identische ts
            limit = min(limit * 2, 1000)
            continue
        # +1 µs: haelt Events mit IDENTISCHER start_time im naechsten Fenster —
        # die id-Dedupe frisst die Wiederholungen (live gegen Frigate verifiziert).
        before = min(e.get("start_time") or 0 for e in batch) + 1e-6
        limit = min(seite, 1000)                    # nach Fortschritt zurueck auf Normalgroesse
    return (events if anzahl is None else events[:anzahl]), seiten


def auswahl_bilanz(events):
    """Wizard-Ausweis (Konzept §P0.2): Zeitspanne + Clip-Verfuegbarkeit der Auswahl.
    -> dict fuer die Anzeige 'letzte N Events = zurueck bis <aeltester> · davon M mit
    verfuegbarem Clip — K ohne Clip werden uebersprungen'. Ehrlich: hat ein Event kein
    has_clip-Feld, zaehlt es als OHNE Clip (Sicherheits-Semantik, nichts stilles)."""
    mit_clip = [e for e in events if e.get("has_clip") is True]
    zeiten = [e.get("start_time") for e in events if e.get("start_time")]
    return {"n": len(events), "mit_clip": len(mit_clip),
            "ohne_clip": len(events) - len(mit_clip),
            "aeltester_ts": min(zeiten) if zeiten else None,
            "juengster_ts": max(zeiten) if zeiten else None}


def clips_fuer_prognose(events, aufloesungen_je_kamera=None, cache_pruefer=None):
    """Events -> Prognose-Eingabe fuer core.wanduhr.lauf_prognose():
    [{'clip_s':…, 'aufloesung':…, 'im_cache':bool}]. Cliplaenge aus end-start
    (fehlendes Ende -> 0 = nur Fixkosten, ehrlich konservativ); Aufloesung aus der
    Kamera-Zuordnung (None -> globaler k-Rueckfall); im_cache via Callable."""
    aus = []
    for e in events:
        if e.get("has_clip") is not True:
            continue                                 # uebersprungene zaehlt die Bilanz aus
        t0, t1 = e.get("start_time"), e.get("end_time")
        clip_s = max((t1 - t0), 0.0) if (t0 and t1) else 0.0
        aufl = (aufloesungen_je_kamera or {}).get(e.get("camera"))
        im_cache = bool(cache_pruefer(e.get("id"))) if cache_pruefer else False
        aus.append({"clip_s": clip_s, "aufloesung": aufl, "im_cache": im_cache})
    return aus
