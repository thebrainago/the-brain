# -*- coding: utf-8 -*-
"""_audcad_them_cap.py - CAP NAO GHEP DUOC vao he AUDCAD?

Chu du an 15/09/2026: *"xem la co ket hop duoc them cap nao vao he thong giao
dich khong."*

## Cach lam

8 cum da qua placebo tren AUDCAD la co che HOI QUY chung (RSI qua ban -> mua,
OU quay ve, pairs trading). Cau hoi: chung co edge tren cac cap CHEO khac
(AUDNZD, EURGBP...) khong, va cap do co DOC LAP voi AUDCAD khong?

Voi moi cap ung vien:
  1. Tinh vi the cua 8 cum tren holdout cua cap do (Python, cung engine).
  2. PLACEBO danh muc (hoan vi khoi vi the) - edge THAT hay chi phoi nhiem?
  3. TUONG QUAN chuoi von danh muc voi AUDCAD - co da dang hoa khong?

Cap DAT ca hai (qua placebo + tuong quan thap voi AUDCAD) thi ghep vao lam
tang Calmar - nang return ma KHONG tang rui ro tuong ung. Do la duong dung de
"27% it" thanh nhieu hon, khac han chi tang don bay.

## GIU NGUYEN, KHONG chon lai tren cap moi

KHONG chon lai 8 cum toi uu cho tung cap - do la overfit tung cap. Dung DUNG 8
cum da chon tren AUDCAD, thu nguyen si tren cap moi. Neu chung van an thi edge
la CUA HO CO CHE, khong phai cua mot cap.

Chay:  python _audcad_them_cap.py [--n 1500]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from _audcad_placebo import _pnl, _khoi_hoan_vi   # noqa: E402

TU, DEN = "2021-03-19", "2026-07-29"
UNG_VIEN = ["AUDNZD", "AUDCHF", "NZDCAD", "EURGBP", "EURCAD", "GBPCAD"]


def _pos_danh_muc(ten_cum: list, kho: dict, df) -> tuple:
    from nhan import ngu_phap as NP
    pos_ds = []
    for t in ten_cum:
        c = kho.get(t)
        if c is None:
            continue
        pos_ds.append(np.nan_to_num(np.asarray(NP.sinh_tu_spec(c, df), float)))
    n = min(len(x) for x in pos_ds)
    return np.sum([x[:n] for x in pos_ds], axis=0), pos_ds, n


def _placebo_dm(tong_pos, ret, n, n_null, rng) -> float:
    that = _pnl(tong_pos, ret)
    trong = (np.abs(tong_pos) > 0).astype(int)
    doi = np.sum(np.abs(np.diff(trong)))
    k = max(2, int(trong.sum() / max(doi / 2, 1)))
    null = np.array([_pnl(_khoi_hoan_vi(tong_pos, k, rng), ret)
                     for _ in range(n_null)])
    return float(np.mean(null >= that)), that


def main() -> int:
    from nhan import du_lieu as DL
    from nhan import ngu_phap as NP

    n_null = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 1500
    cum = json.loads((LAB / "reports" / "AUDCAD_CUM.json").read_text(encoding="utf-8"))
    ten_cum = [c["dai_dien"] for c in cum["cum"]]
    kho = {c.get("ten"): c for c in NP.doc_kho()}
    rng = np.random.default_rng(0)

    # AUDCAD lam moc: chuoi von danh muc de do tuong quan.
    df_au = DL.nap("AUDCAD", "H4", tu=TU, den=DEN)
    ret_au = np.concatenate([[0.0], np.diff(np.log(df_au["close"].to_numpy(float)))])
    pos_au, pos_ds_au, n_au = _pos_danh_muc(ten_cum, kho, df_au)
    von_au = np.cumsum(pos_au[:n_au - 1] * ret_au[1:n_au])

    print("=" * 78)
    print("CAP NAO GHEP DUOC vao he AUDCAD (8 cum hoi quy, giu nguyen)")
    print("=" * 78)
    print("%-8s %10s %9s %11s %s" % ("cap", "lai (don vi)", "placebo p",
                                     "r-von AUDCAD", "ket luan"))
    print("-" * 78)
    ghep = []
    for ma in UNG_VIEN:
        try:
            df = DL.nap(ma, "H4", tu=TU, den=DEN)
        except Exception as e:
            print("%-8s -- %s" % (ma, str(e)[:50]))
            continue
        ret = np.concatenate([[0.0], np.diff(np.log(df["close"].to_numpy(float)))])
        tong, _, n = _pos_danh_muc(ten_cum, kho, df)
        p, lai = _placebo_dm(tong, ret, n, n_null, rng)
        von = np.cumsum(tong[:n - 1] * ret[1:n])
        m = min(len(von), len(von_au))
        r = (float(np.corrcoef(np.diff(von[:m]), np.diff(von_au[:m]))[0, 1])
             if m > 50 and np.std(np.diff(von[:m])) > 0 else float("nan"))
        qua = p < 0.05
        doc_lap = abs(r) < 0.5 if np.isfinite(r) else False
        kl = ("GHEP" if qua and doc_lap else
              "qua placebo nhung tuong quan cao" if qua else "khong qua placebo")
        if qua and doc_lap:
            ghep.append(ma)
        print("%-8s %+11.4f %9.4f %11s  %s"
              % (ma, lai, p, ("%.3f" % r if np.isfinite(r) else "-"), kl))

    print("-" * 78)
    print("CAP GHEP DUOC (qua placebo + doc lap voi AUDCAD): %s"
          % (", ".join(ghep) or "khong cap nao"))
    if ghep:
        print("-> ghep %d cap nay + AUDCAD lam DANH MUC DA TAI SAN: da dang hoa"
              % (len(ghep) + 1))
        print("   nang return o cung DD, roi tang don bay den muc rui ro muon.")
    (LAB / "reports" / "AUDCAD_THEM_CAP.json").write_text(
        json.dumps({"ghep_duoc": ghep, "ung_vien": UNG_VIEN},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
