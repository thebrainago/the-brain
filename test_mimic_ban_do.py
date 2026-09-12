# -*- coding: utf-8 -*-
"""Kiem BANG ANH XA `mimic` -> DSL. Nut that cua duong "truy nguoc lich su".

`SO_DO_HE_THONG.txt`: *"Xay dung kha nang truy nguoc lich su giao dich de tim ra
chien luoc roi dung mo phong chien luoc"*.

`ds/mimic` da lam dung viec do: nhan so lenh + bar, chung cat mot cay quyet dinh
nong, tra ve luat dang `"rsi_14 <= 30.0000"`. Nhung luat do chi co gia tri khi
DICH DUOC sang ngu phap DSL - va cho do la mot BANG ANH XA.

Do 12/09/2026: bang do phu **5/7** dac trung. Hai cai con lai bi de `None`, tuc
moi luat mimic hoc duoc ma cham toi chung deu bi bo im lang.

## Va mot cai bay o giua

`price_position` cua mimic nam trong **[0, 1]**; `stochastic` cua DSL la cung
cong thuc nhung **nhan 100**. Dich ma quen he so thi `price_position <= 0,2`
thanh `stochastic <= 0,2` - mot dieu kien gan nhu khong bao gio dung. Luat khong
bien mat, no bien thanh luat CHET.

Cai bay thu hai, o ben mimic: dac trung ten `dist_ma200_atr` nhung cong thuc
chia cho **ma200** chu khong phai ATR. `<= 0,02` nghia la 2%, khong phai 0,02
ATR - lech hai bac do lon.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))
sys.path.insert(0, str(GOC.parent / "ds"))

from nhan import mimic_cau_noi as MC  # noqa: E402
from nhan import ngu_phap as NP       # noqa: E402


class BangAnhXaPhaiPHU_HET(unittest.TestCase):
    def test_moi_dac_trung_cua_mimic_deu_dich_duoc(self):
        try:
            from mimic.features import compute_feature_names
        except Exception as e:
            self.skipTest("khong import duoc ds/mimic: %s" % e)
        ten = compute_feature_names()
        thieu = [t for t in ten if MC.BAN_DO.get(t) is None]
        self.assertEqual(
            thieu, [],
            "dac trung mimic KHONG dich duoc sang DSL - moi luat cham toi chung "
            "bi bo im lang: %s" % thieu)

    def test_moi_muc_trong_ban_do_la_toan_hang_DSL_that(self):
        """Mot muc anh xa tro toi toan hang khong ton tai = luat chet."""
        import pandas as pd
        import numpy as np
        n = 300
        rng = np.random.default_rng(3)
        c = 100 + np.cumsum(rng.normal(0, 0.5, n))
        o = np.r_[c[0], c[:-1]]
        df = pd.DataFrame(
            {"open": o, "high": np.maximum(o, c) + 0.3,
             "low": np.minimum(o, c) - 0.3, "close": c},
            index=pd.date_range("2020-01-01", periods=n, freq="h"))
        for ten, th in MC.BAN_DO.items():
            if th is None:
                continue
            s = NP.toan_hang(df, th)
            self.assertEqual(len(s), n, ten)
            self.assertTrue(np.isfinite(s.to_numpy(float)[-50:]).any(),
                            "toan hang cua '%s' toan NaN" % ten)


class HeSoTHANG_DO_PhaiDuocAP(unittest.TestCase):
    def test_price_position_duoc_nhan_100(self):
        d = MC.dich_dieu_kien("price_position <= 0.2000")
        self.assertTrue(d["nhan"])
        self.assertAlmostEqual(d["dieu_kien"]["phai"]["hang"], 20.0,
                               msg="quen he so 100 -> dieu kien thanh luat chet")
        self.assertEqual(d["dieu_kien"]["trai"]["chi_bao"], "stochastic")

    def test_dac_trung_khong_co_he_so_thi_giu_nguyen(self):
        d = MC.dich_dieu_kien("rsi_14 <= 30.0000")
        self.assertAlmostEqual(d["dieu_kien"]["phai"]["hang"], 30.0)

    def test_dist_ma200_la_TI_LE_khong_phai_ATR(self):
        """Ten dac trung noi 'atr' nhung cong thuc chia cho ma200. Anh xa phai
        tro toi mot toan hang CHIA CHO TRUNG BINH, khong phai chia cho ATR."""
        th = MC.BAN_DO["dist_ma200_atr"]
        self.assertEqual(th["chi_bao"], "lech_tb")
        self.assertEqual(th["n"], 200)


class ToanHangLechTB(unittest.TestCase):
    def test_lech_tb_dung_cong_thuc(self):
        import pandas as pd
        import numpy as np
        c = np.arange(1, 61, dtype=float)
        df = pd.DataFrame({"open": c, "high": c, "low": c, "close": c},
                          index=pd.date_range("2020-01-01", periods=60, freq="D"))
        s = NP.toan_hang(df, {"chi_bao": "lech_tb",
                              "cua": {"chi_bao": "gia", "cot": "close"},
                              "n": 10}).to_numpy(float)
        # tai i = 59: close 60, tb10 cua 51..60 = 55,5 -> (60-55,5)/55,5
        self.assertAlmostEqual(s[-1], (60 - 55.5) / 55.5, places=10)

    def test_khac_zscore(self):
        import pandas as pd
        import numpy as np
        rng = np.random.default_rng(7)
        c = 100 + np.cumsum(rng.normal(0, 1.0, 200))
        df = pd.DataFrame({"open": c, "high": c, "low": c, "close": c},
                          index=pd.date_range("2020-01-01", periods=200, freq="D"))
        a = NP.toan_hang(df, {"chi_bao": "lech_tb",
                              "cua": {"chi_bao": "gia", "cot": "close"},
                              "n": 20}).to_numpy(float)
        b = NP.toan_hang(df, {"chi_bao": "zscore",
                              "cua": {"chi_bao": "gia", "cot": "close"},
                              "n": 20}).to_numpy(float)
        k = np.isfinite(a) & np.isfinite(b)
        self.assertFalse(np.allclose(a[k], b[k]),
                         "lech_tb va zscore ra giong nhau - sai mau so")


if __name__ == "__main__":
    unittest.main(verbosity=2)
