---
status: complete
phase: 01-brownfield-baseline
source:
  - 01-01-SUMMARY.md
  - 01-02-SUMMARY.md
started: 2026-04-05T21:23:00+03:00
updated: 2026-04-05T21:27:00+03:00
---

## Current Test

[testing complete]

## Tests

### 1. Deployment document exists and matches the real wrapper routes
expected: `docs/DEPLOYMENT.md` describes `app.py`, `templates/index.html`, `/manifest.json`, `/sw.js`, and the supported deployment topologies.
result: pass

### 2. Legacy duplicate frontend file is clearly marked non-authoritative
expected: the root `index.html` warns that `templates/index.html` is the served source of truth.
result: pass

### 3. Smoke-test playbook exists and is referenced from project guidance
expected: `docs/SMOKE-TESTS.md` exists and `AGENTS.md` points maintainers at it for runtime-affecting changes.
result: pass

### 4. Root-path shell loads cleanly at iPad-sized viewport
expected: loading `http://127.0.0.1:5000/` at an iPad-sized viewport should fetch the manifest and service worker without `/app/` 404s and should show no console errors.
result: pass

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[]
