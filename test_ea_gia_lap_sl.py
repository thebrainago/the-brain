# -*- coding: utf-8 -*-
"""Kiem SAN GIA C++ (`nhan/ea_gia_lap.cpp`) cho SL may chu + hop dong / gioi han lot + iTime theo khung + duong gia 4 tick/phut
(`tick_ohlc4`) - 09/10/2026, mini-Brain CanCuBo.

Truoc 09/10 san gia chi co TP may chu; EA CanCuBo thoat chuoi bang SL truot (PositionModify) nen thieu SL = thieu nua co che. Moi ca o day
la mot kich ban nho TAY TINH DUOC (so tay, khong gia lap lai logic cua chinh san gia):
  - MUA dong khi BID <= SL, khop DUNG muc SL (mac dinh) hoac o BID cua tick (--sl-thi-truong, co truot gia)
  - BAN dong khi ASK >= SL
  - TP van khop dung muc, uu tien TP khi ca hai cung dung (EA dat sai phia)
  - --contract doi tien lai (vang = 100); --vmin / --vmax / --vstep chan lot ngoai gioi han
"""
import numpy as np
import pytest

from nhan import ea_gia_lap as G

EA_MAU = r'''
#property version "1.00"
#include <Trade/Trade.mqh>
input double InpSl  = 0.0;
input double InpTp  = 0.0;
input int    InpDir = 0;            // 0 = mua, 1 = ban
input double InpLot = 0.01;
CTrade g_t;
int g_xong = 0;
int OnInit() { return INIT_SUCCEEDED; }
void OnDeinit(const int reason) {}
void OnTick()
  {
   if(g_xong)
      return;
   g_xong = 1;
   const bool ok = InpDir == 0 ? g_t.Buy(InpLot, _Symbol, 0.0, 0.0, 0.0, "t") : g_t.Sell(InpLot, _Symbol, 0.0, 0.0, 0.0, "t");
   if(!ok)
      return;
   g_t.PositionModify(PositionGetTicket(0), InpSl, InpTp);
  }
'''


EA_HAI = r'''
#include <Trade/Trade.mqh>
input double InpSl  = 0.0;
input double InpLot = 0.01;
CTrade g_t;
int g_n = 0;
int OnInit() { return INIT_SUCCEEDED; }
void OnDeinit(const int reason) {}
void OnTick()
  {
   if(g_n >= 2)
      return;
   g_n++;
   g_t.Buy(InpLot, _Symbol, 0.0, 0.0, 0.0, "t");
   if(g_n == 2)
      for(int i = 0; i < PositionsTotal(); i++)
         g_t.PositionModify(PositionGetTicket(i), InpSl, 0.0);
  }
'''

EA_GIO = r'''
input int InpShift = 0;
int OnInit() { return INIT_SUCCEEDED; }
void OnDeinit(const int reason) {}
void OnTick()
  {
   PrintFormat("T %d %d %d %d %d", (int)iTime(_Symbol, PERIOD_CURRENT, InpShift), (int)iTime(_Symbol, PERIOD_M1, InpShift),
               (int)iTime(_Symbol, PERIOD_M5, InpShift), (int)iTime(_Symbol, PERIOD_H1, InpShift), (int)iTime(_Symbol, PERIOD_D1, InpShift));
  }
'''


def bd(tmp_path_factory, ma):
    if not G.trinh_bien_dich():
        pytest.skip("khong co trinh bien dich C++")
    p = tmp_path_factory.mktemp("sl") / "ea.mq5"
    p.write_text(ma, encoding="utf-8")
    return G.bien_dich(p, thu_muc=tmp_path_factory.mktemp("sl_bin"))


@pytest.fixture(scope="module")
def exe(tmp_path_factory):
    return bd(tmp_path_factory, EA_MAU)


def tick(bids, spread=0.02):
    n = len(bids)
    return dict(bid=np.asarray(bids, float), spread=np.full(n, spread), time=np.arange(n, dtype=float) * 20.0,
                bar=np.zeros(n))


