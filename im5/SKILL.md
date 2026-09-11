---
name: im5
description: Explain a thing as if the reader is five years old, in plain words, very short. Use this WHENEVER the user types /im5 followed by a topic, or asks to have something explained "like I'm 5", "in plain English", "without the jargon", "dumb it down", or "what does that actually mean". The topic is whatever follows the command.
---

# im5

Explain **the thing the user named after `/im5`** as if they are five.

## The whole job

Take the topic. Say what it is in a way a smart person with zero background gets on the first read.

## Rules

1. **Four sentences, hard cap.** Usually two or three is better. If it needs more, it needs a better comparison, not more sentences.
2. **One everyday comparison**, from a kitchen, a house, a car, a queue, mail, toys, or money. Pick the one that actually matches the mechanics, not the first one that comes to mind.
3. **Zero jargon.** No acronyms, no nouns invented by the industry. If a term is the whole point, give the plain version first, then name it once at the end: `That's what people mean by X.`
4. **Say what it is FOR before what it is.** Five-year-olds ask "why does that exist", not "how is it implemented".
5. **No hedging.** No "essentially", "basically", "sort of", "you can think of it as". Just say the thing.
6. **No preamble.** Do not restate the question. First word is the answer.
7. **One emoji max**, at the end, only if it adds something. Usually it does not.

## Shape

```
<What it's for, one sentence.>
<The comparison, one or two sentences.>
<The one consequence that matters.>
That's what people mean by <term>.
```

## Worked examples

**`/im5 a load balancer`**

> One computer can only answer so many people at once. A load balancer is the host at a busy restaurant who sends each new group to whichever table is free, so nobody waits at the door while a table sits empty. If one table catches fire, the host just stops seating people there and everyone else keeps eating.

**`/im5 a race condition`**

> Two people reach for the last cookie at the same time. Both of them saw a cookie there, both grabbed, and now one is holding crumbs and confused. Computers do this constantly and it only breaks sometimes, which is why it takes weeks to find.

**`/im5 DNS`**

> You know the name of the place you want, not where it is. DNS is the phone book that turns "the pizza place" into an actual street address, so your computer knows where to knock. When it's broken, everything looks down even though every site is fine.

## What this is not

Not a tutorial, not a summary, not an outline. If the honest answer needs detail, give the five-year-old version first and then offer: `Want the real version?`
