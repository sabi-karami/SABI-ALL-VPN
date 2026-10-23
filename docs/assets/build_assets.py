"""Regenerate the README/Pages SVG artwork (synthetic data only).

Usage: python3 -m pip install 'fonttools[woff]' && python3 docs/assets/build_assets.py
Embeds a Vazirmatn subset (SIL OFL, see panel/static/OFL.txt) into each SVG.
"""

import json, base64, io, math
from pathlib import Path
from xml.sax.saxutils import escape
from fontTools.ttLib import TTFont
from fontTools import subset
R=Path(__file__).resolve().parents[2]; A=R/'docs/assets'; A.mkdir(parents=True,exist_ok=True)
FONT=R/'panel/static/vazirmatn.woff2'
INK='#142f2d';GREEN='#244e43';LIME='#d6e777';PAPER='#f4f3ed';WHITE='#fffef9';MUTED='#687570';LINE='#d9dfd7';ORANGE='#aa5d25';RED='#9d3e33';BLUE='#2b5f73';OLIVE='#6f7d2a'
RLE='\u202b';PDF='\u202c'
MONO="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
def fa(s): return RLE+s+PDF
def T(x,y,s,size=16,w=400,fill=INK,anchor='end',fam='V',extra='',rtl=True,ls=None):
    f="font-family:SabiV,Vazirmatn,Tahoma,sans-serif" if fam=='V' else f"font-family:{MONO}"
    l=f";letter-spacing:{ls}px" if ls else ''
    txt=fa(s) if rtl else s
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" style="{f};font-size:{size}px;font-weight:{w}{l}" fill="{fill}" {extra}>{escape(txt)}</text>'
CHARS=set()
def track(svg):
    import re
    for m in re.findall(r'>([^<]+)<',svg): CHARS.update(m)
def girih(id,color,op,size=72):
    s=size;c=s/2;r=s*0.36
    def sq(rot):
        pts=[]
        for k in range(4):
            a=math.radians(rot+45+90*k);pts.append(f"{c+r*math.cos(a):.1f},{c+r*math.sin(a):.1f}")
        return ' '.join(pts)
    return f'<pattern id="{id}" width="{s}" height="{s}" patternUnits="userSpaceOnUse"><g fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="1"><polygon points="{sq(0)}"/><polygon points="{sq(45)}"/><circle cx="{c}" cy="{c}" r="{r*0.42:.1f}"/><path d="M0 0L{s*0.14:.1f} {s*0.14:.1f}M{s} 0L{s*0.86:.1f} {s*0.14:.1f}M0 {s}L{s*0.14:.1f} {s*0.86:.1f}M{s} {s}L{s*0.86:.1f} {s*0.86:.1f}"/></g></pattern>'
