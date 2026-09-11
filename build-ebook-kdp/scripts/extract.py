import re, json, html

XML = "/private/tmp/claude-502/-Users-shoemoney-Projects-juliesbook/e7a150fd-9f02-46e4-9d59-cd4e7affdfc9/scratchpad/dx/word/document.xml"
d = open(XML, encoding="utf8").read()
body = d[d.index("<w:body>"):]
paras = re.findall(r"<w:p\b[^>]*>.*?</w:p>|<w:p\b[^>]*/>", body, re.S)

def runs_of(p):
    """Return list of (text, bold, italic); <w:br/> becomes '\n'."""
    out = []
    for m in re.finditer(r"<w:r\b[^>]*>(.*?)</w:r>", p, re.S):
        r = m.group(1)
        rpr = re.search(r"<w:rPr>.*?</w:rPr>", r, re.S)
        rpr = rpr.group(0) if rpr else ""
        b = "<w:b/>" in rpr or "<w:b " in rpr
        i = "<w:i/>" in rpr or "<w:i " in rpr
        # walk text + breaks in order
        for t in re.finditer(r"<w:t[^>]*>(.*?)</w:t>|<w:br[^>]*/>|<w:tab[^>]*/>", r, re.S):
            if t.group(0).startswith("<w:br"):
                out.append(("\n", b, i))
            elif t.group(0).startswith("<w:tab"):
                out.append(("\t", b, i))
            else:
                out.append((html.unescape(t.group(1)), b, i))
    return out

items = []
for idx, p in enumerate(paras):
    rs = runs_of(p)
    text = "".join(t for t, _, _ in rs)
    if not text.strip():
        continue
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S)
    ppr = ppr.group(0) if ppr else ""
    center = 'w:val="center"' in ppr
    sizes = set(int(s) for s in re.findall(r'<w:sz w:val="(\d+)"', p))
    mx = max(sizes) if sizes else 22
    allbold = all(b for t, b, _ in rs if t.strip())
    items.append(dict(i=idx, text=text, center=center, sz=mx, bold=allbold,
                      runs=[[t, b, i2] for t, b, i2 in rs]))

json.dump(items, open("build/paras.json", "w"), indent=1)
print(f"{len(items)} non-empty paragraphs")
