# Security review — plain-English version

> Plain-language companion to [`security.md`](../docs/review/security.md). The original is the
> source of truth and is unchanged. If the two disagree, trust the original. Finding codes
> (M1, L1, N1…) are kept so you can look up the full technical detail.

## What this was

An authorised, hands-on security check of the app — reading all the code and then actually
attacking a running copy to see what holds. It's the author reviewing their own work honestly,
not an outside certification.

## The headline good news

The recently-added free-text "metric label" (the thing the aggregator types to describe what's
being measured) is shown on other people's screens, so the obvious worry was: could someone type
in malicious code that runs in another person's browser (an "XSS" attack)? The reviewer traced
every place that label gets displayed and confirmed it's always inserted as **plain text, never
as live HTML** — so the attack doesn't work. This was the highest-risk recent addition and it
was handled correctly.

## The one real bug worth fixing (M1)

There's a flaw in how the app validates submitted numbers. The check it uses treats certain
**non-standard digit characters** (like a superscript "²", or digits from other writing systems)
as valid numbers — but when the server later tries to actually add them up, it either:

- **Crashes that round permanently.** A character like "²" passes the check, gets stored, and
  then every attempt to compute the result crashes — and because the first value is locked in,
  the round is dead until it expires (30 min) or is reset. **Any single participant can do this
  with one well-formed submission**, breaking it for everyone.
- **Or silently desyncs.** Some foreign-script digits pass *and* get added up, so the aggregator
  shows an average — but every participant's own double-check fails, so the app's whole "verify
  it yourself" promise quietly breaks.

The fix is small: only accept plain ASCII digits, and reject the bad value the instant it's
submitted (plus a safety net around the totalling step). The reviewer rates this **Medium**; the
second opinion nudges it to **Medium-High**.

## The minor issues (Low)

- **L1 — Rate-limiting can be bypassed off the intended host.** The app identifies visitors by a
  trusted header that's only trustworthy on its specific hosting platform. If it were ever
  exposed directly, an attacker could fake a new identity per request and slip past the
  rate limits. Accepted for the intended setup; worth a one-line note in the README.
- **L2 — The same risky totalling line.** Related to M1: the place that adds up the numbers has
  no defensive guard. Already a documented accepted limitation; flagged again because it's the
  single riskiest spot.

## Everything that was tested and found solid (the "N" notes)

The reviewer specifically tried to break each of these and couldn't:

- **The aggregator password gate** held against every bypass attempt (empty password, forged
  cookie, missing credentials, etc.).
- **The proof-of-work puzzle** is properly enforced and can't be replayed or downgraded.
- **The tamper-proof tokens and "first-write-wins"** behave exactly as designed — you really
  can't rewrite your submission to steer the result.
- **No file-path trickery** works against the static-file routes.
- **Cheap checks run first** (size limit before authentication), so an unauthenticated flood gets
  shed early.
- **The logs leak nothing** — no tokens, no submitted values, no session codes.
- **Memory housekeeping** is done thoughtfully.

## Bottom line

The cryptography and the auth/anti-abuse machinery are genuinely well-built and resisted every
attack tried. The one thing actually worth fixing before showing it off is the bad-digit bug
(M1). The security posture does not over-claim — for example, it correctly does *not* pretend the
signatures stop impersonation.
