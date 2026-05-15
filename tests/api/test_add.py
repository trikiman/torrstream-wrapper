"""/api/add contract tests.

Source: 2026-05-14 E2E audit Wave 1.4.
"""
import pytest


@pytest.mark.smoke
class TestAdd:
    def test_empty_body_returns_no_link(self, client, mock_ts):
        r = client.post("/api/add", json={})
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is False
        assert data["error"] == "no link"

    def test_invalid_link_returns_invalid(self, client, mock_ts):
        r = client.post("/api/add", json={"link": "not-a-magnet"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is False
        assert "invalid" in data["error"].lower()

    def test_valid_magnet_returns_hash(self, client, mock_ts):
        magnet = "magnet:?xt=urn:btih:" + "a" * 40
        r = client.post("/api/add", json={"link": magnet})
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert data["hash"] == "a" * 40

    def test_bare_hash_accepted(self, client, mock_ts):
        h = "b" * 40
        r = client.post("/api/add", json={"link": h})
        assert r.status_code == 200
        assert r.get_json()["ok"] is True
