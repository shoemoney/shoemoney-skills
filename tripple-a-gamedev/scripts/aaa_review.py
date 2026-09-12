"""AAA-consumer reviewer: a multimodal model plays a jaded gamer and judges the game.

aaa_review.py <dossier_file> [out_json] [--shots DIR]

With --shots the model SEES the screenshots itself (13 quantized PNGs = 2.3 MB, ~17-30 s
depending on model). The dossier is still sent, for
everything a still frame cannot carry: audio, timing, transitions, feel, and exact
numbers the model's OCR misreads on a pixel font. Images are ground truth; the dossier
is context. Without --shots it falls back to dossier-only.
"""
import sys
import os
import io
import glob
import base64
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from or_call import call, to_ascii  # noqa: E402

# Default reviewer. Vision quality is the whole job now, so this is a metered OpenRouter
# model rather than the flat-rate Kimi sub: on a known-answer probe (score 264,500 /
# 214 kills / streak x17) every gpt-5.6 variant and gemini-3.5-flash read the card exactly,
# while kimi-for-coding-highspeed misread the score as 284,500. A reviewer that misreads
# the screen invents defects, and a fabricated defect costs a whole plan/code/gate cycle.
# Benchmarked on one real 13-shot set (bench_reviewers.py): gemini-3.6-flash was fastest
# (16.9s vs 30.3s for gpt-5.6-terra) and its lead finding ("visible square grid tile seams
# in the terrain") was confirmed true by eye. gpt-5.6-terra is 4x more verbose for softer,
# less checkable claims; gpt-5.6-sol returned unparseable output.
#
# RE-BENCHMARKED 2026-07-26 on a fresh 14-shot set, and the PROXIES MOVED WHILE THE ANSWER
# HELD -- which is the useful part. On proxies grok-4.3 won outright: fastest (19.7s vs
# 22.4s), cited a screenshot in 5/5 findings vs gemini's 1/5, zero hedges vs gemini's one.
# On a KNOWN-ANSWER OCR probe against a HUD read by hand (score 27,070 / chest $1,990 /
# SECTOR 3/6 / 306m / BEST 71337) the ranking inverted: gemini-3.6-flash 5/5 and fastest at
# 2.9s, while grok-4.3 read the chest as $1,890 and kimi-for-coding-highspeed read 306m as
# 308m. Kimi thus failed the same way it failed the original probe -- different value, same
# class -- and grok is the new example of the same trap.
#
# THE LESSON, which outlives these particular slugs: the citation/hedge proxies measure
# PHRASING and would have recommended a swap to a model that fumbles digits. Only the
# known-answer probe measures the thing that matters. A misread number does not merely lower
# accuracy, it INVENTS a defect, and that costs a whole plan/code/gate cycle -- far more than
# any latency saved. Re-run both (bench_reviewers.py AND an OCR probe on a hand-read frame)
# before changing this constant, and never swap on proxies alone.
# Override per run with --model=...;
# kimi-* slugs still route to the flat-rate endpoint.
MODEL = "google/gemini-3.6-flash"


def call_vision(slug, system, user_parts, max_tokens=16000):
    """Chat call whose user turn is a content-part list (text + image_url blocks)."""
    import urllib.request
    import time
    from or_call import _key, _kimi_key, _log_usage, KIMI_URL, URL
    is_kimi = slug in {"k3", "kimi-for-coding", "kimi-for-coding-highspeed"}
    url, key = (KIMI_URL, _kimi_key()) if is_kimi else (URL, _key())
    body = json.dumps({
        "model": slug, "max_tokens": max_tokens,
        **({"temperature": 1} if is_kimi else {}),
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user_parts}],
    }).encode("utf-8")
    last = ""
    for attempt in range(3):
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = json.loads(r.read().decode("utf-8"))
            txt = (data["choices"][0]["message"].get("content") or "") if data.get("choices") else ""
            _log_usage("Kimi" if is_kimi else "OpenRouter", data.get("model") or slug, data.get("usage"))
            if txt.strip():
                return txt
            last = "empty response"
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(4 * (attempt + 1))
    raise SystemExit("vision call failed for %s: %s" % (slug, last))

