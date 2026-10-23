#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
[[ "$ENABLE_PPTP" == yes ]] || { echo "PPTP disabled by choice"; exit 0; }
export DEBIAN_FRONTEND=noninteractive
cd /root/allvpn; set -a; . ./secrets.env; set +a
apt-get install -y -qq libpcre3-dev libssl-dev cmake >/dev/null
cd build
clone_pinned https://github.com/accel-ppp/accel-ppp.git accel-ppp b8a3c54aa34434312aa0053686ec37a133fb54e6
mkdir -p accel-ppp/build && cd accel-ppp/build
cmake -DCMAKE_INSTALL_PREFIX=/usr -DLUA=FALSE -DBUILD_IPOE_DRIVER=FALSE -DBUILD_VLAN_MON_DRIVER=FALSE -DRADIUS=FALSE -DSHAPER=FALSE -DNETSNMP=FALSE -DCMAKE_BUILD_TYPE=Release .. >/dev/null
make -j2 >/dev/null
make install >/dev/null
which accel-pppd
mkdir -p /var/log/accel-ppp /etc/ppp
grep -q "^$PPTP_USER " /etc/ppp/chap-secrets || printf '%s * %s *\n' "$PPTP_USER" "$PPTP_PW" >> /etc/ppp/chap-secrets; chmod 600 /etc/ppp/chap-secrets
cat > /etc/accel-ppp.conf <<EOF
[modules]
log_file
pptp
auth_mschap_v2
chap-secrets
ippool
[core]
log-error=/var/log/accel-ppp/core.log
thread-count=2
[common]
single-session=replace
[ppp]
verbose=1
min-mtu=1280
mtu=1400
mru=1400
mppe=require
ipv4=require
ipv6=deny
lcp-echo-interval=20
lcp-echo-timeout=120
[pptp]
verbose=1
bind=0.0.0.0
[dns]
dns1=1.1.1.1
dns2=8.8.8.8
[client-ip-range]
disable
[ip-pool]
gw-ip-address=10.10.0.1
10.10.0.100-10.10.0.200
[chap-secrets]
gw-ip-address=10.10.0.1
chap-secrets=/etc/ppp/chap-secrets
[log]
log-file=/var/log/accel-ppp/accel-ppp.log
log-emerg=/var/log/accel-ppp/emerg.log
level=3
[cli]
tcp=127.0.0.1:2001
EOF
printf 'pptp\ngre\nnf_conntrack_pptp\n' > /etc/modules-load.d/pptp.conf
modprobe pptp; modprobe gre
cat > /etc/systemd/system/accel-ppp.service <<EOF
[Unit]
Description=accel-ppp (PPTP server)
After=network-online.target
[Service]
ExecStart=/usr/sbin/accel-pppd -c /etc/accel-ppp.conf
Restart=always
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload; systemctl enable --now accel-ppp
sleep 2; systemctl is-active accel-ppp; ss -lntp | grep 1723
echo STAGE6_DONE

