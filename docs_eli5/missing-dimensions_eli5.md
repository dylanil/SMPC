# Missing-dimensions review — plain-English version

> This is a plain-language companion to [`missing-dimensions.md`](../docs/review/missing-dimensions.md). The
> original is the source of truth and hasn't been changed. This file explains the same findings
> without assuming you know the technical details. If anything here and the original disagree,
> trust the original. The item codes (MD-01 … MD-12) are kept identical so you can look up the
> full technical detail in the original.

## What this is

The seven main reviews (and their second opinions) covered a lot — but they left a few **angles**
under-examined. This pass went back and checked six of those gaps:

1. **Protocol/state-machine** — does the step-by-step flow behave correctly, including when
   things go sideways?
2. **Browser/mobile compatibility** — does it work across devices and browsers?
3. **Deployment/operations** — is it reliable to host and redeploy?
4. **Privacy/over-claiming** — are we promising more privacy than we deliver?
5. **Maintainability / future-developer safety** — will a future developer accidentally undo a
   deliberate decision?
6. **Test strategy** — are we testing the right things?

Nothing was changed — this is review only. Every finding here also got added to the main release
board (as RB-26 to RB-34 and AC-11 to AC-13), so you'll see overlap with the plain-English board.

---

## 1 · Does the step-by-step flow behave correctly?

### MD-01 — A stuck participant who reloads gets permanently locked out *(should fix)*
When a participant starts, their browser creates a fresh identity. The server locks each slot to
the **first** identity it sees. So if something glitches and they reload, the browser makes a
*new* identity, the server rejects it as a mismatch, and they're stuck out of their own slot for
30 minutes. The advice "just reload" actually makes it worse. **Fix:** remember the identity
across reloads so re-joining just works, or clearly tell them recovery needs a new invite.

### MD-02 — A round can finalise on a garbled total *(accepted)*
The server decides a round is "done" by counting submitted answers, but it doesn't insist that
all the behind-the-scenes key-exchange finished first. A buggy or malicious participant could
therefore produce a meaningless "average." **Why we accept it:** this is really the same as the
already-known "a dishonest input can skew the result" limit — someone who can submit a bad answer
can already mess things up, so adding this check buys nothing security-wise. Recorded so it isn't
re-discovered as new. (Optional nicety: only mark a round "done" once the key-exchange is also
complete.)

### MD-03 — A slow round gets cleaned up while still in progress *(accepted)*
Sessions are deleted 30 minutes after they're **created**, not 30 minutes after the last activity.
So a genuinely slow round (people in different time zones, say) can be wiped mid-flight, and the
access token expires at the same moment. **Why we accept it:** fine for a fast demo, and the
timings are deliberately aligned. Only worth changing if long rounds ever become a real use case.

---

## 2 · Does it work across devices and browsers?

### MD-04 — It silently needs a secure (HTTPS) connection *(should fix; critical if you ever demo across phones on a local network)*
The cryptography this app relies on only exists in the browser over a secure connection (HTTPS,
or directly on your own machine). A natural way to demo across phones is to serve it on a local
network using a plain address — but that **isn't** a secure connection, so every participant's
page dies with an unexplained error. There's no friendly check for this today. **Fix:** detect it
on page load and show a clear "this needs HTTPS or localhost" message, plus a README note that
local-network demos must use the secure live URL.

### MD-05 — Comma-decimal regions and phone keypads can mangle the figure *(should fix, minor)*
In places that write decimals with a comma ("42,5"), the figure input can silently chop it to 42
or reject it — and this is the one number the entire round depends on, with no feedback to the
user. **Fix:** use a decimal keypad on mobile, and either warn when the typed and understood
values differ or accept and normalise the comma.

---

## 3 · Is it reliable to host and redeploy?

### MD-06 — The one dependency isn't locked to a version *(should fix; config only)*
The app's single external library isn't pinned to a tested version. A redeploy weeks from now
would pull whatever's newest, and a breaking change could break the build or behaviour with no
change on our side — and no known-good version to roll back to. **Fix:** pin a tested version
range (or add a lock file).

