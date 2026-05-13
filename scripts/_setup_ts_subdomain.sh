#!/usr/bin/env bash
# Add ts.trikiman.shop as HTTPS reverse proxy to TorrServer on :8090.
# Caddy auto-issues Let's Encrypt cert. TorrServer's own BasicAuth stays in effect.
set -eu

BACKUP="/etc/caddy/Caddyfile.bak.$(date +%s)"
sudo cp /etc/caddy/Caddyfile "$BACKUP"
echo "backed up to $BACKUP"

# Append new site block if not already present
if sudo grep -q 'ts.trikiman.shop' /etc/caddy/Caddyfile; then
  echo "ts.trikiman.shop block already exists; leaving as-is"
else
  sudo tee -a /etc/caddy/Caddyfile >/dev/null <<'EOF'

ts.trikiman.shop {
  reverse_proxy 127.0.0.1:8090
  encode gzip
  log {
    output file /var/log/torrstream/caddy-access-ts.log
  }
}
EOF
  echo "appended ts.trikiman.shop block"
fi

echo "=== validating ==="
sudo caddy validate --config /etc/caddy/Caddyfile

echo "=== reloading ==="
sudo systemctl reload caddy

echo "=== status ==="
sudo systemctl is-active caddy
