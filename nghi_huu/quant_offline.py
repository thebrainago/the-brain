# -*- coding: utf-8 -*-
"""quant_offline.py - QUANT worker OFFLINE (khong can mang).
Quay vong 8 cap M1 local da tai: moi lan goi lam 1 cap (grid mo_phong + ichimoku kiem dinh).
Giu tien do reports/quant_offline_state.json (portable, resume).
Chay: python quant_offline.py
"""
import json, subprocess, sys, time
from pathlib import Path

LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
DATA = LAB.parent / "data"
PY  = r"C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe"
STATE = LAB / "reports" / "quant_offline_state.json"

def doc():
    if STATE.exists():
        try: return json.loads(STATE.read_text(encoding="utf-8-sig"))
        except Exception: pass
    return {"vong": 0, "done": []}

def luu(s):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")

def main():
    st = doc()
    import os
    caps = sorted(p.stem.replace("_M1_mq", "") for p in DATA.glob("*_M1_mq.parquet"))
    phu = int(os.environ.get("BRAIN_PHU", "0")); tong = int(os.environ.get("BRAIN_TONG", "1"))
    caps_mine = caps[phu::tong]
    done = set(st.get("done", []))
    pending = [c for c in caps_mine if c not in done]
    if not pending:
        st = {"vong": st.get("vong", 0) + 1, "done": []}
        pending = caps_mine
    cap = pending[0]
    # 1) grid mo_phong tren M1 (offline)
    r1 = subprocess.run([PY, str(LAB / "cross_pair_quet.py"), "--pair", cap],
                        cwd=str(LAB), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, timeout=2400)
    # 2) ichimoku kiem dinh (offline, placebo)
    r2 = subprocess.run([PY, str(LAB / "ichimoku_cross.py"), cap, "H4,H1", "1,3,6,12,24"],
                        cwd=str(LAB), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, timeout=1500)
    st.setdefault("done", []).append(cap)
    st["done"] = list(dict.fromkeys(st["done"]))[:50]
    luu(st)
    print(f"QUANT_OFFLINE {cap} grid_rc={r1.returncode} ichi_rc={r2.returncode} vong={st['vong']}", flush=True)
    return 0 if (r1.returncode == 0 or r2.returncode == 0) else 1

if __name__ == "__main__":
    sys.exit(main())
