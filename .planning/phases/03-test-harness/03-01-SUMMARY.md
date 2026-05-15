---
phase: 03-test-harness
milestone: v2.2
subsystem: testing
tags: [pytest, harness, ci, smoke, integration, e2e]
provides:
  - tests/api/ — 57 contract tests via Flask test client (mocked TorrServer)
  - tests/integration/ — 10 live-wrapper read-only tests against tv.trikiman.shop
  - tests/conftest.py — shared fixtures (Flask client, mock_ts, live_session)
  - pytest.ini — markers (smoke / integration / e2e / cors)
  - requirements-dev.txt — pytest, pytest-mock, requests
  - .github/workflows/tests.yml — CI hook (smoke on every PR + push, integration nightly)
key-decisions:
  - "Two test layers: smoke uses Flask test client + mock TorrServer (no network, fast). Integration hits the live wrapper read-only."
  - "Mutations gated behind `-m e2e` opt-in; pytest.ini default excludes e2e to keep CI safe"
  - "Skip cleanly when live wrapper is unreachable so local runs don't fail without prod access"
  - "Mock TorrServer extracts magnet hashes from `add` payloads to mirror real upstream behavior"
requirements-completed: [QUAL-04, QUAL-05]
duration: 90min
completed: 2026-05-14
commits:
  - (TBD on push)
---

# Phase 3 Summary: Test harness

**Outcome:** TorrStream now has a runnable pytest harness covering every API contract surfaced by the 2026-05-14 E2E feature audit. Smoke layer runs in 0.58s and stays green without network access; integration layer validates against live `tv.trikiman.shop` and ran 10/10 PASS in 7.48s. CI hook runs the smoke marker on every PR and the integration marker nightly.

## Coverage map

Suite | Tests | Source audit checks covered
--- | --- | ---
`tests/api/test_static.py` | 5 | shell HTML, manifest, sw.js, favicon, lampa-sync.js reachability
`tests/api/test_torrents.py` | 4 | library list shape, status endpoint, TS-down state
`tests/api/test_files.py` | 9 | known-hash success, 404 unknown, 200-with-state when TS down, 400 malformed (5 variants), uppercase normalization, BTv2 SHA-256 hashes
`tests/api/test_position.py` | 11 | GET 404 unknown, GET 200-zeros known-no-position, GET 400 invalid; POST malformed JSON, missing position, non-numeric, invalid hash, round-trip, viewed-sync threshold; OPTIONS preflight, CORS on GET, CORS on 400
`tests/api/test_remove.py` | 4 | unknown 404, known 200, position cleanup, invalid hash
`tests/api/test_search.py` | 12 | empty/missing query, flat-list provider response, dict-keyed-by-id provider response, provider failure → ok:false; recent searches GET/POST/DELETE round-trip, dedupe, 400 on empty
`tests/api/test_stream.py` | 3 | missing hash, probe mode, range request forwarding
`tests/api/test_cors.py` | 4 | static cors origin, scoped CORS (api/torrents has no CORS)
`tests/api/test_add.py` | 4 | empty, invalid, magnet, bare hash
**Total smoke** | **57** | every audit Wave 1.x check, plus v2.2 hardening contracts (Plans 1.1, 1.2)
`tests/integration/` | 10 | live unknown-hash 404s, malformed JSON 400, static CORS, position OPTIONS preflight, search Round trip, /api/torrents shape, real range request

## Verification

```bash
$ pytest -m smoke -q
.................................................................
57 passed in 0.58s

$ pytest -m integration --tb=short
10 passed in 7.48s
```

## What this locks in

The audit's "no automated test framework" gap (`.planning/codebase/STACK.md`) is now retired. Each contract delivered by Phases 1 and 2 has at least one test pinning it:

- **API hygiene (Plans 1.1, 1.2):** invalid hash → 400, unknown hash → 404, malformed JSON → 400, CORS on `/static/*` and `/api/position/*`, hash lowercase normalization.
- **UX completeness (Plans 2.1, 2.2):** download anchor URL shape and byte parity covered by `test_stream_range_request_succeeds` (integration); theme + file-picker UI not unit-tested (require browser; deferred to a future Playwright plan).

## Carry-overs

Not in this phase by design:

- Playwright UI tests (theme timing assertion, file-picker walkthrough, download click-through). Foundation laid; can be a v2.3 plan if the manual MCP-driven verification proves insufficient.
- Service worker / PWA install flow — needs a browser context; same deferral.
- Lampa plugin in-Lampa integration test — needs a Lampa runtime, hard to automate; the cross-origin contract (CORS preflight, position write through wrapper) is covered by the integration suite already.
