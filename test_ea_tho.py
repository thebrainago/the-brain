# -*- coding: utf-8 -*-
"""ea_tho: EA cong khai chay thang tren tester, cham bang tieu chi chu du an, tren doan dong bang.

Khong co MT5 o day: tester la `MayGia` ghi bao cao TONG HOP theo bo cuc `test_bao_cao_mt5.html_mau`.
Cai kiem duoc o day la QUYET DINH cua code (loai EA, ma/khung, cua so, cong, ky luat niem phong, so tay),
khong phai ket qua tester that - bao cao that dau tien tu may nha phai them vao `test_bao_cao_mt5`.
"""
from __future__ import annotations

import json
from datetime import date

import pytest

from nhan import ea_tho as E
from nhan import nc_so_tay as ST
from test_bao_cao_mt5 import EN, html_mau

CHIEN_LUOC = """
#include <Trade/Trade.mqh>
input int    InpFast  = 12;      // chu ky nhanh
input int    InpSlow  = 26;
input double InpStep  = 50.0;
input double InpLots  = 0.1;
input int    InpMagic = 777;
// trade.Sell(0.1) nam trong chu thich - khong phai lenh
CTrade trade;
void Vao(bool mua) { if(mua) trade.Buy(InpLots); else trade.Sell(InpLots); }
void OnTick() { if(iMA(_Symbol,PERIOD_CURRENT,InpFast,0,MODE_SMA,PRICE_CLOSE,0) > 0) Vao(true); }
"""

CHI_NUT_BAM = """
CTrade trade;
void MuaTay() { trade.Buy(0.1); }
void OnChartEvent(const int id, const long &l, const double &d, const string &s)
{ if(id == CHARTEVENT_OBJECT_CLICK) MuaTay(); }
int OnInit() { return INIT_SUCCEEDED; }
void OnTick() { Comment("Panel"); }
"""

CHI_DONG_LENH = """
void OnTick() { for(int i = PositionsTotal() - 1; i >= 0; i--) { trade.PositionClose(PositionGetTicket(i)); } }
"""


def _doan(t0, t1, t2, t3):
    return {"t_dau": t0, "t_xac_nhan": t1, "t_niem_phong": t2, "t_cuoi": t3, "n0": 1,
            "van_tay": "x", "luc": "2026-10-03 00:00:00"}


@pytest.fixture(autouse=True)
def moi_truong(tmp_path, monkeypatch):
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    so_cai = tmp_path / "so_cai"
    so_cai.mkdir()
    dd = _doan("2010-01-01 00:00:00", "2018-01-01 00:00:00", "2021-01-01 00:00:00", "2025-12-31 23:00:00")
    (so_cai / "doan.json").write_text(json.dumps({"EURUSD|H1": dd, "XAUUSD|H1": dd}), encoding="utf-8")
    monkeypatch.setenv("NC_SO_CAI", str(so_cai))
    cfg = tmp_path / "ea_tho.json"
    cfg.write_text(json.dumps({"tu_nap": False}), encoding="utf-8")
    monkeypatch.setenv("EA_THO_CFG", str(cfg))
    monkeypatch.setattr(E, "CHAY_TESTER", None)
    yield


@pytest.fixture
def ea_cl(tmp_path):
    f = tmp_path / "MaCross.mq5"
    f.write_text(CHIEN_LUOC, encoding="utf-8")
    return str(f)


class MayGia:
    """Ghi bao cao tong hop dung cua so cua lenh. `kq(lenh)` tra kwargs cho html_mau; `sua(van)` sua van ban."""

    def __init__(self, tmp_path, kq=None, sua=None, xong=True, log=""):
        self.tmp, self.kq, self.sua, self.xong, self.log = tmp_path, kq or (lambda lenh: {}), sua, xong, log
        self.lenh: list = []

    def __call__(self, lenh, ea, cfg):
        self.lenh.append(lenh)
        if not self.xong:
            return {"xong": False, "loi": "tester chet"}
        cs = lenh["cua_so"]
        kw = dict(ky="%s (%s - %s)" % (lenh["khung"], cs["tu"], cs["den"]))
        kw.update(self.kq(lenh))
        van = html_mau(EN, **kw)
        if self.sua:
            van = self.sua(van)
        f = self.tmp / ("bc%d.htm" % len(self.lenh))
        f.write_text(van, encoding="utf-8")
        return {"xong": True, "bao_cao": str(f), "log": self.log, "giay": 1.5}

    @property
    def lan(self):
        return len(self.lenh)


def dat_tester(monkeypatch, tmp_path, **kw):
    t = MayGia(tmp_path, **kw)
    monkeypatch.setattr(E, "CHAY_TESTER", t)
    return t


def dem(bang, where="1=1"):
    return ST.mot("SELECT COUNT(*) n FROM %s WHERE %s" % (bang, where))["n"]


# ============================================================ PHAN TICH MA
def test_sach_bo_chu_thich_va_noi_dung_chuoi():
    code = E.sach('// trade.Buy(1)\n/* OrderSend( */ string s = "trade.Sell("; x = 1;')
    assert "Buy" not in code and "OrderSend" not in code and "Sell" not in code and "x = 1" in code


def test_phan_loai_chien_luoc_nut_bam_va_cong_cu():
    cl = E.phan_loai(CHIEN_LUOC)
    assert cl["loai"] == "CHIEN_LUOC" and cl["vao"]["vao_tu_dong"] and "Vao" in cl["vao"]["ham_co_vao"]
    nut = E.phan_loai(CHI_NUT_BAM)
    assert nut["loai"] == "TIEN_ICH" and nut["vao"]["vao_chi_qua_nut"], "lenh chi o nut bam khong phai chien luoc"
    dong = E.phan_loai(CHI_DONG_LENH)
    assert dong["loai"] == "TIEN_ICH" and not dong["vao"]["ham_co_vao"]
    chu_thich = E.phan_loai("void OnTick() { /* trade.Buy(1); */ }")
    assert chu_thich["loai"] == "TIEN_ICH"


