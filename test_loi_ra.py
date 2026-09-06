# -*- coding: utf-8 -*-
"""MOT TIN HIEU KHONG CO LOI RA THI CHUA PHAI MOT CHIEN LUOC.

Do tren kho 06/09/2026: 447/540 co che khong co dieu kien `ra`, va 218 trong
so do co `giu = 1` - con so mac dinh cua `sinh_tu_spec`, khong phai lua chon
cua ai. Bo do `quet_loi_ra` sinh HO LOI RA cho tung tin hieu roi chay lai ca
ho tren cac tai san CO CHI PHI DO DUOC.

Cai phai canh o day KHONG phai so hoc, ma la ba cach bo do co the suy bien
trong im lang:

  1. HO RONG. Neu `bien_the` quen mat chan troi nao thi bang tong hop van dep,
     chi la no khong bao gio thay cai no chua thu. Cung ho benh voi
     `sorted(MAU.MAU)` bo sot 321 co che ([[nap-vao-mau-truoc-khi-doc-mau]]).
  2. GHEP BAN DOI BUA. `ra_nguoc` chi dung khi hai ban THAT SU la mot cap
     mua/ban cua cung mot nguon. Ghep nham hai co che khac nhau thi loi ra
     tro thanh mot dieu kien ngau nhien, va ket qua duong tinh se vo nghia.
  3. CHON "TOT NHAT" THEO MOT O. Mot Sharpe cao tren mot tai san la ngau
     nhien; bo chon phai uu tien SO O SONG truoc, khong phai Sharpe.
"""
import unittest

import quet_loi_ra as LR
import _sua_ten_kho as ST
from nhan import ngu_phap as NP


def _spec(ten, chieu=1, nguon="a.mq5", giu=1, hang=30.0, ra=None):
    d = {"ten": ten, "ho": "quay_ve_trung_binh", "chieu": chieu, "giu": giu,
         "co_che": "mot cau du dai de qua cong kiem khai bao cua ngu phap.",
         "nguon": nguon,
         "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<",
                  "phai": {"hang": hang}}]}
    if ra:
        d["ra"] = ra
    return d


class HoLoiRaPhaiDayDu(unittest.TestCase):

    def test_moi_chan_troi_trong_HO_GIU_deu_duoc_sinh(self):
        bt = dict(LR.bien_the(_spec("x"), None))
        for g in LR.HO_GIU:
            self.assertIn("x@giu%d" % g, bt, "thieu chan troi giu%d" % g)
        self.assertEqual({s["giu"] for s in bt.values()}, set(LR.HO_GIU))

    def test_giu_goc_ngoai_HO_GIU_van_duoc_giu_lai(self):
        """Ban goc noi 'giu 50 nen' thi con so do la MOT GIA THUYET cua tac
        gia. Bo do khong duoc lang le vut no de thay bang luoi cua minh."""
        bt = dict(LR.bien_the(_spec("x", giu=50), None))
        self.assertIn("x@giu50", bt)
        self.assertEqual(bt["x@giu50"]["giu"], 50)

    def test_bien_the_khong_sua_spec_goc(self):
        goc = _spec("x", giu=7)
        LR.bien_the(goc, None)
        self.assertEqual(goc["giu"], 7, "bien_the da sua spec goc tai cho")


class GhepBanDoiPhaiChat(unittest.TestCase):

    def test_cap_mua_ban_cung_nguon_duoc_ghep(self):
        kho = [_spec("mua", 1, "f.mq5"), _spec("ban", -1, "f.mq5")]
        doi = LR.cac_ban_doi(kho)
        self.assertEqual(doi["mua"]["ten"], "ban")
        self.assertEqual(doi["ban"]["ten"], "mua")

    def test_ba_ban_cung_nguon_thi_KHONG_ghep(self):
        """Mot file ba tin hieu thi 'ban doi' la mo ho - ghep bua se dat mot
        dieu kien ngau nhien lam loi ra."""
        kho = [_spec("mua", 1, "f.mq5"), _spec("mua2", 1, "f.mq5"),
               _spec("ban", -1, "f.mq5")]
        self.assertEqual(LR.cac_ban_doi(kho), {})

    def test_khac_nguon_thi_khong_ghep(self):
        kho = [_spec("mua", 1, "f.mq5"), _spec("ban", -1, "g.mq5")]
        self.assertEqual(LR.cac_ban_doi(kho), {})

    def test_nguon_rong_khong_gom_thanh_mot_cum(self):
        """Rat nhieu co che co `nguon` rong. Neu chuoi rong duoc coi la mot
        nguon thi ca dam do thanh MOT cum va se ghep cap lung tung."""
        kho = [_spec("mua", 1, ""), _spec("ban", -1, "")]
        self.assertEqual(LR.cac_ban_doi(kho), {})

    def test_ra_nguoc_lay_dung_dieu_kien_cua_ban_doi(self):
        ban = _spec("ban", -1, "f.mq5", hang=70.0)
        bt = dict(LR.bien_the(_spec("mua", 1, "f.mq5"), ban))
        self.assertEqual(bt["mua@ra_nguoc"]["ra"], ban["vao"])
        self.assertEqual(bt["mua@ra_nguoc"]["chieu"], 1)

    def test_ra_nguoc_van_qua_duoc_cong_khai_bao(self):
        """Bien the sinh ra van phai la mot khai bao HOP LE - neu khong no se
        chet o V0 va bi doc nham thanh 'tin hieu khong co gia tri'."""
        ban = _spec("ban", -1, "f.mq5", hang=70.0)
        for ten, s in LR.bien_the(_spec("mua", 1, "f.mq5"), ban):
            self.assertEqual(NP.kiem_khai_bao(s), [], "%s hong: %s" % (ten, s))


