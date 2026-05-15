---
created: 2026-05-14T23:24:58.665Z
title: Add CORS headers to /static/* for cross-origin fetch
area: api
files:
  - app.py
---

## Problem

`fetch('https://tv.trikiman.shop/static/lampa-sync.js', { mode: 'cors' })` from
the `lampa.mx` origin throws `TypeError: Failed to fetch`. The static endpoint
returns the file fine to `<script src=...>` (no-cors mode), but explicit
cross-origin `fetch()` fails because the response has no
`Access-Control-Allow-Origin` header.

Confirmed during E2E audit 2026-05-14: `/api/position/*` works cross-origin,
but `/static/lampa-sync.js` does not.

Today this only matters if a future Lampa-side enhancement wants to fetch the
plugin programmatically (e.g., to read its version, hot-reload, or do an
integrity check). It's not blocking current behavior.

## Solution

Robust:

1. Add `Access-Control-Allow-Origin: *` to all `/static/*` responses.
   Cleanest way is a Flask `after_request` handler that scopes only to
   `request.path.startswith('/static/')`.
2. Also expose `Access-Control-Allow-Headers: Content-Type` and
   `Access-Control-Expose-Headers` if any future fetcher will read custom
   headers. Don't need credentials, so keep `*` origin.
3. The route is fully public read-only static files — no auth concerns from
   widening CORS.
4. Verify by re-running the audit's cross-origin fetch from a `lampa.mx` page
   — must succeed with a `200` and a non-empty body.
5. Don't apply this blanket to `/api/*`. That surface already has explicit
   per-route CORS only on the position endpoints. Static is the only gap.

Tag this with the `[LAMPA]` ergonomics theme — it pairs naturally with
"plugin self-update" and "version probe" features that may show up later.
