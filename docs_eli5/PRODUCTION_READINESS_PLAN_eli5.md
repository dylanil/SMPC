# Production-Readiness Plan — plain-English version

> This is a plain-language companion to [`PRODUCTION_READINESS_PLAN.md`](../docs/PRODUCTION_READINESS_PLAN.md).
> The original is the source of truth and hasn't been changed. This file just explains the
> same thing without assuming you know the technical details. If anything here and the
> original ever disagree, trust the original.

## What this document is for

We built a small web demo that does something genuinely clever: a group of people each type
in a private number, and the app works out the **average** of those numbers **without any
single computer ever seeing the individual numbers**. Think of a salary survey where everyone
learns the team average but nobody learns what anyone else earns.

This plan is the "are we ready to show this off?" checklist. The goal is **not** to turn it
into a product we sell. The goal is to make it a polished, trustworthy thing we can put in a
public portfolio and link from a CV — so it has to look finished and behave honestly, but it
doesn't need enterprise plumbing (no logins, no database, no big infrastructure).

Important: at the time this plan was written, **nothing had been fixed yet.** This is the
to-do list and the reasoning behind it. The actual fixing is a separate, approved step.

**Re-checked on 2026-06-13.** We ran the whole review process a second time — many independent
reviewers, each working alone, plus a second opinion on each. The verdict: the plan still holds,
nothing was overturned, and the to-do list and its order didn't change. (The new run is saved under
`docs/review/run-2026-06-13/`.)

**Then we started fixing — 2026-06-13.** Acting on the recommendation to do the cheap, important
fixes first, the whole "must-fix" batch plus two quick wins are now **DONE**: the weird-character
crash, the forever-frozen waiting screen, the ugly error pop-ups, the missing licence, the phone
layout, and the keyboard-focus outline (items RB-01, RB-02, RB-03, RB-04, RB-05, RB-11). They're
struck through and marked ✅ on the release board. Now the reviews can be shown off as "we found
problems **and fixed them**," which is far more impressive than just "we found problems."

Since then, most of the **should-fix** list landed too (2026-06-13): the "this is a demo"
disclaimers, the softened wording, the solo-visitor signpost, and the inline "don't change this"
code comments (RB-06 through RB-09, and RB-26). And the two "get it seen more widely" items (RB-10,
RB-35) are now **done** too: the README shows screenshots of a finished round, and pasting the link
unfurls into a proper preview card (title, description, and image) on LinkedIn/X/Slack/etc.

## How the thing is built (the 30-second version)

- **One small Python program** runs the whole back end. It's deliberately simple — one file,
  almost no external libraries.
- **Everything lives in memory.** There's no database. If you restart the program, all
  in-progress sessions vanish. That's on purpose — it keeps things simple and private.
- **Three web pages** make up the front end: a home page, a "participant" page (for the people
  entering numbers), and an "aggregator" page (for the person running the round).
- **The clever maths** that hides everyone's numbers happens inside the browser, not on the
  server. The server only ever sees scrambled numbers that cancel out to reveal the average
  and nothing else.
- **It's hosted on one always-on machine.** Because everything is in memory, we can't spread
  it across several machines — they wouldn't share state. One machine, always running.

There's a list of things we **deliberately chose not to build**: no saved data, no user
accounts, no heavyweight identity system, no limits on how big a number you can type, and no
handling for someone dropping out mid-round. These aren't oversights — they're conscious
trade-offs to keep the demo small. (The full list lives in the "Accepted" section of the
release board.)

## What "good enough to ship" actually means here

Five plain goals:

1. **Never lie to the user.** No screens that silently freeze forever, and no ugly raw error
   pop-ups when something predictable goes wrong.
2. **One troublemaker can't break it for everyone.** A single bad entry shouldn't be able to
   kill the whole round.
3. **Look finished and be honest.** Have a proper licence, work on phones, carry a clear "this
   is a demo" note, and don't over-promise in the wording.
4. **Win the first 30 seconds.** Both the live app and the GitHub page should impress someone
   quickly — including a way for a solo visitor to see it work without rounding up friends.
5. **Don't break what's already good.** The maths is sound, it's honest, and it's lightweight.
   Improve the rough edges without spoiling those strengths.

## How we checked the work

We ran **seven separate "reviews,"** each looking at the project from a different angle:
security, the cryptography/maths, quality & correctness, legal/licensing, user experience,
product/viability, and visual design. Then we ran **a second independent opinion on each one**
to catch mistakes. (One of those second opinions did catch a genuine error — a colour-contrast
calculation that was wrong — which is exactly why double-checking was worth it.) The most
important conclusions, the maths and the security, survived this double-checking.

