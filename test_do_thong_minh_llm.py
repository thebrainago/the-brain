# -*- coding: utf-8 -*-
"""Test cho nhan/do_thong_minh.py - chi dung thu vien chuan + nhan.*"""
import math

import numpy as np

from nhan import do_thong_minh as DM
from nhan import luoi as LU


def _ts(**kw):
    """ThamSo mau: chi ghi de truong can thiet, con lai lay mac dinh cua luoi.ThamSo."""
    return LU.ThamSo(**kw)


# ------------------------------------------------------------------ bien_the
def test_bien_the_nhan_khoang_cach_va_so_tang():
    goc = _ts(buoc=10.0, tp=20.0, cho_lui=5.0, bien_cap=3.0, buoc_tran=4.0, tran_tang=10)
    ts = DM.bien_the(goc, 2.0, 1.5, 0.5)
    assert ts.buoc == 20.0
    assert ts.tp == 20.0 * 2.0 * 1.5
    assert ts.cho_lui == 10.0
    assert ts.bien_cap == 6.0
    assert ts.buoc_tran == 8.0
    assert ts.tran_tang == 5  # round(10 * 0.5) = 5


def test_bien_the_tran_tang_toi_thieu_2_va_toi_da_TOI_DA_TANG():
    goc = _ts(buoc=10.0, tp=20.0, tran_tang=3)
    assert DM.bien_the(goc, 1.0, 1.0, 0.01).tran_tang == 2
    goc2 = _ts(buoc=10.0, tp=20.0, tran_tang=DM.DT.TOI_DA_TANG)
    assert DM.bien_the(goc2, 1.0, 1.0, 100.0).tran_tang == DM.DT.TOI_DA_TANG


def test_bien_the_he_so_khong_hop_le_thi_loi():
    goc = _ts(buoc=10.0, tp=20.0)
    for f in (0.0, -1.0, float("nan"), float("inf")):
        try:
            DM.bien_the(goc, f, 1.0, 1.0)
        except ValueError:
            pass
        else:
            raise AssertionError("he so %r phai gay ValueError" % (f,))


# ------------------------------------------------------------------ ap_san
def test_ap_san_nang_len_san_va_bo_qua_san_khong_duong():
    goc = _ts(buoc=1.0, tp=2.0)
    ts = DM.ap_san(goc, san_buoc=5.0, san_tp=3.0)
    assert ts.buoc == 5.0
    assert ts.tp == 3.0
    # san <= 0 = khong ap
    ts2 = DM.ap_san(goc, san_buoc=0.0, san_tp=-1.0)
    assert ts2.buoc == 1.0 and ts2.tp == 2.0
    # khong doi gi thi tra ve chinh doi tuong cu
    assert DM.ap_san(goc) is goc


def test_san_tu_thi_truong_la_max_cua_hai_hang_so():
    class TT:
        A = 0.0001
        C = 0.0002
        pip = 0.0001

    tt = TT()
    ky_vong = max(DM.DT.NGUONG_PHAN_GIAI * tt.A, DM.DT.SAN_CHI_PHI * tt.C) / tt.pip
    assert DM.san_tu_thi_truong(tt) == ky_vong


# ------------------------------------------------------------------ dung_luoi
def test_dung_luoi_kich_thuoc_va_so_o():
    goc = _ts(buoc=10.0, tp=20.0, tran_tang=5)
    lc = DM.dung_luoi(goc, he_buoc=(1.0, 2.0), he_tp=(1.0,), he_tam=(1.0, 2.0))
    assert lc.kich_thuoc() == (2, 1, 2)
    assert len(lc.cac_o()) == 4
    # o dau tien la chinh goc (he so 1,1,1)
    assert lc.o[0][0][0].buoc == goc.buoc
    assert lc.o[1][0][1].buoc == goc.buoc * 2.0


# ------------------------------------------------------------------ cao_nguyen_mang
def test_cao_nguyen_mang_giu_doi_rong_va_hat_dinh_nhon():
    # doi rong phang: moi o = 5
    d = np.full((3, 3, 3), 5.0)
    cn = DM.cao_nguyen_mang(d)
    assert np.allclose(cn, 5.0)
    # dinh nhon o giua: trung vi cua {9, 0, 0, 0, 0, 0, 0} = 0
    d2 = np.zeros((3, 3, 3))
    d2[1, 1, 1] = 9.0
    cn2 = DM.cao_nguyen_mang(d2)
    assert cn2[1, 1, 1] == 0.0


def test_cao_nguyen_mang_bo_qua_o_nan():
    d = np.full((3, 3, 3), 4.0)
    d[1, 1, 1] = np.nan
    cn = DM.cao_nguyen_mang(d)
    assert math.isnan(cn[1, 1, 1])
    # o ke voi NaN khong bi keo xuong: trung vi cua {4,4,4,4,4,4} = 4
    assert cn[0, 1, 1] == 4.0


