# Phase 1 Handoff — Oracle Baseline Complete

**Completed:** 2026-05-11
**Target host:** `158.101.214.234` (Oracle `vless-x86-2`, `eu-amsterdam-1`, Always Free)

## Credentials

Stored on-box at `/etc/torrstream/torrserver.env` (root-owned, mode 600).

| Key | Value |
|---|---|
| TorrServer user | `torrstream` |
| TorrServer password | `m6wkt8jhrsb4x5qiz3u2ngyo` |

**For Lampa TorrServer settings on each client device:** set user/password on the *TorrServer* config page inside Lampa.

## Service Surface

| Service | Port | Purpose |
|---|---|---|
| Caddy | 80 | Public HTTP reverse proxy → Flask wrapper :5000 |
| Xray | 443 | VLESS Reality (untouched; pre-existing) |
| Flask wrapper | 5000 | Localhost-only. Caddy proxies to it. |
| TorrServer | 8090 | Public HTTP, BasicAuth required. Lampa streams direct. |

## Endpoints (externally reachable)

| URL | Status | Use |
|---|---|---|
| `http://158.101.214.234/` | 200 | TorrStream shell (HTML) |
| `http://158.101.214.234/api/status` | 200 | Stack health probe |
| `http://158.101.214.234/api/torrents` | 200 | Library (empty until Phase 2) |
| `http://158.101.214.234/manifest.json` | 200 | PWA manifest |
| `http://158.101.214.234/sw.js` | 200 | Service worker |
| `http://158.101.214.234/static/lampa-sync.js` | 200 | Lampa plugin |
| `http://158.101.214.234:8090/` | 401 | TorrServer admin (auth required) |

## On-box Paths

| Path | Owner | Purpose |
|---|---|---|
| `/opt/torrstream/app/` | ubuntu | Wrapper code (git clone of `trikiman/torrstream-wrapper`) |
| `/opt/torrstream/venv/` | ubuntu | Python venv (flask 3.1.3, requests 2.34.0) |
| `/var/lib/torrserver/` | ubuntu | TorrServer state dir (accs.db here) |
| `/var/lib/torrserver/accs.db` | ubuntu:600 | JSON `{user: plaintext_pass}` |
| `/etc/torrstream/torrserver.env` | root:600 | Wrapper's env file (consumed by Flask systemd unit) |
| `/etc/caddy/Caddyfile` | caddy | Caddy config (auto_https off, :80 → :5000) |
| `/var/log/torrstream/torrserver.log` | ubuntu | TorrServer stdout/stderr |
| `/var/log/torrstream/flask.log` | ubuntu | Flask wrapper stdout/stderr |
| `/var/log/torrstream/caddy-access.log` | caddy | Caddy access log |
| `/swapfile` | root:600 | 4 GB swap, persisted in /etc/fstab |

## Systemd Units

| Unit | After | Restart |
|---|---|---|
| `torrserver.service` | `network-online.target` | on-failure, 10s |
| `flask-wrapper.service` | `torrserver.service` | on-failure, 10s |
| `caddy.service` (distro) | — | on-failure |

All three enabled and verified across a reboot.

## SSH Access

```
ssh -i "e:\Projects\vless\oracle_vless_key" ubuntu@158.101.214.234
```

## Deviations from Plan

1. **Port 80 conflict with pre-existing nginx** — the Oracle host was running nginx fronting a VLESS WebSocket transport on `/stream` → 127.0.0.1:10001. User confirmed nginx is non-critical (VLESS only needs the xray :443 Reality leg). Stopped and disabled nginx to free port 80 for Caddy.
2. **TorrServer accs.db format** — the plan assumed bcrypt hashes, but MatriX.141 expects **plaintext** `{user: password}` JSON. Rewrote accs.db as plaintext. Auth works; file permissions 600 keep the creds host-local.
3. **Caddy log file permissions** — Caddy runs as `caddy:caddy`, not `ubuntu`. Changed `/var/log/torrstream` to 755 and pre-created `caddy-access.log` with `caddy:caddy` ownership.
4. **Swap was already 2 GB** — the Oracle image shipped with an existing `/swapfile`. Swapped off, re-sized to 4 GB with `fallocate`, re-formatted, swapped on. fstab entry already present.

## Known Concerns for Phase 2

1. **`position_entries: 1` in status** — this is a repo-shipped default from `positions.json` at `/opt/torrstream/app/positions.json`. Phase 2 MIGR-01 replaces it with the AWS production file.
2. **Nginx disabled, not removed** — `sudo systemctl disable nginx` will prevent it from starting, but the package is still installed. If user wants to fully remove: `sudo apt-get purge -y nginx nginx-common`.
3. **No HTTPS yet** — Caddy has `auto_https off`. Phase 3 DNS cutover will:
   - Flip DNS for `tv.trikiman.shop` to 158.101.214.234
   - Re-configure Caddyfile to use `tv.trikiman.shop { reverse_proxy :5000 }` (auto Let's Encrypt kicks in)
4. **GitHub webhook not set up** — Phase 2 plan 02-02 decides whether to generate a new Oracle secret or reuse the AWS one. Current `app.py` has the `/api/github-webhook` endpoint; only needs `GITHUB_WEBHOOK_SECRET` added to the Flask env file.
5. **TorrServer has 0 torrents** — empty state. Phase 2 MIGR-02 migrates the 3 current torrents from AWS.

## Open Decisions for Phase 2

- **D1** — Migration method: stop TorrServer on AWS, rsync `/var/lib/torrserver` to Oracle, start? Or re-add torrents by magnet and accept re-indexing?
- **D2** — Staging DNS: test Phase 2 against `158.101.214.234` directly, or add a temporary DNS record like `tv-staging.trikiman.shop`?
- **D3** — GitHub webhook secret: new Oracle-only secret, or reuse AWS secret?
- **D4** — AWS cutover window: how long to keep AWS running post-DNS? 7 days? 1 day?

## Next: `/gsd-plan-phase 2`
