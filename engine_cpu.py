#!/usr/bin/env python3
"""ENGINE onnxruntime/CPU — die vierte Backend-Haelfte des Workers (E4).

HERKUNFT UND ZWECK. Bis 0.1.0.540 kannte `worker_dienst.engine_bauen` nur `ov`,
`cuda` und `migraphx`; `backend: cpu` (Werksvorgabe des cpu-Images) lief in ein
`SystemExit` — auf dem cpu-Image analysierte der neue Worker gar nicht. Diese Datei
schliesst die letzte Luecke. Zielsystem ist JEDE Maschine ohne nutzbaren
Beschleuniger: der universelle Rueckfall des Hauses.

KEIN NEUBAU, SONDERN EIN SCHNITT. Der CPU-Rechenweg dieses Workers existiert seit
E6 bewiesen — als Rueckfall-Pfad von `engine_migraphx`: ohne /dev/kfd baut jede
Stufe dort eine reine CPU-Session, und der Rest der Engine ist geraetefrei
(Zuschnitt cv2.warpAffine auf der CPU, Laplace mit cv2, Erkennungs-Norm und
Kopf-Score in numpy, Stufenformen aus den Modell-Dateien). Genau so gemessen am
17.09.2026: ein Roundtrip im rocm-Image auf DIESER Maschine (kein /dev/kfd, acht
Sessions „FELL BACK cpu") reproduzierte den Intel-Fixpunkt EXAKT — 68 Frames,
bestes 3s-Fenster 9. Diese Datei baut deshalb NICHTS davon neu, sie importiert
`ModellBestand`, `Stufen`, `Satz`, `Geometrie` und `BildStufen` aus
`engine_migraphx` und ersetzt GENAU ZWEI Dinge:

  1. den SESSION-BAUER (`_sitzung` hier statt dort) — CPU statt MIGraphX, und zwar
     bevorzugt ueber den OpenVINO-CPU-EP (s. naechster Abschnitt);
  2. die DECODE-KETTE — Software, ohne VAAPI-Versuch (s. „DECODE").

Eine Zweitschrift der Bestands-Mechanik waere die zweite Quelle, die dieses Haus
verbietet: dann liefen Zuschnitt, Polsterung und Nachrechnung auf zwei Backends
auseinander, ohne dass es jemand merkt.

WELCHE IMAGE-VARIANTE DIESE ENGINE FAEHRT, vollstaendig benannt (Deckungs-Regel):
**cpu** und nur cpu. Die uebrigen vier Varianten kommen hier nie als Engine an —
**gpu** und **gpu-legacy** fahren `engine_ov`, **cuda** faehrt `engine_cuda`,
**rocm** faehrt `engine_migraphx`. Die Datei liegt trotzdem in JEDEM Image (faule
Importe im Dienst, Gate-Stufe „alle Runtime-Module vorhanden").

ABER: SIE IST NICHT NUR DIE ENGINE DES cpu-IMAGES. Jedes Image kann hier landen —
`backend: cpu` ist auf jeder Variante ein gueltiger Config-Wert, und
`face_audit.resolve_backend` liefert `cpu`, wenn nichts gesetzt ist. Auf einem
gpu-Image ohne OpenVINO-EP baut diese Datei dann schlicht Sessions auf dem
CPU-EP. Deshalb gibt es hier keine Zeile, die ein cpu-Image VORAUSSETZT.

────────────────────────────────────────────────────────────────────────────────
WARUM OpenVINO-CPU UND NICHT DER NACKTE CPU-EP — DER GEMESSENE HEBEL
────────────────────────────────────────────────────────────────────────────────
GEMESSEN VOM FELDTESTER (Discussion #29, 10.09.2026, dieselbe Maschine, dieselben
Modelldateien, alle Modelle des Urteilspfads): der OpenVINO-CPU-EP rechnet
durchgehend 3-7x schneller als das nackte `onnxruntime` — adaface **48,7 ms statt
192,2 ms** je Inferenz. Das ist kein Tuning-Effekt an einer Stelle, sondern der
Unterschied zwischen zwei Inferenz-Stacks auf derselben CPU.

Deshalb baut diese Engine ihre Sessions in DIESER Reihenfolge, je Stufe einzeln
und laut protokolliert:

  1. `OpenVINOExecutionProvider` mit `device_type=CPU`, `precision=FP32`
     -> Log: „stage X: bound openvino:CPU"
  2. faellt er aus (EP fehlt, Geraet bindet nicht, Provider-Option unbekannt):
     `CPUExecutionProvider` -> Log: „stage X: plain onnxruntime CPU (…)"

BEIDE ZUSTAENDE SIND KORREKT, nur verschieden schnell — anders als bei ov/cuda ist
hier nichts kaputt, wenn der zweite greift. Genau deshalb WIRFT diese Engine nie
(wie `engine_migraphx`, aus demselben Grund: ein Prozess, der nicht startet,
analysiert nichts; die Erkennung bleibt fachlich korrekt, sie rechnet nur
langsamer). Der Zustand steht in `kopf_auskunft`, in jeder Job-Antwort und in
/health, nicht bloss in einer Startzeile.

`precision=FP32` IST PFLICHT UND KEIN SCHMUCK. Der OpenVINO-CPU-Plugin waehlt seine
Rechen-Genauigkeit sonst selbst und nimmt auf CPUs mit AVX512-BF16/AMX **bf16** —
eine andere Genauigkeit als die fp32-Dateien des Hauses. Dieselbe Klasse Fehler ist
hier schon einmal teuer gewesen: fp16 auf der Intel-iGPU wich auf dem Gesichtsreiz
bis 0,149 ab, FP32 auf demselben Geraet 0,0000095 (face_audit.NORM_PSEUDO_GERAETE,
gemessen 24.08.2026). Die Latten dieses Hauses sind an fp32-Zahlen geeicht; eine
still andere Genauigkeit verschiebt Urteile, ohne dass irgendwo etwas rot wird.
Der Schluessel `precision` ist derselbe, den `face_audit` fuer GPU_FP32 benutzt.

WAS DER OV-CPU-EP NICHT AENDERT: er ist ein ANDERER Rechen-Stack, keine andere
Rechnung — aber Bit-Gleichheit zum nackten CPU-EP ist damit NICHT zugesagt und
wird hier auch nicht behauptet. Der Beleg, dass die URTEILE gleich bleiben, ist die
Vorher/Nachher-Messung am Grundwahrheits-Korpus, nicht diese Datei.

────────────────────────────────────────────────────────────────────────────────
THREAD-REGIE: STRAENGE MAL THREADS GEGEN DIE KERNZAHL
────────────────────────────────────────────────────────────────────────────────
Auf der CPU ist die Threadzahl kein Detail, sondern DER zweite Hebel — und mehr ist
nicht besser. Zwei Messungen dieses Hauses sagen es:

  * Mini-Netze ersticken am Thread-Overhead: 12 Threads 33+57 ms je Bild gegen
    4 Threads 4+13 ms (`core/guete.py:355-358`, im Prod-Container unter Last
    gemessen, .377b). Das sind GENAU die Modelle, die hier als Stufen `e` (fiqa)
    und `t` (ediffiqa) laufen — dieselben Dateien, dieselbe Groessenklasse.
  * Auch mittlere Netze verlieren: 2d106det 4 Threads 3,63 ms gegen 12 Threads
    6,97 ms (`face_audit._ort_thread_opts`, 31.08.2026, diese Maschine).

Dazu kommt der Punkt, den ein einzelner Session-Deckel nicht sieht: der Worker
faehrt N RECHENSTRAENGE im selben Prozess (`worker_dienst --threads N`). Jeder
Strang rechnet seine eigenen Stufen; die Thread-Pools der Sessions sind
prozessweit GETEILT, aber die gleichzeitigen Auffuehrungen sind es nicht. Wer je
Session die volle Kernzahl nimmt, ueberbucht die Maschine um den Faktor N und
bezahlt sie in Umschaltungen.

Die Regie steht deshalb in `_stufen_deckel` und rechnet: erlaubte Kerne (das ist
die EINE Haus-Ableitung `face_audit._threads_ableiten` ueber cgroup-Quote UND
Affinitaets-Maske, nicht `os.cpu_count()`), geteilt durch die Strangzahl, je
Modellklasse zusaetzlich nach oben gedeckelt. Eine ausdrueckliche Vorgabe des
Betreibers (`cpu_threads`/`SUSLIK_CPU_THREADS`) SCHLAEGT die Rechnung — wer die
Zahl setzt, bekommt genau sie, wie ueberall im Haus.

EHRLICHE GRENZE: die Klassen-Deckel sind aus den beiden Messungen oben
UEBERTRAGEN, nicht auf jeder Stufe dieses Wegs einzeln nachgemessen. Uebertragen
ist bei `e`/`t` wortwoertlich (dieselben Modelldateien), bei `fd`/`p` eine
Analogie. Wo sie falsch liegen, kosten sie Tempo, nie Werte.

────────────────────────────────────────────────────────────────────────────────
DECODE
────────────────────────────────────────────────────────────────────────────────
**SOFTWARE, per Bauart, ohne HW-Versuch.** Das cpu-Image traegt ffmpeg, aber KEINEN
VAAPI-Treiber (kein intel-media-va-driver, kein mesa, kein i965) — ein
VAAPI-Versuch koennte dort nie gelingen. Ihn trotzdem je Ereignis zu fahren hiesse:
ein ffmpeg-Start umsonst und eine „hwdec_fallback"-Zeile je Ereignis in einem Log,
in dem dieselbe Zeile auf den anderen Varianten ein echter BEFUND ist. Eine Wache,
die immer anschlaegt, ist keine Wache mehr.

Die Kette ist die SOFTWARE-Kette von `engine_migraphx._ffmpeg_nv12(hw=False)`
(select vor dem Decode, `format=nv12`, rawvideo), der Byte-Weg dahinter
`worker_kern.nv12_strom` — beides unveraendert und nur EINMAL im Haus. Der
gepinnte Pixelpfad (CLAUDE.md) ist damit trivial erfuellt: Software-Decode ist die
Seite, gegen die am 04.08.2026 die Byte-Gleichheit gemessen wurde.

────────────────────────────────────────────────────────────────────────────────
WAS BEWUSST NICHT DRIN IST
────────────────────────────────────────────────────────────────────────────────
* **Ein GPU-Zuschnitt.** Es gibt hier kein Geraet, auf dem ein GridSample billiger
  waere als `cv2.warpAffine`. Der Bestands-Zuschnitt ist zugleich der, an dem alle
  Referenzen dieses Hauses gemessen sind.
* **fp16/bf16.** Siehe oben: fp32 ist die Eichung, nicht die Bequemlichkeit.
* **Kompilat-/Werte-Probe (`Satz.probe`).** Gibt es nur in `engine_ov`; der Dienst
  meldet das Fehlen LAUT und setzt `startprobe` als Ersatz
  (`worker_dienst.engine_bauen`). Wie auf cuda und rocm.
* **Ein Speicher-Deckel.** Der CPU-EP hat keinen Geraetespeicher zu deckeln; der
  RAM dieses Prozesses steht unter der Speicher-Wache des Dienstes
  (`worker_dienst.SpeicherWache`), die ihn ohnehin misst.
"""
import os
import threading

