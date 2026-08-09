"""szenarien — die EINE Szenario-Gruppierung des Tages (Paket B / 0.1.0.49).

Byte-treu aus dem /heute-Render gezogen (Strukturaenderung, ausdruecklich benannt —
Spec 02_today §S3): dieselbe Logik beliefert jetzt /heute UND /auftritte. Neues Modul
nach der E6c-Regel (Neu-Code nicht in den Monolithen). Verhalten unveraendert; Beweis:
normalisierter HTML-Diff der /heute-Seite eines ABGESCHLOSSENEN Tages vor/nach dem
Schnitt (identisch) + synthetische qs-S2-Stufe (Gruppen-Schnitt inkl. ende_ts-Praeferenz).
"""
import time


# GESPEICHERTE Label-Werte (gt_leiste schreibt 'Fremd'/'unklar'; die Buttons ZEIGEN
# "Stranger"/"?" — Review-Fund .54: die Anzeige-Texte standen faelschlich im Code und
# matchten nie; an den Echtdaten verifiziert: 10x 'Fremd', 7x 'unklar' im Bestand).
GT_OFFEN_LABELS = ("Fremd", "unklar")
GT_KEIN_MENSCH = "kein_mensch"   # Issue #16: manuelles 'keine Person'-Urteil —
# schliesst das Event (nicht in GT_OFFEN_LABELS), Anzeige-Text lebt in gt_leiste


def _gt_offen(gtmap, eid):
    """F2: zaehlt dieses gelabelte Event weiter als offen/unbekannt? Kein Label -> ja.
    'Fremd'/'unklar' -> ja (Fremder bleibt Fremder, unklar bleibt offen). Personen-Label
    -> nein (beurteilt). Set-Aufrufer behalten das alte Verhalten (Label = raus)."""
    if isinstance(gtmap, dict):
        lbl = gtmap.get(eid)
        return lbl is None or lbl in GT_OFFEN_LABELS
    return eid not in gtmap


def pass_key(by_h, eid, cfg, gtmap=None, now=None):
    """Der Szenario-Schluessel EINES Events: die Startzeit des DURCHGANGS, zu
    dem es gehoert, in ganzen Sekunden ("%d") — dieselbe Schreibweise, die die
    Lern-Kette schon fuehrt (core/personlauf.py: pass_key aus dem ersten Event
    eines Durchgangs). None = das Event liegt in keiner Gruppe.

    Gruppiert wird NICHT neu: die Antwort faellt aus szenarien_des_tages, der
    EINEN Gruppierung dieses Projekts (gap, ende_ts-Praeferenz, Tagesgrenze).
    Eine zweite Gap-Rechnung waere das Streu-Literal, das qs_ebenen.md
    verbietet — und ein Durchgang, der auf zwei Seiten anders geschnitten
    wird, ist genau der Szenario-Fehler, den CLAUDE.md als wiederkehrend
    fuehrt. Aufrufer: verifyd._kontroll_speicher (Z8, Ablage je Pass)."""
    import datetime
    r = (by_h or {}).get(eid)
    t0 = (r.get("start") or r.get("ts") or 0) if r else 0
    if not t0:
        return None
    tag = datetime.datetime.fromtimestamp(t0).replace(
        hour=0, minute=0, second=0, microsecond=0)
    for s in szenarien_des_tages(by_h, tag.timestamp(),
                                 (tag + datetime.timedelta(days=1)).timestamp(),
                                 cfg, {} if gtmap is None else gtmap, now=now):
        if any(e.get("eid") == eid for e in s.get("evs") or []):
            return "%d" % round(s["start"])
    return None


