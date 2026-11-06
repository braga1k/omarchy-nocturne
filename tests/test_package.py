from pathlib import Path
import hashlib
import json
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'payload'

class PackageTests(unittest.TestCase):
    def test_manifest_and_formats(self):
        actual = {}
        for path in PAYLOAD.rglob('*'):
            self.assertFalse(path.is_symlink(), str(path))
            if not path.is_file():
                continue
            actual[str(path.relative_to(PAYLOAD))] = hashlib.sha256(path.read_bytes()).hexdigest()
            if path.suffix == '.json':
                json.loads(path.read_text())
            elif path.suffix == '.toml':
                tomllib.loads(path.read_text())
        self.assertEqual(actual, json.loads((ROOT / 'payload.sha256.json').read_text()))

    def test_optional_grid_manifest_and_local_imports(self):
        payload = ROOT / 'optional/app-grid'
        actual = {str(p.relative_to(payload)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in payload.rglob('*') if p.is_file()}
        self.assertEqual(actual, json.loads((ROOT / 'optional/app-grid.sha256.json').read_text()))
        plugin = payload / '.config/omarchy/plugins/nocturne.dock'
        manifest = json.loads((plugin / 'manifest.json').read_text())
        self.assertEqual(manifest['id'], 'nocturne.dock')
        self.assertEqual(manifest['omarchy']['clonedFrom'], 'omarchy.dock')
        for entry in manifest['entryPoints'].values():
            self.assertTrue((plugin / entry).is_file())
        for qml in plugin.glob('*.qml'):
            for relative in re.findall(r'^import "([^"]+)"', qml.read_text(), re.M):
                path = (qml.parent / relative).resolve()
                if not path.exists():
                    path = PAYLOAD / path.relative_to(payload)
                self.assertTrue(path.exists(), str(path))
            self.assertNotIn('/home/b1k', qml.read_text())
            self.assertNotIn('b1k.', qml.read_text())

    def test_plugin_entry_points_exist(self):
        for path in PAYLOAD.rglob('manifest.json'):
            manifest = json.loads(path.read_text())
            self.assertTrue(manifest['id'].startswith('nocturne.'))
            self.assertTrue(manifest['omarchy']['clonedFrom'].startswith('omarchy.'))
            for relative in manifest['entryPoints'].values():
                self.assertTrue((path.parent / relative).is_file(), str(path.parent / relative))

    def test_readme_local_links_exist(self):
        for target in re.findall(r'\]\(([^)]+)\)', (ROOT / 'README.md').read_text()):
            if not target.startswith(('https://', '#')):
                self.assertTrue((ROOT / target).exists(), target)

    def test_personal_configuration_not_distributed(self):
        self.assertFalse((PAYLOAD / '.config/omarchy/shell.json').exists())
        self.assertFalse((PAYLOAD / '.config/hypr/hyprland.lua').exists())
        self.assertFalse(any(PAYLOAD.rglob('*.ttf')))
        self.assertFalse(any(PAYLOAD.rglob('*.bak')))
        self.assertFalse(any(PAYLOAD.rglob('*.original')))

if __name__ == '__main__':
    unittest.main()
