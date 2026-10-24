"""core/unbekannt_verbraucher — der Verbraucher der Unbekannt-Stapel: liest die Schlange, deckt jede Gruppe eines Stapels
gegen die Unbekannt-Identitaeten, haengt an oder legt neu an und entscheidet die Meldung je Durchgang.

HERKUNFT: Bauplan analysen/bauplan_verbraucher_unbekannt.md (Fassung 2, vom Eigentuemer am 14.10.2026 abgenickt),
Entscheide 10 und 11, Stufe V1a Punkte 3 und 4; Konzept analysen/konzept_unbekannt_weg.md Sollweg 2, 4 und 6; die
Widerleger-Funde W3, W5, W6, W10, W12, W13, W16, W17, W20, W21, W22, W25 und W26
(backups/release3_bau/verbraucher_unbekannt/widerleger.md).

ZWECK: der Kern, den der Verbraucher-Faden des Dienstes (Stufe V1b) je Runde ruft. Hier stehen Schlange, Zustand,
Deckung, Durchgang und Meldungs-Entscheid. Faden, Wecken, Senden der Meldung (MQTT, Telegram) und /health baut V1b.

DIE SCHLANGE: ein Stueck je Tag unter state/, Name aus core.harvest_set.QUEUE_FILE (Tag der Schreibzeit, Ortszeit). Der
Dienst haengt nach der Buchung eines Ereignisses mit Unbekannt-Gruppen eine Zeile an (schlange_anhaengen): Zeit,
Ereignis, Ordner, Zahl der Gruppen, Kamera, Start, Frigate-Ende oder Dauer, max_bw, Nachhol-Merkmal und die im Fenster
erkannten Namen. Kein Umbenennen, kein Packen. Der Verbraucher liest die Stuecke nach Datum, je Stueck ab seinem
Lesestand (Zeile und Byte); ein Stueck wird erst archiviert (nach state/archiv/unbekannt_schlange/), wenn es ganz
gelesen und aelter als aufbewahrung_tage ist. Nichts geht verloren (ED011).

DER ZUSTAND state/unbekannt_verbraucher.json (core/atomar, ED011): Lesestand je Stueck, die gebuchten Ereignisse je
Kette und Tag (fuer den Durchgang) mit den gemeldeten Paaren Durchgang und Identitaet, die faelligen Meldungen mit
Zeitpunkt. Nichts davon lebt nur im Speicher; die Matrix im Speicher ist nur abgeleitet.

JE STAPEL (eine Schlangen-Zeile) unter pool_lock, mit Frist SPERRE_FRIST_S, sonst zurueckgestellt (W21): die Gruppen ueber
harvest_set.event_unknown; zuerst loest eine Wiederholungsanalyse desselben Ereignisses die Bindungen ihres ersten
Laufs, die nicht mehr im Stapel stehen, und verwirft deren Saetze (W6); dann die Deckung je Gruppe; dann die
Schreibfolge Bindungen im Katalog, Identitaetszeile (anlernen._speichere_unbekannte), Zustand mit Lesestand und
Meldungen (W21, W25). Vor dem ersten Stapel raeumt der Verbraucher Bindungen nach, deren Identitaet fehlt (Abbruch
zwischen Bindung und Identitaetszeile).

DECKUNG (deckung, reine Funktion): Kosinus jedes Gesichts der Gruppe zu jedem Mitglied gleichen Modells, je Identitaet
das naechste Mitglied; ab unbekannt_latte haengt die Gruppe an, zuerst an eine Identitaet des offenen Durchgangs, dann
an irgendeine, gleich welcher Status (W20); darunter entsteht eine neue Identitaet. Zwei Gruppen derselben Stapel-Zeile
(eines Clips) kommen nie in dieselbe Identitaet (harte Regel des Workers, W26). Jedes Stapel-Gesicht zaehlt als
Mitglied, ohne zweites Sieb (W22). Mitglieder sind die gebundenen Saetze (core.refquelle.unknown_members) und der
Altbestand: Pool-Zeilen der Liste members, gelesen ueber anlernen.pool_mit_fingerabdruck, nur mit Kante, Detektion und
Frontalitaet nach dem Kandidaten-Tor des Workers (worker_kern.KAND_*, W12). Die Matrix wird neu zusammengesetzt, sobald
sich Katalog-Stand, Identitaetsdatei oder Pool-Datei geaendert haben (W13); die Fingerabdruecke der Saetze sind
unveraenderlich und bleiben dafuer im Speicher.

DURCHGANG: je Ketten-Schluessel (core.areas.ketten_schluessel, Modus je Area) und Tag die gebuchten Ereignisse nach Start
geordnet und mit der EINEN Anhaenge-Regel szenarien.durchgang_anhaengen gekettet (W5); sein Name kommt aus
szenarien._pass_schluessel.

MELDUNG: einmal je Durchgang und Identitaet, faellig szene_karenz_s nach der Verarbeitung; keine fuer Nachhol-Laeufe und
fuer Ereignisse, die bei der Verarbeitung aelter als die Altersgrenze des Aufrufers sind (W3), keine fuer Identitaeten
mit Status besucher oder dem Merkmal objekt (auch nicht, wenn sie es in der Karenz werden). Eine Meldung ist ein dict
(Ereignis, Identitaet, Kamera, Start, max_bw, Fenster-Namen, ref_id des besten Satzes); runde gibt die faelligen zurueck,
sie bleiben im Zustand, bis meldungen_quittieren sie austraegt. Traegt die Identitaet beim Versand das Merkmal „ähnlich zu
P“, faellt die Meldung weg (Bauplan analysen/bauplan_aehnlich.md Entscheid 15, INFO-Zeile).

AUFRAEUM-SCHRITT (Bauplan analysen/bauplan_aehnlich.md Fassung 4, Stufe AE2 Punkt 3, Entscheide 14 und 17; W3 V1 bis V5):
EIN Weg fuer alle Merkmale „ähnlich zu P“. Er laeuft beim Start vor der ersten Runde, nach jeder Runde mit verarbeiteten
Stapeln vor den Meldungen und, wenn die Wache des Fadens (aufraeumen_faellig) andere Grenzen oder ein fremdes Schreiben
der Identitaetsdatei sieht; die eigenen Schreibungen merkt er sich. Kein Ausloeser bei Katalog-Aenderungen. Eingestuft
wird ausserhalb der Sperre (core.aehnlich.einstufen_alle); unter pool_lock mit Frist liest er die Datei frisch und setzt
NUR das Feld des Merkmals (core.aehnlich.merkmale_setzen), geschrieben wird nur bei einer Aenderung. Ohne Sperre binnen
Frist: WARNING, die Wache stoesst den naechsten Lauf an. Ein Lesefehler (core.aehnlich, dazu eine nicht gelesene Zeile der
Identitaetsdatei) aendert kein Merkmal: ERROR-Zeile, /health und health_ok rot bis zum naechsten gelungenen Lauf; die
Stapel laufen weiter. Je Lauf der Zustand in AEHNLICH_DATEI unter state/, je Lauf mit Aenderung eine INFO-Zeile.

SAMMELBECKEN „ÄHNLICH P“ (Bauplan analysen/bauplan_aehnlich.md Fassung 8, Stufe AE6 Punkt 2, Entscheide 23 bis 25 und 29;
W7 V1 bis V6, V10): im Aufraeum-Schritt, nach dem Setzen der Merkmale und unter derselben Sperre (ohne eigene, W7 V1),
fuehrt er je Person P jede Identitaet mit Merkmal P zusammen, deren Durchgang abgeschlossen ist (sammel_plan: keine
vorgemerkte Meldung, letzter Stapel aelter als szene_karenz_s, Fach ZULETZT des Zustands); Ziel ist immer das Sammelbecken
(core.aehnlich.SAMMEL), gibt es keins, die kleinste Nummer darunter. Erst haengen die Saetze um
(anlernen.zusammenlegen_kern), je Identitaet eine Spurzeile in SAMMEL_DATEI, dann EIN Schreibzug der Identitaetsdatei; ein
Abbruch dazwischen laesst Zeilen mit Merkmal stehen, die der naechste Lauf zusammenfuehrt. Ist ein Durchgang noch offen,
stoesst die Wache den Lauf nach der Karenz an (aufraeumen_faellig). Danach nimmt er die Bilder aus Fremder-Durchgaengen aus
den Becken (anlernen.nicht_p_auswahl_kern). Das Sammelbecken ist kein Ziel der Deckung (nicht in der Matrix).

EHRLICHE GRENZEN:
  - Die Durchgaenge bestehen nur aus Ereignissen mit Unbekannt-Gruppen (nur sie stehen in der Schlange); die
    Aktivitaetsseite kettet ueber alle Ereignisse. Eine Luecke ohne Unbekannte kann einen Durchgang teilen: dann zwei
    Meldungen derselben Identitaet, kein Vermengen. Verschiebt ein spaet gebuchtes Ereignis den Start oder verbindet es
    zwei Durchgaenge, haengt durchgang_einordnen Vermerke und offene Meldungen auf den neuen Namen um (je Identitaet
    hoechstens eine, Bauplan analysen/bauplan_neueste_zuerst.md Stufe LZ1); schon versandte Meldungen zweier bis dahin
    getrennter Durchgaenge bleiben versandt, und geaenderte Ereigniszeiten oder Kettungen loest das nicht.
  - Gehalten werden die Buchungen des juengsten Tags und des Vortags (TAGE_HALTEN); ein noch aelteres Nachhol-Ereignis
    bildet einen eigenen Durchgang (es meldet ohnehin nicht).
  - Die Altersgrenze der Meldung kommt vom Aufrufer (heute ein Literal 900 an zwei Stellen in verifyd.py).
  - Die Frist an pool_lock ist ein Versuch im Takt SPERRE_TAKT_S an derselben Dateisperre wie anlernen.pool_lock.
  - Der Altbestand bleibt im Speicher, bis Pool- oder Identitaetsdatei sich aendern; eine Statusaenderung seiner Saetze
    im Katalog allein liest ihn nicht neu.
  - Eine unlesbare Zeile der Identitaetsdatei faellt beim Ersetzen der Datei weg, wie bei den anderen Schreibern (der
    Aufraeum-Schritt schreibt dann nicht, er meldet den Lesefehler).
  - Eine wegen des Merkmals fallengelassene Meldung kommt im selben Durchgang nicht wieder, auch wenn das Merkmal danach
    wegfaellt (Bauplan analysen/bauplan_aehnlich.md, W3 V9).
  - Sammelbecken (AE6): ein neues Fremder-Urteil wirkt erst beim naechsten Aufraeum-Schritt (die Wache sieht die
    Wahrheits-Datei nicht); die Bilder aus Fremder-Durchgaengen eines Beckens werden je Lauf EINE neue Unbekannte. Bricht
    ein Lauf zwischen der neuen Zeile und dem Umbinden ihrer Saetze ab, bleibt eine Zeile ohne Mitglieder stehen und der
    naechste Lauf nimmt die Bilder noch einmal heraus. Ein Abbruch zwischen Spurzeile und Schreibzug ergibt beim
    Fortsetzen eine zweite Spurzeile derselben Identitaet.
"""
import collections
import contextlib
import datetime
import fcntl
import json
import math
import os
import re
import threading
import time

