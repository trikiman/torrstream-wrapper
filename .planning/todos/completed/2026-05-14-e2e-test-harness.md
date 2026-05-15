---
created: 2026-05-14T23:24:58.665Z
title: Bake E2E feature audit into a runnable smoke harness
area: testing
files:
  - scripts/smoke_prod.py
  - docs/SMOKE-TESTS.md
  - tests/
---

## Problem

The 2026-05-14 E2E audit covered 25 distinct feature checks (backend contract,
UI behavior, Lampa integration, CORS, theme, PWA, position sync, range
requests). It was run by hand through chrome-devtools MCP against the live
deployment. Findings landed in chat history with no replayable artifact.

Existing test surface:

- `scripts/smoke_prod.py` — 9 production checks (shell, manifest, SW, plugin,
  status, library, search, file list, CORS).
- `docs/SMOKE-TESTS.md` — manual walkthrough.
- `.planning/codebase/TESTING.md` notes there are no automated tests.

So the audit's value evaporates unless captured. Same gaps will recur after
the next refactor with no signal until a user notices.

## Solution

Robust:

1. Promote the audit to a real test harness, not a one-off script.
   Recommended: `pytest` + `requests` for backend contract, plus a
   `playwright`-driven UI suite for the click-through paths. Keep both
   colocated under `tests/`.
2. Split into:
   - `tests/api/` — every endpoint x every documented response shape.
     Includes the unknown-hash, malformed-JSON, and CORS preflight cases.
   - `tests/integration/` — Lampa adds → wrapper sees, position round-trip,
     viewed sync threshold (>95% triggers), recent-searches CRUD with
     restore.
   - `tests/ui/` (Playwright) — search input + debounce, theme toggle
     timeline assertion (≤350ms total), card click → player opens, file
     picker (after that feature lands), download link (after it lands),
     install button visibility per UA.
3. Wire the harness into `scripts/smoke_prod.py` as a "thin" mode that hits
   only deterministic checks (no live torrents added). Full mode = pytest run
   against a staging copy.
4. Make tests safe to run against prod: every mutation (add/remove, recent
   searches) must capture pre-state and restore. This audit accidentally
   wiped recent-searches and had to manually restore — no future test should
   leave traces.
5. Document `pytest -m smoke` and `pytest -m e2e` markers in
   `docs/SMOKE-TESTS.md`. Update `STACK.md` codebase note ("No automated
   test framework") once landed.
6. Add a CI hook (GitHub Actions on PR + nightly against prod) that runs the
   smoke marker only — keeps deployments cheap.

This is the foundation that makes every other todo verifiable. Worth treating
as its own phase, not as a side-task to UX/API fixes.
