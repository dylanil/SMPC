# QA / correctness review — plain-English version

> Plain-language companion to [`qa.md`](../docs/review/qa.md). The original is the source of
> truth and is unchanged. If the two disagree, trust the original. Finding codes (H1, H2, M1…)
> are kept for cross-reference.

## What this was

A "does it actually behave correctly?" check — edge cases, things that hang, confusing states,
and how the result is displayed. Not security or cryptography (those were reviewed separately).

## The two big problems (High)

**H1 — A participant's page can wait forever with no warning.** After submitting, a participant's
screen polls for the final result in an endless loop. If anyone else never shows up, or the
session expires, the page just sits on a reassuring-but-false *"Waiting for all shares to
land…"* forever. The aggregator page handles this exact situation gracefully (it shows "session
lost"), but the participant page was never given the same treatment. Since "someone doesn't show
up" is the most common real failure, this is the biggest credibility problem. The fix is
straightforward and the needed data ("3 of 5 in, waiting on B and D") is already available.

**H2 — Errors pop up as ugly raw text.** When something predictable goes wrong after you start
(for example, your slot was already taken), the polished step-by-step screen collapses into a
native browser pop-up showing raw server gibberish like `{"error":"share already committed…"}`.
The very first step (joining) has lovely friendly error messages — but everything after it was
left on the ugly fallback. The fix is to reuse the nice error handling that already exists.

## The medium issues

**M1 — A bad-digit submission wedges or desyncs the whole round.** (This is the QA angle on the
security team's M1.) A participant can submit a number using unusual digit characters that pass
the validation but then either crash the result for everyone, or produce an average that no
participant can reproduce. One person — honest-but-unlucky-locale, or malicious — can break the
round for everyone, with no error shown anywhere.

**M2 — The demo button gets stuck.** If the solo demo fails, its button stays permanently
greyed-out, and the error message tells you to "create a fresh session" — but you can't, without
reloading, which throws away the session. The recovery advice contradicts itself. Easy fix:
re-enable the button on failure.

## The small stuff (Low)

- **L1 — "-0" can appear.** A rounding quirk can display "-0" instead of "0" for tiny negative
  averages. Purely cosmetic.
- **L2 / L3 — Lenient input parsing.** A few odd typed values for the participant count are
  handled loosely on the page, but the server independently re-checks everything, so it's
  harmless.

## Things checked and found fine (the "N" notes)

The metric label is handled consistently (blank labels are hidden, not shown as an empty
"benchmarks:" tag), the demo's internal ordering is correct, the double-click guards work, and
the access log uses unambiguous UTC timestamps.

## The testing gap

The one automated test only runs a clean, successful round. It never checks the error paths,
the bad-digit case, the demo, the reload/expiry behaviour, or the result-formatting edge cases —
which is exactly where the two worst bugs (H1 and M1) live. The highest-value additions: a test
matrix for the error cases, and a test proving a malformed number is rejected cleanly instead of
crashing the round.

## What's solid

The core protocol works (rounds at 3 and 10 people pass, the maths cancels, the "first value
wins" rule holds), the participant-count validation is robust, the metric handling is clean, and
the aggregator's "session lost" detection has sensible debounce so it doesn't false-alarm.
