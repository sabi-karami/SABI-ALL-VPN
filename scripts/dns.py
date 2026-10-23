#!/usr/bin/env python3
import json,sys,time,urllib.request,urllib.parse,socket
from pathlib import Path
C=Path('/etc/sabi-allvpn');cfg=json.loads((C/'config.json').read_text());state=Path('/var/lib/sabi-allvpn/dns-created.json')
records=[('A',cfg['DOMAIN'],cfg['IP'],False),('A',cfg['CDN'],cfg['IP'],True),('A',cfg['DNS_NS'],cfg['IP'],False),('NS',cfg['DNS_TUNNEL'],cfg['DNS_NS'],False)]
if cfg['DNS_MODE']=='cloudflare':
 token=(C/'cloudflare.token').read_text().strip()
 def api(path,method='GET',data=None):
  req=urllib.request.Request('https://api.cloudflare.com/client/v4/'+path,data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=30) as r:d=json.load(r)
  if not d.get('success'):raise RuntimeError('Cloudflare operation failed; inspect token scope and zone.')
  return d['result']
 z=api('zones?'+urllib.parse.urlencode({'name':cfg['ZONE']}))
 if len(z)!=1:raise RuntimeError('Exactly one matching zone is required')
 zid=z[0]['id'];created=json.loads(state.read_text()) if state.exists() else []
 for typ,name,value,proxied in records:
  found=api(f'zones/{zid}/dns_records?'+urllib.parse.urlencode({'name':name}))
  if found:
   if len(found)!=1 or found[0]['type']!=typ or found[0]['content'].rstrip('.')!=value.rstrip('.') or found[0].get('proxied',False)!=proxied:
    raise RuntimeError('DNS conflict at '+name+'; existing records were NOT overwritten.')
   continue
  d=api(f'zones/{zid}/dns_records','POST',{'type':typ,'name':name,'content':value,'proxied':proxied,'ttl':1 if proxied else 120,'comment':'Managed by sabi-allvpn'})
  created.append({'zone_id':zid,'id':d['id'],'name':name});state.write_text(json.dumps(created,indent=2));state.chmod(0o600)
 # Per-host origin rule for the CDN only. Never downgrade zone-wide TLS settings.
 # The installer gets a valid certificate for BOTH names by DNS challenge, so Full (strict) is compatible.
 sslmode=api(f'zones/{zid}/settings/ssl')['value']
 if sslmode not in ['full','strict']:raise RuntimeError('Set Cloudflare SSL mode to Full (strict) or Full before continuing. No zone setting was changed automatically.')
 print('DNS records created or matched; no zone-wide Cloudflare settings changed.')
else:
 print('Manual records: direct and CDN must be DNS-only until certificate issuance:')
 for row in records:print(*row)
 if sys.stdin.isatty():input('Press Enter when DNS is ready: ')
for _ in range(60):
 try:
  if cfg['IP'] in socket.gethostbyname_ex(cfg['DOMAIN'])[2]:break
 except OSError:pass
 time.sleep(5)
else:raise RuntimeError('Direct hostname does not resolve to expected IPv4; fix DNS and rerun.')
