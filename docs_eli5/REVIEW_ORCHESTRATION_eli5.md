# Review Orchestration Brief — plain-English version

> Plain-language companion to [`REVIEW_ORCHESTRATION.md`](../docs/REVIEW_ORCHESTRATION.md). The
> original is the source of truth and is unchanged. If the two disagree, trust the original.

## What this is

A ready-to-go plan for re-running **all** the project's reviews using a team of AI assistants
("agents"), led by a dedicated **manager** agent that runs the whole job and pulls everything into a
single balanced action plan — instead of doing the reviews one at a time across many sessions, the
way they were built up until now.

The idea: open a **fresh** session (so there's plenty of working memory), point it at the original
brief, and let the manager run it.

## Who runs it: a dedicated manager agent

When you start the job, your session spawns **one manager agent**, and that manager then runs
everything itself — it brings in the reviewers, runs the debate, and writes the final plan. The
manager is the boss of the whole job from the start; your session just launches it and passes
messages between you and it.

**One honest caveat:** this is "an assistant that runs other assistants," and that kind of nesting
can sometimes hit limits. If the manager can't bring in its own helpers, the plan falls back to
**your session acting as the manager itself** (same role, same steps) — and it'll tell you which way
it actually ran rather than quietly switching.

**Who the manager "is."** It's told to act like a rare, top-tier all-rounder — an expert
**actuary, software developer, business strategist, and product designer all in one** — so it
judges every issue from all four angles. The aim is a plan that's **fair, practical, and genuinely
worth doing for a portfolio demo**, not over-engineered beyond what the project needs.

## The four phases (the debate only happens AFTER the solo reviews)

The manager runs the job in four steps, in order. The first two are done **in isolation** — each
reviewer works alone and sees nobody else's work. Nothing argues with anything until both solo
rounds are finished.

1. **Solo reviews.** Eight reviewers (security, cryptography, quality, legal, user experience,
   product, visual design, and a catch-all "other angles" review) each examine the code **on their
   own**, with no sight of each other, and write up their findings.
2. **Solo second opinions.** Eight "checker" reviewers each double-check **their own matching
   review only** — again alone, no debate yet — confirming, correcting, or refuting it and spotting
   anything missed.
3. **The debate (now, and only now).** With both solo rounds done, the manager runs the
   arguments: in each subject area it has the **reviewer and its checker hash out their
   disagreements**, and where two subject areas clash (say, tighter security vs. a simpler
   experience) it has **those two reviewers argue it out** too. It then settles each one and writes
   down *why*.
4. **The balanced action plan.** The manager takes the settled results and produces the final
   prioritised to-do list and plan — must-fix / should-fix / nice-to-have / accepted / false alarm —
   plus a short section of **challenges to your own thinking**. **Before it changes any of the main
   documents, it shows you the proposed plan and waits for your go-ahead** — only then does it
   update the to-do list, the plan, the plain-English versions, and the README's "Known
   limitations."

**How the "debate" actually works:** the helper agents can't talk to each other directly — they do
their bit and finish. So the manager acts as a go-between: it carries the checker's criticism back
to the original reviewer, gets the reply, carries it back again, and keeps going until it's resolved
— then makes the call. It's a real back-and-forth; the manager is just the messenger in the middle.

## The rules every agent (and the manager) must follow

The brief hands everyone the project's fixed decisions so nobody wastes effort re-arguing settled
points: no caps on number size, keep the "Simulated round" warning, never claim the signatures stop
impersonation, keep the app lightweight (no database, accounts, or heavy infrastructure), keep
user-typed text display-only, and **don't change any actual code** — just produce findings. It also
tells the user-experience reviewer to **recompute the colour-contrast numbers itself**, because
that's the one thing the previous round got wrong.

On top of those, a few conduct rules bind everyone — the helpers, the manager, and the session
running it: **never make a hidden assumption** (if you must assume something, say it out loud and
flag it); **ask before you guess** — if you're less than ~95% sure what's wanted, stop and ask;
surface disagreements instead of papering over them; **constructively challenge your thinking and
design choices** (offer alternative angles to illuminate, not to be contrarian, and raise an
already-settled decision only once, as a fresh lens); and stay within the project's scope.

## A couple of practical safeguards

- Reviewers write into a **dated folder**, so a parallel run can't trample the existing reviews; the
  manager merges the new findings in deliberately.
- **Isolation is enforced by what each agent is given** — a solo reviewer only gets its own task and
  the code; a checker only gets its own review. Nobody sees another's work until the debate phase.
- At launch you choose whether the agents do a **completely fresh** review (most independent, but
  more churn against decisions you've already accepted) or **refresh and reconcile** the existing
  ones (cheaper, respects what's settled) — the second is recommended.
- Each agent reports back **briefly** (its detailed findings go in its file), so the manager isn't
  flooded.

## How to start it

In a fresh session, say something like *"read `docs/REVIEW_ORCHESTRATION.md` and execute it."* The
original brief now opens with a **kickoff checklist** so a cold session knows exactly what to do.
In plain terms, it will:

1. **Ask you three quick things first** (it won't guess): refresh-and-reconcile vs. a fresh
   independent set; today's date for the run folder; and whether the final plan should update the
   main documents or sit in the run folder until you approve.
2. **Bring in the manager** to run the four phases.
3. **Pause and show you the plan** before changing any of the main documents — nothing canonical
   gets rewritten until you say yes.
4. **Commit and push** once you've approved.

So you can kick it off with one sentence and it'll walk you through the rest.
