# -*- coding: utf-8 -*-
"""nhan/thu_chuyen_tim.py - giai doan 2 cua phep thu "chuyen bot sang tai san khac": QUY TRINH TIM tham so tren the gioi nhan tao (10/10/2026).

Module nay quyet dinh "tim thong minh co hon ngau nhien o ngan sach ngang khong" (ket luan chinh cua S1 giai doan 2), nen moi cho no TINH
SAI MA VAN CHAY DUOC deu lam lech ket luan ma khong ai thay. Test kiem theo tung lop, tu ham nho den duong chay day du:
  (1) ham nho: dat/tach ten bien the, chon top khac nhau, Spearman, can tren Clopper-Pearson (doi chieu dinh nghia xac suat nhi thuc);
  (2) cong xac nhan `cong_xac_nhan`: moi nhanh ly do (chay tai khoan / it lenh / khong lai / khong chot duoc lot / xac nhan lo / maxDD) bang
      engine THAY (khong can gia), + lot = min(lot cham maxDD 80 %, tran don bay), + chay engine THAT tren the gioi nhan tao;
  (3) `so_sanh_quy_trinh` (HAM THUAN) tren mot be mat diem tron co dap an biet truoc: moi o chi ton engine MOT lan, ngan sach ngang dung so,
      FULL tim ra dinh that, top-k chon theo duong KIEM, hoi tiec = (dap an - diem)/dap an, ba chuan, T0 khong ap duoc, dung hat cung ket qua;
  (4) gop ket qua (`tong_hop_giai_doan_2`): thong ke hoi tiec, gate, cap doi bootstrap phan tang (moi tang trong so ngang), Z0 / nhieu tach rieng;
  (5) ke hoach dong bang (`ke_hoach_s2`, nguong), doc dap an / ket qua tu tep, `main tong-hop`;
  (6) duong chay day du NHO (1 hat, duong 0,3 nam) `giai_doan_2` -> tep -> `tong_hop_giai_doan_2` (cham, ~12 giay): hop dong giua ben sinh
      ket qua va ben gop ket qua - noi thay doi mot ben ma quen ben kia."""
from __future__ import annotations

import json
import math
from types import SimpleNamespace

import numpy as np
import pytest

from nhan import dich_tham_so as DT
from nhan import do_thong_minh as DM
from nhan import luoi as LU
from nhan import nc_thi_nghiem as NT
from nhan import thu_chuyen as T
from nhan import thu_chuyen_tim as TT

KIEU = T.KIEU["phang"]
VON = T.VON


# ================================================================================================ (1) ham nho
def test_tach_ten_bien_the_la_nguoc_cua_ten_bien_the():
    n = 0
    for qm in T.KIEU_QUY_MO:
        for w in T.W_THU:
            for tam in T.TAM_THU:
                for san in T.SAN_THU:
                    ten = T.ten_bien_the(qm, w, tam, san)
                    assert TT.tach_ten_bien_the(ten) == (qm, float(w), tam, float(san)), ten
                    n += 1
    assert n == len(T.KIEU_QUY_MO) * len(T.W_THU) * len(T.TAM_THU) * len(T.SAN_THU)


@pytest.mark.parametrize("ten", [
    "A_ref|w=0.5|tam=I6",                       # thieu mot phan
    "A_ref|w=0.5|tam=I6|san=0|them",            # thua mot phan
    "A_ref|x=0.5|tam=I6|san=0",                 # sai tien to
    "A_ref|w=0.5|ham=I6|san=0",
    "A_ref|w=0.5|tam=I6|so=0",
    "A_ref|w=abc|tam=I6|san=0",                 # khong phai so
    "A_ref|w=0.5|tam=I6|san=xyz",
    "khong_co_kieu|w=0.5|tam=I6|san=0",         # kieu quy mo la
    "A_ref|w=0.5|tam=ZZ|san=0",                 # tam thu la
    "A_ref|w=1.5|tam=I6|san=0",                 # w ngoai [0, 1]
    "A_ref|w=-0.1|tam=I6|san=0",
    "A_ref|w=0.5|tam=I6|san=-1",                # san am
    "", "None",
])
def test_tach_ten_bien_the_tu_choi_ten_sai_dang(ten):
    with pytest.raises(ValueError):
        TT.tach_ten_bien_the(ten)


def test_chon_top_khac_nhau_khong_lay_hai_o_ke_nhau_va_dung_khi_het_o():
    cn = np.full((6, 6, 6), np.nan)
    cn[1, 1, 1] = 10.0
    cn[1, 2, 1] = 9.0               # ke (1,1,1) tren mot truc -> bi loai
    cn[2, 2, 2] = 8.5               # ke cheo (lech 1 o ca ba truc) -> cung bi loai
    cn[4, 4, 4] = 8.0
    cn[1, 3, 1] = 7.0               # cach (1,1,1) 2 o tren mot truc -> duoc phep
    cn[3, 1, 1] = 6.0
    goc = cn.copy()
    ra = TT.chon_top_khac_nhau(cn, 10)
    assert ra == [(1, 1, 1), (4, 4, 4), (1, 3, 1), (3, 1, 1)]
    assert all(isinstance(i, int) for o in ra for i in o)
    assert np.array_equal(cn, goc, equal_nan=True), "ham khong duoc ghi len mang vao"
    assert TT.chon_top_khac_nhau(cn, 2) == [(1, 1, 1), (4, 4, 4)]
    assert TT.chon_top_khac_nhau(cn, 0) == []
    assert TT.chon_top_khac_nhau(np.full((3, 3, 3), np.nan), 5) == []


def test_tuong_quan_hang_don_dieu_nguoc_none_khi_it_cap_hoac_khong_doi():
    x = [1, 2, 3, 4, 5, 6]
    assert TT.tuong_quan_hang(x, [2, 4, 6, 8, 10, 12]) == pytest.approx(1.0)
    assert TT.tuong_quan_hang(x, [v ** 3 for v in x]) == pytest.approx(1.0)       # chi hang, khong phai tuyen tinh
    assert TT.tuong_quan_hang(x, x[::-1]) == pytest.approx(-1.0)
    assert TT.tuong_quan_hang([1, 2, 3, 4, np.nan, 6, 7], [2, 4, 6, 8, 99, 12, 14]) == pytest.approx(1.0)   # cap NaN bi bo
    assert TT.tuong_quan_hang([1, 2, 3, 4], [1, 2, 3, 4]) is None                 # < 5 cap
    assert TT.tuong_quan_hang([1, 2, 3, 4, np.nan], [1, 2, 3, 4, 5]) is None      # bo NaN con 4 cap
    assert TT.tuong_quan_hang([1, 1, 1, 1, 1, 1], [1, 2, 3, 4, 5, 6]) is None     # mot day khong doi
    r = TT.tuong_quan_hang([1, 2, 2, 3, 4, 5], [1, 2, 3, 3, 4, 6])              # co dong hang: van trong [-1, 1], khong sap
    assert r is not None and 0.8 < r <= 1.0


def test_can_tren_clopper_pearson_la_can_tren_xac_suat_nhi_thuc_dung_nghia():
    from scipy.stats import binom
    assert TT.can_tren_clopper_pearson(0, 0) is None and TT.can_tren_clopper_pearson(3, -1) is None
    assert TT.can_tren_clopper_pearson(5, 5) == 1.0 and TT.can_tren_clopper_pearson(9, 5) == 1.0
    assert TT.can_tren_clopper_pearson(0, 20) == pytest.approx(1 - 0.05 ** (1 / 20))      # 0 dat / 20 -> ~13,9 % (xap xi "quy tac 3": 15 %)
    for x, n in ((0, 12), (3, 12), (7, 30), (29, 30), (1, 100)):
        u = TT.can_tren_clopper_pearson(x, n)
        assert 0.0 < u < 1.0 and u > x / n
        assert binom.cdf(x, n, u) == pytest.approx(0.05, abs=1e-9), (x, n)               # chinh la p ma P(X <= x | n, p) = 5 %
    assert TT.can_tren_clopper_pearson(0, 20) > TT.can_tren_clopper_pearson(0, 40)       # nhieu mau hon -> can sat hon
    assert TT.can_tren_clopper_pearson(2, 20) > TT.can_tren_clopper_pearson(1, 20)       # nhieu dat hon -> can cao hon
    assert TT.can_tren_clopper_pearson(2, 20, 0.99) > TT.can_tren_clopper_pearson(2, 20, 0.90)


