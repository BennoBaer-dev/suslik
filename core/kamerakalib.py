"""core/kamerakalib — DIE eine Auslegung der Kamera-Kalibrierwerte
(User-Entscheid 31.08. "EIN Menuepunkt Kamera-Kalibrierung", Drei-Latten-Semantik).

WARUM JE KAMERA: die Gueteskalen sind kameraabhaengig. Gemessen am 31.08. an
Feldmaterial: Median fiqa_t 0,181 auf der einen Kamera gegen 0,073 auf der
anderen. Eine gemeinsame Zahl ist fuer die eine grosszuegig und fuer die andere
ein Kahlschlag — globale Latten sind damit konzeptionell ueberholt.

DREI LATTEN, DREI ZWECKE (die Semantik, gegen die dieses Modul geschrieben ist):
  (1) ERKENNEN bleibt UNGESIEBT. Wer vor dem Namens-Voting siebt, verliert
      Bestaetigungen (Messung 31.08.: ohne Siebe 41 % mehr). Dieses Modul wird
      auf dem Urteils-Pfad NICHT gefragt und liefert dafuer auch keine Latte.
  (2) ANZEIGE/MELDEN + VORRAT: die Kamera-Kalibrierwerte (det_min, guete_e_min,
      guete_t_min). Sie entscheiden, WELCHES Bild in Meldung/Anzeige geht und
      WAS in den Kalibrier-Vorrat kommt — existierte schon (.383), liegt im
      Guard-Block des Config-Stores und wird hier nur ZUSAMMENGEFASST gelesen.
  (3) KATALOG-AUFNAHME + LERN-SIEB: eine eigene Latte je Kamera
      (katalog_e_min/katalog_t_min, seit .514 zusaetzlich katalog_det_min/
      katalog_pose_min). Sie greift an ALLEN Uebernahme-Stellen in
      den Referenz-Katalog und ist der Grund, warum es dieses Modul gibt:
      der Deckungs-Vertrag braucht EINE Funktion (katalog_ok), nicht fuenf
      verstreute Vergleiche (QS-Ebenen-Regel K3).
      SEIT .511 ist sie ausdruecklich LIBERAL (Werkswert 0,125/0,125 statt
      0,200/0,400, User-Entscheid 08.09.): aufgenommen wird grosszuegig,
      gesiebt wird DANACH vom Bestands-Pruefer (core/refurteil.py). Das Wort
      "strenger" aus der Fassung von .383 ist damit hinfaellig — die zwei
      Latten beantworten zwei Fragen, sie sind keine Rangfolge.
      SEIT .514 traegt dasselbe Register die Achsen des Hauses und ist
      damit zugleich das QUALITAETS-SIEB DES LERNWEGS (`sieb_latten`/`sieb_ok`
      unten). Der Lernlauf hatte bis .513 einen eigenen Achsen-Satz
      (m_det/m_kante/m_sharp, s_det, vorrat_sharp600) — der ist abgeloest;
      es gibt EIN System und zwei Werte-Saetze (Erkennen / Lernen).
      SEIT .515 sind es SECHS Achsen. Dazugekommen sind (User-Go 10.09.):
      Sensor 5, die FEATURE-NORM (`katalog_norm_min`/`katalog_guete_norm_min`),
      seit .516 werksseitig AN und seit .517 mit dem Grundwert 20
      (core.guete.norm_werk — User-Entscheid 10.09. nach Sichtung am
      Norm-Schieber; im ERKENNEN-Register bleibt sie 0/aus, dort wird die Norm
      nicht gemessen); und Sensor 6, die KANTEN-LATTE in Pixeln
      (`katalog_kante_min`/`katalog_guete_kante_min`), werksseitig 25 px.
      Beide stehen in BEIDEN Registern — im Erkennen-Register als
      `norm_min`/`urteil_norm_min` und `kante_min`/`urteil_kante` (ERK_FELD
      unten). Der globale Rueckfall der Kante ist ausdruecklich der SCHON
      VORHANDENE Schluessel `urteil_kante`: die Zahl, die bis .514 als eine
      Konstante fuer die ganze Anlage im Stimmweg stand, ist damit eine
      Register-Achse geworden — je Kamera einstellbar, im Werkszustand aber
      wertgleich (25 = 25).

ABLAGEORT (bewusst KEIN zweiter): alle Kamera-Werte liegen im schon
vorhandenen Guard-Block `live.guards.<kamera>` des Config-Stores. Damit gibt es
genau EINEN Schreibweg (core.livewache.live_speichern, samt Riegeln und Audit)
und EINE Normalisierung (guards_lesen). Ein Guard-Block ohne `enabled` ist
reine Kalibrierung — eine Kamera braucht keinen Live-Waechter, um kalibriert zu
werden (Etappe 3 speist den Vorrat auch aus dem Event-Weg).

MIGRATIONS-SEMANTIK (Bestandsschutz, ausdruecklich):
  * Die GLOBALEN Werte guete_empfinden_min/guete_t_min (.377) sind mit .516
    ERSATZLOS ENTFALLEN (User 10.09.2026, Sechs-Achsen-Verfassung). Bis .513
    siebten sie den Lernlauf, ab .514 nur noch Gruppen-Flaeche, Sichtung,
    Reihung und Pool-Zulauf — und dort haerter als das Sieb davor: von 1385
    Bildern, die Ernte und Anker-Sieb durchliessen, verwarfen sie 1382
    (.514-Widerleger B1). Alle diese Stellen lesen jetzt DIESES Register.
    Zeilen ohne jede Guete-Messung laufen weiter den Pixel-/Norm-Alt-Weg
    (core.benennung._lattenklasse) — Altbestand verhaelt sich nicht ruecklings
    anders, und nichts stirbt fail-closed.
  * Fuer die ANZEIGE-Latte (2) gilt: Kamera-Wert gesetzt -> er gilt; nicht
    gesetzt -> KEINE Latte (None), exakt wie vor diesem Bau. Der globale Wert
    faellt hier bewusst NICHT ein: auf dem Live-Weg galt nie eine globale
    Latte, und die Messung 31.08. zeigt, dass die Werks-Latte an Fernmaterial
    das gesamte Namensmaterial verwirft (Guete-Werkslatte -> 0 Bestaetigungen).
    Was der globale Wert dort waere, ist deshalb als HINWEIS auf der Seite
    sichtbar, nicht als stille Wirkung.
  * Fuer die KATALOG-Latte (3) gilt: Kamera-Wert -> global (katalog_guete_*)
    -> nicht gesetzt = keine Latte. Ungemessene Bilder (fiqa_t/empf fehlen,
    Alt-Bestand oder Alt-Image ohne die Guete-Modelle) urteilen IMMER alt:
    eine Latte ohne Messgrundlage waere ein stiller Verlust (dieselbe Haltung
    wie core.benennung.guete_weg_aktiv).
  * Vorhandene Referenzen werden NIE rueckwirkend entfernt. Die Latte
    entscheidet ausschliesslich ueber NEUE Aufnahmen.

Dieses Modul rechnet nicht und misst nicht — es LIEST Werte und beantwortet
genau eine Frage (katalog_ok). Zahlen kommen aus der Config bzw. aus
core.guete.KATALOG_STARTWERTE, nie von hier (Haus-Regel, Muster
norm_latte/REF_LATTE).
"""

