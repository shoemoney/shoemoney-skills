"""Reflowable EPUB 3 for Kindle (KDP eBook)."""
import json, os, zipfile, html, uuid, shutil
from typo import smart, smart_runs

BOOK = json.load(open("build/book.json"))
M = BOOK["meta"]
PROMPTS = json.load(open("build/prompts.json"))
UID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "onecallsalesperson-neill-2026"))
OUT = "dist/2_KINDLE/OneCallSalesperson_Kindle.epub"

def esc(s): return html.escape(smart(s), quote=False)

def runs_html(runs):
    out = []
    for t, b, i in smart_runs(runs):
        x = html.escape(t, quote=False).replace("\n", "<br/>")
        if b: x = f"<strong>{x}</strong>"
        if i: x = f"<em>{x}</em>"
        out.append(x)
    return "".join(out)

def page(title, body, cls=""):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head><meta charset="utf-8"/><title>{esc(title)}</title>
<link rel="stylesheet" type="text/css" href="../style.css"/></head>
<body class="{cls}">
{body}
</body></html>'''

CSS = """@charset "utf-8";
body { margin: 0 5%; line-height: 1.5; text-align: justify; }
h1.chap-title { font-size: 1.32em; text-align: center; text-transform: uppercase;
  letter-spacing: 0.09em; line-height: 1.3; margin: 0 0 1.4em; font-weight: bold; }
p.chap-num { text-align: center; font-size: 2.6em; font-weight: bold;
  margin: 1.2em 0 0.1em; line-height: 1; }
hr.chap-rule { width: 18%; border: none; border-top: 3px solid currentColor;
  margin: 0.35em auto 0.9em; }
h2.sub { font-size: 1.0em; text-transform: uppercase; letter-spacing: 0.08em;
  text-align: left; margin: 1.7em 0 0.6em; font-weight: bold; page-break-after: avoid; }
h1.fm { font-size: 1.2em; text-align: center; text-transform: uppercase;
  letter-spacing: 0.16em; margin: 1.6em 0 0.3em; }
p { margin: 0; text-indent: 1.3em; }
p.first, p.noindent { text-indent: 0; }
p.lead { text-indent: 0; font-weight: bold; margin: 0.85em 0; text-align: left; }
div.prompt { margin: 2.2em 8% 1em; padding-top: 0.9em; border-top: 2px solid currentColor;
  text-align: center; }
div.prompt .lbl { font-size: 0.76em; text-transform: uppercase; letter-spacing: 0.18em;
  display: block; margin-bottom: 0.5em; }
div.prompt .q { font-style: italic; }
div.titlepage { text-align: center; margin-top: 22%; }
div.titlepage .t { font-size: 2.0em; font-weight: bold; line-height: 1.1;
  text-transform: uppercase; letter-spacing: 0.02em; }
div.titlepage .s { font-size: 1.05em; text-transform: uppercase; letter-spacing: 0.13em;
  margin-top: 1.1em; }
div.titlepage .a { font-size: 1.1em; text-transform: uppercase; letter-spacing: 0.2em;
  margin-top: 3.2em; }
div.dedication { text-align: center; font-style: italic; margin: 25% 8% 0; text-indent: 0; }
p.copy { font-size: 0.82em; text-indent: 0; margin-bottom: 0.8em; text-align: left; }
nav ol { list-style: none; padding-left: 0; }
nav li { margin: 0.42em 0; }
img.cover { width: 100%; height: auto; }
"""

def chap_file(i, c):
    return f"text/ch{i:02d}.xhtml"

files = {}

# cover
files["text/cover.xhtml"] = page("Cover",
    '<div style="text-align:center;margin:0;padding:0">'
    '<img class="cover" src="../images/cover.jpg" alt="The One Call Salesperson"/></div>',
    cls="cover")

files["text/title.xhtml"] = page("Title Page",
    f'<div class="titlepage"><div class="t">{esc(M["title_line1"])}<br/>{esc(M["title_line2"])}</div>'
    f'<div class="s">{esc(M["subtitle"])}</div>'
    f'<div class="a">{esc(M["author"])}</div></div>')

cp = "".join(f'<p class="copy">{esc(l)}</p>' for l in BOOK["copyright"] if l.strip())
files["text/copyright.xhtml"] = page("Copyright", cp)

files["text/dedication.xhtml"] = page("Dedication",
    f'<div class="dedication">{esc(BOOK["dedication"])}</div>')

grat = "".join(f'<p class="{"first" if i==0 else "noindent"}">{runs_html(b["runs"])}</p>'
               for i, b in enumerate(BOOK["gratitude"]))
files["text/gratitude.xhtml"] = page("A Note of Gratitude",
    '<h1 class="fm">A Note of Gratitude</h1>' + grat)

spine_items = ["text/cover.xhtml", "text/title.xhtml", "text/copyright.xhtml",
               "text/dedication.xhtml", "nav.xhtml", "text/gratitude.xhtml"]
toc = [("A Note of Gratitude", "text/gratitude.xhtml")]

for i, c in enumerate(BOOK["chapters"]):
    body = []
    if c["num"]:
        body.append(f'<p class="chap-num">{esc(c["num"])}</p>')
    body.append('<hr class="chap-rule"/>')
    body.append(f'<h1 class="chap-title">{esc(c["title"])}</h1>')
    first = True
    for b in c["blocks"]:
        if b["kind"] == "subhead":
            body.append(f'<h2 class="sub">{esc("".join(t for t,_,_ in b["runs"]))}</h2>')
            first = True; continue
        cls = "lead" if b["kind"] == "lead" else ("first" if first else "")
        body.append(f'<p class="{cls}">{runs_html(b["runs"])}</p>')
        first = False
    idx = int(c["num"]) - 1 if c["num"] else None
    q = PROMPTS[idx] if idx is not None and idx < len(PROMPTS) else \
        "What is one thing you will do differently tomorrow?"
    body.append(f'<div class="prompt"><span class="lbl">Think about it</span>'
                f'<span class="q">{esc(q)}</span></div>')
    fn = chap_file(i, c)
    label = (f'{c["num"]}. {c["title"]}' if c["num"] else c["title"])
    files[fn] = page(label, "\n".join(body))
    spine_items.append(fn); toc.append((label, fn))

for key, title, blocks in (("onemore", "One More Thing", BOOK["one_more"]),
                           ("author", "About the Author", BOOK["author_bio"])):
    b = "".join(f'<p class="{"first" if i==0 else "noindent"}">{runs_html(x["runs"])}</p>'
                for i, x in enumerate(blocks))
    fn = f"text/{key}.xhtml"
    files[fn] = page(title, f'<h1 class="fm">{esc(title)}</h1>' + b)
    spine_items.append(fn); toc.append((title, fn))

nav_items = "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for t, h in toc)
files["nav.xhtml"] = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head><meta charset="utf-8"/><title>Contents</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><nav epub:type="toc" id="toc"><h1 class="fm">Contents</h1><ol>{nav_items}</ol></nav>
<nav epub:type="landmarks" hidden=""><ol>
<li><a epub:type="cover" href="text/cover.xhtml">Cover</a></li>
<li><a epub:type="bodymatter" href="{toc[1][1]}">Begin Reading</a></li>
</ol></nav></body></html>'''

