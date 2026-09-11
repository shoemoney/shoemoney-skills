"""Build a KDP-ready 6x9 ODT (OpenDocument Text) matching the DOCX:
mirrored margins, odd-page chapter starts, running heads, folios, live TOC."""
import json, os, zipfile, html
from typo import smart, smart_runs

BOOK = json.load(open("build/book.json"))
M = BOOK["meta"]
PROMPTS = json.load(open("build/prompts.json"))
OUT = "dist/3_EDITABLE/OneCallSalesperson_Interior_6x9.odt"
BODY_FONT, DISP_FONT = "Georgia", "Arial Narrow"

NS = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
      'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
      'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
      'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
      'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
      'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
      'xmlns:dc="http://purl.org/dc/elements/1.1/" '
      'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
      'xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" '
      'xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0"')

def esc(s):
    return html.escape(smart(s), quote=False)

def raw_esc(s):
    return html.escape(s, quote=False)

def runs_xml(runs):
    out = []
    for t, b, i in smart_runs(runs):
        chunks = raw_esc(t).split("\n")
        body = "<text:line-break/>".join(chunks)
        span = {(False, False): None, (True, False): "T_b",
                (False, True): "T_i", (True, True): "T_bi"}[(b, i)]
        out.append(body if span is None else f'<text:span text:style-name="{span}">{body}</text:span>')
    return "".join(out)

# ---------------------------------------------------------------- styles ---
def para_style(name, parent, *, font=None, size=None, bold=False, italic=False,
               align=None, before=0, after=0, line="142%", indent=None,
               keep=False, master=None, brk=None, border=False, color=None,
               caps=False, track=None):
    p = [f'style:name="{name}"', 'style:family="paragraph"',
         f'style:parent-style-name="{parent}"']
    if master:
        p.append(f'style:master-page-name="{master}"')
    pp = [f'fo:margin-top="{before}pt"', f'fo:margin-bottom="{after}pt"',
          f'fo:line-height="{line}"', 'fo:orphans="2"', 'fo:widows="2"']
    if align: pp.append(f'fo:text-align="{align}"')
    if indent is not None: pp.append(f'fo:text-indent="{indent}in"')
    if keep: pp.append('fo:keep-with-next="always"')
    if brk: pp.append(f'fo:break-before="{brk}"')
    if border: pp.append('fo:border-bottom="0.5pt solid #aaaaaa" fo:padding-bottom="0.02in"')
    tp = []
    if font: tp.append(f'style:font-name="{font}"')
    if size: tp.append(f'fo:font-size="{size}pt"')
    if bold: tp.append('fo:font-weight="bold"')
    if italic: tp.append('fo:font-style="italic"')
    if caps: tp.append('fo:text-transform="uppercase"')
    if track: tp.append(f'fo:letter-spacing="{track}in"')
    tp.append(f'fo:color="{color or "#000000"}"')
    return (f'<style:style {" ".join(p)}>'
            f'<style:paragraph-properties {" ".join(pp)}/>'
            f'<style:text-properties {" ".join(tp)}/></style:style>')

def page_layout(name, usage):
    return f'''<style:page-layout style:name="{name}" style:page-usage="{usage}">
<style:page-layout-properties fo:page-width="6in" fo:page-height="9in"
 style:print-orientation="portrait" fo:margin-top="0.78in" fo:margin-bottom="0.72in"
 fo:margin-left="0.8125in" fo:margin-right="0.6875in" style:num-format="1"
 style:writing-mode="lr-tb"/>
<style:header-style><style:header-footer-properties fo:min-height="0.2in"
 fo:margin-bottom="0.22in"/></style:header-style>
<style:footer-style><style:header-footer-properties fo:min-height="0.2in"
 fo:margin-top="0.22in"/></style:footer-style>
</style:page-layout>'''

HDR_P = ('<style:style style:name="HdrRun" style:family="text">'
         f'<style:text-properties style:font-name="{DISP_FONT}" fo:font-size="8.5pt" '
         'fo:font-weight="bold" fo:text-transform="uppercase" fo:letter-spacing="0.018in" '
         'fo:color="#000000"/></style:style>')

