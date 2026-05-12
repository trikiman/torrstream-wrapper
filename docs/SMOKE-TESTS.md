# Smoke Tests

## Purpose

Use this document after changes that affect:
- TorrServer integration
- wrapper API routes
- playback or downloading
- search
- deployment pathing or PWA assets

This is a smoke-verification playbook, not a full automated test suite.

## Prerequisites

- Python 3 available locally
- a reachable TorrServer instance
- wrapper environment configured as needed:
  - `TORRSERVER_URL`
  - `TORRSERVER_USER`
  - `TORRSERVER_PASS`
  - `JACRED_URL`
  - `JACRED_KEY`
- at least one real torrent present in TorrServer for file/playback checks

## Start the Wrapper

```bash
python app.py
```

Expected local base URL:

```text
http://127.0.0.1:5000
```

## Fast Path

Run the helper first:

```bash
python scripts/smoke_check.py
```

Then use the detailed checks below when you need to investigate a specific failure.

## Safe Structural Checks

These do not require a real torrent hash.

### UI Shell

```bash
curl -I http://127.0.0.1:5000/
```

Expected:
- HTTP 200

### Manifest

```bash
curl -I http://127.0.0.1:5000/manifest.json
```

Expected:
- HTTP 200

### Service Worker

```bash
curl -I http://127.0.0.1:5000/sw.js
```

Expected:
- HTTP 200

### Library Endpoint

```bash
curl http://127.0.0.1:5000/api/torrents
```

Expected:
- valid JSON
- `ok` is present
- `items` is an array
- `diagnostics.state` distinguishes `ready`, `empty`, and failure-style states
- if TorrServer is reachable and has data, `items` should include hashes/titles

### Status Endpoint

```bash
curl http://127.0.0.1:5000/api/status
```

Expected:
- valid JSON
- `torrserver.ok` distinguishes reachable-vs-unreachable upstream state
- `torrserver.torrent_count` indicates whether the upstream library is simply empty
- `wrapper.position_entries` shows how many local resume records are currently stored

### Search Endpoint

```bash
curl "http://127.0.0.1:5000/api/search?q=test"
```

Expected:
- valid JSON with `Results`
- if jacred is unavailable, response still returns JSON with `ok: false`

### Invalid Add Request

```bash
curl -X POST http://127.0.0.1:5000/api/add ^
  -H "Content-Type: application/json" ^
  -d "{\"link\":\"bad-input\"}"
```

Expected:
- valid JSON
- `ok: false`
- explicit validation error such as `invalid link`

### Remove Request

```bash
curl -X DELETE http://127.0.0.1:5000/api/remove/<TORRENT_HASH>
```

Expected:
- valid JSON
- explicit `ok` state
- `removed_positions` indicates whether local resume state was cleared

## Real-Data Checks

These require a real torrent hash from `/api/torrents`.

Replace:
- `<TORRENT_HASH>` with a real hash
- `<FILE_INDEX>` with a real file index

### File Listing

```bash
curl "http://127.0.0.1:5000/api/files/<TORRENT_HASH>"
```

Expected:
- valid JSON
- `ok` is present
- `diagnostics.state` distinguishes `ready`, `no_playable_files`, `file_lookup_failed`, and upstream failure
- `file_stats` contains playable files only

### Position Read

```bash
curl "http://127.0.0.1:5000/api/position/<TORRENT_HASH>?file_index=<FILE_INDEX>"
```

Expected:
- valid JSON with `position`, `duration`, and `last_file_index`

### Position Write

```bash
curl -X POST "http://127.0.0.1:5000/api/position/<TORRENT_HASH>" ^
  -H "Content-Type: application/json" ^
  -d "{\"position\":120,\"duration\":1000,\"file_index\":<FILE_INDEX>}"
```

Expected:
- `{"ok": true}`
- subsequent GET returns updated values
- completion writes also report `viewed_sync_attempted` and `viewed_synced`

### Stream Probe

Use a real file path segment from the selected torrent file entry.

