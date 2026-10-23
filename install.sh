#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
export REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == --help ]]; then echo 'sudo bash install.sh [--resume|--background|--noninteractive]'; exit; fi
[[ $EUID == 0 ]] || { echo 'Run on a fresh VPS as root (sudo).'; exit 1; }
[[ $(uname -m) == x86_64 ]] || { echo 'Only amd64 supported.'; exit 1; }
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || { echo 'Requires Ubuntu 24.04.'; exit 1; }
mkdir -p /var/lib/sabi-allvpn /etc/sabi-allvpn
exec 9>/var/lib/sabi-allvpn/install.lock
flock -n 9 || { echo 'Another install is running; use journalctl -u sabi-allvpn-install -f'; exit 1; }
if [[ ! -f /var/lib/sabi-allvpn/managed ]]; then
 # Dedicated host only; refuse to overwrite another deployment.
 for d in /root/allvpn /opt/allvpn-panel /opt/vpnserver /usr/local/go /etc/wireguard/wg0.conf /etc/sing-box/config.json /usr/local/etc/xray/config.json; do
  [[ ! -e "$d" ]] || { echo "Existing installation detected: $d. Refusing overwrite."; exit 1; }
 done
 python3 "$REPO/scripts/preflight.py"
fi
if [[ ! -f /etc/sabi-allvpn/install.env ]]; then
 python3 "$REPO/scripts/configure.py"
fi
touch /var/lib/sabi-allvpn/managed
if [[ "${1:-}" != --background ]]; then
 # Copy code to stable path so installation survives SSH disconnect and temporary bootstrap cleanup.
 mkdir -p /opt/sabi-allvpn
 if [[ "$REPO" != /opt/sabi-allvpn ]]; then cp -a "$REPO/." /opt/sabi-allvpn/; fi
 cat >/etc/systemd/system/sabi-allvpn-install.service <<'EOF'
[Unit]
Description=SABI ALLVPN resumable install
After=network-online.target
[Service]
Type=oneshot
ExecStart=/bin/bash /opt/sabi-allvpn/install.sh --background
TimeoutStartSec=infinity
StandardOutput=append:/var/log/sabi-allvpn-install.log
StandardError=append:/var/log/sabi-allvpn-install.log
UMask=0077
EOF
 touch /var/log/sabi-allvpn-install.log; chmod 600 /var/log/sabi-allvpn-install.log
 systemctl daemon-reload
 flock -u 9
 systemctl start --no-block sabi-allvpn-install
 echo 'Installation continues after SSH disconnect.'
 echo 'Progress: sudo tail -f /var/log/sabi-allvpn-install.log'
 echo 'Resume: sudo bash /opt/sabi-allvpn/install.sh --resume'
 echo 'Result: sudo cat /root/allvpn/panel-access.txt (keep private)'
 exit 0
fi
mkdir -p /var/lib/sabi-allvpn/done
trap 'printf "FAILED at line %s; inspect the root-only log and rerun --resume.\n" "$LINENO" >&2' ERR
for file in "$REPO"/modules/*.sh; do
 name=$(basename "$file" .sh)
 if [[ -e "/var/lib/sabi-allvpn/done/$name" ]]; then echo "SKIP completed: $name"; continue; fi
 echo "START $name $(date -Is)"
 bash "$file"
 touch "/var/lib/sabi-allvpn/done/$name"
 echo "DONE $name $(date -Is)"
done
python3 "$REPO/scripts/export_private.py"
python3 "$REPO/scripts/doctor.py"
python3 "$REPO/scripts/export_private.py"
echo 'INSTALLATION_COMPLETE. Credentials: /root/allvpn/panel-access.txt; ZIP: /root/allvpn/export/allvpn-private.zip'
