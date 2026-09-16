# -*- coding: utf-8 -*-
"""Test G3-A: mot tin hieu vao khong duoc ghi so mot minh.

So do cua chu du an dat quan li lenh tren entry. Do 16/09: 262 co che la tin
hieu VAO, chi 18 la quan tri. Cong o day chan dung cho do.

Phan biet PHAI giu: "chua chay du bo luat" khac "bo luat khong co CHO de chay".
Tron hai cai lai la dung bay `CHUA_DO_DUOC` vs `AM` ma luat doc ket qua cam.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import dap_quan_tri as D  # noqa: E402


def _kq(luat, bar_tv=10.0):
    return {"luat": luat, "bar_tv": bar_tv, "so_lenh": 60}


def test_ba_bo_bat_buoc_deu_co_that_trong_BO_LUAT():
    """Tranh go ten mot bo luat khong ton tai roi cong khong bao gio mo."""
    for t in D.BO_BAT_BUOC:
        assert t in D.BO_LUAT, "%s khong co trong BO_LUAT" % t


def test_bo_bat_buoc_phu_ca_hue_lan_trailing():
    co_hue = any(D._co_nut(D.BO_LUAT[t], "hue_tu_atr") for t in D.BO_BAT_BUOC)
    co_trail = any(D._co_nut(D.BO_LUAT[t], "trail_tu_atr") for t in D.BO_BAT_BUOC)
    assert co_hue and co_trail


def test_chan_tin_hieu_chay_mot_minh():
    r = D.du_chan_quan_tri([])
    assert not r["dat"]
    assert any("can >= 3" in x for x in r["ly_do"])


def test_chan_khi_thieu_DAT_HUE():
    ds = [_kq("sl2_trail1"), _kq("sl3_trail2"), _kq("sl2_tp4")]
    r = D.du_chan_quan_tri(ds)
    assert not r["dat"]
    assert any("DAT HUE" in x for x in r["ly_do"])
    assert r["co_trail"] == 2


def test_chan_khi_thieu_TRAILING():
    ds = [_kq("sl2_tp4_hue1"), _kq("sl2_tp4"), _kq("chot_nhanh_sl1_tp1")]
    r = D.du_chan_quan_tri(ds)
    assert not r["dat"]
    assert any("TRAILING" in x for x in r["ly_do"])


def test_dat_khi_du_ba_bo_bat_buoc():
    r = D.du_chan_quan_tri([_kq(t) for t in D.BO_BAT_BUOC])
    assert r["dat"], r["ly_do"]
    assert r["da_chay"] == 3 and r["co_hue"] >= 1 and r["co_trail"] >= 1


def test_khong_gi_khong_tinh_la_mot_bo_luat():
    ds = [_kq("khong_gi")] + [_kq(t) for t in D.BO_BAT_BUOC[:2]]
    r = D.du_chan_quan_tri(ds)
    assert r["da_chay"] == 2, "`khong_gi` la MOC doi chieu, khong phai quan tri"


def test_he_thoat_nhanh_thi_trailing_la_THIEU_CHO_chu_khong_phai_AM():
    ds = [_kq(t, bar_tv=1.0) for t in D.BO_BAT_BUOC]
    r = D.du_chan_quan_tri(ds)
    assert len(r["thieu_cho"]) >= 2, \
        "trailing va dat hue tren he giu 1 bar phai bi danh THIEU CHO"
    assert all("khong kip kich hoat" in x["ly_do"] for x in r["thieu_cho"])


def test_luat_khong_can_cho_thi_khong_bi_danh_thieu_cho():
    """`sl2_tp4` khong co trailing/hue -> giu 1 bar van do duoc."""
    ok, ly = D.luat_co_cho(1.0, "sl2_tp4")
    assert ok and not ly


def test_bar_trung_vi_thieu_thi_khong_ket_luan():
    ok, _ = D.luat_co_cho(None, "sl2_trail1")
    assert ok, "chua do duoc bar_tv thi khong duoc ket luan la thieu cho"
