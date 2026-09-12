# -*- coding: utf-8 -*-
"""Kiem EVO bao xa - duong sinh ra tu quyet dinh VPS 24/7 cua chu du an.

He se chay nhieu thang khong co nguoi ngoi canh. Mot bo giam sat chi ghi vao
`reports/` thi trong khoang thoi gian do bang khong co. Nhung mot bo giam sat
gui CUNG MOT DONG moi gio trong ba thang la 2.160 tin nhan giong het nhau - va
den tin thu ba nguoi ta tat thong bao, tuc no tu lam minh vo hinh.

Nen luat o day la: **chi gui khi TAP VAN DE DOI**, va khi van de HET cung phai
bao (khong thi khong ai biet la da yen).
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import evo as EVO  # noqa: E402


def _ket(xau_ten):
    cs = [EVO._chi_so(t, "mo ta " + t, 1, EVO.XAU, "bang chung " + t)
          for t in xau_ten]
    cs.append(EVO._chi_so("tot.mot", "cai tot", 1, EVO.TOT, "ok"))
    return {"luc": "2026-01-01 00:00:00", "chi_so": cs,
            "dem": {EVO.XAU: len(xau_ten), EVO.TOT: 1, EVO.CHUA_DO: 0}}


class ChiGuiKhiTAP_VAN_DE_DOI(unittest.TestCase):
    def setUp(self):
        self.goc = EVO.DAU_VET_XA
        self.tam = GOC / "reports" / "_evo_da_bao_TEST.json"
        EVO.DAU_VET_XA = self.tam
        self.tam.unlink(missing_ok=True)

    def tearDown(self):
        self.tam.unlink(missing_ok=True)
        EVO.DAU_VET_XA = self.goc

    def _gia_vet(self, ds):
        self.tam.parent.mkdir(exist_ok=True)
        self.tam.write_text(json.dumps({"xau": ds}), encoding="utf-8")

    def test_tap_khong_doi_thi_KHONG_gui(self):
        self._gia_vet(["a.mot", "b.hai"])
        r = EVO.bao_xa(_ket(["a.mot", "b.hai"]), in_ra=lambda *a: None)
        self.assertFalse(r["gui"])
        self.assertEqual(r.get("moi"), None, "khong duoc dung toi buoc dung tin")

    def test_co_van_de_MOI_thi_dung_tin(self):
        self._gia_vet(["a.mot"])
        r = EVO.bao_xa(_ket(["a.mot", "b.hai"]), in_ra=lambda *a: None)
        self.assertIn("b.hai", r["moi"])
        self.assertIn("MOI XAU: b.hai", r["van"])

    def test_van_de_DA_HET_cung_phai_bao(self):
        self._gia_vet(["a.mot", "b.hai"])
        r = EVO.bao_xa(_ket(["a.mot"]), in_ra=lambda *a: None)
        self.assertIn("b.hai", r["da_het"])
        self.assertIn("DA HET: b.hai", r["van"])

    def test_ep_gui_duoc_ke_ca_khi_khong_doi(self):
        self._gia_vet(["a.mot"])
        r = EVO.bao_xa(_ket(["a.mot"]), luon=True, in_ra=lambda *a: None)
        self.assertIn("van", r)
        self.assertIn("khong doi", r["van"])

    def test_tin_nhan_co_de_xuat_chay_duoc_khi_co(self):
        self._gia_vet([])
        ket = _ket(["x.mot"])
        ket["chi_so"][0]["de_xuat"] = "python -m nhan.kham_pha_nguon"
        r = EVO.bao_xa(ket, in_ra=lambda *a: None)
        self.assertIn("python -m nhan.kham_pha_nguon", r["van"])

    def test_KHONG_ghi_dau_vet_khi_gui_that_bai(self):
        """Gui hong ma van ghi dau vet thi lan sau se im - va van de bien mat
        khoi tam mat ma khong ai sua."""
        self._gia_vet([])
        EVO.bao_xa(_ket(["x.mot"]), in_ra=lambda *a: None)
        d = json.loads(self.tam.read_text(encoding="utf-8"))
        self.assertEqual(d.get("xau"), [],
                         "da ghi dau vet du chua gui duoc")


if __name__ == "__main__":
    unittest.main(verbosity=2)
