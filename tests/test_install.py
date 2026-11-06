import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'install.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / 'home'
        self.stock = Path(self.tmp.name) / 'stock'
        (self.home / '.config/hypr').mkdir(parents=True)
        (self.stock / 'config/omarchy').mkdir(parents=True)
        self.hypr = self.home / '.config/hypr/hyprland.lua'
        self.hypr.write_text('require("default.hypr.omarchy")\nrequire("hypr.omacontrol")\nrequire("default.hypr.toggles")\n')
        self.config = {'version': 1, 'idle': {'lock': 900}, 'bar': {'centerAnchor': 'omarchy.clock', 'layout': {
            'left': [{'id': 'omarchy.menu'}], 'center': [{'id': 'omarchy.clock', 'format': 'HH:mm'}],
            'right': [{'id': 'thirdparty.audio'}, {'id': 'omarchy.tray', 'pinned': ['custom-app']}] }},
            'plugins': [{'id': 'custom.service', 'option': 'keep'}], 'disabledPlugins': ['omarchy.emojis']}
        (self.stock / 'config/omarchy/shell.json').write_text(json.dumps(self.config))

    def enable_grid_fixture(self):
        for relative in ['shell/plugins/dock/AppGrid.qml', 'shell/services/AppLibrary.qml']:
            p = self.stock / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('// test dependency')
        self.config['dock'] = {'position': 'left', 'pinned': ['example.desktop']}
        self.config['plugins'].append({'id': 'omarchy.dock', 'customOption': 42})
        (self.stock / 'config/omarchy/shell.json').write_text(json.dumps(self.config))

    def test_optional_grid_roundtrip_and_native_route(self):
        self.enable_grid_fixture()
        m.install(self.home, self.stock, True, app_grid=True)
        installed = self.home / '.config/omarchy/plugins/nocturne.dock/AppGrid.qml'
        self.assertTrue(installed.is_file())
        config = json.loads((self.home / '.config/omarchy/shell.json').read_text())
        self.assertEqual(config['dock'], self.config['dock'])
        self.assertIn({'id': 'nocturne.dock', 'customOption': 42}, config['plugins'])
        self.assertIn('omarchy.dock', config['disabledPlugins'])
        self.assertIn('nocturne.dock', config['cloneSourceRestores'])
        record = json.loads((self.home / m.STATE).read_text())
        self.assertIn(str(installed.relative_to(self.home)), record['files'])
        m.uninstall(self.home, True)
        self.assertFalse(installed.exists())
        self.assertFalse((self.home / m.STATE).exists())

    def test_optional_grid_requires_native_dependencies(self):
        with self.assertRaisesRegex(ValueError, 'requires the Omarchy 4.5'):
            m.install(self.home, self.stock, True, app_grid=True)
        self.assertFalse((self.home / m.STATE).exists())

    def test_optional_grid_preserves_explicit_disable(self):
        self.enable_grid_fixture()
        self.config['plugins'] = []
        self.config['disabledPlugins'].append('omarchy.dock')
        (self.stock / 'config/omarchy/shell.json').write_text(json.dumps(self.config))
        files = m.prepare(self.home, self.stock, app_grid=True)
        config = json.loads(files['.config/omarchy/shell.json'])
        self.assertNotIn({'id': 'nocturne.dock'}, config['plugins'])
        self.assertIn('omarchy.dock', config['disabledPlugins'])

    def test_unsupported_bar_sections_refused_without_writes(self):
        for section in ['centerBegin', 'centerEnd', 'tray']:
            with self.subTest(section=section):
                self.config['bar']['layout'][section] = [{'id': 'omarchy.weather'}]
                (self.stock / 'config/omarchy/shell.json').write_text(json.dumps(self.config))
                before = {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
                with self.assertRaisesRegex(ValueError, section):
                    m.install(self.home, self.stock, True)
                self.assertEqual(before, {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()})
                del self.config['bar']['layout'][section]

    def test_roundtrip_and_preferences(self):
        original = self.hypr.read_bytes()
        m.install(self.home, self.stock, True)
        shell = self.home / '.config/omarchy/shell.json'
        data = json.loads(shell.read_text())
        self.assertEqual(data['idle'], self.config['idle'])
        self.assertEqual(data['bar']['layout']['center'][0]['format'], 'HH:mm')
        self.assertEqual(data['bar']['layout']['right'][1]['pinned'], ['custom-app'])
        self.assertEqual(data['bar']['layout']['right'][0]['id'], 'thirdparty.audio')
        self.assertIn('omarchy.emojis', data['disabledPlugins'])
        self.assertNotIn({'id': 'nocturne.emojis'}, data['plugins'])
        text = self.hypr.read_text()
        self.assertLess(text.index('hypr.nocturne-motion'), text.index('hypr.omacontrol'))
        extra = self.home / '.config/omarchy/plugins/nocturne.menu/my-extra.txt'
        extra.write_text('keep')
        m.uninstall(self.home, True)
        self.assertEqual(self.hypr.read_bytes(), original)
        self.assertFalse(shell.exists())
        self.assertEqual(extra.read_text(), 'keep')

    def test_dry_run_has_no_writes(self):
        before = sorted(str(p) for p in self.home.rglob('*'))
        m.install(self.home, self.stock)
        self.assertEqual(before, sorted(str(p) for p in self.home.rglob('*')))

    def test_conflict_refuses_before_writing(self):
        m.install(self.home, self.stock, True)
        self.hypr.write_text(self.hypr.read_text() + '-- my new preference\n')
        with self.assertRaisesRegex(ValueError, 'Changed since'):
            m.uninstall(self.home, True)
        self.assertTrue((self.home / '.config/omarchy/ui/nocturne/LaunchMorph.qml').exists())
        self.assertIn('my new preference', self.hypr.read_text())

    def test_symlink_parent_refused(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        (self.home / '.config/omarchy').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            m.install(self.home, self.stock, True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_failed_write_restores_prior_files(self):
        original = self.hypr.read_bytes()
        atomic = m.atomic
        counter = [0]
        def fail_once(path, data, **kwargs):
            counter[0] += 1
            if counter[0] == 8:
                raise OSError('simulated disk error')
            return atomic(path, data, **kwargs)
        m.atomic = fail_once
        try:
            with self.assertRaisesRegex(OSError, 'simulated'):
                m.install(self.home, self.stock, True)
        finally:
            m.atomic = atomic
        self.assertEqual(self.hypr.read_bytes(), original)
        self.assertFalse((self.home / m.STATE).exists())
        self.assertFalse(any(p.is_file() for p in (self.home / '.config/omarchy').rglob('*')))

    def test_chmod_failure_restores_written_script(self):
        original = Path.chmod
        failed = [False]
        def fail_once(path, mode, *args, **kwargs):
            if path.name == 'capture.sh' and mode == 0o755 and not failed[0]:
                failed[0] = True
                raise OSError('injected chmod failure')
            return original(path, mode, *args, **kwargs)
        Path.chmod = fail_once
        try:
            with self.assertRaisesRegex(OSError, 'injected chmod'):
                m.install(self.home, self.stock, True)
        finally:
            Path.chmod = original
        self.assertTrue(failed[0])
        self.assertFalse((self.home / m.STATE).exists())
        self.assertFalse(any(p.is_file() for p in (self.home / '.config/omarchy').rglob('*')))

    def test_backup_private_before_atomic_publish(self):
        original = m.os.replace
        modes = []
        def observe(src, dst):
            if Path(dst) == self.home / m.STATE:
                modes.append(Path(src).stat().st_mode & 0o777)
            return original(src, dst)
        m.os.replace = observe
        try:
            m.install(self.home, self.stock, True)
        finally:
            m.os.replace = original
        self.assertEqual(modes, [0o600, 0o600])

    def test_custom_clone_is_not_silently_skipped(self):
        self.config['bar']['layout']['left'] = [{'id': 'custom.menu'}]
        (self.stock / 'config/omarchy/shell.json').write_text(json.dumps(self.config))
        plugin = self.home / '.config/omarchy/plugins/custom.menu'
        plugin.mkdir(parents=True)
        (plugin / 'manifest.json').write_text(json.dumps({'omarchy': {'clonedFrom': 'omarchy.menu'}}))
        with self.assertRaisesRegex(ValueError, 'Active custom clone'):
            m.install(self.home, self.stock, True)
        self.assertFalse((self.home / m.STATE).exists())

    def test_state_path_cannot_escape(self):
        with self.assertRaises(ValueError):
            m.safe_path(self.home, '../../outside')

    def broken_installation(self):
        m.install(self.home, self.stock, True)
        old = (m.ROOT / 'tests/fixtures/launch-before-startup-fix.lua.txt').read_bytes()
        self.assertEqual(m.digest(old), m.BROKEN_LAUNCH_SHA256)
        helper = self.home / m.LAUNCH_HELPER
        helper.write_bytes(old)
        state = self.home / m.STATE
        record = json.loads(state.read_text())
        record['files'][m.LAUNCH_HELPER]['after'] = m.BROKEN_LAUNCH_SHA256
        state.write_text(json.dumps(record))
        return helper, state, record

    def test_startup_repair_preserves_backup_and_uninstall(self):
        original_hypr = self.hypr.read_bytes()
        helper, state, record = self.broken_installation()
        m.repair_startup(self.home, True)
        self.assertEqual(helper.read_bytes(), (m.PAYLOAD / m.LAUNCH_HELPER).read_bytes())
        record['files'][m.LAUNCH_HELPER]['after'] = m.digest(helper.read_bytes())
        self.assertEqual(json.loads(state.read_text()), record)
        self.assertEqual(state.stat().st_mode & 0o777, 0o600)
        m.repair_startup(self.home, True)  # Repeated repair is harmless.
        m.uninstall(self.home, True)
        self.assertFalse(helper.exists())
        self.assertEqual(self.hypr.read_bytes(), original_hypr)

    def test_startup_repair_dry_run(self):
        helper, state, _ = self.broken_installation()
        before = (helper.read_bytes(), state.read_bytes())
        m.repair_startup(self.home)
        self.assertEqual((helper.read_bytes(), state.read_bytes()), before)

    def test_startup_repair_refuses_custom_helper(self):
        helper, state, _ = self.broken_installation()
        helper.write_bytes(helper.read_bytes() + b'\n-- user modification\n')
        before = (helper.read_bytes(), state.read_bytes())
        with self.assertRaisesRegex(ValueError, 'Custom launch helper'):
            m.repair_startup(self.home, True)
        self.assertEqual((helper.read_bytes(), state.read_bytes()), before)

    def test_startup_repair_resumes_after_state_write_failure(self):
        helper, state, _ = self.broken_installation()
        old_record = state.read_bytes()
        atomic = m.atomic
        def fail_state(path, data, **kwargs):
            if path == state:
                raise OSError('injected state failure')
            return atomic(path, data, **kwargs)
        m.atomic = fail_state
        try:
            with self.assertRaisesRegex(OSError, 'injected state'):
                m.repair_startup(self.home, True)
        finally:
            m.atomic = atomic
        self.assertEqual(helper.read_bytes(), (m.PAYLOAD / m.LAUNCH_HELPER).read_bytes())
        self.assertEqual(state.read_bytes(), old_record)
        m.repair_startup(self.home, True)
        m.uninstall(self.home, True)
        self.assertFalse(helper.exists())

    def test_startup_repair_manual_install_without_record(self):
        helper = self.home / m.LAUNCH_HELPER
        helper.write_bytes((m.ROOT / 'tests/fixtures/launch-before-startup-fix.lua.txt').read_bytes())
        m.repair_startup(self.home, True)
        self.assertEqual(helper.read_bytes(), (m.PAYLOAD / m.LAUNCH_HELPER).read_bytes())
        self.assertFalse((self.home / m.STATE).exists())

    def test_startup_repair_refuses_unknown_record(self):
        helper, state, record = self.broken_installation()
        record['files'][m.LAUNCH_HELPER]['after'] = 'unknown'
        state.write_text(json.dumps(record))
        before = (helper.read_bytes(), state.read_bytes())
        with self.assertRaisesRegex(ValueError, 'record does not match'):
            m.repair_startup(self.home, True)
        self.assertEqual((helper.read_bytes(), state.read_bytes()), before)


if __name__ == '__main__':
    unittest.main()
