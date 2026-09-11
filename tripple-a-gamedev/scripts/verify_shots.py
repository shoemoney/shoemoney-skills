"""Gate a screenshot directory before anything downstream is allowed to trust it.

verify_shots.py <shots_dir> [--min-shots N] [--json out.json]

Exists because of a real failure: the harness printed "SAVED" for all 12 shots while writing
12 byte-identical solid-black PNGs. Every stage downstream (dossier -> consumer review -> plan
-> code) then ran on a description that could not have come from the images, and nothing in the
pipeline noticed. A blank capture must be a HARD failure, never a silent one.

Checks, in order of how badly they burn you:
  1. images exist at all, and at least --min-shots of them
  2. no image is byte-identical to another (identical shots == the pose never reached the
     viewport; this is exactly what a frozen/pre-render capture produces)
  3. each image carries real signal: >= MIN_COLORS distinct colours and a luma std dev above
     MIN_STDDEV (a near-black or flat-fill frame fails both)
  4. the frames actually CHANGE across the run (see MIN_MOTION)
  5. the frames are from THIS run, not left over from a previous one (see --max-age / MAX_SPREAD)

Check 4 exists because of the second real failure: the live capture injected no input, so
every shot for ~45 review cycles was the same soldier standing still at sector 1, dying and
respawning. Checks 1-3 all passed — the frames were colourful and byte-distinct (the terrain
scrolls on its own), so nothing downstream noticed the reviewer had never seen the game played.
Measured on this project: an input-less run averages ~2.0 mean consecutive-frame luma delta
(min 0.1); a played one averages ~14.7 (min 3.0).

Check 5 closes a hole the other four CANNOT see, because a stale shot is a perfectly good
image. If a capture writes somewhere other than where the reviewer reads — the capture tool
resolving a relative path against ITS OWN cwd rather than the agent's is the common cause,
and agents running with isolation:'worktree' make the two diverge by construction — then the
expected dir still holds LAST cycle's PNGs. Those are real, distinct, colourful and moving,
so checks 1-4 all pass and the reviewer confidently judges a build that no longer exists.
Observed 2026-07-26 outside this repo: a screenshot tool reported writing './shot.jpeg' twice
and both times the file was not at that path relative to the agent's cwd — the second time
specifically because the agent had entered a worktree and the tool had not.
Pass --max-age with the capture's start time. MAX_SPREAD is the zero-config half: it needs no
reference clock, and a directory holding both fresh and week-old PNGs is mixed vintage by
definition.

Exit 0 = usable. Exit 1 = do not proceed. Prints a human-readable report either way.
"""
import sys
import os
import json
import time
import hashlib

MIN_COLORS = 12      # a real game frame has far more; a flat/blank fill has 1-3
MIN_STDDEV = 6.0     # luma spread; solid or near-solid frames sit near 0
SAMPLE_STRIDE = 4    # subsample for speed - plenty for a blank/not-blank decision
MIN_MOTION = 5.0     # mean consecutive-frame luma delta; idle capture ~2.0, played ~14.7
MOTION_MIN_SHOTS = 3  # below this there is no meaningful "over time" to measure
MAX_SPREAD = 3600.0  # seconds between oldest and newest shot; a real capture run is seconds
                     # apart, so a wide spread means this dir mixes runs (check 5)


def _load(path):
    from PIL import Image
    with Image.open(path) as im:
        return im.convert("RGB")


def _stats(path):
    im = _load(path)
    w, h = im.size
    px = im.load()
    colors, lumas = set(), []
    for y in range(0, h, SAMPLE_STRIDE):
        for x in range(0, w, SAMPLE_STRIDE):
            r, g, b = px[x, y]
            colors.add((r, g, b))
            lumas.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
    n = len(lumas) or 1
    mean = sum(lumas) / n
    std = (sum((v - mean) ** 2 for v in lumas) / n) ** 0.5
    return {"size": [w, h], "distinct_colors": len(colors), "stddev": round(std, 2)}


def _motion(shots_dir, pngs):
    """Mean absolute luma delta between consecutive shots, or None if not measurable."""
    if len(pngs) < MOTION_MIN_SHOTS:
        return None
    try:
        from PIL import Image, ImageChops
    except Exception:  # noqa: BLE001
        return None
    deltas, prev = [], None
    for f in pngs:
        try:
            with Image.open(os.path.join(shots_dir, f)) as im:
                # Downscale first: the decision is about scene change, not pixel noise,
                # and a thumbnail makes this free even for a long run.
                cur = im.convert("L").resize((160, 90))
        except Exception:  # noqa: BLE001
            return None
        if prev is not None:
            d = ImageChops.difference(prev, cur).tobytes()
            deltas.append(sum(d) / len(d))
        prev = cur
    return round(sum(deltas) / len(deltas), 2) if deltas else None


