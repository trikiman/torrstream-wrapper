---
phase: 02-vidstack-swap
milestone: v2.1
subsystem: docs+ops
tags: [docs, smoke, aws-decommission, vidstack]
provides:
  - Updated SMOKE-TESTS.md with production smoke + iOS walkthrough
  - Updated DEPLOYMENT.md with Oracle production topology
  - AWS TorrStream services stopped and disabled (instance preserved for saleapp/VLESS co-tenants)
  - Orphan standalone python app.py process killed
key-decisions:
  - "Stop AWS services but DON'T terminate the EC2 instance itself (shared with unrelated projects)"
  - "Full EC2 termination deferred to user action from AWS console"
  - "AWS webhook already deactivated during v2.1 Phase 1 webhook wiring"
requirements-completed: [QUAL-02, QUAL-03, CUT-03 (partial - services down, instance preserved)]
duration: 30min
completed: 2026-05-12
commits:
  - c39c8dd docs: Oracle production topology + Vidstack/iOS smoke guide
---

# Phase 2 Summary: iOS Verification + AWS Decommission

**Outcome:** Production smoke passes 25/25 via MCP + API suites. Docs reflect Oracle + Vidstack reality. AWS torrstream services stopped and disabled — instance preserved at user request (shared with unrelated projects).

## Accomplishments

### Smoke + Docs

- `scripts/smoke_prod.py` already updated in Phase 1; 9/9 PASS confirmed on the final build
- `docs/SMOKE-TESTS.md` gained a "Production Smoke" section (points at `smoke_prod.py`, notes the `vidstack=True` marker) and a 10-step "iOS Safari Walkthrough" covering PWA install, Vidstack double-tap seek, fullscreen, PiP, Lampa sync
- `docs/DEPLOYMENT.md` gained a "Production Deployment (Oracle Cloud)" section with the host, paths, systemd units, credentials file locations, and SSH access

### MCP E2E (20/20)

Ran in-browser E2E suite against live `tv.trikiman.shop` post-Vidstack swap:

| # | Scenario | Result | Evidence |
|---|---|---|---|
| 1 | Shell loads | ✅ | "TorrStream" present |
| 2 | Library shows 3 torrents | ✅ | all 3 titles |
| 3 | Continue row visible | ✅ | "Продолжить просмотр" |
| 4 | Single `<video>` element | ✅ | no duplicate |
| 5 | Video duration loaded | ✅ | 634.6s |
| 6 | Audio decoded | ✅ | 117 KB |
| 7 | Video decoded | ✅ | 693 KB |
| 8 | Default unmuted | ✅ | volume=1, muted=false |
| 9 | Double-tap ±10s gestures | ✅ | 5 gestures incl. seek:±10 |
| 10 | SW registered + active | ✅ | `/sw.js` |
| 11 | Fullscreen capable | ✅ | `data-can-fullscreen` |
| 12 | playsinline set | ✅ | |
| 13 | Position save via UI | ✅ | 103s / 634s |
| 14 | Seek + save | ✅ | 51 after seek to 50 |
| 15 | Lampa plugin loads | ✅ | |
| 16 | Player listener hooked | ✅ | |
| 17 | `Lampa.Player.play` wrapped | ✅ | |
| 18 | Plugin resume seeks video | ✅ | ct=200 matched seeded 200 |
| 19 | Plugin saves on pause | ✅ | pos=200 |
| 20 | CORS preflight | ✅ | ACAO=* |

### API suite (5/5)

| Scenario | Result |
|---|---|
| TorrServer direct no-auth → 401 | ✅ |
| TorrServer direct with-auth → 200 | ✅ |
| Add magnet torrent | ✅ Cosmos Laundromat added |
| Remove torrent | ✅ clean |
| Status endpoint shape | ✅ ts.ok=true, count=3 |

### AWS Decommission (partial per user choice)

- `caddy` on AWS: stopped + disabled
- `torrserver` on AWS: stopped + disabled
- `flask-wrapper` on AWS: already inactive; disabled
- Orphan `/home/ubuntu/torrstream/.venv/bin/python app.py` on port 5000: killed
- All torrstream-related listening ports on AWS are now idle
- **EC2 instance NOT terminated** — user chose "stop services only, reversible". Instance continues hosting saleapp/VLESS. Full termination deferred to user action from the AWS console when they decide.

### Cleanup

- Big Buck Bunny position reset to 0 after E2E testing
- Synthetic test torrent (Cosmos Laundromat) removed cleanly
- AWS GitHub webhook already deactivated (during v2.1 Phase 1)

## Remaining Open Items

- **CUT-03 partial**: AWS EC2 instance not terminated (user preserved for co-tenants). If user wants to fully terminate later, they can do so from the AWS console with no impact on TorrStream since all its services are stopped + disabled.
- **QUAL-03 partial**: iOS manual walkthrough not executed (that's a user-driven step). MCP validation covered the server-side contract iOS will exercise; what remains is Safari-specific codec + touch behavior.

## Files Changed

| File | Change |
|---|---|
| `docs/DEPLOYMENT.md` | Added Oracle production section; removed webhook-test markers |
| `docs/SMOKE-TESTS.md` | Added Production Smoke + iOS walkthrough sections |

## Issues Encountered

None that blocked the phase.

## Next

Milestone v2.1 is **ready to close**. User's iOS walkthrough can happen independently; if it surfaces anything, it goes into v2.2 backlog.

---
*Phase 2 completed 2026-05-12. Commit `c39c8dd`.*