FONTCSS='/*FONT*/'
MOTION='@media (prefers-reduced-motion: reduce){*{animation:none!important}}'
def wrap(w,h,body,title,desc,css=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d"><title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc><style>{FONTCSS}{css}{MOTION}</style>{body}</svg>'
cat=json.loads((R/'templates/catalog.json').read_text())['items']
GROUPS=[('direct','مستقیم','DIRECT',GREEN),('cdn','پشت کلودفلر','CLOUDFLARE',ORANGE),('classic','وی‌پی‌ان کلاسیک','CLASSIC',BLUE),('tools','ابزارهای دیگر','TOOLS',OLIVE),('optional','اختیاری، خاموش','OPT-IN',RED)]
GC={g[0]:g[3] for g in GROUPS}
def grp(i): return 'optional' if i['id'] in ('pptp','socks','http') else i['group']
def title(i): return {'pptp':'PPTP','reality-singbox':'REALITY · sing-box','reality-xray':'REALITY · Xray','oc':'OpenConnect','shadowtls':'ShadowTLS v3','vless-xhttp':'VLESS · XHTTP','vless-ws':'VLESS · WS','vmess':'VMess · WS','trojan-ws':'Trojan · WS','ss2022':'Shadowsocks 2022','ikev2':'IKEv2 / IPsec','telegram':'MTProto','tor':'Tor · obfs4','ssh':'SSH Tunnel','dnstt':'dnstt · DNS'}.get(i['id'],i['title'])
def port(i): return i['port'].replace(' (سرور)','')
FA_DIG=str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹')
out={}
# ---------------- banner
W,H=1280,420;cx,cy=300,214
b=[f'<defs>{girih("gp",LIME,0.07)}<radialGradient id="glow" cx="23%" cy="50%" r="45%"><stop offset="0" stop-color="{LIME}" stop-opacity=".22"/><stop offset="1" stop-color="{LIME}" stop-opacity="0"/></radialGradient><linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{INK}" stop-opacity="0"/><stop offset=".55" stop-color="{INK}" stop-opacity=".2"/><stop offset="1" stop-color="{INK}" stop-opacity=".92"/></linearGradient></defs>',
   f'<rect width="{W}" height="{H}" rx="28" fill="{INK}"/><rect width="{W}" height="{H}" rx="28" fill="url(#gp)"/><rect width="{W}" height="{H}" rx="28" fill="url(#glow)"/><rect width="{W}" height="{H}" rx="28" fill="url(#fade)"/>']
order=[i for g in GROUPS for i in cat if grp(i)==g[0]]
rings=[(78,6,'s1',40),(128,10,'s2',70),(178,14,'s3',110)]
k=0
for r,n,cls,dur in rings:
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LIME}" stroke-opacity=".22" stroke-dasharray="2 7"/>')
    g=[f'<g class="{cls}">']
    for j in range(n):
        a=2*math.pi*j/n+(0.3*rings.index((r,n,cls,dur)))
        x=cx+r*math.cos(a);y=cy+r*math.sin(a);it=order[k];k+=1;col=GC[grp(it)]
        fill=LIME if grp(it)=='direct' else ('#e9a066' if grp(it)=='cdn' else ('#8fc3d6' if grp(it)=='classic' else ('#c3cf6a' if grp(it)=='tools' else '#e08a7f')))
        g.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{fill}" stroke-opacity=".10"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{7 if r>100 else 8}" fill="{INK}" stroke="{fill}" stroke-width="2.4"/><circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{fill}"/>')
    g.append('</g>');b.append(''.join(g))
b.append(f'<circle class="pulse" cx="{cx}" cy="{cy}" r="46" fill="none" stroke="{LIME}" stroke-width="2"/>')
b.append(f'<path d="M{cx-36} {cy-30} q0 -16 16 -16 h40 q16 0 16 16 v44 q0 16 -16 16 h-40 q-16 0 -16 -16 z" transform="translate(-2 2)" fill="{LIME}"/>')
b.append(T(cx-2,cy+16,'گـ',42,800,GREEN,'middle'))
RX=1210
b.append(T(RX,96,'SELF-HOSTED  ·  MULTI-PROTOCOL  ·  PERSIAN PANEL',13,600,LIME,rtl=False,ls=2.6))
b.append(f'<text x="{RX}" y="186" text-anchor="end" style="font-family:SabiV,Vazirmatn,sans-serif;font-size:94px;font-weight:900;letter-spacing:-1px" fill="{PAPER}">SABI <tspan fill="{LIME}">ALL</tspan> VPN</text>')
b.append(T(RX,246,'یک دستور، سی کارت اتصال، یک پنل خصوصی فارسی',31,700,PAPER))
b.append(T(RX,284,'نصب خودکار روی سرور تازهٔ Ubuntu یا ساخت خودکار سرور در AWS',18,400,'#a9bbb4'))
chips=[('MIT',None),('AWS + Cloudflare',None),('Ubuntu 24.04',None),('v1.0.0-beta.3',ORANGE)]
x=RX
for t,c in chips:
    w=int(len(t)*8.6+30);x0=x-w
    if c: b.append(f'<rect x="{x0}" y="316" width="{w}" height="34" rx="17" fill="{c}"/>'+T(x0+w/2,338,t,14,700,PAPER,'middle',rtl=False))
    else: b.append(f'<rect x="{x0}" y="316" width="{w}" height="34" rx="17" fill="none" stroke="{LIME}" stroke-opacity=".45"/>'+T(x0+w/2,338,t,14,600,LIME,'middle',rtl=False))
    x=x0-10
