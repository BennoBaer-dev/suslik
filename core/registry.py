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
#   - IMPORTFREI (H29, vom Registry-Selbsttest erzwungen): auch nicht `re`. Die
#     URL-Maskierung unten ist deshalb bewusst mit reinen String-Griffen gebaut.

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
    # latest True seit 11.08. (User: "alle 5 identisch" — keine Negativ-Meldungen, und
    # ohne latest kommen keine neuen Tester). status bleibt testing, solange die Betriebs-
    # Belege duenn sind: latest folgt jedem Release, ist aber nicht von unseren
    # Testmaschinen abgedeckt — die Doku sagt das ehrlich dazu.
    "gpu-legacy": {
        "dockerfile": "docker/Dockerfile.gpu-legacy", "compose_test": None,
        "container_yaml": "docker/verifyd.container.gpu.yaml",
        "yaml_default": "auto", "wizard_default": "openvino:GPU",
        "encoder_erwartung": "hw-wenn-geraet", "latest": True, "status": "testing",
        "beleg": {"betrieb": "Gen9-Tester UHD630 2026-07-29"},
    },
    "rocm": {
        "dockerfile": "docker/Dockerfile.rocm", "compose_test": None,
        "container_yaml": "docker/verifyd.container.rocm.yaml",
        "yaml_default": "migraphx", "wizard_default": "migraphx",
        "encoder_erwartung": "hw-wenn-geraet", "latest": True, "status": "testing",
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

# ---------------------------------------------------------------- Frame-Quelle (Z7)
# EINE Stelle baut decode.FrameIter selbst: der Verteiler. Alle anderen bekommen ihre
# Frames von ihm (konzept_frames.md v2 §3.2/§7) — ein zweiter Direktzugriff waere ein
# zweiter Frame-Pfad, und ein Gate, das einen anderen Pfad prueft als den urteilenden,
# prueft nichts (Fehlerklasse R5, Begruendung im Code: abnahme.analysiere). Die
# Ausnahmen stehen HIER mit Begruendungsfeld (Muster APP_DATEIEN) und nie als
# Literalliste im Gate: eine fachliche Aufzaehlung nimmt die zentrale Quelle oder
# deklariert einen Deckungs-Vertrag (qs_ebenen.md).
FRAMEITER_VERTEILER = "core/frames.py"

# Wer decode.FrameIter weiterhin selbst bauen darf — und warum. Pfade relativ zur
# Projekt-Wurzel. Das Gate prueft die Menge in BEIDE Richtungen: ein Direktzugriff
# ausserhalb ist rot, UND eine Ausnahme ohne echten Direktzugriff ist rot (eine
# verfallene Ausnahme wuerde spaeter still einen neuen Verstoss decken).
FRAMEITER_AUSNAHMEN = {
    "anlernen.py":
        "Enrollment/Sammeln, KEIN Urteilspfad: die Vollstaendigkeits-Wache reagiert "
        "hier bewusst nicht (frame_iter-Docstring) — ein Teil-Clip liefert eben "
        "weniger Kandidaten, nie ein falsches Urteil. konzept_frames.md v2 Z7 fuehrt "
        "anlernen.py ausdruecklich als die einzige verbleibende Ausnahme.",
    "prototyp/norm_vorrat.py":
        "MESSWERKBANK des Lernvorrats (bauplan_vorrat.md, 20.08.), KEIN Urteilspfad: "
        "sie nutzt decode.FrameIter BEWUSST direkt — der gepinnte Pixelpfad ohne "
        "Verteiler-Mantel ist hier die Messbedingung (die Zahlen muessen mit der "
        "Knecht-Container-Umgebung bit-vergleichbar bleiben, Parallel-Validierung "
        "20.08.: 0 Abweichungen). Laeuft nie automatisch, liegt nicht im Image "
        "(prototyp/ wird nur fuer personlern gestaged, norm_vorrat gehoert nicht dazu).",
    "prototyp/frame_vergleich.py":
        "Prototyp (E-P1b Frame-Vergleich, 03.08.), KEIN Urteilspfad: der Direktzugriff "
        "sitzt in event_verarbeiten(), und das ruft nur main() dieses Werkzeugs. Der "
        "Koerper-Strang importiert aus dem Modul ausschliesslich die drei reinen Helfer "
        "bewegungs_box/schaerfe/clip_laden (pfad_snapshots.py) — keiner davon dekodiert. "
        "Ehrlich dazu: die Datei liegt sehr wohl im Image (tools/personlern_stage.sh "
        "staged sie nach docker/personlern_stage/), nur laeuft sie dort kein Urteil. "
        "Seit Z2 kommt ihr CLIP-Bezug ohnehin aus core.frames (ein Download je Event). "
        "Z7 laesst Deklaration ODER Umbau zu; deklariert, weil der Umbau Code aenderte, "
        "den kein Urteil liest — der kleinere Eingriff bei gleicher Aussage.",
}

# Ordner ausserhalb des Pruefbestands, je mit Grund. Ohne diese Deklaration liefe das
# Inventar ueber Fremd-Code und ueber die Beweis-Staende, die den alten Weg mit ABSICHT
# festhalten. Das Gate ueberspringt zusaetzlich Punkt-Ordner (Repo-/Werkzeug-Innereien).
FRAMEITER_INVENTAR_AUS = {
    "venv": "fremde Bibliotheken, nicht unser Auslieferungs-Code",
    "scratchpad": "Beweis-/Vergleichsstaende — sie halten den ALTEN Frame-Weg mit "
                  "Absicht fest und fahren ihn gegen den neuen (beweis_z4/z6/z7)",
    "prototyp/modelle": "eingelagerter Fremd-Quelltext (DINOv3-Repo) — nicht unser Code",
    "docker/personlern_stage": "ERZEUGTE Kopie (tools/personlern_stage.sh sed-t "
                               "prototyp/*.py vor jedem Bau) — eine Aenderung hier "
                               "waere beim naechsten Bau weg. Geprueft wird die "
                               "Quelle prototyp/, aus der sie Zeile fuer Zeile faellt",
    "verify_data": "Betriebsdaten, kein Code",
    "samples": "Testmaterial, kein Code",
    "node_modules": "Fremd-Pakete",
    "__pycache__": "Bytecode",
}

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


# --- Config-Export-Vertrag (User-Fund 02.08.: NB-Restore ohne Frigate) --------------
# Der Config-Download (/config_sichern) exportierte NUR den UI-Store. Auf ENV-/yaml-
# konfigurierten Installationen (Prod!) stehen die Verbindungs-Werte aber nie im Store —
# das Backup war fuer sie unvollstaendig, ein Restore anderswo liess Frigate/MQTT leer.
# VERTRAG: Schluessel + Nicht-Export-Defaults hier zentral; Export ergaenzt den Store um
# die WIRKSAMEN Werte, wenn sie fehlen und vom Default abweichen. Store-Werte gewinnen.
EXPORT_VERBINDUNG = {"frigate_url": "", "trigger": "poll", "mqtt": {}}


def export_ergaenzen(store, cfg):
    """Export-Inhalt des Config-Downloads: Store + wirksame Verbindungs-Werte (reine Logik)."""
    d = dict(store)
    for key, default in EXPORT_VERBINDUNG.items():
        wert = cfg.get(key)
        if key not in d and wert not in (None, "", {}) and wert != default:
            d[key] = wert
    return d


# --- Herkunft einer Meldung (0.1.0.163, User-Wunsch 09.08.) --------------------------
# Anlass: die Nachanalyse eines Durchgangs von GESTERN loeste eine Telegram-Meldung
# aus, als stuende die Person gerade vor der Tuer (Live-Bug 09.08. 08:19). Die Ursache
# ist gefixt und die Nachanalyse schweigt (core/personlive `still`). Das hier ist die
# ZWEITE Verteidigungslinie: jede Meldung, die NICHT aus dem Live-Betrieb kommt, traegt
# ihre Herkunft im Text — dann ist ein Fehl-Versand am Handy sofort als Nicht-Ereignis
# lesbar, statt fuer bare Muenze genommen zu werden. Und die GEWOLLTEN Nicht-Live-
# Sendungen (Kanal-Test-Knopf, manuell ausgeloester Lauf) sind endlich ehrlich
# beschriftet, statt sich als Vorfall auszugeben.
#
# EINE Quelle: Werte-Menge und Praefixe stehen nur hier. Der Versandweg reicht genau
# EINEN Parameter durch (`herkunft`), Vorgabe `live`; wer aus Test- oder
# Nachanalyse-Kontext sendet, setzt ihn ausdruecklich.
MELDE_HERKUNFT = {
    # Wert          Praefix im Meldetext (leer = keine Markierung)
    "live": "",                       # echter Vorfall im Betrieb
    "manuell": "[test] ",             # Kanal-Test, manuell ausgeloester Lauf
    "nachanalyse": "[re-analysis] ",  # erneute Analyse eines vergangenen Durchgangs
    # Live-Waechter-Engine (live_reiter_bauplan.md §6, K3-Loch-Fix: der Wert
    # fiel vorher still auf "live" zurueck und markierte nichts). Ein Trigger
    # der Engine ist ein ECHTES Live-Ereignis — der TEXT traegt deshalb keine
    # Marke; die Waechter-Kennung sitzt im Meldungs-TITEL (EIN Literal,
    # core/livewache.WATCHER_TITEL: "Live watcher <kamera>: ..."), und das
    # MQTT-Payload-Feld `herkunft` traegt diesen Wert, damit Home Assistant
    # Waechter-Meldungen filtern kann, ohne Meldetexte zu zerlegen.
    "live_wache": "",
}
MELDE_HERKUNFT_STD = "live"


def melde_praefix(herkunft=None):
    """Das Text-Praefix zu einer Herkunft. Unbekannte oder fehlende Herkunft gilt als
    `live` und markiert nichts — eine erfundene Marke waere schlimmer als keine."""
    return MELDE_HERKUNFT.get(herkunft or MELDE_HERKUNFT_STD, "")


def melde_text(text, herkunft=None):
    """Meldetext mit Herkunfts-Marke. Idempotent: ein Text, der die Marke schon
    traegt, bekommt sie nicht zweimal (der Weg fuehrt an zwei Stellen vorbei —
    Pushover-Titel/Text und Telegram-Caption)."""
    p = melde_praefix(herkunft)
    t = str(text or "")
    return t if not p or t.startswith(p) else p + t


# --- Kachel-Zustaende des Live-Reiters (live_reiter_bauplan.md §2.3, Phase 2) -------
# Die EINE Quelle fuer Kachel-Farbe, Kachel-Text und /health (K3-Regel: nie als
# Streu-Literal in Kachel-HTML, Engine und health getrennt gepflegt). ABGELEITET
# wird der Zustand ausschliesslich in core.livewache.ui_zustand() aus Config +
# Engine-QUITTUNG (Status-Datei) — K1 in BEIDE Richtungen: eine Kachel behauptet
# nie einen Zustand, den die Engine nicht quittiert hat, und ein blosser
# Config-Wunsch (enabled=true im Store) wird nie als 'active' gerendert.
# BEWUSST GETRENNT von den Engine-LAUFZEIT-Zustaenden (livewache.KACHEL_ZUSTAENDE,
# startet/aktiv/gestoert/...): die beschreiben den Thread im Engine-Prozess,
# diese hier die Kachel im UI (Config + Test + Quittung zusammen).
# farbe = CSS-Klasse lv-<farbe> in webui/style.css (eine Klasse je Farbwort).
LIVE_ZUSTAENDE = {
    "unconfigured": {"farbe": "grau",    "label": "Not configured"},
    "untested":     {"farbe": "gelb",    "label": "Configured — test required"},
    # .362 (Konzept-QS 28.08.): enabled, aber der Quelltest laeuft noch/neu —
    # der Selbstheilungs-Zustand des .361-Enables, vorher zeigte die Kachel
    # hier faelschlich 'test required', waehrend der Test schon lief.
    "checking":     {"farbe": "gelb",    "label": "Checking source"},
    "tested":       {"farbe": "blau",    "label": "Tested — ready to enable"},
    "active":       {"farbe": "gruen",   "label": "Active"},
    "disturbed":    {"farbe": "rot",     "label": "Disturbed"},
    "unsupported":  {"farbe": "neutral", "label": "Not available on this build"},
}

# DER eine Kachel-Zustand, der "dieser Waechter laeuft gerade" bedeutet.
# Er steht hier bei den Zustaenden selbst, weil ihn inzwischen ZWEI Stellen
# brauchen: die Systemseite zaehlt damit die aktiven Waechter, und seit .407
# entscheidet verifyd.process() daran, ob der Live-Waechter einer Kamera die
# Ereignis-Analyse wirklich ersetzen darf. Ein zweites Literal an einer der
# beiden Stellen waere die K3-Klasse (eine Umbenennung hier wuerde dort still
# zu "nie aktiv" und damit zu einem stummen Ausfall des Schalters).
LIVE_AKTIV = "active"


# --- Support-Zugriff (analysen/support_api.md, 28.08.2026) --------------------------
# DIE eine Bereichs-Quelle (QS-Ebenen-Regel: kein Streu-Literal): Inventar,
# Handler (core/support.py), Doku-Deckung und QS-Stufe lesen ALLE von hier.
# Nur Daten (Registry-Kopfvertrag: importfrei) — Wurzeln als Pfad-Tupel
# relativ zu data_dir, Regex als String. HARTE Regel fuer die BENANNTEN
# tar-Bereiche (Widerleger 18/36): config/, clips/, events/, live/ duerfen
# dort NIE als Wurzel auftauchen (config/ traegt unmaskierte Alt-Store-
# Kopien; der Rest sind Rohdaten-Riesen) — die QS-Stufe prueft das gegen
# diese Tabelle.
# .380 (User-Entscheid 31.08.): dazu kommt EIN Bereich der Art "baum" —
# Vollzugriff auf den ganzen Datenordner, read-only. Anlass war der
# Feld-Fall vom 31.08.: der Unbekannt-Pool eines Testers lag unter learn/
# und war per Support-API nicht abziehbar, weil kein Bereich ihn nannte.
# Ein Vollbaum-Bereich macht jede kuenftige Ablage ohne Tabellen-Pflege
# erreichbar; die Secrets bleiben trotzdem drin, weil alles unter
# SUPPORT_MASKE_ORDNER nur MASKIERT ausgeliefert wird (core/support).
SUPPORT_BEREICHE = {
    "inventar":   {"art": "json", "text": "what is available (sizes, runs)"},
    "config":     {"art": "json",
                   "text": "masked config export — secrets are replaced by "
                           "***, plain-text values never leave the machine"},
    "logs":       {"art": "tar", "wurzel": ("logs",),
                   "text": "current + rotated service logs"},
    "faces":      {"art": "tar", "wurzel": ("faces",),
                   "text": "reference face images of the people you taught "
                           "this system — personal data, hand out with care"},
    "lauf":       {"art": "tar", "wurzel": ("state", "lernlauf"),
                   "je_lauf": True,
                   "text": "one learning run (crops are face images)"},
    "personlern": {"art": "tar", "wurzel": ("personlern",),
                   "ausschluss": ("werkstatt",),
                   "text": "body-recognition material (body images of "
                           "known people)"},
    "state":      {"art": "tar", "wurzel": ("state",),
                   "dateien": ("deckung.jsonl", "lernlauf.json",
                               "anker.jsonl", "startup.json",
                               "rechenprobe.json", "wanduhr.json",
                               "live_status.json", "systemstat.jsonl"),
                   "text": "per-event results + service state files "
                           "(diagnosis core)"},
    # .408 (Anwesenheits-Marken, M2): der "state"-Bereich ist eine DATEI-
    # Whitelist — ein Ordner darin ergaebe einen leeren Abzug. Deshalb ein
    # eigener Bereich mit Ordner-Walk (kein "dateien"). Text im Wortlaut des
    # faces-Eintrags: die Marken sind ein Bewegungsprofil (wer wann wo war).
    "anwesenheit": {"art": "tar", "wurzel": ("state", "anwesenheit"),
                    "text": "presence marks (who was confirmed where, per "
                            "quarter hour) — personal data, hand out with care"},
    "data":       {"art": "baum", "wurzel": (),
                   "text": "the whole data folder, read-only: "
                           "/support/data lists every file (path, size, "
                           "time — no content), /support/data/<path> "
                           "fetches one file or one folder (as tar.gz); "
                           "anything under config/ is served masked only"},
}
# Ordner unter data_dir, deren Dateien NUR MASKIERT hinausgehen (der
# Vollbaum-Bereich erreicht auch config/, und dort liegen neben config.json
# die Alt-Store-Kopien config.json.vor_* — dieselben Secrets, anderer Name;
# eine Namensliste waere hier die falsche Wache, deshalb der ganze Ordner).
SUPPORT_MASKE_ORDNER = ("config",)
# Muster-Maskierung des Config-Exports (Widerleger 1: eine Feldnamen-
# Heuristik statt einer pflegebeduerftigen Streu-Liste; zu viel maskieren
# ist die sichere Richtung). Ein Feld wird maskiert, wenn sein Name eines
# dieser Woerter enthaelt (case-insensitiv).
SUPPORT_SECRET_MUSTER = ("token", "password", "passwort", "key", "secret",
                         "webhook", "user")


# --- Secret-Vertrag Vision (konzept_vision.md §9 + E8, Zug V1) ----------------------
# ZWEI Geheimnis-Traeger, nicht einer: das Key-Feld UND die Endpunkt-URL. Eine
# Adresse kann Zugangsdaten VOR dem Hostnamen tragen oder als Abfrage-Parameter
# anhaengen; beides ist derselbe Wert wie im Key-Feld und erscheint an MEHR
# Stellen — Status, Export, Log, Fehlermeldung. (Das woertliche Muster steht
# hier bewusst NICHT: das Datenschutz-Gate sucht im Image genau danach, und ein
# Kommentar, der es zitiert, macht das Gate blind fuer den echten Fall —
# .167, Befund aus dem Audit am .166-Image.) Deshalb hier EINE Feldliste
# statt verstreuter Literale (Muster EXPORT_VERBINDUNG); Anzeige/Status/Log/Fehler
# nehmen sie, das Gate prueft gegen sie.
#
# E8 (User-Entscheid 08.08.): der Key wird MITGENOMMEN wie die anderen
# Meldekanal-Secrets — Restore/Umzug bleiben heil, dafuer ist er in
# /config_sichern + /backup_voll enthalten. Das ist DEKLARIERT
# (VISION_EXPORT_HINWEIS steht als Karten-Text an beiden Download-Knoepfen) und
# die qs-Stufe "Key-Austritt" prueft genau diese Trennung: ueberall ROT, nur in
# Export/Backup erlaubt.
VISION_STORE_KEY = "vision"                 # Top-Level-Block im Config-Store
VISION_SECRET_FELDER = ("api_key",)         # Klartext-Geheimnis, nie rendern
VISION_URL_FELDER = ("endpunkt",)           # zweiter Key-Traeger -> endpunkt_anzeige
# Query-Parameter, die in einer URL ein Geheimnis tragen (klein geschrieben; der
# Ersetzer arbeitet case-insensitiv).
SECRET_QUERY_PARAM = ("key", "api_key", "api-key", "token", "access_token")
# Sprach-Stufe 2 Tranche D (3a): die UI-ANZEIGE laeuft ueber den Schluessel
# system.backup.hinweis (core/texte, uebersetzbar); diese Konstante bleibt
# die englische Referenz-Quelle — das Gate prueft die Wortgleichheit
# en.T["system.backup.hinweis"] == VISION_EXPORT_HINWEIS (kein Zweit-Literal).
VISION_EXPORT_HINWEIS = ("contains your API keys — treat this file like a password")

# --- Messwerte-Registry Vision (konzept_vision.md v2 §5, Zug V2) --------------------
# "Die Werte kommen aus EINER zentralen Messwerte-Registry (qs_ebenen-Regel), nie als
# Streu-Literal ins UI." Die Modell-Auswahl der Config-Seite markiert damit jedes
# Modell, das wir REAL vermessen haben; alles andere heisst "untested here" — ohne
# behauptete Zahl, ohne Empfehlung.
#
# ZWEI GETRENNTE FAEHIGKEITEN, nie zu einer Note verrechnet (§5, Messbefund 08.08.):
#   erkennen  "residents identified" — Zwangswahl zwischen zwei bekannten Personen.
#             Die Guenstig-Klasse schafft das ueberall (72/72).
#   abweisen  "strangers rejected"   — derselbe Aufbau mit einem FREMDEN als Kandidat,
#             Sollantwort NEITHER. Genau hier fallen die Klassen auseinander.
# Deshalb steht an jeder Kachel eine DOPPEL-Angabe. Wer nur eine Zahl zeigt, verspricht
# eine Faehigkeit, die das Modell nachweislich nicht hat.
#
# HAKEN-REGEL (nachrechenbar, damit "✓" nie Geschmackssache ist):
#   ✓  jedes gemessene Urteil dieser Art war richtig (Quote == 1,0)
#   ✗  mindestens ein gemessenes Urteil war falsch
#   —  ungemessen (dann steht auch keine Zahl da)
# Der Bruch steht IMMER daneben — der Haken ist Abkuerzung, nie die ganze Aussage.
#
# SCHLUESSEL ist `<modell>|<kachel>`: dasselbe Modell verhaelt sich auf zwei
# Plattformen messbar verschieden (Qwen3.5-9B lokal gegen denselben Namen bei einem
# externen Anbieter), ein Modellname allein waere also eine falsche Zusage.
# `roh_archiviert=False` heisst: die Zahl stammt aus einem Lauf OHNE archiviertes
# Roh-JSON (Praezedenz §2.5) — sie wird gezeigt, aber als nicht nachpruefbar markiert.
VISION_MESSWERTE_STAND = "2026-08-08"
# METHODIK: welcher Weg hat die Zahl erzeugt? Die Angabe ist Pflicht, weil zwei
# Messreihen mit UNTERSCHIEDLICHER Methodik nebeneinanderliegen und ihre Zahlen
# nicht vergleichbar sind. Die aeltere wird NICHT geloescht — sie ist die grosse
# Stichprobe (36 Fremd-Paare je Modell) und bleibt die Grundlage der Badges; die
# neue faehrt die heutige Produkt-Methodik, ist aber klein (3 Fremd-Paare).
METHODIK_EINZELBILD = "single image per judgement (method up to 0.1.0.159)"
METHODIK_GITTER = "candidate grid: the whole walk-through as ONE picture (method since 0.1.0.160)"

VISION_MESSWERTE = {
    "gemini-3.5-flash-lite|gemini": {
        "erkennen": (72, 72), "abweisen": (11, 36), "datum": "2026-08-08",
        "quelle": "scratchpad/gemini_sym_reihe.json", "roh_archiviert": True,
        "methodik": METHODIK_EINZELBILD,
        "notiz": "identifies residents reliably, lets most strangers through",
        "gitter": {
            "erkennen": (8, 8), "abweisen": (0, 3), "konsistent_falsch": 1,
            "datum": "2026-08-09", "methodik": METHODIK_GITTER,
            "quelle": "scratchpad/leiter_gitter_matrix.json",
            "roh_archiviert": True, "offen": 1,
            "unvollstaendig": "1 of 12 pairs never completed",
        },
    },
    "gemini-3.5-flash|gemini": {
        "erkennen": None, "abweisen": (22, 22), "datum": "2026-08-08",
        "quelle": "scratchpad/gemini_sym_reihe.json", "roh_archiviert": True,
        "methodik": METHODIK_EINZELBILD,
        "unvollstaendig": ("stopped by the free-tier quota after 22 of 36 stranger "
                           "runs — the remaining 14 were never asked"),
        "notiz": "no stranger got through in the runs that finished",
        "gitter": {
            "erkennen": (7, 7), "abweisen": (0, 1), "konsistent_falsch": 0,
            "datum": "2026-08-09", "methodik": METHODIK_GITTER,
            "quelle": "scratchpad/leiter_gitter_matrix.json",
            "roh_archiviert": True, "offen": 4,
            "unvollstaendig": ("the free-tier quota stopped it again: 4 of 12 "
                               "pairs never completed"),
        },
    },
    "gpt-5.4-mini|gpt": {
        "erkennen": (72, 72), "abweisen": (2, 36), "datum": "2026-08-08",
        "quelle": "scratchpad/openai_sym_reihe.json", "roh_archiviert": True,
        "methodik": METHODIK_EINZELBILD,
        "notiz": "identifies residents reliably, almost never rejects a stranger",
        "gitter": {
            "erkennen": (9, 9), "abweisen": (1, 3), "konsistent_falsch": 0,
            "datum": "2026-08-09", "methodik": METHODIK_GITTER,
            "quelle": "scratchpad/leiter_gitter_matrix.json",
            "roh_archiviert": True, "offen": 0,
        },
    },
    "gpt-5.4|gpt": {
        "erkennen": None, "abweisen": (16, 36), "datum": "2026-08-08",
        "quelle": "scratchpad/openai_sym_reihe.json", "roh_archiviert": True,
        "methodik": METHODIK_EINZELBILD,
        "notiz": "rejects about half the strangers",
        "gitter": {
            "erkennen": (9, 9), "abweisen": (1, 3), "konsistent_falsch": 1,
            "datum": "2026-08-09", "methodik": METHODIK_GITTER,
            "quelle": "scratchpad/leiter_gitter_matrix.json",
            "roh_archiviert": True, "offen": 0,
        },
    },
    "claude-sonnet-5|anthropic": {
        "erkennen": None, "abweisen": (21, 36), "datum": "2026-08-08",
        "quelle": "scratchpad/anthropic_fremd_reihe.json", "roh_archiviert": True,
        "methodik": METHODIK_EINZELBILD,
        "notiz": "rejects about half the strangers",
        "gitter": {
            "erkennen": (9, 9), "abweisen": (2, 3), "konsistent_falsch": 0,
            "datum": "2026-08-09", "methodik": METHODIK_GITTER,
            "quelle": "scratchpad/leiter_gitter_matrix.json",
            "roh_archiviert": True, "offen": 0,
        },
    },
    "claude-haiku-4-5|anthropic": {
        # NUR mit der Gitter-Methodik gemessen — die aeltere Reihe kannte dieses
        # Modell nicht, deshalb steht oben nichts.
        "erkennen": None, "abweisen": None, "datum": "2026-08-09",
        "quelle": "scratchpad/leiter_gitter_matrix.json", "roh_archiviert": True,
        "methodik": METHODIK_GITTER,
        "notiz": "only measured with the candidate-grid method",
        "gitter": {
            "erkennen": (8, 9), "abweisen": (1, 3), "konsistent_falsch": 1,
            "datum": "2026-08-09", "methodik": METHODIK_GITTER,
            "quelle": "scratchpad/leiter_gitter_matrix.json",
            "roh_archiviert": True, "offen": 0,
        },
    },
    "claude-opus-5|anthropic": {
        "erkennen": None, "abweisen": (29, 29), "datum": "2026-08-08",
        "quelle": "stand.md 2026-08-08 (run over Claude-Code sub-agents)",
        "roh_archiviert": False,
        "methodik": METHODIK_EINZELBILD,
        "notiz": "rejected every stranger it was shown — but see the note on the source",
    },
    "Qwen/Qwen3.5-9B|custom": {
        "erkennen": (72, 72), "abweisen": (9, 36), "datum": "2026-08-08",
        "quelle": "scratchpad/ionos_sym_reihe.json", "roh_archiviert": True,
        "methodik": METHODIK_EINZELBILD,
        "notiz": "measured through an external OpenAI-compatible service",
    },
    "Qwen/Qwen3.5-9B|lokal": {
        "erkennen": (12, 12), "abweisen": None, "datum": "2026-08-07",
        "quelle": ("scratchpad/llamacpp_hm91_test.json, "
                   "scratchpad/llamacpp_tempo_test.json"),
        "roh_archiviert": True,
        "methodik": METHODIK_EINZELBILD,
        "notiz": ("run on a machine of our own (llama.cpp, Q8_0); strangers were "
                  "never part of that set"),
    },
    "Qwen/Qwen3.5-4B|lokal": {
        "erkennen": (12, 12), "abweisen": None, "datum": "2026-08-08",
        "quelle": "scratchpad/llamacpp_4b_test.json", "roh_archiviert": True,
        "methodik": METHODIK_EINZELBILD,
        "notiz": ("same result as the 9B on the same material, at about half the "
                  "working set; strangers were never part of that set"),
    },
}


def vision_messung(modell, kachel=None):
    """(eintrag, exakt) fuer ein Modell. `exakt` False heisst: gemessen wurde
    dasselbe Modell auf einer ANDEREN Plattform — die Zahl wird gezeigt, aber als
    fremde Plattform gekennzeichnet (dasselbe Gewicht laeuft je nach Server
    messbar anders). Kein Treffer -> (None, False)."""
    m = str(modell or "").strip()
    if not m:
        return None, False
    if kachel:
        e = VISION_MESSWERTE.get(f"{m}|{kachel}")
        if e:
            return e, True
    for schluessel, e in VISION_MESSWERTE.items():
        if schluessel.split("|", 1)[0] == m:
            return e, False
    return None, False


def vision_badge(modell, kachel=None):
    """Die Anzeige-Form eines Messwerts fuer die Modell-Karte — EINE Quelle fuer
    Seite, Wizard und Gate. Immer beide Faehigkeiten, immer mit Bruch."""
    e, exakt = vision_messung(modell, kachel)
    if not e:
        return {"gemessen": False, "text": "untested here", "erkennen": "—",
                "abweisen": "—", "exakt": False, "quelle": "", "datum": "",
                "roh_archiviert": True, "notiz": "", "unvollstaendig": ""}

    def _teil(w):
        if not w:
            return "—", ""
        ok, n = w
        return ("✓" if ok == n else "✗"), f"{ok}/{n}"

    ze, be = _teil(e.get("erkennen"))
    za, ba = _teil(e.get("abweisen"))
    text = (f"residents {ze}{(' ' + be) if be else ''} · "
            f"strangers {za}{(' ' + ba) if ba else ''}")
    return {"gemessen": True, "text": text, "erkennen": ze, "abweisen": za,
            "erkennen_bruch": be, "abweisen_bruch": ba, "exakt": exakt,
            "quelle": e.get("quelle", ""), "datum": e.get("datum", ""),
            "roh_archiviert": bool(e.get("roh_archiviert", True)),
            "notiz": e.get("notiz", ""),
            "unvollstaendig": e.get("unvollstaendig", "")}


# --- Klassen-Anker je Anbieter (0.1.0.168) ------------------------------------------
# Die Frage, die ein Nutzer wirklich hat: "welches Modell muss ich mindestens
# nehmen?". Sie laesst sich aus den Bruechen allein nicht ablesen, weil die
# Gitter-Reihe klein ist — deshalb steht hier je Anbieter EIN Anker, und er sagt
# dazu, worauf er beruht. Das ist eine EINSCHAETZUNG aus der Messung, kein
# Messwert; der Ton bleibt Bericht, nie Vorschrift ("from X" statt "use X").
#
# KEINE PREISE, KEINE KOSTEN (User-Entscheid 09.08., ausdruecklich): das Produkt
# — weder gerendert noch als stille Daten.
# nennt keine Betraege. Preise veralten, haengen an Tarif und Region, und eine
# Zahl im Code waere eine Zusage, die niemand halten kann. Wer das wissen will,
# liest die Seite des Anbieters.
VISION_KLASSEN_ANKER = {
    "anthropic": {
        "ab": "from Sonnet 5",
        "grund": ("Sonnet 5 got every resident pair right and was the only model "
                  "with no consistent error at all"),
    },
    "gemini": {
        "ab": "from Gemini Flash (not Lite)",
        "grund": ("Flash made no consistent error in the pairs that finished; "
                  "Lite did"),
    },
    "gpt": {
        "ab": "from GPT-5.4",
        "grund": ("mini also worked in the grid measurement, with less reserve "
                  "on the stranger side"),
    },
}
VISION_KLASSEN_DATUM = "2026-08-09"
# Der Querschnitts-Befund, der ueber ALLEN Modellklassen steht — er gehoert an
# jede Kachel, weil er die Modellwahl relativiert.
VISION_MATERIAL_SATZ = (
    "Across every model class the thinnest candidate grid (3 cells) was the "
    "weakest case: not one stranger pair on it came out right, and it carried "
    "two of the three consistent errors. Material beats model class — more "
    "usable pictures of a walk-through help more than a bigger model."
)


def vision_klassen_hinweis(kachel):
    """Der Orientierungssatz "ab welcher Modellklasse traegt es" fuer EINE
    Anbieter-Kachel (.165, User-Wunsch 09.08.).

    ERZEUGT, nicht geschrieben: der Satz entsteht vollstaendig aus
    VISION_MESSWERTE. Das ist Absicht — ein von Hand formulierter
    Anbieter-Satz waere ein Streu-Literal, das beim naechsten Messlauf
    stillschweigend unwahr wird. Sortiert wird nach der Fremd-Abweisung, weil
    genau daran sich die Klassen hier unterschieden haben; die Erkennung war,
    wo gemessen, ueberall voll.

    TON (Vorgabe): mess-bezogen, kein Muss. Der Satz sagt, was HIER gemessen
    wurde, mit Datum und Bruch — er empfiehlt nichts und verspricht nichts fuer
    fremdes Material.

    Rueckgabe: dict(text, modelle, datum, hat) — leeres `hat`, wenn fuer diese
    Kachel nichts vermessen ist (dann steht auf der Seite auch nichts)."""
    eintraege = []
    for schluessel, e in VISION_MESSWERTE.items():
        m, _, k = schluessel.partition("|")
        if k != kachel:
            continue
        eintraege.append((m, e))
    if not eintraege:
        return {"text": "", "modelle": [], "datum": "", "hat": False}

    def _quote(w):
        return (w[0] / w[1]) if (w and w[1]) else -1.0

    eintraege.sort(key=lambda x: (-_quote(x[1].get("abweisen")), x[0]))
    fremd, eigen, daten, gitter = [], [], [], []
    for m, e in eintraege:
        if e.get("datum"):
            daten.append(e["datum"])
        marke = "" if e.get("roh_archiviert", True) else " (no raw result kept)"
        a = e.get("abweisen")
        if a:
            fremd.append(f"{m} {a[0]}/{a[1]}{marke}")
        r = e.get("erkennen")
        if r:
            eigen.append(f"{m} {r[0]}/{r[1]}{marke}")
        # Die NEUERE Reihe mit der heutigen Produkt-Methodik (Kandidaten-
        # Gitter). Sie steht getrennt, weil ihre Zahlen mit den obigen nicht
        # vergleichbar sind — andere Methodik, viel kleinere Stichprobe.
        g = e.get("gitter") or {}
        if g.get("erkennen") or g.get("abweisen"):
            st = []
            if g.get("erkennen"):
                st.append(f"{g['erkennen'][0]}/{g['erkennen'][1]} residents")
            if g.get("abweisen"):
                st.append(f"{g['abweisen'][0]}/{g['abweisen'][1]} strangers")
            if g.get("konsistent_falsch"):
                st.append(f"{g['konsistent_falsch']} consistent error(s)")
            if g.get("offen"):
                st.append(f"{g['offen']} pair(s) never finished")
            gitter.append(f"{m} " + ", ".join(st))
    teile = []
    if fremd:
        teile.append("turning strangers away: " + ", ".join(fremd))
    if eigen:
        teile.append("recognising people you taught it: " + ", ".join(eigen))
    if not teile:
        return {"text": "", "modelle": [], "datum": "", "hat": False,
                "anker": "", "anker_grund": "", "material": ""}
    datum = max(daten) if daten else ""
    text = ("In our measurement" + (f" ({datum})" if datum else "") + ", "
            + "; ".join(teile)
            + ". Those are our numbers on our material and our galleries — not "
              "a recommendation, and no promise about yours.")
    if gitter:
        text += (" Re-measured with the method suslik actually uses now (the "
                 "whole walk-through as ONE candidate grid): "
                 + "; ".join(gitter)
                 + ". That run is small — 3 candidates, up to 12 pairs per "
                   "model — so read it as a direction, not as a quota.")
    # Der Klassen-Anker (0.1.0.168): welche Klasse hat in der Gitter-Reihe
    # getragen. Er steht als EIGENES Feld neben dem Zahlen-Satz, damit die
    # Anzeige ihn hervorheben kann, ohne ihn nachzubauen.
    a = VISION_KLASSEN_ANKER.get(kachel) or {}
    anker = ""
    if a.get("ab"):
        anker = (f"{a['ab']} in the candidate-grid runs "
                 f"({VISION_KLASSEN_DATUM}) — {a['grund']}. Small sample: "
                 "3 candidates, up to 12 pairs per model.")
    return {"text": text, "modelle": [m for m, _ in eintraege], "datum": datum,
            "hat": True, "anker": anker, "anker_grund": a.get("grund", ""),
            "material": VISION_MATERIAL_SATZ}


def vision_gemessene_modelle(kachel=None):
    """Alle vermessenen Modellnamen (optional je Kachel) — fuer die Anzeige
    'we measured these' und fuer die Gate-Deckungspruefung."""
    aus = []
    for schluessel in VISION_MESSWERTE:
        m, k = schluessel.split("|", 1)
        if kachel is None or k == kachel:
            aus.append(m)
    return tuple(sorted(set(aus)))


def _autoritaet(u):
    """(start, ende) der Authority in einer URL — oder None. Reine String-Griffe
    (H29: die Registry bleibt importfrei, auch ohne `re`)."""
    i = u.find("//")
    if i < 0:
        return None
    start = i + 2
    ende = len(u)
    for z in ("/", "?", "#"):
        j = u.find(z, start)
        if j >= 0:
            ende = min(ende, j)
    return start, ende


def _query_teile(u):
    """(kopf, [paare], fragment) — oder None, wenn die URL keine Query hat."""
    q = u.find("?")
    if q < 0:
        return None
    kopf, rest = u[:q], u[q + 1:]
    frag = ""
    h = rest.find("#")
    if h >= 0:
        rest, frag = rest[:h], rest[h:]
    return kopf, rest.split("&"), frag


def endpunkt_anzeige(url):
    """Endpunkt-URL fuer Anzeige, Status, Log, Fehlermeldung: userinfo UND
    geheime Query-Parameter maskiert. Erweitert das bestehende Muster aus
    /sync_diagnose (dort nur die Zugangsdaten VOR dem Hostnamen) um die
    Query-Parameter — beide Traeger, EINE Funktion. Leere Eingabe -> ""."""
    u = str(url or "").strip()
    if not u:
        return ""
    a = _autoritaet(u)
    if a:
        start, ende = a
        autor = u[start:ende]
        at = autor.rfind("@")
        if at >= 0:
            u = u[:start] + "***@" + autor[at + 1:] + u[ende:]
    t = _query_teile(u)
    if t:
        kopf, paare, frag = t
        neu = []
        for paar in paare:
            if "=" in paar:
                name, _wert = paar.split("=", 1)
                if name.strip().lower() in SECRET_QUERY_PARAM:
                    neu.append(name + "=***")
                    continue
            neu.append(paar)
        u = kopf + "?" + "&".join(neu) + frag
    return u


def vision_maskiert(vcfg):
    """Der Vision-Config-Block in ANZEIGE-Form: Secrets zu '•••• set'/'',
    URL-Felder durch endpunkt_anzeige. Reine Logik — Status, Seite, Log und
    Fehlertexte nehmen NUR diese Form, nie den Rohblock."""
    aus = dict(vcfg or {})
    for f in VISION_SECRET_FELDER:
        aus[f] = "•••• set" if str(aus.get(f) or "") else ""
    for f in VISION_URL_FELDER:
        aus[f] = endpunkt_anzeige(aus.get(f))
    return aus


def vision_geheimnisse(vcfg):
    """Alle Klartext-Geheimnisse des Blocks als Menge — Eingang fuer den
    Log-Filter des Adapters (fehlertext_filtern) und fuer das Gate."""
    aus = set()
    for f in VISION_SECRET_FELDER:
        w = str((vcfg or {}).get(f) or "").strip()
        if w:
            aus.add(w)
    for f in VISION_URL_FELDER:
        u = str((vcfg or {}).get(f) or "")
        a = _autoritaet(u)
        if a:
            autor = u[a[0]:a[1]]
            at = autor.rfind("@")
            if at > 0:
                aus.add(autor[:at])
                for teil in autor[:at].split(":"):
                    if len(teil) >= 4:
                        aus.add(teil)
        t = _query_teile(u)
        if t:
            for paar in t[1]:
                if "=" in paar:
                    name, wert = paar.split("=", 1)
                    if name.strip().lower() in SECRET_QUERY_PARAM and wert:
                        aus.add(wert)
    return aus


# --- Dateinamen-Vertrag (Vorgriff auf konzept_struktur v3 §2; Issues #11 + #12) ---------
# Multi-Gesichts-Crops heissen <event>~N.jpg — die Tilde gehoert zum Alphabet. Diese
# Muster sind die EINZIGE Quelle fuer Pfad-Pruefungen von Event-IDs und Bild-Dateinamen;
# verstreute Regex-Literale haben zweimal dieselbe Fehlklasse erzeugt (Anzeige .103,
# Loeschen .107). Wer prueft, importiert von hier.
EID_RE = r"[\w.\-]+"            # Event-IDs (ts-id), OHNE Tilde
DATEI_RE = r"[\w .\-~']+"       # Bild-/Crop-Dateinamen, MIT Tilde + Leerzeichen + Apostroph
# (S4-Fix 01.09., Feldtester: Alt-WebP-Referenzen tragen den PERSONENNAMEN im
# DATEINAMEN — "<Name mit Apostroph>-<ts>.webp" aus Frigate-Importzeiten. Der
# .369-Fix erweiterte nur PERSON_RE; solche Dateien blieben unsichtbar (404)
# und unloeschbar ("ungueltiger Pfad"). Traversal verhindert weiterhin die
# realpath-Containment-Wache jedes Verbrauchers, nicht dieses Muster.)
# Lauf-Ordner unter state/lernlauf/: L<stempel> (Gesichts-Lernlauf) und
# B<stempel> (Bestands-/QS-Laeufe). Bis .362 lagen ZWEI widerspruechliche
# Literale verstreut (/lernlauf/crop nur L, /lernlauf/vorrat L+B — B-Laeufe
# bekamen an der einen Route nie ein Bild). ASCII explizit, kein \w
# (Support-QS 28.08.: \w ist Unicode-aware).
LAUF_ID_RE = r"[LB][A-Za-z0-9_]+"

# Personen-Namen (Ordnername unter faces/ und Formularwert). Bis 03.08. lagen FUENF
# leicht verschiedene Literale verstreut (Laengenlimits 1-40/2-40, eines mit "!"-Suffix,
# eines ganz ohne Limit) — dieselbe Streuklasse wie die Tilde, nur eine Ebene hoeher:
# ein per Frigate-Import angelegter Name wie "Anna.B" ist sichtbar, aber unbedienbar
# (Thumbnails 404, Loeschen "ungueltiger Pfad"). Wer prueft, nimmt PERSON_RE.
PERSON_RE = r"[\w .\-'()]{1,60}"    # inkl. Apostroph/Klammern: echte Namen (O'Neill,
#                                       "Anna (Nachbarin)") kommen aus dem Frigate-Import.
#                                       Sicher, weil UI escaped (_js/html.escape), URLs quoten
#                                       und der Export seit .107 ohne Shell laeuft (api_upload).

# Referenz-/Crop-Bildendungen. Sieben Stellen zaehlen sie auf; EINE vergass .webp
# (POST /person_loeschen meldete "0 reference images", waehrend 25 .webp im Papierkorb
# lagen — Frigate liefert .webp). Aufzaehlung = Vertrag, nie Streu-Literal.
BILD_ENDUNGEN = (".jpg", ".jpeg", ".png", ".webp")


# --- Modell-Vertrag der Erkennungs-Modelle (Konzept 15 §5 "Vorbedingung", 24.08.2026) ---
# DIE eine Quelle fuer jede fachliche Aufzaehlung der Erkennungs-Modelle: welche Datei,
# welche Eingangsform, welche Vorverarbeitung, welche Ausgangsskala, welches Geraet im
# Betrieb, welche Rolle im Urteil. Wer eine Modell-Liste braucht, nimmt DIESE.
#
# ANLASS (qs_ebenen.md: "Wer eine fachliche Aufzaehlung braucht, nimmt die zentrale Quelle
# oder deklariert einen Deckungs-Vertrag — nie ein weiteres verstreutes Literal").
# Die Aufzaehlung lag VIERFACH verstreut, jede Stelle mit einem anderen Ausschnitt:
#   1. face_audit.MODELLE                      — nur die zwei Recognition-Koepfe
#   2. FaceAnalysis(allowed_modules=[...])     — was insightface ueberhaupt laedt
#      in Embedder.__init__
#   3. das mixed-Dict in Embedder._to_backend  — Geraet je Task unter openvino:MIXED
#   4. die Modell-Konstanten der beiden Masse  — StrukturMass.MODELL_DATEI,
#      NormMass.NORM_KETTE, NormMass._graph_bytes
# Belegte DRIFT zwischen 2 und 3: seit .313 laedt allowed_modules landmark_2d_106 und
# genderage nicht mehr, das mixed-Dict verteilt beide aber weiter — eine Zuordnung, die
# ins Leere laeuft. modellvertrag_deckung() unten FINDET diese Drift und benennt sie;
# ob sie behoben wird, entscheidet ein eigener Zug, nicht dieser Vertrag.
#
# DER VERTRAG BESCHREIBT, ER SCHALTET NICHT. Heute liest ihn nur die Deckungspruefung.
# Die kommende Hardware-Nutzbarkeitspruefung (Konzept 15 §4: laeuft jedes Modell auf
# seinem Geraet wirklich richtig, in fp16 und in FP32?) nimmt ihre Modell-Liste von hier,
# sonst waere sie die fuenfte Streu-Stelle. Aendert sich der Code, meldet die Deckung.
#
# FUNDSTELLEN stehen als SYMBOLE (Modul + Klasse/Funktion/Konstante), nie als Zeilennummer:
# Zeilennummern wandern bei jeder Nachbarschafts-Aenderung — waehrend dieser Vertrag
# entstand, verschob ein paralleler Umbau an face_audit.py alles unterhalb von NormMass um
# rund 26 Zeilen. Ein Beleg, der ins Leere zeigt, ist schlimmer als keiner.
#
# FELDER je Eintrag (Schluessel = Kurzname der Modell-DATEI, nicht der Task: 'recognition'
# gibt es zweimal, einmal je Kopf):
#   datei/pfad_repo/pfad_image  Dateiname und Fundort im Repo bzw. im Image
#   paket            "buffalo_l" (insightface-Paket) | "eigen" (unser ONNX)
#   task             insightface-Taskname (app.models-Schluessel) oder None
#   modell_schluessel  Schluessel in face_audit.MODELLE oder None
#   abgeleitet_von   Eintrag, aus dessen Datei dieser Graph entsteht (Norm-Variante)
#   insightface_modul  wird es ueber FaceAnalysis(allowed_modules) geladen?
#   geladen          laedt der Betrieb es ueberhaupt (auch auf eigenem Weg)?
#   geladen_wann     unter welcher Bedingung (Config/Weg) — Klartext
#   eingang          {name, form, kanal, mean, std}: WIE der Tensor auszusehen hat
#   eingang_notiz    die Fallen dazu (s. PREPROCESSING unten)
#   ausgang          {namen, form, skala}: was herauskommt und in welcher Einheit
#   bezug            die Entscheidungslinie, gegen die der Wert im Betrieb faellt —
#                    daraus leitet die Hardware-Pruefung ihre Schwellen her, nie aus
#                    einer einzelnen Messung
#   soll_cpu         die EINGEFRORENEN CPU-Kennzahlen dieses Modells (s. SOLLZAHLEN unten)
#   geraet           Geraete-Rolle im Betrieb (Klartext)
#   geraet_mixed     Platz unter openvino:MIXED laut _to_backend ("GPU"/"NPU"/None)
#   cpu_fest         True = CPU by design (bekommt in der Pruefung keine Geraete-Zahl)
#   rolle/pruefrang  s. ROLLEN unten
#   notiz/beleg      Besonderheit bzw. Fundstelle je Angabe
#
# ROLLEN (und warum es vier Werte sind statt zwei): "urteil" = das Ergebnis entscheidet
# direkt, wer/ob jemand erkannt wird (Detektion, Erkennung). "vorrat" = die Feature-Norm;
# sie entscheidet nicht ueber Identitaet, sondern darueber, WELCHES Material gelernt wird
# — und sie ist die Pruefung, die auf der Legacy-iGPU die GPU verworfen hat (Konzept 15
# §1/§4). "ernte" = steuert Material und Anzeige (Pose, Struktur), nie eine Identitaet.
# "aus" = wird nicht geladen. pruefrang 1/2/3 ist die Reihenfolge fuers Erststart-Budget
# der Hardware-Pruefung ("Urteilspfad zuerst", Konzept 15 §4), None = nicht zu pruefen.
#
# PREPROCESSING-FALLE (Konzept 15 §4 "Messmaterial"; ohne diese Angabe misst man Unsinn):
# die beiden Landmark-Modelle sind mxnet-Exporte und wollen ROHE 0..255-Werte
# (input_mean=0, input_std=1 — insightface landmark.Landmark.__init__ erkennt den
# mxnet-Export daran; hier am Modell nachgemessen). Ein N(0,1)-Rauschinput ist fuer sie
# voellig off-distribution und erzeugt Scheinabweichungen
# (tester/gputest_kommandos_tokn59.md §1). Kanal-Ordnung: insightface fuettert alle
# buffalo_l-Modelle ueber cv2.dnn.blobFromImage(..., swapRB=True), der Tensor ist also
# RGB; unser adaface-Kopf erwartet dagegen BGR (Embedder._rec_infer).
#
# SOLLZAHLEN (`soll_cpu`, Lieferung C / Konzept 15 §4 "Messmaterial": eingefrorene
# CPU-Sollzahlen je Modell als DRITTER Anker, Zahlen statt Bildern). Sie beantworten die
# Frage, die ein reiner Geraet-gegen-CPU-Vergleich konstruktionsbedingt NIE beantworten
# kann: "und was, wenn Geraet UND CPU beide falsch rechnen?" — falsches Modell, falsche
# Vorverarbeitung, kaputter Runtime-Build. Aufbau je Eintrag:
#   art       Messgroesse (core.rechenprobe.massart leitet sie aus Rolle/Task ab)
#   einheit   was die Zahl BEDEUTET (Betriebsgroesse, wo es eine gibt, sonst Pruefsumme)
#   werte     eine Zahl je Kontrast-Skala des Mess-Reizes, in der Reihenfolge von
#             face_audit.NormMass.NORM_KREUZ_SKALEN — nie eine eigene Skalen-Liste hier
#   gemessen  wo und womit (eine Sollzahl ohne Herkunft waere ein geratener Wert)
# Der Vergleich laeuft relativ mit core.rechenprobe.SOLL_TOLERANZ_REL; die Herleitung
# dieser Toleranz und ihre ehrliche Grenze stehen dort.
MODELL_VERTRAG = {
    "det_10g": {
        "datei": "det_10g.onnx",
        "pfad_repo": "docker/buffalo_l/det_10g.onnx",
        "pfad_image": "/root/.insightface/models/buffalo_l/det_10g.onnx",
        "paket": "buffalo_l", "task": "detection", "modell_schluessel": None,
        "abgeleitet_von": None, "insightface_modul": True, "geladen": True,
        "geladen_wann": "immer (allowed_modules in Embedder.__init__)",
        "eingang": {"name": "input.1", "form": (1, 3, "H", "W"), "kanal": "RGB",
                    "mean": 127.5, "std": 128.0},
        "eingang_notiz": ("H/W sind dynamisch und werden im Betrieb gesetzt: 320x320 beim "
                          "Embedder-Aufbau (Embedder.__init__), fuer Clips ar_det_size mit "
                          "Basis 1280 und der /32-Regel (Embedder.ar_det_size)"),
        "ausgang": {"namen": ("448", "471", "494", "451", "474", "497", "454", "477", "500"),
                    "form": "3x (N,1) score · 3x (N,4) bbox · 3x (N,10) kps",
                    "skala": ("score 0..1; bbox/kps sind Distanzen in STRIDE-Einheiten 8/16/32 "
                              "(insightface scrfd.SCRFD._feat_stride_fpn) — in Pixel erst nach "
                              "Multiplikation mit dem Stride des jeweiligen Ausgangs")},
        "bezug": ("det_thresh 0.5 (insightface-Default scrfd.SCRFD.det_thresh; Config-Spanne "
                  "0.3-0.7, verifyd-Config-Whitelist det_thresh) auf der Score-Achse; auf der "
                  "Pixel-Achse min_kante 70 px (verifyd.yaml, Schluessel min_kante) als "
                  "kleinste Gesichtskante, die ueberhaupt zaehlt"),
        "geraet": ("Backend-Geraet aus resolve_backend (VERIFY_BACKEND/OV_DEVICE); "
                   "_to_backend ersetzt die prepare()-Session auf JEDEM Backend, auch cpu "
                   "(Embedder._to_backend)"),
        "geraet_mixed": "GPU", "cpu_fest": False, "rolle": "urteil", "pruefrang": 1,
        "soll_cpu": {"art": "score", "einheit": "hoechster Score ueber die drei Score-Koepfe",
                     "werte": (0.409645, 0.409774, 0.399527),
                     "gemessen": ("2026-08-24, LXC suslik (Core Ultra 9 285H), "
                                  "onnxruntime 1.24.1 CPU-EP, Eingang 320 px; zwei "
                                  "Laeufe derselben Session bitgleich (Abweichung 0.0). "
                                  "Der 1,0er-Wert deckt sich mit cpu_score_max=0.410 aus "
                                  "tester/gputest_kommandos_tokn59.md §3d")},
        "notiz": ("liefert ausser der Box die fuenf Keypoints fuers norm_crop-Alignment — "
                  "ein Versatz hier verschiebt JEDES Embedding (Embedder._get_mit_rec)"),
        "beleg": {"eingang": ("eigene Messung am Modell 2026-08-24 (ort get_inputs) "
                             "+ insightface scrfd.SCRFD"),
                  "ausgang": "eigene Messung 2026-08-24 + tester/gputest_kommandos_tokn59.md §1/§4",
                  "geraet": "face_audit.Embedder._to_backend, gelesen 2026-08-24"},
    },
    "1k3d68": {
        "datei": "1k3d68.onnx",
        "pfad_repo": "docker/buffalo_l/1k3d68.onnx",
        "pfad_image": "/root/.insightface/models/buffalo_l/1k3d68.onnx",
        "paket": "buffalo_l", "task": "landmark_3d_68", "modell_schluessel": None,
        "abgeleitet_von": None, "insightface_modul": True, "geladen": True,
        "geladen_wann": "immer (allowed_modules in Embedder.__init__)",
        "eingang": {"name": "data", "form": ("N", 3, 192, 192), "kanal": "RGB",
                    "mean": 0.0, "std": 1.0},
        "eingang_notiz": ("ROHE 0..255-Werte (mxnet-Export). Der Zuschnitt kommt IMMER aus "
                          "Landmark.get() mit dem fest verdrahteten Padding-Faktor 1.5 "
                          "(insightface landmark.Landmark.get) — ein eigener Zuschnitt "
                          "verschiebt die Skala"),
        "ausgang": {"namen": ("fc1",), "form": (1, 3309),
                    "skala": ("Rohwerte ~ +-1; Landmark.get() rechnet (wert+1) * 96 -> 1.0 "
                              "entspricht 96 px auf dem 192er Eingang (landmark.Landmark.get). "
                              "Daraus schaetzt insightface die Pose [pitch, yaw, roll] in Grad")},
        "bezug": ("die Pose wird zu front = 1 - (|pitch|+|yaw|)/90 (core.ernte.front_aus_pose) "
                  "und faellt gegen fd_front_min 0.85 (face_audit.ist_fehldetektion) sowie "
                  "gegen die Perspektiv-Bins der Benennung (core.benennung.perspektiv_bin)"),
        "geraet": "wie det_10g: Backend-Geraet, _to_backend ersetzt die Session",
        "geraet_mixed": "GPU", "cpu_fest": False, "rolle": "ernte", "pruefrang": 3,
        "soll_cpu": {"art": "landmark",
                     "einheit": ("Pruefsumme: Summe der Betraege aller 3309 Rohwerte, in "
                                 "px (x 96) — der Kosinus/Versatz braucht zwei Saetze, "
                                 "taugt also nicht als eingefrorener Einzelwert"),
                     "werte": (7014.637412, 6928.580982, 7112.183555),
                     "gemessen": ("2026-08-24, LXC suslik (Core Ultra 9 285H), "
                                  "onnxruntime 1.24.1 CPU-EP, Eingang 192 px ROH 0..255; "
                                  "zwei Laeufe derselben Session bitgleich")},
        "notiz": ("steuert Material und Anzeige, nie eine Identitaet — ABER der Live-Waechter "
                  "filtert mit derselben Pose seine Phantom-Detektionen weg "
                  "(core.livewache.echtes_gesicht), ein grober Fehler kostet dort Meldungen"),
        "beleg": {"eingang": "eigene Messung am Modell 2026-08-24 + insightface landmark.Landmark",
                  "ausgang": "eigene Messung 2026-08-24 + landmark.Landmark.get + gputest §1/§4",
                  "rolle": ("core.ernte.ernten (front aus pose) + "
                            "core.livewache.echtes_gesicht, gelesen 2026-08-24")},
    },
    "2d106det": {
        "datei": "2d106det.onnx",
        "pfad_repo": "docker/buffalo_l/2d106det.onnx",
        "pfad_image": "/root/.insightface/models/buffalo_l/2d106det.onnx",
        "paket": "buffalo_l", "task": "landmark_2d_106", "modell_schluessel": None,
        "abgeleitet_von": None, "insightface_modul": False, "geladen": True,
        "geladen_wann": ("NICHT ueber insightface (seit .313 aus allowed_modules raus), sondern "
                         "LAZY als eigene StrukturMass-Session neben einem warmen Prozess "
                         "(face_audit.StrukturMass, Aufruf worker._strukturmass_holen)"),
        "eingang": {"name": "data", "form": ("N", 3, 192, 192), "kanal": "RGB",
                    "mean": 0.0, "std": 1.0},
        "eingang_notiz": ("ROHE 0..255-Werte wie 1k3d68; gemessen wird IMMER ueber "
                          "Landmark.get() (Padding 1.5 fest) — mit anderem Faktor verschiebt "
                          "sich der Median messbar: 0.143 (1.0) / 0.156 (1.5) / 0.170 (2.0)"),
        "ausgang": {"namen": ("fc1",), "form": (1, 212),
                    "skala": ("106 Punkte x 2; dieselbe Rueckrechnung wie 1k3d68 "
                              "(1.0 ~ 96 px auf dem 192er Eingang). StrukturMass macht daraus "
                              "die mittlere Punkt-Streuung geteilt durch die laengste Bildkante "
                              "-> dimensionslos ~0.0..0.3")},
        "bezug": ("ernte_struktur_min 0.11 filtert VOR dem Crop, sichtung_struktur_min 0.15 "
                  "urteilt ueber die Anzeige (verifyd-Config-Defaults); Median echter "
                  "Gesichter 0.156 bei AUC 0.820 (face_audit.StrukturMass, Messung 22.08.)"),
        "geraet": ("CPU by design, mit gekapptem Pool (2 intra-op / 1 inter-op, "
                   "face_audit.StrukturMass.__init__). Die Geraetedrift WURDE gemessen und ist "
                   "unkritisch (CPU/NPU max |d| 0.00028, CPU/GPU 0.00098, null Kipper) — CPU "
                   "ist hier Sparsamkeit, keine Messbedingung"),
        "geraet_mixed": None, "cpu_fest": True, "rolle": "ernte", "pruefrang": 3,
        "soll_cpu": {"art": "landmark",
                     "einheit": "Pruefsumme: Summe der Betraege aller 212 Rohwerte, in px (x 96)",
                     "werte": (6328.284957, 6455.996761, 6790.516089),
                     "gemessen": ("2026-08-24, LXC suslik (Core Ultra 9 285H), "
                                  "onnxruntime 1.24.1 CPU-EP, Eingang 192 px ROH 0..255; "
                                  "zwei Laeufe derselben Session bitgleich. Das Modell "
                                  "laeuft cpu_fest — die Zahl ist der Anker fuer 'rechnet "
                                  "diese CPU ueberhaupt dasselbe Modell', kein Geraetetest")},
        "notiz": ("das mixed-Dict in _to_backend fuehrt 'landmark_2d_106' weiterhin auf GPU — "
                  "diese Zuordnung laeuft seit .313 ins Leere (die Deckungspruefung meldet sie)"),
        "beleg": {"eingang": ("eigene Messung am Modell 2026-08-24 + insightface "
                             "landmark.Landmark.__init__"),
                  "ausgang": "eigene Messung 2026-08-24 + face_audit.StrukturMass.streuung",
                  "geraet": ("face_audit.StrukturMass (GERAETEWAHL-Absatz + __init__), "
                             "gelesen 2026-08-24")},
    },
    "genderage": {
        "datei": "genderage.onnx",
        "pfad_repo": "docker/buffalo_l/genderage.onnx",
        "pfad_image": "/root/.insightface/models/buffalo_l/genderage.onnx",
        "paket": "buffalo_l", "task": "genderage", "modell_schluessel": None,
        "abgeleitet_von": None, "insightface_modul": False, "geladen": False,
        "geladen_wann": ("gar nicht: seit .313 aus allowed_modules raus (Embedder.__init__), "
                         "vorher lief es je Gesicht umsonst mit; analyze.py haelt die Felder "
                         "nur noch formal"),
        "eingang": {"name": "data", "form": ("N", 3, 96, 96), "kanal": "RGB",
                    "mean": 0.0, "std": 1.0},
        "eingang_notiz": ("rohe 0..255-Werte (mxnet-Export, insightface "
                          "attribute.Attribute.__init__), hier nachgemessen"),
        "ausgang": {"namen": ("fc1",), "form": (1, 3),
                    "skala": ("argmax der ersten zwei Werte = Geschlecht, "
                              "dritter Wert x 100 = Alter")},
        "bezug": None,
        "geraet": "keins — das Modell wird nicht geladen",
        "geraet_mixed": None, "cpu_fest": False, "rolle": "aus", "pruefrang": None,
        "notiz": ("liegt weiter im Image (Teil des buffalo_l-Pakets) und steht weiter im "
                  "mixed-Dict (Embedder._to_backend) — Karteileiche, von der Deckungspruefung "
                  "gemeldet"),
        "beleg": {"eingang": ("eigene Messung am Modell 2026-08-24 + insightface "
                             "attribute.Attribute"),
                  "geladen": "face_audit.Embedder.__init__ (.313), gelesen 2026-08-24"},
    },
    "w600k_r50": {
        "datei": "w600k_r50.onnx",
        "pfad_repo": "docker/buffalo_l/w600k_r50.onnx",
        "pfad_image": "/root/.insightface/models/buffalo_l/w600k_r50.onnx",
        "paket": "buffalo_l", "task": "recognition", "modell_schluessel": "buffalo",
        "abgeleitet_von": None, "insightface_modul": True, "geladen": True,
        "geladen_wann": ("Session wird IMMER gebaut (allowed_modules), aber nur bei "
                         "modell=buffalo genutzt: bei adaface entfernt _init_rec_onnx den "
                         "Eintrag aus app.models. Default ist adaface (verifyd.yaml, "
                         "Schluessel modell)"),
        "eingang": {"name": "input.1", "form": ("N", 3, 112, 112), "kanal": "RGB",
                    "mean": 127.5, "std": 127.5},
        "eingang_notiz": ("norm_crop-112-Ausschnitt aus den fuenf Detektor-Keypoints; "
                          "insightface fuettert ihn per blobFromImages mit swapRB=True, der "
                          "Tensor ist also RGB (arcface_onnx.ArcFaceONNX.get_feat)"),
        "ausgang": {"namen": ("683",), "form": (1, 512),
                    "skala": ("512 Werte, im Graph NICHT normiert — die L2-Normierung macht "
                              "erst insightface (Face.normed_embedding); danach gilt dieselbe "
                              "Kosinus-Skala wie bei adaface")},
        "bezug": "win_thresh 0.38 auf der Kosinus-Skala (verifyd.yaml, Schluessel win_thresh)",
        "geraet": "Backend-Geraet ueber _ort_session wie die anderen app.models-Sessions",
        "geraet_mixed": "NPU", "cpu_fest": False, "rolle": "urteil", "pruefrang": 1,
        "soll_cpu": {"art": "kosinus",
                     "einheit": ("Pruefsumme: Summe der Betraege der 512 Ausgangswerte "
                                 "(im Graph UNnormiert, daher die grosse Zahl)"),
                     "werte": (416.135133, 421.365023, 428.120172),
                     "gemessen": ("2026-08-24, LXC suslik (Core Ultra 9 285H), "
                                  "onnxruntime 1.24.1 CPU-EP, Eingang 112 px RGB; zwei "
                                  "Laeufe derselben Session bitgleich")},
        "notiz": ("zweiter Recognition-Kopf, im Betrieb hier nicht aktiv — die Schwellen und "
                  "der refcache haengen am aktiven Modell, ein Wechsel baut den Cache neu auf"),
        "beleg": {"eingang": ("eigene Messung am Modell 2026-08-24 (mean/std ueber "
                             "get_model) + insightface arcface_onnx.ArcFaceONNX"),
                  "ausgang": "eigene Messung 2026-08-24",
                  "geladen": ("face_audit.Embedder.__init__/_init_rec_onnx + "
                              "verifyd.yaml (modell), gelesen 2026-08-24")},
    },
    "adaface_ir101": {
        "datei": "adaface_ir101_webface12m.onnx",
        "pfad_repo": "models/adaface_ir101_webface12m.onnx",
        "pfad_image": "/app/models/adaface_ir101_webface12m.onnx",
        "paket": "eigen", "task": "recognition", "modell_schluessel": "adaface",
        "abgeleitet_von": None, "insightface_modul": False, "geladen": True,
        "geladen_wann": ("bei modell=adaface (Default, verifyd.yaml Schluessel modell) als "
                         "EIGENE Session self._rec; app.get wird gekapselt und setzt "
                         "face.embedding daraus (Embedder._init_rec_onnx/_get_mit_rec)"),
        "eingang": {"name": "input", "form": ("B", 3, 112, 112), "kanal": "BGR",
                    "mean": 127.5, "std": 127.5},
        "eingang_notiz": ("BGR — der Crop geht OHNE Kanaltausch hinein (Embedder._rec_infer, "
                          "spec['bgr']=True). Auf OpenVINO laeuft er in festen Batch-Stufen "
                          "1/2/4/8 mit Padding, sonst in exakter Batchgroesse "
                          "(Embedder.BATCH_STUFEN/_rec_infer)"),
        "ausgang": {"namen": ("embedding",), "form": ("B", 512),
                    "skala": ("im Graph L2-normiert (ReduceL2 -> Div), ||e|| = 1; Vergleich "
                              "per Kosinus")},
        "bezug": ("win_thresh 0.38 auf der Kosinus-Skala (verifyd.yaml, Schluessel win_thresh) "
                  "— ein Winkelfehler arccos(cos) uebersetzt sich direkt in eine Verschiebung "
                  "auf dieser Linie (Herleitung tester/gputest_kommandos_tokn59.md §4)"),
        "geraet": ("Backend-Geraet, aber mit eigener Fallback-KETTE statt hartem CPU-Absturz: "
                   "auf OpenVINO NPU -> GPU -> CPU, jeder Rueckfall LAUT als "
                   "PLACEMENT-FALLBACK (Embedder._session_kette)"),
        "geraet_mixed": "NPU", "cpu_fest": False, "rolle": "urteil", "pruefrang": 1,
        "soll_cpu": {"art": "kosinus",
                     "einheit": ("Pruefsumme: Summe der Betraege der 512 Embedding-Werte "
                                 "(im Graph L2-normiert, also ||e||=1 — die Summe der "
                                 "Betraege bleibt trotzdem modell-charakteristisch)"),
                     "werte": (18.243309, 18.197966, 18.208139),
                     "gemessen": ("2026-08-24, LXC suslik (Core Ultra 9 285H), "
                                  "onnxruntime 1.24.1 CPU-EP, Eingang 112 px BGR; zwei "
                                  "Laeufe derselben Session bitgleich")},
        "notiz": ("der Kopf, der entscheidet, WER jemand ist — hier zaehlt die Kosinus-"
                  "Abweichung gegen CPU, nicht die Rohdifferenz"),
        "beleg": {"eingang": "face_audit.MODELLE + Embedder._rec_infer + eigene Messung 2026-08-24",
                  "ausgang": ("eigene Messung 2026-08-24 + face_audit.NormMass "
                              "(Docstring Graph-Struktur)"),
                  "geraet": "face_audit.Embedder._to_backend/_session_kette, gelesen 2026-08-24"},
    },
    "adaface_ir101_norm": {
        "datei": "adaface_ir101_webface12m.onnx",
        "pfad_repo": "models/adaface_ir101_webface12m.onnx",
        "pfad_image": "/app/models/adaface_ir101_webface12m.onnx",
        "paket": "eigen", "task": None, "modell_schluessel": None,
        "abgeleitet_von": "adaface_ir101", "insightface_modul": False, "geladen": True,
        "geladen_wann": ("wenn der Lernvorrat traegt: NormMass wird im Worker gebaut "
                         "(worker._normmass_holen) und von der Ernte benutzt; nur fuer "
                         "modell=adaface kalibriert, sonst schaltet sie sich mit Grund ab "
                         "(NormMass.__init__)"),
        "eingang": {"name": "input", "form": ("B", 3, 112, 112), "kanal": "BGR",
                    "mean": 127.5, "std": 127.5},
        "eingang_notiz": ("wortgleich adaface_ir101 (dieselbe spec, NormMass.feature_norm), "
                          "aber EXAKTE Batchgroesse ohne Padding — eine Padding-Zeile darf nie "
                          "als Messwert durchgehen"),
        "ausgang": {"namen": ("embedding", "f"),
                    "form": "('B',512) + der Zusatz-Ausgang f",
                    "skala": ("gemessen wird ||f||, die LAENGE des unnormierten Feature-Vektors "
                              "vor der L2-Normierung: real ~15..30, auf dem synthetischen "
                              "Gesichtsreiz 26.07 (gputest §3f). Der Graph entsteht in-memory, "
                              "f wird als Zusatz-Ausgang deklariert (NormMass._graph_bytes)")},
        "bezug": ("die Qualitaetslinien des Vorrats: min 22.0 / gut 24.0 "
                  "(core.benennung.NORM_LATTE), Profil-Zweige 21.5 bzw. 23.5 "
                  "(verifyd-Config-Defaults vorrat_norm_min_profil / katalog_norm_min_profil). "
                  "Die Kreuzprobe gegen CPU laesst ein Geraet nur unter NORM_KREUZ_MAX 0.10 "
                  "durch (NormMass.NORM_KREUZ_MAX, 24.08.2026 aus dem Linienabstand 0.5 neu "
                  "hergeleitet; die alte 0.30 war an standard_normal-Rauschen bei Norm 11.6 "
                  "geeicht, also 10 Punkte neben jeder Entscheidung). Gemessen wird seither "
                  "auf dem synthetischen Gesichtsreiz (face_audit.gesichtsreiz) in den drei "
                  "Kontrast-Skalen NormMass.NORM_KREUZ_SKALEN"),
        "geraet": ("eigene Kette NPU -> GPU -> GPU_FP32 -> CPU (NormMass.NORM_KETTE) mit "
                   "Kreuzprobe gegen CPU je Stufe; SUSLIK_NORM_DEVICE erzwingt ein Geraet. "
                   "GPU_FP32 ist ein Pseudo-Geraet (face_audit.NORM_PSEUDO_GERAETE): dasselbe "
                   "device_type GPU, aber precision=FP32 statt der OpenVINO-Voreinstellung "
                   "fp16 — die Stufe faengt Geraete auf, deren fp16-Rechnung die Norm "
                   "verschiebt (Feldfall Gen8-iGPU: fp16 105.276), und teilt sich den "
                   "Kompilat-Cache mit der fp16-Stufe (eigener Blob, Praezision steckt im "
                   "Cache-Schluessel, gemessen 24.08.2026). Ohne OpenVINO-EP "
                   "(cpu-/cuda-/rocm-Image) bleibt es by construction CPU, weil "
                   "NormMass._feature_norm_session nur CPU oder OpenVINO kennt"),
        "geraet_mixed": None, "cpu_fest": False, "rolle": "vorrat", "pruefrang": 2,
        "soll_cpu": {"art": "norm",
                     "einheit": ("||f|| — die BETRIEBSGROESSE selbst (real 15..30, "
                                 "Entscheidungslinien 21,5 / 22,0 / 23,5 / 24,0)"),
                     "werte": (24.930459, 26.066286, 27.048271),
                     "gemessen": ("2026-08-24, LXC suslik (Core Ultra 9 285H), "
                                  "onnxruntime 1.24.1 CPU-EP, Graph-Variante mit "
                                  "Zusatz-Ausgang f, Eingang 112 px BGR; zwei Laeufe "
                                  "derselben Session bitgleich. Deckt sich mit der "
                                  "Eich-Messtabelle bei NormMass.NORM_KREUZ_MAX "
                                  "(CPU 24,930 / 26,066 / 27,048) — zwei unabhaengig "
                                  "gelaufene Messungen derselben Groesse")},
        "notiz": ("keine zweite Modell-Datei und kein Netz-Zugriff: derselbe Graph mit einem "
                  "zusaetzlichen Ausgang. Aus f/||f|| laesst sich ||f|| nicht zurueckrechnen, "
                  "deshalb ueberhaupt die Graph-Variante"),
        "beleg": {"eingang": "face_audit.NormMass.feature_norm, gelesen 2026-08-24",
                  "ausgang": ("face_audit.NormMass._graph_bytes + "
                              "tester/gputest_kommandos_tokn59.md §1/§3f"),
                  "geraet": ("face_audit.NormMass (GERAETEWAHL-Absatz, NORM_KETTE, "
                             "_session_waehlen) + face_audit.NORM_PSEUDO_GERAETE, "
                             "gelesen 2026-08-24 (FP32-Stufe)"),
                  "bezug": ("core.benennung.NORM_LATTE + verifyd-Config-Defaults + "
                            "face_audit.NormMass.NORM_KREUZ_MAX (Eich-Messtabelle im "
                            "Kommentar dort), gelesen 2026-08-24")},
    },
}

# Pflichtfelder je Eintrag — ein neues Modell ohne volle Angabe waere wieder eine halbe
# Quelle (die Klasse, gegen die dieser Vertrag gebaut ist).
MODELL_VERTRAG_PFLICHT = ("datei", "pfad_repo", "pfad_image", "paket", "task",
                          "modell_schluessel", "abgeleitet_von", "insightface_modul",
                          "geladen", "geladen_wann", "eingang", "ausgang", "bezug",
                          "geraet", "geraet_mixed", "cpu_fest", "rolle", "pruefrang",
                          "beleg")
MODELL_ROLLEN = ("urteil", "vorrat", "ernte", "aus")


def _vertrag_konstmenge(fn, anker):
    """Aufzaehlung aus einem Code-Objekt lesen, ohne die Datei zu parsen.

    CPython legt Dict-/Listen-Literale mit lauter konstanten Schluesseln als EINEN
    Konstanten-Tupel im Code-Objekt ab (co_consts) — sowohl die allowed_modules-Liste
    als auch die Schluessel des mixed-Dicts. Gelesen wird damit der KOMPILIERTE Stand,
    nicht ein Text, der zufaellig aehnlich aussieht.

    `anker` ist der Eintrag, den die gesuchte Aufzaehlung enthalten MUSS ('detection' —
    ohne Detektor gibt es keine Erkennung). Gibt es nicht genau einen Treffer, kommt
    None zurueck: die Deckungspruefung meldet das dann als 'nicht pruefbar' und faellt
    NIE still auf gruen (K1: eine Diagnose, die nichts findet, darf nicht wie eine
    Diagnose ohne Befund aussehen)."""
    code = getattr(fn, "__code__", None)
    if code is None:
        return None
    treffer = [c for c in code.co_consts
               if isinstance(c, tuple) and c and anker in c
               and all(isinstance(x, str) for x in c)]
    return tuple(treffer[0]) if len(treffer) == 1 else None


def modellvertrag_deckung(modelle=None, geladen_ist=None, mixed_ist=None, quelltext=None):
    """Haelt MODELL_VERTRAG gegen den echten Code -> Liste von Abweichungs-Strings.

    Leere Liste = gedeckt. Jede Zeile ist ein Befund im Klartext, damit ein Gate sie
    unveraendert ausgeben kann. Geprueft wird gegen drei Stellen:
      1. face_audit.MODELLE      — Namen, Dateiname und die Vorverarbeitungs-WERTE
                                   (mean/std/Kanalordnung), nicht nur die Schluessel
      2. allowed_modules         — welche Tasks insightface wirklich laedt
      3. das mixed-Dict aus _to_backend — welche Tasks unter openvino:MIXED verteilt
                                   werden (hier sitzt die bekannte Drift)

    ALLE Fakten sind injizierbar (Konzept 15 §6.2 "injizierbare Messfunktion"): mit
    Argumenten laeuft die Pruefung ohne jeden Fremd-Import und laesst sich mit
    gefaelschten Staenden durchspielen. Ohne Argumente holt sie face_audit selbst.

    ZWEI EHRLICHE GRENZEN:
    - `__import__` statt `import`: core/registry.py ist importfrei (H29), und der
      Registry-Selbsttest prueft das per AST ueber die GANZE Datei, also auch in
      Funktionskoerpern. Die Invariante dahinter ist Import-Freiheit beim LADEN des
      Moduls — die haelt hier: face_audit wird erst beim AUFRUF geholt. Das ist bewusst
      ein Pruefweg fuer Gate/Diagnose, kein Betriebsweg; die Import-Richtung
      "alle -> registry, nie zurueck" gilt fuer den Betrieb unveraendert.
    - Geprueft werden die MENGEN (welche Tasks) exakt und die Geraete-Zuordnung des
      mixed-Dicts nur als Textprobe am Quelltext — die WERTE eines Dict-Literals sind
      aus co_consts nicht verlaesslich der Reihe nach rekonstruierbar. Ist der Quelltext
      nicht lesbar, steht das als Befund in der Liste statt still zu fehlen."""
    abw = []
    fa = None
    if modelle is None or geladen_ist is None or mixed_ist is None or quelltext is None:
        try:
            fa = __import__("face_audit")
        except Exception as ex:                                        # noqa: BLE001
            return ["face_audit nicht ladbar (%s: %s) — Deckung NICHT geprueft"
                    % (type(ex).__name__, str(ex)[:120])]
    embedder = getattr(fa, "Embedder", None)
    if modelle is None:
        modelle = getattr(fa, "MODELLE", None) or {}
    if geladen_ist is None:
        geladen_ist = _vertrag_konstmenge(getattr(embedder, "__init__", None), "detection")
    if mixed_ist is None:
        mixed_ist = _vertrag_konstmenge(getattr(embedder, "_to_backend", None), "detection")
    if quelltext is None:
        try:
            with open(getattr(fa, "__file__", "") or "", encoding="utf-8") as f:
                quelltext = f.read()
        except Exception:                                              # noqa: BLE001
            quelltext = ""

    # --- 0) Vertrag in sich: Pflichtfelder, Rollenwerte, Ableitungen ------------------
    for name, v in MODELL_VERTRAG.items():
        fehlt = [f for f in MODELL_VERTRAG_PFLICHT if f not in v]
        if fehlt:
            abw.append("%s: Pflichtfelder fehlen: %s" % (name, ", ".join(fehlt)))
        if v.get("rolle") not in MODELL_ROLLEN:
            abw.append("%s: unbekannte rolle %r (erlaubt: %s)"
                       % (name, v.get("rolle"), ", ".join(MODELL_ROLLEN)))
        eltern = v.get("abgeleitet_von")
        if eltern:
            if eltern not in MODELL_VERTRAG:
                abw.append("%s: abgeleitet_von %r kennt der Vertrag nicht" % (name, eltern))
            elif MODELL_VERTRAG[eltern].get("eingang") != v.get("eingang"):
                abw.append("%s: Eingangsform weicht von %s ab, obwohl beide denselben Graphen "
                           "fuettern" % (name, eltern))

    # --- 1) face_audit.MODELLE: Namen UND Vorverarbeitungs-Werte ---------------------
    je_schluessel = {}
    for name, v in MODELL_VERTRAG.items():
        if v.get("modell_schluessel"):
            je_schluessel.setdefault(v["modell_schluessel"], []).append(name)
    for k in modelle:
        if k not in je_schluessel:
            abw.append("face_audit.MODELLE fuehrt %r — der Vertrag hat dazu keinen Eintrag" % k)
    for k, namen in sorted(je_schluessel.items()):
        if len(namen) > 1:
            abw.append("Modell-Schluessel %r steht in mehreren Vertrags-Eintraegen (%s) — "
                       "die Zuordnung waere mehrdeutig" % (k, ", ".join(sorted(namen))))
        if k not in modelle:
            abw.append("Vertrag nennt Modell-Schluessel %r (%s) — face_audit.MODELLE kennt ihn "
                       "nicht (mehr)" % (k, ", ".join(sorted(namen))))
            continue
        spec = modelle[k] or {}
        v = MODELL_VERTRAG[namen[0]]
        if spec.get("art") != "onnx":
            continue                       # insightface-eigener Kopf: MODELLE traegt dort
            #                                weder Datei noch Vorverarbeitung (die kommen aus
            #                                der Bibliothek und stehen im Vertrag mit Beleg)
        datei = str(spec.get("onnx") or "").replace("\\", "/").rsplit("/", 1)[-1]
        if datei and datei != v.get("datei"):
            abw.append("%s: MODELLE[%r].onnx heisst %r, der Vertrag fuehrt %r"
                       % (namen[0], k, datei, v.get("datei")))
        e = v.get("eingang") or {}
        if spec.get("mean") != e.get("mean") or spec.get("std") != e.get("std"):
            abw.append("%s: Vorverarbeitung weicht ab — MODELLE mean=%r std=%r, Vertrag "
                       "mean=%r std=%r" % (namen[0], spec.get("mean"), spec.get("std"),
                                           e.get("mean"), e.get("std")))
        kanal = "BGR" if spec.get("bgr") else "RGB"
        if kanal != e.get("kanal"):
            abw.append("%s: Kanalordnung weicht ab — MODELLE sagt %s, Vertrag sagt %r"
                       % (namen[0], kanal, e.get("kanal")))

    # --- 2) allowed_modules: was insightface wirklich laedt ---------------------------
    je_task = {}
    for name, v in MODELL_VERTRAG.items():
        if v.get("task"):
            je_task.setdefault(v["task"], []).append(name)
    if geladen_ist is None:
        abw.append("allowed_modules-Aufzaehlung in Embedder.__init__ nicht eindeutig lesbar "
                   "(Anker 'detection') — diese Deckung wurde NICHT geprueft")
    else:
        for t in geladen_ist:
            if t not in je_task:
                abw.append("allowed_modules laedt Task %r — der Vertrag kennt kein Modell dazu" % t)
            elif not any(MODELL_VERTRAG[n].get("insightface_modul") for n in je_task[t]):
                abw.append("Task %r steht in allowed_modules, der Vertrag fuehrt %s aber NICHT "
                           "als insightface-Modul" % (t, ", ".join(sorted(je_task[t]))))
        for t, namen in sorted(je_task.items()):
            drin = [n for n in namen if MODELL_VERTRAG[n].get("insightface_modul")]
            if drin and t not in geladen_ist:
                abw.append("Vertrag fuehrt %s als insightface-Modul — Task %r steht aber nicht "
                           "in allowed_modules" % (", ".join(sorted(drin)), t))

    # --- 3) mixed-Dict aus _to_backend: die Geraete-Verteilung unter openvino:MIXED ---
    if mixed_ist is None:
        abw.append("mixed-Zuordnung in Embedder._to_backend nicht eindeutig lesbar "
                   "(Anker 'detection') — diese Deckung wurde NICHT geprueft")
    else:
        for t in mixed_ist:
            if t not in je_task:
                abw.append("_to_backend verteilt Task %r — der Vertrag kennt kein Modell dazu" % t)
                continue
            tot = [n for n in je_task[t] if not MODELL_VERTRAG[n].get("insightface_modul")]
            if len(tot) == len(je_task[t]):
                abw.append("DRIFT: _to_backend verteilt Task %r auf ein Geraet, insightface laedt "
                           "ihn aber gar nicht (%s: insightface_modul=False) — die Zuordnung "
                           "laeuft ins Leere" % (t, ", ".join(sorted(tot))))
        for t, namen in sorted(je_task.items()):
            drin = [n for n in namen if MODELL_VERTRAG[n].get("insightface_modul")]
            if drin and t not in mixed_ist:
                abw.append("Vertrag fuehrt %s als insightface-Modul — Task %r fehlt aber im "
                           "mixed-Dict, MIXED legt es damit undeklariert auf den Default"
                           % (", ".join(sorted(drin)), t))

    # --- 4) Textprobe: stimmen die Geraete-WERTE des mixed-Dicts? ---------------------
    if not quelltext:
        abw.append("face_audit-Quelltext nicht lesbar — die Geraete-Werte des mixed-Dicts "
                   "wurden NICHT geprueft")
    else:
        gesehen = set()
        for name, v in sorted(MODELL_VERTRAG.items()):
            t, g = v.get("task"), v.get("geraet_mixed")
            if not t or not g or (t, g) in gesehen:
                continue
            gesehen.add((t, g))
            paar = '"' + t + '": "' + g + '"'
            if paar not in quelltext:
                abw.append("%s: Vertrag legt Task %r unter openvino:MIXED auf %s — in "
                           "face_audit.py steht kein %s" % (name, t, g, paar))
    return abw
