import json,os,shutil,tarfile,zipfile
from pathlib import Path
root=Path('/root/allvpn');data=Path('/var/lib/allvpn-panel');out=data/'files';out.mkdir(exist_ok=True,parents=True)
for f in (root/'clients').iterdir():
 if f.is_file():shutil.copy2(f,out/f.name)
shutil.copy2(root/'secrets.env',out/'vpn-server-secrets.env')
c=json.loads((data/'catalog.json').read_text())
# Remove Naive outbound from bundled general sing-box profile to avoid optional Cronet startup failure.
p=out/'sing-box-client.json'
if p.exists():
 s=json.loads(p.read_text());s['outbounds']=[o for o in s['outbounds'] if o.get('type')!='naive']
 for o in s['outbounds']:
  if 'outbounds' in o:o['outbounds']=[x for x in o['outbounds'] if x!='naive']
 s['outbounds']=[o for o in s['outbounds'] if o.get('tag')!='manual']
 s['outbounds'].insert(0,{'type':'selector','tag':'manual','outbounds':['auto']+[o['tag'] for o in s['outbounds'] if o.get('tag') not in ['auto','direct','shadowtls-out']]})
 s.setdefault('route',{})['final']='manual';p.write_text(json.dumps(s,ensure_ascii=False,indent=2))
# Standalone Naive profile, explicitly requiring supporting clients.
e=dict(x.split('=',1) for x in (root/'secrets.env').read_text().splitlines() if '=' in x)
naive={'listen':'socks://127.0.0.1:1080','proxy':'https://'+e['NAIVE_USER']+':'+e['NAIVE_PW']+'@'+e['DOMAIN']+':10443'}
(out/'naive-client.json').write_text(json.dumps(naive,indent=2))
# Comprehensive guide, including limitations and instructions for every connection.
md=['# راهنمای خصوصی ALLVPN','این فایل حاوی اطلاعات اتصال خصوصی است.','اطلاعات اتصال هنگام ایجاد پنل ثبت شده؛ فعال بودن سرویس تضمین دسترسی از اینترنت شما نیست.','']
for i in c['items']:
 md+=['## '+i['title'],i['summary'],'پورت: '+i['port'],'']
 md += [f"- {f['label']}: `{f['value']}`" for f in i['fields']]
 md += ['']+[str(n+1)+'. '+s for n,s in enumerate(i['steps'])]
 md += ['هشدار: '+w for w in i['warnings']]+['حد آزمون: '+i['evidence'],'']
md+=['## صندوق اطلاعات مدیر','این بخش شامل کلید خصوصی و رمز مدیریت است.']+[f"- {f['label']}: `{f['value']}`" for f in c['vault']]
(out/'README-complete-fa.md').write_text('\n'.join(md))
# Purpose-limited server recovery backup; excludes cloud keys, OS credential stores and panel authentication.
paths=['/etc/iptables','/etc/systemd/system/xray.service','/etc/systemd/system/sing-box.service','/etc/systemd/system/mtg.service','/etc/systemd/system/dnstt.service','/etc/systemd/system/softether-vpnserver.service','/etc/systemd/system/accel-ppp.service','/etc/systemd/system/awg-quick@awg0.service.d','/usr/local/etc/xray/config.json','/etc/sing-box/config.json','/etc/wireguard','/etc/amnezia/amneziawg','/etc/openvpn/server','/etc/ocserv/ocserv.conf','/etc/ocserv/ocpasswd','/etc/mtg.toml','/etc/dnstt','/etc/tor/torrc','/etc/ipsec.conf','/etc/ipsec.secrets','/etc/ipsec.d','/etc/xl2tpd','/etc/ppp/chap-secrets','/etc/ppp/options.xl2tpd','/etc/accel-ppp.conf','/opt/vpnserver/vpn_server.config','/etc/allvpn/cert','/etc/letsencrypt/live','/etc/letsencrypt/archive','/etc/letsencrypt/renewal','/etc/letsencrypt/renewal-hooks/deploy','/root/allvpn/secrets.env']
with tarfile.open(out/'server-configs-private.tgz','w:gz',dereference=True) as t:
 for name in paths:
  if Path(name).exists():t.add(name,arcname=name.lstrip('/'))
# All small client files and guides; binaries are separate downloads.
with zipfile.ZipFile(out/'allvpn-client-files.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.iterdir()):
  if f.is_file() and not f.name.endswith('.zip') and not f.name.startswith('dnstt-client') and f.name not in ['server-configs-private.tgz','vpn-server-secrets.env','allvpn-client-files.zip']:z.write(f,f.name)
text_names={'ssh-tunnel-key','ssh-tunnel-key.pub','dnstt-server.pub'}
descriptions={'allvpn-client-files.zip':'آرشیو کانفیگ‌ها و راهنما؛ خصوصی و حاوی رمز. باینری dnstt جدا دانلود می‌شود.','server-configs-private.tgz':'پشتیبان بسیار حساس تنظیمات و کلیدهای سرور؛ فقط برای بازیابی توسط مدیر. اطلاعات AWS، Cloudflare یا رمز پنل در آن نیست.','vpn-server-secrets.env':'همهٔ مقادیر تولیدشده برای VPN؛ شامل کلید خصوصی سرور و رمز مدیریت.','sing-box-client.json':'انتخاب مسیر دستی / خودکار؛ پروکسی محلی روی 127.0.0.1:2080. بدون TUN و بدون وابستگی Naive/Cronet.','naive-client.json':'پروفایل برای کلاینت رسمی NaiveProxy؛ نه پروکسی HTTP معمولی.','README-complete-fa.md':'راهنمای فارسی همهٔ روش‌ها همراه با اطلاعات خصوصی و نکته‌های سازگاری.','subscription-base64.txt':'متن اشتراک Base64؛ از فایل یا clipboard وارد کلاینت سازگار کنید. URL دانلود نیاز به ورود دارد و لینک سابسکریپشن عمومی نیست.','ssh-tunnel-key':'کلید خصوصی کاربر tunnel؛ به اشتراک نگذارید.','allvpn.p12':'گواهی و کلید IKEv2؛ رمز فایل خالی است.','allvpn.mobileconfig':'پروفایل IKEv2 برای iOS و macOS؛ قبل از نصب مشخصات سرور را بررسی کنید.','allvpn.sswan':'پروفایل strongSwan برای اندروید.','dnstt-client-linux':'باینری Linux x86-64؛ ساخته‌شده روی سرور.','dnstt-client.exe':'باینری Windows x86-64؛ ساخته‌شده روی سرور.','dnstt-client-mac-arm64':'باینری macOS ARM64؛ ممکن است محدودیت اجرای سیستم‌عامل داشته باشد.'}
manifest=[]
for f in sorted(out.iterdir()):
 if f.is_file():
  istext=f.suffix in ['.json','.conf','.ovpn','.txt','.md','.env','.pub'] or f.name in text_names
  manifest.append({'name':f.name,'size':f.stat().st_size,'text':istext,'kind':'SERVER BACKUP' if f.name.startswith('server-configs') else ('SECRET CONFIG' if istext else 'PRIVATE FILE'),'description':descriptions.get(f.name,'فایل خصوصی مربوط به اتصال؛ آموزش آن در کارت همان روش موجود است.')})
(data/'files.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Private file library:',len(manifest),'files')
