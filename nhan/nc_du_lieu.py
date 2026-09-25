# -*- coding: utf-8 -*-
"""nc_du_lieu.py - DU LIEU CHO NHA NGHIEN CUU: ba doan co niem phong + chuoi TONG HOP co dap an.

Module nay la tang duoi cua `nhan/nc_*` (NHA NGHIEN CUU - AI nam quyen, xem
`tai_lieu/NHA_NGHIEN_CUU.md`). No lam DUNG HAI viec, va ca hai deu la chot chan
chong tu lua minh khi mot AI duoc tu do thu hang nghin bien the:

## 1. BA DOAN, doan cuoi bi NIEM PHONG

    kham_pha    [0%, 60%)   AI thu thoai mai: quet, mo xe lenh, tim quy luat
    xac_nhan    [60%, 80%)  chi de XAC NHAN mot bien the da chon - moi lan nhin
                            deu bi dem (`nc_so_tay`), nhin nhieu thi nhan canh bao
    niem_phong  [80%, 100%] chi mo MOT LAN cho mot khai bao DA DONG BANG
                            (`nc_thi_nghiem.niem_phong`). Khong cong cu nao khac
                            doc duoc doan nay - `cat_doan` tu choi thang.

Vi sao 60%: trung voi quy uoc `du_lieu.hai_nua(df, 0.6)` cua ca du an (train 60%
/ holdout 40%). Nha nghien cuu KHONG BAO GIO cham vao 40% cuoi trong luc kham
pha, dung nhu luat cu - chi chia 40% do thanh hai nua de co mot cho XAC NHAN
truoc khi dot phat cuoi cung.

Chi bao can lich su (phan_vi 250 bar...). Nen moi doan tra ve TIEN TO du lieu
toi het doan + chi so bat dau: tin hieu tinh tren tien to (ngu phap khong nhin
truoc nen gia tri tai t chi phu thuoc du lieu <= t), con tien chi tinh trong
doan. Doan sau khong mat 250 bar dau vi thieu lich su.

## 2. CHUOI TONG HOP CO DAP AN (`TONG_HOP_<KICH_BAN>_<HAT>`)

Luat cua du an: *"bo suy nguoc phai co BAI KIEM CO DAP AN"* (BAN_GIAO muc 8.7)
va *"hieu chuan cong phai HAI CHIEU"*. Mot nha nghien cuu tu dong ma chua tung
duoc thu tren chuoi BIET TRUOC dap an thi moi phat hien cua no chi la loi
khang dinh. Nen o day co bon kich ban sinh bang may, cai edge o dung cho da
biet:

    NHIEU      khong co edge nao. Moi "phat hien" la duong tinh gia -> do ti le
               bao dong gia cua bo tim quy luat va bo mo xe.
    HOI_QUY    "A KHI B": IBS thap VA bien dong dang cao -> bar sau co troi
               duong 0,5 sigma (doi xung chieu ban). Dung dang co che duy nhat
               tung song o lab (IBS bat day co dieu kien).
    HOI_QUY_YEU  cung co che, troi 0,3 sigma: sau phi chi con t ~ 2,3. Do tim
               rong (~3.000 dieu kien) gan nhu KHONG thay; mot gia thuyet co chu
               dich (1 phep thu) thay. Day la bai do gia tri cua tu duy AI.
    LOC        sau cu di manh 3 bar (ca hai chieu): bien dong THAP thi hoi lai,
               bien dong CAO thi di tiep. He "mua sau 3 bar giam" goc thua; chi
               mo xe lenh moi tim ra bo loc bien dong. Day la bai kiem cua cau
               hoi chu du an dat: AI co hoc duoc tu lenh dung/lenh sai khong.
    XU_HUONG   BAY CHI PHI: quan tinh ngan co that (tu tuong quan +0,07) nhung
               nho hon chi phi khu hoi. Dap an dung: KHONG co he ra tien - he
               nao "tim ra" o day la dang quen tru phi.

Chuoi tong hop KHONG BAO GIO la ket qua giao dich: `la_tong_hop()` chan chung
khoi xuat MQL5 va khoi moi bao cao "he ra tien".
"""
from __future__ import annotations

import hashlib
import sys
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import chi_phi as CP
else:
    from . import chi_phi as CP

#: Ranh gioi ba doan, tinh theo TI LE so bar.
DOAN = {"kham_pha": (0.0, 0.6), "xac_nhan": (0.6, 0.8), "niem_phong": (0.8, 1.0)}
#: Doan ma cong cu thuong duoc phep doc. `niem_phong` co cua rieng.
DOAN_MO = ("kham_pha", "xac_nhan")