# ================================================================================================ (2) cong xac nhan
class _KQ:
    """Ket qua engine gia: chi cac truong ma `cong_xac_nhan` doc."""

    def __init__(self, equity, so_lenh=50, chay=False, margin=0.0, loi=5.0):
        self.duong_equity = np.asarray(equity, float)
        self.so_lenh, self.chay, self.margin, self.loi = so_lenh, chay, margin, loi


@pytest.fixture
def engine_gia(monkeypatch):
    """`dl` truyen vao chinh la `_KQ` se tra ve: bo qua nhan C va gia, kiem DUNG phan quyet dinh cua `cong_xac_nhan`."""
    monkeypatch.setattr(TT.LU, "chay_mang", lambda dl, ts, von, ghi_lenh=False: dl)
    monkeypatch.setattr(TT.LU, "chi_so", lambda kq, von: {"loi_suat_nam_pct": kq.loi})


_TS = SimpleNamespace(don_bay=1.0)
_E_TIM_DIP_LON = VON + np.array([0, 100, -200, 300, 100, 600.0])      # day sau 300 -> lot cham maxDD 80 % khoang 36
_E_TIM_DIP_NHO = VON + np.array([0, 100, 50, 200, 150, 300.0])       # sut giam nho -> lot khong bi cham tran maxDD, chi bi tran don bay
_E_XN_TOT = VON + np.array([0, 50, 20, 100, 80, 150.0])


def test_cong_xac_nhan_chay_tai_khoan_o_duong_tim(engine_gia):
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_NHO, chay=True), _KQ(_E_XN_TOT))
    assert r == {"dat_kham_pha": False, "dat": False, "k": None, "lai_tong": None, "maxdd": None, "ly_do": "chay_tai_khoan_o_duong_tim"}


def test_cong_xac_nhan_it_lenh_o_duong_tim_bien_giu_20(engine_gia):
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_NHO, so_lenh=TT.SO_LENH_TOI_THIEU - 1), _KQ(_E_XN_TOT))
    assert r["ly_do"] == "it_lenh_o_duong_tim" and not r["dat_kham_pha"] and r["k"] is None
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_NHO, so_lenh=TT.SO_LENH_TOI_THIEU), _KQ(_E_XN_TOT))
    assert r["dat_kham_pha"] and r["ly_do"] == ""                                      # dung 20 lenh la du


@pytest.mark.parametrize("loi", [0.0, -3.0])
def test_cong_xac_nhan_khong_co_lai_o_duong_tim(engine_gia, loi):
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_NHO, loi=loi), _KQ(_E_XN_TOT))
    assert r["ly_do"] == "khong_co_lai_o_duong_tim" and not r["dat_kham_pha"]          # lai = 0 cung la khong co lai


def test_cong_xac_nhan_khong_chot_duoc_lot(engine_gia):
    r = TT.cong_xac_nhan(_TS, _KQ([VON]), _KQ(_E_XN_TOT))                              # duong equity 1 diem: khong tinh duoc lot
    assert r["ly_do"] == "khong_chot_duoc_lot" and not r["dat_kham_pha"] and r["k"] is None


def test_cong_xac_nhan_lot_la_min_cua_lot_cham_maxdd_va_tran_don_bay(engine_gia):
    kd = NT._he_so_lot_tai_tran(_E_TIM_DIP_LON, VON)
    assert 30.0 < kd < 40.0, "gia dinh cua bai test: lot cham maxDD 80 %% o khoang 36 (duoc %s)" % kd
    # margin nho -> tran don bay rong (kl = 10 x 10000 / 100 = 1000) -> lot bi chan boi MAXDD
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_LON, margin=100.0), _KQ(_E_XN_TOT))
    assert r["k"] == pytest.approx(kd)
    # margin lon -> tran don bay hep (kl = 10 x 10000 / 10000 = 10) -> lot bi chan boi DON BAY
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_LON, margin=10000.0), _KQ(_E_XN_TOT))
    assert r["k"] == pytest.approx(T.DON_BAY_TOI_DA * VON / 10000.0) and r["k"] < kd
    # don bay cua tham so nhan vao notional: gap doi don bay -> tran lot giam mot nua
    r2 = TT.cong_xac_nhan(SimpleNamespace(don_bay=2.0), _KQ(_E_TIM_DIP_LON, margin=10000.0), _KQ(_E_XN_TOT))
    assert r2["k"] == pytest.approx(r["k"] / 2)
    # tham so tran don bay duoc ton trong
    r3 = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_LON, margin=10000.0), _KQ(_E_XN_TOT), don_bay_toi_da=5.0)
    assert r3["k"] == pytest.approx(5.0)


def test_cong_xac_nhan_dat_khop_phep_tinh_tay(engine_gia):
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_LON, margin=10000.0), _KQ(_E_XN_TOT))     # k = 10
    assert r["dat_kham_pha"] and r["dat"] and r["ly_do"] == "" and r["k"] == pytest.approx(10.0)
    # v = 10000 + 10 x (e - 10000) = [10000, 10500, 10200, 11000, 10800, 11500]
    assert r["lai_tong"] == pytest.approx(0.15)
    assert r["maxdd"] == pytest.approx(1 - 10200 / 10500)                               # sut giam 2,857 % o buoc 3


def test_cong_xac_nhan_xac_nhan_lo_thi_khong_dat_du_da_qua_kham_pha(engine_gia):
    e_lo = VON + np.array([0, 10, -5, -10.0])
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_LON, margin=10000.0), _KQ(e_lo))
    assert r["dat_kham_pha"] is True and r["dat"] is False and r["ly_do"] == "lo_o_duong_xac_nhan"
    assert r["lai_tong"] == pytest.approx(-0.01) and r["maxdd"] < 0.8


def test_cong_xac_nhan_hoa_von_khong_phai_lai_va_von_con_dung_0_la_hong(engine_gia):
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_LON, margin=10000.0), _KQ(VON + np.array([0, 100, -50, 0.0])))      # k = 10, ket thuc dung bang von
    assert r["lai_tong"] == pytest.approx(0.0, abs=1e-12) and r["dat"] is False and r["ly_do"] == "lo_o_duong_xac_nhan"
    r = TT.cong_xac_nhan(_TS, _KQ(_E_TIM_DIP_NHO, margin=2000.0), _KQ(VON + np.array([0, 100, -200, 10.0])))    # k = 50: v = 10000 + 50 x (-200) = 0 dung
    assert r["ly_do"] == "von_am_o_duong_xac_nhan" and r["lai_tong"] is None and r["dat"] is False


def test_cong_xac_nhan_maxdd_tu_80_phan_tram_o_duong_xac_nhan(engine_gia):
    e_tim = _E_TIM_DIP_NHO                                                             # lot bi chan boi tran don bay, khong boi maxDD
    e_xn = VON + np.array([0, 100, -145, 50.0])                                         # lot 50: v = [10000, 15000, 2750, 12500]
    r = TT.cong_xac_nhan(_TS, _KQ(e_tim, margin=2000.0), _KQ(e_xn))
    assert r["k"] == pytest.approx(50.0)
    assert r["lai_tong"] == pytest.approx(0.25) and r["maxdd"] == pytest.approx(1 - 2750 / 15000) and r["maxdd"] >= 0.8
    assert r["dat_kham_pha"] is True and r["dat"] is False and r["ly_do"] == "maxdd_tu_80_phan_tram"


def test_cong_xac_nhan_von_am_chay_tai_khoan_va_it_lenh_o_duong_xac_nhan(engine_gia):
    tim = _KQ(_E_TIM_DIP_NHO, margin=2000.0)                                           # k = 50
    r = TT.cong_xac_nhan(_TS, tim, _KQ(VON + np.array([0, 50, -250, 10.0])))           # v = 10000 + 50 x (-250) < 0
    assert r["ly_do"] == "von_am_o_duong_xac_nhan" and r["dat_kham_pha"] and not r["dat"] and r["lai_tong"] is None
    r = TT.cong_xac_nhan(_TS, tim, _KQ(VON + np.array([0, 50, np.nan, 10.0])))        # equity khong huu han cung bi xem la hong
    assert r["ly_do"] == "von_am_o_duong_xac_nhan" and not r["dat"]
    r = TT.cong_xac_nhan(_TS, tim, _KQ(_E_XN_TOT, chay=True))
    assert r["ly_do"] == "chay_tai_khoan_o_duong_xac_nhan" and r["dat_kham_pha"] and not r["dat"]
    r = TT.cong_xac_nhan(_TS, tim, _KQ(_E_XN_TOT, so_lenh=TT.SO_LENH_TOI_THIEU - 1))
    assert r["ly_do"] == "it_lenh_o_duong_xac_nhan" and r["dat_kham_pha"] and not r["dat"]


