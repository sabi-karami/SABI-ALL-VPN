#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
cd /root/allvpn
r(){ openssl rand -hex ${1:-12}; }
grep -q IPSEC_PSK secrets.env || cat >> secrets.env <<EOF
IPSEC_PSK=$(r 12)
VPN_USER=vpnuser
VPN_PW=$(r 10)
PPTP_USER=pptpuser
PPTP_PW=$(r 10)
EOF
set -a; . ./secrets.env; set +a
IF=$(ip -o -4 route show default | awk 'NR==1{print $5}')
# ---------- IKEv2 / L2TP / XAuth (libreswan + xl2tpd) ----------
curl -fsSL https://raw.githubusercontent.com/hwdsl2/setup-ipsec-vpn/0ed9d3b1e23dac59d98ee8c6d0f2f4951c330258/vpnsetup_ubuntu.sh -o vpn.sh
python3 - <<'PY'
from pathlib import Path
p=Path('vpn.sh');s=p.read_text().replace('setup-ipsec-vpn/master/extras','setup-ipsec-vpn/0ed9d3b1e23dac59d98ee8c6d0f2f4951c330258/extras').replace('setup-ipsec-vpn/-/raw/master/extras','setup-ipsec-vpn/-/raw/0ed9d3b1e23dac59d98ee8c6d0f2f4951c330258/extras');p.write_text(s)
PY
VPN_IPSEC_PSK=$IPSEC_PSK VPN_USER=$VPN_USER VPN_PASSWORD=$VPN_PW VPN_DNS_NAME=$DOMAIN VPN_CLIENT_NAME=allvpn VPN_DNS_SRV1=1.1.1.1 VPN_DNS_SRV2=8.8.8.8 VPN_PUBLIC_IP=$IP sh vpn.sh > logs/ipsec.log 2>&1
echo "IPsec finished; details are in root-only logs/ipsec.log"
ls -la /root/*.p12 /root/*.mobileconfig /root/*.sswan 2>&1
# ---------- WireGuard ----------
mkdir -p /etc/wireguard clients
if [ ! -f /etc/wireguard/wg0.conf ]; then
 SK=$(wg genkey); SP=$(echo $SK | wg pubkey); CK=$(wg genkey); CP=$(echo $CK | wg pubkey); PSK=$(wg genpsk)
 cat > /etc/wireguard/wg0.conf <<EOF
[Interface]
Address = 10.66.66.1/24
ListenPort = 51820
PrivateKey = $SK
[Peer]
PublicKey = $CP
PresharedKey = $PSK
AllowedIPs = 10.66.66.2/32
EOF
 cat > clients/wireguard.conf <<EOF
[Interface]
PrivateKey = $CK
Address = 10.66.66.2/32
DNS = 1.1.1.1, 8.8.8.8
MTU = 1380
[Peer]
PublicKey = $SP
PresharedKey = $PSK
Endpoint = $IP:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
fi
systemctl enable --now wg-quick@wg0
# ---------- OpenVPN (UDP 1194 + TCP 1194) ----------
apt-get install -y -qq openvpn easy-rsa >/dev/null
if [ ! -f /etc/openvpn/server/ca.crt ]; then
 rm -rf /etc/openvpn/easy-rsa; make-cadir /etc/openvpn/easy-rsa; cd /etc/openvpn/easy-rsa
 export EASYRSA_BATCH=1 EASYRSA_ALGO=ec EASYRSA_CURVE=prime256v1
 ./easyrsa init-pki; ./easyrsa --req-cn=allvpn-ca build-ca nopass
 ./easyrsa build-server-full server nopass; ./easyrsa build-client-full client1 nopass
 cp pki/ca.crt pki/issued/server.crt pki/private/server.key /etc/openvpn/server/
 openvpn --genkey secret /etc/openvpn/server/tc.key
 cd /root/allvpn
fi
for P in udp tcp; do
 if [ $P = udp ]; then NET=10.8.0.0; else NET=10.9.0.0; fi
 cat > /etc/openvpn/server/server-$P.conf <<EOF
port 1194
proto $P
dev tun-$P
dev-type tun
ca ca.crt
cert server.crt
key server.key
dh none
ecdh-curve prime256v1
tls-crypt tc.key
topology subnet
server $NET 255.255.255.0
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 8.8.8.8"
keepalive 10 120
data-ciphers AES-128-GCM:AES-256-GCM:CHACHA20-POLY1305
user nobody
group nogroup
persist-key
persist-tun
verb 2
EOF
 [ $P = udp ] && echo "explicit-exit-notify 1" >> /etc/openvpn/server/server-$P.conf
 systemctl enable --now openvpn-server@server-$P
 cat > clients/openvpn-$P.ovpn <<EOF
client
dev tun
proto $P
remote $IP 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
data-ciphers AES-128-GCM:AES-256-GCM:CHACHA20-POLY1305
verb 3
<ca>
$(cat /etc/openvpn/server/ca.crt)
</ca>
<cert>
$(sed -n '/BEGIN CERTIFICATE/,/END CERTIFICATE/p' /etc/openvpn/easy-rsa/pki/issued/client1.crt)
</cert>
<key>
$(cat /etc/openvpn/easy-rsa/pki/private/client1.key)
</key>
<tls-crypt>
$(cat /etc/openvpn/server/tc.key)
</tls-crypt>
EOF
done
# ---------- NAT / forwarding for 10.0.0.0/8 tunnels ----------
iptables -t nat -C POSTROUTING -s 10.0.0.0/8 -o $IF -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -s 10.0.0.0/8 -o $IF -j MASQUERADE
iptables -C FORWARD -s 10.0.0.0/8 -j ACCEPT 2>/dev/null || iptables -I FORWARD 1 -s 10.0.0.0/8 -j ACCEPT
iptables -C FORWARD -d 10.0.0.0/8 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || iptables -I FORWARD 1 -d 10.0.0.0/8 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -t mangle -C FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu 2>/dev/null || iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
netfilter-persistent save
systemctl is-active ipsec xl2tpd wg-quick@wg0 openvpn-server@server-udp openvpn-server@server-tcp
iptables -S INPUT | sed -n '1,30p'
echo STAGE3_DONE

