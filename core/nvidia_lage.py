"""core/nvidia_lage — die eine Stelle, die entscheidet, ob hier eine NVIDIA-Karte nutzbar ist.

HERKUNFT: Bauplan analysen/bauplan_nvidia_wsl2.md, Stufe NW1, Vertrag NV1 (Issue #37). Unter Linux haengt die
Antwort an den Knoten /dev/nvidia* wie bisher. Unter Windows mit Docker Desktop (WSL2) gibt es diese Knoten nicht;
die Karte kommt ueber den WSL2-Knoten, und der Treiber des Windows-Wirts wird als libcuda eingeblendet. Den
WSL2-Knoten gibt es dort auch fuer Intel- und AMD-Karten, er allein ist kein NVIDIA-Zeichen. Deshalb fragt diese
Stelle dann den Treiber (cuInit, cuDeviceGetCount; der Weg stammt aus dem Pull Request #38 zum Issue).

LAST: Rechner mit /dev/nvidia* und Rechner ohne WSL2-Knoten machen nur die Knotenpruefung. Die Treiberfrage
laeuft hoechstens einmal je Prozess, auch bei gleichzeitigen Erstaufrufen; das Ergebnis bleibt gemerkt.

Die Knotenmuster kommen aus core/registry.py (KNOTEN_BASIS), nie von hier. Nur Standardbibliothek und
core.registry, damit jeder Prozess das Modul ohne Nebenwirkung laden kann.

URTEIL DER CUDA-VARIANTE (Bauplan analysen/bauplan_beschleuniger_lage.md, Stufe BL1): `lage_sammeln` liest, was
von der NVIDIA-Laufzeit im Container ankommt (beide Variablen, nvidia-smi, libcuda.so.1, Knoten, cuInit), und
`urteil` macht daraus genau einen Fall mit Marke und englischem Log-Satz. Anlass: ein Nutzer der cuda-Variante
hatte kein nutzbares Geraet (Fehler 100), und Startpruefung und Systemseite meldeten trotzdem gruen. Die Saetze
stehen nur in der Tabelle SAETZE. Der WSL2-Weg von nvidia_da bleibt davon unberuehrt; er fragt den Treiber getrennt.

EHRLICHE GRENZEN:
  - Ein gemerkter Treiberbefund gilt bis zum Ende des Prozesses; wird der Treiber spaeter verfuegbar, hilft
    ein Neustart. Dasselbe gilt fuer die gemerkte Lage aus `lage_sammeln`.
  - Ein Treiber, der Geraete nennt, beweist noch keine gebundene ONNX-Sitzung und kein NVDEC oder NVENC; das
    pruefen die Aufrufer wie bisher an ihrem echten Weg.
  - Ein Prozess, der nach der Treiberfrage per fork ohne exec Kinder startet, gibt ihnen einen initialisierten
    Treiber mit (Bauplan, Grenzen). `lage_sammeln` ruft cuInit im Dienst schon in der Startpruefung.
  - Unter WSL2 fragen nvidia_da und lage_sammeln den Treiber je einmal, zusammen also zweimal je Prozess.
  - Die Fehlernummer von ONNX Runtime selbst steht nur in deren stderr; das Urteil kennt nur den Code von cuInit.
"""
import ctypes
import glob
import os
import shutil
import threading

from core import registry as _reg

GRUND_KNOTEN = "knoten"
GRUND_WSL2 = "wsl2"

_SCHLOSS = threading.Lock()
# Ergebnis der Treiberfrage als (bool, grund); None heisst: in diesem Prozess noch nicht gefragt.
_TREIBER = None


def _treiber_fragen():
    """Fragt den eingeblendeten NVIDIA-Treiber (libcuda) nach der Zahl seiner Geraete.
    -> Anzahl; wirft OSError, wenn der Treiber fehlt oder eine Funktion einen Fehlercode liefert."""
    lib = ctypes.CDLL("libcuda.so.1")
    lib.cuInit.argtypes = [ctypes.c_uint]
    lib.cuInit.restype = ctypes.c_int
    lib.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
    lib.cuDeviceGetCount.restype = ctypes.c_int
    rc = lib.cuInit(0)
    if rc:
        raise OSError(f"cuInit returned {rc}")
    anzahl = ctypes.c_int()
    rc = lib.cuDeviceGetCount(ctypes.byref(anzahl))
    if rc:
        raise OSError(f"cuDeviceGetCount returned {rc}")
    return anzahl.value


