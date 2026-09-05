# -*- coding: utf-8 -*-
"""XET TUNG CO CHE QUAN TRI VI THE: cai nao dang lay ve?

Chu du an 05/09: *"Boc tach ra se gom chien luoc va cac he thong ho tro. Luc nay
chien luoc thi phai kiem dinh con tien ich thi can xem xem cai nao phu hop de
lay ve"*.

Hai duong khac nhau, va day la duong THU HAI:

  chien luoc  -> dang ky gia thuyet -> `quantlab.xac_nhan` -> cong that
  QUAN TRI    -> **dap len mot he NEN roi do xem no lam he do tot len hay xau di**

Co che quan tri khong tu sinh ra tin hieu nen khong kiem dinh doc lap duoc. Cach
duy nhat do duoc gia tri cua no la DAP LEN mot he da chay va so truoc/sau.

## HE NEN

Luoi AUDCAD cau hinh Bigmouse `.set` that + dung lo 400 + hedge 3 tang/0,5.
Do 05/09: holdout 121,6%/nam tren von can 1.010 USD. Day la moc de so.

## CHAM DIEM: TIEN, khong phai ty le

Bai hoc 05/09: trailing lam sut giam co tu 1.010 USD ve 42 USD, nen ty le
`lai/sut_giam` no len 6.333%/nam - mot con so vo nghia vi mau so gan 0. Phai doc
LAI TUYET DOI truoc, roi moi nhin rui ro. Bang duoi in ca hai.
"""
from __future__ import annotations

import importlib.util as _iu
import json
import sys
import warnings

sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500")
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np

_sp = _iu.spec_from_file_location(
    "mv", r"C:\Users\SV STORE\Downloads\Research SP500\mo_phong_v2.py")
MV = _iu.module_from_spec(_sp)
_sp.loader.exec_module(MV)
MV.SWAP_NGAY = 0.0405

from nhan import du_lieu as DL

#: He NEN de dap co che len. Doi o day thi doi ca bang.
NEN = dict(buoc=36.0, kc_bs=36.0, nhom_dau=4, he_so_1=2.0, he_so_2=1.6,
           chot_tien=250.0, cat_hoa_tu=5, bien_cap=0.0, tp=13.0,
           tang_toi_da=9999, lot_toi_da=1e9, dung_lo=400.0,
           hedge_tu=3, hedge_ty=0.5, hedge_go=10.0)

#: Nut nao cua co che duoc DAP len he nen. Cac nut khac (buoc, tp, he_so_1...)
#: la THAM SO CUA LUOI, khong phai co che quan tri - dap chung vao la doi ca he
#: nen chu khong phai them mot lop.
NUT_DAP = ("trailing_tu", "trailing_buoc", "breakeven_tu", "thoat_theo_gio",
           "vol_min", "vol_max", "hedge_tu", "hedge_ty", "cat_hoa_tu",
           "chot_tien", "dung_lo")


def _mk(df, sm):
    ss = df["spread"].to_numpy(float)
    ss = np.where(np.isfinite(ss) & (ss > 0), ss, sm)
    return {"hi": df["high"].to_numpy(), "lo": df["low"].to_numpy(),
            "c": df["close"].to_numpy(),
            "sp": (ss / 10.0).astype(np.float32),
            "thu": df.index.dayofweek.to_numpy().astype(np.int8),
            "nam": (df.index[-1] - df.index[0]).days / 365.25,
            "pv": 0.0714, "cap": "AUDCAD", "n": len(df)}


def chay(nguon: str = "reports/quan_tri_da_loc.json", in_ra=print) -> list[dict]:
    specs = json.load(open(nguon, encoding="utf-8"))
    d5 = DL.nap("AUDCAD", "M5")
    sm = float(np.nanmedian(d5["spread"].to_numpy(float)))
    tr, ho = DL.hai_nua(d5, 0.6)
    Dtr, Dho = _mk(tr, sm), _mk(ho, sm)

    m_tr = MV.mo_phong(Dtr, **NEN)
    m_ho = MV.mo_phong(Dho, **NEN)
    in_ra("=" * 96)
    in_ra("XET CO CHE QUAN TRI VI THE - dap len he NEN (luoi AUDCAD)")
    in_ra("=" * 96)
    in_ra("HE NEN            train lai %8.0f$/nam  holdout lai %8.0f$/nam  "
          "sut giam %7.0f$" % (m_tr["lai_nam"], m_ho["lai_nam"], m_ho["von"]))
    in_ra("")

    ket = []
    for s in specs:
        nut = {k: v for k, v in (s.get("nut_van") or {}).items()
               if k in NUT_DAP and isinstance(v, (int, float))
               and not isinstance(v, bool)}
        if not nut:
            continue
        try:
            a = MV.mo_phong(Dtr, **{**NEN, **nut})
            b = MV.mo_phong(Dho, **{**NEN, **nut})
        except Exception as e:
            ket.append({"ten": s["ten"], "loi": str(e)[:60]})
            continue
        ket.append({
            "ten": s["ten"], "nut": nut,
            "lai_tr": a["lai_nam"], "lai_ho": b["lai_nam"],
            "sut_ho": b["von"], "ro_ho": b["ro_nam"],
            # DOC TIEN TRUOC: co che chi dang lay ve neu lam TANG lai tuyet doi
            # tren CA HAI nua, khong phai chi lam nho mau so.
            "hon_tr": a["lai_nam"] - m_tr["lai_nam"],
            "hon_ho": b["lai_nam"] - m_ho["lai_nam"],
        })

    tot = [k for k in ket if "loi" not in k
           and k["hon_tr"] > 0 and k["hon_ho"] > 0]
    tot.sort(key=lambda k: -k["hon_ho"])
    in_ra("--- CO CHE LAM HE NEN TOT LEN TREN CA HAI NUA (%d/%d) ---"
          % (len(tot), len(ket)))
    in_ra("  %-40s %11s %11s %10s  %s"
          % ("co che", "hon train$", "hon hold$", "sut giam$", "nut dap"))
    for k in tot[:20]:
        in_ra("  %-40s %+11.0f %+11.0f %10.0f  %s"
              % (str(k["ten"])[:40], k["hon_tr"], k["hon_ho"], k["sut_ho"],
                 ",".join("%s=%g" % kv for kv in k["nut"].items())[:38]))
    xau = [k for k in ket if "loi" not in k and (k["hon_tr"] <= 0
                                                 or k["hon_ho"] <= 0)]
    in_ra("")
    in_ra("  KHONG lay ve: %d (lam xau it nhat MOT nua)" % len(xau))
    # numpy float32 khong JSON hoa duoc -> `default=float`. Da sap 05/09 va
    # lam mat ca bang vi buoc ghi nam SAU buoc in.
    json.dump(ket, open("reports/xet_quan_tri.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    in_ra("  chi tiet -> reports/xet_quan_tri.json")
    return ket


if __name__ == "__main__":
    chay()
