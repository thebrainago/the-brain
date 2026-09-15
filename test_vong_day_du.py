# -*- coding: utf-8 -*-
"""Kiem `nhan/vong_day_du.py` - mot lenh chay ca ba tru.

## Lo hong no va

`SO_DO_HE_THONG.txt` mo ta ba tru NOI TIEP nhau: SEEKER -> QUANTLAB -> EVO.
Nhung do 12/09/2026: `day_chuyen.mot_luot` - cho duy nhat noi cac manh - chi
chay **san -> doc -> boc** roi DUNG. Chinh docstring cua no hua co khau
`DO: bien_don_bay.do_bien + cong`, ma ma nguon khong goi.

He qua neu khong va: mot he "24/7" quay mai o khau thu thap, kho co che phinh
ra, va khong ai cham no.

## Hai tinh chat phai giu

**1. MOT CHANG HONG KHONG CHAN CHANG SAU.** Day chuyen dung o loi dau tien la
day chuyen khong ai dam bat - cung ly do voi `day_viec.py`.

**2. KHONG CHAY LAI THU CON MOI.** Moi chang co han gio. Mot vong day du ma
lan nao cung quet lai tu dau thi khong ai dam chay no.
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import vong_day_du as V  # noqa: E402


class MotChangHongKhongChanChangSau(unittest.TestCase):
    def test_chang_nem_loi_van_tra_ve_dict(self):
        def no():
            raise RuntimeError("hong co y")
        r = V._chang("THU", no, lambda *a: None)
        self.assertFalse(r["ok"])
        self.assertIn("RuntimeError", r["loi"])
        self.assertIn("giay", r)

    def test_chang_chay_duoc_thi_ok(self):
        r = V._chang("THU", lambda: {"so": 7}, lambda *a: None)
        self.assertTrue(r["ok"])
        self.assertEqual(r["so"], 7)

    def test_chang_tra_ve_thu_khong_phai_dict_van_song(self):
        r = V._chang("THU", lambda: "mot chuoi", lambda *a: None)
        self.assertTrue(r["ok"])
        self.assertIn("ket", r)


class HanGioPhaiCHAN_CHAY_LAI(unittest.TestCase):
    def test_moi_chang_dat_deu_co_han_gio(self):
        for k in ("ho_so", "noi_sinh", "suy_nguoc", "to_hop"):
            self.assertIn(k, V.HAN_GIO)
            self.assertGreater(V.HAN_GIO[k], 0)

    def test_tep_chua_co_thi_tuoi_la_VO_CUNG(self):
        """Chua co thi phai CHAY, khong duoc coi la con moi."""
        self.assertEqual(V._tuoi("KHONG_CO_TEP_NAY_12345.json"),
                         float("inf"))

    def test_tep_vua_ghi_thi_tuoi_gan_0(self):
        p = GOC / "reports" / "_thu_tuoi.json"
        p.parent.mkdir(exist_ok=True)
        p.write_text("{}", encoding="utf-8")
        try:
            self.assertLess(V._tuoi("_thu_tuoi.json"), 0.1)
        finally:
            p.unlink(missing_ok=True)


class VongPhaiDU_SAU_CHANG(unittest.TestCase):
    def test_co_du_ham_cua_sau_chang(self):
        # Danh sach chang DOC TU CHINH `vong()` thay vi go cung. Ban cu cung
        # so 6; them chang CHAM_TIEN va DA_THOI_DAI (12/09) lam test do voi
        # "7 != 6" - tuc test dang kiem mot con so, khong kiem mot tinh chat.
        for t in V.TEN_CHANG:
            self.assertTrue(hasattr(V, t), "thieu chang %s" % t)

    def test_vong_ghi_so_va_liet_ke_chang_hong(self):
        """Chay `vong` voi moi chang bi thay bang mot ham hong: phai chay HET,
        ghi so, va liet ke du cac chang hong."""
        goc = {}
        # Danh sach chang DOC TU CHINH `vong()` thay vi go cung. Ban cu cung
        # so 6; them chang CHAM_TIEN va DA_THOI_DAI (12/09) lam test do voi
        # "7 != 6" - tuc test dang kiem mot con so, khong kiem mot tinh chat.
        for t in V.TEN_CHANG:
            goc[t] = getattr(V, t)

            def no(*a, **k):
                raise RuntimeError("hong")
            setattr(V, t, no)
        goc_han = dict(V.HAN_GIO)
        for k in V.HAN_GIO:
            V.HAN_GIO[k] = 0.0            # ep chay moi chang
        try:
            k = V.vong("XM_US500CASH", ("D1",), sp=1, in_ra=lambda *a: None)
        finally:
            for t, f in goc.items():
                setattr(V, t, f)
            V.HAN_GIO.update(goc_han)
        self.assertEqual(len(k["chang"]), len(V.TEN_CHANG),
                         "khong chay du %d chang" % len(V.TEN_CHANG))
        self.assertEqual(len(k["hong"]), len(V.TEN_CHANG),
                         "chang hong khong duoc liet ke du")
        self.assertTrue(V.SO.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_bang_tong_ket_liet_ke_CA_TAM_CHANG():
    """Ban cu chi ghi chang DA CHAY, nen mot vong `--nhanh` in ra 5 dong va
    nguoi doc khong phan biet duoc "bo qua co chu dich" voi "bien mat im lang".

    Do 15/09/2026: `b vong --nhanh` in cac chang 2,3,6,7,8 - thieu 1,4,5 ma
    khong mot dong nao noi vi sao trong BANG (chi co mot dong roi o giua log).
    """
    from nhan import vong_day_du as V
    assert len(V.TEN_HIEN) == len(V.TEN_CHANG) == 8
    s = (Path(__file__).resolve().parent / "nhan" / "vong_day_du.py").read_text(
        encoding="utf-8-sig")
    assert "BO QUA" in s and "KHONG RO VI SAO" in s, (
        "bang tong ket khong con phan biet BO QUA voi HONG")
    assert "chang chay, %d bo qua" in s


def test_moi_chang_BI_BO_deu_ghi_LY_DO():
    """Mot chang bi bo ma khong ro ly do thi khong doc duoc - phai la
    CHUA_DO_DUOC co giai thich, khong phai mot cho trong.
    """
    from nhan import vong_day_du as V
    s = (Path(__file__).resolve().parent / "nhan" / "vong_day_du.py").read_text(
        encoding="utf-8-sig")
    assert s.count("bo_qua.append(") == 3, (
        "co %d cho bo chang ma ghi ly do - phai du ba (nhanh, suy_nguoc, to_hop)"
        % s.count("bo_qua.append("))
    assert '"bo_qua": [{"ten": t, "vi_sao": v} for t, v in bo_qua]' in s, (
        "ly do bo chang khong duoc ghi vao file ket qua")
