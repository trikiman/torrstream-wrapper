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
- `/favicon.ico` -> `static/icons/icon-512.png`
- `/api/torrents`
- `/api/status`
- `/api/files/<torrent_hash>`
- `/api/position/<torrent_hash>` (`GET` and `POST`)
- `/api/stream/<filename>`
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
- `TORRSERVER_USER=""`
- `TORRSERVER_PASS=""`
- `JACRED_URL=https://jac.red`

The wrapper does not replace TorrServer. It reads library state from TorrServer and proxies stream/download traffic to it.

## Dependency Installation

Install runtime dependencies with:

```bash
pip install -r requirements.txt
```

## Production Deployment (Oracle Cloud)

As of 2026-05-12 the production deployment runs on Oracle Cloud Always Free:

| Component | Where |
|---|---|
| TorrServer | `vless-x86-2` @ `158.101.214.234:8090`, BasicAuth required |
| Flask wrapper | same host, `127.0.0.1:5000` |
| Caddy (TLS termination) | same host, `:80` (redirect) + `:443` (TLS) |
| Web UI domain | `tv.trikiman.shop` → A record `158.101.214.234` → Caddy → Flask wrapper (`127.0.0.1:5000`) |
| TorrServer domain (for Lampa / TV clients) | `ts.trikiman.shop` → A record `158.101.214.234` → Caddy → TorrServer (`127.0.0.1:8090`) |
| TLS cert | Let's Encrypt via Caddy auto-HTTPS (both subdomains) |
| Auto-deploy | GitHub webhook → `/api/github-webhook` (HMAC-verified) → `git pull --ff-only` → `systemctl restart flask-wrapper` |

### Why two subdomains

`tv.trikiman.shop` is the web UI for humans. `ts.trikiman.shop` exposes TorrServer's raw HTTP API for clients like Lampa that talk directly to TorrServer (not to the Flask wrapper). Both terminate TLS at Caddy, which puts TorrServer behind HTTPS and lets it benefit from HTTP/2 and CDN-friendly behavior on Russian DPI-throttled networks. The two domains share the same origin server but keep Lampa's TorrServer traffic off the Flask wrapper so range requests for video don't route through Python.

### TorrServer settings (v2.1.1)

`/var/lib/torrserver/settings.json`:

| Key | Value | Why |
|---|---|---|
| `TorrentDisconnectTimeout` | `300` (s) | Stops Lampa seeing "connection drop" when buffering pauses exceed the old 30s default |
| `ReaderReadAHead` | `95` | Default; preserves prefetch window |
| `PreloadCache` | `50` (MB) | Default; preserves initial buffer |
| `CacheSize` | `67108864` (64 MB) | Default |
| `ConnectionsLimit` | `25` | Default |

Settings changed via `POST /settings {"action":"set","sets":{...}}` must send the **full settings block** — TorrServer's `set` replaces, not merges.

On-box paths:

| Path | Purpose |
|---|---|
| `/opt/torrstream/app/` | Flask wrapper git checkout |
| `/opt/torrstream/venv/` | Python venv (Flask, requests) |
| `/var/lib/torrserver/` | TorrServer state (config.db, settings.json, accs.db) |
| `/var/lib/torrserver/accs.db` | Plaintext JSON `{"user": "password"}` for TorrServer auth |
| `/etc/torrstream/torrserver.env` | Flask env file (root-owned, 600): `TORRSERVER_USER`, `TORRSERVER_PASS`, `GITHUB_WEBHOOK_SECRET`, `TORRSTREAM_SERVICE` |
| `/etc/caddy/Caddyfile` | Caddy config for `tv.trikiman.shop` (→ Flask) and `ts.trikiman.shop` (→ TorrServer) |
| `/var/log/torrstream/` | Combined logs (flask, torrserver, caddy access) |
| `/etc/systemd/system/{torrserver,flask-wrapper}.service` | Managed systemd units; Caddy uses distro default |

SSH access: `ssh -i <key> ubuntu@158.101.214.234`.

## Local / Reverse-Proxy Deployment

### 1. Reverse Proxy Under `/app/`

This topology is supported.

Why:
- `templates/index.html` now uses relative asset links
- `static/manifest.json` uses relative `start_url`, `scope`, and icon paths
- `static/sw.js` derives its API prefix from the service-worker registration scope

If the app is reverse-proxied under `/app/`, the frontend assets resolve under `/app/` automatically.

Typical shape:

```text
browser
  -> https://host/app/
  -> reverse proxy
  -> Flask on http://127.0.0.1:5000/
```

### 2. Direct-Root Serving

The Flask app also serves correctly at root:
- `/`
- `/manifest.json`
- `/sw.js`
- `/api/*`

The frontend now uses relative shell asset paths, so root-path deployments do not require a separate `/app/` rewrite layer.

## Operational Notes

- `positions.json` stores wrapper-managed playback state
- the wrapper has no end-user auth
- if exposed publicly, the wrapper exposes torrent listing, add/remove, and playback operations
- keep service credentials out of versioned deployment config

## Installability

The shell now includes an install affordance in the UI.

- Browsers that support `beforeinstallprompt` can surface a native install flow.
- iPad/iPhone Safari users get explicit “Share -> Add to Home Screen” guidance instead of a dead install action.

This behavior lives in `templates/index.html` and depends on:
- a valid manifest at `/manifest.json`
- a registered service worker at `/sw.js`

## Recommended Verification

After deployment or path changes, use `docs/SMOKE-TESTS.md`.

At minimum verify:
- `/` returns the UI shell
- `/manifest.json` returns the manifest
- `/sw.js` returns the service worker
- `/api/status` reflects upstream availability
- `/api/torrents` returns structured library diagnostics
- playback-related flows still work against a real TorrServer instance

For a quick local pass, start the wrapper and run:

```bash
python scripts/smoke_check.py
```

For production verification against the live Oracle deployment:

```bash
python scripts/smoke_prod.py
```

Expect `9/9 PASS`.