def chay(exe, bids, tham_so, **kw):
    r = G.chay(exe, tick(bids), 10000.0, tham_so, digits=2, **kw)
    assert r["ok"], r["loi"]
    return r


def test_mua_sl_khop_dung_muc(exe):
    # mo MUA o ASK = 100,02 ; SL 99,60 ; BID tuot 99,99 -> 99,50 : tick 99,50 chua toi 99,60 truoc do
    r = chay(exe, [100.0, 99.99, 99.70, 99.50, 99.40], dict(InpSl=99.60), hop_dong=100)
    d = r["lenh"]
    assert len(d) == 1 and d.ly_do[0] == "sl" and d.close[0] == pytest.approx(99.60)
    assert d.tick_dong[0] == 3                                   # tick dau tien co BID <= 99,60 la tick thu 3 (99,50)
    assert r["kq"]["n_sl"] == 1 and r["kq"]["n_tp"] == 0 and r["kq"]["n_ea"] == 0
    assert r["kq"]["balance"] == pytest.approx(10000.0 + (99.60 - 100.02) * 0.01 * 100)       # -0,42
    assert r["kq"]["con_mo"] == 0


def test_mua_sl_cham_dung_muc_la_khop(exe):
    r = chay(exe, [100.0, 99.80, 99.60, 99.55], dict(InpSl=99.60), hop_dong=100)
    d = r["lenh"]
    assert d.tick_dong[0] == 2 and d.close[0] == pytest.approx(99.60)         # BID = SL dung -> khop (MT5 cung vay)


def test_sl_thi_truong_khop_o_bid_cua_tick(exe):
    r = chay(exe, [100.0, 99.99, 99.70, 99.50, 99.40], dict(InpSl=99.60), hop_dong=100, sl_thi_truong=True)
    d = r["lenh"]
    assert d.close[0] == pytest.approx(99.50) and d.ly_do[0] == "sl"
    assert r["kq"]["balance"] == pytest.approx(10000.0 + (99.50 - 100.02) * 0.01 * 100)       # -0,52


def test_ban_sl_khop_khi_ask_cham(exe):
    # BAN mo o BID 100,00 ; SL 100,40 ; ASK = BID + 0,02 : 100,12 / 100,37 chua toi ; 100,38 -> ask 100,40 -> khop
    r = chay(exe, [100.0, 100.10, 100.35, 100.38, 100.50], dict(InpDir=1, InpSl=100.40), hop_dong=100)
    d = r["lenh"]
    assert len(d) == 1 and d.type[0] == 1 and d.ly_do[0] == "sl" and d.close[0] == pytest.approx(100.40)
    assert d.tick_dong[0] == 3
    assert r["kq"]["balance"] == pytest.approx(10000.0 + (100.00 - 100.40) * 0.01 * 100)      # -0,40


def test_ban_sl_thi_truong_khop_o_ask_cua_tick(exe):
    # BAN, SL 100,40 ; tick 100,50 nhay qua (ask 100,52) -> thi truong khop o ASK 100,52 (khong phai bid 100,50 va khong phai muc SL)
    r = chay(exe, [100.0, 100.10, 100.50, 100.60], dict(InpDir=1, InpSl=100.40), hop_dong=100, sl_thi_truong=True)
    d = r["lenh"]
    assert d.ly_do[0] == "sl" and d.close[0] == pytest.approx(100.52) and d.tick_dong[0] == 2
    assert r["kq"]["balance"] == pytest.approx(10000.0 + (100.00 - 100.52) * 0.01 * 100)


def test_ban_khong_dat_sl_thi_khong_dong(exe):
    r = chay(exe, [100.0, 110.0, 200.0, 500.0], dict(InpDir=1), hop_dong=100)
    assert r["kq"]["con_mo"] == 1 and r["kq"]["n_sl"] == 0 and r["lenh"].ly_do[0] == "open"


