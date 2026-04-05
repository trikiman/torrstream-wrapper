# Deployment

## Purpose

This is the authoritative runtime and deployment document for the wrapper application in this repository.

The source of truth for the app is:
- Backend: `app.py`
- Frontend: `templates/index.html`
- PWA assets: `static/manifest.json`, `static/sw.js`, `static/icons/icon-512.png`

The root `index.html` file is a legacy prototype copy and is not served by Flask.

## Runtime Shape

The application is a Flask server that serves:
- `/` -> `templates/index.html`
- `/manifest.json` -> `static/manifest.json`
- `/sw.js` -> `static/sw.js`
- `/api/torrents`
- `/api/files/<torrent_hash>`
- `/api/position/<torrent_hash>` (`GET` and `POST`)
- `/api/stream/<filename>`
- `/api/download/<filename>`
- `/api/add`
- `/api/remove/<torrent_hash>`
- `/api/search`

Local startup entrypoint:

```bash
python app.py
```

Current default bind in code:
- host: `0.0.0.0`
- port: `5000`

## Required External Dependency

This wrapper depends on a reachable TorrServer instance.

Environment variables:
- `TORRSERVER_URL`
- `TORRSERVER_USER`
- `TORRSERVER_PASS`
- `JACRED_URL`
- `JACRED_KEY`

Current code defaults in `app.py`:
- `TORRSERVER_URL=http://127.0.0.1:8090`
- `JACRED_URL=https://jacred.xyz`

The wrapper does not replace TorrServer. It reads library state from TorrServer and proxies stream/download traffic to it.

## Supported Deployment Topologies

### 1. Reverse Proxy Under `/app/`

This is the topology most aligned with the current frontend asset assumptions.

Why:
- `templates/index.html` currently references:
  - `/app/static/icons/icon-512.png`
  - `/app/manifest.json`
- `static/sw.js` treats `/app/api/` as the API prefix
- `static/manifest.json` uses:
  - `start_url: /app/`
  - `scope: /app/`

If the app is reverse-proxied under `/app/`, those paths remain coherent.

Typical shape:

```text
browser
  -> https://host/app/
  -> reverse proxy
  -> Flask on http://127.0.0.1:5000/
```

### 2. Direct-Root Serving

The Flask app itself serves routes at root:
- `/`
- `/manifest.json`
- `/sw.js`
- `/api/*`

So root-path serving is possible at the backend level, but the current frontend files are not fully normalized for it.

Current constraint:
- the HTML, manifest, and service worker still contain `/app/` assumptions

That means a direct-root deployment should be treated as requiring path cleanup before it is considered canonical.

## Operational Notes

- `positions.json` stores wrapper-managed playback state
- the wrapper has no end-user auth
- if exposed publicly, the wrapper exposes torrent listing, add/remove, and playback operations
- keep service credentials out of versioned deployment config

## Recommended Verification

After deployment or path changes, use `docs/SMOKE-TESTS.md`.

At minimum verify:
- `/` returns the UI shell
- `/manifest.json` returns the manifest
- `/sw.js` returns the service worker
- `/api/torrents` reaches TorrServer
- playback-related flows still work against a real TorrServer instance
