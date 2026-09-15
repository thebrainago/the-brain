# -*- coding: utf-8 -*-
"""KHAU BOC TACH THEO LAN — `phan_loai_ma` · `doc_chi_bao` · `loc_co_che`.

Ba module ra doi 05/09/2026 de sua MOT cho: khau boc bao "70%" trong khi con
so that la 36 file .mq5 tren 113 da chay, va **190 file chi bao chua bao gio
duoc dua vao khau boc**. Ba bai kiem lon o day, moi bai gac mot loi da sap:

  1. Mot file chi bao KHONG duoc doc thanh chien luoc, va mot file quan ly lenh
     KHONG duoc dem la "boc that bai". Sai lan la nguon cua ca con so 70% sai.
  2. `chua_do` khong duoc lan thanh `0`. Quota API ve 0 d lam ca me 20 file chay
     het 2 giay va bao "0/20 file ra co che" - doc y het mot ket qua am that.
  3. Loai mot co che vi no suy bien tren MOT tai san la nem mat co che that.
     Chi loai khi suy bien tren TAT CA tai san do duoc.
"""
import unittest

import numpy as np
import pandas as pd

from nhan import doc_chi_bao as DC
from nhan import loc_co_che as LCC
from nhan import phan_loai_ma as PL

# --------------------------------------------------------------- MA GIA LAP
CHI_BAO = """
#property indicator_chart_window
#property indicator_buffers 2
double ExtUp[], ExtDn[];
int OnInit(){ SetIndexBuffer(0, ExtUp); SetIndexBuffer(1, ExtDn); return 0; }
int OnCalculate(const int rates_total, const int prev, const double &close[]){
   int h = iRSI(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE);
   double rsi[]; CopyBuffer(h, 0, 0, rates_total, rsi);
   for(int i = prev; i < rates_total; i++){
      if(rsi[i] < 30.0) ExtUp[i] = close[i];
      if(rsi[i] > 70.0) ExtDn[i] = close[i];
   }
   return rates_total;
}
"""

CHIEN_LUOC = """
#property version "1.00"
#include <Trade\\Trade.mqh>
CTrade trade;
void OnTick(){
   int h = iRSI(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE);
   double rsi[]; CopyBuffer(h, 0, 0, 3, rsi);
   if(rsi[1] < 30.0 && close[1] > ma200)
      trade.Buy(0.10);
}
"""

QUAN_TRI = """
#property version "1.00"
#include <Trade\\Trade.mqh>
CTrade trade;
input double InpTrailingStart = 20;
input double InpGridStep      = 30;
input double InpLotMultiplier = 1.6;
void OnTick(){
   // khong co dieu kien vao nao - chi quan ly cai da co
   TrailingStop();
   if(TongLo() > InpMaxLoss) CloseAllPositions();
   if(GiaCachXa(InpGridStep)) trade.Buy(LotTiepTheo() * InpLotMultiplier);
}
"""

TIEN_ICH = """
#property version "1.00"
void OnChartEvent(const int id, const long &l, const double &d, const string &s){
   ObjectCreate(0, "nhan", OBJ_LABEL, 0, 0, 0);
   Comment("bang dieu khien");
}
"""


def _df(n: int = 600, hat: int = 7) -> pd.DataFrame:
    r = np.random.default_rng(hat)
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    dong = 100 + np.cumsum(r.normal(0, 1, n))
    mo = np.concatenate(([dong[0]], dong[:-1])) + r.normal(0, 0.3, n)
    bd = np.abs(r.normal(0, 1.2, n)) + 0.2
    return pd.DataFrame({"open": mo,
                         "high": np.maximum(mo, dong) + bd * r.random(n),
                         "low": np.minimum(mo, dong) - bd * r.random(n),
                         "close": dong,
                         "tick_volume": r.lognormal(7.0, 0.6, n)}, index=idx)