def test_khong_dat_sl_thi_khong_dong(exe):
    r = chay(exe, [100.0, 90.0, 80.0, 10.0], dict(), hop_dong=100)
    assert r["kq"]["con_mo"] == 1 and r["kq"]["n_sl"] == 0 and len(r["lenh"]) == 1 and r["lenh"].ly_do[0] == "open"


def test_tp_thang_sl_khi_ca_hai_cung_dung_tren_mot_tick(exe):
    # EA dat SL va TP cung phia (SL 100,80 tren TP 100,30 cho lenh MUA - sai phia): tick 100,50 thoa CA HAI -> TP duoc uu tien nhu truoc 09/10
    r = chay(exe, [100.0, 100.50, 100.60], dict(InpSl=100.80, InpTp=100.30), hop_dong=100)
    d = r["lenh"]
    assert len(d) == 1 and d.ly_do[0] == "tp" and d.close[0] == pytest.approx(100.30)
    assert r["kq"]["n_tp"] == 1 and r["kq"]["n_sl"] == 0


def test_tp_va_sl_dung_phia_chi_cai_nao_cham_truoc_khop(exe):
    r = chay(exe, [100.0, 100.50, 101.20, 100.0], dict(InpSl=99.0, InpTp=101.0), hop_dong=100)
    d = r["lenh"]
    assert d.ly_do[0] == "tp" and d.close[0] == pytest.approx(101.0) and r["kq"]["n_tp"] == 1 and r["kq"]["n_sl"] == 0
    r = chay(exe, [100.0, 99.50, 98.90, 101.20], dict(InpSl=99.0, InpTp=101.0), hop_dong=100)
    d = r["lenh"]
    assert d.ly_do[0] == "sl" and d.close[0] == pytest.approx(99.0) and r["kq"]["n_tp"] == 0 and r["kq"]["n_sl"] == 1


def test_hop_dong_nhan_tien_lai(exe):
    bids = [100.0, 99.50, 99.40]
    fx = chay(exe, bids, dict(InpSl=99.60))                                     # mac dinh 100000 (FX)
    au = chay(exe, bids, dict(InpSl=99.60), hop_dong=100)
    lo_fx = fx["kq"]["balance"] - 10000.0
    lo_au = au["kq"]["balance"] - 10000.0
    assert lo_fx == pytest.approx(-0.42 * 0.01 * 100000)
    assert lo_au == pytest.approx(-0.42)
    assert lo_fx / lo_au == pytest.approx(1000.0)


def test_gioi_han_lot_tu_dong_cua_san(exe):
    r = chay(exe, [100.0, 100.1], dict(InpLot=0.50), hop_dong=100, lot=(0.01, 0.30, 0.01))
    assert r["kq"]["n_mo"] == 0                                                 # 0,50 > vmax 0,30 -> bi tu choi
    r2 = chay(exe, [100.0, 100.1], dict(InpLot=0.25), hop_dong=100, lot=(0.01, 0.30, 0.05))
    assert r2["kq"]["n_mo"] == 1                                                # 0,25 = 5 x buoc 0,05
    r3 = chay(exe, [100.0, 100.1], dict(InpLot=0.22), hop_dong=100, lot=(0.01, 0.30, 0.05))
    assert r3["kq"]["n_mo"] == 0                                                # 0,22 khong phai boi cua buoc 0,05


