"""core/messkarte — DIE Messkarte eines Gesichts-Funds (Etappe 1 „Messkern",
Bauplan `analysen/etappe1_messkern_bauplan.md`, 09.09.2026).

WOZU: dieselbe fachliche Frage — „was wurde an diesem Gesicht gemessen?" —
wurde bisher an jeder Station neu von Hand zusammengeklaubt. Die Inventur
(`analysen/lernlauf_inventur.md` §I-3) zaehlt VIER manuelle Kopierschritte
derselben Kette (Kandidatenzeile -> Anker-Mitglied -> Sichtung -> Bewertung;
der Kommentar in `core/anker.py` sagt selbst „hier zum dritten Mal") und eine
FUENFTE Stelle, die still vergisst (`core/vorrat.py`: die Angebots-Zeile
kopiert kante/sharp/norm, aber nicht die Guete-Masse). Eine Messkette, die
vier Kopierschritte braucht, verliert beim fuenften Weg — genau das ist
passiert.

Dieses Modul ist deshalb KEIN Rechner und KEIN Messer. Es ist ein VERTRAG,
gebaut nach dem bewaehrten Muster von `core/refmess.MESSFELDER`: EINE Liste
der Felder, die eine Messung erzeugt, und EIN Griff, der sie als Ganzes
weiterreicht. Das Gate haelt Schreiber und Leser dagegen (K3-Regel aus
`qs_ebenen.md`: wer eine fachliche Aufzaehlung braucht, nimmt die zentrale
Quelle oder deklariert einen Deckungs-Vertrag — nie ein weiteres verstreutes
Literal).

ETAPPE 1 IST VERHALTENSNEUTRAL — und dafuer traegt die Karte ihre Guete-Masse
unter EIGENEN Namen (`mk_fiqa_t`/`mk_empf`) neben den bestehenden Feldern
`fiqa_t`/`empf`. Das ist die wichtigste Entscheidung dieses Moduls, und sie
hat einen gemessenen Grund:

  Die bestehenden Felder `fiqa_t`/`empf` sind NICHT nur Daten, sie sind ein
  SCHALTER. `core.benennung.guete_weg_aktiv` (und wortgleich der `_g_da`-Zweig
  in `anlernen.bild_stufe`) entscheidet allein an ihrem Vorhandensein, WELCHE
  Latten-Generation ueber ein Bild urteilt: mit den beiden Werten die
  kalibrierte Guete-Latte (Empfinden/fiqa_t), ohne sie der Alt-Weg ueber
  Pixel-Schaerfe bzw. Feature-Norm. Ebenso fragen die drei Uebernahme-Stellen
  `anlernen.vorrat_aufnehmen`, `anlernen.vorschlag_aufnehmen` und
  `verifyd.enroll_entscheiden` ihre `katalog_ok`-Latte mit genau diesen
  Feldnamen aus der Zeile.

  Wuerde die Ernte ihre neu gemessenen Werte (Baustein B2: Guete kuenftig auch
  fuer v-Kandidaten) einfach unter `fiqa_t`/`empf` schreiben, aenderte sich
  damit SOFORT das Urteil an vier Stellen, ohne dass eine einzige Latte
  angefasst waere: das Anker-Sieb (`core.anker._sieb_besteht`), die
  Gruppen-Flaeche, der Pool-Zulauf und die drei Katalog-Latten. Der Bauplan
  verbietet das ausdruecklich („keine Latte, kein Sieb, kein Urteil aendern";
  fuer `katalog_ok` benennt er die Falle selbst: „das waere eine
  Verhaltensaenderung!"). Er nimmt aber an, das blosse Mitschreiben sei
  neutral — das ist es nicht. BEFUND, im Bau-Bericht gefuehrt.

  Die Karte loest das konstruktiv statt mit Ausnahmen: sie MISST vollstaendig
  (Deckung wird sichtbar und zaehlbar, `bilanz_*` unten), sie TRANSPORTIERT
  vollstaendig (ein Griff, kein Kopierschritt), und sie URTEILT in Etappe 1
  nirgends mit — kein Verbraucher liest `mk_*`. Etappe 3 hat damit genau EINEN
  bewussten Zug vor sich: die Verbraucher von `fiqa_t`/`empf` auf `mk_*`
  umhaengen, wenn die Latten-Hoehen aus E2 stehen. Bis dahin bleibt
  beweisbar, dass sich nichts anders verhaelt.

BEWUSST NICHT IN DER KARTE:
  * `eid`, `kamera`, `t`, `ts`, `bbox`, `emb`, `datei`/`datei_v`, `m`/`s`/`v`,
    `bildquelle`, `richtung`, `quelle` — Identitaet, Ort, Bildzeiger,
    Gate-Ergebnisse und Routing. Sie haengen nicht an der MESSUNG (gleiche
    Abgrenzung wie `refmess`: „NICHT hier drin: anker, camera, kam_stand,
    eid").
  * ein Mess-ZEITSTEMPEL je Fund. `refmess` fuehrt einen, weil es ein CACHE
    ist und Frische braucht. Die Karte reist dagegen IN den Lauf-Dateien mit,
    und die Abnahme dieser Etappe vergleicht zwei Laeufe ueber DIESELBEN
    Ereignisse Feld fuer Feld — eine Wanduhr in jeder Fund-Zeile machte zwei
    identische Laeufe kuenstlich verschieden. Die Herkunft traegt statt dessen
    `mk_quelle` (WORAN gemessen wurde) und `mk_modell` (WOMIT); WANN steht am
    Lauf (Manifest, Datei-mtime). Abweichung vom Bauplan-Wortlaut
    („Herkunfts-/Modell-/ts-Felder"), begruendet und im Bericht gefuehrt.
"""

