# -*- coding: utf-8 -*-
"""Test cho `nhan/doc_ma.py` - doc ma nguon thanh NHIEU khai bao co che.

Moc doi chieu van la SONIC R. Diem khac voi `test_thu_hoi_thanh_phan`: o do ta
hoi "co lay lai duoc cac manh khong", o day hoi "co ghep duoc thanh khai bao
CHAY DUOC khong".
"""
from __future__ import annotations

import unittest

from nhan import doc_ma as DM
from nhan import ngu_phap as NP

PINE = """//@version=3
strategy("Sonic R", overlay=true)
HiLoLen = input(34, minval=2)
EMA     = input(89, minval=2)
Look    = input(55, minval=2)
pacL = ema(low,HiLoLen)
pacH = ema(high,HiLoLen)
ma   = ema(close,EMA)
dcHi = highest(high, Look)
rsiv = rsi(close, 14)
longC  = pacH > ma
shortC = pacL < ma
brk    = close > dcHi[1]
qua    = rsiv < 30
he_so  = input(1.5)
sai    = close > he_so
"""

CHEO = """//@version=5
fast = ta.ema(close, 20)
slow = ta.ema(close, 50)
up = ta.crossover(fast, slow)
dn = ta.crossunder(fast, slow)
"""


class MotFileRaNhieuKieuDanh(unittest.TestCase):
    """Doi hoi trung tam cua chu du an: mot script = nhieu kieu danh."""

    def setUp(self):
        self.ds = DM.doc_ma(PINE, "pine", nguon="thu", tien_to="t")
        self.dk = [s["vao"][0] for s in self.ds]

    def test_ra_nhieu_hon_mot_khai_bao(self):
        self.assertGreaterEqual(len(self.ds), 3, "mot file phai ra nhieu kieu danh")

    def test_moi_khai_bao_deu_qua_kiem_cu_phap(self):
        for s in self.ds:
            self.assertEqual(NP.kiem_khai_bao(s), [], s["ten"])

    def test_khong_sinh_ho_khac(self):
        """Ho `khac` khong khai duoc pham vi -> khong duoc vao thu vien."""
        self.assertNotIn("khac", [s["ho"] for s in self.ds])

    def test_giu_do_tre_cua_pha_vo(self):
        """`close > dcHi[1]` phai giu do tre.

        Cat bo `[1]` bien dieu kien thanh `close > highest(high,55)`, ma
        `highest` gom ca nen hien tai nen dieu kien do KHONG BAO GIO dung - cong
        bao 'kich hoat 0,000%'. Cung ho loi voi quy tac `Open[i+1]`.
        """
        co_tre = [d for d in self.dk
                  if (d.get("phai") or {}).get("chi_bao") == "tre"]
        self.assertTrue(co_tre, "mat do tre cua dieu kien pha vo")
        self.assertEqual(co_tre[0]["phai"]["n"], 1)

    def test_bo_so_sanh_lech_thang_do(self):
        """`close > he_so` voi `he_so = input(1.5)` la rac, phai bi bo.

        Do that tren Sonic R: khong chan thi sinh ra `open < 2` va
        `ema34_high < 1.5`, ca hai kich hoat 100% so bar.
        """
        for d in self.dk:
            if "hang" in (d.get("phai") or {}):
                self.assertNotIn((d.get("trai") or {}).get("chi_bao"),
                                 DM._THANG_GIA, str(d))

    def test_giu_nguon_gia_cua_tung_duong(self):
        """Dai PAC la EMA34 tren high VA tren low - hai duong khac nhau."""
        cot = {(d.get("trai") or {}).get("cot") for d in self.dk}
        self.assertTrue({"high", "low"} & cot)

    def test_nguong_rsi_giu_duoc_vi_rsi_co_thang_do_bi_chan(self):
        rsi = [d for d in self.dk
               if (d.get("trai") or {}).get("chi_bao") == "rsi"]
        self.assertTrue(rsi)
        self.assertEqual(rsi[0]["phai"], {"hang": 30.0})


class Cheo(unittest.TestCase):
    def test_crossover_thanh_phep_cheo_len(self):
        ds = DM.doc_ma(CHEO, "pine", tien_to="c")
        phep = {s["vao"][0]["phep"] for s in ds}
        self.assertIn("cheo_len", phep)
        self.assertIn("cheo_xuong", phep)

    def test_hai_ve_deu_la_ema_dung_chu_ky(self):
        ds = DM.doc_ma(CHEO, "pine", tien_to="c")
        d = ds[0]["vao"][0]
        self.assertEqual(d["trai"], {"chi_bao": "ema", "n": 20, "cot": "close"})
        self.assertEqual(d["phai"], {"chi_bao": "ema", "n": 50, "cot": "close"})


