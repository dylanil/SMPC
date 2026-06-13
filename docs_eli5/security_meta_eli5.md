# Security review — second opinion — plain-English version

> Plain-language companion to [`meta/security.md`](../docs/review/meta/security.md). The original
> is the source of truth and is unchanged. If the two disagree, trust the original.

## What this is

An independent double-check of the [security review](security_eli5.md) — someone re-ran the
attacks themselves to confirm the findings were real and not over- or under-stated.

## The verdict

**Trustworthy and well-calibrated.** Every headline claim reproduced exactly, including the
subtle ones. No false alarms. The reviewer would nudge the main bug (the bad-digit DoS) from
"Medium" up to "Medium-High," because a single participant can permanently kill a round at zero
cost with one well-formed request — but either rating is defensible.

## What it confirmed

- **The bad-digit bug (M1)** — reproduced end-to-end, exactly as described.
- **The rate-limit bypass (L1)** — reproduced in full (70 fake identities all slipped through).
- **The "all clear" items** — the password gate, the proof-of-work puzzle, the tamper-proof
  tokens, the "first value wins" rule, the file-routing safety, and the leak-free logging were
  all independently re-tested and held.
- **The metric label is safe** from code-injection — re-traced and confirmed.

## What the first review missed (the new finding)

**NEW-1 — A "slowloris" flooding weakness.** An attacker can open a connection, claim it's
sending data, and then just... not — tying up the server's resources indefinitely while it waits.
Because the server sets no time limit on reading a request, and spawns a new worker per
connection, many such stalled connections could exhaust it. This sidesteps the size limit, the
proof-of-work, and the rate limits. It's **Low risk on the intended hosting** (the platform's
edge absorbs much of it) but **Medium if exposed directly.** Easy fix: set a read timeout. This
is the most important thing the first review didn't catch.

There's also a minor, by-design note (NEW-2) that unauthenticated requests can use up the
session-creation rate budget — defensible, just worth knowing.

## Bottom line

The security review is reliable enough to act on as-is; just add the slowloris finding to round
it out.
