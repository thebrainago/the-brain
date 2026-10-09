# -*- coding: utf-8 -*-
"""Test `nhan/swap_uoc.py`: uoc phi qua dem (swap) tu bang lenh cua MT5 tester (09/10/2026).

Khong can MT5 / du lieu gia: bang lenh tong hop + 3 bao cao tester THAT da co trong `reports/fixture/` (vang, chi mua)."""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhan import luoi as LU
from nhan import swap_uoc as SW

LAB = Path(__file__).resolve().parent
FIX = LAB / "reports" / "fixture"
T = pd.Timestamp


# ============================================================ 1. DEM SO DEM
def _dem_tham_chieu(mo, dong, triple=2):
    """Cach ngay tho nhat: di tung nua dem 00:00 nam TRONG (mo, dong); viet doc lap voi ban vector hoa."""
    mo, dong = T(mo), T(dong)
    if dong <= mo:
        return 0.0
    t, tong = mo.normalize() + pd.Timedelta(days=1), 0.0
    while t < dong:
        thu = (t - pd.Timedelta(days=1)).weekday()                 # thu cua ngay KET THUC o nua dem nay (thu Hai = 0)
        tong += 0.0 if thu >= 5 else (3.0 if triple is not None and thu == triple else 1.0)
        t += pd.Timedelta(days=1)
    return tong


@pytest.mark.parametrize("mo, dong, mong_doi", [
    ("2018-01-01 10:00", "2018-01-01 20:00", 0),      # thu Hai, trong ngay: khong qua nua dem
    ("2018-01-01 10:00", "2018-01-02 10:00", 1),      # thu Hai -> thu Ba
    ("2018-01-02 10:00", "2018-01-03 10:00", 1),      # thu Ba -> thu Tu
    ("2018-01-03 10:00", "2018-01-04 10:00", 3),      # thu Tu -> thu Nam: nua dem cuoi thu Tu tinh x3
    ("2018-01-04 10:00", "2018-01-05 10:00", 1),      # thu Nam -> thu Sau
    ("2018-01-05 10:00", "2018-01-06 10:00", 1),      # thu Sau -> thu Bay: nua dem cuoi thu Sau tinh 1
    ("2018-01-05 10:00", "2018-01-08 10:00", 1),      # cuoi tuan: thu Bay, Chu nhat KHONG tinh
    ("2018-01-06 10:00", "2018-01-07 10:00", 0),      # trong cuoi tuan
    ("2018-01-01 10:00", "2018-01-08 10:00", 7),      # dung 7 ngay lich = 7 dem
    ("2018-01-03 23:59:59", "2018-01-04 00:00:01", 3),   # qua nua dem thu Tu->thu Nam 2 giay
    ("2018-01-03 12:00", "2018-01-04 00:00:00", 0),   # dong DUNG luc nua dem: chua giu qua no
    ("2018-01-04 00:00:00", "2018-01-05 00:00:00", 0),   # mo DUNG luc nua dem (khong tinh) va dong DUNG luc nua dem (chua qua)
    ("2018-01-04 00:00:00", "2018-01-05 00:00:01", 1),   # ... qua nua dem sau 1 giay thi tinh (cuoi thu Nam = 1)
    ("2018-01-10 10:00", "2018-01-10 09:00", 0),      # dong truoc mo: 0, khong am
])
def test_so_dem_rollover_cac_diem_bien(mo, dong, mong_doi):
    assert SW.so_dem([T(mo)], [T(dong)])[0] == mong_doi
    assert _dem_tham_chieu(mo, dong) == mong_doi, "ban tham chieu cung phai ra dung so (kiem chinh test)"


def test_so_dem_khop_ban_tham_chieu_tren_nhieu_lenh_ngau_nhien():
    rng = np.random.RandomState(7)
    goc = T("2018-01-01")
    mo = goc + pd.to_timedelta(rng.randint(0, 24 * 60 * 730, 600), unit="m")
    mo = mo.where(rng.rand(600) > 0.2, mo.normalize())                       # 20% mo dung 00:00
    dai = pd.to_timedelta(rng.randint(0, 24 * 60 * 40, 600), unit="m")
    dai = dai.where(rng.rand(600) > 0.1, pd.Timedelta(0))                    # 10% dong ngay luc mo
    dong = mo + dai
    dong = dong.where(rng.rand(600) > 0.2, dong.normalize())                 # 20% dong dung 00:00 (co the truoc mo)
    for tri in (2, 4, None):
        got = SW.so_dem(mo, dong, triple=tri)
        mong = np.array([_dem_tham_chieu(a, b, tri) for a, b in zip(mo, dong)])
        assert np.array_equal(got, mong), (tri, np.flatnonzero(got != mong)[:5])


def test_so_dem_triple_doi_ngay_van_du_bay_dem_mot_tuan():
    for tri in (0, 1, 2, 3, 4):
        assert SW.so_dem([T("2018-01-01 10:00")], [T("2018-01-08 10:00")], triple=tri)[0] == 7
    # khong triple: cuoi tuan khong duoc bu -> 5 dem, KHONG phai 7 (co y: mode nay chi de so sanh, khong dung cho FX)
    assert SW.so_dem([T("2018-01-01 10:00")], [T("2018-01-08 10:00")], triple=None)[0] == 5


