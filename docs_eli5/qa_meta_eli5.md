# QA review — second opinion — plain-English version

> Plain-language companion to [`meta/qa.md`](../docs/review/meta/qa.md). The original is the
> source of truth and is unchanged. If the two disagree, trust the original.

## What this is

An independent double-check of the [QA / correctness review](qa_eli5.md), re-running the
server-side cases and re-tracing the browser flows.

## The verdict

**Trustworthy and well-calibrated.** Every finding reproduced or traced cleanly, with one
mechanism corrected (below) and a couple of severity nudges. No false alarms, nothing invented.
Confidence: high — act on it as written, with the refinements.

## What it confirmed

- **The forever-frozen wait (H1)** — confirmed; the participant page really has no "session lost"
  detection while the aggregator does.
- **The raw error pop-ups (H2)** — confirmed for *both* the key-publishing and the share steps.
- **The demo button getting stuck (M2)**, the cosmetic "-0" (L1), the loose input parsing
  (L2/L3), and all the "looks fine" notes — confirmed.

## The one correction

**The bad-digit crash isn't an "HTTP 500."** The first review described the crash variant as
returning an error code "forever." More precisely: the request *thread* crashes and the
connection is simply dropped with no response at all, while a full error trace floods the server's
log on every single poll. The user-visible effect is the same (round wedged, page polls forever),
but the wording should be "the request crashes and the connection resets," not "HTTP 500."

## The severity nudge

The reviewer argues the **silent-divergence half** of the bad-digit bug deserves bumping to
Medium-High, because it defeats the demo's single headline promise — "verify it yourself" — with
no error shown anywhere. (The aggregator confidently shows an average that no participant can
reproduce.)

## Useful extra points

- The crash leaves the status indicators all showing "submitted/green" while the result never
  appears — a *more* confusing state than an obvious failure.
- Because the first (bad) value is locked in, the round can't self-heal. So the fix must reject
  the bad value **the moment it's submitted**, not just when totalling — otherwise it gets locked
  in permanently.
- Independent sessions were confirmed not to interfere with each other.

## Bottom line

The QA review is accurate and free of phantom findings. Apply two refinements: fix the "HTTP 500"
wording, and consider lifting the silent-divergence bug to Medium-High. The single
highest-value fix remains: reject non-standard digits **at submission time**, which closes both
variants and the permanent-lock problem at once.
