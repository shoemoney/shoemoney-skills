"""Shared launch-config loader used by every kdp-book-launch script.

Looks for `_launch_config.json` in the current working directory by default.
Override with --config or KDP_LAUNCH_CONFIG.

Strips JSON `_comment` keys so the config doc can carry inline notes
without breaking strict consumers.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


DEFAULT_CONFIG_NAME = "_launch_config.json"


def _strip_comments(obj):
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items() if k != "_comment"}
    if isinstance(obj, list):
        return [_strip_comments(x) for x in obj]
    return obj


def find_config(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.exists():
            sys.exit(f"config not found: {p}")
        return p

    env = os.environ.get("KDP_LAUNCH_CONFIG")
    if env:
        p = Path(env).expanduser().resolve()
        if not p.exists():
            sys.exit(f"config from env not found: {p}")
        return p

    p = Path.cwd() / DEFAULT_CONFIG_NAME
    if p.exists():
        return p

    sys.exit(
        f"no config found. Looked for ./{DEFAULT_CONFIG_NAME}, "
        f"$KDP_LAUNCH_CONFIG, and --config. "
        f"Copy templates/launch_config.json.template to your project root and edit."
    )


def load_config(explicit: str | None = None) -> dict:
    p = find_config(explicit)
    with open(p, "r") as f:
        data = json.load(f)
    return _strip_comments(data)


def project_root(cfg_path: str | None = None) -> Path:
    """Project root = directory containing the config file."""
    return find_config(cfg_path).parent


def add_config_arg(ap):
    ap.add_argument(
        "--config",
        default=None,
        help=f"Path to launch config JSON (default: ./{DEFAULT_CONFIG_NAME} or $KDP_LAUNCH_CONFIG)",
    )
