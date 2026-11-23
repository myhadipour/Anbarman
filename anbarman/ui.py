# -*- coding: utf-8 -*-
"""رابط کاربری — ویجت‌ها، دیالوگ‌ها و صفحات"""
import os
import sys
import re
import json
import math
import time
import queue
import threading
import traceback
import webbrowser
import tempfile
import uuid
import datetime as dt
from pathlib import Path
from functools import partial
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, font as tkfont

from .jalali import J, fa, to_en, money, short
from .database import DB, app_dir, clean_barcode, now_str, PerfTimer, perf_log
from . import prices as P
from . import theme
from .theme import (
    BG, CARD, TEXT, MUTED, SEP, BLUE, BLUE_BG, GREEN, RED, ORANGE, PURPLE, TEAL, YELLOW,
    FILL, ACCENT, DARK, C, S, F, lbl, rtl, ltr, register_fonts, make_thumb, titlebar_dark,
    apply_custom, COLOR_ROLES, install_theme_hook,
)
from . import icons
from .icons import (
    ICONS, ICON_OF, draw_svg, draw_icon, tile, ico, row_label, heading,
    load_logo, load_app_icon, load_author, ico_path,
)


APP_VERSION = "1.0.0"
TUTORIAL_URL = "https://myhadipour.ir/anbarman"
SUPPORT_EMAIL = "myhadipour@gmail.com"
SUPPORT_URL = "https://donito.me/hadipour"

# سازگاری: بعضی جاها مستقیم از ثابت‌های تم استفاده می‌کنند
# پالت از theme می‌آید؛ اگر در ادامه UI دوباره تعریف شده، override می‌شود


import tkinter as tk
from tkinter import ttk, filedialog, font as tkfont
import threading
import queue
import webbrowser
import base64
import tempfile
import datetime as dt
from functools import partial

# ---------------------------------------------------------------- پالت (الهام از iOS جدید)
BG = "#F2F2F7"  # iOS 18 systemGroupedBackground
CARD = "#FEFEFE"
TEXT = "#000000"
MUTED = "#6E6E73"
FAINT = "#A1A1A6"
SEP = "#E5E5EA"
BLUE = "#0A84FF"
BLUE_BG = "#DCEBFF"
GREEN = "#30D158"
RED = "#FF453A"
ORANGE = "#FF9F0A"
PURPLE = "#BF5AF2"
TEAL = "#64D2FF"
FILL = "#E9E9EF"
FILL2 = "#D8D8DE"
FAM = "Tahoma"
EMOJI = "Segoe UI Emoji"
SC = 1.0   # مقیاس DPI
ZM = 1.0   # بزرگ نمایی متن (تنظیم کاربر)

CURRENCIES = [("IRT", "تومان"), ("USD", "دلار آمریکا"), ("AED", "درهم امارات")]
CUR_NAME = dict(CURRENCIES)
CUR_SHORT = {"IRT": "تومان", "USD": "دلار", "AED": "درهم"}


# ---------------------------------------------------------------- تم روشن/تاریک و راست به چپ
THEME_DARK = False
# هر رنگ روشن → معادل تاریک. (مقدارهای تاریک هرگز نباید خودشان کلید باشند)
_DARK_MAP = {
    "#F2F2F7": "#0E0E11",  # BG
    "#FEFEFE": "#1C1C1F",  # CARD
    "#000000": "#F5F5F8",  # TEXT
    "#6E6E73": "#A3A3AB",  # MUTED
    "#A1A1A6": "#80808A",  # FAINT
    "#E5E5EA": "#2E2E33",  # SEP
    "#E9E9EF": "#2A2A2F",  # FILL
    "#D8D8DE": "#3C3C42",  # FILL2
    "#DCEBFF": "#17304F",  # BLUE_BG
    "#D4E5FF": "#1E3F69",
    "#FFE9E7": "#3B1F1E",
    "#FFD8D4": "#4E2826",
    "#E4F8EA": "#173323",
    "#CFF0D9": "#1F4730",
    "#1F9D45": "#4ADE80",
    "#C7C7CC": "#55555D",
    "#EEEEF3": "#26262B",
    "#D1D1D6": "#4A4A52",
    "#1C1C1E": "#3A3A40",
    "#DADAE0": "#45454C",
    "#FAFAFD": "#232328",
    "#E8F2FF": "#122743",
    "#E9E9EE": "#09090B",  # سایه کارت
    "#EFEFF3": "#0B0B0E",
}
assert not (set(_DARK_MAP) & set(_DARK_MAP.values())), "رنگ تاریک نباید کلید باشد"
_COLOR_KEYS = frozenset((
    "bg", "background", "fg", "foreground", "fill", "outline", "activebackground", "activeforeground",
    "highlightbackground", "highlightcolor", "insertbackground", "selectbackground", "selectforeground",
    "disabledforeground", "troughcolor"))
RLE, LRE, PDF = "\u202b", "\u202a", "\u202c"
# حروف عربی/فارسی (ارقام عمدا بیرون اند: متن فقط عدد همان طور چپ به راست می ماند)
_RTL_LETTER = re.compile("[\u0620-\u064A\u0671-\u06D3\u06FA-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def C(col):
    """رنگ را مطابق تم و سفارشی سازی کاربر برمی گرداند"""
    if isinstance(col, str):
        up = col.upper()
        v = _CUSTOM.get(up)
        if v:
            return v
        if THEME_DARK:
            return _DARK_MAP.get(up, col)
    return col

_CUSTOM = {}
COLOR_ROLES = [("bg", "رنگ پس زمینه برنامه", "#F2F2F7"), ("card", "رنگ کادرها", "#FEFEFE"),
               ("accent", "رنگ دکمه ها و تأکیدها", "#0A84FF"), ("fill", "رنگ فیلدها و دکمه های ساده", "#E9E9EF"),
               ("text", "رنگ نوشته ها", "#000000")]
_RESERVED = set(_DARK_MAP) | set(_DARK_MAP.values()) | {"#0A84FF", "#0A6CE0", "#FFFFFF", "#010203"}


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex([x * (1 - t) + y * t for x, y in zip(ra, rb)])


def _safe(h):
    """رنگ کاربر نباید با یکی از رنگ های داخلی برنامه یکی باشد (وگرنه دوباره تبدیل می شود)"""
    h = h.upper()
    n = 0
    while h in _RESERVED and n < 8:
        r = _rgb(h)
        r[2] = r[2] + 1 if r[2] < 255 else r[2] - 1
        h = _hex(r)
        n += 1
    return h


def apply_custom(d):
    """رنگ های سفارشی کاربر را (برای تم فعلی) فعال می کند"""
    _CUSTOM.clear()
    for role, _t, key in COLOR_ROLES:
        c = (d or {}).get(role)
        if isinstance(c, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", c):
            _CUSTOM[key] = _safe(c)
    acc = (d or {}).get("accent")
    if isinstance(acc, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", acc):
        base = "#1C1C1F" if THEME_DARK else "#FFFFFF"
        t1, t2, t3 = (0.74, 0.66, 0.82) if THEME_DARK else (0.86, 0.78, 0.92)
        _CUSTOM["#DCEBFF"] = _safe(_mix(acc, base, t1))
        _CUSTOM["#D4E5FF"] = _safe(_mix(acc, base, t2))
        _CUSTOM["#E8F2FF"] = _safe(_mix(acc, base, t3))
        _CUSTOM["#0A6CE0"] = _safe(_mix(acc, "#000000", 0.18))



def rtl(s):
    """هر متنی که حرف فارسی دارد را «راست به چپ» می کند تا ویندوز عدد/نقطه/دونقطه را درست بچیند.
    (Tk پیش فرض چپ به راست است؛ بدون این، «۵ عدد» می شود «عدد ۵» و نقطه آخر جمله می پرد اول خط.)"""
    if not isinstance(s, str) or not s or not _RTL_LETTER.search(s) or s.startswith(RLE):
        return s
    return RLE + s.replace("\n", PDF + "\n" + RLE) + PDF


def ltr(s):
    """بخشی از متن (مثل +۵۰٪ یا یک عدد علامت دار) را چپ به راست نگه می دارد"""
    return LRE + str(s) + PDF


_orig_options = tk.Misc._options


def _themed_options(self, cnf, kw=None):
    raw = getattr(self, "_RAW_TEXT", False)
    rawc = getattr(self, "_RAW_COLOR", False)

    def conv(d):
        if not d or not isinstance(d, dict):
            return d
        out = None
        for k, v in d.items():
            if isinstance(v, str):
                nv = v
                if k in _COLOR_KEYS:
                    nv = v if rawc else C(v)
                elif k in ("text", "label") and not raw:
                    nv = rtl(v)
                if nv is not v:
                    if out is None:
                        out = dict(d)
                    out[k] = nv
        return out if out is not None else d
    return _orig_options(self, conv(cnf), conv(kw))


tk.Misc._options = _themed_options


def titlebar_dark(win):
    """نوار عنوان ویندوز را هم رنگ تم می کند (اگر ویندوز ۱۰/۱۱ باشد)"""
    if os.name != "nt":
        return
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        v = ctypes.c_int(1 if THEME_DARK else 0)
        for attr in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), 4) == 0:
                break
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
    except Exception:
        pass


_FC = {}


def tfont(font):
    f = _FC.get(font)
    if f is None:
        f = _FC[font] = tkfont.Font(font=font)
    return f


def S(n):
    return max(1, int(round(n * SC * ZM)))


def F(size=10, bold=False):
    sz = max(7, int(round(size * ZM)))
    return (FAM, sz, "bold") if bold else (FAM, sz)


def lbl(parent, text="", size=10, bold=False, fg=TEXT, bg=None, anchor="e", **kw):
    kw.setdefault("justify", "right")
    return tk.Label(parent, text=text, font=F(size, bold), fg=fg, bg=bg or parent["bg"], anchor=anchor, **kw)


def rrect(c, x1, y1, x2, y2, r, **kw):
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
           x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def sep(parent, pad=0):
    f = tk.Frame(parent, bg=SEP, height=1)
    f.pack(fill="x", padx=pad)
    return f


class Card(tk.Canvas):
    """کارت گوشه گرد با سایه نرم. محتوا را داخل .body بگذارید."""
    SH = ("#E9E9EE", "#EFEFF3")

    def __init__(self, parent, r=20, pad=12, bg=CARD, auto=True, shadow=True):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, height=S(30))
        self.r, self.pad, self.cbg, self.auto, self.shadow = S(r), S(pad), bg, auto, shadow
        self.m = S(5)
        self.body = tk.Frame(self, bg=bg)
        self.win = self.create_window(0, 0, window=self.body, anchor="nw")
        self._cw = self._ch = 0
        self.bind("<Configure>", self._cfg)
        self.body.bind("<Configure>", self._bcfg)

    def _bcfg(self, e=None):
        if self.auto:
            h = self.body.winfo_reqheight() + 2 * (self.pad + self.m)
            if int(float(self["height"])) != h:
                self.configure(height=h)

    def _cfg(self, e):
        if (e.width, e.height) == (self._cw, self._ch):
            return
        self._cw, self._ch = e.width, e.height
        later(self, "_dj", self._draw, 14)

    def _draw(self):
        self.delete("cardbg")
        W, H, m = self._cw, self._ch, self.m
        if W < 20 or H < 20:
            return
        if self.shadow:
            for i, c in enumerate(self.SH):
                k = S(2 - i) + 1
                rrect(self, m - k, m - k + S(2), W - m + k, H - m + k + S(2), self.r + k, fill=c, outline="",
                      tags="cardbg")
        rrect(self, m, m, W - m, H - m, self.r, fill=self.cbg, outline="", tags="cardbg")
        self.tag_lower("cardbg")
        self.coords(self.win, m + self.pad, m + self.pad)
        kw = {"width": max(10, W - 2 * (m + self.pad))}
        if not self.auto:
            kw["height"] = max(10, H - 2 * (m + self.pad))
        self.itemconfigure(self.win, **kw)


def rbox(parent, bg=FILL, r=12, pad=0):
    """کادر گوشه گرد (بدون سایه). محتوا را داخل .body بگذارید."""
    c = Card(parent, r=r, pad=pad, bg=bg, shadow=False)
    c.m = 1
    return c



class RMemo(tk.Frame):
    """کادر چندخطی راست به چپ: متن فارسی راست چین، انتخاب با ماوس و کپی/پیست"""

    def __init__(self, parent, height=3, bg=None):
        bg = bg or FILL
        super().__init__(parent, bg=bg)
        self.t = tk.Text(self, height=height, wrap="word", font=F(10), bg=bg, fg=TEXT, relief="flat", bd=0,
                         highlightthickness=0, insertbackground=TEXT, selectbackground=BLUE,
                         selectforeground="#FFFFFF", inactiveselectbackground=BLUE, exportselection=False,
                         padx=S(6), pady=S(4), undo=True, takefocus=1, cursor="xterm")
        self.t.pack(fill="both", expand=True)
        self.t.tag_configure("r", justify="right")
        for ev in ("<KeyRelease>", "<<Paste>>", "<<Cut>>", "<ButtonRelease-1>"):
            self.t.bind(ev, lambda e: self.t.after_idle(self._align))

    def _align(self):
        self.t.tag_add("r", "1.0", "end")

    def get(self):
        return self.t.get("1.0", "end").strip()

    def set(self, text):
        self.t.delete("1.0", "end")
        self.t.insert("1.0", text or "")
        self._align()


