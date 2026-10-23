#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
cd /root/allvpn
enc(){ python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$1"; }
L=clients/links.txt; : > $L
echo "vless://$UUID@$IP:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=$REALITY_SNI&fp=chrome&pbk=$REALITY_PUB&sid=$REALITY_SID&type=tcp#allvpn-VLESS-REALITY" >> $L
echo "vless://$UUID@$CDN:2053?encryption=none&security=tls&sni=$CDN&fp=chrome&type=ws&host=$CDN&path=$(enc $WS_VLESS)#allvpn-VLESS-WS-CDN" >> $L
echo "vless://$UUID@$CDN:2083?encryption=none&security=tls&sni=$CDN&fp=chrome&alpn=h2&type=xhttp&host=$CDN&path=$(enc $XH_VLESS)&mode=auto#allvpn-VLESS-XHTTP-CDN" >> $L
VM=$(printf '{"v":"2","ps":"allvpn-VMess-WS-CDN","add":"%s","port":"2087","id":"%s","aid":"0","scy":"aes-128-gcm","net":"ws","type":"none","host":"%s","path":"%s","tls":"tls","sni":"%s","fp":"chrome"}' $CDN $UUID $CDN $WS_VMESS $CDN | base64 -w0)
echo "vmess://$VM" >> $L
echo "trojan://$TROJAN_PW@$CDN:2096?security=tls&sni=$CDN&fp=chrome&type=ws&host=$CDN&path=$(enc $WS_TROJAN)#allvpn-Trojan-WS-CDN" >> $L
echo "trojan://$TROJAN_PW@$DOMAIN:8443?security=tls&sni=$DOMAIN&fp=chrome&type=tcp#allvpn-Trojan-TLS" >> $L
echo "ss://$(printf '%s:%s' $SS_METHOD $SS_KEY | base64 -w0)@$IP:8388#allvpn-Shadowsocks-2022" >> $L
echo "hysteria2://$HY2_PW@$DOMAIN:443?sni=$DOMAIN&alpn=h3#allvpn-Hysteria2" >> $L
echo "tuic://$TUIC_UUID:$TUIC_PW@$DOMAIN:8443?sni=$DOMAIN&alpn=h3&congestion_control=bbr&udp_relay_mode=native#allvpn-TUIC" >> $L
echo "anytls://$ANYTLS_PW@$DOMAIN:11443?sni=$DOMAIN#allvpn-AnyTLS" >> $L
echo "naive+https://$NAIVE_USER:$NAIVE_PW@$DOMAIN:10443#allvpn-NaiveProxy" >> $L
echo "socks5://$SOCKS_USER:$SOCKS_PW@$IP:1080#allvpn-SOCKS5" >> $L
echo "http://$SOCKS_USER:$SOCKS_PW@$IP:1080#allvpn-HTTP-proxy" >> $L
MTS=$(grep secret /etc/mtg.toml | cut -d'"' -f2)
echo "tg://proxy?server=$DOMAIN&port=4433&secret=$MTS" > clients/telegram-mtproto.txt
echo "https://t.me/proxy?server=$DOMAIN&port=4433&secret=$MTS" >> clients/telegram-mtproto.txt

# sing-box client config with every proxy protocol + auto selector
cat > clients/sing-box-client.json <<EOF
{
 "log":{"level":"warn"},
 "dns":{"servers":[{"type":"https","tag":"cf","server":"1.1.1.1"}]},
 "inbounds":[{"type":"mixed","tag":"in","listen":"127.0.0.1","listen_port":2080}],
 "outbounds":[
  {"type":"urltest","tag":"auto","outbounds":["reality","vless-ws-cdn","vless-xhttp-cdn","vmess-ws-cdn","trojan-ws-cdn","trojan-tls","ss2022","hy2","tuic","shadowtls","anytls","naive"]},
  {"type":"vless","tag":"reality","server":"$IP","server_port":443,"uuid":"$UUID","flow":"xtls-rprx-vision","tls":{"enabled":true,"server_name":"$REALITY_SNI","utls":{"enabled":true,"fingerprint":"chrome"},"reality":{"enabled":true,"public_key":"$REALITY_PUB","short_id":"$REALITY_SID"}}},
  {"type":"vless","tag":"vless-ws-cdn","server":"$CDN","server_port":2053,"uuid":"$UUID","tls":{"enabled":true,"server_name":"$CDN"},"transport":{"type":"ws","path":"$WS_VLESS","headers":{"Host":"$CDN"}}},
  {"type":"vless","tag":"vless-xhttp-cdn","server":"$CDN","server_port":2083,"uuid":"$UUID","tls":{"enabled":true,"server_name":"$CDN","alpn":["h2"]},"transport":{"type":"http","path":"$XH_VLESS","host":["$CDN"]}},
  {"type":"vmess","tag":"vmess-ws-cdn","server":"$CDN","server_port":2087,"uuid":"$UUID","security":"auto","tls":{"enabled":true,"server_name":"$CDN"},"transport":{"type":"ws","path":"$WS_VMESS","headers":{"Host":"$CDN"}}},
  {"type":"trojan","tag":"trojan-ws-cdn","server":"$CDN","server_port":2096,"password":"$TROJAN_PW","tls":{"enabled":true,"server_name":"$CDN"},"transport":{"type":"ws","path":"$WS_TROJAN","headers":{"Host":"$CDN"}}},
  {"type":"trojan","tag":"trojan-tls","server":"$DOMAIN","server_port":8443,"password":"$TROJAN_PW","tls":{"enabled":true,"server_name":"$DOMAIN"}},
  {"type":"shadowsocks","tag":"ss2022","server":"$IP","server_port":8388,"method":"$SS_METHOD","password":"$SS_KEY"},
  {"type":"hysteria2","tag":"hy2","server":"$DOMAIN","server_port":443,"password":"$HY2_PW","tls":{"enabled":true,"server_name":"$DOMAIN","alpn":["h3"]}},
  {"type":"tuic","tag":"tuic","server":"$DOMAIN","server_port":8443,"uuid":"$TUIC_UUID","password":"$TUIC_PW","congestion_control":"bbr","tls":{"enabled":true,"server_name":"$DOMAIN","alpn":["h3"]}},
  {"type":"shadowsocks","tag":"shadowtls","method":"2022-blake3-aes-128-gcm","password":"$STLS_SS_KEY","detour":"shadowtls-out"},
  {"type":"shadowtls","tag":"shadowtls-out","server":"$IP","server_port":9443,"version":3,"password":"$STLS_PW","tls":{"enabled":true,"server_name":"www.bing.com","utls":{"enabled":true,"fingerprint":"chrome"}}},
  {"type":"anytls","tag":"anytls","server":"$DOMAIN","server_port":11443,"password":"$ANYTLS_PW","tls":{"enabled":true,"server_name":"$DOMAIN"}},
  {"type":"naive","tag":"naive","server":"$DOMAIN","server_port":10443,"username":"$NAIVE_USER","password":"$NAIVE_PW","tls":{"enabled":true,"server_name":"$DOMAIN"}},
  {"type":"direct","tag":"direct"}
 ],
 "route":{"final":"auto"}
}
EOF
cp /root/allvpn.p12 /root/allvpn.sswan /root/allvpn.mobileconfig clients/
for attempt in $(seq 1 30); do
 [[ -s /var/lib/tor/pt_state/obfs4_bridgeline.txt && -s /var/lib/tor/fingerprint ]] && break
 sleep 2
done
BL=$(cat /var/lib/tor/pt_state/obfs4_bridgeline.txt 2>/dev/null | grep '^Bridge' | sed "s/<IP ADDRESS>/$IP/; s/<PORT>/7443/; s/<FINGERPRINT>/$(awk '{print $2}' /var/lib/tor/fingerprint)/")
echo "$BL" > clients/tor-obfs4-bridge.txt

python3 "$REPO/scripts/fix_clients.py"