b.append(f'<rect x="{x-138}" y="316" width="128" height="34" rx="17" fill="{LIME}"/>'+T(x-74,339,'نسخهٔ آزمایشی',14,800,GREEN,'middle'))
css='.s1,.s2,.s3{transform-origin:%dpx %dpx}.s1{animation:spin 40s linear infinite}.s2{animation:spin 70s linear infinite reverse}.s3{animation:spin 110s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.pulse{transform-origin:%dpx %dpx;animation:pulse 3.2s ease-out infinite}@keyframes pulse{0%%{transform:scale(1);opacity:.7}100%%{transform:scale(2.3);opacity:0}}'%(cx,cy,cx,cy)
out['banner.svg']=wrap(W,H,''.join(b),'SABI ALL VPN','بنر پروژه: سی کارت اتصال در پنج گروه دور یک سرور',css)
# ---------------- protocol map
W=1280;cols=5;cw=184;gap=12;right=1052;top=176
p=[f'<defs>{girih("gp2",GREEN,0.05,88)}</defs><rect width="{W}" height="HH" rx="28" fill="{PAPER}"/><rect width="{W}" height="HH" rx="28" fill="url(#gp2)"/>']
p.append(T(1220,78,'نقشهٔ اتصال‌ها',38,900,INK))
p.append(T(1220,118,'سی کارت در پنج گروه؛ هر نصب کلید و رمز تازهٔ خودش را می‌سازد',17,400,MUTED))
p.append(T(60,70,'PROTOCOL MAP',13,700,GREEN,'start',rtl=False,ls=3))
p.append(T(60,104,'30',44,900,INK,'start',rtl=False)+T(118,104,'cards · 5 groups',16,500,MUTED,'start',rtl=False))
p.append(f'<line x1="60" y1="146" x2="1220" y2="146" stroke="{LINE}"/>')
y=top
for gid,name,lat,col in GROUPS:
    items=[i for i in cat if grp(i)==gid]
    rows=math.ceil(len(items)/cols);hh=rows*86+(rows-1)*gap
    p.append(f'<rect x="1072" y="{y}" width="148" height="{hh}" rx="16" fill="{col}"/>')
    p.append(T(1204,y+33,name,17,800,WHITE))
    p.append(T(1204,y+52,lat,10,700,WHITE,rtl=False,ls=1.6,extra='fill-opacity=".72"'))
    p.append(T(1204,y+hh-12,str(len(items)).translate(FA_DIG)+' کارت',14,700,WHITE))
    for j,it in enumerate(items):
        r_,c_=divmod(j,cols);x1=right-c_*(cw+gap);x0=x1-cw;yy=y+r_*(86+gap)
        dash=' stroke-dasharray="6 5"' if gid=='optional' else ''
        p.append(f'<g class="card"><rect x="{x0}" y="{yy}" width="{cw}" height="86" rx="14" fill="{WHITE}" stroke="{col if gid=="optional" else LINE}"{dash}/><rect x="{x1-6}" y="{yy+14}" width="6" height="58" rx="3" fill="{col}"/>')
        t=title(it);sz=16 if len(t)<=17 else 15
        p.append(T(x1-18,yy+36,t,sz,700,INK,rtl=False))
        p.append(T(x1-18,yy+64,port(it),13,600,col,fam='M',rtl=False))
        if gid=='optional': p.append(T(x0+14,yy+64,'خاموش',11,700,RED,'start'))
        p.append('</g>')
    y+=hh+30
