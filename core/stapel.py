"""Der Stapel: die Urteils-Regel des Analyse-Workers fuer die Namen eines Ereignisses (K3 aus L16).

HERKUNFT: Bauplan analysen/bauplan_k3_produkt.md, Stufe KP1 Punkt 1. Die Rechnung kommt unveraendert
aus dem Werkzeug des Labors L16 (backups/release3_bau/labor_k3_norm/werkzeug/): die Regel aus
`regel_stapel.entscheiden`, die Gueltigkeit und die Stimme aus `regel_neu._gueltig` und
`regel_neu._stimme` (regel_neu.py:24-45). Der Massstab fuer „richtig uebernommen" ist der Anker
samples/labor_archiv/versionen/k3_l16_anker_2026-10-03/ (Urteils-Datensaetze `regel_stapel`).

ZWECK: Der Worker rechnet hier aus seinen ungerundeten Kern-Zeilen (worker_kern.event_rechnen), welche
Namen ein Ereignis traegt. Der Dienst rechnet nicht nach, er uebernimmt die Namen als `confirmed` fuer
`verdict_v2` und `verdict` (verifyd.py); damit laeuft die Marge dort nicht (Konzept Abschnitt 2).
  - gueltig ist ein Gesicht mit Erkennungswert, ohne Fehldetektion, ueber der Kante, mit Guete ueber
    den Stimm-Latten (nicht messbar = ungueltig, core.guete.stimme_ok) und mit Kopfhaltung;
  - jedes gueltige Gesicht gibt eine Stimme fuer seinen besten Namen, wenn dessen Wert die
    Stimm-Grenze erreicht;
  - ein Name ist erkannt, sobald er im Ereignis so viele Stimmen hat wie verlangt, egal wann (kein
    Zeitfenster, keine Marge);
  - hoechstens so viele Namen wie die Personenzahl, gereiht nach Stimmen, dann nach Name.

EHRLICHE GRENZEN (wie im Labor, gezaehlt in `diagnose`):
  - Gleichstand des besten und zweitbesten Namens im selben Gesicht gibt keine Stimme
    (gleichstand_stimme).
  - Gleichstand an der Personenzahl-Grenze: Reihung nach Stimmen, dann Name (gleichstand_obergrenze).
  - Zwei Gesichter im selben Bild fuer denselben Namen geben zwei Stimmen (doppelt_im_frame).
  - Der Abstand zum Zweitbesten war im Labor aus (0). Er entfaellt hier, weil ohne ihn dieselbe
    Rechnung herauskommt: bei verschiedenen Werten fuehrt der beste Name immer mit Abstand > 0.
  - Die Personenzahl kommt seit Stufe KP3 (core.personenzahl); der Worker gibt sie dem Stapel im Urteil
    des Ereignisses (worker_dienst) und in der Tuer-Quelle (core.tuer) mit. Ist sie unbrauchbar oder
    fehlt sie, rechnet der Stapel ohne Obergrenze.
"""
from core import guete

# Die Stimm-Grenze des Stapels: ab diesem Erkennungswert stimmt ein gueltiges Gesicht fuer seinen besten
# Namen. Gemessen im Labor L16 (Anker: stimm_grenze 0,4 in allen 318 Urteils-Datensaetzen); ein eigener
# Werkswert, bewusst unabhaengig von `win_thresh` (Bauplan K3, Entscheid 6).
STIMM_GRENZE = 0.40


def gueltig(f, lat):
    """Ob ein Gesicht stimmen darf: Erkennung, keine Fehldetektion, Kante, Guete, Kopfhaltung.
    -> bool"""
    if f.get("sc") is None or f.get("fd") is not False:
        return False
    uk = lat["urteil_kante"]
    if uk > 0 and min(f["bw"], f["bh"]) < uk:
        return False
    if not guete.stimme_ok(lat["guete_e"], lat["guete_t"], f["e"], f["t"]):
        return False
    return lat["pose"] <= 0 or (f["p"] is not None and f["p"] >= lat["pose"])


def stimme(sc):
    """Der Name, fuer den ein gueltiges Gesicht stimmt, und ob sein bester Wert ein Gleichstand ist.
    -> (Name oder None, Gleichstand an der Stimm-Grenze als bool)"""
    werte = sorted(sc.items(), key=lambda x: x[1], reverse=True)
    if not werte:
        # Anlage ohne eine einzige Person: kein Name, keine Stimme. Im Labor kam der Fall nicht vor
        # (dort IndexError); an der Rechnung fuer jedes Gesicht mit Werten aendert das nichts.
        return None, False
    if len(werte) > 1 and werte[0][1] == werte[1][1]:
        return None, werte[0][1] >= STIMM_GRENZE
    name, w = werte[0]
    if w < STIMM_GRENZE:
        return None, False
    return name, False


def entscheiden(gesichter, lat, x, personenzahl=None):
    """Der Stapel auf die Gesichter eines Ereignisses, Stand nach dem letzten Bild mit einer Stimme.
    -> {"namen": [...], "je_name": {Name: {stimmen, erste_frame, erste_zeit_s}}, "stimmen": {Name: n},
        "diagnose": {...}}"""
    diag = {"gesichter": 0, "gueltig": 0, "stimmen": 0, "gleichstand_stimme": 0, "doppelt_im_frame": 0,
            "gleichstand_obergrenze": 0}
    zahl, erste, sieger = {}, {}, []
    reihe = sorted(gesichter, key=lambda f: f["i"])
    k = 0
    while k < len(reihe):
        i, im_frame = reihe[k]["i"], []
        while k < len(reihe) and reihe[k]["i"] == i:
            f = reihe[k]
            k += 1
            diag["gesichter"] += 1
            if not gueltig(f, lat):
                continue
            diag["gueltig"] += 1
            name, gleich = stimme(f["sc"])
            diag["gleichstand_stimme"] += int(gleich)
            if name is not None:
                im_frame.append((name, f["zeit_s"]))
        if not im_frame:
            continue
        diag["doppelt_im_frame"] += len(im_frame) - len({n for n, _z in im_frame})
        for n, _z in im_frame:
            zahl[n] = zahl.get(n, 0) + 1
            diag["stimmen"] += 1
        kand = sorted((n for n in zahl if zahl[n] >= x), key=lambda n: (-zahl[n], n))
        if isinstance(personenzahl, int) and personenzahl > 0 and len(kand) > personenzahl:
            diag["gleichstand_obergrenze"] += int(zahl[kand[personenzahl - 1]] == zahl[kand[personenzahl]])
            kand = kand[:personenzahl]
        sieger = kand
        for n in sieger:
            erste.setdefault(n, (i, round(im_frame[0][1], 4)))
    return {"namen": list(sieger),
            "je_name": {n: {"stimmen": zahl[n], "erste_frame": erste[n][0], "erste_zeit_s": erste[n][1]}
                        for n in sieger},
            "stimmen": dict(sorted(zahl.items(), key=lambda x: -x[1])), "diagnose": diag}
