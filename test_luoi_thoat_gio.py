# -*- coding: utf-8 -*-
"""Co che CAT LO CA RO + THOAT GIO + NGHI + LOC GIO VAO LENH cua engine luoi `duong_di` (08/10/2026) - NGU NGHIA, khong phai khop Python <-> C.

Vi sao file nay: `test_luoi_nhan.py` chung minh nhan C khop Python TUNG BIT (ke ca bon tinh nang moi), `test_ea_luoi_day_du.py` chung minh engine
khop CHINH ma EA tren san gia C++. Ca hai deu KHONG bat duoc mot hieu nham ma moi ben cung mac: cat truoc hay them tang truoc khi hai moc bang
nhau, thoat gio tinh theo gio MO hay gio DONG bar, nghi dem tu luc nao, cua so gio ap cho lenh dau hay cho moi lan mo lai, treo (lo noi) co bi
tinh hai lan sau khi cat... Ba hang rao:

  1. TAY TINH: moi kich ban nho co dap an tinh bang tay TRUOC khi chay (don vi pip, 1 lot = 10 tien / pip; cac ca "bang nhau" dung quy cach nhi
     phan `QC_NP`), chay ca Python va nhan C. Ca nao cung ghi ro no phan biet duoc hai cach hieu nao.
  2. PHAT LAI nhat ky lenh (`PhatLai`, test r1-r5) tren hang tram kich ban ngau nhien, CO VA KHONG CO khe gia giua hai bar: tu tinh lai luat cat /
     thoat gio / nghi / loc gio tu chinh nhat ky va doi chieu (gia cat = trung binh co trong so tru khoang cat, hoac gia mo bar khi nhay gia;
     them tang chi truoc cat khi moc cat nam SAU gia them; thoat gio dung luc, dung gia mo bar; nghi + cua so gio chi chan mo ro MOI; ro rong
     phai duoc mo lai dung gia dung luc; bar khong co su kien thi gia KHONG cham moc cat; lai / phi / thong ke / treo tinh lai khop).
     Kiem chung bang dot bien: 35 loi cu y gai vao engine Python deu bi bat (chi con 2 dot bien tuong duong chung minh duoc).
  3. BIEN DOI: guong `chieu=-1` === `chieu=+1` tren gia dao dau; nhan doi lot ra dung gap doi; tinh nang vo hieu (nghi / cua so gio khong anh
     huong khi khong bao gio cham toi) ra y het chay khong co tinh nang; cua so [0, 24) bang khong loc.
"""
from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd
import pytest

from nhan import luoi as LU
from nhan import luoi_nhan as LN
from test_luoi_duong_di import (BASE, GOC, GOC_NP, PT, PT_NP, QC, QC_NP, _bo_doji, kiem_nhat_ky, kiem_tk, nen, ts_)
from test_luoi_nhan import _df, _so_ngau_nhien_thoat


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


#: Giay epoch cua 00:00:00 ngay thu 10 (864000 = 10 x 86400): gio trong ngay cua bar = (tg - NGAY0) / 3600 mod 24.
NGAY0 = 864000.0


def theo_gio(n, gio0=0):
    """Cot thoi gian bar deu 1 gio: bar i mo luc (gio0 + i) gio cua ngay thu 10."""
    return NGAY0 + 3600.0 * (gio0 + np.arange(n, dtype=float))


def moc(*giay):
    """Cot thoi gian cho truoc, tinh bang giay ke tu 00:00 ngay thu 10."""
    return NGAY0 + np.asarray(giay, dtype=float)


def _chay_mang(may, hi, lo, cl, sp, dem, chieu, ts, qc, tg=None):
    ev: list = []
    if may == "py":
        lai, treo, tk = LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc, ev, tg)
    else:
        r = LN.mot_ro(hi, lo, cl, sp, dem, chieu, ts, qc, ev, tg)
        assert r is not None, "nhan C tra None cho %s" % (ts,)
        lai, treo, tk = r
    return np.asarray(lai), np.asarray(treo), tk, ev


def chay(may, bars, ts, *, chieu=1, sp_pip=0.0, dem=None, qc=QC, goc=GOC, tg=None):
    """bars[0] = (gia bat dau,), bars[i] = (hi, lo, cl) tinh bang pip so voi gia goc (xem `test_luoi_duong_di.nen`); `tg` = cot thoi gian
    (None = khong truyen, dung cho ca chi cat lo)."""
    hi, lo, cl = nen(*bars, qc=qc, goc=goc)
    n = len(cl)
    sp = np.full(n, sp_pip * qc.pip)
    dm = np.zeros(n) if dem is None else np.asarray(dem, float)
    return _chay_mang(may, hi, lo, cl, sp, dm, chieu, ts, qc, tg)


def mo0(bar, gia, ma_id, ro, lot=1.0):
    return ("mo", bar, gia, lot, ma_id, 0, ro)


def mo_tang(bar, gia, ma_id, tang, ro, lot=1.0):
    return ("mo", bar, gia, lot, ma_id, tang, ro)


# ================================================================== 1A. CAT LO CA RO
def test_c1_cat_lo_pip_cat_ca_ro_o_trung_binh_tru_khoang_cat_roi_mo_lai_o_gia_cat(may):
    """cat_lo_pip = 22, buoc 10, tran 4: nen do 0 -> -40. Moc cat ngay sau tang 1 / 2 / 3 la -22 / -27 / -32, moi cai nam SAU moc them tang ke
    tiep (-10 / -20 / -30) -> them tang truoc. Du 4 tang: trung binh (0-10-20-30)/4 = -15, moc cat = -15-22 = -37 (low -40 toi duoc).
    Cat ca ro o -37: lo (-37)+(-27)+(-17)+(-7) = -88 pip-lot = -880. Ro moi mo NGAY o -37 (tang L1); tang ke tiep -47 chua toi.
    treo[1] = 30: chi con lo noi cua ro MOI o low (3 pip), lo noi cu da nam trong -880 (khong tinh hai lan)."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -40, -40)], ts_(cat_lo_pip=22))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(1, -10, 1, 1, 0), mo_tang(1, -20, 2, 2, 0), mo_tang(1, -30, 3, 3, 0),
                      ("dong", 1, -37, 0, "cat"), ("dong", 1, -37, 1, "cat"), ("dong", 1, -37, 2, "cat"), ("dong", 1, -37, 3, "cat"),
                      mo0(1, -37, 4, 1)])
    kiem_tk(tk, lai_gop=-880, so_cat=1, so_gio=0, so_ro=0, so_lenh=5, tang_max=4, con_mo=1)
    assert lai == pytest.approx([0, -880]) and treo == pytest.approx([0, 30])


def test_c1b_ro_ban_cat_o_phia_tren(may):
    """Guong cua c1 cho ro BAN (`chieu=-1`): gia 0 -> +40, tang them o +10 / +20 / +30, cat o +37, ro moi ban o +37."""
    lai, treo, tk, ev = chay(may, [(0,), (40, 0, 40)], ts_(cat_lo_pip=22), chieu=-1)
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(1, 10, 1, 1, 0), mo_tang(1, 20, 2, 2, 0), mo_tang(1, 30, 3, 3, 0),
                      ("dong", 1, 37, 0, "cat"), ("dong", 1, 37, 1, "cat"), ("dong", 1, 37, 2, "cat"), ("dong", 1, 37, 3, "cat"),
                      mo0(1, 37, 4, 1)])
    kiem_tk(tk, lai_gop=-880, so_cat=1, so_lenh=5, tang_max=4, con_mo=1)
    assert lai == pytest.approx([0, -880]) and treo == pytest.approx([0, 30])


def test_c2_cat_lo_tien_moc_cat_keo_gan_gia_khi_them_tang(may):
    """cat_lo_tien = 2 (tien tren 0,01 lot; lot 1,0 -> nguong 200 tien) -> khoang cat = 200 / (100.000 x tong lot) = 20 pip / tong lot.
    1 lot: moc cat -20, them tang -10 -> them tang truoc (tang 2 o -10). 2 lot, trung binh -5: khoang cat 10 -> moc cat -15, them tang -20:
    CAT TRUOC. Cat o -15: lo (-15)+(-5) = -20 pip-lot = -200 = DUNG nguong (so tien co dinh, khong phu thuoc so tang). Ro moi o -15:
    lap lai (them tang -25, cat o -30, lo -200), ro thu ba mo o -30; -40 chua toi (low -38)."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -38, -38)], ts_(cat_lo_tien=2.0))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(1, -10, 1, 1, 0), ("dong", 1, -15, 0, "cat"), ("dong", 1, -15, 1, "cat"),
                      mo0(1, -15, 2, 1), mo_tang(1, -25, 3, 1, 1), ("dong", 1, -30, 2, "cat"), ("dong", 1, -30, 3, "cat"),
                      mo0(1, -30, 4, 2)])
    kiem_tk(tk, lai_gop=-400, so_cat=2, so_lenh=5, tang_max=2, con_mo=1)
    assert lai == pytest.approx([0, -400]) and treo == pytest.approx([0, 80])


def test_c3_dat_ca_hai_nguong_thi_nguong_nao_gan_trung_binh_hon_thang(may):
    """cat_lo_pip = 12 va cat_lo_tien = 2 (20 pip / tong lot): 1 lot -> min(12, 20) = 12 (theo pip), 2 lot -> min(12, 10) = 10 (theo tien).
    Ro 1: them tang -10 (moc cat -12 con sau), cat o -15 (trung binh -5 tru 10; lo -200). Ro 2 mo -15: them tang -25, cat -30 (lo -200).
    Ro 3 mo -30: moc cat -42 (12 pip) sau moc them tang -40 -> them tang -40; 2 lot moc cat -45 chua toi (low -43)."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -43, -43)], ts_(cat_lo_pip=12, cat_lo_tien=2.0))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(1, -10, 1, 1, 0), ("dong", 1, -15, 0, "cat"), ("dong", 1, -15, 1, "cat"),
                      mo0(1, -15, 2, 1), mo_tang(1, -25, 3, 1, 1), ("dong", 1, -30, 2, "cat"), ("dong", 1, -30, 3, "cat"),
                      mo0(1, -30, 4, 2), mo_tang(1, -40, 5, 1, 2)])
    kiem_tk(tk, lai_gop=-400, so_cat=2, so_lenh=6, tang_max=2, con_mo=2)
    assert lai == pytest.approx([0, -400]) and treo == pytest.approx([0, 160])


def test_c4_nhay_gia_vuot_ca_moc_cat_lan_moc_them_tang_thi_cat_o_gia_nhay(may):
    """Nen mo gap xuong: ro mo o 0, nen ke tiep high -35, low -50, close -45 -> gia mo = dong nen truoc kep vao [low, high] = -35. cat_lo_pip =
    15: moc cat -15 VA moc them tang -10 deu da bi vuot: ca hai khop o gia hien tai -35, bang nhau -> CAT (khong them tang roi cat). Lo -35
    pip-lot = -350. Ro moi mo o -35, them tang -45 (cham giua duong -35 -> -50); cat lan nay o -55 (chua toi, low -50) -> con 2 lenh."""
    lai, treo, tk, ev = chay(may, [(0,), (-35, -50, -45)], ts_(cat_lo_pip=15))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 1, -35, 0, "cat"), mo0(1, -35, 1, 1), mo_tang(1, -45, 2, 1, 1)])
    kiem_tk(tk, lai_gop=-350, so_cat=1, so_lenh=3, tang_max=2, con_mo=2)
    assert lai == pytest.approx([0, -350]) and treo == pytest.approx([0, 200])


def test_c5_moc_cat_bang_moc_them_tang_thi_cat_truoc(may):
    """Quy cach NHI PHAN (pip 0,25; gia 100): moc cat = moc them tang DUNG TUNG BIT (97,5). buoc 10, cat_lo_pip 10: bang nhau -> cat truoc
    (khong them tang): lo -10 pip-lot = -2500; ro moi o -10, lai bang nhau o -20 -> cat nua (-2500); ro thu ba mo -20, -30 chua toi."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -25, -25)], ts_(cat_lo_pip=10), qc=QC_NP, goc=GOC_NP)
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 1, -10, 0, "cat"), mo0(1, -10, 1, 1), ("dong", 1, -10 - 10, 1, "cat"), mo0(1, -20, 2, 2)],
                 qc=QC_NP, goc=GOC_NP)
    kiem_tk(tk, lai_gop=-10 * PT_NP * 2, so_cat=2, so_lenh=3, tang_max=1, con_mo=1)
    assert lai == pytest.approx([0, -2 * 10 * PT_NP]) and treo == pytest.approx([0, 5 * PT_NP])


