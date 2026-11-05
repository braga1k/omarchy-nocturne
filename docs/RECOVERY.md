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
- The complete installed configuration passes native `Hyprland --verify-config`.
- Lua regression tests separately model cold startup and offline verification,
  and reject the original helper in both cases. They also cover runtime handoff,
  timeout recovery, reduced motion and configuration reload.
- Temporary-home tests cover targeted repair, preservation of uninstall state,
  interruption/resumption, dry run and refusal of modified files.

A fresh SDDM login and physical reboot were not repeated as part of the release
verification. These tests do not certify every future Hyprland version.
