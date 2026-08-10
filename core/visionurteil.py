"""core/visionurteil — Vision detect: der Urteilspfad
(konzept_vision.md v2 §7/§8, Zuege V4/V4b/V4c).

Was hier passiert, und warum genau so:

  * **Auslöser auf PASS-Ebene (E1).** Geprueft wird EIN Durchgang, nie ein
    Einzel-Event (Szenario-Prinzip). Die Bilder kommen aus dem Kontroll-Speicher
    (Z8) — es entsteht KEIN neues Bild, es wird kein Video geoeffnet und kein
    Decode gestartet (Leitplanke §11). Ist das Bild abgelaufen, gibt es kein
    Urteil und die Anzeige sagt das im Klartext; einen Ausweg ueber einen
    eigenen Decode gibt es ausdruecklich nicht.
  * **DER KANDIDAT IST EIN GITTER (V4c, User-Entscheid 08.08. spaetabend).** Aus den N
    besten Bildern des Durchgangs wird EIN Kandidaten-Gitter gebaut — dieselbe
    Routine, dieselbe Leinwand wie bei den Galerien (core.visiongalerie.
    gitter_bauen; eine zweite Gitter-Implementierung gibt es ausdruecklich
    nicht). Gemessener Grund: derselbe Durchgang, Bild fuer Bild gefragt, wurde
    tausch-KONSISTENT falsch zugeordnet (6 von 6 Anfragen, scratchpad/
    ionos_anker_heike.json) — als Gitter gefragt gab es ueber alle gemessenen
    Paare keine einzige konsistent falsche Zuordnung (ionos_pass_matrix.json,
    ionos_galerie_vs_galerie.json). Eine Anfrage traegt damit den ganzen
    Durchgang statt einer Momentaufnahme.
  * **Guete-Sieb BEIDSEITIG.** Kandidat und Galerie werden nach DERSELBEN Regel
    gesiebt (Hoehe x Laplace-Schaerfe, Mindesthoehe aus core/visiongalerie) —
    gemessener Grund: ein winziges Zielbild ERHOEHT die Zustimmung, ein Urteil
    darueber waere geschenkt.
  * **Kaskade mit Frueh-Stopp (E2), paarweise.** Drei Bilder je Anfrage
    (Galerie A, Galerie B, Kandidaten-Gitter) — die naheliegende Drei- oder
    Vier-Wahl ist gemessen tot: instabil (ionos_dreiwahl.json) und ab fuenf
    Bildern lehnt der gemessene Endpunkt jede Anfrage mit HTTP 400 ab
    (ionos_vierwahl.json). Je Paar GENAU ZWEI Anfragen (untauscht + getauscht).
  * **Reihenfolge OHNE Fremd-Voraussetzung (V4c).** Die Kaskaden-Reihenfolge
    kommt aus eigenem Material: zuletzt per Vision bestaetigte Person zuerst,
    sonst Galerie-Alter. Liegt die Koerper-Rangfolge vor, darf sie als HINWEIS
    einfliessen — der Pfad laeuft ohne sie identisch, nur in anderer
    Pruef-Reihenfolge (User-Entscheid 08.08.: der Embedding-Weg ist unsere Spezialitaet,
    Vision muss allein tragfaehig sein).
  * **Wertung nur tausch-konsistent.** A im untauschten und B im getauschten
    Lauf meinen dieselbe Galerie; Widerspruch ist "kein Votum", nie ein
    Negativ-Beweis. NEITHER ebenso.
  * **Sammel-Regel ueber die ABGEGEBENEN Paar-Urteile** (V4c: eine Messung je
    PAAR statt je Bild): "kein Votum" ist Enthaltung, keine Gegenstimme.
    `min_voten` verlangt jetzt so viele tausch-konsistente Paar-Urteile fuer den
    Sieger — er muss also gegen mehrere Herausforderer bestehen, wo frueher
    mehrere Einzelbilder dasselbe sagen mussten. Mehr Herausforderer als
    Galerien da sind kann niemand verlangen, deshalb wird der Wert an der Zahl
    der moeglichen Paare gedeckelt. Quote und Mindestzahl bleiben Config-Werte.
  * **Kein Tuersteher davor (V4c, User-Entscheid 08.08. spaetabend).** Vision urteilt
    ueber JEDEN Durchgang, auch ueber einen, den die Koerper-Erkennung als
    unbekannt gefuehrt hat. Absicherung ist gemessen und nicht behauptet: die
    Fehlzuordnungen des GITTER-Kandidaten waren in allen Messreihen
    tausch-INKONSISTENT und enden damit als "kein Votum" (ionos_pass_matrix.
    json: 3 von 12 Paaren ohne Votum, keines konsistent falsch). E6 bleibt
    unveraendert — Vision loest keinen Alarm aus, der Wegfall des Gates aendert
    am Meldeweg nichts.

Kontrakt wie core/registry.py, core/vision.py und core/visiongalerie.py: kein
Dienst-Import, kein Dienst-Zustand, data_dir als Parameter. Der Analyse-Lock
wird hier NIE genommen — dieses Modul kennt ihn nicht einmal.
"""
import json
import os
import re
import time

from core import personlive as _plv
from core import vision as _vis
from core import visiongalerie as _vg

# --- Regeln, die auch Gate und Beweis lesen (eine Quelle) --------------------
MIN_HOEHE_PX = _vg.MIN_HOEHE_PX      # dieselbe Mindestgroesse wie die Galerie
GALERIEN_MIN = _vis.GALERIEN_MIN     # unter zwei Galerien gibt es kein Urteil
ZAEHLER_DATEI = "vision_zaehler.json"
# Stiller Ausfall (§10 Stufe 3): DIE Fehlerklasse dieses Pfades — "liefert seit
# Wochen kein Votum, niemand merkt es". Nach AUSFALL_AB ergebnislosen Laeufen in
# Folge wird gemeldet, danach fruehestens wieder nach dem Cooldown; ein Lauf mit
# Urteil setzt die Serie zurueck. Zahlen wie beim Fehlerserien-Waechter, aus
# demselben Grund gewaehlt: drei Einzelfaelle ueber Wochen sind keine Serie.
AUSFALL_AB = 3
AUSFALL_COOLDOWN_S = 6 * 3600


# ------------------------------------------------------------- Kandidatenbilder
def kandidaten(data_dir, pass_key, n=1, jetzt=None, sammeln=None, min_hoehe=None):
    """Die N besten Bilder EINES Durchgangs aus dem Kontroll-Speicher (§7) —
    sie werden zu EINEM Kandidaten-Gitter (V4c).

    `sammeln` ist der ECHTE Config-Wert `diagnostic_collection` des Dienstes
    (Live-Fund 08.08.: die Meldung riet pauschal "turn on diagnostic
    collection", obwohl der Schalter beim Nutzer AN war und nur der gewaehlte
    Durchgang aelter als der Sammel-Beginn). Der Wert wird hereingereicht und
    nie geraten; `None` heisst "nicht mitgeteilt" und faellt auf den alten,
    allgemeinen Text zurueck.

    Sieb, in dieser Reihenfolge:
      1. das Bild existiert noch (im Schlank-Modus lebt es nur waehrend des
         Durchgangs plus Karenz),
      2. Mindesthoehe wie bei der Galerie,
      3. Rang nach der KURATOR-NOTE der Galerie, bei Gleichstand nach roher
         Guete und dann nach Dateiname — derselbe Bestand ergibt immer dieselbe
         Auswahl.

    ZUR NOTE (User-Entscheid 09.08.: "die Basis hat 6, also sollte unser System
    min. 6 aus dem Lauf nehmen und durch das Optimierungsskript ausgewaehlt"):
    Bis .168 sortierte der Kandidat nach ROHER Guete (Hoehe x Schaerfe), die
    Referenzgalerie dagegen nach der saettigenden Kurator-Note. Diese Schieflage
    ist weg, beide Seiten nehmen jetzt dieselbe Regel. Die Note verwendet
    automatisch nur die Messwerte, die da sind: `_spanne` liefert fuer fehlende
    Werte None, und None erzeugt weder Bonus noch Abzug. Ueberstrahlung,
    Personenanteil und Kopfhaltung entstehen erst im Lernlauf, im Kontroll-
    Speicher gibt es sie nicht — hier wirkt deshalb die saettigende Basis aus
    Hoehe und Schaerfe.
    EHRLICH ZUR WIRKUNG (gemessen 09.08. an 3 Durchgaengen mit 7-8 Kandidaten):
    die Auswahl der besten 6 war in ALLEN drei Faellen dieselbe wie vorher, nur
    die Reihenfolge aendert sich. Der Grund sind die Mengen — bei 6 Zellen und
    selten mehr als 7 brauchbaren Bildern faellt hoechstens eines weg. Die
    Umstellung raeumt eine konzeptionelle Schieflage auf, sie ist kein
    Erkennungs-Fix.

    `min_hoehe` ueberschreibt die Mindesthoehe NUR fuer diesen Aufruf (Default
    bleibt MIN_HOEHE_PX). Gebraucht fuer Messungen: die Konstante teilen sich
    Galerie, Ernte und Urteilspfad, sie darf fuer einen Test nicht global
    verstellt werden.

    KEIN Sieb mehr nach der Koerper-Einstufung (V4c, User-Entscheid 08.08. spaetabend:
    "Embedding-Tuersteher machen wir nicht — ist ja etwas Spezielles nur bei
    uns"). Bis .159 flogen Bilder raus, die der Embedding-Weg als FREMD gefuehrt
    hatte; Vision urteilt jetzt unabhaengig davon. Die Einstufung wird trotzdem
    MITGEFUEHRT (`eingestuft`, Feld `klasse` je Bild) — sie ist der
    Vergleichs-Input der Anzeige und des optionalen Nicht-bestaetigt-Alarms,
    aber keine Vorschaltung des Laufs mehr.

    Rueckgabe: dict(bilder, geprueft, verworfen, eingestuft, grund). `grund` ist
    gefuellt, wenn nichts uebrig bleibt — er ist der Text, den die Anzeige
    zeigt."""
    mindest = int(min_hoehe or MIN_HOEHE_PX)
    d = _plv.kontrolle_dir(data_dir, pass_key)
    aus, verworfen = [], {"kein_bild": 0, "zu_klein": 0, "unlesbar": 0}
    eingestuft = {"bekannt": 0, "unbekannt": 0}
    zeilen = []
    if d:
        try:
            with open(os.path.join(d, _plv.KONTROLLE_PROTOKOLL)) as f:
                for z in f:
                    try:
                        zeilen.append(json.loads(z))
                    except ValueError:
                        pass
        except OSError:
            pass
    gesehen = set()
    for e in zeilen:
        datei = e.get("datei")
        if not datei or datei in gesehen:
            continue
        gesehen.add(datei)
        klasse = str(e.get("klasse") or "")
        if klasse and klasse != "FREMD":
            eingestuft["bekannt"] += 1
        else:
            eingestuft["unbekannt"] += 1
        pfad = os.path.join(d, datei)
        if not os.path.isfile(pfad):
            verworfen["kein_bild"] += 1
            continue
        hoehe, schaerfe, guete = _vg.guete_datei(pfad)
        if hoehe is None:
            verworfen["unlesbar"] += 1
            continue
        if hoehe < mindest:
            verworfen["zu_klein"] += 1
            continue
        aus.append({"eid": e.get("eid"), "datei": datei, "pfad": pfad,
                    "klasse": klasse, "score": e.get("score"),
                    "schwelle": e.get("schwelle"), "quelle": e.get("quelle"),
                    "ts": e.get("ts"), "hoehe": hoehe,
                    "schaerfe": round(schaerfe, 2), "guete": guete,
                    # Pose-Messwerte des Live-Pfads (ab .169 im Protokoll, bei
                    # aelteren Zeilen schlicht nicht vorhanden). Die Namen sind
                    # die des Ernte-Manifests, damit _vg.note() sie direkt liest:
                    # `gesicht` und `kopf` erwartet sie flach, die Quelle haelt
                    # sie verschachtelt.
                    "pose_erkannt": e.get("pose_erkannt"),
                    "person_anteil": e.get("person_anteil"),
                    "blick": e.get("blick"),
                    "gesicht": (e.get("blick_mess") or {}).get("gesicht"),
                    "kopf": (e.get("wache") or {}).get("kopf")})
    # Dieselbe Bewertung wie die Referenzgalerie (s. Kopfkommentar). Die rohe
    # Guete bleibt als Gleichstands-Entscheid stehen, damit die Reihenfolge
    # deterministisch ist, auch wenn zwei Noten auf dieselbe Zahl fallen.
    #
    # DAVOR steht seit .169 das einzige Merkmal, das an echtem Material
    # nachweislich TRENNT (Messung 09.08., 45 Bilder aus 10 Durchgaengen):
    # findet die Pose-Wache kein Skelett, taugt das Bild nichts. 4 von 45
    # Bildern fielen so durch, und der User hat unabhaengig ALLE VIER als
    # unbrauchbar eingestuft, die uebrigen 41 durchgewinkt. Der Messwert
    # `person_anteil` selbst trennt NICHT (alle Werte 0,53-0,78, keiner unter
    # der Kurator-Schwelle 0,45) — deshalb steht hier die Ja/Nein-Frage und
    # keine Schwelle.
    # WICHTIG, drei Zustaende statt zwei: `pose_erkannt` FEHLT bei Bildern, die
    # vor .169 abgelegt wurden. Ein fehlender Messwert ist kein schlechter
    # (dieselbe Haltung wie `_spanne`), er wird deshalb wie "erkannt" behandelt.
    # Nur ein ausdrueckliches False sortiert nach hinten. Und es sortiert nur —
    # ausgeschlossen wird nichts, sonst stuende ein Durchgang, in dem die Pose
    # nirgends greift, voellig ohne Gitter da.
    for e in aus:
        e["note"] = _vg.note(e)["note"]
    aus.sort(key=lambda e: (e.get("pose_erkannt") is False,
                            -e["note"], -e["guete"], e["datei"]))
    grund, art = "", ""
    if not aus:
        if not zeilen:
            if sammeln:
                # Der Schalter ist AN — dann ist "schalte ihn ein" schlicht
                # falsch. Was fehlt, ist Material fuer GENAU DIESEN Durchgang.
                art = "kein_material_an"
                grund = ("collecting is on, but nothing was kept for this "
                         "walk-through — it ran before collecting started, or "
                         "its images have already been trimmed. Newer passes "
                         "will have material; this one has to be analysed "
                         "again to get any")
            else:
                art = "kein_material_aus"
                grund = ("no judged images for this pass — they appear while a "
                         "pass is running; turn on diagnostic collection to "
                         "keep them")
        elif verworfen["kein_bild"] and not verworfen["zu_klein"]:
            if sammeln:
                art = "abgelaufen_an"
                grund = ("the judged images of this pass are gone although "
                         "collecting is on — they were trimmed. Analysing this "
                         "walk-through again brings them back")
            else:
                art = "abgelaufen_aus"
                grund = ("image expired — turn on diagnostic collection to "
                         "judge past passes")
        elif verworfen["zu_klein"]:
            art = "zu_klein"
            grund = ("every picture of this walk-through is too small for a "
                     f"reliable comparison (under {mindest} px)")
        else:
            art = "unbrauchbar"
            grund = "no usable picture of this walk-through"
    return {"bilder": aus[:max(1, int(n))], "geprueft": len(zeilen),
            "verworfen": verworfen, "eingestuft": eingestuft, "grund": grund,
            "grund_art": art, "gesamt": len(aus)}


