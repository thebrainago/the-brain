# -*- coding: utf-8 -*-
"""cross_pair_quet.py - QUET M1 local: mo phong he grid LuoiDoiXung/mo_phong_v2
tren tat ca cap co *_M1_mq.parquet da tai ve may (khong can MT5/network).
Chay: python cross_pair_quet.py [--limit N] [--pair EURCAD]
"""
import json, sys, time, argparse
from pathlib import Path

ROOT = Path(r"C:\Users\SV STORE\Downloads\Research SP500")
sys.path.insert(0, str(ROOT))
import mo_phong_v2 as mp

DATA = ROOT / "data"
OUT = ROOT / "lab" / "reports" / "cross_scan_M1.json"

def chay(cap, tham_so=None):
    d = mp.nap(cap)
    r = mp.mo_phong(d, **(tham_so or {}))
    def g(*ks):
        for k in ks:
            if k in r:
                return r[k]
        return None
    # map theo key that mo_phong_v2 tra ve
    return {
        "cap": cap, "nam": round(d.get("nam", 0), 1),
        "lai_nam": round(g("lai_nam", 0) or 0, 1),
        "loi_suat_pct": round(g("ls", 0) or 0, 2),
        "von": round(g("von", 0) or 0, 0),
        "cat_nam": round(g("cat_nam", 0) or 0, 3),
        "ro_nam": round(g("ro_nam", 0) or 0, 0),
        "lenh_ca_tuan": round(g("lenh_tuan", 0) or 0, 1),
        "pct_duoi_dinh": round(g("pct_duoi_dinh", 0) or 0, 2),
        "hoi_von_ngay": round(g("hoi_von_ngay", 0) or 0, 1),
        "giay": round(g("giay", 0) or 0, 1),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--pair", default=None)
    a = ap.parse_args()
    caps = sorted([p.stem.split("_M1_mq")[0] for p in DATA.glob("*_M1_mq.parquet")])
    if a.pair: caps = [c for c in caps if c.upper() in a.pair.upper().split(",")]
    if a.limit: caps = caps[: a.limit]
    kq = []
    for cap in caps:
        t0 = time.time()
        try:
            r = chay(cap)
            r["giay"] = round(time.time() - t0, 1)
            kq.append(r)
            print(f"  {cap:8} lai_nam={r['lai_nam']:>8} roi%={r['loi_suat_pct']:>6} cat={r['cat_nam']} lenh/tuan={r['lenh_ca_tuan']:>6} ({r['giay']}s)", flush=True)
        except Exception as e:
            print(f"  {cap:8} LOI: {str(e)[:120]}", flush=True)
            kq.append({"cap": cap, "loi": str(e)[:200]})
    out = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "loai": "grid_mo_phong_v2_M1",
           "n": len(kq), "ket_qua": kq}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DA GHI:", OUT)

if __name__ == "__main__":
    main()
