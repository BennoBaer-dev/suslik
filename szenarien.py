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
# .313 GT als MENGE (Tester-Fund 21.08., 'C+R'-Knopf): eine Zeile in ground_truth.jsonl
# traegt zusaetzlich "personen": [...] — die Wahrheit; "label" bleibt fuer ALLE
# Altleser byte-gleich abgeleitet (gt_label_aus_personen). Exklusive Werte: unklar und
# kein_mensch stehen nie neben anderen; Fremd darf Mitglied neben Namen sein
# (Zusteller waehrend der Gartenarbeit ist eine reale Wahrheit). GT_MAX_PERSONEN deckelt
# die Liste, jeder Name einzeln bis PERSON_RE (60) — die alte [:40]-Kappung des
# Kombi-Strings schnitt zwei lange Namen still ab.
GT_EXKLUSIV = ("unklar", GT_KEIN_MENSCH)
GT_MAX_PERSONEN = 10
# schliesst das Event (nicht in GT_OFFEN_LABELS), Anzeige-Text lebt in gt_leiste


def _pass_schluessel(start):
    """DIE eine Schreibweise des Pass-/Render-Schluessels (Startzeit des
    Durchgangs in ganzen Sekunden, "%d") — dieselbe Formel, die die Lern-Kette
    (core/personlauf.py) und die Render-Stellen in verifyd fuehren. Hier
    zentral, damit die Vision-Stimme kein weiteres Streu-Literal anlegt
    (qs_ebenen-Regel: Aufzaehlungen/Formeln aus der einen Quelle)."""
    return "%d" % round(start)


def vision_stimme_gilt(zeile):
    """Qualitaets-Sieb der Vision-STIMME (Fix vision-stimme-2): liefert den
    Personennamen, wenn das JUENGSTE Vision-Urteil eines Durchgangs als
    stimmberechtigte Stuetze taugt — sonst None. Alle Bedingungen kommen aus
    der Urteilszeile SELBST (nichts hardgecodet, ein alter Lauf wird an den
    Regeln gemessen, die er protokolliert hat):

      * Lauf sauber beendet (`abgebrochen` nicht gesetzt) und mit Person;
      * `sammlung` vorhanden und konsistent (sammlung.person == person) —
        Alt-Zeilen ohne sammlung stimmen NICHT;
      * EINDEUTIGER Sieger: strikt mehr Voten als jeder andere Name in
        `verteilung`. core.visionurteil.sammeln kuert bei Gleichstand den
        alphabetisch ersten Namen; mit vision_quote an der Whitelist-
        Untergrenze 0.5 kaeme ein 1:1-Patt als "Urteil" durch — genau das
        faengt diese Pruefung (Befund der .171-Zweitkontrolle);
      * die im Lauf festgehaltenen Regeln halten nach: voten >=
        min_voten_wirksam und anteil >= quote (Werte aus der Zeile)."""
    if not isinstance(zeile, dict) or zeile.get("abgebrochen"):
        return None
    p = zeile.get("person")
    s = zeile.get("sammlung")
    if not p or not isinstance(s, dict) or s.get("person") != p:
        return None
    vert = s.get("verteilung") or {}
    if any(n >= vert.get(p, 0) for q, n in vert.items() if q != p):
        return None
    try:
        if (s.get("anteil") is None
                or int(s.get("voten") or 0) < int(s.get("min_voten_wirksam"))
                or float(s.get("anteil")) + 1e-9 < float(s.get("quote"))):
            return None
    except (TypeError, ValueError):
        return None
    return p


def gt_label_aus_personen(personen):
    """EINE Ableitung des Altfeldes 'label' aus der Menge: [] -> 'unklar' (kein Urteil =
    offen, wie '?'), ein Wert -> der Wert, mehrere -> '+'-verkettet und sortiert (so ist
    'A+B' == 'B+A' dieselbe Wahrheit; Altleser werten jeden Nicht-Offen-Wert als
    'beurteilt')."""
    p = sorted(set(str(x) for x in (personen or []) if str(x)))
    if not p:
        return "unklar"
    return p[0] if len(p) == 1 else "+".join(p)


def gt_personen_aus_label(label, master):
    """Lese-Migration fuer Altzeilen ohne 'personen': reservierte Werte bleiben einzeln,
    ein '+'-String wird gespalten, wenn JEDES Stueck eine Master-Person ist (sonst
    bleibt er als opaker Einzelwert stehen — nie raten). Sortiert."""
    lbl = str(label or "")
    if not lbl:
        return []
    if lbl in GT_OFFEN_LABELS or lbl == GT_KEIN_MENSCH:
        return [lbl]
    teile = [t for t in lbl.split("+") if t]
    if len(teile) > 1 and all(t in master for t in teile):
        return sorted(set(teile))
    return [lbl]


