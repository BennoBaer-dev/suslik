"""core/aehnlich — die Regel „ähnlich zu P“: eine Unbekannt-Identität, deren Gesichter klar auf eine bekannte Person P
zeigen; angezeigt heißt die Gruppe „Probably recognized“, die Karte „probably P“ (Entscheid 12, der Name im Code bleibt).

HERKUNFT: Bauplan analysen/bauplan_aehnlich.md, Fassung 2 (Eigentümer 15.10.2026 10:01:06 „ok“), Stufe AE1 mit den
Entscheiden 2 bis 5 und 9; Fassung 4 (Eigentümer 15.10.2026 12:46:24 „Ok zu Fassung 4 des Bauplans ähnlich, mit
Mindestzahl 2 über die Config.“), Stufe AE2 Punkt 1 mit den Entscheiden 11, 14 und 17; Widerleger-Befunde W1 bis W6, W9,
W17 (backups/release3_bau/aehnlich/widerleger.md) und W3 V2, V3, V5, V6, V8 (widerleger_f3.md). Die Grenzen kommen aus
der Config (Entscheide 6 und 11); Werkswerte in core.registry.AEHNLICH_WERK. Fassung 6 (Eigentümer 15.10.2026 14:57:02
„Ok zu Fassung 6 des Bauplans ähnlich, mit dem Vorschlag zum Urteil Fremder.“), Stufe AE5 Punkt 2 mit den Entscheiden 19
und 20; W5 V1 bis V7 (widerleger_f5.md). Fassung 8 (Eigentümer 15.10.2026 19:52:22 „Ok zu Fassung 8 des Bauplans
ähnlich, Sammelbecken ähnlich P je Person mit den Befunden des Widerlegers.“), Stufe AE6 Punkt 1 mit den Entscheiden 24
bis 27; W7 V1 bis V10 (widerleger_f7.md).

DAS SAMMELBECKEN „ÄHNLICH P“ (Entscheide 23 bis 27): eine Identitätszeile mit dem Feld SAMMEL (Wert die Person P) und dem
Merkmal zu P. Es ist fest: die Einstufung lässt es aus und ändert sein Merkmal nicht; die Anzeigen lesen es über vermutlich
wie das Merkmal, ein Urteil „nicht P“ für das ganze Becken gibt es nicht. Zusammengeführt wird im Aufräum-Schritt
(core/unbekannt_verbraucher.py); die Bilder aus einem Fremder-Durchgang nennt fremde_im_becken.

DIE REGEL (regel, reine Funktion, Entscheide 2 und 11), gerechnet wie die Einmal-Rechnung backups/aehnlich_rechnung/
alt_aehnlich.py: erst ab aehnlich_min_gesichter Gesichtern; je Gesicht der Wert zu jeder bekannten Person; P ist die
Person, die bei mehr als der Hälfte der Gesichter den besten Wert hat (bei einem Gesicht dessen beste Person), ohne
solche Mehrheit nicht ähnlich; der Median der Werte zu P muss mindestens aehnlich_latte sein; je Gesicht der Abstand =
Wert zu P minus bester Wert einer anderen Person (zeigt das Gesicht auf eine andere Person, ist er negativ), dessen
Median mindestens aehnlich_abstand. Mit weniger als zwei Personen ist kein Abstand bestimmbar: nichts ist ähnlich.

WERTE JE PERSON (Entscheid 3): die Referenzen liest der Dienst wie die anderen Leser außerhalb des Workers
(core.refquelle.read_matrix ohne Zustandsurteil, J11), gesiebt nur nach dem Modellnamen (face_audit.aktuelles_modell);
aufbereitet und gerechnet über die eine Stelle des Workers (worker_kern.referenzen_laden, worker_kern.scores_rechnen:
Wert je Person = Maximum über ihre Referenzen). Gesichter eines anderen Modells zählen nicht.

GESICHTER (Entscheid 4): alle Mitglieder einer Identität mit Fingerabdruck, ohne Kandidaten-Tor; Identitäten und
Mitglieder über die einen Leser core.unbekanntpool.identitaeten und core.unbekanntpool.mitglieder, die Fingerabdrücke der
gebundenen Sätze über core.refquelle.read_fingerprints, die des Altbestands über anlernen.pool_mit_fingerabdruck. Kein
eigener Dateizugriff.

EINSTUFUNG ALLER IDENTITÄTEN (einstufen_alle, Entscheide 14 und 17): der Verbraucher-Faden ruft sie im Aufräum-Schritt;
geschrieben wird nur dort (core/unbekannt_verbraucher.py). Identitäten mit Status besucher oder Merkmal objekt werden
nicht eingestuft, ihr Ziel ist „kein Merkmal“; archivierte werden eingestuft wie aktive. Eine Identität, von der ein
Mitglied nicht lesbar ist (Satz ohne lesbaren Fingerabdruck, Altbestand-Zeile ohne brauchbaren Fingerabdruck), bekommt
kein Ziel: ihr Merkmal bleibt unverändert (WARNING beim Verbraucher).

DAS MERKMAL (Entscheid 14): das Feld MERKMAL der Identitätszeile, ein dict mit Person, Median, Abstand, Zahl der
Gesichter, Zeit und den Grenzen, mit denen geurteilt wurde. merkmale_setzen setzt NUR dieses Feld in die frisch gelesenen
Zeilen und nur, wo es sich ändert; verglichen werden Person, Zahl der Gesichter, Median und Abstand auf zwei Stellen (die
Zeit zählt nicht, W3 V2).

DAS URTEIL „NICHT P“ (Entscheid 20, W5 V3): das Feld URTEIL der Identitätszeile neben MERKMAL, eine Liste {person, ts}
verneinter Personen. Geschrieben über urteil_schreiben (anlernen.pool_lock, frisch gelesen, nur dieses Feld). Die
Einstufung verwirft nur das Ergebnis P, wenn P in der Liste steht; zeigt die Mehrheit auf eine andere Person Q, urteilt die
Regel über Q wie sonst. Neu-Ordnen und Zusammenlegen tragen die Liste weiter (anlernen, urteile_vereinigen).

DAS FREMDER-URTEIL (Entscheid 20, abgenickt 14:57:02, W5 V7): ein Durchgang, den der Nutzer als Fremden bestätigt hat
(gt_fremd aus szenarien.szenarien_des_tages, dieselbe Quelle wie die Trennung der Heute-Seite), verneint die Person des
Merkmals für jede Identität mit einem Gesicht aus diesem Durchgang; es wird nicht in die Zeile geschrieben.

DIE ANZEIGEN (Entscheide 19 und 21) lesen Merkmal und Urteil zusammen über vermutlich: steht die Person des Merkmals im
Urteil, oder ist die Identität ausgenommen (besucher, objekt), zählt das Merkmal nicht, ohne auf den nächsten Aufräum-Schritt
zu warten.

SPEICHER (Entscheid 5, W17): im Speicher des Dienstes unter einer Sperre: die aufbereiteten Referenzen je Katalog-Stand und
Modell, die Fingerabdrücke je Satz (Sätze sind unveränderlich), der Altbestand je Stand der Pool-Datei, die Ereignisse der
Fremder-Durchgänge je Stand von Akte und Wahrheits-Datei.

FEHLERWEG (Entscheide 9 und 17, AGENTS.md „Fehler laut“, ED008): als Lesefehler zählt jede Ausnahme und jede Fehlermeldung
der Leser (Identitäten, Mitglieder, Fingerabdrücke, Referenzen, Grenzen); dann gibt einstufen_alle kein Ziel, der
Aufräum-Schritt ändert kein Merkmal, eine ERROR-Zeile (einmal je Katalog-Stand), stand() und rot() sind rot, bis ein
Aufräum-Schritt wieder gelingt (lauf_eintragen). Der Zustand für /health ist der des Aufräum-Schritts (W3 V6); die
Heute-Seite rechnet nicht mehr (Entscheid 16), sie liest das Merkmal (merkmal_von).

EHRLICHE GRENZEN:
  - Ein Satz, dessen Fingerabdruck nicht lesbar ist, wird bei jeder Einstufung neu versucht; die WARNING kommt einmal je
    Satz und Prozess.
  - Der Altbestand wird ganz gelesen, wenn sich die Pool-Datei ändert (anlernen.lade_gesichter); im Betrieb wächst sie
    nicht mehr (Altbestand, nur gelesen).
  - Eine Altbestand-Kennung, die in der Pool-Datei fehlt, ist kein Lesefehler (der Reconcile räumt sie); sie zählt nicht.
  - stand() liest den Zustand ohne die Sperre (eine Kopie des dict), damit /health nie auf eine Einstufung wartet.
  - Gibt es ein Fremder-Urteil, liest die Einstufung die ganze Akte (state/deckung.jsonl) neu, sobald sie sich geändert hat,
    und bildet die Durchgänge der Tage mit einem solchen Urteil; ohne Fremder-Urteil liest sie nur die Wahrheits-Datei.
"""
import collections
import datetime
import os
import threading
import time