def _treiber_gemerkt():
    """Die Treiberfrage hoechstens einmal je Prozess, unter einem Schloss. -> (bool, grund)"""
    global _TREIBER
    with _SCHLOSS:
        if _TREIBER is None:
            try:
                anzahl = _treiber_fragen()
                _TREIBER = ((True, GRUND_WSL2) if anzahl >= 1
                            else (False, "WSL2 GPU device present, NVIDIA driver reports no device"))
            except Exception as exc:                         # noqa: BLE001  wirft nie (NV1)
                _TREIBER = (False, f"WSL2 GPU device present, NVIDIA driver not usable "
                                   f"({type(exc).__name__}: {exc})")
        return _TREIBER


def nvidia_da():
    """Entscheidet, ob hier eine NVIDIA-Karte nutzbar ist: Knoten /dev/nvidia*, sonst Treiber unter WSL2.
    -> (bool, grund); grund ist "knoten", "wsl2" oder ein Klartext, warum nicht. Wirft nie."""
    try:
        if glob.glob(_reg.knoten_von("NVIDIA")):
            return True, GRUND_KNOTEN
        if not glob.glob(_reg.knoten_von("WSL2")):
            return False, "no NVIDIA device node and no WSL2 GPU device"
        return _treiber_gemerkt()
    except Exception as exc:                                 # noqa: BLE001  wirft nie (NV1)
        return False, f"NVIDIA check failed ({type(exc).__name__}: {exc})"


# ------------------------------------------------------------------ Urteil der cuda-Variante (BL1)
# Die eine Tabelle der englischen Log-Saetze dieses Urteils. Platzhalter: {wert} NVIDIA_DRIVER_CAPABILITIES,
# {visible} NVIDIA_VISIBLE_DEVICES, {code} Rueckgabe von cuInit, {geraete} Geraetezahl, {smi} und {bibliothek}
# da oder fehlt, {knoten} Zahl der Knoten /dev/nvidia*. Die Woerter fuer Fehlendes stehen unten in derselben Tabelle.
SAETZE = {
    "bibliothek_fehlt": (
        "the NVIDIA driver library libcuda.so.1 is missing in this container: it was started without the "
        "NVIDIA container runtime, so the card cannot compute here. Pass the card in with "
        "`capabilities: [gpu]` (Compose) or `--gpus all` (docker run)"),
    "kein_geraet": (
        "the NVIDIA driver library is present, but it reports no usable device (cuInit returned {code}, "
        "{geraete} device(s)). Check the device selection (NVIDIA_VISIBLE_DEVICES={visible}, "
        "NVIDIA_DRIVER_CAPABILITIES={wert}; Compose `capabilities: [gpu]`) and that the card works on the host "
        "(nvidia-smi there)"),
    "bindet_nicht": (
        "the NVIDIA card is visible (cuInit returned 0, {geraete} device(s)), but the CUDA session did not "
        "bind. Suspected cause: the host driver does not match the CUDA version in this image"),
    "werkzeug_fehlt": (
        "the NVIDIA card computes, but nvidia-smi is missing in this container "
        "(NVIDIA_DRIVER_CAPABILITIES={wert}), so card memory and load cannot be measured. Use "
        "`capabilities: [gpu]` (Compose, without further capabilities such as video) or `--gpus all`"),
    "ok": "NVIDIA card usable: cuInit returned 0, {geraete} device(s), nvidia-smi present",
    "fakten": (
        "NVIDIA in this container: NVIDIA_DRIVER_CAPABILITIES={wert}, NVIDIA_VISIBLE_DEVICES={visible}, "
        "nvidia-smi {smi}, libcuda.so.1 {bibliothek}, {knoten} device node(s), cuInit {code} with "
        "{geraete} device(s)"),
    "wort_da": "present",
    "wort_fehlt": "missing",
    "wort_ungesetzt": "(not set)",
    "wort_unbekannt": "?",
}
# Marke je Fall; werkzeug_fehlt ist FAIL nach Entscheid 2 des Eigentuemers (18.11.2026).
MARKEN = {"bibliothek_fehlt": "FAIL", "kein_geraet": "FAIL", "bindet_nicht": "FAIL",
          "werkzeug_fehlt": "FAIL", "ok": "info"}
