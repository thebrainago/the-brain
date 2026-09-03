# -*- coding: utf-8 -*-
"""mo_phong.py - ENGINE BACKTEST. Mot cua duy nhat de bien tin hieu thanh tien.

Quy uoc THOI GIAN (quan trong nhat file nay):
  - Template chi duoc tra ve `tin_hieu[i]` = phoi nhiem MONG MUON, tinh tu
    thong tin BIET TAI CLOSE cua bar i.
  - Engine TU dich mot bar: vi_the[i+1] = tin_hieu[i]. Template khong tu dich,
    khong tu chon diem vao -> khong the gian lan do tre.
  - Loi suat mot bar la open[i] -> open[i+1] (vao lenh tai OPEN bar ke tiep,
    CLAUDE.md luat 1). KHONG dung close->close.

Chi phi (bao cao 15/08 - loi nang nhat cua ban cu):
  - spread THAT theo gio, tu cot spread cua bar MT5.
  - truot gia.
  - phi qua dem BAT DOI XUNG mua/ban, tinh theo so ngay THAT giua cac bar.
    Loi that #1 ngay 09/08 la phi chi tinh cho chieu mua -> tang 2 %/nam
    alpha gia cho moi chien luoc co chieu ban. Canary `luon ban` gac cho nay.

TP/SL cung bar: dung OPEN cua chinh bar do de doan cai nao cham truoc
(gan TP hon -> TP truoc). KHONG mac dinh SL - "than trong co he thong" van la
so SAI, va no giet dung loai edge mong dang tim (THIET_KE muc 13).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import chi_phi as CP


@dataclass
class KetQua:
    ma: str = ""
    khung: str = ""
    index: pd.DatetimeIndex | None = None
    vi_the: np.ndarray | None = None
    loi: np.ndarray | None = None          # loi suat log RONG tung bar
    loi_tho: np.ndarray | None = None      # chua tru chi phi
    r: np.ndarray | None = None            # loi suat tai san (open->open)
    chi_phi_spread: float = 0.0
    chi_phi_truot: float = 0.0
    chi_phi_giu: float = 0.0
    so_lan_doi: int = 0
    so_lenh: int = 0
    phoi_nhiem: float = 0.0
    canh_bao: list = field(default_factory=list)
    che_do_gop: str = "log"                # log | so_hoc
    don_bay: float = 1.0
    chay_tai_khoan: bool = False           # co bar nao lam von <= nguong khong
    bar_chay: int | None = None
    ngay_chay: object = None
    von_mang: np.ndarray | None = None     # von SO HOC (co the ve 0)

    @property
    def von(self) -> np.ndarray:
        if self.von_mang is not None:
            return self.von_mang
        return np.exp(np.cumsum(np.nan_to_num(self.loi)))

    def chuoi(self) -> pd.Series:
        return pd.Series(self.von, index=self.index, name="von")


def _loi_suat_tien(df: pd.DataFrame) -> np.ndarray:
    """Loi suat log open[i] -> open[i+1]. Bar cuoi = 0 (khong con bar de an)."""
    o = df["open"].to_numpy(dtype=float)
    r = np.zeros(len(o))
    with np.errstate(divide="ignore", invalid="ignore"):
        r[:-1] = np.log(o[1:] / o[:-1])
    return np.nan_to_num(r, nan=0.0, posinf=0.0, neginf=0.0)


def chay(df: pd.DataFrame, tin_hieu, cp: CP.MoHinhChiPhi,
         lai_suat_nam: np.ndarray | None = None, ma: str = "", khung: str = "",
         da_dich: bool = False, don_bay: float = 1.0,
         gop: str = "tu_dong", nguong_chay: float = 0.0) -> KetQua:
    """Chay mot chien luoc. `tin_hieu[i]` la phoi nhiem biet tai close[i].

    da_dich=True chi dung cho CANARY (khi can dat vi the dung bien mot bar).

    `don_bay`: he so nhan phoi nhiem, ap **SAU** khi da cat ve [-1, 1]. Tach
    lam mot tham so rieng la co y: tran +-1 la tam chan chong template tra ve
    so bay (mot template tra 50 se che ra loi suat 50 lan), nen don bay phai
    la thu NGUOI GOI khai ro, khong phai thu template tu gianh duoc.

    Vi sao can: cong 1 so TONG LAI cua he voi mua-giu, nhung he chon loc chi o
    trong thi truong 16-18% thoi gian con moc o 100%. Do khong phai so cung
    don vi. Muon hoi "cung mot muc rui ro thi ben nao lai hon" thi phai dua
    duoc he len dung do bien dong cua moc - va truoc 30/08/2026 dieu do KHONG
    lam duoc: nhan tin hieu len 1,55 lan roi cat ngay ve 1,0, hai lan chay ra
    ket qua GIONG HET NHAU ma khong bao gi.

    Phi cua phan don bay them duoc thu day du: spread theo khoi luong doi va
    phi qua dem theo phoi nhiem, deu tinh tren `v` sau khi nhan.

    `gop`: CACH GOP LOI SUAT QUA THOI GIAN. Day la loi nang duoc phat hien
    03/09/2026, ngay khi du an quay sang cau hoi don bay.
      - "log"    : loi_von = v*r voi r la loi suat LOG. Cong don tuyen tinh.
      - "so_hoc" : loi_von = log(1 + v*(e^r - 1) - phi). Dung.
      - "tu_dong": "so_hoc" khi don_bay != 1, nguoc lai "log" (giu nguyen moi
                   con so cu).

    VI SAO PHAI SUA. Cach "log" cho exp(sum(L*r)) = (S_T/S_0)^L. Do khong phai
    mot vi the don bay L tai can bang hang ngay — do la mua LUY THUA cua chi
    so. Hai thu bi lam bien mat sach:
      1. LUC CAN BIEN DONG ~ 0,5*L*(L-1)*sigma^2/nam. Voi SP500 (sigma 16%)
         va L=3 do la 7,7 diem %/nam bi bo qua.
      2. CHAY TAI KHOAN. Trong log, von khong bao gio am duoc. Ngoai doi L=3
         chet sach o bat ky ngay nao -33,4%.
    Do that tren 98 nam SP500: don_bay=3 kieu log cho von cuoi x76.289.488,
    dung bang (giá cuoi/giá dau)^3, trong khi thuc te chay tai khoan thang
    10/1929. Moi ket luan CAGR o L>1 truoc 03/09/2026 deu phai xem lai.
    (Sharpe thi khong sao: no bat bien theo ti le.)

    `nguong_chay`: von con lai (ti le so voi von truoc bar do) ma duoi no thi
    coi la chay tai khoan. 0,0 = chay sach. San that cat lenh som hon (XM cat
    o muc ky quy 20%), nen 0,0 la CHAN DUOI lac quan.
    """
    n = len(df)
    th = np.asarray(tin_hieu, dtype=float).reshape(-1)
    if len(th) != n:
        raise ValueError(f"tin hieu dai {len(th)} nhung du lieu {n} bar")
    if not np.isfinite(don_bay) or don_bay <= 0:
        raise ValueError(f"don_bay phai la so duong huu han, nhan {don_bay!r}")
    th = np.nan_to_num(th, nan=0.0)
    th = np.clip(th, -1.0, 1.0) * float(don_bay)

    if da_dich:
        v = th
    else:
        v = np.zeros(n)
        v[1:] = th[:-1]          # ENGINE dich, template khong duoc tu dich

    r = _loi_suat_tien(df)
    idx = df.index

    doi = np.abs(np.diff(np.concatenate(([0.0], v))))
    sp = cp.spread_mang(idx)
    phi_sp = doi * sp
    phi_tr = doi * cp.truot_gia_frac
    phi_gi = cp.phi_giu_mang(idx, v, lai_suat_nam)

    if gop == "tu_dong":
        che_do = "so_hoc" if abs(float(don_bay) - 1.0) > 1e-12 else "log"
    elif gop in ("log", "so_hoc"):
        che_do = gop
    else:
        raise ValueError(f"gop phai la log|so_hoc|tu_dong, nhan {gop!r}")

    phi_tong = phi_sp + phi_tr + phi_gi
    canh = list(cp.canh_bao)
    von_mang = None
    chay_tk, bar_chay, ngay_chay = False, None, None

    if che_do == "log":
        loi_tho = v * r
        loi = loi_tho - phi_tong
    else:
        # loi suat SO HOC cua tai san; moi thanh phan duoi day deu la ti le
        # cua VON (notional = v * von), nen cong tru truc tiep duoc.
        ra = np.expm1(r)
        loi_tho_sh = v * ra
        song = 1.0 + loi_tho_sh - phi_tong
        xau = np.nonzero(song <= nguong_chay)[0]
        if len(xau):
            bar_chay = int(xau[0])
            chay_tk = True
            ngay_chay = idx[bar_chay]
            song = song.copy()
            song[bar_chay:] = 1.0        # dong bang: khong con von de lai/lo
            canh.append(f"CHAY TAI KHOAN tai bar {bar_chay} ({ngay_chay}) "
                        f"voi don bay {don_bay:g}x")
        von_mang = np.cumprod(song)
        if bar_chay is not None:
            von_mang[bar_chay:] = 0.0
        loi = np.log(song)
        loi_tho = np.log1p(np.maximum(loi_tho_sh, -1.0 + 1e-12))

    return KetQua(
        ma=ma, khung=khung, index=idx, vi_the=v, loi=loi, loi_tho=loi_tho, r=r,
        chi_phi_spread=float(np.nansum(phi_sp)),
        chi_phi_truot=float(np.nansum(phi_tr)),
        chi_phi_giu=float(np.nansum(phi_gi)),
        so_lan_doi=int(np.sum(doi > 1e-12)),
        so_lenh=dem_lenh(v),
        phoi_nhiem=float(np.mean(np.abs(v))),
        canh_bao=canh,
        che_do_gop=che_do, don_bay=float(don_bay),
        chay_tai_khoan=chay_tk, bar_chay=bar_chay, ngay_chay=ngay_chay,
        von_mang=von_mang)


def dem_lenh(v: np.ndarray) -> int:
    """So LENH = so lan mo mot vi the moi: vao tu trang thai rong HOAC LAT CHIEU.

    Dem theo kieu "chi tinh khi di tu 0 len" la SAI voi chien luoc luon o trong
    thi truong (+1 -> -1 khong bao gio ve 0): no ra dung 1 lenh cho ca chuoi,
    roi bi bo loc "du lenh" danh truot oan. Da sap that ngay 15/08 khi thu luc cong.
    """
    v = np.asarray(v, dtype=float)
    truoc = np.concatenate(([0.0], v[:-1]))
    khac0 = np.abs(v) > 1e-12
    return int(np.sum(khac0 & (np.sign(v) != np.sign(truoc))))


def mua_giu(df: pd.DataFrame, cp: CP.MoHinhChiPhi, ma: str = "", khung: str = "",
            lai_suat_nam: np.ndarray | None = None) -> KetQua:
    """MUA-GIU CFD SAU PHI THAT - moc chinh de so sanh (THIET_KE muc 2).

    Day moi la thu ta mua duoc. `mua_giu_tho` (chi so khong phi) chi de DOC,
    khong duoc lam dieu kien PASS.
    """
    return chay(df, np.ones(len(df)), cp, lai_suat_nam, ma, khung, da_dich=True)


def mua_giu_tho(df: pd.DataFrame, ma: str = "", khung: str = "") -> KetQua:
    """Chi so khong phi. Doc de biet phi an mat bao nhieu, KHONG lam cong."""
    rong = CP.MoHinhChiPhi(ma=ma, spread_frac_chung=0.0, truot_gia_frac=0.0,
                           phi_nam_mua=0.0, phi_nam_ban=0.0, do_tin="KHAI")
    return chay(df, np.ones(len(df)), rong, None, ma, khung, da_dich=True)


# ----------------------------------------------------------------- TP / SL
def chay_tpsl(df: pd.DataFrame, tin_hieu_vao, tp_frac: float, sl_frac: float,
              cp: CP.MoHinhChiPhi, gio_toi_da: int = 0, ma: str = "",
              khung: str = "") -> KetQua:
    """Chien luoc co TP/SL. `tin_hieu_vao[i]` = +1/-1/0 biet tai close[i],
    vao lenh tai OPEN bar i+1.

    Cham ca TP lan SL trong cung mot bar -> dung OPEN cua bar do de doan:
    gan TP hon thi TP truoc. Day la quy tac cua du an, khong phai mac dinh SL.
    """
    n = len(df)
    th = np.nan_to_num(np.asarray(tin_hieu_vao, dtype=float).reshape(-1), nan=0.0)
    o = df["open"].to_numpy(dtype=float)
    hi = df["high"].to_numpy(dtype=float)
    lo = df["low"].to_numpy(dtype=float)
    idx = df.index

    v = np.zeros(n)          # phoi nhiem giu trong bar i (de tinh phi qua dem)
    kl = np.zeros(n)         # khoi luong giao dich trong bar i (de tinh spread)
    loi_tho = np.zeros(n)
    so_lenh = 0
    dang, gia_vao, bar_vao = 0.0, 0.0, -1

    for i in range(1, n):
        # 1) VAO LENH tai OPEN bar i, theo tin hieu biet tai close bar i-1
        if dang == 0.0 and th[i - 1] != 0.0:
            dang = float(np.sign(th[i - 1]))
            gia_vao, bar_vao = o[i], i
            kl[i] += 1.0
            so_lenh += 1

        if dang == 0.0:
            continue
        v[i] = dang

        # 2) KIEM THOAT trong chinh bar i
        muc_tp = gia_vao * (1.0 + tp_frac * dang)
        muc_sl = gia_vao * (1.0 - sl_frac * dang)
        if dang > 0:
            cham_tp, cham_sl = hi[i] >= muc_tp, lo[i] <= muc_sl
        else:
            cham_tp, cham_sl = lo[i] <= muc_tp, hi[i] >= muc_sl

        gia_ra = None
        if cham_tp and cham_sl:
            # cung bar: doan bang OPEN cua chinh bar do - gan TP hon thi TP truoc.
            # KHONG mac dinh SL (THIET_KE muc 13).
            gia_ra = muc_tp if abs(o[i] - muc_tp) <= abs(o[i] - muc_sl) else muc_sl
        elif cham_tp:
            gia_ra = muc_tp
        elif cham_sl:
            gia_ra = muc_sl
        elif gio_toi_da and (i - bar_vao) >= gio_toi_da and i + 1 < n:
            gia_ra = o[i + 1]      # het gio giu -> dong o OPEN bar ke tiep

        if gia_ra is not None:
            loi_tho[i] = dang * np.log(gia_ra / o[i])
            kl[i] += 1.0
            dang, gia_vao, bar_vao = 0.0, 0.0, -1
        elif i + 1 < n:
            loi_tho[i] = dang * np.log(o[i + 1] / o[i])

    loi_tho = np.nan_to_num(loi_tho, nan=0.0, posinf=0.0, neginf=0.0)
    phi_sp = kl * cp.spread_mang(idx)
    phi_tr = kl * cp.truot_gia_frac
    phi_gi = cp.phi_giu_mang(idx, v, None)
    loi = loi_tho - phi_sp - phi_tr - phi_gi

    return KetQua(
        ma=ma, khung=khung, index=idx, vi_the=v, loi=loi, loi_tho=loi_tho,
        r=_loi_suat_tien(df),
        chi_phi_spread=float(np.nansum(phi_sp)), chi_phi_truot=float(np.nansum(phi_tr)),
        chi_phi_giu=float(np.nansum(phi_gi)), so_lan_doi=int(np.sum(kl > 0)),
        so_lenh=so_lenh,      # dem truc tiep trong vong lap, da dung cho ca lat chieu
        phoi_nhiem=float(np.mean(np.abs(v))), canh_bao=list(cp.canh_bao))


# ------------------------------------------------------------------ TIEN ICH
def dich_khong_nhin_truoc(s: pd.Series | np.ndarray) -> np.ndarray:
    """Tien ich cho template: chuyen chuoi chi bao thanh tin hieu hop le.
    Chi de tuong minh - engine van tu dich them mot bar nua."""
    a = np.asarray(s, dtype=float)
    return np.nan_to_num(a, nan=0.0)
