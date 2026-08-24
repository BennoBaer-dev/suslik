#!/usr/bin/env python3
"""core/rechenprobe.py — Lieferung C aus analysen/15 §4: die Hardware-NUTZBARKEITS-Probe.

DIE FRAGE, die sie je Modell des Urteilspfads beantwortet: auf welchem Geraet laeuft
dieses Modell im Betrieb wirklich, und rechnet es dort DAS, was die CPU rechnet — in der
OpenVINO-Voreinstellung (fp16) und mit erzwungenem FP32? Der Start prueft heute nur, ob
ein Geraet BINDET, nie ob es richtig rechnet (Feldfall 24.08.: eine Gen8-iGPU bindet,
benchmarkt 5,9x schneller als ihre CPU und wird von der Norm-Kreuzprobe mit "off by
105.276" verworfen — die Frage "ist diese Sonderhardware nutzbar?" konnte der Start nicht
beantworten).

ALLE AUSSENWELT IST INJIZIERT. `messen()` baut selbst keine Session, kennt kein
onnxruntime, oeffnet kein Geraet: der Aufrufer reicht einen `session_bauer` herein. Im
Betrieb ist das der echte ORT-Bauer (worker._rechenprobe_bauer), im Gate ein Fake, der
falsch rechnende, nicht bindende und still auf CPU zurueckfallende Geraete nachstellt
(Konzept §6.2 "injizierbare Messfunktion"). Auch der Modell-VERTRAG kommt als Argument —
diese Datei traegt keine Modell-Liste (qs_ebenen-Regel: wer eine fachliche Aufzaehlung
braucht, nimmt die zentrale Quelle; die ist core.registry.MODELL_VERTRAG).

WAS NICHT INJIZIERT IST, und warum das keine Aussenwelt ist: der synthetische Mess-Reiz
(face_audit.gesichtsreiz) und die Graph-Variante der Feature-Norm
(face_audit.NormMass._graph_bytes) sind deterministische Rechnungen ohne Geraet und ohne
Datei-Zufall — dieselbe Zahl auf jeder Maschine. Beide werden LAZY geholt, damit das
Modul ohne face_audit importierbar bleibt (das Gate laeuft auf einem python3 ohne
onnxruntime).

MESSMATERIAL (Konzept §4 "Messmaterial", gemessen 24.08.2026): der Gesichtsreiz statt
Rauschen. Rauschen versteckt den Fehler — dieselbe gesunde iGPU weicht im Rauschen 0,099
ab, auf dem Reiz 0,149 und auf echten Crops bis 0,67; ausserdem faellt Rauschen dem
adaface-Kopf auf Feature-Norm 11,6, waehrend die Betriebsentscheidungen bei 21,5..24,0
fallen. Drei Kontrast-Skalen (face_audit.NormMass.NORM_KREUZ_SKALEN), weil der Fehler mit
dem Arbeitspunkt wandert (fp16 auf dieser Maschine: 0,007 / 0,030 / 0,149).

DIE VIER MESSGROESSEN, je nach AUSGANGSSKALA des Vertrags (nicht je nach Modellname):
  norm      |dNorm| — die Laenge ||f|| des unnormierten Feature-Vektors, wortgleich die
            Groesse, die im Log "off by ..." heisst (NormMass._kreuzprobe)
  kosinus   1 - cos(Geraet, CPU) auf dem Erkennungs-Embedding
  score     max |dScore| ueber die Score-Ausgaenge des Detektors
  landmark  max |dKoordinate| in Pixeln auf dem 192er Eingang (Rohwert x 96)

DREI ANKER, damit kein Ausfall still bleibt:
  1. die CPU-Session desselben Modells im selben Lauf (der eigentliche Vergleich),
  2. die im Vertrag eingefrorenen CPU-SOLLZAHLEN (`soll_cpu`) — sie decken den Fall
     "Geraet UND CPU rechnen beide falsch" ab, den ein reiner Geraet-gegen-CPU-Vergleich
     konstruktionsbedingt nie sieht,
  3. jede Geraete-Messung LAEUFT ZWEIMAL im selben Lauf; weichen die zwei Laeufe
     voneinander ab, wird das gemeldet statt eingefroren (die fp16-Rechnung dieser
     Maschine streut zwischen zwoelf Laeufen derselben Session um 0,050, waehrend NPU und
     FP32 bitgenau wiederholen).

WAS SIE NICHT KANN (ehrliche Grenze, gehoert zur Stufe): einen Bauer, der still
CPU-Ergebnisse als Geraete-Ergebnisse liefert, kann diese Funktion NICHT entlarven — die
Zahlen waeren dann perfekt. Diese Klasse faengt allein der BAUER, der nach jedem
Session-Bau prueft, ob der EP wirklich in get_providers() steht, und sonst wirft
(worker._rechenprobe_bauer; die Diagnose-Kommandos in tester/gputest_kommandos_*.md
tragen dieselbe Wache aus demselben Grund).
"""
import gc
import os
import time

