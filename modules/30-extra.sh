#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
cd /root/allvpn
r(){ openssl rand -hex ${1:-12}; }
grep -q OC_USER secrets.env || cat >> secrets.env <<EOF
OC_USER=ocuser
OC_PW=$(r 10)
SE_ADMIN_PW=$(r 12)
SE_USER=seuser
SE_PW=$(r 10)
EOF
set -a; . ./secrets.env; set +a
IF=$(ip -o -4 route show default | awk 'NR==1{print $5}')
mkdir -p clients build
export PATH=/usr/local/go/bin:$PATH GOPATH=/root/go GOCACHE=/root/.cache/go HOME=/root
apt-get install -y -qq ocserv tor obfs4proxy cmake gcc g++ make pkgconf libncurses-dev libreadline-dev libsodium-dev libssl-dev zlib1g-dev >/dev/null
# ---------- AmneziaWG (userspace amneziawg-go + awg tools) ----------
cd /root/allvpn/build
clone_pinned https://github.com/amnezia-vpn/amneziawg-go amneziawg-go b5928efb6ca19f0153958460c3d141f04abc5c2e
(cd amneziawg-go && make && install -m755 amneziawg-go /usr/local/bin/amneziawg-go)
clone_pinned https://github.com/amnezia-vpn/amneziawg-tools amneziawg-tools ee0f0a9aa34ff0a0da4b3433b9512781cfe02843
(cd amneziawg-tools/src && make && make install WITH_WGQUICK=yes WITH_SYSTEMDUNITS=yes)
cd /root/allvpn
mkdir -p /etc/amnezia/amneziawg
if [ ! -f /etc/amnezia/amneziawg/awg0.conf ]; then
 SK=$(awg genkey); SP=$(echo $SK | awg pubkey); CK=$(awg genkey); CP=$(echo $CK | awg pubkey); PSK=$(awg genpsk)
 S1=$((RANDOM%100+20)); S2=$((RANDOM%100+20)); [ $((S1+56)) -eq $S2 ] && S2=$((S2+1))
 H1=$(shuf -i 100000-500000000 -n1); H2=$(shuf -i 500000001-1000000000 -n1); H3=$(shuf -i 1000000001-1500000000 -n1); H4=$(shuf -i 1500000001-2000000000 -n1)
 OBF="Jc = 4
Jmin = 40
Jmax = 70
S1 = $S1
S2 = $S2
H1 = $H1
H2 = $H2
H3 = $H3
H4 = $H4"
 cat > /etc/amnezia/amneziawg/awg0.conf <<EOF
[Interface]
Address = 10.67.67.1/24
ListenPort = 51821
PrivateKey = $SK
$OBF
[Peer]
PublicKey = $CP
PresharedKey = $PSK
AllowedIPs = 10.67.67.2/32
EOF
 cat > clients/amneziawg.conf <<EOF
[Interface]
PrivateKey = $CK
Address = 10.67.67.2/32
DNS = 1.1.1.1, 8.8.8.8
MTU = 1280
$OBF
[Peer]
PublicKey = $SP
PresharedKey = $PSK
Endpoint = $IP:51821
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
fi
mkdir -p /etc/systemd/system/awg-quick@awg0.service.d
printf '[Service]\nEnvironment=WG_QUICK_USERSPACE_IMPLEMENTATION=amneziawg-go\nEnvironment=WG_SUDO=1\n' > /etc/systemd/system/awg-quick@awg0.service.d/override.conf
systemctl daemon-reload; systemctl enable --now awg-quick@awg0
# ---------- OpenConnect (ocserv, AnyConnect-compatible) ----------
cat > /etc/ocserv/ocserv.conf <<EOF
auth = "plain[passwd=/etc/ocserv/ocpasswd]"
tcp-port = 4443
udp-port = 4443
run-as-user = nobody
run-as-group = daemon
socket-file = /run/ocserv-socket
server-cert = /etc/allvpn/cert/fullchain.pem
server-key = /etc/allvpn/cert/privkey.pem
isolate-workers = true
max-clients = 32
max-same-clients = 4
keepalive = 32400
dpd = 90
mobile-dpd = 1800
switch-to-tcp-timeout = 25
try-mtu-discovery = true
tls-priorities = "NORMAL:%SERVER_PRECEDENCE:%COMPAT:-VERS-SSL3.0:-VERS-TLS1.0:-VERS-TLS1.1"
auth-timeout = 240
min-reauth-time = 300
max-ban-score = 80
ban-reset-time = 1200
cookie-timeout = 300
deny-roaming = false
rekey-time = 172800
rekey-method = ssl
use-occtl = true
pid-file = /run/ocserv.pid
device = vpns
predictable-ips = true
default-domain = $DOMAIN
ipv4-network = 10.11.0.0
ipv4-netmask = 255.255.255.0
dns = 1.1.1.1
dns = 8.8.8.8
tunnel-all-dns = true
cisco-client-compat = true
dtls-legacy = true
EOF
printf '%s\n%s\n' "$OC_PW" "$OC_PW" | ocpasswd -c /etc/ocserv/ocpasswd $OC_USER
systemctl enable ocserv; systemctl restart ocserv
# ---------- MTProto proxy for Telegram (mtg v2, fake-TLS) ----------
if [[ ! -f /etc/mtg.toml ]]; then
 printf 'secret = "%s"\nbind-to = "0.0.0.0:4433"\npublic-ipv4 = "%s"\n\n[domain-fronting]\nport = 4443\n' "$(mtg generate-secret --hex "$DOMAIN")" "$IP" >/etc/mtg.toml