def test_so_dem_lien_tuc_la_so_ngay_lich_va_khong_am():
    got = SW.so_dem(pd.Series([T("2018-01-01 00:00"), T("2018-01-01 12:00")]), pd.Series([T("2018-01-02 12:00"), T("2018-01-01 00:00")]),
                    che_do="lien_tuc")
    assert got[0] == pytest.approx(1.5) and got[1] == 0.0


def test_so_dem_mui_gio_bi_bo_va_dau_vao_sai_bi_tu_choi():
    a = pd.DatetimeIndex([T("2018-01-03 10:00", tz="UTC")])
    b = pd.DatetimeIndex([T("2018-01-04 10:00", tz="UTC")])
    assert SW.so_dem(a, b)[0] == 3
    assert SW.so_dem([], []).shape == (0,)
    with pytest.raises(ValueError, match="cung do dai"):
        SW.so_dem([T("2018-01-03")], [T("2018-01-04"), T("2018-01-05")])
    with pytest.raises(ValueError, match="che_do"):
        SW.so_dem([T("2018-01-03")], [T("2018-01-04")], che_do="khac")


def test_cach_dem_theo_lop_ma():
    for ma in ("AUDCAD", "XM_AUDCAD", "TONG_HOP_1", "EURUSD", "USDJPY", "NZDCAD"):
        assert SW.cach_dem_cho(ma) == ("rollover", 2), ma
    for ma in ("XAUUSD", "US500", "US100", "BTCUSD", "KHONG_BIET"):
        assert SW.cach_dem_cho(ma) == ("lien_tuc", None), ma


# ============================================================ 2. TY LE
def test_ty_le_audcad_la_dung_hang_so_cua_engine():
    for ma in ("AUDCAD", "XM_AUDCAD", "TONG_HOP_3"):
        ty = SW.ty_le_cho(ma)
        assert ty["mua"] == LU.QC_AUDCAD.phi_nam_mua and ty["ban"] == LU.QC_AUDCAD.phi_nam_ban
        assert "QC_AUDCAD" in ty["nguon"]


def test_ty_le_ma_khac_lay_tu_thu_vien_chi_phi_va_ma_la_thi_khong_doan():
    ty = SW.ty_le_cho("EURUSD")
    assert ty and isinstance(ty["mua"], float) and isinstance(ty["ban"], float) and ty["nguon"] and ty["tin_cay"]
    assert SW.ty_le_cho("KHONG_CO_MA_NAY") is None
    assert SW.ty_le_cho("") is None


# ============================================================ 3. K
def _bang(n=60, k=71000.0, gia0=0.95, seed=3, lot=0.1, co_swap_cot=False, dau_loi=1.0):
    rng = np.random.RandomState(seed)
    mo = T("2018-01-02 09:00") + pd.to_timedelta(np.sort(rng.randint(0, 60 * 24 * 300, n)), unit="m")
    dong = mo + pd.to_timedelta(rng.randint(30, 60 * 24 * 12, n), unit="m")
    chieu = np.where(rng.rand(n) < 0.5, 1, -1)
    gm = gia0 + rng.randn(n) * 0.01
    gd = gm + rng.randn(n) * 0.004
    lots = np.full(n, lot)
    loi = np.round(dau_loi * chieu * lots * k * (gd - gm), 2)
    b = pd.DataFrame({"mo": mo, "dong": dong, "chieu": chieu, "lot": lots, "gia_mo": gm, "gia_dong": gd, "loi": loi})
    if co_swap_cot:
        b["swap"] = 0.0
    return b


def test_uoc_k_tien_tim_lai_hang_so_dung():
    b = _bang(n=80, k=71000.0)
    r = SW.uoc_k_tien(b)
    assert r["cach"] == "tong" and r["so_mau"] == 80
    assert r["k"] == pytest.approx(71000.0, rel=2e-3)


def test_uoc_k_tien_khong_doi_khi_ghep_nham_gia_dong_giua_cac_lenh_cung_chieu_cung_lot():
    """Cap cheo tien: tester co the ghep nham lenh vao / ra. Tong chieu*lot*(gia_dong - gia_mo) khong doi khi hoan vi gia_dong
    giua cac lenh CUNG chieu CUNG lot, nen K 'tong' van dung (con K 'tung_lenh' thi sai)."""
    b = _bang(n=80, k=71000.0)
    mua = (b["chieu"] == 1).to_numpy()
    b2 = b.copy()
    b2.loc[mua, "gia_dong"] = np.random.RandomState(1).permutation(b.loc[mua, "gia_dong"].to_numpy())
    assert SW.uoc_k_tien(b2)["k"] == pytest.approx(SW.uoc_k_tien(b)["k"], rel=1e-12)
    assert not np.allclose(b2["gia_dong"], b["gia_dong"]), "hoan vi phai that su doi tung lenh"


def test_uoc_k_tien_dung_cot_lai_khi_khong_co_cot_loi():
    b = _bang(n=60, k=100.0, lot=10.0).rename(columns={"loi": "lai"})
    assert SW.uoc_k_tien(b)["k"] == pytest.approx(100.0, rel=5e-3)


