# -*- coding: utf-8 -*-
"""test_cham_tien.py - Chang CUOI cua vong day du phai tra loi cau hoi TIEN.

Ban do 12/09 cho thay `cham_diem` va `cong_ra_tien` - hai module hien than
truc tiep cua LUAT SO 0 (*"muc dich cuoi cung la co tien"*) - deu MO COI.
`vong_day_du._cham_tien` la cho noi chung vao. Test o day giu hai dieu:

  * **Hieu chuan hai chieu.** Mot bo cham tu choi TAT CA cho so lieu y het mot
    bo cham tot. Nen phai co ca phep thu "phai DAT" lan "phai TRUOT".
  * **Khong doan `so_nam`.** Thieu no thi `so_lenh_nam` = TONG so lenh va moi
    dong deu vuot nguong 20/nam mot cach gia.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import cham_diem as CD          # noqa: E402
from nhan import vong_day_du as V         # noqa: E402

_TOT = {"ma": "US500CASH", "khung": "D1", "co_che": "ibs_thap",
        "luat": "sl2_trail1", "cagr_dd20": 26.0, "so_lenh": 300,
        "so_nam": 10.0, "chet_tai_khoan": False}


def test_he_tot_thi_chay_duoc():
    assert CD.tu_to_hop(_TOT)["muc"] == "CHAY_DUOC"


def test_lai_thap_thi_mong():
    x = CD.tu_to_hop(dict(_TOT, cagr_dd20=1.5))
    assert x["muc"] == "MONG"
    assert any("muc 20%" in l for l in x["ly_do"])


def test_it_lenh_thi_mong():
    x = CD.tu_to_hop(dict(_TOT, so_lenh=30))       # 3 lenh/nam
    assert x["muc"] == "MONG"
    assert any("lenh/nam" in l for l in x["ly_do"])


def test_chay_tai_khoan_thi_bo():
    assert CD.tu_to_hop(dict(_TOT, chet_tai_khoan=True))["muc"] == "BO"


def test_bo_dem_von_gap_doi_sut_giam():
    """Von phai bo ra = 2x sut giam lich su, khong phai 1x.

    De 1x thi he 26%/nam bao thanh 130%/nam - con so cua nguoi lac quan.
    """
    x = CD.tu_to_hop(_TOT)
    assert x["von_can"] == 20.0 * CD.BO_DEM_SUT_GIAM
    assert abs(x["lai_pct_nam"] - 26.0 / 40.0 * 100.0) < 0.1


def test_so_lenh_nam_chia_dung_so_nam():
    x = CD.tu_to_hop(dict(_TOT, so_lenh=300, so_nam=10.0))
    assert abs(x["so_lenh_nam"] - 30.0) < 0.01
    y = CD.tu_to_hop(dict(_TOT, so_lenh=300, so_nam=30.0))
    assert abs(y["so_lenh_nam"] - 10.0) < 0.01
    assert y["muc"] == "MONG"          # 10 lenh/nam < nguong 20


def test_thieu_so_nam_thi_bo_qua_chu_khong_doan(tmp_path, monkeypatch):
    """Dong khong co `so_nam` phai bi BO, khong duoc lay tong lenh lam lenh/nam.

    Bai nay dung `ma` = `US500CASH` cho toi 13/09/2026 va do la mot bo do MU:
    `_cham_tien._nam()` nay co duong lui - thieu `so_nam` thi no NAP GIA THAT
    cua ma do roi tu tinh ra (them vi `TO_HOP.json` cu khong co truong nay va
    chay lai ca pheu mat ~110 phut). Voi mot ma CO THAT trong kho, duong lui
    do luon thanh cong, nen `thieu_nam` mai mai bang 0 va bai kiem do khong
    con gac gi.

    Hop dong DUNG bay gio la: thieu `so_nam` VA khong suy ra duoc tu du lieu
    -> bo dong do. Nen o day phai dung mot ma KHONG co trong kho.
    """
    so = tmp_path / "reports"
    so.mkdir()
    (so / "TO_HOP.json").write_text(json.dumps({
        "top": [{k: v for k, v in _TOT.items() if k != "so_nam"}
                | {"ma": "MA_KHONG_TON_TAI_XYZ"}],
        "holdout": []}), encoding="utf-8")
    monkeypatch.setattr(V, "LAB", tmp_path)
    k = V._cham_tien(lambda *a: None)
    assert k.get("thieu_nam") == 1
    assert "0/1" in k.get("bo", "")


def test_qua_holdout_duoc_danh_dau(tmp_path, monkeypatch):
    """He qua holdout phai het la 'canh bac', thanh `da_qua_cong_that`."""
    so = tmp_path / "reports"
    so.mkdir()
    khoa = {k: _TOT[k] for k in ("ma", "khung", "co_che", "luat")}
    (so / "TO_HOP.json").write_text(json.dumps({
        "top": [dict(_TOT)],
        "holdout": [dict(khoa, qua_holdout=True)]}), encoding="utf-8")
    monkeypatch.setattr(V, "LAB", tmp_path)
    ra = []
    k = V._cham_tien(ra.append)
    assert k["cham"] == 1 and k["chay_duoc"] == 1 and k["qua_holdout"] == 1
    assert not any("chua qua cong that" in d for d in ra)


def test_chua_qua_holdout_thi_bi_goi_dung_ten(tmp_path, monkeypatch):
    so = tmp_path / "reports"
    so.mkdir()
    (so / "TO_HOP.json").write_text(json.dumps({
        "top": [dict(_TOT)], "holdout": []}), encoding="utf-8")
    monkeypatch.setattr(V, "LAB", tmp_path)
    ra = []
    V._cham_tien(ra.append)
    assert any("canh bac" in d for d in ra)


def test_khong_co_to_hop_thi_khong_no():
    """Chang phai tra ve chu khong nem loi khi chua co ket qua."""
    import tempfile
    import types
    cu = V.LAB
    try:
        V.LAB = Path(tempfile.mkdtemp())
        assert "bo" in V._cham_tien(lambda *a: None)
    finally:
        V.LAB = cu
    assert isinstance(types, types.ModuleType)


def test_vong_co_chang_cham_tien():
    """Chang phai NAM TRONG vong, khong chi ton tai."""
    import inspect
    ma = inspect.getsource(V.vong)
    assert "_cham_tien" in ma
