# -*- coding: utf-8 -*-
"""Kiem `bo_thu_mo_phong`: bo thu cac phuong an mo phong, so TUNG LENH voi bang lenh MT5 tester.

Ba tang:
  1. Ham thuan (khong can trinh bien dich): doc o hieu chuan, gop nen M1, quy gia BID, ghep lenh, so sanh, xep hang, cau hinh bien the.
  2. Engine nen (`luoi.chay_mang`) tren M1 tong hop: so voi cong thuc DOC LAP (lai truoc swap = (lai_rong + lai treo + phi swap) / f).
  3. KIEM CO DAP AN (can g++/clang++): "tester" = CHINH EA tren tick sinh tu M1 theo MOT thu tu da biet; bo thu PHAI tim lai dung thu tu do
     (khop 100% lenh) va xep no dau - neu khong, bo thu khong phan biet duoc mo phong tot voi xau.
"""
from __future__ import annotations

import dataclasses
import json
import math

import numpy as np
import pandas as pd
import pytest

from nhan import bo_thu_mo_phong as B
from nhan import ea_gia_lap as G
from nhan import luoi as LU

T = pd.Timestamp
can_cxx = pytest.mark.skipif(G.trinh_bien_dich() is None, reason="khong co g++ / clang++ (hoac EA_GIA_LAP_CXX)")
TS_VUA = dict(buoc=6.0, tp=5.0, tran_tang=5, che_do="hai_chieu", lot=0.01, tia_lenh=True, bien_cap=2.0)
KHOA = "0123456789abcdef"


# ----------------------------------------------------------------------------------------------------------------- dung cu
def _bc(ma="audcad", khung="m15", tu="2019.01.01", den="2019.03.31", ngay=90, von=10000.0, f=1.32, q=100.0, khoa=KHOA, lai_t=500.0,
        n_t=100, lai_e=700.0, swap_e=-50.0, ts=None, qc=None, co_khoa=True, co_so_khoa=True):
    """Bao cao `reports/hieu_chuan/*.json` toi thieu (cung bo cuc voi bao cao that cua may nha)."""
    es = {"thong_ke": {"lai_chua_swap": lai_e, "swap": swap_e}}
    if qc is not None:
        es["qc"] = qc
    bc = {"ma": ma, "khung": khung, "von": von, "phien_ban_engine": 4, "cua_so": {"tu": tu, "den": den, "ngay": ngay},
          "he_so_quy_doi": {"dung": f}, "tham_so": dict(TS_VUA if ts is None else ts),
          "tester": {"chat_luong_pct": q, "bang_lenh": ("reports/hieu_chuan/%s_lenh.csv.gz" % khoa) if co_khoa else None,
                     "thong_ke": {"lai_chua_swap": lai_t, "swap": 0.0, "so_lenh_mo": n_t}},
          "engine": es}
    if co_so_khoa:
        bc["so_khoa"] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    return bc


def _ca(**kw):
    return B.ca_tu_bao_cao(_bc(**kw), "ten")


def _don(thu_muc, ten, bc, duong="reports/hieu_chuan/A_e4.json", luc="2026-10-09T10:00:00", lenh=("{py}", "b.py", "nc", "cc", "hieu_chuan_luoi", "{}"),
         co_tep=True):
    b = {"lenh": list(lenh), "dong_cuoi": [' "bao_cao": "%s", "so_khoa": [1, 2, 3, 4, 5, 6]' % duong],
         "tep_moi": ({duong: json.dumps(bc)} if co_tep else {})}
    (thu_muc / ("%s.json" % ten)).write_text(json.dumps({"ma": ten, "luc": luc, "bang_chung": b}), "utf-8")


def _m1_nho(n=30):
    ix = pd.date_range("2019-01-02 00:00", periods=n, freq="1min", name="time")
    o = np.arange(n, dtype=float) + 100.0
    return pd.DataFrame({"open": o, "high": o + 2.0, "low": o - 1.0, "close": o + 1.0, "tick_volume": 10, "spread": np.arange(n) + 1.0}, index=ix)


def _lenh(mo, chieu, bid, dong=None, bid_dong=np.nan, lot=0.01, lai=0.0):
    return dict(mo=T(mo), dong=T(dong) if dong else pd.NaT, chieu=chieu, lot=lot, bid_mo=bid, bid_dong=bid_dong, lai=lai)


def _bang(*rows):
    return pd.DataFrame(list(rows))


def _ca_tay(m1, ts=None, ngay=3, von=10000.0, f=1.32):
    return B.Ca(ten="x", ma="AUDCAD", khung="M15", tu=m1.index[0], den_het=m1.index[-1], ngay=ngay, von=von, f=f,
                ts=dict(TS_VUA if ts is None else ts), khoa=None, q=100.0, qc={}, so_khoa=None)


# =============================================================================================================== 1. CA
def test_ca_tu_bao_cao_doc_dung_cac_truong():
    ca = _ca(qc={"phi_nam_mua": -0.1, "phi_nam_ban": 0.2, "pip": 0.0001})
    assert ca.ma == "AUDCAD" and ca.khung == "M15"                       # viet hoa
    assert ca.tu == T("2019-01-01") and ca.den_het == T("2019-03-31 23:59:59")
    assert (ca.ngay, ca.von, ca.f, ca.q, ca.khoa) == (90, 10000.0, 1.32, 100.0, KHOA)
    assert ca.nam == pytest.approx(90 / 365.25)
    assert (ca.t_truoc, ca.n_t, ca.pb) == (500.0, 100, 4)
    assert ca.e_truoc_nam == pytest.approx(700.0 / 10000.0 / (90 / 365.25) * 100.0)       # engine TRUOC swap, %/nam
    assert ca.so_khoa == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
    assert ca.qc == {"phi_nam_mua": -0.1, "phi_nam_ban": 0.2}            # chi hai khoan phi, khong pip / hop dong
    assert ca.ts["buoc"] == 6.0


def test_ca_bao_cao_cu_khong_ghi_phi_thi_qc_rong_va_so_khoa_thieu_thi_none():
    ca = _ca(co_so_khoa=False)
    assert ca.qc == {} and ca.so_khoa is None


def test_ca_ngay_lay_tu_cua_so_hoac_tu_hai_dau_moc():
    bc = _bc()
    del bc["cua_so"]["ngay"]
    assert B.ca_tu_bao_cao(bc, "t").ngay == 90                           # 01/01 .. 31/03 gom ca hai dau


@pytest.mark.parametrize("truong", ["ma", "khung", "cua_so", "von", "tham_so", "he_so_quy_doi", "tester"])
def test_ca_thieu_truong_bat_buoc_thi_bao_ro_ten(truong):
    bc = _bc()
    del bc[truong]
    with pytest.raises(ValueError, match=truong):
        B.ca_tu_bao_cao(bc, "t")


@pytest.mark.parametrize("sua", [lambda b: b["he_so_quy_doi"].update(dung=0.0), lambda b: b["he_so_quy_doi"].update(dung=float("nan")),
                                 lambda b: b["he_so_quy_doi"].update(dung=float("inf")),
                                 lambda b: b["he_so_quy_doi"].update(dung=-1.0), lambda b: b.update(von=-5.0),
                                 lambda b: b.update(von=float("inf")), lambda b: b.update(von=0.0),
                                 lambda b: b["cua_so"].update(ngay=0, tu="2019.01.02", den="2019.01.01"),
                                 lambda b: b["cua_so"].update(tu="khong phai ngay")])
def test_ca_so_vo_ly_bi_tu_choi(sua):
    bc = _bc()
    sua(bc)
    with pytest.raises(ValueError):
        B.ca_tu_bao_cao(bc, "t")


def test_ca_khong_phai_object_json():
    with pytest.raises(ValueError):
        B.ca_tu_bao_cao([1, 2], "t")


@pytest.mark.parametrize("duong", [None, "reports/hieu_chuan/ngan_lenh.csv.gz", "reports/hieu_chuan/XYZXYZXYZXYZXYZX_lenh.csv.gz"])
def test_ca_bang_lenh_khong_hop_le_thi_khoa_none(duong):
    bc = _bc()
    bc["tester"]["bang_lenh"] = duong
    assert B.ca_tu_bao_cao(bc, "t").khoa is None


def test_doc_cac_ca_loc_o_sach_va_ghi_ly_do_bo_qua(tmp_path):
    _don(tmp_path, "sach", _bc(q=100.0), duong="reports/hieu_chuan/A_e4.json")
    _don(tmp_path, "nhiem", _bc(q=51.0, ma="NZDCAD"), duong="reports/hieu_chuan/B_e4.json")
    _don(tmp_path, "khong_ro", _bc(q=None, ma="EURCAD"), duong="reports/hieu_chuan/C_e4.json")
    _don(tmp_path, "khong_phai_hc", _bc(), duong="reports/hieu_chuan/D_e4.json", lenh=("{py}", "b.py", "nc", "cc", "quet_luoi"))
    _don(tmp_path, "thieu_tep", _bc(), duong="reports/hieu_chuan/E_e4.json", co_tep=False)
    bc_hong = _bc()
    del bc_hong["von"]
    _don(tmp_path, "bao_cao_hong", bc_hong, duong="reports/hieu_chuan/F_e4.json")
    _don(tmp_path, "khong_bang_lenh", _bc(co_khoa=False), duong="reports/hieu_chuan/G_e4.json")
    (tmp_path / "rac.json").write_text("{khong phai json", "utf-8")
    cac, bo = B.doc_cac_ca(str(tmp_path))
    assert [c.ten for c in cac] == ["reports/hieu_chuan/A_e4.json"]
    assert set(bo) == {"reports/hieu_chuan/B_e4.json", "reports/hieu_chuan/C_e4.json", "reports/hieu_chuan/E_e4.json",
                       "reports/hieu_chuan/F_e4.json", "reports/hieu_chuan/G_e4.json"}
    assert "51" in bo["reports/hieu_chuan/B_e4.json"] and "nhiem" in bo["reports/hieu_chuan/B_e4.json"]
    assert "von" in bo["reports/hieu_chuan/F_e4.json"]
    assert "bang lenh" in bo["reports/hieu_chuan/G_e4.json"]


def test_doc_cac_ca_lay_ca_nhiem_khi_duoc_hoi(tmp_path):
    _don(tmp_path, "nhiem", _bc(q=51.0), duong="reports/hieu_chuan/B_e4.json")
    cac, bo = B.doc_cac_ca(str(tmp_path), chi_sach=False)
    assert len(cac) == 1 and not bo


