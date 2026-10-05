# -*- coding: utf-8 -*-
"""Test cho nhan/khoi_phuc.py - chan doan may: con gi, thieu gi."""
from __future__ import annotations

import sys
from pathlib import Path

from nhan import khoi_phuc as KP


# ---------- _dong ----------

def test_dong_tra_ve_dict_du_truong():
    d = KP._dong("nhom", "ten", True, "chi tiet", "sua", mat_that=True)
    assert d == {"nhom": "nhom", "ten": "ten", "ok": True,
                 "chi_tiet": "chi tiet", "sua": "sua", "mat_that": True}


def test_dong_mac_dinh_rong_va_khong_mat_that():
    d = KP._dong("n", "t", None)
    assert d["chi_tiet"] == ""
    assert d["sua"] == ""
    assert d["mat_that"] is False
    assert d["ok"] is None


def test_dong_ok_false_van_giu():
    d = KP._dong("n", "t", False)
    assert d["ok"] is False


# ---------- _gb ----------

def test_gb_khong_va_bien():
    assert KP._gb(0) == "0.00 GB"
    assert KP._gb(1_000_000_000) == "1.00 GB"
    assert KP._gb(1_500_000_000) == "1.50 GB"


# ---------- _parquet ----------

def test_parquet_thu_muc_khong_ton_tai():
    # Path khong ton tai -> glob tra rong, khong nem
    n, b = KP._parquet(Path("__khong_ton_tai_xyz__"))
    assert n == 0
    assert b == 0.0


def test_parquet_thu_muc_rong(tmp_path=None):
    # dung thu muc tam cua he thong qua tempfile de khong ghi vao repo
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        n, b = KP._parquet(Path(td))
        assert n == 0
        assert b == 0.0


# ---------- buoc_tiep ----------

def test_buoc_tiep_khi_khong_thieu_gi():
    ds = [KP._dong("cong cu", "python", True),
          KP._dong("cong cu", "git", True),
          KP._dong("cong cu", "claude (Claude Code)", True),
          KP._dong("ma nguon", "nhanh + commit", True),
          KP._dong("du lieu", "kho gia data/", True),
          KP._dong("du lieu", "nao.db", True),
          KP._dong("ban sao con lai", "ds/ (git rieng, KHONG co tren GitHub)", True),
          KP._dong("mt5", "terminal64.exe", True),
          KP._dong("bi mat", "config/api_keys.json", True)]
    b = KP.buoc_tiep(ds)
    assert b == ["Khong thieu gi dang ke. Chay `b vao`, `b nc`, roi `b test`."]


def test_buoc_tiep_uu_tien_windows_old_len_dau():
    ds = [KP._dong("ban sao con lai", "Windows.old", True, "CO"),
          KP._dong("cong cu", "python", True),
          KP._dong("cong cu", "git", True),
          KP._dong("cong cu", "claude (Claude Code)", True),
          KP._dong("ma nguon", "nhanh + commit", True),
          KP._dong("du lieu", "kho gia data/", True),
          KP._dong("du lieu", "nao.db", True),
          KP._dong("ban sao con lai", "ds/ (git rieng, KHONG co tren GitHub)", True),
          KP._dong("mt5", "terminal64.exe", True),
          KP._dong("bi mat", "config/api_keys.json", True)]
    b = KP.buoc_tiep(ds)
    assert b[0].startswith("COPY Windows.old")


def test_buoc_tiep_bao_kho_git_khong_phai_repo():
    ds = [KP._dong("ma nguon", "kho git (thu muc nay)", False, "khong phai kho git",
                   "git clone https://github.com/thebrainago/the-brain.git lab")]
    b = KP.buoc_tiep(ds)
    assert any("git clone" in s for s in b)


def test_buoc_tiep_bao_nao_db_mat():
    ds = [KP._dong("du lieu", "nao.db", False, "thieu", "tao lai")]
    b = KP.buoc_tiep(ds)
    assert any("nao.db mat" in s for s in b)


def test_buoc_tiep_bao_ds_khong_con():
    ds = [KP._dong("ban sao con lai", "ds/ (git rieng, KHONG co tren GitHub)", False, "thieu")]
    b = KP.buoc_tiep(ds)
    assert any("ds/ khong con" in s for s in b)


def test_buoc_tiep_bao_bi_mat_thieu():
    ds = [KP._dong("bi mat", "config/api_keys.json", False, "khong")]
    b = KP.buoc_tiep(ds)
    assert any("Tao lai file khoa" in s for s in b)


# ---------- bao_cao ----------

def test_bao_cao_in_theo_nhom_va_buoc_tiep():
    ds = [KP._dong("cong cu", "python", True, "3.11"),
          KP._dong("du lieu", "nao.db", False, "thieu")]
    ra = KP.bao_cao(ds)
    assert "[cong cu]" in ra
    assert "[du lieu]" in ra
    assert "CO    python" in ra
    assert "THIEU nao.db" in ra
    assert "BUOC TIEP" in ra


def test_bao_cao_ok_none_hien_dau_gach():
    ds = [KP._dong("goi python", "MetaTrader5 (tuy chon)", None, "chi can cho nhanh MT5")]
    ra = KP.bao_cao(ds)
    assert "  -   MetaTrader5 (tuy chon)" in ra


# ---------- kiem_may_khac ----------

def test_kiem_may_khac_khong_co_gi():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        ds = KP.kiem_may_khac(Path(td))
    ten = [x["ten"] for x in ds]
    assert "Windows.old" in ten
    assert KP.O_LUU + " (o D..H)" in ten
    assert "ds/ (git rieng, KHONG co tren GitHub)" in ten
    # khong co Windows.old trong thu muc tam
    wo = next(x for x in ds if x["ten"] == "Windows.old")
    assert wo["ok"] is None


# ---------- kiem_ma ----------

def test_kiem_ma_tra_ve_it_nhat_mot_dong():
    ds = KP.kiem_ma()
    assert isinstance(ds, list)
    assert len(ds) >= 1
    assert ds[0]["nhom"] == "ma nguon"
    assert ds[0]["ten"] == "nhanh + commit"


# ---------- chan_doan ----------

def test_chan_doan_gop_cac_nhom():
    ds = KP.chan_doan()
    nhom = {x["nhom"] for x in ds}
    assert "cong cu" in nhom
    assert "goi python" in nhom
    assert "ma nguon" in nhom
    assert "du lieu" in nhom
    assert "mt5" in nhom
    assert "kenh cloud<->may" in nhom
    assert "bi mat" in nhom
