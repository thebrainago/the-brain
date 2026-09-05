# -*- coding: utf-8 -*-
"""tinh_cach.py - DO TINH CACH TAI SAN bang so hoc: hoi quy hay xu huong?

Chu du an 05/09/2026: *"He thong can chon loai tai san: he CAD co ve phu hop cho
mean-revert vi co tinh chat hoi quy, he BTC XAU hop danh breakout va follow trend
vi no co trend. Co cach nao dung so hoc phan tich duoc nhung dac diem nay khong?"*

Co, va day la sau thuoc do da duoc kiem chung trong tai lieu. Nhung diem quan
trong khong phai TINH duoc chung - ai cung tinh duoc - ma la **chung co du bao
duoc khong**. Nen module nay di kem mot buoc doi chieu: lay chinh 37.060 phep do
(262 co che x 194 ma, da gan nhan ho `xu_huong`/`quay_ve_trung_binh`/`pha_vo`)
lam su that, roi hoi: thuoc do nao xep hang dung?

## SAU THUOC DO

  `hurst`     Mu Hurst bang R/S. **H < 0,5 = hoi quy · H > 0,5 = xu huong ·
              H = 0,5 = buoc ngau nhien.** Thuoc do co dien nhat, nhung uoc
              luong tren chuoi ngan lech len tren (thien ve 0,5+).
  `vr2/vr10`  **Ty so phuong sai (Lo-MacKinlay)**: Var(r_q)/(q*Var(r_1)).
              VR < 1 = hoi quy · VR > 1 = xu huong. Kem z-stat nen NOI DUOC
              khac 1 co y nghia khong - day la uu the that so voi Hurst.
  `ac1`       Tu tuong quan loi suat tre 1. Am = hoi quy.
  `nua_doi`   Nua doi hoi quy (khop Ornstein-Uhlenbeck): `-ln2/lambda` voi
              `dr = lambda*r + e`. Don vi BAR. Nho = hoi quy nhanh.
  `er`        Ty so hieu qua Kaufman = |quang duong rong| / tong |buoc di|.
              Cao = di thang (xu huong) · thap = di long vong (hoi quy).

## CACH DOC - va mot canh bao

Ba thuoc do dau (hurst, vr, ac1) do **cung mot thu** theo ba duong khac nhau nen
chung tuong quan cao; dung chung nhu ba bang chung doc lap la dem mot bang chung
ba lan. `nua_doi` va `er` moi them thong tin: mot cai noi TOC DO hoi quy, mot cai
noi HINH DANG duong di.

Va tat ca deu do tren TOAN CHUOI. Mot tai san co the hoi quy o khung gio nhung
xu huong o khung ngay - nen phai do theo dung KHUNG se giao dich.
"""
from __future__ import annotations

import numpy as np


def _loi_suat(gia: np.ndarray) -> np.ndarray:
    g = np.asarray(gia, float)
    g = g[np.isfinite(g) & (g > 0)]
    return np.diff(np.log(g))


def hurst(gia: np.ndarray, cac_n=(8, 16, 32, 64, 128, 256)) -> float | None:
    """Mu Hurst bang R/S tren nhieu do dai cua so, hoi quy log-log."""
    r = _loi_suat(gia)
    if len(r) < max(cac_n) * 4:
        return None
    x, y = [], []
    for n in cac_n:
        so = len(r) // n
        if so < 4:
            continue
        m = r[: so * n].reshape(so, n)
        z = m - m.mean(axis=1, keepdims=True)
        tich = np.cumsum(z, axis=1)
        R = tich.max(axis=1) - tich.min(axis=1)
        S = m.std(axis=1, ddof=1)
        ok = S > 0
        if ok.sum() < 2:
            continue
        x.append(np.log(n))
        y.append(np.log((R[ok] / S[ok]).mean()))
    if len(x) < 3:
        return None
    return float(np.polyfit(x, y, 1)[0])


def ty_so_phuong_sai(gia: np.ndarray, q: int = 2) -> tuple[float, float] | None:
    """(VR, z) theo Lo-MacKinlay, phien ban chiu duoc phuong sai thay doi.

    VR < 1 = hoi quy, > 1 = xu huong. |z| > 1,96 = khac 1 co y nghia 5%.
    """
    r = _loi_suat(gia)
    n = len(r)
    if n < q * 20:
        return None
    mu = r.mean()
    var1 = np.sum((r - mu) ** 2) / (n - 1)
    if var1 <= 0:
        return None
    rq = np.convolve(r, np.ones(q), "valid")
    m = q * (n - q + 1) * (1 - q / n)
    varq = np.sum((rq - q * mu) ** 2) / m
    vr = varq / var1
    # phuong sai tiem can chiu duoc heteroskedasticity
    d = 0.0
    for j in range(1, q):
        so = np.sum(((r[j:] - mu) ** 2) * ((r[:-j] - mu) ** 2))
        mau = (np.sum((r - mu) ** 2)) ** 2
        if mau > 0:
            d += (2.0 * (q - j) / q) ** 2 * (so / mau) * n
    z = (vr - 1.0) / np.sqrt(d) if d > 0 else np.nan
    return float(vr), float(z)


