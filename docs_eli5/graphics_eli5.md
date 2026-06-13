# Visual design / graphics review — plain-English version

> Plain-language companion to [`graphics.md`](../docs/review/graphics.md). The original is the
> source of truth and is unchanged. If the two disagree, trust the original. Finding codes
> (G-H1, G-M1, G-L1…) are kept for cross-reference.

## What this was

A review of the **look and feel** only — typography, colour, spacing, icons, visual identity,
polish. This is the owner's explicit "it looks vibe-coded, help me move past that" concern.

## The honest read

It's about **one-third of the way from "vibe-coded" toward "art-directed"** — call it "competent
default dark dashboard." It's clearly not sloppy: the colour palette is restrained, the card
layout is consistent across pages, and the step-by-step reveal shows real product thinking. But
on pure craft it reads like the strong default a capable engineer (or an AI) produces, not
something a designer deliberately art-directed. A senior designer would say "clean, but I've seen
this exact dark theme a thousand times." Closing that gap is the whole job — and the good news is
it needs art direction, not a rebuild, because the underlying bones are sound.

## The high-impact issues

- **G-H1 — No consistent text-size system.** Font sizes are picked one at a time by eye —
  including a tell-tale "12.5px" half-pixel, and the *same* heading being two different sizes on
  different pages. Fix: adopt a proper size scale and use only its steps.
- **G-H2 — No consistent spacing system.** Padding and margins are ad-hoc, with tell-tale 2px
  asymmetries no real system would produce. Fix: snap everything to a tidy 4/8px grid.
- **G-H3 — The 10 participant colours are an arbitrary rainbow.** No logic, wildly varying
  brightness, and two near-identical oranges that are easy to confuse. Fix: generate them all
  from one consistent colour sweep so they look like a family.
- **G-H4 — No logo or favicon at all.** The browser tab shows the generic default icon — the
  single most common "unfinished" signal. Fix: ship a simple custom icon (one small SVG, no build
  step needed).

## The medium issues

- **G-M1 — Emoji/text characters used as icons.** They don't share a consistent weight or style,
  so they read as placeholders. Fix: a small set of proper inline-SVG icons.
- **G-M2 — Inconsistent sense of depth.** Cards use three unrelated styles with no rule, no
  shadows anywhere, and two *almost*-but-not-quite matching gradients (the strongest single
  "vibe-coded" tell). Fix: pick one depth language and unify the gradient.
- **G-M3 — Too many corner-roundness values.** Fix: settle on three.
- **G-M4 — Hierarchy leans on size and colour, barely on font weight,** and one global
  line-height is applied to everything from the huge result number to tiny captions. Fix: vary
  weight and tune line-heights per size.
- **G-M5 — System fonts do all the work,** so the type looks different on each operating system —
  including the code/number font, which is a hero element here. Fix: self-host one characterful
  font (a distinctive monospace would be on-brand for a crypto demo).

## The small stuff (Low)

Animations only on hover, not on state changes, and the demo's share-arrival timing is random
rather than a deliberate rhythm (G-L1); no visible keyboard-focus ring (G-L2); **no mobile
viewport tag, so the responsive design doesn't actually engage on phones** (G-L3 — small here but
the UX second opinion rightly raises this to a big deal); the brand purple being too close to one
of the role colours (G-L4); and the maths notation rendering inconsistently (G-L5).

## What already shows taste

The restrained, cool-toned dark colour base is genuinely good — the most "designed" part of the
system. The greyed-out-steps-that-light-up device is a legitimately elegant piece of visual
storytelling. The per-participant colour concept is a good instinct (even if the execution needs
the G-H3 fix). The result card is a well-built payoff moment. And the restraint overall — no
clutter, no gradient soup — is exactly what makes all these fixes cheap.

## The top 5 upgrades (ranked)

1. Impose a text-size and spacing system (G-H1 + G-H2) — invisible per element, but it's most of
   what "designed" actually feels like.
2. Ship a real logo and favicon (G-H4) — kills the #1 "unfinished" tell.
3. Replace the rainbow with one coherent colour family (G-H3).
4. Swap in a characterful self-hosted font for the codes/numbers (G-M5).
5. Unify the depth and add deliberate motion to the share-arrival moment (G-M2 + G-L1).

The single biggest first-impression change is #1 (the sizing/spacing system); the most visible
single artifact is the favicon (#2).