p.append(f'<line x1="60" y1="{y}" x2="1220" y2="{y}" stroke="{LINE}"/>')
p.append(T(1220,y+40,'پیش‌فرض ۲۷ کارت است؛ PPTP و پروکسی خام SOCKS/HTTP فقط با انتخاب آگاهانه فعال می‌شوند.',15,500,MUTED))
p.append(T(60,y+40,'ports are defaults of this installer',12,500,MUTED,'start',rtl=False))
HH=y+76
out['protocols.svg']=wrap(W,HH,''.join(p).replace('HH',str(HH)),'SABI ALL VPN protocol map','سی کارت اتصال: مستقیم، کلودفلر، کلاسیک، ابزارها و اختیاری، با پورت پیش‌فرض',
 '.card{animation:rise .6s ease-out both}@keyframes rise{from{opacity:0;transform:translateY(6px)}}')
# ---------------- install flow
W,H=1280,640
f=[f'<defs>{girih("gp3",LIME,0.06)}<marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="{LIME}"/></marker></defs><rect width="{W}" height="{H}" rx="28" fill="{INK}"/><rect width="{W}" height="{H}" rx="28" fill="url(#gp3)"/>']
f.append(T(1220,50,'مسیر نصب خودکار',30,900,PAPER)+T(60,46,'INSTALL FLOW',13,700,LIME,'start',rtl=False,ls=3))
snake='M1060 150 V214 M660 150 V190 Q660 214 700 214 H1020 M880 254 H700 M480 254 H300 M120 290 V352 H1176 V482 M1176 520 V540'
f.append(f'<path d="M1060 150 V214" class="flow" stroke="{LIME}" stroke-width="2.4" fill="none" marker-end="url(#ar)"/>')
f.append(f'<path d="M800 150 V174 Q800 190 816 190 H984 Q1000 190 1000 206 V210" class="flow" stroke="{LIME}" stroke-width="2.4" fill="none" marker-end="url(#ar)"/>')
f.append(f'<path d="M880 254 H844 M484 254 H444" class="flow" stroke="{LIME}" stroke-width="2.4" fill="none" marker-end="url(#ar)"/>')
f.append(f'<path d="M262 294 V336 Q262 350 248 350 H94 Q80 350 80 364 V376" class="flow" stroke="{LIME}" stroke-width="2.4" fill="none" marker-end="url(#ar)"/>')
def box(x0,y0,w,h,l1,l2,fill='#1c3d3a',stroke=LIME,so=.35,c1=PAPER,c2=LIME,mono2=True):
    s=f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{stroke}" stroke-opacity="{so}"/>'
    s+=T(x0+w-22,y0+35,l1,19,800,c1)
    s+=T(x0+w-22,y0+h-18,l2,14,600,c2,fam='M' if mono2 else 'V',rtl=not mono2)
    return s
f.append(box(880,70,360,80,'سرور آماده دارید','bootstrap.sh'))
f.append(T(860,116,'یا',16,700,'#a9bbb4','middle'))
f.append(box(480,70,360,80,'سرور را در AWS بسازد','bootstrap.sh --aws',stroke=ORANGE,so=.9,c2='#e9a066'))
f.append(T(500,172,'aws_provision.py  ›  EC2 · Elastic IP · SSM',12,500,'#a9bbb4','start',fam='M',rtl=False))
f.append(box(880,214,360,80,'نصب‌کننده و پیش‌بررسی','install.sh · preflight.py'))
f.append(box(480,214,360,80,'پرسش‌های اولیه','configure.py · DNS · token (hidden)'))
f.append(box(80,214,360,80,'ادامه در پس‌زمینه','systemd · checkpoint · --resume'))
mods=[('00','پایه','base'),('10','هستهٔ پروکسی','Xray · sing-box'),('20','کلاسیک','WG · OVPN · IPsec'),('30','افزونه‌ها','AWG · OC · Tor'),('40','سافت‌اتر','SoftEther'),('45','اختیاری','PPTP'),('50','فایل کلاینت','configs'),('60','پنل فارسی','Flask · nginx'),('70','فایروال','iptables')]
mw=116;mg=14;x=80
for i,(n,l,s) in enumerate(mods):
    opt=n=='45'
    f.append(f'<g class="mod" style="animation-delay:{i*0.12:.2f}s"><rect x="{x}" y="380" width="{mw}" height="104" rx="14" fill="{"none" if opt else "#1c3d3a"}" stroke="{RED if opt else LIME}" stroke-opacity="{1 if opt else .3}"{" stroke-dasharray=\"6 5\"" if opt else ""}/>')
    f.append(T(x+mw/2,412,n,20,800,'#e08a7f' if opt else LIME,'middle',fam='M',rtl=False))
    f.append(T(x+mw/2,444,l,15,800,PAPER,'middle'))
    f.append(T(x+mw/2,468,s,10.5,500,'#a9bbb4','middle',fam='M',rtl=False)+'</g>')
    if i<8: f.append(f'<path d="M{x+mw+1} 432 H{x+mw+mg-2}" stroke="{LIME}" stroke-width="2" marker-end="url(#ar)"/>')
    x+=mw+mg