def test_c6_cham_dung_moc_cat_la_cat_thieu_mot_chut_thi_khong(may):
    """Quy cach nhi phan, buoc 30 (them tang xa), cat_lo_pip 10: low DUNG -10 pip = moc cat -> CAT (cham la khop, nhu `bid <= muc` cua EA);
    low -9,75 pip (thieu 0,25 pip >> dung sai) -> KHONG cat."""
    ts = ts_(buoc=30.0, cat_lo_pip=10)
    lai, treo, tk, ev = chay(may, [(0,), (0, -10, -10)], ts, qc=QC_NP, goc=GOC_NP)
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 1, -10, 0, "cat"), mo0(1, -10, 1, 1)], qc=QC_NP, goc=GOC_NP)
    kiem_tk(tk, lai_gop=-10 * PT_NP, so_cat=1, so_lenh=2, con_mo=1)
    lai, treo, tk, ev = chay(may, [(0,), (0, -9.75, -9.75)], ts, qc=QC_NP, goc=GOC_NP)
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0)], qc=QC_NP, goc=GOC_NP)
    kiem_tk(tk, lai_gop=0, so_cat=0, so_lenh=1, con_mo=1)
    assert treo[1] == pytest.approx(9.75 * PT_NP)


def test_c7_cat_theo_tien_dung_trung_binh_co_trong_so_theo_lot(may):
    """Lot NHAN doi (1, 2), cat_lo_tien = 3 (nguong 300 tien o lot 1,0): 1 lot -> khoang cat 30 pip, them tang -10 truoc. 3 lot: trung binh co
    trong so (0x1 + -10x2)/3 = -6,667 (trung binh ngay thang -5 la SAI), khoang cat 0,003/3 = 10 pip -> moc cat -16,667, truoc moc them
    tang -20 -> cat o -16,667: lo (-16,667)x1 + (-6,667)x2 = -30 pip-lot = -300 = DUNG nguong. Ro moi (lot 1) mo o -16,667."""
    ts = ts_(kieu_lot="nhan", he_so_lot=2.0, cat_lo_tien=3.0)
    lai, treo, tk, ev = chay(may, [(0,), (0, -17, -17)], ts)
    cat = -50.0 / 3.0
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(1, -10, 1, 1, 0, lot=2.0), ("dong", 1, cat, 0, "cat"), ("dong", 1, cat, 1, "cat"),
                      mo0(1, cat, 2, 1)])
    kiem_tk(tk, lai_gop=-300, so_cat=1, so_lenh=3, tang_max=2, con_mo=1)
    assert lai == pytest.approx([0, -300]) and treo == pytest.approx([0, (17 + cat) * PT])      # ro moi: (-16,667) -> low -17


def test_c8_cat_xong_mo_lai_ngay_ke_ca_khi_co_cho_lui(may):
    """`cho_lui` chi hoan viec mo lai sau CHOT LOI; sau CAT LO ro moi vao ngay o gia cat. cat_lo_pip 13, cho_lui 4: them tang -10, trung binh
    -5, moc cat -18 truoc moc them tang -20 -> cat o -18 (lo -26 pip-lot = -260), mo lai o -18 ngay (khong cho lui toi -22)."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -20, -20)], ts_(cat_lo_pip=13, cho_lui=4))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(1, -10, 1, 1, 0), ("dong", 1, -18, 0, "cat"), ("dong", 1, -18, 1, "cat"), mo0(1, -18, 2, 1)])
    kiem_tk(tk, lai_gop=-260, so_cat=1, so_lenh=3, tang_max=2, con_mo=1)


def test_c9_cat_khong_dung_den_cot_thoi_gian_va_khong_doi_khi_co_tg(may):
    """Cat lo thuan (khong thoat gio / nghi / loc gio) khong can `tg`; co truyen `tg` thua vao thi ket qua y het."""
    bars = [(0,), (0, -40, -40)]
    a = chay(may, bars, ts_(cat_lo_pip=22))
    b = chay(may, bars, ts_(cat_lo_pip=22), tg=theo_gio(2))
    assert a[3] == b[3] and a[0].tolist() == b[0].tolist() and a[1].tolist() == b[1].tolist() and a[2] == b[2]


def test_c10_treo_doi_goc_sau_cat_lo_da_chot_khong_tinh_hai_lan_khi_lo_noi_da_thay_truoc_luc_cat(may):
    """`treo` = lo noi lon nhat trong bar; khi cat chot mot khoan lo THI phan lo noi do khong duoc tinh them lan nua. Bar 1: ro (lenh o 0) troi
    xuong -8 -> treo[1] = 80. Bar 2 mo o -8 (lo noi 80 da thay luc mo), roi xuong -40: them tang -10 / -20 / -30, CAT o -37 (c1: lo -880).
    Lo chot -880 nuot het 80 -> doi goc ve 0, con lai chi lo noi cua ro moi o low: treo[2] = 30 (khong phai max(80, 30) = 80)."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -8, -8), (-8, -40, -40)], ts_(cat_lo_pip=22))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(2, -10, 1, 1, 0), mo_tang(2, -20, 2, 2, 0), mo_tang(2, -30, 3, 3, 0),
                      ("dong", 2, -37, 0, "cat"), ("dong", 2, -37, 1, "cat"), ("dong", 2, -37, 2, "cat"), ("dong", 2, -37, 3, "cat"),
                      mo0(2, -37, 4, 1)])
    kiem_tk(tk, lai_gop=-880, so_cat=1, so_lenh=5, tang_max=4, con_mo=1)
    assert lai == pytest.approx([0, 0, -880]) and treo == pytest.approx([0, 80, 30])


def test_c10b_treo_doi_goc_chi_tru_phan_lo_rong_cua_bar_phan_con_du_van_con(may):
    """Bar 2 mo o -8 (lo noi 80), tia xuong -9 (lo noi 90), len 20 = chot ro cu (lenh o 0, tp 20 -> +200) va mo ro moi o 20, ha xuong 2: them
    tang 10, trung binh 15, cat_lo_pip 12 -> moc cat 3 (truoc moc them tang 0): cat o 3 lo (3-20)+(3-10) = -24 pip-lot = -240. Lai rong
    cua bar den luc cat = +200 - 240 = -40 -> treo doi goc: 90 - 40 = 50 (con du, KHONG ve 0); ro moi o 3 co lo noi 1 pip = 10 < 50 -> treo[2] = 50."""
    lai, treo, tk, ev = chay(may, [(0,), (0, -8, -8), (20, -9, 2)], ts_(cat_lo_pip=12, tp=20.0))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 2, 20, 0, "tp"), mo0(2, 20, 1, 1), mo_tang(2, 10, 2, 1, 1),
                      ("dong", 2, 3, 1, "cat"), ("dong", 2, 3, 2, "cat"), mo0(2, 3, 3, 2)])
    kiem_tk(tk, lai_gop=-40, so_cat=1, so_ro=1, so_lenh=4, tang_max=2, con_mo=1)
    assert lai == pytest.approx([0, 0, -40]) and treo == pytest.approx([0, 80, 50])


# ================================================================== 1B. THOAT THEO GIO
def test_t1_thoat_gio_dong_ro_o_gia_mo_bar_dau_tien_du_tuoi_roi_mo_lai_o_gia_do(may):
    """thoat_gio = 2 (bar 1 gio). Ro mo o 0 (tuoi 0). Bar 1 (tuoi 1 gio): chua. Bar 2 (tuoi 2 gio): dong o GIA MO bar = close bar truoc kep
    vao [low, high] = -6 (lo -6 pip-lot = -60), mo ro moi o -6 (dong ho chay lai tu bar 2). Bar 3 (tuoi 1): chua. Bar 4 (tuoi 2): dong o gia
    mo -8 (lo -2 pip-lot = -20), mo ro thu ba o -8. treo: bar 1 = 6 pip (low -6); bar 2 = 2 (ro MOI o low -8, lo cu da nam trong -60);
    bar 3 = 3; bar 4 = 2."""
    bars = [(0,), (-2, -6, -5), (-6, -8, -7), (-7, -9, -8), (-8, -10, -9)]
    lai, treo, tk, ev = chay(may, bars, ts_(thoat_gio=2.0), tg=theo_gio(5))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 2, -6, 0, "gio"), mo0(2, -6, 1, 1), ("dong", 4, -8, 1, "gio"), mo0(4, -8, 2, 2)])
    kiem_tk(tk, lai_gop=-80, so_gio=2, so_cat=0, so_ro=0, so_lenh=3, con_mo=1, tang_max=1)
    assert lai == pytest.approx([0, 0, -60, -60, -80]) and treo == pytest.approx([0, 60, 20, 30, 20])


def test_t2_chua_du_tuoi_mot_giay_thi_chua_thoat(may):
    """thoat_gio = 2, bar mo luc 0 / 3600 / 7199 / 7200 giay: bar 2 (tuoi 7199 giay) CHUA thoat, bar 3 (7200) thoat o gia mo -2."""
    bars = [(0,), (-1, -3, -2), (-1, -3, -2), (-1, -3, -2)]
    lai, treo, tk, ev = chay(may, bars, ts_(thoat_gio=2.0), tg=moc(0, 3600, 7199, 7200))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 3, -2, 0, "gio"), mo0(3, -2, 1, 1)])
    kiem_tk(tk, so_gio=1, lai_gop=-20, so_lenh=2)


def test_t3_gio_thap_phan_lam_tron_nua_len_den_giay(may):
    """thoat_gio = 4,1: 4,1 x 3600 = 14759,999999999998 (double) -> lam tron `floor(x + 0,5)` = 14760 giay. Bar mo luc 14759 chua thoat, 14760
    thoat. (Cat cut `floor(x)` se cho 14759 -> thoat o bar 1, sai.)"""
    bars = [(0,), (-1, -3, -2), (-1, -3, -2), (-1, -3, -2)]
    lai, treo, tk, ev = chay(may, bars, ts_(thoat_gio=4.1), tg=moc(0, 14759, 14760, 14761))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 2, -2, 0, "gio"), mo0(2, -2, 1, 1)])
    kiem_tk(tk, so_gio=1, lai_gop=-20, so_lenh=2)


