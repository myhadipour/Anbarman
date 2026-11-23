<div align="center">

<img src="docs/logo.png" alt="انبارمن" width="120"/>

# انبارمن

### نرم‌افزار حسابداری و انبارداری فروشگاه

مدیریت کالا، موجودی، فروش و فاکتور — همراه با قیمت دیجی‌کالا و نرخ ارز

<br/>

[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey?style=flat-square)](#)

<br/>

<img src="docs/preview.png" alt="محیط انبارمن" width="900"/>

</div>

---

## انبارمن چیست؟

**انبارمن** یک برنامه دسکتاپ برای فروشگاه‌های کوچک و متوسط است.  
با آن می‌توانید کالا و موجودی را ثبت کنید، فروش بزنید، فاکتور بسازید و آمار فروش را ببینید.

قیمت کالا از **دیجی‌کالا** قابل دریافت است و نرخ **دلار، درهم و طلا** هم در برنامه نمایش داده می‌شود.

---

## امکانات

| | |
|:--|:--|
| **کالا و انبار** | ثبت کالا، موجودی، بارکد، دسته و عکس |
| **فروش و فاکتور** | ثبت فروش، ساخت فاکتور و چاپ |
| **داشبورد** | خلاصه فروش امروز، هفته و ماه |
| **قیمت دیجی‌کالا** | به‌روزرسانی قیمت فروش از دیجی‌کالا |
| **نرخ ارز** | دلار آمریکا، درهم امارات، طلای ۱۸ عیار |
| **قیمت فروش** | مبلغ ثابت یا درصد سود روی خرید |

---

## اجرا

### با Setup (پیشنهادی)
فایل `Anbarman-Setup.exe` را از بخش [Releases](../../releases) دانلود و نصب کنید.

### نسخه Portable
`Anbarman-Portable.exe` را اجرا کنید — بدون نصب.

### با پایتون
```bash
# ویندوز: روی Run.bat دوبار کلیک کنید
# یا:
python anbarman.pyw
```
نیاز به **Python 3.10+** با پشتیبانی Tcl/Tk دارد.

---

## ساخت Setup با GitHub Actions

1. مخزن را Fork یا Push کنید  
2. به تب **Actions** بروید  
3. workflow به نام **Build Anbarman Windows Setup** را اجرا کنید  
4. از **Artifacts** فایل Setup و Portable را دانلود کنید  

با زدن تگ نسخه، فایل‌ها در **Releases** هم منتشر می‌شوند:

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## ساختار پروژه

```
anbarman/
├── assets/          # لوگو، آیکون، فونت
├── theme.py         # رنگ و استایل
├── icons.py         # آیکون‌ها
├── prices.py        # دریافت قیمت دیجی‌کالا
├── database.py      # پایگاه داده SQLite
├── jalali.py        # تاریخ شمسی
└── ui.py            # رابط کاربری
anbarman.pyw         # نقطه اجرا
```

داده‌ها در مسیر `%APPDATA%\Anbarman` ذخیره می‌شوند.

---

## پشتیبانی

- آموزش و پشتیبانی: [myhadipour.ir/anbarman](https://myhadipour.ir/anbarman)  
- داخل برنامه: بخش **تنظیمات و پشتیبانی**

---

<div align="center">

**ساخته‌شده برای فروشگاه‌داران ایران**

</div>
