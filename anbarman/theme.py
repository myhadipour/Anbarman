# -*- coding: utf-8 -*-
"""تم، رنگ‌ها و فونت‌ها (معادل استایل/CSS برنامه)"""
import os
import sys
import ctypes
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont

from .jalali import fa
from .database import app_dir

def _assets_dir():
    """مسیر assets — هم در حالت عادی و هم داخل EXE (PyInstaller)"""
    import sys
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
        for cand in (base / "anbarman" / "assets", base / "assets"):
            if cand.exists():
                return cand
    return Path(__file__).resolve().parent / "assets"

ASSETS = _assets_dir()
FONTS_DIR = ASSETS / "fonts"

# ---------------------------------------------------------------- پالت (الهام از iOS جدید)
BG = "#F2F2F7"
CARD = "#FEFEFE"
TEXT = "#1C1C1E"
MUTED = "#8E8E93"
SEP = "#E5E5EA"
BLUE = "#007AFF"
BLUE_BG = "#DCEBFF"
GREEN = "#34C759"
RED = "#FF3B30"
ORANGE = "#FF9500"
PURPLE = "#AF52DE"
TEAL = "#5AC8FA"
YELLOW = "#FFCC00"
FILL = "#F2F2F7"
SHADOW = "#00000018"
ACCENT = BLUE

# ---------------------------------------------------------------- تم روشن/تاریک
DARK = False
_DARK_MAP = {
    "#F2F2F7": "#0E0E11",
    "#FEFEFE": "#1C1C1F",
    "#1C1C1E": "#F5F5F7",
    "#8E8E93": "#98989F",
    "#E5E5EA": "#38383A",
    "#DCEBFF": "#17304F",
    "#007AFF": "#0A84FF",
    "#34C759": "#30D158",
    "#FF3B30": "#FF453A",
    "#FF9500": "#FF9F0A",
    "#AF52DE": "#BF5AF2",
    "#5AC8FA": "#64D2FF",
    "#FFCC00": "#FFD60A",
}

_COLOR_KEYS = frozenset((
    "bg", "background", "fg", "foreground", "activebackground", "activeforeground",
    "highlightbackground", "highlightcolor", "insertbackground", "selectbackground",
    "selectforeground", "disabledforeground", "readonlybackground",
))


def C(col):
    if not col:
        return col
    if DARK and col in _DARK_MAP:
        return _DARK_MAP[col]
    return col


COLOR_ROLES = [
    ("bg", "رنگ پس زمینه برنامه", "#F2F2F7"),
    ("card", "رنگ کادرها", "#FEFEFE"),
    ("text", "رنگ متن", "#1C1C1E"),
    ("muted", "رنگ متن کم‌رنگ", "#8E8E93"),
    ("blue", "رنگ اصلی", "#007AFF"),
]


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


def _mix(a, b, t):
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return _hex((ra+(rb-ra)*t, ga+(gb-ga)*t, ba+(bb-ba)*t))


def _safe(h):
    try:
        _rgb(h)
        return h
    except Exception:
        return None


def apply_custom(d):
    global BG, CARD, TEXT, MUTED, BLUE, BLUE_BG, FILL
    for role, _t, key in COLOR_ROLES:
        v = _safe(d.get(role) or d.get(key))
        if not v:
            continue
        if role == "bg":
            BG = FILL = v
        elif role == "card":
            CARD = v
        elif role == "text":
            TEXT = v
        elif role == "muted":
            MUTED = v
        elif role == "blue":
            BLUE = ACCENT = v
            BLUE_BG = _mix(v, "#FFFFFF", 0.85)


def rtl(s):
    return "\u200f" + str(s)


def ltr(s):
    return "\u200e" + str(s)


def _themed_options(self, cnf, kw=None):
    if kw is None:
        kw = cnf
        cnf = {}
    rawc = getattr(self, "_RAW_COLOR", False)
    if not rawc and DARK:
        for k in list(kw.keys()):
            if k in _COLOR_KEYS:
                kw[k] = C(kw[k])
    return tk.Misc._options_orig(self, cnf, kw) if hasattr(tk.Misc, "_options_orig") else tk.Misc._options(self, cnf, kw)


def install_theme_hook():
    if not hasattr(tk.Misc, "_options_orig"):
        tk.Misc._options_orig = tk.Misc._options
        tk.Misc._options = _themed_options


def titlebar_dark(win):
    if os.name != "nt":
        return
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        if not hwnd:
            hwnd = win.winfo_id()
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        val = ctypes.c_int(1 if DARK else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), 4)
    except Exception:
        pass


_SCALE = 1.0


def S(n):
    return int(round(n * _SCALE))


def F(size=10, bold=False):
    family = "Vazirmatn"
    return (family, S(size), "bold" if bold else "normal")


def lbl(parent, text="", size=10, bold=False, fg=None, bg=None, anchor="e", **kw):
    fg = C(fg or TEXT)
    bg = C(bg) if bg is not None else None
    return tk.Label(parent, text=text, font=F(size, bold), fg=fg, bg=bg, anchor=anchor, **kw)


def register_fonts():
    """فونت‌ها از assets/fonts بارگذاری می‌شوند (دیگر داخل کد base64 نیستند)."""
    d = app_dir() / "fonts"
    d.mkdir(parents=True, exist_ok=True)
    for name in ("Regular", "Bold"):
        src_f = FONTS_DIR / f"Vazirmatn-{name}.ttf"
        p = d / f"Vazirmatn-{name}.ttf"
        if src_f.exists() and (not p.exists() or p.stat().st_size < 1000):
            p.write_bytes(src_f.read_bytes())
        elif not p.exists() and src_f.exists():
            p.write_bytes(src_f.read_bytes())
        if os.name == "nt" and p.exists():
            try:
                ctypes.windll.gdi32.AddFontResourceExW(str(p), 0x10, 0)
            except Exception:
                pass


def make_thumb(src, dst, size=60):
    try:
        from PIL import Image, ImageOps
        im = Image.open(src).convert("RGB")
        ImageOps.fit(im, (size, size)).save(dst, "PNG")
        return True
    except Exception:
        pass
    if os.name == "nt":
        try:
            s, d = str(src).replace("'", "''"), str(dst).replace("'", "''")
            ps = ("Add-Type -AssemblyName System.Drawing;"
                  f"$i=[System.Drawing.Image]::FromFile('{s}');$s=[Math]::Min($i.Width,$i.Height);"
                  "$x=($i.Width-$s)/2;$y=($i.Height-$s)/2;"
                  f"$b=New-Object System.Drawing.Bitmap {size},{size};$g=[System.Drawing.Graphics]::FromImage($b);"
                  "$g.DrawImage($i,[System.Drawing.Rectangle]::FromLTRB(0,0,$b.Width,$b.Height),"
                  "$x,$y,$s,$s,[System.Drawing.GraphicsUnit]::Pixel);"
                  f"$b.Save('{d}');$i.Dispose();$b.Dispose()")
            import subprocess
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False,
                           capture_output=True, timeout=30)
            return Path(dst).exists()
        except Exception:
            pass
    return False


def load_png(name):
    """بارگذاری PNG از پوشه assets"""
    p = ASSETS / name
    if p.exists():
        return tk.PhotoImage(file=str(p))
    return None


def assets_path(*parts):
    return ASSETS.joinpath(*parts)
