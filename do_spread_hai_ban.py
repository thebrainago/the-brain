# -*- coding: utf-8 -*-
"""DO: `mo_phong_v2` co dang tru spread GAP DOI so voi `nhan/mo_phong.py` khong?

## CAU HOI

Ca hai bo mo phong deu tru phi theo LUOT KHOP (mo mot luot, dong mot luot), va
`test_quan_tri_nhieu.py` chot quy uoc do nguyen van: *"hai chan, moi chan mo +
dong = 4 luot khop"*.

Nhung hai ben lay CON SO spread tu hai nguon khac nhau:

  * `nhan/mo_phong.py`  ->  `cp.spread_mang(idx)`, ma docstring cua no ghi ro
    la **"Spread MOT CHIEU"** - tuc NUA spread mua-ban.
    2 luot x nua spread = MOT spread moi vong. Dung.

  * `mo_phong_v2.py`    ->  `sp = m["spread"] / 10.0` doc thang tu bar M1 cua
    MT5. Truong `spread` cua MT5 la spread DAY DU tinh bang point; chia 10 chi
    doi point -> pip, khong chia doi.
    2 luot x spread day du = HAI spread moi vong.

Neu dung the thi `mo_phong_v2` dang dung rao chi phi **gap doi**, va hau qua
KHONG phai mot bang so xau di mot chut: cong `13_edge_vuot_spread` doi
`lai_rong >= k * phi_spread`, nen gap doi `phi_spread` la gap doi nguong. Mot
he luoi that su ra tien co the bi loai vi mot he so 2.

Day la huong BAO THU (khong tao duong tinh gia), nhung LUAT SO 0 noi muc tieu
la TIEN: loai nham mot he ra tien cung dat y nhu nhan nham mot he khong.

## PHEP DO

Cloud KHONG co `data/` nen khong tra loi duoc. Tren may co du lieu:

  1. Lay `sp` trung vi tu parquet M1 cua mot ma (don vi: pip sau khi chia 10).
  2. Lay `cp.spread_frac_chung` cua CUNG ma do (don vi: frac cua gia).
  3. Quy ca hai ve CUNG don vi roi so.

     ty_le = (sp_pip * PIP / gia_tb) / spread_frac_chung

     ~1,0  -> hai ben cung thang do, KHONG gap doi. Cau hoi dong lai.
     ~2,0  -> `mo_phong_v2` dang tru GAP DOI. Phai sua.

Ma thoat 1 khi ty le lech khoi 1,0 qua 40% - tuc `_cham` cham `AM`, va do la
mot ket qua DO DUOC chu khong phai mot loi.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np                      # noqa: E402

import mo_phong_v2 as MP2               # noqa: E402
from nhan import chi_phi as CP          # noqa: E402

MA = sys.argv[1] if len(sys.argv) > 1 else "EURCAD"


def main() -> int:
    ra: dict = {"ma": MA}
    try:
        m = MP2.nap(MA)
    except Exception as e:
        print(json.dumps({"trang_thai": "CHUA_DO_DUOC",
                          "ly_do": "khong nap duoc parquet M1 cua %s: %s: %s"
                                   % (MA, type(e).__name__, e)}, ensure_ascii=False))
        return 2
    sp = np.asarray(m["sp"], float)
    sp = sp[np.isfinite(sp) & (sp > 0)]
    gia = float(np.nanmedian(np.asarray(m["c"], float)))
    if len(sp) < 1000 or not np.isfinite(gia) or gia <= 0:
        print(json.dumps({"trang_thai": "CHUA_DO_DUOC",
                          "ly_do": "chuoi qua ngan hay gia khong doc duoc"},
                         ensure_ascii=False))
        return 2
    sp_pip = float(np.median(sp))
    ra["sp_pip_trung_vi"] = round(sp_pip, 4)
    ra["gia_trung_vi"] = round(gia, 5)
    ra["v2_frac_moi_luot"] = sp_pip * MP2.PIP / gia

    try:
        cp = CP.tu_ten(MA) if hasattr(CP, "tu_ten") else None
        frac = getattr(cp, "spread_frac_chung", None) if cp else None
    except Exception:
        frac = None
    if frac is None:
        try:
            import pandas as pd
            from nhan import du_lieu as DL
            df = DL.nap(MA, "H1")
            cp = CP.tu_du_lieu(MA, df)
            frac = float(np.median(cp.spread_mang(df.index)))
        except Exception as e:
            ra.update({"trang_thai": "CHUA_DO_DUOC",
                       "ly_do": "khong lay duoc spread_frac cua %s: %s"
                                % (MA, type(e).__name__)})
            print(json.dumps(ra, ensure_ascii=False, indent=1))
            return 2
    ra["v1_frac_moi_luot"] = float(frac)
    ty = ra["v2_frac_moi_luot"] / max(float(frac), 1e-12)
    ra["ty_le_v2_tren_v1"] = round(ty, 3)
    ra["doc_the_nao"] = ("~1,0 = cung thang do, cau hoi dong lai; "
                         "~2,0 = mo_phong_v2 tru GAP DOI moi vong")
    dat = 0.6 <= ty <= 1.4
    ra["trang_thai"] = "DAT" if dat else "AM"
    if not dat:
        ra["ket_luan"] = ("LECH: v2 tru %.2f lan v1 moi luot khop. Neu ~2 thi "
                          "cong 13_edge_vuot_spread dang dung nguong gap doi."
                          % ty)
    print(json.dumps(ra, ensure_ascii=False, indent=1))
    return 0 if dat else 1


if __name__ == "__main__":
    raise SystemExit(main())
