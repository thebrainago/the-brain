# -*- coding: utf-8 -*-
r"""kiem_dinh.py - BO KIEM DINH NGHIEM NGAT cho QUANTLAB (hoc tu cach moc xe SP500 cua chu).
- du_mau   : du so lenh de co y nghia thong ke.
- placebo  : so sanh loi that voi phan phoi loi ngau nhien (shuffle vi the) -> p-value.
- era_split: split 2 mien thoi gian, doi edge o ca 2 (out-of-sample).
- sang_loc : tong hop cac cong, tra phan quyet (dat/khong dat).
"""
import numpy as np
import pandas as pd
import metrics

NGUONG_LENH = 30
P_NGUONG = 0.05


def du_mau(so_lenh, nguong=NGUONG_LENH):
    return so_lenh >= nguong


def placebo(close, pos, loai, n_perm=199, seed=42):
    """p-value: ti le shuffle vi the co loi >= loi that (gross). Nho = that that."""
    r = close.pct_change().fillna(0.0).to_numpy()
    pos_arr = pos.to_numpy()
    real = float((pos_arr * r).sum())
    rng = np.random.default_rng(seed)
    trailaoi = 0
    for _ in range(n_perm):
        sh = rng.permutation(pos_arr)
        if (sh * r).sum() >= real:
            trailaoi += 1
    p = (trailaoi + 1) / (n_perm + 1)
    return p, real


def era_split(close, pos, loai, k=2):
    """Chia k mien lien tuc, tinh edge moi mien. Tra danh sach edge_pct."""
    n = len(close)
    edges = []
    for i in range(k):
        sli = slice(i * n // k, (i + 1) * n // k if i < k - 1 else n)
        c, p = close.iloc[sli], pos.iloc[sli]
        kq = metrics.tong_hop(c, p, loai, "era", params={})
        th = (kq["co_che"]["tong_lai_pct"] or 0) - (kq["buy_hold"]["tong_lai_pct"] or 0)
        edges.append(round(float(th), 2))
    return edges


def sang_loc(close, pos, loai, so_lenh, n_perm=199, nguong_lenh=NGUONG_LENH):
    kq = metrics.tong_hop(close, pos, loai, "sang_loc", params={})
    lai = float(kq["co_che"]["tong_lai_pct"] or 0)
    bh = float(kq["buy_hold"]["tong_lai_pct"] or 0)
    pf = float(kq["co_che"]["pf"] or 0)
    sharpe = float(kq["co_che"]["sharpe"] or 0)
    edge = lai - bh
    p, _ = placebo(close, pos, loai, n_perm=n_perm)
    eras = era_split(close, pos, loai)
    ok_mau = du_mau(so_lenh, nguong_lenh)
    ok_placebo = p < P_NGUONG
    ok_era = all(e > 0 for e in eras)
    ok_edge = edge > 0 and pf > 1.0 and sharpe > 0
    dat = ok_mau and ok_placebo and ok_era and ok_edge
    return {
        "lai": round(lai, 2), "buy_hold": round(bh, 2), "edge": round(edge, 2),
        "pf": round(pf, 3), "sharpe": round(sharpe, 3), "so_lenh": so_lenh,
        "placebo_p": round(p, 3), "era_edges": eras,
        "ok_mau": ok_mau, "ok_placebo": ok_placebo, "ok_era": ok_era, "ok_edge": ok_edge,
        "dat": dat,
    }
