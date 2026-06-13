# Release Board — plain-English version

> This is a plain-language companion to [`RELEASE_BOARD.md`](../docs/review/RELEASE_BOARD.md). The original is
> the source of truth and hasn't been changed. This file explains the same findings without
> assuming you know the technical details. If anything here and the original disagree, trust
> the original. The item codes (RB-01, AC-01, FP-01, …) are kept identical so you can look up
> the full technical detail in the original whenever you want.

## What this is

We ran a lot of reviews of the demo (seven angles, each double-checked by a second reviewer).
This board is the **single combined to-do list** — every issue, deduplicated, ranked, and with
a plain note on what to do about it. Where a second reviewer corrected the first, the corrected
version is what's recorded here.

**Update — 2026-06-13: the must-fixes and most of the should-fixes are now DONE.** Built and shipped:
✅ **RB-01, RB-02, RB-03, RB-04, RB-05, RB-06, RB-07, RB-08, RB-09, RB-11, RB-26** — the crash fix,
the frozen-screen fix, the friendly errors, the licence, the phone layout, the keyboard-focus
outline, the "this is a demo" disclaimers, the softened wording, the solo-demo signpost, and inline
code-comment markers. Two more (**RB-10, RB-35**) are **partly done** — their text/wording is in, but
a screenshot/preview image and the public web address are still needed to finish them. They're struck
through (or marked ⏳ partial) below. Everything else is still on the to-do list.

**Checked again on 2026-06-13 (before the fixes).** We first re-ran the whole thing — eight reviews
and eight second opinions, each working alone — to see if the list still held up. It did: **nothing
was overturned, no priorities changed, nothing new was added to the ranking.** A few small fix
*details* got sharper (e.g. RB-01: more kinds of odd characters cause the problem than first listed,
and it can also break the solo-demo screen; RB-26: flag ~4 spots in the code, not just one). The full
run lives in `docs/review/run-2026-06-13/`. We then acted on the recommended order — **fix the cheap,
important bugs first, then show off the reviews** ("found and fixed" beats "found") — which is the
batch now marked DONE above.

**Four ground rules** the whole list respects (the owner's fixed decisions):
- **No limits on how big a number someone can enter.** (Why: the demo should work for any
  scale, from pennies to millions.)
- **Keep the amber "Simulated round" warning** on the solo demo.
- **Never claim the signatures stop impersonation** — they don't, because there's no central
  "who's who" authority. (More on this in AC-02.)
- **Keep it lightweight** — no database, no accounts, no big infrastructure, no rewrite.

**Severity vs. priority:** *severity* is how risky a reviewer thinks something is; *priority*
(P0/P1/P2) is our call on **when to do it**, given the goal is a portfolio demo, not a product.
A small issue can be top priority if it's cheap and very visible (like a missing licence). A
real bug can be low priority if it only happens in a setup this demo never uses.

**The tally:** 4 must-fix · 9 should-fix · 27 nice-to-have · 13 accepted trade-offs · 4 false
alarms. *(Includes a later "public-deployment" scan on 2026-06-13 — RB-35 to RB-40 — logged for
the next planning round, not yet scheduled.)*

---

## P0 — must fix before showing this to anyone  ✅ ALL DONE (2026-06-13)

### ~~RB-01 — A weird-character number can crash or quietly break a round~~ ✅ DONE
**✅ DONE 2026-06-13.** The app now only accepts plain digits and rejects odd characters the moment they're submitted, with a safety net so the totalling step can never crash.
One participant can type a number using non-standard digit characters (like superscript "²" or
Arabic-Indic numerals) that **look** valid but aren't normal digits. Two bad outcomes: in one
case the round **crashes** every time anyone refreshes, and stays dead for 30 minutes; in the
other, the aggregator confidently shows an average that **no participant can reproduce** — which
destroys the demo's whole "verify it yourself" promise. **Fix:** only accept plain digits, and
reject the bad value the moment it's submitted (plus a safety net so the totalling step can
never crash).

### ~~RB-02 — A participant's screen waits forever, with no "something went wrong"~~ ✅ DONE
**✅ DONE 2026-06-13.** The participant page now detects when the session is gone and shows live progress ("3 of 5 in — waiting on B and D") instead of a frozen "waiting…".
The most common real-world hiccup — someone doesn't show up, or the session expires — currently
shows a falsely reassuring "Waiting for all shares…" message **forever**. Three separate
reviewers called this the single biggest credibility-killer. **Fix:** detect that the session is
gone and show live progress like "3 of 5 in — waiting on B and D."

