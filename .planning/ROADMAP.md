# Roadmap: TorrStream

## Overview

Milestone v2.2 closes the gaps surfaced by the 2026-05-14 E2E feature audit:

- **API hygiene** — return proper 404s for unknown hashes, reject malformed JSON, validate hash format at the route boundary, expose CORS on `/static/*` so the Lampa plugin can be fetched cross-origin.
- **UX completeness** — implement the documented-but-missing download UI per file, add a file-picker modal for multi-file torrents (today's UI silently picks the largest file), and fix the slow theme transition (~1.4s vs declared 250ms).
- **Testing foundation** — promote the manual audit into a repeatable pytest + Playwright harness, port the 25-check audit, and wire smoke into CI.

Prior milestones (v1.0, v1.1, v2.0, v2.1) are archived under `.planning/milestones/`.

## Active Milestone: v2.2 Robustness + Coverage

### Phases

- [ ] **Phase 1: API hygiene** — `/api/files`, `/api/position`, `/api/remove`, `/static/*` get correct HTTP semantics (404 on unknown, 400 on malformed, hash validation, CORS).
- [ ] **Phase 2: UX completeness** — file-picker modal, per-file download UI, theme transition fix.
- [ ] **Phase 3: Test harness** — pytest + Playwright; port audit; CI hook.

### Phase Details

#### Phase 1: API hygiene

**Goal:** TorrStream's HTTP API behaves correctly for every documented edge case. Unknown hashes return 404, malformed JSON returns 400, hash format is validated at the route boundary, and `/static/*` is reachable from cross-origin `fetch()`.

**Depends on:** Nothing (independent of v2.1's frontend work).

**Requirements:** [API-01, API-02, API-03, API-04]

**Success Criteria:**
1. `GET /api/files/<unknown_hash>` returns **404** with diagnostics body when the hash is not in TorrServer's library.
2. `GET /api/position/<unknown_hash>` returns **404** with zeroed body when the hash is unknown to both `positions.json` AND TorrServer.
3. `DELETE /api/remove/<unknown_hash>` returns **404** when nothing was removed on either side.
4. All three endpoints reject hashes that don't match `^[0-9a-fA-F]{40}$|^[0-9a-fA-F]{64}$` with **400 invalid hash**.
5. `POST /api/position/<hash>` rejects malformed JSON with **400 invalid JSON** and missing/non-numeric `position` with **400 missing or invalid position**.
6. `GET /static/*` includes `Access-Control-Allow-Origin: *`; `fetch('https://tv.trikiman.shop/static/lampa-sync.js', { mode: 'cors' })` from `lampa.mx` succeeds.
7. The Lampa plugin and TorrStream UI continue to work unchanged — no client modifications needed.
8. Smoke check `scripts/smoke_prod.py` updated to cover the new error paths.

**Plans:** 2
- 01-01: Hash format validator + 404 for unknown hash on `/api/files`, `/api/position` GET, `/api/remove`. (3 endpoint changes, 1 shared validator)
- 01-02: Reject malformed JSON on `POST /api/position` (400 + missing-field validation) + add `Access-Control-Allow-Origin: *` to `/static/*` via `after_request` handler.

#### Phase 2: UX completeness

**Goal:** Every file in every torrent is reachable via the UI — pick any file, play it OR download it. Theme toggle feels instant.

**Depends on:** Phase 1 (API hygiene; the picker reads `/api/files` and depends on its 404 semantics).

**Requirements:** [UX-01, UX-02, UX-03]

**Success Criteria:**
1. Clicking a single-file torrent card still goes straight to player (preserved UX).
2. Clicking a multi-file torrent card opens a file-picker modal listing every file with: path, size, duration if known, viewed flag, resume position.
3. Each row in the picker has a **Play** button and a **Скачать** (Download) button.
4. The Download button uses `<a href="/api/stream/<encoded-name>?hash=X&index=Y" download="<encoded-name>">` so the browser saves the file with the correct name.
5. iOS Safari fallback: tapping Download on iOS shows a toast pointing to "Поделиться → Сохранить в Файлы" (Safari ignores `download` cross-origin).
6. Theme toggle: full background color change reaches its target value within ≤350ms wall-clock from click (was ~1400ms). Implementation note: switch from `body.classList` to `html[data-theme="light"]` and scope transitions to specific properties.
7. `docs/SMOKE-TESTS.md` updated with: file-picker walkthrough, download verification (byte-parity vs API), theme timing assertion.

**Plans:** 2
- 02-01: File-picker modal + per-file download UI. Single click on multi-file torrent opens picker; existing single-file shortcut preserved.
- 02-02: Theme transition fix — root `data-theme` attribute, scoped transitions, drop color transition.

#### Phase 3: Test harness

**Goal:** Every check in the 2026-05-14 E2E audit becomes a runnable test. CI runs the smoke marker on every PR. New regressions are caught before they ship.

**Depends on:** Phase 1, Phase 2 (tests assert the new contracts).

**Requirements:** [QUAL-04, QUAL-05]

**Success Criteria:**
1. `tests/api/` covers every `/api/*` route × every documented response shape: happy path, 404 unknown hash, 400 malformed JSON, 400 invalid hash, CORS preflight, range request, probe mode.
2. `tests/integration/` covers Lampa→TorrServer→TorrStream sync (using a known-fixture magnet), position GET/POST round-trip + Lampa-sync overwrite, viewed-sync threshold (>95% triggers).
3. `tests/ui/` (Playwright) covers shell load, search debounce, theme timing assertion, file picker modal, download anchor, install button visibility per UA.
4. Tests are safe to run against prod: every mutation captures pre-state and restores; no side-effects after a green run.
5. CI hook (GitHub Actions) runs the `smoke` marker on every PR + nightly against prod. Full E2E runs nightly.
6. `scripts/smoke_prod.py` retained but documented as a thin pre-flight; pytest is the source of truth.
7. `docs/SMOKE-TESTS.md` updated with `pytest -m smoke` and `pytest -m e2e` invocation. `.planning/codebase/STACK.md` updated to remove "No automated test framework".

**Plans:** 1
- 03-01: pytest + Playwright harness setup, port audit checks (api/integration/ui), add CI hook, document.

## Progress

**Execution Order:** Phase 1 → Phase 2 → Phase 3

| Phase | Plans Complete | Status |
|-------|----------------|--------|
| 1. API hygiene | 0/2 | Pending |
| 2. UX completeness | 0/2 | Pending |
| 3. Test harness | 0/1 | Pending |

## Archived Milestones

### v2.1 Player UX + iOS readiness (shipped 2026-05-12)
- 2 phases, 5 plans. Vidstack swap + iOS verification + Oracle deployment topology docs. See `.planning/milestones/v2.1-ROADMAP.md`.

### v2.0 Oracle Migration (shipped 2026-05-12)
- 3 phases, 7 plans. Migration AWS → Oracle, full state preservation. See `.planning/phases/01-oracle-baseline/` for artifacts.

### v1.1 Cross-Client Position Sync (shipped 2026-04-29)
- 1 phase, 2 plans. See `.planning/milestones/v1.1-ROADMAP.md`.

### v1.0 TorrStream (shipped 2026-04-24)
- 4 phases, 11 plans. See `.planning/milestones/v1.0-ROADMAP.md`.
