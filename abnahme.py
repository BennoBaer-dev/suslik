#!/usr/bin/env python3
"""Abnahme-Suite (Plan v1.0 AP0): Kalibrier-Neutralitaet nach jedem Umbau beweisen.

Rechnet die archivierten Fixpunkt-Events gegen den EINGEFRORENEN Referenz-Snapshot
(samples/abnahme_fixpunkte/refsnap_v1.npz — NIE der lebende refcache) und vergleicht
mit den eingefrorenen Soll-Werten:

  abnahme.py soll                # Soll-Werte (neu) einfrieren -> soll.<backend>.json
  abnahme.py                     # Pruefen: Fixpunkte exakt, Fremden-GT 0x (0.38 UND 0.35)
  abnahme.py --nach-enrollment   # nach gewollter Basis-Aenderung: Eigen-Fixpunkte
                                 # duerfen nur GLEICH/BESSER sein, Fremde weiter 0x
                                 # (danach mit 'soll' neuen Stand einfrieren)

SOLL-STAND JE BACKEND (25.07.): Die Soll-Werte gelten immer nur fuer das Backend, auf dem sie
eingefroren wurden. Verschiedene Execution Provider (CPU, OpenVINO, CUDA) rechnen dieselbe
Faltung numerisch minimal verschieden — gemessen 0.464 (CPU) gegen 0.449 (CUDA) am selben Clip,
also 0.015 bei TOL 0.005. Die ENTSCHEIDUNG (win38/win35) war dabei identisch; nur der rohe
Score wandert. Wer trotzdem gegen ein fremdes Soll prueft, vergleicht Aepfel mit Birnen und
bekommt ein rotes Gate ohne echten Befund — genau das passierte beim 0.1.0.22-Release auf dem
CUDA-Notebook, wo dieselbe Abweichung auch mit der ALTEN Version auftrat.
Die Toleranz wird deshalb NICHT aufgeweicht (sie wuerde dann echte Verschlechterungen
durchwinken): stattdessen bekommt jedes Backend seinen eigenen, auf seiner Maschine
eingefrorenen Stand, und ohne diesen Stand ist das Ergebnis ROT statt "geht schon".

Exit 0 = gruen, 1 = ROT (Umbau hat die Kalibrierung verschoben -> nicht mergen).
det_size-Reihenfolge beachtet: Snapshot ist fertig embedded, Video laeuft mit 1280."""
import os, sys, json
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from face_audit import Embedder

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIV = os.path.join(HERE, "samples", "abnahme_fixpunkte")
WIN_THRESH, WIN_MIN = 0.38, 2
FPS_SAMPLE = 3.0
TOL = 0.005            # numerische Toleranz auf max-Scores (Lib-Updates), win3s exakt
BACKEND_KEY = "§backend"   # im Soll mitgeschrieben; '§' ist per Namens-Regex kein Personenname


def backend_kennung(emb):
    """Kennung des TATSAECHLICH gebundenen Backends, z.B. 'cpu', 'openvino-GPU', 'cuda'.

    Bewusst aus den realen Providern der Sessions abgeleitet und nicht aus dem Wunsch
    (VERIFY_BACKEND): onnxruntime faellt bei Treiber-/Versions-Mismatch STILL auf CPU zurueck.
    Wuerde die Kennung dem Wunsch folgen, schriebe ein solcher Lauf seine CPU-Zahlen in
    'soll.cuda.json' — und der Test waere fuer immer gegen die falschen Werte geeicht."""
    prov = set()
    for m in getattr(emb.app, "models", {}).values():
        s = getattr(m, "session", None)
        if s is not None:
            prov.update(s.get_providers())
    r = getattr(emb, "_rec", None)
    if r is not None and hasattr(r, "get_providers"):
        prov.update(r.get_providers())
    if "CUDAExecutionProvider" in prov:
        return "cuda"
    if "OpenVINOExecutionProvider" in prov:
        _, dev = getattr(emb, "_backend", ("", ""))
        return f"openvino-{dev or 'GPU'}"
    return "cpu"


def soll_pfad(kennung):
    return os.path.join(ARCHIV, f"soll.{kennung}.json")