def master(name, layout, *, chapter_head=False, header=True, nxt=None):
    """chapter_head=True -> recto shows the live chapter title, verso the book title."""
    n = f' style:next-style-name="{nxt}"' if nxt else ""
    if header:
        recto = ('<text:chapter text:display="name" text:outline-level="1"/>'
                 if chapter_head else raw_esc(M["title"]))
        hdr = (f'<style:header><text:p text:style-name="HeaderP">'
               f'<text:span text:style-name="HdrRun">{recto}</text:span></text:p></style:header>'
               f'<style:header-left><text:p text:style-name="HeaderP">'
               f'<text:span text:style-name="HdrRun">{raw_esc(M["title"])}</text:span>'
               f'</text:p></style:header-left>')
    else:
        hdr = '<style:header style:display="false"/>'
    return f'''<style:master-page style:name="{name}" style:page-layout-name="{layout}"{n}>
{hdr}
<style:footer><text:p text:style-name="FooterP"><text:page-number
 text:select-page="current">1</text:page-number></text:p></style:footer>
<style:footer-left><text:p text:style-name="FooterP"><text:page-number
 text:select-page="current">1</text:page-number></text:p></style:footer-left>
</style:master-page>'''

STYLES = "".join([
    para_style("Standard", "", font=BODY_FONT, size=11.5, align="justify"),
    para_style("OCS_20_Body_20_First", "Standard", align="justify", indent=0),
    para_style("OCS_20_Body", "Standard", align="justify", indent=0.22),
    para_style("OCS_20_Lead", "Standard", bold=True, indent=0, before=8, after=8),
    para_style("OCS_20_Subhead", "Standard", font=DISP_FONT, size=11, bold=True, caps=True,
               track=0.012, align="start", before=16, after=5, keep=True, indent=0),
    para_style("Heading_20_1", "Standard", font=DISP_FONT, size=17, bold=True, caps=True,
               track=0.014, align="center", before=6, after=30, line="125%", keep=True, indent=0),
    para_style("OCS_20_Chapter_20_Number", "Standard", font=DISP_FONT, size=44, bold=True,
               align="center", before=54, after=2, line="100%", indent=0, keep=True),
    para_style("OCS_20_Front_20_Matter_20_Head", "Standard", font=DISP_FONT, size=15,
               bold=True, caps=True, track=0.02, align="center", before=44, after=24,
               keep=True, indent=0),
    para_style("OCS_20_Centered", "Standard", align="center", after=10, indent=0),
    para_style("OCS_20_Copyright", "Standard", size=8.5, line="128%", after=7,
               align="start", indent=0),
    para_style("OCS_20_Book_20_Title", "Standard", font=DISP_FONT, size=30, bold=True,
               caps=True, align="center", line="105%", after=0, indent=0),
    para_style("OCS_20_Contents", "Standard", size=10.5, line="128%", after=4,
               align="start", indent=0),
    para_style("OCS_20_Notes_20_Head", "Standard", font=DISP_FONT, size=14, bold=True,
               caps=True, track=0.02, align="center", before=18, after=6, indent=0),
    para_style("OCS_20_Notes_20_Label", "Standard", font=DISP_FONT, size=8.5, bold=True,
               caps=True, track=0.02, align="center", before=30, after=4, indent=0),
    para_style("OCS_20_Notes_20_Prompt", "Standard", size=9.5, italic=True,
               align="center", after=16, indent=0),
    para_style("OCS_20_Rule", "Standard", size=11.5, after=9, border=True, indent=0),
    para_style("OCS_20_Break", "Standard", brk="page", indent=0),
    para_style("HeaderP", "Standard", align="center", indent=0, line="100%"),
    para_style("FooterP", "Standard", font=DISP_FONT, size=9, align="center",
               indent=0, line="100%"),
    '<style:style style:name="T_b" style:family="text">'
    '<style:text-properties fo:font-weight="bold"/></style:style>',
    '<style:style style:name="T_i" style:family="text">'
    '<style:text-properties fo:font-style="italic"/></style:style>',
    '<style:style style:name="T_bi" style:family="text">'
    '<style:text-properties fo:font-weight="bold" fo:font-style="italic"/></style:style>',
    HDR_P,
])