# ---------------------------------------------------------------- Ablageort
# Die zwei Guard-Felder der Katalog-Latte. Sie stehen zusaetzlich in
# core.livewache.GUARD_USER_FELDER (dem Deckungs-Vertrag des Guard-Blocks) —
# hier als Namens-Quelle fuer Leser und Schreiber dieses Moduls, damit der
# Feldname nicht an vier Stellen als Literal steht.
KAT_FELDER = ("katalog_e_min", "katalog_t_min",
              # .514 (Etappe 3 „ein Sieb", User 09.09.2026: „ein system!!!!
              # nur unterschiedliche werte je normalmodus und ernte bzw.
              # lernmodus"): die zwei FEHLENDEN Achsen des Registers. Das
              # Urteil des Hauses laeuft auf VIER Achsen (det, Empfinden,
              # Erkennbarkeit, Kopfpose) — der Erkennungs-Weg hatte alle vier,
              # das Katalog-/Lern-Register nur zwei, und die Ernte siebte
              # statt dessen mit einem eigenen Satz (m_det/m_kante/m_sharp,
              # s_det, vorrat_sharp600). Seit .514 sieben beide Wege mit
              # DERSELBEN Mechanik, nur mit anderen Werten.
              "katalog_det_min", "katalog_pose_min",
              # .515 (Sensor 5, User-Go 10.09.2026): die FEATURE-NORM als
              # fuenfte Achse desselben Registers. ACHTUNG, eine Namens-
              # Nachbarschaft, die niemand verwechseln darf: der GLOBALE
              # Config-Schluessel `katalog_norm_min` (15-35) ist etwas
              # ANDERES — er ist die Angebots-Linie des Lernvorrats
              # (core.benennung.NORM_LATTE["gut"]) und bleibt unangetastet.
              # DIESES Feld hier lebt im Guard-Block einer Kamera und ist die
              # Sieb-Achse; sein globaler Rueckfall heisst deshalb
              # `katalog_guete_norm_min` (ACHSE_GLOBAL unten), genau nach dem
              # Muster der vier Geschwister.
              "katalog_norm_min",
              # .515 (Sensor 6, User-Entscheid 10.09.2026): die KANTEN-LATTE
              # in Pixeln als sechste Achse. Sie ist die einzige Achse, deren
              # Messwert nichts kostet (die Boxgroesse liegt mit der Detektion
              # vor) — deshalb steht sie in der Kostenordnung ganz vorne.
              "katalog_kante_min")

# Die Achsen des Registers als EINE Aufzaehlung — Reihenfolge = die des
# Urteils und zugleich die KOSTENORDNUNG der Messung (billig zuerst, teuer
# zuletzt; dieselbe Reihenfolge, die der User am 03.09. fuer den
# Erkennungs-Weg festgelegt hat: „erst die Grundwert-Boeden, danach die
# Pose"). .515 haengt die Feature-Norm HINTER die Pose: sie ist die teuerste
# Messung des Hauses (eigene adaface-Session, core.face_audit.NormMass), und
# wer an einer billigen Achse faellt, soll sie nie bezahlen.
# .515 setzt „k" (Kante) direkt hinter „det": beide Messwerte liegen mit der
# Detektion schon vor und kosten nichts, waehrend e/t zwei kleine Netze, p
# einen RTMPose-Lauf und n eine adaface-Inferenz brauchen. Die relative
# Ordnung der vier alten Achsen bleibt dabei unveraendert — ein Fund, der die
# Kante besteht, bekommt genau denselben Grund gemeldet wie vor .515.
SIEB_ACHSEN = ("det", "k", "e", "t", "p", "n")

# .518 (Norm-Nachmess-Job, User-Go 10.09.2026 „so bauen"): WO eine Achse siebt.
# Fluss des Users: „Ernter startet -> Worker parallel mit den fuenf leichten Achsen
# -> DANN die Normierung als EIN gebuendelter Schritt -> dann die Abarbeitung."
#
# Der Grund ist der PLATZ, nicht die Zahl: die Norm-Achse braucht eine eigene
# adaface-Session (core.face_audit.NormMass), deren Bauspitze mit 2700 MB
# gemessen ist (worker._NORMMASS_BAUSPITZE_MB). Solange sie IM Ernte-Job lag,
# war jeder der K parallelen Ernte-Plaetze potenziell ein 2,7-GB-Platz — die
# Plaetze waren also nicht mehr gleich schwer, und ein Lauf mit vier Abholern
# konnte vier solche Sessions nebeneinander bauen wollen. Seit .518 sieben im
# Ernte-Job nur die FUENF leichten Achsen; die Norm misst danach EIN
# gebuendelter Job mit EINER Session (core/normlauf.py).
#
# EINE Quelle, abgeleitet statt danebengeschrieben (K3): wer eine weitere
# teure Achse in den Nachmess-Schritt gibt, traegt sie hier ein — ERNTE_ACHSEN
# folgt automatisch, und die Reihenfolge (Kostenordnung) bleibt die von
# SIEB_ACHSEN.
NACHMESS_ACHSEN = ("n",)
ERNTE_ACHSEN = tuple(a for a in SIEB_ACHSEN if a not in NACHMESS_ACHSEN)

# Guard-Feldname je Achse (EINE Zuordnung statt Streu-Literale).
ACHSE_FELD = {"e": "katalog_e_min", "t": "katalog_t_min",
              "det": "katalog_det_min", "p": "katalog_pose_min",
              "n": "katalog_norm_min", "k": "katalog_kante_min"}

# Globaler Config-Schluessel je Achse (der Rueckfall unter dem Kamera-Wert).
ACHSE_GLOBAL = {"e": "katalog_guete_e_min", "t": "katalog_guete_t_min",
                "det": "katalog_guete_det_min", "p": "katalog_guete_pose_min",
                "n": "katalog_guete_norm_min", "k": "katalog_guete_kante_min"}

