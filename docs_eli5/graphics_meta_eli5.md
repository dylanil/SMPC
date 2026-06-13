# Graphics review — second opinion — plain-English version

> Plain-language companion to [`meta/graphics.md`](../docs/review/meta/graphics.md). The original
> is the source of truth and is unchanged. If the two disagree, trust the original.

## What this is

An independent double-check of the [visual design / graphics review](graphics_eli5.md). The
reviewer re-checked every concrete value (font sizes, spacing, colours, corner radii, etc.) and
confirmed the absences (no favicon, no shadows, no mobile viewport tag) themselves.

## The verdict

**Accurate, fair, and one of the better-calibrated reviews in the repo.** Every factual claim
checks out to the exact value. No manufactured problems, real wins credited specifically, and the
taste-vs-fact line is kept honest throughout. The only changes are one severity bump, one tiny
factual correction, and a ranking opinion.

## What it confirmed

- **No consistent size or spacing system** (including the tell-tale half-pixel and 2px
  asymmetries) — confirmed.
- **The arbitrary 10-colour rainbow,** including two near-identical oranges — confirmed.
- **No logo or favicon, no shadows anywhere, and the two almost-matching gradients** — all
  confirmed (the mismatched gradients being the single strongest "vibe-coded" tell).
- **System fonts doing all the work,** so type looks different per device — confirmed.
- **The "one-third of the way to art-directed" headline is fair** — neither too harsh nor too
  kind.

## The corrections and additions

- **The mobile viewport tag (G-L3) — bumped from Low to High.** The graphics review filed it as a
  minor rendering note, but (agreeing with the UX second opinion) it actually disables the entire
  responsive design on phones — a one-line fix with huge leverage.
- **A tiny factual fix:** there are five distinct corner-roundness values, not six (no "5px"
  exists). Doesn't change the recommendation.
- **NEW — Emoji icons also render differently on each operating system,** so a Windows, Mac, and
  Android user can see different shapes — a broader reason to switch to proper icons.
- **NEW — A couple of small notes:** new motion should ship with a "reduce motion" opt-out, and
  the dark-only / no-print choices were checked and judged fine for a portfolio.
- **A ranking opinion:** for a portfolio specifically, the reviewer would put the **favicon at #1**
  (it's the literal first pixel a reviewer sees, and its absence is an unambiguous "unfinished"
  verdict), with the sizing/spacing system at #2 — the first review had these the other way around.
  Both orderings are defensible.

## Bottom line

The graphics review is factually accurate and its priorities are sound. The most important
cross-review change is treating the missing mobile viewport tag as a high-impact fix, not a minor
one.