SCHEMA = 1

# ---------------------------------------------------------------- Der Vertrag
# DIE Feldliste der Messkarte. Reihenfolge = Schreib-Reihenfolge; neue Felder
# kommen ans ENDE (Haus-Muster: „am DICT-ENDE, nicht zwischen den Messwerten —
# sonst zeigte der Byte-Beweis-Diff eine Schluessel-Umsortierung statt einer
# Ergaenzung").
#
# BESTAND (die Achsen, die es an den Stationen laengst gibt — sie stehen hier,
# damit die Karte die SOLL-Menge deklariert und das Gate jede Station dagegen
# halten kann):
BESTAND = ("det", "kante", "sharp", "front", "front_kps", "pose", "norm",
           "struktur", "luma")

# GUETE (Etappe 1, eigene Namen — Begruendung im Modulkopf): die zwei
# Kalibrier-Masse aus core/guete.py. `mk_fiqa_t` = Erkennbarkeit am aligned
# 112er, `mk_empf` = Empfinden am Ausschnitt.
GUETE = ("mk_fiqa_t", "mk_empf")

# HERKUNFT: woran und womit gemessen wurde.
HERKUNFT = ("mk_quelle", "mk_modell")

# POSE (.514, Etappe 3 „ein Sieb"): der RTMPose-KOPFSCORE — dieselbe Zahl, auf
# die der Erkennungs-Weg seinen pose_min-Regler kalibriert hat. Bis .513 lag
# sie am Ernte-Material NICHT vor (Pruefbericht 09.09.: „kein p-Feld in
# irgendeiner Kandidaten-Zeile"), weshalb die Pose-Achse dort nur ueber
# Stellvertreter abschaetzbar war ([[ersatzmessungen-sind-hypothesen]]). Sie
# steht bewusst am ENDE der Karte und nicht bei `pose`: `pose` sind die drei
# insightface-WINKEL, das hier ist ein Score der Personen-Pose — zwei Skalen,
# die nie vermischt werden duerfen.
POSE = ("mk_pose",)

MESSFELDER = BESTAND + GUETE + HERKUNFT + POSE

