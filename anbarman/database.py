# -*- coding: utf-8 -*-
"""لایه پایگاه داده (SQLite)"""
import os
import json
import shutil
import sqlite3
import re
import tempfile
import uuid
import zipfile
import datetime as dt
from pathlib import Path

from .jalali import J, fa, to_en


import time

def app_dir():
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", str(Path.home())))
        base, old = root / "Anbarman", root / "Anbarak"
    else:
        base, old = Path.home() / ".anbarman", Path.home() / ".anbarak"
    if not base.exists() and old.exists():
        try:
            shutil.copytree(str(old), str(base))
        except Exception:
            pass
    base.mkdir(parents=True, exist_ok=True)
    return base


SCHEMA = """
CREATE TABLE IF NOT EXISTS categories(
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, parent_id INTEGER);
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER,
    qty INTEGER NOT NULL DEFAULT 0,
    buy_price INTEGER NOT NULL DEFAULT 0,
    buy_date TEXT,
    buy_cur TEXT NOT NULL DEFAULT 'IRT',
    buy_amount REAL NOT NULL DEFAULT 0,
    usd_price REAL NOT NULL DEFAULT 0,
    image TEXT,
    note TEXT,
    best_price INTEGER NOT NULL DEFAULT 0,
    best_site TEXT,
    price_updated TEXT);
CREATE TABLE IF NOT EXISTS prices(
    product_id INTEGER NOT NULL, site TEXT NOT NULL,
    price INTEGER NOT NULL DEFAULT 0, title TEXT, url TEXT, error TEXT,
    fetched_at TEXT, PRIMARY KEY(product_id, site));
CREATE TABLE IF NOT EXISTS purchases(
    id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
    date TEXT NOT NULL, qty INTEGER NOT NULL, unit_price INTEGER NOT NULL, note TEXT);
CREATE TABLE IF NOT EXISTS sales(
    id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, product_name TEXT NOT NULL,
    qty INTEGER NOT NULL, unit_price INTEGER NOT NULL, cost INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL, date TEXT NOT NULL, jy INTEGER, jm INTEGER, jd INTEGER,
    invoice_no INTEGER, created_at TEXT, customer TEXT);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date);
CREATE INDEX IF NOT EXISTS idx_sales_j ON sales(jm, jd);
CREATE INDEX IF NOT EXISTS idx_sales_pid ON sales(product_id, date, id);
CREATE INDEX IF NOT EXISTS idx_purchases_pid ON purchases(product_id);
CREATE TABLE IF NOT EXISTS invoices(
    id INTEGER PRIMARY KEY AUTOINCREMENT, number INTEGER, customer TEXT, date TEXT,
    total INTEGER, discount INTEGER, items_json TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
"""


_BC_SPACE = re.compile(r"[\s\u200c\u200b\u200f\u200e\u00a0]+")


def clean_barcode(code):
    """بارکد = همان متنی که نوشته یا اسکن شده، فقط بدون فاصله. حروف و عدد هر دو مجازند."""
    return _BC_SPACE.sub("", J.to_en(code or ""))


def now_str():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ===== ابزار موقت اندازه گیری سرعت (برای پیدا کردن علت کند بودن جابجایی بین منوها) =====
# هیچ قابلیتی را تغییر نمی دهد؛ فقط زمان هر عملیات را در یک فایل لاگ می نویسد.
_PERF_LOG = None


def _perf_path():
    global _PERF_LOG
    if _PERF_LOG is None:
        _PERF_LOG = str(app_dir() / "perf.log")
    return _PERF_LOG


def perf_log(label, ms, extra=""):
    try:
        with open(_perf_path(), "a", encoding="utf-8") as f:
            f.write(f"{now_str()}  {ms:7.1f} ms   {label}  {extra}\n")
    except Exception:
        pass


class PerfTimer:
    """with PerfTimer('go(2)'): ...   -> مدت اجرای بلوک را در perf.log می نویسد"""
    def __init__(self, label, extra=""):
        self.label, self.extra = label, extra

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        perf_log(self.label, (time.perf_counter() - self.t0) * 1000, self.extra)


