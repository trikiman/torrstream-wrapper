# TorrStream

## What This Is

TorrStream is a self-hosted web wrapper around TorrServer. It provides a single browser UI for browsing torrents, searching jacred, streaming or downloading files, and syncing watch progress across devices through server-side position state. A Lampa plugin (`static/lampa-sync.js`) extends the same position state to Lampa playback on any device.

## Core Value

A torrent added once should be easy to find, play, and resume from any device through one simple web UI.

## Requirements

### Validated

**v1.0 + v1.1:**
- ✓ Browse the TorrServer library and inspect playable files
- ✓ Add and remove torrents through the wrapper API
- ✓ Stream and download media through the wrapper with resume support
- ✓ Persist per-file watch state and sync viewed markers back to TorrServer
- ✓ Search jacred and add results to TorrServer
- ✓ Installable PWA shell with Safari/iPad guidance
- ✓ Repeatable smoke-verification path (`docs/SMOKE-TESTS.md`, `scripts/smoke_prod.py`)
- ✓ Cross-client position sync via Lampa plugin + CORS-enabled `/api/position/*`

**v2.0 (Oracle migration, shipped 2026-05-12):**
- ✓ Live deployment moved from AWS EC2 to Oracle Cloud Always Free (`158.101.214.234`)
- ✓ All user state preserved (3 torrents + 4 position entries, viewed markers intact)
- ✓ Domain `tv.trikiman.shop` + HTTPS + auto-deploy webhook working on Oracle
- ✓ Lampa plugin URL unchanged — existing installations keep working
- ✓ Service worker installation fixed along the way (opaque-response tolerance)
- ✓ Auto-warmup on cold-start torrents (file_stats empty → wrapper pings /stream → re-fetches)
- ⏳ AWS EC2 decommission deferred 24h for rollback safety net

### Active (v2.1 — Player UX + iOS readiness)

- [ ] Replace Plyr with Vidstack as the web player; preserve Lampa-plugin wire format and HTTP stream contract
- [ ] Restore audio playback (regression reported after Plyr + Safari autoplay policy interaction)
- [ ] Add double-tap-to-seek ±10s gesture (Vidstack built-in)
- [ ] Verify iOS Safari touch UX (playsinline, gesture, PiP) with the new player
- [ ] Keep `static/lampa-sync.js` untouched — plugin talks to `<video>` element directly, new player must expose the same

### Out of Scope

- Replacing TorrServer as the media engine
- Multi-user accounts and social features
- Native mobile or TV apps
- Rewriting the Flask wrapper into a framework refactor (still single-module, keep it boring)
- Promoting `positions.json` to a database (still fine at current scale)
- Moving frontend into a bundler / SPA framework (Vidstack ships UMD/ESM from CDN)

## Context

### Application

- Backend: Flask, single module `app.py`
- Frontend: single monolithic template `templates/index.html` + `static/lampa-sync.js`
- State: `positions.json` for resume state, TorrServer's own database for torrent metadata
- Deployment: Caddy (80/443) → Flask (localhost:5000) → TorrServer (localhost:8090)
- DNS: `tv.trikiman.shop` A record → Oracle (`158.101.214.234`)
- Plugin: `https://tv.trikiman.shop/static/lampa-sync.js` installed into Lampa.Storage, syncs positions via CORS

### Current Infrastructure (v2.0)

- Oracle Cloud Always Free, `eu-amsterdam-1`, `vless-x86-2` = `158.101.214.234`
- Ubuntu 22.04, 1 OCPU, 1 GB RAM + 4 GB swap, 45 GB disk
- Caddy :80/:443 → Flask wrapper :5000 → TorrServer :8090 (BasicAuth `torrstream`)
- `oracle-hunter` on the sister instance (`152.70.58.201`) continues polling for ARM Ampere capacity
- AWS Frankfurt box (`13.60.174.46`) still running as a 24h hot standby before termination

### Player Today (to be replaced in v2.1)

- Plyr 3.7.8 loaded from `cdn.plyr.io`
- Inline `<video playsinline webkit-playsinline>` inside a custom modal in `templates/index.html`
- Known issues on Oracle + Safari/Chrome:
  - ⚠️ Audio silent on first play (likely Chrome autoplay-muted policy + Plyr not surfacing the unmute prompt clearly)
  - ⚠️ No double-tap-to-seek gesture
  - ⚠️ Safari touch controls are Plyr's defaults, not iOS-native feeling
  - Plyr is in maintenance mode; the Mux team is merging it into Video.js v10. Swapping to Vidstack now avoids a second migration later.

## Constraints

- **Tech stack**: Keep the current Python Flask + single-template + vanilla JS model. Vidstack ships as web components over CDN — no bundler step required.
- **Dependency**: TorrServer remains the source of torrent and stream data
- **Persistence**: Resume state stays in `positions.json`
- **DNS**: Stay on `tv.trikiman.shop`
- **Free tier**: Oracle Always Free, no billing changes
- **No regressions**: Lampa plugin behavior, PWA install, jacred search, CORS `/api/position/*` must keep working

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep a wrapper architecture over TorrServer | Streaming and torrent-state logic already exist upstream | ✓ Good |
| Store playback progress in `positions.json` | Simple persistence for a personal deployment | ⚠️ Revisit later |
| Use a single HTML template for the UI | Fast iteration with minimal tooling | ⚠️ Revisit later |
| Ship Lampa plugin instead of a native TV app | Browser-sourced plugin keeps the wrapper architecture consistent | ✓ Good |
| Migrate to Oracle Always Free | Zero-cost hosting, existing free-tier instance already provisioned | ✓ Shipped v2.0 |
| Accept 1 GB RAM on `vless-x86-2` (mitigate with swap + tuning) | ARM Ampere 4 OCPU / 12 GB is not free-tier available in Amsterdam right now | ✓ Working with 4 GB swap |
| Expose TorrServer :8090 publicly with `--httpauth` | Matches AWS behavior Lampa expects | ✓ Lampa connects successfully |
| **Swap Plyr → Vidstack** (v2.1) | Native double-tap gestures, better iOS Safari handling, HLS.js + DASH built in, actively developed, Plyr is being folded into Video.js v10 anyway | ⏳ v2.1 in progress |
| **Keep plugin targeting raw `<video>` element** | Plugin's `findVideo()` walks the DOM; Vidstack still renders a real `<video>` underneath so the contract holds | ⏳ Must verify during v2.1 |

---
*Last updated: 2026-05-12 at start of v2.1 Player UX milestone*
