# -*- coding: utf-8 -*-
r"""dang_nhap.py - AUTO-LOGIN: dang nhap site/san tu dong qua Chrome CDP.
Dung kho credential config/tai_khoan.json (luu cục bộ tren may cua chu):
  { "ten_site": {"email": "...", "mat_khau": "...", "url_login": "https://..."} }
Chay:
  python dang_nhap.py --site mql5          : dang nhap bang credential luu san
  python dang_nhap.py --test-detect <url>  : chi kiem tra form (khong submit)
"""
import sys, json, time, pathlib, base64
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(__file__).parent
CDP = "http://127.0.0.1:9222"
KHO = LAB / "config" / "tai_khoan.json"

def _doc_kho():
    if KHO.exists():
        try:
            j = json.loads(KHO.read_text(encoding="utf-8-sig"))
            for k, v in j.items():
                if isinstance(v, dict):
                    if v.get("_em"): v["email"] = base64.b64decode(v["_em"]).decode()
                    if v.get("_mk"): v["mat_khau"] = base64.b64decode(v["_mk"]).decode()
            return j
        except Exception:
            pass
    return {}

def _ma_hoa(s):
    return base64.b64encode(s.encode()).decode()

def phat_hien_form(page):
    """Tra (email_sel, pass_sel, submit_sel, tentative) hoac None."""
    em = None; pw = None; sub = None
    for inp in page.query_selector_all("input"):
        t = (inp.get_attribute("type") or "").lower()
        nm = (inp.get_attribute("name") or "").lower()
        ac = (inp.get_attribute("autocomplete") or "").lower()
        aria = (inp.get_attribute("aria-label") or "").lower()
        if t in ("email", "text", "tel") and (not em):
            if any(k in (nm+ac+aria) for k in ["user", "login", "email", "username", "phone", "account"]) or t == "email":
                em = inp
        elif t == "password" and not pw:
            pw = inp
    if not em or not pw:
        return None
    # nut submit
    for b in page.query_selector_all("button, [type=submit]"):
        try:
            bt = (b.inner_text() or "").lower()
        except Exception:
            bt = ""
        if ("sign in" in bt or "log in" in bt or "login" in bt or "đăng nhập" in bt
                or b.get_attribute("type") == "submit"):
            sub = b; break
    return em, pw, sub

def dang_nhap(url, email, mat_khau, cho=2500):
    p = sync_playwright().start()
    b = p.chromium.connect_over_cdp(CDP)
    try:
        page = b.contexts[0].pages[0]
        page.bring_to_front()
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        f = phat_hien_form(page)
        if not f:
            return {"trang_thai": "khong_phat_hien_form", "url": page.url[:50]}
        em, pw, sub = f
        em.click(); em.fill(email)
        pw.click(); pw.fill(mat_khau)
        if sub:
            sub.click()
        else:
            page.keyboard.press("Enter")
        page.wait_for_timeout(cho)
        he = (page.evaluate("document.body.innerText") or "")[:80]
        return {"trang_thai": "da_submit", "url": page.url[:50], "text": he.replace(chr(10)," ")}
    finally:
        b.close(); p.stop()

def main():
    if "--test-detect" in sys.argv:
        url = sys.argv[sys.argv.index("--test-detect")+1]
        test_detect(url) if False else None
        _test(url)
        return
    kho = _doc_kho()
    if "--site" in sys.argv:
        sname = sys.argv[sys.argv.index("--site")+1]
        v = kho.get(sname)
        if not v:
            print(f"KHONG co credential cho '{sname}' trong {KHO}")
            return
        print(dang_nhap(v.get("url_login", ""), v["email"], v["mat_khau"]))
        return
    print("dung: --site <ten> | --test-detect <url>")
    print("Kho credential:", KHO)


def _test(url):
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    b = p.chromium.connect_over_cdp(CDP)
    try:
        page = b.contexts[0].pages[0]
        page.bring_to_front()
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        f = phat_hien_form(page)
        print("Phat hien form:", "CO (email+password+submit)" if f else "KHONG")
        if f:
            print("  submit text:", (f[2].inner_text() if f[2] else "Enter"))
    finally:
        b.close()
        p.stop()


if __name__ == "__main__":
    main()
