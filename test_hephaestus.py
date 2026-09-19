# -*- coding: utf-8 -*-
"""Test cho `nhan/hephaestus.py` - MODULE DE CO CHE.

So do he thong (LUAT SO 0, chu du an duyet 13/09) khai module nay va goi tat
`b hepha`, nhung file chua bao gio duoc viet. Do la ly do he CHI biet may mo
cai co san: `to_hop.py` ket hop co che DA CO, `noi_sinh.py` doc lich su mot ma,
khong ai SINH ra co che moi tu von tu cua chinh ngu phap.

Hau qua do duoc: ngu phap tinh duoc 54 toan hang, kho co che rong 8 chi bao -
va do rong do phu thuoc vao "co ai viet bai ve no khong".

## BA THU BO TEST NAY KHOA, vi thieu cai nao thi may de thanh may NOI DOI

1. **Tien dang ky.** De 10.000 co che roi test la LUONG THIEN neu tra du gia
   FDR. De 10.000, chon 5 cai dep, bao p < 0,05 la GIAN LAN. Nen mot lo phai
   co `plan_hash` chot TRUOC khi ai cham vao du lieu.
2. **Xac dinh.** Cung dau vao phai cho cung thu tu va cung `plan_hash`. Khong
   thi tien dang ky khong co y nghia gi - hash khong doi chieu duoc voi cai gi.
3. **Thang do.** Toan hang THANG GIA khong duoc so voi mot hang so tran. Du an
   da tra gia cho bay nay: Sonic R sinh ra `open < 2` va `ema34_high < 1,5`,
   ca hai kich hoat 100% so bar.
"""
from __future__ import annotations

import unittest

from nhan import hephaestus as HP
from nhan import ngu_phap as NP


class MoiCoCheDeRaDeuHOP_LE(unittest.TestCase):
    """Dieu kien can dau tien: may de khong duoc de ra rac."""

    def setUp(self):
        self.ds = HP.duc(han_ngach=200)

    def test_de_ra_duoc_so_luong_dang_ke(self):
        self.assertGreaterEqual(len(self.ds), 100, "von tu rong ma de ra qua it")

    def test_moi_spec_qua_duoc_cong_cu_phap(self):
        for s in self.ds:
            self.assertEqual(NP.kiem_khai_bao(s), [], s.get("ten"))

    def test_moi_spec_co_ho_hop_le(self):
        for s in self.ds:
            self.assertIn(s["ho"], NP.HO_HOP_LE, s["ten"])

    def test_cau_giai_thich_la_LUAN_DIEM_khong_phai_tham_so(self):
        """`co_che` la cau man hinh duyet doc. No phai noi VI SAO co nguoi tra
        tien, khong duoc chi liet ke lai tham so."""
        for s in self.ds:
            self.assertGreaterEqual(len(s["co_che"]), 25, s["ten"])

    def test_khong_co_hai_co_che_TRUNG_NHAU(self):
        vt = [NP.van_tay_dieu_kien(s) for s in self.ds]
        self.assertEqual(len(vt), len(set(vt)), "co che trung van tay trong mot lo")

    def test_ten_khong_trung(self):
        ten = [s["ten"] for s in self.ds]
        self.assertEqual(len(ten), len(set(ten)))


class ThangDoPhaiDUNG(unittest.TestCase):
    """Bay da sap that: `open < 2` kich hoat 100% so bar."""

    def setUp(self):
        self.ds = HP.duc(han_ngach=400)

    def test_toan_hang_THANG_GIA_khong_bao_gio_so_voi_hang_so(self):
        xau = []
        for s in self.ds:
            for d in s["vao"]:
                if "hang" not in (d.get("phai") or {}):
                    continue
                if HP.thang_do(d["trai"]) == HP.THANG_GIA:
                    xau.append((s["ten"], d))
        self.assertEqual(xau, [], "toan hang thang gia so voi hang so tran")

    def test_hai_ve_cung_thang_do_khi_khong_phai_hang_so(self):
        xau = []
        for s in self.ds:
            for d in s["vao"]:
                p = d.get("phai") or {}
                if "hang" in p:
                    continue
                if HP.thang_do(d["trai"]) != HP.thang_do(p):
                    xau.append((s["ten"], d))
        self.assertEqual(xau, [])


