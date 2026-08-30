# -*- coding: utf-8 -*-
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from nhan import so as SO


class TestSoSongSong(unittest.TestCase):
    def setUp(self):
        self._db_cu = SO.DB
        self._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()

    def test_nhieu_writer_khong_phan_nhanh_hash(self):
        def ghi(i):
            SO.ghi_su_kien("TEST", "song_song", {"i": i})

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(ghi, range(160)))

        lanh, mo_ta = SO.kiem_chuoi_hash()
        self.assertTrue(lanh, mo_ta)
        self.assertEqual(SO.mot("SELECT COUNT(*) n FROM su_kien")["n"], 160)

    def test_cung_ma_khong_duoc_doi_plan(self):
        kw = dict(ma="GT.TEST", co_che="co che", template="rsi_dao_chieu",
                  tai_san="EURCAD", khung="H1", cua_so="2020..2025",
                  ho="test")
        SO.dang_ky_gia_thuyet(tham_so={"n": 14}, **kw)
        with self.assertRaises(ValueError):
            SO.dang_ky_gia_thuyet(tham_so={"n": 15}, **kw)


if __name__ == "__main__":
    unittest.main()
