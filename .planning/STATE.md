---
gsd_state_version: 1.0
milestone: v2.3
milestone_name: lampa-parser-shim
status: in_progress
stopped_at: scaffolded; about to implement Plan 01-01
last_updated: "2026-05-22T02:35:00.000Z"
last_activity: 2026-05-22 -- v2.2 archived, v2.3 scaffolded (single phase, 1 plan, 2 reqs)
progress:
  total_phases: 1
  completed_phases: 0
  total_plans: 1
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (last updated 2026-05-14)

**Core value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.
**Current focus:** v2.3 — Lampa parser shim. Make TorrStream usable as the Lampa torrent-search parser so jac.red mirror flips and ISP blocks stop killing search.

## Current Position

Milestone: v2.3 Lampa parser shim — **IN PROGRESS**
Progress: [          ] 0%

| Phase | Plans | Status |
|-------|-------|--------|
| 1. Lampa parser shim | 0/1 | Pending |

## Why this milestone

2026-05-17 user-blocking incident:
- `http://jac.red` (Lampa's default HTTP fetch) intermittently blocked by user's ISP.
- Workaround: switch Lampa's `jackett_url` to `https://jac.red` — works but fragile.
- Each time jacred mirror is rotated by the upstream maintainers OR HTTPS gets selectively throttled, user has to manually update Lampa settings again.

Robust fix:
- TorrStream wrapper already proxies jac.red via `/api/search` (transformed shape).
- Add `/api/v1.0/torrents` that proxies the **raw jacred shape** — Lampa speaks this natively.
- Lampa points at `https://tv.trikiman.shop` once. Done.
- TorrStream's `JACRED_URL` env var lets ops swap mirrors without code changes.

## Last v2.2 Outcome

Shipped 2026-05-14. API hygiene (404/400 contracts, hash validation, CORS scope) + UX completeness (per-file download UI, theme toggle 1432ms→16ms) + pytest harness (67 tests with CI hook). Archived to `.planning/milestones/v2.2-ROADMAP.md`. Tagged `v2.2`.

## AWS Status

- TorrStream services on AWS (`13.60.174.46`) **stopped and disabled**. Instance preserved per user (shared with co-tenants).
- AWS GitHub webhook deactivated. Oracle (`158.101.214.234`) is sole production.

## Open Backlog (queued for v2.4+)

- **QUAL-03**: User-driven iOS Safari manual walkthrough (10-step guide in `docs/SMOKE-TESTS.md`).
- **PROD-01..05**: Base path config, user auth, richer metadata, chapters, subtitles in Vidstack.
- **ENG-01/02**: Module split + pinned dependency manifest.
- **INFRA-04**: Re-migrate to ARM Ampere if `oracle-hunter` catches capacity.
- **TEST-01**: Playwright UI suite.
- **LAMPA-03** (potential): Multi-mirror failover inside the wrapper.

## Blockers / Concerns

None. Plan 01-01 is small (~30-50 lines of Python + 2-3 tests).

## Session Continuity

Last session: 2026-05-22 02:35 UTC
Stopped at: v2.3 scaffolded; ready to implement Plan 01-01
Resume file: None