import worker_kern as wk                                 # noqa: E402  Bootstrap + Wert-Weg

import onnxruntime as ort                                # noqa: E402

import face_audit                                        # noqa: E402  Thread-Ableitung
import core.registry as _reg                             # noqa: E402  Geraete-Optionen
# DER GANZE BESTANDS-ZUSCHNITT KOMMT AUS engine_migraphx, und das ist der Schnitt
# dieser Etappe (Begruendung im Kopf). Der Import zieht nichts AMD-Spezifisches in
# den Prozess: die Datei laedt beim Import `worker_kern`, `cv2`, `onnx`,
# `onnxruntime`, `bild_kern`, `face_audit` und `engine_cuda` (nur ONNX-Helfer) —
# die erste ROCm-Beruehrung steht in ihrem `_sitzung`, und genau das ist die
# Funktion, die hier ersetzt wird. `SysfsSpeicher` sucht beim Import einmal nach
# einer amdgpu-Karte und findet keine; das kostet einen glob und sonst nichts.
import engine_migraphx as em                             # noqa: E402

EP_OV = "OpenVINOExecutionProvider"
EP_CPU = "CPUExecutionProvider"
# Das Geraet, das `worker_dienst.engine_bauen` VOR dem Bau in die Bindung schreibt.
# Nach dem Bau praezisiert `Engine.bindung_ergaenzen` es auf den Stack, der wirklich
# gebunden hat („openvino:CPU" oder „cpu") — vorher weiss es niemand.
GERAET = "cpu"
# Das OpenVINO-Geraet. „CPU" ist der Geraetename des OpenVINO-CPU-Plugins; er hat
# mit dem ONNXRUNTIME-Geraet „cpu" nichts zu tun und darf nicht mit ihm verwechselt
# werden — das eine waehlt den Inferenz-Stack, das andere den Speicherort.
OV_GERAET = "CPU"
# Die geraete-eigenen Provider-Optionen kommen AUS DER REGISTRY, nicht aus einem
# Literal hier: der Startup-Benchmark misst denselben Weg und muss dieselbe
# Genauigkeit fahren, sonst zeigt er eine Zahl, die die Anlage nie erreicht (K1).
# Heute ist das `precision: FP32` — Begruendung steht am Eintrag in core/registry.
OV_OPTIONEN = _reg.ep_optionen("openvino", OV_GERAET)
OV_PRAEZISION = OV_OPTIONEN.get("precision")
# Wohin der OpenVINO-CPU-EP seine Kompilate legt, wenn nichts gesetzt ist.
# BESTANDSMUSTER (verifyd.py:1052, face_audit.py:1206): `<data_dir>/clips/ov_cache_models`
# — im VOLUME, nicht im Image, und unter `clips/`, weil dieser Ordner vom Backup
# ausgenommen ist (Kompilate sind regenerierbar) und weil der Dienst dort bereits
# einen Deckel fuehrt (`ov_cache_max_gb`, verifyd.py:7569-7576; er raeumt beide
# ov_cache-Ordner). Ohne cache_dir kompiliert der EP bei JEDEM Prozessstart neu.
# Gesetzt wird der Pfad ueber die Umgebung (Dockerfile/Dienst); hier steht der
# Rueckfall fuer Laeufe ausserhalb des Images.
CACHE_ENV = "SUSLIK_OV_CACHE_DIR"
CACHE_VORGABE = "/data/clips/ov_cache_models"