def win3s(punkte, thresh):
    ts = sorted(punkte)
    return max((sum(1 for (t, s) in ts if t0 <= t <= t0 + 3.0 and s >= thresh)
                for t0, _ in ts), default=0)


def analysiere(emb, refs, vid):
    """Kompakte, deterministische Nachbildung der analyze-Pipeline (nur Scores).
    Seit W1 (0.1.0.35) ueber decode.FrameIter — dieselbe Frame-Quelle wie die Produktion,
    sonst prueft das Gate einen anderen Decode-Pfad als den, der live urteilt (Plan-QS R5).
    Semantik (step, i/fps) bit-exakt unveraendert; die Soll-Staende gelten weiter."""
    from decode import FrameIter
    nn = lambda v: {p: float((M @ v).max()) if len(M) else -1.0 for p, M in refs.items()}
    it = FrameIter(vid, FPS_SAMPLE)
    emb.set_det_size(emb.ar_det_size(it.breite, it.hoehe))   # H4: wie die Produktion (R5)
    punkte = {p: [] for p in refs}
    for i, frame in it:
        for fc in emb.app.get(frame):
            sc = nn(np.asarray(fc.normed_embedding, dtype=np.float32))
            for p, s in sc.items():
                punkte[p].append((i / it.fps, s))
    return {p: {"max": round(max((s for _, s in pts), default=-1.0), 3),
                "win38": win3s(pts, 0.38), "win35": win3s(pts, 0.35)}
            for p, pts in punkte.items()}


def vergleiche(ist, soll, fixpunkte, fremde, modus):
    """Der Urteils-Kern des Waechters als REINE Funktion (Task #10: testbar, KeyError-fest).
    -> (fehler, neue_personen). Verhalten fuer Bestandsfaelle unveraendert (Charakterisierung
    ueber qs-Testvektoren); Personen ohne Soll-Eintrag werden gesammelt statt zu crashen."""
    fehler, neue_personen = [], set()
    for eid in fixpunkte:
        # Review .57: ein KOMPLETT fehlendes Event im Soll ist KEIN Neu-Personen-Fall,
        # sondern ein fehlender Soll-Stand (neuer Fixpunkt-Clip/beschaedigtes Soll) —
        # frueher erzwang der KeyError das Einfrieren, ein gruener 0-Vergleiche-Lauf
        # waere stiller Verlust. Laut UND rot:
        if eid not in soll:
            fehler.append(f"FIXPUNKT OHNE SOLL-WERTE: {eid} — 'abnahme.py soll' fahren")
    for eid in fremde:                                     # Fremden-Gate: IMMER 0x, beide Schwellen
        for p, v in ist[eid].items():
            if v["win38"] >= WIN_MIN or v["win35"] >= WIN_MIN:
                fehler.append(f"FREMDEN-GATE VERLETZT: {eid} {p} win38={v['win38']} win35={v['win35']}")
    for eid in fixpunkte:
        for p, v in ist[eid].items():
            s = soll.get(eid, {}).get(p)
            if s is None:
                neue_personen.add(p)
                continue
            if modus == "--nach-enrollment":
                # Task #10, Praezisierung auf die REGEL-ABSICHT (Befund 28.07.): der Soll
                # entsteht aus dem eingefrorenen Snapshot, dieser Modus re-embeddet den
                # LEBENDEN Master — sub-Schwellen-max-Werte rauschen dadurch um ~±0,02
                # (urteils-neutral, win38 beidseitig 0). Deshalb: win38-Monotonie IMMER;
                # der max-Drift zaehlt nur dort, wo er Urteile traegt (Person auf diesem
                # Fixpunkt bestaetigt, soll-win38 >= WIN_MIN). Kein Aufweichen der
                # Entscheidungs-Wache — nur Ende des Fehlalarms auf Mess-Rauschen.
                if v["win38"] < s["win38"]:
                    fehler.append(f"VERSCHLECHTERT: {eid} {p} {v} < soll {s}")
                elif s["win38"] >= WIN_MIN and v["max"] < s["max"] - TOL:
                    fehler.append(f"VERSCHLECHTERT: {eid} {p} {v} < soll {s}")
            else:
                if v["win38"] != s["win38"] or abs(v["max"] - s["max"]) > TOL:
                    fehler.append(f"ABWEICHUNG: {eid} {p} ist {v} != soll {s}")
    return fehler, neue_personen


