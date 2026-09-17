#!/usr/bin/env python3
"""Immutable, additive executive brief editions. Standard library only."""
import argparse
import hashlib
import html
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path escapes the document directory')
    return path


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(v for k, v in attrs if k in ('src', 'href', 'poster') and v)
        for key, val in attrs:
            if key == 'srcset' or (key == 'style' and 'url(' in (val or '')):
                raise ValueError('Use explicit src/href companion files, not srcset or inline CSS URLs')


def referenced(data, suffix):
    if suffix == '.html':
        parser = References()
        parser.feed(data.decode())
        return parser.urls
    if suffix == '.css':
        text = data.decode()
        return re.findall(r'url\(\s*[\"\']?([^\s\)\"\']+)', text) + re.findall(r'@import\s+[\"\']([^\"\']+)', text)
    return []


def verify(archive):
    index = json.loads((archive / 'index.json').read_text())
    previous = None
    for expected, row in enumerate(index['versions'], 1):
        if row['version'] != expected:
            raise ValueError('Nonsequential version history')
        folder = archive / f'v{expected}'
        manifest_bytes = (folder / 'manifest.json').read_bytes()
        if sha(manifest_bytes) != row['manifest_sha256']:
            raise ValueError('Manifest changed after snapshot')
        manifest = json.loads(manifest_bytes)
        if manifest['previous_source_sha256'] != previous:
            raise ValueError('Broken source hash chain')
        for name, digest in manifest['files'].items():
            if sha(inside(folder, name).read_bytes()) != digest:
                raise ValueError(f'Companion changed: {name}')
        source = (folder / 'source.html').read_bytes()
        if sha(source) != manifest['source_sha256']:
            raise ValueError('Source digest mismatch')
        if expected > 1:
            old = (archive / f'v{expected - 1}/source.html').read_bytes()
            head, end, tail = old.rpartition(b'</body>')
            if not source.startswith(head) or not source.endswith(end + tail):
                raise ValueError('Prior document content was removed or replaced')
        previous = manifest['source_sha256']
    if index['latest'] != len(index['versions']):
        raise ValueError('Latest version disagrees with history')
    return index


def snapshot(source_path, archive, addition, note):
    source_path, archive = source_path.resolve(), archive.resolve()
    archive.mkdir(parents=True, exist_ok=True)
    # A lock prevents concurrent writers choosing the same version. Stale locks
    # require operator inspection; never silently steal an active writer's lock.
    lock = archive / '.snapshot.lock'
    with lock.open('x') as handle:
        handle.write(datetime.now(timezone.utc).isoformat())
    staging = None
    try:
        index = verify(archive) if (archive / 'index.json').exists() else {'latest': 0, 'versions': []}
        version = index['latest'] + 1
        prior = archive / f'v{version - 1}'
        old = (prior / 'source.html').read_bytes() if version > 1 else source_path.read_bytes()
        if version > 1 and not addition:
            raise ValueError('Later editions require an additive HTML fragment')
        data = old
        if addition:
            fragment = Path(addition).read_bytes()
            if not fragment.strip() or re.search(br'</?(?:html|head|body)\b', fragment, re.I):
                raise ValueError('Supply a body fragment, not a replacement document')
            prefix, closing, suffix = data.rpartition(b'</body>')
            if not closing:
                raise ValueError('Missing closing body element')
            data = prefix + b'\n' + fragment + b'\n' + closing + suffix
        final = archive / f'v{version}'
        if final.exists():
            raise ValueError('Refusing to overwrite an edition; inspect orphaned snapshot')
        staging = Path(tempfile.mkdtemp(prefix='.preparing-', dir=archive))
        # Carry ALL earlier evidence bytes, including currently unlinked evidence.
        if version > 1:
            shutil.copytree(prior, staging, dirs_exist_ok=True)
            for name in ('manifest.json', 'index.html', 'source.html'):
                (staging / name).unlink()
        (staging / 'source.html').write_bytes(data)
        queue, seen = [('source.html', data)], set()
        while queue:
            name, content = queue.pop()
            if name in seen:
                continue
            seen.add(name)
            for url in referenced(content, Path(name).suffix):
                parsed = urlsplit(url)
                if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith('/'):
                    continue
                relative = (Path(name).parent / unquote(parsed.path)).as_posix()
                dest = inside(staging, relative)
                if dest.exists():
                    payload = dest.read_bytes()  # Version-pinned, never refresh from mutable originals.
                else:
                    candidate = inside(source_path.parent, relative)
                    if not candidate.is_file():
                        raise ValueError(f'Missing companion: {relative}')
                    payload = candidate.read_bytes()
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(payload)
                queue.append((relative, payload))
        stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
        links = ' · '.join(f'<a href="../v{v}/index.html">v{v}</a>' for v in range(1, version + 1))
        navigation = f'<aside aria-label="Edition history" style="font:20px/1.5 sans-serif;padding:24px"><strong>Executive briefing v{version}</strong><p>{html.escape(stamp)} · {html.escape(note)}</p><nav>{links} · <a href="../../execbrief.html">Latest</a></nav></aside>'
        document = data.decode()
        if '<body>' not in document or '</head>' not in document:
            raise ValueError('Source needs literal <body> and </head> markers')
        document = document.replace('<body>', '<body>\n' + navigation, 1)
        document = document.replace('</head>', '<meta name="robots" content="noindex,nofollow,noarchive"></head>', 1)
        (staging / 'index.html').write_text(document)
        files = {p.relative_to(staging).as_posix(): sha(p.read_bytes()) for p in sorted(staging.rglob('*')) if p.is_file()}
        manifest = {'version': version, 'created_at': stamp, 'note': note, 'source_sha256': sha(data), 'previous_source_sha256': sha(old) if version > 1 else None, 'files': files}
        (staging / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        manifest_sha = sha((staging / 'manifest.json').read_bytes())
        staging.rename(final)
        staging = None
        index['latest'] = version
        index['versions'].append({'version': version, 'created_at': stamp, 'manifest_sha256': manifest_sha})
        temporary = archive / '.index.tmp'
        temporary.write_text(json.dumps(index, indent=2) + '\n')
        temporary.replace(archive / 'index.json')
        return {'version': version, 'path': str(final), 'manifest_sha256': manifest_sha}
    finally:
        if staging:
            shutil.rmtree(staging)
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    create = sub.add_parser('snapshot')
    create.add_argument('--source', type=Path, required=True)
    create.add_argument('--archive', type=Path, required=True)
    create.add_argument('--addition', type=Path)
    create.add_argument('--note', required=True)
    check = sub.add_parser('verify')
    check.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.archive) if args.action == 'verify' else snapshot(args.source, args.archive, args.addition, args.note)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