class DB:
    def __init__(self, root=None):
        self.root = Path(root) if root else app_dir()
        self.img_dir = self.root / "images"
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "data.db"
        self.con = None
        self.connect()

    def connect(self):
        self.con = sqlite3.connect(str(self.path))
        self.con.row_factory = sqlite3.Row
        self._rc = {}
        self.con.set_trace_callback(self._on_sql)
        try:
            self.con.execute("PRAGMA journal_mode=WAL")
            self.con.execute("PRAGMA synchronous=NORMAL")
            self.con.execute("PRAGMA temp_store=MEMORY")
            self.con.execute("PRAGMA cache_size=-8000")
        except sqlite3.Error:
            pass
        self.con.executescript(SCHEMA)
        category_cols = [r[1] for r in self.con.execute("PRAGMA table_info(categories)")]
        if "parent_id" not in category_cols:
            self.con.execute("ALTER TABLE categories ADD COLUMN parent_id INTEGER")
        cols = [r[1] for r in self.con.execute("PRAGMA table_info(products)")]
        if "buy_cur" not in cols:
            self.con.execute("ALTER TABLE products ADD COLUMN buy_cur TEXT NOT NULL DEFAULT 'IRT'")
        if "buy_amount" not in cols:
            self.con.execute("ALTER TABLE products ADD COLUMN buy_amount REAL NOT NULL DEFAULT 0")
        if "is_service" not in cols:
            self.con.execute("ALTER TABLE products ADD COLUMN is_service INTEGER NOT NULL DEFAULT 0")
        if "auto_price" not in cols:
            self.con.execute("ALTER TABLE products ADD COLUMN auto_price INTEGER NOT NULL DEFAULT 1")
        if "sell_price" not in cols:
            self.con.execute("ALTER TABLE products ADD COLUMN sell_price INTEGER NOT NULL DEFAULT 0")
        if "sell_usd" not in cols:
            self.con.execute("ALTER TABLE products ADD COLUMN sell_usd REAL NOT NULL DEFAULT 0")
        if "sell_cur" not in cols:
            self.con.execute("ALTER TABLE products ADD COLUMN sell_cur TEXT NOT NULL DEFAULT 'USD'")
        icols = [r[1] for r in self.con.execute("PRAGMA table_info(invoices)").fetchall()]
        if "note" not in icols:
            self.con.execute("ALTER TABLE invoices ADD COLUMN note TEXT NOT NULL DEFAULT ''")
        if "barcode" not in cols:
            self.con.execute("ALTER TABLE products ADD COLUMN barcode TEXT NOT NULL DEFAULT ''")
        self.con.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
        sales_cols = [r[1] for r in self.con.execute("PRAGMA table_info(sales)")]
        if "customer" not in sales_cols:
            self.con.execute("ALTER TABLE sales ADD COLUMN customer TEXT NOT NULL DEFAULT ''")
        self.con.commit()

    def _on_sql(self, sql):
        """هر بار داده ها تغییر کنند، نتیجه های ذخیره شده پاک می شوند"""
        try:
            first = sql.lstrip().split(None, 1)[0].upper()
        except Exception:
            return
        if first in ("INSERT", "UPDATE", "DELETE", "REPLACE", "ALTER", "CREATE", "DROP", "VACUUM"):
            self._rc = {}

    def close(self):
        if self.con:
            self.con.close()
            self.con = None

    # ---------- تنظیمات ----------
    def reset_all(self):
        self.close()
        for f in list(self.img_dir.glob("*")):
            try:
                f.unlink()
            except Exception:
                pass
        try:
            self.path.unlink()
        except Exception:
            pass
        self.connect()

    def get_setting(self, key, default=""):
        r = self.con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default

    def set_setting(self, key, value):
        with self.con:
            self.con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value)))

    # ---------- دسته ها ----------
    def categories(self):
        return self.con.execute(
            "SELECT c.id, c.name, c.parent_id, parent.name AS parent_name, "
            "(SELECT COUNT(*) FROM products p WHERE p.category_id=c.id) AS cnt "
            "FROM categories c LEFT JOIN categories parent ON parent.id=c.parent_id "
            "ORDER BY CASE WHEN c.parent_id IS NULL THEN 0 ELSE 1 END, "
            "COALESCE(parent.name, c.name), CASE WHEN c.parent_id IS NULL THEN '' ELSE c.name END, c.name").fetchall()

    def add_category(self, name, parent_id=None):
        name = (name or "").strip()
        if not name:
            return None
        with self.con:
            self.con.execute("INSERT INTO categories(name, parent_id) VALUES(?, ?)", (name, parent_id))
        return self.con.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()["id"]

    def rename_category(self, cid, name):
        with self.con:
            self.con.execute("UPDATE categories SET name=? WHERE id=?", (name.strip(), cid))

    def delete_category(self, cid):
        with self.con:
            # زیردستهها با حذف دسته مادر به دسته مستقل تبدیل میشوند.
            self.con.execute("UPDATE categories SET parent_id=NULL WHERE parent_id=?", (cid,))
            self.con.execute("UPDATE products SET category_id=NULL WHERE category_id=?", (cid,))
            self.con.execute("DELETE FROM categories WHERE id=?", (cid,))

    # ---------- کالاها ----------
    def products(self, search="", cat=None):
        q = ("SELECT p.*, c.name AS cat_name FROM products p "
             "LEFT JOIN categories c ON c.id=p.category_id WHERE 1=1")
        params = []
        if search:
            q += " AND (p.name LIKE ? OR p.barcode LIKE ?)"
            params.extend((f"%{search}%", f"%{search}%"))
        if cat:
            q += " AND p.category_id=?"
            params.append(cat)
        q += " ORDER BY p.id DESC"
        return self.con.execute(q, params).fetchall()

    def product(self, pid):
        return self.con.execute(
            "SELECT p.*, c.name AS cat_name FROM products p "
            "LEFT JOIN categories c ON c.id=p.category_id WHERE p.id=?", (pid,)).fetchone()

    def product_by_barcode(self, code, exclude_pid=None):
        code = clean_barcode(code)
        if not code:
            return None
        r = self.con.execute("SELECT id FROM products WHERE barcode=? AND id<>?",
                             (code, exclude_pid or -1)).fetchone()
        return r["id"] if r else None

    def store_logo(self, src):
        """لوگو با نسبت اصلی خودش (تا ۴۰۰ پیکسل) ذخیره می شود، نه به شکل مربع برش خورده"""
        try:
            from PIL import Image
            im = Image.open(src)
            im.thumbnail((400, 400))
            name = uuid.uuid4().hex + ".png"
            im.convert("RGBA").save(str(self.img_dir / name), "PNG")
            return name
        except Exception:
            return None

    def store_image(self, src):
        if not src:
            return None
        src = Path(src)
        if src.parent == self.img_dir:
            return src.name
        name = uuid.uuid4().hex + ".png"
        if not make_thumb(str(src), str(self.img_dir / name)):
            return None
        return name

    def set_image(self, pid, name):
        with self.con:
            self.con.execute("UPDATE products SET image=? WHERE id=?", (name, pid))

    def image_path(self, name):
        return str(self.img_dir / name) if name else None

    def add_product(self, d):
        with self.con:
            cur = self.con.execute(
                "INSERT INTO products(name,category_id,qty,buy_price,buy_date,buy_cur,buy_amount,image,note) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (d["name"], d.get("category_id"), d["qty"], d["buy_price"], d["buy_date"],
                 d.get("buy_cur", "IRT"), d.get("buy_amount", 0), d.get("image"), d.get("note", "")))
            pid = cur.lastrowid
            self.con.execute("UPDATE products SET is_service=?, sell_price=?, sell_usd=?, sell_cur=? WHERE id=?",
                             (1 if d.get("is_service") else 0, int(d.get("sell_price") or 0),
                              float(d.get("sell_usd") or 0), d.get("sell_cur") or "USD", pid))
            self.con.execute("UPDATE products SET auto_price=? WHERE id=?",
                             (1 if d.get("auto_price", 1) else 0, pid))
            self.con.execute("UPDATE products SET barcode=? WHERE id=?", (clean_barcode(d.get("barcode")), pid))
            if d["qty"] > 0:
                self.con.execute(
                    "INSERT INTO purchases(product_id,date,qty,unit_price,note) VALUES(?,?,?,?,?)",
                    (pid, d["buy_date"], d["qty"], d["buy_price"], "ثبت اولیه"))
        return pid

    def update_product(self, pid, d):
        old = self.product(pid)
        with self.con:
            self.con.execute(
                "UPDATE products SET name=?,category_id=?,qty=?,buy_price=?,buy_date=?,buy_cur=?,buy_amount=?,"
                "image=?,note=? WHERE id=?",
                (d["name"], d.get("category_id"), d["qty"], d["buy_price"], d["buy_date"],
                 d.get("buy_cur", "IRT"), d.get("buy_amount", 0), d.get("image"), d.get("note", ""), pid))
            self.con.execute("UPDATE products SET is_service=?, sell_price=?, sell_usd=?, sell_cur=? WHERE id=?",
                             (1 if d.get("is_service") else 0, int(d.get("sell_price") or 0),
                              float(d.get("sell_usd") or 0), d.get("sell_cur") or "USD", pid))
            self.con.execute("UPDATE products SET auto_price=? WHERE id=?",
                             (1 if d.get("auto_price", 1) else 0, pid))
            self.con.execute("UPDATE products SET barcode=? WHERE id=?", (clean_barcode(d.get("barcode")), pid))
            delta = d["qty"] - old["qty"]
            changed = d["buy_price"] != old["buy_price"] or d["buy_date"] != old["buy_date"]
            if delta > 0 or changed:
                self.con.execute(
                    "INSERT INTO purchases(product_id,date,qty,unit_price,note) VALUES(?,?,?,?,?)",
                    (pid, d["buy_date"], max(delta, 0), d["buy_price"],
                     "خرید جدید" if delta > 0 else "ویرایش قیمت/تاریخ خرید"))

    def delete_product(self, pid):
        with self.con:
            self.con.execute("DELETE FROM prices WHERE product_id=?", (pid,))
            self.con.execute("DELETE FROM purchases WHERE product_id=?", (pid,))
            self.con.execute("DELETE FROM products WHERE id=?", (pid,))

    def count_dollar_products(self):
        r = self.con.execute("SELECT COUNT(*) AS n FROM products WHERE sell_usd>0").fetchone()
        return int(r["n"]) if r else 0

    def sync_sell_prices(self, rates):
        """rates = {"USD": نرخ دلار, "AED": نرخ درهم}؛ قیمت تومانی هر کالا = پایه ارزی × نرخ همان ارز"""
        with self.con:
            for cur, rate in rates.items():
                if rate:
                    self.con.execute("UPDATE products SET sell_price=CAST(ROUND(sell_usd*?) AS INTEGER) "
                                     "WHERE sell_usd>0 AND sell_cur=?", (float(rate), cur))

    def sync_sell_price(self, pid, usd_rate):
        with self.con:
            self.con.execute("UPDATE products SET sell_price=CAST(ROUND(sell_usd*?) AS INTEGER) WHERE id=? AND sell_usd>0",
                             (float(usd_rate), pid))

    def quick_add(self, pid, n=1):
        p = self.product(pid)
        with self.con:
            self.con.execute("UPDATE products SET qty=qty+? WHERE id=?", (n, pid))
            self.con.execute(
                "INSERT INTO purchases(product_id,date,qty,unit_price,note) VALUES(?,?,?,?,?)",
                (pid, dt.date.today().isoformat(), n, p["buy_price"], "افزودن سریع"))

    def quick_sub(self, pid, n=1):
        with self.con:
            self.con.execute("UPDATE products SET qty=MAX(qty-?,0) WHERE id=?", (n, pid))

    def last_sale(self, pid):
        return self.con.execute(
            "SELECT unit_price, date FROM sales WHERE product_id=? ORDER BY date DESC, id DESC LIMIT 1",
            (pid,)).fetchone()

    def last_sales_bulk(self, pids):
        """آخرین فروش چند کالا را فقط با یک پرس وجو می گیرد (به جای یک پرس وجوی جدا برای هر کالا، هر بار که لیست کالاها نمایش داده می شود)."""
        pids = [p for p in dict.fromkeys(pids) if p is not None]
        if not pids:
            return {}
        qmarks = ",".join("?" * len(pids))
        rows = self.con.execute(
            "SELECT product_id, unit_price, date FROM ("
            "  SELECT product_id, unit_price, date, "
            "         ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY date DESC, id DESC) AS rn "
            "  FROM sales WHERE product_id IN (%s)"
            ") WHERE rn = 1" % qmarks, pids).fetchall()
        return {r["product_id"]: r for r in rows}

    # ---------- قیمت ها ----------
    def prices(self, pid):
        return self.con.execute("SELECT * FROM prices WHERE product_id=?", (pid,)).fetchall()

    def save_prices(self, pid, results):
        ts = now_str()
        with self.con:
            for r in results:
                self.con.execute(
                    "INSERT OR REPLACE INTO prices(product_id,site,price,title,url,error,fetched_at) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (pid, r["site"], int(r.get("price") or 0), r.get("title", ""), r.get("url", ""),
                     r.get("error", ""), ts))
        self.compute_best(pid, stamp=ts)

    def compute_best(self, pid, stamp=None):
        rows = self.con.execute(
            "SELECT site, price FROM prices WHERE product_id=? AND price>0 AND site='digikala'", (pid,)).fetchall()
        mode = "max"  # فقط دیجی کالا
        best, site = 0, ""
        if rows:
            if mode == "min":
                r = min(rows, key=lambda x: x["price"])
                best, site = r["price"], r["site"]
            elif mode == "avg":
                best, site = int(sum(x["price"] for x in rows) / len(rows)), "avg"
            else:
                r = max(rows, key=lambda x: x["price"])
                best, site = r["price"], r["site"]
        with self.con:
            if stamp:
                self.con.execute("UPDATE products SET best_price=?, best_site=?, price_updated=? WHERE id=?",
                                 (best, site, stamp, pid))
            else:
                self.con.execute("UPDATE products SET best_price=?, best_site=? WHERE id=?",
                                 (best, site, pid))

    def recompute_all_best(self):
        for r in self.con.execute("SELECT id FROM products").fetchall():
            self.compute_best(r["id"])

    # ---------- خرید/فروش ----------
    def purchases(self, pid):
        return self.con.execute(
            "SELECT * FROM purchases WHERE product_id=? ORDER BY date DESC, id DESC", (pid,)).fetchall()

    def add_sale(self, pid, qty, unit_price, date=None, invoice_no=None, customer="", allow_overstock=False):
        p = self.product(pid)
        if not p:
            raise ValueError("کالا پیدا نشد")
        if not allow_overstock and not p["is_service"] and qty > p["qty"]:
            raise ValueError(f"موجودی «{p['name']}» کافی نیست")
        date = date or dt.date.today()
        jy, jm, jd = J.to_jalali(date)
        with self.con:
            self.con.execute(
                "INSERT INTO sales(product_id,product_name,qty,unit_price,cost,total,date,jy,jm,jd,"
                "invoice_no,created_at,customer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (pid, p["name"], qty, unit_price, p["buy_price"], qty * unit_price, date.isoformat(),
                 jy, jm, jd, invoice_no, now_str(), (customer or "").strip()))
            if not p["is_service"]:
                self.con.execute("UPDATE products SET qty=qty-? WHERE id=?", (qty, pid))

    def sales_between(self, d1, d2):
        return self.con.execute(
            "SELECT * FROM sales WHERE date BETWEEN ? AND ? ORDER BY date DESC, id DESC",
            (d1.isoformat(), d2.isoformat())).fetchall()

    def latest_sales(self, limit=50, search=""):
        q, params = ("SELECT s.*, COALESCE(p.is_service, 0) AS is_service "
                     "FROM sales s LEFT JOIN products p ON p.id=s.product_id"), []
        if search:
            q += " WHERE (s.product_name LIKE ? OR COALESCE(s.customer, '') LIKE ? OR COALESCE(p.barcode, '') LIKE ?)"
            params.extend((f"%{search}%", f"%{search}%", f"%{search}%"))
        q += " ORDER BY s.date DESC, s.id DESC LIMIT ?"
        params.append(limit)
        return self.con.execute(q, params).fetchall()

    def recent_sales(self, n=6):
        return self.con.execute("SELECT * FROM sales ORDER BY id DESC LIMIT ?", (n,)).fetchall()

    def daily_sales(self, d1, d2):
        rows = self.con.execute(
            "SELECT date, SUM(total) t, SUM((unit_price-cost)*qty) pr FROM sales "
            "WHERE date BETWEEN ? AND ? GROUP BY date", (d1.isoformat(), d2.isoformat())).fetchall()
        return {r["date"]: (r["t"] or 0, r["pr"] or 0) for r in rows}

    def daily_purchases(self, d1, d2):
        rows = self.con.execute(
            "SELECT date, SUM(qty*unit_price) t FROM purchases WHERE date BETWEEN ? AND ? "
            "AND qty>0 GROUP BY date", (d1.isoformat(), d2.isoformat())).fetchall()
        return {r["date"]: r["t"] or 0 for r in rows}

    def sales_years(self):
        return [r["jy"] for r in self.con.execute("SELECT DISTINCT jy FROM sales ORDER BY jy DESC")]

    def same_day_history(self, jm, jd):
        return self.con.execute(
            "SELECT jy, SUM(total) t, SUM(qty) q FROM sales WHERE jm=? AND jd=? "
            "GROUP BY jy ORDER BY jy DESC", (jm, jd)).fetchall()

    def same_month_history(self, jm):
        return self.con.execute(
            "SELECT jy, SUM(total) t, SUM(qty) q FROM sales WHERE jm=? GROUP BY jy ORDER BY jy DESC",
            (jm,)).fetchall()

    def totals(self):
        r = self.con.execute(
            "SELECT COALESCE(SUM(qty*buy_price),0) assets, COALESCE(SUM(qty*buy_price),0) cost, "
            "COUNT(*) n, COALESCE(SUM(qty),0) q, "
            "COALESCE(SUM(CASE WHEN best_price=0 THEN 1 ELSE 0 END),0) noprice FROM products").fetchone()
        return dict(r)

    def low_stock(self, limit=2, n=6):
        return self.con.execute(
            "SELECT * FROM products WHERE qty<=? ORDER BY qty ASC, id DESC LIMIT ?", (limit, n)).fetchall()

    # ---------- فاکتور ----------
    def next_invoice_number(self):
        r = self.con.execute("SELECT COALESCE(MAX(number),1000) m FROM invoices").fetchone()
        return r["m"] + 1

    def save_invoice(self, number, customer, date, total, discount, items, note=""):
        with self.con:
            self.con.execute(
                "INSERT INTO invoices(number,customer,date,total,discount,items_json,created_at,note) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (number, customer, date.isoformat(), total, discount,
                 json.dumps(items, ensure_ascii=False), now_str(), note or ""))

    def get_invoices(self):
        return self.con.execute("SELECT * FROM invoices ORDER BY number DESC").fetchall()

    def old_invoice_qty(self, number):
        if not number:
            return {}
        rows = self.con.execute(
            "SELECT product_id, SUM(qty) q FROM sales WHERE invoice_no=? AND product_id IS NOT NULL "
            "GROUP BY product_id", (number,)).fetchall()
        return {r["product_id"]: r["q"] for r in rows}

    def delete_invoice(self, number):
        rows = self.con.execute(
            "SELECT s.product_id, SUM(s.qty) q, p.is_service FROM sales s LEFT JOIN products p ON p.id=s.product_id "
            "WHERE s.invoice_no=? GROUP BY s.product_id", (number,)).fetchall()
        with self.con:
            for r in rows:
                if r["is_service"] is not None and not r["is_service"]:
                    self.con.execute("UPDATE products SET qty=qty+? WHERE id=?", (r["q"], r["product_id"]))
            self.con.execute("DELETE FROM sales WHERE invoice_no=?", (number,))
            self.con.execute("DELETE FROM invoices WHERE number=?", (number,))

    # ---------- پشتیبان ----------
    def export_zip(self, target):
        tmp = Path(tempfile.mkdtemp())
        try:
            snap = tmp / "data.db"
            bak = sqlite3.connect(str(snap))
            self.con.backup(bak)
            bak.close()
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(snap, "data.db")
                for f in self.img_dir.glob("*"):
                    if f.is_file():
                        z.write(f, f"images/{f.name}")
                z.writestr("meta.json", json.dumps({"app": "Anbarak", "created": now_str()}))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def import_zip(self, source):
        with zipfile.ZipFile(source) as z:
            names = z.namelist()
            if "data.db" not in names:
                raise ValueError("این فایل پشتیبان انبارک نیست.")
            self.close()
            if self.path.exists():
                shutil.copy(str(self.path), str(self.path) + ".bak")
            z.extract("data.db", str(self.root))
            for n in names:
                if n.startswith("images/") and not n.endswith("/"):
                    dest = self.img_dir / Path(n).name
                    with z.open(n) as s, open(dest, "wb") as o:
                        shutil.copyfileobj(s, o)
        self.connect()

