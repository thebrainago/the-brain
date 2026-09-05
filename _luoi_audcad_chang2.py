# -*- coding: utf-8 -*-
"""CHANG 2 cho luoi AUDCAD: holdout + do phan giai + xac suat chay.

Chi chay cho cac cau hinh DAN DAU chang 1. Ba cau hoi, ba phep do rieng:

  1. **HOLDOUT** - cau hinh chon tren train co giu duoc tren 40% cuoi khong.
  2. **DO PHAN GIAI** - quet lam tren M15; luoi bat tang theo duong di TRONG
     bar nen khung tho hon se BO SOT tang va THOI lai. Bo nho du an do duoc
     D1 thoi 11,7 lan. Phai do M15 vs M5 (va M1 neu kip) tren chinh cau hinh
     dan dau, khong duoc gia dinh "M15 du min".
  3. **XAC SUAT CHAY** - `chay=False` tren MOT duong lich su khong co nghia la
     an toan. Cat chuoi thanh nhieu cua so bat dau khac nhau va dem bao nhieu
     cua so chay. Day la thuoc do dung cho lop khong cat lo.

KHONG toi uu them o day. Cau hinh da chon xong o chang 1.
"""
from __future__ import annotations

import json
import os
import sys
import warnings

sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np

from nhan import du_lieu as DL
from nhan import luoi as L

MA = "AUDCAD"
VON = 10_000.0
NGAN_SACH_TREO = 0.33
TOP_N = int(os.environ.get("TOPN", "6"))
NGUON = "reports/luoi_audcad.json"


def lam(cfg, df, von=VON):
    ts = L.ThamSo(buoc=float(cfg["buoc"]), tp=float(cfg["tp"]),
                  tran_tang=int(cfg["tran"]), che_do=cfg["che_do"],
                  kieu_lot=cfg["kieu_lot"], he_so_lot=float(cfg["he_so_lot"]))
    kq = L.chay(df, ts, von)
    c = L.chi_so(kq, von)
    ln = kq.lai_rong / kq.so_nam
    return {"hieu_qua": ln / kq.lo_treo_dinh if kq.lo_treo_dinh > 0 else 0.0,
            "lai_nam": ln, "treo": kq.lo_treo_dinh, "chay": kq.chay,
            "ro_nam": c["ro_nam"], "maxdd_pct": c["maxdd_pct"],
            "loi_suat_scale_pct": (c["loi_suat_nam_pct"] *
                                   (NGAN_SACH_TREO * von / kq.lo_treo_dinh)
                                   if kq.lo_treo_dinh > 0 else 0.0)}


def ten(cfg):
    return ("buoc%d TP%d tran%d %s lot=%s%.2f"
            % (cfg["buoc"], cfg["tp"], cfg["tran"], cfg["che_do"],
               cfg["kieu_lot"], cfg["he_so_lot"]))


