#!/usr/bin/env python3
"""Generate per-chapter illustrations via OpenRouter Gemini 3 Pro Image.

For each chapter listed in your `_launch_config.json`:
  - Reads prompt text from `{prompts_dir}/{slug}.txt`
  - Attaches the protagonist reference image (or strong/custom refs) per config
  - Writes `{color_images_dir}/{slug}.png`
  - Idempotent: skips existing outputs unless --force
  - Hard-caps retries at 3 attempts per slug to bound API spend
  - Optional regen-log appended to `{color_images_dir}/regen-log.md`

Cost note: Gemini 3 Pro Image Preview is billed per-image. In production we
observed ~$0.14/image, not the published $0.04 — budget accordingly. 20
chapters at $0.14 = ~$2.80 per regen pass.

Usage:
    python3 generate_chapter_images.py <slug>
    python3 generate_chapter_images.py --all
    python3 generate_chapter_images.py <slug> --no-ref
    python3 generate_chapter_images.py --all --regen-log
    python3 generate_chapter_images.py --all --force          # rebuild everything

Requires: $OPENROUTER_API_KEY in env (only checked when actually calling
the API — `--help` works without it).
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Make _config importable whether run from skill dir or copied locally.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config, project_root  # noqa: E402

MODEL = "google/gemini-3-pro-image-preview"
MAX_ATTEMPTS = 3
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def mime_for(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return {"png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")


def call_api(api_key: str, prompt: str, ref_paths: list[Path], title: str):
    content = [{"type": "text", "text": prompt}]
    for path in ref_paths:
        b64 = encode_image(path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_for(path)};base64,{b64}"},
        })

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "modalities": ["image", "text"],
    }
    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/shoemoney/gsd-book-skill",
            "X-Title": f"{title} chapter illustration",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=240) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    msg = data["choices"][0]["message"]
    images = msg.get("images") or []
    if not images:
        c = msg.get("content")
        if isinstance(c, list):
            images = [x for x in c if x.get("type") == "image_url"]
    if not images:
        raise RuntimeError(f"No images in response. Raw: {json.dumps(data)[:1200]}")

    decoded = []
    for img in images:
        url = img.get("image_url", {}).get("url") if isinstance(img, dict) else None
        if not url or not url.startswith("data:"):
            continue
        header, b64 = url.split(",", 1)
        ext = "png" if "png" in header else "jpg"
        decoded.append((ext, base64.b64decode(b64)))

    if not decoded:
        raise RuntimeError("Got response but no decodable image data.")
    return decoded


def resolve_refs(chapter: dict, cfg: dict, root: Path, no_ref_override: bool) -> list[Path]:
    if no_ref_override:
        return []
    if not chapter.get("has_protagonist", True) and "custom_refs" not in chapter:
        return []
    if "custom_refs" in chapter:
        paths = [root / p for p in chapter["custom_refs"]]
        existing = [p for p in paths if p.exists()]
        if not existing:
            raise FileNotFoundError(f"custom_refs all missing: {paths}")
        return existing
    if chapter.get("use_strong_refs"):
        strong = cfg["protagonist"].get("strong_refs") or []
        paths = [root / p for p in strong]
        existing = [p for p in paths if p.exists()]
        if not existing:
            raise FileNotFoundError(f"strong_refs all missing: {paths}")
        return existing
    canonical = cfg["protagonist"].get("canonical_ref")
    if not canonical:
        raise FileNotFoundError("protagonist.canonical_ref not set in config")
    p = root / canonical
    if not p.exists():
        raise FileNotFoundError(f"canonical_ref missing: {p}")
    return [p]


def generate_one(slug: str, *, cfg: dict, root: Path, force: bool, regen_log: bool,
                 no_ref_override: bool) -> tuple[bool, str]:
    chapter = next((c for c in cfg["chapters"] if c["slug"] == slug), None)
    if chapter is None:
        return False, f"slug not in config: {slug}"

    prompts_dir = root / cfg["paths"]["prompts_dir"]
    images_dir = root / cfg["paths"]["color_images_dir"]

    prompt_path = prompts_dir / f"{slug}.txt"
    if not prompt_path.exists():
        return False, f"prompt file missing: {prompt_path}"

    out_path = images_dir / f"{slug}.png"
    if out_path.exists() and not force:
        return True, f"skip (exists): {out_path}"

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return False, "OPENROUTER_API_KEY not set in environment"

    prompt = prompt_path.read_text()

    try:
        ref_paths = resolve_refs(chapter, cfg, root, no_ref_override)
    except FileNotFoundError as e:
        return False, str(e)

    images_dir.mkdir(parents=True, exist_ok=True)

    title = cfg.get("title", "Book")
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"  [{slug}] attempt {attempt}/{MAX_ATTEMPTS} (refs: {len(ref_paths)})…")
        try:
            decoded = call_api(api_key, prompt, ref_paths, title)
        except urllib.error.HTTPError as e:
            body_txt = e.read().decode("utf-8", errors="replace")
            last_err = f"HTTP {e.code}: {body_txt[:400]}"
            print(f"  [{slug}] {last_err}")
            time.sleep(2 * attempt)
            continue
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            print(f"  [{slug}] {last_err}")
            time.sleep(2 * attempt)
            continue

        ext, blob = decoded[0]
        write_path = out_path if ext == "png" else out_path.with_suffix(f".{ext}")
        write_path.write_bytes(blob)
        size = write_path.stat().st_size
        print(f"  [{slug}] OK wrote {write_path} ({size/1024:.1f} KB)")

        if regen_log:
            regen_path = images_dir / "regen-log.md"
            ts = datetime.datetime.now().isoformat(timespec="seconds")
            line = (
                f"- {ts} | {slug} | attempt {attempt} | "
                f"{size/1024:.1f} KB | prompt: {prompt_path.relative_to(root)}\n"
            )
            need_header = not regen_path.exists()
            with open(regen_path, "a") as f:
                if need_header:
                    f.write("# Chapter image regen log\n\n")
                f.write(line)

        return True, str(write_path)

    return False, f"3 attempts failed for {slug}: {last_err}"


def main():
    ap = argparse.ArgumentParser(description="Generate per-chapter illustrations via OpenRouter Gemini 3 Pro Image.")
    ap.add_argument("slug", nargs="?", help="Chapter slug from config (e.g. ch01-opening)")
    ap.add_argument("--all", action="store_true", help="Generate every chapter in config")
    ap.add_argument("--force", action="store_true", help="Re-generate even if output exists")
    ap.add_argument("--no-ref", action="store_true", help="Skip protagonist likeness reference for this run")
    ap.add_argument("--regen-log", action="store_true", help="Append a line to {color_images_dir}/regen-log.md per success")
    add_config_arg(ap)
    args = ap.parse_args()

    if not args.slug and not args.all:
        ap.error("provide a slug or --all")

    cfg = load_config(args.config)
    root = project_root(args.config)

    slugs = [c["slug"] for c in cfg["chapters"]] if args.all else [args.slug]
    print(f"-> generating {len(slugs)} chapter image(s)")

    failures = []
    for slug in slugs:
        ok, msg = generate_one(
            slug,
            cfg=cfg,
            root=root,
            force=args.force,
            regen_log=args.regen_log,
            no_ref_override=args.no_ref,
        )
        if not ok:
            failures.append((slug, msg))
            print(f"  [{slug}] FAILED: {msg}")
        else:
            print(f"  [{slug}] {msg}")

    if failures:
        print("\nFailures:")
        for slug, msg in failures:
            print(f"  - {slug}: {msg}")
        sys.exit(1)
    print("\nOK all done")


if __name__ == "__main__":
    main()
