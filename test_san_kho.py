# -*- coding: utf-8 -*-
"""San KHO cua Seeker (17/10/2026): cham repo bang CAY FILE, tach link awesome-*, lan theo submodule."""
from pathlib import Path

import pytest

from tru import seeker as SK

EA = Path("/home/user/ea31337/ea31337")


def test_diem_kho_mot_ea_le_khong_phai_kho():
    d = SK.diem_kho(["README.md", "MyEA.mq5", "include/utils.mqh"])
    assert not d["la_kho"] and d["so_file_mql"] == 2


def test_diem_kho_bo_suu_tap_va_quan_tri_lenh():
    dd = ["Stg_%s/Stg_%s.mqh" % (n, n) for n in "ABCDEFGHIJKLMNOPQRST"]
    assert SK.diem_kho(dd)["la_kho"]
    qt = ["src/grid_manager.py", "src/dca_engine.py", "bot/martingale.mq5", "bot/hedge_lock.mq5", "bot/basket_close.mqh"]
    d = SK.diem_kho(qt)
    assert d["la_kho"] and d["so_file_quan_tri"] == 5 and "src/dca_engine.py" in d["vi_du_quan_tri"]
    assert SK.diem_kho(["a.py"], so_submodule=12)["la_kho"]


def test_tach_link_awesome_va_submodule():
    md = ("- [EA31337](https://github.com/EA31337/EA31337) robot\n- [x](https://github.com/topics/mql5)\n"
          "- see https://github.com/freqtrade/freqtrade-strategies.git and https://github.com/EA31337/EA31337)")
    assert SK.tach_link_github(md) == ["EA31337/EA31337", "freqtrade/freqtrade-strategies"]
    gm = '[submodule "strategies"]\n\tpath = src/strategies\n\turl = https://github.com/EA31337/EA31337-strategies.git\n'
    assert SK.tach_submodule(gm) == ["EA31337/EA31337-strategies"]


@pytest.mark.skipif(not (EA / "src" / "strategies").exists(), reason="can ban clone EA31337 (chi co tren may da tai)")
def test_ea31337_that_duoc_nhan_la_kho():
    # repo con EA31337-strategies: 69 submodule chien luoc -> KHO; repo meta: 42 file Stg_Meta_*.mqh
    goc = EA / "src" / "strategies"
    sm = sum(1 for l in (goc / ".gitmodules").read_text().splitlines() if l.strip().startswith("path"))
    assert SK.diem_kho([], so_submodule=sm)["la_kho"] and sm >= 60
    meta = [str(p.relative_to(EA)) for p in (EA / "src" / "strategies-meta").rglob("*.mqh")]
    assert SK.diem_kho(meta)["la_kho"]


def test_ky_hieu_ea_mql5_mql4_va_chi_bao():
    ea5 = "#include <Trade/Trade.mqh>\nCTrade trade;\nvoid OnTick(){ if(x) trade.Buy(0.01); TrailingStop(); }"
    d = SK.dau_hieu_van_hanh(ea5, "Grid_EA.mq5")
    assert d["nen_tang"] == "MT4/MT5" and d["loai"] == "ea" and d["van_hanh"] and "trailing" in d["quan_tri"]
    ea4 = "extern double LotExponent=1.5;\nint start(){ OrderSend(Symbol(),OP_BUY,Lots,Ask,3,0,0); return(0); }"
    d4 = SK.dau_hieu_van_hanh(ea4, "pipsmaker.mq4")
    assert d4["loai"] == "ea" and "martingale" in d4["quan_tri"]
    ind = "#property indicator_chart_window\nint OnCalculate(const int rates_total){return rates_total;}"
    assert SK.dau_hieu_van_hanh(ind, "TMA_bands.mq5")["loai"] == "chi_bao"


def test_ky_hieu_pine_python_ctrader():
    pine = "//@version=5\nstrategy('ORB', overlay=true)\nif cond\n    strategy.entry('L', strategy.long)"
    assert SK.dau_hieu_van_hanh(pine, "orb.txt") == {**SK.dau_hieu_van_hanh(pine, "orb.txt"), "nen_tang": "TradingView", "loai": "ea"}
    assert SK.dau_hieu_van_hanh("//@version=5\nindicator('x')\nplot(close)", "x.pine")["loai"] == "chi_bao"
    ft = "class NFI(IStrategy):\n    position_adjustment_enable = True\n    def adjust_trade_position(self):\n        pass"
    d = SK.dau_hieu_van_hanh(ft, "NostalgiaForInfinityX.py")
    assert d["loai"] == "ea" and "dca" in d["quan_tri"]
    cs = "public class GridBot : Robot { protected override void OnBar(){ ExecuteMarketOrder(TradeType.Buy, Symbol, 1000); } }"
    assert SK.dau_hieu_van_hanh(cs, "GridBot.cs")["loai"] == "ea"
    # bai van / file khong phai ma -> khong van hanh
    assert not SK.dau_hieu_van_hanh("This strategy buys when RSI < 30.", "notes.md")["van_hanh"]


def test_doc_ma_utf16_va_kiem_ke(tmp_path):
    ma = "void OnTick(){ OrderSend(1); } // basket close all, hedge"
    assert "OnTick" in SK.doc_van_ban_ma(b"\xff\xfe" + ma.encode("utf-16-le"))
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "Hedge_EA.mq5").write_bytes(b"\xff\xfe" + ma.encode("utf-16-le"))
    (tmp_path / "a" / "ind.mq5").write_text("#property indicator_separate_window\nint OnCalculate(){return 0;}")
    (tmp_path / "README.md").write_text("no code")
    kq = SK.kiem_ke_kho(tmp_path, "thu", ra_thu_muc=str(tmp_path / "ra"))
    assert kq["tong"]["ea"] == 1 and kq["tong"]["chi_bao"] == 1 and kq["tong"]["ky_thuat_quan_tri"]["hedge"] == 1
    assert (tmp_path / "ra" / "KHO_thu.json").exists()


@pytest.mark.skipif(not (EA / "src" / "strategies").exists(), reason="can ban clone EA31337")
def test_kiem_ke_ea31337_that(tmp_path):
    kq = SK.kiem_ke_kho(EA, "EA31337", ra_thu_muc=str(tmp_path))
    assert kq["tong"]["chien_luoc"] >= 100                       # 69 chien luoc + 42 meta
    hedge = [t["tep"] for t in kq["tep"] if "hedge" in t["quan_tri"]]
    assert any("Meta_Hedge" in t for t in hedge)
