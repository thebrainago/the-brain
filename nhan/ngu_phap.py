# -*- coding: utf-8 -*-
"""ngu_phap.py - NGU PHAP CO CHE. Cach duy nhat kien thuc moi di vao day chuyen.

VAN DE NO GIAI (do tren so cai 16/08):
  SEEKER da thu 303 tai lieu, trong do 17 tai lieu HANG A mo ta co che CHUA CO
  trong `nhan/mau.py`. Van de `can_mau_moi` mo tu 15/08 va khong bao gio dong
  duoc, vi buoc "doc duoc co che -> co template kiem dinh duoc" la buoc DUY NHAT
  con phai lam bang tay. Ket qua: mot phong lab doc rat nhieu ma hoc duoc rat it.

CACH GIAI - va vi sao khong sinh MA:
  Cho LLM viet ham Python roi `exec` la mo hai cua cung luc: cua bao mat, va
  cua nhin truoc (mot dong `.shift(-1)` hay `transform("last")` la du - bay do
  da sap that ngay 15/08 trong `m_lap_gap`, cho EURCAD H1 ra CAGR 115%).
  O day co che duoc khai bao bang DU LIEU: mot cay JSON gom toan hang va phep
  so sanh. Trinh thong dich nay la thu duy nhat cham vao chuoi gia, va no
  KHONG CO toan tu nao nhin ve tuong lai. Nhin truoc tro thanh dieu KHONG PHAT
  BIEU DUOC, khong phai dieu bi cam.

HINH DANG MOT CO CHE:
    {
      "ten": "ibs_day_khi_bien_dong_cao",
      "co_che": "Mot cau ve vi sao co nguoi tra tien cho phoi nhiem nay.",
      "ho": "quay_ve_trung_binh",
      "chieu": 1,                       # 1 = mua, -1 = ban
      "giu": 1,                         # so bar giu sau khi dieu kien dung
      "vao": [                          # VA voi nhau
        {"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.2}},
        {"trai": {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
         "phep": ">", "phai": {"hang": 0.7}}
      ],
      "ra": []                          # HOAC voi nhau; rong = het `giu` thi ra
    }

QUY UOC THOI GIAN (khong the vi pham):
  Moi toan hang chi duoc tinh tu thong tin BIET TAI CLOSE cua bar i. Trinh
  thong dich tra ve `tin_hieu[i]`; `nhan/mo_phong.py` tu dich mot bar. Khong co
  toan hang nao nhan `shift` am, va `_kiem_khong_nhin_truoc` con kiem lai bang
  thuc nghiem: doi mot gia tri o bar cuoi KHONG duoc lam doi tin hieu bar truoc.
"""
from __future__ import annotations

import copy
import json
import os
import time
import weakref
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import mau as MAU_MOD
else:
    from . import mau as MAU_MOD

LAB = Path(__file__).resolve().parent.parent
KHO_CO_CHE = LAB / "config" / "co_che_dsl.json"

PHEP = {"<", "<=", ">", ">=", "==", "!=", "cheo_len", "cheo_xuong"}
#: `khac` KHONG co trong danh sach nay, du `doc_ma`/`doc_hieu` van tra ve no.
#:
#: `khac` la sentinel DUNG cua bo doc: "khong doc duoc ho, khong xep bua". Nhung
#: no khong duoc phep vao KHO. Ly do (tim ra 06/09/2026 khi `test_pham_vi` do):
#: `boc_ma_llm` va `loc_co_che` deu loai moi co che co `ho` khong nam trong
#: `pham_vi.PHAM_VI`, va `khac` khong nam trong do - nen mot co che ho `khac`
#: vao duoc kho roi **nam im vinh vien, khong bao gio duoc thu mot lan nao**.
#: Do la dung hinh dang loi [[ket-luan-am-phai-phan-biet-chua-do]]: no duoc dem
#: nhu mot co che da co, trong khi thuc te no chua bao gio duoc do.
#:
#: Chan o day thi bo doc nhan ly do NGAY ("ho 'khac' khong thuoc ..."), va
#: nguoi sua biet phai xep lai ho - thay vi mot muc rac nam yen trong kho.
HO_HOP_LE = {"quay_ve_trung_binh", "xu_huong", "pha_vo", "lich", "phien",
             "bien_dong", "dong_tien", "vi_mo"}


# --------------------------------------------------------------- TOAN HANG
#: Nguon gia TONG HOP. Pine goi la `hl2`/`hlc3`/`ohlc4` va chung xuat hien
#: nhu mot cot binh thuong trong ma that (`ta.sma(hl2, 20)`). Truoc 01/09 ngu
#: phap chi biet 4 cot goc nen moi thanh phan dung chung bi cham la "khong dien
#: dat duoc" va bi vut - 9 lan trong kho ban doc hien tai.
COT_TONG_HOP = {
    "hl2": ("high", "low"),
    "hlc3": ("high", "low", "close"),
    "ohlc4": ("open", "high", "low", "close"),
}


def _cot(df: pd.DataFrame, ten: str) -> pd.Series:
    if ten in COT_TONG_HOP:
        phan = [_cot(df, c) for c in COT_TONG_HOP[ten]]
        return sum(phan) / float(len(phan))
    if ten not in df.columns:
        raise KeyError(f"du lieu khong co cot '{ten}'")
    return df[ten].astype(float)


def toan_hang(df: pd.DataFrame, t: dict) -> pd.Series:
    """Dich mot toan hang thanh chuoi gia tri tai tung bar. CO NHO KET QUA.

    MOI nhanh o day chi doc qua khu va hien tai. Khong co nhanh nao dich am.

    VI SAO CO NHO (do that tren mot luot QUANTLAB 01/09/2026): mot luot quet
    8.400 to hop tham so tren CUNG mot tai san, va ham nay duoc goi 34.803 lan
    ngon 55,4 giay = 30% ca luot. Rat nhieu lan trong so do tinh lai DUNG MOT
    thu: `rsi(close,14)`, `ema(close,20)`, `atr(14)` xuat hien trong hang tram
    mau khac nhau. Rolling window tren 20.000 bar khong re, va tinh no lai hang
    tram lan la lang phi thuan tuy.

    Nho khoa theo `id(df)` NHUNG co `weakref.finalize` xoa muc khi khung bi thu
    gom. Khong co no thi id cua mot khung da chet co the duoc cap lai cho khung
    khac va bo nho tra ve chuoi cua MOT KHUNG KHAC - dung hinh dang loi "so lieu
    doc duoc nhung sai" ma du an nay da mat ca ngay 01/09 de truy.

    Ban dau thu cat nho vao `df.attrs`: SAI, va test bat duoc ngay. pandas so
    sanh `obj.attrs == attrs` trong `__finalize__` khi concat; attrs chua Series
    thi phep so tro thanh so sanh theo phan tu va nem "truth value of a Series
    is ambiguous". `attrs` chi duoc chua thu so sanh duoc bang `==`.

    Tra ve BAN SAO: neu nguoi goi sua tai cho chuoi nhan duoc thi ban trong nho
    se hong va moi phep tinh sau do deu sai. Sao mot chuoi 20.000 so la vai chuc
    micro giay, re hon nhieu lan so voi tinh lai.
    """
    if not isinstance(t, dict):
        raise TypeError(f"toan hang phai la dict, nhan duoc {type(t).__name__}")
    if "hang" in t:
        return pd.Series(float(t["hang"]), index=df.index)

    try:
        khoa = json.dumps(t, sort_keys=True, default=str)
        nho = _nho_cua(df)
    except Exception:
        return _toan_hang_tinh(df, t)
    cu = nho.get(khoa)
    if cu is not None:
        return cu.copy()
    ra = _toan_hang_tinh(df, t)
    if len(nho) < 4096:
        nho[khoa] = ra
    return ra.copy()


#: id(df) -> {khoa toan hang: chuoi}. Muc bi xoa khi khung bi thu gom.
_NHO_TOAN_HANG: dict[int, dict] = {}


#: Cac mau nen `mau_nen` noi duoc. Gia tri tra ve CO DAU theo chieu:
#: duong = mau TANG, am = mau GIAM, 0 = khong co mau. Nho vay mot dieu kien
#: `mau_nen(nhan_chim) > 0` la "nhan chim TANG" ma khong can them toan hang.
MAU_NEN = ("nhan_chim", "doji", "bua", "sao_bang", "trong", "ngoai",
           "ba_nen", "rau_duoi", "rau_tren", "nen_dac")


def _atr_series(df: pd.DataFrame, n: int) -> pd.Series:
    """ATR kieu Wilder, tra ve Series cung chi muc voi df."""
    h, l, c = (_cot(df, "high"), _cot(df, "low"), _cot(df, "close"))
    tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()],
                   axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / max(n, 1), adjust=False).mean()


def _heiken(df: pd.DataFrame, lay: str) -> pd.Series:
    """Heikin-Ashi - toan hang CO TRANG THAI thu hai cua ngu phap.

    `ha_open[i] = (ha_open[i-1] + ha_close[i-1]) / 2` - phu thuoc chinh no o bar
    truoc, nen khong ghep tu cac toan hang cua so duoc. 5 co che trong kho nhac
    toi no.

    `lay`: "chieu" (+1/-1 theo than nen HA) | "than" (than HA chia bien do that)
           | "khong_rau_duoi" / "khong_rau_tren" (nen HA khong co rau phia do -
           dau hieu xu huong manh theo cach doc co dien)
    """
    o = _cot(df, "open").to_numpy(float)
    h = _cot(df, "high").to_numpy(float)
    l = _cot(df, "low").to_numpy(float)
    c = _cot(df, "close").to_numpy(float)
    n = len(df)
    ha_c = (o + h + l + c) / 4.0
    ha_o = np.empty(n)
    ha_o[0] = (o[0] + c[0]) / 2.0
    for i in range(1, n):
        ha_o[i] = (ha_o[i - 1] + ha_c[i - 1]) / 2.0
    ha_h = np.maximum.reduce([h, ha_o, ha_c])
    ha_l = np.minimum.reduce([l, ha_o, ha_c])
    if lay == "chieu":
        return pd.Series(np.sign(ha_c - ha_o), index=df.index)
    if lay == "than":
        bien = np.where(ha_h - ha_l > 0, ha_h - ha_l, np.nan)
        return pd.Series((ha_c - ha_o) / bien, index=df.index)
    if lay == "khong_rau_duoi":
        return pd.Series(
            (np.abs(np.minimum(ha_o, ha_c) - ha_l) < 1e-12).astype(float),
            index=df.index)
    if lay == "khong_rau_tren":
        return pd.Series(
            (np.abs(ha_h - np.maximum(ha_o, ha_c)) < 1e-12).astype(float),
            index=df.index)
    raise KeyError("'heiken': khong biet lay='%s' (co: chieu, than, "
                   "khong_rau_duoi, khong_rau_tren)" % lay)


def _supertrend(df: pd.DataFrame, n: int, k: float, lay: str) -> pd.Series:
    """Supertrend - toan hang CO TRANG THAI dau tien cua ngu phap.

    ## Vi sao no khong viet duoc bang cac toan hang co san

    Moi toan hang khac deu la mot ham cua MOT CUA SO du lieu: doc n bar gan
    nhat, ra mot so. Supertrend thi khong - duong bien cua no **chot lai** va
    chi noi long khi xu huong lat:

        bien tren[i] = min(bien tren tho[i], bien tren[i-1])   khi con xu huong giam
        chieu[i]     = lat khi gia dong cua xuyen qua bien dang giu

    Tuc gia tri tai bar i phu thuoc vao gia tri tai bar i-1, khong phai vao mot
    cua so co dinh. Do dung la "toan tu co nho" - va do la ly do khong cach nao
    ghep no tu `tb`/`atr`/`cao_nhat` duoc.

    Do 12/09/2026: **16 co che trong kho nhac toi supertrend** ma ngu phap
    khong noi duoc.

    `lay`: "chieu" (+1 tang / -1 giam) | "duong" (gia tri duong bien) |
           "khoang_cach" (gia cach duong bien, chia ATR - khong phu thuoc thang do)

    KHONG NHIN TRUOC: moi buoc chi doc bar i va trang thai tai i-1.
    """
    c = _cot(df, "close").to_numpy(float)
    hl2 = ((_cot(df, "high") + _cot(df, "low")) / 2.0).to_numpy(float)
    a = _atr_series(df, n).to_numpy(float)
    m = len(df)
    tren = np.full(m, np.nan)
    duoi = np.full(m, np.nan)
    chieu = np.zeros(m)
    duong = np.full(m, np.nan)
    ch = 1.0
    for i in range(m):
        if not np.isfinite(a[i]):
            continue
        tt, td = hl2[i] + k * a[i], hl2[i] - k * a[i]
        if i > 0 and np.isfinite(tren[i - 1]):
            # Bien SIET LAI, chi noi long khi gia pha qua -> day la cho "co nho"
            tt = min(tt, tren[i - 1]) if c[i - 1] <= tren[i - 1] else tt
            td = max(td, duoi[i - 1]) if c[i - 1] >= duoi[i - 1] else td
            ch = chieu[i - 1] or 1.0
            if c[i] > tren[i - 1]:
                ch = 1.0
            elif c[i] < duoi[i - 1]:
                ch = -1.0
        tren[i], duoi[i], chieu[i] = tt, td, ch
        duong[i] = td if ch > 0 else tt
    if lay == "chieu":
        return pd.Series(chieu, index=df.index)
    if lay == "duong":
        return pd.Series(duong, index=df.index)
    if lay == "khoang_cach":
        with np.errstate(divide="ignore", invalid="ignore"):
            return pd.Series((c - duong) / np.where(a > 0, a, np.nan),
                             index=df.index)
    raise KeyError("'supertrend': khong biet lay='%s' (co: chieu, duong, "
                   "khoang_cach)" % lay)


# ------------------------------------------------------------- HINH HOC
#: Nam muc thoai lui Fibonacci chuan. `lay` nhan ca ba cach viet cua cung mot
#: ti le: so (0.618), chuoi ("0.618"), va dang phan tram ("61.8").
MUC_FIBO = (0.236, 0.382, 0.5, 0.618, 0.786)