def test_nhieu_lenh_cung_sl_dong_cung_tick(tmp_path_factory):
    # hai lenh MUA cung SL (chuoi): dong CUNG MOT tick, cung gia SL (giong deal that cua CCBSN: 'sl 1786.60' x 4 lenh)
    exe2 = bd(tmp_path_factory, EA_HAI)
    r = chay(exe2, [100.0, 99.90, 99.60, 99.30], dict(InpSl=99.50), hop_dong=100)
    d = r["lenh"]
    # lenh 1 mo o tick 0 (ASK 100,02), lenh 2 o tick 1 (ASK 99,92) ; SL 99,50 gan cho CA HAI sau tick 1 ; BID 99,60 chua toi -> ca hai dong o tick 3
    assert r["kq"]["n_mo"] == 2 and r["kq"]["n_sl"] == 2 and r["kq"]["con_mo"] == 0
    assert list(d.ly_do) == ["sl", "sl"] and sorted(d.tick_mo) == [0, 1] and list(d.tick_dong) == [3, 3]   # san dong tu lenh moi nhat ve cu nhat
    assert list(np.round(d.close, 2)) == [99.50, 99.50]
    assert r["kq"]["balance"] == pytest.approx(10000.0 + ((99.50 - 100.02) + (99.50 - 99.92)) * 0.01 * 100)


def test_sl_gan_chua_den_thi_lenh_mo_den_cuoi_chuoi(tmp_path_factory):
    exe2 = bd(tmp_path_factory, EA_HAI)
    r = chay(exe2, [100.0, 99.90, 99.60, 99.55], dict(InpSl=99.50), hop_dong=100)
    assert r["kq"]["n_sl"] == 0 and r["kq"]["con_mo"] == 2 and r["kq"]["lot_con_mo"] == pytest.approx(0.02)


def tick_gio(thoi_gian):
    n = len(thoi_gian)
    return dict(bid=np.full(n, 100.0), spread=np.full(n, 0.02), time=np.asarray(thoi_gian, float), bar=np.zeros(n))


def test_itime_theo_khung(tmp_path_factory):
    exe2 = bd(tmp_path_factory, EA_GIO)
    t = [36000, 36020, 36059, 36060, 36119, 36300, 39600]
    r = G.chay(exe2, tick_gio(t), 10000.0, {}, digits=2)
    assert r["ok"], r["loi"]
    ra = [tuple(int(x) for x in dong.split()[1:]) for dong in r["log"] if dong.startswith("T ")]
    # (CURRENT = nen cua chuoi tick = 0 ; M1 ; M5 ; H1 ; D1)
    assert ra == [(0, 36000, 36000, 36000, 0), (0, 36000, 36000, 36000, 0), (0, 36000, 36000, 36000, 0),
                  (0, 36060, 36000, 36000, 0), (0, 36060, 36000, 36000, 0), (0, 36300, 36300, 36000, 0), (0, 39600, 39600, 39600, 0)]


def test_itime_shift_khac_0_dung_chuong_trinh(tmp_path_factory):
    exe2 = bd(tmp_path_factory, EA_GIO)
    r = G.chay(exe2, tick_gio([36000, 36060]), 10000.0, dict(InpShift=1), digits=2)
    assert not r["ok"] and r["ma_thoat"] == 3 and r["log"] == []


def test_khung_tuan_thang_khong_co_trong_san_gia(tmp_path_factory):
    # W1 / MN1 co tinh khong khai bao -> bien dich LOI (khong im lang tra nen sai)
    ma = EA_GIO.replace("PERIOD_D1", "PERIOD_W1")
    with pytest.raises(G.LoiBienDich):
        bd(tmp_path_factory, ma)


# ---------------------------------------------------------------------------------------------------------------- tick_ohlc4
import pandas as pd


def nen_m1(hang, bat_dau="2019-03-04 10:00", spread=20):
    """hang = [(open, high, low, close), ...] -> DataFrame M1 (index = gio mo nen, spread theo point)."""
    idx = pd.date_range(bat_dau, periods=len(hang), freq="60s")
    return pd.DataFrame([dict(open=o, high=h, low=l, close=c, spread=spread) for o, h, l, c in hang],
                        columns=["open", "high", "low", "close", "spread"], index=idx)


