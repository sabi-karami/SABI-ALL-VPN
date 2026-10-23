#!/usr/bin/env python3
import json,getpass,secrets,os
from pathlib import Path
from werkzeug.security import generate_password_hash
if os.geteuid()!=0:raise SystemExit('root required')
p=Path('/var/lib/allvpn-panel/auth.json');a=json.loads(p.read_text());pw=getpass.getpass('New panel password (hidden, at least 8 characters): ')
if not 8<=len(pw)<=256:raise SystemExit('8–256 characters required')
if pw!=getpass.getpass('Repeat password: '):raise SystemExit('Mismatch')
a['password_hash']=generate_password_hash(pw);a['version']=secrets.token_hex(12);tmp=p.with_suffix('.reset.tmp');tmp.write_text(json.dumps(a));st=p.stat();os.chown(tmp,st.st_uid,st.st_gid);tmp.chmod(0o600);tmp.replace(p)
print('Password updated; all old sessions invalidated. Initial-password delivery files are now stale.')
