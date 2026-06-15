# Production-Readiness Plan - SMPC demo

**Purpose.** Move this educational, browser-based SMPC demo *closer to production-ready*
without turning it into an enterprise system. It stays a lightweight, no-database,
no-account demo. This document is the strategy wrapper; the per-finding triage lives in
[`docs/review/RELEASE_BOARD.md`](review/RELEASE_BOARD.md), which is the single source of
truth for what to fix and in what order.

**Status: remediation largely complete (2026-06-13).** Done and pushed: **all P0** (RB-01-04), **all
P1** (RB-05-11, RB-26, RB-35, RB-40), and the **P2 batch** (RB-12-17, RB-19, RB-21-23, RB-27 Tier-1,
RB-28-31, RB-33, RB-34) - **31 of 40** items, all marked ✅ DONE on the board. RB-32/36/38/39
accepted or won't-do, RB-25 skipped. **RB-18** is **done** (via `/review-council` + an owner render-loop):
the bounded subset plus a kept **black+orange + GitHub-typography** direction (`eee0eb1`; OKLCH-even
and grey schemes were trialed and rejected, `@font-face`/motion-easing skipped). Remaining from that 2026-06-13 cycle: only the
optional RB-37 load test on the live instance. (The `fly deploy` and the screenshot recaptures are
done - the README/aggregator screenshots and the OG card are now script-generated and current.)

**Re-validated 2026-06-13.** A second multi-agent pass (8 isolated domain reviews + 8 isolated meta
audits, archived under [`review/run-2026-06-13/`](review/run-2026-06-13/)) re-confirmed this plan and
the board with **0 refutations and no re-prioritisation**. At that point no application code had been
committed since the campaign began. Manager recommendation (see
[`review/run-2026-06-13/debate.md`](review/run-2026-06-13/debate.md)): execute the §8.1 P0 batch
*before* surfacing the `docs/review/` apparatus as a portfolio feature - "found **and fixed**" is a
far stronger signal than "found." **That batch has now been done** (the six items above); the review
apparatus can be surfaced next on solid ground.

**Third pass + implementation (2026-06-14 → 2026-06-15).** A *fresh independent* multi-agent run
(8 isolated domain reviews + 8 metas + a facilitated debate, archived under
[`review/run-2026-06-14/`](review/run-2026-06-14/); plan in
[`review/run-2026-06-14/ACTION_PLAN.md`](review/run-2026-06-14/ACTION_PLAN.md)) found **0 Critical/High
and 0 refutations** - crypto and the test suite were live-reproduced green - and added **RB-41…RB-55**
(portfolio framing, honesty-surface accuracy, cheap hardening, and real test-coverage gaps such as the
ECDSA signature-reject path), plus **RB-56** (display averages/sums to at most 2 dp, display-only). The
owner approved implementing the whole set and it **landed 2026-06-15**. The only board item still open
is **RB-37** (the load-test ceiling). The board's "Current status (2026-06-15)" line is authoritative.

---

## 1. Current architecture summary

A secure multi-party **average**: N participants (3-10) each submit one private number; a
separate aggregator computes only the average, via pairwise ECDH+HKDF masks that cancel, so
no raw figure crosses the wire and every participant can independently re-verify the sum and
all signatures.

- **Backend:** one single-file Python `http.server` (`server.py`), standard library only,
  plus one dependency (`cryptography>=42.0`) for ECDSA P-256 verification. No framework, no
  database, no message queue.
- **State:** entirely in process memory, keyed by 6-char session code; reaped on a TTL
  (~30 min) by a daemon thread. Sessions never share state. Restart wipes everything - by
  design.
- **Frontend:** three self-contained HTML pages (`public/{home,party,aggregator}.html`),
  each with its own inline `<style>` and inline JS, plus two shared static modules
  (`public/static/smpc-core.js` - protocol crypto; `pow.js` - proof-of-work miner).
- **Identity / integrity stack:** per-party invite token → server-signed HMAC bearer token
  → ECDSA-signed pubkeys/shares → first-write-wins per slot. Proof-of-work gates session
  creation and join; per-IP sliding-window rate limits; optional shared aggregator password.
- **Deployment:** Docker (`python:3.11-slim`, drops to non-root uid 1000) on fly.io
  (`fl-wg-smpc`, region `lhr`), **single pinned always-on machine** (`auto_stop_machines =
  false`, `min_machines_running = 1`) because in-memory state can't autoscale; `force_https`;
  `/healthz` check.
