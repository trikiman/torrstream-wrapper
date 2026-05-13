#!/usr/bin/env bash
# Stress test: simulate realistic multi-client streaming load.
# - 4 concurrent workers pulling byte ranges across 3 torrents
# - each worker mixes head requests + seeks (mimics Lampa/player behavior)
# - 2 minute duration
# - samples: torrent stats, system cpu/mem/net, file descriptors
# Goal: identify where Oracle 1 CPU / 1 GB / 4 GB swap saturates.
set -eu

AUTH="torrstream:m6wkt8jhrsb4x5qiz3u2ngyo"
BASE="http://127.0.0.1:8090"
LOG=/tmp/stress.log
STATS=/tmp/stress.stats
SYS=/tmp/stress.sys
DURATION=${1:-120}  # seconds

rm -f "$LOG" "$STATS" "$SYS"
touch "$LOG" "$STATS" "$SYS"

# Pull hash + biggest file index for every warmed torrent
declare -A TORRENTS
TORRENTS[bbb]="dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
TORRENTS[prophet]="7848e598e5b8c1a2cd50f4432d9755377b12d76d"

# Warm Prophet and Pushkin (BBB already warm)
for name in prophet; do
  curl -s -u "$AUTH" -r 0-0 -o /dev/null "$BASE/stream/?link=${TORRENTS[$name]}&index=1&play" &
done
wait
sleep 4

# Worker function: random byte range request loop
worker() {
  local id=$1
  local hash=$2
  local file_size=$3
  local idx=$4
  local chunk=$((1024*1024))  # 1MB per request
  local end_time=$(($(date +%s) + DURATION))
  local requests=0 bytes_total=0
  while [ "$(date +%s)" -lt "$end_time" ]; do
    # Random offset within file (rounded to chunk boundary)
    local max_offset=$((file_size - chunk))
    local offset=$((RANDOM * RANDOM % max_offset))
    local t0_ms=$(date +%s%3N)
    local bytes=$(curl -s -u "$AUTH" -r "${offset}-$((offset+chunk-1))" \
      -o /dev/null -w '%{size_download}' \
      "$BASE/stream/file?link=$hash&index=$idx&play")
    local t1_ms=$(date +%s%3N)
    local elapsed=$((t1_ms - t0_ms))
    requests=$((requests+1))
    bytes_total=$((bytes_total+bytes))
    echo "worker=$id hash=${hash:0:12} offset=$offset bytes=$bytes ms=$elapsed" >> "$LOG"
    sleep 0.2
  done
  echo "worker=$id done requests=$requests bytes=$bytes_total" >> "$STATS"
}

# Sampler: captures system + torrent state every 5s
sampler() {
  local end_time=$(($(date +%s) + DURATION))
  while [ "$(date +%s)" -lt "$end_time" ]; do
    local cpu=$(top -bn1 | awk '/^%Cpu/{print 100-$8}')
    local mem=$(free -m | awk '/^Mem:/{printf "used=%dMB(%.0f%%) avail=%dMB", $3, $3*100/$2, $7}')
    local swap=$(free -m | awk '/^Swap:/{printf "used=%dMB", $3}')
    local conns=$(ss -ant state established | wc -l)
    local fds=$(ls /proc/$(pidof TorrServer)/fd 2>/dev/null | wc -l)
    local stats=""
    for name in "${!TORRENTS[@]}"; do
      local hash="${TORRENTS[$name]}"
      local d=$(curl -s -u "$AUTH" -X POST "$BASE/torrents" -H 'Content-Type: application/json' -d "{\"action\":\"get\",\"hash\":\"$hash\"}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"$name p={d.get('connected_seeders') or 0}/{d.get('active_peers') or 0} dl={(d.get('download_speed') or 0)*8/1000/1000:.1f}Mb ul={(d.get('upload_speed') or 0)*8/1000/1000:.1f}Mb\")" 2>/dev/null || echo "$name err")
      stats="$stats | $d"
    done
    printf 't=%d cpu=%.0f%% mem=%s swap=%s tcp=%d fds=%d%s\n' \
      "$(date +%s)" "$cpu" "$mem" "$swap" "$conns" "$fds" "$stats" >> "$SYS"
    sleep 5
  done
}

# Get file sizes
BBB_IDX=2; BBB_SIZE=276134947
PROPHET_IDX=1; PROPHET_SIZE=14611163992

echo "=== STRESS TEST START ==="
echo "duration=${DURATION}s workers=4 torrents=2"
echo

sampler &
SAMPLER_PID=$!

# Launch 4 workers: 2 on BBB, 2 on Prophet
worker 1 "${TORRENTS[bbb]}"     "$BBB_SIZE"     "$BBB_IDX" &
worker 2 "${TORRENTS[bbb]}"     "$BBB_SIZE"     "$BBB_IDX" &
worker 3 "${TORRENTS[prophet]}" "$PROPHET_SIZE" "$PROPHET_IDX" &
worker 4 "${TORRENTS[prophet]}" "$PROPHET_SIZE" "$PROPHET_IDX" &

wait
kill $SAMPLER_PID 2>/dev/null || true

echo
echo "=== PER-WORKER RESULTS ==="
cat "$STATS"

echo
echo "=== AGGREGATE LATENCY (ms) ==="
awk '{ print $NF }' "$LOG" | sed 's/ms=//' | python3 -c '
import sys, statistics
nums = [int(x) for x in sys.stdin if x.strip()]
if nums:
  print(f"count={len(nums)} min={min(nums)} p50={statistics.median(nums):.0f} p95={statistics.quantiles(nums, n=20)[18]:.0f} max={max(nums)} mean={statistics.mean(nums):.0f}")'

echo
echo "=== THROUGHPUT ==="
awk '/bytes=[0-9]+/ { sub(/bytes=/, "", $3); total += $3 } END { printf "total_bytes=%d (%.1f MB) over '${DURATION}'s => %.2f MB/s = %.1f Mbit/s\n", total, total/1024/1024, total/1024/1024/'${DURATION}', total*8/1000/1000/'${DURATION}' }' "$LOG"

echo
echo "=== SYSTEM SAMPLES (every 5s) ==="
cat "$SYS"

echo
echo "=== ERRORS (0-byte responses) ==="
grep -c 'bytes=0 ' "$LOG" || echo 0
