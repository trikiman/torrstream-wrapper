#!/usr/bin/env bash
# Simplify ts.trikiman.shop block (drop custom log that causes permission issue)
# then clean restart so reload queue is flushed.
set -eu

sudo tee /etc/caddy/Caddyfile >/dev/null <<'EOF'
tv.trikiman.shop {
	reverse_proxy 127.0.0.1:5000
	encode gzip
	log {
		output file /var/log/torrstream/caddy-access.log
	}
}

ts.trikiman.shop {
	reverse_proxy 127.0.0.1:8090
	encode gzip
}
EOF

echo "=== validate ==="
sudo caddy validate --config /etc/caddy/Caddyfile

echo "=== restart (clean) ==="
sudo systemctl restart caddy

sleep 4
echo "=== status ==="
sudo systemctl is-active caddy
sudo ss -tlnp 2>/dev/null | grep -E ':443|:80' | head -5
