"""Turn the raw paragraph dump into a canonical book model shared by the DOCX and PDF renderers."""
import json, re

RAW = {p["i"]: p for p in json.load(open("build/paras.json"))}
ORDER = sorted(RAW)

META = dict(
    title="THE ONE CALL SALESPERSON",
    title_line1="THE ONE CALL",
    title_line2="SALESPERSON",
    subtitle="Stop Selling. Start Listening.",
    author="Julie Neill",
    year="2026",
)

FRONT_SKIP = {0, 1, 2, 4, 6, 7, 9, 11}          # rebuilt by hand below
GRATITUDE = [12, 13, 14, 15]
BACK_ONE_MORE = [368, 369, 370, 371]
BACK_AUTHOR = [373, 374, 375, 376, 377, 378, 379]
SPECIAL = set(FRONT_SKIP) | set(GRATITUDE) | set(BACK_ONE_MORE) | set(BACK_AUTHOR)


def runs(i):
    return [(t, b, it) for t, b, it in RAW[i]["runs"] if t]


def classify(p):
    if p["sz"] == 30 and p["center"] and p["bold"]:
        return "chapter"
    if p["sz"] == 26 and p["bold"] and not p["center"]:
        return "subhead"
    if p["bold"]:
        return "lead"          # standalone bolded punch line
    return "body"


chapters = []          # {num, title, blocks:[(kind, runs)]}
cur = None
for i in ORDER:
    if i in SPECIAL:
        continue
    p = RAW[i]
    if i == 16:                                  # "Introduction" mis-styled as body
        cur = dict(num=None, title="Introduction", blocks=[])
        chapters.append(cur)
        continue
    k = classify(p)
    if k == "chapter":
        m = re.match(r"\s*(\d+)\.\s*(.+)", p["text"])
        num, title = (m.group(1), m.group(2)) if m else (None, p["text"])
        cur = dict(num=num, title=title.strip(), blocks=[])
        chapters.append(cur)
        continue
    if cur is None:
        continue
    cur["blocks"].append(dict(kind=k, runs=runs(i)))

# Title-case the shouty chapter titles against the Contents page (authoritative casing).
toc_src = [l.strip() for l in RAW[11]["text"].split("\n") if l.strip()]
toc_titles = {}
for line in toc_src:
    m = re.match(r"(\d+)\.\s*(.+)", line)
    if m:
        toc_titles[m.group(1)] = m.group(2).strip()
for c in chapters:
    if c["num"] in toc_titles:
        c["title"] = toc_titles[c["num"]]

COPYRIGHT = [l for l in RAW[4]["text"].split("\n")]
DEDICATION = RAW[7]["text"]
GRAT_BLOCKS = [dict(kind="body", runs=runs(i)) for i in GRATITUDE[1:]]
ONE_MORE = [dict(kind="body", runs=runs(i)) for i in BACK_ONE_MORE[1:]]
AUTHOR = [dict(kind="body", runs=runs(i)) for i in BACK_AUTHOR[1:]]

BOOK = dict(meta=META, chapters=chapters, copyright=COPYRIGHT, dedication=DEDICATION,
            gratitude=GRAT_BLOCKS, one_more=ONE_MORE, author_bio=AUTHOR)

if __name__ == "__main__":
    json.dump(BOOK, open("build/book.json", "w"), indent=1)
    print(f"chapters: {len(chapters)}")
    for c in chapters:
        words = sum(len(t.split()) for b in c["blocks"] for t, _, _ in b["runs"])
        print(f"  {c['num'] or '-':>3}. {c['title'][:52]:<54} {len(c['blocks']):>3} blocks {words:>5}w")
    print("back matter blocks:", len(GRAT_BLOCKS), len(ONE_MORE), len(AUTHOR))