- **Deliberate non-goals (do not "fix"):** no persistence, no user accounts, no PKI/identity
  proxy, no input magnitude caps, no dropout resilience. These are documented design
  boundaries, not omissions - see the Accepted section of the board (AC-01…AC-10).

## 2. Release-readiness goals

The bar is a **credible public portfolio demo**, not a commercial product. Concretely:

1. **Don't lie to the user.** No silent forever-hangs or raw error modals on the common
   failure paths (RB-02, RB-03).
2. **One bad actor can't wedge everyone.** A single malformed share must not kill a round
   (RB-01).
3. **Presentable & honest at the surface.** Licensed, mobile-renderable, with a disclaimer
   and accurate (non-over-claimed) copy (RB-04, RB-05, RB-07, RB-08).
4. **Win the 30-second first impression** - both the running app (solo-demo signpost) and the
   GitHub repo page (screenshot, the review folder as a signal) (RB-09, RB-10).
5. **Keep what's already good:** correct crypto, independent verifiability, honest docs,
   defensive hardening, the lightweight architecture. Improve without regressing these.

## 3. Review dimensions run

Seven independent review dimensions, each with an independent second opinion, all in
[`docs/review/`](review/): **security**, **crypto/SMPC soundness**, **QA/correctness**,
**legal/licensing**, **UI/UX**, **product/viability**, **front-end graphics**. The second
opinions (`docs/review/run-2026-06-12/meta/`) validated findings against the code and, in one case, caught
and refuted a review error (the WCAG contrast math). The load-bearing claims - crypto
soundness and the security posture - held up under independent re-derivation and live
testing.

## 4. Findings format

All findings are consolidated in the release board with nine fields each: **ID · Source ·
Severity · Title · Evidence (file:line) · Why it matters · Minimal fix · Confidence · Needs
code change**, grouped into P0 / P1 / P2 / Accepted / False-positive. The board applies the
meta-review corrections (e.g. RB-01 raised to Medium-High; the contrast claims refuted to
FP-01/FP-02). Do not re-derive findings here - cite the board ID.

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
- **The owner runs `git push`** (`! git push`) - agent pushes are blocked by the credential
  manager.

## 6. Test / verification gate

Every remediation change must pass this gate before it's considered done:

1. **`python verify_round.py` and `python verify_round.py 10`** both PASS (masks cancel
   exactly) - the wire-contract regression guard. **`python tests.py`** PASSes too (contract
   vector + error-path matrix + N-sweep, RB-19/33/34) - run it against a freshly-started server
   so the per-IP rate limits don't trip mid-suite.
2. **New error-path assertion** (ships with RB-01): a malformed/non-ASCII-digit share is
   rejected at `/api/share`, and `/api/result` never crashes (RB-19).
3. **Manual click-through** of the three flows on a local `python server.py`: a full real
   round (3 tabs + aggregator), the solo demo (banner + reveal render), and a metric-less
   round - plus the specific failure the change targets (e.g. for RB-02, abandon a round and
   confirm the party page now reports "session lost" instead of hanging).
4. **`git status`** shows only intended files changed; `git diff` of `public/static/smpc-core.js`
   stays empty unless a change is explicitly a protocol change (it should not be for any
   board item).
5. **Mobile spot-check** after RB-05: the pages render at device width, not zoomed-out
   desktop.

## 7. Prioritisation framework

- **P0 - must fix before public demo.** Release-blocking: the demo breaks, lies to the user,
  or is trivially griefable; or a near-zero-cost item whose absence reads as unfinished.
- **P1 - should fix before wider sharing.** Materially improves credibility/usability/mobile
  but the demo is functional without it.
- **P2 - nice to have.** Polish, deeper a11y, the visual-craft pass, test coverage, extra
  hardening for deployment modes this demo doesn't use.
- **Accepted / out of scope.** Deliberate design boundaries; do not action (some warrant a
  documentation note, not code).
- **False positive / no action.** Findings refuted or corrected on audit; recorded so they
  aren't mistakenly actioned.

The board is the instance of this framework. As of 2026-06-15: **P0 ×4, P1 ×15, P2 ×37, Accepted ×14,
FP ×5** - all implemented except RB-37.
*(Totals include the missing-dimensions pass RB-26…RB-34 / AC-11…AC-13, the public-deployment scan
RB-35…RB-40, and the 2026-06-14 fresh run RB-41…RB-56 / AC-14 / FP-05 - see the board for per-item
status.)*

