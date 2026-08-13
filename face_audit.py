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
import glob as _glob
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
def _ort_thread_opts():
    """SessionOptions mit EXPLIZIT gesetzter Intra-Op-Thread-Zahl.

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
    if _ORT_THREADS is None:
        env = os.environ.get("SUSLIK_CPU_THREADS", "")
        if env.isdigit() and int(env) > 0:
            _ORT_THREADS = int(env)          # N9: cpu_threads-Config (Service setzt ENV, Worker erbt)
        else:
            try:
                _ORT_THREADS = max(1, len(os.sched_getaffinity(0)))   # erlaubte Kerne (cgroup/LXC-Maske)
            except AttributeError:                                     # sched_getaffinity nur auf Linux
                _ORT_THREADS = max(1, os.cpu_count() or 1)
    so = ort.SessionOptions()
    so.intra_op_num_threads = _ORT_THREADS
    # inter_op mitsetzen (#21): im Default-Modus ORT_SEQUENTIAL baut ORT zwar keinen
    # Inter-Op-Pool, aber der Default-WERT waere wieder hardware_concurrency — sollte je
    # eine Session in den Parallel-Modus geraten, gilt derselbe Deckel statt der Host-Kernzahl.
    so.inter_op_num_threads = _ORT_THREADS
    return so


def geraete_knoten_muster(dev):
    """Task #15: Pflicht-Geraeteknoten je OpenVINO-Device (None = keine Vorbedingung).
    Basis-Lookup ueber split('.'): GPU.0/GPU.1/NPU.0 (unsere eigene Mehr-GPU-Hilfe
    empfiehlt genau diese Formen) werden wie GPU/NPU behandelt (Widerleger-Fund .66).
    MIXED erreicht _ort_session nie als dev (Aufrufer verteilen auf GPU+NPU); AUTO
    kann bei DIREKTEM CLI-Lauf ankommen — das Mapping liefert dann None und das
    Verhalten bleibt wie vor Task #15 (verifyd loest AUTO vorher auf)."""
    # P3.1: Zuordnung lebt in core.registry (KNOTEN_BASIS) — Signatur und
    # Basislookup-Verhalten (GPU.1 -> GPU, unbekannt -> None) unveraendert.
    from core.registry import knoten_von
    return knoten_von(dev)


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
    with urllib.request.urlopen(f"{FRIGATE}/api/faces", timeout=20) as r:
        d = json.load(r)
    return {k: v for k, v in d.items() if k != "train"}

def furl(person, fname):
    return f"{FRIGATE}/clips/faces/{urllib.parse.quote(person)}/{urllib.parse.quote(fname)}"

def fdate(fname):
    m = re.search(r"(\d{10})", fname)          # Unix-Sekunden im Dateinamen
    if not m: return "?"
    return datetime.datetime.fromtimestamp(int(m.group(1))).strftime("%d.%m.%y %H:%M")

def fetch_image(person, fname):
    with urllib.request.urlopen(furl(person, fname), timeout=20) as r:
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
    def __init__(self, device=None, modell=None):
        import onnxruntime as ort
        ort.set_default_logger_severity(3)
        from insightface.app import FaceAnalysis
        self.app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
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

    def _get_mit_rec(self, img, max_num=0):
        """Kapsel um insightface app.get: Faces detektieren/ausrichten wie gehabt, dann
        face.embedding je Gesicht mit dem eigenen Recognition-Modell ueberschreiben."""
        from insightface.utils import face_align
        faces = self._orig_get(img, max_num=max_num)
        if faces:
            crops = [face_align.norm_crop(img, landmark=f.kps, image_size=112) for f in faces]
            E = self._rec_infer(crops)
            for f, e in zip(faces, E):
                f.embedding = e
        return faces

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
        Weiterhin gilt: NIE app.prepare() direkt aufrufen, immer diese Methode."""
        self.app.prepare(ctx_id=0, det_size=det_size)
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

# ---------------------------------------------------------------- Hilfen
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
