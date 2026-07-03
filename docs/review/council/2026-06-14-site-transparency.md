> **Provenance.** Published verbatim from the project's private review archive on 2026-07-03.
> Finding IDs (`RB-`/`AC-`/`FP-`) refer to the internal release board; see
> [`../README.md`](../README.md) for the ID scheme and the campaign summary. Every council seat
> (each domain lens and the challenger) was an isolated AI agent session; the owner made every
> final decision.

# Review council - Live-site transparency / education

**Date:** 2026-06-14
**Proposal:** Surface more of the educational-POC purpose and known-limitation honesty on
the *live website* (not just GitHub), so visitors understand it isn't production-secure -
without (a) overloading users with documentation or (b) advertising exploitable flaws.
**Counterpoint weighed:** the GitHub repo (README "Known limitations", `SECURITY.md`, `docs/`)
is already fully public, so the information is already out there.

## Convened roster

Legal · UX (with light graphics/placement duty) · Product · Security · Challenger.
(Minimal sufficient subset: the proposal is copy/transparency/framing on public pages plus a
security question about disclosure risk. Crypto/QA not convened - no protocol or lifecycle change.)

## Opinions (one line each)

- **Legal - support-with-changes.** Footer disclaimer is already adequate; the *real* gap is an
  over-claim, not under-disclosure: `<meta name="description">` ("a privacy-preserving secure …
  demo") states an unconditional boast that contradicts AC-02/AC-04 - same class as RB-07, missed
  by that sweep. Required fix is subtractive. No T&Cs/privacy-policy/cookie-banner needed (no PII,
  RB-40 covers privacy).
- **UX - support-with-changes.** Honesty floor already met; the missing piece is the *portfolio
  signal*. Add one closed-by-default `<details>` on home only (pointer, not copy; links out), keep
  it ≤4 lines, do not nudge at the party figure-entry moment, don't touch shared `:root` tokens.
- **Product - support-with-changes.** Transparency *helps* the value proposition iff framed as
  edge-mapping not confession. Highest-leverage win is one sentence + link routing the curious to
  `docs/review/` ("reviewed in the open" flex). Decline a dedicated limitations page.
- **Security - support (wording guardrail).** Marginal abuse risk on the live deployment is ~zero:
  none of the flaws are obscurity-gated (they need an invite token, an authorised slot, or off-fly
  hosting). Surface *what/why* on-page; keep *how* (join-race sequence, session-code entropy math,
  off-fly rate-limit bypass) link-only. Hard lines: never claim signatures stop impersonation
  (AC-02); keep amber banner; `textContent`-only (RB-38).
- **Challenger - REVISE down to near-nothing.** Honesty surface already exists (RB-06/07/08/40/31,
  all DONE); over-disclosure risks looking unfinished and re-creating the just-deleted `docs_eli5/`
  mirror (duplication-drift). Cheapest sharper alternative: one sentence + one GitHub link,
  progressive disclosure, single source of truth; flip posture from apology to pedagogy.

## Debate / resolution

One genuine collision: **UX's `<details>` block vs. Challenger's "one line only."** Resolved -
they are closer than they appear: UX explicitly required the block be a *pointer, not a copy*, and a
*closed-by-default* `<details>` neither clutters (collapsed) nor duplicates (category-level + links).
That satisfies the Challenger's two real objections (clutter, drift) while giving Product/UX the
framing room. Everyone agreed on: link don't fork, frame as maturity, keep banner/AC-02/textContent,
mechanics stay link-only.

## Recommendation: **REVISE** - scoped down, three small changes (one commit)

1. **[Required, Legal]** Fix the `<meta name="description">` over-claim on all three pages →
   "An educational demo of secure multi-party computation … Not production-secure." (Also fixed the
   home `og:title` "privacy-preserving SMPC demo" → "educational SMPC demo" - same boast, same head;
   surfaced rather than left inconsistent.)
2. **[Cheap]** Footer "Demonstration only" → "Educational demonstration only" on all three pages.
3. **[Transparency win]** One closed `<details>` "How honest is this demo?" on home.html only -
   frames the project as an honest educational POC, names limits at category level, links to
   README · SECURITY · review board. Pointer, not a duplicated limitations list.

**Declined:** per-page limitation blocks; party figure-entry nudge; on-site exploit mechanics; any
duplicated limitations list.

## Owner decision

**Approved "All three" (2026-06-14).** Implemented in the same commit as this record.

---

# Follow-up - same day: always-visible, on every page

**New owner directive (HOW, not whether):** make the honesty content **always visible** (not behind
a click) on home, and put it on **all three pages**. Owner priorities, verbatim: "clear to everyone …
do not want to be liable … transparent over what the app can and can't do and what it shouldn't be
used for or depended on." This reverses the earlier same-day call (closed `<details>`, home-only).

**Convened:** Legal · UX · Product · Challenger. (Security not re-spawned - no new trust boundary,
input, or endpoint; only the visibility/placement of already-vetted static copy changes. Its carried
guardrails still bind: `textContent`-safe static copy, AC-02 (never claim signatures stop
impersonation), amber banner untouched.)

**Opinions (one line each):**
- **Legal - support-with-changes.** Always-visible is *legally stronger*: a closed `<details>` is a
  weaker disclaimer under the conspicuousness doctrine (UCC §1-201(b)(10); *Specht v. Netscape*; UK
  CRA 2015 transparency). Load-bearing clauses that must be always-visible are **"as-is / no warranty"**
  and **"do not rely on it for any real, confidential, regulated or production purpose"** - the current
  footer's "please don't enter real figures" was too soft. Stop short of any T&Cs/EULA/clickwrap and
  avoid an enumerated banned-uses list (catch-all is stronger). Keep footer + block both (redundancy
  aids conspicuousness).
- **UX - support-with-changes.** Use a flat always-visible callout, **not `<details open>`** (a toggle
  invites a close click that defeats the requirement). Full copy on home above the role cards; a
  **shorter variant** on the two task pages anchored **above the footer** - never above the figure
  input (it would contradict the very property being demonstrated) and never at the top competing with
  the amber banner. Reuse existing tokens (no `:root` change); minimise CSS; mark the triplication with
  the existing in-file `keep in sync` convention + a CLAUDE.md Styling note.
- **Product - support-with-changes.** Reframe from apology to spec: title **"What this demonstrates -
  and what it deliberately doesn't,"** capability-first, neutral "spec-card" styling (NOT amber/warning).
  "Deliberately" converts each limit from defect → design decision; this is the threat-model-literacy
  signal an insurance/data audience reads as senior. Don't fork the full limitations list onto every
  page.
- **Challenger - revise execution.** The *liability* goal is already carried by the always-visible
  footer; the block does *education*, not liability. Triplicating a long nuanced block re-creates the
  `docs_eli5/` drift hazard deleted the same morning. Minimal-drift form: strengthen the one already-
  triplicated footer, keep depth home-only; if a block must go on task pages, keep it short and add a
  mandatory `keep-in-sync` marker.

**Debate / resolution.** No collision on direction (owner decided always-visible-everywhere). The live
tension was *how much* on the task pages and *how to contain drift*. Resolved: (a) strengthen the
always-visible **footer** with the two legally load-bearing clauses (Legal) - it stays the single
already-synced legal surface; (b) convert the home block to a flat, always-visible, **reframed**
"demonstrates / deliberately doesn't" spec-card (UX form + Product framing); (c) task pages get a
**short, self-contained one-paragraph callout** (one string, identical on both) above the footer -
states the limits inline (owner's "no doubt on every page") without the full wall and without a bare
pointer-link; (d) drift contained: shared `.honesty` CSS block byte-identical in all three with a
`keep-in-sync` marker, two authored copy strings only (home-full, task-short), CLAUDE.md Styling note.
Carried guardrails: neutral (not amber) styling so it doesn't dilute the demo banner; static
`textContent`-safe copy; AC-02 honoured ("can't stop an impostor who registers first").

## Owner decision (follow-up)

**Approved (2026-06-14):** always-visible everywhere; task-page treatment = **short self-contained
callout** (chosen over "full block on every page" and "one-line pointer strip"). Implemented in the
same commit as this follow-up record.

---

# Follow-up 2 - same day: disclaimer prominence on the task pages

**Owner concern:** on party/aggregator the disclaimers sit at the BOTTOM; owner (risk-averse) wants
them MORE OBVIOUS to reduce legal risk.

**Convened:** Legal · UX · Product · Challenger.

**Opinions (one line each):**
- **Legal - support-with-changes.** The real defect is *timing*, specific to **party.html**: the user
  enters a figure at the TOP (Step 1) but meets the warning only at the BOTTOM, *after* acting - the
  classic post-hoc disclaimer courts discount (*Specht v. Netscape*; conspicuousness UCC §1-201(b)(10)).
  Fix = one short pre-action line carrying the load-bearing "demo / no real data / no reliance" payload
  *at the figure-entry point*. Aggregator types a label not a confidential figure, so its bottom
  placement is legally fine (symmetry cheap, optional). Explicitly **no clickwrap/EULA** (disproportionate;
  would imply a contract that doesn't exist). Keep the catch-all, not an enumerated banned-uses list.
- **UX - support-with-changes.** Reconciled its own earlier "never above the input" line: that objection
  was to an *alarming multi-line block*, not a one-line muted guidance. A muted, sandbox-framed "Demo
  only - don't enter real figures" reads as test-mode instruction, not a security confession, and
  coexists with "your figure never leaves your browser." Place above the figure input (party) / in the
  create-row (aggregator). Muted, never amber (preserve the demo banner's salience). Reject top strip
  (competes with amber slot) and sticky footer.
- **Product - support-with-changes.** Prefer a thin neutral "DEMO ENVIRONMENT" top strip (reads as ops
  maturity, like a STAGING banner) over a warning box; keep the educational callout at the bottom. Then
  **freeze** the transparency surface - the ratchet is approaching apologetic.
- **Challenger - revise down.** Third pass today; risk already low and well-covered. Cheapest highest-
  conspicuousness move is one word - put "demo" in the `<title>`/`<h1>` (most conspicuous slot, zero
  clutter, zero drift, no contradiction with the input). A prominent warning over the figure input
  undercuts the core teaching claim. Recommend: H1 word + stop; if more, *relocate* the existing callout,
  don't add a new element.

**Debate / resolution.** Collision: does a line above the figure input contradict the demo's "figure
never leaves your browser" claim? UX (who set that hard line) resolved it: a *muted, sandbox-framed*
single line does not - only an alarmist block would. Adjudicated to the leaner Legal+UX fix over
Product's new top strip (the strip is a new triplicated chrome surface competing with the amber banner;
the near-input line is the more precise "before the transaction" fix). Folded in the Challenger's cheap
"demo" in `<title>`/`<h1>` (different payload from the pre-action line - frames the page; the line
carries the liability clause). Declined: top strip, clickwrap/EULA, alarmist styling. Noted (Product +
Challenger) that this is the freeze point.

## Owner decision (follow-up 2)

**Approved "targeted pre-action line" (2026-06-14)** - chosen over "also add a top DEMO strip" and
"minimal: just H1 word". Implemented:
- Muted, page-specific pre-action line above the party figure input and in the aggregator create-row
  (intentionally **not** a shared/triplicated string - each is worded for its own action, so no
  cross-page sync contract; inline-styled muted text, reusing `--muted`).
- "demo" added to the `<title>` and `<h1>` of party.html and aggregator.html.
- Existing bottom callout + strengthened footer kept unchanged.

Transparency surface considered **frozen** after this pass (owner may reopen on a genuinely new risk).

---

# Follow-up 3 - same day: protocol "how the masks cancel" diagram

**Owner directive:** add a simple geometric schematic - "possibly an animated GIF" - articulating the
core crypto (at minimum the cancelling pairwise masks), on the README and the website "How it works".
Council to decide the form.

**Convened:** Graphics · Crypto · UX · Product · Additional-dimensions (format/rendering/serving) ·
Challenger. (Security not convened - no trust boundary; the asset is static content.)

**Opinions (one line each):**
- **Graphics - support-with-changes.** Equilateral triangle A/B/C + aggregator below; mask edges
  **dashed** (derived, not sent), masked shares **solid** arrows; reuse accent tokens; omit full DH.
  Vector is crisper, but the static final frame must read on its own.
- **Crypto - support-with-changes.** Must-get-right: masks derived independently and **never
  transmitted** (no "r_AB sent A→B" arrow - the classic error), explicit +/− cancellation, aggregator
  sees only masked shares. Show DH only minimally or abstract it with a caption. Keep ECDSA/PoW off the
  diagram; honesty caption (honest-but-curious, no input validation, no impersonation defence - AC-02/04).
- **Additional-dimensions - support-with-changes; format = animated GIF.** Decisive rendering fact:
  **GitHub READMEs animate only GIF** - animated SVG is frozen/stripped. README images load by repo
  path (no server route needed); serving on the site needs a 2-line server.py change (extension +
  `image/gif` Content-Type, the latter mandatory under `nosniff`). Commit the generator as source of truth.
- **UX - support-with-changes.** Home only, inside `.how` above the (untouched) 3 steps. A GIF can't
  honour `prefers-reduced-motion` → wrap in `<picture>` swapping a static frame under reduced-motion.
  Provide `role`/alt longdesc.
- **Product - support-with-changes.** High portfolio value (explains the one hard idea the live demo
  deliberately can't show). README is the primary home; consider replacing the masked-shares screenshot
  (meaningless to a cold reader) with the diagram - explain-then-show.
- **Challenger - revise down.** Risk of redundancy with the existing text + live demo, the accuracy
  trap, and a binary blob in git; cheapest path is a static schematic, README-first.

**Debate / resolution.** The genuine fork was static vs animated. The owner explicitly decided **motion
is worth it**, which settles it - and motion across both surfaces *forces* an animated GIF (additional-
dimensions: GitHub won't animate SVG). The reduced-motion objection (UX) is resolved by the `<picture>`
static-frame swap; the accuracy objection (Challenger/Crypto) by the must-get-right list (dashed,
never-sent masks; solid share arrows only; +/− cancellation; honesty caption). DH abstracted (dashed
"derived independently" links + caption), reconciling Graphics (omit) and Crypto (don't mislead).

## Owner decision (follow-up 3)

**Approved "Static SVG + an animated GIF too" → executed as an animated GIF with a static fallback**
(2026-06-14):
- `public/static/masks.gif` (animated, narrative beats: figures → masks form → masked shares sent →
  worked sum → average) + `public/static/masks-still.png` (composite reduced-motion fallback showing the
  whole story in one frame). Single source of truth: `docs/assets/make_protocol_diagram.py` (Pillow, dev-only).
- Website: home `.how` block, `<figure>` with a `<picture>` that swaps the still under
  `prefers-reduced-motion`; full alt-text longdesc; honest figcaption. `.diagram` CSS is home-only.
- README: animated GIF leads the Protocol section (explain-then-show), kept the real-UI screenshot below.
- `server.py` `/static/` route widened to allow `.gif` with exact `image/gif` Content-Type (nosniff).
- Concrete illustrative numbers (x=12/30/9, masks 5/8/3 → shares 25/28/−2 → total 51 → average 17) so the
  cancellation is tangible. Crypto invariants honoured: masks dashed/never-sent, only masked shares travel.

---

# Follow-up 4 - same day: diagram clarity (arithmetic beat + the no-peer-to-peer question)

**Owner asks:** (1) add the per-party masking arithmetic to the GIF (e.g. `A: 12 + 5 + 8 → s = 25`);
(2) **council to debate** whether the GIF should make clear there's no peer-to-peer comms - the mask/key
exchange is facilitated by the central server - and that it's "broadly how it works", not every detail
(it omits e.g. the server-signed shares). Owner suspected (2) "may be hard / overkill".

**Verified fact:** no P2P channel exists; ECDH **public keys** are relayed via the server
(`/api/pubkey` POST, `/api/pubkeys` GET), and each pair derives its mask **locally** (the mask is never
sent). So the dashed A-B/A-C/B-C lines imply a direct link that doesn't physically exist.

**Convened:** Crypto · Graphics · UX · Product · Challenger.

**Opinions (one line each):**
- **Crypto - support-with-changes (caption).** The dashed line is a *topological* inaccuracy, not a
  cryptographic one - nothing secret crosses it; only public keys are relayed. Fix with a caption, NOT
  by re-routing through the hub (that would wrongly imply the server handles the mask). Add a scope line
  (omits ECDSA signed shares / PoW) - keep captions in HTML/MD, not baked in the frame.
- **Graphics - support-with-changes (dissent: a beat).** Proposed a short party→hub→party key-exchange
  beat before the masks form; rejected curving links through the hub / glyphs (imply server sees masks).
- **UX - support-with-changes (lean: caption only).** The no-P2P point answers a question a first-timer
  isn't asking and risks undercutting the pairwise intuition; ~21s is already at the attention ceiling.
  Fold both points into one caption beneath the figure.
- **Product - support-with-changes (caption).** Server-mediation in-frame is gold-plating; one caption
  carries both the no-P2P accuracy and the scope disclaimer and signals maturity. ROI: (1) arithmetic
  beat, (2) caption, (3) skip on-canvas mediation. Framing nudge: make the caption a *handoff* to the
  README/live demo.
- **Challenger - add arithmetic + one caption, skip geometry.** Sharpest point: animating the relay
  risks the *worse* "server sees the masks" misconception; the dashed line is a fair abstraction of a
  logical pairing. 3rd refinement - ship discipline says land the cheap wins and stop.

**Debate / resolution.** 4 of 5 converged on **caption, not animation**; Graphics' beat was outweighed
by the shared Crypto/Challenger finding that animating party→hub→party during the masking beats invites
the "server sees the masks" misconception - strictly worse than the mild dashed-line abstraction - plus
the runtime/attention cost (UX). Resolved: keep the geometry; satisfy both asks in one static caption.

## Owner decision (follow-up 4)

Owner had delegated the form to the council; implemented the consensus (2026-06-14):
- **Arithmetic beat** added to the GIF - a dedicated "compute" beat shows `s = x ± masks` per party
  (`12+5+8=25`, `30−5+3=28`, `9−8−3=−2`) with the masks visible on the edges; captions renumbered 1→6;
  typographic minus (U+2212) made consistent across all values.
- **One caption** (home `<figcaption>` + README) carries both the no-P2P / server-relays-public-keys /
  mask-derived-locally-never-sent point **and** the "broadly how it works - omits the ECDSA signed-share
  integrity layer" scope note, ending with a handoff to the limitations / README.
- **Geometry unchanged** (no key-exchange beat, no re-routing) - avoids the server-sees-masks
  misconception and keeps the cancellation payoff clean. The Graphics dissent (a minimal key-exchange
  beat) is recorded as the evidence-driven fallback if user feedback later shows real P2P confusion.
