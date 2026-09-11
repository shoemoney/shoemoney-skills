#!/usr/bin/env python3
"""Deduplicate design-jury summary.json into improve.md skeleton + agreed queue.

Usage:
  python3 dedupe.py <summary.json> <out_improve.md> [--round N]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9 #→\-\.]+", "", s)
    return s[:120]


# Lightweight keyword buckets for auto-agree heuristics (agent still decides)
FORCE_AGREE_KEYS = (
    "prefers-reduced-motion",
    "reduced-motion",
    "ember",
    "palette",
    "wcag",
    "contrast",
    "webfont",
    "fraunces",
    "glass",
    "slutmode",
    "human always",
    "you send",
    "thumbnail",
    "dropzone",
    "trust",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("summary", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--round", type=int, default=1)
    args = ap.parse_args()

    data = json.loads(args.summary.read_text())
    buckets = {
        "general": defaultdict(list),
        "transitions": defaultdict(list),
        "professional": defaultdict(list),
        "top3_must": defaultdict(list),
    }
    fonts = []
    stops = data.get("stop_votes", 0)
    n = data.get("n_parsed", 0)

    for r in data.get("results", []):
        p = r.get("parsed") or {}
        model = r.get("model", "?")
        for b in buckets:
            val = p.get(b)
            if not isinstance(val, list):
                continue
            for item in val:
                if not isinstance(item, str):
                    continue
                buckets[b][norm(item)].append({"model": model, "text": item})
        if p.get("font"):
            fonts.append({"model": model, "font": p["font"]})

    lines = [
        f"# Design Jury — Round {args.round}",
        "",
        f"**Models parsed:** {n} · **stop votes:** {stops}",
        "",
        "## Deduped findings",
        "",
    ]

    agree_queue = []

    for bname, store in buckets.items():
        lines.append(f"### {bname}")
        lines.append("")
        lines.append("| Votes | Agree? | Item |")
        lines.append("|---|---|---|")
        # sort by vote count
        items = sorted(store.items(), key=lambda kv: -len(kv[1]))
        for i, (_k, votes) in enumerate(items, 1):
            text = votes[0]["text"]
            v = len(votes)
            auto = v >= 2 or any(k in text.lower() for k in FORCE_AGREE_KEYS)
            # top3 gets auto-agree at 2+
            if bname == "top3_must" and v >= 2:
                auto = True
            flag = "YES" if auto else "REVIEW"
            lines.append(f"| {v} | {flag} | {text.replace('|', '/')} |")
            if auto:
                agree_queue.append({"bucket": bname, "votes": v, "text": text})
        lines.append("")

    lines.append("## Font suggestions")
    lines.append("")
    for f in fonts:
        prim = (f["font"] or {}).get("primary", "")
        pair = (f["font"] or {}).get("pair", "")
        style = (f["font"] or {}).get("react_style", "")
        lines.append(f"- **{f['model']}:** {prim}" + (f" · pair: {pair}" if pair else ""))
        if style:
            lines.append(f"  - `{style}`")
    lines.append("")

    lines.append("## Auto-agree implementation queue (by votes)")
    lines.append("")
    agree_queue.sort(key=lambda x: -x["votes"])
    for i, a in enumerate(agree_queue, 1):
        lines.append(f"{i}. [{a['bucket']} · {a['votes']}×] {a['text']}")
    lines.append("")
    lines.append("## Agent decisions")
    lines.append("")
    lines.append(
        "_Fill during implement step: which YES items you shipped, which you skipped and why._"
    )
    lines.append("")
    lines.append("## Stop condition")
    lines.append("")
    lines.append(
        f"stop_votes={stops} / n_parsed={n}. "
        "Loop ends when stop_votes >= 3 OR agree queue is empty of shippable UI work."
    )
    lines.append("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines))
    print(f"WROTE:{args.out}")
    print(f"AGREE_COUNT:{len(agree_queue)}")
    print(f"STOP_VOTES:{stops}")
    print(f"N_PARSED:{n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
