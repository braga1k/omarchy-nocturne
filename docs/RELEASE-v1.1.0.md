# v1.1.0 — Omarchy 4.5 launcher recovery and optional app grid

## Changes

- Fix the Super+Space launch morph after Omarchy introduced its restricted plugin
  application-library API. Remove private launchSerial/feedback dependencies;
  keep one native launch per request and bounded fallback/recovery.
- Keep the native Apps default inside the Nocturne menu, while preserving explicit
  user overrides.
- Add an **optional Super+Alt+Space grid** (`--app-grid`): organic opening/closing,
  adaptive height and an icon-to-window morph from the activated item. Click and
  Enter share the path; input is released immediately on close; reduced motion
  bypasses the morph. Native dock pins/options and explicit disables are kept.
- Correct workspace numbering, selection and click routing for 4.5 per-monitor
  IDs. Provide an opt-in global-sequence example; no monitor assignments or
  automatic renumbering are distributed.
- Add a bounded post-update compatibility diagnostic, private report and upstream
  fingerprints. Optional checks cover the grid and workspace indicators.
- Verify optional payload hashes and include its files in the existing install /
  rollback / uninstall transaction. Refuse unsupported nonempty bar sections
  before writing, rather than silently dropping their widgets.

## Compatibility and upgrading

This is **not a full port of the shell to Omarchy 4.5**. The Nocturne bar supports
three sections (`left`, `center`, `right`). New native `centerBegin`, `centerEnd`
and `tray` sections must be empty before installation. The version gate remains
conservative; the tested 4.5 paths require an explicit `--allow-untested` override.

Read [compatibility](UPDATE-COMPATIBILITY.md) and [update/recovery](RECOVERY.md)
**before uninstalling an older release**. For a compatible 4.5 installation,
select `--app-grid` on both the install dry run and apply command to include the
new grid. Pulling alone or running `repair-startup` does not update the renderer.
Uninstall refuses files changed since installation; retain the recovery record.

The optional [global workspace module](GLOBAL-WORKSPACES.md) is a separate manual
preference. No personal shell settings, monitor rules, wallpaper or fonts are
included. Earlier startup, shortcut and rendering fixes remain in place.

## Evidence and limits

Native checks on Omarchy 4.5.0-3 / Hyprland 0.56.2-4 / Quickshell
0.3.2.r7.g2b4501a-1 covered full/half/quarter destinations on two monitors for
both launchers. Grid checks covered click/Enter, Escape, empty search and three
interruption cycles per monitor. Workspace checks covered 14 per-monitor cases
and 14 global cases, reload persistence and preservation of existing windows.

**42 automated tests pass locally.** Inert tests cover restricted launch capabilities, routes, stale/failing callbacks,
optional installation/uninstall, hashes, preferences, unsupported layouts and
diagnostic failures. Recordings are 60 FPS; physical key-chord injection,
360 Hz presentation, input latency and a fresh login/reboot are not certified.
Historical council scores are not a new review of this release.

The separate native 4.5 offline verifier has a reproduced cursor-timer teardown
crash, also with native workspace code; the running session and live reload checks
passed. See [the diagnostic distinction](UPDATE-COMPATIBILITY.md#offline-verification-on-45).
