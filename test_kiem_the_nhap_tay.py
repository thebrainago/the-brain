"""Test tay cho nhan.kiem_the_nhap.cham (dung the that trong kho; khong ghi tep)."""
import copy
from nhan import kiem_the_nhap as K, the_phuong_phap as TP

def _the():
    return copy.deepcopy(TP.doc("vao_ngay_lap_tuc"))

def test_the_goc_dat():
    assert K.cham(_the()) == []

def test_ma_la_khong_co_trong_kho():
    t = _the(); t["ma"] = "khong_ton_tai_xyz"
    assert K.cham(t)   # khong rong: hoac kiem_the, hoac "khong co trong kho"

def test_doi_khoa_ngoai_tham_so_bi_bat():
    t = _the(); t["mo_ta"] = "sua lung tung"
    assert any("mo_ta" in x for x in K.cham(t))

def test_thieu_mien_bi_bat():
    t = _the(); t["tham_so"][1]["mien"] = None
    assert any("thieu mien" in x for x in K.cham(t))

def test_ten_o_khong_ascii_bi_bat():
    t = _the(); t["tham_so"][1]["ten"] = "Tre Mo"
    assert any("snake_case" in x for x in K.cham(t))

def test_qua_8_o_bi_bat():
    t = _the(); o = t["tham_so"][1]; t["tham_so"] = [dict(o, ten="o_%d" % i) for i in range(9)]
    assert any("so o phai" in x for x in K.cham(t))

def test_lop_la_bi_bat():
    t = _the(); t["tham_so"][1]["lop"] = "LOP_LA"
    assert any("lop" in x for x in K.cham(t))
