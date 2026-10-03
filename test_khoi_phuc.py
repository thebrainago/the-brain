# -*- coding: utf-8 -*-
"""b khoi-phuc: chan doan may sau khi cai lai Windows - dung ban sao con lai, KHONG lo bi mat."""
from __future__ import annotations

import json

import pytest

from nhan import duong_dan as DP, khoi_phuc as KP


@pytest.fixture
def may_trong(tmp_path, monkeypatch):
    """Mot may 'sach': kho gia / cache tro vao thu muc rong, lab tro vao thu muc rong."""
    lab = tmp_path / "lab"
    (lab / "config").mkdir(parents=True)
    kho, cache = tmp_path / "data", tmp_path / "data_khung"
    kho.mkdir(), cache.mkdir()
    monkeypatch.setenv("BRAIN_DATA", str(kho))
    monkeypatch.setenv("BRAIN_CACHE", str(cache))
    monkeypatch.setattr(KP, "LAB", lab)
    monkeypatch.setattr(DP, "LAB", lab)
    monkeypatch.setattr(DP, "GOC", tmp_path)          # ds/ tim o day
    return tmp_path


def _tim(ds, ten):
    return next(x for x in ds if x["ten"].startswith(ten))


def test_may_trong_bao_thieu_kho_gia_nao_db_va_ds_la_MAT_THAT(may_trong):
    ds = KP.chan_doan(he_thong=may_trong / "khong_co_he_thong")
    for ten in ("kho gia", "nao.db", "ds/"):
        x = _tim(ds, ten)
        assert x["ok"] is False and x["mat_that"] is True, x
    # cache khong phai mat that: tai tao duoc tu data/
    assert _tim(ds, "cache data_khung")["mat_that"] is False


def test_dem_dung_bang_parquet_va_nhan_ra_kho_con(may_trong):
    for i in range(3):
        (may_trong / "data" / f"X{i}_M1_mq.parquet").write_bytes(b"x" * 1000)
    x = _tim(KP.chan_doan(he_thong=may_trong / "k"), "kho gia")
    assert x["ok"] is True and "3 bang" in x["chi_tiet"]


def test_nao_db_vai_chuc_KB_la_DB_moi_khoi_tao_khong_phai_du_lieu_cu(may_trong):
    (may_trong / "lab" / "nao.db").write_bytes(b"x" * 50_000)
    assert _tim(KP.chan_doan(he_thong=may_trong / "k"), "nao.db")["ok"] is False
    (may_trong / "lab" / "nao.db").write_bytes(b"x" * 2_000_000)
    assert _tim(KP.chan_doan(he_thong=may_trong / "k"), "nao.db")["ok"] is True


def test_windows_old_duoc_bao_dong_dau_tien_kem_nao_db_ben_trong(may_trong):
    he = may_trong / "C"
    lab_cu = he / "Windows.old" / "Users" / "SV STORE" / "Downloads" / "Research SP500" / "lab"
    lab_cu.mkdir(parents=True)
    (lab_cu / "nao.db").write_bytes(b"x" * 3_000_000)
    ds = KP.chan_doan(he_thong=he)
    wo = _tim(ds, "Windows.old")
    assert wo["ok"] is True and "nao.db" in wo["chi_tiet"] and "10 ngay" in wo["chi_tiet"]
    buoc = KP.buoc_tiep(ds)
    assert buoc[0].startswith("COPY Windows.old"), buoc[:2]


def test_file_bi_mat_chi_bao_co_hay_khong_KHONG_in_noi_dung(may_trong):
    (may_trong / "lab" / "config" / "api_keys.json").write_text('{"k": "KHOA-BI-MAT-12345"}', "utf-8")
    ds = KP.chan_doan(he_thong=may_trong / "k")
    bao_cao = KP.bao_cao(ds)
    assert "KHOA-BI-MAT-12345" not in bao_cao
    assert "KHOA-BI-MAT-12345" not in json.dumps(ds)
    assert _tim(ds, "config/api_keys.json")["ok"] is True
    assert _tim(ds, "config/gh_token.txt")["ok"] is False


def test_buoc_tiep_khong_rong_va_may_du_do_thi_noi_khong_thieu(may_trong):
    assert KP.buoc_tiep([]) == ["Khong thieu gi dang ke. Chay `b vao`, `b nc`, roi `b test`."]
    assert len(KP.buoc_tiep(KP.chan_doan(he_thong=may_trong / "k"))) >= 3


def test_json_dung_dinh_dang(may_trong, capsys):
    assert KP.main(["--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert set(out) == {"kiem", "buoc_tiep"} and out["kiem"]
