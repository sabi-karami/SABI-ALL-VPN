import subprocess,shutil,os
if os.geteuid()!=0:raise SystemExit('root required')
if shutil.disk_usage('/').free<8*1024**3:raise SystemExit('At least 8 GiB free disk space required; 20+ GiB total recommended')
if not os.path.exists('/dev/net/tun'):raise SystemExit('TUN device required; use a full VM, not an unprivileged container')
# SSH and local resolver may exist. Reject public ports reserved by this installer.
reserved={80,443,992,1080,1194,1723,2053,2083,2087,2096,3443,4433,4443,5555,7443,8388,8443,9443,9444,10443,11443,19771}
r=subprocess.check_output(['ss','-H','-lntup'],text=True)
for line in r.splitlines():
 cols=line.split()
 if len(cols)<5:continue
 try:port=int(cols[4].rsplit(':',1)[1])
 except ValueError:continue
 if port in reserved:raise SystemExit('Port already in use; use a fresh server: '+str(port))
# This suite manages iptables; do not silently bypass a firewall manager.
if shutil.which('ufw'):
 s=subprocess.run(['ufw','status'],capture_output=True,text=True).stdout
 if 'Status: active' in s:raise SystemExit('UFW active: prepare a dedicated VM / reconcile firewall first')
print('Fresh-host preflight passed.')
