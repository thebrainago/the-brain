# -*- coding: utf-8 -*-
"""MOT VUNG KHONG PHAI MOT DIEU KIEN TAI MOT NEN.

Kho 06/09/2026 giu **14 dinh nghia FVG doc lap, 19 order block, 23 cau
truc/BOS, 13 thanh khoan, 6 ORB** - khoang 75 file - va tat ca deu dang bi dich
thanh so sanh THEO TUNG NEN, tuc dich SAI. Mot khoang trong gia sinh o bar i la
mot VAT THE song qua nhieu bar: co bien tren, bien duoi, va chet khi bi lap
day. Bo boc khong dien duoc dieu do nen no dien `hang: 0` vao cho nguong, va ca
ho tro thanh dieu kien hien nhien.

Ba thu bai nay phai canh, va khong cai nao la so hoc:

  1. **NHIN TRUOC.** Day la nguyen thuy DAU TIEN cua ngu phap mang TRANG THAI
     qua nhieu bar. Moi thu khac chi doc mot bar. Neu bien vung co the lay gia
     tri cua bar sau, edge gia se rat dep va rat kho thay
     [[hai-lan-dau-vao-va-vuon-nguon]].
  2. **VUNG SINH O MOI BAR.** `tao` rong (hoac suy bien thanh luon dung) thi
     moi quan he tro nen gan nhu luon dung - dung ho benh "ve luon dung im lang
     bien mat" ma cong `_kiem_hien_nhien` vua dung de chan.
  3. **BO DO KHONG BAO GIO NOI KHONG.** Neu `kiem_khong_nhin_truoc` khong bat
     duoc mot vung ro ri co y, thi viec no xanh o day khong chung minh gi ca
     [[cong-pass-phai-hieu-chuan-hai-chieu]].
"""
import unittest

import numpy as np
import pandas as pd

from nhan import ngu_phap as NP


def _df(n: int = 400) -> pd.DataFrame:
    """Khung gia gia lap CO BIEN DO THAT trong tung bar - khung khong co bien
    do thi khong sinh duoc khoang trong nao, va bai kiem se xanh vi rong."""
    r = np.random.default_rng(11)
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    dong = 100 + np.cumsum(r.normal(0, 1.4, n))
    mo = np.concatenate(([dong[0]], dong[:-1])) + r.normal(0, 0.9, n)
    bd = np.abs(r.normal(0, 1.6, n)) + 0.2
    hi = np.maximum(mo, dong) + bd
    lo = np.minimum(mo, dong) - bd
    return pd.DataFrame({"open": mo, "high": hi, "low": lo, "close": dong},
                        index=idx)


def _fvg_tang(quan_he="cham", huy="cham", song=20, tao=None):
    """FVG tang chuan: `low[i] > high[i-2]`, vung = [high[i-2], low[i]]."""
    if tao is None:
        tao = [{"trai": {"chi_bao": "gia", "cot": "low"}, "phep": ">",
                "phai": {"chi_bao": "tre",
                         "cua": {"chi_bao": "gia", "cot": "high"}, "n": 2}}]
    return {"vung": {"tao": tao,
                     "tren": {"chi_bao": "gia", "cot": "low"},
                     "duoi": {"chi_bao": "tre",
                              "cua": {"chi_bao": "gia", "cot": "high"}, "n": 2},
                     "song": song, "huy": huy},
            "quan_he": quan_he}


def _spec(ve, chieu=1, giu=1):
    return {"ten": "thu_vung", "ho": "pha_vo", "chieu": chieu, "giu": giu,
            "co_che": "Khoang trong gia la lenh chua khop cua ben bi bo lai; "
                      "ho phai dat lai o do khi gia quay ve.",
            "vao": [ve]}


