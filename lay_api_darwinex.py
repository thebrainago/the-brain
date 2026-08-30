# THE BRAIN - tu dong lay API token Darwinex
# Buoc thu cong duy nhat: dang nhap Darwinex 1 lan trong cua so trinh duyet.
import time, json, re, pathlib
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
PROFILE = LAB / ".browser_darwinex"
URL = "https://www.darwinex.com/data/darwin-api"
OUT = LAB / "reports" / "darwinex_page.txt"
CFG = LAB / "config" / "credentials_darwinex.json"
BANNER = """
<div id="brain_banner" style="position:fixed;top:0;left:0;right:0;z-index:999999;
background:#ffdd57;color:#111;padding:12px 16px;font:bold 15px sans-serif;box-shadow:0 2px 6px rgba(0,0,0,.3)">
 THE BRAIN - LAY API DARWINEX<br>
 1) Dang nhap Darwinex (email + mat khau + 2FA neu co).<br>
 2) Vao duoc trang API (noi hien token), bam nut mau xanh ben phai.<br>
</div>
<button id="brain_done" onclick="window.__brain_done=1" style="position:fixed;top:130px;right:16px;z-index:999999;
background:#0066cc;color:#fff;padding:10px 22px;border:none;border-radius:6px;
font:bold 16px sans-serif;cursor:pointer">DA XONG - LAY API</button>
<script>window.__brain_done = 0;</script>
"""

def inject(page):
    try:
        page.evaluate("el => { const d=document.createElement('div'); d.innerHTML=el; document.body.prepend(d); }", BANNER)
    except Exception as e:
        print("banner inject loi:", e)

def main():
    (LAB / "reports").mkdir(exist_ok=True)
    (LAB / "config").mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), headless=False,
            viewport={"width":1366,"height":900}, args=["--start-maximized"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        inject(page)
        print("MO CUA SO -> dang nhap Darwinex roi bam nut XANH.", flush=True)
        deadline = time.time() + 3600   # toi da 60 phut, browser mo toi khi set xong
        done = False; reason = ""
        while time.time() < deadline:
            try:
                if page.evaluate("window.__brain_done === 1"):
                    done = True; reason = "button"; break
            except Exception:
                pass
            try:
                low = page.inner_text("body").lower()
                (LAB / "reports" / "darwinex_heartbeat.txt").write_text(
                    time.strftime("%H:%M:%S") + " len=" + str(len(low)), encoding="utf-8")
            except Exception:
                time.sleep(3); continue
            if ("access token" in low or "consumer key" in low
                    or "refresh token" in low or "consumer secret" in low):
                done = True; reason = "content"; break
            time.sleep(3)
        (LAB / "reports" / "darwinex_heartbeat.txt").write_text("done=" + reason, encoding="utf-8")
        if not done:
            print("HET THOI GIAN (60 phut) hoac chua dang nhap xong.", flush=True)
        else:
            print("DUNG: " + reason, flush=True)
        time.sleep(4)
        text = page.inner_text("body")
        OUT.write_text(text, encoding="utf-8")
        print("DA LUU text trang ->", OUT, flush=True)
        creds = extract(text)
        if creds:
            CFG.write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")
            print("DA LUU credentials ->", CFG, flush=True)
        else:
            print("CHUA tim thay credential -> gui noi dung " + str(OUT) + " cho toi phan tich.", flush=True)
        ctx.close()

TOKEN_RE = re.compile(r"[A-Za-z0-9\-_]{40,}")

def extract(text):
    out = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, l in enumerate(lines):
        low = l.lower()
        key = None
        if "access token" in low or "access_token" in low:
            key = "access_token"
        elif "consumer key" in low or "consumer_key" in low:
            key = "consumer_key"
        elif "consumer secret" in low or "consumer_secret" in low:
            key = "consumer_secret"
        elif "refresh token" in low or "refresh_token" in low:
            key = "refresh_token"
        if key and key not in out:
            for cand in (l, lines[i+1] if i+1 < len(lines) else ""):
                m = TOKEN_RE.search(cand)
                if m and len(m.group(0)) >= 40:
                    out[key] = m.group(0)
                    break
    return out

if __name__ == "__main__":
    main()
