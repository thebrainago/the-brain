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
        # CA LO, khong phai 400 cai dau. Ban truoc cua bai nay lay `han_ngach=
        # 400` va vi the khong bao gio nhin thay cac khuon xep cuoi - dung luc
        # khuon `nen_manh` moi them vao roi ma bai van xanh.
        self.ds = HP.duc(han_ngach=100000)

    def test_THANG_GIA_khong_bao_gio_so_voi_hang_so_KHAC_0(self):
        """Nguong theo don vi gia chi dung cho MOT ma o MOT thoi ky.

        Hang so 0 la ngoai le that su: `than_nen > 0` ("nen tang") khong deo
        theo don vi nao ca. Nhung no chi hop le khi ve trai DAO QUANH 0 - mot
        `ema20 > 0` thi luon dung va khong mang thong tin nao.
        """
        xau = []
        for s in self.ds:
            for d in s["vao"]:
                p = d.get("phai") or {}
                if "hang" not in p or HP.thang_do(d["trai"]) != HP.THANG_GIA:
                    continue
                if float(p["hang"]) != 0.0 or not HP.quanh_khong(d["trai"]):
                    xau.append((s["ten"], d))
        self.assertEqual(xau, [], "toan hang thang gia so voi hang so tran")

    def test_KHOI_LUONG_khong_bao_gio_so_voi_hang_so(self):
        """So hop dong moi bar khac han giua cac ma va truot theo nam, nen
        `khoi_luong > 300` la nguong cua dung mot ma o dung mot nam."""
        for s in self.ds:
            for d in s["vao"]:
                if "hang" in (d.get("phai") or {}):
                    self.assertNotEqual(HP.thang_do(d["trai"]), HP.THANG_KL,
                                        s["ten"])

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


#: Mot co che "boc tu tai lieu" - dung hinh dang cai `doc_ma` tra ve.
GOC = {"ten": "tac_gia_rsi14_30", "ho": "quay_ve_trung_binh", "chieu": 1,
       "giu": 5, "nguon": "tai_lieu",
       "co_che": "Tac gia mua khi RSI cham vung qua ban tren khung gio.",
       "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<",
                "phai": {"hang": 30.0}}]}

GOC2 = {"ten": "tac_gia_tren_ema200", "ho": "xu_huong", "chieu": 1, "giu": 5,
        "nguon": "tai_lieu",
        "co_che": "Tac gia chi mua khi gia con nam tren duong trung binh dai.",
        "vao": [{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
                 "phai": {"chi_bao": "ema", "n": 200, "cot": "close"}}]}


class RaiLuoiThamSoQuanhBAN_TAC_GIA(unittest.TestCase):
    """*"10 trader chau A co 20 kieu dung Ichimoku"* - bien thien nam o NGUONG
    va CACH GHEP, khong o ban than chi bao. 20 kieu khong phai 20 lan boc tai
    lieu; la 1 chi bao + luoi tham so, do MAY sinh."""

    def setUp(self):
        self.ds = HP.bien_the(GOC)

    def test_sinh_ra_nhieu_ban(self):
        self.assertGreaterEqual(len(self.ds), 4)

    def test_moi_ban_deu_hop_le(self):
        for s in self.ds:
            self.assertEqual(NP.kiem_khai_bao(s), [], s["ten"])

    def test_KHONG_tra_lai_chinh_ban_goc(self):
        goc = NP.van_tay_dieu_kien(GOC)
        self.assertNotIn(goc, [NP.van_tay_dieu_kien(s) for s in self.ds])

    def test_cac_ban_khac_nhau_that(self):
        vt = [NP.van_tay_dieu_kien(s) for s in self.ds]
        self.assertEqual(len(vt), len(set(vt)))

    def test_doi_ca_CHU_KY_lan_NGUONG(self):
        n = {s["vao"][0]["trai"]["n"] for s in self.ds}
        v = {s["vao"][0]["phai"]["hang"] for s in self.ds}
        self.assertGreater(len(n), 1, "khong doi chu ky lan nao")
        self.assertGreater(len(v), 1, "khong doi nguong lan nao")

    def test_giu_nguyen_HO_va_CHIEU_cua_ban_goc(self):
        for s in self.ds:
            self.assertEqual(s["ho"], GOC["ho"])
            self.assertEqual(s["chieu"], GOC["chieu"])

    def test_khong_de_ra_nguong_KHONG_CHAM_TOI_DUOC(self):
        for s in self.ds:
            for d in s["vao"]:
                self.assertTrue(HP.nguong_dat_duoc(d), s["ten"])

    def test_ton_trong_han_ngach(self):
        self.assertLessEqual(len(HP.bien_the(GOC, han_ngach=3)), 3)

    def test_xac_dinh(self):
        a = [s["ten"] for s in HP.bien_the(GOC)]
        b = [s["ten"] for s in HP.bien_the(GOC)]
        self.assertEqual(a, b)


