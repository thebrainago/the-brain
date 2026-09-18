# -*- coding: utf-8 -*-
"""Chay ham `do` cua tho qua dung bo ky luat tang kham pha, in JSON ra stdout."""
import json, sys, importlib.util
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import brain_co_che as bc

ten = sys.argv[1]
duong_dan = Path(sys.argv[2])
chi_kl = len(sys.argv) > 3 and sys.argv[3] == "kl"

spec = importlib.util.spec_from_file_location("co_che_tho", duong_dan)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

kq = bc.chay_ham(m.do, ten, ma_kd="DS", chi_kl=chi_kl, in_ra=False, so_hat=3)
if not kq or "loi_mau" in kq:
    print(json.dumps({"loi": (kq or {}).get("loi_mau", "khong thi truong nao chay duoc")},
                     ensure_ascii=False)); sys.exit(0)
g = kq["gop"]
print(json.dumps({
    "co_che": ten, "tom_tat": kq["tom_tat"],
    "trung_vi": g["trung_vi"], "so_thi_truong": g["so_thi_truong"],
    "so_duong": g["so_duong"], "nhom_duong": g["nhom_duong"], "so_nhom": g["so_nhom"],
    "p_theo_nhom": g["p_theo_nhom"], "p_28_dong": g["p_phep_thu_dau"],
    "trung_vi_nhom": g["trung_vi_nhom"],
    "theo_thi_truong": [{k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                         for k, v in r.items()} for r in kq["theo_thi_truong"]],
}, ensure_ascii=False))
