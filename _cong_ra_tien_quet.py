# -*- coding: utf-8 -*-
"""Chay lai TOAN BO kho ung vien da loc qua CONG RA TIEN moi.

Chu du an 05/09: *"Xay bo loc va tieu chi moi roi test lai cac he thong ta da
loc ve xem co tang them phat hien khong"*.

HAI CHANG, va thu tu nay khong duoc doi:

  CHANG 1 tren TRAIN  - mien phi, khong cham holdout. Loc lay nhung ung vien
                        dat CONG RA TIEN.
  CHANG 2 tren HOLDOUT - chi nhung cai qua chang 1. Day la lan DUY NHAT holdout
                        bi cham trong file nay.

Neu chay thang chang 2 cho ca kho thi holdout khong con la holdout: 1.500 lan
nhin vao no se sinh ra ung vien "thang" bang dung cach ma quet tham so sinh ra
ung vien gia.

KET QUA CUA FILE NAY LA MOT PHEP DO, KHONG PHAI MOT KET LUAN. Cai nao qua ca
hai chang van phai duoc dang ky (`SO.dang_ky_gia_thuyet`) va xac nhan mot lan
qua `nhan/cong.py` truoc khi goi la phat hien.
"""
from __future__ import annotations

import json
import os
import sys
import time
import warnings
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
warnings.filterwarnings("ignore")

KHUNG = "D1"
NGUON = "reports/quet_rong_d1.json"
RA = "reports/cong_ra_tien.json"
#: Bao nhieu ung vien tot nhat moi ma duoc thu. Khong lay het 262 vi phan lon
#: co sharpe train am - chay chung chi ton dien.
TOP_MOI_MA = int(os.environ.get("TOPMA", "10"))   # dat 999 = quet HET
SO_LUONG = int(os.environ.get("LUONG", "8"))


def _mot_ma(ma: str, tens: list[str]) -> list[dict]:
    import warnings as w
    w.filterwarnings("ignore")
    sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
    import numpy as np
    from nhan import chi_phi as CP
    from nhan import cong_ra_tien as CRT
    from nhan import du_lieu as DL
    from nhan import ngu_phap as NP

    try:
        df = DL.nap(ma, KHUNG)
        if DL.nguon_tai_san(ma) == "ngoai":
            df = DL.cat_theo_chat_luong(df, ma)[0]
        train, hold = DL.hai_nua(df, 0.6)
        if len(train) < 400 or len(hold) < 300:
            return []
        cp_tr = CP.tu_du_lieu(ma, train)
        cp_tr = cp_tr[0] if isinstance(cp_tr, tuple) else cp_tr
        cp_ho = CP.tu_du_lieu(ma, hold)
        cp_ho = cp_ho[0] if isinstance(cp_ho, tuple) else cp_ho
        bang_tr = CRT.bang_mua_giu(train, cp_tr, ma=ma, khung=KHUNG)
        bang_ho = CRT.bang_mua_giu(hold, cp_ho, ma=ma, khung=KHUNG)
    except Exception:
        return []

    kho = {c.get("ten"): c for c in NP.doc_kho()}
    ra = []
    for ten in tens:
        spec = kho.get(ten)
        if not spec:
            continue
        try:
            v_tr = np.asarray(NP.sinh_tu_spec(spec, train), float)
            r_tr = CRT.xet(train, v_tr, cp_tr, ma=ma, khung=KHUNG, bang_bh=bang_tr)
        except Exception:
            continue
        # Vong quay quyet dinh do nhay spread. Ung vien TS_QQQ (05/09) mat tu
        # 24,6%/nam xuong -13,3% khi spread di tu 1 len 20 bps - biet vong quay
        # thi doan duoc dieu do ma khong phai chay lai 6 lan.
        try:
            vq = float(np.abs(np.diff(np.concatenate(([0.0], v_tr)))).sum()
                       / max((train.index[-1] - train.index[0]).days / 365.25, 1e-9))
        except Exception:
            vq = None
        muc = {"ten": ten, "ma": ma, "ho": spec.get("ho"), "vong_quay_nam": vq,
               "train": {"verdict": r_tr["verdict"], "truot": r_tr["truot"],
                         "he": r_tr["he"], "bh": r_tr["mua_giu_cung_dd"],
                         "so_nam": r_tr["so_nam"]}}
        if r_tr["verdict"] == "RA_TIEN":
            try:
                v_ho = np.asarray(NP.sinh_tu_spec(spec, hold), float)
                r_ho = CRT.xet(hold, v_ho, cp_ho, ma=ma, khung=KHUNG,
                               bang_bh=bang_ho)
                muc["holdout"] = {"verdict": r_ho["verdict"],
                                  "truot": r_ho["truot"], "he": r_ho["he"],
                                  "bh": r_ho["mua_giu_cung_dd"],
                                  "so_nam": r_ho["so_nam"],
                                  "cach_biet_cagr": r_ho["cach_biet_cagr"]}
            except Exception as e:
                muc["holdout"] = {"loi": str(e)[:80]}
        ra.append(muc)
    return ra