# Werte, die `mk_quelle` annehmen darf — EINE Quelle statt Streu-Literalen.
# Sie benennen den AUSSCHNITT, an dem die Guete gemessen wurde; verschiedene
# Ausschnitte haben verschiedene Skalen ([[ersatzmessungen-sind-hypothesen]]),
# deshalb gehoert die Angabe an die Zahl und nicht in einen Kommentar.
QUELLE_M = "ernte_m"        # enger Bbox-Crop des Ernte-Frames. Seit .514 der
#                             EINE Ernte-Ausschnitt: gemessen wird VOR dem Sieb
#                             und damit fuer jeden L-Passierer, nicht mehr je
#                             nach Route.
QUELLE_V = "ernte_v"        # Route „nur Vorratsbild" (.513). Kommt seit .514
#                             in frischen Ernte-Zeilen nicht mehr vor — V haengt
#                             unter M, und beide messen denselben Ausschnitt.
#                             Bleibt gueltig fuer Altlaeufe.
QUELLE_EVENT = "event_crop"  # Event-Crop des Analyse-Laufs (Bestands-Suche W5)
QUELLE_ANALYSE = "analyse"  # im Analyse-Lauf gemessen (Enrollment W6)
QUELLEN = (QUELLE_M, QUELLE_V, QUELLE_EVENT, QUELLE_ANALYSE)


def karte(quelle, felder=MESSFELDER):
    """Die Messkarte EINER Zeile als eigenes Dict -> {feld: wert}.
    Fehlende Felder stehen als None drin: die Karte sagt „nicht gemessen",
    sie schweigt nicht."""
    q = quelle or {}
    return {k: q.get(k) for k in felder}


def uebernehmen(ziel, quelle, felder=MESSFELDER):
    """Die Karte als GANZES weiterreichen — DER Griff, der die vier
    Kopierschritte ersetzt. -> `ziel` (fuer Ketten-Aufrufe).

    ERGAENZT NUR, ueberschreibt NIE: ein Feld, das `ziel` schon traegt, bleibt
    unangetastet. Das ist load-bearing und nicht Bequemlichkeit — die Sichtung
    misst die Feature-Norm eines Mitglieds nachtraeglich nach
    (`anlernen._norm_nachmessen`, gelingt in 44 %) und traegt sie in ihre
    Zeile ein, BEVOR die Karte kommt. Ein blindes Ueberschreiben mit dem
    (None-)Wert der Quelle wuerde genau diese Nachmessung wieder loeschen —
    ein stiller Verlust, und obendrein eine Verhaltensaenderung in einer
    Etappe, die keine haben darf.

    Die Reihenfolge bleibt erhalten: Python behaelt die Einfuege-Position
    eines Schluessels, neue Felder haengen sich hinten an. Ein Byte-Diff
    zweier Laeufe zeigt damit Ergaenzungen, keine Umsortierung."""
    q = quelle or {}
    for k in felder:
        if k not in ziel:
            ziel[k] = q.get(k)
    return ziel


def vollstaendig(zeile, felder=MESSFELDER):
    """-> Liste der Kartenfelder, die diese Zeile NICHT fuehrt (Schluessel
    fehlt). Fuer die Gate-Probe: ein Feld mit dem Wert None ist gemessen-und-
    nichts-gefunden und damit in Ordnung; ein FEHLENDER Schluessel heisst,
    eine Station hat den Kopierschritt vergessen."""
    return [k for k in felder if k not in (zeile or {})]


# ------------------------------------------------------------------- Bilanz
# B4 des Bauplans: das Messbarkeit-vor-Stimme-Gegenstueck fuer den LERNPFAD
# (Inventur-Befund I-7). Auf dem Urteilspfad gibt es den Zaehler
# `stimmen_verworfen_unmessbar`; auf dem Lernpfad gab es bisher NICHTS — kein
# „N Referenzen ungemessen aufgenommen", keine Zeile „die Guete-Latte hat in
# diesem Lauf 0 von 340 Bildern beurteilt". Eine strengere Latte einzuziehen,
# ohne diesen Zaehler zu haben, waere blind.
#
# DIE Gruende, unter denen eine Guete-Messung ausfaellt — EINE Aufzaehlung,
# damit Zaehler und Anzeige nie auseinanderlaufen:
GRUND_KEIN_GESICHT = "kein_gesicht"   # kein Ausschnitt/keine Detektion
GRUND_KPS_FEHLT = "kps_fehlt"         # ohne Landmarken kein aligned 112er
GRUND_MODELL_FEHLT = "modell_fehlt"   # core.guete nicht verfuegbar (Alt-Image)
GRUND_MESSFEHLER = "messfehler"       # Modell da, Messung warf
GRUND_KEIN_WEG = "kein_weg"           # weder M- noch V-Kandidat: nichts zu messen
# .518 (gebuendelter Norm-Schritt): die Messbasis fehlt. Der Fund WAERE
# messbar gewesen, aber seine konservierte 112er-Warp-Kachel ist nicht da
# (keine Landmarken beim Ernten, Kachel unlesbar, oder die Messung warf). Ein
# eigener Grund und kein geliehener: „kps fehlt" waere eine Behauptung ueber
# die Ernte, die dieser Schritt gar nicht pruefen kann.
GRUND_WARP_FEHLT = "warp_fehlt"
GRUENDE = (GRUND_KEIN_GESICHT, GRUND_KPS_FEHLT, GRUND_MODELL_FEHLT,
           GRUND_MESSFEHLER, GRUND_KEIN_WEG, GRUND_WARP_FEHLT)


