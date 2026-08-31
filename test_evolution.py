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
        # Them 31/08: mot day chuyen KHOE la day chuyen DO DUOC so lan restart
        # va so do bang 0. Thieu khoa nay khong phai "khoe" ma la "chua do".
        "watchdog": {"so_lan": 0, "gio": 24, "theo_rc": {}, "moi_gio": 0.0},
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


class CanhTaiNguyenVanHanh(unittest.TestCase):
    """Ba loi lam dung day chuyen ngay 30/08 deu KHONG BAO MOT LOI NAO.

    Chung khong lam he dung lai; chung lam he lang le ngung lam viec. Voi mot
    day chuyen dinh chay 24/7 khong nguoi truc thi day la loai hong nguy hiem
    nhat, va cach duy nhat bat duoc la DO chu khong doi bao loi.

    Nang nhat trong ba: `doc_gan` mo tab moi moi lan doc va khong dong tab nao.
    Do duoc **356 tab**, luot keo toan van dung han 10 phut. Sau khi don ve 6
    tab, moi trang doc het 10-13 giay thay vi ~20.
    """

    def _vh(self, **tn):
        goc = {"tab": {"cong": 9224, "so_tab": 7},
               "chrome": {"gb": 2.9, "so_tien_trinh": 19},
               "ram_dung_pct": 28.0, "ram_trong_gb": 24.0, "cpu_pct": 5.0}
        goc.update(tn)
        return _van_hanh(tai_nguyen=goc)

    def test_binh_thuong_thi_khong_bao_gi(self):
        ds = _ma(EVO.phat_hien(self._vh(), _suc_khoe()))
        for m in ("trinh_duyet_phinh_tab", "trinh_duyet_ngon_ram", "ram_may_sap_het"):
            self.assertNotIn(m, ds, f"bao '{m}' khi tai nguyen binh thuong")

    def test_tab_phinh_bi_bat_va_xep_muc_NANG(self):
        ds = EVO.phat_hien(self._vh(tab={"cong": 9224, "so_tab": 356}), _suc_khoe())
        self.assertIn("trinh_duyet_phinh_tab", _ma(ds))
        self.assertEqual({d["ma"]: d["muc"] for d in ds}["trinh_duyet_phinh_tab"],
                         "NANG")

    def test_chrome_ngon_ram_bi_bat(self):
        ds = EVO.phat_hien(self._vh(chrome={"gb": 9.5, "so_tien_trinh": 40}),
                           _suc_khoe())
        self.assertIn("trinh_duyet_ngon_ram", _ma(ds))

    def test_ram_may_sap_het_la_muc_NANG(self):
        ds = EVO.phat_hien(self._vh(ram_trong_gb=1.2), _suc_khoe())
        self.assertIn("ram_may_sap_het", _ma(ds))
        self.assertEqual({d["ma"]: d["muc"] for d in ds}["ram_may_sap_het"], "NANG")

    def test_khong_do_duoc_tai_nguyen_thi_khong_bao_bua(self):
        """psutil thieu hay CDP tat -> gia tri None. Khong duoc coi la hong."""
        ds = _ma(EVO.phat_hien(
            _van_hanh(tai_nguyen={"tab": {"cong": None, "so_tab": None},
                                  "chrome": {"gb": None, "so_tien_trinh": None}}),
            _suc_khoe()))
        for m in ("trinh_duyet_phinh_tab", "trinh_duyet_ngon_ram", "ram_may_sap_het"):
            self.assertNotIn(m, ds, f"'{m}' bao khi khong do duoc gi ca")

    def test_thieu_han_khoa_tai_nguyen_cung_khong_vo(self):
        """Ban ghi van hanh cu (truoc 30/08) khong co khoa `tai_nguyen`.

        Truoc day bai nay chi goi `phat_hien` roi khong khang dinh gi - tuc no
        tu bao PASSED ma khong kiem dieu gi. Cong hien phap bat duoc dung no.
        """
        vh = _van_hanh()
        vh.pop("tai_nguyen", None)
        ds = EVO.phat_hien(vh, _suc_khoe())     # khong duoc nem ngoai le
        self.assertIsInstance(ds, list)
        for m in ("trinh_duyet_phinh_tab", "trinh_duyet_ngon_ram", "ram_may_sap_het"):
            self.assertNotIn(m, _ma(ds),
                             f"ban ghi cu khong co so lieu ma van bao '{m}'")


