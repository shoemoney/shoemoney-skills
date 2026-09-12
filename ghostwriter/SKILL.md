---
name: ghostwriter
description: Writes AiBook chapters into manuscript/ with verified citations — dispatches a research→write→cite-check Workflow per chapter and proves the file landed. Use for "ghostwriter Ch. N", "ghostwriter 15-24", or "BATCH: Ch. X-Y".
---

# Ghostwriter — executable playbook

You are the **orchestrator**. This skill is not a description; it is a procedure. Follow every step, in order, and do not report success until Step 6 proves the bytes are on disk.

Past failure to never repeat: this skill was invoked five times on 2026-09-09 and wrote zero files because the orchestrator read a description and dispatched nothing. If you finish this skill without having called `Workflow` (or `Agent`) AND without an `ls -la`/`wc -w` proof block in your reply, you have failed.

## Fixed facts

- `BOOK_DIR`: manuscript base directory, default `~/Projects/aibook`
- Book: **AiBook: A Human Survival Guide for When the AI Steals Your Girlfriend, Becomes Your Dog's Best Friend, and Has Your Wi-Fi Password (password1)** (Jeremy "ShoeMoney" Schoemaker)
- Manuscript dir: `<BOOK_DIR>/manuscript/`
- Spine (titles + one-liners): `manuscript/00-SPINE.md`
- Jeremy's raw riffs per chapter: `manuscript/CHAPTER-BRIEFS.md`
- Voice samples (read these, imitate these): `01-How_We_Got_Here.md`, `02-Yeah_Its_a_Bubble.md`, `07-Tiny_Model_Moat.md`, `14-Ralph_Dont_You_Dare_Stop.md`
- Production story sources (example local sources; substitute your own dated incident posts): `~/Projects/airank/blog/*.md` (airank incident posts, one per day, real outcomes), `~/Projects/commander-in-chief/` (Godot 4.7 game, deterministic sim/view, test-first)
- Web research: **SearXNG only** — `mcp__searxng__searxng_web_search` then `mcp__searxng__web_url_read`. Never `WebSearch`. Say this verbatim in every research prompt.
- Model routing (hard rule from global CLAUDE.md): research = `haiku`, writing = `opus`, cite-check = `haiku`.
- No AI attribution anywhere in the output. Ever.

## Chapter template (every chapter, this order)

1. `# <Title from spine>` then `*(Spine Ch. N.)*`
2. **Epigraph.** A real, attributed quote, funny and on-topic, that teaches something: `> "quote"` then `> Name, source (year)`. Must be a quote the researcher actually found and opened (the cite-checker will try to refute it; a misattributed quote fails the chapter). No Einstein-didn't-say-that fabrications. If nothing real fits, use one of Jeremy's own lines and attribute it `— Jeremy, <where he said it>` or leave `[RECEIPT NEEDED: epigraph]`. Never invent.
3. **The hook.** First paragraph after the epigraph. Its only job is to make the reader unable to stop: open on a specific moment (a number, a time, a thing that broke, a dumb decision Jeremy made), withhold the resolution, and promise the payoff is in this chapter. No "In this chapter we will." No thesis yet.
4. `**Bottom line:**` — one paragraph, the thesis, Jeremy's mouth
3. `## When it bites` — 3-5 bullets
4. `## The pattern` (or a titled section that explains the mechanism) — may include a numbered list
5. `## One worked example` — a **real** story with date, system, outcome. From airank blog / commander-in-chief / a cited public incident. Never invented. If nothing real exists, label the block `Illustrative, not a receipt:` and add a `[RECEIPT NEEDED: Jeremy: ...]` line.
6. `## The quiet failure` — the failure that looks like success
7. `## Do / don't` — two bullet lists
8. `## Where this sits in the book` — one paragraph of cross-refs to neighbour chapters (by number + title)
9. `## Sources and receipts` — every date/number/claim listed with outlet + date + URL, or explicitly `[RECEIPT NEEDED: ...]`. Split into **Verified** and **Gaps**.

Length: 1,500-2,500 words. Voice: bottom line first, sarcastic, technical, contrarian, scars visible, short paragraphs, no corporate fluff, no "in today's fast-paced world." Swearing allowed where he'd swear. No canvas metaphor, no AgentSpace tourism, no sentences borrowed from any reference book.

## Voice rules (Jeremy's, 2026-09-09)