TIEN_TO_TONG_HOP = "TONG_HOP_"
KICH_BAN = {
    "NHIEU": "khong co edge - moi phat hien la duong tinh gia",
    "HOI_QUY": "A khi B: IBS < 0,15 VA phan vi ATR > 0,65 -> bar sau troi duong 0,5 sigma "
               "(IBS > 0,85 VA bien dong cao -> troi am)",
    "HOI_QUY_YEU": "nhu HOI_QUY nhung troi chi 0,3 sigma: SAU PHI con t ~ 2,3 tren kham pha - "
                   "do cong suat: do tim rong vs gia thuyet co chu dich",
    "LOC": "sau cu di 3 bar > 1 sigma (ca hai chieu): bien dong thap (phan vi "
           "ATR < 0,5) -> hoi nguoc 5 bar, bien dong cao -> di tiep 5 bar",
    "XU_HUONG": "BAY CHI PHI: loi suat tu tuong quan duong bac 1 (he so 0,07) - quan tinh "
                "THAT nhung sau mot cu soc chi con ~3 bps, xap xi chi phi khu hoi. Dap an "
                "dung: ho so thay quan tinh, nhung KHONG co he nao ra tien sau phi",
}
#: Kich ban nao co edge GIAO DICH DUOC sau chi phi - dap an cua `nc_tu_lai.hieu_chuan`.
CO_EDGE_SAU_PHI = {"NHIEU": False, "HOI_QUY": True, "HOI_QUY_YEU": True, "LOC": True,
                   "XU_HUONG": False}
BAR_MOI_NGAY = {"H1": 24, "H4": 6, "D1": 1}
BAR_MOI_NAM = {"H1": 24 * 260, "H4": 6 * 260, "D1": 260}

_DEM: dict = {}
_DEM_CP: dict = {}


class DoanNiemPhong(PermissionError):
    """Doc doan niem phong ngoai cua `nc_thi_nghiem.niem_phong`."""


# ------------------------------------------------------------------ DOAN
def chi_so_doan(n: int, doan: str) -> tuple[int, int]:
    """(a, b) so nguyen: doan la [a, b) cua chuoi dai n."""
    if doan not in DOAN:
        raise KeyError("doan '%s' khong co (co: %s)" % (doan, ", ".join(DOAN)))
    t0, t1 = DOAN[doan]
    return int(round(n * t0)), int(round(n * t1))


def cat_doan(df: pd.DataFrame, doan: str, _giay_phep: bool = False
             ) -> tuple[pd.DataFrame, int]:
    """-> (TIEN TO du lieu toi het doan, chi so bat dau cua doan trong tien to).

    `niem_phong` chi mo khi `_giay_phep=True`, va chi `nc_thi_nghiem.niem_phong`
    truyen co do. Cong cu, tac tu, nguoi goi tay deu di qua `DOAN_MO`.
    """
    if doan == "niem_phong" and not _giay_phep:
        raise DoanNiemPhong(
            "doan niem_phong chi mo qua nc_thi_nghiem.niem_phong (mot lan, cho "
            "khai bao da dong bang). Kham pha tren 'kham_pha', xac nhan tren "
            "'xac_nhan'.")
    a, b = chi_so_doan(len(df), doan)
    return df.iloc[:b], a


# ------------------------------------------------------------------ NAP
def la_tong_hop(ma: str) -> bool:
    return str(ma).upper().startswith(TIEN_TO_TONG_HOP)


def _tach_ten_tong_hop(ma: str) -> tuple[str, int]:
    than = str(ma).upper()[len(TIEN_TO_TONG_HOP):]
    kb, _, hat = than.rpartition("_")
    if not kb or kb not in KICH_BAN or not hat.isdigit():
        raise KeyError("ten tong hop phai la TONG_HOP_<%s>_<hat so>, nhan '%s'"
                       % ("|".join(KICH_BAN), ma))
    return kb, int(hat)


def nap(ma: str, khung: str = "H4") -> pd.DataFrame:
    """Nap TOAN BO chuoi cua (ma, khung). Nho trong tien trinh.

    Ma that di qua `du_lieu.nap` (dung duong cua ca du an: sua bar hong, cat
    doan tho, cache parquet). Ma `TONG_HOP_*` sinh bang `tong_hop`.
    """
    ma = str(ma).upper()
    khung = str(khung).upper()
    khoa = (ma, khung)
    if khoa in _DEM:
        return _DEM[khoa]
    if la_tong_hop(ma):
        kb, hat = _tach_ten_tong_hop(ma)
        df = tong_hop(kb, hat=hat, khung=khung)
    else:
        from nhan import du_lieu as DL
        df = DL.nap(ma, khung)
    if len(_DEM) >= 12:
        _DEM.pop(next(iter(_DEM)))
    _DEM[khoa] = df
    return df


