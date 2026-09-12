"""Generic OpenRouter chat helper. ASCII-only I/O. Reused by reviewers + judge."""
import os
import sys
import json
import time
import urllib.request

URL = "https://openrouter.ai/api/v1/chat/completions"
KIMI_URL = "https://api.kimi.com/coding/v1/chat/completions"
# Native kimi.com coding-sub models (flat-rate) — routed off metered OpenRouter.
KIMI_MODELS = {"k3", "kimi-for-coding", "kimi-for-coding-highspeed"}


def _aigate_env():
    p = os.path.expanduser("~/.claude/aigate/env")
    out = {}
    if os.path.exists(p):
        for ln in open(p):
            ln = ln.strip()
            if ln.startswith("export "):
                ln = ln[7:]
            if "=" in ln:
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _key():
    # No default aigate host here (vendored copy): AIGATE_URL must be set explicitly
    # (in ~/.claude/aigate/env or the environment) or the aigate lookup is skipped
    # entirely and we fall through to the other sources below, in this order.
    env = _aigate_env()
    base = env.get("AIGATE_URL", os.environ.get("AIGATE_URL", ""))
    tok = env.get("AIGATE_TOKEN", os.environ.get("AIGATE_TOKEN", ""))
    if base and tok:
        try:
            req = urllib.request.Request(
                base + "/api/keys/openrouter",
                headers={"Authorization": "Bearer " + tok})
            with urllib.request.urlopen(req, timeout=30) as r:
                k = json.loads(r.read().decode("utf-8")).get("key", "")
            if k:
                return k
        except Exception:  # noqa: BLE001
            pass
    p = os.path.expanduser("~/.config/openrouter/key")
    if os.path.exists(p):
        k = open(p).read().strip()
        if k:
            return k
    return os.environ.get("OPENROUTER_API_KEY", "")


def _kimi_key():
    # aigate provider `kimi` = the flat-rate kimi.com coding sub (prefix sk-kimi-).
    # Same no-default-host rule as _key(): skip the aigate lookup when AIGATE_URL
    # is unset and fall through to KIMI_API_KEY.
    env = _aigate_env()
    base = env.get("AIGATE_URL", os.environ.get("AIGATE_URL", ""))
    tok = env.get("AIGATE_TOKEN", os.environ.get("AIGATE_TOKEN", ""))
    if base and tok:
        try:
            req = urllib.request.Request(
                base + "/api/keys/kimi",
                headers={"Authorization": "Bearer " + tok})
            with urllib.request.urlopen(req, timeout=30) as r:
                k = json.loads(r.read().decode("utf-8")).get("key", "")
            if k:
                return k
        except Exception:  # noqa: BLE001
            pass
    return os.environ.get("KIMI_API_KEY", "")


LEDGER = os.environ.get(
    "MODEL_USAGE_LOG", os.path.expanduser("~/.claude/aigate/model-usage.jsonl"))


def _log_usage(provider, slug, usage):
    # aigate vaults the key but is not a proxy, so nothing else sees these calls.
    # Record the usage block verbatim; usage_report.py prices it. Never fail a call.
    if not usage:
        return
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a") as f:
            f.write(json.dumps({"ts": time.time(), "provider": provider,
                                "model": slug, "usage": usage}) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _post(url, key, provider, slug, system, user, max_tokens, temperature, retries, timeout):
    if not key:
        raise SystemExit("no %s key" % provider)
    body = json.dumps({
        "model": slug,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode("utf-8")
    last = ""
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            txt = (data["choices"][0]["message"].get("content") or "") if data.get("choices") else ""
            _log_usage(provider, data.get("model") or slug, data.get("usage"))
            if txt.strip():
                return txt
            last = "empty response"
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(4 * (attempt + 1))
    raise SystemExit("%s call failed for %s: %s" % (provider, slug, last))


def call_kimi(slug, system, user, max_tokens=16000, temperature=0.4, retries=3):
    # Native kimi.com coding sub. Reasoning is SLOW -> 240s timeout (90s returns empty).
    # Clean JSON lands in message.content; CoT stays in the separate reasoning_content field.
    # Endpoint rejects any temperature != 1 for these models, so force it (caller's is ignored).
    return _post(KIMI_URL, _kimi_key(), "Kimi", slug, system, user,
                 max_tokens, 1, retries, 240)


def call(slug, system, user, max_tokens=16000, temperature=0.4, retries=3):
    # Dispatch native kimi models to the flat-rate coding endpoint, everything else to OpenRouter.
    if slug in KIMI_MODELS:
        return call_kimi(slug, system, user, max_tokens, temperature, retries)
    return _post(URL, _key(), "OpenRouter", slug, system, user,
                 max_tokens, temperature, retries, 240)


def to_ascii(s):
    return (s.replace("—", "-").replace("–", "-")
             .replace("‘", "'").replace("’", "'")
             .replace("“", '"').replace("”", '"')
             .replace("…", "...").replace(" ", " ")
             .encode("ascii", "ignore").decode("ascii"))


if __name__ == "__main__":
    print(call(sys.argv[1], "You are terse.", sys.argv[2] if len(sys.argv) > 2 else "hi", 200))
