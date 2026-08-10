"""core/visiongalerie — Galerie-Bau fuer Vision detect (konzept_vision.md v2 §6,
Zug V2).

Was hier passiert und warum genau so:

  * **Drei Ansichts-Reihen statt vier** (E5, an echten Store-Daten geprueft):
    Quelle ist das Feld `blick` des Personen-Manifests (vorn / seitlich /
    hinten / unklar). Ein yaw gibt es im Koerper-Pfad nicht, "kein Gesicht =
    Ruecken" ist im Erzeuger-Docstring selbst als gemessen falsch vermerkt, und
    links/rechts existiert gar nicht. Vier Reihen waeren ein eigener gemessener
    Vorlauf, kein Umdeuten eines Vorzeichens.
  * **Guete = Hoehe x Laplace-Schaerfe**, Sieb VOR der Ansicht. Die Schaerfe
    steht nicht im Manifest; sie wird EINMALIG fuer den Bestand nachgezogen und
    dort hineingeschrieben (`schaerfe_nachziehen`), damit der Wizard nur liest
    und kein zweiter Schaerfe-Rechenweg entsteht.
  * **Seit .161 ist die Guete nur noch die BASIS, nicht mehr die ganze
    Rangfolge** (Vorgabe 08.08.: der Wizard soll eine Galerie vorschlagen, die
    man nur noch abnimmt, statt Unbrauchbares auszusortieren). Darueber liegt ein
    inhaltlicher Kurator aus den Signalen, die der Lernlauf je Bild ohnehin
    misst — Gesichts-Punkte, Ueberstrahlung, Person-Anteil, Kopf-Wache — plus
    eine Vielfalts-Spreizung ueber Tage, Ereignisse und Kameras. ALLE Zahlen
    dazu stehen in EINER Tabelle (`KURATOR`), jede mit Herkunft; sie sind
    heuristische STARTWERTE und ausdruecklich eichpflichtig (§6.4).
  * **Mindestgroesse ist `crop_px[1] >= 350`** — die in die Zelle skalierte
    Hoehe, ausdruecklich nicht `hoehe_px` (das ist die Hoehe im Originalframe).
  * **Galerien sind KOPIEN, nie Verweise** (§6.6): der Loeschknopf auf der
    Personen-Seite entfernt Crop-Dateien wirklich (`os.remove`) — eine Galerie
    aus Verweisen bekaeme davon stumm Loecher (Fehlerklasse "stiller Verlust").
    Die Hashes der Quellen bleiben als BELEG: faellt eine Quelle weg oder
    aendert sie sich, wird die Galerie "needs re-approval" und Vision urteilt
    fuer diese Person nicht mehr, statt still weiterzulaufen.
  * **Ablehnungen haben eine EIGENE Ablage** (§6.5). Im Lernlauf heisst
    "falsch" *nicht diese Person / unbrauchbar* und loescht Trainingsmaterial;
    im Wizard heisst "passt nicht" *taugt nicht als Zelle*. Dieses Modul fasst
    den Lernlauf-`status` deshalb NIE an — es liest ihn nur.

Kontrakt wie core/registry.py und core/vision.py: kein Dienst-Import, kein
Dienst-Zustand, reine Funktionen mit data_dir als Parameter. LEITPLANKE §11:
hier wird NIE ein Video geoeffnet und nie ein Decode gestartet — gelesen werden
ausschliesslich schon gespeicherte Crop-Dateien.
"""
import hashlib
import json
import os
import time

# --- Regeln, die auch das Gate und der Beweis lesen (eine Quelle) -------------
MIN_HOEHE_PX = 350             # crop_px[1], die skalierte Hoehe (§6.4)
REIHEN = ("vorn", "seitlich", "hinten")
# Die Oberflaeche ist englisch, die Labels im Store sind deutsch. Die Uebersetzung
# steht HIER, damit sie nicht in zwei Renderern getrennt driftet (der erste Anlauf
# zeigte auf der englischen Seite "vorn 28 · seitlich 11 · hinten 25").
REIHEN_ANZEIGE = {"vorn": "front", "seitlich": "side", "hinten": "back",
                  "unklar": "unclear"}
# Auffuell-Folge fuer die drei realen Mangelfaelle (§6.4): Reihe leer, Reihe
# kuerzer als die Reihenbreite, Pool waehrend der Abnahme erschoepft. Die Folge
# ist FEST und wird immer ehrlich angezeigt ("filled from ...").
AUFFUELL_FOLGE = ("seitlich", "vorn", "hinten", "unklar")
GROESSEN = (6, 12)             # E11: nur diese zwei Stufen, 9/15/18/24 entfallen
LEINWAND = (1176, 1008)        # Leinwand der vermessenen Gitter
HINTERGRUND = 110              # Grauwert der Zwischenraeume (wie die Beispiele)
MANIFEST = "herkunft.json"
ABGELEHNT = "abgelehnt.json"
GITTER = "gitter.jpg"

