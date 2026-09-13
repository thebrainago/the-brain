# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/ho_so_tai_san.py` - MOT CUA gop 5 ho so tai san.

Chu du an 13/09/2026 doi module nay tra loi duoc cau hoi giao dich THAT, va ba
luat bat buoc theo quy uoc du an:

  1. Ba trang thai DAT/AM/CHUA_DO_DUOC - khau do hong LUON la CHUA_DO_DUOC.
  2. Ma khong ton tai/thieu du lieu phai tra co thieu, KHONG duoc nem loi (day
     la dung tinh than "lay 3 thu chac chan CO ra thu bo do" - o day thu them
     chieu nguoc lai: mot thu chac chan KHONG CO phai duoc bo do bat duoc).
  3. `ghep_duoc` khong bao gio de mot ma tu ghep voi chinh no.

Dung DI (dependency injection, cung quy uoc `ho_so_symbol.chon_ung_vien(ho_so=...)`)
de test khong phu thuoc file that tren dia - vay test on dinh du du lieu goc co
chay lai va doi so hay khong.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import ho_so_tai_san as HT       # noqa: E402


def _tinh_cach(ma="A", hurst=0.55, nhan="HOI_QUY"):
    return {ma: {"ma": ma, "hurst": hurst, "vr10": 0.8, "ac1": -0.05,
                "nua_doi_bar": 100.0, "er": 0.09, "nhan": nhan, "so_bar": 5000}}


def _symbol(ma="A", spread=1.2, do_tin="SAN", atr=0.8):
    return {ma: {"ma": ma, "spread_bps": spread, "chi_phi_do_tin": do_tin,
                "phi_nam_mua_pct": 1.0, "phi_nam_ban_pct": -0.5,
                "atr_pct_bar": atr, "buoc_goi_y_pct": atr, "so_nam": 20.0,
                "so_bar": 5000, "tu": "2005-01-01", "den": "2025-01-01",
                "nguon": "san"}}


def _mua_vu(ma="A", dat=True, chenh=10.0, canh_bao=False):
    m3 = {"dat": dat, "chenh_bps": chenh, "p": 0.01, "nhom_cao": 3, "nhom_thap": 1}
    if canh_bao:
        m3["canh_bao_nhan"] = "nhan thu lech mot ngay"
    return {"%s|D1" % ma: {"ma": ma, "khung": "D1", "tu": "2005", "den": "2025",
                          "so_nam": 20.0, "cau_tra_loi": "CO: M3",
                          "M3_ngay_trong_tuan": m3}}


def _cap(voi, r, on_dinh=0.95):
    return {"voi": voi, "r": r, "on_dinh": on_dinh, "bar_chung": 3000}


def _tuong_quan(ma="A", cao_nhat=None, am_nhat=None, so_cap=400):
    return {"khung": "D1", "so_cap": so_cap,
           "ho_so": {ma: {"so_cap": 150, "r_trung_vi": 0.01,
                         "r_tuyet_doi_trung_vi": 0.04, "on_dinh_trung_vi": 0.9,
                         "cao_nhat": cao_nhat or [], "am_nhat": am_nhat or []}},
           "cap": {}}


def _song(ma="A", n=500, loi=None):
    if loi:
        return {"%s|H4" % ma: {"ma": ma, "khung": "H4", "loi": loi}}
    return {"%s|H4" % ma: {"ma": ma, "khung": "H4", "so_bar": 20000,
                          "song": {"so_cap_day_hoi": n,
                                  "bien_do_day_pct": {"trung_vi": 2.0},
                                  "bien_do_hoi_pct": {"trung_vi": 1.2},
                                  "ty_le_hoi_pct": {"trung_vi": 60.0},
                                  "tre_xac_nhan_bar": {"trung_vi": 3.0},
                                  "boi_atr": 2.0}}}


