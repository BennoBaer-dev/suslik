"""E4b — Uebernahme benannter Anker in die Referenzbibliothek (Bauplan §E4b).

Kontrakt wie core/benennung.py: reine Logik, Schwellen/Pfade vom Aufrufer,
Schreib-Effekte nur in in_den_bestand() mit dem Alles-oder-nichts-Vertrag
("Uebernahme-Abbruch-Fall: nichts halb" — QS E4b: erst alles pruefen, dann
schreiben). Der Drift-Waechter laeuft im Dienst-Mantel (dieselbe Nacharbeit wie
beim Pool-Enrollment). FIXPUNKT-KLARSTELLUNG (QS E4b): die abnahme-Solls werden hier
NIE angefasst — der Waechter prueft gegen sie, aktualisiert sie nicht.

Verbindlicher Dedup (Bauplan 4b): erst hier, gegen den JETZT-Zustand — innerhalb
der Auswahl UND gegen frueher uebernommene Lern-Referenzen derselben Person (aus
dem Protokoll, das je Uebernahme die ref_id festhaelt). Manuell hochgeladene
Referenzen tragen keine gespeicherten Embeddings; sie werden NICHT verglichen
und das Protokoll weist das aus (kein stilles "0 uebersprungen").

UEBERNAHME ALS KATALOGZEILE (Bauplan analysen/bauplan_refquelle_einbau.md, Stufe E3
Punkt 1, Schnitt E3a-1d): ein Angebot der Lernlauf-, Vorrats- und Pass-Ernte-Wege ist
seit E3a-1c ein Satz in core/refquelle mit Status kandidat. Uebernehmen heisst
`in_den_bestand`: je ref_id eine Bindung (Person, aktiv wahr) und eine Statuszeile
referenz ueber das Modul — keine Dateikopie, keine refs_meta-Zeile, kein refcache.
Die Herkunft bleibt im Satz. Die Leser des Bestands sehen die neue Referenz erst mit
E3b (Entscheid 16). Ein Angebot ohne ref_id (Lauf vor dieser Version) lehnt die
Uebernahme laut ab, mit Hinweis auf den Umzug (J7, `UMZUG_HINWEIS`)."""
import json
import os

import numpy as np

# J7: ein Angebot aus einem Lauf vor der Referenz-Quelle traegt keine ref_id; der Umzug (E4)
# nimmt die alten Lauf-Ordner mit. Produkt-Text, englisch.
UMZUG_HINWEIS = ("this offer comes from a learning run made before this version (no reference set) and "
                 "cannot be adopted; the one-time migration of this version takes the old runs along")


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
    """Embeddings frueher uebernommener Lern-Referenzen dieser Person — NUR von
    Referenzen, die es noch gibt (.127 Review-MUSS 'Phantom-Dedup': das Protokoll
    wird beim Loeschen von Referenzen/Personen nie nachgezogen; ohne
    Existenz-Pruefung dedupte die Uebernahme gegen Geloeschtes, und der
    already-covered-Abschluss machte die Person still unanlernbar).
    Beides geht ueber das Modul core/refquelle, Lese-Stufe b einmal je Aufruf
    (Nachtrag E3, O595 (1)); den Personenordner liest die Funktion nicht.
    Seit E3a-1d traegt eine Protokoll-Zeile die ref_id: es zaehlt nur ein Satz,
    der noch gebunden und Referenz ist, sein Fingerabdruck kommt ueber das Modul.
    Eine aeltere Zeile (emb + ziel, ohne ref_id) zaehlt, wenn die Person eine aktive
    Referenz (Status referenz oder altbestand, die Auswahl personen der Lese-Stufe b)
    mit genau diesem alten Dateinamen hat (I9: Feld alter_dateiname der Bindung);
    ihr Vektor ist die gespeicherte emb der Zeile, nach dem Umzug E4 bitgleich der
    alte Fingerabdruck dieses Satzes. Steht der Umzug aus (V2), kennt Lese-Stufe b
    keinen Eintrag, und keine aeltere Zeile zaehlt: so gewollt, denn eine Uebernahme
    lehnt das Modul in dieser Zeit ohnehin ab. Zeilen ohne beides zaehlen nicht
    (schlimmstenfalls wird ein Beinahe-Duplikat erneut aufgenommen, nie umgekehrt
    eine Uebernahme verhindert). -> Liste von Vektoren (Listen von Zahlen)."""
    zeilen, _k = protokoll_lesen(data_dir)
    dateien = [d for z in zeilen if z.get("person") == person for d in z.get("dateien") or []]
    if not dateien:
        return []
    from core import refquelle as _rq                      # noqa: PLC0415  spaet wie im Haus
    katalog = _rq.read_catalog({"data_dir": data_dir})
    eintraege = katalog["eintraege"]
    alte_namen = {eintraege[r]["bindung"].get("alter_dateiname") for r in katalog["personen"].get(person, [])}
    aus = [d["emb"] for d in dateien if not d.get("ref_id") and d.get("emb") and d.get("ziel")
           and str(d["ziel"]) in alte_namen]
    rids = [d["ref_id"] for d in dateien if d.get("ref_id")]
    return aus + _bestand_vektoren(data_dir, rids, eintraege)


