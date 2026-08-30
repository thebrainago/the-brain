# THE BRAIN - lay data OHLCV ra CSV (khong can key)
import argparse, pathlib, time
import requests
LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
DATA = LAB / "data"
MS = {"1m":60000,"5m":300000,"15m":900000,"30m":1800000,"1h":3600000,"4h":14400000,"1d":86400000}
def binance(symbol, khung, songay):
    ms = MS.get(khung, 3600000)
    end = int(time.time()*1000)
    start = end - songay*86400000
    rows = []
    cur = start
    while cur < end:
        r = requests.get("https://api.binance.com/api/v3/klines",
                         params={"symbol":symbol,"interval":khung,"startTime":cur,"limit":1000},
                         timeout=30)
        if r.status_code != 200:
            print("loi", r.status_code, r.text[:120]); break
        batch = r.json()
        if not batch:
            break
        for k in batch:
            rows.append([k[0], k[1], k[2], k[3], k[4], k[5]])
        cur = batch[-1][0] + ms
        time.sleep(0.15)
    return rows

MV = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"60m","4h":"4h","1d":"1d"}
RV = {"1d":"1mo","5d":"1mo","1mo":"3mo","3mo":"1y","6mo":"1y","1y":"2y"}
def yahoo_fx(symbol, khung, songay):
    iv = MV.get(khung, "60m")
    rng = RV.get(songay if isinstance(songay,str) else "", "1mo")
    if isinstance(songay, int):
        rng = "1mo" if songay<=31 else ("3mo" if songay<=92 else "1y")
    r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/"+symbol,
                     params={"interval":iv,"range":rng},
                     headers={"User-Agent":"Mozilla/5.0"}, timeout=30)
    if r.status_code != 200:
        print("yahoo loi", r.status_code, r.text[:120]); return []
    res = r.json()["chart"]["result"][0]
    ts = res["timestamp"]; q = res["indicators"]["quote"][0]
    rows = []
    for i, t in enumerate(ts):
        o = q["open"][i]; h = q["high"][i]; lo = q["low"][i]; c = q["close"][i]; v = q["volume"][i]
        if o is None: continue
        rows.append([t*1000, o, h, lo, c, v if v else 0])
    return rows
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nguon", default="binance")
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--khung", default="1h")
    ap.add_argument("--songay", type=int, default=30)
    a = ap.parse_args()
    DATA.mkdir(exist_ok=True)
    rows = yahoo_fx(a.symbol, a.khung, a.songay) if a.nguon=="yahoo" else binance(a.symbol, a.khung, a.songay)
    out = DATA / (a.symbol + "_" + a.khung + ".csv")
    with open(out, "w", encoding="utf-8") as f:
        f.write("open_time,open,high,low,close,volume" + chr(10))
        for r in rows:
            f.write(",".join([str(x) for x in r]) + chr(10))
    print(a.symbol, a.khung, len(rows), "nen ->", out)
if __name__ == "__main__":
    main()
