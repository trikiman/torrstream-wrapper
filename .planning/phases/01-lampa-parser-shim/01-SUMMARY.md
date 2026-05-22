---
phase: 01-lampa-parser-shim
milestone: v2.3
subsystem: api
tags: [lampa, parser, jacred, jackett, proxy, cors]
provides:
  - /api/v1.0/torrents proxy (jacred-flavored, parser_torrent_type=jacred)
  - /api/v2.0/indexers/all/results proxy (Jackett REST flavor, parser_torrent_type=jackett)
  - Shared _lampa_proxy() helper forwarding all query params + auto-injecting JACRED_KEY
  - 502 with `{}` body on upstream failure (Lampa shows "no results" instead of parser error)
  - CORS Access-Control-Allow-Origin:* on both /api/v1.0/* and /api/v2.0/*
key-decisions:
  - "Proxy verbatim — return upstream Content-Type and body bytes unchanged so Lampa parses jacred's native shape without translation"
  - "Add BOTH the v1.0/torrents (jacred) and v2.0/indexers (Jackett) paths — Lampa's parser_torrent_type=jackett actually hits the Jackett REST URL pattern; jacred mirrors transparently accept both"
  - "On upstream failure return 502 with `{}` instead of error JSON so Lampa sees 'no results' not 'parser not responding'"
  - "Auto-deploy webhook broken (looks for torrstream.service unit, real unit is flask-wrapper.service) — captured as v2.4 todo; manual SSH deploy used for this phase"
requirements-completed: [LAMPA-01, LAMPA-02]
duration: 90min (impl 30 + test 15 + deploy debug 30 + verify 15)
completed: 2026-05-22
commits:
  - 9fb813c feat(api): /api/v1.0/torrents Lampa parser shim — survives jac.red blocks
  - 254c58f feat(api): add /api/v2.0/indexers/all/results for Lampa's parser_torrent_type=jackett
---

# Phase 1 Summary: Lampa parser shim

**Outcome:** TorrStream now serves as a Lampa-compatible torrent parser. User pointed Lampa's `jackett_url` at `https://tv.trikiman.shop` (replacing the unreliable `https://jac.red` that kept getting blocked by ISP-side filters), and torrent search renders 20+ results immediately. Survives jacred mirror flips because the wrapper's `JACRED_URL` env var is the only knob ops needs to flip — Lampa never has to be reconfigured again.

## Implementation

Two routes in app.py, both calling shared `_lampa_proxy(upstream_path)`:

| Route | Lampa parser_torrent_type | Upstream call |
|---|---|---|
| `GET /api/v1.0/torrents` | `jacred` | `JACRED_URL/api/v1.0/torrents` |
| `GET /api/v2.0/indexers/all/results` | `jackett` | `JACRED_URL/api/v2.0/indexers/all/results` |

Both forward all query params unchanged (search, Query, title, title_original, year, is_serial, genres, apikey, ...). Body bytes returned verbatim with upstream Content-Type. JACRED_KEY auto-injected when wrapper has it set and caller didn't include apikey. On upstream failure: 502 + `{}` body so Lampa shows "no results" rather than a parser error.

CORS handler in `_cors_headers()` extended to cover `/api/v2.0/*` alongside `/api/v1.0/*` and the existing `/api/position/*`, `/static/*` scopes. Read-only (GET/HEAD/OPTIONS). Origin `*` so any Lampa client can fetch cross-origin.

## Discovered + landed mid-phase

**Lampa's "jackett" parser type uses Jackett's URL pattern, not jacred's.**
First deploy was just `/api/v1.0/torrents`. After switching Lampa's `jackett_url` to TorrStream and reloading the search activity, Lampa returned "Парсер не отвечает на запрос". XHR capture showed Lampa actually hitting `/api/v2.0/indexers/all/results?apikey=&Query=...&title=...&year=...&is_serial=...&genres=...` — the Jackett REST API shape. jacred mirrors accept both paths and return the Jackett-shaped `{Results:[...]}` for the v2.0 path; we proxy each to its matching upstream path. Both shipped in commits 9fb813c → 254c58f same session.

**Auto-deploy webhook is silently broken.**
First push (9fb813c) didn't take effect on prod. Diagnosed via SSH: the `github_webhook` route does `sudo systemctl restart torrstream.service`, but the actual unit on the Oracle host is `flask-wrapper.service`. The restart command silently fails (no error path because Popen returns immediately). git pull happens but Flask is never restarted. **Workaround for this phase: manually `git pull && systemctl restart flask-wrapper.service` via SSH.** Captured as a v2.4 todo (see backlog).

This explains the May 16 process start time observed earlier: the live Flask process has been running since around then with frontend-only commits (templates/index.html, static/lampa-sync.js — served from disk on every request, no restart needed). All Python-level changes (v2.2 hash validation, malformed JSON handling, etc.) have been silently NOT loaded into the running process for ~6 days. Some prior commits worked because they only changed templates/static files.

## Coverage

Tests:
- `tests/api/test_lampa_parser.py` — 11 tests covering both routes: param forwarding, raw body passthrough, empty-object passthrough, upstream failure, apikey injection, caller-provided apikey preservation, CORS origin/methods.
- `tests/integration/test_live_contract.py` — 2 new live tests against `tv.trikiman.shop`: jacred-native shape preserved + CORS for cross-origin Lampa fetch.
- All-suite: 68 smoke + 11 integration (3 skipped — empty library) = 79 total / 76 PASS / 0 FAIL.

Verification:
- curl from Oracle: `/api/v1.0/torrents?search=matrix` → 200, 731 KB body, real jacred records.
- curl from Oracle: `/api/v2.0/indexers/all/results?Query=matrix` → 200, 2553 bytes, Jackett-shape `{Results: [...]}`.
- Lampa from lampa.mx tab: 20 torrent_items rendered for Matrix, sample_titles all real Russian releases.

## Carry-overs

- Auto-deploy webhook unit-name fix → v2.4 backlog (todo: `2026-05-22-fix-webhook-unit-name`).
- Multi-mirror failover in the wrapper (LAMPA-03) → v2.4+ if a single mirror going down ever becomes a real problem; for now `JACRED_URL` env-var swap is enough.
