#!/usr/bin/env python3
"""ENGINE onnxruntime/MIGraphX (AMD ROCm) — die dritte Backend-Haelfte des Workers (E6).

HERKUNFT UND ZWECK. Bis 0.1.0.537 kannte `worker_dienst.engine_bauen` nur `ov` und
`cuda`; `backend: migraphx` (Werksvorgabe des rocm-Images) lief in ein
`SystemExit("Backend 'migraphx' hat noch keine Engine")`. Diese Datei schliesst die
Luecke. Zielsystem ist der einzige Feldtester (Discussion #29): Radeon 760M/gfx1103
(RDNA3, iGPU, 16-GB-BIOS-Carve-out), ROCm 7.2.4, onnxruntime-migraphx 1.27.1,
Frigate auf DERSELBEN iGPU.

WIR HABEN KEINE AMD-HARDWARE. Nichts in dieser Datei ist auf einer AMD-Karte
gemessen. Sein Log ist unser Messgeraet — deshalb ist das LAUTE Bind-Protokoll
(s. `_sitzung`) Teil der Funktion und keine Kosmetik: es beantwortet im Feld genau
die Fragen, die wir hier nicht beantworten koennen.

WELCHE IMAGE-VARIANTE DIESE ENGINE FAEHRT, vollstaendig benannt (Deckungs-Regel):
**rocm** und nur rocm. Die uebrigen vier Varianten kommen hier nie als Engine an —
**gpu** und **gpu-legacy** fahren `engine_ov`, **cuda** faehrt `engine_cuda`, und
**cpu** faehrt seit E4 (17.09.2026) `engine_cpu`. Die Datei liegt trotzdem in
jedem Image: `worker_dienst` importiert die Engines FAUL, und ein vergessenes COPY
faengt die Gate-Stufe „alle Runtime-Module vorhanden" nur, wenn die Datei ueberall
erwartet wird.

E4 BENUTZT DIESE DATEI MIT (17.09.2026), und das ist kein Nebeneffekt, sondern der
Schnitt: `engine_cpu` importiert `ModellBestand`, `Stufen`, `Satz`, `Geometrie` und
`BildStufen` von hier und tauscht allein den SESSION-BAUER (`ModellBestand(sitzung=…)`)
und die Decode-Kette. Der Grund steht unten unter „DER SCHNITT": alles in dieser Datei
ausser dem Session-Bau ist geraetefrei — der Zuschnitt liegt auf der CPU, die
Nachrechnungen liegen in numpy, die Stufenformen kommen aus den Modell-Dateien. Der
CPU-Weg dieser Engine (jede Stufe auf `CPUExecutionProvider`, s. `_sitzung` Stufe 3)
IST der Rechenweg, den `engine_cpu` fuehrt; er ist hier seit dem 17.09. lokal belegt
(Roundtrip im rocm-Image ohne /dev/kfd reproduziert den Intel-Fixpunkt exakt).

────────────────────────────────────────────────────────────────────────────────
DER SCHNITT, UND WARUM ER ANDERS IST ALS BEI ov/cuda
────────────────────────────────────────────────────────────────────────────────
`engine_ov` und `engine_cuda` schneiden die Gesichter auf dem Beschleuniger aus dem
RGB-Vollbild (EIN GridSample je Stufe) und halten alles zwischen den Stufen im
Geraetespeicher. **Dieser Weg ist auf dem ORT-MIGraphX-EP verbaut**, und zwar nicht
aus Tempo-, sondern aus Deckungsgruenden:

  Der EP hat eine eigene, fest eingebaute Op-Allowlist
  (`migraphx_execution_provider.cc:865-1024`, `static std::set<std::string>
  mgx_supported_ops`). **„GridSample" kommt dort 0-mal vor** — geprueft gegen v1.27.1
  UND gegen `main` (beide Fassungen byte-gleich; letzte Aenderung der Datei
  2026-03-09, Commit 7253fdc8). MIGraphX SELBST kann GridSample seit 2.11/ROCm 6.3
  vollstaendig in unserer Auspraegung (`src/onnx/parse_gridsample.cpp`, bilinear /
  zeros / align_corners=0 / 4-D), aber der EP reicht den Knoten nie an MIGraphX
  weiter. Es gibt heute KEINE ORT-Fassung, in der das anders waere; eine
  Versions-Erhoehung loest es nicht.

  Was daraus folgte, wenn man die Graphen 1:1 uebernaehme: `GetCapability`
  (`:1077-1136`) schneidet an den nicht unterstuetzten Knoten, danach wirft
  `SubgraphPostProcessing` (`:592-660`) jedes Cluster weg, das kein RNN/GRU/LSTM und
  keinen {AveragePool,Conv,Gemm,LRN,MatMul,MaxPool}-Knoten mit ALLEN Eingaengen
  <= 300 Elementen enthaelt. Unser Ausschnitt-Graph zerfiele in ein Vorher (MatMul auf
  12544 Abtastpunkten) und ein Nachher (u8-Rundung + Normierung) — beide fielen
  heraus, also liefe der ganze Ausschnitt auf der CPU, mit Geraetewechsel davor und
  danach. Mit `disable_cpu_ep_fallback` scheiterte statt dessen der Session-Bau.

**Der Zuschnitt dieser Engine ist deshalb der BILD-WEG, angewandt auf Video-Frames**
(Zuschnitt des Inhabers 17.09., Punkte 2 und 4):

    NV12 aus ffmpeg  ->  worker_kern.nv12_bgr        [DIE eine Konvertierung, CPU]
      -> Detektor-Leinwand  bild_kern.det_leinwand   [cv2.resize, CPU]
      -> det_10g                                     [GPU, MIGraphX-EP]
      -> je Gesicht cv2.warpAffine aus DEMSELBEN Frame  [CPU, Bild-Weg-Muster]
      -> bild_kern.norm_anwenden                     [CPU, dieselbe Vorschrift]
      -> fd / e / t / p / r                          [GPU, MIGraphX-EP]
      -> Laplace-Schaerfe                            [CPU, cv2]
      -> Score-Matmul, Winkel, Zusammenfassung       [CPU, worker_kern]

KEIN GridSample-Graph verlaesst diese Datei Richtung EP. Die Zuschnitt-Bytes sind
damit die des BESTANDS (cv2.warpAffine auf dem uint8-Frame — genau die Bytes, an
denen alle Referenzen dieses Hauses gemessen sind), nicht die der GPU-Warps. Diese
Engine ist deshalb NICHT bitgleich zu ov/cuda; sie ist naeher am alten Weg als beide.

WAS DIESER SCHNITT KOSTET, ehrlich: pro Frame eine YUV->BGR-Konvertierung und je
Gesicht fuenf warpAffine auf der CPU statt eines GPU-Durchlaufs. Wie viel das auf der
760M ist, weiss nur der Feldlauf. Die Alternative waere kein schnellerer Weg gewesen,
sondern gar keiner.

────────────────────────────────────────────────────────────────────────────────
DECODE
────────────────────────────────────────────────────────────────────────────────
**HW-Decode (VAAPI) ist DEFAULT** — wie auf Intel und CUDA (Entscheid des
Inhabers 17.09.2026). Die Kette ist die von `engine_ov._ffmpeg_nv12`, der Byte-Weg dahinter
`worker_kern.nv12_strom`, der laute Software-Rueckfall `worker_kern.nv12_mit_rueckfall`
(`wache['hwdec_fallback']`, eine Zeile je Ereignis im Dienst).

EHRLICHER STATUS: **Byte-Gleichheit HW = SW ist auf AMD UNGEMESSEN.** Der Beweis vom
04.08.2026 (md5 ueber rawvideo, h264-4K/hevc-4K/hevc-1080p bitgleich) ist auf INTEL
gefuehrt. Fuer die 760M ist bei uns nur der ENCODER belegt (`core/registry.py:147`,
AMD-Tester 780M 2026-07-30) — Encode sagt nichts ueber Decode. Der Default ist damit
ein bewusst getragenes Risiko (Inhaber: „Prinzip Wahrscheinlichkeit"; Rueckkanal sind
Feldtester-Meldungen zur Erkennungsqualitaet). **Nachmessweg:
`docker exec <container> python verifyd.py --benchmark`** — der Abschnitt
„decode byte probe" dort faehrt HW gegen SW ueber `decode.byte_probe` und druckt je
Clip ein Verdikt. Er ist Nachmess-Werkzeug, keine Freischalt-Bedingung; es gibt
bewusst KEINEN automatischen Selbsttest im Dienstbetrieb.

────────────────────────────────────────────────────────────────────────────────
WAS BEWUSST NICHT DRIN IST (Erstwurf)
────────────────────────────────────────────────────────────────────────────────
* **fp16.** Alle Stufen laufen auf den fp32-Dateien des Hauses (`wk.vorgabe_pfade`).
  Der EP-Schalter `ORT_MIGRAPHX_FP16_ENABLE` / `migraphx_fp16_enable` ist
  ausdruecklich NICHT gesetzt: er fuehrt zu `migraphx::quantize_fp16(prog)` mit der
  Vorgabe-Op-Liste `{"all"}` (`quantization.hpp:41-42`) und kappt damit den GANZEN
  Fused-Subgraphen — auch Rechnungen mit f32-Pflicht. Der belastbare Weg waere wie
  auf CUDA das Vorab-Backen je Modell (`tools/fp16_backen.py`); das ist eine eigene
  Etappe mit eigener Abnahme.
* **Kompilat-/Werte-Probe (`Satz.probe`).** Gibt es nur in `engine_ov`; der Dienst
  meldet das Fehlen LAUT und setzt die Kurzform `startprobe` als Ersatz
  (`worker_dienst.engine_bauen`). Hier unveraendert wie auf CUDA.
* **Arena-Deckel.** `migraphx_mem_limit` und `migraphx_arena_extend_strategy` sind in
  v1.27.1 WIRKUNGSLOS: `mem_limit_`/`arena_extend_strategy_` werden im EP-Konstruktor
  nicht aus `info` gesetzt (`migraphx_execution_provider.h:129-130`, `.cc:233-234`),
  `CreatePreferredAllocators` benutzt `AllocatorCreationInfo(factory, id)` mit
  `use_arena=true` und `arena_cfg = {0,-1,-1,-1,-1,-1}`, also ohne Deckel
  (`allocator_utils.h:17-35`). Es gibt auf diesem EP keine Entsprechung zum
  .531-Kartenhaushalt. Deshalb plant `core/gpubudget` fuer migraphx konservativ EINEN
  Rechenstrang, und die Speicherlage wird ueber sysfs BEOBACHTET statt gedeckelt
  (`speicher_bericht`).
"""
import glob
import os
import threading
import time

