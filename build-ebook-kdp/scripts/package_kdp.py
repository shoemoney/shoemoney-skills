"""Assemble the hand-over package: exactly-what-to-upload folders plus the
copy that gets pasted into KDP's web form.

The failure this prevents is the author staring at a folder of PDFs wondering
which one is the interior, or uploading the DOCX (different page count) against
a cover cut for the PDF. Filenames here are self-describing on purpose, and each
folder carries a READ-ME-FIRST with the exact dropdown values for KDP's form.

    python3 package_kdp.py --pages 100
"""
import argparse, json, os, shutil, sys, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kdp_calculator import measurements

def W(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(textwrap.dedent(text).lstrip() + "\n")

def block(text, indent=8):
    """Indent an interpolated multi-line value so dedent() still lines up."""
    pad = " " * indent
    lines = textwrap.dedent(text).strip().split("\n")
    return ("\n" + pad).join(lines)

def cp(src, dst):
    if not os.path.exists(src):
        print(f"   !! missing source: {src}")
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"   {os.path.basename(dst)}")
    return True

RULE = "=" * 68

ROOT_README = """
{rule}
START HERE - {title}
by {author}
{rule}

Everything you need to publish this book is in this folder.
There are four folders. Here is what each one is for.


  UPLOAD_THESE/
  -----------------------------------------------------------------
  The actual files you upload to Amazon. Three sub-folders, one per
  format. Each one contains a READ-ME-FIRST.txt telling you exactly
  which file goes in which box and which settings to choose.

      1_PAPERBACK/       the softcover edition
      2_HARDCOVER/       the hardcover edition
      3_KINDLE_EBOOK/    the Kindle edition

  Files are named after the box they go in, for example
  "1_INTERIOR__upload-as-Manuscript.pdf".

  Publish them in any order. They are three separate submissions on
  KDP, but if the title, subtitle and author match exactly, Amazon
  will join them into one product page with format tabs.


  CONTENT_TO_PASTE/
  -----------------------------------------------------------------
  The words that go into Amazon's web form: title, description,
  keywords, categories, author bio, pricing notes. One file per
  field. Open, copy, paste.

  Start with 00_START-HERE.txt in that folder.


  PROOFS/
  -----------------------------------------------------------------
  Nothing here gets uploaded. These are for checking the work.

  The _PROOF_*.png files show each cover with coloured guides drawn
  on: red = where the book gets trimmed, blue = the safe area your
  text must stay inside, green = the box Amazon reserves for the
  barcode. Open them and confirm nothing important sits outside the
  blue line.

  Also here: the front, back and spine as separate images, if you
  ever need to hand them to a designer.


  EDITABLE_SOURCE/
  -----------------------------------------------------------------
  The manuscript as an editable Word (.docx) and OpenDocument (.odt)
  file, fully formatted.

  These are for EDITING, not for uploading.

  *** Important: these files come out to a different page count than
  the print PDF (about 90 pages instead of {pages}). Different programs
  lay text out differently. The cover was cut for a {pages}-page book,
  so uploading one of these instead of the PDF would put the spine
  artwork in the wrong place. Always upload the PDF. ***

  If you edit the text, the page count changes, which changes the
  spine width, which means the covers have to be rebuilt.


{rule}
THE SHORT VERSION
{rule}

  1. Open  CONTENT_TO_PASTE/00_START-HERE.txt
  2. Open  UPLOAD_THESE/1_PAPERBACK/READ-ME-FIRST.txt  and follow it
  3. Repeat for 2_HARDCOVER and 3_KINDLE_EBOOK
  4. Before publishing each one, look at it in KDP's Previewer


{rule}
THINGS THAT WILL BREAK THE BOOK
{rule}

  - Choosing WHITE paper instead of CREAM. The spine width is
    calculated from cream paper. White is thinner and the spine
    artwork will sit off-centre.

  - Uploading the .docx or .odt instead of the print PDF.
    Different page count, wrong spine.

  - Uploading the .mobi or .azw3 to KDP. Amazon stopped accepting
    .mobi in 2022 and never accepted .azw3. Upload the .epub.
    Those two files exist only so you can email the book to your own
    Kindle and read it on a real device before publishing.

  - Editing the manuscript after the covers were built without
    rebuilding the covers.


Book: {title}
Subtitle: {subtitle}
Trim size: {tw} x {th} in     Pages: {pages}     Paper: {paper}
Paperback spine: {pb_spine} in      Hardcover spine: {hc_spine} in
"""


