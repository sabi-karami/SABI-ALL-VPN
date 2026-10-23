#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
mkdir -p "$ROOT"/{clients,build,logs} /etc/allvpn/cert
apt-get update -qq
printf '%s\n' 'iptables-persistent iptables-persistent/autosave_v4 boolean true' 'iptables-persistent iptables-persistent/autosave_v6 boolean true' | debconf-set-selections
apt-get install -y -qq curl ca-certificates wget unzip jq openssl uuid-runtime iptables iptables-persistent wireguard wireguard-tools build-essential git cmake pkgconf libncurses-dev libreadline-dev libsodium-dev libssl-dev zlib1g-dev dnsutils python3 python3-venv certbot python3-certbot-dns-cloudflare >/dev/null
cat >/etc/sysctl.d/99-sabi-allvpn.conf <<'EOF'
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
net.core.rmem_max=16777216
net.core.wmem_max=16777216
EOF
sysctl --system >/dev/null
if [[ ! -f /swapfile && $(free -m | awk '/Swap:/{print $2}') == 0 ]]; then
 fallocate -l 2G /swapfile; chmod 600 /swapfile; mkswap /swapfile >/dev/null; swapon /swapfile
 echo '/swapfile none swap sw 0 0' >>/etc/fstab
fi
iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport 80 -j ACCEPT
python3 "$REPO/scripts/dns.py"
# DNS-01 supports orange-cloud names and avoids stopping services for renewals.
if [[ "$DNS_MODE" == cloudflare ]]; then
 python3 - <<'PY'
from pathlib import Path
p=Path('/etc/sabi-allvpn');f=p/'certbot-cloudflare.ini';f.write_text('dns_cloudflare_api_token = '+(p/'cloudflare.token').read_text().strip()+'\n');f.chmod(0o600)
PY
 certbot certonly --dns-cloudflare --dns-cloudflare-credentials /etc/sabi-allvpn/certbot-cloudflare.ini --dns-cloudflare-propagation-seconds 60 --non-interactive --agree-tos --register-unsafely-without-email --cert-name allvpn --key-type rsa --rsa-key-size 2048 -d "$DOMAIN" -d "$CDN"
else
 # Both names must be DNS-only for standalone HTTP-01; proxy CDN only after certificates are issued.
 certbot certonly --standalone --non-interactive --agree-tos --register-unsafely-without-email --cert-name allvpn --key-type rsa --rsa-key-size 2048 -d "$DOMAIN" -d "$CDN"
fi
install -m644 /etc/letsencrypt/live/allvpn/fullchain.pem /etc/allvpn/cert/fullchain.pem
install -m600 /etc/letsencrypt/live/allvpn/privkey.pem /etc/allvpn/cert/privkey.pem
python3 "$REPO/scripts/download.py"
