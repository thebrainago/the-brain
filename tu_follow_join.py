# -*- coding: utf-8 -*-
r"""tu_follow_join.py - SEEKER TU FOLLOW + JOIN GROUP (kiem soat spam).
Chong spam:
  - THEO_NGAY_TOI_DA : toi da follow/ngay (mac dinh 8).
  - NGHI_TOI_THIEU   : giay toi thieu giua 2 lan follow (mac dinh 60s).
  - State file ghi nhat ky moi lan follow (audit).
Chay:  python tu_follow_join.py --follow @tk
"""
import sys, time, random, json, pathlib, datetime
from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"
LAB = pathlib.Path(__file__).parent
STATE = LAB / "reports" / "x_follow_state.json"
THEO_NGAY_TOI_DA = 8
NGHI_TOI_THIEU = 60   # giay
random.seed()

def _doc_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"ngay": datetime.date.today().isoformat(), "so_lan": 0, "gan_nhat": 0, "lich": []}

def _ghi_state(st):
    st["ngay"] = datetime.date.today().isoformat()
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")

def cho_phep_follow():
    """Kiem soat spam: tra (duoc_phep, ly_do). Reset theo ngay."""
    st = _doc_state()
    if st["ngay"] != datetime.date.today().isoformat():
        st = {"ngay": datetime.date.today().isoformat(), "so_lan": 0, "gan_nhat": 0, "lich": []}
    if st["so_lan"] >= THEO_NGAY_TOI_DA:
        return False, f"qua_han {THEO_NGAY_TOI_DA}/ngay"
    if time.time() - (st["gan_nhat"] or 0) < NGHI_TOI_THIEU:
        return False, "nghi_ngan"
    return True, "ok"

def _nghi(a=0.5, z=1.5):
    time.sleep(random.uniform(a, z))

def _click_nut(page, text):
    for el in page.query_selector_all("button, [role=button], a"):
        try:
            t = (el.inner_text() or "").strip()
        except Exception:
            continue
        if t.lower() == text.lower():
            box = el.bounding_box()
            if box:
                page.mouse.move(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
                _nghi(0.3, 0.8)
                el.click()
                return True
    return False

def theo_doi_x(ten_tk):
    ok, ly = cho_phep_follow()
    if not ok:
        return {"tk": ten_tk, "trang_thai": "bo_qua:" + ly}
    p = sync_playwright().start()
    b = p.chromium.connect_over_cdp(CDP)
    try:
        page = b.contexts[0].pages[0]
        page.bring_to_front()
        page.goto(f"https://x.com/{ten_tk.lstrip('@')}", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        if _click_nut(page, "Following"):
            return {"tk": ten_tk, "trang_thai": "da_follow_truoc"}
        da = False
        for _ in range(3):
            if _click_nut(page, "Follow"):
                page.wait_for_timeout(2500)
                da = "Following" in page.inner_text()
                break
            _nghi(1, 2)
        if da:
            st = _doc_state()
            st["so_lan"] += 1
            st["gan_nhat"] = time.time()
            st["lich"] = (st.get("lich") or [])[-200:] + [{"tk": ten_tk, "luc": time.strftime("%H:%M:%S")}]
            _ghi_state(st)
        return {"tk": ten_tk, "trang_thai": "followed" if da else "khong_tim_thay_nut"}
    finally:
        b.close(); p.stop()

if __name__ == "__main__":
    if "--follow" in sys.argv:
        print(json.dumps(theo_doi_x(sys.argv[sys.argv.index("--follow")+1]), ensure_ascii=False, indent=2))
    else:
        print("dung: --follow @tk")
