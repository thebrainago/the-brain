import requests, json, time
from pathlib import Path
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
H = {"User-Agent": UA, "Accept": "application/json"}
rep = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab\reports")
urls = [("algotrading", "https://www.reddit.com/r/algotrading/hot.json?limit=10"),
        ("quant", "https://www.reddit.com/r/quant/hot.json?limit=10")]
rows = {}
for name, u in urls:
    try:
        r = requests.get(u, headers=H, timeout=20)
        if r.status_code != 200:
            print(name, "HTTP", r.status_code); continue
        j = r.json()
        posts = j.get("data", {}).get("children", [])
        rows[name] = [{"t": c["data"].get("title"), "url": "https://reddit.com" + c["data"].get("permalink","")} for c in posts]
        print(name, "->", len(posts), "posts HTTP200")
    except Exception as e:
        print(name, "ERR", str(e)[:90])
    time.sleep(1)
lines = ["# REDDIT - algo/quant hot (public, khong login)", "Ngay: " + time.strftime("%Y-%m-%d %H:%M"), ""]
for name, ps in rows.items():
    lines += ["## r/" + name] + [f"- [{p['t']}]({p['url']})" for p in ps] + [""]
f = rep / "REDDIT_HOT.md"
f.write_text("\n".join(lines), encoding="utf-8")
print("DA GHI:", f)
for ps in rows.get("algotrading", [])[:8]:
    print("  -", ps["t"][:80])