def tu_tuong_quan(gia: np.ndarray, tre: int = 1) -> float | None:
    r = _loi_suat(gia)
    if len(r) < 100:
        return None
    a, b = r[tre:], r[:-tre]
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def nua_doi(gia: np.ndarray) -> float | None:
    """Nua doi hoi quy ve trung binh, don vi BAR (khop OU tren log gia)."""
    g = np.asarray(gia, float)
    g = g[np.isfinite(g) & (g > 0)]
    if len(g) < 200:
        return None
    y = np.log(g)
    y_tre = y[:-1]
    dy = np.diff(y)
    x = y_tre - y_tre.mean()
    if x.std() == 0:
        return None
    lam = float(np.polyfit(x, dy, 1)[0])
    if lam >= 0:
        return float("inf")          # khong hoi quy
    return float(-np.log(2.0) / lam)


def ty_so_hieu_qua(gia: np.ndarray, n: int = 100) -> float | None:
    """Kaufman Efficiency Ratio trung binh: |quang duong rong| / tong |buoc di|."""
    g = np.asarray(gia, float)
    g = g[np.isfinite(g)]
    if len(g) < n * 3:
        return None
    b = np.abs(np.diff(g))
    tong = np.convolve(b, np.ones(n), "valid")
    rong = np.abs(g[n:] - g[:-n])
    m = min(len(tong), len(rong))
    ok = tong[:m] > 0
    if ok.sum() < 10:
        return None
    return float(np.mean(rong[:m][ok] / tong[:m][ok]))


def ho_so(gia: np.ndarray) -> dict:
    """Toan bo ho so tinh cach cua mot chuoi gia."""
    vr2 = ty_so_phuong_sai(gia, 2)
    vr10 = ty_so_phuong_sai(gia, 10)
    nd = nua_doi(gia)
    return {
        "hurst": hurst(gia),
        "vr2": vr2[0] if vr2 else None, "vr2_z": vr2[1] if vr2 else None,
        "vr10": vr10[0] if vr10 else None, "vr10_z": vr10[1] if vr10 else None,
        "ac1": tu_tuong_quan(gia, 1),
        "nua_doi_bar": (None if nd is None else
                        (float("inf") if not np.isfinite(nd) else nd)),
        "er": ty_so_hieu_qua(gia),
    }


#: Nguong TUONG DOI, do tu chinh kho 194 ma ngay 05/09. KHONG dung nguong
#: tuyet doi kieu "Hurst < 0,5 = hoi quy": uoc luong Hurst tren chuoi tai chinh
#: **lech len tren** co he thong - do that thi 157/157 ma deu co H > 0,5, ke ca
#: nhung ma ma co che hoi quy chay tot nhat (US500 0,553). Dung nguong tuyet doi
#: se gan nhan TRUNG_TINH cho tat ca va thuoc do thanh vo dung.
#: Cai co gia tri la XEP HANG, khong phai gia tri tuyet doi.
NGUONG = {"hurst": (0.565, 0.590), "vr10": (0.90, 1.00), "er": (0.10, 0.13)}


def nhan(h: dict, nguong: dict | None = None) -> str:
    """Mot nhan gon: HOI_QUY | XU_HUONG | TRUNG_TINH.

    Bo phieu tren ba thuoc do doc lap nhat co the: Hurst, VR(10), ER. Khong dung
    ca vr2 lan vr10 lan ac1 vi chung do cung mot thu - do se la dem mot bang
    chung ba lan. (Va do 05/09: vr2 va ac1 **khong du bao duoc** - tuong quan
    +0,044 va +0,042 voi ket qua that; chi thuoc do TAM DAI moi du bao duoc:
    hurst -0,567 · er -0,348 · vr10 -0,256 tren 157 ma.)
    """
    ng = nguong or NGUONG
    phieu = 0
    for k in ("hurst", "vr10", "er"):
        v = h.get(k)
        if v is None or not np.isfinite(v):
            continue
        lo, hi = ng[k]
        phieu += 1 if v > hi else (-1 if v < lo else 0)
    return "XU_HUONG" if phieu >= 2 else ("HOI_QUY" if phieu <= -2 else "TRUNG_TINH")
