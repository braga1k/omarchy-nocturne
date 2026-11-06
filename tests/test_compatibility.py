import types
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'payload/.local/lib/omarchy-nocturne/check-compatibility.py'
compatibility = types.ModuleType('compatibility')
exec(compile(PATH.read_text(), str(PATH), 'exec'), compatibility.__dict__)


class CompatibilityTests(unittest.TestCase):
    def test_global_preference_detects_compositor_or_bar_reset(self):
        for helper, per_monitor, expected in [('true', False, True), ('false', False, False), ('true', True, False)]:
            responses = ['{"contract":1,"ok":true,"morph":true}', 'true', '', helper,
                         '[{"name":"DP-1","focused":true,"activeWorkspace":{"id":2}}]',
                         '{"perMonitor":%s,"active":2,"buttons":[{"id":2,"focused":true}]}' % str(per_monitor).lower()]
            with self.subTest(helper=helper, per_monitor=per_monitor), patch.object(compatibility, 'run', side_effect=responses):
                self.assertEqual(compatibility.check(include_global=True)['ok'], expected)

    def test_workspace_highlight_mismatch_is_detected(self):
        for selected, expected in [(12, True), (1, False)]:
            responses = ['{"contract":1,"ok":true,"morph":true}', 'true', '',
                         '[{"name":"DP-1","focused":true,"activeWorkspace":{"id":12}}]',
                         '{"perMonitor":true,"active":12,"buttons":[{"id":%s,"focused":true}]}' % selected]
            with self.subTest(selected=selected), patch.object(compatibility, 'run', side_effect=responses):
                self.assertEqual(compatibility.check(include_workspaces=True)['ok'], expected)

    def test_optional_grid_and_missing_grid(self):
        for response, expected in [('{"phase":"idle","active":false}', True), ('unknown', False)]:
            with self.subTest(response=response), patch.object(compatibility, 'run', side_effect=['{"contract":1,"ok":true,"morph":true}', 'true', '', response]):
                self.assertEqual(compatibility.check(include_dock=True)['ok'], expected)

    def test_lazy_menu_is_pending_not_success_or_failure(self):
        with patch.object(compatibility, 'run', side_effect=['unknown', 'true', '']):
            result = compatibility.check()
        self.assertIsNone(result['ok'])
        self.assertTrue(result['pending'])
        self.assertEqual(result['issues'], [])

    def test_supported_live_contract(self):
        with patch.object(compatibility, 'run', side_effect=['{"contract":1,"ok":true,"morph":true}', 'true', '']):
            self.assertTrue(compatibility.check()['ok'])

    def test_missing_or_broken_menu_is_reported(self):
        for response in ['', '{}', '{"contract":1,"ok":false,"morph":true}']:
            with self.subTest(response=response), patch.object(compatibility, 'run', side_effect=[response, 'true', '']):
                self.assertFalse(compatibility.check()['ok'])

    def test_helper_and_config_failures(self):
        with patch.object(compatibility, 'run', side_effect=['{"contract":1,"ok":true,"morph":true}', 'false', 'bad config']):
            result = compatibility.check()
        self.assertFalse(result['ok'])
        self.assertEqual(len(result['issues']), 2)

    def test_unresponsive_shell_is_bounded_failure(self):
        with patch.object(compatibility, 'run', side_effect=[subprocess.TimeoutExpired('omarchy', 8), 'true', '']):
            self.assertFalse(compatibility.check()['ok'])