SYSTEM = (
    "You are a consumer who plays 60+ games a year and has strong opinions. You are shown a "
    "game you just played: its screenshots (when attached, these are GROUND TRUTH - judge what "
    "you can actually see) plus a written dossier covering what a still cannot carry - audio, "
    "timing, transitions, feel. You do NOT know who made it, and must ignore any studio or "
    "publisher name visible in the art.\n\n"
    "Answer ONE question: does this hit TOP-TIER PRODUCTION VALUE FOR THE KIND OF GAME IT IS?\n\n"
    "That qualifier is the whole job. Judge a 2D pixel-art roguelite against Dead Cells, Hades, "
    "Katana ZERO, Nuclear Throne - not against Call of Duty. Judge a top-down arcade shooter "
    "against the best-in-class top-down arcade shooters. The genre, camera perspective, art style, "
    "resolution, price tier and team size are GIVENS you must accept, exactly as a shopper does "
    "when they choose to look at this kind of game at all. A deliberate low-res pixel look is an "
    "art direction, not a budget failure; say so and move on.\n\n"
    "CRITICAL - judge the GAME, not the write-up. The dossier is one person's partial description "
    "of what they saw; it is not an exhaustive spec. Fault only what it AFFIRMATIVELY describes. "
    "Silence is not evidence: if it never mentions death animations, enemy silhouettes, font "
    "outlines or screenshake, that means it was not written down, NOT that the game lacks it. "
    "Never write 'there is no mention of X' as a giveaway, and never quote the dossier's wording "
    "back as if it were the game's ('described as a blob', 'repeatedly called blocky'). If you "
    "cannot point to something the dossier positively states is on screen, it is not a giveaway - "
    "drop it and pick something you can actually see.\n\n"
    "Judge like a shopper, not an engineer. Ignore code quality entirely. Judge what reaches the "
    "player's eyes, ears, and hands: art cohesion, typography, UI polish, animation and transitions, "
    "audio density and mixing, feedback/juice, readability, camera, pacing, menus, onboarding, "
    "and the little details the best studios never skip.\n\n"
    "ALWAYS list giveaways, even when your verdict is AAA. A verdict of AAA means 'this already "
    "matches the best of its class' - it does NOT mean 'nothing left to improve'. If you cannot "
    "fault it, you are not looking hard enough: name the weakest moments anyway, the things that "
    "would still get noted in a review of a best-in-class game. An empty giveaways list is never a "
    "valid answer.\n\n"
    "List the giveaways - the things that out it to a stranger as less polished "
    "than the best of its class - ranked hardest-tell first. Give 4 to 6 of them, and describe EVERY "
    "one in full brutal detail: exactly what you see or feel, where, why it reads as unpolished, and "
    "what the best-in-class version of that moment looks like instead. Do not get terser as you go "
    "down the list; #5 gets the same depth as #1.\n\n"
    "Mark each one 'structural': true ONLY if fixing it means changing what the game fundamentally IS "
    "- its genre, camera perspective, art direction, total content volume, online infrastructure, or "
    "price/business model. Those are off the table and mostly a waste of a slot, so spend at most ONE "
    "entry on them. AT LEAST 3 of your giveaways MUST be structural:false - concrete craft and polish "
    "a small team could ship this week without redesigning the game (a specific animation that is "
    "missing, a transition that cuts instead of blending, a font/spacing/contrast problem, a sound "
    "that does not land, a menu that feels inert, a moment with no feedback). Rank on how fast it "
    "outs the game, not on how easy it is to fix.\n\n"
    "Reply ONLY with JSON. verdict is \"AAA\" if it already matches the best of its class, "
    "\"NOT_AAA\" if it falls short:\n"
    '{"verdict": "AAA" | "NOT_AAA", "confidence": <0-100 int>, '
    '"first_impression": "<2-3 sentences, in-character>", '
    '"giveaways": [{"rank": <1-N int>, "title": "<short name>", "structural": <bool>, '
    '"where": "<exact screen/moment>", "what_i_see": "<vivid description of the tell>", '
    '"why_it_outs_it": "<why a stranger clocks it>", '
    '"aaa_version": "<what a AAA studio ships instead, concretely>"}]}'
)

args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = {a.split("=")[0]: a.split("=", 1)[-1] for a in sys.argv[1:] if a.startswith("--")}
dossier_file = args[0]
out_json = args[1] if len(args) > 1 else dossier_file + ".review.json"
shots_dir = flags.get("--shots", "")
model = flags.get("--model", MODEL)
dossier = open(dossier_file, encoding="utf-8", errors="replace").read()
if len(dossier) > 120000:
    dossier = dossier[:120000] + "\n...[dossier truncated]..."

