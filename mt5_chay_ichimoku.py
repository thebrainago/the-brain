# -*- coding: utf-8 -*-
"""mt5_chay_ichimoku.py - Chay EA_IchimokuCross tren MT5 Strategy Tester.
Mau tu mt5_worker.py. Chay: python mt5_chay_ichimoku.py
"""
import subprocess, time, re
from pathlib import Path

MT5 = Path(r"C:\Program Files\MetaTrader 5\terminal64.exe")
MT5_DATA = Path(r"C:\Users\SV STORE\AppData\Roaming\MetaQuotes\Terminal"
                r"\D0E8209F77C8CF37AD8BF550E51FF075")
EA = "EA_IchimokuCross"
SYMBOL = "EURUSD"
PERIOD = "D1"
TU, DEN = "2016.08.01", "2026.08.01"
VON = 10000.0

INPUTS = dict(
    InpTenkan=9, InpKijun=26, InpSenkou=52, InpHoldBars=3, InpLot=0.01,
    InpMagic=820001, InpOnlyLong=False, InpMaxSpreadPts=60, InpSlippagePts=20,
    InpChikouFilter=False, InpChikouAbove=True, InpUseATRStop=False,
    InpATRPeriod=14, InpStopATR=0.0, InpTakeATR=0.0,
)

def dong_mt5():
    subprocess.run(["taskkill", "/F", "/IM", "terminal64.exe"], capture_output=True)
    time.sleep(2)

def viet_set(ten):
    p = dict(INPUTS)
    d = "".join(f"{k}={v}||{v}||0||0||N\n" for k, v in p.items())
    tp = MT5_DATA / "MQL5" / "Profiles" / "Tester"
    tp.mkdir(parents=True, exist_ok=True)
    (tp / f"{ten}.set").write_text(d, encoding="utf-16")

def chay_tester(ten):
    viet_set(ten)
    ini = MT5_DATA / f"lab_{ten}.ini"
    ini.write_text(f"[Tester]\nExpert={EA}\nExpertParameters={ten}.set\n"
                   f"Symbol={SYMBOL}\nPeriod={PERIOD}\nModel=1\nOptimization=0\n"
                   f"FromDate={TU}\nToDate={DEN}\nDeposit={int(VON)}\nCurrency=USD\n"
                   f"Leverage=1:500\nReport=reports\\{ten}\nReplaceReport=1\n"
                   f"ShutdownTerminal=1\nVisual=0\n", encoding="utf-16")
    t0 = time.time()
    subprocess.Popen([str(MT5), f"/config:{ini}"])
    time.sleep(8)
    while "terminal64.exe" in subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
            capture_output=True, text=True).stdout:
        if time.time() - t0 > 2400:
            dong_mt5(); break
        time.sleep(12)
    return doc_tester(ten)

def doc_tester(ten):
    p = MT5_DATA / "reports" / f"{ten}.htm"
    if not p.exists():
        return None
    t = p.read_text(encoding="utf-16", errors="ignore")
    o = [x.strip() for x in re.sub(r"<[^>]+>", "\n", t).split("\n") if x.strip()]
    khoa = {"Total Net Profit": "loi", "Profit Factor": "pf",
            "Sharpe Ratio": "sharpe", "Equity Drawdown Maximal": "dd",
            "Total Trades": "lenh", "Total Deals": "giao_dich"}
    r = {}
    for i, x in enumerate(o):
        n = x.rstrip(":").strip()
        if n in khoa and khoa[n] not in r and i + 1 < len(o):
            m = re.search(r"-?[\d\s]+[.,]?\d*", o[i + 1].replace("\xa0", " "))
            if m:
                r[khoa[n]] = float(m.group(0).replace(" ", "").replace(",", ""))
    return r or None

if __name__ == "__main__":
    r = chay_tester("ichimoku_eurusd")
    print("KET QUA:", r)
    (Path(__file__).parent / "reports" / "mt5_ichimoku_eurusd.json").write_text(
        __import__("json").dumps(r, ensure_ascii=False), encoding="utf-8")