def test_doc_cac_ca_nguong_chat_luong_la_95_va_gom_dung_bien(tmp_path):
    _don(tmp_path, "a", _bc(q=95.0), duong="reports/hieu_chuan/A_e4.json")
    _don(tmp_path, "b", _bc(q=94.99), duong="reports/hieu_chuan/B_e4.json")
    cac, bo = B.doc_cac_ca(str(tmp_path))
    assert [c.ten for c in cac] == ["reports/hieu_chuan/A_e4.json"] and "reports/hieu_chuan/B_e4.json" in bo
    assert B.NGUONG_CHAT_LUONG == 95.0


def test_doc_cac_ca_cung_bao_cao_chay_hai_lan_giu_lan_moi_nhat(tmp_path):
    _don(tmp_path, "cu", _bc(q=51.0), luc="2026-10-08T10:00:00")
    _don(tmp_path, "moi", _bc(q=100.0), luc="2026-10-09T10:00:00")
    cac, bo = B.doc_cac_ca(str(tmp_path))
    assert len(cac) == 1 and cac[0].q == 100.0 and not bo
    # va nguoc lai: lan sau cua bao cao thanh o nhiem thi bao cao do khong con trong o sach
    for f in tmp_path.glob("*.json"):
        f.unlink()
    _don(tmp_path, "cu", _bc(q=100.0), luc="2026-10-08T10:00:00")
    _don(tmp_path, "moi", _bc(q=51.0), luc="2026-10-09T10:00:00")
    cac, bo = B.doc_cac_ca(str(tmp_path))
    assert not cac and "reports/hieu_chuan/A_e4.json" in bo


def test_doc_cac_ca_ban_cu_hong_ban_moi_tot_thi_khong_con_trong_danh_sach_bo_qua(tmp_path):
    cu = _bc()
    del cu["von"]
    _don(tmp_path, "cu", cu, luc="2026-10-08T10:00:00")
    _don(tmp_path, "moi", _bc(q=100.0), luc="2026-10-09T10:00:00")
    cac, bo = B.doc_cac_ca(str(tmp_path))
    assert len(cac) == 1 and not bo


def test_doc_cac_ca_sap_theo_ma_roi_ngay(tmp_path):
    _don(tmp_path, "1", _bc(ma="NZDCAD", tu="2019.01.01"), duong="reports/hieu_chuan/1_e4.json")
    _don(tmp_path, "2", _bc(ma="AUDCAD", tu="2019.07.01", den="2019.09.30"), duong="reports/hieu_chuan/2_e4.json")
    _don(tmp_path, "3", _bc(ma="AUDCAD", tu="2019.01.01"), duong="reports/hieu_chuan/3_e4.json")
    cac, _ = B.doc_cac_ca(str(tmp_path))
    assert [(c.ma, c.tu.month) for c in cac] == [("AUDCAD", 1), ("AUDCAD", 7), ("NZDCAD", 1)]


# =============================================================================================================== 2. GIA M1
def test_gop_khung_ohlc_dung_tung_o():
    m1 = _m1_nho()
    m5 = B.gop_khung(m1, "M5")
    assert len(m5) == 6 and m5.index[0] == T("2019-01-02 00:00") and m5.index[1] == T("2019-01-02 00:05")
    r0, r1 = m5.iloc[0], m5.iloc[1]
    assert (r0.open, r0.high, r0.low, r0.close, r0.tick_volume) == (100.0, 106.0, 99.0, 105.0, 50)
    assert (r1.open, r1.high, r1.low, r1.close) == (105.0, 111.0, 104.0, 110.0)
    m15 = B.gop_khung(m1, "m15")                                          # khung viet thuong
    assert len(m15) == 2 and (m15.iloc[0].open, m15.iloc[0].high, m15.iloc[0].low, m15.iloc[0].close) == (100.0, 116.0, 99.0, 115.0)


@pytest.mark.parametrize("cach,mong0,mong1", [("dau", 1.0, 6.0), ("cuoi", 5.0, 10.0), ("max", 5.0, 10.0), ("tb", 3.0, 8.0)])
def test_gop_khung_cach_lay_spread(cach, mong0, mong1):
    m5 = B.gop_khung(_m1_nho(), "M5", cach)
    assert (m5.iloc[0].spread, m5.iloc[1].spread) == (mong0, mong1)


def test_gop_khung_spread_dau_va_max_khac_nhau_khi_spread_khong_don_dieu():
    m1 = _m1_nho()
    m1["spread"] = [9, 1, 1, 1, 1] + [1, 1, 7, 1, 1] + [2] * 20
    assert B.gop_khung(m1, "M5", "dau").iloc[0].spread == 9 and B.gop_khung(m1, "M5", "cuoi").iloc[0].spread == 1
    assert B.gop_khung(m1, "M5", "max").iloc[1].spread == 7 and B.gop_khung(m1, "M5", "tb").iloc[1].spread == pytest.approx(11 / 5)


def test_gop_khung_bo_o_rong_khong_de_nan():
    m1 = _m1_nho().drop(_m1_nho().index[10:20])                           # mat hai nen M5 tron (cuoi tuan / khong co tick)
    m5 = B.gop_khung(m1, "M5")
    assert len(m5) == 4 and not m5.isna().any().any()
    assert list(m5.index.minute) == [0, 5, 20, 25]


def test_gop_khung_m1_tra_nguyen_va_tu_choi_khung_hoac_spread_la():
    m1 = _m1_nho()
    assert B.gop_khung(m1, "M1") is m1
    with pytest.raises(ValueError, match="khung"):
        B.gop_khung(m1, "M7")
    with pytest.raises(ValueError, match="spread"):
        B.gop_khung(m1, "M5", "trung_vi")


