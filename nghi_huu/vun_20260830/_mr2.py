import json
from pathlib import Path
d=json.loads(Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab\reports\MR_SIM.json").read_text(encoding="utf-8"))
def line(r): return f"{r['cap']:7s} N={r['N']} k={r['k']} am={r['am']} rr={r['rr']} roi={r['roi']:>6}% dd={r['dd']:>5}% pf={r['pf']} l={r['lenh']} win={r['win']}%"
print("== TOP 10 theo ROI ==")
for r in sorted(d,key=lambda x:-x["roi"])[:10]: print(line(r))
print("== TOP 6 theo PF (positif) ==")
for r in [r for r in sorted(d,key=lambda x:-x["pf"]) if r["roi"]>0][:6]: print(line(r), "<pf cao>")
