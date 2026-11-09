"""CUDA driver evidence, independent of Linux/WSL device-node layout.

Driver availability is not proof of an ONNX provider binding or executing.
Callers must check their real sessions; video callers must probe FFmpeg.
No CUDA contexts/allocations and no pynvml dependency are needed here.
"""
import ctypes
import glob

from core.registry import NVIDIA_KNOTEN


def nvidia_nodes():
    return tuple(sorted({p for pattern in NVIDIA_KNOTEN for p in glob.glob(pattern)}))


def _driver():
    lib = ctypes.CDLL('libcuda.so.1')
    lib.cuInit.argtypes = [ctypes.c_uint]
    lib.cuInit.restype = ctypes.c_int
    lib.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
    lib.cuDeviceGetCount.restype = ctypes.c_int
    return lib


def cuda_status(device=0):
    """Return (usable driver device, diagnostic), never infer from /dev/dxg."""
    try:
        device = int(device)
    except (ValueError, TypeError):
        device = 0  # Same documented normalization as face_audit.
    try:
        lib = _driver()
        rc = lib.cuInit(0)
        if rc:
            return False, f'cuInit={rc}'
        count = ctypes.c_int()
        rc = lib.cuDeviceGetCount(ctypes.byref(count))
        if rc:
            return False, f'cuDeviceGetCount={rc}'
        if not 0 <= device < count.value:
            return False, f'device {device} outside CUDA device count {count.value}'
        return True, f'CUDA driver device {device} available (count={count.value})'
    except (OSError, AttributeError) as exc:
        return False, f'CUDA driver inaccessible: {exc}'
