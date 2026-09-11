"""Build KDP-ready covers for a 6x9 book: front, back, spine, full wrap, ebook.
Geometry is per-binding (paperback vs hardcover case wrap) - see BINDINGS."""
import os, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kdp_calculator import measurements
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None

DPI     = 300
TRIM_W, TRIM_H = 6.0, 9.0
PAGES   = 100

# Per-binding geometry. `wrap()` returns (total_w, total_h, back_x, spine_x, front_x)
# in inches; every panel is placed against those numbers so nothing is hardcoded.
BINDINGS = {}     # filled in below once the verified KDP numbers are in place
BINDING = None    # set by main()
BLEED   = 0.125
SPINE_W = 0.250

NAVY  = (4, 28, 70)
NAVY2 = (14, 37, 74)
GOLD  = (161, 111, 22)
CREAM = (244, 241, 237)
INK   = (26, 26, 30)
WHITE = (255, 255, 255)

def px(inches): return int(round(inches * DPI))

F = "build/fonts/static/%s.ttf"
def font(name, pt):  # pt at 300dpi
    return ImageFont.truetype(F % name, int(round(pt * DPI / 72.0)))

def tw(d, txt, f, track=0):
    if not txt: return 0
    w = d.textlength(txt, font=f)
    return w + track * (len(txt) - 1)

def draw_tracked(d, xy, txt, f, fill, track=0.0, anchor="la"):
    x, y = xy
    total = tw(d, txt, f, track)
    if anchor[0] == "m": x -= total / 2
    elif anchor[0] == "r": x -= total
    for ch in txt:
        d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(ch, font=f) + track
    return total

def wrap_words(d, txt, f, maxw):
    out, cur = [], ""
    for w_ in txt.split():
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            out.append(cur); cur = w_
    if cur: out.append(cur)
    return out

def rich_line(d, x, y, segs, maxw, leading, fonts, default=INK):
    """segs: list of (text, fontkey, color); flows as one paragraph.
    Tokens carry their own trailing space so punctuation never gets orphaned."""
    toks = []                       # (text, fontkey, color, space_after)
    for si, (t, fk, col) in enumerate(segs):
        parts = [p for p in t.split(" ")]
        lead_space = t.startswith(" ")
        for i, w_ in enumerate(parts):
            if w_ == "":
                continue
            last = (i == len(parts) - 1)
            sp = not last or t.endswith(" ")
            if toks and i == 0 and not lead_space:
                # segment continues the previous word (e.g. "..." + ",")
                pt, pfk, pcol, psp = toks[-1]
                if not psp:
                    toks.append((w_, fk, col, sp)); continue
            toks.append((w_, fk, col, sp))
    line, lines = [], []
    for tk in toks:
        trial = line + [tk]
        wsum = sum(d.textlength(t + (" " if sp else ""), font=fonts[fk])
                   for t, fk, _, sp in trial)
        if wsum <= maxw or not line:
            line = trial
        else:
            lines.append(line); line = [tk]
    if line: lines.append(line)
    for ln in lines:
        cx = x
        for i, (t, fk, col, sp) in enumerate(ln):
            d.text((cx, y), t, font=fonts[fk], fill=col)
            cx += d.textlength(t + (" " if sp and i < len(ln)-1 else ""), font=fonts[fk])
        y += leading
    return y

def fit_font(name, text, target_w, start=60.0):
    """Largest size of `name` whose `text` fits target_w px."""
    size = start
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    while size > 6:
        f = font(name, size)
        if probe.textlength(text, font=f) <= target_w:
            return f, size
        size -= 0.5
    return font(name, 6), 6

def cap_top(f, text):
    """Distance from the text-anchor top to the visual top of the glyphs."""
    return f.getbbox(text)[1]

def cap_h(f, text):
    b = f.getbbox(text)
    return b[3] - b[1]

# ---------------------------------------------------------------- front ----
def build_front(w_in=None, h_in=None):
    w_in = TRIM_W if w_in is None else w_in
    h_in = TRIM_H if h_in is None else h_in
    src = Image.open("front cover.png").convert("RGB")
    W, H = src.size
    want_w = int(round(H * w_in / h_in))
    # keep the left edge: the title block lives there, the crop comes off the
    # blurred background at the right (verified visually).
    return src.crop((0, 0, want_w, H)).resize((px(w_in), px(h_in)), Image.LANCZOS)