class HoSoDayDu(unittest.TestCase):
    """Ma co du CA 5 nguon (bom = EURUSD/XAUUSD/US500Cash that trong du an)."""

    def test_ma_co_du_lieu_tra_ho_so_day_du_5_5(self):
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(),
                     _mua_vu=_mua_vu(), _tuong_quan=_tuong_quan(), _song=_song())
        self.assertEqual(h["do_phu"], "5/5")
        for nhom in ("tinh_cach", "chi_phi_bien_do", "mua_vu", "tuong_quan", "song"):
            self.assertNotEqual(h[nhom].get("trang_thai"), HT.CHUA_DO_DUOC,
                               "nhom '%s' le ra phai co du lieu" % nhom)

    def test_mua_vu_dat_va_spread_that_thi_tinh_duoc_song_qua_spread(self):
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(spread=5.0),
                     _mua_vu=_mua_vu(chenh=10.0), _tuong_quan=_tuong_quan(), _song=_song())
        p = h["mua_vu"]["phep_thu"]["M3_ngay_trong_tuan"]
        self.assertIs(p["song_qua_spread"], True)  # 10 > 5

    def test_mua_vu_dat_nhung_khong_du_song_qua_spread(self):
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(spread=50.0),
                     _mua_vu=_mua_vu(chenh=10.0), _tuong_quan=_tuong_quan(), _song=_song())
        p = h["mua_vu"]["phep_thu"]["M3_ngay_trong_tuan"]
        self.assertIs(p["song_qua_spread"], False)  # 10 < 50

    def test_spread_KHAI_khong_ket_luan_duoc_song_qua_spread(self):
        """`chi_phi_do_tin=KHAI` la uoc mac dinh - khong du de PASS/FAIL chi phi."""
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(do_tin="KHAI"),
                     _mua_vu=_mua_vu(chenh=10.0), _tuong_quan=_tuong_quan(), _song=_song())
        p = h["mua_vu"]["phep_thu"]["M3_ngay_trong_tuan"]
        self.assertIsNone(p["song_qua_spread"])

    def test_canh_bao_lech_ngay_duoc_giu_lai(self):
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(),
                     _mua_vu=_mua_vu(canh_bao=True), _tuong_quan=_tuong_quan(), _song=_song())
        self.assertIn("canh_bao", h["mua_vu"]["phep_thu"]["M3_ngay_trong_tuan"])

    def test_song_mong_duoi_nguong_bi_canh_bao(self):
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(),
                     _mua_vu=_mua_vu(), _tuong_quan=_tuong_quan(), _song=_song(n=50))
        self.assertEqual(h["song"]["do_tin"], "MONG")
        self.assertIn("_canh_bao", h["song"])

    def test_song_du_tren_nguong_khong_canh_bao(self):
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(),
                     _mua_vu=_mua_vu(), _tuong_quan=_tuong_quan(), _song=_song(n=500))
        self.assertEqual(h["song"]["do_tin"], "DU")
        self.assertNotIn("_canh_bao", h["song"])


class MaThieuDuLieu(unittest.TestCase):
    """Luat: khau do hong la CHUA_DO_DUOC, khong phai AM, khong duoc nem loi."""

    def test_ma_khong_ton_tai_tra_co_thieu_khong_no(self):
        h = HT.ho_so("MA_BIA_DAT_KHONG_TON_TAI", "D1", _tinh_cach={}, _symbol={},
                    _mua_vu={}, _tuong_quan=_tuong_quan(ma="_khac_"), _song={})
        self.assertEqual(h["do_phu"], "0/5")
        for nhom in ("tinh_cach", "chi_phi_bien_do", "mua_vu", "tuong_quan", "song"):
            self.assertEqual(h[nhom]["trang_thai"], HT.CHUA_DO_DUOC)
            self.assertIn("vi_sao", h[nhom])

    def test_song_bao_loi_ro_rang_van_la_chua_do_duoc(self):
        """VD that: cap exotic chi co D1, zigzag H4 bao `loi` "cach nhau ~1440 phut"."""
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(),
                    _mua_vu=_mua_vu(), _tuong_quan=_tuong_quan(),
                    _song=_song(loi="ValueError: A: du lieu goc cach nhau ~1440 phut"))
        self.assertEqual(h["song"]["trang_thai"], HT.CHUA_DO_DUOC)
        self.assertIn("1440", h["song"]["vi_sao"])

    def test_tom_tat_khong_nem_loi_voi_ma_rong(self):
        # tom_tat() doc file that tren dia (khong DI) - phai chay duoc voi ma la.
        s = HT.tom_tat("MA_BIA_DAT_KHONG_TON_TAI_2", "D1")
        self.assertIn("CHUA_DO_DUOC", s)

    def test_ghep_duoc_voi_ma_thieu_tuong_quan_tra_chua_do_duoc(self):
        gd = HT.ghep_duoc("X", ho_so_da_co={"tuong_quan": {"trang_thai": HT.CHUA_DO_DUOC,
                                                          "vi_sao": "test"}})
        self.assertEqual(gd["trang_thai"], HT.CHUA_DO_DUOC)


