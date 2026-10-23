import json,os,re,base64,urllib.parse
from pathlib import Path
R=Path(os.environ['REPO']);E=dict(os.environ);p=Path('/root/allvpn/clients');E.setdefault('REGION','VPS');E.setdefault('INSTANCE_ID','Dedicated host')
labels={'allvpn-VLESS-REALITY':'reality-xray','allvpn-VLESS-REALITY-singbox':'reality-singbox','allvpn-VLESS-WS-CDN':'vless-ws','allvpn-VLESS-XHTTP-CDN':'vless-xhttp','allvpn-VMess-WS-CDN':'vmess','allvpn-Trojan-WS-CDN':'trojan-ws','allvpn-Trojan-TLS':'trojan-tls','allvpn-Shadowsocks-2022':'ss2022','allvpn-Hysteria2':'hysteria2','allvpn-TUIC':'tuic','allvpn-AnyTLS':'anytls','allvpn-NaiveProxy':'naive','allvpn-SOCKS5':'socks','allvpn-HTTP-proxy':'http'}
for l in (p/'links.txt').read_text().splitlines():
 tag=json.loads(base64.b64decode(l[8:]))['ps'] if l.startswith('vmess://') else urllib.parse.unquote(l.rsplit('#',1)[-1])
 E['LINK_'+labels[tag]]=l
tg=(p/'telegram-mtproto.txt').read_text().splitlines();E.update(TELEGRAM_URI=tg[0],TELEGRAM_WEB=tg[1],TOR_BRIDGE=(p/'tor-obfs4-bridge.txt').read_text().strip(),DNSTT_PUBLIC=(p/'dnstt-server.pub').read_text().strip());E['TOR_BROWSER']=E['TOR_BRIDGE'].removeprefix('Bridge ')
c=json.loads((R/'templates/catalog.json').read_text())
if E['ENABLE_PPTP']!='yes':c['items']=[i for i in c['items'] if i['id']!='pptp']
if E['ENABLE_PLAIN_PROXY']!='yes':c['items']=[i for i in c['items'] if i['id'] not in ['socks','http']]
def walk(v):
 if isinstance(v,str):return re.sub(r'\$\{([^}]+)\}',lambda m:E[m[1]],v)
 if isinstance(v,list):return [walk(x) for x in v]
 if isinstance(v,dict):return {k:walk(x) for k,x in v.items()}
 return v
out=Path('/var/lib/allvpn-panel');out.mkdir(parents=True,exist_ok=True,mode=0o700);(out/'catalog.json').write_text(json.dumps(walk(c),ensure_ascii=False,indent=2));(out/'catalog.json').chmod(0o600)