# Der Kantenlaenge-Rueckfall fuer Modelle mit DYNAMISCHEM Eingang: der Detektor traegt
# (1,3,H,W), H/W setzt erst der Betrieb. 320 ist die Groesse, mit der der Embedder seine
# Sessions aufbaut (face_audit.Embedder.__init__: prepare(det_size=(320,320))) und mit
# der auch die erprobten Diagnose-Kommandos messen (tester/gputest_kommandos_tokn59.md,
# Kommando 1). Fuer Clips schaltet der Betrieb spaeter auf ar_det_size hoch — fuer den
# reinen Zahlenvergleich CPU-gegen-Geraet ist die Kante gleichgueltig, solange BEIDE
# Seiten dieselbe benutzen; deklariert wird sie trotzdem, sonst misst man Unbekanntes.
DET_KANTE = 320

# Rohwert 1.0 der beiden Landmark-Modelle entspricht 96 px auf ihrem 192er Eingang
# (insightface landmark.Landmark.get rechnet (wert+1) * 96; Vertrag "ausgang.skala" beider
# Eintraege, gemessen 2026-08-24).
LANDMARK_PX = 96.0


# ---------------------------------------------------------------- Bewertungsschwellen
# EINE Stelle, hergeleitet aus den ENTSCHEIDUNGSLINIEN des Betriebs (Vertragsfeld "bezug"),
# nicht aus unserer einen Messung. Die Xe-Werte stehen nur als "so sieht gesund aus"
# daneben. Herleitung je Mass, mit Quelle:
#
# norm 0.10 — WORTGLEICH face_audit.NormMass.NORM_KREUZ_MAX, und das ist Absicht: an
#   dieser Zahl entscheidet der Code selbst, ob er ein Geraet fuer die Feature-Norm
#   nimmt. Eine zweite, abweichende Zahl hier waere eine zweite Wahrheit. Das Gate
#   prueft die Gleichheit (Deckungs-Vertrag statt zweiter Zahlenquelle) — s.
#   tools/qs.sh, Rechenproben-Stufe. Herleitung dort im Original: die engsten
#   Qualitaetslinien liegen 0,5 auseinander (21,5/22,0 und 23,5/24,0), der halbe
#   Abstand 0,25 ist die absolute Obergrenze, 0,10 haelt Faktor 2,5 Abstand.
#   Gemessen 24.08.2026: NPU 0,013 · GPU fp16 0,149 · GPU FP32 0,0000095.
# kosinus 0.01 — die Erkennung entscheidet bei win_thresh 0,38 auf der Kosinus-Skala
#   (verifyd.yaml). Aus cos wird der Winkelfehler arccos(cos), und um so viel kann eine
#   Aehnlichkeit im schlimmsten Fall verrutschen: 1-cos = 0,01 sind 8,1 Grad und bis
#   0,14 Verschiebung auf der 0,38-Linie (37 %) — darueber werden Personen verwechselt
#   (Herleitungstabelle tester/gputest_kommandos_tokn59.md §4, Kommando 2).
#   Gemessen 24.08.2026 auf gesunder Xe: fp16 1-cos = 2,47e-04, FP32 0,0.
# score 0.10 — der SCRFD-Score entscheidet gegen det_thresh 0,5 (Config-Spanne 0,3-0,7).
#   Eine Abweichung ueber 20 % dieser Linie laesst Gesichter verschwinden oder erfindet
#   welche (dieselbe Tabelle, Kommando 1: <0,02 gruen · 0,02-0,10 gelb · >0,10 rot).
#   Gemessen: fp16 2,60e-03, FP32 2,68e-07.
# landmark 10.0 px — die Punkte tragen Pose (S-Gate, Blicksortierung, Live-Waechter,
#   fd_front_min 0,85) und das Struktur-Mass; brauchbar ist ein Landmark bis etwa
#   1-2 px, ab 10 px ist es rot (dieselbe Tabelle, Kommando 4/5). Die Linie MUSS hier
#   ueber dem gelben Band liegen: die gesunde Xe misst in fp16 7,02 px (EIN Ausreisser
#   von 1103 Punkten, Mittel 0,087 px) und unter FP32 0,000 px — 7 px sind auf gesunder
#   Hardware normal und duerfen nie als Defekt gelten.
SCHWELLEN = {"norm": 0.10, "kosinus": 0.01, "score": 0.10, "landmark": 10.0}

EINHEIT = {"norm": "|dNorm|", "kosinus": "1-cos", "score": "max|dScore|",
           "landmark": "max|dPixel|"}

