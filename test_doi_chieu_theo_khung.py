# -*- coding: utf-8 -*-
"""nhan/doi_chieu_theo_khung.py - engine <-> MT5 theo KHUNG va theo MUC DD (doc `viec/xong/*hc-luoi-*.json`, 10/10/2026).

Cong cu nay cho ra cac con so DAT NGUONG CAT SOM ("engine <= x %/nam thi bo, MT5 lai bao nhieu") nen sai mot dau la nguong lech ma khong
ai thay. Test dung cac tep ket qua gia CUNG KHUON voi tep that (`dong_cuoi` = cac dong cuoi cua JSON in ra, `so_khoa` =
[engine %/nam, tester %/nam, DD engine, DD tester, so lenh engine, so lenh tester]; `lenh[5]` = JSON dau vao co `ma`, `khung`) va kiem:
  (1) doc dung 4 con so dau, bo qua tep khong co `so_khoa` / khong co `bang_chung`, tep `lenh` hong van doc duoc (khung "?");
  (2) cac con so trong bao cao khop phep tinh tay: cung dau, MT5>0, engine>0 nhung MT5<=0, ti so trung vi MT5/engine, DD trung vi;
  (3) bang loc theo engine va theo DD dem dung o tung nguong;
  (4) khong co du lieu thi in "n 0" chu khong do."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from nhan import doi_chieu_theo_khung as DK


def _dong_cuoi(e, mt, de, dm, n_e=100, n_t=100):
    """Giong het cac dong cuoi cua JSON that: moi phan tu mot dong, so_khoa xuong dong tung so."""
    return ["{", " \"nhan\": [", "  \"mot nhan bat ky\"", " ],", " \"so_khoa\": [", "  %s," % e, "  %s," % mt, "  %s," % de, "  %s," % dm, "  %s," % n_e,
            "  %s" % n_t, " ],", " \"tn_id\": 1,", " \"_giay\": 1.5", "}"]


def _viet(goc: Path, ten: str, e, mt, de, dm, khung="M15", ma="AUDCAD", lenh=None):
    (goc / "viec" / "xong").mkdir(parents=True, exist_ok=True)
    spec = json.dumps({"ma": ma, "khung": khung, "tu": "2019-01-01", "den": "2019-06-30"})
    d = {"ma": ten, "trang_thai": "DAT",
         "bang_chung": {"ma_thoat": 0, "dong_cuoi": _dong_cuoi(e, mt, de, dm),
                        "lenh": lenh if lenh is not None else ["py", "b.py", "nc", "cc", "hieu_chuan_luoi", spec]}}
    (goc / "viec" / "xong" / ("%s.json" % ten)).write_text(json.dumps(d), encoding="utf-8")


@pytest.fixture
def kho(tmp_path, monkeypatch):
    """Thu muc lam viec gia (module doc `viec/xong/` theo duong dan TUONG DOI nen phai chdir)."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------------------------------------------- doc()
def test_doc_lay_dung_bon_con_so_va_khung(kho):
    _viet(kho, "x-hc-luoi-a", 43.07, 23.36, 3.09, 9.54, khung="M15", ma="AUDCAD")
    (r,) = DK.doc()
    assert (r["e"], r["m"], r["de"], r["dm"]) == (43.07, 23.36, 3.09, 9.54)
    assert (r["k"], r["ma"]) == ("M15", "AUDCAD")


def test_doc_chap_nhan_so_am_va_thap_phan(kho):
    _viet(kho, "x-hc-luoi-am", -12.5, -3.25, 45.0, 60.5)
    (r,) = DK.doc()
    assert (r["e"], r["m"]) == (-12.5, -3.25)


