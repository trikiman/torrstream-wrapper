#!/usr/bin/env bash
# Benchmark Prophet download throughput with port 22115 now open.
# Runs an active stream in background, samples torrserver stats every 5s for 60s.
set -eu

AUTH="torrstream:m6wkt8jhrsb4x5qiz3u2ngyo"
HASH="7848e598e5b8c1a2cd50f4432d9755377b12d76d"
BASE="http://127.0.0.1:8090"

get_stats() {
  curl -s -u "$AUTH" -X POST "$BASE/torrents" \
    -H 'Content-Type: application/json' \
    -d "{\"action\":\"get\",\"hash\":\"$HASH\"}"
}

# First, list files so we pick the largest (main movie)
FILE_INFO=$(get_stats | python3 -c 'import sys,json; d=json.load(sys.stdin); fs=d.get("file_stats") or []
if not fs:
  print("0 0")
else:
  biggest = max(fs, key=lambda f: f["length"])
  print(biggest["id"], biggest["length"], biggest["path"])' 2>/dev/null || echo "0 0")
echo "file_info=$FILE_INFO"

# If no file list yet, warmup with a byte-0 probe
if [[ "$FILE_INFO" == "0 0"* ]]; then
  echo "warming up torrent..."
  curl -s -u "$AUTH" -r 0-0 -o /dev/null "$BASE/stream/?link=$HASH&index=1&play"
  sleep 5
  FILE_INFO=$(get_stats | python3 -c 'import sys,json; d=json.load(sys.stdin); fs=d.get("file_stats") or []
if not fs:
  print("0 0")
else:
  biggest = max(fs, key=lambda f: f["length"])
  print(biggest["id"], biggest["length"], biggest["path"])' 2>/dev/null || echo "0 0")
  echo "after warmup: $FILE_INFO"
fi

FILE_IDX=$(echo "$FILE_INFO" | awk '{print $1}')
FILE_SIZE=$(echo "$FILE_INFO" | awk '{print $2}')
FILE_PATH=$(echo "$FILE_INFO" | cut -d' ' -f3-)

if [[ "$FILE_IDX" == "0" ]]; then
  echo "ERROR: could not resolve file index"
  exit 1
fi

echo
echo "=== Streaming file idx=$FILE_IDX size=$((FILE_SIZE/1024/1024))MB path=$FILE_PATH ==="
STREAM_URL="$BASE/stream/file?link=$HASH&index=$FILE_IDX&play"

# Fire a streaming request for 50MB in background; this forces pieces to be fetched
(curl -s -u "$AUTH" -r 0-52428799 -o /dev/null "$STREAM_URL" &) 

echo "=== sampling download_speed every 5s for 50s ==="
for i in 1 2 3 4 5 6 7 8 9 10; do
  sleep 5
  get_stats | python3 -c "
import sys, json
d = json.load(sys.stdin)
s = d.get('download_speed') or 0
p = d.get('connected_seeders') or 0
a = d.get('active_peers') or 0
ls = d.get('loaded_size') or 0
print(f't+{$i*5}s: peers={p}/{a} dl={s/1024/1024:.2f}MB/s ({s*8/1000/1000:.1f}Mbit/s) loaded={ls/1024/1024:.1f}MB')
"
done

echo
echo "=== final state ==="
get_stats | python3 -c 'import sys,json; d=json.load(sys.stdin); print({k:d.get(k) for k in ["stat_string","connected_seeders","active_peers","total_peers","bytes_read","loaded_size","preloaded_bytes"]})'