# ---------------------------------------------------- Das ERKENNEN-Register
# .515: dieselbe Mechanik, zweiter Werte-Satz. Das Erkennen-Register traegt
# seine VIER alten Achsen weiter dort, wo sie gewachsen sind (det ueber das
# analyze-Argument --det-thresh, Empfinden/Erkennbarkeit ueber
# core.guete.stimm_latten, Pose ueber --urteil-pose); sie stehen hier
# ausdruecklich NICHT, weil ein Umhaengen eine Verhaltensaenderung waere und
# nicht zu diesem Zug gehoert. Was hier steht, sind die zwei NEUEN Achsen —
# und sie loesen nach derselben Rangfolge auf wie ihre Katalog-Geschwister
# (Kamera -> global -> Werks-Boden, ungemischt, `erk_latten` unten).
# Bei der KANTE ist der globale Rueckfall ausdruecklich der SCHON VORHANDENE
# Schluessel `urteil_kante` (.400). Das ist der Kern von Sensor 6: der Wert,
# der bisher als eine Zahl fuer die ganze Anlage im Stimmweg stand, wird zur
# Register-Achse — je Kamera ueberschreibbar, im Werkszustand aber
# WERTGLEICH (beide Werks-Vorgaben sind core.guete.KANTE_WERK = 25).
ERK_FELD = {"n": "norm_min", "k": "kante_min"}
ERK_GLOBAL = {"n": "urteil_norm_min", "k": "urteil_kante"}
# Reihenfolge aus DER einen Quelle ableiten statt daneben schreiben (K3).
ERK_ACHSEN = tuple(a for a in SIEB_ACHSEN if a in ERK_FELD)


# Die drei Anzeige-/Vorrats-Felder (Latte 2) — schon vorhanden, hier nur
# benannt, damit die Seite sie ueber DIESE Quelle liest.
ANZ_FELDER = ("det_min", "guete_e_min", "guete_t_min")

# ---------------------------------------------------------------- Inventar
# DIE Liste der Stellen, an denen ein Bild in den Referenz-Katalog wandert
# ("modul:funktion"). Sie ist der Deckungs-Vertrag der Katalog-Latte: jede
# dieser Funktionen MUSS katalog_ok() fragen, und eine neue Uebernahme-Stelle
# muss hier eingetragen werden. Die Gate-Stufe "Katalog-Latte" prueft beides —
# Eintrag ohne Aufruf ist rot, und ein Fund am refs_meta-Schreibweg, der weder
# hier noch in AUSNAHMEN steht, ebenfalls (K3: erreicht die Erweiterung ALLE
# Stellen?).
UEBERNAHME_STELLEN = (
    "core.uebernahme:plan_bauen",       # Lernlauf-Anker -> Katalog (Mitglieder
    #                                     tragen kamera + fiqa_t/empf; der Plan
    #                                     ist die Stelle, an der ein Bild
    #                                     ausgesondert werden kann, BEVOR
    #                                     uebernehmen() Dateien anfasst)
    "anlernen:vorschlag_aufnehmen",     # Bestands-Vorschlag -> Katalog
    "anlernen:vorrat_aufnehmen",        # Vorrats-Angebot -> Katalog
    "anlernen:passernte_aufnehmen",     # .521 Mini-Ernte-Lauf am Pass-Knopf ->
    #                                     Katalog. Die Latte beisst hier per
    #                                     Konstruktion nicht (das Register hat
    #                                     dieselben zwei Werte schon gesiebt) —
    #                                     gefragt wird sie trotzdem: der
    #                                     Deckungs-Vertrag kennt keine Ausnahme
    #                                     „hat gerade dieselbe Zahl".
    "verifyd:enroll_entscheiden",       # Enrollment-Kandidat -> Katalog
)

# Schreibwege auf refs_meta.jsonl, die KEINE Uebernahme sind (Begruendung je
# Zeile — eine Ausnahme ohne Grund waere ein Schlupfloch):
AUSNAHMEN = {
    "anlernen:benenne":
        "Hand-Auswahl je Bild (Today-Karte, Cluster, Unbekannt-Benennung, "
        "Lern-Bruecke): der Nutzer hat jedes Gesicht einzeln angekreuzt — "
        "User-Entscheid 01.09. ('Wenn ich sage hinzufuegen, dann "
        "hinzufuegen'): der bewusste Klick ist die Pruefung, Aussieben "
        "danach macht der Quality-Check. Von .385 bis .396 siebte auch "
        "dieser Weg — bewusst zurueckgebaut, die Latte gilt weiter auf den "
        "Automatik-Wegen",
    "anlernen:entferne_referenz":
        "Tombstone: entfernt eine Referenz, nimmt keine auf",
    "anlernen:_ref_datei_weg":
        "Tombstone-Griff der Stufe A (.511): die gemeinsame Datei-Seite hinter "
        "entferne_referenz UND entferne_referenzen — Datei loeschen, Zeile mit "
        "aktiv:false anhaengen. Er nimmt nie eine Referenz auf; die Zeile ist "
        "die Loeschmarke, ohne die sync_refs das in Frigate noch vorhandene "
        "Bild als 'neu' re-importieren wuerde. Gleiche Begruendung wie beim "
        "Aufrufer darueber (Entscheid 08.09.)",
    "verifyd:upload_referenz":
        "Foto-Upload durch den Nutzer: kein Kameramaterial, keine Kamera und "
        "keine Guete-Messung — eine Kamera-Latte hat hier keine Bedeutung "
        "(Haus-Entscheid 'Personen nie per Upload anlernen' betrifft den "
        "Bedienweg, der Upload selbst bleibt als bewusste Handtuer bestehen)",
    "verifyd:do_POST":
        "Lernlauf-Uebernahme: die Zeile wird geschrieben, NACHDEM "
        "core.uebernahme.plan_bauen gesiebt hat — der Filter sitzt dort",
    "sync_refs:meta_append":
        "Journal-Schreiber des Frigate-Abgleichs: haengt Export-/"
        "Wieder-anbieten-Zeilen zu Bildern an, die BEREITS im Katalog liegen — "
        "er nimmt nie eines auf",
}


# ---------------------------------------------------------------- Lesen
def _zahl(wert, lo=0.0, hi=1.0):
    """Eine optionale Latten-Zahl -> float oder None. Unbrauchbares wird zu
    None (= keine Latte), nie zu einem geratenen Wert: eine kaputte Zahl darf
    keine Bilder verwerfen."""
    if wert in (None, ""):
        return None
    try:
        z = float(wert)
    except (TypeError, ValueError):
        return None
    return z if lo <= z <= hi else None


def _achse_hi(achse):
    """Obergrenze EINER Achse fuer die Zahlen-Wache `_zahl`.

    NICHT jede Achse laeuft auf 0..1 — und eine zu enge Obergrenze macht einen
    gesetzten Wert STILL zu None, also zu „keine Latte":
      p  Kopf-Score der Pose-Wache, bis 2 (core.livewache.POSE_MIN_MAX = die
         Spanne des Vorgabewerts `pose_kopf`).
      n  Feature-Norm, 0..core.guete.NORM_MAX (35) — dieselbe Skala, auf der
         die bestehenden Norm-Linien des Lernvorrats stehen.
      k  Kantenlaenge in PIXELN, 0..core.guete.KANTE_MAX (400) — die Spanne,
         die die Konfigurationsseite fuer `urteil_kante` seit jeher fuehrt.
    Lazy importiert, damit dieses Modul leicht bleibt."""
    if achse == "p":
        from core.livewache import POSE_MIN_MAX
        return float(POSE_MIN_MAX)
    if achse == "n":
        from core import guete as _guete
        return float(_guete.NORM_MAX)
    if achse == "k":
        from core import guete as _guete
        return float(_guete.KANTE_MAX)
    return 1.0


