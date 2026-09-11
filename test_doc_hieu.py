# -*- coding: utf-8 -*-
"""DOC VAN XUOI -> CO CHE. Bo test khoa HIEU CHUAN HAI CHIEU.

Mot bo doc tu choi TAT CA cho ra so lieu y het mot bo doc hieu chuan tot: ca
hai deu bao "0 rac". Nen moi bai kiem o day di theo cap:

  A. CAU LUAT THAT phai duoc doc RA DUNG - dung chi bao, dung chu ky, dung
     chieu, dung nguong. Doc ra "mot cai gi do" khong tinh la doc duoc.
  B. CAU BAY phai bi tu choi - va bay o day khong phai bay tuong tuong, chung
     lay tu chinh nhung gi da lot qua cac bo khop truoc cua du an nay:
       - chuoi tho: "rsi" trong "Ve-rsi-on", "orb" trong "col-orb-ar"
       - van canh chung chung: "alignment strategy" trong mot bai sinh hoc
       - chi bao ve duong bi doc thanh chien luoc vi co chu "sell signal"

Va mot bai kiem thu ba, quan trong khong kem: spec doc ra phai CHAY DUOC qua
`nhan/ngu_phap.py` va qua duoc phep cat nhin truoc tren du lieu that.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import doc_hieu as DH
from nhan import ngu_phap as NP

DEM = " Lorem ipsum dolor sit amet, a filler paragraph so the document passes the "\
      "minimum length gate used by the reader. It says nothing about trading. " * 2


def mot(vb: str):
    r = DH.doc_bai(vb + DEM, "thu", "test://vi_du")
    return r[0]["spec"] if r else None


class DocDuocCauLuatThat(unittest.TestCase):
    """CHIEU A: cau luat that phai ra DUNG spec."""

    def test_rsi2_kem_bo_loc_xu_huong(self):
        s = mot("Buy when the 2-period RSI closes below 10 and the close is "
                "above the 200-day moving average. Sell when the close crosses "
                "above the 5-day moving average. We hold for 5 days at most.")
        self.assertIsNotNone(s)
        self.assertEqual(s["chieu"], 1)
        self.assertEqual(s["giu"], 5)
        self.assertEqual(s["vao"][0]["trai"], {"chi_bao": "rsi", "n": 2})
        self.assertEqual(s["vao"][0]["phep"], "<")
        self.assertEqual(s["vao"][0]["phai"], {"hang": 10.0})
        self.assertEqual(s["vao"][1]["phep"], ">")
        self.assertEqual(s["vao"][1]["phai"]["n"], 200)
        self.assertEqual(s["ra"][0]["phep"], "cheo_len")
        self.assertEqual(s["ra"][0]["phai"]["n"], 5)

    def test_chu_ky_ghi_ro_khong_duoc_bi_thay_bang_mac_dinh(self):
        """Loi that lan chay dau: 'RSI(2)' bi doc thanh RSI mac dinh n=14 vi
        khop ngan bat dau muon hon khop dai, va phep 'lay cai cuoi cung' lay
        nham. Doc mot con so co san thanh mot con so bia ra la loi nang hon ca
        khong doc duoc."""
        for cach_viet, n in (("the 2-period RSI", 2), ("RSI(3)", 3),
                             ("the 14-day RSI", 14), ("RSI(2)", 2)):
            s = mot("Buy when %s is below 10. Exit after 3 days." % cach_viet)
            self.assertIsNotNone(s, cach_viet)
            self.assertEqual(s["vao"][0]["trai"]["n"], n, cach_viet)

    def test_vao_lenh_ban(self):
        s = mot("Go short when the close crosses below the 50-day moving average.")
        self.assertIsNotNone(s)
        self.assertEqual(s["chieu"], -1)
        self.assertEqual(s["vao"][0]["phep"], "cheo_xuong")

    def test_ban_khong_bi_doc_thanh_dong_vi_the(self):
        """'sell short' co chu 'sell'. Neu kiem RA truoc BAN thi mot chien luoc
        ban khong bien thanh mot dieu kien thoat lenh mo coi."""
        self.assertEqual(DH.loai_cau("We sell short when RSI is above 90"), "vao_ban")
        self.assertEqual(DH.loai_cau("We sell when RSI is above 90"), "ra")

    def test_dai_bollinger_thanh_zscore(self):
        """Ngu phap khong co phep tru/nhan nen 'sma - 2*sd' khong viet duoc,
        nhung zscore < -2 la TUONG DUONG, khong phai xap xi."""
        s = mot("Buy when the close falls below the lower Bollinger band.")
        self.assertIsNotNone(s)
        self.assertEqual(s["vao"][0]["trai"]["chi_bao"], "zscore")
        self.assertEqual(s["vao"][0]["trai"]["n"], 20)
        self.assertEqual(s["vao"][0]["phai"], {"hang": -2.0})

    def test_pha_vo_dinh_n_bar_phai_lui_mot_bar(self):
        """'20-day high' phai la dinh cua 20 bar TRUOC do. Neu tinh ca bar hien
        tai thi close > max(high) gan nhu khong bao gio dung - va khi no dung
        thi la do nhin truoc."""
        s = mot("Buy when the close is above the 20-day high. Hold for 10 days.")
        self.assertIsNotNone(s)
        t = s["vao"][0]["phai"]
        self.assertEqual(t["chi_bao"], "cao_nhat")
        self.assertEqual(t["n"], 20)
        self.assertEqual(t["cua"]["chi_bao"], "tre")

    def test_dang_bang_dau_dong(self):
        """Rat nhieu bai viet ta luat bang bang chu khong bang cau."""
        s = mot("Here are the rules.\nEntry: RSI(2) < 5\nExit: the close > "
                "the 10-day moving average\n")
        self.assertIsNotNone(s)
        self.assertEqual(s["vao"][0]["trai"], {"chi_bao": "rsi", "n": 2})
        self.assertEqual(s["vao"][0]["phai"], {"hang": 5.0})

    def test_ibs(self):
        s = mot("Buy when IBS is below 0.2 and hold for 1 day.")
        self.assertIsNotNone(s)
        self.assertEqual(s["vao"][0]["trai"], {"chi_bao": "ibs"})
        self.assertEqual(s["vao"][0]["phai"], {"hang": 0.2})
        self.assertEqual(s["ho"], "quay_ve_trung_binh")


class TuChoiCaiPhaiTuChoi(unittest.TestCase):
    """CHIEU B: bay phai bi tu choi."""

    def test_khong_co_nguong_thi_khong_doan(self):
        self.assertIsNone(mot("Buy when RSI is oversold and sell when it is "
                              "overbought."))

    def test_van_ban_ngoai_nganh(self):
        """Bay that: 'alignment strategy' trong mot bai sinh hoc tung duoc
        cham 2 diem 'co che' boi bo khop cu."""
        self.assertIsNone(mot(
            "The alignment strategy of ribosomes changes when the density of "
            "the initiation complex is above 30 units per micron."))

    def test_quang_cao(self):
        self.assertIsNone(mot("Buy our premium signals when you sign up today "
                              "and get 30 days free access to the channel."))

    def test_cau_co_hoac(self):
        """Ngu phap chi co VA. Doc mot cau OR thanh VA la doc SAI - nguy hiem
        hon doc thieu, vi ket qua trong nhu mot co che that."""
        self.assertIsNone(mot("Buy when the 2-period RSI is below 10 or the "
                              "close is below the 50-day moving average."))

    def test_muc_gia_tho_so_voi_hang_so(self):
        """'buy when the price is above 100' dung cu phap nhung 100 la muc gia
        cua mot ma tai mot nam - khong chuyen duoc di dau."""
        self.assertIsNone(mot("Buy when the price is above 100 and hold."))

    def test_ma_nguon_khong_di_qua_duong_van_xuoi(self):
        """Ma nguon co duong rieng. Neu tha vao day thi mot dong `if (x < 30)`
        bat ky trong mot thu vien bat ky thanh mot 'co che' hoan chinh."""
        ma = ("def on_bar(self, bar):\n"
              "    if self.rsi < 30 and self.close > self.ma:\n"
              "        self.buy(size=1);\n"
              "    return None;\n") * 12
        self.assertTrue(DH.la_ma_nguon(DH._chuan(ma)))
        self.assertEqual(DH.doc_bai(ma), [])

    def test_van_xuoi_that_khong_bi_nham_la_ma_nguon(self):
        """Bai kiem doi xung: bo loc ma nguon khong duoc an van xuoi that.
        Mot bai viet co the co dau ngoac, dau cham phay va vai cong thuc."""
        s = mot("The rules are simple; we use a short lookback. Buy when the "
                "2-period RSI (a momentum oscillator) is below 10, then exit "
                "after 5 days.")
        self.assertIsNotNone(s)


class NoiVaoNgocPhap(unittest.TestCase):
    """Spec doc ra phai CHAY DUOC, khong chi dung cu phap."""

    def test_qua_kiem_khai_bao(self):
        s = mot("Buy when the 2-period RSI closes below 10 and the close is "
                "above the 200-day moving average. Hold for 5 days.")
        self.assertEqual(NP.kiem_khai_bao(s), [])

    def test_chay_va_khong_nhin_truoc_tren_du_lieu_that(self):
        try:
            from nhan import du_lieu as DL
            df = None
            for ma in ("US500CASH", "EURCAD", "AUDNZD"):
                try:
                    d = DL.nap(ma, "D1")
                except Exception:
                    continue
                if d is not None and len(d) > 1200:
                    df = d
                    break
        except Exception:
            df = None
        if df is None:
            self.skipTest("khong co chuoi gia de kiem")
        s = mot("Buy when the 2-period RSI closes below 10 and the close is "
                "above the 200-day moving average. Sell when the close crosses "
                "above the 5-day moving average.")
        sach, mo_ta = NP.kiem_khong_nhin_truoc(s, df)
        self.assertTrue(sach, mo_ta)

    def test_van_tay_gop_ban_sao(self):
        """Hai bai ta cung mot luat = MOT co che voi hai trich dan, khong phai
        hai suat ngan sach thong ke."""
        a = mot("Buy when the 2-period RSI is below 10. Hold for 5 days.")
        b = mot("We go long once the RSI(2) is below 10. Holding period: 5 days.")
        self.assertIsNotNone(b)
        self.assertEqual(DH.van_tay_spec(a), DH.van_tay_spec(b))

    def test_van_tay_phan_biet_luat_khac_nhau(self):
        a = mot("Buy when the 2-period RSI is below 10. Hold for 5 days.")
        b = mot("Buy when the 2-period RSI is below 20. Hold for 5 days.")
        self.assertNotEqual(DH.van_tay_spec(a), DH.van_tay_spec(b))


class BonCoCheDocSaiNgay23_08(unittest.TestCase):
    """Bon co che SAI da duoc dang ky that truoc khi bi phat hien. Moi cai mot
    bai kiem, vi ca bon deu "dung cu phap" - chung chi sai NGHIA."""

    def test_thuc_the_html_khong_duoc_cat_cau(self):
        """`&apos;` chua dau CHAM PHAY, va bo tach menh de cat o dau cham phay.
        Cau "the 10-bar moving average of Bitcoin&apos;s close sits above the
        60-bar moving average" bi cat lam doi -> ve trai tu `sma10` thanh
        `close`. Phai giai ma thuc the TRUOC khi phan tich."""
        cau = ("buy when the 10-bar moving average of Bitcoin&apos;s close "
               "sits above the 60-bar moving average")
        dk, _ = DH.dieu_kien_trong_cau(DH._chuan(cau))
        self.assertTrue(dk)
        self.assertEqual(dk[0]["trai"], {"chi_bao": "sma", "n": 10, "cot": "close"})
        self.assertEqual(dk[0]["phai"]["n"], 60)

    def test_cau_ta_ca_hai_chieu_bi_tu_choi(self):
        """Lay CHIEU tu menh de sau va DIEU KIEN tu menh de truoc = ra co che
        nguoc han. Tu choi ca cau con hon doc nguoc."""
        cau = ("The strategy enters long positions when price breaks below the "
               "lower band and enters short positions when price breaks above "
               "the upper band")
        self.assertEqual(DH.dieu_kien_trong_cau(cau)[0], [])

    def test_cau_dinh_nghia_chi_bao_bi_tu_choi(self):
        cau = "RSI strategy: Buy when RSI is oversold (<30), sell when overbought (>70)"
        self.assertEqual(DH.dieu_kien_trong_cau(cau)[0], [])

    def test_luat_mot_chieu_van_phai_LOT(self):
        """Bai kiem doi xung cua hai cai tren: chan hai chieu khong duoc chan
        luon nhung cau chi noi mot chieu."""
        s = mot("We go long when the close is above the 200-day moving average. "
                "Hold for 10 days.")
        self.assertIsNotNone(s)
        self.assertEqual(s["chieu"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class HoPhaiTheoCHIEUChuKhongChiTheoTENChiBao(unittest.TestCase):
    """Do that 30/08/2026 tren mot phu de YouTube.

    Bai "GPT: Mean Reversion strategy in Python makes 813%" chua nguyen van
    "For long positions the RSI must be above 70". Bo doc trich dan DUNG, nhung
    `suy_ho` xep luat do vao ho `quay_ve_trung_binh` — chi vi thay chu "rsi".

    Mua khi RSI **tren** 70 la mua theo da manh, khong phai bat day. Cung mot
    chi bao, hai chieu la HAI CO CHE NGUOC NHAU.

    Vi sao khong phai chuyen dat ten: `ho` chon NHOM DOI CHUNG cho phep thu
    phan chung va chon ho FDR. Dem mot luat thuan xu huong di so voi nhom doi
    chung cua quay-ve-trung-binh thi phan quyet khong con nghia gi.
    """

    @staticmethod
    def _dk(chi_bao, phep, nguong, n=14):
        return [{"trai": {"chi_bao": chi_bao, "n": n},
                 "phep": phep, "phai": {"hang": float(nguong)}}]

    def test_mua_khi_RSI_THAP_la_quay_ve_trung_binh(self):
        self.assertEqual(
            DH.suy_ho(self._dk("rsi", "<", 30), chieu=1), "quay_ve_trung_binh")

    def test_mua_khi_RSI_CAO_la_XU_HUONG_chu_khong_phai_quay_ve_trung_binh(self):
        """Chinh ca sap that."""
        self.assertEqual(
            DH.suy_ho(self._dk("rsi", ">", 70), chieu=1), "xu_huong",
            "mua luc qua mua ma van xep 'bat day' -> sai nhom doi chung")

    def test_BAN_khi_RSI_CAO_la_quay_ve_trung_binh(self):
        """Ban lut dinh = bat nguoc. Neu chi nhin chieu ma bo qua phia thi sai."""
        self.assertEqual(
            DH.suy_ho(self._dk("rsi", ">", 70), chieu=-1), "quay_ve_trung_binh")

    def test_BAN_khi_RSI_THAP_la_xu_huong(self):
        self.assertEqual(
            DH.suy_ho(self._dk("rsi", "<", 30), chieu=-1), "xu_huong")

    def test_dung_cho_ca_IBS_va_zscore_va_stoch(self):
        for cb in ("ibs", "zscore", "stoch"):
            with self.subTest(chi_bao=cb):
                self.assertEqual(DH.suy_ho(self._dk(cb, "<", 20), 1),
                                 "quay_ve_trung_binh")
                self.assertEqual(DH.suy_ho(self._dk(cb, ">", 80), 1),
                                 "xu_huong")

    def test_nguong_dat_ben_TRAI_thi_phia_phai_lat_lai(self):
        """`70 < rsi` cung nghia voi `rsi > 70`. Doc sai ve la xep nguoc ho."""
        dk = [{"trai": {"hang": 70.0}, "phep": "<",
               "phai": {"chi_bao": "rsi", "n": 14}}]
        self.assertEqual(DH.suy_ho(dk, chieu=1), "xu_huong")

    def test_so_hai_CHI_BAO_voi_nhau_thi_KHONG_DOAN_ho(self):
        """Khong co hang so thi khong co 'phia'. Doan bua o day la xep nham."""
        dk = [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": ">",
               "phai": {"chi_bao": "rsi", "n": 50}}]
        self.assertEqual(DH.suy_ho(dk, chieu=1), "khac")

    def test_chi_bao_KHONG_dao_dong_giu_nguyen_cach_xep_cu(self):
        """Chi sua nhom dao dong; pha_vo / xu_huong / lich khong duoc lay theo."""
        self.assertEqual(
            DH.suy_ho([{"trai": {"chi_bao": "cao_nhat", "n": 20}, "phep": ">",
                        "phai": {"hang": 0.0}}], 1), "pha_vo")
        self.assertEqual(
            DH.suy_ho([{"trai": {"chi_bao": "ngay_trong_thang"}, "phep": "<",
                        "phai": {"hang": 5.0}}], 1), "lich")

    def test_moi_ho_tra_ve_deu_nam_trong_HO_HOP_LE(self):
        """Mot ho la la se bi `ngu_phap` tu choi o cuoi duong — im lang mat bai."""
        from nhan.ngu_phap import HO_HOP_LE
        for cb in ("rsi", "ibs", "zscore", "stoch", "cao_nhat", "sma", "atr"):
            for phep in ("<", ">"):
                for ch in (1, -1):
                    self.assertIn(DH.suy_ho(self._dk(cb, phep, 50), ch),
                                  HO_HOP_LE)


class DaiTuTroVeChiBaoNeuOVeTRUOC(unittest.TestCase):
    """Mot trong hai hinh dang luat THAT ma bo doc con mu (do kho 30/08/2026).

    "The first example is a 2-day RSI strategy where we buy when **it** crosses
    below 15" — ten chi bao va chu ky deu co trong cau, nhung `_vung_dieu_kien`
    cat het phan truoc chu "when" nen chung bi vut di.
    """

    @staticmethod
    def _dk(cau):
        pv, _ = DH.tach_vao_ra(cau)
        dk, _ = DH.dieu_kien_trong_cau(pv)
        dk, _ = DH.loc_dieu_kien(dk)
        return dk

    def test_doc_duoc_luat_viet_bang_dai_tu(self):
        dk = self._dk("The first example is a 2-day RSI strategy where we buy "
                      "when it crosses below 15")
        self.assertTrue(dk, "cau luat that van khong doc duoc")
        self.assertEqual(dk[0]["trai"]["chi_bao"], "rsi")
        self.assertEqual(dk[0]["phai"]["hang"], 15.0)

    def test_GIU_DUNG_CHU_KY_chu_khong_roi_ve_mac_dinh_14(self):
        """Bai nay quan trong hon bai tren.

        Xep cum theo vi tri BAT DAU thi "RSI" tran thang "2-day RSI" va he ghi
        `n=14` cho mot bai noi RSI(2). Khong loi nao bao, va hai cai do la HAI
        CO CHE KHAC HAN: RSI(2)<15 la edge Connors co that, RSI(14)<15 gan nhu
        khong bao gio kich hoat. Tuc he se dang ky mot gia thuyet KHONG AI
        PHAT BIEU roi tieu mot suat FDR cho no.
        """
        for cau, n in (
                ("The first example is a 2-day RSI strategy where we buy "
                 "when it crosses below 15", 2),
                ("This is a 2-period RSI strategy and we go long when it "
                 "falls below 10", 2),
                ("We use a 14-day RSI and buy when it drops under 30", 14)):
            with self.subTest(chu_ky=n):
                dk = self._dk(cau)
                self.assertTrue(dk)
                self.assertEqual(dk[0]["trai"]["n"], n,
                                 "lay nham chu ky -> kiem dinh mot luat khac")

    def test_vung_dieu_kien_DA_co_chi_bao_thi_KHONG_dung_cham(self):
        """Dai tu luc do tro thu khac; thay bua la bia ra mot luat moi."""
        c = "Buy the index when it is above the 200-day moving average"
        self.assertEqual(DH._go_dai_tu(c), c)

    def test_khong_co_chi_bao_nao_o_ve_truoc_thi_KHONG_doan(self):
        c = "Buy the stock when it is a good day"
        self.assertEqual(DH._go_dai_tu(c), c)
        self.assertFalse(self._dk(c), "doan bua ra mot luat tu mot cau vo nghia")

    def test_khong_co_dai_tu_thi_cau_giu_nguyen_TUNG_KY_TU(self):
        for c in ("We buy when the RSI crosses below 15",
                  "Go long when the 50 SMA crosses above the 200 SMA"):
            with self.subTest(cau=c):
                self.assertEqual(DH._go_dai_tu(c), c)

    def test_luat_viet_thang_van_doc_duoc_y_nhu_truoc(self):
        """Chong hoi quy: ban va khong duoc lam hong duong da chay duoc."""
        dk = self._dk("We buy when the RSI crosses below 15")
        self.assertEqual(dk[0]["trai"], {"chi_bao": "rsi", "n": 14})
        self.assertEqual(dk[0]["phep"], "cheo_xuong")


class PhepCATCungMangCHIEU(unittest.TestCase):
    """Bo sot phep cat thi luat Connors RSI(2) cheo xuong 15 bi xep ho "khac".

    Do that 30/08/2026: trong 16 spec rut duoc tu kho, spec duy nhat mang co
    che noi tieng nhat (`mua_rsi2_cheo_xuong_15`, tu quantifiedstrategies) la
    spec DUY NHAT khong xep duoc ho — vi `_phia_nguong` chi biet `<` va `>`.
    "khac" khong bi tu choi o cong, no chi lang le mat nhom doi chung.
    """

    @staticmethod
    def _dk(phep, nguong=15.0):
        return [{"trai": {"chi_bao": "rsi", "n": 2}, "phep": phep,
                 "phai": {"hang": nguong}}]

    def test_cheo_xuong_va_mua_la_quay_ve_trung_binh(self):
        self.assertEqual(DH.suy_ho(self._dk("cheo_xuong"), 1),
                         "quay_ve_trung_binh")

    def test_cheo_len_va_mua_la_xu_huong(self):
        self.assertEqual(DH.suy_ho(self._dk("cheo_len", 70.0), 1), "xu_huong")

    def test_cheo_len_va_BAN_la_quay_ve_trung_binh(self):
        self.assertEqual(DH.suy_ho(self._dk("cheo_len", 70.0), -1),
                         "quay_ve_trung_binh")

    def test_luat_Connors_doc_tu_cau_that_ra_dung_ho_VA_dung_chu_ky(self):
        """Bai kiem dau-den-cuoi tren dung cau da lam lo loi."""
        c = ("The first example is a 2-day RSI strategy where we buy when it "
             "crosses below 15")
        pv, _ = DH.tach_vao_ra(c)
        dk, _ = DH.dieu_kien_trong_cau(pv)
        dk, _ = DH.loc_dieu_kien(dk)
        self.assertEqual(dk[0]["trai"]["n"], 2)
        self.assertEqual(DH.suy_ho(dk, 1), "quay_ve_trung_binh")

    def test_moi_phep_trong_ngu_phap_deu_xep_duoc_ho(self):
        """Chan tho: mot phep moi them vao ngu_phap ma quen o day thi im lang."""
        for phep in ("<", "<=", ">", ">=", "cheo_len", "cheo_xuong"):
            with self.subTest(phep=phep):
                self.assertNotEqual(
                    DH.suy_ho(self._dk(phep, 50.0), 1), "khac",
                    f"phep '{phep}' khong xep duoc ho -> mat nhom doi chung")


class BoDocPhaiSinhRaTOAN_HANG_NGU_PHAP_DA_CO(unittest.TestCase):
    """Do 11/09/2026: 12/43 toan hang chua duoc dung MOT LAN NAO trong 689 co
    che cua kho - va ca 12 deu vang mat khoi `_TOAN_HANG` cua bo doc. Ngu phap
    noi duoc mot dai rong gap hai lan cai ma bo doc biet hoi, nen phan chenh do
    la vung mu KHONG THE vao he bang duong van xuoi.

    Lop nay khoa lai phan da noi duoc. Them mot chi bao vao `CHI_BAO_CO` ma
    quen bo doc thi bai kiem cuoi cung o day keu.
    """

    def _trai(self, cau):
        dk, _ = DH.dieu_kien_trong_cau(cau)
        self.assertTrue(dk, f"khong doc duoc: {cau}")
        return dk[0]["trai"]

    def test_adx_macd_cci_stochastic_obv_momentum(self):
        for cau, mong in (
            ("Buy when the 14-period ADX is above 25", {"chi_bao": "adx", "n": 14}),
            ("Sell when MACD histogram falls below 0", {"chi_bao": "macd", "lay": "hieu"}),
            ("Go long if the 20-period CCI drops below -100", {"chi_bao": "cci", "n": 20}),
            ("Enter when stochastic(14) is below 20", {"chi_bao": "stochastic", "n": 14}),
            ("Buy when OBV is above 0", {"chi_bao": "obv"}),
            ("Short when the 10-period momentum is below 0",
             {"chi_bao": "dong_luong", "n": 10}),
            ("Long when the 50-day weighted moving average is above 100",
             {"chi_bao": "wma", "n": 50, "cot": "close"}),
            ("Buy when the daily range exceeds 2", {"chi_bao": "bien_do"}),
            ("Enter long when volume is above 1000", {"chi_bao": "khoi_luong"}),
        ):
            with self.subTest(cau=cau):
                self.assertEqual(self._trai(cau), mong)

    def test_doc_xong_phai_QUA_duoc_kiem_khai_bao(self):
        """Doc ra mot toan hang ma ngu phap tu choi thi khong hon gi khong doc."""
        cau = "Buy when the 14-period ADX is above 25"
        dk, _ = DH.dieu_kien_trong_cau(cau)
        spec = {"ten": "t", "ho": "xu_huong", "chieu": 1, "giu": 1,
                "vao": dk, "ra": [],
                "co_che": "ADX cao nghia la xu huong dang manh, nen di theo chieu "
                          "cua no thay vi cho gia quay ve trung binh."}
        self.assertEqual(NP.kiem_khai_bao(spec), [])


class LOAI_CAU_PHAI_TU_CHOI_VAN_KE_CHUYEN(unittest.TestCase):
    """Truoc 11/09 `loai_cau` chi can thay chu 'if'/'when' la nhan la luat. Do
    duoc tren 150 cau: CA 150 cau no nhan deu ra 0 dieu kien. Do phu cao, do
    chinh xac gan bang 0 - va mot bo phan loai nhu vay nhoi hang doi boc bang
    rac DONG THOI thoi phong con so 'cau dang luat' nen cho hong that bi che.
    """

    def test_tu_choi_van_ke_chuyen_co_chu_if(self):
        for cau in (
            "And if it's a bearish price movement, you go for a sell",
            "So if you are still bullish, how about buying a stock at an oversold level",
            "Has multiple overlapping exit systems: fixed SL/TP, break-even move",
        ):
            with self.subTest(cau=cau):
                self.assertIsNone(DH.loai_cau(cau))

    def test_van_nhan_luat_that(self):
        self.assertEqual(DH.loai_cau("We sell short when RSI is above 90"), "vao_ban")
        self.assertIsNotNone(
            DH.loai_cau("Buy when the close falls below the lower Bollinger band."),
            "nguong la mot TOAN HANG chu khong phai con so - van la luat day du")

    def test_hang_doi_tu_vung_dung_che_do_LONG(self):
        """`cum_chua_hieu` ton tai de tim cau co toan hang CHUA doc duoc. Siet
        no bang `chat=True` la lam mu chinh cai la khoa mo cho buoc sau."""
        cau = "Buy when the Ichimoku cloud thickness is above 30"
        self.assertIsNone(DH.loai_cau(cau, chat=True))
        self.assertIsNotNone(DH.loai_cau(cau, chat=False))


class MENH_DE_CHUNG_CHU_NGU(unittest.TestCase):
    """Tieng Anh tai chinh luoc chu ngu o menh de sau. Cat o chu 'and' roi doi
    menh de sau tu co chu ngu rieng la doc SAI van pham."""

    def test_thua_ke_chu_ngu_tu_menh_de_truoc(self):
        dk, _ = DH.dieu_kien_trong_cau(
            "if the price rises and exceeds the previous High, the robot buys")
        self.assertTrue(dk)
        self.assertEqual(dk[0]["trai"], {"chi_bao": "gia", "cot": "close"})

    def test_KHONG_thua_ke_qua_mot_chu_ngu_khac(self):
        """Doan trai dai = mot thuc the khac han, thua ke vao do la gan dieu
        kien cho nham nguoi."""
        dk, _ = DH.dieu_kien_trong_cau(
            "Given ORCL known sustained downtrend, a long-only breakout "
            "strategy is exposed above 5")
        self.assertEqual(dk, [])


class BAO_PHAN_BO_SOT_CHU_KHONG_IM_LANG(unittest.TestCase):
    """Doc duoc mot nua roi im lang la mat mat khong do duoc: co che dang ky
    vao he la mot co che KHAC voi y tac gia, va khong ai biet."""

    def test_ve_khong_doc_duoc_phai_hien_ra_trong_ly_do(self):
        dk, ly = DH.dieu_kien_trong_cau(
            "Buy when RSI(14) is below 30 and the Ichimoku cloud is above 55")
        self.assertTrue(dk)
        self.assertTrue(ly.startswith("bo_sot:"),
                        f"ve thu hai bi bo ma khong bao: {ly!r}")

    def test_doc_tron_ven_thi_khong_bao_bo_sot(self):
        _, ly = DH.dieu_kien_trong_cau("Buy when the 2-period RSI closes below 10")
        self.assertEqual(ly, "")


class MOI_CHI_BAO_BO_DOC_SINH_RA_DEU_PHAI_XEP_DUOC_HO(unittest.TestCase):
    """Doc ra mot co che roi vut no vi khong xep duoc ho la mat mat im lang.

    Do 11/09/2026 sau khi them 15 toan hang vao bo doc: ly do TU CHOI lon nhat
    cua `them_co_che` la `ho 'khac'` - 29/58 lan - va trong 19 co che moi duoc
    nhan KHONG co lay mot cci/adx/macd nao. Ban va bo doc bi HUY LANG LE o tang
    duoi vi bang ho khong biet cac ten do.
    """

    def test_bang_ho_va_thu_tu_xet_KHONG_duoc_lech(self):
        """Truoc 11/09 day la HAI nguon su that: mot dict, va mot tuple viet
        cung ben trong `suy_ho`. Them vao dict ma quen tuple = khong co tac dung
        gi, va khong mot loi bao."""
        self.assertEqual(set(DH._HO_THEO_CHI_BAO), set(DH._UU_TIEN_HO))

    def test_moi_chi_bao_trong_bang_ho_deu_hop_le(self):
        hop_le = {"quay_ve_trung_binh", "xu_huong", "pha_vo", "bien_dong",
                  "dong_tien", "lich", "phien", "vi_mo"}
        for ten, ho in DH._HO_THEO_CHI_BAO.items():
            with self.subTest(chi_bao=ten):
                self.assertIn(ho, hop_le)

    def test_dao_dong_phai_nam_trong_bang_ho(self):
        self.assertTrue(set(DH._DAO_DONG) <= set(DH._HO_THEO_CHI_BAO))

    def test_cau_that_voi_chi_bao_moi_deu_ra_ho_KHAC_khac(self):
        for cau, chieu, mong in (
            ("Buy when the 14-period ADX is above 25", 1, "xu_huong"),
            ("Go long if the 20-period CCI drops below -100", 1, "quay_ve_trung_binh"),
            ("Sell when MACD histogram falls below 0", -1, "xu_huong"),
            ("Buy when OBV is above 0", 1, "dong_tien"),
            ("Enter when stochastic(14) is below 20", 1, "quay_ve_trung_binh"),
            ("Buy when the daily range exceeds 2", 1, "bien_dong"),
            ("Enter long when volume is above 1000", 1, "dong_tien"),
        ):
            with self.subTest(cau=cau):
                dk, _ = DH.dieu_kien_trong_cau(cau)
                self.assertTrue(dk, f"khong doc duoc: {cau}")
                self.assertEqual(DH.suy_ho(dk, chieu), mong)


class HINH_HOC_GANN_DOC_DUNG_CHU_KHONG_DOC_BUA(unittest.TestCase):
    """`gann_sq9` vao ngu phap tu 08/09 nhung bo doc chua bao gio sinh ra no -
    nen no van nam trong danh sach "chua ai dung" ke ca sau khi da sua loi
    KeyError. Sua mot cho thi phai di het duong.

    Va o day co mot bay do duoc: "price crosses below the 45 degree Gann angle"
    tung ra `close cheo_xuong 45.0` - SO GIA VOI CON SO 45. Tren US500 (~6.000)
    dieu kien do khong bao gio kich hoat; tren EURUSD (~1,08) thi luon dung. Ca
    hai deu la mot co che khong ai viet, va no TRONG HOAN TOAN HOP LE.
    """

    def _dk(self, cau):
        dk, ly = DH.dieu_kien_trong_cau(cau)
        self.assertTrue(dk, f"khong doc duoc: {cau} ({ly})")
        return dk[0]

    def test_square_of_nine_ra_dung_toan_hang(self):
        d = self._dk("Buy when price is above the Gann square of nine level")
        self.assertEqual(d["phai"], {"chi_bao": "gann_sq9"})

    def test_SO_DO_KHONG_duoc_thanh_NGUONG(self):
        d = self._dk("Sell when price crosses below the 45 degree Gann angle")
        self.assertEqual(d["phai"].get("chi_bao"), "gann_sq9",
                         "con so cua GOC bi doc thanh nguong gia")
        self.assertEqual(d["phai"].get("goc"), 45.0)
        self.assertNotIn("hang", d["phai"])

    def test_gann_angle_of_N_cung_doc_duoc(self):
        d = self._dk("Buy when the close is above the Gann angle of 45")
        self.assertEqual(d["phai"].get("goc"), 45.0)

    def test_xep_ho_PHA_VO_va_qua_cong_ngu_phap(self):
        """Muc Gann la mot MUC GIA hinh hoc - xuyen qua no la pha vo."""
        dk, _ = DH.dieu_kien_trong_cau(
            "Buy when price is above the Gann square of nine level")
        ho = DH.suy_ho(dk, 1)
        self.assertEqual(ho, "pha_vo")
        self.assertEqual(NP.kiem_khai_bao(
            {"ten": "t", "ho": ho, "chieu": 1, "giu": 1, "vao": dk, "ra": [],
             "co_che": "Muc Gann la muc gia hinh hoc; xuyen qua no la pha vo."}), [])

    def test_so_binh_thuong_VAN_lam_nguong_duoc(self):
        """Chot chan goc khong duoc lam hong cac cau khong lien quan."""
        d = self._dk("Buy when the 2-period RSI closes below 10")
        self.assertEqual(d["phai"], {"hang": 10.0})
