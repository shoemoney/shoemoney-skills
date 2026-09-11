"""Make the delivered folder self-repairing: ship the build scripts, the source
assets, and an AGENTS.md that orients an AI assistant who arrives later with no
context.

The reason this matters: six months from now someone will ask an assistant to
"fix the spine" or "change a chapter title", and that assistant will have the
output files but none of the reasoning. Without the scripts it cannot rebuild;
without AGENTS.md it will re-derive the wrong answers - recentre a deliberately
off-centre crop, hand-calculate a hardcover spine, or trust a LibreOffice render
that silently dropped blank pages.

    python3 ship_sources.py --pages 100
"""
import argparse, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kdp_calculator import measurements

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "AGENTS.md.template")

def copy_into(src, dstdir, label):
    if not os.path.exists(src):
        print(f"   !! missing {label}: {src}")
        return
    os.makedirs(dstdir, exist_ok=True)
    dst = os.path.join(dstdir, os.path.basename(src))
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    else:
        shutil.copy2(src, dst)
    print(f"   {os.path.basename(src)}")

def portable(path):
    """Let the shipped shell scripts run without this machine's venv."""
    if not os.path.exists(path):
        return
    s = open(path).read()
    s = re.sub(r"^P=\.venv/bin/python$", 'P="${PY:-python3}"', s, flags=re.M)
    s = s.replace(".venv/bin/python", "${PY:-python3}")
    s = s.replace('"$CH" --headless', '"${CHROME:-$CH}" --headless')
    open(path, "w").write(s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="book.json")
    ap.add_argument("--pages", type=int, required=True)
    ap.add_argument("--dist", default="dist")
    ap.add_argument("--work", default="build")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    cfg.setdefault("trim", [6.0, 9.0]); cfg.setdefault("paper", "cream")
    tw, th = cfg["trim"]
    trim_code = f"{tw:g}x{th:g}"
    out = f"{a.dist}/scripts"
    os.makedirs(out, exist_ok=True)

    print("scripts/")
    shutil.copy2(a.config, os.path.join(out, "book.json"))
    print("   book.json")
    for key in ("front", "back"):
        p = (cfg.get("art") or {}).get(key)
        if p:
            copy_into(p, out, f"{key} art")
    if cfg.get("manuscript"):
        copy_into(cfg["manuscript"], out, "manuscript")

    print("scripts/build/")
    wd = os.path.join(out, "build")
    os.makedirs(wd, exist_ok=True)
    for f in sorted(os.listdir(a.work)):
        p = os.path.join(a.work, f)
        if f == "fonts":
            copy_into(p, wd, "fonts")
        elif f.endswith((".py", ".sh")) and not f.endswith(".bak"):
            copy_into(p, wd, f)
        elif f.endswith(".json"):
            copy_into(p, wd, f)
    # the packaging/verification scripts live in the skill; ship copies too
    for f in ("kdp_calculator.py", "package_kdp.py", "write_listing.py",
              "verify.py", "fonts.py", "ship_sources.py"):
        copy_into(os.path.join(HERE, f), wd, f)
    for sh in ("all.sh", "build_everything.sh", "topdf.sh"):
        portable(os.path.join(wd, sh))

    pb = hc = None
    bindings = cfg.get("bindings") or {}
    if "paperback" in bindings:
        pb = measurements("paperback", trim_code, a.pages, paper=cfg["paper"])
    if "hardcover" in bindings:
        hc = measurements("hardcover", trim_code, a.pages, paper=cfg["paper"])
    def fmt(m, k, unit=""):
        return f"{m[k]}{unit}" if m else "n/a"
    vals = dict(
        TITLE=cfg.get("title_display") or cfg.get("title", ""),
        AUTHOR=cfg.get("author", ""),
        TRIM=f"{tw:g} x {th:g} in", TRIM_CODE=trim_code,
        PAGES=a.pages, PAPER=cfg["paper"].upper(), PAPER_LC=cfg["paper"],
        MANUSCRIPT=os.path.basename(cfg.get("manuscript", "manuscript.docx")),
        PB_SPINE=fmt(pb, "spine-width"), HC_SPINE=fmt(hc, "spine-width"),
        HC_PANEL=(f"{hc['front-cover-width']} x {hc['front-cover-height']} in" if hc else "n/a"),
        HC_HINGE=fmt(hc, "hinge-width"),
        PB_SIZE=(f"{pb['full-cover-width']}x{pb['full-cover-height']}" if pb else "n/a"),
        HC_SIZE=(f"{hc['full-cover-width']}x{hc['full-cover-height']}" if hc else "n/a"),
    )
    tpl = open(TEMPLATE).read()
    for k, v in vals.items():
        tpl = tpl.replace("{" + k + "}", str(v))
    leftover = re.findall(r"\{([A-Z_]+)\}", tpl)
    open(f"{a.dist}/AGENTS.md", "w").write(tpl)
    print(f"\nAGENTS.md -> {a.dist}/AGENTS.md")
    if leftover:
        print("   !! unfilled placeholders:", sorted(set(leftover)))
    print("   NOTE: sections 4 and 9 are marked REWRITE PER BOOK - fill in the "
          "actual cover decisions and any changes made to the author's words.")

if __name__ == "__main__":
    main()