def chay() -> None:
    d = json.load(open(NGUON, encoding="utf-8"))
    song = [k for k in d if not k["chay"] and k.get("hieu_qua") and k["lai_nam"] > 0]
    song.sort(key=lambda k: -k["hieu_qua"])
    top = song[:TOP_N]

    d15 = DL.nap(MA, "M15")
    tr15, ho15 = DL.hai_nua(d15, 0.6)
    d5 = DL.nap(MA, "M5")
    tr5, ho5 = DL.hai_nua(d5, 0.6)

    print("=" * 92)
    print("CHANG 2 - %d cau hinh dan dau" % len(top))
    print("=" * 92)
    print("train M15 %d bar | holdout M15 %d bar | train M5 %d bar | holdout M5 %d bar"
          % (len(tr15), len(ho15), len(tr5), len(ho5)))
    print()

    print("--- 1+2. HOLDOUT va DO PHAN GIAI ---")
    print("  %-42s %9s %9s %9s %9s"
          % ("cau hinh", "M15 train", "M15 hold", "M5 train", "M5 hold"))
    print("  %-42s %9s %9s %9s %9s" % ("", "hieu qua", "hieu qua", "hieu qua",
                                       "hieu qua"))
    ket = []
    for cfg in top:
        a = lam(cfg, tr15)
        b = lam(cfg, ho15)
        c = lam(cfg, tr5)
        e = lam(cfg, ho5)
        ket.append({"cfg": cfg, "m15_tr": a, "m15_ho": b, "m5_tr": c, "m5_ho": e})
        print("  %-42s %9.3f %9.3f %9.3f %9.3f"
              % (ten(cfg), a["hieu_qua"], b["hieu_qua"], c["hieu_qua"],
                 e["hieu_qua"]))
    print()
    thoi = [k["m15_tr"]["hieu_qua"] / k["m5_tr"]["hieu_qua"]
            for k in ket if k["m5_tr"]["hieu_qua"] > 0]
    if thoi:
        print("  THIEN LECH DO PHAN GIAI (M15/M5 tren train): trung vi %.2f lan"
              % float(np.median(thoi)))
        print("  >1 = M15 THOI lai len. Con so nay phai < ~1,15 thi M15 moi dung")
        print("  duoc de quet; neu khong phai quet lai tren M5.")
    print()

    print("--- LOI SUAT THAT (M5, holdout, scale ve ngan sach lo treo %.0f%%) ---"
          % (NGAN_SACH_TREO * 100))
    print("  %-42s %11s %9s %9s %7s"
          % ("cau hinh", "loi suat/nam", "maxDD", "ro/nam", "chay"))
    for k in ket:
        e = k["m5_ho"]
        print("  %-42s %10.2f%% %8.1f%% %9.1f %7s"
              % (ten(k["cfg"]), e["loi_suat_scale_pct"], e["maxdd_pct"],
                 e["ro_nam"], e["chay"]))
    print()

    print("--- 3. XAC SUAT CHAY (M5, cua so 3 nam truot, buoc 6 thang) ---")
    bar_nam = 288 * 252
    cua = 3 * bar_nam
    buoc_cua = bar_nam // 2
    for k in ket[:3]:
        cfg = k["cfg"]
        hs = NGAN_SACH_TREO * VON / max(k["m5_tr"]["treo"], 1e-9)
        chay_n = tong = 0
        ls = []
        for i in range(0, max(len(d5) - cua, 1), buoc_cua):
            seg = d5.iloc[i:i + cua]
            if len(seg) < cua * 0.8:
                break
            ts = L.ThamSo(buoc=float(cfg["buoc"]), tp=float(cfg["tp"]),
                          tran_tang=int(cfg["tran"]), che_do=cfg["che_do"],
                          kieu_lot=cfg["kieu_lot"],
                          he_so_lot=float(cfg["he_so_lot"]) )
            # scale lot len ngan sach thay vi scale von
            ts.lot = 0.01 * hs
            q = L.chay(seg, ts, VON)
            cc = L.chi_so(q, VON)
            tong += 1
            chay_n += bool(q.chay)
            ls.append(cc["loi_suat_nam_pct"])
        print("  %-42s chay %d/%d cua so | loi suat trung vi %.2f%%/nam "
              "(xau nhat %.2f%%)"
              % (ten(cfg), chay_n, tong,
                 float(np.median(ls)) if ls else 0.0,
                 float(np.min(ls)) if ls else 0.0))

    # ---------------------------------------------- 4. THANG RUI RO
    print()
    print("--- 4. THANG RUI RO cho cau hinh so 1 (M5, ca chuoi 13,4 nam) ---")
    print("  Chon muc theo SUT GIAM chiu duoc, khong theo loi suat.")
    print("  'chay cua so' = so cua so 3 nam (truot 6 thang) bi stop-out.")
    cfg = ket[0]["cfg"]
    treo_goc = ket[0]["m5_tr"]["treo"]
    print()
    print("  %-9s %10s %11s %10s %9s %12s"
          % ("lot", "lo treo %", "loi suat/nam", "maxDD", "so ro/nam", "chay cua so"))
    for nhan in (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
        hs = NGAN_SACH_TREO * VON / max(treo_goc, 1e-9) * nhan
        ts = L.ThamSo(buoc=float(cfg["buoc"]), tp=float(cfg["tp"]),
                      tran_tang=int(cfg["tran"]), che_do=cfg["che_do"],
                      kieu_lot=cfg["kieu_lot"], he_so_lot=float(cfg["he_so_lot"]),
                      lot=0.01 * hs)
        q = L.chay(d5, ts, VON)
        c = L.chi_so(q, VON)
        # dem cua so chay
        chay_n = tong = 0
        for i in range(0, max(len(d5) - cua, 1), buoc_cua):
            seg = d5.iloc[i:i + cua]
            if len(seg) < cua * 0.8:
                break
            qq = L.chay(seg, ts, VON)
            tong += 1
            chay_n += bool(qq.chay)
        print("  %-9.4f %9.1f%% %10.2f%% %9.1f%% %9.1f %8d/%d"
              % (ts.lot, c["lo_treo_dinh_pct_von"], c["loi_suat_nam_pct"],
                 c["maxdd_pct"], c["ro_nam"], chay_n, tong))

    json.dump([{**k, "cfg": k["cfg"]} for k in ket],
              open("reports/luoi_audcad_chang2.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=str)
    print()
    print("chi tiet -> reports/luoi_audcad_chang2.json")


if __name__ == "__main__":
    chay()
