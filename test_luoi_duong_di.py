# -*- coding: utf-8 -*-
"""Mo hinh bar `duong_di` (`ThamSo.khop_bar == "duong_di"`, MAC DINH tu 08/10/2026) - NGU NGHIA, khong phai khop Python <-> C.

Vi sao file nay: `test_luoi_nhan.py` chung minh nhan C khop Python TUNG BIT; `test_ea_luoi_day_du.py` chung minh engine khop CHINH ma EA
(~2%, thong ke). Hai cai deu KHONG bat duoc mot hieu nham ma ca Python lan C cung mac (vd thu tu tie, gia khop khi nhay gia, cap tia
tinh theo bar hay theo doan). Day la ba hang rao con thieu:

  1. TAY TINH: moi kich ban nho co dap an tinh bang tay TRUOC khi chay (don vi pip, 1 lot = 10 tien / pip), chay ca Python va nhan C.
     Kich ban nao cung phan biet DUOC hai cach hieu (ghi trong docstring tung ca).
  2. TINH CHAT: tach moi nen thanh ba nen DOAN theo chinh duong cua no phai ra y het (nhat quan do phan giai); guong `chieu=-1` ===
     `chieu=+1` tren gia dao dau; nhan doi lot ra dung gap doi.
  3. THONG KE: tren random walk khong chi phi, khong drift (ky vong that = 0), `duong_di` khong lech so voi chay tung tick trong khi
     `cuc_tri` lech them +58 / +184 (`nhan/kiem_do_phan_giai.py`) - kem kiem LUC cua phep thu (bo lech cu phai bi bat).
"""
from __future__ import annotations

import dataclasses
import io

import numpy as np
import pytest

from nhan import kiem_do_phan_giai as KD
from nhan import luoi as LU
from nhan import luoi_nhan as LN
from test_luoi_nhan import _kich_ban


# ------------------------------------------------------------------ TIEN ICH
@pytest.fixture(scope="module")
def nhan():
    if LN.che_do() == "py":
        pytest.skip("LUOI_NHAN=py")
    lib = LN.lay_nhan()
    if lib is None:
        pytest.skip("khong co nhan C: %s" % LN.trang_thai()["ly_do"])
    return lib


@pytest.fixture(params=["py", "c"])
def may(request):
    """'py' = ban Python chuan (`mot_ro_chuan`); 'c' = nhan C (bo qua khi may khong co trinh bien dich)."""
    if request.param == "c":
        request.getfixturevalue("nhan")
    return request.param


#: Quy cach tong hop: 1 pip = 1e-4, 1 lot = 100.000 don vi -> 1 lot * 1 pip = 10 tien. Khong phi qua dem, khong spread mac dinh.
QC = LU.QuyCach(ma="SYN", pip=1e-4, hop_dong=100_000.0, point=1e-5, phi_nam_mua=0.0, phi_nam_ban=0.0, spread_du_phong=0.0,
                von_quy_doi=1.0, do_tin="SAN")
GOC = 1.45
PT = 10.0                                                      # tien / pip / lot cua QC
#: Quy cach NHI PHAN (pip = 0,25; gia goc 100): moi gia / nguong / trung binh deu la so nhi phan chinh xac -> bat dang thuc o muc bit,
#: dung cho cac ca "bang nhau" (tie) ma double thuong khong giu duoc (vd 1,449 - 0,001 != 1,448).
QC_NP = LU.QuyCach(ma="DYA", pip=0.25, hop_dong=1000.0, point=0.01, phi_nam_mua=0.0, phi_nam_ban=0.0, spread_du_phong=0.0,
                   von_quy_doi=1.0, do_tin="SAN")
GOC_NP = 100.0
PT_NP = 250.0                                                  # 1000 * 0,25

BASE = dict(buoc=10.0, tp=5.0, tran_tang=4, lot=1.0)


def ts_(**kw):
    return LU.ThamSo(**{**BASE, **kw})                         # khop_bar mac dinh = duong_di


def nen(*bars, qc=QC, goc=GOC):
    """bars[0] = (gia bat dau,) tinh bang pip; bars[i] = (hi, lo, cl) tinh bang pip so voi gia goc. Tra (hi, lo, cl) la gia."""
    p = qc.pip
    g0 = goc + bars[0][0] * p
    hi, lo, cl = [g0], [g0], [g0]
    for h, l, c in bars[1:]:
        hi.append(goc + h * p)
        lo.append(goc + l * p)
        cl.append(goc + c * p)
    return np.array(hi), np.array(lo), np.array(cl)


def chay(may, bars, ts, *, chieu=1, sp_pip=0.0, dem=None, qc=QC, goc=GOC):
    hi, lo, cl = nen(*bars, qc=qc, goc=goc)
    n = len(cl)
    sp = np.full(n, sp_pip * qc.pip)
    dm = np.zeros(n) if dem is None else np.asarray(dem, float)
    ev: list = []
    if may == "py":
        lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dm, chieu, ts, qc, ev)
    else:
        r = LN.mot_ro(hi, lo, cl, sp, dm, chieu, ts, qc, ev)
        assert r is not None, "nhan C tra None cho %s" % (ts,)
        lai, treo, tk = r
    return np.asarray(lai), np.asarray(treo), tk, ev


