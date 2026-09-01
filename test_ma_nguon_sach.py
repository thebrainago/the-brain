# -*- coding: utf-8 -*-
"""Ma nguon cua du an khong duoc chua ky tu dieu khien lac.

VI SAO CO BAI KIEM NAY (01/09/2026): trong mot phien lam viec, cung MOT loi lap
lai BA LAN - va lan nao cung mat vai luot moi tim ra, vi trieu chung khong giong
nguyen nhan.

Loi: va file qua heredoc lam `\b` trong mot bieu thuc chinh quy bi ghi thanh ky
tu BACKSPACE (0x08). Regex van bien dich duoc, khong bao loi gi, chi la KHONG
BAO GIO KHOP. Trieu chung nhin tu ngoai:
  - `_GAN` khong tim duoc bien nao -> Sonic R mat het tham so
  - `_chon_nhanh_cau_hinh` tra None -> cong tac cau hinh khong doc duoc
  - `rut_python` tra rong -> ca phuong ngu Python cam

Ba lan deu phai truy nguoc tu "ket qua rong" ve toi mot byte vo hinh. Mot bai
kiem hai dong bat duoc ca ba, va bat NGAY.
"""
from __future__ import annotations

import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent

#: Ky tu dieu khien KHONG duoc phep trong ma nguon. Cho phep tab (9), xuong dong
#: (10, 13) va form feed (12) vi chung xuat hien hop le.
_CAM = {c for c in range(32)} - {9, 10, 12, 13}


def _cac_file_py():
    for thu in ("nhan", "tru", "."):
        for p in (LAB / thu).glob("*.py"):
            if "backups" in str(p) or p.name.startswith("_"):
                continue
            yield p


class MaNguonSach(unittest.TestCase):
    def test_khong_co_ky_tu_dieu_khien_lac(self):
        hong = []
        for p in _cac_file_py():
            try:
                s = p.read_text(encoding="utf-8")
            except Exception:
                continue
            for i, ch in enumerate(s):
                if ord(ch) in _CAM:
                    dong = s.count("\n", 0, i) + 1
                    hong.append(f"{p.name}:{dong} chua ky tu 0x{ord(ch):02x}")
                    break
        self.assertEqual(hong, [], "ky tu dieu khien lac trong ma nguon: " + str(hong))

    def test_moi_file_deu_bien_dich_duoc(self):
        import ast
        hong = []
        for p in _cac_file_py():
            try:
                # `utf-8-sig` bo BOM: file Windows co BOM la hop le,
                # `ast.parse` moi la ben khong chiu duoc.
                ast.parse(p.read_text(encoding="utf-8-sig"))
            except SyntaxError as e:
                hong.append(f"{p.name}:{e.lineno} {e.msg}")
        self.assertEqual(hong, [])



class DuongLLM(unittest.TestCase):
    """Du an tra tien cho Claude nen phai goi duoc Claude."""

    def test_co_ca_duong_anthropic_lan_openai(self):
        from nhan import tri_tue as TT
        self.assertTrue(hasattr(TT, "_goi_anthropic"))
        self.assertTrue(hasattr(TT, "_goi_openai"))

    def test_anthropic_dung_dung_endpoint_va_header(self):
        """Claude khong tuong thich /chat/completions - phai la /v1/messages."""
        import inspect
        from nhan import tri_tue as TT
        src = inspect.getsource(TT._goi_anthropic)
        self.assertIn("/v1/messages", src)
        self.assertIn("x-api-key", src)
        self.assertIn("anthropic-version", src)

    def test_thieu_khoa_thi_bao_ro_chu_khong_nem(self):
        from nhan import tri_tue as TT
        import os
        cu = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            r = TT._goi_anthropic("x", "", {"max_tokens": 10, "timeout_giay": 5})
            self.assertIn("ANTHROPIC_API_KEY", r.get("loi", ""))
        finally:
            if cu:
                os.environ["ANTHROPIC_API_KEY"] = cu

    def test_duong_tat_van_la_mac_dinh(self):
        """Khong ai vo tinh bat duoc cau noi tra tien."""
        from nhan import tri_tue as TT
        self.assertEqual(TT.MAC_DINH["duong"], "tat")

    def test_phanh_chi_phi_con_nguyen(self):
        from nhan import tri_tue as TT
        c = TT.cau_hinh()
        self.assertLessEqual(c["tran_moi_ngay"], 100)
        self.assertGreaterEqual(c["cach_nhau_giay"], 60)

if __name__ == "__main__":
    unittest.main()
