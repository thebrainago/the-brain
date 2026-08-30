# -*- coding: utf-8 -*-
"""Regression tests for the shared active-result reader contract."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import ket_qua_hoat_dong as KQHD
from nhan import so as SO


class ActiveResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="brain_active_result_test_")
        self.original_db = SO.DB
        SO.DB = Path(self.temp_dir.name) / "nao.db"
        SO.khoi_tao()

    def tearDown(self) -> None:
        SO.DB = self.original_db
        self.temp_dir.cleanup()

    def _gia_thuyet(self, ma: str, trang_thai: str) -> None:
        SO.chay("INSERT INTO gia_thuyet(ma,trang_thai) VALUES(?,?)", ma, trang_thai)

    def _ket_qua(self, ma: str, verdict: str, superseded_by: int | None = None) -> int:
        with SO.ket_noi() as cn:
            cur = cn.execute(
                "INSERT INTO ket_qua(gt_ma,luc,verdict,superseded_by) VALUES(?,?,?,?)",
                (ma, "2026-08-16 23:00:00", verdict, superseded_by),
            )
            return int(cur.lastrowid)

    def test_only_latest_non_invalidated_active_hypotheses_are_visible(self) -> None:
        self._gia_thuyet("ACTIVE", "FAIL")
        self._gia_thuyet("QUARANTINED", "QUARANTINED_V2")
        self._gia_thuyet("INACTIVE", "inactive")
        self._gia_thuyet("SUPERSEDED", "SUPERSEDED")
        self._gia_thuyet("INVALID", "FAIL")
        self._gia_thuyet("REPLACED", "FAIL")

        self._ket_qua("ACTIVE", "PASS")
        self._ket_qua("QUARANTINED", "PASS")
        self._ket_qua("INACTIVE", "PASS")
        self._ket_qua("SUPERSEDED", "PASS")
        self._ket_qua("INVALID", "INVALIDATED")
        old = self._ket_qua("REPLACED", "PASS")
        self._ket_qua("REPLACED", "FAIL")
        SO.chay("UPDATE ket_qua SET superseded_by=(SELECT MAX(id) FROM ket_qua) WHERE id=?", old)

        sql = KQHD.truy_van(
            "k.gt_ma, k.verdict",
            dieu_kien_them="k.verdict IN ('PASS', 'UNG_VIEN')",
            sap_xep="k.id",
        )
        self.assertEqual(SO.nhieu(sql), [{"gt_ma": "ACTIVE", "verdict": "PASS"}])

    def test_limit_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            KQHD.truy_van("k.id", gioi_han=0)

    def test_extra_join_is_inserted_before_active_result_filter(self) -> None:
        self._gia_thuyet("ACTIVE", "FAIL")
        self._gia_thuyet("QUARANTINED", "QUARANTINED_V2")
        self._ket_qua("ACTIVE", "FAIL")
        self._ket_qua("QUARANTINED", "FAIL")
        SO.chay("INSERT INTO fdr(luc,gt_ma,bac_bo) VALUES(?,?,?)", "2026-08-16", "ACTIVE", 1)
        SO.chay("INSERT INTO fdr(luc,gt_ma,bac_bo) VALUES(?,?,?)", "2026-08-16", "QUARANTINED", 1)

        sql = (
            "SELECT COUNT(DISTINCT f.gt_ma) n "
            + KQHD.tu_ket_qua_hoat_dong(join_them="JOIN fdr f ON f.gt_ma=k.gt_ma")
            + " AND f.bac_bo=1"
        )
        self.assertEqual(SO.mot(sql)["n"], 1)


if __name__ == "__main__":
    unittest.main()