def chay() -> None:
    from nhan import cong_ra_tien as CRT

    d = json.load(open(NGUON, encoding="utf-8"))
    theo_ma: dict[str, list] = defaultdict(list)
    for x in sorted(d, key=lambda z: -(z["sharpe_gop"] or -9)):
        if len(theo_ma[x["ma"]]) < TOP_MOI_MA:
            theo_ma[x["ma"]].append(x["ten"])
    tong = sum(len(v) for v in theo_ma.values())
    print("=" * 82)
    print("CONG RA TIEN - chay lai kho ung vien da loc")
    print("=" * 82)
    print("nguong khai bao truoc: CAGR >= %.0f%%/nam | maxDD <= %.0f%% | "
          ">= %d lenh | >= %.0f nam"
          % (CRT.MUC_CAGR * 100, CRT.TRAN_DD * 100, CRT.MIN_LENH, CRT.MIN_NAM))
    print("doi thu: MUA-GIU DUOC DON BAY LEN CUNG MUC SUT GIAM cua he")
    print("ung vien: %d ma x toi da %d = %d phep xet\n" % (len(theo_ma), TOP_MOI_MA, tong))

    t0 = time.time()
    ket, xong = [], 0
    with ProcessPoolExecutor(max_workers=SO_LUONG) as ex:
        fu = {ex.submit(_mot_ma, m, t): m for m, t in theo_ma.items()}
        for f in as_completed(fu):
            xong += 1
            try:
                ket.extend(f.result())
            except Exception as e:
                print("  [LOI] %s: %s" % (fu[f], str(e)[:70]))
            if xong % 25 == 0:
                print("  ... %d/%d ma (%.0fs)" % (xong, len(theo_ma), time.time() - t0))

    json.dump(ket, open(RA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    qua1 = [k for k in ket if k["train"]["verdict"] == "RA_TIEN"]
    qua2 = [k for k in qua1 if (k.get("holdout") or {}).get("verdict") == "RA_TIEN"]

    print()
    print("=" * 82)
    print("da xet          : %d" % len(ket))
    print("CHANG 1 (train) : %d qua CONG RA TIEN" % len(qua1))
    print("CHANG 2 (holdout): %d qua" % len(qua2))
    print()

    # vi sao truot - de biet tieu chi nao la nut that, khong chi biet "0 qua"
    dem: dict[str, int] = defaultdict(int)
    for k in ket:
        for t in k["train"]["truot"]:
            dem[t] += 1
    print("--- CHANG 1: tieu chi nao loai nhieu nhat ---")
    for t, n in sorted(dem.items(), key=lambda kv: -kv[1]):
        print("  %-26s loai %5d/%d (%.0f%%)" % (t, n, len(ket), 100 * n / max(len(ket), 1)))
    print()

    if qua2:
        print("--- QUA CA HAI CHANG ---")
        print("  %-40s %-12s %5s %8s %8s %9s"
              % ("co che", "ma", "L", "CAGR", "maxDD", "hon B&H"))
        for k in sorted(qua2, key=lambda z: -z["holdout"]["he"]["cagr"])[:30]:
            h = k["holdout"]["he"]
            print("  %-40s %-12s %5.1f %7.1f%% %7.1f%% %8.1f d%%"
                  % (k["ten"][:40], k["ma"][:12], h["don_bay"], h["cagr"] * 100,
                     h["maxdd"] * 100, k["holdout"]["cach_biet_cagr"] * 100))
    elif qua1:
        print("--- QUA CHANG 1 NHUNG TRUOT HOLDOUT (%d) ---" % len(qua1))
        d2: dict[str, int] = defaultdict(int)
        for k in qua1:
            for t in (k.get("holdout") or {}).get("truot", []):
                d2[t] += 1
        for t, n in sorted(d2.items(), key=lambda kv: -kv[1]):
            print("  %-26s loai %d/%d" % (t, n, len(qua1)))
        print()
        print("  %-38s %-11s %8s %8s | %8s %8s"
              % ("co che", "ma", "CAGR tr", "DD tr", "CAGR ho", "DD ho"))
        for k in sorted(qua1, key=lambda z: -z["train"]["he"]["cagr"])[:20]:
            t, h = k["train"]["he"], (k.get("holdout") or {}).get("he") or {}
            print("  %-38s %-11s %7.1f%% %7.1f%% | %7s %8s"
                  % (k["ten"][:38], k["ma"][:11], t["cagr"] * 100, t["maxdd"] * 100,
                     ("%.1f%%" % (h["cagr"] * 100)) if h else "-",
                     ("%.1f%%" % (h["maxdd"] * 100)) if h else "-"))
    print()
    print("chi tiet -> %s" % RA)
    print("LUU Y: day la PHEP DO. Cai nao qua ca hai chang van phai dang ky +")
    print("xac nhan mot lan qua `nhan/cong.py` truoc khi goi la phat hien.")


if __name__ == "__main__":
    chay()
