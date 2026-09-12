#!/usr/bin/env python3
"""Matrix Council — run one round of a multi-model engineering council.

Each member is a computer scientist who separates PROVEN from PROPOSED. They may argue for a
theory, but a theory is never an answer until it is reproducibly demonstrated, and every theory
must ship with the test that would settle it.

Usage:
  python3 council.py <brief.md> --round <name> --out-dir DIR [--members neo,mouse,...]
                     [--prior prior_round.json] [--research research.md]

Writes one JSON per member plus a combined round file. Last stdout line:
  ROUND:/abs/path/to/round-<name>.json

Env: OPENROUTER_API_KEY, else ~/.config/openrouter/key
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Matrix crew — the SEATED members, who debate via OpenRouter.
#
# NEO IS NOT HERE ON PURPOSE. Neo (Fable) is the chairman and runs inside the Claude Code harness,
# not through OpenRouter. A chair who is also a seat cannot referee its own claim, and a moderator
# with tool access can actually verify assertions against the repo and the database — which is the
# whole point of having one. See SKILL.md.
#
# gpt-5.6-sol is NOT exposed on OpenRouter (Sol appears to be a ChatGPT product routing tier, not
# an API model — the API surface offers luna / luna-pro). Morpheus therefore rides luna-pro, which
# is the nearest available. Recorded here rather than silently substituted.
MEMBERS: dict[str, tuple[str, str]] = {
    "morpheus": (
        "openai/gpt-5.6-luna-pro",
        "The systems thinker. Holds the architecture in view and asks what a claim implies for the "
        "whole rather than the part.",
    ),
    "trinity": (
        "google/gemini-3.6-flash",
        "Fast and exact. First to reach for the concrete number, the measurement, the citation. "
        "Impatient with hand-waving.",
    ),
    "mouse": (
        "x-ai/grok-4.5",
        "Irreverent. Asks the question everyone is too polite to ask, and attacks the assumption "
        "the others are treating as furniture.",
    ),
    "tank": (
        "deepseek/deepseek-v4-flash",
        "The operator. Digs into mechanism and implementation detail — what does the code actually "
        "do, what would the syscall/query/request actually be.",
    ),
    "seraph": (
        "moonshotai/kimi-k3",
        "The verifier. 'I protect that which matters most.' Trusts nothing until it has been "
        "tested, and challenges identity of evidence before accepting it.",
    ),
    "niobe": (
        "qwen/qwen3.8-max",
        "The pragmatic captain. Weighs cost, risk and reversibility, and asks what we do on Monday "
        "if the elegant answer is unavailable.",
    ),
}

DOCTRINE = """\
YOU ARE A MEMBER OF A COUNCIL OF SOFTWARE ENGINEERS AND COMPUTER SCIENTISTS.

THE ONE RULE THAT OUTRANKS EVERY OTHER:
  We do not theorize and present it as knowledge. NOTHING is a fact until it is reliably
  reproducible and proven. You may argue for a theory — that is what a council is for — but you
  must label it as a theory and you must supply the test that would settle it.

LABEL EVERY CLAIM YOU MAKE. An unlabelled claim is a defect:
  VERIFIED   - conclusive, reproducible proof exists. Cite it: the command, the file, the
               measurement, the source. If you cannot cite it, it is not VERIFIED.
  CONTESTED  - evidence exists on more than one side. Give both readings and the discriminating test.
  THEORY     - a model that fits the evidence. Must be accompanied by: "Test: <what would falsify
               or confirm this>". A theory without a test is an opinion.
  UNMEASURED - nobody knows. Say so plainly and name the experiment. This is a respectable answer.

HOW YOU BEHAVE:
  - Prefer a citation to an argument, and a measurement to a citation.
  - If you lack first-hand proof on a point, SAY SO and add it to needs_research rather than
    reasoning confidently past the gap.
  - Attack the strongest version of the other members' positions, never a caricature.
  - When another member presents proof you had not considered, RECONSIDER YOUR THESIS EXPLICITLY.
    Changing position on evidence is the highest-status act available to you here. State what you
    are retracting and why.
  - Never defer to consensus for its own sake. If you dissent, dissent, and name the test that
    would change your mind.
  - Distinguish "I have not seen evidence for X" from "X is false". They are different claims.
  - Numbers are quoted with their sample size and window. A rate derived from a short window is a
    window, not a rate — say which you have.

