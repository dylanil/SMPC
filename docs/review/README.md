# How this project was reviewed

The README claims this demo was "reviewed like a small safety-critical system." A claim like that
is cheap; this folder is the evidence. It summarises the full review campaign and publishes two
representative review-council transcripts verbatim from the project's working archive.

## Two review mechanisms

**1. Whole-codebase audit campaigns.** Independent domain reviews (security, cryptography, QA,
legal, UX, product, graphics - later joined by an "additional dimensions" catch-all lens), each
followed by an equally independent *meta-review* whose job was to confirm, recalibrate, or refute
the original findings. Everything was consolidated into a single prioritised release board.

**2. A proposal-gated review council.** Before any non-trivial change was implemented, a council
convened only the relevant domain lenses plus a mandatory challenger, collected isolated opinions,
debated the collisions, and returned a go / revise / no-go recommendation for the owner to approve.
Code was written only after approval. The workflow diagram is in
[`../assets/review-council.png`](../assets/review-council.png); the two published transcripts below
show it running for real.

## The campaign, by the numbers

- **2026-06-12 - initial campaign.** 7 domain reviews + 7 independent second opinions, plus a
  gap-filling "missing dimensions" pass (12 findings, all independently confirmed). Consolidated
  into the release board.
- **2026-06-13 - re-validation run.** A second full pass: 8 isolated domain reviews + 8 isolated
  meta audits + a manager adjudication, re-validating the board against the code. Result:
  **0 refutations, no severity changes, no new findings** - the board's calibration held.
- **2026-06-14 - fresh-independent run.** A third full pass in which reviewers were told to
  *ignore* all prior reviews and the board, for maximum independence. Result: **0 Critical/High
  findings and 0 refutations of the fix work**; the mask-cancellation crypto and the test suite
  were live-reproduced by two separate reviewers. The run added 15 new lower-severity items
  (mostly presentation polish, honesty-surface accuracy, and cheap hardening).
- **2026-06-15 - closure.** Every board item implemented or consciously closed, ending with a live
  load check (~200 req/s saturation on the single instance, clean up to ~25 concurrent clients).

**Finding IDs used in the transcripts:** `RB-xx` is a release-board finding (RB-01..56, all now
resolved); `AC-xx` is an accepted limitation or deliberate owner decision (e.g. AC-02: never claim
signed shares stop impersonation - there is no identity trust anchor); `FP-xx` is a claimed finding
that meta-review refuted as a false positive (5 total, each refuted twice by independent passes).

## What the reviews actually changed

A review process is only as good as what it catches. Highlights:

- **A round-wedging input bug (RB-01).** `str.isdigit()` accepts non-ASCII digits (`²`, `١٠`),
  which passed share validation and then either crashed the result path or - worse - produced an
  average no participant could reproduce. Found by the security and QA lenses, mechanism corrected
  by meta-review, fixed with ASCII-only validation plus a pinned regression test.
- **An over-claim in the page metadata.** The `<meta name="description">` boasted
  "privacy-preserving secure" without qualification, contradicting the documented limits. The
  legal lens caught it (see the site-transparency transcript); the fix was subtractive.
- **A single misleading word in a diagram.** A proposed animation intro said "encrypt" where the
  project everywhere else says "mask" - a soft over-claim that evokes homomorphic encryption. Four
  lenses independently converged on the same one-word fix (see the cold-open transcript).
- **Limits documented instead of papered over.** The invite-race impersonation gap, the collusion
  floor, and the absence of input-honesty guarantees are stated prominently in the README and
  SECURITY.md because the review process concluded they could not honestly be claimed away.

## Published transcripts

- [`council/2026-06-14-site-transparency.md`](council/2026-06-14-site-transparency.md) - a
  four-round council on surfacing the demo's honesty story on the live site: an initial scope-down,
  an owner-directed reversal, a disclaimer-prominence pass, and the protocol-diagram decision.
  Shows the challenger role pushing back, legal/UX collisions being resolved, and an explicit
  freeze point.
- [`council/2026-06-15-gif-cold-open.md`](council/2026-06-15-gif-cold-open.md) - a short, sharp
  council on a proposed animated intro, including a challenger NO-GO adjudicated down to REVISE and
  a unanimous honesty fix the owner adopted.

## How the reviews were run (honesty note)

The reviewers were not humans. Each review, meta-review, council seat, and challenger was an
isolated AI agent session (Claude), given a single domain lens and no access to the other
reviewers' output; independence between passes was enforced by isolation, and the 2026-06-14 run
additionally withheld all prior review material. The owner adjudicated every debate and approved
every decision. That makes this both a security-review record and a demonstration of multi-agent
review orchestration - and it is stated plainly here because presenting agent output as human
expert review would be exactly the kind of over-claim the process exists to catch.

The full working archive (every per-run domain review, meta audit, debate record, and the item-by-
item release board) is deliberately kept out of the public tree - it is working paper, dense with
machine-local paths and workflow details. The summary above and the two verbatim transcripts are
the representative slice.