def test_cong_xac_nhan_tren_engine_that_khop_phep_tinh_lai_tu_dau():
    """Engine THAT (nhan C) tren hai duong cua the gioi hoi quy: ket qua phai khop cong thuc, ca khi duong xac nhan KHONG la duong tim."""
    dls = T.dung_duong(T.GOC, "TEST_TT_CXN", 2, 1.0, 15)
    ts = KIEU.tham_so(60.0, 60.0, 8)
    r = TT.cong_xac_nhan(ts, dls[0], dls[1])
    assert r["dat_kham_pha"] is True and r["dat"] is True and r["ly_do"] == ""        # the gioi hoi quy, luoi hop ly: qua ca hai duong
    kq_tim = LU.chay_mang(dls[0], ts, VON)
    kl = T.DON_BAY_TOI_DA * VON / (kq_tim.margin * ts.don_bay)
    assert 0 < r["k"] <= kl * (1 + 1e-12)                                              # khong bao gio qua tran don bay
    e = np.asarray(LU.chay_mang(dls[1], ts, VON).duong_equity, float)
    v = VON + r["k"] * (e - VON)
    assert r["lai_tong"] == pytest.approx(v[-1] / VON - 1.0)
    assert r["maxdd"] == pytest.approx(float(np.max(1.0 - v / np.maximum.accumulate(v)))) and 0 <= r["maxdd"] < 0.8
    # doi duong xac nhan: ket qua doi (cong KHONG chi phu thuoc duong tim) nhung van nhat quan voi dinh nghia
    r2 = TT.cong_xac_nhan(ts, dls[0], dls[0])
    assert r2["k"] == pytest.approx(r["k"]) and r2["lai_tong"] != pytest.approx(r["lai_tong"])
    # random walk: dat phai di kem lai > 0 va maxDD < 80 %; khong dat thi PHAI co ly do
    rw = T.dung_duong(T.GOC.doi(hoi_quy=False), "TEST_TT_CXN_RW", 2, 1.0, 15)
    r3 = TT.cong_xac_nhan(ts, rw[0], rw[1])
    if r3["dat"]:
        assert r3["lai_tong"] > 0 and r3["maxdd"] < 0.8
    else:
        assert r3["ly_do"] != ""


# ================================================================================================ o ngau nhien + bo nho
def test_o_ngau_nhien_gan_cho_dung_so_o_moi_trong_khoang_luoi_cuc_bo():
    goc = KIEU.tham_so(60.0, 60.0, 8)
    da_co = {DM._khoa(goc)}
    rng = np.random.default_rng(3)
    moi = TT._o_ngau_nhien_gan([goc], 25, rng, 5.0, da_co)
    khoa = [DM._khoa(t) for t in moi]
    assert len(moi) == 25 and len(set(khoa)) == 25 and DM._khoa(goc) not in khoa
    assert len(da_co) == 26                                                            # tap da co duoc ghi them de lan sau khong trung
    for t in moi:
        assert 30.0 - 1e-9 <= t.buoc <= 120.0 + 1e-9                                   # buoc x [0,5 .. 2,0]
        assert 18.0 - 1e-9 <= t.tp <= 192.0 + 1e-9 and t.tp >= 5.0                     # tp = buoc goc x he so buoc x he so tp [0,6 .. 1,6]
        assert 4 <= t.tran_tang <= 16                                                  # tang x [0,5 .. 2,0], lam tron
    moi2 = TT._o_ngau_nhien_gan([goc], 25, rng, 5.0, da_co)
    assert not ({DM._khoa(t) for t in moi2} & set(khoa))                              # lan sau khong lap lai o da lay
    # xac dinh theo rng
    a = TT._o_ngau_nhien_gan([goc], 5, np.random.default_rng(11), 5.0, set())
    b = TT._o_ngau_nhien_gan([goc], 5, np.random.default_rng(11), 5.0, set())
    assert [DM._khoa(t) for t in a] == [DM._khoa(t) for t in b]


def test_o_ngau_nhien_gan_ap_san_khoang_cach():
    goc = KIEU.tham_so(10.0, 10.0, 8)
    moi = TT._o_ngau_nhien_gan([goc], 20, np.random.default_rng(5), 40.0, set())
    assert moi and all(t.buoc >= 40.0 and t.tp >= 40.0 for t in moi)                  # san phan giai / chi phi duoc ap cho moi o


def test_o_ngau_nhien_gan_co_tran_so_lan_thu_khong_lap_vo_han(monkeypatch):
    goc = KIEU.tham_so(60.0, 60.0, 8)
    goi = []

    def bien_the_hong(g, fb, ft, fm, sb, st):
        goi.append(1)
        return g                                                                       # luon ra chinh o goc (da co) -> khong bao gio them duoc
    monkeypatch.setattr(TT.DM, "bien_the", bien_the_hong)
    assert TT._o_ngau_nhien_gan([goc], 3, np.random.default_rng(1), 5.0, {DM._khoa(goc)}) == []
    assert len(goi) == 60 * 3


def test_nho_nho_moi_o_tinh_mot_lan_giu_thu_tu_va_bao_loi_do_dai_sai():
    cac_lan = []

    def dg(cac):
        cac_lan.append([DM._khoa(t) for t in cac])
        return [t.buoc for t in cac]
    f = TT._nho_nho(dg)
    a, b, c = (KIEU.tham_so(x, x, 8) for x in (10.0, 20.0, 30.0))
    assert f([a, b, a]) == [10.0, 20.0, 10.0]
    assert cac_lan == [[DM._khoa(a), DM._khoa(b)]]                                     # trung trong cung mot goi chi tinh mot lan
    assert f([b, c]) == [20.0, 30.0] and cac_lan[1] == [DM._khoa(c)]                  # b da co trong bo nho
    assert f([c, b, a]) == [30.0, 20.0, 10.0] and len(cac_lan) == 2                   # khong co o moi -> khong goi lai
    assert f([]) == []
    with pytest.raises(ValueError, match="danh_gia tra 1 diem cho 2 o"):
        TT._nho_nho(lambda cac: [1.0])([a, b])


# ================================================================================================ (3) so_sanh_quy_trinh
SAN = 5.0


def _mat(ts) -> float:
    """Be mat diem tron, dinh o buoc ~80, tp = buoc, 8 tang: dap an biet truoc, khong phu thuoc gia."""
    return 100.0 - 20.0 * math.log(ts.buoc / 80.0) ** 2 - 30.0 * math.log(ts.tp / ts.buoc) ** 2 - 2.0 * (ts.tran_tang - 8) ** 2


class _Thu:
    """Chay `so_sanh_quy_trinh` voi be mat `_mat` va ghi lai moi goi vao cac ham do."""

    def __init__(self, san=SAN, ung_vien="mac_dinh", t0="co", b1="co", hat=7, dap_an="max", be_mat="co", kiem=None):
        self.goi_tim, self.goi_kiem, self.goi_b, self.goi_cong, self.o_tim = [], [], [], [], []
        self.san = san
        self.cac, self.chi = T.luoi_o_dap_an(KIEU, san)
        self.dap_an = max(_mat(t) for t in self.cac) if dap_an == "max" else dap_an
        self.ts_b0 = KIEU.tham_so(30.0, 30.0, 4)
        self.ts_t0 = KIEU.tham_so(60.0, 60.0, 8) if t0 == "co" else None
        self.ts_b1 = KIEU.tham_so(100.0, 100.0, 12) if b1 == "co" else None
        self.uv = [KIEU.tham_so(60.0, 60.0, 8), KIEU.tham_so(40.0, 40.0, 6)] if ung_vien == "mac_dinh" else ung_vien
        bm = np.full((len(T.BUOC), len(T.TY_LE_TP), len(T.TANG)), np.nan)
        for (ib, ir, it), ts in zip(self.chi, self.cac):
            bm[ib, ir, it] = _mat(ts)
        self.be_mat = bm if be_mat == "co" else (None if be_mat is None else be_mat(bm))
        self._kiem = kiem
        self.r = TT.so_sanh_quy_trinh(KIEU, self.uv, self.ts_b0, self.ts_t0, self.ts_b1, san, self._tim, self._kiem_f, self._b, self._cong,
                                      np.random.default_rng(hat), self.dap_an, self.be_mat)

    def _tim(self, cac):
        self.goi_tim.extend(DM._khoa(t) for t in cac)
        self.o_tim.extend(cac)
        return [_mat(t) for t in cac]

    def _kiem_f(self, cac):
        self.goi_kiem.append(list(cac))
        return [(_mat(t) + 0.01 * i) if self._kiem is None else self._kiem(t) for i, t in enumerate(cac)]

    def _b(self, cac):
        self.goi_b.append(list(cac))
        return [_mat(t) for t in cac]

    def _cong(self, cac):
        self.goi_cong.append(list(cac))
        return [{"dat_kham_pha": _mat(t) > 50, "dat": _mat(t) > 60, "k": 2.0, "ly_do": "" if _mat(t) > 50 else "khong_co_lai_o_duong_tim"} for t in cac]