# Sollzahlen-Vergleich: RELATIVE Toleranz gegen den im Vertrag eingefrorenen CPU-Wert.
# Diese Pruefung beantwortet eine ANDERE Frage als die Schwellen oben ("rechnet die CPU
# dieses Systems ueberhaupt dasselbe Modell wie unsere?") und braucht deshalb eine eigene
# Zahl. Herleitung:
#  * Boden: fp32-Rundung. Auf dieser Maschine wiederholen zwei CPU-Laeufe derselben
#    Session bitgenau (gemessen 24.08.2026, alle sechs Modelle, Abweichung exakt 0.0).
#  * Was sie fangen MUSS, ist grob: falsches Modell -> Norm faellt von 26 auf ~0;
#    falsche Vorverarbeitung -> 11,6 statt 26 (= 55 %); der Feldfall 105,276 ist Faktor 4.
#  * Decke: die engste relative Entscheidungslinie ist die Norm mit 0,5 auf ~26 = 1,9 %.
#    1 % bleibt darunter und laesst gleichzeitig Luft fuer eine FREMDE CPU.
#  * EHRLICHE GRENZE: die Streuung zwischen VERSCHIEDENEN CPU-Modellen ist NICHT
#    gemessen (wir haben hier nur eine CPU-Klasse) — 1 % ist aus den Entscheidungslinien
#    hergeleitet, nicht aus einer Kreuzmessung. Meldet ein Feld-Startlog ein falsches
#    "reference mismatch", wird die Zahl MIT dieser Messung geweitet, nie stillschweigend.
SOLL_TOLERANZ_REL = 0.01

# Reproduzierbarkeit: zwei Laeufe derselben Session duerfen sich um hoechstens ein
# ZEHNTEL der roten Linie unterscheiden. Kein Ratewert, sondern dieselbe Logik wie die
# Schwellen: wer allein durch Wiederholung ein Zehntel des Entscheidungsabstands
# verbraucht, ist als Messgrundlage unbrauchbar. Gemessen 24.08.2026: NPU und FP32
# wiederholen bitgenau (0.0), fp16 streut auf der Norm um 0,050 zwischen zwoelf Laeufen
# derselben Session — mit dieser Regel (Norm: 0,010) faellt genau das auf.
WIEDERHOL_ANTEIL = 0.1


# ---------------------------------------------------------------- lazy Aussenwelt-Bruecken
def _face_audit():
    """face_audit LAZY — das Modul muss ohne onnxruntime importierbar bleiben."""
    import face_audit
    return face_audit


def skalen():
    """Die drei Kontrast-Skalen des Mess-Reizes. Quelle ist die Kreuzprobe selbst
    (NormMass.NORM_KREUZ_SKALEN) — nie ein zweites Literal hier. Ist face_audit nicht
    ladbar, gibt es keinen stillen Rueckfall auf eine geratene Liste, sondern die
    Ausnahme des Imports."""
    return tuple(_face_audit().NormMass.NORM_KREUZ_SKALEN)


def _pseudo_geraete():
    """face_audit.NORM_PSEUDO_GERAETE oder {} — die eine Quelle dafuer, welcher
    Geraetename in Wahrheit "dasselbe Silizium, andere Praezision" bedeutet."""
    try:
        return _face_audit().NORM_PSEUDO_GERAETE or {}
    except Exception:                                        # noqa: BLE001
        return {}


# ---------------------------------------------------------------- Vertrag lesen
def massart(name, v):
    """Welche Messgroesse gilt fuer dieses Modell? -> 'norm'|'kosinus'|'score'|'landmark'
    oder None.

    Abgeleitet aus dem VERTRAG (Rolle bzw. insightface-Taskname), nicht aus einer
    Modell-Namensliste: ein neues Modell mit bekanntem Task bekommt sein Mass damit
    automatisch, ein neues Modell mit UNBEKANNTEM Ausgang bekommt None und wird laut
    uebersprungen statt still falsch gemessen (K1)."""
    if v.get("rolle") == "vorrat":
        return "norm"                       # die Feature-Norm misst ||f||, nicht cos
    task = str(v.get("task") or "")
    if task == "detection":
        return "score"
    if task.startswith("landmark"):
        return "landmark"
    if task == "recognition":
        return "kosinus"
    if v.get("modell_schluessel"):          # eigener Recognition-Kopf ohne insightface-Task
        return "kosinus"
    return None


def _kantenlaenge(form):
    """Eingangskante aus der Vertrags-Form. (N,3,192,192) -> 192; dynamische Kanten
    (1,3,'H','W') -> DET_KANTE."""
    kanten = [d for d in (form or ()) if isinstance(d, int)]
    if len(kanten) >= 3 and kanten[-1] == kanten[-2]:
        return int(kanten[-1])
    return DET_KANTE


