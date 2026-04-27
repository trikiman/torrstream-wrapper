# 🎬 TorrStream — Deployment Checklist

> **Site**: https://tv.trikiman.shop/
> **Stack**: Flask `app.py` + single-template `templates/index.html` + Plyr CDN + Service Worker (`static/sw.js`)
> **Upstreams**: TorrServer (`http://127.0.0.1:8090` default) · jacred.xyz (`https://jacred.xyz`)
> **Reverse proxy**: Caddy → `127.0.0.1:5000` (1 h read/write timeout for streaming)
> **Last verified**: _populate after first run_ (milestone v1.0 — see `.planning/STATE.md`)
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

- [ ] **QS-1** Public URL reachable: `curl -I https://tv.trikiman.shop/` → `HTTP/2 200`
- [ ] **QS-2** Status endpoint: `curl -s https://tv.trikiman.shop/api/status | jq '.torrserver.ok, .wrapper.position_entries'` → `true`, integer
- [ ] **QS-3** Library endpoint: `curl -s https://tv.trikiman.shop/api/torrents | jq '.ok, .diagnostics.state'` → `true`, `"ready"` or `"empty"`
- [ ] **QS-4** Systemd service: `ssh <ec2-host> 'systemctl is-active torrstream.service'` → `active`
- [ ] 🙋 **QS-5** Live playback: open the site on phone → click any torrent → first episode plays within 5 s with no spinner-of-death

If all 5 pass, deploy is healthy. Otherwise drill into Part 1/2 for the failing area.

**Note:** `python scripts/smoke_check.py` already covers QS-1, QS-2, QS-3 plus shell/manifest/SW fetches. QS-4 + QS-5 are the two checks the script does NOT cover.

---

## PART 0: AI TESTING TOOLKIT (Pre-Flight Check) ⭐ START HERE

> Run **§0** first. If any tool is missing → install it before starting the main checklist.
> Once §0 passes, AI can run §1–§7 autonomously from **0% → 100%**.
> §8 (production), §9 (live flows), §10 (edge cases) need human assistance (`🙋`) even with the full toolkit.

### 0.1 Required CLI Tools

- [ ] **0.1.1** `curl` — HTTP client. *Verify*: `curl --version`
- [ ] **0.1.2** `python` 3.10+. *Verify*: `python --version`
- [ ] **0.1.3** `pip` for Flask + requests install. *Verify*: `pip --version`
- [ ] **0.1.4** `jq` — JSON parser. *Verify*: `jq --version` *(Windows: `choco install jq`)*
- [ ] **0.1.5** `git`. *Verify*: `git --version`
- [ ] **0.1.6** `ssh` — only required for Part 2 production checks. *Verify*: `ssh -V`

### 0.2 Required Credentials & Files

- [ ] **0.2.1** Environment variables documented and set on EC2:
  - `TORRSERVER_URL` (default `http://127.0.0.1:8090`)
  - `TORRSERVER_USER` / `TORRSERVER_PASS` (only if upstream auth is enabled)
  - `JACRED_URL` (default `https://jacred.xyz`) / `JACRED_KEY` (optional)
  - `GITHUB_WEBHOOK_SECRET` (required for auto-deploy)
  - `TORRSTREAM_SERVICE` (default `torrstream.service`)
  - *Verify on EC2*: `systemctl show torrstream.service -p Environment`
- [ ] **0.2.2** SSH key for EC2 (skip Part 2 if missing)
- [ ] 🙋 **0.2.3** At least one real torrent present in TorrServer (for §3.7+, §9 file/playback checks)
- [ ] **0.2.4** Browser with PWA install support (Chrome/Edge desktop, Safari iOS, Chrome Android)

### 0.3 Browser for Manual UI Pass

- [ ] **0.3.1** Chrome/Edge 120+ installed. *Verify*: open `chrome://version/`
- [ ] **0.3.2** Production URL reachable in browser: https://tv.trikiman.shop/
- [ ] ⏭️ **0.3.3** Chrome DevTools MCP server connected (optional — speeds up §3 + §5 + §6)

### 0.4 One-Shot Verification Command

```powershell
# Verify CLI tools
curl --version; python --version; pip --version; jq --version; git --version; ssh -V

# Verify backend imports cleanly (run from repo root)
python -c "from app import app; print('backend OK')"

# Verify deps install cleanly
pip install -r requirements.txt

# Run the bundled smoke check (start instance first: python app.py)
python scripts/smoke_check.py
```

### 0.5 AI Autonomy Coverage

**✅ Fully autonomous**: §1 Build, §2 API, §3 UI (with DevTools MCP), §4 PWA, §5 Responsive, §6 Performance, §7 Security
**🙋 Needs human**: §8 Production SSH, §9 Live flows, §10 Edge cases (real TorrServer kill / real auto-deploy push)

---

## PART 1: PRE-DEPLOY CHECKLIST

> If every item in Part 1 passes → the wrapper is safe to deploy.

---

### 1. 🏗️ BUILD & INFRASTRUCTURE

- [ ] **1.1** `pip install -r requirements.txt` completes without errors (Flask ≥3.1,<4 ; requests ≥2.32,<3)
- [ ] **1.2** Backend imports cleanly — `python -c "from app import app; print('OK')"`
- [ ] **1.3** Local app starts on `0.0.0.0:5000` — `python app.py` then `curl -I http://127.0.0.1:5000/` → 200
- [ ] **1.4** `templates/index.html` exists and Flask serves it at `/` (no 404)
- [ ] **1.5** `static/manifest.json` exists and is valid JSON — `python -c "import json; json.load(open('static/manifest.json'))"`
- [ ] **1.6** `static/sw.js` exists and registers (no syntax error in console)
- [ ] **1.7** `static/icons/icon-512.png` exists (≥10 KB, used by manifest + apple-touch-icon)
- [ ] **1.8** `positions.json` is valid JSON or absent (absent on first install is OK)
- [ ] **1.9** Root-level `index.html` is **not** served by Flask (legacy duplicate per `docs/DEPLOYMENT.md`)
- [ ] **1.10** `scripts/smoke_check.py` runs to completion against a local instance — `Summary: 6/6 checks passed`
- [ ] **1.11** Reverse-proxy config valid:
  - **Caddy**: `caddy validate --config Caddyfile`
  - **nginx (alt)**: `nginx -t -c $(pwd)/nginx-torrstream.conf`
