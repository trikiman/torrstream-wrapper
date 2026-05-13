#!/usr/bin/env bash
# Open inbound BitTorrent peer port 22115 (TCP + UDP) on Ubuntu iptables.
# This unblocks peer connections so TorrServer can actually swarm, not just
# passively accept connections initiated outbound.
set -eu

PORT=22115

echo "=== before ==="
sudo iptables -L INPUT -n | grep -E "$PORT|REJECT" | head -5

# Add rules BEFORE the final REJECT (use insert at position just before reject)
# Find the line number of the REJECT rule and insert just above it
REJECT_LINE=$(sudo iptables -L INPUT -n --line-numbers | awk '/REJECT/ {print $1; exit}')
if [ -z "$REJECT_LINE" ]; then
  echo "no REJECT rule found, appending"
  sudo iptables -A INPUT -p tcp --dport $PORT -j ACCEPT
  sudo iptables -A INPUT -p udp --dport $PORT -j ACCEPT
else
  # Insert TCP and UDP accept rules above the REJECT line
  sudo iptables -I INPUT $REJECT_LINE -p tcp --dport $PORT -j ACCEPT
  sudo iptables -I INPUT $REJECT_LINE -p udp --dport $PORT -j ACCEPT
fi

echo
echo "=== after ==="
sudo iptables -L INPUT -n --line-numbers | grep -E "$PORT|REJECT"

echo
echo "=== persisting ==="
if command -v iptables-save >/dev/null; then
  if [ -d /etc/iptables ]; then
    sudo iptables-save | sudo tee /etc/iptables/rules.v4 >/dev/null
    echo "saved to /etc/iptables/rules.v4"
  else
    sudo iptables-save | sudo tee /etc/iptables.rules >/dev/null
    echo "saved to /etc/iptables.rules"
  fi
fi

echo
echo "=== verifying listener is open to world ==="
echo "(needs also Oracle Cloud Security List ingress rule for port 22115)"