def test_lenh_vao_trong_phuong_thuc_lop_goi_tu_ontick():
    code = ("class CBot { public: void Run() { trade.BuyStop(0.1, 1.0); } };\nCBot bot;\n"
            "void OnTick() { bot.Run(); }")
    assert E.phan_loai(code)["loai"] == "CHIEN_LUOC"


def test_can_tep_va_canh_bao_phu_thuoc():
    ma = ('#include "Mylib.mqh"\n#include <Trade/Trade.mqh>\n#import "x.dll"\n#import\n'
          'void OnTick() { double v = iCustom(_Symbol, 0, "Ind/Zig", 12); WebRequest("GET", "u", "", 5, a, b, c); '
          'trade.Buy(0.1); }')
    pl = E.phan_loai(ma)
    t = pl["can_tep"]
    assert t["include_cuc_bo"] == ["Mylib.mqh"] and t["icustom"] == ["Ind/Zig"] and t["dll"] == ["x.dll"]
    assert t["web_hoac_socket"] is True
    assert any("WebRequest" in x for x in pl["ly_do"]) and any("include_cuc_bo" in x for x in pl["ly_do"])


def test_include_la_phan_biet_thu_vien_chuan_va_tep_cua_tac_gia():
    """Do 22 EA that: moi `#include <MultiPivots.mqh>` / `<HybridMicrostructure\\...>` deu la tep CUA TAC GIA nhung nam trong
    dau <>; tien kiem cu chi bat dau kep nen chung chi hong luc bien dich (9/16 chien luoc)."""
    ma = ('#include <Trade\\Trade.mqh>\n#include <Trade/SymbolInfo.mqh>\n#include <Arrays\\ArrayObj.mqh>\n'
          '#include <Object.mqh>\n#include <MultiPivots.mqh>\n#include <HybridMicrostructure\\Core.mqh>\n'
          '#include <MultiPivots.mqh>\n// #include <ChuThich.mqh>\n/* cu:\n#include <KhoiChuThich.mqh>\n*/\n'
          'void OnTick(){ trade.Buy(0.1); }')
    t = E.phan_loai(ma)["can_tep"]
    assert t["include_la"] == ["MultiPivots.mqh", "HybridMicrostructure/Core.mqh"], "chuan, chu thich, trung: khong tinh"
    assert t["include_cuc_bo"] == []


def test_tep_thieu_khop_theo_ten_khong_duoi_va_chi_bao_examples_co_san():
    ma = ('#include <MultiPivots.mqh>\n#include "Cuc.mqh"\n'
          'void OnTick(){ iCustom(_Symbol,0,"Examples\\\\ZigZag",12); iCustom(_Symbol,0,"MyInd",1); '
          '// iCustom(_Symbol,0,"DaBo",1)\n trade.Buy(1); }')
    tep = E.can_tep(ma, E.sach(ma))
    assert E.tep_thieu(tep) == ["include_cuc_bo:Cuc.mqh", "include_la:MultiPivots.mqh", "icustom:MyInd"]
    assert E.tep_thieu(tep, ["multipivots", "Cuc.mqh", "MyInd.ex5"]) == []
    assert E.phan_loai(ma)["thieu_tep"] == E.tep_thieu(tep)
    assert E.phan_loai(ma, tep_san=["MultiPivots", "Cuc", "MyInd"])["thieu_tep"] == []


def test_ho_goi_y_can_it_nhat_hai_tu_khoa():
    code = "input double LotMultiplier = 2; input int GridStep = 100; void OnTick() { /*recovery*/ trade.Buy(1); }"
    # 'recovery' nam trong chu thich: chi tinh tu khoa trong ten dinh danh THAT
    ho = E.phan_loai(code)["ho"]
    assert "luoi_hoi_phuc" in ho and ho["luoi_hoi_phuc"] >= 2
    assert "luoi_hoi_phuc" not in E.phan_loai("input int GridStep = 100; void OnTick() { trade.Buy(1); }")["ho"]


def _kho():
    f = E.KHO_JSON
    if not f.exists():
        pytest.skip("khong co reports/ea/kho.json")
    return json.loads(f.read_text(encoding="utf-8-sig"))


def test_phan_loai_tren_12_ea_that_cua_mql5_code_base():
    """Dap an tay (03/10/2026): 5/12 EA tai ve KHONG phai chien luoc - cong cu replay, dong ro, dong ho, giam sat
    spread, bang rui ro bam tay. Bo boc bang regex tung ra 5 co che tu 12 EA vi khong biet dieu nay."""
    ds = _kho()
    kq = {d["ten"].split("]")[-1].strip(): E.phan_loai(d["ma"], d["ten"])["loai"] for d in ds}
    tien_ich = ("Market Replay Tool", "Basket Protective Close", "Server Clock and Daily Reset Hour",
                "Quantora Spread Monitor MT5 - Pro", "Interactive On-Chart Risk Management")
    chien_luoc = ("Session Opening Range Breakout EA", "AAPL cfd - ORB strategy", "Sniper Gold Hybrid Recovery EA",
                  "Chaos Theory Lyapunov Exponent EA", "GDS Renko Zones Demo EA")
    for t in tien_ich:
        ung = [v for k, v in kq.items() if k.startswith(t[:24])]
        assert ung and all(v == "TIEN_ICH" for v in ung), (t, kq)
    for t in chien_luoc:
        ung = [v for k, v in kq.items() if k.startswith(t[:24])]
        assert ung and all(v == "CHIEN_LUOC" for v in ung), (t, kq)
    assert sum(v == "TIEN_ICH" for v in kq.values()) == 5 and len(kq) == 12


