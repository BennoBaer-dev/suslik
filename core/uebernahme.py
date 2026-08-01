"""E4b — Uebernahme benannter Anker in die Referenzbibliothek (Bauplan §E4b).

Kontrakt wie core/benennung.py: reine Logik, Schwellen/Pfade vom Aufrufer,
Datei-Effekte nur in uebernehmen() mit dem Alles-oder-nichts-Vertrag
("Uebernahme-Abbruch-Fall: nichts halb" — QS E4b). Der Drift-Waechter und die
refcache-Invalidierung laufen im Dienst-Mantel (dieselbe Nacharbeit wie beim
Pool-Enrollment). FIXPUNKT-KLARSTELLUNG (QS E4b): die abnahme-Solls werden hier
NIE angefasst — der Waechter prueft gegen sie, aktualisiert sie nicht.

Verbindlicher Dedup (Bauplan 4b): erst hier, gegen den JETZT-Zustand — innerhalb
der Auswahl UND gegen frueher uebernommene Lern-Referenzen derselben Person (aus
dem Protokoll, das je Datei das Embedding festhaelt). Manuell hochgeladene
Referenzen tragen keine gespeicherten Embeddings; sie werden NICHT verglichen
und das Protokoll weist das aus (kein stilles "0 uebersprungen")."""
import json
import os
import tempfile

import numpy as np


def _cos(a, b):
    va, vb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    na, nb = float(np.linalg.norm(va)), float(np.linalg.norm(vb))
    if na <= 0.0 or nb <= 0.0 or not (np.isfinite(va).all() and np.isfinite(vb).all()):
        return None
    return float(np.dot(va, vb) / (na * nb))


def _protokoll_pfad(data_dir):
    return os.path.join(data_dir, "state", "uebernahmen.jsonl")


def protokoll_lesen(data_dir):
    """Alle Protokoll-Zeilen (unlesbare GEZAEHLT, nie still verworfen)."""
    p = _protokoll_pfad(data_dir)
    zeilen, kaputt = [], 0
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for z in f:
                if not z.strip():
                    continue
                try:
                    zeilen.append(json.loads(z))
                except Exception:
                    kaputt += 1
    return zeilen, kaputt


def protokoll_anhaengen(data_dir, eintrag):
    p = _protokoll_pfad(data_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def adoptierte_embs(data_dir, person):
    """Embeddings frueher uebernommener Lern-Referenzen dieser Person (Protokoll)."""
    zeilen, _k = protokoll_lesen(data_dir)
    aus = []
    for z in zeilen:
        if z.get("person") == person:
            for d in z.get("dateien") or []:
                if d.get("emb"):
                    aus.append(d["emb"])
    return aus


def bedingungs_tag_pruefen(anker, aktuelle_werte):
    """Bauplan: weicht der Tag der Benennung von den JETZT-Werten ab -> LAUT
    ausweisen und neu bestaetigen lassen, nie still ersetzen.
    -> Liste der Abweichungen (leer = identisch)."""
    tag = (anker.get("auswahl") or {}).get("bedingungs_tag") or {}
    ab = []
    for k, v in aktuelle_werte.items():
        if k in tag and tag[k] != v:
            ab.append(f"{k}: named with {tag[k]!r}, now {v!r}")
    return ab


def plan_bauen(anker, dup_sim, bestands_embs):
    """Verbindlicher Dedup-Plan ueber die PERSISTIERTE Auswahl (nie neu empfehlen —
    Bauplan: E4b uebernimmt GENAU die benannte Menge, prueft sie nur auf Duplikate).
    Reihenfolge deterministisch (front/sharp/det/id wie die Benennungs-Reihung).
    -> {aufnehmen: [mitglied...], uebersprungen: [{datei, grund}...]}"""
    from core.benennung import _reihung
    gewaehlt = [m for m in (anker.get("mitglieder") or []) if m.get("gewaehlt")]
    aufnehmen, uebersprungen, gesehen = [], [], [list(e) for e in bestands_embs]
    for m in sorted(gewaehlt, key=_reihung):
        naher = None
        if m.get("emb"):
            for e in gesehen:
                s = _cos(m["emb"], e)
                if s is not None and s >= float(dup_sim):
                    naher = True
                    break
        if naher:
            uebersprungen.append({"datei": str(m.get("datei", "")),
                                  "grund": f"near-identical to an existing learned reference (sim >= {dup_sim})"})
            continue
        aufnehmen.append(m)
        if m.get("emb"):
            gesehen.append(m["emb"])
    return {"aufnehmen": aufnehmen, "uebersprungen": uebersprungen}


def uebernehmen(data_dir, lauf_id, anker_id, person, plan, kopierer=None):
    """Referenzen schreiben — ALLES ODER NICHTS je Aufruf: erst jede Quelle in eine
    Temp-Datei im Zielordner kopieren; erst wenn ALLE Kopien stehen, werden sie auf
    ihre Endnamen umbenannt (os.replace, gleicher Ordner). Scheitert irgendetwas
    vor dem ersten replace, werden alle Temps entfernt und es bleibt NICHTS zurueck.
    -> Liste der Zieldateinamen. Wirft bei fehlender Quelle/Kopierfehler."""
    import shutil
    kop = kopierer or shutil.copyfile
    lauf_dir = os.path.join(data_dir, "state", "lernlauf", lauf_id)
    ziel_dir = os.path.join(data_dir, "faces", person)
    os.makedirs(ziel_dir, exist_ok=True)
    temps, paare = [], []
    try:
        for m in plan["aufnehmen"]:
            quelle = os.path.join(lauf_dir, str(m.get("datei", "")))
            if not os.path.isfile(quelle):
                raise FileNotFoundError(f"crop missing: {m.get('datei')}")
            base = os.path.basename(str(m.get("datei", "")))
            ziel_name = f"lern_{anker_id}_{base}"
            fd, tmp = tempfile.mkstemp(dir=ziel_dir, prefix=".lern.", suffix=".tmp")
            os.close(fd)
            temps.append(tmp)
            kop(quelle, tmp)
            paare.append((tmp, os.path.join(ziel_dir, ziel_name), ziel_name))
    except Exception:
        for t in temps:
            try:
                os.unlink(t)
            except OSError:
                pass
        raise
    namen = []
    for tmp, ziel, name in paare:
        os.replace(tmp, ziel)
        namen.append(name)
    return namen