def guards(cfg):
    """Die normalisierten Guard-Bloecke -> {kamera: block}. EINE Normalisierung
    (core.livewache.guards_lesen), kein zweiter Leser des Store-Blocks. Der Log
    ist hier bewusst stumm: dieselben Werte werden beim Engine-Start laut
    geprueft, und eine Kalibrier-Seite soll das Dienst-Log nicht doppelt
    fuellen."""
    from core import livewache as _lw          # lazy: dieses Modul bleibt leicht
    try:
        _d, g = _lw.guards_lesen(cfg, log=lambda *_a, **_k: None)
    except Exception:                                       # noqa: BLE001
        return {}
    return g


def anzeige_latte(cfg, kamera, guard=None):
    """Latte 2 (Anzeige/Melden/Vorrat) DIESER Kamera.
    -> {"det": float|None, "e": float|None, "t": float|None}
    None heisst "keine Latte" — exakt wie vor diesem Bau (Migrations-Semantik
    im Modulkopf). Der Aufrufer darf einen bereits gelesenen Guard-Block
    hereinreichen, damit die Uebersicht nicht je Kachel neu normalisiert."""
    g = guard if guard is not None else (guards(cfg).get(kamera) or {})
    return {"det": _zahl(g.get("det_min")),
            "e": _zahl(g.get("guete_e_min")),
            "t": _zahl(g.get("guete_t_min")),
            # Pose-Sieb (03.09.): gleiche Semantik wie e/t — der GESETZTE
            # Kamera-Wert oder None (dann wirkt der Werks-Boden).
            "p": _zahl(g.get("pose_min"))}


# .516 ALT-LATTEN-ABLOESUNG: `global_latte` ist ERSATZLOS ENTFERNT. Sie las die
# zwei GLOBALEN Config-Werte `guete_empfinden_min`/`guete_t_min` und war ihr
# letzter Anzeige-Leser (Uebersichts-Karte "Global fallback"). Beide Werte gibt
# es nicht mehr: der Rueckfall ist seit .514 die GLOBALE Zeile des Registers
# selbst (`katalog_latten(cfg)["global"]`), und die zeigt die Uebersicht direkt.
# Eine Funktion, die eine zweite globale Latte anbietet, waere genau die
# Doppel-Latte, die dieser Zug abschafft.


def katalog_start():
    """Werks-Vorgabe der KATALOG-Latte -> {"e", "t", "det", "p"}.

    EINE Quelle, seit .511 die EIGENE: core.guete.KATALOG_STARTWERTE
    (0,125/0,125, User-Entscheid 08.09.2026). Bis .510 lieh sich diese Latte
    die globalen Lernlauf-Startwerte (0,200/0,400, mit .516 entfernt) — das war
    die NAH-Eichung, und sie war als AUFNAHME-Latte zu streng: am
    Feldtester-Spiegel kamen 34 von 200 Kalibrier-Samples durch, die
    Automatik-Wege liefen damit praktisch leer.

    Der Rollen-Zuschnitt vom 08.09. dreht die Richtung um: AUFNEHMEN ist
    liberal, gesiebt wird danach vom BESTANDS-Pruefer (core/refurteil.py).
    Die Katalog-Latte ist damit kein Guetesieb mehr, sondern der Boden gegen
    totes Material. Wer strenger aufnehmen will, hebt die Kamera-Latte auf
    dieser Seite; wer strenger AUSSORTIEREN will, hebt die Pruefer-Latte im
    dritten Register — zwei Fragen, zwei Regler.

    .514: die zwei neuen Achsen bekommen ihre Werks-Vorgabe aus DEMSELBEN
    Modul, und zwar den gemessenen BODEN — det core.guete.DET_BODEN (0,40, die
    Untergrenze des det-Reglers seit dem Zentral-Umbau), Pose
    core.guete.POSE_BODEN (0,65, die Ring-Sichtung vom 03.09.). Werkswert =
    Boden = Regler-Minimum, dieselbe Regel, die der User am 03.09. fuer die
    Stimm-Latten festgelegt hat („durchgaengig"). Wer schaerfer sieben will,
    kalibriert die Kamera.

    .515 baute die Norm-Achse ein und liess sie AUS (core.guete.NORM_BODEN = 0)
    — sie war neu und ungeeicht. .516 schaltete sie EIN, mit dem geliehenen
    Vorrats-Boden 22,0; .517 setzt den Grundwert auf 20 (User-Entscheid
    10.09.2026 nach Sichtung am Norm-Schieber, 756 Ernte-Bilder, Median 20,7).
    Die Zahl steht als EINE Quelle in `core.guete.norm_werk()` — hier wird sie
    nur gelesen, die Herleitung steht dort. Das ERKENNEN-Register bleibt bei
    0/aus (`erkennen_start`), weil der Erkennungs-Weg die Norm nicht misst."""
    from core import guete as _guete
    return {"e": float(_guete.KATALOG_STARTWERTE["empfinden"]),
            "t": float(_guete.KATALOG_STARTWERTE["t"]),
            "det": float(_guete.DET_BODEN),
            "p": float(_guete.POSE_BODEN),
            "n": _guete.norm_werk(),
            # GANZE PIXEL, bewusst int (.516, Fund der Querpruefung): der
            # Config-Schluessel `katalog_guete_kante_min` steht in der
            # Whitelist als int. Ein float-Werkswert 25.0 wurde vom
            # Konfigurations-Blatt als "25.0" zurueckgepostet, und `int("25.0")`
            # wirft — mit .515 liess sich das GANZE Blatt nicht mehr speichern
            # ("'katalog_guete_kante_min': ungueltiger Wert"), weil
            # config_schreiben beim ersten unguelt. Wert abbricht. Die
            # aufgeloeste Latte bleibt float (`_boden_fuellen` castet), nur die
            # WERKS-Vorgabe traegt den Typ ihrer Skala.
            "k": int(_guete.KANTE_WERK)}


