---
created: 2026-05-14T23:24:58.665Z
title: Return 404 for unknown-hash on /api/files /api/position GET /api/remove
area: api
files:
  - app.py:322
  - app.py:430-455
  - app.py:578-590
---

## Problem

Three wrapper endpoints currently return `200 OK` for hashes that don't exist
in TorrServer. This violates HTTP semantics and makes legitimate "not found"
indistinguishable from "exists with empty state" in client code and logs.

E2E audit 2026-05-14 confirmed:

| Endpoint | Unknown-hash response |
|---|---|
| `GET /api/files/<unknown>` | `200 {"ok":false, "error":"torrent not found or file lookup failed", "state":"file_lookup_failed", "file_stats":[]}` |
| `GET /api/position/<unknown>` | `200 {"ok":true, "position":0, "duration":0, "last_file_index":1}` |
| `DELETE /api/remove/<unknown>` | `200 {"ok":true, "removed_positions":false}` |

Concrete consequences:

- Frontend cannot tell "user has not started watching this" from "this hash
  isn't in the library at all" via `GET /api/position`.
- Lampa plugin can't react to a torrent being deleted upstream — `DELETE` for a
  non-existent hash silently 200s.
- Monitoring/log analysis can't trip on 404 spikes because there are no 404s.

## Solution

Robust (preserve diagnostics-first style without lying about HTTP):

1. `GET /api/files/<hash>`: when `state == "file_lookup_failed"` AND the hash
   is not present in `/api/torrents`, return **404** with the same JSON body
   (clients still get diagnostics). Distinguish "torrent exists but files
   aren't ready" (still 200) from "torrent not in library" (404).

2. `GET /api/position/<hash>`: when the hash isn't in `positions.json` AND not
   in TorrServer's `/api/torrents`, return **404** with the zeroed body. If
   the hash IS known to TorrServer but has no position yet, keep the 200 with
   zeros (current resume-on-play UX still works).

3. `DELETE /api/remove/<hash>`: if the hash wasn't in TorrServer AND there
   were no positions to wipe, return **404** with the existing body. If
   either side had something to remove, keep 200.

4. Update `docs/SMOKE-TESTS.md` and the production smoke (`scripts/smoke_prod.py`)
   to verify the 404 path explicitly (probe a known-bad hash).

5. Existing UI code that depends on these endpoints needs an audit pass — the
   resume-on-play flow currently treats 200/zeros as "never watched", and that
   semantic should still work because hash IS known to TorrServer when user is
   trying to watch.

Out of scope: changing the "ok flag in body" convention (200-with-ok-false
elsewhere). This todo is only about distinguishing nonexistent resources.