class KhongNo(unittest.TestCase):
    def test_van_ban_rong(self):
        self.assertEqual(DM.doc_ma(""), [])

    def test_van_xuoi_thuan_khong_ra_gi(self):
        self.assertEqual(DM.doc_ma("Mua khi RSI thap va ban khi RSI cao."), [])

    def test_khong_chay_ma(self):
        """Bo doc chi doc van ban. Ma co hai khong gay tac dung phu nao."""
        doc = PINE + "\nimport os\nos.system('echo x')\n"
        self.assertTrue(DM.doc_ma(doc, "pine", tien_to="t"))

    def test_ten_khong_co_ky_tu_pha_LIKE(self):
        """Ten di vao `gia_thuyet.ma` roi bi tim lai bang LIKE."""
        for s in DM.doc_ma(PINE, "pine", tien_to="t"):
            self.assertNotIn("%", s["ten"])
            self.assertNotIn(".", s["ten"])



class MienQuetCuaTacGia(unittest.TestCase):
    """Lay mien quet tu `input(...)` cua chinh tac giả - khong chay ma cua ho."""

    def test_doc_duoc_input_pine_kem_minval(self):
        khai = DM.rut_input(PINE)
        self.assertEqual(khai["HiLoLen"]["gia_tri"], 34.0)
        self.assertEqual(khai["HiLoLen"]["min"], 2.0)

    def test_doc_duoc_input_mql(self):
        mql = "input int    InpPeriod   = 14;  // chu ky\ninput double InpRisk = 2.0;\n"
        khai = DM.rut_input(mql)
        self.assertEqual(khai["InpPeriod"]["gia_tri"], 14.0)
        self.assertEqual(khai["InpRisk"]["gia_tri"], 2.0)

    def test_luoi_neo_quanh_gia_tri_tac_gia_dung(self):
        self.assertEqual(DM._luoi_quanh(34, None), [17, 34, 68])

    def test_luoi_bi_chan_trong_mien_tac_gia_khai(self):
        self.assertEqual(DM._luoi_quanh(10, {"min": 8.0, "max": 12.0}), [8, 10, 12])

    def test_hai_ve_cung_chi_bao_khong_ghi_de_nhau(self):
        """`ema34 < ema89`: khoa theo ten chi bao thi mat mot nua dieu kien."""
        ds = DM.doc_ma(PINE, "pine", tien_to="t")
        hai = [s for s in ds if len(s["luoi_goc"]) == 2]
        self.assertTrue(hai, "dieu kien hai ve deu co chu ky phai giu ca hai")

    def test_moi_khai_bao_deu_co_luoi_goc(self):
        for s in DM.doc_ma(PINE, "pine", tien_to="t"):
            self.assertIn("luoi_goc", s)

if __name__ == "__main__":
    unittest.main()


CHIEN_LUOC = """//@version=4
strategy("BB + RSI", overlay=true)
length = input(20)
mult = input(2.0)
RSIlen = input(6)
oversold = 30
price = close
basis = sma(price, length)
dev = mult * stdev(price, length)
BBlower = basis - dev
vrsi = rsi(price, RSIlen)
if (crossover(vrsi, oversold) and crossover(price, BBlower))
    strategy.entry("L", strategy.long)
if (crossunder(price, basis))
    strategy.entry("S", strategy.short)
"""


