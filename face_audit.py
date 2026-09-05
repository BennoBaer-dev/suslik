#!/usr/bin/env python3
"""
Frigate Face-Library Audit -- Prototyp v2
=========================================
Read-only. Holt alle GELERNTEN Referenzgesichter aus Frigate, rechnet
ausgerichtete Face-Embeddings (InsightFace buffalo_l: Detection+Alignment+ArcFace)
und meldet, was Frigate selbst NICHT prueft:

  0. Kein Gesicht detektierbar   -> klarste Loesch-Kandidaten
  A. Personen-Kohaerenz          -> wie einheitlich ist eine Person gelernt
  B. Fehllabel / schaedlich       -> Bild aehnelt fremder Person >= eigener
  C. Verwechslungs-Matrix         -> welche Personen sind sich zu aehnlich
  D. Qualitaets-Flags             -> zu klein / zu unscharf

Zu jedem auffaelligen Bild: direkt anklickbare Frigate-URL (Bild sofort sichtbar,
bleibt im lokalen Netz) + Aufnahmedatum (zum Wiederfinden in der Frigate-UI).
Erzeugt zusaetzlich eine HTML-Galerie (Bilder via Frigate-URL eingebunden).

Greift NUR lesend auf Frigate zu. Aendert NICHTS. Loeschen bleibt separate,
bestaetigte Aktion.
"""
import contextlib as _contextlib
import glob as _glob
import threading as _threading      # E3c: Schloss der Init-Kappung, s. _IF_KAPPUNG_SCHLOSS
import os, sys, json, argparse, urllib.request, urllib.parse, re, datetime, html
import numpy as np
import cv2

FRIGATE = os.environ.get("FRIGATE_URL", "")   # kein Default auf eine konkrete IP (Public-Image); Runtime setzt FRIGATE_URL

# ---------------------------------------------------------------- Recognition-Modell
HIER = os.path.dirname(os.path.abspath(__file__))
# Umschaltbares Recognition-Modell (Shootout 19.07.: AdaFace IR101 trennt unser eigenes
# Material messbar sicherer als buffalo_l, +35 % Marge, einige Personen deutlich besser).
# Detektion+Alignment bleiben IMMER insightface/SCRFD + norm_crop; getauscht wird NUR der
# ArcFace-Kopf. "buffalo" = insightface-eigenes w600k_r50 (RGB, unveraendert). "adaface" =
# eigenes ONNX auf dem norm_crop-112-Crop, Preprocessing BGR + (x-127.5)/127.5 (aus dem
# offiziellen AdaFace-Checkpoint exportiert, ONNX-vs-PyTorch cos 1.0000 verifiziert).
MODELLE = {
    "buffalo": {"art": "insightface"},
    "adaface": {"art": "onnx",
                "onnx": os.path.join(HIER, "models", "adaface_ir101_webface12m.onnx"),
                "bgr": True, "mean": 127.5, "std": 127.5},
}


def aktuelles_modell():
    """Konfiguriertes Modell OHNE etwas zu laden — fuer cache-nur-Leser (anlernen), damit sie
    Modell-Mix im refcache erkennen. Quelle: Umgebungsvariable VERIFY_MODELL (von verifyd
    gesetzt), sonst der modell-Schluessel aus verifyd.yaml (damit Standalone-Tools automatisch
    dem Produktions-Modell folgen und den Cache nicht auf buffalo zurueckwerfen), sonst
    'buffalo' als bekannter Fallback."""
    m = os.environ.get("VERIFY_MODELL")
    if not m:
        try:
            import yaml
            m = (yaml.safe_load(open(os.path.join(HIER, "verifyd.yaml"))) or {}).get("modell")
        except Exception:
            m = None
    m = (m or "buffalo").lower()
    return m if m in MODELLE else "buffalo"


def resolve_backend(spec=None):
    """ML-Backend-Spec -> (kind, dev). Quelle-Prioritaet: expliziter spec (Embedder device=) >
    VERIFY_BACKEND > OV_DEVICE (Abwaertskompat) > leer=cpu. Formen:
      'openvino:GPU'|'openvino:NPU'|'openvino:MIXED' (Intel), 'cuda'|'cuda:0' (Nvidia), 'cpu' (ueberall).
    Ein blosses BEKANNTES OV-Device (GPU/NPU/MIXED/AUTO, alte OV_DEVICE-Welt) -> OpenVINO. Ein
    unbekannter Token (Tippfehler wie 'cudaa') wird NICHT still zu einem OV-Device gedeutet, sondern
    als unbekanntes Backend zurueckgegeben -> _ort_session warnt laut und faellt auf CPU zurueck."""
    # P3.1: Mengen aus core.registry (EINE Quelle statt Literal-Streuung); die SEMANTIK
    # ist wortgleich uebernommen und per Charakterisierungs-Vektoren im Gate eingefroren
    # (unbekannte Token bleiben LAUT-Fallthrough, OV_DEVS-Abwaertsweg bleibt).
    from core.registry import kind_von, OV_DEVS, default_device
    s = (spec or os.environ.get("VERIFY_BACKEND") or os.environ.get("OV_DEVICE") or "").strip()
    if not s:
        return ("cpu", None)
    if ":" in s:
        kind, dev = s.split(":", 1)
        kind, bekannt = kind_von(kind)
    elif s.upper() in OV_DEVS and kind_von(s)[1] is False:
        kind, dev, bekannt = "openvino", s.upper(), True   # bekanntes OV-Device (Abwaertskompat OV_DEVICE)
    else:
        kind, bekannt = kind_von(s)
        dev = ""
    if not bekannt:
        return (kind, "")                              # unbekannter Token (Typo) -> _ort_session: Warnung + CPU
    if kind == "openvino":
        return ("openvino", (dev or default_device("openvino")).upper())
    if kind == "cpu":
        return ("cpu", None)
    return (kind, dev or default_device(kind))        # cuda/migraphx: Geraetenummer, Default aus Registry


_ORT_THREADS = None
_THREADS_BENCH = None            # Ergebnis der Selbstmessung (fuer /health, Gate)
# .505 E4 (05.09.2026, Widerleger W-E3c Notiz 7): Schloss um Cache-Pruefung UND
# Messung in _ort_thread_opts. Ohne es sahen drei parallele Kaltaufrufe alle
# `_ORT_THREADS is None`, massen alle (je ~1,3 s) und kamen dabei auf
# ABWEICHENDE Ergebnisse — gemessen 6 gegen 1 Thread, der letzte Schreiber
# gewann. Das ist beides falsch: die Messung wird verdreifacht (und misst dabei
# sich selbst, weil drei Benches um dieselben Kerne konkurrieren), und welche
# Threadzahl am Ende steht, entscheidet der Zufall. Lock statt RLock: hier laeuft
# kein Weg aus dem gesperrten Abschnitt in sich selbst zurueck (`_threads_messen`
# baut ueber `ort.InferenceSession` mit eigenen Optionen, nie ueber
# `_ort_thread_opts`), und die Kappungs-Klammer haelt ihr eigenes Schloss zu
# diesem Zeitpunkt nicht mehr (s. _insightface_sessions_gekappt).
_ORT_THREADS_SCHLOSS = _threading.Lock()


def _threads_cache_pfad():
    """Wo die gemessene Threadzahl liegt — im Datenordner, nicht im Image
    (sie gehoert zur MASCHINE, nicht zum Build). Ohne VERIFY_DATA_DIR (nackter
    CLI-Lauf) gibt es keinen Cache und der Bench laeuft je Prozess einmal."""
    dd = (os.environ.get("VERIFY_DATA_DIR") or "").strip()
    return os.path.join(dd, "state", "cpu_threads.json") if dd else None


def _threads_schluessel(kerne):
    """Was die Messung gueltig macht: erlaubte Kernzahl + CPU-Modell + Platzzahl.
    Aendert sich eines (anderer Wirt, andere cgroup-Maske, mehr Analyse-Plaetze),
    wird neu gemessen.

    Die Platzzahl gehoert hier hinein, seit die Analyse mehrere Plaetze haben kann
    (Konzept Parallel-Analyse §5.3): der Bench misst die beste Threadzahl fuer EINEN
    Prozess und legt sie ab. Ohne die Platzzahl im Schluessel forderten zwei Worker
    denselben gecachten Wert an, also gemeinsam die doppelte Threadzahl — auf
    Maschinen, wo der Bench `kerne` oder `kerne//2` gewaehlt hat, ist das
    Ueberbuchung, und der Cache haette sie still konserviert."""
    modell = ""
    try:
        with open("/proc/cpuinfo") as f:
            for z in f:
                if z.startswith("model name"):
                    modell = z.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    try:
        plaetze = max(1, int(os.environ.get("SUSLIK_ANALYSE_PLAETZE") or 1))
    except ValueError:
        plaetze = 1
    # Bei einem Platz bleibt der Schluessel bitgleich zu vorher — bestehende
    # Cache-Dateien behalten ihre Gueltigkeit und werden nicht neu vermessen.
    return f"{kerne}|{modell}" if plaetze == 1 else f"{kerne}|{modell}|p{plaetze}"


def _bench_graph(n=256, stufen=4):
    """Winziger ONNX-Graph fuer die Threadzahl-Messung: eine Kette aus
    MatMul+Relu. Bewusst KEIN Modell von Platte — der Bench soll nichts laden,
    nichts cachen und auf jeder Variante gleich aussehen. MatMul ist die
    Operation, die onnxruntime ueber den Intra-Op-Pool verteilt; genau dort
    entsteht der gemessene Hybrid-Effekt."""
    import onnx
    from onnx import helper, TensorProto
    W = np.linspace(-0.05, 0.05, n * n, dtype=np.float32).reshape(n, n)
    init = helper.make_tensor("W", TensorProto.FLOAT, [n, n],
                              W.tobytes(), raw=True)
    knoten, ein = [], "X"
    for i in range(stufen):
        knoten.append(helper.make_node("MatMul", [ein, "W"], [f"m{i}"]))
        knoten.append(helper.make_node("Relu", [f"m{i}"],
                                       ["Y" if i == stufen - 1 else f"r{i}"]))
        ein = f"r{i}"
    g = helper.make_graph(
        knoten, "threadbench",
        [helper.make_tensor_value_info("X", TensorProto.FLOAT, [n, n])],
        [helper.make_tensor_value_info("Y", TensorProto.FLOAT, [n, n])],
        [init])
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 13)])
    m.ir_version = 8            # konservativ: laeuft auf jeder ORT-Version im Haus
    return m.SerializeToString(), n


def _bench_modell():
    """Das ECHTE Netz fuer den Bench, wenn es im Image liegt -> Pfad|None.

    2d106det ist Teil des buffalo_l-Pakets und liegt deshalb in ALLEN FUENF
    Images (StrukturMass nennt genau diese Quelle — kein zweites Literal).
    Ein echtes Faltungsnetz misst die Threadzahl belastbarer als ein
    synthetischer Graph: gemessen 31.08. auf dieser Maschine (12 Kerne
    zugeteilt, im Leerlauf) liegt das Optimum bei 6-8 Threads, 12 Threads
    kosten 1,2- bis 2-fach mehr — genau der Effekt, um den es geht. Fehlt die
    Datei (Fremdumgebung, nackter Checkout), faellt der Bench auf den
    synthetischen Graphen zurueck."""
    try:
        p = os.path.join(StrukturMass.MODELL_DIR, StrukturMass.MODELL_DATEI)
        return p if os.path.exists(p) else None
    except Exception:                                         # noqa: BLE001
        return None


