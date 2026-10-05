# -*- coding: utf-8 -*-
"""thu_chuyen.py - THE GIOI NHAN TAO de thu bo dich tham so (`dich_tham_so`) va do thong minh (`do_thong_minh`) khi BIET DAP AN.

Buoc S1 cua `tai_lieu/CHUYEN_BOT_SANG_TAI_SAN_KHAC.md` (chu du an 04/10/2026: *"co the thu tren cac he thong va tai san don gian
nhieu lan roi moi tang toc ... khi do cang test duoc nhieu ta cang hoc duoc nhieu"*). Tren thi truong that khong ai biet tham so
dung la gi; o day thi biet, nen do duoc mot quy tac chuyen co tot hon "chep nguyen so" hay khong, va tot hon bao nhieu.

## THE GIOI (OU: hoi quy ve mot tam troi ngau nhien)
  gia = 1 + OU(sigma_pip, nua_doi_phut) + tam troi (random walk, troi_nam x sigma moi nam); nen M1 sinh tu buoc 1 phut, dinh / day
  trong nen sinh theo cau Brown dung phan phoi; spread khong doi = chi_phi_pip. `hoi_quy=False`: random walk khop bien do ngan
  han (khong co co hoi thang), dung de dem ti le "tim ra o co lai trong mau nhung thuc ra khong co gi".
  KHONG phai thi truong that: day la phep kiem DIEU KIEN CAN (quy tac chuyen phai qua duoc o the gioi don gian nay), khong phai chung
  minh no dung o thi truong that. Ket qua tren the gioi nay chi dua ra GIA THUYET cho buoc S2 (thi truong that, can may nha).

## DAP AN
  Tham so tot nhat cua mot the gioi duoc tim bang engine `luoi.py` tren nen M1 (nen min nhat: nguong phan giai 2 A thap nhat,
  gan tick nhat co the), lay TRUNG BINH diem tren N duong doc lap (mac dinh 8 x 4 nam), roi chon o co diem CAO NGUYEN tot nhat
  (`do_thong_minh.cao_nguyen_mang`). Dap an cua the gioi KHONG BAO GIO dung chung duong voi mau dung de chon: chon tren tap A,
  CHAM tren tap B (cac duong doc lap khac) - neu khong ket qua tot nhat bi thoi phong ~15-20 % do chon max tren ~450 o co nhieu.
  Diem mot o = `diem_o` (lai suat nam nhan he so lot cham maxDD 80 %, tran don bay 10) - cung thang diem cua `nc_thi_nghiem._o_luoi`
  them tran don bay, vi neu khong o it rui ro se co diem vo han.

## HOI HOI (regret)
  hoi_tuong_doi = (diem_dap_an - diem_cua_o_chon) / diem_dap_an, cham tren tap B. 0 = tot nhu dap an; 1 = mat het; > 1 = lo.
  Dap an <= 0 (the gioi khong co co hoi) thi KHONG tinh hoi tuong doi, bao rieng.
"""
from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import math
import os
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from nhan import dich_tham_so as DT
from nhan import do_thong_minh as DM
from nhan import luoi as LU

PHIEN_BAN = 1

PIP = 1e-4
NGAY_NAM = 261
VON = 10000.0
DON_BAY_TOI_DA = 10.0
#: thi truong nhan tao dung dong tien bao gia, 1 lot = 100.000 don vi, von 10.000
QUY_CACH = LU.QuyCach(ma="TG", pip=PIP, hop_dong=100000.0, point=1e-5, phi_nam_mua=0.0, phi_nam_ban=0.0, spread_du_phong=2e-4,
                      von_quy_doi=1.0, do_tin="DO", da_doi_chieu=True, nguon="the gioi nhan tao")

#: khong gian o cua dap an (khoang cach theo pip, ti le tp / buoc, so tang)
BUOC = tuple(float(x) for x in np.round(np.geomspace(3.0, 400.0, 24), 1))
TY_LE_TP = (0.5, 0.75, 1.0, 1.4, 2.0)
TANG = (4, 8, 14, 24)

SO_DUONG_DAP_AN = 8
SO_NAM_DUONG = 4.0


def luong_mac_dinh() -> int:
    try:
        return max(1, int(os.environ.get("NC_QUET_LUONG", "")))
    except ValueError:
        return max(1, os.cpu_count() or 2)


# ------------------------------------------------------------------------------------------------------ the gioi
@dataclass(frozen=True)
class TheGioi:
    """Mot thi truong nhan tao (don vi pip). `troi_nam`: do troi cua tam, tinh bang so sigma moi nam."""
    sigma_pip: float = 30.0
    nua_doi_phut: float = 240.0
    troi_nam: float = 15.0
    chi_phi_pip: float = 10.0
    hoi_quy: bool = True

    def doi(self, **kw) -> "TheGioi":
        return replace(self, **kw)


