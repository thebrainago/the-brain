# -*- coding: utf-8 -*-
r"""tu_dang_ky.py - QUY TRINH TAO TAI KHOAN TU DONG de lay du lieu.
Dang ky web/san cung cap du lieu: dien form -> submit -> doc ma/link tu Gmail
(IMAP, doc_email) -> xac minh -> ghi nhan.
Registry: config/mo_them_tai_khoan.json (danh sach provider can mo).
Chay:  python tu_dang_ky.py --dang-ky coingecko
       python tu_dang_ky.py --chay-het
"""
import sys, time, json, pathlib, re
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(__file__).parent
sys.path.insert(0, str(LAB))
CDP = "http://127.0.0.1:9222"
REG = LAB / "config" / "mo_them_tai_khoan.json"
KQ = LAB / "reports" / "dang_ky_log.json"
import doc_email, dang_nhap

def _doc_reg():
    if REG.exists():
        try:
            return json.loads(REG.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {"email": "", "mat_khau": "", "sites": []}

def _ghi_kq(x):
    lst = []
    if KQ.exists():
        try:
            lst = json.loads(KQ.read_text(encoding="utf-8-sig"))
        except Exception:
            lst = []
    lst.append(x)
    KQ.write_text(json.dumps(lst, ensure_ascii=False, indent=1), encoding="utf-8")

def _phat_hien_dang_ky(page):
    """Tra (ten, email, mk, submit) hoac None."""
    nm = None; em = None; pw = None; sub = None
    for inp in page.query_selector_all("input"):
        t = (inp.get_attribute("type") or "").lower()
        n = (inp.get_attribute("name") or "").lower()
        au = ((inp.get_attribute("autocomplete") or "").lower() + (inp.get_attribute("aria-label") or "").lower())
        if t == "password" and not pw:
            pw = inp
        elif t in ("email",) and not em:
            em = inp
        elif t in ("text",) and not nm and any(k in n for k in ["name", "first", "last", "full"]):
            nm = inp
    if not em or not pw:
        return None
    for b in page.query_selector_all("button, [type=submit]"):
        try:
            bt = (b.inner_text() or "").lower()
        except Exception:
            bt = ""
        if any(k in bt for k in ["register", "sign up", "create", "đăng ký", "signup", "get started"]) or b.get_attribute("type") == "submit":
            sub = b; break
    return nm, em, pw, sub

def dang_ky_site(site):
    """site: {ten, url, (tu kien ten), email, mat_khau}."""
    p = sync_playwright().start()
    b = p.chromium.connect_over_cdp(CDP)
    try:
        page = b.contexts[0].pages[0]
        page.bring_to_front()
        page.goto(site["url"], timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        # bo banner cookie/consent neu co
        for t in ["Accept all", "Accept", "Đồng ý", "I agree", "OK", "Got it"]:
            try:
                el = page.query_selector(f"button:has-text('{t}')")
                if el and el.is_visible():
                    el.click(); break
            except Exception:
                pass
        page.wait_for_timeout(1500)
        f = _phat_hien_dang_ky(page)
        if not f:
            return {"site": site["ten"], "trang_thai": "khong_phat_hien_form"}
        nm, em, pw, sub = f
        def dien(el, gia_tri):
            try:
                el.scroll_into_view_if_needed(); el.click(); el.fill(gia_tri); return True
            except Exception:
                return False
        dien(nm, site.get("ho_ten", "Vanh"))
        ok1 = dien(em, site["email"]); ok2 = dien(pw, site["mat_khau"])
        if not (ok1 and ok2):
            return {"site": site["ten"], "trang_thai": "form_khong_dien_duoc", "em": ok1, "pw": ok2}
        if sub:
            try: sub.scroll_into_view_if_needed(); sub.click()
            except Exception: page.keyboard.press("Enter")
        else: page.keyboard.press("Enter")
        page.wait_for_timeout(4000)
        # cho email xac minh toi ~60s
        for _ in range(12):
            time.sleep(5)
            try:
                import imaplib
                with imaplib.IMAP4_SSL("imap.gmail.com", 993) as m:
                    m.login(site["email"], _app_pw())
                    m.select("INBOX")
                    typ, data = m.search(None, f'FROM "{site.get("sender_gui","")}" OR SUBJECT "{site.get("tu_khoa_email","")}"')
                    if data[0]: break
            except Exception:
                pass
        return {"site": site["ten"], "trang_thai": "form_da_submit", "url": page.url[:50]}
    finally:
        b.close(); p.stop()

def _app_pw():
    import json
    c = json.loads((LAB/"config"/"email_cong_tac.json").read_text(encoding="utf-8-sig"))
    return c["app_password"]

def main():
    reg = _doc_reg()
    if "--dang-ky" in sys.argv:
        ten = sys.argv[sys.argv.index("--dang-ky")+1]
        site = next((s for s in reg.get("sites", []) if s["ten"] == ten), None)
        if not site:
            print(f"KHONG tim thay '{ten}' trong {REG}"); return
        print(dang_ky_site({**site, "email": site.get("email") or reg["email"],
                            "mat_khau": site.get("mat_khau") or reg["mat_khau"]}))
        return
    print("dung: --dang-ky <ten> | sites trong registry:")
    for s in reg.get("sites", []):
        print("  -", s.get("ten"), s.get("url"))

if __name__ == "__main__":
    main()
