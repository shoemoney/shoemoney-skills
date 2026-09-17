import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import brief
import change_guard


class BriefTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'briefing.html'
        self.source.write_text('<html><head></head><body><h1>Original</h1><a href="proof.json">Proof</a><link rel="stylesheet" href="style.css"></body></html>')
        (self.root / 'proof.json').write_text('{"verified":true}')
        (self.root / 'style.css').write_text('body{background:url("paper.svg")}')
        (self.root / 'paper.svg').write_text('<svg/>')
        self.archive = self.root / 'briefings'

    def snapshot(self, addition=None):
        return brief.snapshot(self.source, self.archive, addition, 'Measured update')

    def test_additive_versions_keep_historical_evidence_even_if_original_changes(self):
        self.snapshot()
        before = {p.relative_to(self.archive / 'v1'): p.read_bytes() for p in (self.archive / 'v1').rglob('*') if p.is_file()}
        (self.root / 'proof.json').write_text('{"verified":false}')
        addition = self.root / 'addition.html'
        addition.write_text('<section><h2>Dated correction</h2><a href="proof-v2.json">New proof</a></section>')
        (self.root / 'proof-v2.json').write_text('{"verified":false}')
        self.snapshot(addition)
        self.assertEqual(brief.verify(self.archive)['latest'], 2)
        for name, content in before.items():
            self.assertEqual((self.archive / 'v1' / name).read_bytes(), content)
        self.assertEqual((self.archive / 'v2/proof.json').read_bytes(), before[Path('proof.json')])
        self.assertTrue((self.archive / 'v2/paper.svg').is_file())
        self.assertIn('Original', (self.archive / 'v2/source.html').read_text())

    def test_tamper_blocks_next_snapshot(self):
        self.snapshot()
        (self.archive / 'v1/proof.json').write_text('tampered')
        with self.assertRaises(ValueError):
            brief.verify(self.archive)
        with self.assertRaises(ValueError):
            self.snapshot()

    def test_missing_and_outside_companions_fail_without_partial_edition(self):
        for reference in ('missing.json', '../outside.json', '%2e%2e/outside.json'):
            self.source.write_text(f'<html><head></head><body><a href="{reference}">Proof</a></body></html>')
            with self.assertRaises((ValueError, FileNotFoundError)):
                self.snapshot()
            self.assertFalse((self.archive / 'v1').exists())
            self.assertFalse((self.archive / '.snapshot.lock').exists())

    def test_empty_or_replacement_update_rejected(self):
        self.snapshot()
        addition = self.root / 'addition.html'
        for text in ('', '<BODY>Replacement</BODY>', '<head>Replacement</head>'):
            addition.write_text(text)
            with self.assertRaises(ValueError):
                self.snapshot(addition)
        with self.assertRaises(ValueError):
            self.snapshot()

    def test_lock_prevents_concurrent_writer(self):
        self.archive.mkdir()
        (self.archive / '.snapshot.lock').write_text('another writer')
        with self.assertRaises(FileExistsError):
            self.snapshot()
        self.assertEqual((self.archive / '.snapshot.lock').read_text(), 'another writer')


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.executive-brief/\n.env\nprivate/\n')
        (self.root / '.executive-brief.json').write_text(json.dumps({'watch': ['app/*', 'ops/*']}))
        (self.root / 'app').mkdir()
        (self.root / 'app/service.py').write_text('version=1')
        self.payload = {'cwd': str(self.root), 'stop_hook_active': False}

    def acknowledge(self):
        change_guard.write_json(change_guard.state_path(self.root), {'acknowledged': change_guard.fingerprint(self.root)})

    def test_only_changed_opted_in_projects_prompt_once(self):
        self.acknowledge()
        self.assertEqual(change_guard.guard(self.payload), {})
        (self.root / 'app/service.py').write_text('version=2')
        self.assertEqual(change_guard.guard(self.payload)['decision'], 'block')
        self.assertEqual(change_guard.guard(self.payload), {})
        self.acknowledge()
        self.assertEqual(change_guard.guard(self.payload), {})

    def test_document_only_edits_and_ignored_secrets_do_not_trigger(self):
        self.acknowledge()
        (self.root / 'README.md').write_text('documentation')
        (self.root / '.env').write_text('NOT_A_REAL_SECRET=test')
        self.assertEqual(change_guard.guard(self.payload), {})

    def test_external_change_triggers_and_recursion_does_not(self):
        self.acknowledge()
        change_guard.write_json(self.root / '.executive-brief/pending.json', {'note': 'Cloud resize'})
        self.assertEqual(change_guard.guard({**self.payload, 'stop_hook_active': True}), {})
        self.assertEqual(change_guard.guard(self.payload)['decision'], 'block')

    def test_no_config_is_noop(self):
        (self.root / '.executive-brief.json').unlink()
        self.assertEqual(change_guard.guard(self.payload), {})

    def test_deleting_watched_file_triggers(self):
        self.acknowledge()
        (self.root / 'app/service.py').unlink()
        self.assertEqual(change_guard.guard(self.payload)['decision'], 'block')


if __name__ == '__main__':
    unittest.main()