def chi_phi(ma: str, df: pd.DataFrame) -> CP.MoHinhChiPhi:
    """Mo hinh chi phi cho `df` (tien to cua doan dang xet).

    Ma that: `chi_phi.tu_du_lieu` - dung duong DO/SAN/KHAI cua du an, nen nhan
    `do_tin` di theo va cong niem phong doc no. Ma tong hop: may SINH ra spread
    nen biet dung no - `do_tin="DO"`, nhung `la_tong_hop` van chan moi duong ra
    tien that.
    """
    khoa = (str(ma).upper(), len(df), str(df.index[-1]) if len(df) else "")
    if khoa in _DEM_CP:
        return _DEM_CP[khoa]
    if la_tong_hop(ma):
        sp = float(np.nanmedian(df["spread"].to_numpy(float))) * 1e-5 \
            / float(np.nanmedian(df["close"].to_numpy(float)))
        cp = CP.MoHinhChiPhi(ma=str(ma).upper(), spread_frac_chung=sp,
                             truot_gia_frac=sp * 0.25, phi_nam_mua=0.01,
                             phi_nam_ban=0.01, do_tin="DO",
                             nguon="tong_hop: spread do may sinh")
    else:
        c = CP.tu_du_lieu(ma, df)
        cp = c[0] if isinstance(c, tuple) else c
    if len(_DEM_CP) >= 32:
        _DEM_CP.pop(next(iter(_DEM_CP)))
    _DEM_CP[khoa] = cp
    return cp


def danh_sach(gom_tong_hop: bool = True) -> list[dict]:
    """Tai san nha nghien cuu dung duoc: ma that trong `data/` + chuoi tong hop."""
    ra: list[dict] = []
    try:
        from nhan import du_lieu as DL
        for ma, g in sorted(DL.kho().items()):
            if not g.get("du_ohlc"):
                continue
            ra.append({"ma": ma, "khung_min": g.get("khung_min"),
                       "so_nam": g.get("uoc_so_nam"),
                       "co_spread": bool(g.get("co_spread")),
                       "nguon": g.get("lop_nguon") or g.get("nguon"),
                       "tong_hop": False})
    except Exception as e:  # khong co data/ (vd tren cloud): van tra tong hop
        ra.append({"loi": "khong doc duoc kho du lieu that: %s" % str(e)[:160]})
    if gom_tong_hop:
        for kb, mo_ta in KICH_BAN.items():
            ra.append({"ma": "%s%s_1" % (TIEN_TO_TONG_HOP, kb), "khung_min": "H1",
                       "so_nam": round(9000 / BAR_MOI_NAM["H4"], 1),
                       "co_spread": True, "nguon": "tong_hop", "tong_hop": True,
                       "dap_an": mo_ta})
    return ra


# ------------------------------------------------------------ TONG HOP
def _hat_kich_ban(kich_ban: str, hat: int) -> int:
    h = hashlib.sha1(("%s:%d" % (kich_ban, hat)).encode()).hexdigest()
    return int(h[:8], 16)


def _chi_muc(so_bar: int, khung: str) -> pd.DatetimeIndex:
    """Chi muc thoi gian that: chi ngay trong tuan, gio dong theo khung."""
    moi_ngay = BAR_MOI_NGAY[khung]
    buoc = 24 // moi_ngay
    so_ngay = so_bar // moi_ngay + 10
    ngay = pd.bdate_range("2011-01-03", periods=so_ngay)
    gio = np.arange(moi_ngay) * buoc
    ts = (ngay.values[:, None] + (gio * 3600 * 10**9).astype("timedelta64[ns]")[None, :])
    return pd.DatetimeIndex(ts.reshape(-1)[:so_bar])


