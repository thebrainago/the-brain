import numpy as np
from nhan.pmg_g0 import (
    _er, _er_cac_cua_so, _cua_so_cho_h, _null_dao_dau, _null_block, _null_gbm,
    do_mot_o, fdr_bh, BAC_MOI_CUA_SO
)


def test_er_trend_thuan():
    gia = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert abs(_er(gia) - 1.0) < 1e-9


def test_er_zigzag_bang_0():
    gia = np.array([1.0, 2.0, 1.0, 2.0, 1.0])
    assert _er(gia) == 0.0


def test_er_phang_tra_nan():
    gia = np.array([5.0, 5.0, 5.0, 5.0])
    assert np.isnan(_er(gia))


def test_er_mot_bar_tra_nan():
    gia = np.array([3.0])
    assert np.isnan(_er(gia))


def test_er_cac_cua_so_do_dai_hop_le():
    gia = np.arange(20, dtype=float)
    L = 4
    ket_qua = _er_cac_cua_so(gia, L)
    assert len(ket_qua) == 5
    for v in ket_qua:
        assert abs(v - 1.0) < 1e-9


def test_er_cac_cua_so_it_qua_tra_rong():
    gia = np.arange(10, dtype=float)
    ket_qua = _er_cac_cua_so(gia, 4)
    assert len(ket_qua) == 0


def test_cua_so_cho_h_buoc_lon():
    gia = np.cumsum(np.ones(200))
    buoc = 10.0
    L = _cua_so_cho_h(gia, buoc)
    mong_doi = max(4, int(round(BAC_MOI_CUA_SO * buoc / 1.0)))
    assert L == mong_doi


def test_cua_so_cho_h_phang_tra_0():
    gia = np.ones(100)
    assert _cua_so_cho_h(gia, 1.0) == 0


def test_null_dao_dau_giu_tri_tuyet_doi():
    r = np.array([0.1, -0.2, 0.3, -0.4, 0.5])
    mau = _null_dao_dau(r, 50, hat=1)
    assert mau.shape == (50, 5)
    for i in range(50):
        assert np.allclose(np.abs(mau[i]), np.abs(r))


def test_null_block_dung_kich_thuoc():
    r = np.random.default_rng(0).normal(0, 1, 100)
    mau = _null_block(r, 10, hat=1, khoi=20)
    assert mau.shape == (10, 100)


def test_null_gbm_dung_kich_thuoc():
    r = np.random.default_rng(0).normal(0, 1, 100)
    mau = _null_gbm(r, 10, hat=1)
    assert mau.shape == (10, 100)


def test_fdr_bh_p_nho_va_lon():
    cac_p = [0.001, 0.5, 0.01, 0.9]
    dat = fdr_bh(cac_p, muc=0.10)
    assert isinstance(dat, list)
    assert len(dat) == 4
    assert dat[0] is True
    assert dat[2] is True
    assert dat[1] is False
    assert dat[3] is False


def test_fdr_bh_rong():
    assert fdr_bh([], muc=0.10) == []


def test_do_mot_o_du_lieu_ngan():
    gia = np.ones(10)
    kq = do_mot_o(gia, h_atr=1.0, atr_tv=0.01, so_null=5)
    assert kq["trang_thai"] == "CHUA_DO_DUOC"
