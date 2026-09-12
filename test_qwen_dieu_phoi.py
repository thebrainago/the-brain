# -*- coding: utf-8 -*-
"""test_qwen_dieu_phoi.py - Kiem he tu chay `qwen/`. KHONG goi LLM.

He nay chay khong nguoi truc nhieu ngay, nen thu phai kiem la nhung cho no co the
im lang lam sai: cong cham nham AM cho mot khau HONG, va viec phu thuoc mot viec
hong van chay tiep.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from qwen import bang_viec as BV
from qwen import cong as CONG
from qwen import so_tay as ST

LAB = Path(__file__).resolve().parent


# ------------------------------------------------------------------ cong
def _viec(cong: dict) -> dict:
    return {"ma": "T", "ten": "thu", "cong": cong}


def test_ma_thoat_khac_khong_la_CHUA_DO_DUOC_chu_khong_phai_AM():
    """Mot tien trinh sap KHONG duoc doc thanh 'khong co edge'."""
    r = CONG.cham(_viec({"kieu": "chay_duoc"}), 4, time.time(), "Traceback...")
    assert r["ket"] == CONG.CHUA
    assert r["ket"] != CONG.AM


def test_thieu_file_ra_la_CHUA_DO_DUOC(tmp_path):
    r = CONG.cham(_viec({"kieu": "khong_rong", "file": "reports/KHONG_TON_TAI_XYZ.json"}),
                  0, time.time(), "")
    assert r["ket"] == CONG.CHUA
    assert "khong co file ra" in r["vi_sao"]


def test_file_ra_CU_hon_luc_chay_la_CHUA_DO_DUOC():
    """Doc lai ket qua cua lan truoc la cach mot con so cu di vao bao cao moi."""
    p = LAB / "reports" / "_thu_cong_cu.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps([{"lai": 1.0, "lenh": 40}]), encoding="utf-8")
    try:
        r = CONG.cham(_viec({"kieu": "chay_duoc", "file": "reports/_thu_cong_cu.json"}),
                      0, time.time() + 600, "")
        assert r["ket"] == CONG.CHUA
        assert "CU hon" in r["vi_sao"]
    finally:
        p.unlink(missing_ok=True)


def test_bay_so_1_bat_duoc_bang_co_cac_dong_giong_het_nhau():
    chet = [{"lai": 5.0, "dd": 20.0, "lenh": 30} for _ in range(8)]
    giong, ly = CONG.dong_giong_het_nhau(chet)
    assert giong, ly


def test_bay_so_1_KHONG_keu_oan_bang_co_mot_cot_hang_so_hop_le():
    """Bang that van co the co mot cot hang so (lot, von). Chan o 1 cot thi cong
    keu oan lien tuc, va mot cong keu oan mai thi nguoi ta tat no."""
    song = [{"lai": i * 1.5, "dd": 20 + i, "lenh": 30 + i, "lot": 0.1} for i in range(8)]
    giong, ly = CONG.dong_giong_het_nhau(song)
    assert not giong, ly


def test_so_lenh_duoi_25_la_AM_chu_khong_phai_DAT():
    p = LAB / "reports" / "_thu_lenh_it.json"
    p.write_text(json.dumps([{"lai": i, "lenh": 5 + i} for i in range(6)]), encoding="utf-8")
    try:
        r = CONG.cham(_viec({"kieu": "so_lenh_du", "file": "reports/_thu_lenh_it.json",
                             "toi_thieu": 25}), 0, time.time() - 1, "")
        assert r["ket"] == CONG.AM
    finally:
        p.unlink(missing_ok=True)


def test_bang_khong_co_cot_so_lenh_la_CHUA_DO_DUOC():
    """Moi bang so cua du an PHAI co so lenh. Khong co thi khong cham duoc."""
    p = LAB / "reports" / "_thu_khong_lenh.json"
    p.write_text(json.dumps([{"lai": i, "dd": 10 + i} for i in range(6)]), encoding="utf-8")
    try:
        r = CONG.cham(_viec({"kieu": "so_lenh_du", "file": "reports/_thu_khong_lenh.json"}),
                      0, time.time() - 1, "")
        assert r["ket"] == CONG.CHUA
    finally:
        p.unlink(missing_ok=True)


def test_dem_dong_dat_can_nhieu_hon_mot_ma():
    """Placebo dat tren 1 ma khong du - 5 co che 'manh tren US100' chet sach khi
    kiem cheo."""
    p = LAB / "reports" / "_thu_placebo.json"
    p.write_text(json.dumps([{"ma": "US100", "p": 0.01, "lenh": 60},
                             {"ma": "US500", "p": 0.30, "lenh": 60},
                             {"ma": "US30", "p": 0.44, "lenh": 60},
                             {"ma": "GER40", "p": 0.51, "lenh": 60}]), encoding="utf-8")
    try:
        r = CONG.cham(_viec({"kieu": "dem_dong_dat", "file": "reports/_thu_placebo.json",
                             "truong": "p", "phep": "<=", "nguong": 0.05,
                             "toi_thieu": 2}), 0, time.time() - 1, "")
        assert r["ket"] == CONG.AM, r
        assert r["so"]["dat"] == 1
    finally:
        p.unlink(missing_ok=True)


# ------------------------------------------------------------------ bang
@pytest.fixture
def bang_thu(tmp_path):
    d = {"viec": [
        {"ma": "A", "ten": "a", "lan": "NHE", "uu_tien": 1, "ngay": 1,
         "lenh": ["-c", "pass"], "cong": {"kieu": "chay_duoc"}},
        {"ma": "B", "ten": "b", "lan": "NHE", "uu_tien": 1, "ngay": 1,
         "phu_thuoc": ["A"], "lenh": ["-c", "pass"], "cong": {"kieu": "chay_duoc"}},
        {"ma": "C", "ten": "c", "lan": "NHE", "uu_tien": 1, "ngay": 1,
         "can_nguoi": True, "cong": {"kieu": "chay_duoc"}},
    ]}
    p = tmp_path / "bang.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    return BV.BangViec(p)


@pytest.fixture
def so_thu(tmp_path):
    return ST.SoTay(tmp_path / "so.json")


def test_viec_phu_thuoc_mot_viec_HONG_thi_KHONG_chay(bang_thu, so_thu):
    """Chay no se cho ra mot con so dua tren dau vao hong - va do la cach mot ket
    qua sai di vao bao cao."""
    so_thu.dat("A", trang_thai="LOI", so_lan_chay=2)
    ma = [v["ma"] for v in bang_thu.san_sang(so_thu)]
    assert "B" not in ma


def test_viec_phu_thuoc_chay_duoc_khi_viec_truoc_XONG(bang_thu, so_thu):
    so_thu.dat("A", trang_thai="XONG", so_lan_chay=1)
    ma = [v["ma"] for v in bang_thu.san_sang(so_thu)]
    assert "B" in ma


def test_viec_can_nguoi_khong_bao_gio_tu_chay(bang_thu, so_thu):
    assert "C" not in [v["ma"] for v in bang_thu.san_sang(so_thu)]
    assert "C" in [v["ma"] for v in bang_thu.ket_treo(so_thu)]


def test_bang_that_cua_du_an_nap_duoc_va_khong_co_phu_thuoc_treo():
    """Phu thuoc tro toi mot ma khong ton tai = viec do khong bao gio chay."""
    bg = BV.BangViec()
    assert len(bg.ds) >= 10
    for v in bg.ds:
        assert v.get("lenh") or v.get("can_nguoi"), \
            "%s khong co lenh ma cung khong danh dau can_nguoi -> nam im mai" % v["ma"]


def test_lan_TESTER_trong_bang_that_deu_co_han_gio():
    """Tester treo 2 gio ma chi ton 12 giay CPU (het dia) - khong han gio thi he
    dung im ca ngay."""
    for v in BV.BangViec().ds:
        if v["lan"] == "TESTER":
            assert v["toi_da_phut"] <= 480, v["ma"]


# ------------------------------------------------------------------ so tay
def test_so_tay_ghi_roc_lai_duoc(tmp_path):
    p = tmp_path / "so.json"
    s = ST.SoTay(p)
    s.dat("X", trang_thai="XONG")
    s.ghi_nhat_ky("X", "xong roi")
    assert ST.SoTay(p).trang_thai("X") == "XONG"
    assert ST.SoTay(p).d["nhat_ky"][-1]["van"] == "xong roi"


def test_viec_con_DANG_CHAY_sau_khi_may_chet_thanh_GIAN_DOAN(tmp_path):
    """Khong duoc coi la XONG (bo qua mat) cung khong duoc coi la CHUA (mat dau vet)."""
    p = tmp_path / "so.json"
    s = ST.SoTay(p)
    s.bat_dau("Y", "CPU", ["-c", "pass"])
    assert ST.don_treo(ST.SoTay(p)) == 1
    s2 = ST.SoTay(p)
    ST.don_treo(s2)
    assert s2.trang_thai("Y") == "GIAN_DOAN"


# ------------------------------------------------------------------ dieu toc
def test_dieu_toc_khong_cap_qua_muc_tieu():
    from qwen import dieu_toc as DT
    dt = DT.DieuToc({**__import__("qwen.cau_hinh", fromlist=["x"]).nap(),
                     "muc_tieu_cpu": 85.0})
    time.sleep(0.2)
    # gia vo dang chay day lan CPU -> phai tu choi phong them
    for i in range(20):
        dt.giu("gia_%d" % i, "CPU")
    duoc, ly = dt.cho_phep("CPU")
    assert not duoc, ly


def test_KHONG_lan_nao_duoc_mien_ngan_sach():
    """Ban dau toi mien lan LLM/MANG khoi ngan sach voi ly do 'chung cho mang
    chu khong an CPU'. Do la GIA DINH CHUA DO: do that luc chu du an choi game,
    mot viec lan LLM an 7,7 loi. Che do nghi ha muc tieu ve 35% ma may van 97%.
    """
    from qwen import dieu_toc as DT
    dt = DT.DieuToc()
    for i in range(20):
        dt.giu("gia_%d" % i, "CPU")
    for lan in ("LLM", "MANG", "NHE", "CPU", "TESTER"):
        duoc, ly = dt.cho_phep(lan)
        assert not duoc, "lan %s van lot qua khi ngan sach da can: %s" % (lan, ly)


def test_dieu_toc_HOC_suat_that_va_lay_max_voi_bang_khai():
    """Bang khai la chan DUOI cho lan chua chay; phep do la su that cho lan da
    chay. Lay max hai cai - uoc thap thi may nghen va nguoi phai di giet tay."""
    from qwen import dieu_toc as DT
    dt = DT.DieuToc({**__import__("qwen.cau_hinh", fromlist=["x"]).nap(),
                     "nang_lan": {"LLM": 1.2}})
    assert dt.nang("LLM") == 1.2
    dt.hoc("LLM", 7.7)
    assert dt.nang("LLM") > 1.2, "do duoc 7,7 loi ma van dung bang khai 1,2"
    # nghieng ve CAO: len nhanh, xuong cham
    truoc = dt.do_duoc["LLM"]
    dt.hoc("LLM", 0.1)
    assert dt.do_duoc["LLM"] > truoc * 0.8, "tut xuong qua nhanh sau mot phep do thap"


def test_cong_khai_SAI_khong_lam_sap_ca_vong():
    """Mot viec khai `cong` sai kieu phai bi danh CHUA_DO_DUOC, KHONG duoc nem
    loi len `mot_vong`.

    Do 12/09/2026: mot viec khai `"cong": "<chuoi>"` (thay vi dict) lam
    `spec.get` nem AttributeError, loi troi len tan `chay()` va **ca qwen dung**.
    Tren VPS chay nhieu thang thi do la chet ca he vi mot dong khai bao.
    """
    from qwen import cong as CONG
    for xau in ("mot chuoi", ["danh", "sach"], 42):
        viec = {"ma": "THU_KHAI_SAI", "ten": "thu", "lan": "NHE",
                "lenh": ["-c", "pass"], "cong": xau}
        r = CONG.cham(viec, 0, 0.0, "", None)
        assert isinstance(r, dict), "cham() phai tra dict, khong duoc nem"
        assert r.get("ket") != "DAT", "khai bao `cong` sai ma van cho DAT"
