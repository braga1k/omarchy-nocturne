-- Model the cold-start lifecycle: input/event-loop managers are unavailable
-- while config is loaded, then become available before a real launch.
local events, timers, windows = {}, {}, {}
local ready, refreshes, animations = false, 0, true
local timerReady = arg[2] == 'cold-start'
hl = {
  window_rule = function() end,
  layer_rule = function() end,
  on = function(name, callback) events[name] = callback end,
  get_windows = function() return windows end,
  get_window = function(selector)
    for _, w in ipairs(windows) do
      if selector == 'address:' .. w.address then return w end
    end
  end,
  get_active_window = function() return windows[1] end,
  get_config = function() return animations end,
  dsp = { window = { tag = function(value) return value end } },
  dispatch = function(value)
    local w = hl.get_window(value.window)
    local label = value.tag:sub(2)
    if value.tag:sub(1, 1) == '+' then w.tags[label] = true
    else w.tags[label] = nil end
  end,
  exec_scheduled_prop_refresh_immediately = function()
    assert(ready, 'property refresh before input manager exists')
    refreshes = refreshes + 1
  end,
  timer = function(callback, opts)
    assert(timerReady, 'timer before event-loop manager exists')
    assert(opts.timeout == 100 and opts.type == 'repeat')
    timers[#timers + 1] = callback
    return {}
  end,
}
local m = dofile(assert(arg[1]))
events['config.reloaded']()
assert(m.phase == 'idle' and refreshes == 0 and #timers == 0)
ready = true
timerReady = true
assert(m.arm('unsupported', {}) == 'unsupported' and #timers == 0)
animations = false
assert(m.arm('reduced-motion', {'app'}) == 'disabled' and #timers == 0)
animations = true
assert(m.arm('one', {'app'}) == 'armed' and #timers == 1)
windows[1] = {address = '0x123', class = 'app', mapped = true, tags = {}}
events['window.open_early'](windows[1])
assert(m.phase == 'held' and windows[1].tags['nocturne-launch-held'])
assert(m.cancel('stale') == 'stale' and m.phase == 'held')
assert(m.reveal('one') == 'ok' and not windows[1].tags['nocturne-launch-held'])
for _ = 1, 4 do timers[1]() end
assert(m.phase == 'idle' and not windows[1].tags['nocturne-launch-handoff'])
assert(m.arm('two', {'app'}) == 'armed' and #timers == 1)
events['window.open_early'](windows[1])
for _ = 1, 18 do timers[1]() end
assert(m.phase == 'idle' and not windows[1].tags['nocturne-launch-held'])
assert(m.arm('three', {'app'}) == 'armed')
events['window.open_early'](windows[1])
events['config.reloaded']()
assert(m.phase == 'idle' and not windows[1].tags['nocturne-launch-held'])
print('Cold start, reduced motion, handoff, watchdog and reload: ok')
