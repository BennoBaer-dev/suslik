"""core/personernte — PE1 Baustein 3: Ganzkoerper-Ernte fuer Person Learn
(stufe2.md; portierte Kette aus prototyp/ernte_lauf.py, User-Mandat 04.08.:
kompletter Durchbau + Selbst-Simulation).

Arbeitsteilung (Architektur-Entscheid, stand.md):
  HANDLER (verifyd) bindet EINMAL beim Lauf-Anlegen: Deckung + Frigate-API
    -> Durchgaenge -> strenge Solo-Bindung inkl. Ueberlapp-Anker fuer
    zonenlose Events -> events_liste mit (person, bindung, pass_key)
    in <data_dir>/state/personlauf.json.
  WORKER (je Event ein Job, typ person_ernte) extrahiert NUR: Clip ->
    Pfad-Snapshots-Kette -> Gates (Mindesthoehe, Pose-Wache streng) ->
    Nach-Zuschnitt auf Skelett-Box -> Metadaten-Zeile (Kamera, zones,
    Lichtphase, Blick, IR/Helligkeits-MESSWERTE, person_anteil) nach
    <data_dir>/personlern/<lauf_id>/ (manifest.jsonl geflusht, Resume
    ueber eids wie core/ernte.fertig-Muster).

Gates/Konventionen EXAKT wie der Prototyp (Messreihe 04.08.): Wache streng
= harte Grenze, IR/Ueberstrahlung/Dunkel nur Messwerte, FIFO-Fragen kommen
erst mit dem Betriebs-Bestand (PE3+)."""
import datetime
import json
import os


def lauf_dir(data_dir, lauf_id):
    return os.path.join(data_dir, "personlern", lauf_id)


def manifest_pfad(data_dir, lauf_id):
    return os.path.join(lauf_dir(data_dir, lauf_id), "manifest.jsonl")


def fertig_eids(data_dir, lauf_id):
    p = manifest_pfad(data_dir, lauf_id)
    if not os.path.exists(p):
        return set()
    return {json.loads(l)["eid"] for l in open(p) if l.strip()}


def zeile_schreiben(data_dir, lauf_id, zeile):
    os.makedirs(lauf_dir(data_dir, lauf_id), exist_ok=True)
    with open(manifest_pfad(data_dir, lauf_id), "a") as f:
        f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def ernte_event(data_dir, lauf_id, job, wache, extraktor, crops_je_event=2):
    """EIN Event verarbeiten (Worker-Kontext). job: eid, person, bindung,
    pass_key, kamera, start, zones, lichtphase, sonnenhoehe (Handler hat
    Lichtphase schon berechnet — Standort-Logik bleibt an einer Stelle).
    wache: PoseWache-Instanz; extraktor: callable(eid) -> (top|None, info)
    mit top = Liste (score, frame_i, crop_bgr, hoehe_px).
    Rueckgabe: dict fuer fertig-Zaehlung."""
    import cv2
    from prototyp.ernte_lauf import person_zuschnitt, blick_bestimmen, \
        crop_messen
    from prototyp import referenz_ernte as _re
    eid = job["eid"]
    try:
        top, info = extraktor(eid)
    except Exception as ex:
        top, info = None, f"Fehler: {str(ex)[:80]}"
    if not top:
        zeile_schreiben(data_dir, lauf_id, {
            "eid": eid, "person": job["person"], "ausfall": info})
        return {"eid": eid, "ok": False, "grund": info}
    ldir = lauf_dir(data_dir, lauf_id)
    os.makedirs(os.path.join(ldir, "crops"), exist_ok=True)
    genommen, siebe = 0, []
    gesehen = set()      # Dubletten-Wache (User-Fund 05.08.): zwei Spur-
    # Punkte koennen auf DENSELBEN Clip-Frame fallen — ohne Pruefung wurde
    # exakt dasselbe Bild als ~0 und ~1 doppelt gespeichert (11 byte-
    # identische Paare im Bestand gemessen) und zaehlte doppelt im Training.
    for j, (score, fi, crop, hh) in enumerate(top):
        if genommen >= crops_je_event:
            break
        kennung = (int(fi), crop.shape)
        if kennung in gesehen:
            siebe.append("dublette")
            continue
        if hh < _re.MIN_HOEHE_PX:
            siebe.append("zu_klein")
            continue
        komplett, det = wache.pruefen(crop)
        if not komplett:
            siebe.append("wache_" + det["gruende"][0].split(" ")[0])
            continue
        crop2, anteil, zbox = person_zuschnitt(crop, det["punkte"],
                                               det["scores"])
        blick, blick_mess = blick_bestimmen(det, crop.shape[0])
        gesehen.add(kennung)
        datei = f"{eid}~{j}.jpg".replace("/", "_")
        pfad = os.path.join(ldir, "crops", datei)
        cv2.imwrite(pfad, crop2, [cv2.IMWRITE_JPEG_QUALITY, 92])
        mess = crop_messen(pfad)
        start = float(job.get("start") or 0)
        zeile_schreiben(data_dir, lauf_id, {
            "eid": eid, "person": job["person"], "bindung": job["bindung"],
            "pass_key": job.get("pass_key"), "camera": job.get("kamera"),
            "start": start,
            "tag": datetime.date.fromtimestamp(start).isoformat(),
            "stunde": datetime.datetime.fromtimestamp(start).hour,
            "zones": job.get("zones"),
            "lichtphase": job.get("lichtphase"),
            "sonnenhoehe": job.get("sonnenhoehe"),
            **mess, "hoehe_px": int(hh),
            "wache": {"kopf": det["kopf"], "knoechel": det["knoechel"],
                      "fuesse": det["fuesse"]},
            "blick": blick, "blick_mess": blick_mess,
            "person_anteil": anteil, "zuschnitt": zbox,
            "datei": datei, "status": "offen"})
        genommen += 1
    if not genommen:
        zeile_schreiben(data_dir, lauf_id, {
            "eid": eid, "person": job["person"],
            "ausfall": "kein Crop durch Gates: " + ",".join(siebe[:6])})
    return {"eid": eid, "ok": genommen > 0, "bilder": genommen,
            "siebe": siebe}


