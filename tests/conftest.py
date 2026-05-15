"""Shared pytest fixtures for TorrStream tests.

Two test layers:

1. **Flask test client** (default) — fast, deterministic. TorrServer interactions
   are mocked via patches on `app.ts_post` / `app.ts_probe` / `app.ts_get` /
   `app.set_viewed`. Hit any API route without network.

2. **Live wrapper smoke** — `live_session` fixture hits `TORRSTREAM_BASE`
   (default `https://tv.trikiman.shop`). Read-only by default; mutations
   require `-m e2e`. Skip cleanly if base is unreachable.
"""

import json
import os
import sys
from pathlib import Path

import pytest
import requests

# Make app.py importable when tests run from project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Fresh Flask app instance with isolated positions.json per test.

    Disables TorrServer auth so tests don't need real credentials.
    """
    # Point positions.json at a tmp file so tests don't pollute prod state.
    monkeypatch.setenv("TORRSERVER_URL", "http://127.0.0.1:8090")
    monkeypatch.setenv("TORRSERVER_USER", "")
    monkeypatch.setenv("TORRSERVER_PASS", "")

    # Reload app module to pick up env override and fresh state.
    if "app" in sys.modules:
        del sys.modules["app"]
    import app as appmod  # noqa: E402  (deferred import is intentional)

    # Override the positions file path so we never touch the real one.
    appmod.POSITIONS_FILE = tmp_path / "positions.json"
    appmod.RECENT_SEARCHES_FILE = tmp_path / "recent_searches.json"

    appmod.app.config["TESTING"] = True
    return appmod


@pytest.fixture
def client(app):
    """Flask test client with TESTING=True."""
    return app.app.test_client()


@pytest.fixture
def known_hash():
    """A well-formed 40-char SHA-1 hex hash (the Matrix torrent on prod).

    Used by tests that need a hash that passes format validation. Tests don't
    rely on this hash being present in any state — they mock as needed.
    """
    return "c6bf7f6f28fe3bf7a8f6d4fed5bdf3f850239141"


@pytest.fixture
def unknown_hash():
    """A well-formed but never-used 40-char hash."""
    return "0000000000000000000000000000000000000000"


@pytest.fixture
def mock_ts(app, monkeypatch):
    """Mock TorrServer helpers. Returns a control object you can set state on.

    Usage:
        def test_x(client, mock_ts):
            mock_ts.set_torrent("c6bf7f...", {"hash": "c6bf7f...", "file_stats": [...]})
            r = client.get("/api/files/c6bf7f...")
    """

    class TSMock:
        def __init__(self):
            self.torrents = {}  # hash -> torrent record
            self.probe_ok = True
            self.viewed = {}    # hash -> [file_index]

        def set_torrent(self, h, record):
            self.torrents[h.lower()] = record

        def set_probe_ok(self, v):
            self.probe_ok = v

    state = TSMock()

    def fake_ts_post(path, payload=None):
        payload = payload or {}
        if path == "/torrents":
            action = payload.get("action")
            h = (payload.get("hash") or "").lower()
            if action == "get":
                return state.torrents.get(h)
            if action == "rem":
                state.torrents.pop(h, None)
                return {"ok": True}
            if action == "list":
                return list(state.torrents.values())
            if action == "add":
                # Real TorrServer extracts the hash from the magnet/URL link;
                # mirror that here so /api/add tests get a non-empty hash.
                link = (payload.get("link") or "").lower()
                import re as _re
                m = _re.search(r"(?:btih:|^)([0-9a-f]{40,64})", link)
                added_hash = m.group(1) if m else ""
                if added_hash:
                    state.torrents[added_hash] = {"hash": added_hash, "title": payload.get("title", "")}
                return {"hash": added_hash, "ok": True}
        return None

    def fake_ts_probe():
        if state.probe_ok:
            return {"ok": True, "torrent_count": len(state.torrents), "error": ""}
        return {"ok": False, "torrent_count": 0, "error": "probe failed"}

    def fake_get_viewed(h):
        return [{"file_index": i} for i in state.viewed.get(h.lower(), [])]

    def fake_set_viewed(h, idx):
        state.viewed.setdefault(h.lower(), []).append(idx)
        return True

    monkeypatch.setattr(app, "ts_post", fake_ts_post)
    monkeypatch.setattr(app, "ts_probe", fake_ts_probe)
    monkeypatch.setattr(app, "get_viewed", fake_get_viewed)
    monkeypatch.setattr(app, "set_viewed", fake_set_viewed)
    return state


# ─── Live wrapper fixtures (integration / e2e) ───────────────────────────────


@pytest.fixture(scope="session")
def live_base():
    """Base URL of the live wrapper. Default prod; override via env."""
    return os.getenv("TORRSTREAM_BASE", "https://tv.trikiman.shop")


@pytest.fixture(scope="session")
def live_session(live_base):
    """Requests session that hits the live wrapper. Skip if unreachable."""
    s = requests.Session()
    s.headers.update({"User-Agent": "torrstream-tests/1.0"})
    try:
        r = s.get(f"{live_base}/api/status", timeout=5)
        if r.status_code != 200:
            pytest.skip(f"live wrapper at {live_base} returned {r.status_code}")
    except Exception as e:
        pytest.skip(f"live wrapper at {live_base} unreachable: {e}")
    return s


@pytest.fixture
def live_known_hash(live_session, live_base):
    """A hash that's actually present on the live wrapper. Skip if library is empty."""
    r = live_session.get(f"{live_base}/api/torrents", timeout=10)
    items = r.json().get("items", [])
    if not items:
        pytest.skip("live wrapper has empty library; can't run hash-dependent tests")
    return items[0]["hash"]