All the individual findings are collected and prioritised in the **Release Board** (see
[`RELEASE_BOARD_eli5.md`](RELEASE_BOARD_eli5.md) for the plain-English version). This
plan is just the strategy wrapper around that board.

## The rules we're holding ourselves to

- **Don't touch the code until each fix is approved.** This is a plan, not a change.
- **Keep it lightweight.** No database, no accounts, no big frameworks, no rewrite. The simple
  one-file server stays simple.
- **Respect the owner's fixed decisions**, e.g. no caps on number size, keep the "Simulated
  round" warning on the solo demo, and never claim the signatures stop someone impersonating a
  participant (they don't — see the board).
- **Small, well-described commits**, one change at a time, each explaining *why*.
- **The automated check must keep passing** after every change — it's the safety net that
  proves the maths still cancels out correctly.
- **Any text shown on screen must be handled safely** so it can't be used to sneak in
  malicious code.

## The safety check every fix must pass

Before any fix counts as "done," it has to clear this gate:

1. The **automated round-trip test** passes for both small and large groups (it proves the
   scrambled numbers still cancel exactly).
2. A **new test** that proves a deliberately-broken entry gets rejected cleanly instead of
   crashing the round.
3. A **manual walk-through** of all three flows: a real multi-person round, the solo demo, and
   a round with no metric label — plus a check of the specific thing the fix was about.
4. A check that **only the intended files changed**, and that the sensitive shared-maths file
   wasn't touched (it almost never should be).
5. A **phone spot-check** once the mobile fix is in, to confirm pages render properly on a
   phone instead of looking like a shrunk-down desktop.

## How we rank the work

- **P0 — must fix before showing anyone.** The demo breaks, lies, or is trivially spoilable;
  or it's a near-free fix whose absence makes it look unfinished.
- **P1 — should fix before sharing widely.** Clearly improves trust, usability, or mobile, but
  the demo still works without it.
- **P2 — nice to have.** Polish, deeper accessibility, the visual-design pass, more tests, and
  hardening for situations this demo doesn't actually run in.
- **Accepted / out of scope.** Deliberate design choices — don't "fix" them.
- **False positive.** Things a review flagged that turned out to be wrong — recorded so nobody
  accidentally "fixes" a non-problem.

The current tally: **4 must-fix, several should-fix, a stack of nice-to-haves, around ten
accepted trade-offs, and four false alarms.**

## The order we'll do it in

1. **First batch — correctness and blockers. ✅ DONE (2026-06-13).** Stopped the bad-entry crash,
   stopped the forever-frozen screen, replaced the ugly error pop-ups with friendly inline messages,
   added the licence, and added the one-line mobile fix.
2. **Second batch — credibility and first impressions. ✅ MOSTLY DONE (2026-06-13).** ~~Added the
   "this is a demo" note and tidied the over-strong wording~~ ✅; the "what this is / isn't" content
   was already covered ✅; ~~added a signpost so solo visitors can see it work~~ ✅; ~~fixed
   keyboard-focus visibility~~ ✅; ~~added screenshots to the README~~ ✅. (This whole batch is done.)
3. **Third batch — polish, hardening, and tests. ✅ DONE (2026-06-13), except the visual redesign.**
   All the quick wins shipped (the slow-request timeout, the extra protective header, the small UI
   fixes, the secure-connection guard, the pinned dependency, the security-contact file, and a proper
   test suite). The bigger **"make it not look vibe-coded" visual redesign (RB-18)** is **done** — it went through the
   review-council and then a look-at-the-screens session, landing on a **black + orange** scheme with
   GitHub-style fonts (a custom font and fancy motion were skipped as not worth it).
4. **Re-deploy** once the must-fixes are in and the safety gate is green, then re-test against
   the live site.
5. **"Going public" extras — written down on 2026-06-13, not scheduled yet.** These came up when
   thinking about sharing the demo *widely* with the public (rather than inviting a few people).
   They're logged on the board (items RB-35 to RB-40) so they can be prioritised together in a
   future planning round, not grabbed at random:
   - **RB-35** a proper "share preview" so the link looks good when posted (cheapest win).
   - **RB-36** a simple uptime alert so you know if the site goes down.
   - **RB-37** a quick load test to learn how much traffic it can handle.
   - **RB-38** decide what to do about offensive text in the free-text label (probably accept).
   - **RB-39** an actual screen-reader/keyboard accessibility check (so far only reasoned, not run).
   - **RB-40** a one-line privacy/cookie note for public users.

Accepted items get at most a note in the docs; false positives get nothing. Nothing in this
plan adds a database, accounts, or any of the heavy infrastructure we deliberately skipped.
