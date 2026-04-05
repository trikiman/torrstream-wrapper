# Codebase Concerns

**Analysis Date:** 2026-04-05

## Tech Debt

**Single-file backend:**
- Issue: `app.py` contains configuration, integrations, persistence, and all route handlers
- Why: the project was built as a compact personal utility
- Impact: changes in one area are easy to couple to unrelated behavior
- Fix approach: split into modules for config, TorrServer client, persistence, and routes

**Monolithic frontend template:**
- Issue: `templates/index.html` contains markup, CSS, and JavaScript inline
- Why: fast iteration and low setup overhead
- Impact: large changes are hard to review, test, and safely refactor
- Fix approach: separate UI concerns or move to a small frontend build step only if complexity justifies it

**Legacy duplicate frontend file:**
- Issue: root `index.html` appears to be an older duplicate and is not served by Flask
- Why: previous iteration was left in the repo
- Impact: easy to edit the wrong file and think the app changed when it did not
- Fix approach: remove or clearly archive the duplicate root file

## Known Bugs

**Silent integration failures:**
- Symptoms: endpoints can return empty arrays or generic wrapper errors without exposing the actual upstream failure
- Trigger: TorrServer auth mismatch, TorrServer downtime, jacred response changes, or file I/O failures
- Workaround: inspect process logs or reproduce calls manually
- Root cause: broad exception handling in helper functions and route handlers

## Security Considerations

**Hardcoded default service credentials:**
- Risk: `app.py` ships default TorrServer credentials (`admin` / `122662Rus`) as fallback values
- Current mitigation: env vars can override them
- Recommendations: remove sensitive defaults and require explicit configuration

**Unauthenticated wrapper endpoints:**
- Risk: if the Flask wrapper is publicly exposed, anyone can list, add, remove, and stream torrents
- Current mitigation: none in app code
- Recommendations: keep the wrapper on a private network, add reverse-proxy auth, or implement application-level access control

## Performance Bottlenecks

**Proxy streaming through Flask:**
- Problem: all playback and download traffic passes through the Python process
- Measurement: not benchmarked in-repo
- Cause: wrapper proxies bytes instead of redirecting to a dedicated media edge
- Improvement path: benchmark real throughput, then decide whether direct signed URLs or a dedicated reverse proxy are needed

**File-backed position writes:**
- Problem: every progress update reads and rewrites `positions.json`
- Measurement: not benchmarked in-repo
- Cause: no database or append-only write strategy
- Improvement path: add locking or move state to a lightweight database if concurrent usage grows

## Fragile Areas

**TorrServer integration contract:**
- Why fragile: wrapper behavior assumes specific response shapes for `/torrents`, `/viewed`, and `/stream`
- Common failures: upstream auth or response changes break merging logic
- Safe modification: validate real TorrServer responses before editing request/response handling
- Test coverage: none

**Playback asset paths and PWA behavior:**
- Why fragile: asset pathing is now relative and scope-aware, but small regressions can still break root or `/app/` deployments
- Common failures: broken icons, manifest registration, or service-worker cache misses after path changes
- Safe modification: verify both direct-root and reverse-proxy deployments after any manifest/service-worker/template path edit
- Test coverage: none

## Scaling Limits

**Process model:**
- Current capacity: single-process Flask app with local JSON persistence
- Limit: no documented concurrency or throughput ceiling
- Symptoms at limit: slower stream proxying, file-write contention, and degraded UI responsiveness
- Scaling path: modularize the backend, add proper WSGI serving, and replace JSON persistence if multi-user demand appears

## Dependencies at Risk

**Implicit Python dependencies:**
- Risk: no `requirements.txt` or lockfile exists in the repo
- Impact: deployments can drift and break on a fresh machine
- Migration plan: add a minimal dependency manifest and pin known-good versions

**jacred API dependency:**
- Risk: search UX depends on an external API contract not controlled in this repo
- Impact: search can degrade or break without local code changes
- Migration plan: document fallback behavior and isolate response parsing

## Missing Critical Features

**Automated verification:**
- Problem: there is no repeatable test suite for the wrapper's core flows
- Current workaround: manual `curl` checks and browser testing
- Blocks: safe refactors and deployment confidence
- Implementation complexity: low to medium

**Deployment documentation that matches reality:**
- Problem: previous project docs drifted away from the current runtime/deployment shape
- Current workaround: inspect code and server state manually
- Blocks: reliable onboarding and maintenance
- Implementation complexity: low

## Test Coverage Gaps

**Backend API surface:**
- What's not tested: list, files, search, add/remove, position, stream, and download routes
- Risk: regressions can ship unnoticed
- Priority: High
- Difficulty to test: Medium because TorrServer and jacred should be mocked

**Frontend integration behavior:**
- What's not tested: search/add/play/resume interactions and PWA asset loading
- Risk: deployment/path regressions are easy to introduce
- Priority: High
- Difficulty to test: Medium

---

*Concerns audit: 2026-04-05*
*Update as issues are fixed or new ones discovered*