def test_uoc_k_tien_tu_choi_khi_khong_uoc_duoc():
    assert SW.uoc_k_tien(None) is None
    assert SW.uoc_k_tien(pd.DataFrame()) is None
    assert SW.uoc_k_tien(_bang(n=10)) is None, "it hon 20 lenh"
    ngu = _bang(n=60, dau_loi=-1.0)
    r = SW.uoc_k_tien(ngu)
    assert r is None or r["k"] > 0, "P&L nguoc dau voi gia: khong duoc tra K am"
    khong_dong = _bang(n=60)
    khong_dong["dong"] = pd.NaT
    assert SW.uoc_k_tien(khong_dong) is None


# ============================================================ 4. PHOI BAY VA SWAP
def _mot(chieu, mo, dong, lot=1.0, gm=1.0, gd=1.0):
    return pd.DataFrame({"mo": [T(mo)], "dong": [T(dong) if dong is not None else pd.NaT], "chieu": [chieu], "lot": [lot], "gia_mo": [gm],
                         "gia_dong": [gd if dong is not None else np.nan]})


def test_phoi_bay_bon_tuan_gia_khong_doi_khop_cong_thuc_tay():
    b = _mot(1, "2018-01-01 10:00", "2018-01-29 10:00", lot=2.0, gm=0.95, gd=0.95)           # 28 ngay lich = 28 dem
    p = SW.phoi_bay(b, 71000.0, ma="AUDCAD")
    assert p["che_do"] == "rollover" and p["so_lenh_tu_1_dem"] == 1
    assert p["A_mua"] == pytest.approx(2.0 * 71000.0 * 0.95 * 28 / 365.0) and p["A_ban"] == 0.0
    assert p["dem_lot_mua"] == 56.0 and p["dem_lot_ban"] == 0.0
    # cung vi the, SELL: A_ban
    s = SW.phoi_bay(_mot(-1, "2018-01-01 10:00", "2018-01-29 10:00", lot=2.0, gm=0.95, gd=0.95), 71000.0, ma="AUDCAD")
    assert s["A_mua"] == 0.0 and s["A_ban"] == pytest.approx(p["A_mua"])


def test_phoi_bay_khop_cong_thuc_tinh_swap_cua_engine_luoi():
    """Engine: phi_sw += lot*hop*ty_le*dem/365*gia (tien bao gia) roi / f. 28 dem, gia khong doi -> hai cach phai ra cung so."""
    ty = SW.ty_le_cho("AUDCAD")
    hop, f, lot, gia = 100000.0, 1.3, 1.5, 0.95
    b = _mot(-1, "2018-01-01 10:00", "2018-01-29 10:00", lot=lot, gm=gia, gd=gia)
    engine = -(lot * hop * ty["ban"] * 28 / 365.0 * gia) / f                               # am = ton tien
    r = SW.ap_ty_le(SW.phoi_bay(b, hop / f, ma="AUDCAD"), ty)
    assert r["nguon"] == "uoc" and r["swap"] == pytest.approx(engine, rel=1e-12)


def test_phoi_bay_lenh_con_mo_dung_gio_het_cua_so_va_khong_co_het_thi_lay_gio_dong_muon_nhat():
    b = pd.concat([_mot(1, "2018-01-01 10:00", None), _mot(1, "2018-01-02 10:00", "2018-01-03 10:00")], ignore_index=True)
    p = SW.phoi_bay(b, 100.0, het=T("2018-01-08 10:00"), ma="AUDCAD")
    assert p["dem_lot_mua"] == 7 + 1                                                          # thu Hai -> thu Hai sau: 7 dem; thu Ba -> thu Tu: 1 dem
    q = SW.phoi_bay(b, 100.0, ma="AUDCAD")                                                    # het = gio dong muon nhat = thu Tu 2018-01-03 10:00
    assert q["dem_lot_mua"] == 2 + 1


def test_phoi_bay_che_do_theo_lop_ma_va_ghi_de():
    b = _mot(1, "2018-01-03 10:00", "2018-01-04 22:00")
    assert SW.phoi_bay(b, 1.0, ma="EURUSD")["dem_lot_mua"] == 3
    v = SW.phoi_bay(b, 1.0, ma="XAUUSD")
    assert v["che_do"] == "lien_tuc" and v["dem_lot_mua"] == pytest.approx(36.0 / 24.0)
    assert SW.phoi_bay(b, 1.0, ma="EURUSD", che_do="lien_tuc", triple=None)["dem_lot_mua"] == pytest.approx(1.5)


def test_phoi_bay_bang_rong_khong_loi_va_k_xau_bi_tu_choi():
    p = SW.phoi_bay(pd.DataFrame(columns=["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong"]), 100.0, ma="EURUSD")
    assert p["so_lenh"] == 0 and p["A_mua"] == 0.0 and p["A_ban"] == 0.0
    for xau in (0.0, -5.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="k_tien"):
            SW.phoi_bay(_mot(1, "2018-01-01", "2018-01-02"), xau, ma="EURUSD")


