"""Benchmark reviewer models on one real dossier + shot set.

bench_reviewers.py <dossier> <shots_dir> [model ...]

Records, per model: wall-clock seconds, output size, and quality proxies. Quality is a
judgement call, but these proxies are the things that actually determine whether a cycle
does useful work:
  fixable%   - share of giveaways marked structural:false. Structural ones are unbuildable,
               so a model that fills the list with "be 3D" wastes the cycle.
  cited      - findings that point at a specific screen/screenshot. Uncheckable findings
               cannot be verified before Opus spends a plan on them.
  detail     - mean chars of what_i_see + why_it_outs_it + aaa_version.
  hedges     - "no mention of" / "described as" / "appears to" - reasoning about the write-up
               instead of the image, the exact failure this reviewer was rebuilt to kill.
"""
import sys
import os
import re
import json
import time
import subprocess
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.join(HERE, "aaa_review.py")
DEFAULT = ["openai/gpt-5.6-terra", "openai/gpt-5.6-sol", "google/gemini-3.6-flash",
           "google/gemini-3.5-flash", "x-ai/grok-4.3"]
HEDGE = re.compile(r"no mention|not mentioned|described as|repeatedly called|appears to be|"
                   r"seems to lack|dossier", re.I)

dossier, shots = sys.argv[1], sys.argv[2]
models = sys.argv[3:] or DEFAULT


def run(model):
    out = "/tmp/bench-%s.json" % re.sub(r"[^a-z0-9]+", "-", model.lower())
    t0 = time.time()
    p = subprocess.run([sys.executable, REVIEW, dossier, out, "--shots=" + shots,
                        "--model=" + model], capture_output=True, text=True, timeout=900)
    dt = time.time() - t0
    if p.returncode != 0 or not os.path.exists(out):
        return {"model": model, "error": (p.stderr or p.stdout)[-160:].strip(), "secs": dt}
    r = json.load(open(out))
    gs = r.get("giveaways") or []
    blob = json.dumps(gs)
    det = [len(g.get("what_i_see", "")) + len(g.get("why_it_outs_it", "")) +
           len(g.get("aaa_version", "")) for g in gs]
    return {
        "model": model, "secs": dt, "verdict": r.get("verdict"), "conf": r.get("confidence"),
        "n": len(gs),
        "fixable_pct": round(100 * sum(1 for g in gs if not g.get("structural")) / max(1, len(gs))),
        "cited": sum(1 for g in gs if re.search(r"screenshot|screen \d|shot \d|\bscreens?\b",
                                                g.get("where", ""), re.I)),
        "detail": round(sum(det) / max(1, len(det))),
        "hedges": len(HEDGE.findall(blob)),
        "bytes": len(blob),
    }


with cf.ThreadPoolExecutor(len(models)) as ex:
    rows = list(ex.map(run, models))

print("%-28s %6s %5s %4s %3s %8s %6s %7s %7s" %
      ("model", "secs", "conf", "n", "cit", "fixable%", "detail", "hedges", "bytes"))
for r in sorted(rows, key=lambda r: r.get("secs", 1e9)):
    if r.get("error"):
        print("%-28s %6.1f  ERROR %s" % (r["model"], r["secs"], r["error"][:70]))
        continue
    print("%-28s %6.1f %4s%% %4d %3d %7d%% %6d %7d %7d" %
          (r["model"], r["secs"], r["conf"], r["n"], r["cited"], r["fixable_pct"],
           r["detail"], r["hedges"], r["bytes"]))