def print_readme(cfg, binding, m, pages, paths):
    tw, th = cfg["trim"]
    paper = cfg["paper"].capitalize()
    is_hc = binding == "hardcover"
    label = "Hardcover" if is_hc else "Paperback"
    spine_note = block(f"""
        Spine width is {m['spine-width']}" - calculated for {pages} pages on
        {paper.upper()} paper. If you change the paper colour or the page
        count, the cover is WRONG and must be rebuilt.""")
    hinge_line = ("\n      [ ] Nothing lands in the 0.394in hinge either side of the spine"
                  if is_hc else "")
    rule = RULE
    return f"""
    {rule}
    {label.upper()} - WHAT TO UPLOAD AND WHAT TO CLICK
    {rule}

    Go to: https://kdp.amazon.com  ->  Create  ->  {label}

    ---------------------------------------------------------------
    STEP 1 - {label} Details
    ---------------------------------------------------------------
    Title, Subtitle, Author, Description, Keywords, Categories:
        Use the files in the  CONTENT_TO_PASTE  folder.

    ---------------------------------------------------------------
    STEP 2 - Content
    ---------------------------------------------------------------
    Print Options:
        Ink and Paper Type ...... Black & white interior with {paper.lower()} paper
        Trim Size ............... {tw} x {th} in
        Bleed Settings .......... No Bleed
        Cover Finish ............ Matte  (or Glossy - your preference)

    Manuscript:
        UPLOAD ->  {paths['interior']}
        This file is {pages} pages. Do not substitute the DOCX or ODT -
        they paginate differently and the cover will not fit.

    Book Cover:
        Choose "Upload a cover you already have (print-ready PDF)"
        UPLOAD ->  {paths['cover']}
        {spine_note}

    ---------------------------------------------------------------
    STEP 3 - Rights & Pricing
    ---------------------------------------------------------------
    See  CONTENT_TO_PASTE/06_pricing-and-rights.txt

    ---------------------------------------------------------------
    BEFORE YOU HIT PUBLISH
    ---------------------------------------------------------------
    Open KDP's Previewer and check:
      [ ] Spine text sits on the spine, not wrapped onto the front or back
      [ ] Nothing important is inside the barcode box on the back cover
      [ ] Chapter 1 starts on a right-hand page
      [ ] Page numbers are centred and start where you expect{hinge_line}

    Cover specs for reference (from KDP's own Cover Calculator):
        Full cover ........ {m['full-cover-width']} x {m['full-cover-height']} in
        Spine ............. {m['spine-width']} in
        Cover panel ....... {m['front-cover-width']} x {m['front-cover-height']} in
        Page count ........ {pages}
        Paper ............. {paper}
    """