class VungChayDungHINH_HOC(unittest.TestCase):

    def setUp(self):
        self.df = _df()

    def _th(self, ve):
        return np.asarray(NP.sinh_tu_spec(_spec(ve), self.df), dtype=float)

    def test_cham_la_hop_cua_cac_quan_he_con(self):
        """`trong` + `bat_len` + `bat_xuong` phai chia het `cham`: moi lan cham,
        gia dong cua hoac o trong vung, hoac tren, hoac duoi. Khong con cho."""
        cham = self._th(_fvg_tang("cham")) != 0
        con = (self._th(_fvg_tang("trong")) != 0)
        con |= (self._th(_fvg_tang("bat_len")) != 0)
        con |= (self._th(_fvg_tang("bat_xuong")) != 0)
        self.assertTrue(cham.any(), "khung thu khong sinh duoc vung nao")
        np.testing.assert_array_equal(cham, con)

    def test_vung_TANG_bat_len_chu_khong_bat_xuong(self):
        """Vung cua FVG tang nam DUOI gia. Neu `bat_xuong` cung nhieu nhu
        `bat_len` thi bien tren/duoi dang bi dao."""
        self.assertGreater((self._th(_fvg_tang("bat_len")) != 0).sum(),
                           (self._th(_fvg_tang("bat_xuong")) != 0).sum())

    def test_vung_GIAM_lat_nguoc_ket_qua(self):
        """Doi chung: cung bo may, vung nam TREN gia thi ket qua phai lat."""
        ve = {"vung": {"tao": [{"trai": {"chi_bao": "gia", "cot": "high"},
                                "phep": "<",
                                "phai": {"chi_bao": "tre",
                                         "cua": {"chi_bao": "gia", "cot": "low"},
                                         "n": 2}}],
                       "tren": {"chi_bao": "tre",
                                "cua": {"chi_bao": "gia", "cot": "low"}, "n": 2},
                       "duoi": {"chi_bao": "gia", "cot": "high"},
                       "song": 20, "huy": "cham"},
              "quan_he": "bat_xuong"}
        xuong = (self._th(ve) != 0).sum()
        ve2 = dict(ve, quan_he="bat_len")
        self.assertGreater(xuong, (self._th(ve2) != 0).sum())

    def test_song_lau_hon_thi_kich_hoat_khong_giam(self):
        it = (self._th(_fvg_tang("cham", song=3)) != 0).sum()
        nhieu = (self._th(_fvg_tang("cham", song=60)) != 0).sum()
        self.assertGreaterEqual(nhieu, it)

    def test_huy_het_han_giu_vung_lau_hon_huy_cham(self):
        """`huy='cham'` la ngu nghia chuan cua FVG - lap day mot lan la het."""
        self.assertGreater((self._th(_fvg_tang("cham", huy="het_han")) != 0).sum(),
                           (self._th(_fvg_tang("cham", huy="cham")) != 0).sum())

    def test_khai_nguoc_bien_tren_duoi_van_ra_cung_ket_qua(self):
        """Doan [a,b] khong co chieu. Nguoi viet khai nguoc thi bo may phai tu
        dao, chu khong duoc lang le tra ve chuoi rong."""
        ve = _fvg_tang("cham")
        dao = {"vung": dict(ve["vung"], tren=ve["vung"]["duoi"],
                            duoi=ve["vung"]["tren"]), "quan_he": "cham"}
        np.testing.assert_array_equal(self._th(ve) != 0, self._th(dao) != 0)

    def test_tran_vung_song_khong_lam_vong_lap_no(self):
        """`tao` luon dung -> mot vung moi MOI BAR. Khong co tran thi vong lap
        thanh O(n^2). Bai nay canh gia, khong canh ket qua."""
        import time
        ve = _fvg_tang("cham", song=500,
                       tao=[{"trai": {"chi_bao": "gia", "cot": "high"},
                             "phep": ">",
                             "phai": {"chi_bao": "gia", "cot": "low"}}])
        t0 = time.time()
        self._th(ve)
        self.assertLess(time.time() - t0, 2.0)

    def test_vung_KHONG_kich_hoat_o_chinh_nen_sinh_ra_no(self):
        """Voi hinh hoc FVG, bien tren = `low[i]` nen nen sinh LUON tu cham
        chinh no. Neu xet tai nen sinh thi moi vung song dung mot nen roi chet:
        so kich hoat = so vung tao, va `song`/`huy` thanh nut GIA.

        Va sai ca ve co che: cai ta muon dien la "gia QUAY LAI lap gap", khong
        phai "gap vua xuat hien"."""
        ve = _fvg_tang("cham", huy="het_han", song=1)
        tao = NP._dieu_kien(self.df, ve["vung"]["tao"], mac_dinh=False).to_numpy()
        cham = self._th(ve) != 0
        # Khong duoc co bar nao vua TAO vua CHAM ma bar truoc do khong tao.
        chi_tao = tao & ~np.concatenate(([False], tao[:-1]))
        self.assertFalse(bool((chi_tao & cham).any()),
                         "vung kich hoat ngay tai nen sinh ra no")

    def test_song_la_nut_van_THAT_duoi_huy_het_han(self):
        """`song` chi co nghia khi vung khong chet ngay lan cham dau. Neu day
        la hang so thi bo do on dinh se do lan can cua mot nut chet."""
        dem = [ (self._th(_fvg_tang("cham", huy="het_han", song=s)) != 0).sum()
                for s in (1, 3, 10, 30) ]
        self.assertEqual(dem, sorted(dem), "song tang ma kich hoat khong tang")
        self.assertGreater(dem[-1], dem[0] * 2, "song gan nhu khong doi gi")

    def test_moi_tham_so_PHOI_BAY_deu_dat_duoc_that(self):
        """`tham_so_cua` liet ke duong dan, `ap_tham_so` dat theo duong do. Voi
        danh sach LONG (`vung.tao`) duong dan co token dinh lien kieu `tao0`, va
        truoc 06/09 `_dat` lang le bo qua - tham so duoc LIET KE nhung khong
        bao gio DAT duoc [[doi-tham-so-ma-khong-doi-ket-qua]]."""
        import json
        s = _spec(_fvg_tang("cham", huy="het_han"))
        ts = NP.tham_so_cua(s)
        self.assertIn("vao0_vung_tao0_phai_n", ts, "khong phoi bay tham so cua 'tao'")
        for k, v in ts.items():
            moi = NP.ap_tham_so(s, {k: v + 3})
            self.assertNotEqual(json.dumps(moi, sort_keys=True),
                                json.dumps(s, sort_keys=True),
                                "tham so '%s' duoc liet ke nhung khong dat duoc" % k)

    def test_tach_chi_so_doc_dung_token_dinh_lien(self):
        self.assertEqual(NP._tach_chi_so("tao0"), ("tao", 0))
        self.assertEqual(NP._tach_chi_so("tao12"), ("tao", 12))
        self.assertEqual(NP._tach_chi_so("trai"), ("trai", None))
        self.assertEqual(NP._tach_chi_so("0"), ("0", None))


