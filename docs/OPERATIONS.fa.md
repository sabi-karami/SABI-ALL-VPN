# عملیات، عیب‌یابی و بازیابی

## مسیرها

| مسیر | کاربرد |
|---|---|
| `/opt/sabi-allvpn` | نسخهٔ installer استفاده‌شده |
| `/etc/sabi-allvpn` | ورودی‌های اعتبارسنجی‌شده؛ توکن Cloudflare فقط root |
| `/var/lib/sabi-allvpn/done` | checkpoint مراحل |
| `/root/allvpn/secrets.env` | رمزها و کلیدهای تولیدشدهٔ VPN |
| `/root/allvpn/clients` | کانفیگ‌های کلاینت |
| `/opt/allvpn-panel` | کد پنل |
| `/var/lib/allvpn-panel` | داده‌های خصوصی پنل، auth و فایل‌ها |
| `/root/allvpn/export` | ZIP خصوصی، هرگز public نشود |

## توقف و ادامه

`systemctl status sabi-allvpn-install` و log root-only را بررسی کنید. شکست در مرحلهٔ X موفقیت بقیهٔ مراحل را پاک نمی‌کند. بعد از رفع مشکل `sudo bash /opt/sabi-allvpn/install.sh --resume` را اجرا کنید.

برای اجرای دوبارهٔ یک مرحلهٔ کامل‌شده، ابتدا backup بگیرید، وابستگی‌ها را بررسی کنید و marker همان مرحله را آگاهانه حذف کنید. حذف همهٔ markerها یا اجرای دوباره روی سیستم تغییرکرده می‌تواند تنظیمات دست‌ساز را بازنویسی کند. rollback کامل خودکار وجود ندارد.

## بررسی

```bash
sudo python3 /opt/sabi-allvpn/scripts/doctor.py
sudo journalctl -u xray -u sing-box --since '10 minutes ago'
sudo journalctl -u allvpn-panel -u nginx --since '10 minutes ago'
sudo certbot certificates
sudo certbot renew --dry-run
```

لاگ upstream IPsec ممکن است رمزهای نصب را چاپ کند؛ به همین دلیل log خصوصی است. لاگ یا screenshot را بدون حذف رمزها در issue عمومی نگذارید.

## تغییر رمز پنل از سرور

```bash
sudo /opt/allvpn-panel/venv/bin/python /opt/sabi-allvpn/scripts/reset_panel_password.py
```

ورودی مخفی و حداقل ۸ نویسه است. نشست‌های قبلی باطل می‌شوند. فایل رمز اولیه و ZIPهای قدیمی تغییر نمی‌کنند و باید به‌عنوان اطلاعات تاریخ‌دار نگه داشته یا حذف شوند. فایل hash رمز به معنی قابل بازیابی بودن متن رمز جدید نیست.

## چه خطاهایی متداول‌اند؟

- **گواهی:** DNS نادرست، پورت 80 بسته در حالت manual، token scope ناقص، CA rate limit.
- **AWS:** SCP/region deny، نبود default VPC یا public subnet، کمبود quota، IAM propagation یا SSM offline.
- **TLS/CDN:** Flexible به‌جای Full(strict)، hostname غلط، WAF challenge یا proxy نامناسب برای UDP.
- **کلاینت:** XHTTP پشتیبانی نمی‌شود، نسخهٔ قدیمی SS2022، REALITY sing-box روی پورت 443 به‌جای 3443، Cronet موردنیاز Naive.
- **Kernel:** نبود TUN/PPP/GRE یا container بدون دسترسی لازم. از KVM/EC2 کامل استفاده کنید.
- **اتصال نیمه‌کاره:** UDP مسدود، NAT/MTU، route overlap یا IPv6 خارج تونل. خاموش‌کردن TLS verification راه‌حل نیست.

## بازیابی سرور جدید

مسیر توصیه‌شده: روی سرور تازه نصب جدید انجام دهید تا کلیدهای تازه بسازد؛ دامنه/رکوردهای جدید انتخاب کنید. ZIP قدیمی برای مراجعه و انتقال کنترل‌شدهٔ مدیر است. `server-configs-private.tgz` یک تصویر کامل دیسک نیست؛ فایل‌ها را کورکورانه روی سرور متفاوت استخراج نکنید.

اگر حفظ هویت قبلی لازم است: نسخه‌های سازگار، شبکه/دامنه/گواهی و مالکیت فایل‌ها را بررسی کنید؛ ابتدا سرویس مربوطه را متوقف، از وضعیت جدید backup و فقط فایل‌های همان سرویس را restore کنید. برای این نسخه فرمان restore خودکار تضمین‌شده ارائه نشده است.

## پاک‌کردن

برای AWS از ابزار --delete با state همان deployment و تأیید صریح استفاده کنید. برای VPS آماده، پس از export بهترین حذف کامل، rebuild/reimage سرور اختصاصی نزد ارائه‌دهنده است. اسکریپت حذف عمومی که ممکن است سرویس‌های دیگر را نابود کند عمداً ارائه نشده.
