"""Fetch Google Fonts variable files and instance static weights.

Static instances embed far more predictably in print PDFs than variable fonts,
and KDP preflight is happier with them. Run once per project.
"""
import os, sys, urllib.request, urllib.parse

FAMILIES = {
    # family: (ofl-dir, [(vf-filename, italic?)])
    "Lora":         ("lora", [("Lora[wght].ttf", False), ("Lora-Italic[wght].ttf", True)]),
    "Oswald":       ("oswald", [("Oswald[wght].ttf", False)]),
    "SourceSans3":  ("sourcesans3", [("SourceSans3[wght].ttf", False),
                                     ("SourceSans3-Italic[wght].ttf", True)]),
    "EBGaramond":   ("ebgaramond", [("EBGaramond[wght].ttf", False),
                                    ("EBGaramond-Italic[wght].ttf", True)]),
    "Merriweather": ("merriweather", [("Merriweather[opsz,wdth,wght].ttf", False)]),
}
WEIGHTS = {"Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700}
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl"

def fetch(family, outdir="build/fonts"):
    if family not in FAMILIES:
        raise SystemExit(f"unknown family {family!r}; known: {', '.join(sorted(FAMILIES))}")
    d, files = FAMILIES[family]
    os.makedirs(outdir, exist_ok=True)
    got = []
    for fn, italic in files:
        url = f"{BASE}/{d}/{urllib.parse.quote(fn)}"
        dest = os.path.join(outdir, ("%s-Italic-VF.ttf" if italic else "%s-VF.ttf") % family)
        try:
            urllib.request.urlretrieve(url, dest)
            got.append((dest, italic))
            print("  fetched", os.path.basename(dest))
        except Exception as e:
            print(f"  !! {fn}: {e}")
    return got

def instance(family, outdir="build/fonts", static="build/fonts/static"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    os.makedirs(static, exist_ok=True)
    for src, italic in fetch(family, outdir):
        for name, w in WEIGHTS.items():
            f = TTFont(src)
            try:
                instancer.instantiateVariableFont(f, {"wght": w}, inplace=True,
                                                  updateFontNames=True)
            except Exception:
                continue
            out = os.path.join(static, f"{family}-{name}{'Italic' if italic else ''}.ttf")
            f.save(out)
            print("   ", os.path.basename(out))

if __name__ == "__main__":
    fams = sys.argv[1:] or ["Lora", "Oswald", "SourceSans3"]
    for fam in fams:
        print(fam + ":")
        instance(fam)
