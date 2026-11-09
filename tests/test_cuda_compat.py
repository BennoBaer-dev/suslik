import ast
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import cuda_compat as cc
from core import systemstat


def function(file, name, namespace):
    tree = ast.parse((ROOT / file).read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), file, 'exec'), namespace)
    return namespace[name]


def driver(init=0, count=1, count_rc=0):
    lib = Mock()
    lib.cuInit.return_value = init
    def get_count(ptr):
        ptr._obj.value = count
        return count_rc
    lib.cuDeviceGetCount.side_effect = get_count
    return lib


class DriverTests(unittest.TestCase):
    def test_native_and_wsl_and_no_nodes_with_working_driver(self):
        for nodes in [('/dev/nvidia0',), ('/dev/dxg',), ()]:
            with self.subTest(nodes=nodes), patch.object(cc, '_driver', return_value=driver()), patch.object(cc, 'nvidia_nodes', return_value=nodes):
                self.assertTrue(cc.cuda_status()[0])

    def test_dxg_does_not_prove_cuda(self):
        for lib in [driver(init=100), driver(count=0), driver(count_rc=999)]:
            with patch.object(cc, '_driver', return_value=lib), patch.object(cc, 'nvidia_nodes', return_value=('/dev/dxg',)):
                self.assertFalse(cc.cuda_status()[0])

    def test_missing_driver_and_invalid_device(self):
        with patch.object(cc, '_driver', side_effect=OSError('absent')):
            self.assertFalse(cc.cuda_status()[0])
        with patch.object(cc, '_driver', return_value=driver()):
            self.assertFalse(cc.cuda_status(1)[0])
            self.assertFalse(cc.cuda_status(-1)[0])

    def test_both_node_patterns(self):
        with patch.object(cc.glob, 'glob', side_effect=lambda p: {'/dev/nvidia*': ['/dev/nvidia0'], '/dev/dxg': ['/dev/dxg']}[p]):
            self.assertEqual(cc.nvidia_nodes(), ('/dev/dxg', '/dev/nvidia0'))


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.ort = Mock()
        self.ort.get_available_providers.return_value = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = Mock()
        self.session.get_providers.return_value = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.ort.InferenceSession.return_value = self.session
        self.log = Mock()
        self.build = function('face_audit.py', '_ort_session', {'_log': self.log, '_ort_thread_opts': lambda: None})
        self.modules = patch.dict(sys.modules, {'onnxruntime': self.ort})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def test_working_driver_attempts_cuda(self):
        with patch.object(cc, 'cuda_status', return_value=(True, 'ok')):
            self.assertIs(self.build('cuda', '0', b'model'), self.session)
        self.assertEqual(self.ort.InferenceSession.call_args.kwargs['providers'][0][0], 'CUDAExecutionProvider')

    def test_provider_listing_without_driver_uses_cpu(self):
        with patch.object(cc, 'cuda_status', return_value=(False, 'cuInit=100')):
            self.build('cuda', '0', b'model')
        self.assertEqual(self.ort.InferenceSession.call_args.kwargs['providers'], ['CPUExecutionProvider'])

    def test_failed_session_init_falls_back_and_logs(self):
        self.ort.InferenceSession.side_effect = [RuntimeError('cuDNN failed'), self.session]
        with patch.object(cc, 'cuda_status', return_value=(True, 'ok')):
            self.assertIs(self.build('cuda', '0', b'model'), self.session)
        self.assertEqual(self.ort.InferenceSession.call_args.kwargs['providers'], ['CPUExecutionProvider'])
        self.log.error.assert_called()

    def test_silent_ort_fallback_is_reported(self):
        self.session.get_providers.return_value = ['CPUExecutionProvider']
        with patch.object(cc, 'cuda_status', return_value=(True, 'ok')):
            self.build('cuda', '0', b'model')
        self.log.error.assert_called()

    def test_missing_ep_uses_cpu(self):
        self.ort.get_available_providers.return_value = ['CPUExecutionProvider']
        self.build('cuda', '0', b'model')
        self.assertEqual(self.ort.InferenceSession.call_args.kwargs['providers'], ['CPUExecutionProvider'])