import numpy as np

from core import logbuch as _logbuch

_log = _logbuch.logger(__name__)

# Die Config-Namen der drei Grenzen; Werkswerte und Herkunft in core.registry.AEHNLICH_WERK (dort nur gezogen von
# verifyd.load_config, Entscheide 6 und 11).
LATTE_KEY = "aehnlich_latte"
ABSTAND_KEY = "aehnlich_abstand"
MINDEST_KEY = "aehnlich_min_gesichter"
# Entscheid 14: der Name des Felds an der Identitätszeile (neben objekt).
MERKMAL = "aehnlich"
# Entscheid 20 (Fassung 6, W5 V3): der Name des Felds mit dem Urteil „nicht P“, eine Liste {person, ts}.
URTEIL = "aehnlich_nein"
# Entscheid 25 (Fassung 8): der Name des Felds am Sammelbecken „ähnlich P“, Wert die Person P.
SAMMEL = "sammel"
STELLEN = 2                      # Entscheid 14: Median und Abstand werden auf zwei Stellen verglichen


def regel(werte, personen, latte, abstand, mindest):
    """Die Regel „ähnlich zu P“ über die Werte einer Identität (Entscheide 2 und 11); werte [Gesichter, Personen] in der
    Spaltenfolge von personen. -> dict person, median, abstand, gesichter, oder None (nicht ähnlich)"""
    w = np.asarray(werte, np.float32)
    if w.ndim != 2 or w.shape[1] != len(personen):
        raise ValueError(f"similar rule: values of shape {w.shape} for {len(personen)} person(s)")
    n = w.shape[0]
    if n == 0 or n < mindest or w.shape[1] < 2:
        return None
    p, anzahl = collections.Counter(w.argmax(axis=1).tolist()).most_common(1)[0]
    if not (n == 1 or anzahl * 2 > n):
        return None
    zu_p = w[:, p]
    median = float(np.median(zu_p))
    vorsprung = float(np.median(zu_p - np.delete(w, p, axis=1).max(axis=1)))
    if median < latte or vorsprung < abstand:
        return None
    return {"person": personen[p], "median": median, "abstand": vorsprung, "gesichter": n}


