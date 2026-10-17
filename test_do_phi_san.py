import sys
sys.path.insert(0, "mt5tools")
import do_phi_san as D  # noqa: E402


def test_ten_goc_nhan_ra_ten_cua_ca_hai_san():
    cap = {"EURUSDc": "EURUSD", "XAUUSDc": "XAUUSD", "EURUSDm": "EURUSD", "USTECm": "US100", "US500m": "US500",
           "DE30m": "GER40", "EURUSDmicro": "EURUSD", "GOLD.i#": "XAUUSD", "US500Cash#": "US500", "GER40Cash": "GER40",
           "OILCash#": "USOIL", "GBPJPY#": "GBPJPY", "USDCHF": "USDCHF", "AUDCAD": "AUDCAD"}
    for s, g in cap.items():
        assert D.ten_goc(s) == g, s
    for s in ("AAPL", "Tesla", "BTCETH", "#AMZN"):
        assert D.ten_goc(s) is None, s


def test_swap_ra_tien_moi_dem():
    # POINTS: -5 diem EURUSD (point 1e-5), tick_value 1 USD / tick 1e-5 / lot -> 0,01 lot = -0,05 USD
    assert abs(D.swap_tien_dem(1, -5.0, 0.01, 1e-5, 1.0, 1e-5, 1.1) + 0.05) < 1e-12
    assert D.swap_tien_dem(0, -5.0, 0.01, 1e-5, 1.0, 1e-5, 1.1) == 0.0
    assert abs(D.swap_tien_dem(4, -3.0, 0.1, 0.01, 0.01, 0.01, 5000) + 0.3) < 1e-12
    # lai suat -2,5 %/nam tren US500 gia 5000, 1 diem = 1 USD/lot -> 0,1 lot ~ -0,0347 USD/dem
    assert abs(D.swap_tien_dem(5, -2.5, 0.1, 0.01, 0.01, 0.01, 5000) + 5000 * 0.1 * 0.025 / 360) < 1e-9
    assert D.swap_tien_dem(9, -1.0, 0.01, 1e-5, 1.0, 1e-5, 1.1) is None    # mode la: KHONG doan


def test_spread_gio_va_gian_doi_ngay():
    gio = [10] * 100 + [0] * 100
    sp = [0.0001] * 100 + [0.0001] * 80 + [0.0010] * 20
    b = D.spread_theo_gio(gio, sp)
    assert b[10][0] == 100 and abs(b[10][1] - 0.0001) < 1e-12
    assert b[0][2] > 0.0005                         # p90 gio 0 bat duoc doan gian
    assert D.gian_doi_ngay(b) >= 5


def test_gap_cuoi_tuan():
    h = 3600
    t = [0, h, 2 * h, 2 * h + 50 * h, 2 * h + 51 * h]
    assert D.gap_cuoi_tuan(t, [1, 1, 1, 1.5, 1.5], [1, 1, 1.2, 1.5, 1.5]) == [abs(1.5 - 1.2)]


def test_tom_tat_lich_su_lenh_dca_dong_tp():
    dl = [  # vi the 7: mua 2 lan (DCA) roi dong bang TP; vi the 8: ban dong tay tren dien thoai, lo
        dict(time=0, type=0, entry=0, volume=0.01, price=1.0, commission=-0.03, swap=0, fee=0, profit=0, symbol="EURUSDc", position_id=7, reason=1),
        dict(time=3600, type=0, entry=0, volume=0.02, price=0.99, commission=-0.06, swap=0, fee=0, profit=0, symbol="EURUSDc", position_id=7, reason=1),
        dict(time=7200, type=1, entry=1, volume=0.03, price=1.0, commission=-0.09, swap=-0.1, fee=0, profit=2.0, symbol="EURUSDc", position_id=7, reason=5),
        dict(time=0, type=1, entry=0, volume=0.01, price=1.0, commission=0, swap=0, fee=0, profit=0, symbol="EURUSDc", position_id=8, reason=1),
        dict(time=36000, type=0, entry=1, volume=0.01, price=1.01, commission=0, swap=0, fee=0, profit=-1.0, symbol="EURUSDc", position_id=8, reason=1),
        dict(time=5, type=2, entry=0, volume=0, price=0, commission=0, swap=0, fee=0, profit=100, symbol="", position_id=0, reason=0),
    ]
    tom, lenh = D.tom_tat_lich_su(dl)
    v7 = [x for x in lenh if x["vi_the"] == 7][0]
    assert v7["so_lan_vao"] == 2 and abs(v7["lot"] - 0.03) < 1e-12 and v7["ly_do_dong"] == "TP" and v7["gio_giu"] == 2.0
    assert abs(v7["rong"] - (2.0 - 0.1 - 0.18)) < 1e-9
    t = tom[0]
    assert t["so_vi_the"] == 2 and t["ti_le_dong_loi"] == 0.5
    assert abs(t["hoa_hong_moi_lot_chieu"] - (-0.18 / 0.04 / 2)) < 1e-9