class PhanLoaiDungLan(unittest.TestCase):
    """Sai lan = mau so sai = con so "ty le boc" sai."""

    def test_chi_bao_khong_bi_doc_thanh_chien_luoc(self):
        z = PL.phan_loai_mot(CHI_BAO, "thu.mq5")
        self.assertEqual(z["lan"], PL.CHI_BAO)
        # Van thuoc duong 1: chi bao DINH NGHIA tin hieu vao, chi la khong dat lenh.
        self.assertTrue(z["vao_lenh"])
        self.assertFalse(z["quan_tri"])

    def test_ea_co_dieu_kien_vao_la_chien_luoc(self):
        z = PL.phan_loai_mot(CHIEN_LUOC, "thu.mq5")
        self.assertEqual(z["lan"], PL.CHIEN_LUOC)
        self.assertTrue(z["vao_lenh"])

    def test_file_quan_ly_lenh_khong_bi_dem_la_boc_that_bai(self):
        """`Trade_Manager.mq5` tra "LLM tra ve rong" va bi ghi nhu that bai.

        No khong that bai - no khong co tin hieu vao de bat dau, va thuoc ho 2.
        """
        z = PL.phan_loai_mot(QUAN_TRI, "Trade_Manager.mq5")
        self.assertEqual(z["lan"], PL.QUAN_TRI)
        self.assertFalse(z["vao_lenh"])
        self.assertTrue(z["quan_tri"])

    def test_tien_ich_khong_di_duong_nao(self):
        z = PL.phan_loai_mot(TIEN_ICH, "Panel.mq5")
        self.assertEqual(z["lan"], PL.TIEN_ICH)
        self.assertFalse(z["vao_lenh"])
        self.assertFalse(z["quan_tri"])

    def test_mot_dau_hieu_quan_tri_la_chua_du(self):
        """`PositionModify` co trong gan nhu moi EA - mot dau hieu khong noi gi."""
        ma = QUAN_TRI.replace("InpGridStep", "X").replace("InpLotMultiplier", "Y")
        ma = ma.replace("TrailingStop", "DatSL").replace("CloseAllPositions", "Dong")
        z = PL.phan_loai_mot(ma, "mo_ho.mq5")
        self.assertLess(z["so_dau_hieu_quan_tri"], PL.TOI_THIEU_QUAN_TRI)


class VungTinHieuCuaChiBao(unittest.TestCase):

    def test_khoanh_duoc_vung_quanh_cho_gan_buffer(self):
        v = DC.vung_tin_hieu(CHI_BAO)
        self.assertTrue(v, "khong khoanh duoc vung nao trong file chi bao")
        self.assertTrue(any("rsi[i] < 30" in x for x in v),
                        "vung khoanh ra khong chua dieu kien tin hieu")

    def test_ten_buffer_hoc_tu_SetIndexBuffer(self):
        """Bat theo ten bien khai bao, khong theo chuoi 'buf' trong ten.

        Do 05/09: 88/190 file khai buffer nhung dat ten kieu `ExtUp`,
        `HistogramValues` - khong khop mau chu nao.
        """
        self.assertTrue(any("ExtUp[i]" in x for x in DC.vung_tin_hieu(CHI_BAO)))

    def test_file_khong_co_gi_thi_tra_rong(self):
        self.assertEqual(DC.vung_tin_hieu("int OnInit(){ return 0; }"), [])