# --- Kurator-Tabelle (.161) ---------------------------------------------------
# EINE Quelle fuer jede Zahl der Vorschlags-Note. Registry-Gedanke: wer eine
# Schwelle oder ein Gewicht braucht, holt es HIER — kein weiteres verstreutes
# Literal im Renderer, im Dienst oder im Beweis (qs_ebenen.md, verbindliche
# Regel aus dem QS-Ebenen-Konzept).
#
# EHRLICHKEIT ZUR HERKUNFT (Faktenregel des Projekts): die Werte sind HEURISTISCHE
# STARTWERTE. Gemessen ist an ihnen nichts. Sie sind gegen genau EINE
# hand-kuratierte Referenz gehalten worden (12 Zellen, EINE Person, 104
# Kandidaten, Nacht 08.08. — scratchpad/kurator_vergleich.py) und gegen die drei
# dort benannten Schlechtfaelle. Das ist ein Plausibilitaets-Abgleich, KEINE
# Eichung: eine Person, ein Bestand, kein Fremd-Satz, keine Leave-Identity-Out.
# Die Eichung steht aus (konzept_vision.md §6.4, Eintrag 08.08.).
# Ausnahme mit echtem Beleg: `kopf_min` ist NICHT geraten, sondern derselbe
# Wert, mit dem die Pose-Wache am 68er-Pruefset geeicht wurde
# (prototyp/pose_wache.py SCHWELLE_STD = 0.60, Regel B, 62/68).
KURATOR = {
    # -- Basis: Hoehe x Schaerfe, aber BEIDE saettigend -----------------------
    # Warum saettigend: die rohe Guete (Hoehe x Laplace-Varianz) belohnte
    # Bildrauschen. Kleine, ueberstrahlte Weitwinkel-Crops (~450-560 px)
    # erreichten Laplace-Werte um 11000 und schlugen damit dreimal so grosse,
    # ruhige Nah-Crops (~1500 px, Laplace ~2000) — genau die Bilder, die eine
    # Hand-Auswahl zuerst nimmt. Ab der Saettigungsmarke bringt mehr Schaerfe
    # nichts mehr, weil sie ab dort ueberwiegend Sensorrauschen ist.
    "hoehe_satt": 1200,        # px Crop-Hoehe, ab hier zaehlt Groesse voll
    "schaerfe_satt": 2500,     # Laplace-Varianz, ab hier zaehlt Schaerfe voll
    # -- Gesichts-Sichtbarkeit, REIHEN-abhaengig ------------------------------
    # Quelle ist `blick_mess.gesicht` = max(Score Nase, Auge links, Auge rechts)
    # aus RTMPose. WICHTIG und im Erzeuger so vermerkt: dieser Wert TRENNT
    # vorn/hinten NICHT (RTMPose schaetzt Kopfpunkte auch von hinten konfident,
    # 5er-Rauchtest 04.08.). Er wird deshalb NICHT als Klassifikator benutzt,
    # sondern nur als abgestufter Bonus INNERHALB einer Reihe: in der
    # Vorn-Reihe ist ein Bild mit deutlichen Augen-/Nasenpunkten mehr wert als
    # eines ohne, in der Hinten-Reihe ist er bedeutungslos.
    "gesicht_gewicht": {"vorn": 0.45, "seitlich": 0.20, "hinten": 0.0,
                        "unklar": 0.20},
    "gesicht_min": 0.60,       # darunter kein Bonus (= Wache-Schwelle)
    "gesicht_voll": 0.95,      # ab hier voller Bonus
    # -- Abzug Ueberstrahlung -------------------------------------------------
    # `ueberstrahlt_anteil` = Anteil der Crop-Mitte mit Luminanz >= 245
    # (prototyp/ernte_lauf.py UEBERSTRAHLT_LUM). Ausgebrannte Flaechen loeschen
    # genau die Merkmale, auf die das Vision-Modell schaut.
    "ueberstrahlt_frei": 0.05,   # bis hier ohne Abzug
    "ueberstrahlt_voll": 0.45,   # ab hier voller Abzug
    "ueberstrahlt_gewicht": 0.45,
    # -- Abzug Fremdzeug im Ausschnitt ---------------------------------------
    # `person_anteil` = Flaeche der Skelett-Box am Original-Crop. Niedrig heisst:
    # der Ausschnitt zeigt ueberwiegend Szene statt Person (Kinderwagen-Befund
    # 04.08.) — das Modell vergleicht dann Hintergrund.
    "person_leer": 0.15,       # darunter voller Abzug
    "person_voll": 0.45,       # ab hier kein Abzug
    "person_gewicht": 0.30,
    # -- Abzug unsichere Haltung ---------------------------------------------
    # `wache.kopf` = Kopf-Score der Pose-Wache (max aus Nase/Augen/Ohren/
    # Kopfmitte). Ein niedriger Wert heisst nicht "kein Kopf" (dann waere gar
    # kein Crop entstanden), sondern: die Pose sitzt nur knapp — verdeckter
    # Kopf, ungewoehnliche Armhaltung, starke Aufsicht. Genau solche Bilder
    # taugen als Referenz schlecht, weil sie eine untypische Haltung zeigen.
    # Im Referenz-Bestand ist der Zusammenhang sichtbar: das eine Bild, das die
    # Hand-Durchsicht als untypisch aussortierte, traegt mit 0.72 den
    # niedrigsten Kopf-Score von 104; die Hand-Auswahl liegt bei 0.81-0.99.
    "kopf_voll": 0.90,         # ab hier kein Abzug
    "kopf_gewicht": 0.25,
    # -- Harte Ausschluesse ---------------------------------------------------
    # Diese drei nehmen einen Kandidaten GANZ aus dem Vorschlag. Ehrlich dazu:
    # im Referenz-Bestand von 104 Kandidaten greift KEINER von ihnen — der
    # Lernlauf siebt vorher schon (die Pose-Wache verwirft Crops ohne Kopf, so
    # dass gar kein Crop entsteht). Sie sind der Schutz gegen Manifest-Zeilen
    # aus aelteren oder fremden Ernte-Wegen, nicht die Arbeitspferde des
    # Vorschlags; die Arbeit macht die abgestufte Note.
    "kopf_min": 0.60,          # wache.kopf; = pose_wache.SCHWELLE_STD (geeicht)
    "ueberstrahlt_hart": 0.55,  # mehr als die halbe Crop-Mitte auf Weiss
    "gesicht_hart_vorn": 0.60,  # Vorn-Reihe ohne verlaessliche Kopfpunkte
    # -- Vielfalts-Spreizung --------------------------------------------------
    # Eine Galerie aus sechs Bildern EINES Nachmittags zeigt eine Kleidung, ein
    # Licht, einen Winkel. Der gemessene Prompt sagt den Modellen ausdruecklich
    # "taken on different days (clothing varies)" — also muss der Vorschlag das
    # auch liefern. Beide Deckel gelten JE REIHE.
    "je_tag_max": 2,           # hoechstens 2 Zellen je Kalendertag und Reihe
    "je_eid_max": 1,           # hoechstens 1 Zelle je Ereignis und Reihe
    # Kamera ist KEIN Deckel, sondern nur ein Gleichstands-Entscheid: bei
    # gleicher Note gewinnt die in dieser Reihe noch nicht benutzte Kamera.
    "note_rundung": 6,         # Stellen, ab denen zwei Noten als gleich gelten
    # -- Optionaler Embedding-Hinweis ----------------------------------------
    # Vision ist eigenstaendig (Entscheid 08.08.) und darf NIE von Embeddings
    # abhaengen. Wer welche mitgibt, bekommt einen kleinen Abzug fuer Zellen,
    # die einer schon gewaehlten sehr aehnlich sind; ohne Embeddings ist das
    # Verhalten Zeichen fuer Zeichen dasselbe.
    "aehnlich_ab": 0.90,       # Kosinus, ab dem ein Bild als Wiederholung gilt
    "aehnlich_gewicht": 0.15,
}


def wurzel(data_dir):
    return os.path.join(str(data_dir or ""), "personlern", "galerien")


def ordner(data_dir, person):
    return os.path.join(wurzel(data_dir), str(person))


def _hash(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for stueck in iter(lambda: f.read(65536), b""):
            h.update(stueck)
    return h.hexdigest()


def _schreiben(pfad, daten):
    """Atomar + geflusht (Muster der uebrigen Stores) — ein halber Schreibvorgang
    darf keine Galerie zerreissen."""
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    tmp = pfad + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, pfad)


