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

Requires Python 3.7+ and `cryptography` for ECDSA P-256 signature verification.

```bash
pip install -r requirements.txt
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

The aggregator opens their page and clicks **Create session** — the server mints a unique 6-character session code plus three per-party invite tokens and returns one combined invite per insurer in the form `SESSION-TOKEN`. The aggregator shares each invite with its matching insurer out-of-band (Slack, email, etc.) — each code is bound to a specific role, so an insurer holding A's invite cannot claim slot B. Each insurer enters their invite on their own page before submitting a claim.

Each insurer enters their claim and clicks *Start Protocol*. Once all three shares have been submitted, each insurer's page independently recomputes the sum from the three public masked shares (a quick cross-check against the aggregator), and the aggregator page reveals the average.

To abandon an in-flight round, reload the aggregator page and create a new one; old sessions live in memory until the server restarts.

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

An insurer's first POST is `/api/join` with `(session, party, token, vk)` — they redeem their invite token and register their ECDSA verifying key. The server returns a server-signed bearer token (HMAC-SHA256 over `{session, party, vk, exp}`). All subsequent party-scoped POSTs carry that bearer token plus an ECDSA signature over a canonical `<action>|<session>|<party>|<content>` message; the server verifies its own HMAC, extracts the registered vk, and verifies the share/pubkey signature against it. Read-only observation endpoints require only a `session=` query param. POSTs with `Content-Length > 16 KB` return `413`.

- `POST /api/session/new` — mint a new session and return `{code, tokens: {A, B, C}}` (aggregator; unprotected, no body)
- `POST /api/join` — redeem an invite, register a signing vk, receive a bearer token (`{session, party, token, vk}` → `{server_token}`)
- `POST /api/pubkey` — publish an ECDH public key, signed (`{server_token, pubkey, sig}`)
- `POST /api/share` — submit a final masked share, signed (`{server_token, share, sig}`)
- `GET  /api/pubkeys?for=X&session=...` — insurer `X` fetches the other two insurers' ECDH pubkeys
- `GET  /api/result?session=...` — masked shares + their signatures + the registered vks + the sum, once all three are in. The aggregator and the insurers both use this to recompute the sum AND independently verify each share's signature
- `GET  /api/state?session=...` — which insurers have submitted so far in this session
- `POST /api/reset` — delete the given session (`{session}`); useful for abandoning a round
- `GET  /healthz` — unprotected liveness probe for platform health checks

---

## Security notes

This is an educational demo, not production-grade:

- **Mask derivation is end-to-end.** Each pair derives its mask via ECDH P-256 + HKDF-SHA256 in the browser; private keys never leave the browser, masks are never transmitted, and the coordinator only sees public keys and masked shares. A coordinator colluding with one insurer can no longer recover another insurer's input.
- **Per-party invite tokens** redeemed at `/api/join` gate which party slot a request can claim.
- **Server-signed bearer tokens** (HMAC-SHA256) committing to `(session, party, vk)` replace the raw invite for subsequent POSTs. Tamper-proof and stateless: the server re-verifies its own HMAC instead of remembering tokens.
- **ECDSA P-256 signed shares.** Every `/api/pubkey` and `/api/share` POST carries a signature over `"<action>|<session>|<party>|<content>"`. The server verifies it against the vk registered at `/api/join`. `/api/result` returns each share's signature and vk so the aggregator and other insurers can independently re-verify and recompute the sum — a dishonest aggregator can be caught.
- **Honest limitation: signed shares do NOT close the impersonation race.** vks are generated per-session in the browser. An attacker who intercepts an invite and races the legitimate insurer to `/api/join` registers their own vk; subsequent signatures verify cleanly. Closing this gap requires a long-term per-insurer key registry (or two-channel delivery, or federated identity) that binds vk to insurer identity *before* the session begins. Not implemented here.
- **Unbounded share magnitude.** `/api/share` accepts any decimal string — nothing caps the number. A malicious or buggy insurer can drag the average by submitting a huge value. Signatures don't help: they only prove who submitted, not what was reasonable.
- **No party-identity authentication beyond the token.** A legitimate holder of an invite token is still trusted to honestly submit *their own* claim — the protocol doesn't prevent an insurer from entering whatever number they like as `x_i`.
- **Fixed-point arithmetic** (×10⁶) is used so decimals work with BigInt on the client. Pick a scale that fits your expected range.
- **Collusion.** As with any pairwise-masking scheme, two colluding insurers (or an insurer colluding with the aggregator) can reconstruct the third insurer's input — this is inherent to 3-party additive secret sharing.
