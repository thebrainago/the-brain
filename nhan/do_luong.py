# -*- coding: utf-8 -*-
"""do_luong.py - CHI SO + ALPHA SO VOI MUA-GIU.

Diem khac ban cu: moc so sanh chinh la MUA-GIU CFD SAU PHI (`buyhold_net`),
khong phai chi so khong phi. Va co `alpha_newey_west` - thu duy nhat chan duoc
DON BAY TRA HINH: neu chien luoc chi la mua-giu phoi nhiem day thi alpha ~ 0
theo cau tao, du loi suat tuyet doi rat dep.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRONG_NAM = 365.25 * 24 * 3600


def bar_moi_nam(index: pd.DatetimeIndex) -> float:
    if len(index) < 3:
        return 252.0
    giay = (index[-1] - index[0]).total_seconds()
    if giay <= 0:
        return 252.0
    return len(index) * TRONG_NAM / giay


def chi_so(loi: np.ndarray, index: pd.DatetimeIndex, vi_the: np.ndarray | None = None) -> dict:
    """Chi so tu chuoi loi suat LOG rong tung bar."""
    loi = np.nan_to_num(np.asarray(loi, dtype=float))
    if len(loi) < 3:
        return {"loi": "qua ngan"}
    bmn = bar_moi_nam(index)
    so_nam = len(loi) / bmn
    von = np.exp(np.cumsum(loi))
    tong = float(von[-1] - 1.0)
    cagr = float(von[-1] ** (1.0 / so_nam) - 1.0) if so_nam > 0 and von[-1] > 0 else float("nan")
    sd = float(np.std(loi, ddof=1))
    sharpe = float(np.mean(loi) / sd * np.sqrt(bmn)) if sd > 0 else float("nan")
    dinh = np.maximum.accumulate(von)
    sut = von / dinh - 1.0
    max_dd = float(np.min(sut))
    calmar = float(cagr / abs(max_dd)) if max_dd < -1e-12 and np.isfinite(cagr) else float("nan")
    lai = float(np.sum(loi[loi > 0]))
    lo = float(-np.sum(loi[loi < 0]))
    pf = float(lai / lo) if lo > 1e-12 else float("nan")
    ra = {
        "tong_lai_pct": round(tong * 100, 2),
        "cagr_pct": round(cagr * 100, 3) if np.isfinite(cagr) else None,
        "sharpe": round(sharpe, 3) if np.isfinite(sharpe) else None,
        "calmar": round(calmar, 3) if np.isfinite(calmar) else None,
        "max_dd_pct": round(max_dd * 100, 2),
        "pf": round(pf, 3) if np.isfinite(pf) else None,
        "so_nam": round(so_nam, 2),
        "so_bar": int(len(loi)),
    }
    if vi_the is not None:
        ra["phoi_nhiem"] = round(float(np.mean(np.abs(vi_the))), 4)
        ra["ty_le_mua"] = round(float(np.mean(vi_the > 0)), 4)
        ra["ty_le_ban"] = round(float(np.mean(vi_the < 0)), 4)
    return ra


def alpha_newey_west(loi_he: np.ndarray, loi_moc: np.ndarray,
                     index: pd.DatetimeIndex | None = None) -> tuple[float, float, float]:
    """Hoi quy loi suat he len loi suat MUA-GIU, sai so chuan Newey-West (HAC).

    Tra (alpha_nam, t_alpha, beta). alpha da quy ve %/nam.
    Day la cong so 4 cua THIET_KE muc 2 - chan don bay tra hinh.
    """
    y = np.nan_to_num(np.asarray(loi_he, dtype=float))
    x = np.nan_to_num(np.asarray(loi_moc, dtype=float))
    n = min(len(y), len(x))
    y, x = y[:n], x[:n]
    if n < 30 or np.std(x) < 1e-15:
        return float("nan"), float("nan"), float("nan")
    bmn = bar_moi_nam(index) if index is not None else 252.0
    lag = int(max(1, np.floor(4 * (n / 100.0) ** (2.0 / 9.0))))
    try:
        import statsmodels.api as sm
        X = sm.add_constant(x)
        kq = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
        a, b = float(kq.params[0]), float(kq.params[1])
        t = float(kq.tvalues[0])
    except Exception:
        # du phong: OLS tay + HAC Newey-West tu tinh
        X = np.column_stack([np.ones(n), x])
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        e = y - X @ beta
        XtX_inv = np.linalg.inv(X.T @ X)
        S = (X * e[:, None]).T @ (X * e[:, None])
        for L in range(1, lag + 1):
            w = 1.0 - L / (lag + 1.0)
            u = (X * e[:, None])
            G = u[L:].T @ u[:-L]
            S += w * (G + G.T)
        V = XtX_inv @ S @ XtX_inv
        a, b = float(beta[0]), float(beta[1])
        t = a / np.sqrt(V[0, 0]) if V[0, 0] > 0 else float("nan")
    return a * bmn, t, b


def so_sanh(kq_he, kq_bh_net, kq_bh_tho=None) -> dict:
    """Bang so sanh day du: he / mua-giu CFD sau phi / chi so khong phi."""
    idx = kq_he.index
    ra = {
        "he": chi_so(kq_he.loi, idx, kq_he.vi_the),
        "mua_giu_net": chi_so(kq_bh_net.loi, kq_bh_net.index, kq_bh_net.vi_the),
    }
    if kq_bh_tho is not None:
        ra["chi_so_khong_phi"] = chi_so(kq_bh_tho.loi, kq_bh_tho.index)
    a, t, b = alpha_newey_west(kq_he.loi, kq_bh_net.loi, idx)
    ra["alpha_vs_mua_giu"] = {
        "alpha_nam_pct": round(a * 100, 3) if np.isfinite(a) else None,
        "t_alpha": round(t, 3) if np.isfinite(t) else None,
        "beta": round(b, 3) if np.isfinite(b) else None,
    }
    tong_cp = kq_he.chi_phi_spread + kq_he.chi_phi_truot + kq_he.chi_phi_giu
    ra["chi_phi"] = {
        "spread_pct": round(kq_he.chi_phi_spread * 100, 3),
        "truot_gia_pct": round(kq_he.chi_phi_truot * 100, 3),
        "phi_qua_dem_pct": round(kq_he.chi_phi_giu * 100, 3),
        "tong_pct": round(tong_cp * 100, 3),
        "phi_qua_dem_ty_trong": round(kq_he.chi_phi_giu / tong_cp, 3) if tong_cp > 1e-12 else None,
    }
    ra["hoat_dong"] = {"so_lenh": kq_he.so_lenh, "so_lan_doi": kq_he.so_lan_doi,
                       "lenh_moi_tuan": round(kq_he.so_lenh /
                                              max(ra["he"].get("so_nam", 1) * 52, 1e-9), 2)}
    return ra


def hieu_qua_giai_doan(loi: np.ndarray, index: pd.DatetimeIndex, k: int = 4) -> list[dict]:
    """Chia k giai doan lien tuc bang nhau, do tung cai.

    Bai hoc IBS: 64 nam CAGR -0,08% ma hai nua deu duong vi CUNG MOT THOI DAI.
    Chia nho hon giup thay, nhung khong thay duoc mot phep kiem phi dung.
    """
    n = len(loi)
    ra = []
    for i in range(k):
        a, b = i * n // k, (i + 1) * n // k if i < k - 1 else n
        if b - a < 20:
            continue
        c = chi_so(loi[a:b], index[a:b])
        ra.append({"tu": str(index[a])[:10], "den": str(index[b - 1])[:10],
                   "cagr_pct": c.get("cagr_pct"), "sharpe": c.get("sharpe")})
    return ra