class GhepDuocKhongTuGhepChinhNo(unittest.TestCase):

    def test_ghep_duoc_loai_chinh_no_dù_no_lot_top(self):
        """Neu du lieu (hong) dua chinh `ma` vao danh sach am/duong cua no,
        `ghep_duoc` phai tu loc no ra - khong duoc goi y "ghep X voi X"."""
        cao = [_cap("A", 0.9), _cap("B", 0.6)]
        am = [_cap("A", -0.9), _cap("C", -0.6)]
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(),
                    _mua_vu=_mua_vu(), _tuong_quan=_tuong_quan(cao_nhat=cao, am_nhat=am),
                    _song=_song())
        gd = HT.ghep_duoc("A", "D1", ho_so_da_co=h)
        self.assertNotIn("A", [x["voi"] for x in gd["am_on_dinh"]])
        self.assertNotIn("A", [x["voi"] for x in gd["trung_rui_ro"]])
        # va B/C hop le thi phai con lai
        self.assertIn("B", [x["voi"] for x in gd["trung_rui_ro"]])
        self.assertIn("C", [x["voi"] for x in gd["am_on_dinh"]])

    def test_nguong_loc_dung_am_manh_moi_qua(self):
        am = [_cap("YEU", -0.2, on_dinh=0.95), _cap("MANH", -0.7, on_dinh=0.95)]
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(),
                    _mua_vu=_mua_vu(), _tuong_quan=_tuong_quan(am_nhat=am), _song=_song())
        gd = HT.ghep_duoc("A", "D1", ho_so_da_co=h)
        self.assertEqual([x["voi"] for x in gd["am_on_dinh"]], ["MANH"])

    def test_khong_on_dinh_thi_bi_loai_du_r_cao(self):
        am = [_cap("DONG_XU", -0.8, on_dinh=0.4)]
        h = HT.ho_so("A", "D1", _tinh_cach=_tinh_cach(), _symbol=_symbol(),
                    _mua_vu=_mua_vu(), _tuong_quan=_tuong_quan(am_nhat=am), _song=_song())
        gd = HT.ghep_duoc("A", "D1", ho_so_da_co=h)
        self.assertEqual(gd["am_on_dinh"], [])


class ThongKeVaBangDungFileThat(unittest.TestCase):
    """Cham vao du lieu THAT tren dia - xac nhan cac ham chay khong loi va con
    so tra ve nhat quan noi bo (khong doi hinh dang ket qua)."""

    def test_thong_ke_tong_quan_chay_duoc_tren_kho_that(self):
        tk = HT.thong_ke_tong_quan("D1")
        self.assertGreater(tk["so_ma_tong"], 100)
        mv = tk["mua_vu"]
        self.assertGreaterEqual(mv["so_dong_ma_khung_co_dat_true"],
                               mv["trong_do_chi_phi_do_tin_DO_SAN"])
        self.assertGreaterEqual(mv["trong_do_chi_phi_do_tin_DO_SAN"],
                               mv["trong_do_song_qua_spread_cua_chinh_no"])

    def test_ho_so_ma_that_bieu_kien_XAUUSD_co_du_lieu(self):
        h = HT.ho_so("XAUUSD", "D1")
        self.assertNotEqual(h["tinh_cach"].get("trang_thai"), HT.CHUA_DO_DUOC)
        self.assertNotEqual(h["chi_phi_bien_do"].get("trang_thai"), HT.CHUA_DO_DUOC)

    def test_tom_tat_ma_that_tra_ve_chuoi_khong_rong(self):
        s = HT.tom_tat("XAUUSD", "D1")
        self.assertIsInstance(s, str)
        self.assertIn("XAUUSD", s)

    def test_chon_khong_tra_ma_trung_chinh_no_trong_ghep(self):
        uv = HT.chon({"kieu": "bat_ky", "tran": 8, "chi_phi_do_duoc": False,
                     "so_nam_min": 0.0, "spread_toi_da": None})
        self.assertIsInstance(uv, list)


