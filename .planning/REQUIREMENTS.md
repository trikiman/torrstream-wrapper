# Requirements: TorrStream

**Defined:** 2026-04-05 (v1.0), amended 2026-05-11 (v2.0) and 2026-05-12 (v2.1)
**Core Value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.

## v1 Requirements (shipped)

### Library
- [x] **LIBR-01**: User can list torrents from TorrServer through the wrapper API.
- [x] **LIBR-02**: User can inspect file choices for a torrent and see video files highlighted for playback.

### Playback
- [x] **PLAY-01**: User can stream a selected file through the wrapper with HTTP range support.
- [x] **PLAY-02**: User can download a selected file through the wrapper.

### Sync
- [x] **SYNC-01**: User watch position is stored per torrent file on the server.
- [x] **SYNC-02**: Wrapper marks a file as viewed in TorrServer when playback passes the completion threshold.
- [x] **SYNC-03** (v1.1): Lampa plugin reads and writes wrapper positions cross-origin, seeking video to saved offset on stream start.

### Management
- [x] **MGMT-01**: User can add a torrent from a magnet link or search result.
- [x] **MGMT-02**: User can remove a torrent and clear any saved local position state for it.

### Discovery
- [x] **DISC-01**: User can search jacred from the UI and review addable results.

### Delivery
- [x] **DELV-01**: The web UI loads as a single installable app shell with manifest and service-worker assets.
- [x] **DELV-02**: Deployment paths and runtime configuration are documented and aligned with the actual access pattern.

### Quality
- [x] **QUAL-01**: Core wrapper behaviors have a repeatable smoke-verification path.

## v2.0 Requirements (Oracle migration, shipped 2026-05-12)

### Infrastructure
- [x] **INFRA-01**: Oracle target host provisioned with swap, firewall open for 80/443/8090, packages installed.
- [x] **INFRA-02**: Systemd units for TorrServer, Flask wrapper, Caddy with `Restart=on-failure`.
- [x] **INFRA-03**: Caddy terminates TLS for `tv.trikiman.shop` via Let's Encrypt.
- [x] **SEC-01**: TorrServer `/` requires BasicAuth (accs.db plaintext `{user: pass}`). Lampa clients send auth via Lampa's built-in TorrServer credentials field.

### Migration
- [x] **MIGR-01**: `positions.json` migrated byte-for-byte.
- [x] **MIGR-02**: TorrServer `config.db` + `settings.json` migrated so all 3 torrents are present with viewed markers.
- [x] **MIGR-03**: Wrapper code + GitHub webhook deployed on Oracle with HMAC-verified auto-pull.

### Cutover
- [x] **CUT-01**: DNS `tv.trikiman.shop` pointed at Oracle (A record `158.101.214.234`).
- [x] **CUT-02**: Production smoke checklist passes 9/9 against the live domain.
- [ ] **CUT-03**: AWS EC2 instance stopped, snapshotted, terminated. *Deferred 24h as hot standby.*

## v2.1 Requirements (active — Player UX + iOS readiness)

### Player
- [ ] **PLAY-03**: Vidstack is the web player; Plyr and its CDN scripts are removed from the shell.
- [ ] **PLAY-04**: Audio plays by default on desktop Chrome/Firefox and on iOS Safari once the user initiates playback. No silent-playback regressions.
- [ ] **PLAY-05**: Double-tap on the left third of the player rewinds 10s; double-tap on the right third fast-forwards 10s. Tap in the middle toggles play/pause.
- [ ] **PLAY-06**: Player exposes the underlying HTMLVideoElement so `static/lampa-sync.js`'s `findVideo()` continues to locate it. Plugin must not need changes.
- [ ] **PLAY-07**: Playback controls (play, pause, seek, volume, fullscreen, PiP where supported) work on iOS Safari and iPad Safari; inline playback is preserved (no forced fullscreen on `<video>` tap).

### Delivery
- [ ] **DELV-05**: Service worker keeps working after the Plyr assets are removed from the cached asset list.
- [ ] **DELV-06**: Bundle footprint increase is documented (Plyr was ~120 KB JS; Vidstack is ~250 KB gzip). Still loaded from CDN, no bundler.

### Quality
- [ ] **QUAL-02**: `scripts/smoke_prod.py` updated to cover the new player markup (it currently checks the shell contains `plyr=True`; swap for the Vidstack indicator).
- [ ] **QUAL-03**: Manual iOS smoke on a real iPhone or iPad: library → file → play → seek via double-tap → resume on reopen.

## Future (v2.2+ backlog)

- **PROD-01**: Wrapper supports configurable base paths and direct-root deployments.
- **PROD-02**: Wrapper supports authenticated user access.
- **PROD-03**: Wrapper provides richer metadata and poster normalization.
- **ENG-01**: Backend is split into modules with automated tests.
- **ENG-02**: Dependency versions are pinned in `requirements.txt`.
- **INFRA-04**: Re-migrate from x86-2 to ARM Ampere if `oracle-hunter` catches capacity.
- **PROD-04**: In-player chapter markers for multi-episode torrents.
- **PROD-05**: Subtitle track selection in Vidstack (TorrServer's subtitle files).

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reimplementing TorrServer | Not the purpose of the wrapper |
| Native mobile/TV apps | Browser delivery + Lampa plugin is sufficient |
| Social or collaborative features | Project is single-user/self-hosted |
| Rewriting `app.py` into modules during this milestone | Keep blast radius small |
| Promoting `positions.json` to a database | Not needed at current scale |
| Moving to a JS bundler / SPA framework | Vidstack ships web components over CDN |

## Traceability

### v1 (shipped, archived)
| Requirement | Phase | Status |
|-------------|-------|--------|
| DELV-02 | v1.0 Phase 1 | Complete |
| QUAL-01 | v1.0 Phase 1 | Complete |
| LIBR-01, LIBR-02 | v1.0 Phase 2 | Complete |
| MGMT-01, MGMT-02 | v1.0 Phase 2 | Complete |
| PLAY-01, PLAY-02 | v1.0 Phase 3 | Complete |
| SYNC-01, SYNC-02 | v1.0 Phase 3 | Complete |
| DISC-01, DELV-01 | v1.0 Phase 4 | Complete |
| SYNC-03 | v1.1 Phase 1 | Complete |

### v2.0 (shipped 2026-05-12)
| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01, INFRA-02, INFRA-03, SEC-01 | v2.0 Phase 1 | Complete |
| MIGR-01, MIGR-02, MIGR-03 | v2.0 Phase 2 | Complete |
| CUT-01, CUT-02 | v2.0 Phase 3 | Complete |
| CUT-03 | v2.0 Phase 3 | Deferred (scheduled) |

### v2.1 (active)
| Requirement | Phase | Status |
|-------------|-------|--------|
| PLAY-03, PLAY-04, PLAY-05, PLAY-06, PLAY-07 | v2.1 Phase 1 | Active |
| DELV-05, DELV-06 | v2.1 Phase 1 | Active |
| QUAL-02, QUAL-03 | v2.1 Phase 2 | Pending |

**Coverage:**
- v1: 13 requirements / 13 shipped
- v2.0: 10 requirements / 9 shipped + 1 deferred
- v2.1: 9 requirements / 0 shipped

---
*Requirements defined: 2026-04-05*
*v1.1 amendments: 2026-04-29 (SYNC-03)*
*v2.0 amendments: 2026-05-11 (INFRA-*, MIGR-*, CUT-*, SEC-01) — shipped 2026-05-12*
*v2.1 amendments: 2026-05-12 (PLAY-03..07, DELV-05..06, QUAL-02..03)*
