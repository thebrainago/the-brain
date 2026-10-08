# -*- coding: utf-8 -*-
"""dich_tham_so.py - DICH tham so cua mot bot luoi/DCA sang THI TRUONG khac (buoc S0, `tai_lieu/CHUYEN_BOT_SANG_TAI_SAN_KHAC.md`).

Chu du an 04/10/2026 (thong diep B): *"cac bot nay chuyen cho gold, toi muon chay thu sang cap tien, timeframe va input khac
thi lam sao? ... do het cac thong so hay do thong minh?"*. Tra loi cua thiet ke: KHONG do het va KHONG chep nguyen so. Doi moi
tham so ve DON VI khong phu thuoc tai san roi dich theo cac BAT BIEN co ten; moi cach dich la mot GIA THUYET co ten, do duoc,
so sanh duoc. Module nay chi lam phan DICH (so hoc thuan tren `luoi.ThamSo` / ten khoa `.set`): khong chay engine, khong
doc `nc.db`, khong ghi gi, khong cham holdout.

## MOT THAM SO = DUNG MOT LOP (luat mot-lop)
  KC_BUOC   khoang cach buoc luoi, cho lui, tran buoc           don vi chuan: A (bien do mot nen)
  KC_TP     chot loi, bien cap tia                              A va C; san >= 3 C
  KC_SL     cat lo, trailing, hoa von (khoang cach)             A
  TAM       tam luoi = do sau toi da cua chuoi (dai luong suy ra: tong cac buoc, khong phai truong rieng)
  SO_DEM    so tang toi da, so lenh moi nhip, ... (dem)         giu so; TAM duoc kiem lai
  HE_SO     he so lot, he so buoc, cac he so nhan khac          giu nguyen
  LOT       lot, lot tran, lot lenh doi ung                     I4 (ngan sach rui ro)
  TIEN      chot theo tien, hoa von theo tien, % von            theo lot x khoang cach x gia tri diem
  PHI       tran spread / tran phi cho phep vao lenh            I2 (ty le chi phi)
  THOI_GIAN cho (phut), gio phien, so nen cua chi bao, khung    I5: hai ung vien (giu gio dong ho / giu so nen)
  NGUONG_CHI_BAO  RSI < 30, ADX > 25 ...                        phan vi (ngoai_sinh.chuyen), o day chi GIU
  CONG_TAC  bat/tat, che do, kieu, magic, stop-out, don bay     giu nguyen
Mot truong `ThamSo` moi ma quen xep lop -> `thieu_lop()` bao va `dich_luoi` tu choi (chong "quen" am tham).

## BA DAI LUONG THI TRUONG (don vi GIA, doan kham_pha cua (ma, khung)): `ThiTruong`
  A  trung vi (high - low) cua nen | C chi phi MOT vong (spread + hoa hong + truot) | E(H,q) do sau thi truong =
  phan vi q cua do lech NGUOC lon nhat trong H nen tiep theo (chi tu gia, khong can chien luoc) | pv = tien cua 1,0 don vi gia
  cua 1,0 lot | von cung dong tien voi pv.

## BAT BIEN (moi cai la mot cach dich)
  I1  giu d / A          d_dich = d_nguon x A_dich / A_nguon            (w = 0)
  I2  giu d / C          d_dich = d_nguon x C_dich / C_nguon            (w = 1)
  pha tron  d_dich = d_nguon x (A_dich/A_nguon)^(1-w) x (C_dich/C_nguon)^w
  I4  giu ngan sach rui ro: lot_dich sao cho "phan tram von mat khi gia di nguoc het TAM luoi" khong doi
  I6  giu tam / E(H,q): tam_dich = tam_nguon x E_dich / E_nguon; so tang tinh lai tu buoc dich va he so buoc
  I5  thoi gian: giu gio dong ho (n_dich = n x T_nguon / T_dich) hoac giu so nen (n_dich = n)
  TIEN  m_dich = m_nguon x (lot x d x pv)_dich / (lot x d x pv)_nguon
Chan: `d >= 3 C_dich` (khong nho hon ba lan chi phi mot vong; ap cho buoc va chot loi) | phan giai `d >= 2 A_dich` cho MOI khoang
cach (luat `pmg_engine.NGUONG_PHAN_GIAI`: duoi nguong bar khong do noi) - duoi nguong `dich_luoi` van ra ket qua nhung gan
`engine_do_duoc = False` (chi tester do duoc, engine tra CHUA_DO_DUOC, KHONG phai AM).

## HAI KIEU KHONG DICH DUOC (khong lan)
  KHONG_AP_DUOC (cung)  thieu lop, thi truong khong hop le, lot dich < lot toi thieu ...: khong co tham so dich nao dung.
  engine_do_duoc = False (mem)  tham so dich co, nhung engine tren bar khong do noi: di thang len tester, khong xep hang engine.
Ca hai chi la LY DO cua CHUA_DO_DUOC, khong bao gio la AM.

## DOAN KHAM_PHA
Module khong tu cat doan: nguoi goi phai dua vao du lieu cua doan kham_pha (xac_nhan / niem_phong khong bao gio vao bo hoc).
"""
from __future__ import annotations

import dataclasses
import math
import re
from dataclasses import dataclass, field, replace

import numpy as np

from nhan import luoi as LU

PHIEN_BAN = 1

KC_BUOC = "KC_BUOC"
KC_TP = "KC_TP"
KC_SL = "KC_SL"
TAM = "TAM"
SO_DEM = "SO_DEM"
HE_SO = "HE_SO"
LOT = "LOT"
TIEN = "TIEN"
PHI = "PHI"
THOI_GIAN = "THOI_GIAN"
NGUONG_CHI_BAO = "NGUONG_CHI_BAO"
CONG_TAC = "CONG_TAC"
CHUA_PHAN_LOP = "CHUA_PHAN_LOP"
LOP = (KC_BUOC, KC_TP, KC_SL, TAM, SO_DEM, HE_SO, LOT, TIEN, PHI, THOI_GIAN, NGUONG_CHI_BAO, CONG_TAC)

OK = "OK"
KHONG_AP_DUOC = "KHONG_AP_DUOC"

#: Cung nguong voi `pmg_engine.NGUONG_PHAN_GIAI` / `hephaestus.NGUONG_PHAN_GIAI_QT` - mot con so, mot cho (test chong lech).
NGUONG_PHAN_GIAI = 2.0
#: Khoang cach buoc / chot loi khong duoc nho hon ngan nay lan chi phi mot vong (thiet ke muc 8.1).
SAN_CHI_PHI = 3.0
#: Tran cho so cach dich co so mot (bot, tai san dich): thiet ke muc 8.2 / 9.1.
TOI_DA_CACH_DICH = 9
#: Toi da tang cho mot chuoi sau khi dich (chan vong lap vo han khi tam rat lon).
TOI_DA_TANG = 500
#: Mot cach dich co them "I2 thuan" khi ty le chi phi/bien do doi tu 2 lan tro len (hai chieu).
NGUONG_CHI_PHI_AP_DAO = 2.0
#: Tran sut giam cua du an (cham_diem.TRAN_SUT_GIAM): mat tai tam >= muc nay chi la CANH BAO o day.
TRAN_RUI_RO_PCT = 80.0