# Die Gruende, bei denen eine erneute Analyse des Durchgangs ueberhaupt etwas
# bringt: der Sammel-Modus ist AN, es fehlt nur das Material dieses Passes.
# EINE Quelle — der Renderer und der Dienst holen sie hier, kein zweites
# Literal (Registry-Regel aus qs_ebenen.md).
NACHANALYSE_GRUENDE = ("kein_material_an", "abgelaufen_an")


# ------------------------------------------------------- Kandidaten-Gitter (V4c)
def kandidaten_gitter(bilder, leinwand=None):
    """Aus den gesiebten Bildern EINES Durchgangs EIN Kandidaten-Gitter.

    Gebaut wird mit `core.visiongalerie.gitter_bauen` — DERSELBEN Routine und
    derselben Leinwand wie bei den Galerien. Das ist keine Bequemlichkeit,
    sondern die Deckungs-Regel: eine zweite Gitter-Implementierung waere ein
    zweites Layout, und das Urteil haengt nachweislich am Layout (die gemessenen
    Gitter sind genau diese Leinwand).

    Spaltenzahl folgt der Zellenzahl (drei Reihen wie im Galerie-Layout, also
    `ceil(n/3)` Spalten); ueberzaehlige Zellen bleiben leer und werden als
    `luecken` gemeldet, nie als Bild behauptet.

    Rueckgabe: (b64, manifest) — `manifest` traegt groesse/luecken/zellen und
    ist damit feldgleich zu dem, was `_zellen_zahl` von einer Galerie liest.
    Ohne Bilder: (None, None)."""
    import cv2
    pfade = [b.get("pfad") for b in (bilder or []) if b.get("pfad")]
    if not pfade:
        return None, None
    spalten = max(1, -(-len(pfade) // len(_vg.REIHEN)))
    groesse = spalten * len(_vg.REIHEN)
    voll = list(pfade) + [None] * (groesse - len(pfade))
    bild = _vg.gitter_bauen(voll, groesse, leinwand or _vg.LEINWAND)
    ok, buf = cv2.imencode(".jpg", bild, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not ok:
        return None, None
    import base64
    manifest = {"groesse": groesse, "luecken": groesse - len(pfade),
                "zellen": len(pfade), "spalten": spalten,
                "leinwand": list(leinwand or _vg.LEINWAND)}
    return base64.b64encode(buf.tobytes()).decode(), manifest


# Namens-Praefix der abgelegten Gitter-Datei — EINE Quelle fuer den Schreiber
# hier und den Leser (Renderer); die Waisen-Raeumung braucht den Namen gar
# nicht, sie liest das Feld `gitter_datei` aus der Abschlusszeile.
GITTER_VOR = "gitter_"
_LAUF_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z_.\-]{0,63}")


def gitter_ablegen(data_dir, pass_key, lauf_id, b64):
    """Das GERENDERTE Kandidaten-Gitter als JPG neben das Protokoll des Passes.

    Warum (User 09.08.): bis hierher entstand das Gitter nur im Speicher und
    ging als base64 in die Anfrage. Nachvollziehen liess sich hinterher, WELCHE
    Bilder hineingingen — nie das fertige Bild, das der Urteiler wirklich sah.
    Genau das ist beim Einstellen der Zellenzahl aber die Frage.

    KEIN zweites Aufbewahrungsregime: die Datei liegt im Pass-Ordner und faellt
    ueber DENSELBEN Trim wie die uebrigen Pass-Bilder (core.personlive:
    Verfall nach TRIM_TAGE, Schlank-Raeumung bei ausgeschaltetem Sammel-Modus).
    Damit die WAISEN-Regel sie nicht sofort wieder wegnimmt, traegt die
    Abschlusszeile ihren Namen im Feld `gitter_datei`; genau dieses Feld bucht
    `core.personlive.kontrolle_raeumen` mit.

    Reine Ablage wie `personlive.kontrolle_ablegen`: ein Fehler bleibt still und
    aendert kein Urteil. Rueckgabe: Dateiname oder None."""
    if not b64:
        return None
    d = _plv.kontrolle_dir(data_dir, pass_key)
    if d is None or not _LAUF_RE.fullmatch(str(lauf_id)):
        return None
    import base64
    datei = GITTER_VOR + str(lauf_id) + ".jpg"
    try:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, datei), "wb") as f:
            f.write(base64.b64decode(b64))
            f.flush()
            os.fsync(f.fileno())
    except (OSError, ValueError):
        return None
    return datei


# ------------------------------------------------------- Reihenfolge (E2, §7)
def zentroide(data_dir):
    """Person -> normierter Zentroid im DINOv2-Raum (personlern/modell/
    embeddings.npz). Leeres dict, wenn es kein Modell gibt."""
    import numpy as np
    from core.personmodell import modell_dir
    p = os.path.join(modell_dir(data_dir), "embeddings.npz")
    if not os.path.isfile(p):
        return {}
    try:
        d = np.load(p, allow_pickle=False)
        X, labels = d["X"], [str(x) for x in d["labels"]]
    except (OSError, ValueError, KeyError):
        return {}
    aus = {}
    for name in sorted(set(labels)):
        m = X[[i for i, l in enumerate(labels) if l == name]]
        if not len(m):
            continue
        z = m.mean(axis=0)
        n = float(np.linalg.norm(z))
        aus[name] = z / n if n else z
    return aus


def reihenfolge(data_dir, bild_rgb, personen, einbetten=None):
    """Die Reihenfolge der Kaskade (E2, User-Entscheid: "die Personenerkennung steuert
    die Reihenfolge, nicht A/B/C/D"): Zentroid-Abstand im DINOv2-Raum, absteigend.

    Massgeblich ist DINOv2 und nicht der Gesichts-Raum: Kandidat und Galerien
    sind KOERPER-Crops; der Gesichts-Raum lieferte hier einen Distraktor, der
    auf dem Bild gar nicht aehnlich aussieht. Personen ohne Embedding fallen
    nicht heraus, sie stehen hinten (nach Namen, damit es deterministisch ist).

    Rueckgabe: [(person, aehnlichkeit|None), ...]"""
    import numpy as np
    zs = zentroide(data_dir)
    kand = (einbetten or _plv.einbetten)(bild_rgb)
    mit, ohne = [], []
    for p in personen:
        z = zs.get(p)
        if z is None:
            ohne.append((p, None))
            continue
        mit.append((p, round(float(np.dot(kand, z)), 4)))
    mit.sort(key=lambda e: (-e[1], e[0]))
    ohne.sort()
    return mit + ohne