def test_t4_chot_loi_khoi_dong_lai_dong_ho_thoat_gio(may):
    """thoat_gio = 2: ro 0 chot loi o bar 1 (+5, tp), mo lai o 5 luc bar 1 -> tuoi tinh tu bar 1. Bar 3 (cach bar 1 hai gio) moi thoat (o gia
    mo 4, lo -1 pip-lot). Neu dong ho khong khoi dong lai khi chot loi, ro se thoat o bar 2."""
    bars = [(0,), (6, 0, 5), (5, 4, 4), (4, 3, 3)]
    lai, treo, tk, ev = chay(may, bars, ts_(thoat_gio=2.0), tg=theo_gio(4))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 1, 5, 0, "tp"), mo0(1, 5, 1, 1), ("dong", 3, 4, 1, "gio"), mo0(3, 4, 2, 2)])
    kiem_tk(tk, lai_gop=40, so_ro=1, so_gio=1, so_lenh=3, con_mo=1)


def test_t4b_thoat_gio_o_bar_dau_tien_co_gia_nhay_van_o_gia_mo_bar(may):
    """thoat_gio = 1: bar 1 mo gap xuong (gia mo -5 = high, vi close bar truoc 0 kep vao [-8, -5]): dong o -5 (lo -50), mo lai -5."""
    lai, treo, tk, ev = chay(may, [(0,), (-5, -8, -6)], ts_(thoat_gio=1.0), tg=theo_gio(2))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 1, -5, 0, "gio"), mo0(1, -5, 1, 1)])
    kiem_tk(tk, lai_gop=-50, so_gio=1, so_lenh=2)
    assert lai == pytest.approx([0, -50]) and treo == pytest.approx([0, 30])


def test_t5_thoat_gio_dong_ca_ro_nhieu_tang(may):
    """thoat_gio = 2: bar 1 them tang o -10 (low -12; treo 14 pip-lot = 140). Bar 2 (tuoi 2 gio) gia mo -11: dong CA HAI lenh o -11 (lo
    (-11)+(-1) = -12 pip-lot = -120), mo ro moi o -11."""
    bars = [(0,), (-1, -12, -11), (-9, -13, -12)]
    lai, treo, tk, ev = chay(may, bars, ts_(thoat_gio=2.0), tg=theo_gio(3))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(1, -10, 1, 1, 0), ("dong", 2, -11, 0, "gio"), ("dong", 2, -11, 1, "gio"), mo0(2, -11, 2, 1)])
    kiem_tk(tk, lai_gop=-120, so_gio=1, so_lenh=3, tang_max=2, con_mo=1)
    assert lai == pytest.approx([0, 0, -120]) and treo == pytest.approx([0, 140, 20])


# ================================================================== 1C. NGHI
def test_n1_nghi_tinh_tu_gio_mo_bar_co_cat_va_het_nghi_dung_luc(may):
    """cat_lo_pip 13, nghi_gio 3: ro cat o bar 1 (mo luc 3600 giay) -> nghi den 3600 + 10800 = 14400. Bar 2 (7200), bar 3 (14399): CHUA duoc
    mo ro moi (ro rong). Bar 4 (14400): duoc, mo o gia mo bar -24. treo bar 1 = 0 (lo noi cu da nam trong -260)."""
    bars = [(0,), (0, -20, -20), (-18, -25, -24), (-20, -25, -24), (-22, -26, -25)]
    lai, treo, tk, ev = chay(may, bars, ts_(cat_lo_pip=13, nghi_gio=3.0), tg=moc(0, 3600, 7200, 14399, 14400))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), mo_tang(1, -10, 1, 1, 0), ("dong", 1, -18, 0, "cat"), ("dong", 1, -18, 1, "cat"), mo0(4, -24, 2, 1)])
    kiem_tk(tk, lai_gop=-260, so_cat=1, so_lenh=3, con_mo=1)
    assert lai == pytest.approx([0, -260, -260, -260, -260]) and treo == pytest.approx([0, 0, 0, 0, 20])


def test_n2_chot_loi_khong_gay_nghi(may):
    """nghi_gio 3 nhung chi chot loi (khong cat / thoat gio) thi khong bao gio nghi: nen xanh +12 chot hai ro lien tiep (o 5 va 10), moi ro mo lai
    NGAY o gia chot."""
    lai, treo, tk, ev = chay(may, [(0,), (12, 0, 11)], ts_(nghi_gio=3.0), tg=theo_gio(2))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 1, 5, 0, "tp"), mo0(1, 5, 1, 1), ("dong", 1, 10, 1, "tp"), mo0(1, 10, 2, 2)])
    kiem_tk(tk, so_ro=2, lai_gop=100, so_lenh=3, con_mo=1)


def test_n3_thoat_gio_cung_gay_nghi(may):
    """thoat_gio 1 + nghi_gio 2: thoat o bar 1 (3600) -> nghi den 10800: bar 2 (7200) chua mo, bar 3 (10800) mo o gia mo -3. Tuoi 1 gio ->
    bar 4 thoat o -4 (lo -1 pip-lot moi lan) va nghi tiep (khong mo lai)."""
    bars = [(0,), (-1, -3, -2), (-2, -4, -3), (-3, -5, -4), (-4, -6, -5)]
    lai, treo, tk, ev = chay(may, bars, ts_(thoat_gio=1.0, nghi_gio=2.0), tg=theo_gio(5))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 1, -1, 0, "gio"), mo0(3, -3, 1, 1), ("dong", 4, -4, 1, "gio")])
    kiem_tk(tk, lai_gop=-20, so_gio=2, so_lenh=2, con_mo=0)
    assert lai == pytest.approx([0, -10, -10, -10, -20]) and treo == pytest.approx([0, 0, 0, 20, 0])


# ================================================================== 1D. LOC GIO VAO LENH
def test_h1_cua_so_chi_chan_mo_ro_moi_ro_rong_cho_bar_duoc_phep_va_mo_o_gia_mo_bar(may):
    """Cua so [2h, 5h). Bar 0 (0h), 1 (1h): ngoai cua so -> khong co lenh dau. Bar 2 (2h): mo o gia mo bar (0). Bar 3 (3h): chot +5, mo lai
    (trong cua so). Bar 4 (4h): chot +10, mo lai. Bar 5 (5h = ngoai): chot +15, KHONG mo lai. Bar 6: rong."""
    bars = [(0,), (1, -1, 0), (1, -1, 0), (7, 0, 6), (12, 5, 11), (18, 10, 17), (20, 16, 19)]
    ts = ts_(gio_vao_tu=2.0, gio_vao_den=5.0)
    lai, treo, tk, ev = chay(may, bars, ts, tg=theo_gio(7))
    kiem_nhat_ky(ev, [mo0(2, 0, 0, 0), ("dong", 3, 5, 0, "tp"), mo0(3, 5, 1, 1), ("dong", 4, 10, 1, "tp"), mo0(4, 10, 2, 2),
                      ("dong", 5, 15, 2, "tp")])
    kiem_tk(tk, so_ro=3, lai_gop=150, so_lenh=3, con_mo=0, tang_max=1)
    assert lai == pytest.approx([0, 0, 0, 50, 100, 150, 150]) and treo == pytest.approx([0, 0, 10, 0, 0, 0, 0])


def test_h1b_ro_rong_mo_o_gia_mo_cua_bar_duoc_phep_khong_phai_close_bar_truoc(may):
    """Cua so [2h, 5h): bar 2 mo gap len (close bar 1 = 0, bar 2 co low 3) -> gia mo kep = 3 -> lenh dau o 3 (khong phai 0)."""
    lai, treo, tk, ev = chay(may, [(0,), (0, 0, 0), (5, 3, 4)], ts_(gio_vao_tu=2.0, gio_vao_den=5.0), tg=theo_gio(3))
    kiem_nhat_ky(ev, [mo0(2, 3, 0, 0)])
    kiem_tk(tk, so_lenh=1, con_mo=1, lai_gop=0)


def test_h2_cua_so_qua_nua_dem(may):
    """Cua so [22h, 4h) (qua nua dem), bar 0 luc 21h. Bar 0 ngoai cua so; bar 1 (22h) mo o 0. Moi bar sau chot +5 (6 lan tai 5, 10, ..., 30) va
    mo lai o gia chot trong luc 23h, 0h, 1h, 2h, 3h; bar 7 (4h, ngoai) chot +30 va KHONG mo lai. Bar 8, 9 (5h, 6h): rong."""
    bars = [(0,), (1, -1, 0)]
    for j in range(2, 10):
        bars.append((5 * (j - 1) + 2, 5 * (j - 2), 5 * (j - 1) + 1))
    lai, treo, tk, ev = chay(may, bars, ts_(gio_vao_tu=22.0, gio_vao_den=4.0), tg=theo_gio(10, gio0=21))
    mong = [mo0(1, 0, 0, 0)]
    for k in range(6):
        mong.append(("dong", 2 + k, 5 * (k + 1), k, "tp"))
        if k < 5:
            mong.append(mo0(2 + k, 5 * (k + 1), k + 1, k + 1))
    kiem_nhat_ky(ev, mong)
    kiem_tk(tk, so_ro=6, lai_gop=300, so_lenh=6, con_mo=0)


def test_h3_gio_vao_tu_bang_gio_vao_den_la_tat_va_khong_can_tg(may):
    """tu == den = TAT (khong phai 'khong mo bao gio' hay 'ca ngay'): khong can `tg`, ket qua y het khong dat cua so."""
    bars = [(0,), (1, -1, 0), (7, 0, 6), (12, 5, 11), (18, 10, 17)]
    a = chay(may, bars, ts_())
    b = chay(may, bars, ts_(gio_vao_tu=5.0, gio_vao_den=5.0))
    assert a[3] == b[3] and a[0].tolist() == b[0].tolist() and a[1].tolist() == b[1].tolist() and a[2] == b[2]
    assert a[2]["so_ro"] == 3


def test_h4_cua_so_ca_ngay_bang_khong_loc(may):
    """Cua so [0h, 24h) la ca ngay: y het khong loc (nhung phai co `tg`)."""
    bars = [(0,), (1, -1, 0), (7, 0, 6), (-3, -14, -13), (12, 5, 11), (18, 10, 17), (-20, -26, -25), (-20, -40, -39)]
    tg = theo_gio(len(bars), gio0=20)
    a = chay(may, bars, ts_(), tg=tg)
    b = chay(may, bars, ts_(gio_vao_tu=0.0, gio_vao_den=24.0), tg=tg)
    assert a[3] == b[3] and a[0].tolist() == b[0].tolist() and a[1].tolist() == b[1].tolist() and a[2] == b[2]


def test_h5_ranh_gioi_cua_so_tinh_theo_giay_gio_mo_bar(may):
    """Cua so [2h, 5h) = [7200, 18000) giay: bar mo luc 7199 giay chua duoc, 7200 duoc; bar mo luc 17999 duoc (mo lai sau chot), 18000 khong."""
    bars = [(0,), (1, -1, 0), (1, -1, 0), (7, 0, 6), (12, 5, 11)]
    lai, treo, tk, ev = chay(may, bars, ts_(gio_vao_tu=2.0, gio_vao_den=5.0), tg=moc(0, 7199, 7200, 17999, 18000))
    kiem_nhat_ky(ev, [mo0(2, 0, 0, 0), ("dong", 3, 5, 0, "tp"), mo0(3, 5, 1, 1), ("dong", 4, 10, 1, "tp")])
    kiem_tk(tk, so_ro=2, lai_gop=100, so_lenh=2, con_mo=0)