class ChonTotNhatPhaiUuTienSoOSong(unittest.TestCase):

    @staticmethod
    def _kq(ten, giu, song, sharpe, co_ra=False):
        o = {}
        for i in range(10):
            song_o = i < song
            o["ma%d" % i] = {"ket_luan": "NEN_GOP" if song_o else "LOAI",
                             "sharpe": sharpe if song_o else None}
        return {"bien_the": ten, "goc": ten.split("@")[0], "giu": giu,
                "co_ra": co_ra, "o": o}

    def test_nhieu_o_song_thang_sharpe_cao_tren_mot_o(self):
        ra = {"ket": [self._kq("x@giu1", 1, 1, 3.0),
                      self._kq("x@giu5", 5, 6, 0.8)]}
        th = LR.tong_hop(ra)
        self.assertEqual(th["bang"][0]["tot_nhat"], "x@giu5")

    def test_dem_dung_so_co_che_doi_chan_troi(self):
        ra = {"ket": [self._kq("x@giu1", 1, 2, 0.5),
                      self._kq("x@giu5", 5, 7, 0.6),
                      self._kq("y@giu1", 1, 9, 1.0),
                      self._kq("y@giu5", 5, 3, 2.0)]}
        th = LR.tong_hop(ra)
        self.assertEqual(th["doi_chan_troi"], 1, "chi 'x' doi chan troi")
        self.assertEqual(th["chan_troi_thang"], {"giu5": 1, "giu1": 1})

    def test_diem_khong_tinh_sharpe_cua_o_da_bi_LOAI(self):
        """Mot o LOAI van co the mang mot so Sharpe trong `do`. Tinh ca no vao
        thi bo chon se uu ai dung nhung chan troi bi loai."""
        r = self._kq("x@giu1", 1, 0, 0.0)
        r["o"]["ma0"] = {"ket_luan": "LOAI", "sharpe": 9.9}
        self.assertEqual(LR._diem(r), (0, 0.0))


class KhoPhaiSachTenSauKhiBIT_CUA_SAU(unittest.TestCase):
    """`them_co_che` chuan hoa ten; duong LLM tung ghi thang vao file JSON va
    bo qua no. 125/540 ten trong kho 06/09 la du chan cua duong do."""

    def test_ten_duoc_chuan_hoa(self):
        moi, bao = ST.sua([_spec("SuperTrend Long"), _spec("x", hang=31.0)])
        self.assertEqual(moi[0]["ten"], "supertrend_long")
        self.assertEqual(bao["doi_ten"], [{"tu": "SuperTrend Long",
                                           "thanh": "supertrend_long"}])

    def test_trung_van_tay_bi_bo_du_khac_ten(self):
        """Mot dieu kien mot suat FDR - `them_co_che` da noi vay, va ban don
        dep phai noi cung mot cau."""
        moi, bao = ST.sua([_spec("a"), _spec("b")])
        self.assertEqual(len(moi), 1)
        self.assertEqual(bao["bo_trung_van_tay"][0]["trung_voi"], "a")

    def test_hai_ten_quy_ve_mot_nhung_khac_dieu_kien_thi_them_hau_to(self):
        moi, bao = ST.sua([_spec("ORB_Long", hang=30.0),
                           _spec("orb_long", hang=40.0)])
        self.assertEqual([c["ten"] for c in moi], ["orb_long", "orb_long_2"])
        self.assertEqual(len(bao["them_hau_to"]), 1)

    def test_khong_con_ten_nao_lech_chuan_sau_khi_sua(self):
        moi, _ = ST.sua(NP.doc_kho())
        lech = [c["ten"] for c in moi if c["ten"] != NP.chuan_hoa_ten(c["ten"])]
        self.assertEqual(lech, [])
        self.assertEqual(len({c["ten"] for c in moi}), len(moi), "ten trung")


class TaiSanPhaiDoDuocChiPhi(unittest.TestCase):

    def test_chi_lay_chuoi_do_tin_DO_hoac_SAN(self):
        """Chuoi KHAI khong bao gio qua duoc dieu 7 cua cong, nen mot chan troi
        'thang' tren do khong doi thanh tien duoc - quet o do la lang phi."""
        from nhan import chi_phi as CP
        ds = LR.tai_san_do_duoc("D1")
        self.assertGreater(len(ds), 20, "khong nap duoc tai san nao")
        from nhan import du_lieu as DL
        for ma in ds[:5]:
            self.assertIn(CP.tu_du_lieu(ma, DL.nap(ma, "D1")).do_tin,
                          ("DO", "SAN"))
        self.assertNotIn("YH_NASDAQ", ds, "chuoi nghien cuu lot vao be mat")


if __name__ == "__main__":
    unittest.main()