class XacDinhVaTienDangKy(unittest.TestCase):
    """Khong xac dinh thi tien dang ky vo nghia."""

    def test_chay_hai_lan_ra_y_het_nhau(self):
        a = [s["ten"] for s in HP.duc(han_ngach=120)]
        b = [s["ten"] for s in HP.duc(han_ngach=120)]
        self.assertEqual(a, b, "may de khong xac dinh")

    def test_lo_co_plan_hash_on_dinh(self):
        h1 = HP.dang_ky_lo(HP.duc(han_ngach=120))["plan_hash"]
        h2 = HP.dang_ky_lo(HP.duc(han_ngach=120))["plan_hash"]
        self.assertEqual(h1, h2)

    def test_doi_MOT_co_che_la_doi_plan_hash(self):
        """Hash phai phu thuoc NOI DUNG lo - khong thi no khong chot duoc gi."""
        ds = HP.duc(han_ngach=120)
        h1 = HP.dang_ky_lo(ds)["plan_hash"]
        h2 = HP.dang_ky_lo(ds[:-1])["plan_hash"]
        self.assertNotEqual(h1, h2)

    def test_lo_ghi_du_SO_PHEP_THU(self):
        """FDR tinh theo so phep thu. Lo phai tu khai no dat bao nhieu suat."""
        lo = HP.dang_ky_lo(HP.duc(han_ngach=120))
        self.assertEqual(lo["so_phep_thu"], len(lo["van_tay"]))
        self.assertGreater(lo["so_phep_thu"], 0)

    def test_han_ngach_duoc_ton_trong(self):
        self.assertLessEqual(len(HP.duc(han_ngach=37)), 37)

    def test_han_ngach_nho_la_TAP_CON_DAU_cua_han_ngach_lon(self):
        """Thu tu uu tien phai on dinh: xin 20 cai la duoc 20 cai dau cua 100."""
        it = [s["ten"] for s in HP.duc(han_ngach=20)]
        nhieu = [s["ten"] for s in HP.duc(han_ngach=100)]
        self.assertEqual(it, nhieu[:len(it)])


class KhongDeLaiCAI_DA_CO(unittest.TestCase):
    """De trung cai kho da co la tra tien FDR hai lan cho mot cau tra loi."""

    def test_bo_qua_co_che_da_co_trong_kho(self):
        ds = HP.duc(han_ngach=60)
        da_co = [ds[0], ds[1]]
        moi = HP.duc(han_ngach=60, kho=da_co)
        ten = {s["ten"] for s in moi}
        self.assertNotIn(ds[0]["ten"], ten)
        self.assertNotIn(ds[1]["ten"], ten)


class DoPhuVaDayNguocVeSEEKER(unittest.TestCase):
    """Nua thu hai cua so do: *"Seeker khong tu nghi ra 'di tim Ichimoku';
    Hephaestus bao no di."*"""

    def setUp(self):
        self.kho = [
            {"ten": "a", "ho": "xu_huong", "chieu": 1, "giu": 5, "co_che": "x" * 30,
             "vao": [{"trai": {"chi_bao": "ema", "n": 20}, "phep": ">",
                      "phai": {"chi_bao": "ema", "n": 50}}]},
            {"ten": "b", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 5,
             "co_che": "x" * 30,
             "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<",
                      "phai": {"hang": 30}}]},
        ]

    def test_dem_theo_SO_CO_CHE_khong_theo_so_lan_xuat_hien(self):
        """`ema` xuat hien HAI lan trong co che "a" (ema20 va ema50) nhung do
        phu hoi "bao nhieu CO CHE dung chi bao nay", nen no dem 1.

        Dem theo so lan xuat hien thi mot co che giao cat hai duong EMA se
        trong nhu hai co che dung EMA, va bang do phu - thu dung de quyet dinh
        Seeker di tim gi - se bao kho giau hon that.
        """
        r = HP.do_phu(self.kho)
        self.assertEqual(r["dang_dung"]["ema"], 1)
        self.assertEqual(r["dang_dung"]["rsi"], 1)

    def test_chi_ra_chi_bao_ngu_phap_CO_ma_kho_KHONG_dung(self):
        r = HP.do_phu(self.kho)
        self.assertIn("ichimoku", r["bo_trong"])
        self.assertIn("keltner", r["bo_trong"])
        self.assertNotIn("ema", r["bo_trong"])

    def test_huong_tim_kiem_uu_tien_CHO_TRONG(self):
        """Day nguoc ve Seeker phai la cho TRONG, khong phai cho da day."""
        hg = HP.tu_vung(self.kho, so_huong=5)
        self.assertTrue(hg)
        self.assertTrue(all("ema" not in h["tu_khoa"] for h in hg))

    def test_moi_huong_co_TU_KHOA_tim_duoc(self):
        for h in HP.tu_vung(self.kho, so_huong=5):
            self.assertTrue(h["tu_khoa"])
            self.assertTrue(h["chi_bao"])