# ============================================================ MA / KHUNG
def test_ma_khung_theo_bang_chung_khong_doan_bua():
    pl = E.phan_loai(CHIEN_LUOC, "XAUUSD scalper M15")
    mk = E.chon_ma_khung(pl, CHIEN_LUOC, "XAUUSD scalper M15")
    assert [(u["ma"], u["khung"], u["nguon"]) for u in mk["ung_vien"]] == [("XAUUSD", "M15", "tieu_de")]
    assert mk["mac_dinh"] is False
    mk = E.chon_ma_khung(E.phan_loai(CHIEN_LUOC), CHIEN_LUOC)
    assert mk["mac_dinh"] is True and [u["ma"] for u in mk["ung_vien"]] == ["EURUSD", "XAUUSD"]
    assert all(u["nguon"] == "mac_dinh" for u in mk["ung_vien"]), "khong co bang chung thi phai ghi la doan"


def test_ea_co_phieu_khong_bi_dat_len_eurusd():
    """Lan chay cu dat EA 'AAPL cfd - ORB' len EURUSD. Nay: ma = AAPL, khong co thi BO QUA, khong thay the."""
    pl = E.phan_loai(CHIEN_LUOC, "AAPL cfd - ORB strategy")
    mk = E.chon_ma_khung(pl, CHIEN_LUOC, "AAPL cfd - ORB strategy", co_san=["EURUSD", "XAUUSDM"])
    assert mk["ung_vien"] == [] and mk["thieu_du_lieu"] == ["AAPL"] and mk["mac_dinh"] is False
    mk = E.chon_ma_khung(pl, CHIEN_LUOC, "AAPL cfd - ORB strategy", co_san=["EURUSD", "AAPL.US"])
    assert [u["ma"] for u in mk["ung_vien"]] == ["AAPL.US"]


def test_goi_y_ma_tu_input_chuoi_va_bieu_danh():
    ma = 'input string InpSymbol = "GBPJPY"; void OnTick() { trade.Buy(1); }'
    assert E.goi_y_ma(ma)[0]["ma"] == "GBPJPY" and E.goi_y_ma(ma)[0]["nguon"] == "input"
    assert [g["ma"] for g in E.goi_y_ma("", "Gold breakout and Nasdaq momentum")] == ["XAUUSD", "US100"]
    assert E.goi_y_ma("", "Moving average EA for FX") == []
    assert E.goi_y_ma("", "Goldfinch bot") == [], "'gold' trong 'Goldfinch' khong phai vang"
    assert [g["ma"] for g in E.goi_y_ma("", "EURUSD/GBPUSD hedge")] == ["EURUSD", "GBPUSD"]


def test_khop_ma_chinh_xac_roi_bat_dau_roi_chua():
    cs = ["XM_US100", "US100CASH", "XAUUSDM", "XAUUSD", "EURUSD"]
    assert E.khop_ma("XAUUSD", cs) == "XAUUSD", "trung ten that thi lay ten that, khong lay XAUUSDM"
    assert E.khop_ma("XAUUSD", ["XAUUSDM", "EURUSD"]) == "XAUUSDM"
    assert E.khop_ma("US100", cs) == "US100CASH", "bat dau bang thang chua"
    assert E.khop_ma("US100", ["XM_US100"]) == "XM_US100" and E.khop_ma("AAPL", cs) is None


def test_khung_goi_y():
    assert E.khung_goi_y("input ENUM_TIMEFRAMES InpTf = PERIOD_M15;") == "M15"
    assert E.khung_goi_y("input ENUM_TIMEFRAMES InpTf = PERIOD_CURRENT;", "Scalper M5") == "M5"
    assert E.khung_goi_y("", "Trend EA", "works on H4 and D1") == "H4"
    assert E.khung_goi_y("", "Trend EA") is None


# ============================================================ THAM SO
def test_input_so_giu_kieu_va_bo_chuoi_va_enum():
    ma = ("input int A = 5; input double B = 0.5; sinput int C = -3; input string S = \"x\"; input bool F = true;\n"
          "input ENUM_TIMEFRAMES T = PERIOD_H1; extern double D = 2;")
    ra = {i["ten"]: (i["kieu"], i["mac_dinh"]) for i in E.input_so(ma)}
    assert ra == {"A": ("int", 5), "B": ("double", 0.5), "C": ("int", -3), "D": ("double", 2.0)}


def test_luoi_tham_so_nho_quanh_mac_dinh_va_khong_dong_lot_magic():
    pl = E.phan_loai(CHIEN_LUOC)
    luoi = E.de_xuat_tham_so(pl["input_so"])
    assert luoi[0] == {"ten": "mac_dinh", "tham_so": {}}
    ten = {k for c in luoi for k in c["tham_so"]}
    assert ten == {"InpFast", "InpSlow", "InpStep"}, "lot / magic khong phai tham so de tinh chinh"
    assert {"InpFast": 8} in [c["tham_so"] for c in luoi] and {"InpFast": 17} in [c["tham_so"] for c in luoi]
    assert all(len(c["tham_so"]) <= 1 for c in luoi), "moi lan chi doi MOT bien"
    assert len(luoi) <= 7 and len(E.de_xuat_tham_so(pl["input_so"], toi_da=3)) == 3
    assert E.de_xuat_tham_so([{"ten": "InpPeriod", "kieu": "int", "mac_dinh": 1}], he_so=(0.7,)) == \
        [{"ten": "mac_dinh", "tham_so": {}}], "chu ky 1 * 0,7 lam tron ve 1 = chinh no, khong tao diem trung"


# ============================================================ CUA SO
def test_cua_so_cach_ly_mot_ngay_va_khong_chong_len_nhau():
    k = _doan("2010-01-01 00:00:00", "2018-01-01 00:00:00", "2021-01-01 00:00:00", "2025-12-31 23:00:00")
    kp, xn, np_ = (E.cua_so(k, d) for d in ("kham_pha", "xac_nhan", "niem_phong"))
    assert kp == (date(2010, 1, 1), date(2017, 12, 31))
    assert xn == (date(2018, 1, 2), date(2020, 12, 31))
    assert np_ == (date(2021, 1, 2), date(2025, 12, 31))
    assert kp[1] < xn[0] and xn[1] < np_[0]