def nhat_ky(ev, qc=QC, goc=GOC):
    """Nhat ky lenh -> tuple de so sanh voi dap an tay: gia doi ra PIP so voi goc."""
    ra = []
    for e in ev:
        if e[0] == "mo":
            _t, bar, gia, lot, ma_id, tang, ro = e
            ra.append(("mo", bar, (gia - goc) / qc.pip, lot, ma_id, tang, ro))
        else:
            _t, bar, gia, ma_id, ly_do = e
            ra.append(("dong", bar, (gia - goc) / qc.pip, ma_id, ly_do))
    return ra


def kiem_nhat_ky(ev, mong, qc=QC, goc=GOC):
    got = nhat_ky(ev, qc, goc)
    assert len(got) == len(mong), "so su kien %d != %d:\n got  %s\n mong %s" % (len(got), len(mong), got, mong)
    for i, (g, m) in enumerate(zip(got, mong)):
        assert g[0] == m[0], (i, g, m)
        for a, b in zip(g[1:], m[1:]):
            if isinstance(b, str):
                assert a == b, (i, g, m)
            else:
                assert a == pytest.approx(b, abs=1e-6), (i, g, m)


def kiem_tk(tk, **mong):
    for k, v in mong.items():
        assert tk[k] == pytest.approx(v, abs=1e-6), (k, tk[k], v, tk)


# ------------------------------------------------------------------ 1. TAY TINH
def test_a_cham_dung_nguong_tp_la_chot_va_mo_lai_o_gia_chot(may):
    """Nen xanh 0 -> 5: TP o +5 pip, nen cao nhat DUNG +5 -> chot (cham dung = khop, nhu `bid <= muc` cua EA). Lai = 5 pip = 50.
    Ro chot xong mo lai L1 NGAY o gia chot (+5). Spread 2 pip tru MOT lan moi lenh (2 lenh = 40), khong tru them luc chot."""
    lai, treo, tk, ev = chay(may, [(0,), (5, 0, 5)], ts_(), sp_pip=2.0)
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("dong", 1, 5, 0, "tp"), ("mo", 1, 5, 1.0, 1, 0, 1)])
    kiem_tk(tk, lai_gop=50, so_ro=1, so_lenh=2, so_cap=0, tang_max=1, con_mo=1, phi_spread=40)
    assert lai == pytest.approx([-20, 10]) and treo == pytest.approx([0, 0])


def test_b_thieu_mot_phan_muoi_pip_thi_khong_chot(may):
    """Cao nhat 4,9 pip < nguong 5 pip (thieu 0,1 pip >> dung sai 1e-6 pip) -> KHONG chot."""
    lai, treo, tk, ev = chay(may, [(0,), (4.9, 0, 4.9)], ts_())
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0)])
    kiem_tk(tk, lai_gop=0, so_ro=0, so_lenh=1, con_mo=1)


def test_c_nhay_gia_xuong_khop_o_gia_mo_va_nguong_ke_tiep_tinh_tu_gia_khop(may):
    """Nen thu 1 mo cua nhay xuong -12 (dong bar truoc o 0, nen nam trong [-30, -12] -> open kep = -12), roi xuong -30.
    Tang 1: nguong -10 da bi vuot luc mo -> khop o GIA MO -12 (khong o -10). Nguong ke tiep tinh tu GIA KHOP: -12 - 10 = -22 (khong phai
    -20 = -10 - 10) -> tang 2 khop o -22; nguong ke -32 < low -30 -> dung. Tong 3 lenh; neu tinh tu nguong se co 4 (-20, -30 cham dung).
    Lo treo lon nhat tren duong = o low -30: (30 + 18 + 8) pip = 560. Spread 2 pip x 3 lenh = 60 (bar 0 da tru 20)."""
    lai, treo, tk, ev = chay(may, [(0,), (-12, -30, -25)], ts_(), sp_pip=2.0)
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, -12, 1.0, 1, 1, 0), ("mo", 1, -22, 1.0, 2, 2, 0)])
    kiem_tk(tk, lai_gop=0, so_lenh=3, tang_max=3, con_mo=3, phi_spread=60)
    assert lai == pytest.approx([-20, -60]) and treo == pytest.approx([0, 560])


def test_c2_nhay_gia_vuot_hon_mot_buoc_chi_mo_mot_tang_o_gia_mo(may):
    """Nen thu 1 mo cua nhay xuong -25 (qua nguong -10 toi 15 pip, hon mot buoc 10 pip), roi xuong low -30. Chi MOT tang khop o gia mo -25;
    nguong ke tiep tinh tu GIA KHOP: -25 - 10 = -35 < low -30 -> khong them tang. (Neu nguong ke tiep tinh tu nguong cu: -10 - 10 = -20
    se mo them tang thu 3 CUNG gia -25 - mot lenh ma EA khong bao gio dat vi khong co lan nao bid <= tang truoc - buoc.) Lo treo o low -30:
    30 + 5 = 35 pip = 350 (cao hon o open: 25 pip = 250 va o dong -28: 31 pip)."""
    lai, treo, tk, ev = chay(may, [(0,), (-25, -30, -28)], ts_())
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, -25, 1.0, 1, 1, 0)])
    kiem_tk(tk, lai_gop=0, so_lenh=2, tang_max=2, con_mo=2)
    assert lai == pytest.approx([0, 0]) and treo == pytest.approx([0, 350])


