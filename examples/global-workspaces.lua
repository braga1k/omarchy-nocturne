-- User override: retain one global workspace sequence (Omarchy 4.5).
-- The bootstrap searches ~/.config before /usr/share/omarchy. This module
-- supplies the public binding helpers without per-monitor reconciliation.
-- No events, timers, dispatches or compositor reads during config loading.
local M = { slots = 10, nocturne_global = true }
local function action(fn, expression)
  o.bind_expressions[fn] = expression
  return fn
end
local function number(slot)
  assert(type(slot) == "number" and slot == math.floor(slot) and slot >= 1, "invalid workspace")
  return tostring(slot)
end
function M.workspace_id(_, slot) return tonumber(number(slot)) end
function M.focus(slot, _)
  local id = number(slot)
  return action(function() hl.dispatch(hl.dsp.focus({ workspace = id })) end,
    "o.workspaces.focus(" .. id .. ")")
end
function M.move_window(slot, follow)
  local id = number(slot)
  return action(function()
    hl.dispatch(hl.dsp.window.move({ workspace = id, follow = follow ~= false }))
  end, "o.workspaces.move_window(" .. id .. (follow == false and ", false" or "") .. ")")
end
function M.move_to_monitor(direction)
  return action(function()
    local target = hl.get_monitor(direction)
    local workspace = hl.get_active_workspace()
    if not target or not workspace or workspace.id < 1 then return end
    hl.dispatch(hl.dsp.workspace.move({ workspace = tostring(workspace.id), monitor = target.name }))
    hl.dispatch(hl.dsp.focus({ workspace = tostring(workspace.id) }))
  end, "o.workspaces.move_to_monitor(" .. string.format("%q", direction) .. ")")
end
function M.move_window_to_monitor(direction)
  return action(function()
    local target = hl.get_monitor(direction)
    if target then hl.dispatch(hl.dsp.window.move({ monitor = target.name })) end
  end, "o.workspaces.move_window_to_monitor(" .. string.format("%q", direction) .. ")")
end
function M.reconcile() end -- Global workspaces stay where the user places them.
o.workspaces = M
return M
