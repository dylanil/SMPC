# docs/

Public project documentation. The app itself lives at the repo root and under
[`public/`](../public/); start with the top-level [`README.md`](../README.md).

- **[PRODUCTION_READINESS_PLAN.md](PRODUCTION_READINESS_PLAN.md)** - public summary of the
  production-readiness posture for this lightweight demo.
- **[CHANGELOG.md](CHANGELOG.md)** - concise history of notable hardening, UX, and public-demo changes.
- **[review/](review/)** - how the project was reviewed: the audit-campaign summary and two
  verbatim review-council transcripts, published as evidence for the README's review claims.
- **[assets/](assets/)** - dev-only asset generators and committed images used by the README,
  pages, and link previews. This includes the public review-council workflow diagram.
  Re-run a generator to regenerate its image; never hand-edit the images.

The full review working archive (every per-run domain review and meta audit), agent memory, and
workflow instructions live locally under `.git/agents/` and are intentionally not part of the
public repository; [`review/`](review/) is the curated public slice.