import numpy as np

import worker_kern as wk                                 # noqa: E402  Bootstrap + Wert-Weg

import cv2                                               # noqa: E402  (vom Kern schon geladen)
import onnx                                              # noqa: E402
import onnxruntime as ort                                # noqa: E402

import bild_kern                                         # noqa: E402  Leinwand + Normierung
import face_audit                                        # noqa: E402  Thread-Kappung
# DIE ONNX-GRAPH-HELFER KOMMEN AUS engine_cuda, und das ist Absicht (bewusste Naht):
# `_fest` (feste Eingangsform + die f_norm-Naht), `_batch_frei`, `_div_naht` und die
# Typ-Leser sind reine onnx-Arbeit OHNE eine Zeile CUDA. Sie hier ein zweites Mal
# hinzuschreiben waere die zweite Quelle, die dieses Haus verbietet — dann liefen die
# f_norm-Naht der Erkennungs-Stufe und die Reshape-Umstellung von fiqa auf zwei
# Backends auseinander. `engine_cuda` laedt beim Import nichts CUDA-Spezifisches
# (Konstanten, `onnx`, `onnxruntime`, `face_audit`); die erste CUDA-Beruehrung steht
# in `_sitzung`/`Engine.__init__`, und beide ruft diese Datei nie. Das rocm-Image
# liefert `engine_cuda.py` ohnehin aus (Dockerfile.rocm, R1-Umzug).
import engine_cuda as ec                                 # noqa: E402

EP = "MIGraphXExecutionProvider"
# Der Geraetename fuer die ORT-PYTHON-Schicht — „gpu", NICHT „cuda".
# GEMESSENE FALLE aus dem Quelltext von 1.27.1 (`onnxruntime_inference_collection.py:56-64`):
# `get_vendor_id_for_device_type("cuda")` liefert NVIDIA. `OrtDevice.make(name, id,
# vendor_id=-1)` benutzt diesen Alias, und `OrtValue.ortvalue_from_numpy` /
# `io_binding.bind_output(name, "cuda")` gehen darueber. Auf einem
# onnxruntime-migraphx-Wheel ergibt das ein OrtDevice GPU/NVIDIA und passt nicht zum
# EP-Geraet (GPU/AMD, `migraphx_allocator.h:14-20`). Der Name „gpu" hat KEINEN Alias
# und faellt auf den 3-Argument-Konstruktor von `C.OrtDevice` zurueck, der den
# Hersteller aus der BUILD-Konfiguration fuellt: `#elif USE_MIGRAPHX -> AMD`
# (`onnxruntime_pybind_state.cc:2008-2029`). Genau deshalb steht hier "gpu".
GERAET_NAME = "gpu"
GERAET_ID = 0
KFD = "/dev/kfd"
# Die Breite JEDES Stufen-Aufrufs im Video-Weg. Dieselbe Zahl wie bei engine_ov
# (`wk.AUFRUF_BREITE`), aus demselben Grund: jede zusaetzliche Form kostet auf diesem
# EP eine VOLLE Neukompilierung (`migraphx_execution_provider.cc:1481-1526`, „Input
# shape mismatch detected. Recompiling"), und der Feldtester hat am 10.09. 63 s fuer
# EIN kleines Modell gemessen. Kuerzere Aufrufe werden gepolstert, das Doppel
# verworfen — Zeile fuer Zeile das Muster von `engine_ov.Satz.stufe`.
BREITE_VIDEO = wk.AUFRUF_BREITE or 1
# Der Bild-Weg rechnet Batch 1 (Norm-Messbasis, s. bild_kern-Kopf).
BREITE_BILD = 1
# Vorgabe fuer den .mxr-Modell-Cache, wenn das Image/der Betreiber nichts gesetzt hat.
# Der Cache ist im EP per Vorgabe AUS („empty cache path means the MXR caching is
# disabled - always compile", `migraphx_execution_provider.cc:1321`); ohne ihn kostet
# JEDER Prozessstart die volle Kompilierung aller Stufen und Breiten.
# Gesetzt wird er im Dockerfile (ENV ORT_MIGRAPHX_MODEL_CACHE_PATH); hier steht nur
# der Rueckfall fuer Laeufe ausserhalb des Images.
MODELL_CACHE_VORGABE = "/data/model_cache"
# sysfs-Griffe der AMD-Speicherlage. Kein HIP-Kontext: `hipMemGetInfo` waere per
# ctypes erreichbar (ORT exportiert es nicht), braucht aber `hipSetDevice` und zoege
# die HIP-Laufzeit in den Worker-Prozess — genau die Sorte Nebenwirkung, die am
# 11.08. auf der Intel-iGPU die Live-Waechter erschlagen hat
# (`core/personmodell.py:62-64`). Auf einer iGPU mit BIOS-Carve-out beschreibt
# „total" ohnehin nur den Carve-out; die interessante Unterscheidung VRAM gegen GTT
# steht nur in sysfs.
SYSFS_FELDER = (("vram_used", "mem_info_vram_used"), ("vram_total", "mem_info_vram_total"),
                ("gtt_used", "mem_info_gtt_used"), ("gtt_total", "mem_info_gtt_total"))


def _melden(text):
    """Eine Zeile ins Prozess-Log (fd 2) — dorthin, wo auch der Dienst seine
    Aufbau-Zeilen schreibt. Kein Import von `worker_dienst`: der importiert diese
    Datei, und ein Ringimport waere hier ein Startfehler statt einer Logzeile
    (wortgleiche Begruendung wie `engine_cuda._melden`)."""
    try:
        os.write(2, (f"engine_migraphx: {str(text).strip()}\n").encode())
    except Exception:                                    # noqa: BLE001
        pass


