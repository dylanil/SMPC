# Production-Readiness Plan — SMPC demo

**Purpose.** Move this educational, browser-based SMPC demo *closer to production-ready*
without turning it into an enterprise system. It stays a lightweight, no-database,
no-account demo. This document is the strategy wrapper; the per-finding triage lives in
[`docs/review/RELEASE_BOARD.md`](review/RELEASE_BOARD.md), which is the single source of
truth for what to fix and in what order.

**Status: planning only — no application code has been changed.** Remediation is a separate,
approved step that follows this plan.

---

## 1. Current architecture summary

A secure multi-party **average**: N participants (3–10) each submit one private number; a
separate aggregator computes only the average, via pairwise ECDH+HKDF masks that cancel, so
no raw figure crosses the wire and every participant can independently re-verify the sum and
all signatures.

- **Backend:** one single-file Python `http.server` (`server.py`), standard library only,
  plus one dependency (`cryptography>=42.0`) for ECDSA P-256 verification. No framework, no
  database, no message queue.
- **State:** entirely in process memory, keyed by 6-char session code; reaped on a TTL
  (~30 min) by a daemon thread. Sessions never share state. Restart wipes everything — by
  design.
- **Frontend:** three self-contained HTML pages (`public/{home,party,aggregator}.html`),
  each with its own inline `<style>` and inline JS, plus two shared static modules
  (`public/static/smpc-core.js` — protocol crypto; `pow.js` — proof-of-work miner).
- **Identity / integrity stack:** per-party invite token → server-signed HMAC bearer token
  → ECDSA-signed pubkeys/shares → first-write-wins per slot. Proof-of-work gates session
  creation and join; per-IP sliding-window rate limits; optional shared aggregator password.
- **Deployment:** Docker (`python:3.11-slim`, drops to non-root uid 1000) on fly.io
  (`fl-wg-smpc`, region `lhr`), **single pinned always-on machine** (`auto_stop_machines =
  false`, `min_machines_running = 1`) because in-memory state can't autoscale; `force_https`;
  `/healthz` check.
- **Deliberate non-goals (do not "fix"):** no persistence, no user accounts, no PKI/identity
  proxy, no input magnitude caps, no dropout resilience. These are documented design
  boundaries, not omissions — see the Accepted section of the board (AC-01…AC-10).

## 2. Release-readiness goals

The bar is a **credible public portfolio demo**, not a commercial product. Concretely:

1. **Don't lie to the user.** No silent forever-hangs or raw error modals on the common
   failure paths (RB-02, RB-03).
2. **One bad actor can't wedge everyone.** A single malformed share must not kill a round
   (RB-01).
3. **Presentable & honest at the surface.** Licensed, mobile-renderable, with a disclaimer
   and accurate (non-over-claimed) copy (RB-04, RB-05, RB-07, RB-08).
4. **Win the 30-second first impression** — both the running app (solo-demo signpost) and the
   GitHub repo page (screenshot, the review folder as a signal) (RB-09, RB-10).
5. **Keep what's already good:** correct crypto, independent verifiability, honest docs,
   defensive hardening, the lightweight architecture. Improve without regressing these.

## 3. Review dimensions run

Seven independent review dimensions, each with an independent second opinion, all in
[`docs/review/`](review/): **security**, **crypto/SMPC soundness**, **QA/correctness**,
**legal/licensing**, **UI/UX**, **product/viability**, **front-end graphics**. The second
opinions (`docs/review/meta/`) validated findings against the code and, in one case, caught
and refuted a review error (the WCAG contrast math). The load-bearing claims — crypto
soundness and the security posture — held up under independent re-derivation and live
testing.

## 4. Findings format

All findings are consolidated in the release board with nine fields each: **ID · Source ·
Severity · Title · Evidence (file:line) · Why it matters · Minimal fix · Confidence · Needs
code change**, grouped into P0 / P1 / P2 / Accepted / False-positive. The board applies the
meta-review corrections (e.g. RB-01 raised to Medium-High; the contrast claims refuted to
FP-01/FP-02). Do not re-derive findings here — cite the board ID.

## 5. Implementation rules

- **Review-only until each item is approved for remediation.** This phase changed no
  application code.
- **Preserve the architecture:** no database, no accounts, no OAuth, no queues, no
  Kubernetes, no observability platform, no rewrite. Standard-library single-file server
  stays; one dependency stays.