f.append(f'<path d="M{x-mg-mw/2} 486 V520" class="flow" stroke="{LIME}" stroke-width="2.4" fill="none" marker-end="url(#ar)"/>')
f.append(f'<rect x="880" y="526" width="360" height="74" rx="18" fill="{LIME}"/>'+T(1218,560,'پنل خصوصی فارسی',20,900,GREEN)+T(1218,584,'https://SUBDOMAIN:9444',13,600,GREEN,fam='M',rtl=False))
f.append(f'<rect x="480" y="526" width="360" height="74" rx="18" fill="{PAPER}"/>'+T(818,560,'ZIP خصوصی کامل',20,900,INK)+T(818,584,'/root/allvpn/export/',13,600,GREEN,fam='M',rtl=False))
f.append(f'<rect x="80" y="526" width="360" height="74" rx="18" fill="none" stroke="#a9bbb4" stroke-opacity=".5"/>'+T(418,560,'گزارش وضعیت سرویس‌ها',18,800,PAPER)+T(418,584,'doctor.py · health.py',13,600,'#a9bbb4',fam='M',rtl=False))
f.append(f'<path d="M880 563 H844 M480 563 H444" stroke="#a9bbb4" stroke-opacity=".5" stroke-width="2" stroke-dasharray="3 5"/>')
out['install-flow.svg']=wrap(W,H,''.join(f),'SABI ALL VPN install flow','دو ورودی bootstrap که به install.sh، نُه ماژول و خروجی پنل و ZIP می‌رسند',
 '.flow{stroke-dasharray:7 7;animation:dash 1.6s linear infinite}@keyframes dash{to{stroke-dashoffset:-28}}.mod{animation:rise .7s ease-out both}@keyframes rise{from{opacity:0;transform:translateY(8px)}}')
