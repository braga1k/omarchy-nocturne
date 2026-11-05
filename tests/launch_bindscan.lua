-- Omarchy's source scanner supplies callable proxies for compositor APIs.
-- Bound the test so the original infinite ipairs loop fails without hanging CI.
local noop
noop = setmetatable({}, {
  __index = function() return noop end,
  __call = function() return noop end,
})
hl = setmetatable({get_config = function() return nil end}, {
  __index = function() return noop end,
})
debug.sethook(function() error('binding scan instruction budget exceeded') end, '', 100000)
local result = dofile(assert(arg[1]))
debug.sethook()
assert(type(result) == 'table' and next(result) == nil)
assert(nocturneLaunch == nil, 'scanner must not initialize the compositor bridge')
print('Binding scan completes without compositor side effects: ok')