def lade_master_refs(emb):
    """Referenzen aus dem LEBENDEN Master embedden (det 320!) — fuer den Drift-Waechter
    nach Enrollment: der muss die NEUE Basis pruefen, nicht den eingefrorenen Snapshot."""
    from sync_refs import master_stand, MASTER
    refs = {}
    for p, dateien in master_stand().items():
        V = []
        for f in dateien:
            img = cv2.imread(os.path.join(MASTER, p, f))
            if img is None:
                continue
            v = emb.embed(img)
            if v is not None:
                V.append(np.asarray(v, dtype=np.float32))
        refs[p] = np.asarray(V, dtype=np.float32)
    return refs


def entscheidungen(ist):
    """Nur die ENTSCHEIDUNGEN (win38/win35) je Event+Person — ohne die rohen Scores.
    Das ist der Teil, der zwischen Backends identisch sein MUSS; die Scores duerfen
    numerisch wandern."""
    return {eid: {p: (v["win38"], v["win35"]) for p, v in werte.items()}
            for eid, werte in ist.items()}


def andere_soll_staende(kennung):
    """Alle bereits eingefrorenen Soll-Staende ANDERER Backends (fuer den Quervergleich)."""
    treffer = {}
    for f in sorted(os.listdir(ARCHIV)):
        if f.startswith("soll.") and f.endswith(".json") and f != f"soll.{kennung}.json":
            # Das alte, backend-lose soll.json bleibt als Quervergleich nuetzlich (seine
            # Entscheidungen sind geprueft), bekommt aber einen sprechenden Namen statt "".
            k = f[len("soll."):-len(".json")] or "soll.json (alt, ohne Backend)"
            try:
                treffer[k] = json.load(open(os.path.join(ARCHIV, f)))
            except Exception:
                pass                                   # unlesbarer Altstand blockiert nicht
    return treffer