# ---------------- panel mockup (synthetic data only)
W,H=1280,800
m=[f'<defs><clipPath id="win"><rect x="0" y="0" width="{W}" height="{H}" rx="22"/></clipPath><filter id="sh" x="-10%" y="-10%" width="120%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#142f2d" flood-opacity=".18"/></filter></defs><g clip-path="url(#win)"><rect width="{W}" height="{H}" fill="{PAPER}"/>']
m.append(f'<rect width="{W}" height="48" fill="#e4e6dc"/><circle cx="26" cy="24" r="6" fill="#d07a5c"/><circle cx="46" cy="24" r="6" fill="#d9b25a"/><circle cx="66" cy="24" r="6" fill="#8bab6a"/><rect x="380" y="11" width="520" height="26" rx="13" fill="{WHITE}"/>'+f'<g transform="translate(530 15)" fill="none" stroke="{GREEN}" stroke-width="1.6"><rect x="0" y="7" width="11" height="9" rx="2"/><path d="M2.5 7V4.5a3 3 0 0 1 6 0V7"/></g>'+T(648,29,'https://vpn.example.com:9444',13,500,MUTED,'middle',fam='M',rtl=False))
m.append(f'<rect x="1038" y="48" width="242" height="{H-48}" fill="#eeefe6"/><line x1="1038" y1="48" x2="1038" y2="{H}" stroke="{LINE}"/>')
m.append(f'<path d="M1206 82 h34 q16 0 16 16 v19 q0 16 -16 16 h-34 q-16 0 -16 -4 v-31 q0 -16 16 -16z" fill="{GREEN}"/>'+T(1224,121,'گـ',30,800,LIME,'middle'))
m.append(T(1178,108,'گذرگاه',24,800,INK)+T(1178,126,'SABI ALLVPN · PRIVATE',8,600,INK,fam='M',rtl=False,ls=1))
navs=[('اتصال‌ها','30',True),('فایل‌ها','24',False),('گاوصندوق','vault',False),('راهنما و امنیت','?',False)]
yy=176
m.append(f'<line x1="1062" y1="160" x2="1256" y2="160" stroke="{LINE}"/>')
for n,c,act in navs:
    if act: m.append(f'<rect x="1058" y="{yy}" width="202" height="42" rx="8" fill="#dce4d3"/>')
    m.append(T(1244,yy+27,n,14,800 if act else 500,GREEN if act else '#596760')+T(1072,yy+27,c,11,500,MUTED,'start',fam='M',rtl=False))
    yy+=50
m.append(T(1250,600,'هر مقدار،',28,500,INK)+T(1250,642,'یک کلیک تا کپی.',28,500,INK)+T(1250,676,'رمزها به‌صورت پیش‌فرض پنهان‌اند.',12,400,MUTED))
m.append(f'<line x1="1062" y1="730" x2="1256" y2="730" stroke="{LINE}"/>'+T(1250,760,'خروج',12,500,INK))
m.append(f'<line x1="44" y1="130" x2="994" y2="130" stroke="{LINE}"/>'+T(994,82,'کتابخانهٔ اتصال',24,900,INK)+T(994,112,'سرور نمایشی · دادهٔ ساختگی',12,500,MUTED))
m.append(f'<rect x="44" y="70" width="300" height="40" rx="20" fill="{WHITE}" stroke="{LINE}"/>'+T(320,96,'جستجوی پروتکل…',13,400,MUTED))
chipsF=[('همه ۳۰',True),('Cloudflare',False),('مستقیم',False),('VPN کلاسیک',False),('ابزارهای دیگر',False)]
x=994
for t,a in chipsF:
    w=len(t)*8+34;x0=x-w
    m.append(f'<rect x="{x0}" y="150" width="{w}" height="34" rx="17" fill="{INK if a else WHITE}" stroke="{INK if a else LINE}"/>'+T(x0+w/2,172,t,13,700 if a else 500,LIME if a else INK,'middle'))
    x=x0-8
cards=[('direct','VLESS · REALITY / Xray','مستقیم',[('آدرس','vpn.example.com'),('پورت','443 / TCP'),('UUID','••••••••-••••')]),
       ('direct','Hysteria 2','مستقیم',[('آدرس','192.0.2.10'),('پورت','443 / UDP'),('رمز','••••••••••••')]),
       ('cdn','VLESS · WS / CDN','پشت کلودفلر',[('میزبان','cdn.example.com'),('پورت','2053 / TCP'),('مسیر','/ws-••••')]),
       ('classic','WireGuard','کلاسیک',[('فایل','wg-client.conf'),('پورت','51820 / UDP'),('کلید','••••••••••••')]),
       ('classic','OpenVPN · UDP','کلاسیک',[('فایل','client-udp.ovpn'),('پورت','1194 / UDP'),('CA','embedded')]),
       ('tools','MTProto · Telegram','ابزار',[('لینک','tg://proxy?…'),('پورت','4433 / TCP'),('رمز','••••••••••••')])]