import numpy as np

from core import aehnlich as _aeh
from core import atomar as _atomar
from core import harvest_set as _hs
from core import logbuch as _logbuch

_log = _logbuch.logger(__name__)

ZUSTAND_DATEI = os.path.join("state", "unbekannt_verbraucher.json")
# Bauplan analysen/bauplan_aehnlich.md Entscheid 17: der Zustand des letzten Aufraeum-Schritts (Zeit, Grenzen, Zahlen, Dauer).
AEHNLICH_DATEI = os.path.join("state", "unbekannt_aehnlich.json")
# Bauplan analysen/bauplan_aehnlich.md Entscheid 29 (Fassung 8, W7 V10): je Zusammenfuehren eine Spurzeile.
SAMMEL_DATEI = os.path.join("state", "unbekannt_sammel.jsonl")
# Entscheid 24: das Fach des Zustands mit der Zeit des letzten Stapels je Identitaet (nur die juengeren als die Karenz).
ZULETZT = "zuletzt"
SCHLANGEN_ORDNER = "state"
ARCHIV_ORDNER = os.path.join("state", "archiv", "unbekannt_schlange")
TAG_FORMAT = "%Y-%m-%d"
SCHEMA = 1
# Entscheid 11: wartet der Verbraucher laenger als eine Minute auf pool_lock, stellt er den Stapel zurueck und meldet es.
SPERRE_FRIST_S = 60.0
SPERRE_TAKT_S = 0.2              # Takt des Versuchs an der Sperre; der Deckel ist die Frist
# Ein Durchgang endet an der Tagesgrenze: gehalten werden der juengste Tag und der Vortag (spaet Gebuchtes um Mitternacht).
TAGE_HALTEN = 2
# Status und Merkmal der Identitaeten, wie anlernen sie schreibt (_unbekannt_besucher_intern, _reconcile_intern).
STATUS_AKTIV, STATUS_ARCHIV, STATUS_BESUCHER, MERKMAL_OBJEKT = "aktiv", "archiviert", "besucher", "objekt"
ZEILE_PFLICHT = ("eid", "pfad", "start")


def _wert(cfg, key):
    """Einen Config-Schluessel lesen, ohne eigenen Werkswert.
    -> der Wert; fehlt er, ERROR-Zeile und KeyError"""
    if not isinstance(cfg, dict) or cfg.get(key) is None:
        _log.error(f"unknown consumer: config key '{key}' is missing — nothing done")
        raise KeyError(key)
    return cfg[key]


def tag_von(zeit):
    """Der Tag einer Zeit in Ortszeit, wie er im Namen eines Schlangen-Stuecks steht.
    -> 'JJJJ-MM-TT'"""
    return time.strftime(TAG_FORMAT, time.localtime(zeit))


def stueck_pfad(cfg, tag):
    """Der Pfad des Schlangen-Stuecks eines Tages (Name aus harvest_set.QUEUE_FILE).
    -> Pfad"""
    return os.path.join(_wert(cfg, "data_dir"), SCHLANGEN_ORDNER, _hs.QUEUE_FILE.format(tag=tag))


def fenster_namen(last_seen, start, karenz, bestaetigt):
    """Die im Fenster eines Ereignisses erkannten Namen (Start plus und minus Karenz, wie die Szenen-Karenz) und die im
    Ereignis bestaetigten. -> sortierte Liste der Namen"""
    namen = {p for p, ts in (last_seen or {}).items() if start - karenz <= ts <= start + karenz}
    return sorted(namen | set(bestaetigt or []))


def schlange_anhaengen(cfg, entry, event_dir, gruppen, last_seen, zeit=None):
    """Die Schlangen-Zeile eines gebuchten Ereignisses an das Stueck des Tages haengen (Stufe V1a Punkt 4, W3, W10); der
    Dienst ruft sie nach der Buchung. -> die geschriebene Zeile; ein Schreibfehler wird weitergeworfen"""
    zeit = time.time() if zeit is None else zeit
    start = entry.get("start") or entry["ts"]
    zeile = {"ts": round(zeit, 1), "eid": entry["eid"], "pfad": event_dir, "gruppen": gruppen,
             "camera": entry.get("camera"), "start": start, "ende_ts": entry.get("ende_ts"),
             "dauer_s": entry.get("dauer_s"), "max_bw": entry.get("max_bw"), "nachhol": bool(entry.get("nachhol")),
             "fenster_namen": fenster_namen(last_seen, start, _wert(cfg, "szene_karenz_s"), entry.get("bestaetigt"))}
    with open(stueck_pfad(cfg, tag_von(zeit)), "a", encoding="utf-8") as f:
        f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
        f.flush()
    return zeile


