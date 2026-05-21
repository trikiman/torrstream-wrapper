# Roadmap: TorrStream

## Active Milestone: v2.3 Lampa parser shim

Single-phase milestone driven by a real user-blocking issue surfaced 2026-05-17:
plain `http://jac.red` is intermittently blocked / throttled on the user's
network, killing Lampa torrent search. Workaround (switching to `https://jac.red`
in Lampa settings) works but is fragile — every time the parser host changes
or HTTPS gets blocked too, the user is stuck.

Robust fix: expose `/api/v1.0/torrents` on TorrStream that proxies to jac.red.
Lampa points at `https://tv.trikiman.shop` as its parser. Survives any single
jacred mirror going down because Oracle Amsterdam reaches all of them and we
already proxy via `JACRED_URL` env var (default `https://jac.red`).

### Phases

- [ ] **Phase 1: Lampa parser shim** — expose `/api/v1.0/torrents` proxy, add CORS, switch Lampa client to use it. Survives jacred mirror flips and ISP-side blocks of jac.red.

### Phase Details

#### Phase 1: Lampa parser shim

**Goal:** TorrStream can be used as a Lampa-compatible torrent parser. Switching Lampa's `jackett_url` from `https://jac.red` to `https://tv.trikiman.shop` works without further configuration.

**Depends on:** Nothing (v2.2 wrapper already proxies jac.red via `/api/search` — this just exposes it under jacred's native URL shape).

**Requirements:** [LAMPA-01, LAMPA-02]

**Success Criteria:**
1. `GET /api/v1.0/torrents?search=Matrix` returns the **raw jacred response shape** (flat array of `{title, size, sid, tracker, magnet, ...}`), unchanged from upstream — Lampa parses it natively.
2. Other query params (`Query`, `title`, `year`, `apikey`, `is_serial`, etc.) forwarded to jac.red unchanged.
3. CORS headers permit cross-origin fetch from `lampa.mx` and other Lampa hosts.
4. Endpoint survives upstream jac.red being temporarily unreachable — returns 502 with diagnostics body, never silently 200.
5. `JACRED_URL` env var override works — production uses `https://jac.red`; can be flipped to a different mirror without code change.
6. Lampa client switched to `https://tv.trikiman.shop` parser URL — torrent search renders results unchanged.

**Plans:** 1
- 01-01: Implement `/api/v1.0/torrents` route, extend CORS to `/api/v1.0/*`, add 2 contract tests + 1 integration test, deploy, switch Lampa, verify.

## Progress

| Phase | Plans Complete | Status |
|-------|----------------|--------|
| 1. Lampa parser shim | 0/1 | Pending |

## Archived Milestones

### v2.2 Robustness + Coverage (shipped 2026-05-14)
- 3 phases, 5 plans, 9 reqs, 67 tests. API hygiene + UX completeness + pytest harness. See `.planning/milestones/v2.2-ROADMAP.md`.

### v2.1 Player UX + iOS readiness (shipped 2026-05-12)
- 2 phases, 5 plans. Plyr→Vidstack swap, audio fix, Oracle topology docs. See `.planning/milestones/v2.1-ROADMAP.md`.

### v2.0 Oracle Migration (shipped 2026-05-12)
- 3 phases, 7 plans. AWS→Oracle migration. See `.planning/phases/01-oracle-baseline/`.

### v1.1 Cross-Client Position Sync (shipped 2026-04-29)
- 1 phase, 2 plans. See `.planning/milestones/v1.1-ROADMAP.md`.

### v1.0 TorrStream (shipped 2026-04-24)
- 4 phases, 11 plans. See `.planning/milestones/v1.0-ROADMAP.md`.