def erkennen_start():
    """Werks-Vorgabe der .515-Achsen des ERKENNEN-Registers -> {"n", "k"}.

    Dieselbe EINE Quelle wie im Katalog-Register (core.guete): die zwei
    Register unterscheiden sich in ihren WERTEN, nicht in ihren Zahlen-
    Quellen. Norm = NORM_BODEN = 0 = aus (und das bleibt sie mit .516: der
    Erkennungs-Weg MISST die Feature-Norm nicht, eine Latte ohne Messung waere
    fail-closed — nur das Katalog-Register schaltet sie ein);
    Kante = KANTE_WERK = 25 px, also
    GENAU die Zahl, die bis .514 als Konstante `urteil_kante` im Stimmweg
    stand — der Umbau ist damit im Werkszustand wertgleich."""
    from core import guete as _guete
    # `k` bewusst int — dieselbe Falle wie im Katalog-Register darueber:
    # `urteil_kante` steht in der Whitelist als int, und ein float-Werkswert
    # machte das Konfigurations-Blatt unspeicherbar (Fund .516).
    return {"n": float(_guete.NORM_BODEN), "k": int(_guete.KANTE_WERK)}


def katalog_latten(cfg):
    """Das REISE-FERTIGE Latten-Dict der Katalog-Aufnahme — der Aufrufer reicht
    es an die Uebernahme-Stellen weiter (Muster norm_latte/guete_latte: die
    Latte reist als fertiges Dict, der Verbraucher waehlt nie selbst
    Config-Schluessel aus).

    -> {"global": {alle Achsen}, "kameras": {name: {alle Achsen}}}

    BEWUSST je Aufruf frisch aus cfg gelesen (kein Env-Transport, keine
    Zwischenspeicherung): die Werte werden auf der Kalibrier-Seite geaendert
    und muessen SOFORT gelten — dieselbe Zusage wie bei den zwei
    .378-Schwellen ("wirkt live, kein Neustart"). Seit .514 traegt das
    Ergebnis ALLE Achsen (SIEB_ACHSEN); die Aufzaehlung steht EINMAL
    oben, nicht als Streu-Zugriffe hier — seit .515 sind es fuenf."""
    aus = {"global": {a: _zahl(cfg.get(ACHSE_GLOBAL[a]), hi=_achse_hi(a))
                      for a in SIEB_ACHSEN},
           "kameras": {}}
    for name, g in (guards(cfg) or {}).items():
        w = {a: _zahl(g.get(ACHSE_FELD[a]), hi=_achse_hi(a)) for a in SIEB_ACHSEN}
        if any(v is not None for v in w.values()):
            aus["kameras"][str(name)] = w
    return aus


def katalog_werte(latten, kamera):
    """Die WIRKSAME Katalog-Latte fuer eine Kamera
    -> {"e", "t", "det", "p", "quelle"}.
    quelle: 'kamera' | 'global' | 'aus'. Gemischt wird NICHT: hat die Kamera
    eigene Werte, gelten ihre (auch wenn nur einer gesetzt ist — der andere
    bleibt dann offen). Eine Halb-Mischung waere eine dritte, nirgends
    sichtbare Zahl.

    .514/.515: die Quellen-Wahl sieht ALLE Achsen an — eine Kamera, die
    irgendeinen eigenen Registerwert traegt, gilt als kalibriert.

    .516, BEWUSSTER UNTERSCHIED zu `sieb_latten`: DORT loest die Rangfolge seit
    der Reparatur JE ACHSE auf (`_aufloesen`), HIER bleibt es bei der ganzen
    Quelle. Das ist keine Schlamperei, sondern die andere Frage: `sieb_latten`
    entscheidet, was ueberhaupt ENTSTEHT, und muss deshalb auf jeder Achse eine
    Zahl haben; `katalog_werte` speist `katalog_ok`, das ausdruecklich
    FAIL-OPEN ist (ohne gesetzte Latte darf jedes Bild in den Katalog,
    Bestandsschutz) und die Uebersichts-Kachel, deren Marke „eigene Werte /
    Vorgabe" genau die ganze Quelle meint. Eine Umstellung hier waere eine
    Verhaltensaenderung an den vier Uebernahme-Stellen — das ist der als
    Folgeschritt ausgeklammerte Zug „Catalogue-check-Register".
    Benannte Rest-Folge, klein und nur theoretisch: eine Kamera, die
    AUSSCHLIESSLICH det/pose gesetzt haette, bekaeme fuer e/t 'offen' statt des
    globalen Rueckfalls — und weil `katalog_ok` bei 'offen' DURCHLAESST, ist
    das die harmlose Richtung. Ueber die Oberflaeche kann es ohnehin nicht
    entstehen: der Uebernehmen-Knopf schickt immer ALLE Felder des Registers."""
    l = latten or {}
    kam = (l.get("kameras") or {}).get(str(kamera or ""))
    if kam and any(kam.get(a) is not None for a in SIEB_ACHSEN):
        aus = {a: kam.get(a) for a in SIEB_ACHSEN}
        aus["quelle"] = "kamera"
        return aus
    gl = l.get("global") or {}
    if any(gl.get(a) is not None for a in SIEB_ACHSEN):
        aus = {a: gl.get(a) for a in SIEB_ACHSEN}
        aus["quelle"] = "global"
        return aus
    aus = {a: None for a in SIEB_ACHSEN}
    aus["quelle"] = "aus"
    return aus


# ------------------------------------------------- DAS EINE SIEB (.514)
# Etappe 3, User-Entscheid 09.09.2026 (Wortlaut): „ein system!!!! nur
# unterschiedliche werte je normalmodus und ernte bzw. lernmodus was das
# gleiche ist."
#
# Bis .513 gab es ZWEI Qualitaets-Siebe mit verschiedenen Achsen, verschiedenen
# Skalen und verschiedenen Zahlen:
#   * Erkennungs-Weg (analyze.py): det (an SCRFD gebunden) + Empfinden +
#     Erkennbarkeit (core.guete.stimme_ok) + Kopf-Pose (URT_POSE) — vier
#     Achsen, je Kamera kalibrierbar.
#   * Lern-/Ernte-Weg (core/ernte.py): m_det/m_kante/m_sharp, s_det,
#     vorrat_kante/vorrat_sharp und ein eigener det_thresh — sechs andere
#     Achsen, global, nicht je Kamera, und die zwei Guete-Masse wurden zwar
#     GEMESSEN, aber nicht gefragt (Pruefbericht 09.09., Tabelle „wirkt im
#     Ernte-Modus": det nein · empfinden nein · fiqa_t nein · pose existiert
#     im Lernpfad gar nicht).
# Seit .514 siebt der Lern-Weg mit DIESER Mechanik und den Werten des
# Katalog-Registers; der Erkennungs-Weg bleibt in .514 byte-unangetastet (er
# ist das VORBILD) und kann hier spaeter andocken — deshalb nimmt `sieb_ok`
# nackte Zahlen und kein Zeilen-Dict.
#
# Die REGEL je Achse steht nicht hier, sondern EINMAL in core.guete.achse_ok
# (dieselbe, die stimme_ok fuer seine zwei Achsen fuehrt): Latte <= 0 = Achse
# aus; Latte > 0 und kein Messwert = der Fund faellt (Messbarkeit vor Stimme,
# fail-closed je FUND); Modell-Ausfall ist Sache des Verbrauchers, der seine
# Latte dann laut auf 0 setzt (fail-open je MODELL).