def stuecke(cfg):
    """Die Tage der Schlangen-Stuecke im Ordner, aelteste zuerst.
    -> Liste 'JJJJ-MM-TT'"""
    vor, nach = _hs.QUEUE_FILE.split("{tag}")
    muster = re.compile(re.escape(vor) + r"(\d{4}-\d{2}-\d{2})" + re.escape(nach))
    try:
        namen = os.listdir(os.path.join(_wert(cfg, "data_dir"), SCHLANGEN_ORDNER))
    except FileNotFoundError:
        return []
    return sorted(m.group(1) for m in map(muster.fullmatch, namen) if m)


def zustand_lesen(cfg):
    """Den Zustand des Verbrauchers lesen; ohne Datei der leere Anfang.
    -> dict schema, lesestand, durchgaenge, faellig; unlesbar: ERROR-Zeile und ValueError (nie still neu anfangen)"""
    pfad = os.path.join(_wert(cfg, "data_dir"), ZUSTAND_DATEI)
    try:
        with open(pfad, encoding="utf-8") as f:
            z = json.load(f)
    except FileNotFoundError:
        return {"schema": SCHEMA, "lesestand": {}, "durchgaenge": {}, "faellig": []}
    except (OSError, ValueError) as e:
        z = f"{type(e).__name__}: {e}"
    if not (isinstance(z, dict) and isinstance(z.get("lesestand"), dict) and isinstance(z.get("durchgaenge"), dict)
            and isinstance(z.get("faellig"), list)):
        _log.error(f"unknown consumer: state file {ZUSTAND_DATEI} is not readable ({str(z)[:200]}) — nothing processed")
        raise ValueError(f"unknown consumer state not readable: {ZUSTAND_DATEI}")
    return z


def _zustand_schreiben(cfg, z):
    """Den Zustand atomar schreiben (core/atomar, ED011).
    -> None; ein Schreibfehler wird weitergeworfen"""
    _atomar.json_schreiben(os.path.join(_wert(cfg, "data_dir"), ZUSTAND_DATEI), z)


def offene_zeilen(cfg, z):
    """Die noch nicht gelesenen vollstaendigen Zeilen aller Stuecke, Stuecke nach Datum, Zeilen in Dateireihenfolge; eine
    Zeile ohne Zeilenende schreibt gerade jemand, sie zaehlt noch nicht.
    -> Liste (Tag, Zeilennummer ab 0, Byte-Ende der Zeile, Text)"""
    aus = []
    for tag in stuecke(cfg):
        stand = z["lesestand"].get(tag) or {"zeile": 0, "byte": 0}
        with open(stueck_pfad(cfg, tag), "rb") as f:
            f.seek(stand["byte"])
            daten = f.read()
        nr, pos = stand["zeile"], stand["byte"]
        for roh in daten[:daten.rfind(b"\n") + 1].splitlines(keepends=True):
            pos += len(roh)
            aus.append((tag, nr, pos, roh.decode("utf-8", errors="replace").strip()))
            nr += 1
    return aus


def stuecke_raeumen(cfg, z, jetzt):
    """Schlangen-Stuecke archivieren, die ganz gelesen und aelter als aufbewahrung_tage sind (W17); nichts wird geloescht,
    der Lesestand vergisst nur archivierte Stuecke. -> Liste der archivierten Tage"""
    grenze = tag_von(jetzt - float(_wert(cfg, "aufbewahrung_tage")) * 86400)
    ziel = os.path.join(_wert(cfg, "data_dir"), ARCHIV_ORDNER)
    aus = []
    for tag in stuecke(cfg):
        pfad, stand = stueck_pfad(cfg, tag), z["lesestand"].get(tag)
        if tag >= grenze or not stand or stand["byte"] != os.path.getsize(pfad):
            continue
        os.makedirs(ziel, exist_ok=True)
        os.rename(pfad, os.path.join(ziel, os.path.basename(pfad)))
        aus.append(tag)
    da = set(stuecke(cfg))
    z["lesestand"] = {t: s for t, s in z["lesestand"].items() if t in da}
    if aus:
        _log.info(f"unknown consumer: {len(aus)} fully read queue piece(s) older than the retention moved to "
                  f"{ARCHIV_ORDNER} ({', '.join(aus)})")
    return aus


@contextlib.contextmanager
def _sperre(frist_s):
    """pool_lock mit Frist (Entscheid 11): dieselbe Dateisperre wie anlernen.pool_lock, im Takt SPERRE_TAKT_S versucht.
    -> Kontext mit True (gehalten) oder False (Frist abgelaufen, nichts gehalten)"""
    import anlernen                                     # noqa: PLC0415  spaet: schwerer Import, Pfade aus der Umgebung
    os.makedirs(os.path.dirname(anlernen.POOL_LOCK_PATH), exist_ok=True)
    with open(anlernen.POOL_LOCK_PATH, "w") as f:
        ende = time.monotonic() + frist_s
        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= ende:
                    yield False
                    return
                time.sleep(SPERRE_TAKT_S)
        try:
            yield True
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def deckung(matrix, uids, modelle, gruppe, modell, latte, zuerst=(), verboten=()):
    """Die Deckung einer Gruppe (Entscheid 11): je Identitaet der hoechste Kosinus eines Gruppen-Gesichts zu einem
    Mitglied gleichen Modells; ab der Latte zuerst eine Identitaet aus zuerst, dann irgendeine; nie eine aus verboten.
    -> (uid oder None, bester Kosinus der Wahl oder ueber alle, None ohne Zeile)"""
    if not len(uids):
        return None, None
    naechst = (np.asarray(gruppe, np.float32) @ np.asarray(matrix, np.float32).T).max(axis=0)
    bester = {}
    for i, (uid, m) in enumerate(zip(uids, modelle)):
        if m == modell and uid not in verboten:
            bester[uid] = max(bester.get(uid, -1.0), float(naechst[i]))
    for menge in (set(zuerst), None):
        treffer = {u: c for u, c in bester.items() if c >= latte and (menge is None or u in menge)}
        if treffer:
            uid = max(sorted(treffer), key=lambda u: treffer[u])
            return uid, treffer[uid]
    return None, (max(bester.values()) if bester else None)


def _ketten_schluessel(cfg, camera):
    """Der Ketten-Schluessel einer Kamera aus der Config, wie szenarien_des_tages ihn bildet.
    -> Text"""
    from core import areas as _areas                    # noqa: PLC0415
    kett = _areas.kettung_normalisieren(cfg.get("areas_kettung"))
    ar = _areas.normalisieren(cfg.get("areas")) if kett else {}
    return _areas.ketten_schluessel(ar, kett, str(camera))


