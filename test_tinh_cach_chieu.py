# -*- coding: utf-8 -*-
"""Test cho hai module ra doi 15/09 ma chua co nguoi kiem.

`nhan/tinh_cach_chieu.py` la cai cau noi TINH CACH TAI SAN (da do) sang CHIEU
DAT LUOI (chua ai dung). Cai phai giu bang test khong phai cong thuc - la cac
ranh gioi:

  - `TRUNG_TINH` phai ra `CHUA_DO_DUOC`, KHONG duoc ra mot chieu mac dinh. Duoi
    random walk ky vong cua luoi khong entry dung bang `-chi phi`, nen chon bua
    mot chieu la doi cai chac chan lo lay mot cai co ve 50/50.
  - `G0` (do tren khung se giao dich, co FDR) phai THANG `ho_so` (suy tu D1).
    Thu tu bang chung nay de bi dao nguoc khi ai do "don gian hoa" ham.
  - Ten tren terminal (`AUDCADmicro`) va ten trong kho (`AUDCAD`) phai cung tra
    ve mot ho so - cho lech ten nay da an mot luot tester 628 giay.

`nhan/tu_khoa_da_ngon_ngu.py` la bang tu khoa cho seeker; cai de hong nhat o mot
bang go tay la trung lap va o rong.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import tinh_cach_chieu as TCC       # noqa: E402
from nhan import tu_khoa_da_ngon_ngu as TK    # noqa: E402


def _dat_ho_so(monkeypatch, tmp_path, ho_so: dict):
    p = tmp_path / "ho_so_symbol.json"
    p.write_text(json.dumps({"ho_so": ho_so}, ensure_ascii=False),
                 encoding="utf-8")
    monkeypatch.setattr(TCC, "KHO_HO_SO", p)
    TCC._doc.cache_clear() if hasattr(TCC._doc, "cache_clear") else None


def _dat_g0(monkeypatch, tmp_path, o: list):
    p = tmp_path / "PMG_G0.json"
    p.write_text(json.dumps({"o": o}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(TCC, "BANG_G0", p)


# ------------------------------------------------------------------ CHIEU
def test_hoi_quy_ra_AGAINST_va_xu_huong_ra_WITH(monkeypatch, tmp_path):
    _dat_g0(monkeypatch, tmp_path, [])
    _dat_ho_so(monkeypatch, tmp_path, {
        "AUDCAD": {"nhan_tinh_cach": "HOI_QUY", "hurst": 0.41, "vr2": 0.8,
                   "ac1": -0.03},
        "US500Cash": {"nhan_tinh_cach": "XU_HUONG", "hurst": 0.57, "vr2": 1.2,
                      "ac1": 0.02}})
    assert TCC.chieu_luoi("AUDCAD")["chieu"] == "AGAINST"
    assert TCC.chieu_luoi("US500Cash")["chieu"] == "WITH"


def test_TRUNG_TINH_khong_duoc_tra_mot_chieu_mac_dinh(monkeypatch, tmp_path):
    """Khong nghieng ben nao thi la CHUA_DO_DUOC, khong phai tung dong xu."""
    _dat_g0(monkeypatch, tmp_path, [])
    _dat_ho_so(monkeypatch, tmp_path,
               {"EURGBP": {"nhan_tinh_cach": "TRUNG_TINH", "hurst": 0.50}})
    k = TCC.chieu_luoi("EURGBP")
    assert k["chieu"] is None
    assert k["trang_thai"] == "CHUA_DO_DUOC"


def test_khong_co_ho_so_va_khong_co_G0_la_CHUA_DO_DUOC(monkeypatch, tmp_path):
    _dat_g0(monkeypatch, tmp_path, [])
    _dat_ho_so(monkeypatch, tmp_path, {})
    k = TCC.chieu_luoi("KHONG_CO_MA_NAY")
    assert k["trang_thai"] == "CHUA_DO_DUOC" and k["chieu"] is None


def test_G0_THANG_ho_so_khi_hai_ben_noi_nguoc_nhau(monkeypatch, tmp_path):
    """Thu tu bang chung: G0 do TREN KHUNG SE GIAO DICH va co FDR."""
    _dat_ho_so(monkeypatch, tmp_path,
               {"AUDCAD": {"nhan_tinh_cach": "XU_HUONG", "hurst": 0.58}})
    _dat_g0(monkeypatch, tmp_path, [
        {"ma": "AUDCAD", "khung": "M5", "qua_fdr": True,
         "huong_de_xuat": "AGAINST"},
        {"ma": "AUDCAD", "khung": "M5", "qua_fdr": True,
         "huong_de_xuat": "AGAINST"}])
    k = TCC.chieu_luoi("AUDCAD")
    assert k["chieu"] == "AGAINST", "ho so D1 dang de len tren G0"
    assert k["do_tin"] == "G0"


def test_G0_mau_thuan_thi_khong_ket_luan(monkeypatch, tmp_path):
    _dat_ho_so(monkeypatch, tmp_path, {})
    _dat_g0(monkeypatch, tmp_path, [
        {"ma": "AUDCAD", "khung": "M5", "qua_fdr": True, "huong_de_xuat": "WITH"},
        {"ma": "AUDCAD", "khung": "M5", "qua_fdr": True,
         "huong_de_xuat": "AGAINST"}])
    assert TCC.chieu_luoi("AUDCAD")["trang_thai"] == "CHUA_DO_DUOC"


def test_ten_terminal_va_ten_kho_tra_ve_cung_mot_ho_so(monkeypatch, tmp_path):
    """`AUDCADmicro` (terminal) va `AUDCAD` (kho) la cung mot tai san."""
    _dat_g0(monkeypatch, tmp_path, [])
    _dat_ho_so(monkeypatch, tmp_path,
               {"AUDCAD": {"nhan_tinh_cach": "HOI_QUY", "hurst": 0.4,
                           "bien_do_bar_pct": 0.5, "nua_doi_bar": 30}})
    assert TCC.ho_so("AUDCADmicro") is not None
    assert TCC.chieu_luoi("AUDCADmicro")["chieu"] == "AGAINST"


# --------------------------------------------------------- BUOC / CHAN TROI
def test_buoc_toi_thieu_la_BOI_cua_bien_do_nen(monkeypatch, tmp_path):
    """Buoc hep hon bar thi moi so deu do mo hinh duong di che ra."""
    _dat_g0(monkeypatch, tmp_path, [])
    _dat_ho_so(monkeypatch, tmp_path,
               {"AUDCAD": {"nhan_tinh_cach": "HOI_QUY", "bien_do_bar_pct": 0.4}})
    k = TCC.buoc_toi_thieu_pct("AUDCAD")
    assert k["trang_thai"] == "DAT"
    assert abs(k["buoc_pct"] - 0.4 * TCC.BOI_BUOC_TOI_THIEU) < 1e-9
    assert TCC.BOI_BUOC_TOI_THIEU >= 2.0, (
        "boi duoi 2 thi bar khong con do duoc luoi - xem pmg_engine")


def test_ho_so_thieu_so_thi_CHUA_DO_DUOC_chu_khong_tra_0(monkeypatch, tmp_path):
    _dat_g0(monkeypatch, tmp_path, [])
    _dat_ho_so(monkeypatch, tmp_path,
               {"AUDCAD": {"nhan_tinh_cach": "HOI_QUY", "bien_do_bar_pct": None}})
    assert TCC.buoc_toi_thieu_pct("AUDCAD")["trang_thai"] == "CHUA_DO_DUOC"
    assert TCC.buoc_toi_thieu_pct("AUDCAD")["buoc_pct"] is None


def test_don_thuoc_gom_du_ba_cau_tra_loi(monkeypatch, tmp_path):
    """Tinh cach noi CA BA thu, khong chi chieu."""
    _dat_g0(monkeypatch, tmp_path, [])
    _dat_ho_so(monkeypatch, tmp_path,
               {"AUDCAD": {"nhan_tinh_cach": "HOI_QUY", "hurst": 0.41,
                           "bien_do_bar_pct": 0.4, "nua_doi_bar": 120}})
    d = TCC.don_thuoc("AUDCAD")
    assert "chieu" in json.dumps(d) and "buoc" in json.dumps(d)
    assert "giu" in json.dumps(d) or "chan_troi" in json.dumps(d)


# ------------------------------------------------------------ TU KHOA
def test_tu_khoa_khong_trung_va_khong_rong():
    ds = TK.tu_khoa()
    assert len(ds) > 20
    assert all(str(x).strip() for x in ds), "co tu khoa rong"
    assert len(ds) == len(set(ds)), "bang tu khoa co ban trung"


def test_theo_ngon_ngu_phu_het_NGON_NGU_khai_bao():
    """`en` la NEN, khong nam trong `NGON_NGU` (bang do liet ke thu tieng KHAC).

    Moi khoa khac `en` phai co trong khai bao - mot ma go sai o `KHAI_NIEM` se
    sinh ra mot thu tieng khong ai quet, im lang.
    """
    d = TK.theo_ngon_ngu()
    assert set(d) - {"en"} <= set(TK.NGON_NGU), (
        "co ma ngon ngu khong nam trong bang NGON_NGU")
    assert "en" in d, "mat lop tu khoa tieng Anh - do la lop nen"
    for ma, ds in d.items():
        assert ds, f"ngon ngu {ma} co o rong"


def test_loc_theo_khai_niem_thu_hep_ket_qua():
    mot = list(TK.KHAI_NIEM)[:1]
    assert len(TK.tu_khoa(mot)) < len(TK.tu_khoa()), (
        "loc theo khai niem khong thu hep gi - bo loc dang bi bo qua")


def test_bang_in_ra_duoc():
    s = TK.bang()
    assert isinstance(s, str) and len(s) > 50