# ---------------------------------------------------------------- Thread-Regie
# Deckel je MODELLKLASSE (Begruendung und Herleitung im Modulkopf). Der Wert ist
# eine OBERGRENZE; gerechnet wird immer das Minimum aus ihm und dem Strang-Budget.
#
#   e, t   die beiden Guete-Netze — DIESELBEN Dateien, die `core/guete.py` mit
#          `deckel=4` faehrt, und dort ist die 4 im Prod-Container GEMESSEN
#          (12 Threads 33+57 ms gegen 4 Threads 4+13 ms). Wortwoertlich uebernommen.
#   fd, p  1k3d68 und RTMPose, beide auf kleinen Eingaengen (192er bzw.
#          pose_wache.INPUT_SIZE). Analogie zur 2d106det-Messung (4 Threads 3,63 ms
#          gegen 12 Threads 6,97 ms, face_audit._ort_thread_opts) — uebertragen,
#          nicht einzeln nachgemessen; das steht auch im Kopf.
#   r      der Erkennungs-Kopf (adaface). Das groesste Netz des Urteilspfads und
#          die Stufe, an der der Feldtester den 3-7x-Unterschied gemessen hat
#          (48,7 gegen 192,2 ms). Kein Klassen-Deckel: hier zahlt sich Breite aus,
#          begrenzt wird allein durch das Strang-Budget.
#   det    der Detektor (det_10g) auf der grossen Leinwand — dito.
STUFEN_DECKEL = {"e": 4, "t": 4, wk.FD: 4, "p": 4, "r": None, "det": None}


