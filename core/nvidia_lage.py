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

EHRLICHE GRENZEN:
  - Ein gemerkter Treiberbefund gilt bis zum Ende des Prozesses; wird der Treiber spaeter verfuegbar, hilft
    ein Neustart.
  - Ein Treiber, der Geraete nennt, beweist noch keine gebundene ONNX-Sitzung und kein NVDEC oder NVENC; das
    pruefen die Aufrufer wie bisher an ihrem echten Weg.
  - Ein Prozess, der nach der Treiberfrage per fork ohne exec Kinder startet, gibt ihnen einen initialisierten
    Treiber mit (Bauplan, Grenzen).
"""
import ctypes
import glob
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
