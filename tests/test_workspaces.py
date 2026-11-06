from pathlib import Path
import json
import subprocess
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]


def function(source, name):
    start = source.index('function ' + name + '(')
    opening = source.index('{', start)
    depth, quote, escaped = 0, None, False
    for i in range(opening, len(source)):
        c = source[i]
        if quote:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == quote:
                quote = None
        elif c in ['"', "'"]:
            quote = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return source[start:i+1]
    raise ValueError(name)


class WorkspaceTests(unittest.TestCase):
    def test_global_example_cold_load_and_binding_contracts(self):
        lua = shutil.which('lua') or shutil.which('lua5.4')
        self.assertIsNotNone(lua, 'Lua is required for workspace contracts')
        result = subprocess.run([lua, str(ROOT / 'tests/global_workspaces.lua'),
                                 str(ROOT / 'examples/global-workspaces.lua')],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_per_monitor_labels_selection_and_click_routing(self):
        source = (ROOT / 'payload/.config/omarchy/plugins/nocturne.workspaces/Workspaces.qml').read_text()
        functions = '\n'.join(function(source, name) for name in
                              ['readBlocks','blockOf','slotOf','labelOf','activeWorkspaceId','workspaceIds','focusWorkspace'])
        script = '''
const vm=require('node:vm'), assert=require('node:assert/strict');
let commands=[];
const context=vm.createContext({slots:10,block:1,perMonitor:true,monitorName:'DP-1',
 monitor:{activeWorkspace:{id:14}},bar:{run(s){commands.push(s)}},
 Util:{shellQuote:JSON.stringify},Hyprland:{focusedWorkspace:{id:1},workspaces:{values:[
 {id:1,monitor:{name:'HDMI-A-1'}},{id:14,monitor:{name:'DP-1'}},
 {id:18,monitor:{name:'DP-1'}},{id:21,monitor:{name:'DP-1'}},
 {id:-99,monitor:{name:'DP-1'}},{id:31,monitor:{name:'other'}}]}}});
context.root=context;vm.runInContext(FUNCTIONS,context);
context.readBlocks('0\\tHDMI-A-1\\tDisplay A\\n1\\tDP-1\\tDisplay B\\nnope\\tbad\\tBroken\\n');
assert.equal(context.blocks['DP-1'],1);assert.equal(context.blocks.bad,undefined);
assert.deepEqual(Array.from(context.workspaceIds()),[11,12,13,14,15,18,21]);
assert.equal(context.activeWorkspaceId(),14);
assert.equal(context.slotOf(14),4);assert.equal(context.slotOf(20),10);
context.focusWorkspace(18);assert.equal(commands.pop(),'hyprctl dispatch '+JSON.stringify('o.workspaces.focus(8, "DP-1")'));
context.focusWorkspace(21);assert.ok(commands.pop().includes('21'));
context.perMonitor=false;context.block=0;
assert.deepEqual(Array.from(context.workspaceIds()),[1,2,3,4,5,14,18,21,31]);
assert.equal(context.labelOf(14),"14");assert.equal(context.labelOf(10),"0");
assert.equal(context.activeWorkspaceId(),1);
context.focusWorkspace(2);assert.ok(!commands.pop().includes('o.workspaces'));
'''.replace('FUNCTIONS', json.dumps(functions))
        result = subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