# ------------------------------------------------------------------ GPU-Speicher (sysfs)
class SysfsSpeicher:
    """Die AMD-Speicherlage aus sysfs — beobachtend, nicht deckelnd.

    `/sys/class/drm/card*/device/mem_info_{vram,gtt}_{used,total}`. Die Karte wird
    EINMAL gesucht (die erste, die alle vier Dateien traegt) und danach nur noch
    gelesen. Ist nichts lesbar, sagt das GENAU EINE laute Zeile und danach ist
    Ruhe — eine Zeile je Ereignis ueber eine Datei, die es nicht gibt, waere
    Rauschen ueber dem Log, in dem eine Ferndiagnose die echten Zeilen sucht."""

    def __init__(self):
        self.pfad = None
        self.grund = None
        self._gemeldet = False
        self._schloss = threading.Lock()
        self._suchen()

    def _suchen(self):
        try:
            for d in sorted(glob.glob("/sys/class/drm/card*/device")):
                if all(os.path.exists(os.path.join(d, n)) for _k, n in SYSFS_FELDER):
                    self.pfad = d
                    return
            self.grund = ("no /sys/class/drm/card*/device with mem_info_vram_* "
                          "(no amdgpu card visible in this container?)")
        except OSError as e:
            self.grund = f"{type(e).__name__}: {e}"

    def stand(self):
        """-> dict in MB oder None. Nie eine Ausnahme: eine Diagnose darf den Lauf
        nicht anhalten."""
        if self.pfad is None:
            return None
        aus = {}
        try:
            for k, name in SYSFS_FELDER:
                with open(os.path.join(self.pfad, name), encoding="ascii") as f:
                    aus[k] = int(f.read().strip()) // (1024 * 1024)
        except (OSError, ValueError) as e:
            with self._schloss:
                if not self._gemeldet:
                    self._gemeldet = True
                    _melden(f"gpu memory: {self.pfad} not readable "
                            f"({type(e).__name__}: {e}) — no further memory lines")
            self.pfad = None
            return None
        aus["karte"] = os.path.basename(os.path.dirname(self.pfad))
        return aus

    def zeile(self, wobei=""):
        """Die kompakte Log-Form. -> str oder "" (dann gibt es nichts zu melden)."""
        st = self.stand()
        if not st:
            return ""
        return (f"gpu memory{(' ' + wobei) if wobei else ''}: "
                f"vram {st['vram_used']}/{st['vram_total']} MB, "
                f"gtt {st['gtt_used']}/{st['gtt_total']} MB ({st['karte']})")

    def melden(self, wobei=""):
        z = self.zeile(wobei)
        if z:
            _melden(z)
        elif not self._gemeldet:
            self._gemeldet = True
            _melden(f"gpu memory: not readable ({self.grund or 'unknown'}) — "
                    f"no further memory lines")


SPEICHER = SysfsSpeicher()


# ------------------------------------------------------------------ Decode
def _ffmpeg_nv12(clip, schritt, hw):
    """Die ffmpeg-Kette dieser Engine, EINMAL fuer beide Wege — wortgleich zu
    `engine_ov._ffmpeg_nv12` (VAAPI ist herstellerneutral: mesa/radeonsi bedient
    dieselbe Schnittstelle wie Intels iHD). Auswahl per ffmpeg-select VOR dem
    Download wie `decode.FrameIter` (decode.py:159-177), NV12 statt yuv420p und ohne
    cv2-Umrechnung. `hw=False` ist dieselbe Kette OHNE VAAPI und ohne hwdownload —
    der Software-Rueckfall; sie endet auf demselben `format=nv12`.

    WARUM HIER EINE DRITTE KOPIE UND KEIN IMPORT AUS engine_ov: `engine_ov` importiert
    beim Laden das eigenstaendige `openvino`-Paket, und das gibt es im rocm-Image
    nicht. Der BYTE-Weg (Leser-Thread, Vorlauf, Pipe-Kapazitaet, Rueckfall-Regel) ist
    trotzdem nur EINMAL im Haus: `worker_kern.nv12_strom` / `nv12_mit_rueckfall`."""
    # .536 B1a: `-nostdin` — ffmpeg darf den fd 0 seines Elternprozesses nicht pollen.
    # Im Worker ist das die Job-Pipe (Byte-Beweis in worker_kern.nv12_strom).
    basis = ["ffmpeg", "-nostdin", "-v", "warning"]
    if hw:
        dev = os.environ.get("SUSLIK_HWDEC_DEVICE", "/dev/dri/renderD128")  # decode.py:168
        basis += ["-hwaccel", "vaapi", "-hwaccel_device", dev,
                  "-hwaccel_output_format", "vaapi"]
    rest = "hwdownload,format=nv12" if hw else "format=nv12"
    return basis + ["-i", clip, "-map", "0:v:0",
                    "-vf", f"select='not(mod(n\\,{schritt}))',{rest}",
                    "-fps_mode", "passthrough", "-f", "rawvideo", "-"]


def frames_nv12(clip, W, H, schritt, wache=None):
    """Sample-Frames als (i, y, uv) ueber VAAPI, MIT LAUTEM SOFTWARE-RUECKFALL.
    Regel und Begruendung stehen EINMAL in `worker_kern.nv12_mit_rueckfall`.

    UNGEMESSEN AUF AMD (s. Modulkopf): dass die VAAPI-Kette auf gfx1103 dieselben
    NV12-Bytes liefert wie die Software-Kette, ist ein Plausibilitaets-Schluss aus der
    Norm (H.264/HEVC-Decode ist normativ festgelegt), KEINE Messung. Nachgemessen
    wird per `verifyd.py --benchmark`, Abschnitt „decode byte probe"."""
    return wk.nv12_mit_rueckfall(_ffmpeg_nv12(clip, schritt, True),
                                 _ffmpeg_nv12(clip, schritt, False),
                                 W, H, schritt, "VAAPI", wache=wache)


# ------------------------------------------------------------------ Sessions
def _kfd_da():
    return bool(glob.glob(KFD))


def _provider_optionen():
    """Die MIGraphX-Provider-Optionen JEDER Session, an einer Stelle.

    Der Modell-Cache ist der einzige Knopf, der hier etwas bewirkt. NICHT gesetzt
    werden `migraphx_mem_limit`/`migraphx_arena_extend_strategy` (in 1.27.1
    wirkungslos, s. Modulkopf) und `migraphx_fp16_enable` (kappt programmweit,
    s. Modulkopf). Neues dict je Aufruf: was ORT damit macht, ist nicht zugesagt.

    ACHTUNG, Vorrang: die Env-Variable `ORT_MIGRAPHX_MODEL_CACHE_PATH` wird im
    EP-Konstruktor NACH der Uebernahme aus `info` gelesen und ueberschreibt die
    Provider-Option (`migraphx_execution_provider.cc:178`, `GET_ENV_STRING`). Wir
    setzen deshalb die Env-Variable, wenn sie leer ist, und reichen denselben Wert
    zusaetzlich als Option herein — beide zeigen dann auf dasselbe Verzeichnis und
    koennen nicht auseinanderlaufen."""
    return {"device_id": GERAET_ID,
            "migraphx_model_cache_dir": os.environ.get(
                "ORT_MIGRAPHX_MODEL_CACHE_PATH", "")}


def modell_cache_vorbereiten():
    """Den .mxr-Cache scharf machen, wenn nichts gesetzt ist. -> (pfad, quelle)

    „Nur dann als Default nachlegen, wenn nichts gesetzt ist" (Zuschnitt des
    Inhabers, Punkt 8): ein Betreiber, der die Variable selbst gesetzt hat, behaelt seine Wahl.

    DER CACHE-SCHLUESSEL TRAEGT EIN RISIKO, das die Bauart dieser Engine aber
    vermeidet: der Dateiname ist `hex(Version)-GenerateGraphId(graph)-hash(gcnArch)-
    hash(input_shapes).mxr` (`:1308`, `:1330`), und `GenerateGraphId`
    (`migraphx_execution_provider_utils.h:251-326`) hasht den Modell-Dateinamen, die
    Namen der Graph-Eingaenge und je Knoten die NAMEN der Ein-/Ausgaenge plus die
    Eingangs-SHAPES — **nicht OpType, nicht Attribute, nicht Initializer-Werte**.
    Zwei selbst gebaute Graphen mit generischen Tensornamen (`t1`, `c1`, … wie in
    `engine_cuda._Bau`) und gleicher Form haetten damit DIESELBE Cache-Datei bei
    VERSCHIEDENEN Konstanten — ein Treffer lieferte still ein Kompilat mit falschen
    Normierungs-Werten. Genau deshalb geht ueber diesen EP **ausschliesslich eine
    echte Modell-DATEI mit ihren eigenen Tensornamen**; die beiden Zahlen-Nachgraphen
    (Erkennungs-Norm, Kopf-Score) rechnet diese Engine in numpy auf der CPU
    (`_rec_post`, `_kopf_post`)."""
    da = (os.environ.get("ORT_MIGRAPHX_MODEL_CACHE_PATH") or "").strip()
    if da:
        quelle = "environment"
        pfad = da
    else:
        quelle = "default"
        pfad = MODELL_CACHE_VORGABE
        os.environ["ORT_MIGRAPHX_MODEL_CACHE_PATH"] = pfad
    try:
        os.makedirs(pfad, exist_ok=True)
    except OSError as e:
        _melden(f"WARN: model cache {pfad!r} not writable ({type(e).__name__}: {e}) "
                f"— every process start will recompile every stage (measured 63 s "
                f"for one small model on the field tester's card)")
        return pfad, f"{quelle} (not writable)"
    return pfad, quelle


def _so(vollstaendig):
    """Session-Optionen. `vollstaendig=True` verlangt, dass JEDER Knoten auf dem
    EP landet — `session.disable_cpu_ep_fallback` laesst den Bau abbrechen, sobald
    auch nur ein Knoten auf der Standard-CPU-EP liegt
    (`inference_session.cc:2653-2680`)."""
    o = face_audit._ort_thread_opts()         # feste Threadzahl, wie in beiden Engines
    if vollstaendig:
        o.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    return o