- **Owner-fixed constraints:** no share/figure magnitude caps (AC-01); keep the solo-demo
  amber "Simulated round" warning; never claim signatures stop real-world impersonation
  (AC-02).
- **One change per commit**, with a short imperative subject explaining the *why*; update
  `CLAUDE.md` in the same commit for any load-bearing change.
- **`verify_round.py` must stay green** (N=3 and N=10) after every change; extend it
  alongside the RB-01 fix (RB-19).
- **Security of new copy:** any user-or-aggregator-supplied string stays `textContent`-only,
  never `innerHTML` (the metric-XSS discipline must not regress).
- **The owner runs `git push`** (`! git push`) — agent pushes are blocked by the credential
  manager.

## 6. Test / verification gate

Every remediation change must pass this gate before it's considered done:

1. **`python verify_round.py` and `python verify_round.py 10`** both PASS (masks cancel
   exactly) — the wire-contract regression guard.
2. **New error-path assertion** (ships with RB-01): a malformed/non-ASCII-digit share is
   rejected at `/api/share`, and `/api/result` never crashes (RB-19).
3. **Manual click-through** of the three flows on a local `python server.py`: a full real
   round (3 tabs + aggregator), the solo demo (banner + reveal render), and a metric-less
   round — plus the specific failure the change targets (e.g. for RB-02, abandon a round and
   confirm the party page now reports "session lost" instead of hanging).
4. **`git status`** shows only intended files changed; `git diff` of `public/static/smpc-core.js`
   stays empty unless a change is explicitly a protocol change (it should not be for any
   board item).
5. **Mobile spot-check** after RB-05: the pages render at device width, not zoomed-out
   desktop.

## 7. Prioritisation framework

- **P0 — must fix before public demo.** Release-blocking: the demo breaks, lies to the user,
  or is trivially griefable; or a near-zero-cost item whose absence reads as unfinished.
- **P1 — should fix before wider sharing.** Materially improves credibility/usability/mobile
  but the demo is functional without it.
- **P2 — nice to have.** Polish, deeper a11y, the visual-craft pass, test coverage, extra
  hardening for deployment modes this demo doesn't use.
- **Accepted / out of scope.** Deliberate design boundaries; do not action (some warrant a
  documentation note, not code).
- **False positive / no action.** Findings refuted or corrected on audit; recorded so they
  aren't mistakenly actioned.

The board is the instance of this framework: **P0 ×4, P1 ×7, P2 ×14, Accepted ×10, FP ×4.**

## 8. Proposed order of work

Each step is its own commit (or small commit series) and must clear the §6 gate. Re-run
`verify_round.py` after every server-side change.

1. **P0 batch — correctness & blockers.**
   1. **RB-01** harden share validation (ASCII-only at `/api/share` write time + guard the
      result-time sum) — *and ship the RB-19 error-path test in the same change*, since it's
      the regression guard for exactly this bug.
   2. **RB-02** port session-lost detection + progress to the party page.
   3. **RB-03** replace the post-join `alert()` with inline status-aware errors.
   4. **RB-04** add the MIT `LICENSE`. **RB-05** (viewport meta) rides along here — it's a
      one-line-per-file change and trivially low-risk.
2. **P1 batch — credibility & surface.** RB-08 disclaimer + RB-07 claim hedge (do them
   together so UI and README agree); RB-06 README threat-model section; RB-09 solo-demo
   signpost; RB-11 `:focus-visible`; then RB-10 (README screenshot/GIF + surface the
   `docs/review/` folder) once the above are in so the captured screenshots show the
   improved UI.
3. **P2 batch — polish, hardening, visual craft.** Quick wins first (RB-16 read timeout,
   RB-17 nosniff, RB-12/RB-22/RB-24 small UI fixes, RB-13/RB-14/RB-15, RB-20, RB-21, RB-23,
   RB-25-as-hint-only); then the **RB-18 visual-craft pass** as its own focused series
   (tokens → favicon/identity → OKLCH colours → mono → depth/motion/icons), each a small
   commit, since it's the largest and most subjective bucket.
4. **Re-deploy** (`fly deploy`) once P0 (and ideally P1) are merged and the gate is green;
   re-run the click-through against production.

Accepted items get at most a documentation note (RB-06, RB-08, RB-23, and the optional
AC-08 line); false positives get nothing. Nothing in this plan adds a database, an account
system, or any of the excluded heavyweight infrastructure.