### ~~RB-03 — Errors show up as an ugly raw pop-up full of code~~ ✅ DONE
**✅ DONE 2026-06-13.** Predictable errors after joining now show as friendly inline messages, not an ugly native pop-up full of technical gibberish.
When a predictable error happens after joining, the polished step-by-step screen collapses into
an ugly native browser pop-up showing raw technical gibberish — at exactly the moments the
design was built to handle gracefully. **Fix:** show friendly inline messages instead, reusing
the nice error handling that one part of the page already has.

### ~~RB-04 — There's no licence file~~ ✅ DONE
**✅ DONE 2026-06-13.** Added a standard MIT licence file at the repo root and a one-line License note in the README, so others may legally reuse and build on the code.
With no licence, the law's default is "all rights reserved" — meaning nobody is actually allowed
to reuse or build on the code, which is the opposite of what a public portfolio wants. It's the
cheapest possible fix with a big payoff. **Fix:** add a standard MIT licence file (the exact
text is already drafted).

---

## P1 — should fix before sharing widely

### ~~RB-05 — The pages don't render properly on phones~~ ✅ DONE
**✅ DONE 2026-06-13.** Added the one missing line to all three pages so phones now render the proper mobile layout instead of a shrunk-down desktop.
A single missing line means phones show the desktop layout shrunk down and zoomed out, so all
the mobile-friendly design that already exists never actually kicks in. For a demo people open
from a phone link, this is the biggest mobile problem — and it's a one-line-per-page fix.

### ~~RB-06 — The README doesn't say "here's what this is, and here's what it deliberately isn't"~~ ✅ DONE
**✅ DONE 2026-06-13.** Already covered: the README's "Known limitations" now spells out the most important caveat (the round stalls if anyone doesn't submit), the "Security notes" act as the threat model, and the new "this is a demo" disclaimer adds the rest — so no extra section was needed.
The most important honest caveat — that the round stalls if anyone fails to submit — is only
mentioned deep in a technical file, not in the main README. **Fix:** a short, honest section
spelling out what the demo is, what it isn't, and its known limits. Owning the limitations
actually builds credibility.

### ~~RB-07 — One claim is worded too strongly ("never sees any raw figure")~~ ✅ DONE
**✅ DONE 2026-06-13.** The README now says raw figures "never cross the wire" (always true), and the aggregator page spells out the one exception — the in-tab demo, which plays every role itself and so necessarily knows the figures it made up.
That phrase appears as an absolute on two screens, but the built-in solo demo *does* generate
and reveal figures (it openly says so). It's a small internal inconsistency a sharp reader could
catch. **Fix:** add a short "in a real round…" qualifier in both places. Don't over-rewrite —
the demo already hedges itself heavily.

### ~~RB-08 — There's no "this is just a demo" disclaimer~~ ✅ DONE
**✅ DONE 2026-06-13.** Added a short "Demonstration only — please don't enter real or sensitive figures" line to the bottom of all three pages, and a matching note near the top of the README.
Nothing on the pages plainly says "this is a toy — don't enter real data." Someone seeing the
insurance example might type in a genuine figure. **Fix:** a short, plain footer line on each
page plus a README paragraph.

### ~~RB-09 — A solo visitor hits a dead end~~ ✅ DONE
**✅ DONE 2026-06-13.** Added a visible "Just exploring on your own? … click Demo" prompt right under the main Aggregator button, so a lone visitor immediately sees the way to watch a full round.
The home page's main button leads to "how many participants will join?" — useless if you're
alone. The one feature that lets a single person watch a full round (the simulator) is buried at
the bottom. **Fix:** add a visible "Just exploring? Try the demo" signpost near the top.

### RB-10 — The best parts of the project are hidden below the fold  ⏳ PARTIAL
**⏳ PARTIAL 2026-06-13.** The README now points to the reviews folder near the top and highlights the "verify it yourself" story. **Still to do:** a screenshot of a finished round at the very top — that needs an actual captured image.
For a CV piece, the GitHub page is the first thing people see — yet the strongest signals
(correct maths, the "verify it yourself" feature, the honest docs, and the whole reviews folder)
are all out of sight. **Fix:** put a screenshot at the top of the README and point clearly to
the reviews folder and the verify-it-yourself story.

