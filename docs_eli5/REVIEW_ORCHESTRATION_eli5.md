# Review Orchestration Brief — plain-English version

> Plain-language companion to [`REVIEW_ORCHESTRATION.md`](../docs/REVIEW_ORCHESTRATION.md). The
> original is the source of truth and is unchanged. If the two disagree, trust the original.

## What this is

A ready-to-go plan for running **all** the project's reviews at once using a team of AI
assistants ("agents"), with one **manager** agent in charge of pulling everything together into a
single balanced to-do list — instead of doing the reviews one at a time across many sessions, the
way they were built up until now.

The idea: open a **fresh** session (so there's plenty of working memory), point it at the original
brief, and let it run the whole thing.

## Why a fresh session

The manager has to keep *every* agent's findings in its head at once to weigh them against each
other, and each helper agent also starts from scratch (which is costly). Doing this with a clean,
empty working memory means nothing important gets squeezed out or summarised halfway through.

## The important catch: it's not all at the same time

You might picture every review running simultaneously. It can't *quite*, because each
"second-opinion" review has to read the review it's checking. So it runs in **three rounds**:

1. **Round 1 — the eight reviews, all at once.** Security, cryptography, quality, legal, user
   experience, product, visual design, and a catch-all "other angles" review. They don't depend on
   each other, so they all run in parallel. Each writes its findings into a **dated folder** so it
   doesn't overwrite the existing, carefully-curated reviews.
2. **Round 2 — the eight second opinions, all at once.** Each one double-checks its matching review
   from Round 1 (so it has to wait for Round 1 to finish), confirming, correcting, or refuting the
   findings and spotting anything missed.
3. **Round 3 — the manager.** It reads all sixteen results, applies the corrections from the
   second opinions, removes duplicates (the same issue often shows up in several reviews), decides
   *when* each thing should be done (must-fix / should-fix / nice-to-have / accepted / false
   alarm), and produces the final balanced to-do list and plan. It then updates the plain-English
   versions and the README's "Known limitations" if anything important changed.

   **Who the manager "is."** The brief tells the manager to act like a rare, top-tier all-rounder —
   an expert **actuary, software developer, business strategist, and product designer all in one** —
   so it judges every issue from all four angles, not just the one that raised it. The aim is a
   plan that's **fair, practical, and genuinely worth doing for a portfolio demo** — not
   over-engineered beyond what the project needs.

   **It runs a debate, it doesn't just staple findings together.** Where two reviewers disagree or
   pull in opposite directions (say, tighter security vs. a simpler experience), the manager puts
   the two views head-to-head, has them argue it out, and settles on the best-justified balance —
   writing down *why* it landed there.

   **It asks before it guesses (the "95% rule").** If the manager is ever less than ~95% sure what
   you actually want, it **stops and asks you** until it's sure, instead of guessing. And it will
   **never make a hidden assumption** — anything it has to assume is stated out loud and flagged to
   you. (This same rule applies to me and to every helper agent too, on this and any task.)

   **It challenges your thinking, not just the findings.** The manager is told to push back on your
   *own* framing and design choices too — pointing out hidden assumptions and offering alternative
   angles (a different core use case or audience, a sharper pitch, a simpler or bolder design) so
   you might see the product in a new light. It makes the strongest honest case for the alternative,
   flags it clearly (especially if it touches a decision you've already made), and leaves the choice
   to you — the aim is to *illuminate*, never to be contrarian for its own sake.

That's **17 agents in total** (8 + 8 + 1).

## The rules every agent must follow

The brief hands every agent the project's fixed decisions so none of them waste effort
re-arguing settled points: no caps on number size, keep the "Simulated round" warning, never claim
the signatures stop impersonation, keep the app lightweight (no database, accounts, or heavy
infrastructure), keep user-typed text display-only, and **don't change any actual code** — just
produce findings. It also tells the user-experience agent to **recompute the colour-contrast
numbers itself**, because that's the one thing the previous round got wrong.

On top of those, a few conduct rules bind **every** agent, the manager, and the session driving the
run: **never make a hidden assumption** (if you must assume something, say so out loud and flag it);
**ask before you guess** — if you're less than ~95% sure what's wanted, stop and ask rather than
press on; surface disagreements instead of papering over them; **constructively challenge the
owner's own thinking and design choices** (offer alternative angles to illuminate, not to be
contrarian, and only raise an already-settled decision once, as a fresh lens); and stay within the
project's scope.

## A couple of practical safeguards

- Agents write into a **dated folder**, so a parallel run can't trample the existing reviews; the
  manager merges the new findings in deliberately.
- At launch you choose whether the agents do a **completely fresh** review (most independent, but
  more churn against decisions you've already accepted) or **refresh and reconcile** the existing
  ones (cheaper, respects what's settled) — the second is recommended.
- Each agent is told to report back **briefly** (its detailed findings go in its file), so the
  manager doesn't get flooded.

## How to start it

In a fresh session, say something like *"read `docs/REVIEW_ORCHESTRATION.md` and execute it,"*
confirm the run-mode choice and today's date for the run folder, and let it go.