def gt_pruefen(personen, master):
    """Handler-Validierung: Liste aus Master-Personen und/oder reservierten Werten,
    exklusive Werte allein, Deckel GT_MAX_PERSONEN, Namenslaenge je Stueck.
    -> (ok, bereinigte_liste_sortiert, grund)."""
    if not isinstance(personen, (list, tuple)):
        return False, [], "personen muss eine Liste sein"
    p = []
    for x in personen:
        x = str(x).strip()
        if not x or x in p:
            continue
        if len(x) > 60:
            return False, [], "Name zu lang"
        if x not in master and x not in GT_OFFEN_LABELS and x != GT_KEIN_MENSCH:
            return False, [], f"unbekannter Wert {x!r}"
        p.append(x)
    if len(p) > GT_MAX_PERSONEN:
        return False, [], "zu viele Personen"
    if any(x in GT_EXKLUSIV for x in p) and len(p) > 1:
        return False, [], "unklar/kein_mensch stehen allein"
    return True, sorted(p), ""


def gt_laden(pfad, master=None):
    """EINE Lese-Quelle der GT-Datei (statt fuenf handgeschriebener Parser): eid ->
    {'label': <Altfeld, letzte Zeile gewinnt>, 'personen': [...]}. Zeilen ohne
    'personen' werden ueber gt_personen_aus_label migriert (ohne master: nur
    reservierte Werte und Einzelwerte, '+'-Strings bleiben opak). Unlesbare Zeilen
    werden uebersprungen wie bisher."""
    import json as _json
    import os as _os
    out = {}
    if not pfad or not _os.path.exists(pfad):
        return out
    master = set(master or ())
    with open(pfad, encoding="utf-8") as f:
        for l in f:
            try:
                d = _json.loads(l)
                eid, lbl = d["eid"], d["label"]     # KeyError -> Zeile faellt wie in den Alt-Parsern
                pers = d.get("personen")
                if not isinstance(pers, list):
                    pers = gt_personen_aus_label(lbl, master)
                out[eid] = {"label": lbl, "personen": [str(x) for x in pers]}
            except Exception:
                continue
    return out


def gt_labelmap(pfad):
    """Altform eid -> label (letzte Zeile gewinnt), aus derselben Quelle."""
    return {k: v["label"] for k, v in gt_laden(pfad).items()}


def gt_segmente(label):
    """Segmente eines GT-Labels (.313): das abgeleitete Label ist '+'-verkettet
    (gt_label_aus_personen); Personennamen enthalten nie '+' (PERSON_RE). So sieht
    jeder Leser 'Fremd' auch NEBEN einem Namen ('Fremd+Rose') — ohne Master-Liste."""
    lbl = str(label or "")
    return [t for t in lbl.split("+") if t] if lbl else []


def gt_hat_fremd(gtmap, eid):
    """Traegt das GT dieses Events die Fremd-Wahrheit (allein ODER neben Namen)?"""
    return isinstance(gtmap, dict) and GT_OFFEN_LABELS[0] in gt_segmente(gtmap.get(eid))


def _gt_offen(gtmap, eid):
    """F2: zaehlt dieses gelabelte Event weiter als offen/unbekannt? Kein Label -> ja.
    'Fremd'/'unklar' -> ja (Fremder bleibt Fremder, unklar bleibt offen), auch als
    MITGLIED neben Namen (.313: 'Fremd+Rose' heisst 'Rose UND ein Fremder' — der
    Fremde bleibt sichtbar). Reines Personen-Label -> nein (beurteilt). Set-Aufrufer
    behalten das alte Verhalten (Label = raus)."""
    if isinstance(gtmap, dict):
        lbl = gtmap.get(eid)
        if lbl is None:
            return True
        return any(t in GT_OFFEN_LABELS for t in gt_segmente(lbl))
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
            return _pass_schluessel(s["start"])
    return None