# ----------------------------------------------------------------- back ----
BACK_COPY = dict(
    headline="What if the secret to becoming the best new home salesperson "
             "isn’t saying the right thing—but listening to the right people?",
    para1=[("In ", "reg", INK), ("The One Call Salesperson", "bi", NAVY),
           (", award-winning new home sales expert Julie Neill shares the real-world "
            "lessons, stories, and mindset that helped her win Salesperson of the Year "
            "with her current builder—in ", "reg", INK),
           ("only eight months, not twelve", "bold", NAVY), (".", "reg", INK)],
    para2=[("I won Salesperson of the Year with my current builder. I did it in ", "reg", INK),
           ("8 months", "bold", NAVY), (" – not 12.", "reg", INK)],
    kicker="That’s not luck. That’s a better way to sell.",
    barlabel="IN THIS BOOK, YOU’LL LEARN HOW TO:",
    bullets=["Build trust by making people feel safe and heard",
             "Turn tough conversations into stronger relationships",
             "Handle objections with calm, confidence, and empathy",
             "Stay persistent without being pushy",
             "Be the person buyers call—now and for years to come",
             "Sell more homes by putting people first"],
    bio="is an award-winning new home sales expert known for her results, "
        "integrity, and ability to connect with people on a real level.",
    quote="“Don’t be the salesperson they’re avoiding.\nBe the person they call.”",
)

def build_back():
    W, H = px(TRIM_W), px(TRIM_H)
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    L, R = px(0.55), W - px(0.55)
    CW = R - L
    cx = W // 2
    BARCODE_TOP = px(TRIM_H - 0.25 - 1.2)          # 7.55in - nothing may cross this

    fonts = dict(
        the=font("Oswald-SemiBold", 13.5), sub=font("Oswald-SemiBold", 12.5),
        head=font("SourceSans3-Bold", 12.2),
        reg=font("SourceSans3-Regular", 10.3), bold=font("SourceSans3-Bold", 10.3),
        bi=font("SourceSans3-BoldItalic", 10.3), kick=font("SourceSans3-Bold", 11.2),
        bar=font("Oswald-SemiBold", 12.6), bul=font("SourceSans3-Regular", 10.0),
        name=font("Oswald-Bold", 20), bio=font("SourceSans3-Regular", 9.5),
        q=font("SourceSans3-Bold", 10.0),
    )
    big, _ = fit_font("Oswald-Bold", "SALESPERSON", px(3.05))
    fonts["big"] = big

    def rules_around(text, f, y_cap, track):
        """Draw `text` centred with gold rules either side, aligned to its cap centre."""
        wpx = draw_tracked(d, (cx, y_cap - cap_top(f, text)), text, f, NAVY,
                           track=track, anchor="ma")
        ry = y_cap + cap_h(f, text) / 2
        gap, rl = px(0.11), px(0.60)
        d.line([(cx - wpx/2 - gap - rl, ry), (cx - wpx/2 - gap, ry)], fill=GOLD, width=4)
        d.line([(cx + wpx/2 + gap, ry), (cx + wpx/2 + gap + rl, ry)], fill=GOLD, width=4)
        return cap_h(f, text)

    y = px(0.44)
    y += rules_around("THE", fonts["the"], y, px(0.05)) + px(0.16)

    for word, col in (("ONE CALL", NAVY), ("SALESPERSON", GOLD)):
        d.text((cx, y - cap_top(big, word)), word, font=big, fill=col, anchor="ma")
        y += cap_h(big, word) + px(0.075)
    y += px(0.10)

    y += rules_around("STOP SELLING. START LISTENING.", fonts["sub"], y, px(0.014)) + px(0.27)

    for ln in wrap_words(d, BACK_COPY["headline"], fonts["head"], CW):
        d.text((L, y), ln, font=fonts["head"], fill=NAVY); y += px(0.198)
    y += px(0.10)

    y = rich_line(d, L, y, BACK_COPY["para1"], CW, px(0.165), fonts) + px(0.16)

    d.text((L, y), BACK_COPY["kicker"], font=fonts["kick"], fill=GOLD)
    y += px(0.30)

    barh = px(0.30)
    d.rectangle([L - px(0.12), y, R + px(0.12), y + barh], fill=NAVY2)
    lab = BACK_COPY["barlabel"]
    draw_tracked(d, (L, y + barh/2 - cap_h(fonts["bar"], lab)/2 - cap_top(fonts["bar"], lab)),
                 lab, fonts["bar"], WHITE, track=px(0.009))
    y += barh + px(0.16)

    r = px(0.082)
    for b in BACK_COPY["bullets"]:
        top = y + px(0.014)
        d.ellipse([L, top, L + 2*r, top + 2*r], fill=GOLD)
        ccx, ccy = L + r, top + r
        d.line([(ccx - r*0.42, ccy + r*0.02), (ccx - r*0.10, ccy + r*0.36),
                (ccx + r*0.46, ccy - r*0.36)], fill=WHITE, width=max(3, int(r*0.30)),
               joint="curve")
        d.text((L + 2*r + px(0.10), y), b, font=fonts["bul"], fill=INK)
        y += px(0.208)
    y += px(0.20)

    sy = y
    star_r = px(0.082)
    pts = []
    for i in range(10):
        ang = -math.pi/2 + i*math.pi/5
        rr = star_r if i % 2 == 0 else star_r*0.42
        pts.append((cx + rr*math.cos(ang), sy + rr*math.sin(ang)))
    d.polygon(pts, fill=GOLD)
    d.line([(L, sy), (cx - px(0.17), sy)], fill=GOLD, width=4)
    d.line([(cx + px(0.17), sy), (R, sy)], fill=GOLD, width=4)
    y = sy + px(0.18)

    boxh = BARCODE_TOP - px(0.10) - y                 # fill everything down to the barcode
    print(f"   [back] star at {sy/DPI:.2f}in, box top {y/DPI:.2f}in, boxh {boxh/DPI:.2f}in")
    d.rounded_rectangle([L - px(0.16), y, R + px(0.16), y + boxh], radius=px(0.06), fill=NAVY2)
    photo = Image.open("back cover.png").convert("RGB").crop((556, 4012, 960, 4608))
    ph = int(boxh - px(0.30))
    pw = int(photo.width * ph / photo.height)
    photo = photo.resize((pw, ph), Image.LANCZOS)
    pxl, pyl = int(L - px(0.06)), int(y + px(0.15))
    d.rectangle([pxl-4, pyl-4, pxl+pw+4, pyl+ph+4], fill=CREAM)
    im.paste(photo, (pxl, pyl))

    tx = pxl + pw + px(0.20)
    tW = R + px(0.10) - tx
    ty = y + px(0.14)
    nm = "JULIE NEILL"
    d.text((tx, ty - cap_top(fonts["name"], nm)), nm, font=fonts["name"], fill=(219, 163, 48))
    ty += cap_h(fonts["name"], nm) + px(0.10)
    for ln in wrap_words(d, BACK_COPY["bio"], fonts["bio"], tW):
        d.text((tx, ty), ln, font=fonts["bio"], fill=(230, 232, 238)); ty += px(0.158)
    ty += px(0.075)
    d.line([(tx, ty), (tx + tW*0.62, ty)], fill=GOLD, width=3)
    ty += px(0.10)
    for ln in BACK_COPY["quote"].split("\n"):
        d.text((tx, ty), ln, font=fonts["q"], fill=WHITE); ty += px(0.172)
    print(f"   [back] author-box content ends {ty/DPI:.2f}in, box bottom {(y+boxh)/DPI:.2f}in")
    return im, y + boxh