def _sitzung(modell_bytes, marke):
    """EINE Session, MIT LAUTEM DREISTUFIGEN BIND-PROTOKOLL. -> (session, bericht)

    WARUM DREI STUFEN UND NICHT ZWEI. Auf diesem EP ist „gebunden" nicht dasselbe wie
    „rechnet auf der GPU": `get_providers()` sagt nur, dass der EP ueberhaupt dabei
    ist. Ob ALLE Knoten bei ihm gelandet sind, sagt ORT von sich aus nur als EINE
    unspezifische Warnung (`session_state.cc:1367`, „Some nodes were not assigned to
    the preferred execution providers…") — welche Knoten, steht nicht drin; die Liste
    gaebe es erst mit `ORT_MIGRAPHX_DUMP_MODEL_OPS=1` und Log-Stufe INFO. Weil wir
    keine AMD-Karte haben, ist genau diese Unterscheidung die wertvollste Zeile im
    Feld-Log. Also wird sie ERZWUNGEN:

      1. Bau MIT `disable_cpu_ep_fallback` -> gelingt er, liegt der GANZE Graph auf
         dem EP.   Log: „bound migraphx:0 (whole graph)"
      2. Scheitert nur DAS: Bau ohne die Sperre, EP zuerst, CPU dahinter -> der Graph
         laeuft, aber ein Teil auf der CPU.
         Log: „PARTLY cpu (…)"  — der Befund, den wir sehen wollen.
      3. Scheitert auch das (oder der EP bindet nicht): reine CPU-Session.
         Log: „FELL BACK cpu (…)"  — laut, aber NICHT toedlich.

    NICHT TOEDLICH IST ABSICHT. `engine_ov`/`engine_cuda` WERFEN, wenn ihr Geraet
    fehlt — dort ist das richtig, weil ein Intel-/NVIDIA-Image ohne sein Geraet eine
    Fehlkonfiguration ist. Hier waere es falsch: ein Prozess, der gar nicht startet,
    analysiert nichts, und die Erkennung bleibt fachlich korrekt, wenn sie auf der CPU
    rechnet — nur langsamer. Der Betreiber sieht den Zustand in jeder Job-Antwort
    (`bindung`) und in `/health`, nicht nur in einer Logzeile. Genau diesen Zustand
    faehrt uebrigens unsere eigene Maschine: hier gibt es kein /dev/kfd, und das
    rocm-Image muss trotzdem sauber hochkommen."""
    bericht = {"stufe": marke, "ep": EP, "geraet": None, "stand": None}
    if EP not in ort.get_available_providers():
        s = ort.InferenceSession(modell_bytes, sess_options=_so(False),
                                 providers=["CPUExecutionProvider"])
        bericht.update({"stand": "cpu", "grund": "MIGraphXExecutionProvider not in "
                                                 "onnxruntime's provider list"})
        _melden(f"stage {marke}: FELL BACK cpu ({bericht['grund']})")
        return s, bericht
    if not _kfd_da():
        # Task-#15-Muster (face_audit._ort_session): ohne Geraeteknoten ist der
        # Versuch chancenlos und produziert nur Treiber-Spam.
        s = ort.InferenceSession(modell_bytes, sess_options=_so(False),
                                 providers=["CPUExecutionProvider"])
        bericht.update({"stand": "cpu", "grund": f"no AMD KFD device node ({KFD})"})
        _melden(f"stage {marke}: FELL BACK cpu ({bericht['grund']})")
        return s, bericht
    opt = _provider_optionen()
    try:
        s = ort.InferenceSession(modell_bytes, sess_options=_so(True),
                                 providers=[(EP, opt)])
        if EP in s.get_providers():
            bericht.update({"stand": "migraphx", "geraet": f"migraphx:{GERAET_ID}",
                            "deckung": "ganzer graph"})
            _melden(f"stage {marke}: bound migraphx:{GERAET_ID} (whole graph)")
            return s, bericht
        voll_grund = "EP dropped out of get_providers()"
    except Exception as e:                               # noqa: BLE001
        voll_grund = f"{type(e).__name__}: {str(e)[:300]}"
    try:
        s = ort.InferenceSession(modell_bytes, sess_options=_so(False),
                                 providers=[(EP, opt), "CPUExecutionProvider"])
    except Exception as e:                               # noqa: BLE001
        s = ort.InferenceSession(modell_bytes, sess_options=_so(False),
                                 providers=["CPUExecutionProvider"])
        bericht.update({"stand": "cpu",
                        "grund": f"{type(e).__name__}: {str(e)[:300]}"})
        _melden(f"stage {marke}: FELL BACK cpu ({bericht['grund']})")
        return s, bericht
    if EP not in s.get_providers():
        bericht.update({"stand": "cpu", "grund": voll_grund})
        _melden(f"stage {marke}: FELL BACK cpu ({voll_grund})")
        return s, bericht
    bericht.update({"stand": "migraphx_teilweise", "geraet": f"migraphx:{GERAET_ID}",
                    "deckung": "teilweise", "grund": voll_grund})
    _melden(f"stage {marke}: PARTLY cpu — the EP bound, but not every node landed on "
            f"it ({voll_grund}). Run once with ORT_MIGRAPHX_DUMP_MODEL_OPS=1 and "
            f"onnxruntime log level INFO to see WHICH ops the EP rejected.")
    return s, bericht


# ------------------------------------------------------------------ Aufrufe
_BIND = {"aus": False, "grund": None, "schloss": threading.Lock()}


def _lauf(s, eingabe):
    """Eine Session mit CPU-Eingaengen rechnen. -> Liste der Ausgaenge (numpy)

    IO-BINDING statt `run()`, mit dem AMD-Geraetenamen (s. `GERAET_NAME`): die
    Ausgaenge werden im GERAETESPEICHER gebunden und in EINEM Zug zurueckgeholt,
    statt dass ORT je Ausgang selbst entscheidet.

    EHRLICHE GRENZE, benannt: in DIESER Engine gibt es keine Kette von
    Geraete-Tensoren zwischen Sessions — der Zuschnitt liegt auf der CPU (Modulkopf),
    also beginnt jede Stufe ohnehin auf dem Host. Der Gewinn ist damit klein; was die
    Bindung wirklich leistet, ist die RICHTIGE Geraeteangabe. Faellt sie in einer
    Laufzeit aus, rechnet `run()` dasselbe — deshalb der einmalige, gemeldete
    Rueckfall statt eines Abbruchs."""
    if _BIND["aus"]:
        return s.run(None, eingabe)
    try:
        b = s.io_binding()
        for name, wert in eingabe.items():
            b.bind_cpu_input(name, np.ascontiguousarray(wert))
        for o in s.get_outputs():
            b.bind_output(o.name, GERAET_NAME)
        s.run_with_iobinding(b)
        return b.copy_outputs_to_cpu()
    except Exception as e:                               # noqa: BLE001
        with _BIND["schloss"]:
            if not _BIND["aus"]:
                _BIND["aus"] = True
                _BIND["grund"] = f"{type(e).__name__}: {str(e)[:200]}"
                _melden(f"io-binding not usable on this runtime "
                        f"({_BIND['grund']}) — running the stages with "
                        f"session.run() instead (same values, one extra copy)")
        return s.run(None, eingabe)


def _rec_post(emb, f_norm):
    """Embedding [n, D] -> L2-normiert, dazu die Feature-Norm — in numpy, was
    `engine_cuda.graph_rec_post` als ONNX-Graph tut.

    WARUM NICHT ALS GRAPH: ein selbst gebauter Graph traegt generische Tensornamen
    und kollidierte im .mxr-Cache (s. `modell_cache_vorbereiten`). Die Rechnung ist
    ausserdem eine Reduktion ueber 512 Zahlen je Gesicht — ihr Weg auf den
    Beschleuniger kostete mehr als sie.

    KNOTEN FUER KNOTEN DIESELBE FOLGE wie dort: `sqrt(sum(e*e)) + 1e-9`, dann
    `e / betrag`. Ausgang 0 bleibt `emb/||emb||` (face_audit liefert als
    `normed_embedding` genau diese zweite Teilung, und weil der adaface-Kopf nicht
    exakt Laenge 1 hat, ist sie kein Nulleffekt). `f_norm` ist der DIVISOR des
    Modell-Kopfs (die Naht aus `engine_cuda._fest(norm_aus=True)`) — das ist die
    Feature-Norm auf der Skala 15-30, auf der die Latten dieses Hauses geeicht sind.
    Fehlt die Naht (fremder, unnormierter Kopf), IST der selbst gerechnete Betrag die
    Feature-Norm. -> (emb_n [n,D], norm [n])"""
    e = np.asarray(emb, np.float32)
    if e.ndim == 1:
        e = e.reshape(1, -1)
    betrag = np.sqrt((e * e).sum(axis=1, keepdims=True)) + np.float32(1e-9)
    emb_n = e / betrag
    norm = (np.asarray(f_norm, np.float32).reshape(-1) if f_norm is not None
            else betrag.reshape(-1))
    return emb_n, norm


