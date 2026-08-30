import re, requests, time
from pathlib import Path
rep = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab\reports")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
cats = [("Trading","https://tlgrm.eu/channels/cat/Trading"),
        ("Forex","https://tlgrm.eu/channels/cat/Forex"),
        ("Crypto","https://tlgrm.eu/channels/cat/Crypto")]
out = {}
for label, url in cats:
    try:
        r = requests.get(url, headers=H, timeout=20)
        names = re.findall(r"/channels/([a-zA-Z0-9_\-\.]{3,60})", r.text)
        seen, rows = set(), []
        for n in names:
            if n.lower() in seen: continue
            seen.add(n.lower()); rows.append(n)
        out[label] = rows[:60]
        print(label, "->", len(rows), "kenh")
    except Exception as e:
        print(label, "ERR", str(e)[:80])
    time.sleep(0.5)
lines = ["# TELEGRAM - Cong dong goi y de join", "Ngay: " + time.strftime("%Y-%m-%d %H:%M"), ""]
for label, rows in out.items():
    lines += ["## " + label, ""]
    lines += [f"- [{x}](https://t.me/{x})" for x in rows[:50]]
    lines += [""]
f = rep / "TELEG_GOI_Y.md"
f.write_text("\n".join(lines), encoding="utf-8")
print("DA GHI:", f)
print("== Trading (20 dau) ==")
for x in out.get("Trading", [])[:20]:
    print("  t.me/" + x)