def test_gop_khung_h1_va_d1_theo_gio_may_chu():
    ix = pd.date_range("2019-01-02 22:00", periods=180, freq="1min", name="time")      # 22:00 .. 00:59
    m1 = pd.DataFrame({"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "tick_volume": 1, "spread": 3.0}, index=ix)
    h1 = B.gop_khung(m1, "H1")
    assert list(h1.index.hour) == [22, 23, 0]
    d1 = B.gop_khung(m1, "D1")
    assert len(d1) == 2 and d1.index[1] == T("2019-01-03")


def test_kiem_phu_chap_nhan_du_va_tu_choi_thieu():
    m1 = B.m1_tong_hop(seed=1, ngay=3.0)
    ca = _ca_tay(m1)
    assert B.kiem_phu(B.cat_cua_so(m1, ca), ca) is None
    assert "nen" in B.kiem_phu(m1.iloc[:10], ca)                         # qua it nen
    ca_xa = dataclasses.replace(ca, tu=ca.tu - pd.Timedelta(days=30), den_het=ca.den_het)
    assert "khong phu" in B.kiem_phu(m1, ca_xa)                          # bat dau som hon du lieu > 7 ngay
    ca_xa2 = dataclasses.replace(ca, den_het=ca.den_het + pd.Timedelta(days=30))
    assert "khong phu" in B.kiem_phu(m1, ca_xa2)                         # ket thuc muon hon du lieu > 7 ngay
    ca_gan = dataclasses.replace(ca, tu=ca.tu - pd.Timedelta(days=6), den_het=ca.den_het + pd.Timedelta(days=6))
    assert B.kiem_phu(m1, ca_gan) is None                                # thieu <= 7 ngay o bien: chap nhan nhu `nua_engine`
    m1n = m1.copy()
    m1n.iloc[100, 1] = np.nan
    assert "NaN" in B.kiem_phu(m1n, ca)


def test_kiem_phu_dung_bien_49_50_nen_va_dung_7_ngay():
    m1 = B.m1_tong_hop(seed=1, ngay=1.0)
    ca = _ca_tay(m1)
    seg50, seg49 = m1.iloc[:50], m1.iloc[:49]
    ca50 = dataclasses.replace(ca, tu=seg50.index[0], den_het=seg50.index[-1])
    ca49 = dataclasses.replace(ca, tu=seg49.index[0], den_het=seg49.index[-1])
    assert B.kiem_phu(seg50, ca50) is None and "nen" in B.kiem_phu(seg49, ca49)
    bay, phut = pd.Timedelta(days=7), pd.Timedelta(minutes=1)
    assert B.kiem_phu(m1, dataclasses.replace(ca, tu=m1.index[0] - bay, den_het=m1.index[-1] + bay)) is None           # dung 7 ngay moi dau: duoc
    assert "khong phu" in B.kiem_phu(m1, dataclasses.replace(ca, tu=m1.index[0] - bay - phut, den_het=m1.index[-1]))
    assert "khong phu" in B.kiem_phu(m1, dataclasses.replace(ca, tu=m1.index[0], den_het=m1.index[-1] + bay + phut))


def test_nap_m1_thieu_cot_hoac_khong_co_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        B.nap_m1("AUDCAD", tmp_path)
    ix = pd.date_range("2019-01-02", periods=3, freq="1min", name="time")
    pd.DataFrame({"open": 1.0, "high": 1.0, "close": 1.0}, index=ix).to_csv(tmp_path / "AUDCAD_M1.csv.gz", compression="gzip")
    with pytest.raises(ValueError, match="low"):
        B.nap_m1("AUDCAD", tmp_path)


def test_serie_spread_theo_gia_va_thay_so_khong_bang_trung_vi():
    qc = LU.QC_AUDCAD
    seg = pd.DataFrame({"spread": [10.0, 0.0, 10.0, 40.0, 0.0]})
    sp = B.serie_spread(seg, qc)
    assert sp == pytest.approx(np.array([10, 10, 10, 40, 10]) * qc.point)         # nen 0 -> trung vi {10, 10, 40} = 10 (trung binh la 20)
    assert B.serie_spread(pd.DataFrame({"close": [1.0, 2.0]}), qc) == pytest.approx([qc.spread_du_phong] * 2)
    assert B.serie_spread(pd.DataFrame({"spread": [0.0, 0.0]}), qc) == pytest.approx([qc.spread_du_phong] * 2)


def test_quy_cach_ca_ap_he_so_va_phi_cua_bao_cao_va_tu_choi_ma_la():
    qc = B.quy_cach_ca(_ca(f=1.32))
    assert qc.pip == 1e-4 and qc.von_quy_doi == pytest.approx(1.32)
    qc2 = B.quy_cach_ca(_ca(qc={"phi_nam_mua": -0.5, "phi_nam_ban": 0.25}))
    assert (qc2.phi_nam_mua, qc2.phi_nam_ban) == (-0.5, 0.25)
    assert B.quy_cach_ca(_ca()).phi_nam_ban == LU.QC_AUDCAD.phi_nam_ban                 # bao cao khong ghi: phi mac dinh
    with pytest.raises(ValueError):
        B.quy_cach_ca(_ca(ma="DE40"))


def test_kiem_nhat_quan_bat_bang_sai_khoa_hoac_bi_cat():
    ca = _ca(lai_t=1000.0, n_t=2)
    ok = _bang(_lenh("2019-01-02", 1, 1.0, lai=400.0), _lenh("2019-01-03", -1, 1.0, lai=600.0))
    assert B.kiem_nhat_quan(ca, ok) == []
    assert any("tong lai" in c for c in B.kiem_nhat_quan(ca, ok.assign(lai=[400.0, 611.0])))        # lech 1,1% > 0,5%
    assert B.kiem_nhat_quan(ca, ok.assign(lai=[400.0, 604.9])) == []                                 # lech 0,49% < 0,5%
    assert any("co 1 lenh" in c and "ghi 2" in c for c in B.kiem_nhat_quan(ca, ok.iloc[:1].assign(lai=1000.0)))
    ca0 = _ca(lai_t=0.0, n_t=2)                                                                     # lai ~ 0: dung san 1% von (100) -> tuyet doi 0,5
    assert B.kiem_nhat_quan(ca0, ok.assign(lai=[0.2, 0.2])) == []                                   # 0,4 < 0,5
    assert any("tong lai" in c for c in B.kiem_nhat_quan(ca0, ok.assign(lai=[0.4, 0.4])))           # 0,8 > 0,5
    assert B.kiem_nhat_quan(dataclasses.replace(ca, t_truoc=None, n_t=None), ok.assign(lai=999.0)) == []     # bao cao khong ghi: khong kiem


# ======================================================================================================== 3. GIA BID + GHEP LENH
def test_them_bid_san_tru_spread_dung_chieu():
    idx = pd.date_range("2019-01-02 00:00", periods=3, freq="1min")
    sp = np.array([0.0002, 0.0004, 0.0006])
    b = pd.DataFrame({"mo": [T("2019-01-02 00:00:30"), T("2019-01-02 00:02:10"), T("2019-01-02 00:01:10"), T("2019-01-02 00:01:00"),
                             T("2019-01-02 00:00:10")],
                      "dong": [T("2019-01-02 00:01:30"), T("2019-01-02 00:01:59"), pd.NaT, pd.NaT, T("2019-01-02 00:02:00")],
                      "chieu": [1, -1, 1, 1, -1], "lot": 0.01, "gia_mo": [1.0010, 1.0020, 1.0030, 1.0040, 1.0050],
                      "gia_dong": [1.0015, 1.0000, np.nan, np.nan, 1.0010], "lai": 0.0})
    r = B.them_bid(b, "san", idx, sp)
    assert r.bid_mo[0] == pytest.approx(1.0010 - 0.0002) and r.bid_dong[0] == pytest.approx(1.0015)     # MUA: mo o ASK, dong o BID
    assert r.bid_mo[1] == pytest.approx(1.0020) and r.bid_dong[1] == pytest.approx(1.0000 - 0.0004)     # BAN: mo o BID, dong o ASK
    assert r.bid_mo[2] == pytest.approx(1.0030 - 0.0004) and math.isnan(r.bid_dong[2])                  # lenh con mo: khong co gia dong
    assert r.bid_mo[3] == pytest.approx(1.0040 - 0.0004)           # mo DUNG luc 00:01:00 = dau nen thu hai: spread cua nen do (khong phai nen truoc)
    assert r.bid_mo[4] == pytest.approx(1.0050) and r.bid_dong[4] == pytest.approx(1.0010 - 0.0006)     # dong DUNG 00:02:00 = dau nen thu ba
    assert list(b.columns) == ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "lai"]                # khong sua bang vao


def test_them_bid_gio_ngoai_khoang_cua_du_lieu_lay_nen_ke_can():
    idx = pd.date_range("2019-01-02 00:00", periods=2, freq="1min")
    b = pd.DataFrame({"mo": [T("2018-12-31 12:00"), T("2019-02-01")], "dong": [pd.NaT, pd.NaT], "chieu": [1, 1], "lot": 0.01,
                      "gia_mo": [1.0, 1.0], "gia_dong": [np.nan, np.nan], "lai": 0.0})
    r = B.them_bid(b, "san", idx, np.array([0.1, 0.3]))
    assert r.bid_mo.tolist() == pytest.approx([0.9, 0.7])


def test_them_bid_kieu_bid_giu_nguyen_va_tu_choi_dau_vao_sai():
    b = _bang(_lenh("2019-01-02", 1, 1.0))
    b = b.assign(gia_mo=1.5, gia_dong=1.7)
    r = B.them_bid(b, "bid")
    assert (r.bid_mo[0], r.bid_dong[0]) == (1.5, 1.7)
    with pytest.raises(ValueError):
        B.them_bid(b, "ask")
    with pytest.raises(ValueError):
        B.them_bid(b, "san")                                              # thieu idx / sp_gia
    with pytest.raises(ValueError):
        B.them_bid(b, "san", pd.date_range("2019-01-02", periods=3, freq="1min"), np.array([0.1, 0.2]))


def test_them_bid_loai_gia_la_bi_tu_choi_ke_ca_khi_da_co_du_idx_va_spread():
    # co du idx + sp_gia thi chi con kiem loai gia: 'ask' khong duoc lang le coi la 'san'
    b = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0)).assign(gia_mo=1.0, gia_dong=1.0, chieu=1)
    idx = pd.date_range("2019-01-02 09:59", periods=3, freq="1min")
    with pytest.raises(ValueError, match="dang_gia phai la"):
        B.them_bid(b, "ask", idx, np.array([0.1, 0.1, 0.1]))


def test_ghep_cung_chieu_gio_gia_va_dem_lenh_le():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0000), _lenh("2019-01-02 10:05:00", -1, 1.0020), _lenh("2019-01-02 10:10:00", 1, 0.9990))
    bien_the = _bang(_lenh("2019-01-02 10:00:20", 1, 1.00003), _lenh("2019-01-02 10:05:00", -1, 1.0020), _lenh("2019-01-02 10:10:00", 1, 0.9980))
    g = B.ghep_lenh(bien_the, tester, tol_giay=120, tol_gia=0.0001)
    assert g["cap"] == [(0, 0), (1, 1)] and g["chi_a"] == [2] and g["chi_b"] == [2]


def test_ghep_khac_chieu_thi_khong_ghep():
    a = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0))
    b = _bang(_lenh("2019-01-02 10:00:00", -1, 1.0))
    g = B.ghep_lenh(a, b, 60, 0.001)
    assert g["cap"] == [] and g["chi_a"] == [0] and g["chi_b"] == [0]


def test_ghep_moi_lenh_tester_chi_ghep_mot_lan():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0))
    bien_the = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0), _lenh("2019-01-02 10:00:00", 1, 1.00005))
    g = B.ghep_lenh(bien_the, tester, 60, 0.001)
    assert len(g["cap"]) == 1 and len(g["chi_a"]) == 1 and g["chi_b"] == []


def test_ghep_chon_lenh_gan_gia_nhat_roi_moi_den_gan_gio():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0000), _lenh("2019-01-02 10:00:00", 1, 1.0001))
    g = B.ghep_lenh(_bang(_lenh("2019-01-02 10:00:00", 1, 1.00009)), tester, 60, 0.001)
    assert g["cap"] == [(0, 1)] and g["chi_b"] == [0]
    # cung gia: lenh gan gio hon thang
    tester2 = _bang(_lenh("2019-01-02 10:00:50", 1, 1.0), _lenh("2019-01-02 10:00:10", 1, 1.0))
    g2 = B.ghep_lenh(_bang(_lenh("2019-01-02 10:00:00", 1, 1.0)), tester2, 60, 0.001)
    assert g2["cap"] == [(0, 1)]
    # gia uu tien hon gio: lenh dung gia nhung xa gio hon van duoc chon
    tester3 = _bang(_lenh("2019-01-02 10:00:50", 1, 1.0000), _lenh("2019-01-02 10:00:10", 1, 1.0002))
    assert B.ghep_lenh(_bang(_lenh("2019-01-02 10:00:00", 1, 1.0000)), tester3, 60, 0.001)["cap"] == [(0, 0)]


def test_ghep_duyet_theo_gio_mo_lenh_som_hon_nhan_truoc_du_bang_vao_khong_xep_gio():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0))
    bien_the = _bang(_lenh("2019-01-02 10:00:30", 1, 1.0), _lenh("2019-01-02 10:00:05", 1, 1.0))      # hang 1 mo som hon
    g = B.ghep_lenh(bien_the, tester, 60, 0.001)
    assert g["cap"] == [(1, 0)] and g["chi_a"] == [0]


def test_ghep_bien_dung_sai_tinh_ca_hai_dau():
    t = _bang(_lenh("2019-01-02 10:00:00", 1, 2.0))
    assert B.ghep_lenh(_bang(_lenh("2019-01-02 10:01:00", 1, 2.0)), t, 60, 0.5)["cap"] == [(0, 0)]                    # dung 60 s
    assert B.ghep_lenh(_bang(_lenh("2019-01-02 10:01:01", 1, 2.0)), t, 60, 0.5)["cap"] == []                          # 61 s
    assert B.ghep_lenh(_bang(_lenh("2019-01-02 09:59:00", 1, 2.0)), t, 60, 0.5)["cap"] == [(0, 0)]                    # dung -60 s
    assert B.ghep_lenh(_bang(_lenh("2019-01-02 10:00:00", 1, 2.5)), t, 60, 0.5)["cap"] == [(0, 0)]                    # dung 0,5
    assert B.ghep_lenh(_bang(_lenh("2019-01-02 10:00:00", 1, 2.5000001)), t, 60, 0.5)["cap"] == []
    assert B.ghep_lenh(_bang(_lenh("2019-01-02 10:00:00", 1, 1.5)), t, 60, 0.5)["cap"] == [(0, 0)]                    # lech am cung tinh


def test_ghep_rong_mot_ben_hoac_hai_ben():
    vazio = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0)).iloc[0:0]
    mot = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0))
    assert B.ghep_lenh(vazio, vazio, 60, 1) == {"cap": [], "chi_a": [], "chi_b": []}
    assert B.ghep_lenh(mot, vazio, 60, 1) == {"cap": [], "chi_a": [0], "chi_b": []}
    assert B.ghep_lenh(vazio, mot, 60, 1) == {"cap": [], "chi_a": [], "chi_b": [0]}


