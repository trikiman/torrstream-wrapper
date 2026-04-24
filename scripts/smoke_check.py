#!/usr/bin/env python3
"""Lightweight smoke check for the local TorrStream wrapper."""

from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:5000"


def fetch(path: str):
    url = f"{BASE_URL}{path}"
    req = Request(url, headers={"User-Agent": "TorrStreamSmoke/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return True, resp.status, body
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return False, e.code, body
    except URLError as e:
        return False, 0, str(e)


def check(label: str, path: str, expect_json: bool = False):
    ok, status, body = fetch(path)
    state = "PASS" if ok else "FAIL"
    print(f"[{state}] {label} -> {path} ({status})")
    if expect_json and body:
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, ensure_ascii=False, indent=2)[:400])
        except json.JSONDecodeError:
            print(body[:200])
    elif not ok:
        print(body[:200])
    return ok


def main():
    results = [
        check("Shell", "/"),
        check("Manifest", "/manifest.json"),
        check("Service Worker", "/sw.js"),
        check("Status", "/api/status", expect_json=True),
        check("Library", "/api/torrents", expect_json=True),
        check("Search", "/api/search?q=Project%20Hail%20Mary", expect_json=True),
    ]
    failed = sum(1 for r in results if not r)
    print(f"\nSummary: {len(results) - failed}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