def _threads_messen(kerne, budget_s=2.0):
    """Kleiner Startup-Bench: welche Intra-Op-Threadzahl ist auf DIESER CPU
    wirklich die schnellste? -> (beste, tabelle_ms) oder (None, {}).

    ANLASS (gemessen 31.08. im Prod-Container, Core Ultra 9 285H): 4 Threads
    rechnen DOPPELT so schnell wie 12. Auf Hybrid-CPUs (P- und E-Kerne) ist
    die Kernzahl eben keine Leistungszahl — onnxruntime verteilt den Intra-Op-
    Pool gleichmaessig, und der Lauf endet mit dem langsamsten Kern. Dieselbe
    Klasse steckte schon im Guete-Deckel (.377: 12 Threads 33+57 ms, 4 Threads
    4+13 ms) — dort war die Antwort ein fester Deckel fuer die Mini-Netze, hier
    ist sie eine MESSUNG statt einer Annahme.

    Der Bench kostet einmalig hoechstens budget_s und wird danach im
    Datenordner gecacht. Er misst NICHT, wenn weniger als vier Kerne erlaubt
    sind: dort gibt es strukturell nichts zu waehlen (die Kandidaten waeren
    1 und 2) und der gemessene Hybrid-Effekt kann in so einer Zuteilung gar
    nicht auftreten."""
    if kerne < 4:
        return None, {}
    import time as _t
    import onnxruntime as ort
    # Kandidaten: die kleinen Stufen plus die HALBE Kernzahl (auf Intel-
    # Hybriden liegt die Zahl der schnellen P-Kerne nahe daran) plus die volle
    # Zahl als Gegenprobe. Alles abgeleitet, kein gewuerfelter Wert.
    kandidaten = sorted({1, 2, 4, 8, max(1, kerne // 2), kerne}
                        & set(range(1, kerne + 1)))
    modell = _bench_modell()
    if modell:
        quelle, laeufe = modell, 6
        # Diese Session liest NUR die Eingangs-Signatur und rechnet nie — sie
        # bekommt trotzdem eine explizite Kappung (1 Thread): der Vertrag der
        # ORT-Kappungs-Deckung kennt keine Ausnahmen, und ein ungekappter Pool
        # nach Wirt-Kernzahl waere hier genauso falsch wie ueberall sonst.
        _so0 = ort.SessionOptions()
        _so0.intra_op_num_threads = 1
        _so0.inter_op_num_threads = 1
        _s0 = ort.InferenceSession(modell, sess_options=_so0,
                                   providers=["CPUExecutionProvider"])
        _in = _s0.get_inputs()[0]
        form = [d if isinstance(d, int) and d > 0 else 1 for d in _in.shape]
        eingabe = np.random.default_rng(11).random(form).astype(np.float32)
        name_in = _in.name
        del _s0
    else:
        quelle, laeufe = _bench_graph(), 3
        quelle, n = quelle
        eingabe = np.ascontiguousarray(
            np.linspace(-1, 1, n * n, dtype=np.float32).reshape(n, n))
        name_in = "X"
    tabelle, ende = {}, _t.perf_counter() + float(budget_s)
    for th in kandidaten:
        if _t.perf_counter() > ende and tabelle:
            break
        so = ort.SessionOptions()
        so.intra_op_num_threads = th
        so.inter_op_num_threads = th
        s = ort.InferenceSession(quelle, sess_options=so,
                                 providers=["CPUExecutionProvider"])
        s.run(None, {name_in: eingabe})               # Warmlauf
        t0 = _t.perf_counter()
        for _ in range(laeufe):
            s.run(None, {name_in: eingabe})
        tabelle[th] = round((_t.perf_counter() - t0) * 1000.0 / laeufe, 2)
        del s
    if not tabelle:
        return None, {}
    return min(tabelle, key=tabelle.get), tabelle


def _threads_bestimmen(kerne):
    """Die EINE Ermittlung: Cache -> Bench -> Kernzahl. Jeder Schritt darf
    scheitern, ohne den Prozess zu kosten (fail-safe auf die Kernzahl, also
    genau das Verhalten vor Welle 1)."""
    global _THREADS_BENCH
    if (os.environ.get("SUSLIK_CPU_THREADS_BENCH") or "").strip() == "0":
        _THREADS_BENCH = {"quelle": "aus (SUSLIK_CPU_THREADS_BENCH=0)",
                          "threads": kerne}
        return kerne
    schluessel, pfad = _threads_schluessel(kerne), _threads_cache_pfad()
    if pfad:
        try:
            with open(pfad) as f:
                d = json.load(f)
            if d.get("schluessel") == schluessel and int(d.get("threads", 0)) > 0:
                _THREADS_BENCH = {**d, "quelle": "cache"}
                return int(d["threads"])
        except Exception:
            pass
    try:
        beste, tabelle = _threads_messen(kerne)
    except Exception as e:                                    # noqa: BLE001
        sys.stderr.write(f"[face_audit] thread bench skipped "
                         f"({type(e).__name__}: {str(e)[:80]}) -> {kerne} threads\n")
        _THREADS_BENCH = {"quelle": "bench fehlgeschlagen", "threads": kerne}
        return kerne
    if not beste:
        _THREADS_BENCH = {"quelle": "kein Bench (unter 4 Kernen)", "threads": kerne}
        return kerne
    import time as _t
    d = {"schluessel": schluessel, "threads": int(beste),
         "kerne": int(kerne), "tabelle_ms": tabelle, "ts": round(_t.time(), 1)}
    sys.stderr.write(
        f"[face_audit] cpu threads measured: {beste} of {kerne} allowed "
        f"({', '.join(f'{t}={ms}ms' for t, ms in sorted(tabelle.items()))})\n")
    if pfad:
        try:
            os.makedirs(os.path.dirname(pfad), exist_ok=True)
            tmp = f"{pfad}.tmp.{os.getpid()}"
            with open(tmp, "w") as f:
                json.dump(d, f)
            os.replace(tmp, pfad)
        except Exception:
            pass
    _THREADS_BENCH = {**d, "quelle": "gemessen"}
    return int(beste)


def _cgroup_quote(wurzel="/sys/fs/cgroup"):
    """Nutzbare GANZE CPUs laut cgroup-CPU-Quote (docker --cpus, LXC cpulimit)
    -> int oder None, wenn keine Quote gesetzt/lesbar ist.

    E3 (.505, 05.09.2026): die Affinitaets-Maske sieht diese Grenze NICHT — ein
    Container mit `--cpus 2` auf einem 12-Kern-Wirt traegt die volle Maske, darf
    aber nur 2 CPU-Sekunden je Sekunde verbrauchen. Abgerundet, mindestens 1
    (konservativ: es geht um eine Thread-ZAHL, nicht um eine Abrechnung).
    cgroup v2 (`cpu.max`: '<quota> <period>' oder 'max ...'), v1 als Rueckfall.

    `wurzel` ist NUR fuer den Testharnisch da (wie `verifyd._cgroup_speicher_grenze`
    es haelt): tools/proben/s11_e3c_pfaddeckung.py legt Attrappen-Dateien in ein
    tmpdir und prueft damit den v1-Rueckfall und die Abrundung. E3c (05.09.2026,
    Widerleger W-E3 LEICHT): beide waren bis hierher nur ARGUMENTIERT, nie
    gelaufen — der v1-Zweig hatte auf dieser Maschine (cgroup v2) noch nie eine
    Datei gesehen.

    EHRLICHE GRENZE, bewusst so: dieser Leser klettert NICHT in Eltern-cgroups.
    Eine Quote, die eine Ebene hoeher steht (systemd-CPUQuota ueber dem
    Container, Docker mit --cgroupns=host), sieht er nicht und meldet dann None
    statt einer geratenen Zahl — es bleibt bei der Affinitaets-Maske. Der
    Zwilling `verifyd._cgroup_speicher_grenze` klettert sehr wohl, weil dort eine
    fehlende Decke die Budget-Rechnung kippt; hier waere die Folge nur ein etwas
    zu grosser Thread-Pool, und dafuer ist das Risiko zu hoch, die Quote eines
    FREMDEN Eltern-cgroups als die eigene zu lesen.

    ZWILLING: `verifyd._cpu_quote` liest dasselbe fuer die Wanduhr-Frage
    ('passen zwei Analyse-Akteure nebeneinander?'). Zwei Leser sind einer zu
    viel; face_audit darf verifyd aber nicht importieren (verifyd importiert
    face_audit, Zirkel), und der Worker-Subprozess laedt verifyd gar nicht.
    Zusammenlegen kann nur ein Zug, der beide Dateien anfasst."""
    try:
        with open(os.path.join(wurzel, "cpu.max")) as f:
            teile = f.read().split()
        if teile and teile[0] != "max":
            periode = int(teile[1]) if len(teile) > 1 else 100000
            return max(1, int(teile[0]) // max(1, periode))
    except (OSError, ValueError, IndexError):
        pass
    try:                                                   # cgroup v1
        with open(os.path.join(wurzel, "cpu", "cpu.cfs_quota_us")) as f:
            q = int(f.read())
        with open(os.path.join(wurzel, "cpu", "cpu.cfs_period_us")) as f:
            p = int(f.read())
        if q > 0 and p > 0:
            return max(1, q // p)
    except (OSError, ValueError):
        pass
    return None


def _cpuset_erlaubt():
    """Anzahl der Kerne, auf denen dieser Prozess laufen DARF (cgroup-/LXC-cpuset)
    -> int oder None, wenn die Plattform das nicht kennt (sched_getaffinity gibt
    es nur auf Linux; None heisst 'unbekannt', nicht '0')."""
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except (AttributeError, OSError):
        return None


def _threads_ableiten(quote, cpuset_n, vorgabe):
    """Die EINE Ableitung der erlaubten Kernzahl -> int >= 1. Rein: keine Datei,
    keine Umgebung, nur Rechnen — damit sie ohne Maschine pruefbar ist
    (tools/proben/s11_e3_threads.py).

    vorgabe  = SUSLIK_CPU_THREADS bzw. Config `cpu_threads` (None/0 = nicht
               gesetzt). Behaelt Vorrang wie bisher: wer die Zahl ausdruecklich
               setzt, bekommt genau sie.
    quote    = ganze CPUs laut cgroup-Quote (_cgroup_quote) oder None.
    cpuset_n = erlaubte Kerne laut Affinitaets-Maske (_cpuset_erlaubt) oder None.

    ANLASS (.505 E3, 05.09.2026): bis hierher zaehlte allein die Affinitaets-
    Maske, die Quote blieb unbeachtet. Beide Grenzen sind aber echt und
    unabhaengig — wer die kleinere ignoriert, baut zu grosse Thread-Pools:
    onnxruntime verteilt den Intra-Op-Pool gleichmaessig und pinnt bei
    ungenannter Threadzahl Thread i an Kern i; passt der Pool nicht in die
    wirklich verfuegbare CPU-Zeit, kostet er Umschaltungen statt Tempo, und auf
    Maschinen mit cpuset < Quote saeumen pthread_setaffinity-EINVAL-Zeilen das
    analyze.log (Feldbefund Test-LXC: Quote 12, nproc 8). Also das MINIMUM
    beider Grenzen; faellt eine weg (kein cgroup-Zugriff, Nicht-Linux), gilt die
    andere, und fehlen beide, bleibt es beim alten Rueckfall os.cpu_count()."""
    if vorgabe:
        try:
            v = int(vorgabe)
        except (TypeError, ValueError):
            v = 0
        if v > 0:
            return v
    grenzen = [int(g) for g in (quote, cpuset_n) if isinstance(g, int) and g > 0]
    if grenzen:
        return max(1, min(grenzen))
    return max(1, os.cpu_count() or 1)


def _ort_thread_opts(deckel=None):
    """SessionOptions mit EXPLIZIT gesetzter Intra-Op-Thread-Zahl.

    deckel (.377, additiv): fuer MINI-Netze (die Guete-Modelle, zusammen
    ~3 Mio Parameter) sind viele Threads LANGSAMER als wenige — gemessen im
    Prod-Container unter Last: 12 Threads 33+57 ms je Bild, 4 Threads
    4+13 ms. Der Deckel kappt die ermittelte Kernzahl zusaetzlich nach
    oben; None = unveraendertes Verhalten fuer alle Bestands-Aufrufer.

    onnxruntime baut seinen Thread-Pool sonst nach std::thread::hardware_concurrency() (= HOST-Kerne)
    und pinnt Thread i an Kern i. Im Container erlaubt die cgroup-CPU-Maske nur eine Teilmenge ->
    pthread_setaffinity_np schlaegt fuer die fremden Kerne mit EINVAL fehl (rote [E]-Zeilen bei jedem
    Session-Aufbau). Fix laut ORT-Meldung selbst: 'Specify the number of threads explicitly so the
    affinity is not set' -> intra_op_num_threads = Anzahl der WIRKLICH erlaubten Kerne.

    WICHTIG — NIE als globaler Monkeypatch von ort.InferenceSession (Regression 0.1.0.13, 22.07.):
    insightface leitet PickableInferenceSession von onnxruntime.InferenceSession AB. Ersetzt man die
    Klasse durch eine Funktion, bricht Vererbung/Unpickling mit
    'TypeError: function() argument 'code' must be code, not str' -> JEDE Analyse stirbt nach 0.3s
    mit 0 Gesichtern, keine Erkennung, keine Alerts. Darum haengen wir die Optionen ausschliesslich
    an unsere EIGENEN Sessions — Ersatz NACH prepare(), nie die Klasse patchen. Seit dem #21-Fix
    ersetzt _to_backend() die insightface-internen prepare()-Sessions auf JEDEM Backend, auch cpu:
    vorher behielten sie auf dem reinen CPU-Pfad ihre UNGEKAPPTEN Default-Pools (je Session
    hardware_concurrency des WIRTS, fuenf Sessions), die cpu_threads-Config deckelte dort nur die
    eigene Recognition-Session (Issue #21: 2C/4T-NUC, zwei Worker a ~160 %)."""
    import onnxruntime as ort
    global _ORT_THREADS
    # Double-checked (.505 E4, W-E3c Notiz 7): der haeufige Fall — die Zahl steht
    # schon — laeuft weiter ohne Schloss; nur der EINE Kaltaufruf nimmt es, und
    # wer waehrenddessen ankommt, wartet auf das Ergebnis, statt ein zweites Mal
    # zu messen (drei Kaltaufrufe ergaben sonst drei Benches mit abweichenden
    # Ergebnissen, letzter Schreiber gewinnt).
    if _ORT_THREADS is None:
        with _ORT_THREADS_SCHLOSS:
            if _ORT_THREADS is None:
                env = os.environ.get("SUSLIK_CPU_THREADS", "")
                vorgabe = int(env) if env.isdigit() and int(env) > 0 else None
                # .505 (E3, 05.09.2026): erlaubte Kernzahl = MINIMUM aus cgroup-Quote
                # und Affinitaets-Maske. Bis hierher zaehlte nur die Maske; auf
                # Maschinen, deren cpuset kleiner ist als die Quote (Feldbefund
                # Test-LXC: Quote 12, nproc 8), bzw. bei `docker --cpus` mit voller
                # Maske entstanden so zu grosse Pools und pthread_setaffinity-Zeilen
                # im analyze.log. Die ausdrueckliche Vorgabe (N9: cpu_threads-Config,
                # Service setzt ENV, Worker erbt) behaelt Vorrang und ueberspringt
                # wie bisher den Bench.
                _kerne = _threads_ableiten(_cgroup_quote(), _cpuset_erlaubt(), vorgabe)
                # .384 (Welle 1, Etappe C): die Kernzahl ist auf Hybrid-CPUs KEINE
                # Leistungszahl — gemessen 31.08. an 2d106det auf dieser Maschine
                # (12 Kerne zugeteilt): 4 Threads 3,63 ms gegen 12 Threads 6,97 ms.
                # Deshalb wird sie GEMESSEN statt angenommen; scheitert die Messung
                # oder ist sie ausgeschaltet, gilt wieder die Kernzahl (Verhalten
                # wie vorher, nie ein stiller Ausfall).
                _ORT_THREADS = _kerne if vorgabe else _threads_bestimmen(_kerne)
    threads = _ORT_THREADS if deckel is None else max(1, min(_ORT_THREADS, int(deckel)))
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    # inter_op mitsetzen (#21): im Default-Modus ORT_SEQUENTIAL baut ORT zwar keinen
    # Inter-Op-Pool, aber der Default-WERT waere wieder hardware_concurrency — sollte je
    # eine Session in den Parallel-Modus geraten, gilt derselbe Deckel statt der Host-Kernzahl.
    so.inter_op_num_threads = threads
    return so


# Reentranz-Tiefe der Init-Kappung: ein zweiter (verschachtelter) Aufruf darf die
# gemerkten Originale NICHT ueberschreiben, sonst stellt der innere finally-Zweig
# den WRAPPER als "Original" wieder her und der Patch bliebe fuer immer stehen.
#
# .505 (E3c, 05.09.2026, Widerleger W-E3 MITTEL 1): Tiefe UND Originale sind
# prozessweit GETEILTER Zustand. Ohne Schloss konnten zwei Threads beide die
# Tiefe 0 sehen, beide patchen — und der erste Aussteiger stellte das Original
# zurueck, waehrend der zweite noch in der Klammer sass; dessen naechste
# insightface-Session lief dann wieder ungekappt (der Widerleger hat das mit
# geweitetem Fenster nachgestellt). Deshalb liegen Ermittlung, Patch und
# Rueckstellung unter diesem Schloss, und die Originale stehen nicht mehr in
# einer lokalen Variablen des ERSTEN Aufrufs, sondern hier im Modul: die Tiefe
# ist damit ein echter Referenzzaehler, und nur der LETZTE Aussteiger raeumt ab.
# RLock statt Lock, bewusst: der Init darf an der Kappung nie sterben — ein
# uebersehener Weg, der aus dem gesperrten Abschnitt heraus noch einmal hier
# hereinliefe, waere mit einem einfachen Lock ein Deadlock im Modell-Laden.
_IF_KAPPUNG_SCHLOSS = _threading.RLock()
_IF_KAPPUNG_TIEFE = 0
_IF_KAPPUNG_STAND = None           # (modul, {name: originalklasse}) des ERSTEN Eintritts
_IF_KAPPUNG_GEMELDET = False       # der "baut anders"-Hinweis nur EINMAL je Prozess
_IF_KAPPUNG_TREFFER = 0            # Session-Baeute DURCH den gepatchten Namen
_IF_KAPPUNG_LEER_GEMELDET = False  # der "0 Treffer"-Hinweis nur EINMAL je Prozess
# .505 E4 (05.09.2026, W-E3c Notiz 4): Trefferstand beim Beginn der KETTE, also
# beim Patchen (Tiefe 0 -> 1). Die "0 Treffer"-Notiz wird nur beim AEUSSERSTEN
# Austritt (Tiefe 1 -> 0) gegen diesen Stand bewertet. Vorher merkte sich JEDER
# Eintritt seinen eigenen Stand und der patchende bewertete beim EIGENEN
# Austritt — bei ueberlappender Verschachtelung (die aeussere Klammer geht,
# bevor die innere baut) feuerte die Notiz deshalb faelschlich und verbrauchte
# dabei die Einmal-je-Prozess-Sperre.
_IF_KAPPUNG_KETTE_TREFFER = 0


def _insightface_session_ziele():
    """Die Namen im insightface-Modul `model_zoo`, ueber die dessen Sessions
    entstehen -> {name: klasse} (leer = dieser insightface-Bau baut anders).

    In insightface 1.0.1 (hier ausgeliefert) ruft `ModelRouter.get_model` die
    MODUL-GLOBALE `PickableInferenceSession` — eine UNTERKLASSE von
    onnxruntime.InferenceSession, die beim Modul-Import gebunden wird. Genau
    dieser Modul-Name ist das Patch-Ziel: `onnxruntime.InferenceSession` selbst
    zu ersetzen wuerde hier NICHTS bewirken (die Unterklasse haelt ihre Basis
    schon) und ist ausserdem ausdruecklich verboten — Regression 0.1.0.13,
    s. Kopf von _ort_thread_opts. `InferenceSession` steht zusaetzlich in der
    Liste fuer insightface-Baeume, die den Namen direkt ins Modul importieren
    (`from onnxruntime import InferenceSession`); das ist ebenfalls ein
    MODUL-lokaler Name, kein Eingriff ins onnxruntime-Paket."""
    try:
        from insightface.model_zoo import model_zoo as _mz
    except Exception:                                  # noqa: BLE001
        return None, {}
    ziele = {}
    for name in ("PickableInferenceSession", "InferenceSession"):
        obj = getattr(_mz, name, None)
        if isinstance(obj, type):                      # nur echte Klassen, nie ein Fremd-Wrapper
            ziele[name] = obj
    return _mz, ziele


@_contextlib.contextmanager
def _insightface_sessions_gekappt():
    """Klammer um den insightface-Init: dessen eigene Modell-Sessions bekommen
    unsere Thread-Optionen (_ort_thread_opts), solange die Klammer offen ist.
    Danach steht das Original wieder — auch bei Ausnahme.

    ANLASS (.505 E3b, 05.09.2026, bauplan_0505 §2 Gruppe E). Gemessen auf der
    CPU-Testmaschine .165 (Wirt 16 Kerne, 8 erlaubt): je Analyse standen 64
    `pthread_setaffinity_np failed`-Zeilen im analyze.log, ALLE VOR den fuenf
    "Applied providers"-Zeilen — also nicht in unseren Sessions (die sind seit
    #21/E3 gekappt und erzeugen null Zeilen), sondern im insightface-Init:
    `FaceAnalysis(...)` baut je ONNX-Datei eine Session ueber
    `PickableInferenceSession(file, providers=..., provider_options=...)` OHNE
    sess_options; onnxruntime nimmt dann hardware_concurrency() des WIRTS und
    pinnt Thread i an Kern i -> EINVAL fuer jeden nicht erlaubten Kern. Die
    Sessions leben nur bis `_to_backend()` sie ersetzt, der zu grosse Pool wird
    aber trotzdem jedes Mal gebaut (Spam + Kaltstart-Zeit).

    WAS THREAD-SICHER GARANTIERT IST (.505 E3c, 05.09.2026, Widerleger W-E3
    MITTEL 1): solange IRGENDEIN Thread in der Klammer steht, ist der gepatchte
    Name gesetzt; erst der LETZTE Aussteiger stellt das Original zurueck. Unter
    dem Schloss liegen nur EINTRITT (Ermittlung + Patch + Zaehler) und AUSTRITT
    (Zaehler + Rueckstellung), NICHT der Rumpf — sonst wuerde die Klammer den
    Modellbau aller Threads hintereinander zwingen, und genau dieser Bau ist das
    Teure. NICHT garantiert ist der umgekehrte Fall: ein Thread OHNE Klammer
    baut weiter ungekappt, der Patch haengt am Modul-Namen, nicht am Thread.

    Ehrliche Grenzen:
    - Gepatcht wird NUR der Modul-Name in insightface.model_zoo.model_zoo,
      nie `onnxruntime.InferenceSession` (s. _insightface_session_ziele).
    - Kennt dieser insightface-Bau keinen der Namen (andere Version, anderer
      Aufrufpfad), wird NICHTS gepatcht: die Klammer reicht durch und meldet das
      einmal auf stderr. Erkennbar bleibt der Fall an den wiederkehrenden
      pthread_setaffinity-Zeilen vor "Applied providers" (Gate-Stufe
      ORT-Thread-Kappung misst sie je Session).
    - Wird in der Klammer KEINE Session ueber den gepatchten Namen gebaut,
      obwohl gepatcht wurde, sagt die Klammer das einmal je Prozess auf stderr
      (E3c/T4, W-E3 MITTEL 3): "richtiger Name gepatcht, Sessions entstehen
      woanders" war vorher ein STILLER Teil-Fehlschlag — der Patch sass, die
      Kappung wirkte nicht, und niemand erfuhr es. Bewertet wird die GANZE
      Klammer-Kette, und zwar erst bei ihrem AEUSSERSTEN Austritt (Tiefe 1 -> 0;
      .505 E4, W-E3c Notiz 4). Vorher urteilte der patchende Aufruf bei seinem
      EIGENEN Austritt ueber seinen EIGENEN Trefferstand — verlaesst die aeussere
      Klammer die Buehne, bevor die innere baut (ueberlappend statt sauber
      verschachtelt, erreichbar z. B. wenn FaceAnalysis() vor dem ersten Bau
      wirft), meldete sie faelschlich "0 Treffer" und verbrauchte damit die
      Einmal-je-Prozess-Sperre fuer den echten Fall.
    - Scheitert ein `setattr` mitten im Patchen (zweiter Zielname), wird das
      bereits Gesetzte sofort zurueckgestellt und die Klammer als NICHT AKTIV
      betreten (Durchreichen + Notiz). Ohne das blieb der erste Name dauerhaft
      gepatcht: `_IF_KAPPUNG_STAND` war noch None, also stellte auch niemand
      zurueck, und der Vertrag "nach der Klammer ist alles Original" galt nicht
      mehr (.505 E4, W-E3c Notiz 6; real kaum erreichbar, aber ein Vertrag mit
      Ausnahme ist keiner).
    - Beide Notizen tragen die feste Kennung `[ortkappung]` am Anfang, damit das
      Gate sie im Startlog greppen kann (D1).
    - Der Wrapper ergaenzt sess_options NUR, wenn der Aufrufer keine mitgibt
      (weder als Schluesselwort noch als zweites Positionsargument) — eine
      fremde Signatur reicht damit unveraendert durch.
    - Scheitert _ort_thread_opts selbst, wird ebenfalls unveraendert
      durchgereicht: der Init darf an der Kappung nie sterben."""
    global _IF_KAPPUNG_TIEFE, _IF_KAPPUNG_GEMELDET, _IF_KAPPUNG_STAND
    global _IF_KAPPUNG_TREFFER, _IF_KAPPUNG_LEER_GEMELDET
    global _IF_KAPPUNG_KETTE_TREFFER

    def _gekappt(orig):
        def bauen(*args, **kwargs):
            global _IF_KAPPUNG_TREFFER
            with _IF_KAPPUNG_SCHLOSS:
                # E3c/T4: der BEWEIS, dass insightface wirklich ueber den
                # gepatchten Namen baut. Gezaehlt wird jeder Durchgang, auch
                # einer mit eigenen Optionen — die Frage ist "laeuft der Bau
                # hier durch?", nicht "haben wir ergaenzt?".
                _IF_KAPPUNG_TREFFER += 1
            # sess_options ist im ORT-Konstruktor das ZWEITE Positionsargument
            # (path_or_bytes, sess_options, providers, provider_options) — wer es
            # so uebergibt, hat schon eigene Optionen.
            if "sess_options" not in kwargs and len(args) < 2:
                try:
                    kwargs["sess_options"] = _ort_thread_opts()
                except Exception as e:                 # noqa: BLE001
                    sys.stderr.write(f"[ortkappung] WARN: init thread capping "
                                     f"skipped ({type(e).__name__}: {str(e)[:80]})\n")
            return orig(*args, **kwargs)
        bauen._suslik_original = orig                  # ablesbar fuer Proben/Wachen
        return bauen

    gezaehlt = False
    patch_fehler = None
    with _IF_KAPPUNG_SCHLOSS:
        if _IF_KAPPUNG_TIEFE > 0:                      # schon geklammert -> nur mitzaehlen
            _IF_KAPPUNG_TIEFE += 1
            gezaehlt = True
        else:
            mz, ziele = _insightface_session_ziele()
            if ziele:
                # ERST alle Wrapper bauen, DANN setzen (.505 E4, W-E3c Notiz 6):
                # wirft ein setattr mitten in der Schleife, wird das bereits
                # Gesetzte hier zurueckgestellt und die Klammer gilt als nicht
                # aktiv — sonst bliebe der erste Name fuer immer gepatcht.
                neu = {name: _gekappt(orig) for name, orig in ziele.items()}
                gesetzt = []
                try:
                    for name, wrapper in neu.items():
                        setattr(mz, name, wrapper)
                        gesetzt.append(name)
                except Exception as e:                 # noqa: BLE001
                    patch_fehler = f"{type(e).__name__}: {str(e)[:80]}"
                    for name in gesetzt:
                        try:
                            setattr(mz, name, ziele[name])
                        except Exception:              # noqa: BLE001
                            pass                       # mehr als versuchen geht nicht
                else:
                    _IF_KAPPUNG_STAND = (mz, ziele)    # NUR der erste merkt die Originale
                    _IF_KAPPUNG_TIEFE = 1
                    _IF_KAPPUNG_KETTE_TREFFER = _IF_KAPPUNG_TREFFER
                    gezaehlt = True
            elif not _IF_KAPPUNG_GEMELDET:
                _IF_KAPPUNG_GEMELDET = True
                sys.stderr.write("[ortkappung] note: insightface builds its sessions "
                                 "elsewhere (no PickableInferenceSession/InferenceSession "
                                 "in model_zoo) -> init thread capping skipped\n")
    if patch_fehler:                                   # Schreiben ohne Schloss
        sys.stderr.write(f"[ortkappung] WARN: could not patch insightface session "
                         f"names ({patch_fehler}) — originals restored, init thread "
                         f"capping skipped\n")
    try:
        yield
    finally:
        melden = False
        with _IF_KAPPUNG_SCHLOSS:
            if gezaehlt:
                _IF_KAPPUNG_TIEFE = max(0, _IF_KAPPUNG_TIEFE - 1)
                if _IF_KAPPUNG_TIEFE == 0 and _IF_KAPPUNG_STAND is not None:
                    _mz, _ziele = _IF_KAPPUNG_STAND
                    for name, orig in _ziele.items():
                        setattr(_mz, name, orig)
                    _IF_KAPPUNG_STAND = None
                    # DIE Bewertung der ganzen Kette, genau hier und nur hier.
                    if (_IF_KAPPUNG_TREFFER == _IF_KAPPUNG_KETTE_TREFFER
                            and not _IF_KAPPUNG_LEER_GEMELDET):
                        _IF_KAPPUNG_LEER_GEMELDET = melden = True
        if melden:                                     # Schreiben ohne Schloss
            sys.stderr.write("[ortkappung] note: insightface built no session through "
                             "the patched name — thread cap may not apply\n")


def geraete_knoten_muster(dev):
    """Task #15: Pflicht-Geraeteknoten je OpenVINO-Device (None = keine Vorbedingung).
    Basis-Lookup ueber split('.'): GPU.0/GPU.1/NPU.0 (unsere eigene Mehr-GPU-Hilfe
    empfiehlt genau diese Formen) werden wie GPU/NPU behandelt (Widerleger-Fund .66).
    MIXED erreicht _ort_session nie als dev (Aufrufer verteilen auf GPU+NPU); AUTO
    kann bei DIREKTEM CLI-Lauf ankommen — das Mapping liefert dann None und das
    Verhalten bleibt wie vor Task #15 (verifyd loest AUTO vorher auf).
    Pseudo-Geraete der Norm-Kette (GPU_FP32) liefern den Knoten ihres ECHTEN
    OpenVINO-Geraets — sie sind dasselbe Stueck Silizium, nur anders kompiliert."""
    # P3.1: Zuordnung lebt in core.registry (KNOTEN_BASIS) — Signatur und
    # Basislookup-Verhalten (GPU.1 -> GPU, unbekannt -> None) unveraendert.
    from core.registry import knoten_von
    _p = NORM_PSEUDO_GERAETE.get(str(dev or "").upper())
    return knoten_von(_p["ov_device"] if _p else dev)


# Pseudo-Geraete: EIN Name der Norm-Kette, der kein eigenes OpenVINO-Device ist,
# sondern dasselbe Geraet mit anderer Rechen-Praezision. EINE Quelle fuer Knoten-
# Lookup UND Session-Bau (K3-Regel: keine zweite verstreute Aufzaehlung).
# ACHTUNG BEIM AUFRAEUMEN: die Definition steht bewusst UNTER der Knoten-Hilfe und
# nicht darueber. Das Gate (tools/qs.sh, Stufe S1) schneidet den Quelltext zwischen
# den Definitionszeilen von geraete_knoten_muster und der naechsten Funktion heraus
# und fuehrt nur diesen Ausschnitt aus, um den Knoten-Lookup ohne onnxruntime-Import
# zu pruefen. Wandert die Konstante darueber, faellt sie aus dem Ausschnitt und der
# Lookup wirft dort NameError. Aus demselben Grund darf in diesem Block auch kein
# Kommentar die Zeichenfolge der beiden Schnittmarken woertlich enthalten — genau
# das ist beim ersten Bauversuch am 24.08. passiert, der Schnitt lief in den
# Kommentar statt in die Funktion.
NORM_PSEUDO_GERAETE = {
    # GPU_FP32: die Intel-iGPU, aber mit erzwungener FP32-Rechnung statt der
    # OpenVINO-Voreinstellung fp16. Gemessen 24.08.2026 (Tabelle bei
    # NormMass.NORM_KREUZ_MAX): fp16 weicht auf dem Gesichtsreiz bis 0,149 von der
    # CPU ab, FP32 auf demselben Geraet 0,0000095 — auf Tokn59s Gen8 (keine
    # fp16-Einheiten) liegt fp16 bei 105,276, dort ist FP32 die einzige Chance,
    # die GPU ueberhaupt zu nutzen.
    "GPU_FP32": {"ov_device": "GPU", "precision": "FP32"},
}


def _ort_session(kind, dev, model_file, cache=None):
    """Baut EINE onnxruntime-Session fuers gewaehlte Backend. Validiert gegen die REAL verfuegbaren
    Provider; fehlt der gewuenschte EP -> LAUTE Warnung + CPU (kein STILLER Fallback, das versteckt
    Fehlkonfiguration und war ein bekannter Footgun). provider_options unterscheiden sich je Backend:
    OpenVINO {device_type, cache_dir}, CUDA {device_id} (kein device_type/cache_dir)."""
    import onnxruntime as ort
    import sys as _sys
    avail = ort.get_available_providers()
    if kind == "openvino" and "OpenVINOExecutionProvider" in avail:
        # Task #15 (Tester-Log Issue #6, Gen9 ohne NPU): Geraete-Knoten VOR dem Session-
        # Versuch pruefen. Ohne Knoten ist der Versuch chancenlos und produziert nur
        # ORT-[E]/[W]-Spam plus eine irrefuehrende "runtime mismatch?"-Warnung — dabei
        # HAT die Plattform das Geraet schlicht nicht (Gen8/9/11 hat nie eine NPU).
        # Ein kurzer note bleibt (kein STILLER Fallback bei expliziter Fehlkonfiguration);
        # der Mismatch-Verdacht unten gilt weiter fuer vorhanden-aber-bindet-nicht.
        _knoten = geraete_knoten_muster(dev)
        if _knoten and not _glob.glob(_knoten):
            _sys.stderr.write(f"[face_audit] note: no {dev} device node ({_knoten}) "
                              f"on this host -> CPU\n")
            return ort.InferenceSession(model_file, providers=["CPUExecutionProvider"],
                                        sess_options=_ort_thread_opts())
        opts = {"device_type": dev}
        if cache:                                 # cache_dir NUR bei echtem Pfad — None wuerde als String
            opts["cache_dir"] = cache             # "None" landen und OpenVINO legt einen Ordner "None/" im CWD an
        s = ort.InferenceSession(model_file, providers=["OpenVINOExecutionProvider"],
                                 provider_options=[opts], sess_options=_ort_thread_opts())
        # EP war da, aber das DEVICE kann fehlen ("Device GPU is not available") -> onnxruntime faellt
        # STILL auf CPU zurueck. Erkennbar: OpenVINO-Provider faellt aus get_providers() raus. Dann laut
        # warnen (sonst laeuft der Dienst auf CPU und meldet GPU -> genau der Footgun, den wir vermeiden).
        if "OpenVINOExecutionProvider" not in s.get_providers():
            _sys.stderr.write(f"[face_audit] WARN: OpenVINO device '{dev}' not available -> running on "
                              f"CPU (GPU/NPU runtime vs. host driver version mismatch?)\n")
        return s
    if kind == "cuda" and "CUDAExecutionProvider" in avail:
        # Task-#15-Muster, cuda nachgezogen (Widerleger 31.07.): ohne /dev/nvidia* ist der
        # Session-Versuch chancenlos und produzierte nur ORT-[E]-Spam + die irrefuehrende
        # "mismatch?"-Warnung — dabei HAT der Host schlicht keine NVIDIA-Karte (Gen9-Klasse).
        if not _glob.glob(geraete_knoten_muster("NVIDIA") or "/dev/nvidia*"):
            _sys.stderr.write("[face_audit] note: no NVIDIA device node (/dev/nvidia*) "
                              "on this host -> CPU\n")
            return ort.InferenceSession(model_file, providers=["CPUExecutionProvider"],
                                        sess_options=_ort_thread_opts())
        try:                                      # 'cuda:GPU' o.ae. -> int() wirft; dokumentiert ist ein
            _did = int(dev or 0)                  # lauter CPU-Fallback, kein Absturz des Dienstes
        except (TypeError, ValueError):
            _sys.stderr.write(f"[face_audit] WARN: ungueltige CUDA-Geraetenummer '{dev}' -> device_id=0\n")
            _did = 0
        s = ort.InferenceSession(
            model_file, providers=[("CUDAExecutionProvider", {"device_id": _did}),
                                   "CPUExecutionProvider"], sess_options=_ort_thread_opts())
        # Wie im OpenVINO-Zweig: der EP kann gelistet sein und trotzdem nicht binden (Treiber-/
        # cuDNN-Mismatch, GPU belegt) -> onnxruntime nimmt still CPUExecutionProvider. Ungeprueft
        # meldete der Startup-Check "cuda engaged", waehrend real die CPU rechnete.
        if "CUDAExecutionProvider" not in s.get_providers():
            _sys.stderr.write(f"[face_audit] WARN: CUDA device '{dev or 0}' not available -> running on "
                              f"CPU (driver/cuDNN vs. onnxruntime-gpu version mismatch?)\n")
        return s
    if kind == "migraphx" and "MIGraphXExecutionProvider" in avail:
        # AMD (N2): Geraete-Vorpruefung wie im OpenVINO-Zweig — ohne /dev/kfd ist der
        # Versuch chancenlos (leiser note statt Treiber-Spam; Task-#15-Muster).
        if not _glob.glob(geraete_knoten_muster("KFD") or "/dev/kfd"):
            _sys.stderr.write("[face_audit] note: no AMD KFD device node (/dev/kfd) "
                              "on this host -> CPU\n")
            return ort.InferenceSession(model_file, providers=["CPUExecutionProvider"],
                                        sess_options=_ort_thread_opts())
        try:
            _did = int(dev or 0)
        except (TypeError, ValueError):
            _sys.stderr.write(f"[face_audit] WARN: ungueltige MIGraphX-Geraetenummer "
                              f"'{dev}' -> device_id=0\n")
            _did = 0
        s = ort.InferenceSession(
            model_file, providers=[("MIGraphXExecutionProvider", {"device_id": _did}),
                                   "CPUExecutionProvider"], sess_options=_ort_thread_opts())
        # Wie bei OpenVINO/CUDA: EP gelistet heisst nicht gebunden -> LAUT statt still.
        if "MIGraphXExecutionProvider" not in s.get_providers():
            _sys.stderr.write(f"[face_audit] WARN: MIGraphX device '{dev or 0}' not "
                              f"available -> running on CPU (ROCm runtime vs. host "
                              f"driver/GPU support mismatch?)\n")
        return s
    if kind == "cpu":
        return ort.InferenceSession(model_file, providers=["CPUExecutionProvider"],
                                sess_options=_ort_thread_opts())
    _sys.stderr.write(f"[face_audit] WARN: Backend '{kind}:{dev}' nicht verfuegbar "
                      f"(vorhanden: {avail}) -> CPUExecutionProvider\n")
    return ort.InferenceSession(model_file, providers=["CPUExecutionProvider"],
                                sess_options=_ort_thread_opts())

# ---------------------------------------------------------------- Frigate I/O
def fetch_index():
    from core import frigate_auth as _fauth     # 5e: DER eine Frigate-Griff
    with _fauth.oeffnen(f"{FRIGATE}/api/faces", timeout=20) as r:
        d = json.load(r)
    return {k: v for k, v in d.items() if k != "train"}

def furl(person, fname):
    return f"{FRIGATE}/clips/faces/{urllib.parse.quote(person)}/{urllib.parse.quote(fname)}"

def fdate(fname):
    m = re.search(r"(\d{10})", fname)          # Unix-Sekunden im Dateinamen
    if not m: return "?"
    return datetime.datetime.fromtimestamp(int(m.group(1))).strftime("%d.%m.%y %H:%M")

def fetch_image(person, fname):
    from core import frigate_auth as _fauth     # 5e: DER eine Frigate-Griff
    with _fauth.oeffnen(furl(person, fname), timeout=20) as r:
        raw = r.read()
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)  # BGR

# ---------------------------------------------------------------- Embedding backend
class Embedder:
    """buffalo_l: Detection + 5-Punkt-Landmark-Alignment + ArcFace.
    OHNE Alignment sind ArcFace-Embeddings verrauscht. embed()==None = kein Gesicht.

    Backend pluggbar ueber VERIFY_BACKEND (oder device=), Abwaertskompat OV_DEVICE. Werte:
      cuda[:N] -> Nvidia (nur wo onnxruntime-gpu installiert ist, z.B. im CUDA-Docker-Image)
      migraphx[:N] / rocm -> AMD via MIGraphX-EP (nur im rocm-Docker-Image; braucht /dev/kfd)
      NPU   -> alle Modelle auf der Intel-NPU (schnellstes End-to-End, ~90x ggue CPU;
               Intel-Images: gpu und gpu-legacy)
      GPU   -> alle Modelle auf der Intel-iGPU
      MIXED -> Detektor+Landmarks auf GPU, ArcFace auf NPU
      leer/CPU -> unveraendert, nativer CPU-Provider (Default).
    insightface reicht providers NICHT an seine Modell-Sessions durch (und auch keine
    SessionOptions), daher werden die ONNX-Sessions nach prepare() IMMER durch eigene
    _ort_session-Sessions ersetzt: auf Beschleunigern wechselt dabei der EP, auf cpu bleibt
    der EP und es greift die Thread-Kappung aus _ort_thread_opts (Issue #21). Die Embeddings
    bleiben numerisch praktisch identisch (cos > 0.9997 ggue. CPU), Schwellwerte gelten weiter."""
    # ZAEHL-WACHE (Live-Performance Welle 1, Etappe B, 31.08.): wie viele
    # Embedder halten in DIESEM Prozess gerade Sessions? Der Leitsatz heisst
    # "EIN Inferenz-Kern je Dienst" — ein zweiter Embedder ist ein zweites
    # Modell auf derselben iGPU, und genau diese Konstellation hat am 11.08.
    # vier Waechter getoetet (CL_OUT_OF_RESOURCES). Die Zahl ist ABLESBAR,
    # damit eine Wache sie pruefen kann, statt sie zu glauben. WeakSet, nicht
    # Zaehler: nach einem Detektor-Neubau faellt der alte heraus, sobald er
    # wirklich weg ist — ein Zaehler wuerde dort dauerhaft falsch stehen.
    _LEBENDE = __import__("weakref").WeakSet()

    @classmethod
    def instanzen(cls):
        """-> Zahl der LEBENDEN Embedder in diesem Prozess."""
        return len(cls._LEBENDE)

    def __init__(self, device=None, modell=None):
        import onnxruntime as ort
        ort.set_default_logger_severity(3)
        from insightface.app import FaceAnalysis
        # .313: nur die drei Modelle, die wir lesen (Detektor liefert kps; landmark_3d_68
        # liefert pose; recognition wird durch adaface ersetzt) — landmark_2d_106 und
        # genderage liefen je Gesicht umsonst mit (zwei GPU-Inferenzen je Detektion).
        # .505 (E3b, 05.09.2026): FaceAnalysis UND prepare in die Init-Kappung
        # klammern. insightface baut seine Modell-Sessions ohne SessionOptions,
        # onnxruntime nimmt dort hardware_concurrency() des WIRTS statt der
        # erlaubten Kerne — gemessen auf der CPU-Testmaschine .165 (Wirt 16,
        # erlaubt 8): 64 pthread_setaffinity-Zeilen je Analyse, ALLE vor den
        # fuenf "Applied providers"-Zeilen, also genau hier. prepare() ist
        # mitgeklammert, weil es je Modell set_providers() ruft und damit die
        # native Session neu aufbaut. GEMESSEN an den AUSGELIEFERTEN IMAGES
        # (05.09.2026, W-E3c: onnxruntime 1.24.1 im gpu-Image — das faehrt auch
        # suslik-prod —, 1.26.0 im cuda-Image, 1.27.0 im cpu-Image; insightface
        # 1.0.1). Die Herkunft gehoert dazu: auf dem WIRT meldet `pip list`
        # 1.29.0, importiert wird im venv trotzdem 1.24.1
        # (onnxruntime-openvino verdeckt das nackte Paket) — eine Wirt-Zahl
        # taugt hier also nicht, die eine Quelle ist die Versionszeile im
        # Startlog des jeweiligen Images. In allen drei Images gilt dieselbe
        # Sachaussage: set_providers() geht ueber _reset_session, und das
        # behaelt _sess_options_initial — unsere Optionen ueberleben, die
        # Klammer um prepare() ist HIER also eine tote Zeile (null zusaetzliche
        # Konstruktor-Aufrufe gemessen). Sie bleibt trotzdem stehen: sie ist die
        # Versicherung fuer fremde Baeume, in denen an dieser Stelle ein echter
        # Neubau ueber den Konstruktor sitzt. Die
        # Sessions leben ohnehin nur bis _to_backend() sie ersetzt — gespart
        # wird der zu grosse Pool je Init-Session (Spam + Kaltstart-Zeit).
        with _insightface_sessions_gekappt():
            self.app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"],
                                    allowed_modules=["detection", "landmark_3d_68", "recognition"])
            self.app.prepare(ctx_id=-1, det_size=(320, 320))
        self.modell = (modell or aktuelles_modell()).lower()
        if self.modell not in MODELLE:
            raise SystemExit(f"Unbekanntes Recognition-Modell '{self.modell}' (erlaubt: {list(MODELLE)})")
        self._rec = None                              # eigenes Recognition-ONNX (None -> insightface buffalo)
        if MODELLE[self.modell]["art"] == "onnx":
            self._init_rec_onnx(MODELLE[self.modell])
        self._backend = resolve_backend(device)   # (kind, dev): device= gewinnt, sonst VERIFY_BACKEND/OV_DEVICE
        self._to_backend()                        # IMMER — auch cpu ersetzt die prepare()-Sessions (Thread-Kappung, #21)
        self._provider_guard("init")              # P1: Aufbau sofort verifizieren (nie Latenz raten); cpu: sofort True
        # Zaehl-Wache (s. Klassenkopf). type(self) statt des Modul-Namens
        # `Embedder`: worker.py bindet den Namen auf eine Singleton-FABRIK um
        # (Warmstart-Vertrag) — ein Zugriff ueber den globalen Namen liefe dort
        # gegen eine Funktion (gemessen im Gate: AttributeError im Worker-
        # Roundtrip, jede Analyse waere tot).
        type(self)._LEBENDE.add(self)

    def _init_rec_onnx(self, spec):
        """Recognition durch eigenes ONNX ersetzen (AdaFace): insightface macht weiter
        Detektion+Landmarks+Alignment, die eigene 'recognition' wird aus app.models entfernt
        (sonst rechnet get() den buffalo-Kopf doppelt und umsonst), app.get wird gekapselt und
        setzt face.embedding aus dem eigenen Modell — normed_embedding und ALLE Leser
        (fc.normed_embedding, embed()) ziehen dadurch transparent nach, kein Caller aendert sich."""
        import onnxruntime as ort
        pfad = spec["onnx"]
        if not os.path.exists(pfad):
            raise SystemExit(f"Recognition-ONNX fehlt: {pfad} (Modell '{self.modell}')")
        self._rec_spec = spec
        self.app.models.pop("recognition", None)
        self._rec = ort.InferenceSession(pfad, providers=["CPUExecutionProvider"],
                                         sess_options=_ort_thread_opts())
        self._rec_in = self._rec.get_inputs()[0].name
        self._orig_get = self.app.get
        self.app.get = self._get_mit_rec

    # P4 (0.1.0.42): feste Batch-Stufen statt beliebiger Batchgroessen. OpenVINO kompiliert je
    # NEUER Input-Shape einmalig nach (gemessen 27.07., P4.0: NPU ~3,2 s, iGPU ~1,7 s je neuer
    # Batchgroesse) — mit variablen Groessen (= Gesichter je Frame) sammelt der Betrieb
    # Compile-Spikes. Vier Stufen + Padding begrenzen das auf 4 Kompilate, die der Warmup beim
    # Session-Bau vorab bezahlt und der OV-Cache (W0, Volume) ueber Prozess-Leben hinweg haelt.
    BATCH_STUFEN = (1, 2, 4, 8)

    def _rec_infer(self, crops_bgr):
        """norm_crop-112-Crops (BGR, wie von insightface geliefert) -> L2-normierte
        Embeddings des eigenen Modells. Preprocessing (Kanalordnung/mean/std) aus MODELLE.
        Batcht in festen Stufen (BATCH_STUFEN, Padding = Wiederholung der letzten Zeile,
        Rueckgabe exakt len(crops_bgr) Zeilen); >8 Crops laufen in 8er-Chunks + Rest-Stufe."""
        spec = self._rec_spec
        batch = []
        for img in crops_bgr:
            x = img if spec.get("bgr") else cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            x = (x.astype(np.float32) - spec["mean"]) / spec["std"]
            batch.append(x.transpose(2, 0, 1))
        X = np.asarray(batch, np.float32)
        # Stufen+Padding NUR auf OpenVINO-Sessions (Compile-je-Shape-Thema). Auf CPU/CUDA
        # gibt es keine Shape-Kompilate — dort waere Padding reine Mehrarbeit (bis +60 %
        # Recognition-CPU beim cpu-Image) -> exakte Batchgroesse wie vor P4.
        if "OpenVINOExecutionProvider" not in self._rec.get_providers():
            E = self._rec.run(None, {self._rec_in: X})[0].astype(np.float32)
            E /= (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
            return E
        teile = []
        i = 0
        while i < len(X):
            teil = X[i:i + self.BATCH_STUFEN[-1]]
            n = len(teil)
            stufe = next(s for s in self.BATCH_STUFEN if s >= n)
            if stufe > n:                          # Padding: letzte Zeile wiederholen, Ergebnis wird verworfen
                teil = np.concatenate([teil, np.repeat(teil[-1:], stufe - n, axis=0)])
            E = self._rec.run(None, {self._rec_in: teil})[0][:n]
            teile.append(E)
            i += n
        E = np.concatenate(teile).astype(np.float32)
        E /= (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
        return E

    def _get_gestaffelt(self, img, max_num=0, vorschranke=None, det_metric="default"):
        """Detektion und Nacharbeit GETRENNT — Zwischenstufe fuer die Ernte-Vorschranke
        (bauplan_ernte_tempo.md §1): erst Boxen + 5 Keypoints, dann die teuren
        Nach-Modelle (landmark_3d_68 = Pose) NUR fuer die Gesichter, die
        `vorschranke(face)` durchlaesst. Aussortierte tragen die Marke
        `face.vorab_verworfen` und bleiben in der Rueckgabe (der Aufrufer zaehlt jede
        Detektion) — sie haben aber weder pose noch embedding.

        Der Rumpf ist ZEILENGLEICH zu insightface FaceAnalysis.get (face_analysis.py:77-96):
        dieselbe det_model.detect(max_num, metric)-Vorauswahl (Sortierung und die
        det_thresh-Filterung sitzen IN detect, get selbst tut nichts weiter), dieselbe
        Face-Bestueckung aus bboxes[i,0:4] / bboxes[i,4] / kpss[i], dieselbe
        Reihenfolge der Nach-Modelle je Gesicht. Damit ist die Kandidatenmenge
        konstruktiv dieselbe wie beim ungeteilten Weg (Plan-Risiko 2), und das
        Alignment des Embeddings nimmt weiter die 5 Detektor-Keypoints (Risiko 3).
        -> (alle_faces, ueberlebende)"""
        from insightface.app.common import Face
        bboxes, kpss = self.app.det_model.detect(img, max_num=max_num, metric=det_metric)
        if bboxes.shape[0] == 0:
            return [], []
        faces, weiter = [], []
        for i in range(bboxes.shape[0]):
            face = Face(bbox=bboxes[i, 0:4], det_score=bboxes[i, 4],
                        kps=(kpss[i] if kpss is not None else None))
            faces.append(face)
            if vorschranke is not None and not vorschranke(face):
                face.vorab_verworfen = True
                continue
            for taskname, model in self.app.models.items():
                if taskname == "detection":
                    continue
                model.get(img, face)
            weiter.append(face)
        return faces, weiter

    def _get_mit_rec(self, img, max_num=0, vorschranke=None):
        """Kapsel um insightface app.get: Faces detektieren/ausrichten wie gehabt, dann
        face.embedding je Gesicht mit dem eigenen Recognition-Modell ueberschreiben.

        `vorschranke` (Default None = Verhalten wie bisher, Zeile fuer Zeile): eine
        Auswahl-Funktion face->bool. Ist sie gesetzt, laufen Nach-Modelle UND die
        AdaFace-Inferenz nur fuer die Ueberlebenden — der Batch von _rec_infer wird
        dann ueber diese Teilmenge gebildet (die Zeilen sind je Crop unabhaengig,
        Padding auf die festen OV-Stufen bleibt Verschnitt und wird verworfen).
        Alle bestehenden Aufrufer rufen ohne das Argument und aendern sich nicht."""
        from insightface.utils import face_align
        if vorschranke is None:
            faces = self._orig_get(img, max_num=max_num)
            if faces:
                crops = [face_align.norm_crop(img, landmark=f.kps, image_size=112) for f in faces]
                E = self._rec_infer(crops)
                for f, e in zip(faces, E):
                    f.embedding = e
            return faces
        faces, weiter = self._get_gestaffelt(img, max_num=max_num, vorschranke=vorschranke)
        if weiter:
            crops = [face_align.norm_crop(img, landmark=f.kps, image_size=112) for f in weiter]
            E = self._rec_infer(crops)
            for f, e in zip(weiter, E):
                f.embedding = e
        return faces

    # ---------------------------------------------------------------- Sammelbatch
    # Live-Performance Welle 1, Etappe B (31.08.): Detektion und Embedding als
    # ZWEI Schritte, damit ein Aufrufer die Crops MEHRERER Bilder (bei uns:
    # mehrerer Waechter) zu EINEM Recognition-Lauf buendeln kann. Gemessen
    # 31.08. in der Placement-Messmatrix: Embedding-Sammelbatch 3,7x auf der
    # iGPU, 2,5x auf CUDA. (Detektions-Batching ist NICHT moeglich — die
    # SCRFD-ONNX hat Batch fest 1; das wurde gemessen und nicht versucht.)
    #
    # ZUSAMMEN sind die beiden Methoden ZEILENGLEICH zu _get_mit_rec(img)
    # ohne vorschranke — dieselbe Detektion, dieselben norm_crop-Crops,
    # dieselbe _rec_infer-Kette. Der EINZIGE Unterschied ist die
    # BATCHGROESSE, mit der _rec_infer laeuft. Das ist kein neuer
    # Effekt: die Batchgroesse schwankt heute schon je Bild mit der Zahl der
    # Gesichter, und die OpenVINO-Stufen (BATCH_STUFEN) padden ohnehin. Die
    # dokumentierte Groessenordnung dieser Abhaengigkeit steht bei NormMass
    # (1,2e-4 auf dem Embedding); die Zeilen des Batches sind je Crop
    # unabhaengig (kein Kontakt zwischen Batch-Zeilen im Graphen).
    def sammelbatch_moeglich(self):
        """Kann dieser Embedder Detektion und Embedding trennen? -> bool.

        NUR mit eigenem Recognition-Kopf (adaface): dort ist 'recognition' aus
        app.models entfernt und laeuft als eigener, batchfaehiger Lauf. Beim
        insightface-eigenen Kopf (buffalo) steckt sie als Modell IN der
        Gesichts-Schleife von app.get — sie herauszuloesen waere ein Umbau der
        Bibliotheks-Kette, kein Sammelbatch. Dort bleibt es beim Einzellauf."""
        return self._rec is not None

    def rec_geraet(self):
        """Auf welchem Geraet rechnet der Recognition-Kopf? -> 'NPU'|'GPU'|
        'CPU'|'CUDA'|… (Grossbuchstaben). Der Aufrufer entscheidet damit
        zwischen Sammelbatch (iGPU/CUDA) und parallelen Einzel-Requests (NPU) —
        gemessen 31.08.: auf der NPU bringen 2-4 gleichzeitige Requests 1,9x,
        ein Batch dort nichts."""
        kind, dev = self._backend
        if kind == "cpu":
            return "CPU"
        if kind == "openvino":
            return "NPU" if str(dev).upper() == "MIXED" else str(dev or "GPU").upper()
        return str(kind).upper()

    def detektieren(self, img, max_num=0):
        """Detektion + Nach-Modelle (Pose/Landmarks) OHNE Embedding
        -> (faces, crops112). Die Gegenstueck-Methode ist embeddings_setzen."""
        if self._rec is None:
            raise RuntimeError("detektieren() braucht den eigenen Recognition-"
                               "Kopf (sammelbatch_moeglich() ist False)")
        from insightface.utils import face_align
        faces = self._orig_get(img, max_num=max_num)
        if not faces:
            return [], []
        crops = [face_align.norm_crop(img, landmark=f.kps, image_size=112)
                 for f in faces]
        return faces, crops

    def embeddings_batch(self, crops_bgr):
        """norm_crop-112-Crops -> L2-normierte Embeddings, EIN Lauf.
        Duenne Huelle um _rec_infer, damit Aufrufer ausserhalb dieses Moduls
        keine Unterstrich-Methode anfassen muessen."""
        if self._rec is None:
            raise RuntimeError("embeddings_batch() braucht den eigenen "
                               "Recognition-Kopf")
        return self._rec_infer(list(crops_bgr))

    def faces_mit_vorschranke(self, img, vorschranke, max_num=0):
        """Der EINE Eintritt fuer Aufrufer, die eine Auswahl mitgeben wollen (Ernte).
        Deckt beide Recognition-Welten ab: mit eigenem ONNX-Kopf (adaface) ueber
        _get_mit_rec, ohne ihn (buffalo) direkt ueber _get_gestaffelt — dort steckt
        'recognition' noch in app.models und laeuft in derselben Schleife mit, also
        ebenfalls nur fuer die Ueberlebenden. Wer die Auswahl nicht braucht, ruft
        weiter app.get(img) und merkt von alledem nichts."""
        if self._rec is not None:
            return self._get_mit_rec(img, max_num=max_num, vorschranke=vorschranke)
        return self._get_gestaffelt(img, max_num=max_num, vorschranke=vorschranke)[0]

    @staticmethod
    def ar_det_size(breite, hoehe, basis=1280):
        """H4 (0.1.0.37): det_size aus dem Clip-Seitenverhaeltnis — lange Kante = basis,
        kurze Kante proportional, AUFGERUNDET auf ein Vielfaches von 32 (SCRFD-Anker-
        Gitter, Strides 8/16/32: nicht /32-teilige Kanten brechen die anchor_centers/
        net_outs-Zuordnung — Plan-QS W7). 16:9-4K -> (1280, 736): gemessen bit-identische
        Detektionen bei -27 % GPU-Zeit (recon H4); der quadratische 1280er-Default
        rechnete ~44 % der Detektorarbeit auf schwarzem Letterbox-Rand. 4:3 -> (1280, 960).
        Unbekannte Geometrie -> quadratischer Bestandswert (nie raten)."""
        if not breite or not hoehe:
            return (basis, basis)
        lang, kurz_px = (breite, hoehe) if breite >= hoehe else (hoehe, breite)
        kurz = (basis * kurz_px + lang - 1) // lang          # proportional, aufgerundet
        kurz = min(basis, max(32, ((kurz + 31) // 32) * 32))  # /32-Regel
        return (basis, kurz) if breite >= hoehe else (kurz, basis)

    def set_det_size(self, det_size):
        """det_size aendern OHNE die Sessions anzufassen (P1, 0.1.0.36).
        prepare(ctx_id=0) setzt in insightface NUR Attribute (input_size/det_thresh);
        bei ctx_id<0 dagegen rief jedes model.prepare() set_providers(['CPU...']) und
        RESETTETE alle Sessions still — der 16.07.-Bug, und obendrein ~17 CPU-s
        Doppelaufbau je Prozess (zweites prepare + zweites _to_backend, gemessen 26.07.).
        Der Guard darunter macht den Reset-Fall dauerhaft unmoeglich UND ueberwacht.
        Weiterhin gilt: NIE app.prepare() direkt aufrufen, immer diese Methode.

        .335 (User-Fund 24.08.): insightface DRUCKT bei jedem prepare eine
        'set det-size:'-Zeile. Die Live-Engine schaltet bei Waechtern mit
        verschiedenen Seitenverhaeltnissen das Netz je Frame um (ein geteilter
        Detektor-Kontext, Ping-Pong ~3/s) — 70k Zeilen in 6 h Prod-Log, echte
        Meldungen gingen darin unter. Der Bibliotheks-Druck wird deshalb hier
        GEFILTERT (nicht verschluckt: alles andere aus dem Fenster wird
        weitergereicht, damit nie eine fremde Logzeile verloren geht). WAS
        gesetzt ist, zeigen Startup-Selbstcheck und /health; die Wechselkosten
        selbst bleiben der dokumentierte offene Messpunkt (core/livewached)."""
        import contextlib
        import io
        _buf = io.StringIO()
        with contextlib.redirect_stdout(_buf):
            self.app.prepare(ctx_id=0, det_size=det_size)
        for _z in _buf.getvalue().splitlines():
            if _z.strip() and not _z.startswith("set det-size"):
                print(_z)
        self._provider_guard("set_det_size")

    def _provider_guard(self, anlass):
        """P1 (User 26.07. — der 16.07.-Bug als DAUER-Absicherung): nach jedem prepare/
        Aufbau an den ECHTEN Sessions verifizieren, dass jede noch auf dem Soll-Provider
        liegt (get_providers(), nie Latenz raten). Abweichung -> laute stderr-Zeile
        (Marker 'PROVIDER-GUARD', verifyd hebt ihn ins Dienst-Log) + EIN Selbstheilungs-
        versuch via _to_backend(); bleibt es falsch, laeuft das System DEGRADIERT weiter
        und sagt es. Auf dem cpu-Backend gibt es kein Soll ausser CPU -> immer ok."""
        kind, _dev = self._backend
        if kind == "cpu":
            return True
        from core.registry import ep_von                  # P3.1: EP-Namen aus der Registry
        soll = ep_von(kind) if kind != "cpu" else None
        if not soll:
            return True

        def _falsche():
            fx = [n for n, m in self.app.models.items()
                  if getattr(m, "session", None) is not None
                  and soll not in m.session.get_providers()]
            if self._rec is not None and soll not in self._rec.get_providers():
                fx.append("recognition(own)")
            return fx

        fx = _falsche()
        if not fx:
            return True
        sys.stderr.write(f"[face_audit] PROVIDER-GUARD ({anlass}): session(s) "
                         f"{', '.join(fx)} fell off {soll} — rebuilding on backend\n")
        self._to_backend()
        fx = _falsche()
        if fx:
            sys.stderr.write(f"[face_audit] PROVIDER-GUARD FAILED ({anlass}): "
                             f"{', '.join(fx)} still not on {soll} — RUNNING DEGRADED "
                             f"(runtime vs. host driver? check the startup self-check)\n")
            return False
        return True

    def _to_backend(self):
        """Ersetzt die insightface-ONNX-Sessions UND das eigene Recognition-ONNX durch Sessions auf
        dem gewaehlten Backend (self._backend). BEIDE muessen umziehen, sonst Detektion auf dem
        Beschleuniger, Recognition auf CPU = gemischte Devices. openvino:MIXED verteilt Tasks
        GPU/NPU (nur OpenVINO). cache_dir cacht kompilierte OV-Blobs (nur 1. Lauf kompiliert).
        cpu-Backend (#21-Fix): gleiche Ersatz-Mechanik, nur mit CPU-Provider — die nativen
        prepare()-Sessions kommen OHNE SessionOptions und bauen je einen Intra-Op-Pool nach
        hardware_concurrency des WIRTS (nicht der cgroup-Maske); erst der Ersatz mit
        _ort_thread_opts laesst SUSLIK_CPU_THREADS bzw. die erlaubten Kerne ALLE Sessions
        deckeln. self._rec bleibt auf cpu unangetastet: der traegt seine Kappung schon aus
        _init_rec_onnx (Neuaufbau waere nur doppelte Ladezeit)."""
        kind, dev = self._backend
        if kind == "cpu":
            for task, model in self.app.models.items():
                s = _ort_session("cpu", None, model.model_file)
                model.session = s
                model.input_name = s.get_inputs()[0].name
                model.output_names = [o.name for o in s.get_outputs()]
            return
        # W0 (GPU-Welle, 26.07.): Kompilat-Cache ins VOLUME statt ~/.cache im Container-Layer —
        # sonst zahlt jeder Image-Pull die volle OV-Kaltkompilierung neu (Plan-QS Lens3-13).
        # VERIFY_DATA_DIR ist im Container immer gesetzt (/data); der Host-venv-Lauf ohne die
        # Variable behaelt den alten ~/.cache-Pfad (Verhalten dort unveraendert).
        _dd = os.environ.get("VERIFY_DATA_DIR")
        cache = os.environ.get("OV_CACHE_DIR",
                               os.path.join(_dd, "clips", "ov_cache_models") if _dd
                               else os.path.expanduser("~/.cache/ov_face_buffalo_l"))
        if kind == "openvino":
            os.makedirs(cache, exist_ok=True)
        # MIXED bleibt (Live-Performance Welle 1, Etappe C — MESSBELEG, kein
        # Umbau): die Placement-Messmatrix vom 31.08. hat die Verteilung auf
        # der Autor-Maschine (Core Ultra 9 285H, iGPU + NPU) unter Doppellast
        # gegen die Alternativen gemessen. Det auf der iGPU + Embedding auf der
        # NPU liefert 42/61 Bilder je Sekunde und ist damit die BESTE
        # Verteilung — genau diese Zuordnung hier. GPU-only kostet das
        # 1,4- bis 2,7-fache. Und AUTO:GPU,NPU wird ausdruecklich NICHT
        # eingefuehrt: es war unter Last schlechter, und seine
        # load_config-Variante faellt STILL auf die CPU zurueck (K1-Klasse).
        mixed = {"detection": "GPU", "landmark_3d_68": "GPU", "landmark_2d_106": "GPU",
                 "genderage": "GPU", "recognition": "NPU"}
        def _dev(task):                               # MIXED ist ein OpenVINO-Untermodus, kein generisches Backend
            return mixed.get(task, "GPU") if (kind == "openvino" and dev == "MIXED") else dev
        for task, model in self.app.models.items():
            s = _ort_session(kind, _dev(task), model.model_file, cache)
            model.session = s
            model.input_name = s.get_inputs()[0].name
            model.output_names = [o.name for o in s.get_outputs()]
        if self._rec is not None:                     # eigenes Recognition-ONNX auf denselben Beschleuniger
            s = self._session_kette(kind, _dev("recognition"), self._rec_spec["onnx"], cache)
            self._rec = s
            self._rec_in = s.get_inputs()[0].name
            self._rec_warmup()

    def _session_kette(self, kind, dev, onnx, cache):
        """P4: echte Fallback-KETTE fuers Recognition-Placement (NPU -> GPU -> CPU) statt des
        direkten CPU-Absturzes aus _ort_session. Bindet ein OpenVINO-Wunsch-Device nicht
        (EP faellt aus get_providers()), wird das NAECHSTE Device der Kette versucht und der
        Rueckfall LAUT markiert ('PLACEMENT-FALLBACK', verifyd hebt Marker ins Dienst-Log);
        erst am Ketten-Ende bleibt CPU. Nicht-OpenVINO-Backends (cuda/cpu) unveraendert."""
        if kind != "openvino":
            return _ort_session(kind, dev, onnx, cache)
        kette = {"NPU": ["NPU", "GPU"], "GPU": ["GPU"]}.get(dev, [dev])
        for i, d in enumerate(kette):
            s = _ort_session(kind, d, onnx, cache)
            if "OpenVINOExecutionProvider" in s.get_providers():
                if i:
                    sys.stderr.write(f"[face_audit] PLACEMENT-FALLBACK: recognition "
                                     f"{dev} -> {d} (device did not bind)\n")
                return s
        sys.stderr.write(f"[face_audit] PLACEMENT-FALLBACK: recognition {dev} -> CPU "
                         f"(no OpenVINO device bound)\n")
        return _ort_session("cpu", None, onnx, cache)

    def _rec_warmup(self):
        """P4.0-Auflage: die festen Batch-Stufen einmal vorkompilieren, damit der Betrieb
        re-compile-frei laeuft (erste Shape-Inferenz kostet auf NPU ~3,2 s / iGPU ~1,7 s;
        mit warmem OV-Cache Sekundenbruchteile). NUR auf OpenVINO-Sessions — auf CPU waere
        das reine Verschwendung (~4 CPU-s je Stufe, kein Compile-Thema)."""
        if self._rec is None or "OpenVINOExecutionProvider" not in self._rec.get_providers():
            return
        import time as _t
        t0 = _t.perf_counter()
        for stufe in self.BATCH_STUFEN:
            x = np.zeros((stufe, 3, 112, 112), np.float32)
            self._rec.run(None, {self._rec_in: x})
        sys.stderr.write(f"[face_audit] rec warmup: batches {'/'.join(map(str, self.BATCH_STUFEN))} "
                         f"in {_t.perf_counter() - t0:.1f}s (OV cache keeps them warm)\n")

    def embed(self, img_bgr):
        h, w = img_bgr.shape[:2]
        scale = max(1.0, 224.0 / min(h, w))         # kurze Kante >=224px
        if scale > 1.0:
            img_bgr = cv2.resize(img_bgr, (round(w*scale), round(h*scale)),
                                 interpolation=cv2.INTER_CUBIC)
        faces = self.app.get(img_bgr)
        if not faces:
            return None
        f = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]))
        return np.asarray(f.normed_embedding, dtype=np.float64)

# ---------------------------------------------------------------- Feature-Norm (Vorrat)
def gesichtsreiz(n=112, kontrast=1.0):
    """Deterministischer synthetischer Gesichtsreiz (uint8, HWC, Kanalfolge BGR) —
    der Mess-Eingang der Norm-Kreuzprobe. Kein Zufall, kein Bild auf Platte, keine
    Personendaten: dieselbe Zahl kommt auf jeder Maschine heraus.

    HERKUNFT: Rechenweg wortgleich der Funktion `face(n)` aus
    tester/gputest_kommandos_tokn59.md (Kommando 1 und 3, am echten Fremdsystem
    erprobt) — heller Gesichtsfleck auf einem Helligkeitsverlauf, sechs Gauss-Marken
    fuer Augen, Brauen, Nase und Mund, die drei Kanaele leicht gegeneinander
    verschoben. Bei kontrast=1.0 liefert diese Funktion Pixel fuer Pixel dasselbe
    Bild wie die Vorlage; die Zahlen aus Tester-Rueckmeldungen bleiben damit direkt
    vergleichbar.

    WARUM NICHT MEHR RAUSCHEN (Grund der Umstellung, gemessen 24.08.2026): dem
    adaface-Kopf faellt standard_normal-Rauschen auf Feature-Norm 11,63 / 12,23.
    Die Betriebsentscheidungen fallen aber bei 21,5 / 22,0 / 23,5 / 24,0. Die alte
    Kreuzprobe hat also an einem Arbeitspunkt gemessen, an dem gar nichts entschieden
    wird — und dort ist der Fehler kleiner: dieselbe gesunde iGPU weicht im Rauschen
    0,099 ab, auf diesem Gesichtsreiz 0,149 und auf echten Crops bis 0,67
    (Nachmessung 21.08., 2052 benannte Gesichter). Zweiter Grund: SCRFD detektiert
    Rauschen ueberhaupt nicht, derselbe Reiz traegt deshalb auch Detektions-Proben.

    kontrast skaliert die Amplitude UM DEN BILDMITTELWERT (die Helligkeit bleibt,
    der Kontrast waechst oder faellt) und verschiebt damit den Arbeitspunkt.
    Gemessen auf CPU: Norm 24,930 (0,7) / 26,066 (1,0) / 27,048 (1,4) — real
    gemessene Crops liegen bei 15..30, die Linien bei 21,5..24,0."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / (n - 1.0)
    v = 60 + 40 * y + 150 * np.exp(-3 * (((x - .5) / .30) ** 2 + ((y - .52) / .40) ** 2))
    for cx, cy, rx, ry, a in ((.36, .42, .09, .05, -90), (.64, .42, .09, .05, -90),
                              (.50, .74, .18, .05, -70), (.36, .30, .11, .03, -45),
                              (.64, .30, .11, .03, -45), (.50, .58, .05, .10, 25)):
        v = v + a * np.exp(-2 * (((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))
    if kontrast != 1.0:
        mitte = float(v.mean())
        v = mitte + (v - mitte) * kontrast
    return np.stack([np.clip(v * .92, 0, 255), np.clip(v * .97, 0, 255),
                     np.clip(v * 1.03, 0, 255)], -1).astype(np.uint8)


class NormMass:
    """Referenzfreies Guetemass ||f|| — die Laenge des UNNORMIERTEN Feature-Vektors
    vor der L2-Normierung des adaface-Kopfs (Messreihe 20.08.2026: trennt oberes
    vom unteren Brauchbarkeits-Quartil mit AUC 0.731, deutlich vor det_score;
    verify_data/messungen/qualitaetsmass_20260820.json). Traeger des Lernvorrats
    (Bauplan bauplan_vorrat.md B1).

    STRIKT GETRENNT vom Urteilspfad: eigene Session, Geraet aus der Kette dieses
    Backends (kette_fuer_backend, seit .506 — davor die feste NORM_KETTE) mit
    Kreuzprobe gegen CPU (seit .313; die aeltere Angabe "IMMER CPU" galt bis dahin),
    exakte Batchgroessen ohne Padding. Gemessen 20.08.: ein Zusatz-Graph-Ausgang
    laesst 'embedding' auf CPU bit-genau unveraendert (maxdiff exakt 0.0),
    verschiebt es auf OpenVINO aber um 1.2e-4, und die Norm selbst schwankt dort
    zwischen Batchgroessen um bis zu 0.047 — deshalb ist CPU hier keine
    Sparsamkeit, sondern die Messbedingung. Der Embedder und seine Sessions
    werden von dieser Klasse NIE beruehrt.

    Der Graph entsteht IN-MEMORY aus dem eingebackenen adaface-ONNX (kein
    zweites Modell-File, kein Netz — self-contained-Regel): der adaface-Kopf
    endet auf f -> ReduceL2 -> Div, der eine Div-Knoten liefert den Graph-
    Ausgang 'embedding'; sein erster Input IST f. Aus f/||f|| laesst sich ||f||
    nicht zurueckrechnen, darum wird f als ZUSATZ-Ausgang deklariert. Nach dem
    Session-Bau werden ModelProto und Bytes sofort freigegeben. Der Bau bleibt
    trotzdem teuer (gemessen 24.08.2026, VmHWM: Erstbau auf der Geraete-Kette
    2,7 GB, aus warmem Kompilat-Cache 2,0 GB, reiner CPU-Weg 1,1 GB) — wer ihn
    ausloest, setzt eine Budget-Pruefung davor und meldet ihn seiner
    Speicherwache an (worker._normmass_fuer_ernte).

    Jede Abweichung (fremdes Modell, unerwartete Graph-Struktur, Konsistenz-
    probe schlaegt fehl) setzt ok=False mit LAUTEM stderr-Marker 'NORMMASS' —
    der Vorrat degradiert dann ab, der Dienst laeuft unveraendert weiter."""

    # .313 GERAETEWAHL (gemessen 21.08., 412 echte Crops, Batch 1): NPU 9 ms je
    # Gesicht gegen CPU 232 ms bei max. Versatz 0,09 / p99 0,04 auf der 15-30-Skala
    # (1 Kipper von 412 an der 23,5-Linie, Batch-Drift 0,000 bei fester Batchgroesse 1).
    # Die CPU war Messbedingung (.306), weil OpenVINO die Norm zwischen BATCHGROESSEN
    # um bis zu 0,047 verschob — mit Batch 1 (Einzel-Inferenz je Gesicht, wie die Ernte
    # sie fuehrt) tritt das nicht auf. NACHMESSUNG auf 2052 benannten Lernlauf-
    # Gesichtern (21.08.): NPU p99 0,05 / max 0,12, Kipper an den Linien 21,5/22/23,5/24
    # = 0/3/1/1 (<= 0,15 %); iGPU 31 ms, p99 0,36 / max 0,67, Kipper 25/17/5/5 (<= 1,2 %).
    # Die GPU ist damit zweite Stufe fuer Intel-Systeme OHNE NPU (sonst 232 ms je
    # Gesicht, ~50-min-Laeufe): ~1 % Kipper am Qualitaetstor sind messbar, aber kein
    # Urteilsfehler.
    #
    # .336 FP32-STUFE (24.08.2026): zwischen GPU und CPU steht jetzt GPU_FP32 —
    # dieselbe iGPU, aber mit erzwungener FP32-Rechnung statt der OpenVINO-
    # Voreinstellung fp16. Anlass ist der Feldfall Tokn59 (Gen8-iGPU, keine
    # fp16-Einheiten): seine GPU bindet, rechnet 5,9x schneller als seine CPU und
    # wird von der Kreuzprobe mit 105,276 verworfen — auf CPU laeuft er damit in
    # ~50-min-Laeufe. Faellt fp16, ist FP32 der letzte Halt vor der CPU, nicht der
    # Sturz auf sie. Kette: NPU -> GPU -> GPU_FP32 -> CPU;
    # SUSLIK_NORM_DEVICE=CPU|NPU|GPU|GPU_FP32|CUDA erzwingt. Jede Nicht-CPU-Session
    # wird per KREUZPROBE gegen eine CPU-Session geprueft (|dNorm| <=
    # NORM_KREUZ_MAX auf dem gepinnten Gesichtsreiz), sonst LAUT naechste Stufe.
    #
    # .506 CUDA-STUFE (05.09.2026, User-Entscheid nach der Ernte-Messung —
    # ersetzt den bisherigen Satz "CUDA/ROCm sind ungemessen und bleiben auf CPU"):
    # NVIDIA ist jetzt GEMESSEN und bekommt eine eigene Kette CUDA -> CPU.
    # Anlass war der Zeitanteil: auf dem CUDA-Testnotebook (RTX 2060, i7-10750H,
    # onnxruntime-gpu 1.26.0, Image 0.1.0.505-cuda) steckten 51,13 von 64,85 s je
    # ERNTE-EREIGNIS = 78,8 % allein in dieser einen CPU-Stufe, waehrend Detektion,
    # Pose und Embedding desselben Laufs nachweislich auf cuda:0 liefen und die
    # Karte sich bei 7 % Median-Auslastung langweilte. Gemessen am selben Tag:
    #   Norm je Bild, Batch 1, echte 112er-Crops   CPU 0,554 s   CUDA 0,0159 s (x34,8)
    #   Kreuzprobe am Gesichtsreiz (3 Skalen)      max |dNorm| 0,00000
    #   64 echte Crops, Norm-Spanne 16,80..26,01   max |dNorm| 0,00002
    # 0,00002 liegt Faktor 5000 unter NORM_KREUZ_MAX und weit unter dem Versatz der
    # NPU (0,013), die die Kette schon traegt — die CUDA-Session rechnet fp32 und
    # hat das fp16-Problem der iGPU nicht, deshalb braucht diese Stufe auch keine
    # Praezisions-Achse (der CUDA-EP kennt sie ohnehin nicht). End-to-End gefahren
    # faellt ein Ernte-Ereignis von 64,85 auf 11,78 s bei Zeile fuer Zeile
    # identischen Zaehlern (144 Detektionen / 124 Kandidaten / 91 M / 27 S / 74 V).
    # Belegt in backups/bau_0505/analyse_ernte_gpu/bericht.md, Abschnitte 1a/2/5.
    # ROCm/MIGraphX bleibt UNGEMESSEN (kein Geraet hier) und damit auf CPU — das
    # ist keine Aussage ueber AMD, sondern das Fehlen einer Messung.
    #
    # EICHBASIS DER SCHWELLE — gemessen 24.08.2026 auf dieser Maschine (LXC suslik
    # .168, Core Ultra 9 285H, iGPU + NPU, OpenVINO-EP, adaface_ir101, Batch 1,
    # je 12 Wiederholungen; Reiz = gesichtsreiz() in drei Kontrast-Skalen):
    #
    #   Geraet          Norm 0,7   Norm 1,0   Norm 1,4   |dNorm| max   Streuung/12
    #   CPU (Referenz)  24,930     26,066     27,048     —             0,000
    #   NPU             24,932     26,075     27,061     0,013         0,000
    #   GPU (fp16)      24,874 /   26,096     26,899     0,149         0,050
    #                   24,923                                         (Skala 0,7)
    #   GPU_FP32        24,930     26,066     27,048     0,0000095     0,000
    #
    # Derselbe Lauf am ALTEN Rausch-Arbeitspunkt (Norm 11,63 / 12,23): NPU 0,007,
    # GPU fp16 0,099, GPU_FP32 0,0000067 — das Rauschen zeigt den fp16-Fehler nur
    # zu zwei Dritteln und liegt 10 Norm-Punkte neben jeder Entscheidung.
    #
    # HERLEITUNG 0,10 (nicht mehr 0,30, und die 0,30 war nie am Arbeitspunkt geeicht):
    #  * Decke aus der Entscheidungs-Sicherheit: die engsten Qualitaetslinien liegen
    #    0,5 auseinander (21,5/22,0 und 23,5/24,0). Ein Geraet, dessen Norm um mehr
    #    als den halben Abstand (0,25) wandert, kann Entscheidungen kippen — 0,25 ist
    #    die absolute Obergrenze, 0,10 haelt Faktor 2,5 Abstand dazu.
    #  * Boden aus der Messung: die NPU, das schnelle Geraet, das bestehen MUSS,
    #    weicht 0,013 ab — Faktor 8 Luft nach oben.
    #  * BEWUSST NICHT ERFUELLT ist "deutlich ueber jedem gesunden Geraet": die
    #    gesunde fp16-iGPU dieser Maschine liegt mit 0,149 UEBER der Schwelle und
    #    faellt damit auf GPU_FP32. Beides zugleich geht nicht (0,149 < x < 0,25
    #    waere weder das eine noch das andere "deutlich"), und dann gewinnt die
    #    Entscheidungs-Sicherheit: dieselbe iGPU wich auf echten Crops bis 0,67 ab
    #    (Nachmessung 21.08.), der Reiz unterschaetzt das echte Material also um
    #    Faktor ~4,5. Dazu ist fp16 hier nicht einmal reproduzierbar (0,050
    #    Streuung zwischen zwoelf Laeufen derselben Session, waehrend NPU und FP32
    #    bitgenau wiederholen). Der Preis ist Rechenzeit, nicht das Geraet: der
    #    Rueckfall geht auf GPU_FP32 (0,0000095), nicht auf die CPU.
    NORM_KREUZ_MAX = 0.10
    NORM_KREUZ_SKALEN = (0.7, 1.0, 1.4)
    # Die Intel-Kette. Seit .506 ist sie NICHT mehr die Kette schlechthin, sondern
    # die des openvino-Backends — gefragt wird ueber kette_fuer_backend(). Sie bleibt
    # als eigene Konstante stehen, weil sie die gemessene Reihenfolge TRAEGT (die
    # Eich-Tabelle oben gehoert zu genau diesen vier Stufen) und weil Gate und
    # Modell-Vertrag sie namentlich zitieren.
    NORM_KETTE = ("NPU", "GPU", "GPU_FP32", "CPU")

    @classmethod
    def kette_fuer_backend(cls, kind):
        """Die Geraete-Kette der Feature-Norm fuer EIN ML-Backend (kind aus
        resolve_backend) — DIE eine Quelle dafuer, welche Stufen die Norm auf dieser
        Maschine ueberhaupt probiert (qs_ebenen-Regel: keine zweite verstreute
        Aufzaehlung; core.rechenprobe.norm_geraet fragt genau hier).

          openvino  NORM_KETTE, unveraendert seit .336 (NPU -> GPU -> GPU_FP32 -> CPU)
          cuda      CUDA -> CPU (.506, gemessen 05.09.2026, s. GERAETEWAHL oben)
          sonst     nur CPU — migraphx/ROCm ist ungemessen, und ein cpu-Backend hat
                    per Definition keinen Beschleuniger, den die Norm nehmen darf.

        BEWUSSTE VERHALTENSAENDERUNG .506, damit sie niemanden ueberrascht: bis .505
        lief diese Kette fuer JEDES Backend, die Norm griff also auch dann nach NPU
        und iGPU, wenn der Nutzer als Backend ausdruecklich `cpu` gewaehlt hatte.
        Auf dem cpu-Image war das folgenlos (ohne OpenVINO-EP endete die Kette
        ohnehin auf CPU); auf dem gpu-Image mit Backend `cpu` rechnete die Norm
        seither auf der NPU. Jetzt folgt sie der Backend-Wahl. Wer die alte Stufe
        dort weiter will, setzt SUSLIK_NORM_DEVICE (das erzwingt weiterhin JEDES
        Geraet, auch quer zum Backend)."""
        k = str(kind or "").strip().lower()
        if k == "openvino":
            return cls.NORM_KETTE
        if k == "cuda":
            return ("CUDA", "CPU")
        return ("CPU",)

    def __init__(self, modell=None, device=None):
        import onnxruntime as ort
        ort.set_default_logger_severity(3)   # auch OHNE Embedder im Prozess kein ORT-Spam
        self.ok = False
        self.grund = ""
        self.device = "CPU"
        self.modell = (modell or aktuelles_modell()).lower()
        spec = MODELLE.get(self.modell) or {}
        if self.modell != "adaface" or spec.get("art") != "onnx":
            # Die Norm-Schwellen (22/21.5/23-Linie) sind an adaface gemessen —
            # auf einem anderen Kopf waeren sie Zahlen ohne Bedeutung.
            self.grund = (f"feature norm is calibrated for 'adaface' only "
                          f"(active model: '{self.modell}')")
            sys.stderr.write(f"[face_audit] NORMMASS: {self.grund} -> disabled\n")
            return
        self._spec = spec
        try:
            self._sess, self.device = self._session_waehlen(spec["onnx"], device)
        except Exception as ex:                                # noqa: BLE001
            self.grund = f"graph variant failed: {type(ex).__name__}: {str(ex)[:200]}"
            sys.stderr.write(f"[face_audit] NORMMASS: {self.grund} -> disabled\n")
            return
        self._in = self._sess.get_inputs()[0].name
        namen = [o.name for o in self._sess.get_outputs()]
        if "embedding" not in namen or len(namen) != 2:
            self.grund = f"unexpected outputs {namen}"
            sys.stderr.write(f"[face_audit] NORMMASS: {self.grund} -> disabled\n")
            return
        self._idx_emb = namen.index("embedding")
        self._idx_f = 1 - self._idx_emb
        abw = self._konsistenzprobe()
        # Toleranz je Geraet: CPU exakt (1e-4); ein Beschleuniger rechnet intern in
        # fp16 — dort gilt 1e-2 fuer f/||f|| gegen den embedding-Ausgang DERSELBEN
        # Session (die Norm-Guete selbst sichert die Kreuzprobe gegen CPU).
        if abw > (1e-4 if self.device == "CPU" else 1e-2):
            if self.device != "CPU":
                sys.stderr.write(f"[face_audit] NORMMASS: consistency probe on {self.device} "
                                 f"off by {abw:.2e} -> CPU\n")
                try:
                    self._sess = self._feature_norm_session(spec["onnx"], "CPU")
                    self.device = "CPU"
                    self._in = self._sess.get_inputs()[0].name
                    abw = self._konsistenzprobe()
                except Exception as ex:                        # noqa: BLE001
                    abw = float("inf"); self.grund = f"CPU fallback failed: {ex}"
            if abw > 1e-4:
                # Falsche Modellvariante wuerde sonst still falsche "Normen" liefern
                # (der Prototyp-Erstlauf starb genau daran: Werte um 0 statt um 23).
                self.grund = self.grund or f"consistency probe failed (f/||f|| vs embedding, maxdiff {abw:.2e})"
                sys.stderr.write(f"[face_audit] NORMMASS: {self.grund} -> disabled\n")
                return
        self.ok = True

    @staticmethod
    def _graph_bytes(pfad):
        """adaface-ONNX -> Graph-Bytes mit f als Zusatz-Ausgang (in-memory)."""
        import onnx
        m = onnx.load(pfad)
        aus = {o.name for o in m.graph.output}
        div = [n for n in m.graph.node
               if n.op_type == "Div" and n.output and n.output[0] in aus]
        if len(div) != 1:
            raise ValueError(f"expected exactly ONE Div node feeding a graph "
                             f"output, found {len(div)}")
        f_name = div[0].input[0]
        m.graph.output.append(
            onnx.helper.make_tensor_value_info(f_name, onnx.TensorProto.FLOAT, None))
        roh = m.SerializeToString()
        del m                                    # Bauspitze druecken (W2.9)
        return roh

    @classmethod
    def _feature_norm_session(cls, pfad, device="CPU", roh=None):
        """Session fuer ein Geraet: CPU = CPUExecutionProvider; CUDA = CUDA-EP mit
        CPU-Rueckfall in der Provider-Liste; NPU/GPU/GPU_FP32 = OpenVINO-EP, nur wenn
        der EP da ist, der Geraeteknoten existiert und der Provider WIRKLICH bindet
        (sonst ValueError — der Aufrufer geht die Kette weiter). GPU_FP32 ist ein
        Pseudo-Geraet (NORM_PSEUDO_GERAETE): dasselbe device_type GPU, aber mit
        precision=FP32 statt der Voreinstellung fp16."""
        import onnxruntime as ort
        roh = roh if roh is not None else cls._graph_bytes(pfad)
        dev = str(device or "CPU").upper()
        if dev == "CPU":
            return ort.InferenceSession(roh, providers=["CPUExecutionProvider"],
                                        sess_options=_ort_thread_opts())
        if dev == "CUDA":
            # .506 (05.09.2026): der CUDA-Zweig. BEWUSST OHNE zwei OpenVINO-Zutaten,
            # die hier nichts zu suchen haetten: kein Geraeteknoten-Vorcheck (der
            # faengt bei OpenVINO den Treiber-Spam eines chancenlosen Versuchs ab —
            # CUDA bindet oder bindet nicht, und genau das prueft die Wache unten)
            # und kein cache_dir (Kompilat-Cache ist eine OpenVINO-Sache).
            # Provider-Liste wortgleich _ort_session: Beschleuniger PLUS CPU-
            # Rueckfall, sonst bricht der Bau, sobald EIN Graph-Knoten nicht auf dem
            # EP laeuft. Still wird der Rueckfall dadurch nicht — er faellt der
            # Bind-Pruefung auf.
            if "CUDAExecutionProvider" not in ort.get_available_providers():
                raise ValueError(f"{dev}: CUDA EP not available")
            # Die GERAETENUMMER steht nicht im Namen der Norm-Stufe (die heisst nur
            # "CUDA"), sondern im Backend des Prozesses — dieselbe Quelle, aus der
            # sich der Embedder bedient (_ort_session, cuda-Zweig). Quer zum
            # Backend erzwungen (SUSLIK_NORM_DEVICE=CUDA auf einer OV-Maschine)
            # gibt es keine Nummer, dann gilt Geraet 0 wie dort.
            _kind, _dev = resolve_backend(None)
            try:
                _did = int(_dev) if _kind == "cuda" else 0
            except (TypeError, ValueError):
                _did = 0
            s = ort.InferenceSession(
                roh, providers=[("CUDAExecutionProvider", {"device_id": _did}),
                                "CPUExecutionProvider"],
                sess_options=_ort_thread_opts())
            if "CUDAExecutionProvider" not in s.get_providers():
                raise ValueError(f"{dev}: provider did not bind")
            return s
        if "OpenVINOExecutionProvider" not in ort.get_available_providers():
            raise ValueError(f"{dev}: OpenVINO EP not available")
        import glob as _glob
        knoten = geraete_knoten_muster(dev)
        if knoten and not _glob.glob(knoten):
            raise ValueError(f"{dev}: no device node ({knoten})")
        pseudo = NORM_PSEUDO_GERAETE.get(dev)
        opts = {"device_type": pseudo["ov_device"] if pseudo else dev}
        if pseudo:
            opts["precision"] = pseudo["precision"]
        # Kompilat-Cache ins Volume: ohne cache_dir kompiliert OpenVINO diesen
        # Graphen bei JEDEM Bau neu. SCRATCH_DIR (<data_dir>/clips) setzt der
        # Dienst beim Worker-Start; im Dienst-Prozess selbst und im nackten
        # CLI-Lauf fehlt sie — dann bleibt es beim Kompilieren, denn ein leerer
        # oder fehlender Wert darf hier NIE landen (als String "None" legte
        # OpenVINO einen Ordner "None/" im CWD an, s. _ort_session).
        # GPU und GPU_FP32 teilen sich DIESES Verzeichnis, und das ist geprueft,
        # nicht angenommen: Probe 24.08.2026 in einem leeren Cache, erst fp16
        # bauen, dann FP32 im SELBEN Verzeichnis — OpenVINO legte einen ZWEITEN
        # Blob an (134 MB fp16 gegen 264 MB FP32, exakt die doppelten Gewichte)
        # und lieferte die saubere FP32-Norm 26,06628 statt der fp16-Zahl
        # 26,14316. Der Cache-Schluessel enthaelt die Praezision, ein eigenes
        # Unterverzeichnis waere nur doppelte Ablage.
        _scratch = (os.environ.get("SCRATCH_DIR") or "").strip()
        if _scratch:
            cache = os.path.join(_scratch, "ov_cache")
            try:
                os.makedirs(cache, exist_ok=True)
                opts["cache_dir"] = cache
            except OSError:      # read-only Volume: dann ohne Cache bauen — der
                pass             # Ausfall des Caches ist kein Grund, das Geraet zu verlieren
        s = ort.InferenceSession(roh, providers=["OpenVINOExecutionProvider"],
                                 provider_options=[opts],
                                 sess_options=_ort_thread_opts())
        if "OpenVINOExecutionProvider" not in s.get_providers():
            raise ValueError(f"{dev}: provider did not bind")
        return s

    @classmethod
    def _session_waehlen(cls, pfad, device=None):
        """Die Kette DIESES Backends (kette_fuer_backend: Intel NPU -> GPU ->
        GPU_FP32 -> CPU, NVIDIA CUDA -> CPU, sonst CPU; oder ein erzwungenes Geraet
        ueber device=/SUSLIK_NORM_DEVICE): JEDE Nicht-CPU-Session besteht eine
        Kreuzprobe gegen CPU (|dNorm| <= NORM_KREUZ_MAX auf dem gepinnten
        Gesichtsreiz), sonst LAUT weiter zur naechsten Stufe. Die GPU-Stufen tragen
        Intel-Systeme OHNE NPU, GPU_FP32 faengt Geraete auf, deren fp16-Rechnung die
        Norm verschiebt (Begruendung und Messwerte im GERAETEWAHL-Kommentar oben).
        -> (session, geraetename)."""
        roh = cls._graph_bytes(pfad)
        wunsch = (device or os.environ.get("SUSLIK_NORM_DEVICE") or "").strip().upper()
        # Ohne Zwang entscheidet das ML-Backend des Prozesses, welche Stufen es
        # ueberhaupt gibt (.506) — nicht mehr eine feste Klassenkonstante fuer alle.
        kette = (wunsch,) if wunsch else cls.kette_fuer_backend(resolve_backend(None)[0])
        if "CPU" not in kette:
            kette = tuple(kette) + ("CPU",)
        cpu = None
        for dev in kette:
            if dev == "CPU":
                return (cpu or cls._feature_norm_session(pfad, "CPU", roh)), "CPU"
            try:
                s = cls._feature_norm_session(pfad, dev, roh)
                cpu = cpu or cls._feature_norm_session(pfad, "CPU", roh)
                abw = cls._kreuzprobe(s, cpu)
                if abw > cls.NORM_KREUZ_MAX:
                    raise ValueError(f"cross-check vs CPU off by {abw:.3f}")
                sys.stderr.write(f"[face_audit] NORMMASS: feature norm on {dev} "
                                 f"(cross-check vs CPU max |dNorm| {abw:.3f})\n")
                # Die CPU-Referenz hat ihren einzigen Zweck erfuellt. Beide
                # Sessions gleichzeitig zu halten IST die Bauspitze (gemessen
                # 24.08.2026: 2,7 GB Geraet+CPU gegen 1,1 GB CPU allein). Das
                # OS bekommt den Speicher damit NICHT zurueck (ORT-Arena,
                # Soak-Befund 27.07.), aber der Prozess kann ihn wiederverwenden
                # statt neben der Arena weiterzuwachsen.
                del cpu
                import gc
                gc.collect()
                return s, dev
            except Exception as ex:                            # noqa: BLE001
                sys.stderr.write(f"[face_audit] NORMMASS: {dev} not used "
                                 f"({type(ex).__name__}: {str(ex)[:120]}) -> next\n")
        return (cpu or cls._feature_norm_session(pfad, "CPU", roh)), "CPU"

    @classmethod
    def _kreuz_eingaben(cls):
        """Die gepinnten Kreuzproben-Eingaenge: der Gesichtsreiz in
        NORM_KREUZ_SKALEN, vorverarbeitet WORTGLEICH feature_norm (Kanalfolge des
        Modells, (x-mean)/std, CHW, Batch 1 — so laeuft die Ernte). NormMass ist per
        Konstruktion auf adaface beschraenkt (Wache in __init__), die spec kommt
        deshalb aus MODELLE statt aus einem zweiten Literal."""
        spec = MODELLE["adaface"]
        aus = []
        for k in cls.NORM_KREUZ_SKALEN:
            img = gesichtsreiz(112, k).astype(np.float32)
            if not spec.get("bgr"):                    # gesichtsreiz liefert BGR
                img = img[:, :, ::-1]
            x = (img - spec["mean"]) / spec["std"]
            aus.append(np.ascontiguousarray(x.transpose(2, 0, 1)[None].astype(np.float32)))
        return aus

    @classmethod
    def _kreuzprobe(cls, sess_a, sess_b):
        """Groesste Norm-Abweichung zweier Sessions auf den gepinnten Gesichtsreizen.

        UMGESTELLT 24.08.2026 — vorher liefen hier zwei standard_normal-Rauschbilder.
        Der Grund steht bei gesichtsreiz(): Rauschen faellt dem adaface-Kopf auf Norm
        11,63/12,23, die Entscheidungen fallen bei 21,5..24,0. Die Probe hat also an
        einem Arbeitspunkt gemessen, an dem nichts entschieden wird, und dort den
        fp16-Fehler unterschaetzt (gemessen 24.08.: 0,099 im Rauschen gegen 0,149 auf
        dem Reiz, gegen bis 0,67 auf echten Crops). Drei Kontrast-Skalen statt einer,
        weil der Fehler mit dem Arbeitspunkt wandert (fp16 hier: 0,007 / 0,030 /
        0,149 ueber die Skalen 0,7 / 1,0 / 1,4).

        Signatur bewusst unveraendert (sess_a, sess_b) — tester/gputest_kommandos_*.md
        ruft diese Methode direkt auf, damit Tester-Zahlen vergleichbar bleiben."""
        inp = sess_a.get_inputs()[0].name
        namen = [o.name for o in sess_a.get_outputs()]
        idx = 1 - namen.index("embedding") if "embedding" in namen else 1
        inp_b = sess_b.get_inputs()[0].name
        abw = 0.0
        for x in cls._kreuz_eingaben():
            fa = np.asarray(sess_a.run(None, {inp: x})[idx], np.float32).reshape(1, -1)
            fb = np.asarray(sess_b.run(None, {inp_b: x})[idx], np.float32).reshape(1, -1)
            abw = max(abw, float(abs(np.linalg.norm(fa) - np.linalg.norm(fb))))
        return abw

    def _konsistenzprobe(self):
        """f/||f|| MUSS dem embedding-Ausgang entsprechen -> groesste Abweichung.
        Gepinnter Zufalls-Input (seed 7) wie die Messwerkbank des Prototyps."""
        x = np.random.default_rng(7).standard_normal((2, 3, 112, 112)).astype(np.float32)
        out = self._sess.run(None, {self._in: x})
        e = np.asarray(out[self._idx_emb], np.float64)
        f = np.asarray(out[self._idx_f], np.float64).reshape(len(x), -1)
        n = np.linalg.norm(f, axis=1, keepdims=True)
        return float(np.abs(f / n - e / np.linalg.norm(e, axis=1, keepdims=True)).max())

    def feature_norm(self, crops_bgr):
        """norm_crop-112-Crops (BGR) -> np.float32-Array der Feature-Normen ||f||.
        Preprocessing wortgleich Embedder._rec_infer (BGR, (x-mean)/std, CHW);
        EXAKTE Batchgroesse ohne Padding — auf CPU gibt es keine Shape-Kompilate,
        und eine Padding-Zeile darf nie als Messwert durchgehen."""
        if not self.ok:
            raise RuntimeError(f"NormMass disabled: {self.grund}")
        spec = self._spec
        batch = []
        for img in crops_bgr:
            x = img if spec.get("bgr") else cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            x = (x.astype(np.float32) - spec["mean"]) / spec["std"]
            batch.append(x.transpose(2, 0, 1))
        X = np.asarray(batch, np.float32)
        F = np.asarray(self._sess.run(None, {self._in: X})[self._idx_f],
                       np.float32).reshape(len(X), -1)
        return np.linalg.norm(F, axis=1)


# ---------------------------------------------------------------- Hilfen
class StrukturMass:
    """Gesichts-STRUKTUR statt Gesichts-QUALITAET: misst, ob ein Ausschnitt
    ueberhaupt ein Gesicht zeigt (Untersuchung 22.08.2026,
    analysen/06_ist_das_ein_gesicht.md).

    ABGRENZUNG ZU NormMass — die beiden beantworten VERSCHIEDENE Fragen:
    NormMass fragt "wie gut ist dieses Gesicht fuer die Erkennung" (Herkunft
    AdaFace, CVPR 2022: dort ein graduelles Trainings-GEWICHT, kein Schalter).
    StrukturMass fragt "ist da ein Gesicht". Die Norm kann das nicht: gemessen
    hat eine Hecken-Gruppe den HOEHEREN Norm-Spitzenwert (22,58) als eine echte
    Personengruppe (22,09) — core/ernte.py sagt es selbst, die Norm sei "als
    Gesicht/Nicht-Gesicht-Trenner nirgends kalibriert".

    VERFAHREN: das 106-Punkt-Landmark-Modell wird auf den GANZEN Ausschnitt
    gezwungen (bbox = ganzes Bild). Bei einem echten Gesicht verteilen sich die
    Punkte ueber Kinn, Augen und Mund; ohne Gesichtsstruktur kollabieren sie zur
    Bildmitte. Gemessen wird ihre mittlere Streuung, normiert auf die Bildkante.

    PREPROCESSING (QS-Auflage 22.08.: ohne diese Angabe ist die Schwelle nicht
    reproduzierbar): insightface Landmark.get() rechnet intern
    _scale = 192 / (max(w,h) * 1.5) — der PADDING-FAKTOR 1,5 ist im
    insightface-Code FEST verdrahtet und damit Teil der Skala. Ein anderer Faktor
    verschiebt alles: gemessen Median 0,143 (1,0) / 0,156 (1,5) / 0,170 (2,0).
    Deshalb wird IMMER ueber Landmark.get() gemessen, nie mit eigenem Zuschnitt.

    MODELLWAHL, gemessen: 2d106det (5 MB, 2D) schlaegt das ohnehin geladene
    1k3d68 (143 MB, 3D) deutlich — AUC 0,820 gegen 0,756 bei 30 ms gegen 219 ms.
    1k3d68 bleibt unangetastet, es liefert die POSE, die S-Gate, front_aus_pose,
    Live-Waechter und Blick-Sortierung ueberall brauchen.

    GERAETEWAHL: bewusst CPU, mit gekapptem Thread-Pool (2 intra-op). Anders als
    bei NormMass ist CPU keine Messbedingung, sondern Sparsamkeit — die
    Geraetedrift wurde gemessen und ist unkritisch (CPU/NPU max |d| 0,00028,
    CPU/GPU 0,00098, NULL Kipper an der Linie auf 132 Crops). Kosten gemessen:
    3,8 ms Wanduhr / 15,4 CPU-ms je Bild (ungekappt waeren es 11,0 / 125,8).

    BAUORT — WICHTIG, und hier gilt das GEGENTEIL der NormMass-Regel: diese
    Session wird LAZY neben einem schon warmen Prozess gebaut, NIE eager am
    Prozess-Start. Gemessen: neben einer warmen Session kostet sie 0 MB und
    0,2 s, in einem nackten Prozess dagegen +464 MB RSS. Der OOM-anfaellige
    Prozess ist der Main (alle vier Kills vom 15.08.).

    Faellt irgendetwas aus, setzt ok=False mit lautem Marker 'STRUKTURMASS' und
    streuung() liefert None — der Aufrufer filtert dann NICHT (ein Test ohne
    Messgrundlage darf nie still Material verlieren)."""

    # Benannte Quelle statt Streu-Literal (K3-Regel): das Modell liegt als Teil
    # des buffalo_l-Pakets in allen fuenf Images (docker/buffalo_l/2d106det.onnx
    # -> /root/.insightface/models/buffalo_l/, s. Dockerfile* COPY).
    MODELL_DATEI = "2d106det.onnx"
    MODELL_DIR = os.path.join(os.path.expanduser("~"), ".insightface",
                              "models", "buffalo_l")

    def __init__(self, device="CPU"):
        self.ok = False
        self.grund = ""
        self.device = str(device or "CPU").upper()
        self._m = None
        pfad = os.path.join(self.MODELL_DIR, self.MODELL_DATEI)
        if not os.path.exists(pfad):
            self.grund = f"model file missing: {pfad}"
            sys.stderr.write(f"[face_audit] STRUKTURMASS: {self.grund} -> disabled\n")
            return
        try:
            import onnxruntime as ort
            ort.set_default_logger_severity(3)
            from insightface.model_zoo import get_model
            # .505 (E3c, 05.09.2026, Widerleger W-E3 SCHWER 1): auch DIESER
            # Init laeuft in die Kappungs-Klammer, wie Embedder.__init__ seit
            # E3b. Bis hierher deckte die Klammer nur den Embedder, und die
            # Session hier blieb nackt — sie entsteht in JEDEM Worker
            # (worker.py) und beim Sammeln (anlernen.py); gemessen 8
            # pthread_setaffinity-Zeilen allein aus diesem Konstruktor, unter
            # taskset auf 3 Kernen. prepare() ist mitgeklammert, gleiche
            # Begruendung wie im Embedder (set_providers baut die native
            # Session neu; hier tote Zeile, in fremden Baeumen Versicherung).
            with _insightface_sessions_gekappt():
                self._m = get_model(pfad, providers=["CPUExecutionProvider"])
                self._m.prepare(ctx_id=-1)
            # THREAD-KAPPUNG (QS-Fund 22.08.): der Ersatz NACH dem Bau bleibt —
            # die Klammer oben gibt der insightface-Session die ALLGEMEINE
            # Ableitung (erlaubte Kerne), fuer dieses 5-MB-Modell ist aber 2 die
            # gemessen beste Stufe. Neu seit E3c ist nur, dass der zu grosse
            # Pool gar nicht mehr ENTSTEHT: vorher baute insightface hier eine
            # Session nach hardware_concurrency() des WIRTS, die eine
            # Affinitaets-Zeile je nicht erlaubtem Kern kostete und gleich
            # darauf verworfen wurde. Gemessen im Prod-Container, 15 Laeufe je
            # Stufe, Ergebnis bitgleich (max |dLandmark| 0,000000):
            #   default  11,0 ms Wanduhr / 125,8 CPU-ms
            #   1 Thread  5,1 ms /  13,1 CPU-ms
            #   2 Threads 3,8 ms /  15,4 CPU-ms   <- genommen
            #   4 Threads 5,6 ms /  25,1 CPU-ms
            # Das Modell ist mit 5 MB zu klein fuer breite Parallelitaet: mehr
            # Threads kosten mehr, als sie bringen. Zwei sind der Kompromiss aus
            # Wanduhr (der Ernter misst viele Bilder nacheinander) und CPU-Last
            # (Issue #21: 2C/4T-Maschinen). Ersatz NACH prepare(), nie die
            # Klasse patchen — Regression 0.1.0.13, s. _ort_thread_opts.
            _so = ort.SessionOptions()
            _so.intra_op_num_threads = 2
            _so.inter_op_num_threads = 1
            self._m.session = ort.InferenceSession(
                pfad, sess_options=_so, providers=["CPUExecutionProvider"])
        except Exception as ex:                                   # noqa: BLE001
            self.grund = f"load failed: {type(ex).__name__}: {str(ex)[:200]}"
            sys.stderr.write(f"[face_audit] STRUKTURMASS: {self.grund} -> disabled\n")
            self._m = None
            return
        self.ok = True
        sys.stderr.write("[face_audit] STRUKTURMASS: face structure on CPU "
                         "(2d106det, padding 1.5 fixed)\n")

    def streuung(self, crop_bgr):
        """-> float (Streuung der 106 Punkte / laengste Bildkante) oder None.

        None heisst IMMER 'nicht gemessen', nie 'kein Gesicht' — der Aufrufer
        darf darauf nicht filtern."""
        if not self.ok or crop_bgr is None or not getattr(crop_bgr, "size", 0):
            return None
        try:
            from insightface.app.common import Face
            h, w = crop_bgr.shape[:2]
            if w < 2 or h < 2:
                return None
            f = Face(bbox=np.array([0, 0, w, h], dtype=np.float32),
                     kps=None, det_score=1.0)
            self._m.get(crop_bgr, f)
            P = np.asarray(f.landmark_2d_106, dtype=np.float32)
            if P.ndim != 2 or len(P) < 3:
                return None
            return round(float(np.std(P, axis=0).mean() / max(w, h)), 4)
        except Exception:                                          # noqa: BLE001
            return None



def quality(img):
    h, w = img.shape[:2]
    return {"w": int(w), "h": int(h), "px": int(w*h),
            "sharp": round(float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()), 0)}

def cos(a, b): return float(np.dot(a, b))


def ist_fehldetektion(front, schaerfe, det, front_min=0.85, sharp_min=1500.0, det_max=0.70):
    """#42 Teil B: 'stehendes Objekt'-Signatur einer SCRFD-Fehldetektion (Radkasten/Hecke).

    Kalibriert an 407 von Hand gelabelten Detektionen (Kalibrier-Messreihe,
    24./25.07.): auf Objekten ohne echten Kopf liefert die Posenschaetzung Winkel nahe null
    ("perfekt frontal", Median 0.91 vs 0.31 bei echten Gesichtern), Vegetation/Speichen sind
    kantenreich (Schaerfe-Median 2145 vs 1170), und der det_score bleibt maessig (Median 0.55
    vs 0.75). ALLE DREI zusammen: faengt 86,1 % der Fehldetektionen bei 1,2 % Verlust echter
    Gesichter; die Schaerfe-Bedingung schuetzt den kritischen Fall fernes-glattes-Gesicht
    (Anmarsch: front 0.94, det 0.55, Schaerfe 462 -> bleibt). Bewusst KEIN allgemeiner
    Gesicht/Nicht-Gesicht-Klassifikator (Hund/Stoff/Laub-Einzelfaelle passieren) und NICHT
    im Urteilspfad (ours/win3s/bestaetigt) — nur Zaehlung, Anzeige, Unbekannt-Pool."""
    return front >= front_min and schaerfe >= sharp_min and det < det_max

def line(r):   # einheitliche Ref-Zeile fuer den Text-Report
    return f"{r['person']}/{r['fname']}  [{fdate(r['fname'])}]  {furl(r['person'], r['fname'])}"

# ---------------------------------------------------------------- Analyse
def run(limit=None, json_out=None, html_out=None):
    idx = fetch_index()
    print(f"Personen: {len(idx)} | Bilder: {sum(len(v) for v in idx.values())}\n")
    emb = Embedder()

    recs, undetected = [], []
    for person, files in idx.items():
        for fname in (files[:limit] if limit else files):
            try:
                img = fetch_image(person, fname)
                if img is None:
                    print(f"  ! nicht dekodierbar: {person}/{fname}"); continue
                q = quality(img); v = emb.embed(img)
                (recs if v is not None else undetected).append(
                    {"person": person, "fname": fname, "vec": v, "q": q})
            except Exception as e:
                print(f"  ! Fehler {person}/{fname}: {e}")
        ok = sum(1 for r in recs if r["person"] == person)
        nd = sum(1 for r in undetected if r["person"] == person)
        print(f"  {person:<12} ok:{ok}/{len(files)}" + (f"  KEIN Gesicht:{nd}" if nd else ""))

    people = sorted({r["person"] for r in recs})
    by = {p: [r for r in recs if r["person"] == p] for p in people}
    centroid = {p: (lambda c: c/(np.linalg.norm(c) or 1))(np.mean([r["vec"] for r in rs], 0))
                for p, rs in by.items()}
    for p, rs in by.items():
        s, n = np.sum([r["vec"] for r in rs], 0), len(rs)
        for r in rs:
            if n > 1:
                loo = (s - r["vec"]) / (n-1); r["sim_own"] = cos(r["vec"], loo/(np.linalg.norm(loo) or 1))
            else:
                r["sim_own"] = None
            oth = [(q, cos(r["vec"], centroid[q])) for q in people if q != p]
            r["nn_other"], r["sim_other"] = max(oth, key=lambda x: x[1]) if oth else (None, None)

    # ---- 0) kein Gesicht -----------------------------------------------
    print("\n" + "="*72 + f"\n0) KEIN GESICHT DETEKTIERBAR ({len(undetected)}) -- staerkste Loesch-Kandidaten\n" + "="*72)
    for r in sorted(undetected, key=lambda r: r["q"]["px"]):
        print("  " + line(r) + f"  ({r['q']['w']}x{r['q']['h']}px, sharp={r['q']['sharp']})")

    # ---- A) Kohaerenz ---------------------------------------------------
    print("\n" + "="*72 + "\nA) PERSONEN-KOHAERENZ (mittl. Aehnlichkeit der Bilder untereinander, 0..1)\n" + "="*72)
    def coh(p):
        ss = [r["sim_own"] for r in by[p] if r["sim_own"] is not None]
        return float(np.mean(ss)) if ss else float("nan")
    for p in sorted(people, key=coh):
        m = coh(p); n = len(by[p])
        hint = "zu wenige Bilder" if n < 5 else ("unheitlich -> pruefen" if m < 0.45 else ("leicht unheitlich" if m < 0.55 else "ok"))
        print(f"  {p:<12}{n:>4} Bilder   Kohaerenz {m:.3f}   {hint}")

    # ---- B) Fehllabel ---------------------------------------------------
    print("\n" + "="*72 + "\nB) VERDACHT FEHLLABEL / SCHAEDLICH (fremd >= eigen, oder eigen sehr niedrig)\n" + "="*72)
    flagged = []
    for r in recs:
        if r["sim_own"] is None: continue
        oth = r["sim_other"] if r["sim_other"] is not None else -1
        if oth >= r["sim_own"] - 0.03 or r["sim_own"] < 0.30:
            flagged.append((oth - r["sim_own"], r))
    flagged.sort(key=lambda x: -x[0])
    if not flagged: print("  keine.")
    for sev, r in flagged[:25]:
        tag = "FREMD naeher" if r["sim_other"] is not None and r["sim_other"] >= r["sim_own"] else "schwach"
        print(f"  [{tag:<12}] eigen={r['sim_own']:.2f} naechste_fremd={r['nn_other']}={r['sim_other']:.2f}")
        print("       " + line(r) + f"  ({r['q']['w']}x{r['q']['h']}px)")

    # ---- C) Verwechslung ------------------------------------------------
    print("\n" + "="*72 + "\nC) VERWECHSLUNGS-MATRIX (Zentroid-Aehnlichkeit, Top-Paare)\n" + "="*72)
    pairs = sorted(((cos(centroid[a], centroid[b]), a, b)
                    for i, a in enumerate(people) for b in people[i+1:]), reverse=True)
    for sim, a, b in pairs[:10]:
        print(f"  {sim:.3f}  {a} <-> {b}" + ("   <- verwechselbar" if sim > 0.45 else ""))

    # ---- D) Qualitaet ---------------------------------------------------
    print("\n" + "="*72 + "\nD) QUALITAETS-FLAGS\n" + "="*72)
    for r in sorted([r for r in recs if r["q"]["px"] < 2500], key=lambda r: r["q"]["px"])[:10]:
        print("  klein   " + line(r) + f"  {r['q']['w']}x{r['q']['h']}px")
    for r in sorted(recs, key=lambda r: r["q"]["sharp"])[:8]:
        print(f"  unscharf sharp={r['q']['sharp']:<6} " + line(r))

    # ---- HTML-Galerie ---------------------------------------------------
    if html_out:
        cards = []
        def card(r, badge):
            return (f'<figure><img src="{furl(r["person"], r["fname"])}" loading="lazy">'
                    f'<figcaption><b>{html.escape(r["person"])}</b> <span class=b>{badge}</span><br>'
                    f'{fdate(r["fname"])} · {r["q"]["w"]}x{r["q"]["h"]}px</figcaption></figure>')
        for r in sorted(undetected, key=lambda r: r["q"]["px"]):
            cards.append(card(r, "kein Gesicht"))
        for sev, r in flagged[:40]:
            cards.append(card(r, f'{r["nn_other"]} {r["sim_other"]:.2f} &gt; eigen {r["sim_own"]:.2f}'))
        doc = ("<!doctype html><meta charset=utf-8><title>Face-Audit</title>"
               "<style>body{font:14px system-ui;background:#111;color:#eee;margin:1.5rem}"
               "h1{font-size:1.2rem}.grid{display:flex;flex-wrap:wrap;gap:14px}"
               "figure{margin:0;background:#1c1c1c;border:1px solid #333;border-radius:8px;padding:8px;width:150px}"
               "img{width:134px;height:auto;image-rendering:auto;border-radius:4px;background:#000}"
               "figcaption{font-size:12px;margin-top:6px;line-height:1.35}.b{color:#f77;font-size:11px}</style>"
               f"<h1>Frigate Face-Audit &mdash; {len(undetected)} ohne Gesicht, {len(flagged)} Fehllabel-Verdacht</h1>"
               "<div class=grid>" + "".join(cards) + "</div>")
        with open(html_out, "w") as f: f.write(doc)
        print(f"\nHTML-Galerie: {html_out}")

    if json_out:
        with open(json_out, "w") as f:
            json.dump({"undetected": [{"person": r["person"], "fname": r["fname"], **r["q"]} for r in undetected],
                       "flagged": [{"person": r["person"], "fname": r["fname"], "sim_own": r["sim_own"],
                                    "nn_other": r["nn_other"], "sim_other": r["sim_other"], "url": furl(r["person"], r["fname"])}
                                   for _, r in flagged],
                       "confusion": [[a, b, s] for s, a, b in pairs]}, f, ensure_ascii=False, indent=2)
        print(f"JSON: {json_out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--html", default=None)
    a = ap.parse_args()
    run(limit=a.limit, json_out=a.json, html_out=a.html)
