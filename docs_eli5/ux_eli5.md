# UX / UI review — plain-English version

> Plain-language companion to [`ux.md`](../docs/review/ux.md). The original is the source of
> truth and is unchanged. If the two disagree, trust the original. Finding codes (H1, M1, L1…)
> are kept for cross-reference. **Note:** some contrast claims in this review were later found to
> be miscalculated — see the [UX second opinion](ux_meta_eli5.md) and the corrections flagged
> below.

## What this was

A candid review of the **interface** across the three pages — how clear it is first time, how the
flows feel, how it handles errors and waiting, accessibility, mobile, and the wording. It's a
"read the code" review, not a live browser test.

## The three big problems (High)

**H1 — Waiting forever with no feedback.** A participant whose round never completes (because
someone didn't show up, or the session ended) sits on a frozen "Waiting…" message indefinitely,
with no way to tell what's wrong. The most common real failure looks like a frozen page. *This is
the single biggest "lose the visitor" issue.* Fix: show live progress ("3 of 5 in, waiting on B,
D") and detect a dead session like the aggregator page already does.

**H2 — Raw error pop-ups.** After you start, errors appear as an unstyled native browser pop-up
full of raw server text — jarring, and it breaks the polished look at exactly the moments the
design exists to handle. Fix: reuse the friendly inline error messages the joining step already
has.

**H3 — A lone visitor hits a dead end.** The home page's only button drops a solo visitor into a
"how many participants will join?" console with no participants and no obvious way to just *watch
it work*. The one feature that lets them (the simulator) is buried at the bottom and hidden
inside the aggregator flow. *(The second opinion downgrades this to Medium — there's a working
escape hatch one scroll away.)* Fix: add a visible "Just exploring? Try the demo" signpost.

## The medium issues

- **M1 — Muted text contrast.** *This finding was later refuted.* The review claimed small grey
  text fails the accessibility contrast standard, but a recheck found it actually passes
  comfortably. **Don't lighten the text as a "fix."** (Bumping tiny 12px notes to 13px is
  optional polish.)
- **M2 — Status shown by colour only.** The little "who's submitted" indicators rely on colour
  and a faint symbol with no text label, so colour-blind users can struggle. Fix: add a word
  ("submitted"/"waiting") and a clearer tick.
- **M3 — Pastel role colours as text.** *Also refuted* on contrast grounds — all the colours pass.
  Any leftover concern is aesthetic (covered by the graphics review), not readability.
- **M4 — The "what number am I entering?" label appears late** (only after a valid invite is
  typed). Minor. Fix: show the metric in the input label sooner.
- **M5 — Copy-to-clipboard fails silently** in some setups, with no feedback — on the exact
  sharing step the flow depends on. Fix: show a fallback ("select & copy") on failure.
- **M6 — No visible keyboard-focus outline.** Keyboard users can't see what's selected, and one
  input actively removes the outline. *(The second opinion bumps this one up — it's a real
  accessibility failure across every control.)* Fix: one shared focus-outline rule.

## The small stuff (Low)

Long numbers wrapping awkwardly (L1), borderline-small tap targets on mobile (L2), no "reload to
restart" hint after the inputs lock (L3), the demo's sample figures being tied to the exact
metric wording (L4), inconsistent heading styles (L5), and a missing mobile-decimal-keypad hint
(L6). All minor.

## What's already good

The participant page's pre-drawn six-step layout (greyed-out steps that light up as you progress)
is genuinely excellent — a clear map of the journey and a free progress indicator. The friendly
join-step error messages are the model the rest of the app should copy. The aggregator's
step-by-step reveal teaches as it goes, the demo is honestly labelled, the dark theme is
cohesive, and the result card is a satisfying payoff. The wording is friendly and refreshingly
non-overclaiming.

## The top 5 fixes (ranked)

1. Fix the infinite wait (H1).
2. Replace the raw error pop-ups with inline messages (H2).
3. Add a solo-demo signpost on the home page (H3).
4. Add a visible keyboard-focus outline (M6) — and note the contrast items (M1/M3) were refuted,
   so don't act on those.
5. Strengthen the colour-only status cues (M2) and the silent-clipboard feedback (M5).