def grenzen(cfg):
    """Die drei Grenzen der Regel aus der Config, ohne eigenen Werkswert (der steht in load_config).
    -> (latte, abstand, mindest); fehlt ein Schlüssel, KeyError; ein unlesbarer Wert ValueError"""
    fehlt = [k for k in (LATTE_KEY, ABSTAND_KEY, MINDEST_KEY) if not isinstance(cfg, dict) or cfg.get(k) is None]
    if fehlt:
        raise KeyError(f"config key(s) missing: {', '.join(fehlt)}")
    return float(cfg[LATTE_KEY]), float(cfg[ABSTAND_KEY]), int(cfg[MINDEST_KEY])


def merkmal(ergebnis, grenz, ts):
    """Das Merkmal einer ähnlichen Identität aus dem Ergebnis der Regel (Entscheid 14).
    -> dict person, median, abstand, gesichter, ts, grenzen"""
    return {"person": ergebnis["person"], "median": round(ergebnis["median"], 4),
            "abstand": round(ergebnis["abstand"], 4), "gesichter": int(ergebnis["gesichter"]), "ts": round(ts, 1),
            "grenzen": dict(zip((LATTE_KEY, ABSTAND_KEY, MINDEST_KEY), grenz))}


def merkmal_von(zeile):
    """Das Merkmal einer Identitätszeile, wenn es die Felder der Anzeige trägt (die Heute-Seite liest nur so).
    -> dict oder None"""
    m = zeile.get(MERKMAL) if isinstance(zeile, dict) else None
    if not (isinstance(m, dict) and isinstance(m.get("person"), str) and m["person"]
            and all(isinstance(m.get(k), (int, float)) for k in ("median", "abstand", "gesichter"))):
        return None
    return m