class ChuaDoKhongDuocThanhKhong(unittest.TestCase):
    """Bai gac ho benh [[ket-luan-am-phai-phan-biet-chua-do]]."""

    def test_loi_quota_ra_chua_do_chu_khong_ra_rong(self):
        from nhan import tri_tue as TT
        cu = TT.hoi_json
        TT.hoi_json = lambda *a, **k: {"loi": "HTTP 403: insufficient user quota"}
        try:
            r = DC._mot({"ten": "x.mq5", "src": CHI_BAO}, "")
        finally:
            TT.hoi_json = cu
        self.assertTrue(r["chua_do"])
        self.assertIn("CHUA DO", r["vi_sao"])

    def test_khong_thu_lai_khi_chua_do(self):
        """Quota het khong tu khoi phuc trong 3 giay - thu lai chi ton thoi gian."""
        from nhan import tri_tue as TT
        dem = {"n": 0}

        def gia(*a, **k):
            dem["n"] += 1
            return {"loi": "HTTP 403: insufficient user quota"}

        cu = TT.hoi_json
        TT.hoi_json = gia
        try:
            DC.mot_file({"ten": "x.mq5", "src": CHI_BAO}, "", so_lan=3)
        finally:
            TT.hoi_json = cu
        self.assertEqual(dem["n"], 1)

    def test_LLM_tra_rong_that_thi_VAN_thu_lai(self):
        """Rong that KHAC chua do: LLM khong tat dinh nen mot lan rong chua
        phai ket luan - va sau khi het luot thu thi DOI MODEL (tang 2)."""
        from nhan import tri_tue as TT
        goi = []

        def gia(*a, **k):
            goi.append(k.get("model") or "")
            return {"json": {"co_che": []}}

        cu = TT.hoi_json
        TT.hoi_json = gia
        try:
            DC.mot_file({"ten": "x.mq5", "src": CHI_BAO}, "", so_lan=3)
        finally:
            TT.hoi_json = cu
        # 3 luot tang 1 + 1 luot tang 2
        self.assertEqual(len(goi), 4)
        self.assertEqual(goi[-1], DC.MODEL_TANG_2)
        self.assertTrue(all(g == DC.MODEL_TANG_1 for g in goi[:3]))

    def test_tat_hai_tang_thi_khong_goi_model_thu_hai(self):
        from nhan import tri_tue as TT
        goi = []

        def gia(*a, **k):
            goi.append(k.get("model") or "")
            return {"json": {"co_che": []}}

        cu = TT.hoi_json
        TT.hoi_json = gia
        try:
            DC.mot_file({"ten": "x.mq5", "src": CHI_BAO}, "", so_lan=2,
                        hai_tang=False)
        finally:
            TT.hoi_json = cu
        self.assertEqual(len(goi), 2)


class LocTinhTruocPheu(unittest.TestCase):

    def test_chi_loai_khi_suy_bien_tren_MOI_tai_san(self):
        """Im lang tren mot chi so My khong phai ban an cho ca co che."""
        from nhan import mau as MAU
        df1, df2 = _df(hat=1), _df(hat=2)
        moc = float(df2["close"].iloc[0])

        def _im_o_df1(df, **_):
            """Vao lenh deu tren df2, im hoan toan tren df1."""
            if abs(float(df["close"].iloc[0]) - moc) > 1e-9:
                return np.zeros(len(df))
            return np.asarray(df.index.day % 3 == 0, dtype=float)

        MAU.MAU["_thu_song_o_df2"] = {"ham": _im_o_df1, "ho": "xu_huong",
                                      "co_che": "thu"}
        try:
            do1 = LCC._do_mot_ma(["_thu_song_o_df2"], df1)
            do2 = LCC._do_mot_ma(["_thu_song_o_df2"], df2)
        finally:
            MAU.MAU.pop("_thu_song_o_df2", None)
        self.assertLess(do1["_thu_song_o_df2"]["ty_le"], LCC.TY_LE_IT)
        self.assertGreater(do2["_thu_song_o_df2"]["ty_le"], LCC.TY_LE_IT)

    def test_van_tay_hanh_vi_gop_hai_ten_cung_mot_chuoi(self):
        a = np.array([0.0, 1.0, 1.0, 0.0, -1.0])
        self.assertEqual(LCC._van_tay_hanh_vi(a), LCC._van_tay_hanh_vi(a.copy()))
        self.assertNotEqual(LCC._van_tay_hanh_vi(a),
                            LCC._van_tay_hanh_vi(np.array([0.0, 1.0, 0.0, 0.0, -1.0])))

    def test_sai_khung_khong_bi_gop_chung_voi_spec_hong(self):
        """Co che theo PHIEN chay tren D1 la SAI KHUNG, khong phai HONG."""
        from nhan import mau as MAU
        self.assertEqual(LCC._nhom_loi(MAU.KhungThieuGio("chi co mot gio")),
                         LCC.SAI_KHUNG)
        self.assertEqual(LCC._nhom_loi(KeyError("'trai'")), LCC.SPEC_HONG)
        self.assertEqual(LCC._nhom_loi(KeyError("du lieu khong co cot 'bid'")),
                         LCC.THIEU_COT)

    def test_gia_so_voi_hang_so_tuyet_doi_bi_bat(self):
        """`close >= 4428.1` la loi ho gia vang mot thoi diem, khong phai co che."""
        xau = {"ten": "x", "ho": "pha_vo", "chieu": 1, "giu": 1,
               "vao": [{"trai": {"chi_bao": "gia", "cot": "close"},
                        "phep": ">=", "phai": {"hang": 4428.1}}]}
        tot = {"ten": "y", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
               "vao": [{"trai": {"chi_bao": "rsi", "n": 14},
                        "phep": "<", "phai": {"hang": 30}}]}
        self.assertEqual(LCC._hang_so_gia(xau), 4428.1)
        self.assertIsNone(LCC._hang_so_gia(tot))

    def test_nguong_hang_so_khong_bat_nham_nguong_chuan_hoa(self):
        """IBS 0,2 · zscore -2 la nguong da chuan hoa - khong duoc coi la gia."""
        ibs = {"vao": [{"trai": {"chi_bao": "gia", "cot": "close"},
                        "phep": "<", "phai": {"hang": 0.2}}]}
        self.assertIsNone(LCC._hang_so_gia(ibs))


