"""Shared config + KDP geometry for every script in this skill.

One book.json drives the whole pipeline. Everything that differs between books
(paths, metadata, palette, trim, back-cover copy) lives there; everything that
differs between BINDINGS (spine width, wrap allowance, hinge, safe area) is
computed here from KDP's published manufacturing rules.
"""
import json, os, functools

CFG_PATH = os.environ.get("KDP_BOOK", "book.json")

@functools.lru_cache(maxsize=1)
def cfg():
    with open(CFG_PATH) as fh:
        c = json.load(fh)
    c.setdefault("year", "")
    c.setdefault("paper", "cream")
    c.setdefault("trim", [6.0, 9.0])
    c.setdefault("dpi", 300)
    c.setdefault("notes_pages", True)
    c.setdefault("note_prompts", [])
    c.setdefault("dist", "dist")
    c.setdefault("work", "build")
    t = c.setdefault("type", {})
    t.setdefault("body_pt", 11.5); t.setdefault("leading", 1.68)
    m = c.setdefault("margins", {})
    m.setdefault("top", 0.78); m.setdefault("bottom", 0.72)
    m.setdefault("side", 0.75); m.setdefault("mirror_shift", 0.0625)
    p = c.setdefault("palette", {})
    p.setdefault("navy", "#041C46"); p.setdefault("gold", "#A16F16")
    p.setdefault("cream", "#F4F1ED"); p.setdefault("ink", "#1A1A1E")
    p.setdefault("white", "#FFFFFF")
    f = c.setdefault("fonts", {})
    f.setdefault("body", "Lora"); f.setdefault("display", "Oswald")
    f.setdefault("sans", "SourceSans3")
    f.setdefault("office_body", "Georgia"); f.setdefault("office_display", "Arial Narrow")
    return c

def rgb(name):
    h = cfg()["palette"][name].lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def trim():
    w, h = cfg()["trim"]
    return float(w), float(h)

# --- KDP paper calipers (inches per page), from KDP's paperback cover guide ---
CALIPER = {"white": 0.002252, "cream": 0.0025, "color": 0.002347,
           "premium-color": 0.002252}

# ---------------------------------------------------------------------------
# Binding geometry.
#
# PAPERBACK is fully specified by KDP: spine = pages x caliper, 0.125" bleed on
# every outer edge, 0.25" safe area inside the trim.
#
# HARDCOVER is NOT: KDP publishes the wrap (0.51"), the spine hinge (0.4") and
# the 0.635" text margin, but deliberately does not publish a spine-width
# formula - they route you through their Cover Calculator instead. So the spine
# width is a REQUIRED input for hardcover; we refuse to invent one. Get it from
# https://kdp.amazon.com/en-US/cover-calculator and put it in
# book.json -> bindings.hardcover.spine_width_in
# ---------------------------------------------------------------------------
def geometry(binding, pages):
    """Return every number needed to lay out a cover, in inches."""
    c = cfg()
    tw, th = trim()
    b = (c.get("bindings") or {}).get(binding, {})
    if binding == "paperback":
        cal = CALIPER[c["paper"]]
        spine = b.get("spine_width_in") or pages * cal
        bleed, hinge, safe = 0.125, 0.0, 0.25
        barcode_bottom, barcode_side = 0.25, 0.25
    elif binding == "hardcover":
        spine = b.get("spine_width_in")
        if not spine:
            raise SystemExit(
                "Hardcover spine width is missing. KDP does not publish a hardcover\n"
                "spine formula - fetch the real number from their Cover Calculator:\n"
                "  https://kdp.amazon.com/en-US/cover-calculator\n"
                f"  (Hardcover, {tw}x{th}, {pages} pages, B&W, {c['paper']} paper)\n"
                "then set bindings.hardcover.spine_width_in in book.json.")
        bleed, hinge, safe = 0.51, 0.4, 0.635 - 0.51
        barcode_bottom, barcode_side = 0.76, 0.25
    else:
        raise SystemExit(f"unknown binding {binding!r}")

    total_w = bleed + tw + hinge + spine + hinge + tw + bleed
    total_h = bleed + th + bleed
    g = dict(binding=binding, pages=pages, trim_w=tw, trim_h=th, spine=spine,
             bleed=bleed, hinge=hinge, safe=safe,
             barcode_bottom=barcode_bottom, barcode_side=barcode_side,
             total_w=total_w, total_h=total_h,
             back_x=bleed, spine_x=bleed + tw + hinge,
             front_x=bleed + tw + hinge + spine + hinge, panel_y=bleed)
    return g

def spine_text_allowed(binding, pages):
    """KDP allows spine text from 79 pages (paperback) and recommends 100+."""
    return pages >= (79 if binding == "paperback" else 79), pages >= 100

def px(inches):
    return int(round(inches * cfg()["dpi"]))

def out(*parts):
    p = os.path.join(cfg()["dist"], *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

def work(*parts):
    p = os.path.join(cfg()["work"], *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

if __name__ == "__main__":
    import sys
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    for bnd in (cfg().get("bindings") or {"paperback": {}}):
        try:
            g = geometry(bnd, pages)
        except SystemExit as e:
            print(f"{bnd}: {e}"); continue
        print(f"{bnd}: spine {g['spine']:.4f}in  wrap {g['total_w']:.3f} x {g['total_h']:.3f}in "
              f"({px(g['total_w'])} x {px(g['total_h'])}px @{cfg()['dpi']}dpi)")
