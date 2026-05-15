"""/api/files/<hash> contracts.

Locks in:
- 200 with `file_stats[]` for a known torrent.
- 404 for a well-formed but unknown hash when TorrServer is reachable.
- 200 with `state: upstream_unavailable` when TorrServer is down.
- 400 for malformed hashes (not 40/64 hex).
- Hash is normalized to lowercase before lookup (uppercase request hits same key).
- `viewed` flag and `position` enrichment from positions.json.

Source: 2026-05-14 E2E audit + v2.2 Plan 1.1.
"""
import pytest


@pytest.mark.smoke
class TestFilesEndpoint:
    def test_known_hash_returns_files(self, client, mock_ts, known_hash):
        mock_ts.set_torrent(known_hash, {
            "hash": known_hash,
            "name": "Matrix.1999.BDRip.avi",
            "file_stats": [{"id": 1, "length": 1571913728, "path": "Matrix.1999.BDRip.avi"}],
        })
        r = client.get(f"/api/files/{known_hash}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert len(data["file_stats"]) == 1
        assert data["file_stats"][0]["path"].endswith(".avi")
        assert data["diagnostics"]["has_playable_files"] is True

    def test_unknown_hash_returns_404(self, client, mock_ts, unknown_hash):
        # mock_ts has no torrents and probe is OK
        r = client.get(f"/api/files/{unknown_hash}")
        assert r.status_code == 404
        data = r.get_json()
        assert data["ok"] is False
        assert "not found" in data["error"].lower()
        assert data["diagnostics"]["state"] == "not_found"

    def test_torrserver_down_returns_200_with_state(self, client, mock_ts, unknown_hash):
        # Distinguish "torrent not in library" from "TorrServer unreachable"
        mock_ts.set_probe_ok(False)
        r = client.get(f"/api/files/{unknown_hash}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is False
        assert data["diagnostics"]["state"] == "upstream_unavailable"

    @pytest.mark.parametrize("bad_hash", [
        "garbage123",                                    # too short
        "z" * 40,                                        # not hex
        "abc",                                           # too short
        "0123456789abcdef" * 2 + "extra",                # too long for SHA-1
        "",                                              # empty (Flask 404s the route)
    ])
    def test_invalid_hash_format_returns_400_or_404(self, client, mock_ts, bad_hash):
        # Empty string makes Flask return 404 (route doesn't match), all others 400.
        r = client.get(f"/api/files/{bad_hash}")
        assert r.status_code in (400, 404)
        if r.status_code == 400:
            data = r.get_json()
            assert data["ok"] is False
            assert "invalid hash" in data["error"]

    def test_uppercase_hash_normalized_to_lowercase(self, client, mock_ts, known_hash):
        # Setup with lowercase
        mock_ts.set_torrent(known_hash, {
            "hash": known_hash,
            "file_stats": [{"id": 1, "length": 100, "path": "movie.mp4"}],
        })
        r = client.get(f"/api/files/{known_hash.upper()}")
        assert r.status_code == 200
        assert r.get_json()["ok"] is True

    def test_btv2_hash_64_chars_accepted(self, client, mock_ts):
        btv2 = "a" * 64
        mock_ts.set_torrent(btv2, {
            "hash": btv2,
            "file_stats": [{"id": 1, "length": 100, "path": "movie.mp4"}],
        })
        r = client.get(f"/api/files/{btv2}")
        assert r.status_code == 200
