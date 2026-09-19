# -*- coding: utf-8 -*-
"""HAI NUT QUAN TRI CON THIEU cua `mo_phong_v2` (19/09/2026).

`nhan/quan_tri_than.py` boc duoc chung tu EA that, nhung bo mo phong khong co
cho de cam vao, nen chung phai mang tien to `_` (boc duoc ma chua mo phong
duoc). Bai nay lap cho do.

## NUT 1 - `chot_lui_ty` / `chot_lui_tu`: NHA LAI MOT PHAN DINH LAI

`EA Snippets_Breakout_Breakout2.mq5` viet thang trong ma:

    if(peakwin>=45 && profits<(peakwin*0.9))   CloseAll();

Khac han `trailing_tu` DA CO: `trailing` do bang PIP tu dinh GIA, con cai nay
do bang TY LE cua dinh LAI. Khac biet khong phai cach viet:

  * mot ro luoi 8 tang co lot gap 8 lan ro 1 tang, nen cung mot so PIP la mot
    so TIEN khac han. Trailing 10 pip that chat voi ro 1 tang va long leo voi
    ro 8 tang - dung nguoc voi cai ta muon.
  * nha lai 10% dinh lai thi tu co gian theo ro, khong phai chinh tay.

## NUT 2 - `tia_ty` / `tia_tu`: DONG MOT PHAN VI THE

Khac `cat_hoa` da co: `cat_hoa` GHEP hai lenh (moi nhat voi cu nhat) va dong
CA CAP. `tia` cat mot TY LE cua ca ro khi lai cham nguong, giu phan con lai
chay tiep.

BAY DA GHI TRONG `dich_mq5_quan_tri.py`: `PositionClosePartial` voi khoi luong
duoi `SYMBOL_VOLUME_MIN` **that bai im lang**. Mo phong phai dung luat do,
khong thi bang so se dep hon that.
"""
from __future__ import annotations

import unittest

import numpy as np

import mo_phong_v2 as MP


def _khung(gia: list[float], sp: float = 1.0) -> dict:
    """Khung gia toi thieu ma `mo_phong` can. `thu` = 1 cho moi bar (khong swap x3)."""
    g = np.asarray(gia, dtype=float)
    return {"hi": g + 1e-4, "lo": g - 1e-4, "c": g,
            "sp": np.full(len(g), sp), "thu": np.ones(len(g), dtype=int),
            "n": len(g), "pv": 0.0714, "nam": 1.0}


#: Gia di THANG LEN roi TUT LAI mot doan - ro MUA lai dan roi nha lai.
#: Buoc luoi 60 pip nen chi co MOT tang; tp 400 pip de khong cham TP.
LEN_ROI_TUT = [1.0 + 0.0001 * x for x in range(0, 120)] + \
              [1.0 + 0.0001 * (119 - x) for x in range(0, 60)]

#: XUONG roi LEN. Doan xuong 100 pip xay nhieu tang cho ro MUA (buoc 20 pip),
#: doan len cho ro do co lai. Can nhieu tang MOI TIA DUOC: mot ro mot lenh o
#: lot toi thieu thi cat mot nua la 0,005 lot - duoi `LOT_MIN`, va MT5 tu choi
#: mot lenh nhu vay trong IM LANG.
XUONG_ROI_LEN = [1.0 - 0.0001 * x for x in range(0, 100)] + \
                [1.0 - 0.0001 * (99 - x) for x in range(0, 300)]


class NhaLaiMotPhanDinhLai(unittest.TestCase):
    """`chot_lui_ty` phai dong ro khi lai tut ve mot ty le cua dinh."""

    def _chay(self, **k):
        return MP.mo_phong(_khung(LEN_ROI_TUT), buoc=60.0, tp=400.0,
                           **k)

    def test_khong_bat_thi_khong_co_lan_chot_lui_nao(self):
        r = self._chay()
        self.assertEqual(r.get("chot_lui_nam", 0), 0)

    def test_bat_thi_CO_chot_lui(self):
        r = self._chay(chot_lui_tu=1.0, chot_lui_ty=0.8)
        self.assertGreater(r["chot_lui_nam"], 0, "bat nut ma khong chot lan nao")

    def test_chot_lui_giu_lai_duoc_tien_so_voi_khong_chot(self):
        """Gia len roi tut sach: khong chot thi tra het lai, chot thi giu duoc."""
        khong = self._chay()["lai_nam"]
        co = self._chay(chot_lui_tu=1.0, chot_lui_ty=0.8)["lai_nam"]
        self.assertGreater(co, khong)

    def test_NGUONG_VU_TRANG_duoc_ton_trong(self):
        """Dinh lai chua cham `chot_lui_tu` thi khong duoc chot - neu khong no
        se dong ngay o dong lai dau tien."""
        r = self._chay(chot_lui_tu=1e9, chot_lui_ty=0.8)
        self.assertEqual(r["chot_lui_nam"], 0)

    def test_KHONG_NHIN_TRUOC(self):
        """Dinh phai tinh den BAR TRUOC. Dung dinh cua chinh bar dang xet la
        gia dinh biet truoc gia cao nhat cua bar - loi da lam AUDCAD ra
        6.557%/nam voi von 41 USD."""
        r = self._chay(chot_lui_tu=1.0, chot_lui_ty=0.999999)
        # Voi ty le gan 1, moi bar co dinh moi deu "vua tut khoi dinh" NEU
        # dung dinh cung bar. Dung luat thi so lan chot phai huu han va nho.
        self.assertLess(r["chot_lui_nam"], 500, "co ve dang dung dinh cung bar")