def modell_quelle(name, v, wurzel=None):
    """Was dem Session-Bauer als `datei` gereicht wird: der PFAD der Modell-Datei — oder
    bei der Feature-Norm die GRAPH-BYTES ihrer Variante (ort.InferenceSession nimmt
    beides).

    Warum Bytes: die Norm ist kein zweites Modell-File, sondern derselbe adaface-Graph
    mit dem Zusatz-Ausgang f (aus f/||f|| laesst sich ||f|| nicht zurueckrechnen). Die
    Graph-Operation lebt in ihrer einen Heimat (NormMass._graph_bytes) und wird hier nur
    gerufen — nachgebaut wird sie nicht.

    Pfad-Reihenfolge: erst der Ort IM IMAGE (dort laeuft der Dienst), sonst der Ort im
    Repo (Entwicklungs-/Gate-Lauf). Beide Angaben kommen aus dem Vertrag."""
    pfad = v.get("pfad_image") or ""
    if not (pfad and os.path.exists(pfad)):
        if wurzel is None:
            from core.pfade import WURZEL as wurzel          # noqa: N813
        pfad = os.path.join(wurzel, v.get("pfad_repo") or "")
    if not os.path.exists(pfad):
        raise FileNotFoundError(f"{name}: model file not found ({v.get('pfad_image')} / "
                                f"{v.get('pfad_repo')})")
    if v.get("rolle") == "vorrat":
        return _face_audit().NormMass._graph_bytes(pfad)
    return pfad


def geraete_karte(vertrag, kind, dev, norm_geraet=None):
    """Welches Geraet traegt im BETRIEB welches Modell -> {vertragsname: (kind, geraet)}.

    Das ist die Karte, die `messen()` als `backend_geraet_je_task` bekommt. Sie wird HIER
    gebildet und nicht beim Aufrufer, damit die MIXED-Verteilung nicht zum zweiten Mal
    irgendwo als Literal steht: unter openvino:MIXED liegt je Modell im Vertragsfeld
    `geraet_mixed`, welches Teil-Geraet es traegt (Deckung gegen das mixed-Dict in
    face_audit.Embedder._to_backend prueft registry.modellvertrag_deckung).

    norm_geraet: das Geraet, das die Norm-KETTE als erstes versucht (NORM_KETTE bzw.
    SUSLIK_NORM_DEVICE). Die Kette entscheidet zur Laufzeit selbst per Kreuzprobe; die
    Probe misst genau die Stufe, an der sie das tut. None = CPU."""
    karte = {}
    for name, v in (vertrag or {}).items():
        if v.get("cpu_fest"):
            karte[name] = ("cpu", None)
        elif v.get("rolle") == "vorrat":
            g = str(norm_geraet or "CPU").upper()
            karte[name] = ("cpu", None) if g == "CPU" else ("openvino", g)
        elif kind == "openvino" and str(dev).upper() == "MIXED":
            karte[name] = ("openvino", v.get("geraet_mixed") or "GPU")
        else:
            karte[name] = (kind, dev)
    return karte


# ---------------------------------------------------------------- Messen
def norm_geraet(knoten_da=None):
    """Die Stufe der Norm-KETTE, die auf DIESER Maschine als erste versucht wird.

    Die Kette (NormMass.NORM_KETTE: NPU -> GPU -> GPU_FP32 -> CPU) entscheidet zur
    Laufzeit selbst per Kreuzprobe, welche Stufe sie nimmt. Die Probe sagt NICHT voraus,
    wie das ausgeht — sie misst die Stufe, an der die Kette es entscheiden wird, und
    liefert damit genau die Zahl, die dort ueber "Geraet oder CPU" befindet.
    SUSLIK_NORM_DEVICE erzwingt eine Stufe und gewinnt deshalb auch hier.

    knoten_da(dev) -> bool ist injizierbar (Gate/Test); Default fragt die echten
    Geraeteknoten ueber face_audit.geraete_knoten_muster ab UND ob der OpenVINO-EP
    ueberhaupt im Image steckt. Beides gehoert zusammen: das cpu-Image sieht auf einer
    Intel-Maschine dieselben Geraeteknoten wie das gpu-Image, kann sie aber nicht
    benutzen — die Kette faellt dort by construction auf CPU, und die Probe darf das
    nicht als Geraete-Ausfall melden."""
    fa = _face_audit()
    wunsch = (os.environ.get("SUSLIK_NORM_DEVICE") or "").strip().upper()
    if wunsch:
        return wunsch
    if knoten_da is None:
        import glob as _glob

        def knoten_da(dev):
            try:
                import onnxruntime as ort
                if "OpenVINOExecutionProvider" not in ort.get_available_providers():
                    return False
            except Exception:                                # noqa: BLE001
                return False
            muster = fa.geraete_knoten_muster(dev)
            return bool(muster) and bool(_glob.glob(muster))
    for dev in fa.NormMass.NORM_KETTE:
        if dev == "CPU" or knoten_da(dev):
            return dev
    return "CPU"


