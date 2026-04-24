#!/usr/bin/env python3
"""TorrStream — Flask backend for cross-device torrent streaming with sync."""

import json
import logging
import os
import re
import time
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, redirect, request, send_from_directory, stream_with_context

app = Flask(__name__, static_folder="static", template_folder="templates")
app.logger.setLevel(logging.INFO)

# ─── Config ──────────────────────────────────────────────────────────────────
TORRSERVER = os.getenv("TORRSERVER_URL", "http://127.0.0.1:8090")
TORRSERVER_USER = os.getenv("TORRSERVER_USER", "")
TORRSERVER_PASS = os.getenv("TORRSERVER_PASS", "")
TORRSERVER_AUTH = (TORRSERVER_USER, TORRSERVER_PASS) if (TORRSERVER_USER or TORRSERVER_PASS) else None
JACRED_URL = os.getenv("JACRED_URL", "https://jacred.xyz")
JACRED_KEY = os.getenv("JACRED_KEY", "")
POSITIONS_FILE = Path(__file__).parent / "positions.json"

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".m4v", ".mov", ".wmv", ".ts", ".webm"}


# ─── Positions DB (file-based) ───────────────────────────────────────────────
def load_positions():
    """Load positions from JSON file. Schema:
    {
        "hash": {
            "files": {
                "1": {"position": 1234, "duration": 5000, "updated": 1711000000},
                "2": {"position": 0, "duration": 0, "updated": 0}
            },
            "last_file_index": 1,
            "updated": 1711000000
        }
    }
    """
    if POSITIONS_FILE.exists():
        try:
            data = json.loads(POSITIONS_FILE.read_text(encoding="utf-8"))
            # Migrate old flat format → new per-file format
            migrated = {}
            for h, v in data.items():
                if "files" in v:
                    migrated[h] = v
                else:
                    # Old format: {position, duration, updated}
                    migrated[h] = {
                        "files": {"1": {"position": v.get("position", 0), "duration": v.get("duration", 0), "updated": v.get("updated", 0)}},
                        "last_file_index": 1,
                        "updated": v.get("updated", 0),
                    }
            return migrated
        except (json.JSONDecodeError, AttributeError) as e:
            app.logger.warning("Failed to parse positions.json: %s", e)
            return {}
    return {}


def save_positions(data):
    tmp_file = POSITIONS_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_file.replace(POSITIONS_FILE)


# ─── TorrServer helpers ──────────────────────────────────────────────────────
def ts_post(path, payload=None):
    """POST to TorrServer with auth."""
    try:
        r = requests.post(f"{TORRSERVER}{path}", json=payload, auth=TORRSERVER_AUTH, timeout=10)
        r.raise_for_status()
        return r.json() if r.text.strip() else {}
    except Exception:
        return None


def ts_get(path, **kwargs):
    """GET from TorrServer with auth."""
    try:
        r = requests.get(f"{TORRSERVER}{path}", auth=TORRSERVER_AUTH, timeout=10, **kwargs)
        r.raise_for_status()
        return r
    except Exception:
        return None


def ts_probe():
    """Probe TorrServer reachability and basic library state."""
    try:
        r = requests.post(f"{TORRSERVER}/torrents", json={"action": "list"}, auth=TORRSERVER_AUTH, timeout=10)
        r.raise_for_status()
        data = r.json() if r.text.strip() else []
        torrent_count = len(data) if isinstance(data, list) else 0
        return {"ok": True, "torrent_count": torrent_count, "error": ""}
    except Exception as e:
        app.logger.warning("TorrServer probe failed: %s", e)
        return {"ok": False, "torrent_count": 0, "error": str(e)}


def normalize_torrent_link(raw_link):
    """Accept magnet links, HTTP URLs, and bare BTIH hashes."""
    link = (raw_link or "").strip()
    if not link:
        return None, "no link"

    if link.startswith("magnet:?"):
        return link, ""

    if link.startswith("http://") or link.startswith("https://"):
        return link, ""

    if re.fullmatch(r"[A-Fa-f0-9]{40}", link) or re.fullmatch(r"[A-Z2-7a-z2-7]{32}", link):
        return f"magnet:?xt=urn:btih:{link}", ""

    return None, "invalid link"


def get_viewed(torrent_hash):
    """Get list of viewed file indices from TorrServer."""
    result = ts_post("/viewed", {"action": "list", "hash": torrent_hash})
    if result and isinstance(result, list):
        return result
    return []