#: Moi truong cua `luoi.ThamSo` -> lop. Truong moi khong co o day = `thieu_lop()` khong rong = `dich_luoi` tu choi.
LOP_THAM_SO_LUOI = {
    "buoc": KC_BUOC,
    "tp": KC_TP,
    "tran_tang": SO_DEM,          # so tang tinh lai tu TAM + buoc dich (I6)
    "che_do": CONG_TAC,
    "lot": LOT,
    "muc_stopout": CONG_TAC,
    "don_bay": CONG_TAC,
    "cho_lui": KC_BUOC,           # la khoang cach pip (khong phai thoi gian): chuyen dong ho -> khoang cach gia
    "kieu_lot": CONG_TAC,
    "he_so_lot": HE_SO,
    "tia_lenh": CONG_TAC,
    "bien_cap": KC_TP,            # tong lai cua cap (pip) de dong cap tia
    "cap_moi_bar": SO_DEM,
    "chot_tien": TIEN,            # tien tren 0,01 lot
    "dung_lo_tong": TIEN,         # engine CHUA cai dat (`luoi.CHUA_CAI_DAT`)
    "he_so_buoc": HE_SO,
    "buoc_tran": KC_BUOC,
    "khop_bar": CONG_TAC,         # cach engine mo phong bar (luoi.MO_HINH_BAR), khong phai tham so giao dich: dich khung giu nguyen
    # ---- co che thoat + loc gio (08/10/2026, `luoi.TINH_NANG_DUONG_DI`): mac dinh 0 = TAT, chi dich khi BAT (xem khoi "co che thoat" o dich_luoi)
    "cat_lo_pip": KC_SL,          # cat CA RO khi gia nguoc n pip so voi gia trung binh theo lot: khoang cach cat lo, I1 nhu moi KC_SL
    "cat_lo_tien": TIEN,          # cat CA RO khi lo noi m tien tren 0,01 lot (cung don vi voi chot_tien)
    "thoat_gio": THOI_GIAN,       # dong ro sau h gio ke tu luc mo: khoang gio dong ho (I5)
    "nghi_gio": THOI_GIAN,        # nghi h gio sau cat lo / thoat gio roi moi mo ro moi: khoang gio dong ho (I5)
    "gio_vao_tu": CONG_TAC,       # cua so gio MO RO MOI: gio-trong-ngay cua may chu (0-24), khong phai khoang thoi gian: giu nguyen
    "gio_vao_den": CONG_TAC,
}

#: Mo ta mot dong cho moi lop (don vi chuan + cach dich mac dinh): nguon cho bang trong tai lieu va bao cao.
MO_TA_LOP = {
    KC_BUOC: ("A", "I1 / I2 pha tron (w), san 3 C, kiem phan giai 2 A"),
    KC_TP: ("A va C", "I1 / I2 pha tron (w = 0,5), san 3 C, kiem phan giai 2 A"),
    KC_SL: ("A", "I1, kiem phan giai 2 A"),
    TAM: ("E(H,q)", "I6: tam_dich = tam_nguon x E_dich / E_nguon"),
    SO_DEM: ("dem", "giu so (tran_tang tinh lai tu TAM)"),
    HE_SO: ("khong thu nguyen", "giu nguyen"),
    LOT: ("% von mat o do sau", "I4: giu phan tram von mat khi gia di het TAM luoi"),
    TIEN: ("tien / (lot x d x pv)", "nhan ti le khoang cach, pv va lot (tien tuyet doi); % von giu nguyen"),
    PHI: ("C", "I2: nhan ti le chi phi"),
    THOI_GIAN: ("gio dong ho hoac so nen", "I5: hai ung vien (giu gio / giu so nen)"),
    NGUONG_CHI_BAO: ("phan vi", "giu nguyen o day (dich bang ngoai_sinh.chuyen)"),
    CONG_TAC: ("-", "giu nguyen"),
}


def thieu_lop() -> list:
    """Truong `luoi.ThamSo` chua co lop + lop khai bao cho truong khong ton tai. Rong = dung luat mot-lop."""
    co = {f.name for f in dataclasses.fields(LU.ThamSo)}
    kb = set(LOP_THAM_SO_LUOI)
    loi = ["ThamSo.%s chua co lop" % t for t in sorted(co - kb)]
    loi += ["lop khai bao cho truong khong ton tai: %s" % t for t in sorted(kb - co)]
    loi += ["ThamSo.%s mang lop la %r" % (t, LOP_THAM_SO_LUOI[t]) for t in sorted(kb & co) if LOP_THAM_SO_LUOI[t] not in LOP]
    return loi


# ------------------------------------------------------------------------------------------------------ dinh dang loi thuong
def _s(x, n: int = 3) -> str:
    """So ngan gon cho van ban tieng Viet (dau phay thap phan): 10.0 -> '10', 0.3125 -> '0,312'."""
    if x is None:
        return "?"
    if isinstance(x, (bool, np.bool_)):
        return "co" if x else "khong"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    x = float(x)
    if not math.isfinite(x):
        return "?"
    if x == int(x) and abs(x) < 1e9:
        return str(int(x))
    return ("%." + str(n) + "g") % x if abs(x) >= 1e-4 else ("%.2e" % x)


def _sv(x, n: int = 3) -> str:
    return _s(x, n).replace(".", ",")


def _tron_pip(x: float) -> float:
    """Lam tron 0,1 pip (1 point o cap 5 chu so), khong bao gio ve 0 khi x > 0."""
    if not math.isfinite(x) or x <= 0:
        return x
    return max(0.1, round(x, 1))


# ------------------------------------------------------------------------------------------------------ thi truong
def _do_lech_nguoc(hi, lo, cl, H: int):
    """(mua, ban): do lech NGUOC lon nhat trong H nen tiep theo cho MOI nen xuat phat i (don vi gia), nan (NaN) o cuoi chuoi.
    Chuoi MUA vao tai close[i]: close[i] - min(low[i+1..i+H]); chuoi BAN: max(high[i+1..i+H]) - close[i]; am -> 0."""
    import pandas as pd
    fmin = pd.Series(lo).rolling(H).min().shift(-H).to_numpy()
    fmax = pd.Series(hi).rolling(H).max().shift(-H).to_numpy()
    return np.maximum(cl - fmin, 0.0), np.maximum(fmax - cl, 0.0)


@dataclass
class ThiTruong:
    """Cac dai luong thi truong cua MOT (ma, khung) dung cho viec dich (don vi GIA tru khi ghi khac).

    `pv` va `von` PHAI cung dong tien (`tien_te`): "bao_gia" = dong bao gia cua chinh ma do (nhu engine `luoi.py`: von da nhan
    `von_quy_doi`), "tai_khoan" = dong tai khoan (cho tep .set). Nguon va dich phai cung `tien_te`."""
    ma: str
    khung_phut: float
    A: float
    C: float
    pip: float
    pv: float
    von: float
    point: float | None = None
    do_tin_chi_phi: str = "KHAI"
    lot_toi_thieu: float = 0.01
    lot_buoc: float = 0.01
    tien_te: str = "bao_gia"
    nguon: str = ""
    #: (high, low, close) numpy - tuy chon, cho E(H,q); khong dua vao so sanh / in ra.
    gia: tuple | None = field(default=None, repr=False, compare=False)
    _nho: dict = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self):
        if self.point is None:
            self.point = self.pip / 10.0

    def do_sau(self, H: int, q: float = 0.9, huong: str = "mua"):
        """E(H,q): phan vi q cua do lech nguoc lon nhat trong H nen tiep theo (don vi GIA), hoac None khi khong tinh duoc
        (khong co gia / chuoi qua ngan: can >= H + 200 nen xuat phat). `huong` = mua | ban | hai_chieu (hai chieu = cao hon)."""
        if self.gia is None:
            return None
        H = int(H)
        hi, lo, cl = self.gia
        if H < 1 or len(cl) < H + 200 or not (0.0 < q < 1.0):
            return None
        kh = (H,)
        if kh not in self._nho:
            if len(self._nho) >= 8:
                self._nho.pop(next(iter(self._nho)))
            mua, ban = _do_lech_nguoc(hi, lo, cl, H)
            ok = np.isfinite(mua)
            self._nho[kh] = (mua[ok], ban[ok])
        mua, ban = self._nho[kh]
        if len(mua) < 200:
            return None
        e_mua, e_ban = float(np.quantile(mua, q)), float(np.quantile(ban, q))
        if huong == "mua":
            return e_mua
        if huong == "ban":
            return e_ban
        return max(e_mua, e_ban)

    def tom_tat(self) -> dict:
        return {"ma": self.ma, "khung_phut": self.khung_phut, "A_pip": self.A / self.pip, "C_pip": self.C / self.pip,
                "C_tren_A": self.C / self.A, "pip": self.pip, "pv": self.pv, "von": self.von,
                "do_tin_chi_phi": self.do_tin_chi_phi, "tien_te": self.tien_te}

    @classmethod
    def tu_du_lieu(cls, df, qc, von: float, ma: str | None = None, khung_phut: float | None = None, hoa_hong_gia: float = 0.0,
                   truot_gia: float = 0.0, lot_toi_thieu: float = 0.01, lot_buoc: float = 0.01) -> "ThiTruong":
        """Dung tu khung nen (cot high / low / close, tuy chon `spread`, chi so thoi gian) + `luoi.QuyCach`, dong "bao_gia".
        C = trung vi spread (don vi gia, qua `luoi.chuan_bi`) + hoa hong + truot (da quy ra gia, mac dinh 0: luoi.py chi tinh spread)."""
        dl = LU.chuan_bi(df, qc)
        A = float(np.median(dl.hi - dl.lo))
        C = float(np.median(dl.sp)) + float(hoa_hong_gia) + float(truot_gia)
        if khung_phut is None:
            d = np.diff(dl.idx.values).astype("timedelta64[s]").astype(float) / 60.0
            khung_phut = float(np.median(d)) if len(d) else float("nan")
        return cls(ma=ma or qc.ma, khung_phut=float(khung_phut), A=A, C=C, pip=float(qc.pip), pv=float(qc.hop_dong),
                   von=float(von) * float(qc.von_quy_doi), point=float(qc.point), do_tin_chi_phi=str(qc.do_tin),
                   lot_toi_thieu=lot_toi_thieu, lot_buoc=lot_buoc, tien_te="bao_gia", nguon="tu_du_lieu",
                   gia=(dl.hi, dl.lo, dl.cl))