def zuletzt_bestaetigt(data_dir, max_passe=20):
    """Die Person des juengsten Vision-URTEILS (oder None). Eigenes Material des
    Vision-Pfades — kein fremdes Modell, keine Einbettung, nur das eigene
    Protokoll. Bewusst nur die juengsten Paesse: das ist eine Reihenfolge-Frage,
    keine Statistik."""
    try:
        ordner = sorted(os.listdir(_plv.kontrolle_dir(data_dir)), reverse=True)
    except OSError:
        return None
    for pk in ordner[:max(1, int(max_passe))]:
        for z in reversed(urteile_lesen(data_dir, pk)):
            if z.get("person"):
                return str(z["person"])
    return None


def eigene_ordnung(galerien, zuletzt=None):
    """Die Kaskaden-Reihenfolge OHNE jede fremde Voraussetzung (V4c).

    Zuerst die zuletzt per Vision bestaetigte Person (wer gerade ueber das
    Grundstueck laeuft, war meistens schon einmal da), danach nach
    Galerie-Alter, bei Gleichstand nach Namen. Rein deterministisch: derselbe
    Bestand ergibt immer dieselbe Reihenfolge, und dieselbe Reihenfolge auf
    jeder Installation — auch auf einer ohne Koerper-Modell.

    Rueckgabe wie `reihenfolge`: [(person, aehnlichkeit|None), ...]; die
    Aehnlichkeit ist hier immer None, denn es wird nichts gerechnet."""
    g = dict(galerien or {})
    return [(n, None) for n in sorted(
        g, key=lambda n: (0 if n == zuletzt else 1,
                          float((g.get(n) or {}).get("abnahme_ts") or 0), n))]


def kontrast_ordnung(ordnung):
    """KONTRAST-REIHENFOLGE (.164, Entscheid 09.08. nach den 08:26er-Laeufen).

    Der FAVORIT bleibt, wo er ist: die wahrscheinlichste Person zuerst. Die
    HERAUSFORDERER dagegen kommen ab jetzt vom UNAEHNLICHSTEN zum aehnlichsten.

    Warum: die B-Seite der Zwangswahl ist das Format-Gegenueber, nicht der
    Pruefstein. Bis .163 stellte die Rangfolge dem Favoriten ausgerechnet die
    AEHNLICHSTE Person gegenueber — also den schwersten denkbaren Vergleich in
    Runde 1. Am Live-Lauf vom 09.08. kippte genau das zweimal in die
    Positions-Schlagseite (beide Tauschseiten antworteten 'A'), das Paar wurde
    zur Enthaltung; gegen den unaehnlichsten Gegner fiel dasselbe Paar
    beidseitig sauber. Ein klarer Kontrast liefert das konsistente Paar in
    Runde 1 — die schweren Vergleiche kommen danach, wenn sie ueberhaupt noch
    gebraucht werden.

    Gedreht wird NUR, wo es einen Aehnlichkeitswert gibt. Personen ohne
    Embedding tragen keinen Abstand; sie zu "unaehnlich" zu erklaeren waere
    erfunden, also bleiben sie hinten in ihrer deterministischen Namensfolge.
    Rein: gleiche Eingabe -> gleiche Ausgabe."""
    o = list(ordnung or ())
    if len(o) < 3:
        return o                    # ein Favorit und ein Herausforderer: nichts zu drehen
    favorit, rest = o[0], o[1:]
    mit = [e for e in rest if e[1] is not None]
    ohne = [e for e in rest if e[1] is None]
    return [favorit] + list(reversed(mit)) + ohne


def ordnung_bauen(data_dir, galerien, bild_rgb=None, einbetten=None,
                  zuletzt=None):
    """Die Reihenfolge, die die Kaskade wirklich faehrt — plus die QUELLE im
    Klartext (das Erzaehl-Log nennt sie, statt eine Herkunft zu verschweigen).

    ENTSCHEID (User 08.08. spaetabend): der Vision-Pfad darf die
    Koerper-Rangfolge nicht VORAUSSETZEN — sie ist eine Eigenheit dieser
    Installation, Vision soll auch allein tragen. Liegt sie vor, ist sie ein
    HINWEIS und sortiert; liegt sie nicht vor, laeuft derselbe Pfad mit der
    eigenen Ordnung. Die URTEILE sind in beiden Faellen dieselben, nur die
    Pruef-Reihenfolge unterscheidet sich.

    FORTGESCHRIEBEN .164: liegt die Rangfolge vor, wird sie fuer die
    HERAUSFORDERER umgedreht (`kontrast_ordnung`) — Favorit unveraendert,
    unaehnlichster Gegner zuerst. Ohne Rangfolge bleibt die eigene Ordnung wie
    sie war: dort gibt es keinen Aehnlichkeits-Abstand, und eine Umdrehung
    ohne Messgroesse waere Zufall mit dem Anschein von Methode. Die Quelle
    sagt beides ehrlich.

    Rueckgabe: (ordnung, quelle)."""
    eigen = eigene_ordnung(galerien, zuletzt)
    quelle = ("last confirmed person first" if zuletzt
              else "gallery age (nothing confirmed yet)")
    if bild_rgb is None:
        return eigen, quelle
    try:
        if not zentroide(data_dir):
            return eigen, quelle          # kein Modell -> gar nicht erst rechnen
        mit = reihenfolge(data_dir, bild_rgb, [n for n, _ in eigen], einbetten)
    except Exception:
        return eigen, quelle              # ein Hinweis kippt nie einen Lauf
    if not mit or all(s is None for _, s in mit):
        return eigen, quelle
    return (kontrast_ordnung(mit),
            "favourite by body ranking, challengers most-different first")


