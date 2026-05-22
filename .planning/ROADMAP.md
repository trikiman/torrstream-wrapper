# Roadmap: TorrStream

## Status

**No active milestone.** Last shipped: **v2.3 Lampa parser shim** (2026-05-22).

To start the next milestone:

- `/gsd-new-milestone` — questioning → research → requirements → roadmap.
- Or review captured ideas: `/gsd-review-backlog`, `/gsd-check-todos`.

## v2.4 candidates (queued from prior milestones)

- **fix-webhook-unit-name** (NEW from v2.3): auto-deploy webhook silently broken — captured at `.planning/todos/pending/2026-05-22-fix-webhook-unit-name.md`. Probably worth fixing first in v2.4 so subsequent deploys are smoother.
- **QUAL-03**: User-driven iOS Safari manual walkthrough.
- **PROD-01..05**: Base path config, user auth, richer metadata, chapters, subtitles in Vidstack.
- **ENG-01/02**: Module split + pinned dependency manifest.
- **INFRA-04**: Re-migrate to ARM Ampere if `oracle-hunter` catches capacity.
- **TEST-01**: Playwright UI suite.
- **LAMPA-03** (potential): Multi-mirror failover for the parser shim.

## Archived Milestones

### v2.3 Lampa parser shim (shipped 2026-05-22)
- 1 phase, 1 plan, 3 reqs. `/api/v1.0/torrents` + `/api/v2.0/indexers/all/results` proxy routes; Lampa now uses TorrStream as parser. See `.planning/milestones/v2.3-ROADMAP.md`.

### v2.2 Robustness + Coverage (shipped 2026-05-14)
- 3 phases, 5 plans, 9 reqs, 67 tests. API hygiene + UX completeness + pytest harness. See `.planning/milestones/v2.2-ROADMAP.md`.

### v2.1 Player UX + iOS readiness (shipped 2026-05-12)
- 2 phases, 5 plans. Plyr→Vidstack swap, audio fix. See `.planning/milestones/v2.1-ROADMAP.md`.

### v2.0 Oracle Migration (shipped 2026-05-12)
- 3 phases, 7 plans. AWS→Oracle migration. See `.planning/phases/01-oracle-baseline/`.

### v1.1 Cross-Client Position Sync (shipped 2026-04-29)
- 1 phase, 2 plans. See `.planning/milestones/v1.1-ROADMAP.md`.

### v1.0 TorrStream (shipped 2026-04-24)
- 4 phases, 11 plans. See `.planning/milestones/v1.0-ROADMAP.md`.
