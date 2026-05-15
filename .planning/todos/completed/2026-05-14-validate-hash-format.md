---
created: 2026-05-14T23:24:58.665Z
title: Reject invalid hash format on /api/position GET and POST
area: api
files:
  - app.py:430-490
---

## Problem

`/api/position/<torrent_hash>` accepts any string as the hash and routes it
through to disk persistence and (for unknowns) returns zeroed state. This
means typos, accidentally-passed paths, or attacker-supplied junk all hit
`positions.json` write paths and accumulate garbage keys.

Spotted while writing the unknown-hash 404 todo — the validation gap is
adjacent. Worth its own todo because the fix is different (input validation
at the route boundary rather than 200→404 status remap).

A torrent infohash is exactly 40 hex chars (SHA-1) or 64 hex chars
(BTv2 SHA-256). Anything else cannot be a real hash.

## Solution

Robust:

1. Add a route-level validator: regex `^[0-9a-fA-F]{40}$|^[0-9a-fA-F]{64}$`.
   Reject with `400 {"ok": false, "error": "invalid hash"}` if the path
   parameter doesn't match.
2. Apply same validator to `/api/files/<hash>` and `/api/remove/<hash>` for
   consistency.
3. After implementing, walk `positions.json` once and delete keys that don't
   match the validator (cleanup). Pair this with a simple `--vacuum` flag on
   a scripts/positions_vacuum.py helper so it can be re-run safely.
4. Lowercase the hash on the way in (TorrServer is case-insensitive but
   `positions.json` keys are not). Prevents `ABCD...` and `abcd...` from
   accumulating two entries for the same torrent.
5. Smoke test: `curl /api/position/garbage` → 400. `curl /api/position/<40hex
   uppercased>` and `<40hex lowercased>` should write to the same key.

This is hygiene, not a security fix — but it cleans up the API surface and
makes the file-backed state predictable.
