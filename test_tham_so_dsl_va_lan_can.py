# -*- coding: utf-8 -*-
"""LAN CAN SUY BIEN CHO RA "CAO NGUYEN" GIA.

Do 03/09/2026. `do_on_dinh` tra loi cau hoi "cao nguyen hay cai gai" bang cach
chay quanh mot tam. Cau tra loi chi co nghia neu cac o THAT SU khac nhau. Hai
duong lam no suy bien, ca hai deu am tham:

  1. MAU DIEC. Closure cua 152 co che DSL la `def _ham(df, _s=spec, **_)` -
     `**_` nuot sach moi tham so. `lan_can` sinh du 81 o, ca 81 o goi cung mot
     spec, tra ve ket qua Y HET nhau -> "100% lan can duong, do doc 0%".
  2. LAN CAN BI DONG BANG. Voi 7-8 tham so, `lan_can` dong bang tung truc de
     giu duoi tran 81 o, va co the rot ve DUNG MOT o.

Ca hai cho ra mot phan quyet on dinh dep de ma bo do chua bao gio co co hoi
noi "khong" - cung lop loi voi mot cong tu choi tat ca ma van co so lieu dep.
"""
import unittest

import numpy as np
import pandas as pd

import do_on_dinh as OD
from nhan import mau as M
from nhan import ngu_phap as NP


def _df(n: int = 1200) -> pd.DataFrame:
    """Khung gia GIA LAP nhung phai co bien do THAT trong tung bar.

    Ban dau bai nay dung `high=g+1, low=g-1, close=g`: IBS khi do LUON dung
    0,5, nen ca ho IBS khong bao gio kich hoat va bi cham nham la "diec"
    (27/170 tren khung do, so voi 4/170 tren US500CASH that). Mot khung gia
    lap khong co bien do trong bar va khong co khoi luong bien thien thi
    khong kiem duoc gi ve cac co che doc hai thu do.
    """
    r = np.random.default_rng(3)
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    dong = 100 + np.cumsum(r.normal(0, 1, n))
    mo = np.concatenate(([dong[0]], dong[:-1])) + r.normal(0, 0.3, n)
    bd = np.abs(r.normal(0, 1.2, n)) + 0.2
    tren = np.maximum(mo, dong) + bd * r.random(n)
    duoi = np.minimum(mo, dong) - bd * r.random(n)
    return pd.DataFrame({"open": mo, "high": tren, "low": duoi, "close": dong,
                         "tick_volume": r.lognormal(7.0, 0.6, n)}, index=idx)


SPEC = {
    "ten": "thu_zscore_tham_so", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 2,
    "vao": [{"trai": {"chi_bao": "zscore", "cua": {"chi_bao": "gia", "cot": "close"},
                      "n": 20},
             "phep": "<", "phai": {"hang": -2.0}}],
    "ra": [{"trai": {"chi_bao": "zscore", "cua": {"chi_bao": "gia", "cot": "close"},
                     "n": 20}, "phep": ">", "phai": {"hang": 0.0}}],
}


class PhoiBayThamSo(unittest.TestCase):
    def test_tim_duoc_moi_hang_so_chinh_duoc(self):
        ts = NP.tham_so_cua(SPEC)
        self.assertEqual(ts, {"vao0_trai_n": 20, "vao0_phai_hang": -2.0,
                              "ra0_trai_n": 20, "ra0_phai_hang": 0.0, "giu": 2})

    def test_ap_tham_so_khong_sua_spec_goc(self):
        goc = NP.tham_so_cua(SPEC)
        moi = NP.ap_tham_so(SPEC, {**goc, "vao0_trai_n": 50})
        self.assertEqual(moi["vao"][0]["trai"]["n"], 50)
        self.assertEqual(SPEC["vao"][0]["trai"]["n"], 20, "spec goc bi sua tai cho")

    def test_ap_tham_so_giu_KIEU(self):
        moi = NP.ap_tham_so(SPEC, {"vao0_trai_n": 33.0, "giu": 4})
        self.assertIsInstance(moi["vao"][0]["trai"]["n"], int)
        self.assertEqual(moi["giu"], 4)

    def test_khoa_la_khong_doi_qua_hai_lan_goi(self):
        self.assertEqual(NP.tham_so_cua(SPEC), NP.tham_so_cua(SPEC))


