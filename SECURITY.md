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

## Reporting

There is **no formal vulnerability-disclosure process and no bug bounty** for this demo. If you spot something useful, please open a GitHub issue or pull request. For anything genuinely sensitive, contact the maintainer via the email on their GitHub profile rather than filing a public issue.

For the full threat model and privacy notes, see [`README.md`](README.md).