def _eingaben(v, skalenliste):
    """Die Mess-Eingaenge dieses Modells: der Gesichtsreiz in den drei Kontrast-Skalen,
    vorverarbeitet NACH VERTRAG (Kanalordnung, mean, std, CHW, Batch 1).

    Die Vorverarbeitung ist der Stolperstein, an dem die Vorlage fast gescheitert waere:
    die beiden Landmark-Modelle sind mxnet-Exporte und wollen ROHE 0..255-Werte
    (mean 0 / std 1), fuer sie ist ein normierter Eingang voellig off-distribution und
    erzeugt Scheinabweichungen. Genau deshalb steht die Vorverarbeitung im Vertrag und
    wird hier nicht geraten."""
    import numpy as np
    reiz = _face_audit().gesichtsreiz
    e = v.get("eingang") or {}
    n = _kantenlaenge(e.get("form"))
    aus = []
    for k in skalenliste:
        img = reiz(n, k).astype(np.float32)                  # gesichtsreiz liefert BGR
        if str(e.get("kanal", "")).upper() == "RGB":
            img = img[:, :, ::-1]
        x = (img - float(e.get("mean") or 0.0)) / float(e.get("std") or 1.0)
        aus.append(np.ascontiguousarray(x.transpose(2, 0, 1)[None].astype(np.float32)))
    return aus


def _lauf(sess, eingaben):
    """Eine Session ueber alle Eingaenge -> Liste {ausgangsname: array} je Eingang.
    Die Session-Schnittstelle ist damit genau die von onnxruntime (get_inputs,
    get_outputs, run) — ein Fake im Gate braucht nicht mehr."""
    import numpy as np
    inp = sess.get_inputs()[0].name
    namen = [o.name for o in sess.get_outputs()]
    aus = []
    for x in eingaben:
        werte = sess.run(None, {inp: x})
        aus.append({n: np.asarray(w, np.float64) for n, w in zip(namen, werte)})
    return aus


def _haupt(d):
    """Der Ausgang, der die Aussage traegt: 'embedding', sonst der erste."""
    return d["embedding"] if "embedding" in d else d[next(iter(d))]


def _f_ausgang(d):
    """Der f-Ausgang der Norm-Variante: der, der NICHT 'embedding' heisst (wortgleich
    die Auswahl in NormMass.__init__/_kreuzprobe)."""
    for k, w in d.items():
        if k != "embedding":
            return w
    return _haupt(d)


def _score_ausgaenge(d):
    """Die Score-Koepfe des Detektors: die Ausgaenge mit letzter Dimension 1 (3x (N,1)
    score gegen 3x (N,4) bbox und 3x (N,10) kps, Vertrag det_10g.ausgang). Erkannt an der
    FORM statt an Ausgangs-NAMEN — die Namen sind Export-Nummern und wandern mit jedem
    Re-Export."""
    return [w for w in d.values() if getattr(w, "shape", ()) and w.shape[-1] == 1]


def kennzahl(art, d):
    """Die eine Zahl je Eingang, die als CPU-SOLLWERT eingefroren wird.

    Je Mass die BETRIEBSGROESSE, wo es eine gibt, sonst eine Pruefsumme:
      norm      ||f|| — genau die Groesse, an der der Vorrat entscheidet (real 15..30)
      score     groesster Score — genau die Groesse, an der det_thresh entscheidet
      kosinus   Summe der Betraege des Embeddings (Pruefsumme: der Kosinus braucht ZWEI
                Vektoren, taugt also nicht als eingefrorener Einzelwert)
      landmark  Summe der Betraege aller Koordinaten in px (Pruefsumme, gleiche Lage)"""
    import numpy as np
    if art == "norm":
        return float(np.linalg.norm(_f_ausgang(d).reshape(-1)))
    if art == "score":
        teile = _score_ausgaenge(d)
        return float(max(np.max(t) for t in teile)) if teile else float(np.max(_haupt(d)))
    if art == "landmark":
        return float(np.abs(_haupt(d)).sum() * LANDMARK_PX)
    return float(np.abs(_haupt(d)).sum())


