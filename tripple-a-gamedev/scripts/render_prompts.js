#!/usr/bin/env node
// Render every stage prompt in wf_aaa.js so you can READ what the agents actually receive.
//
//   node render_prompts.js            # list stages + sizes
//   node render_prompts.js gate       # dump the prompt(s) whose label matches "gate"
//
// WHY THIS EXISTS: `node --check` is necessary and NOT sufficient, and this loop has now been
// bitten three separate ways by trusting it —
//   1. a template literal missing its opening backtick PARSED FINE and emitted a malformed
//      prompt (2026-07-26, the baseline_valid edit);
//   2. `batchList` built from a target that was later retired read STALE, and only failed at
//      runtime;
//   3. an ordering change put the behaviour lens where nothing could ever select it.
// None of those are syntax errors. All three are visible the moment you look at the rendered
// text or simulate the control flow. Prompts are the actual product of this file — read them.
//
// Renders by static extraction, not by executing the workflow (it has no runtime here), so
// ${...} interpolations show as <VAR> placeholders. That is enough to catch broken quoting,
// dropped concatenations, doubled clauses and stray escapes.
const fs = require('fs')
const path = require('path')

const file = path.join(__dirname, 'wf_aaa.js')
const src = fs.readFileSync(file, 'utf8')
const want = (process.argv[2] || '').toLowerCase()

// Find every `agent(` call and pair its template-literal body with the label in its opts object.
const calls = []
const re = /agent\(\s*/g
let m
while ((m = re.exec(src))) {
  const start = m.index + m[0].length
  // Walk forward to the opts object that closes this call, tracking template-literal nesting.
  let i = start, depth = 0, inTpl = false, body = ''
  for (; i < src.length; i++) {
    const c = src[i], prev = src[i - 1]
    if (c === '`' && prev !== '\\') { inTpl = !inTpl; continue }
    if (!inTpl) {
      if (c === '(') depth++
      else if (c === ')') { if (depth === 0) break; depth-- }
      else if (c === '{' && src.slice(i, i + 400).includes('label:')) break
    }
    if (inTpl) body += c
  }
  const tail = src.slice(i, i + 300)
  const lab = /label:\s*[`'"]([^`'"]+)/.exec(tail)
  calls.push({ label: lab ? lab[1].replace(/\$\{[^}]+\}/g, 'N') : '(unlabelled)', body })
}

if (!want) {
  console.log('stage'.padEnd(22), 'chars')
  for (const c of calls) console.log(' ', c.label.padEnd(20), c.body.length)
  console.log(`\n${calls.length} stages. Pass a label substring to dump one, e.g.:  node render_prompts.js gate`)
  process.exit(0)
}

let hits = 0
for (const c of calls) {
  if (!c.label.toLowerCase().includes(want)) continue
  hits++
  console.log('='.repeat(78))
  console.log(`STAGE: ${c.label}   (${c.body.length} chars)`)
  console.log('='.repeat(78))
  // Collapse the source-level concatenation seams so what prints is what the model reads.
  console.log(c.body.replace(/`\s*\+\s*\n\s*`/g, '').replace(/\\n/g, '\n').replace(/\\`/g, '`'))
  console.log()
}
if (!hits) { console.error(`no stage matching "${want}"`); process.exit(1) }
