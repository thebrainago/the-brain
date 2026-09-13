# -*- coding: utf-8 -*-
"""MA NGUON EA/CHI BAO -> CodeArtifact -> ung vien.

Bo test nay khoa BAI KIEM HAI CHIEU cua bo khop ma nguon. Mot chieu thoi la vo
nghia: mot bo khop tu choi TAT CA cho so lieu y het mot bo khop hieu chuan tot.

Hai lan hieu chuan sai da xay ra that ngay 22/08, va ca hai deu duoc khoa o day:

1. **Cua so van canh +-600 ky tu** (chinh cho van xuoi) lam
   `Session Opening Range Breakout EA` bi TU CHOI du co du ca tu khoa lan 14
   diem dat lenh - vi ten co che nam o chu thich dau file con code dat lenh nam
   10 KB ben duoi. Voi ma nguon, van canh phai o muc CA FILE.

2. **Cum van xuoi "sell signal" trong VAN_CANH_MA** lam
   `Fisher Transform Indicator` LOT thanh "chien luoc RSI" - cum do nam trong
   chu thich cua mot chi bao thuan tuy khong he dat lenh. Chi gu API dat lenh
   that moi phan biet duoc CHIEN LUOC voi CHI BAO.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import bien_dich_ung_vien as BD
from nhan import hop_dong as HD
from nhan import ma_nguon as MN
from nhan import so as SO

# --- mau ma nguon toi thieu, viet tay ------------------------------------

EA_THAT = """//+------------------------------------------------------------------+
//|  Opening Range Breakout EA                                       |
//|  Vao lenh khi gia pha vo bien do 30 phut dau phien.              |
//+------------------------------------------------------------------+
#include <Trade/Trade.mqh>
CTrade trade;

double orHigh, orLow;

void OnTick()
  {
   // ... 400 dong tinh toan o giua, ten co che o tren cung ...
   if(Close[0] > orHigh)
      trade.Buy(0.10, _Symbol);
   if(Close[0] < orLow)
      trade.Sell(0.10, _Symbol);
  }
"""

CHI_BAO_THUAN = """//+------------------------------------------------------------------+
//|  Fisher Transform Indicator                                      |
//|  Ve duong Fisher Transform. Giong RSI o cho no do da mua/da ban.  |
//|  Deciding when a given value counts as a buy or sell signal is    |
//|  left to the user - this indicator only draws the line.           |
//+------------------------------------------------------------------+
#property indicator_separate_window
double Buf[];

int OnCalculate(const int rates_total, const int prev_calculated,
                const double &price[])
  {
   for(int i = prev_calculated; i < rates_total; i++)
      Buf[i] = price[i];
   return(rates_total);
  }