class Wrap(tk.Frame):
    """چیدمان شناور (راستبهچپ): اگر جا نباشد، اجزا به خط بعد میروند.
    add(w, side="r"|"l", expand=False, minw=0): اجزای side="r" از راست و side="l" از چپ چیده میشوند."""

    def __init__(self, parent, bg=None, gap=8, vgap=6, align="right"):
        super().__init__(parent, bg=bg or parent["bg"], height=S(10))
        self.gap, self.vgap, self.align = S(gap), S(vgap), align
        self.items, self.off, self._sig = [], set(), None
        self.bind("<Configure>", lambda e: self.layout())

    def add(self, w, side="r", expand=False, minw=0):
        self.items.append([w, side, expand, S(minw)])
        self._sig = None
        self.after_idle(self.layout)
        return w

    def show(self, w, on=True):
        if on:
            self.off.discard(w)
        else:
            self.off.add(w)
            try:
                w.place_forget()
            except Exception:
                pass
        self._sig = None
        self.after_idle(self.layout)

    def layout(self):
        try:
            W = self.winfo_width()
            its = [it for it in self.items if it[0] not in self.off and it[0].winfo_exists()]
        except tk.TclError:
            return
        if W < 40:
            return
        sig = (W, tuple((id(it[0]), it[0].winfo_reqwidth(), it[0].winfo_reqheight()) for it in its))
        if sig == self._sig:
            return
        self._sig = sig
        gap = self.gap
        rows, cur, curw = [], [], 0
        for w, side, ex, mw in its:
            nat = max(w.winfo_reqwidth(), mw)
            add = nat + (gap if cur else 0)
            if cur and curw + add > W:
                rows.append(cur)
                cur, curw, add = [], 0, nat
            cur.append((w, side, ex, nat))
            curw += add
        if cur:
            rows.append(cur)
        y = 0
        for row in rows:
            rh = max(w.winfo_reqheight() for w, _, _, _ in row)
            widths = [r[3] for r in row]
            used = sum(widths) + gap * (len(row) - 1)
            exp = [i for i, r in enumerate(row) if r[2]]
            if exp and W > used:
                share = (W - used) // len(exp)
                for i in exp:
                    widths[i] += share
            rgt = [i for i, r in enumerate(row) if r[1] != "l"]
            lft = [i for i, r in enumerate(row) if r[1] == "l"]
            pos = {}
            if lft:
                x = sum(widths[i] for i in lft) + gap * (len(lft) - 1)
                for i in lft:
                    x -= widths[i]
                    pos[i] = x
                    x -= gap
            if rgt:
                blk = sum(widths[i] for i in rgt) + gap * (len(rgt) - 1)
                x = W if (lft or self.align == "right") else blk
                for i in rgt:
                    x -= widths[i]
                    pos[i] = x
                    x -= gap
            for i, (w, side, ex, nat) in enumerate(row):
                h = w.winfo_reqheight()
                w.place(x=max(0, pos[i]), y=y + (rh - h) // 2, width=widths[i], height=h)
            y += rh + self.vgap
        total = max(1, y - self.vgap)
        try:
            if int(float(self.cget("height"))) != total:
                self.configure(height=total)
        except Exception:
            pass


class RGrid(tk.Frame):
    """شبکه واکنشگرا: تعداد ستونها از روی عرض در دسترس تعیین میشود (راستبهچپ)."""

    def __init__(self, parent, minw=190, maxcols=4, bg=None, padx=4, pady=3):
        super().__init__(parent, bg=bg or parent["bg"])
        self.minw, self.maxcols, self.px, self.py = S(minw), maxcols, S(padx), S(pady)
        self.items, self.cols = [], 0
        self.bind("<Configure>", lambda e: self.layout(e.width))

    def add(self, w):
        self.items.append(w)
        self.cols = 0
        self.after_idle(self.layout)
        return w

    def layout(self, width=None):
        try:
            width = width or self.winfo_width()
        except tk.TclError:
            return
        if width < 40 or not self.items:
            return
        cols = max(1, min(self.maxcols, len(self.items), width // self.minw))
        if cols == self.cols:
            return
        self.cols = cols
        for c in range(self.maxcols + 1):
            self.grid_columnconfigure(c, weight=0, uniform="")
        for c in range(cols):
            self.grid_columnconfigure(c, weight=1, uniform="rg%d" % id(self))
        for i, w in enumerate(self.items):
            r, c = divmod(i, cols)
            w.grid(row=r, column=cols - 1 - c, sticky="nsew", padx=self.px, pady=self.py)


def autowrap(l, pad=0):
    """wraplength برچسب را با عرض والدش هماهنگ میکند (برای متنهای بلند در پنجره کوچک)"""
    if getattr(l, "_aw", False):
        return l
    l._aw = True
    p = l.master

    def fit(e=None):
        try:
            w = p.winfo_width() - pad
            if w > S(80) and str(l.cget("wraplength")) != str(w):
                l.configure(wraplength=w)
        except Exception:
            pass
    p.bind("<Configure>", fit, add="+")
    return l


_BIDI_MARKS = re.compile("[\u202a\u202b\u202c\u200f]")


def _flow_text(raw, w, font):
    """متن را خط به خط با عرض واقعی کادر میشکند (Tk خودش در متن فارسی جای جمله ها را به هم میریزد)"""
    m = tfont(font).measure
    out = []
    for para in raw.split("\n"):
        line = ""
        for wd in para.split(" "):
            cand = wd if not line else line + " " + wd
            if line and m(cand) > w:
                out.append(line)
                line = wd
            else:
                line = cand
        out.append(line)
    return out


def _flow_bind(ch, pad):
    if getattr(ch, "_fl", False):
        return
    ch._fl = True
    ch._raw = _BIDI_MARKS.sub("", str(ch.cget("text")))
    p = ch.master

    def fit(e=None):
        try:
            w = p.winfo_width() - pad
            if w <= S(80) or getattr(ch, "_lw", None) == w:
                return
            ch._lw = w
            lines = _flow_text(ch._raw, w, ch.cget("font"))
            ch.configure(wraplength=0, text="\n".join(lines))
        except Exception:
            pass
    p.bind("<Configure>", fit, add="+")
    p.after_idle(fit)


def wrap_tree(w, pad=None):
    """همه پاراگراف های برچسبی یک صفحه را داخل عرض کادرشان می شکند"""
    pad = S(4) if pad is None else pad
    for ch in w.winfo_children():
        if isinstance(ch, tk.Label) and str(ch.cget("wraplength")) not in ("0", ""):
            try:
                if ch.winfo_manager() == "pack" and ch.pack_info().get("side", "top") == "top":
                    ch.pack_configure(fill="x")
            except Exception:
                pass
            _flow_bind(ch, pad)
        wrap_tree(ch, pad)


_AUTO_ICONS = [
    ("A+", "zoom_in"), ("A−", "zoom_out"), ("بزرگ تر", "zoom_in"), ("کوچک تر", "zoom_out"),
    ("اندازه پیش فرض", "undo"), ("بازنشانی", "undo"), ("فاکتور جدید", "plus"), ("فاکتورهای", "list"),
    ("قدیمی", "chevron"), ("بیشتر", "chevron"), ("نمایش همه", "eye"), ("مشاهده", "eye"), ("نمایش هفته", "calendar"),
    ("آموزش", "tutorial"), ("دریافت دوباره", "refresh"), ("بروزرسانی", "refresh"), ("به روزرسانی", "refresh"),
    ("ریست", "refresh"), ("حذف", "trash"), ("افزودن", "plus"), ("کم کردن", "minus"),
    ("انتخاب", "image"), ("عکس", "image"), ("لوگو", "image"), ("پوشه", "folder"), ("دسته", "category"),
    ("ثبت فروش", "cart"), ("فروش", "cart"), ("فاکتور", "invoice"), ("چاپ", "print"), ("ذخیره", "save"),
    ("ویرایش", "edit"), ("دیجی کالا", "tag"), ("رنگ", "palette"), ("تنظیمات", "settings"),
    ("خروجی", "upload"), ("ورودی", "download"), ("ایمیل", "mail"), ("پشتیبانی", "heart"), ("حمایت", "heart"),
    ("سایت", "globe"), ("جستجو", "search"), ("فیلتر", "filter"), ("توقف", "stop"),
    ("امروز", "calendar"), ("هفته", "calendar"), ("تاریخ", "calendar"), ("بستن", "x"), ("انصراف", "x"),
    ("باشه", "check_circle"), ("بله", "check_circle"), ("ثبت", "check"), ("کپی", "copy"), ("باز", "external"),
    ("لینک", "external"), ("قیمت", "tag"),
]


def _auto_icon(text):
    t = text or ""
    for key, icon in _AUTO_ICONS:
        if key in t:
            return icon
    return "check" if t.strip() else None


class Btn(tk.Canvas):
    STY = {"primary": (BLUE, "#0A6CE0", "#FFFFFF"), "tint": (BLUE_BG, "#D4E5FF", BLUE),
           "plain": (FILL, FILL2, TEXT), "danger": ("#FFE9E7", "#FFD8D4", RED),
           "ok": ("#E4F8EA", "#CFF0D9", "#1F9D45"), "ghost": (CARD, FILL, BLUE)}

    def __init__(self, parent, text, cmd=None, style="plain", size=10, px=16, py=8, w=None, h=None, icon=None,
                 flex=False):
        self.cmd, self.style, self.text, self.flex = cmd, style, text, flex
        self.icon = icon or _auto_icon(text)
        self._f = F(size, style == "primary")
        tf = tfont(self._f)
        self._isz = S(max(14, round(size * 1.7))) if self.icon else 0
        gap = S(6) if (self.icon and text) else 0
        tw = tf.measure(text) if text else 0
        self._content = tw + gap + self._isz
        self._W = S(w) if w else self._content + 2 * S(px)
        self._H = S(h) if h else max(tf.metrics("linespace"), self._isz) + 2 * S(py)
        super().__init__(parent, width=self._W, height=self._H, highlightthickness=0, bg=parent["bg"],
                         cursor="hand2")
        self._bg, self._hv, self._fg = self.STY[style]
        self._render()
        self.bind("<Enter>", lambda e: self.itemconfigure("b", fill=self._hv))
        self.bind("<Leave>", lambda e: self.itemconfigure("b", fill=self._bg))
        self.bind("<ButtonPress-1>", lambda e: self.itemconfigure("b", fill=self._hv))
        self.bind("<ButtonRelease-1>", self._click)
        if flex:
            self.bind("<Configure>", self._resize)

    def _render(self):
        self.delete("all")
        W, H = self._W, self._H
        rrect(self, 0, 0, W, H, H / 2, fill=self._bg, outline="", tags="b")
        x0 = (W - self._content) / 2
        if self.icon:
            draw_icon(self, self.icon, x0 + self._content - self._isz, (H - self._isz) / 2, self._isz, self._fg)
            if self.text:
                self.create_text(x0, H / 2, text=self.text, font=self._f, fill=self._fg, anchor="w")
        else:
            self.create_text(W / 2, H / 2, text=self.text, font=self._f, fill=self._fg)

    def _resize(self, e):
        if e.width > 10 and e.width != self._W:
            self._W = e.width
            self._render()

    def _click(self, e):
        if self.cmd and 0 <= e.x <= self._W and 0 <= e.y <= self._H:
            self.cmd()


class PickRow(tk.Canvas):
    """ردیف انتخابی گوشه گرد (برای منوها و فهرست ها)"""

    def __init__(self, parent, text, cmd, color=None, sub="", bg=CARD):
        h = S(52) if sub else S(40)
        super().__init__(parent, width=S(200), height=h, bg=bg, highlightthickness=0, cursor="hand2")
        self.t, self.sub, self.cmd, self.color, self.hv, self._h = text, sub, cmd, color or TEXT, False, h
        self.bind("<Configure>", lambda e: self._d())
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<Button-1>", lambda e: self.cmd())

    def _hover(self, v):
        self.hv = v
        self._d()

    def _d(self):
        self.delete("all")
        W, H = self.winfo_width(), self._h
        if W < 20:
            return
        if self.hv:
            rrect(self, S(4), S(2), W - S(4), H - S(2), S(12), fill=FILL, outline="")
        if self.sub:
            self.create_text(W - S(16), H * 0.34, text=self.t, font=F(10, True), fill=self.color, anchor="e")
            self.create_text(W - S(16), H * 0.72, text=self.sub, font=F(8), fill=MUTED, anchor="e")
        else:
            self.create_text(W - S(16), H / 2, text=self.t, font=F(10), fill=self.color, anchor="e")


class RScroll(tk.Canvas):
    """نوار اسکرول گوشه گرد"""

    def __init__(self, parent, command, bg=CARD, w=10):
        super().__init__(parent, width=S(w), bg=bg, highlightthickness=0)
        self.command, self.lo, self.hi, self._off = command, 0.0, 1.0, 0
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._move)

    def set(self, lo, hi):
        self.lo, self.hi = float(lo), float(hi)
        self._draw()

    def _geom(self):
        H = self.winfo_height()
        ln = max(S(28), H * (self.hi - self.lo))
        y1 = H * self.lo
        if y1 + ln > H:
            y1 = H - ln
        return H, y1, y1 + ln

    def _draw(self):
        self.delete("all")
        W = self.winfo_width()
        if self.hi - self.lo >= 0.999 or self.winfo_height() < 20 or W < 4:
            return
        H, y1, y2 = self._geom()
        rrect(self, S(2), y1 + S(2), W - S(2), y2 - S(2), (W - S(4)) / 2, fill="#C7C7CC", outline="")

    def _press(self, e):
        H, y1, y2 = self._geom()
        self._off = e.y - y1 if y1 <= e.y <= y2 else (y2 - y1) / 2
        self._move(e)

    def _move(self, e):
        H = max(self.winfo_height(), 1)
        self.command("moveto", max(0.0, (e.y - self._off) / H))


class RProgress(tk.Canvas):
    """نوار پیشرفت گوشه گرد"""

    def __init__(self, parent, length=260, h=8, bg=BLUE_BG):
        super().__init__(parent, width=S(length), height=S(h), bg=bg, highlightthickness=0)
        self.maximum, self.value, self._h = 1, 0, S(h)
        self.bind("<Configure>", lambda e: self._draw())

    def config(self, **kw):
        if "maximum" in kw:
            self.maximum = max(1, kw.pop("maximum"))
        if "value" in kw:
            self.value = kw.pop("value")
        if kw:
            super().configure(**kw)
        self._draw()
    configure = config

    def _draw(self):
        self.delete("all")
        W, H = self.winfo_width(), self._h
        if W < 10:
            return
        rrect(self, 0, 0, W, H, H / 2, fill=FILL2, outline="")
        fw = W * min(1.0, self.value / self.maximum)
        if fw > H:
            rrect(self, 0, 0, fw, H, H / 2, fill=BLUE, outline="")


class Chip(tk.Canvas):
    """برچسب گرد با متن قابل تغییر"""

    def __init__(self, parent, color, icon=None):
        super().__init__(parent, width=S(60), height=S(34), bg=parent["bg"], highlightthickness=0)
        self.color, self.icon = color, icon

    def config(self, **kw):
        if "text" in kw:
            txt = kw.pop("text")
            isz = S(17) if self.icon else 0
            extra = (isz + S(6)) if self.icon else 0
            w = tfont(F(9, True)).measure(txt) + S(30) + extra
            super().configure(width=w)
            self.delete("all")
            rrect(self, 1, 1, w - 1, S(34) - 1, S(17), fill=CARD, outline=SEP)
            if self.icon:
                draw_icon(self, self.icon, w - S(13) - isz, (S(34) - isz) / 2, isz, self.color)
                self.create_text(w - S(13) - isz - S(6), S(17), text=txt, font=F(9, True), fill=self.color, anchor="e")
            else:
                self.create_text(w / 2, S(17), text=txt, font=F(9, True), fill=self.color)
        if kw:
            super().configure(**kw)
    configure = config


class ImgBox(tk.Canvas):
    """جعبه عکس گوشه گرد"""

    def __init__(self, parent, size=116):
        self.s = S(size)
        super().__init__(parent, width=self.s, height=self.s, bg=parent["bg"], highlightthickness=0)
        rrect(self, 0, 0, self.s, self.s, S(18), fill=FILL, outline="")

    def config(self, image=None, **kw):
        if image is not None:
            self.delete("img")
            self._img = image
            self.create_image(self.s / 2, self.s / 2, image=image, tags="img")
    configure = config


def round_img(img, r):
    """گوشه های عکس را شفاف می کند تا گرد دیده شود"""
    try:
        w, h = img.width(), img.height()
        r = min(r, w // 2, h // 2)
        for j in range(r):
            for i in range(r):
                if (r - i - 0.5) ** 2 + (r - j - 0.5) ** 2 > r * r:
                    for x, y in ((i, j), (w - 1 - i, j), (i, h - 1 - j), (w - 1 - i, h - 1 - j)):
                        img.transparency_set(x, y, True)
    except Exception:
        pass


_SWITCH_ICONS = [
    ("خدمات", "settings"), ("دیجی کالا", "tag"), ("قیمت خرید", "wallet"), ("قیمت فروش", "dollar"),
    ("موجودی", "box"), ("سود", "profit"), ("آخرین فروش", "cart"), ("دارایی", "wallet"),
    ("دسته", "category"), ("عکس", "image"),
]


class Switch(tk.Canvas):
    """کلید روشن/خاموش به سبک iOS"""

    def __init__(self, parent, text="", value=False, cmd=None, size=10):
        self.on, self.cmd, self.text = bool(value), cmd, text
        self._f = F(size)
        self.icon = next((ic for k, ic in _SWITCH_ICONS if k in (text or "")), None)
        self._isz = S(18) if self.icon else 0
        tw = tfont(self._f).measure(text) + (self._isz + S(8) if self.icon else 0)
        self._W = tw + S(66)
        self._H = S(34)
        super().__init__(parent, width=self._W, height=self._H, bg=parent["bg"], highlightthickness=0,
                         cursor="hand2")
        self.bind("<Button-1>", self.toggle)
        self._draw()

    def get(self):
        return self.on

    def set(self, v):
        self.on = bool(v)
        self._draw()

    def toggle(self, e=None):
        self.on = not self.on
        self._draw()
        if self.cmd:
            self.cmd(self.on)

    def _draw(self):
        self.delete("all")
        tw, th, y = S(50), S(28), S(3)
        rrect(self, 2, y, 2 + tw, y + th, th / 2, fill=GREEN if self.on else FILL2, outline="")
        r = th / 2 - S(2)
        cx = (2 + tw - th / 2) if self.on else (2 + th / 2)
        self.create_oval(cx - r, y + th / 2 - r, cx + r, y + th / 2 + r, fill="#FFFFFF", outline="#D8D8DE")
        if self.icon:
            draw_icon(self, self.icon, self._W - self._isz, (self._H - self._isz) / 2, self._isz, MUTED)
            self.create_text(self._W - self._isz - S(8), self._H / 2, text=self.text, font=self._f, fill=TEXT, anchor="e")
        else:
            self.create_text(self._W, self._H / 2, text=self.text, font=self._f, fill=TEXT, anchor="e")


# (آیکون‌ها و رندر SVG از ماژول icons وارد می‌شوند)

# ---------- ویرایشگر متن فارسی/راست به چپ ----------
def later(w, key, fn, ms=16):
    """اجرای تأخیری و ادغام شده (برای نرم شدن تغییر اندازه پنجره)"""
    old = getattr(w, key, None)
    if old:
        try:
            w.after_cancel(old)
        except Exception:
            pass
    setattr(w, key, w.after(ms, fn))


_BIDI_SEP = "/,.:٫٬"


def _bclass(ch):
    o = ord(ch)
    if ch.isdigit() or 0x06F0 <= o <= 0x06F9 or 0x0660 <= o <= 0x0669:
        return "D"
    if ch == "\u200c" or 0x064B <= o <= 0x065F or o == 0x0670:
        return "R"
    if ch.isalpha():
        for a, b in ((0x0590, 0x08FF), (0xFB1D, 0xFDFF), (0xFE70, 0xFEFF)):
            if a <= o <= b:
                return "R"
        return "L"
    return "N"


def _reorder(levels):
    n = len(levels)
    order = list(range(n))
    odd = [v for v in levels if v % 2 == 1]
    if not odd:
        return order
    for lvl in range(max(levels), min(odd) - 1, -1):
        i = 0
        while i < n:
            if levels[order[i]] >= lvl:
                j = i
                while j < n and levels[order[j]] >= lvl:
                    j += 1
                order[i:j] = reversed(order[i:j])
                i = j
            else:
                i += 1
    return order


class BidiLayout:
    """چیدمان بصری متن دوجهته: موقعیت نشانگر، انتخاب با ماوس و ناحیه انتخاب"""

    def __init__(self, text, measure, rtl_default=False):
        self.text, self.m = text, measure
        cls = [_bclass(c) for c in text]
        n = len(text)
        first = next((c for c in cls if c in "RL"), None)
        self.base_rtl = rtl_default if first is None else (first == "R")
        for i, ch in enumerate(text):  # جداکننده بین دو رقم، جزو عدد است
            if cls[i] == "N" and ch in _BIDI_SEP and 0 < i < n - 1 and cls[i - 1] == "D" and cls[i + 1] == "D":
                cls[i] = "D"
        prev = "R" if self.base_rtl else "L"
        for i in range(n):  # ارقام بعد از متن لاتین، لاتین حساب می شوند
            if cls[i] in "RL":
                prev = cls[i]
            elif cls[i] == "D" and prev == "L":
                cls[i] = "L"
        base = "R" if self.base_rtl else "L"
        dirs = [None] * n
        for i in range(n):
            if cls[i] == "N":
                continue
            dirs[i] = "R" if cls[i] in "RD" else "L"
        i = 0
        while i < n:
            if cls[i] != "N":
                i += 1
                continue
            j = i
            while j < n and cls[j] == "N":
                j += 1
            a = dirs[i - 1] if i > 0 else base
            b = dirs[j] if j < n else base
            for k in range(i, j):
                dirs[k] = a if a == b else base
            i = j
        lv = []
        for i in range(n):
            if self.base_rtl:
                lv.append(1 if (cls[i] == "R" or (cls[i] == "N" and dirs[i] == "R")) else 2)
            else:
                lv.append(1 if (cls[i] == "R" or (cls[i] == "N" and dirs[i] == "R")) else
                          (2 if cls[i] == "D" else 0))
        self.segs = []
        for i in range(n):
            key = (lv[i], cls[i] == "N")
            if self.segs and self.segs[-1]["key"] == key:
                self.segs[-1]["e"] = i + 1
            else:
                self.segs.append({"key": key, "s": i, "e": i + 1, "lvl": lv[i]})
        for sg in self.segs:
            sg["t"] = text[sg["s"]:sg["e"]]
            sg["w"] = measure(sg["t"])
        self.order = _reorder([sg["lvl"] for sg in self.segs])
        x = 0
        for k in self.order:
            self.segs[k]["x"] = x
            x += self.segs[k]["w"]
        self.total = x

    def caret_x(self, i):
        if not self.segs:
            return 0
        if i >= len(self.text):
            sg, k = self.segs[-1], len(self.segs[-1]["t"])
        else:
            sg = next(s for s in self.segs if s["s"] <= i < s["e"])
            k = i - sg["s"]
        w = self.m(sg["t"][:k])
        return sg["x"] + (w if sg["lvl"] % 2 == 0 else sg["w"] - w)

    def index_at(self, x):
        if not self.segs:
            return 0
        vis = [self.segs[k] for k in self.order]
        sg = vis[-1]
        if x <= vis[0]["x"]:
            sg = vis[0]
        else:
            for s in vis:
                if s["x"] <= x <= s["x"] + s["w"]:
                    sg = s
                    break
        local = x - sg["x"] if sg["lvl"] % 2 == 0 else sg["w"] - (x - sg["x"])
        best, bd = 0, 1e9
        for k in range(len(sg["t"]) + 1):
            d = abs(self.m(sg["t"][:k]) - local)
            if d < bd:
                best, bd = k, d
        return sg["s"] + best

    def sel_rects(self, a, b):
        out = []
        for sg in self.segs:
            lo, hi = max(a, sg["s"]), min(b, sg["e"])
            if lo >= hi:
                continue
            w1 = self.m(sg["t"][:lo - sg["s"]])
            w2 = self.m(sg["t"][:hi - sg["s"]])
            if sg["lvl"] % 2 == 0:
                out.append((sg["x"] + w1, sg["x"] + w2))
            else:
                out.append((sg["x"] + sg["w"] - w2, sg["x"] + sg["w"] - w1))
        return out


class _EProxy:
    """رابط سازگار با Entry برای کدهای قدیمی (bind / focus_set / icursor ...)"""

    def __init__(self, o):
        self.o = o

    def bind(self, seq, fn, add=None):
        return self.o.bind(seq, fn, add)

    def focus_set(self):
        self.o.focus_set()

    def icursor(self, i):
        self.o.set_caret(len(self.o.var.get()) if i == "end" else int(i))

    def index(self, i):
        return self.o.caret if i == "insert" else len(self.o.var.get())

    def select_range(self, a, b):
        self.o.set_sel(int(a), len(self.o.var.get()) if b == "end" else int(b))

    def get(self):
        return self.o.var.get()

    def clipboard_get(self):
        return self.o.clipboard_get()


class REntry(tk.Canvas):
    """کادر ورودی گوشه گرد با ویرایشگر مخصوص متن فارسی (راست به چپ): چسباندن، انتخاب و ویرایش دقیق"""

    _RAW_TEXT = True  # ویرایشگر، خودش چیدمان دوجهته دارد؛ علامت جهت اضافه نشود

    def __init__(self, parent, width=18, justify="right", textvariable=None, placeholder="", h=38, fillbg=FILL,
                 icon=None, size=10):
        self._font = F(size)
        self._W = tfont(self._font).measure("0") * width + S(26)
        self._H = S(h)
        super().__init__(parent, width=self._W, height=self._H, bg=parent["bg"], highlightthickness=0,
                         takefocus=1, cursor="xterm")
        self.var = textvariable or tk.StringVar()
        self.fillbg, self.ph, self.focus, self.icon, self.justify = fillbg, placeholder, False, icon, justify
        self.caret, self.sel, self.anchor = len(self.var.get()), None, 0
        self._x0, self._cx, self._lay = 0, None, None
        self._internal, self._caron, self._bj = False, True, None
        self.e = _EProxy(self)
        self.bind("<Configure>", lambda ev: later(self, "_dj", self._draw, 12))
        self.bind("<Button-1>", self._click)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<Double-Button-1>", lambda ev: self._select_all())
        self.bind("<Button-3>", self._menu)
        self.bind("<KeyPress>", self._key)
        self.bind("<FocusIn>", lambda ev: self._f(True))
        self.bind("<FocusOut>", lambda ev: self._f(False))
        self.var.trace_add("write", lambda *a: self._on_var())

    # ---- ابزار
    def _meas(self, s):
        return tfont(self._font).measure(s)

    def _on_var(self):
        n = len(self.var.get())
        if not self._internal:
            self.caret = n
        self.caret = min(self.caret, n)
        if self.sel and self.sel[1] > n:
            self.sel = None
        self._draw()

    def _f(self, on):
        self.focus = on
        self._caron = True
        if on:
            self._blink()
        self._draw()

    def _blink(self):
        if self._bj:
            try:
                self.after_cancel(self._bj)
            except Exception:
                pass
            self._bj = None
        if not self.focus:
            return
        try:
            self._caret_draw()
            self._caron = not self._caron
            self._bj = self.after(530, self._blink)
        except tk.TclError:
            pass

    # ---- رسم
    def _caret_draw(self):
        self.delete("caret")
        if self.focus and self._caron and self._cx is not None:
            lh = tfont(self._font).metrics("linespace")
            self.create_line(self._cx, self._H / 2 - lh / 2, self._cx, self._H / 2 + lh / 2, fill=TEXT, width=2,
                             tags="caret")

    def _draw(self):
        W, H = max(self.winfo_width(), 20), self._H
        self._W = W
        self.delete("all")
        rrect(self, 1, 1, W - 1, H - 1, S(12), fill=self.fillbg, outline=BLUE if self.focus else self.fillbg,
              width=2 if self.focus else 1)
        pad = S(13)
        left, right = pad + (S(24) if self.icon else 0), W - pad
        if self.icon:
            draw_icon(self, self.icon, S(12), (H - S(16)) / 2, S(16), MUTED)
        text = self.var.get()
        lay = self._lay = BidiLayout(text, self._meas, self.justify == "right")
        vw, tw = right - left, lay.total
        if self.justify == "center":
            x0 = left + (vw - tw) / 2
        elif self.justify == "right":
            x0 = right - tw
        else:
            x0 = left
        cx = x0 + lay.caret_x(self.caret)
        if tw > vw:
            if cx < left:
                x0 += left - cx
            elif cx > right:
                x0 -= cx - right
            cx = x0 + lay.caret_x(self.caret)
        self._x0, self._cx = x0, cx
        lh = tfont(self._font).metrics("linespace")
        if self.sel:
            for x1, x2 in lay.sel_rects(*self.sel):
                self.create_rectangle(x0 + x1, H / 2 - lh / 2, x0 + x2, H / 2 + lh / 2, fill=BLUE_BG, outline="")
        if text:
            for sg in lay.segs:
                self.create_text(x0 + sg["x"], H / 2, text=sg["t"], font=self._font, fill=TEXT, anchor="w")
        elif self.ph and not self.focus:
            ax = {"right": right, "center": (left + right) / 2, "left": left}[self.justify]
            self.create_text(ax, H / 2, text=rtl(self.ph), font=self._font, fill=FAINT,
                             anchor={"right": "e", "center": "center", "left": "w"}[self.justify])
        self._caret_draw()

    # ---- ویرایش
    def _set(self, text, caret):
        self.sel, self.anchor = None, caret
        self._internal = True
        try:
            self.caret = max(0, min(caret, len(text)))
            if text != self.var.get():
                self.var.set(text)
        finally:
            self._internal = False
        self._caron = True
        self._draw()

    def _repl(self, a, b, ins):
        t = self.var.get()
        self._set(t[:a] + ins + t[b:], a + len(ins))

    def set_caret(self, i):
        self.caret = max(0, min(i, len(self.var.get())))
        self.sel, self.anchor, self._caron = None, self.caret, True
        self._draw()

    def set_sel(self, a, b):
        n = len(self.var.get())
        a, b = max(0, min(a, n)), max(0, min(b, n))
        self.sel = (a, b) if a < b else None
        self.caret, self.anchor, self._caron = b, a, True
        self._draw()

    def _select_all(self):
        n = len(self.var.get())
        self.set_sel(0, n)

    def _copy(self):
        if self.sel:
            self.clipboard_clear()
            self.clipboard_append(self.var.get()[self.sel[0]:self.sel[1]])

    def _cut(self):
        if self.sel:
            self._copy()
            self._repl(self.sel[0], self.sel[1], "")

    def _paste(self, ev=None):
        try:
            txt = self.clipboard_get()
        except tk.TclError:
            return "break"
        txt = " ".join(txt.splitlines()).replace("\t", " ")
        a, b = self.sel if self.sel else (self.caret, self.caret)
        self._repl(a, b, txt)
        return "break"

    def _menu(self, ev):
        self.focus_set()
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="برش", command=self._cut)
        m.add_command(label="کپی", command=self._copy)
        m.add_command(label="چسباندن", command=self._paste)
        m.add_separator()
        m.add_command(label="انتخاب همه", command=self._select_all)
        try:
            m.tk_popup(ev.x_root, ev.y_root)
        finally:
            m.grab_release()

    def _at(self, x):
        return self._lay.index_at(x - self._x0) if self._lay else 0

    def _click(self, ev):
        self.focus_set()
        i = self._at(ev.x)
        self.caret, self.anchor, self.sel, self._caron = i, i, None, True
        self._draw()

    def _drag(self, ev):
        i = self._at(ev.x)
        self.caret = i
        a, b = min(self.anchor, i), max(self.anchor, i)
        self.sel = (a, b) if a != b else None
        self._draw()

    def _goto(self, i, shift):
        n = len(self.var.get())
        i = max(0, min(n, i))
        if shift:
            if self.sel is None:
                self.anchor = self.caret
            a, b = min(self.anchor, i), max(self.anchor, i)
            self.sel = (a, b) if a != b else None
        else:
            self.sel, self.anchor = None, i
        self.caret, self._caron = i, True
        self._draw()

    def _key(self, ev):
        ks, st = ev.keysym, ev.state
        ctrl, shift, alt = bool(st & 0x4), bool(st & 0x1), bool(st & 0x20000)
        if ctrl and alt and ev.char and ev.char >= " ":
            ctrl = False  # AltGr
        if ctrl:
            kc = {86: "v", 67: "c", 88: "x", 65: "a"}.get(ev.keycode) if os.name == "nt" else ks.lower()
            if kc == "v":
                return self._paste()
            if kc == "c":
                self._copy()
                return "break"
            if kc == "x":
                self._cut()
                return "break"
            if kc == "a":
                self._select_all()
                return "break"
            if ks not in ("Left", "Right", "Home", "End", "BackSpace", "Delete"):
                return None
        if shift and ks == "Insert":
            return self._paste()
        if ks in ("Return", "KP_Enter", "Tab", "ISO_Left_Tab", "Escape"):
            return None
        n = len(self.var.get())
        rtl = self._lay.base_rtl if self._lay else self.justify == "right"
        if ks in ("Left", "Right"):
            d = (1 if ks == "Left" else -1) * (1 if rtl else -1)
            if self.sel and not shift:
                self._goto(self.sel[1] if d > 0 else self.sel[0], False)
            else:
                self._goto(self.caret + d, shift)
        elif ks == "Home":
            self._goto(0, shift)
        elif ks == "End":
            self._goto(n, shift)
        elif ks == "BackSpace":
            if self.sel:
                self._repl(self.sel[0], self.sel[1], "")
            elif self.caret > 0:
                self._repl(self.caret - 1, self.caret, "")
        elif ks == "Delete":
            if self.sel:
                self._repl(self.sel[0], self.sel[1], "")
            elif self.caret < n:
                self._repl(self.caret, self.caret + 1, "")
        elif ev.char and ev.char >= " " and ev.char != "\x7f" and not alt:
            a, b = self.sel if self.sel else (self.caret, self.caret)
            self._repl(a, b, ev.char)
        else:
            return None
        return "break"

    def get(self):
        return self.var.get()

    def set_text(self, t):
        self.var.set(t)

    def focus_entry(self):
        self.focus_set()


class AmountEntry(REntry):
    def __init__(self, parent, value=0, decimals=False, width=14, cb=None, **kw):
        super().__init__(parent, width=width, justify="center", **kw)
        self.decimals, self.cb, self._busy = decimals, None, False
        self.var.trace_add("write", self._on)
        self.set(value)
        self.cb = cb

    def _on(self, *_):
        if self._busy:
            return
        old = self.var.get()
        ci = self.e.index("insert")
        left = to_en(old[:ci]).replace("٫", ".")
        nd = sum(1 for ch in left if ch.isdigit())
        dot_left = "." in left
        s = to_en(old).replace("٫", ".")
        keep, dot = [], False
        for ch in s:
            if ch.isdigit():
                keep.append(ch)
            elif ch == "." and self.decimals and not dot:
                keep.append(".")
                dot = True
        txt = "".join(keep)
        if "." in txt:
            ip, dp = txt.split(".", 1)
        else:
            ip, dp = txt, None
        ips = money(int(ip)) if ip else ("۰" if dp is not None else "")
        new = ips + ("٫" + fa(dp) if dp is not None else "")
        if new != old:
            pos, cnt = len(new), 0
            if nd > 0:
                for k, ch in enumerate(new):
                    if to_en(ch).isdigit():
                        cnt += 1
                        if cnt == nd:
                            pos = k + 1
                            break
                if dot_left and new[pos:pos + 1] == "٫":
                    pos += 1
            else:
                pos = 1 if (dot_left and new.startswith("۰")) else 0
            self._busy = True
            self.var.set(new)
            self.e.icursor(pos)
            self._busy = False
        if self.cb:
            self.cb()

    def get_num(self):
        s = to_en(self.var.get()).replace("٬", "").replace(",", "").replace("٫", ".")
        try:
            return float(s) if s else 0.0
        except ValueError:
            return 0.0

    def get_int(self):
        return int(round(self.get_num()))

    def set(self, v):
        if not v:
            self.var.set("")
        elif self.decimals and float(v) != int(v):
            self.var.set(fa(("%g" % v).replace(".", "٫")))
        else:
            self.var.set(money(v))


def days_in_jmonth(jy, jm):
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    try:
        J.j2g(jy, 12, 30)
        return 30
    except Exception:
        return 29


class JCal(tk.Toplevel):
    """تقویم شمسی به سبک کاتالوگ: انتخاب روز با یک کلیک"""

    WD = ["ش", "ی", "د", "س", "چ", "پ", "ج"]

    def __init__(self, owner, d):
        super().__init__(owner)
        self.overrideredirect(True)
        key = "#010203"
        try:
            self.configure(bg=key)
            self.attributes("-transparentcolor", key)
        except tk.TclError:
            self.configure(bg=BG)
        self.owner = owner
        self.jy, self.jm, _ = J.to_jalali(d)
        self.card = rbox(self, CARD, 18, 8)
        self.card.auto = False
        self.card.pack(fill="both", expand=True)
        self.frame = self.card.body
        self.draw()
        self.update_idletasks()
        w = self.frame.winfo_reqwidth() + 2 * (1 + S(8))
        h = self.frame.winfo_reqheight() + 2 * (1 + S(8))
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = min(max(owner.winfo_rootx(), 4), sw - w - 4)
        y = owner.winfo_rooty() + owner.winfo_height() + S(4)
        if y + h > sh - 4:
            y = max(4, owner.winfo_rooty() - h - S(4))
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.bind("<Escape>", lambda e: self.close())
        self.bind("<FocusOut>", lambda e: self.after(120, self._maybe_close))
        self.focus_force()

    def _maybe_close(self):
        try:
            if self.focus_get() is None or str(self.focus_get()).find(str(self)) != 0:
                self.close()
        except Exception:
            self.close()

    def shift(self, n):
        self.jm += n
        if self.jm < 1:
            self.jm, self.jy = 12, self.jy - 1
        elif self.jm > 12:
            self.jm, self.jy = 1, self.jy + 1
        self.draw()

    def _nav(self, parent, icon, n):
        cv = tk.Canvas(parent, width=S(32), height=S(32), bg=CARD, highlightthickness=0, cursor="hand2")
        draw_icon(cv, icon, S(6), S(6), S(20), BLUE)
        cv.bind("<Button-1>", lambda e: self.shift(n))
        return cv

    def _cell(self, grid, r, c, n, g, is_sel, is_today):
        cw, ch = S(38), S(32)
        cv = tk.Canvas(grid, width=cw, height=ch, bg=CARD, highlightthickness=0, cursor="hand2")
        cv.grid(row=r, column=c, padx=1, pady=1)

        def paint(hv=False):
            cv.delete("all")
            if is_sel:
                rrect(cv, 1, 1, cw - 1, ch - 1, S(11), fill=BLUE, outline="")
            elif hv:
                rrect(cv, 1, 1, cw - 1, ch - 1, S(11), fill=FILL, outline="")
            elif is_today:
                rrect(cv, 1, 1, cw - 1, ch - 1, S(11), fill=BLUE_BG, outline="")
            cv.create_text(cw / 2, ch / 2, text=fa(n), font=F(10, is_sel or is_today),
                           fill="#FFFFFF" if is_sel else (BLUE if is_today else TEXT))
        paint()
        cv.bind("<Enter>", lambda e: paint(True))
        cv.bind("<Leave>", lambda e: paint())
        cv.bind("<Button-1>", lambda e: self.pick(g))

    def draw(self):
        for w in self.frame.winfo_children():
            w.destroy()
        head = tk.Frame(self.frame, bg=CARD)
        head.pack(fill="x", padx=S(6), pady=(S(4), S(6)))
        self._nav(head, "chev_r", 1).pack(side="left")
        self._nav(head, "chev_l", -1).pack(side="right")
        tk.Label(head, text=fa(f"{MONTHS[self.jm - 1]} {self.jy}"), font=F(11, True), bg=CARD, fg=TEXT).pack(
            side="top", expand=True)
        grid = tk.Frame(self.frame, bg=CARD)
        grid.pack(padx=S(4), pady=(0, S(6)))
        for c, w in enumerate(self.WD):
            tk.Label(grid, text=w, font=F(9, True), bg=CARD, fg=MUTED, width=4).grid(row=0, column=c, pady=S(2))
        for r in range(1, 7):
            grid.grid_rowconfigure(r, minsize=S(34))
        first = J.j2g(self.jy, self.jm, 1)
        start = (first.weekday() - 5) % 7
        today = dt.date.today()
        sel = self.owner.get_date()
        for n in range(1, days_in_jmonth(self.jy, self.jm) + 1):
            idx = start + n - 1
            g = J.j2g(self.jy, self.jm, n)
            self._cell(grid, idx // 7 + 1, idx % 7, n, g, sel == g, g == today)
        foot = tk.Frame(self.frame, bg=CARD)
        foot.pack(fill="x", padx=S(6), pady=(0, S(4)))
        Btn(foot, "امروز", lambda: self.pick(today), "tint", size=9, py=5, icon="calendar").pack(side="right")

    def pick(self, g):
        self.owner.set(g)
        self.close()

    def close(self):
        try:
            self.owner.pop = None
            self.destroy()
        except Exception:
            pass


class DateEntry(REntry):
    def __init__(self, parent, d=None, width=11, **kw):
        super().__init__(parent, width=width, justify="center", **kw)
        self.pop = None
        self.set(d or dt.date.today())
        self.bind("<Button-1>", self._open, add="+")

    def _open(self, e=None):
        if self.pop is not None:
            self.pop.close()
            return
        d = self.get_date() or dt.date.today()
        self.pop = JCal(self, d)

    def set(self, d):
        self.var.set(J.fmt(d))

    def get_date(self):
        return J.parse(self.var.get())


class Dropdown(tk.Canvas):
    def __init__(self, parent, values, value=None, width=18, cmd=None, h=38, fill=FILL):
        tf = tfont(F(10))
        self._W = tf.measure("0") * width + S(26)
        self._H = S(h)
        super().__init__(parent, width=self._W, height=self._H, bg=parent["bg"], highlightthickness=0,
                         cursor="hand2")
        self.values, self.cmd, self.top = list(values), cmd, None
        self.fill = fill
        self.value = value if value is not None else (self.values[0] if self.values else "")
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Button-1>", lambda e: self.popup())
        self._draw()

    def _draw(self):
        self.delete("all")
        W = max(self.winfo_width(), 20)
        rrect(self, 1, 1, W - 1, self._H - 1, S(12), fill=self.fill, outline=self.fill)
        self.create_text(W - S(13), self._H / 2, text=self.value, font=F(10), fill=TEXT, anchor="e")
        draw_icon(self, "chevron", S(12), (self._H - S(16)) / 2, S(16), MUTED)

    def get(self):
        return self.value

    def set(self, v):
        self.value = v
        self._draw()

    def set_values(self, values):
        self.values = list(values)

    def popup(self):
        if self.top:
            self.close()
            return
        top = self.top = tk.Toplevel(self)
        top.overrideredirect(True)
        key = "#010203"
        try:
            top.configure(bg=key)
            top.attributes("-transparentcolor", key)
        except tk.TclError:
            top.configure(bg=BG)
        card = rbox(top, CARD, 14, 6)
        card.auto = False
        card.pack(fill="both", expand=True)
        host = card.body
        if len(self.values) > 8:
            sf = ScrollFrame(host, CARD)
            sf.pack(fill="both", expand=True)
            sf.canvas.configure(height=S(8 * 40), width=max(self.winfo_width(), S(200)))
            host = sf.inner
        for v in self.values:
            PickRow(host, v, partial(self._pick, v), BLUE if v == self.value else TEXT).pack(fill="x")
        top.update_idletasks()
        w = max(self.winfo_width(), card.body.winfo_reqwidth() + 2 * (1 + S(6)), S(200))
        h = card.body.winfo_reqheight() + 2 * (1 + S(6))
        sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
        x = min(max(self.winfo_rootx() + self.winfo_width() - w, 4), sw - w - 4)
        y = self.winfo_rooty() + self.winfo_height() + S(4)
        if y + h > sh - 4:
            y = max(4, self.winfo_rooty() - h - S(4))
        top.geometry(f"{w}x{h}+{x}+{y}")
        top.focus_force()
        top.bind("<FocusOut>", lambda e: self.after(80, self.close) if e.widget is top else None)
        top.bind("<Escape>", lambda e: self.close())

    def _pick(self, v, e=None):
        self.value = v
        self._draw()
        self.close()
        if self.cmd:
            self.cmd(v)

    def close(self):
        if self.top:
            try:
                self.top.destroy()
            except Exception:
                pass
            self.top = None


class Segmented(tk.Canvas):
    def __init__(self, parent, items, cmd=None, sel=0, size=10):
        self.items, self.cmd, self.sel = items, cmd, sel
        self._f = F(size, False)
        tf = tfont(self._f)
        self.ws = [tf.measure(t) + S(30) for t in items]
        self._H = tf.metrics("linespace") + S(14)
        super().__init__(parent, width=sum(self.ws) + S(8), height=self._H + S(8), bg=parent["bg"],
                         highlightthickness=0, cursor="hand2")
        self.bind("<Button-1>", self._click)
        self._draw()

    def _spans(self):
        x = sum(self.ws) + S(4)
        out = []
        for w in self.ws:
            out.append((x - w, x))
            x -= w
        return out

    def _draw(self):
        self.delete("all")
        W = sum(self.ws) + S(8)
        rrect(self, 0, 0, W, self._H + S(8), (self._H + S(8)) / 2, fill=FILL2, outline="")
        for i, (a, b) in enumerate(self._spans()):
            if i == self.sel:
                rrect(self, a, S(4), b, S(4) + self._H, self._H / 2, fill=CARD, outline="#DADAE0")
            self.create_text((a + b) / 2, S(4) + self._H / 2, text=self.items[i], font=self._f,
                             fill=BLUE if i == self.sel else MUTED)

    def _click(self, e):
        for i, (a, b) in enumerate(self._spans()):
            if a <= e.x <= b:
                self.sel = i
                self._draw()
                if self.cmd:
                    self.cmd(i)
                return


class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.vsb = RScroll(self, self.canvas.yview, bg)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="left", fill="y")
        self.canvas.pack(side="right", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: (self.canvas.configure(scrollregion=self.canvas.bbox("all")),
                                                  self.canvas.after_idle(self._clamp)))
        self.canvas.bind("<Configure>", lambda e: (self.canvas.itemconfigure(self.win, width=e.width),
                                                   self.canvas.after_idle(self._clamp)))

    def _clamp(self):
        """اگر محتوا کوچک شد یا پنجره عوض شد، نمایش را داخل محدوده واقعی محتوا نگه می دارد
        (جلوگیری از اینکه صفحه خالی دیده شود وقتی از ته اسکرول شده بود)"""
        try:
            sr = self.canvas.bbox("all")
            if not sr:
                return
            ch = self.canvas.winfo_height()
            total = sr[3] - sr[1]
            if total <= ch:
                self.canvas.yview_moveto(0)
                return
            top = self.canvas.canvasy(0)
            limit = sr[3] - ch
            if top > limit or top < sr[1]:
                self.canvas.yview_moveto(max(0.0, (limit - sr[1]) / total))
        except Exception:
            pass

    def _wheel(self, e):
        if self.inner.winfo_reqheight() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-e.delta / 120), "units")

    def clear(self):
        for w in self.inner.winfo_children():
            w.destroy()


