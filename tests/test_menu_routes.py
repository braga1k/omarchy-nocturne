from pathlib import Path
import json
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MenuRouteTests(unittest.TestCase):
    def test_apps_stays_native_to_nocturne_and_user_override_wins(self):
        source = (ROOT / 'payload/.config/omarchy/plugins/nocturne.menu/MenuModel.js').read_text()
        script = '''
const vm=require('node:vm'), assert=require('node:assert/strict');
const context=vm.createContext({}); vm.runInContext(SOURCE,context);
for(const action of ['', 'omarchy-shell omarchy.dock apps']) {
  const defaults=context.parseMenuJsonc(JSON.stringify({apps:{label:'Apps',provider:'apps',action,aliases:['app']}}));
  const merged=context.mergeMenuSources(defaults,[]);
  assert.equal(merged.items.apps.kind,'menu');
  assert.equal(merged.items.apps.action,'');
  assert.equal(merged.items.apps.provider,'apps');
  assert.equal(context.resolveRoute(merged.items,merged.itemOrder,'app'),'apps');
  assert.equal(defaults[0].action,action,'input stays unchanged');
  const user=context.parseMenuJsonc(JSON.stringify({apps:{action:'custom-launcher'}}));
  const custom=context.mergeMenuSources(defaults,user);
  assert.equal(custom.items.apps.action,'custom-launcher');
  assert.equal(custom.items.apps.kind,'action');
}
'''.replace('SOURCE', json.dumps(source))
        result = subprocess.run(['node','-e',script], capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
