# Omarchy update compatibility

Omarchy 4.5 introduced a restricted application-library capability for plugins.
Nocturne v1.0.2 read the internal `launchSerial` property after launching an app.
That property is absent from the restricted API; QML threw
`Cannot assign [undefined] to int`, interrupting the transition to `waiting`.

The current renderer only calls the public `launch(id, name)` method. Native
launch feedback manages its own lifecycle. An exception in that launch call
cancels the visual state; it does not retry or duplicate the app launch.
The helper watchdog and the existing 650 ms unknown/slow-window fallback remain.

The update also changed the default Apps route into an action opening the dock
grid. Nocturne adapts that default to its own Apps submenu, preserving the row
that originates the morph. Explicit user actions/redirects still override this
default. No packaged Omarchy files are edited.

## After future updates

New installations include `~/.config/omarchy/hooks/post-update.d/nocturne-check.sh`.
Omarchy runs it after update migrations and restarts. It checks the loaded menu's
public capabilities and Apps route, the compositor helper's functions, and
Hyprland configuration errors. It records fingerprints of the relevant upstream
files. A changed dependency triggers a notification even if capability checks
pass, since method availability alone cannot prove visual behaviour.

Run it manually after updates made outside `omarchy update`:

```sh
python3 ~/.local/lib/omarchy-nocturne/check-compatibility.py
```

The report is saved privately to
`~/.local/state/omarchy-nocturne/compatibility.json` (or `$XDG_STATE_HOME`).
Each external command has an eight-second deadline. There is no resident process,
network access, package pinning, config rewrite or automatic rollback.

A shell that has not instantiated the menu reports **pending**, not success.
Open Super+Space once, then repeat the check. A removed diagnostic method may
also appear pending; this is not a compatibility approval. Failures return a
nonzero exit status and the hook sends a desktop notification when available.

For an existing installation, follow the checked complete-update procedure in
[RECOVERY.md](RECOVERY.md). `git pull` and `repair-startup` do not update the QML
renderer. Keep personal changes and uninstall backups. The installer's broad
version gate remains conservative: launch validation on 4.5 does not certify
every panel, provider or new upstream feature.

## Verification and limits

Regression tests execute the production launch callbacks against a restricted
capability, reject private-property reads, and check failure cleanup and duplicate
launch protection. Menu tests cover old/new defaults and explicit user overrides.
The diagnostic tests cover missing capabilities, configuration errors, timeouts
and lazy loading. Existing startup, keybinding scanner and installer tests remain.

On Omarchy 4.5.0-3, Hyprland 0.56.2-4 and Quickshell 0.3.2.r7.g2b4501a-1,
the old QML reproduced the reported exception in an isolated process. Corrected
QML passed delayed/stale callback, cancellation and fallback tests. Native
launches are checked on two outputs at full, half and quarter tiled sizes.
These tests do not certify future API semantics, all applications, physical
360 Hz presentation or a new login/reboot.

## Workspaces and the optional grid

Omarchy 4.5 gives each monitor ten numbered workspaces. The widget now reads the
monitor assignments, highlights the workspace on that output, and routes a click
to the corresponding native helper. Without assignments it uses global numbers.
An explicit `"perMonitor": false` on the widget's bar layout entry selects global
labels; this setting alone does **not** change the compositor's workspace model.
The optional [global-workspace example](GLOBAL-WORKSPACES.md) is separate and is
never installed automatically. Global labels keep IDs above ten distinct.

`check-compatibility.py --workspaces` compares each bar with live compositor
state. `--global-workspaces` additionally checks the local global helper marker
and rejects a bar that has reverted to per-monitor mode. `--dock` checks the
optional Nocturne grid service. These flags require those local components.

The Super+Alt+Space clone is distributed under `optional/app-grid` and installed
only with `install.py install --app-grid`. On 4.5 the explicit `--allow-untested`
version override remains necessary. The installer verifies its separate SHA-256
manifest and native dock/AppLibrary dependencies. It records the extra files in
the same private recovery transaction; uninstall includes them automatically.
The native dock IPC route and keybinding remain unchanged. Shared motion supports
an icon-only source, explicit icon decoding size and reduced-motion mode.

## New bar sections on 4.5

Nocturne's current bar clone renders `left`, `center`, and `right`. Native 4.5
also has `centerBegin`, `centerEnd`, and `tray`. A fresh 4.5 default configuration
uses these sections, so it is **not a drop-in target** for this release. The
installer refuses nonempty unsupported sections before writing, even with
`--allow-untested`. It does not silently discard those widgets.

If you choose this customization, back up your shell configuration and use the
native bar settings to place the widgets you want in `left`, `center`, or `right`;
leave unsupported sections empty. Review that layout before running the dry run
again. Independent side sections and the native tray drawer are not provided by
this clone. Existing three-section Nocturne layouts, including the development
machine, do not have this migration issue. Full native 4.5 bar parity is future work.

## Offline verification on 4.5

The separately launched `Hyprland --verify-config` crashed while cleaning up a
timer created by native `default/hypr/startup-cursor.lua:92`. It reproduced with
both the native workspace module and the optional global example. A temporary
verification-only config setting `omarchy_startup_cursor_pending=false` before
loading the actual config parsed successfully. That workaround was not installed.
The running desktop remained active, and reload/configerrors passed. This is a
separate observation from the Nocturne startup defect fixed in v1.0.1; it does
not demonstrate a new login failure. No new login or reboot was certified.