def main():
    argv = sys.argv[1:]
    if not argv:
        print("usage: verify_shots.py <shots_dir> [--min-shots N] [--json out.json] "
              "[--max-age SECONDS]")
        return 2
    shots_dir = argv[0]
    min_shots = 1
    out_json = None
    max_age = None
    for i, a in enumerate(argv):
        if a == "--min-shots" and i + 1 < len(argv):
            min_shots = int(argv[i + 1])
        if a == "--json" and i + 1 < len(argv):
            out_json = argv[i + 1]
        if a == "--max-age" and i + 1 < len(argv):
            max_age = float(argv[i + 1])

    report = {"dir": shots_dir, "ok": False, "shots": [], "errors": []}
    now = time.time()

    if not os.path.isdir(shots_dir):
        report["errors"].append("shots dir does not exist: %s" % shots_dir)
        return _finish(report, out_json)

    pngs = sorted(f for f in os.listdir(shots_dir) if f.lower().endswith(".png"))
    if len(pngs) < min_shots:
        report["errors"].append("found %d PNGs, expected at least %d" % (len(pngs), min_shots))

    digests = {}
    for f in pngs:
        p = os.path.join(shots_dir, f)
        entry = {"name": f, "bytes": os.path.getsize(p), "age_s": round(now - os.path.getmtime(p), 1)}
        d = hashlib.md5(open(p, "rb").read()).hexdigest()
        digests.setdefault(d, []).append(f)
        try:
            entry.update(_stats(p))
            if entry["distinct_colors"] < MIN_COLORS:
                entry["blank"] = True
                report["errors"].append(
                    "%s: only %d distinct colours (< %d) - frame is blank/flat"
                    % (f, entry["distinct_colors"], MIN_COLORS))
            elif entry["stddev"] < MIN_STDDEV:
                entry["blank"] = True
                report["errors"].append(
                    "%s: luma stddev %.2f (< %.1f) - frame carries no image"
                    % (f, entry["stddev"], MIN_STDDEV))
        except Exception as e:  # noqa: BLE001
            report["errors"].append("%s: could not read image (%s)" % (f, e))
        report["shots"].append(entry)

    for d, names in digests.items():
        if len(names) > 1:
            report["errors"].append(
                "identical images (the pose never reached the viewport): %s" % ", ".join(names))

    motion = _motion(shots_dir, pngs)
    if motion is not None:
        report["motion"] = motion
        if motion < MIN_MOTION:
            report["errors"].append(
                "frames barely change over the run (mean luma delta %.2f < %.1f) - the capture is "
                "of an IDLE game, not a played one. Check the harness injects input "
                "(main.demo_autoplay)." % (motion, MIN_MOTION))

    # Check 5: are these shots from THIS run? A leftover PNG is a perfectly good image,
    # so nothing above can see it. Age is the only channel that distinguishes them.
    ages = [s["age_s"] for s in report["shots"] if "age_s" in s]
    if ages:
        report["age_newest_s"], report["age_oldest_s"] = min(ages), max(ages)
        if max_age is not None and report["age_oldest_s"] > max_age:
            stale = [s["name"] for s in report["shots"] if s.get("age_s", 0) > max_age]
            report["errors"].append(
                "%d shot(s) older than --max-age %.0fs (oldest %.0fs): %s - the capture did NOT "
                "write here this run, so these are a PREVIOUS build. Check the capture tool's cwd "
                "(a relative shot path resolves against ITS cwd, not the agent's - worktrees "
                "diverge)." % (len(stale), max_age, report["age_oldest_s"], ", ".join(stale[:4])))
        spread = report["age_oldest_s"] - report["age_newest_s"]
        report["age_spread_s"] = round(spread, 1)
        if spread > MAX_SPREAD:
            report["errors"].append(
                "shot mtimes span %.0fs (> %.0f) - this directory mixes capture runs. Clear it "
                "before capturing so a stale frame cannot reach the reviewer." % (spread, MAX_SPREAD))

    report["unique"] = len(digests)
    report["count"] = len(pngs)
    report["ok"] = not report["errors"]
    return _finish(report, out_json)


def _finish(report, out_json):
    if out_json:
        open(out_json, "w").write(json.dumps(report, indent=2))
    if report["ok"]:
        print("SHOTS OK: %d images, %d unique, motion %s, newest %ss old"
              % (report["count"], report["unique"], report.get("motion", "n/a"),
                 report.get("age_newest_s", "?")))
        for s in report["shots"]:
            print("  %-42s %6d B  colors=%-6d stddev=%-6s age=%ss"
                  % (s["name"], s["bytes"], s.get("distinct_colors", -1),
                     s.get("stddev", "?"), s.get("age_s", "?")))
        return 0
    print("SHOTS UNUSABLE - refusing to hand these to the reviewer:")
    for e in report["errors"]:
        print("  ! " + e)
    print("\nThe capture 'succeeding' (SAVED lines, files on disk) means nothing on its own.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
