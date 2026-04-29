---
status: complete
phase: 01-cross-client-position-sync
source:
  - 01-01-SUMMARY.md
  - 01-02-SUMMARY.md
started: 2026-04-29T08:30:00+00:00
updated: 2026-04-29T09:00:00+00:00
---

## Current Test

[testing complete]

## Tests

### 1. Plugin URL is publicly served
expected: `GET https://tv.trikiman.shop/static/lampa-sync.js` returns HTTP 200 with `Content-Type: text/javascript`.
result: pass

### 2. CORS preflight on /api/position/* succeeds
expected: `OPTIONS https://tv.trikiman.shop/api/position/<hash>` from `Origin: https://lampa.mx` returns `Access-Control-Allow-Origin: *` and `Access-Control-Allow-Methods: GET, POST, OPTIONS`.
result: pass

### 3. /api/torrents exposes viewed_in_torrserver
expected: a torrent watched in Lampa but not in the wrapper player returns `viewed_in_torrserver: true` from `/api/torrents`.
result: pass

### 4. Continue-row UI includes externally-watched torrents
expected: the homepage `Продолжить просмотр` row shows a Lampa-watched torrent next to a wrapper-watched torrent, with no progress bar on the externally-watched one.
result: pass

### 5. Plugin self-installs in Lampa
expected: after pasting the plugin URL into Lampa's Plugin store, `window.__torrstream_sync_loaded === true` and `Lampa.Player.__torrstream_wrapped === true`.
result: pass

### 6. Lampa → wrapper position sync (POSTs during playback)
expected: starting a TorrServer-backed file in Lampa produces POSTs to `https://tv.trikiman.shop/api/position/<hash>` with `{file_index, position, duration}` at ~5 s cadence.
result: pass

### 7. Wrapper → Lampa resume (auto-seek on player open)
expected: with a stored wrapper position for a torrent, opening the same file in Lampa seeks `<video>.currentTime` to the saved offset within the first metadata-ready tick.
result: pass

### 8. Player teardown flushes final position
expected: closing the Lampa player triggers a final POST so the wrapper's `/api/position/<hash>` reflects the user's last frame within ~1 s of close.
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[]
