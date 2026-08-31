"""core/kalibfueller — der ON-DEMAND-FUELLER der Kalibrier-Seite
(User-Entscheid 31.08.: "Knopf 'frisches Material holen' startet einen
Mini-Ernte-Lauf ueber die LETZTEN Person-Events DIESER Kamera").

WOZU: Der Kalibrier-Vorrat fuellt sich im Betrieb von selbst — aus dem
Live-Waechter und (seit dem Zentral-Umbau) aus jeder Ereignis-Ernte. Beides
braucht aber Zeit und einen Durchgang vor der Kamera. Wer JETZT kalibrieren
will, soll nicht warten muessen: dieser Lauf holt die letzten Person-Events
der Kamera nach und legt je Event das beste Gesicht in den Ring.

ZWEI STOPP-BEDINGUNGEN, beide verbindlich (Design-Vorgabe):
  * Ziel-Bilderzahl erreicht  ODER
  * Event-Deckel verbraucht
Was zuerst eintritt, beendet den Lauf — er laeuft nie ewig. Beide Werte
kommen aus der Config (kalib_fueller_bilder / kalib_fueller_events), nicht
von hier.

MAGERE AUSBEUTE IST EIN ERGEBNIS, keine Panne: "aus 50 Ereignissen kamen 3
Bilder" ist die ehrliche Auskunft, dass diese Kamera kaum verwertbare
Gesichter liefert — genau die Diagnose, die der Nutzer fuer seine
Erwartungshaltung braucht. Deshalb wird die Bilanz IMMER angezeigt, auch
(und gerade) wenn sie klein ist.

BAUFORM: Muster des Pass-Checks in klein (verifyd._bruecke_ernte) — ein
Hintergrund-Thread, ein Worker-Job je Event, Fortschritt als Modul-Stand,
den die Seite pollt. Die schweren Teile werden INJIZIERT (Kontrakt wie
core.personlauf.fahren): dieses Modul kennt weder Worker noch Frigate noch
den Dienst-Lock — es kennt nur die Reihenfolge und die zwei Stopp-Regeln.

GEZAEHLT WIRD AM RING, nicht an einer Job-Antwort: die Ernte meldet ihre
Vorrats-Bilder bewusst nicht ueber die Zaehler-Transportlisten zurueck
(SK3), und der Ring hat einen Deckel — bei vollem Ring waechst seine Laenge
nicht mehr. Gezaehlt werden deshalb die Eintraege, die NACH dem Start
entstanden sind (der Index traegt je Bild seinen Zeitstempel). Damit stimmt
die Bilanz auch dann, wenn der Ring gleichzeitig aeltere Bilder verliert."""
import threading
import time

# Ein Lauf zur Zeit, prozessweit. Zwei parallele Fueller wuerden sich nur um
# denselben Worker-Slot streiten und die Fortschritts-Anzeigen beider
# verlangsamen; die ehrliche Antwort ist "eine Kamera nach der anderen".
_LOCK = threading.Lock()
_STAND = {}          # kamera -> Stand-Dict (siehe _neuer_stand)
_AKTIV = {"kamera": None}


def _neuer_stand(kamera, n_events, ziel):
    return {"kamera": kamera, "laeuft": True, "i": 0, "n": int(n_events),
            "bilder": 0, "ziel": int(ziel), "grund": "", "fehler": "",
            "ts": round(time.time(), 1)}


def stand(kamera):
    """Der Stand EINES Fuellers -> Dict oder None (nie gelaufen). Der Stand
    bleibt nach dem Ende stehen: die Seite soll die Bilanz noch lesen
    koennen, auch wenn der Nutzer erst spaeter hinschaut."""
    return _STAND.get(str(kamera))


def laeuft_gerade():
    """-> Kameraname des laufenden Fuellers oder None."""
    return _AKTIV["kamera"]


def _zaehlen(vorrat_lesen, t0):
    """Bilder, die SEIT t0 im Ring gelandet sind (s. Modulkopf)."""
    try:
        return sum(1 for e in (vorrat_lesen() or [])
                   if float(e.get("ts") or 0) >= t0)
    except Exception:                                       # noqa: BLE001
        return 0