def test_phoi_bay_bo_hang_khong_co_gio_mo():
    b = pd.concat([_mot(1, "2018-01-01 10:00", "2018-01-08 10:00"), _mot(1, "2018-01-01 10:00", "2018-01-08 10:00")], ignore_index=True)
    b.loc[1, "mo"] = pd.NaT
    p = SW.phoi_bay(b, 100.0, ma="AUDCAD")
    assert p["so_lenh"] == 1 and p["dem_lot_mua"] == 7


# ============================================================ 5. AP TY LE (dau + uu tien do)
def test_dau_swap_am_khi_tra_duong_khi_nhan():
    phoi = SW.phoi_bay(_mot(1, "2018-01-01 10:00", "2018-01-29 10:00", gm=1.0, gd=1.0), 1000.0, ma="AUDCAD")
    tra = SW.ap_ty_le(phoi, {"mua": 0.05, "ban": 0.0})
    nhan = SW.ap_ty_le(phoi, {"mua": -0.05, "ban": 0.0})
    assert tra["swap"] < 0 < nhan["swap"] and tra["swap"] == pytest.approx(-nhan["swap"])
    assert tra["swap"] == pytest.approx(-0.05 * 1000.0 * 28 / 365.0)


def test_swap_do_khac_0_thi_dung_so_do_khong_cong_uoc_them():
    phoi = SW.phoi_bay(_mot(1, "2018-01-01 10:00", "2018-01-29 10:00"), 1000.0, ma="AUDCAD")
    r = SW.ap_ty_le(phoi, {"mua": 0.05, "ban": 0.05}, swap_do=-12.5)
    assert r["nguon"] == "do" and r["swap"] == -12.5
    r0 = SW.ap_ty_le(phoi, {"mua": 0.05, "ban": 0.05}, swap_do=0.0)
    assert r0["nguon"] == "uoc"
    assert SW.ap_ty_le(phoi, {"mua": 0.05, "ban": 0.05}, swap_do=None)["nguon"] == "uoc"


def test_thieu_phoi_bay_hoac_ty_le_la_khong_uoc_duoc_va_khong_doan():
    phoi = SW.phoi_bay(_mot(1, "2018-01-01 10:00", "2018-01-29 10:00"), 1000.0, ma="AUDCAD")
    a = SW.ap_ty_le(None, {"mua": 0.1, "ban": 0.1})
    b = SW.ap_ty_le(phoi, None)
    assert a["nguon"] == b["nguon"] == "khong_uoc_duoc" and a["swap"] is None and b["swap"] is None
    assert a["ly"] and b["ly"] and b["phoi_bay"]["A_mua"] > 0, "van giu phoi bay de cloud doi ty le roi tinh lai"


def test_doi_ty_le_tinh_lai_tu_phoi_bay_da_luu_khong_can_bang_lenh():
    b = pd.concat([_mot(1, "2018-01-01 10:00", "2018-02-05 10:00", lot=1.0, gm=1.0, gd=1.0),
                   _mot(-1, "2018-01-01 10:00", "2018-02-05 10:00", lot=3.0, gm=1.0, gd=1.0)], ignore_index=True)
    phoi = SW.phoi_bay(b, 500.0, ma="AUDCAD")
    r = SW.ap_ty_le(phoi, None)
    mong = -(0.02 * phoi["A_mua"] + 0.06 * phoi["A_ban"])
    assert SW.doi_ty_le(r, 0.02, 0.06) == pytest.approx(mong)
    assert phoi["A_ban"] == pytest.approx(3 * phoi["A_mua"])
    assert SW.doi_ty_le({}, 0.02, 0.06) is None
    # tinh lai qua JSON (nhu luu vao ket qua / thu): khong mat do chinh xac
    r2 = json.loads(json.dumps(r))
    assert SW.doi_ty_le(r2, 0.02, 0.06) == pytest.approx(mong, rel=1e-12)


def test_doi_k_nhan_a_theo_ty_le_va_giu_so_dem_va_lot():
    b = pd.concat([_mot(1, "2018-01-01 10:00", "2018-02-05 10:00", lot=1.0, gm=1.0, gd=1.0),
                   _mot(-1, "2018-01-01 10:00", "2018-02-05 10:00", lot=3.0, gm=1.0, gd=1.0)], ignore_index=True)
    p = SW.phoi_bay(b, 500.0, ma="AUDCAD")
    q = SW.doi_k(p, 1500.0)
    assert q["k_tien"] == 1500.0 and q["A_mua"] == pytest.approx(3 * p["A_mua"]) and q["A_ban"] == pytest.approx(3 * p["A_ban"])
    assert q["dem_lot_mua"] == p["dem_lot_mua"] and q["dem_lot_ban"] == p["dem_lot_ban"] and q["so_lenh"] == p["so_lenh"]
    assert p["k_tien"] == 500.0, "ban goc khong bi sua"
    # phoi doi K = phoi tinh thang voi K moi (A tuyen tinh theo K)
    thang = SW.phoi_bay(b, 1500.0, ma="AUDCAD")
    assert q["A_mua"] == pytest.approx(thang["A_mua"], rel=1e-12) and q["A_ban"] == pytest.approx(thang["A_ban"], rel=1e-12)
    # va swap tinh tu phoi doi K = swap tinh thang
    ty = SW.ty_le_cho("AUDCAD")
    assert SW.ap_ty_le(q, ty)["swap"] == pytest.approx(SW.ap_ty_le(thang, ty)["swap"], rel=1e-12)


