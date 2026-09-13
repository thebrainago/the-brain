# -*- coding: utf-8 -*-
"""Kiem `nhan/to_hop.py` - pheu to hop da cap x da khung x da quan li x da thong so.

Module nay nguy hiem theo mot kieu rieng: no chay HANG TRAM NGHIN o roi in ra
mot bang xep hang. Neu phep TIA sai thi khong ai nhin thay - bang van dep, chi
la no da bo mat nua khong gian, hoac da dem hai lan cung mot tai san duoi hai
cai ten. Nen o day kiem PHEP TIA va PHEP GOP, khong kiem "chay duoc".

Va mot dieu nua phai kiem bang test chu khong bang thien chi: bang tong ket
PHAI mang canh bao thien lech chon loc. Chang 1 da chon top N theo chinh
`cagr_dd20` roi chang 2 mo rong dung nhung o do, nen con so "hon moc" o bang
chang 2 bi thoi len boi chinh phep chon. Ai doc ma khong biet dieu do se tuong
he vua tim ra hang chuc he thang moc.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import to_hop as TH  # noqa: E402


class PhepTiaPhaiDUNG(unittest.TestCase):
    def test_bo_ban_sao_nhung_GIU_mot_dai_dien(self):
        cap = {"A|B": {"r": 1.0, "trung": True},
               "B|C": {"r": 0.99, "trung": True}}
        import nhan.ho_so_tuong_quan as TQ
        that = TQ.doc
        TQ.doc = lambda khung="D1": {"cap": cap}
        try:
            giu, bo = TH.ma_khong_trung(["A", "B", "C", "D"], "D1")
        finally:
            TQ.doc = that
        self.assertIn("D", giu, "ma khong lien quan bi bo oan")
        self.assertEqual(len(set(bo) & set(giu)), 0, "vua bo vua giu mot ma")
        # ca ba A/B/C la mot thu -> phai con DUNG mot dai dien
        self.assertEqual(len([m for m in giu if m in ("A", "B", "C")]), 1,
                         "ba ban sao ma giu lai %s" % giu)

    def test_khong_co_ho_so_tuong_quan_thi_GIU_NGUYEN(self):
        """Mot module tia khong duoc tu y chay lai 40 giay CPU, va cung khong
        duoc bo bua khi thieu du lieu."""
        import nhan.ho_so_tuong_quan as TQ
        that = TQ.doc
        TQ.doc = lambda khung="D1": {}
        try:
            giu, bo = TH.ma_khong_trung(["A", "B", "C"], "D1")
        finally:
            TQ.doc = that
        self.assertEqual(giu, ["A", "B", "C"])
        self.assertEqual(bo, {})

    def test_khoang_kich_hoat_hop_le(self):
        lo, hi = TH.KICH_HOAT
        self.assertGreater(lo, 0.0)
        self.assertLess(hi, 1.0)
        self.assertLess(lo, hi)

    def test_co_che_ngoai_khoang_kich_hoat_bi_loai(self):
        import nhan.ngu_phap as NP
        that = NP.doc_kho
        NP.doc_kho = lambda: [
            {"ten": "qua_thua", "_ty_le_kich_hoat": 0.001},
            {"ten": "vua", "_ty_le_kich_hoat": 0.20},
            {"ten": "qua_day", "_ty_le_kich_hoat": 0.95},
            {"ten": "khong_do", "_ty_le_kich_hoat": None},
        ]
        try:
            ten = [s["ten"] for s in TH.co_che_dung_duoc()]
        finally:
            NP.doc_kho = that
        self.assertEqual(ten, ["vua"])


class PhepGOP_PhaiDUNG(unittest.TestCase):
    def _rows(self):
        return [
            {"khung": "D1", "cagr_dd20": 2.0, "hon_moc": True},
            {"khung": "D1", "cagr_dd20": -1.0, "hon_moc": False},
            {"khung": "H4", "cagr_dd20": -3.0, "hon_moc": False},
            {"khung": "H4", "cagr_dd20": -5.0, "hon_moc": False},
        ]

    def test_xep_theo_trung_vi_giam_dan(self):
        b = TH._theo_chieu(self._rows(), "khung")
        self.assertEqual([r["gia_tri"] for r in b], ["D1", "H4"])

    def test_dem_dung_so_o_va_ti_le_duong(self):
        b = {r["gia_tri"]: r for r in TH._theo_chieu(self._rows(), "khung")}
        self.assertEqual(b["D1"]["so_o"], 2)
        self.assertEqual(b["D1"]["hon_moc"], 1)
        self.assertAlmostEqual(b["D1"]["ti_le_duong"], 0.5)
        self.assertEqual(b["H4"]["hon_moc"], 0)
        self.assertAlmostEqual(b["H4"]["ti_le_duong"], 0.0)

    def test_tot_nhat_la_CUC_DAI_khong_phai_trung_vi(self):
        b = {r["gia_tri"]: r for r in TH._theo_chieu(self._rows(), "khung")}
        self.assertAlmostEqual(b["D1"]["tot_nhat"], 2.0)


class TongKetPhaiMANG_CANH_BAO(unittest.TestCase):
    def test_bao_cao_noi_ro_thien_lech_chon_loc(self):
        ket = {"so_ma": 3, "khung": ["D1"], "giay": 1.0,
               "tat_ca_chang2": [
                   {"khung": "D1", "cau_truc": "thi_truong", "luat": "-",
                    "ho": "x", "ma": "A", "cagr_dd20": 1.0, "hon_moc": True,
                    "moc_dd20": 0.0, "co_che": "c1"},
                   {"khung": "D1", "cau_truc": "tt_hedge", "luat": "-",
                    "ho": "x", "ma": "A", "cagr_dd20": -1.0, "hon_moc": False,
                    "moc_dd20": 0.0, "co_che": "c1"}]}
        vb = TH.tong_ket(ket, in_ra=lambda *a, **k: None)
        self.assertIn("DOC BANG NAY NHU THE NAO", vb)
        self.assertIn("bi thoi len boi chinh phep", vb)
        self.assertIn("NEN DI", vb)
        self.assertIn("NEN TRANH", vb)

    def test_khong_o_nao_thang_moc_thi_NOI_THANG(self):
        ket = {"so_ma": 1, "khung": ["D1"], "giay": 1.0,
               "tat_ca_chang2": [
                   {"khung": "D1", "cau_truc": "thi_truong", "luat": "-",
                    "ho": "x", "ma": "A", "cagr_dd20": -1.0, "hon_moc": False,
                    "moc_dd20": 5.0, "co_che": "c1"},
                   {"khung": "H4", "cau_truc": "tt_hedge", "luat": "-",
                    "ho": "x", "ma": "A", "cagr_dd20": -2.0, "hon_moc": False,
                    "moc_dd20": 5.0, "co_che": "c1"}]}
        vb = TH.tong_ket(ket, in_ra=lambda *a, **k: None)
        self.assertIn("Khong o nao thang moc", vb)
        self.assertIn("khong phai mot", vb)


class LuoiThamSoPhaiDO_DO_NHAY(unittest.TestCase):
    def test_luoi_co_cap_lan_can_de_do_cao_nguyen(self):
        """`cao-nguyen-hay-cai-gai`: mot luoi ma moi diem mot goc troi thi khong
        noi duoc edge la cao nguyen hay cai gai."""
        sl = sorted({t.get("sl_atr") for t in TH.LUOI_THAM if "sl_atr" in t})
        self.assertGreaterEqual(len(sl), 3, "luoi khong du diem de do do nhay")

    def test_giu_chang_giam_dan(self):
        self.assertGreater(TH.GIU_CHANG1, TH.GIU_CHANG2,
                           "pheu phai HEP dan, khong thi khong phai pheu")


if __name__ == "__main__":
    unittest.main(verbosity=2)


# --------------------------------------------- THU TU DUYET PHAI THEO PHEP DO
#
# Them 13/09/2026. `co_che_dung_duoc` truoc do xep theo TEN (bang chu cai), nen
# khi `gioi_han` cat bot thi cai bi cat la cai co ten van bang Z - hoan toan
# ngau nhien so voi chat luong.
#
# Do tren 1.276 ket qua da cham:
#     phoi nhiem 10-25%: 494 phep thu (39%), ty le PASS 1,2%, CAGR tv -0,42%
#     phoi nhiem 25-40%: 104 phep thu ( 8%), ty le PASS 4,8%, CAGR tv +0,86%
# Pheu tieu 39% cong suc vao vung ngheo nhat va 8% vao vung tot nhat.
#
# `_ty_le_kich_hoat` trong kho du bao phoi nhiem that voi r = 0,964 (97 cap),
# nen no xep hang truoc duoc.

def test_thu_tu_duyet_uu_tien_vung_sinh_loi():
    from nhan import to_hop as TH
    ds = TH.co_che_dung_duoc()
    assert len(ds) > 200, "kho qua nho de kiem thu tu"
    lo, hi = TH.VUNG_SINH_LOI
    n = min(300, len(ds) // 2)
    dau = sum(1 for s in ds[:n]
              if lo <= float(s["_ty_le_kich_hoat"]) <= hi)
    cuoi = sum(1 for s in ds[-n:]
               if lo <= float(s["_ty_le_kich_hoat"]) <= hi)
    assert dau > cuoi * 3, (
        "%d/%d cai DUYET DAU nam trong vung sinh loi, %d/%d cai CUOI - thu tu "
        "khong uu tien gi" % (dau, n, cuoi, n))


def test_van_giu_DU_co_che_khong_loai_them():
    """Doi thu tu KHONG duoc lam mat co che nao - do la mot cong tra hinh."""
    from nhan import ngu_phap as NP
    from nhan import to_hop as TH
    lo, hi = TH.KICH_HOAT
    du = [s for s in NP.doc_kho()
          if s.get("_ty_le_kich_hoat") is not None
          and lo <= float(s["_ty_le_kich_hoat"]) <= hi]
    assert len(TH.co_che_dung_duoc()) == len(du)


def test_tran_kich_hoat_060_co_co_so():
    """Tran tren KHONG duoc noi: nhom >=60% la nhom TE NHAT (356 mau, CAGR
    tv -1,89%, ty le PASS 0%). Ghi chu goc cua no khong neu phep do nao, nen
    phep do nam o day."""
    from nhan import to_hop as TH
    assert TH.KICH_HOAT[1] <= 0.60
    assert TH.VUNG_SINH_LOI[1] <= TH.KICH_HOAT[1]
