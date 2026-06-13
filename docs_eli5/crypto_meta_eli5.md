# Cryptography review — second opinion — plain-English version

> Plain-language companion to [`meta/crypto.md`](../docs/review/meta/crypto.md). The original is
> the source of truth and is unchanged. If the two disagree, trust the original.

## What this is

An independent double-check of the [cryptography review](crypto_eli5.md). The reviewer re-derived
the maths and re-ran the tests rather than taking the first review on trust — because the maths is
the part most likely to hide a subtle bug.

## The verdict

**The "it's sound, nothing critical" conclusion holds up.** Every headline claim reproduced
cleanly. No errors, no over-statements, and nothing under-stated that should have been rated
higher. The one medium finding (the precision ceiling on enormous numbers) is real and fairly
bounded. Confidence: high.

## What it confirmed

- **The masks cancel exactly** — re-tested at 3 and 10 people, and with negatives.
- **No wrap-around or truncation anywhere** — the single most common way these schemes go wrong,
  and it's genuinely done right, confirmed two independent ways.
- **The precision ceiling (M1)** — reproduced the exact example; the ~9-billion ceiling is
  correct. Fairly rated.
- **The collusion floor** is exactly as claimed.
- **The signatures prove authorship and anti-tampering, not input honesty** — confirmed.
- **The hiding is grounded in the cryptographic handshake's secrecy,** not in luck — confirmed.

## What the first review missed (minor additions only)

- **NEW-1** — The choice to use an "empty salt" in the key-derivation is fine, but the first
  review never explained *why* it's fine. (It is: the underlying secret is already high-quality,
  so the salt adds nothing and costs nothing.)
- **NEW-2** — The astronomically unlikely chance of two masks colliding is not just negligible,
  it's also harmless even if it happened. The first review dismissed it quickly; this just shows
  the working.
- **NEW-3** — The validator accepts a few non-standard ways of writing the same number (like
  "-0" or "007"), but they get normalised before use, so there's zero effect. Cosmetic only.

## Bottom line

The crypto review is accurate, well-calibrated, and trustworthy — its verdict survives
independent re-derivation and live testing. The only additions are minor footnotes that don't
change anything. Confidence: high.
