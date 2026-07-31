# core/registry.py — DIE eine Quelle fuer Backend-, Geraete-, Varianten- und Encoder-Mengen.
# Paket 3 / P3.1 (qs_ebenen.md §3, 31.07.2026).
#
# Entstanden aus dem rocm-Fall: dieselben Mengen lagen als Literale an 50 Stellen
# (Inventur wf_8003d901); eine Erweiterung erreichte nie alle (Klasse K3). Regeln:
#   - NUR Standardbibliothek importieren (H29; die Registry-Selbsttest-Stufe erzwingt es) —
#     alle Ebenen (verifyd, face_audit, abnahme, tools, qs.sh via python3 -c) muessen sie
#     ohne Nebenwirkungen laden koennen. Import-Richtung: alle -> registry, NIE zurueck.
#   - Zwei Achsen (Plan-QS MUSS 3): BACKENDS traegt, was je kind EINDEUTIG ist;
#     DEVICES traegt die Geraete je kind (openvino hat GPU+NPU+MIXED — ein Knoten/Label
#     je kind kann die Realitaet nicht abbilden).
#   - Provenienz je Fremdhardware-WERT (SOLL 18): beleg = "unbelegt" ODER "quelle JJJJ-MM-TT".
#     Unbelegte Werte erscheinen in der Grenzen-Ausgabe des Gates (SD3-Vorgriff).
#   - Reihenfolge ist Semantik, wo sie als Liste steht (KENNUNG_PRIORITAET, TAG_SUFFIXE).

# ---------------------------------------------------------------- Backends (kinds)
# wizard_werte = die Beitraege des kinds zur Wizard-Whitelist (ALLOWED_BK) in der
# historisch gewachsenen, byte-genauen Schreibweise (Config-Werte, nie umformatieren).
BACKENDS = {
    "cpu": {
        "aliase": ("cpu",),
        "ep": "CPUExecutionProvider",
        "wizard_werte": ("cpu",),
        "beleg": {"ep": "eigene Anlage 2026-07-22"},
    },
    "openvino": {
        "aliase": ("openvino", "ov"),
        "ep": "OpenVINOExecutionProvider",
        "wizard_werte": ("openvino:GPU", "openvino:NPU", "openvino:MIXED"),
        "beleg": {"ep": "eigene Anlage 2026-07-22"},
    },
    "cuda": {
        "aliase": ("cuda",),
        "ep": "CUDAExecutionProvider",
        "wizard_werte": ("cuda",),
        "beleg": {"ep": "CUDA-NB RTX2060 2026-07-30"},
    },
    "migraphx": {
        "aliase": ("migraphx", "rocm"),
        "ep": "MIGraphXExecutionProvider",
        "wizard_werte": ("migraphx",),
        "beleg": {"ep": "unbelegt"},   # EP-Praesenz belegt (Tester-Log 2026-07-30), BIND unbelegt
    },
}

# Bekannte OpenVINO-Device-Kurzformen der alten OV_DEVICE-Welt (resolve_backend-
# Abwaertskompatibilitaet; Verhalten wortgleich uebernommen, Charakterisierungs-Vektoren
# in qs.sh sichern die Semantik).
OV_DEVS = ("GPU", "NPU", "MIXED", "AUTO")

# ---------------------------------------------------------------- Geraete je kind
# knoten = Pflicht-Geraeteknoten-Muster (None = keine Vorbedingung pruefbar).
# MIXED ist UNSER Untermodus (detector=GPU, recognition=NPU), kein OpenVINO-Device —
# er erreicht die Knoten-Vorpruefung nie als Einzel-Device (face_audit verteilt).
DEVICES = {
    "cpu": (),
    "openvino": (
        {"name": "GPU", "knoten": "/dev/dri/renderD*", "benchmark_label": "iGPU (OpenVINO)",
         "default": True, "beleg": {"knoten": "eigene Anlage 2026-07-22"}},
        {"name": "NPU", "knoten": "/dev/accel/accel*", "benchmark_label": "NPU  (OpenVINO)",
         "default": False, "beleg": {"knoten": "eigene Anlage 2026-07-22"}},
        {"name": "MIXED", "knoten": None, "benchmark_label": None,
         "default": False, "beleg": {}},
    ),
    "cuda": (
        {"name": "0", "knoten": "/dev/nvidia*", "benchmark_label": "CUDA (Nvidia)",
         "default": True, "beleg": {"knoten": "CUDA-NB 2026-07-31 (Widerleger-Nachzug)"}},
    ),
    "migraphx": (
        {"name": "0", "knoten": "/dev/kfd", "benchmark_label": "MIGraphX (AMD)",
         "default": True, "beleg": {"knoten": "unbelegt"}},
    ),
}

