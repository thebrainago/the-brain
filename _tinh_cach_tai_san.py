# -*- coding: utf-8 -*-
"""Do TINH CACH tai san roi DOI CHIEU voi ket qua that de xem no co du bao khong.

Chu du an 05/09: *"He CAD co ve phu hop cho mean-revert vi co tinh chat hoi quy,
he BTC XAU hop danh breakout va follow trend. Co cach nao dung so hoc phan tich
duoc nhung dac diem nay khong?"*

Tinh duoc Hurst/VR/half-life thi de. Cau hoi that la **chung co du bao duoc
khong**. Nen file nay lam hai viec, va viec thu hai moi quan trong:

  1. Do 6 thuoc do tinh cach cho moi ma D1 trong kho.
  2. **DOI CHIEU** voi `reports/quet_rong_d1.json` - 37.060 phep do that cua
     262 co che x 194 ma, moi co che da co nhan ho (`xu_huong` /
     `quay_ve_trung_binh` / `pha_vo` / `bien_dong`). Hoi: thuoc do tinh cach co
     xep hang dung khong - tuc tren ma duoc cham nhan HOI QUY thi co che ho
     `quay_ve_trung_binh` co that su chay tot hon ho `xu_huong` khong?

Neu buoc 2 khong ra gi thi buoc 1 chi la mot bang so dep. Chi buoc 2 moi bien
no thanh CONG CU CHON TAI SAN.
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np
from pathlib import Path

KHUNG = "D1"
NGUON = "reports/quet_rong_d1.json"
RA = "reports/tinh_cach_tai_san.json"
SO_LUONG = int(os.environ.get("LUONG", "10"))


def _mot(ma: str) -> dict | None:
    import warnings as w
    w.filterwarnings("ignore")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from nhan import du_lieu as DL
    from nhan import tinh_cach as TC
    try:
        d = DL.nap(ma, KHUNG)
        if DL.nguon_tai_san(ma) == "ngoai":
            d = DL.cat_theo_chat_luong(d, ma)[0]
        if len(d) < 600:
            return None
        h = TC.ho_so(d["close"].to_numpy(float))
        h["ma"] = ma
        h["so_bar"] = len(d)
        h["nhan"] = TC.nhan(h)
        return h
    except Exception:
        return None


def chay() -> None:
    from nhan import du_lieu as DL

    mas = sorted(DL.kho())
    print("=" * 92)
    print("TINH CACH TAI SAN - %d ma, khung %s" % (len(mas), KHUNG))
    print("=" * 92)
    ho = []
    with ProcessPoolExecutor(max_workers=SO_LUONG) as ex:
        fu = {ex.submit(_mot, m): m for m in mas}
        for f in as_completed(fu):
            r = f.result()
            if r:
                ho.append(r)
    print("do duoc %d/%d ma\n" % (len(ho), len(mas)))
    json.dump(ho, open(RA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ------------------------------------------------ bang cho vai ma quen
    quen = ["AUDCAD", "EURCAD", "NZDCAD", "USDCAD", "TS_BTC", "TS_ETH",
            "YH_VANG", "XAUUSD", "XM_US100CASH", "XM_US500CASH", "SP500",
            "EURUSD", "USDJPY", "YH_DAX"]
    ix = {h["ma"]: h for h in ho}
    print("--- MA QUEN THUOC ---")
    print("  %-16s %7s %7s %7s %8s %10s %7s  %s"
          % ("ma", "hurst", "VR(2)", "VR(10)", "ac1", "nua doi", "ER", "nhan"))
    for m in quen:
        h = ix.get(m)
        if not h:
            continue
        f = lambda v, n=3: "-" if v is None else ("inf" if not np.isfinite(v)
                                                  else "%.*f" % (n, v))
        print("  %-16s %7s %7s %7s %8s %10s %7s  %s"
              % (m, f(h["hurst"]), f(h["vr2"]), f(h["vr10"]), f(h["ac1"]),
                 f(h["nua_doi_bar"], 0), f(h["er"]), h["nhan"]))
    print()

    # ------------------------------------------- DOI CHIEU voi ket qua that
    try:
        kq = json.load(open(NGUON, encoding="utf-8"))
    except Exception:
        print("khong doc duoc %s - bo qua buoc doi chieu" % NGUON)
        return

    theo = defaultdict(lambda: defaultdict(list))
    for x in kq:
        s = x.get("sharpe_gop")
        if s is None or x.get("ho") is None:
            continue
        theo[x["ma"]][x["ho"]].append(s)

    print("--- DOI CHIEU: thuoc do co DU BAO duoc khong? ---")
    print("Voi moi ma: hieu Sharpe trung vi cua ho `quay_ve_trung_binh` tru ho")
    print("`xu_huong`. Duong = ma do HOP hoi quy hon. Roi tuong quan hieu do voi")
    print("tung thuoc do tinh cach. |tuong quan| cao = thuoc do du bao duoc.\n")
    cap = []
    for m, d in theo.items():
        if "quay_ve_trung_binh" not in d or "xu_huong" not in d:
            continue
        if len(d["quay_ve_trung_binh"]) < 8 or len(d["xu_huong"]) < 8:
            continue
        h = ix.get(m)
        if not h:
            continue
        cap.append((m, float(np.median(d["quay_ve_trung_binh"])
                             - np.median(d["xu_huong"])), h))
    print("  so ma doi chieu duoc: %d" % len(cap))
    if len(cap) < 20:
        print("  qua it de ket luan.")
        return
    y = np.array([c[1] for c in cap])
    print("  %-14s %10s %10s %s" % ("thuoc do", "tuong quan", "|r|", "doc the nao"))
    for k, chieu in (("hurst", -1), ("vr2", -1), ("vr10", -1), ("ac1", -1),
                     ("er", -1)):
        x = np.array([(c[2].get(k) if c[2].get(k) is not None else np.nan)
                      for c in cap], float)
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() < 20:
            continue
        r = float(np.corrcoef(x[ok], y[ok])[0, 1])
        doc = ("dung chieu: thap = hop hoi quy" if r * chieu > 0
               else "NGUOC chieu ky vong")
        print("  %-14s %10.3f %10.3f  %s" % (k, r, abs(r), doc))
    print()
    print("  Ky vong: ca 5 thuoc do deu phai AM (gia tri thap = hoi quy hon =")
    print("  ho quay_ve_trung_binh chay tot hon). Cai nao duong la thuoc do do")
    print("  KHONG du bao duoc tren kho nay.")

    # top/bottom theo hieu
    cap.sort(key=lambda c: -c[1])
    print()
    print("  --- 8 ma HOP HOI QUY NHAT (theo ket qua that) ---")
    for m, dv, h in cap[:8]:
        print("    %-16s hieu %+.3f | hurst %s  VR10 %s  ER %s  -> %s"
              % (m, dv, "%.3f" % h["hurst"] if h["hurst"] else "-",
                 "%.3f" % h["vr10"] if h["vr10"] else "-",
                 "%.3f" % h["er"] if h["er"] else "-", h["nhan"]))
    print("  --- 8 ma HOP XU HUONG NHAT ---")
    for m, dv, h in cap[-8:]:
        print("    %-16s hieu %+.3f | hurst %s  VR10 %s  ER %s  -> %s"
              % (m, dv, "%.3f" % h["hurst"] if h["hurst"] else "-",
                 "%.3f" % h["vr10"] if h["vr10"] else "-",
                 "%.3f" % h["er"] if h["er"] else "-", h["nhan"]))
    print()
    print("chi tiet -> %s" % RA)


if __name__ == "__main__":
    chay()
