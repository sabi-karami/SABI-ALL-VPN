#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
cd /root/allvpn
mkdir -p /usr/local/etc/xray
for svc in xray sing-box; do
 if [[ "$svc" == xray ]]; then cmd='/usr/local/bin/xray run -c /usr/local/etc/xray/config.json'; else cmd='/usr/local/bin/sing-box run -c /etc/sing-box/config.json'; fi
 cat >/etc/systemd/system/$svc.service <<EOF
[Unit]
Description=$svc managed by sabi-allvpn
After=network-online.target
[Service]
ExecStart=$cmd
Restart=on-failure
RestartSec=5
LimitNOFILE=1048576
UMask=0077
[Install]
WantedBy=multi-user.target
EOF
done
if [ ! -f secrets.env ]; then
  X=$(xray x25519)
  PRIV=$(echo "$X" | grep -i 'private' | awk -F': *' '{print $2}')
  PUB=$(echo "$X" | grep -iE 'public|password' | head -1 | awk -F': *' '{print $2}')
  r(){ openssl rand -hex ${1:-12}; }
  cat > secrets.env <<EOF
DOMAIN=$DOMAIN
CDN=$CDN
IP=$IP
UUID=$(xray uuid)
REALITY_PRIV=$PRIV
REALITY_PUB=$PUB
REALITY_SID=$(r 8)
REALITY_SNI=$REALITY_SNI
WS_VLESS=/$(r 6)-vl
XH_VLESS=/$(r 6)-xh
WS_VMESS=/$(r 6)-vm
WS_TROJAN=/$(r 6)-tr
TROJAN_PW=$(r 16)
SS_METHOD=2022-blake3-aes-128-gcm
SS_KEY=$(openssl rand -base64 16)
HY2_PW=$(r 16)
TUIC_UUID=$(xray uuid)
TUIC_PW=$(r 16)
STLS_PW=$(r 16)
STLS_SS_KEY=$(openssl rand -base64 16)
NAIVE_USER=u$(r 4)
NAIVE_PW=$(r 16)
ANYTLS_PW=$(r 16)
SOCKS_USER=u$(r 4)
SOCKS_PW=$(r 16)
EOF
  chmod 600 secrets.env