def test_doc_chi_lay_tep_hc_luoi_va_bo_tep_khong_co_so_khoa(kho):
    _viet(kho, "x-hc-luoi-co", 1.0, 2.0, 3.0, 4.0)
    _viet(kho, "y-khong-phai-loai-nay", 1.0, 2.0, 3.0, 4.0)                           # ten khong chua hc-luoi -> bo
    xong = kho / "viec" / "xong"
    (xong / "z-hc-luoi-hong.json").write_text(json.dumps({"bang_chung": {"dong_cuoi": ["{", " \"trang_thai\": \"CHUA_DO_DUOC\"", "}"]}}), encoding="utf-8")
    (xong / "t-hc-luoi-trong.json").write_text(json.dumps({"ma": "t"}), encoding="utf-8")   # khong co bang_chung
    (xong / "u-hc-luoi-null.json").write_text(json.dumps({"bang_chung": {"dong_cuoi": None}}), encoding="utf-8")
    cac = DK.doc()
    assert len(cac) == 1 and cac[0]["e"] == 1.0


def test_lenh_hong_van_doc_duoc_voi_khung_dau_hoi(kho):
    _viet(kho, "a-hc-luoi-1", 5, 4, 10, 12, lenh=["py", "b.py"])                       # thieu lenh[5]
    _viet(kho, "b-hc-luoi-2", 5, 4, 10, 12, lenh=["py", "b.py", "nc", "cc", "x", "{khong phai json"])
    _viet(kho, "c-hc-luoi-3", 5, 4, 10, 12, lenh=["py", "b.py", "nc", "cc", "x", "{\"ma\": \"EURCAD\"}"])   # co ma, khong co khung
    r = {x["ma"] if x["ma"] else x["k"]: x for x in DK.doc()}
    assert [x["k"] for x in DK.doc()].count("?") == 3
    assert r["EURCAD"]["k"] == "?"


# ---------------------------------------------------------------------------------------------------------------- main()
def _chay_main(capsys) -> str:
    DK.main()
    return capsys.readouterr().out


def test_bao_cao_theo_khung_khop_phep_tinh_tay(kho, capsys):
    # M15: (10,5) cung dau, (8,-2) engine>0 nhung MT5<=0, (-5,-8) cung dau (hai ben am)
    _viet(kho, "m15-hc-luoi-1", 10, 5, 20, 30, khung="M15")
    _viet(kho, "m15-hc-luoi-2", 8, -2, 40, 60, khung="M15")
    _viet(kho, "m15-hc-luoi-3", -5, -8, 10, 12, khung="M15")
    _viet(kho, "m5-hc-luoi-4", 20, 10, 50, 45, khung="M5")
    ra = _chay_main(capsys).splitlines()
    assert ra[0] == "n 4"
    m15 = next(d for d in ra if d.startswith("M15"))
    m5 = next(d for d in ra if d.startswith("M5 "))
    # M15: n=3, cung dau 2/3, MT5>0: 1, engine>0 nhung MT5<=0: 1, MT5/engine trung vi = 5/10 (chi dong duong-duong), DD: dm/de = 1,5 / 1,5 / 1,2 -> 1,5
    assert "n=3" in m15 and "cung dau 2/3" in m15 and "MT5>0 1 " in m15
    assert "engine>0 nhung MT5<=0: 1" in m15 and "MT5/engine trung vi 0.5" in m15 and "DD engine/MT5 trung vi 1.5" in m15
    # M5: mot dong, MT5/engine = 10/20, DD = 45/50
    assert "n=1" in m5 and "cung dau 1/1" in m5 and "MT5/engine trung vi 0.5" in m5 and "DD engine/MT5 trung vi 0.9" in m5


