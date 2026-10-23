import os,json,secrets,shutil,re
from pathlib import Path
from werkzeug.security import generate_password_hash
repo=Path(os.environ['REPO']);root=Path('/opt/allvpn-panel');data=Path('/var/lib/allvpn-panel');root.mkdir(parents=True,exist_ok=True);data.mkdir(parents=True,exist_ok=True)
E=dict(os.environ);E.setdefault('REGION','VPS')
for f in (repo/'panel').iterdir():
 if f.is_file():
  text=f.read_text()
  if f.suffix=='.html':text=re.sub(r'\$\{([A-Z_]+)\}',lambda m:E[m[1]],text)
  (root/f.name).write_text(text)
shutil.copytree(repo/'panel/static',root/'static',dirs_exist_ok=True)
if not (data/'auth.json').exists():
 pw=secrets.token_urlsafe(24);a={'username':E['PANEL_USER'],'password_hash':generate_password_hash(pw),'version':secrets.token_hex(16),'session_key':secrets.token_urlsafe(48)};(data/'auth.json').write_text(json.dumps(a));(data/'auth.json').chmod(0o600)
 Path('/root/allvpn/panel-access.txt').write_text(f'PRIVATE — do not publish\nPanel: https://{E["DOMAIN"]}:9444\nUsername: {E["PANEL_USER"]}\nInitial password: {pw}\nChange it in the panel. Passwords have a minimum of 8 characters.\nThis file is not automatically updated after a password change.\n')
 Path('/root/allvpn/panel-access.txt').chmod(0o600)