def _bestand_vektoren(data_dir, ref_ids, eintraege):
    """Die Fingerabdruecke der Saetze, die noch als Referenz gebunden sind (Bindung und Status aus
    den Eintraegen der Lese-Stufe b, die der Aufrufer schon gelesen hat; Lese-Stufe a je Lauf ueber
    core.lernlauf). -> Liste von Listen."""
    if not ref_ids:
        return []
    from core import lernlauf as _ll                       # noqa: PLC0415  spaet wie im Haus
    cfg = {"data_dir": data_dir}
    noch = [r for r in dict.fromkeys(ref_ids) if r in eintraege
            and eintraege[r]["status"].get("status") == "referenz"
            and eintraege[r]["bindung"].get("aktiv") is True and eintraege[r].get("ort")]
    vek = _ll.mitglieder_fingerabdruecke(cfg, noch)
    return [vek[r].tolist() for r in noch if r in vek]


def bestand_da(data_dir, person):
    """Phantom-Wache (Review-MUSS .127, seit E3a-1d ueber das Modul): hat die Person mindestens einen
    Satz, der aktiv an sie gebunden ist (Status referenz oder altbestand, Ordner vorhanden)?
    Lese-Stufe b. -> bool"""
    from core import refquelle as _rq                      # noqa: PLC0415
    return any(e["bindung"].get("person") == person and e["bindung"].get("aktiv") is True
               and e["status"].get("status") in ("referenz", "altbestand") and e.get("ort")
               for e in _rq.read_catalog({"data_dir": data_dir})["eintraege"].values())


def ref_ids(mitglieder):
    """Die ref_ids der Mitglieder oder Angebote; eines ohne ref_id stammt aus einem Lauf vor dieser
    Version (J7). -> Liste der ref_ids; fehlt eine: ValueError mit UMZUG_HINWEIS (laut)."""
    alt = [str(m.get("datei") or "") for m in mitglieder if not m.get("ref_id")]
    if alt:
        raise ValueError(f"{UMZUG_HINWEIS} ({len(alt)} picture(s))")
    return [m["ref_id"] for m in mitglieder]


def in_den_bestand(data_dir, ids, person, grund):
    """Saetze in den Bestand aufnehmen: je ref_id eine Bindung (person, aktiv wahr) und eine Statuszeile
    referenz ueber core/refquelle; erst werden alle geprueft (Lese-Stufe c), dann wird geschrieben; danach zieht
    das Modul den abgeleiteten Personenordner nach (E4-3). Vor dem gruenen Umzug lehnt das Modul die Zeilen ab (V2).
    Bauplan analysen/bauplan_katalog_lebenszyklus.md, Stufe LK1: Anfang (Auswahl) und Ende (Uebernahme oder Fehlschlag
    mit Kennwort) stehen im Journal der Nutzung (refquelle.usage_selection, usage_adoption); eine Ablehnung ist eine
    refquelle.UsageRefusal, also weiter ein ValueError mit demselben Text.
    -> {"neu": [ref_id...], "schon_da": [ref_id...]}; fehlt ein Satz oder ist er nicht aufnehmbar:
    ValueError, und es ist nichts geschrieben."""
    from core import refquelle as _rq                      # noqa: PLC0415
    cfg = {"data_dir": data_dir}
    vorgang = _rq.usage_selection(cfg, ids, __file__)
    neu, da, fertig, schreiben = [], [], [], False
    try:
        for rid in dict.fromkeys(ids):
            s = _rq.read_set(cfg, rid)
            if s is None:
                raise _rq.UsageRefusal(_rq.UsageRefusal.MISSING,
                                       f"reference set {rid} does not exist — nothing adopted")
            if s["fehler"] or s["fingerabdruck"] is None:
                raise _rq.UsageRefusal(_rq.UsageRefusal.DAMAGED, f"reference set {rid} is damaged "
                                       f"({', '.join(sorted(s['fehler'])) or 'fingerprint'}) — nothing adopted")
            bindung, status = s["katalog"]["bindung"], s["katalog"]["status"].get("status")
            if bindung.get("person") == person and bindung.get("aktiv") is True and status == "referenz":
                da.append(rid)
                continue
            if status != "kandidat" or bindung.get("person"):
                raise _rq.UsageRefusal(_rq.UsageRefusal.NOT_ADOPTABLE, f"reference set {rid} cannot be adopted "
                                       f"(status {status}{', bound to a person' if bindung.get('person') else ''})"
                                       " — nothing adopted")
            neu.append(rid)
        schreiben = True
        for rid in neu:
            _rq.append(cfg, rid, "bindung", {"person": person, "aktiv": True, "grund": grund})
            _rq.append(cfg, rid, "status", {"status": "referenz", "grund": grund})
            fertig.append(rid)
    except Exception as e:
        _rq.usage_adoption(cfg, vorgang, fertig, da, e.code if isinstance(e, _rq.UsageRefusal) else (
            _rq.UsageRefusal.WRITE if schreiben else _rq.UsageRefusal.OTHER))
        raise
    _rq.usage_adoption(cfg, vorgang, neu, da)
    if neu:                                  # E4-3 (Entscheid 6): der abgeleitete Personenordner zieht nach
        _rq.build_person_folders(cfg, follow=True)
    return {"neu": neu, "schon_da": da}


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


