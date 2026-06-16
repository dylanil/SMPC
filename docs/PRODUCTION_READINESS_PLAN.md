# Production-Readiness Notes - SMPC Demo

This project is a credible public portfolio demo, not a commercial service. It intentionally
stays lightweight: one Python `http.server`, in-memory sessions, no database, no accounts, and
one pinned deployment instance.

## Current Status

The public demo has the main correctness, UX, and security-hygiene guardrails expected for its
scope:

- browser-side SMPC flow with ECDH + HKDF pairwise masks;
- ECDSA-signed pubkeys and shares;
- server-signed bearer tokens after invite redemption;
- first-write-wins semantics for joins, pubkeys, and shares;
- exact fixed-point decimal handling with BigInt in the browser and Python integers on the server;
- proof-of-work on session creation and join;
- per-IP rate limits on write endpoints;
- session and rate-counter cleanup;
- security headers for frame denial and MIME-sniffing defense;
- non-root container user;
- clear demo-only, privacy, and known-limitations copy.

## Deployment Posture

The app should run as exactly one always-on instance. Session state is in process memory, so
horizontal scaling, scale-to-zero, or overlapping rolling deploys can split or erase in-flight
rounds.

The Fly deployment is configured for a single pinned machine. `/healthz` is the unprotected
health-check endpoint.

For the public self-serve demo, leave both `SITE_PASSWORD` and `AGGREGATOR_PASSWORD` unset so
`/aggregator?demo=1` remains one-click. Use `SITE_PASSWORD` only as a temporary whole-site
private curtain, and use `AGGREGATOR_PASSWORD` only for private/coordinated deployments where
self-serve session creation should be blocked.

## Verification Gate

Run these against a freshly started local server:

```bash
python verify_round.py
python verify_round.py 10
python tests.py
```

Run the browser numeric contract tests without the server:

```bash
node tests_numeric.js
```

For UI-affecting changes, also run the README screenshot generator and inspect the generated
assets before committing.

## Non-Goals

Do not treat the following as accidental gaps:

- no persistence;
- no user accounts;
- no PKI or long-term participant identity registry;
- no input magnitude caps;
- no dropout resilience;
- no queue, database, Kubernetes, or observability platform.

Those are production features or heavier product choices, not requirements for this educational
demo.
