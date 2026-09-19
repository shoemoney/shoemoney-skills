"""Offline behavior tests. Always exercise the reader beside this file."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

SUBJECT = Path(__file__).resolve().with_name("read_book.py")
SPEC = importlib.util.spec_from_file_location("lfsm_reader_under_test", SUBJECT)
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


class BookUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.cache = Path(self.temporary.name)
        self.snapshot = self.cache / "snapshot-original"
        self.snapshot.mkdir()
        self.pdf = b"%PDF-1.7\noriginal test fixture"
        self.pages = [
            "C H A P T E R 1\nFirst lesson\n" + "Verify the actual output. " * 30,
            "C H A P T E R 2\nSecond lesson\n" + "Record every failed attempt. " * 30,
        ]
        self.book = {
            "source_url": reader.SOURCE_URL,
            "retrieved_at_utc": "2026-09-19T00:00:00+00:00",
            "sha256": reader.digest(self.pdf),
            "page_count": 2,
            "pages": self.pages,
            "chapters": [
                {"chapter": 1, "title": "First lesson", "pdf_start": 1, "pdf_end": 1},
                {"chapter": 2, "title": "Second lesson", "pdf_start": 2, "pdf_end": 2},
            ],
        }
        raw = json.dumps(self.book).encode()
        (self.snapshot / "AiBook.pdf").write_bytes(self.pdf)
        (self.snapshot / "book.json").write_bytes(raw)
        reader.write_pointer(self.cache, {
            "snapshot": self.snapshot.name,
            "text_sha256": reader.digest(raw),
            "http_validators": {"etag": '"original"', "last_modified": "Sat, 19 Sep 2026 00:00:00 GMT"},
        })

    def network(self, body=None, headers=None, error=None):
        opener = Mock()
        if error:
            opener.open.side_effect = error
        else:
            response = io.BytesIO(body)
            response.headers = headers or {"ETag": '"new"'}
            opener.open.return_value = response
        replacement = patch.object(reader.urllib.request, "build_opener", return_value=opener)
        replacement.start()
        self.addCleanup(replacement.stop)
        return opener

    def pointer(self):
        return json.loads((self.cache / "current.json").read_text())

    def fake_parser(self, pages):
        module = types.ModuleType("pypdf")
        module.PdfReader = Mock(return_value=types.SimpleNamespace(pages=[
            types.SimpleNamespace(extract_text=lambda text=text: text) for text in pages
        ]))
        replacement = patch.dict(sys.modules, {"pypdf": module})
        replacement.start()
        self.addCleanup(replacement.stop)
        return module.PdfReader

    def test_304_reuses_snapshot_and_sends_etag(self):
        opener = self.network(error=urllib.error.HTTPError(reader.SOURCE_URL, 304, "Not Modified", {}, io.BytesIO()))
        parse = self.fake_parser([])
        book, snapshot = reader.fetch(self.cache, False)
        self.assertEqual(snapshot, self.snapshot)
        self.assertEqual(book, self.book)
        self.assertEqual(opener.open.call_args.args[0].get_header("If-none-match"), '"original"')
        self.assertEqual(self.pointer()["http_validators"]["etag"], '"original"')
        self.assertEqual(self.pointer()["update_check"]["downloaded_bytes"], 0)
        self.assertEqual(self.pointer()["update_check"]["status"], "not_modified")
        parse.assert_not_called()

    def test_last_modified_is_used_when_etag_missing(self):
        pointer = self.pointer()
        del pointer["http_validators"]["etag"]
        reader.write_pointer(self.cache, pointer)
        opener = self.network(error=urllib.error.HTTPError(reader.SOURCE_URL, 304, "Not Modified", {}, io.BytesIO()))
        reader.fetch(self.cache, False)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_header("If-modified-since"), "Sat, 19 Sep 2026 00:00:00 GMT")
        self.assertIsNone(request.get_header("If-none-match"))

    def test_identical_download_does_not_extract_again(self):
        self.network(self.pdf)
        parse = self.fake_parser([])
        _, snapshot = reader.fetch(self.cache, False)
        self.assertEqual(snapshot, self.snapshot)
        self.assertEqual(self.pointer()["update_check"]["status"], "unchanged")
        self.assertEqual(self.pointer()["update_check"]["downloaded_bytes"], len(self.pdf))
        parse.assert_not_called()

    def test_changed_source_reindexes_and_flags_notes_and_changed_chapter(self):
        self.network(b"%PDF-1.7\nupdated fixture")
        parse = self.fake_parser([self.pages[0], self.pages[1] + " New failure learned."])
        with patch.object(reader, "NOTES_SHA256", self.book["sha256"]):
            book, snapshot = reader.fetch(self.cache, False)
            metadata = reader.metadata(book, snapshot)
        self.assertNotEqual(snapshot, self.snapshot)
        self.assertTrue((self.snapshot / "AiBook.pdf").exists())
        self.assertFalse(metadata["matches_failure_notes"])
        self.assertEqual(metadata["update_check"]["changed_chapters"], [2])
        self.assertEqual(metadata["update_check"]["previous_sha256"], self.book["sha256"])
        self.assertEqual(metadata["update_check"]["status"], "updated")
        self.assertIn("New failure learned", book["pages"][1])
        parse.assert_called_once()

    def test_timeout_preserves_last_valid_snapshot(self):
        before = (self.cache / "current.json").read_bytes()
        self.network(error=TimeoutError("controlled offline failure"))
        with self.assertRaises(TimeoutError):
            reader.fetch(self.cache, False)
        self.assertEqual((self.cache / "current.json").read_bytes(), before)
        self.assertEqual(reader.load(self.cache)[0], self.book)

    def test_non_pdf_response_preserves_last_valid_snapshot(self):
        before = (self.cache / "current.json").read_bytes()
        self.network(b"<html>service temporarily unavailable</html>")
        with self.assertRaisesRegex(ValueError, "did not return a PDF"):
            reader.fetch(self.cache, False)
        self.assertEqual((self.cache / "current.json").read_bytes(), before)
        self.assertEqual(reader.load(self.cache)[0], self.book)

    def test_changed_heading_format_preserves_last_valid_snapshot(self):
        before = (self.cache / "current.json").read_bytes()
        self.network(b"%PDF-1.7\nnew layout")
        self.fake_parser(["Unrecognized heading\n" + "text " * 400])
        with self.assertRaisesRegex(ValueError, "Chapter headings changed"):
            reader.fetch(self.cache, False)
        self.assertEqual((self.cache / "current.json").read_bytes(), before)
        self.assertEqual(reader.load(self.cache)[0], self.book)

    def test_forced_refresh_does_not_send_validators(self):
        opener = self.network(self.pdf)
        reader.fetch(self.cache, True)
        request = opener.open.call_args.args[0]
        self.assertIsNone(request.get_header("If-none-match"))
        self.assertIsNone(request.get_header("If-modified-since"))

    def test_corrupt_cached_text_is_rejected(self):
        (self.snapshot / "book.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "text integrity"):
            reader.load(self.cache)

    def test_search_returns_only_matching_context_with_source_page(self):
        output = io.StringIO()
        argv = [str(SUBJECT), "--cache-dir", str(self.cache), "search", "failed attempt", "--limit", "1"]
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            reader.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["matching_pages"], 1)
        self.assertEqual(len(result["shown"]), 1)
        self.assertEqual(result["shown"][0]["pdf_page"], 2)
        self.assertEqual(result["shown"][0]["url"], reader.SOURCE_URL + "#page=2")
        self.assertLess(len(result["shown"][0]["snippet"]), len(self.pages[1]))

    def test_read_rejects_out_of_range_pages(self):
        argv = [str(SUBJECT), "--cache-dir", str(self.cache), "read", "--pages", "1-200"]
        with patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as failure:
                reader.main()
        self.assertEqual(failure.exception.code, 1)

    def test_canonical_pdf_redirect_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "redirected"):
            reader.NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://example.org/other.pdf")


if __name__ == "__main__":
    unittest.main()
