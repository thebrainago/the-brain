# -*- coding: utf-8 -*-
"""HIEU CHUAN HAI CHIEU cua nha nghien cuu tren chuoi CO DAP AN (cham: ~1-2 phut).

Luat du an: *"hieu chuan cong phai HAI CHIEU - mot cong tu choi TAT CA cho so lieu y
het mot cong tot"*. Nen o day do ca hai: edge cai san phai DAT qua niem phong; nhieu va
bay chi phi thi KHONG duoc DAT. Chay day du + ti le bao dong gia: `b nc kiem 30`.
"""
from __future__ import annotations

import pytest

from nhan import nc_so_tay as ST
from nhan import nc_tu_lai as TL


@pytest.mark.cham
def test_tu_lai_hai_chieu_tren_chuoi_co_dap_an(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    r = TL.hieu_chuan(cac_ma=("TONG_HOP_NHIEU_1", "TONG_HOP_HOI_QUY_1", "TONG_HOP_XU_HUONG_1"),
                      so_null=100, ghi_bao_cao=False, in_ra=lambda *_: None)
    theo = {k["ma"]: k for k in r["chi_tiet"]}
    assert theo["TONG_HOP_HOI_QUY_1"]["ket_cuc"] == "DAT", "bo sot edge cai san"
    assert theo["TONG_HOP_NHIEU_1"]["ket_cuc"] != "DAT", "bao dong gia tren nhieu"
    assert theo["TONG_HOP_XU_HUONG_1"]["ket_cuc"] != "DAT", "quen tru chi phi (bay chi phi)"
    assert r["sai"] == 0
    assert all(d["dung"] for d in r["hoc_tu_lenh"]), r["hoc_tu_lenh"]
    assert ST.DB == tmp_path / "nc.db", "hieu chuan phai tra so tay ve cho cu"
