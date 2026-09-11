#!/usr/bin/env python3
"""Run design jury: N OpenRouter models review a product UI design brief.

Usage:
  python3 jury.py <brief.txt> [--models m1,m2,...] [--out-dir DIR]

Env:
  OPENROUTER_API_KEY (or key from ~/.hermes/.env, ~/.config/openrouter/key)

Prints paths to per-model JSON and a combined summary JSON on stdout last line:
  SUMMARY:/path/to/summary.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


DEFAULT_MODELS = [
    "anthropic/claude-opus-5",
    "openai/gpt-5.6-sol",
    "google/gemini-3.7-flash",
    "x-ai/grok-4.6",
    "deepseek/deepseek-v4-flash",
]


def find_key() -> str:
    env = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPEN_ROUTER_API_KEY")
    if env:
        return env.strip()
    home = Path.home()
    for p in (
        home / ".config/openrouter/key",
        home / ".hermes/.env",
        home / ".config/zsh/private/secrets.zsh",
    ):
        if not p.is_file():
            continue
        text = p.read_text(errors="ignore")
        m = re.search(r"sk-or-v1-[A-Za-z0-9]+", text)
        if m:
            return m.group(0)
        if p.name == "key":
            return text.strip()
    raise SystemExit("No OPENROUTER_API_KEY found")


def chat(key: str, model: str, brief: str, timeout: int = 240,
         max_tokens: int = 6000) -> dict:
    # Reasoning models spend the whole budget thinking and finish=length with an
    # empty content field. 2200 was enough before they were the default everywhere.
    payload = {
        "model": model,
        "temperature": 0.35,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Senior product designer + brand critic. "
                    "Output ONLY a single minified JSON object. No markdown fences. "
                    "No preamble."
                ),
            },
            {"role": "user", "content": brief},
        ],
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cue.shoemoney.ai",
            "X-Title": "Design Jury Loop",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
            return {"ok": True, "model": model, "http": resp.status, "raw": body}
    except Exception as e:
        return {"ok": False, "model": model, "error": str(e)}


def _salvage_partial(c: str) -> dict | None:
    out: dict = {}
    if re.search(r'"stop"\s*:\s*true', c, re.I):
        out["stop"] = True
    if re.search(r'"stop"\s*:\s*false', c, re.I):
        out["stop"] = False
    for bucket in ("general", "transitions", "professional", "top3_must"):
        mm = re.search(rf'"{bucket}"\s*:\s*\[(.*?)\]', c, re.S)
        if mm:
            items = re.findall(r'"((?:\\.|[^"\\])*)"', mm.group(1))
            out[bucket] = [bytes(i, "utf-8").decode("unicode_escape") for i in items]
    note = re.search(r'"model_note"\s*:\s*"((?:\\.|[^"\\])*)"', c)
    if note:
        out["model_note"] = bytes(note.group(1), "utf-8").decode("unicode_escape")
    fm = re.search(
        r'"font"\s*:\s*\{[^}]*"primary"\s*:\s*"((?:\\.|[^"\\])*)"', c, re.S
    )
    if fm:
        out["font"] = {"primary": bytes(fm.group(1), "utf-8").decode("unicode_escape")}
    return out or None


def parse_content(raw: dict) -> dict | None:
    """Extract JSON vote from chat/completions payload. Handles None content,
    reasoning-only models, markdown fences, and truncated JSON."""
    msg: dict = {}
    try:
        msg = (raw.get("choices") or [{}])[0].get("message") or {}
    except Exception:
        msg = {}
    c = msg.get("content")
    if not isinstance(c, str) or not c.strip():
        # reasoning models sometimes dump JSON only in reasoning
        for alt in ("reasoning", "refusal"):
            v = msg.get(alt)
            if isinstance(v, str) and "{" in v:
                c = v
                break
        if not isinstance(c, str):
            return None
    c = c.strip()
    c = re.sub(r"^```(?:json)?\s*", "", c, flags=re.I)
    c = re.sub(r"\s*```$", "", c)
    try:
        return json.loads(c)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", c, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return _salvage_partial(m.group(0)) or _salvage_partial(c)
        return _salvage_partial(c)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("brief", type=Path)
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/design-jury"))
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--max-tokens", type=int, default=6000)
    args = ap.parse_args()

    brief = args.brief.read_text()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    key = find_key()

    results = []
    with ThreadPoolExecutor(max_workers=len(models)) as ex:
        futs = {ex.submit(chat, key, m, brief, args.timeout, args.max_tokens): m for m in models}
        for fut in as_completed(futs):
            r = fut.result()
            safe = r["model"].replace("/", "_").replace(":", "_")
            path = out_dir / f"{safe}.json"
            path.write_text(json.dumps(r, indent=2))
            parsed = parse_content(r.get("raw") or {}) if r.get("ok") else None
            entry = {
                "model": r["model"],
                "ok": r.get("ok"),
                "path": str(path),
                "parsed": parsed,
                "error": r.get("error"),
            }
            results.append(entry)
            status = "OK" if parsed else ("ERR" if not r.get("ok") else "PARSE_FAIL")
            print(f"{status:10} {r['model']}", file=sys.stderr)

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "models": models,
        "results": results,
        "stop_votes": sum(
            1
            for r in results
            if (r.get("parsed") or {}).get("stop") is True
        ),
        "n_parsed": sum(1 for r in results if r.get("parsed")),
    }
    sp = out_dir / "summary.json"
    sp.write_text(json.dumps(summary, indent=2))
    print(f"SUMMARY:{sp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