def _kopf_post(simcc_x, simcc_y):
    """RTMPose-Ausgaenge -> Kopf-Score je Gesicht, in numpy — was
    `engine_cuda.graph_kopf` als ONNX-Graph tut und `engine_ov.modell_p` als
    angehaengte Knoten. Score je Punkt 0,5 * (max simcc_x + max simcc_y), Kopf =
    Maximum ueber `pose_wache.KOPF_IDX` (wie `core/ernte.pose_kopf`). -> [n]"""
    mx = np.asarray(simcc_x, np.float32).max(axis=2)
    my = np.asarray(simcc_y, np.float32).max(axis=2)
    kp = (mx + my) * np.float32(0.5)
    return kp[:, wk.pose_wache.KOPF_IDX].max(axis=1)


# ------------------------------------------------------------------ Modelle prozessweit
class ModellBestand:
    """Die Sessions dieses Prozesses: je Stufe und Breite eine, dazu je
    Detektor-Leinwand eine. EINMAL je Prozess, faul gebaut.

    Aufloesungs-UNABHAENGIG ist hier alles ausser dem Detektor: die Eingangsformen
    der fuenf Stufen kommen aus den Modell-Dateien selbst bzw. aus
    `pose_wache.INPUT_SIZE`, und der Zuschnitt davor liegt auf der CPU — es gibt
    also, anders als bei ov/cuda, GAR KEINE geometrie-abhaengigen Graphen ausser dem
    Detektor. Deshalb teilen Video- und Bild-Weg hier denselben Bestand ohne
    Zusatzarbeit.

    KEIN fp16 (Erstwurf, s. Modulkopf): geladen werden die fp32-Dateien aus
    `worker_kern.vorgabe_pfade`.

    `sitzung` (E4, 17.09.2026): DER EINE GRIFF, den eine Schwester-Engine ersetzt,
    die diese Mechanik mit einem anderen Session-Bauer fuehrt. `engine_cpu` fuehrt
    genau diesen Zuschnitt — CPU-Zuschnitt, CPU-Laplace, Sessions je Stufe und
    Breite —, baut seine Sessions aber auf dem OpenVINO-CPU-EP statt auf MIGraphX.
    Die Naht steht HIER und nicht als Kopie drueben, weil sonst zwei Fassungen
    derselben Bestands-Mechanik auseinanderliefen (Hausregel: keine zweite Quelle).
    Vorgabe ist `_sitzung` dieser Datei, also unveraendertes rocm-Verhalten.

    `melden` geht mit: die Bauzeit-Zeilen dieser Klasse tragen sonst die Kennung
    „engine_migraphx" — auf einem cpu-Image liest ein Betreiber dort den Namen eines
    Backends, das seine Maschine gar nicht hat, und sucht an der falschen Stelle
    (im Vorlauf am 17.09. genau so im Log gesehen).

    `lauf` geht mit, und hier ist es KEINE Kosmetik: `_lauf` bindet die Ausgaenge per
    io-binding an das Geraet `GERAET_NAME` („gpu", AMD). Auf einer reinen CPU-Session
    ist das im besten Fall sinnlos und im schlechteren eine falsche Geraeteangabe —
    `engine_cpu` reicht deshalb einen schlichten `session.run()` herein. Die Vorgabe
    bleibt `_lauf`, also unveraendertes rocm-Verhalten."""

    def __init__(self, sitzung=None, melden=None, lauf=None):
        self.sitzung = sitzung or _sitzung
        self.melden = melden or _melden
        self.lauf = lauf or _lauf
        self.spec = wk.rec_spec()
        self.pfade = wk.vorgabe_pfade(self.spec)
        self.norm_vorschrift = wk.norm_vorschriften(self.spec)
        mfd = onnx.load(self.pfade[wk.FD], load_external_data=False)
        me = onnx.load(self.pfade["e"], load_external_data=False)
        mt = onnx.load(self.pfade["t"], load_external_data=False)
        mr = onnx.load(self.pfade["r"], load_external_data=False)
        def dim(m, i):                                    # noqa: E306
            return ec._eingang(m).type.tensor_type.shape.dim[i].dim_value
        pw, ph = wk.pose_wache.INPUT_SIZE
        self.seiten = {wk.FD: (dim(mfd, 2), dim(mfd, 3)),
                       "e": (dim(me, 2), dim(me, 3)), "t": (dim(mt, 2), dim(mt, 3)),
                       "p": (ph, pw), "r": (dim(mr, 2), dim(mr, 3))}
        self.typ = {k: ec._typ_datei(self.pfade[k]) for k in wk.STUFEN}
        # E2c-Naht: traegt dieser Erkennungs-Kopf den Divisor, aus dem die echte
        # Feature-Norm kommt? EINMAL am Modell abgelesen, damit Session und
        # Nachrechnung DIESELBE Antwort benutzen.
        self.norm_naht = ec._div_naht(mr) is not None
        # Die Punktzahl der Pose kommt aus der mittleren Form, an der sie geschaetzt
        # wird (68), die GESAMTZAHL im Ausgang wird GELESEN und geprueft, nicht
        # angenommen — der Schnitt in `stufe` rechnet mit ihr (Intel-Lehre 13.09.:
        # eine geratene Schnittgrenze verfaelschte dort STILL die naechste Stufe).
        self.lm_punkte = len(wk.mean_lmk())
        lm_aus = [d.dim_value for d in mfd.graph.output[0].type.tensor_type.shape.dim]
        if len(lm_aus) != 2 or lm_aus[1] <= 0 or lm_aus[1] % 3 or lm_aus[1] // 3 < self.lm_punkte:
            raise SystemExit(f"1k3d68-Ausgang {mfd.graph.output[0].name!r} hat Form "
                             f"{lm_aus} — erwartet [N, 3*Punkte] mit Punkten "
                             f">= {self.lm_punkte}")
        self.lm_gesamt = lm_aus[1] // 3
        del mfd, me, mt, mr
        self._bau = {
            wk.FD: lambda n: ec._fest(self.pfade[wk.FD], (n, 3, *self.seiten[wk.FD])),
            "e": lambda n: ec._fest(self.pfade["e"], (n, 3, *self.seiten["e"]),
                                    batch_frei=True),
            "t": lambda n: ec._fest(self.pfade["t"], (n, 3, *self.seiten["t"])),
            "p": lambda n: ec._fest(self.pfade["p"], (n, 3, ph, pw)),
            "r": lambda n: ec._fest(self.pfade["r"], (n, 3, *self.seiten["r"]),
                                    norm_aus=self.norm_naht)}
        self._sessions = {}                               # Schluessel -> session
        self._det_typ = {}                                # det-Pfad -> numpy-Typ
        self.bindung = {}                                 # Marke -> Bind-Bericht
        self._schloss = threading.Lock()
        self.bau_s = 0.0

    def _bauen(self, schluessel, marke, bytes_fn):
        with self._schloss:
            eintrag = self._sessions.get(schluessel)
            if eintrag is None:
                t0 = time.monotonic()
                s, bericht = self.sitzung(bytes_fn(), marke)
                dauer = time.monotonic() - t0
                self.bau_s += dauer
                bericht["bau_s"] = round(dauer, 1)
                self.bindung[marke] = bericht
                # Die Bauzeit ist auf diesem EP eine ECHTE Auskunft, keine Fussnote:
                # ohne .mxr-Cache faellt sie bei JEDEM Prozessstart erneut an (der
                # Feldtester mass am 10.09. 63 s fuer ein kleines Modell).
                self.melden(f"stage {marke}: built in {dauer:.1f}s")
                eintrag = self._sessions[schluessel] = s
            return eintrag

    def stufe_session(self, k, n):
        return self._bauen((k, n), f"{k}[n={n}]", lambda: self._bau[k](n))

    def det_session(self, det_wh, det_pfad):
        det_w, det_h = int(det_wh[0]), int(det_wh[1])
        return self._bauen(("det", det_w, det_h), f"det[{det_w}x{det_h}]",
                           lambda: ec._fest(det_pfad, (1, 3, det_h, det_w)))

    def det_typ(self, det_pfad):
        """Der numpy-Typ, in dem die Detektor-Leinwand uebergeben werden muss —
        EINMAL je Datei aus dem ONNX gelesen. Als Aufruf je Frame waere das ein
        `onnx.load` je Frame (der Bild-Weg der CUDA-Engine kann sich das leisten,
        der Video-Weg nicht)."""
        t = self._det_typ.get(det_pfad)
        if t is None:
            t = self._det_typ[det_pfad] = ec._np_typ(ec._typ_datei(det_pfad))
        return t

    def sessions_zaehlen(self):
        return len(self._sessions)

    def stufen_marken(self):
        """Die Stufen-Namen, zu denen es wirklich eine Session gibt — gezaehlt an
        den Objekten, nicht aus STUFEN hochgerechnet."""
        return sorted({k[0] for k in self._sessions if k[0] != "det"})