def set_viewed(torrent_hash, file_index):
    """Mark file as viewed in TorrServer (so Lampa sees it too)."""
    result = ts_post("/viewed", {"action": "set", "hash": torrent_hash, "file_index": file_index})
    return result is not None


def probe_stream_access(filename, torrent_hash, file_index):
    """Check whether a stream/download request would succeed without returning the media body."""
    ts_url = f"{TORRSERVER}/stream/{filename}?link={torrent_hash}&index={file_index}&play"
    try:
        r = requests.get(ts_url, auth=TORRSERVER_AUTH, headers={"Range": "bytes=0-0"}, stream=True, timeout=20)
        try:
            content_type = r.headers.get("Content-Type", "")
            ok = r.status_code < 400
            return {
                "ok": ok,
                "upstream_status": r.status_code,
                "content_type": content_type,
                "error": "" if ok else f"upstream returned {r.status_code}",
            }
        finally:
            r.close()
    except Exception as e:
        return {
            "ok": False,
            "upstream_status": 0,
            "content_type": "",
            "error": str(e),
        }


# ─── API Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static/icons", "icon-512.png", mimetype="image/png")


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.route("/api/torrents")
def list_torrents():
    """List all torrents with merged position + viewed data."""
    result = ts_post("/torrents", {"action": "list"})
    if result is None:
        probe = ts_probe()
        return jsonify({
            "ok": False,
            "items": [],
            "error": probe.get("error", "torrserver error"),
            "diagnostics": {
                **probe,
                "state": "upstream_unavailable",
            },
        })

    torrents = result if isinstance(result, list) else []
    positions = load_positions()

    enriched = []
    for t in torrents:
        h = t.get("hash", "")
        pos_data = positions.get(h, {})
        files_pos = pos_data.get("files", {})
        last_idx = pos_data.get("last_file_index", 0)

        # Get the last-played file's position for the "continue watching" bar
        last_pos = files_pos.get(str(last_idx), {})

        t["position"] = last_pos.get("position", 0)
        t["duration"] = last_pos.get("duration", 0)
        t["last_file_index"] = last_idx
        t["updated"] = pos_data.get("updated", 0)
        enriched.append(t)

    return jsonify({
        "ok": True,
        "items": enriched,
        "diagnostics": {
            "ok": True,
            "torrent_count": len(enriched),
            "state": "empty" if not enriched else "ready",
            "error": "",
        },
    })


@app.route("/api/status")
def status():
    """Lightweight diagnostics for the wrapper shell."""
    positions = load_positions()
    return jsonify({
        "torrserver": {
            "url": TORRSERVER,
            **ts_probe(),
        },
        "search": {
            "url": JACRED_URL,
            "api_key_configured": bool(JACRED_KEY),
        },
        "wrapper": {
            "root": "/",
            "manifest": "/manifest.json",
            "service_worker": "/sw.js",
            "auth_configured": bool(TORRSERVER_AUTH),
            "position_entries": len(positions),
        },
    })


@app.route("/api/files/<torrent_hash>")
def list_files(torrent_hash):
    """Get file list for a torrent, enriched with viewed + position data."""
    result = ts_post("/torrents", {"action": "get", "hash": torrent_hash})
    if result is None:
        probe = ts_probe()
        return jsonify({
            "ok": False,
            "error": probe.get("error") or "torrent not found or file lookup failed",
            "file_stats": [],
            "last_file_index": 0,
            "viewed_indices": [],
            "diagnostics": {
                **probe,
                "state": "upstream_unavailable" if not probe.get("ok") else "file_lookup_failed",
                "playable_count": 0,
                "total_file_count": 0,
                "has_playable_files": False,
            },
        })

    file_stats = result.get("file_stats") or []
    positions = load_positions()
    pos_data = positions.get(torrent_hash, {})
    files_pos = pos_data.get("files", {})

    # Get viewed data from TorrServer (what Lampa has marked)
    viewed_list = get_viewed(torrent_hash)
    viewed_indices = set()
    for v in viewed_list:
        if isinstance(v, dict):
            viewed_indices.add(v.get("file_index", 0))
        elif isinstance(v, int):
            viewed_indices.add(v)

    for fs in file_stats:
        idx = str(fs.get("id", 0))
        fp = files_pos.get(idx, {})
        fs["position"] = fp.get("position", 0)
        fs["file_duration"] = fp.get("duration", 0)
        fs["viewed"] = fs.get("id", 0) in viewed_indices

        # If no explicit viewed flag but position > 95% of duration, count as viewed
        if fp.get("duration", 0) > 0 and fp.get("position", 0) / fp["duration"] > 0.95:
            fs["viewed"] = True

    # Filter to video files only
    video_files = []
    for fs in file_stats:
        path = fs.get("path", "")
        ext = os.path.splitext(path)[1].lower()
        if ext in VIDEO_EXTENSIONS or not ext:
            video_files.append(fs)

    return jsonify({
        "ok": True,
        "file_stats": video_files,
        "last_file_index": pos_data.get("last_file_index", 0),
        "viewed_indices": list(viewed_indices),
        "diagnostics": {
            "ok": True,
            "state": "no_playable_files" if not video_files and file_stats else "ready",
            "playable_count": len(video_files),
            "total_file_count": len(file_stats),
            "has_playable_files": bool(video_files),
            "error": "",
        },
    })


