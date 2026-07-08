# Changelog

Notable changes that affect the public demo, threat model, or operator workflow.

## 2026-07-08 - Take the evidence home

- **Round transcript download + offline verification.** Every completed round's result card now
  offers **Download transcript (JSON)** - the round's public evidence (masked shares, signatures,
  verifying keys, sum, stated average), built entirely client-side from data the server already
  publishes to any session-code holder. A new `python verify_round.py --transcript <file>` mode
  re-verifies every signature and recomputes the sum and displayed average offline, with no server
  running and no trust in the page. The test suite pins the transcript shape and confirms a forged
  self-consistent share fails the signature check.
- **"What If Someone Cheats?"** - SECURITY.md now retells the Known Limits as attack scenarios
  (forged share, misreported average, lying participant, stolen invite, collusion, dropout,
  repeated rounds, aggregate sensitivity), each stating what the design catches vs what is out of
  scope.
- **Copy honesty + real-round guidance.** The solo-demo watch guide no longer claims masked shares
  "look unrelated to the inputs" (falsifiable at extreme figure scales); the aggregator's invite
  card now explains how to run a real multi-device round (QR flow, everyone must finish, phones
  need the deployed HTTPS site) with the test-figures warning alongside.

## 2026-06-15 - Practical portfolio cleanup

- **Exact browser decimals.** Participant figures are now parsed as plain ASCII decimal strings directly into the `1e6` BigInt fixed-point representation. The UI rejects exponent notation, commas, `Infinity`, blank input, and non-ASCII digits instead of letting browser `Number` parsing quietly round or normalize them. Display of sums and averages now formats from BigInt too.
- **One-click solo demo.** `/aggregator?demo=1` creates a default 3-party session and runs the in-tab simulator automatically. The normal aggregator flow and the amber simulated-round warning remain unchanged.
- **Shared visual contract.** The common palette, focus ring, reduced-motion rule, honesty panel styles, and disclaimer style now live in `public/static/theme.css`; page-specific layout CSS stays inline.
- **Layered demo boundaries.** The public warning copy uses concise "test figures only" warnings near actions, contextual limitations in the "About this demo" blocks, a compact as-is footer, and a short privacy/cookie note. The generated README screenshots were refreshed from the real solo-demo flow.

## Earlier hardening and UX pass

- **Optional aggregator password.** Set `AGGREGATOR_PASSWORD` and the `/aggregator` page itself goes behind a browser auth dialog (HTTP Basic Auth). Casual visitors cannot see the form, and only people who hold the password can mint or wipe sessions. Leaving the variable unset keeps everything open, which is fine for local dev and the public demo.
- **Browser-friendly auth bridge.** After the auth dialog accepts, the server hands the browser a signed cookie. Subsequent API calls ride that cookie automatically; there is no JS-side password handling. The cookie key is derived from the password itself, so cookies survive server restarts but invalidate when the password rotates.
- **Auto-retry on stale proof-of-work.** If a tab is backgrounded while mining a PoW puzzle, the client silently fetches a fresh puzzle and retries once instead of failing the request outright.
- **Status-aware join errors.** The participant page surfaces concrete next steps for expired sessions, claimed slots, rate limits, bad requests, and network errors.
- **Aggregator session-lost detection.** The aggregator reports a likely lost or expired in-memory session after a few seconds of sustained 403s, while tolerating single-blip routing or timing failures.
- **Memory-hygiene sweeps.** The per-IP rate-counter map and proof-of-work used-challenge tracker are swept by the session-reaper thread so stale entries do not accumulate indefinitely.
- **Clickjacking defence.** Every response carries `X-Frame-Options: DENY`.
- **MIME-sniffing defence.** Every response carries `X-Content-Type-Options: nosniff`, and static image/script/CSS content types are explicit.
- **Non-root container.** The Docker container creates a regular `app` user (uid 1000) and switches to it before launching the server.
