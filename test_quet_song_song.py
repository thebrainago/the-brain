# -*- coding: utf-8 -*-
"""QUET SONG SONG — phai cho cung PHAN QUYET voi quet tuan tu.

DO THAT 30/08/2026 tren ca 18 co che x 122 tai san D1 (2.196 o):

     1 tien trinh   117,8 s   18,6 o/giay
     8 tien trinh    31,1 s   70,6 o/giay   (3,8 lan)
    16 tien trinh    27,8 s   79,0 o/giay   (4,2 lan)

Phep do nay LAT mot niem tin cu cua du an. Ghi chu `may-nghet-bang-thong-ram`
ket luan "20 luong chay y het 1 luong" va khuyen KHONG bat dau bang nhan luong.
Ket luan do do bang mot bai quet MANG LON nen nghet kenh nho; mot o cua pheu D1
chi ~128 KB, nam gon trong cache CPU. Hai bai do khac tap lam viec.

SONG SONG LAM LO RA MOT LOI THAT: `do_luc` ghi cache MDE bang
`write_text` thang len file dang duoc doc - khong nguyen tu va khong gop. Tam
tien trinh cung ghi thi muc cua nhau bien mat, va ai doc trung cua so ghi se
nhan JSON hong roi coi nhu cache RONG. Da sua bang temp + os.replace + doc lai
truoc khi ghi (giong het `chi_phi._ghi_cau_hinh`, noi du an DA sua dung loi nay
tu 15/08 nhung khong ai mang sang).

CON MOT DIEU CHUA GIAI THICH DUOC, ghi lai de khong ai quen: dung **1/2.196 o**
(`stoch_qua_ban|XM_USDCHF`) cho Sharpe lech o chu so thu ba giua hai cach chay,
voi so lenh y het (77) va phan quyet y het. Chay lai 5 lan trong cung mot tien
trinh thi on dinh tuyet doi. Nghi la V2 quet luoi tham so va hai bo sat nhau
doi nguoi thang, nhung CHUA CHUNG MINH.

Vi vay bo test nay khoa PHAN QUYET, khong khoa chu so thap phan: phan quyet la
thu di tiep vao day chuyen, con Sharpe o tang kham pha chi de xep hang.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

import quet_be_mat as Q   # noqa: E402

MAU_THU = ["ibs_bat_day", "donchian", "cuoi_thang"]


class SongSongCungPhanQuyetVoiTuanTu(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.a = Q.quet("D1", cac_mau=MAU_THU, so_tien_trinh=1)
        cls.b = Q.quet("D1", cac_mau=MAU_THU, so_tien_trinh=4)

    def test_cung_tap_o(self):
        self.assertEqual(set(self.a["o"]), set(self.b["o"]))

    def test_MOI_O_cho_cung_PHAN_QUYET(self):
        lech = [k for k in self.a["o"]
                if self.a["o"][k]["ket_luan"] != self.b["o"][k]["ket_luan"]]
        self.assertEqual(
            lech, [],
            "song song cho phan quyet KHAC tuan tu - day chuyen khong tat dinh:\n"
            + "\n".join(f"  {k}: {self.a['o'][k]['ket_luan']} vs "
                        f"{self.b['o'][k]['ket_luan']}" for k in lech[:8]))

    def test_cung_so_lenh(self):
        """So lenh la ham cua TIN HIEU. Lech o day nghia la tin hieu doi."""
        lech = [k for k in self.a["o"]
                if self.a["o"][k]["so_lenh"] != self.b["o"][k]["so_lenh"]]
        self.assertEqual(lech, [],
                         f"so lenh lech o {len(lech)} o - tin hieu khong tat dinh")

    def test_cung_ket_luan_pham_vi(self):
        self.assertEqual(self.a["pham_vi"], self.b["pham_vi"])

    def test_bo_dem_bi_loai_khong_bi_mat_khi_chay_song_song(self):
        """Moi tien trinh con co bo dem RIENG; `quantlab` co doc `lay_bo_dem()`.

        Khong gom ve thi tien trinh cha mat sach phan do va khong ai biet.
        """
        self.assertEqual(len(self.a["bi_loai"]), len(self.b["bi_loai"]))
        self.assertGreater(len(self.b["bi_loai"]), 0, "bo dem rong -> nghi bi mat")

    def test_tong_ket_giong_nhau(self):
        self.assertEqual(self.a["tong"], self.b["tong"])


class GhiNhanSoTienTrinh(unittest.TestCase):

    def test_ket_qua_ghi_lai_da_chay_may_tien_trinh(self):
        r = Q.quet("D1", cac_mau=["donchian"], so_tien_trinh=2)
        self.assertIn("so_tien_trinh", r)
        # mot co che thi khong the chia cho 2 tien trinh
        self.assertEqual(r["so_tien_trinh"], 1)

    def test_mac_dinh_la_diem_ngot_da_do(self):
        self.assertGreaterEqual(Q.SO_TIEN_TRINH, 4)
        self.assertLessEqual(Q.SO_TIEN_TRINH, 16)


if __name__ == "__main__":
    unittest.main()
