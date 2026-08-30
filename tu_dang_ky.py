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
# Cong CDP cua con Chrome bot la 9224 (`mo_chrome_cdp.py`), khong phai
# 9222. Truoc 30/08 file nay tro nham 9222 nen no chua bao gio ket noi
# duoc - mot day thieu nua, cung ho voi `toan_van` khong goi trinh duyet.
CDP = "http://127.0.0.1:9224"
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

def xac_minh_co_thu(ten_site: str, phut: int = 10) -> dict:
    """Co thu tu nha cung cap trong `phut` phut gan day khong?

    VI SAO CAN. `form_da_submit` KHONG phai `da_co_tai_khoan`. Do that
    30/08/2026: marketstack tra ve `form_da_submit` va URL doi sang
    `/signup/free/monthly` - do la trang CHON GOI, khong phai xac nhan tao tai
    khoan. Kiem hop thu thi khong co mot thu nao tu ho.

    Ket qua that cua ca luot: **0/4 tai khoan duoc tao**, trong khi bao cao tho
    nhin nhu 1/4 thanh cong. Cung mot bai hoc voi `auto_follow` bao 8/8 followed
    trong khi 0/8 an: mot buoc BAM XONG khong phai mot buoc DA XONG.
    """
    import imaplib, email as _em, time as _t
    from datetime import datetime, timedelta
    c = _cau_hinh_email() if "_cau_hinh_email" in globals() else None
    try:
        import json as _j
        cf = _j.loads((LAB / "config" / "email_cong_tac.json")
                      .read_text(encoding="utf-8-sig"))
    except Exception:
        return {"co_thu": None, "ly_do": "khong doc duoc cau hinh email"}
    try:
        m = imaplib.IMAP4_SSL("imap.gmail.com")
        m.login(cf["email"], cf["app_password"])
        m.select("INBOX")
        moc = (datetime.now() - timedelta(minutes=phut)).strftime("%d-%b-%Y")
        typ, ids = m.search(None, f'(SINCE "{moc}")')
        thay = []
        for i in (ids[0].split() or [])[-40:]:
            _, d = m.fetch(i, "(BODY[HEADER.FIELDS (FROM SUBJECT)])")
            h = _em.message_from_bytes(d[0][1])
            gop = f"{h.get('From','')} {h.get('Subject','')}".lower()
            if ten_site.lower() in gop:
                thay.append(str(h.get("Subject"))[:90])
        m.logout()
        return {"co_thu": bool(thay), "tieu_de": thay[:3]}
    except Exception as e:
        return {"co_thu": None, "ly_do": f"{type(e).__name__}: {str(e)[:60]}"}

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
    if "--chay-het" in sys.argv:
        # Docstring dau file da noi co co nay tu lau, nhung main() khong he xu
        # ly no: go `--chay-het` chi in ra huong dan su dung. Mot co duoc ghi
        # trong tai lieu ma khong ton tai trong ma la mot dang day thieu khac.
        import time as _t
        for s in reg.get("sites", []):
            r = dang_ky_site({**s, "email": s.get("email") or reg["email"],
                              "mat_khau": s.get("mat_khau") or reg["mat_khau"]})
            # KHONG tin `form_da_submit`. Doi chieu bang hop thu.
            if str(r.get("trang_thai", "")).startswith("form_da_submit"):
                _t.sleep(20)
                xm = xac_minh_co_thu(s.get("sender_gui") or s["ten"])
                r["xac_minh_email"] = xm
                if xm.get("co_thu") is False:
                    r["trang_thai"] = "submit_nhung_KHONG_CO_THU"
                elif xm.get("co_thu") is True:
                    r["trang_thai"] = "da_gui_thu_xac_minh"
            print(f"  {s['ten']:14s} {r}", flush=True)
            _t.sleep(4)
        return
    print("dung: --dang-ky <ten> | --chay-het | sites trong registry:")
    for s in reg.get("sites", []):
        print("  -", s.get("ten"), s.get("url"))

if __name__ == "__main__":
    main()