# =====================================================================
# KHU TRUNG VAN DE THEO NOI DUNG (31/08/2026)
#
# Do that tren so ngay 31/08: 30 van de dang mo, **13 trong so do la
# `llm_<bam>`** va chung noi trung nhau ve dung 7 chuyen (ba chuyen chiem
# 9 dong). Nguyen nhan: `phan_tich_sau` dat ma bang `van_tay(van_ban)[:10]`,
# tuc BAM CUA CHUOI - cung mot phat hien dien dat khac di la mot dong moi,
# va cu 6 gio lai de mot lan.
#
# Bo test o day khoa HAI CHIEU, va chieu thu hai quan trong hon:
#   1. cung mot phat hien viet ba kieu -> MOT ma;
#   2. hai phat hien KHAC NHAU -> khong bao gio bi gop lam mot.
# Gop nham la MAT mot phat hien; khong gop duoc chi la mot dong thua. Hai
# loi khong ngang gia, nen nguong `NGUONG_TRUNG` dat cao va bo test phai
# chung minh duoc chieu thu hai bang MOT CON SO.
# =====================================================================

#: Nguyen van tu so ngay 31/08. Ba cach dien dat cua CUNG mot phat hien.
NULL_QUA_NHO = [
    "[LLM chan doan] Nha may null qua nho va khong dai dien de ket luan bat cu "
    "dieu gi ve hieu chuan",
    "[LLM chan doan] Khong the phan biet 'cong hieu chuan dung' voi 'cong tu "
    "choi tat ca' - nha may null qua nho de lam bang chung",
    "[LLM chan doan] Nha may null qua nho de ket luan bat cu dieu gi ve cong",
]
CONG_LOAI_SACH = [
    "[LLM chan doan] Cong loai bo ca 8 gia thuyet da vuot FDR - day la bang "
    "chung dinh luong dau tien cho gia thuyet 'cong qua chat'",
    "[LLM chan doan] Cong PASS loai sach ca 8 gia thuyet da vuot FDR - day "
    "chuyen co dau ra o tang thong ke nhung khong co gi di ra khoi cong",
    "[LLM chan doan] Co 1 gia thuyet vuot FDR nhung van bi cong loai - dau ra "
    "tang thong ke khong di duoc ra ngoai",
]
P_LECH_NULL = [
    "[LLM chan doan] Phan phoi p cua ung vien KHONG phai phan phoi null - "
    "nhung khong co gi di ra khoi day chuyen",
    "[LLM chan doan] Phan phoi p cua ung vien lech han khoi null - hoac co tin "
    "hieu that dang bi vut, hoac p-value dang tinh sai",
    "[LLM chan doan] Phan phoi p cua ung vien lech manh khoi null ma khong co "
    "gi ra khoi cong",
]
#: Bay phat hien KHAC NHAU (mot dai dien moi nhom). Khong hai cai nao duoc gop.
BAY_PHAT_HIEN_KHAC_NHAU = [
    NULL_QUA_NHO[0], CONG_LOAI_SACH[0], P_LECH_NULL[0],
    "[LLM chan doan] Nguon 'semantic' loi im: bat, chay, khong bao loi, khong "
    "thu duoc gi",
    "[LLM chan doan] Buoc kiem dinh quyet dinh (MT5 tick-test) dang bi khoa va "
    "nguong con dang tut",
    "[LLM chan doan] Mau thuan so lieu FDR giua cac tang dem",
    "[LLM chan doan] 63,6% ket qua di duong DU PHONG",
]


