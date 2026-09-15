# -*- coding: utf-8 -*-
"""_san_quan_tri_lenh.py - SAN NGUON NGOAI cho ho QUAN TRI LENH.

## Vi sao co file nay

Chu du an, 15/09/2026: *"khi co de bai cau chua he dung seeker de tim kiem
nguon ben ngoai. Vi du toi la cau hom nay toi se tim nat tu khoa hedging,
trailing, bot dat lenh khong dieu kien, audcad, audcad hedging, cau khong su
dung kenh dan manh nhat?"*

Dung. `TU_KHOA_GOC` da co lop quan tri vi the tu 13/09, nhung no chi duoc quet
khi `seeker.mot_luot()` tinh co xoay toi - va no thieu han lop **THEO CAP**
(`audcad hedging`, `eurgbp grid`). Mot de bai cu the thi phai san CHO de bai
do, khong doi vong xoay.

Khac `seeker.mot_luot()` o hai diem:
  - tu khoa do de bai quyet dinh, khong lay tu `TU_KHOA_GOC`
  - khong co ngan sach 90 giay/nguon: de bai nay dang mo, cho no chay du

Chay:  python _san_quan_tri_lenh.py            (tat ca)
       python _san_quan_tri_lenh.py --nhanh    (chi nguon co MA NGUON)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import tu_khoa_da_ngon_ngu as TK   # noqa: E402
from tru import seeker as SK                 # noqa: E402

#: Lop THEO CAP - cai chua ai san bao gio. AUDCAD/EURGBP la hai cap vua qua
#: tester that nen no la cho dong tien that se chay. Giu rieng vi no khong phai
#: khai niem chung, khong dua vao `tu_khoa_da_ngon_ngu` duoc.
TU_KHOA_CAP = [
    "audcad grid trading", "audcad hedging expert advisor",
    "audcad mean reversion strategy", "eurgbp range trading strategy",
    "eurgbp grid expert advisor", "aud cad correlation pairs trading",
    "cross pair mean reversion forex ea",
    # Nga/Nhat/Trung cho chinh hai cap nay - cong dong ban le ba nuoc nay viet
    # ve cap cheo bang tieng me de, khong bang tieng Anh.
    "AUDCAD сеточный советник", "AUDCAD стратегия форекс",
    "AUDCAD 両建て", "AUDCAD ナンピン EA",
    "AUDCAD 网格 策略", "EURGBP 网格 EA",
    "EURGBP советник форекс", "EURGBP レンジ 自動売買",
]

#: Nguon KEYWORD-DRIVEN. `n_mql5_code` duyet theo DANH MUC chu khong theo tu
#: khoa (xem `MQL5_DANH_MUC`) nen khong nhan duoc lop tu khoa nay - de rieng.
NGUON_THEO_TU_KHOA = ["github", "tradingview_pine", "lean_algo", "stackexchange",
                      "quantconnect", "blog", "hackernews"]
NGUON_NHANH = ["github", "tradingview_pine", "lean_algo"]


def main() -> int:
    nhanh = "--nhanh" in sys.argv
    uu_tien = int(sys.argv[sys.argv.index("--uu-tien") + 1]
                  if "--uu-tien" in sys.argv else 3)
    ten_nguon = NGUON_NHANH if nhanh else NGUON_THEO_TU_KHOA
    tu_khoa = TK.tu_khoa(uu_tien_toi_da=uu_tien) + TU_KHOA_CAP
    print("SAN NGUON NGOAI cho ho QUAN TRI LENH")
    print("%d tu khoa x %d nguon (uu tien ngon ngu <= %d)"
          % (len(tu_khoa), len(ten_nguon), uu_tien))
    theo = TK.theo_ngon_ngu()
    print("   %-4s %3d: %s" % ("cap", len(TU_KHOA_CAP), TU_KHOA_CAP[0]))
    for m, ds in theo.items():
        ten = "Anh" if m == "en" else TK.NGON_NGU[m][0]
        print("   %-4s %3d: %s" % (m, len(ds), ds[0]))
        del ten
    print()
    tong = 0
    for ten in ten_nguon:
        cfg = SK.NGUON.get(ten)
        if not cfg:
            print("%-18s KHONG CO trong seeker.NGUON - bo" % ten)
            continue
        t0 = time.time()
        try:
            # Nhieu nguon tu cat `tu_khoa[:_so_tu_khoa(ten)]` - de bai nay can
            # QUET HET nen goi tung me nho thay vi dua ca danh sach mot lan.
            n_tk = SK._so_tu_khoa(ten)
            ds = []
            for i in range(0, len(tu_khoa), n_tk):
                ds += cfg["ham"](tu_khoa[i:i + n_tk]) or []
            moi = SK.luu_tai_lieu(ten, ds)
        except Exception as e:
            print("%-18s LOI: %s" % (ten, repr(e)[:70]))
            continue
        tong += int(moi or 0)
        print("%-18s tim %4d · MOI %4d · %5.1fs"
              % (ten, len(ds), moi or 0, time.time() - t0))
    print("\ntong tai lieu MOI vao kho: %d" % tong)
    print("buoc sau: `b boc` de doc va boc co che tu chung")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