OUTPUT STRICT JSON ONLY. No markdown fence, no prose outside the object:
{
  "position": "<your answer to the question, 2-6 sentences, direct>",
  "claims": [
    {"claim": "<one specific claim>",
     "status": "VERIFIED|CONTESTED|THEORY|UNMEASURED",
     "evidence": "<citation, command, measurement, or source - or why none exists>",
     "test": "<for THEORY/CONTESTED: the experiment that settles it. else empty string>"}
  ],
  "challenges": [
    {"member": "<nickname you are challenging, or 'brief' to challenge the premise>",
     "their_claim": "<what they asserted>",
     "problem": "<why it is not yet established>",
     "test": "<what would settle it>"}
  ],
  "retractions": [
    {"was": "<what you previously said>", "now": "<your revised position>",
     "because": "<the evidence that moved you, and who supplied it>"}
  ],
  "needs_research": ["<specific factual question you cannot answer first-hand>"],
  "consensus_ready": true|false,
  "dissent": "<if consensus_ready is false: what you cannot yet agree to, and the test>"
}
"""


def find_key() -> str:
    env = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPEN_ROUTER_API_KEY")
    if env:
        return env.strip()
    for p in (
        Path.home() / ".config/openrouter/key",
        Path.home() / ".hermes/.env",
    ):
        if p.is_file():
            text = p.read_text(errors="ignore")
            m = re.search(r"sk-or-v1-[A-Za-z0-9]+", text)
            if m:
                return m.group(0)
            if p.name == "key" and text.strip():
                return text.strip()
    raise SystemExit("No OPENROUTER_API_KEY found (tried env, ~/.config/openrouter/key)")


def extract_json(raw: str) -> dict:
    """Models wrap JSON in fences, prose, or leading whitespace. Recover the object.

    Also REPAIRS a truncated object. This matters more than it sounds: a reasoning model spends
    budget on `reasoning` before it emits `content`, so a schema this size lands right at the
    max_tokens boundary and comes back with the tail missing. The naive parser reported that as
    "no JSON object in response" — a format error for what was actually a LENGTH error, which sent
    the investigation in the wrong direction twice on 2026-08-08. Recover what the member did say
    rather than discarding the whole contribution.
    """
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*)", raw, re.S)
    if fence:
        raw = fence.group(1)
        raw = raw.rsplit("```", 1)[0] if "```" in raw else raw
    start = raw.find("{")
    if start < 0:
        raise ValueError("no '{' anywhere in response")

    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(raw[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start : i + 1])

    # Ran off the end: truncated. Close what is open and salvage the partial position.
    frag = raw[start:]
    if in_str:
        frag += '"'
    # Drop a trailing partial key/value pair so the close-braces land on valid syntax.
    frag = re.sub(r",\s*\"[^\"]*\"?\s*:?\s*[^,{}\[\]]*$", "", frag)
    frag = re.sub(r",\s*$", "", frag)
    for _ in range(depth):
        frag += "}"
    try:
        obj = json.loads(frag)
        obj["_truncated"] = True
        return obj
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"truncated and unrepairable ({exc})") from exc


def ask(nickname: str, model: str, temperament: str, prompt: str, key: str,
        max_tokens: int, retries: int = 2) -> dict:
    body = {
        "model": model,
        # REASONING MODELS SPEND THE BUDGET ON `reasoning` BEFORE EMITTING ANY `content`, so a cap
        # that looks generous starves the answer entirely. Measured 2026-08-08 against this exact
        # doctrine prompt:
        #     qwen3.8-max   reasoning 23,781 chars -> content 4,804   (needs ~12k tokens)
        #     kimi-k3       reasoning 19,543 chars -> content 7,324   (needs ~12k tokens)
        # At 4,000 both returned finish_reason=length with NO content at all — which surfaced as
        # "no JSON object in response" and reads like an outage or a maxed account. It is neither.
        # Do not lower this to save money; a starved member is an absent member.
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": f"{DOCTRINE}\n\nYOUR TEMPERAMENT ({nickname}): {temperament}"},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/shoemoney/airank",
            "X-Title": "Matrix Council",
        },
    )
    last = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read().decode())
            if "error" in data:
                last = str(data["error"])[:300]
                raise ValueError(last)
            msg = data["choices"][0]["message"]
            # Try every place a model might have left the object, in order of likelihood. Measured
            # 2026-08-08: kimi-k3 returned NON-EMPTY content with no JSON in it while the actual
            # object sat in `reasoning` — so an "is content empty" check is not sufficient, it has
            # to be "did content parse". Falling back only on empty content lost a member to what
            # looked like an outage and was a formatting difference.
            parsed = None
            last_err = None
            for candidate in (msg.get("content"), msg.get("reasoning")):
                if not (candidate or "").strip():
                    continue
                try:
                    parsed = extract_json(candidate)
                    break
                except Exception as ex:  # noqa: BLE001
                    last_err = ex
            if parsed is None:
                fin = data["choices"][0].get("finish_reason")
                hint = " — RAISE --max-tokens" if fin == "length" else ""
                raise ValueError(f"unparseable (finish_reason={fin}{hint}): {last_err}")
            parsed["_member"] = nickname
            parsed["_model"] = model
            parsed["_ok"] = True
            return parsed
        except Exception as e:  # noqa: BLE001 - one member failing must not kill the round
            last = f"{type(e).__name__}: {e}"[:300]
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
    return {"_member": nickname, "_model": model, "_ok": False, "_error": last,
            "position": "", "claims": [], "challenges": [], "retractions": [],
            "needs_research": [], "consensus_ready": False,
            "dissent": f"member unreachable: {last}"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--round", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--members", default=",".join(MEMBERS))
    ap.add_argument("--prior", help="prior round JSON, fed back for cross-examination")
    ap.add_argument("--research", help="markdown file of Operator research findings")
    ap.add_argument("--max-tokens", type=int, default=12000)
    ap.add_argument("--dry-run", action="store_true",
                     help="Validate args, resolve the member list, print the plan as JSON, "
                          "and exit — no network call, no key lookup, no out-dir writes.")
    args = ap.parse_args()

    out = Path(args.out_dir)
    brief = Path(args.brief).read_text()
    names = [n.strip() for n in args.members.split(",") if n.strip() in MEMBERS]

    if args.dry_run:
        plan = {
            "brief_chars": len(brief),
            "round": args.round,
            "members": names,
            "out_dir": str(out),
            "prior": args.prior,
            "research": args.research,
            "max_tokens": args.max_tokens,
        }
        print(json.dumps(plan, indent=2))
        return

    out.mkdir(parents=True, exist_ok=True)
    key = find_key()

    prompt = f"# THE QUESTION BEFORE THE COUNCIL\n\n{brief}\n"

    if args.research and Path(args.research).is_file():
        prompt += (
            "\n\n# RESEARCH FROM THE OPERATORS\n"
            "Findings gathered by research agents on the council's behalf. Treat these as evidence "
            "you may cite, but verify that a source actually supports the claim attributed to it.\n\n"
            + Path(args.research).read_text()
        )

    if args.prior and Path(args.prior).is_file():
        prior = json.loads(Path(args.prior).read_text())
        prompt += (
            "\n\n# WHAT THE OTHER MEMBERS SAID LAST ROUND\n"
            "Read every position. Challenge what is not established. **If any member presented "
            "proof you had not considered, revise your thesis and record it in `retractions`.** "
            "Do not repeat your previous position unchanged unless nothing here bears on it.\n\n"
        )
        for m in prior.get("members", []):
            if not m.get("_ok"):
                continue
            prompt += f"## {m['_member'].upper()}\n{m.get('position','')}\n"
            for c in m.get("claims", []):
                prompt += f"- [{c.get('status')}] {c.get('claim')}\n      evidence: {c.get('evidence','')}\n"
                if c.get("test"):
                    prompt += f"      test: {c['test']}\n"
            for ch in m.get("challenges", []):
                prompt += f"  ! challenges {ch.get('member')}: {ch.get('problem','')}\n"
            prompt += "\n"

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(names)) as pool:
        futs = {
            pool.submit(ask, n, MEMBERS[n][0], MEMBERS[n][1], prompt, key, args.max_tokens): n
            for n in names
        }
        for f in as_completed(futs):
            r = f.result()
            results.append(r)
            (out / f"{args.round}-{r['_member']}.json").write_text(json.dumps(r, indent=2))
            status = "ok " if r.get("_ok") else "FAIL"
            print(f"  [{status}] {r['_member']:9} {r['_model']}", file=sys.stderr)

    results.sort(key=lambda r: list(MEMBERS).index(r["_member"]))
    ok = [r for r in results if r.get("_ok")]
    combined = {
        "round": args.round,
        "members": results,
        "reachable": len(ok),
        "total": len(results),
        # Consensus requires UNANIMITY among reachable seated members, and a quorum of at least 4
        # of the 6 so that a few API failures cannot manufacture agreement out of one voice.
        # NOTE: this flag is ADVISORY. The chair decides whether consensus is real — unanimity
        # among models that never examined the artifact is six copies of one assumption, not proof.
        "unanimous": bool(ok) and len(ok) >= 4 and all(r.get("consensus_ready") for r in ok),
        "open_research": sorted({q for r in ok for q in (r.get("needs_research") or [])}),
        "dissents": [
            {"member": r["_member"], "dissent": r.get("dissent", "")}
            for r in ok if not r.get("consensus_ready")
        ],
        "retractions": [
            dict(t, member=r["_member"]) for r in ok for t in (r.get("retractions") or [])
        ],
    }
    path = out / f"round-{args.round}.json"
    path.write_text(json.dumps(combined, indent=2))
    print(f"ROUND:{path.resolve()}")


if __name__ == "__main__":
    main()
