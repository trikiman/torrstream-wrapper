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
