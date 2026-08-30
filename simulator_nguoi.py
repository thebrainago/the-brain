# -*- coding: utf-8 -*-
r"""simulator_nguoi.py - BO MO PHONG NGUOI DUNG TREN WEB.
Dung cho trang chong AI co (Anubis, Cloudflare, bot-block...). Gia lap:
  - chuot: di chuyen theo duong Bezier + muy jitter, nhanh/cham tuy y.
  - cuon: tung doan nho, toc do + nghi ngau nhien.
  - go phim: do tre ngau nhien giua cac ky tu.
  - thoi gian: nghi "suy nghi" ngau nhien truoc khi click.
  - Profile (user-data-dir) de dung phien da dang nhap (forum/reddit/discord).
Chay (python co playwright - AppData\Local\Python\bin\python.exe):
  python simulator_nguoi.py <url> [--can-chua a,b] [--scroll 3] [--anh reports/s.png]
"""
import sys, time, random, re

random.seed()

def _bezier(t, x0, y0, x1, y1, x2, y2, x3, y3):
    u = 1 - t
    bx = u**3*x0 + 3*u*u*t*x1 + 3*u*t*t*x2 + t**3*x3
    by = u**3*y0 + 3*u*u*t*y1 + 3*u*t*t*y2 + t**3*y3
    return bx, by

def _nhay_chuot(page, x, y, buoc=25):
    """Di chuyen chuot tu vi tri hien tai den (x,y) theo duong cong + jitter."""
    try:
        khoi = page.mouse.position() or (400, 300)
    except Exception:
        khoi = (400, 300)
    kx, ky = khoi
    # diem dieu khien ngau nhien
    cx = (kx + x) / 2 + random.uniform(-60, 60)
    cy = (ky + y) / 2 + random.uniform(-60, 60)
    for i in range(1, buoc + 1):
        t = i / buoc
        mx, my = _bezier(t, kx, ky, cx, cy, x, y, x, y)
        mx += random.uniform(-1.2, 1.2)
        my += random.uniform(-1.2, 1.2)
        page.mouse.move(mx, my)
        time.sleep(random.uniform(0.004, 0.014))

def _cuon_nguoi(page, so_lan=3):
    for _ in range(so_lan):
        page.mouse.wheel(0, random.randint(300, 900))
        time.sleep(random.uniform(0.4, 1.4))

def _go_phim(page, text):
    for ch in text:
        page.keyboard.type(ch)
        time.sleep(random.uniform(0.03, 0.11))

def _click_nguoi(page, selector):
    el = page.query_selector(selector)
    if not el:
        raise RuntimeError(f"khong thay {selector}")
    box = el.bounding_box()
    if not box:
        raise RuntimeError(f"khong co box {selector}")
    _nhay_chuot(page, box["x"] + box["width"]/2, box["y"] + box["height"]/2)
    time.sleep(random.uniform(0.3, 0.9))
    el.click()

def mo_va_doc(url, can_chua=(), scroll=3, profile=None, toi_thieu=200):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        args = ["--disable-blink-features=AutomationControlled"]
        if profile:
            b = p.chromium.launch_persistent_context(profile, headless=False,
                                                     args=args, viewport={"width":1440,"height":900})
            page = b.pages[0] if b.pages else b.new_page()
        else:
            b = p.chromium.launch(headless=True, args=args)
            ctx = b.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                locale="en-US", timezone_id="Asia/Ho_Chi_Minh",
                viewport={"width":1440,"height":900})
            page = ctx.new_page()
        try:
            # an dau hieu automation
            page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
            page.goto(url, timeout=40000)
            time.sleep(random.uniform(1.2, 2.5))
            _nhay_chuot(page, random.randint(200, 500), random.randint(150, 400))
            _cuon_nguoi(page, scroll)
            time.sleep(random.uniform(0.5, 1.2))
            txt = page.evaluate("document.body.innerText")
            txt = re.sub(r"\s+", " ", txt)
            ok = len(txt) >= toi_thieu and all(m in txt for m in can_chua)
            return txt, ok, len(txt)
        finally:
            try: b.close()
            except Exception: pass

if __name__ == "__main__":
    url = sys.argv[1]
    cc = sys.argv[sys.argv.index("--can-chua")+1].split(",") if "--can-chua" in sys.argv else []
    sc = int(sys.argv[sys.argv.index("--scroll")+1]) if "--scroll" in sys.argv else 3
    t, ok, n = mo_va_doc(url, can_chua=cc, scroll=sc)
    print(f"OK={ok} LEN={n}")
    if t:
        print(t[:700])