class ClosureKhongDuocNuotThamSo(unittest.TestCase):
    """Loi goc: `**_`. Neu no quay lai, bai nay do."""

    def setUp(self):
        NP.nap_vao_mau()
        self.df = _df()

    def test_moi_mau_deu_phan_ung_voi_it_nhat_mot_tham_so(self):
        diec = []
        for ten, spec in M.MAU.items():
            tam = spec.get("tham_so_tam") or (spec.get("luoi") or [{}])[0]
            if not tam:
                continue
            try:
                goc = np.nan_to_num(np.asarray(M.sinh(ten, self.df, tam), float))
            except M.KhungThieuGio:
                continue
            except Exception:
                continue
            doi = False
            for ts in OD.lan_can(tam):
                if ts == tam:
                    continue
                try:
                    v = np.nan_to_num(np.asarray(M.sinh(ten, self.df, ts), float))
                except Exception:
                    continue
                if not np.array_equal(goc, v):
                    doi = True
                    break
            if not doi:
                diec.append(ten)
        # Con mot vai mau DIEC that su (vd chi loc theo lich) thi van chap nhan,
        # nhung TUYET DAI DA SO phai phan ung. Truoc ban va: 152/170 diec.
        ty = 1.0 - len(diec) / max(1, len(M.MAU))
        self.assertGreater(ty, 0.90,
                           f"{len(diec)}/{len(M.MAU)} mau diec: {diec[:8]}")

    def test_mau_DSL_cu_the_doi_theo_tham_so(self):
        ten = next((k for k, v in M.MAU.items()
                    if v.get("dsl") and v.get("tham_so_tam")), None)
        self.assertIsNotNone(ten, "khong co mau DSL nao co tham so")
        tam = M.MAU[ten]["tham_so_tam"]
        khoa_n = next((k for k in tam if k.endswith("_n")), None)
        if khoa_n is None:
            self.skipTest("mau DSL dau tien khong co cua so nhin lai")
        a = M.sinh(ten, self.df, tam)
        b = M.sinh(ten, self.df, {**tam, khoa_n: int(tam[khoa_n]) * 3 + 1})
        self.assertFalse(np.array_equal(np.nan_to_num(a), np.nan_to_num(b)))


class LanCanSuyBienThiTuChoi(unittest.TestCase):
    """`do_hinh_dang` khong duoc dat ten hinh dang cho mot lan can suy bien."""

    def _gia_lap(self, alphas):
        """Thay `do_mot_o` bang mot ham tra ve alpha cho san."""
        goc = OD.do_mot_o
        cac = list(alphas)

        def _thay(mau, tham_so, tai_san, khung):
            return {"tham_so": tham_so, "alpha": cac[min(len(cac) - 1, _thay.i)],
                    "t": 1.0, "sharpe": 0.5, "so_lenh": 100}
        _thay.i = 0

        def _dem(*a, **k):
            r = _thay(*a, **k)
            _thay.i += 1
            return r
        return goc, _dem

    def test_moi_o_giong_nhau_thi_KHONG_DO_DUOC(self):
        goc, thay = self._gia_lap([5.0])
        OD.do_mot_o = thay
        try:
            r = OD.do_hinh_dang("ibs_bat_day", {"nguong": 0.2, "giu": 1},
                                "US500CASH", "D1", luong=1)
        finally:
            OD.do_mot_o = goc
        self.assertFalse(r["do_duoc"])
        self.assertIn("SUY BIEN", r["ly_do"])
        self.assertEqual(r["hinh_dang"], "KHONG DO DUOC")
        self.assertEqual(r["so_o_khac_nhau"], 1)

    def test_lan_can_that_su_khac_nhau_thi_VAN_do_duoc(self):
        """Hieu chuan chieu nguoc: gac nay khong duoc tu choi tat ca."""
        goc, thay = self._gia_lap([1.0, 2.0, 3.0, 4.0, 5.0] * 40)
        OD.do_mot_o = thay
        try:
            r = OD.do_hinh_dang("ibs_bat_day", {"nguong": 0.2, "giu": 1},
                                "US500CASH", "D1", luong=1)
        finally:
            OD.do_mot_o = goc
        self.assertTrue(r["do_duoc"], r.get("ly_do"))
        self.assertGreater(r["so_o_khac_nhau"], 1)
        self.assertNotEqual(r["hinh_dang"], "KHONG DO DUOC")


if __name__ == "__main__":
    unittest.main()