### ~~RB-11 — Keyboard users can't see what they've selected~~ ✅ DONE
**✅ DONE 2026-06-13.** Added a shared rule that shows a clear focus outline on every control when navigating by keyboard (mouse clicks stay outline-free).
The buttons and links don't show a visible "you're here" outline when navigating by keyboard,
and one input actively removes it. That's an accessibility failure across every control. **Fix:**
one shared rule that restores a clear focus outline everywhere.

### ~~RB-26 — Deliberate decisions aren't flagged where a future developer would see them~~ ✅ DONE
**✅ DONE 2026-06-13.** Added short "this is deliberate — don't "fix" it" comments right next to each of the spots in the code a future developer might otherwise trip over.
Some choices ("don't cap number size," etc.) are written down in the project docs but **not**
next to the actual code they affect. The worry: a future developer (or AI agent) fixing
something nearby might "helpfully" re-add a thing we deliberately left out. **Fix:** a one-line
comment at each such spot in the code pointing to the reasoning.

### RB-35 — No "share preview" when the demo link is posted  ⏳ PARTIAL
**⏳ PARTIAL 2026-06-13.** Added a short page "description" tag (helps a little). **Still to do:** the full social-preview tags and a preview image — those need an actual preview image and the site's public web address.
When you paste the link into LinkedIn, X, Slack, or a text message, it shows up as a bare URL —
no title, no description, no preview image. For something whose whole point is to be *shared*,
that blank card is the first impression *before* anyone even clicks. **Fix:** add the standard
"social preview" tags and one preview image (a screenshot of a finished round, which also doubles
as the README screenshot from RB-10). Cheapest reach win for going public.

---

## P2 — nice to have

### RB-12 — The demo button stays stuck after a failure
If the solo demo fails, the button stays greyed out even though the message says "try again" —
the only way back is a full reload, which throws away the session. **Fix:** re-enable the button
when it fails.

### RB-13 — Status is shown by colour alone
The little status dots change colour (and a faint symbol) but no text, so colour-blind users
can't tell them apart. **Fix:** add a word like "submitted" / "waiting" and/or a clearer tick.

### RB-14 — "Copy to clipboard" can fail silently
If copying doesn't work (common in certain setups), nothing tells the user. **Fix:** on failure,
switch the label to "select & copy" or auto-select the text.

### RB-15 — The participant doesn't see what they're being asked to measure until late
The "what is this number?" label only appears after a valid invite is entered; before that the
box just says "e.g. 42." **Fix:** show the metric in the input label as soon as it's known.

### RB-16 — A slow, half-finished request can tie up the server
There's no time limit on how long the server waits for an incoming request, so a deliberately
slow connection can hog resources. Low risk on our current hosting, but a cheap robustness win.
**Fix:** set a request timeout (one line).

### RB-17 — Add one more protective header
The server sends one security header today; adding a second cheap one ("don't guess file types")
is easy defence-in-depth. **Fix:** one extra header line.

### RB-18 — The "make it not look vibe-coded" visual polish pass
This is the owner's explicit "it looks AI-generated" concern. Lots of small inconsistencies: no
consistent text-size or spacing system, an arbitrary 10-colour rainbow, no icon or favicon, emoji
used as icons (which look different on each device), mismatched gradients and shadows, too many
corner-roundness values. **Fix:** a focused series of small design improvements — consistent
sizing/spacing, a proper icon and favicon, a tidied colour scheme, a real font, unified shadows
and motion. All cheap, no new build tooling needed.

### RB-19 — The automated test only checks the happy path
The current test only confirms a clean, successful round. It never checks what happens when
things go wrong — which is exactly where the two worst bugs live. **Fix:** add tests for the
error cases, including "a bad number is rejected and the totalling step never crashes."

### RB-20 — No "reduce motion" option
Some people get motion sickness from animation; the OS has a "reduce motion" setting we don't
honour. **Fix:** one rule that turns off the animations for those users.

### RB-21 — No security-contact file
For a security-flavoured project, there's no short note saying "this is a demo; here's how (or
whether) to report issues." **Fix:** a brief SECURITY file.

