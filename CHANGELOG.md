# Changelog

## v1.0.2 — 2026-11-05

- Bound morph render-target allocation and skip unnecessary interior border shading; publish raw resource measurements and their limits.
- Stop the launch watchdog while idle and reactivate it for the next launch.
- Prevent the native keybinding scanner and key promoter from spinning in a Lua proxy loop.
- Recognize corroborated reverse-DNS Wayland identities, including T3 Code, without title matching.
- Return slow or unsupported launches to native feedback after 650 ms.

## v1.0.1 — 2026-11-05

Fix a startup crash in the launcher morph helper that could return users to the
login screen. Idle cancellation no longer refreshes compositor properties before
the input manager exists, and the watchdog starts only on the first valid launch
instead of during configuration loading.

- Add `python3 install.py repair-startup --apply` for existing installations.
  It replaces only the known affected helper and preserves uninstall backups.
- Add a [TTY recovery guide](docs/RECOVERY.md).
- Require Lua in CI. Separate cold-start and offline-verification regression
  tests detect both failures in the original helper; runtime recovery and
  interrupted repair are also covered. All 23 tests pass locally.
- The affected desktop was recovered through UWSM and native configuration
  verification passes. A fresh SDDM login and physical reboot were not repeated.

The affected version is the initial public commit `08dfe9d` from 4 November 2026,
which was published without a GitHub release tag. This is the first tagged patch
release. Earlier visual-review scores did not cover startup and are not evidence
that the affected version was safe to boot.
