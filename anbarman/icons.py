# -*- coding: utf-8 -*-
"""آیکون‌های SVG و رندر آن‌ها روی Canvas"""
import re
import math as _math
import tkinter as tk
from pathlib import Path

from . import theme
from .theme import S, MUTED, BLUE, TEXT, lbl

from .theme import ASSETS  # مسیر مشترک (شامل حالت EXE)


def rrect(c, x1, y1, x2, y2, r, **kw):
    """مستطیل گوشه‌گرد روی Canvas"""
    r = min(r, abs(x2 - x1) / 2, abs(y2 - y1) / 2)
    c.create_polygon(
        x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2,
        x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1,
        smooth=True, **kw
    )

import math as _math

_SVG_TOK = re.compile(r"[MmLlHhVvCcSsQqZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_SVG_ATTR = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')
_SVG_ELEM = re.compile(r"<(path|circle|rect|line|polyline|polygon|ellipse)\b([^>]*?)/?>")
_SVG_CACHE = {}

# آیکون ها به صورت کد SVG (۲۴×۲۴، خطی) — با یک رندرکننده کوچک روی Canvas رسم می شوند
ICONS = {
    "dashboard": '<rect x="3" y="3" width="7" height="9" rx="2"/><rect x="14" y="3" width="7" height="5" rx="2"/><rect x="14" y="12" width="7" height="9" rx="2"/><rect x="3" y="16" width="7" height="5" rx="2"/>',
    "box": '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>',
    "invoice": '<rect x="5" y="3" width="14" height="18" rx="3"/><path d="M9 8h6M9 12h6M9 16h4"/>',
    "settings": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2.3"/><circle cx="8" cy="17" r="2.3"/>',
    "tag": '<path d="M3.5 3.5H12l9 9-8.5 8.5-9-9z"/><circle cx="8" cy="8" r="1.4"/>',
    "cart": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2.5 3.5h3l2.4 11.2h10.6l2-8.4H6.5"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "edit": '<path d="M4 20l1-4L15.5 5.5l3 3L8 19z"/><path d="M13.5 7.5l3 3"/>',
    "trash": '<path d="M4 7h16M10 3h4M6 7l1 13h10l1-13M10 11v6M14 11v6"/>',
    "print": '<path d="M7 9V3h10v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v7H7z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "category": '<rect x="3" y="3" width="8" height="8" rx="2.5"/><rect x="13" y="3" width="8" height="8" rx="2.5"/><rect x="3" y="13" width="8" height="8" rx="2.5"/><rect x="13" y="13" width="8" height="8" rx="2.5"/>',
    "folder": '<path d="M3 6h6l2 2h10v11H3z"/>',
    "profit": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "save": '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v5h7V3M8 21v-7h8v7"/>',
    "download": '<path d="M12 4v11M7 11l5 5 5-5M4 20h16"/>',
    "upload": '<path d="M12 16V5M7 9l5-5 5 5M4 20h16"/>',
    "refresh": '<path d="M19 12C19 15.9 15.9 19 12 19C9.8 19 7.9 18 6.6 16.5"/><path d="M5 12C5 8.1 8.1 5 12 5C14.2 5 16.1 6 17.4 7.5"/><path d="M18 3v5h-5"/><path d="M6 21v-5h5"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
    "chart": '<path d="M5 21V10M12 21V4M19 21v-8"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "chevron": '<path d="M6 9l6 6 6-6"/>',
    "chev_l": '<path d="M15 6l-6 6 6 6"/>',
    "chev_r": '<path d="M9 6l6 6-6 6"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="1.6"/><path d="M4 18l5-5 4 4 3-3 4 4"/>',
    "palette": '<path d="M12 3C7 3 3 7 3 12s4 9 9 9c1.5 0 2-1 2-2 0-.8-.5-1.3-.5-2 0-1 .8-1.5 1.8-1.5H18c1.7 0 3-1.3 3-3 0-4-4-7.5-9-7.5z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10.5" cy="7" r="1"/><circle cx="15" cy="7.5" r="1"/>',
    "store": '<path d="M3 9l2-5h14l2 5"/><path d="M5 9v11h14V9"/><path d="M3 9c0 1.7 1.3 3 3 3s3-1.3 3-3c0 1.7 1.3 3 3 3s3-1.3 3-3c0 1.7 1.3 3 3 3s3-1.3 3-3"/>',
}
ICON_OF = {}
ICONS["sun"] = '<circle cx="12" cy="12" r="4"/><line x1="19.00" y1="12.00" x2="21.50" y2="12.00"/><line x1="16.95" y1="16.95" x2="18.72" y2="18.72"/><line x1="12.00" y1="19.00" x2="12.00" y2="21.50"/><line x1="7.05" y1="16.95" x2="5.28" y2="18.72"/><line x1="5.00" y1="12.00" x2="2.50" y2="12.00"/><line x1="7.05" y1="7.05" x2="5.28" y2="5.28"/><line x1="12.00" y1="5.00" x2="12.00" y2="2.50"/><line x1="16.95" y1="7.05" x2="18.72" y2="5.28"/>'
ICONS["moon"] = '<polygon fill="currentColor" points="3.03,11.22 3.14,10.44 3.31,9.67 3.54,8.92 3.84,8.20 4.21,7.50 4.63,6.84 5.11,6.21 5.64,5.64 6.21,5.11 6.84,4.63 7.50,4.21 8.20,3.84 8.92,3.54 9.67,3.31 10.44,3.14 20.86,13.56 20.69,14.33 20.46,15.08 20.16,15.80 19.79,16.50 19.37,17.16 18.89,17.79 18.36,18.36 17.79,18.89 17.16,19.37 16.50,19.79 15.80,20.16 15.08,20.46 14.33,20.69 13.56,20.86 12.78,20.97 12.00,21.00 11.22,20.97 10.44,20.86 9.67,20.69 8.92,20.46 8.20,20.16 7.50,19.79 6.84,19.37 6.21,18.89 5.64,18.36 5.11,17.79 4.63,17.16 4.21,16.50 3.84,15.80 3.54,15.08 3.31,14.33 3.14,13.56 3.03,12.78 3.00,12.00 9.00,8.00 9.03,8.61 9.11,9.22 9.24,9.81 9.42,10.39 9.66,10.96 9.94,11.50 10.27,12.02 10.64,12.50 11.05,12.95 11.50,13.36 11.98,13.73 12.50,14.06 13.04,14.34 13.61,14.58 14.19,14.76 14.78,14.89 15.39,14.97 16.00,15.00 16.61,14.97 17.22,14.89 17.81,14.76 18.39,14.58 18.96,14.34 19.50,14.06 20.02,13.73 20.50,13.36 11.05,3.05 10.64,3.50 10.27,3.98 9.94,4.50 9.66,5.04 9.42,5.61 9.24,6.19 9.11,6.78 9.03,7.39"/>'
ICONS["filter"] = '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>'
ICONS["globe"] = '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3C9 6.5 9 17.5 12 21M12 3c3 3.5 3 14.5 0 18"/>'
ICONS["heart"] = '<path d="M12 20C5 15 3 11.5 3 8.5C3 6 5 4 7.5 4C9.3 4 11 5 12 6.5C13 5 14.7 4 16.5 4C19 4 21 6 21 8.5C21 11.5 19 15 12 20z"/>'
ICONS["menu"] = '<path d="M4 7h16M4 12h16M4 17h16"/>'
ICONS["mail"] = '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 8l9 6 9-6"/>'
ICONS["book"] = '<path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5z"/><path d="M12 6.5v13"/>'
ICONS["tutorial"] = '<circle cx="12" cy="12" r="9"/><path d="M10 8.5v7l5.5-3.5z"/>'
ICONS["eye"] = '<path d="M2 12C5 6.5 8.5 5 12 5s7 1.5 10 7c-3 5.5-6.5 7-10 7s-7-1.5-10-7z"/><circle cx="12" cy="12" r="3"/>'
ICONS["zoom_in"] = '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21M11 8v6M8 11h6"/>'
ICONS["zoom_out"] = '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21M8 11h6"/>'
ICONS["dollar"] = '<path d="M12 4.5v15"/><path d="M15.5 9C15.2 7.9 13.9 7.3 12 7.3 10 7.3 8.7 8.2 8.7 9.6 8.7 12.6 15.5 11.4 15.5 14.4 15.5 15.8 14 16.7 12 16.7 10.1 16.7 8.8 16 8.5 14.9"/>'
ICONS["wallet"] = '<path d="M4 8V6.5C4 5.7 4.7 5 5.5 5H17v3"/><rect x="3" y="8" width="18" height="12" rx="3"/><circle cx="16.5" cy="14" r="1.2" fill="currentColor"/>'
ICONS["info"] = '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5v.6"/>'
ICONS["clock"] = '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>'
ICONS["trend_down"] = '<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>'
ICONS["arrow_up"] = '<path d="M12 19V5M6 11l6-6 6 6"/>'
ICONS["arrow_down"] = '<path d="M12 5v14M6 13l6 6 6-6"/>'
ICONS["barcode"] = '<path d="M4 6v12M7.5 6v12M11 6v12M14 6v12M17 6v12M20 6v12"/>'
ICONS["users"] = '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><path d="M16 4.8c1.9.3 3 1.7 3 3.4s-1.1 3.1-3 3.4M18 14.2c2.2.7 3.5 2.6 3.5 5.8"/>'
ICONS["percent"] = '<path d="M19 5L5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/>'
ICONS["external"] = '<path d="M14 4h6v6M20 4l-9 9M18 14v5H5V6h5"/>'
ICONS["home"] = '<path d="M3.5 11L12 4l8.5 7M6 9.5V20h12V9.5M10 20v-5h4v5"/>'
ICONS["undo"] = '<path d="M8 5L4 9l4 4"/><path d="M4 9h10c3 0 5 2 5 5s-2 5-5 5H8"/>'
ICONS["stop"] = '<rect x="6" y="6" width="12" height="12" rx="3"/>'
ICONS["check_circle"] = '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>'
ICONS["list"] = '<path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4.5" cy="6" r="1.1" fill="currentColor"/><circle cx="4.5" cy="12" r="1.1" fill="currentColor"/><circle cx="4.5" cy="18" r="1.1" fill="currentColor"/>'
ICONS["store"] = '<path d="M4 9l1.5-5h13L20 9"/><path d="M4 9c0 1.7 1.3 3 3 3s3-1.3 3-3c0 1.7 1.3 3 3 3s3-1.3 3-3c0 1.7 1.3 3 3 3"/><path d="M5 12v8h14v-8M10 20v-4h4v4"/>'
ICONS["sync"] = '<path d="M20 7v5h-5"/><path d="M19.5 12C19.5 16 16.2 19 12 19c-2.4 0-4.4-1-5.8-2.6"/><path d="M4 17v-5h5"/><path d="M4.5 12C4.5 8 7.8 5 12 5c2.4 0 4.4 1 5.8 2.6"/>'
ICONS["layers"] = '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 12.5l9 5 9-5M3 16.5l9 5 9-5"/>'
ICONS["credit"] = '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 10h18M7 15h4"/>'
ICONS["bell"] = '<path d="M6 17V11C6 7.7 8.7 5 12 5s6 2.7 6 6v6l1.5 2h-15z"/><path d="M10 20.5h4"/>'
ICONS["copy"] = '<rect x="9" y="9" width="11" height="11" rx="3"/><path d="M5 15V7C5 5.3 6.3 4 8 4h8"/>'

def _bez(p0, p1, p2, p3, n=12):
    pts = []
    for i in range(1, n + 1):
        s = i / n
        u = 1 - s
        pts.append((u * u * u * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s * s * s * p3[0],
                    u * u * u * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s * s * s * p3[1]))
    return pts


def _svg_path(d):
    tok = _SVG_TOK.findall(d)
    i, n = 0, len(tok)
    subs, cur = [], []
    x = y = sx = sy = 0.0
    cmd, lc = "M", None

    def nm():
        nonlocal i
        v = float(tok[i])
        i += 1
        return v
    while i < n:
        if tok[i].isalpha():
            cmd = tok[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    cur.append(cur[0])
                    subs.append(cur)
                    cur = []
                x, y, lc = sx, sy, None
                continue
        rel, C = cmd.islower(), cmd.upper()
        if not cur and C != "M":
            cur = [(x, y)]
        if C == "M":
            nx, ny = nm(), nm()
            if rel:
                nx, ny = nx + x, ny + y
            if cur:
                subs.append(cur)
            cur = [(nx, ny)]
            x = sx = nx
            y = sy = ny
            cmd = "l" if rel else "L"
            lc = None
        elif C == "L":
            nx, ny = nm(), nm()
            if rel:
                nx, ny = nx + x, ny + y
            cur.append((nx, ny))
            x, y, lc = nx, ny, None
        elif C == "H":
            nx = nm() + (x if rel else 0)
            cur.append((nx, y))
            x, lc = nx, None
        elif C == "V":
            ny = nm() + (y if rel else 0)
            cur.append((x, ny))
            y, lc = ny, None
        elif C in "CS":
            if C == "C":
                a, b = nm(), nm()
                if rel:
                    a, b = a + x, b + y
                c1 = (a, b)
            else:
                c1 = (2 * x - lc[0], 2 * y - lc[1]) if lc else (x, y)
            a, b, ex, ey = nm(), nm(), nm(), nm()
            if rel:
                a, b, ex, ey = a + x, b + y, ex + x, ey + y
            cur.extend(_bez((x, y), c1, (a, b), (ex, ey)))
            lc = (a, b)
            x, y = ex, ey
        elif C == "Q":
            a, b, ex, ey = nm(), nm(), nm(), nm()
            if rel:
                a, b, ex, ey = a + x, b + y, ex + x, ey + y
            c1 = (x + 2 / 3 * (a - x), y + 2 / 3 * (b - y))
            c2 = (ex + 2 / 3 * (a - ex), ey + 2 / 3 * (b - ey))
            cur.extend(_bez((x, y), c1, c2, (ex, ey)))
            x, y, lc = ex, ey, None
        else:
            i += 1
    if cur:
        subs.append(cur)
    return subs


def _rrect_pts(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    if r <= 0:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for k in range(7):
            a = _math.radians(a0 + k * 15)
            pts.append((cx + r * _math.cos(a), cy + r * _math.sin(a)))
    pts.append(pts[0])
    return pts


def _svg_shapes(svg):
    got = _SVG_CACHE.get(svg)
    if got is not None:
        return got
    out = []
    for tag, attrs in _SVG_ELEM.findall(svg):
        a = dict(_SVG_ATTR.findall(attrs))

        def f(k, d=0.0, a=a):
            return float(a.get(k, d))
        filled = a.get("fill") == "currentColor"
        if tag == "path":
            for s in _svg_path(a.get("d", "")):
                out.append((s, filled))
        elif tag in ("circle", "ellipse"):
            rx = f("r") if tag == "circle" else f("rx")
            ry = rx if tag == "circle" else f("ry")
            cx, cy = f("cx"), f("cy")
            out.append(([(cx + rx * _math.cos(k * _math.pi / 16), cy + ry * _math.sin(k * _math.pi / 16))
                         for k in range(33)], filled))
        elif tag == "rect":
            out.append((_rrect_pts(f("x"), f("y"), f("width"), f("height"), f("rx")), filled))
        elif tag == "line":
            out.append(([(f("x1"), f("y1")), (f("x2"), f("y2"))], False))
        else:
            nums = [float(v) for v in re.findall(r"[-+]?\d*\.?\d+", a.get("points", ""))]
            pts = list(zip(nums[::2], nums[1::2]))
            if tag == "polygon" and pts:
                pts.append(pts[0])
            out.append((pts, filled))
    _SVG_CACHE[svg] = out
    return out


def draw_svg(c, svg, x, y, size, fg, sw=2.0, tags=()):
    k = size / 24.0
    w = max(1.4, sw * k)
    for pts, filled in _svg_shapes(svg):
        if len(pts) < 2:
            continue
        flat = []
        for px, py in pts:
            flat += [x + px * k, y + py * k]
        if filled and len(pts) > 2:
            c.create_polygon(*flat, fill=fg, outline="", tags=tags)
        else:
            c.create_line(*flat, fill=fg, width=w, capstyle="round", joinstyle="round", tags=tags)


def draw_icon(c, name, x, y, s, fg, tags=()):
    svg = ICONS.get(ICON_OF.get(name, name))
    if svg:
        draw_svg(c, svg, x, y, s, fg, tags=tags)


def tile(parent, glyph, color, size=38, r=11, fsize=14):
    c = tk.Canvas(parent, width=S(size), height=S(size), bg=parent["bg"], highlightthickness=0)
    rrect(c, 0, 0, S(size), S(size), S(r), fill=color, outline="")
    inset = S(size) * 0.24
    draw_icon(c, ICON_OF.get(glyph, glyph), inset, inset, S(size) - 2 * inset, "#FFFFFF")
    return c


def ico(parent, name, size=16, color=None, bg=None):
    """آیکون SVG کوچک روی کانواس"""
    c = tk.Canvas(parent, width=S(size), height=S(size), bg=bg or parent["bg"], highlightthickness=0)
    draw_icon(c, name, 0, 0, S(size), color or MUTED)
    return c


_ROW_ICONS = [
    ("نام کالا", "box"), ("دسته", "category"), ("تعداد", "layers"), ("ارز", "dollar"), ("مبلغ خرید", "wallet"),
    ("قیمت فروش", "tag"), ("تاریخ", "calendar"), ("بارکد", "barcode"), ("خریدار", "user"),
]


def row_label(parent, text, size=9, bg=None):
    """برچسب فرم همراه با آیکون SVG کوچک (سمت راست متن)"""
    bg = bg or parent["bg"]
    icon = next((ic for k, ic in _ROW_ICONS if k in text), None)
    f = tk.Frame(parent, bg=bg)
    if icon:
        ico(f, icon, 16, MUTED, bg).pack(side="right", padx=(S(6), 0))
    lbl(f, text, size, fg=MUTED, bg=bg).pack(side="right")
    return f


def heading(parent, text, size=13, icon="box", color=None, bg=None):
    """عنوان بخش با آیکون SVG داخل کاشی رنگی"""
    bg = bg or parent["bg"]
    f = tk.Frame(parent, bg=bg)
    ts = 24 if size <= 12 else (28 if size <= 14 else 34)
    tile(f, icon, color or BLUE, ts, 8).pack(side="right", padx=(S(8), 0))
    lbl(f, text, size, True, bg=bg).pack(side="right")
    return f




def load_logo():
    p = ASSETS / "logo.png"
    if p.exists():
        return tk.PhotoImage(file=str(p))
    return None

def load_app_icon():
    p = ASSETS / "app_icon.png"
    if p.exists():
        return tk.PhotoImage(file=str(p))
    # fallback
    p2 = ASSETS / "icon.png"
    if p2.exists():
        return tk.PhotoImage(file=str(p2))
    return None

def load_author():
    p = ASSETS / "author.png"
    if p.exists():
        return tk.PhotoImage(file=str(p))
    return None

def ico_path():
    return str(ASSETS / "app_ico.ico")
