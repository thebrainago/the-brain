# -*- coding: utf-8 -*-
"""Tests for SEEKER V2 artifact output and disabled legacy execution paths."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import hop_dong as HD
from nhan import so as SO
from tru import seeker


class SeekerArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="seeker_artifact_test_")
        self.original_db = SO.DB
        SO.DB = Path(self.temp_dir.name) / "nao.db"
        SO.khoi_tao()

    def tearDown(self) -> None:
        SO.DB = self.original_db
        self.temp_dir.cleanup()

    def _tai_lieu(self, index: int, title: str = "Research document") -> int:
        url = f"https://example.test/research-{index}"
        with SO.ket_noi() as connection:
            cursor = connection.execute(
                "INSERT INTO tai_lieu(van_tay,nguon,loai,tieu_de,url,tom_tat,"
                "tu_khoa,diem,luc) VALUES(?,?,?,?,?,?,?,?,?)",
                (SO.van_tay(url), "mock_source", "paper", title, url, "", "B", 2.0,
                 "2026-08-16 16:00:00"),
            )
            return int(cursor.lastrowid)

    def _noi_dung(self, index: int, *, readable: bool = True) -> None:
        tai_lieu_id = self._tai_lieu(index, f"Document {index}")
        url = f"https://example.test/research-{index}"
        content = f"Observed evidence number {index}." if readable else ""
        with SO.ket_noi() as connection:
            connection.execute(
                "INSERT INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,so_ky_tu,"
                "so_ky_tu_goc,van_ban,luc,da_boc,ket_boc) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (tai_lieu_id, SO.van_tay("nd", url), url,
                 "bai_bao" if readable else "khong_doc_duoc",
                 "mock", len(content), len(content), content, "2026-08-16 16:05:00",
                 int(not readable), ""),
            )

    def test_doc_success_writes_document_artifact_idempotently(self) -> None:
        self._tai_lieu(1)
        fetched = {
            "kieu": "bai_bao",
            "cach": "mock-reader",
            "so_ky_tu": 43,
            "so_ky_tu_goc": 52,
            "van_ban": "Observed spread predicts execution cost.",
        }
        with patch.object(seeker.TV, "doc", return_value=fetched):
            result = seeker.doc_toan_van(gioi_han=1, ngan_sach_giay=10)

        self.assertEqual(result["doc_duoc"], 1)
        self.assertEqual(result["artifact_moi"], 1)
        row = SO.mot("SELECT payload FROM artifact WHERE artifact_type='document'")
        artifact = HD.artifact_from_json(row["payload"])
        self.assertIsInstance(artifact, HD.DocumentArtifact)
        self.assertEqual(artifact.source_id, "mock_source")
        self.assertEqual(artifact.content, fetched["van_ban"])
        self.assertEqual(artifact.metadata["acquisition_method"], "mock-reader")

        content_row = SO.mot("SELECT van_tay FROM noi_dung LIMIT 1")
        first_id, first_created = seeker._noi_dung_artifact(content_row["van_tay"])
        second_id, second_created = seeker._noi_dung_artifact(content_row["van_tay"])
        self.assertFalse(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first_id, second_id)
        self.assertEqual(SO.mot("SELECT COUNT(*) n FROM artifact")["n"], 1)

    def test_backfill_advances_cursor_and_skips_unreadable_rows(self) -> None:
        self._noi_dung(1, readable=True)
        self._noi_dung(2, readable=False)
        self._noi_dung(3, readable=True)

        first = seeker.backfill_document_artifacts(gioi_han=2)
        self.assertEqual(first["da_xem"], 2)
        self.assertEqual(first["artifact_moi"], 1)
        self.assertEqual(first["bo_qua"], 1)
        self.assertEqual(first["con_lai"], 1)

        second = seeker.backfill_document_artifacts(gioi_han=2)
        self.assertEqual(second["da_xem"], 1)
        self.assertEqual(second["artifact_moi"], 1)
        self.assertEqual(second["con_lai"], 0)
        self.assertEqual(
            SO.mot("SELECT COUNT(*) n FROM artifact WHERE artifact_type='document'")["n"], 2
        )

        third = seeker.backfill_document_artifacts(gioi_han=2)
        self.assertEqual(third["da_xem"], 0)
        self.assertEqual(third["artifact_moi"], 0)

    def test_mot_luot_never_calls_legacy_llm_or_backtest_bridge(self) -> None:
        empty_doc = {
            "doc_duoc": 0, "that_bai": 0, "ky_tu_luot_nay": 0,
            "artifact_moi": 0, "artifact_da_co": 0, "artifact_loi": 0,
            "thu_vien_ban_doc": 0, "thu_vien_ky_tu": 0, "thu_vien_trang_a4": 0,
        }
        empty_backfill = {
            "da_xem": 0, "artifact_moi": 0, "artifact_da_co": 0, "bo_qua": 0,
            "loi": None, "cursor": 0, "con_lai": 0,
        }
        with (
            patch.object(seeker, "dang_ky_nguon"),
            patch.object(seeker, "nguon_den_han", return_value=[]),
            patch.object(seeker, "quet_trinh_duyet", return_value={}),
            patch.object(seeker, "doc_toan_van", return_value=empty_doc),
            patch.object(seeker, "backfill_document_artifacts", return_value=empty_backfill),
            patch.object(seeker, "viet_bao_cao"),
            patch.object(seeker, "boc_co_che", side_effect=AssertionError("legacy BOC called")) as boc,
            patch.object(
                seeker, "noi_sang_quantlab", side_effect=AssertionError("legacy bridge called")
            ) as bridge,
            patch.object(seeker.TT, "hoi_json", side_effect=AssertionError("LLM called")) as llm,
            patch.object(SO, "them_viec", side_effect=AssertionError("backtest queued")) as queue,
        ):
            result = seeker.mot_luot(ngan_sach_giay=60)

        boc.assert_not_called()
        bridge.assert_not_called()
        llm.assert_not_called()
        queue.assert_not_called()
        self.assertTrue(result["BOC"]["legacy_disabled"])
        self.assertEqual(result["cau_noi_quantlab"]["che_do"], "artifact_contract")
        # SEEKER xep UNG VIEN (co dan nguon), tuyet doi khong xep VIEC backtest:
        # `queue.assert_not_called()` o tren la cho chan that, con so 0 nay la
        # cho bao cao. Sua kien truc sai se lam vo mot trong hai.
        self.assertEqual(result["cau_noi_quantlab"]["xep_viec"], 0)
        self.assertIn("xep_moi", result["cau_noi_quantlab"])


if __name__ == "__main__":
    unittest.main()