@app.route("/api/position/<torrent_hash>", methods=["GET"])
def get_position(torrent_hash):
    """Get watch position for a torrent (with optional file_index query param)."""
    positions = load_positions()
    pos_data = positions.get(torrent_hash, {})
    file_index = request.args.get("file_index", str(pos_data.get("last_file_index", 1)))

    files_pos = pos_data.get("files", {})
    fp = files_pos.get(file_index, {})

    return jsonify({
        "ok": True,
        "position": fp.get("position", 0),
        "duration": fp.get("duration", 0),
        "last_file_index": pos_data.get("last_file_index", int(file_index)),
    })


@app.route("/api/position/<torrent_hash>", methods=["POST"])
def save_position(torrent_hash):
    """Save watch position. Body: {position, duration, file_index}."""
    body = request.get_json(force=True, silent=True) or {}
    try:
        pos = max(0, int(body.get("position", 0)))
        dur = max(0, int(body.get("duration", 0)))
        file_index_int = int(body.get("file_index", 1))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid position payload"}), 400

    if file_index_int < 1:
        return jsonify({"ok": False, "error": "invalid file_index"}), 400

    file_index = str(file_index_int)
    now = int(time.time())

    positions = load_positions()
    if torrent_hash not in positions:
        positions[torrent_hash] = {"files": {}, "last_file_index": file_index_int, "updated": now}

    entry = positions[torrent_hash]
    if "files" not in entry:
        entry["files"] = {}

    entry["files"][file_index] = {"position": pos, "duration": dur, "updated": now}
    entry["last_file_index"] = file_index_int
    entry["updated"] = now

    viewed_sync_attempted = dur > 0 and pos / dur > 0.95
    viewed_synced = False
    # Auto-mark as viewed in TorrServer when > 95% watched
    if viewed_sync_attempted:
        viewed_synced = set_viewed(torrent_hash, file_index_int)

    try:
        save_positions(positions)
    except Exception as e:
        app.logger.warning("Failed to save positions: %s", e)
        return jsonify({"ok": False, "error": "failed to save position"}), 500

    return jsonify({
        "ok": True,
        "viewed_sync_attempted": viewed_sync_attempted,
        "viewed_synced": viewed_synced,
    })


@app.route("/api/stream/<path:filename>")
def stream(filename):
    """Proxy video stream from TorrServer with range support."""
    torrent_hash = request.args.get("hash", "")
    file_index = request.args.get("index", "1")
    probe_mode = request.args.get("probe") == "1"

    if not torrent_hash:
        return jsonify({"ok": False, "error": "missing hash"}), 400

    ts_url = f"{TORRSERVER}/stream/{filename}?link={torrent_hash}&index={file_index}&play"
    headers = {}
    if "Range" in request.headers:
        headers["Range"] = request.headers["Range"]

    if probe_mode:
        diagnostics = probe_stream_access(filename, torrent_hash, file_index)
        status_code = 200 if diagnostics["ok"] else 502
        return jsonify(diagnostics), status_code

    try:
        r = requests.get(ts_url, auth=TORRSERVER_AUTH, headers=headers, stream=True, timeout=30)
        if r.status_code >= 400:
            payload = {
                "ok": False,
                "error": f"stream request failed with {r.status_code}",
                "upstream_status": r.status_code,
                "content_type": r.headers.get("Content-Type", ""),
            }
            r.close()
            return jsonify(payload), 502

        resp_headers = {
            "Content-Type": r.headers.get("Content-Type", "video/mp4"),
            "Accept-Ranges": "bytes",
        }
        if "Content-Range" in r.headers:
            resp_headers["Content-Range"] = r.headers["Content-Range"]
        if "Content-Length" in r.headers:
            resp_headers["Content-Length"] = r.headers["Content-Length"]

        def generate():
            for chunk in r.iter_content(chunk_size=1024 * 256):
                yield chunk

        return Response(
            stream_with_context(generate()),
            status=r.status_code,
            headers=resp_headers,
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "upstream_status": 0}), 502