def main():
    modus = sys.argv[1] if len(sys.argv) > 1 else "pruefen"
    # Quelltext-Release: das Fixpunkt-Archiv (echte Clips) wird bewusst NICHT
    # mitveroeffentlicht. Ohne Archiv ist das hier kein Gate — sauber sagen und
    # neutral enden statt FileNotFoundError (Fremdnutzer-Falle, Scrub .92-alpha).
    if not os.path.isdir(ARCHIV):
        print("no acceptance fixtures installed (samples/abnahme_fixpunkte/ missing) — "
              "this suite verifies the author's frozen fixpoint clips and is skipped "
              "on installations without them. Nothing to do.")
        sys.exit(0)
    ev = json.load(open(os.path.join(ARCHIV, "events.json")))
    fixpunkte, fremde = ev["fixpunkte"], ev["fremde"]
    emb = Embedder()
    if modus == "--nach-enrollment":
        refs = lade_master_refs(emb)              # lebender Master, det 320 VOR dem Umschalten
    else:
        z = np.load(os.path.join(ARCHIV, "refsnap_v1.npz"), allow_pickle=True)
        refs = {p: z[p].astype(np.float32) for p in z.files if p != "meta"}
    emb.set_det_size((1280, 1280))

    ist = {}
    for eid in dict.fromkeys(fixpunkte + fremde):          # dedupliziert, Reihenfolge stabil
        vid = os.path.join(ARCHIV, eid + ".mp4")
        if not os.path.exists(vid):
            print(f"ROT: Archiv-Clip fehlt: {eid}")
            sys.exit(1)
        ist[eid] = analysiere(emb, refs, vid)
        top = sorted(ist[eid].items(), key=lambda x: -x[1]["max"])[:2]
        print(f"  {eid}: " + ", ".join(f"{p} {v['max']:+.2f}/{v['win38']}x" for p, v in top))

    kennung = backend_kennung(emb)
    SOLL = soll_pfad(kennung)
    print(f"\nBackend (real gebunden): {kennung}   Soll-Stand: {os.path.basename(SOLL)}")

    if modus == "soll":
        # Quervergleich gegen bereits eingefrorene Backends: die ENTSCHEIDUNGEN muessen
        # uebereinstimmen. Sonst wuerde ein kaputter Build hier stillschweigend zur neuen
        # Wahrheit eingefroren — der Test bewiese danach nur noch sich selbst.
        meine = entscheidungen(ist)
        abweichungen = []
        for k, fremd in andere_soll_staende(kennung).items():
            fremd_e = entscheidungen({e: w for e, w in fremd.items() if e != BACKEND_KEY})
            for eid, personen in fremd_e.items():
                for p, ent in personen.items():
                    if eid in meine and p in meine[eid] and meine[eid][p] != ent:
                        abweichungen.append(f"gegen {k}: {eid} {p} ist {meine[eid][p]} != {ent}")
        if abweichungen and "--trotz-abweichung" not in sys.argv:
            print("\nROT — nicht eingefroren: die ENTSCHEIDUNGEN weichen von einem anderen "
                  "Backend ab.\nZwischen Backends duerfen die Scores wandern, die Entscheidungen "
                  "nicht. Das ist ein echter Befund, kein Numerik-Rauschen:")
            [print("  " + a) for a in abweichungen]
            print("\nUrsache klaeren. Nur wenn die Aenderung GEWOLLT ist (z.B. nach Enrollment "
                  "auf allen Backends):\n  abnahme.py soll --trotz-abweichung")
            sys.exit(1)
        json.dump({BACKEND_KEY: kennung, **ist}, open(SOLL, "w"), ensure_ascii=False, indent=1)
        print(f"Soll-Werte eingefroren -> {SOLL}"
              + (f"  (Entscheidungen decken sich mit: {', '.join(andere_soll_staende(kennung))})"
                 if andere_soll_staende(kennung) else ""))
        return

    if not os.path.exists(SOLL):
        # KEIN Rueckfall auf den Stand eines anderen Backends. Genau dieser Rueckfall war der
        # Fehler: auf dem CUDA-Notebook wurde gegen die CPU-Zahlen geprueft und das Gate war
        # rot, obwohl nichts kaputt war. Fehlende Sim-Quelle = nicht bestanden (Runbook).
        print(f"\nROT — kein Soll-Stand fuer Backend '{kennung}' auf dieser Maschine.\n"
              f"  Erwartet: {SOLL}\n"
              f"  Ein Soll-Stand eines ANDEREN Backends gilt hier nicht (andere Execution Provider\n"
              f"  rechnen numerisch minimal anders — gemessen 0.464 CPU/OpenVINO gegen 0.449 CUDA).\n"
              f"  Einmalig auf DIESER Maschine einfrieren:  abnahme.py soll")
        sys.exit(1)
    soll = {e: w for e, w in json.load(open(SOLL)).items() if e != BACKEND_KEY}
    fehler, neue_personen = vergleiche(ist, soll, fixpunkte, fremde, modus)
    if neue_personen:
        # Task #10 (28.07.): Personen, die NACH dem Einfrieren des Soll-Stands angelernt
        # wurden, haben dort keine Werte — vorher lief die Schleife hier in einen KeyError
        # und der Waechter war fuer JEDEN Lauf tot. Kein stiller Vergleich, kein Crash:
        # LAUT ausweisen, Urteil nur ueber die Schnittmenge.
        print(f"\nHINWEIS — ohne Soll-Werte (neu seit dem Einfrieren, KEIN Drift-Urteil): "
              + ", ".join(sorted(neue_personen)))
        print("  Bei der naechsten GEWOLLTEN Basis-Aenderung 'abnahme.py soll' fahren, "
              "dann sind sie erfasst.")
    if fehler:
        print("\nROT — Kalibrierung verletzt:")
        [print("  " + f) for f in fehler]
        sys.exit(1)
    print(f"\nGRUEN — {len(fixpunkte)} Fixpunkte {'monoton ok' if modus == '--nach-enrollment' else 'exakt'}, "
          f"{len(fremde)} Fremden-Events 0x (0.38 und 0.35).")


if __name__ == "__main__":
    main()
