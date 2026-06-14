# Security Policy

This is an educational **demonstration project**, not a production or commercial service. It runs
as a single in-memory instance and has known, documented limitations — see *Security notes* and
*Known limitations* in [`README.md`](README.md), and the self-review in [`docs/review/`](docs/review/).

## Reporting

There is **no formal vulnerability-disclosure process and no bug bounty** for this demo. If you spot
something interesting, please open a GitHub issue or a pull request. For anything you'd consider
genuinely sensitive, contact the maintainer via the email on their GitHub profile rather than filing
a public issue.

## Scope and known limits

The cryptographic plumbing (pairwise ECDH + HKDF masking, ECDSA-signed shares) is a faithful demo of
the mechanics; it is **not** a hardened product. Two limits in particular are accepted and documented,
not bugs to report:

- **Impersonation race** — identities are generated per session in the browser, so there is no
  long-term trust anchor; an interceptor who claims an invite first can pose as that participant.
- **Collusion bound** — enough colluding participants (or one plus the aggregator) can reconstruct an
  honest participant's input, inherent to pairwise masking.

See the README for the full list.