def mass(art, dev_d, cpu_d):
    """Die Abweichung EINES Eingangs zwischen Geraet und CPU, in der Einheit des Masses."""
    import numpy as np
    if art == "norm":
        return abs(float(np.linalg.norm(_f_ausgang(dev_d).reshape(-1)))
                   - float(np.linalg.norm(_f_ausgang(cpu_d).reshape(-1))))
    if art == "kosinus":
        a = _haupt(dev_d).reshape(-1)
        b = _haupt(cpu_d).reshape(-1)
        na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        if na <= 0 or nb <= 0:
            return float("inf")             # ein Nullvektor ist kein "perfekter" Treffer
        return 1.0 - float(a.dot(b) / (na * nb))
    if art == "score":
        dev_t, cpu_t = _score_ausgaenge(dev_d), _score_ausgaenge(cpu_d)
        if not dev_t or len(dev_t) != len(cpu_t):
            return float(np.abs(_haupt(dev_d) - _haupt(cpu_d)).max())
        return float(max(np.abs(a - b).max() for a, b in zip(dev_t, cpu_t)))
    if art == "landmark":
        return float(np.abs(_haupt(dev_d) - _haupt(cpu_d)).max() * LANDMARK_PX)
    return float("inf")


def _soll_pruefen(v, art, ist_werte):
    """Live gemessene CPU-Kennzahlen gegen die im Vertrag eingefrorenen halten.
    -> (ok, text). Kein soll_cpu im Vertrag = (None, Grund) — NICHT still gruen (K1)."""
    soll = v.get("soll_cpu") or {}
    werte = soll.get("werte")
    if not werte:
        return None, "no frozen CPU reference in the model contract"
    if len(werte) != len(ist_werte):
        return False, (f"frozen CPU reference has {len(werte)} value(s), measured "
                       f"{len(ist_werte)}")
    schlimm = 0.0
    for s, i in zip(werte, ist_werte):
        nenner = max(abs(float(s)), 1e-9)
        schlimm = max(schlimm, abs(float(i) - float(s)) / nenner)
    if schlimm > SOLL_TOLERANZ_REL:
        return False, (f"CPU itself is off the frozen reference by {schlimm * 100:.2f}% "
                       f"(limit {SOLL_TOLERANZ_REL * 100:.0f}%): measured "
                       + " / ".join(f"{i:.4f}" for i in ist_werte) + " vs expected "
                       + " / ".join(f"{float(s):.4f}" for s in werte))
    return True, f"CPU matches the frozen reference ({schlimm * 100:.3f}% off)"


def _zeile(name, geraet, art=None, **rest):
    z = {"modell": name, "geraet": geraet, "art": art,
         "einheit": EINHEIT.get(art or ""), "schwelle": SCHWELLEN.get(art or ""),
         "mass_fp16": None, "mass_fp32": None, "reproduzierbar": None,
         "soll_ok": None, "urteil": "skip", "grund": ""}
    z.update(rest)
    return z


def _geraet_text(kind, dev):
    if kind == "cpu" or not dev:
        return "CPU"
    return f"{kind}:{dev}"