### RB-22 — "Negative zero" can show up
A tiny rounding quirk can display "-0" instead of "0." Purely cosmetic. **Fix:** treat -0 as 0.

### RB-23 — Note that rate-limiting depends on the hosting setup
Our defences against request-flooding rely on a feature of our specific host. If someone ran the
app exposed directly, that protection would quietly stop working. The risk itself is accepted for
our setup — this item is just **documenting** the caveat in the README.

### RB-24 — A bundle of small UX tidy-ups
A handful of minor fixes grouped together: better text-wrapping for long codes, bigger tap
targets that wrap nicely on small screens, a "locked — reload to restart" hint, tidier step
headings, and a phone-friendly numeric keypad for the figure input.

### RB-25 — An optional gentle hint for an unusual figure
Optionally show a soft, **non-blocking** hint if a typed figure looks out of the expected range.
**Important:** this is *not* a cap — it must never reject the value (that's a fixed owner
decision). A hint at most.

### RB-27 — A stuck participant has no way to recover
If a participant's page glitches, reloading actually makes it **worse** — they get permanently
locked out of their slot until the session expires. The only real recovery is a brand-new
invite. **Fix:** remember the participant's identity across a reload so re-joining just works,
and/or tell them recovery needs a fresh invite.

### RB-28 — The app silently needs a secure (HTTPS) connection
The cryptography only works over a secure connection (HTTPS, or on your own machine). If someone
tries to demo it across phones on a local network using a plain address, **every** page dies with
an unexplained error. **Fix:** detect this on load and show a friendly "use the HTTPS link"
message, plus a README note.

### RB-29 — Numbers with a comma decimal can be misread
In countries that write decimals with a comma ("42,5"), the figure input can silently chop it to
42 or reject it — on the one number the whole round depends on. **Fix:** use a decimal keypad and
validate/normalise commas.

### RB-30 — The one dependency isn't pinned to a version
The app's single external library isn't locked to a tested version, so a future redeploy could
pull a newer, possibly-incompatible version and break with no code change from us. **Fix:** pin a
known-good version range.

### RB-31 — Step-6 wording could be read as "signatures catch impersonation"
A sentence in the verification step can be over-read as claiming the signatures detect an
impersonator — which they don't, in the one impersonation scenario the docs admit to. **Fix:**
reword to be precise, and add an explicit "this does not catch someone who registered first."

### RB-32 — Anyone with a session code can read the whole round's metadata
The read-only pages aren't rate-limited, so in theory someone could guess session codes and read
a round's label, who's in it, the scrambled values, and the final average. **Crucially, the raw
individual figures stay safe** — but "whoever has the code can see the round" should be stated
plainly. (Guessing a code is impractical at real speeds, which keeps this low priority.) **Fix:**
a generous rate limit on reads, and/or document that the code is effectively a read-pass.

### RB-33 — The protocol rules are written out in three places at once
The exact format the maths depends on is hand-copied into the server, the browser, and the test —
in two different languages. If someone changes one and not the others, it breaks silently, caught
only if someone remembers to run the test. **Fix:** add a fixed "known-good" reference example that
both sides check against, so any mismatch fails loudly.

### RB-34 — Add more tests beyond the happy path
Build out a proper little test file covering: different group sizes, the "first answer wins" rule,
rejected expired/replayed security puzzles, rejected tampered tokens, and the reference example
from RB-33. The worst bugs and the most important design claim all live in currently-untested
areas. **Fix:** one self-contained test file, added to the safety gate.

### RB-36 — Nobody gets told if the site goes down
There's one always-on machine with a health-check address, but nothing actually watches it. If it
falls over (a redeploy, a flood, a traffic spike), you'd only find out when someone hits a dead
link. **Fix:** a free external "uptime monitor" that pings the health address and emails you. No
app code — and deliberately kept lightweight, not a big monitoring platform.

### RB-37 — We don't know how much traffic it can take
No one has measured how many people can use it at once before the single machine struggles. A
link that suddenly gets popular, or a bot, could overwhelm it. **Fix:** a quick load test to find
the realistic ceiling and decide whether the simple timeout fix (RB-16) is enough.