@pytest.fixture(scope="module")
def thu():
    return _Thu()


def _tiep(ten_goc, ks=TT.TOP_K_THU):
    return ["%s_%d" % (ten_goc, k) for k in ks]


def test_so_sanh_moi_o_chi_ton_engine_mot_lan_va_cong_goi_mot_lan(thu):
    assert len(thu.goi_tim) == len(set(thu.goi_tim)), "cung mot o tren cung mot duong bi do hai lan"
    assert len(thu.goi_b) == 1 and len(thu.goi_cong) == 1                              # cham tap B va cong: MOT goi cho tat ca o khac nhau
    ks = [DM._khoa(t) for t in thu.goi_b[0]]
    assert len(ks) == len(set(ks)) and [DM._khoa(t) for t in thu.goi_cong[0]] == ks
    assert thu.goi_kiem and all(len(c) >= 2 for c in thu.goi_kiem) and {len(c) for c in thu.goi_kiem} == {4, 12}   # k = 1 khong can duong kiem


def test_so_sanh_co_du_ba_chuan_chin_quy_trinh_ba_muc_top_k(thu):
    qt = thu.r["quy_trinh"]
    mong = {"B0", "T0", "B1"} | {"%s_%d" % (q, k) for q in TT.QUY_TRINH_TIM for k in TT.TOP_K_THU}
    assert set(qt) == mong and len(qt) == 30
    for ten in TT.CAC_CHUAN:
        assert qt[ten]["so_phep_thu"] == 0 and qt[ten]["so_kiem"] == 0                 # chuan khong ton phep thu nao
    for q in TT.QUY_TRINH_TIM:
        assert qt["%s_1" % q]["so_kiem"] == 0 and qt["%s_4" % q]["so_kiem"] == 4 and qt["%s_12" % q]["so_kiem"] == 12
        phep = {qt["%s_%d" % (q, k)]["so_phep_thu"] for k in TT.TOP_K_THU}
        assert len(phep) == 1 and phep == {thu.r["ngan_sach"][q]}                      # moi k cung mot ngan sach cua quy trinh


def test_so_sanh_ngan_sach_ngang_giua_thong_minh_va_ngau_nhien(thu):
    ns = thu.r["ngan_sach"]
    n_full = len(thu.cac)
    assert thu.r["so_o_luoi_dap_an"] == n_full == 404
    assert ns["FULL_RAW"] == ns["FULL_PLAT"] == n_full
    assert ns["SMART"] == ns["SMARTRAW"] == ns["RANDT"] == ns["RAND"]                  # ngau nhien do DUNG so o ma SMART da do
    assert ns["SMART_S"] == ns["RANDT_S"] == ns["RAND_S"]
    assert 0 < ns["SMART_S"] <= len(thu.uv) + TT.SO_O_LUOI_CUC_BO - 1                  # ngan sach nho = ung vien + 1 luoi cuc bo (tru o trung tam)
    assert ns["SMART_S"] < ns["SMART"] < n_full


def test_so_sanh_full_tim_dung_dinh_that_va_hoi_tiec_bang_khong(thu):
    tot = max(thu.cac, key=_mat)
    for ten in ("FULL_RAW_1", "FULL_PLAT_1"):
        e = thu.r["quy_trinh"][ten]
        assert (e["buoc"], e["tp"], e["tang"]) == (tot.buoc, tot.tp, tot.tran_tang)
        assert e["hoi_tiec"] == pytest.approx(0.0, abs=1e-12) and e["diem_b"] == pytest.approx(_mat(tot))
    assert thu.r["rho_xep_hang_full"] == pytest.approx(1.0)                            # cung be mat -> hang giong het
    # thong minh gan dap an hon cac chuan xa dinh (B0: 30 pip, 4 tang)
    assert thu.r["quy_trinh"]["SMART_1"]["hoi_tiec"] < thu.r["quy_trinh"]["B0"]["hoi_tiec"]
    assert thu.r["quy_trinh"]["T0"]["hoi_tiec"] == pytest.approx(T.hoi_tuong_doi(thu.dap_an, _mat(thu.ts_t0)))


def test_so_sanh_hoi_tiec_none_khi_khong_co_dap_an_hoac_dap_an_khong_duong():
    for dap_an in (None, 0.0, -5.0):
        r = _Thu(dap_an=dap_an).r
        assert all(e["hoi_tiec"] is None for e in r["quy_trinh"].values()), dap_an
        assert all(e["ap_duoc"] for e in r["quy_trinh"].values())


def test_so_sanh_rho_none_khi_khong_co_be_mat_va_dao_dau_khi_be_mat_nguoc():
    assert _Thu(be_mat=None).r["rho_xep_hang_full"] is None
    nguoc = _Thu(be_mat=lambda bm: -bm).r["rho_xep_hang_full"]
    assert nguoc == pytest.approx(-1.0)


def test_so_sanh_top_k_chon_theo_duong_kiem_khong_theo_duong_tim():
    t = _Thu(kiem=lambda ts: ts.buoc)                                                  # duong kiem thich buoc LON nhat
    d = np.array([_mat(c) for c in t.cac])
    for k in (4, 12):
        top = [t.cac[j] for j in np.argsort(-d, kind="stable")[:k]]                    # k o tot nhat theo duong TIM
        chon = top[int(np.argmax([c.buoc for c in top]))]
        e = t.r["quy_trinh"]["FULL_RAW_%d" % k]
        assert (e["buoc"], e["tp"], e["tang"]) == (chon.buoc, chon.tp, chon.tran_tang), k
    e1 = t.r["quy_trinh"]["FULL_RAW_1"]                                                # k = 1: khong qua duong kiem, lay o tot nhat duong tim
    tot = t.cac[int(np.argmax(d))]
    assert (e1["buoc"], e1["tp"]) == (tot.buoc, tot.tp)
    # FULL_PLAT: top-k tren be mat CAO NGUYEN, khong hai o ke nhau; FULL_RAW: top-k theo diem tho -> neu duong kiem thich buoc lon, hai quy trinh chon khac nhau
    arr = np.full((len(T.BUOC), len(T.TY_LE_TP), len(T.TANG)), np.nan)
    o_cua = dict(zip(t.chi, t.cac))
    for i, c in zip(t.chi, t.cac):
        arr[i] = _mat(c)
    cn = DM.cao_nguyen_mang(arr)
    for k in (4, 12):
        top = [o_cua[i] for i in TT.chon_top_khac_nhau(cn, 12)][:k]
        chon_plat = top[int(np.argmax([c.buoc for c in top]))]
        e = t.r["quy_trinh"]["FULL_PLAT_%d" % k]
        assert (e["buoc"], e["tp"], e["tang"]) == (chon_plat.buoc, chon_plat.tp, chon_plat.tran_tang), k
    assert t.r["quy_trinh"]["FULL_PLAT_12"]["buoc"] > t.r["quy_trinh"]["FULL_RAW_12"]["buoc"], "o cach xa nhau phai cho buoc lon hon cum quanh dinh"
    t2 = _Thu(kiem=lambda ts: -ts.buoc)
    top12 = [t2.cac[j] for j in np.argsort(-d, kind="stable")[:12]]
    chon2 = top12[int(np.argmax([-c.buoc for c in top12]))]
    assert t2.r["quy_trinh"]["FULL_RAW_12"]["buoc"] == chon2.buoc != t.r["quy_trinh"]["FULL_RAW_12"]["buoc"]


def test_so_sanh_cong_gate_di_theo_tung_quy_trinh(thu):
    qt = thu.r["quy_trinh"]
    assert qt["B0"]["dat_kham_pha"] is False and qt["B0"]["dat_xac_nhan"] is False and qt["B0"]["ly_do_gate"] == "khong_co_lai_o_duong_tim"
    assert qt["B0"]["k_lot"] == 2.0                                                    # k duoc chuyen nguyen
    assert qt["T0"]["dat_kham_pha"] is True and qt["T0"]["dat_xac_nhan"] is True and qt["T0"]["ly_do_gate"] == ""
    for ten, e in qt.items():                                                          # gate khop be mat tai chinh o do
        assert e["dat_xac_nhan"] == (e["diem_b"] > 60) and e["dat_kham_pha"] == (e["diem_b"] > 50), ten