ncx_pts = "".join(
    f'<navPoint id="n{i}" playOrder="{i+1}"><navLabel><text>{esc(t)}</text></navLabel>'
    f'<content src="{h}"/></navPoint>' for i, (t, h) in enumerate(toc))
files["toc.ncx"] = f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="{UID}"/></head>
<docTitle><text>{esc(M["title"])}</text></docTitle>
<navMap>{ncx_pts}</navMap></ncx>'''

manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '<item id="css" href="style.css" media-type="text/css"/>',
            '<item id="cover-img" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>']
for i, f in enumerate(x for x in files if x.endswith(".xhtml") and x != "nav.xhtml"):
    manifest.append(f'<item id="x{i}" href="{f}" media-type="application/xhtml+xml"/>')
ids = {f: f'x{i}' for i, f in enumerate(x for x in files if x.endswith(".xhtml") and x != "nav.xhtml")}
spine = "".join(f'<itemref idref="{"nav" if s=="nav.xhtml" else ids[s]}"/>' for s in spine_items)

files["content.opf"] = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bid">{UID}</dc:identifier>
<dc:title>{esc(M["title"].title())}: {esc(M["subtitle"])}</dc:title>
<dc:creator>{esc(M["author"])}</dc:creator>
<dc:language>en-US</dc:language>
<dc:date>{M["year"]}-01-01</dc:date>
<dc:publisher>{esc(M["author"])}</dc:publisher>
<dc:subject>new home sales</dc:subject><dc:subject>sales</dc:subject>
<dc:subject>listening</dc:subject><dc:subject>trust</dc:subject>
<dc:description>Stop selling. Start listening.</dc:description>
<meta property="dcterms:modified">{M["year"]}-01-01T00:00:00Z</meta>
<meta name="cover" content="cover-img"/>
</metadata>
<manifest>{"".join(manifest)}</manifest>
<spine toc="ncx">{spine}</spine>
</package>'''

files["style.css"] = CSS

os.makedirs("dist", exist_ok=True)
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT, "w") as z:
    z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip",
               compress_type=zipfile.ZIP_STORED)
    z.writestr("META-INF/container.xml",
               '<?xml version="1.0" encoding="utf-8"?>\n'
               '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
               '<rootfiles><rootfile full-path="OEBPS/content.opf" '
               'media-type="application/oebps-package+xml"/></rootfiles></container>',
               compress_type=zipfile.ZIP_DEFLATED)
    for name, data in files.items():
        z.writestr("OEBPS/" + name, data, compress_type=zipfile.ZIP_DEFLATED)
    z.write("dist/4_COVER_PARTS/OneCallSalesperson_EbookCover_1600x2560.jpg", "OEBPS/images/cover.jpg",
            compress_type=zipfile.ZIP_DEFLATED)
print("wrote", OUT, f"({len(files)+2} files)")