def test_ke_hoach_dinh_dang_ngay_mt5_va_cac_ly_do_khong_chay():
    kh = E.ke_hoach("eurusd", "H1", "kham_pha")
    assert kh["tu"] == "2010.01.01" and kh["den"] == "2017.12.31" and kh["khoa_doan"] == "EURUSD|H1"
    # khung chua dong bang -> lui ve H1 (cung ranh gioi voi cac EA khac cua cap nay)
    assert E.ke_hoach("EURUSD", "M15", "xac_nhan")["khoa_doan"] == "EURUSD|H1"
    thieu = E.ke_hoach("AUDCAD", "H1", "kham_pha")
    assert thieu["trang_thai"] == "CHUA_DO_DUOC" and thieu["ha_tang"] and "chua co doan dong bang" in thieu["ly_do"]
    cfg = dict(E.cau_hinh(), tick_tu="2017-12-15")
    ngan = E.ke_hoach("EURUSD", "H1", "kham_pha", cfg)
    assert ngan["ha_tang"] and "ngoai tick that" in ngan["ly_do"], "tick that chi tu 15/12/2017: kham_pha con 17 ngay < 30"
    cfg = dict(E.cau_hinh(), tick_tu="2012-06-15")
    assert E.ke_hoach("EURUSD", "H1", "kham_pha", cfg)["tu"] == "2012.06.15"
    with pytest.raises(ValueError):
        E.ke_hoach("EURUSD", "H1", "toan_bo")


# ============================================================ CONG (thuan, khong tester)
def _lenh(doan="kham_pha", model=4, von=10000.0):
    cs = E.ke_hoach("EURUSD", "H1", doan)
    return {"cua_so": cs, "model": model, "von": von, "doan": doan}


def _bc(**kw):
    van = html_mau(EN, **{"ky": "H1 (2010.01.01 - 2017.12.31)", **kw})
    from nhan import bao_cao_mt5 as BC
    return BC.phan_tich(van)


def test_cong_dat_khi_co_lai_va_maxdd_duoi_80():
    tt, ly, so = E.phan_quyet(_bc(), "kham_pha", _lenh(), E.cau_hinh())
    assert tt == "DAT" and not so["ha_tang"] and so["so_lenh"] == 51 and so["dd_pct"] == 21.0
    # (1 + 1234,56/10000)^(365,25/2922) - 1 = 1,4%/nam: lai nho van la co lai
    assert 1.3 < so["cagr_pct"] < 1.5, so


def test_cong_chi_chan_lo_va_dd_tu_80_tro_len_khong_chan_kieu_martingale():
    cfg = E.cau_hinh()
    tt, ly, _ = E.phan_quyet(_bc(lai=-300.0, tho=900.0, lo=-1200.0), "kham_pha", _lenh(), cfg)
    assert tt == "AM" and "KHONG co lai" in ly
    tt, ly, _ = E.phan_quyet(_bc(dd="8 000.00 (80.00%)"), "kham_pha", _lenh(), cfg)
    assert tt == "AM" and "maxDD" in ly, "dung 80% la bi chan: TRAN_SUT_GIAM la < 80"
    tt, _, so = E.phan_quyet(_bc(dd="7 900.00 (79.00%)", lai=5000.0, tho=9000.0, lo=-4000.0), "kham_pha",
                             _lenh(), cfg)
    assert tt == "DAT", "DD 79% van duoc - chu du an: chi can co lai va maxDD duoi 80%, bat ke phuong phap"
    assert any("gan tran" in x for x in E.nhan_canh_bao(so, {}, cfg, _lenh()))


def test_cong_it_lenh_la_chua_do_duoc_va_van_ghi_phep_thu():
    tt, ly, so = E.phan_quyet(_bc(lenh=7), "kham_pha", _lenh(), E.cau_hinh())
    assert tt == "CHUA_DO_DUOC" and "7 lenh" in ly and not so["ha_tang"]


def test_cong_hong_ha_tang_khong_phai_am():
    cfg = E.cau_hinh()
    from nhan import bao_cao_mt5 as BC
    cac = [
        E.phan_quyet(BC.phan_tich("<html>crashed</html>"), "kham_pha", _lenh(), cfg),
        E.phan_quyet(_bc(), "kham_pha", _lenh(), cfg, log_hong="TESTER KHONG CHAY DUOC"),
        E.phan_quyet(_bc(ky="H1 (2009.01.01 - 2017.12.31)"), "kham_pha", _lenh(), cfg),   # ra ngoai doan
        E.phan_quyet(_bc(ky="H1 (2012.01.01 - 2013.12.31)"), "kham_pha", _lenh(), cfg),   # phu < 80%
    ]
    for tt, ly, so in cac:
        assert tt == "CHUA_DO_DUOC" and so["ha_tang"], ly


def test_cong_cua_so_bao_cao_chi_can_nam_trong_khong_doi_trung_ngay():
    # tester cat ngay cuoi thieu du lieu: van hop le
    tt, _, so = E.phan_quyet(_bc(ky="H1 (2010.01.04 - 2017.12.29)"), "kham_pha", _lenh(), E.cau_hinh())
    assert tt == "DAT" and so["cua_so_khop"] is True


