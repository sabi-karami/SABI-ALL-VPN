#!/usr/bin/env python3
"""Create a private ZIP; never upload this artifact to GitHub."""
import json,zipfile,os
from pathlib import Path
root=Path('/root/allvpn');out=root/'export';out.mkdir(exist_ok=True,mode=0o700)
zpath=out/'allvpn-private.zip';temp=out/'allvpn-private.zip.tmp'
with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
 for f in (Path('/var/lib/allvpn-panel/files')).iterdir():
  if f.is_file():z.write(f,'files/'+f.name)
 for n in ['panel-access.txt','health.json']:
  if (root/n).exists():z.write(root/n,n)
 z.writestr('PRIVATE-READ-ME.txt','PRIVATE archive: contains VPN passwords, server private keys, initial panel credentials. Keep offline; do not publish, email broadly, or commit to GitHub. Initial password may be outdated after changing it in the panel. No AWS/Cloudflare API credentials are included.\n')
os.chmod(temp,0o600);temp.replace(zpath)
print('Private export created at /root/allvpn/export/allvpn-private.zip (not publicly served).')