def hat_on_dinh(tg: TheGioi, vai_tro: str, i: int) -> int:
    """Hat ngau nhien on dinh theo (the gioi, vai tro, thu tu): chay lai ra dung so cu."""
    return zlib.crc32(("%r|%s|%d" % (tg, vai_tro, int(i))).encode("ascii")) & 0x7FFFFFFF


def sinh_duong(tg: TheGioi, so_nam: float, hat: int, buoc_phut: int = 1) -> pd.DataFrame:
    """Duong gia nen `buoc_phut` phut (open/high/low/close/spread). Chi so thoi gian: ngay lam viec tu 2000-01-03, 24 gio moi ngay."""
    from scipy.signal import lfilter
    per_day = 1440 // buoc_phut
    n_days = int(round(so_nam * NGAY_NAM))
    n = n_days * per_day
    rng = np.random.default_rng(int(hat))
    sigma = tg.sigma_pip * PIP
    phi = math.exp(-math.log(2.0) / tg.nua_doi_phut * buoc_phut)
    z = rng.standard_normal(n)
    if tg.hoi_quy:
        ou = lfilter([1.0], [1.0, -phi], z * sigma * math.sqrt(1 - phi * phi))
    else:
        ou = np.cumsum(z * sigma * math.sqrt(2.0 * (1.0 - phi)))
    s_c = tg.troi_nam * sigma / math.sqrt(NGAY_NAM * per_day)
    ctr = np.cumsum(rng.standard_normal(n) * s_c)
    c = 1.0 + ou + ctr
    o = np.empty(n)
    o[0] = c[0]
    o[1:] = c[:-1]
    v = sigma ** 2 * (1 - phi * phi) + s_c ** 2 if tg.hoi_quy else sigma ** 2 * 2.0 * (1.0 - phi) + s_c ** 2
    u1 = rng.random(n)
    u2 = rng.random(n)
    d = c - o
    mid = 0.5 * (o + c)
    hi = mid + 0.5 * np.sqrt(d * d - 2 * v * np.log(u1))
    lo = mid - 0.5 * np.sqrt(d * d - 2 * v * np.log(u2))
    ngay = pd.bdate_range("2000-01-03", periods=n_days)
    gio = (np.arange(per_day) * buoc_phut * 60 * 10 ** 9).astype("timedelta64[ns]")
    idx = pd.DatetimeIndex((ngay.values[:, None] + gio[None, :]).reshape(-1))
    sp = np.full(n, tg.chi_phi_pip * (PIP / QUY_CACH.point))
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c, "spread": sp}, index=idx)


