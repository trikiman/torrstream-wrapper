# External Integrations

**Analysis Date:** 2026-04-05

## APIs & External Services

**Streaming Backend:**
- TorrServer - source of torrent library, file metadata, viewed markers, and media streams
  - Integration method: REST-like HTTP calls via `requests` in `app.py`
  - Auth: optional HTTP basic auth via `TORRSERVER_USER` and `TORRSERVER_PASS`
  - Endpoints used: `/torrents`, `/viewed`, `/stream/...`

**External APIs:**
- jacred.xyz - torrent search provider for `/api/search`
  - Integration method: HTTP GET to `https://jacred.xyz/api/v1.0/torrents`
  - Auth: optional API key via `JACRED_KEY`
  - Response shape is normalized in `app.py` before returning to the UI

**Frontend CDN:**
- Plyr CDN - player CSS and JavaScript loaded by the browser
  - Assets: `https://cdn.plyr.io/3.7.8/plyr.css` and `https://cdn.plyr.io/3.7.8/plyr.polyfilled.js`
  - Auth: none

## Data Storage

**Databases:**
- None

**File Storage:**
- Local JSON file `positions.json` - persisted watch-position and last-file state
  - Connection: direct file reads/writes through `Path.read_text()` and `Path.write_text()`
  - Format: per-torrent, per-file nested JSON structure

**Caching:**
- Browser service worker cache in `static/sw.js`
  - Stores shell assets and successful GET responses

## Authentication & Identity

**Auth Provider:**
- None for end users

**Service Credentials:**
- TorrServer basic-auth credentials can be supplied via environment variables
- jacred API key can be supplied via environment variable

## Monitoring & Observability

**Error Tracking:**
- None configured

**Analytics:**
- None configured

**Logs:**
- No structured logging in app code
- Flask process stdout/stderr is the effective log surface

## CI/CD & Deployment

**Hosting:**
- Manual/self-hosted Python deployment
  - No deployment manifest or container definition is present in the repo
  - Existing live infrastructure is outside the repo and currently exposes TorrServer directly

**CI Pipeline:**
- None configured in-repo

## Environment Configuration

**Development:**
- Required env vars only when defaults are unsuitable
- Secrets location is not documented in-repo

**Staging:**
- No dedicated staging configuration documented

**Production:**
- Requires network access to the configured TorrServer host
- Requires write access to `positions.json`

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-04-05*
*Update when adding/removing external services*
