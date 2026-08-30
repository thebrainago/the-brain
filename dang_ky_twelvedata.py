# THE BRAIN - dang ky Twelve Data lay API key
import time, json, re, pathlib, secrets, string
from playwright.sync_api import sync_playwright
LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
EMA = json.loads((LAB/"config"/"email_cong_tac.json").read_text(encoding="utf-8"))
CFG = LAB/"config"/"credentials.json"
HB = LAB/"reports"/"twelvedata_dk_heartbeat.txt"
URL = "https://twelvedata.com/register"
def gen_pw(l=18):
    al = string.ascii_letters+string.digits+"!@#"
    return "".join(secrets.choice(al) for _ in range(l))
def load_creds():
    if CFG.exists():
        try: return json.loads(CFG.read_text(encoding="utf-8"))
        except Exception: pass
    return {}
def save_creds(c):
    CFG.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
def main():
    (LAB/"reports").mkdir(exist_ok=True)
    pw = gen_pw()
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(channel="chrome",
            user_data_dir=str(LAB/".profile_twelvedata"), headless=False,
            viewport={"width":1280,"height":900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="load", timeout=60000)
        time.sleep(3)
        try:
            page.wait_for_selector('input[name="email"]', timeout=20000)
            page.fill('input[name="name"]', "The Brain")
            page.fill('input[name="email"]', EMA["email"])
            page.fill('input[name="password"]', pw)
            page.fill('input[name="password_confirmation"]', pw)
            HB.write_text("da dien form", encoding="utf-8")
            page.click('input[type="submit"], button[type="submit"]', timeout=10000)
            HB.write_text("da submit", encoding="utf-8")
        except Exception as e:
            try:
                (LAB/"reports"/"twelvedata_dk_page.txt").write_text("URL="+page.url+"\n"+page.inner_text("body")[:1500], encoding="utf-8")
            except Exception: pass
            HB.write_text("loi: "+str(e)[:200], encoding="utf-8")
            ctx.close(); return
        # cho roi tren dashboard, tim key
        key = None
        for _ in range(40):
            time.sleep(3)
            try: txt = page.inner_text("body")
            except Exception: continue
            (LAB/"reports"/"twelvedata_live.txt").write_text(txt, encoding="utf-8")
            m = re.search(r"\b[A-Za-z0-9]{40}\b", txt)
            if m:
                key = m.group(0); break
            if "dashboard" in page.url.lower() or "account" in page.url.lower():
                break
        c = load_creds()
        if key:
            c["twelvedata"] = {"api_key": key, "email": EMA["email"], "password": pw}
            save_creds(c)
            HB.write_text("KEY: "+key, encoding="utf-8")
            print("KEY:", key)
        else:
            c["twelvedata"] = {"ghi_chu": "chua lay duoc key", "password": pw, "email": EMA["email"]}
            save_creds(c)
            HB.write_text("chua co key", encoding="utf-8")
            print("chua co key")
        ctx.close()
if __name__ == "__main__":
    main()