# Zusatz-Knoten fuer die Geraeteknoten-Hilfe (geraete_knoten_muster-Basislookup):
# Schluessel, die KEIN kind sind, sondern Device-/Familien-Namen.
KNOTEN_BASIS = {
    "GPU": "/dev/dri/renderD*",
    "NPU": "/dev/accel/accel*",
    "KFD": "/dev/kfd",
    "NVIDIA": "/dev/nvidia*",
}

# ---------------------------------------------------------------- Image-Varianten
# yaml_default = Rohwert aus docker/verifyd.container.*.yaml (darf 'auto' sein);
# wizard_default = der real per Wizard speicherbare Wert (Plan-QS MUSS 5: 'auto' ist
# BEWUSST nicht in der Wizard-Whitelist — auto loest sich beim Boot zu einem konkreten
# Placement auf, der Wizard bietet nur konkrete Werte an).
# encoder_erwartung: hw-wenn-geraet = mit passendem Geraet MUSS ein HW-Encoder melden,
# ohne Geraet ist libx264 korrekt (SOLL 16 — die Geraete-Tatsache wird IM Container
# gemessen, nie aus dem Tag geraten); cpu-ok = libx264 ist immer korrekt.
VARIANTEN = {
    "gpu": {
        "dockerfile": "docker/Dockerfile.gpu", "compose_test": "docker/compose.test-gpu-npu.yml",
        "container_yaml": "docker/verifyd.container.gpu.yaml",
        "yaml_default": "auto", "wizard_default": "openvino:GPU",
        "encoder_erwartung": "hw-wenn-geraet", "latest": True, "status": "stable",
        "beleg": {"betrieb": "Prod/8200 taeglich", "encoder": "eigene Anlage 2026-07-26"},
    },
    "cpu": {
        "dockerfile": "docker/Dockerfile", "compose_test": "docker/compose.test-cpu.yml",
        "container_yaml": "docker/verifyd.container.yaml",
        "yaml_default": "cpu", "wizard_default": "cpu",
        "encoder_erwartung": "cpu-ok", "latest": True, "status": "stable",
        "beleg": {"betrieb": "Sim .165 je Release"},
    },
    "cuda": {
        "dockerfile": "docker/Dockerfile.cuda", "compose_test": "docker/compose.test-cuda.yml",
        "container_yaml": "docker/verifyd.container.cuda.yaml",
        "yaml_default": "cuda", "wizard_default": "cuda",
        "encoder_erwartung": "hw-wenn-geraet", "latest": True, "status": "stable",
        "beleg": {"betrieb": "CUDA-NB 2026-07-30", "encoder": "sprior RTX3060 2026-07-30"},
    },
    "gpu-legacy": {
        "dockerfile": "docker/Dockerfile.gpu-legacy", "compose_test": None,
        "container_yaml": "docker/verifyd.container.gpu.yaml",
        "yaml_default": "auto", "wizard_default": "openvino:GPU",
        "encoder_erwartung": "hw-wenn-geraet", "latest": False, "status": "testing",
        "beleg": {"betrieb": "Gen9-Tester UHD630 2026-07-29"},
    },
    "rocm": {
        "dockerfile": "docker/Dockerfile.rocm", "compose_test": None,
        "container_yaml": "docker/verifyd.container.rocm.yaml",
        "yaml_default": "migraphx", "wizard_default": "migraphx",
        "encoder_erwartung": "hw-wenn-geraet", "latest": False, "status": "testing",
        "beleg": {"betrieb": "unbelegt", "encoder": "AMD-Tester 780M VAAPI 2026-07-30"},
    },
}

