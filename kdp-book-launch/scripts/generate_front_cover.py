#!/usr/bin/env python3
"""Generate paperback FRONT cover artwork via OpenRouter Gemini 3 Pro Image.

Generates the ARTWORK only — title and author typography are best overlaid
in a vector editor (Affinity Publisher / InDesign / Figma) for clean text.

Reads the prompt from `prompts/Covers/front-prompt.txt` (or the
`--prompt-file` arg) and attaches multiple protagonist reference images
from your launch config for identity anchoring.

Cost: ~$0.14 per generation in our production runs. Plan on 3-6
iterations to nail composition / likeness / negative space for title.

Usage:
    python3 generate_front_cover.py
    python3 generate_front_cover.py --prompt-file prompts/Covers/front-alt.txt
    python3 generate_front_cover.py --out-dir covers/alt --basename front-alt

Requires: $OPENROUTER_API_KEY in env.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config, project_root  # noqa: E402

MODEL = "google/gemini-3-pro-image-preview"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_PROMPT_REL = "prompts/Covers/front-prompt.txt"


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def mime_for(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return {"png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--prompt-file", help=f"Override prompt file (default: {DEFAULT_PROMPT_REL})")
    ap.add_argument("--out-dir", default=None, help="Output directory (default: covers/ from config)")
    ap.add_argument("--basename", default="front-cover-art", help="Output filename stem")
    ap.add_argument("--refs", nargs="*", help="Override reference image paths (default: protagonist.strong_refs from config)")
    add_config_arg(ap)
    args = ap.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("OPENROUTER_API_KEY not set in environment")

    cfg = load_config(args.config)
    root = project_root(args.config)

    prompt_path = Path(args.prompt_file) if args.prompt_file else (root / DEFAULT_PROMPT_REL)
    if not prompt_path.is_absolute():
        prompt_path = (root / prompt_path).resolve()
    if not prompt_path.exists():
        sys.exit(f"prompt file not found: {prompt_path}")
    prompt = prompt_path.read_text()

    if args.refs:
        refs = [Path(p) if Path(p).is_absolute() else root / p for p in args.refs]
    else:
        refs = [root / p for p in cfg["protagonist"].get("strong_refs", [])]
        if not refs:
            refs = [root / cfg["protagonist"]["canonical_ref"]]
    missing = [str(p) for p in refs if not p.exists()]
    if missing:
        sys.exit(f"reference images not found: {missing}")

    out_dir = Path(args.out_dir) if args.out_dir else (root / cfg["paths"].get("covers_dir", "covers"))
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    content = [{"type": "text", "text": prompt}]
    for p in refs:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_for(p)};base64,{encode_image(p)}"},
        })
    print(f"-> attaching {len(refs)} reference images")

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "modalities": ["image", "text"],
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/shoemoney/gsd-book-skill",
            "X-Title": f"{cfg.get('title','Book')} front cover gen",
        },
        method="POST",
    )

    print(f"-> calling {MODEL} (30-90s)…")
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", errors="replace")
        sys.exit(f"HTTP {e.code}: {body_txt[:800]}")

    msg = data["choices"][0]["message"]
    images = msg.get("images") or []
    if not images:
        c = msg.get("content")
        if isinstance(c, list):
            images = [x for x in c if x.get("type") == "image_url"]
    if not images:
        sys.exit(f"No images in response. Raw: {json.dumps(data)[:1200]}")

    saved = []
    for i, img in enumerate(images):
        url = img.get("image_url", {}).get("url") if isinstance(img, dict) else None
        if not url or not url.startswith("data:"):
            continue
        header, b64 = url.split(",", 1)
        ext = "png" if "png" in header else "jpg"
        suffix = "" if i == 0 else f"-alt{i}"
        out_path = out_dir / f"{args.basename}{suffix}.{ext}"
        out_path.write_bytes(base64.b64decode(b64))
        saved.append(out_path)

    if not saved:
        sys.exit("Got response but no decodable image data.")
    for p in saved:
        print(f"OK wrote {p} ({p.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