def test_c3_nen_khong_bien_do_sau_nhay_gia_xuong_van_mo_tang(may):
    """Nen CHI MOT GIA (hi = lo = dong) sau cu nhay gia: khong co doan nao de di, nen tang thuoc nguong da bi vuot chi mo duoc o buoc
    "nhay gia luc mo nen" (neu bo buoc do thi lenh khong bao gio duoc mo).
    (a) Nen 1 = -25 ca bo: tang 1 khop o -25, khong them (nguong ke -35). Lo treo = 25 pip (tang dau) = 250.
    (b) Ro vua chot o +5 va dang CHO lui toi +1 (`cho_lui=4`); nen 2 chi mot gia -3 -> L1 moi khop o -3 (gia mo, vi +1 da bi vuot)."""
    lai, treo, tk, ev = chay(may, [(0,), (-25, -25, -25)], ts_())
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, -25, 1.0, 1, 1, 0)])
    kiem_tk(tk, lai_gop=0, so_lenh=2, tang_max=2, con_mo=2)
    assert lai == pytest.approx([0, 0]) and treo == pytest.approx([0, 250])
    lai, treo, tk, ev = chay(may, [(0,), (10, 0, 8), (-3, -3, -3)], ts_(cho_lui=4.0))
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("dong", 1, 5, 0, "tp"), ("mo", 2, -3, 1.0, 1, 0, 1)])
    kiem_tk(tk, lai_gop=50, so_ro=1, so_lenh=2, con_mo=1)


def test_d_nen_doji_di_theo_nen_xanh_xuong_low_truoc(may):
    """Dong = open (doji) tinh la XANH: O -> L -> H -> C. Nen: open 0, low -18, high +20, dong 0.
    Xuong -18: tang 1 o -10 (nguong ke -20 chua toi). Len: TP cua ro 2 tang (tb -5, TP 0) o 0: lai (0-0)+(0+10) = 10 pip = 100; mo lai
    L1 o 0, roi chot tiep o +5, +10, +15, +20 (cham dung high), moi lan 5 pip = 50 -> TONG 300, 5 ro chot. Xuong ve 0 theo duong H -> C:
    tang o +10, o 0 (cham dung) -> con 3 lenh. Neu hieu doji la DO (O -> H -> L -> C) chi chot 4 ro (200). Lo treo = 300 (cuoi duong)."""
    lai, treo, tk, ev = chay(may, [(0,), (20, -18, 0)], ts_())
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, -10, 1.0, 1, 1, 0),
                      ("dong", 1, 0, 0, "tp"), ("dong", 1, 0, 1, "tp"), ("mo", 1, 0, 1.0, 2, 0, 1),
                      ("dong", 1, 5, 2, "tp"), ("mo", 1, 5, 1.0, 3, 0, 2),
                      ("dong", 1, 10, 3, "tp"), ("mo", 1, 10, 1.0, 4, 0, 3),
                      ("dong", 1, 15, 4, "tp"), ("mo", 1, 15, 1.0, 5, 0, 4),
                      ("dong", 1, 20, 5, "tp"), ("mo", 1, 20, 1.0, 6, 0, 5),
                      ("mo", 1, 10, 1.0, 7, 1, 5), ("mo", 1, 0, 1.0, 8, 2, 5)])
    kiem_tk(tk, lai_gop=300, so_ro=5, so_lenh=9, tang_max=3, con_mo=3)
    assert lai == pytest.approx([0, 300]) and treo[1] == pytest.approx(300)


def test_e1_cho_lui_khop_dung_muc_cho_khong_phai_low(may):
    """`cho_lui=4`: chot o +5 xong KHONG mo lai ngay ma cho gia lui toi +1 (= 5 - 4). Nen 2 (open 8 kep trong [-4, 9]) xuong -4 -> L1
    khop o +1 (muc cho), khong o low -4. Ro moi = ro 1. Lo treo nen 2: (1 - (-4)) = 5 pip = 50; nen 1 khong co lenh mo luc het bar."""
    lai, treo, tk, ev = chay(may, [(0,), (10, 0, 8), (9, -4, -2)], ts_(cho_lui=4.0))
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("dong", 1, 5, 0, "tp"), ("mo", 2, 1, 1.0, 1, 0, 1)])
    kiem_tk(tk, lai_gop=50, so_ro=1, so_lenh=2, con_mo=1)
    assert lai == pytest.approx([0, 50, 50]) and treo == pytest.approx([0, 0, 50])


def test_e2_cho_lui_nhay_gia_vuot_muc_cho_khop_o_gia_mo(may):
    """Nhu e1 nhung nen 2 nhay xuong [-8, -3] (muc cho +1 da bi vuot luc mo) -> L1 khop o GIA MO -3, khong o muc +1."""
    lai, treo, tk, ev = chay(may, [(0,), (10, 0, 8), (-3, -8, -6)], ts_(cho_lui=4.0))
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("dong", 1, 5, 0, "tp"), ("mo", 2, -3, 1.0, 1, 0, 1)])
    kiem_tk(tk, lai_gop=50, so_lenh=2, con_mo=1)
    assert treo[2] == pytest.approx(50)                        # low -8: (-3) - (-8) = 5 pip


