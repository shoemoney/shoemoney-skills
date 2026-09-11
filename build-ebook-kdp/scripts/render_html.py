"""Render the book model to print-ready HTML (6x9 trim)."""
import json, html, os, sys, re
from typo import smart, smart_runs

BOOK = json.load(open("build/book.json"))
M = BOOK["meta"]
FONTDIR = os.path.abspath("build/fonts")
FINAL = "--final" in sys.argv
PAGENOS = {}
if os.path.exists("build/pagenos.json"):
    PAGENOS = json.load(open("build/pagenos.json"))

def mk(name):
    return "" if FINAL else f'<span class="mk">[[OP:{name}]]</span>'

def esc(s):
    return html.escape(smart(s))

def render_runs(runs, drop=False):
    out = []
    for i, (t, b, it) in enumerate(smart_runs(runs)):
        t = esc(t).replace("\n", "<br/>")
        if b:
            t = f"<b>{t}</b>"
        if it:
            t = f"<i>{t}</i>"
        out.append(t)
    s = "".join(out)
    if drop:
        m = re.match(r"^([A-Za-z“\"'])(.*)$", s, re.S)
        if m:
            s = f'<span class="dropcap">{m.group(1)}</span>{m.group(2)}'
    return s

def chap_id(c):
    return "ch-" + (c["num"] or "intro")

parts = []
A = parts.append

A(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(M['title'])}</title>
<style>
@font-face{{font-family:Lora;src:url('file://{FONTDIR}/static/Lora-Regular.ttf');font-weight:400;font-style:normal}}
@font-face{{font-family:Lora;src:url('file://{FONTDIR}/static/Lora-Bold.ttf');font-weight:700;font-style:normal}}
@font-face{{font-family:Lora;src:url('file://{FONTDIR}/static/Lora-Italic.ttf');font-weight:400;font-style:italic}}
@font-face{{font-family:Lora;src:url('file://{FONTDIR}/static/Lora-BoldItalic.ttf');font-weight:700;font-style:italic}}
@font-face{{font-family:Oswald;src:url('file://{FONTDIR}/static/Oswald-Regular.ttf');font-weight:400;font-style:normal}}
@font-face{{font-family:Oswald;src:url('file://{FONTDIR}/static/Oswald-Medium.ttf');font-weight:500;font-style:normal}}
@font-face{{font-family:Oswald;src:url('file://{FONTDIR}/static/Oswald-SemiBold.ttf');font-weight:600;font-style:normal}}
@font-face{{font-family:Oswald;src:url('file://{FONTDIR}/static/Oswald-Bold.ttf');font-weight:700;font-style:normal}}

@page {{ size: 6in 9in; margin: 0.78in 0.75in 0.72in 0.75in; }}

html,body{{margin:0;padding:0}}
body{{font-family:Lora,Georgia,serif; font-size:11.5pt; line-height:1.68; color:#000;
      text-align:justify; hyphens:auto; -webkit-hyphens:auto; orphans:2; widows:2;}}
p{{margin:0; text-indent:1.4em;}}
p.first, p.noindent{{text-indent:0}}
b{{font-weight:700}}

/* --- structural pages --- */
.page{{page-break-after:always; break-after:page; position:relative; text-align:center;}}
.recto{{page-break-before:always; break-after:page;}}
.blankpage{{page-break-after:always; break-after:page;}}

/* --- half title --- */
.halftitle .ht{{margin-top:2.6in; font-family:Oswald; font-weight:600; font-size:19pt;
   letter-spacing:.14em; text-transform:uppercase; line-height:1.35;}}

/* --- title page --- */
.titlepage .t1{{margin-top:1.55in; font-family:Oswald; font-weight:700; font-size:31pt;
   letter-spacing:.015em; line-height:1.06; text-transform:uppercase;}}
.titlepage .t2{{font-family:Oswald; font-weight:700; font-size:31pt; letter-spacing:.015em;
   line-height:1.06; text-transform:uppercase;}}