class DocChienLuocThat(unittest.TestCase):
    """Doc CHIEN LUOC, khong nhat manh - vế "phai dung" cua chu du an."""

    def setUp(self):
        self.k = DM.doc_chien_luoc(CHIEN_LUOC, nguon="thu", tien_to="t")
        self.cc = self.k["co_che"]

    def test_ra_dung_hai_co_che_theo_hai_lenh_vao(self):
        self.assertEqual(len(self.cc), 2, self.k["chua_dien_dat_duoc"])

    def test_ghep_DU_hai_dieu_kien_chu_khong_tach_roi(self):
        """Guard co `and` thi phai thanh MOT co che hai dieu kien."""
        mua = [c for c in self.cc if c["chieu"] == 1][0]
        self.assertEqual(len(mua["vao"]), 2)

    def test_chieu_doc_dung_tu_strategy_long_va_short(self):
        self.assertEqual(sorted(c["chieu"] for c in self.cc), [-1, 1])

    def test_dich_dung_dai_bollinger_thanh_tuyen_tinh(self):
        mua = [c for c in self.cc if c["chieu"] == 1][0]
        bb = [d["phai"] for d in mua["vao"]
              if (d["phai"] or {}).get("chi_bao") == "tuyen_tinh"]
        self.assertTrue(bb, "khong dich duoc `basis - dev`")
        self.assertEqual(bb[0]["he_so"], [1.0, -1.0])

    def test_ho_nhin_xuyen_qua_tuyen_tinh(self):
        """`khac` khong khai duoc pham vi nen se bi bo o cua cuoi."""
        for c in self.cc:
            self.assertNotEqual(c["ho"], "khac", c["ten"])

    def test_moi_co_che_qua_kiem_cu_phap(self):
        for c in self.cc:
            self.assertEqual(NP.kiem_khai_bao(c), [], c["ten"])

    def test_CRLF_khong_lam_hong_gi(self):
        """File Pine tai ve dung CRLF; mot ky tu CR tung lam rot ca chien luoc."""
        k = DM.doc_chien_luoc(CHIEN_LUOC.replace("\n", "\r\n"), tien_to="t")
        self.assertEqual(len(k["co_che"]), 2)

    def test_bo_CA_co_che_khi_mot_ve_khong_dich_duoc(self):
        """Bo rieng mot ve lam dieu kien LONG hon ban goc - do la noi doi."""
        xau = CHIEN_LUOC.replace("crossover(vrsi, oversold)", "direction > 0")
        k = DM.doc_chien_luoc(xau, tien_to="t")
        mua = [c for c in k["co_che"] if c["chieu"] == 1]
        self.assertEqual(mua, [], "phai bo ca co che, khong duoc bo rieng ve")

    def test_khong_co_strategy_entry_thi_khong_ra_gi(self):
        self.assertEqual(DM.doc_chien_luoc("x = ema(close, 20)")["co_che"], [])


CO_NHO = """//@version=4
strategy("MA cross state", overlay=true)
fast_ma = ema(close, 10)
slow_ma = ema(close, 30)
direction = na(direction[1]) ? 1 : crossunder(fast_ma, slow_ma) and direction[1] > 0 ? -1 : crossover(fast_ma, slow_ma) and direction[1] < 0 ? 1 : direction[1]
if (direction > 0)
    strategy.entry("L", strategy.long)
"""

CONG_TAC = """//@version=4
strategy("switch", overlay=true)
dung_dai = input(true)
ma_nhanh = ema(close, 10)
ma_cham = ema(close, 50)
muc = dung_dai ? ma_cham : ma_nhanh
if (close > muc)
    strategy.entry("L", strategy.long)
"""


class DocBienCoNho(unittest.TestCase):
    """Bien TU THAM CHIEU viet bang tam nguyen long -> `trang_thai_lat`."""

    def setUp(self):
        self.cc = DM.doc_chien_luoc(CO_NHO, tien_to="t")["co_che"]

    def test_dich_duoc_thanh_trang_thai_lat(self):
        self.assertEqual(len(self.cc), 1)
        t = self.cc[0]["vao"][0]["trai"]
        self.assertEqual(t["chi_bao"], "trang_thai_lat")

    def test_nhanh_len_va_xuong_dung_chieu(self):
        t = self.cc[0]["vao"][0]["trai"]
        self.assertEqual(t["len"]["phep"], "cheo_len")
        self.assertEqual(t["xuong"]["phep"], "cheo_xuong")

    def test_BO_ve_tu_tham_chieu_khoi_dieu_kien(self):
        """`and direction[1] > 0` la guard trang thai - `trang_thai_lat` da giu san."""
        t = self.cc[0]["vao"][0]["trai"]
        self.assertNotIn("trang_thai_lat", str(t["len"]["phai"]))
        self.assertEqual(t["len"]["trai"]["chi_bao"], "ema")

    def test_ho_nhin_xuyen_qua_trang_thai(self):
        """`khac` khong khai duoc pham vi nen se bi bo o cua cuoi."""
        self.assertNotEqual(self.cc[0]["ho"], "khac")

    def test_qua_kiem_cu_phap(self):
        self.assertEqual(NP.kiem_khai_bao(self.cc[0]), [])

    def test_khong_tu_tham_chieu_thi_khong_thanh_trang_thai(self):
        self.assertIsNone(DM._trang_thai_tu_tam_nguyen(
            "x", "a > b ? 1 : -1", 10 ** 6, [], []))


