#!/usr/bin/env python3
"""Bounded, read-only desktop checks. Never launch apps or rewrite config."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=8)
    if result.returncode:
        raise RuntimeError(f'{args[0]} exited {result.returncode}: {result.stderr.strip()[:300]}')
    return result.stdout.strip()


def check(include_dock=False, include_workspaces=False, include_global=False):
    issues = []
    def attempt(label, action):
        try:
            return action()
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            issues.append(f'{label}: {error}')
            return None

    raw_menu = attempt('menu', lambda: run(['omarchy', 'shell', 'shell', 'call',
                                           'omarchy.menu', 'inspectCompatibility', '']))
    # Panels are lazy-loaded after restart. Do not summon one over the user's
    # desktop, or mistake an uninstantiated panel for a broken installation.
    pending = raw_menu == 'unknown'
    menu = attempt('menu response', lambda: json.loads(raw_menu or 'null')) if not pending else None
    if not pending and (not isinstance(menu, dict) or menu.get('contract') != 1 or menu.get('ok') is not True or menu.get('morph') is not True):
        issues.append('Nocturne menu capability contract unavailable or incomplete')
    helper = attempt('helper', lambda: run(['hyprctl', 'repl',
        'return type(nocturneLaunch) == "table" and type(nocturneLaunch.arm) == "function" and type(nocturneLaunch.cancel) == "function" and type(nocturneLaunch.status) == "function" and type(nocturneLaunch.reveal) == "function"']))
    if helper != 'true':
        issues.append('Nocturne compositor helper unavailable or incomplete')
    errors = attempt('configuration', lambda: run(['hyprctl', 'configerrors']))
    if errors:
        issues.append('Hyprland configuration: ' + errors[:500])
    dock = None
    if include_dock:
        dock = attempt('dock', lambda: json.loads(run(['omarchy', 'shell', 'omarchy.dock', 'inspect'])))
        if not isinstance(dock, dict) or dock.get('phase') not in ['idle', 'arming', 'waiting', 'capturing', 'moving', 'handoff', 'fallback'] or not isinstance(dock.get('active'), bool):
            issues.append('Nocturne app grid unavailable or incomplete')
    workspaces = []
    if include_global:
        global_mode = attempt("global workspace helpers", lambda: run(["hyprctl", "repl", "return type(o.workspaces) == \"table\" and o.workspaces.nocturne_global == true"]))
        if global_mode != "true":
            issues.append("Global workspace preference is not active in the compositor")
    if include_workspaces or include_global:
        monitors = attempt('monitors', lambda: json.loads(run(['hyprctl', '-j', 'monitors'])))
        if not isinstance(monitors, list) or not monitors:
            issues.append('Monitor state unavailable')
        else:
            focused = next((m for m in monitors if m.get('focused')), {})
            for monitor in monitors:
                name = monitor.get('name', '')
                state = attempt('workspaces ' + name, lambda: json.loads(run([
                    'omarchy', 'shell', 'nocturne.workspaces.' + name, 'inspect'])))
                workspaces.append(state)
                if not isinstance(state, dict):
                    issues.append('Nocturne workspace diagnostic unavailable: ' + name)
                    continue
                if include_global and state.get('perMonitor') is not False:
                    issues.append('Global workspace preference is not active in the bar: ' + name)
                expected = (monitor if state.get('perMonitor') else focused).get('activeWorkspace', {}).get('id')
                selected = [b.get('id') for b in state.get('buttons', []) if b.get('focused')]
                if state.get('active') != expected or selected != [expected]:
                    issues.append('Workspace highlight differs from compositor: ' + name)
    upstream = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy'))
    fingerprints = {}
    for relative in ['shell/services/AppLibrary.qml', 'shell/services/PluginAppLibraryApi.qml',
                     'shell/shell.qml', 'default/omarchy/omarchy-menu.jsonc',
                     'shell/plugins/dock/AppGrid.qml', 'shell/plugins/dock/Dock.qml',
                     'shell/Commons/Style.qml', 'shell/plugins/bar/widgets/Workspaces.qml',
                     'default/hypr/monitor-workspaces.lua']:
        path = upstream / relative
        if path.is_file():
            fingerprints[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'ok': False if issues else (None if pending else True), 'issues': issues, 'menu': menu,
            'pending': pending, 'dock': dock, 'workspaces': workspaces, 'upstream': fingerprints,
            'scope': 'Live capability/configuration checks only; no visual, launch or reboot certification'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notify', action='store_true', help='Notify on failure or changed upstream dependencies')
    parser.add_argument('--dock', action='store_true', help='Also require the optional Nocturne app-grid diagnostic')
    parser.add_argument('--workspaces', action='store_true', help='Compare each workspace indicator with the compositor')
    parser.add_argument('--global-workspaces', action='store_true', help='Also require the explicit global workspace preference')
    args = parser.parse_args()
    report = check(include_dock=args.dock, include_workspaces=args.workspaces, include_global=args.global_workspaces)
    directory = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'omarchy-nocturne'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'compatibility.json'
    try:
        previous = json.loads(path.read_text())
    except (OSError, ValueError):
        previous = {}
    report['upstream_changed'] = bool(previous.get('upstream')) and previous['upstream'] != report['upstream']
    fd, temporary = tempfile.mkstemp(prefix='.compatibility-', dir=directory)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(json.dumps(report, indent=2))
    if args.notify and (not report['ok'] or report['upstream_changed']):
        message = ('Compatibility check failed. ' if report['issues'] else
                   'Open Super+Space once, then rerun this check to validate the menu API. ' if report['pending'] else
                   'Omarchy dependencies changed; capability checks passed. Verify the launch animation. ')
        try:
            run(['notify-send', '--app-name=Omarchy Nocturne', 'Nocturne update check', message + str(path)])
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            pass
    return 1 if report['issues'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
