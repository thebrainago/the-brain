# THE BRAIN - vao_web: lay khoa API tu NHIEU web (cau hinh bang JSON, khong code lai)
# Dung:  python vao_web.py --xem
#        python vao_web.py --site <ten> [--url <duong_dan_thu_vieng>]
# Mo ta: mo browser profile rieng cho web, cho dang nhap 1 lan, tu dong vao trang lay key,
#        trich xuat va luu vao config/credentials.json
"""VAO WEB bang trinh duyet that (dang nhap, giu phien)."""

import argparse, json, re, time, pathlib
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
REG = json.loads((LAB / "web_registry.json").read_text(encoding="utf-8"))
CFG_FILE = LAB / "config" / "credentials.json"
PROFILE_OVERRIDE = None
_prof_override_global = {'val': None}
BANNER = """
<div id="brain_banner" style="position:fixed;top:0;left:0;right:0;z-index:999999;
background:#ffdd57;color:#111;padding:12px 16px;font:bold 15px sans-serif;box-shadow:0 2px 6px rgba(0,0,0,.3)">
 THE BRAIN - <b>{ten}</b> | Dang nhap 1 lan, sau do he thong tu lam nốt.<br>
 Neu trang bat buoc dang nhap -> nhap tai khoan + mat khau (+ 2FA). Khong can lam gi them.
</div>
"""
TOKEN_RE = re.compile(r"[A-Za-z0-9\-_]{40,}")

def la(_p):
    (LAB / "reports").mkdir(exist_ok=True)
    (LAB / "config").mkdir(exist_ok=True)

def inject(page, ten):
    try:
        page.evaluate("el => { const d=document.createElement('div'); d.innerHTML=el; document.body.prepend(d); }",
                      BANNER.format(ten=ten))
    except Exception:
        pass

def is_login(low):
    return ("password" in low or "contrase" in low or "passwort" in low) and (
        "log in" in low or "sign in" in low or "iniciar ses" in low or "anmelden" in low or "login" in low)

def extract_fields(text, fields):
    out = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for key, labels in fields.items():
        for i, l in enumerate(lines):
            low = l.lower()
            if any(lb.lower() in low for lb in labels):
                for cand in (l, lines[i+1] if i+1 < len(lines) else ""):
                    m = TOKEN_RE.search(cand)
                    if m and len(m.group(0)) >= 30:
                        out[key] = m.group(0)
                        break
                if key in out:
                    break
    return out

def ensure_inject(page, ten):
    """Chen banner + nut xanh (khong lap lai neu da co)."""
    try:
        ok = page.evaluate("document.getElementById('brain_btn')") is not None
        if ok:
            return
        page.evaluate("""
            el => {
                const b=document.createElement('button');
                b.id='brain_btn'; b.innerText='DA XONG - LAY KEY';
                b.style.cssText='position:fixed;top:130px;right:16px;z-index:999999;background:#0066cc;color:#fff;padding:10px 22px;border:none;border-radius:6px;font:bold 16px sans-serif;cursor:pointer';
                b.onclick=()=>{window.__brain_done=1};
                document.body.prepend(b);
                const d=document.createElement('div');
                d.id='brain_banner_'; d.innerHTML=el; document.body.prepend(d);
            }""", BANNER.format(ten=ten))
    except Exception:
        pass


def run(site, url_override=None):
    cfg = REG[site]
    profile = pathlib.Path(_prof_override_global['val']) if _prof_override_global['val'] else (LAB / (".profile_" + site))
    ten = cfg["ten"]
    login = url_override or cfg["login"]
    targets = [url_override] if url_override else cfg["targets"]
    fields = cfg.get("fields", {})
    report = LAB / "reports" / (site + "_live.txt")
    hb = LAB / "reports" / (site + "_heartbeat.txt")
    print(f"=== {ten} ===", flush=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            channel="chrome",
            user_data_dir=str(profile), headless=False,
            viewport={"width":1366,"height":900}, args=["--start-maximized"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(login, wait_until="domcontentloaded", timeout=60000)
        except Exception:
            pass
        deadline = time.time() + 3600
        clicked = False
        while time.time() < deadline:
            ensure_inject(page, ten)
            try:
                if page.evaluate("window.__brain_done === 1"):
                    clicked = True; break
            except Exception:
                pass
            try:
                low = page.inner_text("body").lower()
            except Exception:
                time.sleep(3); continue
            hb.write_text(time.strftime("%H:%M:%S") + " len=" + str(len(low)), encoding="utf-8")
            # tu bat khi thay key ngay tren trang hien tai
            if not clicked and any(k in low for k in ("access token", "consumer key",
                                                       "refresh token", "consumer secret",
                                                       "api key", "api token")):
                clicked = True; break
            time.sleep(3)
        if not clicked:
            print("het thoi gian / chua xong, giu cua so.", flush=True)
        # di qua tung trang dich de lay key
        captured = {}
        for u in targets:
            try:
                page.goto(u, wait_until="domcontentloaded", timeout=60000)
            except Exception:
                time.sleep(3); continue
            time.sleep(4)
            ensure_inject(page, ten)
            try:
                text = page.inner_text("body")
            except Exception:
                text = ""
            report.write_text(u + "\n" + text, encoding="utf-8")
            got = extract_fields(text, fields)
            if got:
                captured.update(got)
                break
        # neu chua co, lay trang hien tai
        if not captured:
            try:
                text = page.inner_text("body")
            except Exception:
                text = ""
            captured = extract_fields(text, fields)
        creds = {}
        if CFG_FILE.exists():
            try:
                creds = json.loads(CFG_FILE.read_text(encoding="utf-8"))
            except Exception:
                creds = {}
        if captured:
            creds[site] = captured
        else:
            creds[site] = {"ghi_chu": "chua tu bat duoc - xem " + str(report)}
        CFG_FILE.write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")
        print("DA LUU ->", CFG_FILE if captured else report, flush=True)
        ctx.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xem", action="store_true")
    ap.add_argument("--site")
    ap.add_argument("--url")
    ap.add_argument("--profile", help="duong dan profile Chrome muon dung")
    a = ap.parse_args()
    la(_p := None)
    if a.xem:
        for s, c in REG.items():
            print(f"  {s:14} {c['ten']} | login: {c['login']}")
        return
    if not a.site:
        print("dung --site <ten>. Xem danh sach: python vao_web.py --xem")
        return
    if a.site not in REG:
        print("khong co web", a.site, "trong registry")
        return
    if a.profile:
        _prof_override_global["val"] = a.profile
    run(a.site, a.url)

if __name__ == "__main__":
    main()