def starten(kamera, ziel, deckel_events, events_holen, ernte_job,
            vorrat_lesen, log=print, abschluss=None):
    """Fueller starten -> (ok, msg). Laeuft im Hintergrund; der Fortschritt
    kommt ueber stand().

    events_holen()      -> [{"id","start_time","has_clip"}, ...] juengste
                           zuerst (im Dienst: core.ereignisse.person_events
                           mit kameras=[kamera])
    ernte_job(eid, ts)  -> Antwort-Dict des Worker-Jobs (der Aufrufer kennt
                           Slot-Regeln, Timeouts und den Live-Vorrang)
    vorrat_lesen()      -> die Ring-Liste dieser Kamera
    abschluss()         -> wird IMMER am Ende gerufen (auch nach einem
                           Fehler): der Aufrufer raeumt damit seinen
                           Ernte-Ordner weg. Ein Fehler darin ist eine
                           Log-Zeile, nie ein zweiter Fehler.
    """
    kamera = str(kamera or "")
    if not kamera:
        return False, "camera name missing"
    ziel, deckel_events = int(ziel or 0), int(deckel_events or 0)
    if ziel <= 0 or deckel_events <= 0:
        # Ohne beide Stopp-Bedingungen wuerde der Lauf entweder nie oder
        # sofort enden — dann lieber gar nicht starten und es sagen.
        return False, "top-up limits are not configured (see Advanced)"
    with _LOCK:
        if _AKTIV["kamera"]:
            return False, (f"a top-up run for '{_AKTIV['kamera']}' is still "
                           f"going — one camera at a time")
        _AKTIV["kamera"] = kamera
        _STAND[kamera] = _neuer_stand(kamera, 0, ziel)
    threading.Thread(
        target=_lauf, name="kalib-fueller", daemon=True,
        args=(kamera, ziel, deckel_events, events_holen, ernte_job,
              vorrat_lesen, log, abschluss)).start()
    return True, "started"


def _lauf(kamera, ziel, deckel_events, events_holen, ernte_job, vorrat_lesen,
          log, abschluss=None):
    t0 = time.time()
    st = _STAND[kamera]
    try:
        events = list(events_holen() or [])[:deckel_events]
        # Ohne Clip kein Frame — solche Events wuerden nur Zeit kosten. Sie
        # fallen VOR dem Zaehler heraus, damit "aus N Events" die Zahl der
        # wirklich versuchten meint (has_clip fehlt = mitnehmen und es den
        # Job entscheiden lassen; nur ein ausdrueckliches False fliegt raus).
        events = [e for e in events if e.get("has_clip") is not False]
        st["n"] = len(events)
        if not events:
            st["grund"] = "keine"
            return
        for i, ev in enumerate(events, 1):
            antwort = ernte_job(str(ev.get("id")),
                                float(ev.get("start_time") or 0))
            st["i"] = i
            st["bilder"] = _zaehlen(vorrat_lesen, t0)
            st["ts"] = round(time.time(), 1)
            if antwort is not None and not antwort.get("ok"):
                # Ein einzelnes Event ohne Clip/mit Fehler beendet den Lauf
                # NICHT (der naechste kann liefern), aber es bleibt sichtbar.
                st["fehler"] = str(antwort.get("fehler") or "")[:120]
            if st["bilder"] >= ziel:
                st["grund"] = "ziel"
                break
        else:
            st["grund"] = "events"
    except Exception as e:                                  # noqa: BLE001
        st["grund"] = "fehler"
        st["fehler"] = f"{type(e).__name__}: {e}"[:160]
        log(f"calibration top-up {kamera}: {type(e).__name__}: {e}")
    finally:
        st["bilder"] = _zaehlen(vorrat_lesen, t0)
        st["laeuft"] = False
        st["ts"] = round(time.time(), 1)
        if abschluss is not None:
            try:
                abschluss()
            except Exception as e:                          # noqa: BLE001
                log(f"calibration top-up {kamera}: cleanup failed "
                    f"({type(e).__name__}: {e})")
        with _LOCK:
            _AKTIV["kamera"] = None
        log(f"CALIBRATION TOP-UP {kamera}: {st['bilder']} picture(s) from "
            f"{st['i']} of {st['n']} event(s) — stopped: {st['grund'] or '?'}"
            + (f" [{st['fehler']}]" if st["fehler"] else ""))
