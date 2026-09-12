# -*- coding: utf-8 -*-
"""Chay LUONG 3 (noi sinh) tren mot ma + khung, dung quy trinh.

QUY TRINH (thu tu nay la de giu holdout sach):
  1. `hai_nua` -> TRAIN / HOLDOUT
  2. sinh co che tren TRAIN (nguong = phan vi cua TRAIN)
  3. cham diem TAT CA tren TRAIN, xep hang
  4. chi TOP-K duoc cham HOLDOUT
  5. bao cao kem canh bao boi so phep thu

KHONG dang ky gia thuyet, KHONG cham FDR (`ghi_so` khong duoc dung o day) —
day la buoc KHAM PHA. Ung vien nao song moi di tiep qua `cong`.
"""
from __future__ import annotations

#: Duoi so lenh nay o HOLDOUT thi phep thu CHUA CHAY DUOC, khong phai thua.
LENH_HO_TOI_THIEU = 10

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import bien_don_bay as B          # noqa: E402
from nhan import chi_phi as CP              # noqa: E402
from nhan import du_lieu as DU              # noqa: E402
from nhan import ngu_phap as NP             # noqa: E402
from nhan import noi_sinh as NS             # noqa: E402

BAO = Path(__file__).resolve().parent / "reports"


def _cham(df, spec, cp, ma, khung):
    """Sharpe cua co che va cua moc mua-giu tren CUNG doan df.

    Tra ve kem `so_lenh`. `bien_don_bay._chi_so` KHONG co khoa do - va lan dau
    toi viet `h.get("so_lenh")` thi no tra `None` cho moi dong, roi co
    `KHONG_KICH_HOAT` bat cho **ca 10/10** ung vien. Bao cao khi do noi "khong
    co gi kich hoat o holdout" trong khi that ra chua ai dem ca.
    Cung ho loi voi chinh cai no dinh bat: doc mot con so khong ton tai roi
    dung gia tri mac dinh nhu mot phep do.
    """
    import numpy as _np
    from nhan import mo_phong as _MP
    th = NP.sinh_tu_spec(spec, df)
    h = dict(B.do_bien(df, th, cp, cac_don_bay=(1.0,), co_tuc=False,
                       ma=ma, khung=khung)[0][0])
    v = _np.clip(_np.nan_to_num(_np.asarray(th, float).reshape(-1)), -1.0, 1.0)
    v = _np.r_[0.0, v[:-1]]          # engine dich mot bar, dem tren ban DA dich
    h["so_lenh"] = int(_MP.dem_lenh(v))
    return h


def _lenh(v, loi):
    out, i, n = [], 0, len(v)
    while i < n:
        if abs(v[i]) < 1e-12:
            i += 1
            continue
        j = i
        while j + 1 < n and abs(v[j + 1]) > 1e-12 and np.sign(v[j + 1]) == np.sign(v[i]):
            j += 1
        out.append(float(np.sum(loi[i:j + 1])))
        i = j + 1
    return np.array(out)