# ---------------------------------------------------------------- spine ----
def build_spine(spine_w=None, spine_h=None, margin=0.0625):
    spine_w = SPINE_W if spine_w is None else spine_w
    spine_h = TRIM_H if spine_h is None else spine_h
    W, H = px(spine_w), px(spine_h)
    im = Image.new("RGB", (W, H), CREAM)
    # compose horizontally then rotate so text reads top-to-bottom (US convention)
    strip = Image.new("RGB", (H, W), CREAM)
    d = ImageDraw.Draw(strip)
    safe = px(margin)
    band = W - 2*safe                       # usable cap-height budget
    # start from the band itself: Oswald's cap height is ~0.72em, so the largest
    # plausible size is band/0.72. A hardcover spine is ~2.5x a paperback's, and
    # a fixed starting guess would silently waste that room.
    size = (band / DPI) * 72.0 / 0.70
    while True:
        f = font("Oswald-Bold", size)
        asc, desc = f.getmetrics()
        if f.getbbox("THEONECALLSALESPERSON")[3] - f.getbbox("THEONECALLSALESPERSON")[1] > band*0.94:
            size -= 0.25; continue
        break
    f  = font("Oswald-Bold", size)
    fa = font("Oswald-SemiBold", size * 0.92)
    cy = W / 2
    ty  = cy - cap_h(f,  "THE ONE CALL SALESPERSON") / 2 - cap_top(f,  "THE ONE CALL SALESPERSON")
    tya = cy - cap_h(fa, "JULIE NEILL") / 2 - cap_top(fa, "JULIE NEILL")
    x = px(0.62)
    x += draw_tracked(d, (x, ty), "THE ONE CALL ", f, NAVY, track=px(0.004))
    x += draw_tracked(d, (x, ty), "SALESPERSON", f, GOLD, track=px(0.004))
    aw = tw(d, "JULIE NEILL", fa, px(0.006))
    draw_tracked(d, (H - px(0.62) - aw, tya), "JULIE NEILL", fa, NAVY, track=px(0.006))
    print(f"   [spine] {spine_w:.3f}in wide, type {size:.2f}pt, "
          f"cap {cap_h(f,'THE')}px, safe band {W - 2*safe}px")
    return strip.rotate(-90, expand=True)

