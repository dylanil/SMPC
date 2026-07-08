# Security Policy

Cravage (a **cr**yptographic **av**er**age**) is an educational **demonstration project**, not a production or commercial service. It computes a group average without pooling raw figures (under the hood, secure multi-party computation). The security goal is narrow: show the mechanics of secure aggregation honestly, with the important limits visible.

## What This Demo Protects

- Raw participant figures are parsed and masked in the browser; they are not sent to the server.
- Pairwise masks are derived locally with ECDH P-256 + HKDF-SHA256 and are never transmitted.
- The server receives public keys, signed masked shares, session metadata, and the final sum/average.
- Every share is ECDSA-signed, server-verified, and returned with its signature and verifying key so participants can independently re-check the result.
- First-write-wins prevents a participant from replacing their key or share after seeing other submissions.

## Known Limits

These are accepted demo boundaries, not vulnerabilities to report:

- **No identity anchor.** Invite tokens bind a browser session to a party slot, but there is no long-term participant identity or key registry. An interceptor who claims an invite first can impersonate that party.
- **No input honesty guarantee.** A participant can enter any value, including a very large one. The app deliberately has no figure cap and no range proofs.
- **Collusion is possible.** Enough colluding participants, or a participant plus the aggregator, can reconstruct another participant's input. This is inherent to the simple pairwise-mask design.
- **The aggregate can still be sensitive.** SMPC hides individual inputs, but it does not automatically make the final average non-sensitive. Small groups, repeated overlapping rounds, or prior knowledge can leak information through the statistic itself.
- **All parties must finish.** There is no dropout recovery or threshold reconstruction.
- **Single in-memory instance.** Sessions vanish on restart and cannot be horizontally scaled.
- **A session code is a read-and-reset capability.** Anyone who holds a code can observe the round's public state (status, masked shares, the final sum - never raw figures) and, unless the deployment sets `AGGREGATOR_PASSWORD`, delete the session via `/api/reset`. Codes are random six-character values with a 30-minute lifetime; share them like the invites they accompany.
- **Read endpoints are deliberately un-throttled.** `/api/state`, `/api/result`, and `/api/pubkeys` are polled sub-second by every page in a round, so they carry no rate limit. Guessing a live code by scanning is astronomically unlikely within a session's lifetime, and the prize would be the metadata above, not raw figures.
- **No certification.** This is not an independent third-party security audit.

## What If Someone Cheats?

The same limits, retold as attack scenarios: what each attempt looks like, what the design
catches, and what is deliberately out of scope.

- **The aggregator (or server) forges a share.** Caught - by the participants. Every share is
  ECDSA-signed and verified at write time, and first-write-wins locks it in; `/api/result` then
  returns each share with its signature and verifying key, and every participant's page
  re-verifies all of them. A forged share fails those checks even when the forged sum is kept
  self-consistent. The catch depends on participants actually re-verifying - which is why
  verification is built into the participant page rather than left as an exercise.
- **The aggregator misreports the average.** Caught - by recomputation. Anyone holding the
  session code can re-derive the sum and average from the masked shares in `/api/result`, so the
  aggregator's headline number carries no authority.
- **A participant lies about their figure.** Not caught, deliberately. There are no range proofs
  and no figure caps; a signature proves who submitted a share and that nobody else altered it,
  not that the figure is truthful or reasonable.
- **Someone steals an invite.** Depends who joins first. Invites are one-shot: once the intended
  participant has joined, the stolen invite is dead. A thief who joins *first*, though, claims
  the slot completely - their signatures verify cleanly from then on, because there is no
  long-term identity anchor to check a newcomer against. Signed shares do not stop impersonation.
  (A session *code* is a lesser, separate capability: it lets a holder watch the round's public
  state and, when no aggregator password is set, delete the session - see the Known Limits bullet
  above.)
- **Participants collude.** Privacy has a floor. N−2 colluding participants - or fewer, if the
  aggregator colludes too - can reconstruct an honest participant's figure from what they jointly
  know. In a 3-party round, any two participants can recover the third's figure exactly.
- **Someone drops out.** The round stalls; nothing is revealed, but nothing completes either.
  There is no dropout recovery or threshold reconstruction - create a fresh session.
- **The same group runs repeated or overlapping rounds.** Differencing the aggregates can isolate
  an individual or a subgroup. Nothing in the demo prevents it - one reason the final statistic
  itself must be treated as sensitive.
- **Nobody cheats at all - what does the average still reveal?** Possibly plenty. SMPC hides the
  inputs, not the output: in a small group, or against prior knowledge, the average alone can
  narrow an individual figure sharply.

## Reporting

There is **no formal vulnerability-disclosure process and no bug bounty** for this demo. If you spot something useful, please open a GitHub issue or pull request. For anything genuinely sensitive, contact the maintainer via the email on their GitHub profile rather than filing a public issue.

For the full threat model and privacy notes, see [`README.md`](README.md).
