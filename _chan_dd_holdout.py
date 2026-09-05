# -*- coding: utf-8 -*-
"""Chan sut giam co thuc su "gan nhu mien phi" khong - do tren HOLDOUT.

Muc 4 cua ban giao 04/09 ghi: *"Them luat chan DD 40% vao he - do duoc la gan
nhu mien phi"*. Con so do (`_linh_hoat.py`) do tren TRAIN, tren dung mot he
(`macd_stochastic_doub`, YH_NASDAQ, L=2).

Hai ly do khong duoc them thang vao he:

  1. Nguong 40% duoc CHON sau khi nhin train. Mot nguong chon tren train la
     THAM SO cua gia thuyet, khong phai mot tien ich mien phi. Neu no chi mien
     phi o dung 40% va dung tren chuoi do thi no la mot lan qua khop nua.
  2. Chinh 6 he do vua FAIL holdout (`_dang_ky_6_he.py`, 05/09). Gan them luat
     vao mot he khong thang mua-giu thi khong lam no thang.

Nen viec dung o day khong phai "them vao he" ma la **do xem luat co giu tinh
chat khong khi doi sang doan du lieu chua ai nhin**. Neu giu -> no la mot luat
quan tri von dung duoc cho MOI he ve sau, va da nam san trong
`bien_don_bay.ap_luat_von`. Neu khong -> gach khoi danh sach.

Chay tren HOLDOUT, cung cach chia ma `quantlab._nap` dung (khong tu chia lai).
"""
from __future__ import annotations

import json
import sys
import warnings

sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np

from nhan import bien_don_bay as B
from nhan import chi_phi as CP
from nhan import du_lieu as DL
from nhan import mo_phong as MP
from nhan import ngu_phap as NP

KHUNG, L = "D1", 2.0
KICH_BAN = [
    ("khong lam gi", dict()),
    ("chan DD 30%", dict(chan_dd=0.30)),
    ("chan DD 40%", dict(chan_dd=0.40)),
    ("chan DD 50%", dict(chan_dd=0.50)),
    ("rut 50% lai/quy", dict(rut_ky=0.5)),
    ("rut 50% + chan 40%", dict(rut_ky=0.5, chan_dd=0.40)),
]


def doan_holdout(ma: str):
    """Y HET `quantlab._nap`: cat theo chat luong neu nguon NGOAI, roi 60/40."""
    df = DL.nap(ma, KHUNG)
    if DL.nguon_tai_san(ma) == "ngoai":
        df = DL.cat_theo_chat_luong(df, ma)[0]
    return DL.hai_nua(df, 0.6)[1]


def chay() -> None:
    he = [k for k in json.load(open("reports/muc_tieu_25.json", encoding="utf-8"))
          if k["dat"]]
    kho = {c.get("ten"): c for c in NP.doc_kho()}
    print("=" * 78)
    print("CHAN SUT GIAM TREN HOLDOUT - %d he, L=%.0f" % (len(he), L))
    print("=" * 78)

    bang: dict[str, list] = {ten: [] for ten, _ in KICH_BAN}
    for k in he:
        ma, ten = k["ma"], k["ten"]
        spec = kho.get(ten)
        if not spec:
            continue
        ho = doan_holdout(ma)
        cp = CP.tu_du_lieu(ma, ho)
        cp = cp[0] if isinstance(cp, tuple) else cp
        vi_the = np.asarray(NP.sinh_tu_spec(spec, ho), float)
        kq = MP.chay(ho, vi_the, cp, ma=ma, khung=KHUNG, don_bay=L, gop="so_hoc")
        so_nam = (ho.index[-1] - ho.index[0]).days / 365.25

        print("\n  %s | %s | holdout %d bar, %.1f nam"
              % (ten[:48], ma, len(ho), so_nam))
        print("    %-22s %8s %14s %16s %7s"
              % ("kich ban", "CAGR", "DD tai khoan", "DD von ca nhan", "so lan"))
        goc = None
        for ten_kb, kw in KICH_BAN:
            r = B.ap_luat_von(kq.loi, so_nam, **kw)
            if r.get("vo"):
                print("    %-22s   VO TAI KHOAN" % ten_kb)
                continue
            if goc is None:
                goc = r
            bang[ten_kb].append(r)
            print("    %-22s %7.2f%% %13.2f%% %15.2f%% %7d"
                  % (ten_kb, (r["cagr"] or 0) * 100, r["dd_tai_khoan"] * 100,
                     r["dd_von_ca_nhan"] * 100, r["so_lan_chan"]))

    print()
    print("=" * 78)
    print("TRUNG BINH 6 HE (holdout)")
    print("  %-22s %8s %14s %16s %10s"
          % ("kich ban", "CAGR", "DD tai khoan", "DD von ca nhan", "gia phai tra"))
    nen = None
    for ten_kb, _ in KICH_BAN:
        v = bang[ten_kb]
        if not v:
            continue
        c = float(np.mean([x["cagr"] for x in v]))
        d1 = float(np.mean([x["dd_tai_khoan"] for x in v]))
        d2 = float(np.mean([x["dd_von_ca_nhan"] for x in v]))
        if nen is None:
            nen = c
        print("  %-22s %7.2f%% %13.2f%% %15.2f%% %9.2f dd%%"
              % (ten_kb, c * 100, d1 * 100, d2 * 100, (c - nen) * 100))
    print()
    print("  Cot cuoi la CAGR mat di so voi 'khong lam gi'. 'Gan nhu mien phi'")
    print("  chi dung neu cot do gan 0 MA cot DD cai thien that.")


if __name__ == "__main__":
    chay()