def plan_bauen(anker, dup_sim, bestands_embs, luma_grenzen=None,
               kat_latten=None):
    """Verbindlicher Dedup-Plan ueber die PERSISTIERTE Auswahl (nie neu empfehlen —
    Bauplan: E4b uebernimmt GENAU die benannte Menge, prueft sie nur auf Duplikate).
    Reihenfolge deterministisch (front/sharp/det/id wie die Benennungs-Reihung).
    luma_grenzen (bauplan_belichtung.md E4, 26.08.) reicht die Belichtungsachse
    der Reihung hier durch — sie entscheidet mit, WELCHES von zwei Beinahe-
    Duplikaten in den Katalog wandert (das besser belichtete gewinnt). Ohne
    Grenzen ist die Reihung Element fuer Element die bisherige.
    kat_latten (Zentral-Umbau 31.08.): die KATALOG-Latte je Kamera
    (core.kamerakalib). Sie sitzt HIER und nicht in uebernehmen(), weil dies
    die Stelle ist, an der ein Bild mit GRUND aussortiert werden kann, bevor
    Dateien angefasst werden — der Nutzer sieht den Grund in derselben Liste
    wie das Dedup-Ergebnis. Das Mitglied traegt kamera + fiqa_t/empf (seit
    .377 wandern die Guete-Masse mit), die Latte beisst hier also real.
    Ungemessene Mitglieder (Alt-Anker) kommen durch — Bestandsschutz.
    .516: dasselbe Register speist seit der Alt-Latten-Abloesung auch die
    REIHUNG (frueher die globale `guete_latte`) — ein Aufruf, eine Latte.
    -> {aufnehmen: [mitglied...], uebersprungen: [{datei, grund}...]}"""
    from core.benennung import _reihung
    from core.kamerakalib import katalog_ok
    gewaehlt = [m for m in (anker.get("mitglieder") or []) if m.get("gewaehlt")]
    aufnehmen, uebersprungen, gesehen = [], [], [list(e) for e in bestands_embs]
    for m in sorted(gewaehlt,
                    key=lambda x: _reihung(x, luma_grenzen=luma_grenzen,
                                           kat_latten=kat_latten)):
        kat_ok, kat_grund = katalog_ok(kat_latten, m.get("kamera"),
                                       m.get("empf"), m.get("fiqa_t"))
        if not kat_ok:
            # Vor dem Dedup: ein Bild, das gar nicht in den Katalog darf, soll
            # auch keinen Platz im Aehnlichkeits-Vergleich belegen.
            uebersprungen.append({"datei": str(m.get("datei", "")),
                                  "grund": kat_grund})
            continue
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


def uebernehmen(data_dir, anker_id, person, plan):
    """Die Mitglieder des Plans in den Bestand aufnehmen — ALLES ODER NICHTS je Aufruf: seit E3a-1d
    Katalogzeilen ueber `in_den_bestand` (erst alle pruefen, dann schreiben) statt Dateikopien; ein
    Mitglied ohne ref_id lehnt die Uebernahme laut ab (J7).
    -> Liste der aufgenommenen ref_ids (auch die, die schon gebunden waren). Wirft ValueError."""
    ids = ref_ids(plan["aufnehmen"])
    in_den_bestand(data_dir, ids, person, f"learning run anchor {anker_id}")
    return ids
