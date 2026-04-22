# SMPC — Secure Average of Three Private Claims

A small demo of Secure Multi-Party Computation. Three insurers each enter one private number ("claim") from their own browser. A separate aggregator computes the average **without ever seeing any insurer's raw claim**. Security comes from *pairwise one-time-pad masking*: every pair of insurers shares a random mask that cancels out when all three masked shares are summed.

---

## Protocol

For every pair `(i, j)` with `i < j`, a 64-bit mask `r_ij` is **derived locally by both insurers** from an ECDH shared secret — neither sends the mask to anyone, and the coordinator never sees it. Each insurer then computes a local masked share:

```
s_A = x_A + r_AB + r_AC
s_B = x_B − r_AB + r_BC
s_C = x_C − r_AC − r_BC
```

Only `s_A`, `s_B`, `s_C` are sent to the aggregator. Every mask appears once with `+` and once with `−`, so:

```
s_A + s_B + s_C = x_A + x_B + x_C    (all masks cancel)
average         = (s_A + s_B + s_C) / 3
```

The aggregator learns only the sum (and therefore the average). Individual claims remain private.

Mask derivation uses **ECDH P-256 + HKDF-SHA256** in the browser:
- Each insurer generates an ECDH keypair locally; private keys never leave the browser.
- Each insurer publishes only their **public key** to the coordinator.
- For each pair, both parties run `ECDH(myPriv, theirPub)` to derive the same 32-byte shared secret, then expand it via HKDF (with a deterministic per-pair info string) into the 64-bit mask `r_ij`.
- The coordinator only ever sees public keys and masked shares — it cannot derive any mask, even in collusion with one insurer.

---

## Running it

Requires Python 3.7+ (uses only the stdlib).

```bash
python server.py
```

Then open each page in a **separate** browser tab or window:

| Role        | URL                                   |
| ----------- | ------------------------------------- |
| Home        | <http://127.0.0.1:8765/>              |
| Insurer A   | <http://127.0.0.1:8765/party/a>       |
| Insurer B   | <http://127.0.0.1:8765/party/b>       |
| Insurer C   | <http://127.0.0.1:8765/party/c>       |
| Aggregator  | <http://127.0.0.1:8765/aggregator>    |

The home page shows a 6-character **session code**. Each insurer and the aggregator must enter this code on their own page before submitting data or computing the average — it gates every data-bearing endpoint and prevents two rounds from accidentally cross-talking.

Each insurer enters their claim and clicks *Start Protocol*. Once all three have submitted, the aggregator page reveals the average.

To start a fresh round, click **Reset session** on the home page (this also rotates the session code).

### Deploying

The repo includes a `Dockerfile` and respects `HOST` / `PORT` env vars (defaulting to `0.0.0.0:8765`), so any container PaaS that injects `PORT` (Fly.io, Render, Cloud Run, Railway) will work out of the box. **Pin to exactly one always-on instance** — protocol state is in process memory, so autoscaling or scale-to-zero will break rounds in flight. Health-check path is `/healthz`.

---

## Project layout

```
SMPC/
├── server.py          # Python stdlib HTTP server: relays masks, collects masked shares
├── public/
│   ├── home.html      # Landing page with links to each role
│   ├── party.html     # Per-insurer page (served for /party/a, /party/b, /party/c)
│   └── aggregator.html
└── index.html         # Earlier single-page demo (kept as a reference)
```

### Server endpoints

All data endpoints require a `session` field (POST body) or `session=` query param matching the current session code; mismatches return `403`.

- `GET  /api/session` — current session code (used by the home page to display it; unprotected)
- `POST /api/verify` — verify a session code without side effects (`{session}` → `{ok}`)
- `POST /api/pubkey` — an insurer publishes its ECDH public key (base64 P-256, 88 chars)
- `GET  /api/pubkeys?for=X` — insurer `X` fetches the other two insurers' public keys
- `POST /api/share` — an insurer submits its final masked share
- `GET  /api/result` — aggregator retrieves masked shares and their sum (only once all three are submitted)
- `GET  /api/state` — public status (which insurers have submitted so far)
- `POST /api/reset` — clear all state for a new round and rotate the session code (returns the new code)
- `GET  /healthz` — unprotected liveness probe for platform health checks

---

## Security notes

This is an educational demo, not production-grade:

- **Mask derivation is end-to-end.** Each pair derives its mask via ECDH P-256 + HKDF-SHA256 in the browser; private keys never leave the browser, masks are never transmitted, and the coordinator only sees public keys and masked shares. A coordinator colluding with one insurer can no longer recover another insurer's input.
- **No authentication.** Anyone who can reach the server can claim to be any insurer (the 6-char session code is a low bar — fine for a demo over a private link, not for the open internet).
- **Fixed-point arithmetic** (×10⁶) is used so decimals work with BigInt on the client. Pick a scale that fits your expected range.
- **Collusion.** As with any pairwise-masking scheme, two colluding insurers (or an insurer colluding with the aggregator) can reconstruct the third insurer's input — this is inherent to 3-party additive secret sharing.
