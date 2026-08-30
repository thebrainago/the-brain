# -*- coding: utf-8 -*-
r"""doc_otp_gmail.py - Doc MA OTP/code tu Gmail (web CDP, da dang nhap).
Khong can app password: dung phiên Gmail dang mo trong Chrome CDP.
Chay:  python doc_otp_gmail.py --gui <sender> --tu-khoa <kw>   (tim email moi nhat + trich ma)
"""
import sys, re, time, pathlib, urllib.parse
from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"

def _tim_ma_text(text):
    ma = set()
    for m in re.finditer(r'(?<![A-Za-z0-9])(\d{4,8})(?![A-Za-z0-9])', text):
        ma.add(m.group(1))
    # uu tien 6 chu so (OTP pho bien)
    for m in sorted(ma, key=lambda x: (len(x) != 6, -len(x))):
        return m
    return None

def doc_moi_nhat(nguoi_gui="", tu_khoa="", max_doi=35):
    q = " ".join(x for x in [("from:"+nguoi_gui) if nguoi_gui else "", tu_khoa] if x)
    p = sync_playwright().start()
    b = p.chromium.connect_over_cdp(CDP)
    try:
        page = b.contexts[0].pages[0]
        page.bring_to_front()
        page.goto("https://mail.google.com/mail/u/0/#search/" + urllib.parse.quote(q),
                  timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        # tim hang email dau tien va click
        rows = [r for r in page.query_selector_all("table tbody tr")
                if r.query_selector("td")]
        if not rows:
            return {"trang_thai": "khong_thay_email", "query": q}
        rows[0].click()
        page.wait_for_timeout(3000)
        body = ""
        for sel in ["div.a3s", "div[role=main]", "div[dir=ltr] div[dir=ltr]"]:
            try:
                t = page.query_selector(sel)
                if t:
                    body = (t.inner_text() or "")
                    if len(body) > 20:
                        break
            except Exception:
                continue
        ma = _tim_ma_text(body)
        links = []
        for a in page.query_selector_all("div.a3s a[href], div[role=main] a[href]"):
            try:
                h = a.get_attribute("href") or ""
                if h.startswith("http") and "mail.google.com" not in h:
                    links.append(h)
            except Exception:
                continue
        return {"trang_thai": "ok", "ma": ma, "links": links[:5], "query": q,
                "text": body[:200].replace("\n", " ")}
    finally:
        b.close(); p.stop()

if __name__ == "__main__":
    import json
    gui = sys.argv[sys.argv.index("--gui")+1] if "--gui" in sys.argv else ""
    kw = sys.argv[sys.argv.index("--tu-khoa")+1] if "--tu-khoa" in sys.argv else ""
    print(json.dumps(doc_moi_nhat(gui, kw), ensure_ascii=False, indent=2))