STYLES_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles {NS} office:version="1.3">
<office:font-face-decls>
<style:font-face style:name="{BODY_FONT}" svg:font-family="{BODY_FONT}" style:font-family-generic="roman"/>
<style:font-face style:name="{DISP_FONT}" svg:font-family="{DISP_FONT}" style:font-family-generic="swiss"/>
</office:font-face-decls>
<office:styles>{STYLES}</office:styles>
<office:automatic-styles>
{page_layout("PL_Front", "mirrored")}
{page_layout("PL_ChapterFirst", "right")}
{page_layout("PL_ChapterBody", "mirrored")}
</office:automatic-styles>
<office:master-styles>
<style:master-page style:name="Standard" style:page-layout-name="PL_Front"/>
{master("Chapter", "PL_ChapterFirst", header=False, nxt="ChapterBody")}
{master("ChapterBody", "PL_ChapterBody", chapter_head=True)}
</office:master-styles>
</office:document-styles>'''

# --------------------------------------------------------------- content ---
def P(style, text=None, runs=None, master_break=None):
    attrs = f'text:style-name="{style}"'
    inner = runs_xml(runs) if runs is not None else \
            ("<text:line-break/>".join(esc(c) for c in (text or "").split("\n")))
    return f'<text:p {attrs}>{inner}</text:p>'

body = []
A = body.append

A(P("OCS_20_Book_20_Title", M["title_line1"] + "\n" + M["title_line2"]))
A(P("OCS_20_Break"))
A(P("OCS_20_Book_20_Title", M["title_line1"] + "\n" + M["title_line2"]))
A(f'<text:p text:style-name="OCS_20_Centered"><text:span text:style-name="T_i">'
  f'{esc(M["subtitle"])}</text:span></text:p>')
A(P("OCS_20_Centered", ""))
A(P("OCS_20_Centered", M["author"]))
A(P("OCS_20_Break"))
for line in [l for l in BOOK["copyright"] if l.strip()]:
    A(P("OCS_20_Copyright", line))
A(P("OCS_20_Break"))
A(P("OCS_20_Front_20_Matter_20_Head", "Dedication"))
A(f'<text:p text:style-name="OCS_20_Centered"><text:span text:style-name="T_i">'
  f'{esc(BOOK["dedication"])}</text:span></text:p>')
A(P("OCS_20_Break"))

# live table of contents (LibreOffice refreshes on F9 / Tools > Update > Indexes)
toc_entries = "".join(
    f'<text:p text:style-name="OCS_20_Contents">{esc((c["num"] + ". " if c["num"] else "") + c["title"])}</text:p>'
    for c in BOOK["chapters"])
A(f'''<text:table-of-content text:style-name="Standard" text:protected="true" text:name="TOC">
<text:table-of-content-source text:outline-level="1" text:use-outline-level="true">
<text:index-title-template text:style-name="OCS_20_Front_20_Matter_20_Head">Contents</text:index-title-template>
<text:table-of-content-entry-template text:outline-level="1" text:style-name="OCS_20_Contents">
<text:index-entry-text/><text:index-entry-tab-stop style:type="right" style:leader-char="."/>
<text:index-entry-page-number/></text:table-of-content-entry-template>
</text:table-of-content-source>
<text:index-body>
<text:index-title text:name="TOC_Head"><text:p text:style-name="OCS_20_Front_20_Matter_20_Head">Contents</text:p></text:index-title>
{toc_entries}
</text:index-body></text:table-of-content>''')

A(P("OCS_20_Break"))
A(P("OCS_20_Front_20_Matter_20_Head", "A Note of Gratitude"))
for i, b in enumerate(BOOK["gratitude"]):
    A(P("OCS_20_Body_20_First" if i == 0 else "OCS_20_Body", runs=b["runs"]))

def notes_pages(label, prompt):
    A(P("OCS_20_Break"))
    A(P("OCS_20_Notes_20_Label", label))
    A(P("OCS_20_Notes_20_Head", "Your Notes"))
    A(P("OCS_20_Notes_20_Prompt", prompt))
    for _ in range(18):
        A('<text:p text:style-name="OCS_20_Rule"/>')

first_chapter = True
for c in BOOK["chapters"]:
    # switching to the Chapter master page forces the next available RIGHT page
    A(f'<text:p text:style-name="OCS_20_Chapter_20_Number_Break">'
      f'{esc(c["num"]) if c["num"] else ""}</text:p>')
    A(f'<text:h text:style-name="Heading_20_1" text:outline-level="1">{esc(c["title"])}</text:h>')
    first = True
    for b in c["blocks"]:
        if b["kind"] == "subhead":
            A(P("OCS_20_Subhead", "".join(t for t, _, _ in b["runs"])))
            first = True
            continue
        sn = "OCS_20_Lead" if b["kind"] == "lead" else \
             ("OCS_20_Body_20_First" if first else "OCS_20_Body")
        A(P(sn, runs=b["runs"]))
        first = False
    idx = int(c["num"]) - 1 if c["num"] else None
    prompt = PROMPTS[idx] if idx is not None and idx < len(PROMPTS) else \
             "What is one thing you will do differently tomorrow?"
    notes_pages(f'Chapter {c["num"]} · {c["title"]}' if c["num"] else "Introduction", prompt)

for title, blocks in (("One More Thing", BOOK["one_more"]),
                      ("About the Author", BOOK["author_bio"])):
    A(f'<text:p text:style-name="OCS_20_Front_20_Matter_20_Head_Break">{esc(title)}</text:p>')
    for i, b in enumerate(blocks):
        A(P("OCS_20_Body_20_First" if i == 0 else "OCS_20_Body", runs=b["runs"]))

# automatic styles that carry the master-page switch (= "start on next right page")
AUTO = "".join([
    '<style:style style:name="OCS_20_Chapter_20_Number_Break" style:family="paragraph" '
    'style:parent-style-name="OCS_20_Chapter_20_Number" style:master-page-name="Chapter">'
    '<style:paragraph-properties/></style:style>',
    '<style:style style:name="OCS_20_Front_20_Matter_20_Head_Break" style:family="paragraph" '
    'style:parent-style-name="OCS_20_Front_20_Matter_20_Head" style:master-page-name="Chapter">'
    '<style:paragraph-properties/></style:style>',
])

CONTENT_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content {NS} office:version="1.3">
<office:font-face-decls>
<style:font-face style:name="{BODY_FONT}" svg:font-family="{BODY_FONT}" style:font-family-generic="roman"/>
<style:font-face style:name="{DISP_FONT}" svg:font-family="{DISP_FONT}" style:font-family-generic="swiss"/>
</office:font-face-decls>
<office:automatic-styles>{AUTO}</office:automatic-styles>
<office:body><office:text>
<text:sequence-decls/>
{"".join(body)}
</office:text></office:body></office:document-content>'''

META_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta {NS} office:version="1.3"><office:meta>
<dc:title>The One Call Salesperson: {raw_esc(M["subtitle"])}</dc:title>
<dc:creator>{raw_esc(M["author"])}</dc:creator>
<dc:subject>{raw_esc(M["subtitle"])}</dc:subject>
<meta:keyword>new home sales</meta:keyword><meta:keyword>sales</meta:keyword>
<meta:keyword>listening</meta:keyword><meta:keyword>trust</meta:keyword>
</office:meta></office:document-meta>'''

MANIFEST = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">
<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''

os.makedirs(os.path.dirname(OUT), exist_ok=True)
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT, "w") as z:
    z.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.oasis.opendocument.text",
               compress_type=zipfile.ZIP_STORED)
    for n, d in (("META-INF/manifest.xml", MANIFEST), ("content.xml", CONTENT_XML),
                 ("styles.xml", STYLES_XML), ("meta.xml", META_XML)):
        z.writestr(n, d, compress_type=zipfile.ZIP_DEFLATED)
print("wrote", OUT)
