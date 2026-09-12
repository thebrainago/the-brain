# -*- coding: utf-8 -*-
"""Kiem `nhan/khoa_tester.py`.

Cai khoa nay bao ve mot rang buoc VAT LY: `chay_tester_kho` ghi de cung mot
.mq5 / .ini / .xml va may chi co MOT terminal64.exe. Hai viec cung luc thi ghi
de ket qua cua nhau VA khong ai bao loi - bang so ra doc y het mot ket qua that.

Do la dang hong dat nhat cua du an: no khong lam gi sap, no chi lam moi con so
sai. Nen o day bai kiem quan trong nhat la bai kiem TU CHOI.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import khoa_tester as KT  # noqa: E402


class KhoaPhaiTU_CHOI_NGUOI_THU_HAI(unittest.TestCase):
    def setUp(self):
        KT.KHOA.unlink(missing_ok=True)

    def tearDown(self):
        KT.KHOA.unlink(missing_ok=True)

    def test_trong_thi_lay_duoc(self):
        self.assertTrue(KT.thu_lay("viec A")["duoc"])

    def test_TIEN_TRINH_KHAC_bi_tu_choi(self):
        """Khoa phai theo FILE, khong theo bien trong tien trinh - ba tien trinh
        khac nhau khong nhin thay bien cua nhau."""
        KT.thu_lay("viec A")
        r = subprocess.run(
            [sys.executable, "-c",
             "import sys,json;sys.path.insert(0,r'%s');"
             "from nhan import khoa_tester as KT;"
             "print(json.dumps(KT.thu_lay('viec B')))" % GOC],
            capture_output=True, text=True, cwd=str(GOC))
        kq = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertFalse(kq["duoc"], "tien trinh thu hai VAN lay duoc khoa")
        self.assertIn("ghi de ket qua cua nhau", kq["ly_do"])

    def test_cung_tien_trinh_thi_khong_tu_chan(self):
        KT.thu_lay("viec A")
        self.assertTrue(KT.thu_lay("viec A lan hai")["duoc"])

    def test_with_tra_khoa_khi_ra(self):
        with KT.giu("viec A"):
            self.assertIsNotNone(KT.dang_giu())
        self.assertIsNone(KT.dang_giu())

    def test_tra_khoa_KE_CA_KHI_NEM_LOI(self):
        """Mot ngoai le giua chung ma khong tra khoa se khoa cung ca day chuyen."""
        with self.assertRaises(ValueError):
            with KT.giu("viec A"):
                raise ValueError("hong giua chung")
        self.assertIsNone(KT.dang_giu())

    def test_nguoi_thu_hai_nem_TesterDangBan(self):
        KT.KHOA.write_text(json.dumps(
            {"pid": os.getpid() + 1 if os.getpid() % 2 else 999999,
             "viec": "nguoi khac", "luc": time.time(),
             "luc_doc": "2026-09-11 22:00:00"}), encoding="utf-8")
        # gia dinh pid do khong ton tai thi khoa se bi thu hoi; nen ep bang pid THAT
        KT.KHOA.write_text(json.dumps(
            {"pid": os.getppid(), "viec": "nguoi khac", "luc": time.time(),
             "luc_doc": "2026-09-11 22:00:00"}), encoding="utf-8")
        with self.assertRaises(KT.TesterDangBan):
            with KT.giu("viec cua toi"):
                pass


class KhoaMO_COI_PHAI_DUOC_THU_HOI(unittest.TestCase):
    """Mot lan Ctrl-C khong duoc khoa cung ca day chuyen cho toi khi co nguoi
    vao xoa file."""

    def tearDown(self):
        KT.KHOA.unlink(missing_ok=True)

    def test_qua_han_thi_thu_hoi(self):
        KT.KHOA.write_text(json.dumps(
            {"pid": os.getppid(), "viec": "cu", "luc": time.time() - KT.HAN_GIAY - 10,
             "luc_doc": "cu"}), encoding="utf-8")
        self.assertIsNone(KT.dang_giu())

    def test_chu_giu_da_chet_thi_thu_hoi(self):
        KT.KHOA.write_text(json.dumps(
            {"pid": 999_999_999, "viec": "chu da chet", "luc": time.time(),
             "luc_doc": "vua xong"}), encoding="utf-8")
        self.assertIsNone(KT.dang_giu())

    def test_file_khoa_HONG_thi_thu_hoi_chu_khong_nem(self):
        KT.KHOA.parent.mkdir(exist_ok=True)
        KT.KHOA.write_text("{khong phai json", encoding="utf-8")
        self.assertIsNone(KT.dang_giu())


class TesterKhoDA_DUNG_KHOA(unittest.TestCase):
    def test_chay_tester_kho_goi_khoa(self):
        """Viet cai khoa ma khong ai goi thi bang khong viet."""
        import inspect
        import chay_tester_kho as CT
        ma = inspect.getsource(CT.chay)
        self.assertIn("khoa_tester", ma,
                      "chay_tester_kho.chay khong giu khoa - rang buoc mot "
                      "terminal64 lai quay ve dua vao ky luat con nguoi")
        self.assertIn("KT.giu", ma)




class KHONG_SCRIPT_NAO_DUOC_PHONG_TERMINAL_NGOAI_KHOA(unittest.TestCase):
    """Cai khoa chi co gia tri neu MOI duong phong deu di qua no.

    Bai kiem nay quet ma nguon that: bat ky file nao goi `Popen` voi `XM_EXE`
    (hoac `/config:`) ma trong file khong he nhac toi `khoa_tester` deu bi keu.
    Do la cach duy nhat chan duoc mot script MOI viet sau nay - ghi chu trong
    tai lieu khong chan duoc ai.
    """

    #: File duoc mien, kem LY DO. Mien ma khong co ly do la mo lai dung cai lo
    #: vua bit.
    MIEN = {
        "nhan/khoa_tester.py": "chinh la cai khoa",
        "test_khoa_tester.py": "bai kiem cua cai khoa",
        # He TRUOC 15/08/2026, khong nam trong duong chay hien tai va khong co
        # trong bang viec cua qwen. Neu mot ngay nao do goi lai chung thi PHAI
        # boc khoa truoc, va go ten khoi day.
        "lab.py": "he truoc 15/08, da nghi (BAN_DO.md ghi ro)",
        "mt5_worker.py": "he truoc 15/08, khong trong bang viec qwen",
        "mt5_chay_ichimoku.py": "script mot lan cua 12/08, khong con goi",
        "chay_tester_z5.py": "thay bang _z5_don_bay.py (da boc khoa)",
        "ea_tu_dong.py": "duong EA tu dong cu, chua noi lai vao day chuyen",
    }

    def test_quet_toan_bo_lab(self):
        import re
        vi_pham = []
        for f in sorted(GOC.glob("*.py")) + sorted((GOC / "nhan").glob("*.py")):
            ten = f.relative_to(GOC).as_posix()
            if ten in self.MIEN:
                continue
            try:
                s = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            phong = re.search(r"Popen\s*\(\s*\[[^\]]*(?:XM_EXE|terminal64|/config:)",
                              s, re.S)
            if phong and "khoa_tester" not in s:
                vi_pham.append(ten)
        self.assertEqual(
            vi_pham, [],
            "cac file sau phong terminal64 NGOAI khoa - hai viec tester cung luc "
            "se ghi de ket qua cua nhau va khong ai bao loi: " + str(vi_pham))


class CuaGIETCungPhaiCoKhoa(unittest.TestCase):
    """Do 12/09/2026: khoa chan duong PHONG nhung KHONG chan duong GIET.

    Bon script (`mt5_worker`, `lab`, `mt5_chay_ichimoku`, `chay_tester_z5`) goi
    thang `taskkill /F /IM terminal64.exe` de don duong. Lenh do giet ca luot
    tester cua nguoi khac, roi ben do doc file ket qua CU **va khong bao loi**.
    Mot cai khoa chi chan mot chieu thi khong phai mot cai khoa.
    """

    def setUp(self):
        KT.KHOA.unlink(missing_ok=True)

    def tearDown(self):
        KT.KHOA.unlink(missing_ok=True)

    def test_tu_choi_giet_khi_nguoi_khac_giu(self):
        # Gia lam mot tien trinh KHAC dang giu khoa (pid cua he dieu hanh, luon song)
        KT.KHOA.parent.mkdir(exist_ok=True)
        KT.KHOA.write_text(json.dumps(
            {"pid": 4, "viec": "tester cua nguoi khac", "luc": time.time(),
             "luc_doc": "2026-09-12 00:00:00"}), encoding="utf-8")
        with self.assertRaises(KT.TesterDangBan):
            KT.dong_terminal("thu giet")

    def test_khong_con_file_nao_taskkill_thang(self):
        """Hieu chuan chieu nguoc: neu con duong tat thi cai khoa vo nghia."""
        import re
        from pathlib import Path
        goc = Path(__file__).resolve().parent
        rx = re.compile(r"taskkill.{0,40}terminal64", re.I)
        hong = []
        for p in list(goc.glob("*.py")) + list(goc.glob("nhan/*.py")) +                 list(goc.glob("tru/*.py")) + list(goc.glob("qwen/*.py")):
            if p.name == "khoa_tester.py" or p.name == Path(__file__).name:
                continue
            try:
                s = p.read_text(encoding="utf-8-sig")
            except Exception:
                continue
            if rx.search(s):
                hong.append(p.name)
        self.assertEqual(hong, [], "goi taskkill terminal64 KHONG qua khoa_tester: "
                                   + str(hong))


if __name__ == "__main__":
    unittest.main()
