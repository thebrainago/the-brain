# -*- coding: utf-8 -*-
"""DO TAI NGUYEN — bat HONG IM LANG bang cach do, khong bang cach doi bao loi.

Trong mot phien (30/08/2026), NAM loi lam dung hoac lam lech day chuyen, va
**khong loi nao bao mot ngoai le**:

  1. `toan_van` khong co duong qua trinh duyet -> 675/1338 tai lieu khong doc duoc
  2. Loi MOI TRUONG bi ghi thanh "dia chi hong" vinh vien -> 84 dia chi khoa oan
  3. `doc_gan` mo tab moi khong dong -> Chrome 356 tab, luot keo dung han
  4. Nhan NEN_GOP chi gan duoc o V3 -> 2/3 co che co tin hieu bi chan
  5. Nguon trinh duyet khong ORDER BY uu_tien -> facebook/x/youtube 0 bai

Ca nam deu la HONG IM LANG: he van chay, bo test van xanh. Voi mot day chuyen
dinh chay 24/7 khong nguoi truc, day la loai hong nguy hiem nhat - no khong
dung lai, no chi lang le ngung lam viec.

Module nay do bon thu de EVO nhin thay chung. Bo test o day khoa MOT hop dong:
**do khong duoc thi phai tra `None`, khong duoc tra so bia** - vi EVO se so con
so do voi mot nguong, va mot so bia se sinh ra bao dong gia hoac im lang gia.

Khong goi mang, khong doi hoi Chrome dang chay.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import do_tai_nguyen as DTN   # noqa: E402


class KhongDoDuocThiTraNone(unittest.TestCase):
    """Hop dong quan trong nhat: thieu so lieu != so lieu bang 0."""

    def test_khong_co_CDP_thi_so_tab_la_None_chu_khong_phai_0(self):
        r = DTN.so_tab_trinh_duyet(cong=(59_998, 59_999))
        self.assertIsNone(r["cong"])
        self.assertIsNone(
            r["so_tab"],
            "tra 0 khi khong do duoc -> EVO se ket luan 'trinh duyet sach' "
            "trong khi that ra no khong nhin thay gi")

    def test_khong_co_tien_trinh_khop_thi_ram_la_0_va_so_tien_trinh_la_0(self):
        r = DTN.ram_trinh_duyet(dau_hieu="khong_bao_gio_co_chuoi_nay_xyz")
        self.assertIn("gb", r)
        self.assertIn("so_tien_trinh", r)
        if r["so_tien_trinh"] is not None:
            self.assertEqual(r["so_tien_trinh"], 0)
            self.assertEqual(r["gb"], 0.0)


class DoDuocMayThat(unittest.TestCase):

    def test_may_tra_ve_ba_chi_so_hop_le(self):
        m = DTN.may()
        if not m:
            self.skipTest("khong co psutil")
        self.assertGreaterEqual(m["ram_dung_pct"], 0.0)
        self.assertLessEqual(m["ram_dung_pct"], 100.0)
        self.assertGreater(m["ram_trong_gb"], 0.0)
        self.assertGreaterEqual(m["cpu_pct"], 0.0)

    def test_tat_ca_gom_du_khoa_ma_EVO_doc(self):
        """EVO doc dung nhung khoa nay; doi ten mot khoa la lam cam EVO."""
        r = DTN.tat_ca()
        for k in ("tab", "chrome"):
            self.assertIn(k, r, f"thieu khoa '{k}' ma EVO doc")
        self.assertIn("so_tab", r["tab"])
        self.assertIn("gb", r["chrome"])

    def test_chay_xong_nhanh_tu_lan_thu_hai(self):
        """EVO goi moi luot. Cham thi no tu tro thanh mot cai nghen.

        LAN DAU cham hon vi phai DO CONG CDP: mot cong khong ai nghe phai cho
        het timeout. Do that 30/08: lan dau 3,56 giay, tu lan hai 1,55 giay nho
        nho lai cong da dung duoc.

        Nguong dat o 2,5 giay cho lan thu hai. EVO co ngan sach 150 giay/luot
        nen 1,5 giay la 1% - chap nhan duoc; 4 giay tro len thi khong.
        """
        import time
        DTN.tat_ca()                      # lan dau: do cong
        t0 = time.time()
        DTN.tat_ca()
        giay = time.time() - t0
        self.assertLess(giay, 2.5,
                        f"do tai nguyen mat {giay:.1f}s moi luot - qua dat cho "
                        "mot phep do phu tro")


class EVODocDuocKetQua(unittest.TestCase):
    """Doi chieu hai dau: khoa o day phai khop khoa EVO tra cuu."""

    def test_khoa_khop_voi_nguong_cua_EVO(self):
        from tru import evolution as EVO
        self.assertIsInstance(EVO.TRAN_TAB_BAO_DONG, int)
        self.assertIsInstance(EVO.TRAN_RAM_CHROME_GB, (int, float))
        # 356 tab da lam dung day chuyen that -> tran phai bat duoc con so do
        self.assertLess(EVO.TRAN_TAB_BAO_DONG, 356,
                        "tran cao hon so tab da tung lam dung he")


if __name__ == "__main__":
    unittest.main()
