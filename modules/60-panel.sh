#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
apt-get install -y -qq nginx python3-venv >/dev/null
id allvpn-panel >/dev/null 2>&1 || useradd --system --home /var/lib/allvpn-panel --shell /usr/sbin/nologin allvpn-panel
mkdir -p /opt/allvpn-panel /var/lib/allvpn-panel
chmod 755 /opt/allvpn-panel
python3 -m venv /opt/allvpn-panel/venv
/opt/allvpn-panel/venv/bin/pip install --disable-pip-version-check -q -r "$REPO/panel/requirements.txt"
python3 "$REPO/scripts/catalog.py"
/opt/allvpn-panel/venv/bin/python "$REPO/scripts/render_panel.py"
python3 /opt/allvpn-panel/build_files.py
chown -R root:root /opt/allvpn-panel
find /opt/allvpn-panel -type d -exec chmod 755 {} \;
find /opt/allvpn-panel -type f -exec chmod a+r {} \;
chown -R allvpn-panel:allvpn-panel /var/lib/allvpn-panel
find /var/lib/allvpn-panel -type d -exec chmod 700 {} \;
find /var/lib/allvpn-panel -type f -exec chmod 600 {} \;
cat >/etc/systemd/system/allvpn-panel.service <<EOF
[Unit]
Description=SABI private connection library
After=network-online.target
[Service]
User=allvpn-panel
Group=allvpn-panel
WorkingDirectory=/opt/allvpn-panel
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PANEL_ORIGIN=https://$DOMAIN:9444
ExecStart=/opt/allvpn-panel/venv/bin/gunicorn --workers 1 --threads 4 --bind 127.0.0.1:19771 --timeout 30 app:app
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/allvpn-panel
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
UMask=0077
[Install]
WantedBy=multi-user.target
EOF
cat >/etc/systemd/system/allvpn-panel-health.service <<'EOF'
[Unit]
Description=Read-only VPN service status
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/allvpn-panel/health.py
EOF
cat >/etc/systemd/system/allvpn-panel-health.timer <<'EOF'
[Unit]
Description=Refresh VPN service status
[Timer]
OnBootSec=15
OnUnitActiveSec=60
[Install]
WantedBy=timers.target
EOF
rm -f /etc/nginx/sites-enabled/default
cat >/etc/nginx/conf.d/allvpn-panel-rate.conf <<'EOF'
limit_req_zone $binary_remote_addr zone=allvpn_login:10m rate=10r/m;
EOF
cat >/etc/nginx/sites-available/allvpn-panel <<EOF
server {
 listen 9444 ssl;
 server_name $DOMAIN;
 ssl_certificate /etc/allvpn/cert/fullchain.pem;
 ssl_certificate_key /etc/allvpn/cert/privkey.pem;
 ssl_protocols TLSv1.2 TLSv1.3;
 server_tokens off;
 client_max_body_size 8k;
 client_body_timeout 10s;
 access_log off;
 location = /api/login {
  limit_req zone=allvpn_login burst=5 nodelay;
  limit_req_status 429;
  proxy_pass http://127.0.0.1:19771;
  proxy_set_header Host \$host;
  proxy_set_header X-Real-IP \$remote_addr;
  proxy_set_header X-Forwarded-Proto https;
 }
 location / {
  proxy_pass http://127.0.0.1:19771;
  proxy_set_header Host \$host;
  proxy_set_header X-Real-IP \$remote_addr;
  proxy_set_header X-Forwarded-Proto https;
  proxy_read_timeout 60s;
  proxy_buffering off;
 }
}
EOF
ln -sf /etc/nginx/sites-available/allvpn-panel /etc/nginx/sites-enabled/allvpn-panel
cat >/etc/letsencrypt/renewal-hooks/deploy/allvpn.sh <<'EOF'
#!/bin/bash
set -e
cp -L /etc/letsencrypt/live/allvpn/fullchain.pem /etc/allvpn/cert/fullchain.pem
cp -L /etc/letsencrypt/live/allvpn/privkey.pem /etc/allvpn/cert/privkey.pem
chmod 600 /etc/allvpn/cert/privkey.pem
systemctl try-restart xray sing-box ocserv
. /root/allvpn/secrets.env
/opt/vpnserver/vpncmd localhost:5555 /SERVER /PASSWORD:"$SE_ADMIN_PW" /CMD ServerCertSet /LOADCERT:/etc/allvpn/cert/fullchain.pem /LOADKEY:/etc/allvpn/cert/privkey.pem </dev/null >/dev/null
nginx -t && systemctl reload nginx
EOF
chmod 700 /etc/letsencrypt/renewal-hooks/deploy/allvpn.sh
systemctl daemon-reload
systemctl enable --now allvpn-panel allvpn-panel-health.timer
systemctl start allvpn-panel-health.service
nginx -t
systemctl enable nginx
systemctl restart nginx
sleep 2
require_service allvpn-panel
require_service nginx