def _urteile(zeile):
    """Die gültigen Einträge des Urteils „nicht P“ einer Identitätszeile (Entscheid 20). -> Liste {person, ts}"""
    u = zeile.get(URTEIL) if isinstance(zeile, dict) else None
    return [e for e in u if isinstance(e, dict) and isinstance(e.get("person"), str) and e["person"]] \
        if isinstance(u, list) else []


def verneint(zeile):
    """Die Personen, die der Nutzer für diese Identität verneint hat (Urteil „nicht P“, Entscheid 20).
    -> Menge der Namen"""
    return {e["person"] for e in _urteile(zeile)}


def sammel_von(zeile):
    """Die Person P, wenn die Identitätszeile das Sammelbecken „ähnlich P“ ist (Entscheid 25).
    -> Name oder None"""
    s = zeile.get(SAMMEL) if isinstance(zeile, dict) else None
    return s if isinstance(s, str) and s else None


def becken_setzen(zeile, person):
    """Eine Identitätszeile zum Sammelbecken „ähnlich person“ machen (Entscheide 24 und 25): das Feld SAMMEL, Status
    aktiv; das Merkmal zu person bleibt, wie es ist. -> True, wenn sich die Zeile geändert hat"""
    from core import unbekannt_verbraucher as _uv        # noqa: PLC0415  die eine Quelle der Status-Namen
    if sammel_von(zeile) == person and zeile.get("status") == _uv.STATUS_AKTIV:
        return False
    zeile[SAMMEL] = person
    zeile["status"] = _uv.STATUS_AKTIV
    return True


def vermutlich(zeile):
    """Das Merkmal, wie die Anzeigen es lesen (Entscheide 19, 21 und 27): Merkmal und Urteil zusammen; steht die Person im
    Urteil oder ist die Identität ausgenommen (besucher, objekt), zählt es nicht. Am Sammelbecken zählt das Merkmal seiner
    Person ohne Urteil (Entscheid 25: kein „nicht P“ für das ganze Becken). -> dict oder None"""
    m = merkmal_von(zeile)
    if m is None or ausgenommen(zeile):
        return None
    p = sammel_von(zeile)
    if p is not None:
        return m if m["person"] == p else None
    return None if m["person"] in verneint(zeile) else m


def urteil_setzen(zeile, person, an, ts):
    """Das Urteil „nicht person“ in einer Identitätszeile setzen (an) oder zurücknehmen; nur das Feld URTEIL, eine leere
    Liste fällt weg (Entscheid 20). -> True, wenn sich die Zeile geändert hat"""
    liste = _urteile(zeile)
    if an:
        if person in {e["person"] for e in liste}:
            return False
        liste.append({"person": person, "ts": round(ts, 1)})
    else:
        neu = [e for e in liste if e["person"] != person]
        if len(neu) == len(liste):
            return False
        liste = neu
    if liste:
        zeile[URTEIL] = liste
    else:
        zeile.pop(URTEIL, None)
    return True


def urteile_vereinigen(a, b):
    """Die Urteile zweier Identitätszeilen vereinigt, für das Zusammenlegen (Entscheid 20, W5 V2); je Person der
    früheste Eintrag. -> Liste {person, ts} (leer ohne Urteil)"""
    out = {}
    for e in _urteile(a) + _urteile(b):
        alt = out.get(e["person"])
        if alt is None or (e.get("ts") or 0) < (alt.get("ts") or 0):
            out[e["person"]] = dict(e)
    return list(out.values())


