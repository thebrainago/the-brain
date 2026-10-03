# -*- coding: utf-8 -*-
"""bao_cao_mt5: doc bao cao tester thanh SO, khop nguyen O, thieu truong -> khong phai 0.

Mau la TONG HOP dung bo cuc bao cao MT5 (cap nhan/gia tri lap trong mot hang, so co khoang
trang nghin, DD dang "tien (pct%)"). Mau THAT dau tien tu may nha phai them vao day.
"""
from __future__ import annotations

from nhan import bao_cao_mt5 as B

# nhan Anh / Viet cho cac truong chinh (nhan Viet chi lay nhung nhan co that trong chay_tester_z5.NHAN)
EN = {"lai_rong": "Total Net Profit", "lai_tho": "Gross Profit", "lo_tho": "Gross Loss",
      "so_lenh": "Total Trades", "pf": "Profit Factor", "dd": "Equity Drawdown Maximal",
      "thang": "Profit Trades (% of total)", "sharpe": "Sharpe Ratio"}
VI = {"lai_rong": "Tổng lợi nhuận ròng", "lai_tho": "Lợi nhuận ròng", "lo_tho": "Lỗ ròng",
      "so_lenh": "Tổng giao dịch", "pf": "Hệ số lợi nhuận", "dd": "Sụt giảm vốn sở hữu tối đa",
      "thang": "Giao dịch có lợi nhuận", "sharpe": "Tỷ lệ Sharpe"}


def html_mau(nhan: dict, lai=1234.56, tho=3000.0, lo=-1765.44, lenh=51, dd="2 100.00 (21.00%)",
             von="10 000.00", ky="H1 (2020.01.01 - 2020.12.31)") -> str:
    hang = [
        ("Expert:", "MyEA"), ("Symbol:", "EURUSD"), ("Period:", ky),
        ("Initial Deposit:", von), ("History Quality:", "100%"),
        ("Bars:", "6 200"), ("Ticks:", "12 345 678"),
    ]
    thong_so = (
        "<tr><td>%s:</td><td><b>%s</b></td><td>%s:</td><td><b>%s</b></td><td>%s:</td><td><b>%s</b></td></tr>"
        % (nhan["lai_rong"], "{:,.2f}".format(lai).replace(",", " "),
           nhan["lai_tho"], "{:,.2f}".format(tho).replace(",", " "),
           nhan["lo_tho"], "{:,.2f}".format(lo).replace(",", " ")))
    tren = "".join("<tr><td nowrap>%s</td><td colspan=3><b>%s</b></td></tr>" % h for h in hang)
    duoi = ("<tr><td>%s:</td><td><b>1.70</b></td><td>%s:</td><td><b>%d</b></td></tr>"
            "<tr><td>%s:</td><td><b>%s</b></td><td>Equity Drawdown Relative:</td>"
            "<td><b>21.00%% (2 100.00)</b></td></tr>"
            "<tr><td>%s:</td><td><b>29 (56.86%%)</b></td></tr>"
            % (nhan["pf"], nhan["so_lenh"], lenh, nhan["dd"], dd, nhan["thang"]))
    return ("<html><head><title>Strategy Tester Report</title><style>td{x:1}</style></head><body>"
            "<table>%s%s%s</table></body></html>" % (tren, thong_so, duoi))


def test_doc_bao_cao_tieng_anh_ra_so_dung():
    r = B.phan_tich(html_mau(EN))
    assert r["doc_duoc"] and r["thieu"] == []
    assert r["lai_rong"] == 1234.56 and r["lai_tho"] == 3000.0 and r["lo_tho"] == -1765.44
    assert r["so_lenh"] == 51 and r["von"] == 10000.0 and r["pf"] == 1.7
    assert r["dd_von_toi_da"] == {"tien": 2100.0, "pct": 21.0} and r["dd_pct"] == 21.0
    assert r["thang"] == {"so": 29.0, "pct": 56.86}
    assert (r["khung"], r["tu"], r["den"]) == ("H1", "2020.01.01", "2020.12.31")
    assert r["symbol"] == "EURUSD" and r["expert"] == "MyEA"
    assert r["ticks"] == 12345678 and r["chat_luong_pct"] == 100.0


