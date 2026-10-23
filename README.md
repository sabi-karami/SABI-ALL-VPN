# گذرگاه SABI ALLVPN

کتابخانهٔ خصوصی اتصال + نصب‌کنندهٔ چندروشی روی سرور اختصاصی.

**نسخهٔ آزمایشی `v1.0.0-beta.1` — Ubuntu 24.04 / x86-64 فقط.**

> این پروژه نصب مجموعهٔ مشخص‌شدهٔ پایین را خودکار می‌کند؛ «تمام پروتکل‌های VPN دنیا» نیست. ۳۰ کارت پنل شامل حالت‌های مختلف یک پروتکل است، نه ۳۰ استاندارد مستقل. کلیدها و رمزهای واقعی هیچ سرور در این مخزن عمومی نیستند.

## دو دستور به انتخاب شما

### ۱. سرور آماده دارید

روی **سرور تازهٔ Ubuntu 24.04 amd64** وارد SSH شوید. `curl` و Python 3 باید نصب باشند:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sabi-karami/sabi-allvpn/v1.0.0-beta.1/bootstrap.sh)
```

اسکریپت در صورت نیاز `sudo` می‌خواهد. نام دامنه، پیشوند ساب‌دامین‌ها، IPv4 و تنظیم DNS را می‌پرسد. در حالت Cloudflare، توکن را **فقط در ورودی مخفی ترمینال خودتان** وارد کنید؛ نه در چت، دستور shell، فایل عمومی یا GitHub.

### ۲. می‌خواهید سرور AWS هم ساخته شود

روی Linux/WSL یا محیط دارای **Bash، curl، Python 3 + venv** و حساب AWS از قبل احراز هویت‌شده اجرا کنید:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sabi-karami/sabi-allvpn/v1.0.0-beta.1/bootstrap.sh) --aws
```

از زنجیرهٔ استاندارد اعتبارنامهٔ boto3 (مانند AWS profile یا SSO) استفاده می‌شود. این فرمان **پس از تأیید `CREATE` هزینه‌زا است**: EC2، EBS، IPv4 ثابت و ترافیک. منطقهٔ پیش‌فرض `us-east-2` است و قابل انتخاب است؛ محدودیت SCP/Quota دور زده نمی‌شود.

> یک خط، به معنی «بدون ورودی یا مجوز» نیست. برای حالت AWS به مجوز ایجاد EC2، IAM role/profile، SSM و یک VPC پیش‌فرض با subnet عمومی نیاز دارید. قیمت ثابت یا سقف هزینهٔ خودکار وجود ندارد.

### روش قابل‌ممیزی‌تر

اجرای کد اینترنت با دسترسی root ریسک دارد. پیش از اجرا کد را بررسی کنید؛ نسخهٔ مشخص بهتر از شاخهٔ متغیر `main` است:

```bash
curl -fL https://github.com/sabi-karami/sabi-allvpn/archive/refs/tags/v1.0.0-beta.1.tar.gz -o sabi-source.tgz
tar -xzf sabi-source.tgz
cd sabi-allvpn-1.0.0-beta.1
sha256sum -c MANIFEST.sha256
sudo bash install.sh
```

`MANIFEST.sha256` برای تشخیص تغییر و خرابی فایل‌هاست؛ امضای مستقل یا تضمین اعتماد به ناشر نیست.

## چه چیزی نصب می‌شود؟

| گروه | موارد |
|---|---|
| Xray / مستقیم | VLESS-REALITY روی 443، Trojan-TLS، Shadowsocks-2022 |
| sing-box / مستقیم | REALITY سازگار sing-box روی 3443، Hysteria2، TUIC، ShadowTLS v3 + SS2022، AnyTLS، Naive |
| Cloudflare | VLESS-WS، VLESS-XHTTP، VMess-WS، Trojan-WS |
| VPN کلاسیک | WireGuard، AmneziaWG، OpenVPN UDP/TCP، IKEv2، L2TP/IPsec، IPsec-XAuth، OpenConnect، SSTP/SoftEther |
| ابزارها | MTProto تلگرام، پل خصوصی Tor/obfs4، dnstt، SSH SOCKS tunnel |
| اختیاری و پیش‌فرض خاموش | PPTP ناامن؛ پروکسی خام SOCKS5/HTTP روی 1080 |

PPTP و پروکسی خام را فقط اگر آگاهانه لازم دارید فعال کنید. انتخاب هر دو، مجموعهٔ حداکثری ۳۰ کارت را می‌دهد؛ پیش‌فرض ۲۷ کارت است. هر نصب کلید و رمز تازه می‌سازد؛ فایل یک سرور روی سرور دیگر بازاستفاده نمی‌شود.

**نصب نمی‌شوند:** NordLynx و پروتکل‌های اختصاصی خدمات تجاری، MPLS/EVPN و زیرساخت اپراتوری، شبکه‌های Mesh، Psiphon، I2P، MASQUE و هر مورد خارج از فهرست بالا.

## پنل خصوصی فارسی

- `https://SUBDOMAIN:9444`
- نام کاربری پیش‌فرض `sabi`؛ قابل انتخاب در wizard سرور آماده.
- رمز اولیهٔ تصادفی؛ حداقل طول رمز قابل تغییر ۸ نویسه (ترکیب طولانی‌تر توصیه می‌شود).
- کلیک برای کپی اطلاعات، پنهان/نمایش رمز، فیلتر، آموزش هر مورد، دانلود و پیش‌نمایش فایل‌ها.
- ورود امن، cookie با Secure/HttpOnly/SameSite، CSRF، محدودیت تلاش ورود و no-store.
- وضعیت سرویس تقریباً هر دقیقه؛ **این وضعیت، تست اتصال از اینترنت کاربر نیست**.
- پنل read-only است: ساخت کاربر، فروش اشتراک، حسابداری مصرف و محدودیت حجم ندارد.