def tag_anfang(zeit):
    """Mitternacht des Tages einer Zeit in Ortszeit (der Tagesschnitt des Durchgangs).
    -> Sekunden seit 1970"""
    return datetime.datetime.fromtimestamp(zeit).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def durchgang_einordnen(z, cfg, zeile):
    """Ein Ereignis in den Durchgang seiner Kette einordnen: die Buchungen je Kette und Tag nach Start geordnet und mit der
    EINEN Anhaenge-Regel gekettet (W5); eine zweite Zeile desselben Ereignisses ersetzt die erste.
    -> (Name des Durchgangs, Menge seiner Ereignisse, Fach des Zustands mit evs und gemeldet)"""
    import szenarien as _sz                             # noqa: PLC0415  spaet wie core/kette
    kette = _ketten_schluessel(cfg, zeile.get("camera", "?"))
    start = float(zeile["start"])
    tag0 = tag_anfang(start)
    fach = z["durchgaenge"].setdefault(kette, {}).setdefault(tag_von(start), {"evs": [], "gemeldet": []})
    ev = {"eid": zeile["eid"], "start": start, "ende_ts": zeile.get("ende_ts"), "dauer_s": zeile.get("dauer_s")}
    fach["evs"] = sorted([e for e in fach["evs"] if e["eid"] != ev["eid"]] + [ev], key=lambda e: (e["start"], e["eid"]))
    gap, offen, gaenge = int(_wert(cfg, "szenario_gap_min")) * 60, {}, []
    for e in fach["evs"]:
        cur, neu = _sz.durchgang_anhaengen(offen, kette, e, gap, tag0)
        if neu:
            gaenge.append(cur)
    mein = next(g for g in gaenge if any(e["eid"] == ev["eid"] for e in g["evs"]))
    name = _meldungen_umhaengen(z, fach, kette, mein)
    tage = sorted({t for faecher in z["durchgaenge"].values() for t in faecher})[-TAGE_HALTEN:]
    for k in list(z["durchgaenge"]):
        z["durchgaenge"][k] = {t: f for t, f in z["durchgaenge"][k].items() if t in tage}
        if not z["durchgaenge"][k]:
            del z["durchgaenge"][k]
    return name, {e["eid"] for e in mein["evs"]}, fach


def _meldungen_umhaengen(z, fach, kette, mein):
    """Meldungsvermerke und offene Meldungen des Durchgangs mein von den Schluesseln seiner Ereignisse auf seinen Namen
    umhaengen, je Identitaet hoechstens eine (Bauplan analysen/bauplan_neueste_zuerst.md, Stufe LZ1 Punkt 3).
    -> der Name des Durchgangs (szenarien._pass_schluessel seines Starts)"""
    import szenarien as _sz                             # noqa: PLC0415
    name = _sz._pass_schluessel(mein["start"], kette)
    # Jeder fruehere Name dieses Durchgangs war der Start eines seiner Ereignisse (Startverschiebung oder Bruecke);
    # bearbeitet wird nur das Fach dieses Tages und dieser Kette.
    alte = {_sz._pass_schluessel(e["start"], kette) for e in mein["evs"]}
    je_uid = {}
    for v in fach["gemeldet"]:
        gang, _s, uid = v.partition("|")
        if gang in alte:
            je_uid.setdefault(uid, []).append(v)
    offen = {m["id"]: m for m in z["faellig"]}
    for uid, vermerke in je_uid.items():
        ziel = f"{name}|{uid}"
        if vermerke == [ziel]:
            continue
        # Erledigt heisst: Vermerk ohne offene Meldung; bestimmt vor dem Umhaengen, der Zielschluessel eingeschlossen.
        offene = [offen[v] for v in vermerke if v in offen]
        weg = set(vermerke)
        neu = None
        if offene and len(offene) == len(vermerke):
            neu = dict(min(offene, key=lambda m: m["faellig_ab"]), id=ziel)     # keine neue Karenz
            neu["fenster_namen"] = sorted({n for m in offene for n in m["fenster_namen"]})
            best = max(offene, key=lambda m: m["mass"])
            neu.update(ref_id=best["ref_id"], mass=best["mass"])
        fach["gemeldet"] = [v for v in fach["gemeldet"] if v not in weg] + [ziel]
        z["faellig"] = [m for m in z["faellig"] if m["id"] not in weg] + ([neu] if neu else [])
    return name


def meldung_vormerken(z, fach, durchgang, zeile, uid, gruppe, ident, jetzt, karenz, alt_grenze_s):
    """Der Meldungs-Entscheid je Durchgang und Identitaet (Entscheid 11): keine fuer Nachhol und alt, keine fuer besucher
    und objekt, sonst einmal je Durchgang, faellig nach der Karenz; ein weiterer Stapel ergaenzt die offene Meldung.
    -> 'neu', 'ergaenzt' oder der Grund ohne Meldung ('nachhol', 'alt', 'stumm', 'schon_gemeldet')"""
    if zeile.get("nachhol"):
        return "nachhol"
    if jetzt - float(zeile["start"]) > alt_grenze_s:
        return "alt"
    if ident.get("status") == STATUS_BESUCHER or ident.get(MERKMAL_OBJEKT):
        return "stumm"
    schluessel = f"{durchgang}|{uid}"
    bestes = gruppe.get("bestes") or gruppe["ref_ids"][0]
    mass = next((float(g.get("mass") or 0) for g in gruppe.get("gesichter") or [] if g.get("ref_id") == bestes), 0.0)
    namen = set(zeile.get("fenster_namen") or [])
    if schluessel in fach["gemeldet"]:
        offen = next((m for m in z["faellig"] if m["id"] == schluessel), None)
        if offen is None:
            return "schon_gemeldet"
        offen["fenster_namen"] = sorted(set(offen["fenster_namen"]) | namen)
        if mass > offen["mass"]:
            offen.update(ref_id=bestes, mass=mass)
        return "ergaenzt"
    fach["gemeldet"].append(schluessel)
    z["faellig"].append({"id": schluessel, "eid": zeile["eid"], "uid": uid, "camera": zeile.get("camera"),
                         "start": zeile["start"], "max_bw": zeile.get("max_bw"), "fenster_namen": sorted(namen),
                         "ref_id": bestes, "mass": mass, "faellig_ab": jetzt + karenz})
    return "neu"


def faellige_meldungen(z, idents, jetzt):
    """Die faelligen Meldungen (faellig_ab erreicht); wurde die Identitaet in der Karenz besucher oder objekt oder traegt
    sie beim Versand das Merkmal „ähnlich zu P“ (Bauplan analysen/bauplan_aehnlich.md Entscheid 15), faellt die Meldung aus
    dem Zustand (INFO-Zeile). -> Liste der faelligen Meldungen (Kopien)"""
    aus, bleibt = [], []
    for m in z["faellig"]:
        ident = idents.get(m["uid"]) or {}
        aehnlich = _aeh.merkmal_von(ident)
        if ident.get("status") == STATUS_BESUCHER or ident.get(MERKMAL_OBJEKT) or aehnlich:
            grund = ("an object" if ident.get(MERKMAL_OBJEKT) else f"probably {aehnlich['person']}" if aehnlich
                     else "an ignored visitor")
            _log.info(f"unknown consumer: notification for {m['uid']} ({m['eid']}) dropped — the identity is now {grund}")
            continue
        bleibt.append(m)
        if m["faellig_ab"] <= jetzt:
            aus.append(dict(m))
    z["faellig"] = bleibt
    return aus


def _stempel(pfad):
    """Groesse und Aenderungszeit einer Datei als Stand-Merkmal.
    -> [Byte, mtime_ns] oder None ohne Datei"""
    try:
        st = os.stat(pfad)
    except FileNotFoundError:
        return None
    return [st.st_size, st.st_mtime_ns]


def _uid_nummer(uid):
    """Die Nummer einer Identitaet 'U<n>'.
    -> int oder 0"""
    return int(uid[1:]) if isinstance(uid, str) and uid[:1] == "U" and uid[1:].isdigit() else 0


