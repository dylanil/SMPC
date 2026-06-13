# Legal / licensing review — plain-English version

> Plain-language companion to [`legal.md`](../docs/review/legal.md). The original is the source
> of truth and is unchanged. If the two disagree, trust the original. Finding codes (S1, S2,
> C1, N1…) are kept for cross-reference.

## Important caveat

The reviewer is **not a lawyer and this isn't legal advice.** It's a practical "let's get this
hobby/portfolio repo into a normal, sensible state and not over-promise" pass. For a demo with no
real users, the stakes are tidiness and honesty, not liability.

## The three things to do if you do nothing else

1. **Add a licence file.** Right now there's none — which legally means "all rights reserved," so
   nobody is actually allowed to reuse or build on the code. That's the opposite of what a
   portfolio piece wants. The recommendation is the **MIT licence** (short, well-known,
   permissive). Ready-to-paste text is in the original.
2. **Add a short "this is only a demo" disclaimer** — a one-line footer on the pages and a
   sentence in the README: it's a demonstration, provided as-is, don't enter real sensitive
   figures.
3. **Soften one absolute claim.** The aggregator page says it "never sees any participant's raw
   figure" — true for a real round, but the page's own built-in demo *does* generate and show
   figures. One small qualifying clause fixes the inconsistency.

## More detail on the recommendations

- **S1 (licence):** MIT is the right default. Apache-2.0 was considered (it adds patent
  protection, which can matter for crypto-related code in a commercial setting) but is overkill
  for a portfolio demo using only standard, unpatented building blocks.
- **S2 (disclaimer):** This is *not* a second legal warranty — the MIT licence already contains
  the legal "no warranty" wording. The disclaimer is plain-English clarity of intent ("this is a
  toy, don't put real data in"). Keep it plain; don't paste legalese into the UI.
- **C1 (soften the claim):** Turning a potential "gotcha" into a sentence that shows you
  understand the boundary actually *adds* credibility.

## The good news (no action needed)

- **The one dependency is cleanly licensed** and is downloaded at build time rather than copied
  in, so it creates no attribution obligations for this repo.
- **The privacy/data-protection footprint is tiny** — nothing personal is saved to disk, there's
  no database, and the logs deliberately avoid recording sensitive data. About as small a GDPR
  footprint as a web app can have.
- **The documentation is notably honest** and doesn't oversell, the insurance angle is already
  scoped as just "an example," and there are no trackers or analytics that would drag in
  cookie-consent obligations.

## "Get a real solicitor" flags (only if it ever goes commercial)

Not needed now, but listed so they're not forgotten: turning it into a real multi-user service
handling real figures (privacy notices, formal assessments, terms of service), trademark
clearance if you brand it, and contributor agreements if you accept outside contributions.
