# -*- coding: utf-8 -*-
"""HAI TOAN HANG CUOI CUNG CUA `ngu_phap` DA CO KHUON (20/09/2026).

Do 19/09: `duc()` phu 43/45 toan hang. Hai cai con lai la `phuong_sai` (72 lan
trong ma that) va `gann_sq9` (them 08/09 nhung chua khuon nao goi). Mot toan
hang khong khuon nao dung thi may DE khong bao gio sinh ra no - no ton tai
tren giay chu khong tren duong chay nao.

## BA CAU HOI CUA BO BAI NAY

1. **Phu that chua** - `do_phu` tren chinh lo duc phai rong.
2. **Co phai ban doi ten khong** - `phuong_sai` de nhat la bi dung thanh mot
   ban cua `do_lech`. `phan_vi(phuong_sai(n))` va `phan_vi(do_lech(n))` BANG
   NHAU tung bar (can bac hai la don dieu tang), nen mot khuon nhu vay se tra
   suat FDR hai lan cho mot cau hoi. Bai o day do CHINH dieu do.
3. **Thang do co that su cat khong** - Gann phu thuoc `sqrt(gia)`, va bo bai
   phai chung minh dieu do bang cung mot chuoi loi suat o hai muc gia.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from nhan import hephaestus as HP
from nhan import ngu_phap as NP


def _chuoi(p0: float, n: int = 3000, hat: int = 7, ar: float = 0.0):
    """Chuoi gia tong hop o MUC GIA `p0`, cung hat giong -> cung loi suat."""
    rng = np.random.default_rng(hat)
    e = rng.normal(0, 0.002, n)
    if ar:
        for i in range(1, n):
            e[i] += ar * e[i - 1]
    gia = p0 * np.exp(np.cumsum(e))
    idx = pd.date_range("2018-01-01", periods=n, freq="h")
    return pd.DataFrame({"open": gia, "high": gia * 1.001, "low": gia * 0.999,
                         "close": gia, "volume": 1.0}, index=idx)


LO = HP.duc(han_ngach=5000)
VR = [d for d in LO if d["ten"].startswith("hp_vr_")]
GANN = [d for d in LO if d["ten"].startswith("hp_gann_")]


class PhuHet(unittest.TestCase):
    def test_khong_con_toan_hang_nao_khong_co_khuon(self):
        self.assertEqual(HP.do_phu(kho=LO)["bo_trong"], [],
                         "van con toan hang khong khuon nao sinh ra duoc")

    def test_ca_hai_khuon_moi_deu_gop_co_che(self):
        self.assertTrue(VR, "khuon ty_le_phuong_sai khong sinh co che nao")
        self.assertTrue(GANN, "khuon gann khong sinh co che nao")

    def test_khai_bao_hop_le_het(self):
        for d in VR + GANN:
            self.assertFalse(NP.kiem_khai_bao(d), d["ten"])


class KhongPhaiDoLechDoiTen(unittest.TestCase):
    """Chot chan chinh cua khuon `phuong_sai`.

    Neu ai do sau nay "don gian hoa" khuon thanh `phan_vi(phuong_sai(n)) < v`
    thi no se bang HET tung bar voi ban `do_lech` da co trong
    `_khuon_bien_dong_do_lech`, va khong cong nao bat duoc vi ca hai deu hop
    le va deu kich hoat binh thuong.
    """

    def setUp(self):
        self.df = _chuoi(1.08)

    def test_phan_vi_cua_phuong_sai_BANG_phan_vi_cua_do_lech(self):
        """Hieu chuan chieu nguoc: chung minh cai bay co that."""
        gia = {"chi_bao": "gia", "cot": "close"}
        a = NP.toan_hang(self.df, {"chi_bao": "phan_vi", "n": 100,
                                   "cua": {"chi_bao": "phuong_sai", "n": 20,
                                           "cua": gia}})
        b = NP.toan_hang(self.df, {"chi_bao": "phan_vi", "n": 100,
                                   "cua": {"chi_bao": "do_lech", "n": 20,
                                           "cua": gia}})
        m = a.notna() & b.notna()
        self.assertGreater(int(m.sum()), 500)
        np.testing.assert_allclose(a[m].to_numpy(), b[m].to_numpy(), atol=1e-12)

    def test_tin_hieu_VR_khac_han_tin_hieu_phan_vi_do_lech(self):
        """Neu khuon moi chi la ban doi ten thi day se trung gan het."""
        do_lech = [d for d in LO if d["ten"].startswith(("hp_vol_thap",
                                                         "hp_vol_cao"))]
        self.assertTrue(do_lech, "khong tim thay khuon do_lech de doi chieu")
        tin_vr = [NP.sinh_tu_spec(d, self.df) for d in VR]
        tin_dl = [NP.sinh_tu_spec(d, self.df) for d in do_lech]
        for i, a in enumerate(tin_vr):
            for b in tin_dl:
                giong = float(np.mean(np.asarray(a) == np.asarray(b)))
                self.assertLess(giong, 0.99,
                                "co che VR %s trung 99%% voi mot co che do_lech "
                                "- nghia la mot phep thu tra suat FDR hai lan"
                                % VR[i]["ten"])

    def test_VR_do_dung_cai_no_noi_la_do_TREN_CA_BA_CHE_DO(self):
        """Hieu chuan HAI CHIEU tren chuoi dat san, khong chi mot chieu.

        Mot khuon tu choi TAT CA cho so lieu y het mot khuon tot (luat
        `null_ty_le_lot` + `thu_luc_cong` cua du an), nen phai do ca ba che do
        va doi hinh dang CHU X: moi ban chi song o dung che do cua no.

        DO 20/09/2026 (3.000 bar, hat 7, nhieu AR tren LOI SUAT, ty le kich
        hoat trung binh):

            AR tren loi suat   -0,35    0,00   +0,35
            ban 'tiep_dien'    0,000   0,090   0,615
            ban 'hoi_ve'       0,428   0,018   0,000

        Cot giua la buoc ngau nhien: `VR = 1` dung bang dinh nghia nen ca hai
        ban deu gan im - dung nhu phai the. Neu mot ban van kich hoat manh o
        cot giua thi no dang doc mot thu khac chu khong doc tu tuong quan.
        """
        tiep = [d for d in VR if d["ten"].startswith("hp_vr_tiep_dien_")]
        hoi = [d for d in VR if d["ten"].startswith("hp_vr_hoi_ve")]
        self.assertTrue(tiep and hoi)
        do = lambda ds, df: float(np.mean([NP._ty_le_kich_hoat(d, df)
                                           for d in ds]))
        bang = {ar: (do(tiep, _chuoi(1.08, ar=ar)), do(hoi, _chuoi(1.08, ar=ar)))
                for ar in (-0.35, 0.0, 0.35)}

        # Don dieu theo dung chieu cua tung ban.
        self.assertGreater(bang[0.35][0], bang[0.0][0], bang)
        self.assertGreater(bang[0.0][0], bang[-0.35][0], bang)
        self.assertGreater(bang[-0.35][1], bang[0.0][1], bang)
        self.assertGreater(bang[0.0][1], bang[0.35][1], bang)

        # Chieu nguoc cua bai: buoc ngau nhien phai gan IM o ca hai ban. Thieu
        # chot nay thi mot khuon kich hoat 90% moi luc van "don dieu".
        self.assertLess(max(bang[0.0]), 0.25,
                        "tren buoc ngau nhien (VR = 1 dung bang dinh nghia) ma "
                        "van kich hoat manh: %r" % (bang,))



class GannPhuThuocCanBacHaiCuaGia(unittest.TestCase):
    """Thang do cua Gann la `sqrt(gia)`, va do la ly do `goc` phai quet rong."""

    def test_cung_loi_suat_khac_muc_gia_thi_kich_hoat_khac_han(self):
        ho_tro = [d for d in GANN if d["ten"].startswith("hp_gann_ho_tro_20_")]
        self.assertGreaterEqual(len(ho_tro), 5)
        re = _chuoi(1.08)      # EURUSD
        dat = _chuoi(2000.0)   # XAUUSDM - CUNG chuoi loi suat, khac muc gia
        a = [NP._ty_le_kich_hoat(d, re) for d in ho_tro]
        b = [NP._ty_le_kich_hoat(d, dat) for d in ho_tro]
        self.assertGreater(
            max(abs(x - y) for x, y in zip(a, b)), 0.1,
            "doi muc gia ma ty le kich hoat khong doi - hoac `gann_sq9` khong "
            "con phu thuoc sqrt(gia), hoac bai kiem dang do nham thu gi do")

    def test_moi_muc_gia_deu_con_it_nhat_mot_goc_dung_duoc(self):
        """Quet `goc` rong la de DUNG viec nay - phai kiem, khong duoc tin."""
        for ten, p0 in (("EURUSD", 1.08), ("USDJPY", 150.0),
                        ("US500", 5000.0), ("XAUUSD", 2000.0)):
            df = _chuoi(p0)
            song = [d["ten"] for d in GANN
                    if 0.005 < NP._ty_le_kich_hoat(d, df) < 0.95]
            self.assertTrue(song, "muc gia %s (%s): khong goc nao song - dai "
                                  "quet `goc` chua du rong" % (p0, ten))

    def test_khong_nhin_truoc_bar_hien_tai(self):
        """`thap_nhat(n)` gom ca nen dang xet nen phai co `tre(1)`."""
        for d in GANN:
            ve = str(d["vao"])
            self.assertIn("'tre'", ve,
                          "%s khong lui bar nao - muc chieu tu chinh nen dang "
                          "xet la nhin truoc" % d["ten"])


if __name__ == "__main__":
    unittest.main()