# Tag-Suffix -> Variante: LAENGSTE zuerst pruefen (SOLL 24: '…-gpu-legacy' traefe sonst
# '*-gpu*'); Konsumenten iterieren ueber TAG_SUFFIXE, nie ueber VARIANTEN-Reihenfolge.
TAG_SUFFIXE = tuple(sorted(VARIANTEN, key=len, reverse=True))

# ---------------------------------------------------------------- Encoder-Arten
# soll_marker = die Startlog-Kennung des video-Selbstchecks (byte-genau, S5/SU2-Soll).
ENCODER_ARTEN = {
    "nvenc-voll": {"soll_marker": "h264_nvenc — full-hw pipeline probe passed",
                   "beleg": "sprior RTX3060 2026-07-30"},
    "nvenc":      {"soll_marker": "h264_nvenc — encode probe passed",
                   "beleg": "CUDA-NB 2026-07-27"},
    "vaapi":      {"soll_marker": "h264_vaapi", "beleg": "eigene Anlage 2026-07-26; AMD-Tester 780M 2026-07-30"},
    "cpu":        {"soll_marker": "libx264 (CPU)", "beleg": "ueberall"},
}

# Host-Klassen fuer SD2-Erwartungen (SD2: die Klasse kommt IMMER per Deklaration von
# aussen — Gate-Flag/Tester-Angabe — nie aus der eigenen Hardware-Sonde, sonst waehlt
# der Pruefling seine eigene Erwartung).
# Merkmale (nur Doku): keine_geraete = weder /dev/dri noch /dev/accel noch /dev/nvidia*
# noch /dev/kfd · intel = /dev/dri · intel_npu = /dev/dri + /dev/accel ·
# nvidia = /dev/nvidia* · amd = /dev/kfd + /dev/dri.
HOST_KLASSEN = ("keine_geraete", "intel", "intel_npu", "nvidia", "amd")

# App-Quelldateien der Auslieferung (P3.5): DIE eine Liste — Dockerfile-COPYs und die
# source_export-Whitelist werden per Deckungs-Regel dagegen geprueft (die "Datei-Familie
# waechst, Liste nicht"-Klasse; bisher lag die Liste 7x unabhaengig herum).
APP_DATEIEN = ("verifyd.py", "analyze.py", "anlernen.py", "face_audit.py", "abnahme.py",
               "auftritte.py", "szenarien.py", "decode.py", "worker.py", "no_person.py",
               "sync_refs.py")

# abnahme.backend_kennung: PRUEFREIHENFOLGE ist Semantik (CUDA vor MIGraphX vor OpenVINO
# vor cpu-Fallthrough) und das Format ist ein DATEINAME (soll.<kennung>.json) — byte-genau,
# nie umformatieren (SOLL 15).
KENNUNG_PRIORITAET = ("cuda", "migraphx", "openvino", "cpu")
KENNUNG_FORMAT = {"cuda": "cuda", "migraphx": "migraphx",
                  "openvino": "openvino-{dev}", "cpu": "cpu"}


# Wizard-Anzeigetexte je Wert (UI englisch; zentral, damit eine neue Option nie ohne
# Label auftaucht — SK1 prueft die Deckung Label-Menge == Werte-Menge im Selbsttest).
WIZARD_LABELS = {
    "openvino:GPU": "Intel GPU (OpenVINO) — recommended",
    "openvino:NPU": "Intel NPU (OpenVINO)",
    "openvino:MIXED": "Intel GPU + NPU (MIXED)",
    "cuda": "Nvidia GPU (CUDA)",
    "migraphx": "AMD GPU (ROCm / MIGraphX)",
    "cpu": "CPU — works everywhere (universal fallback)",
}