- [ ] **1.12** `requirements.txt` only lists in-scope deps (Flask, requests) — no accidental extras committed

---

### 2. 🌐 BACKEND API ENDPOINTS

> Test each endpoint using `curl` against `https://tv.trikiman.shop` (or `http://127.0.0.1:5000` locally). Use `jq` to inspect JSON shape.

#### 2.1 Shell & PWA Assets

- [ ] **2.1.1** `GET /` serves frontend — 200, `Content-Type: text/html`
- [ ] **2.1.2** `GET /manifest.json` returns valid manifest (`name=TorrStream`, `start_url=./`, `scope=./`)
- [ ] **2.1.3** `GET /sw.js` returns service worker with `Content-Type: application/javascript`
- [ ] **2.1.4** `GET /favicon.ico` returns the 512×512 PNG with `Content-Type: image/png`
- [ ] **2.1.5** Manifest icons resolve: `curl -I https://tv.trikiman.shop/static/icons/icon-512.png` → 200

#### 2.2 Status & Diagnostics

- [ ] **2.2.1** `GET /api/status` returns valid JSON
- [ ] **2.2.2** Response shape: `torrserver.{url, ok, torrent_count, error}`, `search.{url, api_key_configured}`, `wrapper.{root, manifest, service_worker, auth_configured, position_entries}`
- [ ] **2.2.3** `torrserver.ok=true` when upstream is reachable
- [ ] **2.2.4** `torrserver.ok=false` + non-empty `.error` when upstream is killed (kill TorrServer, retry, restart)
- [ ] **2.2.5** `wrapper.auth_configured` reflects whether `TORRSERVER_USER`/`PASS` are set
- [ ] **2.2.6** `wrapper.position_entries` matches `positions.json` keys count

#### 2.3 Library Listing

- [ ] **2.3.1** `GET /api/torrents` returns `{ok, items, diagnostics}` JSON
- [ ] **2.3.2** `diagnostics.state ∈ {ready, empty, upstream_unavailable}` — exhaustive enum
- [ ] **2.3.3** Each item carries: `hash`, `title`, `poster`, `torrent_size`, `position`, `duration`, `last_file_index`, `updated`, `stat`
- [ ] **2.3.4** `position`/`duration`/`last_file_index` reflect the **last-played file** for the "Continue Watching" rail
- [ ] **2.3.5** Empty library returns `ok=true`, `items=[]`, `diagnostics.state="empty"` (NOT a fake error)
- [ ] **2.3.6** TorrServer offline returns `ok=false`, `items=[]`, `diagnostics.state="upstream_unavailable"`, explicit `.error` string

#### 2.4 File Listing

- [ ] **2.4.1** `GET /api/files/<hash>` returns `{ok, file_stats, last_file_index, viewed_indices, diagnostics}`
- [ ] **2.4.2** `diagnostics.state ∈ {ready, no_playable_files, file_lookup_failed, upstream_unavailable}` — exhaustive enum
- [ ] **2.4.3** `file_stats` contains only video files (extensions: `.mp4 .mkv .avi .m4v .mov .wmv .ts .webm` or no extension)
- [ ] **2.4.4** Each entry includes `id`, `path`, `length`, `position`, `file_duration`, `viewed`
- [ ] **2.4.5** `viewed=true` when file is in TorrServer `/viewed` list OR `position/duration > 0.95`
- [ ] **2.4.6** `viewed_indices` mirrors TorrServer's `/viewed` list for that hash
- [ ] **2.4.7** Bogus hash → `ok=false`, `diagnostics.state="upstream_unavailable"` (not a 500)

#### 2.5 Position Read/Write

- [ ] **2.5.1** `GET /api/position/<hash>` returns `{ok, position, duration, last_file_index}` (defaults 0/0/1 for unknown)
- [ ] **2.5.2** `GET /api/position/<hash>?file_index=2` returns the per-file entry, not the last-played file
- [ ] **2.5.3** `POST /api/position/<hash>` with `{position, duration, file_index}` returns `{ok, viewed_sync_attempted, viewed_synced}`
- [ ] **2.5.4** Negative `position` is clamped to 0
- [ ] **2.5.5** `file_index < 1` → 400 `{ok:false, error:"invalid file_index"}`
- [ ] **2.5.6** Non-integer payload → 400 `{ok:false, error:"invalid position payload"}`
- [ ] **2.5.7** Subsequent `GET` returns the value just written
- [ ] **2.5.8** When `position/duration > 0.95`, `viewed_sync_attempted=true` and TorrServer `/viewed` is hit
- [ ] **2.5.9** `positions.json` writes are atomic (`.tmp` then rename — no half-written file on crash)
- [ ] **2.5.10** Multi-file torrent: writing index=2 doesn't clobber index=1's saved position
- [ ] **2.5.11** `last_file_index` updates to the most recently written file

#### 2.6 Stream Proxy

