# Requirements: TorrStream

**Defined:** 2026-04-05 (v1.0), amended 2026-05-11 (v2.0), 2026-05-12 (v2.1), 2026-05-14 (v2.2)
**Core Value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.

## v1 + v2.0 + v2.1 (shipped, archived)

See archives:
- `.planning/milestones/v1.0-REQUIREMENTS.md` — base requirements (LIBR, PLAY, SYNC, MGMT, DISC, DELV, QUAL).
- `.planning/milestones/v1.1-REQUIREMENTS.md` — SYNC-03 cross-client position sync.
- `.planning/milestones/v2.0-REQUIREMENTS.md` — INFRA, MIGR, CUT, SEC.
- `.planning/milestones/v2.1-REQUIREMENTS.md` — PLAY-03..07, DELV-05..06, QUAL-02..03.

## v2.2 Requirements (active — Robustness + Coverage)

Source: 2026-05-14 E2E feature audit (8 captured todos in `.planning/todos/pending/`).

### API hygiene

- [ ] **API-01**: `/api/files/<hash>`, `/api/position/<hash>` (GET), `/api/remove/<hash>` return **404** when the hash is unknown to both `positions.json` AND TorrServer's library, with the existing diagnostics body preserved.
- [ ] **API-02**: All hash-bearing routes reject hashes that don't match `^[0-9a-fA-F]{40}$|^[0-9a-fA-F]{64}$` with **400 invalid hash**. Hashes are normalized to lowercase before persistence.
- [ ] **API-03**: `POST /api/position/<hash>` rejects malformed JSON with **400 invalid JSON**, and missing/non-numeric `position` with **400 missing or invalid position**, while preserving CORS headers on error responses.
- [ ] **API-04**: `GET /static/*` exposes `Access-Control-Allow-Origin: *` so a Lampa-side `fetch('https://tv.trikiman.shop/static/lampa-sync.js', { mode: 'cors' })` succeeds.

### UX completeness

- [ ] **UX-01**: Clicking a multi-file torrent opens a file-picker modal listing every file with path, size, duration, viewed flag, resume position. Single-file torrents preserve current straight-to-player UX.
- [ ] **UX-02**: Each row in the file-picker has a **Скачать** (Download) anchor using `<a download="...">` against `/api/stream/...`. iOS Safari fallback shows a toast pointing at "Поделиться → Сохранить в Файлы".
- [ ] **UX-03**: Theme toggle full background color change reaches its target value within **≤350ms** wall-clock from click. Implementation: switch theming root from body class to `html[data-theme]`, scope transitions to specific properties.

### Quality

- [ ] **QUAL-04**: Every check in the 2026-05-14 E2E feature audit is a runnable test under `tests/api/`, `tests/integration/`, or `tests/ui/`. Tests are safe to run against prod (mutations capture+restore pre-state).
- [ ] **QUAL-05**: GitHub Actions runs `pytest -m smoke` on every PR and nightly against prod. `pytest -m e2e` runs nightly. `scripts/smoke_prod.py` retained but documented as thin pre-flight.

## Future (v2.3+ backlog)

- **PROD-01**: Wrapper supports configurable base paths and direct-root deployments.
- **PROD-02**: Wrapper supports authenticated user access.
- **PROD-03**: Wrapper provides richer metadata and poster normalization.
- **PROD-04**: In-player chapter markers for multi-episode torrents.
- **PROD-05**: Subtitle track selection in Vidstack (TorrServer's subtitle files).
- **ENG-01**: Backend is split into modules.
- **ENG-02**: Dependency versions are pinned in `requirements.txt`.
- **INFRA-04**: Re-migrate from x86-2 to ARM Ampere if `oracle-hunter` catches capacity.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reimplementing TorrServer | Not the purpose of the wrapper |
| Native mobile/TV apps | Browser delivery + Lampa plugin is sufficient |
| Social or collaborative features | Project is single-user/self-hosted |
| Rewriting `app.py` into modules during this milestone | Defer to v2.3+ (ENG-01) |
| Promoting `positions.json` to a database | Not needed at current scale |
| Moving to a JS bundler / SPA framework | Vidstack ships web components over CDN |

## Traceability — v2.2

| Requirement | Phase | Plan | Status |
|-------------|-------|------|--------|
| API-01, API-02 | v2.2 Phase 1 | 01-01 | Pending |
| API-03, API-04 | v2.2 Phase 1 | 01-02 | Pending |
| UX-01, UX-02 | v2.2 Phase 2 | 02-01 | Pending |
| UX-03 | v2.2 Phase 2 | 02-02 | Pending |
| QUAL-04, QUAL-05 | v2.2 Phase 3 | 03-01 | Pending |

**Coverage so far:**
- v1: 13 requirements / 13 shipped
- v1.1: 1 requirement / 1 shipped
- v2.0: 10 requirements / 9 shipped + 1 deferred
- v2.1: 9 requirements / 8 shipped + 1 user-driven deferred
- **v2.2: 9 requirements / 0 shipped (active)**

---
*v2.2 amendments: 2026-05-14 (API-01..04, UX-01..03, QUAL-04..05) — driven by 2026-05-14 E2E audit*
