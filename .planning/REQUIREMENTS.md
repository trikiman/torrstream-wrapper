# Requirements: TorrStream

**Defined:** 2026-04-05 (v1.0), amended through 2026-05-22
**Core Value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.

## v1 + v2.0 + v2.1 + v2.2 (shipped, archived)

See archives:
- `.planning/milestones/v1.0-REQUIREMENTS.md` — base requirements (LIBR, PLAY, SYNC, MGMT, DISC, DELV, QUAL).
- `.planning/milestones/v1.1-REQUIREMENTS.md` — SYNC-03 cross-client position sync.
- `.planning/milestones/v2.0-REQUIREMENTS.md` — INFRA, MIGR, CUT, SEC.
- `.planning/milestones/v2.1-REQUIREMENTS.md` — PLAY-03..07, DELV-05..06, QUAL-02..03.
- `.planning/milestones/v2.2-REQUIREMENTS.md` — API-01..04, UX-01..03, QUAL-04..05.

## v2.3 Requirements (active — Lampa parser shim)

Source: 2026-05-17 user-blocking incident — plain `http://jac.red` blocked on user's
network; even after switching to `https://jac.red` the failure mode is fragile to
mirror flips and selective HTTPS throttling.

### Lampa shim

- [ ] **LAMPA-01**: `GET /api/v1.0/torrents` on TorrStream proxies to `JACRED_URL/api/v1.0/torrents`, forwarding all query params and returning the **raw upstream response body** (flat array of jacred records — `{title, size, sid, tracker, magnet, ...}`). Lampa parses the response identically to a direct jac.red call.

- [ ] **LAMPA-02**: `/api/v1.0/torrents` includes `Access-Control-Allow-Origin: *` so a Lampa client running on `lampa.mx` (or any other origin) can `fetch()` it cross-origin without a preflight failure. Pair with the existing `/api/position/*` and `/static/*` CORS scoping.

### Out of scope for v2.3

- Multi-mirror failover inside the wrapper (Plan 1 sticks with the single configured `JACRED_URL`; failover is v2.4+ if needed).
- Caching of search results.
- Returning a Cloudflare/CDN tier in front of TorrStream.

## Future (v2.4+ backlog)

- **PROD-01..05**: Base path config, user auth, richer metadata, chapters, subtitles in Vidstack.
- **ENG-01/02**: Module split + pinned dependency manifest.
- **INFRA-04**: Re-migrate to ARM Ampere if `oracle-hunter` catches capacity.
- **TEST-01**: Playwright UI suite (theme timing, picker walkthrough, download click-through).
- **LAMPA-03** (potential): Multi-mirror failover for the parser shim.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reimplementing TorrServer | Not the purpose of the wrapper |
| Native mobile/TV apps | Browser delivery + Lampa plugin is sufficient |
| Social or collaborative features | Project is single-user/self-hosted |
| Promoting `positions.json` to a database | Not needed at current scale |
| Moving frontend into a bundler / SPA framework | Vidstack ships web components over CDN |

## Traceability — v2.3

| Requirement | Phase | Plan | Status |
|-------------|-------|------|--------|
| LAMPA-01, LAMPA-02 | v2.3 Phase 1 | 01-01 | Pending |

**Coverage so far:**
- v1: 13 / 13 shipped
- v1.1: 1 / 1 shipped
- v2.0: 10 / 9 shipped + 1 deferred
- v2.1: 9 / 8 shipped + 1 user-driven deferred
- v2.2: 9 / 9 shipped
- **v2.3: 2 / 0 shipped (active)**

---
*v2.3 amendments: 2026-05-22 (LAMPA-01..02) — driven by 2026-05-17 jac.red blocking incident*