def test_f_nhay_gia_len_chot_o_gia_mo_khong_o_nguong(may):
    """Nen 1 nhay LEN [12, 20] (dong bar truoc o 0 -> open kep = 12): TP cu (+5) da bi vuot luc mo -> chot o GIA MO 12 (lai 12 pip =
    120), khong o 5 (50). Mo lai o 12, chot tiep o 17 (+50), mo lai o 17."""
    lai, treo, tk, ev = chay(may, [(0,), (20, 12, 15)], ts_())
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("dong", 1, 12, 0, "tp"), ("mo", 1, 12, 1.0, 1, 0, 1),
                      ("dong", 1, 17, 1, "tp"), ("mo", 1, 17, 1.0, 2, 0, 2)])
    kiem_tk(tk, lai_gop=170, so_ro=2, con_mo=1)


@pytest.mark.parametrize("bien_cap,lai_mong,ket", [
    (3.0, 2500.0, [("tia", "tia", "tp")]),                      # tia nguong 98,75 < TP 99 -> tia truoc
    (4.0, 3000.0, [("tia", "tia", "tp")]),                      # BANG NHAU (99 = 99): tia truoc TP
    (5.0, 3000.0, [("tp", "tp", "tp")]),                        # tia nguong 99,25 > TP 99 -> TP chot ca ro
])
def test_g_tia_truoc_tp_khi_nguong_tia_nho_hon_hoac_bang(may, bien_cap, lai_mong, ket):
    """Quy cach nhi phan (gia chinh xac). 3 tang o 100 / 98 / 96 (lot 1, buoc 8 pip = 2,0); nen sau len 96 -> 99. TB 98 -> TP = 98 + 4 pip
    = 99. Tia cap (tang dau 100 + tang cuoi 96, TB 98) nguong = 98 + bien_cap pip. Bang nhau -> tia TRUOC TP (so_cap = 1, khong phai
    so_ro). Tien (1 pip = 250): bien_cap 3: tia o 98,75 = 1500, roi tang giua chot o 99 = 1000 -> 2500; bien_cap 4: tia o 99 = 2000 +
    1000; bien_cap 5: TP chot ca 3 tang o 99: -1 + 1 + 3 = 3 -> 3000."""
    ts = ts_(buoc=8.0, tp=4.0, tia_lenh=True, bien_cap=bien_cap)
    lai, treo, tk, ev = chay(may, [(0,), (0, -16, -16), (-4, -16, -4)], ts, qc=QC_NP, goc=GOC_NP)
    gia_chot = (99.0 - 100.0) / 0.25                           # -4 pip
    gia_tia = ((98.0 + 0.25 * bien_cap) - 100.0) / 0.25
    if ket[0][0] == "tia":
        mong_cuoi = [("dong", 2, gia_tia, 0, "tia"), ("dong", 2, gia_tia, 2, "tia"), ("dong", 2, gia_chot, 1, "tp"),
                     ("mo", 2, gia_chot, 1.0, 3, 0, 1)]
        so_cap, so_ro = 1, 1
    else:
        mong_cuoi = [("dong", 2, gia_chot, 0, "tp"), ("dong", 2, gia_chot, 1, "tp"), ("dong", 2, gia_chot, 2, "tp"),
                     ("mo", 2, gia_chot, 1.0, 3, 0, 1)]
        so_cap, so_ro = 0, 1
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, -8, 1.0, 1, 1, 0), ("mo", 1, -16, 1.0, 2, 2, 0)] + mong_cuoi,
                 qc=QC_NP, goc=GOC_NP)
    kiem_tk(tk, lai_gop=lai_mong, so_cap=so_cap, so_ro=so_ro, con_mo=1, tang_max=3)


def test_h_tia_lam_rong_ro_thi_mo_lai_ngay_du_co_cho_lui(may):
    """Ro 2 tang (0, -10), bien_cap 2, `cho_lui=4`: tia nguong -5 + 2 = -3 < TP 0 -> tia chot CA HAI o -3 (+4 pip = 40), ro RONG nen mo lai
    NGAY o -3 (khong cho lui nhu sau TP). Vi vay con 1 lenh, ro 1."""
    ts = ts_(tia_lenh=True, bien_cap=2.0, cho_lui=4.0)
    lai, treo, tk, ev = chay(may, [(0,), (0, -10, -10), (-3, -10, -3)], ts)
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, -10, 1.0, 1, 1, 0), ("dong", 2, -3, 0, "tia"), ("dong", 2, -3, 1, "tia"),
                      ("mo", 2, -3, 1.0, 2, 0, 1)])
    kiem_tk(tk, lai_gop=40, so_cap=1, so_ro=0, con_mo=1)


@pytest.mark.parametrize("cap,lai_pip,so_cap,so_ro,con_mo", [(1, 29, 1, 4, 1), (999, 23, 2, 3, 1)])
def test_i_cap_moi_bar_khong_lam_tia_trong_mot_nen(may, cap, lai_pip, so_cap, so_ro, con_mo):
    """4 tang (0, -10, -20, -30), bien_cap 2, TP 5. Nen len -30 -> +5: tia (tang dau + cuoi, TB -15, nguong -13): +4 pip. Con 2 tang giua
    (-10, -20): neu cho tia tiep (cap 999) tia lai o -13 (+4), mo lai L1 o -13 roi chot o -8, -3, +2 (+15) -> 23 pip, 2 tia, 3 ro. Neu
    chi 1 tia / bar (cap 1): 2 tang giua chot TP o -10 (+10), mo lai chot o -5, 0, +5 (+15) -> 29 pip, 1 tia, 4 ro."""
    ts = ts_(tia_lenh=True, bien_cap=2.0, cap_moi_bar=cap)
    lai, treo, tk, ev = chay(may, [(0,), (0, -30, -30), (5, -30, 5)], ts)
    kiem_tk(tk, lai_gop=lai_pip * PT, so_cap=so_cap, so_ro=so_ro, con_mo=con_mo, so_lenh=8)