_TRUONG_SO_DUONG = ("khung_phut", "A", "C", "pip", "pv", "von", "point", "lot_toi_thieu", "lot_buoc")


def _hop_le(x) -> bool:
    try:
        return math.isfinite(float(x)) and float(x) > 0
    except (TypeError, ValueError):
        return False


def kiem_thi_truong(tt: ThiTruong, nhan: str = "") -> list:
    """Ly do thi truong khong dung duoc (rong = dung duoc)."""
    t = nhan or tt.ma
    return ["%s: %s = %r phai la so duong huu han" % (t, f, getattr(tt, f)) for f in _TRUONG_SO_DUONG if not _hop_le(getattr(tt, f))]


def _la_cung_thi_truong(a: ThiTruong, b: ThiTruong) -> bool:
    """Nguon = dich: cung hang so VA (khong co gia hoac cung mang gia). Khi do `dich_luoi` giu nguyen moi tham so (cap L0)."""
    if a is b:
        return True
    if not all(math.isclose(float(getattr(a, f)), float(getattr(b, f)), rel_tol=1e-12) for f in _TRUONG_SO_DUONG):
        return False
    if a.tien_te != b.tien_te:
        return False
    if a.gia is None and b.gia is None:
        return True
    if a.gia is None or b.gia is None:
        return False
    return all(x is y for x, y in zip(a.gia, b.gia))


def khoang_cach_thi_truong(src: ThiTruong, dst: ThiTruong) -> dict:
    """Vector khoang cach log (dich - nguon): dung de ghi hang hoc va de canh bao khi hai thi truong qua xa nhau."""
    def ln(x, y):
        return math.log(x / y) if _hop_le(x) and _hop_le(y) else None
    return {"log_A": ln(dst.A, src.A), "log_C": ln(dst.C, src.C), "log_C_tren_A": ln(dst.C / dst.A, src.C / src.A),
            "log_pv": ln(dst.pv, src.pv), "log_khung": ln(dst.khung_phut, src.khung_phut)}


# ------------------------------------------------------------------------------------------------------ bat bien
def he_so_ty_le(src: ThiTruong, dst: ThiTruong, w: float) -> float:
    """k = (A_dich/A_nguon)^(1-w) x (C_dich/C_nguon)^w. w = 0: I1 (giu d/A); w = 1: I2 (giu d/C)."""
    if not (0.0 <= w <= 1.0):
        raise ValueError("w phai nam trong [0,1], nhan %r" % (w,))
    ka = dst.A / src.A
    if w == 0.0:
        return ka
    kc = dst.C / src.C
    if w == 1.0:
        return kc
    return (ka ** (1.0 - w)) * (kc ** w)


def dich_do_dai(d_nguon_gia: float, src: ThiTruong, dst: ThiTruong, w: float, san_chi_phi: bool):
    """Dich MOT khoang cach (don vi GIA). Tra (d_dich_gia, nang_len_san). `san_chi_phi`: nang len 3 C_dich neu thap hon."""
    d = d_nguon_gia * he_so_ty_le(src, dst, w)
    nang = False
    if san_chi_phi and d < SAN_CHI_PHI * dst.C:
        d, nang = SAN_CHI_PHI * dst.C, True
    return d, nang


# ------------------------------------------------------------------------------------------------------ hinh hoc luoi
def buoc_thu_k(buoc: float, he_so_buoc: float, buoc_tran: float, k: int) -> float:
    """Khoang cach tu tang k den tang k+1 (k tinh tu 0) - dung cong thuc cua `luoi._mot_ro._buoc`."""
    if he_so_buoc == 1.0:
        return buoc
    return min(buoc * (he_so_buoc ** k), buoc_tran)


def cac_muc(buoc: float, he_so_buoc: float, buoc_tran: float, n: int) -> list:
    """Do lech (cung don vi voi `buoc`) cua tang 0..n-1 so voi tang dau tien."""
    muc = [0.0]
    for k in range(max(n, 1) - 1):
        muc.append(muc[-1] + buoc_thu_k(buoc, he_so_buoc, buoc_tran, k))
    return muc


def lot_tuong_doi(kieu_lot: str, he_so_lot: float, k: int) -> float:
    """Lot cua tang k (0-based) chia lot goc - dung cong thuc cua `luoi._mot_ro._lot`."""
    if kieu_lot == "nhan":
        return he_so_lot ** k
    if kieu_lot == "cong":
        return 1.0 + he_so_lot * k
    return 1.0


def hinh_rui_ro(buoc: float, he_so_buoc: float, buoc_tran: float, kieu_lot: str, he_so_lot: float, n: int) -> dict:
    """Hinh hoc mot chuoi n tang (don vi cua `buoc`, 1,0 lot goc):
      tam        do lech cua tang sau cung so voi tang dau (= tong n-1 buoc)
      mat_tai_tam  tong lot_tuong_doi[k] x (tam - muc[k]): thua lo (don vi gia x lot) khi gia di nguoc ngang tang sau cung
    n = 1 (khong co luoi) khong co tam: lay mot buoc lam do sau tham chieu."""
    muc = cac_muc(buoc, he_so_buoc, buoc_tran, n)
    tam = muc[-1]
    lots = [lot_tuong_doi(kieu_lot, he_so_lot, k) for k in range(len(muc))]
    if tam <= 0.0:
        return {"tam": 0.0, "tam_tham_chieu": buoc, "mat_tai_tam": lots[0] * buoc, "muc": muc, "lot_tuong_doi": lots,
                "tong_lot_tuong_doi": sum(lots)}
    mat = sum(l * (tam - m) for l, m in zip(lots, muc))
    return {"tam": tam, "tam_tham_chieu": tam, "mat_tai_tam": mat, "muc": muc, "lot_tuong_doi": lots, "tong_lot_tuong_doi": sum(lots)}


