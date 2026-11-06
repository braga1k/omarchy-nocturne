"""Run production JavaScript callbacks against legacy and restricted capabilities."""
from pathlib import Path
import json
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LaunchApiTests(unittest.TestCase):
    def test_public_capability_and_failure_recovery(self):
        source = (ROOT / 'payload/.config/omarchy/ui/nocturne/LaunchMorph.qml').read_text()
        functions = '\n'.join(re.search(r'  function ' + name + r'\([^\n]*\) \{.*?\n  \}', source, re.S).group()
                              for name in ['launchNative', 'completeArm', 'finish'])
        script = '''
const assert = require('node:assert/strict');
const vm = require('node:vm');
function scenario(legacy, throws) {
  let launches=0, cancelled=0, refreshes=0;
  const api = {launch() { launches++; if(throws) throw Error('upstream failure'); }};
  if(legacy) { api.launchSerial=7; api.closeLaunchFeedback=()=>{throw Error('private API used')}; }
  // Stronger than undefined: any private read is a regression.
  const appLibrary = new Proxy(api, {get(obj,key) {
    if(key !== 'launch') throw Error('private API read: '+key);
    return obj[key];
  }});
  const context = vm.createContext({appLibrary, token:'current', active:true, phase:'arming',
    cancelTicket(){}, cancel(){cancelled++}, console:{warn(){}},
    Hyprland:{refreshToplevels(){refreshes++}}});
  vm.runInContext(FUNCTIONS, context);
  const request={id:'demo',label:'Demo',ticket:'current',launched:false};
  context.completeArm('current',request,'armed');
  assert.equal(launches,1);
  assert.equal(cancelled,throws?1:0);
  assert.equal(refreshes,throws?0:1);
  if(!throws) assert.equal(context.phase,'waiting');
  context.completeArm('old',request,'armed');
  assert.equal(launches,1,'stale completion cannot launch twice');
  context.finish();
  assert.equal(cancelled,throws?2:1);
}
scenario(true,false); scenario(false,false); scenario(false,true);
'''.replace('FUNCTIONS', json.dumps(functions))
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
