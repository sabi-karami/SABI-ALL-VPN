#!/usr/bin/env python3
"""Local service health is not an end-to-end censorship or client compatibility test."""
import json,subprocess,socket,datetime,urllib.request,ssl
from pathlib import Path
cfg=json.loads(Path('/etc/sabi-allvpn/config.json').read_text())
services=['xray','sing-box','ipsec','xl2tpd','wg-quick@wg0','awg-quick@awg0','openvpn-server@server-udp','openvpn-server@server-tcp','ocserv','softether-vpnserver','mtg','tor@default','dnstt','ssh','allvpn-panel','nginx']
if cfg['ENABLE_PPTP']=='yes':services.append('accel-ppp')
rows={s:subprocess.run(['systemctl','is-active',s],capture_output=True,text=True).stdout.strip() for s in services}
for s,v in rows.items():print(f'{s:32} {v}')
report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'services':rows,'scope':'Server service health, not remote end-to-end VPN testing'}
try:
 with urllib.request.urlopen('https://'+cfg['DOMAIN']+':9444/login',timeout=15) as r:report['panel_tls']=r.status==200
except Exception:report['panel_tls']=False
Path('/root/allvpn/health.json').write_text(json.dumps(report,indent=2))
if not all(v=='active' for v in rows.values()) or not report['panel_tls']:raise SystemExit('Health incomplete. See health.json and journalctl. Do not assume every protocol works.')
print('Local service and panel HTTPS checks passed. Test each intended client separately.')