def szenarien_des_tages(by_h, heute0, tag_ende, cfg, gtmap, now=None, nur_kameras=None,
                        koerper_map=None, koerper_ab=2):
    """rows-Sicht eines Tages -> Szenarien-Liste (neueste zuerst). by_h = last-wins je eid;
    gtmap = Label-Map eid->letztes Label (F2, .54): Personen-Label = beurteilt/raus,
    'Fremd'/'unklar' (Speicherwerte!) = bleibt sichtbar unbekannt. Ein SET wird akzeptiert
    (Alt-Aufrufer: Mitgliedschaft = altes Raus-Verhalten).
    nur_kameras (Areas Stufe 1 v2, 30.07.): Kamera-Menge einer Area-Sicht. Die Sicht
    WAEHLT Durchgaenge AUS (behalten wird jeder Durchgang, der mindestens ein Event
    auf einer Sicht-Kamera hat) — sie projiziert NICHT hinein: Kette, Urteil
    (pers/unbek/kat), Zeiten, laeuft und Kameras bleiben property-weit (I2/Szenario-
    Prinzip; der Widerleger .91 bewies am Beispiel, dass eine hineinprojizierte Sicht
    einen erkannten Durchgang als 'Unbekannten' rendert — genau der dokumentierte Fehler, aus einem
    Teil eines Durchgangs auf die ganze Person zu schliessen).
    None = Identitaet (All-Sicht)."""
    now = now if now is not None else time.time()
    # --- Szenarien bilden: zeitlich benachbarte Events = EIN Durchgang (User 20.07.) ---
    import collections as _coll
    gap = int(cfg.get("szenario_gap_min", 5)) * 60
    # (Review .50: die Extraktion hatte hier ein zweites `now = time.time()` aus dem
    # Original mitgenommen, das den now-Parameter tot machte — entfernt; Verhalten fuer
    # now=None identisch, injiziertes now wirkt jetzt wirklich [qs-S2 testet das].)
    karenz = int(cfg.get("szene_karenz_s", 90))   # Durchgang gilt erst nach Karenz als abgeschlossen (User 21.07.)
    heute_evs = sorted((r for r in by_h.values()
                        if heute0 <= (r.get("start") or r.get("ts") or 0) < tag_ende),
                       key=lambda r: (r.get("start") or r.get("ts") or 0))
    grp, cur = [], None
    for e in heute_evs:
        t = e.get("start") or e.get("ts") or 0
        # Paket A: echtes Frigate-Event-Ende bevorzugen (maschinenunabhaengiger
        # Schnitt); dauer_s (Analyse-Wanduhr) nur noch als Fallback fuer
        # Bestands-Zeilen von vor 0.1.0.48.
        ende = e.get("ende_ts") or (t + (e.get("dauer_s") or 0))
        if cur and t - cur["ende"] <= gap:
            cur["evs"].append(e); cur["ende"] = max(cur["ende"], ende)
        else:
            cur = {"start": t, "ende": ende, "evs": [e]}; grp.append(cur)
    szenarien = []
    for g in grp:
        pers, unbek, noface = {}, 0, 0
        unbek_stark = 0        # Issue #16 Automatik: unerkannte Events MIT
        # ernstzunehmendem Gesicht (fremd_verdacht bzw. User-Fremd-Label);
        # ein Pass, dessen Unbekannte alle nur schwach sind, bekommt die
        # stille Klasse statt Warn-Plakette/Unknown-Karte.
        gt_fremd = False
        unbek_eid = None
        unbek_eids = []          # ALLE unerkannten Events des Durchgangs, s.u.
        kams = _coll.OrderedDict()
        ev_liste = []                      # /auftritte (.50, additiv): Events des Durchgangs
        evs_g = sorted(g["evs"], key=lambda x: (x.get("start") or x.get("ts") or 0))
        if nur_kameras is not None:        # Areas: AUSWAHL, keine Projektion (s. Docstring)
            if not any(str(x.get("camera", "?")) in nur_kameras for x in evs_g):
                continue
        for x in evs_g:
            cam = str(x.get("camera", "?"))
            ev_liste.append({"eid": x.get("eid"), "t": x.get("start") or x.get("ts") or 0, "cam": cam,
                             "conf": list(x.get("bestaetigt") or [])})
            best = x.get("bestaetigt") or []
            ours = x.get("ours") or {}
            cl = kams.setdefault(cam, {"n": 0, "erk": _coll.Counter(),
                                       "eid": {}, "unbek": 0, "bw": 0, "unbek_eid": None,
                                       "bw_eid": None})
            cl["n"] += 1
            # bw_eid = Event mit der groessten Gesichtskante der Kamera — Ziel des
            # Video-Buttons der Zeile (Anforderung: EIN Klick, bester Clip; die
            # px-Anzeige der Zeile stammt vom selben Event).
            _bw = x.get("max_bw") or 0
            if x.get("eid") and (_bw > cl["bw"] or cl["bw_eid"] is None):
                cl["bw_eid"] = x.get("eid")
            cl["bw"] = max(cl["bw"], _bw)
            if best:
                xt = x.get("start") or x.get("ts") or 0
                for p in best:
                    mx = (ours.get(p) or {}).get("max", 0)
                    d = pers.setdefault(p, {"count": 0, "best": 0, "eid": None,
                                            "letzt_t": 0, "letzt_cam": None,
                                            "erst_t": xt})
                    d["count"] += 1
                    # Erste BESTAETIGUNG dieser Person, nicht der Szenario-Start (Fund
                    # 25.07.): ein Durchgang beginnt mit Bewegung, die Person wird oft
                    # Minuten spaeter erst erkannt. Gemessen an heute: 5 Bestaetigungen
                    # lagen >60 s hinter dem Start; ein Durchgang begann 09:20:39, die Person
                    # war erst 09:26:09 bestaetigt. Die Seite behauptete trotzdem
                    # "since 09:20" — eine Zeit, zu der niemand wusste, wer da kommt.
                    d["erst_t"] = min(d["erst_t"], xt)
                    if mx >= d["best"]:
                        d["best"], d["eid"] = mx, x.get("eid")
                    # Zuletzt gesehen = letztes Event, in dem DIESE Person bestaetigt
                    # wurde. Nicht die zuletzt hinzugekommene Kamera des Durchgangs:
                    # die kann eine sein, auf der die Person nie bestaetigt war (Fund
                    # 25.07.: angezeigt wurde die letzte Kamera des Durchgangs,
                    # bestaetigt war die Person zuletzt 5 min frueher woanders).
                    if xt >= d["letzt_t"]:
                        d["letzt_t"], d["letzt_cam"] = xt, cam
                    cl["erk"][p] += 1
                    cl["eid"].setdefault(p, x.get("eid"))
            elif (x.get("faces_geprueft", x.get("faces", 0)) > 0
                  or (isinstance(gtmap, dict) and gtmap.get(x["eid"]) == "Fremd")) and \
                    _gt_offen(gtmap, x["eid"]):   # #42 Teil B: gefilterte Zahl; F2: Label-KLASSE
                # entscheidet; ein User-'Fremd'-Label haelt das Event auch dann sichtbar,
                # wenn der fd-Filter alle Detektionen frisst (User-Urteil schlaegt Filter).
                unbek += 1; cl["unbek"] += 1
                if x.get("kategorie") == "fremd_verdacht" or (
                        isinstance(gtmap, dict) and gtmap.get(x["eid"]) == "Fremd"):
                    unbek_stark += 1
                if isinstance(gtmap, dict) and gtmap.get(x["eid"]) == "Fremd":
                    gt_fremd = True          # F2/A2: vom User bestaetigter Fremder (Badge)
                # ALLE unerkannten Events sammeln, nicht nur das erste (Fund 25.07.).
                # Die Zuordnung zum Unbekannt-Pool lief ueber `unbek_eid`, also ueber das
                # zeitlich ERSTE Event des Durchgangs — und ausgerechnet das ist oft das
                # schlechteste (Person kommt von hinten, Gesicht halb im Bild). Kannte der
                # Pool die Person ueber ein spaeteres Event, stand auf der Karte trotzdem
                # "not grouped yet". Das ist der Szenario-Fehler, den CLAUDE.md als
                # wiederkehrend benennt: aus EINEM Event geschlossen statt aus dem
                # ganzen Durchgang.
                unbek_eids.append(x.get("eid"))
                unbek_eid = unbek_eid or x.get("eid")
                cl["unbek_eid"] = cl["unbek_eid"] or x.get("eid")
            else:
                noface += 1
        if not pers and koerper_map:
            # ZUSCHREIBUNG via Koerper-Strang (User 05.08., Fusion Schritt 1):
            # kein Gesicht im ganzen Durchgang, aber der Personen-Strang kennt
            # die Person ueber mehrere Events (>= koerper_ab Stuetzen, Pendant
            # zur Feuer-Regel) -> der Pass GEHOERT ihr: Karte zaehlt ihn, kein
            # "no known person", kein Unknown-Besucher-Kandidat. quelle=
            # "koerper" haelt die Urteilsquelle fuer die Anzeige unterscheidbar;
            # Gesichts-Urteile je Event bleiben unangetastet.
            khits = {}
            for x in evs_g:
                t3 = koerper_map.get(x.get("eid"))
                if t3 and t3.get("person"):
                    khits.setdefault(t3["person"], []).append((x, t3))
            for p, hits in khits.items():
                if len(hits) < koerper_ab:
                    continue
                _xt = lambda x: x.get("start") or x.get("ts") or 0
                beste_x, beste_t = max(hits, key=lambda ht: ht[1].get("score") or 0)
                pers[p] = {"count": len(hits),
                           "best": beste_t.get("score") or 0,
                           "eid": beste_x.get("eid"),
                           "erst_t": min(_xt(x) for x, _ in hits),
                           "letzt_t": max(_xt(x) for x, _ in hits),
                           "letzt_cam": str(max(hits, key=lambda ht: _xt(ht[0]))[0]
                                            .get("camera", "?")),
                           "quelle": "koerper"}
            if pers:
                # Zugeschriebene Passe verlassen den Unbekannt-Topf der SEITE
                # (der persistente Pool/Reconcile bleibt Gesichts-Sache).
                unbek_eids, unbek_eid = [], None
        kat = ("gemischt" if pers and unbek else "erkannt" if pers
               else "unbekannt" if unbek else "motion")
        letzte_akt = max((x.get("start") or x.get("ts") or 0) for x in evs_g)  # Erkennungszeit, NICHT Verarbeitungs-ts: sonst faelscht ein Verarbeitungs-Lag (Neustart-Sweep/Last) beendete Durchgaenge zu "in progress"
        szenarien.append({"start": g["start"], "ende": g["ende"], "n": len(evs_g),
                          "pers": pers, "unbek": unbek, "unbek_stark": unbek_stark,
                          "kat": kat, "kams": kams,
                          "unbek_eid": unbek_eid, "unbek_eids": unbek_eids,
                          "evs": ev_liste, "gt_fremd": gt_fremd,
                          "laeuft": (now - letzte_akt) < karenz})
    szenarien.sort(key=lambda s: -s["start"])              # neueste oben
    return szenarien