# ------------------------------------------------------------------ Die Stufen
class Stufen:
    """Die Rechenstufen auf FERTIGEN, CPU-normierten Ausschnitten — die EINE
    Umsetzung fuer Video-Weg und Bild-Weg.

    Bei `engine_ov`/`engine_cuda` sind das zwei getrennte Mechaniken (dort holt der
    Video-Weg seine Ausschnitte per GridSample aus einem Geraete-Tensor, der Bild-Weg
    bekommt numpy herein). Hier gibt es den Unterschied nicht mehr: beide Wege
    schneiden auf der CPU, beide reichen `[n,3,h,w] float32` herein. Zwei Fassungen
    daneben waeren zwei Quellen fuer dieselbe Rechnung."""

    def __init__(self, bestand, breite):
        self.bestand = bestand
        self.breite = int(breite)
        self.seiten = bestand.seiten
        self.norm_vorschrift = bestand.norm_vorschrift
        self.lm_punkte = bestand.lm_punkte

    def det(self, leinwand, det_wh, det_pfad):
        """Die neun Detektor-Ausgaenge fuer EINE fertige Leinwand [1,3,h,w] float32
        (RGB, 0..255 — die Normierung rechnet der Aufrufer, s. `det_normiert`)."""
        s = self.bestand.det_session(det_wh, det_pfad)
        x = np.asarray(leinwand, self.bestand.det_typ(det_pfad))
        aus = self.bestand.lauf(s, {s.get_inputs()[0].name: x})
        return [np.asarray(a, np.float32) for a in aus]

    def _einmal(self, k, X):
        """EIN Aufruf einer Stufe mit GENAU `self.breite` Zeilen.
        -> je Zeile ein Tupel ihrer Ausgabezeilen"""
        s = self.bestand.stufe_session(k, self.breite)
        x = np.asarray(X, ec._np_typ(self.bestand.typ[k]))
        eingabe = {s.get_inputs()[0].name: x}
        namen = [o.name for o in s.get_outputs()]
        werte = self.bestand.lauf(s, eingabe)
        paare = dict(zip(namen, werte))
        n = x.shape[0]
        if k == wk.FD:
            # fc1 [n, 3*gesamt] -> je Gesicht die LETZTEN `lm_punkte` Punkte
            # (insightface landmark.Landmark.get: pred[-lmk_num:]). Die Grenze wird
            # aus der MODELLFORM gerechnet, nie als Konstante gesetzt.
            roh = np.asarray(werte[0], np.float32)
            gesamt = roh.shape[1] // 3
            pts = roh.reshape(-1, gesamt, 3)[:, gesamt - self.lm_punkte:, :]
            return [(pts[j],) for j in range(n)]
        if k == "p":
            kopf = _kopf_post(paare["simcc_x"], paare["simcc_y"])
            return [(kopf[j],) for j in range(n)]
        if k == "r":
            emb_n, norm = _rec_post(werte[0], paare.get("f_norm"))
            return [(emb_n[j], norm[j]) for j in range(n)]
        return [tuple(np.asarray(w, np.float32)[j] for w in werte) for j in range(n)]

    def stufe(self, k, X):
        """Eine Stufe fuer beliebig viele Zeilen, in Aufrufen FESTER Breite.
        Der letzte Rest wird durch Wiederholen der letzten Zeile aufgefuellt, sein
        Doppel verworfen — dasselbe Polster-Muster wie `engine_ov.Satz.stufe`, und
        hier besonders teuer zu verletzen: jede NEUE Form kostet auf diesem EP eine
        volle Neukompilierung. -> je Zeile ein Tupel ihrer Ausgabezeilen"""
        X = np.asarray(X, np.float32)
        aus = []
        b = self.breite
        for start in range(0, len(X), b):
            teil = X[start:start + b]
            fehlt = b - len(teil)
            voll = (np.concatenate([teil, np.repeat(teil[-1:], fehlt, axis=0)])
                    if fehlt else teil)
            aus.extend(self._einmal(k, voll)[:len(teil)])
        return aus