class CongPhaiTuChoiVungHONG(unittest.TestCase):

    def test_thieu_tao_bi_tu_choi(self):
        """`tao` rong -> vung sinh o moi bar -> quan he gan nhu luon dung."""
        ve = _fvg_tang()
        ve["vung"]["tao"] = []
        self.assertTrue(any("tao" in e for e in NP.kiem_khai_bao(_spec(ve))))

    def test_thieu_bien_bi_tu_choi(self):
        ve = _fvg_tang()
        ve["vung"].pop("tren")
        self.assertTrue(any("tren" in e for e in NP.kiem_khai_bao(_spec(ve))))

    def test_quan_he_la_bi_tu_choi(self):
        ve = _fvg_tang()
        ve["quan_he"] = "nhay_mua"
        self.assertTrue(NP.kiem_khai_bao(_spec(ve)))

    def test_ve_tao_hien_nhien_bi_tu_choi(self):
        """`tao` cung phai qua bo chan hien nhien - `high > low` luon dung."""
        ve = _fvg_tang(tao=[{"trai": {"chi_bao": "gia", "cot": "high"},
                             "phep": ">=",
                             "phai": {"chi_bao": "gia", "cot": "low"}}])
        self.assertTrue(any("LUON dung" in e
                            for e in NP.kiem_khai_bao(_spec(ve))))

    def test_song_ngoai_khoang_bi_tu_choi(self):
        ve = _fvg_tang()
        ve["vung"]["song"] = 0
        self.assertTrue(any("song" in e for e in NP.kiem_khai_bao(_spec(ve))))
        ve["vung"]["song"] = 9999
        self.assertTrue(any("song" in e for e in NP.kiem_khai_bao(_spec(ve))))

    def test_cach_huy_la_bi_tu_choi(self):
        ve = _fvg_tang(huy="xoa_het")
        self.assertTrue(any("huy" in e for e in NP.kiem_khai_bao(_spec(ve))))


class BoDoNHIN_TRUOC_PHAI_BIET_NOI_KHONG(unittest.TestCase):
    """Vung la nguyen thuy DAU TIEN mang trang thai qua nhieu bar. Neu
    `kiem_khong_nhin_truoc` khong bat duoc mot vung ro ri co y thi viec no xanh
    o day khong chung minh gi ca."""

    def test_vung_sach_thi_qua(self):
        dat, mo_ta = NP.kiem_khong_nhin_truoc(_spec(_fvg_tang("cham")), _df())
        self.assertTrue(dat, mo_ta)

    def test_vung_RO_RI_bi_bat(self):
        goc = NP.toan_hang

        def _ro_ri(d, t):
            # Bien tren cua vung lay LOW CUA HAI BAR SAU.
            #
            # Phai la -2, khong phai -1. Vung chi song tu nen SAU nen sinh, nen
            # mot vung sinh o bar i-1 voi bien lay tu bar i duoc dung o bar i -
            # va `low[i]` thi BIET tai close cua bar i. Do khong phai ro ri, va
            # mot canary dung -1 se doi bo do bat mot thu khong sai.
            if isinstance(t, dict) and t.get("_ro_ri"):
                return NP._cot(d, "low").shift(-2)
            return goc(d, t)

        ve = _fvg_tang("cham")
        ve["vung"]["tren"] = {"chi_bao": "gia", "cot": "low", "_ro_ri": True}
        NP.toan_hang = _ro_ri
        try:
            dat, _ = NP.kiem_khong_nhin_truoc(_spec(ve), _df())
        finally:
            NP.toan_hang = goc
        self.assertFalse(dat, "bo do nhin truoc KHONG bat duoc vung ro ri")


if __name__ == "__main__":
    unittest.main()
