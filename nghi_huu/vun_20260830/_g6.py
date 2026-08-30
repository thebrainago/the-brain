p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\evo_giam_sat.py"
s = open(p, encoding="utf-8").read()
old = '''        if not e:
            van_de.append(f"{t}: KHONG co du lieu task - kiem tra worker")
        elif e.get("code") != "ok":
            van_de.append(f"{t}: task khong ok ({e.get('code')})")
        lines.append(f"| {t} | {e.get('lan','-')} | {e.get('code','-')} | {e.get('giay','-')} | {e.get('ngu','-')} |")'''
new = '''        if not e:
            van_de.append(f"{t}: KHONG co du lieu task - kiem tra worker")
            e = {}
        elif e.get("code") != "ok":
            van_de.append(f"{t}: task khong ok ({e.get('code')})")
        lines.append(f"| {t} | {e.get('lan','-')} | {e.get('code','-')} | {e.get('giay','-')} | {e.get('ngu','-')} |")'''
assert old in s, "evo loop not found"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("evo None guard ok")
