# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import numpy as np
import pandas as pd

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import du_lieu as DL
    from nhan import mo_phong as MP
    from nhan import sang_loc as SL
else:
    from . import du_lieu as DL
    from . import mo_phong as MP
    from . import sang_loc as SL

HAT = 4242
SO_NULL_TOI_THIEU = 200

# ============================================================== NULL FACTORY

def _block_bootstrap(r, hat, block_size=None):
    n = len(r)
    if block_size is None:
        block_size = max(20, min(60, n // 20))
    rng = np.random.default_rng(hat)
    n_blocks = int(np.ceil(n / block_size))
    starts = rng.integers(0, n - block_size, size=n_blocks)
    out = np.concatenate([r[s:s + block_size] for s in starts])
    return out[:n]

def null_block_bootstrap(ma, khung, so_chuoi=SO_NULL_TOI_THIEU, hat=HAT):
    df = DL.nap(ma, khung)
    r = MP._loi_suat_tien(df)
    r = r[r != 0]
    if len(r) < 200:
        return []
    ra = []
    for i in range(so_chuoi):
        ra.append(_block_bootstrap(r, hat + i))
    return ra

def _garch11_sim(r, hat):
    rng = np.random.default_rng(hat)
    n = len(r)
    var_r = np.var(r)
    alpha = 0.10
    beta = 0.85
    omega = max(var_r * (1 - alpha - beta), 1e-12)
    sigma2 = np.ones(n) * var_r
    eps = np.zeros(n)
    for t in range(1, n):
        sigma2[t] = omega + alpha * (eps[t-1]**2) + beta * sigma2[t-1]
        eps[t] = rng.normal(0, np.sqrt(sigma2[t]))
    return eps

def null_garch(ma, khung, so_chuoi=SO_NULL_TOI_THIEU, hat=HAT):
    df = DL.nap(ma, khung)
    r = MP._loi_suat_tien(df)
    r = r[r != 0]
    if len(r) < 200:
        return []
    ra = []
    for i in range(so_chuoi):
        ra.append(_garch11_sim(r, hat + i))
    return ra

def null_permute_time(ma, khung, so_chuoi=SO_NULL_TOI_THIEU, hat=HAT):
    df = DL.nap(ma, khung)
    r = MP._loi_suat_tien(df)
    r = r[r != 0]
    n = len(r)
    if n < 200:
        return []
    rng = np.random.default_rng(hat)
    ra = []
    for i in range(so_chuoi):
        ra.append(r[rng.permutation(n)])
    return ra

def bar_tu_chuoi_null(r_null, df_mau, hat=HAT):
    """Mang loi suat null -> khung bar OHLC de chay duoc qua pheu.

    Ba ham `null_*` o tren tra ve MANG LOI SUAT, con pheu can BAR (co
    open/high/low/close de tinh IBS, bien do, than nen...). Khong co buoc nay
    thi nha may null khong the noi vao pheu duoc - va do la ly do no chua tung
    chay lan nao du da viet xong.

    Cach dung bar: lay HINH DANG bar cua chuoi that lam khuon (cap `ibs` va
    `bien_do/gia`), nhung **xao tron thu tu** cua chung roi gan len duong gia
    null. Nho the:
      - IBS van co phan phoi that (khong phai 0,5 o moi bar nhu bar tong hop ngay tho),
      - nhung IBS cua bar i KHONG con lien quan gi toi loi suat bar i+1.
    Do dung la gia thuyet null can kiem: "hinh dang bar khong du bao gi ca".
    """
    r = np.asarray(r_null, dtype=float).reshape(-1)
    n = len(r)
    if n < 200 or df_mau is None or len(df_mau) < n:
        return None
    mau = df_mau.iloc[:n]
    ibs, rong = _ibs_cua(mau)
    c_mau = mau["close"].to_numpy(float)
    o_mau = mau["open"].to_numpy(float)
    ty_rong = rong / np.where(c_mau > 0, c_mau, 1e-12)
    ty_open = o_mau / np.where(c_mau > 0, c_mau, 1e-12)

    rng = np.random.default_rng(hat)
    hv = rng.permutation(n)                 # xao tron HINH DANG bar
    ibs_x, ty_rong_x, ty_open_x = ibs[hv], ty_rong[hv], ty_open[hv]

    c = float(c_mau[0]) * np.exp(np.cumsum(r))
    rong_moi = ty_rong_x * c
    low = c - ibs_x * rong_moi
    d = mau.copy()
    d["close"] = c
    d["low"] = low
    d["high"] = low + rong_moi
    d["open"] = ty_open_x * c
    return d


def chay_pheu_tren_null(ma="US500CASH", khung="D1", so_chuoi=200,
                        phuong_phap="block_bootstrap", hat=HAT, cp=None):
    """Chay CA PHEU tren chuoi null. Tra ty le lot o tung vong.

    Day la chieu con lai cua bai kiem hai chieu: nha may LUC noi cong co bo sot
    edge that khong; nha may NULL noi cong co nhan bua khong. Mot cong tu choi
    tat ca dat bai kiem null voi diem tuyet doi - nen hai so nay chi co nghia
    khi doc CUNG NHAU.
    """
    df = DL.nap(ma, khung)
    if cp is None:
        cp = SL._chi_phi_cua(ma)
    chuoi = tao_null(ma, khung, "", so_chuoi=so_chuoi,
                     phuong_phap=phuong_phap, hat=hat)
    bao = {"tai_san": ma, "khung": khung, "phuong_phap": phuong_phap,
           # `so_loi` chu khong phai `loi`: khoa `loi` o khap he nay nghia la
           # "ham nay that bai", nen dung no cho mot BO DEM bang 0 lam moi cho
           # kiem `if r.get("loi")` hieu nham.
           "so_chuoi": 0, "lot": 0, "dung_o_vong": {}, "so_loi": 0}
    for i, r in enumerate(chuoi):
        d = bar_tu_chuoi_null(r, df, hat=hat + i)
        if d is None:
            bao["so_loi"] += 1
            continue
        SL.xoa_bo_dem()
        try:
            kq = SL.chay_pheu(MAU_CAY, {"nguong": NGUONG_IBS}, ma, khung,
                              df=d, cp=cp, pham_vi=None)
        except Exception:
            bao["so_loi"] += 1
            continue
        bao["so_chuoi"] += 1
        bao["dung_o_vong"][kq["vong"]] = bao["dung_o_vong"].get(kq["vong"], 0) + 1
        if kq["ket_luan"] == SL.SAN_SANG_V4:
            bao["lot"] += 1
    bao["ty_le_lot_pct"] = round(100.0 * bao["lot"] / max(bao["so_chuoi"], 1), 2)
    return bao


def null_day_du(ma="US500CASH", khung="D1", so_chuoi=SO_NULL_TOI_THIEU, hat=HAT):
    """Ca ba phuong phap null. Moi phuong phap pha mot thu khac nhau, nen ba
    con so cung nhau moi noi duoc cong co nhan bua khong."""
    ra = {"tai_san": ma, "khung": khung, "so_chuoi_moi_pp": so_chuoi, "theo_pp": {}}
    for pp in ("block_bootstrap", "garch", "permute_time"):
        try:
            ra["theo_pp"][pp] = chay_pheu_tren_null(ma, khung, so_chuoi, pp, hat)
        except Exception as e:
            ra["theo_pp"][pp] = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}
    tot = [v.get("ty_le_lot_pct") for v in ra["theo_pp"].values()
           if isinstance(v.get("ty_le_lot_pct"), (int, float))]
    ra["ty_le_lot_cao_nhat_pct"] = max(tot) if tot else None
    return ra


def tao_null(ma, khung, ho, so_chuoi=SO_NULL_TOI_THIEU, phuong_phap='block_bootstrap', hat=HAT):
    ham = {
        'block_bootstrap': null_block_bootstrap,
        'garch': null_garch,
        'permute_time': null_permute_time,
    }
    fn = ham.get(phuong_phap)
    if fn is None:
        raise ValueError(f'Khong biet phuong phap: {phuong_phap}')
    return fn(ma, khung, so_chuoi=so_chuoi, hat=hat)

def tao_null_day_du(ma, khung, ho, so_chuoi=SO_NULL_TOI_THIEU, hat=HAT):
    ra = {}
    for pp in ['block_bootstrap', 'garch', 'permute_time']:
        try:
            ra[pp] = tao_null(ma, khung, ho, so_chuoi=so_chuoi, phuong_phap=pp, hat=hat)
        except Exception:
            ra[pp] = []
    return ra

# ============================================================== NHA MAY LUC
# Cay mot edge BIET TRUOC vao chuoi that, roi do xac suat pheu phat hien ra no.
#
# Ban dau (DS) co dung y tuong nhung KHONG CAY DUOC GI: `_cay_edge` tinh chuoi
# loi suat da cay xong roi ham goi lai lam `df_gia = df.copy()` va nem ket qua
# do di. Moi muc delta vi the chay tren CUNG mot du lieu goc, duong cong luc
# phang tuyet doi, va MDE luon la None. Loi nay khong lo ra o dau ca - ham van
# chay, van tra ve mot cai bang.
#
# CACH CAY DUNG: giu nguyen TIN HIEU, chi doi PHAN THUONG.
#   - IBS cua tung bar phai KHONG DOI sau khi cay, neu khong thi ta vua doi luat
#     vua doi loi suat va khong biet cai nao gay ra khac biet;
#   - loi suat cua bar KE TIEP bar co tin hieu duoc cong them delta;
#   - dung lai OHLC tu gia dong cua moi sao cho IBS giu nguyen tuyet doi.

MUC_DELTA = (0.0, 0.5, 1.0, 2.0, 5.0, 10.0)   # bps moi lenh
SO_LAN_LAP = 200
NGUONG_IBS = 0.2
MAU_CAY = "ibs_bat_day"          # luat duoc cay = luat duoc do. Phai trung nhau.


def _ibs_cua(df):
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    rong = h - l
    rong = np.where(rong < 1e-12, 1e-12, rong)
    return (c - l) / rong, rong


def cay_edge_vao_gia(df, delta_bps: float, nguong_ibs: float = NGUONG_IBS,
                     hat: int | None = None):
    """Chuoi gia MOI, trong do LENH sinh ra tu tin hieu lai them `delta_bps`.

    Tra (df_moi, so_bar_co_tin_hieu).

    Ba dieu phai dung cung luc, va hai trong so do da sai o ban truoc:

    1. **IBS tung bar giu NGUYEN.** Nhan CA BON cot cua mot bar voi cung mot he
       so thi moi ty le trong bar khong doi - co che sinh ra dung tin hieu cu,
       chi phan thuong doi. (Ban truoc giai nguoc low/high tu close nen gan
       dung, nhung khong can thiet phuc tap den the.)

    2. **Bu tru de mua-giu KHONG huong.** Chi cong them thi ta nang ca chuoi gia
       len; mua-giu o trong thi truong 100% thoi gian con co che ~18%, nen cang
       cay manh co che cang THUA. Do that: delta 200 bps cho mua-giu Sharpe 6,67
       va co che 2,41. Phai tru lai dung bay nhieu tren cac bar con lai.

    3. **Cay dung CHO ma engine tinh lai.** `nhan/mo_phong.py` vao lenh o
       `open[i+1]` va an loi suat `open[i+2]/open[i+1]`. Cong delta vao loi suat
       DONG CUA cua bar i+1 thi lenh gan nhu khong nhan duoc gi: do that o ban
       truoc, delta 20 bps chi nang Sharpe tu 0,127 len 0,138. Buoc nhay phai
       nam giua bar i+1 va i+2.
    """
    ibs, _ = _ibs_cua(df)
    tin_hieu = ibs < nguong_ibs
    n = len(df)

    # dlog[t] = buoc nhay gia giua bar t-1 va bar t
    dlog = np.zeros(n)
    an_o = np.zeros(n, dtype=bool)
    idx = np.nonzero(tin_hieu)[0] + 2          # xem muc 3 o tren
    idx = idx[idx < n]
    an_o[idx] = True
    n_co, n_khong = int(an_o.sum()), int(n - an_o.sum())
    if n_co and n_khong and float(delta_bps):
        d = float(delta_bps) / 1e4
        dlog[an_o] = d
        dlog[~an_o] = -d * n_co / n_khong      # tong bang 0 -> drift khong doi

    M = np.exp(np.cumsum(dlog))
    d2 = df.copy()
    for cot in ("open", "high", "low", "close"):
        if cot in d2.columns:
            d2[cot] = d2[cot].to_numpy(float) * M
    return d2, int(tin_hieu.sum())


def _pheu_phat_hien(df, ma, khung, cp, nhan) -> tuple[bool, str]:
    """Chay pheu tren mot chuoi. Tra (co phat hien khong, dung o vong nao)."""
    r = SL.chay_pheu(MAU_CAY, {"nguong": NGUONG_IBS}, ma, khung, df=df, cp=cp,
                     pham_vi=None, da_chay=None)
    return r["ket_luan"] == SL.SAN_SANG_V4, r["vong"]


def duong_cong_luc(ma="US500CASH", khung="D1", cac_delta=MUC_DELTA,
                   so_lan=20, hat=HAT, cp=None):
    """Bang `delta` x `vong`: xac suat pheu phat hien ra edge da cay.

    `so_lan` mac dinh nho de goi thu duoc nhanh; ban nghiem thu phai chay 200.
    Moi lan lap dung mot doan con ngau nhien cua chuoi (bootstrap theo cua so)
    de co bien do, vi ban than phep cay la tat dinh.
    """
    df = DL.nap(ma, khung)
    n = len(df)
    if n < 1500:
        return {"loi": f"qua it bar: {n}"}
    if cp is None:
        cp = SL._chi_phi_cua(ma)

    rng = np.random.default_rng(hat)
    cua_so = max(1200, int(n * 0.7))
    ra = {"tai_san": ma, "khung": khung, "so_lan": so_lan,
          "nguong_ibs": NGUONG_IBS, "mau": MAU_CAY, "bang": {}}

    for delta in cac_delta:
        phat_hien = 0
        dung_o = {}
        for i in range(so_lan):
            dau = int(rng.integers(0, max(1, n - cua_so)))
            phan = df.iloc[dau:dau + cua_so]
            d2, _ = cay_edge_vao_gia(phan, delta)
            SL.xoa_bo_dem()
            duoc, vong = _pheu_phat_hien(d2, ma, khung, cp, f"luc_{delta}_{i}")
            phat_hien += int(duoc)
            dung_o[vong] = dung_o.get(vong, 0) + 1
        ra["bang"][str(delta)] = {
            "ty_le_phat_hien_pct": round(100.0 * phat_hien / max(so_lan, 1), 1),
            "dung_o_vong": dung_o}

    # MDE: delta nho nhat dat >= 80% phat hien. Khong dat muc nao thi MDE nam
    # NGOAI dai da quet - phai noi ro chu khong tra None trong.
    mde = None
    for d in cac_delta:
        if ra["bang"][str(d)]["ty_le_phat_hien_pct"] >= 80.0:
            mde = float(d)
            break
    ra["MDE_bps_moi_lenh"] = mde
    ra["ghi_chu"] = ("MDE nam ngoai dai da quet (> %g bps)" % max(cac_delta)
                     if mde is None else "")
    # Bai kiem doi xung: delta = 0 la NULL. Ty le phat hien o do chinh la ty le
    # duong tinh gia cua pheu.
    ra["duong_tinh_gia_pct"] = ra["bang"][str(cac_delta[0])]["ty_le_phat_hien_pct"]         if cac_delta and float(cac_delta[0]) == 0.0 else None
    return ra


def cay_va_chay(ma, khung, delta, so_lan=SO_LAN_LAP, hat=HAT):
    """Mot muc delta. Giu ten cu de khong pha ban goi hien co."""
    return duong_cong_luc(ma, khung, cac_delta=(delta,), so_lan=so_lan, hat=hat)