class TiaMotPhanViThe(unittest.TestCase):
    """`tia_ty` cat mot ty le cua ro khi lai cham `tia_tu`, giu phan con lai."""

    def _chay(self, **k):
        """Buoc 20 pip tren doan giam 100 pip -> ro MUA co nhieu tang, nen
        `tia_ty` cat ra mot luong >= LOT_MIN.

        `cat_hoa_tu=999` TAT cat hoa. No bat MAC DINH (cat_hoa_tu=2) va an het
        ro truoc khi lai kip cham nguong tia, nen khong tat thi bai nay do ma
        ly do la mot tinh nang KHAC.
        """
        return MP.mo_phong(_khung(XUONG_ROI_LEN), buoc=20.0, tp=900.0,
                           cat_hoa_tu=999, **k)

    def test_ro_co_du_nhieu_tang_de_tia_duoc(self):
        """Dieu kien can cua ca lop nay - neu ro chi mot tang thi moi bai duoi
        deu 'dat' vi mot ly do sai."""
        self.assertGreaterEqual(self._chay()["tang_max"], 3)

    def test_khong_bat_thi_khong_tia(self):
        self.assertEqual(self._chay().get("tia_nam", 0), 0)

    def test_bat_thi_CO_tia(self):
        r = self._chay(tia_tu=1.0, tia_ty=0.5)
        self.assertGreater(r["tia_nam"], 0)

    def test_tia_KHONG_dong_het_ro(self):
        """Tia la cat mot phan. Dong het thi do la chot, khong phai tia."""
        r = self._chay(tia_tu=1.0, tia_ty=0.5)
        self.assertGreater(r["tia_nam"], 0)
        self.assertGreater(r["tang_max"], 0)

    def test_TY_LE_1_0_bi_tu_choi(self):
        """Tia 100% la dong ca ro - phai goi dung ten no, khong goi la tia."""
        with self.assertRaises(ValueError):
            self._chay(tia_tu=1.0, tia_ty=1.0)

    def test_KHONG_tia_duoi_lot_toi_thieu(self):
        """`PositionClosePartial` duoi `SYMBOL_VOLUME_MIN` that bai IM LANG
        tren MT5. Mo phong cho tia duoi muc do la bang so dep hon that.

        Hieu chuan chieu nguoc nam o `test_bat_thi_CO_tia`: cung khung gia do,
        `tia_ty` du lon thi CO tia. Khong co doi chieu do thi bai nay "dat"
        ngay ca khi ca tinh nang chet.
        """
        r = self._chay(tia_tu=1.0, tia_ty=0.001)
        self.assertEqual(r["tia_nam"], 0,
                         "tia mot luong duoi lot toi thieu - MT5 se tu choi")


class HaiNutNAY_KHONG_PHA_CAI_CU(unittest.TestCase):
    """Them nut khong duoc doi ket qua cua cau hinh khong dung nut do."""

    def test_mac_dinh_giu_nguyen_ket_qua(self):
        d = _khung(LEN_ROI_TUT)
        a = MP.mo_phong(d, buoc=60.0, tp=400.0)
        b = MP.mo_phong(d, buoc=60.0, tp=400.0,
                        chot_lui_tu=None, tia_tu=None)
        self.assertEqual(a["lai_nam"], b["lai_nam"])
        self.assertEqual(a["ro_nam"], b["ro_nam"])


class TiaVaCatHoaTRANH_VIEC_CUA_NHAU(unittest.TestCase):
    """Do 19/09/2026 - phai biet truoc khi doc bat ky bang so nao co `tia_nam`.

    `cat_hoa` bat MAC DINH (`cat_hoa_tu=2`). No dong cac cap ngay khi tong lai
    cua cap vuot `bien_cap`, nen lai CA RO khong bao gio kip cham `tia_tu`.

    Hau qua: mot bang so co `tia_nam = 0` doc nhu "tia vo dung", trong khi that
    ra tia CHUA BAO GIO DUOC CHAY. Do la lan CHUA_DO_DUOC voi ket qua AM - thu
    du an cam.
    """

    def setUp(self):
        self.d = _khung(XUONG_ROI_LEN)
        self.k = dict(buoc=20.0, tp=900.0, tia_tu=1.0, tia_ty=0.5)

    def test_cat_hoa_BAT_thi_tia_khong_kich_hoat(self):
        r = MP.mo_phong(self.d, cat_hoa_tu=2, **self.k)
        self.assertEqual(r["tia_nam"], 0)

    def test_cat_hoa_TAT_thi_tia_kich_hoat(self):
        """Hieu chuan chieu nguoc - khong co bai nay thi bai tren "dat" ngay ca
        khi `tia` hong hoan toan."""
        r = MP.mo_phong(self.d, cat_hoa_tu=999, **self.k)
        self.assertGreater(r["tia_nam"], 0)
