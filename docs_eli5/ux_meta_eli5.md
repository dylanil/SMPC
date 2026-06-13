# UX review — second opinion — plain-English version

> Plain-language companion to [`meta/ux.md`](../docs/review/meta/ux.md). The original is the
> source of truth and is unchanged. If the two disagree, trust the original.

## What this is

An independent double-check of the [UX / UI review](ux_eli5.md). Importantly, the reviewer
**recomputed every colour-contrast number themselves** — and that's where the first review went
wrong.

## The verdict

**Trustworthy on behaviour, but wrong on its contrast numbers.** The three big behavioural
findings are all real and correctly prioritised. But the accessibility/contrast section is
miscalculated and should *not* be acted on as written.

## What it confirmed

- **The infinite wait (H1)** — confirmed, correctly the #1 issue, and the fix is nearly free
  because the needed progress data already exists.
- **The raw error pop-ups (H2)** — confirmed, *plus* a nuance: trying to retry actually re-runs
  the whole protocol from scratch, so the recovery path is broken too, not just ugly.
- **The colour-only status cues (M2), the silent clipboard (M5),** and most of the small items —
  confirmed.

## The important corrections

- **M1 (muted text contrast) — REFUTED.** The first review claimed small grey text fails the
  accessibility standard. Recomputed, it actually **passes comfortably** (5.37:1 in the worst
  case, above the 4.5:1 bar). The first review's numbers were about 1.4× too low. **Don't lighten
  the text as a "fix."**
- **M3 (pastel role colours as text) — REFUTED.** All ten colours pass the contrast standard, and
  the one singled out as "worst" is actually among the *best*. Any leftover concern is purely
  aesthetic.
- **H3 (lone-visitor dead end) — downgraded** from High to Medium: it's a discoverability gap with
  a working escape hatch one scroll away, not a broken page.
- **M6 (no keyboard-focus outline) — bumped UP** toward High: removing the focus outline with no
  replacement is a real accessibility failure affecting *every* keyboard user on *every* control —
  bigger impact than several of the Mediums combined.

## What the first review missed (new findings)

- **NEW-1 (the big one) — No mobile viewport setting, so the entire responsive design is dead on
  phones.** A one-line-per-file omission means phones render the desktop layout shrunk and zoomed
  out, and none of the carefully-written mobile rules ever kick in. For a demo people open from a
  phone link, this is the **largest single mobile defect** — rated High.
- **NEW-2 — No "reduce motion" option** for users with motion sensitivity. Low.
- **NEW-4 — No favicon means every browser tab looks identical,** which makes juggling the
  aggregator + participant tabs hard. Low (a usability angle on the graphics review's favicon
  point).
- **NEW-5 — The figure input gives no feedback on an out-of-range value.** Borderline Low/Medium.
- A couple of paths were checked and confirmed clean (no per-keystroke network spam).

## Bottom line

Rely on the behaviour findings; **recompute before touching the text colour** (it already passes).
The single most important addition is the missing mobile viewport tag — a one-line fix that
quietly unlocks all the responsive work already done.