class MotPhatHienMotVanDe(SoTam):

    def test_ba_cach_dien_dat_cua_MOT_phat_hien_ra_MOT_ma(self):
        for ten, nhom in (("null", NULL_QUA_NHO), ("cong", CONG_LOAI_SACH),
                          ("p", P_LECH_NULL)):
            with self.subTest(nhom=ten):
                ma = {EVO.ma_chuan_van_de(x) for x in nhom}
                self.assertEqual(len(ma), 1,
                                 f"cung mot phat hien ra {len(ma)} ma: {ma}")

    def test_BAY_phat_hien_khac_nhau_KHONG_bao_gio_bi_gop(self):
        """Chieu quan trong hon. Gop nham la mat mot phat hien that."""
        ma = [EVO.ma_chuan_van_de(x) for x in BAY_PHAT_HIEN_KHAC_NHAU]
        self.assertEqual(len(set(ma)), len(ma),
                         f"hai phat hien khac nhau bi gop lam mot: {ma}")

    def test_do_trung_cheo_giua_cac_phat_hien_deu_duoi_nguong(self):
        """Bang chung SO cho bai tren, khong chi la ket qua nhi phan.

        Do that 31/08: Jaccard cheo cao nhat la 0,105 tren nguong 0,60 - tuc
        con rat xa moi cham vao tang gop theo do trung.
        """
        cao = 0.0
        for i, a in enumerate(BAY_PHAT_HIEN_KHAC_NHAU):
            for b in BAY_PHAT_HIEN_KHAC_NHAU[i + 1:]:
                cao = max(cao, EVO.trung_nhau(EVO.tap_tu(a), EVO.tap_tu(b)))
        self.assertLess(cao, EVO.NGUONG_TRUNG,
                        f"do trung cheo cao nhat {cao:.3f} da cham nguong")

    def test_doi_thu_tu_tu_va_doi_con_so_van_ra_MOT_ma(self):
        """Tang 3: bam tren TAP TU da chuan hoa, khong tren chuoi tho."""
        a = "Ban dieu khien treo 45 giay khi mo bang lon"
        b = "Khi mo bang lon, ban dieu khien treo 91 giay"
        self.assertEqual(EVO.ma_chuan_van_de(a), EVO.ma_chuan_van_de(b))

    def test_bo_dau_tieng_Viet_khong_lam_doi_ma(self):
        self.assertEqual(EVO.ma_chuan_van_de("Nhà máy null quá nhỏ để kết luận"),
                         EVO.ma_chuan_van_de("Nha may null qua nho de ket luan"))

    def test_tap_tu_rong_thi_do_trung_la_0_chu_khong_phai_1(self):
        """Hai cau rong khong phai 'giong het nhau' - do la KHONG DO DUOC."""
        self.assertEqual(EVO.trung_nhau(frozenset(), frozenset()), 0.0)
        self.assertEqual(EVO.trung_nhau(EVO.tap_tu("va cua cho"), frozenset()), 0.0)

    def test_bao_lai_cung_phat_hien_thi_DEM_TAI_PHAT_chu_khong_de_dong_moi(self):
        for x in NULL_QUA_NHO:
            EVO.bao_van_de_gop("NANG", x, {"nguon": "chan_doan"})
        mo = SO.van_de_mo()
        self.assertEqual(len(mo), 1, f"ba lan bao ra {len(mo)} dong")
        bc = EVO._doc_bang_chung(mo[0])
        self.assertEqual(bc["so_lan_tai_phat"], 3)
        self.assertEqual(len(bc["cac_dien_dat"]), 3,
                         "khong giu lai cac cach dien dat da gap")
        self.assertTrue(bc.get("lan_gan_nhat"), "khong ghi moc thoi gian gan nhat")
        self.assertTrue(bc.get("lan_dau"), "khong ghi moc thoi gian lan dau")

    def test_muc_lay_theo_muc_CAO_NHAT_da_gap(self):
        EVO.bao_van_de_gop("VUA", NULL_QUA_NHO[0])
        EVO.bao_van_de_gop("NANG", NULL_QUA_NHO[1])
        EVO.bao_van_de_gop("NHE", NULL_QUA_NHO[2])
        self.assertEqual(SO.van_de_mo()[0]["muc"], "NANG",
                         "mot lan bao NHE lam tut muc cua ca phat hien")

    def test_hai_phat_hien_khac_nhau_van_ra_hai_dong(self):
        for x in BAY_PHAT_HIEN_KHAC_NHAU:
            EVO.bao_van_de_gop("NANG", x)
        self.assertEqual(len(SO.van_de_mo()), len(BAY_PHAT_HIEN_KHAC_NHAU))