def _lesen(pfad, fallback=None):
    try:
        with open(pfad, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return fallback


# --------------------------------------------------------- Schaerfe nachziehen
def guete_datei(pfad):
    """Die Guete-Regel des Konzepts an EINER Bilddatei: (hoehe, schaerfe,
    guete = hoehe x schaerfe) aus genau EINEM imread.

    Gebraucht wird das ausserhalb des Manifests: die Kandidatenbilder des
    Urteilspfads (§7) liegen im Kontroll-Speicher und haben keine Manifest-Zeile.
    Die Rechnung ist trotzdem DIESELBE — Galerie und Kandidat werden nach
    derselben Regel gesiebt (§7: "dieselbe Guete-Regel wie bei der Galerie,
    keine dritte Regel"). Rueckgabe (None, None, None), wenn die Datei nicht
    lesbar ist."""
    import cv2
    im = cv2.imread(pfad)
    if im is None:
        return None, None, None
    schaerfe = float(cv2.Laplacian(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY),
                                   cv2.CV_64F).var())
    hoehe = int(im.shape[0])
    return hoehe, schaerfe, round(float(hoehe) * schaerfe, 1)


def schaerfe_rechnen(pfad):
    """Laplace-Varianz eines Crops — DIESELBE Rechnung wie im Analyse-Werkzeug
    (Graustufen, cv2.Laplacian, .var()). Ein zweiter Rechenweg waere genau die
    Streuklasse, die dieses Projekt schon mehrfach eingefangen hat; deshalb
    liegt die Formel nur in `guete_datei` und diese Funktion greift dorthin."""
    return guete_datei(pfad)[1]


def schaerfe_nachziehen(data_dir, laeufe_lesen, grenze=None):
    """Einmalig fuer den Bestand: fehlende `schaerfe` in die Manifest-Zeilen
    schreiben. Idempotent (vorhandene Werte bleiben), geflusht je Lauf, und es
    werden NUR Zeilen angefasst, deren Crop-Datei noch existiert.

    `laeufe_lesen` wird hereingereicht (core.personernte.laeufe_lesen) statt
    importiert: dieses Modul bleibt damit ohne Abhaengigkeit auf den Ernte-Pfad
    und im Beweis mit einer Attrappe pruefbar.
    Rueckgabe: dict(gerechnet, uebersprungen, laeufe)."""
    n_neu = n_alt = n_lauf = 0
    for lauf_id, zeilen in laeufe_lesen(data_dir):
        geaendert = False
        for z in zeilen:
            if "ausfall" in z or z.get("status") != "abgenommen":
                continue
            if z.get("schaerfe") is not None:
                n_alt += 1
                continue
            pfad = os.path.join(data_dir, "personlern", lauf_id, "crops",
                                z.get("datei", ""))
            if not os.path.isfile(pfad):
                continue
            wert = schaerfe_rechnen(pfad)
            if wert is None:
                continue
            z["schaerfe"] = round(wert, 2)
            geaendert = True
            n_neu += 1
            if grenze and n_neu >= grenze:
                break
        if geaendert:
            _manifest_schreiben(data_dir, lauf_id, zeilen)
            n_lauf += 1
        if grenze and n_neu >= grenze:
            break
    return {"gerechnet": n_neu, "uebersprungen": n_alt, "laeufe": n_lauf}


