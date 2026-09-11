"""Emit CONTENT_TO_PASTE/ - the copy that goes into KDP's web form.

KDP's form has hard limits and quirks (the description box takes a subset of
HTML; there are exactly 7 keyword slots; the same fields are re-entered for each
format). Splitting the copy into one file per form field means the author pastes
rather than composes, and nothing gets silently truncated.

Content comes from book.json -> "listing". Anything missing is emitted as a
clearly marked TODO rather than invented.
"""
import argparse, json, os, re, sys, textwrap

LIMITS = dict(title=200, subtitle=200, description=4000, bio=2400, keyword=50)

def W(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(textwrap.dedent(text).lstrip())

def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="book.json")
    ap.add_argument("--dist", default="dist")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    L = cfg.get("listing", {})
    out = f"{a.dist}/CONTENT_TO_PASTE"
    TODO = "<<< TODO - not supplied in book.json >>>"

    title = cfg.get("title_display") or cfg.get("title", TODO)
    subtitle = cfg.get("subtitle", "")
    author = cfg.get("author", TODO)
    desc = L.get("description_html") or TODO
    bio = L.get("author_bio") or TODO
    kws = L.get("keywords") or []
    cats = L.get("categories") or []

    W(f"{out}/00_START-HERE.txt", f"""
    ==================================================================
    CONTENT TO PASTE INTO KDP
    ==================================================================

    Every file here maps to one field on KDP's form. Open the file,
    copy the text between the ----- lines, paste it in.

      01_title-and-subtitle.txt .... Title + Subtitle fields
      02_description.html .......... "Description" box
      03_keywords.txt .............. the 7 keyword boxes
      04_categories.txt ............ "Categories" chooser
      05_author-bio.txt ............ Author Central / About the Author
      06_pricing-and-rights.txt .... Rights, territories, price, royalty

    You will enter this SAME content three times - once for the
    paperback, once for the hardcover, once for the Kindle edition.
    Keep it identical so Amazon links the three editions on one
    product page. If the title or subtitle differs even slightly
    between formats, Amazon may list them as separate books.

    Files to upload live in  UPLOAD_THESE/  - each format's folder has
    a READ-ME-FIRST.txt with the exact settings to choose.
    """)

    W(f"{out}/01_title-and-subtitle.txt", f"""
    TITLE  (max {LIMITS['title']} chars - currently {len(strip_html(title))})
    ------------------------------------------------------------------
    {title}
    ------------------------------------------------------------------

    SUBTITLE  (max {LIMITS['subtitle']} chars - currently {len(strip_html(subtitle))})
    ------------------------------------------------------------------
    {subtitle}
    ------------------------------------------------------------------

    AUTHOR
    ------------------------------------------------------------------
    {author}
    ------------------------------------------------------------------

    NOTE: type these EXACTLY the same for all three formats.
    Do not put the subtitle inside the title field.
    """)

    dlen = len(strip_html(desc))
    W(f"{out}/02_description.html", f"""
    <!-- KDP DESCRIPTION - max {LIMITS['description']} chars, currently ~{dlen}
         KDP accepts a limited subset of HTML in this box:
           <b> <i> <u> <br> <p> <h4>..<h6> <ol> <ul> <li> <em> <strong>
         It does NOT accept: <div> <span> <img> <a> style= class=
         Paste everything below this comment block. -->

    {desc}
    """)

    kw_lines = "\n".join(
        f"    {i+1}. {kws[i] if i < len(kws) else '<<< TODO >>>'}" for i in range(7))
    over = [k for k in kws if len(k) > LIMITS["keyword"]]
    W(f"{out}/03_keywords.txt", f"""
    KEYWORDS - KDP gives you exactly 7 boxes, one phrase each
    (max {LIMITS['keyword']} chars per box)
    ------------------------------------------------------------------
{kw_lines}
    ------------------------------------------------------------------
    {'!! TOO LONG: ' + ', '.join(over) if over else ''}

    Guidance:
      - Phrases people actually type into Amazon search, not single words.
      - Do NOT repeat words already in your title or subtitle - Amazon
        already indexes those, so repeating them wastes a slot.
      - No competitor names, no "bestseller", no subjective claims.
    """)

    cat_lines = "\n".join(f"    {i+1}. {c}" for i, c in enumerate(cats)) or f"    {TODO}"
    W(f"{out}/04_categories.txt", f"""
    CATEGORIES
    ------------------------------------------------------------------
{cat_lines}
    ------------------------------------------------------------------

    KDP asks you to pick categories from its own browse tree. Search
    the chooser for the nearest match to each line above.
    You may also email KDP support to be added to further categories
    after publishing.
    """)

    W(f"{out}/05_author-bio.txt", f"""
    AUTHOR BIO  (max {LIMITS['bio']} chars - currently ~{len(strip_html(bio))})
    Used on Amazon Author Central and the "About the Author" section.
    ------------------------------------------------------------------
    {bio}
    ------------------------------------------------------------------
    """)

    p = L.get("pricing", {})
    W(f"{out}/06_pricing-and-rights.txt", f"""
    RIGHTS, TERRITORIES AND PRICING
    ------------------------------------------------------------------
    Publishing rights .... {p.get('rights', 'I own the copyright and hold necessary publishing rights')}
    Territories .......... {p.get('territories', 'All territories (worldwide rights)')}
    Primary marketplace .. {p.get('marketplace', 'Amazon.com')}

    Suggested list prices:
      Kindle eBook ....... {p.get('ebook', '<<< TODO >>>')}
      Paperback .......... {p.get('paperback', '<<< TODO >>>')}
      Hardcover .......... {p.get('hardcover', '<<< TODO >>>')}

    Royalty:
      Kindle 70% requires a list price between $2.99 and $9.99.
      Below $2.99 or above $9.99 drops you to 35%.
      Print royalties are 60% of list price minus the printing cost;
      KDP shows the printing cost once you set the trim and page count,
      and it will refuse a price that does not cover it.

    ISBN:
      KDP provides a free ISBN per format. A free KDP ISBN cannot be
      used with another printer or distributor. Buy your own only if
      you plan to print elsewhere too.
      Paperback and hardcover each need their OWN ISBN.
      Kindle eBooks do not need one (Amazon assigns an ASIN).
    ------------------------------------------------------------------
    """)
    print(f"CONTENT_TO_PASTE/ -> {out}")
    for f in sorted(os.listdir(out)):
        flag = "  <-- has TODOs" if "TODO" in open(f"{out}/{f}").read() else ""
        print(f"   {f}{flag}")

if __name__ == "__main__":
    main()