@pytest.mark.parametrize("cap,lai_pip,so_cap,con_mo", [(1, 9, 1, 3), (2, 13, 2, 1)])
def test_j_cap_moi_bar_tinh_chung_cho_ca_ba_doan_cua_nen(may, cap, lai_pip, so_cap, con_mo):
    """Nen DO (open -12 -> high -5 -> low -25 -> dong -13) co HAI doan len. 3 tang (0, -10, -20), bien_cap 2. Doan len dau: tia o -8 (+4),
    tang giua chot TP o -5 (+5), mo lai L1 o -5. Xuong -25: them tang -15, -25. Doan len cuoi toi -13: tia thu hai (tang -5 + -25, TB -15,
    nguong -13) chi duoc neu cap >= 2: +4. Cap 1 = 1 tia moi NEN, khong phai moi doan: 9 pip, con 3 lenh; cap 2: 13 pip, con 1 lenh."""
    ts = ts_(tia_lenh=True, bien_cap=2.0, cap_moi_bar=cap)
    lai, treo, tk, ev = chay(may, [(0,), (0, -20, -12), (-5, -25, -13)], ts)
    kiem_tk(tk, lai_gop=lai_pip * PT, so_cap=so_cap, so_ro=1, con_mo=con_mo)


def test_k_chot_theo_tien_dung_tien_chu_khong_phai_pip(may):
    """`chot_tien=0.5` (0,01 lot) voi lot 1 -> nguong 50 tien; ro 2 tang (0, -10) tong 2 lot: TP = TB -5 + 50 / (100.000 x 2) = -5 + 2,5 pip
    = -2,5 pip (khong phai TB + tp = 0). Chot o -2,5: (-2,5 - 0) + (-2,5 + 10) = 5 pip = 50 tien = chinh nguong."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -10, -10), (-2, -10, -2)], ts_(chot_tien=0.5))
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, -10, 1.0, 1, 1, 0), ("dong", 2, -2.5, 0, "tp"), ("dong", 2, -2.5, 1, "tp"),
                      ("mo", 2, -2.5, 1.0, 2, 0, 1)])
    kiem_tk(tk, lai_gop=50, so_ro=1, con_mo=1)


def test_l_ro_ban_la_guong_cua_ro_mua(may):
    """`chieu=-1` tren nen guong cua kich ban c: open kep = +12, len +30. Tang 1 khop o gia mo +12 (nguong +10 da bi vuot), tang 2 o +22
    (tu gia khop), nguong +32 > high 30 -> dung. Lo treo = 560 (o high)."""
    lai, treo, tk, ev = chay(may, [(0,), (30, 12, 25)], ts_(), chieu=-1)
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, 12, 1.0, 1, 1, 0), ("mo", 1, 22, 1.0, 2, 2, 0)])
    kiem_tk(tk, lai_gop=0, so_lenh=3, tang_max=3, con_mo=3)
    assert treo[1] == pytest.approx(560)


def test_m_ro_ban_chot_o_gia_thap_hon(may):
    """Ro ban mo o 0, TP = 0 - 5 = -5. Nen xanh -10 -> 0: len -10 (cung chieu ban) chot o -5 (+5 pip = 50), mo lai ban o -5, chot tiep o -10
    (cham dung low)."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -10, 0)], ts_(), chieu=-1)
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("dong", 1, -5, 0, "tp"), ("mo", 1, -5, 1.0, 1, 0, 1),
                      ("dong", 1, -10, 1, "tp"), ("mo", 1, -10, 1.0, 2, 0, 2), ("mo", 1, 0, 1.0, 3, 1, 2)])
    kiem_tk(tk, lai_gop=100, so_ro=2)


def test_n_qua_dem_tinh_tren_lot_con_mo_luc_het_bar_theo_chieu(may):
    """Phi qua dem = tong lot con mo CUOI bar x hop dong x ty le nam x so dem / 365 x gia dong. Mua 3,65%/nam, 1 lot, 1 dem, gia dong
    +5 pip = 1,4505: 100.000 x 0,0365 / 365 x 1,4505 = 14,505. Ro ban dung `phi_nam_ban`. Bar ro RONG (cho lui) khong mat phi."""
    qc = dataclasses.replace(QC, phi_nam_mua=0.0365, phi_nam_ban=0.0073)
    lai, treo, tk, ev = chay(may, [(0,), (5, 0, 5)], ts_(), dem=[0, 1], qc=qc)
    kiem_tk(tk, phi_swap=14.505, lai_gop=50)
    assert lai[1] == pytest.approx(50 - 14.505)
    lai, treo, tk, ev = chay(may, [(0,), (0, -5, -5)], ts_(), chieu=-1, dem=[0, 3], qc=qc)
    assert tk["phi_swap"] == pytest.approx(100_000 * 0.0073 / 365 * 3 * (GOC - 5e-4))
    lai, treo, tk, ev = chay(may, [(0,), (10, 0, 8)], ts_(cho_lui=4.0), dem=[0, 1], qc=qc)
    assert tk["phi_swap"] == 0.0                              # ro chot xong dang cho lui: khong lenh nao con mo
    kiem_tk(tk, lai_gop=50)


