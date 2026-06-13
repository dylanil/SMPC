# CLAUDE.md — plain-English version

> Plain-language companion to [`CLAUDE.md`](../CLAUDE.md), the file that tells AI coding
> assistants how to work in this repo. The original is the source of truth and is unchanged.
> If the two ever disagree, trust the original. This version is here so a non-engineer can
> understand what the project is made of and what decisions are baked in.

## What CLAUDE.md is

It's an instruction sheet for any AI assistant (like Claude) editing this codebase. It explains
how to run the app, how the pieces fit together, and — most importantly — which design choices
are **deliberate** so a future assistant doesn't "helpfully" undo them. You can read it as a
plain-English tour of the whole system.

## Running it

`python server.py` starts the app on a local address. The only external library it needs is one
cryptography package. There's no build step and no fancy test suite — just one end-to-end check
script (`verify_round.py`) that runs a full pretend round and confirms the masking maths cancels
out exactly. That script is deliberately a *separate, independent* implementation of the rules,
so if someone changes the protocol on one side but not the other, the check fails loudly.

## The shape of the system

- **Lots of browser tabs** act as the participants (3–10 of them), plus one tab as the
  aggregator. They all talk to **one small Python server** that keeps everything in memory,
  organised by session code.
- **Sessions are created on demand** by the aggregator. The home page is just a static landing
  page — it never creates or shows a session code. (This is a firm rule: the aggregator is the
  only thing that mints codes.)
- **Multiple independent sessions can run at once** without interfering, and nothing is
  hard-coded to "3 participants" — the count is chosen per session.

## The security layers (the load-bearing part)

Four layers protect each participant's submissions:

1. **A personal invite** that you redeem once to claim your slot.
2. **A tamper-proof token** the server hands back, used for the rest of your submissions. The
   server doesn't store it — it re-checks its own signature each time, which keeps things simple.
3. **Digital signatures** on each submission, so the server (and other participants) can verify
   each one came from the right person and wasn't altered.
4. **First-write-wins:** the first value you commit to a slot is locked. An identical resend is
   fine (so network retries don't break), but trying to *change* it is rejected. This stops the
   "watch everyone else, then change mine to steer the average" attack.

**An honest limitation that's flagged repeatedly:** because identities are made fresh in the
browser each session, none of this stops a determined impersonator who intercepts an invite and
claims the slot first. The cryptography is sound; the missing piece is a pre-established "who's
who" registry, which is deliberately out of scope. The docs are careful never to over-claim here.

## Input rules and a key owner decision

Submissions are size-checked (anything over 16 KB is rejected) and shape-checked. But there is
**deliberately no cap on how large a number you can submit.** This is an explicit owner decision,
not an oversight: the app should work for any scale (pennies to millions), a simple size cap
wouldn't actually stop someone skewing the average anyway (that needs heavier cryptography that's
out of scope), and the overall request-size limit already blocks abusive payloads. The file
says, in effect: **do not keep re-proposing number caps.**

## The hardening and housekeeping layer

Over time the project grew a set of protective and tidiness features, each explained in the
original with full reasoning. In plain terms:

- **Optional aggregator password** to gate session creation/deletion and the aggregator page.
- **Per-visitor rate limits** and a small **proof-of-work puzzle** to deter flooding and abuse.
- **Auto-deletion of old sessions** and periodic sweeps of stale internal bookkeeping, so memory
  doesn't grow forever (described with a nice analogy: tearing the empty pages out of a
  guestbook instead of letting it grow).
- **A security header** that stops the pages being embedded in a malicious site.
- **The container runs as a non-admin user** for defence-in-depth.
- **A minimal access log** that deliberately never records request bodies or session codes, so
  secrets can't leak into the logs.
- **Rate-limit identity comes from the hosting platform's trusted client-IP header**, never from
  a header a visitor could fake.

## The shared crypto module and why it's sensitive

The actual masking and signing maths lives in one shared file (`smpc-core.js`) used by both the
participant and aggregator pages, so the two can never drift apart and compute different masks.
Several things (the curve, the exact label strings, the number-format conversions) **must match
between the browser and the server** or everything breaks silently. The original repeatedly
warns: change the protocol in the shared file and the server *together*, never one alone.

## Other documented design choices worth knowing

- **Fixed-point numbers:** decimals are handled by scaling everything up by a million and working
  in whole numbers, to avoid rounding errors.
- **Solo demo mode** lets one person simulate a full round in one tab — with a mandatory amber
  "Simulated round" warning that must never be removed (it's the only thing that keeps the demo
  honest, since one tab knows every number).
- **Single-instance deployment** is required because state is in memory.
- A note on the **legacy `index.html`** — an older standalone demo that should be left alone
  unless specifically asked about.

## The working agreement

The file also sets the workflow: commit and push after every meaningful change (the owner wants
a continuous history), use short commit messages explaining *why*, and — a practical note — the
AI's shell can't push directly, so the owner runs the push.
