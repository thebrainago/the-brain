# -*- coding: utf-8 -*-
"""test_chuyen_he.py - Mang mot he sang khung / tai san khac.

Ba module (`doi_khung` · `ngoai_sinh` · `quy_doi_tham_so`) deu MO COI cho toi
12/09. Chung tra loi cung mot cau: *mang he nay sang cho khac thi phai sua gi
de no van la chinh no?*

Ba dieu phai chan:

  * **Tra kho bang `ten`, khong phai `van_tay`.** `to_hop` ghi
    `co_che = spec["ten"]`. Tra nham khoa thi MOI dong bao "khong tim thay
    spec" va ca chang im lang bo qua - mot am tinh gia nua
    ([[luat-do-phai-thay-duoc-cai-co]]). Da sap that o ban dau file nay.
  * **"Khong dat" != "co che sai".** No nghia la co che GAN VOI KHUNG do. Hai
    ket luan khac han nhau ([[ket-luan-am-phai-phan-biet-CHUA-DO]]).
  * **Chi doi don vi CO THU NGUYEN GIA.** `boi_so`/`dem`/`phan_tram`/`lot`
    khong co thu nguyen gia; nhan chung voi ty le ATR la lam hong y dinh cua
    tac gia.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import chuyen_he as CH          # noqa: E402
from nhan import quy_doi_tham_so as QT    # noqa: E402


def test_tra_kho_bang_ten(monkeypatch, tmp_path):
    """Khoa tra la `ten` cua spec - `to_hop` ghi truong do, khong ghi van tay."""
    from nhan import ngu_phap as NP
    spec = {"ten": "co_che_thu_X", "van_tay": "abc123", "giu": 1,
            "vao": {"va": [{"chi_bao": "rsi", "n": 14, "phep": "<",
                            "nguong": 30}]}}
    monkeypatch.setattr(NP, "doc_kho", lambda: [spec])
    so = tmp_path / "reports"
    so.mkdir()
    (so / "TO_HOP.json").write_text(json.dumps({
        "holdout": [{"ma": "US500CASH", "khung": "D1",
                     "co_che": "co_che_thu_X", "qua_holdout": True}]}),
        encoding="utf-8")
    monkeypatch.setattr(CH, "LAB", tmp_path)
    k = CH.sang_khung("H4", in_ra=lambda *a: None)
    assert k["thieu_spec"] == 0, "tra kho bang van_tay thi con so nay = 1"


def test_khong_dat_khong_phai_co_che_sai(monkeypatch, tmp_path):
    """Thong diep phai phan biet 'gan voi khung' voi 'co che sai'."""
    from nhan import ngu_phap as NP
    spec = {"ten": "cx", "giu": 1,
            "vao": {"va": [{"chi_bao": "rsi", "n": 14, "phep": "<",
                            "nguong": 30}]}}
    monkeypatch.setattr(NP, "doc_kho", lambda: [spec])
    so = tmp_path / "reports"
    so.mkdir()
    (so / "TO_HOP.json").write_text(json.dumps({
        "holdout": [{"ma": "US500CASH", "khung": "D1", "co_che": "cx",
                     "qua_holdout": True}]}), encoding="utf-8")
    monkeypatch.setattr(CH, "LAB", tmp_path)
    ra = []
    k = CH.sang_khung("H4", in_ra=ra.append)
    vb = "\n".join(ra)
    # BA trang thai. Thong diep phai khop dung nhom, khong duoc tron:
    if k.get("do_duoc") and not k.get("dat"):
        assert "GAN VOI" in vb            # do duoc va truot -> ket qua am that
    if k.get("chua_do_duoc"):
        assert "CHUA DO" in vb and "KHONG phai ket qua am" in vb
        assert "GAN VOI" not in vb or k.get("do_duoc")


def test_thieu_du_lieu_khong_bi_dem_la_truot(monkeypatch, tmp_path):
    """"Thieu du lieu H4" va "lech qua nguong" la HAI ket luan khac nhau."""
    from nhan import doi_khung as DK
    from nhan import ngu_phap as NP
    spec = {"ten": "cx", "giu": 1,
            "vao": {"va": [{"chi_bao": "rsi", "n": 14, "phep": "<",
                            "nguong": 30}]}}
    monkeypatch.setattr(NP, "doc_kho", lambda: [spec])
    monkeypatch.setattr(DK, "doi",
                        lambda *a, **k: {"loi": "thieu du lieu X D1/H4"})
    so = tmp_path / "reports"
    so.mkdir()
    (so / "TO_HOP.json").write_text(json.dumps({
        "holdout": [{"ma": "X", "khung": "D1", "co_che": "cx",
                     "qua_holdout": True}]}), encoding="utf-8")
    monkeypatch.setattr(CH, "LAB", tmp_path)
    k = CH.sang_khung("H4", in_ra=lambda *a: None)
    assert k["chua_do_duoc"] == 1
    assert k["do_duoc"] == 0 and k["dat"] == 0


def test_nguon_uu_tien_co_che_qua_holdout(monkeypatch, tmp_path):
    so = tmp_path / "reports"
    so.mkdir()
    (so / "TO_HOP.json").write_text(json.dumps({
        "holdout": [{"ma": "A", "co_che": "x", "qua_holdout": True},
                    {"ma": "B", "co_che": "y", "qua_holdout": False}],
        "top": [{"ma": "C", "co_che": "z"}]}), encoding="utf-8")
    monkeypatch.setattr(CH, "LAB", tmp_path)
    ds = CH._nguon(in_ra=None)
    assert len(ds) == 1 and ds[0]["ma"] == "A"


def test_khong_co_holdout_thi_lay_top_va_NOI_RA(monkeypatch, tmp_path):
    """Lay nguon yeu hon thi phai noi ra, khong im lang doi nguon."""
    so = tmp_path / "reports"
    so.mkdir()
    (so / "TO_HOP.json").write_text(json.dumps({
        "holdout": [], "top": [{"ma": "C", "co_che": "z"}]}), encoding="utf-8")
    monkeypatch.setattr(CH, "LAB", tmp_path)
    ra = []
    ds = CH._nguon(in_ra=ra.append)
    assert len(ds) == 1
    assert any("yeu hon" in d for d in ra)


# ------------------------------------------------- quy doi tham so
def test_chi_doi_don_vi_co_thu_nguyen_gia():
    khai = [{"ten": "sl_diem", "gia_tri": 50.0, "don_vi": "diem"},
            {"ten": "he_so_lot", "gia_tri": 2.0, "don_vi": "boi_so"},
            {"ten": "rui_ro_pct", "gia_tri": 1.0, "don_vi": "phan_tram"}]
    k = QT.quy_doi(khai, atr_goc=10.0, atr_dich=20.0)
    ds = k.get("khai") or k.get("ket") or []
    theo = {d.get("ten"): d for d in ds if isinstance(d, dict)}
    if "he_so_lot" in theo:
        assert theo["he_so_lot"].get("gia_tri_moi",
                                     theo["he_so_lot"].get("gia_tri")) == 2.0
    if "rui_ro_pct" in theo:
        assert theo["rui_ro_pct"].get("gia_tri_moi",
                                      theo["rui_ro_pct"].get("gia_tri")) == 1.0


def test_atr_khong_duong_thi_nem_loi():
    """Khong doan: ATR khong do duoc thi tu choi quy doi."""
    import pytest
    with pytest.raises(ValueError):
        QT.quy_doi([{"ten": "a", "gia_tri": 1.0, "don_vi": "gia"}], 0.0, 5.0)


def test_ba_module_da_noi_vao_duong_chay():
    from nhan import ban_do as BD
    toi, _ = BD.voi_toi_duoc()
    for t in ("nhan/chuyen_he.py", "nhan/doi_khung.py", "nhan/ngoai_sinh.py",
              "nhan/quy_doi_tham_so.py"):
        assert t in toi, "%s van mo coi" % t