def messen(vertrag, session_bauer, zeitbudget_s=60.0, backend_geraet_je_task=None,
           jetzt=None):
    """Die Messung. -> Liste von Zeilen (eine je geprueftem Modell).

    vertrag                 core.registry.MODELL_VERTRAG (oder ein Ausschnitt/Fake)
    session_bauer(datei, geraet, precision=None) -> Session ODER wirft.
                            `datei` ist, was modell_quelle() liefert (Pfad oder
                            Graph-Bytes), `geraet` das Paar (kind, geraet) aus der
                            Karte — ("cpu", None) fuer die Referenz. Wirft der Bauer,
                            ist das ein BEFUND, kein Absturz.
    zeitbudget_s            Gesamtbudget. Vor JEDEM Modell geprueft; was nicht mehr
                            hineinpasst, wird als "not measured yet" gemeldet und beim
                            naechsten Start nachgeholt — nichts faellt still weg.
    backend_geraet_je_task  {Vertragsname: (kind, geraet)} aus geraete_karte().
    jetzt                   Zeitquelle (Test-Injektion), Default time.monotonic.

    REIHENFOLGE ist der pruefrang des Vertrags (Urteilspfad zuerst, Konzept §4): reisst
    das Budget, fehlen die unwichtigen Zeilen, nie die wichtigen.

    SPEICHER: strikt seriell. Es steht IMMER nur EINE Session im Prozess — die
    CPU-Ausgaenge werden als Zahlen behalten, die CPU-Session danach freigegeben, erst
    dann entsteht die Geraete-Session. Zwei gleichzeitige Sessions SIND die Bauspitze
    (gemessen 24.08.2026 an der Feature-Norm: 2,7 GB Geraet+CPU gegen 1,1 GB CPU allein),
    und vier gleichzeitig offene Modelle auf einer 24-EU-iGPU haben in einem Probelauf
    den Erkennungs-Kosinus von 0,999753 auf 0,857 gedrueckt — die Messung verfaelschte
    sich selbst."""
    jetzt = jetzt or time.monotonic
    t0 = jetzt()
    karte = dict(backend_geraet_je_task or {})
    aus = []
    for name, v in sorted((vertrag or {}).items(),
                          key=lambda kv: (kv[1].get("pruefrang") or 99, kv[0])):
        if not v.get("geladen") or v.get("pruefrang") is None:
            continue                        # z.B. genderage: laeuft nicht mit, kein Thema
        if name not in karte:
            # Kein Geraet deklariert heisst NICHT "also CPU" — es heisst, die Karte ist
            # unvollstaendig. Das wird gesagt, nicht geraten (K1).
            aus.append(_zeile(name, "?", massart(name, v), urteil="warn",
                              grund="no operating device declared for this model — "
                                    "not checked"))
            continue
        kind, dev = karte[name]
        geraet = _geraet_text(kind, dev)
        if v.get("cpu_fest") or kind == "cpu":
            # "CPU by design" bekommt KEINE Zahl (Konzept §4). Die Geraetedrift dieser
            # Modelle wurde gemessen und ist unkritisch — CPU ist dort Sparsamkeit.
            # ZWEI VERSCHIEDENE Gruende, und sie duerfen nicht denselben Satz bekommen:
            # cpu_fest ist eine Eigenschaft des MODELLS, ein CPU-Backend eine des
            # SYSTEMS (cpu-Image, kein Beschleuniger, Placement auf CPU) — wer im
            # Startlog liest "cpu by design", waehrend in Wahrheit sein Beschleuniger
            # fehlt, sucht an der falschen Stelle.
            aus.append(_zeile(name, geraet, massart(name, v), urteil="skip",
                              grund=("cpu by design — no accelerator to check"
                                     if v.get("cpu_fest") else
                                     "runs on the CPU with this backend — nothing to "
                                     "cross-check against")))
            continue
        art = massart(name, v)
        if art is None:
            aus.append(_zeile(name, geraet, None, urteil="warn",
                              grund="no measure defined for this output scale — not checked"))
            continue
        rest = zeitbudget_s - (jetzt() - t0)
        if rest <= 0:
            aus.append(_zeile(name, geraet, art, urteil="skip",
                              grund="not measured yet (time budget) — continues on a "
                                    "later start"))
            continue
        try:
            aus.append(_ein_modell(name, v, art, kind, dev, geraet, session_bauer))
        except Exception as ex:                              # noqa: BLE001
            # Auffangnetz: EIN kaputtes Modell darf die Probe der anderen nicht
            # mitnehmen, und ein Absturz hier darf den Start nicht reissen.
            aus.append(_zeile(name, geraet, art, urteil="warn",
                              grund=f"probe crashed for this model "
                                    f"({type(ex).__name__}: {str(ex)[:100]})"))
    return aus


def _ein_modell(name, v, art, kind, dev, geraet, session_bauer):
    """Ein Modell: CPU-Referenz, Betriebsgeraet in Voreinstellung, bei OpenVINO
    zusaetzlich FP32 — jede Geraete-Messung zweimal."""
    try:
        skalenliste = skalen()
        quelle = modell_quelle(name, v)
        eingaben = _eingaben(v, skalenliste)
    except Exception as ex:                                  # noqa: BLE001
        return _zeile(name, geraet, art, urteil="warn",
                      grund=f"input/model not available ({type(ex).__name__}: "
                            f"{str(ex)[:100]})")
    # --- 1) CPU-Referenz. Nur die AUSGAENGE ueberleben, die Session nicht.
    try:
        s = session_bauer(quelle, ("cpu", None))
        cpu_aus = _lauf(s, eingaben)
    except Exception as ex:                                  # noqa: BLE001
        return _zeile(name, geraet, art, urteil="warn",
                      grund=f"cpu reference session failed ({type(ex).__name__}: "
                            f"{str(ex)[:100]}) — nothing to compare against")
    finally:
        s = None
        gc.collect()
    cpu_werte = [kennzahl(art, d) for d in cpu_aus]
    soll_ok, soll_text = _soll_pruefen(v, art, cpu_werte)

    def _geraet_messen(precision):
        """-> (mass, reproduzierbar, fehler). mass=None heisst: nicht gemessen."""
        sess = None
        try:
            sess = session_bauer(quelle, (kind, dev), precision)
            laeufe = []
            for _ in range(2):              # ZWEIMAL im selben Lauf (Konzept §4)
                dev_aus = _lauf(sess, eingaben)
                laeufe.append(max(mass(art, a, b) for a, b in zip(dev_aus, cpu_aus)))
            grenze = SCHWELLEN[art] * WIEDERHOL_ANTEIL
            return max(laeufe), abs(laeufe[0] - laeufe[1]) <= grenze, None
        except Exception as ex:                              # noqa: BLE001
            return None, None, f"{type(ex).__name__}: {str(ex)[:100]}"
        finally:
            del sess
            gc.collect()

    m16, rep16, fehler16 = _geraet_messen(None)
    m32 = rep32 = fehler32 = None
    if kind == "openvino" and not _ist_fp32(dev):
        # Die Praezisions-Achse gibt es NUR bei OpenVINO; CUDA/MIGraphX kennen die
        # Option nicht (Konzept §4: "ein Lauf ohne Praezisions-Achse").
        m32, rep32, fehler32 = _geraet_messen("FP32")
    return _urteilen(name, v, art, geraet, dev, m16, rep16, fehler16,
                     m32, rep32, fehler32, soll_ok, soll_text, cpu_werte)


