# -*- coding: utf-8 -*-
"""ابزارهای تاریخ شمسی و اعداد فارسی"""
import datetime as dt
from types import SimpleNamespace


MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
          "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
# ایندکس = date.weekday()  (دوشنبه=۰)
WEEKDAYS = ["دوشنبه", "سه شنبه", "چهارشنبه", "پنج شنبه", "جمعه", "شنبه", "یکشنبه"]

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(s):
    return str(s).translate(_FA)


def to_en(s):
    out = []
    for ch in str(s):
        if "۰" <= ch <= "۹":
            out.append(chr(ord(ch) - ord("۰") + 48))
        elif "٠" <= ch <= "٩":
            out.append(chr(ord(ch) - ord("٠") + 48))
        else:
            out.append(ch)
    return "".join(out)


def money(n):
    try:
        n = int(round(float(n)))
    except Exception:
        n = 0
    return fa(f"{n:,}".replace(",", "٬"))


def short(n):
    """۲۰ میلیون، ۱٫۵ میلیارد ..."""
    n = float(n or 0)
    for div, name in ((1e9, " میلیارد"), (1e6, " میلیون"), (1e3, " هزار")):
        if abs(n) >= div:
            s = f"{n / div:.1f}".rstrip("0").rstrip(".")
            return fa(s.replace(".", "٫")) + name
    return fa(int(n))


def g2j(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
            - 80 + gd + g_d_m[gm - 1])
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def j2g(jy, jm, jd):
    doy = (jm - 1) * 31 + jd - 1 if jm <= 6 else 186 + (jm - 7) * 30 + jd - 1
    base = dt.date(jy + 621, 3, 21) + dt.timedelta(days=doy)
    for delta in (0, -1, 1, -2, 2):
        c = base + dt.timedelta(days=delta)
        if g2j(c.year, c.month, c.day) == (jy, jm, jd):
            return c
    raise ValueError("تاریخ نامعتبر")


def to_jalali(d):
    return g2j(d.year, d.month, d.day)


def fmt(d):
    jy, jm, jd = to_jalali(d)
    return fa(f"{jy:04d}/{jm:02d}/{jd:02d}")


def fmt_long(d):
    jy, jm, jd = to_jalali(d)
    return fa(f"{WEEKDAYS[d.weekday()]} {jd} {MONTHS[jm - 1]} {jy}")


def parse(s):
    s = to_en(s).strip().replace("-", "/").replace(".", "/")
    parts = [p for p in s.split("/") if p]
    if len(parts) != 3:
        return None
    try:
        jy, jm, jd = (int(p) for p in parts)
        if not (1 <= jm <= 12 and 1 <= jd <= 31):
            return None
        return j2g(jy, jm, jd)
    except Exception:
        return None


def today():
    return dt.date.today()


def week_start(d):
    """شروع هفته = شنبه"""
    return d - dt.timedelta(days=(d.weekday() - 5) % 7)


def month_range(jy, jm):
    start = j2g(jy, jm, 1)
    nxt = j2g(jy + 1, 1, 1) if jm == 12 else j2g(jy, jm + 1, 1)
    return start, nxt - dt.timedelta(days=1)

from types import SimpleNamespace
J = SimpleNamespace(**{k: v for k, v in list(globals().items()) if not k.startswith('__')})
