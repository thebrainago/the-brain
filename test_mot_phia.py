# -*- coding: utf-8 -*-
"""He LUON CO LENH nhung dao mua/ban khong phai "mua-giu tra hinh" (ra soat 18/10/2026)."""
from unittest import mock

import numpy as np
import pandas as pd

from nhan import loc_co_che as LCC, sang_loc as SL, to_hop as TH


def _df(n=3000):
    gia = 100 * np.exp(np.cumsum(np.random.default_rng(3).normal(0, 0.01, n)))
    return pd.DataFrame({"open": gia, "high": gia, "low": gia, "close": gia},
                        index=pd.date_range("2010-01-01", periods=n, freq="D"))


def _dao_chieu(n):
    th = np.ones(n)
    for k in range(0, n, 120):
        th[k + 60:k + 120] = -1.0              # 60 bar mua, 60 bar ban, luon co lenh
    return th


def test_sang_loc_khong_coi_he_dao_chieu_la_mua_giu():
    df = _df()
    with mock.patch.object(SL.MAU, "sinh", return_value=_dao_chieu(len(df))), \
            mock.patch.object(SL, "_ghi_loai"), mock.patch.object(SL, "_ghi_cho_them"):
        kq, ly, do = SL.v1_sang_re(None, "x", {}, "EURUSD", "D1", df)
    assert ly != "mua_giu_tra_hinh" and do["kich_hoat"] == 1.0 and do["mot_phia"] == 0.5
    with mock.patch.object(SL.MAU, "sinh", return_value=np.ones(len(df))), \
            mock.patch.object(SL, "_ghi_loai"), mock.patch.object(SL, "_ghi_cho_them"):
        assert SL.v1_sang_re(None, "x", {}, "EURUSD", "D1", df)[1] == "mua_giu_tra_hinh"


def test_loc_co_che_dem_lat_chieu_va_mot_phia():
    df = _df(600)
    with mock.patch("nhan.mau.sinh", return_value=_dao_chieu(len(df))):
        r = LCC._do_mot_ma(["x"], df)["x"]
    assert r["ty_le"] == 1.0 and r["mot_phia"] == 0.5 and r["so_lenh"] >= 9


def test_to_hop_khong_chan_he_o_thi_truong_lau():
    assert TH.KICH_HOAT[1] >= 0.95
