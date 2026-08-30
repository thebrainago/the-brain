# -*- coding: utf-8 -*-
"""tu_dang_nhap.py - TU DANG NHAP cac site co san pass trong config/tai_khoan.json
tren con Chrome CDP dang mo. Khong can nguoi dung dang nhap lai.
Dung lai form-detect cua dang_nhap.py. Giu tab mo (da nguoi dung quan sat)."""
from __future__ import annotations
import sys, pathlib
LAB = pathlib.Path(__file__).resolve().parent.parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))
import dang_nhap as DN

def danh_sach_site():
    kho = DN._doc_kho()
    return {k: v for k, v in kho.items()
            if isinstance(v, dict) and v.get("email") and v.get("mat_khau") and v.get("url_login")}

def dang_nhap_tat(port, toi_da=6):
    from playwright.sync_api import sync_playwright
    kq = {}
    cac = list(danh_sach_site().keys())[:toi_da]
    if not cac:
        return kq
    p = sync_playwright().start()
    try:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:%d" % port)
    except Exception as e:
        p.stop()
        return {"__loi__": "%s: %s" % (type(e).__name__, str(e)[:80])}
    try:
        ctx = b.contexts[0] if b.contexts else b.new_context()
        for site in cac:
            cred = danh_sach_site()[site]
            url = cred["url_login"]
            try:
                pg = ctx.new_page()
                try:
                    pg.bring_to_front()
                except Exception:
                    pass
                pg.goto(url, timeout=30000, wait_until="domcontentloaded")
                pg.wait_for_timeout(3500)
                f = DN.phat_hien_form(pg)
                if not f:
                    kq[site] = "da_dang_nhap"
                else:
                    em, pw, sub = f
                    em.click(); em.fill(cred["email"])
                    pw.click(); pw.fill(cred["mat_khau"])
                    try:
                        if sub: sub.click()
                        else: pg.keyboard.press("Enter")
                    except Exception:
                        pg.keyboard.press("Enter")
                    pg.wait_for_timeout(3000)
                    f2 = DN.phat_hien_form(pg)
                    kq[site] = "loi_dang_nhap" if f2 else "da_submit"
                # KHONG dong tab (giu lai, nguoi dung thay duoc)
            except Exception as e:
                kq[site] = "loi:" + ("%s: %s" % (type(e).__name__, str(e)[:40]))
        return kq
    finally:
        try: b.close()
        except Exception: pass
        p.stop()

if __name__ == "__main__":
    from nhan import doc_trinh_duyet as DT
    port = DT.cdp_dang_chay()
    print("port:", port)
    if port:
        import json
        print(json.dumps(dang_nhap_tat(port), ensure_ascii=False, indent=1))