def test_tick_ohlc4_4_tick_moi_nen_o_giay_0_20_40_59():
    df = nen_m1([(100.0, 100.4, 99.9, 100.3), (100.3, 100.6, 100.0, 100.1)])
    tk = G.tick_ohlc4(df, point=0.01)
    assert len(tk["bid"]) == 8
    t0 = df.index[0].timestamp()
    assert list(tk["time"] - t0) == [0, 20, 40, 59, 60, 80, 100, 119]
    assert list(tk["bar"] - t0) == [0, 0, 0, 0, 60, 60, 60, 60] and list(tk["bar_idx"]) == [0, 0, 0, 0, 1, 1, 1, 1]
    assert np.allclose(tk["spread"], 0.20)                                       # 20 point x 0,01


def test_tick_ohlc4_thu_tu_theo_mau_nen():
    df = nen_m1([(100.0, 100.4, 99.9, 100.3), (100.3, 100.6, 100.0, 100.1), (100.5, 100.5, 100.5, 100.5)])
    # nen tang: O, LOW, HIGH, C ; nen giam: O, HIGH, LOW, C ; nen phang: 4 tick bang nhau (EA van thay tick dau nen o giay 0)
    assert np.allclose(G.tick_ohlc4(df, "theo_nen", 0.01)["bid"], [100.0, 99.9, 100.4, 100.3,  100.3, 100.6, 100.0, 100.1,  100.5, 100.5, 100.5, 100.5])
    assert np.allclose(G.tick_ohlc4(df, "thap_truoc", 0.01)["bid"][:8], [100.0, 99.9, 100.4, 100.3,  100.3, 100.0, 100.6, 100.1])
    assert np.allclose(G.tick_ohlc4(df, "cao_truoc", 0.01)["bid"][:8], [100.0, 100.4, 99.9, 100.3,  100.3, 100.6, 100.0, 100.1])
    assert np.allclose(G.tick_ohlc4(df, "xen_ke", 0.01)["bid"][:8], [100.0, 99.9, 100.4, 100.3,  100.3, 100.6, 100.0, 100.1])


def test_tick_ohlc4_tu_choi_dau_vao_vo_ly():
    df = nen_m1([(100.0, 100.4, 99.9, 100.3)])
    with pytest.raises(ValueError):
        G.tick_ohlc4(df, "ngau_nhien", 0.01)
    with pytest.raises(ValueError):
        G.tick_ohlc4(df, "theo_nen", 0.01, giay=(0, 20, 40, 60))                 # giay 60 = nen sau
    with pytest.raises(ValueError):
        G.tick_ohlc4(df, "theo_nen", 0.01, giay=(0, 40, 20, 59))
    with pytest.raises(ValueError):
        G.tick_ohlc4(df, "theo_nen", 0.0)
    with pytest.raises(ValueError, match="nen M1 hong"):
        G.tick_ohlc4(nen_m1([(100.0, 100.4, 99.9, 100.3), (100.0, 100.1, 99.9, 100.5)]), "theo_nen", 0.01)   # close > high


def test_tick_ohlc4_nen_rong_va_khong_cot_spread():
    tk = G.tick_ohlc4(nen_m1([]), point=0.01)
    assert all(len(v) == 0 for v in tk.values())
    tk = G.tick_ohlc4(nen_m1([(100.0, 100.4, 99.9, 100.3)]).drop(columns="spread"), point=0.01)
    assert np.all(tk["spread"] == 0.0)


EA_VAO_NEN = r'''
#include <Trade/Trade.mqh>
input double InpTp = 0.0;
input double InpSl = 0.0;
CTrade g_t;
datetime g_nen = 0;
int g_mo = 0;
int OnInit() { return INIT_SUCCEEDED; }
void OnDeinit(const int reason) {}
void OnTick()
  {
   const datetime nen = iTime(_Symbol, PERIOD_M1, 0);
   if(nen == g_nen)
      return;
   g_nen = nen;
   if(g_mo == 0 && g_t.Buy(0.01, _Symbol, 0.0, 0.0, 0.0, "t"))
     {
      g_mo = 1;
      g_t.PositionModify(PositionGetTicket(0), InpSl, InpTp);
     }
  }
'''


