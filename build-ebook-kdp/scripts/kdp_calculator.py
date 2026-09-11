"""Ask KDP's own Cover Calculator for a book's cover geometry.

KDP publishes a spine formula for paperback but NOT for hardcover - the help
page routes you to their calculator instead. That calculator is backed by a
plain form POST that returns an HTML fragment, so we can query Amazon's real
production math rather than inventing numbers.

    python3 kdp_calculator.py --binding hardcover --trim 6x9 --pages 100 --paper cream

Results are cached in .kdp_cover_cache.json so a rebuild works offline.
"""
import argparse, json, os, re, html, urllib.request, urllib.parse

ENDPOINT = "https://kdp.amazon.com/cover-calculator/measurements-table"
CACHE = os.environ.get("KDP_COVER_CACHE", ".kdp_cover_cache.json")

BINDING = {"paperback": "PAPERBACK", "hardcover": "CASE_LAMINATE"}
PAPER   = {"cream": "CREAM", "white": "WHITE"}
INTERIOR = {"bw": "BLACK_AND_WHITE", "color": "STANDARD_COLOR",
            "premium-color": "PREMIUM_COLOR"}
FIELDS = ("full-cover-width", "full-cover-height", "front-cover-width",
          "front-cover-height", "margin-width", "wrap-width", "hinge-width",
          "spine-width", "spine-height", "spine-safe-area-width",
          "spine-margin-width", "barcode-margin-width", "barcode-margin-height")

def _cache():
    if os.path.exists(CACHE):
        try:
            return json.load(open(CACHE))
        except Exception:
            pass
    return {}

def measurements(binding, trim, pages, paper="cream", interior="bw", refresh=False):
    """trim like '6x9'. Returns a dict of inches, keyed as in FIELDS."""
    key = f"{binding}|{trim}|{pages}|{paper}|{interior}"
    c = _cache()
    if key in c and not refresh:
        return c[key]
    body = urllib.parse.urlencode({
        "bindingType": BINDING[binding], "paperType": PAPER[paper],
        "interiorType": INTERIOR[interior], "rightToLeft": "false",
        "trimSize": trim.upper().replace("X", "X") + "IN", "unit": "inches",
        "pageCount": str(pages)}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8", "replace")
    out = {}
    for f in FIELDS:
        m = re.search(rf'class="{f}"[^>]*>([^<]+)<', page)
        if m:
            try:
                out[f] = float(html.unescape(m.group(1)).strip())
            except ValueError:
                pass
    if "spine-width" not in out or "full-cover-width" not in out:
        raise SystemExit("KDP calculator returned no usable measurements. "
                         "Check the trim code (e.g. 6X9IN) and page count.")
    # sanity: panels + spine + wrap must reconstruct the full width
    # paperback reports the outer allowance as margin-width (bleed); hardcover
    # reports it as wrap-width (the paper that folds around the board).
    outer = out.get("wrap-width", out.get("margin-width", 0.0))
    out["outer"] = outer
    lhs = out["full-cover-width"]
    rhs = 2 * outer + 2 * out["front-cover-width"] + out["spine-width"]
    out["_reconstructs"] = abs(lhs - rhs) < 0.01
    c[key] = out
    json.dump(c, open(CACHE, "w"), indent=1, sort_keys=True)
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--binding", required=True, choices=sorted(BINDING))
    ap.add_argument("--trim", default="6x9")
    ap.add_argument("--pages", type=int, required=True)
    ap.add_argument("--paper", default="cream", choices=sorted(PAPER))
    ap.add_argument("--interior", default="bw", choices=sorted(INTERIOR))
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    m = measurements(a.binding, a.trim, a.pages, a.paper, a.interior, a.refresh)
    print(f"{a.binding} {a.trim} {a.pages}pp {a.paper}:")
    for k in FIELDS:
        if k in m:
            print(f"  {k:24s} {m[k]:8.3f} in   ({round(m[k]*300):5d} px @300dpi)")
    print(f"  geometry reconstructs: {m['_reconstructs']}")
