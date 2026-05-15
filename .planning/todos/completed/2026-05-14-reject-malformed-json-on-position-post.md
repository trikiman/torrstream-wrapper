---
created: 2026-05-14T23:24:58.665Z
title: Reject malformed JSON on POST /api/position with 400
area: api
files:
  - app.py:460-490
---

## Problem

`POST /api/position/<hash>` currently uses
`request.get_json(force=True, silent=True)` which swallows JSON parse errors
and returns `None`. The route then falls back to `{}` and runs to completion,
returning `{"ok": true, "viewed_sync_attempted": false, "viewed_synced": false}`.

E2E audit 2026-05-14 sent two broken bodies:

| Body | Response |
|---|---|
| `not json{` (malformed) | `200 {"ok":true,...}` |
| `{}` (no position field) | `200 {"ok":true,...}` |

Neither actually wrote a position, but the client got a "success" signal. A
broken Lampa plugin or a misbehaving fetch wrapper would silently lose all
position updates and never know.

## Solution

Robust:

1. Switch to `request.get_json(force=True, silent=False)` and wrap in
   try/except for `werkzeug.exceptions.BadRequest`. Return
   `400 {"ok": false, "error": "invalid JSON"}` when parse fails.
2. Validate required fields explicitly: at minimum `position` must be a
   non-negative number. If missing or not numeric, return
   `400 {"ok": false, "error": "missing or invalid position"}`.
3. `duration` should be optional but if present must be a non-negative
   number; reject negative or NaN.
4. Keep the `viewed_sync_attempted` / `viewed_synced` flags only on the
   success path — they don't apply to 400s.
5. CORS preflight (OPTIONS) must continue to work; only the POST validation
   changes. Add a smoke test for the bad-JSON case from the lampa.mx origin
   to confirm the 400 still has CORS headers.
6. `static/lampa-sync.js` already constructs proper JSON, so this is purely a
   contract hardening — no client change needed for current callers.

Add a unit/integration smoke step that POSTs garbage and confirms 400.
