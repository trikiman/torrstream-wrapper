---
gsd_state_version: 1.0
milestone: v2.2
milestone_name: robustness-coverage
status: completed
stopped_at: v2.2 Robustness + Coverage shipped
last_updated: "2026-05-14T23:55:00.000Z"
last_activity: 2026-05-14 -- v2.2 complete (3 phases, 5 plans, 9 reqs, 67 tests)
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 5
  completed_plans: 5
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (last updated 2026-05-14)

**Core value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.
**Current focus:** Milestone closure — ready to archive and start v2.3.

## Current Position

Milestone: v2.2 Robustness + Coverage — **COMPLETE**
Progress: [██████████] 100%

| Phase | Plans | Status |
|-------|-------|--------|
| 1. API hygiene | 2/2 | ✓ Complete |
| 2. UX completeness | 2/2 | ✓ Complete |
| 3. Test harness | 1/1 | ✓ Complete |

## Shipped in v2.2 (2026-05-14)

- **API hygiene** (Phase 1):
  - `/api/files`, `/api/position` GET, `/api/remove` return 404 for well-formed but unknown hashes (was: 200 with empty/zero state).
  - All hash routes reject malformed hashes with 400 invalid hash. Lowercase normalization at persistence + lookup.
  - `POST /api/position` rejects malformed JSON with 400 (was: silent 200), missing `position` with 400.
  - `/static/*` exposes `Access-Control-Allow-Origin: *` so cross-origin `fetch()` of the Lampa plugin source works.
  - Removed corner cases noted by 2026-05-14 audit; `/api/remove` returns 502 on TS failure (was: 200 with ok:false).

- **UX completeness** (Phase 2):
  - Per-file download UI: ⬇ Скачать button in Episode Panel rows + round download button in player header. iOS fallback opens new tab + toast.
  - Theme toggle: 1432ms → ≤16ms (instant). Implementation pivoted after three CSS-only attempts to JS-driven inline style write that bypasses Chrome's ~680ms style cascade recompute on this DOM.
  - File picker for multi-file torrents was already implemented (Episode Panel) — discovered during this milestone; original audit grep used wrong selectors.

- **Test harness** (Phase 3):
  - 67 pytest tests across `tests/api/` (57 contract via Flask test client + mocked TorrServer) and `tests/integration/` (10 live read-only against `tv.trikiman.shop`).
  - `pytest.ini` markers: smoke / integration / e2e / cors. e2e gated behind opt-in.
  - `.github/workflows/tests.yml` runs smoke on every PR + push to main; integration nightly + on push.
  - `requirements-dev.txt` documents the dev dependency set.

- **Docs**:
  - `docs/SMOKE-TESTS.md` updated with pytest invocation as preferred path.
  - `.planning/codebase/STACK.md` no longer claims "no automated test framework".

## Validated in this session

- **Phase 1**: 11/11 backend contract checks via chrome-devtools MCP against `tv.trikiman.shop` after auto-deploy. Cross-origin checks from `lampa.mx` (Lampa plugin still loads, position sync still active).
- **Phase 2**: theme reach-target measured at 0ms (next paint frame). Download anchor URL `download="Matrix.1999.BDRip.avi"`, server returns 206 `Content-Range: bytes 0-15/1571913728`.
- **Phase 3**: `pytest -m smoke` 57/57 PASS in 0.58s. `pytest -m integration` 10/10 PASS in 7.48s against live wrapper.

## Source todos (closed)

All 8 todos from the 2026-05-14 E2E audit are now in `.planning/todos/completed/`. Each maps to a v2.2 requirement and a specific commit. See `.planning/milestones/v2.2-REQUIREMENTS.md` for the full mapping.

## Open Backlog (queued for v2.3+)

- **QUAL-03**: User-driven iOS Safari manual walkthrough (10-step guide in `docs/SMOKE-TESTS.md`). Carried from v2.1.
- **PROD-01..05**: Base path config, user auth, richer metadata, chapters, subtitles in Vidstack.
- **ENG-01/02**: Module split + pinned dependency manifest.
- **INFRA-04**: Re-migrate to ARM Ampere if `oracle-hunter` catches capacity.
- **TEST-01** (new): Playwright UI suite — theme timing assertion, picker walkthrough, download click-through. Covered today by chrome-devtools MCP manual runs; promote when manual coverage becomes insufficient.

## AWS Status

- TorrStream services on AWS (`13.60.174.46`) **stopped and disabled**. Instance preserved per user (shared with co-tenants).
- AWS GitHub webhook deactivated. Oracle (`158.101.214.234`) is sole production.

## Blockers / Concerns

None. v2.2 is done.

## Session Continuity

Last session: 2026-05-14 23:55 UTC
Stopped at: v2.2 complete; ready to archive milestone or start v2.3
Resume file: None
