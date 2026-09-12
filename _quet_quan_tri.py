# -*- coding: utf-8 -*-
"""_quet_quan_tri.py - QUET CA HAI HO QUAN TRI tren nhieu tai san.

Cau hoi cua chu du an (`SO_DO_HE_THONG.txt`, muc quan trong nhat cua QUANTLAB):

    "he quan li lenh nay co the quan tri doc lap hoac lam 1 bo quy tac de tich
     hop vao nhung he thong khac (tet thu tung phuong phap quan li lenh khac
     nhau) de xem hieu qua cung nhu ket qua thay doi ra sao"

Hai ho, chay tren CUNG mot tin hieu de bien doc lap chi con mot:

    HO 1 - CAU TRUC VAO LENH   `nhan/vao_lenh.py`     hinh dang luc VAO
    HO 2 - LUAT QUAN TRI       `nhan/dap_quan_tri.py` nhung gi xay ra SAU khi vao

Tin hieu doi chieu la NEN TRONG NGOAI (bien do bar > phan vi 80 cua 20 bar gan
nhat), lay chieu theo than nen. Chon no vi no la mot LUC chu khong phai mot
huong - cau truc hai dau can dung mot tin hieu nhu vay moi co nghia.

Moi dong quy ve CUNG ngan sach sut giam 20% de so duoc voi nhau va voi moc.
Moc = max(mua-giu, ban-giu, tien mat), khong phai chi mua-giu: he long/short
lay mua-giu lam moc la sai va da sua 11/09.

Chay:  python _quet_quan_tri.py [KHUNG] [so_ma] [so_tien_trinh]
Ra:    reports/QUET_QUAN_TRI_<KHUNG>.json
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

BAR_TOI_THIEU = 800
SO_TIEN_TRINH = 10
#: Chan troi giu lenh cho tin hieu doi chieu.
GIU_DOI_CHIEU = 10


def tin_hieu_nen_trong_ngoai(df: pd.DataFrame) -> np.ndarray:
    """Nen co bien do vuot phan vi 80 cua 20 bar truoc -> chieu theo than nen.

    `rolling(...).quantile` da bao gom chinh bar hien tai, nen phai `shift(1)`:
    khong thi nguong duoc tinh tu chinh cai bar dang xet = nhin truoc.
    """
    bd = (df["high"] - df["low"]).astype(float)
    nguong = bd.rolling(20).quantile(0.8).shift(1)
    than = np.sign((df["close"] - df["open"]).to_numpy(float))
    return np.where((bd.to_numpy() > nguong.to_numpy()) & np.isfinite(nguong.to_numpy()),
                    than, 0.0)


def mot_ma(viec):
    ma, khung = viec
    try:
        from nhan import du_lieu as DL
        from nhan import dap_quan_tri as DQ
        from nhan import vao_lenh as VL
        df = DL.nap(ma, khung)
        if len(df) < BAR_TOI_THIEU:
            return {"ma": ma, "bo": "it bar (%d)" % len(df)}
        th = tin_hieu_nen_trong_ngoai(df)
        if int(np.sum(np.abs(th) > 0)) < 40:
            return {"ma": ma, "bo": "it tin hieu"}
        # Tin hieu doi chieu la nen trong ngoai - mot su kien BIEN DONG, chan
        # troi tu nhien cua no ngan. 60 bar la con so cua mot he xu huong.
        ct = VL.so_cau_truc(df, th, ma, khung, giu_toi_da=GIU_DOI_CHIEU)
        lt = DQ.so_luat(df, th, ma, khung, giu_toi_da=GIU_DOI_CHIEU)
        return {"ma": ma, "bar": len(df), "cau_truc": ct, "luat": lt}
    except Exception as e:
        return {"ma": ma, "bo": "%s: %s" % (type(e).__name__, e)}


def _xep(rows: list[dict], khoa: str) -> list[dict]:
    """Gop theo ten cau truc / ten luat: bao nhieu ma, trung vi, bao nhieu hon moc."""
    theo: dict[str, list[dict]] = {}
    for r in rows:
        theo.setdefault(r[khoa], []).append(r)
    ra = []
    for ten, ds in theo.items():
        dd20 = [d["cagr_dd20"] for d in ds]
        ra.append({"ten": ten, "so_ma": len(ds),
                   "dd20_trung_vi": round(float(np.median(dd20)), 3),
                   "dd20_tot_nhat": round(float(np.max(dd20)), 3),
                   "duong": int(sum(1 for x in dd20 if x > 0)),
                   "hon_moc": int(sum(1 for d in ds if d["hon_moc"])),
                   "sharpe_trung_vi": round(float(np.median(
                       [d["sharpe"] for d in ds])), 3)})
    return sorted(ra, key=lambda x: -x["dd20_trung_vi"])


def main(argv: list[str]) -> int:
    from nhan import ho_so_symbol as HSS
    khung = argv[0] if argv else "D1"
    gh = int(argv[1]) if len(argv) > 1 else 0
    sp = int(argv[2]) if len(argv) > 2 else SO_TIEN_TRINH
    hs = HSS.doc()
    if isinstance(hs, dict):
        hs = list(hs.values())
    ma = sorted({str(x.get("ma")) for x in hs if isinstance(x, dict) and x.get("ma")})
    if gh:
        ma = ma[:gh]
    t0 = time.time()
    with Pool(sp) as pool:
        kq = pool.map(mot_ma, [(m, khung) for m in ma], chunksize=1)
    tot = [k for k in kq if "bo" not in k]
    print("chay %d/%d ma trong %.0fs" % (len(tot), len(ma), time.time() - t0))
    ct = [r for k in tot for r in k["cau_truc"]]
    lt = [r for k in tot for r in k["luat"]]

    print("\nHO 1 - CAU TRUC VAO LENH (dd20 = lai %%/nam quy ve cung sut giam 20%%)")
    print("%-14s %5s %10s %10s %7s %8s %8s"
          % ("CAU TRUC", "MA", "DD20 TV", "DD20 TOT", "DUONG", "HON MOC", "SHARPE"))
    for d in _xep(ct, "cau_truc"):
        print("%-14s %5d %10.3f %10.3f %7d %8d %8.3f"
              % (d["ten"], d["so_ma"], d["dd20_trung_vi"], d["dd20_tot_nhat"],
                 d["duong"], d["hon_moc"], d["sharpe_trung_vi"]))

    print("\nHO 2 - LUAT QUAN TRI")
    print("%-22s %5s %10s %10s %7s %8s %8s"
          % ("LUAT", "MA", "DD20 TV", "DD20 TOT", "DUONG", "HON MOC", "SHARPE"))
    for d in _xep(lt, "luat"):
        print("%-22s %5d %10.3f %10.3f %7d %8d %8.3f"
              % (d["ten"], d["so_ma"], d["dd20_trung_vi"], d["dd20_tot_nhat"],
                 d["duong"], d["hon_moc"], d["sharpe_trung_vi"]))

    tep = LAB / "reports" / ("QUET_QUAN_TRI_%s.json" % khung.upper())
    tep.parent.mkdir(exist_ok=True)
    tep.write_text(json.dumps(
        {"khung": khung, "so_ma": len(tot), "giay": round(time.time() - t0, 1),
         "cau_truc": _xep(ct, "cau_truc"), "luat": _xep(lt, "luat"),
         "chi_tiet_cau_truc": sorted(ct, key=lambda x: -x["cagr_dd20"])[:300],
         "chi_tiet_luat": sorted(lt, key=lambda x: -x["cagr_dd20"])[:300],
         "bo": [k for k in kq if "bo" in k][:60]},
        ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print("\n-> %s" % tep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