def test_cao_nguyen_mang_can_mang_3_truc():
    try:
        DM.cao_nguyen_mang(np.zeros((2, 2)))
    except ValueError:
        pass
    else:
        raise AssertionError("mang 2 truc phai gay ValueError")


# ------------------------------------------------------------------ ke_hoach
def test_ke_hoach_so_phep_thu_toi_da_va_hash_on_dinh():
    kh = DM.ke_hoach(4, so_tot=2, so_vong=1, he_buoc=(1.0, 2.0), he_tp=(1.0,), he_tam=(1.0,))
    # 4 ung vien + 2 * (2*1*1) + 1 * 27
    assert kh["so_phep_thu_toi_da"] == 4 + 2 * 2 + 27
    assert isinstance(kh["plan_hash"], str) and len(kh["plan_hash"]) == 16
    kh2 = DM.ke_hoach(4, so_tot=2, so_vong=1, he_buoc=(1.0, 2.0), he_tp=(1.0,), he_tam=(1.0,))
    assert kh2["plan_hash"] == kh["plan_hash"]
    kh3 = DM.ke_hoach(5, so_tot=2, so_vong=1, he_buoc=(1.0, 2.0), he_tp=(1.0,), he_tam=(1.0,))
    assert kh3["plan_hash"] != kh["plan_hash"]


# ------------------------------------------------------------------ tim
def _danh_gia_theo_buoc(muc_tieu: float):
    """Ham danh gia gia: diem = -|buoc - muc_tieu|, de kiem tra tim dung huong."""
    def f(cac):
        return [-abs(ts.buoc - muc_tieu) for ts in cac]
    return f


def test_tim_rong_thi_loi():
    try:
        DM.tim([], lambda cac: [0.0] * len(cac))
    except ValueError:
        pass
    else:
        raise AssertionError("ung_vien rong phai gay ValueError")


def test_tim_tra_ve_ung_vien_khi_ngan_sach_chi_du_cho_buoc_0():
    uv = [_ts(buoc=10.0, tp=20.0, tran_tang=5), _ts(buoc=30.0, tp=60.0, tran_tang=5)]
    kq = DM.tim(uv, _danh_gia_theo_buoc(30.0), ngan_sach=2)
    assert kq.so_phep_thu == 2
    assert kq.ly_do_dung == "het ngan sach o luoi thu gon"
    # ung vien tot nhat (buoc=30) phai co trong top
    assert any(abs(t["tham_so"].buoc - 30.0) < 1e-9 for t in kq.top)


def test_tim_chon_dung_o_gan_muc_tieu():
    uv = [_ts(buoc=10.0, tp=20.0, tran_tang=5)]
    kq = DM.tim(uv, _danh_gia_theo_buoc(20.0), he_buoc=(0.5, 1.0, 2.0), he_tp=(1.0,), he_tam=(1.0,),
                so_tot=1, so_vong=0)
    assert kq.so_phep_thu > 0
    assert kq.tot_nhat is not None
    # o tot nhat phai co buoc gan 20 (trong luoi 5,10,20)
    assert abs(kq.tot_nhat.buoc - 20.0) < 1e-9
    assert kq.plan_hash == DM.ke_hoach(1, 1, 0, (0.5, 1.0, 2.0), (1.0,), (1.0,))["plan_hash"]


def test_tim_khong_do_lai_o_trung():
    # hai ung vien giong het nhau -> chi do 1 lan
    uv = [_ts(buoc=10.0, tp=20.0, tran_tang=5), _ts(buoc=10.0, tp=20.0, tran_tang=5)]
    kq = DM.tim(uv, _danh_gia_theo_buoc(10.0), he_buoc=(1.0,), he_tp=(1.0,), he_tam=(1.0,), so_tot=1, so_vong=0)
    assert kq.so_phep_thu == 1


def test_tim_danh_gia_sai_so_diem_thi_loi():
    uv = [_ts(buoc=10.0, tp=20.0, tran_tang=5)]
    try:
        DM.tim(uv, lambda cac: [0.0] * (len(cac) + 1), he_buoc=(1.0,), he_tp=(1.0,), he_tam=(1.0,), so_tot=1, so_vong=0)
    except ValueError:
        pass
    else:
        raise AssertionError("danh_gia tra sai so diem phai gay ValueError")


def test_tim_to_dict_co_cac_truong_can_thiet():
    uv = [_ts(buoc=10.0, tp=20.0, tran_tang=5)]
    kq = DM.tim(uv, _danh_gia_theo_buoc(10.0), he_buoc=(1.0,), he_tp=(1.0,), he_tam=(1.0,), so_tot=1, so_vong=0)
    d = kq.to_dict()
    assert set(d.keys()) == {"so_phep_thu", "plan_hash", "ly_do_dung", "lich_su", "top"}
    assert d["so_phep_thu"] == kq.so_phep_thu
    assert d["plan_hash"] == kq.plan_hash
    for t in d["top"]:
        assert set(t.keys()) == {"tham_so", "diem", "cao_nguyen", "nguon"}
        assert isinstance(t["tham_so"], dict)