class CongTacCauHinh(unittest.TestCase):
    """`x = co_bat ? A : B` voi `co_bat = input(true)` la LUA CHON, khong phai tin hieu."""

    def test_chon_dung_nhanh_theo_mac_dinh_cua_tac_gia(self):
        cc = DM.doc_chien_luoc(CONG_TAC, tien_to="t")["co_che"]
        self.assertEqual(len(cc), 1, "khong chon duoc nhanh cua cong tac")
        self.assertEqual(cc[0]["vao"][0]["phai"]["n"], 50)

    def test_input_false_thi_chon_nhanh_kia(self):
        cc = DM.doc_chien_luoc(CONG_TAC.replace("input(true)", "input(false)"),
                               tien_to="t")["co_che"]
        self.assertEqual(cc[0]["vao"][0]["phai"]["n"], 10)


# ---------------------------------------------------------------------------
# MQL5 KIEU C - nut that do duoc ngay 18/09/2026
# ---------------------------------------------------------------------------
# `mau_thu/do_moc.py` do duoc: 10 file .mq5 mau -> 22 diem vao lenh -> 0 co che.
# Nguyen nhan khong phai ngu phap thieu toan hang, ma la bo doc KHONG NHIN THAY
# cac bien: MQL5 khai bao co KIEU o dau dong (`bool x=...`, `double y=...`) nen
# `_GAN_BOOL`/`_GAN` - von viet cho Pine (`x = ...`) - truot sach. Bien khong
# vao bang thi `_no_dieu_kien` gap `downbreakout` la mot dinh danh tran, khong
# truy nguoc duoc, va BO CA CO CHE.
#
# Bon lop trong mot: khai bao co kieu · toan tu `&&`/`||`/`!` · truong cua
# MqlRates (`rates[0].close`) · `CopyBuffer` noi mot mang voi handle chi bao.

MQL_KHAI_BAO_CO_KIEU = """
input int InpMaChuKy = 50;
int MaHandle = iMA(NULL,0,InpMaChuKy,0,MODE_SMA,PRICE_CLOSE);
void OnTick()
  {
   double MaValues[];
   MqlRates current[];
   ArraySetAsSeries(MaValues,true);
   ArraySetAsSeries(current,true);
   CopyRates(_Symbol,_Period,0,3,current);
   CopyBuffer(MaHandle,0,0,10,MaValues);
   bool trenMa = current[0].close > MaValues[0];
   double rsiv = iRSI(_Symbol,_Period,14,PRICE_CLOSE);
   bool quaBan = rsiv < 30;
   if(trenMa && quaBan)
     {
      CTrade trade;
      trade.Buy(0.1,_Symbol);
     }
  }
"""


class KhaiBaoCoKieuCuaMQL5(unittest.TestCase):
    """MQL5 khai bao bien co KIEU o dau dong. Khong bat thi ca chuoi dut."""

    def setUp(self):
        self.vb = DM._chuan_hoa(MQL_KHAI_BAO_CO_KIEU)

    def test_bien_bool_co_kieu_vao_duoc_bang(self):
        ten = {t[1] for t in DM._bang_bool(self.vb)}
        self.assertIn("trenMa", ten, "`bool trenMa = ...` phai vao bang bool")
        self.assertIn("quaBan", ten)

    def test_bo_dau_cham_phay_cuoi_bieu_thuc(self):
        """`x = a > b;` con dau `;` thi khong phep so sanh nao fullmatch duoc."""
        for _, ten, bt in DM._bang_bool(self.vb):
            self.assertFalse(bt.rstrip().endswith(";"),
                             f"{ten} con dau ; -> moi regex so sanh deu truot")

    def test_bien_chi_bao_co_kieu_vao_duoc_bang_ky_hieu(self):
        """`double rsiv = iRSI(...)` - khai bao co kieu, van phai ra chi bao."""
        bang = {t[1]: t[2] for t in DM._bang_ky_hieu(self.vb)}
        self.assertIn("rsiv", bang)
        self.assertEqual(bang["rsiv"].get("chi_bao"), "rsi")

    def test_input_co_kieu_giai_duoc_chu_ky(self):
        """`iMA(...,InpMaChuKy,...)` - chu ky nam trong mot input MQL5."""
        bang = {t[1]: t[2] for t in DM._bang_ky_hieu(self.vb)}
        self.assertIn("MaHandle", bang)
        self.assertEqual(bang["MaHandle"].get("tham_so"), [50.0])