def test_h6_cua_so_khong_chan_them_tang_cua_ro_dang_mo_va_khong_chan_chot(may):
    """Cua so [2h, 3h): ro mo luc bar 2 (2h). Bar 3 (3h, NGOAI cua so): them tang o -10 (van duoc), bar 4 (4h): chot ca ro o 0 (lo/lai
    (0-0)+(0+10) = +10 pip-lot = 100) nhung KHONG mo lai."""
    bars = [(0,), (1, -1, 0), (1, -1, 0), (0, -12, -11), (2, -11, 1)]
    lai, treo, tk, ev = chay(may, bars, ts_(gio_vao_tu=2.0, gio_vao_den=3.0), tg=theo_gio(5))
    kiem_nhat_ky(ev, [mo0(2, 0, 0, 0), mo_tang(3, -10, 1, 1, 0), ("dong", 4, 0, 0, "tp"), ("dong", 4, 0, 1, "tp")])
    kiem_tk(tk, so_ro=1, lai_gop=100, tang_max=2, so_lenh=2, con_mo=0)
    assert lai == pytest.approx([0, 0, 0, 0, 100]) and treo == pytest.approx([0, 0, 10, 140, 120])


def test_h7_cua_so_khong_chan_cat_lo_nhung_chan_mo_lai_sau_cat(may):
    """Cua so [2h, 3h) + cat_lo_pip 13: ro mo luc 2h, bar 3 (ngoai cua so) them tang -10 roi CAT o -18 (lo -260); KHONG mo lai (ngoai cua so)."""
    bars = [(0,), (1, -1, 0), (1, -1, 0), (0, -20, -20)]
    lai, treo, tk, ev = chay(may, bars, ts_(gio_vao_tu=2.0, gio_vao_den=3.0, cat_lo_pip=13), tg=theo_gio(4))
    kiem_nhat_ky(ev, [mo0(2, 0, 0, 0), mo_tang(3, -10, 1, 1, 0), ("dong", 3, -18, 0, "cat"), ("dong", 3, -18, 1, "cat")])
    kiem_tk(tk, lai_gop=-260, so_cat=1, so_lenh=2, tang_max=2, con_mo=0)


def test_h8_lenh_dau_o_bar_0_cung_theo_cua_so(may):
    """Bar 0 luc 3h trong cua so [0h, 5h) -> co lenh dau o close bar 0. Bar 0 luc 6h (ngoai cua so) -> KHONG co lenh dau, bar 1 luc 7h cung
    ngoai -> khong co lenh nao ca."""
    ts = ts_(gio_vao_tu=0.0, gio_vao_den=5.0)
    lai, treo, tk, ev = chay(may, [(0,), (1, -1, 0)], ts, tg=theo_gio(2, gio0=3))
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0)])
    lai, treo, tk, ev = chay(may, [(0,), (1, -1, 0)], ts, tg=theo_gio(2, gio0=6))
    assert ev == [] and tk["so_lenh"] == 0 and tk["con_mo"] == 0
    assert lai.tolist() == [0.0, 0.0] and treo.tolist() == [0.0, 0.0]


def test_h9_gio_trong_ngay_cua_moc_thoi_gian_am_la_phan_du_duong(may):
    """Moc thoi gian am (truoc 1970): gio trong ngay = phan du DUONG cua tg mod 86400 (-3600 giay la 23h, khong phai -1h). Cua so [22h, 24h) +
    thoat_gio 1h: bar 0 (22h) co lenh dau; bar 1 (23h) het han -> thoat roi mo lai (23h nam trong cua so); bar 2 (0h) het han -> thoat, khong
    mo lai (0h ngoai cua so); bar 3 (1h) van ngoai cua so."""
    tg = np.asarray([-7200.0, -3600.0, 0.0, 3600.0])
    bars = [(0,), (1, -1, 0), (1, -1, 0), (1, -1, 0)]
    lai, treo, tk, ev = chay(may, bars, ts_(thoat_gio=1.0, gio_vao_tu=22.0, gio_vao_den=24.0), tg=tg)
    kiem_nhat_ky(ev, [mo0(0, 0, 0, 0), ("dong", 1, 0, 0, "gio"), mo0(1, 0, 1, 1), ("dong", 2, 0, 1, "gio")])
    kiem_tk(tk, so_gio=2, so_lenh=2, con_mo=0)


# ================================================================== 2A. DAU VAO XAU / NGOAI MIEN (hop dong chung Python <-> C)
def _ban_nho():
    """Ba bar nho: (hi, lo, cl, sp, dem)."""
    hi, lo, cl = nen((0,), (1, -1, 0), (2, -2, 1))
    n = len(cl)
    return hi, lo, cl, np.zeros(n), np.zeros(n)


def _bao_loi_o_ca_hai(ts, tg, mau, hi_lo=None):
    """Python NEM ValueError khop `mau`; nhan C tu choi (None) de Python lo; duong dispatcher (`_mot_ro_nhanh`) cung nem dung loi do."""
    hi, lo, cl, sp, dm = hi_lo or _ban_nho()
    with pytest.raises(ValueError, match=mau):
        LU.mot_ro_chuan(hi, lo, cl, sp, dm, 1, ts, QC, [], tg)
    assert LN.mot_ro(hi, lo, cl, sp, dm, 1, ts, QC, [], tg) is None, "nhan C phai nhuong cho Python de Python bao loi"
    with pytest.raises(ValueError, match=mau):
        LU._mot_ro_nhanh(hi, lo, cl, sp, dm, 1, ts, QC, [], tg)


@pytest.mark.parametrize("sua", [dict(thoat_gio=1.0), dict(nghi_gio=1.0), dict(gio_vao_tu=1.0, gio_vao_den=5.0),
                                 dict(thoat_gio=1.0, nghi_gio=2.0, gio_vao_tu=22.0, gio_vao_den=4.0)])
def test_e1_thieu_cot_thoi_gian_thi_bao_loi_khong_chay_am_tham(nhan, sua):
    """Tinh nang gio ma khong co `tg` -> ValueError ro rang o Python; nhan C tra None (khong tu doan, khong doc bo nho bay)."""
    _bao_loi_o_ca_hai(ts_(**sua), None, "cot thoi gian")


@pytest.mark.parametrize("ten,tg", [
    ("ngan_hon", np.zeros(2)), ("dai_hon", np.zeros(4)), ("hai_chieu", np.zeros((3, 1))), ("nan", np.array([0.0, np.nan, 3.0])),
    ("inf", np.array([0.0, 1.0, np.inf])), ("am_inf", np.array([-np.inf, 1.0, 2.0])),
])
def test_e2_cot_thoi_gian_sai_hinh_thi_bao_loi(nhan, ten, tg):
    """`tg` phai la mang 1 chieu, huu han, cung do dai voi chuoi gia."""
    _bao_loi_o_ca_hai(ts_(thoat_gio=1.0), tg, "tg phai la mang 1 chieu")


_NGOAI_MIEN = [
    dict(cat_lo_pip=-1.0), dict(cat_lo_tien=-0.5), dict(thoat_gio=-1.0), dict(nghi_gio=-0.25), dict(gio_vao_tu=25.0), dict(gio_vao_den=-1.0),
    dict(gio_vao_tu=-0.5), dict(gio_vao_den=24.5), dict(thoat_gio=2e6), dict(nghi_gio=1000001.0),
    dict(cat_lo_pip=float("nan")), dict(cat_lo_pip=float("inf")), dict(cat_lo_tien=float("nan")), dict(cat_lo_tien=float("inf")),
    dict(thoat_gio=float("nan")), dict(thoat_gio=float("inf")), dict(nghi_gio=float("nan")), dict(nghi_gio=float("inf")),
    dict(gio_vao_tu=float("nan")), dict(gio_vao_den=float("inf")),
    dict(cat_lo_pip=True), dict(cat_lo_tien=True), dict(thoat_gio=True), dict(nghi_gio=True), dict(gio_vao_tu=True), dict(gio_vao_den=True),
    dict(cat_lo_pip="10"), dict(thoat_gio=None), dict(gio_vao_den="5"),
]


@pytest.mark.parametrize("sua", _NGOAI_MIEN)
def test_e3_tham_so_moi_ngoai_mien_thi_python_nem_loi_va_nhan_c_nhuong(nhan, sua):
    """Mot nguon `mien_duong_di`: Python nem ValueError ("khop_bar='duong_di': ..."), nhan C tra None. Ca ba cua vao (engine Python chuan,
    dispatcher, va `LU.chay` qua DataFrame) bao CUNG mot loi ro rang - khong con OverflowError / TypeError / 'cannot convert float NaN'
    cua `_giay` khi gia tri la inf / None / NaN."""
    ts = ts_(**sua)
    assert LU.mien_duong_di(ts, QC), "mien_duong_di phai tu choi %s" % (sua,)
    tg = theo_gio(3)
    hi, lo, cl, sp, dm = _ban_nho()
    assert LN.mot_ro(hi, lo, cl, sp, dm, 1, ts, QC, [], tg) is None
    with pytest.raises(ValueError, match="duong_di"):
        LU.mot_ro_chuan(hi, lo, cl, sp, dm, 1, ts, QC, [], tg)
    with pytest.raises(ValueError, match="duong_di"):
        LU._mot_ro_nhanh(hi, lo, cl, sp, dm, 1, ts, QC, [], tg)
    with pytest.raises(ValueError, match="duong_di"):
        LU.chay(_df(120), ts, 10000.0)


def test_e3b_kieu_so_float32_cua_tham_so_moi_python_va_nhan_c_deu_chay_va_khop(nhan):
    """`np.float32` la so huu han nen `mien_duong_di` chap nhan; ca hai ben doi no ra `float` truoc khi tinh (khong phep tinh nao giu float32)
    -> cung mot ket qua tung bit. (Khac voi `lot` / `buoc`: ben do Python nhan thang vao phep nhan nen float32 lam lech - bi `kha_dung` loai.)"""
    hi, lo, cl, sp, dm = _ban_nho()
    n = len(cl)
    tg = theo_gio(n)
    for sua in (dict(cat_lo_pip=np.float32(3.3)), dict(cat_lo_tien=np.float32(0.7)), dict(thoat_gio=np.float32(1.1)),
                dict(nghi_gio=np.float32(0.5), cat_lo_pip=5.0), dict(gio_vao_tu=np.float32(0.5), gio_vao_den=np.float32(23.5)),
                dict(thoat_gio=np.int64(2)), dict(gio_vao_tu=np.int64(1), gio_vao_den=np.int64(20))):
        ts = ts_(**sua)
        evp, evc = [], []
        a = LU.mot_ro_chuan(hi, lo, cl, sp, dm, 1, ts, QC, evp, tg)
        b = LN.mot_ro(hi, lo, cl, sp, dm, 1, ts, QC, evc, tg)
        assert b is not None, sua
        assert a[0].tolist() == b[0].tolist() and a[1].tolist() == b[1].tolist() and a[2] == b[2] and evp == evc, sua


def test_e4_mo_hinh_cuc_tri_cu_tu_choi_tinh_nang_moi_khong_bo_qua_am_tham(nhan):
    """`khop_bar='cuc_tri'` (ban cu) khong cai dat sau tinh nang moi: dat != 0 -> ValueError chu khong chay ra ket qua nhu da tat."""
    hi, lo, cl, sp, dm = _ban_nho()
    tg = theo_gio(3)
    for sua in (dict(cat_lo_pip=5.0), dict(cat_lo_tien=1.0), dict(thoat_gio=1.0), dict(nghi_gio=1.0), dict(gio_vao_tu=1.0, gio_vao_den=5.0),
                dict(gio_vao_tu=22.0, gio_vao_den=4.0)):
        ts = ts_(khop_bar="cuc_tri", **sua)
        with pytest.raises(ValueError, match="cuc_tri"):
            LU.mot_ro_chuan(hi, lo, cl, sp, dm, 1, ts, QC, [], tg)
        assert LN.mot_ro(hi, lo, cl, sp, dm, 1, ts, QC, [], tg) is None
    # doi chung: chua dat tinh nang nao -> cuc_tri van chay nhu cu
    LU.mot_ro_chuan(hi, lo, cl, sp, dm, 1, ts_(khop_bar="cuc_tri"), QC, [], tg)
    # tinh nang dat 0 = tat: khong bi tu choi
    LU.mot_ro_chuan(hi, lo, cl, sp, dm, 1, ts_(khop_bar="cuc_tri", cat_lo_pip=0.0, thoat_gio=0, gio_vao_tu=0.0, gio_vao_den=0.0), QC, [], tg)
    # "dat != 0" la tieu chi cua `tinh_nang_duong_di_dang_bat`: ke ca cua so tu == den != 0 (o duong_di la TAT) cung bi cuc_tri tu choi - thanh
    # than co chu y (khong am tham bo qua mot truong khac 0), khong phai loi
    ts = ts_(khop_bar="cuc_tri", gio_vao_tu=3.0, gio_vao_den=3.0)
    with pytest.raises(ValueError, match="cuc_tri"):
        LU.mot_ro_chuan(hi, lo, cl, sp, dm, 1, ts, QC, [], tg)
    assert LN.mot_ro(hi, lo, cl, sp, dm, 1, ts, QC, [], tg) is None


