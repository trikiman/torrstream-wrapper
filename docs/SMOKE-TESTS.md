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
- response is an array
- if TorrServer is reachable and has data, items should include hashes/titles

### Search Endpoint

```bash
curl "http://127.0.0.1:5000/api/search?q=test"
```

Expected:
- valid JSON with `Results`
- no server crash even if jacred is unavailable

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
- `file_stats` array present
- video files listed when available

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

### Stream Probe

Use a real file path segment from the selected torrent file entry.

```bash
curl -I "http://127.0.0.1:5000/api/stream/<FILENAME>?hash=<TORRENT_HASH>&index=<FILE_INDEX>"
```

Expected:
- HTTP 200 or 206
- `Accept-Ranges: bytes`

### Download Probe

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
3. search returns results
4. adding a result succeeds
5. opening a torrent shows file choices
6. playback starts for a real file
7. seeking and returning updates resume position

## Pathing Checks

If you changed manifest, service-worker, or deployment-path logic, verify both:

1. direct-root serving assumptions
2. `/app/` reverse-proxy assumptions

At minimum confirm that:
- the icon path resolves
- the manifest loads
- the service worker registers from the expected path

## Current Gaps

- This project still has no automated test suite
- playback verification still requires a real TorrServer instance and real data