def test_ghep_chi_so_hang_khong_phu_thuoc_thu_tu_dong_cua_bang():
    # bang vao khong xep theo gio: chi so tra ve phai la chi so HANG cua bang vao
    tester = _bang(_lenh("2019-01-02 12:00:00", 1, 1.2), _lenh("2019-01-02 10:00:00", 1, 1.0))
    bien_the = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0), _lenh("2019-01-02 12:00:00", 1, 1.2))
    assert B.ghep_lenh(bien_the, tester, 60, 0.01)["cap"] == [(0, 1), (1, 0)]


def test_ghep_cap_va_chi_a_xep_theo_chi_so_hang_ke_ca_khi_lan_mua_ban():
    # ham duyet MUA truoc roi BAN; ket qua van phai xep theo chi so hang cua bang vao (khong theo thu tu duyet)
    tester = _bang(_lenh("2019-01-02 10:05:00", 1, 1.0), _lenh("2019-01-02 10:00:00", -1, 1.0))
    bien_the = _bang(_lenh("2019-01-02 10:00:00", -1, 1.0), _lenh("2019-01-02 10:05:00", 1, 1.0),
                     _lenh("2019-01-02 11:00:00", -1, 1.0), _lenh("2019-01-02 11:05:00", 1, 1.0))
    g = B.ghep_lenh(bien_the, tester, 60, 0.01)
    assert g["cap"] == [(0, 1), (1, 0)]                                    # nguoc lai (1, 0), (0, 1) neu khong xep
    assert g["chi_a"] == [2, 3]                                            # nguoc lai [3, 2] neu khong xep
    assert g["chi_b"] == []


# ============================================================================================================ 4. SO SANH
VON, NGAY = 10000.0, 365.25
T0, T1 = T("2019-01-02 10:00:00"), T("2019-01-02 11:00:00")


def _so(a, b, **kw):
    kw = dict(dict(tol_giay=300, tol_gia=0.0001, pip=0.0001, von=VON, ngay=NGAY, t0=T0, t1=T1), **kw)
    return B.so_sanh_bang(a, b, **kw)


def test_so_sanh_hai_bang_giong_het_nhau():
    b = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0, "2019-01-02 10:10:00", 1.0010, lai=10.0),
              _lenh("2019-01-02 10:20:00", -1, 1.003, "2019-01-02 10:30:00", 1.0020, lai=20.0))
    r = _so(b.copy(), b)
    assert (r["n_a"], r["n_b"], r["n_khop"], r["ti_le_khop"]) == (2, 2, 2, 1.0)
    assert r["lech_dau"] is None and r["khop_den"] == 1.0
    assert r["phan_ra"] == {"cap": 0.0, "chi_bien_the": 0.0, "chi_tester": 0.0}
    assert (r["lech_gia_mo_pip"], r["lech_gio_mo_giay"], r["khop_dong"], r["khac_lot"]) == (0.0, 0.0, 1.0, 0)
    assert r["lai_thang"]["mae_pct_von"] == 0.0


def test_so_sanh_lenh_lech_dau_tien_la_lenh_som_nhat_cua_hai_ben():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0), _lenh("2019-01-02 10:05:00", -1, 1.002), _lenh("2019-01-02 10:20:00", 1, 0.998))
    bien_the = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0), _lenh("2019-01-02 10:07:00", -1, 1.003), _lenh("2019-01-02 10:20:00", 1, 0.998))
    r = _so(bien_the, tester)
    assert r["n_khop"] == 2 and r["n_chi_a"] == 1 and r["n_chi_b"] == 1
    assert r["lech_dau"]["ben"] == "tester" and r["lech_dau"]["mo"] == "2019-01-02 10:05:00" and r["lech_dau"]["chieu"] == -1
    assert r["lech_dau"]["bid_mo"] == 1.002 and r["lech_dau"]["lot"] == 0.01
    assert r["khop_den"] == pytest.approx(5.0 / 60.0, abs=1e-4)
    # doi ben: lenh som nhat chi co o bien the
    r2 = _so(tester, bien_the)
    assert r2["lech_dau"]["ben"] == "bien_the" and r2["lech_dau"]["mo"] == "2019-01-02 10:05:00"


def test_so_sanh_khop_den_bi_chan_trong_0_1_va_lech_ngoai_cua_so():
    a = _bang(_lenh("2019-01-02 09:00:00", 1, 1.0))                       # truoc t0
    b = _bang(_lenh("2019-01-02 12:00:00", 1, 1.0))                       # sau t1
    assert _so(a, b.iloc[0:0])["khop_den"] == 0.0
    assert _so(b, a.iloc[0:0])["khop_den"] == 1.0
    assert _so(a, b)["khop_den"] == 0.0                                   # min(09:00, 12:00) -> truoc t0 -> 0
    sau = _so(a, a.iloc[0:0], t0=None, t1=None)
    assert sau["khop_den"] is None
    assert sau["lai_thang"] == {"mae_pct_von": None, "tuong_quan": None, "n_thang": 0}       # lenh con mo, khong biet gio het: khong chia thang duoc


def test_so_sanh_lech_gia_gio_lot_va_dong():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0000, "2019-01-02 10:10:00", 1.0010, lot=0.01),
                   _lenh("2019-01-02 10:20:00", -1, 1.0030, "2019-01-02 10:30:00", 1.0020, lot=0.01),
                   _lenh("2019-01-02 10:40:00", 1, 1.0000, "2019-01-02 10:50:00", 1.0010, lot=0.02))
    bien_the = _bang(_lenh("2019-01-02 10:00:20", 1, 1.00005, "2019-01-02 10:10:00", 1.0010, lot=0.01),
                     _lenh("2019-01-02 10:20:00", -1, 1.0030, "2019-01-02 10:30:00", 1.0010, lot=0.01),
                     _lenh("2019-01-02 10:40:00", 1, 1.00005, "2019-01-02 10:50:00", 1.0010, lot=0.03))
    r = _so(bien_the, tester)
    assert r["n_khop"] == 3
    assert r["lech_gia_mo_pip"] == pytest.approx(0.5)                     # trung vi {0,5; 0; 0,5} pip
    assert r["lech_gio_mo_giay"] == 0.0                                   # trung vi {20; 0; 0} giay
    assert r["khop_dong"] == pytest.approx(2.0 / 3.0, abs=1e-4)           # lenh 2 dong o 1,0020 vs 1,0010: lech 10 pip > dung sai 1 pip
    assert r["khac_lot"] == 1


def test_so_sanh_ti_le_khop_chia_cho_ben_nhieu_lenh_hon():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0), _lenh("2019-01-02 10:10:00", 1, 1.1))
    bien_the = _bang(*[_lenh("2019-01-02 10:%02d:00" % m, 1, p) for m, p in ((0, 1.0), (10, 1.1), (20, 1.2), (30, 1.3))])
    assert _so(bien_the, tester)["ti_le_khop"] == 0.5                      # 2 cap / max(4, 2)
    assert _so(tester, bien_the)["ti_le_khop"] == 0.5


def test_so_sanh_khop_dong_cung_gia_nhung_dong_tre_qua_dung_sai_thi_khong_khop():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0, "2019-01-02 10:10:00", 1.001))
    bien_the = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0, "2019-01-02 10:25:00", 1.001))      # dong tre 15 phut > dung sai 5 phut
    assert _so(bien_the, tester)["khop_dong"] == 0.0


def test_so_sanh_khop_dong_dung_bien_dung_sai_gio_va_gia():
    # gia nhi phan chinh xac de `<=` khong bi sai so dau phay dong: dung sai gio 300 giay, gia 0,5
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 2.0, "2019-01-02 10:10:00", 2.0))
    dung = _bang(_lenh("2019-01-02 10:00:00", 1, 2.0, "2019-01-02 10:15:00", 2.5))                # dong tre dung 300 s, lech gia dung 0,5
    qua_gio = _bang(_lenh("2019-01-02 10:00:00", 1, 2.0, "2019-01-02 10:15:01", 2.0))
    qua_gia = _bang(_lenh("2019-01-02 10:00:00", 1, 2.0, "2019-01-02 10:10:00", 2.5000001))
    kw = dict(tol_giay=300, tol_gia=0.5, pip=1.0)
    assert _so(dung, tester, **kw)["khop_dong"] == 1.0
    assert _so(qua_gio, tester, **kw)["khop_dong"] == 0.0
    assert _so(qua_gia, tester, **kw)["khop_dong"] == 0.0


def test_so_sanh_mot_ben_rong_van_tinh_lai_thang_ben_kia():
    a = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0, "2019-01-02 10:30:00", 1.0, lai=7.0))
    for r in (_so(a, a.iloc[0:0], von=1000.0), _so(a.iloc[0:0], a, von=1000.0)):
        assert r["lai_thang"]["n_thang"] == 1 and r["lai_thang"]["mae_pct_von"] == pytest.approx(0.7)         # |7 - 0| / 1000 * 100


def test_so_sanh_khop_dong_chi_tinh_cap_co_gia_dong_ca_hai_ben():
    tester = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0, "2019-01-02 10:10:00", 1.001), _lenh("2019-01-02 10:20:00", 1, 0.9))
    bien_the = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0, "2019-01-02 10:10:00", 1.001), _lenh("2019-01-02 10:20:00", 1, 0.9, "2019-01-02 10:25:00", 0.95))
    assert _so(bien_the, tester)["khop_dong"] == 1.0                      # cap thu hai thieu dong o tester -> khong tinh
    tester2 = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0))
    bien_the2 = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0))
    assert _so(bien_the2, tester2)["khop_dong"] is None                   # khong cap nao co dong o hai ben