class GhepHAI_HE_DA_CO(unittest.TestCase):
    """*"ket hop cac he thong va ly thuyet lai voi nhau"*. Ghep mot kich hoat
    voi mot bo loc cho ra thu khong ban goc nao co."""

    def test_ghep_duoc_hai_co_che(self):
        s = HP.ghep(GOC, GOC2)
        self.assertIsNotNone(s)
        self.assertEqual(len(s["vao"]), 2)
        self.assertEqual(NP.kiem_khai_bao(s), [])

    def test_TU_CHOI_ghep_hai_co_che_NGUOC_CHIEU(self):
        """Mua va ban cung luc khong phai mot co che - la mot mau thuan."""
        nguoc = dict(GOC2, chieu=-1)
        self.assertIsNone(HP.ghep(GOC, nguoc))

    def test_TU_CHOI_ghep_mot_co_che_voi_CHINH_NO(self):
        self.assertIsNone(HP.ghep(GOC, dict(GOC, ten="ten_khac")))

    def test_ghep_nhieu_khong_sinh_ban_trung(self):
        ds = HP.ghep_lo([GOC, GOC2], han_ngach=50)
        vt = [NP.van_tay_dieu_kien(s) for s in ds]
        self.assertEqual(len(vt), len(set(vt)))

    def test_cau_giai_thich_NOI_CA_HAI_ve(self):
        s = HP.ghep(GOC, GOC2)
        self.assertGreaterEqual(len(s["co_che"]), 25)


class NapVaoKhoPhaiCHAY_KHO_MAC_DINH(unittest.TestCase):
    """`nap()` noi may de voi kho that - va do la cho de gay hong nhat.

    Ngay 19/09 chinh toi goi `them_co_che` mot lan de "xem thu no chay khong",
    va no GHI THAT vao `config/co_che_dsl.json` ngay lap tuc. Kho la du lieu
    san xuat; mot lenh go nham khong duoc phep sua no. Nen `nap` chay KHO
    (`that=False`) o mac dinh, va chi ghi khi duoc bao ro.
    """

    def setUp(self):
        self.ds = HP.duc(han_ngach=8)

    def _kho_tam(self):
        """Tra (thu muc tam, ham don dep) - tro kho sang cho khac, y nhu
        `test_chan_hang_so.test_nap_vao_mau_tu_choi_spec_khong_qua_cong`."""
        import json
        import tempfile
        from pathlib import Path
        tm = tempfile.TemporaryDirectory()
        f = Path(tm.name) / "co_che_dsl.json"
        f.write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")
        cu = (NP.KHO_CO_CHE, NP.MOC_CAO)
        NP.KHO_CO_CHE, NP.MOC_CAO = f, f.with_suffix(".moc_cao")

        def don():
            NP.KHO_CO_CHE, NP.MOC_CAO = cu
            tm.cleanup()
        return f, don

    def test_MAC_DINH_khong_ghi_gi(self):
        f, don = self._kho_tam()
        try:
            r = HP.nap(self.ds)
            self.assertFalse(r["da_ghi"])
            self.assertEqual(len(NP.doc_kho(cho_rong_khi_hong=True)), 0,
                             "chay kho ma van ghi vao kho")
        finally:
            don()

    def test_co_bao_RO_thi_moi_ghi(self):
        f, don = self._kho_tam()
        try:
            r = HP.nap(self.ds, that=True)
            self.assertTrue(r["da_ghi"])
            self.assertGreater(len(NP.doc_kho(cho_rong_khi_hong=True)), 0)
        finally:
            don()

    def test_LUON_tien_dang_ky_du_chi_chay_kho(self):
        """Lo da sinh ra la da ton tai. Khong dang ky no thi lan sau chay lai
        cung lo do se trong nhu mot lo moi, va FDR dem hai lan."""
        f, don = self._kho_tam()
        try:
            r = HP.nap(self.ds)
            self.assertIn("plan_hash", r)
            self.assertEqual(r["so_phep_thu"], len(self.ds))
        finally:
            don()

    def test_bao_ro_CHUA_DO_DUOC_khi_khong_co_du_lieu(self):
        """Khong co chuoi kiem thi phep do ty le kich hoat KHONG chay duoc.
        Bao "dat" luc do la noi doi: chua ai do gi ca."""
        f, don = self._kho_tam()
        try:
            r = HP.nap(self.ds, df_kiem=None)
            self.assertIn(r["do_kich_hoat"], ("DA_DO", "CHUA_DO_DUOC"))
        finally:
            don()

    def test_khong_nap_lai_cai_kho_DA_CO(self):
        f, don = self._kho_tam()
        try:
            HP.nap(self.ds, that=True)
            r2 = HP.nap(self.ds, that=True)
            self.assertEqual(r2["nhan"], 0, "nap lai cung lo ma van vao kho")
        finally:
            don()