class CongNgoaiVaoKho(unittest.TestCase):
    """`boc_ma_llm.kiem_va_giu` la cong chung cua CA HAI duong boc LLM."""

    def test_ho_chua_khai_pham_vi_thi_bi_tu_choi(self):
        """Me 05/09 dua 61 co che ho `khac` + 1 ho `khong_dien_dat_duoc` vao kho.

        `doc_ma` da cam ho `khac` tu 01/09 voi ly do da viet: khong khai duoc
        pham vi thi khong co co so doi hoi phep thu phan chung. Duong LLM khong
        ap luat do nen bai `test_moi_ho_trong_thu_vien_mau_deu_da_khai_pham_vi` do.
        """
        from nhan import boc_ma_llm as BM
        ve = [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<",
               "phai": {"hang": 30}}]
        giu, ho = BM.kiem_va_giu([
            {"ten": "a", "ho": "khac", "chieu": 1, "giu": 1, "vao": ve},
            {"ten": "b", "ho": "khong_dien_dat_duoc", "chieu": 1, "giu": 1, "vao": ve},
            {"ten": "c", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1, "vao": ve},
        ])
        self.assertEqual([g["ten"] for g in giu], ["c"])
        self.assertEqual(len(ho), 2)

    def test_danh_sach_chuoi_khong_lam_sap_ca_me(self):
        """LLM doi khi tra `co_che: ["mua khi rsi < 30"]` - danh sach CHUOI."""
        from nhan import boc_ma_llm as BM
        giu, ho = BM.kiem_va_giu(["mua khi rsi < 30"])
        self.assertEqual(giu, [])
        self.assertEqual(len(ho), 1)

    def test_loi_goi_ra_chua_do_o_ca_duong_EA(self):
        from nhan import boc_ma_llm as BM
        from nhan import tri_tue as TT
        cu = TT.hoi_json
        TT.hoi_json = lambda *a, **k: {"loi": "HTTP 403: insufficient user quota"}
        try:
            r = BM._mot({"ten": "x.mq5", "src": CHIEN_LUOC}, "")
        finally:
            TT.hoi_json = cu
        self.assertTrue(r["chua_do"])