# Verwurfsgruende — EINE Aufzaehlung fuer Zaehler, Bilanz und Log; ein
# zweites Literal in der Ernte waere genau die K3-Falle.
GRUND_UNTER = "unter"           # gemessen, aber unter der gesetzten Latte
GRUND_UNMESSBAR = "unmessbar"   # Latte aktiv, aber kein Messwert
SIEB_GRUENDE = tuple(f"{a}_{k}" for a in SIEB_ACHSEN
                     for k in (GRUND_UNTER, GRUND_UNMESSBAR))


def klemm_boeden():
    """Die KLEMM-Untergrenze je Achse — unter diese Zahl geht ein GESETZTER
    Wert nicht, egal wer ihn gesetzt hat (.516 R3b, Widerleger-Befund B7).

    WOZU: `core.guete.stimm_latten` klemmt seit jeher jeden gesetzten Wert auf
    `STIMM_BODEN` („weder der User noch sonst was geht darunter"). Das
    Sieb-Register tat das NICHT — der Store laesst `katalog_det_min` bis 0,05
    und `katalog_e_min`/`_t_min` bis 0,0 durch, und weil die Ernte den DETEKTOR
    an genau diese Zahl bindet (`emb.app.det_model.det_thresh`), machte ein
    Hand-Edit von 0,05 nicht nur ein weiches Sieb, sondern eine
    Detektions-Explosion.

    ZWEI SORTEN, und der Unterschied ist die Haus-Invariante „Latte <= 0 = aus":
      * e/t/p werden nur geklemmt, WENN sie > 0 sind. Eine gesetzte 0 bleibt
        eine 0 und heisst weiter „diese Achse ist bewusst aus" (Diagnose-Laeufe).
      * det wird IMMER geklemmt, auch eine 0. Der det-Wert ist keine reine
        Latte: er PARAMETRIERT den Detektor. „det aus" gibt es physisch nicht —
        eine 0 dort waere jeder Pixel ein Gesichtskandidat.
      * n/k haben den Boden 0, werden also faktisch nicht geklemmt: ihr
        Regler-Minimum IST die Aus-Stellung, und einen gemessenen Boden
        darunter gibt es nicht.

    DECKUNGS-VERTRAG: diese Zuordnung deckt SIEB_ACHSEN vollstaendig ab (die
    s11-Probe haelt das fest). Eine kuenftige Achse ohne Eintrag hier bekommt
    den Boden 0 — also kein Klemmen; das ist die richtige Vorgabe, aber sie
    soll eine ENTSCHEIDUNG sein, kein Vergessen."""
    from core import guete as _guete
    return {"det": float(_guete.DET_BODEN),
            "e": float(_guete.KATALOG_BODEN["empfinden"]),
            "t": float(_guete.KATALOG_BODEN["t"]),
            "p": float(_guete.POSE_BODEN),
            "n": 0.0,
            "k": 0.0}

# Die EINE Achse, deren Boden auch eine gesetzte 0 anhebt (Begruendung oben).
KLEMM_IMMER = ("det",)


def _klemmen(achse, wert, boeden):
    """Ein GESETZTER Wert auf seinen Boden — die Regel aus `klemm_boeden`."""
    b = float(boeden.get(achse, 0.0))
    if wert <= 0 and achse not in KLEMM_IMMER:
        return wert                      # bewusst aus, bleibt aus
    return max(wert, b)


def _aufloesen(kam, gl, std, achsen):
    """Die Rangfolge JE ACHSE: Kamera-Wert -> globaler Wert -> Werks-Boden.

    .516 R3a (Widerleger-Befund B3) — VORHER galt sie je QUELLE: sobald eine
    Kamera IRGENDEINEN Registerwert trug, war die ganze globale Zeile aus dem
    Rennen und jede offene Achse fiel auf den Werks-Boden. Der Docstring sagte
    „Kamera-Wert schlaegt global schlaegt Werks-Boden" und meinte etwas
    anderes. Das ist kein theoretischer Fall: JEDE vor .514 kalibrierte Kamera
    traegt `katalog_e_min`/`katalog_t_min` und KEIN `katalog_det_min`/
    `katalog_pose_min`. Hob der Betreiber danach den globalen
    `katalog_guete_pose_min` — das Config-Register bewirbt ihn genau dafuer:
    „This is what keeps bins, leaves and car parts out of the learning
    material" —, wirkte er auf dieser Kamera NICHT. Still, und die
    Registerbeschreibung sagte das Gegenteil.

    `quelle` benennt weiter die STAERKSTE beteiligte Quelle (kamera > global >
    aus) — das ist die Frage, die Anzeige und Log stellen („traegt diese Kamera
    eigene Werte?"), und die Wort-Menge bleibt damit unveraendert. Wer es genau
    wissen will, liest `quellen`: die Quelle JE Achse."""
    boeden = klemm_boeden()
    aus, quellen = {}, {}
    for a in achsen:
        w, q = kam.get(a), "kamera"
        if w is None:
            w, q = gl.get(a), "global"
        if w is None:
            w, q = std[a], "aus"
            aus[a] = float(w)
        else:
            aus[a] = _klemmen(a, float(w), boeden)
        quellen[a] = q
    q = set(quellen.values())
    aus["quelle"] = ("kamera" if "kamera" in q
                     else "global" if "global" in q else "aus")
    aus["quellen"] = quellen
    return aus


def sieb_latten(latten, kamera):
    """Die WIRKSAMEN Sieb-Werte einer Kamera -> {alle SIEB_ACHSEN, "quelle",
    "quellen"}.

    Kamera-Wert schlaegt global schlaegt WERKS-BODEN, seit .516 JE ACHSE
    (`_aufloesen` oben, Begruendung dort). Die dritte Stufe ist der Unterschied
    zu `katalog_werte` darueber und der Grund, warum es diese Funktion gibt:
    die Katalog-AUFNAHME darf ohne gesetzte Latte offen bleiben
    (Bestandsschutz, `katalog_ok` laesst dann alles durch), das LERN-SIEB nicht
    — eine Ernte ohne jede Latte sammelte wieder alles ein, was die Anlage
    sieht. Gesetzte Werte werden auf ihren Boden geklemmt (`klemm_boeden`).

    `kamera` darf None sein — dann gilt die globale Zeile (so schreibt der
    Lernlauf sein Manifest-Profil, das je LAUF und nicht je Kamera gilt)."""
    l = latten or {}
    kam = (l.get("kameras") or {}).get(str(kamera or "")) or {}
    return _aufloesen(kam, l.get("global") or {}, katalog_start(), SIEB_ACHSEN)