def so_tang_cho_tam(tam: float, buoc: float, he_so_buoc: float, buoc_tran: float, n_min: int = 2, n_max: int = TOI_DA_TANG) -> int:
    """So tang n (n_min..n_max) sao cho tang sau cung nam GAN NHAT do sau `tam` (cung don vi voi `buoc`); hoa -> n nho hon."""
    ung = []
    n, off = 1, 0.0
    while n <= n_max:
        if n >= n_min:
            ung.append((abs(off - tam), n))
            if off > tam:
                break
        off += buoc_thu_k(buoc, he_so_buoc, buoc_tran, n - 1)
        n += 1
    return min(ung)[1] if ung else n_min


def _lam_tron_lot(x: float, buoc: float) -> float:
    """Ha xuong boi so cua buoc lot (khong bao gio vuot ngan sach rui ro)."""
    v = math.floor(x / buoc + 1e-9) * buoc
    nd = max(0, -int(math.floor(math.log10(buoc)))) + 2
    return round(v, nd)


# ------------------------------------------------------------------------------------------------------ cach dich + ket qua
@dataclass(frozen=True)
class CachDich:
    """Mot to hop lua chon dich (mac dinh = thiet ke muc 8.1: buoc w = 0, chot loi w = 0,5, tam I6, lot I4).
      w_buoc / w_tp   0 = I1 (ty le bien do), 1 = I2 (ty le chi phi), giua = pha tron
      tam             "I6" (theo do sau thi truong) | "giu" (giu so tang)
      thoi_gian       "dong_ho" (giu gio) | "so_nen" (giu so nen) - quyet dinh chan troi H cua E(H,q) va muc THOI_GIAN
      lot             "I4" (giu ngan sach rui ro) | "giu" (giu lot)"""
    w_buoc: float = 0.0
    w_tp: float = 0.5
    tam: str = "I6"
    thoi_gian: str = "dong_ho"
    lot: str = "I4"
    q_do_sau: float = 0.9

    def ten(self) -> str:
        b = "I1" if self.w_buoc == 0.0 else ("I2" if self.w_buoc == 1.0 else "w%s" % _s(self.w_buoc))
        return "buoc=%s;tam=%s;gio=%s;lot=%s" % (b, self.tam, self.thoi_gian, self.lot)


@dataclass
class HeSoDich:
    """He so thuc te da ap (sau san / lam tron): dung lai de dich cac gia tri CUNG LOP trong tep .set / the phuong phap."""
    buoc: float = 1.0           # KC_BUOC: khoang cach gia dich / nguon
    tp: float = 1.0             # KC_TP
    sl: float = 1.0             # KC_SL (I1 thuan)
    tam: float = 1.0            # do sau tam luoi dich / nguon (gia)
    lot: float = 1.0            # lot dich / lot nguon (da lam tron)
    tien_tp: float = 1.0        # tien tuyet doi lien quan loi nhuan: lot x khoang cach TP x pv
    tien_tam: float = 1.0       # tien tuyet doi lien quan thua lo: lot x tam x pv
    phi: float = 1.0            # C dich / C nguon
    pip: float = 1.0            # pip nguon / pip dich (don vi pip -> don vi pip)
    point: float = 1.0          # point nguon / point dich
    nen_theo_phut: float = 1.0  # T_nguon / T_dich: so nen dich moi so nen nguon neu giu gio dong ho
    phut_theo_nen: float = 1.0  # T_dich / T_nguon


@dataclass
class KetQuaDich:
    trang_thai: str = OK
    cach: CachDich = field(default_factory=CachDich)
    tham_so: object = None
    he_so: HeSoDich = field(default_factory=HeSoDich)
    chi_tiet: list = field(default_factory=list)
    ly_do: list = field(default_factory=list)
    canh_bao: list = field(default_factory=list)
    engine_do_duoc: bool = True
    engine_ly_do: list = field(default_factory=list)
    cung_ket_qua: list = field(default_factory=list)
    khoang_cach: dict = field(default_factory=dict)

    def tom_tat(self) -> list:
        """3-8 dong loi thuong (ASCII)."""
        dong = ["Cach dich %s: %s." % (self.cach.ten(), "KHONG AP DUOC" if self.trang_thai != OK else "ap duoc")]
        if self.trang_thai != OK:
            dong += ["  - " + x for x in self.ly_do[:4]]
            return dong
        for c in self.chi_tiet:
            if c.get("quan_trong"):
                dong.append("  - " + c["vi_sao"])
        if not self.engine_do_duoc:
            dong.append("  - ENGINE KHONG DO DUOC: " + "; ".join(self.engine_ly_do[:3]) + " (chi tester do duoc)")
        dong += ["  - luu y: " + x for x in self.canh_bao[:2]]
        return dong[:8]

    def to_dict(self) -> dict:
        return {"trang_thai": self.trang_thai, "cach": dataclasses.asdict(self.cach), "ten_cach": self.cach.ten(),
                "tham_so": dataclasses.asdict(self.tham_so) if self.tham_so is not None else None,
                "he_so": dataclasses.asdict(self.he_so), "chi_tiet": self.chi_tiet, "ly_do": self.ly_do,
                "canh_bao": self.canh_bao, "engine_do_duoc": self.engine_do_duoc, "engine_ly_do": self.engine_ly_do,
                "cung_ket_qua": self.cung_ket_qua, "khoang_cach": self.khoang_cach}


def _huong_cua(che_do: str) -> str:
    return {"mua": "mua", "ban": "ban"}.get(che_do, "hai_chieu")