- [ ] **2.6.1** `GET /api/stream/<filename>?hash=<h>&index=<i>` returns video with `Accept-Ranges: bytes` and `Content-Type: video/*`
- [ ] **2.6.2** Range request (`Range: bytes=0-99`) returns 206 with matching `Content-Range`
- [ ] **2.6.3** Probe mode `?probe=1` returns JSON `{ok, upstream_status, content_type, error}` (no media body)
- [ ] **2.6.4** Probe ok=true when TorrServer would serve the file
- [ ] **2.6.5** Probe ok=false with explicit error when TorrServer rejects
- [ ] **2.6.6** Missing `hash` query param → 400 `{ok:false, error:"missing hash"}`
- [ ] **2.6.7** TorrServer 4xx/5xx → 502 `{ok:false, upstream_status, error}` (no silent hang)
- [ ] **2.6.8** TorrServer connection error → 502 with explicit `.error`
- [ ] **2.6.9** Chunked transfer keeps wrapping headers (`Content-Type`, `Accept-Ranges`, `Content-Range`, `Content-Length`)

#### 2.7 Download Proxy

- [ ] **2.7.1** `GET /api/download/<filename>?hash=<h>&index=<i>` returns the file with `Content-Disposition: attachment; filename="..."`
- [ ] **2.7.2** Probe mode `?probe=1` mirrors §2.6.3 contract
- [ ] **2.7.3** `Content-Type` is `application/octet-stream` (or upstream's value if explicit)
- [ ] **2.7.4** Range support intact (resumable downloads)
- [ ] **2.7.5** Filename in `Content-Disposition` is the basename (no path leak)

#### 2.8 Add Torrent

- [ ] **2.8.1** `POST /api/add` with `{link: "magnet:?xt=urn:btih:..."}` returns `{ok:true, hash, normalized_link}`
- [ ] **2.8.2** Bare 40-char SHA1 → normalized to `magnet:?xt=urn:btih:<HASH>`
- [ ] **2.8.3** Bare 32-char base32 hash → normalized to magnet
- [ ] **2.8.4** `http://`/`https://` `.torrent` URL → passed through as-is
- [ ] **2.8.5** Empty link → `{ok:false, error:"no link"}`
- [ ] **2.8.6** Garbage input (`bad-input`) → `{ok:false, error:"invalid link"}`
- [ ] **2.8.7** Optional `title` and `poster` round-trip into TorrServer
- [ ] **2.8.8** TorrServer add failure → `{ok:false, error:"torrserver add failed", normalized_link}` (link still echoed for retry)

#### 2.9 Remove Torrent

- [ ] **2.9.1** `DELETE /api/remove/<hash>` returns `{ok:true, removed_positions}`
- [ ] **2.9.2** `removed_positions=true` only when there was an entry in `positions.json` for that hash
- [ ] **2.9.3** Position entry is gone from `positions.json` after successful delete
- [ ] **2.9.4** TorrServer removal failure still cleans local positions and returns `{ok:false, error, removed_positions}`
- [ ] **2.9.5** Removing an unknown hash returns either upstream success (idempotent) or explicit `{ok:false}` — no 500

#### 2.10 Search Proxy

- [ ] **2.10.1** `GET /api/search?q=<query>` returns `{ok, Results}` JSON
- [ ] **2.10.2** Empty `q` → `{ok:true, Results:[]}` (no upstream call)
- [ ] **2.10.3** Each result has `Title`, `Size`, `Seeders`, `Tracker`, `MagnetUri`
- [ ] **2.10.4** Cyrillic query (`?q=матрица`) round-trips correctly (URL-encoded)
- [ ] **2.10.5** jacred outage → `{ok:false, Results:[], error:<reason>}` (UI then shows fallback)
- [ ] **2.10.6** `JACRED_KEY` env var is appended as `apikey=` when configured

#### 2.11 GitHub Webhook (Auto-Deploy)

- [ ] **2.11.1** `POST /api/github-webhook` with no signature when `GITHUB_WEBHOOK_SECRET` is unset → succeeds (best effort)
- [ ] **2.11.2** With secret set, missing/invalid `X-Hub-Signature-256` → 401 `{ok:false, error:"invalid signature"}`
- [ ] **2.11.3** Valid HMAC + non-`refs/heads/main` ref → `{ok:true, status:"ignored", ref}`
- [ ] **2.11.4** Valid HMAC + `refs/heads/main` push → `{ok:true, status:"updated", restart_scheduled, files_changed, pull_output}`
- [ ] **2.11.5** Restart scheduled only when commits touched `*.py` / `*.html` / `*.js` / `*.css` / `requirements.txt`
- [ ] **2.11.6** `positions.json` is preserved across the pull (backup → pull → restore if changed)
- [ ] **2.11.7** Malformed JSON body → 400 `{ok:false, error:"invalid json"}`
- [ ] **2.11.8** Service restart command targets the unit named in `TORRSTREAM_SERVICE` env var

---

### 3. 🖥️ FRONTEND — UI / UX (Every Button, Every Click)

> Open `https://tv.trikiman.shop/` in a desktop and a mobile browser. Verify each interaction below. **This is the section to drill the hardest into — the user explicitly asked for full button & click coverage.**

#### 3.1 Initial Load

- [ ] **3.1.1** Page loads without blank screen — torrents render within 2 s on broadband
- [ ] **3.1.2** No red console errors on load (warnings OK; SW registration message is fine)
- [ ] **3.1.3** Logo `🎬 TorrStream` visible in nav
- [ ] **3.1.4** Search input has placeholder `Поиск фильмов и сериалов...`
- [ ] **3.1.5** Theme button (`☀️` or `🌙`) visible top-right
- [ ] **3.1.6** Add button (`+ Magnet`) visible top-right
- [ ] **3.1.7** Spinner shows in section title `📁 Все торренты` and disappears after fetch
- [ ] **3.1.8** Library renders in a responsive grid (≥2 cols mobile, more on desktop)
- [ ] **3.1.9** Auto-refresh fires every 30 s — confirm via DevTools Network tab (one `/api/torrents` per 30 s)
- [ ] **3.1.10** Service worker registers — `navigator.serviceWorker.controller` not null after second load

#### 3.2 Theme Toggle (☀️ / 🌙)

- [ ] **3.2.1** Click theme button — colors invert dark ↔ light
- [ ] **3.2.2** Icon toggles correctly (`☀️` in dark mode, `🌙` in light mode)
- [ ] **3.2.3** Theme persists across full reload (`localStorage.theme`)
- [ ] **3.2.4** Theme persists across new tab in same origin
- [ ] **3.2.5** No flash of wrong theme on initial load (FOUC check)
- [ ] **3.2.6** All overlays (player, episode, modal) honor the active theme

#### 3.3 Install Affordance (PWA)

- [ ] **3.3.1** Chrome/Edge desktop: `beforeinstallprompt` fires → `Установить` button appears in nav
- [ ] **3.3.2** Click `Установить` → native install dialog opens
- [ ] **3.3.3** Install succeeds → `appinstalled` event → toast `Приложение установлено`
- [ ] **3.3.4** After install → `Установить` button hides (matchMedia standalone)
- [ ] **3.3.5** iPad/iPhone Safari: `Установить` still appears (no `beforeinstallprompt` available)
- [ ] **3.3.6** iPad/iPhone click → toast `Safari: Поделиться → На экран «Домой»`
- [ ] **3.3.7** Browsers without PWA support: button hidden (no dead click)
- [ ] **3.3.8** Standalone mode (already installed): button hidden

#### 3.4 Add Magnet Modal

- [ ] **3.4.1** Click `+ Magnet` → modal opens, backdrop blurs content
- [ ] **3.4.2** Magnet input is auto-focused
- [ ] **3.4.3** Input placeholder: `magnet:?xt=urn:btih:... или хеш`
- [ ] **3.4.4** Title input placeholder: `Название (необязательно)`
- [ ] **3.4.5** Click `Отмена` → modal closes, both inputs cleared
- [ ] **3.4.6** Click outside the modal box → modal closes (backdrop click)
- [ ] **3.4.7** Press `Escape` → modal closes
- [ ] **3.4.8** Empty submit → toast `Введите magnet-ссылку или хеш`
- [ ] **3.4.9** Valid magnet submit → toast `Торрент добавлен!`, modal closes, library refreshes
- [ ] **3.4.10** Bare hash submit → still works (normalized server-side)
- [ ] **3.4.11** TorrServer down → toast surfaces backend error message (not silent)
- [ ] **3.4.12** Network error → toast `Ошибка соединения`

#### 3.5 Search

- [ ] **3.5.1** Type 1 character → no fetch (debounce + min-2 char gate)
- [ ] **3.5.2** Type 2+ chars → after 500 ms debounce, fetch fires once
- [ ] **3.5.3** Results panel `Результаты поиска` opens, count chip updates
- [ ] **3.5.4** Spinner shows while waiting, then results render
- [ ] **3.5.5** Each result row shows title, tracker, size, seeders, `+ Добавить` button
- [ ] **3.5.6** Cyrillic query works (e.g. `матрица`)
- [ ] **3.5.7** Latin query works (e.g. `Project Hail Mary`)
- [ ] **3.5.8** Results capped at 30 in DOM
- [ ] **3.5.9** Successful results are cached to `localStorage` under `search-cache:<query>`
- [ ] **3.5.10** No results → empty state `🔍 Ничего не найдено`
- [ ] **3.5.11** jacred down → empty state `⚠️ Сервис поиска недоступен` + `Повторить` button
- [ ] **3.5.12** jacred down + cached results exist → `Сохраненные результаты` block renders below the warning
- [ ] **3.5.13** jacred down + library matches exist → `Совпадения в библиотеке` block renders with `Открыть` buttons
- [ ] **3.5.14** Click outside the search panel → results close, input clears
- [ ] **3.5.15** Press `Escape` while modal/player closed: focus stays sane (does not close search)

#### 3.6 Add From Search Result

- [ ] **3.6.1** Click `+ Добавить` on a row → button text changes to `...`, disabled
- [ ] **3.6.2** Success → button becomes `✓ Добавлен` with green background, toast `Торрент добавлен!`, library reloads
- [ ] **3.6.3** Failure → button reverts to `Ошибка`, re-enabled, toast surfaces backend error
- [ ] **3.6.4** Library-fallback row `Открыть` → opens that torrent's episode/player flow directly

#### 3.7 Library Card

- [ ] **3.7.1** Each card shows poster (or `🎬` placeholder if `poster` empty/broken)
- [ ] **3.7.2** Title is shown (max 2 lines, truncated with ellipsis)
- [ ] **3.7.3** Meta row shows size + watched percentage (when in progress)
- [ ] **3.7.4** Progress bar at 0–100% renders for items with `position > 30 && < 95% of duration`
- [ ] **3.7.5** Currently-streaming torrents (`stat=3`) show `▶` badge top-right
- [ ] **3.7.6** Multi-file torrents with `last_file_index > 1` show `EP N` badge top-left
- [ ] **3.7.7** Hover → card lifts (translateY -6px) and casts shadow (desktop)
- [ ] **3.7.8** Active/tap → card scales down (mobile feedback)
- [ ] **3.7.9** Click anywhere on card (except `Удалить`) → opens torrent (episode panel or player)
- [ ] **3.7.10** Lampa-prefixed titles (`[LAMPA] ...`) are stripped to clean display

#### 3.8 Continue Watching Rail

- [ ] **3.8.1** Section `▶️ Продолжить просмотр` only shows when ≥1 torrent has progress 30 s < pos < 95%
- [ ] **3.8.2** Cards in this rail show progress bar (not in main grid)
- [ ] **3.8.3** Clicking a continue-card opens directly to last-played file
- [ ] **3.8.4** Section disappears when all in-progress torrents are completed
- [ ] **3.8.5** Section ordering: most recently updated first

#### 3.9 Card Delete (`Удалить`)

- [ ] **3.9.1** `Удалить` button visible on each card (bottom-right of card-info)
- [ ] **3.9.2** Click does NOT bubble up to open-torrent (event.stopPropagation works)
- [ ] **3.9.3** `window.confirm("Удалить торрент \"<title>\"?")` appears
- [ ] **3.9.4** Cancel → no API call, card remains
- [ ] **3.9.5** Confirm → `DELETE /api/remove/<hash>` fires
- [ ] **3.9.6** Success with prior position → toast `Торрент и позиция удалены`
- [ ] **3.9.7** Success with no prior position → toast `Торрент удален`
- [ ] **3.9.8** Library reloads; card disappears
- [ ] **3.9.9** Failure → toast surfaces backend error, card remains

#### 3.10 Empty States

- [ ] **3.10.1** TorrServer reachable + no torrents → icon `🎞️`, title `Библиотека пока пуста`, hint about magnet/Lampa
- [ ] **3.10.2** TorrServer unreachable → icon `⚠️`, title `Нет подключения к TorrServer`, message includes upstream URL + error, `Повторить` button
- [ ] **3.10.3** Initial render before first fetch (no diagnostics) → fallback empty `Нет добавленных торрентов`
- [ ] **3.10.4** `Повторить` button retriggers `loadTorrents()` and updates state correctly

#### 3.11 Episode Panel (multi-file torrents)

- [ ] **3.11.1** Click multi-file card → episode overlay slides in (full-screen)
- [ ] **3.11.2** Header shows torrent title, `←` back button, `▶ Продолжить (EP N)` continue button
- [ ] **3.11.3** Continue button shows `▶ Начать (EP N)` if no last-watched and there's an unwatched episode
- [ ] **3.11.4** Continue button hides entirely when everything is watched
- [ ] **3.11.5** Click `←` → panel closes, body scroll restored
- [ ] **3.11.6** Press `Escape` → panel closes
- [ ] **3.11.7** Each episode row shows: episode number, filename, size, percent, watched badge, `⬇` download button, `▶` play button
- [ ] **3.11.8** Watched episodes show `✓` instead of number, `.watched` class dims them
- [ ] **3.11.9** Currently-playing episode shows `.playing` border-highlight
- [ ] **3.11.10** Click episode row anywhere (except action buttons) → plays that episode
- [ ] **3.11.11** Body has `overflow:hidden` while panel is open
- [ ] **3.11.12** Episode list is single-column on mobile (≤600 px)
- [ ] **3.11.13** Episode panel handles file lookup failure with `⚠️` empty state + explicit message
- [ ] **3.11.14** Episode panel handles "no playable files" with `📼` empty state + explicit message

#### 3.12 Episode Action Buttons

- [ ] **3.12.1** `⬇` (download) does NOT trigger play (event.stopPropagation works)
- [ ] **3.12.2** `⬇` first probes `/api/download/...?probe=1` — only opens new tab on `ok=true`
- [ ] **3.12.3** Probe ok → toast `Загрузка начата...`, browser native download manager opens
- [ ] **3.12.4** Probe fail → toast surfaces backend error
- [ ] **3.12.5** `▶` (play) does NOT trigger row click duplicate
- [ ] **3.12.6** `▶` plays the same episode as a row click

#### 3.13 Single-File Direct Play

- [ ] **3.13.1** Click single-file card → skips episode panel, opens player directly
- [ ] **3.13.2** Player title shows torrent title (no `EP n / N` for single file)
- [ ] **3.13.3** `Далее →` button hidden for single-file
- [ ] **3.13.4** Position auto-restores from previous session
- [ ] **3.13.5** Closing player auto-saves position if `currentTime > 5 s`

#### 3.14 Video Player (Plyr)

- [ ] **3.14.1** Player overlay covers full viewport (z-index 1000)
- [ ] **3.14.2** Header shows: `←` back, title, `EP n / N`, `Далее →` (multi-episode only)
- [ ] **3.14.3** Plyr controls: play/pause, progress bar, current/duration, mute, volume, fullscreen
- [ ] **3.14.4** Click `←` → player closes, position auto-saves, library reloads
- [ ] **3.14.5** Press `Escape` → player closes (same path)
- [ ] **3.14.6** Press `Space` → toggles play/pause (Plyr keyboard global)
- [ ] **3.14.7** Press `←/→` → seeks 10 s
- [ ] **3.14.8** Press `M` → mute toggle
- [ ] **3.14.9** Press `F` → fullscreen toggle
- [ ] **3.14.10** Stream pre-flight: `/api/stream/...?probe=1` runs before video.src is set
- [ ] **3.14.11** Probe failure → in-player `⚠️ Поток недоступен` overlay (no infinite spinner)
- [ ] **3.14.12** Mid-playback error (`onerror`) → re-probes and shows `⚠️ Ошибка воспроизведения` with reason
- [ ] **3.14.13** First-load metadata → if saved position > 10 s, video seeks there + toast `С <time>`
- [ ] **3.14.14** Plays inline on iOS (`playsinline`, `webkit-playsinline`)
- [ ] **3.14.15** AirPlay route allowed (`x-webkit-airplay="allow"`)
- [ ] **3.14.16** Position auto-saves every 5 s while playing (one POST per 5 s — verify in DevTools Network)
- [ ] **3.14.17** Position saves on `pause` event (only if `currentTime > 5`)
- [ ] **3.14.18** Position saves on close (only if `currentTime > 5`)
- [ ] **3.14.19** End-of-file: completion POST sends `position=duration` → triggers TorrServer `/viewed` sync
- [ ] **3.14.20** Episode end → toast `Серия завершена ✓` (or `... но синхронизация статуса не удалась` on viewed-sync fail)
- [ ] **3.14.21** Auto-next: 3 s after `onended`, next episode plays automatically (multi-file torrents only)
- [ ] **3.14.22** Click `Далее →` → immediately advances (no 3 s wait)
- [ ] **3.14.23** Last episode: `Далее →` is hidden, no auto-next fires

#### 3.15 Toast Notifications

- [ ] **3.15.1** Toast appears bottom-center, 24 px above safe-area inset
- [ ] **3.15.2** Toast auto-dismisses after 2.5 s (default)
- [ ] **3.15.3** Multiple sequential toasts queue cleanly (no flicker)
- [ ] **3.15.4** Toast text is single-line, never truncated mid-word visually
- [ ] **3.15.5** Toast respects active theme (uses `--bg2`/`--text`)

#### 3.16 Cross-Cutting Keyboard

- [ ] **3.16.1** `Escape` priority: player → episodes → modal (only top-most overlay closes per press)
- [ ] **3.16.2** No keyboard handler swallows browser-native shortcuts (`Cmd+W`, `Cmd+R`, etc.)

#### 3.17 Click-Outside Behavior

- [ ] **3.17.1** Click outside search panel + search input → results close, input clears
- [ ] **3.17.2** Click on add-modal backdrop (not the modal box) → modal closes
- [ ] **3.17.3** Click on player overlay backdrop → does NOT close player (must use `←` or Escape)
- [ ] **3.17.4** Click on episode overlay backdrop → does NOT close panel (must use `←` or Escape)

---

### 4. 📲 PWA & SERVICE WORKER

- [ ] **4.1** Manifest `name=TorrStream`, `short_name=TorrStream`, `display=standalone`
- [ ] **4.2** Manifest `start_url=./` and `scope=./` (relative — works under root and `/app/`)
- [ ] **4.3** Manifest `background_color=#141414`, `theme_color=#e50914`
- [ ] **4.4** Manifest icon 512×512 with `purpose: any maskable`
- [ ] **4.5** SW registers from `sw.js` relative path (no `/app/` 404 under reverse proxy)
- [ ] **4.6** SW caches shell on install: root, `static/icons/icon-512.png`, Plyr CSS, Plyr JS
- [ ] **4.7** SW deletes old caches on activate (`CACHE_NAME` not in keep-list)
- [ ] **4.8** Network-first for `/api/*` paths (always fresh data when online)
- [ ] **4.9** Cache-first for shell assets, with successful GETs added to cache
- [ ] **4.10** Offline behavior: shell loads from cache, API calls show graceful failure UI
- [ ] **4.11** Lighthouse PWA score ≥ 90 (`Installable` ✓)
- [ ] **4.12** Apple touch icon resolves: `<link rel="apple-touch-icon" href="static/icons/icon-512.png">` returns 200
- [ ] **4.13** Theme color meta + apple-mobile-web-app-* metas all present in `<head>`
- [ ] **4.14** SW survives version bump — change `CACHE_NAME` → old cache deleted on activate

---

### 5. 📱 RESPONSIVE & MOBILE

- [ ] **5.1** Layout works at 375 px (iPhone SE) — 2-col grid, no horizontal scroll
- [ ] **5.2** Layout works at 414 px (iPhone Plus) — 2-col grid
- [ ] **5.3** Layout works at 768 px (iPad portrait) — 3+ col grid
- [ ] **5.4** Layout works at 1280 px (laptop) — 5+ col grid
- [ ] **5.5** Layout works at 1920 px (desktop) — 7+ col grid
- [ ] **5.6** Card width adapts via CSS variable `--card-w` (130 px ≤600 px viewport, 175 px above)
- [ ] **5.7** Nav: `+ Magnet` button collapses to `+` icon on ≤600 px (text span hidden)
- [ ] **5.8** Episode grid collapses to 1 column on ≤600 px
- [ ] **5.9** Touch targets ≥ 44×44 px on mobile (delete button, episode action buttons)
- [ ] **5.10** Safe-area insets honored (`env(safe-area-inset-top)` / `bottom` on body, toast)
- [ ] **5.11** Player viewport: `100dvh` used (no iOS Safari url-bar bounce that crops video)
- [ ] **5.12** Modal centers and stays within viewport at all sizes
- [ ] **5.13** Search input: full width on mobile, `max-width:460px` on desktop
- [ ] **5.14** Cards do NOT exhibit horizontal scroll inside the grid
- [ ] **5.15** Theme toggle and install button render correctly side-by-side on narrow viewports

---

### 6. ⚡ PERFORMANCE

- [ ] **6.1** `/` initial load < 3 s on broadband (cold cache)
- [ ] **6.2** `/api/status` response < 200 ms (local) / < 500 ms (over Caddy)
- [ ] **6.3** `/api/torrents` response < 500 ms with ≤50 torrents
- [ ] **6.4** `/api/files/<hash>` response < 800 ms (TorrServer is the long pole)
- [ ] **6.5** Stream first byte (`?probe=1`) < 1.5 s
- [ ] **6.6** Card poster images load lazily (`loading="lazy"`)
- [ ] **6.7** Auto-refresh interval is 30 s (not 5 s — verify in DevTools Performance)
- [ ] **6.8** Position-save POST runs every 5 s while playing — no busier
- [ ] **6.9** No memory leak after 30 minutes idle (heap snapshot stable ±5 MB)
- [ ] **6.10** SW caches Plyr assets so subsequent loads serve from cache (Network panel: from disk cache)
- [ ] **6.11** No render-blocking JS (Plyr loaded via `<script>` after CSS)
- [ ] **6.12** Caddy `flush_interval -1` honored — streaming bytes reach client without buffering
- [ ] **6.13** Range seeking returns within 1 s for 1080p mkv (real torrent test)

---

### 7. 🔒 SECURITY

- [ ] **7.1** No secrets in repo: `git ls-files | rg -i 'secret|key|password|token'` returns nothing committed
- [ ] **7.2** `.gitignore` covers `*.pem`, `.webhook-secret.txt`, `__pycache__/`, `venv/`, `.planning/*.log`
- [ ] **7.3** GitHub webhook rejects without `X-Hub-Signature-256` when `GITHUB_WEBHOOK_SECRET` is set → 401
- [ ] **7.4** GitHub webhook rejects forged signature (constant-time compare via `hmac.compare_digest`)
- [ ] **7.5** Webhook ignores non-`refs/heads/main` ref (no rogue branch deploys)
- [ ] **7.6** Webhook does NOT execute arbitrary commits (uses `git pull --ff-only` only)
- [ ] **7.7** Wrapper has no end-user auth — confirm public exposure is INTENDED for this private deployment
- [ ] **7.8** Reverse proxy (Caddy) terminates TLS; backend listens on `127.0.0.1:5000` only (verify `ss -tlnp | grep 5000`)
- [ ] **7.9** TorrServer credentials, if used, only set via env (not hardcoded in `app.py` defaults)
- [ ] **7.10** `download_file` strips path traversal (`filename.split("/")[-1]`) before `Content-Disposition`
- [ ] **7.11** No directory traversal possible via `/api/stream/<path:filename>` because TorrServer enforces hash+index match upstream
- [ ] **7.12** Streamed bytes are not echoed via JSON / no XSS surface in API responses
- [ ] **7.13** `positions.json` is written atomically — concurrent crash cannot leave a half-written JSON
- [ ] **7.14** TLS cert valid via Caddy automatic HTTPS — `curl -vI https://tv.trikiman.shop/ 2>&1 | grep -E 'subject|expire'`

---

## PART 2: POST-DEPLOY CHECKLIST

> Run these checks **after deploying** to the EC2 host.

---

### 8. 🌍 PRODUCTION ENVIRONMENT

- [ ] **8.1** Public URL serves the wrapper — `curl -I https://tv.trikiman.shop/` → 200, TLS valid
- [ ] **8.2** TLS certificate not expiring within 30 days (`curl -vI` → check expiry)
- [ ] **8.3** Caddy is up — `systemctl is-active caddy.service` → `active`
- [ ] **8.4** Caddy config matches `Caddyfile` in repo — `caddy adapt --config /etc/caddy/Caddyfile`
- [ ] **8.5** TorrStream service is up — `systemctl is-active torrstream.service` → `active`
- [ ] **8.6** Service auto-restarts on crash (`Restart=always` configured) — `kill -9 $(pidof python)` test
- [ ] **8.7** TorrServer is up on `127.0.0.1:8090` — `curl -I http://127.0.0.1:8090/` from EC2
- [ ] **8.8** Wrapper listens only on `127.0.0.1:5000` (not `0.0.0.0` if behind Caddy in production)
- [ ] **8.9** `journalctl -u torrstream.service --since "10 min ago"` shows no exception loops
- [ ] **8.10** `positions.json` writable by service user (no permission-denied warnings on save)
- [ ] **8.11** Service env vars match §0.2.1 list (`systemctl show torrstream.service -p Environment`)
- [ ] **8.12** GitHub webhook URL is registered in repo settings → `https://tv.trikiman.shop/api/github-webhook`
- [ ] **8.13** Webhook secret in repo settings matches `GITHUB_WEBHOOK_SECRET` on EC2
- [ ] **8.14** Disk has ≥1 GB free for log accumulation
- [ ] **8.15** Logrotate or service log limits configured (no infinite log growth)
- [ ] **8.16** `sudo systemctl restart torrstream.service` permission granted to webhook runner (sudoers entry)

---

### 9. 🔄 LIVE END-TO-END FLOWS

> All require a real torrent in TorrServer + a real device.

- [ ] 🙋 **9.1** Search a known title → result shows up → `+ Добавить` → torrent appears in library
- [ ] 🙋 **9.2** Click newly added torrent → file list loads (single or multi)
- [ ] 🙋 **9.3** Single file: video plays within 5 s, controls responsive, seeking works
- [ ] 🙋 **9.4** Multi-file: episode panel renders, click EP1 → plays, `Далее →` jumps to EP2
- [ ] 🙋 **9.5** Watch ≥30 s → close player → reopen → resumes within 1 s of last position
- [ ] 🙋 **9.6** Watch to >95% → close → reopen → episode marked `✓ просмотрено`, TorrServer `/viewed` updated
- [ ] 🙋 **9.7** Cross-device: watch on phone → open on desktop → resumes from same position
- [ ] 🙋 **9.8** Cross-device: mark watched on phone → desktop shows `✓` for that episode
- [ ] 🙋 **9.9** Auto-next fires 3 s after EP1 ends → EP2 starts cleanly
- [ ] 🙋 **9.10** Click `⬇` on an episode → browser native download manager opens, file size matches
- [ ] 🙋 **9.11** Delete a watched torrent → returns to library, position entry gone (verify with `cat positions.json`)
- [ ] 🙋 **9.12** Search a Cyrillic title → results return; add → plays
- [ ] 🙋 **9.13** Install as PWA on phone → launches as standalone, no browser chrome, library loads
- [ ] 🙋 **9.14** Add via bare hash in modal → torrent gets normalized magnet, downloads start
- [ ] 🙋 **9.15** Add via `.torrent` URL in modal → adds successfully

---

### 10. 🔥 EDGE CASES & FAILURE MODES

- [ ] 🙋 **10.1** Stop TorrServer → reload UI → empty state shows `⚠️ Нет подключения к TorrServer` with the upstream URL
- [ ] 🙋 **10.2** Restart TorrServer → click `Повторить` → library re-populates
- [ ] 🙋 **10.3** Stop jacred (or block via `/etc/hosts`) → search shows `⚠️ Сервис поиска недоступен` + cached + library fallbacks
- [ ] 🙋 **10.4** Send malformed magnet → `Ошибка добавления` toast, no crash, library unaffected
- [ ] 🙋 **10.5** Mid-playback: kill TorrServer → player shows `⚠️ Ошибка воспроизведения`, not silent freeze
- [ ] 🙋 **10.6** Mid-playback: drop network → Plyr shows native error, position last save is intact
- [ ] 🙋 **10.7** Auto-deploy: push commit touching `app.py` → service restarts within 5 s (check `systemctl show ... -p ActiveEnterTimestamp`)
- [ ] 🙋 **10.8** Auto-deploy: push commit touching only `.planning/*.md` → no restart (`restart_scheduled=false`)
- [ ] 🙋 **10.9** Auto-deploy: invalid signature → 401, no `git pull` runs (`journalctl` clean)
- [ ] 🙋 **10.10** Auto-deploy: `positions.json` survives a code push (back up before, diff after)
- [ ] 🙋 **10.11** Concurrent position writes (open same torrent on 2 devices) → both writes land, last-write-wins per file_index
- [ ] 🙋 **10.12** Open the site after 24 h offline → SW shell loads from cache → API calls fail gracefully with toasts
- [ ] **10.13** Smoke script passes against production: `BASE_URL=https://tv.trikiman.shop python scripts/smoke_check.py` → 6/6
- [ ] 🙋 **10.14** Browser back/forward buttons don't break overlay state (player → close → back → no zombie player)
- [ ] 🙋 **10.15** Force-kill `python app.py` → systemd brings it back within 5 s, library reachable again
- [ ] 🙋 **10.16** Old format `positions.json` (flat schema) → wrapper auto-migrates to per-file schema on first read

---

## PART 3: FINAL SIGN-OFF

- [ ] **All Part 1 build/import items passed** — deps install, app imports, smoke script green
- [ ] **All Part 1 §2 API endpoints tested** — status, library, files, position, stream, download, add, remove, search, webhook
- [ ] **All Part 1 §3 UI/UX clicks tested** — every button on every overlay, every keyboard shortcut, every empty state
- [ ] **PWA verified** — install flow on Chrome desktop + Safari iOS + Chrome Android
- [ ] **Responsive verified** — 375 / 414 / 768 / 1280 / 1920 all clean
- [ ] **Performance baselines captured** — record actual numbers in §6
- [ ] **Security audit** — no committed secrets, webhook HMAC works, backend not publicly bound
- [ ] **Production environment** — Caddy + systemd both `active`, TLS valid, env vars set
- [ ] **Live e2e flows verified** — at least one real torrent end-to-end on phone + desktop
- [ ] **Edge cases drilled** — TorrServer kill, jacred kill, mid-playback failure, auto-deploy good + bad signature

> **Last verified**: _populate after first run_
> **Score**: _N/M passed per section_
>
> **Known gaps to track** (update as fixed; sourced from `.planning/codebase/CONCERNS.md`):
> - 🙋 **No automated test suite** — `tests/` does not exist. Manual verification only.
> - 🙋 **Single-file backend** — `app.py` mixes config, integrations, persistence, routes. Refactor pending.
> - 🙋 **Monolithic frontend** — `templates/index.html` is 1356 lines with inline CSS+JS. Split when complexity justifies it.
> - 🙋 **Legacy root `index.html`** — present but not served. Archive or delete to avoid confusion.
> - 🙋 **No DB-backed positions** — `positions.json` is file-based; revisit if multi-user concurrency grows.
> - 🙋 **No request validation library** — routes trust JSON shape with safe defaults; add schema validation if exposure widens.
> - 🙋 **Streaming proxies through Flask** — all bytes pass through Python; benchmark before scaling beyond personal use.
>
> **Resolved (do NOT re-add)**:
> - ✅ PWA paths under both root and `/app/` reverse proxy (phase 1, 2026-04-05)
> - ✅ Catalog/management diagnostics surface explicit upstream state (phase 2, 2026-04-21)
> - ✅ Playback probe + per-file resume + viewed-state sync (phase 3, 2026-04-24)
> - ✅ jacred outage fallback (cached + library matches) + installable shell (phase 4, 2026-04-24)
> - ✅ HMAC-verified GitHub webhook auto-deploy with `positions.json` preservation (post-v1.0)

---

## How to Run This Checklist

```bash
# 1. Pre-flight (local)
pip install -r requirements.txt
python -c "from app import app; print('OK')"
python app.py &                          # local instance on :5000
python scripts/smoke_check.py            # 6/6 expected

# 2. API surface (against production)
curl -I https://tv.trikiman.shop/
curl -s https://tv.trikiman.shop/api/status | jq
curl -s https://tv.trikiman.shop/api/torrents | jq '.diagnostics'

# 3. UI/UX manual pass (open in browser, walk every button per §3)
# Use Chrome DevTools MCP if available — covers §3 + §5 + §6 fast.

# 4. Production health (on EC2)
ssh ubuntu@<host> 'systemctl is-active caddy.service torrstream.service'
ssh ubuntu@<host> 'journalctl -u torrstream.service --since "10 min ago" | tail -50'

# 5. Auto-deploy webhook smoke (push a no-op doc commit, watch logs)
git commit --allow-empty -m "test: verify auto-deploy webhook"
git push origin main
ssh ubuntu@<host> 'journalctl -u torrstream.service -n 20'
```
