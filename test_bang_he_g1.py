# -*- coding: utf-8 -*-
"""Test cho G1: xep theo TIEN, va bat ban trung.

Hai thu nay tung hong theo kieu khong ai thay: bang xep theo Sharpe nen he
0,62%/nam dung dau, va hai ban sao cua mot co che trong nhu hai xac nhan doc
lap. Test o day khoa ca hai lai.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import bang_he as BH  # noqa: E402


def _he(ten, cagr, sharpe, dd, calmar, lenh, nam=9.0, mua_giu=0.0):
    return {"he": ten, "cagr_pct": cagr, "sharpe": sharpe, "max_dd_pct": dd,
            "calmar": calmar, "so_lenh": lenh, "so_nam": nam,
            "mua_giu_cagr": mua_giu, "sach": True, "cong_truot": []}


def _chuan(ds):
    for d in ds:
        c, m = d["cagr_pct"], d["mua_giu_cagr"]
        d["hon_mua_giu_cagr"] = round(c - m, 3)
    BH._danh_ban_trung(ds)
    for d in ds:
        d["cong_tien"] = BH._cong_tien(d)
    ds.sort(key=BH._xep_theo_tien)
    return ds


def test_he_sharpe_cao_ma_khong_ra_tien_khong_duoc_dung_dau():
    """Chinh cai da xay 16/09: Sharpe 1,47 / 0,62%/nam dung dau bang."""
    ds = _chuan([
        _he("EURGBP.H4.mat_can_bang", 0.62, 1.47, -0.28, 2.19, 49, mua_giu=-2.84),
        _he("XM_US100.D1.z5", 14.05, 1.16, -13.51, 1.04, 204, mua_giu=2.0),
    ])
    assert ds[0]["he"] == "XM_US100.D1.z5", \
        "he ra tien 12 diem phai dung tren he ra tien 3,46 diem"


def test_thua_mua_giu_thi_xuong_duoi_du_cagr_cao():
    """Xep hang van day he thua mua-giu xuong duoi. Tu 25/09 (chu du an: "chi can co
    lai va maxdd duoi 80% la ok") thua mua-giu la NHAN, khong con truot cong tien."""
    ds = _chuan([
        _he("A.D1.thua_moc", 8.26, 0.95, -10.21, 0.81, 197, mua_giu=9.97),
        _he("B.H4.hon_moc", 4.16, 1.16, -3.72, 1.12, 62, mua_giu=0.60),
    ])
    assert ds[0]["he"] == "B.H4.hon_moc"
    assert ds[-1]["cong_tien"]["dat"], "co lai + DD duoi 80% -> qua cong tien"
    assert any("KHONG hon mua-giu" in x for x in ds[-1]["cong_tien"]["nhan"])


def test_khong_lai_hoac_sut_giam_80_thi_truot_cong_tien():
    ds = _chuan([_he("C.D1.lo", -1.0, -0.2, -30.0, -0.03, 120, mua_giu=0.0),
                 _he("D.D1.sau", 30.0, 0.8, -80.0, 0.37, 120, mua_giu=0.0)])
    for d in ds:
        assert not d["cong_tien"]["dat"], d["he"]


def test_bat_ban_trung_va_day_xuong_duoi():
    ds = _chuan([
        _he("X.H4.co_che.", 0.69, 0.94, -1.17, 0.59, 53, mua_giu=0.60),
        _he("X.H4.co_che.mac_dinh", 0.69, 0.94, -1.17, 0.59, 53, mua_giu=0.60),
        _he("X.H4.khac", 3.00, 0.50, -5.00, 0.60, 80, mua_giu=0.60),
    ])
    trung = [d for d in ds if d.get("ban_trung_cua")]
    assert len(trung) == 1, "hai dong trung khit phai bat duoc dung mot ban trung"
    assert trung[0]["he"] == "X.H4.co_che.mac_dinh"
    assert trung[0]["ban_trung_cua"] == "X.H4.co_che."
    assert ds[-1] is trung[0], "ban trung phai xuong cuoi bang"


def test_lech_mot_lenh_thi_KHONG_phai_ban_trung():
    """Van tay phai du chat: lech mot lenh la hai he khac nhau."""
    ds = _chuan([
        _he("Y.H4.a", 5.0, 1.0, -4.0, 1.25, 60, mua_giu=0.5),
        _he("Y.H4.b", 5.0, 1.0, -4.0, 1.25, 61, mua_giu=0.5),
    ])
    assert not any(d.get("ban_trung_cua") for d in ds)


def test_nguong_lay_tu_cong_ra_tien_chu_khong_go_lai():
    """Neu ai doi nguong trong `cong_ra_tien` thi bang nay phai doi theo."""
    from nhan import cong_ra_tien as CRT
    assert BH._nguong() == (CRT.MUC_CAGR, CRT.TRAN_DD,
                            CRT.MIN_LENH, CRT.MIN_NAM)


def test_he_it_lenh_bi_cong_tien_tu_choi():
    d = _chuan([_he("Z.H4.it_lenh", 25.0, 2.0, -10.0, 2.5, 9, mua_giu=1.0)])[0]
    assert not d["cong_tien"]["dat"]
    assert any("lenh <" in x for x in d["cong_tien"]["ly_do"])
