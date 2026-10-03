# -*- coding: utf-8 -*-
"""Doan du lieu DONG BANG theo NGAY: du lieu lon them o cuoi khong keo doan niem phong nhay ve phia truoc."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from nhan import nc_du_lieu as NDL


def _chuoi(n: int, tz=None, bat_dau="2020-01-01", hat=3) -> pd.DataFrame:
    g = np.random.default_rng(hat)
    gia = 100 * np.exp(np.cumsum(g.normal(0, 0.002, n)))
    idx = pd.date_range(bat_dau, periods=n, freq="4h", tz=tz)
    return pd.DataFrame({"open": gia, "high": gia * 1.001, "low": gia * 0.999, "close": gia,
                         "spread": 10.0}, index=idx)


@pytest.fixture
def so_cai(tmp_path, monkeypatch):
    monkeypatch.setenv("NC_SO_CAI", str(tmp_path))
    return tmp_path


def test_lan_dau_ghi_moc_theo_ti_le_va_ghi_vao_so_cai(so_cai):
    df = _chuoi(1000)
    k = NDL.dong_bang("audcad", "h4", df)
    assert k["t_dau"] == str(df.index[0]) and k["t_cuoi"] == str(df.index[-1]) and k["n0"] == 1000
    assert k["t_xac_nhan"] == str(df.index[600]) and k["t_niem_phong"] == str(df.index[800])
    reg = json.loads((so_cai / "doan.json").read_text(encoding="utf-8"))
    assert list(reg) == ["AUDCAD|H4"], "khoa phai chuan hoa HOA"
    assert NDL.chi_so_doan(1000, "niem_phong", df) == (800, 1000)


def test_du_lieu_lon_them_cuoi_chuoi_KHONG_keo_ranh_gioi_nhay(so_cai):
    """Dung loi ro ri holdout: truoc day 80% cua chuoi DAI HON nhay ve phia truoc."""
    cu = _chuoi(1000)
    NDL.dong_bang("AUDCAD", "H4", cu)
    t_np_cu = cu.index[800]
    moi = _chuoi(1300)                                    # cung chuoi, them 300 bar o cuoi
    assert NDL.dong_bang("AUDCAD", "H4", moi) is not None
    # CHUA dong bang (cach cu): 80% cua 1300 = bar 1040 -> 240 bar da niem phong bi rot sang xac_nhan
    assert NDL.chi_so_doan(1300, "niem_phong")[0] == 1040
    # DA dong bang: van o bar 800, va 300 bar moi KHONG thuoc doan nao
    a, b = NDL.chi_so_doan(1300, "niem_phong", moi)
    assert (a, b) == (800, 1000) and moi.index[a] == t_np_cu
    assert NDL.chi_so_doan(1300, "xac_nhan", moi) == (600, 800)
    pre, bd = NDL.cat_doan(moi, "kham_pha")
    assert len(pre) == 600 and bd == 0
    pre_np, bd_np = NDL.cat_doan(moi, "niem_phong", _giay_phep=True)
    assert len(pre_np) == 1000 and bd_np == 800, "bar moi phai nam NGOAI moi doan"


def test_van_cam_doc_niem_phong_khi_khong_co_giay_phep(so_cai):
    df = _chuoi(1000)
    NDL.dong_bang("AUDCAD", "H4", df)
    with pytest.raises(NDL.DoanNiemPhong):
        NDL.cat_doan(df, "niem_phong")


def test_du_lieu_trong_doan_da_dong_bang_bi_doi_thi_nem_LoiDoan(so_cai):
    df = _chuoi(1000)
    NDL.dong_bang("AUDCAD", "H4", df)
    sua = _chuoi(1000)
    sua.iloc[500, sua.columns.get_loc("close")] *= 1.0001     # moi de mot bar bi nha moi gioi dieu chinh
    with pytest.raises(NDL.LoiDoan) as e:
        NDL.dong_bang("AUDCAD", "H4", sua)
    assert "DA DOI" in str(e.value)
    # hieu chuan nguoc: du lieu y het thi di qua
    assert NDL.dong_bang("AUDCAD", "H4", _chuoi(1000)) is not None


def test_du_lieu_bat_dau_som_hon_hay_thieu_doan_cuoi_cung_la_LoiDoan(so_cai):
    NDL.dong_bang("AUDCAD", "H4", _chuoi(1000))
    with pytest.raises(NDL.LoiDoan):
        NDL.dong_bang("AUDCAD", "H4", _chuoi(1000, bat_dau="2019-12-01"))   # lich su dai hon o dau
    with pytest.raises(NDL.LoiDoan):
        NDL.dong_bang("AUDCAD", "H4", _chuoi(900))                           # thieu 100 bar cuoi


def test_mui_gio_chay_duoc_va_khong_nhan_nham_naive_voi_aware(so_cai):
    utc = _chuoi(1000, tz="UTC")
    NDL.dong_bang("EURUSD", "H4", utc)
    assert NDL.chi_so_doan(1000, "niem_phong", utc) == (800, 1000)
    assert NDL.dong_bang("EURUSD", "H4", _chuoi(1200, tz="UTC")) is not None
    with pytest.raises(NDL.LoiDoan):
        NDL.dong_bang("EURUSD", "H4", _chuoi(1000))                          # moc co mui gio, du lieu naive


def test_chuoi_qua_ngan_khong_dong_bang_va_chuoi_khong_co_attrs_van_dung_ti_le(so_cai):
    ngan = _chuoi(50)
    assert NDL.dong_bang("X", "H4", ngan) is None and not (so_cai / "doan.json").exists()
    kg = _chuoi(1000)
    assert NDL.chi_so_doan(len(kg), "xac_nhan", kg) == (600, 800)           # tuong thich nguoc: tong hop, test cu
    assert NDL.chi_so_doan(1000, "niem_phong") == (800, 1000)


def test_chuoi_tong_hop_khong_bi_dong_bang_khi_nap(so_cai):
    d = NDL.nap("TONG_HOP_NHIEU_1", "H4")
    assert "doan_dong_bang" not in d.attrs and not (so_cai / "doan.json").exists()