@pytest.mark.parametrize("tran,treo_mong,tb", [(1, 500.0, 0.0), (3, 1200.0, -10.0), (5, 1500.0, -20.0)])
def test_p_tran_tang_dung_them_tang_roi_chot_ca_ro_o_tp(may, tran, treo_mong, tb):
    """Gia roi tu 0 xuong -50, buoc 10 pip: nguong -10, -20, -30, -40, -50 -> toi da `tran_tang` tang (lenh dau tinh la tang 1). Lo treo o
    low -50 (lot 1, 1 pip = 10): tran 1 -> 50 pip = 500; tran 3 (0, -10, -20) -> 50 + 40 + 30 = 120 pip = 1200; tran 5 (0 ... -40) ->
    50 + 40 + 30 + 20 + 10 = 150 pip = 1500 (khong mo -50 du cham dung low). Nen sau len dung TP = trung binh + 5 pip (tran 1: 0 -> +5;
    tran 3: -10 -> -5; tran 5: -20 -> -15): chot ca ro, lai = tong (TP - gia tang) pip; ro moi mo lai o gia chot."""
    ts = ts_(tran_tang=tran)
    lai, treo, tk, ev = chay(may, [(0,), (0, -50, -50)], ts)
    kiem_tk(tk, tang_max=tran, so_lenh=tran, con_mo=tran, lai_gop=0, so_ro=0)
    assert treo[1] == pytest.approx(treo_mong)
    lai, treo, tk, ev = chay(may, [(0,), (0, -50, -50), (tb + 5.0, -50, tb + 5.0)], ts)
    lai_pip = sum((tb + 5.0) + 10.0 * k for k in range(tran))                              # tang k (k = 0..) mo o -10k
    kiem_tk(tk, so_ro=1, lai_gop=lai_pip * PT, con_mo=1, so_lenh=tran + 1, tang_max=tran)


def test_q_tia_dung_trung_binh_co_trong_so_theo_lot(may):
    """Lot NHAN doi (1, 2, 4) o 0 / -10 / -20; tia cap = tang DAU (0, lot 1) + tang CUOI (-20, lot 4): trung binh CO TRONG SO
    (0x1 + -20x4) / 5 = -16, + bien_cap 2 = -14 (trung binh ngay thang -10 + 2 = -8 la SAI). Ca ro: TB = -100/7 = -14,29 -> TP -9,29.
    Tia (-14) < TP (-9,29) nen tia truoc: lai cap (-14 - 0) x 1 + (-14 + 20) x 4 = 10 pip-lot = 100. Con tang giua (-10, lot 2): TB -10,
    TP -5: chot o -5 (+5 x 2 = 10 pip-lot = 100), mo lai L1 lot 1 o -5, chot o 0 (cham dung high, +5 pip-lot = 50) = 250."""
    ts = ts_(kieu_lot="nhan", he_so_lot=2.0, tran_tang=4, tia_lenh=True, bien_cap=2.0)
    lai, treo, tk, ev = chay(may, [(0,), (0, -20, -20), (0, -20, 0)], ts)
    kiem_nhat_ky(ev, [("mo", 0, 0, 1.0, 0, 0, 0), ("mo", 1, -10, 2.0, 1, 1, 0), ("mo", 1, -20, 4.0, 2, 2, 0),
                      ("dong", 2, -14, 0, "tia"), ("dong", 2, -14, 2, "tia"),
                      ("dong", 2, -5, 1, "tp"), ("mo", 2, -5, 1.0, 3, 0, 1),
                      ("dong", 2, 0, 3, "tp"), ("mo", 2, 0, 1.0, 4, 0, 2)])
    kiem_tk(tk, lai_gop=250, so_cap=1, so_ro=2, tang_max=3, so_lenh=5, con_mo=1)
    assert treo[1] == pytest.approx(400.0)                    # o low -20: 20 x 1 + 10 x 2 + 0 x 4 = 40 pip-lot


def test_o_bar_dau_chi_tru_spread_lenh_dau_o_moi_do_dai(may):
    lai, treo, tk, ev = chay(may, [(0,)], ts_(), sp_pip=2.0)
    assert lai == pytest.approx([-20]) and treo == pytest.approx([0])
    kiem_tk(tk, so_lenh=1, phi_spread=20, con_mo=1)


# ------------------------------------------------------------------ 2. TINH CHAT
def tach_theo_duong(hi, lo, cl, sp):
    """Tach moi nen (i >= 1) thanh BA nen doan theo chinh duong `o -> x -> y -> cl` cua mo hinh (moi nen doan la mot nhat cat thang,
    nen mo = dong nen truoc nam trong nen). Nen 0 giu nguyen. Spread cua nen goc gan cho ca ba nen doan."""
    H, L_, C, S = [hi[0]], [lo[0]], [cl[0]], [sp[0]]
    for i in range(1, len(cl)):
        o = min(max(cl[i - 1], lo[i]), hi[i])
        x, y = (lo[i], hi[i]) if cl[i] >= o else (hi[i], lo[i])
        a = o
        for b in (x, y, cl[i]):
            H.append(max(a, b))
            L_.append(min(a, b))
            C.append(b)
            S.append(sp[i])
            a = b
    return np.array(H), np.array(L_), np.array(C), np.array(S)