class GopVanDeTrungLapCoRanhGioi(SoTam):
    """`gop_van_de_trung_lap` la mot viec TU SUA - nen ranh gioi phai co test."""

    def _sau_dong_llm(self):
        for x in NULL_QUA_NHO + CONG_LOAI_SACH:
            SO.bao_van_de("llm_" + SO.van_tay(x)[:10], "NANG", x,
                          {"bang_chung": "so lieu", "nguon": "chan_doan"})

    def test_gop_6_dong_llm_ve_2_phat_hien(self):
        self._sau_dong_llm()
        self.assertEqual(len(SO.van_de_mo()), 6)
        EVO.gop_van_de_trung_lap()
        con = SO.van_de_mo()
        self.assertEqual(len(con), 2, f"gop xong con {len(con)} dong")
        self.assertEqual({v["ma"] for v in con},
                         {"vd_null_qua_nho", "vd_cong_loai_sach_fdr"})
        for v in con:
            self.assertEqual(EVO._doc_bang_chung(v)["so_lan_tai_phat"], 3)

    def test_KHONG_CHAY_khi_duoi_hai_dong_llm(self):
        """Dieu kien khong thoa thi ham khong duoc dong vao so mot cau nao."""
        SO.bao_van_de("llm_motminh", "NANG", NULL_QUA_NHO[0])
        SO.bao_van_de("dia_thap", "NANG", "Dia con 9 GB")
        truoc = SO.nhieu("SELECT id, ma, trang_thai FROM van_de ORDER BY id")
        self.assertEqual(EVO.gop_van_de_trung_lap(), [])
        self.assertEqual(SO.nhieu("SELECT id, ma, trang_thai FROM van_de ORDER BY id"),
                         truoc, "so bi doi khi dieu kien gop khong thoa")

    def test_KHONG_BAO_GIO_cham_van_de_khong_phai_llm(self):
        khac = ("dia_thap", "hieu_chuan_v6", "tru_dung_im_SEEKER",
                "quant_pass_quarantine_v2")
        for ma in khac:
            SO.bao_van_de(ma, "NANG", "Nha may null qua nho de ket luan gi ca")
        self._sau_dong_llm()
        EVO.gop_van_de_trung_lap()
        con = {v["ma"] for v in SO.van_de_mo()}
        for ma in khac:
            self.assertIn(ma, con, f"van de '{ma}' do nguoi/tru khac dat bi gop")

    def test_dong_bi_gop_van_giu_NGUYEN_VAN_va_mo_lai_duoc(self):
        self._sau_dong_llm()
        EVO.gop_van_de_trung_lap()
        bi_gop = SO.nhieu("SELECT ma, mo_ta, trang_thai, hanh_dong FROM van_de "
                          "WHERE trang_thai='DA_SUA'")
        self.assertEqual(len(bi_gop), 4, "so dong bi gop khong dung")
        for v in bi_gop:
            self.assertTrue(v["mo_ta"], "nguyen van bi xoa - khong dao nguoc duoc")
            self.assertIn("gop vao", v["hanh_dong"] or "",
                          "khong ghi lai no da gop vao dau")
        # DAO NGUOC: mot cau UPDATE la ve nhu cu.
        SO.chay("UPDATE van_de SET trang_thai='MO' WHERE trang_thai='DA_SUA'")
        self.assertEqual(len(SO.van_de_mo()), 6)

    def test_chay_hai_lan_khong_doi_gi_them(self):
        self._sau_dong_llm()
        EVO.gop_van_de_trung_lap()
        sau1 = SO.nhieu("SELECT id, ma, muc, trang_thai FROM van_de ORDER BY id")
        self.assertEqual(EVO.gop_van_de_trung_lap(), [])
        self.assertEqual(SO.nhieu("SELECT id, ma, muc, trang_thai FROM van_de ORDER BY id"),
                         sau1, "chay lan hai lam doi so")