def bilanz_start(weg):
    """Frische Bilanz EINES Wegs. `weg` benennt den Pfad im Klartext
    ('ernte', 'bestands-suche', 'enrollment' …) — er steht in der Lauf-Datei
    und in der Logzeile, damit eine Deckungs-Luecke ihren Ort nennt.

    `sieb` (.514) ist die zweite Haelfte derselben Buchfuehrung: die
    Mess-Bilanz sagt, wie viel BEURTEILBAR war, die Sieb-Bilanz, wie das
    Urteil ausfiel und woran es scheiterte. Sie sitzt bewusst IM selben Dict
    und nicht daneben — dann reist sie ueber denselben einen Weg
    (fertig.jsonl -> Resume -> Lauf-Zustand -> Logzeile) und kann nicht an
    einer nicht mitgezogenen Transport-Liste still herausfallen (genau die
    Fehlerklasse, die .343/.346 dreimal binnen 24 h getreten hat)."""
    return {"weg": str(weg), "gesehen": 0, "gemessen": 0, "unmessbar": 0,
            "gruende": {},
            "sieb": {"durch": 0, "gesiebt": 0, "gruende": {}}}


def sieb_zaehlen(b, ok, grund=None):
    """Ein Sieb-Urteil verbuchen (.514, Etappe 3 „ein Sieb").
    `grund` kommt aus core.kamerakalib.SIEB_GRUENDE ('<achse>_unter' bzw.
    '<achse>_unmessbar') oder ist 'fd' fuer die Objekt-Signatur. -> die Bilanz.

    WOZU der Grund einzeln: eine Latte, die man verstellen soll, muss sagen
    koennen, WAS an ihr haengenbleibt. Und die unmessbar-Faelle sind das
    Gegenstueck zu `stimmen_verworfen_unmessbar` auf dem Urteilspfad — sie
    beziffern den Preis der Regel „Messbarkeit vor Stimme" auf dem Lernpfad
    (fail-closed je Fund), statt ihn verschwinden zu lassen."""
    if b is None:
        return b
    s = b.setdefault("sieb", {"durch": 0, "gesiebt": 0, "gruende": {}})
    if ok:
        s["durch"] = int(s.get("durch") or 0) + 1
        return b
    s["gesiebt"] = int(s.get("gesiebt") or 0) + 1
    if grund:
        g = s.setdefault("gruende", {})
        g[str(grund)] = int(g.get(str(grund)) or 0) + 1
    return b


def sieb_unmessbar(b):
    """-> Zahl der Funde, die das Sieb verwarf, WEIL ein Wert fehlte."""
    g = ((b or {}).get("sieb") or {}).get("gruende") or {}
    return sum(int(v or 0) for k, v in g.items() if str(k).endswith("_unmessbar"))


def bilanz_zaehlen(b, gemessen, grund=None):
    """Einen Fund verbuchen. `gemessen` True = beide Guete-Masse liegen vor.
    Sonst zaehlt `grund` (aus GRUENDE) mit. -> die Bilanz."""
    if b is None:
        return b
    b["gesehen"] = int(b.get("gesehen") or 0) + 1
    if gemessen:
        b["gemessen"] = int(b.get("gemessen") or 0) + 1
        return b
    b["unmessbar"] = int(b.get("unmessbar") or 0) + 1
    if grund:
        g = b.setdefault("gruende", {})
        g[str(grund)] = int(g.get(str(grund)) or 0) + 1
    return b


