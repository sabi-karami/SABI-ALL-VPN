#!/usr/bin/env python3
import json,hashlib,urllib.request,tarfile,zipfile,os,shutil,subprocess
from pathlib import Path
repo=Path(os.environ['REPO']);lock=json.loads((repo/'versions.lock.json').read_text());base=Path('/root/allvpn/build/assets');base.mkdir(parents=True,exist_ok=True)
def fetch(name,obj):
 p=base/name
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=obj['sha256']:
  with urllib.request.urlopen(obj['url'],timeout=120) as r,open(p,'wb') as f:shutil.copyfileobj(r,f)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=obj['sha256']:raise RuntimeError('Checksum mismatch: '+name)
 return p
x=fetch('xray.zip',lock['assets']['xray']);xd=base/'xray';xd.mkdir(exist_ok=True)
with zipfile.ZipFile(x) as z:z.extractall(xd)
for n in ['xray','geoip.dat','geosite.dat']:
 if (xd/n).exists():
  dst=Path('/usr/local/bin/xray') if n=='xray' else Path('/usr/local/share/xray')/n;dst.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(xd/n,dst);dst.chmod(0o755 if n=='xray' else 0o644)
for key,name in [('sing_box','sing-box'),('mtg','mtg')]:
 p=fetch(key+'.tgz',lock['assets'][key]);d=base/key;d.mkdir(exist_ok=True)
 with tarfile.open(p) as t:t.extractall(d,filter='data')
 src=next(d.rglob(name));shutil.copy2(src,'/usr/local/bin/'+name);Path('/usr/local/bin/'+name).chmod(0o755)
p=fetch('go.tgz',lock['go'])
# Dedicated-host preflight ensures this directory is not an unrelated deployment.
if Path('/usr/local/go').exists():shutil.rmtree('/usr/local/go')
with tarfile.open(p) as t:t.extractall('/usr/local',filter='data')
print('Pinned downloads verified and installed.')