دیدن اطلاعات اولیه روی سرور:

```bash
sudo cat /root/allvpn/panel-access.txt
```

پس از اولین ورود رمز را از «راهنما و امنیت» تغییر دهید. فایل بالا رمز اولیه است و پس از تغییر به‌روز نمی‌شود.

## نصب چگونه ادامه پیدا می‌کند؟

نصب بعد از پرسش‌های اولیه در سرویس systemd جدا ادامه می‌یابد؛ بستن SSH به‌تنهایی نصب را متوقف نمی‌کند:

```bash
sudo tail -f /var/log/sabi-allvpn-install.log
sudo systemctl status sabi-allvpn-install
```

خطا را اصلاح و همان نصب را ادامه دهید:

```bash
sudo bash /opt/sabi-allvpn/install.sh --resume
```

checkpoint در `/var/lib/sabi-allvpn/done/` ثبت می‌شود. مراحل موفق رد می‌شوند. مرحلهٔ شکست‌خورده ممکن است تغییر جزئی انجام داده باشد؛ این پروژه تراکنش یا rollback کامل همهٔ نرم‌افزارهای ثالث نیست. روی سرور دارای سرویس دیگر اجرا نکنید.

## ZIP خصوصی کامل

پس از تکمیل:

```text
/root/allvpn/export/allvpn-private.zip
```

شامل فایل‌های کلاینت، راهنمای فارسی، رمزهای VPN، پشتیبان تنظیمات سرور، کلیدهای خصوصی و **رمز اولیهٔ پنل** است. شامل کلید API AWS/Cloudflare نیست. ZIP رمزنگاری‌شده نیست؛ خودتان در محل امن نگه دارید. **هرگز در GitHub عمومی یا Release آپلود نکنید.**

دریافت از سرور:

```bash
scp admin@YOUR_SERVER:/path-you-securely-copied/allvpn-private.zip ./
```

فایل root-only است؛ با حساب ادمین به‌صورت کنترل‌شده کپی کنید. کاربر `tunnel` شِل/دسترسی مدیریتی ندارد. از Session Manager یا حساب مدیریت خود استفاده کنید. فایل‌های معمول اتصال نیز پس از ورود در پنل دانلود می‌شوند.

به‌روزرسانی خروجی پس از تغییر فایل‌ها:

```bash
sudo /opt/allvpn-panel/venv/bin/python /opt/allvpn-panel/build_files.py
sudo chown -R allvpn-panel:allvpn-panel /var/lib/allvpn-panel
sudo python3 /opt/sabi-allvpn/scripts/export_private.py
```

این کار configهای دلخواهی را که بعداً با دست ویرایش کرده‌اید به معنای «مهاجرت خودکار» تفسیر نمی‌کند. کاتالوگ متنی ممکن است نیازمند بازتولید توسط مدیر باشد.

## حد تست و ریسک‌ها

- syntax همهٔ Bash/Python، JSONهای اصلی، کنترل دسترسی پنل و مرز رمز ۷/۸ نویسه خودکار تست می‌شوند.
- پنل مبنا قبلاً با مرورگر دسکتاپ/موبایل و دانلود احراز هویت‌شده تست شده بود.
- **این نسخهٔ یکپارچه هنوز نصب کامل fresh-host و AWS provisioning انتهابه‌انتها را نگذرانده است.** ابتدا روی ماشین آزمایشی disposable استفاده کنید؛ نه تنها سرور مهمتان.
- هسته‌ها و source revisionها در `versions.lock.json` ثبت شده‌اند. بسته‌های apt، وابستگی‌های build و بعضی دانلودهای nested نصب‌کنندهٔ IPsec کاملاً قفل نشده‌اند؛ این یک build صددرصد reproducible نیست.
- گرفتن گواهی، تأخیر DNS، فیلترینگ، سیاست دیتاسنتر و تفاوت کلاینت‌ها ممکن است باعث خطا شوند.
- IPv4 در اولویت است؛ مسیر IPv6 داخل فایل‌های جدید WG/AWG تنظیم نشده. برای جلوگیری از خروج IPv6 خارج تونل، IPv6 را روی کلاینت مدیریت/مسدود کنید؛ تضمین جلوگیری از نشت وجود ندارد.

## مستندات کامل

- [آموزش فارسی همهٔ روش‌ها](docs/PROTOCOLS.fa.md)
- [AWS، دسترسی‌ها، هزینه و حذف](docs/AWS.fa.md)
- [Cloudflare، دامنه و TLS](docs/CLOUDFLARE.fa.md)
- [پورت‌ها و شبکه](docs/PORTS.md)
- [ادامهٔ نصب، عیب‌یابی، بازیابی](docs/OPERATIONS.fa.md)
- [امنیت و سیاست رمزها](SECURITY.md)
- [نسخه‌ها و انتساب پروژه‌های ثالث](THIRD_PARTY.md)
- [گزارش آزمون](docs/TESTING.md)

## مجوز

کد هماهنگ‌کننده و پنل این مخزن MIT است؛ پروژه‌های ثالث مجوزهای خودشان را دارند. فونت Vazirmatn تحت SIL OFL است. این مخزن نرم‌افزارهای VPN را به نام خود بازنشر نمی‌کند و ادعای ممیزی امنیتی مستقل ندارد.