def test_cong_niem_phong_chi_phi_khai_la_hong_ha_tang_va_khong_lo_so():
    cfg = E.cau_hinh()
    lenh = _lenh("niem_phong")
    ky = "H1 (%s - %s)" % (lenh["cua_so"]["tu"], lenh["cua_so"]["den"])
    from nhan import bao_cao_mt5 as BC
    ok = BC.phan_tich(html_mau(EN, ky=ky, lenh=40))
    assert E.phan_quyet(ok, "niem_phong", lenh, cfg)[0] == "DAT"
    kem = BC.phan_tich(html_mau(EN, ky=ky, lenh=40).replace("<b>100%</b>", "<b>70%</b>"))
    tt, ly, so = E.phan_quyet(kem, "niem_phong", lenh, cfg)
    assert tt == "CHUA_DO_DUOC" and so["ha_tang"] and "cagr_pct" not in so, "khong do duoc chi phi thi khong tra so"
    khong_nhan = BC.phan_tich(html_mau(EN, ky=ky, lenh=40).replace("History Quality:", "Chat luong:"))
    assert E.phan_quyet(khong_nhan, "niem_phong", lenh, cfg)[2]["ha_tang"]
    # doan mo: chi phi khai chi con la NHAN
    tt, _, so = E.phan_quyet(BC.phan_tich(html_mau(EN, ky="H1 (2010.01.01 - 2017.12.31)").replace(
        "<b>100%</b>", "<b>70%</b>")), "kham_pha", _lenh(), cfg)
    assert tt == "DAT" and so["do_tin_chi_phi"] == "KHAI"
    assert any("chi phi KHAI" in x for x in E.nhan_canh_bao(so, {}, cfg, _lenh()))
    it = BC.phan_tich(html_mau(EN, ky=ky, lenh=12))
    assert E.phan_quyet(it, "niem_phong", lenh, cfg)[0] == "CHUA_DO_DUOC", "niem phong can >= 20 lenh"


def test_chi_phi_do_duoc_can_model_4_va_chat_luong():
    cfg = E.cau_hinh()
    assert E.chi_phi_do_duoc({"chat_luong_pct": 99.0}, 4, cfg)[0] is True
    assert E.chi_phi_do_duoc({"chat_luong_pct": 99.0}, 1, cfg)[0] is False
    assert E.chi_phi_do_duoc({"chat_luong_pct": 89.9}, 4, cfg)[0] is False
    assert E.chi_phi_do_duoc({}, 4, cfg)[0] is False


# ============================================================ LAP LENH / VAN TAY
def test_van_tay_theo_noi_dung_khong_theo_thu_tu_khoa_hay_kieu_so(ea_cl):
    d = E.doc_ea(ea_cl)
    cfg = E.cau_hinh()
    a = E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpFast": 8, "InpStep": 35}, cfg=cfg)["lenh"]["van_tay"]
    b = E.lap_lenh(d, "eurusd", "h1", "kham_pha", {"InpStep": 35.0, "InpFast": 8.0}, cfg=cfg)["lenh"]["van_tay"]
    assert a == b
    khac = [E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpFast": 9, "InpStep": 35}, cfg=cfg)["lenh"]["van_tay"],
            E.lap_lenh(d, "EURUSD", "H1", "xac_nhan", {"InpFast": 8, "InpStep": 35}, cfg=cfg)["lenh"]["van_tay"],
            E.lap_lenh(d, "XAUUSD", "H1", "kham_pha", {"InpFast": 8, "InpStep": 35}, cfg=cfg)["lenh"]["van_tay"],
            E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpFast": 8, "InpStep": 35},
                       cfg=dict(cfg, model=1))["lenh"]["van_tay"],
            E.lap_lenh(d, "EURUSD", "H1", "kham_pha", {"InpFast": 8, "InpStep": 35},
                       cfg=dict(cfg, von=5000))["lenh"]["van_tay"]]
    assert len({a, *khac}) == 6


def test_lenh_tester_co_dung_cua_so_symbol_va_input(ea_cl, tmp_path):
    d = E.doc_ea(ea_cl)
    cfg = dict(E.cau_hinh(), hau_to_symbol="m", ban_do_symbol={"XAUUSD": "GOLD"}, don_bay=50, von=2000)
    v = E.lap_lenh(d, "EURUSD", "H1", "xac_nhan", {"InpFast": 8}, cfg=cfg)["lenh"]["viec"]
    assert v["symbol"] == "EURUSDm" and (v["tu"], v["den"]) == ("2018.01.02", "2020.12.31")
    assert v["model"] == 4 and v["von"] == 2000 and v["don_bay"] == 50 and v["khung"] == "H1"
    assert v["input"] == {"InpFast": {"gia_tri": 8}}
    assert E.lap_lenh(d, "XAUUSD", "H1", "xac_nhan", cfg=cfg)["lenh"]["viec"]["symbol"] == "GOLD"
    assert E.lap_lenh(d, "EURUSD", "H9", "xac_nhan", cfg=cfg)["trang_thai"] == "CHUA_DO_DUOC"


def test_doc_ea_tu_file_utf16_va_tu_kho(tmp_path):
    f = tmp_path / "Ea16.mq5"
    f.write_bytes(b"\xff\xfe" + CHIEN_LUOC.encode("utf-16-le"))
    d = E.doc_ea(str(f))
    assert E.phan_loai(d["ma"])["loai"] == "CHIEN_LUOC" and d["sha"] == E.doc_ea(str(f))["sha"]
    with pytest.raises(KeyError):
        E.doc_ea(str(tmp_path / "khong_co.mq5"))
    ds = _kho()
    assert E.doc_ea("kho:0")["tieu_de"] == ds[0]["ten"]
    with pytest.raises(KeyError):
        E.doc_ea("kho:999")
    with pytest.raises(KeyError):
        E.doc_ea("kho:GDS Renko")          # khop 2 EA -> khong doan


# ============================================================ CHAY MOT LAN
def test_kham_pha_ghi_so_tay_va_chay_lai_y_het_khong_tinh_them(ea_cl, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path)
    gt = ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")
    r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", {"InpFast": 8}, gt)
    assert r["trang_thai"] == "DAT" and r["chi_so"]["so_lenh"] == 51 and t.lan == 1
    assert r["nhan"]["canh_bao"], "phai co nhan canh bao (chua hieu chuan lenh mo cuoi ky)"
    row = ST.mot("SELECT * FROM thi_nghiem WHERE id=?", r["tn_id"])
    assert (row["loai"], row["doan"], row["ma"], row["khung"], row["trang_thai"], row["so_phep_thu"]) == \
           ("ea_tho_kham_pha", "kham_pha", "EURUSD", "H1", "DAT", 1) and row["gt_id"] == gt
    assert ST.dem_phep_thu(gt_id=gt) == 1
    r2 = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", {"InpFast": 8.0}, gt)
    assert r2["tu_so_tay"] and t.lan == 1 and r2["trang_thai"] == "DAT", "cung van tay: khong chay, khong dem"
    assert ST.dem_phep_thu(gt_id=gt) == 1 and dem("thi_nghiem") == 1
    E.chay(ea_cl, "EURUSD", "H1", "kham_pha", {"InpFast": 9}, gt)
    assert ST.dem_phep_thu(gt_id=gt) == 2 and t.lan == 2