# ----------------------------------------------------------------- wrap ----
def fit_panel(im, w_in, h_in):
    """Pad (never crop) a finished panel out to a larger case-wrap panel."""
    W, H = px(w_in), px(h_in)
    if (im.width, im.height) == (W, H):
        return im
    out = Image.new("RGB", (W, H), CREAM)
    x, y = (W - im.width)//2, (H - im.height)//2
    out.paste(im, (x, y))
    for src, box, dst in (
        (im.crop((0,0,1,im.height)),        (x, H), (0, y)),
        (im.crop((im.width-1,0,im.width,im.height)), (W-x-im.width, H), (x+im.width, y))):
        if box[0] > 0:
            out.paste(src.resize(box), dst)
    top = out.crop((0, y, W, y+1)).resize((W, y)) if y > 0 else None
    if top: out.paste(top, (0, 0))
    bot_h = H - (y + im.height)
    if bot_h > 0:
        out.paste(out.crop((0, y+im.height-1, W, y+im.height)).resize((W, bot_h)),
                  (0, y+im.height))
    return out

def build_wrap(front, back, spine, m):
    """m = measurements dict from KDP's cover calculator."""
    pw, ph = m["front-cover-width"], m["front-cover-height"]
    outer, spine_w = m["outer"], m["spine-width"]
    WW, HH = px(m["full-cover-width"]), px(m["full-cover-height"])
    im = Image.new("RGB", (WW, HH), CREAM)
    front = fit_panel(front, pw, ph)
    back  = fit_panel(back,  pw, ph)
    b = px(outer)
    im.paste(back,  (b, b))
    im.paste(spine, (b + px(pw), b))
    im.paste(front, (b + px(pw) + px(spine_w), b))
    # the wrap/bleed band is edge replication, never scaled-up artwork
    inner_h = px(ph)
    left  = im.crop((b, b, b+1, b+inner_h)).resize((b, inner_h))
    right = im.crop((WW-b-1, b, WW-b, b+inner_h)).resize((b, inner_h))
    im.paste(left, (0, b)); im.paste(right, (WW-b, b))
    im.paste(im.crop((0, b, WW, b+1)).resize((WW, b)), (0, 0))
    im.paste(im.crop((0, HH-b-1, WW, HH-b)).resize((WW, b)), (0, HH-b))
    return im

# ---------------------------------------------------------------- ebook ----
def build_ebook(front_src=None):
    src = Image.open("front cover.png").convert("RGB")
    W, H = src.size
    want_w = int(round(H * TRIM_W / TRIM_H))
    art = src.crop((0, 0, want_w, H))
    target_ratio = 1600 / 2560
    need_h = int(round(art.width / target_ratio))
    pad = need_h - art.height
    top, bottom = pad // 2, pad - pad // 2
    out = Image.new("RGB", (art.width, need_h))
    out.paste(art.crop((0, 0, art.width, 1)).resize((art.width, top)), (0, 0))
    out.paste(art, (0, top))
    out.paste(art.crop((0, art.height-1, art.width, art.height)).resize((art.width, bottom)),
              (0, top + art.height))
    return out.resize((1600, 2560), Image.LANCZOS)

