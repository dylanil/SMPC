# Cryptography review — plain-English version

> Plain-language companion to [`crypto.md`](../docs/review/crypto.md). The original is the source
> of truth and is unchanged. If the two disagree, trust the original. Finding codes (M1, N1…)
> are kept for cross-reference.

## What this was

A check of whether the **maths** behind the privacy actually works — not the website, not the
buttons, just: does the masking genuinely hide each person's number while still producing the
correct average? The reviewer both read the code and ran real rounds to test it.

## The verdict: it's sound

The core promise holds up. When everyone's masked numbers are added together, the secret "fudge"
values **cancel out exactly** — tested with 3 people, with 10 people, and even with negative
numbers. Crucially, the maths is done with unlimited-size whole numbers and **never wraps around
or gets truncated**, which is the single most common way schemes like this go subtly wrong — and
here it's done right. The aggregator genuinely only ever learns the total (hence the average) and
nothing about any individual figure.

The privacy rests on a well-established cryptographic handshake (ECDH on the P-256 curve) that
the aggregator simply cannot reverse, because it never holds the necessary secret keys.

There are no critical or high-severity problems. The caveats that exist are the normal,
unavoidable ones for this style of scheme, and the project documents them honestly.

## The one medium finding (M1)

For **extremely large numbers** — above roughly 9 billion — the browser's number handling loses a
tiny bit of precision before the value gets locked into exact maths. In plain terms: if someone
entered a figure in the billions with fractional pennies, the fractional part could be slightly
off. It does **not** break the cancellation or cause mismatches between people; it's purely a
ceiling on how huge a single input can be before it loses sub-unit precision. For realistic
figures (claim costs in pounds) this never bites. Worth a one-line note in the docs; not a real
bug for normal data.

There's also one tiny cosmetic rounding asymmetry for negative halves (L1) that has no real
effect.

## The honest boundaries (what it deliberately doesn't do)

These aren't flaws — they're the edge of what this kind of scheme can offer, and they're all
documented:

- **Collusion has a floor.** If all-but-two participants gang up (or one teams up with the
  aggregator), they can work out a remaining person's number. With at least two honest people
  left, each individual stays hidden. This limit is exact and confirmed.
- **No proof that inputs are honest.** Someone can lie about their *own* number and it's
  undetectable — the signatures prove *who* submitted and that it wasn't tampered with by others,
  not that the number was truthful or reasonable.
- **No handling for dropouts.** If anyone fails to submit, the round just stalls. Production
  systems add extra machinery to recover from this; this demo doesn't.
- **No pre-established identities,** so the impersonation race (covered in the security review) is
  open.

## Where it sits

The reviewer's honest one-liner: this is *"a correct, end-to-end-verifiable demo of pairwise-
masked secure averaging — the cryptographic plumbing of secure aggregation, minus the
dropout-resilience, malicious-security, and identity layers that production deployments require."*
In other words: well above a hand-wavy toy, deliberately below a production system, and honest
about exactly where it sits. The independent verification (the separate check script, and the
in-browser re-checking) is genuinely good engineering that most demos skip.
