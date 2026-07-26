#!/usr/bin/env bash
# Restore ReaderReadAHead=95 + PreloadCache=50 (accidentally zeroed by a prior
# partial set call) and keep TorrentDisconnectTimeout=300.
set -eu
AUTH="${TORRSERVER_USER:?set TORRSERVER_USER}:${TORRSERVER_PASS:?set TORRSERVER_PASS}"

# NOTE: PeersListenPort MUST stay 22115 (the firewalled-open port). Setting it
# to 0 caused the v2.5 peer-port regression: TorrServer picked a random port on
# each restart, which the firewall blocked, killing inbound peer connections.
curl -s -u "$AUTH" -X POST http://127.0.0.1:8090/settings \
  -H 'Content-Type: application/json' \
  -d '{"action":"set","sets":{
    "CacheSize":67108864,
    "ReaderReadAHead":95,
    "PreloadCache":50,
    "UseDisk":false,
    "TorrentsSavePath":"",
    "RemoveCacheOnDrop":false,
    "ForceEncrypt":false,
    "RetrackersMode":0,
    "TorrentDisconnectTimeout":300,
    "EnableDebug":false,
    "EnableDLNA":false,
    "FriendlyName":"",
    "EnableRutorSearch":false,
    "EnableTorznabSearch":false,
    "EnableIPv6":false,
    "DisableTCP":false,
    "DisableUTP":false,
    "DisableUPNP":false,
    "DisableDHT":false,
    "DisablePEX":false,
    "DisableUpload":false,
    "DownloadRateLimit":0,
    "UploadRateLimit":0,
    "ConnectionsLimit":25,
    "PeersListenPort":22115,
    "SslPort":0,
    "SslCert":"",
    "SslKey":"",
    "ResponsiveMode":false,
    "ShowFSActiveTorr":false,
    "StoreSettingsInJson":false,
    "StoreViewedInJson":false,
    "EnableProxy":false
  }}' >/dev/null

echo "=== verify after restore ==="
curl -s -u "$AUTH" -X POST http://127.0.0.1:8090/settings \
  -H 'Content-Type: application/json' \
  -d '{"action":"get"}' \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(json.dumps({k:d[k] for k in ["TorrentDisconnectTimeout","ReaderReadAHead","PreloadCache","CacheSize","ConnectionsLimit","DisableTCP","DisableUTP","DisableDHT"]},indent=2))'