```bash
curl "http://127.0.0.1:5000/api/stream/<FILENAME>?hash=<TORRENT_HASH>&index=<FILE_INDEX>&probe=1"
```

Expected:
- valid JSON
- `ok: true` when playback should be available
- explicit error payload when playback is not available

Then verify the real stream response:

```bash
curl -I "http://127.0.0.1:5000/api/stream/<FILENAME>?hash=<TORRENT_HASH>&index=<FILE_INDEX>"
```

Expected:
- HTTP 200 or 206
- `Accept-Ranges: bytes`

### Download Probe

```bash
curl "http://127.0.0.1:5000/api/download/<FILENAME>?hash=<TORRENT_HASH>&index=<FILE_INDEX>&probe=1"
```

Expected:
- valid JSON
- `ok: true` when download should be available
- explicit error payload when download is not available

Then verify the real download response:

```bash
curl -I "http://127.0.0.1:5000/api/download/<FILENAME>?hash=<TORRENT_HASH>&index=<FILE_INDEX>"
```

Expected:
- HTTP 200 or 206
- `Content-Disposition: attachment`

## Production Smoke (Oracle)

The repo ships `scripts/smoke_prod.py` which hits the live deployment at `https://tv.trikiman.shop`. Run it before shipping any change to the shell, service worker, manifest, player, Lampa plugin, or CORS surface:

```bash
python scripts/smoke_prod.py
```

Expected output: `9/9 PASS`. The Shell row should report `vidstack=True` — this confirms the Vidstack web components are embedded in the served HTML.

## Manual Browser Checks

Open:

```text
http://127.0.0.1:5000/
```

Verify:
1. the UI loads without a blank screen
2. the library populates from TorrServer
3. if TorrServer is empty, the UI explicitly says the library is empty instead of looking broken
4. if jacred is unavailable, search shows a service-unavailable message instead of “nothing found”
5. adding a result succeeds
6. opening a torrent shows file choices
7. playback starts for a real file
8. seeking and returning updates resume position

If the library is empty, verify the UI specifically says TorrServer is reachable but empty.
If playback fails, verify the player shows an explicit error state instead of silently staying broken.

## iOS Safari Walkthrough

Run this on a real iPhone or iPad, not simulator, to catch Safari-specific gotchas.

1. **Open** `https://tv.trikiman.shop/` in Safari. Shell should load with Russian copy; no red errors.
2. **Install PWA**: Share → "На экран «Домой»" → open from the home-screen icon. The shell must launch standalone (no Safari chrome).
3. **Play a file**: tap a torrent card from Библиотека → tap a playable file → Vidstack player opens inline (not forced fullscreen).
4. **Audio check**: video starts with audio. On Safari, autoplay may require a single user tap; confirm a tap on the centre of the player toggles play and audio is audible.
5. **Double-tap seek**: double-tap the left third of the player → position jumps back 10s. Double-tap the right third → forward 10s.
6. **Seek bar**: drag the scrub bar to a new position → playback resumes there.
7. **Fullscreen**: tap fullscreen button → Safari native fullscreen opens with Vidstack's controls retained.
8. **Resume**: exit the player, tap the same file again → video resumes from where you left off (toast shows "С MM:SS").
9. **PiP** (optional, Safari 14+): tap picture-in-picture button → Safari's native PiP overlay appears, playback continues, web UI remains interactive.
10. **Lampa sync** (optional, if Lampa is installed on the same device): open a TorrServer stream in Lampa → after ≥5s, return to TorrStream shell → "Продолжить просмотр" row shows the updated position.

## Pathing Checks

If you changed manifest, service-worker, or deployment-path logic, verify both:

1. direct-root serving assumptions
2. `/app/` reverse-proxy assumptions

At minimum confirm that:
- the icon path resolves
- the manifest loads
- the service worker registers from the expected path

Expected after the current path normalization work:
- root deployment should load `manifest.json` and `sw.js` without `/app/` 404s
- `/app/` reverse-proxy deployment should also continue to work because the asset paths are relative

## Current Gaps

- This project still has no automated test suite
- playback verification still requires a real TorrServer instance and real data