KINDLE_README = """
    {rule}
    KINDLE eBOOK - WHAT TO UPLOAD AND WHAT TO CLICK
    {rule}

    Go to: https://kdp.amazon.com  ->  Create  ->  Kindle eBook

    ---------------------------------------------------------------
    STEP 1 - eBook Details
    ---------------------------------------------------------------
    Use the files in the  CONTENT_TO_PASTE  folder.

    ---------------------------------------------------------------
    STEP 2 - Content
    ---------------------------------------------------------------
    Manuscript:
        UPLOAD ->  {manuscript}

        ** Upload the .epub file. **
        Amazon stopped accepting .mobi in August 2022 and has never
        accepted .azw3. Those two files are in EXTRA_for-device-proofing/
        and exist only so you can email them to your own Kindle and read
        the book on a real device before publishing.

    eBook Cover:
        Choose "Upload a cover you already have"
        UPLOAD ->  {cover}
        (1600 x 2560 px JPG - Amazon's recommended size)

    Digital Rights Management (DRM): your choice.

    ---------------------------------------------------------------
    STEP 3 - Rights & Pricing
    ---------------------------------------------------------------
    See  CONTENT_TO_PASTE/06_pricing-and-rights.txt
    KDP Select is optional - it requires 90-day Amazon exclusivity.

    ---------------------------------------------------------------
    BEFORE YOU HIT PUBLISH
    ---------------------------------------------------------------
    Open the Kindle Previewer and check:
      [ ] The table of contents links jump to the right chapters
      [ ] Chapter headings look right on phone AND tablet
      [ ] No blank pages or stray ruled lines
    """

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="book.json")
    ap.add_argument("--pages", type=int, required=True)
    ap.add_argument("--dist", default="dist")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    cfg.setdefault("trim", [6.0, 9.0]); cfg.setdefault("paper", "cream")
    tw, th = cfg["trim"]
    trim_code = f"{tw:g}x{th:g}"
    slug = cfg.get("slug") or "".join(w[0] for w in cfg["title"].split())[:12]
    D = a.dist
    src = cfg.get("built", {})

    print("UPLOAD_THESE/")
    for binding, folder in (("paperback", "1_PAPERBACK"), ("hardcover", "2_HARDCOVER")):
        if binding not in (cfg.get("bindings") or {}):
            continue
        m = measurements(binding, trim_code, a.pages, paper=cfg["paper"])
        base = f"{D}/UPLOAD_THESE/{folder}"
        names = dict(interior=f"1_INTERIOR__upload-as-Manuscript.pdf",
                     cover=f"2_COVER__upload-as-Book-Cover.pdf")
        print(f"  {folder}/")
        cp(src.get(f"{binding}_interior", src.get("interior", "")), f"{base}/{names['interior']}")
        cp(src.get(f"{binding}_cover", ""), f"{base}/{names['cover']}")
        W(f"{base}/READ-ME-FIRST.txt", print_readme(cfg, binding, m, a.pages, names))
        print("   READ-ME-FIRST.txt")

    base = f"{D}/UPLOAD_THESE/3_KINDLE_EBOOK"
    names = dict(manuscript="1_MANUSCRIPT__upload-as-eBook.epub",
                 cover="2_COVER__upload-as-eBook-Cover.jpg")
    print("  3_KINDLE_EBOOK/")
    cp(src.get("epub", ""), f"{base}/{names['manuscript']}")
    cp(src.get("ebook_cover", ""), f"{base}/{names['cover']}")
    for k, n in (("azw3", "SIDELOAD_modern-kindle.azw3"), ("mobi", "SIDELOAD_older-kindle.mobi")):
        if src.get(k):
            cp(src[k], f"{base}/EXTRA_for-device-proofing/{n}")
    W(f"{base}/READ-ME-FIRST.txt",
      KINDLE_README.format(rule=RULE, manuscript=names["manuscript"], cover=names["cover"]))
    print("   READ-ME-FIRST.txt")

    # proofs + editable sources: present, clearly labelled, obviously not uploads
    print("PROOFS/")
    for key, dest in src.get("proofs", {}).items():
        cp(key, f"{D}/PROOFS/{dest}")
    print("EDITABLE_SOURCE/")
    for key, dest in src.get("editable", {}).items():
        cp(key, f"{D}/EDITABLE_SOURCE/{dest}")

    pb = measurements("paperback", trim_code, a.pages, paper=cfg["paper"])["spine-width"] \
         if "paperback" in (cfg.get("bindings") or {}) else "n/a"
    hc = measurements("hardcover", trim_code, a.pages, paper=cfg["paper"])["spine-width"] \
         if "hardcover" in (cfg.get("bindings") or {}) else "n/a"
    W(f"{D}/READ_ME_FIRST.TXT", ROOT_README.format(
        rule=RULE, title=cfg.get("title_display") or cfg["title"],
        subtitle=cfg.get("subtitle", ""), author=cfg["author"], pages=a.pages,
        tw=f"{tw:g}", th=f"{th:g}", paper=cfg["paper"].capitalize(),
        pb_spine=pb, hc_spine=hc))
    print(f"\nREAD_ME_FIRST.TXT -> {D}/READ_ME_FIRST.TXT")
    print("CONTENT_TO_PASTE/ -> run write_listing.py")

if __name__ == "__main__":
    main()