def build_proof(im, m, path):
    """Annotated proof: trim/panel edges, safe area, spine folds, barcode reserve."""
    im = im.copy()
    d = ImageDraw.Draw(im, "RGBA")
    pw, ph, outer = m["front-cover-width"], m["front-cover-height"], m["outer"]
    spine_w, hinge = m["spine-width"], m.get("hinge-width", 0.0)
    marg = m.get("margin-width", 0.125)
    b, W, H = px(outer), im.size[0], im.size[1]
    RED, CY, GRN = (230,0,0,255), (0,160,220,255), (0,170,60,255)
    def box(x0,y0,x1,y1,c,w=4): d.rectangle([x0,y0,x1,y1], outline=c, width=w)
    box(b, b, W-b, H-b, RED)                                   # visible panel edge
    sx = b + px(pw)
    d.line([(sx, b),(sx, H-b)], fill=RED, width=4)             # spine folds
    d.line([(sx+px(spine_w), b),(sx+px(spine_w), H-b)], fill=RED, width=4)
    # safe area: margin on outer edges, hinge on the spine side
    box(b+px(marg), b+px(marg), sx-px(max(hinge, marg)), b+px(ph)-px(marg), CY, 3)
    box(sx+px(spine_w)+px(max(hinge, marg)), b+px(marg), W-b-px(marg),
        b+px(ph)-px(marg), CY, 3)
    if hinge:                                                  # hinge keep-clear
        d.rectangle([sx-px(hinge), b, sx, b+px(ph)], fill=(255,170,0,40))
        d.rectangle([sx+px(spine_w), b, sx+px(spine_w)+px(hinge), b+px(ph)],
                    fill=(255,170,0,40))
    sm = px(m.get("spine-margin-width", 0.062))
    box(sx+sm, b, sx+sm+1, b+px(ph), GRN, 2)
    box(sx+px(spine_w)-sm-1, b, sx+px(spine_w)-sm, b+px(ph), GRN, 2)
    # barcode reserve, both bottom corners kept clear
    bw, bh = px(2.0), px(1.2)
    by = b + px(ph) - px(m.get("barcode-margin-height", 0.25))
    for bx in (sx - px(m.get("barcode-margin-width", 0.25)) - bw,
               b + px(m.get("barcode-margin-width", 0.25))):
        d.rectangle([bx, by-bh, bx+bw, by], outline=GRN, width=5)
    f = font("Oswald-Bold", 11)
    d.text((b+px(0.30), by-bh+px(0.10)), "BARCODE RESERVE", font=f, fill=(0,120,40))
    im.save(path, dpi=(DPI, DPI))
    print("   proof ->", path)

if __name__ == "__main__":
    for d in ("dist", "dist/2_KINDLE", "dist/4_COVER_PARTS"):
        os.makedirs(d, exist_ok=True)
    back, back_bottom = build_back()          # designed once at 6x9, padded per binding
    ebook = build_ebook(None)
    ebook.save("dist/4_COVER_PARTS/OneCallSalesperson_EbookCover_1600x2560.jpg",
               quality=95, subsampling=0, dpi=(DPI, DPI))
    ebook.save("dist/2_KINDLE/OneCallSalesperson_EbookCover_1600x2560.jpg",
               quality=95, subsampling=0, dpi=(DPI, DPI))

    for binding, folder in (("paperback", "1_PAPERBACK"), ("hardcover", "1b_HARDCOVER")):
        m = measurements(binding, "6x9", PAGES, paper="cream")
        pw, ph = m["front-cover-width"], m["front-cover-height"]
        print(f"\n=== {binding.upper()}  spine {m['spine-width']}in  "
              f"wrap {m['full-cover-width']} x {m['full-cover-height']}in")
        front = build_front(pw, ph)
        spine = build_spine(m["spine-width"], m["spine-height"],
                            m.get("spine-margin-width", 0.0625))
        wrap = build_wrap(front, back, spine, m)
        os.makedirs(f"dist/{folder}", exist_ok=True)
        os.makedirs("dist/4_COVER_PARTS", exist_ok=True)
        tag = f"{binding}_{PAGES}pg"
        base = f"dist/{folder}/OneCallSalesperson_CoverWrap_6x9_{tag}"
        wrap.save(base + ".pdf", "PDF", resolution=DPI, quality=97, subsampling=0)
        wrap.save(f"dist/4_COVER_PARTS/CoverWrap_{tag}.png", dpi=(DPI, DPI))
        front.save(f"dist/4_COVER_PARTS/front_{tag}.png", dpi=(DPI, DPI))
        spine.save(f"dist/4_COVER_PARTS/spine_{tag}_{m['spine-width']}in.png", dpi=(DPI, DPI))
        build_proof(wrap, m, f"dist/4_COVER_PARTS/_PROOF_{tag}.png")
        print(f"   wrap {wrap.size[0]}x{wrap.size[1]}px = "
              f"{wrap.size[0]/DPI:.3f} x {wrap.size[1]/DPI:.3f}in")
