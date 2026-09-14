"""Check 5 regression: stale-but-real shots must pass checks 1-4 and fail ONLY on age."""
import os, subprocess, sys, tempfile, json
from PIL import Image
import random

VS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_shots.py")  # the copy next to this test, never the installed one

def make_shots(d, n=4):
    """Real, distinct, colourful, MOVING frames - passes checks 1-4 by construction."""
    rnd = random.Random(7)
    for i in range(n):
        im = Image.new("RGB", (160, 90))
        px = im.load()
        for y in range(90):
            for x in range(160):
                px[x, y] = ((x * 3 + i * 60) % 256, (y * 5 + i * 40) % 256, rnd.randrange(256))
        im.save(os.path.join(d, "shot_%02d.png" % i))

def run(d, *args):
    p = subprocess.run([sys.executable, VS, d, *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

def backdate(d, seconds):
    for f in os.listdir(d):
        p = os.path.join(d, f)
        old = os.path.getmtime(p) - seconds
        os.utime(p, (old, old))

# 1. fresh shots pass everything
with tempfile.TemporaryDirectory() as d:
    make_shots(d)
    rc, out = run(d, "--min-shots", "3", "--max-age", "600")
    assert rc == 0, "fresh shots should pass:\n" + out
    assert "age=" in out, "ages should be reported:\n" + out
print("PASS fresh shots accepted, ages reported")

# 2. THE HOLE: day-old shots are real/distinct/colourful/moving -> checks 1-4 see nothing
with tempfile.TemporaryDirectory() as d:
    make_shots(d)
    backdate(d, 86400)
    rc, out = run(d, "--min-shots", "3")          # no --max-age, uniform age -> old gate blind
    assert rc == 0, "checks 1-4 alone should NOT catch stale shots (that is the hole):\n" + out
    rc, out = run(d, "--min-shots", "3", "--max-age", "600")
    assert rc == 1, "check 5 must reject day-old shots:\n" + out
    assert "PREVIOUS build" in out, "error must name the real cause:\n" + out
print("PASS stale shots slip past checks 1-4, and check 5 catches them")

# 3. mixed vintage caught with NO reference clock
with tempfile.TemporaryDirectory() as d:
    make_shots(d)
    p = os.path.join(d, "shot_00.png")
    old = os.path.getmtime(p) - 7200
    os.utime(p, (old, old))
    rc, out = run(d, "--min-shots", "3")           # no --max-age at all
    assert rc == 1, "MAX_SPREAD must catch mixed vintages with no --max-age:\n" + out
    assert "mixes capture runs" in out, out
print("PASS mixed-vintage dir caught with zero config")
print("ALL FRESHNESS CHECKS PASS")