def giay_cua(tk, i):
    return int(tk["time"][i] % 60)


def test_ea_vao_lenh_o_giay_0_va_thoat_tp_o_giay_40_hoac_20_theo_mau_nen(tmp_path_factory):
    exe2 = bd(tmp_path_factory, EA_VAO_NEN)
    # nen 0: mo lenh MUA o giay 0 (ASK = 100,00 + 0,20). TP 101,00.
    # nen 1 TANG (O 100,2 L 100,1 H 101,3 C 101,2): thu tu O,L,H,C -> cham TP o tick H = giay 40
    tang = nen_m1([(100.0, 100.2, 99.9, 100.1), (100.2, 101.3, 100.1, 101.2)])
    tk = G.tick_ohlc4(tang, point=0.01)
    r = G.chay(exe2, tk, 10000.0, dict(InpTp=101.0), digits=2, hop_dong=100)
    d = r["lenh"]
    assert r["ok"] and len(d) == 1 and d.ly_do[0] == "tp" and d.close[0] == pytest.approx(101.0)
    assert giay_cua(tk, d.tick_mo[0]) == 0 and giay_cua(tk, d.tick_dong[0]) == 40
    assert d.open[0] == pytest.approx(100.20)                                    # MUA o ASK = open + spread 0,20
    # nen 1 GIAM nhung van cham TP (O 100,9 H 101,3 L 100,1 C 100,2): O,H,L,C -> cham TP o tick H = giay 20
    giam = nen_m1([(100.0, 100.2, 99.9, 100.1), (100.9, 101.3, 100.1, 100.2)])
    tk2 = G.tick_ohlc4(giam, point=0.01)
    r2 = G.chay(exe2, tk2, 10000.0, dict(InpTp=101.0), digits=2, hop_dong=100)
    d2 = r2["lenh"]
    assert d2.ly_do[0] == "tp" and giay_cua(tk2, d2.tick_dong[0]) == 20


def test_ea_thoat_sl_o_giay_40_tren_nen_giam_va_giay_20_tren_nen_tang(tmp_path_factory):
    exe2 = bd(tmp_path_factory, EA_VAO_NEN)
    giam = nen_m1([(100.0, 100.2, 99.9, 100.1), (100.1, 100.2, 99.0, 99.2)])        # O,H,L,C: low (99,0) o giay 40
    tk = G.tick_ohlc4(giam, point=0.01)
    r = G.chay(exe2, tk, 10000.0, dict(InpSl=99.5), digits=2, hop_dong=100)
    d = r["lenh"]
    assert d.ly_do[0] == "sl" and d.close[0] == pytest.approx(99.5) and giay_cua(tk, d.tick_dong[0]) == 40
    tang = nen_m1([(100.0, 100.2, 99.9, 100.1), (100.1, 100.3, 99.0, 100.2)])       # nen tang: O,L,H,C: low o giay 20
    tk2 = G.tick_ohlc4(tang, point=0.01)
    r2 = G.chay(exe2, tk2, 10000.0, dict(InpSl=99.5), digits=2, hop_dong=100)
    assert giay_cua(tk2, r2["lenh"].tick_dong[0]) == 20


def test_ea_chi_mo_lenh_dau_nen_moi_dung_iTime_M1(tmp_path_factory):
    # iTime(M1) doi o tick giay 0 cua moi nen -> lenh mo o tick dau tien (giay 0) cua nen 0
    exe2 = bd(tmp_path_factory, EA_VAO_NEN)
    tk = G.tick_ohlc4(nen_m1([(100.0, 100.2, 99.9, 100.1)] * 3), point=0.01)
    r = G.chay(exe2, tk, 10000.0, {}, digits=2, hop_dong=100)
    assert r["kq"]["n_mo"] == 1 and r["lenh"].tick_mo[0] == 0 and r["kq"]["con_mo"] == 1
