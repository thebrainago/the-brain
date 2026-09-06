import subprocess, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _placebo_tester as P
gop = {}
for ma in (sys.argv[1].split(",") if len(sys.argv) > 1
           else ["US500Cash", "US30Cash", "GER40Cash"]):
    print("\n########", ma, flush=True)
    try:
        r = P.chay(ma, "2021.06.01", "2026.07.29")
    except Exception as e:
        print("  LOI:", type(e).__name__, str(e)[:100]); continue
    if r.get("loi"):
        print("  LOI:", r["loi"]); continue
    gop[ma] = r["he"]
Path("reports/PLACEBO_DA_MA.json").write_text(
    json.dumps(gop, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n-> reports/PLACEBO_DA_MA.json")
