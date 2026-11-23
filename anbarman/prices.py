"""دریافت قیمت از دیجی کالا و ترب با جستجوی هوشمند (فقط کتابخانه های خود پایتون)"""
from types import SimpleNamespace
from .jalali import to_en, fa
import re
import json
import time
import socket
import html as htmllib
import urllib.parse
import urllib.request
import urllib.error
from urllib.parse import quote, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7"}
TIMEOUT = 18

SITES = [("digikala", "دیجی کالا")]
SITE_LABEL = dict(SITES)
SITE_LABEL["avg"] = "میانگین سایت ها"


# ------------------------------------------------------------------ شبکه
def _get(url, params=None, headers=None, retries=1):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    h = dict(HEADERS)
    if headers:
        h.update(headers)
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 490, 500, 502, 503, 504) and i < retries:
                time.sleep(1.2 + i)
                continue
            raise
        except Exception as e:  # noqa
            last = e
            if i < retries:
                time.sleep(0.8)
                continue
            raise
    raise last


def _num(v):
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    s = to_en(str(v)).replace(",", "").replace("٬", "")
    s = re.sub(r"[^\d.]", "", s)
    try:
        return int(float(s)) if s else 0
    except ValueError:
        return 0


def _numf(v):
    s = to_en(str(v)).replace(",", "").replace("٬", "")
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def _clean(s):
    return htmllib.unescape(re.sub(r"<[^>]+>", " ", s or "")).replace("\u200c", " ").strip()


# ------------------------------------------------------------------ درک متن: هم معنی ها و برندها
# (هر گروه: اولین مورد شکل استاندارد است)
SYN_GROUPS = [
    ["اسپیکر", "بلندگو", "speaker"],
    ["گوشی", "موبایل", "تلفن همراه", "mobile", "phone", "smartphone"],
    ["ماوس", "موس", "mouse"],
    ["کیبورد", "کیبرد", "صفحه کلید", "keyboard"],
    ["لپتاپ", "لپ تاپ", "laptop", "notebook"],
    ["فلش", "فلش مموری", "فلش درایو", "flash drive"],
    ["هدفون", "هدفن", "headphone", "headphones"],
    ["هدست", "headset"],
    ["شارژر", "charger", "آداپتور"],
    ["کابل", "cable"],
    ["پاوربانک", "پاور بانک", "powerbank", "power bank"],
    ["ساعت هوشمند", "smartwatch", "smart watch"],
    ["مانیتور", "monitor"],
    ["هارد", "هارددیسک", "هارد دیسک", "harddisk"],
    ["رم", "ram", "حافظه رم"],
    ["وبکم", "وب کم", "webcam"],
    ["میکروفون", "میکروفن", "microphone", "mic"],
    ["تبلت", "tablet"],
    ["دوربین", "camera"],
    ["چاپگر", "پرینتر", "printer"],
]
BRANDS = {
    "جی بی ال": "jbl", "جیبیال": "jbl", "جی بی ال": "jbl", "سامسونگ": "samsung", "سامسونج": "samsung",
    "شیائومی": "xiaomi", "شیاومی": "xiaomi", "اپل": "apple", "سونی": "sony", "کینگستون": "kingston",
    "لاجیتک": "logitech", "هواوی": "huawei", "هوآوی": "huawei", "ایسوس": "asus", "ایسر": "acer",
    "لنوو": "lenovo", "اچ پی": "hp", "دل": "dell", "ال جی": "lg", "انکر": "anker", "ریزر": "razer",
    "سن دیسک": "sandisk", "سندیسک": "sandisk", "وسترن دیجیتال": "wd", "سیگیت": "seagate", "بوز": "bose",
    "مارشال": "marshall", "هارمن": "harman", "ردمی": "redmi", "پوکو": "poco", "وان پلاس": "oneplus",
    "ریلمی": "realme", "نوکیا": "nokia", "موتورولا": "motorola", "کریتیو": "creative", "هیسکا": "hiska",
    "ریمکس": "remax", "بیسوس": "baseus", "آنر": "honor", "تی پی لینک": "tplink", "دی لینک": "dlink",
    "پرومیت": "promate", "ایکس ویژن": "xvision", "تسکو": "tsco", "گوگل": "google", "ناب": "nab",
    "هایک ویژن": "hikvision", "دوو": "daewoo", "پاناسونیک": "panasonic", "کانن": "canon", "نیکون": "nikon",
    "ترنسند": "transcend", "پتریوت": "patriot", "ای دیتا": "adata", "ادیتا": "adata", "تیم گروپ": "teamgroup",
    "گیگابایت": "gigabyte_brand", "ام اس آی": "msi", "اینتل": "intel", "ای ام دی": "amd", "انویدیا": "nvidia",
}
STOP = {"مدل", "نسخه", "ورژن", "اصل", "اورجینال", "original", "جدید", "کد", "محصول", "و", "با", "برای", "از",
        "به", "در", "the", "for", "and", "with"}
