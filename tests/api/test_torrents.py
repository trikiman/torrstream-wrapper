"""/api/torrents and /api/status contracts.

Locks in the response shape for the library list and the diagnostic status.
Frontend's Continue Watching + library grid both read /api/torrents — its
shape changes are user-visible.

Source: 2026-05-14 E2E audit Wave 1.2.
"""
import pytest


@pytest.mark.smoke
class TestTorrentsEndpoint:
    def test_returns_diagnostics_and_items(self, client, mock_ts):
        mock_ts.set_torrent("a" * 40, {
            "hash": "a" * 40,
            "title": "Test Movie",
            "torrent_size": 1000000,
            "stat": 3,
            "stat_string": "Torrent working",
        })
        r = client.get("/api/torrents")
        assert r.status_code == 200
        data = r.get_json()
        assert "diagnostics" in data
        assert "items" in data
        assert data["diagnostics"]["ok"] is True
        assert data["diagnostics"]["state"] == "ready"
        assert data["diagnostics"]["torrent_count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test Movie"

    def test_empty_library_returns_empty_items(self, client, mock_ts):
        r = client.get("/api/torrents")
        assert r.status_code == 200
        data = r.get_json()
        assert data["items"] == []
        assert data["diagnostics"]["torrent_count"] == 0

    def test_torrserver_down_returns_diagnostic_state(self, client, mock_ts):
        mock_ts.set_probe_ok(False)
        r = client.get("/api/torrents")
        assert r.status_code == 200
        data = r.get_json()
        # state should reflect upstream issue, not crash
        assert data["diagnostics"]["ok"] is False or data["diagnostics"]["state"] != "ready"


@pytest.mark.smoke
class TestStatusEndpoint:
    def test_status_returns_config_block(self, client, mock_ts):
        r = client.get("/api/status")
        assert r.status_code == 200
        data = r.get_json()
        assert "search" in data
        assert "torrserver" in data
        assert "wrapper" in data
        assert data["wrapper"]["root"] == "/"
        assert "url" in data["torrserver"]
        # Don't leak credentials, but auth_configured flag is fine
        assert "auth_configured" in data["wrapper"]
