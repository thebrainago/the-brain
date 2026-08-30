# -*- coding: utf-8 -*-
"""mt5_worker.py - Chay MT5 Strategy Tester THAT (worker chung cho moi vai 'test').

Tach tu lab.py de bo_nao.py (orchestrator) va cac pha khac dung chung.
Chi dung terminal MetaTrader 5 co du lieu M1 (xem cau hinh ben duoi).
Ghi report vao `reports/lab_<ten>.htm` cua MT5_DATA roi doc lai.
"""
import re
import subprocess
import time
from pathlib import Path

# ---- cau hinh MT5 (sua theo may) ----
MT5 = Path(r"C:\Program Files\MetaTrader 5\terminal64.exe")
MT5_DATA = Path(r"C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal"
                r"\D0E8209F77C8CF37AD8BF550E51FF075")
EA = "LuoiDoiXung"
CAP_CHINH = "EURCAD"
CAP_KIEM_CHEO = ["NZDCAD", "EURGBP"]
TU, DEN = "2013.03.01", "2026.07.31"
VON = 20000.0

EA_INPUT_MAC_DINH = dict(
    LotCoSo=0.01, BuocPip=30.0, HeSoBuoc=1.0, BuocTranPip=400.0, TP_Pip=20.0,
    TangToiDa=60, HeSoLot1=1.0, NhomDau=4, HeSoLot2=1.0, LotToiDa=20.0,
    LocEntry=0, EMA_ChuKy=50, LechATR=2.0, ChoLuiPip=10.0, ChoToiDaNen=120,
    BatChotCap="true", BienCapPip=4.0, ChotTien_0v01=2.5, DungLo_0v01=4000.0,
    MagicMua=770001, MagicBan=770002, TruotToiDa=20, ChoPhepGiaoDich="true")


def dong_mt5():
    subprocess.run(["taskkill", "/F", "/IM", "terminal64.exe"], capture_output=True)
    time.sleep(2)


def viet_set(ten, input_ghi_de):
    p = dict(EA_INPUT_MAC_DINH)
    p.update(input_ghi_de or {})
    d = "".join(f"{k}={v}||{v}||0||0||N\n" for k, v in p.items())
    tp = MT5_DATA / "MQL5" / "Profiles" / "Tester"
    tp.mkdir(parents=True, exist_ok=True)
    (tp / f"{ten}.set").write_text(d, encoding="utf-16")


def chay_tester(ten, symbol=CAP_CHINH, tu=TU, den=DEN):
    ini = MT5_DATA / f"lab_{ten}.ini"
    ini.write_text(f"[Tester]\nExpert={EA}\nExpertParameters={ten}.set\n"
                   f"Symbol={symbol}\nPeriod=M1\nModel=1\nOptimization=0\n"
                   f"FromDate={tu}\nToDate={den}\nDeposit={int(VON)}\nCurrency=USD\n"
                   f"Leverage=1:500\nReport=reports\\lab_{ten}\nReplaceReport=1\n"
                   f"ShutdownTerminal=1\nVisual=0\n", encoding="utf-16")
    t0 = time.time()
    subprocess.Popen([str(MT5), f"/config:{ini}"])
    time.sleep(8)
    while "terminal64.exe" in subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
            capture_output=True, text=True).stdout:
        if time.time() - t0 > 2400:
            dong_mt5()
            break
        time.sleep(12)
    return doc_tester(ten)


def doc_tester(ten):
    p = MT5_DATA / "reports" / f"lab_{ten}.htm"
    if not p.exists():
        return None
    t = p.read_text(encoding="utf-16", errors="ignore")
    o = [x.strip() for x in re.sub(r"<[^>]+>", "\n", t).split("\n") if x.strip()]
    khoa = {"Total Net Profit": "loi", "Profit Factor": "pf",
            "Sharpe Ratio": "sharpe", "Equity Drawdown Maximal": "dd",
            "Total Trades": "lenh"}
    r = {}
    for i, x in enumerate(o):
        n = x.rstrip(":").strip()
        if n in khoa and khoa[n] not in r and i + 1 < len(o):
            m = re.search(r"-?[\d\s]+[.,]?\d*", o[i + 1].replace("\xa0", " "))
            if m:
                r[khoa[n]] = float(m.group(0).replace(" ", "").replace(",", ""))
    return r or None