# ------------------------------------------------------------------- Kaskade
def _b64(pfad):
    import base64
    with open(pfad, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _zellen_zahl(manifest):
    """Wie viele Bilder das Gitter WIRKLICH zeigt — Luecken zaehlen nicht mit.
    Die Zahl steht woertlich im Label ("6 images of ONE person"), eine falsche
    Zahl waere eine Behauptung ueber das Bild."""
    g = int((manifest or {}).get("groesse") or 0)
    return max(0, g - int((manifest or {}).get("luecken") or 0))


def teile_bauen(gal_a, gal_b, kandidat_b64, kandidat_zellen=0):
    """Die Bild-/Text-Folge EINER Anfrage, byte-genau in der gemessenen
    Reihenfolge: Label A, Gitter A, Label B, Gitter B, Kandidaten-Label,
    Kandidat. gal_* = (manifest, gitter_b64).

    DREI Bilder — genau `_vis.BILDER_JE_ANFRAGE`, und das ist der Grund fuer die
    paarweise Kaskade: der gemessene Endpunkt nimmt vier Bilder je Anfrage an
    und lehnt fuenf ab, eine Vier-Wahl braeuchte fuenf.

    `kandidat_zellen` traegt die WIRKLICH gefuellten Zellen des
    Kandidaten-Gitters ins Label (V4c) — bei einem Einzelbild bleibt es beim
    gemessenen Einzelbild-Label."""
    ma, ba = gal_a
    mb, bb = gal_b
    return [("text", _vis.label_a(_zellen_zahl(ma))), ("bild", ba),
            ("text", _vis.label_b(_zellen_zahl(mb))), ("bild", bb),
            ("text", _vis.label_k(kandidat_zellen)), ("bild", kandidat_b64)]


def _sagen(melden, text, **felder):
    """Eine Erzaehl-Zeile absetzen, wenn ein Melder da ist. Der Lauf laeuft auch
    ohne — das Log ist Mitnahme, nie Voraussetzung."""
    if melden:
        try:
            melden(text, **felder)
        except Exception:
            pass                      # ein Log-Fehler kippt nie ein Urteil


def _antwort_satz(u, name_a, name_b, runde, arm, doppellauf=True):
    """EIN Lauf in Klartext. Konkret statt geglaettet: das echte Antwort-Wort,
    der echte Name der Galerie, die es meint, die echte Dauer.

    Ohne Doppellauf heisst der Arm nicht "as shown" — es gibt nichts, wogegen
    er stuende; er heisst "single run — swap check off"."""
    wer = {"A": name_a, "B": name_b}.get(u.get("wahl"))
    wie = (("as shown" if arm == 1 else "galleries swapped") if doppellauf
           else "single run — swap check off")
    dauer = f" ({u['dauer_s']} s)" if u.get("dauer_s") is not None else ""
    if u.get("kein_votum"):
        return (f"round {runde}, {wie}: no usable answer — "
                f"{_vis.grund_text(u.get('grund'))}{dauer}")
    if u.get("wahl") == "NEITHER":
        return f"round {runde}, {wie}: the model answered NEITHER{dauer}"
    return (f"round {runde}, {wie}: the model answered {u['wahl']} — "
            f"that is {wer}{dauer}")


def min_wirksam(min_voten, paare_moeglich=None):
    """Die Mindestzahl tausch-konsistenter Paar-Urteile, die WIRKLICH verlangt
    werden kann (V4c).

    Der Config-Wert sagt, wie oft der Sieger bestaetigt sein soll. Mehr
    Bestaetigungen als es Herausforderer gibt kann niemand liefern — bei genau
    zwei abgenommenen Galerien existiert exakt EIN Paar. Ohne diesen Deckel
    haette eine ganz normale Installation nie ein Urteil bekommen, und zwar
    still."""
    n = max(1, int(min_voten or 1))
    if paare_moeglich:
        n = min(n, max(1, int(paare_moeglich)))
    return n


def urteile_aus_runden(runden):
    """Die Paar-Urteile einer Kaskade als Liste fuer die Sammel-Regel (V4c: EIN
    Urteil je PAAR, frueher eines je Bild). Ein Votum gibt es nur, wo der Tausch
    konsistent war; `A` meint die erste Galerie der Runde, `B` die zweite.

    Runden OHNE Votum kommen als Enthaltung MIT — sonst zaehlte die Anzeige
    "1 von 1 Vergleichen" statt ehrlich "1 von 2", und der Anteil unbrauchbarer
    Vergleiche verschwaende genau so, wie es §8 verbietet."""
    aus = []
    for r in runden or []:
        if r.get("kein_votum") or r.get("wahl") not in ("A", "B"):
            aus.append(_vis.urteil_leer(grund=r.get("grund"), arm=r.get("nr"),
                                        wahl=r.get("wahl"),
                                        konsistent=r.get("konsistent"),
                                        dauer_s=r.get("dauer_s")))
            continue
        aus.append(_vis.urteil_leer(
            person=r["a"] if r["wahl"] == "A" else r["b"], wahl=r["wahl"],
            konsistent=True, kein_votum=False, beginnt_mit_wort=True,
            arm=r.get("nr"), dauer_s=r.get("dauer_s")))
    return aus


def kaskade(galerien, ordnung, kandidat_b64, anfrage_fn, budget=None,
            melden=None, kandidat_zellen=0, min_bestaetigungen=1,
            doppellauf=True):
    """Kaskade mit Frueh-Stopp (E2). `galerien` = {person: (manifest, b64)},
    `ordnung` = Personen nach Wahrscheinlichkeit, `anfrage_fn(teile)` liefert ein
    NORMIERTES Einzel-Urteil (core.vision.antwort_auswerten) — dadurch ist der
    ganze Pfad ohne Netz pruefbar und die Kaskade kennt kein HTTP.

    budget = hoechstens so viele Anfragen (Deckel, §7). Reicht es fuer die
    naechste Runde nicht, endet die Kaskade mit Grund "deckel" statt eine halbe
    Runde zu fahren (eine einzelne Anfrage ohne ihren Tauschlauf ist wertlos).

    melden(text, **felder) (V4b, User-Wunsch 08.08.: "super waere es wenn man
    lesen koennte was passiert"): wird VOR und NACH jeder Anfrage gerufen. Eine
    Anfrage dauert lokal Minuten — ohne diese Zeilen sieht der Nutzer minutenlang
    nichts und weiss nicht, ob ueberhaupt etwas passiert.

    kandidat_zellen (V4c): wie viele Bilder das Kandidaten-GITTER wirklich zeigt
    — die Zahl steht woertlich im Label.

    min_bestaetigungen (V4c): so oft muss der Favorit seine Stellung als A
    verteidigen, bevor die Kaskade stoppt. 1 ist der bisherige Frueh-Stopp
    (eindeutig = Schluss); groessere Werte lassen den Sieger gegen weitere
    Herausforderer antreten, statt wie frueher mehrere Einzelbilder zu befragen.
    Der Wert kommt gedeckelt herein (`min_wirksam`) — mehr Herausforderer als
    Galerien gibt es nicht.

    ENTHALTUNG BEENDET DEN LAUF NICHT (.162, User-Entscheid nach dem Live-Fall
    vom 09.08.): ein Paar ohne Votum — Tausch-Widerspruch ODER konsistentes
    NEITHER — ist eine ENTHALTUNG. Der Favorit bleibt, der naechste
    Herausforderer wird gefragt, und der Lauf endet erst, wenn die
    Herausforderer alle sind (oder das Budget greift). Die offenen Paare stehen
    im Rueckgabe-Objekt (`offen`) und im Erzaehl-Log; sie werden nie zu einem
    Negativ-Beweis und nie verschwiegen.

    VERWORFENES SOLL (bis 0.1.0.161, hier absichtlich als Historie stehend):
    bis .161 BRACH die Kaskade bei der ersten Enthaltung ab, mit der Begruendung
    "nicht durch die restlichen Galerien raten". Gekippt am 09.08. an einem
    echten Durchgang: Runde 1 lieferte zweimal dieselbe Antwort auf beiden
    Tauschseiten (die bekannte Positions-Neigung, §2.5), das Paar galt als
    Widerspruch — und die beiden restlichen Galerien wurden nie gefragt,
    obwohl gegen sie noch gar nichts gesagt war. Ein Abbruch macht aus einer
    Enthaltung faktisch ein Urteil ueber ALLE ungefragten Personen; genau das
    verbietet §4.

    doppellauf (.165, abschaltbar): jedes Paar wird ZWEIMAL gefragt, mit
    getauschten Galerien — das ist der Positions-Test (§2.5). Auf False kostet
    ein Paar nur EINE Anfrage, gewertet wird das eine Antwort-Wort, und der
    Lauf weist das ueberall aus (Urteil, Runden, Erzaehl-Log). Der Default
    bleibt True: die Schlagseite ist gemessen und der Tausch ist das einzige,
    was sie sichtbar macht.

    Rueckgabe: (urteil, runden, anfragen)."""
    runden, anfragen, summe = [], 0, {}
    offen = []              # Paare ohne Votum (Enthaltungen), ehrlich mitgefuehrt
    doppellauf = bool(doppellauf)
    ordnung = [p for p, _ in ordnung] if ordnung and isinstance(
        ordnung[0], (tuple, list)) else list(ordnung)
    ordnung = [p for p in ordnung if p in galerien]
    if len(ordnung) < GALERIEN_MIN:
        _sagen(melden, "not enough approved galleries to compare against")
        return _vis.urteil_leer(grund="zu_wenige_galerien"), runden, anfragen
    noetig = min_wirksam(min_bestaetigungen, len(ordnung) - 1)
    favorit, letzte, bestaetigt = ordnung[0], None, 0
    letzte_mit_votum = None
    herausforderer = ordnung[1:]
    for _i, gegner in enumerate(herausforderer):
        if budget is not None and anfragen + 2 > budget:
            _sagen(melden, "stopping here — the request limit is reached")
            u = _vis.urteil_leer(grund="deckel")
            u["arm"] = len(runden)
            return u, runden, anfragen
        r = len(runden) + 1
        _sagen(melden,
               f"round {r}: asking {favorit} vs {gegner}"
               + ("" if r == 1 else
                  f" — {favorit} won the last round, next challenger is {gegner}")
               + (". Each round is asked twice, with the galleries swapped."
                  if doppellauf else
                  ". Asked ONCE — the swap check is switched off, so the "
                  "position bias is not tested."),
               runde=r, a=favorit, b=gegner, doppellauf=doppellauf)
        u1 = anfrage_fn(teile_bauen(galerien[favorit], galerien[gegner],
                                    kandidat_b64, kandidat_zellen))
        _sagen(melden, _antwort_satz(u1, favorit, gegner, r, 1, doppellauf),
               runde=r, arm=1, wahl=u1.get("wahl"), dauer_s=u1.get("dauer_s"))
        if doppellauf:
            u2 = anfrage_fn(teile_bauen(galerien[gegner], galerien[favorit],
                                        kandidat_b64, kandidat_zellen))
            _sagen(melden, _antwort_satz(u2, gegner, favorit, r, 2, True),
                   runde=r, arm=2, wahl=u2.get("wahl"),
                   dauer_s=u2.get("dauer_s"))
            anfragen += 2
            paar = _vis.paar_werten(u1, u2)
        else:
            anfragen += 1
            paar = _vis.einzel_werten(u1)
        if paar.get("kein_votum"):
            _sagen(melden,
                   f"round {r}: no vote — {_vis.grund_text(paar.get('grund'))}."
                   f" That is an abstention, not a point against {favorit} or "
                   f"{gegner} — nothing was decided about either of them.",
                   runde=r, grund=paar.get("grund"), enthaltung=True)
        elif paar.get("wahl") == "A":
            _sagen(melden,
                   (f"round {r}: both runs point at {favorit} — consistent, so "
                    "this comparison votes for that person"
                    if doppellauf else
                    f"round {r}: the single run points at {favorit} — swap "
                    "check off, so this counts on one answer alone")
                   + f" ({bestaetigt + 1} of {noetig} needed)",
                   runde=r, person=favorit, doppellauf=doppellauf)
        else:
            _sagen(melden,
                   (f"round {r}: both runs point at {gegner} — consistent, so "
                    if doppellauf else
                    f"round {r}: the single run points at {gegner} — swap "
                    "check off, so ")
                   + f"{gegner} takes over as the favourite for the next round",
                   runde=r, person=gegner, doppellauf=doppellauf)
        for feld in ("prompt", "completion", "total"):
            a = (summe.get(feld) or 0) + ((paar["token"] or {}).get(feld) or 0)
            summe[feld] = a or None
        letzte = paar
        runden.append({"nr": len(runden) + 1, "a": favorit, "b": gegner,
                       "wahl": paar["wahl"], "konsistent": paar["konsistent"],
                       "kein_votum": paar["kein_votum"], "grund": paar["grund"],
                       "einzeln": ([u1["wahl"], u2["wahl"]] if doppellauf
                                   else [u1["wahl"]]),
                       "doppellauf": doppellauf,
                       "dauer_s": paar["dauer_s"]})
        if paar["kein_votum"]:
            # ENTHALTUNG (.162): NEITHER oder Tausch-Widerspruch heisst "dieses
            # Paar hat nichts entschieden" — weder fuer noch gegen einen der
            # beiden. Der Favorit bleibt, der naechste Herausforderer kommt
            # dran. Bis .161 endete der Lauf hier (verworfenes SOLL, s.
            # Docstring): damit wurden Personen ungefragt mit-erledigt.
            offen.append({"nr": len(runden), "a": favorit, "b": gegner,
                          "grund": paar["grund"]})
            if _i + 1 < len(herausforderer):
                _sagen(melden,
                       f"{favorit} stays the favourite (nothing spoke against "
                       "them) — asking the next challenger", runde=r,
                       person=favorit)
            continue
        letzte_mit_votum = paar
        if paar["wahl"] == "A":
            bestaetigt += 1
            if bestaetigt >= noetig:
                break                   # EINDEUTIG -> STOPP (Normalfall)
            if _i + 1 < len(herausforderer):
                _sagen(melden,
                       f"{favorit} still needs {noetig - bestaetigt} more "
                       "consistent comparison(s) — asking the next challenger",
                       runde=r, person=favorit)
            continue
        favorit, bestaetigt = gegner, 0  # B gewinnt -> neuer Favorit, von vorn
    else:
        # Die Herausforderer sind alle — und der Favorit hat seine
        # Bestaetigungen nicht voll. Das gehoert AUSGESPROCHEN: sonst stuende
        # da nur ein Urteil (oder keines) ohne den Grund davor.
        if runden and bestaetigt < noetig:
            _sagen(melden, "no gallery left to ask — "
                           f"{favorit} was confirmed {bestaetigt} of {noetig} "
                           "time(s)", person=favorit)
    # Der Sammel-Satz ueber die offenen Paare steht bewusst NICHT hier, sondern
    # genau einmal an der Abschluss-Zeile (`pass_urteilen`) — zusammen mit dem
    # Urteil, zu dem er gehoert. Zweimal derselbe Satz waere Rauschen.
    # Hat ueberhaupt eine Runde ein Votum abgegeben? Wenn nicht, darf hier kein
    # Favorit als Person behauptet werden — sonst stuende im Objekt ein Name,
    # den kein einziger Vergleich getragen hat.
    votum_da = bool(letzte_mit_votum)
    u = _vis.urteil_leer(person=favorit if votum_da else None,
                         wahl=(letzte_mit_votum or {}).get("wahl"),
                         konsistent=True if votum_da else None,
                         kein_votum=not votum_da,
                         grund=None if votum_da else (offen[-1]["grund"]
                                                      if offen else None),
                         beginnt_mit_wort=votum_da, arm=len(runden),
                         galerie_stand=_stand(galerien, runden),
                         backend=(letzte or {}).get("backend", ""),
                         quelle=(letzte or {}).get("quelle", ""),
                         custom_prompt=bool((letzte or {}).get("custom_prompt")))
    u["dauer_s"] = round(sum(r.get("dauer_s") or 0 for r in runden), 1) or None
    # Token ueber ALLE Runden, nicht nur die letzte: das Urteil hat sie alle
    # gekostet, und der Deckel rechnet in Anfragen, die Kosten-Anzeige in Token.
    u["token"] = dict(summe) or u["token"]
    u["offen"] = offen
    u["doppellauf"] = doppellauf
    return u, runden, anfragen


def offen_satz(offen):
    """EIN Satz ueber die unentschiedenen Vergleiche — dieselbe Formulierung im
    Erzaehl-Log und in der Anzeige (eine Quelle, kein zweiter Wortlaut).

    Er nennt die betroffenen Namen und den Grund, weil "1 unresolved" allein
    nichts wert ist: der Nutzer muss sehen, WER ungeklaert blieb."""
    if not offen:
        return ""
    teile = []
    for e in offen:
        teile.append(f"{e.get('a')} vs {e.get('b')} "
                     f"({_vis.grund_text(e.get('grund'))})")
    return (f"{len(offen)} comparison(s) stayed unresolved and decided nothing "
            "either way: " + "; ".join(teile))


def _stand(galerien, runden):
    """Womit tatsaechlich verglichen wurde — die beiden Namen der letzten Runde
    plus die Groessen. Die Anzeige nennt genau das (§4: nie eine Formulierung,
    die eine Aussage ueber ungepruefte Personen suggeriert)."""
    if not runden:
        return None
    r = runden[-1]
    return {"a": r["a"], "b": r["b"], "runden": len(runden),
            "zellen": {r["a"]: _zellen_zahl(galerien[r["a"]][0]),
                       r["b"]: _zellen_zahl(galerien[r["b"]][0])}}


# --------------------------------------------------------------- Sammel-Regel
def sammeln(urteile, quote=1.0, min_voten=2, paare_moeglich=None):
    """Aus den Paar-Urteilen eines Durchgangs GENAU EIN Gesamturteil
    (User-Entscheid 08.08., fortgeschrieben V4c).

    V4c: gesammelt werden die tausch-konsistenten PAAR-Urteile der Kaskade, nicht
    mehr die Urteile ueber N Einzelbilder — der ganze Durchgang steckt jetzt in
    EINEM Kandidaten-Gitter, die Wiederholung liegt also nicht mehr in den
    Bildern, sondern in den Herausforderern. Die Rechnung selbst ist unveraendert:

      * Die Quote laeuft ueber die ABGEGEBENEN Voten, nie ueber die Versuche —
        "kein Votum" ist Enthaltung, keine Gegenstimme.
      * Verlangt werden mindestens `min_voten` abgegebene Voten, gedeckelt an der
        Zahl der moeglichen Paare (`paare_moeglich`): bei genau zwei Galerien
        gibt es exakt ein Paar, und eine unerfuellbare Forderung waere ein
        stiller Dauer-Ausfall.

    Rueckgabe: dict(person, voten, bilder, verteilung, anteil, grund,
    min_voten, min_voten_wirksam). `bilder` heisst aus Rueckwaerts-Gruenden
    weiter so und zaehlt die VERSUCHE (bis .159 Bilder, seit V4c Paare)."""
    voten = [u for u in urteile if u.get("person") and not u.get("kein_votum")]
    verteilung = {}
    for u in voten:
        verteilung[u["person"]] = verteilung.get(u["person"], 0) + 1
    noetig = min_wirksam(min_voten, paare_moeglich)
    aus = {"person": None, "bilder": len(urteile), "voten": len(voten),
           "verteilung": verteilung, "anteil": None, "quote": float(quote),
           "min_voten": int(min_voten), "min_voten_wirksam": noetig,
           "grund": ""}
    if not voten:
        aus["grund"] = "no comparison gave a usable answer"
        return aus
    beste = max(sorted(verteilung), key=lambda p: verteilung[p])
    anteil = verteilung[beste] / len(voten)
    aus["anteil"] = round(anteil, 3)
    if len(voten) < noetig:
        aus["grund"] = (f"only {len(voten)} of {len(urteile)} comparison(s) "
                        f"gave an answer — {noetig} are required")
        return aus
    if anteil + 1e-9 < float(quote):
        aus["grund"] = ("the comparisons contradict each other: "
                        + ", ".join(f"{verteilung[p]}x {p}"
                                    for p in sorted(verteilung)))
        return aus
    aus["person"] = beste
    return aus


# ------------------------------------------------- Zaehler, Deckel, Ausfall
def zaehler_pfad(data_dir):
    return os.path.join(str(data_dir or ""), "state", ZAEHLER_DATEI)


def zaehler_lesen(data_dir):
    leer = {"urteile": 0, "kein_votum_neither": 0, "kein_votum_widerspruch": 0,
            "fehler": 0, "timeouts": 0, "deckel_pausen": 0, "anfragen": [],
            "ausfall_serie": 0, "ausfall_gemeldet_ts": 0, "letzter_lauf": 0,
            "letzter_fehler": ""}
    try:
        with open(zaehler_pfad(data_dir)) as f:
            d = json.load(f)
    except (OSError, ValueError):
        return leer
    leer.update({k: v for k, v in (d or {}).items() if k in leer})
    return leer


def zaehler_schreiben(data_dir, z):
    """Atomar + geflusht (Muster der uebrigen Stores): ein halber Schreibvorgang
    darf keinen Zaehler zerreissen — an ihm haengt der Deckel."""
    p = zaehler_pfad(data_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(z, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def deckel_lage(z, jetzt, max_h, max_tag):
    """Wie viele Anfragen im laufenden Stunden-/Tagesfenster schon gingen und
    wie viele noch frei sind. Gezaehlt wird JEDE Anfrage, auch die
    fehlgeschlagene (§7) — jeder Versuch ist ein weiterer Bild-Upload und, bei
    bezahlten Endpunkten, Geld."""
    ts = [float(t) for t in (z.get("anfragen") or []) if float(t) > jetzt - 86400]
    h = sum(1 for t in ts if t > jetzt - 3600)
    return {"stunde": h, "tag": len(ts), "frei_h": max(0, int(max_h) - h),
            "frei_tag": max(0, int(max_tag) - len(ts)),
            "frei": max(0, min(int(max_h) - h, int(max_tag) - len(ts)))}


def anfragen_buchen(z, jetzt, n=1):
    ts = [float(t) for t in (z.get("anfragen") or []) if float(t) > jetzt - 86400]
    z["anfragen"] = ts + [round(float(jetzt), 1)] * int(n)
    return z


def ausfall_buchen(z, mit_urteil, jetzt):
    """Stiller Ausfall (§10 Stufe 3). Ein Lauf MIT Gesamturteil setzt die Serie
    zurueck; ohne Urteil waechst sie. Ab AUSFALL_AB meldet der Dienst eine
    Stoerung — danach erst wieder nach dem Cooldown, damit eine anhaltende
    Stoerung meldet, ohne zu spammen.

    Rueckgabe: (z, stoerung: bool)."""
    if mit_urteil:
        z["ausfall_serie"] = 0
        z["ausfall_gemeldet_ts"] = 0
        return z, False
    z["ausfall_serie"] = int(z.get("ausfall_serie") or 0) + 1
    if z["ausfall_serie"] < AUSFALL_AB:
        return z, False
    # 0 heisst "noch nie gemeldet" — nicht "gerade eben gemeldet". Ohne diese
    # Unterscheidung haette der Cooldown die ERSTE Meldung verschluckt, solange
    # die Uhr des Laufs unter dem Cooldown liegt; genau das hat die Gate-Stufe
    # beim Bau gefangen.
    letzt = float(z.get("ausfall_gemeldet_ts") or 0)
    if letzt and jetzt - letzt < AUSFALL_COOLDOWN_S:
        return z, False
    z["ausfall_gemeldet_ts"] = round(float(jetzt), 1)
    return z, True


# ------------------------------------------------------- Protokoll (§8)
# Zwei Sorten Zeile in EINER Datei (V4b): die Erzaehl-Schritte waehrend des
# Laufs und das Urteil am Ende. Eine zweite Datei waere ein zweites
# Aufbewahrungsregime (§8) — hier ist es dieselbe Datei, derselbe Trim, derselbe
# Waisen-Schutz. Alt-Zeilen ohne `art` sind Urteile (Rueckwaerts-Vertrag).
ART_SCHRITT = "schritt"
ART_URTEIL = "urteil"


def melder(data_dir, pass_key, lauf_id):
    """Gibt `melden(text, **felder)` zurueck: schreibt JEDE Zeile SOFORT und
    geflusht ins Lauf-Protokoll. Pro Schritt, nicht am Ende — sonst stuende bei
    einem Abbruch nach 20 Minuten nichts da, und die Seite koennte waehrend des
    Laufs nichts anzeigen (genau das ist der Zweck)."""
    zaehler = {"n": 0}

    def melden(text, **felder):
        zaehler["n"] += 1
        zeile = {"art": ART_SCHRITT, "lauf": str(lauf_id), "nr": zaehler["n"],
                 "ts": round(time.time(), 1), "text": str(text)}
        zeile.update({k: v for k, v in felder.items() if v is not None})
        protokoll_schreiben(data_dir, pass_key, zeile)
        return zeile

    return melden


def protokoll_schreiben(data_dir, pass_key, zeile):
    """Die Vision-Protokollzeile NEBEN das Kontroll-Protokoll desselben Passes
    (§8) — kein zweites Aufbewahrungsregime: sie verfaellt mit dem Pass-Ordner
    ueber denselben Trim (core.personlive.TRIM_TAGE) und ueberlebt die
    Waisen-Raeumung ueber PASS_PROTOKOLLE."""
    d = _plv.kontrolle_dir(data_dir, pass_key)
    if d is None:
        return None
    try:
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, _plv.VISION_PROTOKOLL)
        with open(p, "a") as f:
            f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return p
    except OSError:
        return None


def protokoll_lesen(data_dir, pass_key):
    d = _plv.kontrolle_dir(data_dir, pass_key)
    aus = []
    if d is None:
        return aus
    try:
        with open(os.path.join(d, _plv.VISION_PROTOKOLL)) as f:
            for z in f:
                try:
                    aus.append(json.loads(z))
                except ValueError:
                    pass
    except OSError:
        pass
    return aus


def urteile_lesen(data_dir, pass_key):
    """Nur die URTEILS-Zeilen eines Passes (Alt-Zeilen ohne `art` zaehlen als
    Urteil — Rueckwaerts-Vertrag)."""
    return [z for z in protokoll_lesen(data_dir, pass_key)
            if z.get("art", ART_URTEIL) == ART_URTEIL]


def lauf_lesen(data_dir, pass_key):
    """Was auf diesem Pass GERADE passiert bzw. zuletzt passiert ist (V4b):

      schritte  die Erzaehl-Zeilen des JUENGSTEN Laufs, in Reihenfolge
      urteil    das Urteil dieses Laufs — None, solange er noch laeuft
      laeuft    True, wenn es Schritte ohne zugehoeriges Urteil gibt

    "laeuft" haengt damit am PROTOKOLL, nicht am Prozess-Zustand: nach einem
    Dienst-Neustart mitten im Lauf steht hier ehrlich der letzte Stand, statt
    dass die Seite eine Zuversicht behauptet, die niemand mehr hat."""
    zeilen = protokoll_lesen(data_dir, pass_key)
    urteile = [z for z in zeilen if z.get("art", ART_URTEIL) == ART_URTEIL]
    schritte = [z for z in zeilen if z.get("art") == ART_SCHRITT]
    letztes = urteile[-1] if urteile else None
    if not schritte:
        return {"schritte": [], "urteil": letztes, "laeuft": False,
                "lauf": (letztes or {}).get("lauf")}
    juengster = schritte[-1].get("lauf")
    aktuell = [z for z in schritte if z.get("lauf") == juengster]
    fertig = letztes if (letztes or {}).get("lauf") == juengster else None
    # Alt-Urteile ohne `lauf`-Feld (Zeilen aus .158) gehoeren zu keinem
    # Schritt-Lauf; sie bleiben sichtbar, solange kein neuer Lauf laeuft.
    if fertig is None and letztes and not (letztes or {}).get("lauf") \
            and schritte[-1]["ts"] <= (letztes.get("ts") or 0):
        fertig = letztes
    return {"schritte": aktuell, "urteil": fertig, "laeuft": fertig is None,
            "lauf": juengster}


# Der Abbruch-Grund steht an EINER Stelle: der Waisen-Abschluss beim Start, die
# defensive Zweitsicherung im Dienst und die Anzeige lesen alle hier (und die
# Hand-Reparatur vom 09.08. hat denselben Wortlaut, damit alte und neue Zeilen
# gleich aussehen).
ABBRUCH_GRUND = ("the service was restarted while this run was going — it did "
                 "not finish")


def waise(data_dir, pass_key):
    """Ist das Protokoll dieses Durchgangs eine WAISE — also ein Lauf ohne
    Abschluss-Zeile? Rueckgabe: die Lauf-ID der Waise oder None.

    Geprueft wird mit derselben Funktion, aus der die Anzeige ihr "laeuft"
    zieht (`lauf_lesen`). Eine zweite, eigene Regel waere genau die Falle: dann
    koennte die Anzeige "laeuft" sagen und die Reparatur "ist keine Waise"."""
    stand = lauf_lesen(data_dir, pass_key)
    return stand.get("lauf") if stand.get("laeuft") else None


def waise_schliessen(data_dir, pass_key, jetzt=None):
    """Eine Waise mit GENAU EINER Abbruch-Urteil-Zeile schliessen. Rueckgabe:
    die geschriebene Zeile oder None (keine Waise).

    Form wie ein normales Urteil, damit die Anzeige nichts Neues lernen muss —
    plus `abgebrochen: True`, damit sie den Fall als eigenen Zustand zeigen
    kann statt als Fehlschlag."""
    lauf = waise(data_dir, pass_key)
    if not lauf:
        return None
    zeile = {"ts": round(time.time() if jetzt is None else jetzt, 1),
             "pass_key": str(pass_key), "lauf": lauf, "art": ART_URTEIL,
             "manuell": False, "person": None, "grund": ABBRUCH_GRUND,
             "abgebrochen": True, "bilder": [], "gitter": None, "runden": [],
             "reihenfolge": [], "reihenfolge_quelle": "", "voten": 0,
             "anfragen": 0, "dauer_s": None, "sammlung": None, "offen": [],
             "galerien": []}
    protokoll_schreiben(data_dir, pass_key, zeile)
    return zeile


def waisen_schliessen(data_dir, lebt=None):
    """Alle verwaisten Lauf-Protokolle schliessen (.164, Live-Fund 09.08.).

    Der Laufend-Zustand haengt bewusst am PROTOKOLL und nicht am Prozess
    (.159): nach einem Dienst-Neustart soll die Seite den letzten ehrlichen
    Stand zeigen statt eine Zuversicht, die niemand mehr hat. Der Preis dafuer
    war ein toter Winkel — stirbt der Dienst MITTEN im Lauf, fehlt die
    Abschluss-Zeile fuer immer, die Seite zeigt den Lauf ewig als laufend und
    der Start-Knopf bleibt gesperrt. Real passiert am 09.08. (Neustart waehrend
    Runde 2); der User war blockiert und das Protokoll musste von Hand
    geschlossen werden.

    `lebt(pass_key) -> bool` ist die defensive Zweitsicherung: im laufenden
    Dienst darf ein Protokoll nur dann als Waise gelten, wenn zu ihm KEIN
    lebender Lauf gehoert. Beim Start gibt es keine Laeufe, dort bleibt der
    Parameter leer.

    Rueckgabe: Liste der geschlossenen pass_keys."""
    try:
        ordner = sorted(os.listdir(_plv.kontrolle_dir(data_dir)))
    except OSError:
        return []
    aus = []
    for pk in ordner:
        if lebt is not None and lebt(pk):
            continue
        if waise_schliessen(data_dir, pk):
            aus.append(pk)
    return aus


def laufliste(data_dir, pass_key, grenze=12):
    """Die bisherigen Laeufe EINES Durchgangs, neueste zuerst (.164).

    Zweck (User 09.08.): "ich kann den Testlauf nutzen, um mich an meine
    optimale Frameanzahl ranzutesten" — dafuer muss man Laeufe mit
    verschiedenen Zellenzahlen und Bestaetigungs-Zahlen NEBENEINANDER sehen,
    nicht nur den letzten.

    Gelesen wird NUR das bestehende Protokoll dieses Passes; es entsteht keine
    zweite Ablage, und der bestehende Verfall (der Kontroll-Speicher-Trim)
    raeumt die Liste automatisch mit. Alt-Zeilen ohne die .164-Felder fehlen
    nicht, sie sagen `None` — geraten wird nichts.

    Je Lauf: ts · manuell · zellen (gewuenscht/wirksam) · voten-Regel ·
    Backend (schon maskiert) · Urteil oder Grund · Voten x/y · offene Paare ·
    Anfragen · Dauer."""
    aus = []
    for z in urteile_lesen(data_dir, pass_key):
        s = z.get("sammlung") or {}
        r = z.get("regeln_lauf") or {}
        g = z.get("gitter") or {}
        aus.append({
            "ts": z.get("ts"),
            "lauf": z.get("lauf"),
            "manuell": bool(z.get("manuell")),
            "zellen": g.get("zellen"),
            "zellen_gewollt": r.get("bilder_je_pass"),
            "min_voten": r.get("min_voten"),
            "min_voten_wirksam": (r.get("min_voten_wirksam")
                                  if r.get("min_voten_wirksam") is not None
                                  else s.get("min_voten_wirksam")),
            "backend": z.get("backend") or "",
            "person": z.get("person"),
            "grund": z.get("grund") or s.get("grund") or "",
            "voten": s.get("voten"),
            "vergleiche": s.get("bilder"),
            "offen": len(z.get("offen") or []),
            "anfragen": z.get("anfragen"),
            "dauer_s": z.get("dauer_s"),
            "abgebrochen": bool(z.get("abgebrochen")),
            # None bei Alt-Zeilen: vor .165 gab es den Schalter nicht, und
            # "True" waere hier eine Behauptung ueber einen Lauf, der die Frage
            # gar nicht kannte.
            "doppellauf": (r.get("doppellauf") if r.get("doppellauf") is not None
                           else z.get("doppellauf")),
        })
    aus.reverse()                       # neueste zuerst
    return aus[:max(1, int(grenze))]


def protokoll_karte(data_dir, max_passe=80):
    """pass_key -> JUENGSTES URTEIL. Das liest die Ereignis-Karte (§7:
    Zusatz-Info auf der Karte, bei Aufruf gerendert) — sie rechnet nichts nach
    und startet nichts. Erzaehl-Schritte gehoeren NICHT auf die Karte: dort
    steht das Ergebnis, nicht der Weg dorthin."""
    karte = {}
    try:
        ordner = sorted(os.listdir(_plv.kontrolle_dir(data_dir)), reverse=True)
    except OSError:
        return karte
    for pk in ordner[:max_passe]:
        zeilen = urteile_lesen(data_dir, pk)
        if zeilen:
            karte[pk] = zeilen[-1]
    return karte


# --------------------------------------------------- Single-Flight-Guard (§7)
class Einfachlauf:
    """EIN Lauf gleichzeitig, Warteschlange gedeckelt auf 1 wartend, Rest
    verworfen UND gezaehlt (§7) — Muster `_sammel_laeuft`/`_sammel_nachhol`.

    Grund: der gemessene lokale Server laeuft mit `--parallel 1`; zwei
    gleichzeitige Laeufe wuerden sich dort gegenseitig ausbremsen und den
    Deckel doppelt verbrauchen. Reine Zustandslogik ohne Threads und ohne
    Zeit — deshalb ohne laufenden Dienst pruefbar (der Dienst legt nur einen
    Lock und einen Thread darum)."""

    def __init__(self):
        self.laeuft = None
        self.wartend = None
        self.verworfen = 0

    def annehmen(self, key):
        """-> "starten" | "wartet" | "verworfen"."""
        key = str(key)
        if self.laeuft is None:
            self.laeuft = key
            return "starten"
        if key == self.laeuft or key == self.wartend:
            # Derselbe Durchgang noch einmal (zweiter Anstoss waehrend des
            # Laufs): es gaebe nichts Neues zu urteilen.
            self.verworfen += 1
            return "verworfen"
        if self.wartend is None:
            self.wartend = key
            return "wartet"
        self.verworfen += 1
        return "verworfen"

    def fertig(self):
        """Lauf beendet -> der wartende Schluessel wird der neue laufende."""
        self.laeuft, self.wartend = self.wartend, None
        return self.laeuft


# ------------------------------------------------------------ Der ganze Lauf
def pass_urteilen(data_dir, pass_key, galerien, regeln, anfrage_fn,
                  jetzt=None, manuell=False, einbetten=None, melden=None):
    """EIN Vision-Gesamturteil fuer EINEN Durchgang — die Klammer um alles oben.

    galerien  {person: manifest} — NUR abgenommene und unversehrte Galerien
    regeln    dict(bilder_je_pass, quote, min_voten, anfragen_h, anfragen_tag);
              `bilder_je_pass` sind seit V4c die ZELLEN des Kandidaten-Gitters
    anfrage_fn(teile) -> normiertes Einzel-Urteil (kein HTTP in diesem Modul)
    melden    Erzaehl-Log (V4b); None = der Standard-Melder schreibt geflusht
              ins Lauf-Protokoll. `melden=False` schaltet es ganz ab.

    Der Ablauf seit V4c: Bilder sieben -> EIN Kandidaten-Gitter bauen -> EINE
    Kaskade darueber. Der Durchgang kostet damit zwei Anfragen JE GEPRUEFTEM
    PAAR, nicht mehr zwei je Bild.

    Der Analyse-Lock wird nirgends genommen, nichts blockiert den
    Embedding-Pfad; Fehler werden protokolliert, nie geworfen.

    Rueckgabe: die Protokollzeile (JSON-fest, ohne Geheimnisse)."""
    jetzt = time.time() if jetzt is None else jetzt
    lauf_id = "%.1f" % jetzt
    if melden is None:
        melden = melder(data_dir, pass_key, lauf_id)
    zeile = {"ts": round(jetzt, 1), "pass_key": str(pass_key), "lauf": lauf_id,
             "art": ART_URTEIL,
             "manuell": bool(manuell), "person": None, "grund": "",
             "bilder": [], "gitter": None, "runden": [], "reihenfolge": [],
             "reihenfolge_quelle": "", "voten": 0, "anfragen": 0,
             "dauer_s": None, "sammlung": None,
             "galerien": sorted(galerien or {})}
    t0 = time.monotonic()
    z = zaehler_lesen(data_dir)
    _sagen(melden, "starting a vision run for this walk-through"
                   + (" (you asked for it)" if manuell else "")
                   + f" — comparing against {len(galerien or {})} approved "
                     "galleries")
    if len(galerien or {}) < GALERIEN_MIN:
        zeile["grund"] = (f"{len(galerien or {})} of {GALERIEN_MIN} approved "
                          "galleries — vision always compares one person "
                          "against another")
        return _abschluss(data_dir, pass_key, zeile, z, jetzt, t0)
    k = kandidaten(data_dir, pass_key, int(regeln.get("bilder_je_pass") or 1),
                   jetzt, regeln.get("sammeln"))
    zeile["kandidaten"] = {"gesamt": k["gesamt"], "geprueft": k["geprueft"],
                           "verworfen": k["verworfen"],
                           "eingestuft": k.get("eingestuft")}
    if not k["bilder"]:
        zeile["grund"] = k["grund"]
        # Maschinenlesbar mit: die Seite entscheidet daran, ob ein erneutes
        # Analysieren dieses Durchgangs ueberhaupt etwas bringen kann.
        zeile["grund_art"] = k.get("grund_art") or ""
        _sagen(melden, f"nothing to judge: {k['grund']}")
        return _abschluss(data_dir, pass_key, zeile, z, jetzt, t0)
    lage = deckel_lage(z, jetzt, regeln.get("anfragen_h") or 0,
                       regeln.get("anfragen_tag") or 0)
    if lage["frei"] < 2:
        z["deckel_pausen"] = int(z.get("deckel_pausen") or 0) + 1
        zeile["grund"] = ("request limit reached — paused until the hour/day "
                          f"window frees up ({lage['stunde']}/h, "
                          f"{lage['tag']}/day)")
        zeile["deckel"] = lage
        _sagen(melden, "pausing: " + zeile["grund"])
        return _abschluss(data_dir, pass_key, zeile, z, jetzt, t0)
    # Gitter EINMAL je Person lesen (dasselbe Bild geht in jede Runde).
    gal = {}
    for name, m in (galerien or {}).items():
        p = os.path.join(_vg.ordner(data_dir, name), (m or {}).get("gitter")
                         or _vg.GITTER)
        if os.path.isfile(p):
            gal[name] = (m, _b64(p))
    if len(gal) < GALERIEN_MIN:
        zeile["grund"] = "a gallery grid file is missing — rebuild the gallery"
        return _abschluss(data_dir, pass_key, zeile, z, jetzt, t0)
    # DAS KANDIDATEN-GITTER (V4c): EIN Bild fuer den ganzen Durchgang, gebaut
    # mit der Galerie-Routine auf der Galerie-Leinwand (keine zweite
    # Gitter-Implementierung, Deckungs-Regel).
    zeile["bilder"] = [{"eid": b["eid"], "datei": b["datei"],
                        "hoehe": b["hoehe"], "guete": b["guete"],
                        "koerper_klasse": b["klasse"],
                        "koerper_score": b["score"]} for b in k["bilder"]]
    kand_b64, kand_m = kandidaten_gitter(k["bilder"])
    if not kand_b64:
        zeile["grund"] = ("the candidate grid could not be built from this "
                          "walk-through's pictures")
        _sagen(melden, "nothing to judge: " + zeile["grund"])
        return _abschluss(data_dir, pass_key, zeile, z, jetzt, t0)
    zeile["gitter"] = kand_m
    # Das gefragte Bild sichtbar machen (User 09.08.): dasselbe JPG, das gleich
    # als base64 in die Anfrage geht, liegt danach im Kontroll-Ordner und wird
    # von der Durchgangs-Seite ueber den vorhandenen Bild-Weg ausgeliefert.
    # Der Name steht in der Zeile, damit die Waisen-Raeumung ihn kennt.
    zeile["gitter_datei"] = gitter_ablegen(data_dir, pass_key, lauf_id,
                                           kand_b64)
    zellen = int(kand_m["zellen"])
    # .164: der Lauf sagt, MIT WELCHEN Regeln er gefahren ist. Beim manuellen
    # Testlauf sind das die Feld-Werte, sonst die Config — der Erzaehl-Log und
    # die Vergleichsliste zeigen das nebeneinander, damit man Laeufe mit
    # verschiedenen Zellenzahlen wirklich vergleichen kann.
    gewuenscht = max(1, int(regeln.get("bilder_je_pass") or 1))
    doppellauf = regeln.get("doppellauf")
    doppellauf = True if doppellauf is None else bool(doppellauf)
    zeile["regeln_lauf"] = {"bilder_je_pass": gewuenscht,
                            "bilder_wirksam": zellen,
                            "min_voten": int(regeln.get("min_voten") or 1),
                            "doppellauf": doppellauf}
    zeile["doppellauf"] = doppellauf
    _sagen(melden,
           f"built the candidate grid from {zellen} of {k['gesamt']} usable "
           "picture(s) of this walk-through (sharpest and largest first) — one "
           "grid for the whole walk, asked as a whole; each compared pair "
           + ("costs two requests" if doppellauf else "costs one request")
           # EHRLICHE KAPPUNG: wer 8 Zellen einstellt und 3 Bilder hat, bekommt
           # 3 — und erfaehrt es, statt sich zu wundern, warum sein Versuch
           # nichts geaendert hat.
           + ("" if zellen >= gewuenscht else
              f" — you asked for {gewuenscht} cells, this walk-through only "
              f"has {k['gesamt']} usable picture(s), so {zellen} were used"),
           zellen=zellen, gewuenscht=gewuenscht, gitter=kand_m["groesse"])
    # Reihenfolge: eigenes Material zuerst, Koerper-Rangfolge nur als HINWEIS
    # (V4c) — der Pfad laeuft ohne sie identisch, nur in anderer Reihenfolge.
    bild_rgb = None
    try:
        import cv2
        im = cv2.imread(k["bilder"][0]["pfad"])
        bild_rgb = None if im is None else im[:, :, ::-1]
    except Exception:
        bild_rgb = None
    ordnung, quelle = ordnung_bauen(
        data_dir, {n: gal[n][0] for n in gal}, bild_rgb, einbetten,
        zuletzt_bestaetigt(data_dir))
    zeile["reihenfolge"] = [[p, s] for p, s in ordnung]
    zeile["reihenfolge_quelle"] = quelle
    _sagen(melden, f"order of the comparisons: {quelle} — "
                   + ", ".join(p for p, _ in ordnung), quelle=quelle)
    gewollt_voten = max(1, int(regeln.get("min_voten") or 1))
    noetig = min_wirksam(gewollt_voten, len(ordnung) - 1)
    zeile["regeln_lauf"]["min_voten_wirksam"] = noetig
    _sagen(melden,
           f"this run needs {noetig} consistent comparison(s) to reach a "
           "verdict"
           # Dieselbe Ehrlichkeit wie bei den Zellen: mehr Bestaetigungen als
           # es Herausforderer gibt, kann niemand verlangen.
           + ("" if noetig >= gewollt_voten else
              f" — you asked for {gewollt_voten}, but {len(ordnung)} approved "
              f"galleries allow at most {len(ordnung) - 1} comparison(s)"),
           voten_gewollt=gewollt_voten, voten_noetig=noetig)
    if not doppellauf:
        # Der Ausweis steht VOR den Runden im Log, nicht irgendwo dazwischen:
        # wer die Zeilen liest, soll von Anfang an wissen, wie gewertet wird.
        _sagen(melden,
               "swap check is OFF for this run: each pair is asked once "
               "instead of twice. That halves the requests and gives up the "
               "test for position bias — the answer is taken as it comes.",
               doppellauf=False)
    u, runden, n = kaskade(gal, ordnung, kand_b64, anfrage_fn, lage["frei"],
                           melden, kandidat_zellen=zellen,
                           min_bestaetigungen=noetig, doppellauf=doppellauf)
    zeile["anfragen"] = n
    zeile["runden"] = runden
    zeile["wahl"] = u["wahl"]
    zeile["konsistent"] = u["konsistent"]
    zeile["kein_votum"] = u["kein_votum"]
    zeile["token"] = u["token"]
    zeile["custom_prompt"] = u["custom_prompt"]
    # .164: das Backend (schon maskiert — Kachel-Label bzw. "local"/"cloud: host")
    # wandert in die Zeile, damit die Vergleichsliste je Lauf zeigen kann, WOMIT
    # gefahren wurde. Ein Geheimnis ist das keines (§9: die Maskierung passiert im
    # Adapter, nicht hier).
    zeile["backend"] = u.get("backend") or ""
    zeile["quelle"] = u.get("quelle") or ""
    # .162: die unentschiedenen Paare fahren im Urteils-Objekt mit — die
    # Anzeige soll sie nennen koennen, ohne die Runden noch einmal zu deuten.
    zeile["offen"] = u.get("offen") or []
    z = anfragen_buchen(z, jetzt, n)
    z = _zaehler_fortschreiben(z, u, runden)
    if u["grund"] == "deckel":
        zeile["grund"] = "request limit reached during this pass"
    s = sammeln(urteile_aus_runden(runden), float(regeln.get("quote") or 1.0),
                int(regeln.get("min_voten") or 1), len(ordnung) - 1)
    zeile["sammlung"] = s
    zeile["person"] = s["person"]
    zeile["voten"] = s["voten"]
    if not s["person"] and not zeile["grund"]:
        zeile["grund"] = s["grund"] or _vis.grund_text(u.get("grund"))
    if s["person"]:
        z["urteile"] = int(z.get("urteile") or 0) + 1
        # .162: ein Urteil MIT offenen Paaren sagt beides in EINEM Satz. Sonst
        # laese man "verdict: X" und wuesste nicht, dass daneben ein Vergleich
        # gar nichts entschieden hat.
        _offen = zeile.get("offen") or []
        _sagen(melden,
               f"verdict: {s['person']} — {s['voten']} consistent comparison(s) "
               f"of this walk-through's grid, all pointing the same way"
               + (f" — but {offen_satz(_offen)}" if _offen else ""),
               person=s["person"], fertig=True, enthaltungen=len(_offen))
    else:
        _offen = zeile.get("offen") or []
        _sagen(melden, "no verdict — " + (zeile["grund"] or s["grund"])
               + (f" — {offen_satz(_offen)}" if _offen else ""),
               fertig=True, enthaltungen=len(_offen))
    return _abschluss(data_dir, pass_key, zeile, z, jetzt, t0)


def _zaehler_fortschreiben(z, u, runden=None):
    """Die getrennt gefuehrten Zaehler (§8). Getrennt, weil "kein Votum" kein
    Randfall ist: wer nur Urteile und Fehler zeigt, meldet eine Trefferquote,
    die den Anteil unbrauchbarer Durchgaenge verschweigt.

    Seit .162 kommen die Enthaltungen aus den RUNDEN, nicht mehr aus dem
    Gesamt-Urteil: die Kaskade bricht bei einer Enthaltung nicht mehr ab, also
    kann ein Lauf mehrere haben — und mit dem alten Griff auf `u["grund"]`
    waeren sie ab dem zweiten Paar stillschweigend verschwunden. Ohne `runden`
    bleibt es beim alten Weg (Alt-Aufrufer)."""
    if runden is not None:
        for r in runden:
            if not r.get("kein_votum"):
                continue
            if r.get("grund") == "neither":
                z["kein_votum_neither"] = int(z.get("kein_votum_neither") or 0) + 1
            elif r.get("grund") == "tausch_widerspruch":
                z["kein_votum_widerspruch"] = \
                    int(z.get("kein_votum_widerspruch") or 0) + 1
        g = u.get("grund")
        if g == "timeout":
            z["timeouts"] = int(z.get("timeouts") or 0) + 1
        elif g == "fehler":
            z["fehler"] = int(z.get("fehler") or 0) + 1
        return z
    g = u.get("grund")
    if g == "neither":
        z["kein_votum_neither"] = int(z.get("kein_votum_neither") or 0) + 1
    elif g == "tausch_widerspruch":
        z["kein_votum_widerspruch"] = int(z.get("kein_votum_widerspruch") or 0) + 1
    elif g == "timeout":
        z["timeouts"] = int(z.get("timeouts") or 0) + 1
    elif g == "fehler":
        z["fehler"] = int(z.get("fehler") or 0) + 1
    return z


def _abschluss(data_dir, pass_key, zeile, z, jetzt, t0):
    zeile["dauer_s"] = round(time.monotonic() - t0, 1)
    z["letzter_lauf"] = round(float(jetzt), 1)
    if zeile.get("grund"):
        z["letzter_fehler"] = str(zeile["grund"])[:160]
    z, stoerung = ausfall_buchen(z, bool(zeile.get("person")), jetzt)
    zeile["ausfall_serie"] = z["ausfall_serie"]
    zeile["stoerung"] = bool(stoerung)
    try:
        zaehler_schreiben(data_dir, z)
    except OSError:
        pass
    protokoll_schreiben(data_dir, pass_key, zeile)
    return zeile


# ------------------------------------------------- Drei-Wege-Sicht (§4, Test)
def _event_scores(event_dir):
    """`persons[..]["max"]` aus der results.jsonl EINES Events.

    Genau die Zahl, aus der die Gesichts-Spalte ihr "best" bildet (in der Akte
    heisst sie `ours`) — deshalb wird sie hier gelesen und nicht aus dem
    Dateinamen des Crops geraten. Mehrere Zeilen (ein Label je Clip) werden zum
    Maximum je Person zusammengefasst."""
    werte = {}
    try:
        with open(os.path.join(event_dir, "results.jsonl")) as f:
            for zeile in f:
                try:
                    d = json.loads(zeile)
                except Exception:
                    continue
                for p, w in (d.get("persons") or {}).items():
                    try:
                        v = float((w or {}).get("max"))
                    except (TypeError, ValueError):
                        continue
                    if p not in werte or v > werte[p]:
                        werte[p] = v
    except OSError:
        pass
    return werte


def gesichtsbilder(data_dir, szenario):
    """Die abgelegten GESICHTS-Crops eines Durchgangs, je Event eine Kachel.

    Der Fall dahinter (User 10.08.): die Gesichts-Spalte des Erkennungstests
    zeigte nur Text ("… 4 event(s) · best 0.60 · 2 event(s) with a face that was
    not matched"), waehrend Person und Vision daneben ihre Bilder zeigten. Man
    sah also nicht, WELCHE Gesichter des Durchgangs erkannt wurden und welche
    nicht — genau die Sicht, um die es beim Nachvollziehen geht.

    Genommen wird ausschliesslich, was die Analyse damals ohnehin geschrieben
    hat: die Crops im Event-Ordner (`<label>_show_<Person>_NN…` bzw.
    `_best_<Person>_NN…` fuer eine gestuetzte Person, `<label>_enroll_FREMD_…`
    fuer ein Gesicht ohne Namen). KEIN neuer Speicher, kein Clip wird geoeffnet,
    kein Frame dekodiert, nichts gegen Frigate gefragt — nur ein
    Verzeichnis-Listing je Event des Durchgangs. Fehlt der Ordner (Retention),
    entsteht schlicht keine Kachel; die Zahlen der Spalte kommen weiter aus der
    Akte und bleiben davon unberuehrt.

    Ausgeliefert werden die Bilder ueber den BESTEHENDEN Weg
    `/events/<eid>/<datei>` — dieselbe Route, die die Heute-Seite fuer ihre
    Avatare nutzt (`_crop_url`). Hier steht nur, welche Datei zu welchem Urteil
    gehoert.

    Rueckgabe (zeitlich sortiert, Szenario-Prinzip: der ganze Durchgang):
    `{"eid", "kamera", "t", "datei", "person"|None, "score"|None}` — `person`
    ist None, wenn das Event keinen bestaetigten Namen trug."""
    s = szenario or {}
    kacheln = []
    for ev in s.get("evs") or []:
        eid = str(ev.get("eid") or "")
        if not eid:
            continue
        edir = os.path.join(data_dir, "events", eid.replace("/", "_"))
        try:
            dateien = sorted(d for d in os.listdir(edir) if d.endswith(".jpg"))
        except OSError:
            continue
        scores = _event_scores(edir)
        rumpf = {"eid": eid, "kamera": str(ev.get("cam") or ""), "t": ev.get("t")}
        conf = [str(p) for p in (ev.get("conf") or [])]
        for p in conf:
            # Reihenfolge wie im Push-Bild: `_show_` (Gesicht mit Umfeld) vor
            # dem engen `_best_`-Ausschnitt.
            datei = (next((d for d in dateien if f"_show_{p}_" in d), None)
                     or next((d for d in dateien if f"_best_{p}_NN" in d), None))
            if datei:
                kacheln.append({**rumpf, "datei": datei, "person": p,
                                "score": scores.get(p)})
        if conf:
            continue
        # OHNE bestaetigten Namen: das Gesicht, das die Analyse trotzdem
        # aufgehoben hat — erst der Enrollment-Crop des Fremden, sonst der
        # staerkste `_best_`-Ausschnitt (er lag ueber der Bild-Schwelle, aber
        # unter der Bestaetigung). Der Score ist der beste, den irgendeine
        # Referenz auf diesem Event erreicht hat.
        datei = next((d for d in dateien if "_enroll_FREMD_" in d), None)
        if datei is None:
            uebrig = [d for d in dateien if "_best_" in d and "_NN" in d]
            datei = sorted(uebrig)[0] if uebrig else None
        if datei:
            bester = max(scores.values(), default=None)
            kacheln.append({**rumpf, "datei": datei, "person": None,
                            "score": bester})
    kacheln.sort(key=lambda b: (b.get("t") or 0, b.get("datei") or ""))
    return kacheln


def dreiwege(szenario, kontroll_zeilen, treffer, vision_lauf, konfiguriert,
             gesichts_bilder=None):
    """Die drei Traegerwege eines Durchgangs NEBENEINANDER (User 08.08.:
    "optimal waere eine allgemeine Erkennung durch alle drei").

    Gesicht und Koerper kommen aus den BUECHERN des Durchgangs — hier wird
    nichts neu gerechnet und kein Bild angefasst. Vision kommt aus dem
    Protokoll des ECHTEN Urteilspfads; ohne Konfiguration sagt die Spalte das
    ehrlich, statt eine leere Tabelle zu zeigen.

    Reine Aufbereitung, keine Datei- und keine Netz-Zugriffe. `gesichts_bilder`
    ist die fertige Kachel-Liste aus `gesichtsbilder()` — DORT wird gelesen,
    hier nur durchgereicht, damit dieser Kontrakt gilt."""
    s = szenario or {}
    gesicht = {"personen": [], "unbekannt": s.get("unbek") or 0,
               "events": s.get("n") or 0,
               "kameras": len(s.get("kams") or {}),
               "bilder": list(gesichts_bilder or [])}
    for name, d in sorted((s.get("pers") or {}).items()):
        if d.get("quelle") == "koerper":
            continue                    # das ist die Koerper-Spalte, nicht diese
        gesicht["personen"].append({"person": name, "events": d.get("count"),
                                    "best": d.get("best")})
    koerper = {"bilder": [], "personen": {}, "treffer": []}
    for e in kontroll_zeilen or []:
        koerper["bilder"].append({
            "eid": e.get("eid"), "datei": e.get("datei"),
            "klasse": e.get("klasse"), "score": e.get("score"),
            "schwelle": e.get("schwelle"), "quelle": e.get("quelle"),
            "bild": bool(e.get("bild")), "ts": e.get("ts")})
        if e.get("klasse") and e.get("klasse") != "FREMD":
            koerper["personen"][e["klasse"]] = \
                koerper["personen"].get(e["klasse"], 0) + 1
    for e in s.get("evs") or []:
        t = (treffer or {}).get(e.get("eid"))
        if t and t.get("person"):
            koerper["treffer"].append({"eid": e.get("eid"),
                                       "person": t["person"],
                                       "score": t.get("score"),
                                       "feuer": bool(t.get("feuer"))})
    # `vision_lauf` ist der Stand aus lauf_lesen() — Schritte, Urteil, laeuft.
    # Eine blosse Urteils-Zeile wird ebenfalls akzeptiert (Alt-Aufrufer und die
    # Karten-Sicht, die nur das Ergebnis kennt).
    v = dict(vision_lauf or {})
    if v and "urteil" not in v and "schritte" not in v:
        v = {"urteil": vision_lauf, "schritte": [], "laeuft": False}
    vision = {"konfiguriert": bool(konfiguriert),
              "zeile": v.get("urteil") or None,
              "schritte": list(v.get("schritte") or []),
              "laeuft": bool(v.get("laeuft"))}
    return {"gesicht": gesicht, "koerper": koerper, "vision": vision}