"""

TIEN_ICH = """//| Server Clock and Daily Reset Hour
//| Hien gio may chu len bieu do.
void OnTick() { Comment(TimeCurrent()); }
"""


def _code(noi_dung, ten="X.mq5", tieu_de="thu"):
    return HD.CodeArtifact(
        source_id="mql5_codebase:experts",
        repository_url="https://www.mql5.com/en/code/99999",
        revision="mql5-code-99999", path=ten,
        retrieved_at="2026-08-22T00:00:00Z", content=noi_dung,
        language="mql5", metadata={"tieu_de": tieu_de, "muc": "experts"})


class BaiKiemHaiChieu(unittest.TestCase):
    """Bay phai bi tu choi VA co che that phai duoc nhan ra."""

    def test_EA_that_duoc_nhan_ra(self):
        """Ten co che o dau file, code dat lenh o cuoi - phai van khop."""
        uv = BD.bien_dich(_code(EA_THAT, "ORB_EA.mq5", "Opening Range Breakout EA"))
        self.assertTrue(uv, "EA that bi tu choi - bo khop qua chat")
        self.assertEqual(uv[0].metadata["mau"], "orb_pha_vo")

    def test_chi_bao_thuan_bi_tu_choi(self):
        """Nhac RSI + cum 'buy or sell signal' nhung KHONG dat lenh."""
        self.assertEqual(BD.bien_dich(_code(CHI_BAO_THUAN, "Fisher.mq5")), [])

    def test_tien_ich_bi_tu_choi(self):
        self.assertEqual(BD.bien_dich(_code(TIEN_ICH, "Clock.mq5")), [])

    def test_dat_lenh_nhung_khong_ten_co_che_thi_khong_ra_ung_vien(self):
        """Co OrderSend nhung khong mau nao trong thu vien duoc goi ten."""
        ma = "CTrade trade;\nvoid OnTick(){ trade.Buy(0.1,_Symbol); }"
        self.assertEqual(BD.bien_dich(_code(ma, "Blind.mq5")), [])

    def test_van_canh_ma_khong_nhan_cum_van_xuoi(self):
        """'sell signal' trong chu thich KHONG duoc tinh la dat lenh."""
        self.assertIsNone(BD._VAN_CANH_MA_RE.search("// this is a sell signal"))
        self.assertIsNotNone(BD._VAN_CANH_MA_RE.search("trade.Buy(0.1,_Symbol);"))
        self.assertIsNotNone(BD._VAN_CANH_MA_RE.search("OrderSend(req,res);"))


class KhongChayMaTaiVe(unittest.TestCase):
    """Rang buoc an toan so 1: ma nguon la VAN BAN de doc, khong bao gio chay."""

    def test_module_khong_he_goi_exec_hay_import_dong(self):
        nguon = (Path(LAB) / "nhan" / "ma_nguon.py").read_text(encoding="utf-8")
        than = "\n".join(d for d in nguon.split("\n") if not d.strip().startswith("#"))
        for cam in ("exec(", "eval(", "__import__", "importlib", "subprocess",
                    "os.system", "compile("):
            self.assertNotIn(cam, than, f"ma_nguon.py dung {cam}")

    def test_bien_dich_chi_tro_toi_mau_co_san(self):
        from nhan import mau as MAU, ngu_phap as NP
        NP.nap_vao_mau()
        uv = BD.bien_dich(_code(EA_THAT, "ORB_EA.mq5"))
        for x in uv:
            self.assertIn(x.metadata["mau"], MAU.MAU)


class HopDongArtifact(unittest.TestCase):

    def setUp(self):
        self._db = SO.DB
        self._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(self._tmp.name) / "n.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db
        self._tmp.cleanup()

    def test_thanh_artifact_co_provenance_day_du(self):
        a = MN.thanh_artifact({
            "id": "76331", "url": "https://www.mql5.com/en/code/76331",
            "tieu_de": "HybridMicrostructure EA", "muc": "experts",
            "ten_file": "Hybrid.mq5", "noi_dung": EA_THAT, "so_byte": len(EA_THAT)})
        self.assertEqual(a.revision, "mql5-code-76331")
        self.assertEqual(a.path, "Hybrid.mq5")
        self.assertTrue(a.repository_url.endswith("/76331"))
        self.assertEqual(a.language, "mql5")

    def test_ghi_duoc_vao_so_cai_va_khong_trung(self):
        a = MN.thanh_artifact({
            "id": "1", "url": "https://www.mql5.com/en/code/1", "tieu_de": "t",
            "muc": "experts", "ten_file": "A.mq5", "noi_dung": EA_THAT,
            "so_byte": len(EA_THAT)})
        _i1, moi1 = SO.them_artifact(a)
        _i2, moi2 = SO.them_artifact(a)
        self.assertTrue(moi1)
        self.assertFalse(moi2, "cung mot file ghi hai lan phai bi coi la trung")

    def test_tran_kich_thuoc_duoc_khai_bao(self):
        self.assertGreater(MN.TRAN_BYTE, MN.SAN_BYTE)
        self.assertLessEqual(MN.TRAN_BYTE, 2_000_000)


class BienDichNhanCaHaiLoai(unittest.TestCase):

    def test_tu_choi_loai_artifact_la(self):
        with self.assertRaises(HD.ContractError):
            BD.bien_dich("khong phai artifact")

    def test_nhan_ca_document_lan_code(self):
        tl = HD.DocumentArtifact(
            source_id="x", source_url="https://e.com/a", title="RSI oversold entry",
            retrieved_at="2026-08-22T00:00:00Z",
            content="Buy when RSI is oversold, this is the entry signal.")
        self.assertTrue(BD.bien_dich(tl))
        self.assertTrue(BD.bien_dich(_code(EA_THAT)))

    def test_loai_nguon_duoc_ghi_lai(self):
        uv = BD.bien_dich(_code(EA_THAT))
        self.assertEqual(uv[0].metadata["loai_nguon"], "ma_nguon")
        self.assertIn("ma_nguon", uv[0].tags)


class NhanDangURLCanTaiPayload(unittest.TestCase):
    """`RE_URL_CODE_MQL5` la cong vao cua `_doc_dinh_tuyen` (tru/seeker.py).

    Sai o day (khong khop mot bien the URL that) tuong duong voi mot trang bi
    bo qua vinh vien khoi duong tai payload - dung loi da xay ra voi href
    tuong doi trong `liet_ke_mql5` (xem chu thich cua ham do).
    """

    def test_khop_bien_the_that_cua_URL_trang_bai(self):
        for u in ("https://www.mql5.com/en/code/74894",
                  "https://mql5.com/en/code/74894",       # khong www
                  "https://www.mql5.com/ru/code/26693",   # ngon ngu khac en
                  "https://www.mql5.com/zh/code/1"):
            import re
            self.assertIsNotNone(re.match(MN.RE_URL_CODE_MQL5, u), f"{u} phai khop")

    def test_khong_khop_trang_danh_sach_hay_trang_tai(self):
        import re
        for u in ("https://www.mql5.com/en/code/mt5/experts",
                  "https://www.mql5.com/en/code/download/74894/x.mq5",
                  "https://www.mql5.com/en/signals/1",
                  "https://www.mql5.com/en/code"):
            self.assertIsNone(re.match(MN.RE_URL_CODE_MQL5, u), f"{u} khong duoc khop")


class DauHieuMaThatVsLandingPage(unittest.TestCase):
    """Phan biet FILE MA that voi TRANG LANDING - day la ca goc cua loi he thong
    chu du an bao: mot trang mql5.com/en/code/N dai 62.924 ky tu nhung 0 lan
    xuat hien OnTick/OrderSend/CTrade (kiem 12/09/2026, xem BAO_CAO)."""

    def test_ma_that_co_dau_hieu(self):
        self.assertTrue(MN.co_dau_hieu_ma_that(EA_THAT))
        self.assertTrue(MN.co_dau_hieu_ma_that(CHI_BAO_THUAN))  # co OnCalculate

    def test_trang_landing_KHONG_co_dau_hieu(self):
        # Mo phong dung hinh dang van ban trang landing MQL5: dieu huong +
        # tom tat + binh luan, khong mot dong ma. Do 0 markers la trong tam
        # cua ca lo hong ("62.924 ky tu, 0 lan OnTick/OrderSend/CTrade").
        trang_landing = (
            "Home Market Freelance Jobs Signals Forum CodeBase Articles "
            "Quotes VPS Rent Blogs " * 40 +
            "This SuperTrend indicator draws colored trend lines on the "
            "chart. Downloads: 512. Rating 4.5 stars. Comments (12): "
            "great indicator, works well, thanks for sharing! " * 20
        )
        self.assertGreater(len(trang_landing), 2000)
        self.assertFalse(MN.co_dau_hieu_ma_that(trang_landing))

    def test_rong_hoac_None_khong_co_dau_hieu(self):
        self.assertFalse(MN.co_dau_hieu_ma_that(""))
        self.assertFalse(MN.co_dau_hieu_ma_that(None))


class LayHaiTangDNS(unittest.TestCase):
    """`_lay` phai thu DNS that TRUOC, chi bat `dns_vuot` khi lan dau that bai -
    day la sua chinh cua phien 13/09 (xem chu thich o `_lay`)."""

    def setUp(self):
        from nhan import dns_vuot as DV
        self.DV = DV
        DV.tat()
        self._ban_do_cu = dict(DV.BAN_DO)

    def tearDown(self):
        self.DV.tat()
        self.DV.BAN_DO.clear()
        self.DV.BAN_DO.update(self._ban_do_cu)

    def test_thanh_cong_ngay_lan_dau_thi_KHONG_bat_dns_vuot(self):
        goi = {"bat": 0}
        goc_bat = self.DV.bat
        self.DV.bat = lambda: goi.__setitem__("bat", goi["bat"] + 1) or goc_bat()
        try:
            class _Resp:
                status_code = 200
                text = "noi dung that"
                content = b"noi dung that"
            with unittest.mock.patch("requests.get", return_value=_Resp()):
                r = MN._lay("https://www.mql5.com/en/code/1")
            self.assertEqual(r, "noi dung that")
            self.assertEqual(goi["bat"], 0, "thanh cong ngay lan dau ma van bat dns_vuot")
        finally:
            self.DV.bat = goc_bat

    def test_that_bai_lan_dau_thi_THU_LAI_voi_dns_vuot(self):
        self.DV.BAN_DO.clear()
        self.DV.BAN_DO["www.mql5.com"] = "203.29.60.247"

        class _Resp:
            status_code = 200
            text = "thu hai thanh cong"
            content = b"thu hai thanh cong"

        goi = {"n": 0}

        def _get(*a, **k):
            goi["n"] += 1
            if goi["n"] == 1:
                raise ConnectionError("gia lap DNS bi dau doc")
            return _Resp()

        with unittest.mock.patch("requests.get", side_effect=_get):
            r = MN._lay("https://www.mql5.com/en/code/1")
        self.assertEqual(r, "thu hai thanh cong")
        self.assertEqual(goi["n"], 2, "phai thu lai dung mot lan nua voi dns_vuot")

    def test_url_khong_trong_ban_do_thi_khong_thu_lai(self):
        """Domain la khong trong `BAN_DO` cua dns_vuot - that bai la vinh vien,
        khong co gi de bat, nen `_lay` phai tra None ngay chu khong lap."""
        self.DV.BAN_DO.clear()   # rong: khong domain nao duoc coi la "co the vuot"
        goi = {"n": 0}

        def _get(*a, **k):
            goi["n"] += 1
            raise ConnectionError("hong that, khong lien quan DNS")

        with unittest.mock.patch("requests.get", side_effect=_get):
            r = MN._lay("https://example.com/x")
        self.assertIsNone(r)
        self.assertEqual(goi["n"], 1, "domain ngoai BAN_DO thi khong duoc thu lai")


class ThuHoiSaiLoai(unittest.TestCase):
    """`thu_hoi_sai_loai` - sua cac ban `noi_dung` da luu TRANG LANDING thay vi
    FILE MA, cho cac dia chi ma `_doc_dinh_tuyen` da tung roi qua truoc khi co
    sua DNS hai tang o `_lay` (xem chu thich cua ham nay o nhan/ma_nguon.py)."""

    def setUp(self):
        self._db = SO.DB
        self._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(self._tmp.name) / "n.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db
        self._tmp.cleanup()

    def _chen_ban_sai_loai(self, url="https://www.mql5.com/en/code/74894",
                           ket_boc=None):
        with SO.ket_noi() as cn:
            cn.execute(
                "INSERT INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
                "so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc,ket_boc) "
                "VALUES(NULL,?,?,?,?,?,?,?,?,0,?)",
                (SO.van_tay("nd", url), url, "khac", "trinh_duyet",
                 3000, 3000, "Home Market Forum CodeBase " * 100,
                 SO.bay_gio(), ket_boc))

    def test_sua_duoc_khi_tai_lai_ra_ma_that(self):
        self._chen_ban_sai_loai()
        with unittest.mock.patch.object(
                MN, "tai_ma_nguon",
                return_value={"noi_dung": EA_THAT, "so_byte": len(EA_THAT)}):
            bao = MN.thu_hoi_sai_loai(gioi_han=5)
        self.assertEqual(bao["sua_duoc"], 1)
        row = SO.mot("SELECT kieu, cach, van_ban FROM noi_dung "
                     "WHERE url='https://www.mql5.com/en/code/74894'")
        self.assertEqual(row["kieu"], "ma_nguon")
        self.assertEqual(row["cach"], "mql5_download")
        self.assertTrue(MN.co_dau_hieu_ma_that(row["van_ban"]))

    def test_sua_duoc_ngay_ca_khi_ma_that_khong_co_marker_dat_lenh(self):
        """Do that 13/09: mql5.com/en/code/17996 la mot SCRIPT dep-doi-tuong
        (khong OnTick/OrderSend) nhung VAN LA MA THAT 1.390 ky tu, khong phai
        landing page. Ban dau ham nay doi hoi ca `co_dau_hieu_ma_that` tren
        KET QUA TAI VE -> tu choi oan chinh nhung file no vua sua thanh cong."""
        self._chen_ban_sai_loai()
        ma_khong_dat_lenh = "void OnStart(){ ObjectsDeleteAll(0, -1, OBJ_TREND); }"
        self.assertFalse(MN.co_dau_hieu_ma_that(ma_khong_dat_lenh))
        with unittest.mock.patch.object(
                MN, "tai_ma_nguon",
                return_value={"noi_dung": ma_khong_dat_lenh,
                             "so_byte": len(ma_khong_dat_lenh)}):
            bao = MN.thu_hoi_sai_loai(gioi_han=5)
        self.assertEqual(bao["sua_duoc"], 1, "tu choi oan script that khong co marker")

    def test_ban_da_la_ma_that_thi_KHONG_goi_mang_lai(self):
        self._chen_ban_sai_loai()
        with SO.ket_noi() as cn:
            cn.execute("UPDATE noi_dung SET van_ban=? WHERE url=?",
                      (EA_THAT, "https://www.mql5.com/en/code/74894"))
        with unittest.mock.patch.object(MN, "tai_ma_nguon") as m:
            bao = MN.thu_hoi_sai_loai(gioi_han=5)
        m.assert_not_called()
        self.assertEqual(bao["khop_mau"], 0)

    def test_bo_cuoc_sau_TRAN_lan_that_bai_lien_tiep(self):
        """DUONG RA SONG ma tai van hong -> moi duoc dem la mot lan bo cuoc.

        `_duong_ra_song` phai bi GIA LAP o day. Ban dau bai nay khong gia lap
        no, va the la mot bai kiem don vi bong phu thuoc vao mang that: no do
        ngay khi mql5 dang bop toc do, bao `ket_boc is None`. Mot bai kiem
        don vi phai xanh ke ca khi rut day mang.
        """
        self._chen_ban_sai_loai()
        with unittest.mock.patch.object(MN, "_duong_ra_song", return_value=True),              unittest.mock.patch.object(MN, "tai_ma_nguon", return_value=None):
            for _ in range(MN.TRAN_THU_LAI_SAI_LOAI):
                MN.thu_hoi_sai_loai(gioi_han=5)
            row = SO.mot("SELECT ket_boc FROM noi_dung "
                         "WHERE url='https://www.mql5.com/en/code/74894'")
            self.assertIn(f"sai_loai:{MN.TRAN_THU_LAI_SAI_LOAI}", row["ket_boc"])
            # Mot vong nua: khong duoc goi mang them, da bo cuoc voi dia chi nay.
            with unittest.mock.patch.object(MN, "tai_ma_nguon") as m2:
                MN.thu_hoi_sai_loai(gioi_han=5)
            m2.assert_not_called()

    def test_MANG_HONG_khong_duoc_dot_han_muc_thu_lai(self):
        """Chieu nguoc lai cua bai tren, va la bai hoc dat nhat ngay 13/09.

        Cloudflare WARP chan mql5 ca buoi. Bo thu hoi chay 4 me, moi lan hong
        lai cong mot vach, va **29 URL hoan toan tot bi loai VINH VIEN**. Tat
        WARP thi chinh nhung trang do tra 200 voi 62.851 ky tu.

        Nen: hong vi DUONG RA thi khong duoc dem.
        """
        self._chen_ban_sai_loai()
        with unittest.mock.patch.object(MN, "_duong_ra_song", return_value=False),              unittest.mock.patch.object(MN, "tai_ma_nguon", return_value=None):
            for _ in range(MN.TRAN_THU_LAI_SAI_LOAI + 2):
                MN.thu_hoi_sai_loai(gioi_han=5)
        row = SO.mot("SELECT ket_boc FROM noi_dung "
                     "WHERE url='https://www.mql5.com/en/code/74894'")
        self.assertIsNone(
            row["ket_boc"],
            "mang hong ma van cong vach bo cuoc - mot su co tam thoi se loai "
            "vinh vien ca mot lop nguon")


if __name__ == "__main__":
    unittest.main(verbosity=2)
