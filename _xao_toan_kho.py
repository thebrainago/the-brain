# -*- coding: utf-8 -*-
"""_xao_toan_kho.py - BOC NOT KHO TON, chay het cong suat duong LLM.

Chu du an 13/09/2026: *"khong nap them nhieu nua ma boc tach not cho con ton
trong kho"* + *"multiagent goi qwen maxtoken tang toc het co"*.

Khac ban trong `day_viec.json` (gioi_han=400, luong=4):
  - LAP cho den khi het ton kho, khong dung sau mot me
  - LUONG cao (mac dinh 24) vi day la duong MANG chu khong phai CPU
  - GHI TIEN DO xuong dia sau moi me, de xem duoc tu ngoai
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import boc_llm as BL
from nhan import so as SO
from nhan import loc_co_che as LCC
from nhan import ngu_phap as NP

LAB = Path(__file__).resolve().parent
TIEN_DO = LAB / "reports" / "xao_toan_kho.json"

def con_ton() -> int:
    r = SO.mot("SELECT COUNT(*) c FROM noi_dung WHERE da_boc=0 AND so_ky_tu>800 "
               "AND kieu!='khong_doc_duoc'")
    return int(r["c"]) if r else 0

def main(me: int = 300, luong: int = 24, toi_da_me: int = 60):
    df = LCC.df_kiem_chuan()
    if df is None:
        print("!! khong nap duoc chuoi kiem -> dung"); return
    t0 = time.time()
    tong = {"ban": 0, "co_che_moi": 0, "me": 0}
    kho0 = len(NP.doc_kho())
    for i in range(1, toi_da_me + 1):
        ton = con_ton()
        print(f"\n=== ME {i} | con ton {ton} | kho {len(NP.doc_kho())} | "
              f"{time.time()-t0:.0f}s ===", flush=True)
        if ton <= 0:
            print("het ton kho"); break
        try:
            k = BL.boc(gioi_han=me, luong=luong, ghi_kho=True, df_kiem=df)
        except Exception as e:
            print("LOI ME:", repr(e)[:300], flush=True)
            time.sleep(5); continue
        print("  ->", json.dumps(k, ensure_ascii=False)[:400], flush=True)
        tong["ban"] += k.get("ban", 0)
        tong["co_che_moi"] += k.get("co_che_moi", 0)
        tong["me"] = i
        tong["kho"] = len(NP.doc_kho())
        tong["kho_dau"] = kho0
        tong["con_ton"] = con_ton()
        tong["giay"] = round(time.time() - t0, 1)
        TIEN_DO.parent.mkdir(exist_ok=True)
        TIEN_DO.write_text(json.dumps(tong, ensure_ascii=False, indent=1), encoding="utf-8")
        if k.get("ban", 0) == 0:
            print("me rong -> dung"); break
    print("\nTONG:", json.dumps(tong, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    a = sys.argv[1:]
    main(me=int(a[0]) if a else 300, luong=int(a[1]) if len(a) > 1 else 24)