def bilanz_summe(bilanzen):
    """Mehrere Bilanzen DESSELBEN Wegs zusammenziehen (die Ernte laeuft je
    Event einen eigenen Job) -> eine Bilanz."""
    bs = [b for b in (bilanzen or []) if b]
    if not bs:
        return None
    aus = bilanz_start(bs[0].get("weg") or "?")
    for b in bs:
        for k in ("gesehen", "gemessen", "unmessbar"):
            aus[k] += int(b.get(k) or 0)
        for g, n in (b.get("gruende") or {}).items():
            aus["gruende"][g] = int(aus["gruende"].get(g) or 0) + int(n or 0)
        # Sieb-Haelfte (.514). Alt-Bilanzen (Laeufe vor .514, fertig.jsonl
        # eines Resumes) tragen den Schluessel nicht — sie zaehlen mit 0 und
        # bleiben gueltig, dieselbe Regel wie bei jedem anderen Zusatzfeld.
        s = b.get("sieb") or {}
        for k in ("durch", "gesiebt"):
            aus["sieb"][k] += int(s.get(k) or 0)
        for g, n in (s.get("gruende") or {}).items():
            aus["sieb"]["gruende"][g] = (int(aus["sieb"]["gruende"].get(g) or 0)
                                         + int(n or 0))
    return aus


# ------------------------------------------------------------------- Profil
# B5 des Bauplans, VARIANTE KLEIN (User-Entscheid 09.09.). Das
# Architektur-Bild des Users (Diktat 09.09.): „Der Worker ist immer das Kernsystem.
# Maximal bekommt der Worker beim Aufruf einen Hinweis: Material fuer die
# normale Analyse ODER vorgefiltertes Material fuer den Lernlauf." Dieser
# Hinweis ist das PROFIL — ein Zweck-Name plus die vier Achsen, auf denen das
# Haus urteilt (det, Empfinden, Erkennbarkeit, Kopfpose;
# `analysen/personenpfad_inventur.md` §2).
#
# IN ETAPPE 1 SIEBT DAS PROFIL NICHTS. Es wurde ausschliesslich MITGESCHRIEBEN,
# damit an jedem Ergebnis steht, was zur Laufzeit galt (E10).
#
# SEIT ETAPPE 3 (.514) IST DAS NUR NOCH FUER DEN ANALYSE-ZWECK WAHR. Auf dem
# LERN-Weg sind die vier Achsen das Sieb geworden: der Dienst loest sie je
# Kamera aus dem Katalog-Register auf (core.kamerakalib.sieb_latten), legt sie
# als `sieb` an den Ernte-Job, und core.ernte urteilt mit ihnen. Das
# Manifest-Profil eines Lernlaufs traegt seitdem GENAU die Zahlen, die gewirkt
# haben (global aufgeloest — je Kamera steht es am Job), statt eines Protokolls
# ohne Wirkung. Fuer ZWECK_ANALYSE gilt der Absatz darueber unveraendert
# weiter: dort sieben nach wie vor die Argumente von analyze.py.
#
# GEFUELLT WIRD ES VOM DIENST, nie vom Worker (refqs-Muster, worker.py: „der
# Worker greift nie selbst in die Config"). Der Worker weiss damit nie, WOZU er
# misst — er liefert Karten; wann welche Zahl zaehlt, regelt der Aufrufer.
ZWECK_LERNEN = "lernlauf"      # vorgefiltertes Material fuer den Lernlauf
ZWECK_ANALYSE = "analyse"      # die normale Ereignis-Analyse