def erk_latten(cfg, guard):
    """Die WIRKSAMEN .515-Achsen des ERKENNEN-Registers -> {"n", "k",
    "quelle", "quellen"}.

    BAUFORM WIE `core.guete.stimm_latten`, nicht wie `sieb_latten`: der
    Aufrufer reicht den schon gelesenen Guard-Block DIESER Kamera herein
    (roh aus dem Store oder normalisiert — `_zahl` prueft beides). Grund ist
    der Live-Weg: `livewache._namens_stimmen` fragt je Namens-Stimme, und ein
    `guards_lesen` je Stimme normalisierte den ganzen Store neu.

    RANGFOLGE wortgleich zu `sieb_latten` und seit .516 ueber DIESELBE Funktion
    (`_aufloesen`): Kamera schlaegt global schlaegt Werks-Boden, JE ACHSE. Die
    „kalibriert?"-Frage stellt sich damit gar nicht mehr als Ganzes — eine
    Kamera, die vor .515 ihre Erkennen-Regler gesetzt hat, traegt keines der
    neuen Felder und bekommt fuer sie weiter den GLOBALEN Wert; das war schon
    vorher so gemeint und ist jetzt auch so gebaut."""
    g = guard or {}
    c = cfg or {}
    kam = {a: _zahl(g.get(ERK_FELD[a]), hi=_achse_hi(a)) for a in ERK_ACHSEN}
    gl = {a: _zahl(c.get(ERK_GLOBAL[a]), hi=_achse_hi(a)) for a in ERK_ACHSEN}
    return _aufloesen(kam, gl, erkennen_start(), ERK_ACHSEN)


def sieb_ok(werte, det=None, e=None, t=None, p=None, n=None, k=None):
    """DIE eine Sieb-Mechanik aller Achsen -> (ok, grund).

    `werte` = das Ergebnis von `sieb_latten` (oder jedes Dict mit
    Achsen-Schluesseln; eine FEHLENDE Achse wirkt wie „aus"). Die Messwerte
    kommen als nackte Zahlen herein, damit diese Funktion nichts ueber
    Zeilen-Formate wissen muss und beide Register mit denselben Argumenten
    andocken.

    grund ist None, wenn ok — sonst '<achse>_unter' bzw. '<achse>_unmessbar'
    aus SIEB_GRUENDE. Er ist Zaehl-Schluessel und Log-Text in einem: „warum
    faellt das Material" ist die Frage, die eine Latten-Aenderung beantworten
    koennen muss, und ein blosses False beantwortet sie nicht.

    REIHENFOLGE = SIEB_ACHSEN, also billig zuerst. Sie ist hier nicht nur
    Kosmetik: der Aufrufer misst die teure Pose (und seit .515 die noch
    teurere Feature-Norm) erst, wenn die billigen Achsen bestanden haben
    (Reihenfolge-Entscheid des Users 03.09.), und bekommt dann p=None/n=None
    herein — ohne diese Reihenfolge meldete die Funktion 'p_unmessbar' fuer
    einen Fund, der in Wahrheit schon an der Erkennbarkeit gescheitert ist."""
    from core import guete as _guete
    w = werte or {}
    for achse, wert in (("det", det), ("k", k), ("e", e), ("t", t),
                        ("p", p), ("n", n)):
        latte = w.get(achse)
        if _guete.achse_ok(latte, wert):
            continue
        return False, f"{achse}_" + (GRUND_UNMESSBAR if wert is None
                                     else GRUND_UNTER)
    return True, None


def sieb_satz(werte):
    """Die Klartext-Zeile eines Latten-Satzes (englisch wie alle Dienst-Logs).

    .516: die Zeile nennt die Quelle JE ACHSE, wenn sie gemischt ist. Seit die
    Rangfolge je Achse aufloest, kann eine Zeile aus zwei Quellen stammen — und
    „welche Zahl kam woher" ist genau die Frage, die ein Betreiber stellt, wenn
    ein gehobener globaler Regler an einer Kamera nichts zu bewirken scheint
    (der Bestands-Bedienweg aus Widerleger-Befund B3)."""
    w = werte or {}
    teile = ", ".join(f"{a} {w.get(a)}" for a in SIEB_ACHSEN)
    qn = w.get("quellen") or {}
    misch = ""
    if len(set(qn.values())) > 1:
        misch = " [" + ", ".join(f"{a}:{qn[a]}" for a in SIEB_ACHSEN
                                 if a in qn) + "]"
    return f"sieve bars ({w.get('quelle', '?')}){misch}: {teile}"


# ---------------------------------------------------------------- Uebersicht
def anzeige_start():
    """Werks-Vorgabe der ANZEIGE-Latte -> {"e","t"} (Quelle core.guete
    .ANZEIGE_STARTWERTE, User-Vorgabe 31.08. — Muster katalog_start)."""
    from core import guete as _guete
    return {"e": float(_guete.ANZEIGE_STARTWERTE["empfinden"]),
            "t": float(_guete.ANZEIGE_STARTWERTE["t"])}


def store_kameras(cfg):
    """Kameras, die der STORE kennt -> Menge von Namen.

    Zwei Datenlagen, EINE Frage: ein Guard-Block `live.guards.<kamera>`
    (dort liegen ALLE Kamera-Latten — Anzeige, Katalog, Pruefer) und/oder ein
    Kalibrier-Vorrat auf Platte (core.livewache.kalib_kameras). Beide werden
    ueber ihren jeweils schon vorhandenen Leser geholt, nie ueber einen
    zweiten Config- oder Pfad-Griff.

    WOZU (Fund 08.09.): bis dahin war die Frigate-Kameraliste die einzige
    Quelle der Uebersichts-Kacheln und der Erreichbarkeit von
    /kalibrierung/<kamera>. Eine frische Installation ohne Frigate-Verbindung
    und ohne Live-Waechter kam damit an keine Kalibrierseite — obwohl sie
    Material und Werte im Store hatte. Der Modulkopf und der Kommentar am
    Handler versprechen genau das Gegenteil ("jede Kamera, die Frigate kennt
    ODER die schon Werte im Store hat"); diese Funktion loest das Versprechen
    ein.

    NICHT gefiltert wird hier auf Sub-Kameras: die Uebersicht blendet sie aus
    (ist_subkamera), ihre Direkt-Adresse bleibt erreichbar — dieselbe Regel
    wie vorher, nur an EINER Stelle."""
    from core import livewache as _lw          # lazy: dieses Modul bleibt leicht
    aus = {str(n) for n in (guards(cfg) or {})}
    try:
        aus |= {str(n) for n in _lw.kalib_kameras(cfg)}
    except Exception:                                       # noqa: BLE001
        pass                    # Anzeige-Pfad: eine unlesbare Platte darf die
                                # Guard-Kameras nicht mitreissen
    return aus


