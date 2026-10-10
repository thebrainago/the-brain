# -*- coding: utf-8 -*-
"""nhan/thu_cach_quet.py - so sanh cac CACH QUET luoi tren du lieu da quet (chu du an 07/10/2026; test 10/10/2026).

Cau hoi cua module: cach nao TIM LAI dung vung tot (top-K o) voi it phep tinh nhat? Phan "tinh logic" (`so_sanh`, `tong_hop`) la ham thuan nen
duoc kiem tren BE MAT NHAN TAO co dap an biet truoc (khong can gia, khong can nhan C):
  (1) tien de cua cach "thua roi min": tren mot be mat tron CO DINH DUY NHAT, quet thua roi mo rong quanh vai o thua tot nhat PHAI tim ra dinh
      that voi chi phi nho hon quet day, va tot hon ngau nhien o cung chi phi - neu khong thi ket luan "cach nao toi uu" cua module vo nghia;
  (2) cac con so chi phi / top-K / hang dung dinh nghia (toan bo = chi phi 1, top-K = 1, hang 0; ngau nhien X% = dung X% o);
  (3) cac the nhan khong lam sai bao cao: o -inf (chay tai khoan / khong co lai) khong keo lan can; thieu `diem_1_3` thi khong co cach hai tang;
  (4) doc don / chon don / `main` giu loi (mot don hong khong lam mat het, loi duoc ghi chu khong nuot) - khong can du lieu gia."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from nhan import thu_cach_quet as TC


def _be_mat(dai, tam):
    """Be mat tron: diem = -(khoang cach binh phuong toi `tam`); co_lai = gan tam; chay = rat xa tam."""
    toa = TC._toa_do(dai)
    diem = np.array([-float(sum((c - t) ** 2 for c, t in zip(o, tam))) for o in toa])
    return diem, diem > -12, diem < -60


# ---------------------------------------------------------------------------------------------------------------- ham nho
def test_toa_do_chu_so_cuoi_doi_nhanh_nhat():
    assert TC._toa_do([2, 3])[:4] == [(0, 0), (0, 1), (0, 2), (1, 0)]
    assert len(TC._toa_do([3, 4, 5])) == 60


def test_diem_chi_co_o_co_lai_moi_co_diem():
    assert TC._diem({"co_lai": True, "loi_suat_o_tran_pct": 12.5}) == 12.5
    assert TC._diem({"co_lai": True, "loi_suat_o_tran_pct": -3}) == -3.0                # co lai nhung o tran am van la so, khong phai -inf
    for xau in (None, {}, {"co_lai": False, "loi_suat_o_tran_pct": 9}, {"co_lai": True, "loi_suat_o_tran_pct": None},
                {"loi": "chay_tai_khoan", "co_lai": True, "loi_suat_o_tran_pct": 9}):
        assert TC._diem(xau) == -math.inf, xau


def test_top_phan_tram_chon_dung_so_o_cao_nhat_va_bo_qua_minus_inf():
    d = np.array([-math.inf, 1.0, 2.0, -math.inf, 3.0])
    assert TC._top_phan_tram(d, 0.4).tolist() == [False, False, True, False, True]    # int(5 * 0.4) = 2 o: 3,0 va 2,0
    assert TC._top_phan_tram(d, 0.01).sum() == 1                                      # luon lay it nhat 1 o


# ---------------------------------------------------------------------------------------------------------------- so_sanh
def test_toan_bo_la_chuan_chi_phi_1_top_1_hang_0():
    dai = [5, 4, 3]
    diem, co_lai, chay = _be_mat(dai, (1, 1, 1))
    kq = TC.so_sanh(diem, co_lai, chay, dai, hat=3, lan_ngau_nhien=5)
    tb = kq["toan_bo"]
    assert kq["so_o"] == 60 and tb["ti_le_chi_phi"] == 1.0 and tb["top10"] == 1.0 and tb["top50"] == 1.0
    assert tb["hang_tot_nhat_tim_duoc"] == 0 and tb["sai_lech_ti_le_co_lai"] == 0.0
    assert kq["ti_le_co_lai_that"] == pytest.approx(co_lai.mean(), abs=1e-3) and kq["ti_le_chay_tai_khoan"] == pytest.approx(chay.mean(), abs=1e-3)


def test_ngau_nhien_chi_dung_dung_ti_le_o_da_noi():
    dai = [9, 9, 9]
    diem, co_lai, chay = _be_mat(dai, (3, 5, 3))
    kq = TC.so_sanh(diem, co_lai, chay, dai, hat=0, lan_ngau_nhien=4)
    for ten, ti in (("ngau_nhien_10%", 0.1), ("ngau_nhien_20%", 0.2), ("ngau_nhien_30%", 0.3)):
        assert kq[ten]["ti_le_chi_phi"] == pytest.approx(ti, abs=0.002), ten          # chi phi = so o lay / tong, khong phu thuoc hat


def test_thua_roi_min_tim_ra_dinh_that_voi_chi_phi_nho_hon_quet_day_va_tot_hon_ngau_nhien():
    """Tien de cua ca module: be mat tron mot dinh o (3,5,3) - toa do le nen KHONG nam trong luoi thua (chi so chan + chi so cuoi)."""
    dai = [9, 9, 9]
    diem, co_lai, chay = _be_mat(dai, (3, 5, 3))
    kq = TC.so_sanh(diem, co_lai, chay, dai, hat=0, lan_ngau_nhien=20)
    toa = TC._toa_do(dai)
    dinh = int(np.argmax(diem))
    assert toa[dinh] == (3, 5, 3) and not all(c % 2 == 0 or c == 8 for c in toa[dinh])
    thua = kq["thua_roi_min_top5"]
    assert thua["hang_tot_nhat_tim_duoc"] == 0, "quet thua roi min khong tim ra dinh that"
    assert thua["top10"] == 1.0                                                         # 10 o tot nhat that deu nam trong tap da tinh
    assert thua["ti_le_chi_phi"] < 0.35                                                 # rat nho so voi quet day (1,0)
    ngau = kq["ngau_nhien_10%"]                                                         # chi phi ngau nhien 10% < thua roi min, va khong tim ra dinh
    assert ngau["ti_le_chi_phi"] < thua["ti_le_chi_phi"] and ngau["hang_tot_nhat_tim_duoc"] > 3
    assert kq["thua3_roi_min_top5"]["ti_le_chi_phi"] > thua["ti_le_chi_phi"]           # thua hon (buoc 3) -> nhieu o lan can phai bo sung


def test_thua_roi_min_kich_thuoc_tap_thua_dung_cong_thuc():
    """Neu moi o deu -inf (khong ai co lai) thi khong mo rong lan can: chi con dung tap thua = chi so chan HOAC chi so cuoi tung truc."""
    dai = [9, 9, 9]
    n = 9 ** 3
    kq = TC.so_sanh(np.full(n, -math.inf), np.zeros(n, bool), np.zeros(n, bool), dai, hat=0, lan_ngau_nhien=2)
    assert kq["thua_roi_min_top5"]["chi_phi"] == 5 ** 3                                 # moi truc: {0,2,4,6,8} (8 vua chan vua la chi so cuoi)
    assert kq["thua_roi_min_top20"]["chi_phi"] == 5 ** 3
    assert kq["thua3_roi_min_top5"]["chi_phi"] == 4 ** 3                                # moi truc: {0,3,6,8}: 8 la chi so cuoi, khong chia het 3
    dai2 = [5, 4, 3]
    kq2 = TC.so_sanh(np.full(60, -math.inf), np.zeros(60, bool), np.zeros(60, bool), dai2, hat=0, lan_ngau_nhien=2)
    assert kq2["thua_roi_min_top5"]["chi_phi"] == 3 * 3 * 2                             # {0,2,4} x {0,2,3} x {0,2}: chi so cuoi (3 / 2) cung duoc giu


def test_hai_tang_chi_phi_gom_mot_phan_ba_quet_dau_cong_so_o_da_giu():
    dai = [5, 4, 3]
    diem, co_lai, chay = _be_mat(dai, (1, 1, 1))
    kq = TC.so_sanh(diem, co_lai, chay, dai, diem_1_3=diem, co_lai_1_3=co_lai, hat=0, lan_ngau_nhien=2)
    a = kq["hai_tang_co_lai_1_3"]
    assert a["so_o"] == int(co_lai.sum()) and a["chi_phi"] == pytest.approx(60 / 3 + co_lai.sum(), abs=0.1)
    b = kq["hai_tang_top30_1_3"]
    assert b["so_o"] == int(60 * 0.3) and b["chi_phi"] == pytest.approx(60 / 3 + 18, abs=0.1)
    assert b["hang_tot_nhat_tim_duoc"] == 0                                             # dinh co mat o top 30%
    kq_khong = TC.so_sanh(diem, co_lai, chay, dai, hat=0, lan_ngau_nhien=2)
    assert "hai_tang_co_lai_1_3" not in kq_khong and "hai_tang_top30_1_3" not in kq_khong


def test_sai_lech_ti_le_co_lai_la_tuyet_doi_khong_mang_dau():
    n = 20
    diem = np.arange(n, 0, -1, dtype=float)
    co_lai = np.arange(n) < 12                                     # 12 / 20 = 0,6 o co lai
    chay = np.zeros(n, bool)
    # hai tang giu DUNG cac o KHONG co lai: tap giu co ti le co lai 0 < 0,6 -> sai lech 0,6 (khong phai -0,6 - cong thuc phai la tri tuyet doi)
    r = TC.so_sanh(diem, co_lai, chay, [5, 4], diem_1_3=diem, co_lai_1_3=~co_lai)
    assert r["hai_tang_co_lai_1_3"]["sai_lech_ti_le_co_lai"] == pytest.approx(0.6)
    # giu dung cac o co lai: ti le 1 > 0,6 -> 0,4
    r = TC.so_sanh(diem, co_lai, chay, [5, 4], diem_1_3=diem, co_lai_1_3=co_lai)
    assert r["hai_tang_co_lai_1_3"]["sai_lech_ti_le_co_lai"] == pytest.approx(0.4)
    assert r["toan_bo"]["sai_lech_ti_le_co_lai"] == 0.0


def test_bang_khong_khop_luoi_bi_tu_choi_to_tieng():
    with pytest.raises(AssertionError, match="khong khop luoi"):
        TC.so_sanh(np.zeros(10), np.zeros(10, bool), np.zeros(10, bool), [3, 4])


def test_ket_qua_cung_hat_cung_ket_qua_hat_khac_chi_ngau_nhien_doi():
    dai = [6, 5, 4]
    diem, co_lai, chay = _be_mat(dai, (2, 2, 1))
    a = TC.so_sanh(diem, co_lai, chay, dai, hat=7, lan_ngau_nhien=6)
    b = TC.so_sanh(diem, co_lai, chay, dai, hat=7, lan_ngau_nhien=6)
    c = TC.so_sanh(diem, co_lai, chay, dai, hat=8, lan_ngau_nhien=6)
    assert a == b                                                                       # xac dinh theo hat
    for k in ("toan_bo", "thua_roi_min_top5", "thua3_roi_min_top10"):
        assert a[k] == c[k], k                                                          # cac cach khong ngau nhien khong phu thuoc hat
    assert a["ngau_nhien_20%"] != c["ngau_nhien_20%"]


# ---------------------------------------------------------------------------------------------------------------- tong_hop
def test_tong_hop_la_trung_binh_tung_chi_so_cua_tung_cach():
    dai = [6, 5, 4]
    diem, co_lai, chay = _be_mat(dai, (2, 2, 1))
    d2, c2, h2 = _be_mat(dai, (4, 1, 2))
    a = TC.so_sanh(diem, co_lai, chay, dai, hat=1, lan_ngau_nhien=3)
    b = TC.so_sanh(d2, c2, h2, dai, hat=1, lan_ngau_nhien=3)
    th = TC.tong_hop([a, b])
    assert set(th) == {k for k, v in a.items() if isinstance(v, dict)}                  # chi gom cac cach (dict co chi_phi), bo cac so le
    assert th["toan_bo"]["ti_le_chi_phi"] == 1.0 and th["toan_bo"]["hang_tot_nhat_tim_duoc"] == 0.0
    for ten in ("thua_roi_min_top5", "ngau_nhien_30%"):
        for k in ("ti_le_chi_phi", "top10", "top50"):
            assert th[ten][k] == pytest.approx(round((a[ten][k] + b[ten][k]) / 2, 3), abs=1e-3), (ten, k)
    assert "so_o" not in th["toan_bo"]


# ---------------------------------------------------------------------------------------------------------------- doc don / chon don
def _don(goc: Path, ten: str, ma: str, khung: str, luoi_khoa=("buoc", "cho_lui", "tp", "tran_tang"), tool="quet_luoi", cho_bang_chung=False):
    (goc / "viec" / "xong").mkdir(parents=True, exist_ok=True)
    spec = {"ma": ma, "khung": khung, "co_dinh": {"che_do": "thua_roi_min"}, "luoi": {k: [1, 2, 3] for k in luoi_khoa}}
    lenh = ["py", "b.py", "nc", "cc", tool, json.dumps(spec)]
    d = {"ma": ten, "bang_chung": {"lenh": lenh}} if cho_bang_chung else {"ma": ten, "lenh": lenh}
    (goc / "viec" / "xong" / (ten + ".json")).write_text(json.dumps(d), encoding="utf-8")


def test_doc_don_nhan_quet_luoi_va_bo_cac_loai_khac(tmp_path):
    _don(tmp_path, "2201-a", "AUDCAD", "M15")
    _don(tmp_path, "2201-b", "AUDCAD", "M15", tool="thu_co_che")
    _don(tmp_path, "2201-c", "AUDCAD", "H1", cho_bang_chung=True)                       # `lenh` nam trong bang_chung cung duoc
    spec, ten = TC._doc_don(tmp_path / "viec" / "xong" / "2201-a.json")
    assert ten == "2201-a" and spec["ma"] == "AUDCAD" and spec["khung"] == "M15"
    assert TC._doc_don(tmp_path / "viec" / "xong" / "2201-b.json") is None
    spec_c, _ = TC._doc_don(tmp_path / "viec" / "xong" / "2201-c.json")
    assert spec_c["khung"] == "H1"
    (tmp_path / "viec" / "xong" / "2201-d.json").write_text(json.dumps({"lenh": ["py"]}), encoding="utf-8")
    assert TC._doc_don(tmp_path / "viec" / "xong" / "2201-d.json") is None             # lenh qua ngan khong lam sap


def test_chon_don_moi_khung_toi_da_hai_don_khac_nhau_m5_chi_mot(tmp_path, monkeypatch):
    monkeypatch.setattr(TC, "GOC", tmp_path)
    _don(tmp_path, "2201-a", "AUDCAD", "M15")
    _don(tmp_path, "2202-b", "EURCAD", "M15")
    _don(tmp_path, "2203-c", "AUDCAD", "M15")                                           # trung (ma, khung) voi don a -> bo
    _don(tmp_path, "2204-d", "NZDCAD", "M15")                                           # khung M15 da du 2 don -> bo
    _don(tmp_path, "2205-e", "AUDCAD", "H1")
    _don(tmp_path, "2206-f", "AUDCAD", "M5")
    _don(tmp_path, "2207-g", "EURCAD", "M5")                                            # M5 chi 1 don (chay lau)
    _don(tmp_path, "2208-h", "AUDCAD", "H4", luoi_khoa=("buoc", "tp"))                  # luoi khac dang -> bo
    _don(tmp_path, "2209-i", "AUDCAD", "D1", tool="thu_co_che")
    (tmp_path / "viec" / "xong" / "9999-ngoai.json").write_text("{}", encoding="utf-8")  # khong bat dau bang 220 -> khong xet
    chon = [ten for _, ten in TC.chon_don(10)]
    assert chon == ["2201-a", "2202-b", "2205-e", "2206-f"]
    assert [ten for _, ten in TC.chon_don(2)] == ["2201-a", "2202-b"]                   # `toi_da` cat dung chung


# ---------------------------------------------------------------------------------------------------------------- main
def _ket_qua_gia():
    dai = [5, 4, 3]
    diem, co_lai, chay = _be_mat(dai, (1, 1, 1))
    kq = TC.so_sanh(diem, co_lai, chay, dai, diem_1_3=diem, co_lai_1_3=co_lai, hat=0, lan_ngau_nhien=3)
    kq.update({"giay_day_du": 1.5, "giay_1_3": 0.5, "ty_le_giay_1_3_so_day_du": 0.333, "ma": "AUDCAD", "khung": "M15", "che_do": "thua_roi_min"})
    return kq


def test_main_ghi_bao_cao_ghi_chu_loi_don_hong_va_tra_ma_thoat_0(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(TC, "GOC", tmp_path)
    monkeypatch.setattr(TC, "chon_don", lambda toi_da: [({"ma": "A"}, "don1"), ({"ma": "B"}, "don2"), ({"ma": "C"}, "don3")])

    def chay(spec, luong=0):
        if spec["ma"] == "B":
            raise RuntimeError("khong co du lieu gia")
        return _ket_qua_gia()
    monkeypatch.setattr(TC, "chay_don", chay)
    assert TC.main(["3"]) == 0
    ra = json.loads((tmp_path / "reports" / "thu_cach_quet.json").read_text(encoding="utf-8"))
    assert [x["don"] for x in ra["cac_don"]] == ["don1", "don3"]
    assert len(ra["loi"]) == 1 and ra["loi"][0]["don"] == "don2" and "RuntimeError: khong co du lieu gia" in ra["loi"][0]["loi"]   # loi duoc GHI, khong nuot
    assert ra["tong_hop"]["toan_bo"]["ti_le_chi_phi"] == 1.0
    out = capsys.readouterr().out
    assert "xong don1" in out and "LOI don2" in out and "TONG HOP (trung binh 2 don" in out


def test_main_tat_ca_don_hong_thi_ma_thoat_1_va_khong_co_tong_hop(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(TC, "GOC", tmp_path)
    monkeypatch.setattr(TC, "chon_don", lambda toi_da: [({"ma": "A"}, "don1")])
    monkeypatch.setattr(TC, "chay_don", lambda spec, luong=0: (_ for _ in ()).throw(ValueError("x" * 500)))
    assert TC.main(["1"]) == 1
    ra = json.loads((tmp_path / "reports" / "thu_cach_quet.json").read_text(encoding="utf-8"))
    assert ra["cac_don"] == [] and ra["tong_hop"] is None and len(ra["loi"]) == 1
    assert len(ra["loi"][0]["loi"]) < 260                                               # thong bao loi bi cat gon (khong day 500 ky tu vao bao cao)
    assert "TONG HOP" not in capsys.readouterr().out


def test_chay_don_nem_loi_ro_khi_khong_co_du_lieu_gia_cua_ma():
    """`chay_don` can du lieu gia: ma khong co gia phai nem FileNotFoundError RO (de `main` ghi vao `loi`), khong tra ket qua rong / so 0."""
    with pytest.raises(FileNotFoundError, match="khong co du lieu cho KHONG_CO_MA_NAY"):
        TC.chay_don({"ma": "KHONG_CO_MA_NAY", "khung": "M15", "luoi": {"buoc": [10]}, "co_dinh": {}})