def _hoi_quy_truot(y: pd.Series, n: int) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Hoi quy tuyen tinh tren cua so n bar KET THUC TAI BAR i.

    Tra ve `(doc, r2, gia_tri)`:
      doc      he so goc theo DON VI CUA `y` TREN MOI BAR (chua chuan hoa)
      r2       do khop cua duong, 0..1 - "duong nay co that su la mot duong khong"
      gia_tri  gia tri cua duong tai chinh bar i (dung de so voi gia)

    VI SAO TINH BANG TICH CHAP chu khong `rolling().apply(np.polyfit)`: trong so
    `k - trung binh k` la CO DINH nen tu so cua he so goc chi la mot phep tich
    chap voi nhan co dinh - chay trong C, khong mot lan goi Python nao cho moi
    bar. `polyfit` tren 20.000 bar ton hang giay; `toan_hang` da tung ngon 30%
    mot luot quet (do 01/09) nen mot toan hang moi khong duoc phep dat hon cai
    da co.

    R^2 tinh bang `b^2 * Sxx / Syy` - dung dai luong da co san, khong can chay
    lai phep khop lan hai.

    KHONG NHIN TRUOC: cua so cua bar i la [i-n+1 .. i]. Bar i da dong khi ta
    doc no, nen lay ca bar i la hop le (khac `fibo` va `donchian` - xem duoi).
    """
    n = max(int(n), 2)
    v = np.asarray(y, dtype=float)
    m = len(v)
    k = np.arange(n, dtype=float)
    w = k - k.mean()
    sxx = float(np.dot(w, w))

    tu = np.full(m, np.nan)
    if m >= n:
        # np.convolve(v, w[::-1])[i] = tong_j v[j]*w[j-(i-n+1)] tren dung cua so
        # [i-n+1 .. i]. Chi doc qua khu vi nhan chay LUI.
        tu[:] = np.convolve(v, w[::-1])[:m]
        tu[: n - 1] = np.nan

    doc = pd.Series(tu / sxx, index=y.index)
    tb = y.rolling(n).mean()
    # Tong binh phuong lech quanh trung binh. Dung `var(ddof=0)*n` chu khong
    # `sum(y^2) - n*tb^2`: cach sau tru hai so gan bang nhau va mat chu so co
    # nghia khi gia lon (BTC ~ 1e5), cach nay pandas tinh bang thuat toan on dinh.
    ss = y.rolling(n).var(ddof=0) * n
    r2 = (doc * doc * sxx) / ss.where(ss > 0)
    gia_tri = tb + doc * ((n - 1) / 2.0)
    return doc, r2.clip(0.0, 1.0), gia_tri


def _song_fibo(df: pd.DataFrame, n: int, huong) -> tuple:
    """Doan song n bar KET THUC TAI BAR i-1 -> (dinh, day, la_song_tang).

    ## DICH MOT BAR - cung ly do voi `donchian`

    Neo Fibonacci phai la mot doan song DA XONG. Neu cua so om ca bar i thi
    `dinh` chay theo chinh bar dang xet: gia khong bao gio vuot duoc muc 0,0 va
    `vi_tri` bi ep cung trong [0; 1] - moi dieu kien dang "gia cham muc 0,618"
    tro thanh mot dieu kien KHAC han cai nguoi viet dinh noi. Do la kieu nhin
    truoc kin nhat: no khong lam ket qua dep len, no lam co che im lang.

    ## CHIEU CUA SONG quyet dinh muc thoai lui nam o dau

    Trong mot song TANG (day den TRUOC, dinh den SAU), thoai lui do NGUOC XUONG
    tu dinh: muc f nam o `dinh - f*(dinh-day)`. Trong song GIAM thi nguoc lai.
    Lay nham chieu la lay guong cua muc dung (0,382 thanh 0,618), nen chieu duoc
    suy tu VI TRI cua dinh/day trong cua so, khong doan.

    `huong`: "tu_dong" (mac dinh) | 1 / "tang" | -1 / "giam" - ep chieu khi co
    che noi ro no chi mua thoai lui trong xu huong tang.
    """
    n = max(int(n), 2)
    h = _cot(df, "high").to_numpy(float)
    l = _cot(df, "low").to_numpy(float)
    m = len(h)
    dinh = np.full(m, np.nan)
    day = np.full(m, np.nan)
    tang = np.full(m, np.nan)
    if m > n:
        ch = sliding_window_view(h, n)
        cl = sliding_window_view(l, n)
        so = m - n                      # hang r om bar [r .. r+n-1] -> gan cho bar r+n
        dinh[n:] = ch.max(axis=1)[:so]
        day[n:] = cl.min(axis=1)[:so]
        tang[n:] = (ch.argmax(axis=1)[:so] >= cl.argmin(axis=1)[:so]).astype(float)

    if isinstance(huong, str):
        huong = huong.lower()
    if huong in ("tu_dong", "auto", None, ""):
        pass
    elif huong in (1, 1.0, "1", "tang", "len"):
        tang = np.where(np.isfinite(dinh), 1.0, np.nan)
    elif huong in (-1, -1.0, "-1", "giam", "xuong"):
        tang = np.where(np.isfinite(dinh), 0.0, np.nan)
    else:
        raise KeyError("'fibo': khong biet huong='%s' (co: tu_dong, 1/tang, "
                       "-1/giam)" % huong)
    return dinh, day, tang


def _ti_le_fibo(lay) -> float | None:
    """"0.618" -> 0,618 · "61.8" -> 0,618 · 1.618 -> 1,618. None neu khong phai so.

    CHI coi la viet theo phan tram khi >= 10. Nguong "> 1" de hong mot dang khai
    bao dung: `1.618` la muc MO RONG that su ton tai (161,8%), doi no thanh
    1,6% la doc sai mot khai bao dung ma khong mot loi bao nao.
    """
    try:
        f = float(lay)
    except (TypeError, ValueError):
        return None
    return f / 100.0 if f >= 10.0 else f


def _mau_nen(df: pd.DataFrame, mau: str) -> pd.Series:
    """Mau nen hop thanh, CO DAU theo chieu.

    ## Vi sao can toan hang nay

    Do 12/09/2026: ngu phap co `than_nen`, `bien_do`, `ibs`, `dem_lien_tiep` -
    du de noi tung manh cua mot mau nen, nhung KHONG noi duoc mau nen. Ket qua
    la 41 co che ten "nen" + 20 "candle" + 10 "engulf" trong kho deu la ban NHAP
    TU NGOAI, va bo sinh noi sinh khong tu dat ra duoc mot mau nen nao. Tuc mot
    dong nguyen trong so do (*"Cac dang nen khac nhau"*) chua bao gio duoc quet
    mot cach he thong.

    ## Moi mau deu CHUAN HOA, khong dung nguong tuyet doi

    "Than nen dai" la dai so voi cai gi? O day moi nguong deu tinh theo BIEN DO
    CUA CHINH BAR (hoac bar truoc), nen mot mau nen dinh nghia tren EURUSD dung
    y nguyen tren XAUUSD. Mot mau nen khai bang so pip la mau nen cua mot tai
    san, khong phai mot mau nen.
    """
    if mau not in MAU_NEN:
        raise KeyError("'mau_nen': khong biet mau='%s' (co: %s)"
                       % (mau, ", ".join(MAU_NEN)))
    o = _cot(df, "open").astype(float)
    h = _cot(df, "high").astype(float)
    l = _cot(df, "low").astype(float)
    c = _cot(df, "close").astype(float)
    bien = (h - l).replace(0.0, np.nan)
    than = c - o
    than_abs = than.abs()
    chieu = np.sign(than)
    tren = h - np.maximum(o, c)          # rau tren
    duoi = np.minimum(o, c) - l          # rau duoi

    if mau == "nen_dac":
        return (than_abs / bien) * chieu
    if mau == "rau_tren":
        return tren / bien
    if mau == "rau_duoi":
        return duoi / bien
    if mau == "doji":
        # Than cang nho so voi bien do thi cang "doji". Khong co dau - doji la
        # trang thai LUONG LU, gan cho no mot chieu la bia them thong tin.
        return 1.0 - (than_abs / bien)
    if mau == "bua":
        # Bua: rau duoi dai, than nho, nam o nua tren bar. Duong khi la bua
        # (dao chieu TANG), am khi la hinh guong cua no (sao bang nguoc).
        diem = (duoi / bien) - (tren / bien) - (than_abs / bien)
        return diem
    if mau == "sao_bang":
        return (tren / bien) - (duoi / bien) - (than_abs / bien)
    if mau == "trong":
        # Inside bar: ca bien do nam gon trong bar truoc. Tra ve do "gon".
        co = (h < h.shift(1)) & (l > l.shift(1))
        return co.astype(float) * (1.0 - bien / (h.shift(1) - l.shift(1))
                                   .replace(0.0, np.nan))
    if mau == "ngoai":
        co = (h > h.shift(1)) & (l < l.shift(1))
        return co.astype(float) * chieu
    if mau == "nhan_chim":
        # Than bar nay TRUM than bar truoc VA nguoc chieu bar truoc.
        tren_truoc = np.maximum(o.shift(1), c.shift(1))
        duoi_truoc = np.minimum(o.shift(1), c.shift(1))
        trum = (np.maximum(o, c) >= tren_truoc) & (np.minimum(o, c) <= duoi_truoc)
        doi_chieu = (chieu * np.sign(than.shift(1))) < 0
        return (trum & doi_chieu).astype(float) * chieu
    # ba_nen: ba bar lien tiep cung chieu, than moi bar chiem phan lon bien do
    dac = (than_abs / bien) > 0.5
    cung = (chieu == chieu.shift(1)) & (chieu == chieu.shift(2))
    ba = dac & dac.shift(1) & dac.shift(2) & cung
    return ba.astype(float) * chieu


def _nho_cua(df: pd.DataFrame) -> dict:
    k = id(df)
    d = _NHO_TOAN_HANG.get(k)
    if d is None:
        d = _NHO_TOAN_HANG[k] = {}
        weakref.finalize(df, _NHO_TOAN_HANG.pop, k, None)
    return d


#: BI DANH: ten khac cua toan hang DA CO. `None` = chi doi ten; dict = doi ten
#: kem dat san truong.
#:
#: VI SAO CAN (do 06/09/2026 tren ban tho da boc). 39 co che chet o cong voi
#: `KeyError: chi bao 'stochastik' khong biet`, va khi lat ra thi **khong cai
#: nao la nang luc con thieu**: ngu phap da co `stochastic`, da co `bollinger`
#: voi `lay=tren/duoi`, da co `gia` voi `cot`. Chung chet vi nguoi viet ma goi
#: no bang ten khac - `stoch_k`, `bb_upper`, `upperbuffer`, `high`.
#:
#: Day la dang that bai dat nhat cua ca day chuyen: mat mot co che THAT vi mot
#: van de CHINH TA. Cung ho benh voi [[ket-luan-am-phai-phan-biet-chua-do]] -
#: "khong dien dat duoc" va "goi bang ten khac" bi tron lam mot.
#:
#: Chi nhan bi danh cho thu ngu phap DA LAM DUOC. Ten cua mot nang luc chua co
#: (`sar`, `kci`, `smoothacfbuffer`) KHONG duoc dua vao day: gan bua no vao mot
#: toan hang gan giong la che ra mot co che khong ai viet.
BI_DANH: dict[str, dict | None] = {
    # Stochastic - mot ten, nam cach viet
    "stoch": None, "stochastik": None, "stochastics": None, "stoch_k": None,
    "%k": None, "k_stoch": None,
    # Bollinger - bo doc rut ra theo ten BUFFER cua MT5
    "bb_upper": {"lay": "tren"}, "upperbuffer": {"lay": "tren"},
    "upper_band": {"lay": "tren"}, "bb_up": {"lay": "tren"},
    "bb_lower": {"lay": "duoi"}, "lowerbuffer": {"lay": "duoi"},
    "lower_band": {"lay": "duoi"}, "bb_low": {"lay": "duoi"},
    "bb_middle": {"lay": "giua"}, "bb_basis": {"lay": "giua"},
    "middleband": {"lay": "giua"},
    # Cot gia goi thang bang ten cot
    "high": {"cot": "high"}, "low": {"cot": "low"},
    "open": {"cot": "open"}, "close": {"cot": "close"},
    "hl2": {"cot": "hl2"}, "hlc3": {"cot": "hlc3"}, "ohlc4": {"cot": "ohlc4"},
    # Hinh hoc - CHI nhung ten la mot cach viet khac cua dung phep tinh o day.
    #
    # `trendline` KHONG co trong bang nay du no la tu duoc nhac nhieu: duong xu
    # huong ve tay di qua HAI dinh nguoi ta chon, con `duong_xu_huong` la hoi
    # quy tren n bar. Hai thu khac nhau, va gan bi danh giua chung la "che ra
    # mot co che khong ai viet" - dung dieu ma ghi chu cua bang nay cam.
    # `slope` cung khong: do doc cua ho la gia/bar, cua ta la ATR/bar.
    "fib": None, "fibonacci": None, "fibonacci_retracement": None,
    "fib_618": {"lay": "0.618"}, "fib_382": {"lay": "0.382"},
    "angle": None,
    # `ta.linreg(src, len, offset=0)` cua Pine tra ve GIA TRI duong tai bar
    # hien tai, khong phai do doc.
    "linreg": {"lay": "gia_tri"}, "linearregression": {"lay": "gia_tri"},
}
#: Bi danh -> ten that. Tach khoi BI_DANH cho de doc.
BI_DANH_TEN = {
    "stoch": "stochastic", "stochastik": "stochastic", "stochastics": "stochastic",
    "stoch_k": "stochastic", "%k": "stochastic", "k_stoch": "stochastic",
    "bb_upper": "bollinger", "upperbuffer": "bollinger", "upper_band": "bollinger",
    "bb_up": "bollinger", "bb_lower": "bollinger", "lowerbuffer": "bollinger",
    "lower_band": "bollinger", "bb_low": "bollinger", "bb_middle": "bollinger",
    "bb_basis": "bollinger", "middleband": "bollinger",
    "high": "gia", "low": "gia", "open": "gia", "close": "gia",
    "hl2": "gia", "hlc3": "gia", "ohlc4": "gia",
    "fib": "fibo", "fibonacci": "fibo", "fibonacci_retracement": "fibo",
    "fib_618": "fibo", "fib_382": "fibo",
    "angle": "goc",
    "linreg": "duong_xu_huong", "linearregression": "duong_xu_huong",
}


def _doi_bi_danh(t: dict) -> dict:
    """Ten khac -> ten chinh. Truong nguoi viet dat san LUON THANG mac dinh
    cua bi danh (`bb_upper` co `lay=duoi` thi ho co y do rieng)."""
    cb = str(t.get("chi_bao", "")).lower()
    if cb not in BI_DANH_TEN:
        return t
    ra = dict(t)
    ra["chi_bao"] = BI_DANH_TEN[cb]
    for k, v in (BI_DANH.get(cb) or {}).items():
        ra.setdefault(k, v)
    return ra


def _toan_hang_tinh(df: pd.DataFrame, t: dict) -> pd.Series:
    """Phan TINH THAT cua `toan_hang`. Xem giai thich o do."""
    if "hang" in t:
        return pd.Series(float(t["hang"]), index=df.index)

    t = _doi_bi_danh(t)
    cb = str(t.get("chi_bao", "")).lower()
    n = int(t.get("n", 14) or 14)

    if cb == "gia":
        return _cot(df, str(t.get("cot", "close")).lower())
    if cb == "rsi":
        # Nhan `cua`/`cot` tu 01/09: `rsi(ema(close,5), 14)` va `rsi(hl2, 14)`
        # la dang co that trong ma nguoi ta viet, va truoc do chung bi vut.
        x = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        return MAU_MOD.rsi(x, n)
    if cb == "ibs":
        return MAU_MOD.ibs(df)
    if cb == "atr":
        return MAU_MOD.atr(df, n)
    # `ema`/`sma`/`wma`/`smma` nhan CA `cot` (cot gia) LAN `cua` (toan hang bat ky).
    #
    # Truoc 01/09 chung chi lam muot mot COT GIA, va do la mot gioi han that:
    # `ema(DX, 6)`, `ema(rsi, 9)`, `sma(atr, 20)` la nhung dang cuc ky pho bien
    # trong ma that. Do duoc: `SmoothedADX1 = ema(DX, input(6))` lam ca mot chien
    # luoc ADX rot o buoc dich chi vi khong lam muot duoc mot chuoi khong-phai-gia.
    # `tb`/`do_lech` da nhan `cua` tu truoc, nen day chi la lam cho nhat quan.
    if cb in ("ema", "sma"):
        x = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        return MAU_MOD.ema(x, n) if cb == "ema" else MAU_MOD.sma(x, n)
    if cb == "bien_do":
        return _cot(df, "high") - _cot(df, "low")
    if cb == "than_nen":
        return _cot(df, "close") - _cot(df, "open")
    if cb == "mau_nen":
        return _mau_nen(df, str(t.get("mau", "nhan_chim")).lower())
    if cb == "khoi_luong":
        return _cot(df, "tick_volume") if "tick_volume" in df.columns \
            else pd.Series(np.nan, index=df.index)
    if cb == "gio":
        # Cung gac nhu `mau._phai_co_gio`, nhung cho duong DSL. Do that
        # 03/09/2026: `mat_can_bang_lenh_dong_cua` (gio >= 20 va gio <= 22) va
        # `hoan_lai_sau_gio_dinh_gia_nav` (gio >= 16 va gio < 17) chay tren
        # US500CASH.D1 - moi bar co hour=0 nen dieu kien LUON SAI, tin hieu
        # toan 0, va doi bat ky tham so nao cung khong lam no doi. Chung lot
        # qua bo do on dinh nhu mot "cao nguyen" hoan hao.
        #
        # Nem loi thay vi tra chuoi 0: mot co che theo GIO chay tren khung
        # khong co gio la LOI CAU HINH, khong phai mot co che khong vao lenh.
        MAU_MOD._phai_co_gio(df, f"DSL chi_bao='gio'")
        return pd.Series(df.index.hour, index=df.index, dtype=float)
    if cb == "ngay_trong_tuan":
        return pd.Series(df.index.dayofweek, index=df.index, dtype=float)
    if cb == "ngay_trong_thang":
        return pd.Series(df.index.day, index=df.index, dtype=float)
    if cb == "thang":
        return pd.Series(df.index.month, index=df.index, dtype=float)

    # --- toan tu GOP: nhan MOT DANH SACH toan hang ---
    # Them 16/08 vi tang BOC bao dung cho thieu: GMMA can
    # mean(EMA3,EMA5,EMA7,EMA10,EMA12,EMA15) vs mean(EMA30..EMA60), va no da
    # phai xap xi bang EMA9 vs EMA43 - khong tuong duong. Mot dai chi bao khong
    # phai mot chi bao trung binh: dai bo qua khi cac duong PHAN KY.
    if cb in ("tb_cua_cac", "cao_nhat_cua_cac", "thap_nhat_cua_cac", "tong_cua_cac"):
        ds = t.get("toan_hang") or []
        if not isinstance(ds, list) or not ds:
            raise KeyError(f"'{cb}' can truong 'toan_hang' la danh sach khong rong")
        khung = pd.concat([toan_hang(df, x) for x in ds[:24]], axis=1)
        if cb == "tb_cua_cac":
            return khung.mean(axis=1)
        if cb == "tong_cua_cac":
            return khung.sum(axis=1)
        return khung.max(axis=1) if cb == "cao_nhat_cua_cac" else khung.min(axis=1)

    # --- TO HOP TUYEN TINH: sum(he_so[i] * toan_hang[i]) ---
    #
    # Them 01/09. Vi sao can: bo doc ma rut duoc guard cua `strategy.entry` roi
    # nhung phan lon dieu kien Pine that so gia voi mot MUC DUOC TINH RA -
    # `crossover(source, BBlower)` voi `BBlower = basis - mult * dev`,
    # `crossover(price, bottom)`, kenh Keltner, pivot. Ngu phap co `tb` va
    # `do_lech` nhung khong co phep cong/nhan nen khong viet noi `tb + 2*do_lech`,
    # va moi chien luoc ho do deu rot o buoc dich.
    #
    # Mot toan tu tuyen tinh mo ca ho do ma khong mo them cua nao: no chi cong
    # va nhan cac toan hang DA CO, khong co nhanh nao nhin ve tuong lai.
    #   Bollinger duoi = tb(close,20) - 2*do_lech(close,20)
    #   Keltner tren   = ema(close,20) + 2*atr(14)
    if cb == "tuyen_tinh":
        ds = t.get("toan_hang") or []
        hs = t.get("he_so") or []
        if not isinstance(ds, list) or not ds:
            raise KeyError("'tuyen_tinh' can 'toan_hang' la danh sach khong rong")
        if len(hs) != len(ds):
            raise KeyError("'tuyen_tinh': 'he_so' phai cung do dai 'toan_hang'")
        tong = None
        for h, x in zip(hs[:12], ds[:12]):
            phan = float(h) * toan_hang(df, x)
            tong = phan if tong is None else tong + phan
        return tong + float(t.get("cong_them", 0.0))

    # --- CHI BAO MUC KHUNG: can ca OHLC, khong tinh tu mot toan hang con ---
    #
    # Them 01/09. Danh sach nay KHONG phai doan: no la thu tu do duoc tu ma that
    # (`thu_hoi_thanh_phan.toan_hang_con_thieu`), xep theo so lan nguoi viet bot
    # thuc su dung. Moi cai them vao day mo khoa mot so chien luoc dem duoc.
    if cb == "wma":                       # 56 lan
        s = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        w = np.arange(1, n + 1, dtype=float)
        return s.rolling(n).apply(lambda x: float(np.dot(x, w) / w.sum()), raw=True)
    if cb == "smma":                      # 46 lan - RMA cua Wilder, dung trong ADX/RSI
        s = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        return s.ewm(alpha=1.0 / max(n, 1), adjust=False).mean()
    if cb == "cci":                       # 33 lan
        # Mac dinh la typical price (hlc3) dung nhu sach; nhung `ta.cci(src, n)`
        # cua Pine nhan nguon bat ky, nen cho khai `cua`/`cot`.
        tp = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
              else _cot(df, str(t.get("cot", "hlc3")).lower()))
        tb_ = tp.rolling(n).mean()
        mad = tp.rolling(n).apply(
            lambda x: float(np.mean(np.abs(x - x.mean()))), raw=True)
        return (tp - tb_) / (0.015 * mad.replace(0, np.nan))
    if cb == "stochastic":                # 20 lan
        thap = _cot(df, "low").rolling(n).min()
        cao = _cot(df, "high").rolling(n).max()
        return 100.0 * (_cot(df, "close") - thap) / (cao - thap).replace(0, np.nan)
    if cb == "obv":                       # 29 lan
        kl = (_cot(df, "tick_volume") if "tick_volume" in df.columns
              else pd.Series(1.0, index=df.index))
        return (np.sign(_cot(df, "close").diff().fillna(0.0)) * kl).cumsum()
    if cb == "adx":                       # 50 lan - Wilder
        h, l, c = _cot(df, "high"), _cot(df, "low"), _cot(df, "close")
        len_h, len_l = h.diff(), -l.diff()
        dm_duong = ((len_h > len_l) & (len_h > 0)) * len_h.clip(lower=0)
        dm_am = ((len_l > len_h) & (len_l > 0)) * len_l.clip(lower=0)
        tr = pd.concat([h - l, (h - c.shift(1)).abs(),
                        (l - c.shift(1)).abs()], axis=1).max(axis=1)
        a = 1.0 / max(n, 1)
        atr_ = tr.ewm(alpha=a, adjust=False).mean().replace(0, np.nan)
        di_d = 100.0 * dm_duong.ewm(alpha=a, adjust=False).mean() / atr_
        di_a = 100.0 * dm_am.ewm(alpha=a, adjust=False).mean() / atr_
        dx = 100.0 * (di_d - di_a).abs() / (di_d + di_a).replace(0, np.nan)
        return dx.ewm(alpha=a, adjust=False).mean()

    # --- BA TOAN HANG BAO CAO DA GIAU MAT (them 01/09/2026) ---
    #
    # `thu_hoi_thanh_phan._DIEN_DAT_DUOC` la mot ban SAO CHEP TAY cua danh sach
    # nay, va no khai ca ba cai duoi day la "da co" trong khi ngu phap khong he
    # co. Hau qua: bang `toan_hang_con_thieu` - thu duy nhat noi cho ta biet nen
    # them gi - **giau dung ba toan hang duoc dung nhieu nhat**: macd 115 lan
    # (hang 2), dong_luong 36 lan (hang 7), bollinger 35 lan (hang 8).
    # Nguon su that gio la `CHI_BAO_CO` o cuoi file nay, va co bai test doi
    # chieu tung ten mot bang cach GOI THAT.
    if cb == "macd":
        # `lay`: "macd" (mac dinh) | "tin_hieu" | "hieu" (histogram).
        x = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        nhanh = int(t.get("nhanh", 12) or 12)
        cham = int(t.get("cham", 26) or 26)
        n_tin = int(t.get("tin_hieu", 9) or 9)
        duong = MAU_MOD.ema(x, nhanh) - MAU_MOD.ema(x, cham)
        lay = str(t.get("lay", "macd")).lower()
        if lay == "macd":
            return duong
        tin = MAU_MOD.ema(duong, n_tin)
        return tin if lay == "tin_hieu" else duong - tin

    if cb == "donchian":
        # Kenh Donchian: cao nhat / thap nhat n bar. Viet duoc bang
        # `cao_nhat`/`thap_nhat` nhung 12 co che trong kho goi ten "donchian",
        # va mot toan hang dung ten giup bo doc khong phai doan cau truc.
        #
        # DICH MOT BAR: kenh phai tinh tren n bar TRUOC bar hien tai. Khong dich
        # thi `gia >= donchian_tren` LUON DUNG o dinh mới - vi chinh bar do da
        # duoc dua vao phep max. Do la mot cach nhin truoc rat kin.
        hi_ = _cot(df, "high").rolling(n).max().shift(1)
        lo_ = _cot(df, "low").rolling(n).min().shift(1)
        lay = str(t.get("lay", "tren")).lower()
        if lay == "tren":
            return hi_
        if lay == "duoi":
            return lo_
        if lay == "giua":
            return (hi_ + lo_) / 2.0
        if lay == "do_rong":
            return (hi_ - lo_) / ((hi_ + lo_) / 2.0).replace(0, np.nan)
        if lay == "vi_tri":
            return (_cot(df, "close") - lo_) / (hi_ - lo_).replace(0, np.nan)
        raise KeyError("'donchian': khong biet lay='%s' (co: tren, duoi, giua, "
                       "do_rong, vi_tri)" % lay)
    if cb == "ichimoku":
        # 10 co che trong kho nhac toi. Tenkan/Kijun la trung diem kenh; hai
        # duong may (senkou) tren BIEU DO duoc ve DICH TOI 26 bar, nghia la gia
        # tri nhin thay tai bar i duoc tinh tu du lieu cua bar i-26 - HOP LE.
        # Ve dung the la `.shift(+dich)`, KHONG phai shift(-dich).
        h_, l_ = _cot(df, "high"), _cot(df, "low")
        n_t = int(t.get("n_tenkan", 9) or 9)
        n_k = int(t.get("n_kijun", 26) or 26)
        n_b = int(t.get("n_senkou_b", 52) or 52)
        dich = int(t.get("dich", n_k) or n_k)

        def _giua(m):
            return (h_.rolling(m).max() + l_.rolling(m).min()) / 2.0

        tenkan, kijun = _giua(n_t), _giua(n_k)
        lay = str(t.get("lay", "kijun")).lower()
        if lay == "tenkan":
            return tenkan
        if lay == "kijun":
            return kijun
        if lay == "senkou_a":
            return ((tenkan + kijun) / 2.0).shift(dich)
        if lay == "senkou_b":
            return _giua(n_b).shift(dich)
        if lay == "day_may":
            return (((tenkan + kijun) / 2.0).shift(dich)
                    - _giua(n_b).shift(dich))
        if lay == "chikou":
            # Gia dong cua cua CHINH bar nay, doi chieu voi gia `dich` bar truoc.
            # Tra ve CHENH LECH de dung duoc ngay, va no chi doc qua khu.
            return _cot(df, "close") - _cot(df, "close").shift(dich)
        raise KeyError("'ichimoku': khong biet lay='%s' (co: tenkan, kijun, "
                       "senkou_a, senkou_b, day_may, chikou)" % lay)
    if cb == "vwap":
        # Gia trung binh theo KHOI LUONG trong n bar.
        #
        # Khong co cot khoi luong thi tra NaN chu KHONG lang le rot ve trung
        # binh thuong: mot "vwap" ma that ra la SMA se trong nhu mot chi bao
        # khac han, va khong ai biet.
        # KIEM KHAI BAO TRUOC, kiem du lieu SAU. Nguoc lai thi mot `lay` go sai
        # se di lot tren moi bang khong co cot khoi luong, roi nem loi o mot ma
        # khac vao mot luc khac - loi chuyen cho la loi kho tim nhat.
        lay = str(t.get("lay", "gia")).lower()
        if lay not in ("gia", "lech"):
            raise KeyError("'vwap': khong biet lay='%s' (co: gia, lech)" % lay)
        if "tick_volume" not in df.columns:
            return pd.Series(np.nan, index=df.index)
        kl = _cot(df, "tick_volume")
        tp = (_cot(df, "high") + _cot(df, "low") + _cot(df, "close")) / 3.0
        tong_kl = kl.rolling(n).sum()
        v = (tp * kl).rolling(n).sum() / tong_kl.replace(0, np.nan)
        if lay == "gia":
            return v
        return (_cot(df, "close") - v) / v.replace(0, np.nan)
    if cb == "heiken":
        return _heiken(df, str(t.get("lay", "chieu")).lower())
    if cb == "keltner":
        # Dai Keltner: EMA(n) +- k * ATR(n_atr). Cung ho voi `bollinger` nhung
        # do rong theo BIEN DO THAT (ATR) thay vi do lech chuan cua gia dong.
        #
        # Them 12/09/2026: **12 co che trong kho nhac toi "keltner" ma ngu phap
        # khong noi duoc** - chung hoac bi dich gan dung, hoac nam im. Cung luc
        # do co donchian 12, supertrend 16, ichimoku 10, renko 9, vwap 6.
        x = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        k = float(t.get("k", 2.0) or 2.0)
        giua = x.ewm(span=n, adjust=False).mean()
        a = _atr_series(df, int(t.get("n_atr", n) or n))
        lay = str(t.get("lay", "duoi")).lower()
        if lay == "giua":
            return giua
        if lay == "tren":
            return giua + k * a
        if lay == "duoi":
            return giua - k * a
        if lay == "do_rong":
            return (2.0 * k * a) / giua.replace(0, np.nan)
        if lay == "phan_tram_b":
            tren, duoi = giua + k * a, giua - k * a
            return (x - duoi) / (tren - duoi).replace(0, np.nan)
        raise KeyError("'keltner': khong biet lay='%s' (co: giua, tren, duoi, "
                       "do_rong, phan_tram_b)" % lay)
    if cb == "supertrend":
        return _supertrend(df, n, float(t.get("k", 3.0) or 3.0),
                           str(t.get("lay", "chieu")).lower())
    if cb == "bollinger":
        # `lay`: "tren" | "giua" | "duoi" | "do_rong" | "phan_tram_b".
        # Ngu phap da viet duoc dai nay bang `tuyen_tinh`, nhung phai go ba tang
        # long nhau moi lan - va bo doc phai DOAN ra cau truc do tu mot dong
        # Pine `ta.bb(src, 20, 2)`. Mot toan hang thang giam khoang cach do.
        x = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        k = float(t.get("k", 2.0) or 2.0)
        giua = x.rolling(n).mean()
        sd = x.rolling(n).std()
        lay = str(t.get("lay", "duoi")).lower()
        if lay == "giua":
            return giua
        if lay == "tren":
            return giua + k * sd
        if lay == "duoi":
            return giua - k * sd
        if lay == "do_rong":
            return (2.0 * k * sd) / giua.replace(0, np.nan)
        if lay == "phan_tram_b":
            duoi = giua - k * sd
            return (x - duoi) / (2.0 * k * sd).replace(0, np.nan)
        raise KeyError(f"'bollinger': khong biet lay='{lay}'")

    if cb == "dong_luong":
        # `mom(src, n)` cua Pine = src - src[n]. Ngu phap co `doi` lam dung viec
        # do nhung qua truong `cua`; bo doc rut ra ten `dong_luong` va khong noi
        # duoc chung la mot. Giu ca hai ten cho mot phep tinh.
        x = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        return x.diff(n)

    # --- TUONG QUAN TRUOT giua HAI toan hang (120 lan - nhieu nhat) ---
    if cb == "tuong_quan":
        ds = t.get("toan_hang") or []
        if not isinstance(ds, list) or len(ds) != 2:
            raise KeyError("'tuong_quan' can dung HAI toan hang trong 'toan_hang'")
        a = toan_hang(df, ds[0])
        b = toan_hang(df, ds[1])
        return a.rolling(n).corr(b)

    # --- TOAN TU CO NHO TRANG THAI ---
    #
    # Them 01/09 (chu du an chot). Vi sao can: sau khi sua bo doc, 11/18 chien
    # luoc Pine con lai deu chan o CUNG MOT loai bieu thuc - `direction < 0`,
    # `fractal_average[0] > [1]`, `close < dtime_l4`. Chung khong phai thieu chi
    # bao ma la mot LOAI KHAC: gia tri hom nay phu thuoc gia tri hom qua theo mot
    # quy tac re nhanh. Ngu phap truoc do chi co toan tu KHONG NHO (rolling,
    # shift, so sanh) nen khong phat bieu duoc.
    #
    # AN TOAN KHONG DOI. Ca hai toan tu duoi day chay MOT VONG TIEN theo thoi
    # gian, moi buoc chi doc bar hien tai va trang thai cua buoc TRUOC. Khong co
    # duong nao nhin ve tuong lai - va `kiem_khong_nhin_truoc` van chay tren
    # chung nhu moi co che khac.
    if cb == "trang_thai_lat":
        # Trang thai +1/-1, lat khi mot trong hai dieu kien dung. Day la hinh
        # dang chung cua supertrend, parabolic SAR, va moi bo loc che do:
        # "dang len cho toi khi co tin hieu xuong".
        len_ = t.get("len") or t.get("bat_len")
        xuong = t.get("xuong") or t.get("bat_xuong")
        if not isinstance(len_, dict) or not isinstance(xuong, dict):
            raise KeyError("'trang_thai_lat' can hai dieu kien 'len' va 'xuong'")
        a = _dieu_kien(df, [len_], mac_dinh=False).to_numpy()
        b = _dieu_kien(df, [xuong], mac_dinh=False).to_numpy()
        ra = np.zeros(len(df), dtype=float)
        cur = float(t.get("ban_dau", 0.0))
        for i in range(len(df)):
            if a[i]:
                cur = 1.0
            elif b[i]:
                cur = -1.0
            ra[i] = cur
        return pd.Series(ra, index=df.index)

    if cb == "dem_lien_tiep":
        # Bao nhieu bar LIEN TIEP toi nay dieu kien van dung (0 neu bar nay sai).
        # Dung cho "gia da tren duong trung binh N bar lien", "chuoi thang thu N".
        dk = t.get("khi")
        if not isinstance(dk, dict):
            raise KeyError("'dem_lien_tiep' can dieu kien 'khi'")
        a = _dieu_kien(df, [dk], mac_dinh=False).to_numpy()
        ra = np.zeros(len(df), dtype=float)
        d = 0.0
        for i in range(len(df)):
            d = d + 1.0 if a[i] else 0.0
            ra[i] = d
        return pd.Series(ra, index=df.index)

    # DAT TRUOC chot `cua is None` ben duoi: gann_sq9 nhan `cot` HOAC `cua`,
    # nhung truoc 11/09 no nam SAU chot do nen ban khong co `cua` khong bao gio
    # toi noi - `{'chi_bao':'gann_sq9'}` nem KeyError 'khong biet'. Mot toan hang
    # khai trong CHI_BAO_CO ma goi khong duoc doc y het mot toan hang khong ton tai.
    # --- GANN SQUARE OF 9: mot MUC GIA HINH HOC ---
    #
    # Them 08/09/2026 theo gia thuyet #4 cua chu du an. Vi sao can: "square of
    # nine" xuat hien **0 lan** trong ca 574 co che cua kho, trong khi no la mot
    # ho muc tinh co that va rat pho bien. Ngu phap co `vung` (bien tren/duoi
    # tinh tai bar sinh) nen chi con thieu ham tinh RA muc; them mot toan hang
    # la du, khong can mot he rieng - va nho the no thua huong nguyen cong
    # placebo/holdout/MDE thay vi tu do bang mot script roi.
    #
    #     muc = (sqrt(nen) + huong * k * goc/360) ** 2
    #
    # `nen` la mot toan hang bat ky (thuong la `thap_nhat`/`cao_nhat` n bar =
    # mot pivot), nen KHONG co nhanh nhin truoc: no chi doc qua khu nhu moi
    # toan hang khac.
    #
    # BA CHOT CHAN cua chinh ho nay:
    #   - gia am hoac 0 -> sqrt khong xac dinh. Tra NaN, khong tra 0: mot muc
    #     bang 0 se bien moi so sanh thanh mot dieu kien hien nhien.
    #   - THANG DO. Muc cach nhau ~2*sqrt(nen)*goc/360. Tren vang (nen ~2000)
    #     buoc la ~4,0 diem; tren EURUSD (nen ~1,08) buoc la ~0,0029. Cung mot
    #     `goc` cho ra do hiem HOAN TOAN khac nhau giua hai tai san - dung bug,
    #     dung ky vong (chu du an do duoc: "0 lenh o tai san bien dong thap").
    #     Cach chuyen dung tai san la `ngoai_sinh.quy_doi` KHOP TY LE KICH HOAT,
    #     khong phai bung nguyen con so `goc`.
    # --- MOC NEO THEO CHU KY (magnetic) ---
    #
    # Them 12/09/2026 sau khi `quy_luat_song` do duoc quy luat L5: diem KET THUC
    # HOI nam gan `dong_thang_truoc` hon muc ngau nhien **5,4 den 31,2 lan**, va
    # no dat 15/15 o tren 3 ma x 5 khung (M15..D1). Truoc do ngu phap khong noi
    # duoc moc nao nhu vay, nen mot quy luat da do duoc van khong thanh co che.
    #
    # LUU Y QUAN TRONG: cung mot moc, hai cach hoi cho hai ket qua khac han:
    #   "gia co CHAM moc khong"      -> 1,35 lan muc ngau nhien   (yeu)
    #   "HOI co DUNG o moc khong"    -> 5-31 lan                  (rat manh)
    # Nen moc nay dung de dat NGUONG/MUC TIEU, khong dung lam tin hieu "cham".
    #
    # AN TOAN: dich mot KY chu khong mot BAR. Cai bay 15/08 trong `mau.py` la
    # `transform("last")` phat gia dong cua CUOI NGAY cho MOI bar trong ngay roi
    # `.shift(1)` chi dich mot BAR - ra EURCAD H1 CAGR 115% Sharpe 10,4.
    # `mo_<ky>` cua ky HIEN TAI la hop le: biet ngay tu bar dau ky.
    if cb == "moc_ky":
        ky = str(t.get("ky", "thang")).lower()
        lay = str(t.get("lay", "dong_truoc")).lower()
        if ky not in ("ngay", "tuan", "thang"):
            raise KeyError("'moc_ky': ky phai la ngay/tuan/thang, khong phai '%s'" % ky)
        idx = pd.DatetimeIndex(df.index)
        if idx.tz is not None:
            idx = idx.tz_convert("UTC").tz_localize(None)
        nhom = {"ngay": idx.normalize(),
                "tuan": idx.to_period("W").start_time,
                "thang": idx.to_period("M").start_time}[ky]
        gr = df.groupby(nhom)
        ns = pd.Series(nhom, index=df.index)
        if lay == "mo":                       # mo ky HIEN TAI - hop le
            return ns.map(gr["open"].first())
        bang = {"dong_truoc": gr["close"].last(), "cao_truoc": gr["high"].max(),
                "thap_truoc": gr["low"].min(), "mo_truoc": gr["open"].first()}
        if lay not in bang:
            raise KeyError("'moc_ky': khong biet lay='%s' (co: mo, mo_truoc, "
                           "dong_truoc, cao_truoc, thap_truoc)" % lay)
        return ns.map(bang[lay].shift(1))     # DICH MOT KY, khong mot bar

    if cb == "gann_sq9":
        goc = float(t.get("goc", 45.0) or 45.0)
        k = float(t.get("k", 1.0) or 1.0)
        huong = 1.0 if float(t.get("huong", 1) or 1) >= 0 else -1.0
        nen = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
               else _cot(df, str(t.get("cot", "close")).lower()))
        can = np.sqrt(nen.where(nen > 0))
        return (can + huong * k * goc / 360.0) ** 2

    # --- HINH HOC: fibo · duong_xu_huong · goc (them 12/09/2026) ---
    #
    # So do he thong co dong: *"Cac dang phuong phap dac biet nhu hinh hoc,
    # gann,..."*. Gann da co tu 08/09 (`gann_sq9`), hinh hoc thi chua co gi.
    #
    # DO DUOC (12/09, tren kho 1.764 co che va corpus 150 cau/tang):
    #   kho:    28 co che nhac "fib" · 9 "retrace" · 4 "angle" · 3 "trendline"
    #   corpus: nhom tu vung `hinh_hoc` la nhom thieu lon thu NHI o tang KHAU DOC
    #           (16/150 cau) va thu NHI o tang NGU PHAP (3/150)
    # Tuc day khong phai mot y tuong dep - la mot lo thung do dem duoc.
    #
    # CA BA DEU TRA VE SO KHONG THANG DO (tru cac muc GIA, xem tung nhanh). Do
    # 12/09 cho biet vi sao phai vay: nguong `atr14 < 0,003472` hoc tu train
    # kich hoat 1.719 lan o train va **0 lan o holdout** - mot toan hang tra ve
    # gia tho bien ca co che thanh co che cua MOT tai san o MOT thoi ky.
    if cb == "fibo":
        # Muc thoai lui Fibonacci giua dinh/day cua n bar gan nhat.
        #
        # `lay`:
        #   "vi_tri" (mac dinh)  gia dang o muc thoai lui nao - SO LIEN TUC:
        #                        0 = dang o dau song (dinh, neu song tang),
        #                        1 = da thoai lui het ve goc, >1 = pha qua goc,
        #                        <0 = dang lam dinh moi. Khong thang do.
        #   0.236/0.382/0.5/0.618/0.786 (hay "muc" + truong `muc`)
        #                        MUC GIA cua thoai lui do - de so voi `gia`
        #                        (`gia cheo_xuong fibo(0.618)`). Day la gia, nen
        #                        no thang do - dung nhu `donchian` lay=tren.
        #   "khoang_cach"        (gia - muc) chia BIEN DO SONG - khong thang do,
        #                        dung khi muon "gia cach muc 0,618 bao xa".
        # Ti le > 1 la muc MO RONG (1.272 / 1.618) - cung cong thuc, nam ben kia
        # goc song; 3 co che trong kho noi toi "extension" lam muc chot loi.
        #
        # `dinh`/`day` KHONG lo ra o day: `donchian` lay=tren/duoi da lam dung
        # viec do (co dich mot bar y het), va hai ten cho mot phep tinh la cach
        # bang "toan hang con thieu" bat dau noi doi.
        lay = str(t.get("lay", "vi_tri")).lower()
        dinh, day_, tang = _song_fibo(df, n, t.get("huong", "tu_dong"))
        bien = dinh - day_
        bien = np.where(bien > 0, bien, np.nan)
        c = _cot(df, "close").to_numpy(float)
        if lay == "vi_tri":
            # Do SAU cua thoai lui, do tu dau song. Cung mot cong thuc cho ca
            # hai chieu nho lay goc song lam moc.
            sau = np.where(tang > 0, dinh - c, c - day_)
            return pd.Series(sau / bien, index=df.index)
        # "muc" va "khoang_cach" lay ti le tu truong `muc`; con lai thi CHINH
        # `lay` la ti le ("0.618" / "61.8" / 0.618).
        f = (_ti_le_fibo(t.get("muc", 0.618)) if lay in ("muc", "khoang_cach")
             else _ti_le_fibo(lay))
        if f is None or not (0.0 <= f <= 2.0):
            raise KeyError(
                "'fibo': khong biet lay='%s' (co: vi_tri, khoang_cach, muc, "
                "hay mot ti le trong [0; 2] - %s la nam muc thoai lui chuan, "
                "viet '0.618' hay '61.8'; > 1 la muc MO RONG nhu 1.618)"
                % (lay, ", ".join(str(x) for x in MUC_FIBO)))
        muc_gia = np.where(tang > 0, dinh - f * bien, day_ + f * bien)
        if lay == "khoang_cach":
            return pd.Series((c - muc_gia) / bien, index=df.index)
        return pd.Series(muc_gia, index=df.index)

    if cb in ("duong_xu_huong", "goc"):
        # Duong hoi quy tuyen tinh n bar, va GOC cua no.
        #
        # `chuan` - chia do doc cho cai gi de het thang do:
        #   "atr" (mac dinh)  ATR(n_atr) cua khung. Do doc thanh "bao nhieu ATR
        #                     moi bar", so sanh duoc giua US500 va EURUSD.
        #   "nguon"           trung binh |doi| cua chinh chuoi nguon n bar. Dung
        #                     khi `cua` KHONG phai gia (`duong_xu_huong` cua
        #                     rsi chang han): chia cho ATR khi do la chia hai
        #                     don vi khac nhau, ra mot so khong doc duoc.
        #
        # `goc` = arctan cua do doc da chuan hoa, theo DO. No khong them thong
        # tin so voi `lay="doc"` nhung no CHAN LAI trong (-90; 90): do doc co
        # duoi rat day (mot nen khe gia lam no gap hang chuc lan), nen mot
        # nguong hoc tren train de thanh nguong khong bao gio cham lai o holdout.
        # 45 do = gia di dung MOT ATR moi bar.
        #
        # DA DO, DUNG TIN QUA MUC (EURUSD D1, train 7.232 bar / holdout 4.822):
        # chuan hoa ATR chuyen duoc o q5..q95 nhung **q2 va q98 ra 0 lan kich
        # hoat o holdout**. ATR(n) la mau so lam muot cham, con do doc thi nhay
        # ngay - nen dung duoi phan phoi van con mui che do. Ba cach chua, ca ba
        # deu viet duoc bang ngu phap hien co:
        #   n_atr lon hon (n_atr=100 -> q2 co 9 lan, q98 co 15)
        #   chuan="nguon"          -> q2 62 lan, q98 24 - chuyen duoc o MOI muc
        #   boc trong `phan_vi`    -> chuyen duoc o moi muc (cach chuan cua lab)
        # De doi chieu: `atr14` THO o cung phep do ra 0 lan o q2/q5 va **949 lan
        # o q90 trong khi train chi 724** - tuc gap doi ti le. Chuan hoa khong
        # phai la thuoc chua bach benh, no chi ha benh xuong hai bac.
        x = (toan_hang(df, t["cua"]) if isinstance(t.get("cua"), dict)
             else _cot(df, str(t.get("cot", "close")).lower()))
        doc, r2, gia_tri = _hoi_quy_truot(x, n)
        chuan = str(t.get("chuan", "atr")).lower()
        if chuan == "atr":
            thang = _atr_series(df, int(t.get("n_atr", n) or n))
        elif chuan == "nguon":
            thang = x.diff().abs().rolling(max(int(n), 2)).mean()
        else:
            raise KeyError("'%s': khong biet chuan='%s' (co: atr, nguon)"
                           % (cb, chuan))
        thang = thang.where(thang > 0)
        doc_chuan = doc / thang

        if cb == "goc":
            lay = str(t.get("lay", "do")).lower()
            if lay == "do":
                return np.degrees(np.arctan(doc_chuan))
            if lay == "radian":
                return np.arctan(doc_chuan)
            raise KeyError("'goc': khong biet lay='%s' (co: do, radian)" % lay)

        lay = str(t.get("lay", "doc")).lower()
        if lay == "doc":
            return doc_chuan
        if lay == "r2":
            return r2
        if lay == "gia_tri":
            return gia_tri                 # MUC GIA cua duong tai bar nay
        if lay == "lech":
            return (x - gia_tri) / thang   # gia dang cach duong may ATR
        raise KeyError("'duong_xu_huong': khong biet lay='%s' (co: doc, r2, "
                       "gia_tri, lech)" % lay)

    # --- toan tu BIEN DOI: nhan mot toan hang con ---
    con = t.get("cua")
    if con is None:
        raise KeyError(f"chi bao '{cb}' khong biet, va khong co truong 'cua'")
    x = toan_hang(df, con)
    if cb == "tb":
        return x.rolling(n).mean()
    if cb == "do_lech":
        return x.rolling(n).std()
    if cb == "phuong_sai":                 # 72 lan trong ma that
        return x.rolling(n).var()
    if cb == "lech_tb":
        # (x - trung binh n) / trung binh n  -> khoang cach TI LE toi duong
        # trung binh. Khac `zscore` o MAU SO: zscore chia cho do lech chuan, cai
        # nay chia cho chinh trung binh, nen doc duoc thang la "cach MA bao
        # nhieu phan tram".
        #
        # Them 12/09/2026 de dich duoc dac trung `dist_ma200_atr` cua `ds/mimic`.
        # Luu y cai bay o ben do: TEN co chu "atr" nhung CONG THUC chia cho
        # ma200, tuc no la PHAN TRAM chu khong phai so lan ATR. Mot luat hoc ra
        # `dist_ma200_atr <= 0,02` nghia la 2%, khong phai 0,02 ATR - lech nhau
        # hai bac do lon.
        tb_ = x.rolling(n).mean()
        return (x - tb_) / tb_.replace(0, np.nan)
    if cb == "zscore":
        sd = x.rolling(n).std()
        return (x - x.rolling(n).mean()) / sd.replace(0, np.nan)
    if cb == "phan_vi":
        # thu hang cua gia tri HIEN TAI trong N bar GAN NHAT, ke ca bar nay.
        # Hop le: bar nay da dong. `rank(pct=True)` tren cua so truot.
        return x.rolling(n).rank(pct=True)
    if cb == "doi":
        return x.diff(n)
    if cb == "doi_pct":
        return x.pct_change(n)
    if cb == "tre":
        return x.shift(max(n, 1))          # LUI ve qua khu; n am bi chan o duoi
    if cb == "cao_nhat":
        return x.rolling(n).max()
    if cb == "thap_nhat":
        return x.rolling(n).min()
    if cb == "tuyet_doi":
        return x.abs()
    if cb == "tong":                       # 19 lan trong ma that
        return x.rolling(n).sum()

    raise KeyError(f"chi bao khong biet: '{cb}'")


#: NGUON SU THAT ve nhung toan hang ngu phap noi duoc. `thu_hoi_thanh_phan`
#: PHAI import tu day, khong duoc giu ban sao.
#:
#: VI SAO (do 01/09/2026). `thu_hoi_thanh_phan._DIEN_DAT_DUOC` la mot ban chep
#: tay, va no da lech ca HAI CHIEU:
#:   - khai thua `macd`, `bollinger`, `dong_luong` -> bang "toan hang con
#:     thieu", thu duy nhat noi cho ta biet nen them gi, GIAU dung ba cai duoc
#:     dung nhieu nhat (115 / 35 / 36 lan trong ma that);
#:   - khai thieu 6 toan tu co that (`tb_cua_cac`, `cao_nhat_cua_cac`,
#:     `thap_nhat_cua_cac`, `tong_cua_cac`, `dem_lien_tiep`, `trang_thai_lat`)
#:     -> thanh phan nao dung chung bi cham la "khong dien dat duoc" va bi vut.
#: Mot danh sach chep tay se lech lai. Bai test doi chieu tung ten bang cach
#: GOI THAT `toan_hang()`, khong doc lai chinh danh sach nay.
CHI_BAO_CO = {
    # nguon truc tiep tu bang gia
    "gia", "bien_do", "than_nen", "khoi_luong", "ibs",
    # lich
    "gio", "ngay_trong_tuan", "ngay_trong_thang", "thang",
    # chi bao muc khung (can nhieu cot)
    "rsi", "atr", "cci", "stochastic", "obv", "adx",
    "ema", "sma", "wma", "smma", "macd", "bollinger", "dong_luong",
    # gop danh sach toan hang
    "tb_cua_cac", "cao_nhat_cua_cac", "thap_nhat_cua_cac", "tong_cua_cac",
    "tuyen_tinh", "tuong_quan",
    # muc gia hinh hoc (08/09/2026)
    "gann_sq9",
    # HINH HOC (12/09/2026) - dong "hinh hoc, gann,..." cua so do he thong
    "fibo", "duong_xu_huong", "goc",
    # moc neo theo chu ky (magnetic) - them 12/09 sau quy luat L5
    "moc_ky",
    # co nho trang thai
    "trang_thai_lat", "dem_lien_tiep",
    # BAY TOAN HANG BI LOT SO (19/09/2026). Bo dieu phoi `_toan_hang_tinh` DA
    # tinh duoc ca bay, nhung chung khong co ten o day - ma day chinh la
    # `thu_hoi_thanh_phan._DIEN_DAT_DUOC`, danh sach bo boc dung de quyet dinh
    # "co dien dat duoc khong". Hau qua: moi tai lieu noi ve Donchian, Ichimoku,
    # VWAP, Keltner, Supertrend, Heiken Ashi hay mau nen deu bi cham la KHONG
    # DIEN DAT DUOC roi bo, trong khi ngu phap chay chung tot.
    #
    # Docstring o `_toan_hang_tinh` da canh bao dung lop loi nay mot lan roi
    # ("BA TOAN HANG BAO CAO DA GIAU MAT", 01/09) va no tai dien vi bai test chi
    # khoa MOT CHIEU: "khai ra thi phai goi duoc". Chieu con thieu - "goi duoc
    # thi phai khai ra" - nay da co `test_moi_toan_hang_goi_duoc_deu_KHAI_RA`.
    #
    # Do luc do: kho co che rong 8 chi bao, con bo dieu phoi noi duoc 52.
    "donchian", "ichimoku", "vwap", "keltner", "supertrend", "heiken",
    "mau_nen",
    # bien doi mot toan hang con (qua truong `cua`)
    "tb", "do_lech", "phuong_sai", "zscore", "phan_vi", "doi", "doi_pct",
    "tre", "cao_nhat", "thap_nhat", "tuyet_doi", "tong",
}

#: Toan hang nhan truc tiep truong `cot` (nguon gia). Cac toan tu cua so nhan
#: nguon gia qua truong `cua` chu khong phai `cot`, nhung bo doc rut ra dang
#: `highest(high, 55)` nen chung phai co mat o day - neu khong thi Donchian,
#: dieu kien pha vo pho bien nhat, bi cham la "khong dien dat duoc".
CHI_BAO_NHAN_COT = {
    "gia", "ema", "sma", "wma", "smma", "macd", "bollinger", "dong_luong",
    "cao_nhat", "thap_nhat", "tb", "do_lech", "phuong_sai", "zscore",
    "phan_vi", "doi", "doi_pct", "tre", "tuyet_doi", "tong", "rsi", "cci",
    "gann_sq9",
    # `duong_xu_huong`/`goc` khop duong tren MOT chuoi nguon -> nhan `cot`.
    # `fibo` thi KHONG: no neo vao dinh/day, tuc luon can ca high lan low.
    "duong_xu_huong", "goc",
    # `keltner` lay duong giua tu mot chuoi nguon (giong `bollinger`). Bay cai
    # con lai cua dot 19/09 thi KHONG: `donchian`/`ichimoku`/`supertrend`/
    # `heiken`/`mau_nen` deu can ca high lan low, con `vwap` can khoi luong.
    "keltner",
}


def _so_sanh(a: pd.Series, phep: str, b: pd.Series) -> pd.Series:
    # `==` / `!=` them 06/09/2026. Ly do: 7 co che chet o cong voi "phep '=='
    # khong hop le", va tat ca deu la dieu kien LICH - `ngay_trong_tuan == 2`
    # (Turnaround Tuesday), `gio == 9` (mo phien). Khong co phep bang thi ca
    # mot ho co che theo lich khong phat bieu duoc, va no bi ghi nham thanh
    # "spec hong" chu khong phai "ngu phap thieu".
    #
    # Tren chuoi LIEN TUC (gia, rsi) phep bang gan nhu khong bao gio dung -
    # va do la ket qua DUNG, khong phai loi: cong kich hoat se loai no ngay vi
    # 0% so bar. Khong tu y noi thanh "gan bang": mot nguong bia ra o day se
    # am tham doi y nghia cua moi co che dung `==`.
    if phep == "==":
        return a == b
    if phep == "!=":
        return a != b
    if phep == "<":
        return a < b
    if phep == "<=":
        return a <= b
    if phep == ">":
        return a > b
    if phep == ">=":
        return a >= b
    if phep == "cheo_len":
        return (a > b) & (a.shift(1) <= b.shift(1))
    if phep == "cheo_xuong":
        return (a < b) & (a.shift(1) >= b.shift(1))
    raise KeyError(f"phep so sanh khong biet: '{phep}'")


# ------------------------------------------------------------------- VUNG
#: Quan he giua gia cua bar hien tai va mot vung con song.
QUAN_HE_VUNG = {"cham", "bat_len", "bat_xuong", "trong", "xuyen_len",
                "xuyen_xuong"}
#: Vung chet khi nao. "cham" = chuan cua FVG/order block (lap day mot lan la
#: het); "dong_ngoai" = chi chet khi gia DONG CUA ra ngoai; "het_han" = chi
#: chet khi het `song` bar.
HUY_VUNG = {"cham", "dong_ngoai", "het_han"}
#: Tran so vung song cung luc. Khong phai toi uu - la CHAN AN TOAN: mot dieu
#: kien `tao` suy bien (luon dung) se sinh mot vung moi moi bar, va khong co
#: tran thi vong lap thanh O(n^2) tren 20.000 bar.
TRAN_VUNG_SONG = 64


def _vung(df: pd.DataFrame, v: dict) -> pd.Series:
    """Mot VUNG CO TRANG THAI -> chuoi bool "bar nay thoa quan he voi vung".

    ## VI SAO NGU PHAP CAN THU NAY (do tren kho 06/09/2026)

    Kho dang giu **14 dinh nghia FVG doc lap, 19 order block, 23 cau truc/BOS,
    13 thanh khoan, 6 ORB** - khoang 75 file - va tat ca deu dang bi dich thanh
    so sanh THEO TUNG NEN, tuc dich SAI. Mot khoang trong gia tao ra o bar i
    khong phai la mot dieu kien tai bar i: no la mot VAT THE song qua nhieu bar,
    co bien tren, bien duoi, va chet khi bi lap day. Bo boc khong dien duoc dieu
    do nen no dien `hang: 0` vao cho nguong, va ca ho tro thanh dieu kien hien
    nhien [[cong-chua-ap-cho-hang-trong-kho]].

    ## KHAI BAO

        {"vung": {
            "tao":  [dieu kien ...],      # bar nao SINH ra mot vung
            "tren": <toan hang>,          # bien tren, tinh TAI BAR SINH
            "duoi": <toan hang>,          # bien duoi, tinh TAI BAR SINH
            "song": 20,                   # song toi da bao nhieu bar
            "huy":  "cham"                # cham | dong_ngoai | het_han
         },
         "quan_he": "cham"}               # xem `QUAN_HE_VUNG`

    ## QUY UOC THOI GIAN VAN KHONG THE VI PHAM

    Bien vung tinh tai bar SINH bang chinh `toan_hang`, ma `toan_hang` khong co
    nhanh nao nhin ve tuong lai. Vung chi duoc dung tu bar sinh tro DI. Nen
    khong co duong nao de mot gia tri tuong lai chay nguoc vao tin hieu, giong
    het phan con lai cua ngu phap.

    Diem tinh te: mot FVG chuan dinh nghia bang bar i-2 va i (`low[i] >
    high[i-2]`), va CA HAI deu biet tai close cua bar i. Viet bang `tre` trong
    `tao` la du - khong can toan tu moi nao.

    ## QUAN HE

    Goi vung la doan [duoi, tren] (tu dao neu khai nguoc):
      `cham`        bien do bar phu len vung
      `trong`       gia dong cua nam trong vung
      `bat_len`     cham vung roi dong cua TREN vung  (tu choi tu duoi len)
      `bat_xuong`   cham vung roi dong cua DUOI vung
      `xuyen_len`   dong cua vuot han len tren sau khi bar truoc con o duoi
      `xuyen_xuong` nguoc lai
    """
    if not isinstance(v, dict):
        raise TypeError("'vung' phai la dict")
    kb = v.get("vung") if "vung" in v else v
    qh = str(v.get("quan_he", "cham"))
    if qh not in QUAN_HE_VUNG:
        raise KeyError("quan he vung khong biet: '%s'" % qh)

    tao = _dieu_kien(df, kb.get("tao") or [], mac_dinh=False).to_numpy()
    tren = toan_hang(df, kb["tren"]).to_numpy(dtype=float)
    duoi = toan_hang(df, kb["duoi"]).to_numpy(dtype=float)
    song = int(kb.get("song", 20) or 20)
    huy = str(kb.get("huy", "cham"))
    if huy not in HUY_VUNG:
        raise KeyError("cach huy vung khong biet: '%s'" % huy)

    hi = _cot(df, "high").to_numpy(dtype=float)
    lo = _cot(df, "low").to_numpy(dtype=float)
    dong = _cot(df, "close").to_numpy(dtype=float)
    n = len(df)
    ra = np.zeros(n, dtype=bool)

    # (bien duoi, bien tren, bar het han). Danh sach NGAN - xem TRAN_VUNG_SONG.
    song_ds: list = []
    for i in range(n):
        # MOT VUNG CHI SONG TU NEN SAU NEN SINH RA NO.
        #
        # Do 06/09/2026: ban dau vung duoc xet ngay tai nen sinh, va voi hinh
        # hoc cua FVG thi no LUON tu cham chinh no o do (bien tren = `low[i]`,
        # nen `low[i] <= tren` la hien nhien). Hau qua: moi vung song dung mot
        # nen roi chet, so lan kich hoat bang y so vung duoc tao, va **`song`
        # lan `huy` khong doi ket qua mot ly nao** - do lai voi song = 20/21/23/28
        # deu ra dung 20. Tuc hai nut van cua nguyen thuy la nut GIA
        # [[doi-tham-so-ma-khong-doi-ket-qua]].
        #
        # Va quan trong hon: co che that cua ho nay la "gia QUAY LAI lap gap",
        # khong phai "gap vua xuat hien". Xet tai nen sinh la dien sai chinh cai
        # minh dinh dien.
        if tao[i - 1] and i and np.isfinite(tren[i - 1]) and np.isfinite(duoi[i - 1]):
            a, b = ((duoi[i - 1], tren[i - 1]) if duoi[i - 1] <= tren[i - 1]
                    else (tren[i - 1], duoi[i - 1]))
            song_ds.append([a, b, i - 1 + song])
            if len(song_ds) > TRAN_VUNG_SONG:
                del song_ds[0]
        if not song_ds:
            continue
        con = []
        for z in song_ds:
            a, b, han = z
            if i > han:
                continue                                  # het han
            cham = (lo[i] <= b) and (hi[i] >= a)
            if not cham:
                con.append(z)
                continue
            if qh == "cham":
                ra[i] = True
            elif qh == "trong":
                ra[i] = ra[i] or (a <= dong[i] <= b)
            elif qh == "bat_len":
                ra[i] = ra[i] or (dong[i] > b)
            elif qh == "bat_xuong":
                ra[i] = ra[i] or (dong[i] < a)
            elif qh == "xuyen_len":
                ra[i] = ra[i] or (dong[i] > b and dong[i - 1] <= b if i else False)
            elif qh == "xuyen_xuong":
                ra[i] = ra[i] or (dong[i] < a and dong[i - 1] >= a if i else False)
            if huy == "cham":
                continue                                  # lap day mot lan la het
            if huy == "dong_ngoai" and (dong[i] > b or dong[i] < a):
                continue
            con.append(z)
        song_ds = con
    return pd.Series(ra, index=df.index)


def _dieu_kien(df: pd.DataFrame, ds: list, mac_dinh: bool) -> pd.Series:
    """Danh sach dieu kien -> chuoi bool. Rong thi tra `mac_dinh`."""
    if not ds:
        return pd.Series(mac_dinh, index=df.index)
    ra = None
    for d in ds:
        if "vung" in d:
            m = _vung(df, d)
        else:
            m = _so_sanh(toan_hang(df, d["trai"]), d.get("phep", ">"),
                         toan_hang(df, d["phai"]))
        m = m.fillna(False)
        ra = m if ra is None else (ra & m)
    return ra


# ------------------------------------------------------------------ KIEM TRA
def kiem_khai_bao(spec: dict) -> list[str]:
    """Kiem CU PHAP truoc khi cham vao du lieu. Tra danh sach loi (rong = dat)."""
    loi = []
    if not isinstance(spec, dict):
        return ["khai bao khong phai dict"]
    for k in ("ten", "co_che", "ho", "vao"):
        if not spec.get(k):
            loi.append(f"thieu truong bat buoc '{k}'")
    if spec.get("ho") and spec["ho"] not in HO_HOP_LE:
        loi.append(f"ho '{spec['ho']}' khong thuoc {sorted(HO_HOP_LE)}")
    if len(str(spec.get("co_che", ""))) < 25:
        loi.append("'co_che' phai la MOT CAU giai thich vi sao co nguoi tra tien "
                   "cho phoi nhiem nay - man hinh duyet doc cau nay, khong doc tham so")
    if spec.get("chieu") not in (None, 1, -1):
        loi.append("'chieu' chi duoc la 1 hoac -1")
    giu = spec.get("giu", 1)
    if not isinstance(giu, int) or not (1 <= giu <= 500):
        loi.append("'giu' phai la so nguyen 1..500")
    for nhom in ("vao", "ra"):
        for i, d in enumerate(spec.get(nhom) or []):
            if isinstance(d, dict) and "vung" in d:
                loi += [f"{nhom}[{i}]: {e}" for e in _kiem_vung(d)]
                continue
            if not isinstance(d, dict) or "trai" not in d or "phai" not in d:
                loi.append(f"{nhom}[{i}] phai co 'trai' va 'phai'")
                continue
            if d.get("phep", ">") not in PHEP:
                loi.append(f"{nhom}[{i}] phep '{d.get('phep')}' khong hop le")
            for ben in ("trai", "phai"):
                loi += [f"{nhom}[{i}].{ben}: {e}" for e in _kiem_toan_hang(d[ben])]
            loi += [f"{nhom}[{i}]: {e}" for e in _kiem_hien_nhien(d)]
    return loi


def _kiem_vung(d: dict) -> list[str]:
    """Kiem CU PHAP mot ve `vung`. Xem `_vung` de biet hinh dang."""
    loi = []
    if d.get("quan_he", "cham") not in QUAN_HE_VUNG:
        loi.append("'quan_he' phai thuoc %s" % sorted(QUAN_HE_VUNG))
    kb = d.get("vung")
    if not isinstance(kb, dict):
        return loi + ["'vung' phai la dict"]
    if not kb.get("tao"):
        # Thieu `tao` thi vung sinh o MOI bar, va moi quan he thanh gan nhu
        # luon dung - dung hinh dang "ve luon dung im lang bien mat".
        loi.append("'vung.tao' rong - vung se sinh o moi bar")
    for k in ("tren", "duoi"):
        if k not in kb:
            loi.append("'vung' thieu bien '%s'" % k)
        else:
            loi += ["vung.%s: %s" % (k, e) for e in _kiem_toan_hang(kb[k])]
    for i, x in enumerate(kb.get("tao") or []):
        if not isinstance(x, dict) or "trai" not in x or "phai" not in x:
            loi.append("vung.tao[%d] phai co 'trai' va 'phai'" % i)
            continue
        if x.get("phep", ">") not in PHEP:
            loi.append("vung.tao[%d] phep '%s' khong hop le" % (i, x.get("phep")))
        for ben in ("trai", "phai"):
            loi += ["vung.tao[%d].%s: %s" % (i, ben, e)
                    for e in _kiem_toan_hang(x[ben])]
        loi += ["vung.tao[%d]: %s" % (i, e) for e in _kiem_hien_nhien(x)]
    s = kb.get("song", 20)
    if not isinstance(s, int) or isinstance(s, bool) or not (1 <= s <= 500):
        loi.append("'vung.song' phai la so nguyen 1..500")
    if kb.get("huy", "cham") not in HUY_VUNG:
        loi.append("'vung.huy' phai thuoc %s" % sorted(HUY_VUNG))
    return loi


#: Quan he LUON DUNG giua cac cot gia trong mot bar: `high` la chan tren,
#: `low` la chan duoi. Dung de bat dieu kien hien nhien.
_CHAN_TREN, _CHAN_DUOI = "high", "low"
_COT_GIA = ("open", "high", "low", "close")


def _kiem_hien_nhien(d: dict) -> list[str]:
    """Bat dieu kien LUON DUNG hoac LUON SAI - biet duoc ma khong can du lieu.

    VI SAO (do 06/09/2026). 110 co che bi cong loai voi ly do "suy bien tren
    MOI tai san do duoc", va khi mo ra thi khong cai nao la co che that bi mat:
    chung la `high > high`, `low > high`, `close >= low`, `close > close`,
    `tb(X) cheo_len tb(X)`. LLM sinh ra dieu kien vo nghia.

    Cong VAN loai dung, nhung no phai chay backtest tren BA tai san moi ket
    luan duoc - trong khi nhin vao khai bao la thay ngay. Chuyen 110 lan chay
    du lieu thanh 110 phep so chuoi la dung huong [[thong-luong-kiem-dinh]]:
    cat thoi gian kiem dinh, khong cat chat luong ket luan.

    Va quan trong hon toc do: ly do tu choi tro nen DUNG TEN. "Suy bien tren
    moi tai san" doc nhu mot phat hien ve thi truong; "hai ve giong het nhau"
    doc dung nhu no la - mot loi cua bo boc, sua duoc o bo boc.
    """
    trai, phai, phep = d.get("trai"), d.get("phai"), d.get("phep", ">")
    if not isinstance(trai, dict) or not isinstance(phai, dict):
        return []

    # GIA SO VOI MOT HANG SO <= 0. Gia la so DUONG NGAT tren moi tai san, nen
    # `close > 0` luon dung va `low < 0` khong bao gio dung - o ca hai chieu,
    # ve do khong quyet dinh gi.
    #
    # Do 06/09/2026: 27 ve nhu vay trong kho (`low < 0`, `high > 0`,
    # `close >= 0`) tren 12 co che, phan lon la ho FVG / order block /
    # liquidity sweep. Chung KHONG phai co che that bi mat, ma la dau vet cua
    # mot lan boc HONG: bo boc thay `if(cond) Buffer[i] = low[i] - 10*_Point;`
    # roi dien `hang: 0` vao cho nguong ma no khong doc duoc.
    #
    # Vi sao phai chan chu khong de pheu tu loc: ve LUON SAI thi pheu bat duoc
    # (`gan_khong_bao_gio_vao`), nhung ve LUON DUNG thi **im lang bien mat** -
    # co che van chay, van co ve co hai dieu kien, va ta khong bao gio biet
    # minh dang kiem dinh mot thu KHAC voi cai ban goc noi.
    if (str(trai.get("chi_bao", "")).lower() == "gia" and "hang" in phai
            and isinstance(phai.get("hang"), (int, float))
            and not isinstance(phai.get("hang"), bool)
            and float(phai["hang"]) <= 0.0):
        return ["gia luon DUONG nen 'gia %s %g' la hang so - nguong that da "
                "mat luc boc" % (phep, float(phai["hang"]))]

    try:
        gt, gp = (json.dumps(x, sort_keys=True, default=str) for x in (trai, phai))
    except Exception:
        return []
    if gt == gp:
        # `a > a` luon sai, `a >= a` luon dung, `a cheo_len a` khong bao gio.
        # Ca ba deu la mot dieu kien khong mang thong tin nao.
        return ["hai ve GIONG HET nhau - dieu kien khong mang thong tin"]

    # Chan tren / chan duoi trong cung mot bar.
    ct = str(trai.get("chi_bao", "")).lower()
    cp = str(phai.get("chi_bao", "")).lower()
    if ct != "gia" or cp != "gia" or "cua" in trai or "cua" in phai:
        return []
    a = str(trai.get("cot", "close")).lower()
    b = str(phai.get("cot", "close")).lower()
    if a not in _COT_GIA or b not in _COT_GIA:
        return []
    # Trong mot bar: `high` >= moi cot, `low` <= moi cot. Neu MOT trong hai
    # chieu da luon dung thi dieu kien suy bien voi MOI phep - ke ca `cheo_len`
    # / `cheo_xuong`, vi phep cheo doi mot bar TRUOC o chieu nguoc lai, ma
    # chieu nguoc lai thi khong bao gio xay ra.
    luon_lon = (a == _CHAN_TREN or b == _CHAN_DUOI)      # a >= b luon dung
    luon_nho = (a == _CHAN_DUOI or b == _CHAN_TREN)      # a <= b luon dung
    if luon_lon or luon_nho:
        quan_he = ">=" if luon_lon else "<="
        return [f"trong mot bar '{a}' {quan_he} '{b}' LUON dung, nen "
                f"'{a} {phep} {b}' khong mang thong tin"]
    return []


def _kiem_toan_hang(t, sau: int = 0) -> list[str]:
    if sau > 6:
        return ["toan hang long qua sau (> 6 tang)"]
    if not isinstance(t, dict):
        return ["toan hang phai la dict"]
    if "hang" in t:
        return [] if isinstance(t["hang"], (int, float)) else ["'hang' phai la so"]
    if "toan_hang" in t:
        ds = t["toan_hang"]
        if not isinstance(ds, list) or not ds:
            return ["'toan_hang' phai la danh sach khong rong"]
        if len(ds) > 24:
            return ["'toan_hang' qua 24 phan tu"]
        loi = []
        for x in ds:
            loi += _kiem_toan_hang(x, sau + 1)
        # `tuyen_tinh` doi `he_so` cung do dai. Thieu kiem o day thi loi chi lo
        # ra luc CHAM DU LIEU, tuc sau khi da tieu cong do backtest.
        if str(t.get("chi_bao", "")).lower() == "tuyen_tinh":
            hs = t.get("he_so")
            if not isinstance(hs, list) or len(hs) != len(ds):
                loi.append("'tuyen_tinh': 'he_so' phai la danh sach cung do dai "
                           "'toan_hang'")
            elif not all(isinstance(h, (int, float)) for h in hs):
                loi.append("'tuyen_tinh': moi 'he_so' phai la so")
        return loi
    # Toan tu CO NHO: kiem de quy cac dieu kien con, khong de loi lo ra luc
    # cham du lieu (sau khi da tieu cong backtest).
    cb0 = str(t.get("chi_bao", "")).lower()
    if cb0 == "trang_thai_lat":
        loi = []
        for k in ("len", "xuong"):
            d = t.get(k) or t.get("bat_" + k)
            if not isinstance(d, dict) or "trai" not in d or "phai" not in d:
                loi.append(f"'trang_thai_lat' can dieu kien '{k}' co trai/phai")
                continue
            if d.get("phep", ">") not in PHEP:
                loi.append(f"'trang_thai_lat.{k}': phep khong hop le")
            loi += _kiem_toan_hang(d["trai"], sau + 1)
            loi += _kiem_toan_hang(d["phai"], sau + 1)
        return loi
    if cb0 == "dem_lien_tiep":
        d = t.get("khi")
        if not isinstance(d, dict) or "trai" not in d or "phai" not in d:
            return ["'dem_lien_tiep' can dieu kien 'khi' co trai/phai"]
        loi = []
        if d.get("phep", ">") not in PHEP:
            loi.append("'dem_lien_tiep.khi': phep khong hop le")
        return loi + _kiem_toan_hang(d["trai"], sau + 1) +             _kiem_toan_hang(d["phai"], sau + 1)

    if "n" in t:
        try:
            n = int(t["n"])
        except Exception:
            return ["'n' phai la so nguyen"]
        if n < 0:
            # Chan duy nhat can thiet cho nhin truoc: moi cua so deu lui ve qua khu.
            return ["'n' AM = nhin ve tuong lai - khong phat bieu duoc trong ngu phap nay"]
        if n > 5000:
            return ["'n' > 5000 bar"]
    return _kiem_toan_hang(t["cua"], sau + 1) if "cua" in t else []


def kiem_khong_nhin_truoc(spec: dict, df: pd.DataFrame, k: int = 5) -> tuple[bool, str]:
    """Kiem THUC NGHIEM bang PHEP CAT: tin hieu tai bar t phai GIONG HET du ta
    co biet cac bar sau t hay khong.

    Kiem cu phap da chan `n` am, nhung mot chi bao moi them sau nay co the lam
    ro ri ma cu phap khong thay. Bai kiem nay khong phu thuoc vao danh sach
    chi bao - no do TRIEU CHUNG, khong do nguyen nhan.

    Hai cach lam nhieu DA THU VA DA TRUOT truoc khi den cach nay (16/08), giu
    lai day vi ca hai deu "co ve dung":
      1. Nhan bon cot cua bar cuoi voi 1,5 - IBS la TY LE trong bar nen nhan deu
         ca bon cot khong lam IBS doi mot ly nao. Bay khong he rung.
      2. Pha hinh dang 5 bar cuoi - chi ~5 bar bi anh huong, va neu dieu kien
         thu hai cua co che tinh co sai o dung may bar do thi tin hieu khong
         doi, bay van khong rung. Do nhay phu thuoc vao du lieu = khong dung duoc.
    Phep CAT thi khong the truot: neu tin hieu dung point-in-time thi hai ben
    bang nhau THEO DINH NGHIA; lech mot moc la du ket toi.
    """
    if len(df) < 300:
        return True, "khong du bar de kiem"
    day_du = sinh_tu_spec(spec, df)
    rng = np.random.default_rng(20260816)
    lo_, hi_ = len(df) // 3, len(df) - 2
    diem = set(int(x) for x in rng.integers(lo_, hi_, size=40))

    # LAY MAU O CHO CO CHUYEN DONG, khong chi lay ngau nhien.
    #
    # Do 06/09/2026 khi dung nguyen thuy `vung` lam canary: mot ban RO RI CO Y
    # (bien vung lay `low` cua bar KE TIEP) lam lech tin hieu o **16/400 bar**,
    # nhung 40 moc ngau nhien voi hat giong co dinh khong trung moc nao trong
    # 16 do -> bo do bao "dat". Bay khong rung truoc mot ro ri that.
    #
    # Nguyen nhan khong phai xui: co che thua (kich hoat 2,75% so bar) thi moc
    # ngau nhien gan nhu luon roi vao bar tin hieu BANG 0, va o bar do hai ban
    # bang nhau du co ro ri hay khong. Tuc **luc cua bo do ti le voi tan suat
    # kich hoat** - dung o lop co che thua nhat, no yeu nhat.
    #
    # Sua: uu tien moc noi tin hieu KHAC 0 va moc no vua DOI GIA TRI. Do la cho
    # duy nhat mot ro ri co the lo ra. Van giu moc ngau nhien de khong bo sot
    # ro ri chi hien o bar im lang.
    kh = np.abs(np.asarray(day_du, dtype=float)) > 1e-12
    doi = np.zeros(len(df), dtype=bool)
    doi[1:] = kh[1:] != kh[:-1]
    dang_quan_tam = np.flatnonzero((kh | doi))
    dang_quan_tam = dang_quan_tam[(dang_quan_tam >= lo_) & (dang_quan_tam < hi_)]
    if dang_quan_tam.size:
        lay = min(40, dang_quan_tam.size)
        diem |= set(int(x) for x in
                    rng.choice(dang_quan_tam, size=lay, replace=False))
    diem = sorted(diem)
    lech, vi_du = 0, []
    for t in diem:
        cat = sinh_tu_spec(spec, df.iloc[: t + 1])       # chi biet den bar t
        if abs(float(cat[-1]) - float(day_du[t])) > 1e-12:
            lech += 1
            if len(vi_du) < 3:
                vi_du.append(f"bar {t} ({str(df.index[t])[:16]}): "
                             f"cat={float(cat[-1]):+.3f} vs day_du={float(day_du[t]):+.3f}")
    if lech:
        return False, (f"{lech}/{len(diem)} moc: tin hieu tai bar t DOI khi biet them "
                       "bar sau t - co NHIN TRUOC. " + " | ".join(vi_du))
    return True, f"dat ({len(diem)} moc cat)"


# ------------------------------------------------------------------ SINH
def sinh_tu_spec(spec: dict, df: pd.DataFrame) -> np.ndarray:
    """Khai bao -> `tin_hieu[i]` = phoi nhiem mong muon biet tai close[i]."""
    chieu = float(spec.get("chieu", 1) or 1)
    giu = int(spec.get("giu", 1) or 1)
    vao = _dieu_kien(df, spec.get("vao") or [], mac_dinh=False)
    ra = _dieu_kien(df, spec.get("ra") or [], mac_dinh=False)

    v = vao.astype(float)
    if giu > 1:
        v = v.rolling(giu, min_periods=1).max()
    if (spec.get("ra") or []):
        # co dieu kien ra tuong minh: giu vi the tu luc VAO cho toi luc RA
        trang_thai = np.zeros(len(df))
        dang = 0.0
        vao_a, ra_a = vao.to_numpy(), ra.to_numpy()
        for i in range(len(df)):
            if dang and ra_a[i]:
                dang = 0.0
            elif vao_a[i]:
                dang = 1.0
            trang_thai[i] = dang
        v = pd.Series(trang_thai, index=df.index)
    return MAU_MOD._ra(v.to_numpy() * chieu, len(df))


# --------------------------------------------------------------- KHO CO CHE
_XAU = __import__("re").compile(r"[^a-z0-9_]+")


def chuan_hoa_ten(ten: str) -> str:
    """Ten co che -> chi con [a-z0-9_]. Xem ly do o `them_co_che`."""
    import unicodedata
    t = unicodedata.normalize("NFKD", str(ten or "").strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = _XAU.sub("_", t).strip("_")
    while "__" in t:
        t = t.replace("__", "_")
    return t[:60]


class KhoDocHong(RuntimeError):
    """File kho CO nhung doc khong ra. Khac han voi kho RONG.

    Ten loai nay ton tai vi mot ly do cu the: xem `doc_kho`.
    """


def doc_kho(cho_rong_khi_hong: bool = False) -> list[dict]:
    """Doc kho co che.

    ## VI SAO HAM NAY KHONG DUOC NUOT LOI - chuyen 13/09/2026

    Kho tut tu **2.741 co che xuong 130** trong mot buoi sang, va lan nay chot
    chong teo cua `luu_kho` KHONG chan duoc. Duong di cua loi:

        doc_kho()  gap loi doc  ->  `except Exception: return []`
        them_co_che: ds = doc_kho() = []  ->  ds.append(spec)
        luu_kho([spec]): `cu = len(doc_kho())` cung = 0
                         chot la `if not ep and cu and moi < cu*0.8`
                         -> `cu` bang 0 nen menh de TAT, chot khong chay
        ghi de 2.741 co che bang 1

    Mot lan doc hong la du. Va hom do may dang nghet bo nho (mot bo test 8
    tien trinh bao `paging file too small`), nen `json.loads` tren file 2,1 MB
    hoan toan co the nem `MemoryError` - ma `MemoryError` LA mot `Exception`.

    Day dung la ho loi ma ca du an nay da gap nhieu lan duoi mot ten khac:
    **khau doc hong doc y het mot ket qua rong**. Nen o day phan biet ba
    truong hop, khong phai hai:

        file khong ton tai        -> kho rong THAT, tra []
        file ton tai, doc duoc    -> tra noi dung
        file ton tai, doc KHONG   -> NEM `KhoDocHong`, khong bao gio tra []

    `cho_rong_khi_hong=True` chi danh cho cho nao that su can mot con so de
    hien thi (bang trang thai), khong bao gio cho duong GHI.
    """
    if not KHO_CO_CHE.exists():
        return []
    try:
        d = json.loads(KHO_CO_CHE.read_text(encoding="utf-8-sig"))
    except Exception as e:
        if cho_rong_khi_hong:
            return []
        raise KhoDocHong(
            "kho %s CO (%d byte) nhung doc khong ra: %s. KHONG duoc coi day la "
            "kho rong - mot lan ghi sau do se xoa sach kho."
            % (KHO_CO_CHE.name, KHO_CO_CHE.stat().st_size, repr(e)[:150])) from e
    if not isinstance(d, list):
        raise KhoDocHong("kho khong phai mot danh sach: %s" % type(d).__name__)
    return d


#: Bao nhieu phan tram kho duoc phep BIEN MAT trong mot lan ghi. Vuot nguong
#: nay thi tu choi ghi - gan nhu chac chan la mot lan doc-sua-ghi bi chen ngang.
NGUONG_HAO_HUT = 0.20

import shutil as _shutil  # noqa: E402

#: MOC CAO NHAT kho tung dat. Chot hao hut so voi moc nay chu khong chi so voi
#: lan ghi truoc - neu khong thi bao mon tung buoc nho luon lot qua.
MOC_CAO = KHO_CO_CHE.with_suffix(".moc_cao")


def _doc_moc_cao() -> int:
    try:
        return int(MOC_CAO.read_text(encoding="utf-8").strip())
    except Exception:
        return 0


def _ghi_moc_cao(n: int) -> None:
    try:
        MOC_CAO.write_text(str(int(n)), encoding="utf-8")
    except Exception:
        pass


class KhoBiTeoLai(RuntimeError):
    """Mot lan ghi lam kho nho di dot ngot. Ten loai co y: day khong phai loi
    cua co che nao, day la mat du lieu."""


def luu_kho(ds: list[dict], ep: bool = False) -> None:
    """Ghi kho co che. CO KHOA va CO CHOT CHONG TEO.

    ## Chuyen da xay ra that, 23:48 ngay 11/09/2026

    Kho tut tu **1.149 co che xuong 3** trong vai phut, va khong mot dong log
    nao bao. Nguyen nhan: `doc_kho()` -> sua -> `luu_kho()` la mot chuoi
    DOC-SUA-GHI khong khoa. Khi chu du an cho toan bo CPU va `q ultra` chay 3
    tien trinh boc LLM dong thoi, moi tien trinh doc kho, them co che cua no,
    roi ghi de len - **nguoi ghi cuoi cung thang, va vut het phan cua nhung
    nguoi kia**. Mot tien trinh doc phai trang thai som se ghi lai mot danh
    sach ti hon.

    Va toi da COMMIT dung trang thai hong do (`fa6a4e1`, 3 co che) truoc khi
    phat hien. Cuu duoc nho git con ban `c56034c` (1.149).

    ## Hai lop chan

    1. **Khoa file** quanh ca chuoi doc-sua-ghi -> `voi_khoa()`.
    2. **Chot chong teo**: tu choi mot lan ghi lam kho mat hon 20%. Khoa co the
       hong (tien trinh bi giet giua chung); chot nay thi khong phu thuoc gi.
       Muon ghi nho that (don kho) thi phai noi ro `ep=True`.
    """
    KHO_CO_CHE.parent.mkdir(parents=True, exist_ok=True)
    moi = len(ds or [])

    # CHOT 0 - CON CHO GHI KHONG.
    #
    # Them 13/09/2026 sau khi kho bi ghi de HAI lan trong mot buoi. Nguyen nhan
    # chung cua ca hai: o C tut ve 233 MB, pytest 6 nhan chet voi `paging file
    # too small`, va mot lan ghi khong tron ven doc y het mot kho rong. Xem
    # `nhan/dia.py` - het dia khong hien ra nhu loi dia.
    from nhan import dia as _DIA
    _DIA.du_cho(_DIA.NGUONG_KHO_GB, "ghi kho co che", KHO_CO_CHE.parent)

    # CHOT 1 - DOC PHAI THANH CONG TRUOC KHI GHI.
    #
    # Truoc 13/09 day la `cu = len(doc_kho())` voi `doc_kho` nuot moi loi. Mot
    # lan doc hong -> `cu = 0` -> chot duoi TAT (vi no doi `cu` khac 0) -> ghi
    # de ca kho. Xem ghi chu day du trong `doc_kho`.
    cu = len(doc_kho())          # nem KhoDocHong neu file co ma doc khong ra

    # CHOT 2 - MOC CAO NHAT, khong chi lan ghi truoc.
    #
    # Chot ty le 20% chi so voi LAN NGAY TRUOC, nen mot chuoi ghi moi lan nho
    # di 19% van bao mon ca kho ma khong lan nao bi chan: 2.741 -> 130 chi can
    # 15 buoc. Moc cao nhat lam cho bao mon dan cung bi chan.
    moc = _doc_moc_cao()
    nen = max(cu, moc)
    if not ep and nen and moi < nen * (1 - NGUONG_HAO_HUT):
        raise KhoBiTeoLai(
            f"tu choi ghi: kho {cu} -> {moi} co che (moc cao nhat tung thay "
            f"{moc}; mat {nen - moi}, {(nen - moi) / nen:.0%}). Gan nhu chac "
            f"chan la mot lan doc-sua-ghi bi chen ngang, hoac mot lan doc hong. "
            f"Muon ghi nho that thi goi luu_kho(ds, ep=True).")

    # CHOT 3 - BAN LUI MOT BUOC. Khoa va chot deu co the bi vuot (vd `ep=True`
    # dung sai); mot ban sao cua trang thai TRUOC lan ghi thi khong.
    if cu and KHO_CO_CHE.exists():
        try:
            _shutil.copy2(KHO_CO_CHE, KHO_CO_CHE.with_suffix(".json.lui"))
        except Exception:
            pass

    # CHOT 3 - SPEC HONG KHONG DUOC VAO KHO IM LANG.
    #
    # `kiem_khai_bao` la cong cua ngu phap, nhung truoc 14/09/2026 `luu_kho`
    # khong he goi no. Hau qua: spec hong ghi vao kho BINH THUONG, roi den luc
    # chay tester moi bi loc ra - va thu nguoi doc nhan duoc chi la mot con so
    # nho hon mong doi, khong mot loi giai thich.
    #
    # Do 14/09: **44/3233 co che trong kho khong qua cong**, bi vut moi luot
    # chay tester suot nhieu ngay ma khong ai biet. Chinh toi cung sap dung bay:
    # them 5 spec voi `ho="hoi_quy"` (khong thuoc danh sach hop le), tester bao
    # "dich duoc 1" thay vi 6, va neu khong tinh co dem lai so co che thi da
    # chay tester tren MOT he roi tuong la ket qua cua ca ba.
    #
    # Khong TU CHOI ghi - kho dang co 44 cai hong tu truoc, tu choi la lam do ca
    # nhung duong ghi hop le khac. Nhung phai KEU TO, va phai keu dung cai moi.
    try:
        hong_moi = [(x.get("ten", "?"), kiem_khai_bao(x)) for x in (ds or [])]
        hong_moi = [(t, l) for t, l in hong_moi if l]
    except Exception:
        hong_moi = []
    if hong_moi:
        import sys as _sys
        print("[luu_kho] CANH BAO: %d/%d spec KHONG qua `kiem_khai_bao` - chung "
              "se bi loc bo im lang o moi luot chay tester:" % (len(hong_moi), len(ds or [])),
              file=_sys.stderr)
        for t, l in hong_moi[:8]:
            print("            %-44s %s" % (str(t)[:44], str(l[0])[:70]), file=_sys.stderr)

    # TEN FILE TAM PHAI MANG PID (sua 16/09).
    #
    # `.json.tam` co dinh: me boc 374 file chay `LUONG = 6` luong, va moi luong
    # goi den day. Hai luong ghi cung luc thi ca hai cung ghi vao dung mot file
    # tam roi ca hai cung `replace` - ban ra co the la mot ban LAI cua hai kho.
    # Kho nay dang giu 4.049 co che; mot ban lai khong bao loi, no chi lam kho
    # tut so muc, va `_ghi_nhat_ky_ghi` ben duoi moi la thu phat hien ra.
    #
    # Khong dung `ghi_an_toan.sua_json` o day: ham nay da tu gom `ds` day du
    # trong bo nho tu truoc do, tuc no GHI DE co chu dich chu khong doc-sua-ghi.
    # Chi can ten tam rieng cho moi tien trinh.
    import os as _os
    tam = KHO_CO_CHE.with_suffix(".json.tam%d" % _os.getpid())
    tam.write_text(json.dumps(ds, ensure_ascii=False, indent=1), encoding="utf-8")
    tam.replace(KHO_CO_CHE)      # thay the NGUYEN TU, khong de lai file nua voi
    _ghi_moc_cao(max(moi, moc))
    if moi < cu:
        _ghi_nhat_ky_ghi(cu, moi, ep)


#: Nhat ky MOI lan ghi lam kho NHO DI, kem vet goi.
#:
#: Vi sao can: 13/09/2026 kho bi xoa HAI lan trong mot buoi. Lan mot truy ra
#: duoc nguyen nhan (`doc_kho` nuot loi). Lan hai thi khong - chot da chac,
#: khong test nao ghi thang vao file, khong cho nao goi `ep=True`, va van mat.
#: Suy luan tu ma nguon het duong; can mot vet goi THAT.
#:
#: Ghi noi tiep, khong bao gio xoa. File nay nho (chi ghi khi kho nho di) va
#: no la thu duy nhat tra loi duoc "ai da ghi" sau khi su viec xay ra.
NHAT_KY_GHI = KHO_CO_CHE.parent.parent / "nhat_ky" / "kho_co_che_ghi.log"


def _ghi_nhat_ky_ghi(cu: int, moi: int, ep: bool) -> None:
    import traceback
    try:
        NHAT_KY_GHI.parent.mkdir(parents=True, exist_ok=True)
        vet = "".join(traceback.format_stack(limit=14)[:-1])
        with NHAT_KY_GHI.open("a", encoding="utf-8") as f:
            f.write("\n=== %s | pid %d | %d -> %d co che | ep=%s ===\n%s"
                    % (time.strftime("%Y-%m-%d %H:%M:%S"), os.getpid(),
                       cu, moi, ep, vet))
    except Exception:
        pass


@contextmanager
def voi_khoa(cho_giay: float = 120.0, nhip: float = 0.25):
    """Khoa quanh ca chuoi DOC-SUA-GHI kho co che.

        with NP.voi_khoa():
            ds = NP.doc_kho(); ds.append(spec); NP.luu_kho(ds)

    Khoa theo FILE (ba tien trinh khong nhin thay bien cua nhau), tu thu hoi
    khi chu giu da chet hoac qua 5 phut.
    """
    khoa = KHO_CO_CHE.with_suffix(".khoa")
    het = time.time() + cho_giay
    while True:
        try:
            fd = os.open(str(khoa), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                cu = float(khoa.stat().st_mtime)
                if time.time() - cu > 300:      # khoa mo coi
                    khoa.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            if time.time() >= het:
                raise KhoBiTeoLai(
                    "khong lay duoc khoa kho co che sau %.0fs - co tien trinh "
                    "khac dang ghi. Xoa %s neu chac khong con ai ghi."
                    % (cho_giay, khoa.name))
            time.sleep(nhip)
    try:
        yield
    finally:
        khoa.unlink(missing_ok=True)


def van_tay_dieu_kien(spec: dict) -> str:
    """Van tay theo NOI DUNG QUYET DINH, bo qua ten va cau giai thich.

    Hai co che cung `vao`/`ra`/`chieu`/`giu` la MOT co che du dat ten khac nhau -
    va do la truong hop pho bien khi rut tu dong tu nhieu nguon noi ve cung mot
    y tuong.
    """
    return json.dumps({"vao": spec.get("vao"), "ra": spec.get("ra"),
                       "chieu": spec.get("chieu", 1), "giu": spec.get("giu", 1)},
                      sort_keys=True, ensure_ascii=False, default=str)


#: Tai san DO THEM khi bai kich hoat truot tren chuoi kiem chinh.
#:
#: VI SAO (lo hong tim ra 06/09/2026). Cong nay tu choi mot co che khi no kich
#: hoat < 0,2% so bar — nhung no chi do tren MOT chuoi: `XM_US100CASH H1`
#: (`loc_co_che.MA_KIEM`). Tin hieu mui ten, tin hieu theo phien, tin hieu cua
#: ho tien te von la SU KIEN HIEM tren mot chi so My va day du tren tai san
#: khac. Luat "chi loai khi suy bien tren TAT CA tai san" da duoc viet cho
#: `loc_co_che` (xem docstring "KHONG DUOC KET LUAN TREN MOT TAI SAN") nhung
#: QUEN ap cho cua vao kho, la cho no can nhat: o `loc_co_che` co che bi bo qua
#: mot vong quet, o day no bi nem di han.
#:
#: Khac LOP nhau co chu dich: mot hang hoa, mot cap tien. Cong chi tu choi khi
#: co che suy bien tren ca ba.
MA_DO_THEM = (("XAUUSD", "H1"), ("EURUSD", "H1"))

#: Nguong kich hoat cua CUA VAO KHO. Long hon `loc_co_che.TY_LE_IT` (0,005) co
#: chu dich: cua vao kho chi chan cai KHONG THE kiem dinh duoc, con viec chon
#: cai dang chay la cua bo loc tinh phia sau.
TY_LE_IT_KHO, TY_LE_NHIEU_KHO = 0.002, 0.98

_CHUOI_DO_THEM: dict = {}


def _chuoi_do_them() -> list[tuple[str, "pd.DataFrame"]]:
    """Nap (mot lan) cac chuoi do them. Rong neu khong nap duoc — va cai rong
    do duoc PHAN BIET voi "da do va suy bien" o ly do tu choi."""
    if not _CHUOI_DO_THEM:
        ds = []
        try:
            from nhan import du_lieu as DL
            for ma, khung in MA_DO_THEM:
                try:
                    ds.append((f"{ma} {khung}", DL.hai_nua(DL.nap(ma, khung), 0.6)[0]))
                except Exception:
                    continue
        except Exception:
            pass
        _CHUOI_DO_THEM["ds"] = ds
    return _CHUOI_DO_THEM.get("ds") or []


def _ty_le_kich_hoat(spec: dict, df: "pd.DataFrame") -> float | None:
    """Ty le bar co tin hieu. `None` = KHONG DO DUOC tren chuoi nay."""
    try:
        th = sinh_tu_spec(spec, df)
    except Exception:
        return None
    return float(np.mean(np.abs(th) > 1e-12))


def _kich_hoat_dat(ty_le: float) -> bool:
    return TY_LE_IT_KHO <= ty_le <= TY_LE_NHIEU_KHO


def them_co_che(spec: dict, df_kiem: pd.DataFrame | None = None) -> dict:
    """Them mot co che vao kho SAU KHI qua ca hai bai kiem.

    Khong dat -> KHONG vao kho, va tra ly do de tang suy nghi hoc duoc tu no.

    CHAY TRONG KHOA (tu 12/09/2026). Ham nay doc kho, sua, roi ghi lai - mot
    chuoi DOC-SUA-GHI. Khi nhieu tien trinh boc chay dong thoi, nguoi ghi cuoi
    cung vut het phan cua nhung nguoi kia: kho tut 1.149 -> 3 co che trong vai
    phut, khong mot dong log nao bao. Xem `luu_kho`.
    """
    with voi_khoa():
        return _them_co_che_trong_khoa(spec, df_kiem)


def _them_co_che_trong_khoa(spec: dict,
                            df_kiem: pd.DataFrame | None = None) -> dict:
    # Chuan hoa TEN truoc moi thu. Ten di thang vao `gia_thuyet.ma` duoi dang
    # `{tai_san}.{khung}.{ten}.{tham_so}`, va sau do bi tim lai bang LIKE
    # '%.{ten}.%'. Mot cai ten nhu `sma2_cat_keo_(nhanh_tren_cham)` (tang BOC
    # sinh ra that 16/08) lam hong ca hai: dau cham/ngoac trong ten pha cach
    # tach, con `%` `_` la ky tu dai dien cua LIKE.
    spec = dict(spec)
    spec["ten"] = chuan_hoa_ten(spec.get("ten", ""))
    if not spec["ten"]:
        return {"nhan": False, "ly_do": ["ten rong sau khi chuan hoa"]}

    loi = kiem_khai_bao(spec)
    if loi:
        return {"nhan": False, "ly_do": loi[:6]}
    if df_kiem is not None:
        try:
            th = sinh_tu_spec(spec, df_kiem)
        except Exception as e:
            return {"nhan": False, "ly_do": [f"chay loi: {type(e).__name__}: {str(e)[:120]}"]}
        ty_le = float(np.mean(np.abs(th) > 1e-12))
        do_tren = "chuoi kiem"
        if not _kich_hoat_dat(ty_le):
            # KHONG LOAI THEO MOT TAI SAN. Do lai tren tai san khac lop; chi tu
            # choi khi suy bien tren TAT CA cho do duoc.
            da_do = [f"chuoi kiem {ty_le:.3%}"]
            chua_do = []
            # DO HET, KHONG DUNG O CHUOI DAU TIEN DAT.
            #
            # Ban cu `break` ngay khi mot chuoi dat, nen spec chi mang ve MOT
            # con so - va do la con so cua chuoi MAY MAN. `ty_le_than_nen`
            # (`close - open > 0.5`, tuc mot hang so DON VI GIA) vao kho voi
            # `_ty_le_kich_hoat = 0,5202` do tren XAUUSD, trong khi tren moi cap
            # FX no la **0,000** - va nam thang sau no van ra 0 lenh moi luot
            # tester, moi lan chi hien ra la mot dong 0 lan giua cac dong that.
            # Do them mot chuoi ton vai chuc mili giay; giu ca bang thi cau hoi
            # "co che nay song o dau" tra loi duoc bat cu luc nao sau do.
            # Xem `nhan/thang_gia.py`.
            theo_chuoi = {"chuoi kiem": round(ty_le, 4)}
            for ten_ma, df_them in _chuoi_do_them():
                tl2 = _ty_le_kich_hoat(spec, df_them)
                if tl2 is None:
                    chua_do.append(ten_ma)
                    continue
                da_do.append(f"{ten_ma} {tl2:.3%}")
                theo_chuoi[ten_ma] = round(tl2, 4)
                if _kich_hoat_dat(tl2) and not _kich_hoat_dat(ty_le):
                    ty_le, do_tren = tl2, ten_ma
            spec = dict(spec, _ty_le_theo_chuoi=theo_chuoi)
            if not _kich_hoat_dat(ty_le):
                huong = ("mua-giu tra hinh" if ty_le > TY_LE_NHIEU_KHO
                         else "khong du lenh de kiem dinh bao gio")
                ly = f"suy bien tren MOI tai san do duoc ({', '.join(da_do)}) - {huong}"
                if chua_do:
                    ly += f" [CHUA DO: {', '.join(chua_do)}]"
                return {"nhan": False, "ly_do": [ly]}
        sach, mo_ta = kiem_khong_nhin_truoc(spec, df_kiem)
        if not sach:
            return {"nhan": False, "ly_do": [mo_ta]}
        spec = dict(spec, _ty_le_kich_hoat=round(ty_le, 4), _do_tren=do_tren)

    kho = doc_kho()
    if any(c.get("ten") == spec["ten"] for c in kho):
        return {"nhan": False, "ly_do": [f"da co co che ten '{spec['ten']}'"]}
    # KHU TRUNG THEO DIEU KIEN, khong chi theo TEN.
    #
    # Do that 01/09: mot lo tu dong dua thu vien tu 29 len 146 co che, nhung chi
    # **81 dieu kien rieng biet** - 65 cai trung y het nhau va chi khac ten, vi
    # cung mot script duoc xu ly hai lan (mot lan luc thu thap, mot lan luc quet
    # lai kho) nen sinh ra `x_...` va `pine_x_...`. Khu trung theo ten khong bat
    # duoc, va moi ban trung se an MOT SUAT FDR rieng o tang kham pha.
    vt = van_tay_dieu_kien(spec)
    trung = next((c for c in kho if van_tay_dieu_kien(c) == vt), None)
    if trung is not None:
        return {"nhan": False,
                "ly_do": [f"trung DIEU KIEN voi co che '{trung.get('ten')}' "
                          "(chi khac ten) - mot dieu kien chi duoc mot suat FDR"]}
    kho.append(spec)
    luu_kho(kho)
    return {"nhan": True, "ten": spec["ten"], "so_co_che": len(kho)}


# ------------------------------------------------- THAM SO CHON TRONG SPEC
#: Cac khoa mang GIA TRI SO co the chinh duoc trong mot khai bao DSL.
#: `n`  = do dai cua so nhin lai. `hang` = nguong so sanh.
#: `song` = tuoi tho cua mot VUNG (them 06/09/2026). Do la nut van tu nhien cua
#: ho FVG/order block - "gap nay con hieu luc bao lau" - va neu khong liet ke o
#: day thi `do_on_dinh.lan_can` se do lan can cua mot vung MA KHONG BAO GIO DOI
#: tuoi tho no, roi ket luan "cao nguyen" [[doi-tham-so-ma-khong-doi-ket-qua]].
KHOA_CHINH_DUOC = ("n", "hang", "song")


def _di_spec(nut, duong: str, ra: dict) -> None:
    """Di sau vao cay spec, gom moi hang so chinh duoc kem DUONG DAN cua no."""
    if isinstance(nut, dict):
        for k, v in nut.items():
            if k in KHOA_CHINH_DUOC and isinstance(v, (int, float))                     and not isinstance(v, bool):
                ra[f"{duong}_{k}" if duong else k] = v
            else:
                _di_spec(v, f"{duong}_{k}" if duong else str(k), ra)
    elif isinstance(nut, list):
        for i, v in enumerate(nut):
            _di_spec(v, f"{duong}{i}", ra)


def tham_so_cua(spec: dict) -> dict:
    """Phoi bay cac hang so CHON DUOC cua mot khai bao DSL thanh dict PHANG.

    VI SAO CAN (loi tim ra 03/09/2026). `do_on_dinh.lan_can()` — bo may tra
    loi "cao nguyen hay cai gai" — nhan mot dict tham so phang. 152 co che DSL
    trong kho co `luoi = [{}]` va closure cua chung la:

        def _ham(df, _s=spec, **_):   # <- `**_` NUOT SACH moi tham so
            return sinh_tu_spec(_s, df)

    Nen neu ai chay `b on-dinh` len mot co che DSL: `lan_can` sinh du 81 o,
    ca 81 o goi cung mot ham voi cung mot spec, tra ve **ket qua y het nhau**,
    va bo do hinh dang ket luan "CAO NGUYEN - 100% lan can duong, do doc 0%"
    cho mot co che **chua he duoc doi tham so lan nao**. Mot phan quyet on
    dinh gia mao, im lang, theo dung huong lam ta tin tuong.

    Ten khoa la DUONG DAN trong cay, vd `vao0_trai_n`, `vao0_phai_hang`,
    cong `giu` o muc goc. Dung `ap_tham_so` de dat nguoc vao.
    """
    ra: dict = {}
    for phan in ("vao", "ra"):
        _di_spec(spec.get(phan) or [], phan, ra)
    giu = spec.get("giu")
    if isinstance(giu, int) and not isinstance(giu, bool) and giu >= 1:
        ra["giu"] = giu
    return ra


def ap_tham_so(spec: dict, ts: dict) -> dict:
    """Ban SAO cua `spec` voi cac hang so thay bang gia tri trong `ts`."""
    if not ts:
        return spec
    moi = copy.deepcopy(spec)
    for khoa, gt in ts.items():
        if khoa == "giu":
            moi["giu"] = int(gt)
            continue
        nut, duong = None, khoa
        for phan in ("vao", "ra"):
            if khoa.startswith(phan):
                nut, duong = moi.get(phan) or [], khoa[len(phan):]
                break
        if nut is None:
            continue
        _dat(nut, duong, gt)
    return moi


def _tach_chi_so(buoc: str) -> tuple[str, int | None]:
    """`'tao0'` -> `('tao', 0)`. `'trai'` -> `('trai', None)`.

    VI SAO (loi tim ra 06/09/2026 khi them nguyen thuy `vung`). `_di_spec` noi
    chi so cua danh sach vao duong dan MA KHONG CO DAU PHAN CACH
    (`f"{duong}{i}"`), va `_dat` thi tach duong bang `split("_")`. Voi mot danh
    sach o TANG GOC (`vao`, `ra`) khong sao: chi so thanh token dau tien
    (`"0_trai_n"`). Nhung mot danh sach LONG BEN TRONG - `vung.tao` - cho ra
    token dinh lien `"tao0"`, ma `"tao0"` khong phai khoa cua dict nao, nen
    `_dat` lang le `return` va tham so KHONG DUOC DAT.

    Trieu chung neu khong sua: `tham_so_cua` van LIET KE `vao0_vung_tao0_phai_n`
    nen bo do on dinh tuong minh dang doi tham so, con `ap_tham_so` thi tra ve
    spec Y HET. Do dung la hinh dang "doi tham so ma khong doi ket qua" da lam
    ca mot phan quyet CAO NGUYEN gia hoi 03/09
    [[doi-tham-so-ma-khong-doi-ket-qua]].
    """
    i = len(buoc)
    while i > 0 and buoc[i - 1].isdigit():
        i -= 1
    if i == 0 or i == len(buoc):
        return buoc, None
    return buoc[:i], int(buoc[i:])


def _dat(nut, duong: str, gt) -> None:
    """Dat `gt` vao vi tri `duong` (dang `0_trai_n`) trong cay `nut`."""
    phan = duong.split("_")
    cuoi = phan[-1]
    cur = nut
    for buoc in phan[:-1]:
        if buoc == "":
            continue
        if isinstance(cur, dict) and buoc not in cur:
            # Token dinh lien kieu `tao0` - xem `_tach_chi_so`.
            k, idx = _tach_chi_so(buoc)
            if idx is None or k not in cur or not isinstance(cur[k], list):
                return
            if idx >= len(cur[k]):
                return
            cur = cur[k][idx]
            continue
        if isinstance(cur, list):
            i = int(buoc)
            if i >= len(cur):
                return
            cur = cur[i]
        elif isinstance(cur, dict):
            if buoc not in cur:
                return
            cur = cur[buoc]
        else:
            return
    if isinstance(cur, dict) and cuoi in cur:
        cur[cuoi] = type(cur[cuoi])(gt) if isinstance(cur[cuoi], int)             and not isinstance(cur[cuoi], bool) else gt


#: Muc bi `nap_vao_mau` tu choi o lan nap gan nhat: {ten: ly_do}.
#:
#: Phai GIU LAI chu khong duoc vut: mot muc bi tu choi im lang thi khong ai
#: biet kho vua nho di, va con so "540 co che" van duoc doc nhu 540 phep thu.
#: `loc_co_che.loc` doc bien nay de bao ra dung ten benh.
BI_TU_CHOI_KHI_NAP: dict = {}


def nap_vao_mau(kiem_cong: bool = True) -> int:
    """Dua co che trong kho vao `MAU.MAU` de QUANTLAB quet nhu mau goc.

    Diem cot yeu: co che tu hoc KHONG co duong tat nao. No di qua dung engine,
    dung cong, dung ngan sach FDR nhu mau viet tay.

    `kiem_cong=True` (mac dinh, tu 06/09/2026): CHAN o cua nay luon.

    VI SAO CHUYEN CONG VE DAY. Ngay 06/09 cong `kiem_khai_bao` duoc ap o
    `loc_co_che.loc` va cat 125 muc khoi be mat. Nhung `loc()` khong phai cua
    duy nhat: `do_on_dinh`, `hinh_dang_vs_null`, `cham_lai_the_he`,
    `ngoai_sinh`, `p_null_vs_ung_vien` deu goi thang `nap_vao_mau` roi doc
    `MAU.MAU`. Tuc mot co che khong co truong `co_che` van duoc CHAM LAI diem,
    van duoc do lan can "cao nguyen hay cai gai", van duoc dem trong nha may
    null - chi khong len be mat.

    Chan o hai cho voi hai danh sach thi som muon se lech nhau. Cong phai nam
    o CUA, va cua la day: `MAU.MAU` khong duoc chua thu ma cong tu choi.
    [[cong-chua-ap-cho-hang-trong-kho]]

    `kiem_cong=False` chi danh cho phep DO DAC ve chinh cai kho (dem xem co bao
    nhieu muc hong), khong danh cho duong chay nghien cuu nao.
    """
    them = 0
    BI_TU_CHOI_KHI_NAP.clear()
    for spec in doc_kho():
        ten = spec.get("ten")
        if not ten or ten in MAU_MOD.MAU:
            continue
        if kiem_cong:
            loi = kiem_khai_bao(spec)
            if loi:
                BI_TU_CHOI_KHI_NAP[ten] = loi[0]
                continue

        def _ham(df, _s=spec, **ts):
            # Truoc 03/09/2026 cho nay la `**_` (nuot sach). Xem `tham_so_cua`.
            return sinh_tu_spec(ap_tham_so(_s, ts) if ts else _s, df)

        tam = tham_so_cua(spec)
        MAU_MOD.MAU[ten] = {
            "ham": _ham, "ho": spec.get("ho", "khac"),
            "co_che": spec.get("co_che", ""),
            "nguon": spec.get("nguon", "ngu_phap"),
            "luoi": spec.get("luoi") or ([tam] if tam else [{}]),
            "tham_so_tam": tam,
            "dsl": True,
        }
        them += 1
    return them


if __name__ == "__main__":
    from nhan import du_lieu as DL
    thu = {
        "ten": "thu_ibs_bien_dong",
        "co_che": "Dong cua o day bien do khi bien dong cao: nguoi ban can thanh khoan "
                  "gap, nguoi mua duoc tra cong o phien sau.",
        "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
        "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.2}},
                {"trai": {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
                 "phep": ">", "phai": {"hang": 0.6}}],
    }
    print("kiem cu phap:", kiem_khai_bao(thu) or "DAT")
    df = DL.nap("EURCAD", "H4")
    th = sinh_tu_spec(thu, df)
    print(f"kich hoat {np.mean(np.abs(th) > 0):.2%} so bar tren {len(df)} bar")
    print("khong nhin truoc:", kiem_khong_nhin_truoc(thu, df))

    # BAI KIEM DO NHAY: mot bay chua tung bat duoc gi thi khong biet no co hoat
    # dong khong. Chen mot chi bao NHIN TRUOC roi xem `kiem_khong_nhin_truoc`
    # co gao len khong (cung cach `canary.tu_kiem` lam voi engine).
    goc = globals()["toan_hang"]

    def _ro_ri(d, t):
        if isinstance(t, dict) and t.get("chi_bao") == "ibs":
            return MAU_MOD.ibs(d).shift(-1)      # dung IBS cua bar KE TIEP
        return goc(d, t)

    globals()["toan_hang"] = _ro_ri
    try:
        bat = kiem_khong_nhin_truoc(thu, df)
    finally:
        globals()["toan_hang"] = goc
    print("do nhay (chen ro ri co y):", "BAT DUOC" if not bat[0] else "TRUOT - PHAI SUA",
          "|", bat[1])
