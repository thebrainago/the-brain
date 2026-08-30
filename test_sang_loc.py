# -*- coding: utf-8 -*-
"""PHEU BON VONG. Bo test nay thay ban dau (DS, 23/08).

Ban dau co 13 bai va ca 13 deu XANH trong khi pheu HONG HOAN TOAN: moi vong
goi `MP.mua_giu()` roi do chinh MUA-GIU, khong he sinh tin hieu cua co che dang
xet. Ly do bo test khong bat duoc la no chi cham vao ONG NUOC - bo dem, hang so,
"khong crash" - ma khong bai nao chay MOT CO CHE THAT qua pheu roi doi chieu.

Nen luat cua bo test nay: **moi bai kiem phai chay mot co che that tren du lieu
that va doi chieu voi mot ky vong biet truoc.** Va theo `02_KHAC_SAU_LUAT` muc
L3, moi cong phai co ca hai chieu: thu dang bi chan phai bi chan, thu dang qua
phai qua.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import mau as MAU
from nhan import sang_loc as SL


def _chuoi(n=2000, hat=7, xu_huong=0.0):
    """Chuoi gia tong hop, du dai de qua nguong so bar."""
    rng = np.random.default_rng(hat)
    r = rng.normal(xu_huong, 0.01, n)
    gia = 100 * np.exp(np.cumsum(r))
    idx = pd.date_range("2010-01-01", periods=n, freq="D")
    # Dong cua phai nam o VI TRI NGAU NHIEN trong bien do bar. Neu dat close
    # vao giua (high = gia + bd, low = gia - bd) thi IBS = 0,5 o moi bar va moi
    # co che dua tren vi tri dong cua se "khong bao gio kich hoat" - bo test se
    # to cao nham chinh no thay vi to cao pheu.
    bd = np.abs(rng.normal(0, 0.004, n)) * gia + 1e-9
    vt = rng.uniform(0.02, 0.98, n)          # IBS muc tieu tung bar
    low = gia - bd * vt
    high = low + bd
    return pd.DataFrame({
        "open": low + bd * rng.uniform(0, 1, n),
        "high": high, "low": low, "close": gia,
        "tick_volume": rng.integers(100, 1000, n),
        "spread": np.full(n, 2.0),
    }, index=idx)


class _Nen(unittest.TestCase):
    def setUp(self):
        SL.xoa_bo_dem()


class V0VanTay(_Nen):
    def test_van_tay_doi_khi_tham_so_doi(self):
        a = SL.van_tay_phep_thu("ibs_bat_day", {"nguong": 0.2}, "X", "D1")
        b = SL.van_tay_phep_thu("ibs_bat_day", {"nguong": 0.3}, "X", "D1")
        self.assertNotEqual(a, b)

    def test_van_tay_on_dinh(self):
        a = SL.van_tay_phep_thu("ibs_bat_day", {"nguong": 0.2}, "X", "D1")
        b = SL.van_tay_phep_thu("ibs_bat_day", {"nguong": 0.2}, "X", "D1")
        self.assertEqual(a, b)

    def test_trung_phep_thu_bi_loai(self):
        vt = SL.van_tay_phep_thu("ibs_bat_day", {}, "X", "D1")
        kl, ly_do, _ = SL.v0_van_tay("ibs_bat_day", {}, "X", "D1", da_chay={vt})
        self.assertEqual(kl, SL.LOAI)
        self.assertEqual(ly_do, "trung_phep_thu")

    def test_phep_thu_moi_KHONG_bi_loai(self):
        """Chieu nghich cua bai tren, va la bai da bat duoc loi that: ban dau
        V0 hoi `candidate_queue` xem van tay co trong do khong - ma moi ung vien
        deu duoc RUT RA TU chinh hang doi do, nen V0 loai sach 100% dau vao."""
        kl, _, _ = SL.v0_van_tay("ibs_bat_day", {"nguong": 0.123456}, "KHONG_CO_MA",
                                 "D1", da_chay=set())
        self.assertEqual(kl, SL.NHAN)


class V1SangRe(_Nen):
    def test_thieu_bar_la_CHUA_DU_LUC_chu_khong_phai_LOAI(self):
        """Thieu du lieu khong phai la bang chung chong lai co che."""
        kl, _, _ = SL.v1_sang_re("t", "ibs_bat_day", {}, "X", "D1", _chuoi(300))
        self.assertEqual(kl, SL.CHUA_DU_LUC)

    def test_co_che_that_qua_duoc_V1(self):
        kl, ly_do, do = SL.v1_sang_re("t", "ibs_bat_day", {"nguong": 0.2},
                                      "X", "D1", _chuoi())
        self.assertEqual(kl, SL.NHAN, ly_do)
        self.assertGreater(do["kich_hoat"], 0.02)
        self.assertLess(do["kich_hoat"], 0.9)

    def test_mua_giu_tra_hinh_bi_chan(self):
        """Kich hoat ~100% nghia la luon o trong thi truong - do la mua-giu doi
        ten, va no se 'thang' moi phep do neu khong chan o day."""
        MAU.MAU["_luon_mua_thu"] = {
            "ham": lambda df, **_: np.ones(len(df)), "ho": "khac",
            "co_che": "chi de kiem thu", "luoi": [{}]}
        try:
            kl, ly_do, do = SL.v1_sang_re("t", "_luon_mua_thu", {}, "X", "D1", _chuoi())
            self.assertEqual(kl, SL.LOAI)
            self.assertEqual(ly_do, "mua_giu_tra_hinh")
            self.assertGreater(do["kich_hoat"], 0.98)
        finally:
            MAU.MAU.pop("_luon_mua_thu", None)

    def test_khong_bao_gio_vao_lenh_bi_chan(self):
        MAU.MAU["_khong_bao_gio_thu"] = {
            "ham": lambda df, **_: np.zeros(len(df)), "ho": "khac",
            "co_che": "chi de kiem thu", "luoi": [{}]}
        try:
            kl, ly_do, _ = SL.v1_sang_re("t", "_khong_bao_gio_thu", {}, "X", "D1",
                                         _chuoi())
            self.assertEqual(kl, SL.LOAI)
            self.assertEqual(ly_do, "kich_hoat_qua_thap")
        finally:
            MAU.MAU.pop("_khong_bao_gio_thu", None)


class V2SangKinhTe(_Nen):
    """V2 phai do CO CHE, khong phai do mua-giu. Day la loi goc cua ban dau."""

    def _cp(self):
        from nhan import chi_phi as CP
        return CP.MoHinhChiPhi(ma="X", spread_frac_chung=0.5e-4,
                               truot_gia_frac=0.2e-4, phi_nam_mua=0.02,
                               phi_nam_ban=0.02, do_tin="SAN")

    def test_hai_co_che_khac_nhau_cho_hai_ket_qua_khac_nhau(self):
        """Bai kiem QUAN TRONG NHAT cua file nay.

        Neu pheu do mua-giu thay vi do co che thi MOI co che tren cung mot chuoi
        se cho y het mot bo so. Bai nay so hai co che khac han nhau tren CUNG
        mot chuoi: neu so lieu trung nhau thi pheu dang do nham thu."""
        df = _chuoi()
        cp = self._cp()
        _, _, a = SL.v2_sang_kinh_te("t", "ibs_bat_day", {"nguong": 0.2},
                                     "X", "D1", df, cp)
        SL.xoa_bo_dem()
        _, _, b = SL.v2_sang_kinh_te("t", "sma_cheo", {"nhanh": 10, "cham": 50},
                                     "X", "D1", df, cp)
        self.assertTrue(a and b, "ca hai phai do duoc")
        self.assertNotEqual(a.get("so_lenh"), b.get("so_lenh"))
        self.assertNotEqual(a.get("sharpe"), b.get("sharpe"))

    def test_sharpe_mua_giu_giong_nhau_giua_hai_co_che(self):
        """Chieu nguoc lai: moc so sanh (mua-giu) thi PHAI giong nhau, vi no la
        thuoc tinh cua chuoi chu khong cua co che. Hai bai nay chi co nghia khi
        di cung nhau."""
        df = _chuoi()
        cp = self._cp()
        _, _, a = SL.v2_sang_kinh_te("t", "ibs_bat_day", {"nguong": 0.2},
                                     "X", "D1", df, cp)
        SL.xoa_bo_dem()
        _, _, b = SL.v2_sang_kinh_te("t", "sma_cheo", {"nhanh": 10, "cham": 50},
                                     "X", "D1", df, cp)
        self.assertAlmostEqual(a["sharpe_mua_giu"], b["sharpe_mua_giu"], places=6)

    def test_thieu_lenh_la_CHUA_DU_LUC(self):
        df = _chuoi(1600)
        MAU.MAU["_it_lenh_thu"] = {
            "ham": lambda d, **_: np.where(np.arange(len(d)) % 400 == 0, 1.0, 0.0),
            "ho": "khac", "co_che": "chi de kiem thu", "luoi": [{}]}
        try:
            kl, ly_do, _ = SL.v2_sang_kinh_te("t", "_it_lenh_thu", {}, "X", "D1",
                                              df, self._cp())
            self.assertEqual(kl, SL.CHUA_DU_LUC)
            self.assertEqual(ly_do, "thieu_lenh_de_ket_luan")
        finally:
            MAU.MAU.pop("_it_lenh_thu", None)

    def test_tan_suat_theo_HO_chu_khong_theo_nguong_chung(self):
        """Nguong chung 1 lenh/thang loai oan ca ho `lich`: turn-of-month vao
        12 lan/nam la DUNG ban chat co che. Do that tren US500CASH D1:
        cuoi_thang cho 0,81 lenh/thang."""
        v2 = SL.TC["v2"]
        theo_ho = v2.get("lenh_moi_thang_min_theo_ho") or {}
        self.assertLess(theo_ho.get("lich", 9), v2["lenh_moi_thang_min"])


class V3PhanChung(_Nen):
    def test_pham_vi_am_tinh_thi_LOAI(self):
        kl, ly_do, _ = SL.v3_phan_chung(
            "t", "ibs_bat_day", {}, "X", "D1", _chuoi(), None,
            pham_vi={"ket_luan": "KHONG_PHAN_BIET", "ly_do": "thu"})
        self.assertEqual(kl, SL.LOAI)
        self.assertIn("pham_vi", ly_do)

    def test_pham_vi_thieu_mau_thi_CHUA_DU_LUC(self):
        """Khac biet then chot: khong do duoc KHONG PHAI la bang chung am."""
        kl, ly_do, _ = SL.v3_phan_chung(
            "t", "ibs_bat_day", {}, "X", "D1", _chuoi(), None,
            pham_vi={"ket_luan": "CHUA_DU_MAU", "ly_do": "thu"})
        self.assertEqual(kl, SL.CHUA_DU_LUC)


class ChayPheuThat(_Nen):
    """Chay ca pheu tren DU LIEU THAT - duong ma ban dau chua bao gio chay."""

    def setUp(self):
        super().setUp()
        from nhan import du_lieu as DL
        self.df = None
        for ma in ("US500CASH", "EURCAD", "AUDNZD"):
            try:
                d = DL.nap(ma, "D1")
            except Exception:
                continue
            if d is not None and len(d) > 1600:
                self.df, self.ma = d, ma
                break
        if self.df is None:
            self.skipTest("khong co chuoi gia that de kiem")

    def test_pheu_chay_het_va_tra_ba_gia_tri(self):
        r = SL.chay_pheu("ibs_bat_day", {"nguong": 0.2}, self.ma, "D1", df=self.df)
        self.assertIn(r["ket_luan"], (SL.NHAN, SL.LOAI, SL.CHUA_DU_LUC, SL.SAN_SANG_V4))
        self.assertIn(r["vong"], ("V0", "V1", "V2", "V3"))
        self.assertEqual(r["phien_ban"], SL.PHIEN_BAN)

    def test_moi_lan_LOAI_deu_ghi_lai_du_bon_truong(self):
        """Khong ghi lai thi sau nay khong tra loi duoc 'noi tieu chi X thi bao
        nhieu thu song lai' - phai chay lai tat ca."""
        MAU.MAU["_luon_mua_thu2"] = {
            "ham": lambda df, **_: np.ones(len(df)), "ho": "khac",
            "co_che": "chi de kiem thu", "luoi": [{}]}
        try:
            SL.chay_pheu("_luon_mua_thu2", {}, self.ma, "D1", df=self.df)
        finally:
            MAU.MAU.pop("_luon_mua_thu2", None)
        bo = SL.lay_bo_dem()
        self.assertTrue(bo)
        for d in bo:
            for truong in ("vong", "tieu_chi", "gia_tri", "nguong", "phien_ban"):
                self.assertIn(truong, d)

    def test_pheu_dung_truoc_V4(self):
        """V0-V3 khong tieu ngan sach thong ke; viec cham holdout la cua
        `nhan/cong.py`. Pheu khong duoc tu phan quyet PASS."""
        r = SL.chay_pheu("ibs_bat_day", {"nguong": 0.2}, self.ma, "D1", df=self.df)
        self.assertNotEqual(r["ket_luan"], "PASS")


