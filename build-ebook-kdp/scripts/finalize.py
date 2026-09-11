"""Assemble the shipping interior PDF: blanks -> epigraph pages, running heads,
folios, mirrored margins, metadata."""
import json, io, re, os
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, Color
from typo import smart

FD = os.path.abspath("build/fonts/static")
for name, fn in [("Oswald", "Oswald-Regular.ttf"), ("Oswald-Md", "Oswald-Medium.ttf"),
                 ("Oswald-Sb", "Oswald-SemiBold.ttf"), ("Oswald-Bd", "Oswald-Bold.ttf"),
                 ("Lora", "Lora-Regular.ttf"), ("Lora-It", "Lora-Italic.ttf")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FD, fn)))

W, H = 432.0, 648.0                 # 6 x 9 in points
SHIFT = 4.5                         # 1/16in mirrored gutter shift
BOOK = json.load(open("build/book.json"))
PAGENOS = json.load(open("build/pagenos.json"))
INSERTS = {int(k): v for k, v in json.load(open("build/inserts.json")).items()}

# ---------- epigraphs -------------------------------------------------------
def pick_quote(ch):
    cands = [" ".join(t for t, _, _ in b["runs"]).strip()
             for b in ch["blocks"] if b["kind"] == "lead"]
    cands = [smart(c) for c in cands if 24 <= len(c) <= 96]
    return max(cands, key=len) if cands else None

QUOTES, LABELS = {}, {}
for c in BOOK["chapters"]:
    key = "ch-" + (c["num"] or "intro")
    q = pick_quote(c)
    if q:
        QUOTES[key] = q
        LABELS[key] = f'Chapter {c["num"]}' if c["num"] else "Introduction"
QUOTES.setdefault("ch-intro", smart("They're lessons about people."))
LABELS.setdefault("ch-intro", "Introduction")
QUOTES["fm-onemore"] = smart("Find the people who make you better.")
LABELS["fm-onemore"] = "One More Thing"
QUOTES["fm-end"] = smart("But they will remember how you made them feel.")
LABELS["fm-end"] = "The One Call Salesperson"

# ---------- page -> chapter map --------------------------------------------
order = sorted(PAGENOS.items(), key=lambda kv: kv[1])
TITLE_OF = {}
for c in BOOK["chapters"]:
    TITLE_OF["ch-" + (c["num"] or "intro")] = c["title"]
TITLE_OF.update({"fm-grat": "A Note of Gratitude", "fm-onemore": "One More Thing",
                 "fm-author": "About the Author", "fm-end": ""})

def wrap(text, font, size, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if pdfmetrics.stringWidth(t, font, size) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines

def tracked(c, text, font, size, cx, y, track):
    c.setFont(font, size)
    tw = pdfmetrics.stringWidth(text, font, size) + track * (len(text) - 1)
    x = cx - tw / 2
    for ch in text:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, size) + track

def epigraph(c, key):
    q, lab = QUOTES.get(key), LABELS.get(key, "")
    if not q:
        return
    size, maxw = 15.5, 3.45 * 72
    lines = wrap(q, "Oswald-Md", size, maxw)
    lh = size * 1.5
    top = H / 2 + (len(lines) * lh) / 2 + 14
    c.setStrokeColor(black); c.setLineWidth(1.6)
    c.line(W / 2 - 22, top + 30, W / 2 + 22, top + 30)
    c.setFillColor(black); c.setFont("Oswald-Md", size)
    y = top
    for ln in lines:
        c.drawCentredString(W / 2, y, ln); y -= lh
    if lab:
        c.setFillColor(Color(.25, .25, .25))
        tracked(c, lab.upper(), "Oswald", 7.6, W / 2, y - 12, 1.5)

def chrome(c, folio, head):
    if head:
        c.setFillColor(black)
        tracked(c, head.upper(), "Oswald-Md", 7.6, W / 2, H - 40, 1.35)
    if folio:
        c.setFillColor(black)
        tracked(c, folio, "Oswald-Md", 9.0, W / 2, 34, 0.6)

# ---------- assemble --------------------------------------------------------
raw = PdfReader("build/raw.pdf")            # markerless render
pages, kinds = [], []
for i, p in enumerate(raw.pages):
    if i in INSERTS:
        pages.append(None); kinds.append(("epigraph", INSERTS[i]))
    pages.append(p); kinds.append(("content", None))
if len(pages) % 2:
    pages.append(None); kinds.append(("pad", None))

n = len(pages)
opener_pages = {v: k for k, v in PAGENOS.items()}
NOTES_RE = re.compile(r"YOURNOTES")

cur_key = None
writer = PdfWriter()
for idx in range(n):
    pno = idx + 1
    kind, meta = kinds[idx]
    if kind == "content":
        page = pages[idx]
        text = (page.extract_text() or "").replace(" ", "")
    else:
        page = writer.add_blank_page(width=W, height=H)
        text = ""
    if pno in opener_pages:
        cur_key = opener_pages[pno]

    is_notes = bool(NOTES_RE.search(text))
    is_opener = pno in opener_pages
    is_blank = kind in ("epigraph", "pad") or not text.strip()

    folio = "" if (pno <= 8 or kind in ("epigraph", "pad") or is_blank) else str(pno)
    head = ""
    if folio and not is_opener and not is_notes and cur_key:
        head = (BOOK["meta"]["title"] if pno % 2 == 0
                else TITLE_OF.get(cur_key, "")) or ""

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H), initialFontName="Oswald-Md", initialFontSize=9)
    if kind == "epigraph":
        epigraph(c, meta)
    chrome(c, folio, head)
    c.showPage()
    c.save()
    buf.seek(0)
    ov = PdfReader(buf).pages[0]

    if kind == "content":
        tx = SHIFT if pno % 2 else -SHIFT
        page.add_transformation(Transformation().translate(tx, 0))
        writer.add_page(page)
        writer.pages[-1].merge_page(ov)
    else:
        writer.pages[-1].merge_page(ov)

writer.add_metadata({"/Title": "The One Call Salesperson: Stop Selling. Start Listening.",
                     "/Author": "Julie Neill",
                     "/Subject": "New home sales, listening, and trust",
                     "/Keywords": "new home sales, sales, homebuilding, listening, trust, sales training",
                     "/Creator": "", "/Producer": ""})
os.makedirs("dist", exist_ok=True)
out = "dist/OneCallSalesperson_Interior_6x9_KDP.pdf"
with open(out, "wb") as fh:
    writer.write(fh)
print(f"{out}: {n} pages")
