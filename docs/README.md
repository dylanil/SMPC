# docs/

Project documentation and the **open review apparatus**. (The app itself lives at the repo root and
under [`public/`](../public/); start with the top-level [`README.md`](../README.md).)

- **[review/](review/)** - the review apparatus. This repo is reviewed adversarially in the open;
  that depth is a deliberate portfolio signal, not scaffolding.
  - **[review/RELEASE_BOARD.md](review/RELEASE_BOARD.md)** - the canonical, deduplicated triage of
    every finding (stable `RB-` / `AC-` / `FP-` IDs). The single source of truth for what to do and
    in what order.
  - **[review/council/](review/council/)** - dated records of [`/review-council`](../.claude/skills/review-council/SKILL.md)
    runs: a gated, proportionate expert review of one proposed change *before* it is implemented.
  - **`review/run-<date>/`** - dated full multi-agent review runs (eight domain reviews + independent
    meta second-opinions + a debate). Append-only snapshots; earlier runs predate later conventions.
- **[PRODUCTION_READINESS_PLAN.md](PRODUCTION_READINESS_PLAN.md)** - strategy wrapper: how the demo
  moves *toward* production-ready within its deliberately lightweight scope.
- **[REVIEW_ORCHESTRATION.md](REVIEW_ORCHESTRATION.md)** - brief for the heavy periodic whole-repo
  multi-agent audit (the heavyweight companion to the per-proposal council).
- **[assets/](assets/)** - dev-only Pillow generators (`make_*.py`) that are the single editable
  source for the committed diagrams, the README screenshots, and the social/OG image. Re-run a
  generator to regenerate its image; never hand-edit the images.