def test_so_sanh_phan_ra_cong_lai_bang_lech_tong_voi_bang_ngau_nhien():
    rng = np.random.default_rng(7)
    n = 60
    gio = pd.Timestamp("2019-01-02 00:00") + pd.to_timedelta(np.sort(rng.integers(0, 40 * 3600, n)) * 60, unit="s")
    chieu = rng.choice([-1, 1], n)
    bid = np.round(0.9 + rng.integers(0, 400, n) * 0.0005, 5)
    lai = np.round(rng.normal(0, 3, n), 4)
    tester = pd.DataFrame({"mo": gio, "dong": gio + pd.Timedelta(minutes=7), "chieu": chieu, "lot": 0.01, "bid_mo": bid, "bid_dong": bid + 0.001, "lai": lai})
    giu = np.ones(n, bool)
    giu[rng.choice(n, 9, replace=False)] = False                          # bien the thieu 9 lenh cua tester
    bien_the = tester[giu].copy()
    bien_the["lai"] = bien_the["lai"] + rng.normal(0, 0.5, len(bien_the))
    them = pd.DataFrame({"mo": [gio[3] + pd.Timedelta(seconds=40)] * 5, "dong": pd.NaT, "chieu": [1] * 5, "lot": 0.01,
                         "bid_mo": [5.0, 5.1, 5.2, 5.3, 5.4], "bid_dong": np.nan, "lai": [1.5, -2.0, 3.0, 0.5, 4.0]})
    bien_the = pd.concat([bien_the, them], ignore_index=True)
    r = B.so_sanh_bang(bien_the, tester, tol_giay=120, tol_gia=0.0004, pip=0.0001, von=10000.0, ngay=40.0, t0=gio[0], t1=gio[-1] + pd.Timedelta(hours=1))
    assert r["n_khop"] == n - 9 and r["n_chi_a"] == 5 and r["n_chi_b"] == 9
    tong = (bien_the["lai"].sum() - tester["lai"].sum()) * 100.0 / 10000.0 / (40.0 / 365.25)
    assert sum(r["phan_ra"].values()) == pytest.approx(tong, abs=5e-4)                # moi phan duoc lam tron 4 chu so
    assert r["phan_ra"]["chi_bien_the"] == pytest.approx(7.0 * 100.0 / 10000.0 / (40.0 / 365.25), abs=1e-4)         # 1,5 - 2 + 3 + 0,5 + 4 = 7
    miss = tester[~giu]["lai"].sum()
    assert r["phan_ra"]["chi_tester"] == pytest.approx(-miss * 100.0 / 10000.0 / (40.0 / 365.25), abs=1e-4)


def test_so_sanh_lai_theo_thang_mae_va_tuong_quan():
    gio = ["2019-01-10 10:00:00", "2019-02-10 10:00:00", "2019-03-10 10:00:00", "2019-04-10 10:00:00"]
    tester = pd.DataFrame({"mo": [T(g) for g in gio], "dong": [T(g) + pd.Timedelta(hours=1) for g in gio], "chieu": 1, "lot": 0.01,
                           "bid_mo": [1.0, 1.1, 1.2, 1.3], "bid_dong": 1.0, "lai": [10.0, 20.0, 30.0, 40.0]})
    a = tester.assign(lai=[10.0, 0.0, 30.0, 40.0])
    r = B.so_sanh_bang(a, tester, tol_giay=60, tol_gia=0.001, pip=0.0001, von=1000.0, ngay=120.0, t0=T("2019-01-01"), t1=T("2019-05-01"))["lai_thang"]
    assert r["n_thang"] == 4 and r["mae_pct_von"] == pytest.approx(0.5)                  # (0 + 20 + 0 + 0) / 4 / 1000 * 100
    assert -1.0 <= r["tuong_quan"] <= 1.0 and r["tuong_quan"] == pytest.approx(np.corrcoef([10, 0, 30, 40], [10, 20, 30, 40])[0, 1], abs=1e-4)


def test_so_sanh_lai_thang_tuong_quan_none_khi_mot_chuoi_khong_doi():
    gio = ["2019-01-10 10:00:00", "2019-02-10 10:00:00", "2019-03-10 10:00:00"]
    tester = pd.DataFrame({"mo": [T(g) for g in gio], "dong": [T(g) + pd.Timedelta(hours=1) for g in gio], "chieu": 1, "lot": 0.01,
                           "bid_mo": [1.0, 1.1, 1.2], "bid_dong": 1.0, "lai": [10.0, 10.0, 10.0]})
    a = tester.assign(lai=[5.0, 10.0, 15.0])
    r = B.so_sanh_bang(a, tester, tol_giay=60, tol_gia=0.001, pip=0.0001, von=1000.0, ngay=90.0, t0=T("2019-01-01"), t1=T("2019-04-01"))["lai_thang"]
    assert r["n_thang"] == 3 and r["tuong_quan"] is None and r["mae_pct_von"] == pytest.approx(10 / 3 / 1000 * 100, abs=1e-4)


def test_so_sanh_lenh_con_mo_luc_het_tinh_vao_thang_cuoi_cua_cua_so():
    tester = pd.DataFrame({"mo": [T("2019-01-10 10:00:00")], "dong": [T("2019-01-10 11:00:00")], "chieu": [1], "lot": 0.01,
                           "bid_mo": 1.0, "bid_dong": 1.0, "lai": [5.0]})
    a = pd.DataFrame({"mo": [T("2019-01-10 10:00:00"), T("2019-02-10 10:00:00")], "dong": [T("2019-01-10 11:00:00"), pd.NaT], "chieu": [1, 1],
                      "lot": 0.01, "bid_mo": [1.0, 1.1], "bid_dong": [1.0, np.nan], "lai": [5.0, -3.0]})
    r = B.so_sanh_bang(a, tester, tol_giay=60, tol_gia=0.001, pip=0.0001, von=1000.0, ngay=60.0, t0=T("2019-01-01"), t1=T("2019-02-28 23:59:59"))
    assert r["lai_thang"]["n_thang"] == 2 and r["lai_thang"]["mae_pct_von"] == pytest.approx(0.15)         # (0 + 3) / 2 / 1000 * 100
    assert r["lai_thang"]["tuong_quan"] is None                                                            # duoi 3 thang: khong tinh tuong quan


def test_so_sanh_hai_bang_rong():
    rong = _bang(_lenh("2019-01-02 10:00:00", 1, 1.0)).iloc[0:0]
    r = _so(rong, rong)
    assert r["ti_le_khop"] == 1.0 and r["n_khop"] == 0 and r["lech_dau"] is None
    assert r["phan_ra"] == {"cap": 0.0, "chi_bien_the": 0.0, "chi_tester": 0.0} and r["lai_thang"]["n_thang"] == 0


# ======================================================================================================== 5. BIEN THE
def test_bien_the_mac_dinh_ten_duy_nhat_va_du_hai_kieu():
    ds = B.bien_the_mac_dinh()
    ten = [b.ten for b in ds]
    assert len(ten) == len(set(ten))
    assert {b.kieu for b in ds} == {"bar", "ea"}
    assert {b.thu_tu for b in ds if b.kieu == "ea"} == set(B.THU_TU_TICK)
    assert {(b.khung, b.khop_bar) for b in ds if b.kieu == "bar" and b.nhan_spread == 1.0 and b.spread_gop == "dau"} == \
           {(k, m) for k in ("M1", "M5", "M15") for m in LU.MO_HINH_BAR}
    assert any(b.nhan_spread == 0.0 for b in ds) and any(b.nhan_spread == 2.0 for b in ds) and any(b.spread_gop == "max" for b in ds)
    assert all(b.khung == "M1" for b in ds if b.kieu == "ea")


@pytest.mark.parametrize("kw", [dict(ten=""), dict(kieu="xyz"), dict(khung="M7"), dict(khop_bar="giua"), dict(spread_gop="la"), dict(thu_tu="ngau_nhien"),
                                dict(nhan_spread=-1.0), dict(nhan_spread=float("nan")), dict(nhan_spread=float("inf")), dict(kieu="ea", khung="M5")])
def test_bien_the_tu_choi_gia_tri_vo_ly(kw):
    with pytest.raises(ValueError):
        B.BienThe(**dict(dict(ten="x"), **kw))


def test_chon_bien_the():
    tat = B.bien_the_mac_dinh()
    assert B.chon_bien_the(None) == tat and B.chon_bien_the("") == tat and B.chon_bien_the("tat_ca") == tat
    assert all(b.kieu == "bar" for b in B.chon_bien_the("bar")) and all(b.kieu == "ea" for b in B.chon_bien_the("ea"))
    assert len(B.chon_bien_the("bar")) + len(B.chon_bien_the("ea")) == len(tat)
    assert [b.ten for b in B.chon_bien_the("bar_m1_duong_di, ea_m1_cao_truoc")] == ["bar_m1_duong_di", "ea_m1_cao_truoc"]
    with pytest.raises(ValueError, match="khong_co"):
        B.chon_bien_the("bar_m1_duong_di,khong_co")


def test_dung_sai_theo_khung_va_buoc_luoi():
    ca = _ca(ts=dict(TS_VUA, buoc=20.0))
    assert B.dung_sai_cua(ca, B.BienThe("a", "bar", "M1")) == (120.0, pytest.approx(1.0e-4))        # buoc/4 = 5 -> chan 1 pip
    assert B.dung_sai_cua(ca, B.BienThe("a", "bar", "M15"))[0] == 1350.0
    ca_nho = _ca(ts=dict(TS_VUA, buoc=1.0))
    assert B.dung_sai_cua(ca_nho, B.BienThe("a", "bar", "M5"))[1] == pytest.approx(0.3e-4)           # chan duoi 0,3 pip
    assert B.dung_sai_cua(_ca(ts=dict(TS_VUA, buoc=2.0)), B.BienThe("a", "bar", "M5"))[1] == pytest.approx(0.5e-4)
    assert B.dung_sai_cua(ca, B.BienThe("a", "bar", "M5"), pip=0.01)[1] == pytest.approx(0.01)


# ======================================================================================================= 6. ENGINE NEN
@pytest.fixture(scope="module")
def m1_3ngay():
    return B.m1_tong_hop(seed=3, ngay=3.0, spread_pts=20)


def test_m1_tong_hop_hop_le():
    m1 = B.m1_tong_hop(seed=4, ngay=1.0, spread_pts=15)
    assert len(m1) == 1440 and (m1.spread == 15).all()
    assert (m1.high >= np.maximum(m1.open, m1.close)).all() and (m1.low <= np.minimum(m1.open, m1.close)).all()
    assert np.allclose(m1.open.to_numpy()[1:], m1.close.to_numpy()[:-1])         # nen sau mo dung cho nen truoc dong
    assert np.allclose(m1.close * 1e5, np.round(m1.close * 1e5))                  # tren luoi 5 chu so
    assert B.m1_tong_hop(seed=4, ngay=1.0).equals(B.m1_tong_hop(seed=4, ngay=1.0))
    assert not B.m1_tong_hop(seed=4, ngay=1.0).close.equals(B.m1_tong_hop(seed=5, ngay=1.0).close)