def _global_wheel(e):
    """چرخ موس: اسکرول نزدیکترین ScrollFrame به نشانگر (حتی وقتی روی دکمه/متن کودک است)"""
    if e.state & 0x0004:  # Ctrl+چرخ = تغییر اندازه متن
        return
    w = e.widget
    while w is not None and not isinstance(w, str):
        if isinstance(w, ScrollFrame):
            w._wheel(e)
            return
        w = getattr(w, "master", None)


class Dlg(tk.Toplevel):
    def __init__(self, app, title, minw=420):
        super().__init__(app.root)
        self.app = app
        self.title(title)
        self.configure(bg=BG)
        self.transient(app.root)
        self.minw = S(minw)
        self.card = Card(self, pad=16)
        self.card.pack(fill="both", expand=True, padx=S(12), pady=S(12))
        self.body = self.card.body

    def finish(self, modal=True):
        titlebar_dark(self)
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), self.minw) + S(24)
        h = self.winfo_reqheight() + S(24)
        r = self.app.root
        x = r.winfo_rootx() + (r.winfo_width() - w) // 2
        y = r.winfo_rooty() + (r.winfo_height() - h) // 2
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h - 40))
        self.geometry(f"{w}x{h}+{x}+{y}")
        if modal:
            try:
                self.grab_set()
            except Exception:
                pass


def info(app, text):
    d = Dlg(app, "انبارمن", 360)
    lbl(d.body, text, 10, wraplength=S(340)).pack(anchor="e", pady=(0, S(14)))
    Btn(d.body, "باشه", d.destroy, "primary", w=100).pack(anchor="w")
    d.finish()
    app.root.wait_window(d)


def ask(app, text, yes="بله"):
    d = Dlg(app, "انبارمن", 360)
    res = {"v": False}
    lbl(d.body, text, 10, wraplength=S(340)).pack(anchor="e", pady=(0, S(14)))
    row = tk.Frame(d.body, bg=CARD)
    row.pack(anchor="w")

    def ok():
        res["v"] = True
        d.destroy()
    Btn(row, yes, ok, "primary").pack(side="left")
    Btn(row, "انصراف", d.destroy).pack(side="left", padx=S(8))
    d.finish()
    app.root.wait_window(d)
    return res["v"]


class Stepper(tk.Frame):
    def __init__(self, parent, value=1, minimum=0, maximum=10 ** 6, cb=None):
        super().__init__(parent, bg=parent["bg"])
        self.min, self.max, self.cb = minimum, maximum, cb
        Btn(self, "", lambda: self.set(self.get() + 1), "tint", size=12, w=34, h=34, icon="plus").pack(side="right")
        self.e = REntry(self, width=4, justify="center", h=34)
        self.e.pack(side="right", padx=S(5))
        Btn(self, "", lambda: self.set(self.get() - 1), "tint", size=12, w=34, h=34, icon="minus").pack(side="right")
        self.e.e.bind("<FocusOut>", lambda e: self.set(self.get()), add="+")
        self.e.e.bind("<Return>", lambda e: self.set(self.get()))
        self.set(value, call=False)

    def get(self):
        d = "".join(c for c in to_en(self.e.get()) if c.isdigit())
        return max(self.min, min(self.max, int(d) if d else self.min))

    def set(self, v, call=True):
        v = max(self.min, min(self.max, int(v)))
        self.e.set_text(fa(v))
        if call and self.cb:
            self.cb()


# ---------------------------------------------------------------- نمودار
def catmull(pts, steps=10):
    if len(pts) < 3:
        return pts
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


