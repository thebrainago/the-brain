# -*- coding: utf-8 -*-
"""Test: duong ra tai khoan that. Day la cho DUY NHAT trong lab gui lenh.

Moi cho khac trong he sai thi mat thoi gian. Cho nay sai thi mat tien, va mat
trong luc khong co ai ngoi canh - he chay tren VPS.

Bon thu bo test nay giu, theo dung thu tu quan trong:

  1. **Mac dinh KHONG gui lenh.** `that=False` la mac dinh, va no phai tinh du
     roi dung lai - khong duoc "tien tay" gui.
  2. **Tai khoan TIEN THAT can HAI chia khoa o HAI cho.** Mot co trong dang ky,
     mot phai go tren dong lenh. Mot chia khoa thi de bi mo nham.
  3. **Phanh chan MO, khong chan DONG.** Mot cai phanh chan ca duong thoat la
     mot cai bay: he vuot tran roi ket trong vi the khong ra duoc.
  4. **Tin hieu tinh tren bar DA DONG.** Dung bar dang chay la nhin truoc, va
     no cho mot chuoi lai DEP HON backtest - rat de bi doc thanh "chay that con
     tot hon do", roi tang von.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import chay_that as CT   # noqa: E402


# --------------------------------------------------------------- MT5 GIA
class _Tick:
    bid, ask = 0.9, 0.9002


class _VT:
    def __init__(self, ticket, volume, type_, magic):
        self.ticket, self.volume, self.type, self.magic = ticket, volume, type_, magic


class MT5Gia:
    """Ban gia cua MetaTrader5 - ghi lai moi lenh thay vi gui di."""
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
    ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
    TRADE_ACTION_DEAL = 1
    TIMEFRAME_H4 = 16388

    def __init__(self, loai_tk=CT.TK_DEMO, vi_the=(), n_bar=400):
        self.loai_tk, self._vt, self.da_gui = loai_tk, list(vi_the), []
        r = np.random.default_rng(0)
        c = 0.9 * np.exp(np.cumsum(r.normal(0, 0.002, n_bar)))
        self._df = pd.DataFrame({
            "time": np.arange(n_bar) * 14400,
            "open": c, "high": c * 1.001, "low": c * 0.999, "close": c,
            "tick_volume": np.full(n_bar, 100.0)})

    def account_info(self):
        return types.SimpleNamespace(login=1, trade_mode=self.loai_tk,
                                     balance=1000.0, currency="USD")

    def symbol_select(self, ma, bat=True):
        return True

    def symbol_info_tick(self, ma):
        return _Tick()

    def copy_rates_from_pos(self, ma, k, tu, n):
        return self._df.tail(n).to_records(index=False)

    def positions_get(self, symbol=None):
        return list(self._vt)

    def order_send(self, yc):
        self.da_gui.append(dict(yc))
        return types.SimpleNamespace(retcode=10009, comment="ok", order=123)

    def shutdown(self):
        pass


@pytest.fixture
def san(tmp_path, monkeypatch):
    """Dang ky + nhat ky o thu muc tam - khong dung vao dang ky that."""
    monkeypatch.setattr(CT, "DANG_KY", tmp_path / "he.json")
    monkeypatch.setattr(CT, "NHAT_KY", tmp_path / "nk.jsonl")
    monkeypatch.setattr(CT, "spec_cua", lambda t: {
        "ten": t, "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
        "co_che": "Ca thu - khong dang ky vao he.",
        "vao": [{"trai": {"chi_bao": "rsi", "n": 2}, "phep": "<",
                 "phai": {"hang": 50.0}}], "ra": []})
    return tmp_path


def _dung(monkeypatch, mt5, phanh_mo=True):
    monkeypatch.setattr(CT, "_mt5", lambda *a, **k: mt5)
    monkeypatch.setattr(CT, "tin_hieu", lambda spec, df: 1.0)
    hm = types.SimpleNamespace(
        duoc_vao_lenh=lambda he, *a, **k: (phanh_mo, "thu"))
    monkeypatch.setitem(sys.modules, "nhan.han_muc", hm)
    ns = types.SimpleNamespace(giu_warp=lambda *a, **k: _KhongLam())
    monkeypatch.setitem(sys.modules, "nhan.ngan_sach", ns)


class _KhongLam:
    def __enter__(self): return self
    def __exit__(self, *a): return False


# ------------------------------------------------------------------ TEST
def test_mac_dinh_la_DIEN_TAP_khong_gui_lenh(san, monkeypatch):
    mt5 = MT5Gia()
    _dung(monkeypatch, mt5)
    CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 1, bat=True)
    ket = CT.mot_nhip()
    assert ket[0]["trang_thai"] == "DIEN_TAP"
    assert mt5.da_gui == [], "mac dinh ma da gui lenh di"


def test_tien_that_can_HAI_chia_khoa(san, monkeypatch):
    """Mot chia khoa trong dang ky, mot tren dong lenh - thieu cai nao cung chan."""
    for trong_dang_ky, tren_dong_lenh, mong in (
            (False, False, "CHAN"), (True, False, "CHAN"),
            (False, True, "CHAN"), (True, True, "DA_LAM")):
        mt5 = MT5Gia(loai_tk=CT.TK_TIEN_THAT)
        _dung(monkeypatch, mt5)
        CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 1, bat=True,
                   cho_phep_tien_that=trong_dang_ky)
        ket = CT.mot_nhip(that=True, cho_tien_that=tren_dong_lenh)
        assert ket[0]["trang_thai"] == mong, (
            "dang ky=%s dong lenh=%s -> %s (mong %s)"
            % (trong_dang_ky, tren_dong_lenh, ket[0]["trang_thai"], mong))


def test_tai_khoan_DEMO_thi_khong_can_chia_khoa_nao(san, monkeypatch):
    mt5 = MT5Gia(loai_tk=CT.TK_DEMO)
    _dung(monkeypatch, mt5)
    CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 1, bat=True)
    assert CT.mot_nhip(that=True)[0]["trang_thai"] == "DA_LAM"
    assert len(mt5.da_gui) == 1


def test_CHAN_van_TINH_chu_khong_lam_mu(san, monkeypatch):
    """Chot an toan chan GUI LENH, khong duoc chan phep DO.

    Ban dau toi chan ca hai va no lam mat chinh cai can nhat: khong con biet
    duong tin hieu co chay khong.
    """
    mt5 = MT5Gia(loai_tk=CT.TK_TIEN_THAT)
    _dung(monkeypatch, mt5)
    CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 1, bat=True)
    b = CT.mot_nhip(that=True)[0]
    assert b["trang_thai"] == "CHAN"
    assert "muc_tieu" in b and "bar_cuoi" in b, "chan xong khong con do duoc gi"
    assert b.get("viec_le_ra"), "khong noi ro no DINH lam gi"


def test_PHANH_chan_MO_nhung_KHONG_chan_DONG(san, monkeypatch):
    """Mot cai phanh chan ca duong thoat la mot cai bay."""
    vt = [_VT(1, 0.01, MT5Gia.POSITION_TYPE_BUY, 7)]
    mt5 = MT5Gia(loai_tk=CT.TK_DEMO, vi_the=vt)
    _dung(monkeypatch, mt5, phanh_mo=False)
    monkeypatch.setattr(CT, "tin_hieu", lambda spec, df: 0.0)   # muon THOAT
    CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 7, bat=True)
    b = CT.mot_nhip(that=True)[0]
    assert b["trang_thai"] == "DA_LAM", "phanh dang chan ca duong thoat"
    assert mt5.da_gui, "khong dong vi the du tin hieu bao thoat"


def test_phanh_DONG_thi_khong_mo_vi_the_moi(san, monkeypatch):
    mt5 = MT5Gia(loai_tk=CT.TK_DEMO)
    _dung(monkeypatch, mt5, phanh_mo=False)
    CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 1, bat=True)
    assert CT.mot_nhip(that=True)[0]["trang_thai"] == "PHANH"
    assert mt5.da_gui == []


def test_he_CHUA_BAT_thi_khong_lam_gi(san, monkeypatch):
    mt5 = MT5Gia()
    _dung(monkeypatch, mt5)
    CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 1, bat=False)
    assert CT.mot_nhip(that=True)[0]["trang_thai"] == "TAT"
    assert mt5.da_gui == []


def test_bar_CUOI_bi_bo_vi_no_chua_dong(san, monkeypatch):
    """Dung bar dang chay la nhin truoc - va no cho chuoi lai DEP HON backtest."""
    mt5 = MT5Gia()
    df = CT._bar(mt5, "AUDCADmicro", "H4", n=100)
    tho = pd.DataFrame(mt5.copy_rates_from_pos("x", 0, 0, 100))
    assert len(df) == len(tho) - 1, "chua bo bar dang chay"


def test_nhat_ky_ghi_CA_quyet_dinh_khong_lam_gi(san, monkeypatch):
    """He im lang co hai nghia: dang cho, hoac da chet tu hom kia."""
    mt5 = MT5Gia()
    _dung(monkeypatch, mt5)
    monkeypatch.setattr(CT, "tin_hieu", lambda spec, df: 0.0)
    CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 1, bat=True)
    CT.mot_nhip()
    dong = [json.loads(x) for x in CT.NHAT_KY.read_text(encoding="utf-8").splitlines()]
    assert dong and dong[-1]["trang_thai"] == "GIU"
    assert "luc" in dong[-1], "khong co dau thoi gian"


def test_dang_ky_moi_mac_dinh_la_TAT(san):
    c = CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 1)
    assert c["bat"] is False, "he moi dang ky ma da tu chay"
    assert c["cho_phep_tien_that"] is False


def test_khong_co_he_nao_thi_noi_CHUA_DO_DUOC(san):
    k = CT.mot_nhip()
    assert k[0]["trang_thai"] == "CHUA_DO_DUOC"


def test_chi_dong_vi_the_dung_MAGIC_cua_minh(san, monkeypatch):
    """Tai khoan co the co vi the cua he khac hoac cua nguoi. Dung dung vao."""
    vt = [_VT(1, 0.01, MT5Gia.POSITION_TYPE_BUY, 7),
          _VT(2, 0.50, MT5Gia.POSITION_TYPE_BUY, 999)]
    mt5 = MT5Gia(loai_tk=CT.TK_DEMO, vi_the=vt)
    assert CT._vi_the(mt5, "AUDCADmicro", 7) == pytest.approx(0.01)
    _dung(monkeypatch, mt5)
    monkeypatch.setattr(CT, "tin_hieu", lambda spec, df: 0.0)
    CT.dang_ky("h", "AUDCADmicro", "H4", "cc", 0.01, 7, bat=True)
    CT.mot_nhip(that=True)
    assert all(g.get("position") != 2 for g in mt5.da_gui), (
        "dang dong vi the cua he khac")
