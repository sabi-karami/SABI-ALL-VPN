#!/usr/bin/env bash
source "$REPO/scripts/common.sh"
cd /root/allvpn; set -a; . ./secrets.env; set +a
cd build
clone_pinned https://github.com/SoftEtherVPN/SoftEtherVPN_Stable.git SoftEtherVPN_Stable ed17437af9719ac66acab30faa29e375d613c35f
cd SoftEtherVPN_Stable
./configure </dev/null >/dev/null 2>&1 || true
make -j2 >/dev/null
mkdir -p /opt/vpnserver
cp bin/vpnserver/vpnserver bin/vpnserver/hamcore.se2 /opt/vpnserver/
cp bin/vpncmd/vpncmd /opt/vpnserver/
ls -la /opt/vpnserver
cat > /etc/systemd/system/softether-vpnserver.service <<EOF
[Unit]
Description=SoftEther VPN Server (SSTP + SoftEther protocol)
After=network-online.target
[Service]
Type=forking
ExecStart=/opt/vpnserver/vpnserver start
ExecStop=/opt/vpnserver/vpnserver stop
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload; systemctl enable --now softether-vpnserver
sleep 8
V="/opt/vpnserver/vpncmd localhost:5555 /SERVER"
if [[ ! -f /var/lib/sabi-allvpn/softether-password.done ]]; then
 $V /CMD ServerPasswordSet "$SE_ADMIN_PW" </dev/null
 touch /var/lib/sabi-allvpn/softether-password.done
fi
VP="$V /PASSWORD:$SE_ADMIN_PW /CMD"
$VP ListenerDelete 443 </dev/null || true
$VP ListenerDelete 1194 </dev/null || true
$VP ListenerCreate 992 </dev/null || true
$VP ListenerList </dev/null
$VP ServerCertSet /LOADCERT:/etc/allvpn/cert/fullchain.pem /LOADKEY:/etc/allvpn/cert/privkey.pem </dev/null
$VP SstpEnable yes </dev/null
$VP OpenVpnEnable no /PORTS:1194 </dev/null
$VP IPsecEnable /L2TP:no /L2TPRAW:no /ETHERIP:no /PSK:disabled /DEFAULTHUB:DEFAULT </dev/null
$VP VpnAzureSetEnable no </dev/null
HP="$V /PASSWORD:$SE_ADMIN_PW /ADMINHUB:DEFAULT /CMD"
$HP UserCreate $SE_USER /GROUP:none /REALNAME:none /NOTE:none </dev/null || true
$HP UserPasswordSet $SE_USER /PASSWORD:$SE_PW </dev/null
$HP SecureNatEnable </dev/null
systemctl stop softether-vpnserver; sleep 2
sed -i '/declare DDnsClient/,/}/ s/bool Disabled false/bool Disabled true/' /opt/vpnserver/vpn_server.config
systemctl start softether-vpnserver; sleep 4

systemctl restart openvpn-server@server-udp openvpn-server@server-tcp
sleep 2
ss -lntup | grep -E 'vpnserver|openvpn'
echo STAGE5_DONE