def dich_luoi(ts, src: ThiTruong, dst: ThiTruong, cach: CachDich | None = None, gio_giu_phut: float | None = None,
              tang_tham_chieu: int | None = None) -> KetQuaDich:
    """Dich mot `luoi.ThamSo` tu thi truong `src` sang `dst` theo `cach`. Khong chay engine.

    `gio_giu_phut`      thoi gian giu chuoi dien hinh cua bot (phut, vd p90 tu `ho_so_bot`) - can cho I6; thieu -> giu so tang.
    `tang_tham_chieu`   so tang THUONG DUNG cua bot (vd p90 `chuoi_sau`); mac dinh `ts.tran_tang`. Dung khi tran khai bao
                        (vd 100 lenh) xa hon do sau chuoi that su: TAM va ngan sach rui ro tinh theo do sau THUONG DUNG."""
    cach = cach or CachDich()
    kq = KetQuaDich(cach=cach)

    def hong(msg):
        kq.trang_thai = KHONG_AP_DUOC
        kq.ly_do.append(msg)

    def ghi(ten, lop, nguon, dich, quy_tac, vi_sao, don_vi="", he_so=None, quan_trong=True):
        kq.chi_tiet.append({"ten": ten, "lop": lop, "nguon": nguon, "dich": dich, "don_vi": don_vi, "quy_tac": quy_tac,
                            "he_so": he_so, "vi_sao": vi_sao, "quan_trong": quan_trong})

    # ---- dieu kien cung (khong ap duoc thi dung, khong chay tuy tien)
    for t in thieu_lop():
        hong("luat mot-lop: " + t)
    for ten, tt in (("nguon", src), ("dich", dst)):
        for t in kiem_thi_truong(tt, ten):
            hong(t)
    if src.tien_te != dst.tien_te:
        hong("nguon tinh tien bang %r, dich bang %r: phai cung dong tien" % (src.tien_te, dst.tien_te))
    if ts.che_do not in ("mua", "ban", "hai_chieu"):
        hong("che_do %r khong hop le" % (ts.che_do,))
    if not (ts.buoc > 0):
        hong("buoc nguon phai > 0, nhan %r" % (ts.buoc,))
    if not (ts.lot > 0):
        hong("lot nguon phai > 0, nhan %r" % (ts.lot,))
    if int(ts.tran_tang) < 1:
        hong("tran_tang nguon phai >= 1, nhan %r" % (ts.tran_tang,))
    if not (0.0 <= cach.w_buoc <= 1.0 and 0.0 <= cach.w_tp <= 1.0):
        hong("w_buoc / w_tp phai trong [0,1]")
    if cach.tam not in ("I6", "giu") or cach.thoi_gian not in ("dong_ho", "so_nen") or cach.lot not in ("I4", "giu"):
        hong("cach dich khong hop le: %s" % cach.ten())
    if kq.trang_thai != OK:
        return kq
    kq.khoang_cach = khoang_cach_thi_truong(src, dst)
    if "KHAI" in (src.do_tin_chi_phi, dst.do_tin_chi_phi):
        kq.canh_bao.append("chi phi cua %s la KHAI BAO (khong do duoc): ket qua dua tren no khong bao gio duoc DAT"
                           % ("nguon va dich" if src.do_tin_chi_phi == dst.do_tin_chi_phi == "KHAI" else
                              ("nguon" if src.do_tin_chi_phi == "KHAI" else "dich")))

    che = ts.che_do
    p_s, p_d = src.pip, dst.pip
    hs = kq.he_so
    hs.pip = p_s / p_d
    hs.point = src.point / dst.point
    hs.nen_theo_phut = src.khung_phut / dst.khung_phut
    hs.phut_theo_nen = dst.khung_phut / src.khung_phut

    # ---- nguon = dich: giu nguyen (cap L0)
    if _la_cung_thi_truong(src, dst):
        kq.tham_so = replace(ts)
        ghi("tat_ca", "-", None, None, "giu_nguyen", "nguon va dich la CUNG mot thi truong: giu nguyen moi tham so (khong dich)")
        for o in kq.chi_tiet:
            o["quan_trong"] = True
        return kq

    # ---- KC_BUOC: buoc (+ tran buoc, cho lui theo cung ti le)
    d_buoc_s = ts.buoc * p_s
    d_buoc_d, nang_buoc = dich_do_dai(d_buoc_s, src, dst, cach.w_buoc, True)
    buoc_d = _tron_pip(d_buoc_d / p_d)
    d_buoc_d = buoc_d * p_d
    k_buoc = d_buoc_d / d_buoc_s
    hs.buoc = k_buoc
    buoc_tran_d = _tron_pip(ts.buoc_tran * (buoc_d / ts.buoc)) if ts.buoc_tran > 0 else ts.buoc_tran
    cho_lui_d = _tron_pip(ts.cho_lui * (buoc_d / ts.buoc)) if ts.cho_lui > 0 else 0.0
    ka, kc = dst.A / src.A, dst.C / src.C
    w = cach.w_buoc
    quy = "I1" if w == 0.0 else ("I2" if w == 1.0 else "pha tron w=%s" % _s(w))
    vs = ("buoc luoi %s pip -> %s pip (x%s): %s; bien do nen nguon %s pip, dich %s pip; chi phi mot vong nguon %s pip, dich %s pip"
          % (_sv(ts.buoc), _sv(buoc_d), _sv(k_buoc),
             "giu ti le voi bien do nen (I1)" if w == 0.0 else ("giu ti le voi chi phi (I2)" if w == 1.0 else
                                                                  "pha tron giua ti le bien do (x%s) va ti le chi phi (x%s)" % (_sv(ka), _sv(kc))),
             _sv(src.A / p_s), _sv(dst.A / p_d), _sv(src.C / p_s), _sv(dst.C / p_d)))
    if nang_buoc:
        vs += "; NANG LEN SAN %s lan chi phi mot vong" % _s(SAN_CHI_PHI)
    ghi("buoc", KC_BUOC, ts.buoc, buoc_d, quy + ("+san" if nang_buoc else ""), vs, "pip", k_buoc)
    if ts.buoc_tran > 0 and ts.he_so_buoc != 1.0:
        ghi("buoc_tran", KC_BUOC, ts.buoc_tran, buoc_tran_d, "theo buoc", "tran buoc giu ti le voi buoc dau (x%s)" % _sv(buoc_d / ts.buoc),
            "pip", buoc_d / ts.buoc, quan_trong=False)
    if ts.cho_lui > 0:
        ghi("cho_lui", KC_BUOC, ts.cho_lui, cho_lui_d, "theo buoc", "cho lui %s pip -> %s pip (cung ti le voi buoc)" % (_sv(ts.cho_lui), _sv(cho_lui_d)), "pip",
            buoc_d / ts.buoc)

    # ---- KC_TP: tp, bien_cap
    wt = cach.w_tp
    k_tp_thuan = he_so_ty_le(src, dst, wt)
    tp_d = ts.tp
    k_tp = k_tp_thuan
    if ts.tp > 0:
        d_tp_d, nang_tp = dich_do_dai(ts.tp * p_s, src, dst, wt, True)
        tp_d = _tron_pip(d_tp_d / p_d)
        k_tp = tp_d * p_d / (ts.tp * p_s)
        quy_tp = ("I1" if wt == 0.0 else "I2" if wt == 1.0 else "pha tron w=%s" % _s(wt)) + ("+san" if nang_tp else "")
        vs = "chot loi %s pip -> %s pip (x%s): %s" % (_sv(ts.tp), _sv(tp_d), _sv(k_tp),
                                                      "pha tron w=%s giua ti le bien do (x%s) va ti le chi phi (x%s)" % (_s(wt), _sv(ka), _sv(kc)) if 0.0 < wt < 1.0
                                                      else ("giu ti le voi bien do nen (I1)" if wt == 0.0 else "giu ti le voi chi phi (I2)"))
        if nang_tp:
            vs += "; NANG LEN SAN %s lan chi phi mot vong" % _s(SAN_CHI_PHI)
        ghi("tp", KC_TP, ts.tp, tp_d, quy_tp, vs, "pip", k_tp)
    hs.tp = k_tp
    bien_cap_d = ts.bien_cap
    if ts.bien_cap > 0:
        d_bc, nang_bc = dich_do_dai(ts.bien_cap * p_s, src, dst, wt, bool(ts.tia_lenh))
        bien_cap_d = _tron_pip(d_bc / p_d)
        ghi("bien_cap", KC_TP, ts.bien_cap, bien_cap_d, "tp" + ("+san" if nang_bc else ""),
            "bien cap tia %s pip -> %s pip (cung luat voi chot loi)%s" % (_sv(ts.bien_cap), _sv(bien_cap_d), "" if ts.tia_lenh else " [tia dang tat: chua tac dung]"),
            "pip", bien_cap_d * p_d / (ts.bien_cap * p_s), quan_trong=bool(ts.tia_lenh))
    hs.sl = he_so_ty_le(src, dst, 0.0)

    # ---- TAM + so tang (I6)
    n_nguon = int(ts.tran_tang)
    n_ref = min(int(tang_tham_chieu), n_nguon) if tang_tham_chieu else n_nguon
    if n_ref < 1:
        n_ref = 1
    hinh_s = hinh_rui_ro(ts.buoc, ts.he_so_buoc, ts.buoc_tran, ts.kieu_lot, ts.he_so_lot, n_ref)
    tam_s_gia = hinh_s["tam"] * p_s
    n_ref_d = n_ref
    k_tam = None
    if cach.tam == "I6" and n_ref >= 2:
        if not gio_giu_phut or gio_giu_phut <= 0:
            kq.canh_bao.append("khong biet thoi gian giu chuoi (gio_giu_phut) -> khong dich tam theo do sau thi truong (I6), giu so tang")
        else:
            h_s = max(1, int(round(gio_giu_phut / src.khung_phut)))
            h_d = h_s if cach.thoi_gian == "so_nen" else max(1, int(round(gio_giu_phut / dst.khung_phut)))
            e_s = src.do_sau(h_s, cach.q_do_sau, _huong_cua(che))
            e_d = dst.do_sau(h_d, cach.q_do_sau, _huong_cua(che))
            if e_s is None or e_d is None or not (e_s > 0 and e_d > 0):
                kq.canh_bao.append("khong do duoc do sau thi truong E(H,q) (thieu gia hoac chuoi qua ngan cho H = %d / %d nen) -> giu so tang" % (h_s, h_d))
            else:
                k_tam = e_d / e_s
                tam_d_gia = tam_s_gia * k_tam
                n_ref_d = so_tang_cho_tam(tam_d_gia / p_d, buoc_d, ts.he_so_buoc, buoc_tran_d, n_min=2)
                vs = ("tam luoi (%d tang): %s pip -> muc tieu %s pip theo do sau thi truong (I6: phan vi %s cua do lech nguoc lon nhat trong %s gio: "
                      "nguon %s pip, dich %s pip, x%s) => %d tang"
                      % (n_ref, _sv(hinh_s["tam"]), _sv(tam_d_gia / p_d), _s(cach.q_do_sau), _sv(gio_giu_phut / 60.0),
                         _sv(e_s / p_s), _sv(e_d / p_d), _sv(k_tam), n_ref_d))
                ghi("tam", TAM, hinh_s["tam"], tam_d_gia / p_d, "I6", vs, "pip", k_tam)
    if k_tam is None:
        vs = "so tang giu nguyen %d (tam dich theo buoc dich: x%s)" % (n_ref, _sv(k_buoc))
        ghi("tam", TAM, hinh_s["tam"], None, "giu_so_tang", vs, "pip", None, quan_trong=False)
    if tang_tham_chieu and tang_tham_chieu < n_nguon and n_ref_d != n_ref:
        tran_d = max(n_ref_d, int(round(n_nguon * n_ref_d / n_ref)))
    elif tang_tham_chieu and tang_tham_chieu < n_nguon:
        tran_d = n_nguon
    else:
        tran_d = n_ref_d
    if tran_d != n_nguon:
        ghi("tran_tang", SO_DEM, n_nguon, tran_d, "tu tam", "so tang toi da %d -> %d (tinh lai tu tam dich va buoc dich)" % (n_nguon, tran_d), "tang", None)
    hinh_d = hinh_rui_ro(buoc_d, ts.he_so_buoc, buoc_tran_d, ts.kieu_lot, ts.he_so_lot, n_ref_d)
    tam_d_gia_thuc = hinh_d["tam"] * p_d
    hs.tam = (tam_d_gia_thuc / tam_s_gia) if tam_s_gia > 0 else k_buoc

    # ---- LOT (I4)
    mat_s = ts.lot * src.pv * hinh_s["mat_tai_tam"] * p_s
    pct_s = mat_s / src.von * 100.0
    lot_d = ts.lot
    if cach.lot == "I4":
        mat_d_don_vi = dst.pv * hinh_d["mat_tai_tam"] * p_d
        if not (mat_d_don_vi > 0 and math.isfinite(mat_d_don_vi)):
            hong("khong tinh duoc thua lo tai tam o thi truong dich")
            return kq
        lot_tho = ts.lot * (src.pv * hinh_s["mat_tai_tam"] * p_s / src.von) / (mat_d_don_vi / dst.von)
        if lot_tho < dst.lot_toi_thieu - 1e-12:
            hong("von khong du de chay luoi nay o thi truong dich: giu nguyen ngan sach rui ro can lot %s < lot toi thieu %s "
                 "(tai tam mat %s%% von nguon)" % (_sv(lot_tho), _sv(dst.lot_toi_thieu), _sv(pct_s)))
            return kq
        lot_d = max(dst.lot_toi_thieu, _lam_tron_lot(lot_tho, dst.lot_buoc))
        pct_d = lot_d * mat_d_don_vi / dst.von * 100.0
        vs = ("lot %s -> %s (x%s): giu phan tram von mat khi gia di nguoc het tam luoi (I4): nguon %s%% von, dich %s%% von"
              % (_sv(ts.lot), _sv(lot_d), _sv(lot_d / ts.lot), _sv(pct_s), _sv(pct_d)))
        ghi("lot", LOT, ts.lot, lot_d, "I4", vs, "lot", lot_d / ts.lot)
    else:
        pct_d = lot_d * dst.pv * hinh_d["mat_tai_tam"] * p_d / dst.von * 100.0
        ghi("lot", LOT, ts.lot, lot_d, "giu", "lot giu nguyen %s: phan tram von mat o tam luoi doi tu %s%% (nguon) sang %s%% (dich)"
            % (_sv(lot_d), _sv(pct_s), _sv(pct_d)), "lot", 1.0)
    hs.lot = lot_d / ts.lot
    if pct_d >= TRAN_RUI_RO_PCT:
        kq.canh_bao.append("tai tam luoi thi truong dich mat %s%% von (>= %s%% = tran sut giam du an)" % (_sv(pct_d), _s(TRAN_RUI_RO_PCT)))

    # ---- TIEN (tien tren 0,01 lot: ti le lot triet tieu), PHI
    pv_ty = dst.pv / src.pv
    hs.tien_tp = k_tp * pv_ty * hs.lot
    hs.tien_tam = hs.tam * pv_ty * hs.lot
    hs.phi = dst.C / src.C
    chot_d = ts.chot_tien
    if ts.chot_tien > 0:
        chot_d = float("%.4g" % (ts.chot_tien * k_tp * pv_ty))
        ghi("chot_tien", TIEN, ts.chot_tien, chot_d, "TIEN",
            "chot theo tien %s -> %s (tren 0,01 lot): nhan ti le khoang cach chot loi (x%s) va gia tri diem (x%s)"
            % (_sv(ts.chot_tien), _sv(chot_d), _sv(k_tp), _sv(pv_ty)), "tien/0,01 lot", k_tp * pv_ty)
    dung_lo_d = ts.dung_lo_tong
    if ts.dung_lo_tong != 0:
        k_dl = (hs.tam if tam_s_gia > 0 else k_buoc) * pv_ty
        dung_lo_d = float("%.4g" % (ts.dung_lo_tong * k_dl))
        ghi("dung_lo_tong", TIEN, ts.dung_lo_tong, dung_lo_d, "TIEN", "dung lo toan cuc %s -> %s (theo tam luoi va gia tri diem)" % (_sv(ts.dung_lo_tong), _sv(dung_lo_d)),
            "tien/0,01 lot", k_dl)
        kq.engine_do_duoc = False
        kq.engine_ly_do.append("dung_lo_tong: luoi.py CHUA cai dat (luoi.CHUA_CAI_DAT)")

    # ---- CO CHE THOAT (cat lo ca ro, thoat theo gio, nghi): mac dinh 0 = TAT thi khong dich gi. Khoang cach cat lo theo I1 thuan (nhu moi
    # KC_SL: `hs.sl`), tien theo khoang cach do va gia tri diem (khong nhan lot: la tien tren 0,01 lot), gio dong ho giu / giu so nen (I5).
    cat_pip_d, cat_tien_d, thoat_d, nghi_d = ts.cat_lo_pip, ts.cat_lo_tien, ts.thoat_gio, ts.nghi_gio
    if ts.cat_lo_pip > 0:
        cat_pip_d = _tron_pip(ts.cat_lo_pip * hs.sl * hs.pip)
        ghi("cat_lo_pip", KC_SL, ts.cat_lo_pip, cat_pip_d, "I1", "cat lo ca ro %s pip -> %s pip (x%s): giu ti le voi bien do nen (I1)"
            % (_sv(ts.cat_lo_pip), _sv(cat_pip_d), _sv(cat_pip_d * p_d / (ts.cat_lo_pip * p_s))), "pip", cat_pip_d * p_d / (ts.cat_lo_pip * p_s))
    if ts.cat_lo_tien > 0:
        k_ct = hs.sl * pv_ty
        cat_tien_d = float("%.4g" % (ts.cat_lo_tien * k_ct))
        ghi("cat_lo_tien", TIEN, ts.cat_lo_tien, cat_tien_d, "TIEN", "cat lo ca ro theo tien %s -> %s (tren 0,01 lot): nhan ti le khoang cach (x%s) "
            "va gia tri diem (x%s)" % (_sv(ts.cat_lo_tien), _sv(cat_tien_d), _sv(hs.sl), _sv(pv_ty)), "tien/0,01 lot", k_ct)
    k_gio = hs.phut_theo_nen if cach.thoi_gian == "so_nen" else 1.0
    for ten_g, v_g in (("thoat_gio", ts.thoat_gio), ("nghi_gio", ts.nghi_gio)):
        if v_g > 0:
            moi_g = v_g if k_gio == 1.0 else float("%.4g" % (v_g * k_gio))
            if ten_g == "thoat_gio":
                thoat_d = moi_g
            else:
                nghi_d = moi_g
            ghi(ten_g, THOI_GIAN, v_g, moi_g, "I5_" + cach.thoi_gian, "%s %s gio -> %s gio (%s)" % (
                "thoat theo gio" if ten_g == "thoat_gio" else "nghi sau khi cat", _sv(v_g), _sv(moi_g),
                "giu gio dong ho" if k_gio == 1.0 else "giu so nen: x%s" % _sv(k_gio)), "gio", k_gio, quan_trong=False)

    # ---- ap dung + giu nguyen cac truong con lai
    kq.tham_so = replace(ts, buoc=buoc_d, tp=tp_d, tran_tang=tran_d, lot=lot_d, cho_lui=cho_lui_d, bien_cap=bien_cap_d,
                         chot_tien=chot_d, dung_lo_tong=dung_lo_d, buoc_tran=buoc_tran_d,
                         cat_lo_pip=cat_pip_d, cat_lo_tien=cat_tien_d, thoat_gio=thoat_d, nghi_gio=nghi_d)
    giu = [t for t, l in LOP_THAM_SO_LUOI.items() if l in (HE_SO, CONG_TAC) or t == "cap_moi_bar"]
    ghi("giu_nguyen", "-", None, None, "giu", "giu nguyen: " + ", ".join(sorted(giu)), quan_trong=False)

    # ---- phan giai: MOI khoang cach phai >= 2 lan bien do nen (luat pmg_engine); duoi nguong: engine khong do noi
    ts_d = kq.tham_so
    kiem = [("buoc", ts_d.buoc, True), ("chot loi", ts_d.tp, ts_d.chot_tien <= 0), ("bien cap tia", ts_d.bien_cap, bool(ts_d.tia_lenh)),
            ("cho lui", ts_d.cho_lui, True), ("cat lo ca ro", ts_d.cat_lo_pip, True)]
    for nhan, v, dung in kiem:
        if dung and v and v > 0:
            ty = v * p_d / dst.A
            if ty < NGUONG_PHAN_GIAI:
                kq.engine_do_duoc = False
                kq.engine_ly_do.append("%s %s pip = %sx bien do nen (can >= %s)" % (nhan, _sv(v), _sv(ty), _s(NGUONG_PHAN_GIAI)))
    if ts_d.chot_tien > 0:
        kq.canh_bao.append("chot theo tien khong kiem duoc phan giai truoc khi chay (xem hephaestus.NUT_THEO_TIEN)")
    return kq


