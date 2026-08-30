import json
p = r"C:\Users\SV STORE\Downloads\Research SP500\lab\config\tai_nguyen.json"
c = json.loads(open(p, encoding="utf-8-sig").read())
c["worker"]["EVO"]["task"] = ["evo_giam_sat.py"]
open(p, "w", encoding="utf-8").write(json.dumps(c, ensure_ascii=False, indent=1))
print("EVO task =>", c["worker"]["EVO"]["task"])
