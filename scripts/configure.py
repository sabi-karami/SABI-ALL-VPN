#!/usr/bin/env python3
"""Interactive configuration. Secrets are read through getpass on a TTY, not command arguments."""
import os,json,getpass,re,ipaddress,secrets,shlex,urllib.request,sys
from pathlib import Path
C=Path('/etc/sabi-allvpn');C.mkdir(mode=0o700,exist_ok=True)
if (C/'install.env').exists():print('Saved configuration found; resuming without changing keys.');sys.exit(0)
def ask(q,default=''):
 v=input(q+(f' [{default}]' if default else '')+': ').strip();return v or default
def domain(v):
 if not re.fullmatch(r'(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}',v):raise ValueError('Enter a lowercase ASCII FQDN; use punycode for IDNs.')
 return v
cfg=json.loads((C/'input.json').read_text()) if (C/'input.json').exists() else {}
if not cfg:
 print('SABI ALLVPN — fresh Ubuntu 24.04 amd64 only. Existing services/files will not be migrated.')
 cfg['ZONE']=domain(ask('Cloudflare zone (example.com)'))
 prefix=ask('Subdomain prefix','allvpn')
 if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?',prefix):raise ValueError('Invalid prefix')
 cfg.update(DOMAIN=f'{prefix}.{cfg["ZONE"]}',CDN=f'{prefix}-cdn.{cfg["ZONE"]}',DNS_NS=f'{prefix}-ns.{cfg["ZONE"]}',DNS_TUNNEL=f'{prefix}-t.{cfg["ZONE"]}')
 detected=''
 try:detected=urllib.request.urlopen('https://api.ipify.org',timeout=8).read().decode().strip()
 except Exception:pass
 cfg['IP']=str(ipaddress.IPv4Address(ask('Public IPv4 of this server',detected)))
 cfg['PANEL_USER']=ask('Panel username','sabi')
 cfg['REALITY_SNI']=domain(ask('REALITY TLS 1.3 target','www.speedtest.net'))
 cfg['ENABLE_PPTP']='yes' if ask('Enable INSECURE PPTP? yes/no','no')=='yes' else 'no'
 cfg['ENABLE_PLAIN_PROXY']='yes' if ask('Expose unencrypted SOCKS/HTTP 1080? yes/no','no')=='yes' else 'no'
 mode=ask('DNS mode: cloudflare or manual','cloudflare');cfg['DNS_MODE']=mode
 if mode=='cloudflare':
  token=getpass.getpass('Cloudflare API token (DNS edit + Zone read + Zone settings read, hidden): ').strip()
  if not token:raise ValueError('Token required for automatic DNS')
  (C/'cloudflare.token').write_text(token);os.chmod(C/'cloudflare.token',0o600)
 elif mode!='manual':raise ValueError('Invalid DNS mode')
 else:
  print('MANUAL DNS: create direct, CDN and NS A records pointing here. Keep direct AND CDN DNS-only during issuance. Add NS delegation for DNS_TUNNEL. Turn on proxy for CDN only after successful TLS issuance. Zone SSL must be Full or Full (strict).')
  print(json.dumps({k:cfg[k] for k in ['DOMAIN','CDN','DNS_NS','DNS_TUNNEL','IP']},indent=2))
  if ask('Type DNSREADY after creating these records')!='DNSREADY':raise SystemExit('Cancelled')
 print('Will install VPN listeners, private HTTPS panel, forwarding/NAT and TLS certificates on this dedicated server.')
 if ask('Type INSTALL to confirm')!='INSTALL':raise SystemExit('Cancelled')
allowed={'ZONE','DOMAIN','CDN','DNS_NS','DNS_TUNNEL','REALITY_SNI','IP','PANEL_USER','ENABLE_PPTP','ENABLE_PLAIN_PROXY','DNS_MODE','REGION','INSTANCE_ID'}
if set(cfg)-allowed:raise ValueError('Unexpected configuration keys')
for key in ['ZONE','DOMAIN','CDN','DNS_NS','DNS_TUNNEL','REALITY_SNI']:cfg[key]=domain(cfg[key])
if len({cfg[k] for k in ['DOMAIN','CDN','DNS_NS','DNS_TUNNEL']})!=4:raise ValueError('DNS names must be distinct')
for k in ['DOMAIN','CDN','DNS_NS','DNS_TUNNEL']:
 if not cfg[k].endswith('.'+cfg['ZONE']):raise ValueError('Hostnames must belong to zone')
cfg['IP']=str(ipaddress.IPv4Address(cfg['IP']))
if not re.fullmatch(r'[A-Za-z0-9_.-]{1,32}',cfg['PANEL_USER']):raise ValueError('Invalid username')
for k in ['ENABLE_PPTP','ENABLE_PLAIN_PROXY']:
 if cfg[k] not in ['yes','no']:raise ValueError(k+' must be yes/no')
if cfg['DNS_MODE'] not in ['manual','cloudflare']:raise ValueError('Invalid DNS mode')
cfg['PANEL_PORT']='9444'
(C/'install.env').write_text('\n'.join(f'export {k}={shlex.quote(str(v))}' for k,v in cfg.items())+'\n');os.chmod(C/'install.env',0o600)
(C/'config.json').write_text(json.dumps(cfg,indent=2));os.chmod(C/'config.json',0o600)
print('Configuration saved. Generated passwords will be kept locally, not in GitHub.')
