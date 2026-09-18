# -*- coding: utf-8 -*-
"""
brain_strategies.py - SO DANG KY CHIEN LUOC cho The Brain
=====================================================================================
Moi chien luoc = 1 ham nhan DataFrame OHLC -> tra ve chuoi VI THE (-1/0/+1), chot o close(t).
The Brain se lo phan vao lenh OPEN[i+1], cost, placebo, walk-forward, FDR toan cuc.

BAT BUOC khi nap chien luoc moi (khong co ngoai le):
  - `nguon` + `tac_gia` + `giay_phep`: de biet minh dang dung cua ai, va co duoc dung khong.
  - `ly_do_kinh_te`: TAI SAO no phai co lai? Neu khong tra loi duoc -> KHONG NAP.
    Day la bo loc quan trong nhat. Ca du an da chay vai trieu to hop; khong the sua FDR o quy mo
    do. Thu duy nhat bao ve khoi dương tinh gia la co che kinh te that dang sau.
  - Tham so PHAI la so cua tac giaphoac so kinh dien. KHONG do tren du lieu. Muon thu bo tham so
    khac = dang ky mot chien luoc MOI (lam tang tong so phep thu -> siet FDR cho tat ca).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import sonic_r as sr           # tai dung chi bao + 5 tang tin hieu da hien thuc

CHIEN_LUOC = {}


def dang_ky(ten, nguon, tac_gia, giay_phep, ly_do_kinh_te, lop_tai_san=None):
    def deco(fn):
        CHIEN_LUOC[ten] = dict(fn=fn, nguon=nguon, tac_gia=tac_gia, giay_phep=giay_phep,
                               ly_do_kinh_te=ly_do_kinh_te, lop_tai_san=lop_tai_san)
        return fn
    return deco


# ============================================================ nhom KINH DIEN / HOC THUAT
@dang_ky("sma200_long", "kinh dien", "khong ro (co tu thap ky 1980)", "public domain",
         "Xu huong dai han phan anh dong von cham chay vao/ra tai san; dung ngoai thi truong gau "
         "tranh duoc phan lon sut giam. Da duoc kiem chung rong tren nhieu lop tai san.")
def sma200_long(d):
    return (d["close"] > d["close"].rolling(200).mean()).astype(float)


@dang_ky("tsmom_12thang", "hoc thuat", "Moskowitz, Ooi & Pedersen (2012)", "public domain",
         "Time-series momentum: nguoi tham gia phan ung CHAM voi thong tin moi (under-reaction), "
         "cong voi dong von duoi theo hieu suat. Da kiem chung tren 58 tai san, 25 nam, tap chi "
         "Journal of Financial Economics.")
def tsmom_12thang(d):
    return pd.Series(np.sign(d["close"] / d["close"].shift(252) - 1), index=d.index).fillna(0.0)


@dang_ky("donchian20", "kinh dien", "Richard Donchian / Turtle Traders", "public domain",
         "Pha khoi bien do N ngay = co thong tin moi du manh de vuot thanh khoan hai chieu. "
         "Tham so 20/55 la so GOC cua nhom Turtle, khong phai do tren du lieu.")
def donchian20(d):
    hi, lo = d["high"].rolling(20).max(), d["low"].rolling(20).min()
    st = pd.Series(np.where(d["close"] >= hi, 1.0, np.where(d["close"] <= lo, -1.0, np.nan)),
                   index=d.index)
    return st.ffill().fillna(0.0)


@dang_ky("donchian55", "kinh dien", "Richard Donchian / Turtle Traders", "public domain",
         "Nhu donchian20 nhung cua so dai hon - it tin hieu gia hon, doi lai vao cham hon.")
def donchian55(d):
    hi, lo = d["high"].rolling(55).max(), d["low"].rolling(55).min()
    st = pd.Series(np.where(d["close"] >= hi, 1.0, np.where(d["close"] <= lo, -1.0, np.nan)),
                   index=d.index)
    return st.ffill().fillna(0.0)


@dang_ky("ibs_bat_day", "tu nghien cuu (Phase 2, 27/07/2026)", "du an nay", "noi bo",
         "Dong cua o 20% duoi bien do ngay = ben ban da can kiet thanh khoan trong phien; nha tao "
         "lap thi truong doi phi de om ton kho, hoan lai vao phien sau. Chi song o chi so co phieu "
         "chau My (sp500/dow/nasdaq/russell/bovespa); chau Au bang 0 hoac AM -> co gioi han dia ly ro.",
         lop_tai_san="chi_so_cp")
def ibs_bat_day(d):
    rng = (d["high"] - d["low"]).replace(0, np.nan)
    ibs = (d["close"] - d["low"]) / rng
    return (ibs < 0.2).astype(float)


# ============================================================ MOC SO SANH (bat buoc phai co)
@dang_ky("mua_va_giu", "moc so sanh", "(khong ai ca)", "n/a",
         "KHONG phai chien luoc - la MOC SO SANH. Moi chien luoc long-biased phai vuot duoc cai nay "
         "moi duoc goi la co edge. Thieu no thi mot luat 'long khi X' bat ky tren tai san tang gia "
         "20 nam deu trong nhu co edge - do dung la bay da sap voi usdars (Sharpe 1,75/placebo 0%) "
         "va SMA200 tren vang.")
def mua_va_giu(d):
    return pd.Series(1.0, index=d.index)


# ============================================================ nhom DI THUONG KINH DIEN
# Nap 27/07/2026. Tieu chi chon: (a) da qua phan bien o tap chi dau nganh, (b) tham so la so GOC
# cua tac gia - khong do lai tren du lieu, (c) co co che kinh te ro rang.
@dang_ky("turn_of_month", "hoc thuat", "Ariel (1987); Lakonishok & Smidt (1988)", "public domain",
         "Dong tien luong huu/luong thang do vao quy chi so vao cuoi thang va dau thang moi; cong "
         "them tai can bang cua quy. Day la dong tien CO LICH, khong phu thuoc du bao - nen ton tai "
         "ben bi qua nhieu thap ky va nhieu thi truong.")
def turn_of_month(d):
    ngay = d.index.day
    cuoi_thang = d.index.to_series().groupby([d.index.year, d.index.month]).transform("max").dt.day
    return pd.Series(np.where((ngay <= 3) | (ngay >= cuoi_thang.values), 1.0, 0.0),
                     index=d.index)


@dang_ky("halloween_nov_apr", "hoc thuat", "Bouman & Jacobsen (2002), American Economic Review",
         "public domain",
         "Loi suat thang 11-4 cao hon han thang 5-10 tren 36/37 thi truong khao sat. Gia thuyet: "
         "chu ky nghi he lam giam khau vi rui ro va thanh khoan mua he; cong voi dong tien thuong "
         "cuoi nam. La mua vu THUAN LICH nen khong bi 'giao dich het' de dang.")
def halloween_nov_apr(d):
    return pd.Series(np.where(d.index.month.isin([11, 12, 1, 2, 3, 4]), 1.0, 0.0), index=d.index)


@dang_ky("momentum_12_1", "hoc thuat", "Jegadeesh & Titman (1993), Journal of Finance",
         "public domain",
         "Momentum 12 thang BO QUA thang gan nhat - bo qua de tranh dao chieu ngan han (thang cuoi "
         "thuong nguoc chieu). Day la quy uoc GOC cua bai bao, khong phai tham so do lai.")
def momentum_12_1(d):
    return pd.Series(np.sign(d["close"].shift(21) / d["close"].shift(252) - 1),
                     index=d.index).fillna(0.0)


@dang_ky("high_52_tuan", "hoc thuat", "George & Hwang (2004), Journal of Finance", "public domain",
         "Gia gan dinh 52 tuan du bao loi suat tuong lai TOT HON momentum thuan: nha dau tu neo "
         "vao dinh cu va phan ung cham khi gia vuot dinh -> thong tin tot bi tham thau dan.")
def high_52_tuan(d):
    dinh = d["close"].rolling(252).max()
    return (d["close"] >= 0.95 * dinh).astype(float)


@dang_ky("dao_chieu_1_tuan", "hoc thuat", "Lehmann (1990); Jegadeesh (1990)", "public domain",
         "Dao chieu ngan han: nguoi ban bi ep thanh khoan (margin call, quy rut von) day gia xuong "
         "duoi gia tri, nguoi cung cap thanh khoan doi phi va nhan lai trong vai ngay. Day la phi "
         "THANH KHOAN, khong phai du bao.")
def dao_chieu_1_tuan(d):
    return (d["close"] < d["close"].shift(5)).astype(float)


@dang_ky("vol_thap", "hoc thuat", "Blitz & van Vliet (2007); Baker, Bradley & Wurgler (2011)",
         "public domain",
         "Di thuong bien dong thap: nha dau tu bi han che don bay phai mua tai san bien dong cao de "
         "tim loi suat -> tai san bien dong cao bi dinh gia qua cao. Nghich ly voi CAPM nhung ton "
         "tai ben bi tren co phieu, trai phieu, hang hoa.")
def vol_thap(d):
    bd = d["close"].pct_change().rolling(20).std()
    return (bd < bd.rolling(252).median()).astype(float)


@dang_ky("vol_dieu_tiet", "hoc thuat", "Moreira & Muir (2017), Journal of Finance", "public domain",
         "Danh NHO khi bien do lon va nguoc lai: bien dong co the du bao (cum lai) trong khi loi "
         "suat ky vong thi khong tang tuong ung -> ty le loi/rui ro TOT HON o pha bien dong thap. "
         "Da test rieng tren SP500 hom 27/07 (that bai o do), nap day de kiem tren TAI SAN KHAC.")
def vol_dieu_tiet(d):
    bd = d["close"].pct_change().rolling(20).std() * np.sqrt(252)
    he_so = (0.12 / bd.replace(0, np.nan)).clip(0, 1.0)
    return ((he_so * 4).round() / 4).fillna(0.0)


# ============================================================ nhom SONIC R (VuTienTurtleTrader)
# Nguon: pineturtle.txt (chu du an tu suu tam tu TradingView, script open-source dang 25/06/2018).
# Phan tich day du: SONIC_R_PHAN_TICH.md. Chi TRICH QUY TAC, khong chep code.
def _sonic(d, tang):
    sig, _atr = sr.build_signals(d)
    return sig[tang]


@dang_ky("sonic_r_s1_loi", "TradingView", "VuTienTurtleTrader", "open-source (MPL 2.0)",
         "Gia hoi ve dai EMA34(high/low) trong xu huong EMA89: vung nay la noi lenh cho mua/ban "
         "cua nguoi lo nhip tap trung -> thanh khoan day. Co ly do vi cau truc lenh, khong phai "
         "chi vi 'duong dep'.")
def sonic_r_s1_loi(d):
    return _sonic(d, "S1_loi")


@dang_ky("sonic_r_s2_linreg", "TradingView", "VuTienTurtleTrader", "open-source (MPL 2.0)",
         "Nhu S1 nhung dung Linear Regression 89 thay gia tho de loc nhieu - giam tin hieu gia do "
         "nen rau dai. Ly do ky thuat (loc nhieu), khong phai ly do kinh te moi.")
def sonic_r_s2_linreg(d):
    return _sonic(d, "S2_linreg")


@dang_ky("sonic_r_s3_macd", "TradingView", "VuTienTurtleTrader", "open-source (MPL 2.0)",
         "Them dieu kien HUONG THAY DOI cua MACD histogram - tranh vao khi da tan luc. Day la bo "
         "loc dong luong ngan han chong lai viec bat dao chieu qua som.")
def sonic_r_s3_macd(d):
    return _sonic(d, "S3_macd")


@dang_ky("sonic_r_s4_loc_nen", "TradingView", "VuTienTurtleTrader", "open-source (MPL 2.0)",
         "Loc hinh nen theo BOI SO BE RONG DAI (than nen < 2x, bong tren < 0.5x, cach dai < 1.5x). "
         "Day la phan tinh nhat cua ca bo: chuan hoa theo BIEN DONG thay vi so diem co dinh, nen "
         "tu thich nghi khi thi truong doi bien do.")
def sonic_r_s4_loc_nen(d):
    return _sonic(d, "S4_loc_nen")


@dang_ky("sonic_r_s5_hull", "TradingView", "VuTienTurtleTrader", "open-source (MPL 2.0)",
         "Them Hull MA 377 lam bo loc CHE DO thi truong - chi danh thuan chieu xu hurong rat dai. "
         "Cung tinh than voi SMA200 nhung muot hon, do tre thap hon.")
def sonic_r_s5_hull(d):
    return _sonic(d, "S5_hull")