# ---------------------------------------------------------------- Helfer
def kind_von(wert):
    """Alias -> (kind, bekannt). Unbekannte Token werden DURCHGEREICHT (bekannt=False) —
    die Laut-Warnung beim Aufrufer bleibt Semantik (resolve_backend, SOLL 23)."""
    w = (wert or "").strip().lower()
    for kind, b in BACKENDS.items():
        if w in b["aliase"]:
            return kind, True
    return w, False


def ep_von(kind):
    b = BACKENDS.get(kind)
    return b["ep"] if b else None


def geraete_von(kind):
    return DEVICES.get(kind, ())


def default_device(kind):
    for d in DEVICES.get(kind, ()):
        if d.get("default"):
            return d["name"]
    return None


def knoten_von(basis):
    """Device-/Familien-Name (GPU/GPU.0/NPU/KFD/NVIDIA) -> Knoten-Muster oder None.
    Basislookup ueber split('.') wie gehabt (GPU.1 -> GPU)."""
    b = str(basis).split(".")[0] if basis is not None else basis
    return KNOTEN_BASIS.get(b)


def wizard_optionen(verfuegbare_eps):
    """EP-Liste -> Wizard-Werte in stabiler Reihenfolge (openvino, cuda, migraphx, cpu
    zuletzt als Universal-Fallback) — speist bk_opts UND die ALLOWED_BK-Whitelist."""
    werte = []
    for kind in ("openvino", "cuda", "migraphx"):
        if BACKENDS[kind]["ep"] in (verfuegbare_eps or ()):
            werte.extend(BACKENDS[kind]["wizard_werte"])
    werte.extend(BACKENDS["cpu"]["wizard_werte"])
    return tuple(werte)


def alle_wizard_werte():
    """STATISCHE Whitelist aller je moeglichen Backend-Werte (ALLOWED_BK-Semantik:
    unabhaengig von den EPs DIESES Images — Verhalten der Vor-Registry-Zeit)."""
    werte = []
    for kind in ("openvino", "cuda", "migraphx", "cpu"):
        werte.extend(BACKENDS[kind]["wizard_werte"])
    return frozenset(werte)


def knoten_familie(kind):
    """kind -> (Familienname aus KNOTEN_BASIS, Muster) des Pflicht-Knotens des
    Default-Geraets — fuer Meldungstexte wie 'no KFD device (/dev/kfd)'."""
    devs = DEVICES.get(kind) or ()
    kn = devs[0]["knoten"] if devs else None
    for fam, m in KNOTEN_BASIS.items():
        if m == kn:
            return fam, kn
    return None, kn


def varianten_namen():
    return tuple(VARIANTEN)


def latest_varianten():
    return tuple(v for v, d in VARIANTEN.items() if d["latest"])


def variante_von_tag(tag):
    """Image-Tag/-Suffix -> Varianten-Name oder None (laengste Endung zuerst, SOLL 24)."""
    t = str(tag or "")
    for v in TAG_SUFFIXE:
        if t == v or t.endswith("-" + v):
            return v
    return None


def unbelegte_werte():
    """[(pfad, wert)] aller Provenienz-Felder mit 'unbelegt' — Grenzen-Ausgabe (SD3)."""
    aus = []
    for kind, b in BACKENDS.items():
        for feld, beleg in (b.get("beleg") or {}).items():
            if beleg == "unbelegt":
                aus.append((f"BACKENDS.{kind}.{feld}", b.get(feld)))
    for kind, devs in DEVICES.items():
        for d in devs:
            for feld, beleg in (d.get("beleg") or {}).items():
                if beleg == "unbelegt":
                    aus.append((f"DEVICES.{kind}.{d['name']}.{feld}", d.get(feld)))
    for v, d in VARIANTEN.items():
        for feld, beleg in (d.get("beleg") or {}).items():
            if beleg == "unbelegt":
                aus.append((f"VARIANTEN.{v}.{feld}", feld))
    return aus
