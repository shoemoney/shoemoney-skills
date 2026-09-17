#!/usr/bin/env python3
"""Project-opted-in Stop reminder; never runs a model, deploys, or reads secrets."""
import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIG = '.executive-brief.json'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(value, handle, indent=2)
            handle.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def locate(cwd):
    start = Path(cwd).resolve()
    for folder in [start, *start.parents]:
        if (folder / CONFIG).is_file():
            return folder
    return None


def state_path(root):
    directory = root / '.executive-brief'
    if directory.is_symlink():
        raise ValueError('State directory must not be a symlink')
    return directory / 'state.json'


def fingerprint(root):
    config = json.loads((root / CONFIG).read_text())
    names = subprocess.run(['git', '-C', str(root), 'ls-files', '-co', '--exclude-standard', '-z'], check=True, capture_output=True, timeout=5).stdout.decode().split('\0')
    rows = {}
    for name in sorted(set(names)):
        if not name or not any(fnmatch.fnmatch(name, pattern) for pattern in config['watch']):
            continue
        parts = Path(name).parts
        if any(part.startswith('.') or part in ('private', 'secrets', 'node_modules', 'vendor') for part in parts):
            continue
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            continue
        if path.is_file():
            if path.stat().st_size > 10_000_000:
                raise ValueError('Watched file exceeds 10 MB; narrow the watch list')
            rows[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    marker = root / '.executive-brief/pending.json'
    if marker.is_file():
        rows['external_change'] = hashlib.sha256(marker.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def guard(payload):
    if payload.get('stop_hook_active') or payload.get('agent_id'):
        return {}
    root = locate(payload.get('cwd') or os.getcwd())
    if root is None:
        return {}
    path = state_path(root)
    state = json.loads(path.read_text()) if path.exists() else {}
    current = fingerprint(root)
    if current in (state.get('acknowledged'), state.get('notified')):
        return {}
    state['notified'] = current
    write_json(path, state)
    return {'decision': 'block', 'reason': 'Use $executive-brief for this opted-in project. Software or infrastructure inputs changed since the last briefing review. Inspect the changes: if material, append a dated evidence-based edition, preserve every older version, and publish only within existing authorization. If minor or blocked, record the reason without inventing an edition. Finish with change_guard.py acknowledge --root <project> --note <outcome>. Do not restart workers or launch another agent from this hook.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['hook', 'mark', 'acknowledge'])
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--note')
    args = parser.parse_args()
    if args.action == 'hook':
        try:
            print(json.dumps(guard(json.load(sys.stdin))))
        except Exception as error:
            print(json.dumps({'systemMessage': f'Executive briefing change check could not finish ({type(error).__name__}); review it manually.'}))
        return
    if not args.note or not args.note.strip():
        parser.error('--note is required')
    root = args.root.resolve()
    path = state_path(root)
    if args.action == 'mark':
        write_json(path.parent / 'pending.json', {'note': args.note, 'nonce': os.urandom(16).hex()})
    else:
        write_json(path, {'acknowledged': fingerprint(root), 'note': args.note})
    print(json.dumps({'action': args.action, 'recorded': True}))


if __name__ == '__main__':
    main()