class AnhXaNutVanBangLLM(unittest.TestCase):
    """`quan_tri_llm` — LLM chi duoc CHON nut, khong duoc tao nut hay tao so."""

    MA = """
input double InpStrategy1GridStepPct = 0.34;
input double InpLockProfitPoints     = 50;
input double InpTrailingStopDist     = 200;
input int    InpMagic                = 12345;
"""

    def _chay(self, tra):
        from nhan import quan_tri_llm as QL
        from nhan import tri_tue as TT
        cu = TT.hoi_json
        TT.hoi_json = lambda *a, **k: {"json": {"anh_xa": tra}}
        try:
            return QL.anh_xa_mot(self.MA, "thu.mq5")
        finally:
            TT.hoi_json = cu

    def test_don_vi_lech_thi_TU_CHOI(self):
        """Loi da sap 05/09: `...Pct` (phan tram) bi gan vao `buoc` (pip).

        Anh xa dung ten nhung sai don vi van chay ra so - va so do vo nghia.
        """
        r = self._chay({"InpStrategy1GridStepPct": {"nut": "buoc",
                                                    "don_vi": "phan_tram"}})
        self.assertNotIn("buoc", r)
        self.assertTrue(r.get("_bo_vi_don_vi"))

    def test_don_vi_khop_thi_nhan(self):
        r = self._chay({"InpTrailingStopDist": {"nut": "trailing_buoc",
                                                "don_vi": "diem"}})
        self.assertEqual(r["trailing_buoc"][0], 200.0)
        self.assertEqual(r["trailing_buoc"][1], "InpTrailingStopDist")

    def test_khong_duoc_tao_nut_moi(self):
        r = self._chay({"InpMagic": {"nut": "nut_tu_bia", "don_vi": "so_lan"}})
        self.assertEqual({k: v for k, v in r.items() if not k.startswith("_")}, {})

    def test_khong_duoc_bia_ten_input(self):
        r = self._chay({"KhongHeCoInputNay": {"nut": "tp", "don_vi": "pip"}})
        self.assertNotIn("tp", r)

    def test_gia_tri_lay_tu_MA_NGUON_khong_lay_tu_loi_mo_hinh(self):
        """Mo hinh noi 999 nhung ma nguon ghi 50 -> phai lay 50."""
        r = self._chay({"InpLockProfitPoints": {"nut": "tp", "don_vi": "diem",
                                                "gia_tri": 999}})
        self.assertEqual(r["tp"][0], 50.0)

    def test_chua_do_khong_thanh_rong(self):
        from nhan import quan_tri_llm as QL
        from nhan import tri_tue as TT
        cu = TT.hoi_json
        TT.hoi_json = lambda *a, **k: {"loi": "HTTP 403: quota"}
        try:
            r = QL.anh_xa_mot(self.MA, "thu.mq5")
        finally:
            TT.hoi_json = cu
        self.assertIn("_chua_do", r)


class XetTienIchTheoNhuCauDAKHAI(unittest.TestCase):
    """`tien_ich_xet` — LLM chi duoc GAN vao nhu cau da khai, khong nghi ra moi.

    Cung ly do voi `san_cong_cu`: *"tim truoc roi moi nghi ra ly do can no thi
    lan nao cung 'tim thay thu huu ich', va do la mot dang tu lua minh"*.
    """

    def _chay(self, tra):
        from nhan import tien_ich_xet as TI
        from nhan import tri_tue as TT
        cu = TT.hoi_json
        TT.hoi_json = lambda *a, **k: {"json": tra}
        try:
            return TI.xet_mot("void OnTick(){}", "thu.mq5")
        finally:
            TT.hoi_json = cu

    def test_nhu_cau_tu_bia_bi_bo(self):
        r = self._chay({"nhu_cau": "toi_uu_hoa_vu_tru", "muc_do": "cao"})
        self.assertIsNone(r["nhu_cau"])

    def test_nhu_cau_da_khai_thi_giu(self):
        r = self._chay({"nhu_cau": "do_chi_phi_that", "muc_do": "cao",
                        "lam_gi": "ghi spread that ra file"})
        self.assertEqual(r["nhu_cau"], "do_chi_phi_that")

    def test_chua_do_khong_thanh_khong_hop(self):
        from nhan import tien_ich_xet as TI
        from nhan import tri_tue as TT
        cu = TT.hoi_json
        TT.hoi_json = lambda *a, **k: {"loi": "HTTP 403: quota"}
        try:
            r = TI.xet_mot("void OnTick(){}", "thu.mq5")
        finally:
            TT.hoi_json = cu
        self.assertTrue(r["chua_do"])
        self.assertNotIn("nhu_cau", r)


if __name__ == "__main__":
    unittest.main()


