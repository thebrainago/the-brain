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
import weakref
import sys
from pathlib import Path

import numpy as np
import pandas as pd

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
    # co nho trang thai
    "trang_thai_lat", "dem_lien_tiep",
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


def _dieu_kien(df: pd.DataFrame, ds: list, mac_dinh: bool) -> pd.Series:
    """Danh sach dieu kien -> chuoi bool. Rong thi tra `mac_dinh`."""
    if not ds:
        return pd.Series(mac_dinh, index=df.index)
    ra = None
    for d in ds:
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
            if not isinstance(d, dict) or "trai" not in d or "phai" not in d:
                loi.append(f"{nhom}[{i}] phai co 'trai' va 'phai'")
                continue
            if d.get("phep", ">") not in PHEP:
                loi.append(f"{nhom}[{i}] phep '{d.get('phep')}' khong hop le")
            for ben in ("trai", "phai"):
                loi += [f"{nhom}[{i}].{ben}: {e}" for e in _kiem_toan_hang(d[ben])]
            loi += [f"{nhom}[{i}]: {e}" for e in _kiem_hien_nhien(d)]
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
    diem = sorted(set(int(x) for x in rng.integers(len(df) // 3, len(df) - 2, size=40)))
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


def doc_kho() -> list[dict]:
    try:
        d = json.loads(KHO_CO_CHE.read_text(encoding="utf-8-sig"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def luu_kho(ds: list[dict]) -> None:
    KHO_CO_CHE.parent.mkdir(parents=True, exist_ok=True)
    KHO_CO_CHE.write_text(json.dumps(ds, ensure_ascii=False, indent=1), encoding="utf-8")


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
    """
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
            for ten_ma, df_them in _chuoi_do_them():
                tl2 = _ty_le_kich_hoat(spec, df_them)
                if tl2 is None:
                    chua_do.append(ten_ma)
                    continue
                da_do.append(f"{ten_ma} {tl2:.3%}")
                if _kich_hoat_dat(tl2):
                    ty_le, do_tren = tl2, ten_ma
                    break
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
KHOA_CHINH_DUOC = ("n", "hang")


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


def _dat(nut, duong: str, gt) -> None:
    """Dat `gt` vao vi tri `duong` (dang `0_trai_n`) trong cay `nut`."""
    phan = duong.split("_")
    cuoi = phan[-1]
    cur = nut
    for buoc in phan[:-1]:
        if buoc == "":
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


def nap_vao_mau() -> int:
    """Dua toan bo co che trong kho vao `MAU.MAU` de QUANTLAB quet nhu mau goc.

    Diem cot yeu: co che tu hoc KHONG co duong tat nao. No di qua dung engine,
    dung cong, dung ngan sach FDR nhu mau viet tay.
    """
    them = 0
    for spec in doc_kho():
        ten = spec.get("ten")
        if not ten or ten in MAU_MOD.MAU:
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
