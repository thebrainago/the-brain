# -*- coding: utf-8 -*-
"""EVOLUTION — tru chiu trach nhiem nhin ra he hong, va cho toi 30/08 khong ai kiem no.

`tru/evolution.py` (531 dong) do SUC KHOE day chuyen va tu sua nhung viec da
khai bao truoc. No la lop phong thu cuoi: khi bon tru kia hong im lang, EVO la
thu duy nhat duoc cho la se len tieng. Vay ma no **khong co mot file test nao**,
va nhip tim cuoi cua no la 16/08/2026 - dung 14 ngay truoc phien nay.

Bo test do dung mot thu: **`phat_hien` co that su GAO khi co chuyen, va co that
su IM khi khong co chuyen gi.** Ca hai chieu deu can. Mot EVO khong bao gio bao
van de nao cho so lieu y het mot day chuyen khoe manh - va do la trang thai
khong phan biet duoc ma du an nay da gap o cong PASS, o null factory, va o
`plugins.yaml` ben `ds`.

`phat_hien` co doc so (dem so PASS trong ngay), nen moi bai deu tro `SO.DB`
sang CSDL TAM. Neu khong thi chinh bo test lai bom dong vao so quyet dinh that -
dung cai bay ma `test_ghi_so_fdr.py` da bat ngay 24/08.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import so as SO           # noqa: E402
from tru import evolution as EVO    # noqa: E402


def _van_hanh(**doi) -> dict:
    """Anh chup van hanh cua mot day chuyen KHOE MANH."""
    goc = {
        "tru": {
            "SEEKER": {"trang_thai": "song", "tre_giay": 60, "dung_im": False},
            "QUANTLAB": {"trang_thai": "song", "tre_giay": 30, "dung_im": False},
        },
        "so_toan_ven": {"lanh": True},
        "dia_trong_gb": 120.0,
        "seeker_ty_le_vong_rong": 0.10,
        "viec_loi": 0,
        "viec": {},
        "nguon": {"arxiv": {"trang_thai": "BAT", "lan": 5, "thu_hoach": 12}},
    }
    goc.update(doi)
    return goc


def _suc_khoe(**doi) -> dict:
    goc = {"null_ty_le_lot": 0.08, "so_ket_qua": 50, "ty_le_qua_cong": 0.02,
           "cong_co_luc": True, "null_chi_tiet": {}}
    goc.update(doi)
    return goc


def _ma(ds) -> set:
    return {d["ma"] for d in ds}


class SoTam(unittest.TestCase):
    """`phat_hien` dem so PASS trong ngay -> phai doc so TAM, khong doc so that."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._db_cu = SO.DB
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()


class ImLangKhiDayChuyenKhoe(SoTam):

    def test_khong_bao_van_de_nao_khi_moi_thu_binh_thuong(self):
        ds = EVO.phat_hien(_van_hanh(), _suc_khoe())
        self.assertEqual(_ma(ds), set(),
                         f"bao van de tren mot day chuyen khoe: {_ma(ds)}")