def tong_hop(kich_ban: str = "NHIEU", hat: int = 1, so_bar: int = 9000,
             khung: str = "H4", do_manh: float = 1.0) -> pd.DataFrame:
    """Sinh chuoi OHLC + tick_volume + spread co edge DA BIET (xem docstring dau file).

    Mo hinh: log gia di ngau nhien, do bien dong GARCH(1,1) (cum bien dong that
    - khong co no thi 'phan vi ATR' la nhieu trang, va moi bo loc theo bien dong
    deu vo nghia). Moi bar chia 8 buoc con de high/low la cuc tri cua MOT duong
    di that, khong phai nhieu dan len close. Troi `mu` cua bar t CHI phu thuoc
    thong tin DA BIET tai close bar t-1 - chinh edge cai vao cung khong nhin truoc.
    """
    kich_ban = str(kich_ban).upper()
    khung = str(khung).upper()
    if kich_ban not in KICH_BAN:
        raise KeyError("kich ban '%s' khong co (co: %s)" % (kich_ban, ", ".join(KICH_BAN)))
    if khung not in BAR_MOI_NGAY:
        raise KeyError("khung tong hop chi co %s" % ", ".join(BAR_MOI_NGAY))
    rng = np.random.default_rng(_hat_kich_ban(kich_ban, hat))
    s_bar = 0.09 / np.sqrt(BAR_MOI_NAM[khung])
    a_g, b_g = 0.06, 0.92
    w_g = s_bar ** 2 * (1.0 - a_g - b_g)
    m = 8

    o = np.empty(so_bar)
    h = np.empty(so_bar)
    lo = np.empty(so_bar)
    c = np.empty(so_bar)
    kl = np.empty(so_bar)
    sp = np.empty(so_bar)

    p = 0.0                      # log gia mo cua bar hien tai
    var = s_bar ** 2
    r_truoc = 0.0
    atr = s_bar
    atr_cua_so: deque = deque(maxlen=250)
    ibs_truoc, pv_truoc = 0.5, 0.5
    r_gan: deque = deque(maxlen=3)
    troi_cho = np.zeros(so_bar + 8)  # troi da hen cho cac bar sau (kich ban LOC)
    c_truoc = 0.0

    for t in range(so_bar):
        var = w_g + a_g * r_truoc ** 2 + b_g * var
        s = float(np.sqrt(var))
        mu = troi_cho[t]
        if kich_ban in ("HOI_QUY", "HOI_QUY_YEU") and t > 260:
            k = 0.50 if kich_ban == "HOI_QUY" else 0.30
            if ibs_truoc < 0.15 and pv_truoc > 0.65:
                mu += k * s * do_manh
            elif ibs_truoc > 0.85 and pv_truoc > 0.65:
                mu -= k * s * do_manh
        elif kich_ban == "XU_HUONG":
            mu += 0.07 * do_manh * r_truoc
        buoc = rng.standard_normal(m) * (s / np.sqrt(m)) + mu / m
        duong = p + np.cumsum(buoc)
        o[t] = p
        h[t] = max(p, float(duong.max()))
        lo[t] = min(p, float(duong.min()))
        c[t] = float(duong[-1])
        r = c[t] - p
        # --- thong tin BIET tai close bar t, dung cho troi cua bar t+1 ---
        tr = max(h[t] - lo[t], abs(h[t] - c_truoc), abs(lo[t] - c_truoc)) if t else h[t] - lo[t]
        atr = atr + (tr - atr) / 14.0
        atr_cua_so.append(atr)
        if len(atr_cua_so) >= 50:
            pv_truoc = float(np.mean(np.asarray(atr_cua_so) <= atr))
        rong = h[t] - lo[t]
        ibs_truoc = (c[t] - lo[t]) / rong if rong > 0 else 0.5
        r_gan.append(r)
        if kich_ban == "LOC" and t > 260 and len(r_gan) == 3:
            # DOI XUNG: cu giam VA cu tang 3 bar. Chi cai nhanh giam thi nhanh
            # "bien dong cao -> di tiep" tich thanh mot xu huong giam cua ca
            # chuoi (do 25/09: mua-giu -26%/nam, moc ban-giu o DD20 = +98%/nam)
            # va moi he mua deu thua moc vi mot ly do khong lien quan toi edge.
            tong3 = sum(r_gan)
            nguong3 = 1.0 * s * np.sqrt(3.0)
            if abs(tong3) > nguong3:
                hoi = 1.0 if pv_truoc < 0.5 else -1.0   # +1 = nguoc cu vua xay ra
                troi_cho[t + 1:t + 6] += -np.sign(tong3) * hoi * 0.12 * s * do_manh
        kl[t] = 800.0 * (1.0 + 2.5 * abs(r) / max(s, 1e-12)) * float(rng.lognormal(0.0, 0.3))
        sp[t] = float(np.clip(15.0 + rng.normal(0.0, 2.0), 8.0, 30.0))
        r_truoc = r
        c_truoc = c[t]
        p = c[t]                 # khong co khe gia giua hai bar

    goc = 1.0
    df = pd.DataFrame({
        "open": goc * np.exp(o), "high": goc * np.exp(h), "low": goc * np.exp(lo),
        "close": goc * np.exp(c), "tick_volume": np.round(kl),
        "spread": np.round(sp)}, index=_chi_muc(so_bar, khung))
    df.index.name = "time"
    df.attrs["tong_hop"] = {"kich_ban": kich_ban, "hat": hat, "do_manh": do_manh,
                            "dap_an": KICH_BAN[kich_ban]}
    return df


if __name__ == "__main__":
    import json
    for kb in KICH_BAN:
        d = tong_hop(kb, 1)
        r = np.log(d["open"]).diff().dropna()
        print(kb, len(d), str(d.index[0])[:16], str(d.index[-1])[:16],
              "sd bar %.5f" % r.std(), "ac1 %+.3f" % r.autocorr(1))
    print(json.dumps(danh_sach(), ensure_ascii=False, default=str)[:600])