@pytest.mark.parametrize("sua", [dict(cat_lo_pip=5.0), dict(cat_lo_tien=1.0), dict(thoat_gio=1.0), dict(nghi_gio=1.0), dict(gio_vao_tu=1.0, gio_vao_den=5.0),
                                 dict(cat_lo_pip=float("nan")), dict(thoat_gio=float("inf")), dict(nghi_gio=float("nan")), dict(gio_vao_den=float("inf"))])
def test_e4b_chay_qua_dataframe_voi_cuc_tri_nem_loi_cuc_tri_khong_phai_loi_doi_gio(nhan, sua):
    """`LU.chay` voi mo hinh cu: loi la "cuc_tri khong cai dat ..." - KHONG bi `cau_hinh_gio` / `_giay` nem loi la ve NaN / inf / kieu (cho
    nguoi goi biet DUNG nguyen nhan: mo hinh cu khong co tinh nang nay, khong phai gia tri sai)."""
    with pytest.raises(ValueError, match="cuc_tri"):
        LU.chay(_df(120), ts_(khop_bar="cuc_tri", **sua), 10000.0)


def test_e5_chay_mang_thieu_tg_trong_du_lieu_chay_thi_bao_loi():
    """`DuLieuChay` dung tay (khong qua `chuan_bi`) khong co `tg` ma ThamSo can gio -> ValueError nhac `chuan_bi`."""
    df = _df(200)
    dl = LU.chuan_bi(df)
    assert dl.tg is not None and len(dl.tg) == len(df)
    khong_tg = LU.DuLieuChay(dl.hi, dl.lo, dl.cl, dl.sp, dl.dem, dl.idx, dl.qc)
    assert khong_tg.tg is None
    for sua in (dict(thoat_gio=2.0), dict(nghi_gio=1.0), dict(gio_vao_tu=1.0, gio_vao_den=5.0)):
        with pytest.raises(ValueError, match="cot thoi gian"):
            LU.chay_mang(khong_tg, ts_(**sua), 10000.0)
    LU.chay_mang(khong_tg, ts_(cat_lo_pip=20.0), 10000.0)           # cat lo thuan khong can gio


def test_e6_loc_gio_tren_khung_lon_hon_h1_bi_tu_choi():
    """Cua so gio vo nghia khi bar cach nhau > 1 gio (khung ngay: moi bar mo 00:00): tu choi thay vi am tham ra ket qua sai. Thoat gio /
    nghi gio van dung duoc tren khung ngay."""
    df = _df(300).iloc[::96]                                         # 15 phut x 96 = 1 ngay
    assert pd.Series(df.index).diff().dropna().median() == pd.Timedelta(days=1)
    with pytest.raises(ValueError, match="loc gio vao lenh"):
        LU.chay(df, ts_(gio_vao_tu=1.0, gio_vao_den=5.0), 10000.0)
    LU.chay(df, ts_(thoat_gio=48.0, nghi_gio=24.0), 10000.0)
    df4 = _df(300).iloc[::16]                                        # H4
    with pytest.raises(ValueError, match="loc gio vao lenh"):
        LU.chay(df4, ts_(gio_vao_tu=1.0, gio_vao_den=5.0), 10000.0)
    df1 = _df(300).iloc[::4]                                         # H1: bien (3600 giay) van duoc
    LU.chay(df1, ts_(gio_vao_tu=1.0, gio_vao_den=5.0), 10000.0)


def test_e7_chay_qua_dataframe_ghi_ly_do_va_dem_cat_gio(nhan, monkeypatch):
    """`LU.chay` (co `chuan_bi` + dispatcher + nhan C): thong ke `so_cat` / `so_gio`, bang lenh co ly do "cat" / "gio"; cung ket qua o che do
    `LUOI_NHAN=py`; chi so thoi gian co mui gio UTC ra y het khong mui gio."""
    df = _df(3000)
    ts = ts_(buoc=15.0, tp=8.0, tran_tang=6, lot=0.1, cat_lo_pip=30.0, thoat_gio=6.0, nghi_gio=1.0)
    kq = LU.chay(df, ts, 10000.0, ghi_lenh=True)
    assert kq.so_cat > 0 and kq.so_gio > 0 and kq.so_ro > 0, (kq.so_cat, kq.so_gio, kq.so_ro)
    ly_do = kq.lenh["ly_do"].value_counts().to_dict()
    assert ly_do.get("cat", 0) > 0 and ly_do.get("gio", 0) > 0 and ly_do.get("tp", 0) > 0, ly_do
    assert set(ly_do) <= {"tp", "tia", "cat", "gio", ""} and ly_do["cat"] >= kq.so_cat and ly_do["gio"] >= kq.so_gio     # moi ro dong >= 1 lenh
    # moi ro bi cat / thoat gio la ro nguyen: ly do giong nhau tren moi lenh cua ro do va gia dong bang nhau
    for (_chieu, _ro), g in kq.lenh[kq.lenh["ly_do"].isin(["cat", "gio"])].groupby(["chieu", "ro"]):
        assert g["ly_do"].nunique() == 1 and g["dong"].nunique() == 1 and g["gia_dong"].nunique() == 1
    # so ro bi cat / thoat = so nhom (chieu, ro) co ly do do
    nhom = kq.lenh[kq.lenh["ly_do"].isin(["cat", "gio"])].groupby(["chieu", "ro", "ly_do"]).ngroups
    assert nhom == kq.so_cat + kq.so_gio, (nhom, kq.so_cat, kq.so_gio)
    # tz UTC == khong tz
    kq_utc = LU.chay(df.tz_localize("UTC"), ts, 10000.0, ghi_lenh=True)
    assert kq_utc.lai_gop == kq.lai_gop and kq_utc.so_cat == kq.so_cat and kq_utc.so_gio == kq.so_gio
    assert (kq_utc.lenh["gia_mo"].to_numpy() == kq.lenh["gia_mo"].to_numpy()).all()
    # mui gio khac UTC: gio trong ngay lay theo UTC cua `.values` (khong theo dong ho dia phuong) -> y het chi so UTC khong mui gio
    kq_vn = LU.chay(df.tz_localize("UTC").tz_convert("Asia/Ho_Chi_Minh"), ts, 10000.0)
    assert kq_vn.lai_gop == kq.lai_gop and kq_vn.so_gio == kq.so_gio
    # nhan C va Python chuan: y het
    monkeypatch.setenv("LUOI_NHAN", "py")
    kp = LU.chay(df, ts, 10000.0, ghi_lenh=True)
    for ten in ("lai_rong", "lai_gop", "phi_spread", "phi_swap", "lo_treo_dinh", "so_ro", "so_lenh", "tang_max", "so_cat", "so_gio"):
        assert getattr(kp, ten) == getattr(kq, ten), ten
    pd.testing.assert_frame_equal(kp.lenh, kq.lenh, check_exact=True)
    # dich gio ca chuoi di 7 gio (cung ngay khong doi): cat lo khong doi nhung thoat gio / nghi khong dung gio => khong ve gio trong ngay
    df7 = df.copy()
    df7.index = df.index + pd.Timedelta(hours=7)
    ts_cat = ts_(buoc=15.0, tp=8.0, tran_tang=6, lot=0.1, cat_lo_pip=30.0)
    assert LU.chay(df7, ts_cat, 10000.0).lai_gop == LU.chay(df, ts_cat, 10000.0).lai_gop
    ts_h = ts_(buoc=15.0, tp=8.0, tran_tang=6, lot=0.1, thoat_gio=6.0, nghi_gio=1.0, cat_lo_pip=30.0)
    assert LU.chay(df7, ts_h, 10000.0).lai_gop == LU.chay(df, ts_h, 10000.0).lai_gop       # chi tuoi / nghi: khong phu thuoc gio trong ngay


# ================================================================== 2B. BIEN DOI tren kich ban ngau nhien (`_so_ngau_nhien_thoat`)
_TAT_HET = {k: 0.0 for k in LU.TINH_NANG_DUONG_DI}


def _tat_het(ts):
    return dataclasses.replace(ts, **_TAT_HET)


def _y_het(a, b, ten):
    """a, b = (lai, treo, tk, nhat ky) tu `_chay_mang`: BANG NHAU TUNG BIT (khong dung sai)."""
    assert np.array_equal(a[0], b[0]), (ten, "lai")
    assert np.array_equal(a[1], b[1]), (ten, "treo")
    assert a[2] == b[2], (ten, a[2], b[2])
    assert a[3] == b[3], (ten, "nhat ky lenh")


def _gan_nhau(a, b, ten):
    """Nhu `_y_het` nhung dung sai 1e-12 (phep guong / nhan doi lot: thu tu cong don co the khac o bit cuoi)."""
    assert np.asarray(a[0]) == pytest.approx(np.asarray(b[0]), rel=1e-12, abs=1e-9), (ten, "lai")
    assert np.asarray(a[1]) == pytest.approx(np.asarray(b[1]), rel=1e-12, abs=1e-9), (ten, "treo")


def _chay_tk(hi, lo, cl, sp, dem, chieu, ts, qc, tg):
    """Thong ke cua mot lan chay bang cach NHANH NHAT co san (nhan C, neu khong co thi Python) - chi de CHON kich ban, khong de so sanh."""
    r = LN.mot_ro(hi, lo, cl, sp, dem, chieu, ts, qc, [], tg)
    return r[2] if r is not None else LU.mot_ro_chuan(hi, lo, cl, sp, dem, chieu, ts, qc, [], tg)[2]


def _ca_co_su_kien(seed, so_ca, toi_thieu=3):
    """`_so_ngau_nhien_thoat` nhung chi giu kich ban co it nhat `toi_thieu` lan CAT LO + THOAT GIO: phep bien doi chay tren du lieu ma
    tinh nang that su hoat dong (khong phai chuoi gia im lang), tranh test qua de vi khong chay toi dau."""
    thay = 0
    for hi, lo, cl, sp, dem, ts, qc, tg in _so_ngau_nhien_thoat(seed, so_ca * 12):
        tk = _chay_tk(hi, lo, cl, sp, dem, 1, ts, qc, tg)
        if tk["so_cat"] + tk["so_gio"] >= toi_thieu:
            yield hi, lo, cl, sp, dem, ts, qc, tg
            thay += 1
            if thay == so_ca:
                return
    assert thay > 0, ("khong tim duoc kich ban co su kien tu hat giong", seed)


