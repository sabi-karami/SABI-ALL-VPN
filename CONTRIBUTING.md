# مشارکت در SABI ALL VPN / Contributing

از کمک شما ممنونیم 🌱 این پروژه **نسخهٔ آزمایشی** است؛ گزارش دقیق خطا و تست روی ماشین disposable بیشترین کمک را می‌کند.

## قانون طلایی: هیچ راز عمومی نمی‌شود

- رمز، کلید خصوصی، UUID، لینک اتصال، IP یا دامنهٔ واقعی، توکن API، `auth.json`، `.env` و ZIP خصوصی را **هرگز** commit نکنید و در Issue/PR نگذارید.
- در مثال‌ها فقط `vpn.example.com`، `cdn.example.com` و آدرس‌های مستند `192.0.2.0/24` را به کار ببرید.
- تصویر پنل واقعی منتشر نکنید؛ از `docs/assets/panel-mockup.svg` (دادهٔ ساختگی) استفاده کنید.
- آسیب‌پذیری امنیتی را فقط از [گزارش خصوصی](https://github.com/sabi-karami/SABI-ALL-VPN/security/advisories/new) بفرستید.

## راه‌اندازی محلی

```bash
git clone https://github.com/sabi-karami/SABI-ALL-VPN.git && cd SABI-ALL-VPN
python3 -m venv .venv && . .venv/bin/activate
pip install -r panel/requirements.txt
python -m unittest discover -s tests -v
node --check panel/static/app.js && node --check panel/static/login.js
```

## بازتولید MANIFEST

هر بار فایلی اضافه یا عوض شد (CI آن را بررسی می‌کند):

```bash
git ls-files -z | grep -zv '^MANIFEST.sha256$' | xargs -0 sha256sum > MANIFEST.sha256
sha256sum -c MANIFEST.sha256
```

فایل‌های جدید را پیش از اجرای دستور بالا `git add` کنید.

## گرافیک‌ها

تصاویر README و صفحهٔ معرفی SVG هستند و با یک اسکریپت ساخته می‌شوند (زیرمجموعهٔ فونت Vazirmatn داخل SVG جاسازی می‌شود):

```bash
pip install 'fonttools[woff]'
python3 docs/assets/build_assets.py
```

## سبک تغییرات

- اسکریپت‌های shell با `set -Eeuo pipefail`؛ بدون `set -x` در ماژول‌ها (رمزها در لاگ نروند).
- هر مرحلهٔ نصب باید با `--resume` قابل ادامه باشد.
- متن کاربر فارسی و روشن؛ محدودیت‌ها را صادقانه بنویسید و ادعای «تست‌شده» بدون مدرک نکنید.
- یک PR برای یک موضوع؛ چک‌لیست قالب PR را کامل کنید.

---

**English:** Run the unit tests and JS syntax checks above, regenerate `MANIFEST.sha256`, keep all examples synthetic (`example.com`, `192.0.2.0/24`), never commit secrets or real panel screenshots, and report vulnerabilities privately via GitHub security advisories.
