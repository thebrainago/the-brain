# -*- coding: utf-8 -*-
"""GHEP QUAN TRI LENH: mot luoi + NHIEU co che, nhu EA that (20/09/2026).

`CLAUDE.md` do duoc: *"ho 2 QUAN TRI VI THE ... do 05/09 no QUAN TRONG HON ho
1 voi lop luoi: entry co tinh SAI van cho 92-97%/nam"*. Day la module ra tien
nhat cua ca he.

Nhung `duc_quan_tri` chi de duoc cau hinh MOT KHUON: mot luoi + dung mot co
che phu. Mot EA luoi that ngoai doi chay **bon den sau** co che cung luc - cat
hoa, tia, chot lui, chan von, hedge - va chinh su KET HOP do moi la cai lam no
song qua mot cu sut. De tung cai mot roi ket luan "quan tri lenh khong an thua"
la ket luan ve mot thu khac.
"""
from __future__ import annotations

import unittest
from collections import Counter

from nhan import hephaestus as HP

DON = HP.duc_quan_tri(han_ngach=500)
GHEP = HP.ghep_lo_quan_tri(DON, han_ngach=400)


class GhepDoi(unittest.TestCase):
    def test_co_ghep_ra_va_khong_trung_ten(self):
        self.assertTrue(GHEP)
        ten = [c["ten"] for c in GHEP]
        self.assertEqual(len(ten), len(set(ten)))

    def test_moi_ban_ghep_THAT_SU_co_hai_co_che(self):
        """`nut` phai co nut RIENG cua ca hai ve, khong chi cua mot ve."""
        for c in GHEP:
            rieng = set(c["nut"]) - HP.NUT_NEN
            self.assertGreaterEqual(
                len(rieng), 2,
                "%s chi co %d nut ngoai nen - khong phai mot phep ghep"
                % (c["ten"], len(rieng)))

    def test_KHONG_ghep_voi_LUOI_TRAN(self):
        """`luoi_tran` chi co nut NEN, nen `tran + X` khong cho hai co che -
        no chi la `X` voi `buoc`/`tp` khac, tuc mot bien the tham so doi lot
        mot phep ghep.

        Do 20/09/2026 khi chua co chot nay: 400 cap dau TOAN LA `tran + X`
        (`tran` dung dau danh sach), va cac cap THAT bi han ngach cat het -
        ham ghep tieu sach ngan sach de sinh ra thu no khong dinh sinh.
        """
        for c in GHEP:
            self.assertNotIn("luoi_tran", c["khuon"], c["ten"])

    def test_cung_khuon_thi_KHONG_ghep(self):
        cf = DON[0]
        self.assertIsNone(HP.ghep_quan_tri(cf, dict(cf)))

    def test_DUNG_DO_nut_ngoai_nen_thi_KHONG_ghep(self):
        """Hai ve noi khac nhau ve CUNG mot thu; lay bua mot ben la bia ra mot
        cau hinh thu ba khong ai dinh viet."""
        a = {"ten": "a", "khuon": "x", "nut": {"buoc": 30.0, "tia_tu": 2.0},
             "co_che": "a"}
        b = {"ten": "b", "khuon": "y", "nut": {"buoc": 60.0, "tia_tu": 5.0},
             "co_che": "b"}
        self.assertIsNone(HP.ghep_quan_tri(a, b))

    def test_nut_NEN_dung_do_thi_lay_ve_THU_NHAT(self):
        a = {"ten": "a", "khuon": "x", "nut": {"buoc": 30.0, "tp": 60.0,
                                               "tia_tu": 2.0}, "co_che": "a"}
        b = {"ten": "b", "khuon": "y", "nut": {"buoc": 99.0, "tp": 11.0,
                                               "chot_lui_tu": 3.0}, "co_che": "b"}
        cf = HP.ghep_quan_tri(a, b)
        self.assertIsNotNone(cf)
        self.assertEqual(cf["nut"]["buoc"], 30.0)
        self.assertEqual(cf["nut"]["tp"], 60.0)
        self.assertEqual(cf["nut"]["tia_tu"], 2.0)
        self.assertEqual(cf["nut"]["chot_lui_tu"], 3.0)

    def test_moi_NUT_deu_la_tham_so_THAT_cua_bo_mo_phong(self):
        """Mot nut la se khong nem luc de - no nem luc CHAY, sau khi da tieu
        mot suat FDR de dang ky."""
        import importlib
        import inspect
        mp = importlib.import_module("mo_phong_v2")
        hop_le = set(inspect.signature(mp.mo_phong).parameters)
        for c in DON + GHEP:
            la = set(c["nut"]) - hop_le
            self.assertEqual(la, set(), "%s co nut la: %r" % (c["ten"], la))

    def test_XAC_DINH_chay_lai_cho_y_het(self):
        """Lo ghep phai tien dang ky duoc: xin 20 hom nay roi 100 ngay mai thi
        20 cai dau van la 20 cai cu."""
        a = HP.ghep_lo_quan_tri(DON, han_ngach=20)
        b = HP.ghep_lo_quan_tri(DON, han_ngach=100)
        self.assertEqual([x["ten"] for x in a], [x["ten"] for x in b[:20]])

    def test_co_che_neu_ten_CA_HAI_luan_diem(self):
        """Man hinh duyet phai thay day la mot he GHEP, khong phai mot luan cu
        don doi ten."""
        for c in GHEP[:40]:
            self.assertIn("VA:", c["co_che"], c["ten"])
            self.assertGreater(len(c["co_che"]), 80)

    def test_phu_duoc_NHIEU_cap_khuon_chu_khong_dinh_mot_cho(self):
        """Neu 400 cap deu tu 2-3 khuon thi ham ghep dang khong phu khong
        gian, chi dang rai tham so quanh mot goc."""
        cap = Counter(c["khuon"] for c in GHEP)
        self.assertGreaterEqual(len(cap), 8,
                                "chi %d cap khuon: %r" % (len(cap), cap))