#: Cach dat tung tinh nang sao cho KHONG BAO GIO cham toi tren moi chuoi gia / gio cua test: ket qua phai y het khi khong co no.
_VO_HIEU = {
    "cat_pip_xa_vo_cuc": dict(cat_lo_pip=1e9),
    "cat_tien_xa_vo_cuc": dict(cat_lo_tien=1e12),
    "thoat_gio_toi_da": dict(thoat_gio=1e6),
    "nghi_gio_khi_khong_co_gi_de_nghi": dict(nghi_gio=7.5),
    "cua_so_ca_ngay": dict(gio_vao_tu=0.0, gio_vao_den=24.0),
    "tat_ca_cung_luc": dict(cat_lo_pip=1e9, cat_lo_tien=1e12, thoat_gio=1e6, nghi_gio=3.0, gio_vao_tu=0.0, gio_vao_den=24.0),
}


@pytest.mark.parametrize("ten", list(_VO_HIEU))
@pytest.mark.parametrize("seed", range(4))
def test_b1_tinh_nang_khong_bao_gio_cham_toi_ra_y_het_khong_co_tinh_nang(may, ten, seed):
    """Moc cat xa vo cuc, thoat gio toi da, nghi khi khong co gi de nghi, cua so [0, 24): ket qua y het TUNG BIT chay voi bon tinh nang tat
    (ca lai, treo, thong ke, nhat ky lenh). Bat loi 'tinh nang bat nhung lam hong duong chay cu': doi thu tu xu ly, tinh thua mot buoc,
    chen moc vao ranh gioi nen..."""
    for chieu in (1, -1):
        for hi, lo, cl, sp, dem, ts, qc, tg in _so_ngau_nhien_thoat(5000 + seed, 3):
            goc = _tat_het(ts)
            a = _chay_mang(may, hi, lo, cl, sp, dem, chieu, goc, qc, tg)
            b = _chay_mang(may, hi, lo, cl, sp, dem, chieu, dataclasses.replace(goc, **_VO_HIEU[ten]), qc, tg)
            _y_het(a, b, (ten, chieu))
            assert b[2]["so_cat"] == 0 and b[2]["so_gio"] == 0


@pytest.mark.parametrize("seed", range(6))
def test_b2_them_tinh_nang_vo_hieu_len_cau_hinh_dang_bat_van_y_het(may, seed):
    """Nhu b1 nhung tren cau hinh co cac tinh nang khac DANG BAT (ngau nhien): them mot tinh nang chac chan khong cham toi khong duoc doi
    gi. `nghi_gio` chi vo hieu khi KHONG co cat lo lan thoat gio nao de kich hoat nghi."""
    dem_them = 0
    for hi, lo, cl, sp, dem, ts, qc, tg in _ca_co_su_kien(5500 + seed, 5):
        a = _chay_mang(may, hi, lo, cl, sp, dem, 1, ts, qc, tg)
        them = []
        if ts.cat_lo_pip == 0:
            them.append(dict(cat_lo_pip=1e9))
        if ts.cat_lo_tien == 0:
            them.append(dict(cat_lo_tien=1e12))
        if ts.thoat_gio == 0:
            them.append(dict(thoat_gio=1e6))
        if ts.gio_vao_tu == ts.gio_vao_den:
            them.append(dict(gio_vao_tu=0.0, gio_vao_den=24.0))
        if ts.cat_lo_pip == 0 and ts.cat_lo_tien == 0 and ts.thoat_gio == 0 and ts.nghi_gio == 0:
            them.append(dict(nghi_gio=5.0))
        for kw in them:
            b = _chay_mang(may, hi, lo, cl, sp, dem, 1, dataclasses.replace(ts, **kw), qc, tg)
            _y_het(a, b, (kw, ts))
            dem_them += 1
    assert dem_them > 0


@pytest.mark.parametrize("ngay", [1, 3, 365])
@pytest.mark.parametrize("seed", range(4))
def test_b3_dich_ca_cot_thoi_gian_di_so_nguyen_ngay_khong_doi_gi(may, ngay, seed):
    """Cua so gio, thoat gio va nghi chi phu thuoc gio trong ngay (mod 86400) va HIEU hai moc: dich moi moc di tron ngay ra y het. Bat loi
    tinh gio trong ngay theo moc epoch / tuan thay vi mod ngay, hoac dung gia tri tuyet doi cua `tg` thay vi hieu."""
    for hi, lo, cl, sp, dem, ts, qc, tg in _ca_co_su_kien(6000 + seed, 4):
        a = _chay_mang(may, hi, lo, cl, sp, dem, 1, ts, qc, tg)
        b = _chay_mang(may, hi, lo, cl, sp, dem, 1, ts, qc, np.ascontiguousarray(tg + 86400.0 * ngay))
        _y_het(a, b, (ngay, ts))


@pytest.mark.parametrize("seed", range(8))
def test_b4_ro_ban_bang_ro_mua_tren_gia_dao_dau_ke_ca_tinh_nang_moi(may, seed):
    """Guong (nhu `test_luoi_duong_di.test_ro_ban_bang_ro_mua_tren_gia_dao_dau`) nhung cau hinh co cat lo / thoat gio / nghi / loc gio:
    `chieu=-1` tren (hi, lo, cl) === `chieu=+1` tren (-lo, -hi, -cl). Gio khong phu thuoc gia nen cot thoi gian giu nguyen."""
    rng = np.random.default_rng(7000 + seed)
    for hi, lo, cl, sp, dem, ts, qc, tg in _ca_co_su_kien(7000 + seed, 3):
        hi, lo, cl = _bo_doji(rng, hi, lo, cl)
        dem = np.zeros(len(cl))
        lai_b, treo_b, tk_b, ev_b = _chay_mang(may, hi, lo, cl, sp, dem, -1, ts, qc, tg)
        lai_m, treo_m, tk_m, ev_m = _chay_mang(may, -lo, -hi, -cl, sp, dem, 1, ts, qc, tg)
        assert lai_b == pytest.approx(lai_m, rel=1e-12, abs=1e-9) and treo_b == pytest.approx(treo_m, rel=1e-12, abs=1e-9), ts
        for k in tk_b:
            assert tk_b[k] == pytest.approx(tk_m[k], rel=1e-12, abs=1e-9), (k, tk_b, tk_m)
        assert len(ev_b) == len(ev_m)
        for a, b in zip(ev_b, ev_m):
            assert a[:2] == b[:2], (a, b)
            assert a[2] == pytest.approx(-b[2], rel=1e-12, abs=1e-12), (a, b)
            assert a[3:] == b[3:], (a, b)                          # lot, ma lenh, tang, ro (hoac ma lenh, ly do cat / gio / tp) y het


@pytest.mark.parametrize("seed", range(8))
def test_b5_nhan_doi_lot_ra_dung_gap_doi_ke_ca_tinh_nang_moi(may, seed):
    """Lot x2: moc cat theo TIEN quy theo lot (khoang cat tinh theo gia khong doi) nen gia lenh, thoi diem cat, thoat gio, nghi, cua so gio
    KHONG doi; tien gap doi."""
    for hi, lo, cl, sp, dem, ts, qc, tg in _ca_co_su_kien(8000 + seed, 3):
        a = _chay_mang(may, hi, lo, cl, sp, dem, 1, ts, qc, tg)
        b = _chay_mang(may, hi, lo, cl, sp, dem, 1, dataclasses.replace(ts, lot=ts.lot * 2.0), qc, tg)
        assert b[0] == pytest.approx(2.0 * a[0], rel=1e-12, abs=1e-9) and b[1] == pytest.approx(2.0 * a[1], rel=1e-12, abs=1e-9), ts
        for k in ("so_ro", "so_lenh", "tang_max", "so_cap", "con_mo", "so_cat", "so_gio"):
            assert a[2][k] == b[2][k], (k, ts, a[2], b[2])
        for k in ("lai_gop", "phi_spread", "phi_swap"):
            assert b[2][k] == pytest.approx(2.0 * a[2][k], rel=1e-12, abs=1e-9)
        assert len(a[3]) == len(b[3])
        for x, y in zip(a[3], b[3]):
            assert x[0] == y[0] and x[1] == y[1] and x[2] == pytest.approx(y[2], rel=1e-12, abs=1e-12), (x, y)
            if x[0] == "mo":
                assert y[3] == pytest.approx(2.0 * x[3], rel=1e-12) and x[4:] == y[4:], (x, y)
            else:
                assert x[3:] == y[3:], (x, y)


def _tach_ba(hi, lo, cl, sp, tg):
    """`test_luoi_duong_di.tach_theo_duong` + cot thoi gian: ba nen doan cua nen i DEU mang gio mo cua nen i (gio khong doi giua chung)."""
    from test_luoi_duong_di import tach_theo_duong
    hi2, lo2, cl2, sp2 = tach_theo_duong(hi, lo, cl, sp)
    tg2 = np.concatenate([[tg[0]], np.repeat(tg[1:], 3)])
    return hi2, lo2, cl2, sp2, np.ascontiguousarray(tg2)


@pytest.mark.parametrize("seed", range(10))
def test_b6_tach_moi_nen_thanh_ba_doan_theo_duong_di_ra_y_het_ke_ca_tinh_nang_moi(may, seed):
    """NHAT QUAN DO PHAN GIAI (nhu `test_tach_moi_nen_thanh_ba_doan_theo_duong_di_ra_y_het`) voi cat lo / thoat gio / nghi / loc gio: ba nen
    doan cung gio mo cua nen goc -> cung lenh, cung gia, cung lai o cuoi nen. Neu thoat gio / cua so / nghi dem theo SO NEN thay vi theo gio,
    hay mo ro lai o dau doan thay vi dau nen, phep tach khong con bang nhau."""
    for hi, lo, cl, sp, dem, ts, qc, tg in _ca_co_su_kien(9000 + seed, 3):
        ts = dataclasses.replace(ts, cap_moi_bar=999)
        dem = np.zeros(len(cl))
        hi2, lo2, cl2, sp2, tg2 = _tach_ba(hi, lo, cl, sp, tg)
        lai1, treo1, tk1, ev1 = _chay_mang(may, hi, lo, cl, sp, dem, 1, ts, qc, tg)
        lai2, treo2, tk2, ev2 = _chay_mang(may, hi2, lo2, cl2, sp2, np.zeros(len(cl2)), 1, ts, qc, tg2)
        n = len(cl)
        cuoi = [0] + [3 * i for i in range(1, n)]
        assert lai2[cuoi] == pytest.approx(lai1, rel=1e-12, abs=1e-9), ts
        for k in ("so_ro", "so_lenh", "tang_max", "so_cap", "con_mo", "so_cat", "so_gio"):
            assert tk1[k] == tk2[k], (k, ts, tk1, tk2)
        for k in ("lai_gop", "phi_spread"):
            assert tk1[k] == pytest.approx(tk2[k], rel=1e-12, abs=1e-9), (k, tk1, tk2)
        assert len(ev1) == len(ev2), (len(ev1), len(ev2), ts)
        for a, b in zip(ev1, ev2):
            assert a[0] == b[0] and a[1] == _bar_goc_(b[1]), (a, b, ts)
            assert a[2] == pytest.approx(b[2], rel=1e-12, abs=1e-12), (a, b)
            assert a[3:] == pytest.approx(b[3:]) if a[0] == "mo" else a[3:] == b[3:], (a, b)


def _bar_goc_(j):
    return 0 if j == 0 else (j - 1) // 3 + 1