def _manifest_schreiben(data_dir, lauf_id, zeilen):
    mp = os.path.join(data_dir, "personlern", lauf_id, "manifest.jsonl")
    tmp = mp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for z in zeilen:
            f.write(json.dumps(z, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, mp)


# ------------------------------------------------------------------ Kandidaten
def kandidaten(data_dir, laeufe_lesen, person):
    """Alle galerie-tauglichen Crops einer Person, bester zuerst.

    Sieb (in dieser Reihenfolge, §6.4): abgenommen · Datei existiert ·
    crop_px[1] >= 350 · Schaerfe bekannt. Danach Guete = Hoehe x Schaerfe.
    Die Sortierung ist DETERMINISTISCH: bei gleicher Guete entscheidet der
    Dateiname, damit derselbe Bestand immer dieselbe Galerie vorschlaegt."""
    aus = []
    for lauf_id, zeilen in laeufe_lesen(data_dir):
        for z in zeilen:
            if "ausfall" in z or z.get("status") != "abgenommen":
                continue
            if z.get("person") != person:
                continue
            hoehe = (z.get("crop_px") or [0, 0])[1]
            if not hoehe or hoehe < MIN_HOEHE_PX:
                continue
            schaerfe = z.get("schaerfe")
            if schaerfe is None:
                continue
            pfad = os.path.join(data_dir, "personlern", lauf_id, "crops",
                                z.get("datei", ""))
            if not os.path.isfile(pfad):
                continue
            aus.append({
                "lauf_id": lauf_id, "datei": z["datei"], "pfad": pfad,
                "blick": z.get("blick") or "unklar",
                "hoehe": int(hoehe), "breite": int((z.get("crop_px") or [0])[0]),
                "schaerfe": float(schaerfe),
                "guete": round(float(hoehe) * float(schaerfe), 1),
                "tag": z.get("tag"), "camera": z.get("camera"),
                "start": z.get("start"),
                # Die Kurator-Signale (.161). Sie werden HIER mitgenommen, weil
                # der Vorschlag rein sein soll: `vorschlag` liest keine Datei
                # und kein Manifest mehr nach.
                "eid": z.get("eid"),
                "gesicht": (z.get("blick_mess") or {}).get("gesicht"),
                "ueberstrahlt": z.get("ueberstrahlt_anteil"),
                "person_anteil": z.get("person_anteil"),
                "kopf": (z.get("wache") or {}).get("kopf"),
            })
    aus.sort(key=lambda e: (-e["guete"], e["datei"]))
    return aus


def schluessel(e):
    """Die Identitaet eines Kandidaten ueber Laeufe hinweg (Dateinamen sind je
    Lauf eindeutig, aber derselbe Name kann in zwei Laeufen liegen)."""
    return f"{e['lauf_id']}/{e['datei']}"


# ------------------------------------------------------------------- Kurator
def _spanne(wert, unten, oben):
    """Ein Messwert auf 0..1, linear zwischen zwei Marken, ausserhalb geklemmt.
    `None` gibt None zurueck — ein FEHLENDER Messwert ist kein schlechter, und
    er darf weder Bonus noch Abzug erfinden."""
    if wert is None:
        return None
    try:
        w = float(wert)
    except (TypeError, ValueError):
        return None
    if oben == unten:
        return 1.0 if w >= oben else 0.0
    return max(0.0, min(1.0, (w - unten) / float(oben - unten)))


def ausschluss(e, reihe=None):
    """Harte Ausschluesse: Gruende, aus denen ein Kandidat ueberhaupt nicht in
    den Vorschlag darf. Rueckgabe: englischer Klartext oder "" (brauchbar).

    Ein FEHLENDER Messwert schliesst NIE aus — sonst wuerde jede Manifest-Zeile
    aus einem aelteren Ernte-Weg stumm verschwinden (Fehlerklasse "stiller
    Verlust"). Ausgeschlossen wird nur, was gemessen schlecht ist."""
    kopf = e.get("kopf")
    if kopf is not None and float(kopf) < KURATOR["kopf_min"]:
        return "no reliable head in the picture"
    ueb = e.get("ueberstrahlt")
    if ueb is not None and float(ueb) >= KURATOR["ueberstrahlt_hart"]:
        return f"burnt out by light ({round(float(ueb) * 100)}% of the crop)"
    if reihe == "vorn":
        ges = e.get("gesicht")
        if ges is not None and float(ges) < KURATOR["gesicht_hart_vorn"]:
            return "labelled front, but no reliable eyes/nose points"
    return ""


def note(e, reihe=None):
    """Die REIHEN-abhaengige Gesamtnote eines Kandidaten (§6.4, .161).

        Note = (Hoehe x Schaerfe, beide saettigend)
               + Gesichts-Bonus je nach Reihe
               - Abzug Ueberstrahlung
               - Abzug Fremdzeug im Ausschnitt

    Reine Rechnung auf den Feldern, die `kandidaten` mitgebracht hat: kein
    Datei-Zugriff, kein Zustand, gleiche Eingabe -> gleiche Zahl. Alle Zahlen
    kommen aus KURATOR.

    Rueckgabe: dict(note, basis, gesicht, ueberstrahlt, fremd) — die Teile
    stehen einzeln da, damit die Begruendung sie nicht nachrechnen muss und der
    Beweis sie einzeln pruefen kann."""
    h = _spanne(e.get("hoehe"), 0, KURATOR["hoehe_satt"]) or 0.0
    s = _spanne(e.get("schaerfe"), 0, KURATOR["schaerfe_satt"]) or 0.0
    basis = h * s
    g_gew = KURATOR["gesicht_gewicht"].get(reihe if reihe in KURATOR["gesicht_gewicht"]
                                           else "unklar", 0.0)
    g_norm = _spanne(e.get("gesicht"), KURATOR["gesicht_min"],
                     KURATOR["gesicht_voll"])
    bonus = g_gew * (g_norm if g_norm is not None else 0.0)
    u_norm = _spanne(e.get("ueberstrahlt"), KURATOR["ueberstrahlt_frei"],
                     KURATOR["ueberstrahlt_voll"])
    ueber = KURATOR["ueberstrahlt_gewicht"] * (u_norm if u_norm is not None else 0.0)
    p_norm = _spanne(e.get("person_anteil"), KURATOR["person_leer"],
                     KURATOR["person_voll"])
    fremd = KURATOR["person_gewicht"] * (1.0 - p_norm if p_norm is not None else 0.0)
    k_norm = _spanne(e.get("kopf"), KURATOR["kopf_min"], KURATOR["kopf_voll"])
    haltung = KURATOR["kopf_gewicht"] * (1.0 - k_norm if k_norm is not None else 0.0)
    return {"note": round(basis + bonus - ueber - fremd - haltung,
                          KURATOR["note_rundung"]),
            "basis": round(basis, 4), "gesicht": round(bonus, 4),
            "ueberstrahlt": round(-ueber, 4), "fremd": round(-fremd, 4),
            "haltung": round(-haltung, 4)}


def begruendung(e, reihe=None):
    """Die eine Zeile, die im Wizard unter der Zelle steht (englisch).

    Sie ist AUS DEN ECHTEN MESSWERTEN gebaut, nie erfunden: jedes Stueck nennt
    das Feld, aus dem es kommt. Wo ein Wert fehlt, steht nichts — kein
    geschoenter Satz. Der Wortlaut nennt die Gesichts-Punkte beim Namen
    ("eyes/nose"), weil der Wert genau das ist (max Score aus Nase und Augen)
    und nicht "Gesicht erkannt"."""
    teile = []
    if e.get("hoehe"):
        teile.append(f"{int(e['hoehe'])} px tall")
    ges = e.get("gesicht")
    g_gew = KURATOR["gesicht_gewicht"].get(reihe if reihe in KURATOR["gesicht_gewicht"]
                                           else "unklar", 0.0)
    if ges is not None and g_gew > 0:
        n = _spanne(ges, KURATOR["gesicht_min"], KURATOR["gesicht_voll"])
        wort = ("eyes/nose clear" if n >= 0.75 else
                "eyes/nose partly visible" if n >= 0.35 else "eyes/nose weak")
        teile.append(f"{wort} ({round(float(ges), 2)})")
    ueb = e.get("ueberstrahlt")
    if ueb is not None:
        if float(ueb) <= KURATOR["ueberstrahlt_frei"]:
            teile.append("evenly lit")
        else:
            teile.append(f"{round(float(ueb) * 100)}% blown out by light")
    pa = e.get("person_anteil")
    if pa is not None:
        if float(pa) >= KURATOR["person_voll"]:
            teile.append(f"person fills {round(float(pa) * 100)}% of the crop")
        else:
            teile.append(f"only {round(float(pa) * 100)}% of the crop is the "
                         "person")
    kopf = e.get("kopf")
    if kopf is not None and float(kopf) < KURATOR["kopf_voll"]:
        teile.append(f"unusual or partly hidden pose ({round(float(kopf), 2)})")
    ort = " ".join(str(t) for t in (e.get("tag"), e.get("camera")) if t)
    if ort:
        teile.append(ort)
    return " · ".join(teile)


def _kosinus(a, b):
    """Kosinus zweier Vektoren, ohne numpy (dieses Modul bleibt import-arm).
    None/leer -> None, damit der Aufrufer 'kein Hinweis' von '0 Aehnlichkeit'
    unterscheiden kann."""
    if not a or not b or len(a) != len(b):
        return None
    p = na = nb = 0.0
    for x, y in zip(a, b):
        p += float(x) * float(y)
        na += float(x) * float(x)
        nb += float(y) * float(y)
    if na <= 0 or nb <= 0:
        return None
    return p / ((na ** 0.5) * (nb ** 0.5))


def deckung(data_dir, laeufe_lesen, personen):
    """Je Person: was ist da, und was laesst sich daraus WIRKLICH bauen (§3.2).
    `personen` ist die massgebliche Menge (personlern/modell/status.json ->
    personen) — nicht der Gesichts-Bestand, der einen anderen Nenner hat.

    `max_groesse` ist ehrlich: eine Groesse gilt als baubar, wenn sich die
    Zellen ueberhaupt fuellen lassen (notfalls aus anderen Reihen), NICHT erst
    wenn jede Reihe voll ist — sonst waere fuer die meisten Bestaende gar nichts
    baubar. Wie viele Zellen aus der eigenen Ansicht kommen, steht daneben."""
    aus = []
    for name in personen:
        k = kandidaten(data_dir, laeufe_lesen, name)
        je_reihe = {r: [e for e in k if e["blick"] == r] for r in REIHEN}
        je_reihe["unklar"] = [e for e in k if e["blick"] not in REIHEN]
        moeglich = [g for g in GROESSEN if len(k) >= g]
        eintrag = {
            "person": name, "gesamt": len(k),
            "je_reihe": {r: len(v) for r, v in je_reihe.items()},
            "groessen": moeglich,
            "max_groesse": max(moeglich) if moeglich else 0,
            "empfehlung": max(moeglich) if moeglich else 0,
        }
        # Reihen, die ihre Breite bei der empfohlenen Groesse nicht fuellen —
        # der Nutzer soll das VOR der Abnahme-Schleife sehen, nicht darin.
        if eintrag["empfehlung"]:
            breite = eintrag["empfehlung"] // len(REIHEN)
            eintrag["duenn"] = [r for r in REIHEN if len(je_reihe[r]) < breite]
        else:
            eintrag["duenn"] = list(REIHEN)
        aus.append(eintrag)
    return aus


# -------------------------------------------------------------- Reihen-Vorschlag
KLASSISCH = "klassisch"        # eingefrorene Rangfolge vor .161 (nur Beweis)
KURATIERT = "kurator"          # das Produkt faehrt IMMER diese


def _lage_neu():
    """Der Vielfalts-Stand EINER Reihe: was ist in dieser Reihe schon
    vergeben."""
    return {"tage": {}, "eids": {}, "kameras": set(), "vektoren": []}


def _lage_zubuchen(lage, e, embeddings=None):
    lage["tage"][e.get("tag")] = lage["tage"].get(e.get("tag"), 0) + 1
    lage["eids"][e.get("eid")] = lage["eids"].get(e.get("eid"), 0) + 1
    if e.get("camera"):
        lage["kameras"].add(e["camera"])
    if embeddings:
        v = embeddings.get(schluessel(e))
        if v:
            lage["vektoren"].append(v)


def _deckel_frei(lage, e):
    """Halten die beiden Vielfalts-Deckel dieser Reihe fuer diesen Kandidaten?
    Ein FEHLENDES Feld (kein Tag, keine eid) deckelt nie — sonst wuerden alte
    Manifest-Zeilen ohne diese Felder alle in denselben Topf fallen."""
    if e.get("tag") is not None and \
            lage["tage"].get(e.get("tag"), 0) >= KURATOR["je_tag_max"]:
        return False
    if e.get("eid") is not None and \
            lage["eids"].get(e.get("eid"), 0) >= KURATOR["je_eid_max"]:
        return False
    return True


def vorschlag(kand, groesse, abgelehnt=(), gesetzt=None, regel=KURATIERT,
              embeddings=None):
    """Der automatische Vorschlag: ZEILE JE ANSICHT, kuratiert (.161).

    Reihe 1 vorn, Reihe 2 seitlich, Reihe 3 hinten; je Reihe `groesse // 3`
    Zellen. Die Rangfolge INNERHALB einer Reihe ist die Kurator-Note (`note`,
    reihen-abhaengig), nicht mehr die rohe Guete; harte Ausschluesse
    (`ausschluss`) kommen gar nicht erst in Frage, und die Vielfalts-Deckel aus
    KURATOR sorgen dafuer, dass eine Reihe nicht dreimal denselben Nachmittag
    zeigt. Reicht eine Ansicht nicht, wird aus der FESTEN Folge
    (seitlich -> vorn -> hinten -> unklar) aufgefuellt und die Zelle traegt
    `geliehen_aus` — die Anzeige sagt es im Klartext, statt stillschweigend
    etwas Fremdes einzusetzen.

    Die Deckel duerfen NIE ein Loch erzeugen: greift ein Deckel, wird zuerst
    innerhalb der eigenen Ansicht gelockert und erst danach geliehen (die
    sichtbare Ausleihe ist der ehrlichere Kompromiss als eine leere Zelle).

    Rein: kein Datei- und kein Store-Zugriff. Gleiche Eingabe -> gleiche
    Ausgabe.

    abgelehnt   Menge von schluessel(); kommt nicht wieder (Gedaechtnis, §6.5)
    gesetzt     optional {(reihe, spalte): schluessel} — schon bestaetigte
                Zellen, die stehen bleiben (Nachruecken fasst sie nicht an)
    regel       KURATIERT (Produkt) oder KLASSISCH. KLASSISCH ist die
                EINGEFRORENE Rangfolge vor .161 (reine Guete, keine Deckel,
                keine Ausschluesse) und existiert nur, damit der Beweis die von
                abgenommenen Beispiel-Galerien weiter nachbauen kann —
                sie wurden nach dieser Regel gebaut. Kein Produktpfad ruft sie.
    embeddings  optional {schluessel: vektor} — nur ein SPREIZ-HINWEIS. Fehlt
                er (Normalfall), ist die Auswahl Zeichen fuer Zeichen dieselbe;
                Vision haengt nie an Embeddings.
    """
    breite = max(1, int(groesse) // len(REIHEN))
    abgelehnt = set(abgelehnt or ())
    gesetzt = dict(gesetzt or {})
    nach_schluessel = {schluessel(e): e for e in kand}
    frei = [e for e in kand if schluessel(e) not in abgelehnt]
    vergeben = set()
    for s in gesetzt.values():
        vergeben.add(s)
    zeilen = []
    for r_i, reihe in enumerate(REIHEN):
        zellen, luecken = [], 0
        lage = _lage_neu()
        # Schon bestaetigte Zellen dieser Reihe zaehlen fuer die Deckel mit —
        # sonst wuerde ein Nachruecker den Tag doppeln, den der Nutzer eben
        # bestaetigt hat.
        for sp in range(breite):
            fest = gesetzt.get((reihe, sp)) or gesetzt.get(f"{reihe}:{sp}")
            if fest and fest in nach_schluessel:
                _lage_zubuchen(lage, nach_schluessel[fest], embeddings)
        for spalte in range(breite):
            fest = gesetzt.get((reihe, spalte)) or gesetzt.get(f"{reihe}:{spalte}")
            if fest and fest in nach_schluessel:
                zellen.append(_zelle_bauen(nach_schluessel[fest], reihe, spalte))
                continue
            e = _bester(frei, reihe, vergeben, lage, regel, embeddings)
            if e is None:
                zellen.append(None)
                luecken += 1
                continue
            vergeben.add(schluessel(e))
            _lage_zubuchen(lage, e, embeddings)
            zellen.append(_zelle_bauen(e, reihe, spalte))
        zeilen.append({"reihe": reihe, "nr": r_i, "zellen": zellen,
                       "luecken": luecken,
                       "eigene": sum(1 for z in zellen if z and not z["geliehen_aus"]),
                       "geliehen": sum(1 for z in zellen if z and z["geliehen_aus"]),
                       "tage": sorted({z["tag"] for z in zellen
                                       if z and z.get("tag")}),
                       "kameras": sorted({z["camera"] for z in zellen
                                          if z and z.get("camera")})})
    return {"groesse": int(groesse), "breite": breite, "zeilen": zeilen,
            "vollstaendig": all(z["luecken"] == 0 for z in zeilen),
            "bestand": len(kand), "abgelehnt": len(abgelehnt),
            "regel": regel}


def _zelle_bauen(e, reihe, spalte=None):
    """Eine Zelle mit allem, was die Anzeige braucht: Note, Begruendungszeile
    und die Herkunfts-Ansicht. Die Begruendung entsteht GENAU HIER — der
    Renderer und der Browser bauen keinen eigenen Text (sonst driften zwei
    Fassungen desselben Satzes, die Klasse hat dieses Projekt schon getroffen)."""
    n = note(e, reihe)
    z = dict(e, reihe=reihe, note=n["note"], note_teile=n,
             begruendung=begruendung(e, reihe),
             geliehen_aus=None if e["blick"] == reihe else e["blick"])
    if spalte is not None:
        z["spalte"] = spalte
    return z


def _bester(frei, reihe, vergeben, lage=None, regel=KURATIERT, embeddings=None):
    """Bester noch freier Kandidat FUER DIESE REIHE.

    Vier Stufen, in dieser Folge: eigene Ansicht mit Deckeln · eigene Ansicht
    ohne Deckel · Auffuell-Folge mit Deckeln · Auffuell-Folge ohne Deckel. Die
    erste Stufe, die etwas liefert, gewinnt.

    Innerhalb einer Stufe entscheidet die Note (KURATIERT) bzw. die Guete
    (KLASSISCH). Bei GLEICHSTAND gewinnt eine in dieser Reihe noch nicht
    benutzte Kamera, danach der Dateiname — die Auswahl bleibt damit
    deterministisch."""
    lage = lage if lage is not None else _lage_neu()
    kuriert = (regel != KLASSISCH)
    quellen = (reihe,) + tuple(r for r in AUFFUELL_FOLGE if r != reihe)
    if kuriert:
        stufen = ([(reihe, True), (reihe, False)]
                  + [(q, True) for q in quellen[1:]]
                  + [(q, False) for q in quellen[1:]])
    else:
        # KLASSISCH kennt keine Deckel — also auch keine zweite, gelockerte
        # Runde. Die Folge ist exakt die von vor .161.
        stufen = [(q, True) for q in quellen]
    for quelle, streng in stufen:
        beste = None
        for e in frei:
            if schluessel(e) in vergeben:
                continue
            blick = e["blick"] if e["blick"] in REIHEN else "unklar"
            if blick != quelle:
                continue
            if kuriert:
                if ausschluss(e, reihe):
                    continue
                if streng and not _deckel_frei(lage, e):
                    continue
                wert = note(e, reihe)["note"]
                if embeddings:
                    wert -= KURATOR["aehnlich_gewicht"] * _wiederholung(
                        e, lage, embeddings)
                wert = round(wert, KURATOR["note_rundung"])
                # Kleiner ist besser: Note absteigend, dann neue Kamera vor
                # schon benutzter, dann Dateiname/Lauf (deterministischer
                # Schluss-Entscheid).
                rang = (-wert, 0 if e.get("camera") not in lage["kameras"] else 1,
                        e["datei"], e["lauf_id"])
            else:
                rang = (-e["guete"], e["datei"], e["lauf_id"])
            if beste is None or rang < beste[0]:
                beste = (rang, e)
        if beste is not None:
            return beste[1]
    return None


def _wiederholung(e, lage, embeddings):
    """0..1: wie sehr wiederholt dieser Kandidat eine schon gewaehlte Zelle
    derselben Reihe? Nur ein HINWEIS (optionale Embeddings, §Vision-
    Unabhaengigkeit). Ohne Vektor fuer diesen Kandidaten: 0 — kein Hinweis ist
    kein Verdacht."""
    v = (embeddings or {}).get(schluessel(e))
    if not v or not lage["vektoren"]:
        return 0.0
    beste = 0.0
    for w in lage["vektoren"]:
        c = _kosinus(v, w)
        if c is None:
            continue
        beste = max(beste, c)
    n = _spanne(beste, KURATOR["aehnlich_ab"], 1.0)
    return n if n is not None else 0.0


def nachruecken(kand, reihe, abgelehnt=(), belegt=(), gewaehlt=(),
                regel=KURATIERT, embeddings=None):
    """Der naechstbeste Kandidat DERSELBEN Ansicht, wenn eine Zelle abgelehnt
    wird. Ist die eigene Ansicht erschoepft, greift dieselbe Auffuell-Folge wie
    im Vorschlag — der dritte der drei realen Mangelfaelle (§6.4).

    `gewaehlt` sind die Kandidaten, die in DIESER Reihe stehen bleiben; sie
    fuellen die Vielfalts-Deckel, damit der Nachruecker nicht den Tag doppelt,
    den der Nutzer gerade behalten hat. Rueckgabe: Kandidat oder None."""
    abgelehnt = set(abgelehnt or ())
    frei = [e for e in kand if schluessel(e) not in abgelehnt]
    lage = _lage_neu()
    for e in gewaehlt or ():
        _lage_zubuchen(lage, e, embeddings)
    e = _bester(frei, reihe, set(belegt or ()), lage, regel, embeddings)
    if e is None:
        return None
    return _zelle_bauen(e, reihe)


# ------------------------------------------------------------------ Gitter-Bild
def gitter_bauen(zellen_pfade, groesse, leinwand=None):
    """Das gerenderte Gitter (BGR-Array). Layout exakt wie die abgenommenen
    Beispiel-Galerien: drei Reihen (eine je Ansicht), `ceil(groesse/3)` Spalten,
    Zellen im Crop-Seitenverhaeltnis gefuellt durch HOCHSKALIEREN — nie durch
    Beschneiden des Koerpers (§6.4). Der Rest bleibt grau, das kostet keine
    Aussage und keine nennenswerten Token.

    AUFGERUNDET, nicht abgeschnitten (09.08.): bei einer Zellenzahl, die nicht
    durch drei teilbar ist, gab `groesse//3` ZU WENIGE Plaetze — 7 Bilder auf
    2x3 = 6 Zellen, und `divmod(6, 2)` legte das siebte auf Reihe 3 (= ausserhalb
    der Leinwand). Das Ergebnis war kein stiller Verlust, sondern ein Abbruch:
    numpy weigert sich, in einen leeren Slice zu schreiben (ValueError). Fuer die
    Galerie-Groessen 6 und 12 ist ceil == floor, das Layout der abgenommenen
    Galerien aendert sich also NICHT — die Rundung greift nur bei den Zahlen, die
    vorher gar nicht durchliefen. Ueberzaehlige Plaetze bleiben grau wie jede
    andere Luecke.

    zellen_pfade: Liste in Lesereihenfolge (Reihe 1 links->rechts, dann Reihe 2
    ...), None fuer eine leere Zelle."""
    import cv2
    import numpy as np
    lw, lh = leinwand or LEINWAND
    spalten = max(1, -(-int(groesse) // len(REIHEN)))
    zb, zh = lw // spalten, lh // len(REIHEN)
    bild = np.full((zh * len(REIHEN), zb * spalten, 3), HINTERGRUND,
                   dtype=np.uint8)
    for i, pfad in enumerate(zellen_pfade):
        if not pfad:
            continue
        im = cv2.imread(pfad)
        if im is None:
            continue
        r, c = divmod(i, spalten)
        h, w = im.shape[:2]
        f = min(zb / w, zh / h)
        nw, nh = max(1, int(round(w * f))), max(1, int(round(h * f)))
        klein = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_AREA)
        x0 = c * zb + (zb - nw) // 2
        y0 = r * zh + (zh - nh) // 2
        bild[y0:y0 + nh, x0:x0 + nw] = klein
    return bild


# ------------------------------------------------------------------ Abnahme
def wizard_lage(data_dir, laeufe_lesen, personen, person="", groesse=None,
                neu=False):
    """Alles, was die Wizard-Seite braucht, in EINEM Griff — damit der Dienst
    duenn bleibt (I1) und der Beweis ohne laufenden Server pruefen kann.

    Rueckgabe: dict(deckung, galerien, person, groesse, vorschlag, groessen,
    empfehlung, abgelehnt_n, fertig, pruefung, auffrischung)."""
    deck = deckung(data_dir, laeufe_lesen, personen)
    galerien = {}
    for n, m in alle(data_dir).items():
        galerien[n] = dict(m, pruefung=pruefen(data_dir, n))
    lage = {"deckung": deck, "galerien": galerien, "person": person,
            "groesse": None, "vorschlag": None, "groessen": GROESSEN,
            "empfehlung": 0, "abgelehnt_n": 0, "fertig": None,
            "pruefung": {}, "auffrischung": "",
            "reihen_text": dict(REIHEN_ANZEIGE)}
    if not person:
        return lage
    eintrag = next((d for d in deck if d["person"] == person), None)
    if not eintrag:
        return lage
    lage["empfehlung"] = eintrag["empfehlung"]
    lage["groessen"] = tuple(eintrag["groessen"]) or GROESSEN
    k = kandidaten(data_dir, laeufe_lesen, person)
    fertig = galerien.get(person)
    if fertig and not neu:
        lage["fertig"] = fertig
        lage["pruefung"] = fertig.get("pruefung") or {}
        # Auffrischungs-ANGEBOT, kein Automatismus: nur ein Hinweis, wenn seit
        # der Abnahme neues abgenommenes Material dazugekommen ist.
        alt = fertig.get("bestand")
        if alt is not None and len(k) > alt:
            lage["auffrischung"] = (
                f"{len(k) - alt} more approved body images have appeared since "
                "you approved this gallery. Rebuilding may give it better "
                "pictures.")
        return lage
    lage["groesse"] = int(groesse) if groesse in GROESSEN else eintrag["empfehlung"]
    abgelehnt = abgelehnt_lesen(data_dir, person)
    lage["abgelehnt_n"] = len(abgelehnt)
    if lage["groesse"]:
        lage["vorschlag"] = vorschlag(k, lage["groesse"], abgelehnt)
        lage["vorschlag"]["bestand"] = len(k)
    return lage


def abnehmen(data_dir, person, zellen, groesse, leinwand=None, bestand=None):
    """Die abgenommene Galerie als KOPIE ablegen (§6.6).

    Geschrieben wird nach <data_dir>/personlern/galerien/<person>/:
      * je Zelle eine Bild-KOPIE `z<nr>_<reihe>.jpg`
      * das gerenderte Gitter `gitter.jpg`
      * `herkunft.json` mit Quell-Lauf, Quell-Datei, sha256 der QUELLE, sha256
        der KOPIE, Reihe/Spalte, Guete, Ansicht, Abnahme-Zeit und Groesse.

    Warum unter `personlern/`: dieser Pfad faehrt im Voll-Backup UND im Restore
    automatisch mit; ein eigener Ordner `vision/` waere beim Restore als
    unbekanntes Mitglied abgelehnt worden.

    `zellen` ist die Lesereihenfolge (Reihe 1 links->rechts, ...); None-Zellen
    sind erlaubt und werden als Luecke protokolliert. Rueckgabe: das Manifest."""
    import cv2
    ziel = ordner(data_dir, person)
    os.makedirs(ziel, exist_ok=True)
    # Alte Kopien derselben Galerie weg, damit keine Reste einer groesseren
    # Vorgaengerin liegen bleiben (die Herkunft ist die Wahrheit, nicht das
    # Verzeichnis-Listing).
    for n in os.listdir(ziel):
        if n.startswith("z") and n.endswith(".jpg"):
            os.remove(os.path.join(ziel, n))
    eintraege, pfade = [], []
    spalten = max(1, int(groesse) // len(REIHEN))
    for i, z in enumerate(zellen):
        if not z:
            pfade.append(None)
            eintraege.append({"nr": i, "reihe": REIHEN[i // spalten],
                              "spalte": i % spalten, "leer": True})
            continue
        quelle = z.get("pfad") or os.path.join(
            data_dir, "personlern", z["lauf_id"], "crops", z["datei"])
        reihe = REIHEN[i // spalten]
        name = f"z{i:02d}_{reihe}.jpg"
        kopie = os.path.join(ziel, name)
        with open(quelle, "rb") as q, open(kopie, "wb") as k:
            k.write(q.read())
        pfade.append(kopie)
        # "geliehen" wird HIER aus Position und Ansicht abgeleitet, nicht vom
        # Aufrufer uebernommen: sonst haette die Wahrheit zwei Quellen, und die
        # zweite koennte still schweigen.
        eintraege.append({
            "nr": i, "reihe": reihe, "spalte": i % spalten,
            "leer": False, "datei": name,
            "quelle_lauf": z["lauf_id"], "quelle_datei": z["datei"],
            "quelle_hash": _hash(quelle), "kopie_hash": _hash(kopie),
            "blick": z.get("blick"),
            "geliehen_aus": (z.get("blick") if z.get("blick") != reihe else None),
            "guete": z.get("guete"), "hoehe": z.get("hoehe"),
            "schaerfe": z.get("schaerfe"), "tag": z.get("tag"),
            "camera": z.get("camera"),
            # Kurator-Spur (.161): WARUM diese Zelle vorgeschlagen wurde. Sie
            # wandert ins Herkunfts-Manifest, damit eine spaetere Eichung an
            # abgenommenen Galerien nachrechnen kann, ohne den Bestand zu
            # rekonstruieren.
            "note": z.get("note") if z.get("note") is not None
            else note(z, reihe)["note"],
            "begruendung": z.get("begruendung") or begruendung(z, reihe),
        })
    bild = gitter_bauen(pfade, groesse, leinwand)
    cv2.imwrite(os.path.join(ziel, GITTER), bild,
                [cv2.IMWRITE_JPEG_QUALITY, 92])
    manifest = {
        "person": person, "groesse": int(groesse),
        "abnahme_ts": round(time.time(), 1),
        "leinwand": list(leinwand or LEINWAND),
        "reihen": list(REIHEN), "gitter": GITTER,
        "zellen": eintraege,
        "luecken": sum(1 for e in eintraege if e.get("leer")),
        "geliehen": sum(1 for e in eintraege if e.get("geliehen_aus")),
        # Wie gross der Kandidaten-Bestand zum Abnahme-Zeitpunkt war. Daraus
        # entsteht spaeter das Auffrischungs-ANGEBOT (§6.6) — ein Hinweis, nie
        # ein stiller Austausch.
        "bestand": int(bestand) if bestand is not None else None,
    }
    _schreiben(os.path.join(ziel, MANIFEST), manifest)
    return manifest


def lesen(data_dir, person):
    """Das Herkunfts-Manifest einer abgenommenen Galerie (oder None)."""
    return _lesen(os.path.join(ordner(data_dir, person), MANIFEST))


def alle(data_dir):
    """Alle abgenommenen Galerien, Name -> Manifest."""
    aus = {}
    try:
        namen = sorted(os.listdir(wurzel(data_dir)))
    except OSError:
        return aus
    for n in namen:
        m = lesen(data_dir, n)
        if m:
            aus[n] = m
    return aus


def pruefen(data_dir, person):
    """Der Kopien-Vertrag (§6.6, qs-Stufe "Galerie-Integritaet"):

      * jede Zelle hat ihre KOPIE, und die Kopie hat noch ihren Hash
        -> die Galerie ist heil, auch wenn die Quelle laengst geloescht ist
      * fehlt eine Quelle oder hat sie sich geaendert, wird die Galerie
        "needs re-approval" — Vision urteilt fuer diese Person dann nicht mehr,
        statt still mit halben Loechern weiterzulaufen

    Rueckgabe: dict(ok, status, kopien_fehlen, kopien_veraendert,
    quellen_fehlen, quellen_veraendert, text)."""
    m = lesen(data_dir, person)
    if not m:
        return {"ok": False, "status": "keine", "text": "no gallery yet",
                "kopien_fehlen": [], "kopien_veraendert": [],
                "quellen_fehlen": [], "quellen_veraendert": []}
    ziel = ordner(data_dir, person)
    kf, kv, qf, qv = [], [], [], []
    for e in m.get("zellen") or []:
        if e.get("leer"):
            continue
        kopie = os.path.join(ziel, e.get("datei", ""))
        if not os.path.isfile(kopie):
            kf.append(e.get("datei"))
        elif e.get("kopie_hash") and _hash(kopie) != e["kopie_hash"]:
            kv.append(e.get("datei"))
        quelle = os.path.join(data_dir, "personlern", e.get("quelle_lauf", ""),
                              "crops", e.get("quelle_datei", ""))
        if not os.path.isfile(quelle):
            qf.append(e.get("quelle_datei"))
        elif e.get("quelle_hash") and _hash(quelle) != e["quelle_hash"]:
            qv.append(e.get("quelle_datei"))
    heil = not (kf or kv)
    frisch = not (qf or qv)
    if not heil:
        status, text = "kaputt", ("gallery files are missing or changed — "
                                  "build it again")
    elif not frisch:
        status = "nachabnahme"
        text = (f"{len(qf) + len(qv)} of {len(m.get('zellen') or [])} source "
                "images were deleted or changed since you approved this "
                "gallery — the gallery itself is intact, but it needs your "
                "approval again before it is used")
    else:
        status, text = "gut", "approved and intact"
    return {"ok": heil and frisch, "status": status, "text": text,
            "kopien_fehlen": kf, "kopien_veraendert": kv,
            "quellen_fehlen": qf, "quellen_veraendert": qv}


# ------------------------------------------------------- Ablehn-Ablage (§6.5)
def abgelehnt_lesen(data_dir, person):
    """Die abgelehnten Zellen dieser Person: {schluessel: {ts, reihe, grund}}.
    EIGENE Ablage — der Lernlauf-`status` wird hier nie angefasst."""
    d = _lesen(os.path.join(ordner(data_dir, person), ABGELEHNT), {})
    return d if isinstance(d, dict) else {}


def ablehnen(data_dir, person, schluessel_, reihe, grund="does not fit as a cell"):
    """Eine Zelle ablehnen (Gedaechtnis): sie kommt im Nachruecken und in jedem
    kuenftigen Vorschlag nicht wieder, bis sie zurueckgenommen wird."""
    d = abgelehnt_lesen(data_dir, person)
    d[str(schluessel_)] = {"ts": round(time.time(), 1), "reihe": reihe,
                           "grund": grund}
    _schreiben(os.path.join(ordner(data_dir, person), ABGELEHNT), d)
    return d


def ablehnung_zuruecknehmen(data_dir, person, schluessel_):
    d = abgelehnt_lesen(data_dir, person)
    d.pop(str(schluessel_), None)
    _schreiben(os.path.join(ordner(data_dir, person), ABGELEHNT), d)
    return d