class LaiGhepQuaHO(unittest.TestCase):
    """Chu du an: *"ket hop cac he thong va ly thuyet lai voi nhau"*.

    Gia tri khong nam o mot chi bao la, ma o viec dat mot KICH HOAT cua ho nay
    ben trong mot BO LOC cua ho khac - thu khong tai lieu nao viet san.
    """

    def test_co_co_che_ghep_tu_HAI_ho_khac_nhau(self):
        ds = HP.duc(han_ngach=400)
        ghep = [s for s in ds if len(s["vao"]) >= 2]
        self.assertTrue(ghep, "khong de ra co che ghep nao")

    def test_co_che_ghep_dung_chi_bao_cua_hai_nhom_khac_nhau(self):
        ds = HP.duc(han_ngach=400)
        co = False
        for s in ds:
            if len(s["vao"]) < 2:
                continue
            nhom = {HP.nhom_cua(d["trai"]) for d in s["vao"]}
            if len(nhom) >= 2:
                co = True
                break
        self.assertTrue(co, "moi co che ghep deu trong cung mot nhom von tu")


class NguongPhaiCHAM_TOI_DUOC(unittest.TestCase):
    """Bat cai LUON SAI bang mot phep so, khong bang mot luot backtest.

    `phan_vi(n)` la thu hang trong cua so n bar nen no chi nhan n gia tri roi
    rac: voi n = 5 thi gia tri nho nhat la 0,20. `phan_vi(5) < 0,05` khong bao
    gio dung - tren moi tai san, o moi thoi ky - nhung cu phap hoan toan hop
    le, nen no lot cong va kich hoat 0,0%, trong y het mot co che qua hiem.
    """

    def test_tu_choi_nguong_min_hon_do_phan_giai(self):
        d = {"trai": {"chi_bao": "phan_vi", "n": 5,
                      "cua": {"chi_bao": "gia", "cot": "close"}},
             "phep": "<", "phai": {"hang": 0.05}}
        self.assertFalse(HP.nguong_dat_duoc(d))

    def test_nhan_nguong_dat_toi_duoc(self):
        d = {"trai": {"chi_bao": "phan_vi", "n": 20,
                      "cua": {"chi_bao": "gia", "cot": "close"}},
             "phep": "<", "phai": {"hang": 0.05}}
        self.assertTrue(HP.nguong_dat_duoc(d))

    def test_chan_ca_dau_tren(self):
        d = {"trai": {"chi_bao": "phan_vi", "n": 5,
                      "cua": {"chi_bao": "gia", "cot": "close"}},
             "phep": ">", "phai": {"hang": 0.95}}
        self.assertFalse(HP.nguong_dat_duoc(d))

    def test_may_de_KHONG_con_de_ra_loai_nay(self):
        for s in HP.duc(han_ngach=100000):
            for d in s["vao"]:
                self.assertTrue(HP.nguong_dat_duoc(d), s["ten"])


class MoiCoCheDeRaDeuCHAY_DUOC(unittest.TestCase):
    """Cong cu phap KHONG du. Do 19/09: sau spec co `cao_nhat` nhan nguon qua
    `cot` thay vi qua `cua` - `kiem_khai_bao` cho qua sach (no chi di xuong
    `cua` KHI co `cua`), roi ca sau nem `KeyError` luc cham du lieu.

    Day la lop loi chi mot luot chay that moi thay, nen bai nay chay that.
    Khung tong hop la du: no khong tra loi duoc "co lai khong" - va cung khong
    dinh hoi the - nhung no tra loi duoc "co no khong".
    """

    @classmethod
    def setUpClass(cls):
        import numpy as np
        import pandas as pd
        rng = np.random.default_rng(11)
        n = 4000
        c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
        op = np.r_[c[0], c[:-1]]
        hi = c * (1 + abs(rng.normal(0, 0.002, n)))
        lo = c * (1 - abs(rng.normal(0, 0.002, n)))
        cls.df = pd.DataFrame(
            {"open": op, "high": np.maximum(hi, np.maximum(op, c)),
             "low": np.minimum(lo, np.minimum(op, c)), "close": c,
             "tick_volume": rng.integers(80, 400, n) * 1.0},
            index=pd.date_range("2015-01-01", periods=n, freq="h"))
        cls.ds = HP.duc(han_ngach=100000)

    def test_khong_spec_nao_nem_loi_khi_cham_du_lieu(self):
        hong = []
        for s in self.ds:
            try:
                NP.sinh_tu_spec(s, self.df)
            except Exception as e:
                hong.append(f"{s['ten']}: {type(e).__name__}: {str(e)[:70]}")
        self.assertEqual(hong[:5], [], f"{len(hong)}/{len(self.ds)} spec nem loi")

    def test_phan_lon_co_che_ra_tin_hieu_do_duoc(self):
        """Khong doi 100%: mot to hop hiem VAN la mot gia thuyet hop le, va
        khung tong hop nay khong co duoi beo nhu thi truong that. Nhung neu
        phan lon cam thi may de dang sinh rac chu khong sinh gia thuyet."""
        import numpy as np
        song = 0
        for s in self.ds:
            th = NP.sinh_tu_spec(s, self.df)
            if float(np.mean(np.abs(th) > 1e-12)) >= 0.002:
                song += 1
        self.assertGreater(song / len(self.ds), 0.6,
                           "qua nua so co che de ra khong kich hoat noi")
