# Roadmap: TorrStream

## Overview

This roadmap treats the existing wrapper as a brownfield codebase that already provides useful behavior but lacks durable planning, deployment clarity, and automated verification. The work starts by stabilizing documentation and project memory, then hardens the wrapper API, playback/sync behavior, and browser delivery path.

## Phases

- [x] **Phase 1: Brownfield Baseline** - Replace stale docs with planning artifacts and operationally accurate project instructions. (completed 2026-04-05)
- [x] **Phase 2: Library and Management Hardening** - Verify and stabilize listing, file inspection, add, and remove flows. (completed 2026-04-21)
- [ ] **Phase 3: Playback and Sync Hardening** - Verify and stabilize streaming, downloading, and per-file resume behavior.
- [ ] **Phase 4: Discovery and Delivery Alignment** - Verify search, app-shell delivery, and deployment-path correctness.

## Phase Details

### Phase 1: Brownfield Baseline
**Goal**: Establish the codebase map, project memory, and repo instructions that reflect the current application reality.
**Depends on**: Nothing (first phase)
**Requirements**: [DELV-02, QUAL-01]
**Success Criteria** (what must be TRUE):
  1. Project-facing docs and instructions describe the actual codebase and runtime assumptions.
  2. The repo has `.planning/` artifacts that future GSD workflows can build on.
  3. Known stale or duplicate project documentation is removed or explicitly marked non-authoritative.
**Plans**: 2 plans

Plans:
- [x] 01-01: Map the existing codebase and capture stack, structure, conventions, and risks.
- [x] 01-02: Create brownfield planning artifacts and Codex-facing project instructions.

### Phase 2: Library and Management Hardening
**Goal**: Make core catalog and mutation flows dependable against the real TorrServer integration.
**Depends on**: Phase 1
**Requirements**: [LIBR-01, LIBR-02, MGMT-01, MGMT-02]
**Success Criteria** (what must be TRUE):
  1. Listing torrents and torrent files works against the configured TorrServer instance.
  2. Add/remove flows behave consistently and keep local position state in sync.
  3. Failure cases are visible enough to debug without guessing.
**Plans**: 3 plans

Plans:
- [x] 02-01: Verify and harden torrent listing and file inspection responses.
- [x] 02-02: Verify and harden add/remove flows plus local cleanup behavior.
- [x] 02-03: Improve integration-error visibility for catalog and management routes.

### Phase 3: Playback and Sync Hardening
**Goal**: Make playback, downloading, and resume behavior reliable across the wrapper and TorrServer boundary.
**Depends on**: Phase 2
**Requirements**: [PLAY-01, PLAY-02, SYNC-01, SYNC-02]
**Success Criteria** (what must be TRUE):
  1. Streaming and downloading selected files return correct headers and media bytes.
  2. Resume position is stored per file and read back correctly.
  3. Viewed-state sync behaves predictably when playback completes.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Verify stream/download proxy behavior and range handling.
- [ ] 03-02: Verify and harden per-file position persistence.
- [ ] 03-03: Verify viewed-state synchronization with TorrServer.

### Phase 4: Discovery and Delivery Alignment
**Goal**: Make search and browser delivery paths reliable for the intended deployment shape.
**Depends on**: Phase 3
**Requirements**: [DISC-01, DELV-01]
**Success Criteria** (what must be TRUE):
  1. Search returns usable results and integrates cleanly with add flow.
  2. The web shell, manifest, icons, and service worker load under the supported deployment path.
  3. A repeatable smoke-verification path exists for the main user flows.
**Plans**: 3 plans

Plans:
- [ ] 04-01: Verify and harden jacred search integration.
- [ ] 04-02: Reconcile browser asset paths with the supported deployment topology.
- [ ] 04-03: Add a lightweight smoke-verification workflow for critical flows.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Brownfield Baseline | 2/2 | Complete    | 2026-04-05 |
| 2. Library and Management Hardening | 3/3 | Complete | 2026-04-21 |
| 3. Playback and Sync Hardening | 0/3 | Not started | - |
| 4. Discovery and Delivery Alignment | 0/3 | Not started | - |