if __name__ == "__main__":
    unittest.main()


class LenhCLIPhaiKHOP_VOI_DON(unittest.TestCase):
    """Don hang da day len viet `qt ... --ghep`. Neu CLI cai `--ghep` o mot
    lenh KHAC thi don se chay NHAM DUONG **ma khong bao gi** - dung kieu lang
    phi mot dem may chay het cong suat de lay ve mot con so tra loi cau khac.

    Bai nay doi chieu don THAT trong `viec/cho/` voi CLI THAT.
    """

    def test_moi_don_goi_b_py_deu_dung_lenh_CLI_co_that(self):
        import json
        from pathlib import Path
        lenh_co = set()
        txt = Path("b.py").read_text(encoding="utf-8")
        import re
        for m in re.finditer(r'"([a-z0-9\-_]+)":\s*c_[a-z_]+', txt):
            lenh_co.add(m.group(1))
        self.assertTrue(lenh_co, "khong doc duoc bang lenh cua b.py")
        for p in sorted(Path("viec/cho").glob("*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            l = d.get("lenh") or []
            if len(l) < 3 or not str(l[1]).endswith("b.py"):
                continue
            self.assertIn(l[2], lenh_co,
                          "don %s goi `b %s` - khong co lenh nay" % (d["ma"], l[2]))

    def test_don_qt_ghep_dung_co_ghep_va_CLI_hieu_co_do(self):
        import json
        from pathlib import Path
        p = Path("viec/cho/hepha-qt-ghep.json")
        if not p.exists():
            self.skipTest("chua co don hepha-qt-ghep")
        l = json.loads(p.read_text(encoding="utf-8"))["lenh"]
        self.assertIn("--ghep", l)
        self.assertIn("qt", l)
        txt = Path("b.py").read_text(encoding="utf-8")
        self.assertIn('if "--ghep" in a:', txt,
                      "CLI khong hieu co `--ghep` trong nhanh `qt`")
