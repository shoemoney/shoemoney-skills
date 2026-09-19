#!/usr/bin/env python3
"""Cache the canonical AiBook PDF and retrieve bounded, page-cited source text."""

import argparse
import hashlib
import io
import json
import re
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://cdn.shoemoney.com/aibook/AiBook.pdf"
NOTES_SHA256 = "2c9a531b9c84e1959f83921ba70ee45815a32898bcabab2b264ec71ac2ae9303"
MAX_BYTES = 100 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError(f"Canonical PDF redirected (HTTP {code}); verify the new source manually.")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(cache):
    pointer = json.loads((cache / "current.json").read_text())
    snapshot_name = pointer["snapshot"]
    if not re.fullmatch(r"snapshot-[a-zA-Z0-9_-]+", snapshot_name):
        raise ValueError("Invalid cache snapshot path.")
    snapshot = cache / snapshot_name
    raw = (snapshot / "book.json").read_bytes()
    if digest(raw) != pointer["text_sha256"]:
        raise ValueError("Cached text integrity failed; run fetch --refresh.")
    book = json.loads(raw)
    if digest((snapshot / "AiBook.pdf").read_bytes()) != book["sha256"]:
        raise ValueError("Cached PDF integrity failed; run fetch --refresh.")
    if book["source_url"] != SOURCE_URL:
        raise ValueError("Cached source does not match the canonical PDF.")
    return book, snapshot


def metadata(book, snapshot):
    pointer = json.loads((snapshot.parent / "current.json").read_text())
    return {
        key: book[key]
        for key in ("source_url", "retrieved_at_utc", "sha256", "page_count")
    } | {
        "indexed_chapters": len(book["chapters"]),
        "matches_failure_notes": book["sha256"] == NOTES_SHA256,
        "local_pdf": str(snapshot / "AiBook.pdf"),
        "update_check": pointer.get("update_check", {"status": "not_checked"}),
    }


def write_pointer(cache, pointer):
    with tempfile.NamedTemporaryFile(mode="w", dir=cache, delete=False) as stream:
        json.dump(pointer, stream)
        temporary = Path(stream.name)
    temporary.replace(cache / "current.json")


def update_pointer(cache, headers, status, downloaded_bytes, changed_chapters, previous_sha256=None):
    pointer = json.loads((cache / "current.json").read_text())
    old_headers = pointer.get("http_validators", {}) if status == "not_modified" else {}
    pointer["http_validators"] = {
        "etag": headers.get("ETag", old_headers.get("etag")),
        "last_modified": headers.get("Last-Modified", old_headers.get("last_modified")),
    }
    pointer["update_check"] = {
        "status": status,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "downloaded_bytes": downloaded_bytes,
        "changed_chapters": changed_chapters,
        "previous_sha256": previous_sha256,
    }
    write_pointer(cache, pointer)


def chapter_digests(book):
    return {
        chapter["chapter"]: digest("\n".join(book["pages"][chapter["pdf_start"] - 1:chapter["pdf_end"]]).encode())
        for chapter in book["chapters"]
    }


