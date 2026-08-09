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
DATEI_RE = r"[\w .\-~]+"        # Bild-/Crop-Dateinamen, MIT Tilde + Leerzeichen

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
