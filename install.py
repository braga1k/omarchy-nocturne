#!/usr/bin/env python3
"""User-local Nocturne installation. Dry run by default; no sudo or network."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / 'payload'
STATE = '.local/state/omarchy-nocturne/install.json'
LAUNCH_HELPER = '.config/hypr/nocturne-launch.lua'
BROKEN_LAUNCH_SHA256 = '785701d2993f367c34d22bd499cdd757518b316f26fc112c04ccad2758bbb887'
STARTUP_FIXED_LAUNCH_SHA256 = '80c7ca7aae9ef57c6ec56025f12632329882c51bfbce98b5d281869dcaf3b5fb'
BEGIN = '-- BEGIN OMARCHY NOCTURNE'
END = '-- END OMARCHY NOCTURNE'
BLOCK = BEGIN + '\nrequire("hypr.nocturne-motion")\nrequire("hypr.nocturne-launch")\n' + END + '\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(home, relative):
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError(f'Unsafe path: {relative}')
    path = home / rel
    for part in [path, *path.parents]:
        if part == home:
            break
        if part.is_symlink():
            raise ValueError(f'Refusing symlink: {part}')
    return path


def atomic(path, data, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode is None:
        mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, name = tempfile.mkstemp(prefix='.nocturne-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def plugin_specs():
    return [json.loads(p.read_text()) for p in sorted((PAYLOAD / '.config/omarchy/plugins').glob('*/manifest.json'))]


def merge_shell(config):
    result = copy.deepcopy(config)
    bar = result.setdefault('bar', {})
    layout = bar.setdefault('layout', {})
    plugins = result.setdefault('plugins', [])
    disabled = result.setdefault('disabledPlugins', [])
    restores = result.setdefault('cloneSourceRestores', [])
    bar['id'] = 'nocturne.bar'
    bar['autoHide'] = False
    bar['transparent'] = True
    for spec in plugin_specs():
        source = spec.get('omarchy', {}).get('clonedFrom')
        if not source or 'bar' in spec['kinds']:
            continue
        target = spec['id']
        found = False
        for entries in [*layout.values(), plugins]:
            for index, entry in enumerate(entries):
                eid = entry if isinstance(entry, str) else entry.get('id')
                if eid == source:
                    entries[index] = {'id': target} if isinstance(entry, str) else {**entry, 'id': target}
                    found = True
                elif eid == target:
                    found = True
        # Preserve absent widgets. Non-widget plugins replace built-in services.
        if 'bar-widget' not in spec['kinds'] and not found and source not in disabled:
            plugins.append({'id': target})
            found = True
        if found and any(k != 'bar-widget' for k in spec['kinds']) and source not in disabled:
            disabled.append(source)
            if target not in restores:
                restores.append(target)
        if bar.get('centerAnchor') == source:
            bar['centerAnchor'] = target
    return result


def prepare(home, stock):
    expected = json.loads((ROOT / 'payload.sha256.json').read_text())
    actual = {str(p.relative_to(PAYLOAD)): digest(p.read_bytes()) for p in PAYLOAD.rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('Payload differs from payload.sha256.json. Use a complete release checkout.')
    files = {}
    for src in sorted(PAYLOAD.rglob('*')):
        if src.is_file():
            rel = str(src.relative_to(PAYLOAD))
            dest = safe_path(home, rel)
            if dest.exists() and dest.read_bytes() != src.read_bytes():
                raise ValueError(f'Existing custom file differs: {dest}. Move it aside before installation.')
            files[rel] = src.read_bytes()
    shell = safe_path(home, '.config/omarchy/shell.json')
    config = json.loads(shell.read_text() if shell.exists() else (stock / 'config/omarchy/shell.json').read_text())
    replacements = {s.get('omarchy', {}).get('clonedFrom') for s in plugin_specs()}
    active_ids = [config.get('bar', {}).get('id', '')]
    for entries in [*config.get('bar', {}).get('layout', {}).values(), config.get('plugins', [])]:
        active_ids.extend(e if isinstance(e, str) else e.get('id', '') for e in entries)
    for plugin_id in active_ids:
        if not plugin_id or plugin_id.startswith(('omarchy.', 'nocturne.')):
            continue
        manifest = safe_path(home, '.config/omarchy/plugins/' + plugin_id + '/manifest.json')
        if manifest.is_file() and json.loads(manifest.read_text()).get('omarchy', {}).get('clonedFrom') in replacements:
            raise ValueError(f'Active custom clone {plugin_id} overlaps Nocturne. Switch that plugin back to its native source before installing.')
    files['.config/omarchy/shell.json'] = (json.dumps(merge_shell(config), indent=2) + '\n').encode()
    hypr = safe_path(home, '.config/hypr/hyprland.lua')
    if not hypr.is_file():
        raise ValueError('This package requires the Omarchy Lua-based Hyprland configuration.')
    text = hypr.read_text()
    if BEGIN in text or 'require("hypr.nocturne-' in text or "require('hypr.nocturne-" in text:
        raise ValueError('Nocturne modules are already required. Remove the old integration before installing.')
    # Place before persisted GUI overrides/toggles when the native template has them.
    marker = next((m for m in ['require("hypr.omacontrol")', 'require("default.hypr.toggles")'] if m in text), None)
    text = text.replace(marker, BLOCK + '\n' + marker, 1) if marker else text.rstrip() + '\n\n' + BLOCK
    files['.config/hypr/hyprland.lua'] = text.encode()
    return files


def install(home, stock, apply=False):
    state_path = safe_path(home, STATE)
    if state_path.exists():
        raise ValueError('An installation is already recorded. Uninstall it before changing versions.')
    files = prepare(home, stock)
    print(f'{len(files)} user-local files; shell preferences merged; wallpaper and fonts preserved.')
    if not apply:
        print('Dry run. Add --apply to install.')
        return
    record = {'version': 1, 'status': 'prepared', 'files': {}}
    for rel, data in files.items():
        path = safe_path(home, rel)
        previous = path.read_bytes() if path.exists() else None
        record['files'][rel] = {'before': previous.hex() if previous is not None else None,
                                'after': digest(data), 'mode': path.stat().st_mode & 0o777 if path.exists() else None}
    atomic(state_path, (json.dumps(record, indent=2) + '\n').encode(), mode=0o600)
    written = []
    try:
        for rel, data in files.items():
            path = safe_path(home, rel)
            atomic(path, data)
            written.append(rel)
            if rel.endswith('.sh'):
                path.chmod(0o755)
        record['status'] = 'installed'
        atomic(state_path, (json.dumps(record, indent=2) + '\n').encode(), mode=0o600)
    except BaseException:
        for rel in reversed(written):
            restore(home, rel, record['files'][rel])
        state_path.unlink(missing_ok=True)
        raise
    print('Installed. Apply the palette and reload using the commands in README.md.')


def restore(home, rel, entry):
    path = safe_path(home, rel)
    if entry['before'] is None:
        path.unlink(missing_ok=True)
    else:
        atomic(path, bytes.fromhex(entry['before']))
        path.chmod(entry['mode'])


def uninstall(home, apply=False):
    state_path = safe_path(home, STATE)
    record = json.loads(state_path.read_text())
    conflicts = []
    for rel, entry in record['files'].items():
        path = safe_path(home, rel)
        actual = digest(path.read_bytes()) if path.is_file() else None
        original = digest(bytes.fromhex(entry['before'])) if entry['before'] is not None else None
        if actual not in (entry['after'], original):
            conflicts.append(str(path))
    if conflicts:
        raise ValueError('Changed since installation; nothing removed. Back up and reconcile these files first:\n' + '\n'.join(conflicts))
    print(f'Restore {len(record["files"])} managed paths; preserve additional files.')
    if not apply:
        print('Dry run. Add --apply to uninstall.')
        return
    for rel, entry in reversed(list(record['files'].items())):
        restore(home, rel, entry)
    state_path.unlink()
    # Only empty directories owned by managed paths are eligible for removal.
    for rel in sorted(record['files'], key=lambda x: len(Path(x).parts), reverse=True):
        path = (home / rel).parent
        while path != home and path != home / '.config' and path != home / '.local':
            try:
                path.rmdir()
            except OSError:
                break
            path = path.parent
    print('Uninstalled. Select your previous theme, then reload Hyprland and the shell.')


def repair_startup(home, apply=False):
    """Replace only the known broken helper; preserve uninstall's original backup.

    Write the helper first. If updating the install record is interrupted, a
    repeat accepts the corrected helper and completes the record update.
    Never roll a repaired helper back to the version that prevents login.
    """
    data = (PAYLOAD / LAUNCH_HELPER).read_bytes()
    fixed = digest(data)
    expected = json.loads((ROOT / 'payload.sha256.json').read_text())
    if expected.get(LAUNCH_HELPER) != fixed:
        raise ValueError('Launch helper differs from payload.sha256.json.')
    path = safe_path(home, LAUNCH_HELPER)
    current = digest(path.read_bytes())
    allowed = (BROKEN_LAUNCH_SHA256, STARTUP_FIXED_LAUNCH_SHA256, fixed)
    if current not in allowed:
        raise ValueError('Custom launch helper differs; nothing changed. See docs/RECOVERY.md.')
    state_path = safe_path(home, STATE)
    record = json.loads(state_path.read_text()) if state_path.exists() else None
    entry = None
    if record is not None:
        entry = record.get('files', {}).get(LAUNCH_HELPER)
        if record.get('status') != 'installed' or not entry or entry.get('after') not in allowed:
            raise ValueError('Installation record does not match this repair; nothing changed.')
    print('Repair only the launch helper; preserve theme, preferences and uninstall backups.')
    if not apply:
        print('Dry run. Add --apply to repair.')
        return
    if current != fixed:
        atomic(path, data)
    if entry is not None and entry['after'] != fixed:
        entry['after'] = fixed
        atomic(state_path, (json.dumps(record, indent=2) + '\n').encode(), mode=0o600)
    print('Startup helper repaired. Verify configuration and follow docs/RECOVERY.md.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall', 'repair-startup'])
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--allow-untested', action='store_true', help='Allow an Omarchy version other than 4.0.6 (Lua is still required).')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as your desktop user, without sudo.')
    home = Path.home()
    stock = Path('/usr/share/omarchy')
    try:
        if args.action == 'install':
            version = subprocess.check_output(['pacman', '-Q', 'omarchy'], text=True).split()[1].rsplit('-', 1)[0]
            if version != '4.0.6' and not args.allow_untested:
                raise ValueError(f'Tested on Omarchy 4.0.6, found {version}. See compatibility notes.')
            install(home, stock, args.apply)
        elif args.action == 'repair-startup':
            repair_startup(home, args.apply)
        else:
            uninstall(home, args.apply)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'Nocturne: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