def test_doi_k_none_di_thang_va_k_khong_hop_le_bi_tu_choi():
    assert SW.doi_k(None, 5.0) is None and SW.doi_k({}, 5.0) == {}
    p = SW.phoi_bay(_mot(1, "2018-01-01 10:00", "2018-01-29 10:00"), 100.0, ma="AUDCAD")
    for xau in (0.0, -3.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            SW.doi_k(p, xau)
    with pytest.raises(ValueError):
        SW.doi_k({**p, "k_tien": 0.0}, 5.0)


# ============================================================ 6. TRON GOI TREN BANG LENH
def test_uoc_cho_bang_tron_goi_audcad_dung_hang_so_engine():
    b = _bang(n=70, k=71000.0, co_swap_cot=True)
    r = SW.uoc_cho_bang(b, "AUDCAD")
    assert r["nguon"] == "uoc" and r["ty_le"]["mua"] == LU.QC_AUDCAD.phi_nam_mua
    p = r["phoi_bay"]
    assert r["swap"] == pytest.approx(-(LU.QC_AUDCAD.phi_nam_mua * p["A_mua"] + LU.QC_AUDCAD.phi_nam_ban * p["A_ban"]))
    assert p["k_tien"] == pytest.approx(71000.0, rel=2e-3) and p["k_cach"] == "tong"
    assert SW.uoc_cho_bang(b, "AUDCAD", k_tien=71000.0)["phoi_bay"]["k_cach"] == "cho"


def test_uoc_cho_bang_swap_tester_khac_0_la_do_khong_phai_uoc():
    b = _bang(n=70, k=71000.0, co_swap_cot=True)
    b.loc[5, "swap"] = -3.21
    b.loc[9, "swap"] = np.nan
    r = SW.uoc_cho_bang(b, "AUDCAD")
    assert r["nguon"] == "do" and r["swap"] == pytest.approx(-3.21) and "phoi_bay" not in r


def test_uoc_cho_bang_khong_uoc_duoc_thi_noi_ly_do():
    ngan = _bang(n=8, co_swap_cot=True)
    r = SW.uoc_cho_bang(ngan, "AUDCAD")
    assert r["nguon"] == "khong_uoc_duoc" and "K" in r["ly"] and r["swap"] is None
    la = SW.uoc_cho_bang(_bang(n=70, co_swap_cot=True), "KHONG_CO_MA_NAY")
    assert la["nguon"] == "khong_uoc_duoc" and "ty le" in la["ly"]


def test_uoc_cho_bang_bang_k_rieng():
    b = _bang(n=70, k=100.0, lot=10.0, co_swap_cot=True)
    bk = b.copy()
    bk["loi"] = bk["loi"] * 2.0                                       # bang K cho K = 200: phai thay doi phoi bay gap doi
    r1 = SW.uoc_cho_bang(b, "AUDCAD")
    r2 = SW.uoc_cho_bang(b, "AUDCAD", bang_k=bk)
    assert r2["phoi_bay"]["k_tien"] == pytest.approx(2 * r1["phoi_bay"]["k_tien"], rel=1e-9)


# ============================================================ 7. BAO CAO TESTER THAT (3 bao cao vang, chi mua)
@pytest.mark.parametrize("ten", ["cancubo_kp", "cancubo_xn", "vamge10k_kp"])
def test_bao_cao_tester_that_swap_bang_0_va_uoc_ra_so_am(ten):
    p = FIX / ("tester_%s_deals.csv.gz" % ten)
    r = SW.uoc_tu_bao_cao(p, "XAUUSD")
    assert r["bang_doc_duoc"] is True and r["nguon"] == "uoc", r.get("ly")
    ph = r["phoi_bay"]
    assert ph["k_tien"] == pytest.approx(100.0, rel=1e-6), "vang: hop dong 100 oz tren tai khoan USD -> K = 100"
    assert ph["che_do"] == "lien_tuc" and ph["so_lenh"] > 1000
    ty = SW.ty_le_cho("XAUUSD")
    assert r["swap"] == pytest.approx(-(ty["mua"] * ph["A_mua"] + ty["ban"] * ph["A_ban"]))
    assert r["swap"] < 0, "mua vang tra swap"


def test_bao_cao_tester_that_ma_chua_do_duoc_thi_giu_phoi_bay_cho_cloud():
    r = SW.uoc_tu_bao_cao(FIX / "tester_cancubo_kp_deals.csv.gz", "GOLD.i#")
    assert r["bang_doc_duoc"] is True and r["nguon"] == "khong_uoc_duoc" and r["phoi_bay"]["A_mua"] > 0


def test_bao_cao_khong_co_tep_thi_none_va_bao_cao_hong_thi_khong_doc_duoc_bang(tmp_path):
    assert SW.uoc_tu_bao_cao(None, "XAUUSD") is None
    assert SW.uoc_tu_bao_cao({"lai_rong": 1.0}, "XAUUSD") is None
    assert SW.uoc_tu_bao_cao(tmp_path / "khong_co.htm", "XAUUSD") is None
    rac = tmp_path / "rac.htm"
    rac.write_text("<html><body>khong co bang Deals</body></html>", encoding="utf-8")
    r = SW.uoc_tu_bao_cao(rac, "XAUUSD")
    assert r["bang_doc_duoc"] is False and r["nguon"] == "khong_uoc_duoc" and r["swap"] is None and r["ly"]


# ============================================================ 8. QUET HANG HIEU CHUAN DA LUU
def _ghi_hang(thu_muc: Path, ten: str, b: pd.DataFrame, hop=100000.0, f=1.3, co_bang=True):
    bang = thu_muc / (ten + "_lenh.csv.gz")
    if co_bang:
        b.to_csv(bang, index=False, compression="gzip")
    r = {"trang_thai": "DAT", "ma": "AUDCAD", "khung": "M15", "cua_so": {"tu": "2018.01.02", "den": "2018.12.31", "ngay": 364}, "von": 10000.0,
         "he_so_quy_doi": {"dung": f}, "tester": {"lai_nam_pct": 3.5, "bang_lenh": str(bang), "thong_ke": {"swap": 0.0}},
         "engine": {"lai_nam_pct": 5.0, "qc": {"hop_dong": hop}, "thong_ke": {"swap": -150.0}}}
    (thu_muc / (ten + ".json")).write_text(json.dumps(r), encoding="utf-8")
    return r


def test_quet_hieu_chuan_gom_phoi_bay_va_bo_qua_hang_hong(tmp_path):
    b = _bang(n=70, k=100000.0 / 1.3, co_swap_cot=True)
    _ghi_hang(tmp_path, "hang_tot", b)
    _ghi_hang(tmp_path, "hang_mat_bang", b, co_bang=False)
    (tmp_path / "chi_engine.json").write_text(json.dumps({"trang_thai": "CHUA_DO_DUOC", "engine": {}}), encoding="utf-8")
    (tmp_path / "hong.json").write_text("{khong phai json", encoding="utf-8")
    ra = tmp_path / "ra" / "swap.json"
    out = SW.quet_hieu_chuan(tmp_path, ra)
    assert out["so_hang"] == 1 and list(out["cac_hang"]) == ["hang_tot"] and out["so_bo_qua"] == 3
    h = out["cac_hang"]["hang_tot"]
    assert h["phoi_bay"]["k_tien"] == pytest.approx(100000.0 / 1.3) and h["swap_tester_do"] == 0.0
    assert h["lai_tester_pct_nam"] == 3.5 and h["swap_engine"] == -150.0
    assert h["phoi_bay"]["A_mua"] > 0 and h["phoi_bay"]["A_ban"] > 0
    luu = json.loads(ra.read_text(encoding="utf-8"))
    assert luu["so_hang"] == 1 and len(ra.read_text(encoding="utf-8")) < 4000, "ban nho de dua cho cloud qua git"
    assert luu["phan"] == ["swap_p01.json"] and out["tep_ra"] == ["swap.json", "swap_p01.json"]
    doc = SW.giai_gom(luu, {"swap_p01.json": (ra.parent / "swap_p01.json").read_text(encoding="utf-8")})
    assert doc["hang_tot"]["A_mua"] == pytest.approx(h["phoi_bay"]["A_mua"]) and doc["hang_tot"]["lai_engine"] == 5.0
    # lan quet sau khong doc lai chinh tep ra (ten bat dau bang swap_)
    ra2 = tmp_path / "swap_gom.json"
    SW.quet_hieu_chuan(tmp_path, ra2)
    assert SW.quet_hieu_chuan(tmp_path)["so_hang"] == 1


def test_cli_quet_va_mot_bang(tmp_path, capsys):
    b = _bang(n=70, k=100000.0 / 1.3, co_swap_cot=True)
    _ghi_hang(tmp_path, "h1", b)
    assert SW.main_cli(["--quet", str(tmp_path)]) == 0
    assert "1 hang" in capsys.readouterr().out
    f = tmp_path / "bang.csv"
    b.to_csv(f, index=False)
    assert SW.main_cli([str(f), "--ma", "AUDCAD"]) == 0
    assert json.loads(capsys.readouterr().out)["nguon"] == "uoc"
    assert SW.main_cli([str(f), "--ma", "AUDCAD", "--mua", "0.01", "--ban", "0.02", "--k", "50000"]) == 0
    r = json.loads(capsys.readouterr().out)
    assert r["ty_le"]["mua"] == 0.01 and r["phoi_bay"]["k_tien"] == 50000.0
    assert SW.main_cli([]) == 2
    assert SW.main_cli(["--quet", str(tmp_path / "khong_co_thu_muc")]) == 1


# ---- chia phan: bo chay may nha chi mang theo 40.000 ky tu / tep, 300.000 / don
def _hang_ao(i: int) -> dict:
    return {"ma": "AUDCAD", "khung": "M15", "cua_so": ["2018.01.02", "2018.12.31", 364], "von": 10000.0,
            "phoi_bay": {"che_do": "rollover", "triple": 2, "k_tien": 76923.076923 + i, "so_lenh": 70 + i, "so_lenh_tu_1_dem": 60,
                         "A_mua": 4390.276104 + i, "A_ban": 4430.864311 + i, "dem_lot_mua": 21.9, "dem_lot_ban": 22.1},
            "swap_tester_do": 0.0, "lai_tester_pct_nam": 3.5 + i / 100.0, "lai_engine_pct_nam": 5.0, "swap_engine": -150.0,
            "ty_le_engine": [-0.00263, 0.03853]}


def _out_ao(n: int) -> dict:
    cac = {"AUDCAD_M15_2018.01.02_2018.12.31_%040x_e4" % i: _hang_ao(i) for i in range(n)}
    return {"thu_muc": "reports/hieu_chuan", "cac_hang": cac, "so_hang": n, "so_bo_qua": 5,
            "bo_qua": {"x%d.json" % i: "mat bang lenh y%d_lenh.csv.gz" % i for i in range(5)}}


def _doc_het(thu_muc: Path, ten: list[str]) -> tuple[dict, dict]:
    man = json.loads((thu_muc / ten[0]).read_text(encoding="utf-8"))
    return man, {t: (thu_muc / t).read_text(encoding="utf-8") for t in man["phan"]}


def test_ghi_gom_chia_phan_khong_vuot_gioi_han_khong_mat_hang_va_doc_nguoc_dung(tmp_path):
    out = _out_ao(400)
    ten = SW.ghi_gom(out, tmp_path / "swap_gom.json")
    assert ten[0] == "swap_gom.json" and ten[1:] == ["swap_gom_p%02d.json" % i for i in range(1, len(ten))] and len(ten) >= 3
    for t in ten:
        assert len((tmp_path / t).read_text(encoding="utf-8")) <= SW.PHAN_TOI_DA, t
    man, phan = _doc_het(tmp_path, ten)
    assert man["so_hang"] == 400 and man["so_hang_khong_vua"] == 0 and man["phan"] == ten[1:]
    assert man["bo_qua_theo_ly_do"] == {"mat bang lenh": 5} and len(man["bo_qua"]) == 5
    doc = SW.giai_gom(man, phan)
    assert list(doc) == list(out["cac_hang"]), "du hang, dung thu tu, khong trung"
    for k, h in out["cac_hang"].items():
        d = doc[k]
        assert d["A_mua"] == pytest.approx(h["phoi_bay"]["A_mua"]) and d["A_ban"] == pytest.approx(h["phoi_bay"]["A_ban"])
        assert d["ty_mua"] == -0.00263 and d["ty_ban"] == 0.03853 and d["den"] == "2018.12.31" and d["tu"] == "2018.01.02"
        assert d["von"] == 10000.0 and d["so_lenh"] == h["phoi_bay"]["so_lenh"] and d["swap_engine"] == -150.0
        assert d["lai_tester"] == h["lai_tester_pct_nam"] and d["k_tien"] == pytest.approx(h["phoi_bay"]["k_tien"])


def test_ghi_gom_dong_goi_chat_phan_nao_tru_phan_cuoi_khong_nhet_them_duoc_mot_hang(tmp_path, monkeypatch):
    out = _out_ao(60)
    khoa0, h0 = next(iter(out["cac_hang"].items()))
    n_hang = len(json.dumps([khoa0, SW._hang_gon(h0)], separators=(",", ":"))) + 2          # dung cach dem cua ghi_gom ("khoa":[...],)
    khung = len(json.dumps({"cot": list(SW.COT_GOM), "hang": {}}, separators=(",", ":")))
    gioi = 10 * n_hang + 50                      # < khung + 10 hang: neu quen tinh khung rong thi mot phan se vuot gioi han
    assert khung > 60, "test chi co nghia khi khung rong lon hon do tre 50 o tren"
    monkeypatch.setattr(SW, "PHAN_TOI_DA", gioi)
    ten = SW.ghi_gom(out, tmp_path / "swap_gom.json")
    man, phan = _doc_het(tmp_path, ten)
    do_dai = [len((tmp_path / t).read_text(encoding="utf-8")) for t in man["phan"]]
    assert len(do_dai) >= 6 and all(d <= gioi for d in do_dai), do_dai
    assert all(d + n_hang > gioi for d in do_dai[:-1]), "phan bi bo trong qua nhieu: %s" % do_dai
    assert len(SW.giai_gom(man, phan)) == 60


def test_ghi_gom_tran_tong_thi_dem_va_noi_ro_khong_im_lang(tmp_path, monkeypatch):
    monkeypatch.setattr(SW, "TONG_TOI_DA", 4000)
    out = _out_ao(100)
    ten = SW.ghi_gom(out, tmp_path / "swap_gom.json")
    man, phan = _doc_het(tmp_path, ten)
    doc = SW.giai_gom(man, phan)
    assert 0 < len(doc) < 100 and len(doc) + man["so_hang_khong_vua"] == 100
    assert list(doc) == list(out["cac_hang"])[:len(doc)], "giu cac hang DAU, bo cac hang cuoi"


def test_ghi_gom_hang_qua_to_bi_dem_khong_lam_hong_tep_va_khong_keo_theo_hang_khac(tmp_path):
    out = _out_ao(3)
    ks = list(out["cac_hang"])
    out["cac_hang"][ks[1]]["ma"] = "X" * (SW.PHAN_TOI_DA + 10)
    ten = SW.ghi_gom(out, tmp_path / "swap_gom.json")
    man, phan = _doc_het(tmp_path, ten)
    assert man["so_hang_khong_vua"] == 1 and list(SW.giai_gom(man, phan)) == [ks[0], ks[2]]
    for t in ten:
        json.loads((tmp_path / t).read_text(encoding="utf-8"))


def test_ghi_gom_khong_co_hang_nao_van_ra_tep_tong_hop_le(tmp_path):
    out = {"thu_muc": "x", "cac_hang": {}, "bo_qua": {"a.json": "khong phai ket qua hieu chuan day du"}, "so_hang": 0, "so_bo_qua": 1}
    ten = SW.ghi_gom(out, tmp_path / "swap_gom.json")
    assert ten == ["swap_gom.json"]
    man = json.loads((tmp_path / "swap_gom.json").read_text(encoding="utf-8"))
    assert man["phan"] == [] and man["so_hang"] == 0 and SW.giai_gom(man, {}) == {}


def test_giai_gom_thieu_phan_thi_bao_loi_chu_khong_tra_ban_thieu(tmp_path):
    ten = SW.ghi_gom(_out_ao(300), tmp_path / "swap_gom.json")
    man, phan = _doc_het(tmp_path, ten)
    phan.pop(man["phan"][-1])
    with pytest.raises(ValueError, match="thieu phan"):
        SW.giai_gom(man, phan)


def test_720_hang_that_vua_mot_don_duoi_tran_300k_cua_bo_chay(tmp_path):
    """720 = 286 hang da luu + 434 phep do: toan bo phai nam trong ngan sach mot don (tep_moi cat o 300.000 ky tu tong / 40.000 moi tep)."""
    ten = SW.ghi_gom(_out_ao(720), tmp_path / "swap_gom.json")
    man, phan = _doc_het(tmp_path, ten)
    tong = sum(len((tmp_path / t).read_text(encoding="utf-8")) for t in ten)
    assert man["so_hang_khong_vua"] == 0 and len(SW.giai_gom(man, phan)) == 720
    assert tong < 300_000 and max(len((tmp_path / t).read_text(encoding="utf-8")) for t in ten) < 40_000


def test_quet_ra_mang_theo_duoc_nguyen_ven_bang_tep_moi_cua_bo_chay(tmp_path):
    """Duong that cua don `00s-swap-gom`: lenh --quet ghi ra reports/ -> `cau_git.tep_moi` nhet vao ket qua -> cloud doc nguoc. Khong mat hang, khong tep hong."""
    import os
    import time
    from qwen import cau_git as CG
    thu = tmp_path / "reports" / "hieu_chuan"
    thu.mkdir(parents=True)
    b = _bang(n=70, k=100000.0 / 1.3, co_swap_cot=True)
    for i in range(150):
        _ghi_hang(thu, "AUDCAD_M15_2018.01.02_2018.12.31_%016x_e4" % (i * 7919), b)
    cu = time.time() - 86400.0
    for f in thu.iterdir():
        os.utime(f, (cu, cu))                              # tep cu: tep_moi KHONG mang theo (chi mang tep do don vua ghi)
    t0 = time.time()
    assert SW.main_cli(["--quet", str(thu), "--ra", str(thu / "swap_gom.json")]) == 0
    tep = CG.tep_moi(t0, lab=tmp_path)
    ten = sorted(tep)
    assert ten[0] == "reports/hieu_chuan/swap_gom.json" and len(ten) >= 2, ten
    assert all(len(v) < 40_000 for v in tep.values()) and sum(len(v) for v in tep.values()) < 300_000
    man = json.loads(tep[ten[0]])
    doc = SW.giai_gom(man, {k.rsplit("/", 1)[-1]: v for k, v in tep.items()})
    assert man["so_hang"] == 150 and man["so_hang_khong_vua"] == 0 and len(doc) == 150 and all(h["A_mua"] > 0 for h in doc.values())


def test_cli_quet_in_ten_cac_tep_ra(tmp_path, capsys):
    _ghi_hang(tmp_path, "h1", _bang(n=70, k=100000.0 / 1.3, co_swap_cot=True))
    assert SW.main_cli(["--quet", str(tmp_path), "--ra", str(tmp_path / "swap_gom.json")]) == 0
    o = capsys.readouterr().out
    assert "swap_gom.json" in o and "swap_gom_p01.json" in o


# ============================================================ 9. QUY UOC CUA DU AN
def _ten_cam() -> re.Pattern:
    return re.compile("|".join(("cla" + "ude", "son" + "net", "op" + "us", "hai" + "ku", "fa" + "ble")), re.I)


def test_file_moi_chi_co_ascii_va_khong_ten_mo_hinh():
    for p in (Path(SW.__file__), Path(__file__)):
        van = p.read_text(encoding="utf-8")
        assert van.isascii(), (p.name, [c for c in van if ord(c) > 127][:5])
        m = _ten_cam().search(van.replace("CLAUDE.md", ""))
        assert m is None, (p.name, m and van[max(0, m.start() - 30): m.end() + 30])


def test_module_da_xep_lop_trong_so_do_kien_truc():
    from nhan import kien_truc as KT
    assert any("swap_uoc" in v[1] for v in KT.LOP.values()), "nhan/kien_truc.LOP phai liet ke swap_uoc"