def _melden(text):
    """Eine Zeile ins Prozess-Log (fd 2) — dorthin, wo auch der Dienst seine
    Aufbau-Zeilen schreibt. Kein Import von `worker_dienst`: der importiert diese
    Datei, und ein Ringimport waere hier ein Startfehler statt einer Logzeile
    (wortgleiche Begruendung wie `engine_cuda._melden`/`engine_migraphx._melden`)."""
    try:
        os.write(2, (f"engine_cpu: {str(text).strip()}\n").encode())
    except Exception:                                    # noqa: BLE001
        pass


def _kerne():
    """Die erlaubte Kernzahl dieses Containers -> (n, quelle).

    DIE EINE HAUS-ABLEITUNG, nicht `os.cpu_count()`: `face_audit._threads_ableiten`
    nimmt das MINIMUM aus cgroup-Quote und Affinitaets-Maske und laesst eine
    ausdrueckliche Vorgabe (`SUSLIK_CPU_THREADS`, aus der Config `cpu_threads`
    gesetzt) vorgehen. Beide Grenzen sind echt und unabhaengig; wer die kleinere
    ignoriert, baut zu grosse Pools und saeumt das Log mit
    pthread_setaffinity-EINVAL-Zeilen (Feldbefund Test-LXC: Quote 12, nproc 8)."""
    env = (os.environ.get("SUSLIK_CPU_THREADS") or "").strip()
    vorgabe = int(env) if env.isdigit() and int(env) > 0 else None
    n = face_audit._threads_ableiten(face_audit._cgroup_quote(),
                                     face_audit._cpuset_erlaubt(), vorgabe)
    return max(1, int(n)), ("cpu_threads/SUSLIK_CPU_THREADS" if vorgabe
                            else "cgroup quota / cpu affinity mask")


