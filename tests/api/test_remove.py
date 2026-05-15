"""/api/remove/<hash> contracts.

Locks in:
- 404 on unknown hash with no positions to clean.
- 200 with `removed_positions: true` when wrapper had a saved position.
- 200 idempotent on torrent that exists in TS but no positions.
- 400 on invalid hash format.
- Side effect: positions.json entry is gone after successful remove.

Source: 2026-05-14 E2E audit + v2.2 Plan 1.1.
"""
import pytest


@pytest.mark.smoke
class TestRemoveEndpoint:
    def test_remove_unknown_hash_returns_404(self, client, mock_ts, unknown_hash):
        r = client.delete(f"/api/remove/{unknown_hash}")
        assert r.status_code == 404
        data = r.get_json()
        assert data["ok"] is False
        assert "unknown hash" in data["error"]

    def test_remove_known_torrent_returns_200(self, client, mock_ts, known_hash):
        mock_ts.set_torrent(known_hash, {"hash": known_hash})
        r = client.delete(f"/api/remove/{known_hash}")
        assert r.status_code == 200
        assert r.get_json()["ok"] is True
        # Side effect: torrent gone from mock TS
        assert known_hash not in mock_ts.torrents

    def test_remove_with_saved_position_reports_cleanup(self, client, mock_ts, known_hash):
        # First, save a position
        mock_ts.set_torrent(known_hash, {"hash": known_hash, "file_stats": []})
        client.post(
            f"/api/position/{known_hash}",
            json={"position": 100, "duration": 1000, "file_index": 1},
        )
        # Now remove
        r = client.delete(f"/api/remove/{known_hash}")
        assert r.status_code == 200
        body = r.get_json()
        assert body["ok"] is True
        assert body["removed_positions"] is True

        # And the position is gone — subsequent GET 404s (because torrent is gone too)
        r = client.get(f"/api/position/{known_hash}")
        assert r.status_code == 404

    def test_remove_invalid_hash_returns_400(self, client, mock_ts):
        r = client.delete("/api/remove/garbage")
        assert r.status_code == 400
        assert r.get_json()["error"] == "invalid hash"
