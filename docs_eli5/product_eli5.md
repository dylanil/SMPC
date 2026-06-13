# Product / viability review — plain-English version

> Plain-language companion to [`product.md`](../docs/review/product.md). The original is the
> source of truth and is unchanged. If the two disagree, trust the original. Finding codes
> (H-P1, M-P1…) are kept for cross-reference.

## What this was

The "big picture" review that pulls the other five together and asks one question: **is this a
believable, useful proof-of-concept and a strong portfolio piece** that would impress a skeptical
senior engineer or hiring manager? (Not "could you sell it?")

## The verdict

**Yes — it's a credible, genuinely strong portfolio piece — but it's currently undercut by a few
specific, fixable bugs that a sharp reviewer will hit before they finish admiring the clever
parts.**

The reason it lands: the cryptography is *actually correct* (independently confirmed), the
recent security-risk addition was handled properly, the documentation is unusually honest about
its own limits, and there's a built-in way for anyone to independently verify the result. That
combination — correct crypto + honest framing + real hardening + verifiability — is exactly what
signals competence.

What holds it back is concrete and fixable: the forever-frozen waiting page, the ugly raw error
pop-ups, the missing licence file, and the bad-digit bug that can wedge a round. None of these are
deep — they're an afternoon of work each — but they matter disproportionately because they're the
parts a visitor actually *experiences*, versus the crypto they have to *trust you about*.

## The skeptic's toughest objections, and how well the project answers them

1. **"It only computes an average — so what?"** Fair, but the point isn't the arithmetic, it's
   that no raw number is ever exposed and the result is independently checkable. **Answered well.**
2. **"Anyone can just lie about their own number."** True — and the project openly says so.
   **Answered well.**
3. **"The signatures don't stop impersonation."** The sharpest objection — and the one the
   project handles *best*, by naming it as a known limitation in writing. Owning your biggest
   weakness reads as understanding, not naivety. **Answered well.**
4. **"It stalls if anyone drops out."** True, and this is the **gap**: it's under-mentioned in
   the user-facing docs *and* it's the cause of the worst live bug (the frozen page). The one
   under-acknowledged objection is also the one producing the worst experience — so fixing it is
   the highest-leverage move.
5. **"Collusion breaks it."** Inherent to the scheme, and honestly documented. **Answered well.**

Net: four of the five toughest objections are fairly and openly acknowledged; the fifth (dropout)
is the gap to close.

## Is the insurance framing apt?

Mostly yes — and keeping it as just one *example* rather than the whole pitch is the right call.
"Competing insurers privately comparing average claim costs" is a believable motivation
(distrustful competitors, sensitive numbers). A real insurance consortium would want more than a
simple average and would usually run it through a trusted third party — so the example earns
"believable motivation," not "this is how insurers actually do it." Keeping the app generic is
smart: it avoids faking domain expertise while still giving a concrete hook.

## What it signals well (strengths)

Correct, non-hand-waved crypto; built-in independent verification (rare in demos); honest
documentation (every reviewer remarked on it); real defensive depth for a demo; the security-risk
addition handled correctly; and a UI that teaches as it goes.

## What undercuts it (drags)

The forever-frozen wait, the raw error pop-ups, the missing licence, the round-wedging bad-digit
bug, one over-strong privacy claim, no signpost for the lone visitor, and a couple of
accessibility nits.

## Does the value land in 30 seconds?

**Partially.** A literate reader gets "private inputs, public average" quickly, but two things
blunt it: it doesn't quickly convey *why private averaging is hard* (a skeptic might think "just
use a trusted server"), and a lone visitor has no fast path to actually see it run. Fixing the
signpost and adding a screenshot/GIF to the README are the cheapest first-impression wins.

## Priority fixes

- **High:** fix the infinite wait (H-P1); replace the raw error pop-ups (H-P2); add a licence
  (H-P3); harden the share input so one bad value can't wedge a round (H-P4).
- **Medium:** add a solo-demo signpost (M-P1); add a README "what this is / isn't" section
  including the dropout limitation (M-P2); soften the one absolute privacy claim (M-P3); add a
  screenshot or GIF (M-P4).
- **Low:** re-enable the stuck demo button (L-P1); accessibility polish (L-P2); the cosmetic
  "-0" (L-P3).

## Bottom line

A credible, honest, technically-sound proof-of-concept that already does the hard part right. The
remaining work is almost entirely on the surfaces a visitor touches — fix those and a skeptical
senior engineer comes away impressed rather than unconvinced.