class LeoThangGop(unittest.TestCase):
    """Thieu luc tren MOT tai san khong phai cau tra loi cuoi, NEU phep thu
    phan chung noi co che song o ca lop."""

    def setUp(self):
        SL.xoa_bo_dem()

    def test_co_co_che_thi_de_nghi_GOP(self):
        kl, ly_do, _ = SL.v3_phan_chung(
            "t", "ibs_bat_day", {}, "KHONG_CO_MA", "D1", _chuoi(), None,
            pham_vi={"ket_luan": "CO_CO_CHE", "ly_do": "thu"}, sharpe=0.05)
        self.assertEqual(kl, SL.NEN_GOP)
        self.assertTrue(any(x["ly_do"] == "thieu_luc_don_le_nen_gop"
                            for x in SL.lay_cho_them()))

    def test_KHONG_co_co_che_thi_dung_lai(self):
        """Chieu nghich, va la chieu quan trong: gop khong phai thuoc bo vo dieu
        kien. Do that 23/08 tren 200 cua so - voi FX, gop lam TE DI o vung giua
        (delta 2 bps: don 74% so voi gop 62,5%), vi gop them nhung chan ma co
        che khong song chi them nhieu."""
        kl, _, _ = SL.v3_phan_chung(
            "t", "ibs_bat_day", {}, "KHONG_CO_MA", "D1", _chuoi(), None,
            pham_vi=None, sharpe=0.05)
        self.assertNotEqual(kl, SL.NEN_GOP)

    def test_NEN_GOP_khong_phai_mot_phan_quyet_duong(self):
        """`NEN_GOP` la 'con mot duong nua de thu', khong phai 'da qua'."""
        self.assertNotIn(SL.NEN_GOP, (SL.NHAN, SL.SAN_SANG_V4))
        self.assertEqual(len({SL.NHAN, SL.LOAI, SL.CHUA_DU_LUC,
                              SL.SAN_SANG_V4, SL.NEN_GOP}), 5)