### MD-07 — Running more than one machine quietly breaks rounds *(accepted)*
All the state lives in one machine's memory. The hosting is correctly pinned to a single machine,
but nothing in the app *enforces* that. If someone scaled it up to several machines, a
participant's steps could land on different machines that don't know about each other, and rounds
would break with no obvious cause. **Why we accept it:** the single-machine setting is the right
fix. Just keep that requirement loud in the deploy docs — don't "solve" it by adding shared state
(that means a database, which is out of scope).

---

## 4 · Are we promising more privacy than we deliver?

### MD-08 — The Step-6 explainer can be read as "signatures catch impersonation" *(should fix; wording)*
A sentence in the verification step says a "key substitution" would show as INVALID. But the one
impersonation scenario the docs openly admit to **is** a key substitution — and in that scenario
it verifies cleanly and is **not** caught. A careful reader could conclude impersonation is
caught when it isn't. This brushes against the owner's firm rule "don't claim signatures stop
impersonation." **Fix:** reword precisely and add an explicit "this does not catch an interceptor
who registered their key first."

### MD-09 — Anyone with a session code can read the round's metadata *(should fix)*
The read-only pages have no rate limit, so someone could rapidly try session codes to find live
rounds and read each one's label, participant list, who's submitted, the scrambled values, the
signatures, and the final average. **The good news:** the raw individual figures are **never**
exposed, and the scrambled values reveal nothing on their own — so the core privacy promise
holds. But "anyone who has the code can read the whole round" deserves to be stated plainly rather
than implied. Guessing codes is impractical at realistic speeds, which keeps this lower priority.
**Fix:** add a generous rate limit to the read pages (invisible to honest use), and/or document
that the code is effectively a read-pass for the round.

---

## 5 · Will a future developer accidentally undo a deliberate decision?

### MD-10 — Deliberate trade-offs aren't flagged in the code itself *(should fix; comments only)*
Several conscious decisions (most importantly "don't cap the size of a number") are written down
in the project docs but **not** in a comment next to the actual code they affect. The risk the
owner specifically flagged: the *next* likely edit touches exactly that piece of code, and a
developer (or AI agent) working there sees no warning and might "while I'm here" re-add a cap —
silently undoing a deliberate choice. Decisions written far from the code they govern don't
survive contact with a future editor. **Fix:** a one-line comment at each such spot pointing to
the reasoning.

### MD-11 — The protocol rules are hand-copied into three places *(should fix; test/docs)*
The exact format the maths depends on is written out separately in the server, the browser, and
the test — across two programming languages. Keeping three hand-maintained copies in sync is
fragile: change one and forget the others, and it breaks **silently**, caught only if someone
remembers to run the test (which is itself a third copy). You can't literally merge a
Python copy and a JavaScript copy, but you can pin the contract. **Fix:** add a fixed "known-good"
reference example that both sides check against, so any drift fails loudly.

---

## 6 · Are we testing the right things?

### MD-12 — The most valuable missing tests *(should fix; tests only)*
The current automated test runs one successful round for one group size. The highest-value things
**not** yet tested anywhere: (a) a sweep across all group sizes from 3 to 10 in one run; (b) the
"first answer wins, later changes rejected" rule — the load-bearing anti-cheating behaviour, which
is currently not checked by any automation; (c) replayed or expired security puzzles being
rejected; (d) tampered or expired access tokens being rejected; (e) the known-good reference
example from MD-11. The two worst live bugs and the single strongest design claim all live in
paths the current test never touches. **Fix:** one self-contained test file covering all of the
above, added to the safety gate. It's small, needs no new tooling, and extends (doesn't replace)
the existing test.

---

## Where each finding ended up on the main board

| This finding | Board code | Priority |
| --- | --- | --- |
| MD-01 | RB-27 | should fix |
| MD-02 | AC-11 | accepted |
| MD-03 | AC-12 | accepted |
| MD-04 | RB-28 | should fix |
| MD-05 | RB-29 | should fix |
| MD-06 | RB-30 | should fix |
| MD-07 | AC-13 | accepted |
| MD-08 | RB-31 | should fix |
| MD-09 | RB-32 | should fix |
| MD-10 | RB-26 | should fix (higher) |
| MD-11 | RB-33 | should fix |
| MD-12 | RB-34 | should fix |

*This was a self-check pass grounded in the actual code, not an outside certification. No new
false alarms were introduced.*