- **Humorous and factual at the same time.** The joke never replaces the number. Every laugh sits next to a date, a figure, a file, or a receipt.
- **Self-deprecating, never self-important.** Jeremy is not too proud to be the idiot in the story. When a chapter has a failure, the default protagonist who screwed up is Jeremy, by name, in first person. He makes fun of himself before he makes fun of anyone else. No humblebrags dressed as lessons. Credentials appear only when they are the receipt (e.g. a merged PR number), never as a flex.
- **Not egotistical.** Cut any sentence whose only function is to say Jeremy is smart, early, or right. Let the story do it or drop it.
- **His wife is never the joke.** Standing order from Jeremy (2026-09-09): never insult, embarrass, or make a punchline of his wife, in any line, caption, or aside. She is unnamed; do not invent a name. If a household joke (Georgia the Bernedoodle, the home agent, the fireplace portrait) only works by making her look left out or second place, rewrite it so Jeremy is the ridiculous one. Jeremy, Clark the robot, and the machine are always fair game.
- **Enlightening.** The reader should finish each chapter knowing one thing they can do Monday morning.
- **Internet-native, 1995-2005 vintage.** Jeremy ran NextPimp at 150K uniques a day in 2002 and was on Slashdot before it had a CSS file. The humor should sound like it. Where it fits naturally (never forced, never in the Sources section, never replacing a fact):
  - **1337 5p34k**, sparingly: `pwned`, `n00b`, `teh`, `1337`, `w00t`, `roxxor`, `sux0rz`, `j00`, `l0l`. One or two per chapter max, usually in a heading, a code comment, or the punchline of a self-deprecating line. Not in the Bottom line paragraph.
  - **All Your Base** (Zero Wing, 1992 Mega Drive; the meme peaked Feb 2001): "All your base are belong to us," "Somebody set up us the bomb," "You have no chance to survive make your time," "For great justice," "What you say!!" Use for: the agent that took over, the tool that fired, the prod DB that is now the agent's.
  - **Other era memes, fair game:** "I'm in ur base killin ur d00dz" (2006, borderline, allowed), Hampster Dance (1998), Dancing Baby (1996), "first post!" / Slashdot effect / "In Soviet Russia" (Slashdot), Badger Badger Badger (2003), Numa Numa (2004), Star Wars Kid (2003), Leeroy Jenkins (2005: the plan-vs-execution meme; Ch. 15 and 26 should use it), Chuck Norris facts (2005), Zerg rush (StarCraft, 1998), "Do a barrel roll" (Star Fox 64, 1997), Homestar Runner / Strong Bad emails (2001), "Snakes on a Plane" (2006), "the cake is a lie" (2007, only if nothing older fits), Newgrounds, Ebaum's World, Something Awful, GeoCities under-construction GIFs, `<blink>`, `<marquee>`, AOL "You've got mail," "Welcome to the Internet, here's your complimentary AOL CD," Napster, ICQ uh-oh, dial-up handshake, "Y2K." Each reference must be era-accurate; if the writer is not sure of the year, skip it. The cite-checker will flag anachronisms.
  - **"That's what she said"**, only when the technical vocabulary already loaded the chamber (the domain words: mount, load, finish, grind, hard/soft, swell, tight, deep, blew up, came out limp and didn't finish, barely fit, two workers on one unit). Built from the actual sentence, never bolted on. Max one per chapter. If it lands flat, cut it.
  - **Budget:** 2-4 such references per chapter total. The joke never replaces the number. A chapter with zero memes is fine; a chapter with eight is a Digg comment thread.

## Unslop rules (hard, checked mechanically)

- **Zero em dashes (—) and zero en dashes used as em dashes.** Use a period, comma, colon, or parentheses. `grep -c '—'` on the finished file must return 0. The only exception is inside a verbatim quoted source title.
- Banned words/phrases (delete or rewrite): delve, leverage, robust, seamless, harness (as verb), cutting-edge, game-changing, landscape, tapestry, testament, navigate (metaphorical), unlock, elevate, empower, journey, paradigm, synergy, crucial, vital, pivotal, "it's important to note", "in today's", "at the end of the day", "the reality is", "here's the thing", "let's be honest", "make no mistake", "not just X, but Y", "it's not about X, it's about Y", "the truth is", "whether you're a ... or a ...".
- No triplet lists for rhythm's sake. No rhetorical question followed by its own answer. No sentence that restates the previous sentence. No closing line that summarizes the section.
- Every paragraph must contain at least one concrete noun (a number, a file, a date, a product, a person). Abstract paragraphs get cut.

## Step 1 — Parse ARGUMENTS into a chapter list

Accept: `12`, `Ch. 12`, `15-24`, `Ch. 15-24`, `15,16,19`, `BATCH: Ch. 25-40 ...`. Extract every integer or range → sorted unique list `CHAPTERS`. Any extra prose in ARGUMENTS is per-chapter direction — keep it and pass it through to the writer as `DIRECTION`.

If ARGUMENTS is empty: ask which chapters, stop.

## Step 2 — Resolve the target file for each chapter (bash, one call)

```bash
cd $BOOK_DIR/manuscript && for n in <CHAPTERS zero-padded>; do wc -w ${n}-*.md 2>/dev/null; done
```

Rules:
- Exactly one `NN-*.md` → that is `TARGET`.
- Two files (duplicate naming conventions exist for Ch. 1-8, 10, 11, 13) → `TARGET` = the one with the **higher word count** (the real draft; the ~80-word one is a template skeleton). Record the skeleton path as `DUPLICATE` and report it at the end — do not delete it.
- Zero files → `TARGET` = `NN-<Spine_Title_Slug>.md` (underscores, no punctuation).

Also pull, for each chapter, in one bash: the spine line(s) (`grep -n -A2 "Ch. N —" 00-SPINE.md`), and the CHAPTER-BRIEFS section (`awk '/^## .*Ch\.? *N\b/,/^## /' CHAPTER-BRIEFS.md`). If the brief is missing, say so in the prompt — the writer must not invent Jeremy's opinions; it writes from spine + research and flags where his take is needed.

## Step 3 — Dispatch the Workflow (this is the step that was skipped before)

Call the `Workflow` tool with the script below, passing `args` as a real JSON array (not a string):

```json
[{"n": 15, "target": "/Users/.../15-A_Plan_Is_Not_the_Work.md", "title": "A Plan Is Not the Work", "spine": "<one-liner>", "brief": "<CHAPTER-BRIEFS text or 'none'>", "existing": "<current file contents, may be skeleton>", "direction": "<from ARGUMENTS>"}]
```

Script (copy verbatim, edit nothing except nothing):

```javascript
export const meta = {
  name: 'ghostwriter-chapters',
  description: 'Research, write, and cite-check AiBook chapters into manuscript/',
  phases: [
    { title: 'Research', detail: 'Haiku: SearXNG + airank blog receipts' },
    { title: 'Write', detail: 'Opus: chapter in Jeremy voice, writes file' },
    { title: 'Unslop', detail: 'Sonnet: zero em dashes, banned words out, tighten' },
    { title: 'Cite-check', detail: 'Haiku: refute every citation' },
    { title: 'Patch', detail: 'Opus: fix or flag refuted claims' },
  ],
}

const RESEARCH = {
  type: 'object',
  properties: {
    receipts: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, outlet: { type: 'string' }, date: { type: 'string' },
      url: { type: 'string' }, quote: { type: 'string' }, confidence: { type: 'string' } },
      required: ['claim', 'outlet', 'date', 'url', 'confidence'] } },
    stories: { type: 'array', items: { type: 'object', properties: {
      source: { type: 'string' }, date: { type: 'string' }, what_happened: { type: 'string' },
      outcome: { type: 'string' }, path_or_url: { type: 'string' } },
      required: ['source', 'date', 'what_happened', 'outcome', 'path_or_url'] } },
    gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['receipts', 'stories', 'gaps'],
}

const WRITE = {
  type: 'object',
  properties: { path: { type: 'string' }, words: { type: 'number' }, flagged: { type: 'array', items: { type: 'string' } } },
  required: ['path', 'words', 'flagged'],
}

const CHECK = {
  type: 'object',
  properties: {
    verdicts: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, status: { type: 'string' }, reason: { type: 'string' } },
      required: ['claim', 'status', 'reason'] } },
    unsupported_count: { type: 'number' },
  },
  required: ['verdicts', 'unsupported_count'],
}

const results = await pipeline(
  args,
  ch => agent(
    'You are a fact researcher for a book chapter. ALL web search goes through our local SearXNG: use mcp__searxng__searxng_web_search (pass engines="google,bing,wikipedia,wikiquote,mojeek,qwant,yahoo") then mcp__searxng__web_url_read to open sources. NEVER use WebSearch. Load them via ToolSearch first. HARD CAP: 6 searches per task; an empty result is not retried. If every search returns nothing, SearXNG is rate-limited: stop, return what you have, and put "SEARXNG DOWN" in gaps.\n\n' +
    'CHAPTER ' + ch.n + ': ' + ch.title + '\nSPINE: ' + ch.spine + '\nJEREMY BRIEF: ' + ch.brief + '\nDIRECTION: ' + ch.direction + '\n\n' +
    'Tasks:\n' +
    '1. Find 5-10 checkable receipts (dates, numbers, named incidents, papers, vendor announcements) that support or sharpen this chapter. Each MUST have outlet, date (month+year minimum), and a URL you actually opened. confidence = "verified" only if you opened the page and saw the claim; otherwise "unverified".\n' +
    '2. Find 2-3 real stories. FIRST grep the local airank blog at ~/Projects/airank/blog/ (dated incident posts — read the ones whose titles match the theme; cite the file path). Also consider ~/Projects/commander-in-chief/ (Godot game, test-first, deterministic sim). THEN public documented incidents via SearXNG.\n' +
    '3. Find 2-3 candidate EPIGRAPHS: real, attributed quotes that are funny, on-topic, and teach something (engineers, comedians, scientists, old programmers, Jeremy himself). Open the source page and confirm the wording and attribution. Add each as a receipt with claim starting "EPIGRAPH:" and the exact wording in quote. No Einstein/Twain/Franklin misattributions; if you cannot confirm who said it, drop it.\n' +
    '4. List gaps: anything the chapter needs that you could not verify. Do not guess. Do not invent. An empty list beats a fake URL.\n' +
    'Return only the structured object.',
    { label: 'research:ch' + ch.n, phase: 'Research', model: 'haiku', schema: RESEARCH }
  ),
  (research, ch) => agent(
    'You are ghostwriting a chapter of AiBook for Jeremy "ShoeMoney" Schoemaker. Write it AS HIM. First read these voice samples in full: <BOOK_DIR>/manuscript/01-How_We_Got_Here.md, 02-Yeah_Its_a_Bubble.md, 07-Tiny_Model_Moat.md. Match that register exactly: bottom line first, sarcastic, technical, contrarian, short paragraphs, scars visible.\n\n' +
    'CHAPTER ' + ch.n + ': ' + ch.title + '\nSPINE: ' + ch.spine + '\nJEREMY BRIEF (his words — his opinions come from here, not from you): ' + ch.brief + '\nDIRECTION: ' + ch.direction + '\n\n' +
    'EXISTING FILE (may be a skeleton; keep anything real, replace [RECEIPT NEEDED: brief ...] template placeholders):\n' + ch.existing + '\n\n' +
    'RESEARCH (use ONLY these receipts and stories for dates/numbers/incidents; anything not here gets [RECEIPT NEEDED: ...]):\n' + JSON.stringify(research) + '\n\n' +
    'VOICE: humorous AND factual (every joke sits next to a number or receipt); self-deprecating (when something broke, Jeremy is the idiot in the story, first person, by name; he mocks himself before anyone else); never egotistical (cut any sentence whose only job is to say Jeremy is smart or early); enlightening (one thing the reader can do Monday morning).\n' +
    'INTERNET 1995-2005 LAYER, 2-4 references per chapter, only where natural, never in Sources, never replacing a fact: light 1337 5p34k (pwned, n00b, teh, w00t, 1337; one or two, in a heading, code comment, or punchline, never in Bottom line); All Your Base lines ("All your base are belong to us", "Somebody set up us the bomb", "You have no chance to survive make your time", "For great justice", "What you say!!") for agents/tools that took over; era memes (Hampster Dance 1998, Dancing Baby 1996, Slashdot "first post"/"In Soviet Russia", Badger Badger 2003, Numa Numa 2004, Star Wars Kid 2003, Leeroy Jenkins 2005 for plan-vs-execution, Chuck Norris facts 2005, Zerg rush, "Do a barrel roll", Homestar Runner/Strong Bad, GeoCities under-construction GIF, <blink>, <marquee>, AOL "You\'ve got mail", Napster, ICQ uh-oh, dial-up handshake, Y2K). Era-accurate only; skip if unsure of the year. One "that\'s what she said" max, and only if the chapter\'s own technical words (mount, load, finish, grind, hard/soft, blew up, barely fit) set it up; never bolted on.\n' +
    'Template, in this order: # Title, *(Spine Ch. N.)*, EPIGRAPH as a blockquote (> "quote" newline > Name, source (year)) chosen ONLY from research receipts whose claim starts "EPIGRAPH:"; if none, write "> [RECEIPT NEEDED: epigraph]"; then THE HOOK: one paragraph whose only job is to make the reader unable to stop (open on a specific moment: a number, a time, a thing that broke, a dumb decision Jeremy made; withhold the resolution; no thesis yet, no "in this chapter"); then **Bottom line:**, ## When it bites, ## The pattern, ## One worked example (a REAL story from research.stories with date + outcome; if none, label "Illustrative, not a receipt:" and add a [RECEIPT NEEDED: Jeremy: ...] line), ## The quiet failure, ## Do / don\'t, ## Where this sits in the book (cross-ref neighbour chapters by number), ## Sources and receipts (Verified list with outlet+date+URL, then Gaps list).\n' +
    '1,500-2,500 words. No AI attribution. No canvas metaphor.. Do not invent a citation, ever.\n' +
    'STYLE HARD RULES: ZERO em dashes (the character —). Use periods, commas, colons, or parentheses instead. Banned words: delve, leverage, robust, seamless, harness (verb), cutting-edge, game-changing, landscape, tapestry, testament, navigate, unlock, elevate, empower, journey, paradigm, synergy, crucial, vital, pivotal, "it\'s important to note", "in today\'s", "at the end of the day", "the reality is", "here\'s the thing", "let\'s be honest", "make no mistake", "not just X but Y", "it\'s not about X it\'s about Y", "the truth is". No triplet lists for rhythm. No rhetorical question you then answer. No closing line that summarizes the section. Every paragraph needs a concrete noun (number, file, date, product, person).\n\n' +
    'Use the Write tool to write the finished chapter to EXACTLY this path: ' + ch.target + '\nThen run `wc -w` on it and `grep -c "—"` (must be 0). Return path, word count, and the list of [RECEIPT NEEDED] lines you left.',
    { label: 'write:ch' + ch.n, phase: 'Write', model: 'opus', schema: WRITE }
  ),
  (written, ch) => agent(
    'Unslop pass. Edit ' + ch.target + ' in place with the Edit tool (or rewrite with Write if edits exceed 20). Do NOT change facts, numbers, citations, section order, or [RECEIPT NEEDED] lines. Do:\n' +
    '1. Remove EVERY em dash (—) and any en dash (–) used as one. Rewrite each sentence with a period, comma, colon, or parentheses. After editing, run `grep -c "—" ' + ch.target + '` and it must print 0; keep going until it does.\n' +
    '2. Delete or rewrite banned words/phrases: delve, leverage, robust, seamless, harness (verb), cutting-edge, game-changing, landscape, tapestry, testament, navigate (metaphorical), unlock, elevate, empower, journey, paradigm, synergy, crucial, vital, pivotal, "it\'s important to note", "in today\'s", "at the end of the day", "the reality is", "here\'s the thing", "let\'s be honest", "make no mistake", "not just X but Y", "it\'s not about X it\'s about Y", "the truth is", "whether you\'re a ... or a ...".\n' +
    '3. Cut: triplet lists written for rhythm, rhetorical questions followed by their own answer, sentences that restate the previous one, closing lines that summarize the section, paragraphs with no concrete noun.\n' +
    '4. Keep the voice: bottom line first, sarcastic, technical, short paragraphs. Shorter is better. Target 1,400-2,300 words after the cut.\n' +
    '5. PRESERVE the jokes: 1337 5p34k, All Your Base lines, 1995-2005 meme references, and "that\'s what she said" lines are intentional and stay verbatim (misspellings included). Do not "correct" pwned, teh, n00b, w00t.\n' +
    'Return: em-dash count after (must be 0), words before/after, and the list of banned phrases you removed.',
    { label: 'unslop:ch' + ch.n, phase: 'Unslop', model: 'sonnet' }
  ),
  (written, ch) => agent(
    'Adversarial citation check. Read ' + ch.target + '. FIRST: the epigraph blockquote under the title. Verify the exact wording and the attribution via SearXNG; misattributed or unverifiable = "unsupported". THEN extract EVERY concrete claim: dates, dollar figures, percentages, named incidents, paper titles, product names with versions, quotes. For each, decide status: "supported" (a URL/file path in the Sources section backs it and it is plausible), "flagged" (already marked [RECEIPT NEEDED]), or "unsupported" (stated as fact with no source, or the source does not say that). For anything you doubt, verify via mcp__searxng__searxng_web_search / mcp__searxng__web_url_read (load via ToolSearch; NEVER WebSearch) or read the local file. Default to unsupported when uncertain. Return the verdict list and unsupported_count.',
    { label: 'check:ch' + ch.n, phase: 'Cite-check', model: 'haiku', schema: CHECK }
  ),
  async (check, ch) => {
    if (!check || check.unsupported_count === 0) return { n: ch.n, target: ch.target, unsupported: 0, patched: false }
    const bad = check.verdicts.filter(v => v.status === 'unsupported')
    await agent(
      'Patch ' + ch.target + ' in place with the Edit tool. These claims were judged UNSUPPORTED:\n' + JSON.stringify(bad, null, 2) + '\n\nFor each: either soften to an explicitly hedged statement, or append " [RECEIPT NEEDED: <what would prove it>]" right after the claim. Do NOT add new sources you did not verify. Keep the voice. Do not touch anything else. Return the list of edits made.',
      { label: 'patch:ch' + ch.n, phase: 'Patch', model: 'opus' }
    )
    return { n: ch.n, target: ch.target, unsupported: bad.length, patched: true }
  }
)

return results.filter(Boolean)
```

Batch size: any. The runtime caps concurrency at ~10-16 agents; 20 chapters just queue. Do not split into multiple Workflow calls unless a chapter needs different direction.

## Step 4 — While it runs

Do not narrate. Do not claim progress. You may answer the user. When the `<task-notification>` arrives, go to Step 5.

## Step 5 — Read the result

The workflow returns `[{n, target, unsupported, patched}]`. If any chapter returned `null`, the writer died — re-run the Workflow with `resumeFromRunId` for the failed chapters only.

## Step 6 — PROVE IT (mandatory, in your reply)

```bash
cd $BOOK_DIR/manuscript && ls -la <targets> && wc -w <targets> && grep -c "RECEIPT NEEDED" <targets> && grep -c "—" <targets>
```

Success per chapter = mtime is after the Workflow started AND words ≥ 1200 AND the file starts with `# ` AND em-dash count is 0. Anything else is a failure. Say so. If em dashes remain, run the Unslop agent prompt from Step 3 on that file directly via the Agent tool (model sonnet) and re-check.

## Standalone retrofit (for chapters written before the epigraph/hook/humor rules)

`/ghostwriter retrofit 1-24` runs a 4-stage pipeline per chapter file: Haiku finds 3 verified epigraph candidates via SearXNG (opened source required) → Opus inserts the epigraph blockquote under the spine line, adds a 60-120 word hook paragraph before **Bottom line:**, adds 3-6 self-deprecating first-person lines where Jeremy's own failures appear, adds 2-4 era-accurate 1995-2005 internet references per the Internet layer rule above (1337 5p34k, All Your Base, Leeroy Jenkins, etc.; one "that's what she said" max, only if the chapter's own words set it up), and deletes ego sentences → Sonnet unslop (em dash 0, memes preserved) → Haiku re-verifies the epigraph attribution and flags any meme reference whose year is wrong and replaces it with `> [RECEIPT NEEDED: epigraph ...]` if it fails. Facts, numbers, citations, section order, and `[RECEIPT NEEDED]` lines are never touched. Reference script: the persisted `ghostwriter-retrofit-*.js` in this session's workflows dir; rebuild from this description if missing.

## Standalone unslop (for chapters written before this rule)

`/ghostwriter unslop 1-14` runs only the Unslop stage (Step 3 prompt, `model: 'sonnet'`) on the resolved target files, then the Step 6 proof. Use the same Workflow shape with a single pipeline stage.

Then update `CHAPTER-BRIEFS.md`: under each chapter's section append one line `- Status: drafted <date> by ghostwriter, <words> words, <N> receipts open`. Report to the user as a table: chapter, file, words, open receipts, duplicate-skeleton path (if any). List the `[RECEIPT NEEDED]` lines that need **Jeremy** specifically (his production stories, his numbers) — those are the questions to ask him next.

## What this skill never does

- Never invents a source, date, quote, or URL. Gaps are flagged, not filled.
- Never borrows sentences from any reference book. Original text only.
- Never adds AI attribution.
- Never says "done" without the Step 6 proof block.
- Never uses WebSearch — SearXNG only.