# .515 (Sensoren 5+6): `norm_min` und `kante_min` sind dazugekommen. Ein Profil, das eine
# WIRKENDE Achse verschweigt, ist genau die Klasse „das Manifest sagt nicht die
# Wahrheit", die der .514-Widerleger als B9 gefuehrt hat — also wandert jede
# neue Sieb-Achse hier mit. None heisst weiterhin „auf diesem Weg gilt keine
# Latte": der ANALYSE-Weg misst die Feature-Norm nicht, und das soll sein
# Profil auch sagen, statt eine 0 zu behaupten, die nach nichts aussieht.
# ANGEHAENGT, nicht einsortiert (Haus-Muster oben): neue Felder kommen ans
# ENDE, sonst zeigte ein Byte-Vergleich zweier Laeufe eine Schluessel-
# Umsortierung statt einer Ergaenzung. Die Reihenfolge hier ist deshalb
# ausdruecklich NICHT die von SIEB_ACHSEN — geprueft wird die DECKUNG.
PROFIL_ACHSEN = ("det_min", "guete_e_min", "guete_t_min", "pose_min",
                 "norm_min", "kante_min")
PROFIL_FELDER = ("zweck",) + PROFIL_ACHSEN


def profil(zweck, werte=None):
    """Ein Latten-Profil -> {zweck, det_min, guete_e_min, guete_t_min,
    pose_min}. Fehlende Achsen stehen als None: „hier gilt keine Latte" ist
    eine Aussage, kein Loch. Der Aufrufer ist IMMER der Dienst."""
    w = werte or {}
    aus = {"zweck": str(zweck)}
    for k in PROFIL_ACHSEN:
        v = w.get(k)
        try:
            aus[k] = None if v is None else float(v)
        except (TypeError, ValueError):
            aus[k] = None
    return aus


def profil_satz(p, nachmess=None):
    """Die Klartext-Zeile eines Profils (englisch, wie alle Dienst-Logzeilen).
    Der Nachsatz sagt, ob dieses Profil URTEILT: seit .514 tut es das auf dem
    Lern-Weg, auf dem Analyse-Weg bleibt es Protokoll.

    `nachmess` (.518) = die Achsen, die im ERNTE-JOB nicht sieben, sondern in
    einem gebuendelten Schritt danach gemessen werden (heute nur die
    Feature-Norm, Quelle core.kamerakalib.NACHMESS_ACHSEN). Sie stehen mit
    ihrer WIRKENDEN Zahl im Profil — die Zahl gilt ja —, aber das Profil muss
    auch sagen, WO sie faellt: „in effect" allein liesse einen Betreiber
    glauben, ein Ernte-Job habe darueber entschieden. Ein Profil, das nicht
    die Wahrheit sagt, ist der Widerleger-Befund B9."""
    if not p:
        return ""
    teile = ", ".join(f"{k} {p.get(k)}" for k in PROFIL_ACHSEN)
    nach = ("in effect" if p.get("zweck") == ZWECK_LERNEN
            else "recorded, not sieving")
    satz = f"profile '{p.get('zweck')}' ({teile}) — {nach}"
    if nachmess:
        satz += (" (" + ", ".join(str(a) for a in nachmess)
                 + ": measured after the harvest, in the bundled step)")
    return satz


def bilanz_satz(b):
    """Die EINE Logzeile einer Bilanz (englisch wie alle Dienst-Logzeilen).
    -> str, oder '' ohne Bilanz."""
    if not b:
        return ""
    g = b.get("gruende") or {}
    rest = ("; " + ", ".join(f"{k} {v}" for k, v in sorted(g.items()))) if g else ""
    satz = (f"measurement coverage ({b.get('weg')}): "
            f"{b.get('gemessen', 0)} of {b.get('gesehen', 0)} finding(s) carry "
            f"both quality scores, {b.get('unmessbar', 0)} unmeasurable{rest}")
    s = b.get("sieb") or {}
    if int(s.get("durch") or 0) or int(s.get("gesiebt") or 0):
        sg = s.get("gruende") or {}
        srest = ("; " + ", ".join(f"{k} {v}" for k, v in sorted(sg.items()))) if sg else ""
        satz += (f" | sieve ({b.get('weg')}): {s.get('durch', 0)} kept, "
                 f"{s.get('gesiebt', 0)} sieved out, of which "
                 f"{sieb_unmessbar(b)} for want of a measurement{srest}")
    return satz