def sammel_plan(zeilen, z, jetzt, karenz):
    """Der Plan des Zusammenfuehrens (Bauplan analysen/bauplan_aehnlich.md Entscheid 24): je Person P die Identitaeten mit
    Merkmal P (aktiv oder archiviert, nicht ausgenommen), deren Durchgang abgeschlossen ist: keine Meldung von ihr im
    Zustand z vorgemerkt und ihr letzter Stapel (Fach ZULETZT) mindestens karenz Sekunden alt; Ziel ist das Sammelbecken von
    P, gibt es keins, die kleinste Nummer darunter (W7 V2).
    -> ({Person: (Sammelbecken, [Kennungen ohne das Becken])}, Zeitpunkt des naechsten aufgeschobenen oder None)"""
    offen = {m.get("uid") for m in z.get("faellig") or []}
    zuletzt = z.get(ZULETZT) or {}
    becken, kand, spaeter = {}, {}, []
    for u in zeilen:
        uid, m = u.get("id"), _aeh.merkmal_von(u)
        if _aeh.sammel_von(u):
            becken.setdefault(_aeh.sammel_von(u), uid)
            continue
        if (not m or _aeh.ausgenommen(u) or m["person"] in _aeh.verneint(u)
                or u.get("status") not in (STATUS_AKTIV, STATUS_ARCHIV)):
            continue
        if uid in offen or jetzt - float(zuletzt.get(uid, -math.inf)) < karenz:
            spaeter.append(jetzt if uid in offen else float(zuletzt[uid]) + karenz)
            continue
        kand.setdefault(m["person"], []).append(uid)
    plan = {}
    for p, uids in kand.items():
        uids.sort(key=_uid_nummer)
        ziel = becken.get(p) or uids[0]
        plan[p] = (ziel, [u for u in uids if u != ziel])
    return plan, (min(spaeter) if spaeter else None)


def _stapel_gruppen(pfad):
    """Die Gruppen der Stapel-Datei eines Ereignisses, je mit der Nummer ihrer Stapel-Zeile (eines Clips).
    -> Liste (Zeilennummer, Gruppe); Gruppen ohne ref_ids fallen weg"""
    return [(i, g) for i, sz in enumerate(_hs.event_unknown(pfad)) for g in (sz.get("gruppen") or [])
            if isinstance(g, dict) and isinstance(g.get("ref_ids"), list) and g["ref_ids"]]