def urteil_schreiben(uid, person, an, ts=None):
    """Das Urteil „nicht person“ an der Identität uid schreiben oder zurücknehmen, über den bestehenden Schreibweg: unter
    anlernen.pool_lock frisch gelesen, nur das Feld URTEIL gesetzt, anlernen._speichere_unbekannte (Entscheide 14, 20).
    -> (gefunden, geändert)"""
    import anlernen                                  # noqa: PLC0415  der eine Schreibweg der Identitätsdatei
    ts = time.time() if ts is None else ts
    with anlernen.pool_lock():
        zeilen = anlernen.lade_unbekannte()
        treffer = [z for z in zeilen if isinstance(z, dict) and z.get("id") == uid]
        geaendert = [z for z in treffer if urteil_setzen(z, person, an, ts)]
        if geaendert:
            anlernen._speichere_unbekannte(zeilen)
    return bool(treffer), bool(geaendert)


def _vergleich(m):
    """Die Vergleichsfelder eines Merkmals (Entscheid 14). -> Tupel oder None"""
    if not isinstance(m, dict):
        return None
    return (m.get("person"), m.get("gesichter"), round(float(m.get("median") or 0), STELLEN),
            round(float(m.get("abstand") or 0), STELLEN))


def ausgenommen(zeile):
    """Wird diese Identität nicht eingestuft (Status besucher oder Merkmal objekt, Entscheid 14)?
    -> bool"""
    from core import unbekannt_verbraucher as _uv        # noqa: PLC0415  die eine Quelle der Status-Namen
    return zeile.get("status") == _uv.STATUS_BESUCHER or bool(zeile.get(_uv.MERKMAL_OBJEKT))


def merkmale_setzen(zeilen, ziel):
    """Das Feld MERKMAL in den frisch gelesenen Identitätszeilen nach dem Ziel setzen oder entfernen, nur wo es sich
    ändert; Identitäten ohne Ziel und alle anderen Felder bleiben, eine inzwischen ausgenommene verliert es (Entscheid 14),
    ebenso eine, deren Person inzwischen im Urteil „nicht P“ steht (Entscheid 20). -> Liste der geänderten Kennungen"""
    geaendert = []
    for z in zeilen:
        uid = z.get("id")
        if uid not in ziel:
            continue
        neu = None if ausgenommen(z) else ziel[uid]
        if neu is not None and neu["person"] in verneint(z):
            neu = None
        if _vergleich(z.get(MERKMAL)) == _vergleich(neu):
            continue
        if neu is None:
            z.pop(MERKMAL, None)
        else:
            z[MERKMAL] = neu
        geaendert.append(uid)
    return geaendert


def fremde_im_becken(idents, ms, fremd):
    """Die Bilder jedes Sammelbeckens aus einem Durchgang, den der Nutzer als Fremden bestätigt hat (Entscheid 25: der
    Aufräum-Schritt nimmt sie heraus wie „nicht P“ einer Auswahl). -> {Sammelbecken: (Person, [Mitglied-Kennungen])}"""
    out = {}
    for uid, d in idents.items():
        p = sammel_von(d)
        ids = [m["id"] for m in ms.get(uid) or [] if p and str(m.get("eid")) in fremd]
        if ids:
            out[uid] = (p, ids)
    return out


def _stempel(pfad):
    """Größe und Änderungszeit einer Datei als Stand-Merkmal. -> (Byte, mtime_ns) oder None ohne Datei"""
    try:
        st = os.stat(pfad)
    except FileNotFoundError:
        return None
    return st.st_size, st.st_mtime_ns


def _normiert(v):
    """Einen Fingerabdruck L2-normieren (scores_rechnen erwartet normierte Vektoren). -> float32 [512]"""
    v = np.asarray(v, np.float32).ravel()
    return v / (float(np.linalg.norm(v)) or 1.0)