def test_so_sanh_t0_hoac_b1_khong_ap_duoc_chi_danh_dau_khong_lam_hong_phan_con_lai():
    r = _Thu(t0=None).r["quy_trinh"]
    assert r["T0"] == {"ap_duoc": False} and len(r) == 30 and all(r[k]["ap_duoc"] for k in r if k != "T0")
    r = _Thu(b1=None).r["quy_trinh"]
    assert r["B1"] == {"ap_duoc": False} and all(r[k]["ap_duoc"] for k in r if k != "B1")


def test_so_sanh_duoi_phan_giai_chi_danh_dau_cho_o_thap_hon_san():
    t = _Thu(san=40.0)
    qt = t.r["quy_trinh"]
    assert qt["B0"]["duoi_phan_giai"] is True                                          # 30 pip < san 40: chuan chep nguyen khong duoc nang san
    assert qt["T0"]["duoi_phan_giai"] is False
    for q in TT.QUY_TRINH_TIM:
        for k in TT.TOP_K_THU:
            e = qt["%s_%d" % (q, k)]
            assert e["duoi_phan_giai"] is False and min(e["buoc"], e["tp"]) >= 40.0 - 1e-9, (q, k)
    assert t.r["so_o_luoi_dap_an"] < 404                                                # nang san -> luoi dap an nho di


def test_so_sanh_ung_vien_thap_hon_san_bi_nang_len_san_truoc_khi_do():
    t = _Thu(san=40.0, ung_vien=[KIEU.tham_so(10.0, 10.0, 6), KIEU.tham_so(20.0, 90.0, 4), KIEU.tham_so(60.0, 60.0, 8)])
    assert t.o_tim and all(min(c.buoc, c.tp) >= 40.0 - 1e-9 for c in t.o_tim), "co o thap hon san duoc dua vao engine"
    assert t.r["smart_lich_su"][0]["so_phep_thu"] == 3                                  # (10,10,6)->(40,40,6), (20,90,4)->(40,90,4), (60,60,8): 3 o khac nhau
    assert (40.0, 40.0, 6) in {(c.buoc, c.tp, c.tran_tang) for c in t.o_tim} and (40.0, 90.0, 4) in {(c.buoc, c.tp, c.tran_tang) for c in t.o_tim}
    gop = _Thu(san=40.0, ung_vien=[KIEU.tham_so(10.0, 10.0, 6), KIEU.tham_so(30.0, 25.0, 6)])      # hai ung vien cung ve (40,40,6) -> gop con 1
    assert gop.r["smart_lich_su"][0]["so_phep_thu"] == 1


def test_so_sanh_khong_co_ung_vien_thi_bat_dau_tu_b0_da_ap_san():
    t = _Thu(ung_vien=[])
    h = t.r["smart_lich_su"]
    assert h[0]["buoc"] == "ung_vien" and h[0]["so_phep_thu"] == 1                    # dung MOT ung vien: chinh B0
    assert len(t.r["quy_trinh"]) == 30


def test_so_sanh_dung_hat_cung_ket_qua_cac_quy_trinh_khong_ngau_nhien_khong_phu_thuoc_hat():
    a, b = _Thu(hat=7).r, _Thu(hat=7).r
    assert a == b                                                                      # xac dinh theo hat
    c = _Thu(hat=8).r
    for q in ("FULL_RAW", "FULL_PLAT", "SMART", "SMARTRAW", "SMART_S"):
        for k in TT.TOP_K_THU:
            assert a["quy_trinh"]["%s_%d" % (q, k)] == c["quy_trinh"]["%s_%d" % (q, k)], (q, k)
    for ten in TT.CAC_CHUAN:
        assert a["quy_trinh"][ten] == c["quy_trinh"][ten]
    ngau = [q for q in a["quy_trinh"] if q.startswith("RAND")]
    assert any(a["quy_trinh"][q] != c["quy_trinh"][q] for q in ngau), "doi hat ma cac quy trinh ngau nhien giong het"


# ================================================================================================ (4) gop ket qua
def _qt(hoi_tiec, ap_duoc=True, kp=True, xn=True, duoi=False, phep=100, kiem=4):
    return {"ap_duoc": ap_duoc, "hoi_tiec": hoi_tiec, "duoi_phan_giai": duoi, "so_phep_thu": phep, "so_kiem": kiem, "dat_kham_pha": kp,
            "dat_xac_nhan": xn}


def _kb(ten, loai, kieu, hats, rho=None):
    return {"kich_ban": ten, "loai": loai, "kieu": kieu,
            "hat_ket_qua": [{"quy_trinh": h, "rho_xep_hang_full": (rho[i] if rho else None)} for i, h in enumerate(hats)]}


def _tap_ket_qua():
    smart_a, randt_a = [0.10, 0.00, 0.20, 0.05], [0.30, 0.20, 0.50, 0.25]
    smart_b, randt_b = [0.20, 0.10, 0.30, 0.00], [0.25, 0.20, 0.20, 0.10]
    gia_c = [0.10, 0.20, 0.30, 0.40]
    a = _kb("K2", "L1", "phang",
            [{"SMART_4": _qt(s, xn=(i != 3), phep=100 + i), "RANDT_4": _qt(r, kp=(i < 3), xn=False, phep=100 + i), "T0": _qt(0.4)}
             for i, (s, r) in enumerate(zip(smart_a, randt_a))], rho=[0.9, 0.8, 0.7, 0.6])
    b = _kb("K2", "L1", "geo", [{"SMART_4": _qt(s, duoi=(i == 0)), "RANDT_4": _qt(r)} for i, (s, r) in enumerate(zip(smart_b, randt_b))],
            rho=[0.5, 0.5, 0.5, 0.5])
    c = _kb("C2", "L2", "phang", [{"SMART_4": _qt(x), "RANDT_4": _qt(x)} for x in gia_c], rho=[0.2, 0.4, 0.6, 0.8])
    z = _kb("Z0", "L0", "phang", [{"SMART_4": _qt(0.0), "RANDT_4": _qt(0.5)} for _ in range(4)], rho=[1.0] * 4)
    n = _kb("N0", "L5", "phang", [{"SMART_4": _qt(None, xn=(i == 0)), "RANDT_4": _qt(None, xn=False, kp=False)} for i in range(4)])
    la = _kb("X9", "L9", "phang", [{"SMART_4": _qt(0.1)}])                              # loai la: bi bo qua
    return [a, b, c, z, n, la], dict(smart_a=smart_a, randt_a=randt_a, smart_b=smart_b, randt_b=randt_b, gia_c=gia_c)


def test_phan_vi_va_thong_ke_hoi_tiec():
    assert TT._phan_vi([], 0.5) is None and TT._phan_vi([None, float("nan"), float("inf")], 0.5) is None
    assert TT._phan_vi([1.0, 2.0, 3.0, None, 4.0], 0.5) == pytest.approx(2.5)
    assert TT._phan_vi([1.0, 2.0, 3.0, 4.0, 5.0], 0.9) == pytest.approx(4.6)
    assert TT._thong_ke_hoi_tiec([]) == {"n": 0} and TT._thong_ke_hoi_tiec([None, float("nan")]) == {"n": 0}
    xs = [0.0, 0.10, 0.15, 0.40, 0.50, 0.60, None, float("inf")]                       # None / inf bi bo; 0,15 va 0,50 la hai bien
    s = TT._thong_ke_hoi_tiec(xs)
    assert s["n"] == 6 and s["trung_vi"] == pytest.approx(0.275) and s["trung_binh"] == pytest.approx(1.75 / 6)
    assert s["ty_le_tot"] == pytest.approx(3 / 6)                                      # <= 0,15 tinh la tot (bien 0,15 tinh, 0,40 khong)
    assert s["ty_le_te"] == pytest.approx(1 / 6)                                       # > 0,5 tinh la te (bien 0,50 KHONG tinh)
    assert s["p90"] == pytest.approx(float(np.quantile([0.0, 0.10, 0.15, 0.40, 0.50, 0.60], 0.9)))


def test_hieu_cap_doi_chi_giu_cap_ap_duoc_va_co_hoi_tiec_huu_han():
    du_lieu = {"t1": [{"A": _qt(0.1), "B": _qt(0.3)},
                      {"A": _qt(0.1, ap_duoc=False), "B": _qt(0.3)},                   # A khong ap duoc
                      {"A": _qt(None), "B": _qt(0.3)},                                 # A khong co hoi tiec
                      {"A": _qt(0.1), "B": _qt(float("nan"))},                         # B khong huu han
                      {"A": _qt(0.1)},                                                 # thieu B
                      {"B": _qt(0.2)}],                                                # thieu A
               "t2": [{"A": _qt(0.2), "B": _qt(0.2)}], "t3": [{"A": _qt(None), "B": _qt(0.1)}]}
    assert TT._hieu_cap_doi(du_lieu, "A", "B") == {"t1": [(0.1, 0.3)], "t2": [(0.2, 0.2)]}