@app.route("/api/download/<path:filename>")
def download_file(filename):
    """Stream video with Content-Disposition: attachment for download."""
    torrent_hash = request.args.get("hash", "")
    file_index = request.args.get("index", "1")
    probe_mode = request.args.get("probe") == "1"

    if not torrent_hash:
        return jsonify({"ok": False, "error": "missing hash"}), 400

    ts_url = f"{TORRSERVER}/stream/{filename}?link={torrent_hash}&index={file_index}&play"
    headers = {}
    if "Range" in request.headers:
        headers["Range"] = request.headers["Range"]

    if probe_mode:
        diagnostics = probe_stream_access(filename, torrent_hash, file_index)
        status_code = 200 if diagnostics["ok"] else 502
        return jsonify(diagnostics), status_code

    try:
        r = requests.get(ts_url, auth=TORRSERVER_AUTH, headers=headers, stream=True, timeout=30)
        if r.status_code >= 400:
            payload = {
                "ok": False,
                "error": f"download request failed with {r.status_code}",
                "upstream_status": r.status_code,
                "content_type": r.headers.get("Content-Type", ""),
            }
            r.close()
            return jsonify(payload), 502

        safe_filename = filename.split("/")[-1] if "/" in filename else filename
        resp_headers = {
            "Content-Type": r.headers.get("Content-Type", "application/octet-stream"),
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Accept-Ranges": "bytes",
        }
        if "Content-Range" in r.headers:
            resp_headers["Content-Range"] = r.headers["Content-Range"]
        if "Content-Length" in r.headers:
            resp_headers["Content-Length"] = r.headers["Content-Length"]

        def generate():
            for chunk in r.iter_content(chunk_size=1024 * 256):
                yield chunk

        return Response(
            stream_with_context(generate()),
            status=r.status_code,
            headers=resp_headers,
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "upstream_status": 0}), 502


@app.route("/api/add", methods=["POST"])
def add_torrent():
    """Add a torrent by magnet link or hash."""
    body = request.get_json(force=True, silent=True) or {}
    link, link_error = normalize_torrent_link(body.get("link", ""))
    title = body.get("title", "")
    poster = body.get("poster", "")

    if not link:
        return jsonify({"ok": False, "error": link_error or "no link"})

    payload = {"action": "add", "link": link, "title": title, "poster": poster, "save_to_db": True}
    result = ts_post("/torrents", payload)
    if result is not None:
        return jsonify({"ok": True, "hash": result.get("hash", ""), "normalized_link": link})
    return jsonify({"ok": False, "error": "torrserver add failed", "normalized_link": link})


@app.route("/api/remove/<torrent_hash>", methods=["DELETE"])
def remove_torrent(torrent_hash):
    """Remove a torrent."""
    result = ts_post("/torrents", {"action": "rem", "hash": torrent_hash})
    # Also clean up positions
    positions = load_positions()
    had_position = torrent_hash in positions
    positions.pop(torrent_hash, None)
    save_positions(positions)
    if result is None:
        return jsonify({"ok": False, "error": "torrserver remove failed", "removed_positions": had_position})
    return jsonify({"ok": True, "removed_positions": had_position})


@app.route("/api/search")
def search():
    """Search via jacred.xyz."""
    q = request.args.get("q", "")
    if not q:
        return jsonify({"ok": True, "Results": []})

    try:
        params = {"search": q, "apikey": JACRED_KEY} if JACRED_KEY else {"search": q}
        r = requests.get(f"{JACRED_URL}/api/v1.0/torrents", params=params, timeout=15)
        data = r.json()
        results = []
        if isinstance(data, dict):
            for key, item in data.items():
                for torrent in item.get("torrents", []):
                    results.append({
                        "Title": torrent.get("title", item.get("title", "")),
                        "Size": torrent.get("size", 0),
                        "Seeders": torrent.get("sid", 0),
                        "Tracker": torrent.get("tracker", ""),
                        "MagnetUri": torrent.get("magnet", ""),
                    })
        return jsonify({"ok": True, "Results": results})
    except Exception as e:
        app.logger.warning("Search provider failed: %s", e)
        return jsonify({"ok": False, "Results": [], "error": str(e)})


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Ensure directories exist
    (Path(__file__).parent / "templates").mkdir(exist_ok=True)
    (Path(__file__).parent / "static").mkdir(exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
