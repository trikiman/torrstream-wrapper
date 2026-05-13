#!/usr/bin/env bash
# Simulate Lampa player streaming pattern: byte-range requests with idle gaps
# Tests that TorrentDisconnectTimeout bump (30 -> 300) keeps torrent alive
# between ranges the way Lampa's buffering behaves.

set -eu

AUTH="torrstream:m6wkt8jhrsb4x5qiz3u2ngyo"
HASH="dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
URL="http://127.0.0.1:8090/stream/Big%20Buck%20Bunny.mp4?link=${HASH}&index=2&play"

log() { echo "[$(date +%H:%M:%S)] $*"; }

check_alive() {
  local seeders
  seeders=$(curl -s -u "$AUTH" -X POST http://127.0.0.1:8090/torrents \
    -H 'Content-Type: application/json' \
    -d "{\"action\":\"get\",\"hash\":\"$HASH\"}" \
    | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("stat_string","?"),"|seeders=",d.get("connected_seeders"))')
  log "  state: $seeders"
}

log "=== Lampa streaming simulation ==="
log "Baseline"
check_alive

for i in 1 2 3; do
  log "Cycle $i: 4MB head range (like initial play)"
  bytes=$(curl -s -u "$AUTH" -r 0-4194303 -o /dev/null -w '%{size_download}' "$URL")
  log "  got ${bytes} bytes"
  check_alive

  log "Cycle $i: idle 45s (simulating buffer pause; old 30s timeout would kill here)"
  sleep 45
  check_alive

  log "Cycle $i: seek range (like user seeked / re-buffer)"
  offset=$((i * 20000000))
  end=$((offset + 1048575))
  bytes=$(curl -s -u "$AUTH" -r "${offset}-${end}" -o /dev/null -w '%{size_download}' "$URL")
  log "  got ${bytes} bytes at offset ${offset}"
  check_alive
done

log "=== Final check: torrent survived ==="
check_alive
log "=== Done ==="
