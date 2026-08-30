# -*- coding: utf-8 -*-
r"""loc_chat_luong.py - SEEKER: BO LOC CHAT LUONG noi dung.
Phan loai cot noi dung thu duoc thanh:
  - RA_TIEN : chien luoc/phuong phap/chi bao co quy tac (vao ra) -> LUU & xu ly.
  - DU_BAO  : du doan/nhan dinh -> kiem tra co so (co he thong khong, lay duoc khong).
  - NOISE   : tin tuc/y kien/quang cao -> bo.
Chay:  python loc_chat_luong.py --van-ban "..."   hoac goi qua import.
"""
import sys, re, json, argparse

RA_TIEN = ["entry", "exit", "stop loss", "take profit", "tp", "sl", "signal", "indicator",
           "ea", "strategy", "backtest", "long", "short", "buy when", "sell when", "rule",
           "system", "breakout", "momentum", "mean reversion", "donchian", "ichimoku",
           "rsi", "macd", "ema", "bollinger", "vào lệnh", "cắt lỗ", "chốt lời", "tín hiệu",
           "chiến lược", "chỉ báo", "lệnh", "stop loss", "cản", "hỗ trợ", "kháng cự",
           "стратегия", "индикатор", "сделка", "策略", "指标", "estrategia", "indicador"]
DU_BAO = ["forecast", "prediction", "expect", "target price", "will rise", "will fall",
          "outlook", "dự đoán", "dự báo", "kỳ vọng", "nhận định", "triển vọng", "diễn biến",
          "прогноз", "ожидается", "预测", "预期", "pronóstico", "previsión"]
NOISE = ["subscribe", "follow me", "join now", "limited time", "free webinar", "đăng ký kênh",
         "bấm like", "chia sẻ", "follow", "like và đăng ký", "подпишитесь", "订阅", "sígueme"]

def _dem(text, tu):
    t = text.lower()
    return sum(1 for w in tu if w.lower() in t)

def phan_loai(text):
    if not text:
        return {"loai": "NOISE", "diem": 0.0, "ly_do": "rong"}
    rt = _dem(text, RA_TIEN)
    db = _dem(text, DU_BAO)
    ns = _dem(text, NOISE)
    # chi so: ma co quy tac thi ra tien nhieu hon
    diem = rt - db - ns * 0.5
    if rt >= 2 and diem >= 1:
        return {"loai": "RA_TIEN", "diem": round(diem, 1),
                "so_mark_ra_tien": rt, "so_mark_du_bao": db, "ly_do": "co quy tac vao/ra"}
    if db >= 1 and rt >= 1:
        return {"loai": "DU_BAO", "diem": round(diem, 1),
                "so_mark_ra_tien": rt, "so_mark_du_bao": db, "ly_do": "du bao NHUNG co mo ta he thong -> kiem tra co so"}
    if db >= 1:
        return {"loai": "DU_BAO", "diem": round(diem, 1),
                "so_mark_ra_tien": rt, "so_mark_du_bao": db, "ly_do": "du bao don thuan"}
    return {"loai": "NOISE", "diem": round(diem, 1),
            "so_mark_ra_tien": rt, "so_mark_du_bao": db, "ly_do": "khong duoc quy tac"}

def kiem_tra_co_so(text):
    """Voi DU_BAO: co mo ta he thong + co so du lieu de ve lai khong."""
    he = _dem(text, RA_TIEN)
    co_so = _dem(text, ["backtest", "test", "data", "số liệu", "dữ liệu", "lịch sử",
                        "win rate", "drawdown", "pf", "sharpe", "бэктест", "回测",
                        "данные", "历史"])
    return {"co_he_thong": he >= 1, "co_du_lieu": co_so >= 1,
            "lay_duoc": he >= 1 and co_so >= 1,
            "nhan_xet": "co he + co so -> lay duoc" if (he >= 1 and co_so >= 1)
                        else ("co he, thieu so lieu" if he >= 1 else "doan mo, khong lay duoc")}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--van-ban", default="")
    a = ap.parse_args()
    if a.van_ban:
        print(json.dumps({"phan_loai": phan_loai(a.van_ban),
                          "kiem_du_bao": kiem_tra_co_so(a.van_ban)}, ensure_ascii=False, indent=2))