fi
set -a; . ./secrets.env; set +a
C=/etc/allvpn/cert
cat > /usr/local/etc/xray/config.json <<EOF
{
 "log": {"loglevel": "warning"},
 "inbounds": [
  {"tag":"vless-reality","port":443,"protocol":"vless",
   "settings":{"clients":[{"id":"$UUID","flow":"xtls-rprx-vision"}],"decryption":"none"},
   "streamSettings":{"network":"tcp","security":"reality",
     "realitySettings":{"dest":"$REALITY_SNI:443","serverNames":["$REALITY_SNI"],"privateKey":"$REALITY_PRIV","shortIds":["$REALITY_SID"]}},
   "sniffing":{"enabled":true,"destOverride":["http","tls","quic"]}},
  {"tag":"vless-ws","port":2053,"protocol":"vless","settings":{"clients":[{"id":"$UUID"}],"decryption":"none"},
   "streamSettings":{"network":"ws","security":"tls","tlsSettings":{"certificates":[{"certificateFile":"$C/fullchain.pem","keyFile":"$C/privkey.pem"}]},"wsSettings":{"path":"$WS_VLESS"}}},
  {"tag":"vless-xhttp","port":2083,"protocol":"vless","settings":{"clients":[{"id":"$UUID"}],"decryption":"none"},
   "streamSettings":{"network":"xhttp","security":"tls","tlsSettings":{"alpn":["h2","http/1.1"],"certificates":[{"certificateFile":"$C/fullchain.pem","keyFile":"$C/privkey.pem"}]},"xhttpSettings":{"path":"$XH_VLESS","mode":"auto"}}},
  {"tag":"vmess-ws","port":2087,"protocol":"vmess","settings":{"clients":[{"id":"$UUID"}]},
   "streamSettings":{"network":"ws","security":"tls","tlsSettings":{"certificates":[{"certificateFile":"$C/fullchain.pem","keyFile":"$C/privkey.pem"}]},"wsSettings":{"path":"$WS_VMESS"}}},
  {"tag":"trojan-ws","port":2096,"protocol":"trojan","settings":{"clients":[{"password":"$TROJAN_PW"}]},
   "streamSettings":{"network":"ws","security":"tls","tlsSettings":{"certificates":[{"certificateFile":"$C/fullchain.pem","keyFile":"$C/privkey.pem"}]},"wsSettings":{"path":"$WS_TROJAN"}}},
  {"tag":"trojan-tcp","port":8443,"protocol":"trojan","settings":{"clients":[{"password":"$TROJAN_PW"}]},
   "streamSettings":{"network":"tcp","security":"tls","tlsSettings":{"alpn":["h2","http/1.1"],"certificates":[{"certificateFile":"$C/fullchain.pem","keyFile":"$C/privkey.pem"}]}}},
  {"tag":"ss2022","port":8388,"protocol":"shadowsocks","settings":{"method":"$SS_METHOD","password":"$SS_KEY","network":"tcp,udp"}}
 ],
 "outbounds":[{"protocol":"freedom","tag":"direct"},{"protocol":"blackhole","tag":"block"}],
 "routing":{"rules":[{"type":"field","ip":["geoip:private"],"outboundTag":"block"}]}
}
EOF
mkdir -p /etc/sing-box
cat > /etc/sing-box/config.json <<EOF
{
 "log":{"level":"warn"},
 "inbounds":[
  {"type":"hysteria2","tag":"hy2","listen":"::","listen_port":443,"users":[{"name":"u","password":"$HY2_PW"}],
   "masquerade":"https://www.bing.com","tls":{"enabled":true,"server_name":"$DOMAIN","alpn":["h3"],"certificate_path":"$C/fullchain.pem","key_path":"$C/privkey.pem"}},
  {"type":"tuic","tag":"tuic","listen":"::","listen_port":8443,"users":[{"name":"u","uuid":"$TUIC_UUID","password":"$TUIC_PW"}],"congestion_control":"bbr",
   "tls":{"enabled":true,"server_name":"$DOMAIN","alpn":["h3"],"certificate_path":"$C/fullchain.pem","key_path":"$C/privkey.pem"}},
  {"type":"shadowtls","tag":"stls","listen":"::","listen_port":9443,"version":3,"users":[{"name":"u","password":"$STLS_PW"}],
   "handshake":{"server":"www.bing.com","server_port":443},"strict_mode":true,"detour":"stls-ss"},
  {"type":"shadowsocks","tag":"stls-ss","listen":"127.0.0.1","listen_port":18388,"method":"2022-blake3-aes-128-gcm","password":"$STLS_SS_KEY"},
  {"type":"naive","tag":"naive","listen":"::","listen_port":10443,"users":[{"username":"$NAIVE_USER","password":"$NAIVE_PW"}],
   "tls":{"enabled":true,"server_name":"$DOMAIN","certificate_path":"$C/fullchain.pem","key_path":"$C/privkey.pem"}},
  {"type":"anytls","tag":"anytls","listen":"::","listen_port":11443,"users":[{"name":"u","password":"$ANYTLS_PW"}],
   "tls":{"enabled":true,"server_name":"$DOMAIN","certificate_path":"$C/fullchain.pem","key_path":"$C/privkey.pem"}},
  {"type":"mixed","tag":"mixed","listen":"::","listen_port":1080,"users":[{"username":"$SOCKS_USER","password":"$SOCKS_PW"}]}
 ],
 "outbounds":[{"type":"direct","tag":"direct"}]
}
EOF
python3 "$REPO/scripts/fix_core.py"
xray run -test -c /usr/local/etc/xray/config.json
sing-box check -c /etc/sing-box/config.json
systemctl daemon-reload
systemctl enable --now xray sing-box
systemctl restart xray sing-box
sleep 3
systemctl is-active xray sing-box
ss -lntup | grep -E 'xray|sing-box'
echo STAGE2_DONE

