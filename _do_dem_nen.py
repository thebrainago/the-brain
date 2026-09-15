# -*- coding: utf-8 -*-
"""_do_dem_nen.py - BO DEM NEN co NOI THEM gi so voi Hurst khong?

Chu du an 15/09/2026: *"dem mau nen (nen co 1 bo dem nen thuong va 1 bo nen Ha
va cac loai nen khac)"*.

Dem duoc thi de. Cau hoi that la: **con so do co phan biet duoc tai san khong,
hay moi tai san deu ra gan giong nhau?** Do tren 11 ma dau tien thi ca 11 deu
ra 0,95-0,99 lan ngau nhien - nhin nhu mot hang so, khong phai mot dac tinh.

Nen file nay quet TOAN BO kho va hoi ba cau:
  1. bien thien giua cac ma co lon hon nhieu tap khong (neu khong thi vo dung)
  2. no co tuong quan voi `hurst` khong - tuc co noi THEM gi khong
  3. p-value that, khong phai mot con so r tren 11 quan sat

Chay:  python _do_dem_nen.py [--khung D1] [--so 200]
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

KHUNG = "D1"


def _mot(ma: str) -> dict | None:
    try:
        from nhan import dem_nen as DN
        h = DN.ho_so(ma, KHUNG)
        t = h["bo_dem"]["thuong"]
        a = h["bo_dem"]["ha"]
        return {"ma": ma, "so_bar": h["so_bar"],
                "chuoi": h["hon_ngau_nhien_tb"],
                "than_bd": t["than_tren_bien_do"]["trung_vi"],
                "doji": t["doji_pct"], "ty_le_tang": t["ty_le_tang_pct"],
                "ha_chuoi_tang": a["chuoi_tang"].get("trung_binh"),
                "ha_than_bd": a["than_tren_bien_do"]["trung_vi"]}
    except Exception:
        return None


def main() -> int:
    import multiprocessing as mp
    import numpy as np
    global KHUNG
    if "--khung" in sys.argv:
        KHUNG = sys.argv[sys.argv.index("--khung") + 1]
    so = int(sys.argv[sys.argv.index("--so") + 1]) if "--so" in sys.argv else 0

    from nhan import du_lieu as DL
    from nhan import tran_cpu as TC
    ma = sorted(DL.bang_ohlc(toi_thieu_nam=3.0))
    if so:
        ma = ma[:so]
    print("quet %d ma tren khung %s" % (len(ma), KHUNG))
    t0 = time.time()
    with mp.Pool(max(1, min(TC.so_luong_goi_y(), 10))) as p:
        ket = [x for x in p.map(_mot, ma, chunksize=4) if x]
    print("do duoc %d/%d ma trong %.0fs\n" % (len(ket), len(ma), time.time() - t0))

    hs = {}
    f = LAB / "reports" / "tinh_cach_tai_san.json"
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(d, dict):
            d = d.get("ho_so", d)
        hs = ({x["ma"]: x for x in d if isinstance(x, dict) and x.get("ma")}
              if isinstance(d, list) else d)

    def _tq(x, y):
        """Pearson + p-value hai duoi. n nho thi r to cung khong noi len gi."""
        from math import sqrt
        x, y = np.asarray(x, float), np.asarray(y, float)
        ok = np.isfinite(x) & np.isfinite(y)
        x, y = x[ok], y[ok]
        n = len(x)
        if n < 8:
            return None, None, n
        r = float(np.corrcoef(x, y)[0, 1])
        if abs(r) >= 1.0:
            return r, 0.0, n
        t = r * sqrt((n - 2) / max(1 - r * r, 1e-12))
        try:
            from statistics import NormalDist
            p = 2 * (1 - NormalDist().cdf(abs(t)))
        except Exception:
            p = float("nan")
        return r, p, n

    print("%-14s %8s %8s %8s %8s" % ("chi so", "trung vi", "p10", "p90",
                                     "bien thien"))
    cot = ("chuoi", "than_bd", "doji", "ty_le_tang", "ha_chuoi_tang")
    for c in cot:
        v = np.array([k[c] for k in ket if k.get(c) is not None], float)
        if not len(v):
            continue
        tv = float(np.median(v))
        print("%-14s %8.3f %8.3f %8.3f %8.3f"
              % (c, tv, float(np.percentile(v, 10)), float(np.percentile(v, 90)),
                 (float(np.percentile(v, 90)) - float(np.percentile(v, 10)))
                 / max(abs(tv), 1e-9)))

    print("\n--- co NOI THEM gi so voi hurst khong ---")
    hu = [(hs.get(k["ma"]) or {}).get("hurst") for k in ket]
    n_hu = sum(1 for x in hu if x is not None)
    if n_hu < 8:
        print("  chi %d ma co hurst - khong du de ket luan" % n_hu)
    else:
        for c in cot:
            r, p, n = _tq([x for x in hu], [k.get(c) for k in ket])
            if r is None:
                continue
            print("  hurst vs %-14s r = %+.3f   p = %.4f   n = %d%s"
                  % (c, r, p, n, "   <- DAT" if p is not None and p < 0.05 else ""))

    ra = LAB / "reports" / ("DEM_NEN_%s.json" % KHUNG)
    ra.write_text(json.dumps({"khung": KHUNG, "so_ma": len(ket), "ket": ket},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s" % ra.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