def bekannt(cfg, kameras):
    """DIE eine Antwort auf "kennt die Kalibrierung diese Kamera?" -> Menge.

    Frigates Liste (vom Aufrufer hereingereicht — hier wird NIE eine zweite
    Kameraliste gebaut) plus die Store-Kameras. Uebersicht und
    404-Wache des Handlers fragen dieselbe Funktion; ein Name, der hier nicht
    steht, bleibt unbekannt (der Name kommt nie aus der URL)."""
    return {str(k) for k in (kameras or [])} | store_kameras(cfg)


def ist_subkamera(name):
    """Sub-/Zweitstrom-Kameras gehoeren nicht auf die Kalibrier-Uebersicht
    (User 31.08.: "cams die als sub sind ... gar nicht erst anzeigen").
    Erkennung am Namens-Baustein `_sub` (unterstrich-gebunden, z.B.
    Hof_CAM_sub_rec) — die Direkt-Adresse /kalibrierung/<name> bleibt
    erreichbar, nur die Uebersicht blendet aus."""
    n = str(name).lower()
    return "_sub_" in n or n.endswith("_sub")


def uebersicht_daten(cfg, kameras):
    """Der Stand ALLER Kameras fuer die zentrale Uebersichts-Seite.

    `kameras` kommt vom Aufrufer (verifyd.frigate_cameras) — hier wird NIE
    eine zweite Kameraliste gebaut (Deckungs-Regel). Kameras, die nur noch im
    Store stehen (aus Frigate entfernt, aber kalibriert) ODER die Frigate
    gerade nicht meldet (keine Verbindung, keine URL), kommen HINTEN dazu und
    sind als solche markiert: ihre Werte still verschwinden zu lassen waere
    ein Verlust ohne Ansage. Die Store-Seite kommt seit 08.09. aus
    store_kameras() — Guard-Block ODER Kalibrier-Vorrat, nicht mehr nur der
    Guard-Block (Fund: Vorrat auf der Platte, aber keine Kachel und 404 auf
    der Kameraseite).

    -> [{name, in_frigate, vorrat_n, vorrat_ts, vorrat_ts_min, det, e, t,
         eigene, kat_e, kat_t, kat_quelle}]"""
    from core import livewache as _lw
    g_alle = guards(cfg)
    latten = katalog_latten(cfg)
    namen = [str(k) for k in (kameras or []) if not ist_subkamera(k)]
    bekannt = set(namen)
    extra = sorted(n for n in store_kameras(cfg)
                   if n not in bekannt and not ist_subkamera(n))
    aus = []
    for name in namen + extra:
        g = g_alle.get(name) or {}
        anz = anzeige_latte(cfg, name, guard=g)
        kat = katalog_werte(latten, name)
        vorrat = _lw.kalib_lesen(cfg, name)
        # Nur GESTEMPELTE Eintraege: ts 0 heisst "kein Zeitstempel" (Alt-Zeile,
        # kaputter Wert) und ist kein Zeitpunkt von 1970. Fuer das Maximum
        # aendert das nichts, fuer das Minimum alles — eine einzige 0 machte
        # den Ring sonst "seit 1970 gefuellt".
        _ts = [z for z in (float(e.get("ts") or 0) for e in vorrat) if z > 0]
        aus.append({
            "name": name,
            "in_frigate": name in bekannt,
            "vorrat_n": len(vorrat),
            # Der juengste Eintrag des Rings = "zuletzt aktualisiert". Aus den
            # Daten gerechnet, nicht aus einer Datei-mtime: der Ring wird beim
            # Kappen neu geschrieben, die mtime waere dann eine Luege.
            "vorrat_ts": max(_ts, default=0.0),
            # .507: der AELTESTE Eintrag — mit dem juengsten zusammen der
            # Zeitraum, ueber den der Ring reicht. min/max statt "erste/letzte
            # Zeile", weil der Index nach Schreib-Reihenfolge sortiert ist und
            # eine Uhr-Korrektur diese Reihenfolge brechen kann.
            "vorrat_ts_min": min(_ts, default=0.0),
            "det": anz["det"], "e": anz["e"], "t": anz["t"], "p": anz["p"],
            # "eigene": traegt diese Kamera ueberhaupt einen eigenen Wert?
            # Genau die Frage, die die Kachel beantworten muss — sonst sieht
            # der Nutzer drei Zahlen und weiss nicht, ob sie IHM gehoeren.
            "eigene": any(v is not None for v in
                          (anz["det"], anz["e"], anz["t"], anz["p"])),
            "kat_e": kat["e"], "kat_t": kat["t"], "kat_quelle": kat["quelle"]})
    return aus


# ---------------------------------------------------------------- Das Urteil
def katalog_ok(latten, kamera, empf, fiqa_t):
    """DIE eine Frage aller Uebernahme-Stellen: darf dieses Bild in den
    Referenz-Katalog? -> (ok, grund).

    grund ist None, wenn ok — sonst ein kurzer, ehrlicher Satz MIT ZAHLEN
    (der Nutzer sieht ihn in der Uebersprungen-Liste; "abgelehnt" ohne Wert
    waere nicht nachvollziehbar).

    DURCHLASSEN ist der Rueckfall in JEDEM Zweifelsfall:
      * latten fehlt/leer            -> durch (Latte aus, Alt-Verhalten)
      * keine Latte fuer die Kamera  -> durch
      * empf/fiqa_t nicht gemessen   -> durch ("ungemessene Bilder urteilen
        alt" — Alt-Bestand, Alt-Image ohne die Guete-Modelle, Messfehler)
    Gesperrt wird nur, was GEMESSEN unter einer GESETZTEN Latte liegt.

    .514/.515, AUSDRUECKLICH: diese Funktion liest weiterhin NUR die zwei
    Guete-Achsen und behaelt ihr fail-open. Das Register traegt seit .515 fuenf
    Achsen, aber die neuen (det, Pose, Norm) gehoeren dem LERN-SIEB (`sieb_ok`).
    Die Uebernahme-Stellen an einem vierachsigen `katalog_ok` waeren eine
    Verhaltensaenderung an vier Stellen des Katalog-Wegs — die ist als eigener
    Zug ausgeklammert (User: „Catalogue-check-Register-Konsolidierung ist ein
    Folgeschritt"). Die Werte sind dieselben, nur die FRAGE ist eine andere:
    aufnehmen ist liberal, das Lern-Sieb entscheidet, was ueberhaupt entsteht."""
    w = katalog_werte(latten, kamera)
    if w["quelle"] == "aus":
        return True, None
    if empf is None or fiqa_t is None:
        return True, None
    try:
        e_ist, t_ist = float(empf), float(fiqa_t)
    except (TypeError, ValueError):
        return True, None
    if w["e"] is not None and e_ist < float(w["e"]):
        return False, (f"below the catalogue bar for picture impression "
                       f"({e_ist:.3f} < {float(w['e']):.3f})")
    if w["t"] is not None and t_ist < float(w["t"]):
        return False, (f"below the catalogue bar for recognisability "
                       f"({t_ist:.3f} < {float(w['t']):.3f})")
    return True, None
