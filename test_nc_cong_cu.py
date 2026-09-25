# -*- coding: utf-8 -*-
"""Bo cong cu cua nha nghien cuu: mot danh sach, schema dung, loi tra ve chu khong vo vong."""
from __future__ import annotations

import json

import pytest

from nhan import nc_cong_cu as CC
from nhan import nc_so_tay as ST


@pytest.fixture(autouse=True)
def so_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    monkeypatch.setattr(CC, "THU_MUC_EA", tmp_path / "nc_ea")
    monkeypatch.setattr(CC, "HANG_DOI_TESTER", tmp_path / "hd.jsonl")
    monkeypatch.setattr(CC, "YEU_CAU_SEEKER", tmp_path / "sk.jsonl")
    yield


def test_schema_api_hop_le_va_ten_duy_nhat():
    s = CC.schema_api()
    ten = [t["name"] for t in s]
    assert len(ten) == len(set(ten)) >= 14
    for t in s:
        assert t["description"] and len(t["description"]) > 40, t["name"]
        sch = t["input_schema"]
        assert sch["type"] == "object"
        assert set(sch.get("required", [])) <= set(sch["properties"]), t["name"]
    assert json.dumps(s) == json.dumps(CC.schema_api()), "thu tu co dinh de giu cache prompt"


def test_loi_dau_vao_tra_ve_loi_khong_nem():
    assert "loi" in CC.goi("khong_co_cong_cu", {})
    assert "thieu tham so" in CC.goi("thu_co_che", {"ma": "X"})["loi"]
    assert "khong co trong schema" in CC.goi("xem_so_tay", {"la": 1})["loi"]
    r = CC.goi("ghi_gia_thuyet", {"cau": "ngan", "vi_sao": "ngan"})
    assert "loi" in r


def test_ghi_so_qua_cong_cu_roi_doc_lai_trong_so_tay():
    g = CC.goi("ghi_gia_thuyet", {"cau": "EURGBP H4 hoi quy sau cu soc 1 bar",
                                   "vi_sao": "thanh khoan cheo cap mong, gia qua da"})["gt_id"]
    CC.goi("ghi_cau_hoi", {"cau": "EURGBP co hoi quy o H1 khong?", "uu_tien": 0.8, "gt_id": g})
    CC.goi("ghi_gia_thuyet", {"gt_id": g, "trang_thai": "DANG_THU"})
    md = CC.goi("xem_so_tay", {})["so_tay"]
    assert "EURGBP H4 hoi quy" in md and "EURGBP co hoi quy o H1" in md
    assert ST.mot("SELECT trang_thai FROM gia_thuyet WHERE id=?", g)["trang_thai"] == "DANG_THU"


def test_gon_giu_duoi_gioi_han():
    to = {"bang": [{"i": i, "x": "a" * 200} for i in range(500)]}
    s = CC._gon(to, 3000)
    assert len(s) <= 3000 + 10


def test_xuat_mq5_tu_choi_chuoi_tong_hop_va_khai_bao_chua_niem_phong():
    spec = {"ten": "x_y", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
            "co_che": "mot cau du dai de qua kiem cu phap cua ngu phap",
            "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.2}}]}
    r = CC.goi("xuat_mq5", {"ten": "Thu", "khung": "H4",
                            "cac": [{"ma": "TONG_HOP_HOI_QUY_1", "spec": spec},
                                    {"ma": "AUDCAD", "spec": spec}]})
    assert r["trang_thai"] == "CHUA_DO_DUOC"
    lo = " ".join(r["ly_do"])
    assert "TONG HOP" in lo and "chua DAT niem phong" in lo


def test_xuat_mq5_mang_don_bay_niem_phong_da_chot_sang_hang_doi_tester():
    """Niem phong DAT o don bay CHOT TRUOC -> tester phai chay dung muc do, khong lot tuy y."""
    from nhan import nc_thi_nghiem as TN
    spec = {"ten": "x_y", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
            "co_che": "mot cau du dai de qua kiem cu phap cua ngu phap",
            "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<", "phai": {"hang": 0.2}}]}
    s = TN.chuan_hoa_spec(spec)
    vt = ST.van_tay("niem_phong", "AUDCAD", "H4", {k: s[k] for k in ("vao", "ra", "chieu", "giu")},
                    None)
    gt = ST.them_gia_thuyet("IBS day tren AUDCAD H4", "thanh khoan cuoi bar duoc tra")
    ck = {"don_bay": 3.2, "dd_pct": 41.0, "cagr_pct": 18.5}
    with ST.ket_noi() as cn:
        cn.execute("INSERT INTO niem_phong(luc,van_tay,gt_id,ma,khung,spec,ket_qua,trang_thai) "
                   "VALUES(?,?,?,?,?,?,?,?)", (ST.bay_gio(), vt, gt, "AUDCAD", "H4", "{}",
                                               json.dumps({"tien": {"o_don_bay_cam_ket": ck}}), "DAT"))
    r = CC.goi("xuat_mq5", {"ten": "Thu", "khung": "H4", "cac": [{"ma": "AUDCAD", "spec": spec}]})
    assert r["trang_thai"] == "DAT", r
    dong = json.loads(CC.HANG_DOI_TESTER.read_text(encoding="utf-8").splitlines()[-1])
    assert dong["don_bay_cam_ket"]["AUDCAD/x_y"] == ck and dong["tran_dd_pct"] == 80.0


def test_yeu_cau_seeker_xep_hang_doi():
    r = CC.goi("yeu_cau_seeker", {"chu_de": "EA tia lenh / basket close",
                                  "tu_khoa": ["partial close grid", "basket close mql5"]})
    assert r["da_xep"] == 2


def test_thu_luoi_chi_ma_co_chi_phi_dung_va_ghi_so():
    r = CC.goi("thu_luoi", {"ma": "EURUSD", "khung": "M15", "tham_so": {"buoc": 30}})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "AUDCAD" in r["ly_do"]
    r = CC.goi("thu_luoi", {"ma": "TONG_HOP_NHIEU_1", "khung": "H1", "tham_so": {"khong_co": 1}})
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "khong biet" in r["ly_do"]
    ts = {"buoc": 40, "tp": 30, "tran_tang": 8, "che_do": "hai_chieu", "tia_lenh": True}
    r = CC.goi("thu_luoi", {"ma": "TONG_HOP_NHIEU_1", "khung": "H1", "tham_so": ts})
    assert r["trang_thai"] in ("DAT", "AM", "CHUA_DO_DUOC")
    assert "lo_treo_o_tran_pct_von" in r["tien"] and r["lenh"]["so_lenh"] > 0
    assert r["tien"]["tran_dd_pct"] == 80.0
    assert any("TONG_HOP" in c for c in r["canh_bao"])
    r2 = CC.goi("thu_luoi", {"ma": "TONG_HOP_NHIEU_1", "khung": "H1", "tham_so": ts})
    assert "tu_so_tay" in r2