def test_bang_loc_theo_engine_dem_dung_o_tung_nguong(kho, capsys):
    for i, (e, mt) in enumerate([(-12, -3), (-3, 4), (4, 12), (9, 1), (18, 30)]):      # 5 o, DD tuy y
        _viet(kho, "k-hc-luoi-%d" % i, e, mt, 5, 6)
    ra = _chay_main(capsys)
    dong = {int(l.split("<=")[1].split(":")[0]): l for l in ra.splitlines() if l.startswith("engine <=")}
    # engine <= -10: chi o 0 (MT5=-3: khong lai); <= -5: van o 0; <= 0: o 0 va o 1 (MT5=4 lai); <= 5: them o 2 (MT5=12 lai, >= 10 nen la cat nham)
    assert "n=1" in dong[-10] and "MT5>0 0" in dong[-10] and "cat nham neu MT5 >= 10: 0" in dong[-10]
    assert "n=1" in dong[-5]
    assert "n=2" in dong[0] and "MT5>0 1" in dong[0] and "cat nham neu MT5 >= 10: 0" in dong[0]
    assert "n=3" in dong[5] and "MT5>0 2" in dong[5] and "cat nham neu MT5 >= 10: 1" in dong[5]
    assert "n=4" in dong[10] and "MT5>0 3" in dong[10]                                  # them o (9,1)
    assert "n=4" in dong[15]
    assert "n=5" in dong[20] and "MT5>0 4" in dong[20] and "cat nham neu MT5 >= 10: 2" in dong[20]


def test_bang_loc_theo_dd_dem_dung_va_khong_in_phan_tram_kep(kho, capsys):
    for i, (de, dm, mt) in enumerate([(20, 30, 5), (45, 70, -1), (65, 90, -9)]):
        _viet(kho, "d-hc-luoi-%d" % i, 3, mt, de, dm)
    ra = _chay_main(capsys)
    dong = {int(l.split(">=")[1].split(":")[0]): l for l in ra.splitlines() if l.startswith("DD engine >=")}
    assert "n=3" in dong[20] and "MT5 DD trung vi 70.0" in dong[20] and "MT5 lai>0: 1" in dong[20]
    assert "n=2" in dong[40] and "MT5 DD trung vi 80.0" in dong[40] and "MT5 lai>0: 0" in dong[40]       # median(70, 90)
    assert "n=1" in dong[60] and "MT5 DD trung vi 90.0" in dong[60]
    assert "n=0" in dong[70] and "MT5 DD trung vi None" in dong[70]
    assert "%%" not in ra                                                               # 08/10 in nham '%%' nguyen van ra man hinh


def test_khong_co_du_lieu_in_n_0_va_khong_do(kho, capsys):
    ra = _chay_main(capsys)
    assert ra.splitlines()[0] == "n 0"
    assert "engine <=  -10: n=0" in ra and "DD engine >= 70: n=0" in ra


def test_khung_khong_co_dong_duong_duong_thi_ti_so_la_none(kho, capsys):
    _viet(kho, "z-hc-luoi-1", -4, -9, 10, 15, khung="H1")                              # hai ben am: khong co dong de tinh MT5/engine
    h1 = next(d for d in _chay_main(capsys).splitlines() if d.startswith("H1"))
    assert "MT5/engine trung vi None" in h1 and "cung dau 1/1" in h1


def test_dd_engine_bang_hoac_duoi_mot_khong_vao_ti_so_dd(kho, capsys):
    _viet(kho, "w-hc-luoi-1", 5, 4, 0.5, 3.0, khung="M30")                             # DD engine 0,5 <= 1: chia se vo nghia -> bo
    m30 = next(d for d in _chay_main(capsys).splitlines() if d.startswith("M30"))
    assert "DD engine/MT5 trung vi None" in m30


def test_chay_tren_tep_that_neu_co_khong_lech_so_dem(monkeypatch):
    """Tep ket qua that cua repo (neu co): moi dong doc duoc phai co du bon con so huu han, DD khong am."""
    monkeypatch.chdir(Path(__file__).resolve().parent)
    for r in DK.doc():
        assert all(isinstance(r[k], float) and r[k] == r[k] and abs(r[k]) != float("inf") for k in ("e", "m", "de", "dm")), r
        assert r["de"] >= 0 and r["dm"] >= 0, "DD khong the am: %r" % (r,)