cw2,ch2=304,236;gx=19
for i,(g,t,lab,fields) in enumerate(cards):
    r_,c_=divmod(i,3);x1=994-c_*(cw2+gx);x0=x1-cw2;y0=208+r_*(ch2+20);col=GC[g]
    m.append(f'<g class="mc" style="animation-delay:{i*0.08:.2f}s"><rect x="{x0}" y="{y0}" width="{cw2}" height="{ch2}" rx="18" fill="{WHITE}" stroke="{LINE}" filter="url(#sh)"/>')
    m.append(f'<circle cx="{x1-24}" cy="{y0+28}" r="5" fill="{col}"/>'+T(x1-36,y0+33,lab,12,700,col)+T(x0+20,y0+33,'active',11,600,'#5f8f3a','start',fam='M',rtl=False))
    m.append(T(x1-20,y0+66,t,18,800,INK,rtl=False))
    fy=y0+86
    for k2,(l,v) in enumerate(fields):
        hl=(i==0 and k2==0)
        m.append(f'<rect x="{x0+16}" y="{fy}" width="{cw2-32}" height="36" rx="10" fill="{"#eef3d0" if hl else PAPER}" stroke="{"#99b434" if hl else "none"}"/>')
        m.append(T(x1-28,fy+23,l,12,600,MUTED)+T(x0+52,fy+23,v,13,600,INK,'start',fam='M',rtl=False))
        m.append(f'<g transform="translate({x0+26} {fy+10})" fill="none" stroke="{GREEN}" stroke-width="1.6"><rect x="4" y="0" width="11" height="13" rx="2"/><path d="M1 4v11h10"/></g>')
        fy+=42
    m.append(T(x1-20,y0+ch2-14,'آموزش قدم‌به‌قدم',12,700,GREEN)+'</g>')
m.append(f'<path d="M232 316 l0 22 l6 -6 l5 11 l4 -2 l-5 -10 l8 0 z" fill="{INK}" stroke="{WHITE}" stroke-width="1.5"/>')
m.append(f'<g class="toast"><rect x="440" y="720" width="160" height="44" rx="22" fill="{INK}"/>'+T(536,748,'کپی شد',15,800,LIME,'middle')+f'<path d="M480 742 l6 6 l12 -13" fill="none" stroke="{LIME}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'+'</g>')
m.append(f'<rect x="44" y="722" width="236" height="44" rx="22" fill="{ORANGE}"/>'+T(258,750,'تصویر نمایشی · دادهٔ ساختگی',14,800,WHITE)+T(380,96,'',1))
m.append('</g>')
out['panel-mockup.svg']=wrap(W,H,''.join(m),'Illustrative SABI panel mockup','تصویر نمایشی پنل با دادهٔ ساختگی: vpn.example.com و 192.0.2.10؛ اسکرین‌شات واقعی نیست',
 '.mc{animation:rise .6s ease-out both}@keyframes rise{from{opacity:0;transform:translateY(8px)}}.toast{animation:toast 4s ease-in-out infinite}@keyframes toast{0%,15%{opacity:0}25%,75%{opacity:1}90%,100%{opacity:0}}')
# ---------- font subset + embed
for s in out.values(): track(s)
CHARS.update(' ‌')
opts=subset.Options();opts.flavor='woff2';opts.layout_features=['*'];opts.name_IDs=['*'];opts.notdef_outline=True
ft=TTFont(str(FONT));print('variable' if 'fvar' in ft else 'static', ft['name'].getDebugName(1))
sub=subset.Subsetter(opts);sub.populate(text=''.join(CHARS));sub.subset(ft)
buf=io.BytesIO();ft.flavor='woff2';ft.save(buf);b64=base64.b64encode(buf.getvalue()).decode()
facecss="@font-face{font-family:SabiV;src:url(data:font/woff2;base64,%s) format('woff2');font-weight:100 900}"%b64
for name,s in out.items():
    (A/name).write_text(s.replace('/*FONT*/',facecss)); print(name,len(s.replace('/*FONT*/',facecss))//1024,'KB')
