# -*- coding: utf-8 -*-
"""_thu_chuoi_dai.py - BA PHEP THU BAT BUOC cho moi ung vien, tren chuoi DAI NHAT co.

Tong quat hoa `_z5_chuoi_dai.py` sau khi phep thu do lat nguoc ung vien manh nhat
cua du an. Bat ky co che nao trong `doc_kho()` deu chay duoc qua day.

## VI SAO BA PHEP NAY, KHONG PHAI MOT

1. **Chuoi dai nhat co.** Mot cua so 6 nam co the nam tron trong mot che do.
   z5 do 12/09: Sharpe 1,158 tren 6,3 nam CFD, nhung **-0,141 tren 55,5 nam**
   NASDAQ va **-0,081 tren 98,6 nam** SP500.

2. **Ban do tham so so voi MDE, khong so voi 0.** "Cao nguyen" cham bang nguong 0
   la vo nghia: tren mot chuoi dai moi o deu quanh 0. Phai hoi **bao nhieu o vuot
   MDE cua chinh chuoi do**. z5: 0/48 o tren ca hai chuoi dai.
   Quet o day la NHAN CHU KY voi mot he so, ap cho moi `n` trong khai bao - cach
   nay dung duoc cho ca co che khong co tham so nguong (vd. chong EMA).

3. **Tach theo giai doan 5 nam.** Trung binh 50 nam co the la mot nua song cong
   mot nua chet. z5 tren SP500: AM lien tuc 1962-2001, DUONG lien tuc 2002-2026.

## KHONG PHAI CHE DO GIAO DICH

Chuoi Yahoo/chi so KHONG mua duoc; chi phi o day la KHAI BAO. File nay tra loi
**"co che co ton tai khong"**, khong tra loi "co giao dich duoc khong". Mot co che
qua day van phai quay ve chuoi giao dich duoc de lay PASS.

Chay:  python _thu_chuoi_dai.py <ten_co_che> [MA]
       python _thu_chuoi_dai.py quantora_ma_dashboard_sell YH_NASDAQ
Ra:    reports/CHUOI_DAI_<ten>_<MA>.json
"""
from __future__ import annotations

import copy
import json
import sys
import warnings
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402

from nhan import bien_don_bay as B  # noqa: E402
from nhan import chi_phi as CP  # noqa: E402
from nhan import do_luc as DLUC  # noqa: E402
from nhan import du_lieu as DL  # noqa: E402
from nhan import mo_phong as MP  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

KHUNG = "D1"
HE_SO = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]


def nhan_chu_ky(nut, he_so: float):
    """Nhan MOI truong `n` trong cay khai bao voi `he_so` (toi thieu 2)."""
    if isinstance(nut, dict):
        ra = {}
        for k, v in nut.items():
            if k == "n" and isinstance(v, (int, float)) and not isinstance(v, bool):
                ra[k] = max(2, int(round(v * he_so)))
            else:
                ra[k] = nhan_chu_ky(v, he_so)
        return ra
    if isinstance(nut, list):
        return [nhan_chu_ky(v, he_so) for v in nut]
    return nut


def _cp(d, ma):
    c = CP.tu_du_lieu(ma, d)
    return c[0] if isinstance(c, tuple) else c