class Speicher:
    """Speicher und Zustand der Einstufung im Dienst (Entscheide 5, 9 und 17): Referenzen, Fingerabdrücke und
    Altbestand unter einer Sperre, dazu der Zustand des letzten Aufräum-Schritts für /health."""

    def __init__(self):
        self._sperre = threading.Lock()
        self._refs = None            # (Katalog-Stand, Modell, Personen mit Referenzen, Aufbereitung des Workers)
        self._saetze = {}            # ref_id -> (Vektor, Modell); Sätze sind unveränderlich
        self._gemeldet = set()       # ref_ids ohne lesbaren Fingerabdruck, schon als WARNING gemeldet
        self._alt = None             # (Stempel der Pool-Datei, {Pool-ID: (Vektor, Modell)}, {Pool-ID ohne Fingerabdruck})
        self._fremd = None           # (Stempel von Wahrheits-Datei und Akte, Ereignisse der Fremder-Durchgänge)
        self._zustand = {"rot": False, "letzter_fehler": None, "fehler_ts": None, "fehler_stand": None,
                         "letzte_ts": None, "letzte_dauer_ms": None, "identitaeten_n": None, "aehnlich_n": None,
                         "personen_n": None, "geaendert_n": None, "unlesbar_n": None, "grenzen": None,
                         "sammel_n": None, "zusammengefuehrt_n": None}

    def einstufen_alle(self, cfg):
        """Alle Identitäten nach der Regel einstufen (Entscheide 14 und 17), ohne zu schreiben; dazu die Bilder der
        Sammelbecken aus Fremder-Durchgängen (Entscheid 25). -> dict ziel {uid: Merkmal oder None}, unlesbar {uid: Grund},
        fremd_raus {Sammelbecken: (Person, [Mitglied-Kennungen])}, grenzen, fehler (Text oder None), dauer_ms"""
        from core import unbekanntpool as _up            # noqa: PLC0415
        t0, ts = time.monotonic(), time.time()
        with self._sperre:
            try:
                grenz = grenzen(cfg)
                meldungen = []
                idents = _up.identitaeten(cfg["data_dir"])
                ms = _up.mitglieder(cfg["data_dir"], idents, log=meldungen.append)
                if meldungen:                            # Entscheid 17: eine Fehlermeldung der Leser ist ein Lesefehler
                    raise LookupError("; ".join(str(m) for m in meldungen))
                modell, personen, erk = self._referenzen(cfg)
                fremd = self._fremde_ereignisse(cfg)
                ziel, unlesbar = self._ziele(cfg, idents, ms, (modell, personen, erk), grenz, ts, fremd)
                raus = fremde_im_becken(idents, ms, fremd)
            except Exception as e:                       # noqa: BLE001  laut: ERROR, /health rot, kein Merkmal geändert
                return {"ziel": {}, "unlesbar": {}, "fremd_raus": {}, "grenzen": None, "fehler": self.fehler(cfg, e),
                        "dauer_ms": None}
        dauer_ms = round((time.monotonic() - t0) * 1000.0, 1)
        _log.debug(f"similar check: {len(ziel)} unknown identities judged, {sum(1 for m in ziel.values() if m)} "
                   f"probably a known person, {len(unlesbar)} with a member not readable, "
                   f"{len(personen)} person(s) with references, {dauer_ms:.1f} ms")
        return {"ziel": ziel, "unlesbar": unlesbar, "fremd_raus": raus, "grenzen": grenz, "fehler": None,
                "dauer_ms": dauer_ms}

    def lauf_eintragen(self, **zahlen):
        """Einen gelungenen Aufräum-Schritt eintragen: grün, Zeit, Dauer, Zahlen und Grenzen (Entscheid 17).
        -> None"""
        self._zustand.update(rot=False, letzte_ts=round(time.time(), 1), **zahlen)

    def stand(self):
        """Der Zustand für /health `aehnlich`: rot, letzter Fehler mit Zeit, letzter Aufräum-Schritt mit Dauer und Zahlen.
        -> dict (Kopie)"""
        z = dict(self._zustand)
        z.pop("fehler_stand", None)
        return z

    def rot(self):
        """Der Teil an health_ok (Entscheide 9 und 17): rot nach einem Fehler, bis ein Aufräum-Schritt wieder gelingt.
        -> bool"""
        return bool(self._zustand["rot"])

    def fehler(self, cfg, e):
        """Einen Fehler des Aufräum-Schritts eintragen (Entscheide 9 und 17): ERROR-Zeile einmal je Katalog-Stand, rot bis
        zum nächsten gelungenen Lauf. -> Fehlertext"""
        from core import refquelle as _rq                # noqa: PLC0415
        text = f"{type(e).__name__}: {e}"
        try:
            stand = _rq.state_id(cfg)
        except Exception:                                # noqa: BLE001  der Stand ist hier nur das Merkmal der Zeile
            _logbuch.swallowed(_log, _logbuch.WARNING, "catalog state unknown")
            stand = None
        z = self._zustand
        if not z["rot"] or z["fehler_stand"] != stand:
            _log.error(f"similar check failed ({text}) — no mark of the unknown identities is changed, the next run "
                       "tries again")
        z.update(rot=True, letzter_fehler=text, fehler_ts=round(time.time(), 1), fehler_stand=stand)
        return text

    def _ziele(self, cfg, idents, ms, refs, grenz, ts, fremd):
        """Das Ziel jeder Identität (Entscheide 4, 14, 17, 20): ausgenommene ohne Merkmal, mit nicht lesbarem Mitglied keins;
        das Ergebnis P fällt weg, wenn P im Urteil „nicht P“ steht oder ein Gesicht aus einem Fremder-Durchgang (fremd)
        stammt. Das Sammelbecken und eine Identität ohne jedes Mitglied bekommen keins (Entscheide 24 und 25: fest, und ein
        abgebrochenes Zusammenführen hinterlässt eine Zeile ohne Mitglieder, die der nächste Lauf noch zusammenführt).
        -> ({uid: Merkmal oder None}, {uid: Grund})"""
        modell, personen, erk = refs
        einstufen = {uid: d for uid, d in idents.items() if not ausgenommen(d) and not sammel_von(d)}
        satz_weg = self._saetze_lesen(cfg, [m["ref_id"] for uid in einstufen
                                            for m in ms.get(uid) or [] if m.get("satz") and m.get("ref_id")])
        brauche_alt = any(not m.get("satz") for uid in einstufen for m in ms.get(uid) or [])
        alt, alt_weg = self._altbestand() if brauche_alt else ({}, {})
        ziel, unlesbar = {}, {}
        for uid, d in idents.items():
            if ausgenommen(d):
                ziel[uid] = None
                continue
            mm = ms.get(uid) or []
            if uid not in einstufen or not mm:
                continue
            weg = [satz_weg.get(m["ref_id"]) if m.get("satz") else alt_weg.get(m["id"]) for m in mm]
            if any(weg):
                unlesbar[uid] = next(g for g in weg if g)
                continue
            erg = self._urteil(mm, modell, personen, erk, grenz, alt)
            if erg and (erg["person"] in verneint(d) or any(str(m.get("eid")) in fremd for m in mm)):
                erg = None
            ziel[uid] = merkmal(erg, grenz, ts) if erg else None
        return ziel, unlesbar

    def _urteil(self, ms, modell, personen, erk, grenz, alt):
        """Das Urteil einer Identität aus ihren Mitgliedern (Entscheide 2 bis 4, 11). -> Ergebnis der Regel oder None"""
        import worker_kern as _wk                        # noqa: PLC0415  die eine Score-Rechnung (Entscheid 3)
        vek = []
        for m in ms:
            v, m_modell = (self._saetze.get(m["ref_id"]) if m.get("satz") else alt.get(m["id"])) or (None, None)
            if v is not None and m_modell == modell:
                vek.append(v)
        if not vek or len(personen) < 2:
            return None
        return regel(_wk.scores_rechnen(np.stack(vek), erk), personen, *grenz)

    def _fremde_ereignisse(self, cfg):
        """Die Ereignisse der Durchgänge, die der Nutzer als Fremden bestätigt hat (gt_fremd, Entscheid 20), über die eine
        Gruppierung szenarien.szenarien_des_tages, je Tag mit einem Fremder-Urteil; je Stand von Wahrheits-Datei und Akte.
        -> frozenset der Ereignis-Kennungen"""
        import auftritte as _auf                         # noqa: PLC0415  die Leser von Akte und Wahrheits-Datei
        import szenarien as _sz                          # noqa: PLC0415
        akte = os.path.join(cfg["data_dir"], "state", "deckung.jsonl")
        gt_pfad = os.path.join(cfg["data_dir"], "state", "ground_truth.jsonl")
        stand = (_stempel(gt_pfad), _stempel(akte))
        if self._fremd is not None and self._fremd[0] == stand:
            return self._fremd[1]
        gtmap = _auf._lade_gtmap(cfg)
        fremd_eids = [eid for eid in gtmap if _sz.gt_hat_fremd(gtmap, eid)]
        out = set()
        if fremd_eids:
            by_h = {r["eid"]: r for r in _auf._lade_rows(akte) if isinstance(r, dict) and r.get("eid")}
            tage = {datetime.datetime.fromtimestamp(by_h[e].get("start") or by_h[e].get("ts") or 0).date()
                    for e in fremd_eids if e in by_h}
            for tag in sorted(tage):
                t0 = datetime.datetime.combine(tag, datetime.time())
                for s in _sz.szenarien_des_tages(by_h, t0.timestamp(), (t0 + datetime.timedelta(days=1)).timestamp(),
                                                 cfg, gtmap):
                    if s.get("gt_fremd"):
                        out.update(str(e["eid"]) for e in s.get("evs") or [] if e.get("eid"))
        self._fremd = (stand, frozenset(out))
        return self._fremd[1]

    def _referenzen(self, cfg):
        """Die aufbereiteten Referenzen je Katalog-Stand und Modell (Entscheid 3, 5).
        -> (Modell, Personen mit Referenzen in Spaltenfolge, Aufbereitung von worker_kern.referenzen_laden)"""
        import face_audit                                # noqa: PLC0415
        import worker_kern as _wk                        # noqa: PLC0415  die eine Aufbereitung (Entscheid 3)
        from core import refquelle as _rq                # noqa: PLC0415
        modell = face_audit.aktuelles_modell()
        if self._refs is None or self._refs[:2] != (_rq.state_id(cfg), modell):
            _alle, mit_refs, erk = _wk.referenzen_laden(_rq.read_matrix(cfg, None), {"modell": modell})
            self._refs = (erk["stand"], modell, mit_refs, erk)
        return self._refs[1:]

    def _saetze_lesen(self, cfg, ref_ids):
        """Fingerabdrücke gebundener Sätze über core.refquelle.read_fingerprints, je lesbarem Satz einmal je Prozess.
        -> {ref_id: Grund} der nicht lesbaren unter ref_ids (WARNING einmal je Satz)"""
        from core import refquelle as _rq                # noqa: PLC0415
        fehlt = [r for r in dict.fromkeys(ref_ids) if r not in self._saetze]
        if not fehlt:
            return {}
        got = _rq.read_fingerprints(cfg, fehlt)
        for r, v in got["vek"].items():
            self._saetze[r] = (_normiert(v), got["modell"][r])
        neu = {r: g for r, g in got["ausgelassen"].items() if r not in self._gemeldet}
        if neu:
            self._gemeldet.update(neu)
            _log.warning(f"similar check: {len(neu)} set(s) without a readable fingerprint — their identities keep "
                         f"their mark ({', '.join(sorted(set(neu.values())))})")
        return dict(got["ausgelassen"])

    def _altbestand(self):
        """Die Fingerabdrücke des Altbestands je Pool-Kennung über anlernen.pool_mit_fingerabdruck, je Stand der
        Pool-Datei (Entscheide 4, 5). -> ({Pool-ID: (Vektor, Modell)}, {Pool-ID: Grund} ohne brauchbaren Fingerabdruck)"""
        import anlernen                                  # noqa: PLC0415  derselbe Pool-Leser wie im Verbraucher
        from core import refquelle as _rq                # noqa: PLC0415
        stempel = _stempel(anlernen.GES_PATH)
        if self._alt is None or self._alt[0] != stempel:
            zeilen, fehlt = anlernen.pool_mit_fingerabdruck()
            karte = {g["id"]: (_normiert(g["emb"]), g.get("modell")) for g in zeilen
                     if g.get("id") and len(g.get("emb") or []) == _rq.basis.FINGERPRINT_DIM}
            self._alt = (stempel, karte, dict(fehlt))
        return self._alt[1], self._alt[2]


# Der eine Speicher des Prozesses (Entscheid 5): der Aufräum-Schritt des Verbraucher-Fadens schreibt seinen Zustand,
# /health, health_ok und der rote Hinweis der Heute-Seite lesen ihn.
SPEICHER = Speicher()