class DoSupervisorRestart(unittest.TestCase):
    """EVO tung bao 'thoi gian song 7 ngay 0,0%' ma khong noi duoc VI SAO.

    Nguyen nhan goc (bat duoc 31/08/2026): supervisor chet moi 4-5 phut vi
    `os.replace` len file lease dang bi watchdog MO - WinError 5. Trieu chung
    duy nhat hien ra la `rc=1`, va khong mot traceback nao ton tai o dau ca.
    Truoc ban va con so la **~12 lan/gio va khong ai thay**.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._cu = EVO.NHAT_KY_WATCHDOG
        EVO.NHAT_KY_WATCHDOG = Path(self._tmp.name) / "watchdog.log"

    def tearDown(self):
        EVO.NHAT_KY_WATCHDOG = self._cu
        self._tmp.cleanup()

    def _viet(self, dong):
        EVO.NHAT_KY_WATCHDOG.write_text("\n".join(dong), encoding="utf-8")

    @staticmethod
    def _luc(phut_truoc):
        from datetime import datetime as _dt, timedelta as _td
        return (_dt.now() - _td(minutes=phut_truoc)).strftime("%Y-%m-%d %H:%M:%S")

    def test_khong_co_nhat_ky_thi_tra_None_CHU_KHONG_PHAI_0(self):
        """Bay da sap that ba lan trong mot phien: `da_quet=0` bao thanh
        'khong bo nao thang'. O day '0 lan restart' la tin TOT con 'khong doc
        duoc nhat ky' la tin XAU - gop hai cai lam mot la giau mat tin xau."""
        r = EVO.do_watchdog()
        self.assertIsNone(r["so_lan"])
        self.assertTrue(r.get("ly_do"))

    def test_nhat_ky_co_ma_khong_lan_chet_nao_thi_tra_0(self):
        self._viet([f"{self._luc(30)} WATCHDOG khoi dong supervisor"])
        self.assertEqual(EVO.do_watchdog()["so_lan"], 0)

    def test_dem_dung_so_lan_chet_va_gom_theo_ma_thoat(self):
        self._viet([
            f"{self._luc(200)} WATCHDOG supervisor thoat rc=1; restart sau 5s",
            f"{self._luc(150)} WATCHDOG supervisor thoat rc=1; restart sau 10s",
            f"{self._luc(100)} WATCHDOG supervisor thoat rc=4; restart sau 15s",
            f"{self._luc(50)} WATCHDOG khoi dong supervisor",
        ])
        r = EVO.do_watchdog()
        self.assertEqual(r["so_lan"], 3)
        self.assertEqual(r["theo_rc"], {"1": 2, "4": 1})

    def test_bo_qua_dong_ngoai_cua_so_24_gio(self):
        self._viet([
            f"{self._luc(60 * 40)} WATCHDOG supervisor thoat rc=1; restart sau 5s",
            f"{self._luc(30)} WATCHDOG supervisor thoat rc=1; restart sau 5s",
        ])
        self.assertEqual(EVO.do_watchdog()["so_lan"], 1)

    def test_dong_rac_khong_lam_vo_phep_do(self):
        self._viet(["khong phai dinh dang gi ca", "",
                    f"{self._luc(10)} WATCHDOG supervisor thoat rc=1; restart"])
        self.assertEqual(EVO.do_watchdog()["so_lan"], 1)