def fetch(cache, refresh):
    cached = None
    pointer = {}
    if (cache / "current.json").exists():
        try:
            cached = load(cache)
            pointer = json.loads((cache / "current.json").read_text())
        except (ValueError, OSError, KeyError):
            if not refresh:
                raise
    headers = {"User-Agent": "LearnFromShoeMoney/1.1", "Cache-Control": "no-cache"}
    validators = pointer.get("http_validators", {})
    if cached and not refresh:
        if validators.get("etag"):
            headers["If-None-Match"] = validators["etag"]
        elif validators.get("last_modified"):
            headers["If-Modified-Since"] = validators["last_modified"]
    request = urllib.request.Request(SOURCE_URL, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=45) as response:
            pdf = response.read(MAX_BYTES + 1)
            response_headers = response.headers
    except urllib.error.HTTPError as exc:
        if exc.code != 304 or not cached or refresh:
            raise
        try:
            update_pointer(cache, exc.headers, "not_modified", 0, [])
            return load(cache)
        finally:
            exc.close()
    if len(pdf) > MAX_BYTES:
        raise ValueError("PDF exceeds 100 MiB; source not cached.")
    if not pdf.startswith(b"%PDF-"):
        raise ValueError("Source did not return a PDF; existing cache preserved.")
    if cached and digest(pdf) == cached[0]["sha256"]:
        update_pointer(cache, response_headers, "unchanged", len(pdf), [])
        return load(cache)
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("Use a Python interpreter with pypdf; see this skill's INSTALL.md.") from exc
    reader = PdfReader(io.BytesIO(pdf))
    pages = [unicodedata.normalize("NFKC", page.extract_text() or "") for page in reader.pages]
    if not pages or sum(len(page.strip()) for page in pages) < 1000:
        raise ValueError("Insufficient extracted text; inspect PDF/OCR before using it.")
    boundaries = []
    for number, text in enumerate(pages, 1):
        match = re.search(r"^C H A P T E R[ \t]+([\d \t]+)\n([^\n]+)", text)
        if match:
            boundaries.append({"chapter": int("".join(match[1].split())), "title": match[2], "pdf_start": number})
    if not boundaries or len({item["chapter"] for item in boundaries}) != len(boundaries):
        raise ValueError("Chapter headings changed or are ambiguous; inspect the source before indexing.")
    for i, chapter in enumerate(boundaries):
        end = boundaries[i + 1]["pdf_start"] - 1 if i + 1 < len(boundaries) else len(pages)
        # Interlude and back matter are separate from chapter content.
        for page_number in range(chapter["pdf_start"] + 1, end + 1):
            first = pages[page_number - 1].splitlines()
            if first and "".join(first[0].split()).casefold() in {"interlude", "onepageontheframeworks", "abouttheauthor"}:
                end = page_number - 1
                break
        chapter["pdf_end"] = end
    book = {"source_url": SOURCE_URL, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": digest(pdf), "page_count": len(pages), "chapters": boundaries, "pages": pages}
    cache.mkdir(parents=True, exist_ok=True)
    # A fresh snapshot plus atomic pointer preserves the previous one on failed refresh.
    snapshot = Path(tempfile.mkdtemp(prefix="snapshot-", dir=cache))
    (snapshot / "AiBook.pdf").write_bytes(pdf)
    raw = json.dumps(book, ensure_ascii=False, indent=2).encode()
    (snapshot / "book.json").write_bytes(raw)
    previous = chapter_digests(cached[0]) if cached else {}
    current = chapter_digests(book)
    changed = sorted(chapter for chapter in previous.keys() | current.keys() if previous.get(chapter) != current.get(chapter))
    write_pointer(cache, {"snapshot": snapshot.name, "text_sha256": digest(raw)})
    update_pointer(cache, response_headers, "updated" if cached else "downloaded", len(pdf), changed,
                   cached[0]["sha256"] if cached else None)
    return load(cache)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path.home() / ".cache/codex/learn-from-shoemoney")
    sub = parser.add_subparsers(dest="command", required=True)
    downloader = sub.add_parser("fetch", help="Check for book updates; reuse unchanged content and index changed PDFs")
    downloader.add_argument("--refresh", action="store_true", help="Download unconditionally, ignoring HTTP validators")
    sub.add_parser("index", help="Show source identity and available chapter page ranges")
    search = sub.add_parser("search", help="Case-insensitive literal search with page-cited snippets")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=12)
    read = sub.add_parser("read", help="Read one chapter or a bounded one-based PDF page range")
    selector = read.add_mutually_exclusive_group(required=True)
    selector.add_argument("--chapter", type=int)
    selector.add_argument("--pages", help="One-based page number or range, e.g. 341-342")
    args = parser.parse_args()
    cache = args.cache_dir.expanduser().resolve()
    try:
        book, snapshot = fetch(cache, args.refresh) if args.command == "fetch" else load(cache)
        if args.command in {"fetch", "index"}:
            result = metadata(book, snapshot)
            if args.command == "index":
                result["chapters"] = book["chapters"]
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return
        if book["sha256"] != NOTES_SHA256:
            print("NOTICE: PDF differs from curated notes; revalidate citations and lessons.", file=sys.stderr)
        if args.command == "search":
            needle = " ".join(args.query.split()).casefold()
            if not needle or args.limit < 1:
                raise ValueError("Search needs a nonempty query and a positive limit.")
            matches = []
            for number, text in enumerate(book["pages"], 1):
                text = " ".join(text.split())
                position = text.casefold().find(needle)
                if position >= 0:
                    matches.append({"pdf_page": number, "url": f"{SOURCE_URL}#page={number}",
                                    "snippet": text[max(0, position - 160):position + len(needle) + 240]})
            print(json.dumps({"matching_pages": len(matches), "shown": matches[:args.limit]}, indent=2, ensure_ascii=False))
            return
        if args.chapter is not None:
            chapter = next((item for item in book["chapters"] if item["chapter"] == args.chapter), None)
            if chapter is None:
                raise ValueError("Chapter not indexed; use index to inspect available chapters.")
            start, end = chapter["pdf_start"], chapter["pdf_end"]
        else:
            match = re.fullmatch(r"(\d+)(?:-(\d+))?", args.pages)
            if not match:
                raise ValueError("Use a single page or range, e.g. 341-342.")
            start, end = int(match[1]), int(match[2] or match[1])
        if not 1 <= start <= end <= book["page_count"]:
            raise ValueError("Page range is outside the PDF.")
        if end - start + 1 > 20:
            raise ValueError("Read at most 20 pages per call; select the relevant chapter or section.")
        for page_number in range(start, end + 1):
            print(f"\n=== PDF PAGE {page_number} | {SOURCE_URL}#page={page_number} ===\n{book['pages'][page_number - 1]}")
    except Exception as exc:
        parser.exit(1, f"Book read failed: {exc}\n")


if __name__ == "__main__":
    main()