class CauHinh(_Nen):
    def test_nguong_nam_trong_mot_file(self):
        for vong in ("v1", "v2", "v3"):
            self.assertIn(vong, SL.TC)
        self.assertTrue(SL.PHIEN_BAN)

    def test_cac_hang_so_phan_biet(self):
        self.assertEqual(len({SL.NHAN, SL.LOAI, SL.CHUA_DU_LUC,
                              SL.SAN_SANG_V4, SL.NEN_GOP}), 5)


class KhongChayLaiXacNhan(unittest.TestCase):
    """Xac nhan la HAM Y NGUYEN. Chay lai = nhin lai cung mot holdout, va moi
    lan chay deu tieu MOT suat FDR ke ca khi truot o cong re.

    Da xay ra that 23/08: 4 viec `xac_nhan_gop` nam CHO tu 22/08 trong khi ca 4
    gia thuyet DA CO ket qua FAIL cung ngay - ham duoc goi thang khong qua vong
    lam viec nen `xong_viec` khong bao gio duoc goi. Bat vong lap len la dot 4
    suat FDR cho nhung gia thuyet da biet truot.
    """

    def test_vong_lam_viec_co_chan_chay_lai(self):
        from pathlib import Path
        s = (Path(__file__).resolve().parent / "tru" / "quantlab.py").read_text(
            encoding="utf-8")
        self.assertIn('v["loai"] in ("xac_nhan", "xac_nhan_gop")', s,
                      "khong con chan chay lai xac nhan")
        self.assertIn("superseded_by IS NULL", s)

    def test_khong_con_viec_xac_nhan_treo_ma_da_co_ket_qua(self):
        """Bat truc tiep tren SO CAI, khong doc lai ma."""
        import json as _json
        from nhan import so as _SO
        treo = []
        for v in _SO.nhieu("SELECT id, tham_so FROM viec WHERE loai LIKE 'xac_nhan%' "
                           "AND trang_thai='CHO'"):
            gt = (_json.loads(v["tham_so"]) or {}).get("gt_ma", "")
            if gt and _SO.mot("SELECT id FROM ket_qua WHERE gt_ma=? "
                              "AND superseded_by IS NULL", gt):
                treo.append(gt)
        self.assertEqual(treo, [], f"viec xac_nhan treo ma da co ket qua: {treo}")


class MoiLoaiViecDeuCoNhanhXuLy(unittest.TestCase):
    """Xep mot loai viec ma vong lam viec khong co case cho no thi viec do roi
    vao `else` va bi danh dau 'loai viec chua ho tro' - IM LANG.

    Da xay ra that 16/08 voi `kham_pha_theo_mau` (ca duong ong tu tai lieu sang
    kiem dinh dut o dung day), va suyt xay ra lan hai 23/08 voi `kham_pha_gop`.
    Bai kiem nay lam cho lan thu ba khong the xay ra.
    """

    def test_khong_loai_viec_nao_bi_bo_roi(self):
        import re
        from pathlib import Path
        s = (Path(__file__).resolve().parent / "tru" / "quantlab.py").read_text(
            encoding="utf-8")
        xep = set(re.findall(r"them_viec\(TRU,\s*[\"'](\w+)", s))
        xu_ly = set(re.findall(r'v\["loai"\] == "(\w+)"', s))
        self.assertEqual(xep - xu_ly, set(),
                         f"xep viec nhung khong co nhanh xu ly: {sorted(xep - xu_ly)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