class TuongQuanTaiCho(unittest.TestCase):
    """Lo hong thu 3 (bao cao 13/09/2026): bang tuong quan chi luu top-400/
    11.960 cap toan cuc + top-3 rieng moi ma - hoi mot cap TUY Y ngoai hai
    danh sach do phai TINH LAI TAI CHO, khong duoc tra "khong biet"."""

    def test_uu_tien_bang_toan_cuc_neu_co(self):
        tq = _tuong_quan(cao_nhat=[], am_nhat=[])
        tq["cap"] = {"A|B": {"r": 0.9, "bar_chung": 1000, "on_dinh": 0.95}}
        v = HT.tuong_quan("A", "B", "D1", _tuong_quan=tq)
        self.assertEqual(v["nguon"], "bang_toan_cuc_da_luu")
        self.assertEqual(v["r"], 0.9)

    def test_bang_toan_cuc_chieu_nguoc_doi_dau_r(self):
        tq = _tuong_quan(cao_nhat=[], am_nhat=[])
        tq["cap"] = {"B|A": {"r": 0.7, "bar_chung": 1000, "on_dinh": 0.9,
                            "r_min": 0.5, "r_max": 0.9}}
        v = HT.tuong_quan("A", "B", "D1", _tuong_quan=tq)
        self.assertEqual(v["r"], -0.7)
        self.assertEqual((v["r_min"], v["r_max"]), (-0.9, -0.5))

    def test_roi_xuong_top3_rieng_cua_ma_khi_khong_co_bang_toan_cuc(self):
        tq = _tuong_quan(ma="A", am_nhat=[_cap("C", -0.6, on_dinh=0.9)])
        v = HT.tuong_quan("A", "C", "D1", _tuong_quan=tq)
        self.assertEqual(v["nguon"], "top3_rieng_cua_A")
        self.assertEqual(v["r"], -0.6)

    def test_ma_trung_nhau_tra_chua_do_duoc_khong_tu_ghep(self):
        v = HT.tuong_quan("XAUUSD", "XAUUSD")
        self.assertEqual(v["trang_thai"], HT.CHUA_DO_DUOC)

    def test_ma_khong_ton_tai_tra_chua_do_duoc_khong_no(self):
        # Khong co trong bang/top-3 (DI rong) nen roi xuong nhanh TINH TAI CHO
        # tren du lieu that - ma bia dat thi phai CHUA_DO_DUOC, khong duoc nem loi.
        v = HT.tuong_quan("MA_BIA_DAT_KHONG_TON_TAI_1", "MA_BIA_DAT_KHONG_TON_TAI_2",
                          _tuong_quan=_tuong_quan(cao_nhat=[], am_nhat=[]))
        self.assertEqual(v["trang_thai"], HT.CHUA_DO_DUOC)
        self.assertIn("vi_sao", v)

    def test_tinh_tai_cho_tren_du_lieu_that_cho_cap_ngoai_bang(self):
        """Cap XAUUSD-EURPLN gan nhu chac chan khong lot top-3/top-400 (khong
        chung dong tien, khong chung chi so) - phai tinh duoc, khong "khong biet"."""
        v = HT.tuong_quan("XAUUSD", "EURPLN", "D1")
        self.assertNotEqual(v.get("trang_thai"), HT.CHUA_DO_DUOC)
        self.assertEqual(v.get("nguon"), "tinh_tai_cho (khong co trong bang da luu)")
        self.assertIn("r", v)
        self.assertGreaterEqual(v["bar_chung"], 500)

    def test_ghep_duoc_voi_doi_tac_cu_the_dung_tuong_quan(self):
        v = HT.ghep_duoc("XAUUSD", voi="USDCAD")
        self.assertIn("am_on_dinh", v)
        self.assertIn("r", v)
        self.assertEqual(v["ma"], "XAUUSD")
        self.assertEqual(v["voi"], "USDCAD")


if __name__ == "__main__":
    unittest.main()
