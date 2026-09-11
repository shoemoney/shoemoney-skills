"""Publisher-grade text cleanup: curly quotes, em dashes, ellipses, primes."""
import re

def smartify(text, prev=" "):
    """Convert straight quotes/dashes in `text`. `prev` is the last emitted char
    from the preceding run so quote direction survives run boundaries."""
    out = []
    for ch in text:
        if ch == '"':
            out.append('“' if prev in ' \t\n([{—–“‘/' or prev == "" else '”')
        elif ch == "'":
            # apostrophe when hugged by word chars or after a letter; else opening single
            out.append('’' if (prev.isalnum() or prev in ".,!?”") else '‘')
        else:
            out.append(ch)
        prev = out[-1]
    s = "".join(out)
    s = re.sub(r"(?<=\s)-(?=\s)", "—", s)          # spaced hyphen -> em dash
    s = s.replace(" — ", "—")                  # close it up, US style
    s = s.replace("...", "…")
    s = re.sub(r"(\d)\s*-\s*(\d)", "–".join(["\\1", "\\2"]), s)   # number range -> en dash
    return s, (s[-1] if s else prev)

def smart_runs(runs):
    prev, out = " ", []
    for t, b, i in runs:
        s, prev = smartify(t, prev)
        out.append((s, b, i))
    return out

def smart(text):
    return smartify(text)[0]