# ===== LAN THU BA CUNG MOT HO LOI: bo do luat chi doc duoc mot vai thu tieng
def test_bo_do_luat_phai_THAY_duoc_luat_o_MOI_thu_tieng():
    """Cung MOT cau luat, dich sang 10 thu tieng - bo do phai thay het.

    Do 15/09/2026 TRUOC khi sua: Anh 5 · Viet 4 · **Nga 0 · Nhat 0 · Thai 0**.
    Va no bat duoc dung luc: seeker vua duoc noi vao sau dien dan quoc gia
    (mql5 Nga, note.com Nhat, thaiforexschool). Neu khong sua thi ta vua xay
    mot day chuyen THU VE ROI VUT DI trong im lang.

    Hai lan truoc cung ho: bo loc viet cho van xuoi Anh cham ma nguon 0 diem
    (03/09), roi cham tieng Viet CO DAU 0 diem (04/09).
    """
    from nhan import boc_llm as BL
    cau = {
        "Anh": "Buy when RSI(14) crosses below 30 and close is above the 200 "
               "EMA. Exit after 5 bars. Stop loss 2 ATR.",
        "Viet": "Mua khi RSI(14) cắt xuống dưới 30 và giá đóng cửa trên "
                "EMA200. Thoát sau 5 nến. Cắt lỗ 2 ATR.",
        "Nga": "Покупаем когда RSI(14) опускается ниже 30 и цена закрытия "
               "выше EMA200. Выход через 5 баров. Стоп 2 ATR.",
        "Nhat": "RSI(14)が30を下回り、終値がEMA200より上のときに買う。5本後に決済。損切りは2ATR。",
        "Trung": "当RSI(14)下穿30且收盘价高于EMA200时买入，持有5根K线后止盈，止损2ATR。",
        "Han": "RSI(14)가 30 아래로 내려가고 종가가 EMA200 위에 있으면 매수. 손절 2ATR.",
        "Thai": "ซื้อเมื่อ RSI(14) ต่ำกว่า 30 และราคาปิดอยู่เหนือ EMA200 ตัดขาดทุน 2ATR",
        "TayBanNha": "Comprar cuando RSI(14) cruza por debajo de 30 y el "
                     "cierre está sobre la EMA200. Stop de pérdida 2 ATR.",
        "Duc": "Kaufen wenn RSI(14) unter 30 fällt und der Schlusskurs über "
               "der EMA200 liegt.",
        "Indo": "Beli ketika RSI(14) turun di bawah 30 dan harga penutupan di "
                "atas EMA200.",
    }
    truot = [k for k, v in cau.items()
             if BL._diem_luat(v) < BL.DIEM_TOI_THIEU]
    assert not truot, (
        "bo do luat MU voi: %s - day la thu tieng seeker DANG thu ve, tai lieu "
        "cua chung se bi vut o cong boc ma khong ai thay" % ", ".join(truot))


def test_bo_do_luat_van_BO_van_ban_khong_phai_luat():
    """Chieu nguoc lai. Mot bo do bat tat ca thi cung vo dung nhu bo do mu."""
    from nhan import boc_llm as BL
    rac = [
        "Ngan hang trung uong chau Au giu nguyen lai suat trong cuoc hop thang "
        "nay, theo Reuters. Thi truong phan ung tich cuc.",
        "Cho dau vao chao, dun nong roi cho hanh vao phi thom trong 5 phut.",
        "Đăng ký ngay hôm nay để nhận tín hiệu miễn phí từ chuyên gia hàng đầu!",
        "Центральный банк оставил ставку без изменений на заседании в этом месяце.",
    ]
    bat_oan = [s for s in rac if BL._diem_luat(s) >= BL.DIEM_TOI_THIEU]
    assert not bat_oan, "bat oan %d van ban khong phai luat" % len(bat_oan)


def test_mau_KHONG_PHU_THUOC_NGON_NGU_bat_duoc_thu_tieng_chua_liet_ke():
    """Ten chi bao luon viet bang chu Latin, ke ca trong bai tieng Nhat.

    Nho vay mot bai tieng Ba Lan / Hy Lap / Do Thai - nhung thu tieng chua ai
    liet ke - van qua duoc cong neu no THAT SU noi ve mot luat.
    """
    from nhan import boc_llm as BL
    # Tieng Ba Lan, khong co trong danh sach tu khoa nao
    s = "Kupuj gdy RSI(14) spadnie poniżej 30, a cena zamknięcia jest powyżej EMA200."
    assert BL._diem_luat(s) >= BL.DIEM_TOI_THIEU, (
        "mau khong phu thuoc ngon ngu khong hoat dong")
