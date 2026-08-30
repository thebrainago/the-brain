# -*- coding: utf-8 -*-
"""Phan loai file .mq5: chien luoc / tien ich / chi bao.

Bay bat ngay 24/08/2026 khi thu thap 40 file dau tien cua MQL5 Code Base muc
`experts`. `ma_nguon._bao_mau_con_thieu` bao **24 chien luoc chua co mau**,
nhung doc danh sach thi trong do co: Quantora Margin Calculator, Risk
Calculator, Position Size Calculator, Break Even Manager, Trailing Stop Manager,
Trade Manager Panel, Trading Journal, Equity Guard panel. Khong cai nao la
chien luoc.

Nguyen nhan: `VAN_CANH_MA` khop ca chu `CTrade`, ma MOI tien ich quan ly lenh
deu khai bao `CTrade trade;`.

Chinh docstring cua `_bao_mau_con_thieu` da canh bao: gop ba loai vao mot con
so thi khong ai biet nen them template nao. Con so dung tren kho 52 file:
18 chien luoc / 12 tien ich / 22 chi bao.
"""
from __future__ import annotations

import unittest

from nhan import bien_dich_ung_vien as BD


class LoaiMaNguon(unittest.TestCase):

    def test_mo_vi_the_moi_la_chien_luoc(self):
        for ma in ("CTrade trade;\ntrade.Buy(0.1);",
                   "OrderSend(req, res);",
                   "m_trade.PositionOpen(_Symbol, ORDER_TYPE_BUY, 0.1, p, 0, 0);",
                   "trade . Sell ( lot , _Symbol );"):
            self.assertEqual(BD.loai_ma_nguon(ma), "chien_luoc", ma[:40])

    def test_chi_sua_vi_the_la_tien_ich(self):
        """Trailing stop / break even / panel: co CTrade nhung KHONG mo vi the."""
        for ma in ("CTrade trade;\ntrade.PositionModify(ticket, sl, tp);",
                   "CTrade t; t.PositionClose(ticket);",
                   "if(TRADE_ACTION_DEAL == req.action) Print(1);"):
            self.assertEqual(BD.loai_ma_nguon(ma), "tien_ich", ma[:40])

    def test_khong_giao_dich_la_chi_bao(self):
        for ma in ("int h=iMA(_Symbol,0,20,0,MODE_SMA,PRICE_CLOSE);"
                   "\nCopyBuffer(h,0,0,10,buf);",
                   "SetIndexBuffer(0, ExtBuffer);",
                   ""):
            self.assertEqual(BD.loai_ma_nguon(ma), "chi_bao", ma[:40])

    def test_tien_ich_khong_bi_dem_thanh_chien_luoc_thieu_mau(self):
        """Bai kiem doi voi dung 4 file that da lam sai con so 24."""
        tien_ich_that = [
            "CTrade trade;\n// Break Even Manager\n"
            "trade.PositionModify(PositionGetTicket(i), be, tp);",
            "CTrade trade;\n// Trailing Stop\n"
            "if(newSL > sl) trade.PositionModify(tk, newSL, tp);",
            "// Position Size Calculator\n"
            "double lot = risk / (sl_points * tick_value);",
            "// Trading Journal\nFileWrite(h, deal_ticket, profit);",
        ]
        for ma in tien_ich_that:
            self.assertNotEqual(BD.loai_ma_nguon(ma), "chien_luoc", ma[:40])


if __name__ == "__main__":
    unittest.main()