class BatVongLapChetRestart(SoTam):

    def test_restart_qua_tran_bi_bat_va_xep_muc_NANG(self):
        vh = _van_hanh(watchdog={"so_lan": EVO.TRAN_RESTART_24H + 10,
                                 "gio": 24, "theo_rc": {"1": 10},
                                 "moi_gio": 0.5})
        ds = EVO.phat_hien(vh, _suc_khoe())
        self.assertIn("supervisor_restart_lien_tuc", _ma(ds))
        self.assertEqual({d["ma"]: d["muc"] for d in ds}["supervisor_restart_lien_tuc"],
                         "NANG")

    def test_khong_restart_lan_nao_thi_IM(self):
        vh = _van_hanh(watchdog={"so_lan": 0, "gio": 24, "theo_rc": {}})
        self.assertEqual(_ma(EVO.phat_hien(vh, _suc_khoe())), set())

    def test_KHONG_DO_DUOC_khac_han_KHONG_CO_VAN_DE(self):
        vh = _van_hanh(watchdog={"so_lan": None, "ly_do": "khong co file"})
        ds = _ma(EVO.phat_hien(vh, _suc_khoe()))
        self.assertIn("watchdog_khong_do_duoc", ds)
        self.assertNotIn("supervisor_restart_lien_tuc", ds,
                         "chua do duoc ma da ket luan la hong")

    def test_ban_ghi_van_hanh_cu_khong_co_khoa_watchdog_van_bao_la_CHUA_DO(self):
        vh = _van_hanh()
        vh.pop("watchdog", None)
        ds = _ma(EVO.phat_hien(vh, _suc_khoe()))
        self.assertIn("watchdog_khong_do_duoc", ds,
                      "thieu phep do ma van im - do la giau mat mot cho mu")


class HaiViecTuSuaMoiPhaiCoRanhGioi(unittest.TestCase):
    """Hai viec them 31/08 phai DAO NGUOC DUOC va khong cham duong quyet dinh."""

    MOI = ("gop_van_de_trung_lap", "xep_hang_doc_cong_cu")

    def test_ca_hai_deu_da_duoc_khai_bao_truoc(self):
        for k in self.MOI:
            self.assertIn(k, EVO.TU_SUA_DUOC,
                          f"'{k}' chay ma khong khai bao trong TU_SUA_DUOC")

    def test_khong_viec_tu_sua_nao_cham_toi_ONG_TOA(self):
        import inspect
        nguon = (inspect.getsource(EVO.gop_van_de_trung_lap) +
                 inspect.getsource(EVO.bao_van_de_gop) +
                 inspect.getsource(EVO.tu_sua))
        for cam in ("cong.py", "chi_phi.py", "ngu_phap.py", "do_luc.py",
                    "exec(", "eval("):
            self.assertNotIn(cam, nguon,
                             f"duong tu sua co '{cam}' - vuot ranh gioi")

    def test_khong_viec_tu_sua_nao_GHI_vao_bang_quyet_dinh(self):
        import inspect
        nguon = (inspect.getsource(EVO.gop_van_de_trung_lap) +
                 inspect.getsource(EVO.bao_van_de_gop) +
                 inspect.getsource(EVO.tu_sua)).lower()
        for bang in ("ket_qua", "gia_thuyet", "fdr", "khang_dinh"):
            self.assertNotIn(f"update {bang}", nguon,
                             f"EVO tu sua dang ghi vao bang quyet dinh '{bang}'")

    def test_khong_viec_tu_sua_nao_ghi_ra_FILE_PY(self):
        import inspect
        nguon = inspect.getsource(EVO.tu_sua)
        self.assertNotIn(".py", nguon, "duong tu sua nhac toi mot file .py")
