"""/api/position/<hash> contracts.

Covers GET / POST / OPTIONS preflight + all the v2.2 Plan 1.1 / 1.2 hardening:
- Hash format validation (400 on invalid).
- 404 on unknown hash GET when TorrServer says not-found.
- 200 with zeros on unknown-position-for-known-torrent (resume-on-play UX).
- POST: malformed JSON → 400; missing position → 400; non-numeric → 400.
- POST: valid round-trip writes positions.json and is readable via GET.
- Viewed sync threshold: position/duration > 0.95 triggers set_viewed.
- CORS preflight returns 204 with proper Access-Control-* headers.

Source: 2026-05-14 E2E audit Wave 1.4 + v2.2 Plan 1.1, 1.2.
"""
import pytest


@pytest.mark.smoke
class TestPositionGet:
    def test_get_unknown_hash_returns_404(self, client, mock_ts, unknown_hash):
        # No positions, no torrent → 404
        r = client.get(f"/api/position/{unknown_hash}")
        assert r.status_code == 404
        data = r.get_json()
        assert data["ok"] is False
        assert "unknown hash" in data["error"]

    def test_get_known_torrent_no_position_returns_200_zeros(self, client, mock_ts, known_hash):
        # Torrent IS in TS but no position recorded → resume-on-play returns zeros
        mock_ts.set_torrent(known_hash, {"hash": known_hash, "file_stats": []})
        r = client.get(f"/api/position/{known_hash}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert data["position"] == 0
        assert data["duration"] == 0

    def test_get_invalid_hash_returns_400(self, client, mock_ts):
        r = client.get("/api/position/notahash")
        assert r.status_code == 400
        assert r.get_json()["error"] == "invalid hash"


@pytest.mark.smoke
class TestPositionPost:
    def test_post_malformed_json_returns_400(self, client, mock_ts, known_hash):
        r = client.post(
            f"/api/position/{known_hash}",
            data="not json{",
            content_type="application/json",
        )
        assert r.status_code == 400
        data = r.get_json()
        assert data["ok"] is False
        assert "invalid JSON" in data["error"]

    def test_post_missing_position_returns_400(self, client, mock_ts, known_hash):
        r = client.post(
            f"/api/position/{known_hash}",
            json={},
        )
        assert r.status_code == 400
        assert "missing position" in r.get_json()["error"]

    def test_post_non_numeric_position_returns_400(self, client, mock_ts, known_hash):
        r = client.post(
            f"/api/position/{known_hash}",
            json={"position": "not a number"},
        )
        assert r.status_code == 400
        assert "invalid" in r.get_json()["error"].lower()

    def test_post_invalid_hash_returns_400(self, client, mock_ts):
        r = client.post("/api/position/garbage", json={"position": 10})
        assert r.status_code == 400

    def test_post_round_trip(self, client, mock_ts, known_hash):
        # Mark torrent as known so subsequent GET doesn't 404
        mock_ts.set_torrent(known_hash, {"hash": known_hash, "file_stats": []})
        r = client.post(
            f"/api/position/{known_hash}",
            json={"position": 60, "duration": 300, "file_index": 1},
        )
        assert r.status_code == 200
        assert r.get_json()["ok"] is True

        # Read it back
        r = client.get(f"/api/position/{known_hash}?file_index=1")
        assert r.status_code == 200
        data = r.get_json()
        assert data["position"] == 60
        assert data["duration"] == 300
        assert data["last_file_index"] == 1

    def test_post_viewed_sync_threshold(self, client, mock_ts, known_hash):
        # Mark torrent known so the route doesn't 404
        mock_ts.set_torrent(known_hash, {"hash": known_hash, "file_stats": []})

        # Below threshold (50%) — no viewed sync attempt
        r = client.post(
            f"/api/position/{known_hash}",
            json={"position": 150, "duration": 300, "file_index": 1},
        )
        assert r.get_json()["viewed_sync_attempted"] is False

        # Above threshold (96%) — viewed sync attempted
        r = client.post(
            f"/api/position/{known_hash}",
            json={"position": 288, "duration": 300, "file_index": 1},
        )
        body = r.get_json()
        assert body["viewed_sync_attempted"] is True
        assert body["viewed_synced"] is True


@pytest.mark.smoke
@pytest.mark.cors
class TestPositionCors:
    def test_options_preflight_returns_204(self, client, known_hash):
        r = client.options(
            f"/api/position/{known_hash}",
            headers={
                "Origin": "https://lampa.mx",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert r.status_code == 204
        assert r.headers.get("Access-Control-Allow-Origin") == "*"
        assert "POST" in r.headers.get("Access-Control-Allow-Methods", "")
        assert "Content-Type" in r.headers.get("Access-Control-Allow-Headers", "")

    def test_get_includes_cors_origin(self, client, mock_ts, known_hash):
        mock_ts.set_torrent(known_hash, {"hash": known_hash, "file_stats": []})
        r = client.get(f"/api/position/{known_hash}")
        assert r.headers.get("Access-Control-Allow-Origin") == "*"

    def test_post_400_still_has_cors(self, client, mock_ts, known_hash):
        # Important: error responses must still carry CORS so the browser
        # exposes the body to JS and the Lampa plugin can read the error.
        r = client.post(
            f"/api/position/{known_hash}",
            data="not json{",
            content_type="application/json",
            headers={"Origin": "https://lampa.mx"},
        )
        assert r.status_code == 400
        assert r.headers.get("Access-Control-Allow-Origin") == "*"
