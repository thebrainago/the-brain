# -*- coding: utf-8 -*-
"""Kiem duong DSL -> MQL5: `dich_mq5`, `dich_mq5_ghep`, `dich_mq5_qtvt`,
`dich_mq5_quan_tri`, `doi_khung`, `quan_tri_dsl`.

Sau tep nay la duong tu mot khai bao DSL den mot lan chay tester THAT - tuc la
den moi con so du an dung de quyet dinh. Chung ra doi ngay 07/09 va den 11/09
van chua co bai kiem nao (`test_hien_phap` keu suot bon ngay).

Cac bai kiem o day khong kiem "ma sinh ra co dep khong" - chung kiem HAI thu:
  1. cai gi KHONG dich duoc thi phai bi BO kem ly do, khong duoc lang le sinh
     ra mot EA khac voi khai bao;
  2. cac chot an toan (martingale, tran vi the, don vi khoang cach) con nguyen.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import dich_mq5 as D  # noqa: E402
from nhan import quan_tri_dsl as QT  # noqa: E402


def _spec(ten="thu", vao=None, ra=None, chieu=1, giu=1):
    return {"ten": ten, "ho": "quay_ve_trung_binh", "chieu": chieu, "giu": giu,
            "vao": vao if vao is not None else
            [{"trai": {"chi_bao": "rsi", "n": 2}, "phep": "<",
              "phai": {"hang": 10.0}}],
            "ra": ra or [],
            "co_che": "Ca kiem duong dich - khong dang ky vao he."}


class SinhEA_CHO_NHIEU_CO_CHE(unittest.TestCase):
    def test_dich_duoc_thi_ra_ma_va_danh_sach(self):
        ma, dat = D.sinh_ea([_spec()], ten="ThuEA", khung="D1")
        self.assertIn("ThuEA", ma + "ThuEA")
        self.assertGreaterEqual(len(dat), 1)
        self.assertIn("VAO", ma)

    def test_them_mua_giu_la_MOC_bat_buoc(self):
        """Moi bang ket qua phai co dong mua-giu de so sanh. Bo no di thi mot he
        'co lai' khong con doi chieu duoc voi viec khong lam gi ca."""
        _, co = D.sinh_ea([_spec()], khung="D1", them_mua_giu=True)
        _, khong = D.sinh_ea([_spec()], khung="D1", them_mua_giu=False)
        self.assertEqual(len(co), len(khong) + 1)

    def test_KHONG_dich_duoc_thi_BO_kem_ly_do(self):
        """Sinh ra mot EA KHAC voi khai bao la dang hong te nhat: no van chay,
        van ra so, va con so do noi ve mot co che khong ai viet."""
        xau = _spec(ten="la", vao=[{"trai": {"chi_bao": "mot_chi_bao_khong_ton_tai"},
                                    "phep": "<", "phai": {"hang": 1.0}}])
        # Ca me KHONG dich duoc thi ham NEM chu khong tra ve EA rong - dung, vi
        # mot EA khong co co che nao van chay duoc trong tester va van ghi ra
        # mot bang ket qua. Bang do se doc nhu "da thu, khong an gi".
        with self.assertRaises(D.KhongDichDuoc):
            D.sinh_ea([xau], khung="D1", them_mua_giu=False)
        self.assertIn("_khong_dich", xau, "bo roi ma khong ghi ly do")
        self.assertTrue(str(xau["_khong_dich"]).strip())

    def test_mot_co_che_hong_KHONG_lam_hong_ca_me(self):
        xau = _spec(ten="la", vao=[{"trai": {"chi_bao": "khong_biet"},
                                    "phep": "<", "phai": {"hang": 1.0}}])
        _, dat = D.sinh_ea([xau, _spec(ten="tot")], khung="D1",
                           them_mua_giu=False)
        self.assertEqual([d["ten"] for d in dat], ["tot"])

    def test_dich_PLACEBO_giu_nguyen_chuoi_tin_hieu(self):
        """`_dich` la placebo dung cach cho duong tester: giu nguyen ty le kich
        hoat va cum, chi pha su khop thoi diem. Hoan vi lai/lo thi luon ra ~50%
        - do la loi da mac 29/07."""
        s = _spec(ten="placebo")
        s["_dich"] = 7
        ma, dat = D.sinh_ea([s], khung="D1", them_mua_giu=False)
        self.assertEqual(len(dat), 1)
        self.assertIn("s+7", ma, "co `_dich` ma ma sinh ra khong he dich bar")


class CongQuanTriGIU_CAC_CHOT_AN_TOAN(unittest.TestCase):
    """Nhung chot nay khong phai so thich - moi cai la mot lan da chay tai khoan."""

    def test_khong_co_luat_nao_thi_tu_choi(self):
        self.assertTrue(QT.kiem_khai_bao({"ten": "rong"}))

    def test_thieu_ten_thi_tu_choi(self):
        self.assertIn("thieu 'ten'",
                      QT.kiem_khai_bao({"dat_hue": {"kich_hoat": {"atr": 1.0}}}))

    def test_NHOI_khong_co_tran_bi_tu_choi(self):
        loi = QT.kiem_khai_bao({"ten": "nhoi_khong_tran",
                                "nhoi": {"buoc": {"atr": 1.0}}})
        self.assertTrue(any("chay tai khoan" in x for x in loi), loi)

    def test_MARTINGALE_tren_lot_bi_tu_choi(self):
        """lot_x > 1,0 - da do DD 99,98% ngay TRONG mau."""
        loi = QT.kiem_khai_bao({
            "ten": "martingale", "nhoi": {"buoc": {"atr": 1.0}, "lot_x": 1.5},
            "chan": {"so_vi_the_toi_da": 5}})
        self.assertTrue(any("martingale" in x for x in loi), loi)

    def test_nhoi_co_tran_va_lot_x_KHONG_tang_thi_qua(self):
        self.assertEqual(QT.kiem_khai_bao({
            "ten": "nhoi_lanh", "nhoi": {"buoc": {"atr": 1.0}, "lot_x": 1.0},
            "chan": {"so_vi_the_toi_da": 5}}), [])

    def test_KHOANG_CACH_phai_co_DON_VI(self):
        """Mot con so khong don vi tren vang va tren EURUSD la hai the gioi."""
        loi = QT.kiem_khai_bao({"ten": "thieu_don_vi",
                                "dat_hue": {"kich_hoat": {"gia_tri": 50}}})
        self.assertTrue(any("thieu don vi" in x for x in loi), loi)

    def test_sang_atr_quy_moi_khoang_cach_ve_boi_ATR(self):
        s = {"ten": "t", "dat_hue": {"kich_hoat": {"atr": 2.0}}}
        r = QT.sang_atr(dict(s), atr=1.5, gia_diem=0.01)
        self.assertIsInstance(r, dict)
        self.assertEqual(r["ten"], "t")

    def test_van_tay_theo_CAU_TRUC_khong_theo_TEN(self):
        a = {"ten": "mot", "dat_hue": {"kich_hoat": {"atr": 1.0}}}
        b = {"ten": "hai", "dat_hue": {"kich_hoat": {"atr": 1.0}}}
        self.assertEqual(QT.van_tay(a), QT.van_tay(b),
                         "doi TEN ma van tay doi -> kho se day ban trung")


class CacBoDichKHAC_DEU_NAP_DUOC(unittest.TestCase):
    """Chan tho. Mot module trong day chuyen ma import loi thi ca duong ra
    tester dut, va trieu chung se hien ra o mot cho khac han."""

    def test_nap_duoc_va_co_cua_vao(self):
        from nhan import dich_mq5_ghep as G
        from nhan import dich_mq5_qtvt as Q
        from nhan import dich_mq5_quan_tri as QTr
        from nhan import doi_khung as DK
        for mod, ham in ((G, "sinh_ea_ghep"), (Q, "sinh_ea_giam_sat"),
                         (QTr, "sinh_ea_quan_tri"), (DK, "doi")):
            with self.subTest(mod=mod.__name__):
                self.assertTrue(callable(getattr(mod, ham, None)),
                                f"{mod.__name__}.{ham} khong goi duoc")

    def test_ghep_nhieu_he_ra_MOT_ea(self):
        from nhan import dich_mq5_ghep as G
        ma, dat = G.sinh_ea_ghep([_spec(ten="a"), _spec(ten="b", chieu=-1)],
                                 ten="ThuGhep", khung="D1")
        self.assertGreaterEqual(len(dat), 2)
        self.assertIsInstance(ma, str)
        self.assertGreater(len(ma), 200)

    def test_doi_khung_GIU_TY_LE_KICH_HOAT_chu_khong_giu_con_so(self):
        """Cai khong doi khi sang khung khac la DO HIEM cua su kien. Quy doi chu
        ky theo ti le bar la CAN NHUNG KHONG DU - da do 07/09 tren 36 chan."""
        import inspect
        from nhan import doi_khung as DK
        tl = inspect.getsource(DK)
        self.assertIn("phan vi", tl.lower().replace("_", " "),
                      "doi_khung khong he khop phan vi - no dang chi quy doi chu ky")


if __name__ == "__main__":
    unittest.main()