# Die Faelle, in denen die Karte gar nicht rechnen kann (Bibliothek fehlt oder kein Geraet); Schritt 2 der
# Startpruefung meldet die CUDA-Zeile nur ausserhalb dieser Faelle mit ok.
KARTE_FEHLT = frozenset({"bibliothek_fehlt", "kein_geraet"})
# Gemerkte Lage aus lage_sammeln; None heisst: in diesem Prozess noch nicht gesammelt.
_LAGE = None


def _treiber_lesen():
    """Laedt libcuda.so.1 und fragt cuInit und die Geraetezahl, ohne zu werfen.
    -> (bibliothek_da, code, geraete); code und geraete sind None, wenn sie nicht gefragt werden konnten"""
    try:
        lib = ctypes.CDLL("libcuda.so.1")
    except OSError:
        return False, None, None
    try:
        lib.cuInit.argtypes = [ctypes.c_uint]
        lib.cuInit.restype = ctypes.c_int
        lib.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
        lib.cuDeviceGetCount.restype = ctypes.c_int
        code = lib.cuInit(0)
        if code:
            return True, code, None
        anzahl = ctypes.c_int()
        return True, code, (anzahl.value if lib.cuDeviceGetCount(ctypes.byref(anzahl)) == 0 else None)
    except Exception:                                        # noqa: BLE001  wirft nie
        return True, None, None


def lage_sammeln():
    """Sammelt, was von der NVIDIA-Laufzeit im Container ankommt; einmal je Prozess unter dem Schloss gemerkt.
    -> dict capabilities, visible, smi_da, bibliothek_da, code, geraete, knoten (Kopie); wirft nie"""
    global _LAGE
    with _SCHLOSS:
        if _LAGE is None:
            bibliothek_da, code, geraete = _treiber_lesen()
            try:
                knoten = len(glob.glob(_reg.knoten_von("NVIDIA")))
            except Exception:                                # noqa: BLE001  wirft nie
                knoten = None
            _LAGE = {"capabilities": os.environ.get("NVIDIA_DRIVER_CAPABILITIES"),
                     "visible": os.environ.get("NVIDIA_VISIBLE_DEVICES"),
                     "smi_da": shutil.which("nvidia-smi") is not None,
                     "bibliothek_da": bibliothek_da, "code": code, "geraete": geraete, "knoten": knoten}
        return dict(_LAGE)


def _anzeige(lage):
    """Die Werte der Lage als Text fuer die Saetze; Fehlendes mit den Woertern aus SAETZE. -> dict"""
    def zahl(x):
        return SAETZE["wort_unbekannt"] if x is None else str(x)

    def variable(x):
        return SAETZE["wort_ungesetzt"] if x is None else x

    def da(x):
        return SAETZE["wort_da"] if x else SAETZE["wort_fehlt"]
    return {"wert": variable(lage.get("capabilities")), "visible": variable(lage.get("visible")),
            "code": zahl(lage.get("code")), "geraete": zahl(lage.get("geraete")),
            "knoten": zahl(lage.get("knoten")), "smi": da(lage.get("smi_da")),
            "bibliothek": da(lage.get("bibliothek_da"))}


def urteil(lage, ort_gebunden=None):
    """Urteilt ueber die NVIDIA-Lage, erste passende Regel gilt; ohne `ort_gebunden` (Schritt 2) kein bindet_nicht.
    -> dict fall, marke, satz (englischer Log-Satz), werte mit wert (NVIDIA_DRIVER_CAPABILITIES) und code (cuInit)"""
    if not lage.get("bibliothek_da"):
        fall = "bibliothek_fehlt"
    elif lage.get("code") != 0 or not lage.get("geraete"):
        fall = "kein_geraet"
    elif ort_gebunden is False:
        fall = "bindet_nicht"
    elif not lage.get("smi_da"):
        fall = "werkzeug_fehlt"
    else:
        fall = "ok"
    return {"fall": fall, "marke": MARKEN[fall], "satz": SAETZE[fall].format(**_anzeige(lage)),
            "werte": {"wert": lage.get("capabilities"), "code": lage.get("code")}}


def faktenzeile(lage):
    """Baut die Faktenzeile fuers Startlog: beide Variablen, nvidia-smi, libcuda.so.1, Knoten, cuInit mit Geraetezahl.
    -> str"""
    return SAETZE["fakten"].format(**_anzeige(lage))