@pytest.mark.parametrize("seed", range(8))
def test_b7_nghi_vo_han_dong_bang_sau_lan_cat_hoac_thoat_gio_dau_tien(may, seed):
    """`nghi_gio` = 1.000.000 gio: den lan cat lo / thoat gio DAU TIEN moi thu y het cau hinh nghi = 0 (nghi chua duoc dung toi); sau do KHONG
    mo ro nao nua - lai khong doi, treo = 0, khong them lenh. Tinh nang khac (cua so, tia) khong lam ro nao mo lai."""
    thay = 0
    for hi, lo, cl, sp, dem, ts, qc, tg in _ca_co_su_kien(9500 + seed, 5, toi_thieu=1):
        if ts.cat_lo_pip == 0 and ts.cat_lo_tien == 0 and ts.thoat_gio == 0:
            continue
        a = _chay_mang(may, hi, lo, cl, sp, dem, 1, dataclasses.replace(ts, nghi_gio=0.0), qc, tg)
        b = _chay_mang(may, hi, lo, cl, sp, dem, 1, dataclasses.replace(ts, nghi_gio=1e6), qc, tg)
        ev_a = a[3]
        k0 = next((j for j, e in enumerate(ev_a) if e[0] == "dong" and e[4] in ("cat", "gio")), None)
        if k0 is None:
            _y_het(a, b, ts)
            continue
        thay += 1
        bar_c, ly = ev_a[k0][1], ev_a[k0][4]
        k1 = k0
        while k1 + 1 < len(ev_a) and ev_a[k1 + 1][0] == "dong" and ev_a[k1 + 1][1] == bar_c and ev_a[k1 + 1][4] == ly:
            k1 += 1
        assert b[3] == ev_a[:k1 + 1], (ts, "nhat ky phai dung o het nhom dong dau tien")
        assert np.array_equal(b[0][:bar_c], a[0][:bar_c]) and np.array_equal(b[1][:bar_c], a[1][:bar_c])
        assert (b[0][bar_c:] == b[0][bar_c]).all() and (b[1][bar_c + 1:] == 0.0).all(), ts
        assert b[2]["con_mo"] == 0
    assert thay > 0



# ================================================================== 2C. PHAT LAI NHAT KY LENH (`PhatLai`)
class PhatLai:
    """TU TINH LAI luat cua bon tinh nang moi tu CHINH nhat ky lenh, KHONG goi lai code engine (chi dung `LU.cau_hinh_gio` - dinh nghia duy nhat
    cua phep lam tron gio -> giay): neu engine dung thi moi dieu duoi day phai dung; khong can biet engine tinh bang cach nao.

      - cau truc: ma lenh tang dan, mot ro song tai mot luc, cac nhom dong dung nhom (TP / cat / gio dong HET ro, tia dong lenh dau + cuoi);
      - CAT LO: gia dong = trung binh co trong so cua ro dang song tru khoang cat (gan hon trong pip / tien) VA gia cham toi moc do trong bar;
        hoac nhay gia: bang gia mo bar khi moc cat da nam sau gia mo; bar khong co su kien thi gia KHONG cham moc cat;
      - THOAT GIO: dong het dung o bar dau tien cach gio mo ro >= thoat_gio, o GIA MO bar, dung dau bar; khong ro nao song qua han;
      - NGHI + CUA SO GIO: ro moi chi mo khi het nghi va gio mo bar trong cua so; sau khi ro het (cat / gio / tia / tp khong cho lui) ma dang
        duoc phep thi ro moi mo NGAY o gia dong, con khong thi o gia mo cua bar dau tien duoc phep (khong bo, khong tre);
      - KE TOAN: lai tung bar = lai chot - spread - qua dem tinh lai tu nhat ky; thong ke khop; lo noi (treo) >= lo noi cuoi bar, va BANG lo
        noi o gia cuc tri khi bar khong co su kien.
    Khong kiem: toa do chinh xac cua tang / tp / tia (da co tay tinh + doi chieu EA tung tick)."""

    def __init__(self, hi, lo, cl, sp, dem, chieu, ts, qc, tg, ten=""):
        self.hi, self.lo, self.cl, self.sp, self.dem, self.tg = hi, lo, cl, sp, dem, tg
        self.n = len(cl)
        self.s = chieu
        self.ts, self.ten = ts, ten
        self.pip, self.hop = qc.pip, qc.hop_dong
        self.eps = LU.EPS_CHAM_PIP * self.pip
        self.tol = 1e-9 * self.pip
        self.thoat_s, self.nghi_s, self.tu_s, self.den_s = LU.cau_hinh_gio(ts)
        self.loc_gio = self.tu_s != self.den_s
        self.ty_le = qc.phi_nam_mua if chieu > 0 else qc.phi_nam_ban
        self.nguong_cat = ts.cat_lo_tien * (ts.lot / 0.01)
        self.live: dict = {}                                    # ma lenh -> (gia, lot), theo thu tu mo
        self.nghi_den = -math.inf
        self.pend = (0, float(cl[0]), "dau")                    # (bar, gia, ly do) ro dang rong, mong mo lai ngay neu duoc phep; ("cho",) = TP co cho lui
        self.ro_hien, self.t_mo, self.tang_ke, self.max_id = -1, None, 0, -1
        self.so_mo = self.so_tp = self.so_tia = self.so_cat = self.so_gio = 0
        self.tang_max = 0
        self.gross = self.spread = self.swap = 0.0
        self.so_cat_pip_tien = [0, 0]                           # [cat o moc, cat do nhay gia]

    # ---- tien ich
    def tai(self, msg, *a):
        raise AssertionError("[%s] %s" % (self.ten, (msg % a) if a else msg))

    def gia_mo(self, i):
        return min(max(self.cl[i - 1], self.lo[i]), self.hi[i])

    def cuc_tri(self, i):
        return self.lo[i] if self.s > 0 else self.hi[i]

    def cho_phep(self, i):
        t = self.tg[i]
        if t < self.nghi_den:
            return False
        if self.loc_gio:
            sec = math.fmod(t, 86400.0)
            if self.tu_s < self.den_s:
                return self.tu_s <= sec < self.den_s
            return sec >= self.tu_s or sec < self.den_s
        return True

    def lo_noi(self, gia):
        return sum(max(0.0, self.s * (g - gia)) * lt for g, lt in self.live.values()) * self.hop

    def moc_cat(self):
        tong = sum(lt for _g, lt in self.live.values())
        tb = sum(lt * g for g, lt in self.live.values()) / tong
        kc = math.inf
        if self.ts.cat_lo_pip > 0:
            kc = self.ts.cat_lo_pip * self.pip
        if self.ts.cat_lo_tien > 0:
            kc = min(kc, self.nguong_cat / (self.hop * tong))
        return tb - self.s * kc

    def phai_mo_lai(self, i):
        """Ro rong, khong phai TP cho lui, bar `i` cho phep mo -> ro moi PHAI mo ngay."""
        return (not self.live) and self.pend is not None and self.pend != ("cho",) and self.cho_phep(i)

    # ---- su kien
    def _mo(self, i, e):
        _t, _b, gia, lot, ma, tang, ro = e
        if ma != self.max_id + 1:
            self.tai("ma lenh %r sau %r", ma, self.max_id)
        self.max_id = ma
        if i >= 1 and not (self.lo[i] - self.tol <= gia <= self.hi[i] + self.tol):
            self.tai("gia mo %r ngoai [low, high] cua bar %d", gia, i)
        if tang == 0:
            if self.live:
                self.tai("mo ro moi (bar %d) khi ro cu con song %s", i, list(self.live))
            if ro != self.ro_hien + 1:
                self.tai("ma ro %r sau %r", ro, self.ro_hien)
            if not self.cho_phep(i):
                self.tai("mo ro moi o bar %d ngoai cua so / dang nghi (nghi_den=%r, tg=%r)", i, self.nghi_den, self.tg[i])
            if self.pend is not None and self.pend != ("cho",):
                bc, gc, ly = self.pend
                mong = gc if bc == i else self.gia_mo(i)
                if gia != mong:
                    self.tai("sau '%s' o bar %d, ro moi o bar %d phai mo o %r, nhan %r", ly, bc, i, mong, gia)
            self.pend = None
            self.ro_hien, self.t_mo, self.tang_ke = ro, self.tg[i], 1
        else:
            if not self.live or tang != self.tang_ke:
                self.tai("tang %r khong khop (mong %r, dang song %s)", tang, self.tang_ke, list(self.live))
            if self.ts.cat_lo_pip > 0 or self.ts.cat_lo_tien > 0:                 # them tang TRUOC cat chi khi moc cat nam SAU gia them (hoa -> cat truoc)
                mc = self.moc_cat()
                if not self.s * (mc - gia) < -self.tol:
                    self.tai("them tang o %r (bar %d) khi moc cat %r khong nam sau gia them: cat phai khop truoc (hoac cung luc -> cat truoc)",
                             gia, i, mc)
            self.tang_ke += 1
        self.live[ma] = (gia, lot)
        self.spread += self.sp[i] * lot * self.hop
        self.so_mo += 1
        self.tang_max = max(self.tang_max, len(self.live))

    def _dong(self, i, evs, p):
        gia, ly = evs[p][2], evs[p][4]
        q, ids = p, []
        while q < len(evs) and evs[q][0] == "dong" and evs[q][2] == gia and evs[q][4] == ly:
            ids.append(evs[q][3])
            q += 1
        if i >= 1 and not (self.lo[i] - self.tol <= gia <= self.hi[i] + self.tol):
            self.tai("gia dong %r ngoai [low, high] cua bar %d", gia, i)
        if ly == "tia":
            if len(ids) % 2:
                self.tai("tia dong so le lenh: %s", ids)
            for a in range(0, len(ids), 2):
                ma = list(self.live)
                if len(ma) < 2 or ids[a:a + 2] != [ma[0], ma[-1]]:
                    self.tai("tia phai dong lenh dau + cuoi cua ro %s, nhan %s", ma, ids[a:a + 2])
                for k in ids[a:a + 2]:
                    g, lt = self.live.pop(k)
                    self.gross += self.s * (gia - g) * lt * self.hop
                self.so_tia += 1
        else:
            if sorted(ids) != sorted(self.live):
                self.tai("'%s' o bar %d phai dong HET ro song %s, nhan %s", ly, i, list(self.live), ids)
            if ly == "cat":
                self._kiem_cat(i, gia)
            elif ly == "gio":
                self._kiem_gio(i, gia, p)
            for k in ids:
                g, lt = self.live.pop(k)
                self.gross += self.s * (gia - g) * lt * self.hop
            if ly == "tp":
                self.so_tp += 1
            elif ly == "cat":
                self.so_cat += 1
            elif ly == "gio":
                self.so_gio += 1
            else:
                self.tai("ly do dong la %r", ly)
            if ly in ("cat", "gio") and self.nghi_s > 0:
                self.nghi_den = self.tg[i] + self.nghi_s
        if not self.live:
            self.pend = ("cho",) if (ly == "tp" and self.ts.cho_lui > 0) else (i, gia, ly)
        return q

    def _kiem_cat(self, i, gia):
        if self.ts.cat_lo_pip <= 0 and self.ts.cat_lo_tien <= 0:
            self.tai("co lenh cat khi cat lo tat")
        mc = self.moc_cat()
        o = self.gia_mo(i) if i >= 1 else None
        if abs(gia - mc) <= self.tol:
            if self.s * (mc - self.cuc_tri(i)) < -self.eps - self.tol:
                self.tai("cat o %r nhung gia khong cham moc cat: cuc tri bar %d la %r", gia, i, self.cuc_tri(i))
            self.so_cat_pip_tien[0] += 1
        elif o is not None and gia == o and self.s * (mc - o) > 0:
            self.so_cat_pip_tien[1] += 1                         # nhay gia: moc cat da nam sau gia mo
        else:
            self.tai("gia cat %r khong phai moc cat %r (cung khong phai nhay gia o gia mo %r), bar %d", gia, mc, o, i)

    def _kiem_gio(self, i, gia, p):
        if not (i >= 1 and self.thoat_s > 0 and self.live and self.tg[i] - self.t_mo >= self.thoat_s):
            self.tai("thoat gio o bar %d khi chua den han (thoat_s=%r, t_mo=%r, tg=%r)", i, self.thoat_s, self.t_mo, self.tg[i])
        if p != 0 or gia != self.gia_mo(i):
            self.tai("thoat gio phai la su kien DAU bar %d o GIA MO %r (nhan vi tri %d, gia %r)", i, self.gia_mo(i), p, gia)

    # ---- tung bar + cuoi
    def chay(self, ev, lai, treo, tk):
        n = self.n
        theo_bar = [[] for _ in range(n)]
        for e in ev:
            theo_bar[e[1]].append(e)
        for i in range(n):
            evs = theo_bar[i]
            p = 0
            if i >= 1 and self.live and self.thoat_s > 0 and self.tg[i] - self.t_mo >= self.thoat_s:
                if not (evs and evs[0][0] == "dong" and evs[0][4] == "gio"):
                    self.tai("bar %d: ro mo luc %r da den han thoat gio %r giay nhung khong thoat", i, self.t_mo, self.thoat_s)
            while True:
                if self.phai_mo_lai(i) and not (p < len(evs) and evs[p][0] == "mo" and evs[p][5] == 0):
                    self.tai("bar %d: ro rong, duoc phep mo (%r) nhung khong mo lai", i, self.pend)
                if p >= len(evs):
                    break
                if evs[p][0] == "mo":
                    self._mo(i, evs[p])
                    p += 1
                else:
                    p = self._dong(i, evs, p)
            self._het_bar(i, evs, lai, treo)
        self._ket(tk)

    def _het_bar(self, i, evs, lai, treo):
        if i >= 1 and self.live and self.dem[i] != 0.0:
            tl = sum(lt for _g, lt in self.live.values())
            self.swap += tl * self.hop * self.ty_le * self.dem[i] / 365.0 * self.cl[i]
        mong = -self.spread if i == 0 else self.gross - self.spread - self.swap
        if abs(lai[i] - mong) > 1e-9 * (1.0 + abs(mong)):
            self.tai("lai bar %d: engine %r, tinh lai tu nhat ky %r", i, lai[i], mong)
        if i == 0:
            if treo[0] != 0.0:
                self.tai("treo[0] phai bang 0, nhan %r", treo[0])
            return
        cuoi = self.lo_noi(self.cl[i])
        if treo[i] < cuoi - 1e-9 * (1.0 + abs(cuoi)):
            self.tai("treo bar %d = %r < lo noi luc het bar %r", i, treo[i], cuoi)
        if not evs:
            if self.live:
                cuc = self.lo_noi(self.cuc_tri(i))
                if abs(treo[i] - cuc) > 1e-9 * (1.0 + abs(cuc)):
                    self.tai("bar %d khong su kien: treo %r, lo noi o cuc tri %r", i, treo[i], cuc)
                if self.ts.cat_lo_pip > 0 or self.ts.cat_lo_tien > 0:
                    mc = self.moc_cat()
                    if not self.s * (mc - self.cuc_tri(i)) < -0.5 * self.eps:
                        self.tai("bar %d khong co su kien nhung gia %r da cham moc cat %r", i, self.cuc_tri(i), mc)
            elif treo[i] != 0.0:
                self.tai("bar %d ro rong khong su kien: treo %r != 0", i, treo[i])

    def _ket(self, tk):
        def gan(a, b):
            return abs(a - b) <= 1e-9 * (1.0 + abs(b))
        for ten, v in (("lai_gop", self.gross), ("phi_spread", self.spread), ("phi_swap", self.swap)):
            if not gan(tk[ten], v):
                self.tai("tk[%s] = %r, tinh lai tu nhat ky %r", ten, tk[ten], v)
        for ten, v in (("so_lenh", self.so_mo), ("so_ro", self.so_tp), ("so_cap", self.so_tia), ("so_cat", self.so_cat),
                       ("so_gio", self.so_gio), ("con_mo", len(self.live)), ("tang_max", self.tang_max)):
            if tk[ten] != v:
                self.tai("tk[%s] = %r, tinh lai tu nhat ky %r", ten, tk[ten], v)


