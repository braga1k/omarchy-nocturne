-- Native, bounded handoff between the launcher surface and a real window.
-- No client resizing, compositor plugin, or persistent per-window overrides.
if nocturneLaunch then nocturneLaunch.cancel() end
local M = { token = '', phase = 'idle', remaining = 0, address = '', classes = {} }
nocturneLaunch = M
local HOLD, QUIET = 'nocturne-launch-held', 'nocturne-launch-handoff'

hl.window_rule({ name = 'nocturne-launch-hold', match = { tag = HOLD },
  opacity = '0 override 0 override 0 override', no_anim = true, no_shadow = true, no_blur = true })
hl.window_rule({ name = 'nocturne-launch-handoff', match = { tag = QUIET }, no_anim = true })
hl.layer_rule({ name = 'nocturne-launch-overlay', match = { namespace = '^nocturne-launch-morph$' }, no_anim = true })

local function tag(address, value)
  if address ~= '' and hl.get_window('address:' .. address) then
    hl.dispatch(hl.dsp.window.tag({ window = 'address:' .. address, tag = value }))
  end
end

function M.cancel(token)
  if token and token ~= M.token then return 'stale' end
  local address = M.address
  M.phase, M.address, M.remaining = 'idle', '', 0
  tag(address, '-' .. HOLD)
  tag(address, '-' .. QUIET)
  hl.exec_scheduled_prop_refresh_immediately()
  return 'ok'
end

local function matches(w)
  if not w or not w.mapped then return false end
  local class = string.lower(w.class or '')
  local initial = string.lower(w.initial_class or '')
  return M.classes[class] or M.classes[initial]
end

local function claim(w)
  if M.phase ~= 'armed' or not matches(w) then return end
  M.address, M.phase, M.remaining = w.address, 'held', 1800
  tag(M.address, '+' .. HOLD)
  hl.exec_scheduled_prop_refresh_immediately()
end

function M.arm(token, classes)
  M.cancel()
  if hl.get_config('animations.enabled') == false then return 'disabled' end
  M.token, M.classes = token, {}
  for _, value in ipairs(classes) do
    if type(value) == 'string' and #value > 1 then M.classes[string.lower(value)] = true end
  end
  if next(M.classes) == nil then return 'unsupported' end
  M.phase, M.remaining = 'armed', 7000
  return 'armed'
end

function M.status(token)
  if token ~= M.token then return 'stale' end
  if M.address == '' then return M.phase end
  local w = hl.get_window('address:' .. M.address)
  if not w or not w.mapped then M.cancel(token); return 'gone' end
  local at, size = w.at, w.size
  local gradient = hl.get_config('general.col:active_border')
  local border = tonumber(hl.get_config('general.border_size')) or 0
  local radius = tonumber(hl.get_config('decoration.rounding')) or 0
  local power = tonumber(hl.get_config('decoration.rounding_power')) or 2
  local colors = type(gradient) == 'table' and gradient.colors or {'0xFFABA7EB'}
  local function color(v) return '#' .. tostring(v):gsub('^0[xX]', '') end
  if w.fullscreen == 2 then border, radius = 0, 0 end
  return table.concat({M.phase, w.address, at.x, at.y, size.x, size.y, border, radius, power,
    color(colors[1]), color(colors[#colors]), type(gradient) == 'table' and gradient.angle or 0}, '\t')
end

function M.reveal(token)
  if token ~= M.token or M.phase ~= 'held' then return 'stale' end
  tag(M.address, '+' .. QUIET)
  tag(M.address, '-' .. HOLD)
  M.phase, M.remaining = 'handoff', 350
  hl.exec_scheduled_prop_refresh_immediately()
  return 'ok'
end

-- Execute in the compositor before the first render, rather than reacting
-- to a socket notification after the client may already have flashed.
hl.on('window.open_early', claim)
hl.on('window.open', claim)
hl.on('window.active', function(w)
  if M.phase == 'armed' and matches(w) then claim(w)
  elseif M.phase == 'held' and (not w or w.address ~= M.address) then M.cancel() end
end)
-- Reload replaces Lua state; static tags survive it, so clear our own tags.
local function cleanupTags()
  for _, w in ipairs(hl.get_windows()) do
    local owned = false
    for _, value in ipairs(w.tags or {}) do
      if value == HOLD or value == QUIET then owned = true end
    end
    if owned then tag(w.address, '-' .. HOLD); tag(w.address, '-' .. QUIET) end
  end
end
cleanupTags()
hl.on('config.reloaded', function() M.cancel(); cleanupTags() end)

-- A shell crash, canceled launcher or failed capture cannot strand a client.
-- The already-active, single-instance case may produce no activation event.
hl.timer(function()
  if M.phase == 'idle' then return end
  M.remaining = M.remaining - 100
  if M.phase == 'armed' and M.remaining <= 6600 then
    local w = hl.get_active_window()
    if matches(w) then claim(w) end
  end
  if M.remaining <= 0 then M.cancel() end
end, { timeout = 100, type = 'repeat' })

return M
