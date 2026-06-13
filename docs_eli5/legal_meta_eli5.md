# Legal review — second opinion — plain-English version

> Plain-language companion to [`meta/legal.md`](../docs/review/meta/legal.md). The original is the
> source of truth and is unchanged. If the two disagree, trust the original. (Still not legal
> advice — the reviewer is not a lawyer.)

## What this is

An independent double-check of the [legal / licensing review](legal_eli5.md), verifying each
claim against the actual repo and comparing the recommended licence text word-for-word against the
official version.

## The verdict

**Sound, accurate, and safe to act on** (within the not-legal-advice frame). The MIT licence text
is verbatim-correct, the "no licence = all rights reserved" point is fair, and the
dependency/data-protection findings check out. The one real weakness is **under-coverage, not
error** — it missed a second place where the same over-strong claim appears.

## What it confirmed

- **No licence file exists** → all rights reserved by default. Correct.
- **MIT is the right primary recommendation;** the licence text is exact and standard, with no
  missing clauses or typos.
- **The disclaimer is correctly framed** as plain-English clarity, *not* a second legal warranty.
- **The dependency is cleanly licensed** and the **data-protection footprint is genuinely tiny.**

## What the first review missed

- **G1 (the important one) — The README makes the SAME absolute claim.** The first review only
  flagged the over-strong "never sees any raw figure" wording on the aggregator *page*, but the
  very first sentence of the README (the most-read file) says the same unconditional thing. If you
  soften one, soften both — otherwise the page and the README disagree.
- **A recalibration:** the first review slightly *overstated* how exposed that claim is. The demo
  on screen is already heavily hedged with honest "this tab knows every figure" warnings, so it's
  a small consistency polish, not a big "gotcha."
- A few minor notes: the base container image raises nothing for sharing source code; a short
  `SECURITY.md` would be a nice touch; MIT needs no per-file copyright headers (the one licence
  file covers it).

## Bottom line

Adopt the first review's MIT + disclaimer recommendations as written — they're correct. Just also
hedge the README's opening sentence (G1), so the page and the README don't disagree about whether
the aggregator "ever" sees a raw figure.