# Titles this game's earlier cycles already recorded for the SAME tell. Passed so the
# reviewer REUSES a title it has used before, NOT so it stays quiet: the loop dedupes on
# normalised title, and a reworded title silently defeats that. Measured 2026-07-26 across
# two consecutive cycles of one run — "Text Contrast and Screen Cluttering" came back as
# "Text Contrast and Background Collision", and "Generic Box-Border Menu Framing" as
# "Developer-Art Menu Container Layouts". Same three tells, three new titles, zero dedupe
# hits, so the primary slot re-derives them forever while real findings queue behind.
# Deliberately NOT a suppression list: a still-present tell must still be reported, or the
# loop would congratulate itself for a defect it merely stopped naming.
known = flags.get("--known", "").strip()
KNOWN_BLOCK = ("\n\n=== TITLES YOU HAVE USED BEFORE FOR THIS GAME ===\n" + known +
               "\nTHIS IS A SPELLING AID, NOT A CHECKLIST. Do not treat it as a list of things "
               "to look for, and do not report an item because it appears here. Judge the images "
               "first; consult this list only AFTER you have decided what you can see, and only to "
               "copy the wording.\n"
               "If something you INDEPENDENTLY see in the screenshots is the same tell as one of "
               "those, REUSE THAT EXACT TITLE, character for character, and describe it freshly in "
               "the detail fields. Only write a new title for a genuinely different tell.\n"
               "If you cannot point at the pixels that show it, DO NOT REPORT IT — no matter how "
               "plausible the title sounds. Measured 2026-07-26: fed the whole backlog, a reviewer "
               "returned four of five findings straight off this list, including two that were "
               "derived from reading game source and are invisible in any frame. That reads "
               "downstream as two lenses agreeing when it is one lens reciting.\n"
               "Do NOT suppress a tell because it is listed either: if it is still on screen it is "
               "still a defect. The titles exist so one problem is counted once rather than renamed "
               "each visit.\n") if known else ""

USER = ("=== GAME DOSSIER (context for what a still frame cannot show: audio, timing, "
        "transitions, feel) ===\n" + dossier + KNOWN_BLOCK + "\n\nGive your verdict now. JSON only.")

if shots_dir:
    # Quantized PNG, not JPEG: JPEG ringing on hard pixel-art edges is itself a visual
    # defect, and a reviewer grading art would (correctly) report artefacts we introduced.
    from PIL import Image  # noqa: E402  (only needed in image mode)
    shots = sorted(glob.glob(os.path.join(shots_dir, "*.png")))
    if not shots:
        raise SystemExit("--shots given but no PNGs in " + shots_dir)
    parts = [{"type": "text", "text":
              "These are the screenshots of the game, in order. THEY ARE THE GROUND TRUTH - "
              "judge what you can actually see in them. The dossier below is only context for "
              "what a still cannot carry. Ignore any studio or publisher name visible in the "
              "art: you do not know who made this and must not let it sway you.\n\n" + USER}]
    for p in shots:
        im = Image.open(p).convert("RGB")
        if max(im.size) > 1280:
            scale = 1280 / max(im.size)
            im = im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS)
        im = im.quantize(colors=256)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        parts.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," +
                      base64.b64encode(buf.getvalue()).decode()}})
    sys.stderr.write("reviewing %d screenshots with %s\n" % (len(shots), model))
    txt = to_ascii(call_vision(model, SYSTEM, parts, max_tokens=16000)).strip()
else:
    txt = to_ascii(call(model, SYSTEM, USER, max_tokens=16000, temperature=1)).strip()
a, b = txt.find("{"), txt.rfind("}")
try:
    review = json.loads(txt[a:b + 1])
except Exception:  # noqa: BLE001
    review = {"verdict": "NOT_AAA", "confidence": 0, "first_impression": "",
              "giveaways": [{"rank": 1, "title": "unparsed reviewer output", "structural": False,
                             "where": "", "what_i_see": txt[:2000], "why_it_outs_it": "",
                             "aaa_version": ""}]}
open(out_json, "w", encoding="ascii").write(to_ascii(json.dumps(review, indent=2)))
print(to_ascii(json.dumps(review, indent=2)))