def test_bootstrap_phan_tang_trong_so_ngang_giua_cac_tang_va_ci_dung_phia():
    assert TT.bootstrap_phan_tang({}) == {"n_tang": 0, "n_cap": 0}
    # hai tang: tang X 1 cap hieu -1, tang Y 3 cap hieu +1 -> TB tung tang = 0 (KHONG phai 0,5 neu gop cap)
    tang = {"X": [(0.0, 1.0)], "Y": [(1.0, 0.0), (2.0, 1.0), (3.0, 2.0)]}
    r = TT.bootstrap_phan_tang(tang, so_lan=400, hat=1)
    assert r["n_tang"] == 2 and r["n_cap"] == 4 and r["hieu_trung_binh"] == pytest.approx(0.0)
    assert r["tung_tang"] == {"X": pytest.approx(-1.0), "Y": pytest.approx(1.0)} and r["so_tang_a_tot_hon"] == 1
    # tang duy nhat, moi hieu am: can tren CI < 0, trung vi a < trung vi b
    ro = TT.bootstrap_phan_tang({"A": [(0.1, 0.3), (0.0, 0.2), (0.2, 0.5), (0.05, 0.25)]}, so_lan=500, hat=2)
    assert ro["ci95_tren"] < 0 and ro["ci95_duoi"] <= ro["hieu_trung_binh"] <= ro["ci95_tren"]
    assert ro["trung_vi_a"] == pytest.approx(0.075) and ro["trung_vi_b"] == pytest.approx(0.275)
    assert ro["ty_so_trung_vi"] == pytest.approx(0.075 / 0.275) and ro["so_tang_a_tot_hon"] == 1
    # hieu doi dau luan phien: CI phai chua 0
    rd = TT.bootstrap_phan_tang({"A": [(0.1, 0.2), (0.2, 0.1)] * 5}, so_lan=500, hat=3)
    assert rd["hieu_trung_binh"] == pytest.approx(0.0) and rd["ci95_duoi"] < 0 < rd["ci95_tren"]
    # xac dinh theo hat
    assert TT.bootstrap_phan_tang(tang, 200, 5) == TT.bootstrap_phan_tang(tang, 200, 5)
    # hai dau khoang tin cay la phan vi 2,5 % va 97,5 % (khong phai 90 %): 5 cap hieu 1 + 5 cap hieu 0 -> trung binh lay lai = Nhi thuc(10; 0,5) / 10
    # P(X<=1)=1,1 % < 2,5 % <= P(X<=2)=5,5 %  ->  can duoi 0,2;  P(X<=7)=94,5 % < 97,5 % <= P(X<=8)=98,9 %  ->  can tren 0,8 (90 % se ra 0,7)
    rb = TT.bootstrap_phan_tang({"A": [(1.0, 0.0)] * 5 + [(0.0, 0.0)] * 5}, so_lan=4000, hat=7)
    assert rb["hieu_trung_binh"] == pytest.approx(0.5) and rb["ci95_duoi"] == pytest.approx(0.2) and rb["ci95_tren"] == pytest.approx(0.8)
    # b trung vi = 0 -> ty so None, khong chia cho 0
    r0 = TT.bootstrap_phan_tang({"A": [(0.1, 0.0), (0.2, 0.0)]}, so_lan=50)
    assert r0["ty_so_trung_vi"] is None


def test_tong_hop_phan_tap_chinh_z0_va_nhieu_rieng_ra_va_bo_loai_la():
    kq, _ = _tap_ket_qua()
    ra = TT.tong_hop_giai_doan_2(kq, so_lan_bootstrap=300)
    assert ra["so_kich_ban"] == {"chinh": 3, "z0": 1, "nhieu": 1}                       # K2 phang + K2 geo + C2 phang; Z0; N0
    assert ra["theo_quy_trinh"]["SMART_4"]["n"] == 12 and ra["z0"]["SMART_4"]["n"] == 4  # Z0 KHONG lot vao tap chinh
    assert ra["z0"]["SMART_4"]["trung_vi"] == 0.0 and ra["z0"]["RANDT_4"]["trung_vi"] == 0.5
    assert ra["nhieu"]["SMART_4"]["n"] == 0 and ra["nhieu"]["SMART_4"]["so_hang"] == 4  # nhieu: khong co hoi tiec (khong dap an), van dem gate
    assert set(ra["nhieu_theo_the_gioi"]) == {"N0|phang"}
    json.dumps(T._json_an_toan(ra))                                                     # xuat duoc ra JSON


def test_tong_hop_thong_ke_theo_quy_trinh_khop_tinh_tay():
    kq, d = _tap_ket_qua()
    tr = TT.tong_hop_giai_doan_2(kq, so_lan_bootstrap=200)["theo_quy_trinh"]
    smart = d["smart_a"] + d["smart_b"] + d["gia_c"]
    s = tr["SMART_4"]
    assert s["so_hang"] == 12 and s["khong_ap_duoc"] == 0 and s["n"] == 12
    assert s["trung_vi"] == pytest.approx(float(np.median(smart))) == pytest.approx(0.15)
    assert s["trung_binh"] == pytest.approx(float(np.mean(smart)))
    assert s["ty_le_tot"] == pytest.approx(float(np.mean([x <= 0.15 for x in smart])))
    assert s["ty_le_duoi_phan_giai"] == pytest.approx(1 / 12)                          # chi hat 0 cua K2|geo bi danh dau
    assert s["so_phep_thu_trung_vi"] == pytest.approx(100.0) and s["so_kiem_trung_vi"] == 4.0
    # gate: 12 hat deu dat kham pha; xac nhan hong 1 hat (K2|phang hat 3)
    assert (s["dat_kham_pha"], s["dat_xac_nhan"], s["so_mau_gate"]) == (12, 11, 12)
    assert s["ty_le_dat_xac_nhan"] == pytest.approx(11 / 12)
    assert s["can_tren_dat_xac_nhan"] == pytest.approx(TT.can_tren_clopper_pearson(11, 12))
    assert s["can_tren_dat_kham_pha"] == 1.0                                            # 12/12 -> can tren la 1
    r = tr["RANDT_4"]
    assert (r["dat_kham_pha"], r["dat_xac_nhan"]) == (3 + 4 + 4, 0 + 4 + 4)
    t0 = tr["T0"]                                                                       # T0 chi co o K2|phang: 4 hang / 4 mau
    assert t0["so_hang"] == 4 and t0["trung_vi"] == pytest.approx(0.4)


def test_tong_hop_hang_khong_ap_duoc_dem_nhung_khong_vao_thong_ke():
    hats = [{"T0": _qt(0.3)}, {"T0": {"ap_duoc": False}}, {"T0": _qt(0.5)}]
    ra = TT.tong_hop_giai_doan_2([_kb("K2", "L1", "phang", hats)], so_lan_bootstrap=50)["theo_quy_trinh"]["T0"]
    assert ra["so_hang"] == 3 and ra["khong_ap_duoc"] == 1 and ra["n"] == 2 and ra["trung_vi"] == pytest.approx(0.4)
    assert ra["so_mau_gate"] == 2                                                       # gate cung chi tinh hang ap duoc
    tat_ca_khong = TT.tong_hop_giai_doan_2([_kb("K2", "L1", "phang", [{"T0": {"ap_duoc": False}}])], so_lan_bootstrap=50)["theo_quy_trinh"]["T0"]
    assert tat_ca_khong["n"] == 0 and tat_ca_khong["khong_ap_duoc"] == 1 and "so_mau_gate" not in tat_ca_khong
    assert tat_ca_khong["ty_le_duoi_phan_giai"] is None


def test_tong_hop_theo_loai_va_rho_xep_hang():
    kq, d = _tap_ket_qua()
    ra = TT.tong_hop_giai_doan_2(kq, so_lan_bootstrap=100)
    assert set(ra["theo_loai"]) == {"L1", "L2"}                                          # khong co L3 / L4 -> khong co khoa; Z0, N0 khong tinh
    assert ra["theo_loai"]["L1"]["SMART_4"] == pytest.approx(float(np.median(d["smart_a"] + d["smart_b"])))
    assert ra["theo_loai"]["L2"]["SMART_4"] == pytest.approx(float(np.median(d["gia_c"])))
    # bang rho: trung vi theo hat cua tung the gioi; chi loai L5 (nhieu) bi bo; Z0 co mat (loai L0); the gioi khong co rho -> None, khong sap
    assert ra["rho_xep_hang"] == {"K2|phang": pytest.approx(0.75), "K2|geo": pytest.approx(0.5), "C2|phang": pytest.approx(0.5),
                                  "Z0|phang": pytest.approx(1.0), "X9|phang": None}
    assert ra["rho_trung_vi"] == pytest.approx(float(np.median([0.75, 0.5, 0.5, 1.0])))   # None bi bo khi lay trung vi


