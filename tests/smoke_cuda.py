"""Tiny real CUDA run; no app data, network, or configuration access."""
import ast
import json
import logging
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# The image's core package remains intact; prepend only the patched core modules.
import core
core.__path__.insert(0, str(ROOT / 'core'))
from core.cuda_compat import cuda_status, nvidia_nodes
from core import systemstat
import numpy as np
import onnx
from onnx import helper, TensorProto
import onnxruntime as ort

print('nodes:', nvidia_nodes())
print('driver:', cuda_status())
assert cuda_status()[0]
print('telemetry:', systemstat._sonde_cuda())
model = helper.make_model(helper.make_graph(
    [helper.make_node('MatMul', ['a', 'b'], ['c'])], 'cuda-proof',
    [helper.make_tensor_value_info(x, TensorProto.FLOAT, [32, 32]) for x in ['a', 'b']],
    [helper.make_tensor_value_info('c', TensorProto.FLOAT, [32, 32])]),
    opset_imports=[helper.make_opsetid('', 16)], ir_version=8).SerializeToString()

with tempfile.TemporaryDirectory() as td:
    def options():
        so = ort.SessionOptions()
        so.intra_op_num_threads = 1
        so.inter_op_num_threads = 1
        so.enable_profiling = True
        so.profile_file_prefix = str(Path(td) / 'cuda-proof')
        return so
    # Execute the exact patched factory without importing application startup code.
    tree = ast.parse((ROOT / 'face_audit.py').read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_ort_session')
    ns = {'_log': logging.getLogger('smoke'), '_ort_thread_opts': options}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'face_audit.py', 'exec'), ns)
    session = ns['_ort_session']('cuda', '0', model)
    assert 'CUDAExecutionProvider' in session.get_providers(), session.get_providers()
    session.disable_fallback()
    a = np.arange(1024, dtype=np.float32).reshape(32, 32) / 1024
    result = session.run(None, {'a': a, 'b': a})[0]
    np.testing.assert_allclose(result, a @ a, rtol=1e-4, atol=1e-5)
    events = json.loads(Path(session.end_profiling()).read_text())
    kernels = [e for e in events if e.get('cat') == 'Node' and e.get('args', {}).get('provider')]
    assert kernels, 'No profiled execution events'
    assert all(e['args']['provider'] == 'CUDAExecutionProvider' for e in kernels), kernels
    assert any(e['args'].get('op_name') == 'MatMul' for e in kernels), kernels
    print('PASS: patched face_audit factory executed MatMul on CUDAExecutionProvider; numerical result verified')
    del session
    strict = options()
    strict.add_session_config_entry('session.disable_cpu_ep_fallback', '1')
    session = ort.InferenceSession(model, sess_options=strict,
        providers=[('CUDAExecutionProvider', {'device_id': 0, 'gpu_mem_limit': 32 * 1024 * 1024})])
    session.disable_fallback()
    np.testing.assert_allclose(session.run(None, {'a': a, 'b': a})[0], a @ a, rtol=1e-4, atol=1e-5)
    events = json.loads(Path(session.end_profiling()).read_text())
    assert any(e.get('args', {}).get('provider') == 'CUDAExecutionProvider' for e in events)
    print('PASS: additional strict session executed with CPU EP fallback disabled')
