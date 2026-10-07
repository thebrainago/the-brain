# -*- coding: utf-8 -*-
"""nc_dac_trung.py - DAC TRUNG NGU CANH tai diem vao lenh, viet bang CHINH toan hang ngu phap.

Nha nghien cuu (`nhan/nc_*`) hoc tu lenh dung/lenh sai bang cach hoi: *luc vao
lenh, lenh thang khac lenh thua o dau?* Cau hoi do can mot bo do NGU CANH tai
bar tin hieu: bien dong dang cao hay thap, gia dang o dau trong kenh, xu huong
manh hay yeu, ngay nao trong tuan...

## VI SAO MOI DAC TRUNG LA MOT TOAN HANG CUA `ngu_phap`

Khong tu viet chi bao o day. Moi dac trung la mot dict toan hang cua
`nhan/ngu_phap.py`, tinh bang `NP.toan_hang`. Hai he qua, ca hai deu quan trong:

1. **Khong nhin truoc theo cau tao.** Trinh thong dich khong co toan tu nao
   doc tuong lai; `kiem_khong_nhin_truoc` con kiem them bang phep cat.
2. **Luat tim ra CHAY NGAY duoc.** Mot bo loc mo xe tim thay ("chi vao khi
   `atr_pv < 0,5`") la mot DIEU KIEN DSL hop le - noi vao `vao` cua khai bao
   goc la thu lai duoc bang dung engine, dung chi phi, va dich sang MQL5 bang
   `dich_mq5` (cot `mq5` noi toan hang do co trong `CHI_BAO_DICH_DUOC` khong).

Neu tu tinh dac trung bang numpy roi dich nguoc sang DSL, hai ban se lech nhau
o mot chi tiet nao do (dich bar, cua so rank) va luat "hoc duoc" se khong con
la luat dang chay - dung ho loi *"bo phan co ton tai nhung khong nam tren
duong chay"* cua du an.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import ngu_phap as NP
else:
    from . import ngu_phap as NP

_C = {"chi_bao": "gia", "cot": "close"}


def _pv(con: dict, n: int) -> dict:
    return {"chi_bao": "phan_vi", "cua": con, "n": n}


def _z(con: dict, n: int) -> dict:
    return {"chi_bao": "zscore", "cua": con, "n": n}


#: ten -> (toan hang DSL, mo ta cho AI doc, nhom). Thu tu co y nghia: bao cao
#: liet ke theo thu tu nay khi hai dac trung diem bang nhau.
DAC_TRUNG: dict[str, tuple[dict, str, str]] = {
    # --- vi tri gia / qua mua qua ban ---
    "ibs": ({"chi_bao": "ibs"}, "dong cua o dau trong bien do bar: 0 = day, 1 = dinh", "dao_dong"),
    "rsi2": ({"chi_bao": "rsi", "n": 2}, "RSI 2 bar (0..100) - qua mua/qua ban rat ngan", "dao_dong"),
    "rsi14": ({"chi_bao": "rsi", "n": 14}, "RSI 14 bar (0..100)", "dao_dong"),
    "stoch14": ({"chi_bao": "stochastic", "n": 14}, "Stochastic %K 14 (0..100)", "dao_dong"),
    "z20": (_z(_C, 20), "do lech chuan cua close so voi TB 20 bar", "dao_dong"),
    "z100": (_z(_C, 100), "do lech chuan cua close so voi TB 100 bar", "dao_dong"),
    "bb_b": ({"chi_bao": "bollinger", "n": 20, "k": 2.0, "lay": "phan_tram_b"},
             "%b Bollinger 20/2: <0 duoi dai duoi, >1 tren dai tren", "dao_dong"),
    "don20": ({"chi_bao": "donchian", "n": 20, "lay": "vi_tri"},
              "vi tri close trong kenh Donchian 20 bar TRUOC (0 = day kenh, 1 = dinh)", "kenh"),
    "don55": ({"chi_bao": "donchian", "n": 55, "lay": "vi_tri"},
              "vi tri close trong kenh Donchian 55 bar truoc", "kenh"),
    # --- dong luong / xu huong ---
    "r1_pv": (_pv({"chi_bao": "doi_pct", "cua": _C, "n": 1}, 250),
              "phan vi cua loi suat bar nay trong 250 bar (cu soc 1 bar)", "dong_luong"),
    "r5_z": (_z({"chi_bao": "doi_pct", "cua": _C, "n": 5}, 250),
             "loi suat 5 bar chuan hoa (z trong 250 bar)", "dong_luong"),
    "r20_z": (_z({"chi_bao": "doi_pct", "cua": _C, "n": 20}, 250),
              "loi suat 20 bar chuan hoa (z trong 250 bar)", "dong_luong"),
    "doc_ema20": (_z({"chi_bao": "doi_pct", "cua": {"chi_bao": "ema", "cot": "close", "n": 20},
                      "n": 5}, 250),
                  "do doc EMA20 qua 5 bar, chuan hoa z 250 bar", "xu_huong"),
    "z200": (_z(_C, 200), "close so voi TB 200 bar (chuan hoa) - che do xu huong dai", "xu_huong"),
    "adx14": ({"chi_bao": "adx", "n": 14}, "ADX 14 - do manh xu huong (khong co chieu)", "xu_huong"),
    "st_chieu": ({"chi_bao": "supertrend", "n": 10, "k": 3.0, "lay": "chieu"},
                 "chieu Supertrend 10/3: +1 len, -1 xuong", "xu_huong"),
    "ha_chieu": ({"chi_bao": "heiken", "lay": "chieu"}, "chieu nen Heikin-Ashi: +1/-1", "xu_huong"),
    # --- bien dong / che do ---
    "atr_pv": (_pv({"chi_bao": "atr", "n": 14}, 250),
               "phan vi ATR14 trong 250 bar: bien dong dang cao hay thap", "bien_dong"),
    "bd_pv": (_pv({"chi_bao": "bien_do"}, 100), "phan vi bien do bar nay trong 100 bar", "bien_dong"),
    "rong20": ({"chi_bao": "donchian", "n": 20, "lay": "do_rong"},
               "do rong kenh Donchian 20 / gia - nen chat hay rong", "bien_dong"),
    "than_pv": (_pv({"chi_bao": "than_nen"}, 100),
                "phan vi than nen CO DAU (close-open) trong 100 bar", "nen"),
    # --- dong tien ---
    "kl_pv": (_pv({"chi_bao": "khoi_luong"}, 100), "phan vi tick volume trong 100 bar", "dong_tien"),
    # --- lich ---
    "thu": ({"chi_bao": "ngay_trong_tuan"}, "thu trong tuan: 0 = thu Hai .. 4 = thu Sau", "lich"),
    "ngay": ({"chi_bao": "ngay_trong_thang"}, "ngay trong thang (1..31)", "lich"),
    "thang": ({"chi_bao": "thang"}, "thang (1..12)", "lich"),
    "gio": ({"chi_bao": "gio"}, "gio mo bar (chi co tren khung trong ngay)", "lich"),
}

#: Nhom -> ho co che cua ngu phap (`NP.HO_HOP_LE`) khi mot luat chi dung nhom do.
HO_THEO_NHOM = {"dao_dong": "quay_ve_trung_binh", "kenh": "pha_vo",
                "dong_luong": "xu_huong", "xu_huong": "xu_huong",
                "bien_dong": "bien_dong", "nen": "quay_ve_trung_binh",
                "dong_tien": "dong_tien", "lich": "lich"}


def co_gio(df: pd.DataFrame) -> bool:
    """Khung co gio (bar trong ngay) khong. D1 thi `gio` luon 0 -> vo nghia."""
    try:
        return len(np.unique(pd.DatetimeIndex(df.index).hour)) > 1
    except Exception:
        return False


def toan_hang(ten: str) -> dict:
    return dict(DAC_TRUNG[ten][0])


def dich_duoc_mq5(ten: str) -> bool:
    """Toan hang (va moi toan hang con) co trong bo dich MQL5 khong."""
    try:
        from nhan import dich_mq5 as DM
        duoc = DM.CHI_BAO_DICH_DUOC
    except Exception:
        return False

    def _di(t) -> bool:
        if not isinstance(t, dict):
            return True
        if "chi_bao" in t and t["chi_bao"] not in duoc:
            return False
        return all(_di(v) for v in t.values() if isinstance(v, dict))
    return _di(DAC_TRUNG[ten][0])


def tinh(df: pd.DataFrame, chon: list[str] | None = None,
         ty_le_hop_le: float = 0.5) -> pd.DataFrame:
    """Bang dac trung cho MOI bar cua `df` (cot = ten dac trung).

    Bo dac trung nao: loi khi tinh (thieu cot), hoac co hon (1 - ty_le_hop_le)
    gia tri NaN, hoac hang so. Bo `gio` tren khung khong co gio - ngu phap se
    nem loi, va do la dung: mot dieu kien theo gio tren D1 la loi cau hinh.
    """
    cot: dict[str, pd.Series] = {}
    for ten, (op, _mo_ta, _nhom) in DAC_TRUNG.items():
        if chon and ten not in chon:
            continue
        if ten == "gio" and not co_gio(df):
            continue
        try:
            s = NP.toan_hang(df, op).astype(float)
        except Exception:
            continue
        s = s.replace([np.inf, -np.inf], np.nan)
        if s.notna().mean() < ty_le_hop_le:
            continue
        if s.nunique(dropna=True) < 2:
            continue
        cot[ten] = s
    return pd.DataFrame(cot, index=df.index)


def dieu_kien(ten: str, phep: str, nguong: float) -> dict:
    """Mot dieu kien DSL `{trai: dac trung, phep, phai: hang}`."""
    if phep not in NP.PHEP:
        raise KeyError("phep '%s' khong hop le" % phep)
    return {"trai": toan_hang(ten), "phep": phep, "phai": {"hang": float(nguong)}}


def ten_cua_toan_hang(op: dict) -> str | None:
    """Toan hang -> ten dac trung (neu trung khit mot dac trung da khai)."""
    for ten, (t, _m, _n) in DAC_TRUNG.items():
        if t == op:
            return ten
    return None


def mo_ta() -> list[dict]:
    """Danh sach cho AI doc: ten, y nghia, nhom, dich MQL5 duoc khong."""
    return [{"ten": t, "y_nghia": m, "nhom": n, "mq5": dich_duoc_mq5(t)}
            for t, (_op, m, n) in DAC_TRUNG.items()]


if __name__ == "__main__":
    from nhan import nc_du_lieu as NDL
    d = NDL.nap("TONG_HOP_NHIEU_1", "H4")
    X = tinh(d)
    print(X.shape, list(X.columns))
    print(X.describe().T[["mean", "min", "max"]].round(3).to_string())