def _phat_lai(may, hi, lo, cl, sp, dem, chieu, ts, qc, tg, ten=""):
    lai, treo, tk, ev = _chay_mang(may, hi, lo, cl, sp, dem, chieu, ts, qc, tg)
    pl = PhatLai(hi, lo, cl, sp, dem, chieu, ts, qc, tg, ten)
    pl.chay(ev, lai, treo, tk)
    return pl, (lai, treo, tk, ev)


@pytest.mark.parametrize("seed", range(10))
def test_r1_phat_lai_nhat_ky_khop_luat_tren_kich_ban_ngau_nhien(may, seed):
    """Moi kich ban x moi chieu: nhat ky lenh cua engine thoa TOAN BO luat cat / thoat gio / nghi / loc gio / ke toan (xem `PhatLai`)."""
    tong = {"cat": 0, "gio": 0, "nhay": 0}
    for j, (hi, lo, cl, sp, dem, ts, qc, tg) in enumerate(_so_ngau_nhien_thoat(11000 + seed, 6)):
        for chieu in (1, -1):
            pl, _ = _phat_lai(may, hi, lo, cl, sp, dem, chieu, ts, qc, tg, "seed %d ca %d chieu %d %s" % (seed, j, chieu, ts))
            tong["cat"] += pl.so_cat
            tong["gio"] += pl.so_gio
            tong["nhay"] += pl.so_cat_pip_tien[1]
    assert tong["cat"] + tong["gio"] > 0, tong


def test_r2_phat_lai_phu_het_bon_tinh_nang_khong_phai_phep_thu_rong(nhan):
    """Bao ve chong 'test rong': tren 12 hat giong x 6 kich ban x 2 chieu, nhat ky co du cac loai su kien ma `PhatLai` kiem: cat o moc, cat do
    nhay gia, thoat gio, nghi chan mo lai, cua so chan mo lai (so voi chay khong co no)."""
    cat = nhay = gio = nghi_chan = cua_so_chan = 0
    for seed in range(12):
        for hi, lo, cl, sp, dem, ts, qc, tg in _so_ngau_nhien_thoat(11000 + seed, 6):
            for chieu in (1, -1):
                pl, (_l, _t, tk, ev) = _phat_lai("c", hi, lo, cl, sp, dem, chieu, ts, qc, tg)
                cat += pl.so_cat_pip_tien[0]
                nhay += pl.so_cat_pip_tien[1]
                gio += pl.so_gio
                if ts.nghi_gio > 0:
                    nghi_chan += _chay_mang("c", hi, lo, cl, sp, dem, chieu, dataclasses.replace(ts, nghi_gio=0.0), qc, tg)[3] != ev
                if ts.gio_vao_tu != ts.gio_vao_den:
                    cua_so_chan += _chay_mang("c", hi, lo, cl, sp, dem, chieu, dataclasses.replace(ts, gio_vao_tu=0.0, gio_vao_den=0.0), qc, tg)[3] != ev
    assert cat >= 1000 and gio >= 1000 and nghi_chan >= 10 and cua_so_chan >= 10, (cat, nhay, gio, nghi_chan, cua_so_chan)   # do thuc: 3867 / 7866 / 32 / 33
    assert nhay == 0, "kich ban ngau nhien lien tuc (moi bar bao gom close bar truoc) khong the co nhay gia: %d" % nhay


@pytest.mark.cham
def test_r3_phat_lai_tren_nhieu_hat_giong_nhan_c(nhan):
    """Mo rong r1 ra 60 hat giong x 8 kich ban x 2 chieu tren nhan C (nhanh)."""
    tong = 0
    for seed in range(60):
        for j, (hi, lo, cl, sp, dem, ts, qc, tg) in enumerate(_so_ngau_nhien_thoat(12000 + seed, 8)):
            for chieu in (1, -1):
                pl, _ = _phat_lai("c", hi, lo, cl, sp, dem, chieu, ts, qc, tg, "seed %d ca %d chieu %d %s" % (seed, j, chieu, ts))
                tong += pl.so_cat + pl.so_gio
    assert tong > 100


def _con_khe_gia(hi, lo, cl, ts, qc, rng):
    """Chen KHE GIA vao kich ban: dich ca duoi chuoi (bar j tro di) mot doan d. Hinh dang tung bar giu nguyen nhung `clamp(close_truoc, low, high)`
    khong con la close_truoc (kich ban goc luon bao gom close bar truoc nen khong bao gio co khe). d lay theo buoc luoi / khoang cat de co khi
    vuot ca moc cat cua ro dang mo; dau ngau nhien nen mot nua so khe bat loi cho chieu mua, nua con lai cho chieu ban."""
    hi, lo, cl = hi.copy(), lo.copy(), cl.copy()
    n = len(cl)
    k = min(n - 1, max(4, n // 40))
    don_vi = max(ts.buoc, ts.cat_lo_pip) * qc.pip
    for j in sorted(int(x) for x in rng.choice(np.arange(1, n), size=k, replace=False)):
        d = float(rng.choice([-1.0, 1.0]) * rng.uniform(0.3, 4.0) * don_vi)
        hi[j:] += d
        lo[j:] += d
        cl[j:] += d
    return hi, lo, cl


@pytest.mark.parametrize("seed", range(8))
def test_r4_phat_lai_khi_gia_co_khe_nhay_giua_hai_bar(may, seed):
    """Nhu r1 nhung gia co khe nhay: `PhatLai` kiem cat o GIA MO bar khi moc cat da nam sau gia mo, thoat gio / mo lai o gia mo da kep, v.v."""
    rng_k = np.random.default_rng(seed)
    for j, (hi, lo, cl, sp, dem, ts, qc, tg) in enumerate(_so_ngau_nhien_thoat(13000 + seed, 6)):
        hi, lo, cl = _con_khe_gia(hi, lo, cl, ts, qc, rng_k)
        for chieu in (1, -1):
            _phat_lai(may, hi, lo, cl, sp, dem, chieu, ts, qc, tg, "khe seed %d ca %d chieu %d %s" % (seed, j, chieu, ts))


def test_r5_khe_gia_thuc_su_sinh_ra_cat_do_nhay_gia_va_thoat_gio_o_gia_mo_kep(nhan):
    """Bao ve chong 'test rong' cho r4: tren 12 hat giong x 6 kich ban x 2 chieu, `PhatLai` phai tha thay cat do NHAY GIA (gia cat = gia mo bar,
    moc cat nam sau gia mo) va thoat gio o gia mo bar da kep vao [low, high] (khac close bar truoc)."""
    nhay = gio_kep = 0
    for seed in range(12):
        rng_k = np.random.default_rng(seed)
        for hi, lo, cl, sp, dem, ts, qc, tg in _so_ngau_nhien_thoat(13000 + seed, 6):
            hi, lo, cl = _con_khe_gia(hi, lo, cl, ts, qc, rng_k)
            for chieu in (1, -1):
                pl, (_l, _t, _k, ev) = _phat_lai("c", hi, lo, cl, sp, dem, chieu, ts, qc, tg)
                nhay += pl.so_cat_pip_tien[1]
                gio_kep += sum(1 for e in ev if e[0] == "dong" and e[4] == "gio" and e[2] != cl[e[1] - 1])
    assert nhay >= 200 and gio_kep >= 60, (nhay, gio_kep)                                 # do thuc: 710 / 217