def cac_cach_dich(ts, src: ThiTruong, dst: ThiTruong, gio_giu_phut: float | None = None, tang_tham_chieu: int | None = None,
                  q_do_sau: float = 0.9, lot: str = "I4") -> list:
    """Danh sach <= 9 cach dich CO SO (thiet ke muc 8.2): buoc {I1, pha tron 0,5} x tam {I6, giu} x thoi gian {dong ho, so nen};
    them 'I2 thuan' khi ti le chi phi / bien do doi tu 2 lan. Cac cach cho ra CUNG tham so duoc gop (`cung_ket_qua`).
    `lot`: cach chia lot cua MOI cach ('I4' giu ngan sach rui ro | 'giu' giu lot); chon 'giu' khi lot se do cong chot sau (bo thu chuyen S1 /
    quy trinh tim: lot nho nhat 0,01 khong chia duoc nua thi 'I4' tra KHONG_AP_DUOC)."""
    cac = []
    for w in (0.0, 0.5):
        for tam in ("I6", "giu"):
            for tg in ("dong_ho", "so_nen"):
                cac.append(CachDich(w_buoc=w, tam=tam, thoi_gian=tg, q_do_sau=q_do_sau, lot=lot))
    if _hop_le(src.A) and _hop_le(src.C) and _hop_le(dst.A) and _hop_le(dst.C):
        if abs(math.log((dst.C / dst.A) / (src.C / src.A))) >= math.log(NGUONG_CHI_PHI_AP_DAO):
            cac.append(CachDich(w_buoc=1.0, tam="I6", thoi_gian="dong_ho", q_do_sau=q_do_sau, lot=lot))
    ra, thay = [], {}
    for c in cac:
        k = dich_luoi(ts, src, dst, c, gio_giu_phut, tang_tham_chieu)
        khoa = (k.trang_thai, dataclasses.astuple(k.tham_so) if k.tham_so is not None else tuple(k.ly_do), k.engine_do_duoc)
        if khoa in thay:
            thay[khoa].cung_ket_qua.append(c.ten())
        else:
            thay[khoa] = k
            ra.append(k)
    return ra[:TOI_DA_CACH_DICH]


