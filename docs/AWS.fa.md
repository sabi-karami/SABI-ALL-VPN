# AWS: ساخت، ادامه و حذف

## پیش‌نیاز

Bash و دسترسی sudo روی ماشین مدیریت (Linux، WSL یا macOS). اگر curl، Python 3 یا venv نباشند، bootstrap آن‌ها را با apt/dnf/yum/zypper/apk/pacman/Homebrew خودکار نصب می‌کند (فقط پیش‌نیازها: `bootstrap.sh --deps-only --aws`)؛ احراز هویت استاندارد boto3 مانند AWS CLI profile / SSO. توکن یا secret key را در آرگومان دستور، مخزن یا چت نگذارید.

نمونه با profile از قبل تنظیم‌شده:

```bash
AWS_PROFILE=my-profile bash <(curl -fsSL https://raw.githubusercontent.com/sabi-karami/SABI-ALL-VPN/v1.0.0-beta.4/bootstrap.sh) --aws --region us-east-2
```

رمز Cloudflare به‌صورت ورودی پنهان ترمینال خوانده می‌شود؛ هیچ کلید AWS در کد نیست.

## منابع ساخته‌شده

- یک EC2 Ubuntu 24.04 amd64؛ حداقل ۲ GiB RAM؛ پیش‌فرض t3.small.
- ۳۰ GiB gp3 رمزنگاری‌شده؛ public IPv4 ثابت / Elastic IP.
- security group با پورت‌های سرویس؛ SSH و پنل محدود به CIDR انتخابی.
- role/profile برای SSM؛ instance metadata از نوع IMDSv2.
- **default VPC و subnet عمومی لازم‌اند**؛ اسکریپت VPC/IGW/NAT Gateway جدید نمی‌سازد.
- یک SSM Parameter Store از نوع SecureString فقط برای bootstrap؛ بعد از دریافت پاک می‌شود.

توکن Cloudflare برای تمدید ACME در فایل root-only روی سرور می‌ماند. آن را به Zone موردنظر محدود کنید. نقش EC2 پس از bootstrap فقط دسترسی مدیریت SSM موردنیاز را نگه می‌دارد؛ حذف سرویس مدیریت به‌طور خودکار انجام نمی‌شود.

## مجوزهای حساب اجراکننده

فراخوانی‌های خواندن EC2/SSM/STS، ساخت و حذف EC2/EIP/SG، تغییر SourceDestCheck، ایجاد/مدیریت role/profile IAM با PassRole، policy موردنیاز SSM، Put/Get/DeleteParameter و SendCommand/GetCommandInvocation لازم‌اند. با محدودکردن منابع به پیشوند `sabi-allvpn-*` و permission boundary سازمانتان مجوز مناسب تهیه کنید. پروژه policy ادمین به حساب شما اضافه نمی‌کند و SCP/region restriction را تغییر نمی‌دهد.

## هزینه و حفاظت

تأیید `CREATE` پیش از ساخت منابع گرفته می‌شود. هزینهٔ EC2، EBS، IPv4 و خروجی شبکه ادامه می‌یابد. اعتبار رایگان یا مقدار ترافیک رایگان فرض نشده است. AWS Budgets هشدار است، نه قطع تضمینی هزینه. این نسخه سقف ترافیک/هزینهٔ اجباری ندارد.

فایل حالت محلی:

```text
~/.local/state/sabi-allvpn/aws-state.json
```

برای استقرار دوم، `--state /مسیر/حالت-دیگر.json` بدهید. همان state به‌صورت پیش‌فرض مانع ساخت تصادفی استقرار جدید می‌شود. در صورت failure، منابع حذف نمی‌شوند تا بتوانید اشکال را بررسی کنید؛ ممکن است هزینه ادامه پیدا کند.

ادامه:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sabi-karami/SABI-ALL-VPN/v1.0.0-beta.4/bootstrap.sh) --aws --resume
```

اگر bootstrap قبلاً راه افتاده، ادامهٔ نصب روی سرور با `sudo bash /opt/sabi-allvpn/install.sh --resume` است. گزینهٔ `--resume` محلی دوباره instance جدید نمی‌سازد.

حذف صریح منابع ثبت‌شده پس از تهیهٔ پشتیبان:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sabi-karami/SABI-ALL-VPN/v1.0.0-beta.4/bootstrap.sh) --aws --delete
```

حذف به تأیید `DELETE` نیاز دارد؛ EC2 با دیسک آن، EIP، SG و role/profile این deployment را حذف می‌کند. رکوردهای Cloudflare عمداً خودکار حذف نمی‌شوند؛ با فهرست `/var/lib/sabi-allvpn/dns-created.json` تطبیق دهید و فقط رکوردهای همین deployment را پاک کنید. این ابزار جایگزین بررسی Billing/EC2 console نیست.

## دریافت فایل‌ها از AWS

در Systems Manager → Session Manager به instance متصل شوید. پیشرفت در `/var/log/sabi-allvpn-install.log` و ورود پنل در `/root/allvpn/panel-access.txt` است. برای انتقال archive از روش مدیریتی امن خودتان (SSH با کلید ادمین، انتقال کنترل‌شده به S3 خصوصی یا انتقال فایل سازمانی) استفاده کنید. کاربر `tunnel` فقط forwarding دارد؛ دسترسی root به آن داده نمی‌شود.
