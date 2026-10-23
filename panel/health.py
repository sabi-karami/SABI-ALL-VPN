#!/usr/bin/python3
import json,subprocess,datetime,os
from pathlib import Path
p=Path('/var/lib/allvpn-panel');c=json.loads((p/'catalog.json').read_text());names=sorted({i['service'] for i in c['items']})
services={}
for n in names:
 r=subprocess.run(['systemctl','is-active',n],capture_output=True,text=True,timeout=5)
 services[n]=r.stdout.strip() or 'unknown'
r=subprocess.run(['ssh-keygen','-lf','/etc/ssh/ssh_host_ed25519_key.pub'],capture_output=True,text=True,timeout=5)
cdata={'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'services':services,'ssh_fingerprint':r.stdout.strip(),'scope':'وضعیت سرویس روی سرور؛ نه تست اتصال از اینترنت کاربر'}
t=p/'status.tmp';t.write_text(json.dumps(cdata,ensure_ascii=False));os.chmod(t,0o644);t.replace(p/'status.json')