def szenarien_des_tages(by_h, heute0, tag_ende, cfg, gtmap, now=None, nur_kameras=None,
                        koerper_map=None, koerper_ab=2, vision_map=None):
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
    None = Identitaet (All-Sicht).
    vision_map (Fix vision-stimme-2): pass_key -> juengstes Vision-Urteil
    (visionurteil.protokoll_karte). None = bei Bedarf selbst laden, s.u."""
    now = now if now is not None else time.time()
    # Vision-STIMME (Fix vision-stimme-2, Rueckweg-Fall 10.08.): das
    # Vision-Urteil eines Durchgangs zaehlt als EINE zusaetzliche Stuetze
    # Richtung koerper_ab, wenn es DIESELBE Person nennt wie der Koerper-Weg
    # (Regeln am Einsatzort unten). vision_map=None laedt die Urteils-Karte
    # selbst — so erben /auftritte und /pass die Stimme ohne eigenen Code
    # (K3-Klasse aus qs_ebenen.md); Aufrufer ohne koerper_map (pass_key,
    # Ketten-Gate _gesicht_pass_bestaetigt, Event-Navigation, qs-Harnische)
    # laden nie und bleiben unberuehrt. Schalter: `vision_stimme` (Default
    # an, load_config-Paar). Ketten-Schalter `vision_pfad=aus` stoppt
    # Vision-LAEUFE an der Quelle — fuer neue Passe entsteht dann keine
    # Urteilszeile und damit keine Stimme; vorhandene bzw. von Hand
    # gestartete Urteile (die der Schalter ausdruecklich weiter erlaubt)
    # behalten ihre Stimme.
    if (vision_map is None and koerper_map
            and cfg.get("vision_stimme", True) and cfg.get("data_dir")):
        try:
            from core import visionurteil as _vu
            vision_map = _vu.protokoll_karte(cfg["data_dir"])
        except Exception:
            vision_map = None
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
                  or gt_hat_fremd(gtmap, x["eid"])) and \
                    _gt_offen(gtmap, x["eid"]):   # #42 Teil B: gefilterte Zahl; F2: Label-KLASSE
                # entscheidet; ein User-'Fremd'-Label haelt das Event auch dann sichtbar,
                # wenn der fd-Filter alle Detektionen frisst (User-Urteil schlaegt Filter).
                unbek += 1; cl["unbek"] += 1
                if x.get("kategorie") == "fremd_verdacht" or (
                        gt_hat_fremd(gtmap, x["eid"])):
                    unbek_stark += 1
                if gt_hat_fremd(gtmap, x["eid"]):
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
            # Vision-STIMME: EIN Urteil je Durchgang = hoechstens EINE
            # Stuetze. Sie zaehlt nur, wenn (a) das Qualitaets-Sieb
            # (vision_stimme_gilt) haelt, (b) die genannte Person EIGENE
            # Koerper-Treffer hat (Vision allein schreibt NIE einen Pass
            # zu), (c) sie der EINDEUTIGE Koerper-Favorit ist — strikt mehr
            # Treffer als jede andere Person. Das ist Widerspruchs-Wache
            # und Patt-Riegel in einem: nennt Vision jemand anderen als den
            # Favoriten, traegt sie nicht (kein Veto, der Favorit behaelt
            # seine eigenen Stuetzen); beim Gleichstand zweier Kandidaten
            # traegt sie ebenfalls nicht (Befund D der .171-Zweitkontrolle:
            # sonst kippte ein Patt unterhalb der Schwelle per Vision zur
            # Falsch-Zuschreibung, wo vorher NIEMAND zugeschrieben wurde).
            # (d) Materialtrennung: das Kandidaten-Gitter des Urteils muss
            # mindestens ein Event DIESES Passes enthalten, das nicht schon
            # als Koerper-Treffer der Person zaehlt — die zweite Stuetze
            # ruht auf eigenem Material, nicht auf denselben Pixeln
            # (koerper_ab=2 soll genau Doppelzaehlung verhindern). Der
            # Schluessel ist der exakte RENDER-Schluessel — dieselbe
            # Leseart wie die Vision-Fussnote der Karte, BEWUSST ohne
            # tolerante Suche (Befund B/C der .171-Zweitkontrolle: eine
            # nur hier tolerante Suche erzeugte Anzeige-Widersprueche und
            # aenderte an 74 Echt-Passen ueber 4 Tage exakt nichts).
            stimme = None
            if khits and vision_map and cfg.get("vision_stimme", True):
                vz = vision_map.get(_pass_schluessel(g["start"])) or {}
                vp = vision_stimme_gilt(vz)
                if vp and vp in khits and all(
                        len(khits[vp]) > len(h)
                        for q, h in khits.items() if q != vp):
                    gitter = {b.get("eid") for b in (vz.get("bilder") or [])
                              if b.get("eid")}
                    pass_eids = {x.get("eid") for x in evs_g}
                    eigene = {x.get("eid") for x, _ in khits[vp]}
                    if (gitter & pass_eids) - eigene:
                        stimme = vp
            for p, hits in khits.items():
                if len(hits) + (1 if p == stimme else 0) < koerper_ab:
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
                if p == stimme and len(hits) < koerper_ab:
                    # Ausweis fuer Anzeige/Nachvollzug: die Vision-Stimme hat
                    # diese Zuschreibung GETRAGEN. Nur wenn die Koerper-
                    # Treffer allein NICHT reichten (len(hits) < koerper_ab)
                    # — dann ist der Ausweis per Konstruktion wahr. Reichte
                    # der Koerper-Weg schon allein, bleibt die Karte bei
                    # "via person recognition" (Befund 1 der Drittkontrolle:
                    # der bedingungslose Ausweis erzaehlte fuer einen fertig
                    # zugeschriebenen Alt-Pass rueckwirkend einen anderen
                    # Zustandekommens-Weg — Klasse "falsche Darstellung").
                    # Quelle bleibt koerper; count bleibt die Zahl der
                    # Koerper-Treffer-Events.
                    pers[p]["vision_stimme"] = True
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
