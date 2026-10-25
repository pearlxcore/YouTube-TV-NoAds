"""Unsupported inputs must fail before any build output is created."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class InputGuards(unittest.TestCase):
    def test_wrong_profile_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            wrong = folder / 'not-the-original.apk'
            wrong.write_bytes(b'unsupported APK fixture')
            output = folder / 'output'
            result = subprocess.run([sys.executable, str(ROOT / 'patcher.py'), '--base', str(wrong),
                '--arm-split', str(wrong), '--apktool', str(wrong), '--build-tools', str(folder),
                '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('Unsupported APK hash', result.stderr)
            self.assertFalse(output.exists())

    def test_optimized_python_rejected(self):
        result = subprocess.run([sys.executable, '-O', str(ROOT / 'patcher.py'), '--base', 'unused',
            '--arm-split', 'unused', '--apktool', 'unused', '--build-tools', 'unused'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Run without -O', result.stderr)

if __name__ == '__main__':
    unittest.main()