def test_bay_nhan_tieng_viet_loi_nhuan_rong_la_gross_khong_phai_net():
    """'Loi nhuan rong' = Gross Profit; lai THAT la 'Tong loi nhuan rong' (lech 13,5 lan o ban cu)."""
    r = B.phan_tich(html_mau(VI, lai=222.0, tho=3000.0, lo=-2778.0))
    assert r["lai_rong"] == 222.0, r
    assert r["lai_tho"] == 3000.0 and r["lo_tho"] == -2778.0
    assert r["so_lenh"] == 51 and r["dd_pct"] == 21.0


def test_dd_lay_so_lon_hon_trong_cac_cach_tinh():
    r = B.phan_tich(html_mau(EN, dd="900.00 (9.00%)"))
    assert r["dd_von_toi_da"]["pct"] == 9.0 and r["dd_von_tuong_doi"]["pct"] == 21.0
    assert r["dd_pct"] == 21.0, "gate phai doc DD LON nhat de thua con hon de lot"


def test_thieu_truong_bat_buoc_khong_phai_so_khong():
    van = html_mau(EN).replace("Total Trades:", "Tong so lenh:")
    r = B.phan_tich(van)
    assert not r["doc_duoc"] and "so_lenh" in r["thieu"] and "so_lenh" not in r
    r = B.phan_tich("<html><body><p>Tester crashed</p></body></html>")
    assert not r["doc_duoc"] and set(r["thieu"]) >= {"lai_rong", "so_lenh", "dd_von"}


def test_nhan_thieu_gia_tri_khong_an_nhan_ke_tiep():
    van = ("<table><tr><td>Total Net Profit:</td><td>Gross Profit:</td><td>3 000.00</td></tr>"
           "<tr><td>Total Trades:</td><td>10</td></tr></table>")
    r = B.phan_tich(van)
    assert "lai_rong" not in r and r["lai_tho"] == 3000.0 and r["so_lenh"] == 10


def test_nhan_them_cho_ban_ngu_chua_co_mau():
    van = html_mau(EN).replace("Total Trades:", "Số giao dịch:")
    assert not B.phan_tich(van)["doc_duoc"]
    r = B.phan_tich(van, nhan_them={"so_lenh": "Số giao dịch"})
    assert r["doc_duoc"] and r["so_lenh"] == 51


def test_cac_dang_so():
    assert B.so("10 000.00") == 10000.0
    assert B.so("1" + chr(0xa0) + "234.56 (12.3%)") == 1234.56
    assert B.so(chr(0x2212) + "123,5") == -123.5
    assert B.so("-1 765.44") == -1765.44
    assert B.so("1,234") == 1234.0 and B.so("1,5") == 1.5 and B.so("1.234,50") == 1234.5
    assert B.so("n/a") is None and B.so("") is None
    assert B.cac_so("500.00 (4.85%)") == [(500.0, False), (4.85, True)]
    assert B.cac_so("12.34% (1 234.00)") == [(12.34, True), (1234.0, False)]


def test_doc_file_utf16_co_bom_va_utf8_va_khong_co_file(tmp_path):
    van = html_mau(VI)
    f16 = tmp_path / "a.htm"
    f16.write_bytes(b"\xff\xfe" + van.encode("utf-16-le"))
    f8 = tmp_path / "b.htm"
    f8.write_bytes(van.encode("utf-8"))
    f16_khong_bom = tmp_path / "c.htm"
    f16_khong_bom.write_bytes(van.encode("utf-16-le"))
    for f in (f16, f8, f16_khong_bom):
        r = B.doc_bao_cao(f)
        assert r["doc_duoc"] and r["lai_rong"] == 1234.56 and r["file"] == str(f), f.name
    r = B.doc_bao_cao(tmp_path / "khong_co.htm")
    assert not r["doc_duoc"] and "loi" in r


def test_dau_hieu_hong_chi_xet_luot_cuoi():
    cu = "MetaTester 5 started\ncannot generate history data, check disk space\n"
    moi = "MetaTester 5 started\ntest passed in 0:00:07\n"
    assert B.dau_hieu_hong(cu).startswith("TESTER KHONG CHAY DUOC")
    assert B.dau_hieu_hong(cu + moi) == "", "loi cua luot truoc khong duoc lam luot sau bi bao hong oan"
    assert B.dau_hieu_hong("") == "" and B.dau_hieu_hong(None) == ""
