# CLAUDE.md

This public file is a minimal bootstrap for Claude Code sessions in this repository.

Private, machine-local project guidance lives outside the committed tree at:

`.git\agents\repo-private\CLAUDE.md`

Before substantive work, if that file exists, read it first. Also read
`.git\agents\memory\MEMORY.md` and any linked note that matches the task.
When private guidance refers to files that are no longer public, resolve those paths under
`.git\agents\repo-private\`.

If the private files are absent, use the public instructions below.

## Running The App

```bash
python server.py
```

The app serves on `http://127.0.0.1:8765`. Install dependencies with:

```bash
pip install -r requirements.txt
```

## Verification

Run these against a freshly started server:

```bash
python verify_round.py
python verify_round.py 10
python tests.py
```

Run the browser numeric contract tests without the server:

```bash
node tests_numeric.js
```

Run the auth-layer suite any time - it needs no pre-running server (it tests in-process and
spawns its own password-configured instance on a scratch port):

```bash
python tests_auth.py
```

## Public Scope

Keep the public repository focused on the demo source, user-facing docs, and reproducible assets.
Local agent memory, the full review working archive, and personal workflow instructions should
remain under `.git\agents\` and must not be committed. The one deliberate exception is
`docs/review/`: a curated public slice (campaign summary + selected council transcripts, published
2026-07-03) that substantiates the README's review claims - keep it in sync if the review story
changes, but do not publish further private material without an explicit owner decision.