def test_tong_hop_so_sanh_cap_doi_thong_minh_voi_ngau_nhien_cung_ngan_sach():
    kq, d = _tap_ket_qua()
    ra = TT.tong_hop_giai_doan_2(kq, so_lan_bootstrap=300)
    cap = {(c["k"], c["a"], c["b"]): c for c in ra["so_sanh_cap_doi"]}
    assert (4, "SMART", "RANDT") in cap and (4, "SMART", "T0") in cap
    assert (4, "SMART", "B0") not in cap and (4, "SMART_S", "RANDT_S") not in cap       # khong co du lieu -> khong co dong rong
    c = cap[(4, "SMART", "RANDT")]
    assert c["ngan_sach"] == "day_du" and c["n_tang"] == 3 and c["n_cap"] == 12
    hieu_a = np.mean(np.array(d["smart_a"]) - np.array(d["randt_a"]))                   # -0,225
    hieu_b = np.mean(np.array(d["smart_b"]) - np.array(d["randt_b"]))                   # -0,0375
    assert c["hieu_trung_binh"] == pytest.approx((hieu_a + hieu_b + 0.0) / 3)           # trong so ngang giua tang (tang C hieu 0)
    assert c["so_tang_a_tot_hon"] == 2
    ts, tr = np.median(d["smart_a"] + d["smart_b"] + d["gia_c"]), np.median(d["randt_a"] + d["randt_b"] + d["gia_c"])
    assert c["trung_vi_a"] == pytest.approx(ts) and c["trung_vi_b"] == pytest.approx(tr)
    assert c["ty_so_trung_vi"] == pytest.approx(ts / tr) and c["dat_nguong_08"] is True  # 0,15 / 0,225 = 0,667 <= 0,8
    assert c["thong_minh_thang"] == bool(c["ci95_tren"] < 0) and c["ci95_duoi"] <= c["hieu_trung_binh"] <= c["ci95_tren"]
    # voi chuan T0 chi tang K2|phang co mat
    t0 = cap[(4, "SMART", "T0")]
    assert t0["n_tang"] == 1 and t0["n_cap"] == 4 and t0["trung_vi_b"] == pytest.approx(0.4)


def test_tong_hop_thong_minh_thang_chi_khi_can_tren_ci_am():
    ro = [_kb("K2", "L1", "phang", [{"SMART_4": _qt(0.1), "RANDT_4": _qt(0.4)} for _ in range(6)])]            # luon tot hon ro rang
    c = TT.tong_hop_giai_doan_2(ro, so_lan_bootstrap=300)["so_sanh_cap_doi"][0]
    assert c["thong_minh_thang"] is True and c["dat_nguong_08"] is True
    hoa = [_kb("K2", "L1", "phang", [{"SMART_4": _qt(0.2 if i % 2 else 0.1), "RANDT_4": _qt(0.1 if i % 2 else 0.2)} for i in range(10)])]
    c = TT.tong_hop_giai_doan_2(hoa, so_lan_bootstrap=300)["so_sanh_cap_doi"][0]
    assert c["thong_minh_thang"] is False and c["ci95_duoi"] < 0 < c["ci95_tren"]
    bang = [_kb("K2", "L1", "phang", [{"SMART_4": _qt(0.2), "RANDT_4": _qt(0.2)} for _ in range(6)])]         # giong het: can tren CI dung bang 0
    c = TT.tong_hop_giai_doan_2(bang, so_lan_bootstrap=100)["so_sanh_cap_doi"][0]
    assert c["ci95_tren"] == 0.0 and c["thong_minh_thang"] is False and c["dat_nguong_08"] is False and c["ty_so_trung_vi"] == pytest.approx(1.0)
    for a, b, mong in ((0.5, 0.625, True), (0.5, 0.5625, False)):                                               # ti so 0,8 dung bien tinh; 0,889 khong tinh
        r = [_kb("K2", "L1", "phang", [{"SMART_4": _qt(a), "RANDT_4": _qt(b)} for _ in range(4)])]
        c = TT.tong_hop_giai_doan_2(r, so_lan_bootstrap=50)["so_sanh_cap_doi"][0]
        assert c["ty_so_trung_vi"] == pytest.approx(a / b) and c["dat_nguong_08"] is mong, (a, b)
    te = [_kb("K2", "L1", "phang", [{"SMART_4": _qt(0.3), "RANDT_4": _qt(0.2)} for _ in range(6)])]            # thong minh te hon
    c = TT.tong_hop_giai_doan_2(te, so_lan_bootstrap=300)["so_sanh_cap_doi"][0]
    assert c["thong_minh_thang"] is False and c["dat_nguong_08"] is False and c["so_tang_a_tot_hon"] == 0


def test_tong_hop_rong_khong_sap():
    ra = TT.tong_hop_giai_doan_2([], so_lan_bootstrap=10)
    assert ra["so_kich_ban"] == {"chinh": 0, "z0": 0, "nhieu": 0} and ra["so_sanh_cap_doi"] == [] and ra["rho_trung_vi"] is None
    assert ra["theo_quy_trinh"] == {} and ra["theo_loai"] == {}


# ================================================================================================ (5) ke hoach, tep, main
def test_ke_hoach_s2_la_dau_van_tay_on_dinh_va_nhay_voi_tung_tham_so():
    kh = TT.ke_hoach_s2("A_ref|w=0.5|tam=I6|san=0")
    assert set(kh) == {"plan_hash", "cau_hinh"} and len(kh["plan_hash"]) == 16 and int(kh["plan_hash"], 16) >= 0
    assert TT.ke_hoach_s2("A_ref|w=0.5|tam=I6|san=0") == kh                             # on dinh giua cac lan goi
    assert TT.ke_hoach_s2("A_ref|w=1|tam=I6|san=0")["plan_hash"] != kh["plan_hash"]     # ket qua giai doan 1 nam trong van tay
    ch = kh["cau_hinh"]
    assert ch["quy_trinh"] == list(TT.QUY_TRINH_TIM) and ch["chuan"] == list(TT.CAC_CHUAN) and ch["top_k"] == [1, 4, 12]
    assert ch["cap_so_sanh"][0][:2] == ["SMART", list(TT.CAP_SO_SANH[0][1])] and ch["cap_so_sanh"][1][2] == "nho"
    assert ch["ke_hoach_do_thong_minh"] == DM.ke_hoach(5)["plan_hash"] and ch["van_tay_gd1"] == T.ke_hoach_s1()["plan_hash"]
    assert [k["ten"] for k in ch["kich_ban_nhieu"]] == ["N0", "N0_re"] and all(k["loai"] == "L5" for k in ch["kich_ban_nhieu"])
    with pytest.raises(ValueError):
        TT.ke_hoach_s2("khong phai ten bien the")                                        # ten sai dang bi tu choi truoc khi ra van tay


def test_nguong_giai_doan_2_dong_bang():
    """Doi bat ky so nao duoi day = mot gia thuyet KHAC: phai tang `PHIEN_BAN_GD2`, khong sua im lang (luat pre-registration)."""
    n = TT.NGUONG_GD2
    assert TT.PHIEN_BAN_GD2 == n["phien_ban"] == 1
    assert n["thong_minh_so_voi_ngau_nhien"] == 0.8 and n["dat_gia_sau_xac_nhan"] == 0.05 and n["dat_gia_truoc_xac_nhan"] == 0.25
    assert (n["so_hat"], n["so_hat_nhieu"], n["so_nam_quan_sat"]) == (TT.SO_HAT_GD2, TT.SO_HAT_NHIEU, TT.SO_NAM_QUAN_SAT_GD2) == (12, 24, 2.0)
    assert n["top_k"] == [1, 4, 12] and TT.SO_LENH_TOI_THIEU == 20
    assert TT.SO_O_LUOI_CUC_BO == len(DM.HE_SO_BUOC) * len(DM.HE_SO_TP) * len(DM.HE_SO_TAM) == 45
    assert {q for q in TT.NGAN_SACH_DAY_DU} | {q for q in TT.NGAN_SACH_NHO} <= set(TT.QUY_TRINH_TIM)
    for a, bs, muc in TT.CAP_SO_SANH:                                                   # moi cap so sanh tham chieu quy trinh / chuan co that
        assert a in TT.QUY_TRINH_TIM and muc in ("day_du", "nho")
        assert all(b in TT.QUY_TRINH_TIM or b in TT.CAC_CHUAN for b in bs), (a, bs)