class ToanTuBooleanKieuC(unittest.TestCase):
    """`&&` `||` `!` - MQL5/Pine v6 dung chung, bo tach chi biet `and`/`or`."""

    def test_tach_va_hieu_dau_va_kieu_c(self):
        self.assertEqual(DM._tach_va("a > b && c < d"), ["a > b", "c < d"])

    def test_tach_va_khong_cat_trong_ngoac(self):
        self.assertEqual(DM._tach_va("(a && b) > c"), ["(a && b) > c"])

    def test_hoac_kieu_c_van_bi_tu_choi(self):
        """`||` khong dien dat duoc bang danh sach VA - phai bao ra, khong nuot."""
        dk, ho = DM._no_dieu_kien("close > 10 || close < 5", 0, [], [])
        self.assertEqual(dk, [], "gap `||` thi khong duoc tra ve dieu kien nao")
        self.assertTrue(ho, "phai bao vao `chua_dien_dat_duoc`")

    def test_phu_dinh_dao_phep_so_sanh(self):
        """`!(rsi < 30)` la `rsi >= 30`. Bo qua dau `!` la doi han y nghia."""
        vb = DM._chuan_hoa(
            "double rsiv = iRSI(_Symbol,_Period,14,PRICE_CLOSE);\n"
            "bool quaBan = rsiv < 30;\n")
        bang_cb, bang_bl = DM._bang_ky_hieu(vb), DM._bang_bool(vb)
        dk, ho = DM._no_dieu_kien("!quaBan", len(vb), bang_cb, bang_bl)
        self.assertEqual(ho, [], "phu dinh mot so sanh don phai dich duoc")
        self.assertEqual(len(dk), 1)
        self.assertEqual(dk[0]["phep"], ">=", "`!(x < 30)` phai thanh `x >= 30`")


class TruongCuaMqlRates(unittest.TestCase):
    """`current[0].close` - dang viet gia pho bien nhat cua MQL5."""

    def setUp(self):
        self.vb = DM._chuan_hoa(MQL_KHAI_BAO_CO_KIEU)
        self.bang = DM._bang_ky_hieu(self.vb)
        self.bl = DM._bang_bool(self.vb)

    def test_truong_gia_doc_duoc(self):
        t = DM._toan_hang("current[0].close", len(self.vb), self.bang, self.bl)
        self.assertEqual(t, {"chi_bao": "gia", "cot": "close"})

    def test_giu_do_tre_cua_chi_so(self):
        """`current[1].high` la nhin lui 1 bar - mat do tre la doi y nghia."""
        t = DM._toan_hang("current[1].high", len(self.vb), self.bang, self.bl)
        self.assertEqual(t, {"chi_bao": "tre",
                             "cua": {"chi_bao": "gia", "cot": "high"}, "n": 1})

    def test_khong_nhan_bua_truong_la(self):
        """`Tradesinfo.initup` la co trang thai cua EA, khong phai gia."""
        self.assertIsNone(
            DM._toan_hang("Tradesinfo.initup", len(self.vb), self.bang, self.bl))


class CopyBufferNoiMangVoiHandle(unittest.TestCase):
    """`CopyBuffer(MaHandle,0,0,10,MaValues)` -> `MaValues[k]` la chi bao do."""

    def setUp(self):
        self.vb = DM._chuan_hoa(MQL_KHAI_BAO_CO_KIEU)
        self.bang = DM._bang_ky_hieu(self.vb)
        self.bl = DM._bang_bool(self.vb)

    def test_mang_dem_thua_ke_chi_bao_cua_handle(self):
        t = DM._toan_hang("MaValues[0]", len(self.vb), self.bang, self.bl)
        self.assertIsNotNone(t, "`MaValues[0]` phai tro ve chinh iMA cua handle")
        self.assertEqual(t.get("chi_bao"), "sma")
        self.assertEqual(t.get("n"), 50)


class MotEAMQL5DayDuRaDuocCoChe(unittest.TestCase):
    """Bai kiem ca chuoi: tu `trade.Buy` nguoc ve hai dieu kien goc."""

    def setUp(self):
        self.d = DM.doc_chien_luoc(MQL_KHAI_BAO_CO_KIEU, nguon="thu")

    def test_tim_thay_diem_vao_lenh(self):
        self.assertEqual(self.d["so_vao_lenh"], 1)

    def test_ra_duoc_co_che(self):
        self.assertTrue(self.d["co_che"], self.d["chua_dien_dat_duoc"])

    def test_giu_du_ca_hai_ve(self):
        """Bo mot ve lam dieu kien LONG hon ban goc - do la noi doi."""
        self.assertEqual(self.d["co_che"][0]["so_dieu_kien"], 2)

    def test_khai_bao_qua_duoc_kiem_cu_phap(self):
        for s in self.d["co_che"]:
            self.assertEqual(NP.kiem_khai_bao(s), [], s["ten"])