def test_hong_ha_tang_khong_ghi_so_tay_va_khong_dem_phep_thu(ea_cl, tmp_path, monkeypatch):
    gt = ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")
    dat_tester(monkeypatch, tmp_path, xong=False)
    r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", None, gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r["ha_tang"] and dem("thi_nghiem") == 0
    dat_tester(monkeypatch, tmp_path, sua=lambda v: "<html>Tester crashed</html>")
    r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", None, gt)
    assert r["ha_tang"] and "khong doc duoc" in r["ly_do"] and dem("thi_nghiem") == 0
    dat_tester(monkeypatch, tmp_path, log="MetaTester started\ncannot generate history data, check disk space\n")
    r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", None, gt)
    assert r["ha_tang"] and "TESTER KHONG CHAY DUOC" in r["ly_do"] and dem("thi_nghiem") == 0
    assert ST.dem_phep_thu(gt_id=gt) == 0


def test_am_va_it_lenh_deu_duoc_ghi_va_dem(ea_cl, tmp_path, monkeypatch):
    gt = ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")
    dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lai": -800.0, "tho": 1000.0, "lo": -1800.0})
    r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", {"InpFast": 5}, gt)
    assert r["trang_thai"] == "AM"
    dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lenh": 4})
    r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha", {"InpFast": 6}, gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and not r.get("ha_tang") and r["tn_id"]
    assert ST.dem_phep_thu(gt_id=gt) == 2 and dem("thi_nghiem", "trang_thai='CHUA_DO_DUOC'") == 1


def test_chay_o_may_khong_co_mt5_noi_ro_can_may_nha(ea_cl, monkeypatch):
    monkeypatch.setattr(E.os, "name", "posix")
    r = E.chay(ea_cl, "EURUSD", "H1", "kham_pha")
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r["ha_tang"] and "may nha" in r["ly_do"]
    assert dem("thi_nghiem") == 0


# ============================================================ NIEM PHONG
def _xac_nhan_dat(ea_cl, gt, ts):
    r = E.chay(ea_cl, "EURUSD", "H1", "xac_nhan", ts, gt)
    assert r["trang_thai"] == "DAT", r


def test_niem_phong_bi_chan_khi_thieu_dieu_kien_va_khong_chay_tester(ea_cl, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lenh": 40})
    ts = {"InpFast": 8}
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, None)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "gt_id" in r["ly_do"] and t.lan == 0
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, 999)
    assert "khong co gia thuyet" in r["ly_do"] and t.lan == 0
    gt = ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, gt)
    assert "xac_nhan DAT" in r["ly_do"] and t.lan == 0, "chua qua xac_nhan thi khong duoc cham seal"
    _xac_nhan_dat(ea_cl, gt, ts)
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", {"InpFast": 9}, gt)      # bo khac: chon tren seal
    assert "xac_nhan DAT" in r["ly_do"] and "CHINH bo" in r["ly_do"]
    monkeypatch.setenv("EA_THO_CFG", str(_cfg(tmp_path, model=1)))
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, gt)
    assert "Model=4" in r["ly_do"] and dem("niem_phong") == 0 and t.lan == 1, "chi xac_nhan da chay tester"


def _cfg(tmp_path, **kw):
    f = tmp_path / "ea_tho2.json"
    f.write_text(json.dumps({"tu_nap": False, **kw}), encoding="utf-8")
    return f


def test_niem_phong_mot_lan_cho_mot_bo_va_ghi_ba_noi(ea_cl, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lenh": 40})
    gt = ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")
    ts = {"InpFast": 8}
    _xac_nhan_dat(ea_cl, gt, ts)
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, gt)
    assert r["trang_thai"] == "DAT" and "chua phai chan ly" in r["goi_ten_dung"] and t.lan == 2
    assert (r["cua_so"]["tu"], r["cua_so"]["den"]) == ("2021.01.02", "2025.12.31")
    np_ = ST.mot("SELECT * FROM niem_phong")
    assert np_["gt_id"] == gt and np_["trang_thai"] == "DAT" and np_["ma"] == "EURUSD"
    assert ST.mot("SELECT trang_thai FROM gia_thuyet WHERE id=?", gt)["trang_thai"] == "XAC_NHAN"
    assert dem("thi_nghiem", "doan='niem_phong'") == 1
    r2 = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, gt)
    assert "da_mo_truoc" in r2 and r2["trang_thai"] == "DAT" and t.lan == 2 and dem("niem_phong") == 1


def test_niem_phong_am_danh_dau_truot_va_tran_ba_lan_moi_dong(ea_cl, tmp_path, monkeypatch):
    def kq(lenh):
        return {"lai": -900.0, "tho": 800.0, "lo": -1700.0, "lenh": 40} if lenh["doan"] == "niem_phong" \
            else {"lenh": 40}
    t = dat_tester(monkeypatch, tmp_path, kq=kq)
    gt = ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")
    for i in range(3):
        ts = {"InpFast": 8 + i}
        _xac_nhan_dat(ea_cl, gt, ts)
        r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, gt)
        assert r["trang_thai"] == "AM", r
    assert dem("niem_phong") == 3
    assert ST.mot("SELECT trang_thai FROM gia_thuyet WHERE id=?", gt)["trang_thai"] == "TRUOT_NIEM_PHONG"
    ts = {"InpFast": 20}
    _xac_nhan_dat(ea_cl, gt, ts)
    lan = t.lan
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, gt)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "tran 3" in r["ly_do"] and t.lan == lan and dem("niem_phong") == 3
    con = ST.them_gia_thuyet("Bien the cua EA tren", "con", ho="ea_tho", cha=gt)
    _xac_nhan_dat(ea_cl, con, ts)
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, con)
    assert "tran 3" in r["ly_do"], "gia thuyet CON cung dong voi goc: khong lach tran bang cach tao nhanh moi"


