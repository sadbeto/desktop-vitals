"""User-local packaging checks; no writes to real application directories."""
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from install import FILES, install


class InstallTests(unittest.TestCase):
    def test_install_and_update(self):
        source = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / 'data with spaces'
            launcher = install(source, data, 1)
            if shutil.which('desktop-file-validate'):
                subprocess.run(['desktop-file-validate', str(launcher)], check=True)
            for name in FILES:
                self.assertEqual((source / name).read_bytes(),
                                 (data / 'desktop-vitals' / name).read_bytes())
            self.assertIn('--monitor 1', launcher.read_text())
            self.assertIn('Icon=desktop-vitals', launcher.read_text())
            install(source, data)
            self.assertIn('--monitor 0', launcher.read_text())
            probe = subprocess.run(['/usr/bin/python3', str(data / 'desktop-vitals/app.py'), '--probe'], capture_output=True, text=True)
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertIn('"cpu"', probe.stdout)

    def test_missing_source_leaves_no_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / 'destination'
            with self.assertRaises(FileNotFoundError):
                install(Path(tmp), data)
            self.assertFalse(data.exists())