## 8. Proposed order of work

Each step is its own commit (or small commit series) and must clear the §6 gate. Re-run
`verify_round.py` after every server-side change.

1. **P0 batch - correctness & blockers. ✅ DONE 2026-06-13** (RB-01 `f753341`, RB-02/RB-03 `6a5cd6c`, RB-04 `0b4c176`, RB-05 `0f11cfa`).
   1. **RB-01** harden share validation (ASCII-only at `/api/share` write time + guard the
      result-time sum) - *and ship the RB-19 error-path test in the same change*, since it's
      the regression guard for exactly this bug.
   2. **RB-02** port session-lost detection + progress to the party page.
   3. **RB-03** replace the post-join `alert()` with inline status-aware errors.
   4. **RB-04** add the MIT `LICENSE`. **RB-05** (viewport meta) rides along here - it's a
      one-line-per-file change and trivially low-risk.
2. **P1 batch - credibility & surface. ✅ MOSTLY DONE 2026-06-13.** ~~RB-08 disclaimer + RB-07 claim
   hedge~~ ✅ (`bc39b32`); ~~RB-06 README threat-model section~~ ✅ (covered by the existing *Known
   limitations* + the RB-08 disclaimer); ~~RB-09 solo-demo signpost~~ ✅ (`0d4a152`); ~~RB-11
   `:focus-visible`~~ ✅ (`0f11cfa`); ~~RB-10 (README screenshot/GIF + surface the `docs/review/`
   folder)~~ ✅ (`a6ae549`, `9b9dceb`): `docs/review/` pointer + verify-it-yourself story + a
   completed-round hero screenshot (and two contextual shots).
3. **P2 batch - polish, hardening, tests. ✅ DONE 2026-06-13** (everything except RB-18). Shipped:
   ~~RB-16 read timeout, RB-17 nosniff, RB-12/RB-13/RB-14/RB-15/RB-22, RB-24 (most), RB-19/RB-33/RB-34
   tests, RB-21 SECURITY.md, RB-23, RB-27 Tier-1, RB-28/RB-29/RB-30/RB-31~~. RB-32 accepted (reads
   stay unlimited), RB-20/RB-25 deferred/skipped, RB-24-L2/L5 + RB-37 load-test folded onward. Then
   the **RB-18 visual-craft pass** is **done** (via `/review-council` + an owner render-loop): the
   bounded subset plus a kept **black+orange + GitHub-typography** direction (OKLCH-even and grey
   schemes trialed and rejected; `@font-face`/motion-easing skipped). See
   `docs/review/council/2026-06-13-rb18.md`.
4. **Re-deploy** (`fly deploy`) once P0 (and ideally P1) are merged and the gate is green;
   re-run the click-through against production.
5. **Public-deployment dimension - logged 2026-06-13, not yet scheduled.** Surfaced when
   scoping "share this more widely with the public" rather than "invite a few people." These
   are logged on the board (RB-35…RB-40) to be prioritised holistically in the next planning
   pass, **not** actioned case-by-case:
   - **RB-35** Open Graph / `description` share-preview metadata + a preview image (the single
     cheapest reach win; the image doubles as RB-10's screenshot - slot near the P1 surface work).
     ✅ **DONE** (`a6ae549`, `9b9dceb`): `<meta name="description">` + full OG/Twitter card tags on
     all three heads with absolute `fl-wg-smpc.fly.dev` URLs; the `og:image` is served from
     `/static/og-preview.png` (a completed-round screenshot, doubling as RB-10's hero).
   - **RB-36** a lightweight external uptime check on `/healthz` (ops; no app code).
   - **RB-37** a load/capacity reality-check on the single instance (pairs with the RB-16
     read-timeout).
   - **RB-38** decide the stance on unmoderated free-text metric content for a public audience
     (likely accept; must not regress the textContent-only rendering or add a figure cap).
   - **RB-39** a real screen-reader / keyboard-only accessibility pass (all prior a11y findings
     were code-traced, never run - slot after RB-11/RB-13).
   - **RB-40** a one-line privacy/cookie note (README-targeted; pairs with the RB-08 disclaimer).

Accepted items get at most a documentation note (RB-06, RB-08, RB-23, and the optional
AC-08 line); false positives get nothing. Nothing in this plan adds a database, an account
system, or any of the excluded heavyweight infrastructure.