.titlepage .rule{{width:2.1in; height:2.4pt; background:#000; margin:.26in auto .24in;}}
.titlepage .sub{{font-family:Oswald; font-weight:500; font-size:13pt; letter-spacing:.15em;
   text-transform:uppercase;}}
.titlepage .auth{{margin-top:2.5in; font-family:Oswald; font-weight:500; font-size:15pt;
   letter-spacing:.24em; text-transform:uppercase;}}

/* --- copyright --- */
.copyright{{font-size:8.6pt; line-height:1.45; text-align:left; text-indent:0;}}
.copyright .cp{{margin:0 0 .5em 0; text-indent:0;}}
.copyright .cptop{{font-family:Oswald;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
   font-size:9pt;margin-bottom:1.1em;}}

/* --- dedication --- */
.mk{{position:absolute;left:0;top:0;color:#fff;font-size:2pt;line-height:0}}
.dedication .ded{{margin-top:3.0in; font-style:italic; font-size:12pt; line-height:1.7;
   text-align:center; text-indent:0; padding:0 .35in;}}

/* --- contents --- */
h1.fm{{font-family:Oswald; font-weight:600; font-size:15pt; letter-spacing:.24em;
   text-transform:uppercase; text-align:center; margin:0.55in 0 .1in;}}
h1.fm + .fmrule{{width:.85in;height:2pt;background:#000;margin:0 auto .42in;}}
table.toc{{width:100%; border-collapse:collapse; font-size:10.5pt; text-align:left;
   line-height:1.3;}}
table.toc td{{padding:.2em 0; vertical-align:bottom;}}
td.tnum{{font-family:Oswald;font-weight:600;width:.42in;}}
td.ttitle{{}}
td.tpage{{font-family:Oswald;font-weight:500;text-align:right;width:.4in;}}
.tdots{{border-bottom:1px dotted #bbb;}}

/* --- generic front/back matter section --- */
section.fmsec{{page-break-before:always; break-before:page; position:relative;}}
section.fmsec p{{text-indent:0; margin-bottom:.75em;}}

/* --- chapter --- */
section.chapter{{page-break-before:always; break-before:page; position:relative;}}
.chnum{{font-family:Oswald; font-weight:700; font-size:52pt; line-height:1; text-align:center;
   margin-top:1.05in; letter-spacing:-.01em;}}
.chnum.nonum{{margin-top:1.35in;}}
.chrule{{width:.72in;height:2.4pt;background:#000;margin:.16in auto .18in;}}
h2.chtitle{{font-family:Oswald; font-weight:600; font-size:16pt; letter-spacing:.11em;
   text-transform:uppercase; text-align:center; line-height:1.32; margin:0 0 .46in;
   padding:0 .12in;}}
h3.sub{{font-family:Oswald; font-weight:600; font-size:10.5pt; letter-spacing:.15em;
   text-transform:uppercase; text-align:left; margin:1.5em 0 .5em; page-break-after:avoid;
   break-after:avoid;}}
p.lead{{font-weight:700; text-indent:0; margin:.95em 0 .95em; text-align:left;}}
p.body{{margin-top:0}}
.dropcap{{float:left; font-family:Oswald; font-weight:700; font-size:32pt; line-height:.82;
   padding:.06em .09em 0 0; margin-top:.02em;}}
.endrule{{width:.45in;height:2pt;background:#000;margin:1.7em auto 0;}}

/* --- notes page --- */
section.notes{{page-break-before:always; break-before:page; page-break-after:always;
   break-after:page;}}
.notes .nlabel{{font-family:Oswald;font-weight:600;font-size:8.5pt;letter-spacing:.22em;
   text-transform:uppercase;text-align:center;color:#444;margin-top:.15in;}}
.notes h4{{font-family:Oswald;font-weight:700;font-size:15pt;letter-spacing:.2em;
   text-transform:uppercase;text-align:center;margin:.1in 0 .05in;}}
.notes .nrule{{width:.6in;height:2pt;background:#000;margin:0 auto .34in;}}
.notes .line{{border-bottom:.75pt solid #b0b0b0; height:.31in;}}
.notes .prompt{{font-style:italic;font-size:9.5pt;text-align:center;color:#222;
   margin:0 0 .3in;text-indent:0;padding:0 .2in;}}
</style></head><body>""")

# ---------- FRONT MATTER ----------
A(f'<section class="page halftitle"><div class="ht">{esc(M["title_line1"])}<br/>{esc(M["title_line2"])}</div></section>')
A('<div class="blankpage">&nbsp;</div>')
A(f'''<section class="page titlepage">
<div class="t1">{esc(M["title_line1"])}</div><div class="t2">{esc(M["title_line2"])}</div>
<div class="rule"></div><div class="sub">{esc(M["subtitle"])}</div>
<div class="auth">{esc(M["author"])}</div></section>''')

cp = [l for l in BOOK["copyright"] if l.strip()]
A('<section class="page copyright" style="text-align:left">')
A(f'<div class="cptop">{esc(cp[0])}<br/>{esc(cp[1])}</div>')
for line in cp[2:]:
    A(f'<p class="cp">{esc(line)}</p>')
A('<p class="cp" style="margin-top:1.4em">Cover design and author photograph &copy; 2026 Julie Neill.</p>')
A('</section>')

A(f'<section class="page dedication"><div class="ded">{esc(BOOK["dedication"])}</div></section>')
A('<div class="blankpage">&nbsp;</div>')

# Contents
A('<section class="page contents" style="text-align:left">')
A('<h1 class="fm">Contents</h1><div class="fmrule"></div>')
A('<table class="toc">')
rows = [("", "Introduction", PAGENOS.get("ch-intro", ""))]
for c in BOOK["chapters"]:
    if c["num"]:
        rows.append((c["num"] + ".", c["title"], PAGENOS.get(chap_id(c), "")))
rows.append(("", "One More Thing", PAGENOS.get("fm-onemore", "")))
rows.append(("", "About the Author", PAGENOS.get("fm-author", "")))
for num, title, pg in rows:
    A(f'<tr><td class="tnum">{esc(num)}</td><td class="ttitle tdots">{esc(title)}</td>'
      f'<td class="tpage">{pg}</td></tr>')
A('</table></section>')

# Gratitude
A('<div class="blankpage">&nbsp;</div>')
A('<section class="fmsec">' + mk('fm-grat') + '<h1 class="fm">A Note of Gratitude</h1><div class="fmrule"></div>')
for i, b in enumerate(BOOK["gratitude"]):
    A(f'<p class="{"first" if i==0 else "noindent"}">{render_runs(b["runs"])}</p>')
A('</section>')

# ---------- CHAPTERS ----------
NOTE_PROMPTS = [
 "What did you hear today that you almost talked over?",
 "Who on your list have you not actually called?",
 "Where in your process do people have to perform for you?",
 "Who calls you first when something goes wrong?",
 "What are you telling buyers that is urgency, not information?",
 "Which buyer have you quietly given up on?",
 "Where could you say less and learn more?",
 "What made you lose your calm this week?",
 "Which battle did you win and still lose?",
 "Which “difficult” buyer is just scared?",
 "What do your three closest competitors offer right now?",
 "What do you love about your community? Be specific.",
 "Where are you performing instead of being yourself?",
 "What did a buyer tell you that you should remember?",
 "Who did you meet this week that you didn’t follow up with?",
 "Who walked through and didn’t buy? What do they need?",
 "What did you do this week that won’t pay off until next year?",
 "Are you the salesperson they avoid, or the person they call?",
]

def notes_page(label, title, prompt):
    s = ['<section class="notes">']
    s.append(f'<div class="nlabel">{esc(label)}</div>')
    s.append('<h4>Your Notes</h4><div class="nrule"></div>')
    if prompt:
        s.append(f'<p class="prompt">{esc(prompt)}</p>')
    s.append('<div>' + '<div class="line"></div>' * 19 + '</div>')
    s.append('</section>')
    return "".join(s)

for ci, c in enumerate(BOOK["chapters"]):
    A(f'<section class="chapter" id="{chap_id(c)}">{mk(chap_id(c))}')
    if c["num"]:
        A(f'<div class="chnum">{esc(c["num"])}</div>')
    else:
        A('<div class="chnum nonum"></div>')
    A('<div class="chrule"></div>')
    A(f'<h2 class="chtitle">{esc(c["title"])}</h2>')
    first = True
    for b in c["blocks"]:
        if b["kind"] == "subhead":
            A(f'<h3 class="sub">{esc("".join(t for t,_,_ in b["runs"]))}</h3>')
            first = True
            continue
        cls = "lead" if b["kind"] == "lead" else ("first" if first else "body")
        A(f'<p class="{cls}">{render_runs(b["runs"])}</p>')
        first = False
    A('</section>')
    idx = int(c["num"]) - 1 if c["num"] else None
    prompt = NOTE_PROMPTS[idx] if idx is not None and idx < len(NOTE_PROMPTS) else \
             "What is one thing you will do differently tomorrow?"
    label = (f'Chapter {c["num"]} · {c["title"]}' if c["num"] else "Introduction")
    A(notes_page(label, c["title"], prompt))

# ---------- BACK MATTER ----------
A('<section class="fmsec" id="fm-onemore">' + mk('fm-onemore') + '<h1 class="fm">One More Thing</h1><div class="fmrule"></div>')
for i, b in enumerate(BOOK["one_more"]):
    A(f'<p class="{"first" if i==0 else "noindent"}">{render_runs(b["runs"])}</p>')
A('<div class="endrule"></div></section>')
A(notes_page("One More Thing", "", "Who makes you better? Have you told them?"))

A('<section class="fmsec" id="fm-author">' + mk('fm-author') + '<h1 class="fm">About the Author</h1><div class="fmrule"></div>')
for i, b in enumerate(BOOK["author_bio"]):
    A(f'<p class="{"first" if i==0 else "noindent"}">{render_runs(b["runs"])}</p>')
A('</section>')

A(f'''<section class="page colophon" style="text-align:center;position:relative">''' + mk('fm-end') + '''
<div style="margin-top:2.5in;font-family:Oswald;font-weight:700;font-size:15pt;
letter-spacing:.2em;text-transform:uppercase;line-height:1.5">Be the call.</div>
<div style="font-family:Oswald;font-weight:500;font-size:11pt;letter-spacing:.2em;
text-transform:uppercase;margin-top:.22in;color:#333">Be The One Call Salesperson.</div>
<div style="width:.6in;height:2pt;background:#000;margin:.34in auto 0"></div>
</section>''')

A("</body></html>")
open("build/interior.html", "w", encoding="utf8").write("\n".join(parts))
print("wrote build/interior.html")
