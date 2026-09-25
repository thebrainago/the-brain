# -*- coding: utf-8 -*-
"""Thi nghiem cua nha nghien cuu: ky luat du lieu do CODE ep, khong phai do AI tu giac."""
from __future__ import annotations

import pytest

from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN
from nhan import nc_tu_lai as TL


@pytest.fixture(autouse=True)
def so_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    yield


SPEC = {"ten": "ibs_day_bd_cao", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
        "co_che": "Ban thao cuoi bar trong bien dong cao day gia qua sau; nguoi cung cap "
                  "thanh khoan duoc tra cu hoi.",
        "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.15}},
                {"trai": {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14}, "n": 250},
                 "phep": ">", "phai": {"hang": 0.65}}]}
MA = "TONG_HOP_HOI_QUY_1"


def test_doan_niem_phong_khong_mo_bang_cua_thuong():
    d = NDL.nap(MA, "H4")
    with pytest.raises(NDL.DoanNiemPhong):
        NDL.cat_doan(d, "niem_phong")
    with pytest.raises(TN.LoiKhaiBao):
        TN.danh_gia(MA, "H4", SPEC, doan="niem_phong")
    pre, a = NDL.cat_doan(d, "xac_nhan")
    assert len(pre) == round(len(d) * 0.8) and a == round(len(d) * 0.6)


def test_khai_bao_sai_la_CHUA_DO_DUOC_khong_phai_AM():
    xau = dict(SPEC, co_che="ngan")
    r = TN.danh_gia(MA, "H4", xau)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "co_che" in r["ly_do"]
    r = TN.danh_gia(MA, "H4", SPEC, quan_tri={"sl_pct": 1})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "nut quan tri" in r["ly_do"]


def test_chay_lai_y_het_tra_ket_qua_cu_va_khong_tinh_them_phep_thu():
    r1 = TN.danh_gia(MA, "H4", SPEC)
    assert r1["trang_thai"] == "DAT" and r1["lenh"]["so_lenh"] > 100
    r2 = TN.danh_gia(MA, "H4", dict(SPEC, ten="ten_khac_cung_luat"))
    assert "tu_so_tay" in r2, "doi TEN khong phai mot phep thu moi"
    assert ST.mot("SELECT COUNT(*) n FROM thi_nghiem")["n"] == 1


def test_quan_tri_chay_qua_dap_quan_tri_va_tien_duoi_tran_dd80():
    r = TN.danh_gia(MA, "H4", SPEC, quan_tri={"sl_atr": 1.5, "tp_atr": 1.0, "thoat_bar": 3})
    assert r["trang_thai"] in ("DAT", "AM")
    t = r["tien"]
    assert t["cagr_duoi_tran_pct"] is not None and t["moc_duoi_tran_pct"] is not None
    assert t["tran_dd_pct"] == 80.0 and t["dd_pct"] < 80.0
    assert r["quan_tri"] == {"sl_atr": 1.5, "tp_atr": 1.0, "thoat_bar": 3}


def test_niem_phong_mot_lan_moi_khai_bao_va_toi_da_ba_lan_moi_dong():
    assert TN.niem_phong(MA, "H4", SPEC)["trang_thai"] == "CHUA_DO_DUOC"   # thieu gt_id
    gt = ST.them_gia_thuyet("IBS day khi bien dong cao", "thanh khoan cuoi phien duoc tra")
    r1 = TN.niem_phong(MA, "H4", SPEC, gt_id=gt, cong_that=False)
    assert r1["trang_thai"] in ("DAT", "AM", "CHUA_DO_DUOC")
    assert "sharpe_giam_phat" in r1["nhan"]
    r2 = TN.niem_phong(MA, "H4", SPEC, gt_id=gt, cong_that=False)
    assert "da_mo_truoc" in r2
    con = ST.them_gia_thuyet("bien the con", "van la y do", cha=gt)
    for i, g in enumerate((0.20, 0.25)):
        s = dict(SPEC, ten="bt%d" % i, vao=[dict(SPEC["vao"][0], phai={"hang": g}), SPEC["vao"][1]])
        TN.niem_phong(MA, "H4", s, gt_id=con, cong_that=False)
    s4 = dict(SPEC, ten="bt4", vao=[dict(SPEC["vao"][0], phai={"hang": 0.3}), SPEC["vao"][1]])
    r4 = TN.niem_phong(MA, "H4", s4, gt_id=con, cong_that=False)
    assert r4["trang_thai"] == "CHUA_DO_DUOC" and "da mo niem phong 3 lan" in r4["ly_do"]


def test_quet_dem_moi_o_la_mot_phep_thu_va_doc_hinh_dang():
    gt = ST.them_gia_thuyet("IBS day khi bien dong cao", "thanh khoan cuoi phien duoc tra")
    r = TN.quet(MA, "H4", SPEC, luoi={"vao0_phai_hang": [0.1, 0.15, 0.2],
                                      "vao1_phai_hang": [0.6, 0.65, 0.7]}, gt_id=gt)
    assert r["so_o"] == 9 and r["hinh_dang"] in ("CAO_NGUYEN", "CAI_GAI", "HON_HOP")
    assert ST.dem_phep_thu(gt_id=gt) == 9
    x = TN.quet(MA, "H4", SPEC, luoi={"khong_co": [1, 2]})
    assert x["trang_thai"] == "CHUA_DO_DUOC"


def test_mo_xe_he_goc_tim_bo_loc_bien_dong_cai_san_va_he_loc_thang_tren_xac_nhan():
    """Bai kiem cau hoi cua chu du an: AI co hoc duoc luat vao lenh tu lenh dung/lenh sai?"""
    r = TL.hoc_tu_lenh(("TONG_HOP_LOC_1",), so_null=100)[0]
    assert r["tim_ra"] and r["bo_loc"].startswith("atr_pv <"), r
    assert r["kv_loc_xn"] > 0 > r["kv_goc_xn"]
    assert r["dung"]


def test_ho_so_tai_san_nhan_ra_hoi_quy():
    h = TN.ho_so(MA, "H4")
    assert h["ti_so_phuong_sai"]["5"]["vr"] < 1.0
    assert any("HOI QUY" in g for g in h["goi_y_huong"])
