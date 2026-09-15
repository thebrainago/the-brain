# -*- coding: utf-8 -*-
"""Test: NGUONG TINH BANG DON VI GIA khong duoc di qua trong im lang.

## Chuyen da xay ra, 15/09/2026

Chay 61 co che `than_nen` qua MT5 tester tren AUDCADmicro H4: **13 co che ra
dung 0 lenh**. Bai hoc hom truoc ("mot dong 0 lenh thi doc ma MQL5 no sinh ra")
dan toi bo dich - va bo dich khong co loi: ban Python cung ban 0 tin hieu.

Cai hong nam trong loi khai: `than_nen > 0.5`, tuc `close - open` (DON VI GIA)
so voi mot hang so tran. Tren nam chuoi, ty le kich hoat di tu 0,000 (EURUSD,
gia 1,17) den 0,532 (US500Cash, gia 2.753) **chi theo muc gia**.

Va no song sot duoc vi cua vao kho `break` ngay o chuoi dau tien dat: co che
vao kho mang theo con so cua XAUUSD (0,3639), mot con so hoan toan khoe manh.

Bo test nay giu ba thu: bo do phai THAY duoc ca hai ca that; no khong duoc bat
oan co che thua thot; va thong tin "song o dau" phai duoc GIU LAI chu khong bi
nuot con mot so.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import thang_gia as TG   # noqa: E402


def _chuoi_gia(gia: float, n: int = 4000, seed: int = 0):
    """Chuoi ngau nhien o mot MUC GIA cho truoc, bien dong tuong doi nhu nhau."""
    r = np.random.default_rng(seed)
    c = gia * np.exp(np.cumsum(r.normal(0, 0.002, n)))
    o = np.concatenate([[c[0]], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(r.normal(0, 0.001, n)))
    l = np.minimum(o, c) * (1 - np.abs(r.normal(0, 0.001, n)))
    return pd.DataFrame(
        {"open": o, "high": h, "low": l, "close": c,
         "tick_volume": np.full(n, 100.0)},
        index=pd.date_range("2015-01-01", periods=n, freq="h"))


def _ds():
    """Bon bac gia, cung mot hanh vi - khac nhau DUY NHAT o thang gia."""
    return [("re.H1", _chuoi_gia(1.0), 1.0),
            ("vua.H1", _chuoi_gia(1.2, seed=1), 1.2),
            ("kha.H1", _chuoi_gia(1.5, seed=2), 1.5),
            ("dat.H1", _chuoi_gia(120.0, seed=3), 120.0),
            ("rat_dat.H1", _chuoi_gia(1500.0, seed=4), 1500.0),
            ("dat_nhat.H1", _chuoi_gia(4000.0, seed=5), 4000.0)]


def _spec(vao, ten="thu"):
    return {"ten": ten, "ho": "bien_dong", "chieu": 1, "giu": 1,
            "co_che": "Chi de thu bo do, khong phai gia thuyet kinh te nao.",
            "vao": vao, "ra": []}


def test_BAT_DUOC_nguong_don_vi_gia(monkeypatch):
    """Ca that: `than_nen > 0.5` - dung hinh dang da lam hong 13 co che."""
    ds = _ds()
    monkeypatch.setattr(TG, "chuoi", lambda lam_moi=False: ds)
    s = _spec([{"trai": {"chi_bao": "than_nen"}, "phep": ">",
                "phai": {"hang": 0.5}}], "ty_le_than_nen_gia")
    k = TG.mot_co_che(s, ds)
    assert k["xep_loai"] == "PHU_THUOC_THANG_GIA", k["ty_le"]
    assert k["ty_le"]["re.H1"] < TG.SAN, "chuoi gia thap phai CHET"
    assert k["ty_le"]["dat_nhat.H1"] > 0.2, "chuoi gia cao phai SONG"


def test_KHONG_bat_oan_co_che_khong_dinh_don_vi(monkeypatch):
    """Chieu nguoc lai: neu bo do bat ca cai tot thi no vo dung.

    `close > open` khong co hang so don vi gia nao - phai la ON_DINH o moi bac.
    """
    ds = _ds()
    monkeypatch.setattr(TG, "chuoi", lambda lam_moi=False: ds)
    s = _spec([{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
                "phai": {"chi_bao": "gia", "cot": "open"}}], "nen_xanh")
    k = TG.mot_co_che(s, ds)
    assert k["xep_loai"] == "ON_DINH", k["ty_le"]


def test_co_che_THUA_THOT_khong_bi_goi_la_dinh_don_vi(monkeypatch):
    """Ban dau tien bat oan `pine_golden_cross`: 0,003 khap noi, 0,0019 o mot cho.

    Dao qua dao lai quanh `SAN` khong phai dau van tay cua don vi gia. Chenh
    lech chi doc duoc khi mot ben THAT SU song.
    """
    ds = _ds()
    monkeypatch.setattr(TG, "chuoi", lambda lam_moi=False: ds)
    ty_le = {"re.H1": 0.003, "vua.H1": 0.003, "kha.H1": 0.003,
             "dat.H1": 0.003, "rat_dat.H1": 0.003, "dat_nhat.H1": 0.0019}
    assert TG.xep_loai(ty_le) == "THUA_THOT"


def test_mot_cap_le_chet_KHONG_phai_chuyen_cua_thang_gia(monkeypatch):
    """Ba chuoi cung bac gia phai CUNG chet thi moi quy cho thang gia.

    Mot cap don le chet la chuyen cua cap do. Neu khong doi dieu nay thi bo do
    se do moi khac biet giua cac tai san len dau don vi gia.
    """
    ds = _ds()
    monkeypatch.setattr(TG, "chuoi", lambda lam_moi=False: ds)
    ty_le = {"re.H1": 0.000, "vua.H1": 0.150, "kha.H1": 0.160,
             "dat.H1": 0.170, "rat_dat.H1": 0.180, "dat_nhat.H1": 0.190}
    assert TG.xep_loai(ty_le) == "ON_DINH"


def test_chet_moi_noi_tach_khoi_chua_do_duoc(monkeypatch):
    """Ba trang thai, khong phai hai: khong do duoc KHAC voi do ra 0."""
    ds = _ds()
    monkeypatch.setattr(TG, "chuoi", lambda lam_moi=False: ds)
    assert TG.xep_loai({t: 0.0 for t, _, _ in ds}) == "CHET_MOI_NOI"
    assert TG.xep_loai({t: None for t, _, _ in ds}) == "CHUA_DO_DUOC"


def test_chuoi_gan_chon_theo_BAC_GIA_khong_theo_TEN(monkeypatch):
    """`EURGBP` (0,85) gan `GBPUSD` (1,51) hon la `EURUSD`-vi-cung-chu-EUR.

    Chon theo tien to ten la thoi quen, khong phai lap luan: cai quyet dinh co
    che song hay chet la MUC GIA.
    """
    ds = _ds()
    monkeypatch.setattr(TG, "chuoi", lambda lam_moi=False: ds)
    monkeypatch.setattr(TG, "_gia_cua_ma", lambda ma: 0.85, raising=False)

    class _DL:
        @staticmethod
        def nap(ma, khung):
            return pd.DataFrame({"close": [0.85] * 10})
    monkeypatch.setitem(sys.modules, "nhan.du_lieu", _DL)
    gan = TG.chuoi_gan("EURGBPmicro")
    assert "re.H1" in gan and "kha.H1" in gan
    assert "rat_dat.H1" not in gan, "chuoi cach ba bac gia khong noi duoc gi"


def test_canh_bao_cho_ma_chi_noi_khi_co_kho_do(monkeypatch):
    """Chua quet thi im lang - khong duoc doan bua khi chua co so lieu."""
    monkeypatch.setattr(TG, "kho_xep_loai", lambda: {})
    assert TG.canh_bao_cho_ma(["bat_ky"], "AUDCADmicro") == []


def test_cua_vao_kho_GIU_ty_le_cua_TUNG_chuoi():
    """`_ty_le_kich_hoat` mot so la khong du - phai biet no song o DAU.

    Truoc 15/09 cua vao kho `break` ngay o chuoi dau tien dat, nen
    `ty_le_than_nen` vao kho voi 0,5202 (cua XAUUSD) va khong mot cho nao trong
    he biet no la 0,000 tren toan bo FX.
    """
    s = (LAB / "nhan" / "ngu_phap.py").read_text(encoding="utf-8-sig")
    assert "_ty_le_theo_chuoi" in s, "cua vao kho khong giu bang ty le tung chuoi"
    i = s.index("da_do = [f\"chuoi kiem")
    khoi = s[i:i + 1800]
    j = khoi.index("for ten_ma, df_them in _chuoi_do_them()")
    assert "break" not in khoi[j:j + 700], (
        "cua vao kho van dung o chuoi dau tien dat - bang ty le se khuyet")


def test_tester_NOI_TRUOC_co_che_nao_se_ra_0_lenh():
    """Canh bao phai nam TRUOC luc sinh EA, khong phai sau khi doc ket qua."""
    s = (LAB / "chay_tester_kho.py").read_text(encoding="utf-8-sig")
    i = s.index("def _chay_trong_khoa")
    j = s.index("ma, dat = D.sinh_ea(", i)
    assert "thang_gia" in s[i:j], (
        "chay_tester_kho khong canh bao co che chet-vi-loi-khai truoc khi chay")
