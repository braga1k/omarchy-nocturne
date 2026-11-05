from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LaunchLifecycleTests(unittest.TestCase):
    def test_keybinding_scanner_completes(self):
        result = subprocess.run(
            ['lua', str(ROOT / 'tests/launch_bindscan.lua'),
             str(ROOT / 'payload/.config/hypr/nocturne-launch.lua')],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_original_keybinding_hang_is_detected(self):
        result = subprocess.run(
            ['lua', str(ROOT / 'tests/launch_bindscan.lua'),
             str(ROOT / 'tests/fixtures/launch-before-startup-fix.lua.txt')],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('binding scan instruction budget exceeded', result.stderr)

    def check_lifecycle(self, mode):
        result = subprocess.run(
            ['lua', str(ROOT / 'tests/launch_lifecycle.lua'),
             str(ROOT / 'payload/.config/hypr/nocturne-launch.lua'), mode],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cold_start_and_runtime_recovery(self):
        self.check_lifecycle('cold-start')

    def test_offline_config_and_runtime_recovery(self):
        self.check_lifecycle('verify-config')

    def test_original_cold_start_regression_is_detected(self):
        self.check_original('cold-start', 'property refresh before input manager exists')

    def test_original_verify_config_regression_is_detected(self):
        self.check_original('verify-config', 'timer before event-loop manager exists')

    def check_original(self, mode, error):
        result = subprocess.run(
            ['lua', str(ROOT / 'tests/launch_lifecycle.lua'),
             str(ROOT / 'tests/fixtures/launch-before-startup-fix.lua.txt'), mode],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(error, result.stderr)


if __name__ == '__main__':
    unittest.main()