def do_mot(d, spec, cp, ma):
    v = np.asarray(NP.sinh_tu_spec(spec, d), float)
    kq = MP.chay(d, v, cp, ma=ma, khung=KHUNG, don_bay=1.0, gop="so_hoc")
    c = B._chi_so(kq)
    c["so_lenh"] = int(kq.so_lenh)
    c["phoi_nhiem_vao"] = float(np.mean(np.abs(v) > 0))
    return c


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[-3])
        return 2
    ten = argv[0]
    ma = argv[1] if len(argv) > 1 else "YH_NASDAQ"

    goc = next((s for s in NP.doc_kho() if s.get("ten") == ten), None)
    if goc is None:
        print("khong thay co che '%s' trong kho" % ten)
        return 1

    df = DL.nap(ma, KHUNG)
    nam = (df.index[-1] - df.index[0]).days / 365.25
    cp = _cp(df, ma)
    mde = (DLUC._doc_mde_cache().get("%s|%s" % (ma, KHUNG)) or {}).get("mde")

    print("=" * 78)
    print("BA PHEP THU CHUOI DAI: %s tren %s %s" % (ten, ma, KHUNG))
    print("=" * 78)
    print("%d bar · %s -> %s · %.1f nam · MDE %s · chieu %+d · ho %s"
          % (len(df), df.index[0].date(), df.index[-1].date(), nam,
             ("%.3f" % mde) if mde else "chua do",
             goc.get("chieu", 1), goc.get("ho", "?")))

    he = do_mot(df, goc, cp, ma)
    bh = do_mot(df, {"ten": "mua_giu", "ho": "chung", "chieu": 1, "giu": 10 ** 9,
                     "vao": [], "ra": []}, cp, ma) if False else None
    v1 = np.ones(len(df), float)
    kqbh = MP.chay(df, v1, cp, ma=ma, khung=KHUNG, don_bay=1.0, gop="so_hoc")
    bh = B._chi_so(kqbh)

    print("\n--- 1. TREN CA %.1f NAM ---" % nam)
    print("  %-12s %9s %9s %9s %9s %8s %8s"
          % ("", "CAGR%", "Sharpe", "Calmar", "maxDD%", "lenh", "phoinhiem"))
    print("  %-12s %9.2f %9.3f %9.3f %9.1f %8d %8.1f%%"
          % (ten[:12], he["cagr"] * 100, he["sharpe"], he.get("calmar", 0),
             he["maxdd"] * 100, he["so_lenh"], 100 * he["phoi_nhiem_vao"]))
    print("  %-12s %9.2f %9.3f %9.3f %9.1f %8s %8.1f%%"
          % ("MUA-GIU", bh["cagr"] * 100, bh["sharpe"], bh.get("calmar", 0),
             bh["maxdd"] * 100, "-", 100.0))
    if mde:
        print("  Sharpe / MDE = %.3f / %.3f = **%.2f lan**"
              % (he["sharpe"], mde, he["sharpe"] / mde))

    print("\n--- 2. BAN DO CHU KY x he so (so la SHARPE) ---")
    ban_do = {}
    for hs in HE_SO:
        s = copy.deepcopy(goc)
        s["vao"] = nhan_chu_ky(s.get("vao") or [], hs)
        s["ra"] = nhan_chu_ky(s.get("ra") or [], hs)
        try:
            ban_do["x%.2f" % hs] = round(do_mot(df, s, cp, ma)["sharpe"], 3)
        except Exception:
            ban_do["x%.2f" % hs] = None
    print("  " + "  ".join("%6s" % k for k in ban_do))
    print("  " + "  ".join("%6s" % ("%.2f" % v if v is not None else "-")
                           for v in ban_do.values()))
    tren = sum(1 for v in ban_do.values() if v is not None and mde and v > mde)
    print("  o co Sharpe > MDE: %d/%d" % (tren, len(ban_do)))

    print("\n--- 3. THEO GIAI DOAN 5 NAM ---")
    print("  %-12s %8s %9s %9s %9s %7s"
          % ("giai doan", "bar", "CAGR%", "Sharpe", "BH CAGR%", "lenh"))
    ky = []
    for y in range(df.index[0].year, df.index[-1].year, 5):
        sub = df.loc[str(y):str(y + 4)]
        if len(sub) < 250:
            continue
        cps = _cp(sub, ma)
        try:
            h = do_mot(sub, goc, cps, ma)
            m = B._chi_so(MP.chay(sub, np.ones(len(sub), float), cps, ma=ma,
                                  khung=KHUNG, don_bay=1.0, gop="so_hoc"))
        except Exception:
            continue
        ky.append({"tu": y, "cagr": round(h["cagr"] * 100, 2),
                   "sharpe": round(h["sharpe"], 3),
                   "bh_cagr": round(m["cagr"] * 100, 2), "lenh": h["so_lenh"]})
        print("  %-12s %8d %9.2f %9.3f %9.2f %7d"
              % ("%d-%d" % (y, y + 4), len(sub), h["cagr"] * 100, h["sharpe"],
                 m["cagr"] * 100, h["so_lenh"]))
    duong = sum(1 for x in ky if x["cagr"] > 0)
    print("  giai doan DUONG: %d/%d" % (duong, len(ky)))

    ket = {"ten": ten, "ma": ma, "so_bar": len(df), "so_nam": round(nam, 2),
           "mde": mde, "he": {k: round(v, 4) if isinstance(v, float) else v
                              for k, v in he.items()},
           "mua_giu": {k: round(v, 4) if isinstance(v, float) else v
                       for k, v in bh.items()},
           "sharpe_tren_mde": round(he["sharpe"] / mde, 3) if mde else None,
           "ban_do_he_so": ban_do, "o_tren_mde": tren,
           "theo_giai_doan": ky, "giai_doan_duong": duong, "so_giai_doan": len(ky)}
    ra = LAB / "reports" / ("CHUOI_DAI_%s_%s.json" % (ten, ma))
    ra.parent.mkdir(exist_ok=True)
    ra.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float),
                  encoding="utf-8")
    print("\n-> %s" % ra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