# ------------------------------------------------------------------------------------------------------ tep .set
def _chuan(ten: str) -> str:
    return re.sub(r"^Inp(?=[A-Z0-9_])", "", str(ten).strip()).lower()


#: (mau, lop, don_vi) tren ten da chuan hoa (bo "Inp", chu thuong). THU TU quan trong: luat khop DAU TIEN thang (chi bao ngoai dung
#: truoc luat chung vi ten co 'multiplier' / 'period' / 'price'; 'period...' dung truoc 'per...').
_LUAT_TEN_SET = (
    (r"^(show|magic|combine|nameindi|buybuffer|sellbuffer|barsignal|utbot_show|utbot_arrow)", CONG_TAC, ""),
    (r"^(indimode|stochmamethod|stochprice|cciprice|momentumprice|rsiapplyprice|appliedpricemacd|bbprice|typebuysell|dcamode|coeffmode|addbllmode)$", CONG_TAC, ""),
    (r"^(cciperiod|stochkperiod|stochdperiod|stochslowing|momentumperiod|rsiperiod|bbperiod|periodsindi\w*|utbot_nbr_periods|fastemamacd|slowemamacd|smamacd|ichi(tenkan|kijun|senkou)|ema\d+)$", THOI_GIAN, "nen"),
    (r"^(\w*overbought\w*|\w*oversold\w*|bbdeviations|multiplierindi\w*|utbot_multiplier)$", NGUONG_CHI_BAO, "muc"),
    (r"^tf\w+$", THOI_GIAN, "khung"),
    (r"^maxdist\w*$", KC_BUOC, "pip"),
    (r"^(lots|lotsopp|resetlots|maxlots|maxlotshedgingzone|addlotsbll|minlotssniper|difflots2\w+)$", LOT, "lot"),
    (r"^(multiplier\w*|newmultiplier\d*|hedgingzonemultiplier|distancemulti|mulisniper)$", HE_SO, ""),
    (r"^(orders2\w*|maxbuyorders|maxsellorders|firstorders\w*|lastorders\w*|allorders2\w*)$", SO_DEM, "lenh"),
    (r"^(distance\d+|zonehedgingpips)$", KC_BUOC, "pip"),
    (r"^(tp|tpdca|singletp|tphedging|tpallwhenhedging|pipstpallhedgingzone|tpreset|tpdcachange|tpsniper)$", KC_TP, "pip"),
    (r"^(sl|initialsltrailing|trailingstart|trailingstep)$", KC_SL, "pip"),
    (r"^(new)?(daily)?money\w*$", TIEN, "tien"),
    (r"^(per(?!iod)\w*|percent\w*|dailyper\w+|minper\w+)$", TIEN, "pct"),
    (r"^maxspread$", PHI, "point"),
    (r"^(starttime\d*|endtime\d*)$", THOI_GIAN, "gio_ngay"),
    (r"^minutedelay\w*$", THOI_GIAN, "phut"),
    (r"^(delay\w*)$", THOI_GIAN, "khong_ro"),
    (r"^use\w*$", CONG_TAC, ""),
)
_LUAT_TEN_SET_BIEN = tuple((re.compile(m), lop, dv) for m, lop, dv in _LUAT_TEN_SET)
_RX_GIO_NGAY = re.compile(r"^\s*\d{1,2}:\d{2}(:\d{2})?\s*$")
_RX_SO = re.compile(r"^\s*[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?\s*$")


