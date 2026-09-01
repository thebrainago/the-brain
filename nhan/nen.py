# -*- coding: utf-8 -*-
"""nen.py - DOI CACH DUNG NEN, NHUNG CHI CHO TIN HIEU.

VI SAO CO FILE NAY (chu du an chot 01/09/2026: "thu ca cac loai nen nua").

RANG BUOC LON NHAT, va no khong thuong luong duoc:

    **Gia Heikin Ashi KHONG PHAI GIA MUA BAN DUOC.**

`ha_close` la trung binh cua (open, high, low, close) va `ha_open` la trung binh
cua hai gia tri HA truoc do. Khong mot lenh nao khop duoc o nhung muc do - chung
la so ke toan, khong phai gia tren so lenh. Mot backtest vao/ra o gia HA che ra
lai tu cho khong co, va no che RAT NHIEU vi HA da san bang dung phan nhieu ma
mot lenh that phai chiu.

Day dung la ho voi bay `Model=1` da sap ngay 01/08: mot mo hinh gia dinh duong
di trong nen, va TP luon duoc khop o chan thuan loi -> +1.161,5% so voi -100,7%
o tick that, lech 12 lan.

Nen quy tac o day:

    NEN BIEN DOI CHI DUNG DE TINH TIN HIEU.
    KHOP LENH, CHI PHI, LOI SUAT LUON TINH TREN NEN THAT.

`sinh_tren_nen()` giu dung ranh gioi do: no tinh tin hieu tren khung DA BIEN DOI
roi tra ve mot mang chi so THEO KHUNG THAT, de `mo_phong.chay(df_that, ...)`
khong doi mot dong nao.

TINH NHAN QUA. Moi phep bien doi o day chi doc bar hien tai va qua khu:
`ha_close[i]` dung OHLC cua chinh bar i (biet luc bar i dong cua, y het `close[i]`
trong moi mau khac), `ha_open[i]` dung HA cua bar i-1. Khong nhanh nao nhin ve
tuong lai. Bai kiem `kiem_khong_nhin_truoc` cua ngu phap van chay binh thuong.

KHONG CO RENKO. `SONIC_R_PHAN_TICH.md` muc 3.4 da ket luan: nen Renko hinh thanh
theo muc di chuyen gia chu khong theo thoi gian, nen backtest Renko **khong tai
lap duoc tren thi truong that** - do la loi kinh dien lam duong von Renko trong
hoan hao. Khong dua no vao day.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

#: Nen goc cua san. Khong bien doi gi.
THUONG = "thuong"
#: Heikin Ashi.
HA = "ha"

LOAI = (THUONG, HA)


def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Khung Heikin Ashi, cung chi so bar va cung so dong.

    ha_close[i] = mean(open, high, low, close)[i]        - biet khi bar i dong
    ha_open[0]  = mean(open, close)[0]
    ha_open[i]  = mean(ha_open[i-1], ha_close[i-1])      - chi doc qua khu
    ha_high[i]  = max(high[i], ha_open[i], ha_close[i])
    ha_low[i]   = min(low[i],  ha_open[i], ha_close[i])
    """
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    n = len(df)
    ha_c = (o + h + l + c) / 4.0
    ha_o = np.empty(n, dtype=float)
    if n:
        ha_o[0] = (o[0] + c[0]) / 2.0
        # Vong lap that su can: `ha_open` de quy nen khong viet vector duoc.
        for i in range(1, n):
            ha_o[i] = (ha_o[i - 1] + ha_c[i - 1]) / 2.0
    ra = df.copy()
    ra["open"] = ha_o
    ra["close"] = ha_c
    ra["high"] = np.maximum.reduce([h, ha_o, ha_c])
    ra["low"] = np.minimum.reduce([l, ha_o, ha_c])
    return ra


_BIEN_DOI = {HA: heikin_ashi}


def bien_doi(df: pd.DataFrame, kieu: str = THUONG) -> pd.DataFrame:
    """Khung de TINH TIN HIEU. `thuong` tra ve chinh no (khong copy thua)."""
    kieu = (kieu or THUONG).lower()
    if kieu == THUONG:
        return df
    if kieu not in _BIEN_DOI:
        raise KeyError(f"khong co loai nen '{kieu}'. Co: {', '.join(LOAI)}")
    for cot in ("open", "high", "low", "close"):
        if cot not in df.columns:
            raise KeyError(f"khung thieu cot '{cot}', khong bien doi nen duoc")
    return _BIEN_DOI[kieu](df)


def sinh_tren_nen(ham_sinh, df: pd.DataFrame, kieu: str = THUONG, **kw):
    """Tinh tin hieu tren nen `kieu`, tra mang THEO KHUNG THAT.

    `ham_sinh(khung, **kw)` la bat ky bo sinh tin hieu nao (`mau.sinh` da gan
    tham so, hay `ngu_phap.sinh_tu_spec`). Ranh gioi cua ca file nam o mot dong:
    ta doi khung dua VAO bo sinh, va khong doi gi o phia `mo_phong.chay`.
    """
    th = ham_sinh(bien_doi(df, kieu), **kw)
    a = np.asarray(th, dtype=float)
    if len(a) != len(df):
        raise ValueError(f"tin hieu {len(a)} bar khong khop khung that {len(df)} bar")
    return a


def mo_ta(kieu: str) -> str:
    return {
        THUONG: "nen goc cua san",
        HA: "Heikin Ashi - CHI de tinh tin hieu; khop lenh van o gia that",
    }.get((kieu or THUONG).lower(), kieu)