class TelemetryTests(unittest.TestCase):
    def probe(self, result=None, error=None):
        with patch.object(systemstat.subprocess, 'run', return_value=result, side_effect=error):
            return systemstat._sonde_cuda()

    def test_inventory_uses_driver_instead_of_nodes_for_cuda(self):
        for available in (True, False):
            with patch.object(systemstat, 'nvidia_nodes', return_value=()), patch.object(systemstat, 'cuda_status', return_value=(available, 'probe')), patch.object(systemstat, '_knoten_da', return_value=False):
                self.assertEqual(systemstat.geraete_lage()['cuda'], ('0',) if available else ())

    def test_gpu_tile_keeps_nvml_telemetry_when_cuda_init_fails(self):
        result = types.SimpleNamespace(returncode=0, stdout='5, 7547, 8188, 40, 641')
        for nodes in [('/dev/nvidiactl',), ('/dev/dxg',)]:
            with self.subTest(nodes=nodes), patch.object(systemstat, 'nvidia_nodes', return_value=nodes), patch.object(systemstat, 'cuda_status', return_value=(False, 'cuInit=100')), patch.object(systemstat, '_knoten_da', return_value=False), patch.object(systemstat.subprocess, 'run', return_value=result) as query:
                d = systemstat.gpu_messen()
                self.assertEqual(d['kind'], 'cuda')
                self.assertEqual(d['prozent'], 5)
                self.assertEqual(d['speicher_frei_mb'], 641)
                self.assertIsNone(d['grund'])
                query.assert_called_once()

    def test_missing_utilization_has_tile_reason_without_invalidating_memory(self):
        result = types.SimpleNamespace(returncode=0, stdout='[N/A], 7547, 8188, [N/A], 641')
        with patch.object(systemstat, 'nvidia_nodes', return_value=('/dev/dxg',)), patch.object(systemstat, '_knoten_da', return_value=False), patch.object(systemstat.subprocess, 'run', return_value=result):
            raw = systemstat.SONDEN['cuda']()
            tile = systemstat.gpu_messen()
        self.assertIsNone(raw['grund'])
        self.assertEqual(raw['speicher_frei_mb'], 641)
        self.assertEqual(tile['grund'], 'nicht_lesbar')
        self.assertIsNone(tile['prozent'])
        self.assertNotIn('auslastung_grund', raw)
        self.assertEqual(tile['speicher_max_mb'], 8188)

    def test_unavailable_process_memory_is_not_reported_as_zero(self):
        result = types.SimpleNamespace(returncode=0, stdout='1, [N/A]')
        with patch.object(systemstat.subprocess, 'run', return_value=result):
            values, reason = systemstat.prozesse_karte_mb([123])
        self.assertEqual(values, {})
        self.assertEqual(reason, 'kein_eintrag')

    def test_memory_without_device_nodes(self):
        d = self.probe(types.SimpleNamespace(returncode=0, stdout='0, 7547, 8188, 40, 641'))
        self.assertEqual(d['speicher_frei_mb'], 641)
        self.assertIsNone(d['grund'])

    def test_optional_wsl_fields(self):
        d = self.probe(types.SimpleNamespace(returncode=0, stdout='[N/A], 7547, 8188, [N/A], 641'))
        self.assertEqual(d['speicher_max_mb'], 8188)
        self.assertIsNone(d['grund'])
        self.assertIsNone(d['prozent'])

    def test_missing_tool_timeout_and_bad_data(self):
        self.assertEqual(self.probe(error=FileNotFoundError())['grund'], 'werkzeug_fehlt')
        self.assertEqual(self.probe(error=subprocess.TimeoutExpired('nvidia-smi', 2))['messgrund'], 'timeout')
        for stdout in ['', 'bad', '0, N/A, N/A, 40, N/A']:
            self.assertIsNotNone(self.probe(types.SimpleNamespace(returncode=0, stdout=stdout))['grund'])
        self.assertIsNotNone(self.probe(types.SimpleNamespace(returncode=1, stdout=''))['grund'])


class VideoTests(unittest.TestCase):
    def test_decode_candidate_requires_working_driver(self):
        candidate = function('decode.py', 'nv_da', {})
        for available in (True, False):
            with patch.object(cc, 'cuda_status', return_value=(available, 'probe')):
                self.assertEqual(candidate(), available)

    def test_dxg_never_skips_real_encode_probe(self):
        import os
        import time
        probe = Mock(return_value=False)
        ns = {'_VIDEO_ENCODER': None, '_encode_probe': probe, 'os': os, 'time': time}
        video = function('verifyd.py', 'video_encoder', ns)
        with patch.object(cc, 'nvidia_nodes', return_value=('/dev/dxg',)), patch.object(os, 'listdir', side_effect=FileNotFoundError()):
            self.assertEqual(video(), ('cpu', None))
        self.assertIn('h264_nvenc', probe.call_args.args[0])


class DiagnosticTests(unittest.TestCase):
    def test_variant_banner_uses_driver_evidence(self):
        import os
        banner = function('verifyd.py', 'varianten_hinweis', {'os': os})
        with patch.object(cc, 'cuda_status', return_value=(True, 'driver ok')):
            self.assertIsNone(banner('cuda', []))
        with patch.object(cc, 'cuda_status', return_value=(False, 'cuInit=100')), patch.object(cc, 'nvidia_nodes', return_value=()), patch.object(os.path, 'exists', return_value=False):
            self.assertIn('cuInit=100', banner('cuda', []))

    def test_cpu_image_recommends_cuda_without_compute_driver(self):
        import os
        banner = function('verifyd.py', 'varianten_hinweis', {'os': os})
        for nodes in [('/dev/nvidiactl',), ('/dev/dxg',)]:
            with self.subTest(nodes=nodes), patch.object(cc, 'cuda_status', return_value=(False, 'missing libcuda')), patch.object(cc, 'nvidia_nodes', return_value=nodes):
                self.assertIn('cuda image would', banner('cpu', []))

    def test_visible_node_does_not_hide_cuda_image_driver_failure(self):
        import os
        banner = function('verifyd.py', 'varianten_hinweis', {'os': os})
        with patch.object(cc, 'cuda_status', return_value=(False, 'cuInit=100')), patch.object(cc, 'nvidia_nodes', return_value=('/dev/dxg',)), patch.object(os.path, 'exists', return_value=False):
            self.assertIn('cuInit=100', banner('cuda', []))

    def test_no_nvidia_evidence_does_not_recommend_cuda(self):
        import os
        banner = function('verifyd.py', 'varianten_hinweis', {'os': os})
        with patch.object(cc, 'cuda_status', return_value=(False, 'missing libcuda')), patch.object(cc, 'nvidia_nodes', return_value=()):
            self.assertIsNone(banner('cpu', []))


if __name__ == '__main__':
    unittest.main()
