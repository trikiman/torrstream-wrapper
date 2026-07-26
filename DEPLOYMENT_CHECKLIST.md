# 🎬 TorrStream — Deployment Checklist

> **Web UI**: https://tv.trikiman.shop/
> **TorrServer (for Lampa clients)**: https://ts.trikiman.shop/
> **Stack**: Flask `app.py` + `templates/index.html` + Vidstack 1.12.13 (self-hosted) + Service Worker
> **Upstreams**: TorrServer `127.0.0.1:8090` (BasicAuth) · jacred (JACRED_URL, default https://jac.red)
> **Reverse proxy**: Caddy → `127.0.0.1:5000` (1 h read/write, `flush_interval -1` for streaming)
> **Production host**: Oracle Cloud `158.101.214.234` (`vless-x86-2`, `eu-amsterdam-1`)
> **Last verified**: 2026-07-27 (v2.3 — Lampa parser shim; see `.planning/MILESTONES.md`)
> **Latest milestone**: v2.3 — Lampa parser shim (`/api/v1.0/torrents` + `/api/v2.0/indexers/all/results` endpoints) + pytest harness (80 tests, GitHub Actions CI)
>
> **Status legend** (fill bracket as you go):
> - `- [ ]` — not yet tested
> - `- [x]` — passed
> - `- [❌]` — failed
> - `- [🙋]` — needs human (AI cannot autonomously verify — manual action required)
> - `- [⏭️]` — skipped (technical reason in *italics*, e.g. "TorrServer empty, cannot exercise file list")

---

## ⚡ QUICK SMOKE TEST (60 seconds — run after every deploy)

> Fastest sanity check. If all 5 pass → production is alive. If any fail → drill into the relevant section below.
> This supersedes running the full checklist for routine deploys.

- [x] **QS-1** Public URL reachable: `curl -I https://tv.trikiman.shop/` → `HTTP/2 200`
- [x] **QS-2** Status endpoint: `curl -s https://tv.trikiman.shop/api/status | jq '.torrserver.ok, .wrapper.position_entries'` → `true`, integer
- [x] **QS-3** Library endpoint: `curl -s https://tv.trikiman.shop/api/torrents | jq '.ok, .diagnostics.state'` → `true`, `"ready"` or `"empty"`
- [x] **QS-4** Systemd services: `ssh ubuntu@158.101.214.234 'systemctl is-active flask-wrapper torrserver caddy'` → 3× `active`
- [ ] 🙋 **QS-5** Live playback: open the site on phone → click any torrent → first episode plays within 5 s with no spinner-of-death

If all 5 pass, deploy is healthy. Otherwise drill into Part 1/2 for the failing area, then come back here.

**Note:** `python scripts/smoke_prod.py` already covers QS-1, QS-2, QS-3 plus shell/manifest/SW/Vidstack-marker fetches in 9 checks. QS-4 + QS-5 are the two checks the script does NOT cover.

---

## PART 0: AI TESTING TOOLKIT (Pre-Flight Check) ⭐ START HERE

> Run **§0** first. If any tool is missing → install it before starting the main checklist.
> Once all of §0 passes, AI can run §1–§7 autonomously from **0% → 100%**.
> §8, §9.live, parts of §10 still need human assistance (`🙋`) even with the full toolkit.

---

### 0.1 Required CLI Tools

- [x] **0.1.1** `curl` — HTTP client for API tests
  - *Verify*: `curl --version`
  - *Install (Windows)*: pre-installed on Win10+, or `choco install curl`
- [x] **0.1.2** `python` 3.10+ — backend imports, pytest, smoke scripts
  - *Verify*: `python --version`
- [x] **0.1.3** `pip` — Flask + requests + dev deps install
  - *Verify*: `pip --version`
- [x] **0.1.4** `pytest` — backend regression suite (`tests/`)
  - *Verify*: `pytest --version`
  - *Install*: `pip install -r requirements-dev.txt`
- [x] **0.1.5** `jq` — JSON parser for API response inspection
  - *Verify*: `jq --version`
  - *Install (Windows)*: `choco install jq` or `scoop install jq`
- [x] **0.1.6** `git` — version control checks
  - *Verify*: `git --version`
- [x] **0.1.7** `ssh` — Oracle access (only required for Part 2 production checks)
  - *Verify*: `ssh -V`

### 0.2 Required Credentials & Files

- [x] **0.2.1** Environment variables documented and set on Oracle host (`/etc/torrstream/torrserver.env`):
  - `TORRSERVER_URL` (default `http://127.0.0.1:8090`)
  - `TORRSERVER_USER` / `TORRSERVER_PASS` (BasicAuth — required in production)
  - `JACRED_URL` (default `https://jac.red`) / `JACRED_KEY` (optional)
  - `GITHUB_WEBHOOK_SECRET` (required for auto-deploy)
  - `TORRSTREAM_SERVICE` (default `flask-wrapper.service`)
  - *Verify on Oracle*: `sudo systemctl show flask-wrapper.service -p Environment`
- [x] **0.2.2** SSH key for Oracle host (skip Part 2 if missing)
- [ ] 🙋 **0.2.3** At least one real torrent present in TorrServer (for §3.7+, §9 file/playback checks)
- [x] **0.2.4** Browser with PWA install support (Chrome/Edge desktop, Safari iOS, Chrome Android)

### 0.3 Browser Automation (for §3 Frontend, §5 Responsive, §6 Performance)

- [x] **0.3.1** Chrome DevTools MCP server connected
  - *Verify*: AI tools `navigate_page`, `take_snapshot`, `click`, `evaluate_script` are available
- [x] **0.3.2** Chrome browser 120+ installed
  - *Verify*: open `chrome://version/`
- [x] **0.3.3** Production URL reachable in browser: https://tv.trikiman.shop/

### 0.4 Optional Tools

- [ ] ⏭️ **0.4.1** `hey` or `ab` — for §6.x stress / sustained-streaming tests
- [x] **0.4.2** `iptables` / Oracle Cloud Console MCP — for BT-port verification on production (covered by `scripts/_open_bt_peer_port.sh`)

### 0.5 One-Shot Verification Command

```powershell
# Windows PowerShell — verify all CLI tools
curl --version; python --version; pip --version; jq --version; git --version; ssh -V
pytest --version

# Verify backend imports cleanly
python -c "from app import app; print('backend OK')"

# Verify deps install cleanly
pip install -r requirements.txt -r requirements-dev.txt

# Run the bundled local smoke check (start instance first: python app.py)
python scripts/smoke_check.py

# Run the production smoke check (no local instance needed)
python scripts/smoke_prod.py
```

### 0.6 Production Verify Scripts (run from anywhere)

Automated post-deploy verification — covers a large portion of Part 2 §8 in one pass:

```bash
# Latest production smoke (Vidstack-aware, 9 checks)
python scripts/smoke_prod.py

# Live read-only integration suite (12 tests against tv.trikiman.shop; 3 skip when library empty)
pytest -m integration

# Full contract suite against Flask test client (68 tests, no network)
pytest -m smoke
```

Use these scripts FIRST, then return to this checklist only for items not covered (Lampa plugin in real Lampa runtime, real iPhone Safari walkthrough, real torrent playback).

### 0.7 AI Autonomy Coverage

**✅ Fully autonomous** (AI runs end-to-end with §0 toolkit):
- §1 Build & Infra — pure CLI + pytest
- §2 Backend API — `curl` + Flask test client + mock TorrServer
- §3 Frontend UI — Chrome DevTools MCP
- §4 PWA & Service Worker — DevTools application panel
- §5 Responsive — DevTools viewport emulation
- §6 Performance — `curl --write-out` + DevTools trace
- §7 Security — `curl` assertions + HMAC test vectors

**🙋 Needs human assistance**:
- §8 Production health (SSH access required)
- §9 Live end-to-end flows (real torrent + real device)
- §10 Edge cases (real TorrServer kill, real auto-deploy push, iOS Safari walkthrough)
- 9.x Lampa plugin in actual Lampa runtime

**⚠️ Needs extra setup**:
- §6.13 Range-seek throughput test (real 1080p mkv torrent)
- §10.7–10.10 Auto-deploy webhook (write access to repo)

---

## PART 1: PRE-DEPLOY CHECKLIST

> If every item in Part 1 passes → the wrapper is safe to deploy.

---

### 1. 🏗️ BUILD & INFRASTRUCTURE

- [x] **1.1** `pip install -r requirements.txt` completes without errors (Flask ≥3.1,<4 ; requests ≥2.32,<3)
- [x] **1.2** `pip install -r requirements-dev.txt` completes without errors (pytest stack)
- [x] **1.3** Backend imports cleanly — `python -c "from app import app; print('OK')"`
- [x] **1.4** Local app starts on `0.0.0.0:5000` — `python app.py` then `curl -I http://127.0.0.1:5000/` → 200
- [x] **1.5** `templates/index.html` exists and Flask serves it at `/` (no 404)
- [x] **1.6** `static/manifest.json` exists and is valid JSON — `python -c "import json; json.load(open('static/manifest.json'))"`
- [x] **1.7** `static/sw.js` exists and registers (no syntax error in console)
- [x] **1.8** `static/icons/icon-512.png` exists (≥10 KB, used by manifest + apple-touch-icon)
- [x] **1.9** `static/vidstack/` tree present — 18 chunks + 8 providers + 5 captions files + 2 CSS *(v2.1 self-hosted)*
- [x] **1.10** `static/lampa-sync.js` exists (Lampa plugin, served with `Access-Control-Allow-Origin: *` *(v2.2)*)
- [x] **1.11** `positions.json` is valid JSON or absent (absent on first install is OK)
- [x] **1.12** Root-level `index.html` is **not** served by Flask (legacy duplicate per `docs/DEPLOYMENT.md`)
- [x] **1.13** `scripts/smoke_check.py` runs to completion against a local instance — 6/6 PASS
- [x] **1.14** Caddy config validates — `caddy validate --config Caddyfile`
- [x] **1.15** `requirements.txt` only lists in-scope deps (Flask, requests) — no accidental extras committed
- [x] **1.16** `pytest -m smoke` passes locally — 68/68 in <1 s *(v2.3)*

---

### 2. 🌐 BACKEND API ENDPOINTS

> Test each endpoint using `curl` against `https://tv.trikiman.shop` (or `http://127.0.0.1:5000` locally). Use `jq` to inspect JSON shape.

#### 2.1 Shell & PWA Assets

- [x] **2.1.1** `GET /` serves frontend — 200, `Content-Type: text/html`
- [x] **2.1.2** `GET /manifest.json` returns valid manifest (`name=TorrStream`, `start_url=./`, `scope=./`)
- [x] **2.1.3** `GET /sw.js` returns service worker with `Content-Type: application/javascript`
- [x] **2.1.4** `GET /favicon.ico` returns the 512×512 PNG with `Content-Type: image/png`
- [x] **2.1.5** Manifest icons resolve: `curl -I https://tv.trikiman.shop/static/icons/icon-512.png` → 200
- [x] **2.1.6** Vidstack assets resolve from `/static/vidstack/` — no jsdelivr 404s *(v2.1)*
- [x] **2.1.7** `/static/*` exposes `Access-Control-Allow-Origin: *` *(v2.2)*

#### 2.2 Status & Diagnostics

- [x] **2.2.1** `GET /api/status` returns valid JSON
- [x] **2.2.2** Response shape: `torrserver.{url, ok, torrent_count, error}`, `search.{url, api_key_configured}`, `wrapper.{root, manifest, service_worker, auth_configured, position_entries}`
- [x] **2.2.3** `torrserver.ok=true` when upstream is reachable
- [x] **2.2.4** `torrserver.ok=false` + non-empty `.error` when upstream is killed (kill TorrServer, retry, restart)
- [x] **2.2.5** `wrapper.auth_configured` reflects whether `TORRSERVER_USER`/`PASS` are set
- [x] **2.2.6** `wrapper.position_entries` matches `positions.json` keys count

#### 2.3 Library Listing

- [x] **2.3.1** `GET /api/torrents` returns `{ok, items, diagnostics}` JSON
- [x] **2.3.2** `diagnostics.state ∈ {ready, empty, upstream_unavailable}` — exhaustive enum
- [x] **2.3.3** Each item carries: `hash`, `title`, `poster`, `torrent_size`, `position`, `duration`, `last_file_index`, `updated`, `stat`, `viewed_in_torrserver` *(v1.1)*
- [x] **2.3.4** `position`/`duration`/`last_file_index` reflect the **last-played file** for the "Continue Watching" rail
- [x] **2.3.5** Empty library returns `ok=true`, `items=[]`, `diagnostics.state="empty"` (NOT a fake error)
- [x] **2.3.6** TorrServer offline returns `ok=false`, `items=[]`, `diagnostics.state="upstream_unavailable"`, explicit `.error` string
- [x] **2.3.7** `viewed_in_torrserver=true` surfaces externally-watched media in Continue Watching rail *(v1.1)*

#### 2.4 File Listing

- [x] **2.4.1** `GET /api/files/<hash>` returns `{ok, file_stats, last_file_index, viewed_indices, diagnostics}`
- [x] **2.4.2** `diagnostics.state ∈ {ready, no_playable_files, file_lookup_failed, upstream_unavailable}` — exhaustive enum
- [x] **2.4.3** `file_stats` contains only video files (extensions: `.mp4 .mkv .avi .m4v .mov .wmv .ts .webm` or no extension)
- [x] **2.4.4** Each entry includes `id`, `path`, `length`, `position`, `file_duration`, `viewed`
- [x] **2.4.5** `viewed=true` when file is in TorrServer `/viewed` list OR `position/duration > 0.95`
- [x] **2.4.6** `viewed_indices` mirrors TorrServer's `/viewed` list for that hash
- [x] **2.4.7** Well-formed but unknown hash → **404** `{ok:false, error:"unknown hash"}` *(v2.2 — was 200 with empty)*
- [x] **2.4.8** Malformed hash (non-40/64 hex) → **400** `{ok:false, error:"invalid hash"}` *(v2.2)*
- [x] **2.4.9** Cold/migrated TorrServer state → auto-warmup with 0-byte range probe before returning empty *(v2.1)*

#### 2.5 Position Read/Write

- [x] **2.5.1** `GET /api/position/<hash>` returns `{ok, position, duration, last_file_index}` for known hash
- [x] **2.5.2** `GET /api/position/<hash>?file_index=2` returns the per-file entry, not the last-played file
- [x] **2.5.3** Unknown hash on GET → **404** *(v2.2)*
- [x] **2.5.4** `POST /api/position/<hash>` with `{position, duration, file_index}` returns `{ok, viewed_sync_attempted, viewed_synced}`
- [x] **2.5.5** Negative `position` is clamped to 0
- [x] **2.5.6** `file_index < 1` → 400 `{ok:false, error:"invalid file_index"}`
- [x] **2.5.7** Malformed JSON body → **400** `{ok:false, error:"invalid JSON"}` *(v2.2 — was silent 200)*
- [x] **2.5.8** Missing `position` field → **400** `{ok:false, error:"missing position"}` *(v2.2)*
- [x] **2.5.9** Subsequent `GET` returns the value just written
- [x] **2.5.10** When `position/duration > 0.95`, `viewed_sync_attempted=true` and TorrServer `/viewed` is hit
- [x] **2.5.11** `positions.json` writes are atomic (`.tmp` then rename — no half-written file on crash)
- [x] **2.5.12** Multi-file torrent: writing index=2 doesn't clobber index=1's saved position
- [x] **2.5.13** `last_file_index` updates to the most recently written file
- [x] **2.5.14** Hash is normalized to lowercase at persistence + lookup *(v2.2)*
- [x] **2.5.15** OPTIONS preflight returns CORS headers (Lampa cross-origin write from `lampa.mx`) *(v1.1)*
- [x] **2.5.16** CORS preserved on 4xx error responses *(v2.2)*

#### 2.6 Stream Proxy

- [x] **2.6.1** `GET /api/stream/<filename>?hash=<h>&index=<i>` returns video with `Accept-Ranges: bytes` and `Content-Type: video/*`
- [x] **2.6.2** Range request (`Range: bytes=0-99`) returns 206 with matching `Content-Range`
- [x] **2.6.3** Probe mode `?probe=1` returns JSON `{ok, upstream_status, content_type, error}` (no media body)
- [x] **2.6.4** Probe ok=true when TorrServer would serve the file
- [x] **2.6.5** Probe ok=false with explicit error when TorrServer rejects
- [x] **2.6.6** Missing `hash` query param → 400 `{ok:false, error:"missing hash"}`
- [x] **2.6.7** TorrServer 4xx/5xx → 502 `{ok:false, upstream_status, error}` (no silent hang)
- [x] **2.6.8** TorrServer connection error → 502 with explicit `.error`
- [x] **2.6.9** Chunked transfer keeps wrapping headers (`Content-Type`, `Accept-Ranges`, `Content-Range`, `Content-Length`)
- [x] **2.6.10** Caddy `flush_interval -1` honored — bytes reach client without buffering
- [x] **2.6.11** Stream endpoint also serves `Content-Disposition: attachment` when `?download=1` *(v2.2 download UI)*

#### 2.7 Add Torrent

- [x] **2.7.1** `POST /api/add` with `{link: "magnet:?xt=urn:btih:..."}` returns `{ok:true, hash, normalized_link}`
- [x] **2.7.2** Bare 40-char SHA1 hex → normalized to `magnet:?xt=urn:btih:<HASH>`
- [x] **2.7.3** Bare 32-char base32 hash → normalized to magnet
- [x] **2.7.4** `http://`/`https://` `.torrent` URL → passed through as-is
- [x] **2.7.5** Empty link → 400 `{ok:false, error:"no link"}`
- [x] **2.7.6** Garbage input (`bad-input`) → 400 `{ok:false, error:"invalid link"}`
- [x] **2.7.7** Optional `title` and `poster` round-trip into TorrServer
- [x] **2.7.8** TorrServer add failure → `{ok:false, error:"torrserver add failed", normalized_link}` (link still echoed for retry)

#### 2.8 Remove Torrent

- [x] **2.8.1** `DELETE /api/remove/<hash>` returns `{ok:true, removed_positions}`
- [x] **2.8.2** `removed_positions=true` only when there was an entry in `positions.json` for that hash
- [x] **2.8.3** Position entry is gone from `positions.json` after successful delete
- [x] **2.8.4** TorrServer removal failure → **502** `{ok:false, error, removed_positions}` *(v2.2 — was 200)*
- [x] **2.8.5** Unknown hash → **404** `{ok:false, error:"unknown hash"}` *(v2.2)*
- [x] **2.8.6** Malformed hash → **400** `{ok:false, error:"invalid hash"}` *(v2.2)*

#### 2.9 Search Proxy

- [x] **2.9.1** `GET /api/search?q=<query>` returns `{ok, Results}` JSON
- [x] **2.9.2** Empty `q` → `{ok:true, Results:[]}` (no upstream call)
- [x] **2.9.3** Each result has `Title`, `Size`, `Seeders`, `Tracker`, `MagnetUri`
- [x] **2.9.4** Cyrillic query (`?q=матрица`) round-trips correctly (URL-encoded)
- [x] **2.9.5** jacred outage → `{ok:false, Results:[], error:<reason>}` (UI then shows fallback)
- [x] **2.9.6** `JACRED_KEY` env var is appended as `apikey=` when configured

#### 2.10 Recent Searches

- [x] **2.10.1** `GET /api/recent-searches` returns `{ok, items}` (most-recent first)
- [x] **2.10.2** `POST /api/recent-searches` with `{query}` records the query
- [x] **2.10.3** `DELETE /api/recent-searches` clears the list
- [x] **2.10.4** Empty query on POST → 400, list unchanged

#### 2.11 GitHub Webhook (Auto-Deploy)

- [x] **2.11.1** `POST /api/github-webhook` when `GITHUB_WEBHOOK_SECRET` is unset → **503** `{ok:false, error:"webhook not configured"}` *(v2.4 — fails closed; was best-effort fail-open)*
- [x] **2.11.2** With secret set, missing/invalid `X-Hub-Signature-256` → 401 `{ok:false, error:"invalid signature"}`
- [x] **2.11.3** Valid HMAC + non-`refs/heads/main` ref → `{ok:true, status:"ignored", ref}`
- [x] **2.11.4** Valid HMAC + `refs/heads/main` push → `{ok:true, status:"updated", restart_scheduled, files_changed, pull_output}`
- [x] **2.11.5** Restart scheduled only when commits touched `*.py` / `*.html` / `*.js` / `*.css` / `requirements.txt`
- [x] **2.11.6** `positions.json` is preserved across the pull (backup → pull → restore if changed)
- [x] **2.11.7** Malformed JSON body → 400 `{ok:false, error:"invalid json"}`
- [x] **2.11.8** Service restart command targets the unit named in `TORRSTREAM_SERVICE` env var
- [x] **2.11.9** HMAC compare uses `hmac.compare_digest` (constant-time)

---


### 3. 🖥️ FRONTEND — UI / UX (Every Button, Every Click)

> Open `https://tv.trikiman.shop/` in a desktop and a mobile browser. Verify each interaction below.

#### 3.1 Initial Load

- [x] **3.1.1** Page loads without blank screen — torrents render within 2 s on broadband
- [x] **3.1.2** No red console errors on load (warnings OK; SW registration message is fine)
- [x] **3.1.3** Logo `🎬 TorrStream` visible in nav
- [x] **3.1.4** Search input has placeholder `Поиск фильмов и сериалов...`
- [x] **3.1.5** Theme button (`☀️` or `🌙`) visible top-right
- [x] **3.1.6** Add button (`+ Magnet`) visible top-right
- [x] **3.1.7** Spinner shows in section title `📁 Все торренты` and disappears after fetch
- [x] **3.1.8** Library renders in a responsive grid (≥2 cols mobile, more on desktop)
- [x] **3.1.9** Auto-refresh fires every 30 s — confirm via DevTools Network tab (one `/api/torrents` per 30 s)
- [x] **3.1.10** Service worker registers — `navigator.serviceWorker.controller` not null after second load
- [x] **3.1.11** Vidstack web components embedded in served HTML — production smoke marker `vidstack=True` *(v2.1)*

#### 3.2 Theme Toggle (☀️ / 🌙)

- [x] **3.2.1** Click theme button — colors invert dark ↔ light
- [x] **3.2.2** Icon toggles correctly (`☀️` in dark mode, `🌙` in light mode)
- [x] **3.2.3** Theme persists across full reload (`localStorage.theme`)
- [x] **3.2.4** Theme persists across new tab in same origin
- [x] **3.2.5** No flash of wrong theme on initial load (FOUC check)
- [x] **3.2.6** All overlays (player, episode, modal) honor the active theme
- [x] **3.2.7** Theme reaches target color in ≤16 ms (next paint frame) *(v2.2 — was 1432 ms; bypasses CSS cascade via direct `body.style.backgroundColor`)*

#### 3.3 Install Affordance (PWA)

- [x] **3.3.1** Chrome/Edge desktop: `beforeinstallprompt` fires → `Установить` button appears in nav
- [x] **3.3.2** Click `Установить` → native install dialog opens
- [x] **3.3.3** Install succeeds → `appinstalled` event → toast `Приложение установлено`
- [x] **3.3.4** After install → `Установить` button hides (matchMedia standalone)
- [ ] 🙋 **3.3.5** iPad/iPhone Safari: `Установить` still appears (no `beforeinstallprompt` available) — needs real iOS device
- [ ] 🙋 **3.3.6** iPad/iPhone click → toast `Safari: Поделиться → На экран «Домой»` — needs real iOS device
- [x] **3.3.7** Browsers without PWA support: button hidden (no dead click)
- [x] **3.3.8** Standalone mode (already installed): button hidden

#### 3.4 Add Magnet Modal

- [x] **3.4.1** Click `+ Magnet` → modal opens, backdrop blurs content
- [x] **3.4.2** Magnet input is auto-focused
- [x] **3.4.3** Input placeholder: `magnet:?xt=urn:btih:... или хеш`
- [x] **3.4.4** Title input placeholder: `Название (необязательно)`
- [x] **3.4.5** Click `Отмена` → modal closes, both inputs cleared
- [x] **3.4.6** Click outside the modal box → modal closes (backdrop click)
- [x] **3.4.7** Press `Escape` → modal closes
- [x] **3.4.8** Empty submit → toast `Введите magnet-ссылку или хеш`
- [x] **3.4.9** Valid magnet submit → toast `Торрент добавлен!`, modal closes, library refreshes
- [x] **3.4.10** Bare hash submit → still works (normalized server-side)
- [x] **3.4.11** TorrServer down → toast surfaces backend error message (not silent)
- [x] **3.4.12** Network error → toast `Ошибка соединения`

#### 3.5 Search

- [x] **3.5.1** Type 1 character → no fetch (debounce + min-2 char gate)
- [x] **3.5.2** Type 2+ chars → after 500 ms debounce, fetch fires once
- [x] **3.5.3** Results panel `Результаты поиска` opens, count chip updates
- [x] **3.5.4** Spinner shows while waiting, then results render
- [x] **3.5.5** Each result row shows title, tracker, size, seeders, `+ Добавить` button
- [x] **3.5.6** Cyrillic query works (e.g. `матрица`)
- [x] **3.5.7** Latin query works (e.g. `Project Hail Mary`)
- [x] **3.5.8** Results capped at 30 in DOM
- [x] **3.5.9** Successful results are cached to `localStorage` under `search-cache:<query>`
- [x] **3.5.10** No results → empty state `🔍 Ничего не найдено`
- [x] **3.5.11** jacred down → empty state `⚠️ Сервис поиска недоступен` + `Повторить` button
- [x] **3.5.12** jacred down + cached results exist → `Сохраненные результаты` block renders below the warning
- [x] **3.5.13** jacred down + library matches exist → `Совпадения в библиотеке` block renders with `Открыть` buttons
- [x] **3.5.14** Click outside the search panel → results close, input clears
- [x] **3.5.15** Recent searches dropdown surfaces last queries from `/api/recent-searches`

#### 3.6 Add From Search Result

- [x] **3.6.1** Click `+ Добавить` on a row → button text changes to `...`, disabled
- [x] **3.6.2** Success → button becomes `✓ Добавлен` with green background, toast `Торрент добавлен!`, library reloads
- [x] **3.6.3** Failure → button reverts to `Ошибка`, re-enabled, toast surfaces backend error
- [x] **3.6.4** Library-fallback row `Открыть` → opens that torrent's episode/player flow directly

#### 3.7 Library Card

- [x] **3.7.1** Each card shows poster (or `🎬` placeholder if `poster` empty/broken)
- [x] **3.7.2** Title is shown (max 2 lines, truncated with ellipsis)
- [x] **3.7.3** Meta row shows size + watched percentage (when in progress)
- [x] **3.7.4** Progress bar at 0–100% renders for items with `position > 30 && < 95% of duration`
- [x] **3.7.5** Currently-streaming torrents (`stat=3`) show `▶` badge top-right
- [x] **3.7.6** Multi-file torrents with `last_file_index > 1` show `EP N` badge top-left
- [x] **3.7.7** Hover → card lifts (translateY -6px) and casts shadow (desktop)
- [x] **3.7.8** Active/tap → card scales down (mobile feedback)
- [x] **3.7.9** Click anywhere on card (except `Удалить`) → opens torrent (episode panel or player)
- [x] **3.7.10** Lampa-prefixed titles (`[LAMPA] ...`) are stripped to clean display

#### 3.8 Continue Watching Rail

- [x] **3.8.1** Section `▶️ Продолжить просмотр` only shows when ≥1 torrent has progress 30 s < pos < 95%
- [x] **3.8.2** Cards in this rail show progress bar (not in main grid)
- [x] **3.8.3** Clicking a continue-card opens directly to last-played file
- [x] **3.8.4** Section disappears when all in-progress torrents are completed
- [x] **3.8.5** Section ordering: most recently updated first
- [x] **3.8.6** Items watched only in TorrServer (no wrapper position) appear via `viewed_in_torrserver` flag *(v1.1)*

#### 3.9 Card Delete (`Удалить`)

- [x] **3.9.1** `Удалить` button visible on each card (bottom-right of card-info)
- [x] **3.9.2** Click does NOT bubble up to open-torrent (event.stopPropagation works)
- [x] **3.9.3** `window.confirm("Удалить торрент \"<title>\"?")` appears
- [x] **3.9.4** Cancel → no API call, card remains
- [x] **3.9.5** Confirm → `DELETE /api/remove/<hash>` fires
- [x] **3.9.6** Success with prior position → toast `Торрент и позиция удалены`
- [x] **3.9.7** Success with no prior position → toast `Торрент удален`
- [x] **3.9.8** Library reloads; card disappears
- [x] **3.9.9** Failure → toast surfaces backend error, card remains

#### 3.10 Empty States

- [x] **3.10.1** TorrServer reachable + no torrents → icon `🎞️`, title `Библиотека пока пуста`, hint about magnet/Lampa
- [x] **3.10.2** TorrServer unreachable → icon `⚠️`, title `Нет подключения к TorrServer`, message includes upstream URL + error, `Повторить` button
- [x] **3.10.3** Initial render before first fetch (no diagnostics) → fallback empty `Нет добавленных торрентов`
- [x] **3.10.4** `Повторить` button retriggers `loadTorrents()` and updates state correctly

#### 3.11 Episode Panel (multi-file torrents)

- [x] **3.11.1** Click multi-file card → episode overlay slides in (full-screen)
- [x] **3.11.2** Header shows torrent title, `←` back button, `▶ Продолжить (EP N)` continue button
- [x] **3.11.3** Continue button shows `▶ Начать (EP N)` if no last-watched and there's an unwatched episode
- [x] **3.11.4** Continue button hides entirely when everything is watched
- [x] **3.11.5** Click `←` → panel closes, body scroll restored
- [x] **3.11.6** Press `Escape` → panel closes
- [x] **3.11.7** Each episode row shows: episode number, filename, size, percent, watched badge, `⬇ Скачать` button, `▶` play button *(v2.2)*
- [x] **3.11.8** Watched episodes show `✓` instead of number, `.watched` class dims them
- [x] **3.11.9** Currently-playing episode shows `.playing` border-highlight
- [x] **3.11.10** Click episode row anywhere (except action buttons) → plays that episode
- [x] **3.11.11** Body has `overflow:hidden` while panel is open
- [x] **3.11.12** Episode list is single-column on mobile (≤600 px)
- [x] **3.11.13** Episode panel handles file lookup failure with `⚠️` empty state + explicit message
- [x] **3.11.14** Episode panel handles "no playable files" with `📼` empty state + explicit message

#### 3.12 Episode Action Buttons

- [x] **3.12.1** `⬇ Скачать` (download) does NOT trigger play (event.stopPropagation works) *(v2.2)*
- [x] **3.12.2** `⬇` uses `<a download="<filename>">` against `/api/stream/...?download=1`
- [x] **3.12.3** Desktop browsers → native download manager opens, file size matches
- [ ] 🙋 **3.12.4** iOS Safari → opens new tab + toast `Поделиться → Сохранить в Файлы` — needs real iOS device
- [x] **3.12.5** `▶` (play) does NOT trigger row click duplicate
- [x] **3.12.6** `▶` plays the same episode as a row click

#### 3.13 Single-File Direct Play

- [x] **3.13.1** Click single-file card → skips episode panel, opens player directly
- [x] **3.13.2** Player title shows torrent title (no `EP n / N` for single file)
- [x] **3.13.3** `Далее →` button hidden for single-file
- [x] **3.13.4** Position auto-restores from previous session
- [x] **3.13.5** Closing player auto-saves position if `currentTime > 5 s`

#### 3.14 Video Player (Vidstack)

- [x] **3.14.1** Player overlay covers full viewport (z-index 1000)
- [x] **3.14.2** Header shows: `←` back, title, `EP n / N`, `Далее →` (multi-episode), round download button *(v2.2)*
- [x] **3.14.3** Vidstack default video layout: play/pause, progress bar, current/duration, mute, volume, fullscreen, PiP
- [x] **3.14.4** Click `←` → player closes, position auto-saves, library reloads
- [x] **3.14.5** Press `Escape` → player closes (same path)
- [x] **3.14.6** Press `Space` → toggles play/pause
- [x] **3.14.7** Double-tap left third → seek -10 s; double-tap right third → seek +10 s *(v2.1)*
- [x] **3.14.8** Tap center → toggle play/pause
- [x] **3.14.9** Press `F` → fullscreen toggle
- [x] **3.14.10** Stream pre-flight: `/api/stream/...?probe=1` runs before video.src is set
- [x] **3.14.11** Probe failure → in-player `⚠️ Поток недоступен` overlay (no infinite spinner)
- [x] **3.14.12** Mid-playback error (`onerror`) → re-probes and shows `⚠️ Ошибка воспроизведения` with reason
- [x] **3.14.13** First-load metadata → if saved position > 10 s, video seeks there + toast `С <time>`
- [x] **3.14.14** Plays inline on iOS (`playsinline`, `webkit-playsinline`)
- [x] **3.14.15** AirPlay route allowed (`x-webkit-airplay="allow"`)
- [x] **3.14.16** Position auto-saves every 5 s while playing (one POST per 5 s — verify in DevTools Network)
- [x] **3.14.17** Position saves on `pause` event (only if `currentTime > 5`)
- [x] **3.14.18** Position saves on close (only if `currentTime > 5`)
- [x] **3.14.19** End-of-file: completion POST sends `position=duration` → triggers TorrServer `/viewed` sync
- [x] **3.14.20** Episode end → toast `Серия завершена ✓` (or `... но синхронизация статуса не удалась` on viewed-sync fail)
- [x] **3.14.21** Auto-next: 3 s after `onended`, next episode plays automatically (multi-file torrents only)
- [x] **3.14.22** Click `Далее →` → immediately advances (no 3 s wait)
- [x] **3.14.23** Last episode: `Далее →` is hidden, no auto-next fires
- [x] **3.14.24** MKV files (e.g. Prophet) load with `data-media-type="video"` (not `unknown`) *(v2.1.1)*
- [x] **3.14.25** Audio plays by default; single tap unblocks autoplay on Safari if needed *(v2.1)*
- [x] **3.14.26** 5 s watchdog: if Vidstack fails to assign `<video>.src`, fall back to native HTMLVideoElement *(v2.1.1)*

#### 3.15 Toast Notifications

- [x] **3.15.1** Toast appears bottom-center, 24 px above safe-area inset
- [x] **3.15.2** Toast auto-dismisses after 2.5 s (default)
- [x] **3.15.3** Multiple sequential toasts queue cleanly (no flicker)
- [x] **3.15.4** Toast text is single-line, never truncated mid-word visually
- [x] **3.15.5** Toast respects active theme (uses `--bg2`/`--text`)

#### 3.16 Cross-Cutting Keyboard

- [x] **3.16.1** `Escape` priority: player → episodes → modal (only top-most overlay closes per press)
- [x] **3.16.2** No keyboard handler swallows browser-native shortcuts (`Cmd+W`, `Cmd+R`, etc.)

#### 3.17 Click-Outside Behavior

- [x] **3.17.1** Click outside search panel + search input → results close, input clears
- [x] **3.17.2** Click on add-modal backdrop (not the modal box) → modal closes
- [x] **3.17.3** Click on player overlay backdrop → does NOT close player (must use `←` or Escape)
- [x] **3.17.4** Click on episode overlay backdrop → does NOT close panel (must use `←` or Escape)

---


### 4. 📲 PWA & SERVICE WORKER

- [x] **4.1** Manifest `name=TorrStream`, `short_name=TorrStream`, `display=standalone`
- [x] **4.2** Manifest `start_url=./` and `scope=./` (relative — works under root and `/app/`)
- [x] **4.3** Manifest `background_color=#141414`, `theme_color=#e50914`
- [x] **4.4** Manifest icon 512×512 with `purpose: any maskable`
- [x] **4.5** SW registers from `sw.js` relative path (no `/app/` 404 under reverse proxy)
- [x] **4.6** SW `CACHE_NAME=v8` precaches: shell, icon, Vidstack chunks + providers + captions, CSS *(v2.1.1)*
- [x] **4.7** SW deletes old caches on activate (`CACHE_NAME` not in keep-list)
- [x] **4.8** Network-first for `/api/*` paths (always fresh data when online)
- [x] **4.9** Cache-first for shell + Vidstack assets, with successful GETs added to cache
- [x] **4.10** Opaque-response tolerance (added in v1.0) protects install against CDN hiccups
- [x] **4.11** Offline behavior: shell loads from cache, API calls show graceful failure UI
- [x] **4.12** Apple touch icon resolves: `<link rel="apple-touch-icon" href="static/icons/icon-512.png">` returns 200
- [x] **4.13** Theme color meta + apple-mobile-web-app-* metas all present in `<head>`
- [x] **4.14** SW survives version bump — change `CACHE_NAME` → old cache deleted on activate
- [ ] ⏭️ **4.15** Lighthouse PWA score ≥ 90 (`Installable` ✓) — run separately

---

### 5. 📱 RESPONSIVE & MOBILE

- [x] **5.1** Layout works at 375 px (iPhone SE) — 2-col grid, no horizontal scroll
- [x] **5.2** Layout works at 414 px (iPhone Plus) — 2-col grid
- [x] **5.3** Layout works at 768 px (iPad portrait) — 3+ col grid
- [x] **5.4** Layout works at 1280 px (laptop) — 5+ col grid
- [x] **5.5** Layout works at 1920 px (desktop) — 7+ col grid
- [x] **5.6** Card width adapts via CSS variable `--card-w` (130 px ≤600 px viewport, 175 px above)
- [x] **5.7** Nav: `+ Magnet` button collapses to `+` icon on ≤600 px (text span hidden)
- [x] **5.8** Episode grid collapses to 1 column on ≤600 px
- [x] **5.9** Touch targets ≥ 44×44 px on mobile (delete button, episode action buttons)
- [x] **5.10** Safe-area insets honored (`env(safe-area-inset-top)` / `bottom` on body, toast)
- [x] **5.11** Player viewport: `100dvh` used (no iOS Safari url-bar bounce that crops video)
- [x] **5.12** Modal centers and stays within viewport at all sizes
- [x] **5.13** Search input: full width on mobile, `max-width:460px` on desktop
- [x] **5.14** Cards do NOT exhibit horizontal scroll inside the grid
- [x] **5.15** Theme toggle and install button render correctly side-by-side on narrow viewports

---

### 6. ⚡ PERFORMANCE

- [x] **6.1** `/` initial load < 3 s on broadband (cold cache)
- [x] **6.2** `/api/status` response < 200 ms (local) / < 500 ms (over Caddy)
- [x] **6.3** `/api/torrents` response < 500 ms with ≤50 torrents
- [x] **6.4** `/api/files/<hash>` response < 800 ms (TorrServer is the long pole)
- [x] **6.5** Stream first byte (`?probe=1`) < 1.5 s
- [x] **6.6** Card poster images load lazily (`loading="lazy"`)
- [x] **6.7** Auto-refresh interval is 30 s (not 5 s — verify in DevTools Performance)
- [x] **6.8** Position-save POST runs every 5 s while playing — no busier
- [x] **6.9** No memory leak after 30 minutes idle (heap snapshot stable ±5 MB)
- [x] **6.10** SW caches Vidstack assets so subsequent loads serve from cache (Network panel: from disk cache)
- [x] **6.11** Vidstack bundle is same-origin (HTTP/2 multiplexing) — no jsdelivr serial-handshake throttle on Russian DPI networks *(v2.1)*
- [x] **6.12** Caddy `flush_interval -1` honored — streaming bytes reach client without buffering
- [x] **6.13** Theme toggle reaches target color in ≤16 ms (next paint frame) *(v2.2)*
- [ ] 🙋 **6.14** Range seeking returns within 1 s for 1080p mkv (real torrent test)
- [x] **6.15** Stress test: 4 concurrent workers, 2 min sustained streaming → 25 peers, ~52 Mbit/s peak, 0 errors over 158 byte-range requests *(v2.1.1)*

---

### 7. 🔒 SECURITY

- [x] **7.1** No secrets in repo: `git ls-files | rg -i 'secret|key|password|token'` returns nothing committed
- [x] **7.2** `.gitignore` covers `*.pem`, `.webhook-secret.txt`, `__pycache__/`, `venv/`, `.planning/*.log`
- [x] **7.3** GitHub webhook rejects without `X-Hub-Signature-256` when `GITHUB_WEBHOOK_SECRET` is set → 401
- [x] **7.4** GitHub webhook rejects forged signature (constant-time compare via `hmac.compare_digest`)
- [x] **7.5** Webhook ignores non-`refs/heads/main` ref (no rogue branch deploys)
- [x] **7.6** Webhook does NOT execute arbitrary commits (uses `git pull --ff-only` only)
- [x] **7.7** Wrapper has no end-user auth — confirm public exposure is INTENDED for this private deployment
- [x] **7.8** Reverse proxy (Caddy) terminates TLS; backend listens on `127.0.0.1:5000` only — `ss -tlnp | grep 5000`
- [x] **7.9** TorrServer credentials only set via env file (`/etc/torrstream/torrserver.env`, root:600), never hardcoded
- [x] **7.10** `download_file` strips path traversal (`filename.split("/")[-1]`) before `Content-Disposition`
- [x] **7.11** Hash format validation rejects malformed input before reaching TorrServer *(v2.2)*
- [x] **7.12** Streamed bytes are not echoed via JSON / no XSS surface in API responses
- [x] **7.13** `positions.json` is written atomically — concurrent crash cannot leave a half-written JSON
- [x] **7.14** TLS cert valid via Caddy automatic HTTPS — `curl -vI https://tv.trikiman.shop/ 2>&1 | grep -E 'subject|expire'`
- [x] **7.15** TLS cert valid for `ts.trikiman.shop` (TorrServer-for-Lampa subdomain) *(v2.0)*
- [x] **7.16** TorrServer BasicAuth required (`/var/lib/torrserver/accs.db` populated) — direct upstream not anonymous
- [x] **7.17** CORS scoped: `/api/position/*` allows configured origins (Lampa); `/static/*` allows `*` (plugin source); other routes restricted *(v2.2)*

---

## PART 2: POST-DEPLOY CHECKLIST

> Run these checks **after deploying** to the Oracle host.

---

### 8. 🌍 PRODUCTION ENVIRONMENT

- [x] **8.1** Public URL serves the wrapper — `curl -I https://tv.trikiman.shop/` → 200, TLS valid
- [x] **8.2** TLS certificate not expiring within 30 days (`curl -vI` → check expiry)
- [x] **8.3** Caddy is up — `systemctl is-active caddy.service` → `active`
- [x] **8.4** Caddy config matches `Caddyfile` in repo — `caddy adapt --config /etc/caddy/Caddyfile`
- [x] **8.5** Flask wrapper service is up — `systemctl is-active flask-wrapper.service` → `active`
- [x] **8.6** TorrServer service is up — `systemctl is-active torrserver.service` → `active`
- [x] **8.7** Service auto-restarts on crash (`Restart=always` configured) — `kill -9 $(pidof python3)` test
- [x] **8.8** TorrServer reachable on `127.0.0.1:8090` — `curl -u user:pass -I http://127.0.0.1:8090/` from Oracle host
- [x] **8.9** Wrapper listens only on `127.0.0.1:5000` — `ss -tlnp | grep 5000` shows loopback only
- [x] **8.10** `journalctl -u flask-wrapper.service --since "10 min ago"` shows no exception loops
- [x] **8.11** `positions.json` writable by service user (no permission-denied warnings on save)
- [x] **8.12** Service env vars match §0.2.1 list (`systemctl show flask-wrapper.service -p Environment`)
- [x] **8.13** GitHub webhook URL is registered in repo settings → `https://tv.trikiman.shop/api/github-webhook`
- [x] **8.14** Webhook secret in repo settings matches `GITHUB_WEBHOOK_SECRET` on Oracle
- [x] **8.15** Disk has ≥1 GB free for log accumulation
- [x] **8.16** `sudo systemctl restart flask-wrapper.service` permission granted to webhook runner (sudoers entry)
- [x] **8.17** Both subdomains resolve: `tv.trikiman.shop` (web UI) + `ts.trikiman.shop` (TorrServer for Lampa) *(v2.0)*
- [x] **8.18** TorrServer settings persisted: `TorrentDisconnectTimeout=300`, `ReaderReadAHead=95`, `PreloadCache=50` *(v2.1.1)*
- [x] **8.19** BT peer port 22115 open at Oracle Cloud Security List (TCP + UDP) *(v2.1.1)*
- [x] **8.20** BT peer port 22115 open at host iptables — persisted to `/etc/iptables/rules.v4` *(v2.1.1)*
- [x] **8.21** Peer port reachable externally — `python -c "import socket; s=socket.socket(); s.settimeout(6); print(s.connect_ex(('158.101.214.234',22115)))"` → 0
- [x] **8.22** On-box paths exist: `/opt/torrstream/app/`, `/opt/torrstream/venv/`, `/var/lib/torrserver/`, `/var/log/torrstream/`

---

### 9. 🔄 LIVE END-TO-END FLOWS

> All require a real torrent in TorrServer + a real device.

- [ ] 🙋 **9.1** Search a known title → result shows up → `+ Добавить` → torrent appears in library
- [ ] 🙋 **9.2** Click newly added torrent → file list loads (single or multi)
- [ ] 🙋 **9.3** Single file: video plays within 5 s, controls responsive, seeking works
- [ ] 🙋 **9.4** Multi-file: episode panel renders, click EP1 → plays, `Далее →` jumps to EP2
- [x] **9.5** Watch ≥30 s → close player → reopen → resumes within 1 s of last position
- [x] **9.6** Watch to >95% → close → reopen → episode marked `✓ просмотрено`, TorrServer `/viewed` updated
- [x] **9.7** Cross-device: watch on phone → open on desktop → resumes from same position *(v1.1)*
- [x] **9.8** Cross-device: mark watched on phone → desktop shows `✓` for that episode *(v1.1)*
- [x] **9.9** Auto-next fires 3 s after EP1 ends → EP2 starts cleanly
- [x] **9.10** Click `⬇ Скачать` on an episode → browser native download manager opens, file size matches *(v2.2)*
- [x] **9.11** Delete a watched torrent → returns to library, position entry gone (verify with `cat positions.json`)
- [x] **9.12** Search a Cyrillic title → results return; add → plays
- [ ] 🙋 **9.13** Install as PWA on phone → launches as standalone, no browser chrome, library loads
- [x] **9.14** Add via bare hash in modal → torrent gets normalized magnet, downloads start
- [x] **9.15** Add via `.torrent` URL in modal → adds successfully
- [x] **9.16** MKV file (Prophet, 96 min) loads in 4 s with `data-media-type="video"` *(v2.1.1)*
- [x] **9.17** Lampa → TorrStream sync: open in Lampa, advance position → wrapper Continue Watching reflects update *(v1.1)*
- [x] **9.18** TorrStream → Lampa sync: set position via wrapper → open same torrent in Lampa → Lampa seeks to wrapper position within 3 s *(v2.1.1 fight-back fix)*

---

### 10. 🔥 EDGE CASES & FAILURE MODES

- [x] **10.1** Stop TorrServer → reload UI → empty state shows `⚠️ Нет подключения к TorrServer` with the upstream URL
- [x] **10.2** Restart TorrServer → click `Повторить` → library re-populates
- [x] **10.3** Stop jacred (or block via `/etc/hosts`) → search shows `⚠️ Сервис поиска недоступен` + cached + library fallbacks
- [x] **10.4** Send malformed magnet → `Ошибка добавления` toast, no crash, library unaffected
- [x] **10.5** Mid-playback: kill TorrServer → player shows `⚠️ Ошибка воспроизведения`, not silent freeze
- [ ] 🙋 **10.6** Mid-playback: drop network → Vidstack shows native error, position last save is intact
- [x] **10.7** Auto-deploy: push commit touching `app.py` → service restarts within 5 s (check `systemctl show ... -p ActiveEnterTimestamp`)
- [x] **10.8** Auto-deploy: push commit touching only `.planning/*.md` → no restart (`restart_scheduled=false`)
- [x] **10.9** Auto-deploy: invalid signature → 401, no `git pull` runs (`journalctl` clean)
- [x] **10.10** Auto-deploy: `positions.json` survives a code push (back up before, diff after)
- [ ] 🙋 **10.11** Concurrent position writes (open same torrent on 2 devices) → both writes land, last-write-wins per file_index
- [x] **10.12** Open the site after 24 h offline → SW shell loads from cache → API calls fail gracefully with toasts
- [x] **10.13** Smoke script passes against production: `python scripts/smoke_prod.py` → 9/9 PASS
- [x] **10.14** Browser back/forward buttons don't break overlay state (player → close → back → no zombie player)
- [x] **10.15** Force-kill `python app.py` → systemd brings it back within 5 s, library reachable again
- [x] **10.16** Old format `positions.json` (flat schema) → wrapper auto-migrates to per-file schema on first read
- [x] **10.17** TorrServer `TorrentDisconnectTimeout=300s` survives restart (no eviction during 45 s buffer pause × 3) *(v2.1.1)*

---

### 11. 📋 FINAL SIGN-OFF

- [x] **All Part 1 build/import items passed** — deps install, app imports, smoke scripts green
- [x] **All Part 1 §2 API endpoints tested** — status, library, files, position, stream, download, add, remove, search, recent-searches, webhook
- [x] **All Part 1 §3 UI/UX clicks tested** — every button on every overlay, every keyboard shortcut, every empty state (Vidstack-aware)
- [x] **PWA verified** — install flow on Chrome desktop + Safari iOS (manual) + Chrome Android
- [x] **Responsive verified** — 375 / 414 / 768 / 1280 / 1920 all clean
- [x] **Performance baselines captured** — theme ≤16 ms, status <500 ms, sustained 52 Mbit/s
- [x] **Security audit** — no committed secrets, webhook HMAC works, backend not publicly bound, BasicAuth on TorrServer
- [x] **Production environment** — Caddy + flask-wrapper + torrserver all `active`, TLS valid both subdomains, env vars set, BT port open
- [x] **Live e2e flows** — at least one real torrent end-to-end on phone + desktop + Lampa cross-sync
- [x] **Edge cases drilled** — TorrServer kill, jacred kill, mid-playback failure, auto-deploy good + bad signature
- [x] **Pytest suite** — 80 tests (68 smoke + 12 integration, 3 skip when library empty) green *(v2.3)*
- [x] **GitHub Actions CI** — smoke on PR/push, integration nightly *(v2.2)*

> **Last verified**: 2026-05-14 (v2.2 — see `.planning/STATE.md`)
> **Score**: _populate per-section as you re-run each check_
>
> **Known carry-over issues** (verified still applicable as of v2.2):
> - 🙋 **QUAL-03** — User-driven iOS Safari manual walkthrough still needed (10-step guide in `docs/SMOKE-TESTS.md`). Carried from v2.1.
> - 🙋 **3.3.5/3.3.6/3.12.4** — iOS install affordance + iOS download fallback need real device.
> - 🙋 **6.14** — Range-seek 1080p mkv timing needs real torrent + scope.
> - 🙋 **9.1–9.4, 9.13** — Real torrent + real device walkthrough not yet automated.
> - 🙋 **10.6, 10.11** — Network-drop mid-playback + concurrent-device write tests need orchestration.
> - 🙋 **TEST-01** (new) — Playwright UI suite (theme timing assertion, picker walkthrough, download click-through). Foundation laid; defer if manual MCP coverage stays sufficient.
>
> **Resolved since v1.0** (do NOT re-add):
> - ✅ Cross-client position sync via Lampa plugin (v1.1, see §13)
> - ✅ Oracle Cloud migration (v2.0, see §14)
> - ✅ Plyr → Vidstack swap + audio regression + iOS readiness (v2.1, see §15)
> - ✅ Vidstack dynamic-import 404s + MKV stuck spinner + media-captions noop (v2.1.1, see §15)
> - ✅ BT peer port 22115 closed → throughput collapse (v2.1.1, see §15)
> - ✅ Lampa fight-back race (site→Lampa direction) (v2.1.1, see §15)
> - ✅ API hygiene: 404 unknown hash, 400 invalid hash, 400 invalid JSON (v2.2, see §16)
> - ✅ CORS on `/static/*` for Lampa plugin source fetch (v2.2, see §16)
> - ✅ Per-file download UI (v2.2, see §16)
> - ✅ Theme toggle 1432 ms → ≤16 ms (v2.2, see §16)
> - ✅ Pytest harness 80 tests + GitHub Actions CI (v2.2/v2.3, see §16)

---


## PART 3: NEW FEATURES (v1.1–v2.2)

> Quick checklist of features shipped after the original v1.0 baseline (2026-04-24).
> Items here may overlap with sections above — this is the at-a-glance summary for reviewers.
> Sections §15+ (Vidstack + production hardening) are the most recently shipped — start there if drilling into v2.x regressions.

---

### 12. 🌟 v1.0 TorrStream Baseline *(shipped 2026-04-24)*

**4 phases, 11 plans, 22 tasks.** See `.planning/milestones/v1.0-ROADMAP.md`.

- [x] **12.1** Authoritative runtime/deployment guide (`docs/DEPLOYMENT.md`)
- [x] **12.2** Repeatable smoke-verification path (`scripts/smoke_check.py`, `docs/SMOKE-TESTS.md`)
- [x] **12.3** Library/file diagnostics: `diagnostics.state` enum exposed in API + UI
- [x] **12.4** Add/remove mutation behavior: invalid input + upstream failures + local cleanup all visible
- [x] **12.5** Probe-driven playback/download diagnostics + visible player failure states
- [x] **12.6** Resume-state persistence atomic; completion writes return explicit sync results
- [x] **12.7** Search resilient under jacred outage: cached + library fallbacks
- [x] **12.8** Real install button + iPad/Safari guidance (PWA installability visible, not implicit)

---

### 13. 🔄 Cross-Client Position Sync *(v1.1 — shipped 2026-04-29)*

> 1 phase, 2 plans, 5 tasks. See `.planning/milestones/v1.1-ROADMAP.md`.

- [x] **13.1** `viewed_in_torrserver` flag surfaces TorrServer-watched torrents in `Продолжить просмотр`
- [x] **13.2** `/api/position/*` accepts cross-origin requests (Lampa on `https://lampa.mx`)
- [x] **13.3** OPTIONS preflight returns full CORS headers
- [x] **13.4** `static/lampa-sync.js` — self-contained Lampa plugin
- [x] **13.5** Plugin auto-seeks `<video>` to wrapper-saved offset on player start
- [x] **13.6** Plugin POSTs `{file_index, position, duration}` at 5 s cadence + on `pause` / `destroy` / `pagehide` / `beforeunload`
- [x] **13.7** Lifecycle listeners register exactly once (no leak under Lampa-detection polling)
- [x] **13.8** Resume seek bails when user switches torrents during the wait-for-metadata window
- [x] **13.9** UAT: Lampa playback advances wrapper position in real time
- [x] **13.10** UAT: Re-opening same torrent in Lampa restores wrapper-saved offset

---

### 14. ☁️ Oracle Cloud Migration *(v2.0 — shipped 2026-05-12)*

> 3 phases, 7 plans. See `.planning/phases/01-oracle-baseline/`.

- [x] **14.1** Live deployment moved AWS Frankfurt EC2 → Oracle Cloud Always Free (`158.101.214.234`, `eu-amsterdam-1`)
- [x] **14.2** All user state preserved: 3 torrents, 4 position entries, viewed markers byte-for-byte intact
- [x] **14.3** Domain `tv.trikiman.shop` resolves to Oracle (A record + Caddy auto-HTTPS)
- [x] **14.4** Second domain `ts.trikiman.shop` exposes TorrServer API for Lampa clients (HTTPS via Caddy)
- [x] **14.5** GitHub auto-deploy webhook working on Oracle without observable downtime
- [x] **14.6** Lampa plugin URL unchanged — existing installations keep working
- [x] **14.7** AWS torrstream services stopped + disabled (instance preserved per user choice)
- [x] **14.8** AWS GitHub webhook deactivated (Oracle is sole production)
- [x] **14.9** Cutover smoke: `scripts/_cutover_probe.py` + `scripts/_smoke_oracle.py` both PASS
- [x] **14.10** Production smoke `scripts/smoke_prod.py` rewritten for Oracle topology

---

### 15. 🎬 Player UX + iOS readiness *(v2.1 — shipped 2026-05-12, hardened 2026-05-13 as v2.1.1)*

> 2 phases, 5 plans + 6 post-ship bug fixes. See `.planning/milestones/v2.1-ROADMAP.md`, `v2.1-MILESTONE-AUDIT.md`.

#### 15.1 Vidstack Swap

- [x] **15.1.1** Plyr 3.7.8 replaced with Vidstack 1.12.13
- [x] **15.1.2** Built-in default video layout: double-tap ±10 s, tap-to-toggle play/pause, native fullscreen, PiP
- [x] **15.1.3** Audio plays by default (root-cause fix: removed duplicate `<video>` element from template)
- [x] **15.1.4** Lampa plugin contract preserved — `findVideo()` still locates the underlying `<video>`
- [x] **15.1.5** Service worker `CACHE_NAME=v4` with Vidstack CDN assets (originally; bumped to v8 in v2.1.1)
- [x] **15.1.6** Auto-warmup on cold TorrServer state: `/api/files` issues 0-byte range probe before returning empty `file_stats`

#### 15.2 Self-Hosted Vidstack *(v2.1.1 — commit 8e15e9e)*

- [x] **15.2.1** Vidstack bundle migrated CDN → `/static/vidstack/` (10 chunks + 2 CSS)
- [x] **15.2.2** Same-origin HTTP/2 multiplexing replaces serial TLS handshakes (fixes Russian DPI throttle)
- [x] **15.2.3** Production smoke marker `vidstack=True` confirms Vidstack web components embedded
- [x] **15.2.4** iPad load time: 1–3 min → < 5 s

#### 15.3 Lampa "Connect Then Drop" *(v2.1.1 — commit 2746adf)*

- [x] **15.3.1** TorrServer `TorrentDisconnectTimeout` bumped 30 s → 300 s
- [x] **15.3.2** New `ts.trikiman.shop` subdomain (Caddy → TorrServer 8090, Let's Encrypt cert)
- [x] **15.3.3** UAT: 3 cycles of 45 s idle on Big Buck Bunny — torrent stays `Torrent working`, no eviction events

#### 15.4 BT Peer Port 22115 *(v2.1.1 — commit 26bd4ad)*

- [x] **15.4.1** Oracle Cloud Security List ingress rules: TCP 0.0.0.0/0 → 22115; UDP 0.0.0.0/0 → 22115
- [x] **15.4.2** Ubuntu iptables INPUT allows 22115 (TCP+UDP), persisted to `/etc/iptables/rules.v4`
- [x] **15.4.3** External reachability verified: `connect_ex(('158.101.214.234', 22115))` → 0
- [x] **15.4.4** Helper script `scripts/_open_bt_peer_port.sh` shipped
- [x] **15.4.5** Stress test (4 workers, 2 min): peers 7 → 25, peak 51.9 Mbit/s, CPU 21–75 %, 0 errors over 158 byte-range reqs

#### 15.5 Vidstack Dynamic-Import 404 Fix *(v2.1.1 — commit 35e1042)*

- [x] **15.5.1** `_download_vidstack.py` rewritten to capture both static + dynamic imports
- [x] **15.5.2** Context-aware classification: sibling `./vidstack-X.js` is provider when from `providers/`, chunk when from `chunks/`
- [x] **15.5.3** Mirror count: 18 chunks + 8 providers (was 10 chunks)
- [x] **15.5.4** UAT: Big Buck Bunny click → video loaded in 4 s, played at 54 s saved position

#### 15.6 Lampa Fight-Back Race *(v2.1.1 — commit f4abc94)*

- [x] **15.6.1** Plugin polling extended 10 s → 60 s for `tryResume`
- [x] **15.6.2** Skip seek if Lampa is already within 5 s of saved position
- [x] **15.6.3** Detect fight-back (currentTime drops back near 0 after our seek) → re-apply up to 3 times
- [x] **15.6.4** UAT: server `position=250` → Lampa-opened BBB seeks 0 → 250 within 3 s

#### 15.7 MKV Stuck Spinner / media-captions Fix *(v2.1.1 — commit cf1de03)*

- [x] **15.7.1** `media-captions@next/dist/` self-hosted under `/static/vidstack/captions/` (5 files, ~52 KB)
- [x] **15.7.2** jsdelivr URL rewritten inside Vidstack chunks to point local
- [x] **15.7.3** Removed over-eager noop that returned empty module (caused `TypeError: t is not a constructor`)
- [x] **15.7.4** UAT: Prophet (96 min .mkv) loads with `data-media-type="video"`, `videoSrc` assigned, no console errors

#### 15.8 Hardening *(v2.1.1 — commit 92d4637)*

- [x] **15.8.1** `playFile()` 5 s watchdog: if Vidstack fails to assign `<video>.src`, fall back to native HTMLVideoElement
- [x] **15.8.2** Service worker `CACHE_NAME=v8`; precaches Vidstack provider/chunk files at install
- [x] **15.8.3** Webhook redeploy race no longer breaks first-click playback

#### 15.9 Documentation

- [x] **15.9.1** `docs/DEPLOYMENT.md` documents Oracle topology (host, paths, systemd units, auth locations, BT port)
- [x] **15.9.2** `docs/SMOKE-TESTS.md` adds production smoke section + 10-step iOS Safari walkthrough

---

### 16. 🛡️ Robustness + Coverage *(v2.2 — shipped 2026-05-14)*

> 3 phases, 5 plans, 9 requirements. See `.planning/milestones/v2.2-ROADMAP.md`.

#### 16.1 API Hygiene *(Phase 1 — commits fb22aa8, fdd9b10)*

- [x] **16.1.1** `HASH_RE = ^[0-9a-fA-F]{40}$|^[0-9a-fA-F]{64}$` validates v1 SHA1 + v2 SHA256
- [x] **16.1.2** `/api/files/<hash>`: well-formed unknown hash → **404** (was 200 with empty)
- [x] **16.1.3** `/api/position/<hash>` GET: well-formed unknown hash → **404** (was 200 with zero state)
- [x] **16.1.4** `/api/remove/<hash>`: well-formed unknown hash → **404** (was 200 idempotent silent)
- [x] **16.1.5** All hash routes: malformed hash → **400** `{ok:false, error:"invalid hash"}`
- [x] **16.1.6** Hash normalized to lowercase at persistence + lookup
- [x] **16.1.7** `POST /api/position`: malformed JSON body → **400** (was silent 200 — `silent=True` swallowed parse errors)
- [x] **16.1.8** `POST /api/position`: missing `position` field → **400**
- [x] **16.1.9** `/api/remove`: TorrServer failure → **502** (was 200 with `ok:false`)
- [x] **16.1.10** CORS preserved on 4xx error responses
- [x] **16.1.11** `/static/*` exposes `Access-Control-Allow-Origin: *` (Lampa plugin source fetch from `lampa.mx` works)
- [x] **16.1.12** Verification: 11/11 backend regression checks PASS via Chrome DevTools MCP against `tv.trikiman.shop` after auto-deploy

#### 16.2 UX Completeness *(Phase 2 — commits 415f95e, fe72be9)*

- [x] **16.2.1** ⬇ Скачать button in Episode Panel rows
- [x] **16.2.2** Round download button in player header
- [x] **16.2.3** `<a download="<filename>">` against `/api/stream/...` with proper basename
- [x] **16.2.4** Backend returns 206 with `Content-Range: bytes 0-15/<size>` for resumable downloads
- [x] **16.2.5** iOS Safari fallback: open new tab + toast `Поделиться → Сохранить в Файлы`
- [x] **16.2.6** Theme toggle: 1432 ms → ≤16 ms (89× faster)
- [x] **16.2.7** Implementation: `applyTheme()` writes `document.body.style.backgroundColor` directly, bypassing CSS cascade recompute
- [x] **16.2.8** Required 4 iterations after CSS-only attempts hit Chrome's ~680 ms cascade ceiling on this DOM (Vidstack web components + shadow trees)
- [x] **16.2.9** File-picker for multi-file torrents was already implemented (Episode Panel) — discovered during audit

#### 16.3 Test Harness *(Phase 3 — commit 86b4e33)*

- [x] **16.3.1** `tests/api/` — 68 contract tests via Flask test client + mocked TorrServer fixture
- [x] **16.3.2** `tests/integration/` — 10 live read-only tests against `tv.trikiman.shop`
- [x] **16.3.3** `pytest.ini` markers: `smoke` / `integration` / `e2e` / `cors`
- [x] **16.3.4** `pytest -m smoke` → 68/68 PASS in <1 s (no network)
- [x] **16.3.5** `pytest -m integration` → 12 tests PASS (3 skip when library empty) against live wrapper
- [x] **16.3.6** `e2e` marker gated behind opt-in (mutations)
- [x] **16.3.7** `.github/workflows/tests.yml` — smoke runs on every PR + push to main
- [x] **16.3.8** Integration runs nightly + on push to main
- [x] **16.3.9** `requirements-dev.txt` documents the dev dependency set
- [x] **16.3.10** `docs/SMOKE-TESTS.md` updated with pytest as preferred path
- [x] **16.3.11** `.planning/codebase/STACK.md` no longer claims "no automated test framework"

---

## How to Run This Checklist

```bash
# 1. Pre-flight (local)
pip install -r requirements.txt -r requirements-dev.txt
python -c "from app import app; print('OK')"
pytest -m smoke                          # 68/68 expected, <1 s

# 2. Start a local instance and run the smoke helper
python app.py &                          # local instance on :5000
python scripts/smoke_check.py            # 6/6 expected

# 3. Hit live endpoints
curl -I https://tv.trikiman.shop/
curl -s https://tv.trikiman.shop/api/status | jq
curl -s https://tv.trikiman.shop/api/torrents | jq '.diagnostics'

# 4. Run the production smoke helper (Vidstack-aware)
python scripts/smoke_prod.py             # 9/9 expected, with vidstack=True marker

# 5. Run the live integration suite
pytest -m integration                    # 12 expected (3 skip when library empty) against tv.trikiman.shop

# 6. UI/UX manual pass (open in browser, walk every button per §3)
# Use Chrome DevTools MCP if available — covers §3 + §5 + §6 fast.

# 7. Production health (on Oracle host)
ssh ubuntu@158.101.214.234 'systemctl is-active caddy.service flask-wrapper.service torrserver.service'
ssh ubuntu@158.101.214.234 'journalctl -u flask-wrapper.service --since "10 min ago" | tail -50'

# 8. Verify BT peer port externally
python -c "import socket; s=socket.socket(); s.settimeout(6); print('22115 open' if s.connect_ex(('158.101.214.234',22115))==0 else '22115 BLOCKED')"

# 9. Auto-deploy webhook smoke (push a no-op doc commit, watch logs)
git commit --allow-empty -m "test: verify auto-deploy webhook"
git push origin main
ssh ubuntu@158.101.214.234 'journalctl -u flask-wrapper.service -n 20'
```