def _chay_mang(may, hi, lo, cl, sp, dem, chieu, ts, qc):
    ev: list = []
    if may == "py":
        lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc, ev)
    else:
        r = LN.mot_ro(hi, lo, cl, sp, dem, chieu, ts, qc, ev)
        assert r is not None
        lai, treo, tk = r
    return np.asarray(lai), np.asarray(treo), tk, ev


def _bar_goc(j):
    return 0 if j == 0 else (j - 1) // 3 + 1


@pytest.mark.parametrize("seed", range(40))
def test_tach_moi_nen_thanh_ba_doan_theo_duong_di_ra_y_het(may, seed):
    """NHAT QUAN DO PHAN GIAI: chay tren nen goc va chay tren cac nen doan sinh ra tu CHINH duong di cua no phai cho lenh, lai, thong ke y
    het (cap_moi_bar = 999 va khong qua dem, vi hai thu do dem theo nen). Neu mo hinh xu ly ranh gioi nen khac ranh gioi doan (vd mat nhay gia
    luc mo, doi cho tia / cho lui giua hai doan) thi phep tach khong con bang nhau."""
    rng = np.random.default_rng(1000 + seed)
    hi, lo, cl, sp, dem, ts, qc = _kich_ban(rng)
    ts = dataclasses.replace(ts, cap_moi_bar=999)
    dem = np.zeros(len(cl))
    hi2, lo2, cl2, sp2 = tach_theo_duong(hi, lo, cl, sp)
    lai1, treo1, tk1, ev1 = _chay_mang(may, hi, lo, cl, sp, dem, 1, ts, qc)
    lai2, treo2, tk2, ev2 = _chay_mang(may, hi2, lo2, cl2, sp2, np.zeros(len(cl2)), 1, ts, qc)
    n = len(cl)
    cuoi = [0] + [3 * i for i in range(1, n)]
    assert lai2[cuoi] == pytest.approx(lai1, rel=1e-12, abs=1e-9)
    treo_nen = [treo2[0]] + [max(treo2[3 * i - 2:3 * i + 1]) for i in range(1, n)]
    assert np.array(treo_nen) == pytest.approx(treo1, rel=1e-12, abs=1e-9)
    for k in ("so_ro", "so_lenh", "tang_max", "so_cap", "con_mo"):
        assert tk1[k] == tk2[k], (k, tk1, tk2)
    for k in ("lai_gop", "phi_spread"):
        assert tk1[k] == pytest.approx(tk2[k], rel=1e-12, abs=1e-9), (k, tk1, tk2)
    assert len(ev1) == len(ev2), (len(ev1), len(ev2), ts)
    for a, b in zip(ev1, ev2):
        assert a[0] == b[0] and a[1] == _bar_goc(b[1]), (a, b)
        assert a[2] == pytest.approx(b[2], rel=1e-12, abs=1e-12), (a, b)
        assert a[3:] == pytest.approx(b[3:]) if a[0] == "mo" else a[3:] == b[3:], (a, b)
    assert len(ev1) > 0 and tk1["so_lenh"] >= 1


def _bo_doji(rng, hi, lo, cl):
    """Them nhieu nho de khong nen nao co dong = open / dong cham cuc tri (nen doji luon LA XANH theo gia tuyet doi, khong theo chieu ro,
    nen guong khong con tuong ung 1-1 o rieng cac nen do)."""
    cl = cl + rng.uniform(1e-9, 1e-7, len(cl))
    return np.maximum(hi, cl + 1e-9), np.minimum(lo, cl - 1e-9), cl


@pytest.mark.parametrize("seed", range(30))
def test_ro_ban_bang_ro_mua_tren_gia_dao_dau(may, seed):
    """Doi xung: `chieu=-1` tren (hi, lo, cl) === `chieu=+1` tren (-lo, -hi, -cl): lai, treo, thong ke y het, gia lenh doi dau. Bat loi dau
    (treo, cho lui, chot tien, tia) chi sai o mot chieu. Khong qua dem (ty le mua / ban khac nhau)."""
    rng = np.random.default_rng(2000 + seed)
    hi, lo, cl, sp, dem, ts, qc = _kich_ban(rng)
    hi, lo, cl = _bo_doji(rng, hi, lo, cl)
    dem = np.zeros(len(cl))
    lai_b, treo_b, tk_b, ev_b = _chay_mang(may, hi, lo, cl, sp, dem, -1, ts, qc)
    lai_m, treo_m, tk_m, ev_m = _chay_mang(may, -lo, -hi, -cl, sp, dem, 1, ts, qc)
    assert lai_b == pytest.approx(lai_m, rel=1e-12, abs=1e-9) and treo_b == pytest.approx(treo_m, rel=1e-12, abs=1e-9)
    for k in tk_b:
        assert tk_b[k] == pytest.approx(tk_m[k], rel=1e-12, abs=1e-9), (k, tk_b, tk_m)
    assert len(ev_b) == len(ev_m)
    for a, b in zip(ev_b, ev_m):
        assert a[:2] == b[:2], (a, b)                          # cung loai su kien, cung bar
        assert a[2] == pytest.approx(-b[2], rel=1e-12, abs=1e-12), (a, b)
        assert a[3:] == b[3:], (a, b)                          # lot, ma lenh, tang, ro (hoac ma lenh, ly do) y het


