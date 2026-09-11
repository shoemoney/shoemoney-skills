"""Post-build assertions. Structural checks that would otherwise pass silently.

    python3 verify.py dist/Interior.pdf --expect-trim 6x9 --expect-even
    python3 verify.py dist/CoverWrap.pdf --expect-size 14.014x10.417
"""
import argparse, re, sys
from pypdf import PdfReader

def fonts_report(reader):
    embedded, missing, type3 = set(), set(), set()
    for i, p in enumerate(reader.pages, 1):
        for k, v in (p.get("/Resources", {}) or {}).get("/Font", {}).items():
            f = v.get_object()
            if str(f.get("/Subtype")) == "/Type3":
                type3.add((str(f.get("/BaseFont")), i))
            d = f.get("/DescendantFonts")
            if d:
                f = d[0].get_object()
            fd = f.get("/FontDescriptor")
            ok = bool(fd and any(x in fd for x in ("/FontFile", "/FontFile2", "/FontFile3")))
            (embedded if ok else missing).add(str(f.get("/BaseFont")))
    return embedded, missing, type3

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--expect-trim", help="e.g. 6x9")
    ap.add_argument("--expect-size", help="full cover, e.g. 14.014x10.417")
    ap.add_argument("--expect-even", action="store_true")
    ap.add_argument("--expect-pages", type=int)
    a = ap.parse_args()

    r = PdfReader(a.pdf)
    b = r.pages[0].mediabox
    w, h = float(b.width) / 72, float(b.height) / 72
    fails = []
    print(f"{a.pdf}\n  pages: {len(r.pages)}\n  size : {w:.3f} x {h:.3f} in")

    want = a.expect_trim or a.expect_size
    if want:
        ew, eh = (float(x) for x in want.lower().split("x"))
        if abs(w - ew) > 0.01 or abs(h - eh) > 0.01:
            fails.append(f"size {w:.3f}x{h:.3f} != expected {ew}x{eh}")
    if a.expect_even and len(r.pages) % 2:
        fails.append(f"page count {len(r.pages)} is odd - print interiors should be even")
    if a.expect_pages and len(r.pages) != a.expect_pages:
        fails.append(f"page count {len(r.pages)} != expected {a.expect_pages}")

    emb, miss, t3 = fonts_report(r)
    print(f"  fonts: {len(emb)} embedded")
    for f in sorted(emb):
        print(f"           {f}")
    if miss:
        fails.append(f"NOT embedded: {sorted(miss)}")
    if t3:
        fails.append(f"Type3 fonts (KDP dislikes these): {sorted(t3)}")

    # recto discipline: a chapter opener is a page whose text starts with a
    # number + caps, which is how the interior builder sets them.
    versos = []
    for i, p in enumerate(r.pages, 1):
        t = re.sub(r"\s+", " ", p.extract_text() or "").strip()
        if re.match(r"^\d{1,2} [A-Z]{3}", t) and i % 2 == 0:
            versos.append(i)
    if versos:
        fails.append(f"chapter openers on verso pages: {versos}")

    if fails:
        print("\nFAIL")
        for f in fails:
            print("  x", f)
        sys.exit(1)
    print("\nPASS")

if __name__ == "__main__":
    main()
