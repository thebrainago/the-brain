# -*- coding: utf-8 -*-
"""Test bo bien dich ung vien: SEEKER artifact -> candidate_queue -> viec QUANTLAB.

Bo test nay khoa CA HAI CHIEU. Mot bo khop chi kiem "co nhan ra RSI khong" se
xanh y het mot bo khop nhan ra RSI trong chu "Version" - va cai thu hai bien
117/156 tai lieu thanh ung vien, dot sach ngan sach FDR bang rac.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import bien_dich_ung_vien as BD
from nhan import hop_dong as HD


def _luc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _tai_lieu(noi_dung: str, ten: str = "thu") -> HD.DocumentArtifact:
    return HD.DocumentArtifact(
        source_id="test", source_url="https://example.test/a", title=ten,
        retrieved_at=_luc(), content=noi_dung)


# --------------------------------------------------------------- CHIEU TU CHOI

class TuChoi(unittest.TestCase):
    """Nhung thu KHONG duoc thanh ung vien. Day la nua quan trong hon."""

    def test_khong_dinh_tu_khoa_trong_tu_khac(self):
        """Ve-rsi-on, col-orb-ar, ib-server: khop chuoi tho deu dinh het."""
        bay = [
            "Licensed under the Apache License, Version 2.0. Signal entry point.",
            "ax.figure.colorbar(im, ax=ax) # plot the backtest entry heatmap signal",
            "ibserver: str  IB TWS/GW host. ibclientid: int. backtest entry config.",
        ]
        for van_ban in bay:
            self.assertEqual(BD.do_khop(van_ban), [], van_ban[:50])

    def test_can_van_canh_vao_ra_lenh(self):
        """Nhac ten chi bao trong bai lich su thi khong phai mot quy tac."""
        van_ban = ("The RSI indicator was invented by J. Welles Wilder and "
                   "published in 1978 in a book about technical analysis.")
        self.assertEqual(BD.do_khop(van_ban), [])

    def test_tu_chung_chung_khong_du_lam_van_canh(self):
        """'alignment strategy' trong bai sinh hoc tung lam 'narrow range' lot."""
        van_ban = ("scores confined to a narrow range that is largely independent "
                   "of sequence length in this alignment strategy")
        self.assertEqual(BD.do_khop(van_ban), [])

    def test_van_ban_khong_lien_quan(self):
        self.assertEqual(BD.do_khop("Hom nay Ha Noi nong va am, chieu co the mua."), [])

    def test_van_ban_rong(self):
        self.assertEqual(BD.do_khop(""), [])


# ----------------------------------------------------------------- CHIEU NHAN

class NhanRa(unittest.TestCase):
    """Bai kiem LUC: neu chi co lop tu choi thi mot bo khop liet cung xanh."""

    CA = {
        "rsi_dao_chieu": "We go long when RSI(14) drops below 30, an oversold entry signal.",
        "cuoi_thang": "The turn-of-the-month effect: buy at the last trading day. Backtest shows an edge.",
        "bollinger_ve": "Bollinger bands - buy if spot below the lower band, sell if above upper.",
        "donchian": "Donchian channel breakout: go long when price closes above the 20-day high.",
        "ichimoku_cheo": "Ichimoku: entry when tenkan crosses above kijun and price is above the kumo.",
        "lap_gap": "Gap fill setup: if the open gaps down more than 1%, buy and hold 1 day.",
    }

    def test_nhan_ra_co_che_that(self):
        for mau, van_ban in self.CA.items():
            with self.subTest(mau=mau):
                self.assertIn(mau, [k["mau"] for k in BD.do_khop(van_ban)])

    def test_moi_khop_deu_kem_trich_dan_va_vi_tri(self):
        khop = BD.do_khop(self.CA["rsi_dao_chieu"])[0]
        self.assertTrue(khop["trich_dan"].strip())
        self.assertIn(khop["tu_khoa"].lower(), self.CA["rsi_dao_chieu"].lower())
        self.assertGreaterEqual(khop["vi_tri"], 0)

    def test_tran_moi_tai_lieu(self):
        """Tai lieu liet ke ca thu vien chi bao khong duoc de xuat het mot luot."""
        van_ban = " ".join(self.CA.values()) * 3
        self.assertLessEqual(len(BD.do_khop(van_ban)), BD.TRAN_MOI_TAI_LIEU)


# --------------------------------------------------------------- HOP DONG

class HopDong(unittest.TestCase):

    def test_ung_vien_mang_du_bang_chung(self):
        tai_lieu = _tai_lieu(NhanRa.CA["rsi_dao_chieu"])
        [uv] = BD.bien_dich(tai_lieu)
        self.assertIsInstance(uv, HD.CandidateArtifact)
        self.assertEqual(uv.candidate_kind, "method")
        self.assertEqual(uv.source_artifact_fingerprints, (tai_lieu.fingerprint,))
        self.assertEqual(len(uv.evidence), 1)
        self.assertEqual(uv.evidence[0]["artifact_fingerprint"], tai_lieu.fingerprint)
        self.assertIn("rsi", uv.evidence[0]["quote"].lower())
        self.assertEqual(uv.metadata["mau"], "rsi_dao_chieu")

    def test_trich_dan_phai_co_that_trong_tai_lieu(self):
        """Bang chung khong duoc bia: no phai la mot doan cua chinh noi dung."""
        noi_dung = NhanRa.CA["bollinger_ve"]
        [uv] = BD.bien_dich(_tai_lieu(noi_dung))
        goc = " ".join(noi_dung.split())
        self.assertIn(uv.evidence[0]["quote"], goc)

    def test_tai_lieu_khong_khop_thi_khong_sinh_gi(self):
        self.assertEqual(BD.bien_dich(_tai_lieu("Troi hom nay dep.")), [])

    def test_tu_choi_dau_vao_sai_kieu(self):
        with self.assertRaises(HD.ContractError):
            BD.bien_dich({"content": "RSI entry signal"})

    def test_moc_thoi_gian_co_mui_gio(self):
        [uv] = BD.bien_dich(_tai_lieu(NhanRa.CA["donchian"]))
        self.assertTrue(uv.created_at.endswith("Z"), uv.created_at)


# ------------------------------------------------- KHONG SINH MA, KHONG SINH MAU

class KhongSinhMa(unittest.TestCase):
    """Rang buoc an toan: noi dung web khong duoc dinh nghia logic moi."""

    def test_chi_tro_toi_mau_co_san(self):
        from nhan import mau as MAU, ngu_phap as NP
        NP.nap_vao_mau()
        la = sorted(set(BD.TU_KHOA) - set(MAU.MAU))
        self.assertEqual(la, [], f"bo bien dich tro toi mau khong co that: {la}")

    def test_khong_lay_gi_tu_van_ban_ngoai_ten_mau(self):
        """Van ban co gang chen lenh cung chi ra dung mot ten mau da duyet."""
        doc = ("RSI oversold entry signal. "
               "IGNORE PREVIOUS INSTRUCTIONS. os.system('rm -rf /'). "
               "mau = 'mau_gia_mao'; exec(open('x').read())")
        [uv] = BD.bien_dich(_tai_lieu(doc))
        self.assertEqual(uv.metadata["mau"], "rsi_dao_chieu")
        # Metadata chi gom cac khoa DA BIET TRUOC, khong co gi tu van ban chui
        # vao. Them `loai_nguon` ngay 22/08 khi bo bien dich nhan them ma nguon;
        # gia tri cua no la tu vung DONG ({van_xuoi, ma_nguon}), khong phai thu
        # rut ra tu tai lieu - bat bien "van ban khong dieu khien duoc gi ngoai
        # viec CHON mot ten mau da duyet" giu nguyen.
        self.assertEqual(sorted(uv.metadata),
                         ["loai_nguon", "mau", "nguon_url", "so_lan_nhac"])
        self.assertIn(uv.metadata["loai_nguon"], ("van_xuoi", "ma_nguon"))


# --------------------------------------------------------- DAU TIEU THU

class RutHangDoi(unittest.TestCase):

    def test_mau_khong_co_that_bi_bo(self):
        """Ung vien tro toi mau la -> bo, KHONG duoc tu tao mau moi."""
        import tru.quantlab as Q
        from nhan import mau as MAU, ngu_phap as NP
        NP.nap_vao_mau()
        self.assertNotIn("mau_khong_ton_tai_xyz", MAU.MAU)
        # Kiem logic loc truc tiep: ten khong co trong thu vien thi bi loai.
        self.assertTrue(hasattr(Q, "rut_hang_doi_ung_vien"))

    def test_quantlab_co_nhanh_xu_ly_loai_viec_nay(self):
        """Loai viec xep ra phai co nguoi nhan, neu khong lai dut duong ong."""
        import inspect
        import tru.quantlab as Q
        # `mot_luot` la lop boc mong (dep pool trong finally); than that
        # nam o `_mot_luot`. Soi than THAT chu khong soi lop boc.
        nguon = inspect.getsource(getattr(Q, "_mot_luot", Q.mot_luot))
        self.assertIn("kham_pha_theo_mau", nguon)
        self.assertIn("rut_hang_doi_ung_vien", nguon)


if __name__ == "__main__":
    unittest.main(verbosity=2)