@pytest.mark.parametrize("khung", ["M1", "M5", "M15"])
@pytest.mark.parametrize("mo_hinh", list(LU.MO_HINH_BAR))
def test_chay_bar_lai_bang_cong_thuc_doc_lap(m1_3ngay, khung, mo_hinh):
    ca = _ca_tay(m1_3ngay)
    kq = B.chay_bar(ca, m1_3ngay, B.BienThe("t", "bar", khung, mo_hinh))
    bars = B.gop_khung(m1_3ngay, khung)
    qc = B.quy_cach_ca(ca, float(bars["close"].median()))
    dl = LU.chuan_bi(bars, qc)
    e = LU.chay_mang(dl, LU.ThamSo(**dict(TS_VUA, khop_bar=mo_hinh)), 10000.0 * 1.32, ghi_lenh=True)
    treo = float((e.lenh["chieu"].to_numpy(float) * (float(dl.cl[-1]) - e.lenh["gia_mo"].to_numpy(float)) * e.lenh["lot"].to_numpy(float) * qc.hop_dong)[e.lenh["dong"].isna().to_numpy()].sum())
    assert kq.loi is None and kq.canh_bao == [] and len(kq.bang) == len(e.lenh)
    assert kq.lai == pytest.approx((e.lai_rong + treo + e.phi_swap) / 1.32, rel=1e-9, abs=1e-9)          # TRUOC swap, tien tai khoan
    assert kq.lai_nam_pct == pytest.approx(kq.lai / 10000.0 / (3 / 365.25) * 100.0)
    assert kq.dd_pct >= 0.0 and kq.dd_pct == pytest.approx(abs(float(LU.chi_so(e, 10000.0 * 1.32)["maxdd_pct"])))
    assert {"bid_mo", "bid_dong"} <= set(kq.bang.columns)
    assert kq.bang["bid_mo"].tolist() == kq.bang["gia_mo"].tolist()      # engine da o chuoi BID: khong tru them


def test_chay_bar_nhan_spread_la_tuyen_tinh_va_khong_doi_tap_lenh(m1_3ngay):
    ca = _ca_tay(m1_3ngay)
    r = [B.chay_bar(ca, m1_3ngay, B.BienThe("t", "bar", "M5", nhan_spread=k)) for k in (0.0, 1.0, 2.0)]
    assert len(r[0].bang) == len(r[1].bang) == len(r[2].bang)
    assert r[0].lai > r[1].lai > r[2].lai
    assert (r[0].lai - r[1].lai) == pytest.approx(r[1].lai - r[2].lai, rel=1e-9)
    spread_tien = float((m1_3ngay.loc[:, "spread"].median()) * 1e-5)       # sanity: spread ~ 20 point = 2 pip -> chi phi duong
    assert spread_tien > 0 and (r[0].lai - r[1].lai) > 0


def test_chay_bar_khop_bar_doi_ket_qua_khi_co_tia_lenh(m1_3ngay):
    ca = _ca_tay(m1_3ngay)
    a = B.chay_bar(ca, m1_3ngay, B.BienThe("t", "bar", "M15", "duong_di"))
    b = B.chay_bar(ca, m1_3ngay, B.BienThe("t", "bar", "M15", "cuc_tri"))
    assert len(a.bang) != len(b.bang) or abs(a.lai - b.lai) > 1.0


def test_chay_bar_khung_khac_cho_so_nen_khac(m1_3ngay):
    ca = _ca_tay(m1_3ngay)
    n = {k: len(B.chay_bar(ca, m1_3ngay, B.BienThe("t", "bar", k)).bang) for k in ("M1", "M5", "M15")}
    assert len(set(n.values())) == 3                                      # khung mo phong khac nhau -> tap lenh khac nhau


def test_chay_bar_chuyen_dung_che_do_gop_spread_xuong_gop_khung(m1_3ngay, monkeypatch):
    goi, that = [], B.gop_khung
    monkeypatch.setattr(B, "gop_khung", lambda seg, khung, spread="dau": goi.append((khung, spread)) or that(seg, khung, spread))
    B.chay_bar(_ca_tay(m1_3ngay), m1_3ngay, B.BienThe("t", "bar", "M15", "duong_di", spread_gop="max"))
    assert goi == [("M15", "max")]


def test_chay_bar_spread_gop_max_dat_hon_dau_khi_spread_nhap_nhang(m1_3ngay):
    m1 = m1_3ngay.copy()
    m1["spread"] = np.where(np.arange(len(m1)) % 2 == 0, 10, 40)           # nen dau cua cua so 15 phut luc 10, luc 40; max luon 40
    ca = _ca_tay(m1)
    dau = B.chay_bar(ca, m1, B.BienThe("t", "bar", "M15", spread_gop="dau"))
    mx = B.chay_bar(ca, m1, B.BienThe("t", "bar", "M15", spread_gop="max"))
    assert dau.loi is None and mx.loi is None and len(dau.bang) > 0 and len(mx.bang) > 0
    assert dau.lai > mx.lai


def test_chay_bien_the_loi_ha_tang_thanh_dong_loi_khong_nem_ra_ngoai(m1_3ngay):
    ca = _ca_tay(m1_3ngay, ts=dict(TS_VUA, ten_la=3))
    r = B.chay_bien_the(ca, m1_3ngay, B.BienThe("t", "bar", "M5"))
    assert r.loi and "TypeError" in r.loi and r.bang is None
    r2 = B.chay_bien_the(_ca_tay(m1_3ngay), m1_3ngay, B.BienThe("e", "ea", "M1"), exe=None)
    assert r2.loi and "exe" in r2.loi
    r3 = B.chay_bien_the(_ca_tay(m1_3ngay), m1_3ngay, B.BienThe("e", "ea", "M1"), exe="/khong/co/file/ea.exe")
    assert r3.loi and r3.loi.startswith("FileNotFoundError") and r3.bang is None


# ========================================================================================================= 7. QUET (DIA)
def _ghi_dia(tmp_path, m1, tester):
    (tmp_path / "gia").mkdir()
    (tmp_path / "lenh").mkdir()
    m1.to_csv(tmp_path / "gia" / "AUDCAD_M1.csv.gz", compression="gzip")
    tester.to_csv(tmp_path / "lenh" / ("%s_lenh.csv.gz" % KHOA), index=False, compression="gzip")
    return tmp_path / "gia", tmp_path / "lenh"


def _tester_tay():
    return pd.DataFrame({"mo": [T("2019-01-02 05:00:00"), T("2019-01-02 06:00:00"), T("2019-01-02 07:00:00")],
                         "dong": [T("2019-01-02 05:30:00"), T("2019-01-02 06:30:00"), pd.NaT], "chieu": [1, -1, 1], "lot": 0.01,
                         "gia_mo": [0.9, 0.9, 0.9], "gia_dong": [0.9005, 0.8995, np.nan], "lai": [1.0, 1.0, -0.5], "swap": 0.0, "ly": "tp"})


def test_chay_mot_ca_doc_tu_dia_va_tra_mot_dong_moi_bien_the(tmp_path, m1_3ngay):
    gia, lenh = _ghi_dia(tmp_path, m1_3ngay, _tester_tay())
    ca = dataclasses.replace(_ca_tay(m1_3ngay), khoa=KHOA, so_khoa=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0))
    cac = [B.BienThe("a", "bar", "M5"), B.BienThe("b", "bar", "M15", "cuc_tri")]
    rows = B.chay_mot_ca(ca, cac, gia, lenh)
    assert [r["bien_the"] for r in rows] == ["a", "b"] and not any(r.get("loi") for r in rows)
    r = rows[0]
    assert r["n_b"] == 3 and r["n_tester"] == 3 and r["ma"] == "AUDCAD" and r["q"] == 100.0 and r["dd_tester"] == 4.0
    assert r["lai_nam_tester"] == pytest.approx(1.5 / 10000.0 / (3 / 365.25) * 100.0)
    assert {"ti_le_khop", "phan_ra", "lech_dau", "khop_den", "lai_thang", "dd_pct", "giay", "n_a"} <= set(r)


def test_chay_mot_ca_thieu_gia_hoac_lenh_hoac_phu_thieu_la_dong_loi_co_ly_do(tmp_path, m1_3ngay):
    ca = dataclasses.replace(_ca_tay(m1_3ngay), khoa=KHOA)
    cac = [B.BienThe("a", "bar", "M5")]
    (r,) = B.chay_mot_ca(ca, cac, tmp_path, tmp_path)                       # khong co file gia
    assert "FileNotFoundError" in r["loi"]
    gia, lenh = _ghi_dia(tmp_path, m1_3ngay, _tester_tay())
    (lenh / ("%s_lenh.csv.gz" % KHOA)).unlink()
    (r,) = B.chay_mot_ca(ca, cac, gia, lenh)                                # co gia, khong co bang lenh
    assert "FileNotFoundError" in r["loi"]
    ca_xa = dataclasses.replace(ca, tu=T("2018-01-01"), den_het=T("2018-03-31"))
    (r,) = B.chay_mot_ca(ca_xa, cac, gia, lenh)                             # gia khong phu cua so
    assert "khong phu" in r["loi"] or "nen" in r["loi"]


def test_chay_mot_ca_bang_lenh_thieu_cot_la_dong_loi(m1_3ngay):
    rows = B.chay_mot_ca(_ca_tay(m1_3ngay), [B.BienThe("a", "bar", "M5")], m1=m1_3ngay, bang_tester=_tester_tay().drop(columns=["gia_mo"]))
    assert "gia_mo" in rows[0]["loi"]


def test_chay_mot_ca_canh_bao_khi_bang_lenh_khong_phai_cua_bao_cao(m1_3ngay):
    ca = dataclasses.replace(_ca_tay(m1_3ngay), t_truoc=999.0, n_t=3)
    (r,) = B.chay_mot_ca(ca, [B.BienThe("a", "bar", "M5")], m1=m1_3ngay, bang_tester=_tester_tay())
    assert r["canh_bao"] and "tong lai" in r["canh_bao"][0]


def test_chay_mot_ca_truyen_dung_von_ngay_cua_so_va_dung_sai_vao_so_sanh(m1_3ngay, monkeypatch):
    bat, that = [], B.so_sanh_bang
    monkeypatch.setattr(B, "so_sanh_bang", lambda a, b, **kw: bat.append(kw) or that(a, b, **kw))
    ca = _ca_tay(m1_3ngay)
    bt = B.BienThe("a", "bar", "M15", "cuc_tri")
    B.chay_mot_ca(ca, [bt], m1=m1_3ngay, bang_tester=_tester_tay())
    qc = B.quy_cach_ca(ca, float(np.nanmedian(B.cat_cua_so(m1_3ngay, ca)["close"].to_numpy(float))))
    tg, tp = B.dung_sai_cua(ca, bt, qc.pip)
    assert bat == [dict(tol_giay=tg, tol_gia=tp, pip=qc.pip, von=ca.von, ngay=ca.ngay, t0=ca.tu, t1=ca.den_het)]
    assert tg == 1350.0                                                        # 1,5 nen M15, khong phai mac dinh 120 s


