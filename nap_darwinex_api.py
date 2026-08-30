# THE BRAIN - tu dong vao trang API Darwinex (dung lai profile da dang nhap)
import time, json, re, pathlib
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
PROFILE = LAB / ".browser_darwinex"
URLS = [
 "https://www.darwinex.com/data/darwin-api?hsLang=en",
 "https://www.darwinex.com/data/darwin-api",
 "https://www.darwinex.com/es/data/darwin-api?hsLang=en",
]
OUT = LAB / "reports" / "darwinex_page.txt"
LIVE = LAB / "reports" / "darwinex_live.txt"
CFG = LAB / "config" / "credentials_darwinex.json"
HB = LAB / "reports" / "darwinex_heartbeat.txt"
BANNER = """
<div id="brain_banner" style="position:fixed;top:0;left:0;right:0;z-index:999999;
background:#ffdd57;color:#111;padding:12px 16px;font:bold 15px sans-serif;box-shadow:0 2px 6px rgba(0,0,0,.3)">
 THE BRAIN - dang nhap Darwinex 1 lan, sau do he thong TU DONG vao trang API va bat token.<br>
 Khong can lam gi them sau khi dang nhap.
</div>
"""

def dump(page, tag):
    try:
        t = page.inner_text("body")
        LIVE.write_text(tag + "\n" + t, encoding="utf-8")
        return t.lower()
    except Exception:
        return ""

def main():
    (LAB / "reports").mkdir(exist_ok=True)
    (LAB / "config").mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), headless=False,
            viewport={"width":1366,"height":900}, args=["--start-maximized"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        ui = 0
        for u in URLS:
            try:
                page.goto(u, wait_until="domcontentloaded", timeout=60000)
                break
            except Exception as e:
                print("goto err", u, e, flush=True)
        deadline = time.time() + 1800
        last = ""
        while time.time() < deadline:
            low = dump(page, "loop")
            if low != last:
                last = low
                HB.write_text(time.strftime("%H:%M:%S") + " len=" + str(len(low)), encoding="utf-8")
            # man hinh login?
            if "log in" in low and "password" in low and "access token" not in low:
                try:
                    page.evaluate("el => { const d=document.createElement('div'); d.innerHTML=el; document.body.prepend(d); }", BANNER)
                except Exception:
                    pass
                time.sleep(3); continue
            # 404?
            if "page not found" in low or "404" in low:
                ui += 1
                if ui < len(URLS):
                    try:
                        page.goto(URLS[ui], wait_until="domcontentloaded", timeout=60000)
                    except Exception:
                        pass
                    time.sleep(3); continue
                time.sleep(3); continue
            # co token?
            if ("access token" in low or "consumer key" in low
                    or "refresh token" in low or "consumer secret" in low):
                break
            time.sleep(3)
        time.sleep(4)
        text = page.inner_text("body")
        OUT.write_text(text, encoding="utf-8")
        HB.write_text("DONE " + time.strftime("%H:%M:%S"), encoding="utf-8")
        print("DA LUU text trang ->", OUT, flush=True)
        creds = extract(text)
        if creds:
            CFG.write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")
            print("DA LUU credentials ->", CFG, flush=True)
        else:
            print("CHUA thay credential -> gui " + str(OUT) + " cho toi phan tich.", flush=True)
        ctx.close()

TOKEN_RE = re.compile(r"[A-Za-z0-9\-_]{40,}")

def extract(text):
    out = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, l in enumerate(lines):
        low = l.lower()
        key = None
        if "access token" in low:
            key = "access_token"
        elif "consumer key" in low:
            key = "consumer_key"
        elif "consumer secret" in low:
            key = "consumer_secret"
        elif "refresh token" in low:
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