def test_the_gioi_nhieu_khong_co_hoi_quy_va_co_loai_l5():
    assert [k.ten for k in TT.BO_KICH_BAN_NHIEU] == ["N0", "N0_re"]
    assert all(k.loai == "L5" and not k.dich.hoi_quy and k.dich.chi_phi_pip <= k.nguon.chi_phi_pip for k in TT.BO_KICH_BAN_NHIEU)
    assert TT.BO_KICH_BAN_NHIEU[1].dich.chi_phi_pip == 3.0


def test_doc_giai_doan_2_doc_dung_tep_p2_theo_thu_tu_ten(tmp_path):
    for ten, ghi in (("p2_b_phang.json", {"v": 2}), ("p2_a_phang.json", {"v": 1}), ("ke_hoach_s2.json", {"v": 9}), ("p2_c.txt", "x"),
                     ("dapan_goc_phang.json", {"v": 8})):
        (tmp_path / ten).write_text(json.dumps(ghi), encoding="utf-8")
    assert TT.doc_giai_doan_2(str(tmp_path)) == [{"v": 1}, {"v": 2}]
    vang = tmp_path / "trong"
    vang.mkdir()
    assert TT.doc_giai_doan_2(str(vang)) == []


def test_doc_dap_an_doc_lai_dung_dap_an_giai_doan_1_ke_ca_o_thieu(tmp_path):
    be = np.full((len(T.BUOC), len(T.TY_LE_TP), len(T.TANG)), np.nan)
    be[3, 2, 1], be[4, 2, 1] = 12.5, -7.25
    da = T.DapAn(tg=T.GOC.doi(sigma_pip=60.0), kieu=T.KIEU["geo"], san_pip=11.5, be_mat=be, tot_nhat=T.KIEU["geo"].tham_so(40.0, 56.0, 8),
                 diem_cao_nguyen=9.5, diem_b=float("nan"), a_nen_pip=33.3)
    f = tmp_path / "dapan_x_geo.json"
    T.ghi_json(str(f), T.dap_an_ra_dict(da))                                             # NaN -> null trong tep
    d2 = TT.doc_dap_an(str(f))
    assert d2.tg == da.tg and d2.kieu == da.kieu and d2.tot_nhat == da.tot_nhat
    assert d2.san_pip == 11.5 and d2.diem_cao_nguyen == 9.5 and d2.a_nen_pip == 33.3 and math.isnan(d2.diem_b)
    assert np.array_equal(d2.be_mat, be, equal_nan=True) and d2.be_mat.shape == be.shape


def test_main_tong_hop_in_json_ascii_hoac_ghi_tep_va_tu_choi_lenh_la(tmp_path, capsys):
    kq, _ = _tap_ket_qua()
    for r in kq[:5]:
        (tmp_path / ("p2_%s_%s.json" % (r["kich_ban"], r["kieu"]))).write_text(json.dumps(r), encoding="utf-8")
    (tmp_path / "ke_hoach_s2.json").write_text("{}", encoding="utf-8")
    assert TT.main(["tong-hop", "--ra", str(tmp_path)]) == 0
    ra = capsys.readouterr().out
    assert ra.isascii()
    tong = json.loads(ra)
    assert tong["so_kich_ban"] == {"chinh": 3, "z0": 1, "nhieu": 1} and tong["theo_quy_trinh"]["SMART_4"]["n"] == 12
    out = tmp_path / "ket_qua" / "tong.json"
    assert TT.main(["tong-hop", "--ra", str(tmp_path), "--ghi", str(out)]) == 0
    assert capsys.readouterr().out == ""                                                 # ghi tep thi khong in
    ghi = json.loads(out.read_text(encoding="utf-8"))
    assert ghi["so_kich_ban"] == tong["so_kich_ban"] and ghi["so_sanh_cap_doi"] == tong["so_sanh_cap_doi"]
    with pytest.raises(SystemExit):
        TT.main([])                                                                      # thieu lenh con
    with pytest.raises(SystemExit):
        TT.main(["tong-hop"])                                                            # thieu --ra


# ================================================================================================ (6) duong chay day du nho
@pytest.mark.cham
def test_giai_doan_2_chay_het_duong_nho_roi_gop_duoc(tmp_path):
    """MOT hat, duong 0,3 nam, the gioi K2: toan bo duong sinh gia -> doc -> tim (engine C that) -> cong xac nhan -> JSON -> gop ket qua."""
    kb = T.kich_ban("K2")
    ts_nguon = KIEU.tham_so(60.0, 60.0, 8)
    be = np.full((len(T.BUOC), len(T.TY_LE_TP), len(T.TANG)), np.nan)
    da_n = T.DapAn(tg=kb.nguon, kieu=KIEU, san_pip=10.0, be_mat=be, tot_nhat=ts_nguon, diem_cao_nguyen=5.0, diem_b=5.0, a_nen_pip=40.0)
    da_d = T.DapAn(tg=kb.dich, kieu=KIEU, san_pip=20.0, be_mat=be.copy(), tot_nhat=KIEU.tham_so(120.0, 120.0, 8), diem_cao_nguyen=5.0,
                   diem_b=1000.0, a_nen_pip=80.0)                                       # dap an cao hon moi so engine: hoi tiec duong
    dong = []
    r = TT.giai_doan_2(kb, KIEU, da_n, da_d, "A_ref|w=0.5|tam=I6|san=0", so_hat=1, so_nam_qs=0.3, so_duong_b=1, so_nam_b=0.3, luong=2,
                       log=dong.append)
    assert (r["kich_ban"], r["loai"], r["kieu"], r["so_hat"]) == ("K2", "L1", "phang", 1) and len(r["hat_ket_qua"]) == 1 and len(dong) == 1
    h = r["hat_ket_qua"][0]
    assert len(h["quy_trinh"]) == 30 and all(e["ap_duoc"] for e in h["quy_trinh"].values())
    assert h["ly_do_dich"] == [] and h["so_cach_dich"] >= 1 and h["tham_so_t0"] is not None
    ns = h["ngan_sach"]
    assert 0 < ns["SMART_S"] <= ns["SMART"] and ns["FULL_RAW"] == h["so_o_luoi_dap_an"] > 0
    assert ns["RANDT"] == ns["RAND"] == ns["SMART"]
    for ten, e in h["quy_trinh"].items():
        assert e["hoi_tiec"] is not None and math.isfinite(e["hoi_tiec"]) and e["hoi_tiec"] < 1.0, ten      # dap an 1000 > moi diem engine
        assert math.isfinite(e["diem_b"]) and e["buoc"] > 0 and e["tp"] > 0 and e["tang"] >= 2, ten
    # san phan giai suy tu duong quan sat (bien variant san=0 -> chi con san phan giai cua nen); moi o duoc chon bang quy trinh TIM khong duoi san
    assert h["san_pip"] == pytest.approx(DT.NGUONG_PHAN_GIAI * h["a_nen_pip"]) and h["a_nen_pip"] > 0
    for q in TT.QUY_TRINH_TIM:
        for k in TT.TOP_K_THU:
            e = h["quy_trinh"]["%s_%d" % (q, k)]
            assert e["duoi_phan_giai"] is False and min(e["buoc"], e["tp"]) >= h["san_pip"] - 1e-6, (q, k)
    assert h["ung_vien_dau"] and all(len(u) == 3 and u[0] > 0 and u[1] > 0 and u[2] >= 2 for u in h["ung_vien_dau"])
    # hop dong voi ben gop: tep ghi ra doc lai duoc va `tong_hop_giai_doan_2` tieu thu duoc
    T.ghi_json(str(tmp_path / "p2_K2_phang.json"), r)
    doc = TT.doc_giai_doan_2(str(tmp_path))
    assert len(doc) == 1
    tong = TT.tong_hop_giai_doan_2(doc, so_lan_bootstrap=50)
    assert tong["so_kich_ban"] == {"chinh": 1, "z0": 0, "nhieu": 0}
    assert tong["theo_quy_trinh"]["SMART_4"]["so_hang"] == 1 and tong["theo_quy_trinh"]["SMART_4"]["n"] == 1
    assert tong["theo_quy_trinh"]["FULL_RAW_1"]["trung_vi"] == pytest.approx(h["quy_trinh"]["FULL_RAW_1"]["hoi_tiec"])
    assert any(c["a"] == "SMART" and c["b"] == "RANDT" and c["k"] == 4 for c in tong["so_sanh_cap_doi"])