@pytest.mark.parametrize("seed", range(20))
def test_nhan_doi_lot_ra_dung_gap_doi(may, seed):
    """Lot x2 (so mu 2 nen phep nhan chinh xac): tien (lai, treo, spread) gap doi TUNG BIT, dem lenh, tang, ro khong doi, gia lenh khong doi.
    `chot_tien` quy theo lot nen nguong chot theo gia khong doi."""
    rng = np.random.default_rng(3000 + seed)
    hi, lo, cl, sp, dem, ts, qc = _kich_ban(rng)
    ts2 = dataclasses.replace(ts, lot=ts.lot * 2.0)
    a = _chay_mang(may, hi, lo, cl, sp, dem, 1, ts, qc)
    b = _chay_mang(may, hi, lo, cl, sp, dem, 1, ts2, qc)
    assert b[0] == pytest.approx(2.0 * a[0], rel=1e-12, abs=1e-9) and b[1] == pytest.approx(2.0 * a[1], rel=1e-12, abs=1e-9)
    for k in ("so_ro", "so_lenh", "tang_max", "so_cap", "con_mo"):
        assert a[2][k] == b[2][k], (k, a[2], b[2])
    for k in ("lai_gop", "phi_spread", "phi_swap"):
        assert b[2][k] == pytest.approx(2.0 * a[2][k], rel=1e-12, abs=1e-9)
    assert len(a[3]) == len(b[3])
    for x, y in zip(a[3], b[3]):
        assert x[0] == y[0] and x[1] == y[1], (x, y)           # cung loai su kien, cung bar
        assert x[2] == pytest.approx(y[2], rel=1e-12, abs=1e-12), (x, y)   # gia khop khong doi
        if x[0] == "mo":
            assert y[3] == pytest.approx(2.0 * x[3], rel=1e-12) and x[4:] == y[4:], (x, y)   # lot gap doi; ma lenh, tang, ro y het
        else:
            assert x[3:] == y[3:], (x, y)


# ------------------------------------------------------------------ 3. THONG KE
@pytest.mark.parametrize("ten,k", [("tia", 300), ("tia", 900), ("chot_tien", 300), ("chot_tien", 900), ("tia_cho_lui", 900),
                                    ("nhan_lot", 900)])
def test_duong_di_het_lech_do_phan_giai_va_phep_thu_du_luc_bat_cuc_tri(nhan, ten, k):
    """Random walk 1 tick / giay, KHONG drift, KHONG chi phi (ky vong ket qua that = 0), ghep doi theo hat giong (24 hat x 2 ngay): tren nen
    gop k tick, `cuc_tri` lech them hang chuc..tram don vi so voi chay tung tick (do 08/10: z = 9-17 sai so chuan o cac cau hinh nay) - day LA
    phep thu du luc: phai > 6 sai so chuan, neu khong thi 'duong_di khong lech' chi la phep thu mu. `duong_di` phai giam >= 80% lech do
    (hoac ngang nhieu 3 sai so chuan)."""
    d = KD.lech_ghep_doi(KD.CAU_HINH_MAU[ten], range(1, 25), 2, ks=(k,))
    ct, se_ct = KD.trung_binh_sai_so(d[("cuc_tri", k)])
    dd, se_dd = KD.trung_binh_sai_so(d[("duong_di", k)])
    assert ct > 6.0 * se_ct and ct > 0, ("phep thu khong bat duoc lech cua cuc_tri", ct, se_ct)
    assert abs(dd) <= 0.2 * ct + 3 * se_dd, ("duong_di con lech do phan giai", dd, se_dd, "cuc_tri", ct)


@pytest.mark.parametrize("ten", ["khong_tia", "tia", "cho_lui", "chot_tien", "tia_cho_lui"])
def test_duong_di_tren_doan_tick_ra_y_het_cuc_tri_tren_diem_tick(nhan, ten):
    """Tu nhat o muc tick: hai mo ta CUNG mot duong gia thang tung doan (`cuc_tri` tren nen diem, `duong_di` tren nen doan) phai cho cung
    mot ket qua (sai khac nho: gia khop cua cuc_tri o tick, ~nua tick moi lenh)."""
    m, se = KD.kiem_tu_nhat(KD.CAU_HINH_MAU[ten], range(1, 17), 2)
    assert abs(m) <= 3 * se + 0.25, (m, se)


def test_cong_cu_do_chay_duoc_va_in_bang():
    ra = io.StringIO()
    KD.in_bang(KD.chay_kiem(["tia"], range(1, 3), 0.25, ks=(60, 300)), ks=(60, 300), ra_ngoai=ra)
    s = ra.getvalue()
    assert "cuc_tri" in s and "duong_di" in s and "k=60" in s
    with pytest.raises(ValueError):
        KD.chay_kiem(["khong_co_cau_hinh_nay"], range(1, 2), 0.1)
    with pytest.raises(ValueError):
        KD.gop(np.arange(5.0), 10)