class GaoKhiCoChuyen(SoTam):
    """Moi bai o day chen DUNG MOT hong hoc, va doi dung mot ma van de."""

    def test_tru_dung_im_bi_bat_va_xep_muc_NANG(self):
        vh = _van_hanh(tru={
            "SEEKER": {"trang_thai": "song", "tre_giay": 60, "dung_im": False},
            "QUANTLAB": {"trang_thai": "song", "tre_giay": 99999, "dung_im": True},
        })
        ds = EVO.phat_hien(vh, _suc_khoe())
        self.assertIn("tru_dung_im_QUANTLAB", _ma(ds))
        muc = {d["ma"]: d["muc"] for d in ds}
        self.assertEqual(muc["tru_dung_im_QUANTLAB"], "NANG")

    def test_tru_chua_chay_lan_nao_bi_bat(self):
        vh = _van_hanh(tru={
            "NGHI": {"trang_thai": "CHUA CHAY LAN NAO", "tre_giay": 0},
        })
        self.assertIn("tru_chua_chay_NGHI", _ma(EVO.phat_hien(vh, _suc_khoe())))

    def test_chuoi_hash_cua_so_bi_dut_la_muc_NANG(self):
        ds = EVO.phat_hien(_van_hanh(so_toan_ven={"lanh": False}), _suc_khoe())
        self.assertIn("so_dut_chuoi", _ma(ds))
        self.assertEqual({d["ma"]: d["muc"] for d in ds}["so_dut_chuoi"], "NANG")

    def test_dia_thap_bi_bat_vi_no_khoa_buoc_kiem_tick_MT5(self):
        ds = EVO.phat_hien(_van_hanh(dia_trong_gb=9.0), _suc_khoe())
        self.assertIn("dia_thap", _ma(ds))

    def test_seeker_quay_vong_rong_bi_bat(self):
        ds = EVO.phat_hien(_van_hanh(seeker_ty_le_vong_rong=0.95), _suc_khoe())
        self.assertIn("vong_lap_rong", _ma(ds))

    def test_nhieu_viec_LOI_bi_bat(self):
        ds = EVO.phat_hien(_van_hanh(viec_loi=44), _suc_khoe())
        self.assertIn("nhieu_viec_loi", _ma(ds))


class ChotHieuChuanCong(SoTam):
    """THIET_KE muc 9 va bai hoc `cong-pass-phai-hieu-chuan-hai-chieu`."""

    def test_chua_bao_gio_do_null_ma_da_co_50_ket_qua_thi_bi_bat(self):
        sk = _suc_khoe(null_ty_le_lot=None, so_ket_qua=50)
        ds = EVO.phat_hien(_van_hanh(), sk)
        self.assertIn("chua_hieu_chuan_null", _ma(ds))

    def test_null_lot_qua_nhieu_thi_bi_bat(self):
        ds = EVO.phat_hien(_van_hanh(), _suc_khoe(null_ty_le_lot=0.45))
        self.assertIn("null_lot_qua_nhieu", _ma(ds))

    def test_it_ket_qua_thi_chua_doi_hieu_chuan_null(self):
        sk = _suc_khoe(null_ty_le_lot=None, so_ket_qua=3)
        ds = EVO.phat_hien(_van_hanh(), sk)
        self.assertNotIn("chua_hieu_chuan_null", _ma(ds),
                         "doi hieu chuan khi moi co 3 ket qua la qua som")


class ChiTuSuaNhungViecDaKhaiBao(unittest.TestCase):
    """EVO khong duoc tu y sua code. Ranh gioi nay la mot phan cua thiet ke."""

    def test_danh_sach_tu_sua_duoc_la_huu_han_va_co_mo_ta(self):
        self.assertTrue(EVO.TU_SUA_DUOC, "danh sach tu sua rong")
        for khoa, mo_ta in EVO.TU_SUA_DUOC.items():
            self.assertIsInstance(khoa, str)
            self.assertTrue(mo_ta.strip(), f"viec '{khoa}' khong co mo ta")

    def test_khong_co_viec_tu_sua_nao_dung_toi_ma_nguon(self):
        cam = ("sua_code", "ghi_file_py", "exec", "eval", "vi_ma")
        for khoa in EVO.TU_SUA_DUOC:
            for tu in cam:
                self.assertNotIn(
                    tu, khoa,
                    f"'{khoa}' cho phep EVO dong vao ma nguon - vuot ranh gioi")


class DoDiaTrong(unittest.TestCase):

    def test_dia_trong_la_so_duong(self):
        gb = EVO.dia_trong_gb()
        self.assertIsInstance(gb, float)
        self.assertGreater(gb, 0.0, "khong doc duoc dung luong dia trong")


if __name__ == "__main__":
    unittest.main()
