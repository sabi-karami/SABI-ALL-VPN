import json,base64,os
from pathlib import Path
E=os.environ;p=Path('/root/allvpn/clients');links=(p/'links.txt').read_text().splitlines()
sb=links[0].replace(':443?',':3443?').replace('#allvpn-VLESS-REALITY','#allvpn-VLESS-REALITY-singbox');links.insert(1,sb)
if E['ENABLE_PLAIN_PROXY']!='yes':links=[l for l in links if not l.startswith(('socks5://','http://'))]
(p/'links.txt').write_text('\n'.join(links)+'\n');(p/'subscription-base64.txt').write_text(base64.b64encode(('\n'.join(l for l in links if not l.startswith(('socks5://','http://')))+'\n').encode()).decode())
f=p/'sing-box-client.json';c=json.loads(f.read_text());c['outbounds']=[o for o in c['outbounds'] if o.get('tag') not in ['naive','vless-xhttp-cdn']]
for o in c['outbounds']:
 if o.get('tag')=='reality':o['server_port']=3443
 if o.get('tag')=='vmess-ws-cdn':o['security']='aes-128-gcm'
 if 'outbounds' in o:o['outbounds']=[x for x in o['outbounds'] if x not in ['naive','vless-xhttp-cdn']]
c['outbounds'].insert(0,{'type':'selector','tag':'manual','outbounds':['auto']+[o['tag'] for o in c['outbounds'] if o['tag'] not in ['auto','direct','shadowtls-out']]});c['route']['final']='manual';f.write_text(json.dumps(c,indent=2))
naive={'listen':'socks://127.0.0.1:1080','proxy':f'https://{E["NAIVE_USER"]}:{E["NAIVE_PW"]}@{E["DOMAIN"]}:10443'};(p/'naive-client.json').write_text(json.dumps(naive,indent=2))
