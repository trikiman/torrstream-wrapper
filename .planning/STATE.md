---
gsd_state_version: 1.0
milestone: v2.2
milestone_name: robustness-coverage
status: in_progress
stopped_at: scaffolded; about to plan Phase 1 (API hygiene)
last_updated: "2026-05-14T23:35:00.000Z"
last_activity: 2026-05-14 -- v2.1 archived, v2.2 scaffolded with 3 phases (API hygiene, UX completeness, Test harness)
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 5
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (last updated 2026-05-14)

**Core value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.
**Current focus:** v2.2 — robustness fixes and a real test harness, derived from the 2026-05-14 E2E audit.

## Current Position

Milestone: v2.2 Robustness + Coverage — **IN PROGRESS**
Progress: [          ] 0%

| Phase | Plans | Status |
|-------|-------|--------|
| 1. API hygiene | 0/2 | Pending |
| 2. UX completeness | 0/2 | Pending |
| 3. Test harness | 0/1 | Pending |

## v2.2 Source

Driven by 8 todos captured in `.planning/todos/pending/` from the 2026-05-14 E2E feature audit:

| Todo | Phase / Plan | Requirement |
|------|------|------|
| `return-404-for-unknown-hash` | 1 / 01-01 | API-01 |
| `validate-hash-format` | 1 / 01-01 | API-02 |
| `reject-malformed-json-on-position-post` | 1 / 01-02 | API-03 |
| `cors-headers-on-static` | 1 / 01-02 | API-04 |
| `file-picker-modal-multi-file-torrents` | 2 / 02-01 | UX-01 |
| `add-download-ui-per-file` | 2 / 02-01 | UX-02 |
| `fix-slow-theme-transition` | 2 / 02-02 | UX-03 |
| `e2e-test-harness` | 3 / 03-01 | QUAL-04, QUAL-05 |

## Last v2.1 Outcome

Shipped 2026-05-12. Plyr → Vidstack swap, audio regression fixed, Lampa plugin contract preserved, Oracle production topology documented, MCP E2E 20/20 PASS. Archived to `.planning/milestones/v2.1-ROADMAP.md`. Tagged `v2.1`.

## AWS Status

- TorrStream services on AWS (`13.60.174.46`) are **stopped and disabled**: `caddy`, `torrserver`, `flask-wrapper`. Orphan `python app.py` killed.
- **EC2 instance itself preserved** per user choice — box shared with co-tenants.
- AWS GitHub webhook deactivated.
- Full EC2 termination deferred to user action from AWS console.

## Open Backlog (queued for v2.3+)

- **QUAL-03**: User-driven iOS Safari manual walkthrough (10-step guide in `docs/SMOKE-TESTS.md`).
- **PROD-01..05**: Base path config, user auth, richer metadata, chapters, subtitles in Vidstack.
- **ENG-01/02**: Module split + pinned dependency manifest.
- **INFRA-04**: Re-migrate to ARM Ampere if `oracle-hunter` catches capacity.

## Blockers / Concerns

None. v2.2 scaffold is in place; ready to plan Phase 1.

## Session Continuity

Last session: 2026-05-14 23:35 UTC (scaffolded v2.2 from 2026-05-14 E2E audit todos)
Stopped at: ready to plan Phase 1 (API hygiene)
Resume file: None
