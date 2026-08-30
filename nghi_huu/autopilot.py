# -*- coding: utf-8 -*-
"""autopilot.py - THORN TU HANH: khong co lenh thi tu chon viec kha thi nhat lam.
Uu tien:
  T1. quet 1 cap M1 local chua quet (data/*_M1_mq.parquet, khong can mang)
  T2. neu da quet het -> MT5 re-verify fill the (neu co qwen) hoac evolution
Ghi: reports/autopilot_log.jsonl + reports/autopilot_state.json
Chay: python autopilot.py            (1 vai)
"""
import json, os, subprocess, sys, time
from pathlib import Path

LAB  = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
ROOT = Path(r"C:\Users\SV STORE\Downloads\Research SP500")
PY   = r"C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe"
DATA = ROOT / "data"
STATE = LAB / "reports" / "autopilot_state.json"
LOGL  = LAB / "reports" / "autopilot_log.jsonl"

# cau hinh chu ky (giay) - de dat meo the ngu==
CHU_KY = {
    "scan_pair": 3600,     # them d'in lam viec khi khong con cap moi
    "mt5_verify": 7200,    # 2 gio 1 lan, neu disk ok
    "evolution": 1800,     # 30p (trung R5, chi chay khi that nhanh)
}
DISK_TOI_THIEU = 15.0  # GB

def ghi(e):
    LOGL.parent.mkdir(exist_ok=True)
    with LOGL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def doc_state():
    if STATE.exists():
        try: return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception: pass
    return {"last": {}, "done_pairs": [], "done_ichimoku": ["EURCAD"]}

def luu_state(st):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")

def disk_gb():
    try:
        import ctypes
        free = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            str(DATA)[:3], None, None, ctypes.byref(free))
        return free.value / (1024**3)
    except Exception:
        return 999.0

def dau_cap_moi(st):
    caps = sorted(p.stem.replace("_M1_mq", "") for p in DATA.glob("*_M1_mq.parquet"))
    done = set(st.get("done_pairs", []))
    return [c for c in caps if c not in done]

def dau_cap_ichimoku(st):
    caps = sorted(p.stem.replace("_M1_mq", "") for p in DATA.glob("*_M1_mq.parquet"))
    done = set(st.get("done_ichimoku", []))
    return [c for c in caps if c not in done]

def chay_quet(cap):
    o = LAB / "reports" / "autopilot_scan.log"
    with o.open("w", encoding="utf-8") as f:
        subprocess.run([PY, str(LAB / "cross_pair_quet.py"), "--pair", cap],
                       cwd=str(LAB), stdout=f, stderr=subprocess.STDOUT, timeout=2400)

def chon_va_chay():
    st = doc_state()
    now = time.time()
    disk = disk_gb()
    # T1: cap M1 local chua quet (kha thi nhat, khong can mang)
    moi = dau_cap_moi(st)
    if moi and now - st.get("last", {}).get("scan_pair", 0) >= 1:
        cap = moi[0]
        ok = False
        try:
            chay_quet(cap); ok = True
        except Exception as e:
            ghi({"luc": ts(), "viec": "scan_pair", "cap": cap, "loi": str(e)[:200]})
        if ok:
            st.setdefault("done_pairs", []).append(cap)
        st["last"]["scan_pair"] = now
        ghi({"luc": ts(), "viec": "scan_pair", "cap": cap, "ok": ok, "disk_gb": round(disk,1)})
        luu_state(st)
        return "scan_pair:" + cap
    # T1b: quantlab ichimoku cho cap chua kiem dinh (tu xay - tu kiem dinh)
    ichim = dau_cap_ichimoku(st)
    if ichim and now - st.get("last", {}).get("ichimoku", 0) >= 1:
        cap = ichim[0]
        try:
            with (LAB / "reports" / "autopilot_ichimoku.log").open("w", encoding="utf-8") as f:
                subprocess.run([PY, str(LAB / "ichimoku_cross.py"), cap, "H4,H1", "1,3,6,12,24"],
                               cwd=str(LAB), stdout=f, stderr=subprocess.STDOUT, timeout=1500)
            st.setdefault("done_ichimoku", []).append(cap)
            ok = True
        except Exception as e:
            ghi({"luc": ts(), "viec": "ichimoku", "cap": cap, "loi": str(e)[:200]}); ok = False
        st["last"]["ichimoku"] = now
        ghi({"luc": ts(), "viec": "ichimoku", "cap": cap, "ok": ok, "disk_gb": round(disk, 1)})
        luu_state(st)
        return "ichimoku:" + cap
    # T2: MT5 re-verify (flush engine), neu disk ok
    if disk >= DISK_TOI_THIEU and now - st.get("last", {}).get("mt5_verify", 0) >= CHU_KY["mt5_verify"]:
        try:
            with (LAB / "reports" / "autopilot_mt5.log").open("w", encoding="utf-8") as f:
                subprocess.run([PY, str(LAB / "run_mt5_flag.py")], cwd=str(LAB),
                               stdout=f, stderr=subprocess.STDOUT, timeout=6000)
        except Exception as e:
            ghi({"luc": ts(), "viec": "mt5_verify", "loi": str(e)[:200]})
        st["last"]["mt5_verify"] = now
        ghi({"luc": ts(), "viec": "mt5_verify", "ok": True, "disk_gb": round(disk,1)})
        luu_state(st)
        return "mt5_verify"
    # T3: evolution (nhanh, it ton)
    if now - st.get("last", {}).get("evolution", 0) >= CHU_KY["evolution"]:
        try:
            subprocess.run([PY, str(LAB / "evolution.py")], cwd=str(LAB),
                           capture_output=True, text=True, timeout=600)
        except Exception as e:
            ghi({"luc": ts(), "viec": "evolution", "loi": str(e)[:200]})
        st["last"]["evolution"] = now
        ghi({"luc": ts(), "viec": "evolution", "ok": True, "disk_gb": round(disk,1)})
        luu_state(st)
        return "evolution"
    # khong co gi de lam -> ghi nhip va thoat
    ghi({"luc": ts(), "viec": "idle", "disk_gb": round(disk,1)})
    return "idle"

def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    print("AUTOPILOT:", chon_va_chay())
