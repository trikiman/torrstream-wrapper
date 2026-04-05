# Architecture

**Analysis Date:** 2026-04-05

## Pattern Overview

**Overall:** Monolithic Flask proxy with a single large client-side web app

**Key Characteristics:**
- One backend module, `app.py`, contains routing, integration logic, and local persistence
- One primary frontend template, `templates/index.html`, contains markup, styles, and client logic inline
- Server-side state is file-based, not database-backed
- External capability is delegated to TorrServer and jacred rather than implemented natively

## Layers

**HTTP/UI Delivery Layer:**
- Purpose: serve the HTML shell, manifest, and service worker
- Contains: `/`, `/manifest.json`, `/sw.js`
- Depends on: local files under `templates/` and `static/`
- Used by: browser clients

**API Route Layer:**
- Purpose: expose library, playback, search, and position endpoints
- Contains: `/api/*` route handlers in `app.py`
- Depends on: helper functions, file persistence, and external services
- Used by: the client-side app in `templates/index.html`

**Integration Layer:**
- Purpose: translate wrapper actions into TorrServer and jacred requests
- Contains: `ts_post()`, `ts_get()`, `get_viewed()`, `set_viewed()`, and `search()`
- Depends on: `requests` and environment configuration
- Used by: API route handlers

**Persistence Layer:**
- Purpose: persist local playback state that TorrServer does not fully own
- Contains: `load_positions()` and `save_positions()`
- Depends on: local `positions.json`
- Used by: library, file-list, and playback position routes

## Data Flow

**Browser Request Flow:**

1. Browser loads `/` and receives `templates/index.html`
2. Inline client code calls `/api/torrents`, `/api/files/<hash>`, `/api/search`, and playback endpoints
3. Flask routes normalize input and call TorrServer or jacred
4. Flask merges local `positions.json` data with remote TorrServer data
5. Browser renders cards, episode/file panels, and player state from the API responses

**Playback Sync Flow:**

1. Browser starts playback via `/api/stream/<filename>?hash=<torrent>&index=<file>`
2. Flask proxies TorrServer stream bytes and passes through range headers
3. Browser periodically posts progress to `/api/position/<torrent_hash>`
4. Flask updates `positions.json`
5. If position exceeds 95%, Flask also marks the file viewed in TorrServer

**State Management:**
- Browser state lives in the single-page client
- Persistent wrapper state lives in `positions.json`
- Torrent catalog and file metadata live in TorrServer

## Key Abstractions

**Torrent Wrapper Endpoint:**
- Purpose: expose a friendlier app-specific API around TorrServer
- Examples: `/api/torrents`, `/api/add`, `/api/remove/<torrent_hash>`
- Pattern: thin Flask route over helper methods and JSON shaping

**Per-File Position Record:**
- Purpose: track resume state at the file level, not just the torrent level
- Examples: `positions.json` entries with `files`, `last_file_index`, and `updated`
- Pattern: file-backed dictionary keyed by torrent hash

**Single-Template Frontend:**
- Purpose: keep the full UI in one delivered document
- Examples: `templates/index.html`
- Pattern: inline CSS + inline JavaScript in a monolithic template

## Entry Points

**Backend Entry:**
- Location: `app.py`
- Triggers: Flask process startup or `python app.py`
- Responsibilities: define routes, helpers, config defaults, and serve HTTP traffic

**Frontend Entry:**
- Location: `templates/index.html`
- Triggers: browser load of `/`
- Responsibilities: render the UI, call backend APIs, and manage playback/search interactions

**PWA Entry:**
- Locations: `static/manifest.json`, `static/sw.js`
- Triggers: browser install/service-worker lifecycle
- Responsibilities: app metadata and shell asset caching

## Error Handling

**Strategy:** Fail soft at integration boundaries and return empty results or 502s

**Patterns:**
- `ts_post()` and `ts_get()` swallow exceptions and return `None`
- Search failures return `{"Results": []}`
- Stream and download proxy failures return `502` JSON errors

## Cross-Cutting Concerns

**Logging:**
- No explicit logging framework in app code

**Validation:**
- Minimal request validation
- Most routes trust JSON/query input shape and depend on safe defaults

**Authentication:**
- No user authentication in the wrapper
- Optional service-to-service basic auth for TorrServer only

---

*Architecture analysis: 2026-04-05*
*Update when major patterns change*