def _stufen_deckel(straenge):
    """Threads je Session, je Modellklasse -> ({klasse: n}, bericht)

    STRAENGE MAL THREADS GEGEN DIE KERNZAHL (Modulkopf). `straenge` ist die Zahl der
    Rechenstraenge dieses Prozesses; das Budget je Strang ist die erlaubte Kernzahl
    durch sie, mindestens 1. Darauf der Klassen-Deckel.

    EINE AUSDRUECKLICHE VORGABE SCHLAEGT DIE STRANG-RECHNUNG: wer `cpu_threads`
    setzt, bekommt diese Zahl als Budget und nicht die geteilte — das ist die
    Hausregel aus `_ort_thread_opts`. Sie schlaegt aber NICHT den Klassen-Deckel:
    `cpu_threads` ist eine OBERGRENZE, keine Vorschrift, und der Deckel der
    Mini-Netze ist gemessen. Dieselbe Lesart hat `core/guete.py`, das seine beiden
    Netze mit `deckel=4` baut, egal was der Betreiber gesetzt hat — waere das anders,
    rechneten dieselben zwei Modelle im Worker langsamer als im Dienst."""
    kerne, quelle = _kerne()
    vorgabe = quelle.startswith("cpu_threads")
    budget = kerne if vorgabe else max(1, kerne // max(1, int(straenge)))
    aus = {}
    for k, deckel in STUFEN_DECKEL.items():
        aus[k] = budget if deckel is None else max(1, min(budget, deckel))
    bericht = {"kerne": kerne, "kerne_quelle": quelle, "straenge": int(straenge),
               "budget_je_strang": budget, "vorgabe_schlaegt_rechnung": vorgabe,
               "threads_je_stufe": dict(aus)}
    # DIE UEBERBUCHUNG, die eine ausdrueckliche Vorgabe erzeugen kann — benannt, nicht
    # heimlich korrigiert. `cpu_threads` bedeutet „so viele Threads je Session", und
    # auf schwachen Maschinen setzt der Auto-Default (core/kette.auto_default, #21)
    # genau das: die Zahl der physischen Kerne. Mit mehreren Rechenstraengen laufen
    # dann N Sessions mit je dieser Zahl. Wir aendern die Bedeutung des Schalters
    # NICHT (Hausregel: wer die Zahl setzt, bekommt genau sie) — aber wir sagen, was
    # daraus folgt, sonst sucht ein Betreiber die verlorene Zeit woanders.
    if vorgabe and int(straenge) * budget > kerne:
        bericht["ueberbucht"] = {"threads_gesamt": int(straenge) * budget,
                                 "kerne": kerne}
    return aus, bericht


# Prozessweit: die Regie steht EINMAL fest (beim Engine-Bau), damit jede Session
# dieselbe Zahl bekommt und der Bericht nicht je Aufruf neu gerechnet wird.
_REGIE = {"deckel": None, "bericht": None, "schloss": threading.Lock()}


def regie_setzen(straenge):
    """Die Thread-Regie dieses Prozesses festlegen und LAUT melden. -> bericht"""
    with _REGIE["schloss"]:
        deckel, bericht = _stufen_deckel(straenge)
        _REGIE["deckel"], _REGIE["bericht"] = deckel, bericht
    je_klasse = ", ".join(f"{k}={v}" for k, v in sorted(deckel.items()))
    _melden(f"thread plan: {bericht['kerne']} usable core(s) "
            f"({bericht['kerne_quelle']}) / {bericht['straenge']} compute thread(s) "
            f"= {bericht['budget_je_strang']} per session, capped per model class "
            f"({je_klasse})")
    if bericht.get("ueberbucht"):
        u = bericht["ueberbucht"]
        _melden(f"WARN: cpu_threads is set explicitly, so every session gets that "
                f"number — {bericht['straenge']} compute thread(s) x "
                f"{bericht['budget_je_strang']} = {u['threads_gesamt']} threads on "
                f"{u['kerne']} usable core(s). That is your setting and it is kept; "
                f"if the analysis feels slow, either lower cpu_threads or reduce the "
                f"number of compute threads.")
    return bericht


def _threads_fuer(marke):
    """Die Threadzahl fuer eine Stufen-Marke („det[640x640]", „r[n=2]", …).
    Unbekannte Marke -> Budget ohne Klassen-Deckel (nie 0, nie eine Ausnahme)."""
    deckel = _REGIE["deckel"]
    if not deckel:
        return None
    klasse = marke.split("[", 1)[0]
    return deckel.get(klasse) or deckel.get("r")


def cache_vorbereiten():
    """Den OpenVINO-Kompilat-Cache scharf machen. -> (pfad, quelle)

    „Nur dann als Default nachlegen, wenn nichts gesetzt ist" (dieselbe Regel wie
    `engine_migraphx.modell_cache_vorbereiten`): ein Betreiber, der den Pfad selbst
    gesetzt hat, behaelt seine Wahl. Nicht schreibbar ist kein Fehler, sondern eine
    laute Zeile und danach Kompilieren bei jedem Start."""
    da = (os.environ.get(CACHE_ENV) or "").strip()
    pfad, quelle = (da, "environment") if da else (CACHE_VORGABE, "default")
    try:
        os.makedirs(pfad, exist_ok=True)
        probe = os.path.join(pfad, ".writetest")
        with open(probe, "w") as f:
            f.write("x")
        os.remove(probe)
    except OSError as e:
        _melden(f"WARN: OpenVINO cache dir {pfad!r} not writable "
                f"({type(e).__name__}: {e}) — every process start will recompile "
                f"every stage")
        return pfad, f"{quelle} (not writable)"
    return pfad, quelle


_CACHE = {"pfad": None, "quelle": None}


def _so(marke):
    """Session-Optionen einer Stufe -> (SessionOptions, wirklich gesetzte Threadzahl)

    Die Haus-Kappung, zusaetzlich auf die Klassen-Zahl dieser Stufe gedeckelt
    (s. `_stufen_deckel`). `face_audit._ort_thread_opts` ist DER eine Griff des
    Hauses fuer `intra_op_num_threads`/`inter_op_num_threads` (Gate-Stufe
    „ORT-Kappungs-Deckung" erzwingt ihn); `deckel=` ist sein vorgesehener Weg, eine
    Klasse kleiner zu fahren — derselbe, mit dem `core/guete.py` seine Mini-Netze
    auf 4 setzt.

    ZURUECKGEGEBEN WIRD DIE ZAHL AUS DEN OPTIONEN, nicht unser Wunsch: der
    Haus-Griff deckelt zusaetzlich mit seiner eigenen, GEMESSENEN Threadzahl
    (`_threads_bestimmen`), und das Ergebnis kann kleiner sein als unser Deckel. Wer
    im Bericht den Wunsch statt der Wirkung nennt, baut genau die Diagnose-Luege,
    gegen die dieses Haus seine K1-Regel hat."""
    so = face_audit._ort_thread_opts(deckel=_threads_fuer(marke))
    return so, int(getattr(so, "intra_op_num_threads", 0) or 0)


def _sitzung(modell_bytes, marke):
    """EINE Session, MIT LAUTEM ZWEISTUFIGEM BIND-PROTOKOLL. -> (session, bericht)

    Stufe 1: OpenVINO-CPU-EP (fp32, mit Kompilat-Cache) — der gemessene Hebel.
    Stufe 2: `CPUExecutionProvider` — korrekt, nur langsamer.

    WARUM DIE PROVIDER-OPTIONEN EINZELN ABGESCHAELT WERDEN: `onnxruntime-openvino`
    prueft seine Provider-Optionen streng und WIRFT bei einem unbekannten
    Schluessel. Welche Schluessel eine gegebene Fassung kennt, ist kein Vertrag,
    den wir haben — also wird es PROBIERT und der Verlust benannt, statt ihn
    anzunehmen. Faellt `num_of_threads` weg, rechnet OpenVINO mit seiner eigenen
    Vorgabe (Tempo-Frage); faellt `precision` weg, ist das ein WERTE-Thema und die
    Zeile sagt es ausdruecklich.

    NIE TOEDLICH (wie `engine_migraphx._sitzung`, gleiche Begruendung): ein Prozess,
    der nicht startet, analysiert nichts. Hier kommt dazu, dass beide Zustaende
    fachlich richtig sind — CPU IST das Soll dieses Backends."""
    sess_opt, threads = _so(marke)
    bericht = {"stufe": marke, "geraet": None, "stand": None, "threads": threads}
    if EP_OV in ort.get_available_providers():
        opt = {"device_type": OV_GERAET, **OV_OPTIONEN}
        if _CACHE["pfad"] and not str(_CACHE["quelle"] or "").endswith("(not writable)"):
            opt["cache_dir"] = _CACHE["pfad"]
        if threads:
            opt["num_of_threads"] = str(threads)
        verloren = []
        while True:
            try:
                s = ort.InferenceSession(modell_bytes, sess_options=sess_opt,
                                         providers=[EP_OV], provider_options=[dict(opt)])
                break
            except Exception as e:                       # noqa: BLE001
                # Genau EINEN Schluessel abschaelen, in der Reihenfolge
                # „kostet Tempo" vor „kostet Aussage" — und den Verlust merken.
                for k in ("num_of_threads", "cache_dir", "precision"):
                    if k in opt:
                        verloren.append((k, f"{type(e).__name__}: {str(e)[:120]}"))
                        del opt[k]
                        break
                else:
                    s = None
                    bericht.update({"stand": "cpu",
                                    "grund": f"{type(e).__name__}: {str(e)[:300]}"})
                    _melden(f"stage {marke}: OpenVINO CPU EP unusable "
                            f"({bericht['grund']}) — plain onnxruntime CPU instead")
                    break
        if s is not None:
            for k, g in verloren:
                _melden(f"stage {marke}: provider option {k!r} rejected by this "
                        f"onnxruntime-openvino ({g})" + (
                            " — stages may compute in a precision other than fp32; "
                            "the house thresholds are calibrated on fp32"
                            if k == "precision" else ""))
            if EP_OV in s.get_providers():
                bericht.update({"stand": "openvino", "geraet": f"openvino:{OV_GERAET}",
                                "precision": opt.get("precision"),
                                "cache_dir": opt.get("cache_dir"),
                                "optionen_abgelehnt": [k for k, _g in verloren]})
                _melden(f"stage {marke}: bound openvino:{OV_GERAET} "
                        f"(precision {opt.get('precision', 'plugin default')}, "
                        f"{bericht['threads'] or 'default'} thread(s))")
                return s, bericht
            # EP war gelistet, ist aber aus der Session gefallen: onnxruntime
            # rechnet dann still auf dem CPU-EP weiter. Das ist kein Fehler,
            # aber es ist NICHT der Weg, den wir gewaehlt haben — also laut.
            bericht.update({"stand": "cpu",
                            "grund": "OpenVINO EP dropped out of get_providers()"})
            _melden(f"stage {marke}: OpenVINO CPU EP did not stay bound "
                    f"({bericht['grund']}) — plain onnxruntime CPU instead")
    else:
        bericht.update({"stand": "cpu", "grund": f"no {EP_OV} in this onnxruntime "
                                                 f"build"})
    s = ort.InferenceSession(modell_bytes, sess_options=sess_opt,
                             providers=[EP_CPU])
    bericht["geraet"] = "cpu"
    _melden(f"stage {marke}: plain onnxruntime CPU "
            f"({bericht.get('grund') or 'no reason recorded'}, "
            f"{bericht['threads'] or 'default'} thread(s))")
    return s, bericht


def _run(s, eingabe):
    """Eine Stufe rechnen. -> Liste der Ausgaenge (numpy)

    SCHLICHT, UND DAS IST DER PUNKT. Die AMD-Seite bindet ihre Ausgaenge per
    io-binding an ein Geraet (`engine_migraphx._lauf`, Geraetename „gpu"/AMD) und
    holt sie in EINEM Zug zurueck. Hier gibt es kein Geraet: die Eingaenge liegen im
    Hostspeicher, die Ausgaenge auch, und eine Geraeteangabe waere im besten Fall
    wirkungslos und im schlechteren falsch. `run()` ist der ehrliche Weg — dieselben
    Werte, ein Aufruf weniger."""
    return s.run(None, eingabe)


# ------------------------------------------------------------------ Decode
def frames_nv12(clip, W, H, schritt, wache=None):
    """Sample-Frames als (i, y, uv) — SOFTWARE-Decode, ohne HW-Versuch.

    Begruendung im Modulkopf („DECODE"): das cpu-Image traegt keinen VAAPI-Treiber,
    ein HW-Versuch koennte nie gelingen, und eine `hwdec_fallback`-Zeile je Ereignis
    entwertete dieselbe Zeile auf den Varianten, wo sie ein echter Befund ist.
    Kette und Byte-Weg sind die des Hauses, nicht eine dritte Fassung."""
    return wk.nv12_strom(em._ffmpeg_nv12(clip, schritt, False), W, H, schritt, "SW",
                         wache=wache)


# ------------------------------------------------------------------ Bild-Weg
class BildStufen(em.BildStufen):
    """Der Bild-Weg dieser Engine — unveraendert der von `engine_migraphx`
    (Batch 1, CPU-Zuschnitt, dieselben Normierungs-Vorschriften). Ueberschrieben
    wird allein die AUSKUNFT: „geraet" darf hier nicht den MIGraphX-EP nennen."""

    def auskunft(self):
        a = super().auskunft()
        a.update({"engine": Engine.name, "geraet": Engine.geraet_text()})
        return a


# ------------------------------------------------------------------ Die Engine
class Engine:
    """Die CPU-Seite, wie der Kern sie sieht: Frames, Geometrien, Kopf-Auskunft.

    Die Rechen-Mechanik kommt vollstaendig aus `engine_migraphx` (Modulkopf); diese
    Klasse setzt den Session-Bauer, die Decode-Kette und die Auskunft."""

    name = "cpu"
    stufen_folge = wk.STUFEN

    @staticmethod
    def argumente(ap):
        ap.add_argument("--wurzel", help="Projektwurzel (im Image /app)")
        ap.add_argument("--ov-cache", dest="ov_cache", default=None,
                        help=f"Ordner fuer die OpenVINO-Kompilate des CPU-EP "
                             f"(ueberschreibt {CACHE_ENV}). Ohne Cache kompiliert "
                             f"JEDER Prozessstart jede Stufe neu.")

    @classmethod
    def geraet_text(cls):
        """Was WIRKLICH rechnet, an den gebauten Sessions abgelesen — „openvino:CPU",
        wenn wenigstens eine Stufe dort gebunden hat, sonst „cpu". Vor der ersten
        Session gibt es dazu keine Aussage; dann gilt der Wunsch."""
        return cls._geraet

    _geraet = GERAET

    def __init__(self, a):
        # Der Cache muss stehen, BEVOR die erste Session gebaut wird.
        if getattr(a, "ov_cache", None):
            os.environ[CACHE_ENV] = a.ov_cache
        _CACHE["pfad"], _CACHE["quelle"] = cache_vorbereiten()
        self.ep_ov = EP_OV in ort.get_available_providers()
        # Die Strangzahl dieses Prozesses steht im Dienst-Argument `--threads`; sie
        # ist die zweite Haelfte der Thread-Rechnung (Modulkopf). Fehlt sie (nackter
        # Lauf, Probe), gilt 1 — die vorsichtige Richtung.
        self.straenge = max(1, int(getattr(a, "threads", 1) or 1))
        self.regie = regie_setzen(self.straenge)
        _melden(f"compute cache: {_CACHE['pfad']} ({_CACHE['quelle']})")
        if self.ep_ov:
            _melden(f"computing on CPU — this is the design of the cpu image, not a "
                    f"fallback. Stages run on the OpenVINO CPU runtime "
                    f"({EP_OV}, precision {OV_PRAEZISION}); measured 3-7x faster "
                    f"than plain onnxruntime on the same CPU (field comparison "
                    f"2026-09-10).")
        else:
            _melden(f"computing on CPU — this is the design of the cpu image, not a "
                    f"fallback. No {EP_OV} in this onnxruntime build, so the stages "
                    f"run on the plain onnxruntime CPU provider. That is correct, "
                    f"just slower (measured 3-7x on the same CPU); an "
                    f"onnxruntime-openvino build would be faster.")
        # DIE VARIANTEN-FRAGE, und warum sie hier steht (.541, E4). Bis .540 starb
        # der Worker, wenn `resolve_backend` auf `cpu` fiel — und GENAU DAS war der
        # einzige Weg, auf dem ein Betreiber erfuhr, dass sein Beschleuniger nicht
        # gebunden hat (nachgestellt 17.09. am gpu-legacy-Image: Legacy-OpenCL-Treiber
        # bindet auf einer Gen12+-iGPU nicht, der Dienst meldete „ready", die Analyse
        # stand). Seit E4 rechnet dieser Fall — langsam, aber er rechnet. Das ist die
        # bessere Anlage und die schlechtere Diagnose, wenn niemand es sagt. Also wird
        # es gesagt: laut im Log UND in `bindung`, damit es in jeder Job-Antwort und
        # in /health steht. `SUSLIK_VARIANT` setzt jedes Dockerfile.
        self.variante = (os.environ.get("SUSLIK_VARIANT") or "").strip().lower()
        self.unerwartet = bool(self.variante) and self.variante != "cpu"
        if self.unerwartet:
            _melden(f"WARN: this is the {self.variante!r} image, but the analysis "
                    f"resolved to the CPU — the accelerator did not bind. Analysis "
                    f"runs (correct values, much slower). Check that the device is "
                    f"passed into the container (/dev/dri for Intel and AMD, "
                    f"/dev/nvidia* for NVIDIA), that the image matches your hardware "
                    f"(Intel Gen8/9/11 needs the gpu-legacy image, Gen12+ the gpu "
                    f"image), and that 'backend' in your configuration names the "
                    f"accelerator. 'suslik --benchmark' inside the container shows "
                    f"what it sees.")
        os.makedirs(a.out, exist_ok=True)
        self.bestand = None

    # -------------------------------------------------- Die Schnittstelle des Kerns
    def bestand_neu(self):
        """Der Modell-Bestand — Bestands-Mechanik, eigener Session-Bauer, eigene
        Log-Kennung (sonst stuende „engine_migraphx" im Log eines cpu-Images) und
        ein schlichter `run` statt des io-bindings der AMD-Seite (s. `_run`)."""
        return em.ModellBestand(_sitzung, _melden, _run)

    def bindung_ergaenzen(self, bindung):
        """Was NUR diese Engine weiss, in die Bindung des Dienstes. In place.

        CPU IST HIER DAS SOLL, nicht der Notnagel: `gebunden` bleibt True, es gibt
        keinen Fehlzustand zu melden. Praezisiert wird allein das GERAET — welcher
        Rechen-Stack die Stufen wirklich gefuehrt hat. Zum Zeitpunkt dieses Aufrufs
        steht noch keine Session (die Stufen entstehen faul, beim ersten Job), also
        wird der WUNSCH gemeldet und spaeter aus den Berichten praezisiert."""
        Engine._geraet = f"openvino:{OV_GERAET}" if self.ep_ov else "cpu"
        bindung["gebunden"] = True
        bindung["geraet"] = Engine._geraet
        if self.unerwartet:
            # KEIN „by design" auf einer GPU-Variante: dort IST die CPU ein Befund.
            bindung["gebunden"] = False
            bindung["grund"] = (f"the {self.variante} image resolved to the CPU — the "
                                f"accelerator did not bind; analysis runs, much slower")
        else:
            bindung["grund"] = ("CPU by design (this image computes on the CPU)"
                                if self.ep_ov else
                                "CPU by design (this image computes on the CPU); no "
                                "OpenVINO CPU runtime in this build — correct, slower")
        bindung["variante"] = self.variante or None
        return bindung

    def frames(self, clip, W, H, schritt, wache=None):
        return frames_nv12(clip, W, H, schritt, wache=wache)

    def bild_stufen(self):
        """Der BILD-Weg dieser Engine, einmal je Prozess. -> BildStufen"""
        if getattr(self, "_bild", None) is None:
            self._bild = BildStufen(self)
        return self._bild

    def geometrie_bauen(self, geo):
        """Je Clip-Geometrie einmal die Sessions. -> {(W, H): Geometrie}

        Wie auf rocm ist das NUR der Detektor: alles andere haengt an den
        Modell-Dateien, nicht am Frame (`engine_migraphx.ModellBestand`)."""
        if self.bestand is None:
            self.bestand = self.bestand_neu()
        graphen = {}
        for W, H, _fps in geo.values():
            if (W, H) not in graphen:
                graphen[(W, H)] = em.Geometrie(W, H, self.bestand)
        return graphen

    def kopf_auskunft(self, graphen):
        """Was WIRKLICH gebaut und gebunden wurde — an den Objekten abgelesen, nicht
        aus den Wuenschen. Das wichtigste Feld ist hier der STACK je Stufe: ob eine
        Stufe auf der OpenVINO-CPU-Laufzeit lief oder auf dem nackten CPU-EP, ist
        der Unterschied, den der Feldvergleich mit 3-7x beziffert hat."""
        g0 = next(iter(graphen.values()))
        best = self.bestand
        stand = {m: b.get("stand") for m, b in sorted(best.bindung.items())}
        # Praezisieren, sobald es Sessions gibt: gemessen statt gewuenscht.
        if stand:
            Engine._geraet = (f"openvino:{OV_GERAET}"
                              if any(s == "openvino" for s in stand.values()) else "cpu")
        return {"provider": EP_OV if self.ep_ov else EP_CPU, "ort": ort.__version__,
                "ep_openvino": self.ep_ov, "geraet": Engine.geraet_text(),
                "bindung": {m: dict(b) for m, b in sorted(best.bindung.items())},
                "bindung_kurz": stand,
                "auf_openvino": sorted(m for m, s in stand.items() if s == "openvino"),
                "auf_cpu_ep": sorted(m for m, s in stand.items() if s == "cpu"),
                "precision": OV_PRAEZISION if self.ep_ov else "fp32 (model files)",
                "compute_cache": _CACHE["pfad"],
                "compute_cache_quelle": _CACHE["quelle"],
                "threads": dict(self.regie or {}),
                "sessions": best.sessions_zaehlen(),
                "bau_s": round(best.bau_s, 1),
                "breite_video": em.BREITE_VIDEO, "breite_bild": em.BREITE_BILD,
                "det_onnx": g0.det_pfad,
                "modell_pfade": {k: best.pfade[k] for k in sorted(best.pfade)},
                "modell_typen": {k: em.ec._typ_name(t)
                                 for k, t in sorted(best.typ.items())},
                "zuschnitt": {"wo": "cpu (cv2.warpAffine, Bild-Weg-Muster)",
                              "grund": "kein Beschleuniger, auf dem ein GridSample "
                                       "billiger waere als warpAffine"},
                "laplace": "cpu (cv2.Laplacian auf der Leinwand des Kerns)",
                "decode": {"kette": "software (no VAAPI attempt — this image ships "
                                    "no VAAPI driver)",
                           "byte_gleichheit": "Software-Decode IST die Seite, gegen "
                                              "die am 04.08.2026 gemessen wurde"},
                "fd": {"breite": em.BREITE_VIDEO, "punkte_im_ausgang": best.lm_gesamt}}
