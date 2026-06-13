# Missing-dimensions review — second opinion — plain-English version

> Plain-language companion to [`meta/missing-dimensions.md`](../docs/review/meta/missing-dimensions.md).
> The original is the source of truth and is unchanged. If the two disagree, trust the original.
> Item codes (MD-01 … MD-12) are kept for cross-reference.

## What this is

An independent double-check of the [missing-dimensions review](missing-dimensions_eli5.md) — the
pass that went looking for angles the seven main reviews under-covered. The reviewer re-checked
every finding against the actual code.

## The verdict

**Accurate, well-calibrated, and trustworthy — no false alarms.** Every one of the twelve findings
was confirmed against the code exactly as written, including the four the original said it had
re-verified. Unlike the UX review (whose contrast numbers were wrong), this one contains no factual
error. The reviewer adds a few small footnotes and one "why is this rated the way it is" note, but
**nothing changes the to-do list.** Confidence: high.

## What it confirmed

All twelve, in short:

- **MD-01** — reloading a stuck participant's page really does lock them out permanently. Confirmed.
- **MD-02 / MD-03 / MD-07** — the three "accepted trade-offs" (a round can finalise on a garbled
  total; sessions expire from creation not last activity; multiple machines would break rounds) are
  all real and all correctly left as accepted.
- **MD-04** — it really does silently need a secure (HTTPS) connection, with no friendly check.
- **MD-05** — comma-decimal numbers really can be mangled.
- **MD-06** — the one dependency really is unpinned.
- **MD-08** — the wording that could be misread as "signatures catch impersonation" is there word
  for word.
- **MD-09** — the read pages really aren't rate-limited (but, confirmed again, raw figures stay
  safe — only round metadata is exposed).
- **MD-10 / MD-11 / MD-12** — the un-flagged deliberate decisions, the triplicated protocol rules,
  and the testing gaps are all real.

## The small additions and one calibration note

- **MD-10's "P1" rating rests on a *hypothetical*** (a future developer undoing a decision) rather
  than a current bug. The reviewer would keep it at P1 anyway — it's a near-free comment and the
  owner explicitly cares about future-developer safety — but flags that's *why* it's elevated, so
  nobody mistakes it for a live bug.
- **NEW notes (all minor):** the MD-01 fix needs care because the browser key can't simply be
  copied; the MD-02 "garbage total" has the same confusing shape as the bad-digit bug, so the
  optional safety check isn't *completely* valueless; truly reproducible builds would want
  dependency *hashes*, not just a version range (MD-06); the unlimited read pages also amplify the
  bad-digit bug's log spam (MD-09 × RB-01); and the test list correctly leaves out CI, since CI is
  a deliberate non-goal for this repo.
- **Checked and *not* a problem:** the multi-session handling is safe, and the
  monitoring/capacity gaps aren't missing — they're now logged separately as RB-36/RB-37.

## Bottom line

The missing-dimensions review is accurate and safe to act on as written. The second opinion only
adds footnotes and one rating-rationale note; it doesn't change any priorities.