class Chart(tk.Canvas):
    def __init__(self, parent, height=260):
        super().__init__(parent, bg=CARD, highlightthickness=0, height=S(height))
        self.labels, self.series = [], []
        self.bind("<Configure>", lambda e: later(self, "_dj", self.draw, 24))
        self.bind("<Motion>", self.hover)
        self.bind("<Leave>", lambda e: self.delete("tip"))

    def set_data(self, labels, series):
        self.labels, self.series = labels, series
        self.draw()

    def geom(self):
        W, H = self.winfo_width(), self.winfo_height()
        l, r, t, b = S(8), S(74), S(14), S(30)
        return W, H, l, r, t, b

    def draw(self):
        self.delete("all")
        W, H, l, r, t, b = self.geom()
        if W < 50:
            return
        pw, ph = W - l - r, H - t - b
        vals = [v for s in self.series for v in s["values"]]
        m = max(vals) if vals else 0
        mx = 1
        if m > 0:
            mag = 10 ** (len(str(int(m))) - 1)
            mx = next((k * mag for k in (1, 2, 2.5, 5, 10) if m <= k * mag), m)
        self.mx = mx
        for i in range(5):
            y = t + ph * i / 4
            self.create_line(l, y, W - r, y, fill="#EEEEF3", dash=(3, 5))
            self.create_text(W - r + S(8), y, text=short(mx * (1 - i / 4)), anchor="w", font=F(8), fill=FAINT)
        n = len(self.labels)
        self.xs = [l + pw * (1 - (i / (n - 1 if n > 1 else 1))) for i in range(n)]
        step = max(1, n // 7)
        for i in range(0, n, step):
            self.create_text(self.xs[i], H - S(12), text=self.labels[i], font=F(8), fill=FAINT)
        if not vals or m == 0:
            self.create_text(W / 2, H / 2, text="هنوز داده ای برای نمایش وجود ندارد", font=F(10), fill=FAINT)
            return
        for s in self.series:
            pts = [(self.xs[i], t + ph * (1 - v / mx)) for i, v in enumerate(s["values"])]
            if len(pts) < 2:
                continue
            dense = [(x, min(max(y, t), t + ph)) for x, y in catmull(pts)]
            self.create_polygon([c for p in dense for c in p] + [dense[-1][0], t + ph, dense[0][0], t + ph],
                                fill=s["tint"], outline="")
            self.create_line([c for p in dense for c in p], fill=s["color"], width=max(2, S(3)),
                             capstyle="round", joinstyle="round")

    def hover(self, e):
        self.delete("tip")
        if not self.labels or not getattr(self, "xs", None):
            return
        W, H, l, r, t, b = self.geom()
        i = min(range(len(self.xs)), key=lambda k: abs(self.xs[k] - e.x))
        x = self.xs[i]
        self.create_line(x, t, x, H - b, fill="#D1D1D6", tags="tip")
        lines = [self.labels[i]] + [f"{s['name']}: {short(s['values'][i])}" for s in self.series]
        tw = S(150)
        bx = min(max(x - tw / 2, S(4)), W - tw - S(4))
        rrect(self, bx, t, bx + tw, t + S(20 * len(lines) + 10), S(10), fill="#1C1C1E", outline="", tags="tip")
        for k, ln in enumerate(lines):
            self.create_text(bx + tw / 2, t + S(18 + 20 * k) - S(4), text=ln, font=F(9), fill="#FFFFFF", tags="tip")


class SalesTree(tk.Frame):
    HEAD = ["روز / کالا", "تعداد", "قیمت واحد", "مبلغ فروش (تومان)", "سود تقریبی"]
    # سطح ۰: کامل | ۱: بدون «قیمت واحد» | ۲: فقط نام، مبلغ و سود (ستون ها: سود، مبلغ، قیمت واحد، تعداد)
    LV = {0: (130, 170, 120, 70), 1: (110, 130, 0, 56), 2: (84, 100, 0, 0)}

    def __init__(self, parent, bg=CARD):
        super().__init__(parent, bg=bg)
        self.bgc = bg
        self.lv = 0
        hb = self.hb = rbox(self, FILL, 12)
        hb.pack(fill="x")
        self.cells(hb.body, self.HEAD, True, MUTED, FILL, 9, size=9)
        self.body = tk.Frame(self, bg=bg)
        self.body.pack(fill="x")

    @property
    def W(self):
        c = self.LV[self.lv]
        return [S(c[0]), S(c[1]), S(c[2]), S(c[3]), 0]

    def set_level(self, lv):
        self.lv = lv
        for w in self.hb.body.winfo_children():
            w.destroy()
        self.cells(self.hb.body, self.HEAD, True, MUTED, FILL, 9, size=9)

    def cells(self, parent, texts, bold=False, fg=TEXT, bg=CARD, py=8, indent=0, size=10):
        W = self.W
        for c in range(5):
            parent.grid_columnconfigure(c, minsize=W[c], weight=1 if c == 4 else 0)
        px = S(4) if self.lv else S(8)
        for i, t in enumerate(texts):
            c = 4 - i
            if c < 4 and W[c] == 0:
                continue
            wl = (0, S(150), S(110))[self.lv] if i == 0 else 0
            tk.Label(parent, text=t, font=F(size, bold), fg=fg, bg=bg, anchor="e" if i == 0 else "center",
                     wraplength=wl, justify="right").grid(
                row=0, column=c, sticky="nsew", padx=(px, px + S(4) + (indent if i == 0 else 0)), pady=S(py))

    def clear(self):
        for w in self.body.winfo_children():
            w.destroy()

    def node(self, parent, texts, builder=None, bold=True, fg=TEXT, bg=CARD, indent=0, expand=False):
        holder = tk.Frame(parent, bg=self.bgc)
        holder.pack(fill="x")
        rb = None
        if bg != self.bgc:
            rb = rbox(holder, bg, 10)
            rb.pack(fill="x", pady=1)
            row = rb.body
            if builder:
                rb.configure(cursor="hand2")
        else:
            row = tk.Frame(holder, bg=bg, cursor="hand2" if builder else "")
            row.pack(fill="x")
        self.cells(row, texts, bold, fg, bg, 8, indent)
        tk.Frame(holder, bg=SEP, height=1).pack(fill="x")
        body = tk.Frame(holder, bg=self.bgc)
        st = {"open": False, "built": False}

        def toggle(e=None):
            if not builder:
                return
            if st["open"]:
                body.pack_forget()
                st["open"] = False
            else:
                if not st["built"]:
                    builder(body)
                    st["built"] = True
                body.pack(fill="x")
                st["open"] = True
        if builder:
            for w in [row] + row.winfo_children() + ([rb] if rb is not None else []):
                w.bind("<Button-1>", toggle)
        if expand:
            toggle()
        return body

    def fill(self, rows, d1, d2, show_empty=True, group_months=False):
        self.clear()
        by = {}
        for r in rows:
            by.setdefault(r["date"], []).append(r)
        if show_empty:
            days, cur = [], d2
            while cur >= d1:
                days.append(cur.isoformat())
                cur -= dt.timedelta(days=1)
        else:
            days = sorted(by, reverse=True)
        tot = [0, 0, 0]
        best = None
        months = {}
        for iso in days:
            d = dt.date.fromisoformat(iso)
            items = by.get(iso, [])
            s = sum(i["total"] for i in items)
            q = sum(i["qty"] for i in items)
            pr = sum((i["unit_price"] - i["cost"]) * i["qty"] for i in items)
            tot[0] += s
            tot[1] += q
            tot[2] += pr
            if s and (best is None or s > best[1]):
                best = (d, s)
            months.setdefault(J.to_jalali(d)[:2] if group_months else None, []).append((d, items, s, q, pr))
        today = dt.date.today()

        def day_node(parent, d, items, s, q, pr, indent=0):
            texts = [f"{J.WEEKDAYS[d.weekday()]}   {J.fmt(d)}", fa(q) if q else "—", "",
                     money(s) if s else "—", money(pr) if s else "—"]
            fg = FAINT if not s else (BLUE if d == today else TEXT)

            def build(body):
                for it in items:
                    self.node(body, [it["product_name"], fa(it["qty"]), money(it["unit_price"]), money(it["total"]),
                                     money((it["unit_price"] - it["cost"]) * it["qty"])],
                              None, False, MUTED, "#FAFAFD", indent + S(22))
            self.node(parent, texts, build if items else None, True, fg, CARD, indent,
                      expand=bool(items) and (d == today or len(days) <= 8))
        if group_months:
            for (jy, jm), lst in months.items():
                mq, ms, mp = sum(x[3] for x in lst), sum(x[2] for x in lst), sum(x[4] for x in lst)

                def mbuild(body, lst=lst):
                    for d, items, s, q, pr in lst:
                        day_node(body, d, items, s, q, pr, S(14))
                self.node(self.body, [f"{J.MONTHS[jm - 1]} {fa(jy)}", fa(mq), "", money(ms), money(mp)],
                          mbuild, True, BLUE, BLUE_BG)
        else:
            for d, items, s, q, pr in months.get(None, []):
                day_node(self.body, d, items, s, q, pr)
        return tot, best



# ======================================================================= گفتگوها
def usd_text(usd, cur="USD"):
    d = int(usd)
    c = int(round((usd - d) * 100))
    if c >= 100:
        d, c = d + 1, 0
    unit, sub = ("درهم", "فلس") if cur == "AED" else ("دلار", "سنت")
    return f"{money(d)} {unit} و {fa(f'{c:02d}')} {sub}"


def price_move(now, prev):
    """تغییر نرخ نسبت به نرخ قبلی: متن و رنگ"""
    if not now or not prev or abs(now - prev) < 1e-9:
        return "", MUTED
    pct = (now - prev) * 100.0 / prev
    up = now > prev
    txt = ("▲ " if up else "▼ ") + fa(f"{abs(pct):.1f}").replace(".", "٫") + "٪"
    return txt, (GREEN if up else RED)


class ProductDialog(Dlg):
    def __init__(self, app, pid=None):
        super().__init__(app, "ویرایش کالا" if pid else "افزودن کالای جدید", 700)
        self.db, self.pid, self.saved = app.db, pid, False
        self.img_src = None
        p = self.db.product(pid) if pid else None
        self.img_name = p["image"] if p else None
        self._orig_name = (p["name"] if p else "") or ""
        self._orig_img = self.img_name
        b = self.body
        heading(b, "ویرایش کالا" if pid else "افزودن کالای جدید", 16, "edit" if pid else "plus", BLUE).pack(anchor="e", pady=(0, S(12)))
        main = tk.Frame(b, bg=CARD)
        main.pack(fill="x")
        imgcol = tk.Frame(main, bg=CARD)
        imgcol.pack(side="right", anchor="n", padx=(S(18), 0))
        self.img_lbl = ImgBox(imgcol, 116)
        self.img_lbl.pack()
        Btn(imgcol, "پیدا کردن عکس", self.find_image, "tint", size=9, w=116, h=34).pack(pady=(S(10), S(6)))
        self.img_status = lbl(imgcol, "", 8, fg=MUTED, anchor="center", wraplength=S(116))
        self.img_status.pack(pady=(0, S(6)))
        Btn(imgcol, "انتخاب عکس", self.pick_img, "tint", size=9, w=116, h=34).pack(pady=(0, S(6)))
        Btn(imgcol, "حذف عکس", self.clear_img, "plain", size=9, w=116, h=34).pack()

        form = tk.Frame(main, bg=CARD)
        form.pack(side="right", fill="x", expand=True)
        form.grid_columnconfigure(0, weight=1)

        def row(i, text, w, sticky="ew"):
            row_label(form, text).grid(row=i, column=1, sticky="e", padx=(S(12), 0), pady=S(6))
            w.grid(row=i, column=0, sticky=sticky, pady=S(6))
        self.name = REntry(form, width=30, placeholder="مثلا: اسپیکر JBL 120")
        self.name.set_text(p["name"] if p else "")
        row(0, "نام کالا (دقیق، با مدل)", self.name)
        self.cats = {c["name"]: c["id"] for c in self.db.categories()}
        self.cat = Dropdown(form, ["بدون دسته"] + list(self.cats),
                            p["cat_name"] if p and p["cat_name"] else "بدون دسته", width=26)
        row(1, "دسته بندی", self.cat)
        self.qty = Stepper(form, p["qty"] if p else 1, 0)
        row(2, "تعداد موجود", self.qty, "e")
        self.cur = Dropdown(form, [n for _, n in CURRENCIES], CUR_NAME.get(p["buy_cur"], "تومان") if p else "تومان",
                            width=26, cmd=lambda v: self.preview())
        row(3, "ارز خرید", self.cur)
        amt0 = (p["buy_amount"] if p and p["buy_cur"] != "IRT" else (p["buy_price"] if p else 0))
        self.amt = AmountEntry(form, amt0, decimals=True, width=26, cb=self.preview)
        row(4, "مبلغ خرید (هر عدد)", self.amt)
        self.prev = lbl(form, "", 9, fg=BLUE)
        self.prev.grid(row=5, column=0, columnspan=2, sticky="e")
        self.sell_orig = 0.0
        if p and p["sell_price"]:
            self.sell_orig = float(p["sell_usd"]) if (p["sell_cur"] != "IRT" and p["sell_usd"]) else float(p["sell_price"])
        scur0 = (p["sell_cur"] if p and p["sell_cur"] else None) or (p["buy_cur"] if p and p["buy_cur"] in ("USD", "AED") else "IRT")
        self.scur = Dropdown(form, [n for _, n in CURRENCIES], CUR_NAME.get(scur0, "تومان"),
                             width=26, cmd=lambda v: self.on_scur())
        self._scode = scur0
        row(6, "ارز قیمت فروش", self.scur)
        self.sell = AmountEntry(form, self.sell_orig, decimals=True, width=26, cb=self.on_sell_change)
        row(7, "قیمت فروش (هر عدد)", self.sell)
        # درصد سود نسبت به قیمت خرید
        mk = tk.Frame(form, bg=CARD)
        self.markup = AmountEntry(mk, 0, decimals=True, width=12, cb=self.on_markup_change)
        self.markup.pack(side="right")
        lbl(mk, "٪ سود روی خرید", 9, fg=MUTED).pack(side="right", padx=(S(8), S(6)))
        Btn(mk, "اعمال درصد", self.apply_markup, "tint", size=8, py=4, h=32).pack(side="left")
        row(8, "درصد سود پیشنهادی", mk)
        self.sell_prev = lbl(form, "", 9, fg=GREEN)
        self.sell_prev.grid(row=9, column=0, columnspan=2, sticky="e")
        self.date = DateEntry(form, dt.date.fromisoformat(p["buy_date"]) if p and p["buy_date"] else None, width=26)
        row(10, "تاریخ خرید (شمسی)", self.date)
        self.barcode = REntry(form, width=26, placeholder="مثلا 6291234567890 یا A123456789a (بدون فاصله)")
        self.barcode.set_text(p["barcode"] if p and p["barcode"] else "")
        row(11, "بارکد", self.barcode)
        self._markup_lock = False
        options = tk.Frame(b, bg=CARD)
        options.pack(fill="x", anchor="e", pady=(S(10), 0))
        self.service = Switch(options, "خدمات (موجودی نامحدود)", bool(p and p["is_service"]))
        self.service.pack(anchor="e", pady=S(3))
        self.fetch = Switch(options, "گرفتن قیمت از دیجی کالا", bool(p["auto_price"]) if p else True)
        self.fetch.pack(anchor="e", pady=S(3))
        bl = tk.Frame(b, bg=CARD)
        bl.pack(fill="x", pady=(S(14), 0))
        Btn(bl, "ذخیره", self.save, "primary", w=110).pack(side="left")
        Btn(bl, "انصراف", self.destroy, w=110).pack(side="left", padx=(S(8), 0))
        if self.pid:
            Btn(bl, "حذف کالا", self.delete_this, "danger", w=110).pack(side="left", padx=(S(8), 0))
        self.refresh_img()
        self.preview()
        self.preview_sell()
        try:
            self._sync_markup_from_sell()
        except Exception:
            pass
        self.finish()
        self.name.focus_entry()

    def delete_this(self):
        p = self.db.product(self.pid)
        if ask(self.app, f"«{p['name']}» حذف شود؟\n(سوابق فروش قبلی در آرشیو می ماند)", "حذف"):
            self.db.delete_product(self.pid)
            self.app.reload_all()
            self.destroy()

    def code(self):
        return next((k for k, n in CURRENCIES if n == self.cur.get()), "IRT")

    def preview(self):
        code = self.code()
        rate = 1 if code == "IRT" else self.app.rate(code)
        if code == "IRT":
            self.prev.config(text="")
        else:
            self.prev.config(text=(f"ارزش امروز هر عدد: {money(self.amt.get_num() * rate)} تومان "
                                   f"(نرخ {CUR_SHORT[code]}: {money(rate)})") if rate else "نرخ ارز هنوز دریافت نشده")

    def scur_code(self):
        return next((k for k, n in CURRENCIES if n == self.scur.get()), "USD")

    def on_scur(self):
        """وقتی ارز قیمت فروش عوض می شود، مبلغ وارد شده به ارز جدید تبدیل می شود"""
        new, old = self.scur_code(), self._scode
        self._scode = new
        amt = self.sell.get_num()
        if amt > 0 and new != old:
            ro = 1 if old == "IRT" else self.app.rate(old)
            rn = 1 if new == "IRT" else self.app.rate(new)
            if ro and rn:
                self.sell.set(round(amt * ro / rn, 2))
        self.preview_sell()

    def preview_sell(self):
        amt = self.sell.get_num()
        code = self.scur_code()
        if amt <= 0:
            self.sell_prev.config(text="")
            return
        if code == "IRT":
            rate_u = self.app.rate("USD")
            if not rate_u:
                self.sell_prev.config(text="نرخ دلار هنوز دریافت نشده است")
                return
            self.sell_prev.config(text=(f"این تومان با توجه به قیمت دلار می شود: {usd_text(amt / rate_u, 'USD')}   "
                                        f"(نرخ دلار: {money(int(round(rate_u)))} تومان)\n"
                                        f"این یک قیمت فروش پیشنهادی است و با توجه به قیمت دلار بالا و پایین می شود."))
            return
        unit = CUR_SHORT[code]
        rate = self.app.rate(code)
        if not rate:
            self.sell_prev.config(text="نرخ هنوز دریافت نشده است")
            return
        self.sell_prev.config(text=(f"معادل: {money(int(round(amt * rate)))} تومان   (نرخ {unit}: {money(int(round(rate)))} تومان)\n"
                                    f"این یک قیمت فروش پیشنهادی است و با توجه به قیمت {unit} بالا و پایین می شود."))
        self._sync_markup_from_sell()

    def _buy_toman(self):
        """قیمت خرید هر عدد به تومان"""
        code = self.code()
        amount = self.amt.get_num()
        if code == "IRT":
            return amount
        rate = self.app.rate(code) or 0
        return amount * rate if rate else 0

    def _sell_toman(self):
        amt = self.sell.get_num()
        code = self.scur_code()
        if code == "IRT":
            return amt
        rate = self.app.rate(code) or 0
        return amt * rate if rate else 0

    def _sync_markup_from_sell(self):
        """درصد سود را از روی قیمت فروش و خرید محاسبه می‌کند"""
        if getattr(self, "_markup_lock", False):
            return
        buy = self._buy_toman()
        sell = self._sell_toman()
        if buy <= 0 or sell <= 0:
            return
        pct = (sell - buy) * 100.0 / buy
        self._markup_lock = True
        try:
            self.markup.set(round(pct, 1))
        except Exception:
            pass
        self._markup_lock = False

    def on_sell_change(self):
        self.preview_sell()

    def on_markup_change(self):
        """با تغییر درصد، قیمت فروش را از خرید می‌سازد (اگر قفل نباشد)"""
        if getattr(self, "_markup_lock", False):
            return
        # فقط نمایش؛ اعمال با دکمه «اعمال درصد» تا موقع تایپ پرش نکند
        pass

    def apply_markup(self):
        """قیمت فروش = خرید × (1 + درصد/100) به همان ارز فروش فعلی"""
        buy = self._buy_toman()
        if buy <= 0:
            info(self.app, "اول مبلغ خرید را وارد کنید.")
            return
        pct = self.markup.get_num()
        sell_toman = buy * (1 + pct / 100.0)
        code = self.scur_code()
        self._markup_lock = True
        try:
            if code == "IRT":
                self.sell.set(int(round(sell_toman)))
            else:
                rate = self.app.rate(code)
                if not rate:
                    info(self.app, "نرخ ارز هنوز دریافت نشده است.")
                    return
                self.sell.set(round(sell_toman / rate, 2))
        finally:
            self._markup_lock = False
        self.preview_sell()

    def refresh_img(self):
        path = self.img_src or self.db.image_path(self.img_name)
        self.ph = self.app.thumb_path(path, S(110))
        self.img_lbl.config(image=self.ph, width=S(116), height=S(116))

    def pick_img(self):
        f = filedialog.askopenfilename(parent=self, filetypes=[("تصاویر", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if f:
            self.img_src = f
            self.refresh_img()

    def clear_img(self):
        self.img_src = self.img_name = None
        self.refresh_img()

    def find_image(self):
        name = self.name.get().strip()
        if not name:
            self.img_status.config(text="اول نام کالا را وارد کنید", fg=RED)
            return
        if getattr(self, "_finding", False):
            return
        self._finding = True
        # اگر نام عوض شده، عکس قبلی را کنار بگذار تا عکس محصول جدید بیاید
        if name != (self._orig_name or ""):
            self.img_src = None
            # img_name را فعلاً نگه می‌داریم تا اگر جستجو شکست خورد، عکس قبلی نپرد
        self.img_status.config(text="در حال جستجوی عکس برای نام جدید...", fg=MUTED)

        def work():
            try:
                url = P.fetch_digikala_image(name, strict=True)
                if not url:
                    # بدون strict هم یک‌بار دیگر
                    url = P.fetch_digikala_image(name, strict=False)
                if not url:
                    msg = ("عکسی برای این نام پیدا نشد", RED, None)
                else:
                    cover = fetch_cover(url, self.db)
                    msg = ("عکس جدید پیدا و ذخیره شد", GREEN, cover) if cover else ("دانلود عکس ناموفق بود", RED, None)
            except Exception:
                msg = ("اینترنت یا دسترسی به دیجی کالا برقرار نیست؛ دوباره بزنید", RED, None)
            self.app.q.put(lambda: self._find_done(msg))
        threading.Thread(target=work, daemon=True).start()

    def _find_done(self, msg):
        text, col, cover = msg
        self._finding = False
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if cover:
            # کش تصویر قدیمی را پاک کن تا همان فایل قبلی نشان داده نشود
            try:
                keys = [k for k in list(self.app.imgcache) if self._orig_img and self._orig_img in str(k[0])]
                for k in keys:
                    self.app.imgcache.pop(k, None)
            except Exception:
                pass
            self.img_name, self.img_src = cover, None
            self._orig_img = cover
            self.refresh_img()
        self.img_status.config(text=text, fg=col)

    def save(self):
        name = self.name.get().strip()
        if not name:
            info(self.app, "نام کالا را وارد کنید.")
            return
        bd = self.date.get_date()
        if not bd:
            info(self.app, "تاریخ خرید معتبر نیست. نمونه: ۱۴۰۵/۰۷/۲۰")
            return
        barcode = clean_barcode(self.barcode.get())
        if barcode and re.search(r"[^A-Za-z0-9\-_./+]", barcode):
            info(self.app, "بارکد فقط میتواند شامل حروف انگلیسی، عدد و علامت های - _ . / + باشد.")
            return
        if barcode:
            owner = self.db.product_by_barcode(barcode, self.pid)
            if owner:
                info(self.app, f"این بارکد قبلا برای کالای دیگری ثبت شده:\n{self.db.product(owner)['name']}")
                return
        code, amount = self.code(), self.amt.get_num()
        if code == "IRT":
            buy_price = int(round(amount))
        else:
            rate = self.app.rate(code)
            if not rate:
                info(self.app, "نرخ ارز هنوز دریافت نشده؛ چند ثانیه صبر کنید یا اینترنت را بررسی کنید.")
                return
            buy_price = int(round(amount * rate))
        old = self.db.product(self.pid) if self.pid else None
        scode, samt = self.scur_code(), self.sell.get_num()
        if samt <= 0:
            sell_usd, sell_price, scode = 0.0, 0, "USD"
        elif scode == "IRT":
            # تومان وارد شده به دلار تبدیل و پایه دلاری ثبت می شود تا با نرخ دلار بالا و پایین شود
            rate_u = self.app.rate("USD")
            if not rate_u:
                info(self.app, "نرخ دلار هنوز دریافت نشده است. چند ثانیه صبر کنید یا اینترنت را بررسی کنید.")
                return
            if old and old["sell_usd"] and (old["sell_cur"] or "USD") != "IRT" and abs(int(old["sell_price"] or 0) - samt) < 1:
                sell_usd, scode = float(old["sell_usd"]), (old["sell_cur"] or "USD")
            else:
                sell_usd, scode = samt / rate_u, "USD"
            sell_price = int(round(samt))
        else:
            rate_s = self.app.rate(scode)
            if not rate_s:
                info(self.app, "نرخ ارز فروش هنوز دریافت نشده است. چند ثانیه صبر کنید یا اینترنت را بررسی کنید.")
                return
            if old and old["sell_usd"] and (old["sell_cur"] or "USD") == scode and abs(float(old["sell_usd"]) - samt) < 0.005:
                sell_usd = float(old["sell_usd"])  # قیمت تغییر نکرده: پایه قبلی حفظ شود
            else:
                sell_usd = samt
            sell_price = int(round(sell_usd * rate_s))
        cid = self.cats.get(self.cat.get())
        image = self.img_name
        if self.img_src:
            self.config(cursor="watch")
            self.update()
            image = self.db.store_image(self.img_src)
        data = dict(name=name, category_id=cid, qty=self.qty.get(), buy_price=buy_price, buy_date=bd.isoformat(),
                    buy_cur=code, buy_amount=0 if code == "IRT" else amount, image=image,
                    note="", barcode=barcode, is_service=1 if self.service.get() else 0,
                    sell_price=sell_price, sell_usd=sell_usd, sell_cur=scode,
                    auto_price=1 if self.fetch.get() else 0)
        if self.pid:
            self.db.update_product(self.pid, data)
            self.result_pid = self.pid
        else:
            self.result_pid = self.db.add_product(data)
        # اگر نام عوض شده و عکس قدیمی مانده، بعد از ذخیره عکس را برای نام جدید بگیر
        name_changed = (name != (self._orig_name or ""))
        if name_changed and self.img_name == self._orig_img and self.img_src is None:
            # عکس مربوط به نام قبلی است → بعد از ذخیره دوباره جستجو شود
            self.want_fetch = True
            # تصویر را خالی نکنیم تا تا قبل از دانلود جدید خالی نباشد؛ start_fetch با need_img هم کار می‌کند
            if self.result_pid:
                # need_img را True کنیم با پاک کردن موقت؟ بهتر: force fetch image
                pass
        else:
            self.want_fetch = self.fetch.get()
        self._name_changed = name_changed
        self.saved = True
        self.destroy()


class SupportDialog(Dlg):
    SITE = "https://www.myhadipour.ir/"
    PAY = "https://www.myhadipour.ir/hemayat"
    GITHUB = "https://github.com/myhadipour"

    def __init__(self, app):
        super().__init__(app, "حمایت از انبارمن", 400)
        b = self.body
        W = S(370)
        try:
            self._ph = icons.load_author()
            tk.Label(b, image=self._ph, bg=CARD).pack(pady=(0, S(4)))
        except Exception:
            tile(b, "heart", RED, 48, 16).pack(pady=(0, S(4)))
        lbl(b, "حسین هادی پور", 13, True, anchor="center").pack(fill="x")
        lbl(b, "سازنده انبارمن", 9, fg=MUTED, anchor="center").pack(fill="x")
        lbl(b, f"نسخه {fa(APP_VERSION)}", 9, True, fg=BLUE, anchor="center").pack(fill="x", pady=(S(2), 0))
        lbl(b, "اگر انبارمن به کار شما می آید، با حمایت خود به ادامه توسعه آن کمک کنید.", 9, anchor="center",
            wraplength=W, justify="center").pack(fill="x", pady=(S(6), S(8)))
        warn = rbox(b, FILL, 12, 2)
        warn.pack(fill="x", pady=(0, S(8)))
        lbl(warn.body, "قیمت های دیجی کالا ممکن است کمی با قیمت واقعی فرق داشته باشد. قبل از فروش بررسی کنید.",
            8, fg=TEXT, bg=FILL, wraplength=W - S(20), justify="right").pack(anchor="e", padx=S(8), pady=S(6))
        br = tk.Frame(b, bg=CARD)
        br.pack(fill="x")
        br.grid_columnconfigure(0, weight=1, uniform="sp")
        br.grid_columnconfigure(1, weight=1, uniform="sp")
        Btn(br, "گیت‌هاب", lambda: webbrowser.open(self.GITHUB), "tint", size=10, h=40,
            icon="external", flex=True).grid(row=0, column=0, sticky="ew", padx=(0, S(3)))
        Btn(br, "حمایت از سازنده", self.pay, "primary", size=10, h=40, icon="heart", flex=True).grid(
            row=0, column=1, sticky="ew", padx=(S(3), 0))
        box = rbox(b, FILL, 12, 2)
        box.pack(fill="x", pady=(S(8), 0))
        row = tk.Frame(box.body, bg=FILL)
        row.pack(fill="x", padx=S(8), pady=S(5))
        tile(row, "mail", BLUE, 28, 9).pack(side="right")
        col = tk.Frame(row, bg=FILL)
        col.pack(side="right", padx=S(8))
        lbl(col, "ایمیل پشتیبانی", 8, fg=MUTED, bg=FILL).pack(anchor="e")
        lbl(col, SUPPORT_EMAIL, 10, True, anchor="e", bg=FILL).pack(anchor="e")
        Btn(row, "", self.copy_mail, "plain", size=8, w=32, h=28, icon="copy").pack(side="left", padx=S(3))
        Btn(row, "", lambda: webbrowser.open("mailto:" + SUPPORT_EMAIL), "tint", size=8, w=32, h=28,
            icon="mail").pack(side="left")
        Btn(b, "بستن", self.destroy, "plain", size=9, py=4).pack(anchor="w", pady=(S(8), 0))
        self.finish()

    def pay(self):
        webbrowser.open(SUPPORT_URL or self.PAY)

    def copy_mail(self):
        self.clipboard_clear()
        self.clipboard_append(SUPPORT_EMAIL)


class SaleDialog(Dlg):
    def __init__(self, app, pid):
        super().__init__(app, "ثبت فروش", 420)
        self.db, self.pid, self.done = app.db, pid, False
        p = self.db.product(pid)
        b = self.body
        heading(b, p["name"][:40], 14, "cart", GREEN).pack(anchor="e")
        if p["barcode"]:
            lbl(b, "بارکد: " + ltr(p["barcode"]), 9, fg=MUTED).pack(anchor="e")
        lbl(b, f"موجودی: {fa(p['qty'])} عدد", 9, fg=MUTED).pack(anchor="e", pady=(0, S(6)))
        self.customer = REntry(b, 28, h=34, placeholder="نام خریدار / مشتری")
        self.customer.pack(fill="x", pady=(0, S(8)))
        g = tk.Frame(b, bg=CARD)
        g.pack(fill="x")
        g.grid_columnconfigure(0, weight=1)
        self.qty = Stepper(g, 1, 1, 10 ** 9, cb=self.upd)
        self.price = AmountEntry(g, p["sell_price"] or p["buy_price"], cb=self.upd, width=22)
        self.date = DateEntry(g, width=22)
        for i, (t, w) in enumerate([("تعداد", self.qty), ("قیمت فروش هر عدد (تومان)", self.price),
                                    ("تاریخ فروش", self.date)]):
            row_label(g, t).grid(row=i, column=1, sticky="e", padx=(S(12), 0), pady=S(6))
            w.grid(row=i, column=0, sticky="e" if i == 0 else "ew", pady=S(6))
        self.total = lbl(b, "", 13, True, fg=BLUE)
        self.total.pack(anchor="e", pady=S(10))
        bl = tk.Frame(b, bg=CARD)
        bl.pack(anchor="w")
        Btn(bl, "ثبت فروش", self.save, "primary", w=120).pack(side="left")
        Btn(bl, "انصراف", self.destroy).pack(side="left", padx=S(8))
        self.upd()
        self.finish()
        self.bind("<Return>", lambda e: self.save())

    def upd(self):
        self.total.config(text=f"جمع: {money(self.qty.get() * self.price.get_int())} تومان")

    def save(self):
        d = self.date.get_date()
        if not d or self.price.get_int() <= 0:
            info(self.app, "تاریخ و قیمت فروش را درست وارد کنید.")
            return
        try:
            self.db.add_sale(self.pid, self.qty.get(), self.price.get_int(), d, customer=self.customer.var.get().strip(), allow_overstock=True)
        except ValueError as e:
            info(self.app, str(e))
            return
        except Exception as e:
            info(self.app, f"ثبت فروش انجام نشد:\n{e}")
            return
        self.done = True
        self.destroy()


class Swatch(tk.Canvas):
    """مربع رنگی (رنگ را عینا نشان می دهد؛ از تبدیل تم مستثنی است)"""
    _RAW_COLOR = True

    def __init__(self, parent, color, cmd=None, size=28):
        s = S(size)
        super().__init__(parent, width=s, height=s, bg=parent["bg"], highlightthickness=0,
                         cursor="hand2" if cmd else "")
        rrect(self, 2, 2, s - 2, s - 2, S(8), fill=color, outline="#8E8E93")
        if cmd:
            self.bind("<Button-1>", lambda e: cmd())


class PricesDialog(Dlg):
    """جزئیات قیمت دیجی کالا برای یک کالا"""

    def __init__(self, app, pid):
        super().__init__(app, "دیجی کالا", 620)
        self.db, self.pid = app.db, pid
        self.title_l = lbl(self.body, "", 14, True, wraplength=S(580))
        self.title_l.pack(anchor="e", pady=(0, S(10)))
        self.tab = tk.Frame(self.body, bg=CARD)
        self.tab.pack(fill="x")
        bl = tk.Frame(self.body, bg=CARD)
        bl.pack(anchor="w", pady=(S(12), 0))
        Btn(bl, "دریافت دوباره قیمت", self.refetch, "primary").pack(side="left")
        Btn(bl, "بستن", self.destroy).pack(side="left", padx=S(8))
        app.listeners.append(self.load)
        self.bind("<Destroy>", lambda e: self.app.listeners.remove(self.load)
                  if e.widget is self and self.load in self.app.listeners else None)
        self.load()
        self.finish(modal=False)

    def kv(self, label, value, fg=TEXT, bold=True, buttons=()):
        r = tk.Frame(self.tab, bg=CARD)
        r.pack(fill="x", pady=S(5))
        kic = next((ic for k, ic in (("قیمت", "tag"), ("نام", "box"), ("لینک", "external"), ("خطا", "info"),
                                     ("ارزش", "wallet"), ("اختلاف", "profit")) if k in label), "info")
        ico(r, kic, 16, MUTED, CARD).pack(side="right", anchor="n", padx=(S(6), 0), pady=S(2))
        lbl(r, label, 9, fg=MUTED, width=20, anchor="e").pack(side="right", anchor="n")
        for text, fn in buttons:
            Btn(r, text, fn, "tint", size=8, py=3).pack(side="left", padx=(S(4), 0))
        lbl(r, value, 10, bold, fg=fg, wraplength=S(290), anchor="e").pack(side="right", fill="x", expand=True,
                                                                           padx=S(8))
        tk.Frame(self.tab, bg=SEP, height=1).pack(fill="x")

    def copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def load(self):
        try:
            p = self.db.product(self.pid)
            for w in self.tab.winfo_children():
                w.destroy()
        except Exception:
            return
        self.title_l.config(text=p["name"])
        rows = {r["site"]: r for r in self.db.prices(self.pid)}
        r = rows.get("digikala")
        ok = bool(r and r["price"])
        hero = rbox(self.tab, FILL, 16, 10)
        hero.pack(fill="x", pady=(0, S(8)))
        h = hero.body
        lbl(h, "قیمت در دیجی کالا", 9, fg=MUTED, bg=FILL).pack(anchor="e")
        lbl(h, (money(r["price"]) + " تومان") if ok else "قیمت پیدا نشد", 20, True, fg=GREEN if ok else RED,
            bg=FILL).pack(anchor="e")
        stamp = (r["fetched_at"] or p["price_updated"] or "") if r else (p["price_updated"] or "")
        lbl(h, ("آخرین به روزرسانی: " + fa(stamp[:16].replace("T", " "))) if stamp else "هنوز قیمتی دریافت نشده", 9,
            fg=MUTED, bg=FILL).pack(anchor="e")
        if r and r["error"] and not ok:
            self.kv("پیام خطا", r["error"], RED, False)
        if ok:
            title = (r["title"] or "").split(" | ")[0]
            self.kv("نام کالا در دیجی کالا", title or "—", TEXT, False)
            url = r["url"] or ""
            if url:
                short_url = url if len(url) <= 60 else url[:57] + "..."
                self.kv("لینک کالا", ltr(short_url), BLUE, False,
                        [("باز کردن", partial(webbrowser.open, url)), ("کپی", partial(self.copy, url))])
        buy = int(p["buy_price"] or 0)
        self.kv("قیمت خرید من", (money(buy) + " تومان") if buy else "ثبت نشده", MUTED if not buy else TEXT)
        if ok and buy:
            diff = r["price"] - buy
            self.kv("اختلاف با قیمت خرید", ltr(("+" if diff >= 0 else "") + money(diff)) + " تومان  (" +
                    ltr(fa(f"{diff * 100.0 / buy:+.0f}") + "٪") + ")", GREEN if diff >= 0 else RED)
        if ok and not p["is_service"]:
            self.kv("ارزش کل موجودی", f"{money(p['qty'] * r['price'])} تومان  ({fa(p['qty'])} عدد)")
        mode = {"max": "بالاترین", "min": "کمترین", "avg": "میانگین"}[self.db.get_setting("price_mode", "max")]
        self.kv(f"قیمت اصلی جلوی کالا ({mode})", (money(p["best_price"]) + " تومان") if p["best_price"] else "—")
        hist = self.db.purchases(self.pid)
        if hist:
            lbl(self.tab, "تاریخچه خرید", 11, True).pack(anchor="e", pady=(S(14), S(4)))
            for hh in hist[:8]:
                lbl(self.tab, f"{J.fmt(dt.date.fromisoformat(hh['date']))}  •  {fa(hh['qty'])} عدد  •  "
                              f"{money(hh['unit_price'])} تومان  •  {hh['note'] or ''}", 9, fg=MUTED).pack(anchor="e")

    def refetch(self):
        p = self.db.product(self.pid)
        # (pid, name, need_img, fetch_details)
        self.app.start_fetch([(p["id"], p["name"], not p["image"], True)])


# ======================================================================= صفحه ها
class StatCard(Card):
    def __init__(self, parent, glyph, color, title):
        super().__init__(parent, r=14, pad=5)
        self.m = S(3)
        row = tk.Frame(self.body, bg=CARD)
        row.pack(fill="x")
        tile(row, glyph, color, 26, 8).pack(side="right", anchor="n", pady=S(1))
        col = tk.Frame(row, bg=CARD)
        col.pack(side="right", fill="x", expand=True, padx=(0, S(8)))
        lbl(col, title, 8, fg=MUTED).pack(fill="x")
        self.v = lbl(col, "—", 11, True)
        self.v.pack(fill="x")
        self.s = lbl(col, "", 7, fg=FAINT)
        self.s.pack(fill="x")

    def set(self, v, sub=""):
        self.v.config(text=v)
        self.s.config(text=sub)


def make_stats(parent, specs, cols=4):
    """شبکه کارت های آماری (واکنشگرا). specs: [(کلید, آیکون, رنگ, عنوان)]"""
    out = {}
    g = RGrid(parent, minw=150, maxcols=cols, bg=BG, padx=3, pady=2)
    g.pack(fill="x")
    for key, glyph, color, title in specs:
        card = StatCard(g, glyph, color, title)
        g.add(card)
        out[key] = card
    return out


class DashboardPage:
    """داشبورد: همه آمارها در کادر، نمودار فروش هفته، آخرین فروش ها و کم موجودی ها (بزرگ) و دکمه آمار کامل هفته"""

    def __init__(self, app, parent):
        self.app, self.db = app, app.db
        self.days = 7
        self.frame = ScrollFrame(parent, BG)
        root = tk.Frame(self.frame.inner, bg=BG)
        root.pack(fill="both", expand=True, padx=S(8), pady=(0, S(8)))
        sg = tk.Frame(root, bg=BG)
        sg.pack(fill="x")
        self.cards = make_stats(sg, [
            ("sale", "invoice", BLUE, "فروش امروز"), ("profit", "profit", GREEN, "سود امروز"),
            ("wsale", "chart", PURPLE, "فروش این هفته"), ("wprofit", "profit", TEAL, "سود این هفته"),
            ("msale", "cart", ORANGE, "فروش این ماه"), ("mprofit", "calendar", PURPLE, "سود این ماه"),
            ("assets", "box", BLUE, "کل دارایی انبار"), ("stock", "tag", RED, "موجودی انبار")])
        cc = Card(root, auto=False, pad=12)
        cc.configure(height=S(270))
        cc.pack(fill="x", pady=S(6), padx=S(4))
        hd = Wrap(cc.body, bg=CARD, gap=8, vgap=4)
        hd.pack(fill="x")
        self.chart_hd = hd
        self.chart_title = lbl(hd, "نمودار فروش هفته", 13, True)
        hd.add(self.chart_title)
        self.seg_days = Segmented(hd, ["۳۰ روز", "۱۴ روز", "۷ روز"], self.set_days, 2, size=9)
        hd.add(self.seg_days, side="l")
        self.chart = Chart(cc.body, 170)
        self.chart.pack(fill="both", expand=True, pady=(S(6), 0))
        lists = RGrid(root, minw=380, maxcols=2, bg=BG, padx=4, pady=4)
        lists.pack(fill="x")
        self.recent = Card(lists, pad=10)
        lists.add(self.recent)
        self.low = Card(lists, pad=10)
        lists.add(self.low)

    def set_days(self, i):
        self.days = (30, 14, 7)[i]
        self.refresh()

    def refresh(self):
        today = dt.date.today()
        ws = J.week_start(today)
        jy, jm, _ = J.to_jalali(today)
        ds = self.db.daily_sales(today, today).get(today.isoformat(), (0, 0))
        wk = self.db.daily_sales(ws, ws + dt.timedelta(days=6))
        mon = self.db.daily_sales(*J.month_range(jy, jm))
        t = self.db.totals()
        c = self.cards
        c["sale"].set(short(ds[0]) + " تومان", J.fmt_long(today))
        c["profit"].set(short(ds[1]) + " تومان", "فروش − قیمت خرید")
        c["wsale"].set(short(sum(v[0] for v in wk.values())) + " تومان", f"از {J.fmt(ws)}")
        c["wprofit"].set(short(sum(v[1] for v in wk.values())) + " تومان", "سود خالص هفته")
        c["msale"].set(short(sum(v[0] for v in mon.values())) + " تومان", f"{J.MONTHS[jm - 1]} {fa(jy)}")
        c["mprofit"].set(short(sum(v[1] for v in mon.values())) + " تومان", "سود خالص ماه")
        c["assets"].set(short(t["assets"]) + " تومان", "بر اساس قیمت خرید")
        c["stock"].set(f"{fa(t['q'])} عدد", f"در {fa(t['n'])} کالا")
        # نمودار
        d1 = today - dt.timedelta(days=self.days - 1)
        sales = self.db.daily_sales(d1, today)
        days = [d1 + dt.timedelta(days=i) for i in range(self.days)][::-1]
        labels = [fa(f"{J.to_jalali(d)[1]:02d}/{J.to_jalali(d)[2]:02d}") for d in days]
        self.chart_title.config(text="نمودار فروش هفته" if self.days == 7 else f"نمودار فروش {fa(self.days)} روز اخیر")
        self.chart_hd.after_idle(self.chart_hd.layout)
        self.chart.set_data(labels, [{"name": "فروش", "color": BLUE, "tint": "#E8F2FF",
                                      "values": [sales.get(d.isoformat(), (0, 0))[0] for d in days]}])
        for card, title in ((self.recent, "آخرین فروش ها"), (self.low, "موجودی کم / تمام شده")):
            for w in card.body.winfo_children():
                w.destroy()
            hdr = tk.Frame(card.body, bg=CARD)
            hdr.pack(fill="x", pady=(0, S(8)))
            lbl(hdr, title, 14, True).pack(side="right")
            if card is self.recent:
                Btn(hdr, "مشاهده همه", lambda: self.app.go(4), "tint", size=9, py=4).pack(side="left")
        rs = self.db.recent_sales(3)
        if not rs:
            lbl(self.recent.body, "هنوز فروشی ثبت نشده است.", 10, fg=FAINT).pack(anchor="e", pady=S(10))
        for s in rs:
            tk.Frame(self.recent.body, bg=SEP, height=1).pack(fill="x")
            r = tk.Frame(self.recent.body, bg=CARD)
            r.pack(fill="x", pady=S(6))
            lbl(r, money(s["total"]) + " تومان", 10, True, fg=GREEN).pack(side="left")
            col = tk.Frame(r, bg=CARD)
            col.pack(side="right", fill="x", expand=True, padx=(S(10), 0))
            lbl(col, s["product_name"][:34], 10, True).pack(anchor="e")
            lbl(col, f"{fa(s['qty'])} عدد × {money(s['unit_price'])} تومان  •  "
                     f"{J.fmt(dt.date.fromisoformat(s['date']))}", 8, fg=MUTED).pack(anchor="e")
        low = self.db.low_stock(2, 8)
        if not low:
            lbl(self.low.body, "همه کالاها موجودی کافی دارند.", 10, fg=FAINT).pack(anchor="e", pady=S(10))
        for p in low:
            tk.Frame(self.low.body, bg=SEP, height=1).pack(fill="x")
            r = tk.Frame(self.low.body, bg=CARD)
            r.pack(fill="x", pady=S(6))
            col = RED if p["qty"] == 0 else ORANGE
            lbl(r, "تمام شده" if p["qty"] == 0 else f"{fa(p['qty'])} عدد مانده", 10, True, fg=col).pack(side="left")
            lbl(r, p["name"][:34], 10, True).pack(side="right")


class WeeklyStatsPage:
    """آمار فروش هفته: فقط درباره فروش یک هفته؛ هر هفته ای را با تاریخ می شود انتخاب کرد"""

    def __init__(self, app, parent):
        self.app, self.db = app, app.db
        self.start = J.week_start(dt.date.today())
        self.frame = ScrollFrame(parent, BG)
        root = tk.Frame(self.frame.inner, bg=BG)
        root.pack(fill="both", expand=True, padx=S(8), pady=(0, S(8)))
        bar = Card(root, pad=12)
        bar.pack(fill="x", padx=S(4), pady=S(4))
        heading(bar.body, "انتخاب هفته", 13, "calendar", ORANGE).pack(anchor="e", pady=(0, S(8)))
        b = Wrap(bar.body, bg=CARD, gap=6, vgap=6)
        b.pack(fill="x")
        for t, fn in (("هفته بعد", lambda: self.shift(1)), ("این هفته", lambda: self.shift(0)),
                      ("هفته قبل", lambda: self.shift(-1))):
            b.add(Btn(b, t, fn, "tint", size=9, py=6))
        b.add(lbl(b, "یک تاریخ دلخواه:", 9, fg=MUTED), side="l")
        self.date_e = DateEntry(b, width=10, h=34)
        b.add(self.date_e, side="l")
        self.date_e.set(dt.date.today())
        b.add(Btn(b, "نمایش هفته این تاریخ", self.pick_date, "primary", size=9, py=6), side="l")
        self.range_l = lbl(bar.body, "", 11, True, fg=BLUE)
        self.range_l.pack(anchor="e", pady=(S(10), 0))
        sg = tk.Frame(root, bg=BG)
        sg.pack(fill="x")
        self.cards = make_stats(sg, [
            ("total", "invoice", BLUE, "کل فروش هفته"), ("qty", "cart", ORANGE, "تعداد کالای فروخته شده"),
            ("profit", "profit", GREEN, "سود تقریبی هفته"), ("margin", "chart", PURPLE, "درصد سود"),
            ("avg", "calendar", TEAL, "میانگین فروش روزانه"), ("best", "tag", BLUE, "بهترین روز هفته"),
            ("cmp", "profit", ORANGE, "تغییر نسبت به هفته قبل"), ("active", "check", GREEN, "روزهای دارای فروش")])
        dc = Card(root, pad=12)
        dc.pack(fill="x", padx=S(4), pady=S(4))
        heading(dc.body, "جزئیات روز به روز", 13, "list", BLUE).pack(anchor="e", pady=(0, S(8)))
        self.tree = SalesTree(dc.body)
        self.tree.pack(fill="x")
        self.lv = app.level(720, 520)
        self.tree.set_level(self.lv)
        lbl(dc.body, "روی هر روز کلیک کنید تا کالاهای فروخته شده همان روز باز شود.", 8, fg=FAINT).pack(
            anchor="e", pady=(S(6), 0))
        self.top = Card(root, pad=12)
        self.top.pack(fill="x", padx=S(4), pady=S(4))
        self.loaded = False

    def shift(self, d):
        if d == 0:
            self.start = J.week_start(dt.date.today())
        else:
            self.start += dt.timedelta(days=7 * d)
        self.date_e.set(self.start)
        self.load()

    def relayout(self):
        lv = self.app.level(720, 520)
        if lv != self.lv:
            self.lv = lv
            self.tree.set_level(lv)
            self.load()

    def pick_date(self):
        d = self.date_e.get_date()
        if not d:
            info(self.app, "تاریخ را درست وارد کنید (مثلا ۱۴۰۵/۰۷/۲۰).")
            return
        self.start = J.week_start(d)
        self.load()

    def refresh(self):
        self.load()

    def load(self):
        d1 = self.start
        d2 = d1 + dt.timedelta(days=6)
        rows = self.db.sales_between(d1, d2)
        (s, q, pr), best = self.tree.fill(rows, d1, d2, True, False)
        by = {}
        for r in rows:
            by[r["date"]] = by.get(r["date"], 0) + r["total"]
        prev = self.db.daily_sales(d1 - dt.timedelta(days=7), d1 - dt.timedelta(days=1))
        ps = sum(v[0] for v in prev.values())
        c = self.cards
        self.range_l.config(text=f"هفته {J.fmt(d1)}  تا  {J.fmt(d2)}")
        c["total"].set(money(s) + " تومان", "جمع مبلغ فروش این هفته")
        c["qty"].set(f"{fa(q)} عدد", f"در {fa(len(rows))} ردیف فروش")
        c["profit"].set(money(pr) + " تومان", "فروش − قیمت خرید")
        c["margin"].set(fa(f"{(pr * 100.0 / s) if s else 0:.1f}").replace(".", "٫") + "٪", "سود نسبت به فروش")
        c["avg"].set(money(s / 7) + " تومان", "میانگین هفت روز")
        c["best"].set(J.fmt(best[0]) if best else "—", (money(best[1]) + " تومان") if best else "فروشی ثبت نشده")
        if ps:
            ch = (s - ps) * 100.0 / ps
            c["cmp"].set(ltr(fa(f"{ch:+.0f}") + "٪"), f"هفته قبل: {short(ps)} تومان")
        else:
            c["cmp"].set("—", "هفته قبل فروشی نبوده")
        c["active"].set(f"{fa(len(by))} از ۷", "روز")
        for w in self.top.body.winfo_children():
            w.destroy()
        heading(self.top.body, "پرفروش ترین کالاهای این هفته", 13, "profit", GREEN).pack(anchor="e", pady=(0, S(8)))
        agg = {}
        for r in rows:
            a = agg.setdefault(r["product_name"], [0, 0, 0])
            a[0] += r["qty"]
            a[1] += r["total"]
            a[2] += (r["unit_price"] - r["cost"]) * r["qty"]
        if not agg:
            lbl(self.top.body, "در این هفته فروشی ثبت نشده است.", 10, fg=FAINT).pack(anchor="e", pady=S(8))
            return
        hb = rbox(self.top.body, FILL, 10)
        hb.pack(fill="x")
        hr = tk.Frame(hb.body, bg=FILL)
        hr.pack(fill="x", pady=S(6))
        lbl(hr, "کالا", 9, True, fg=MUTED, bg=FILL).pack(side="right", padx=S(8))
        lv = self.lv
        wd = (14, 12, 11)[lv]
        heads = ("سود", "مبلغ فروش", "تعداد")[:2 if lv == 2 else 3]
        for t in heads:
            x = lbl(hr, t, 9, True, fg=MUTED, bg=FILL, anchor="center")
            x.configure(width=wd)
            x.pack(side="left")
        for i, (name, (qq, tt, pp)) in enumerate(sorted(agg.items(), key=lambda kv: -kv[1][1])[:10], 1):
            r = tk.Frame(self.top.body, bg=CARD)
            r.pack(fill="x", pady=S(5))
            lbl(r, f"{fa(i)}.  {name[:40]}", 10, True, wraplength=(0, S(170), S(100))[lv]).pack(side="right", padx=S(8))
            for t, col in ((money(pp), GREEN if pp >= 0 else RED), (money(tt), TEXT), (fa(qq), TEXT))[:len(heads)]:
                x = lbl(r, t, 10, fg=col, anchor="center")
                x.configure(width=wd)
                x.pack(side="left")
            tk.Frame(self.top.body, bg=SEP, height=1).pack(fill="x")


class LatestSalesPage:
    """آخرین فروش ها: فهرست دقیق فروش ها با همه جزئیات"""
    HEAD = ["تاریخ و ساعت", "کالا", "خریدار", "تعداد", "قیمت فروش", "قیمت خرید", "مبلغ کل", "سود", "فاکتور"]
    W = [150, 0, 105, 55, 105, 105, 110, 75, 55]

    def __init__(self, app, parent):
        self.app, self.db = app, app.db
        self.limit = 50
        self.mode = "table" if (app.win_w() >= 1000 and S(app.avail()) >= S(1040)) else "card"
        self.frame = ScrollFrame(parent, BG)
        root = tk.Frame(self.frame.inner, bg=BG)
        root.pack(fill="both", expand=True, padx=S(8), pady=(0, S(8)))
        top = Card(root, pad=12)
        top.pack(fill="x", padx=S(4), pady=S(4))
        heading(top.body, "آخرین فروش ها", 14, "cart", BLUE).pack(anchor="e")
        lbl(top.body, "فهرست دقیق فروش ها، از جدیدترین به قدیمی ترین", 9, fg=MUTED).pack(anchor="e", pady=(S(2), S(10)))
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *a: self._debounce())
        REntry(top.body, 40, textvariable=self.q, placeholder="جستجوی نام کالا یا بارکد در فروش ها...", icon="search",
               h=42, size=11).pack(fill="x")
        self._job = None
        sg = tk.Frame(root, bg=BG)
        sg.pack(fill="x", pady=(S(2), 0))
        self.stats = make_stats(sg, [("n", "cart", BLUE, "تعداد فروش"), ("sum", "invoice", GREEN, "مجموع مبلغ"),
                                     ("prf", "profit", PURPLE, "سود تقریبی")], cols=3)
        self.card = Card(root, pad=10)
        self.card.pack(fill="x", padx=S(4), pady=S(4))
        self.more_host = tk.Frame(root, bg=BG)
        self.more_host.pack(fill="x")

    def table_ok(self):
        return self.app.win_w() >= 1000 and S(self.app.avail()) >= S(1040)

    def _debounce(self):
        if self._job:
            self.frame.after_cancel(self._job)
        self._job = self.frame.after(300, self._reset)

    def _reset(self):
        self.limit = 50
        self.refresh()

    def relayout(self):
        m = "table" if self.table_ok() else "card"
        if m != self.mode:
            self.mode = m
            self.refresh()

    def _grid(self, f):
        n = len(self.W)
        for i, w in enumerate(self.W):
            f.grid_columnconfigure(n - 1 - i, minsize=S(w), weight=1 if w == 0 else 0)

    def _cells(self, f, texts, bold=False, fgs=None, bg=CARD, size=10, py=8):
        n = len(self.W)
        for i, t in enumerate(texts):
            tk.Label(f, text=t, font=F(size, bold), fg=(fgs[i] if fgs else TEXT), bg=bg,
                     anchor="e" if i == 1 else "center").grid(row=0, column=n - 1 - i, sticky="nsew", padx=S(6), pady=S(py))

    def add_card(self, body, r):
        d = dt.date.fromisoformat(r["date"])
        profit = r["total"] if r["is_service"] else (r["unit_price"] - r["cost"]) * r["qty"]
        has_p = bool(r["is_service"] or r["cost"])
        tm = fa((r["created_at"] or "")[11:16]) if r["created_at"] else ""
        cost_text = "—" if r["is_service"] else (money(r["cost"]) if r["cost"] else "—")
        profit_text = ((("+" if profit >= 0 else "") + money(profit)) if has_p else "—")
        box = tk.Frame(body, bg=CARD)
        box.pack(fill="x", pady=(S(8), S(6)), padx=S(2))
        head = Wrap(box, bg=CARD, gap=8, vgap=2)
        head.pack(fill="x")
        wl = max(S(120), S(self.app.avail() - 210))
        head.add(lbl(head, r["product_name"], 10, True, wraplength=wl))
        head.add(lbl(head, money(r["total"]) + " تومان", 10, True, fg=BLUE), side="l")
        meta = f"{J.WEEKDAYS[d.weekday()]}  {J.fmt(d)}" + (f"  {tm}" if tm else "")
        if r["customer"]:
            meta += f"   •   خریدار: {r['customer']}"
        autowrap(lbl(box, meta, 8, fg=MUTED, wraplength=S(300)), pad=S(4)).pack(anchor="e", pady=(S(2), S(4)))
        g = RGrid(box, minw=105, maxcols=5, bg=CARD, padx=3, pady=2)
        g.pack(fill="x")

        def kv(title, val, fg=TEXT):
            f = tk.Frame(g, bg=FILL)
            lbl(f, title, 8, fg=MUTED, bg=FILL, anchor="center").pack(fill="x", padx=S(6), pady=(S(4), 0))
            lbl(f, val, 10, True, fg=fg, bg=FILL, anchor="center").pack(fill="x", padx=S(6), pady=(0, S(4)))
            g.add(f)
        kv("تعداد", fa(r["qty"]))
        kv("قیمت فروش", money(r["unit_price"]))
        kv("قیمت خرید", cost_text, MUTED)
        kv("سود", profit_text, (GREEN if profit >= 0 else RED) if has_p else FAINT)
        kv("فاکتور", fa(r["invoice_no"]) if r["invoice_no"] else "—", MUTED)
        tk.Frame(body, bg=SEP, height=1).pack(fill="x")

    def refresh(self):
        self.mode = "table" if self.table_ok() else "card"  # عرض فعلی پنجره
        body = self.card.body
        for w in body.winfo_children():
            w.destroy()
        for w in self.more_host.winfo_children():
            w.destroy()
        search = self.q.get().strip()
        rows = self.db.latest_sales(self.limit + 1, search)
        more = len(rows) > self.limit
        rows = rows[:self.limit]
        tot = sum(r["total"] for r in rows)
        prf = sum((r["total"] if r["is_service"] else (r["unit_price"] - r["cost"]) * r["qty"]) for r in rows)
        self.stats["n"].set(f"{fa(len(rows))} فروش", "نتیجه جستجو" if search else "نمایش داده شده")
        self.stats["sum"].set(short(tot) + " تومان", money(tot))
        self.stats["prf"].set(short(prf) + " تومان", "فروش − قیمت خرید")
        if not rows:
            lbl(body, "فروشی پیدا نشد." if search else "هنوز فروشی ثبت نشده است.", 11, fg=FAINT).pack(pady=S(40))
            return
        if self.mode == "card":
            for r in rows:
                self.add_card(body, r)
        else:
            hb = rbox(body, FILL, 12)
            hb.pack(fill="x")
            self._grid(hb.body)
            self._cells(hb.body, self.HEAD, True, [MUTED] * len(self.HEAD), FILL, 9, 9)
            for ri, r in enumerate(rows):
                d = dt.date.fromisoformat(r["date"])
                rbg = CARD if ri % 2 == 0 else BG
                row = tk.Frame(body, bg=rbg)
                row.pack(fill="x")
                self._grid(row)
                profit = r["total"] if r["is_service"] else (r["unit_price"] - r["cost"]) * r["qty"]
                tm = fa((r["created_at"] or "")[11:16]) if r["created_at"] else ""
                cost_text = "—" if r["is_service"] else (money(r["cost"]) if r["cost"] else "—")
                profit_text = ((("+" if profit >= 0 else "") + money(profit)) if (r["is_service"] or r["cost"]) else "—")
                texts = [f"{J.WEEKDAYS[d.weekday()]}  {J.fmt(d)}" + (f"\n{tm}" if tm else ""), r["product_name"],
                         (r["customer"] or "—"), fa(r["qty"]), money(r["unit_price"]), cost_text,
                         money(r["total"]), profit_text,
                         fa(r["invoice_no"]) if r["invoice_no"] else "—"]
                fgs = [MUTED, TEXT, TEXT, TEXT, TEXT, MUTED, BLUE,
                       (GREEN if profit >= 0 else RED) if (r["is_service"] or r["cost"]) else FAINT, MUTED]
                self._cells(row, texts, False, fgs, rbg, 10, 11)
                for w in row.winfo_children():
                    w.configure(wraplength=S(320) if w.grid_info().get("column") == len(self.W) - 2 else 0)
                    if w.grid_info().get("column") == len(self.W) - 1:
                        w.configure(justify="center")
                    elif w.grid_info().get("column") == len(self.W) - 2:
                        w.configure(justify="right", font=F(10, True))
                tk.Frame(body, bg=SEP, height=1).pack(fill="x")
        if more:
            Btn(self.more_host, "نمایش ۵۰ فروش قدیمی تر", self._more, "tint").pack(pady=S(12))

    def _more(self):
        self.limit += 50
        self.refresh()


class FilterDialog(Dlg):
    """انتخاب اینکه چه چیزهایی جلوی مشخصات کالا نشان داده شود"""
    OPTIONS = [("buy", "قیمت خرید"), ("sell", "قیمت فروش"), ("qty", "موجودی"), ("profit", "سود آخرین فروش"),
               ("last", "آخرین فروش / قیمت فروش من"), ("digi", "قیمت دیجی کالا"), ("assets", "دارایی (ارزش موجودی)"),
               ("cat", "دسته بندی زیر نام کالا"), ("img", "عکس کالا")]

    def __init__(self, app, page):
        super().__init__(app, "فیلتر نمایش", 380)
        self.page = page
        b = self.body
        heading(b, "فیلتر نمایش مشخصات کالا", 14, "filter", BLUE).pack(anchor="e")
        lbl(b, "هر مورد را که نمی خواهید جلوی کالاها دیده شود، خاموش کنید. (پیش فرض: همه نمایش داده می شوند)", 9,
            fg=MUTED, wraplength=S(340)).pack(anchor="e", pady=(S(4), S(10)))
        self.sw = {}
        for key, text in self.OPTIONS:
            sw = Switch(b, text, key not in page.hidden, partial(self.toggle, key), 10)
            sw.pack(anchor="e", pady=S(3))
            self.sw[key] = sw
        row = tk.Frame(b, bg=CARD)
        row.pack(fill="x", pady=(S(14), 0))
        Btn(row, "بستن", self.destroy, "primary", w=100).pack(side="left")
        Btn(row, "نمایش همه", self.show_all, "tint").pack(side="left", padx=S(8))
        self.finish(modal=False)

    def toggle(self, key, on):
        self.page.set_hidden(key, not on)

    def show_all(self):
        self.page.hidden.clear()
        self.page.save_hidden()
        for sw in self.sw.values():
            sw.set(True)
        self.page.refresh()


class ProductsPage:
    KEYS = ["ops", "assets", "digi", "last", "profit", "buy", "sell", "qty", "name", "img"]
    COLS = [(350, 0), (100, 0), (100, 0), (100, 0), (100, 0), (100, 0), (110, 0), (60, 0), (200, 1), (64, 0)]
    HEAD = ["عملیات", "دارایی", "قیمت دیجی کالا", "آخرین فروش", "سود آخرین فروش", "قیمت خرید", "قیمت فروش", "موجودی", "نام کالا", ""]

    def __init__(self, app, parent):
        self.app, self.db = app, app.db
        try:
            self.hidden = set(json.loads(self.db.get_setting("prod_hidden", "[]")))
        except Exception:
            self.hidden = set()
        self.frame = tk.Frame(parent, bg=BG)
        self.view = self.calc_view()
        top = Wrap(self.frame, bg=BG, gap=8, vgap=8)
        top.pack(fill="x", padx=S(8), pady=(0, S(10)))
        self.top = top
        self.q = tk.StringVar()
        self.limit = 50
        self.q.trace_add("write", lambda *a: self._debounce())
        top.add(REntry(top, 12, textvariable=self.q, placeholder="جستجوی نام کالا یا بارکد...", fillbg=CARD, icon="search", h=46,
                       size=12), expand=True, minw=170)
        self.filter_btn = Btn(top, "فیلتر", self.open_filter, "tint", h=46, icon="filter")
        top.add(self.filter_btn)
        # شمارنده مستقل با کادر قرمز و گوشههای گرد؛ فاصلهگذاری هماهنگ با کنترلهای ردیف
        self.badge = tk.Canvas(top, width=S(46), height=S(46), bg=BG, bd=0,
                               highlightthickness=0, relief="flat")
        rrect(self.badge, S(1), S(1), S(45), S(45), S(13),
              fill="#FFF1F0", outline=RED, width=max(1, S(1)), tags="badge_bg")
        self.badge.create_text(S(23), S(23), text=fa(len(self.hidden)),
                               font=F(11, True), fill=RED, tags="badge_count")
        top.add(self.badge)
        self._update_hidden_badge()
        self.cat = Dropdown(top, ["همه دسته ها"], "همه دسته ها", width=12, cmd=lambda v: self._reset_refresh(),
                            h=46, fill=CARD)
        top.add(self.cat)
        top.add(Btn(top, "دسته بندی ها", app.manage_categories, "ghost", h=46), side="l")
        top.add(Btn(top, "به روزرسانی قیمت همه", app.update_all, "tint", h=46), side="l")
        top.add(Btn(top, "افزودن کالا", app.add_product, "primary", h=46), side="l")
        self.card = Card(self.frame, auto=False, pad=8)
        self.card.pack(fill="both", expand=True, padx=S(4), pady=(0, S(4)))
        self.hb = rbox(self.card.body, FILL, 12)
        self.hb.pack(fill="x")
        self.sf = ScrollFrame(self.card.body, CARD)
        self.sf.pack(fill="both", expand=True)
        self._job = None
        self.cat_ids = {}
        self.build_head()

    # ---- فیلتر ستون ها
    def vis(self, k):
        return k not in self.hidden

    def save_hidden(self):
        self.db.set_setting("prod_hidden", json.dumps(sorted(self.hidden)))

    def _update_hidden_badge(self):
        """فقط وقتی حداقل یک بخش مخفی است، شمارنده را نشان بده."""
        self.badge.itemconfigure("badge_count", text=fa(len(self.hidden)))
        self.top.show(self.badge, bool(self.hidden))

    def set_hidden(self, key, hide):
        (self.hidden.add if hide else self.hidden.discard)(key)
        self.save_hidden()
        self._update_hidden_badge()
        self.refresh()

    def open_filter(self):
        FilterDialog(self.app, self)

    def build_head(self):
        for w in self.hb.body.winfo_children():
            w.destroy()
        head = self.hb.body
        self.grid_cols(head)
        for i, t in enumerate(self.HEAD):
            if self.vis(self.KEYS[i]):
                tk.Label(head, text=t, font=F(9, True), fg=MUTED, bg=FILL).grid(row=0, column=i, pady=S(9), padx=S(4))

    def grid_cols(self, f):
        for i, (w, wt) in enumerate(self.COLS):
            f.grid_columnconfigure(i, minsize=S(w) if self.vis(self.KEYS[i]) else 0, weight=wt)

    def _debounce(self):
        if self._job:
            self.frame.after_cancel(self._job)
        self._job = self.frame.after(300, self._reset_refresh)

    def _reset_refresh(self):
        self.limit = 50
        self.refresh()

    def more(self):
        self.limit += 50
        self.refresh()

    def refresh(self):
        self.view = self.calc_view()  # همیشه با عرض فعلی پنجره چیده شود (نه عرض قبلی)
        if self.view == "table":
            if not self.hb.winfo_manager():
                self.hb.pack(fill="x", before=self.sf)
            self.build_head()
        else:
            self.hb.pack_forget()
        # شمارنده فقط هنگام مخفی بودن حداقل یک بخش نمایش داده میشود.
        self._update_hidden_badge()
        # فهرست دستهها بهصورت درختی: مادرها و سپس زیردستههایشان
        self.cat_ids = {"همه دسته ها": None}
        categories = list(self.db.categories())
        roots = [c for c in categories if not c["parent_id"]]
        children = {}
        for c in categories:
            if c["parent_id"]:
                children.setdefault(c["parent_id"], []).append(c)
        for parent in roots:
            self.cat_ids[parent["name"]] = parent["id"]
            for child in children.get(parent["id"], []):
                # پیشوند و نام مادر کمک میکند رابطه تودرتو در منوی کشویی روشن باشد.
                label = f"  └ {parent['name']}  ›  {child['name']}"
                self.cat_ids[label] = child["id"]
        self.cat.set_values(list(self.cat_ids))
        if self.cat.get() not in self.cat_ids:
            self.cat.set("همه دسته ها")
        q = self.q.get().strip()
        rows = self.db.products(q, self.cat_ids.get(self.cat.get()))
        self.sf.clear()
        if not rows:
            lbl(self.sf.inner, "کالایی پیدا نشد.\nبا «افزودن کالا» اولین کالا را ثبت کنید.", 11, fg=FAINT,
                anchor="center").pack(pady=S(70))
            return
        visible = rows[:self.limit]
        # آخرین فروش همه کالاهای نمایش داده شده را یکجا می گیریم تا به جای ده ها پرس وجوی
        # جدا (یکی برای هر ردیف)، فقط یک پرس وجو اجرا شود؛ همین باعث می شود رفتن به این صفحه سریع تر شود.
        self.last_map = self.db.last_sales_bulk([p["id"] for p in visible])
        for p in visible:
            self.add_row(p)
        if len(rows) > self.limit:
            Btn(self.sf.inner, f"نمایش {fa(min(50, len(rows) - self.limit))} کالای بیشتر  (از {fa(len(rows))})",
                self.more, "tint").pack(pady=S(14))

    def calc_view(self):
        """جدول کامل اگر جا باشد؛ وگرنه هر کالا یک کارت (برای پنجره کوچک و موبایل)"""
        if self.app.win_w() < 1000:
            return "card"
        need = sum(S(w) for i, (w, _) in enumerate(self.COLS) if self.vis(self.KEYS[i])) + S(8) * len(self.COLS) + S(70)
        return "table" if S(self.app.avail()) >= need else "card"

    def relayout(self):
        v = self.calc_view()
        if v != self.view:
            self.view = v
            self.refresh()

    def add_card(self, p):
        app, pid, vis = self.app, p["id"], self.vis
        last = getattr(self, "last_map", {}).get(pid)
        box = tk.Frame(self.sf.inner, bg=CARD)
        box.pack(fill="x", padx=S(6))
        top = tk.Frame(box, bg=CARD)
        top.pack(fill="x", pady=(S(10), S(6)))
        if vis("img"):
            tk.Label(top, image=app.thumb(p["image"], S(56)), bg=CARD).pack(side="right", padx=(S(10), 0))
        if vis("qty"):
            if p["is_service"]:
                qtxt, qcol = "∞", BLUE
            else:
                qtxt = fa(p["qty"])
                qcol = RED if p["qty"] == 0 else (ORANGE if p["qty"] <= 2 else TEXT)
            qb = tk.Frame(top, bg=CARD)
            qb.pack(side="left", padx=(0, S(6)))
            lbl(qb, qtxt, 14, True, fg=qcol, anchor="center").pack(fill="x")
            lbl(qb, "موجودی", 8, fg=MUTED, anchor="center").pack(fill="x")
        col = tk.Frame(top, bg=CARD)
        col.pack(side="right", fill="x", expand=True)
        autowrap(lbl(col, p["name"], 10, True, wraplength=S(200)), pad=S(4)).pack(anchor="e")
        if vis("cat"):
            lbl(col, p["cat_name"] or "بدون دسته", 8, fg=MUTED).pack(anchor="e")
        if p["barcode"]:
            lbl(col, "بارکد: " + ltr(p["barcode"]), 8, fg=FAINT).pack(anchor="e")
        g = RGrid(box, minw=120, maxcols=6, bg=CARD, padx=3, pady=3)
        g.pack(fill="x")

        def kv(title, main, sub="", fg=TEXT):
            f = tk.Frame(g, bg=FILL)
            lbl(f, title, 8, fg=MUTED, bg=FILL, anchor="center").pack(fill="x", padx=S(6), pady=(S(5), 0))
            lbl(f, main, 10, True, fg=fg, bg=FILL, anchor="center").pack(fill="x", padx=S(6))
            lbl(f, sub or " ", 8, fg=MUTED, bg=FILL, anchor="center").pack(fill="x", padx=S(6), pady=(0, S(5)))
            g.add(f)
        if vis("buy"):
            if p["buy_cur"] != "IRT" and p["buy_amount"]:
                kv("قیمت خرید", f"{fa(('%g' % p['buy_amount']).replace('.', '٫'))} {CUR_SHORT.get(p['buy_cur'], '')}",
                   money(p["buy_price"]) + " تومان")
            else:
                kv("قیمت خرید", money(p["buy_price"]) if p["buy_price"] else "—", "", MUTED)
        if vis("sell") and p["sell_price"]:
            parts = []
            if p["sell_usd"]:
                cur = p["sell_cur"] or "USD"
                mv, mcol = price_move(app.rate(cur), app.rate_prev(cur))
                parts += [mv, usd_text(p["sell_usd"], cur)]
                main_col = mcol if mv else TEXT
            else:
                main_col = TEXT
            kv("قیمت فروش", money(p["sell_price"]) + " تومان", "  •  ".join(x for x in parts if x), main_col)
        if vis("profit"):
            basis = int(last["unit_price"]) if last else int(p["sell_price"] or 0)
            if basis and p["buy_price"]:
                diff = basis - int(p["buy_price"])
                kv("سود آخرین فروش", ("+" if diff >= 0 else "") + money(diff), "", GREEN if diff >= 0 else RED)
            else:
                kv("سود آخرین فروش", "—", "", FAINT)
        if vis("last"):
            if last:
                kv("آخرین فروش", money(last["unit_price"]), J.fmt(dt.date.fromisoformat(last["date"])))
            elif p["sell_price"]:
                kv("آخرین فروش", money(p["sell_price"]), "قیمت فروش من")
            else:
                kv("آخرین فروش", "هنوز فروش نداشته", "", FAINT)
        if vis("digi") and p["auto_price"]:
            if p["best_price"]:
                kv("قیمت دیجی کالا", money(p["best_price"]))
            else:
                kv("قیمت دیجی کالا", "نیافت", "", FAINT)
        if vis("assets"):
            if p["is_service"]:
                kv("دارایی", "خدمت", "", BLUE)
            else:
                kv("دارایی", money(p["qty"] * p["buy_price"]) if p["buy_price"] else "—", "",
                   BLUE if p["buy_price"] else FAINT)
        row = Wrap(box, bg=CARD, gap=4, vgap=4)
        row.pack(fill="x", pady=(S(6), S(10)))
        acts = [("فروش", "ok", partial(app.sell, pid), 76, "cart")]
        if p["sell_usd"]:
            acts += [("بروزرسانی", "tint", partial(app.update_sell_price, pid), 100, "refresh")]
        if p["auto_price"]:
            acts += [("دیجی کالا", "tint", partial(app.show_prices, pid), 100, "tag")]
        acts += [("", "plain", partial(app.edit_product, pid), 36, "edit")]
        for text, style, fn, w, ic in acts:
            row.add(Btn(row, text, fn, style, size=9, w=w, h=34, icon=ic))
        tk.Frame(self.sf.inner, bg=SEP, height=1).pack(fill="x", padx=S(10))

    def add_row(self, p):
        if self.view == "card":
            return self.add_card(p)
        app, pid, vis = self.app, p["id"], self.vis
        r = tk.Frame(self.sf.inner, bg=CARD)
        r.pack(fill="x")
        self.grid_cols(r)

        def cell(i):
            f = tk.Frame(r, bg=CARD)
            f.grid(row=0, column=i, sticky="nsew", padx=S(4), pady=S(9))
            return f
        if vis("img"):
            tk.Label(r, image=app.thumb(p["image"], S(56)), bg=CARD).grid(row=0, column=9, padx=S(8), pady=S(8))
        nm = cell(8)
        lbl(nm, p["name"], 10, True, wraplength=S(240)).pack(anchor="e")
        if vis("cat"):
            lbl(nm, p["cat_name"] or "بدون دسته", 8, fg=MUTED).pack(anchor="e")
        if p["barcode"]:
            lbl(nm, "بارکد: " + ltr(p["barcode"]), 8, fg=FAINT).pack(anchor="e")
        if vis("qty"):
            if p["is_service"]:
                qtxt, qcol = "∞", BLUE
            else:
                qtxt = fa(p["qty"])
                qcol = RED if p["qty"] == 0 else (ORANGE if p["qty"] <= 2 else TEXT)
            lbl(cell(7), qtxt, 12, True, fg=qcol, anchor="center").pack(expand=True)

        # قیمت خرید (با ارز یا تومان)
        if vis("buy"):
            b = cell(5)
            if p["buy_cur"] != "IRT" and p["buy_amount"]:
                lbl(b, f"{fa(('%g' % p['buy_amount']).replace('.', '٫'))} {CUR_SHORT.get(p['buy_cur'], '')}", 10, True,
                    anchor="center").pack(fill="x")
                lbl(b, money(p["buy_price"]) + " تومان", 8, fg=MUTED, anchor="center").pack(fill="x")
            else:
                lbl(b, money(p["buy_price"]) if p["buy_price"] else "—", 10, fg=MUTED, anchor="center").pack(
                    expand=True, fill="x")

        # قیمت فروش (جدا از قیمت خرید) + تفکیک دلار و سنت + تغییر نرخ
        if vis("sell"):
            s = cell(6)
            if p["sell_price"]:
                mv, mcol = price_move(app.rate(p["sell_cur"] or "USD"), app.rate_prev(p["sell_cur"] or "USD")) if p["sell_usd"] else ("", MUTED)
                lbl(s, money(p["sell_price"]) + " تومان", 10, True, anchor="center").pack(fill="x")
                if p["sell_usd"]:
                    lbl(s, usd_text(p["sell_usd"], p["sell_cur"] or "USD"), 8, fg=MUTED, anchor="center", wraplength=S(104)).pack(fill="x")
                    if mv:
                        lbl(s, mv + " نسبت به قبل", 8, True, fg=mcol, anchor="center").pack(fill="x")
            else:
                lbl(s, "—", 10, fg=FAINT, anchor="center").pack(expand=True, fill="x")

        # قیمت دیجی کالا
        if vis("digi") and p["auto_price"]:
            m = cell(2)
            if p["best_price"]:
                lbl(m, money(p["best_price"]), 11, True, anchor="center").pack(expand=True, fill="x")
            else:
                lbl(m, "قیمت نگرفته / نیافت", 9, fg=FAINT, anchor="center").pack(expand=True, fill="x")

        last = getattr(self, "last_map", {}).get(pid)
        # آخرین فروش
        if vis("last"):
            s = cell(3)
            if last:
                lbl(s, money(last["unit_price"]), 11, True, anchor="center").pack(fill="x")
                lbl(s, J.fmt(dt.date.fromisoformat(last["date"])), 8, fg=MUTED, anchor="center").pack(fill="x")
            elif p["sell_price"]:
                lbl(s, money(p["sell_price"]), 11, True, anchor="center").pack(fill="x")
                lbl(s, "قیمت فروش من", 8, fg=MUTED, anchor="center").pack(fill="x")
            else:
                lbl(s, "هنوز فروش نداشته", 9, fg=FAINT, anchor="center").pack(expand=True, fill="x")

        # سود هر عدد = قیمت فروش من (یا آخرین فروش) − قیمت خرید من
        if vis("profit"):
            pr = cell(4)
            basis = int(last["unit_price"]) if last else int(p["sell_price"] or 0)
            if basis and p["buy_price"]:
                diff = basis - int(p["buy_price"])
                col = GREEN if diff >= 0 else RED
                lbl(pr, (("+" if diff >= 0 else "") + money(diff)), 11, True, fg=col, anchor="center").pack(expand=True, fill="x")
            else:
                lbl(pr, "—", 10, fg=FAINT, anchor="center").pack(expand=True, fill="x")

        # دارایی (ارزش موجودی بر اساس قیمت دیجی کالا)
        if vis("assets"):
            if p["is_service"]:
                lbl(cell(1), "خدمت", 9, True, fg=BLUE, anchor="center").pack(expand=True, fill="x")
            else:
                lbl(cell(1), money(p["qty"] * p["buy_price"]) if p["buy_price"] else "—", 10, True,
                    fg=BLUE if p["buy_price"] else FAINT, anchor="center").pack(expand=True, fill="x")

        row = tk.Frame(cell(0), bg=CARD)
        row.pack(anchor="center", expand=True)
        acts = [("فروش", "ok", partial(app.sell, pid), 76, "cart")]
        if p["sell_usd"]:
            acts += [("بروزرسانی", "tint", partial(app.update_sell_price, pid), 100, "refresh")]
        if p["auto_price"]:
            acts += [("دیجی کالا", "tint", partial(app.show_prices, pid), 100, "tag")]
        acts += [("", "plain", partial(app.edit_product, pid), 34, "edit")]
        for text, style, fn, w, ic in acts:
            Btn(row, text, fn, style, size=9, w=w, h=32, icon=ic).pack(side="left", padx=S(2))
        tk.Frame(self.sf.inner, bg=SEP, height=1).pack(fill="x", padx=S(10))


class CategoriesDialog(Dlg):
    COLORS = [BLUE, GREEN, ORANGE, PURPLE, TEAL, RED]

    def __init__(self, app):
        super().__init__(app, "مدیریت دستهبندیها", 600)
        self.db = app.db
        self.parent_ids = {"بدون دسته مادر": None}

        # سربرگ ساده و راستچین
        head = tk.Frame(self.body, bg=CARD)
        head.pack(fill="x", pady=(0, S(12)))
        tile(head, "category", BLUE, 42, 14).pack(side="right", padx=(0, S(10)))
        title_col = tk.Frame(head, bg=CARD)
        title_col.pack(side="right", fill="x", expand=True)
        lbl(title_col, "مدیریت دستهبندیها", 16, True).pack(anchor="e")
        lbl(title_col, "دسته مادر و زیردستهها را از همینجا مرتب کنید.", 9, fg=MUTED).pack(anchor="e", pady=(S(3), 0))

        form = rbox(self.body, FILL, 16, 14)
        form.pack(fill="x", pady=(0, S(12)))
        lbl(form.body, "افزودن دستهبندی", 11, True, bg=FILL).pack(anchor="e", pady=(0, S(8)))

        lbl(form.body, "نام دستهبندی", 9, True, fg=MUTED, bg=FILL).pack(anchor="e", pady=(0, S(4)))
        self.name = REntry(form.body, 36, placeholder="مثلا: کابل و شارژر", h=40)
        self.name.pack(fill="x", pady=(0, S(10)))
        self.name.e.bind("<Return>", lambda e: self.add())

        lbl(form.body, "دسته مادر (اختیاری)", 9, True, fg=MUTED, bg=FILL).pack(anchor="e", pady=(0, S(4)))
        self.parent = Dropdown(form.body, ["بدون دسته مادر"], "بدون دسته مادر", width=34, h=40)
        self.parent.pack(anchor="e", fill="x", pady=(0, S(12)))

        actions = tk.Frame(form.body, bg=FILL)
        actions.pack(fill="x")
        Btn(actions, "افزودن دسته", self.add, "primary", icon="plus", h=40).pack(side="right")
        lbl(actions, "برای ساخت دسته اصلی، مادر را روی «بدون دسته مادر» بگذارید.", 8,
            fg=MUTED, bg=FILL).pack(side="right", padx=(0, S(10)), pady=S(8))

        list_head = tk.Frame(self.body, bg=CARD)
        list_head.pack(fill="x", pady=(0, S(6)))
        heading(list_head, "دستههای ثبتشده", 12, "folder", ORANGE).pack(side="right")
        self.count_lbl = lbl(list_head, "", 9, fg=MUTED)
        self.count_lbl.pack(side="left")

        self.sf = ScrollFrame(self.body, CARD)
        self.sf.pack(fill="both", expand=True)
        self.sf.canvas.configure(height=S(290))
        footer = tk.Frame(self.body, bg=CARD)
        footer.pack(fill="x", pady=(S(10), 0))
        Btn(footer, "بستن", self.destroy, "plain", h=38).pack(side="left")
        self.load()
        self.finish()
        self.name.focus_entry()

    def add(self):
        n = self.name.get().strip()
        if not n:
            info(self.app, "لطفا نام دستهبندی را وارد کنید.")
            self.name.focus_entry()
            return
        cats = self.db.categories()
        if any(c["name"].casefold() == n.casefold() for c in cats):
            info(self.app, "این نام قبلا استفاده شده است. نام دیگری انتخاب کنید.")
            self.name.focus_entry()
            return
        parent_id = self.parent_ids.get(self.parent.get())
        try:
            self.db.add_category(n, parent_id)
        except Exception:
            info(self.app, "ذخیره دستهبندی انجام نشد. لطفا دوباره تلاش کنید.")
            return
        self.name.set_text("")
        self.parent.set("بدون دسته مادر")
        self.load()
        self.app.reload_all()
        self.name.focus_entry()

    def load(self):
        self.sf.clear()
        cats = list(self.db.categories())
        roots = [c for c in cats if not c["parent_id"]]
        self.parent_ids = {"بدون دسته مادر": None}
        for c in roots:
            self.parent_ids[c["name"]] = c["id"]
        parent_values = ["بدون دسته مادر"] + [c["name"] for c in roots]
        self.parent.set_values(parent_values)
        if self.parent.get() not in parent_values:
            self.parent.set("بدون دسته مادر")
        self.count_lbl.configure(text=f"{fa(len(cats))} دسته")

        if not cats:
            empty = rbox(self.sf.inner, FILL, 16, 18)
            empty.pack(fill="x", pady=S(8))
            tile(empty.body, "folder", MUTED, 42, 14).pack(pady=(S(8), S(10)))
            lbl(empty.body, "هنوز دستهبندیای نساختهاید", 11, True, bg=FILL, anchor="center").pack(fill="x")
            lbl(empty.body, "از کادر بالا اولین دسته یا دسته مادر را اضافه کنید.", 9, fg=MUTED,
                bg=FILL, anchor="center").pack(fill="x", pady=(S(5), S(8)))
            return

        children = {}
        for c in cats:
            if c["parent_id"]:
                children.setdefault(c["parent_id"], []).append(c)
        ordered = []
        for root in roots:
            ordered.append((root, False))
            ordered.extend((child, True) for child in children.get(root["id"], []))
        for i, (c, is_child) in enumerate(ordered):
            rb = rbox(self.sf.inner, FILL if not is_child else CARD, 13, 8)
            rb.pack(fill="x", pady=S(3), padx=S(1))
            r = rb.body
            # اکشنها در سمت چپ و متن فارسی در سمت راست قرار میگیرند.
            Btn(r, "", partial(self.delete, c["id"]), "danger", size=9, w=34, h=32, icon="trash").pack(
                side="left", padx=(S(3), 0))
            Btn(r, "", partial(self.rename, c["id"], c["name"]), "plain", size=9, w=34, h=32, icon="edit").pack(
                side="left", padx=S(3))
            icon_color = self.COLORS[i % len(self.COLORS)]
            tile(r, "folder" if not is_child else "tag", icon_color if not is_child else MUTED, 34, 11).pack(
                side="right", padx=(S(6), S(2)), pady=S(3))
            col = tk.Frame(r, bg=r["bg"])
            col.pack(side="right", fill="x", expand=True, padx=S(5), pady=S(3))
            if is_child:
                lbl(col, f"↳  {c['name']}", 10, True, bg=r["bg"]).pack(anchor="e")
                lbl(col, f"زیردسته {c['parent_name']}  •  {fa(c['cnt'])} کالا", 8, fg=MUTED,
                    bg=r["bg"]).pack(anchor="e", pady=(S(2), 0))
            else:
                lbl(col, c["name"], 10, True, bg=r["bg"]).pack(anchor="e")
                lbl(col, f"دسته مادر  •  {fa(c['cnt'])} کالا", 8, fg=MUTED, bg=r["bg"]).pack(anchor="e", pady=(S(2), 0))

    def rename(self, cid, name):
        d = Dlg(self.app, "تغییر نام دستهبندی", 400)
        lbl(d.body, "نام جدید دستهبندی", 10, True).pack(anchor="e")
        e = REntry(d.body, 30, placeholder="نام دستهبندی", h=40)
        e.set_text(name)
        e.pack(fill="x", pady=S(10))

        def ok():
            new_name = e.get().strip()
            if not new_name:
                info(self.app, "نام دستهبندی نمیتواند خالی باشد.")
                return
            try:
                self.db.rename_category(cid, new_name)
            except Exception:
                info(self.app, "این نام قبلا استفاده شده است.")
                return
            d.destroy()
            self.load()
            self.app.reload_all()
        Btn(d.body, "ذخیره تغییرات", ok, "primary", w=130, h=40).pack(anchor="w")
        d.finish()
        e.focus_entry()

    def delete(self, cid):
        if ask(self.app, "این دسته حذف شود؟ کالاهای آن بدون دسته میشوند و زیردستهها به دسته اصلی تبدیل میشوند.", "حذف دسته"):
            self.db.delete_category(cid)
            self.load()
            self.app.reload_all()


def invoice_html(shop, number, date, customer, lines, discount, note=""):
    sub = sum(l["qty"] * l["price"] for l in lines)
    pay = max(sub - discount, 0)
    rows = "".join(
        f"<tr><td>{fa(i)}</td><td class=n>{l['name']}</td><td>{fa(l['qty'])}</td><td>{money(l['price'])}</td>"
        f"<td><b>{money(l['qty'] * l['price'])}</b></td></tr>" for i, l in enumerate(lines, 1))
    fonts = "".join(
        f"@font-face{{font-family:V;font-weight:{w};src:url(data:font/ttf;base64,{base64.b64encode((Path(__file__).resolve().parent / "assets" / "fonts" / f"Vazirmatn-{n}.ttf").read_bytes()).decode()})}}"
        for n, w in (("Regular", 400), ("Bold", 700)))
    contact = " • ".join(x for x in (shop.get("phone"), shop.get("address")) if x)
    logo = ""
    lp = shop.get("logo")
    if lp and os.path.exists(lp):
        with open(lp, "rb") as fh:
            logo = ('<img alt="" style="max-height:82px;max-width:190px;flex:0 0 auto" src="data:image/png;base64,'
                    + base64.b64encode(fh.read()).decode() + '">')
    disc = f"<tr><td>تخفیف</td><td>{money(discount)} تومان</td></tr>" if discount else ""
    import html as _h
    note_html = ""
    if (note or "").strip():
        note_html = ('<div class="note"><b>توضیحات</b>' + _h.escape(note.strip()).replace("\n", "<br>") + '</div>')
    return f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>فاکتور {fa(number)}</title>
<style>{fonts}
@page{{size:A4;margin:0}}
*{{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
html,body{{margin:0;background:#fff}}
body{{font-family:V,Tahoma;color:#1C1C1E;padding:15mm 14mm;font-size:15px}}
.head{{background:#fff;color:#000;border:2.5px solid #000;border-radius:16px;padding:24px 30px;display:flex;justify-content:space-between;align-items:center}}
.head h1{{margin:0;font-size:30px}}.head small{{opacity:.92;font-size:14px}}.meta{{text-align:left;font-size:15px;line-height:2}}
.cust{{background:#fff;border:1.5px solid #000;border-radius:12px;padding:14px 20px;margin:20px 0;font-size:16px}}
.note{{border:1.5px solid #000;border-radius:12px;padding:14px 20px;margin:34px 0 0 0;font-size:14px;line-height:1.9;text-align:right}}
.note b{{display:block;margin-bottom:4px}}
table{{width:100%;border-collapse:collapse;font-size:15px}}
th{{background:#E6E6E6;color:#000;border:1.5px solid #000;padding:13px;text-align:center;font-size:14px}}
td{{padding:13px;text-align:center;border-bottom:1.5px solid #888}}td.n{{text-align:right}}
.tot{{width:48%;margin:24px 0 0 auto;margin-right:0}}.tot td{{border:0;padding:10px 14px;text-align:right;background:none!important}}
.tot td:last-child{{text-align:left}}
.pay td{{background:#fff!important;color:#000;font-weight:bold;font-size:18px;border-top:2.5px solid #000;border-bottom:2.5px solid #000}}
.foot{{text-align:center;color:#444;margin-top:30px;font-size:13px}}</style></head><body>
<div class="head"><div style="display:flex;align-items:center;gap:18px">{logo}<div><h1>{shop.get('name') or 'فروشگاه'}</h1><small>{contact}</small></div></div>
<div class="meta"><b style="font-size:20px">فاکتور فروش</b><br>شماره: {fa(number)}<br>تاریخ: {J.fmt(date)}</div></div>
<div class="cust">خریدار: <b>{customer or '—'}</b></div>
<table><tr><th>ردیف</th><th>شرح کالا</th><th>تعداد</th><th>قیمت واحد (تومان)</th><th>مبلغ (تومان)</th></tr>{rows}</table>
<table class="tot"><tr><td>جمع اقلام</td><td>{money(sub)} تومان</td></tr>{disc}
<tr class="pay"><td>مبلغ قابل پرداخت</td><td>{money(pay)} تومان</td></tr></table>
{note_html}<div class="foot">از خرید شما سپاسگزاریم</div>
<script>window.onafterprint=function(){{setTimeout(function(){{window.close()}},400)}};
window.onload=function(){{setTimeout(function(){{window.print()}},600)}}</script></body></html>"""


def find_chromium():
    bases = [os.environ.get(k) for k in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA")]
    for b in bases:
        if not b:
            continue
        for rel in ("Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe"):
            p = Path(b) / rel
            if p.exists():
                return p
    return None


def open_print_window(path):
    """صفحه فاکتور را در یک پنجره مستقل (بدون نوار مرورگر) باز می کند و مستقیم پنجره چاپ می آید."""
    exe = find_chromium()
    if exe:
        try:
            subprocess.Popen([str(exe), f"--app={path.as_uri()}", "--window-size=980,1100",
                              "--disable-features=Translate", "--no-first-run"])
            return
        except Exception:
            pass
    webbrowser.open(path.as_uri())


class InvoicesDialog(Dlg):
    """لیست فاکتورهای ثبت شده: چاپ، ویرایش، حذف"""

    def __init__(self, app, page):
        super().__init__(app, "فاکتورهای ثبت شده", 760)
        self.app, self.page, self.db = app, page, app.db
        self.sf = ScrollFrame(self.body, CARD)
        self.sf.pack(fill="both", expand=True)
        Btn(self.body, "بستن", self.destroy).pack(anchor="w", pady=(S(12), 0))
        self.load()
        self.finish(modal=False)

    def load(self):
        for w in self.sf.inner.winfo_children():
            w.destroy()
        rows = self.db.get_invoices()
        if not rows:
            lbl(self.sf.inner, "هنوز فاکتوری ثبت نشده است.", 10, fg=FAINT).pack(pady=S(40))
            return
        for r in rows:
            self.add_row(r)

    def add_row(self, r):
        f = tk.Frame(self.sf.inner, bg=CARD)
        f.pack(fill="x", padx=S(6), pady=S(6))
        left = tk.Frame(f, bg=CARD)
        left.pack(side="right", fill="x", expand=True)
        lbl(left, f"فاکتور {fa(r['number'])}  •  {r['customer'] or 'بدون نام خریدار'}", 11, True).pack(anchor="e")
        lbl(left, f"{J.fmt(dt.date.fromisoformat(r['date']))}  •  مبلغ: {money(r['total'])} تومان", 9,
            fg=MUTED).pack(anchor="e")
        bf = tk.Frame(f, bg=CARD)
        bf.pack(side="left")
        Btn(bf, "چاپ", partial(self.print_row, r), "tint", size=9, w=60, h=32).pack(side="left", padx=S(3))
        Btn(bf, "ویرایش", partial(self.edit_row, r), "plain", size=9, w=70, h=32).pack(side="left", padx=S(3))
        Btn(bf, "حذف", partial(self.delete_row, r), "danger", size=9, w=60, h=32).pack(side="left", padx=S(3))
        tk.Frame(self.sf.inner, bg=SEP, height=1).pack(fill="x", padx=S(10))

    def print_row(self, r):
        lines = json.loads(r["items_json"] or "[]")
        g = self.db.get_setting
        shop = {"name": g("shop_name"), "phone": g("shop_phone"), "address": g("shop_address"),
                "logo": self.db.image_path(g("shop_logo"))}
        note = r["note"] if "note" in r.keys() else ""
        html = invoice_html(shop, r["number"], dt.date.fromisoformat(r["date"]), r["customer"] or "", lines,
                            r["discount"] or 0, note or "")
        path = Path(tempfile.gettempdir()) / f"Anbarman-invoice-{r['number']}.html"
        path.write_text(html, encoding="utf-8")
        open_print_window(path)

    def edit_row(self, r):
        self.destroy()
        self.page.load_invoice(r)

    def delete_row(self, r):
        if ask(self.app, f"فاکتور شماره {fa(r['number'])} حذف شود؟\nاگر کالاها از انبار کم شده بودند، موجودی برمی گردد.",
               yes="حذف"):
            self.db.delete_invoice(r["number"])
            self.app.reload_all()
            self.load()


class InvoicePage:
    def __init__(self, app, parent):
        self.app, self.db = app, app.db
        self.editing = None
        self.lines = []
        self.frame = tk.Frame(parent, bg=BG)
        self.tabs = tk.Frame(self.frame, bg=BG)
        self.seg = Segmented(self.tabs, ["فاکتور", "انتخاب کالا"], self.set_tab, 0, size=10)
        self.seg.pack(anchor="e", padx=S(6), pady=(0, S(6)))
        pw = tk.Frame(self.frame, bg=BG)
        pw.pack(fill="both", expand=True, padx=S(4), pady=(0, S(4)))
        self.area = pw
        pick = Card(pw, auto=False, pad=14)
        inv = Card(pw, auto=False, pad=16)
        self.pick, self.inv, self.tab, self.narrow = pick, inv, 0, None
        b = inv.body
        head = Wrap(b, bg=CARD, gap=6, vgap=6)
        head.pack(fill="x")
        self.head = head
        self.title = lbl(head, "", 14, True)
        head.add(self.title)
        head.add(lbl(head, "تاریخ:", 9, fg=MUTED), side="l")
        self.date = DateEntry(head, width=10, h=34)
        head.add(self.date, side="l")
        cr = Wrap(b, bg=CARD, gap=8, vgap=4)
        cr.pack(fill="x", pady=S(8))
        cr.add(lbl(cr, "خریدار:", 9, fg=MUTED))
        self.cust = REntry(cr, 10, h=34, placeholder="نام خریدار (اختیاری)")
        cr.add(self.cust, expand=True, minw=200)
        hhb = rbox(b, FILL, 12)
        hhb.pack(fill="x")
        self.hhb = hhb
        hh = hhb.body
        self.W = [(56, 0), (120, 0), (150, 0), (150, 0), (0, 1), (34, 0)]
        for w, c in ((w, c) for c, (w, _) in enumerate(self.W)):
            pass
        self.cols(hh)
        for i, t in enumerate(["", "جمع (تومان)", "قیمت واحد", "تعداد", "کالا", "#"]):
            tk.Label(hh, text=t, font=F(9, True), fg=MUTED, bg=FILL).grid(row=0, column=i, pady=S(8))
        self.sf = ScrollFrame(b, CARD)
        self.sf.pack(fill="both", expand=True)
        nbox = rbox(b, FILL, 12)
        nbox.pack(fill="x", pady=S(8))
        lbl(nbox.body, "توضیحات فاکتور", 10, True, fg=MUTED).pack(anchor="e", padx=S(14), pady=(S(10), 0))
        self.note_box = REntry(nbox.body, 40, h=44, fillbg=FILL, placeholder="مثلا: پرداخت نقدی، گارانتی ۶ ماهه ...")
        self.note_box.pack(fill="x", padx=S(12), pady=(S(4), S(12)))
        bot = Wrap(b, bg=CARD, gap=6, vgap=6)
        bot.pack(fill="x", pady=S(8))
        self.bot = bot
        self.total = lbl(bot, "", 14, True, fg=BLUE)
        bot.add(self.total)
        bot.add(lbl(bot, "تخفیف (تومان):", 9, fg=MUTED), side="l")
        self.disc = AmountEntry(bot, 0, width=12, cb=self.upd, h=34)
        bot.add(self.disc, side="l")
        self.deduct = Switch(b, "ثبت در فروش ها و کم کردن از موجودی انبار", False)
        self.deduct.pack(anchor="e")
        autowrap(lbl(b, "اگر تیک نزنید، فاکتور فقط برای چاپ است و موجودی انبار تغییری نمی کند.", 8, fg=MUTED,
                     wraplength=S(400)), pad=S(4)).pack(anchor="e")
        bl = Wrap(b, bg=CARD, gap=8, vgap=6)
        bl.pack(fill="x", pady=(S(10), 0))
        bl.add(Btn(bl, "چاپ / ذخیره PDF", self.print, "primary"))
        bl.add(Btn(bl, "ثبت فاکتور", self.register, "tint"))
        bl.add(Btn(bl, "فاکتور جدید", self.reset, "plain"))
        bl.add(Btn(bl, "فاکتورهای ثبت شده", self.history, "ghost"), side="l")
        pb = pick.body
        heading(pb, "کالاهای موجود", 12, "box", ORANGE).pack(anchor="e", pady=(0, S(6)))
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *a: self.fill_products())
        REntry(pb, 20, textvariable=self.q, placeholder="جستجو...", h=34, icon="search").pack(fill="x")
        self.psf = ScrollFrame(pb, CARD)
        self.psf.pack(fill="both", expand=True, pady=S(6))
        lbl(pb, "برای افزودن روی کالا کلیک کنید", 8, fg=MUTED, anchor="center").pack()
        self.relayout()

    # ---- واکنشگرایی: در پنجره باریک «فاکتور» و «انتخاب کالا» دو زبانه میشوند
    def set_tab(self, i):
        self.tab = i
        self.apply_tab()

    def apply_tab(self):
        self.pick.pack_forget()
        self.inv.pack_forget()
        if self.narrow:
            self.tabs.pack(fill="x", before=self.area)
            (self.inv if self.tab == 0 else self.pick).pack(fill="both", expand=True)
            if self.hhb.winfo_manager():
                self.hhb.pack_forget()
        else:
            self.tabs.pack_forget()
            self.pick.configure(width=S(330))
            self.pick.pack(side="right", fill="y", padx=(S(6), 0))
            self.inv.pack(side="left", fill="both", expand=True)
            if not self.hhb.winfo_manager():
                self.hhb.pack(fill="x", before=self.sf)

    def relayout(self):
        nar = S(self.app.avail()) < S(860)
        if nar == self.narrow:
            return
        self.narrow = nar
        self.apply_tab()
        self.render()

    def set_title(self, text):
        self.title.config(text=text)
        self.head.after_idle(self.head.layout)

    def cols(self, f):
        for c, (w, wt) in enumerate(self.W):
            f.grid_columnconfigure(c, minsize=S(w), weight=wt)

    def fill_products(self):
        code = clean_barcode(self.q.get())
        if code:
            pid = self.db.product_by_barcode(code)
            if pid:
                self.q.set("")
                self.add_line(pid)
                return
        self.psf.clear()
        shown = 0
        for p in self.db.products(self.q.get().strip()):
            shown += 1
            if shown > 60:
                lbl(self.psf.inner, "برای دیدن بقیه، نام کالا را جستجو کنید", 9, fg=MUTED, anchor="center").pack(pady=S(8))
                break
            PickRow(self.psf.inner, p["name"][:34], partial(self.add_line, p["id"]),
                    sub=("خدمات  •  " if p["is_service"] else f"موجودی: {fa(p['qty'])}  •  ")
                    + f"{money(p['sell_price'] or p['buy_price'])} تومان").pack(fill="x", pady=1)

    def add_line(self, pid, e=None):
        for l in self.lines:
            if l["pid"] == pid:
                l["qty"] = min(l["qty"] + 1, 999999)
                self.render()
                return
        p = self.db.product(pid)
        self.lines.append(dict(pid=pid, name=p["name"], qty=1, max=999999,
                               price=p["sell_price"] or p["buy_price"]))
        self.render()

    def render(self):
        self.sf.clear()
        nar = bool(self.narrow)
        for i, l in enumerate(self.lines):
            r = tk.Frame(self.sf.inner, bg=CARD)
            r.pack(fill="x")
            tot = tk.Label(r, text=money(l["qty"] * l["price"]), font=F(10, True), bg=CARD, fg=TEXT)
            if nar:
                for c in range(4):
                    r.grid_columnconfigure(c, minsize=0, weight=0)
                r.grid_columnconfigure(1, weight=1)
                wl = max(S(160), S(self.app.avail() - 120))
                lbl(r, f"{fa(i + 1)}.  {l['name']}", 10, True, wraplength=wl).grid(
                    row=0, column=0, columnspan=4, sticky="e", padx=S(4), pady=(S(8), S(2)))
                tot.grid(row=1, column=1, padx=S(4), pady=(0, S(8)))
                Btn(r, "", partial(self.remove, l), "danger", size=9, w=36, h=30, icon="trash").grid(
                    row=1, column=0, padx=S(4), pady=(0, S(8)))
                price = AmountEntry(r, l["price"], width=8, h=34)
                price.grid(row=1, column=2, padx=S(4), pady=(0, S(8)))
                st = Stepper(r, l["qty"], 1, l["max"])
                st.grid(row=1, column=3, padx=S(4), pady=(0, S(8)))
            else:
                self.cols(r)
                tot.grid(row=0, column=1, padx=S(4), pady=S(8))
                Btn(r, "", partial(self.remove, l), "danger", size=9, w=36, h=30, icon="trash").grid(row=0, column=0, padx=S(4))
                price = AmountEntry(r, l["price"], width=11, h=34)
                price.grid(row=0, column=2, padx=S(4))
                st = Stepper(r, l["qty"], 1, l["max"])
                st.grid(row=0, column=3, padx=S(4))
                lbl(r, l["name"], 10, wraplength=S(250)).grid(row=0, column=4, sticky="e", padx=S(4))
                lbl(r, fa(i + 1), 9, fg=FAINT).grid(row=0, column=5)

            def ch(l=l, st=st, price=price, tot=tot):
                l["qty"], l["price"] = st.get(), price.get_int()
                tot.config(text=money(l["qty"] * l["price"]))
                self.upd()
            st.cb = ch
            price.cb = ch
            tk.Frame(self.sf.inner, bg=SEP, height=1).pack(fill="x")
        self.upd()

    def remove(self, l):
        self.lines.remove(l)
        self.render()

    def upd(self):
        sub = sum(l["qty"] * l["price"] for l in self.lines)
        self.total.config(text=f"مبلغ قابل پرداخت: {money(max(sub - self.disc.get_int(), 0))} تومان")
        self.bot.after_idle(self.bot.layout)

    def shop(self):
        g = self.db.get_setting
        return {"name": g("shop_name"), "phone": g("shop_phone"), "address": g("shop_address"),
                "logo": self.db.image_path(g("shop_logo"))}

    def ok(self):
        if not self.lines:
            info(self.app, "هنوز کالایی به فاکتور اضافه نشده است.")
            return False
        return True

    def print(self):
        if not self.ok():
            return
        d = self.date.get_date() or dt.date.today()
        html = invoice_html(self.shop(), self.number, d, self.cust.get().strip(), self.lines, self.disc.get_int(),
                            self.get_note())
        path = Path(tempfile.gettempdir()) / f"Anbarman-invoice-{self.number}.html"
        path.write_text(html, encoding="utf-8")
        open_print_window(path)

    def register(self):
        if not self.ok():
            return
        old_qty = self.db.old_invoice_qty(self.editing) if self.editing else {}
        d = self.date.get_date() or dt.date.today()
        sub = sum(l["qty"] * l["price"] for l in self.lines)
        total = max(sub - self.disc.get_int(), 0)
        if self.editing:
            self.db.delete_invoice(self.editing)
            self.editing = None
        if self.deduct.get():
            ratio = total / (sub or 1)
            for l in self.lines:
                self.db.add_sale(l["pid"], l["qty"], int(round(l["price"] * ratio)), d, self.number, self.cust.get().strip(), allow_overstock=True)
        self.db.save_invoice(self.number, self.cust.get().strip(), d, total, self.disc.get_int(),
                             [{"pid": l["pid"], "name": l["name"], "qty": l["qty"], "price": l["price"]} for l in self.lines],
                             self.get_note())
        info(self.app, f"فاکتور شماره {fa(self.number)} ثبت شد." + ("\nموجودی انبار کم شد." if self.deduct.get() else ""))
        self.reset()
        self.app.reload_all()

    def history(self):
        InvoicesDialog(self.app, self)

    def load_invoice(self, row):
        self.reset()
        old = self.db.old_invoice_qty(row["number"])
        items = json.loads(row["items_json"] or "[]")
        lines, missing = [], []
        for it in items:
            p = self.db.con.execute("SELECT * FROM products WHERE name=?", (it["name"],)).fetchone()
            if not p:
                missing.append(it["name"])
                continue
            mx = 999999 if p["is_service"] else p["qty"] + old.get(p["id"], 0)
            lines.append(dict(pid=p["id"], name=p["name"], qty=it["qty"], max=mx, price=it["price"]))
        self.lines = lines
        self.number = row["number"]
        self.editing = row["number"]
        self.set_title(f"ویرایش فاکتور شماره {fa(row['number'])}")
        self.cust.set_text(row["customer"] or "")
        self.set_note(row["note"] if "note" in row.keys() else "")
        self.disc.set(row["discount"] or 0)
        self.date.set(dt.date.fromisoformat(row["date"]))
        self.render()
        self.fill_products()
        if missing:
            info(self.app, "این کالاها دیگر در انبار نیستند و در ویرایش حذف شدند:\n" + "، ".join(missing))
        self.app.go(2)

    def get_note(self):
        return self.note_box.get().strip()

    def set_note(self, text):
        self.note_box.set_text(text or "")

    def reset(self):
        self.editing = None
        self.lines = []
        self.disc.set(0)
        self.cust.set_text("")
        self.set_note("")
        self.render()
        self.refresh()

    def refresh(self):
        self.number = self.db.next_invoice_number()
        self.set_title(f"فاکتور شماره {fa(self.number)}")
        self.fill_products()


class SettingsPage:
    def __init__(self, app, parent):
        self.app, self.db = app, app.db
        self.frame = ScrollFrame(parent, BG)
        wrap = tk.Frame(self.frame.inner, bg=BG)
        wrap.pack(fill="both", expand=True, padx=S(8))
        c1 = Card(wrap, pad=18)
        c1.pack(fill="x", padx=S(4), pady=S(4))
        heading(c1.body, "اطلاعات فروشگاه (روی فاکتور چاپ می شود)", 13, "store", BLUE).pack(anchor="e", pady=(0, S(8)))
        g = tk.Frame(c1.body, bg=CARD)
        g.pack(fill="x")
        g.grid_columnconfigure(0, weight=1)
        self.e = {}
        for i, (k, t) in enumerate((("shop_name", "نام فروشگاه"), ("shop_phone", "تلفن"), ("shop_address", "آدرس"))):
            ic = {"shop_name": "store", "shop_phone": "bell", "shop_address": "home"}[k]
            lf = tk.Frame(g, bg=CARD)
            ico(lf, ic, 16, MUTED, CARD).pack(side="right", padx=(S(6), 0))
            lbl(lf, t, 9, fg=MUTED).pack(side="right")
            lf.grid(row=i, column=1, sticky="e", padx=(S(12), 0), pady=S(6))
            e = REntry(g, 10)
            e.set_text(self.db.get_setting(k))
            e.grid(row=i, column=0, sticky="ew", pady=S(6))
            self.e[k] = e
        lbl(c1.body, "لوگوی فروشگاه (روی فاکتور چاپ می شود)", 9, fg=MUTED).pack(anchor="e", pady=(S(12), S(4)))
        lr = tk.Frame(c1.body, bg=CARD)
        lr.pack(fill="x")
        self.logo_lbl = tk.Label(lr, bg=CARD)
        self.logo_lbl.pack(side="right", padx=(S(12), 0))
        bf = tk.Frame(lr, bg=CARD)
        bf.pack(side="right", fill="y")
        Btn(bf, "انتخاب لوگو", self.pick_logo, "tint", size=9, h=36, w=130).pack(anchor="e", pady=(0, S(8)))
        Btn(bf, "حذف لوگو", self.clear_logo, "plain", size=9, h=36, w=130).pack(anchor="e")
        self.refresh_logo()
        Btn(c1.body, "ذخیره تنظیمات", self.save, "primary").pack(anchor="w", pady=(S(10), 0))
        c3 = Card(wrap, pad=18)
        c3.pack(fill="x", padx=S(4), pady=S(8))
        heading(c3.body, "اندازه متن و ظاهر", 13, "zoom_in", ORANGE).pack(anchor="e")
        lbl(c3.body, "اندازهٔ نوشته ها را اینجا تغییر دهید.", 9, fg=MUTED).pack(anchor="e", pady=S(6))
        lbl(c3.body, "سایدبار را با موس بکشید تا بزرگ یا کوچک شود.", 9, fg=MUTED).pack(anchor="e")
        zr = Wrap(c3.body, bg=CARD, gap=8, vgap=6)
        zr.pack(fill="x")
        zr.add(Btn(zr, "بزرگ تر  A+", lambda: app.zoom(10), "tint"))
        zr.add(Btn(zr, "کوچک تر  A−", lambda: app.zoom(-10), "tint"))
        zr.add(Btn(zr, "اندازه پیش فرض", lambda: app.zoom(0, reset=True), "plain"))
        self.build_colors(wrap)
        c2 = Card(wrap, pad=18)
        c2.pack(fill="x", padx=S(4), pady=S(4))
        lbl(c2.body, "پشتیبان گیری و انتقال اطلاعات", 13, True).pack(anchor="e")
        lbl(c2.body, "خروجی: همه اطلاعات در یک فایل ZIP", 9, fg=MUTED).pack(anchor="e", pady=(S(4), 0))
        lbl(c2.body, "ورودی: برگرداندن اطلاعات از فایل ZIP", 9, fg=MUTED).pack(anchor="e", pady=(S(2), S(8)))
        r = Wrap(c2.body, bg=CARD, gap=8, vgap=6)
        r.pack(fill="x")
        r.add(Btn(r, "خروجی گرفتن (Export)", self.export, "primary"))
        r.add(Btn(r, "ورودی (Import)", self.import_, "plain"))
        r.add(Btn(r, "باز کردن پوشه داده ها", lambda: webbrowser.open(self.db.root.as_uri()), "plain"))
        r.add(Btn(r, "ریست کل برنامه", self.reset_app, "danger"))
        lbl(c2.body, f"محل داده ها: {self.db.root}", 8, fg=FAINT).pack(anchor="e", pady=(S(8), 0))
        self._autowrap_all(wrap)

    def _autowrap_all(self, w):
        """متن های بلند با عرض کادر هماهنگ شوند (پنجره کوچک/موبایل)"""
        for ch in w.winfo_children():
            if isinstance(ch, tk.Label) and str(ch.cget("wraplength")) not in ("0", ""):
                autowrap(ch, pad=S(4))
            self._autowrap_all(ch)

    def build_colors(self, wrap):
        c = Card(wrap, pad=18)
        c.pack(fill="x", padx=S(4), pady=S(8))
        heading(c.body, "رنگ بندی برنامه (سفارشی سازی)", 13, "palette", PURPLE).pack(anchor="e")
        lbl(c.body, "رنگ ها برای تم روشن و تاریک جدا ذخیره می شوند.", 9, fg=MUTED).pack(anchor="e", pady=S(6))
        dark = THEME_DARK
        presets = {
            "bg": ["#000001", "#0E0E11", "#10151C", "#15110E", "#0F1A14"] if dark else
                  ["#F2F2F7", "#FFFFFF", "#EEF3FB", "#F7F1E8", "#EAF4EE", "#F3EAF7"],
            "card": ["#1C1C1F", "#22262E", "#1E1A16", "#18201B"] if dark else
                    ["#FEFEFE", "#F8FAFF", "#FFF9F0", "#F4FBF6", "#FBF5FF"],
            "accent": ["#0A84FF", "#30D158", "#FF9F0A", "#BF5AF2", "#FF375F", "#00B8A9", "#5E5CE6"],
            "fill": ["#2A2A2F", "#323844", "#3A322A", "#2A3A30"] if dark else
                    ["#E9E9EF", "#DDE6F5", "#EFE6D6", "#DCEFE3"],
            "text": ["#F5F5F8", "#E6EDF7", "#FFE9C7"] if dark else ["#000000", "#1D2A44", "#2B2B2B"]}
        for role, title, key in COLOR_ROLES:
            r = Wrap(c.body, bg=CARD, gap=6, vgap=6)
            r.pack(fill="x", pady=S(6))
            r.add(lbl(r, title, 10, width=24, anchor="e"))
            r.add(Swatch(r, C(key), None, 34))
            for col in presets[role]:
                r.add(Swatch(r, col, partial(self.set_color, role, col), 26))
            r.add(Btn(r, "رنگ دلخواه...", partial(self.custom_color, role, key), "tint", size=9, py=5))
        Btn(c.body, "بازنشانی همه رنگ ها", lambda: self.app.save_colors({}), "plain").pack(anchor="w", pady=(S(8), 0))

    def reset_app(self):
        msg = ("همه کالاها، فروش ها، فاکتورها و تنظیمات پاک می شود.\n"
               "این کار قابل بازگشت نیست.\n\n"
               "اگر لازم است، اول «خروجی گرفتن» را بزنید.\n\n"
               "آیا مطمئن هستید؟")
        if not ask(self.app, msg, "بله، ریست کن"):
            return
        global THEME_DARK, ZM
        self.db.reset_all()
        THEME_DARK = False
        ZM = 0.95
        self.app.imgcache.clear()
        self.app.sidebar_w = 270.0
        self.app.load_colors()
        self.app.root.configure(bg=BG)
        titlebar_dark(self.app.root)
        self.app.rebuild()
        info(self.app, "برنامه با موفقیت ریست شد.")

    def pick_logo(self):
        f = filedialog.askopenfilename(parent=self.app.root,
                                       filetypes=[("تصاویر", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if not f:
            return
        name = None
        try:
            name = self.db.store_logo(f) or self.db.store_image(f)
        except Exception:
            name = None
        if not name:
            info(self.app, "این فایل عکس قابل استفاده نیست.")
            return
        self.db.set_setting("shop_logo", name)
        self.refresh_logo()

    def clear_logo(self):
        self.db.set_setting("shop_logo", "")
        self.refresh_logo()

    def refresh_logo(self):
        name = self.db.get_setting("shop_logo")
        if name and os.path.exists(self.db.image_path(name)):
            self.logo_lbl.config(image=self.app.thumb(name, S(64)), text="")
        else:
            self.logo_lbl.config(image="", text="بدون لوگو", font=F(9), fg=MUTED, bg=CARD)

    def set_color(self, role, hexv):
        d = self.app.colors()
        d[role] = hexv
        self.app.save_colors(d)

    def custom_color(self, role, key):
        from tkinter import colorchooser
        res = colorchooser.askcolor(color=C(key), parent=self.app.root, title="انتخاب رنگ")
        if res and res[1]:
            self.set_color(role, res[1].upper())

    def refresh(self):
        pass

    def save(self):
        for k, e in self.e.items():
            self.db.set_setting(k, e.get().strip())
        self.db.recompute_all_best()
        self.app.reload_all()
        info(self.app, "تنظیمات ذخیره شد.")

    def export(self):
        name = f"anbarman-backup-{to_en(J.fmt(dt.date.today())).replace('/', '-')}.zip"
        f = filedialog.asksaveasfilename(defaultextension=".zip", initialfile=name, filetypes=[("ZIP", "*.zip")])
        if f:
            self.db.export_zip(f)
            info(self.app, "فایل پشتیبان با موفقیت ذخیره شد.")

    def import_(self):
        f = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")])
        if not f or not ask(self.app, "اطلاعات فعلی با محتوای فایل پشتیبان جایگزین می شود. ادامه می دهید؟",
                            "جایگزین کن"):
            return
        try:
            self.db.import_zip(f)
        except Exception as e:  # noqa
            info(self.app, f"خطا در بازیابی: {e}")
            self.db.connect()
            return
        self.app.imgcache.clear()
        self.app.reload_all()
        info(self.app, "اطلاعات با موفقیت بازیابی شد.")


# ======================================================================= پنجره اصلی
def fetch_cover(url, db):
    tmp = Path(tempfile.gettempdir()) / ("anbarman_cover_" + uuid.uuid4().hex)
    try:
        P.download_file(url, str(tmp))
        name = uuid.uuid4().hex + ".png"
        if make_thumb(str(tmp), str(db.img_dir / name)):
            return name
    except Exception:
        pass
    finally:
        try:
            tmp.unlink()
        except Exception:
            pass
    return None


class NavItem(tk.Canvas):
    def __init__(self, parent, text, glyph, color, cmd, compact=False):
        super().__init__(parent, height=S(48), bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.text, self.glyph, self.color, self.cmd, self.on, self.hover = text, glyph, color, cmd, False, False
        self.compact = compact
        self.bind("<Configure>", lambda e: later(self, "_dj", self.draw, 14))
        self.bind("<Button-1>", lambda e: self.cmd())
        self.bind("<Enter>", lambda e: self.set_hover(True))
        self.bind("<Leave>", lambda e: self.set_hover(False))

    def set_hover(self, v):
        self.hover = v
        self.draw()

    def set_on(self, v):
        self.on = v
        self.draw()

    def draw(self):
        self.delete("all")
        W, H = self.winfo_width(), S(48)
        if W < 30:
            return
        if self.on or self.hover:
            rrect(self, 2, 2, W - 2, H - 2, S(14), fill=BLUE_BG if self.on else FILL, outline="")
        ts = S(32)
        x = (W - ts) / 2 if self.compact else W - S(10) - ts
        rrect(self, x, (H - ts) / 2, x + ts, (H + ts) / 2, S(9), fill=self.color, outline="")
        draw_icon(self, ICON_OF.get(self.glyph, self.glyph), x + S(8), (H - ts) / 2 + S(8), ts - S(16), "#FFFFFF")
        if self.compact:
            return
        self.create_text(x - S(10), H / 2, text=self.text, font=F(10, self.on), fill=BLUE if self.on else TEXT,
                         anchor="e", width=max(S(40), x - S(18)))


class App:
    NAV = [("داشبورد", "dashboard", BLUE), ("کالاها و انبار", "box", ORANGE),
           ("ساخت فاکتور", "invoice", GREEN), ("آمار فروش هفته", "chart", PURPLE),
           ("آخرین فروش ها", "cart", TEAL), ("تنظیمات و پشتیبان", "settings", "#8E8E93")]
    # ترتیب نمایش در سایدبار: داشبورد، کالاها، آخرین فروش، آمار هفته، ساخت فاکتور، تنظیمات
    NAV_ORDER = [0, 1, 4, 3, 2, 5]
    TITLES = ["داشبورد", "کالاها و انبار", "ساخت فاکتور", "آمار فروش هفته", "آخرین فروش ها",
              "تنظیمات و پشتیبان گیری"]

    def __init__(self):
        global FAM, SC, ZM, THEME_DARK
        register_fonts()
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("anbarman.shop.app.v2")  # تا آیکون پایتون در نوار وظیفه نیاید
        except Exception:
            pass
        self.root = tk.Tk()
        self.root.bind_all("<MouseWheel>", _global_wheel, add="+")
        self.root.title("انبارمن")
        self.root.configure(bg=BG)
        FAM = "Vazirmatn" if "Vazirmatn" in tkfont.families() else "Tahoma"
        try:
            SC = max(1.0, self.root.winfo_fpixels("1i") / 96.0)
        except Exception:
            SC = 1.0
        self.db = DB()
        THEME_DARK = self.db.get_setting("theme", "light") == "dark"
        self.load_colors()
        self.root.configure(bg=BG)
        titlebar_dark(self.root)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        lw, lh = sw / SC, sh / SC
        fit = max(0.8, min(1.15, min(lw / 1920.0, lh / 1080.0) ** 0.5))
        if self.db.get_setting("zoom", "") == "":
            self.db.set_setting("zoom", str(int(round(95 * fit))))
        try:
            ZM = max(0.7, min(1.8, int(self.db.get_setting("zoom", "95")) / 100.0))
        except ValueError:
            ZM = 0.95 * fit
        self.sidebar_w = max(260.0, min(420.0, float(self.db.get_setting("sidebar_w", "270") or 270)))
        w = min(S(1360), int(sw * 0.94))
        h = min(S(840), int(sh * 0.88))
        x, y = max(0, (sw - w) // 2), max(0, (sh - h) // 2 - 20)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self._init_w, self._init_h = w, h
        try:
            self.root.state("zoomed")  # تمام صفحه (ماکسیمایز) هنگام اجرا
        except Exception:
            pass
        self.root.minsize(min(S(340), w), min(S(480), h))
        self.imgcache, self.listeners = {}, []
        self.q = queue.Queue()
        self.fetching = False
        self.stop = False
        self.set_icon()
        self.cur = 0
        self.side_open = False
        self.mode = "wide"
        self.build()
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Map>", lambda e: later(self.root, "_rz", self.apply_layout, 200) if e.widget is self.root else None)
        self.root.bind("<Escape>", lambda e: self.hide_drawer() if getattr(self, "side_open", False) else None)
        self.root.after(150, self.pump)
        self.root.after(1500, self.rates_tick)
        self.root.after(30000, self.day_tick)
        self.last_day = dt.date.today()
        self.root.bind("<Control-plus>", lambda e: self.zoom(10))
        self.root.bind("<Control-equal>", lambda e: self.zoom(10))
        self.root.bind("<Control-minus>", lambda e: self.zoom(-10))
        self.root.bind("<Control-0>", lambda e: self.zoom(0, reset=True))
        self.root.bind("<Control-n>", lambda e: self.go(2))
        self.root.bind("<Control-N>", lambda e: self.go(2))
        self.root.bind("<Control-f>", lambda e: self.go(1))
        self.root.bind("<Control-F>", lambda e: self.go(1))
        self.root.bind("<Control-d>", lambda e: self.go(0))
        self.root.bind("<Control-D>", lambda e: self.go(0))
        self.root.bind("<Control-MouseWheel>", lambda e: self.zoom(10 if e.delta > 0 else -10))
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.go(0)
        self.root.after(800, self._prebuild_step)

    def set_icon(self):
        try:
            import tempfile
            path = icons.ico_path()
            if path and os.path.exists(path):
                self.root.iconbitmap(default=path)
                self.root.iconbitmap(path)
                return
        except Exception:
            pass
        try:
            img = icons.load_app_icon()  # فقط خود لوگوی انبارمن (بدون کادر)
            self.root.iconphoto(True, img)
            self._icon = img
            return
        except Exception:
            pass
        try:
            img = icons.load_app_icon()
            self.root.iconphoto(True, img)
            self._icon = img
            return
        except Exception:
            pass
        try:
            img = tk.PhotoImage(width=64, height=64)
            img.put(BLUE, to=(0, 0, 64, 64))
            img.put("#FFFFFF", to=(16, 24, 48, 48))
            img.put(BLUE, to=(30, 16, 34, 48))
            img.put("#FFFFFF", to=(20, 16, 44, 24))
            self.root.iconphoto(True, img)
            self._icon = img
        except Exception:
            pass

    def zoom(self, delta, reset=False):
        cur = int(round(ZM * 100))
        new = 100 if reset else max(70, min(180, cur + delta))
        if new == cur:
            return
        self.save_layout()
        self.db.set_setting("zoom", new)
        self.rebuild()

    def save_layout(self):
        if getattr(self, "mode", "wide") != "wide":
            return
        if self._minimized() or getattr(self, "_was_min", False) or getattr(self, "_skip_save", False):
            return
        try:
            x = self.shell.sash_coord(0)[0]
            self.sidebar_w = max(260, min(420, (self.shell.winfo_width() - x) / (SC * ZM)))
            self.db.set_setting("sidebar_w", int(self.sidebar_w))
        except Exception:
            pass

    def rebuild(self):
        global ZM
        ZM = max(0.7, min(1.8, int(self.db.get_setting("zoom", "95")) / 100.0))
        self.imgcache.clear()
        self.listeners.clear()
        self.shell.destroy()
        self.build()
        self.go(self.cur)

    # ---- ارز
    def rate(self, code):
        if code == "IRT":
            return 1.0
        try:
            return float(self.db.get_setting("rate_" + code, "0") or 0)
        except ValueError:
            return 0.0

    def rate_prev(self, code):
        try:
            return float(self.db.get_setting("rate_prev_" + code, "0") or 0)
        except ValueError:
            return 0.0

    def rates_tick(self):
        try:
            at = self.db.get_setting("rates_at", "")
            if (not at) or (dt.datetime.now() - dt.datetime.fromisoformat(at)) > dt.timedelta(hours=1):
                self.start_rates()
        except Exception:
            self.start_rates()
        self.root.after(60 * 1000, self.rates_tick)

    def start_rates(self, manual=False):
        if getattr(self, "_rates_busy", False):
            if manual:
                info(self, "بروزرسانی نرخ در حال انجام است؛ چند ثانیه صبر کنید.")
            return
        self._rates_busy = True
        self._rates_manual = manual

        def work():
            try:
                r = P.fetch_rates()
                self.q.put(lambda: self.on_rates(r, None))
            except Exception as e:  # noqa
                msg = str(e)
                self.q.put(lambda: self.on_rates(None, msg))
        threading.Thread(target=work, daemon=True).start()

    def on_rates(self, r, err):
        self._rates_busy = False
        if r:
            old = {c: self.rate(c) for c in ("USD", "AED")}
            for k, v in r.items():
                self.db.set_setting("rate_" + k, v)
            new = {c: self.rate(c) for c in ("USD", "AED")}
            for c in ("USD", "AED"):
                if old[c] and new[c] and abs(new[c] - old[c]) > 1e-9:
                    self.db.set_setting("rate_prev_" + c, old[c])
            self.db.sync_sell_prices(new)
            new_usd = new["USD"]
            self.db.set_setting("rates_at", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.update_rates_box(err)
        if r:
            self.reload_all()  # همه صفحه ها (کالاها، فروش، داشبورد) با قیمت جدید دوباره ساخته شوند
        else:
            self.refresh_current()
        if getattr(self, "_rates_manual", False):
            if r:
                n = self.db.count_dollar_products()
                info(self, f"نرخ دلار: {money(self.rate('USD'))} تومان\n"
                           f"قیمت فروش {fa(n)} کالا بر اساس این نرخ به‌روز شد.")
            else:
                info(self, f"دریافت نرخ ناموفق بود:\n{err or ''}\n(اینترنت یا دسترسی به tgju را بررسی کنید)")
            self._rates_manual = False

    def update_rates_box(self, err=None):
        if not self.rate_lbls or self.rate_time is None:
            return
        at = self.db.get_setting("rates_at", "")
        for code, l in self.rate_lbls.items():
            r = self.rate(code)
            l.config(text=(money(r) + " تومان") if r else "—")
        if err and not at:
            self.rate_time.config(text="دریافت نرخ ناموفق (اینترنت؟)", fg=RED)
        else:
            try:
                d = dt.datetime.fromisoformat(at)
                txt = f"آخرین بروزرسانی:\n{fa(J.fmt(d.date()))}  ساعت {fa(d.strftime('%H:%M'))}"
            except Exception:
                txt = "هنوز دریافت نشده"
            self.rate_time.config(text=txt, fg=MUTED)

    # ---- واکنشگرایی
    def win_px(self):
        w = self.root.winfo_width()
        return w if w > 200 else getattr(self, "_init_w", S(1100))

    def win_h(self):
        h = self.root.winfo_height()
        return h if h > 200 else getattr(self, "_init_h", S(700))

    def win_w(self):
        """عرض پنجره برنامه (به واحد طراحی)"""
        return self.win_px() / (SC * ZM)

    def calc_mode(self):
        """wide: سایدبار کامل | compact: سایدبار فقطآیکون | narrow: منوی کشویی (موبایل)"""
        lw = self.win_px() / (SC * ZM)
        return "wide" if lw >= 1100 else ("compact" if lw >= 700 else "narrow")

    def make_key(self):
        lh = self.win_h() / (SC * ZM)
        return (self.mode, lh >= 560, lh >= 650, lh >= 740)

    def avail(self):
        """عرض ناحیه محتوا (به واحد طراحی، هممقیاس با S())"""
        k = SC * ZM
        w = self.content.winfo_width()
        if w < 200:
            side = {"wide": S(max(260, min(self.sidebar_w, 420))) + S(10), "compact": S(86), "narrow": 0}.get(self.mode, 0)
            w = self.win_px() - side
        return w / k

    def level(self, a, b):
        w = self.avail()
        return 0 if w >= a else (1 if w >= b else 2)

    def on_resize(self, e):
        if e.widget is self.root:
            later(self.root, "_rz", self.apply_layout, 120)

    def _minimized(self):
        try:
            return self.root.state() == "iconic" or self.root.winfo_width() < 200 or self.root.winfo_height() < 200
        except Exception:
            return False

    def apply_layout(self):
        try:
            if self._minimized():
                self._was_min = True  # حالت مینیمایز: چیدمان و عرض سایدبار را دست نزن
                return
            if getattr(self, "_was_min", False):
                self._was_min = False
                self.root.update_idletasks()
                self.mode = self.calc_mode()
                self.chrome_key = None  # بعد از برگشتن، همه چیز از نو چیده شود
                self._skip_save = True  # عرض فعلی سایدبار (فشرده) ذخیره نشود
            self.mode_old = self.mode
            new = self.calc_mode()
            old = self.mode
            self.mode = new
            key = self.make_key()
            self.mode = old
            if key != self.chrome_key:
                self.save_layout()
                self.mode = new
                self.rebuild_chrome()
            self.fix_side()
            self._skip_save = False
            self.root.update_idletasks()
            later(self.root, "_fx", self.fix_side, 350)
            for i, pg in enumerate(self.pages):
                if pg is None:
                    continue
                if i == self.cur:
                    rl = getattr(pg, "relayout", None)
                    if rl:
                        rl()
                    elif getattr(pg, "relayout", None) is None:
                        pass
                else:
                    self.dirty[i] = True  # صفحه های دیگر هنگام نمایش با عرض جدید ساخته شوند
        except Exception:
            traceback.print_exc()

    def fix_side(self):
        """اگر بعد از مینیمایز/بازگردانی سایدبار فشرده شده بود، به عرض حداقل برمی گردد"""
        try:
            if self.mode != "wide" or self._minimized():
                return
            self.root.update_idletasks()
            if self.side.winfo_width() < S(258):
                self.place_side()
        except Exception:
            pass

    def rebuild_chrome(self):
        self.chrome_key = self.make_key()
        if self.mode != "narrow":
            self.side_open = False
        self.build_header()
        self.build_side()
        self.place_side()
        self.update_header()
        self.update_rates_box()
        for n in self.nav:
            n.set_on(n._pi == self.cur)

    def place_side(self):
        sh = self.shell
        try:
            sh.forget(self.side)
        except tk.TclError:
            pass
        self.side.place_forget()
        if self.mode == "wide":
            lw = self.win_px() / (SC * ZM)
            sh.configure(sashwidth=S(10), bg=BG, sashrelief="flat")
            sh.add(self.side, minsize=S(260), stretch="never", width=S(max(260, min(self.sidebar_w, 420))))
        elif self.mode == "compact":
            sh.configure(sashwidth=0)
            sh.add(self.side, minsize=S(70), stretch="never", width=S(86))
        else:
            sh.configure(sashwidth=0)
            if self.side_open:
                self.show_drawer()

    def show_drawer(self):
        self.side_open = True
        self.side.place(in_=self.shell, relx=1.0, rely=0.0, anchor="ne", relheight=1.0,
                        width=max(S(220), min(S(300), self.win_px() - S(50))))
        self.side.tkraise()

    def hide_drawer(self):
        self.side_open = False
        self.side.place_forget()

    def toggle_drawer(self):
        if self.side_open:
            self.hide_drawer()
        else:
            self.show_drawer()

    # ---- ساخت UI
    def build(self):
        self.mode = self.calc_mode()
        self.chrome_key = self.make_key()
        self.shell = tk.PanedWindow(self.root, orient="horizontal", sashwidth=S(10) if self.mode == "wide" else 0,
                                    sashrelief="flat", bg=BG, bd=0,
                                    opaqueresize=False, sashcursor="sb_h_double_arrow")
        self.shell.pack(fill="both", expand=True)
        self.content = tk.Frame(self.shell, bg=BG)
        self.side = tk.Frame(self.shell, bg=BG)
        self.shell.add(self.content, minsize=S(280), stretch="always")
        self.side_open = False
        self.nav = []
        self.build_side()
        self.place_side()
        self.hd = None
        self.build_header()
        self.strip = rbox(self.content, BLUE_BG, 14, 2)
        sbody = self.strip.body
        self.strip_l = tk.Label(sbody, text="", font=F(9), bg=BLUE_BG, fg=BLUE, anchor="e")
        self.strip_l.pack(side="right", padx=S(16), pady=S(6))
        self.bar = RProgress(sbody, 170, 8, BLUE_BG)
        self.bar.pack(side="right", padx=S(8))
        Btn(sbody, "توقف", self.stop_fetch, "plain", size=8, py=3, icon="x").pack(side="left", padx=S(16), pady=S(4))
        self.stack = tk.Frame(self.content, bg=BG)
        self.stack.pack(fill="both", expand=True, padx=S(8), pady=(0, S(8)))
        # لایه بارگذاری روی stack — تا وقتی صفحه آماده شود دیده می‌شود
        self.loading = tk.Frame(self.content, bg=BG)
        self.loading_inner = tk.Frame(self.loading, bg=BG)
        self.loading_inner.place(relx=0.5, rely=0.42, anchor="center")
        self._loading_dots = 0
        self._loading_job = None
        # اسکلتون ساده (استخوانی)
        sk = tk.Frame(self.loading_inner, bg=BG)
        sk.pack()
        self._sk_bars = []
        for wfrac, h in ((0.0, 14), (0.0, 14), (0.0, 14)):
            bar = tk.Frame(sk, bg=SEP, height=S(14))
            bar.pack(fill="x", pady=S(6))
            bar.configure(width=S(280))
            self._sk_bars.append(bar)
        self.loading_lbl = tk.Label(self.loading_inner, text="در حال بارگذاری…",
                                    font=F(11), bg=BG, fg=MUTED)
        self.loading_lbl.pack(pady=(S(16), 0))
        self.pages = [None] * 6
        self.dirty = [True] * 6
        self._rj = None
        self._page_busy = False

    def build_header(self):
        old = getattr(self, "hd", None)
        if old is not None:
            try:
                old.destroy()
            except Exception:
                pass
        narrow = self.mode == "narrow"
        own_row = self.mode != "wide"
        hd = tk.Frame(self.content, bg=BG)
        kw = {}
        st = getattr(self, "stack", None)
        try:
            if st is not None and st.winfo_exists():
                kw["before"] = st
        except Exception:
            pass
        hd.pack(fill="x", padx=S(14), pady=(S(14), S(8)), **kw)
        self.hd = hd
        top = tk.Frame(hd, bg=BG)
        top.pack(fill="x")
        if narrow:
            Btn(top, "", self.toggle_drawer, "plain", w=42, h=42, icon="menu").pack(side="right", padx=(S(10), 0))
        Btn(top, "", self.toggle_theme, "plain", w=40, h=40, icon="sun" if THEME_DARK else "moon").pack(
            side="left", padx=(0, S(12)), pady=(S(2), 0))
        tcol = tk.Frame(top, bg=BG)
        tcol.pack(side="right")
        self.title = tk.Label(tcol, text=self.TITLES[self.cur], font=F(18 if narrow else 24, True), bg=BG, fg=TEXT,
                              anchor="e")
        self.title.pack(anchor="e")
        self.subtitle = tk.Label(tcol, text=self.now_text(), font=F(10), bg=BG, fg=MUTED, anchor="e")
        self.subtitle.pack(anchor="e")
        if own_row:
            cw = Wrap(hd, bg=BG, gap=8, vgap=6, align="right")
            cw.pack(fill="x", pady=(S(8), 0))
            order = (("today", BLUE), ("items", ORANGE), ("assets", GREEN))
        else:
            cw = Wrap(top, bg=BG, gap=8, vgap=6, align="left")
            cw.pack(side="left", fill="x", expand=True, padx=(0, S(8)))
            order = (("assets", GREEN), ("items", ORANGE), ("today", BLUE))
        self.chips = {}
        chip_icons = {"today": "cart", "items": "box", "assets": "wallet"}
        for k, col in order:
            ch = Chip(cw, col, chip_icons.get(k))
            cw.add(ch)
            self.chips[k] = ch
        self.chips_wrap = cw

    def build_side(self):
        for w in self.side.winfo_children():
            w.destroy()
        self.shop_lbl = None
        self.rate_lbls, self.rate_time = {}, None
        self.nav = []
        compact = self.mode == "compact"
        sc = Card(self.side, r=26, pad=8 if compact else 12, auto=False)
        sc.pack(fill="both", expand=True, padx=(0, S(10)), pady=S(10))
        if compact:
            self.build_side_compact(sc.body)
        else:
            self.build_side_full(sc.body)

    def build_side_compact(self, sb):
        tile(sb, "box", BLUE, 40, 13, 16).pack(pady=(S(2), S(10)))
        for i in self.NAV_ORDER:
            t, g, c = self.NAV[i]
            n = NavItem(sb, t, g, c, partial(self.go, i), compact=True)
            n._pi = i
            n.pack(fill="x", pady=S(2))
            self.nav.append(n)
        Btn(sb, "", self.show_support, "primary", w=44, h=40, icon="heart").pack(side="bottom", pady=(S(6), 0))
        Btn(sb, "", self.open_site, "tint", w=44, h=40, icon="globe").pack(side="bottom", pady=(S(6), 0))
        Btn(sb, "", self.open_tutorial, "plain", w=44, h=40, icon="book").pack(side="bottom", pady=(S(6), 0))

    def build_side_full(self, sb):
        lh = self.win_h() / (SC * ZM)
        if self.mode == "narrow":
            cr = tk.Frame(sb, bg=CARD)
            cr.pack(fill="x", pady=(0, S(4)))
            Btn(cr, "بستن منو", self.hide_drawer, "plain", size=9, py=5, icon="x").pack(side="left")
        # ---- پایین سایدبار: همیشه دیده می شود (دکمه ها و اندازه متن)
        br = tk.Frame(sb, bg=CARD)
        br.pack(side="bottom", fill="x", pady=(S(8), 0))
        for ci in (0, 1, 2):
            br.grid_columnconfigure(ci, weight=1, uniform="sbb")
        Btn(br, "حمایت", self.show_support, "primary", size=9, h=40, px=6, icon="heart", flex=True).grid(
            row=0, column=2, sticky="ew")
        Btn(br, "آموزش", self.open_tutorial, "plain", size=9, h=40, px=6, icon="tutorial", flex=True).grid(
            row=0, column=1, sticky="ew", padx=S(5))
        Btn(br, "سایت من", self.open_site, "tint", size=9, h=40, px=6, icon="globe", flex=True).grid(
            row=0, column=0, sticky="ew")
        zr = tk.Frame(sb, bg=CARD)
        zr.pack(side="bottom", fill="x", pady=(S(8), 0))
        Btn(zr, "A+", lambda: self.zoom(10), "tint", size=10, w=46, h=32).pack(side="left")
        Btn(zr, "A−", lambda: self.zoom(-10), "tint", size=10, w=46, h=32).pack(side="left", padx=S(6))
        lbl(zr, "اندازه متن", 9, fg=MUTED).pack(side="right")
        # ---- بخش بالا: لوگو، فروشگاه، منو و نرخ ها؛ اگر جا نشد با چرخ موس پایین برود
        mid = ScrollFrame(sb, CARD)
        mid.pack(side="top", fill="both", expand=True)
        body = mid.inner
        logo = tk.Frame(body, bg=CARD)
        logo.pack(fill="x", pady=(S(2), S(6)))
        done = False
        if lh >= 560:
            try:
                self.logo_img = icons.load_logo()  # لوگوی SVG شما به‌صورت PNG با کیفیت بالا (200×159)
                plate = rbox(logo, "#FDFDFD", 18, 6)
                plate.pack(fill="x")
                tk.Label(plate.body, image=self.logo_img, bg="#FDFDFD").pack()
                done = True
            except Exception:
                done = False
        if not done:
            tile(logo, "box", BLUE, 40, 13, 16).pack(side="right")
            tk.Label(logo, text="انبارمن", font=F(18, True), fg=BLUE, bg=CARD).pack(side="right", padx=S(10))
        self.shop_lbl = tk.Label(body, text="", font=F(9, True), fg=MUTED, bg=FILL, anchor="e", padx=S(12), pady=S(8))
        self.shop_lbl.pack(fill="x", pady=(0, S(12)))
        for i in self.NAV_ORDER:
            t, g, c = self.NAV[i]
            n = NavItem(body, t, g, c, partial(self.go, i))
            n._pi = i
            n.pack(fill="x", pady=S(2))
            self.nav.append(n)
        boxc = rbox(body, FILL, 16)
        boxc.pack(fill="x", pady=(S(8), S(6)))
        box = boxc.body
        tk.Label(box, text="نرخ امروز", font=F(9, True), bg=FILL, fg=MUTED, anchor="e").pack(
            fill="x", padx=S(12), pady=(S(10), S(4)))
        for code, name, col in (("USD", "دلار آمریکا", GREEN), ("AED", "درهم امارات", ORANGE),
                                ("GOLD18", "طلای ۱۸ عیار", "#FFB300")):
            r = tk.Frame(box, bg=FILL)
            r.pack(fill="x", padx=S(12), pady=S(2))
            ico(r, {"USD": "dollar", "AED": "credit", "GOLD18": "layers"}[code], 16, col, FILL).pack(side="right")
            tk.Label(r, text=name, font=F(9), bg=FILL, fg=TEXT, anchor="e").pack(side="right", padx=S(4))
            l = tk.Label(r, text="—", font=F(9, True), bg=FILL, fg=BLUE)
            l.pack(side="left")
            self.rate_lbls[code] = l
        self.rate_time = tk.Label(box, text="", font=F(8), bg=FILL, fg=MUTED, anchor="e", wraplength=S(210),
                                  justify="right")
        self.rate_time.pack(fill="x", padx=S(12), pady=(S(2), S(4)))
        Btn(box, "بروزرسانی نرخ", lambda: self.start_rates(manual=True), "tint", size=8, py=4, icon="refresh").pack(pady=(0, S(10)))
        self.update_rates_box()

    PAGE_CLS = None

    def page(self, i):
        if self.pages[i] is None:
            with PerfTimer(f"ساخت اولیه صفحه #{i}"):
                self.pages[i] = (DashboardPage, ProductsPage, InvoicePage, WeeklyStatsPage, LatestSalesPage, SettingsPage)[i](self, self.stack)
        return self.pages[i]

    def show_page_loading(self):
        """نمایش اسکلتون/بارگذاری روی ناحیه محتوا"""
        try:
            self.loading.configure(bg=BG)
            self.loading.place(in_=self.stack, relx=0, rely=0, relwidth=1, relheight=1)
            self.loading.lift()
            # روی همه فرزندان stack باشد
            try:
                self.loading.tkraise()
            except Exception:
                pass
            self.loading_lbl.config(text="در حال بارگذاری…")
            self._loading_dots = 0
            self._animate_loading()
        except Exception:
            pass

    def _animate_loading(self):
        if self._loading_job:
            try:
                self.root.after_cancel(self._loading_job)
            except Exception:
                pass
            self._loading_job = None
        if not self.loading.winfo_ismapped():
            return
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        try:
            self.loading_lbl.config(text="در حال بارگذاری" + dots)
            # پالس ملایم اسکلتون
            for i, bar in enumerate(getattr(self, "_sk_bars", [])):
                bar.configure(bg=SEP if (self._loading_dots + i) % 2 == 0 else "#EBEBF0")
        except Exception:
            pass
        self._loading_job = self.root.after(280, self._animate_loading)

    def hide_page_loading(self):
        if self._loading_job:
            try:
                self.root.after_cancel(self._loading_job)
            except Exception:
                pass
            self._loading_job = None
        try:
            self.loading.place_forget()
        except Exception:
            pass

    def go(self, i, e=None):
        with PerfTimer(f"go({i}) کل زمان کلیک روی منو تا پایان"):
            if getattr(self, "_page_busy", False):
                return
            self._page_busy = True
            try:
                self.cur = i
                if self.mode == "narrow" and self.side_open:
                    self.hide_drawer()
                for n in self.nav:
                    n.set_on(n._pi == i)
                for p in self.pages:
                    if p is not None:
                        p.frame.pack_forget()
                # همیشه اسکلتون را نشان بده تا چیدمان ناقص دیده نشود
                self.show_page_loading()
                try:
                    self.root.update_idletasks()
                except Exception:
                    pass

                pg = self.page(i)
                rl = getattr(pg, "relayout", None)
                if rl:
                    with PerfTimer(f"relayout صفحه #{i} (پیش از نمایش)"):
                        try:
                            rl()
                        except Exception:
                            traceback.print_exc()
                if not getattr(pg, "_wrapped", False):
                    pg._wrapped = True
                    with PerfTimer(f"wrap_tree صفحه #{i} (پیش از نمایش)"):
                        try:
                            wrap_tree(pg.frame)
                        except Exception:
                            pass
                if self.dirty[i]:
                    self.dirty[i] = False
                    with PerfTimer(f"refresh صفحه #{i} (پیش از نمایش)"):
                        try:
                            pg.refresh()
                        except Exception:
                            traceback.print_exc()
                if rl:
                    try:
                        rl()
                    except Exception:
                        pass

                # صفحه را زیر لایه loading قرار بده (هنوز دیده نمی‌شود)
                pg.frame.pack(fill="both", expand=True)
                try:
                    self.root.update_idletasks()
                    # یک پاس دیگر برای Wrap/RGrid بعد از دانستن عرض واقعی
                    if rl:
                        rl()
                    self.root.update_idletasks()
                except Exception:
                    pass

                self.title.config(text=self.TITLES[i])
                self.subtitle.config(text=self.now_text())
                self.schedule_refresh(10)

                # loading را بعد از چند میلی‌ثانیه بردار تا Wrap/RGrid چیدمان نهایی کنند
                def _reveal(step=0):
                    try:
                        self.root.update_idletasks()
                        rl2 = getattr(self.page(self.cur), "relayout", None)
                        if rl2 and step == 0:
                            rl2()
                            self.root.update_idletasks()
                    except Exception:
                        pass
                    if step < 1:
                        self.root.after(40, lambda: _reveal(1))
                        return
                    self.hide_page_loading()
                    self._page_busy = False
                self.root.after(30, lambda: _reveal(0))
            except Exception:
                traceback.print_exc()
                try:
                    self.hide_page_loading()
                except Exception:
                    pass
                self._page_busy = False

    def _prebuild_step(self):
        try:
            for i in range(len(self.pages)):
                if self.pages[i] is None:
                    self.page(i)
                    break
        except Exception:
            pass
        if any(p is None for p in self.pages):
            self.root.after(120, self._prebuild_step)

    def mark_dirty(self):
        self.dirty = [True] * 6

    def schedule_refresh(self, delay=40):
        if self._rj is None:
            self._rj = self.root.after(delay, self._do_refresh)

    def _do_refresh(self):
        self._rj = None
        i = self.cur
        if self.dirty[i]:
            self.dirty[i] = False
            with PerfTimer(f"refresh صفحه #{i}"):
                try:
                    self.page(i).refresh()
                except Exception:
                    traceback.print_exc()
        with PerfTimer("update_header"):
            self.update_header()
        for f in list(self.listeners):
            try:
                f()
            except Exception:
                pass

    def refresh_current(self):
        self.mark_dirty()
        self.schedule_refresh(40)

    def reload_all(self):
        self.mark_dirty()
        self.schedule_refresh(10)


    def manage_categories(self):
        d = CategoriesDialog(self)
        self.root.wait_window(d)
        self.reload_all()

    def update_header(self):
        t = self.db.totals()
        today = dt.date.today()
        ds = self.db.daily_sales(today, today).get(today.isoformat(), (0, 0))
        self.chips["assets"].config(text=f"کل دارایی: {short(t['assets'])} تومان")
        self.chips["items"].config(text=f"{fa(t['q'])} عدد در {fa(t['n'])} کالا")
        self.chips["today"].config(text=f"فروش امروز: {short(ds[0])} تومان")
        if self.shop_lbl is not None:
            self.shop_lbl.config(text=(self.db.get_setting("shop_name") or "فروشگاه من"))
        cw = getattr(self, "chips_wrap", None)
        if cw is not None:
            cw.after_idle(cw.layout)

    def thumb(self, name, size=56):
        return self.thumb_path(self.db.image_path(name) if name else None, size)

    def thumb_path(self, path, size=56):
        key = (path, size)
        if key in self.imgcache:
            return self.imgcache[key]
        img = None
        if path and os.path.exists(path):
            try:
                img = tk.PhotoImage(file=path)
                w = img.width()
                if w > size * 1.5:
                    img = img.subsample(max(1, round(w / size)))
                elif w * 1.4 < size:
                    img = img.zoom(max(1, round(size / w)))
            except Exception:
                img = None
        if img is None:
            img = tk.PhotoImage(width=size, height=size)
            img.put(C(FILL), to=(0, 0, size, size))
        round_img(img, max(4, size // 6))
        self.imgcache[key] = img
        return img

    def now_text(self):
        return J.fmt_long(dt.date.today()) + "  ساعت " + J.fa(dt.datetime.now().strftime("%H:%M"))

    def day_tick(self):
        if getattr(self, "subtitle", None) is not None:
            try:
                self.subtitle.config(text=self.now_text())
            except Exception:
                pass
        if dt.date.today() != self.last_day:
            self.last_day = dt.date.today()
            self.reload_all()
        self.root.after(30000, self.day_tick)

    # ---- عملیات
    def add_product(self):
        d = ProductDialog(self)
        self.root.wait_window(d)
        if d.saved:
            self.reload_all()
            p = self.db.product(d.result_pid)
            if d.want_fetch or not p["image"]:
                self.start_fetch([(p["id"], p["name"], not p["image"], d.want_fetch)])

    def edit_product(self, pid):
        d = ProductDialog(self, pid)
        self.root.wait_window(d)
        if d.saved:
            self.reload_all()
            p = self.db.product(pid)
            force_img = bool(getattr(d, "_name_changed", False))
            need_img = force_img or (not p["image"])
            if d.want_fetch or need_img:
                self.start_fetch([(p["id"], p["name"], need_img, bool(d.want_fetch))])

    def delete_product(self, pid, name):
        if ask(self, f"«{name}» حذف شود؟\n(سوابق فروش قبلی در آرشیو می ماند)", "حذف"):
            self.db.delete_product(pid)
            self.reload_all()

    def sell(self, pid):
        d = SaleDialog(self, pid)
        self.root.wait_window(d)
        if d.done:
            # Mark all pages stale and immediately refresh sales views, not only the current page.
            self.mark_dirty()
            try:
                if self.pages[0] is not None:
                    self.pages[0].refresh()
                    self.dirty[0] = False
                if self.pages[4] is not None:
                    self.pages[4].refresh()
                    self.dirty[4] = False
            except Exception as e:
                info(self, f"فروش ثبت شد، اما بهروزرسانی نمایش آخرین فروشها با خطا مواجه شد:\n{e}")
            self.update_header()
            self.schedule_refresh(10)

    def quick_add(self, pid):
        self.db.quick_add(pid, 1)
        self.reload_all()

    def show_support(self):
        SupportDialog(self)

    def colors(self):
        try:
            d = json.loads(self.db.get_setting("colors_dark" if THEME_DARK else "colors_light", "{}"))
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}

    def load_colors(self):
        apply_custom(self.colors())

    def save_colors(self, d):
        self.db.set_setting("colors_dark" if THEME_DARK else "colors_light", json.dumps(d))
        self.save_layout()
        self.load_colors()
        self.root.configure(bg=BG)
        self.rebuild()

    def open_tutorial(self):
        webbrowser.open(TUTORIAL_URL)

    def open_site(self):
        webbrowser.open("https://www.myhadipour.ir/")

    def toggle_theme(self):
        global THEME_DARK
        self.save_layout()
        THEME_DARK = not THEME_DARK
        self.db.set_setting("theme", "dark" if THEME_DARK else "light")
        self.load_colors()
        self.root.configure(bg=BG)
        titlebar_dark(self.root)
        self.rebuild()

    def update_sell_price(self, pid):
        p = self.db.product(pid)
        if not p["sell_usd"]:
            info(self, "این کالا قیمت فروش پایه ندارد. ابتدا در «ویرایش کالا» قیمت فروش را وارد کنید.")
            return
        cur = p["sell_cur"] or "USD"
        rate = self.rate(cur)
        if not rate:
            info(self, "نرخ ارز هنوز دریافت نشده؛ چند ثانیه صبر کنید یا اینترنت را بررسی کنید.")
            return
        self.db.sync_sell_price(pid, rate)
        self.reload_all()

    def quick_sub(self, pid):
        self.db.quick_sub(pid, 1)
        self.reload_all()

    def show_prices(self, pid):
        PricesDialog(self, pid)

    def update_all(self):
        self.start_rates()
        rows = [r for r in self.db.products() if r["auto_price"] or not r["image"]]
        if rows:
            self.start_fetch([(r["id"], r["name"], not r["image"], bool(r["auto_price"])) for r in rows])

    def start_fetch(self, items):
        if self.fetching:
            info(self, "یک دریافت قیمت در حال انجام است؛ کمی صبر کنید یا «توقف» را بزنید.")
            return
        self.fetching = True
        self.stop = False
        self.bar.config(maximum=len(items), value=0)
        self.strip_l.config(text="در حال دریافت قیمت...")
        self.strip.pack(fill="x", before=self.stack)

        def work():
            for i, (pid, name, need_img, fetch_details) in enumerate(items):
                if self.stop:
                    break
                self.q.put(lambda i=i, name=name: (self.bar.config(value=i),
                                                   self.strip_l.config(text=f"({fa(i + 1)}/{fa(len(items))}) {name[:38]}")))
                res = P.fetch_all(name) if fetch_details else None
                time.sleep(0.4)
                img = None
                if need_img:
                    if fetch_details:
                        for r in sorted(res or [], key=lambda r: not r.get("price")):
                            if r.get("img"):
                                img = fetch_cover(r["img"], self.db)
                                if img:
                                    break
                    else:
                        image_url = P.fetch_digikala_image(name)
                        if image_url:
                            img = fetch_cover(image_url, self.db)
                self.q.put(lambda pid=pid, res=res, img=img: self.on_price(pid, res, img))
            self.q.put(self.fetch_done)
        threading.Thread(target=work, daemon=True).start()

    def on_price(self, pid, res, img):
        if res is not None:
            self.db.save_prices(pid, res)
        if img:
            self.db.set_image(pid, img)
        self.mark_dirty()
        self.schedule_refresh(900)

    def fetch_done(self):
        self.fetching = False
        self.strip.pack_forget()
        self.update_header()

    def stop_fetch(self):
        self.stop = True

    def pump(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        except Exception:
            traceback.print_exc()
        self.root.after(150, self.pump)

    def close(self):
        self.stop = True
        self.save_layout()
        self.root.destroy()

    def run(self):
        self.root.after(300, self.apply_layout)  # چیدمان را بعد از نمایش اولیه پنجره، با اندازه واقعی بساز
        self.root.mainloop()


def _memo_methods(cls, names):
    """نتیجه پرس وجوهای سنگین خواندنی تا وقتی داده عوض نشده، دوباره اجرا نمی شود"""
    for n in names:
        orig = getattr(cls, n)

        def make(orig, n):
            def f(self, *a):
                cache = self.__dict__.setdefault("_rc", {})
                key = (n,) + a
                try:
                    if key in cache:
                        return cache[key]
                except TypeError:
                    return orig(self, *a)
                v = orig(self, *a)
                cache[key] = v
                return v
            return f
        setattr(cls, n, make(orig, n))


_memo_methods(DB, ["last_sale", "daily_sales", "totals"])


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            try:  # اولویت پردازش را کمی بالا می برد تا وقتی سیستم شلوغ است، برنامه کندتر نشود
                import ctypes
                k = ctypes.windll.kernel32
                k.SetPriorityClass(k.GetCurrentProcess(), 0x00008000)
            except Exception:
                pass
        App().run()
    except Exception:
        err = traceback.format_exc()
        try:
            open(str(app_dir() / "error.log"), "w", encoding="utf-8").write(err)
        except Exception:
            pass
        try:
            ctypes.windll.user32.MessageBoxW(0, "خطای برنامه:\n\n" + err[-900:], "انبارمن", 0x10)
        except Exception:
            print(err)