def test_niem_phong_hong_chi_phi_khong_tieu_luot_mo(ea_cl, tmp_path, monkeypatch):
    gt = ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")
    ts = {"InpFast": 8}
    dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lenh": 40})
    _xac_nhan_dat(ea_cl, gt, ts)
    dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lenh": 40}, sua=lambda v: v.replace("<b>100%</b>", "<b>55%</b>"))
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, gt)
    assert r["ha_tang"] and "chi_so" not in r and dem("niem_phong") == 0
    t = dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lenh": 40})
    r = E.chay(ea_cl, "EURUSD", "H1", "niem_phong", ts, gt)
    assert r["trang_thai"] == "DAT" and dem("niem_phong") == 1 and t.lan == 1, "lan hong khong tinh la mot lan mo"


# ============================================================ TINH CHINH + QUET
def test_tinh_chon_bo_dat_tot_nhat_xac_nhan_dung_bo_do_va_khong_cham_seal(ea_cl, tmp_path, monkeypatch):
    def kq(lenh):
        f = lenh["tham_so"].get("InpFast")
        return {"lai": {None: 1000.0, 8: 3000.0, 17: 2000.0}.get(f, -100.0), "lenh": 60}
    t = dat_tester(monkeypatch, tmp_path, kq=kq)
    r = E.tinh(ea_cl, "EURUSD", "H1")
    assert r["tot_nhat"]["tham_so"] == {"InpFast": 8} and len(r["bang"]) == 7
    assert r["xac_nhan"]["tham_so"] == {"InpFast": 8} and r["trang_thai"] == "DAT"
    assert t.lenh[-1]["doan"] == "xac_nhan" and t.lenh[-1]["tham_so"] == {"InpFast": 8}
    assert dem("niem_phong") == 0 and not any(l["doan"] == "niem_phong" for l in t.lenh)
    assert ST.dem_phep_thu(gt_id=r["gt_id"]) == 7, "moi diem luoi la mot phep thu duoc dem"
    assert ST.mot("SELECT trang_thai FROM gia_thuyet WHERE id=?", r["gt_id"])["trang_thai"] == "TRIEN_VONG"


