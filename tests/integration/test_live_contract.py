"""Live wrapper smoke tests — read-only checks against tv.trikiman.shop.

These tests hit the actual deployed wrapper. They never mutate state and skip
cleanly if the wrapper is unreachable. Run with:

    pytest -m integration

Or against a different base:

    TORRSTREAM_BASE=http://localhost:5000 pytest -m integration

Each test asserts a v2.2 contract delivered by the API hygiene phase.
"""
import pytest


@pytest.mark.integration
class TestLiveContract:
    def test_unknown_hash_returns_404(self, live_session, live_base):
        # Plan 1.1: 404 for well-formed but unknown hash
        r = live_session.get(f"{live_base}/api/files/{'0' * 40}", timeout=10)
        assert r.status_code == 404
        assert r.json()["diagnostics"]["state"] == "not_found"

    def test_invalid_hash_returns_400(self, live_session, live_base):
        # Plan 1.1: 400 for malformed hash
        r = live_session.get(f"{live_base}/api/files/garbage", timeout=10)
        assert r.status_code == 400
        assert "invalid hash" in r.json()["error"]

    def test_unknown_position_returns_404(self, live_session, live_base):
        r = live_session.get(f"{live_base}/api/position/{'0' * 40}", timeout=10)
        assert r.status_code == 404

    def test_unknown_remove_returns_404(self, live_session, live_base):
        r = live_session.delete(f"{live_base}/api/remove/{'0' * 40}", timeout=10)
        assert r.status_code == 404

    def test_malformed_json_returns_400(self, live_session, live_base, live_known_hash):
        r = live_session.post(
            f"{live_base}/api/position/{live_known_hash}",
            data="not json{",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert r.status_code == 400
        assert "invalid JSON" in r.json()["error"]

    def test_static_lampa_sync_has_cors(self, live_session, live_base):
        r = live_session.get(f"{live_base}/static/lampa-sync.js", timeout=10)
        assert r.status_code == 200
        assert r.headers.get("Access-Control-Allow-Origin") == "*"
        assert "__torrstream_sync_loaded" in r.text

    def test_position_options_preflight(self, live_session, live_base, live_known_hash):
        r = live_session.options(
            f"{live_base}/api/position/{live_known_hash}",
            headers={
                "Origin": "https://lampa.mx",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
            timeout=10,
        )
        assert r.status_code == 204
        assert r.headers.get("Access-Control-Allow-Origin") == "*"

    def test_search_returns_results_or_empty(self, live_session, live_base):
        r = live_session.get(f"{live_base}/api/search?q=matrix", timeout=15)
        assert r.status_code == 200
        data = r.json()
        # Either provider responded (`Results` is a list) or it's down
        # (ok:false with empty Results). Both are valid; just no crash.
        assert isinstance(data["Results"], list)

    def test_torrents_list_has_diagnostics(self, live_session, live_base):
        r = live_session.get(f"{live_base}/api/torrents", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "diagnostics" in data
        assert "items" in data

    def test_stream_range_request_succeeds(self, live_session, live_base, live_known_hash):
        # Use the first file of the first torrent to fetch a small range.
        r = live_session.get(f"{live_base}/api/files/{live_known_hash}", timeout=10)
        files = r.json().get("file_stats", [])
        if not files:
            pytest.skip(f"torrent {live_known_hash} has no files yet (cold)")
        idx = files[0].get("id", 1)
        path = files[0]["path"].split("/")[-1]
        r = live_session.get(
            f"{live_base}/api/stream/{path}?hash={live_known_hash}&index={idx}",
            headers={"Range": "bytes=0-15"},
            timeout=15,
            stream=True,
        )
        assert r.status_code == 206
        assert "Content-Range" in r.headers
        # consume + close to free the connection without downloading whole file
        next(r.iter_content(chunk_size=16), None)
        r.close()
