# Recover from the initial launch-helper startup crash

The initial public commit (`08dfe9d`, 4 November 2026) can prevent the Hyprland
session from starting after login. **v1.0.1 fixes this failure.** Pulling the
repository alone does not update an already installed helper.

The helper refreshed window properties from `config.reloaded` even when it had
no window. Hyprland emits that event during startup, before its input manager
exists. The resulting call reached `CInputManager::setKeyboardLayout()` and
crashed the session. The initial helper also created its watchdog while loading
configuration; offline `--verify-config` has no event loop for that timer.

## Apply the targeted repair

If login returns to the greeter, press **Ctrl+Alt+F2** and log in as your normal
user. If the desktop still works, the same repair can be run from a terminal.
Do not use `sudo`.

From your Nocturne checkout:

```sh
git pull --ff-only
python3 install.py repair-startup          # dry run
python3 install.py repair-startup --apply
Hyprland --verify-config
```

If you no longer have the checkout, clone the repository into a new directory
first. Confirm that verification ends with `config ok` before starting a session.
From the TTY, return to your login screen and log in, or use the Omarchy session
command `uwsm start hyprland.desktop`. If the desktop is already running, use
`hyprctl reload` followed by `hyprctl configerrors`; a reboot is not required to
load the repaired helper.

The repair replaces **only** `~/.config/hypr/nocturne-launch.lua`, and only if its
hash matches the known broken version or the corrected version. It preserves
your theme, monitors, shell preferences and the original uninstall backups.
When an installation record exists, the repair updates that helper's installed
hash so uninstall continues to work. Manual installations without a record are
also supported for those exact helper versions; no synthetic uninstall record
is created.

If updating the installation record fails after the helper was fixed, rerun the
same command. It accepts the corrected helper and finishes updating the record;
it never reinstalls the broken helper as a rollback. Do not delete the record.

## If your helper has local edits

The command refuses unknown contents or inconsistent installation records before
writing. Preserve those edits. Back up your Hyprland configuration and temporarily
comment out the `require("hypr.nocturne-launch")` line in your user
`~/.config/hypr/hyprland.lua` if you need to regain access. This disables the launch
morph. Compare your helper with the corrected payload before enabling that line
again; do not restore the original broken helper from a backup.

## What was verified

- The reported cold-start failure was diagnosed from the compositor backtrace.
- The affected installation returned to the desktop through UWSM after repair.
- On the 4.0.6 recovery environment, the complete installed configuration passed native `Hyprland --verify-config`.
- Lua regression tests separately model cold startup and offline verification,
  and reject the original helper in both cases. They also cover runtime handoff,
  timeout recovery, reduced motion and configuration reload.
- Temporary-home tests cover targeted repair, preservation of uninstall state,
  interruption/resumption, dry run and refusal of modified files.

A fresh SDDM login and physical reboot were not repeated as part of the release
verification. These tests do not certify every future Hyprland version.

## Updating the renderer and other files

`repair-startup` updates only the helper; it does not install a new renderer or menu. For a complete update, use the installer’s checked uninstall/reinstall flow from a terminal:

```sh
git pull --ff-only
python3 install.py uninstall         # inspect; refuses modified managed files
python3 install.py uninstall --apply
python3 install.py install           # inspect the new installation
python3 install.py install --apply
hyprctl reload
hyprctl configerrors
omarchy restart shell
```

Keep the installation record and original backups. If uninstall reports a conflict, preserve and reconcile your local edits before proceeding; do not delete the state or force overwrite. The original preferences are restored by uninstall and merged again by install. Changes made to managed files since installation require that explicit reconciliation. Manual installations should compare the payload and preserve their own backups.

## v1.1.0 and Omarchy 4.5

Read [4.5 compatibility](UPDATE-COMPATIBILITY.md) before uninstalling. The new bar
sections are not supported by this clone: if your original pre-Nocturne layout
uses them, prepare a compatible layout or postpone the update. Preserve your
current settings and the installation record before changing anything.

For a compatible 4.5 layout, use `install --allow-untested --app-grid` for the dry
run and `install --allow-untested --app-grid --apply` for the install steps above
if you want the new grid. Omit `--app-grid` to keep the native service. Uninstall
uses the recorded file list and needs no grid flag. The global workspace example
is a separate manual preference and is not affected by uninstall.

The native 4.5 offline verifier has a separately reproduced cursor-timer crash;
see the compatibility note. A verifier crash is not itself evidence that the
running desktop or Nocturne launch helper crashed. Keep the current session while
checking `hyprctl reload` and `hyprctl configerrors`.
