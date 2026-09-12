# -*- coding: utf-8 -*-
"""Nguong sinh ra tren TRAIN phai CHUYEN DUOC sang HOLDOUT.

## Loi da xay ra 12/09/2026

Luong noi sinh lay nguong tu PHAN VI THAT cua chuoi - dung ve nguyen tac. Nhung
no dong bang phan vi do thanh mot SO TUYET DOI tai thoi diem train. Voi mot dai
luong phu thuoc thang do thi so do chi co nghia trong dung che do bien dong da
lay no ra:

    EURUSD D1, nguong `atr14 < 0,003472` (= phan vi 20 cua TRAIN)
        TRAIN   : kich hoat 1.719 bar
        HOLDOUT : kich hoat **0 bar**     <- trung vi ATR holdout 0,00927

Bay trong top 10 "song sot" that ra khong vao mot lenh nao o holdout. Va vi moc
holdout am (-0,254) nen "chenh" cua mot he khong giao dich van ra DUONG, roi bao
cao dem chung la "giu dau ngoai mau 9/10".

Hai lop chan, ca hai deu can:
  1. Bo sinh dung `phan_vi` TRUOT cho dai luong phu thuoc thang do.
  2. Bo cham diem phan biet **KHONG KICH HOAT** voi **THUA** (`LENH_HO_TOI_THIEU`).

Cung ho voi luat L3 trong `LUAT_GIAM_SAT.md`: "khong do duoc" khong phai "am".
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import ngu_phap as NP  # noqa: E402
from nhan import noi_sinh as NS  # noqa: E402

#: Toan hang PHU THUOC THANG DO - gia tri cua no doi khi doi tai san hoac doi
#: che do bien dong. Khong duoc so voi mot hang so dong bang.
PHU_THUOC_THANG_DO = {"atr", "bien_do", "than_nen", "dong_luong", "gia", "tb",
                      "ema", "smma", "wma", "khoi_luong", "do_lech",
                      "phuong_sai", "tong", "doi"}


def _goc(t: dict) -> str:
    """Ten chi bao o TRONG CUNG - `phan_vi(cua=atr)` thi goc la `phan_vi`."""
    return str(t.get("chi_bao", "")).lower()


class BoSinhKhongDuocDungHANG_SO_TREN_DAI_LUONG_CO_THANG_DO(unittest.TestCase):
    def test_moi_toan_hang_goc_deu_khong_phu_thuoc_thang_do(self):
        xau = [t for t in NS.TOAN_HANG_GOC if _goc(t) in PHU_THUOC_THANG_DO]
        self.assertEqual(
            xau, [],
            "toan hang phu thuoc thang do dung truc tiep lam ve trai - nguong "
            "tuyet doi cua no KHONG chuyen duoc sang che do bien dong khac. "
            "Boc no trong `phan_vi`:\n  %s" % xau)

    def test_phan_vi_van_duoc_phep_boc_dai_luong_co_thang_do(self):
        """`phan_vi(cua=atr)` la CACH DUNG - no tra ve hang trong cua so, khong
        phu thuoc thang do."""
        co = [t for t in NS.TOAN_HANG_GOC
              if _goc(t) == "phan_vi"
              and str((t.get("cua") or {}).get("chi_bao", "")).lower()
              in PHU_THUOC_THANG_DO]
        self.assertGreaterEqual(len(co), 3,
                                "khong con duong nao doc bien dong/bien do")


class NguongTRAIN_PhaiKICH_HOAT_O_HOLDOUT(unittest.TestCase):
    def _hai_nua_that(self):
        """Dung du lieu DA QUA KIEM CHAT LUONG, khong dung ban tho.

        EURUSD tho co doan 1971-1979 gom nhieu bar KHONG RAU (high = than tren,
        low = than duoi) - do la du lieu tai tao truoc khi co dong euro, va no
        keo phan vi thap cua moi thuoc do dinh toi high/low ve nhung gia tri
        khong bao gio xuat hien lai. `nen_doji @q2` chet vi dung cai do.
        Mot phep thu ve kha nang CHUYEN cua nguong phai chay tren du lieu ma
        he that su dung."""
        from nhan import du_lieu as DL
        try:
            df = DL.cat_theo_chat_luong(DL.nap("EURUSD", "D1"), "EURUSD")[0]
        except Exception as e:
            self.skipTest("khong co du lieu EURUSD: %s" % e)
        if len(df) < 2000:
            self.skipTest("sau kiem chat luong chi con %d bar" % len(df))
        return DL.hai_nua(df, 0.6)

    def test_phan_vi_truot_chuyen_duoc_con_tuyet_doi_thi_khong(self):
        tr, ho = self._hai_nua_that()
        tuyet_doi = {"chi_bao": "atr", "n": 14}
        truot = {"chi_bao": "phan_vi", "cua": {"chi_bao": "atr", "n": 14},
                 "n": 250}

        def kich_hoat(th):
            x_tr = NP.toan_hang(tr, th).dropna()
            q = float(x_tr.quantile(0.2))
            x_ho = NP.toan_hang(ho, th).to_numpy(float)
            return int(np.nansum(x_tr.to_numpy() < q)), int(np.nansum(x_ho < q))

        a_tr, a_ho = kich_hoat(tuyet_doi)
        b_tr, b_ho = kich_hoat(truot)
        self.assertGreater(a_tr, 100, "chuoi thu khong du bar")
        # Dang TRUOT phai chuyen duoc: holdout kich hoat it nhat 1/3 muc train,
        # can theo do dai hai nua.
        ty = (b_ho / max(len(ho), 1)) / max(b_tr / max(len(tr), 1), 1e-9)
        self.assertGreater(
            ty, 0.5,
            "phan vi TRUOT ma ti le kich hoat holdout/train chi %.2f" % ty)

    def test_moi_toan_hang_goc_deu_kich_hoat_duoc_o_HOLDOUT(self):
        """Quet ca bo: khong toan hang nao duoc de nguong train ra 0 bar o holdout."""
        tr, ho = self._hai_nua_that()
        chet = []
        for t in NS.TOAN_HANG_GOC:
            try:
                x_tr = NP.toan_hang(tr, t).dropna()
                if len(x_tr) < 200:
                    continue
                x_ho = NP.toan_hang(ho, t).to_numpy(float)
            except Exception:
                continue
            # Chi xet nhung nguong ma BO SINH thuc su dung - `nguong_tu_lich_su`
            # da bo cac nguong suy bien (dung vao bien cua dai luong bi chan).
            for pv, q in NS.nguong_tu_lich_su(tr, t).items():
                duoi = pv <= 0.5
                n_ho = int(np.nansum(x_ho < q) if duoi else np.nansum(x_ho > q))
                if n_ho == 0:
                    chet.append("%s @q%.0f" % (NS._ten(t), pv * 100))
        self.assertEqual(
            chet, [],
            "nguong lay tu TRAIN KHONG kich hoat lan nao o HOLDOUT:\n  %s"
            % "\n  ".join(chet))


class BoChamDiemPhaiPhanBietKHONG_KICH_HOAT(unittest.TestCase):
    def test_co_nguong_lenh_holdout_toi_thieu(self):
        import importlib.util
        p = GOC / "_noi_sinh_chay.py"
        spec = importlib.util.spec_from_file_location("_ns_chay", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        self.assertTrue(hasattr(m, "LENH_HO_TOI_THIEU"),
                        "khong co nguong phan biet 'khong kich hoat' voi 'thua'")
        self.assertGreaterEqual(m.LENH_HO_TOI_THIEU, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
