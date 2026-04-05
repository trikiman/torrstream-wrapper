# Testing Patterns

**Analysis Date:** 2026-04-05

## Test Framework

**Runner:**
- No automated test runner is configured in this repository
- No `pytest`, `unittest`, Playwright, or other test config files are present

**Assertion Library:**
- None configured

**Run Commands:**
```bash
python app.py
curl http://127.0.0.1:5000/api/torrents
curl "http://127.0.0.1:5000/api/search?q=test"
```

## Test File Organization

**Location:**
- No test files or test directories currently exist

**Naming:**
- No naming convention established yet

**Structure:**
```text
No automated test structure is present today.
```

## Test Structure

**Suite Organization:**
- Manual smoke testing is the de facto validation method
- Typical validation is endpoint-level `curl` checks plus browser/manual playback testing

**Patterns:**
- Start the Flask app
- Verify library/search endpoints
- Verify browser load and playback manually against a real TorrServer instance

## Mocking

**Framework:**
- None configured

**What to Mock:**
- Future automated tests should mock TorrServer and jacred HTTP responses
- Future tests should isolate file writes to a temporary positions file

**What NOT to Mock:**
- Wrapper request/response shaping logic
- Resume-state serialization rules

## Fixtures and Factories

**Test Data:**
- Current sample state exists only as hand-edited `positions.json`

**Location:**
- No fixtures/factories directory currently exists

## Coverage

**Requirements:**
- No coverage target is defined

**Configuration:**
- No coverage tool is configured

## Test Types

**Unit Tests:**
- Missing

**Integration Tests:**
- Missing
- Most valuable first targets are `list_torrents`, `list_files`, `save_position`, `add_torrent`, and `search`

**E2E Tests:**
- Missing
- Most valuable E2E target is browser playback/resume behavior through a mocked or disposable TorrServer instance

## Common Patterns

**Current Practical Verification:**
- Verify `/api/torrents` returns data from TorrServer
- Verify `/api/files/<hash>` includes merged viewed/position data
- Verify `/api/position/<hash>` read/write behavior
- Verify `/api/stream/<filename>` returns range-capable media responses
- Verify the UI loads the served `templates/index.html` and can add/search/play content

---

*Testing analysis: 2026-04-05*
*Update when test patterns change*