def _ist_fp32(dev):
    """Ist dieses Geraet schon per Definition FP32 (Pseudo-Geraet GPU_FP32)? Dann waere
    ein zweiter FP32-Lauf dieselbe Messung."""
    p = _pseudo_geraete().get(str(dev or "").upper()) or {}
    return str(p.get("precision", "")).upper() == "FP32"


def _urteilen(name, v, art, geraet, dev, m16, rep16, fehler16, m32, rep32, fehler32,
              soll_ok, soll_text, cpu_werte):
    """Aus den Zahlen ein Urteil. Vier Werte, jeder mit Klartext-Grund:

    fail  KLAR KAPUTT — beide Praezisionen jenseits der roten Linie (bzw. die einzige
          gemessene, wo es keine zweite gibt), ODER die CPU selbst weicht von den
          eingefrorenen Sollzahlen ab ("reference mismatch": das ist der Fall, den ein
          reiner Geraet-gegen-CPU-Vergleich nie sieht). Nur DAS zaehlt in startup_fails.
    warn  die Messung selbst traegt nicht: Geraet nicht baubar, nicht reproduzierbar,
          keine Sollzahlen — oder die Voreinstellung ist unbrauchbar, waehrend FP32
          sauber rechnet (ABWEICHUNG vom Konzept-Wortlaut, bewusst und deklariert: das
          ist genau der Feldfall, dessentwegen die FP32-Stufe existiert, und er darf
          nicht als gruene Zeile untergehen — geschaltet wird trotzdem nichts).
    ok    im Rahmen.
    skip  nichts zu messen (cpu by design, Budget)."""
    rot = SCHWELLEN[art]
    z = _zeile(name, geraet, art, mass_fp16=m16, mass_fp32=m32,
               reproduzierbar=(None if rep16 is None and rep32 is None
                               else bool(rep16 is not False and rep32 is not False)),
               soll_ok=soll_ok)
    if soll_ok is False:
        z.update(urteil="fail", grund="reference mismatch — " + soll_text)
        return z
    if m16 is None and m32 is None:
        z.update(urteil="warn",
                 grund=f"device session failed ({fehler16 or fehler32}) — not measured, "
                       f"the model runs wherever the service places it")
        return z
    kaputt16 = m16 is not None and m16 > rot
    kaputt32 = m32 is not None and m32 > rot
    teile = [f"{EINHEIT[art]} {m16:.4f}" if m16 is not None else f"default {fehler16}"]
    if m32 is not None:
        teile.append(f"FP32 {m32:.4f}")
    elif fehler32:
        # Gemessen 24.08.2026: die Intel-NPU nimmt precision=FP32 NICHT an, sie sagt es
        # sogar woertlich ("[OpenVINO] Unsupported inference precision is selected. NPU
        # only supports FP16, ACCURACY") und der Provider bindet dann gar nicht erst.
        # Das ist kein Defekt, sondern eine Eigenschaft des Geraets — es bekommt deshalb
        # einen Klartext-Halbsatz und nicht die rohe Ausnahme, die im Startlog wie ein
        # Ausfall des MODELLS aussaehe.
        teile.append("no FP32 leg on this device")
    teile.append(f"limit {rot:g}")
    if soll_ok is None:
        teile.append("no frozen CPU reference")
    kern = " · ".join(teile)
    if kaputt16 and (kaputt32 or m32 is None):
        z.update(urteil="fail",
                 grund=f"device does NOT compute what the CPU computes — {kern}")
        return z
    if kaputt16 and not kaputt32:
        z.update(urteil="warn",
                 grund=f"default precision (fp16) unusable on this device, FP32 is "
                       f"clean — {kern}")
        return z
    if z["reproduzierbar"] is False:
        z.update(urteil="warn",
                 grund=f"not reproducible — two runs of the same session disagree; "
                       f"{kern}")
        return z
    if soll_ok is None:
        z.update(urteil="warn", grund=f"{kern} — {soll_text}")
        return z
    z.update(urteil="ok", grund=kern)
    return z


def logzeile(z):
    """Eine Zeile fuers Docker-Log (englisch wie der uebrige Startup-Block).
    GEDRUCKT WIRD IMMER VOM HAUPTPROZESS — der Messprozess liefert nur Daten
    (User-Entscheid: sonst steht es nicht im Docker-Log)."""
    return f"{z['modell']:<18} {str(z['geraet']):<14} {z['grund']}"