class Verbraucher:
    """Der Kern des Verbraucher-Fadens: Matrix im Speicher, Zustand auf Platte (Kopf des Moduls)."""

    def __init__(self, cfg, alt_grenze_s, sperre_frist_s=SPERRE_FRIST_S):
        """Den Verbraucher fuer die Config des Dienstes anlegen; alt_grenze_s ist die Altersgrenze der Meldung (W3).
        -> None; liest anlernen einen anderen Datenordner als die Config, ERROR-Zeile und RuntimeError"""
        import anlernen                                 # noqa: PLC0415
        self.cfg, self.alt_grenze_s, self.sperre_frist_s = cfg, float(alt_grenze_s), float(sperre_frist_s)
        if os.path.realpath(anlernen.DATA) != os.path.realpath(_wert(cfg, "data_dir")):
            _log.error(f"unknown consumer: anlernen reads another data folder ({anlernen.DATA}) than the config "
                       f"({cfg['data_dir']}) — nothing done")
            raise RuntimeError("unknown consumer: data folder of anlernen differs from the config")
        self._m = None
        self._vek = {}                  # ref_id -> (Vektor, Modell); Saetze sind unveraenderlich
        self._alt = None                # (Stempel, Zeilen) des Altbestands
        self._geraeumt = False
        self._aufraeum_stand = None     # (Grenzen, Stempel der Identitaetsdatei) nach dem letzten gelungenen Aufraeum-Schritt
        self._sammel_ab = None          # Entscheid 24: ab dann ist ein aufgeschobenes Zusammenfuehren faellig
        self._sammel_n = 0              # zusammengefuehrte Identitaeten seit dem Start des Prozesses (/health)
        self._lock = threading.Lock()

    def runde(self, jetzt=None):
        """Eine Runde: beim Start der Aufraeum-Schritt, vor dem ersten Stapel Bindungen ohne Identitaet nachraeumen, dann
        alle offenen Schlangen-Zeilen der Reihe nach, je unter pool_lock; danach Stuecke raeumen, nach verarbeiteten
        Stapeln oder geaendertem Stand der Aufraeum-Schritt, dann die faelligen Meldungen holen.
        -> dict verarbeitet, uebersprungen, zurueckgestellt, fehler, meldungen, archiviert"""
        with self._lock:
            jetzt = time.time() if jetzt is None else jetzt
            erst = self._aufraeum_stand is None             # Entscheid 17: beim Start vor der ersten Runde
            z = zustand_lesen(self.cfg)
            if erst:
                self._aufraeumen(z, jetzt)
            out = {"verarbeitet": 0, "uebersprungen": 0, "zurueckgestellt": False, "fehler": None, "meldungen": [],
                   "archiviert": []}
            for tag, nr, ende, text in offene_zeilen(self.cfg, z):
                zeile = self._zeile_lesen(tag, nr, text)
                if zeile is None:
                    out["uebersprungen"] += 1
                else:
                    ergebnis = self._unter_sperre(z, zeile, jetzt)
                    if ergebnis is not None:
                        out[ergebnis[0]] = ergebnis[1]
                        z = zustand_lesen(self.cfg)
                        break
                    out["verarbeitet"] += 1
                z["lesestand"][tag] = {"zeile": nr + 1, "byte": ende}
                _zustand_schreiben(self.cfg, z)
            out["archiviert"] = stuecke_raeumen(self.cfg, z, jetzt)
            if out["verarbeitet"] or (not erst and self.aufraeumen_faellig(jetzt)):   # Entscheid 17, vor den Meldungen
                self._aufraeumen(z, jetzt)
            out["meldungen"] = faellige_meldungen(z, self._identitaeten(), jetzt)
            _zustand_schreiben(self.cfg, z)
            return out

    def aufraeumen_faellig(self, jetzt=None):
        """Die Stand-Pruefung der Wache (Bauplan analysen/bauplan_aehnlich.md Entscheid 17): andere Grenzen in der Config
        oder eine Identitaetsdatei, die seit dem letzten gelungenen Aufraeum-Schritt ein anderer Schreiber geaendert hat;
        dazu ein aufgeschobenes Zusammenfuehren, dessen Durchgang inzwischen abgeschlossen ist (Entscheid 24).
        -> bool; vor dem ersten gelungenen Lauf und bei unlesbaren Grenzen True (der Lauf meldet den Fehler laut)"""
        import anlernen                                 # noqa: PLC0415
        if self._aufraeum_stand is None:
            return True
        if self._sammel_ab is not None and (time.time() if jetzt is None else jetzt) >= self._sammel_ab:
            return True
        try:
            return self._aufraeum_stand != (_aeh.grenzen(self.cfg), _stempel(anlernen.UNB_PATH))
        except Exception:                               # noqa: BLE001  der Aufraeum-Schritt meldet ihn laut
            _logbuch.swallowed(_log, _logbuch.WARNING, "similar check due")
            return True

    def _aufraeumen(self, z=None, jetzt=None):
        """Der Aufraeum-Schritt (Entscheide 14 und 17): alle Identitaeten einstufen (ausserhalb der Sperre), unter pool_lock
        mit Frist die Datei frisch lesen, nur das Merkmal setzen; dann je Person P zusammenfuehren (Entscheid 24, z ist der
        Zustand des Verbrauchers, nur gelesen) und in einem Zug schreiben, nur bei Aenderung; danach die Bilder aus
        Fremder-Durchgaengen aus den Sammelbecken (Entscheid 25); Zustand unter state/.
        -> Liste der geaenderten Kennungen oder None (Fehler oder Sperre nicht bekommen)"""
        import anlernen                                 # noqa: PLC0415
        t0 = time.monotonic()
        jetzt = time.time() if jetzt is None else jetzt
        vorher = _stempel(anlernen.UNB_PATH)
        self._aufraeum_stand = None                     # bis zum Gelingen faellig: die Wache versucht es wieder
        erg = _aeh.SPEICHER.einstufen_alle(self.cfg)
        if erg["fehler"] is not None:
            return self._aehnlich_zustand({})
        try:
            z = zustand_lesen(self.cfg) if z is None else z
            with _sperre(self.sperre_frist_s) as gehalten:
                if not gehalten:
                    _log.warning(f"similar check: pool lock held longer than {self.sperre_frist_s:.0f} s — the marks "
                                 "are written in the next run")
                    return None
                zeilen = self._identitaeten_zeilen()
                unter_sperre = _stempel(anlernen.UNB_PATH)
                geaendert = _aeh.merkmale_setzen(zeilen, erg["ziel"])
                zusammen, becken = self._zusammenfuehren(zeilen, z, jetzt)
                if geaendert or becken:
                    anlernen._speichere_unbekannte(zeilen)
                raus = self._fremde_heraus(erg["fremd_raus"], jetzt)
                if raus:
                    zeilen = self._identitaeten_zeilen()
                nachher = _stempel(anlernen.UNB_PATH)
        except Exception as e:                          # noqa: BLE001  laut: ERROR, /health rot, Stapel laufen weiter
            _aeh.SPEICHER.fehler(self.cfg, e)
            return self._aehnlich_zustand({})
        # Die eigene Schreibung merkt sich der Faden; schrieb ein anderer zwischen Einstufen und Sperre, bleibt der alte
        # Stand stehen und die Wache stuft neu ein (Entscheid 17).
        self._aufraeum_stand = (erg["grenzen"], nachher if unter_sperre == vorher else vorher)
        geaendert = list(dict.fromkeys(geaendert + becken + raus))
        self._aufraeum_bilanz(erg, zeilen, geaendert, (time.monotonic() - t0) * 1000.0, zusammen)
        return geaendert

    def _zusammenfuehren(self, zeilen, z, jetzt):
        """Das Zusammenfuehren im Aufraeum-Schritt (Entscheid 24), innerhalb seiner Sperre, ohne eigene: je Person P nach
        sammel_plan in das Sammelbecken (anlernen.zusammenlegen_kern: erst die Saetze umhaengen), je Identitaet eine
        Spurzeile (Entscheid 29); zeilen wird an Ort geaendert, schreiben tut der Aufrufer in einem Zug.
        -> ({Person: [zusammengefuehrte Kennungen]}, [geaenderte Sammelbecken])"""
        import anlernen                                 # noqa: PLC0415
        from core import refquelle as _rq               # noqa: PLC0415
        plan, self._sammel_ab = sammel_plan(zeilen, z, jetzt, float(_wert(self.cfg, "szene_karenz_s")))
        if not plan:
            return {}, []
        U = {u.get("id"): u for u in zeilen}
        saetze = _rq.unknown_members(self.cfg) if any(q for _z, q in plan.values()) else {}
        zusammen, becken = {}, []
        for person, (ziel, quellen) in sorted(plan.items()):
            if _aeh.becken_setzen(U[ziel], person):
                becken.append(ziel)
            for q in quellen:
                self._spur(ziel, U[q], len(U[q].get("members") or []) + len(saetze.get(q) or []), jetzt)
                anlernen.zusammenlegen_kern(U, ziel, q, sammel=person)
                zusammen.setdefault(person, []).append(q)
            if quellen and ziel not in becken:
                becken.append(ziel)
        weg = {q for qs in zusammen.values() for q in qs}
        zeilen[:] = [u for u in zeilen if u.get("id") not in weg]
        return zusammen, becken

    def _spur(self, ziel, zeile, gesichter, jetzt):
        """Die Spurzeile eines Zusammenfuehrens nach SAMMEL_DATEI (Entscheid 29): Zeit, Sammelbecken, Nummer, Label,
        Status, Merkmalswerte, Zahl der Gesichter; ein Schreibfehler wird weitergeworfen (der Lauf scheitert laut). -> None"""
        m = _aeh.merkmal_von(zeile) or {}
        spur = {"ts": round(jetzt, 1), "sammel": ziel, "uid": zeile.get("id"), "label": zeile.get("label"),
                "status": zeile.get("status"), "merkmal": {k: m.get(k) for k in ("person", "median", "abstand", "gesichter")},
                "gesichter": gesichter}
        with open(os.path.join(_wert(self.cfg, "data_dir"), SAMMEL_DATEI), "a", encoding="utf-8") as f:
            f.write(json.dumps(spur, ensure_ascii=False) + "\n")
            f.flush()

    def _fremde_heraus(self, fremd_raus, jetzt):
        """Die Bilder aus Fremder-Durchgaengen aus jedem Sammelbecken nehmen (Entscheid 25), je Becken eine neue Unbekannte
        mit dem Urteil „nicht P“ ueber anlernen.nicht_p_auswahl_kern, innerhalb der Sperre des Aufraeum-Schritts.
        -> Liste der geaenderten Kennungen (Becken und neue Identitaeten)"""
        import anlernen                                 # noqa: PLC0415
        aus = []
        for uid, (person, ids) in sorted(fremd_raus.items()):
            neu, n = anlernen.nicht_p_auswahl_kern(uid, ids, ts=jetzt)
            if neu:
                aus += [uid, neu]
                _log.info(f"similar check: {n} face(s) of a pass confirmed as a stranger taken out of the collection "
                          f"{uid} (similar to {person}) as new unknown {neu}")
        return aus

    def _aufraeum_bilanz(self, erg, zeilen, geaendert, dauer_ms, zusammen):
        """Zahlen eines gelungenen Aufraeum-Schritts: Zustand fuer /health und unter state/, INFO-Zeile bei Aenderung und
        je Lauf mit Zusammenfuehren (Entscheid 24), WARNING fuer Identitaeten mit nicht lesbarem Mitglied (Entscheid 17).
        -> None"""
        je_person = collections.Counter(m["person"] for m in map(_aeh.merkmal_von, zeilen) if m)
        n_zus = sum(len(v) for v in zusammen.values())
        self._sammel_n += n_zus
        zahlen = {"letzte_dauer_ms": round(dauer_ms, 1), "identitaeten_n": len(zeilen),
                  "aehnlich_n": sum(je_person.values()), "personen_n": len(je_person), "geaendert_n": len(geaendert),
                  "unlesbar_n": len(erg["unlesbar"]), "grenzen": dict(zip(
                      (_aeh.LATTE_KEY, _aeh.ABSTAND_KEY, _aeh.MINDEST_KEY), erg["grenzen"])),
                  "sammel_n": sum(1 for u in zeilen if _aeh.sammel_von(u)), "zusammengefuehrt_n": self._sammel_n}
        _aeh.SPEICHER.lauf_eintragen(**zahlen)
        self._aehnlich_zustand({"je_person": dict(je_person), "geaendert": geaendert, "zusammengefuehrt": zusammen})
        if n_zus:
            _log.info(f"similar check: {n_zus} unknown identities merged into the collections 'similar to P' ("
                      + ", ".join(f"{p} {len(u)}" for p, u in sorted(zusammen.items())) + f"), {zahlen['sammel_n']} "
                      f"collection(s), {dauer_ms:.0f} ms")
        if erg["unlesbar"]:
            uids = sorted(erg["unlesbar"], key=_uid_nummer)
            _log.warning(f"similar check: {len(uids)} identities keep their mark, a member is not readable "
                         f"({', '.join(uids[:10])}{' …' if len(uids) > 10 else ''}: "
                         f"{'; '.join(sorted(set(erg['unlesbar'].values())))})")
        text = (f"similar check: {len(zeilen)} unknown identities, {zahlen['aehnlich_n']} probably a known person ("
                + ", ".join(f"{p} {n}" for p, n in sorted(je_person.items())) + f"), {len(geaendert)} changed, "
                f"{len(erg['unlesbar'])} kept (member not readable), {dauer_ms:.0f} ms")
        (_log.info if geaendert else _log.debug)(text)

    def _aehnlich_zustand(self, mehr):
        """Den Zustand des Aufraeum-Schritts atomar unter state/ ablegen (Entscheid 17); ein Schreibfehler ist laut, kostet
        aber den Lauf nicht. -> None"""
        try:
            _atomar.json_schreiben(os.path.join(_wert(self.cfg, "data_dir"), AEHNLICH_DATEI),
                                   dict(_aeh.SPEICHER.stand(), **mehr))
        except Exception as e:                          # noqa: BLE001  laut, die Merkmale stehen schon
            _log.error(f"similar check: state file {AEHNLICH_DATEI} not written ({type(e).__name__}: {e})")
        return None

    def _identitaeten_zeilen(self):
        """Die Identitaetszeilen frisch ueber den einen Leser (unter pool_lock), mit der Pruefung, dass jede Zeile der
        Datei gelesen wurde (Entscheid 17: eine verschluckte Zeile ist ein Lesefehler).
        -> Liste der Zeilen; nicht lesbar: OSError oder ValueError"""
        import anlernen                                 # noqa: PLC0415
        from core import unbekanntpool as _up           # noqa: PLC0415
        try:
            with open(anlernen.UNB_PATH, "rb") as f:
                n = sum(1 for z in f if z.strip())
        except FileNotFoundError:
            return []
        zeilen = list(_up._cluster_lesen(_wert(self.cfg, "data_dir")))
        if len(zeilen) != n:
            raise ValueError(f"identity file: {n - len(zeilen)} of {n} line(s) not readable")
        return zeilen

    def meldungen_quittieren(self, ids):
        """Gesendete Meldungen aus dem Zustand austragen (der Sender quittiert nach dem Senden, Stufe V1b).
        -> Zahl der ausgetragenen"""
        with self._lock:
            z = zustand_lesen(self.cfg)
            weg = set(ids)
            vorher = len(z["faellig"])
            z["faellig"] = [m for m in z["faellig"] if m["id"] not in weg]
            _zustand_schreiben(self.cfg, z)
            return vorher - len(z["faellig"])

    def _zeile_lesen(self, tag, nr, text):
        """Eine Schlangen-Zeile lesen; unlesbar oder ohne Pflichtfeld ist sie laut uebersprungen.
        -> dict oder None"""
        try:
            d = json.loads(text)
        except ValueError:
            d = None
        if not isinstance(d, dict) or any(d.get(k) is None for k in ZEILE_PFLICHT):
            _log.error(f"unknown consumer: queue piece {tag} line {nr + 1} is not readable or lacks "
                       f"{', '.join(ZEILE_PFLICHT)} — skipped")
            return None
        return d

    def _unter_sperre(self, z, zeile, jetzt):
        """Einen Stapel unter pool_lock mit Frist verarbeiten; ein Fehler ist laut, der Lesestand bleibt stehen.
        -> None (verarbeitet) oder (Schluessel, Wert) fuer zurueckgestellt oder fehler"""
        with _sperre(self.sperre_frist_s) as gehalten:
            if not gehalten:
                _log.warning(f"unknown consumer: pool lock held longer than {self.sperre_frist_s:.0f} s — stack "
                             f"{zeile['eid']} put back, the next round takes it")
                return "zurueckgestellt", True
            try:
                if not self._geraeumt:
                    self._nachraeumen()
                    self._geraeumt = True
                self._stapel(z, zeile, jetzt)
            except Exception as e:                      # noqa: BLE001  laut, der Lesestand bleibt stehen
                self._m = None
                _log.error(f"unknown consumer: stack {zeile['eid']} not processed ({type(e).__name__}: {e}) — the "
                           "read position stays, the next round tries again")
                return "fehler", f"{zeile['eid']}: {type(e).__name__}: {e}"
        return None

    def _identitaeten(self):
        """Die Identitaeten ueber den einen Leser core.unbekanntpool._cluster_lesen (W25).
        -> {uid: Identitaet}"""
        from core import unbekanntpool as _up           # noqa: PLC0415
        return {u["id"]: u for u in _up._cluster_lesen(_wert(self.cfg, "data_dir")) if u.get("id")}

    def _nachraeumen(self):
        """Bindungen, deren Identitaet fehlt, loesen (Abbruch zwischen Bindung und Identitaetszeile, W21).
        -> Zahl der geloesten Saetze"""
        from core import refquelle as _rq               # noqa: PLC0415
        ids = set(self._identitaeten())
        waisen = [r for uid, ms in _rq.unknown_members(self.cfg).items() if uid not in ids for r, _e in ms]
        if not waisen:
            return 0
        n = _rq.unknown_release(self.cfg, waisen, _rq.basis.UNKNOWN_ORPHAN_REASON)
        _log.warning(f"unknown consumer: {n} binding(s) to an identity that does not exist released (interrupted stack)")
        return n

    def _stapel(self, z, zeile, jetzt):
        """Ein Stapel unter pool_lock: Wiederholung loesen, Gruppen decken, binden, Identitaeten schreiben, Meldungen.
        -> Liste (uid, Gruppe, neu)"""
        from core import refquelle as _rq               # noqa: PLC0415
        gruppen = _stapel_gruppen(zeile["pfad"])
        self._wiederholung_loesen(zeile["eid"], {r for _i, g in gruppen for r in g["ref_ids"]})
        self._matrix_frisch()
        durchgang, eids, fach = durchgang_einordnen(z, self.cfg, zeile)
        im_gang = {uid for uid, ms in _rq.unknown_members(self.cfg).items() for _r, e in ms if e in eids}
        zuordnung = self._decken(gruppen, im_gang)
        for uid, g, _neu in zuordnung:
            _rq.unknown_bind(self.cfg, g["ref_ids"], uid)
        idents = self._identitaeten_schreiben(zuordnung, zeile)
        karenz = float(_wert(self.cfg, "szene_karenz_s"))
        gruende = [meldung_vormerken(z, fach, durchgang, zeile, uid, g, idents[uid], jetzt, karenz, self.alt_grenze_s)
                   for uid, g, _neu in zuordnung]
        # Bauplan analysen/bauplan_aehnlich.md Entscheid 24: die Zeit des letzten Stapels je Identitaet, fuer das Warten des
        # Zusammenfuehrens auf den abgeschlossenen Durchgang; aeltere als die Karenz zaehlen nicht mehr und fallen weg.
        z[ZULETZT] = dict({u: t for u, t in (z.get(ZULETZT) or {}).items() if jetzt - float(t) < karenz},
                          **{uid: round(jetzt, 1) for uid, _g, _neu in zuordnung})
        self._m["stand"] = self._matrix_stand()         # die eigenen Zeilen stehen schon in der Matrix
        _log.info(f"unknown consumer: stack {zeile['eid']} — {len(zuordnung)} group(s): "
                  + ", ".join(f"{uid}{' (new)' if neu else ''} {grund}"
                              for (uid, _g, neu), grund in zip(zuordnung, gruende)) + f"; pass {durchgang}")
        return zuordnung

    def _wiederholung_loesen(self, eid, neu_ids):
        """Eine zweite Zeile zum selben Ereignis ersetzt die erste (W6): Bindungen des Ereignisses, die nicht mehr im
        Stapel stehen, loesen und ihre Saetze verwerfen. -> Zahl der geloesten Saetze"""
        from core import lernlauf as _ll                # noqa: PLC0415
        from core import refquelle as _rq               # noqa: PLC0415
        alt = sorted({r for ms in _rq.unknown_members(self.cfg).values() for r, e in ms if e == eid and r not in neu_ids})
        if not alt:
            return 0
        n = _rq.unknown_release(self.cfg, alt, _rq.basis.UNKNOWN_REPLACED_REASON)
        _ll.saetze_verwerfen(self.cfg, alt, _rq.basis.UNKNOWN_REPLACED_REASON)
        _log.info(f"unknown consumer: repeated analysis of {eid} — {n} set(s) of the first run released and discarded")
        return n

    def _decken(self, gruppen, im_gang):
        """Die Deckung je Gruppe gegen die Matrix (zuerst der Durchgang, harte Regel je Stapel-Zeile); eine neue
        Identitaet bekommt die naechste freie Nummer. -> Liste (uid, Gruppe, neu)"""
        latte = float(_wert(self.cfg, "unbekannt_latte"))
        fp = self._fingerabdruecke([r for _i, g in gruppen for r in g["ref_ids"]])
        aus, verboten = [], {}
        for i, g in gruppen:
            rids = [r for r in g["ref_ids"] if r in fp]
            if not rids:
                _log.warning(f"unknown consumer: a group without a readable fingerprint left out ({len(g['ref_ids'])} "
                             "set(s))")
                continue
            modell = fp[rids[0]][1]
            vek = np.stack([fp[r][0] for r in rids if fp[r][1] == modell])
            uid, _cos = deckung(self._m["vek"], self._m["uid"], self._m["modell"], vek, modell, latte, im_gang,
                                verboten.get(i, ()))
            neu = uid is None
            if neu:
                uid = f"U{max([_uid_nummer(u) for u in self._m['uid'] + list(self._identitaeten())] + [0]) + 1}"
            verboten.setdefault(i, set()).add(uid)
            im_gang.add(uid)
            self._m["vek"] = np.concatenate([self._m["vek"], vek])
            self._m["uid"] += [uid] * len(vek)
            self._m["modell"] += [modell] * len(vek)
            aus.append((uid, g, neu))
        return aus

    def _identitaeten_schreiben(self, zuordnung, zeile):
        """Identitaetszeilen anlegen oder erweitern (first_seen, last_seen; eine archivierte lebt wieder auf) und die Datei
        ueber anlernen._speichere_unbekannte ersetzen (unter pool_lock, W25). -> {uid: Identitaet}"""
        import anlernen                                 # noqa: PLC0415
        from core import unbekanntpool as _up           # noqa: PLC0415
        start = float(zeile["start"])
        liste = list(_up._cluster_lesen(_wert(self.cfg, "data_dir")))
        nach_id = {u.get("id"): u for u in liste}
        for uid, _g, _neu in zuordnung:
            u = nach_id.get(uid)
            if u is None:
                u = {"id": uid, "created": start, "first_seen": start, "last_seen": start, "status": STATUS_AKTIV,
                     "label": None}
                liste.append(u)
                nach_id[uid] = u
                _log.info(f"unknown consumer: new identity {uid} from event {zeile['eid']}")
                continue
            u["first_seen"] = min(u.get("first_seen") or start, start)
            u["last_seen"] = max(u.get("last_seen") or start, start)
            if u.get("status") == STATUS_ARCHIV:
                u["status"] = STATUS_AKTIV
                _log.info(f"unknown consumer: archived identity {uid} seen again in {zeile['eid']} — reactivated")
        if zuordnung:
            anlernen._speichere_unbekannte(liste)
        return nach_id

    def _matrix_stand(self):
        """Das Stand-Merkmal der Matrix: Katalog-Stand, Identitaetsdatei, Pool-Datei (W13).
        -> Liste"""
        import anlernen                                 # noqa: PLC0415
        from core import refquelle as _rq               # noqa: PLC0415
        return [_rq.state_id(self.cfg), _stempel(anlernen.UNB_PATH), _stempel(anlernen.GES_PATH)]

    def _matrix_frisch(self):
        """Die Matrix neu zusammensetzen, wenn sich ihr Stand geaendert hat (W13): gebundene Saetze jeder bestehenden
        Identitaet und der Altbestand. -> None"""
        from core import refquelle as _rq               # noqa: PLC0415
        stand = self._matrix_stand()
        if self._m is not None and self._m["stand"] == stand:
            return
        # Bauplan analysen/bauplan_aehnlich.md Entscheide 23 und 25: das Sammelbecken ist kein Ziel der Deckung.
        idents = {uid: d for uid, d in self._identitaeten().items() if not _aeh.sammel_von(d)}
        mitglieder = {uid: ms for uid, ms in _rq.unknown_members(self.cfg).items() if uid in idents}
        fp = self._fingerabdruecke([r for ms in mitglieder.values() for r, _e in ms])
        zeilen = [(uid, fp[r][0], fp[r][1]) for uid, ms in sorted(mitglieder.items()) for r, _e in ms if r in fp]
        alt = self._altbestand(idents)
        alle = zeilen + alt
        self._m = {"vek": (np.stack([v for _u, v, _m in alle]) if alle
                           else np.zeros((0, _rq.basis.FINGERPRINT_DIM), np.float32)),
                   "uid": [u for u, _v, _m in alle], "modell": [m for _u, _v, m in alle], "stand": stand}
        _log.info(f"unknown consumer: matrix built — {len(zeilen)} bound set(s) and {len(alt)} legacy pool face(s) "
                  f"for {len(idents)} identities")

    def _fingerabdruecke(self, ref_ids):
        """Fingerabdruecke ueber core.refquelle.read_fingerprints, je Satz einmal je Prozess (Saetze sind
        unveraenderlich). -> {ref_id: (Vektor, Modell)} nur der lesbaren"""
        from core import refquelle as _rq               # noqa: PLC0415
        fehlt = [r for r in dict.fromkeys(ref_ids) if r not in self._vek]
        if fehlt:
            got = _rq.read_fingerprints(self.cfg, fehlt)
            for r, v in got["vek"].items():
                self._vek[r] = (v, got["modell"][r])
            if got["ausgelassen"]:
                _log.warning(f"unknown consumer: {len(got['ausgelassen'])} set(s) without a readable fingerprint left "
                             f"out ({', '.join(sorted(set(got['ausgelassen'].values())))})")
        return {r: self._vek[r] for r in ref_ids if r in self._vek}

    def _altbestand(self, idents):
        """Die Altbestand-Mitglieder: Pool-Zeilen der Liste members ueber anlernen.pool_mit_fingerabdruck, nur nach dem
        Kandidaten-Tor des Workers aus den gespeicherten Werten (W12). -> Liste (uid, Vektor, Modell)"""
        import anlernen                                 # noqa: PLC0415
        import worker_kern as _wk                       # noqa: PLC0415  das eine Kandidaten-Tor
        stempel = [_stempel(anlernen.UNB_PATH), _stempel(anlernen.GES_PATH)]
        if self._alt is not None and self._alt[0] == stempel:
            return self._alt[1]
        wem = {m: uid for uid, u in idents.items() for m in (u.get("members") or []) if isinstance(m, str)}
        zeilen = [g for g in anlernen.lade_gesichter() if g.get("id") in wem]
        aus = []
        for g in anlernen.pool_mit_fingerabdruck(zeilen)[0] if zeilen else []:
            if ((g.get("kante") or 0) >= _wk.KAND_KANTE and (g.get("det") or 0) >= _wk.KAND_DET
                    and (g.get("front") or 0) >= _wk.KAND_FRONT and g.get("emb")):
                v = np.asarray(g["emb"], np.float32)
                aus.append((wem[g["id"]], v / (np.linalg.norm(v) + 1e-9), g.get("modell")))
        self._alt = (stempel, aus)
        return aus
