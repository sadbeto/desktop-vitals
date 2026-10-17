"""Unit and live smoke tests for the telemetry collector."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import metrics


class SensorTests(unittest.TestCase):
    def test_sampler_cpu_delta_and_network(self):
        sampler = metrics.Sampler()
        fake_cpu = [(100, 25), (200, 55)]
        fake_net = [(1000, 2000), (3000, 5000)]
        with patch.object(metrics, 'cpu', side_effect=fake_cpu), patch.object(metrics, 'network', side_effect=fake_net), patch.object(metrics, 'processes', return_value=[]), patch.object(metrics, 'sensor', return_value=None), patch('time.monotonic', side_effect=[10, 12]):
            self.assertIsNone(sampler.sample()['cpu'])
            result = sampler.sample()
        self.assertEqual(result['cpu'], 70)
        self.assertEqual(result['network'], (1000, 1500))

    def test_nvidia_gpu_telemetry(self):
        output = SimpleNamespace(stdout='GeForce Test, 23, 64, 512, 4096\n')
        with patch('shutil.which', return_value='/usr/bin/nvidia-smi'), \
             patch('subprocess.run', return_value=output), \
             patch.object(metrics.Path, 'glob', return_value=iter([])):
            result = metrics.gpu_devices()
        self.assertEqual(result[0]['vendor'], 'NVIDIA')
        self.assertEqual(result[0]['usage'], 23)
        self.assertEqual(result[0]['vram_total'], 4096)

    def test_gpu_absent(self):
        with patch('shutil.which', return_value=None), \
             patch.object(metrics.Path, 'glob', return_value=iter([])):
            self.assertEqual(metrics.gpu_devices(), [])

    def test_live_readings(self):
        result = metrics.Sampler().sample()
        self.assertIsNotNone(result['memory'])
        self.assertTrue(0 <= result['memory'][0] <= 100)
        self.assertTrue(0 <= result['disk'][0] <= 100)
        self.assertIsInstance(result['processes'], list)


if __name__ == '__main__':
    unittest.main()
