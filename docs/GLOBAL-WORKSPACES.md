# Optional global workspace sequence

Omarchy 4.5 uses ten workspace slots per monitor. Nocturne follows that model by
default. `examples/global-workspaces.lua` is an **opt-in user override** for one
global numeric sequence. The installer does not enable it or assign monitors.

The module provides the binding helpers that Omarchy's native shortcuts call,
without the per-monitor reconciliation hooks. It performs no dispatch, timer
creation or compositor reads while loading. It does not change the launch helper.

To adopt it on the tested 4.5 layout:

1. Back up your shell/Hyprland configuration and any existing
   `~/.config/default/hypr/monitor-workspaces.lua`. Do not overwrite an existing
   custom module without reconciling it.
2. Copy `examples/global-workspaces.lua` to that path. Omarchy's bootstrap loads
   user modules before package defaults.
3. In `~/.config/omarchy/shell.json`, add `"perMonitor": false` directly to the
   `nocturne.workspaces` layout entry, alongside `"id"`. It is not nested under
   a `settings` object. For example:

   ```json
   { "id": "nocturne.workspaces", "perMonitor": false }
   ```

4. Run `hyprctl reload`, then `hyprctl configerrors`, and restart the shell with
   `omarchy restart shell`. Confirm both bars and Super+number select the same
   global IDs. Each monitor still displays its own active workspace; this is not
   screen mirroring.
5. Run the diagnostic after opening Super+Space once:

   ```sh
   python3 ~/.local/lib/omarchy-nocturne/check-compatibility.py --global-workspaces
   ```

Existing IDs (for example 11–14) are **not renumbered automatically**. The bar shows
their actual global numbers. Monitor placement and optional renumbering are your
own preferences and are intentionally absent from the example. If enabling this
at first login, set your desired default workspace/monitor rules separately.

To return to native per-monitor workspaces, restore your previous module (or
remove only the example you installed), remove the `perMonitor` override from the
widget, and reload Hyprland and the shell. Native reconciliation can renumber
existing workspaces. Preserve later edits before restoring any backup. A future
upstream change to the binding contract may require updating this example.
