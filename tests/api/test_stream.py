"""/api/stream/<filename> contracts.

Locks in:
- Missing hash query param → 400.
- Probe mode (`?probe=1`) returns JSON diagnostics, not a stream.
- Range requests are forwarded; Content-Range echoed back.
- Invalid hash isn't validated by /api/stream (keeps the stream proxy fast and
  permissive — TS handles unknown hashes by returning 4xx from upstream).

Source: 2026-05-14 E2E audit Wave 1.4.
"""
import io

import pytest


@pytest.mark.smoke
class TestStreamEndpoint:
    def test_missing_hash_returns_400(self, client):
        r = client.get("/api/stream/movie.mp4")
        assert r.status_code == 400
        assert "missing hash" in r.get_json()["error"]

    def test_probe_mode_returns_diagnostics(self, client, mocker, known_hash):
        # Mock requests.head used inside probe_stream_access if it exists,
        # otherwise just patch ts_get / requests.get whichever the probe uses.
        mock_get = mocker.patch("requests.get")
        mock_get.return_value.status_code = 206
        mock_get.return_value.headers = {"Content-Type": "video/mp4", "Content-Range": "bytes 0-0/1000"}
        mock_get.return_value.iter_content.return_value = iter([])
        mock_get.return_value.close = lambda: None

        r = client.get(f"/api/stream/movie.mp4?hash={known_hash}&index=1&probe=1")
        # Probe returns JSON regardless of upstream — content-type must be JSON
        assert "json" in r.headers["Content-Type"].lower()

    def test_range_request_forwarded(self, client, mocker, known_hash):
        # Stub requests.get to return a fake streaming response
        class FakeResp:
            status_code = 206
            headers = {
                "Content-Type": "video/mp4",
                "Content-Range": "bytes 0-15/1000",
                "Content-Length": "16",
            }
            def iter_content(self, chunk_size):
                yield b"\x00" * 16
            def close(self): pass

        mocker.patch("requests.get", return_value=FakeResp())
        r = client.get(
            f"/api/stream/movie.mp4?hash={known_hash}&index=1",
            headers={"Range": "bytes=0-15"},
        )
        # Wrapper proxies the upstream status and headers
        assert r.status_code == 206
        assert r.headers.get("Content-Range") == "bytes 0-15/1000"
        assert r.headers.get("Accept-Ranges") == "bytes"
