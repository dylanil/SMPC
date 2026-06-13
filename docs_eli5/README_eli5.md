# Project README — plain-English version

> Plain-language companion to the repo's [`README.md`](../README.md). The original is the
> source of truth and is unchanged. If the two ever disagree, trust the original.

## What this project is

A demo of **Secure Multi-Party Computation (SMPC)**. Between 3 and 10 people each type one
private number into their own browser. A separate "aggregator" works out the **average** of
those numbers **without ever seeing any individual number**.

The trick that makes this possible is called **pairwise masking**, and the everyday version of
it is simple: every pair of participants secretly agrees on a random "fudge" number. One person
in the pair adds it to their figure, the other subtracts it. When all the fudged numbers are
added up, every fudge cancels out — so the total (and therefore the average) is exactly right,
but no single fudged number tells you anything about the real figure behind it.

## How a round works, in plain steps

1. The aggregator opens their page, optionally types a label for what's being measured (the
   example is "Average claim severity (£)" — competing insurers privately comparing claim
   costs), picks how many people will take part, and clicks **Create session**.
2. The system produces one 6-character session code and one personal invite per participant.
   The aggregator sends each person their invite privately (Slack, email, etc.). Each invite
   is tied to a specific slot, so you can't use someone else's.
3. Each participant opens their page, enters their invite and their private number, and clicks
   **Start**. The browser does the masking maths automatically.
4. Only the fudged ("masked") numbers are ever sent to the server. Once everyone's in, each
   participant's own page re-adds the masked numbers to double-check the total, and the
   aggregator shows the average.

## Trying it on your own

After creating a session, the aggregator page has a **"Demo: simulate all participants in this
tab"** button. It plays every participant's part inside one browser tab over the real
protocol, so a single visitor can watch a whole round. The page is honest that this mode has
**no privacy** (one tab obviously knows every number — which is why it can show a "reveal" card
that a real round never could) and that running the demo uses up all the invites, so you make a
fresh session for real participants.

## Running it yourself (for developers)

It needs Python 3.7+ and one library (`cryptography`). Install it, run `python server.py`, then
open the home page, the participant pages, and the aggregator page in separate browser tabs.
The README lists the exact URLs.

## Locking down who can create sessions

You can optionally set a shared password (the `AGGREGATOR_PASSWORD` setting). When it's set,
the aggregator page and the create/delete actions are all password-protected, so casual
visitors can't even see the aggregator screen. Participants never need this password — they're
gated by their personal invite instead. Left unset, everything is open, which is fine for local
testing. The README notes this is a single shared password with no per-person tracking; for
real access control you'd put the whole app behind a proper identity service.

## Deploying it

There's a ready-made container setup, and it works on common hosting platforms. **One important
rule:** run exactly one always-on instance. Because all the state lives in memory (no database),
spreading it across multiple machines or letting it scale to zero would break rounds that are in
progress. There's also an optional section on putting Cloudflare and a custom domain in front
for a nicer URL and some extra protection.

## The honest security notes (what it does and doesn't protect)

The README is candid that this is an **educational demo, not a production system**. The key
points in plain terms:

- **The masking is genuinely end-to-end.** The private "fudge" numbers are worked out inside
  each browser and never sent anywhere; the server only ever sees the masked numbers and some
  public keys. Even if the aggregator teamed up with one participant, they couldn't recover
  someone else's number.
- **Layered identity checks.** A personal invite gets you into your slot; then the server hands
  you a tamper-proof token; then every submission is digitally signed, so others can verify it
  and catch a dishonest aggregator. And **the first value you submit is locked in** — you can't
  wait to see everyone else's numbers and then change yours to skew the average.
- **Defensive extras:** the container runs as a non-admin user, a header blocks the page from
  being embedded in a malicious site, there are per-visitor rate limits and a small
  "proof-of-work" puzzle to deter flooding, and old sessions are auto-deleted.

It's also honest about the limits:

- **Signatures don't stop impersonation.** Because identities are created fresh per session in
  the browser, someone who intercepts an invite and races to claim the slot first can pose as
  that participant convincingly. Closing this would need a proper pre-established identity
  system — out of scope.
- **No limit on how big a number you can submit.** A participant could drag the average with a
  huge value; signatures prove *who* submitted, not whether the number was reasonable.
- **It trusts participants to enter their own real number** — nothing forces honesty about your
  own figure.
- **Collusion has a floor:** in any scheme like this, enough people working together (or one
  plus the aggregator) can deduce a remaining person's number. This is inherent, and documented.