def abnahme_anwenden(data_dir, lauf_id, falsch):
    """PE2-Abschluss (User 04.08.: "wo bestaetige ich, dass ich das
    abgearbeitet habe?"): Klick-Urteile werden in den Lauf-Bestand
    gestempelt — status abgenommen/verworfen je Bild, atomar.
    Rueckgabe (n_abgenommen, n_verworfen)."""
    mp = manifest_pfad(data_dir, lauf_id)
    zeilen = [json.loads(l) for l in open(mp) if l.strip()]
    n_ok = n_falsch = 0
    for z in zeilen:
        if "ausfall" in z:
            continue
        if z["datei"] in falsch:
            z["status"] = "verworfen"
            n_falsch += 1
        else:
            z["status"] = "abgenommen"
            n_ok += 1
    tmp = mp + ".tmp"
    with open(tmp, "w") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, mp)
    return n_ok, n_falsch


def laeufe_lesen(data_dir):
    """Alle Person-Learn-Laeufe (fuer die Bestands-Seite, PE2b):
    Liste (lauf_id, zeilen) — neueste zuerst."""
    wurzel = os.path.join(data_dir, "personlern")
    laeufe = []
    if os.path.isdir(wurzel):
        for lid in sorted(os.listdir(wurzel), reverse=True):
            mp = manifest_pfad(data_dir, lid)
            if os.path.isfile(mp):
                laeufe.append((lid, [json.loads(l) for l in open(mp)
                                     if l.strip()]))
    return laeufe


def _manifest_umschreiben(data_dir, lauf_id, zeilen):
    mp = manifest_pfad(data_dir, lauf_id)
    tmp = mp + ".tmp"
    with open(tmp, "w") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, mp)


def loeschen(data_dir, lauf_id, datei=None):
    """PE2b (User 04.08.: nachtraeglich loeschen, Einzelbild oder ganzer
    Lauf): Crop-Dateien WEG, Manifest-Zeilen bleiben als Beleg mit
    status=geloescht (Grabstein; ein NEUER Lauf erntet die Events wieder,
    weil Resume je Lauf gilt). Rueckgabe: Anzahl geloeschter Bilder."""
    mp = manifest_pfad(data_dir, lauf_id)
    if not os.path.isfile(mp):
        return 0
    zeilen = [json.loads(l) for l in open(mp) if l.strip()]
    n = 0
    for z in zeilen:
        if "ausfall" in z or z.get("status") == "geloescht":
            continue
        if datei is not None and z["datei"] != datei:
            continue
        pfad = os.path.join(lauf_dir(data_dir, lauf_id), "crops", z["datei"])
        try:
            os.remove(pfad)
        except FileNotFoundError:
            pass
        z["status"] = "geloescht"
        n += 1
    if n:
        _manifest_umschreiben(data_dir, lauf_id, zeilen)
    return n
