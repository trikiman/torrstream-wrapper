---
gsd_state_version: 1.0
milestone: v2.3
milestone_name: lampa-parser-shim
status: completed
stopped_at: v2.3 Lampa parser shim shipped
last_updated: "2026-05-22T01:35:00.000Z"
last_activity: 2026-05-22 -- v2.3 complete (1 phase, 1 plan, 3 reqs, 13 new tests)
progress:
  total_phases: 1
  completed_phases: 1
  total_plans: 1
  completed_plans: 1
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (last updated 2026-05-14)

**Core value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.
**Current focus:** Milestone closure — ready to archive and start v2.4 (fix auto-deploy webhook).

## Current Position

Milestone: v2.3 Lampa parser shim — **COMPLETE**
Progress: [██████████] 100%

| Phase | Plans | Status |
|-------|-------|--------|
| 1. Lampa parser shim | 1/1 | ✓ Complete |

## Shipped in v2.3 (2026-05-22)

- `/api/v1.0/torrents` (jacred shape, `parser_torrent_type=jacred`) — proxy to JACRED_URL preserving body verbatim (commit 9fb813c)
- `/api/v2.0/indexers/all/results` (Jackett shape, `parser_torrent_type=jackett`) — proxy to same upstream (commit 254c58f)
- Both routes share `_lampa_proxy()` helper; auto-inject JACRED_KEY when caller omits apikey; return 502 + `{}` on upstream failure
- CORS `Access-Control-Allow-Origin: *` on both `/api/v1.0/*` and `/api/v2.0/*`
- 11 new contract tests + 2 new integration tests
- Lampa client switched: `jackett_url: https://tv.trikiman.shop` — verified live with 20 Matrix torrents rendered

## Validated in this session

- Pytest smoke 68/68 PASS in 0.93s.
- Pytest integration 9/12 PASS, 3 skipped (empty library).
- curl on Oracle host: `/api/v1.0/torrents?search=matrix` → 200 / 731 KB; `/api/v2.0/indexers/all/results?Query=matrix` → 200 / 2553 bytes.
- Lampa from lampa.mx browser tab after switching parser: 20 torrent_items rendered, all real Russian Matrix releases.

## Mid-phase findings (captured for v2.4)

- **Auto-deploy webhook silently broken since project inception**: app.py `github_webhook` defaults `TORRSTREAM_SERVICE` to `torrstream.service`, but the real systemd unit on Oracle is `flask-wrapper.service`. The Popen-based restart fails silently. Worked around for v2.3 via manual `ssh ubuntu@oracle && git pull && systemctl restart flask-wrapper.service`. Captured at `.planning/todos/pending/2026-05-22-fix-webhook-unit-name.md`.
- All v2.x Python-only changes since the May 16 process start were silently NOT loaded into the running Flask process. v2.2 Plan 1.1 hash validation only worked because someone manually restarted around May 16 during the resume bug iteration day.

## AWS Status

- TorrStream services on AWS (`13.60.174.46`) **stopped and disabled**. Instance preserved per user.
- AWS GitHub webhook deactivated. Oracle (`158.101.214.234`) is sole production.

## Open Backlog (queued for v2.4+)

- **fix-webhook-unit-name** (NEW, P0 for v2.4): the auto-deploy bug. See todo file.
- **QUAL-03**: User-driven iOS Safari manual walkthrough.
- **PROD-01..05**: Base path config, user auth, richer metadata, chapters, subtitles in Vidstack.
- **ENG-01/02**: Module split + pinned dependency manifest.
- **INFRA-04**: Re-migrate to ARM Ampere if `oracle-hunter` catches capacity.
- **TEST-01**: Playwright UI suite.
- **LAMPA-03** (potential): Multi-mirror failover inside the wrapper.

## Blockers / Concerns

None. v2.3 is done.

## Session Continuity

Last session: 2026-05-22 01:35 UTC
Stopped at: v2.3 complete; ready to archive milestone or start v2.4 (auto-deploy fix should be v2.4 P0)
Resume file: None