### RB-38 — The free-text label is unmoderated and shown to others
The label the aggregator types appears on everyone's screen. It can't be used to inject malicious
code (that's already prevented), but on a *public* site someone could type something offensive
that others see — a decency/reputation issue, not a security one. **Note:** this is *not* about
limiting numbers, and any fix must keep the safe text-only display. **Fix:** decide explicitly —
probably accept it (it's a short, throwaway demo), or add a light bad-word filter.

### RB-39 — Accessibility was reasoned about, never actually tested with a screen reader
All the accessibility findings so far came from *reading the code*, not from running a real
screen reader or navigating by keyboard. **Fix:** a 20-minute hands-on pass with a screen reader
and keyboard-only, once the accessibility fixes (RB-11/RB-13) are in, to confirm they actually
work and catch anything reading-the-code can't.

### RB-40 — No privacy/cookie note for public users
Once real members of the public use it, the site briefly handles their internet addresses (for
rate-limiting) and sets one functional cookie. The footprint is tiny, but there's no short
"here's what we do and don't store" note. **Fix:** a one-line privacy note in the README and/or
page footer; pairs with the "this is a demo" disclaimer (RB-08).

---

## Accepted — deliberate trade-offs, do NOT "fix" these

| Code | What it is | Why we're fine with it |
| --- | --- | --- |
| AC-01 | No limits on number size | The demo must work for any scale; the overall request-size cap already stops abuse. Do **not** re-add caps. |
| AC-02 | Signatures don't stop impersonation | There's no central "who's who" authority, so a fast interceptor could register as someone else and still produce valid-looking signatures. Closing this needs heavyweight identity infrastructure — out of scope. The signatures still do their real job (detecting tampering after registration). |
| AC-03 | Everything in memory, one machine, nothing saved | Deliberate lightweight design. No database or multi-machine setup. |
| AC-04 | If enough people collude they can unmask one person | This is inherent to how this style of private averaging works; documented and confirmed. |
| AC-05 | One shared aggregator password, no individual logins | Enough to keep casual visitors out; fine for a demo. |
| AC-06 | If anyone drops out, the round stalls | Inherent to the method. The limitation is accepted; *documenting* it is RB-06. |
| AC-07 | Two heavier security headers left out | They're real long-term maintenance commitments; deliberately skipped. The one cheap header is RB-17. |
| AC-08 | A precision ceiling on extremely huge numbers | A non-issue for realistic figures; an optional one-line README note at most. |
| AC-09 | Rate-limiting can be bypassed if hosted differently | Accepted for our specific hosting; the mitigation is the README note (RB-23), not code. |
| AC-10 | Dark mode only, no light or print styles | A committed dark look is a fine, arguably better, choice for a portfolio. |
| AC-11 | The round can finalise before all the key-exchange is complete | This boils down to the same "a dishonest input can skew the result" limit we already accept — so enforcing extra ordering buys nothing. Optional safety nicety only. |
| AC-12 | Sessions expire 30 min after creation, not after last activity | A round taking over 30 minutes gets cleaned up mid-flight — deliberate and aligned with the token expiry. Only worth changing if long rounds ever matter. |
| AC-13 | Running multiple machines would break rounds | The single-machine setting is correct; just keep that requirement prominent in the deploy docs. Don't "fix" with shared state (that means a database — out of scope). |

---

## False alarms — reviews flagged these, but they're not real problems

| Code | The claim | The verdict |
| --- | --- | --- |
| FP-01 | "Muted text fails the contrast standard" | **Wrong.** Recomputed — it passes comfortably. Do **not** lighten the text as a "fix." (Bumping tiny 12px notes to 13px is optional polish only.) |
| FP-02 | "The pastel role colours are too faint as text" | **Wrong.** All ten pass the contrast standard; the one singled out as worst is actually among the best. Any leftover concern is aesthetic, handled by the visual pass (RB-18). |
| FP-03 | "The crash returns an HTTP 500 forever" | **Mechanism mis-described.** It's actually a thread crash with a stderr flood, no status code. Corrected and folded into RB-01; not a separate issue. |
| FP-04 | "The demo reveals figures in the wrong order" | **Already fine.** Checked — the ordering is correct, the reveal always has its data. No action. |

---

*Note on provenance: this board combines our own reviews with our own second opinions — it's
rigorous self-checking, not an outside certification. The most important conclusions (the maths
and the security) held up under independent re-derivation, and the one review mistake we caught
(the contrast maths) is recorded above as a false alarm so nobody accidentally "fixes" it.*
