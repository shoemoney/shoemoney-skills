"""Force every chapter/section opener onto a recto (odd) page by inserting blanks,
then report the final page number of each opener so the Contents can be filled in."""
import json, re, sys
from pypdf import PdfReader, PdfWriter, PageObject
from pypdf.generic import RectangleObject

MARK = re.compile(r"\[\[OP:([a-z0-9-]+)\]\]")

def markers(reader):
    out = {}
    for i, p in enumerate(reader.pages):
        t = (p.extract_text() or "").replace(" ", "")
        for m in MARK.finditer(t):
            out.setdefault(i, []).append(m.group(1))
    return out

def run(src, dst):
    r = PdfReader(src)
    mk = markers(r)
    box = r.pages[0].mediabox
    W, H = float(box.width), float(box.height)

    out_pages = []
    pagenos = {}
    inserts = {}            # source page index -> name of the opener the blank precedes
    for i, p in enumerate(r.pages):
        if i in mk:
            if (len(out_pages) + 1) % 2 == 0:          # would be a verso -> push right
                out_pages.append(None)
                inserts[i] = mk[i][0]
            for name in mk[i]:
                pagenos[name] = len(out_pages) + 1
        out_pages.append(p)

    w = PdfWriter()
    for p in out_pages:
        if p is None:
            w.add_blank_page(width=W, height=H)
        else:
            w.add_page(p)
    with open(dst, "wb") as fh:
        w.write(fh)
    return pagenos, len(out_pages), inserts

if __name__ == "__main__":
    pagenos, n, inserts = run("build/raw_marked.pdf", "build/body.pdf")
    json.dump(pagenos, open("build/pagenos.json", "w"), indent=1)
    json.dump({str(k): v for k, v in inserts.items()}, open("build/inserts.json", "w"), indent=1)
    print(f"pages: {n}")
    for k, v in pagenos.items():
        print(f"  {k:>12} -> p{v} {'OK' if v % 2 else '!! VERSO'}")
