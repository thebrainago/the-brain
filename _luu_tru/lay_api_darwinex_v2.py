# -*- coding: utf-8 -*-
"""Mở cua so chrome cho bro dang nhap Darwinex 1 lan -> bam DA XONG -> bat token."""
import pathlib, time, json, re
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
PROFILE = LAB / ".browser_darwinex"
SHOTS = LAB / "reports" / "darwinex_shots"
SHOTS.mkdir(parents=True, exist_ok=True)
LOG = LAB / "reports" / "darwinex_v2.log"
CFG = LAB / "config" / "credentials_darwinex.json"
URLS = ["https://www.darwinex.com/data/darwin-api",
        "https://www.darwinex.com/account"]

BANNER = ('<div id="bb" style="position:fixed;top:0;left:0;right:0;z-index:999999;'
          'background:#ffdd57;color:#111;padding:14px 16px;font:bold 15px sans-serif">'
          'THE BRAIN - <b>DANG NHAP DARWINEX o cua so nay 1 lan</b> (email+pass+2FA). '
          'Sau khi vao duoc trang token, bam nut <b style="color:#0066cc">DA XONG - LAY API</b>.</div>'
          '<button id="bd" onclick="window.__br_done=1" style="position:fixed;top:120px;right:16px;'
          'z-index:999999;background:#0066cc;color:#fff;padding:10px 22px;border:none;border-radius:6px;'
          'font:bold 16px sans-serif;cursor:pointer">DA XONG - LAY API</button>')

def log(msg):
    s = time.strftime('%H:%M:%S') + " " + msg
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(s + "\n")
    print(s)

def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE), headless=False, viewport={"width":1400,"height":950}, locale="en-US")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        log("Da mo cua so chrome. Dang mo trang API...")
        for u in URLS:
            try:
                page.goto(u, timeout=30000, wait_until="domcontentloaded")
                log("Mo " + u)
                break
            except Exception as e:
                log("goto loi " + u + " :: " + str(e)[:80])
        time.sleep(3)
        try:
            page.evaluate(f"document.body.insertAdjacentHTML('beforeend', {BANNER!r})")
            log("Da chen banner + nut DA XONG. Bro hay dang nhap roi bam nut.")
        except Exception as e:
            log("banner loi: " + str(e)[:80])
        try:
            page.screenshot(path=str(SHOTS / "v2_login.png"))
        except Exception:
            pass
        # cho bro bam DA XONG (toi da 5 phut)
        done = False
        for _ in range(300):
            try:
                if page.evaluate("window.__br_done"):
                    done = True
                    break
            except Exception:
                pass
            time.sleep(1)
        log("Bro da bam DA XONG" if done else "Het thoi gian cho (5p)")
        time.sleep(3)
        try:
            page.screenshot(path=str(SHOTS / "v2_after.png"), full_page=True)
            txt = page.evaluate("document.body ? document.body.innerText : ''")
            (SHOTS / "v2_after.txt").write_text(txt, encoding="utf-8")
            log("Da chup + luu text v2_after. Tim token...")
            found = {}
            for name in ["Access Token", "Consumer Key", "Consumer Secret", "Refresh Token"]:
                m = re.search(re.escape(name) + r"\s*[:.]?\s*([A-Za-z0-9._\-~+/=]{10,})", txt)
                if m:
                    found[name] = m.group(1)
            if found:
                CFG.write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8")
                log("TOKEN OK: " + json.dumps(list(found), ensure_ascii=False))
            else:
                log("CHUA THAY token trong text - xem anh v2_after.png")
        except Exception as e:
            log("chup loi: " + str(e)[:80])
        ctx.close()

if __name__ == "__main__":
    main()
