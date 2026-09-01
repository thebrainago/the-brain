# -*- coding: utf-8 -*-
"""FRED: nguon bi bo roi 15/08 -> 01/09 vi mot header cua chinh ta.

`banker._tai` gan cung User-Agent Chrome cho moi dia chi. FRED tra 200 khi
KHONG co UA va treo den het timeout khi CO UA. Vi `_tai` nuot ngoai le va tra
None, trieu chung chi la "khong tai duoc", va ket luan **"FRED bi chan tu mang
nay"** duoc viet vao ma nguon roi ton tai 17 ngay - 12 seri vi mo nam chet, va
BANKER chay bang proxy Yahoo 2 nam thay cho so that hang chuc nam.
"""
from __future__ import annotations

import unittest

from tru import banker as B


class TaiKhongDuocDatUAChet(unittest.TestCase):
    def test_thu_khong_UA_TRUOC(self):
        """Thu tu quan trong: co UA truoc thi FRED treo het timeout moi lan."""
        import inspect
        src = inspect.getsource(B._tai)
        i_rong = src.index("({}, ")
        i_ua = src.index("UA_TRINH_DUYET", i_rong)
        self.assertLess(i_rong, i_ua, "phai thu headers rong TRUOC")

    def test_khong_con_gan_cung_UA_cho_moi_dia_chi(self):
        import inspect
        self.assertIn("for headers in", inspect.getsource(B._tai))


class SeriFredCoDuongLay(unittest.TestCase):
    def test_moi_seri_khai_bao_deu_co_ham_lay(self):
        """12 seri FRED tung nam trong so ma khong ham nao nhan - kho khai bao
        va bang tra phai khop nhau, neu khong thi im lang tra ve rong."""
        import inspect
        src = inspect.getsource(B.nap_seri)
        for ma, (nguon, *_) in B.SERI.items():
            self.assertIn(f'"{nguon}"', src, f"{ma}: nguon '{nguon}' chua co duong lay")

    def test_nguon_la_khong_duoc_lang_le_tra_rong(self):
        goc = B.SERI.get("__thu__")
        B.SERI["__thu__"] = ("nguon_bia", "x", "thu", 1, "thu")
        try:
            r = B.nap_seri("__thu__", ep=True)
            self.assertIn("loi", r)
            self.assertIn("chua co duong lay", r["loi"])
        finally:
            B.SERI.pop("__thu__", None)
            if goc:
                B.SERI["__thu__"] = goc

    def test_co_du_12_seri_fred(self):
        fred = [m for m, v in B.SERI.items() if v[0] == "fred"]
        self.assertGreaterEqual(len(fred), 12)


class NguongOiPhaiKhopTanSuat(unittest.TestCase):
    """CPI thang 8 cong bo giua thang 9: nguong 7 ngay se LUON danh no la oi,
    tuc lang le loai mot seri khoi moi phan loai che do."""

    def test_seri_thang_co_nguong_rong_hon_seri_ngay(self):
        self.assertGreater(B._nguong_tuoi("CPIAUCSL"), B._nguong_tuoi("DGS10"))
        self.assertGreater(B._nguong_tuoi("UNRATE"), B._nguong_tuoi("DGS10"))

    def test_seri_tuan_rong_hon_ngay_nhung_hep_hon_thang(self):
        self.assertGreater(B._nguong_tuoi("WALCL"), B._nguong_tuoi("DGS10"))
        self.assertLess(B._nguong_tuoi("WALCL"), B._nguong_tuoi("CPIAUCSL"))


class CheDoDungSoTHAT(unittest.TestCase):
    def setUp(self):
        self.d = B.phan_loai_che_do()

    def test_co_che_do_chi_FRED_moi_lam_duoc(self):
        for k in ("chinh_sach_tien_te", "dieu_kien_tai_chinh", "thanh_khoan",
                  "tin_dung_that"):
            self.assertIn(k, self.d["che_do"], k)

    def test_giu_CA_proxy_lan_so_that_de_doi_chieu(self):
        self.assertIn("tin_dung", self.d["che_do"])
        self.assertIn("tin_dung_that", self.d["che_do"])

    def test_moi_che_do_deu_viet_ro_QUY_TAC(self):
        for k, v in self.d["che_do"].items():
            self.assertTrue(v.get("quy_tac"), k)
            self.assertTrue(v.get("y_nghia"), k)


if __name__ == "__main__":
    unittest.main()