def chay(ma: str, khung: str, top_k: int = 10, cap: int = 2500,
         lenh_toi_thieu: int = 30):
    t0 = time.time()
    df = DU.nap(ma, khung)
    cp = CP.tu_du_lieu(ma, df)
    cp = cp[0] if isinstance(cp, tuple) else cp
    tr, ho = DU.hai_nua(df, 0.6)
    print(f"=== NOI SINH: {ma}.{khung} ===")
    print(f"  ca chuoi {len(df)} bar  {df.index[0].date()} -> {df.index[-1].date()}")
    print(f"  TRAIN   {len(tr):>6} bar  {tr.index[0].date()} -> {tr.index[-1].date()}")
    print(f"  HOLDOUT {len(ho):>6} bar  {ho.index[0].date()} -> {ho.index[-1].date()}")
    print(f"  spread do duoc {cp.spread_frac_chung*1e4:.2f} bps | "
          f"phi giu {cp.phi_nam_mua*100:.3f} %/nam | do_tin {cp.do_tin}")

    bh_tr = B.do_bien(tr, np.ones(len(tr)), cp, cac_don_bay=(1.0,), co_tuc=False,
                      ma=ma, khung=khung, da_dich=True)[0][0]
    bh_ho = B.do_bien(ho, np.ones(len(ho)), cp, cac_don_bay=(1.0,), co_tuc=False,
                      ma=ma, khung=khung, da_dich=True)[0][0]
    print(f"  moc mua-giu: TRAIN S={bh_tr['sharpe']:+.3f} (CAGR {bh_tr['cagr']*100:+.2f}%, "
          f"DD {bh_tr['maxdd']*100:.1f}%) | HOLDOUT S={bh_ho['sharpe']:+.3f} "
          f"(CAGR {bh_ho['cagr']*100:+.2f}%, DD {bh_ho['maxdd']*100:.1f}%)")

    specs = NS.sinh(tr) + NS.sinh_cap(tr, toi_da=cap)
    print(f"  sinh {len(specs)} co che tu chinh TRAIN ({time.time()-t0:.0f}s)")

    hang = []
    for s in specs:
        try:
            h = _cham(tr, s, cp, ma, khung)
        except Exception:
            continue
        th = NP.sinh_tu_spec(s, tr)
        v = np.zeros(len(tr))
        v[1:] = np.clip(np.nan_to_num(th), -1, 1)[:-1]
        n_lenh = len(_lenh(v, np.zeros(len(tr))))
        if n_lenh < lenh_toi_thieu:
            continue
        hang.append({"ten": s["ten"], "spec": s, "S_tr": h["sharpe"],
                     "chenh_tr": h["sharpe"] - bh_tr["sharpe"],
                     "cagr_tr": h["cagr"], "dd_tr": h["maxdd"],
                     "pn": h["phoi_nhiem"], "lenh": n_lenh})
    hang.sort(key=lambda r: -r["chenh_tr"])
    print(f"  cham diem xong: {len(hang)} co che du {lenh_toi_thieu} lenh "
          f"({time.time()-t0:.0f}s)")
    print(f"  vuot moc tren TRAIN: {sum(1 for r in hang if r['chenh_tr'] > 0)}")

    print(f"\n  -- TOP {top_k} tren TRAIN, gio cham HOLDOUT (lan duy nhat) --")
    print(f"  {'co che':<44}{'S_tr':>7}{'chenh_tr':>9}{'S_ho':>7}{'chenh_ho':>9}"
          f"{'lenh':>6}{'l_ho':>6}  ket")
    song = []
    for r in hang[:top_k]:
        try:
            h = _cham(ho, r["spec"], cp, ma, khung)
        except Exception:
            continue
        c_ho = h["sharpe"] - bh_ho["sharpe"]
        r["S_ho"], r["chenh_ho"] = h["sharpe"], c_ho
        # KHONG KICH HOAT khac han THUA. Do 12/09/2026: nguong lay tu phan vi
        # TRAIN la mot SO TUYET DOI; voi dai luong phu thuoc thang do, so do co
        # the nam NGOAI HAN phan phoi cua HOLDOUT:
        #   `atr14 < 0,003472` kich hoat 1.719 lan o TRAIN, **0 lan o HOLDOUT**
        # Sharpe khi do la 0,000; va vi moc holdout AM (-0,254) nen "chenh" ra
        # DUONG - bay trong top 10 khong vao lenh nao van duoc dem la "giu dau".
        # Mot he khong giao dich khong phai mot he thang.
        lenh_ho = int(h.get("so_lenh") or 0)
        r["lenh_ho"] = lenh_ho
        if lenh_ho < LENH_HO_TOI_THIEU:
            r["ket"] = "KHONG_KICH_HOAT"
        elif c_ho > 0:
            r["ket"] = "giu_dau"
            song.append(r)
        else:
            r["ket"] = "mat_dau"
        print(f"  {r['ten'][:43]:<44}{r['S_tr']:>7.3f}{r['chenh_tr']:>+9.3f}"
              f"{h['sharpe']:>7.3f}{c_ho:>+9.3f}{r['lenh']:>6}{lenh_ho:>6}"
              f"  {r['ket']}")

    im = [r for r in hang[:top_k] if r.get("ket") == "KHONG_KICH_HOAT"]
    print(f"\n  giu dau ngoai mau: {len(song)}/{min(top_k, len(hang))}")
    if im:
        print(f"  KHONG KICH HOAT o holdout: {len(im)}/{min(top_k, len(hang))}"
              f"  <- nguong tu TRAIN nam ngoai phan phoi HOLDOUT.")
        print(f"     Day KHONG phai ket qua am - la phep thu chua chay duoc.")
    print(f"  CANH BAO boi so phep thu: da cham diem {len(hang)} co che tren TRAIN; "
          f"nguong Bonferroni cho {top_k} lan nhin holdout la p < {0.05/max(top_k,1):.4f}")
    BAO.mkdir(exist_ok=True)
    pd.DataFrame([{k: v for k, v in r.items() if k != "spec"} for r in hang]).to_csv(
        BAO / f"noi_sinh_{ma.lower()}_{khung.lower()}.csv", index=False)
    print(f"  -> reports/noi_sinh_{ma.lower()}_{khung.lower()}.csv  "
          f"({time.time()-t0:.0f}s)")
    return song


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ma", default="US500CASH")
    ap.add_argument("--khung", default="H4")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--cap", type=int, default=2500)
    a = ap.parse_args()
    chay(a.ma, a.khung, top_k=a.top, cap=a.cap)
