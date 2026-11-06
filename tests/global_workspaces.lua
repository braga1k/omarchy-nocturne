local events = {}
o = {bind_expressions = {}}
local function command(kind)
  return function(args) return {kind = kind, args = args} end
end
hl = {
  dsp = {focus = command('focus'), window = {move = command('move-window')},
         workspace = {move = command('move-workspace')}},
  dispatch = function(value) events[#events+1] = value end,
  get_monitor = function() return {name='DP-1'} end,
  get_active_workspace = function() return {id=2} end,
  timer = function() error('unexpected startup timer') end,
  on = function() error('unexpected event registration') end,
}
local module = dofile(assert(arg[1]))
assert(module.nocturne_global and #events == 0)
for _, monitor in ipairs({'HDMI-A-1','DP-1'}) do
  for i=1,10 do
    assert(module.workspace_id(monitor,i)==i)
    local action=module.focus(i,monitor)
    assert(o.bind_expressions[action]=='o.workspaces.focus('..i..')')
    action();assert(events[#events].args.workspace==tostring(i))
  end
end
module.move_window(3,false)();assert(events[#events].args.follow==false)
module.move_window(3)();assert(events[#events].args.follow==true)
module.move_to_monitor('r')();assert(events[#events-1].args.monitor=='DP-1')
assert(events[#events].args.workspace=='2')
module.move_window_to_monitor('r')();assert(events[#events].args.monitor=='DP-1')
local count=#events;hl.get_monitor=function() return nil end
module.move_to_monitor('r')();module.move_window_to_monitor('r')();module.reconcile()
assert(#events==count)
print('PASS: global IDs/binding expressions/movement/no-monitor fallback; no startup timers or reconciliation')
