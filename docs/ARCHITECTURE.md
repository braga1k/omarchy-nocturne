# Architecture

`payload/.config/omarchy/plugins/nocturne.*` contains local clones. Their manifests retain `omarchy.clonedFrom`, so native shell routes continue to work. Shared visual components live in `ui/nocturne`. The theme changes colour, spacing and type-size tokens; it does not ship fonts or a wallpaper.

`hypr/nocturne-motion.lua` configures native window/workspace motion and card blur. `hypr/nocturne-launch.lua` coordinates a bounded window handoff. The installer's marked require block is inserted before persisted GUI settings/toggles when those native markers exist, preserving their precedence.

## Launch bridge

1. Capture the selected row's geometry, icon decoding size and text metrics.
2. Arm the native helper with a request token and the desktop entry's ID / startup class.
3. Launch through Omarchy's application library.
4. Hold the matching window invisibly while obtaining its real destination and capture.
5. Prepare overlay surfaces and content on the origin and destination outputs.
6. Animate geometry with a damped spring; reveal unscaled application content through the expanding surface.
7. Match the native border width, colours and corner profile; reveal the real window and fade the overlay.

Each asynchronous process owns its request ticket. Old completions cannot cancel a newer launch. Input belongs to the launcher only while it is logically open. Reopening, unrelated focus and external tiling changes cancel the bridge. The compositor-side watchdog releases held clients if the presenter disappears.

The border uses the active global decoration settings. The public package does not claim complete support for application-specific decoration overrides or gradients with more than two stops. No client resizing or persistent per-window tags are required.

Configuration loading must be safe before the input and event-loop managers
exist. An idle cancellation does not force a property refresh. The watchdog is
created lazily on the first supported, animation-enabled launch request, then
reused. `config.reloaded` alone must never initialize that timer. See the
[startup incident and targeted recovery](RECOVERY.md).

## Shortcut presentation

The native command still enumerates bindings and dispatches the chosen action. The menu only separates the displayed `keys → action` text into an action label and keycaps. Selection returns the original input string, including its spacing, to preserve the caller's record lookup. Generic dmenu selectors retain their normal presentation.

## Installation state

The Python installer writes only the listed payload, a merged `shell.json`, and a marked block in `hyprland.lua`. Its private state file stores original bytes, modes and installed hashes. Uninstall validates every path before writing and refuses conflicts. Symlink parents and path traversal are rejected. Theme activation remains the native Omarchy command and must be reverted separately.

## Launcher compatibility

The Lua helper declines Omarchy’s keybinding-scanner context, whose callable table stubs are not compositor APIs. This prevents an unbounded proxy iteration during shortcut discovery. Exact window classes remain preferred. A reverse-DNS Wayland class may match a short desktop class only when its leaf, the selected executable basename and `/proc/PID/comm` agree. Unverified identities use native launch feedback. A 650 ms waiting budget releases the row overlay for slow or unsupported launches without canceling the application launch.

## Bounded renderer resources

The morph uses a fixed native-resolution intermediate surface for each destination, with the existing overshoot allowance. The shader samples the visible portion without scaling the content; fully covered interior fragments skip border-gradient work. The inactive source is released. The watchdog remains lazily constructed and is disabled after cancel/finish, then re-enabled on the next supported arm. No idle compositor timer is created at config load. See PERFORMANCE.md for measured effects and limitations.