def test_tinh_khong_bo_nao_dat_thi_khong_xac_nhan(ea_cl, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lai": -500.0, "tho": 500.0, "lo": -1000.0})
    r = E.tinh(ea_cl, "EURUSD", "H1")
    assert r["trang_thai"] == "AM" and r["tot_nhat"] is None and r["xac_nhan"] is None
    assert not any(l["doan"] == "xac_nhan" for l in t.lenh)
    assert E.tinh(ea_cl, "EURUSD", "H1", xac_nhan=False)["trang_thai"] == "AM"


def test_tinh_khong_xac_nhan_thi_dung_o_bo_tot_nhat(ea_cl, tmp_path, monkeypatch):
    t = dat_tester(monkeypatch, tmp_path, kq=lambda l: {"lai": 3000.0 if l["tham_so"].get("InpSlow") == 18 else 100.0,
                                                          "lenh": 60})
    r = E.tinh(ea_cl, "EURUSD", "H1", xac_nhan=False)
    assert r["trang_thai"] == "DANG_CHO_XAC_NHAN" and r["tot_nhat"]["tham_so"] == {"InpSlow": 18}
    assert r["xac_nhan"] is None and not any(l["doan"] == "xac_nhan" for l in t.lenh)


def test_quet_bo_tien_ich_dat_ma_theo_bang_chung_va_het_ngan_sach(tmp_path, monkeypatch):
    _kho()
    t = dat_tester(monkeypatch, tmp_path)
    r = E.quet("kho:*", toi_da_lan=3, co_san=["EURUSD", "XAUUSDM", "XAUUSD"])
    assert r["het_ngan_sach"] and r["so_lan_chay"] == 3 and len(r["bang"]) == 3 and t.lan == 3
    assert r["con_lai"], "phan chua chay phai duoc liet ke de goi lai di tiep"
    loai_bo = {b["ea"]: b.get("loai") for b in r["bo_qua"]}
    assert sum(1 for v in loai_bo.values() if v == "TIEN_ICH") == 5, "phan loai chay het du het ngan sach: %s" % loai_bo
    assert any(v == "THIEU_DU_LIEU" for v in loai_bo.values()), "EA co phieu: may khong co AAPL -> bo qua co ly do"
    assert all(b["trang_thai"] == "DAT" for b in r["bang"])
    ma = {b["ma"] for b in r["bang"]}
    assert ma <= {"EURUSD", "XAUUSD"}, "khong co ma nao ngoai danh sach co san"
    assert dem("gia_thuyet", "nguon='ea_tho'") == 3
    r2 = E.quet("kho:*", toi_da_lan=30, co_san=["EURUSD", "XAUUSD"])
    assert not r2["het_ngan_sach"] and not r2["con_lai"]
    assert sum(1 for b in r2["bang"] if b["tu_so_tay"]) == 3, "3 lan dau da co trong so tay: khong chay lai"
    assert t.lan == 3 + r2["so_lan_chay"] and len(r2["bang"]) == 3 + r2["so_lan_chay"]
    assert dem("gia_thuyet", "nguon='ea_tho'") == len(r2["bang"]), "mot gia thuyet moi cap (EA, ma, khung)"
    assert not any(b["ea"].startswith("AAPL") for b in r2["bang"]), "EA co phieu khong co ma AAPL thi bo qua"
    # chay lai: tat ca ra tu so tay, khong gia tang lenh tester
    lan = t.lan
    r3 = E.quet("kho:*", toi_da_lan=30, co_san=["EURUSD", "XAUUSD"])
    assert t.lan == lan and r3["so_lan_chay"] == 0 and all(b["tu_so_tay"] for b in r3["bang"])


def test_ea_thieu_tep_bi_loai_truoc_khi_tao_gia_thuyet_hay_ton_luot_tester(ea_cl, tmp_path, monkeypatch):
    thieu = tmp_path / "ThieuTep.mq5"
    thieu.write_text("#include <MultiPivots.mqh>\n" + CHIEN_LUOC, encoding="utf-8")
    t = dat_tester(monkeypatch, tmp_path)
    r = E.chay(str(thieu), "EURUSD", "H1")
    assert r["trang_thai"] == "CHUA_DO_DUOC" and r["ha_tang"] and r["thieu_tep"] == ["include_la:MultiPivots.mqh"]
    assert "tep_san" in r["ly_do"] and t.lan == 0 and dem("thi_nghiem") == 0, "thieu tep: khong tester, khong ghi so"
    k = E.kham(str(thieu), "EURUSD H1 trend", co_san=["EURUSD"])
    assert "THIEU TEP" in k["ket_luan"] and k["ma_khung"]["ung_vien"], "kham van cho thay ma/khung nham toi (de biet tai goi nao)"
    q = E.quet([str(thieu), ea_cl], co_san=["EURUSD"], toi_da_lan=5)
    assert [b["loai"] for b in q["bo_qua"] if b["ea"].startswith("ThieuTep")] == ["THIEU_TEP"]
    assert q["so_lan_chay"] == len(q["bang"]) == t.lan >= 1
    assert all(not l["ea_ten"].startswith("ThieuTep") for l in t.lenh)
    assert dem("gia_thuyet", "nguon='ea_tho'") == len(q["bang"]), "khong tao gia thuyet cho EA khong chay duoc"
    # khai bao tep da cai san -> qua tien kiem va duoc chay
    (tmp_path / "ea_tho.json").write_text(json.dumps({"tu_nap": False, "tep_san": ["MultiPivots.mqh"]}), encoding="utf-8")
    r2 = E.chay(str(thieu), "EURUSD", "H1")
    assert r2["trang_thai"] == "DAT" and t.lan >= 2 and r2["tn_id"]


# ============================================================ BO CONG CU (nc_cong_cu)
def test_bon_cong_cu_ea_tho_dang_ky_cuoi_danh_sach_va_goi_duoc(ea_cl, tmp_path, monkeypatch):
    from nhan import nc_cong_cu as CC
    ten = [c["ten"] for c in CC.CONG_CU]
    # NOI TIEP sau cong cu cu cuoi cung (`yeu_cau_seeker`), khong chen vao giua: cong cu sau nay (vd boc_lich_su) lai noi tiep
    # sau bon cai nay - day truoc do khong doi thi cache prompt con. (Truoc 03/10 viet `ten[-4:]` nen moi cong cu them sau la vo.)
    i = ten.index("ea_tho_kham")
    assert ten[i - 1] == "yeu_cau_seeker" and ten[i:i + 4] == ["ea_tho_kham", "ea_tho_chay", "ea_tho_quet", "ea_tho_tinh"], \
        "them o CUOI: giu cache prompt"
    api = {t["name"]: t for t in CC.schema_api()}
    for n in ten[i:i + 4]:
        assert len(api[n]["description"]) > 200 and api[n]["input_schema"]["required"]
    r = CC.goi("ea_tho_kham", {"ea": ea_cl, "tieu_de": "XAUUSD trend M30", "co_san": ["XAUUSDM"]})
    assert r["phan_loai"]["loai"] == "CHIEN_LUOC" and r["ma_khung"]["ung_vien"][0]["ma"] == "XAUUSDM"
    assert r["ma_khung"]["ung_vien"][0]["khung"] == "M30" and "loi" not in r
    t = dat_tester(monkeypatch, tmp_path)
    gt = ST.them_gia_thuyet("EA cong khai co lai sau phi tren EURUSD H1", "EA da ban cong khai", ho="ea_tho")
    r = CC.goi("ea_tho_chay", {"ea": ea_cl, "ma": "EURUSD", "khung": "H1", "tham_so": {"InpFast": 8}, "gt_id": gt})
    assert r["trang_thai"] == "DAT" and t.lan == 1 and r["tn_id"]
    r = CC.goi("ea_tho_quet", {"eas": ["kho:*"], "toi_da_lan": 1, "co_san": ["EURUSD", "XAUUSD"]})
    assert r["so_lan_chay"] == 1 and r["con_lai"] and len(r["bo_qua"]) >= 5
    r = CC.goi("ea_tho_tinh", {"ea": ea_cl, "ma": "EURUSD", "khung": "H1", "toi_da_lan": 3, "xac_nhan": False})
    assert len(r["bang"]) == 3 and r["trang_thai"] == "DANG_CHO_XAC_NHAN"


def test_cong_cu_ea_tho_loi_nhap_lieu_tra_loi_khong_vo_vong_lap(tmp_path):
    from nhan import nc_cong_cu as CC
    assert "khong thay file EA" in CC.goi("ea_tho_kham", {"ea": str(tmp_path / "khong_co.mq5")})["loi"]
    assert "tham so khong co trong schema" in CC.goi("ea_tho_chay", {"ea": "x", "ma": "A", "khung": "H1",
                                                                      "so_lenh_toi_da": 3})["loi"]
    assert "thieu tham so bat buoc" in CC.goi("ea_tho_chay", {"ea": "x"})["loi"]
    assert "KeyError" in CC.goi("ea_tho_kham", {"ea": "kho:999"})["loi"] or "kho co" in CC.goi(
        "ea_tho_kham", {"ea": "kho:999"})["loi"]


def test_tho_khong_duoc_goi_cong_cu_ea_tho():
    """Mo hinh re (DeepSeek) chi kham pha - EA tho cham xac_nhan/niem_phong nen khong nam trong CONG_CU_THO."""
    from nhan import nc_tho
    assert not any(n.startswith("ea_tho") for n in nc_tho.CONG_CU_THO)
