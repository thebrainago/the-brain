# -*- coding: utf-8 -*-
"""262 co che x TOAN BO ma D1 trong kho (194 ma), gop da thoi dai.

Muc 3 cua ban giao 04/09: phien truoc chi quet 5 ma nen "khong cai nao vuot
MDE" khong phan biet duoc voi "chua do". Day la ban rong.

Chi DO - khong dang ky gia thuyet, khong cham holdout, khong ghi so FDR
(`da_thoi_dai.chay_co_che` khong dung `nhan/so` o bat cu dau; da kiem 05/09).

Chia luong THEO TAI SAN, khong theo co che: mot ma nap parquet mot lan roi
chay ca 262 co che tren no. Chia theo co che thi moi luong phai nap ca 194 ma.
"""
from __future__ import annotations

import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

KHUNG = "D1"
RA = "reports/quet_rong_d1.json"
SO_LUONG = int(os.environ.get("LUONG", "8"))


def _mot_ma(ma: str) -> list[dict]:
    """Ca 262 co che tren MOT ma. Chay trong tien trinh con."""
    import warnings as w
    w.filterwarnings("ignore")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from nhan import da_thoi_dai as DT
    from nhan import do_luc as DL
    from nhan import ngu_phap as NP

    try:
        r_mde = DL.mde_cua(ma, KHUNG)
        mde, do_tin = r_mde.get("mde"), r_mde.get("chi_phi_do_tin")
    except Exception:
        mde, do_tin = None, None
    ra = []
    for spec in NP.doc_kho():
        try:
            r = DT.chay_co_che(spec, ma, KHUNG)
        except Exception:
            continue
        g = r.get("gop") or {}
        s = g.get("sharpe_gop")
        if s is None:
            continue
        ra.append({"ten": spec.get("ten"), "ho": spec.get("ho"), "ma": ma,
                   "khung": KHUNG, "sharpe_gop": s, "so_bar": g.get("so_bar"),
                   "so_thoi_dai": g.get("so_thoi_dai"),
                   "dong_thuan": g.get("dong_thuan"),
                   "tung_thoi_dai": g.get("sharpe_tung_thoi_dai"),
                   "mde": mde, "chi_phi_do_tin": do_tin,
                   "vuot_mde": (mde is not None and s >= mde),
                   # Chi phi KHAI = mot con so bia (1 bps cho MOI ma khong do
                   # duoc). MDE tinh tu no khong phai nguong phat hien - do
                   # 05/09: ca 3 ma "vuot MDE" (NZDHUF 0,120 / YH_NASDAQ 0,532
                   # / TS_BTC 1,409) deu la do_tin=KHAI, va NZDHUF chi 620 bar
                   # ma MDE 0,12 trong khi EURUSD 5.729 bar duoc 0,596.
                   "vuot_mde_do_duoc": (mde is not None and s >= mde
                                        and do_tin not in (None, "KHAI"))})
    return ra


def chay() -> None:
    from nhan import du_lieu as DU
    from nhan import ngu_phap as NP

    mas = sorted(DU.kho())
    print("co che: %d | ma: %d | luong: %d" % (len(NP.doc_kho()), len(mas), SO_LUONG))
    t0 = time.time()
    ket: list[dict] = []
    xong = 0
    with ProcessPoolExecutor(max_workers=SO_LUONG) as ex:
        fu = {ex.submit(_mot_ma, m): m for m in mas}
        for f in as_completed(fu):
            xong += 1
            try:
                ket.extend(f.result())
            except Exception as e:
                print("  [LOI] %s: %s" % (fu[f], str(e)[:80]))
            if xong % 20 == 0:
                print("  ... %d/%d ma (%.0fs, %d phep do)"
                      % (xong, len(mas), time.time() - t0, len(ket)))

    ket.sort(key=lambda x: -(x["sharpe_gop"] or -9))
    json.dump(ket, open(RA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    do_duoc = [k for k in ket if k["mde"] is not None]
    vuot_tho = [k for k in do_duoc if k["vuot_mde"]]
    vuot = [k for k in do_duoc if k["vuot_mde_do_duoc"]]
    print()
    print("=" * 78)
    print("TONG phep do : %d  (%.0f phut)" % (len(ket), (time.time() - t0) / 60))
    print("do duoc MDE  : %d  |  KHONG do duoc MDE: %d"
          % (len(do_duoc), len(ket) - len(do_duoc)))
    print("VUOT MDE (tho): %d  <- gom ca ma co chi phi KHAI (bia 1 bps)"
          % len(vuot_tho))
    print("VUOT MDE THAT : %d  <- buoc chi phi phai DO DUOC" % len(vuot))
    if vuot_tho and not vuot:
        from collections import Counter
        print("  ca %d dong 'vuot' deu tren ma chi phi KHAI: %s"
              % (len(vuot_tho),
                 ", ".join("%s(%d)" % kv
                           for kv in Counter(k["ma"] for k in vuot_tho).items())))
        print("  Day KHONG phai ket qua am ve co che - la ket qua am ve CHUOI")
        print("  GIAO DICH DUOC. Chung van la ung vien cho chang bac cau san.")
    print()
    if vuot:
        print("%-42s %-14s %7s %7s %6s %5s" %
              ("co che", "ma", "sharpe", "mde", "bar", "t.dai"))
        for k in vuot[:40]:
            print("%-42s %-14s %7.3f %7.3f %6d %5s"
                  % (str(k["ten"])[:42], str(k["ma"])[:14], k["sharpe_gop"],
                     k["mde"], k["so_bar"] or 0, k["so_thoi_dai"]))
        if len(vuot) > 40:
            print("  ... con %d dong nua trong %s" % (len(vuot) - 40, RA))
    else:
        print("Khong co che nao vuot MDE (voi chi phi do duoc) tren ma nao.")
        if do_duoc:
            tot = max(do_duoc, key=lambda x: x["sharpe_gop"] - x["mde"])
            print("  gan nhat: %s tren %s  sharpe %.3f vs MDE %.3f (thieu %.3f)"
                  % (tot["ten"], tot["ma"], tot["sharpe_gop"], tot["mde"],
                     tot["mde"] - tot["sharpe_gop"]))
    print("chi tiet -> %s" % RA)


if __name__ == "__main__":
    chay()
