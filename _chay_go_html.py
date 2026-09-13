# -*- coding: utf-8 -*-
"""_chay_go_html.py - go HET kho HTML tho, chay nhieu me cho den khi sach."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhan import go_html as GH

if __name__ == "__main__":
    me = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    luong = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    t0 = time.time(); tong = {"ban": 0, "rong": 0, "loi": 0}
    for i in range(1, 60):
        print(f"=== ME {i} | {time.time()-t0:.0f}s ===", flush=True)
        d = GH.go_kho(me, luong)
        print(" ", json.dumps(d, ensure_ascii=False), flush=True)
        for k in ("ban", "rong", "loi"):
            tong[k] += d.get(k, 0)
        if d.get("ban", 0) + d.get("rong", 0) == 0:
            break
    tong["giay"] = round(time.time() - t0, 1)
    print("TONG:", json.dumps(tong, ensure_ascii=False), flush=True)
