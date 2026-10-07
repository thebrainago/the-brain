# -*- coding: utf-8 -*-
"""So tay nghien cuu: bo nho ngoai cua AI - khong lap viec cu, dem phep thu theo dong."""
from __future__ import annotations

import pytest

from nhan import nc_so_tay as ST


@pytest.fixture(autouse=True)
def so_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    yield


def test_gia_thuyet_trung_ma_khong_ghi_de():
    a = ST.them_gia_thuyet("AUDCAD H4 hoi quy sau cu soc", "nguoi cung cap thanh khoan duoc tra", ma="gt_x")
    b = ST.them_gia_thuyet("cau khac", "vi sao khac", ma="gt_x")
    assert a == b
    assert ST.mot("SELECT cau FROM gia_thuyet WHERE id=?", a)["cau"].startswith("AUDCAD")


def test_dong_ho_va_dem_phep_thu_theo_DONG_chu_khong_theo_la():
    goc = ST.them_gia_thuyet("goc", "vi sao goc")
    con = ST.them_gia_thuyet("con", "vi sao con", cha=goc)
    chau = ST.them_gia_thuyet("chau", "vi sao chau", cha=con)
    khac = ST.them_gia_thuyet("khac", "vi sao khac")
    assert set(ST.dong_ho(goc)) == {goc, con, chau}
    assert ST.goc_cua(chau) == goc
    ST.ghi_thi_nghiem("quet", {}, {}, "AM", "v1", "EURGBP", "H4", "kham_pha", gt_id=con, so_phep_thu=40)
    ST.ghi_thi_nghiem("thu_co_che", {}, {}, "DAT", "v2", "EURGBP", "H4", "kham_pha", gt_id=chau)
    ST.ghi_thi_nghiem("thu_co_che", {}, {}, "DAT", "v3", "EURGBP", "H4", "xac_nhan", gt_id=chau)
    ST.ghi_thi_nghiem("thu_co_che", {}, {}, "DAT", "v4", "EURGBP", "H4", "kham_pha", gt_id=khac)
    # hoi tu CHAU van phai dem ca dong (goc + con + chau), chi tren kham_pha
    assert ST.dem_phep_thu(gt_id=chau) == 41
    assert ST.dem_phep_thu(ma="eurgbp", khung="h4") == 42


def test_da_thu_bo_qua_ket_qua_CHUA_DO_DUOC():
    ST.ghi_thi_nghiem("thu_co_che", {}, {"x": 1}, "CHUA_DO_DUOC", "vt", "A", "H4", "kham_pha")
    assert ST.da_thu("vt") == {}, "khau do hong khong duoc thanh 'da thu roi'"
    ST.ghi_thi_nghiem("thu_co_che", {}, {"x": 2}, "AM", "vt", "A", "H4", "kham_pha")
    assert ST.da_thu("vt")["ket_qua"] == {"x": 2}


def test_hieu_biet_khong_bang_chung_bi_kep_do_tin_va_bang_chung_phai_ton_tai():
    h = ST.them_hieu_biet("khong co bang chung ma rat chac", 0.95)
    assert ST.mot("SELECT do_tin FROM hieu_biet WHERE id=?", h)["do_tin"] <= 0.3
    with pytest.raises(KeyError):
        ST.them_hieu_biet("tro toi thi nghiem khong co", 0.8, [999])
    t = ST.ghi_thi_nghiem("thu_co_che", {}, {}, "DAT", "v", "A", "H4", "kham_pha")
    h2 = ST.them_hieu_biet("co bang chung", 0.8, [t])
    assert ST.mot("SELECT do_tin FROM hieu_biet WHERE id=?", h2)["do_tin"] == 0.8
    ST.bac_hieu_biet(h2, "xac nhan lat nguoc", [t])
    assert ST.mot("SELECT trang_thai FROM hieu_biet WHERE id=?", h2)["trang_thai"] == "BI_BAC"


def test_cau_hoi_cua_NGUOI_xep_truoc_va_khong_trung():
    ST.them_cau_hoi("cau cua ai uu tien cao", uu_tien=0.99)
    i = ST.them_cau_hoi("cau cua chu du an", uu_tien=0.2, nguon="nguoi")
    assert ST.them_cau_hoi("cau cua chu du an", nguon="nguoi") == i
    mo = ST.tom_tat()["cau_hoi_mo"]
    assert mo[0]["nguon"] == "nguoi"
    ST.dong_cau_hoi(i, "da tra loi")
    assert all(c["id"] != i for c in ST.tom_tat()["cau_hoi_mo"])


def test_tom_tat_md_co_du_muc_va_trang_thai_sai_bi_chan():
    ST.them_cau_hoi("cau hoi mo dau tien")
    g = ST.them_gia_thuyet("gia thuyet A", "vi sao A")
    ST.cap_nhat_gia_thuyet(g, "TRIEN_VONG", "qua xac nhan")
    with pytest.raises(ValueError):
        ST.cap_nhat_gia_thuyet(g, "THANG_LON")
    with pytest.raises(ValueError):
        ST.ghi_thi_nghiem("x", {}, {}, "TOT", "v", "", "", "")
    md = ST.tom_tat_md()
    assert "SO TAY NGHIEN CUU" in md and "Cau hoi dang mo" in md and "Gia thuyet dang song" in md