def test_chay_mot_ca_ghi_giay_chay_lam_tron_hai_so(m1_3ngay, monkeypatch):
    that = B.chay_bien_the
    monkeypatch.setattr(B, "chay_bien_the", lambda ca, seg, bt, exe=None: dataclasses.replace(that(ca, seg, bt, exe), giay=1.2399))
    (r,) = B.chay_mot_ca(_ca_tay(m1_3ngay), [B.BienThe("a", "bar", "M5")], m1=m1_3ngay, bang_tester=_tester_tay())
    assert r["giay"] == 1.24


def test_quet_hai_luong_cho_ket_qua_giong_mot_luong(tmp_path, m1_3ngay):
    gia, lenh = _ghi_dia(tmp_path, m1_3ngay, _tester_tay())
    cas = [dataclasses.replace(_ca_tay(m1_3ngay), ten="c%d" % i, khoa=KHOA) for i in range(3)]
    cac = [B.BienThe("a", "bar", "M5"), B.BienThe("b", "bar", "M1", "cuc_tri")]
    r1 = B.quet(cas, cac, gia, lenh, luong=1)
    r2 = B.quet(cas, cac, gia, lenh, luong=2)

    def bo_giay(rows):
        return [{k: v for k, v in r.items() if k != "giay"} for r in rows]
    assert len(r1) == 6 and bo_giay(r1) == bo_giay(r2)
    assert [r["ca"] for r in r2] == ["c0", "c0", "c1", "c1", "c2", "c2"]    # thu tu theo ca, khong theo luc xong


@can_cxx
def test_quet_tu_bien_dich_ea_khi_co_bien_the_ea_ma_khong_dua_exe(exe, tmp_path):
    ca, m1, b = B.tao_ca_tong_hop(exe, seed=3, ngay=0.5, thu_tu_that="cao_truoc")
    gia, lenh = _ghi_dia(tmp_path, m1, b)
    ca = dataclasses.replace(ca, khoa=KHOA)
    rows = B.quet([ca], [B.BienThe("ea_m1_cao_truoc", "ea", "M1", thu_tu="cao_truoc")], gia, lenh, exe=None)
    assert len(rows) == 1 and not rows[0].get("loi") and rows[0]["ti_le_khop"] == 1.0


# =========================================================================================================== 8. TONG HOP
def _dong(ten, lai, lai_t, n_a=10, n_b=10, dd=5.0, dd_t=5.0, khop=0.5, khop_den=0.5, giay=1.0):
    return {"ca": "c", "bien_the": ten, "lai_nam_pct": lai, "lai_nam_tester": lai_t, "n_a": n_a, "n_b": n_b, "dd_pct": dd, "dd_tester": dd_t,
            "ti_le_khop": khop, "khop_den": khop_den, "giay": giay}


def test_tong_hop_xep_theo_sai_so_tuyet_doi_va_bo_dong_loi():
    rows = [_dong("A", 10.0, 8.0), _dong("A", 5.0, 6.0), _dong("B", 1.1, 1.0), _dong("B", 2.1, 2.0),
            {"ca": "c", "bien_the": "C", "loi": "hong"}, {"ca": "c", "bien_the": "C", "loi": "hong"}]
    t = B.tong_hop(rows)
    assert [d["bien_the"] for d in t] == ["B", "A"]                       # C chi co dong loi -> khong co mat
    a = t[1]
    assert (a["n"], a["lech_trung_vi"], a["sai_so_tb"], a["cung_dau"]) == (2, 0.5, 1.5, 2)
    assert t[0]["sai_so_tb"] == pytest.approx(0.1)


def test_tong_hop_cung_dau_ti_le_lenh_dd_va_khop():
    rows = [_dong("A", 5.0, -1.0, n_a=20, n_b=10, dd=8.0, dd_t=4.0, khop=0.9, khop_den=0.2),
            _dong("A", 3.0, 2.0, n_a=10, n_b=10, dd=2.0, dd_t=4.0, khop=0.7, khop_den=0.6),
            _dong("A", -2.0, -3.0, n_a=0, n_b=0, dd=1.0, dd_t=None, khop=1.0, khop_den=None)]
    (a,) = B.tong_hop(rows)
    assert a["cung_dau"] == 2                                             # dong 1: +5 vs -1 khac dau
    assert a["ti_le_lenh_trung_vi"] == 1.5                                # {2,0; 1,0} -> dong n_b=0 bi bo
    assert a["ti_le_dd_trung_vi"] == 1.25                                 # {2,0; 0,5}, dong dd_t None bi bo
    assert a["khop_lenh_tb"] == pytest.approx((0.9 + 0.7 + 1.0) / 3, abs=1e-4)
    assert a["khop_den_trung_vi"] == pytest.approx(0.4)                   # {0,2; 0,6}


def test_tong_hop_ti_le_dd_bo_dong_co_dd_tester_khong_qua_1_phan_tram():
    (a,) = B.tong_hop([_dong("A", 1.0, 1.0, dd=3.0, dd_t=1.0), _dong("A", 1.0, 1.0, dd=3.0, dd_t=1.5)])
    assert a["ti_le_dd_trung_vi"] == 2.0                                   # chi dong dd_t = 1,5 (dd_t = 1,0 chua du de chia)


def test_tong_hop_hoa_sai_so_thi_xep_theo_khop_lenh_roi_ten():
    t = B.tong_hop([_dong("Z", 1.0, 1.0, khop=0.9), _dong("A", 1.0, 1.0, khop=0.5), _dong("M", 1.0, 1.0, khop=0.9)])
    assert [d["bien_the"] for d in t] == ["M", "Z", "A"]


def test_tong_hop_rong():
    assert B.tong_hop([]) == [] and B.tong_hop([{"ca": "c", "bien_the": "A", "loi": "x"}]) == []


def test_in_bang_va_viet_bao_cao(tmp_path):
    rows = [_dong("A", 10.0, 8.0) | {"lech_dau": {"ben": "tester"}, "phan_ra": {"cap": 1.0}}, {"ca": "k", "bien_the": "A", "loi": "hong that"}]
    t = B.tong_hop(rows)
    dong = []
    B.in_bang(t, dong.append)
    assert len(dong) == 2 and dong[1].lstrip().startswith("A")
    f = tmp_path / "ra" / "bo.md"
    B.viet_bao_cao(rows, t, f, {"X": "ly do bo"})
    van = f.read_text("utf-8")
    assert "Lenh lech dau tien" in van and "Dong loi (1)" in van and "hong that" in van and "X: ly do bo" in van


def test_main_khong_co_ca_nao_thi_thoat_ma_2_va_noi_cho_gi(tmp_path, capsys):
    (tmp_path / "xong").mkdir()
    assert B.main(["--xong", str(tmp_path / "xong"), "--gia", str(tmp_path)]) == 2
    assert "chua co ca nao" in capsys.readouterr().out


def test_main_chay_tu_dia_va_ghi_bao_cao(tmp_path, monkeypatch, m1_3ngay, capsys):
    xong = tmp_path / "xong"
    xong.mkdir()
    ts = dict(TS_VUA)
    bc = _bc(tu="2019.01.02", den="2019.01.04", ngay=3, ts=ts, khoa=KHOA, lai_t=1.5, n_t=3)
    _don(xong, "j1", bc, duong="reports/hieu_chuan/A_e4.json")
    gia, lenh = _ghi_dia(tmp_path, m1_3ngay, _tester_tay())
    monkeypatch.setattr(B, "GOC", tmp_path)
    kq = B.main(["--xong", str(xong), "--gia", str(gia), "--lenh", str(lenh), "--bien-the", "bar_m5_duong_di,bar_m1_cuc_tri", "--ghi"])
    ra = capsys.readouterr().out
    assert kq == 0 and "ca san sang: 1 / 1" in ra and "bar_m5_duong_di" in ra
    assert (tmp_path / "reports" / "bo_thu_mo_phong.md").exists()


def _moi_truong_main(tmp_path, m1, cac_bao_cao):
    """cac_bao_cao: [(ten_don, duong_bao_cao, bao_cao)] -> (thu muc xong, thu muc gia, thu muc lenh); gia chi co AUDCAD, bang lenh chi co KHOA."""
    xong = tmp_path / "xong"
    xong.mkdir()
    for ten, duong, bc in cac_bao_cao:
        _don(xong, ten, bc, duong=duong)
    gia, lenh = _ghi_dia(tmp_path, m1, _tester_tay())
    return xong, gia, lenh


def _bc_main(**kw):
    """Bao cao hieu chuan cho cua so 02..04/01/2019 cua `m1_3ngay`, khop voi `_tester_tay()` (3 lenh, lai 1,5)."""
    return _bc(**dict(dict(tu="2019.01.02", den="2019.01.04", ngay=3, ts=dict(TS_VUA), khoa=KHOA, lai_t=1.5, n_t=3), **kw))


def test_main_loc_theo_ma_va_gioi_han_so_ca(tmp_path, monkeypatch, m1_3ngay, capsys):
    xong, gia, lenh = _moi_truong_main(tmp_path, m1_3ngay, [("j1", "reports/hieu_chuan/A_e4.json", _bc_main()),
                                                          ("j2", "reports/hieu_chuan/B_e4.json", _bc_main())])
    base = ["--xong", str(xong), "--gia", str(gia), "--lenh", str(lenh), "--bien-the", "bar_m5_duong_di"]
    assert B.main(base + ["--ma", "EURCAD"]) == 2
    assert "ca san sang: 0 / 0" in capsys.readouterr().out
    assert B.main(base + ["--ma", "audcad", "--toi-da", "1"]) == 0
    assert "ca san sang: 1 / 2" in capsys.readouterr().out
    assert B.main(base) == 0
    assert "ca san sang: 2 / 2" in capsys.readouterr().out


def test_main_chi_lay_o_sach_tru_khi_co_ca_nhiem(tmp_path, m1_3ngay, capsys):
    xong, gia, lenh = _moi_truong_main(tmp_path, m1_3ngay, [("j1", "reports/hieu_chuan/A_e4.json", _bc_main(q=51.0))])
    base = ["--xong", str(xong), "--gia", str(gia), "--lenh", str(lenh), "--bien-the", "bar_m5_duong_di"]
    assert B.main(base) == 2
    assert B.main(base + ["--ca-nhiem"]) == 0
    assert "ca san sang: 1 / 1" in capsys.readouterr().out.split("ca san sang: 0 / 0")[-1]


