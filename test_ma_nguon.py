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


if __name__ == "__main__":
    unittest.main(verbosity=2)