_UNITS = {"گیگابایت": "gb", "گیگ": "gb", "گیگا": "gb", "gigabyte": "gb", "gig": "gb", "ترابایت": "tb",
          "ترا": "tb", "terabyte": "tb", "مگابایت": "mb", "megabyte": "mb", "وات": "w", "watt": "w",
          "اینچ": "inch", "مگاپیکسل": "mp"}


def _norm(s):
    s = to_en(s).lower()
    for a, b in (("ي", "ی"), ("ك", "ک"), ("ۀ", "ه"), ("ة", "ه"), (" ", " "), ("\u200c", " "), ("‍", ""),
                 ("-", " "), ("_", " "), ("/", " "), ("|", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


_PHRASES = []   # (عبارت نرمال شده، شکل استاندارد) از بلندترین به کوتاه ترین


def _build_phrases():
    items = []
    for g in SYN_GROUPS:
        for w in g:
            items.append((_norm(w), _norm(g[0]).replace(" ", "")))
    for w, c in BRANDS.items():
        items.append((_norm(w), c))
    items.sort(key=lambda x: -len(x[0]))
    _PHRASES[:] = items


def canon_text(s):
    """متن را نرمال می کند و هم معنی ها/برندهای فارسی را به شکل استاندارد (لاتین/ثابت) می برد."""
    if not _PHRASES:
        _build_phrases()
    s = " " + _norm(s) + " "
    for ph, c in _PHRASES:
        if ph in s:
            s = re.sub(r"(?<=\s)" + re.escape(ph) + r"(?=\s)", " " + c + " ", s)
    return s.strip()


def tokens(s):
    toks = re.findall(r"\d+(?:\.\d+)?|[a-z]+|[\u0600-\u06FF]+", canon_text(s))
    out = []
    for t in toks:
        t = _UNITS.get(t, t)
        if t not in STOP:
            out.append(t)
    return out


def _split(toks):
    nums = {t for t in toks if t[0].isdigit()}
    latin = {t for t in toks if t[0].isascii() and t[0].isalpha()}
    fa_ = {t for t in toks if not t[0].isascii()}
    return nums, latin, fa_


def match_extra(query, title):
    """None اگر عنوان همان کالای دقیق نیست؛ وگرنه تعداد کلمات اضافی (هرچه کمتر، شبیه تر).
    همه عددها (مثل 120) و کلمات لاتین/برند (مثل JBL) باید دقیقا در عنوان باشند؛ هم معنی ها
    (بلندگو=اسپیکر، جی بی ال=JBL) یکسان حساب می شوند. پس «JBL 130» به جای «JBL 120» پذیرفته نمی شود."""
    q, t = tokens(query), tokens(title)
    qn, ql, qf = _split(q)
    tn, tl, tf = _split(t)
    if not (qn | ql | qf):
        return None
    if not qn <= tn or not ql <= tl:
        return None
    if qf and len(qf & tf) < max(1, (len(qf) + 1) // 2):
        return None
    return len(set(t) - set(q))


def relevance(query, title):
    q, t = set(tokens(query)), set(tokens(title))
    return len(q & t) / len(q) if q else 0.0


def query_variants(q):
    """چند عبارت جستجو برای یک کالا: خود متن، هم معنی ها، و فقط برند+مدل."""
    q = " ".join(q.split())
    out = [q]
    nq = _norm(q)
    for g in SYN_GROUPS:
        for w in g:
            wn = _norm(w)
            if re.search(r"(?<!\S)" + re.escape(wn) + r"(?!\S)", nq):
                for alt in g[:2]:
                    if _norm(alt) != wn:
                        out.append(re.sub(r"(?<!\S)" + re.escape(wn) + r"(?!\S)", alt, nq))
                break
    toks = tokens(q)
    core = [t for t in toks if t[0].isascii()]
    if core and len(core) < len(toks):
        out.append(" ".join(core))
    seen, res = set(), []
    for v in out:
        k = _norm(v)
        if k and k not in seen:
            seen.add(k)
            res.append(v)
    return res[:4]


def pick_best(query, items):
    cands = []
    for i in items:
        if i.get("price", 0) <= 0:
            continue
        e = match_extra(query, i["title"])
        if e is not None:
            cands.append((e, i["price"], i))
    if not cands:
        return None
    cands.sort(key=lambda c: (c[0], c[1]))
    return cands[0][2]


def fuzzy_rel(query, title):
    """شباهت نرم: هر کلمه جستجو کافی است داخل نام (بدون فاصله) باشد، مثلا JBL داخل JBLPartiBox"""
    qt = [t for t in tokens(query) if t]
    if not qt:
        return 0.0
    tn = re.sub(r"\s+", "", _norm(title))
    hits = sum(1 for t in qt if re.sub(r"\s+", "", _norm(t)) in tn)
    return hits / len(qt)


def nearest(query, items):
    """نزدیک ترین کالا (نه دقیق) فقط برای نمایش به عنوان راهنما."""
    scored = [(fuzzy_rel(query, i["title"]), i) for i in items if i.get("price", 0) > 0]
    scored = [s for s in scored if s[0] >= 0.5]
    if not scored:
        return None
    return max(scored, key=lambda s: s[0])[1]


# ------------------------------------------------------------------ استخراج عمومی (JSON داخل صفحه)
_TITLE_KEYS = ("title_fa", "title", "name", "name1", "product_name", "title_en", "name2")
_PRICE_KEYS = ("selling_price", "final_price", "sale_price", "price", "min_price", "lowPrice")


def _walk(obj, out, depth=0):
    if depth > 25:
        return
    if isinstance(obj, dict):
        t1 = [str(obj[k]) for k in _TITLE_KEYS if isinstance(obj.get(k), str) and len(obj[k]) > 3]
        price = next((_num(obj[k]) for k in _PRICE_KEYS
                      if k in obj and isinstance(obj[k], (int, float, str)) and _num(obj[k]) >= 1000), 0)
        if t1 and price:
            url = obj.get("web_client_absolute_url") or obj.get("url") or obj.get("link") or ""
            img = obj.get("image_url") or obj.get("image") or ""
            out.append({"title": " | ".join(t1), "price": price, "url": url if isinstance(url, str) else "",
                        "img": img if isinstance(img, str) and img.startswith("http") else ""})
        for v in obj.values():
            _walk(v, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, out, depth + 1)


def extract_items(page_html, base_url):
    items = []
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page_html, re.S)
    if m:
        try:
            _walk(json.loads(m.group(1)), items)
        except Exception:
            pass
    for it in items:
        it["url"] = urljoin(base_url, it["url"]) if it["url"] else base_url
    return items


# ------------------------------------------------------------------ دیجی کالا
DK_H = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.digikala.com",
    "Referer": "https://www.digikala.com/",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8",
    "User-Agent": UA,
}


def _dk_extract_price(p):
    """قیمت فروش را از ساختارهای مختلف محصول دیجی کالا می‌گیرد (ریال)"""
    if not isinstance(p, dict):
        return 0
    # default_variant.price.selling_price
    dv = p.get("default_variant") or {}
    price = ((dv.get("price") or {}).get("selling_price")
             or (dv.get("price") or {}).get("rrp_price")
             or 0)
    if not price:
        pr = p.get("price") or {}
        if isinstance(pr, dict):
            price = pr.get("selling_price") or pr.get("rrp_price") or 0
        else:
            price = pr or 0
    if not price:
        # ساختار جدید discovery
        price = (p.get("selling_price") or p.get("rrp_price")
                 or (p.get("price") if isinstance(p.get("price"), (int, float)) else 0))
    return _num(price)


def _dk_extract_img(p):
    try:
        main = (p.get("images") or {}).get("main") or {}
        urls = main.get("url") or main.get("urls") or []
        if isinstance(urls, list) and urls:
            return urls[0] if isinstance(urls[0], str) else ""
        if isinstance(main.get("url"), str):
            return main["url"]
    except Exception:
        pass
    for k in ("image_url", "image", "thumbnail", "photo"):
        v = p.get(k)
        if isinstance(v, str) and v.startswith("http"):
            return v
        if isinstance(v, dict):
            u = v.get("url") or v.get("src")
            if isinstance(u, str) and u.startswith("http"):
                return u
    return ""


def _dk_products_to_items(products):
    out = []
    for p in products or []:
        if not isinstance(p, dict):
            continue
        # گاهی خود widget داده را داخل data دارد
        if "data" in p and isinstance(p["data"], dict) and ("title_fa" in p["data"] or "id" in p["data"]):
            p = p["data"]
        price = _dk_extract_price(p)
        img = _dk_extract_img(p)
        title = (p.get("title_fa") or p.get("title") or p.get("name") or "")
        en = p.get("title_en") or ""
        if en:
            title = (title + " | " + en).strip(" |")
        pid = p.get("id") or p.get("product_id")
        url = p.get("url") or p.get("web_client_absolute_url") or ""
        if not url and pid:
            url = f"https://www.digikala.com/product/dkp-{pid}/"
        if not price and not img:
            continue
        # قیمت API به ریال است → به تومان
        out.append({
            "title": title,
            "price": int(price) // 10 if price else 0,
            "url": url if isinstance(url, str) else f"https://www.digikala.com/product/dkp-{pid}/",
            "img": img or "",
        })
    return out


def _dk_parse_discovery(js):
    """پاسخ جدید discovery/api/v2/search را به لیست محصول تبدیل می‌کند"""
    products = []
    data = js.get("data") or js
    # مسیر اصلی: widgets → vertical_product_listing → widgets از نوع product
    widgets = data.get("widgets") or []
    for w in widgets:
        if not isinstance(w, dict):
            continue
        wtype = w.get("type") or ""
        wdata = w.get("data") or w
        if wtype in ("vertical_product_listing", "product_list", "products"):
            inner = wdata.get("widgets") or wdata.get("products") or wdata.get("items") or []
            for item in inner:
                if isinstance(item, dict):
                    if item.get("type") == "product":
                        products.append(item.get("data") or item)
                    else:
                        products.append(item)
        elif wtype == "product":
            products.append(wdata)
    # مسیرهای قدیمی‌تر / جایگزین
    if not products:
        products = (data.get("products")
                    or data.get("items")
                    or (data.get("search") or {}).get("products")
                    or [])
    return _dk_products_to_items(products)


def _dk_api(q):
    """مسیرهای JSON دیجی کالا — اول discovery جدید، بعد endpointهای قدیمی"""
    last = None
    # ۱) endpoint فعلی (از اواخر ۲۰۲۵ / آبان ۱۴۰۵)
    for path in (
        "https://api.digikala.com/discovery/api/v2/search",
        "https://api.digikala.com/discovery/api/v1/search",
    ):
        try:
            raw = _get(path, {"q": q, "page": 1}, DK_H)
            js = json.loads(raw)
            # بعضی پاسخ‌ها status:404 داخل JSON دارند حتی با HTTP 200
            if isinstance(js, dict) and js.get("status") in (404, "404"):
                last = urllib.error.HTTPError(path, 404, "Not Found", {}, None)
                continue
            items = _dk_parse_discovery(js)
            if items:
                return items
        except Exception as e:  # noqa
            last = e
    # ۲) endpointهای قدیمی (برای سازگاری اگر دوباره فعال شوند)
    for base in ("https://api.digikala.com/v1/search/", "https://api.digikala.com/v2/search/"):
        try:
            js = json.loads(_get(base, {"q": q}, DK_H))
            items = _dk_products_to_items((js.get("data") or {}).get("products"))
            if items:
                return items
        except Exception as e:  # noqa
            last = e
    if last:
        raise last
    return []


def _dk_html(q):
    """مسیر پشتیبان: خود صفحه جستجوی دیجی کالا (داده JSON داخل صفحه)"""
    page = _get("https://www.digikala.com/search/", {"q": q},
                {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                 "Referer": "https://www.digikala.com/", "User-Agent": UA})
    items = extract_items(page, "https://www.digikala.com/")
    for it in items:
        # اگر قیمت هنوز ریال باشد
        pr = int(it.get("price") or 0)
        if pr > 100_000_000:  # احتمالاً ریال است
            it["price"] = pr // 10
        else:
            it["price"] = pr
    return [it for it in items if it.get("title")]


def search_digikala(q):
    items, err = [], None
    try:
        items = _dk_api(q)
    except Exception as e:  # noqa
        err = e
    if not items:
        try:
            items = _dk_html(q)
        except Exception as e:  # noqa
            err = err or e
    if not items and err:
        raise err
    return [it for it in items if it.get("price")]


# ------------------------------------------------------------------ ترب (چند مسیر پشتیبان)
TOROB_H = {"Accept": "application/json, text/plain, */*", "Origin": "https://torob.com",
           "Referer": "https://torob.com/", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
           "Sec-Fetch-Site": "same-site"}


def _torob_parse(js):
    out = []
    for it in js.get("results") or []:
        price = _num(it.get("price"))
        if not price:
            continue
        url = it.get("web_client_absolute_url") or ("https://torob.com/p/" + str(it.get("random_key", "")))
        if url.startswith("/"):
            url = "https://torob.com" + url
        out.append({"title": (it.get("name1") or "") + " | " + (it.get("name2") or ""), "price": price,
                    "url": url, "img": it.get("image_url") or ""})
    return out


def search_torob(q):
    errs = []
    base = {"page": 0, "sort": "popularity", "size": 24, "query": q, "q": q, "source": "next"}
    for extra in ({"discover_method": "user"}, {}):
        try:
            out = _torob_parse(json.loads(_get("https://api.torob.com/v4/base-product/search/",
                                               dict(base, **extra), TOROB_H)))
            if out:
                return out
        except Exception as e:  # noqa
            errs.append(e)
    try:  # مسیر پشتیبان: صفحه جستجوی خود سایت
        page = _get("https://torob.com/search/", {"query": q},
                    {"Accept": "text/html,application/xhtml+xml", "Referer": "https://torob.com/"})
        out = extract_items(page, "https://torob.com/")
        if out:
            return out
    except Exception as e:  # noqa
        errs.append(e)
    if errs:
        raise errs[0]
    return []


SEARCHERS = {"digikala": search_digikala, "torob": search_torob}


def _err_text(e, site=""):
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 490:
            return "ترب درخواست را رد کرد (۴۹۰)؛ چند دقیقه بعد دوباره تلاش کنید"
        return f"سایت پاسخ نداد (کد {e.code})"
    if isinstance(e, (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError)):
        return "عدم دسترسی به سایت (اینترنت/فیلتر)"
    return str(e)[:100]


def _run_site(key, query):
    allitems, last_err = [], None
    try:
        for v in query_variants(query):
            try:
                items = SEARCHERS[key](v)
            except Exception as e:  # noqa
                last_err = e
                continue
            allitems.extend(items)
            best = pick_best(query, allitems)
            if best:
                return {"site": key, "price": best["price"], "title": best["title"], "url": best["url"],
                        "img": best.get("img", ""), "error": ""}
        if not allitems and last_err:
            raise last_err
        near = nearest(query, allitems)
        if near:
            # مدل دقیق نبود: قیمت و لینک نزدیک ترین محصول ثبت می شود
            return {"site": key, "price": near["price"], "title": near["title"], "url": near["url"],
                    "img": near.get("img", ""), "error": ""}
        loose = [i for i in allitems if i.get("img") and relevance(query, i["title"]) >= 0.6]
        loose.sort(key=lambda i: -relevance(query, i["title"]))
        msg = "همین مدل دقیق پیدا نشد" if allitems else "نتیجه ای پیدا نشد"
        if near:
            msg += f" — نزدیک ترین: {near['title'].split(' | ')[0][:50]} ({_fmt(near['price'])} تومان)"
        return {"site": key, "price": 0, "title": "", "url": "", "img": loose[0]["img"] if loose else "",
                "error": msg}
    except Exception as e:  # noqa
        return {"site": key, "price": 0, "title": "", "url": "", "img": "", "error": _err_text(e, key)}


def _fmt(n):
    return f"{int(n):,}"


def fetch_all(query):
    keys = [k for k, _ in SITES]
    results = {}
    with ThreadPoolExecutor(max_workers=len(keys)) as ex:
        futs = {ex.submit(_run_site, k, query): k for k in keys}
        for f in as_completed(futs):
            results[futs[f]] = f.result()
    return [results[k] for k in keys]


def fetch_digikala_image(query, strict=False):
    """فقط تصویر محصول را از نتایج دیجی کالا پیدا می کند؛ قیمت/جزئیات ذخیره نمی شود."""
    try:
        items = []
        try:
            items = [it for it in _dk_api(query) if it.get("img")]
        except Exception:  # noqa
            pass
        if not items:
            items = [it for it in _dk_html(query) if it.get("img")]
        exact = [x for x in items if match_extra(query, x["title"]) is not None]
        if exact:
            exact.sort(key=lambda x: match_extra(query, x["title"]))
            return exact[0].get("img")
        scored = [(relevance(query, item["title"]), item) for item in items]
        scored = [pair for pair in scored if pair[0] >= 0.5]
        near = max(scored, key=lambda pair: pair[0])[1] if scored else None
        return near.get("img") if near else ""
    except Exception:
        if strict:
            raise
        return ""


# ------------------------------------------------------------------ نرخ ارز (tgju)
RATE_KEYS = {"USD": "price_dollar_rl", "AED": "price_aed", "GOLD18": "geram18"}


def fetch_rates():
    """نرخ دلار و درهم از tgju (به تومان)"""
    out = {}
    try:
        cur = json.loads(_get("https://call3.tgju.org/ajax.json")).get("current", {})
        for c, k in RATE_KEYS.items():
            v = _numf((cur.get(k) or {}).get("p"))
            if v > 0:
                out[c] = v / 10
    except Exception:
        pass
    for c, k in RATE_KEYS.items():
        if c in out:
            continue
        try:
            h = _get(f"https://www.tgju.org/profile/{k}")
            m = re.search(r'data-col="info\.last_trade\.PDrCotVal"[^>]*>\s*([\d,٬.]+)', h)
            v = _numf(m.group(1)) if m else 0
            if v <= 0:
                i = h.find(k)
                m = re.search(r">\s*([\d,]{3,}(?:\.\d+)?)\s*<", h[i:i + 1500]) if i >= 0 else None
                v = _numf(m.group(1)) if m else 0
            if v > 0:
                out[c] = v / 10
        except Exception:
            pass
    if not out:
        try:
            h = _get("https://www.tgju.org/")
            for c, k in RATE_KEYS.items():
                i = h.find(k)
                m = re.search(r">\s*([\d,]{3,})\s*<", h[i:i + 1200]) if i >= 0 else None
                if m and _numf(m.group(1)) > 0:
                    out[c] = _numf(m.group(1)) / 10
        except Exception:
            pass
    if not out:
        raise RuntimeError("نرخ ارز دریافت نشد")
    return out


def download_file(url, path):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)

P = SimpleNamespace(SITES=SITES, SITE_LABEL=SITE_LABEL, fetch_all=fetch_all, fetch_rates=fetch_rates, download_file=download_file)