def test_main_noi_ro_vi_sao_bo_qua_ca_thieu_gia_hoac_thieu_bang_lenh(tmp_path, m1_3ngay, capsys):
    xong, gia, lenh = _moi_truong_main(tmp_path, m1_3ngay, [
        ("j1", "reports/hieu_chuan/A_e4.json", _bc_main()),
        ("j2", "reports/hieu_chuan/B_e4.json", _bc_main(ma="NZDCAD")),                         # khong co file gia NZDCAD
        ("j3", "reports/hieu_chuan/C_e4.json", _bc_main(khoa="fedcba9876543210")),             # khong co bang lenh cua khoa nay
        ("j4", "reports/hieu_chuan/D_e4.json", _bc_main(tu="2019.01.02", den="2019.01.25", ngay=24)),         # gia chi den 04/01: thieu > 7 ngay o cuoi
        ("j5", "reports/hieu_chuan/E_e4.json", _bc_main(tu="2018.01.01", den="2018.03.31", ngay=90))])        # khong co nen nao trong cua so
    assert B.main(["--xong", str(xong), "--gia", str(gia), "--lenh", str(lenh), "--bien-the", "bar_m5_duong_di"]) == 0
    ra = capsys.readouterr().out
    assert "ca san sang: 1 / 5 (bo qua 4)" in ra
    assert "B_e4.json: chua co gia M1 cua NZDCAD" in ra and "C_e4.json: chua co bang lenh tester fedcba9876543210" in ra
    assert "D_e4.json: gia M1 chi phu" in ra and "khong phu cua so" in ra and "E_e4.json: gia M1 chi co 0 nen" in ra


# ======================================================================================== 9. EA TREN TICK SINH TU M1 (co dap an)
@pytest.fixture(scope="module")
def exe(tmp_path_factory):
    if G.trinh_bien_dich() is None:
        pytest.skip("khong co g++ / clang++")
    return B.bien_dich_ea(thu_muc=tmp_path_factory.mktemp("ea_bo_thu"))


def test_bang_tu_ea_tinh_tay_lai_va_dong_not_lenh_con_mo():
    lenh = pd.DataFrame({"ticket": [1, 2], "type": [0, 1], "vol": [0.02, 0.01], "open": [1.00010, 1.00000], "close": [1.00020, np.nan],
                         "tick_mo": [1, 2], "tick_dong": [3.0, np.nan], "ly_do": ["tp", "open"], "spread_mo": [0.00002, 0.00002], "comment": ["", ""]})
    tk = {"time": np.array([0.0, 10.0, 20.0, 30.0, 40.0]), "bid": np.array([1.0, 1.0001, 1.0, 1.0002, 0.9999]),
          "spread": np.array([0.00002] * 5)}
    qc = LU.QC_AUDCAD
    b = B.bang_tu_ea(lenh, tk, qc, 2.0)
    assert b["chieu"].tolist() == [1, -1] and b["lot"].tolist() == [0.02, 0.01]
    assert b["mo"].tolist() == [T("1970-01-01 00:00:10"), T("1970-01-01 00:00:20")]
    assert b["dong"][0] == T("1970-01-01 00:00:30") and pd.isna(b["dong"][1])
    assert b["ly"].tolist() == ["tp", "het_gio"]
    # MUA 0,02 lot dong o BID 1,0002 mo o ASK 1,0001: (0,0001 * 0,02 * 100000) / f = 0,2 / 2 = 0,1
    assert b["lai"][0] == pytest.approx(0.1)
    # BAN 0,01 lot mo o BID 1,0000, dong not o ASK = bid cuoi + spread cuoi = 0,99992: (1,0 - 0,99992) * 0,01 * 100000 / 2 = 0,04
    assert b["lai"][1] == pytest.approx(0.04, abs=1e-9)
    assert b["gia_dong"][0] == 1.00020 and pd.isna(b["gia_dong"][1])


def test_bang_tu_ea_khong_co_lenh_cho_bang_rong_du_cot():
    b = B.bang_tu_ea(pd.DataFrame(), {"time": np.array([0.0]), "bid": np.array([1.0]), "spread": np.array([0.0])}, LU.QC_AUDCAD, 1.0)
    assert len(b) == 0 and list(b.columns) == B.COT_LENH


@can_cxx
@pytest.mark.parametrize("that", ["cao_truoc", "thap_truoc", "theo_nen"])
def test_bo_thu_tim_ra_dung_thu_tu_tick_da_gieo(exe, that):
    ca, m1, b = B.tao_ca_tong_hop(exe, seed=2, ngay=1.0, thu_tu_that=that)
    assert len(b) > 100 and B.kiem_nhat_quan(ca, b) == []
    rows = B.chay_mot_ca(ca, [v for v in B.bien_the_mac_dinh() if v.kieu == "ea"], exe=exe, m1=m1, bang_tester=b)
    khop = {r["bien_the"]: r["ti_le_khop"] for r in rows}
    assert khop["ea_m1_" + that] == 1.0
    assert all(v < 0.95 for k, v in khop.items() if k != "ea_m1_" + that), khop
    t = B.tong_hop(rows)
    assert t[0]["bien_the"] == "ea_m1_" + that and t[0]["sai_so_tb"] == pytest.approx(0.0, abs=1e-9)
    dung = next(r for r in rows if r["bien_the"] == "ea_m1_" + that)
    assert dung["lech_dau"] is None and dung["khop_den"] == 1.0 and dung["khop_dong"] == 1.0 and dung["khac_lot"] == 0
    assert dung["phan_ra"] == {"cap": pytest.approx(0.0, abs=1e-6), "chi_bien_the": 0.0, "chi_tester": 0.0}


@can_cxx
def test_bien_the_bar_khong_khop_het_du_lieu_co_dap_an_nhay_nhung_ea_dung_thu_tu_khop(exe):
    ca, m1, b = B.tao_ca_tong_hop(exe, seed=5, ngay=1.0, thu_tu_that="cao_truoc")
    rows = B.chay_mot_ca(ca, B.bien_the_mac_dinh(), exe=exe, m1=m1, bang_tester=b)
    t = B.tong_hop(rows)
    assert t[0]["bien_the"] == "ea_m1_cao_truoc"
    khop = {r["bien_the"]: r["ti_le_khop"] for r in rows}
    assert max(v for k, v in khop.items() if k.startswith("bar_")) < 0.9           # cau hinh nhay: nen lon khong tai lap duoc tung lenh


@can_cxx
def test_chay_ea_khop_lai_tay_voi_tick_sinh_tu_m1(exe):
    ca, m1, b = B.tao_ca_tong_hop(exe, seed=1, ngay=1.0, thu_tu_that="cao_truoc")
    kq = B.chay_ea(ca, m1, B.BienThe("e", "ea", "M1", thu_tu="cao_truoc"), exe)
    assert len(kq.bang) == len(b) and kq.lai == pytest.approx(float(b["lai"].sum()), abs=1e-9)
    assert kq.lai_nam_pct == pytest.approx(kq.lai / ca.von / ca.nam * 100.0) and kq.dd_pct >= 0.0
    # nhan spread = 0: lai cao hon (khong tra spread)
    kq0 = B.chay_ea(ca, m1, B.BienThe("e0", "ea", "M1", thu_tu="cao_truoc", nhan_spread=0.0), exe)
    assert kq0.lai > kq.lai


@can_cxx
def test_chay_ea_dung_cau_hinh_da_chot_tick_1_point_60_giay_5_chu_so(exe):
    """Tester tong hop cung do `chay_ea` sinh ra nen kiem co-dap-an khong bat duoc loi cau hinh chung: ghim cau hinh bang cach goi san gia truc tiep."""
    m1 = B.m1_tong_hop(seed=2, ngay=1.0)
    ca = dataclasses.replace(_ca_tay(m1, ts=B.CAU_HINH_NHAY, ngay=1), f=1.32)
    qc = B.quy_cach_ca(ca)
    ps = G.tham_so_ea_tu_luoi(LU.ThamSo(**dict(B.CAU_HINH_NHAY, khop_bar="duong_di")))
    ps["InpPipSize"] = qc.pip
    tk = G.tick_tu_bar(m1, "thap_truoc", point=qc.point, giay_bar=60.0, paso=qc.point)
    r = G.chay(exe, tk, ca.von * ca.f, ps, digits=5, han_giay=1800)
    assert r["ok"] and len(r["lenh"]) > 50
    tay = B.bang_tu_ea(r["lenh"], tk, qc, ca.f)
    kq = B.chay_ea(ca, m1, B.BienThe("e", "ea", "M1", thu_tu="thap_truoc"), exe)
    assert len(kq.bang) == len(tay) and kq.lai == pytest.approx(float(tay["lai"].sum()), abs=1e-9)
    assert kq.bang["gia_mo"].to_numpy() == pytest.approx(tay["gia_mo"].to_numpy())
    # gio mo / dong den tung giay phu thuoc `giay_bar` (rai tick trong nen); sut giam % phu thuoc von * f dua cho EA
    assert kq.bang["mo"].equals(tay["mo"]) and kq.bang["dong"].equals(tay["dong"])
    assert kq.dd_pct > 0 and kq.dd_pct == pytest.approx(float(r["kq"]["max_dd_pct"]))


@can_cxx
def test_chay_ea_nhan_spread_dua_vao_gia_san_va_tru_dung_spread_da_nhan(exe):
    m1 = B.m1_tong_hop(seed=2, ngay=1.0, spread_pts=20)
    ca = dataclasses.replace(_ca_tay(m1, ts=B.CAU_HINH_NHAY, ngay=1), f=1.32)
    kq = B.chay_ea(ca, m1, B.BienThe("e", "ea", "M1", thu_tu="thap_truoc", nhan_spread=2.0), exe)
    mua, ban = kq.bang[kq.bang["chieu"] > 0], kq.bang[kq.bang["chieu"] < 0]
    assert len(mua) > 5 and len(ban) > 5
    assert (mua["gia_mo"] - mua["bid_mo"]).to_numpy() == pytest.approx(2 * 20 * 1e-5, abs=1e-9)       # MUA mo o ASK = BID + 2 x 20 point
    assert (ban["gia_mo"] - ban["bid_mo"]).abs().max() == 0                                             # BAN mo o BID
    dong_ban = ban[ban["dong"].notna()]
    assert len(dong_ban) > 0 and (dong_ban["gia_dong"] - dong_ban["bid_dong"]).to_numpy() == pytest.approx(2 * 20 * 1e-5, abs=1e-9)


@can_cxx
def test_tu_kiem_in_bang_va_tra_dung_thu_tu_gieo(exe):
    dong = []
    t = B.tu_kiem(exe, dong.append, thu_tu_that="thap_truoc", seeds=(1,), ngay=1.0)
    assert t[0]["bien_the"] == "ea_m1_thap_truoc" and any("thap_truoc" in d for d in dong)
    assert B.main(["--tu-kiem"]) == 0