def gop_khung(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """Gop `k` nen lien tiep thanh mot nen (open dau, high max, low min, close cuoi, spread dau). k = 1: tra nguyen."""
    k = int(k)
    if k <= 1:
        return df
    n = (len(df) // k) * k
    a = df.iloc[:n]
    g = lambda col: a[col].to_numpy().reshape(-1, k)
    return pd.DataFrame({"open": g("open")[:, 0], "high": g("high").max(1), "low": g("low").min(1), "close": g("close")[:, -1],
                         "spread": g("spread")[:, 0]}, index=a.index[::k])


def bien_do_nen_pip(df: pd.DataFrame) -> float:
    return float(np.median(df["high"].to_numpy() - df["low"].to_numpy())) / PIP


def bien_do_ngang_pip(df: pd.DataFrame, gio_phut: float, khung_phut: float) -> float:
    """R(H): trung vi cua (cao nhat - thap nhat) trong cua so H phut tren cac nen cua khung (pip). Khong phu thuoc khung neu H lon hon nen."""
    w = max(1, int(round(gio_phut / khung_phut)))
    hi = df["high"].rolling(w).max()
    lo = df["low"].rolling(w).min()
    r = (hi - lo).dropna().to_numpy()[::max(1, w // 4)]
    return float(np.median(r)) / PIP


# ------------------------------------------------------------------------------------------------------ cham diem
def diem_o(dl, ts, von: float = VON, don_bay_toi_da: float = DON_BAY_TOI_DA) -> float:
    """Diem cua mot (duong, tham so): -100 = chay tai khoan; lo thi lai suat nam am nguyen; co lai thi lai suat nam nhan he so lot
    cham maxDD 80 % (`nc_thi_nghiem._he_so_lot_tai_tran`) va khong qua tran don bay `don_bay_toi_da` (cung nghia voi niem phong luoi)."""
    from nhan import nc_thi_nghiem as NT
    kq = LU.chay_mang(dl, ts, von)
    if kq.chay:
        return -100.0
    cs = LU.chi_so(kq, von)
    ln = float(cs["loi_suat_nam_pct"])
    if ln <= 0:
        return ln
    kd = NT._he_so_lot_tai_tran(np.asarray(kq.duong_equity, float), von)
    if not kd:
        return -100.0
    notional = kq.margin * ts.don_bay
    kl = don_bay_toi_da * von / notional if notional > 0 else float("inf")
    return ln * min(kd, kl)


def diem_tren_cac_duong(dls: list, cac_ts: list, luong: int | None = None) -> np.ndarray:
    """Ma tran [so tham so, so duong] diem; chay song song (nhan C nha GIL). Loi engine -> -100 (khong lam hong ca luot)."""
    luong = luong or luong_mac_dinh()
    viec = [(i, j) for i in range(len(cac_ts)) for j in range(len(dls))]

    def f(ij):
        try:
            return diem_o(dls[ij[1]], cac_ts[ij[0]])
        except Exception:
            return -100.0
    with ThreadPoolExecutor(max_workers=luong) as ex:
        out = list(ex.map(f, viec))
    return np.array(out, float).reshape(len(cac_ts), len(dls))


# ------------------------------------------------------------------------------------------------------ phong cach + khong gian o
@dataclass(frozen=True)
class Kieu:
    """Phong cach cua bot = cai KHONG doi khi chuyen (lop HE_SO / CONG_TAC cua dich_tham_so)."""
    ten: str = "phang"
    kieu_lot: str = "phang"
    he_so_lot: float = 1.0
    he_so_buoc: float = 1.0
    che_do: str = "hai_chieu"

    def tham_so(self, buoc: float, tp: float, tang: int, lot: float = 0.01) -> "LU.ThamSo":
        return LU.ThamSo(buoc=float(buoc), tp=float(tp), tran_tang=int(tang), lot=lot, che_do=self.che_do, kieu_lot=self.kieu_lot,
                         he_so_lot=self.he_so_lot, he_so_buoc=self.he_so_buoc)


#: phang = lot phang, buoc khong doi (luoi tron); geo = lot x1,1 va buoc x1,15 moi tang (kieu martingale / DCA gian dan)
KIEU = {"phang": Kieu("phang"), "geo": Kieu("geo", "nhan", 1.1, 1.15)}


def luoi_o_dap_an(kieu: Kieu, san_pip: float) -> tuple:
    """(danh sach ThamSo, chi so (ib, ir, it)) cua cac o hop le: buoc va tp deu >= `san_pip` (nguong phan giai cua nen dung de cham)."""
    cac, chi = [], []
    for ib, b in enumerate(BUOC):
        for ir, r in enumerate(TY_LE_TP):
            tp = round(b * r, 1)
            if b < san_pip or tp < san_pip:
                continue
            for it, t in enumerate(TANG):
                cac.append(kieu.tham_so(b, tp, t))
                chi.append((ib, ir, it))
    return cac, chi


@dataclass
class DapAn:
    """Dap an cua mot the gioi theo mot phong cach: be mat diem (tap A) + o tot nhat + diem cua no tren tap B."""
    tg: TheGioi
    kieu: Kieu
    san_pip: float
    be_mat: np.ndarray = field(repr=False, default=None)
    tot_nhat: object = None
    diem_cao_nguyen: float = float("nan")
    diem_b: float = float("nan")
    a_nen_pip: float = float("nan")


def dung_duong(tg: TheGioi, vai_tro: str, so_duong: int, so_nam: float = SO_NAM_DUONG, k_gop: int = 1) -> list:
    return [LU.chuan_bi(gop_khung(sinh_duong(tg, so_nam, hat_on_dinh(tg, vai_tro, i)), k_gop), QUY_CACH) for i in range(so_duong)]


def tim_dap_an(tg: TheGioi, kieu: Kieu, so_duong: int = SO_DUONG_DAP_AN, so_nam: float = SO_NAM_DUONG, luong: int | None = None) -> DapAn:
    """Dap an: chon tren tap A (`so_duong` duong, `so_nam` nam M1 moi duong) bang be mat TRUNG BINH + cao nguyen; cham o chon tren tap B
    (cac duong khac han, cung hat on dinh nen chay lai ra dung so cu)."""
    tap_a = dung_duong(tg, "A", so_duong, so_nam)
    a_nen = float(np.median(np.concatenate([d.hi - d.lo for d in tap_a[:2]]))) / PIP
    san = DT.NGUONG_PHAN_GIAI * a_nen
    cac, chi = luoi_o_dap_an(kieu, san)
    m = diem_tren_cac_duong(tap_a, cac, luong)
    del tap_a
    tb = m.mean(axis=1)
    arr = np.full((len(BUOC), len(TY_LE_TP), len(TANG)), np.nan)
    for (ib, ir, it), x in zip(chi, tb):
        arr[ib, ir, it] = x
    cn = DM.cao_nguyen_mang(arr)
    ib, ir, it = np.unravel_index(int(np.nanargmax(cn)), cn.shape)
    tot = kieu.tham_so(BUOC[ib], round(BUOC[ib] * TY_LE_TP[ir], 1), TANG[it])
    da = DapAn(tg=tg, kieu=kieu, san_pip=san, be_mat=arr, tot_nhat=tot, diem_cao_nguyen=float(cn[ib, ir, it]), a_nen_pip=a_nen)
    tap_b = dung_duong(tg, "B", so_duong, so_nam)
    da.diem_b = float(diem_tren_cac_duong(tap_b, [tot], luong)[0].mean())
    return da


def diem_tb(tap_b: list, cac_ts: list, luong: int | None = None) -> np.ndarray:
    """Diem trung binh tren tap B cho tung tham so."""
    return diem_tren_cac_duong(tap_b, cac_ts, luong).mean(axis=1)


def hoi_tuong_doi(diem_dap_an: float, diem: float) -> float | None:
    """(dap an - diem) / dap an; None khi dap an <= 0 (the gioi khong co co hoi)."""
    if not (diem_dap_an > 0) or not math.isfinite(diem):
        return None
    return (diem_dap_an - diem) / diem_dap_an


# ------------------------------------------------------------------------------------------------------ do tu du lieu QUAN SAT
def ho_so_chuoi(dl, ts, von: float = VON) -> dict:
    """Thoi gian giu va do sau cua cac CHUOI (ro) khi chay `ts` tren duong `dl`: p90 -> (`gio_giu_phut`, `tang_tham_chieu`) cua `dich_luoi`.
    Chi chuoi da dong moi tinh thoi gian giu; tra None neu khong du chuoi."""
    kq = LU.chay_mang(dl, ts, von, ghi_lenh=True)
    ln = kq.lenh
    if ln is None or len(ln) == 0:
        return {"so_chuoi": 0, "gio_giu_phut": None, "tang_p90": None, "chay": bool(kq.chay)}
    g = ln.groupby("ro")
    tang = (g["tang"].max() + 1).to_numpy()
    mo = g["mo"].min()
    dong = g["dong"].max()
    ok = dong.notna()
    giu = ((dong[ok] - mo[ok]).dt.total_seconds() / 60.0).to_numpy()
    return {"so_chuoi": int(len(tang)), "so_chuoi_dong": int(ok.sum()),
            "gio_giu_phut": float(np.quantile(giu, 0.9)) if len(giu) >= 20 else None,
            "tang_p90": int(np.ceil(np.quantile(tang, 0.9))), "chay": bool(kq.chay)}


KIEU_QUY_MO = ("A_chart", "A_ref", "R_H", "sigma")
KHUNG_THAM_CHIEU_PHUT = 15


def thi_truong_do_duoc(df_m1: pd.DataFrame, khung_phut: int, kieu_quy_mo: str, tg: TheGioi | None = None,
                       gio_giu_phut: float | None = None) -> "DT.ThiTruong":
    """`ThiTruong` do tu duong M1 quan sat, trong khung `khung_phut` cua bot. `kieu_quy_mo` doi dai luong QUY MO `A` (thay cho bien do nen cua khung):
      A_chart  trung vi bien do nen cua CHINH khung cua bot (mac dinh cua S0)
      A_ref    trung vi bien do nen cua khung tham chieu co dinh M15 (khong phu thuoc khung bot chon)
      R_H      trung vi (cao nhat - thap nhat) trong cua so `gio_giu_phut` (thoi gian giu chuoi dien hinh)
      sigma    do lech chuan THAT cua the gioi (chi de chan doan: ngoai doi that khong biet)"""
    if kieu_quy_mo not in KIEU_QUY_MO:
        raise ValueError("kieu_quy_mo %r khong hop le" % (kieu_quy_mo,))
    tt = DT.ThiTruong.tu_du_lieu(gop_khung(df_m1, khung_phut), QUY_CACH, VON, ma="TG", khung_phut=float(khung_phut))
    if kieu_quy_mo == "A_chart":
        return tt
    if kieu_quy_mo == "A_ref":
        a = bien_do_nen_pip(gop_khung(df_m1, KHUNG_THAM_CHIEU_PHUT)) * PIP
    elif kieu_quy_mo == "R_H":
        if not gio_giu_phut or gio_giu_phut <= 0:
            raise ValueError("R_H can gio_giu_phut")
        a = bien_do_ngang_pip(df_m1, gio_giu_phut, 1.0) * PIP
    else:
        if tg is None:
            raise ValueError("sigma can the gioi that")
        a = tg.sigma_pip * PIP
    return replace(tt, A=float(a))


@contextlib.contextmanager
def san_chi_phi_tam(he_so: float):
    """Doi tam thoi `dich_tham_so.SAN_CHI_PHI` (chan duoi theo chi phi, mac dinh 3): chi de do anh huong cua chan duoi. Khong dung da luong."""
    cu = DT.SAN_CHI_PHI
    DT.SAN_CHI_PHI = float(he_so)
    try:
        yield
    finally:
        DT.SAN_CHI_PHI = cu


def dich_theo_quy_tac(ts, src, dst, w: float, tam: str, san: float, gio_giu_phut: float | None, tang_tham_chieu: int | None):
    """Mot cach dich: buoc va tp cung ti le `w` (0 = theo bien do, 1 = theo chi phi), `tam` I6 | giu, chan duoi `san` x chi phi; lot giu nguyen
    (diem o `diem_o` khong phu thuoc lot: lot nhan he so cham maxDD). Tra `KetQuaDich`."""
    cach = DT.CachDich(w_buoc=float(w), w_tp=float(w), tam=tam, thoi_gian="dong_ho", lot="giu")
    with san_chi_phi_tam(san):
        return DT.dich_luoi(ts, src, dst, cach, gio_giu_phut, tang_tham_chieu)


# ------------------------------------------------------------------------------------------------------ bo kich ban
@dataclass(frozen=True)
class KichBan:
    """Mot cap (the gioi nguon -> the gioi dich) va khung cua bot o moi ben. `k`: he so khoang cach ky vong (chi cap L1)."""
    ten: str
    loai: str
    nguon: TheGioi
    dich: TheGioi
    khung_nguon: int = 1
    khung_dich: int = 1
    k: float | None = None
    mo_ta: str = ""


GOC = TheGioi(sigma_pip=30.0, nua_doi_phut=240.0, troi_nam=15.0, chi_phi_pip=10.0, hoi_quy=True)

#: Chi gom the gioi ma buoc toi uu NAM TREN nguong phan giai cua nen M1 (chi phi / bien do nen M1 >= ~2,6): neu khong, dap an chi la
#: "o nho nhat engine do duoc" va phep thu khong noi duoc gi (do 05/10/2026: `tai_lieu/CHUYEN_BOT_SANG_TAI_SAN_KHAC.md` muc 11.6).
BO_KICH_BAN = (
    KichBan("Z0", "L0", GOC, GOC, mo_ta="cung the gioi, hai duong quan sat doc lap: nhieu cua cac dai luong do duoc"),
    KichBan("K2", "L1", GOC, GOC.doi(sigma_pip=60.0, chi_phi_pip=20.0), k=2.0, mo_ta="bien do x2 va chi phi x2 (moi khoang cach nen x2)"),
    KichBan("K05", "L1", GOC, GOC.doi(sigma_pip=15.0, chi_phi_pip=5.0), k=0.5, mo_ta="bien do x0,5 va chi phi x0,5"),
    KichBan("C2", "L2", GOC, GOC.doi(chi_phi_pip=20.0), mo_ta="chi phi x2, bien do giu nguyen"),
    KichBan("S05", "L2", GOC, GOC.doi(sigma_pip=15.0), mo_ta="bien do x0,5, chi phi giu nguyen (chi phi tuong doi x2)"),
    KichBan("H4", "L4", GOC, GOC.doi(nua_doi_phut=960.0), mo_ta="hoi quy cham hon 4 lan (nua doi 240 -> 960 phut)"),
    KichBan("TF5", "L3", GOC, GOC, khung_nguon=15, khung_dich=5, mo_ta="cung the gioi, bot chay khung M15 o nguon va M5 o dich"),
    KichBan("TF1", "L3", GOC, GOC, khung_nguon=15, khung_dich=1, mo_ta="cung the gioi, bot chay khung M15 o nguon va M1 o dich"),
)


def kich_ban(ten: str) -> KichBan:
    for k in BO_KICH_BAN:
        if k.ten == ten:
            return k
    raise KeyError(ten)


# ------------------------------------------------------------------------------------------------------ giai doan 1: dich "zero-shot"
W_THU = (0.0, 0.5, 1.0)
TAM_THU = ("I6", "giu")
SAN_THU = (DT.SAN_CHI_PHI, 0.0)


def ten_bien_the(quy_mo: str, w: float, tam: str, san: float) -> str:
    return "%s|w=%g|tam=%s|san=%g" % (quy_mo, w, tam, san)


def _cho_quan_sat(tg: TheGioi, vai_tro: str, so_nam: float, i: int = 0) -> pd.DataFrame:
    return sinh_duong(tg, so_nam, hat_on_dinh(tg, vai_tro, i))


def giai_doan_1(kb: KichBan, kieu: Kieu, da_nguon: DapAn, da_dich: DapAn | None = None, so_duong: int = SO_DUONG_DAP_AN,
                so_nam: float = SO_NAM_DUONG, luong: int | None = None, quy_mo=KIEU_QUY_MO, w_thu=W_THU, tam_thu=TAM_THU,
                san_thu=SAN_THU, so_obs: int = 3) -> dict:
    """Mot (kich ban, phong cach): moi cach dich cho mot tham so du doan cua dich; cham tren tap B cua the gioi dich; hoi tiec so voi dap an.

    `da_nguon`: dap an cua the gioi nguon (= tham so cua "bot" nguon). `da_dich`: dap an cua the gioi dich (None = tinh o day; neu
    nguon = dich thi dung chung). `so_obs`: so CAP duong quan sat doc lap (moi cap = mot duong M1 cua nguon + mot duong M1 cua dich) de do
    nhieu cua cac dai luong do duoc (A, C, R(H), E(H,q), thoi gian giu). Tra dict {kich_ban, kieu, dap_an_nguon, dap_an_dich, hang: [...]}
    moi hang co `obs` (0..so_obs-1)."""
    luong = luong or luong_mac_dinh()
    ts_nguon = da_nguon.tot_nhat
    if da_dich is None:
        da_dich = da_nguon if kb.dich == kb.nguon else tim_dap_an(kb.dich, kieu, so_duong, so_nam, luong)
    tap_b = dung_duong(kb.dich, "B", so_duong, so_nam)
    san_phan_giai = DT.NGUONG_PHAN_GIAI * da_dich.a_nen_pip
    hang, ho_so = [], []
    cac_bien_the = [("B0_chep", None, None, None, None)]
    for qm in quy_mo:
        for w in w_thu:
            for tam in tam_thu:
                for san in san_thu:
                    cac_bien_the.append((ten_bien_the(qm, w, tam, san), qm, w, tam, san))
    for o in range(int(so_obs)):
        # quan sat: mot duong M1 doc lap cho moi ben, moi lan quan sat mot cap moi
        obs_n = _cho_quan_sat(kb.nguon, "obs_n", so_nam, o)
        obs_d = _cho_quan_sat(kb.dich, "obs_d", so_nam, o)
        hs = ho_so_chuoi(LU.chuan_bi(obs_n, QUY_CACH), ts_nguon)
        gio_giu, tang_tc = hs["gio_giu_phut"], hs["tang_p90"]
        ho_so.append(hs)
        cho_tt: dict = {}

        def tt_cua(ben: str, qm: str):
            k = (ben, qm)
            if k not in cho_tt:
                if ben == "nguon":
                    cho_tt[k] = thi_truong_do_duoc(obs_n, kb.khung_nguon, qm, kb.nguon, gio_giu)
                else:
                    cho_tt[k] = thi_truong_do_duoc(obs_d, kb.khung_dich, qm, kb.dich, gio_giu)
            return cho_tt[k]

        ket, khoa_ts, can_do = {}, {}, []
        for ten, qm, w, tam, san in cac_bien_the:
            ly_do = []
            if qm is None:
                ts = ts_nguon
            else:
                try:
                    kqd = dich_theo_quy_tac(ts_nguon, tt_cua("nguon", qm), tt_cua("dich", qm), w, tam, san, gio_giu, tang_tc)
                except ValueError as e:
                    kqd = None
                    ly_do = [str(e)]
                else:
                    ly_do = list(kqd.ly_do)
                ts = kqd.tham_so if (kqd is not None and kqd.trang_thai == DT.OK) else None
            ket[ten] = {"quy_mo": qm, "w": w, "tam": tam, "san": san, "ts": ts, "ly_do": ly_do}
            if ts is not None and dataclasses.astuple(ts) not in khoa_ts:
                khoa_ts[dataclasses.astuple(ts)] = ts
                can_do.append(ts)
        diem = {}
        if can_do:
            for ts, x in zip(can_do, diem_tb(tap_b, can_do, luong)):
                diem[dataclasses.astuple(ts)] = float(x)
        for ten, r in ket.items():
            ts = r["ts"]
            row = {"obs": o, "ten": ten, "quy_mo": r["quy_mo"], "w": r["w"], "tam": r["tam"], "san": r["san"], "ly_do": r["ly_do"]}
            if ts is None:
                row["ap_duoc"] = False
            else:
                x = diem[dataclasses.astuple(ts)]
                row.update({"ap_duoc": True, "buoc": ts.buoc, "tp": ts.tp, "tang": ts.tran_tang, "diem_b": x,
                            "hoi_tiec": hoi_tuong_doi(da_dich.diem_b, x), "duoi_phan_giai": bool(min(ts.buoc, ts.tp) < san_phan_giai)})
            hang.append(row)
    return {"kich_ban": kb.ten, "loai": kb.loai, "kieu": kieu.ten, "k_ky_vong": kb.k, "khung_nguon": kb.khung_nguon, "khung_dich": kb.khung_dich,
            "nguon": dataclasses.asdict(kb.nguon), "dich": dataclasses.asdict(kb.dich),
            "dap_an_nguon": {"buoc": ts_nguon.buoc, "tp": ts_nguon.tp, "tang": ts_nguon.tran_tang, "diem_cao_nguyen": da_nguon.diem_cao_nguyen},
            "dap_an_dich": {"buoc": da_dich.tot_nhat.buoc, "tp": da_dich.tot_nhat.tp, "tang": da_dich.tot_nhat.tran_tang,
                            "diem_b": da_dich.diem_b, "diem_cao_nguyen": da_dich.diem_cao_nguyen, "a_nen_pip": da_dich.a_nen_pip,
                            "san_phan_giai_pip": san_phan_giai},
            "ho_so_nguon": ho_so, "hang": hang}


# ------------------------------------------------------------------------------------------------------ nguong + ke hoach DONG BANG
#: Nguong DE XUAT dong bang TRUOC lan chay dau (thiet ke muc 11.4). Doi nguong sau khi da chay = PHIEN BAN MOI, bao cao ghi ca hai.
#: Day la NHAN canh bao de biet "co hoc duoc khong", KHONG phai cong chan (luat 25/09/2026).
NGUONG = {
    "phien_ban": 1,
    "L0": "cung ThiTruong thi moi truong cua tham so khong doi (giu nguyen tung bit)",
    "L1_sai_so_log_toi_da": 0.12,          # |ln(d_dich / (k x d_nguon))| cua buoc va tp, quy tac mac dinh
    "L1_hoi_tiec_trung_vi": 0.15,
    "L2_L3_L4_hoi_tiec_trung_vi": 0.15,    # quy tac mac dinh, trung vi tren cac cap duong quan sat
    "thong_minh_so_voi_ngau_nhien": 0.8,   # giai doan 2: hoi tiec thong minh <= 0,8 x hoi tiec tim ngau nhien o ngan sach ngang
    "ty_le_dat_gia_toi_da_sau_xac_nhan": 0.05,
    "ty_le_dat_gia_toi_da_truoc_xac_nhan": 0.25,
    "khong_do_duoc": "min(buoc, tp) < 2 x bien do nen M1 cua the gioi dich: KHONG tinh hoi tiec (chua do duoc, khong phai am)",
    "chon_quy_tac_mac_dinh": ("bien the (quy mo, w, tam, san) co hoi tiec trung vi thap nhat tren cac kich ban do duoc, tru Z0; hoa (cach <= 0,02) thi lay "
                              "bien the don gian nhat theo thu tu quy mo A_chart < A_ref < R_H < sigma, roi w nho, tam giu, san 0; kiem bang bo mot-kich-ban-ra"),
    "so_duong_dap_an": SO_DUONG_DAP_AN,
    "so_nam_duong": SO_NAM_DUONG,
    "so_obs": 3,
}


def ke_hoach_s1() -> dict:
    """Cau hinh dong bang cua S1 + dau van tay (sha256 cat 16): ghi vao bao cao de thay chay lan sau co dung ke hoach da dong bang khong."""
    ch = {"phien_ban_module": PHIEN_BAN, "nguong": NGUONG, "kich_ban": [dataclasses.asdict(k) for k in BO_KICH_BAN], "buoc": list(BUOC),
          "ty_le_tp": list(TY_LE_TP), "tang": list(TANG), "w_thu": list(W_THU), "tam_thu": list(TAM_THU), "san_thu": list(SAN_THU),
          "quy_mo": list(KIEU_QUY_MO), "kieu": {k: dataclasses.asdict(v) for k, v in KIEU.items()}, "goc": dataclasses.asdict(GOC),
          "don_bay_toi_da": DON_BAY_TOI_DA, "von": VON, "ngay_nam": NGAY_NAM}
    h = hashlib.sha256(json.dumps(_json_an_toan(ch), sort_keys=True).encode("ascii")).hexdigest()[:16]
    return {"plan_hash": h, "cau_hinh": ch}


# ------------------------------------------------------------------------------------------------------ ghi / doc
def _json_an_toan(x):
    """numpy / NaN -> JSON hop le (NaN -> None)."""
    if isinstance(x, dict):
        return {str(k): _json_an_toan(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_an_toan(v) for v in x]
    if isinstance(x, np.ndarray):
        return _json_an_toan(x.tolist())
    if isinstance(x, (np.floating, float)):
        v = float(x)
        return v if math.isfinite(v) else None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def dap_an_ra_dict(da: DapAn) -> dict:
    return _json_an_toan({"the_gioi": dataclasses.asdict(da.tg), "kieu": dataclasses.asdict(da.kieu), "san_pip": da.san_pip,
                          "a_nen_pip": da.a_nen_pip, "tot_nhat": dataclasses.asdict(da.tot_nhat), "diem_cao_nguyen": da.diem_cao_nguyen,
                          "diem_b": da.diem_b, "buoc": list(BUOC), "ty_le_tp": list(TY_LE_TP), "tang": list(TANG),
                          "be_mat": da.be_mat})


def ghi_json(duong_dan: str, obj) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(duong_dan)), exist_ok=True)
    tam = duong_dan + ".tmp"
    with open(tam, "w", encoding="utf-8") as f:
        json.dump(_json_an_toan(obj), f, ensure_ascii=True, indent=1)
    os.replace(tam, duong_dan)


def chay_giai_doan_1(thu_muc: str, ten_kich_ban=None, ten_kieu=("phang", "geo"), so_duong: int = SO_DUONG_DAP_AN, so_nam: float = SO_NAM_DUONG,
                     so_obs: int = 3, luong: int | None = None, log=print) -> None:
    """Chay giai doan 1, ghi tung (kich ban, phong cach) ra `thu_muc/p1_<kich ban>_<kieu>.json` va dap an ra `thu_muc/dapan_*.json`.
    Da co tep thi bo qua (chay lai khong ton cong)."""
    import time
    ten_kich_ban = list(ten_kich_ban or [k.ten for k in BO_KICH_BAN])
    for kn in ten_kieu:
        kieu = KIEU[kn]
        goc_f = os.path.join(thu_muc, "dapan_%s_%s.json" % ("goc", kn))
        t0 = time.time()
        da_goc = tim_dap_an(GOC, kieu, so_duong, so_nam, luong)
        ghi_json(goc_f, dap_an_ra_dict(da_goc))
        log("[%s] dap an goc %.0fs: buoc %.1f tp %.1f tang %d diem_b %.1f" % (kn, time.time() - t0, da_goc.tot_nhat.buoc, da_goc.tot_nhat.tp,
                                                                          da_goc.tot_nhat.tran_tang, da_goc.diem_b))
        for ten in ten_kich_ban:
            kb = kich_ban(ten)
            f = os.path.join(thu_muc, "p1_%s_%s.json" % (ten, kn))
            if os.path.exists(f):
                log("[%s] %s: da co, bo qua" % (kn, ten))
                continue
            t0 = time.time()
            da_dich = da_goc if kb.dich == kb.nguon else tim_dap_an(kb.dich, kieu, so_duong, so_nam, luong)
            if da_dich is not da_goc:
                ghi_json(os.path.join(thu_muc, "dapan_%s_%s.json" % (ten, kn)), dap_an_ra_dict(da_dich))
            r = giai_doan_1(kb, kieu, da_goc, da_dich, so_duong, so_nam, luong, so_obs=so_obs)
            ghi_json(f, r)
            log("[%s] %s xong %.0fs: dap an dich buoc %.1f tp %.1f tang %d" % (kn, ten, time.time() - t0, da_dich.tot_nhat.buoc, da_dich.tot_nhat.tp,
                                                                           da_dich.tot_nhat.tran_tang))


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Bo thu chuyen tham so tren the gioi tong hop (S1)")
    ap.add_argument("giai_doan", choices=["p1"])
    ap.add_argument("--ra", required=True, help="thu muc ghi ket qua")
    ap.add_argument("--kich-ban", default="", help="danh sach ten, ngan cach dau phay (mac dinh: tat ca)")
    ap.add_argument("--kieu", default="phang,geo")
    ap.add_argument("--so-duong", type=int, default=SO_DUONG_DAP_AN)
    ap.add_argument("--so-nam", type=float, default=SO_NAM_DUONG)
    ap.add_argument("--so-obs", type=int, default=3)
    a = ap.parse_args(argv)
    kb = [x for x in a.kich_ban.split(",") if x] or None
    chay_giai_doan_1(a.ra, kb, tuple(x for x in a.kieu.split(",") if x), a.so_duong, a.so_nam, a.so_obs, log=lambda m: print(m, flush=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