# ------------------------------------------------------------------ Lauf (Video-Weg)
class Satz:
    """Alles, was EIN Rechenstrang fuer sich braucht: der BGR-Vollframe des aktuellen
    Frames und die Stufen-Huelle mit der Video-Breite.

    Warum je Strang (wie bei ov/cuda): die Sessions selbst sind thread-sicher,
    gefaehrlich ist allein der Frame-Zustand — zwei Threads wuerden sich sonst den
    Frame unter der laufenden Rechnung austauschen, und der Fehler faellt nicht auf,
    er verschiebt nur Werte.

    KEIN `probe`: die Kompilat-Wache existiert allein in `engine_ov`; der Dienst
    meldet das Fehlen LAUT und setzt `startprobe` als Ersatz."""

    def __init__(self, g):
        self.g = g
        self.stufen = Stufen(g.bestand, BREITE_VIDEO)
        self.bgr = None

    # -------------------------------------------------- Zuschnitt (CPU)
    def _minv(self, theta):
        """theta (Ausschnitt-Pixel -> GridSample-Koordinate) zurueck in die
        Pixel-Matrix (Ausschnitt-Pixel -> FRAME-Pixel). -> 2x3

        DER KERN REDET IN THETAS, WEIL DIE BEIDEN GPU-ENGINES SIE BRAUCHEN
        (`worker_kern._theta`: `theta = nm @ minv`, `nm = gitter_norm(W, H)`). Diese
        Engine braucht die Gegenrichtung fuer `cv2.warpAffine`. Statt eine zweite
        Matrizen-Familie neben `worker_kern.theta_*` zu stellen — das waere die
        zweite Quelle — wird `nm` hier ANALYTISCH invertiert:
            nm bildet ab:  g = 2x/W + 1/W - 1
            also zurueck:  x = g*W/2 + (W-1)/2
        Das ist exakt und braucht keine Matrix-Inversion. Die fd-Stufe reicht dem
        Kern ihr `M` ohnehin selbst zurueck (`theta_fd`), fuer sie ist dies der
        Rueckweg desselben Wertes; der Gleitkomma-Rundweg liegt bei ~1e-16 relativ
        und damit weit unter der 1/32-Pixel-Quantisierung von `warpAffine`."""
        W, H = self.g.W, self.g.H
        t = np.asarray(theta, np.float64)
        minv = np.empty((2, 3), np.float64)
        minv[0] = t[0] * (W / 2.0)
        minv[1] = t[1] * (H / 2.0)
        minv[0, 2] += (W - 1) / 2.0
        minv[1, 2] += (H - 1) / 2.0
        return minv

    def _crop(self, theta, seiten):
        """EIN Ausschnitt aus dem aktuellen Frame, auf der CPU. -> BGR [h,w,3] uint8

        `cv2.warpAffine(..., borderValue=0.0)` ist GENAU der Griff des Bild-Wegs
        (`bild_kern.pose`, insightface `face_align.norm_crop`) — INTER_LINEAR,
        BORDER_CONSTANT 0, Festkomma auf dem uint8-Frame. Damit sind die
        Ausschnitt-Bytes die Messbasis des vorhandenen Bestands, und die
        uint8-Rundung, die die GPU-Engines hinter ihrem GridSample nachruesten
        muessen (`_u8_rundung`), ist hier per Konstruktion schon da."""
        h, w = seiten
        M = cv2.invertAffineTransform(self._minv(theta))
        return cv2.warpAffine(self.bgr, M, (w, h), borderValue=0.0)

    # -------------------------------------------------- Die Schnittstelle des Kerns
    def det(self, y, uv):
        """Vorverarbeitung + Detektor fuer EINEN Frame. -> die neun Detektor-Ausgaenge

        Der BGR-Vollframe bleibt danach am Satz liegen; die Stufen schneiden ihre
        Gesichter daraus. `worker_kern.nv12_bgr` ist DIE eine Konvertierung dieses
        Hauses (NV12-Puffer -> cv2), `bild_kern.det_leinwand` DIE eine Leinwand-
        Rechnung (Seitenverhaeltnis halten, cv2.resize, oben links, dann RGB) — beide
        werden hier benutzt, nicht nachgebaut."""
        g = self.g
        self.bgr = wk.nv12_bgr((y, uv), g.W, g.H)
        lw, _det_scale, det_wh = bild_kern.det_leinwand(self.bgr, g.det_wh)
        lw = (lw - wk.DET_MEAN) / wk.DET_STD
        return self.stufen.det(lw, det_wh, g.det_pfad)

    def stufe(self, k, thetas):
        """Eine Stufe fuer die uebergebenen Gesichter.
        -> je Gesicht ein Tupel seiner Ausgabezeilen"""
        if self.bgr is None:
            raise RuntimeError("stufe() vor det()")
        if not len(thetas):
            # Der Kern ruft heute nie mit leerer Liste (er prueft `messbar`/`weiter`
            # davor), aber `bild_kern.norm_anwenden` wuerde an `np.stack([])`
            # sterben — und eine leere Stufe ist kein Fehler, sondern nichts zu tun.
            return []
        crops = [self._crop(t, self.g.seiten[k]) for t in thetas]
        X = bild_kern.norm_anwenden(crops, self.g.bestand.norm_vorschrift[k])
        return self.stufen.stufe(k, X)

    def stufe_fd(self, thetas, zuege):
        """Die fd-Stufe: Landmark-Punkte (1k3d68, GPU) und die Laplace-Summen (CPU).
        -> je Gesicht (Punkte [68,3], s_lap, s_lap2)"""
        if self.bgr is None:
            raise RuntimeError("stufe_fd() vor det()")
        aus = self.stufe(wk.FD, thetas)
        lap = [self._laplace(z) for z in zuege]
        return [(a[0], sl, sl2) for a, (sl, sl2) in zip(aus, lap)]

    def _laplace(self, zug):
        """Summe und Summe der Quadrate der Laplace-Werte ueber den engen Crop —
        auf der CPU mit cv2, aus DEMSELBEN Leinwand-Zug, den auch die GPU-Engines
        bekommen. -> (s_lap, s_lap2)

        WARUM UEBER DIE LEINWAND UND NICHT DIREKT UEBER DEN CROP: `worker_kern
        .leinwand_zug` ist die EINE Quelle fuer die Spiegel-Indizes von
        BORDER_REFLECT_101, fuer das Beschneiden ueberlanger Crops und fuer die
        Pixelzahl. Wer hier die Box neu aus dem Zug zurueckrechnete, haette eine
        zweite Fassung derselben Regel. Die Leinwand wird deshalb GEZOGEN (fancy
        indexing = der Gather der GPU-Engines), dann cv2.

        DIE REGION: der 3x3-Kern ohne Polster liefert [C-2,C-2], Ausgabezeile i ist
        Leinwand-Zeile i+1 — und genau dort liegt die erste Crop-Zeile (der
        Spiegelring sitzt auf Leinwand-Zeile 0). `cv2.Laplacian` polstert selbst
        (BORDER_REFLECT_101), also wird der INNERE Teil [1:C-1, 1:C-1] genommen; die
        Maske waehlt daraus die ersten `ch` Zeilen und `cw` Spalten, wortgleich zum
        Masken-Produkt mu*mv der Graphen.

        cv2.cvtColor(BGR2GRAY) statt der nachgebauten Festkomma-Gewichte: das IST die
        Rechnung, die `worker_kern.GRAU_W`/`GRAU_SHIFT` in den Graphen nachbilden
        (dieselben Gewichte, dieselbe CV_DESCALE-Rundung). Hier gibt es das Original,
        also wird das Original benutzt."""
        jx, iy, mu, mv, npx, _beschnitten = zug
        if npx == 0:
            return 0.0, 0.0
        ch = int(mu.sum())
        cw = int(mv.sum())
        lein = self.bgr[iy][:, jx]                        # [C,C,3] uint8, wie der Gather
        grau = cv2.cvtColor(np.ascontiguousarray(lein), cv2.COLOR_BGR2GRAY)
        # CV_64F wie `analyze.sharp` es seit jeher rechnet (dort cv2.Laplacian(...,
        # CV_64F).var()) — die Werte sind ganzzahlig, also ist es dieselbe Zahl wie
        # in f32; genommen wird die Fassung des Bestands.
        lap = cv2.Laplacian(grau, cv2.CV_64F, ksize=1)[1:-1, 1:-1][:ch, :cw]
        return float(lap.sum()), float((lap * lap).sum())

    def warm(self):
        """Jede Session einmal rechnen, bevor die Uhr laeuft — mit genau den Formen,
        die der Lauf ruft. Auf diesem EP ist das keine Hoeflichkeit: die erste
        Rechnung einer Form KOMPILIERT (und legt, wenn der Cache steht, die
        .mxr-Datei an)."""
        g = self.g
        y0 = np.zeros((1, g.H, g.W, 1), np.uint8)
        uv0 = np.full((1, g.H // 2, g.W // 2, 2), 128, np.uint8)
        self.det(y0, uv0)
        # Dasselbe Platzhalter-theta wie in beiden Schwester-Engines (dort
        # `th0 = [[1,0,0],[0,1,0]]`): gewaermt wird die FORM, nicht der Inhalt.
        th0 = np.array([[1, 0, 0], [0, 1, 0]], np.float32)
        for k in wk.KASKADE:
            self.stufe(k, [th0] * BREITE_VIDEO)
        zug0 = wk.leinwand_zug([0, 0, min(wk.LEINWAND - 2, g.W), min(wk.LEINWAND - 2, g.H)],
                               g.W, g.H)
        self.stufe_fd([th0] * BREITE_VIDEO, [zug0] * BREITE_VIDEO)


class Geometrie:
    """Die Sessions EINER Clip-Geometrie. Auf diesem Backend ist das NUR der
    Detektor — alles andere haengt an den Modell-Dateien, nicht am Frame (s.
    `ModellBestand`). Der Geometrie-Bau ist hier deshalb billig; was Zeit kostet,
    ist der einmalige Stufen-Bau im Bestand.

    Kein Frame-Zustand am Objekt: der BGR-Frame liegt im `Satz`, den sich jeder
    Rechenstrang einmal holt."""

    def __init__(self, W, H, best):
        t0 = time.monotonic()
        self.W, self.H = W, H
        (det_w, det_h), _neu, det_scale = wk.det_geometrie(W, H)
        self.det_wh, self.det_scale = (det_w, det_h), det_scale
        self.det_pfad = wk.modell_pfad("det_10g")
        self.bestand = best
        self.seiten = best.seiten
        geteilt0 = best.bau_s
        # Den Detektor dieser Geometrie SOFORT bauen: sein Bind-Bericht gehoert in
        # die Kopf-Auskunft, und auf diesem EP soll die Kompilierzeit im
        # Geometrie-Bau stehen, nicht spaeter still im ersten Frame.
        best.det_session(self.det_wh, self.det_pfad)
        self.bau_geteilt_s = best.bau_s - geteilt0
        self.nm = wk.gitter_norm(W, H)
        self.zentren = wk.zentren_fuellen(self.det_wh, self.det_scale)
        self._lokal = threading.local()
        self._satz_schloss = threading.Lock()
        self.saetze = 0
        self.bau_s = time.monotonic() - t0

    def satz(self):
        s = getattr(self._lokal, "satz", None)
        if s is not None:
            return s
        with self._satz_schloss:
            s = Satz(self)
            self.saetze += 1
        self._lokal.satz = s
        return s


# ------------------------------------------------------------------ Bild-Weg (E2c)
class BildStufen:
    """Der BILD-Weg dieser Engine — die Schnittstelle, die `bild_kern.BildRechner`
    erwartet (`det`, `det_normiert`, `stufe`, `auskunft`, `seiten`,
    `norm_vorschrift`, `lm_punkte`).

    Hier ist er fast nichts mehr: der Video-Weg dieser Engine IST der Bild-Weg,
    angewandt auf Frames (Modulkopf). Der einzige Unterschied ist die Breite —
    Batch 1, weil die Feature-Norm des Lernlaufs ausdruecklich Batch 1 misst
    (`core/normlauf.py`, „NormMass driftet zwischen Batchgroessen")."""

    BREITE = BREITE_BILD

    def __init__(self, engine):
        self.engine = engine
        if engine.bestand is None:
            engine.bestand = engine.bestand_neu()
        self.bestand = engine.bestand
        self.stufen = Stufen(self.bestand, self.BREITE)
        self.seiten = self.bestand.seiten
        self.norm_vorschrift = self.bestand.norm_vorschrift
        self.lm_punkte = self.bestand.lm_punkte
        self._det_pfad = wk.modell_pfad("det_10g")
        self._gesehen = set()

    def det(self, leinwand, det_wh):
        self._gesehen.add(tuple(int(v) for v in det_wh))
        return self.stufen.det(leinwand, det_wh, self._det_pfad)

    def det_normiert(self):
        """Rechnet dieser Bild-Detektor die (x-mean)/std selbst? -> False.
        Wie bei `engine_cuda.BildStufen`: hier wird dasselbe Detektor-ONNX geladen,
        das auch der Video-Weg fuehrt, und die Normierung rechnet `bild_kern` davor
        auf der CPU. Die Frage steht als METHODE da, damit `bild_kern` sie nicht an
        der Engine-Sorte festmacht."""
        return False

    def stufe(self, k, X):
        return self.stufen.stufe(k, X)

    def auskunft(self):
        return {"engine": Engine.name, "geraet": EP, "breite": self.BREITE,
                "det_leinwaende": [f"{w}x{h}" for (w, h) in sorted(self._gesehen)],
                "stufen": self.bestand.stufen_marken()}


# ------------------------------------------------------------------ Die Engine
class Engine:
    """Die MIGraphX-Seite, wie der Kern sie sieht: Frames, Geometrien, Kopf-Auskunft."""

    name = "migraphx"
    stufen_folge = wk.STUFEN

    @staticmethod
    def argumente(ap):
        ap.add_argument("--wurzel", help="Projektwurzel (im Image /app)")
        ap.add_argument("--migraphx-cache", dest="migraphx_cache", default=None,
                        help="Ordner fuer den .mxr-Modell-Cache des MIGraphX-EP "
                             "(ueberschreibt ORT_MIGRAPHX_MODEL_CACHE_PATH). Ohne "
                             "Cache kompiliert JEDER Prozessstart jede Stufe neu.")

    def __init__(self, a):
        # Der Modell-Cache muss stehen, BEVOR die erste Session gebaut wird: der EP
        # liest den Pfad im Konstruktor, eine spaeter gesetzte Variable erreicht eine
        # gebaute Session nicht mehr.
        if getattr(a, "migraphx_cache", None):
            os.environ["ORT_MIGRAPHX_MODEL_CACHE_PATH"] = a.migraphx_cache
        self.cache, self.cache_quelle = modell_cache_vorbereiten()
        _melden(f"model cache: {self.cache} ({self.cache_quelle})")
        self.ep_gelistet = EP in ort.get_available_providers()
        self.kfd = _kfd_da()
        if not self.ep_gelistet:
            # LAUT, aber nicht toedlich (Begruendung in `_sitzung`). Die
            # Provider-Liste allein ist ohnehin KEIN Beweis fuer Ladbarkeit — das
            # war der .510-Befund, aus dem die ldd-Selbstpruefung im Dockerfile
            # entstand; den Beweis liefert erst der Session-Bau.
            _melden("WARN: no MIGraphXExecutionProvider in onnxruntime — every "
                    "stage of this process will run on the CPU (correct values, "
                    "slower). This is reported in /health and in every job answer.")
        elif not self.kfd:
            _melden(f"WARN: no AMD KFD device node ({KFD}) in this container — every "
                    f"stage will run on the CPU. Pass the devices through "
                    f"(--device /dev/kfd --device /dev/dri).")
        os.makedirs(a.out, exist_ok=True)
        self.bestand = None
        SPEICHER.melden("at start")

    def frames(self, clip, W, H, schritt, wache=None):
        return frames_nv12(clip, W, H, schritt, wache=wache)

    def bild_stufen(self):
        """Der BILD-Weg dieser Engine, einmal je Prozess. -> BildStufen"""
        if getattr(self, "_bild", None) is None:
            self._bild = BildStufen(self)
        return self._bild

    def bestand_neu(self):
        """Der Modell-Bestand dieses Prozesses. Als METHODE und nicht als
        `ModellBestand()` an zwei Stellen, damit eine Engine, die DIESE Mechanik mit
        einem anderen Session-Bauer fuehrt (`engine_cpu`, E4), genau diesen einen
        Griff ueberschreibt statt die Klassen zu kopieren. -> ModellBestand"""
        return ModellBestand(_sitzung)

    def bindung_ergaenzen(self, bindung):
        """Die Bindung, die `worker_dienst.engine_bauen` aus dem gelungenen Bau
        ableitet, um das korrigieren, was NUR diese Engine weiss. In place.

        E6 (17.09.2026), hierher gezogen in E4 (17.09.2026): auf migraphx ist „die
        Engine steht" NICHT dasselbe wie „das Geraet rechnet". Der Dienst darf das
        nicht wissen muessen — bis E4 stand diese Unterscheidung als
        `hasattr(engine, 'ep_gelistet')`-Sonderfall IM DIENST, und der naechste
        Backend-Sonderfall haette einen zweiten danebengestellt. Jetzt fragt der
        Dienst EINE Methode, und jede Engine beantwortet sie fuer sich (K1: eine
        Diagnose, die „gebunden" sagt, waehrend die CPU rechnet, ist die teuerste
        Sorte Luege)."""
        echt = bool(self.ep_gelistet and self.kfd)
        bindung["gebunden"] = echt
        bindung["geraet"] = bindung.get("geraet") if echt else "cpu"
        if not echt:
            bindung["grund"] = ("MIGraphXExecutionProvider missing"
                                if not self.ep_gelistet
                                else "no AMD KFD device node (/dev/kfd) in this "
                                     "container")
        return bindung

    def geometrie_bauen(self, geo):
        """Je Clip-Geometrie einmal die Sessions. -> {(W, H): Geometrie}"""
        if self.bestand is None:
            self.bestand = self.bestand_neu()
        graphen = {}
        for W, H, _fps in geo.values():
            if (W, H) not in graphen:
                graphen[(W, H)] = Geometrie(W, H, self.bestand)
        return graphen

    def speicher_bericht(self):
        """Die AMD-Speicherlage aus sysfs (MB) oder None. Der Dienst schreibt daraus
        je Ereignis eine Zeile; die Methode steht HIER, damit `worker_dienst` nichts
        ueber amdgpu wissen muss."""
        return SPEICHER.stand()

    def speicher_melden(self, wobei=""):
        SPEICHER.melden(wobei)

    def kopf_auskunft(self, graphen):
        """Was WIRKLICH gebaut und gebunden wurde — an den Objekten abgelesen, nicht
        aus den Wuenschen. Auf diesem Backend ist der BIND-BERICHT je Stufe das
        wichtigste Feld: er sagt, ob der EP den ganzen Graphen genommen hat, nur einen
        Teil, oder gar nichts (s. `_sitzung`)."""
        g0 = next(iter(graphen.values()))
        best = self.bestand
        stand = {m: b.get("stand") for m, b in sorted(best.bindung.items())}
        return {"provider": EP, "ort": ort.__version__,
                "ep_gelistet": self.ep_gelistet, "kfd": self.kfd,
                "geraet": f"migraphx:{GERAET_ID}" if self.kfd and self.ep_gelistet
                          else "cpu",
                # DER BEFUND, den nur das Feld liefern kann.
                "bindung": {m: dict(b) for m, b in sorted(best.bindung.items())},
                "bindung_kurz": stand,
                "auf_cpu": sorted(m for m, s in stand.items() if s == "cpu"),
                "teilweise_cpu": sorted(m for m, s in stand.items()
                                        if s == "migraphx_teilweise"),
                "model_cache": self.cache, "model_cache_quelle": self.cache_quelle,
                "io_binding": {"geraet": GERAET_NAME, "aus": _BIND["aus"],
                               "grund": _BIND["grund"]},
                "sessions": best.sessions_zaehlen(),
                "bau_s": round(best.bau_s, 1),
                "breite_video": BREITE_VIDEO, "breite_bild": BREITE_BILD,
                "det_onnx": g0.det_pfad,
                "modell_pfade": {k: best.pfade[k] for k in sorted(best.pfade)},
                "modell_typen": {k: ec._typ_name(t) for k, t in sorted(best.typ.items())},
                "fp16": {"stand": "aus (Erstwurf) — fp32-Dateien des Hauses; der "
                                  "EP-Schalter migraphx_fp16_enable kappt "
                                  "programmweit und ist bewusst nicht gesetzt"},
                "zuschnitt": {"wo": "cpu (cv2.warpAffine, Bild-Weg-Muster)",
                              "grund": "der ORT-MIGraphX-EP fuehrt GridSample in "
                                       "keiner Fassung in seiner Op-Allowlist "
                                       "(migraphx_execution_provider.cc:865-1024)"},
                "laplace": "cpu (cv2.Laplacian auf der Leinwand des Kerns)",
                "decode": {"kette": "VAAPI (hw) mit lautem SW-Rueckfall",
                           "byte_gleichheit_amd": "ungemessen — Nachmessweg "
                                                  "`verifyd.py --benchmark`"},
                "gpu_speicher": self.speicher_bericht(),
                "fd": {"breite": BREITE_VIDEO, "punkte_im_ausgang": best.lm_gesamt}}