def lop_khoa_set(ten: str, gia_tri=None) -> tuple:
    """(lop, don_vi) cua mot khoa .set: theo GIA TRI truoc (true/false -> CONG_TAC, HH:MM -> THOI_GIAN, chuoi khong phai so ->
    CONG_TAC), roi theo TEN. Khong khop luat nao = (CHUA_PHAN_LOP, ""): de nguoi / LLM xem xet, KHONG tu doan."""
    if gia_tri is not None:
        v = str(gia_tri).strip()
        if v.lower() in ("true", "false"):
            return CONG_TAC, ""
        if _RX_GIO_NGAY.match(v):
            return THOI_GIAN, "gio_ngay"
        if v != "" and not _RX_SO.match(v):
            return CONG_TAC, ""
    n = _chuan(ten)
    for rx, lop, dv in _LUAT_TEN_SET_BIEN:
        if rx.match(n):
            return lop, dv
    return CHUA_PHAN_LOP, ""


def _khung_gan_nhat(ma: int) -> int:
    """Ma khung MT5 (PERIOD_*, phut) -> giu nguyen: `.set` luu ma phut hoac hang so enum lon; khong dich."""
    return ma


def dich_gia_tri(lop: str, gia_tri, don_vi: str, hs: HeSoDich, src: ThiTruong, dst: ThiTruong, thoi_gian: str = "dong_ho",
                 ten: str = "") -> tuple:
    """Dich MOT gia tri so cua mot tham so theo lop. Tra (gia_tri_moi | None, quy_tac, ghi_chu); None = giu nguyen.
    `hs` la `HeSoDich` cua mot lan `dich_luoi` (cung bo he so cho moi khoa cung lop)."""
    try:
        v = float(str(gia_tri).strip())
    except (TypeError, ValueError):
        return None, "giu", "khong phai so"
    if lop in (CONG_TAC, HE_SO, SO_DEM, NGUONG_CHI_BAO, TAM, CHUA_PHAN_LOP):
        return None, "giu", ""
    if v == 0.0:
        return None, "giu", "bang 0 (tat)"
    if lop == KC_BUOC:
        return _tron_pip(v * hs.buoc * hs.pip), "KC_BUOC", "x%s" % _sv(hs.buoc * hs.pip)
    if lop == KC_TP:
        return _tron_pip(v * hs.tp * hs.pip), "KC_TP", "x%s" % _sv(hs.tp * hs.pip)
    if lop == KC_SL:
        return _tron_pip(abs(v) * hs.sl * hs.pip) * (1 if v > 0 else -1), "KC_SL", "x%s" % _sv(hs.sl * hs.pip)
    if lop == LOT:
        moi = _lam_tron_lot(v * hs.lot, dst.lot_buoc)
        if v > 0 and moi < dst.lot_toi_thieu:
            moi = dst.lot_toi_thieu
        return moi, "LOT", "x%s (da lam tron buoc lot %s)" % (_sv(hs.lot), _sv(dst.lot_buoc))
    if lop == TIEN:
        if don_vi == "pct":
            return None, "giu", "phan tram: giu (ngan sach rui ro da giu theo I4)"
        n = _chuan(ten)
        theo_tp = any(t in n for t in ("tp", "profit", "target", "sniper")) and not any(t in n for t in ("sl", "loss", "stop"))
        k = hs.tien_tp if theo_tp else hs.tien_tam
        return float("%.4g" % (v * k)), "TIEN", "x%s (%s)" % (_sv(k), "theo chot loi" if theo_tp else "theo tam luoi")
    if lop == PHI:
        return float("%.4g" % (v * hs.phi * hs.point)), "PHI", "x%s" % _sv(hs.phi * hs.point)
    if lop == THOI_GIAN:
        if don_vi in ("gio_ngay", "khung"):
            return None, "giu", "gio dong ho / khung chi bao: giu"
        if don_vi == "nen":
            if thoi_gian == "dong_ho":
                moi = max(1, int(round(v * hs.nen_theo_phut)))
                return (None, "giu", "") if moi == v else (moi, "I5_dong_ho", "x%s (giu gio dong ho)" % _sv(hs.nen_theo_phut))
            return None, "I5_so_nen", "giu so nen"
        if don_vi in ("phut", "khong_ro"):
            if thoi_gian == "dong_ho" or don_vi == "khong_ro":
                return None, "giu", "giu gio dong ho" if don_vi == "phut" else "don vi khong ro: giu"
            moi = max(1, int(round(v * hs.phut_theo_nen)))
            return (None, "giu", "") if moi == v else (moi, "I5_so_nen", "x%s (giu so nen)" % _sv(hs.phut_theo_nen))
    return None, "giu", ""


def dich_bo_set(khoa: dict, kq: KetQuaDich, src: ThiTruong, dst: ThiTruong, thoi_gian: str | None = None,
                nen_theo_khung_bieu_do: bool = False) -> dict:
    """Dich cac khoa so cua mot bo .set theo `HeSoDich` cua mot lan `dich_luoi` (khoa -> van ban). Chi tra khoa DOI.
    `khoa` = {ten: gia_tri} (vi du `ea_tho.doc_set(...)["khoa"]`). Khoa chua phan lop duoc liet ke rieng (khong tu doan).
    Gia dinh: 1 don vi pip trong .set = `ThiTruong.pip` cua tung thi truong (do ben nhan: vang 1 pip = 0,1 USD).
    `nen_theo_khung_bieu_do`: mac dinh False = so nen cua chi bao GIU NGUYEN (chi bao cua EA chay tren khung tin hieu
    InpTF... cua chinh no, khong phai khung bieu do); True = chi bao theo khung bieu do -> doi so nen theo ti le khung (I5)."""
    tg = thoi_gian or kq.cach.thoi_gian
    doi, giu, chua, chi_tiet = {}, [], [], []
    for ten, gt in khoa.items():
        lop, dv = lop_khoa_set(ten, gt)
        if lop == CHUA_PHAN_LOP:
            chua.append(ten)
            continue
        if lop == THOI_GIAN and dv == "nen" and not nen_theo_khung_bieu_do:
            giu.append(ten)
            continue
        moi, quy, ghi_chu = dich_gia_tri(lop, gt, dv, kq.he_so, src, dst, tg, ten)
        if moi is None:
            giu.append(ten)
            continue
        if isinstance(moi, float) and moi == int(moi) and "." not in str(gt):
            moi_s = str(int(moi))
        else:
            moi_s = ("%.10g" % moi)
        if moi_s != str(gt).strip():
            doi[ten] = moi_s
            chi_tiet.append({"ten": ten, "lop": lop, "don_vi": dv, "nguon": str(gt), "dich": moi_s, "quy_tac": quy, "ghi_chu": ghi_chu})
        else:
            giu.append(ten)
    return {"doi": doi, "giu": giu, "chua_phan_lop": chua, "chi_tiet": chi_tiet,
            "dem": {"doi": len(doi), "giu": len(giu), "chua_phan_lop": len(chua)}}
