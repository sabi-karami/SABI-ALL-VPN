import json,os
from pathlib import Path
E=os.environ;p=Path('/etc/sing-box/config.json');c=json.loads(p.read_text())
c['inbounds']=[x for x in c['inbounds'] if x['tag'] not in ['sb-reality','socks-local']]
if E['ENABLE_PLAIN_PROXY']!='yes':c['inbounds']=[x for x in c['inbounds'] if x['tag']!='mixed']
c['inbounds'] += [{'type':'vless','tag':'sb-reality','listen':'::','listen_port':3443,'users':[{'name':'u','uuid':E['UUID'],'flow':'xtls-rprx-vision'}],'tls':{'enabled':True,'server_name':E['REALITY_SNI'],'reality':{'enabled':True,'handshake':{'server':E['REALITY_SNI'],'server_port':443},'private_key':E['REALITY_PRIV'],'short_id':[E['REALITY_SID']]}}},{'type':'socks','tag':'socks-local','listen':'127.0.0.1','listen_port':1081}]
p.write_text(json.dumps(c,indent=2));p.chmod(0o600)
