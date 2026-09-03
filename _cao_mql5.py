# -*- coding: utf-8 -*-
"""Cao MQL5 Code Base: tai file .mq5 THAT ve (03/09/2026, qua Cloudflare WARP)."""
import sys, time, json
sys.path.insert(0, '.')
from nhan import ma_nguon as MN, so as SO

if __name__ == "__main__":
    def ghi(*a): print(*a, flush=True)
    t0 = time.time()
    n0 = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu WHERE nguon='mql5_code'"))["n"]
    ghi(f"truoc: {n0} tai lieu mql5_code")
    tong = {"nhin_thay": 0, "tai_duoc": 0, "ghi_moi": 0, "trung": 0}
    loai = {}
    for vong in range(6):
        r = MN.thu_thap(muc_can=("experts", "indicators"), so_bai=30)
        for k in tong:
            tong[k] += int(r.get(k, 0) or 0)
        for k, v in (r.get("theo_loai") or {}).items():
            loai[k] = loai.get(k, 0) + int(v or 0)
        ghi(f"  vong {vong+1}: nhin {r.get('nhin_thay')} | tai {r.get('tai_duoc')} "
            f"| moi {r.get('ghi_moi')} | trung {r.get('trung')}  ({time.time()-t0:.0f}s)")
        cl = r.get("chien_luoc_chua_co_mau") or []
        for c in cl[:4]:
            ghi(f"      CHIEN LUOC: {str(c)[:90]}")
        if not r.get("nhin_thay"):
            break
    ghi(f"\n  TONG: {json.dumps(tong, ensure_ascii=False)}")
    ghi(f"  theo loai: {json.dumps(loai, ensure_ascii=False)}")
    n1 = dict(SO.mot("SELECT COUNT(*) n FROM tai_lieu WHERE nguon='mql5_code'"))["n"]
    nd = dict(SO.mot("SELECT COUNT(*) n FROM noi_dung n JOIN tai_lieu t "
                     "ON t.id=n.tai_lieu_id WHERE t.nguon='mql5_code' "
                     "AND n.kieu='ma_nguon'"))["n"]
    ghi(f"  tai lieu mql5: {n0} -> {n1}   ban doc MA NGUON: {nd}   ({time.time()-t0:.0f}s)")
