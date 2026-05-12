---
gsd_state_version: 1.0
milestone: v2.1
milestone_name: player-ux-ios
status: completed
stopped_at: v2.1 Player UX + iOS readiness shipped
last_updated: "2026-05-12T23:55:00.000Z"
last_activity: 2026-05-12 -- v2.1 complete, Vidstack live, AWS services stopped
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 5
  completed_plans: 5
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (last updated 2026-05-12)

**Core value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.
**Current focus:** Milestone closure — optional user-driven iOS walkthrough pending.

## Current Position

Milestone: v2.1 Player UX + iOS readiness — **COMPLETE**
Progress: [██████████] 100%

## Shipped in v2.1 (2026-05-12)

- **Player**: Plyr 3.7.8 → Vidstack 1.12.13. Default video layout with built-in double-tap ±10s seek, tap-to-toggle play/pause, native fullscreen, PiP where supported.
- **Audio regression fixed**: Root cause was a duplicate `<video>` element when both the template and Vidstack each inserted one. Now Vidstack owns a single `<video>`; audio plays by default.
- **Lampa plugin preserved**: No plugin changes; contract (find `<video>` element, read/write `currentTime`/`duration`) still holds against Vidstack's internal video element.
- **Service worker**: Cache bumped to `v4`; shell assets now reference Vidstack CDN URLs. Opaque-response tolerance added previously still protects install against CDN hiccups.
- **Auto-warmup for cold TorrServer state**: `/api/files` issues a 0-byte range probe against `/stream/...` when it gets empty file_stats, so first click on a migrated torrent now returns the file list immediately (no "no video files" flash).
- **Docs**: `docs/DEPLOYMENT.md` documents the Oracle production topology (host, paths, systemd units, auth locations). `docs/SMOKE-TESTS.md` adds a production smoke section and a 10-step iOS Safari walkthrough.
- **Smoke**: `scripts/smoke_prod.py` updated to check for `vidstack=True` in the shell. 9/9 PASS on final run.

## Validated in this session

- **MCP E2E (20/20 PASS)** against live `tv.trikiman.shop`: shell, library, SW, single video, audio+video decoding, default unmuted, Vidstack gestures, playsinline, fullscreen-capable, wrapper UI save, seek+save, Lampa plugin load+hook+resume+flush, CORS preflight.
- **API suite (5/5 PASS)**: TorrServer auth enforced (401 without creds, 200 with), add/remove torrent round-trip, status endpoint shape.
- **Production smoke (9/9 PASS)**: shell, manifest, SW, Lampa plugin asset, status, library, search, file list, CORS.

## AWS Status

- TorrStream services on AWS (`13.60.174.46`) are **stopped and disabled**: `caddy`, `torrserver`, `flask-wrapper`. Orphan `python app.py` on port 5000 killed. No torrstream ports listening.
- **EC2 instance itself preserved** per user choice — box shared with saleapp/VLESS co-tenants.
- AWS GitHub webhook was deactivated during v2.1 Phase 1.
- Full EC2 termination deferred to user action from the AWS console.

## Open Backlog (not blocking; queued for v2.2+)

- **QUAL-03 / iOS manual walkthrough**: User-driven; 10-step guide in `docs/SMOKE-TESTS.md`. MCP validation covered the server contract; remaining gaps are Safari-specific codec + touch behavior.
- **INFRA-04**: Re-migrate to ARM Ampere if `oracle-hunter` eventually catches capacity.
- **PROD-01..05**: Base path config, user auth, richer metadata, chapters, subtitles in Vidstack.
- **ENG-01/02**: Module split + pinned dependency manifest.

## Blockers / Concerns

None. v2.1 is done.

## Session Continuity

Last session: 2026-05-12 23:55 UTC
Stopped at: v2.1 milestone complete; ready to archive or start v2.2
Resume file: None