fi
chmod 600 /etc/mtg.toml
cat > /etc/systemd/system/mtg.service <<EOF
[Unit]
Description=mtg MTProto proxy
After=network-online.target
[Service]
ExecStart=/usr/local/bin/mtg run /etc/mtg.toml
Restart=always
User=root
AmbientCapabilities=CAP_NET_BIND_SERVICE
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload; systemctl enable --now mtg
# ---------- Tor private obfs4 bridge ----------
cat > /etc/tor/torrc <<EOF
BridgeRelay 1
ORPort 127.0.0.1:9001
AssumeReachable 1
ServerTransportPlugin obfs4 exec /usr/bin/obfs4proxy
ServerTransportListenAddr obfs4 0.0.0.0:7443
ExtORPort auto
PublishServerDescriptor 0
BridgeDistribution none
Nickname allvpnbridge
ContactInfo none
EOF
chmod 644 /etc/tor/torrc
systemctl enable tor; systemctl restart tor@default
# ---------- dnstt (DNS tunnel) -> local SOCKS ----------
cd build
clone_pinned https://www.bamsoftware.com/git/dnstt.git dnstt 0c5c52a57d899c05428c116898941761a2ed83c2
(cd dnstt/dnstt-server && go build -o /usr/local/bin/dnstt-server .)
(cd dnstt/dnstt-client && GOOS=linux go build -o /root/allvpn/clients/dnstt-client-linux . && GOOS=windows go build -o /root/allvpn/clients/dnstt-client.exe . && GOOS=darwin GOARCH=arm64 go build -o /root/allvpn/clients/dnstt-client-mac-arm64 .)
cd /root/allvpn
mkdir -p /etc/dnstt
chmod 700 /etc/dnstt
[ -f /etc/dnstt/server.key ] || dnstt-server -gen-key -privkey-file /etc/dnstt/server.key -pubkey-file /etc/dnstt/server.pub
cp /etc/dnstt/server.pub clients/dnstt-server.pub
cat > /etc/systemd/system/dnstt.service <<EOF
[Unit]
Description=dnstt server
After=network-online.target
[Service]
ExecStart=/usr/local/bin/dnstt-server -udp 0.0.0.0:5300 -privkey-file /etc/dnstt/server.key $DNS_TUNNEL 127.0.0.1:1081
Restart=always
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload; systemctl enable --now dnstt
iptables -t nat -C PREROUTING -i $IF -p udp --dport 53 -j REDIRECT --to-ports 5300 2>/dev/null || iptables -t nat -I PREROUTING -i $IF -p udp --dport 53 -j REDIRECT --to-ports 5300
# local no-auth SOCKS for dnstt upstream (loopback only)
jq '.inbounds += [{"type":"socks","tag":"socks-local","listen":"127.0.0.1","listen_port":1081}] | .inbounds |= unique_by(.tag)' /etc/sing-box/config.json > /tmp/sb.json && sing-box check -c /tmp/sb.json && cp /tmp/sb.json /etc/sing-box/config.json && systemctl restart sing-box
# ---------- SSH tunnel user (key only, no shell) ----------
id tunnel >/dev/null 2>&1 || useradd -m -s /usr/sbin/nologin tunnel
mkdir -p /home/tunnel/.ssh
[ -f clients/ssh-tunnel-key ] || ssh-keygen -q -t ed25519 -N "" -C allvpn-tunnel -f clients/ssh-tunnel-key
cp clients/ssh-tunnel-key.pub /home/tunnel/.ssh/authorized_keys; chown -R tunnel:tunnel /home/tunnel/.ssh; chmod 700 /home/tunnel/.ssh; chmod 600 /home/tunnel/.ssh/authorized_keys
cat > /etc/ssh/sshd_config.d/50-tunnel.conf <<EOF
Match User tunnel
  AllowTcpForwarding yes
  X11Forwarding no
  PermitTTY no
  ForceCommand /usr/sbin/nologin
EOF
chmod 644 /etc/ssh/sshd_config.d/50-tunnel.conf
sshd -t
systemctl reload ssh
netfilter-persistent save
systemctl is-active awg-quick@awg0 ocserv mtg tor@default dnstt sing-box
echo STAGE4_DONE

